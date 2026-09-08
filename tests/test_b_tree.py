import os

import pytest

from buffer.buffer_pool import BufferPoolManager
from index.b_tree import BPlusTree

FILE_ID = 999
N_KEYS = 1024


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def bpm(tmp_path, monkeypatch):
    """A buffer pool writing into a throwaway directory, closed after each test."""
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    pool = BufferPoolManager()
    yield pool
    pool.close()


@pytest.fixture
def tree(bpm):
    return BPlusTree(bpm, FILE_ID, True)


@pytest.fixture
def populated_tree(tree):
    """A tree large enough to have split into several leaves."""
    for i in range(N_KEYS):
        tree.insert(i, (i, i))
    return tree


@pytest.fixture
def leaves(populated_tree):
    """Every leaf page of the populated tree, keyed by page_id."""
    pages = (populated_tree._find_leaf(key)[0] for key in range(N_KEYS))
    return {page.page_id: page for page in pages}


# --- search and insert ------------------------------------------------------

def test_search_returns_inserted_value(tree):
    tree.insert(1, (1, 1))
    tree.insert(2, (2, 2))

    assert tree.search(1) == [(1, 1)]
    assert tree.search(2) == [(2, 2)]


def test_search_missing_key_returns_empty(tree):
    tree.insert(1, (1, 1))

    assert tree.search(60) == []


def test_duplicate_keys_return_all_values_in_insertion_order(tree):
    tree.insert(4, (2, 1))
    tree.insert(4, (4, 4))

    assert tree.search(4) == [(2, 1), (4, 4)]


# --- splitting --------------------------------------------------------------

def test_all_keys_survive_leaf_splitting(populated_tree):
    for i in range(N_KEYS):
        assert populated_tree.search(i) == [(i, i)]


# --- leaf chain (white-box: relies on _find_leaf) ---------------------------

def test_leaf_links_are_symmetric(leaves):
    for page_id, page in leaves.items():
        if page.next_leaf != -1:
            assert leaves[page.next_leaf].prev_leaf == page_id
        if page.prev_leaf != -1:
            assert leaves[page.prev_leaf].next_leaf == page_id


def test_leaf_chain_is_ordered_and_complete(leaves, populated_tree):
    page = populated_tree._find_leaf(0)[0]
    assert page.prev_leaf == -1, "leftmost leaf should have no predecessor"

    seen = {page.page_id}
    while page.next_leaf != -1:
        nxt = leaves[page.next_leaf]
        assert nxt.page_id not in seen, f"cycle at page {nxt.page_id}"
        assert page.keys[-1] < nxt.keys[0]
        seen.add(nxt.page_id)
        page = nxt

    assert seen == leaves.keys(), "chain does not reach every leaf"


# --- durability -------------------------------------------------------------

def test_data_survives_reopen(bpm, tree):
    tree.insert(1, (1, 1))
    bpm.flush_all()

    reopened = BPlusTree(bpm, FILE_ID, False)

    assert reopened.search(1) == [(1, 1)]