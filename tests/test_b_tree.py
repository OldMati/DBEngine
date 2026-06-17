import pytest
from index.b_tree import BPlusTree
from buffer.buffer_pool import BufferPoolManager
import os

file_id = 5
bpm = BufferPoolManager()
tree = BPlusTree(bpm, file_id, True)

def test_insert_and_search():
    tree.insert(1, (1, 1))
    tree.insert(2, (2, 2))
    tree.insert(3, (3, 3))
    tree.insert(4, (2, 1))
    tree.insert(4, (4, 4))

    assert tree.search(1) == [(1, 1)]
    assert tree.search(2) == [(2, 2)]
    assert tree.search(3) == [(3, 3)]
    assert tree.search(4) == [(2, 1), (4, 4)]
    assert tree.search(60) == []

def test_leaf_splitting():

    for i in range(5, 1024):
        tree.insert(i, (i, i))

    
    for i in range(5, 1024):
        assert tree.search(i) == [(i, i)]

def test_leaf_linkage():
    keys = [i for i in range(1024)]
    pages = [tree._find_leaf(key)[0] for key in keys]
    page_table = {page.page_id: page for page in pages}

    for page_id in page_table:
        if pages[page_id].next_leaf != -1:
            assert pages[page_id].page_id == page_table[pages[page_id].next_leaf].prev_leaf
        
        if pages[page_id].prev_leaf != -1:
            assert pages[page_id].page_id == page_table[pages[page_id].prev_leaf].next_leaf
    
    page_id = pages[0].page_id
    page = page_table[page_id]

    while page.next_leaf >= 0:
        max_key = page.keys[-1]

        next_page = page_table[page.next_leaf]
        next_min_key = next_page.keys[0]

        assert max_key < next_min_key
        page_id = page.next_leaf
        page = page_table[page_id]


def test_close():
    bpm.close()
    os.remove(f'data/{file_id}.db')