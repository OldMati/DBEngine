from buffer.buffer_pool import BufferPoolManager
from storage.page import Page

class HeapFile:

    def __init__(self, filepath):
        self.bpm = BufferPoolManager(filepath)

    
    def insert_tuple(self, data: bytes) -> tuple[int, int]:
        page_id = 0

        page_raw = self.bpm.fetch_page(page_id)
        page = Page(page_raw)
        slot_id = page.insert_tuple(data)
        self.bpm.unpin_page(page_id, True)
        return (page_id, slot_id)

    def get_tuple(self, page_id: int, slot_id: int) -> bytes:
        page_raw = self.bpm.fetch_page(page_id)
        page = Page(page_raw)
        self.bpm.unpin_page(page_id)
        data = page.get_tuple(slot_id)

        return data


    def scan(self):
        pass

    def close(self):
        self.bpm.close()