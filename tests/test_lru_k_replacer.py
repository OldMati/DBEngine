import pytest

from buffer.lru_k_replacer import K, NUM_FRAMES, LRUKReplacer


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def replacer():
    return LRUKReplacer()


def touch(replacer, frame_id, times=1, evictable=True):
    """Record `times` accesses for a frame and set its evictability."""
    for _ in range(times):
        replacer.record_access(frame_id)
    replacer.set_evictable(frame_id, evictable)


# --- availability -----------------------------------------------------------

def test_evict_returns_none_when_nothing_has_been_recorded(replacer):
    assert replacer.evict() is None


def test_evict_returns_none_when_every_frame_is_pinned(replacer):
    for frame_id in range(NUM_FRAMES):
        touch(replacer, frame_id, evictable=False)

    assert replacer.evict() is None


def test_only_evictable_frames_are_candidates(replacer):
    for frame_id in range(NUM_FRAMES):
        touch(replacer, frame_id, evictable=False)
    replacer.set_evictable(5, True)

    assert replacer.evict() == 5


def test_frame_made_unevictable_again_is_not_returned(replacer):
    touch(replacer, 3)
    replacer.set_evictable(3, False)

    assert replacer.evict() is None


# --- choosing a victim ------------------------------------------------------

def test_frame_with_fewer_than_k_accesses_is_evicted_first(replacer):
    touch(replacer, 0, times=K)  # has a full history
    touch(replacer, 1)           # has only one access

    assert replacer.evict() == 1


def test_oldest_of_the_under_k_frames_is_evicted_first(replacer):
    for frame_id in range(NUM_FRAMES):
        touch(replacer, frame_id)
    # Give everything below NUM_FRAMES - 5 a second access, so only the last
    # five still have fewer than K, in the order they were first seen.
    for frame_id in range(NUM_FRAMES - 5):
        touch(replacer, frame_id)

    assert replacer.evict() == NUM_FRAMES - 5
    assert replacer.evict() == NUM_FRAMES - 4
    assert replacer.evict() == NUM_FRAMES - 3


def test_among_full_histories_the_oldest_kth_access_is_evicted(replacer):
    touch(replacer, 0, times=K)
    touch(replacer, 1, times=K)
    touch(replacer, 2, times=K)
    # Refresh frame 0, pushing its k-th access forward past the others.
    touch(replacer, 0, times=K)

    assert replacer.evict() == 1


def test_recent_access_protects_a_frame_from_eviction(replacer):
    touch(replacer, 0, times=K)
    touch(replacer, 1, times=K)
    touch(replacer, 0, times=K)

    assert replacer.evict() != 0


# --- state after eviction ---------------------------------------------------

def test_evicted_frame_is_not_returned_twice(replacer):
    touch(replacer, 0)
    touch(replacer, 1)

    first = replacer.evict()

    assert replacer.evict() != first


def test_evicting_every_frame_returns_each_exactly_once(replacer):
    for frame_id in range(NUM_FRAMES):
        touch(replacer, frame_id)

    evicted = [replacer.evict() for _ in range(NUM_FRAMES)]

    assert sorted(evicted) == list(range(NUM_FRAMES))
    assert replacer.evict() is None


def test_evicted_frame_history_is_cleared(replacer):
    touch(replacer, 0, times=K)
    touch(replacer, 1, times=K)
    replacer.evict()

    # Frame 0 comes back as a fresh frame with one access, so it should now
    # look younger than frame 1 in k-distance terms but older in the under-K
    # sense — it should be picked first.
    touch(replacer, 0)

    assert replacer.evict() == 0