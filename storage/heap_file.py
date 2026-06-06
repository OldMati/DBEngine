from buffer.buffer_pool import BufferPoolManager
from storage.page import Page
from storage.directory_page import DirectoryPage

class HeapFile:

    # first page: directory
    # page_id >= 1: db
    def __init__(self, filepath):
        self.bpm = BufferPoolManager(filepath)
        self.freespace = []
        self.directory_id = 0
    
    def insert_tuple(self, data: bytes) -> tuple[int, int]:
        # load the directory
        dir_raw = self.bpm.fetch_page(self.directory_id)
        directory = DirectoryPage(dir_raw)
        print('DIRECTORY FREE SPACE: ', directory.free_space)
        page_id = None
        new_page = False

        # find a page with enough space
        size = len(data) + Page.HEADER_SIZE
        for i in range(directory.page_count):
            if directory.free_space[i] >= size:
                page_id = i
                print('HeapFile, PageID with enough space: ', page_id, 'space available: ', directory.free_space[page_id])
                break
        
        if not page_id:
            print('no page has enough space, allocate new page')
            # no page has enough space, allocate new page
            page_id, page_raw = self.bpm.allocate_page()
            directory.update_num_pages(page_id + 1)
            #print('ALLOCATE NEW PAGE_ID: ', page_id)
            new_page = True


        ## FIX HANDLING OF PAGE_RAW, DECIDE WHETHER NO BYTES SHOULD BE SOLVED BY ALLOCATING OR READING
        page_raw = self.bpm.fetch_page(page_id)
        #print('page_raw: ', page_raw[:20])
        page = Page(page_raw, new_page)
        slot_id = page.insert_tuple(data)
        print('slot_id: ', slot_id, 'page_id: ', page_id)

        self.bpm.unpin_page(page_id, True)

        # update the directory
        directory.update_directory(page_id, page.free_space, page.num_slots)
        self.bpm.unpin_page(self.directory_id, True)
        return (page_id, slot_id)

    def get_tuple(self, page_id: int, slot_id: int) -> bytes:
        # get directory


        page_raw = self.bpm.fetch_page(page_id)
        page = Page(page_raw)
        self.bpm.unpin_page(page_id)
        data = page.get_tuple(slot_id)

        # unpin directory

        return data

    # def fetch_directory(self):
    #     directory = DirectoryPage()
    #     dir_raw = self.bpm.fetch_page(self.directory_id)
    #     self.free_space = DirectoryPage(dir_raw)
    #     self.bpm.unpin_page(self.directory_id)

    def scan(self):
        pass

    #def allocate_page(self):
        #return page_id, page_raw

    def close(self):
        self.bpm.close()

    def create_directory(self):
        # create a new DirectoryPage object
        dir_raw = self.bpm.fetch_page(0)
        directory = DirectoryPage(dir_raw)
        directory.createDirectory()
        self.bpm.flush_page(0)

        

