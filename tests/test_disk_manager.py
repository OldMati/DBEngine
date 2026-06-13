import pytest
from storage.disk_manager import DiskManager, PAGE_SIZE
import os

filepath = 'data/999.db'
file_id = 999

def test_write_read_page():
    os.remove(filepath)
    disk_manager = DiskManager()
    test_count = 30
    page_id_table = {}

    # write pages to disk
    for _ in range(test_count):
        page = os.urandom(PAGE_SIZE)
        page_id = disk_manager.allocate_page(file_id)
        assert page_id not in page_id_table and type(page_id) == int
        disk_manager.write_page(page_id, file_id, page)
        page_id_table[page_id] = page
    
    # assert all pages have been written
    assert len(page_id_table) == test_count
    # read pages from disk manager
    for page_id in page_id_table:
        assert page_id_table[page_id] == disk_manager.read_page(page_id, file_id)

def test_reading_after_reopening_file():
    os.remove(filepath)
    disk_manager = DiskManager()

    test_count = 30
    page_id_table = {}

    # write pages to disk
    for _ in range(test_count):
        page = os.urandom(PAGE_SIZE)
        page_id = disk_manager.allocate_page(file_id)
        assert page_id not in page_id_table and type(page_id) == int
        disk_manager.write_page(page_id, file_id, page)
        page_id_table[page_id] = page
    
    # assert all pages have been written
    assert len(page_id_table) == test_count
    
    for page_id in page_id_table:
        assert page_id_table[page_id] == disk_manager.read_page(page_id, file_id)
    

