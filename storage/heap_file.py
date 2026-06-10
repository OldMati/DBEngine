from buffer.buffer_pool import BufferPoolManager
from storage.page import Page
from storage.directory_page import DirectoryPage

class HeapFile:

    # first page: directory
    # page_id >= 1: db
    def __init__(self, filepath):
        self.bpm = BufferPoolManager(filepath)
        self.directory_id = 0
    
    def insert_tuple(self, data: bytes) -> tuple[int, int]:
        # load the directory
        dir_raw = self.bpm.fetch_page(self.directory_id)
        directory = DirectoryPage(dir_raw)
        # print('DIRECTORY FREE SPACE: ', directory.free_space)
        page_id = None
        new_page = False

        # find a page with enough space
        size = len(data) + Page.HEADER_SIZE
        page_id = directory.find_page_with_enough_space(size)
        
        if not page_id:
            print('no page has enough space, allocate new page')
            # no page has enough space, allocate new page
            page_id = self.bpm.allocate_page()
            directory.increase_page_count()
            #print('ALLOCATE NEW PAGE_ID: ', page_id)
            new_page = True


        page_raw = self.bpm.fetch_page(page_id)
        #print('page_raw: ', page_raw[:20])
        page = Page(page_raw, new_page)
        slot_id = page.insert_tuple(data)

        self.bpm.unpin_page(page_id, True)

        # update the directory
        directory.update_directory(page_id, page.free_space, page.num_slots)
        self.bpm.unpin_page(self.directory_id, True)
        return (page_id, slot_id)

    def get_tuple(self, page_id: int, slot_id: int) -> bytes:
        page_raw = self.bpm.fetch_page(page_id)
        #print(page_raw)
        page = Page(page_raw)
        self.bpm.unpin_page(page_id)
        data = page.get_tuple(slot_id)
        return data

    def scan(self):
        pass

    def close(self):
        self.bpm.close()

    def create_directory(self):
        # create a new DirectoryPage object
        page_id = self.bpm.allocate_page()
        dir_raw = self.bpm.fetch_page(page_id)
        directory = DirectoryPage(dir_raw, True)
        self.bpm.unpin_page(page_id)
        self.bpm.flush_page(page_id)
    
    def _get_page_count(self):
        dir_raw = self.bpm.fetch_page(self.directory_id)
        directory = DirectoryPage(dir_raw)
        self.bpm.unpin_page(self.directory_id)
        return directory.page_count
