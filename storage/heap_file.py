from storage.disk_manager import DiskManager
from storage.page import Page

class HeapFile:

    def __init__(self, filepath):
        self.disk_manager = DiskManager(filepath)

        if self.disk_manager.num_pages == 0:
            self.disk_manager.allocate_page()
            page = Page()
            self.disk_manager.write_page(0, page.page)
    
    def insert_tuple(self, data: bytes) -> tuple[int, int]:
        # assume the first page has enough memory:
        page_id = 0

        # read the page into memory
        page_raw = self.disk_manager.read_page(page_id)
        page = Page(page_raw)
        print('page: numslots, freespace, pointer:', page.num_slots, page.free_space, page.free_space_pointer)
        slot_id = page.insert_tuple(data)
        self.disk_manager.write_page(page_id, page.page)
        return (page_id, slot_id)

    def get_tuple(self, page_id: int, slot_id: int) -> bytes:
        page_raw = self.disk_manager.read_page(page_id)
        page = Page(page_raw)
        data = page.get_tuple(slot_id)

        return data


    def scan(self):
        pass

    def close(self):
        self.disk_manager.close()