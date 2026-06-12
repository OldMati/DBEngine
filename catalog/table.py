from storage.heap_file import HeapFile
from schema import Schema, Record

class Table:
    table_name: str
    heap_file: HeapFile
    schema: Schema

    def __init__(self, table_name: str, heap_file: HeapFile, schema: Schema):
        self.table_name = table_name
        self.heap_file = heap_file
        self.schema = schema

    def insert(self, row: Record) -> tuple[int, int]:
        raw = self.schema.serialize(row)
        return self.heap_file.insert_tuple(raw)

    def get(self, rid: tuple[int, int]):
        raw = self.heap_file.get_tuple(rid)
        return self.schema.deserialize(raw, rid)
    
    def delete(self, rid):
        return self.heap_file.delete_tuple(rid)

    def scan(self):
        for rid, raw in self.heap_file.scan():
            record = self.schema.deserialize(raw, rid)
            yield record
    
    def get_index(self, col_name: str):
        return self.schema.get_index(col_name)