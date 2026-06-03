from buffer.lru_k_replacer import LRUKReplacer, NUM_FRAMES
from storage.disk_manager import DiskManager, PAGE_SIZE

class BufferPoolManager:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.disk_manager = DiskManager(filepath)
        self.frames = [bytearray(PAGE_SIZE) for _ in range(NUM_FRAMES)]
        self.page_table = {}     # mapping page_id to frame_id
        self.frame_table = {}    # mapping frame_id to page_id
        self.free_frames = set(0 for _ in range(NUM_FRAMES))   # set of free frames
        self.pin_count = [0 for _ in range(NUM_FRAMES)]
        self.dirty = [False for _ in range(NUM_FRAMES)]
        self.replacer = LRUKReplacer()
    
    def fetch_page(self, page_id: int):
        if page_id in self.page_table:
            self.pin_count[page_id] += 1
            self.replacer.record_access(page_id)
            return self.frames[self.page_table[page_id]]

        if self.free_frames:
            frame_id = self.free_frames.pop()
        else:
            print("NO FREE FRAMES")
            frame_id = self.replacer.evict()
            old_page_id = self.frame_table[frame_id]
            self.page_table.pop(old_page_id)
            if self.dirty[frame_id]:
                self.disk_manager.write_page(self.frames[frame_id])
        
        
        
        
        self.frame_table[frame_id] = page_id
        self.page_table[page_id] = frame_id
        self.frames[frame_id] = self.disk_manager.read_page(page_id)

        self.pin_count[frame_id] = 1
        self.dirty[frame_id] = False
        self.replacer.record_access(frame_id)
        self.replacer.set_evictable(frame_id, False)

        self.disk_manager.read_page(page_id)

        return self.frames[frame_id]
    
    def unpin_page(self, page_id: int, is_dirty: bool = False):
        if page_id not in self.page_table:
            return False

        frame_id = self.frame_table[page_id]

        if self.pin_count[frame_id] == 0:
            return False
    
        self.pin_count[frame_id] -= 1

        if is_dirty:
            print("######### IS DIRTY!! ")
            self.dirty[frame_id] = True
        
        if self.pin_count[frame_id] == 0:
            print("PAGE IS EVICTABLE!")
            self.replacer.set_evictable(frame_id, True)

    def flush_page(self, page_id):
        if page_id not in self.page_table:
            return False
        
        frame_id = self.page_table[page_id]

        self.disk_manager.write_page(page_id, self.frames[frame_id])
        self.dirty[frame_id] = False


    def close(self):
        for frame_id in range(NUM_FRAMES):
            if self.dirty[frame_id]:
                self.flush_page(self.frame_table[frame_id])
        self.disk_manager.close()
        