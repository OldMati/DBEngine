from catalog.catalog import Catalog
from execution.planner.logical_planner import LogicalPlanner
from execution.planner.physical_planner import PhysicalPlanner
from execution.planner.query_optimizer import QueryOptimizer
import time

class Database:

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.logical_planner = LogicalPlanner()
        self.physical_planner = PhysicalPlanner(catalog)
        self.query_optimizer = QueryOptimizer()

    def execute(self, sql: str):
        logical_tree = self.logical_planner.plan(sql)
        optimized_query = self.query_optimizer.push_down(logical_tree)
        physical_tree = self.physical_planner.plan(optimized_query)
        #print(physical_tree.output_schema)
        #print('Reached Database.execute loop')
        if type(physical_tree) == str:
            return physical_tree, None
        else:
            result = []
            for row in physical_tree.next():
                #print(f'------ appending row: {row} to result')
                result.append(row)
            physical_tree.close()
            schema = physical_tree.output_schema()
            return result, schema
