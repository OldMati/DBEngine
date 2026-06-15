from catalog.table import Table
from catalog.schema import Schema, Column, DataType
from storage.heap_file import HeapFile
from buffer.buffer_pool import BufferPoolManager
from index.b_tree import BPlusTree
import json

class Catalog:
    next_file_id: int
    data_dir: str
    catalog_filepath: str
    tables: dict[str, Table]

    def __init__(self, bpm: BufferPoolManager, data_dir: str):
        self.next_file_id = 0
        self.filepath = data_dir + 'catalog.json'
        self.bpm = bpm
        self.catalog_filepath = self.filepath
        self.tables = {}

    def flush(self):
        data = {
            'next_file_id': self.next_file_id,
            'tables': {}
        }
        for name, table in self.tables.items():
            serializable_indices = {}
            for col_name, index_dict in table.indices.items():
                meta = {k: v for k, v in index_dict.items() if k != 'tree'}
                serializable_indices[col_name] = meta

            data['tables'][name] = {
                'file_id': table.file_id,
                'schema': table.schema.to_dict(),
                'indices': serializable_indices,
            }
        
        with open(self.catalog_filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        with open(self.catalog_filepath, 'r') as f:
            data = json.load(f)
        self.next_file_id = data['next_file_id']
        for name, meta in data['tables'].items():
            schema = Schema.from_dict(meta['schema'])
            file_id = meta['file_id']
            indices = meta['indices']
            print('FETCHING INDICES, INDICES: ', indices)
            for index in indices.values():
                index['tree'] = BPlusTree(self.bpm, index['file_id'])
            heap_file = HeapFile(self.bpm, file_id)
            self.tables[name] = Table(name, heap_file, schema, file_id, indices)

    def create_index(self, table_name: str, index_name: str, column_name: int):
        # create the entry
        file_id = self.next_file_id
        self.next_file_id += 1
        table = self.get_table(table_name)
        print('table indices: ', table.indices)
        print('column name: ', column_name)
        if column_name in table.indices:
            raise KeyError(f'An index in {table_name} on {column_name} already exists')
        
        tree = BPlusTree(self.bpm, file_id, True)
        col_index = table.get_index(column_name)

        for record in table.scan():
            tree.insert(record.values[col_index], record.rid)
        
        table.indices[column_name] = {
            'file_id': file_id,
            'index_name': index_name,
            'tree': tree
        }
        self.flush()

    def create_table(self, table_name: str, schema: Schema):
        file_id = self.next_file_id
        self.next_file_id += 1

        if table_name in self.tables:
            raise NameError(f'A table named {table_name} already exists')
        #print('CREATING TABLE')
        heap_file = HeapFile(self.bpm, file_id)
        heap_file.create_directory()
        new_table = Table(table_name, heap_file, schema, file_id)
        self.tables[table_name] = new_table
        #print('tables: ', self.tables)
        self.flush()
        return True

    def delete_table(self, table_name):
        if table_name not in self.tables:
            raise KeyError(f'A table named {table_name} does not exist')
        del self.tables[table_name]
        self.flush()
        return True
    
    def get_table(self, table_name):
        if table_name not in self.tables:
            raise KeyError(f'A table named {table_name} does not exist')
        return self.tables[table_name]
