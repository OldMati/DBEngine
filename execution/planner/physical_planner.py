from catalog.catalog import Catalog
from execution.expressions.column_ref import ColumnRef
from execution.expressions.literal import Literal
from execution.expressions.comparison import Comparison, ComparisonOp
from execution.expressions.logical import And
from execution.planner.logical import *
from execution.operators.seq_scan import SeqScan
from execution.operators.index_scan import IndexScan
from execution.operators.filter import Filter
from execution.operators.hash_join import HashJoin
from execution.operators.index_join import IndexJoin
from execution.operators.delete import Delete
from catalog.schema import Schema
from catalog.table import Table
from index.b_tree import BPlusTree
# from execution.operators.projection import Projection

class PhysicalPlanner:
    catalog: Catalog

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan(self, node: LogicalNode, predicate = None):
        if isinstance(node, LogicalInsert):
            table_name = node.table_name
            table = self.catalog.get_table(table_name)
            values = node.values
            count = 0
            for row in values:
                row = table.schema.coerce(row)
                table.insert(row)
                count += 1
            return f'Values inserted successfully. Rows affected: {count}'
        
        elif isinstance(node, LogicalCreateIndex):
            columns = node.column_names

            for column in columns:
                self.catalog.create_index(node.table_name, node.index_name, column)

            return f'Index {node.index_name} created successfully'
        
        elif isinstance(node, LogicalDescribe):
            table = self.catalog.get_table(node.table_name)
            columns = [(col.name, col.type.name) for col in table.schema.columns]
            name_width = max([len('Columns')] + [len(col[0]) for col in columns])
            type_width = max([len('Type')] + [len(col[1]) for col in columns])

            res = [
                f'{'Columns':<{name_width}}  {'Type':<{type_width}}',
                f'{'-'*name_width}  {'-'*type_width}',
            ]
            for name, typ in columns:
                res.append(f'{name:<{name_width}}  {typ:<{type_width}}')

            return '\n'.join(res)

        elif isinstance(node, LogicalTableDrop):
            if self.catalog.delete_table(node.table_name):
                return f'Table {node.table_name} dropped successfully'
        
        elif isinstance(node, LogicalDelete):
            table = self.catalog.tables[node.table_name]
            child = self.plan(node.child)
            operator = Delete()
            operator.open(child, table)
            return operator

        elif isinstance(node, LogicalCreateTable):
            if self.catalog.create_table(node.table_name, Schema(node.columns)):
                return f'Table {node.table_name} created successfully'
            return 'Failed to create table'

        elif isinstance(node, LogicalScan):
            # is there a predicate:
            table = self.catalog.tables[node.table_name]
            tree_meta, key, residual = self._find_index_lookup(table, node.predicate)

            if tree_meta:
                return self._index_scan(node, table, tree_meta['tree'], key, residual)
            else:
                return self._seq_scan(node, table)
            
        
        elif isinstance(node, LogicalFilter):
            child = self.plan(node.child)
            operator = Filter()
            operator.open(child, node.predicate)
            return operator

        elif isinstance(node, LogicalJoin):
            left = self.plan(node.left)
            right = self.plan(node.right)

            # need to check the logic for getting the column names for keys
            left_key = node.condition.left.column_name
            right_key = node.condition.right.column_name
            
            left_table = self._table_of(node.left)
            right_table = self._table_of(node.right)

            right_col_name = right_key.split('.')[-1]
            if right_table is not None and right_col_name in right_table.indices:
                print('DOING INDEX JOIN')
                index_meta = right_table.indices[right_col_name]
                operator = IndexJoin()
                operator.open(index_meta['tree'], left, left_key, right_table, right_key)
                return operator

            left_col_name = right_key.split('.')[-1]
            if left_table is not None and left_col_name in left_table.indices:
                print('DOING INDEX JOIN')
                index_meta = left_table.indices[left_col_name]
                operator = IndexJoin()
                operator.open(index_meta['tree'], right, right_key, left_table, left_key)
                return operator

            #if cannot index join, do hash join
            print('DOING HASH JOIN')
            operator = HashJoin()
            operator.open(left, left_key, right, right_key)

            return operator

        elif isinstance(node, LogicalProjection):
            pass

    def _index_scan(self, node: LogicalScan, table: Table, tree: BPlusTree, key: int, residual: Expression):
        operator = IndexScan()
        operator.open(table, tree, key, residual, node.yield_rid)
        return operator

    def _seq_scan(self, node: LogicalScan, table: Table):
        operator = SeqScan()
        operator.open(table, node.predicate, node.yield_rid)
        return operator

    def _find_index_lookup(self, table: Table, predicate: Expression | None = None):
        # if not predicate, return none
        # split conjuncts
        conjuncts = self._split_conjuncts(predicate)
        for i, c in enumerate(conjuncts):
            if not isinstance(c, Comparison) or c.op != ComparisonOp.EQ:
                continue
            col_ref, literal = self._as_col_and_literal(c)
            if col_ref is None:
                continue
            col_name = col_ref.column_name.split('.')[-1]
            if col_name not in table.indices:
                continue
            
            residual = self._combine_conjuncts(conjuncts[:i] + conjuncts[i + 1:])
            return (table.indices[col_name], literal.value, residual)
        return (None, None, None)

    def _split_conjuncts(self, predicate) -> list:
        if isinstance(predicate, And):
            return self._split_conjuncts(predicate.left) + self._split_conjuncts(predicate.right)
        return [predicate]

    def _as_col_and_literal(self, comparison):
        if isinstance(comparison.left, ColumnRef) and isinstance(comparison.right, Literal):
            return comparison.left, comparison.right
        if isinstance(comparison.left, Literal) and isinstance(comparison.right, ColumnRef):
            return comparison.right, comparison.left
        return None, None

    def _combine_conjuncts(self, conjuncts: list):
        if not conjuncts:
            return None
        
        combined = conjuncts[0]
        for c in conjuncts[1:]:
            combined = And(combined, c)
        
        return combined

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
        