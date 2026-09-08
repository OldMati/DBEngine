import random

import pytest

from buffer.buffer_pool import BufferPoolManager
from buffer.lru_k_replacer import NUM_FRAMES
from storage.disk_manager import PAGE_SIZE

FILE_ID = 997


def random_page():
    return random.randbytes(PAGE_SIZE)


@pytest.fixture
def make_bpm(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    pools = []

    def _make():
        pool = BufferPoolManager()
        pools.append(pool)
        return pool

    yield _make
    for pool in pools:
        pool.close()


@pytest.fixture
def bpm(make_bpm):
    return make_bpm()


# --- allocation -------------------------------------------------------------

def test_allocate_page_returns_unique_non_negative_ids(bpm):
    seen = set()
    for _ in range(100):
        page_id = bpm.allocate_page(FILE_ID)
        assert page_id >= 0
        assert page_id not in seen
        seen.add(page_id)


# --- caching ----------------------------------------------------------------

def test_write_is_visible_to_a_later_fetch_while_cached(bpm):
    page_id = bpm.allocate_page(FILE_ID)
    frame = bpm.fetch_page(page_id, FILE_ID)
    data = random_page()
    frame[:] = data
    bpm.unpin_page(page_id, FILE_ID, True)

    assert bytes(bpm.fetch_page(page_id, FILE_ID)) == data
    bpm.unpin_page(page_id, FILE_ID)


def test_cache_hit_reuses_the_same_frame(bpm):
    page_id = bpm.allocate_page(FILE_ID)
    first = bpm.fetch_page(page_id, FILE_ID)
    second = bpm.fetch_page(page_id, FILE_ID)

    assert first is second

    bpm.unpin_page(page_id, FILE_ID)
    bpm.unpin_page(page_id, FILE_ID)


# --- pinning ----------------------------------------------------------------

def test_pin_count_tracks_fetches_and_unpins(bpm):
    page_id = bpm.allocate_page(FILE_ID)
    bpm.fetch_page(page_id, FILE_ID)
    frame_id = bpm.page_table[(FILE_ID, page_id)]
    assert bpm.pin_count[frame_id] == 1

    bpm.fetch_page(page_id, FILE_ID)
    assert bpm.pin_count[frame_id] == 2

    bpm.unpin_page(page_id, FILE_ID)
    bpm.unpin_page(page_id, FILE_ID)
    assert bpm.pin_count[frame_id] == 0


def test_unpin_below_zero_is_rejected(bpm):
    page_id = bpm.allocate_page(FILE_ID)
    bpm.fetch_page(page_id, FILE_ID)
    bpm.unpin_page(page_id, FILE_ID)

    assert bpm.unpin_page(page_id, FILE_ID) is False


def test_unpin_unknown_page_is_rejected(bpm):
    page_id = bpm.allocate_page(FILE_ID)

    assert bpm.unpin_page(page_id, FILE_ID) is False


# --- durability -------------------------------------------------------------

def test_flushed_page_is_readable_by_a_new_pool(bpm, make_bpm):
    page_id = bpm.allocate_page(FILE_ID)
    frame = bpm.fetch_page(page_id, FILE_ID)
    data = random_page()
    frame[:] = data
    bpm.unpin_page(page_id, FILE_ID, True)
    bpm.flush_page((FILE_ID, page_id))

    reopened = make_bpm()

    assert bytes(reopened.fetch_page(page_id, FILE_ID)) == data


def test_flush_all_persists_every_dirty_page(bpm, make_bpm):
    written = {}
    for _ in range(3):
        page_id = bpm.allocate_page(FILE_ID)
        frame = bpm.fetch_page(page_id, FILE_ID)
        written[page_id] = random_page()
        frame[:] = written[page_id]
        bpm.unpin_page(page_id, FILE_ID, True)
    bpm.flush_all()

    reopened = make_bpm()

    for page_id, data in written.items():
        assert bytes(reopened.fetch_page(page_id, FILE_ID)) == data


# --- eviction ---------------------------------------------------------------

def test_unpinned_pages_are_evicted_once_the_pool_is_full(bpm):
    for _ in range(NUM_FRAMES + 10):
        page_id = bpm.allocate_page(FILE_ID)
        bpm.fetch_page(page_id, FILE_ID)
        bpm.unpin_page(page_id, FILE_ID)

    assert len(bpm.page_table) <= NUM_FRAMES


def test_dirty_page_is_written_out_when_evicted(bpm):
    page_id = bpm.allocate_page(FILE_ID)
    frame = bpm.fetch_page(page_id, FILE_ID)
    data = random_page()
    frame[:] = data
    bpm.unpin_page(page_id, FILE_ID, True)


    for _ in range(NUM_FRAMES + 1):
        other = bpm.allocate_page(FILE_ID)
        bpm.fetch_page(other, FILE_ID)
        bpm.unpin_page(other, FILE_ID)

    assert (FILE_ID, page_id) not in bpm.page_table, "page was not evicted"
    assert bytes(bpm.fetch_page(page_id, FILE_ID)) == data
