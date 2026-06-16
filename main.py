from buffer.buffer_pool import BufferPoolManager
from catalog.catalog import Catalog
from database import Database
from cli.format import format_table
import time

data_dir = 'data/'
bpm = BufferPoolManager()
catalog = Catalog(bpm, data_dir)
catalog.load()

db = Database(catalog)

while True:
    sql = input('db> ')
    
    if sql == 'exit': break

    if not sql: continue
    try: 
        start = time.perf_counter()
        results, schema = db.execute(sql)
        bpm.flush_all()
        end = time.perf_counter()
        print()
        if type(results) == str:
            print(results)
            print()
        else:
            to_print = format_table(schema.columns, results)
            
            print(to_print)
            print(f'\nRows affected: {len(results)}')
                
        print(f'Executed in {end - start:.6f}s\n')
    except Exception as e:
        print(e)

bpm.close()