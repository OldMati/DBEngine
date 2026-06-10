import pytest
from buffer.lru_k_replacer import LRUKReplacer, NUM_FRAMES, K

def test_infinity_frame_evicted_before_k_frame():
    replacer = LRUKReplacer()

    # give frame 0 K accesses
    for _ in range(K):
        replacer.record_access(0)
    replacer.set_evictable(0, True)

    # give frame 1 1 access
    replacer.record_access(1)
    replacer.set_evictable(1, True)

    assert replacer.evict() == 1

def test_oldest_infinit_frame_evicted_first():
    replacer = LRUKReplacer()

    for frame_id in range(NUM_FRAMES):
        replacer.record_access(frame_id)
        replacer.set_evictable(frame_id, True)
    

    for frame_id in range(NUM_FRAMES - 5):
        replacer.record_access(frame_id)
        replacer.set_evictable(frame_id, True)
    
    assert replacer.evict() == NUM_FRAMES - 5
    assert replacer.evict() == NUM_FRAMES - 4
    assert replacer.evict() == NUM_FRAMES - 3

def test_pinned_frame_not_evicted():
    replacer = LRUKReplacer()

    for frame_id in range(NUM_FRAMES):
        replacer.record_access(frame_id)
        replacer.set_evictable(frame_id, False)
    
    replacer.set_evictable(5, True)
    assert replacer.evict() == 5
    
def test_evict_returns_none_when_no_frames_to_evict():
    replacer = LRUKReplacer()

    for frame_id in range(NUM_FRAMES):
        replacer.record_access(frame_id)
        replacer.set_evictable(frame_id, False)
    
    assert replacer.evict() == None
