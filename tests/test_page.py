import os
import random

import pytest

from storage.page import Page


def random_row(size=None):
    return os.urandom(size if size is not None else random.randint(50, 100))


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def raw():
    return bytearray(Page.PAGE_SIZE)


@pytest.fixture
def page(raw):
    return Page(raw, new_page=True)


@pytest.fixture
def populated_page(page):
    rows = {}
    for _ in range(20):
        row = random_row()
        rows[page.insert_tuple(row)] = row
    page.rows = rows
    return page


# --- creation ---------------------------------------------------------------

def test_new_page_is_empty(page):
    assert page.num_slots == 0
    assert page.free_space == Page.PAGE_SIZE - Page.HEADER_SIZE


# --- insert and read back ---------------------------------------------------

def test_inserted_tuple_is_readable_by_slot_id(page):
    row = random_row()

    slot_id = page.insert_tuple(row)

    assert page.get_tuple(slot_id) == row


def test_slot_ids_are_sequential_from_zero(page):
    slot_ids = [page.insert_tuple(random_row()) for _ in range(20)]

    assert slot_ids == list(range(20))


def test_all_tuples_remain_readable_after_later_inserts(populated_page):
    for slot_id, row in populated_page.rows.items():
        assert populated_page.get_tuple(slot_id) == row


def test_insert_reduces_free_space_by_tuple_and_slot(page):
    before = page.free_space
    row = random_row(80)

    page.insert_tuple(row)

    assert page.free_space == before - len(row) - Page.SLOT_SIZE


def test_get_tuple_beyond_the_last_slot_returns_none(populated_page):
    assert populated_page.get_tuple(populated_page.num_slots) is None


# --- delete -----------------------------------------------------------------

def test_delete_reports_success_and_hides_the_tuple(populated_page):
    assert populated_page.delete_tuple(1) is True
    assert populated_page.get_tuple(1) is None


def test_deleting_twice_reports_failure(populated_page):
    populated_page.delete_tuple(1)

    assert populated_page.delete_tuple(1) is False


def test_delete_leaves_neighbouring_slots_intact(populated_page):
    rows = populated_page.rows

    populated_page.delete_tuple(1)

    assert populated_page.get_tuple(0) == rows[0]
    assert populated_page.get_tuple(2) == rows[2]


def test_delete_does_not_shift_later_slot_ids(populated_page):
    rows = populated_page.rows

    populated_page.delete_tuple(0)

    assert populated_page.get_tuple(19) == rows[19]


# --- scan -------------------------------------------------------------------

def test_scan_yields_every_tuple(populated_page):
    assert dict(populated_page.scan()) == populated_page.rows


def test_scan_of_an_empty_page_yields_nothing(page):
    assert list(page.scan()) == []


def test_scan_skips_deleted_tuples(populated_page):
    populated_page.delete_tuple(5)

    scanned = dict(populated_page.scan())

    assert 5 not in scanned
    assert scanned == {k: v for k, v in populated_page.rows.items() if k != 5}


# --- persistence ------------------------------------------------------------

def test_tuples_survive_reload(populated_page, raw):
    reloaded = Page(raw)

    for slot_id, row in populated_page.rows.items():
        assert reloaded.get_tuple(slot_id) == row


def test_header_survives_reload(populated_page, raw):
    reloaded = Page(raw)

    assert reloaded.num_slots == populated_page.num_slots
    assert reloaded.free_space == populated_page.free_space
    assert reloaded.free_space_pointer == populated_page.free_space_pointer


def test_deletions_survive_reload(populated_page, raw):
    populated_page.delete_tuple(3)

    assert Page(raw).get_tuple(3) is None
