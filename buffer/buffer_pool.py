from buffer.lru_k_replacer import LRUKReplacer, NUM_FRAMES
from storage.disk_manager import DiskManager, PAGE_SIZE

class BufferPoolManager:

    def __init__(self):
        self.frames = [bytearray(PAGE_SIZE) for _ in range(NUM_FRAMES)]
        self.page_table = {}     # mapping (file_id, page_id) to frame_id
        self.frame_table = {}    # mapping frame_id to (file_id, page_id)
        self.free_frames = set([_ for _ in range(NUM_FRAMES)])   # set of free frames
        self.pin_count = [0 for _ in range(NUM_FRAMES)] # pin count per frame_id
        self.dirty = [False for _ in range(NUM_FRAMES)]
        self.replacer = LRUKReplacer()
        self.disk_manager = DiskManager()
    
    def fetch_page(self, page_id: int, file_id: int) -> bytearray:
        # cache hit, return from memory
        if (file_id, page_id) in self.page_table:
            frame_id = self.page_table[(file_id, page_id)]
            self.pin_count[frame_id] += 1
            self.replacer.record_access(frame_id)
            self.replacer.set_evictable(frame_id, False)
            return self.frames[frame_id]


        # find a free frame
        if self.free_frames:
            frame_id = self.free_frames.pop()
        else:
            frame_id = self.replacer.evict()
            (old_file_id, old_page_id) = self.frame_table[frame_id]
            if (old_file_id, old_page_id) in self.page_table:
                self.page_table.pop((old_file_id, old_page_id))
            if self.dirty[frame_id]:
                self.disk_manager.write_page(old_page_id, old_file_id, self.frames[frame_id])
        
        # update the tables
        self.frame_table[frame_id] = (file_id, page_id)
        self.page_table[(file_id, page_id)] = frame_id

        # read the page
        self.frames[frame_id] = self.disk_manager.read_page(page_id, file_id)

        self.pin_count[frame_id] = 1
        self.dirty[frame_id] = False

        self.replacer.record_access(frame_id)
        self.replacer.set_evictable(frame_id, False)

        return self.frames[frame_id]
    
    def unpin_page(self, page_id: int, file_id: int, is_dirty: bool = False):
        if (file_id, page_id) not in self.page_table:
            return False

        frame_id = self.page_table[(file_id, page_id)]

        if self.pin_count[frame_id] == 0:
            return False
    
        self.pin_count[frame_id] -= 1

        if is_dirty:
            self.dirty[frame_id] = True
        
        if self.pin_count[frame_id] == 0:
            self.replacer.set_evictable(frame_id, True)

    def flush_page(self, rid: tuple[int, int]):
        if rid not in self.page_table:
            return False
        
        frame_id = self.page_table[rid]

        (file_id, page_id) = rid
        self.disk_manager.write_page(page_id, file_id, self.frames[frame_id])
        self.dirty[frame_id] = False

    def allocate_page(self, file_id: int) -> int:
        page_id = self.disk_manager.allocate_page(file_id)
        return page_id
        
    def flush_all(self):
        for frame_id in range(NUM_FRAMES):
            if self.dirty[frame_id]:
                self.flush_page(self.frame_table[frame_id])

    def close(self):
        for frame_id in range(NUM_FRAMES):
            if self.dirty[frame_id]:
                self.flush_page(self.frame_table[frame_id])
        self.disk_manager.close()