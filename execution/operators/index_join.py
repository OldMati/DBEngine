from catalog.table import Table
from index.b_tree import BPlusTree
from execution.operators.seq_scan import SeqScan
from catalog.schema import Column, Schema
from execution.operators.base import Operator

class IndexJoin(Operator):
    index: BPlusTree
    left: Operator
    right: Operator
    left_key: str
    right_key: str

    def open(self, index: BPlusTree, left: Operator, left_key, right: Table, right_key):
        self.index = index
        self.left = left
        self.left_key = left_key
        self.right = right
        self.right_key = right_key

        _temp_scan = SeqScan()
        _temp_scan.open(right)
        self.right_schema = _temp_scan.output_schema()
        _temp_scan.close()

        self.left_schema = self.left.output_schema()
        self.left_index = self.left_schema.get_index(self.left_key)
        self.right_index = self.right_schema.get_index(self.right_key)


    def next(self):
        for values in self.left.next():
            key = values[self.left_index]
            rids = self.index.search(key)
            for rid in rids:
                values_right = self.right.get(rid).values
                yield values + values_right

    def output_schema(self):
        return Schema(
            self.left_schema.columns + self.right_schema.columns
        )

    def close(self):
        self.left.close()