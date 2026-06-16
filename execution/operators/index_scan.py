from execution.operators.base import Operator
from catalog.table import Table
from catalog.schema import Schema, Column, DataType
from index.b_tree import BPlusTree
from execution.expressions.base import Expression

class IndexScan(Operator):
    table: Table
    tree: BPlusTree
    key: int | None
    start_key: int | None
    end_key: int | None
    predicate: Expression | None
    yield_rid: bool
    mode: str
    # eq for equal, range for range

    def open(self, table: Table, tree: BPlusTree, mode: str, key = None, start_key = None, end_key = None, predicate: Expression | None = None, yield_rid=False):
        self.table = table
        self.tree = tree
        self.predicate = predicate
        self.yield_rid = yield_rid
        self.key = key
        self.start_key = start_key
        self.end_key = end_key
        self.mode = mode

        self.schema = Schema([
            Column(f'{self.table.table_name}.{col.name}', col.type, col.max_length)
            for col in self.table.schema.columns
        ])

        if predicate:
            predicate.bind(self.schema)
    
    def next(self):
        if self.mode == 'eq':
            rids = self.tree.search(self.key)
        # range
        else:
            rids = self.tree.range_scan(self.start_key, self.end_key)
        for rid in rids:
            record = self.table.get(rid)
            if self.predicate is None or self.predicate.evaluate(record.values, self.schema):
                yield record.rid if self.yield_rid else record.values

    def output_schema(self):
        return self.schema
    
    def close(self):
        pass