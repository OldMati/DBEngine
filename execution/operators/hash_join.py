from catalog.table import Table
from catalog.schema import Record, Schema
from execution.operators.seq_scan import SeqScan
from execution.operators.base import Operator

class HashJoin(Operator):
    left: Operator
    left_key: any
    right: Operator
    right_key: any

    def open(self, left: Operator, left_key, right: Operator, right_key):
        self.left = left
        self.left_key = left_key
        self.right = right
        self.right_key = right_key

        self.hash_table = {}

        self.left.open()
        self.left_schema = self.left.output_schema()
        left_index = self.left.get_index(self.left_key)

        # build the hash_table
        for record in left.next():
            key = record[left_index]
            if key not in self.hash_table:
                self.hash_table[key] = []
            self.hash_table[record[left_index]].append(record)

        self.left.close()

        self.right.open()
        self.right_schema = self.seq_scan_right.output_schema()
        self.right_index = self.right.get_index(self.right_key)


    def next(self):
        for record in self.right.next():
            key = record[self.right_index]
            if key in self.hash_table:
                for left_values in self.hash_table[key]:
                    yield left_values + record
    
    def output_schema(self):
        return Schema(
            self.left_schema.columns + self.right_schema.columns
        )

    def close(self):
        self.right.close()