import pytest
from storage.page import Page
import os
import random as rn

page = Page(bytearray(Page.PAGE_SIZE), new_page=True)

def test_insert_get_tuples():
    slot_id_table = {}

    # write tuples to page
    for _ in range(20):
        size = rn.randint(50, 100)
        row = os.urandom(size)
        slot_id = page.insert_tuple(row)
        assert slot_id not in slot_id_table and type(slot_id) == int
        slot_id_table[slot_id] = row
    
    # read tuples from page
    for slot_id in slot_id_table:
        assert slot_id_table[slot_id] == page.get_tuple(slot_id)

def test_delete():
    assert type(page.get_tuple(1)) == bytearray
    page.delete_tuple(1)
    assert page.get_tuple(1) == None


    assert type(page.get_tuple(19)) == bytearray
    page.delete_tuple(19)
    assert page.get_tuple(19) == None
