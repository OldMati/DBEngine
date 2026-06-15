import sqlglot
import sqlglot.expressions as exp
from execution.planner.logical import *
from execution.expressions.comparison import Comparison, ComparisonOp
from execution.expressions.column_ref import ColumnRef
from execution.expressions.literal import Literal
from execution.expressions.logical import And, Or
from catalog.schema import Column, DataType

class LogicalPlanner:

    def plan(self, sql:str) -> LogicalNode:
        ast = sqlglot.parse_one(sql)

        if isinstance(ast, exp.Select):
            return self._plan_select(ast)
        elif isinstance(ast, exp.Drop):
            return self._plan_drop(ast)
        elif isinstance(ast, exp.Delete):
            return self._plan_delete(ast)
        elif isinstance(ast, exp.Create):
            return self._plan_create(ast)
        elif isinstance(ast, exp.Insert):
            return self._plan_insert(ast)
        elif isinstance(ast, exp.Describe):
            return self._plan_describe(ast)
        else:
            raise(NotImplementedError(f'{sql.split()[0]} has not been implemented'))

    def _plan_describe(self, node: exp.Describe):
        table_name = node.this.name
        return LogicalDescribe(table_name)

    def _plan_drop(self, node: exp.Drop):
        kind = node.args['kind']
        assert type(kind) == str
        if kind == 'TABLE':
            return self._plan_drop_table(node)
        
        raise NotImplementedError(f'DROP {kind} is not supported')

    def _plan_drop_table(self, node: exp.Drop):
        table_name = node.this.name
        return LogicalTableDrop(table_name)


    def _plan_delete(self, node: exp.Delete):
        table_name = node.this.name

        # create predicate
        predicate = self._plan_expression(node.args['where'].this, table_name)

        # logical scan
        scan = LogicalScan(table_name, None, predicate, True)

        # apply delete on top
        delete = LogicalDelete(scan, table_name)
        
        return delete


    def _plan_insert(self, node: exp.Insert):
        table_name = node.this.name
        assert type(table_name) == str
        values = []
        #print('node.expression: ', node.expression.expressions)
        for row in node.expression.expressions:
            temp = []
            for val in row.expressions:
                temp.append(str(val.this))
            values.append(tuple(temp))
        #print('values: ', values)
        return LogicalInsert(table_name, values)

    def _plan_create(self, node: exp.Create):
        kind = node.args['kind']
        # print('Node arg keys')
        # print([arg for arg in node.args])
        if kind == 'TABLE':
            return self._plan_create_table(node)
        elif kind == 'INDEX':
            return self._plan_create_index(node)
        
        raise NotImplementedError(f'CREATE {kind} is not supported')
    
    def _plan_create_index(self, node: exp.Create):
        idx_name = node.this.name
        table_name = node.this.args['table'].name
        
        column_names = [col.this.name for col in node.this.args['params'].args['columns']]

        return LogicalCreateIndex(idx_name, table_name, column_names)
 # CREATE INDEX mat_idx on flatmates (id, name)

    def _plan_create_table(self, node: exp.Create):
        table_name = node.this.this.name
        column_defs = node.this.expressions
        columns = []
        for column in column_defs:
            data_type = column.args['kind'].this.name
            #print('data type: ', data_type)
            columns.append(Column(column.name, DataType[data_type]))
        
        return LogicalCreateTable(table_name, columns)


    def _plan_select(self, node: exp.Select) -> LogicalNode:
        table_from_name = node.args['from_'].this.name
        # build the scan
        plan = self._plan_from(node.args['from_'])

        # layer joins
        for join in node.args.get('joins', []):
            right = LogicalScan(join.this.name)
            condition = self._plan_expression(join.args['on'])
            plan = LogicalJoin(left=plan, right=right, condition=condition)
        
        # layer where
        if node.args.get('where'):
            predicate = self._plan_expression(node.args['where'].this, table_from_name)
            plan = LogicalFilter(plan, predicate)
        
        # SKIPPED PROJECTIONS FOR NOW

        return plan

    def _plan_from(self, node) -> LogicalNode:
        table = node.this
        self.from_table = table
        alias = table.alias if table.alias else None
        return LogicalScan(table_name=table.name, alias=alias)
    
    def _plan_projections(self, expressions) -> list[str]:
        return ['*']

    def _plan_expression(self, node, table_name=None) -> Expression:

        if isinstance(node, exp.Column):
            
            col = node.name
            if node.table:
                return ColumnRef(f"{node.table}.{col}")
            return ColumnRef(f"{table_name}.{col}")
    
        elif isinstance(node, exp.Literal):
            value = float(node.this) if node.is_number else node.this
            return Literal(value)
        
        elif isinstance(node, exp.Boolean):
            return Literal(node.this)

        elif isinstance(node, exp.EQ):
            return Comparison(
                self._plan_expression(node.left, table_name),
                ComparisonOp.EQ,
                self._plan_expression(node.right, table_name)
            )
        
        elif isinstance(node, exp.GT):
            return Comparison(
                self._plan_expression(node.left, table_name),
                ComparisonOp.GT,
                self._plan_expression(node.right, table_name)
            )

        elif isinstance(node, exp.GTE):
            return Comparison(
                self._plan_expression(node.left, table_name),
                ComparisonOp.GTE,
                self._plan_expression(node.right, table_name)
            )
        
        elif isinstance(node, exp.LT):
            return Comparison(
                self._plan_expression(node.left, table_name),
                ComparisonOp.LT,
                self._plan_expression(node.right, table_name)
            )
        
        elif isinstance(node, exp.LTE):
            return Comparison(
                self._plan_expression(node.left, table_name),
                ComparisonOp.LTE,
                self._plan_expression(node.right, table_name)
            )
        
        elif isinstance(node, exp.And):
            return And(
                self._plan_expression(node.left, table_name),
                self._plan_expression(node.right, table_name)
            )
        
        elif isinstance(node, exp.Or):
            return Or(
                self._plan_expression(node.left, table_name),
                self._plan_expression(node.right, table_name)
            )


        raise NotImplementedError(f"Unsupported expression type: {type(node)}")