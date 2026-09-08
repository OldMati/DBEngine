import os

import pytest

from buffer.buffer_pool import BufferPoolManager
from storage.heap_file import HeapFile

FILE_ID = 998


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def make_heap_file(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    pools = []

    def _make(create=True):
        bpm = BufferPoolManager()
        pools.append(bpm)
        heap_file = HeapFile(bpm=bpm, file_id=FILE_ID)
        if create:
            heap_file.create_directory()
        return heap_file

    yield _make
    for bpm in pools:
        bpm.close()


@pytest.fixture
def heap_file(make_heap_file):
    return make_heap_file()


@pytest.fixture
def rows(heap_file):
    """Twenty inserted tuples, as rid -> row."""
    return {heap_file.insert_tuple(os.urandom(50)): None} | {
        rid: row
        for row, rid in (
            (row, heap_file.insert_tuple(row))
            for row in (os.urandom(50) for _ in range(19))
        )
    }


# --- insert and read back ---------------------------------------------------

def test_inserted_tuple_is_readable_by_rid(heap_file):
    row = os.urandom(50)

    rid = heap_file.insert_tuple(row)

    assert heap_file.get_tuple(rid) == row


def test_every_insert_gets_a_distinct_rid(heap_file):
    rids = [heap_file.insert_tuple(os.urandom(50)) for _ in range(20)]

    assert len(set(rids)) == 20


def test_all_tuples_remain_readable_after_later_inserts(heap_file):
    written = {}
    for _ in range(20):
        row = os.urandom(50)
        written[heap_file.insert_tuple(row)] = row

    for rid, row in written.items():
        assert heap_file.get_tuple(rid) == row


def test_tuples_spanning_many_pages_are_all_readable(heap_file):
    written = {}
    for _ in range(400):
        row = os.urandom(400)
        written[heap_file.insert_tuple(row)] = row

    for rid, row in written.items():
        assert heap_file.get_tuple(rid) == row


# --- page allocation --------------------------------------------------------

def test_first_insert_allocates_a_data_page(heap_file):
    heap_file.insert_tuple(os.urandom(50))

    assert heap_file._get_page_count() == 2  # directory + one data page


def test_small_tuples_share_a_page(heap_file):
    for _ in range(5):
        heap_file.insert_tuple(os.urandom(50))

    assert heap_file._get_page_count() == 2


def test_filling_a_page_allocates_another(heap_file):
    heap_file.insert_tuple(os.urandom(400))
    before = heap_file._get_page_count()

    for _ in range(400):
        heap_file.insert_tuple(os.urandom(400))

    assert heap_file._get_page_count() > before


def test_tuples_never_share_a_page_id_and_slot(heap_file):
    rids = [heap_file.insert_tuple(os.urandom(400)) for _ in range(400)]

    assert len(set(rids)) == len(rids)


# --- delete -----------------------------------------------------------------

def test_delete_reports_success(heap_file):
    rid = heap_file.insert_tuple(os.urandom(50))

    assert heap_file.delete_tuple(rid) is True


def test_delete_leaves_other_tuples_intact(heap_file):
    keep_rid = heap_file.insert_tuple(os.urandom(50))
    keep = heap_file.get_tuple(keep_rid)
    drop_rid = heap_file.insert_tuple(os.urandom(50))

    heap_file.delete_tuple(drop_rid)

    assert heap_file.get_tuple(keep_rid) == keep


# --- scan -------------------------------------------------------------------

def test_scan_yields_every_inserted_tuple(heap_file):
    written = {}
    for _ in range(30):
        row = os.urandom(50)
        written[heap_file.insert_tuple(row)] = row