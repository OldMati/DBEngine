from catalog.table import Table
from catalog.schema import Schema, Column
from execution.operators.base import Operator
from execution.expressions.base import Expression

class SeqScan(Operator):
    table: Table
    predicate: None | Expression

    def open(self, table, predicate=None):
        self.table = table
        self.predicate = predicate
        self.schema = Schema([
            Column(f'{self.table.table_name}.{col.name}', col.type, col.max_length)
            for col in self.table.schema.columns
        ])
        if predicate:
            predicate.bind(self.schema)

    def next(self):
        for record in self.table.scan():
            if self.predicate is None or self.predicate.evaluate(record.values, self.schema):
                yield record.values

    def output_schema(self) -> Schema:
        return self.schema

    def close(self):
        pass