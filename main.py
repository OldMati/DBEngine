from buffer.buffer_pool import BufferPoolManager
from catalog.catalog import Catalog
from database import Database

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
        results = db.execute(sql)
        for res in results:
            print(res)
    except Exception as e:
        print(f'Error: ', e)

bpm.close()
