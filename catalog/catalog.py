from catalog.table import Table
from schema import Schema, Column, DataType
from storage.heap_file import HeapFile
from buffer.buffer_pool import BufferPoolManager
import json

filepath = 'data/catalog.json'
bpm = BufferPoolManager(filepath)

class Catalog:
    data_dir: str
    catalog_filepath: str
    tables: dict[str, Table]

    def __init__(self):
        self.catalog_filepath = filepath

    def flush(self):
        data = {}
        for name, table in self.tables.items():
            data[name] = {
                'file': table.heap_file.filepath,
                'schema': table.schema.to_dict()
            }
        
        with open(self.catalog_filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        with open(self.catalog_filepath, '4') as f:
            data = json.load(f)
        
        for name, meta in data.items():
            schema = Schema.from_dict(meta['schema'])
            heap_file = HeapFile(schema, bpm)
            self.tables[name] = Table(name, heap_file, schema)

    def create_table(self):
        pass

    def delete_table(self):
        pass