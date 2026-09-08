import random

import pytest

from storage.disk_manager import PAGE_SIZE, DiskManager

FILE_ID = 996
OTHER_FILE_ID = 995


def random_page():
    return random.randbytes(PAGE_SIZE)


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def make_dm(tmp_path, monkeypatch):
    """Factory for disk managers over one throwaway directory.

    Several can be opened against the same files (to test durability);
    all are closed after the test.
    """
    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    managers = []

    def _make():
        dm = DiskManager()
        managers.append(dm)
        return dm

    yield _make
    for dm in managers:
        dm.close()


@pytest.fixture
def dm(make_dm):
    return make_dm()


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


# --- allocation -------------------------------------------------------------

def test_allocate_page_returns_sequential_ids(dm):
    ids = [dm.allocate_page(FILE_ID) for _ in range(5)]

    assert ids == [0, 1, 2, 3, 4]


def test_allocate_page_grows_the_file_by_one_page(dm, data_dir):
    for _ in range(3):
        dm.allocate_page(FILE_ID)

    assert (data_dir / f"{FILE_ID}.db").stat().st_size == 3 * PAGE_SIZE


def test_allocated_page_is_zeroed(dm):
    page_id = dm.allocate_page(FILE_ID)

    assert bytes(dm.read_page(page_id, FILE_ID)) == bytes(PAGE_SIZE)


# --- reading and writing ----------------------------------------------------

def test_write_then_read_returns_the_same_bytes(dm):
    page_id = dm.allocate_page(FILE_ID)
    data = random_page()
    dm.write_page(page_id, FILE_ID, data)

    assert bytes(dm.read_page(page_id, FILE_ID)) == data


def test_writes_to_different_pages_do_not_overlap(dm):
    first = dm.allocate_page(FILE_ID)
    second = dm.allocate_page(FILE_ID)
    a, b = random_page(), random_page()

    dm.write_page(first, FILE_ID, a)
    dm.write_page(second, FILE_ID, b)

    assert bytes(dm.read_page(first, FILE_ID)) == a
    assert bytes(dm.read_page(second, FILE_ID)) == b


def test_overwriting_a_page_replaces_its_contents(dm):
    page_id = dm.allocate_page(FILE_ID)
    dm.write_page(page_id, FILE_ID, random_page())
    latest = random_page()

    dm.write_page(page_id, FILE_ID, latest)

    assert bytes(dm.read_page(page_id, FILE_ID)) == latest


def test_read_past_the_end_of_the_file_returns_a_blank_page(dm):
    dm.allocate_page(FILE_ID)

    assert bytes(dm.read_page(50, FILE_ID)) == bytes(PAGE_SIZE)


# --- file isolation ---------------------------------------------------------

def test_files_with_different_ids_are_independent(dm):
    dm.allocate_page(FILE_ID)
    dm.allocate_page(OTHER_FILE_ID)
    a, b = random_page(), random_page()

    dm.write_page(0, FILE_ID, a)
    dm.write_page(0, OTHER_FILE_ID, b)

    assert bytes(dm.read_page(0, FILE_ID)) == a
    assert bytes(dm.read_page(0, OTHER_FILE_ID)) == b


def test_page_ids_restart_for_each_file(dm):
    assert dm.allocate_page(FILE_ID) == 0
    assert dm.allocate_page(OTHER_FILE_ID) == 0


# --- durability -------------------------------------------------------------

def test_data_survives_a_new_disk_manager(dm, make_dm):
    page_id = dm.allocate_page(FILE_ID)
    data = random_page()
    dm.write_page(page_id, FILE_ID, data)
    dm.close()

    reopened = make_dm()

    assert bytes(reopened.read_page(page_id, FILE_ID)) == data


def test_page_count_survives_a_new_disk_manager(dm, make_dm):
    for _ in range(3):
        dm.allocate_page(FILE_ID)
    dm.close()

    reopened = make_dm()

    assert reopened.allocate_page(FILE_ID) == 3