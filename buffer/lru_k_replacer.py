from collections import deque

NUM_FRAMES = 20
K = 2

class LRUKReplacer:

    def __init__(self):
        self.history = {
            i: deque(maxlen=K) for i in range(NUM_FRAMES)
        }
        self.evictable = set()
        self.current_time = 0

    def record_access(self, frame_id: int):
        #print(self.history)
        self.history[frame_id].append(self.current_time)
        self.current_time += 1
    
    def set_evictable(self, frame_id:int, evictable: bool):
        if evictable:
            self.evictable.add(frame_id)
        else:
            self.evictable.discard(frame_id)
        
    def evict(self) -> int:
        evict_id = 0
        last_use = self.current_time
        found_infinity = False

        for frame_id in self.evictable:
            queue = self.history[frame_id]
            if len(queue) < K:
                if found_infinity and queue[0] < last_use or not found_infinity:
                    found_infinity = True
                    last_use = queue[0]
                    evict_id = frame_id
                    continue
            if found_infinity:
                continue
                
            if queue[0] < last_use:
                last_use = queue[0]
                evict_id = frame_id

        #print('Evicting page with frame_id: ', evict_id)
        self.evictable.discard(evict_id)
        self.history[evict_id] = deque(maxlen=K)
        #print('Evict_id: ', evict_id)
        return evict_id