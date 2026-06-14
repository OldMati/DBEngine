import pytest
from storage.directory_page import DirectoryPage, PAGE_SIZE

def set_up_directory():
    directory = DirectoryPage(bytearray(PAGE_SIZE), True)
    return directory


def test_create_directory():
    directory = set_up_directory()
    assert directory.page_count == 1
    assert len(directory.free_space) == 1

def test_increase_page_count():
    directory = set_up_directory()
    page_count = directory.page_count

    for _ in range(50):
        directory.increase_page_count(_)
    
    assert directory.page_count == page_count + 50

def test_update_directory():
    directory = set_up_directory()
    for _ in range(50):
        directory.increase_page_count(_)
    page_count = directory.page_count

    print('page_count: ', page_count)
    assert directory.update_directory(0, 0, 0) == False
    assert directory.update_directory(1, 0, 0) == None
    assert directory.update_directory(page_count - 1, 1, 4000) == None
    assert directory.update_directory(page_count - 3, 5, 1000) == None
    assert directory.update_directory(1, 4000, 1) == None
    assert directory.update_directory(page_count, 4000, 1) == False
    assert directory.update_directory(page_count + 30, 4000, 1) == False
    assert directory.update_directory(3, -5, 1) == False
    assert directory.update_directory(3, -5, -3) == False
    assert directory.update_directory(3, 3, -3) == False

