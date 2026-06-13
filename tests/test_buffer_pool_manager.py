import pytest
from buffer.buffer_pool import BufferPoolManager
import random
import os


filepath = 'data/997.db'
file_id = 997

def set_up_bpm():
    try:
        os.remove(filepath)
    except:
        print('No such filepath')
    bpm = BufferPoolManager()
    return bpm

def test_page_allocation():
    bpm = set_up_bpm()
    pages_set = set()
    for _ in range(100):
        page_id = bpm.allocate_page(file_id)
        assert page_id >= 0
        assert page_id not in pages_set
        pages_set.add(page_id)

def test_fetch_persistance():
    bpm = set_up_bpm()
    page_id = bpm.allocate_page(file_id)
    page_raw = bpm.fetch_page(page_id, file_id)

    data = bytes([random.randint(0, 255) for _ in range(4096)])
    page_raw[0:4096] = data
    bpm.unpin_page(page_id, file_id, True)

    page_2 = bpm.fetch_page(page_id, file_id)

    assert page_2 == data
    bpm.unpin_page(page_id, file_id)

def test_pinning():
    bpm = set_up_bpm()
    page_id = bpm.allocate_page(file_id)
    bpm.fetch_page(page_id, file_id)
    frame_id = bpm.page_table[(file_id, page_id)]
    assert bpm.pin_count[frame_id] == 1
    bpm.fetch_page(page_id, file_id)
    assert bpm.pin_count[frame_id] == 2
    bpm.unpin_page(page_id, file_id)
    bpm.unpin_page(page_id, file_id)
    assert bpm.pin_count[frame_id] == 0
    # cannot have negative pin_count
    assert bpm.unpin_page(page_id, file_id) == False

def test_flushing():
    bpm = set_up_bpm()
    page_id = bpm.allocate_page(file_id)
    page_raw = bpm.fetch_page(page_id, file_id)

    data = bytes([random.randint(0, 255) for _ in range(4096)])
    page_raw[0:4096] = data
    bpm.unpin_page(page_id, file_id, True)
    bpm.flush_page((file_id, page_id))
    bpm.page_table.pop(page_id, file_id)
    page_2 = bpm.fetch_page(page_id, file_id)

    assert page_2 == data
    bpm.unpin_page(page_id, file_id)


def test_eviction():
    bpm = set_up_bpm()
    pages = [_ for _ in range(300)]
    raw = []
    for page_id in pages:
        raw.append(bpm.fetch_page(page_id, file_id))


