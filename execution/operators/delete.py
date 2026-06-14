from execution.operators.base import Operator
from catalog.table import Table
from catalog.schema import Schema

class Delete(Operator):
    child: Operator
    table: Table

    def open(self, child: Operator, table: Table):
        self.child = child
        self.table = table
        self.rids = []
    
    def next(self):
        self.rids = [rid for rid in self.child.next()]
        for rid in self.rids:
            self.table.delete(rid)
        yield f'Rows affected: {len(self.rids)}'
        
    def output_schema(self):
        return Schema()

    def close(self):
        self.child.close

