import sqlglot
import sqlglot.expressions as exp
from execution.planner.logical import *
from execution.expressions.comparison import Comparison, ComparisonOp
from execution.expressions.column_ref import ColumnRef
from execution.expressions.literal import Literal
from execution.expressions.logical import And, Or

class LogicalPlanner:

    def plan(self, sql:str) -> LogicalNode:
        ast = sqlglot.parse_one(sql)
        return self._plan_select(ast)
    
    def _plan_select(self, node: exp.select) -> LogicalNode:
        # build the scan
        plan = self._plan_from(node.args['from_'])

        # layer joins
        for join in node.args.get('joins', []):
            right = LogicalScan(join.this.name)
            condition = self._plan_expression(join.args['on'])
            plan = LogicalJoin(left=plan, right=right, condition=condition)
        
        # layer where
        if node.args.get('where'):
            predicate = self._plan_expression(node.args['where'].this)
            plan = LogicalFilter(plan, predicate)
        
        # SKIPPED PROJECTIONS FOR NOW

        return plan


    def _plan_from(self, node) -> LogicalNode:
        table = node.this
        alias = table.alias if table.alias else None
        return LogicalScan(table_name=table.name, alias=alias)
    
    def _plan_projections(self, expressions) -> list[str]:
        return ['*']

    def _plan_expression(self, node) -> Expression:

        if isinstance(node, exp.Column):
            table = node.table  # maybe needs .this
            col = node.name
            return ColumnRef(f"{table}.{col}" if table else col)
    
        elif isinstance(node, exp.Literal):
            value = float(node.this) if node.is_number else node.this
            return Literal(value)
        
        elif isinstance(node, exp.EQ):
            return Comparison(
                self._plan_expression(node.left),
                ComparisonOp.EQ,
                self._plan_expression(node.right)
            )
        
        elif isinstance(node, exp.GT):
            return Comparison(
                self._plan_expression(node.left),
                ComparisonOp.GT,
                self._plan_expression(node.right)
            )

        elif isinstance(node, exp.GTE):
            return Comparison(
                self._plan_expression(node.left),
                ComparisonOp.GTE,
                self._plan_expression(node.right)
            )
        
        elif isinstance(node, exp.LT):
            return Comparison(
                self._plan_expression(node.left),
                ComparisonOp.LT,
                self._plan_expression(node.right)
            )
        
        elif isinstance(node, exp.LTE):
            return Comparison(
                self._plan_expression(node.left),
                ComparisonOp.LTE,
                self._plan_expression(node.right)
            )
        
        elif isinstance(node, exp.And):
            return And(
                self._plan_expression(node.left),
                self._plan_expression(node.right)
            )
        
        elif isinstance(node, exp.Or):
            return Or(
                self._plan_expression(node.left),
                self._plan_expression(node.right)
            )


        raise NotImplementedError(f"Unsupported expression type: {type(node)}")