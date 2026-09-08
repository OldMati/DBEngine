import pytest

from storage.directory_page import PAGE_SIZE, DirectoryPage


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def raw():
    """The backing buffer, kept separate so tests can reload from it."""
    return bytearray(PAGE_SIZE)


@pytest.fixture
def directory(raw):
    return DirectoryPage(raw, new_directory=True)


@pytest.fixture
def populated_directory(directory):
    """A directory with 50 pages added, ids 1..50."""
    for page_id in range(1, 51):
        directory.increase_page_count(page_id)
    return directory


# --- creation ---------------------------------------------------------------

def test_new_directory_holds_only_itself(directory):
    assert directory.page_count == 1
    assert directory.free_space == {0: 0}


# --- adding pages -----------------------------------------------------------

def test_each_new_page_increments_the_count(directory):
    for page_id in range(1, 51):
        directory.increase_page_count(page_id)

    assert directory.page_count == 51


def test_new_page_starts_entirely_free(directory):
    directory.increase_page_count(1)

    assert directory.free_space[1] == PAGE_SIZE


# --- updating entries -------------------------------------------------------

def test_update_records_free_space(populated_directory):
    populated_directory.update_directory(1, 1000, 7)

    assert populated_directory.free_space[1] == 1000


def test_update_accepts_the_last_page(populated_directory):
    last = populated_directory.page_count - 1

    assert populated_directory.update_directory(last, 1, 4000) is None


def test_update_rejects_the_directory_page_itself(populated_directory):
    assert populated_directory.update_directory(0, 0, 0) is False


@pytest.mark.parametrize("offset", [0, 30])
def test_update_rejects_pages_that_do_not_exist(populated_directory, offset):
    page_id = populated_directory.page_count + offset

    assert populated_directory.update_directory(page_id, 4000, 1) is False


@pytest.mark.parametrize(
    "free_space, tuple_count",
    [(-5, 1), (3, -3), (-5, -3)],
)
def test_update_rejects_negative_values(populated_directory, free_space, tuple_count):
    assert populated_directory.update_directory(3, free_space, tuple_count) is False


# --- persistence ------------------------------------------------------------

def test_page_count_survives_reload(populated_directory, raw):
    assert DirectoryPage(raw).page_count == populated_directory.page_count