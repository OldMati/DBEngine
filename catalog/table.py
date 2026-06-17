from storage.heap_file import HeapFile
from catalog.schema import Schema, Record

class Table:
    table_name: str
    heap_file: HeapFile
    schema: Schema
    indices: dict # dict mapping column_name to index: {file_id, index_name, tree}

    def __init__(self, table_name: str, heap_file: HeapFile, schema: Schema, file_id: int, indices: dict | None = None):
        self.table_name = table_name
        self.heap_file = heap_file
        self.schema = schema
        self.file_id = file_id
        self.indices = indices if indices else {}

    def insert(self, row: Record | tuple) -> tuple[int, int]:
        if type(row) == tuple:
            row = Record(row, (0, 0))
        raw = self.schema.serialize(row)
        rid = self.heap_file.insert_tuple(raw)

        for col_name, meta in self.indices.items():
            col_index = self.get_index(col_name)
            meta['tree'].insert(row.values[col_index], rid)
        return rid

    def get(self, rid: tuple[int, int]):
        raw = self.heap_file.get_tuple(rid)
        return self.schema.deserialize(raw, rid)
    
    def delete(self, rid):
        row = self.get(rid)
        result = self.heap_file.delete_tuple(rid)

        for col_name, meta in self.indices.items():
            col_index = self.get_index(col_name)
            meta['tree'].delete(row.values[col_index], rid)

        return result

    def scan(self):
        for rid, raw in self.heap_file.scan():
            record = self.schema.deserialize(raw, rid)
            yield record
    
    def get_index(self, col_name: str):
        return self.schema.get_index(col_name)