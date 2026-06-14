from buffer.buffer_pool import BufferPoolManager
from catalog.catalog import Catalog
from database import Database
import time

data_dir = 'data/'
bpm = BufferPoolManager()
catalog = Catalog(bpm, data_dir)
catalog.load()
# CREATE TABLE users (id INT, name VARCHAR)
db = Database(catalog)

while True:
    sql = input('db> ')
    
    if sql == 'exit': break

    if not sql: continue
    
    start = time.perf_counter()
    results = db.execute(sql)
    end = time.perf_counter()
    if type(results) == str:
        print(results)
    else:
        for res in results[:8]:
            print(res)
    # except Exception as e:
    #     print(f'Error: ', e)
    print(f'Executed in {end - start:.6f}s')
    print()

bpm.close()
