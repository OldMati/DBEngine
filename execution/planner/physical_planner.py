from catalog.catalog import Catalog
from execution.planner.logical import *
from execution.operators.seq_scan import SeqScan
from execution.operators.filter import Filter
from execution.operators.hash_join import HashJoin
from execution.operators.delete import Delete
from catalog.schema import Schema
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
                #print(f'row before coerce: {row}')
                row = table.schema.coerce(row)
                #print(f'row after coerce: {row}')
                table.insert(row)
                count += 1
            return f'Values inserted successfully. Rows affected: {count}'
        
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
            table = self.catalog.tables[node.table_name]
            operator = SeqScan()
            operator.open(table, node.predicate, node.yield_rid)
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
