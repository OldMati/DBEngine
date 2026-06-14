from catalog.catalog import Catalog
from execution.planner.logical import *
from execution.operators.seq_scan import SeqScan
from execution.operators.filter import Filter
from execution.operators.hash_join import HashJoin
# from execution.operators.projection import Projection

class PhysicalPlanner:
    catalog: Catalog

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan(self, node: LogicalNode, predicate = None):
        if isinstance(node, LogicalScan):
            table = self.catalog.tables[node.table_name]
            operator = SeqScan()
            operator.open(table, predicate)
            return operator
        
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

            operator = HashJoin()
            operator.open(left, left_key, right, right_key)

            return operator

        elif isinstance(node, LogicalProjection):
            pass
