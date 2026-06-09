import pytest
from buffer.buffer_pool import BufferPoolManager
import random
import os


filepath = 'tests/bpm.db'
bpm = BufferPoolManager(filepath)

def test_page_allocation():
    pages_set = set()
    for i in range(100):
        page_id = bpm.allocate_page()
        assert page_id >= 0
        assert page_id not in pages_set
        pages_set.add(page_id)

def test_fetch_persistance():
    page_id = bpm.allocate_page()
    page_raw = bpm.fetch_page(page_id)

    data = bytes([random.randint(0, 255) for _ in range(4096)])
    page_raw[0:4096] = data
    bpm.unpin_page(page_id, True)

    page_2 = bpm.fetch_page(page_id)

    assert page_2 == data
    bpm.unpin_page(page_id)

def test_pinning():
    page_id = bpm.allocate_page()
    bpm.fetch_page(page_id)
    frame_id = bpm.page_table[page_id]
    assert bpm.pin_count[frame_id] == 1
    bpm.fetch_page(page_id)
    assert bpm.pin_count[frame_id] == 2
    bpm.unpin_page(page_id)
    bpm.unpin_page(page_id)
    assert bpm.pin_count[frame_id] == 0
    # cannot have negative pin_count
    assert bpm.unpin_page(page_id) == False

def test_flushing():
    page_id = bpm.allocate_page()
    page_raw = bpm.fetch_page(page_id)

    data = bytes([random.randint(0, 255) for _ in range(4096)])
    page_raw[0:4096] = data
    bpm.unpin_page(page_id, True)
    bpm.flush_page(page_id)
    bpm.page_table.pop(page_id)
    page_2 = bpm.fetch_page(page_id)

    assert page_2 == data
    bpm.unpin_page(page_id)


def test_eviction():
    pages = [_ for _ in range(300)]
    raw = []
    for page_id in pages:
        raw.append(bpm.fetch_page(page_id))

def test_close():
    bpm.close()
    os.remove(filepath)

