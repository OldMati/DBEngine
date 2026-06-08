from buffer.lru_k_replacer import LRUKReplacer, NUM_FRAMES
from storage.disk_manager import DiskManager, PAGE_SIZE

class BufferPoolManager:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.disk_manager = DiskManager(filepath)
        self.frames = [bytearray(PAGE_SIZE) for _ in range(NUM_FRAMES)]
        self.page_table = {}     # mapping page_id to frame_id
        self.frame_table = {}    # mapping frame_id to page_id
        self.free_frames = set([_ for _ in range(NUM_FRAMES)])   # set of free frames
        self.pin_count = [0 for _ in range(NUM_FRAMES)]
        self.dirty = [False for _ in range(NUM_FRAMES)]
        self.replacer = LRUKReplacer()
        #print('NUMBER OF FREE FRAMES: ', len(self.free_frames))
        #print('FREE FRAMES: ', NUM_FRAMES)

    
    
    def fetch_page(self, page_id: int) -> bytearray:
        #print('Buffer pool: adding page_id: ', page_id, 'to the table')
        # cache hit, return from memory
        if page_id in self.page_table:
            # print(f'cache hit, {page_id} in memory')
            self.pin_count[page_id] += 1
            self.replacer.record_access(page_id)
            return self.frames[self.page_table[page_id]]

        # find a free frame
        if self.free_frames:
            frame_id = self.free_frames.pop()
        else:
            frame_id = self.replacer.evict()
            old_page_id = self.frame_table[frame_id]
            self.page_table.pop(old_page_id)
            if self.dirty[frame_id]:
                self.disk_manager.write_page(self.frames[frame_id])
        
        # update the tables
        self.frame_table[frame_id] = page_id
        self.page_table[page_id] = frame_id
        self.frames[frame_id] = self.disk_manager.read_page(page_id)

        self.pin_count[frame_id] = 1
        self.dirty[frame_id] = False
        #print('FRAME ID: ', frame_id)
        self.replacer.record_access(frame_id)
        self.replacer.set_evictable(frame_id, False)

        # read the page from disc
        self.disk_manager.read_page(page_id)

        #print(f'Page {page_id} raw: ', self.frames[frame_id][:20])
        return self.frames[frame_id]
    
    def unpin_page(self, page_id: int, is_dirty: bool = False):
        #print('Buffer pool: removing ', page_id, 'from the table')
        if page_id not in self.page_table:
            return False

        frame_id = self.page_table[page_id]

        if self.pin_count[frame_id] == 0:
            return False
    
        self.pin_count[frame_id] -= 1

        if is_dirty:
            self.dirty[frame_id] = True
        
        if self.pin_count[frame_id] == 0:
            # print("PAGE IS EVICTABLE!")
            self.replacer.set_evictable(frame_id, True)

    def flush_page(self, page_id):
        #print('FLUSHING PAGE_id: ', page_id)
        if page_id not in self.page_table:
            return False
        
        frame_id = self.page_table[page_id]

        #print('sending page to disk manager to write')
        self.disk_manager.write_page(page_id, self.frames[frame_id])
        self.dirty[frame_id] = False

    def allocate_page(self) -> int:
        page_id = self.disk_manager.allocate_page()
        #page_raw = bytearray(PAGE_SIZE)
        return page_id #page_raw
        

    def close(self):
        for frame_id in range(NUM_FRAMES):
            if self.dirty[frame_id]:
                self.flush_page(self.frame_table[frame_id])
        self.disk_manager.close()