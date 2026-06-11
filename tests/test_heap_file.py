import pytest
from storage.heap_file import HeapFile
from buffer.buffer_pool import BufferPoolManager
import os

filepath = 'tests/heap_file.db'

def set_up_heap_file():
    try:
        os.remove(filepath)
    except:
        print('no such filepath')
    bpm = BufferPoolManager(filepath)
    heap_file = HeapFile(bpm, filepath)
    heap_file.create_directory()
    return heap_file


# insert a tuple and retrieve by RID
def test_insert_get_tuple():
    heap_file = set_up_heap_file()

    test_count = 20
    rows = {} # RID -> row

    # write tuples to heap_file
    for _ in range(test_count):
        row = os.urandom(50)
        rid = heap_file.insert_tuple(row)
        rows[rid] = row
        assert rows[rid] == heap_file.get_tuple(rid)

    assert len(rows) == test_count

    # read tuples from file 
    for rid in rows:
        print('RID: ', rid)
        assert rows[rid] == heap_file.get_tuple(rid)

    heap_file.close()


# insert enough tuples to fill a page, verify the page count increased
def test_page_count_increase():
    heap_file = set_up_heap_file()
    size = 403

    for _ in range(11):
        row = os.urandom(size)
        heap_file.insert_tuple(row)
    
    assert heap_file._get_page_count() == 3


