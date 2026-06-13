from buffer.buffer_pool import BufferPoolManager
from storage.page import Page
from storage.directory_page import DirectoryPage

class HeapFile:

    # first page: directory
    # page_id >= 1: db
    def __init__(self, bpm: BufferPoolManager, file_id: int):
        self.bpm = bpm
        self.directory_id = 0
        self.file_id = file_id
    
    def insert_tuple(self, data: bytes) -> tuple[int, int]:

        # load the directory
        dir_raw = self.bpm.fetch_page(self.directory_id, self.file_id)
        directory = DirectoryPage(dir_raw)
        page_id = None
        new_page = False

        # find a page with enough space
        size = len(data) + Page.HEADER_SIZE
        page_id = directory.find_page_with_enough_space(size)
        
        if not page_id:
            # no page has enough space, allocate new page
            page_id = self.bpm.allocate_page(self.file_id)
            directory.increase_page_count(page_id)
            print('ALLOCATE NEW PAGE_ID: ', page_id)
            print('dir.freespace: ', directory.free_space)
            new_page = True


        page_raw = self.bpm.fetch_page(page_id, self.file_id)
        #print('page_raw: ', page_raw[:20])
        page = Page(page_raw, new_page)
        slot_id = page.insert_tuple(data)

        self.bpm.unpin_page(page_id, True)

        # update the directory
        directory.update_directory(page_id, page.free_space, page.num_slots)
        self.bpm.unpin_page(self.directory_id, True)

        print('dir.freespace: ', directory.free_space)
        return (page_id, slot_id)

    def get_tuple(self, rid: tuple[int, int]) -> bytes:
        page_id = rid[0]
        slot_id = rid[1]
        page_raw = self.bpm.fetch_page(page_id, self.file_id)
        #print(page_raw)
        page = Page(page_raw)
        self.bpm.unpin_page(page_id, self.file_id)
        raw = page.get_tuple(slot_id)

        return raw
    
    def delete_tuple(self, rid: tuple[int, int]) -> bool:
        page_id = rid[0]
        slot_id = rid[1]
        page_raw = self.bpm.fetch_page(page_id, self.file_id)
        page = Page(page_raw)
        deleted = page.delete_tuple(slot_id)
        self.bpm.unpin_page(page_id, self.file_id, deleted)
        return deleted

    def scan(self):
        # load the directory
        dir_raw = self.bpm.fetch_page(self.directory_id, self.file_id)
        directory = DirectoryPage(dir_raw)
        self.bpm.unpin_page(self.directory_id, self.file_id)
        page_count = directory.page_count

        # loop over all pages
        for page_id in range(1, page_count):
            # read the page
            page_raw = self.bpm.fetch_page(page_id, self.file_id)
            page = Page(page_raw)
            self.bpm.unpin_page(page_id, self.file_id)
            # scan the page
            for slot_id, raw in page.scan():
                # yield rid, raw
                yield (page_id, slot_id), raw
        
    def close(self):
        self.bpm.close()

    def create_directory(self):
        # create a new DirectoryPage object
        page_id = self.bpm.allocate_page(self.file_id)
        dir_raw = self.bpm.fetch_page(page_id, self.file_id)
        directory = DirectoryPage(dir_raw, True)
        self.bpm.unpin_page(page_id, self.file_id)
        self.bpm.flush_page((self.file_id, page_id))
    
    def _get_page_count(self):
        dir_raw = self.bpm.fetch_page(self.directory_id, self.file_id)
        directory = DirectoryPage(dir_raw)
        self.bpm.unpin_page(self.directory_id, self.file_id)
        return directory.page_count
