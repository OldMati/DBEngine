from catalog.catalog import Catalog
from execution.planner.logical_planner import LogicalPlanner
from execution.planner.physical_planner import PhysicalPlanner

class Database:

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.logical_planner = LogicalPlanner()
        self.physical_planner = PhysicalPlanner(catalog)

    def execute(self, sql: str):
        logical_tree = self.logical_planner.plan(sql)
        physical_tree = self.physical_planner.plan(logical_tree)
        print(physical_tree.output_schema)
        result = []
        print('Reached Database.execute loop')
        for row in physical_tree.next():
            print(f'------ appending row: {row} to result')
            result.append(row)
        physical_tree.close()
        return result
