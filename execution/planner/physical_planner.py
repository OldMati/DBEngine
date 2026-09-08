from catalog.catalog import Catalog
from catalog.schema import Schema
from catalog.table import Table
from execution.expressions.column_ref import ColumnRef
from execution.expressions.comparison import Comparison, ComparisonOp
from execution.expressions.literal import Literal
from execution.expressions.logical import And
from execution.operators.delete import Delete
from execution.operators.filter import Filter
from execution.operators.hash_join import HashJoin
from execution.operators.index_join import IndexJoin
from execution.operators.index_scan import IndexScan
from execution.operators.seq_scan import SeqScan
from execution.operators.projection import Projection
from execution.planner.logical import *
from index.b_tree import BPlusTree


class PhysicalPlanner:
    """Turns a logical plan into physical operators.

    DDL and DML nodes are executed directly and return a status string;
    query nodes return an opened operator ready to be iterated.
    """

    catalog: Catalog

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self._handlers = {
            LogicalInsert: self._plan_insert,
            LogicalCreateIndex: self._plan_create_index,
            LogicalDescribe: self._plan_describe,
            LogicalTableDrop: self._plan_drop_table,
            LogicalDelete: self._plan_delete,
            LogicalCreateTable: self._plan_create_table,
            LogicalScan: self._plan_scan,
            LogicalFilter: self._plan_filter,
            LogicalJoin: self._plan_join,
            LogicalProjection: self._plan_projection,
        }

    def plan(self, node: LogicalNode):
        handler = self._handlers.get(type(node))
        if handler is None:
            return None
        return handler(node)

    # --- DDL / DML ----------------------------------------------------------

    def _plan_insert(self, node: LogicalInsert) -> str:
        table = self.catalog.get_table(node.table_name)
        count = 0
        for row in node.values:
            table.insert(table.schema.coerce(row))
            count += 1
        return f'Values inserted successfully. Rows affected: {count}'

    def _plan_create_table(self, node: LogicalCreateTable) -> str:
        if self.catalog.create_table(node.table_name, Schema(node.columns)):
            return f'Table {node.table_name} created successfully'
        return 'Failed to create table'

    def _plan_drop_table(self, node: LogicalTableDrop) -> str | None:
        if self.catalog.delete_table(node.table_name):
            return f'Table {node.table_name} dropped successfully'
        return None

    def _plan_create_index(self, node: LogicalCreateIndex) -> str:
        for column in node.column_names:
            self.catalog.create_index(node.table_name, node.index_name, column)
        return f'Index {node.index_name} created successfully'

    def _plan_delete(self, node: LogicalDelete):
        table = self.catalog.tables[node.table_name]
        child = self.plan(node.child)

        operator = Delete()
        operator.open(child, table)
        result = operator.execute()
        operator.close()
        return result

    def _plan_describe(self, node: LogicalDescribe) -> str:
        table = self.catalog.get_table(node.table_name)
        columns = [(col.name, col.type.name) for col in table.schema.columns]
        return self._format_column_table(columns)

    def _format_column_table(self, columns: list[tuple[str, str]]) -> str:
        name_width = max([len("Columns")] + [len(name) for name, _ in columns])
        type_width = max([len("Type")] + [len(typ) for _, typ in columns])

        lines = [
            f"{'Columns':<{name_width}}  {'Type':<{type_width}}",
            f"{'-' * name_width}  {'-' * type_width}",
        ]
        for name, typ in columns:
            lines.append(f"{name:<{name_width}}  {typ:<{type_width}}")
        return "\n".join(lines)

    # --- query operators ----------------------------------------------------

    def _plan_projection(self, node: LogicalProjection):
        operator = Projection()
        operator.open(self.plan(node.child), node.projections)
        return operator

    def _plan_filter(self, node: LogicalFilter):
        operator = Filter()
        operator.open(self.plan(node.child), node.predicate)
        return operator

    def _plan_scan(self, node: LogicalScan):
        table = self.catalog.tables[node.table_name]
        match = self._find_index_lookup(table, node.predicate)

        if match is None:
            return self._seq_scan(node, table)

        tree_meta, start, end, residual = match
        return self._index_scan(node, table, tree_meta['tree'], start, end, residual)

    def _seq_scan(self, node: LogicalScan, table: Table):
        operator = SeqScan()
        operator.open(table, node.predicate, node.yield_rid)
        return operator

    def _index_scan(
        self,
        node: LogicalScan,
        table: Table,
        tree: BPlusTree,
        start: int,
        end: int,
        residual: Expression,
    ):
        operator = IndexScan()
        if start == end:
            operator.open(
                table, tree, mode='eq', key=start,
                predicate=residual, yield_rid=node.yield_rid,
            )
        else:
            operator.open(table, tree, 'range', None, start, end, residual, node.yield_rid)
        return operator

    # --- joins --------------------------------------------------------------

    def _plan_join(self, node: LogicalJoin):
        left = self.plan(node.left)
        right = self.plan(node.right)

        left_key = node.condition.left.column_name
        right_key = node.condition.right.column_name

        left_table = self._table_of(node.left)
        right_table = self._table_of(node.right)

        # Prefer probing an index on either side over building a hash table.
        operator = self._try_index_join(right_table, right_key, left, left_key)
        if operator is not None:
            return operator

        operator = self._try_index_join(left_table, right_key, right, right_key, left_key)
        if operator is not None:
            return operator

        return self._hash_join(left, left_key, right, right_key)

    def _try_index_join(
        self,
        indexed_table: Table | None,
        indexed_key: str,
        probe_child,
        probe_key: str,
        indexed_open_key: str | None = None,
    ):
        """Return an IndexJoin if `indexed_table` has an index on `indexed_key`."""
        if indexed_table is None:
            return None

        column_name = indexed_key.split('.')[-1]
        if column_name not in indexed_table.indices:
            return None

        index_meta = indexed_table.indices[column_name]
        operator = IndexJoin()
        operator.open(
            index_meta['tree'],
            probe_child,
            probe_key,
            indexed_table,
            indexed_open_key if indexed_open_key is not None else indexed_key,
        )
        return operator

    def _hash_join(self, left, left_key: str, right, right_key: str):
        operator = HashJoin()
        operator.open(left, left_key, right, right_key)
        return operator

    # --- index selection ----------------------------------------------------

    def _find_index_lookup(self, table: Table, predicate: Expression | None = None):
        """Find an indexed column in the predicate and the key range it implies.

        Returns (index_meta, start, end, residual) or None if no index applies.
        """
        if predicate is None:
            return None

        conjuncts = self._split_conjuncts(predicate)
        index_col = None
        start, end = None, None

        for c in conjuncts:
            if not isinstance(c, Comparison):
                continue

            col_ref, literal = self._as_col_and_literal(c)
            if col_ref is None:
                continue

            col_name = col_ref.column_name.split('.')[-1]
            if col_name not in table.indices:
                continue

            if index_col is None:
                index_col = col_name
            elif col_name != index_col:
                continue

            start, end = self._tighten_bounds(c.op, literal.value, start, end)

        if index_col is None:
            return None

        residual = self._combine_conjuncts(conjuncts)
        return (table.indices[index_col], start, end, residual)

    def _tighten_bounds(self, op, value, start, end):
        """Narrow an existing [start, end] range with one more comparison."""
        if op == ComparisonOp.EQ:
            return value, value
        if op == ComparisonOp.GT:
            lower = value + 1
            return (lower if start is None else max(start, lower)), end
        if op == ComparisonOp.GTE:
            return (value if start is None else max(start, value)), end
        if op == ComparisonOp.LT:
            upper = value - 1
            return start, (upper if end is None else min(end, upper))
        if op == ComparisonOp.LTE:
            return start, (value if end is None else min(end, value))
        return start, end

    # --- predicate helpers --------------------------------------------------

    def _split_conjuncts(self, predicate) -> list:
        if isinstance(predicate, And):
            return (
                self._split_conjuncts(predicate.left)
                + self._split_conjuncts(predicate.right)
            )
        return [predicate]

    def _combine_conjuncts(self, conjuncts: list):
        if not conjuncts:
            return None

        combined = conjuncts[0]
        for c in conjuncts[1:]:
            combined = And(combined, c)
        return combined

    def _as_col_and_literal(self, comparison):
        if isinstance(comparison.left, ColumnRef) and isinstance(comparison.right, Literal):
            return comparison.left, comparison.right
        if isinstance(comparison.left, Literal) and isinstance(comparison.right, ColumnRef):
            return comparison.right, comparison.left
        return None, None

    def _table_of(self, node: LogicalNode) -> Table | None:
        if isinstance(node, LogicalScan):
            return self.catalog.get_table(node.table_name)

        for attr in ('left', 'right', 'child'):
            sub = getattr(node, attr, None)
            if sub is not None:
                found = self._table_of(sub)
                if found is not None:
                    return found
        return None