from collections import deque

NUM_FRAMES = 1024
K = 2

class LRUKReplacer:

    def __init__(self):
        self.history = [deque(maxlen=K) for i in range(NUM_FRAMES)]
        self.evictable = set()
        self.current_time = 0

    def record_access(self, frame_id: int):
        self.history[frame_id].append(self.current_time)
        self.current_time += 1
    
    def set_evictable(self, frame_id:int, evictable: bool):
        if evictable:
            self.evictable.add(frame_id)
        else:
            self.evictable.discard(frame_id)
        
    def evict(self) -> int | None:
        # no frames to evict
        if len(self.evictable) == 0:
            return None
        
        evict_id = 0
        last_use = float('inf')
        found_inf = False

        # find the frame to evict
        for frame_id in self.evictable:
            queue = self.history[frame_id]

            if len(queue) < K:
                if not found_inf or queue[0] < last_use:
                    found_inf = True
                    last_use = queue[0]
                    evict_id = frame_id
            elif not found_inf:
                if queue[0] < last_use:
                    last_use = queue[0]
                    evict_id = frame_id

        self.evictable.remove(evict_id)
        self.history[evict_id] = deque(maxlen=K)
        return evict_id