import struct

# max children per node
ORDER = 100

# internal node: [is_leaf(1) | page_id(4) | num_keys(2) | n+1 pointers(4 each) | n keys(4 each)]
# leaf node: [is_leaf(1) | page_id(4) | num_keys(2) | prev_leaf(4) | next_leaf(4) | n keys(4 each) | n rids(8 each)]

class BTreePage:
    page_id: int
    page_raw: bytearray
    is_leaf: bool
    num_keys: int
    pointers: list[int] | None
    keys: list[int]
    next_leaf: int | None
    prev_leaf: int | None
    RIDs: list[tuple[int, int]] | None

    def __init__(self, raw, new_page: bool = False, page_id: int | None = None, is_leaf: int | None = None):
        self.page_raw = raw
        self.keys = []
        if not new_page:
            self.deserialize()
            return

        # is new page
        self.num_keys = 0
        self.page_id = page_id
        self.is_leaf = is_leaf

        if is_leaf:
            self.RIDs = []
            self.next_leaf = -1
            self.prev_leaf = - 1
        else:
            self.pointers = []


    def serialize(self):
        raw = self.page_raw
        assert type(raw) == bytearray
        # write is_lead, page_id and num_keys
        struct.pack_into('?', raw, 0, self.is_leaf)
        struct.pack_into('I', raw, 1, self.page_id)
        struct.pack_into('H', raw, 5, self.num_keys)

        offset = 7
        n = self.num_keys

        if self.is_leaf:
            # if self.prev_leaf == None:
            #     self.prev_leaf = -1
            # if self.next_leaf == None:
            #     self.next_leaf = -1

            # write pointers
            struct.pack_into('i', raw, offset, self.prev_leaf)
            struct.pack_into('i', raw, offset + 4, self.next_leaf)
            offset += 8

            # write keys
            for i in range(n):
                struct.pack_into('i', raw, offset, self.keys[i])
                offset += 4
            
            # write RIDs (page_id, slot_id)
            for i in range(n):
                struct.pack_into('I', raw, offset, self.RIDs[i][0])
                struct.pack_into('I', raw, offset + 4, self.RIDs[i][1])
                offset += 8

        else:
            # write pointers
            for i in range(n + 1):
                struct.pack_into('I', raw, offset, self.pointers[i])
                offset += 4
            
            # write keys
            for i in range(n):
                struct.pack_into('i', raw, offset, self.keys[i])
                offset += 4
        

    def deserialize(self):
        raw = self.page_raw
        self.is_leaf = struct.unpack_from('?', raw, 0)[0]
        self.page_id = struct.unpack_from('I', raw, 1)[0]
        self.num_keys = struct.unpack_from('H', raw, 5)[0]

        offset = 7
        n = self.num_keys

        if self.is_leaf:
            self.RIDs = []

            self.prev_leaf = struct.unpack_from('i', raw, offset)[0]
            # if self.prev_leaf == -1:
            #     self.prev_leaf = None

            self.next_leaf = struct.unpack_from('i', raw, offset + 4)[0]
            # if self.next_leaf == -1:
            #     self.next_leaf = None
            
            offset += 8
            
            # read the keys into array
            for _ in range(n):
                self.keys.append(struct.unpack_from('i', raw, offset)[0])
                offset += 4
            
            # read the RIDs (page_id, slot_id) into the array
            for _ in range(n):
                page_id = struct.unpack_from('I', raw, offset)[0]
                slot_id = struct.unpack_from('I', raw, offset + 4)[0]
                self.RIDs.append((page_id, slot_id))
                offset += 8
            
        else:
            #print('not self.leaf')
            # read the pointers (page_ids)
            self.pointers = []
            for _ in range(n + 1):
                self.pointers.append(struct.unpack_from('I', raw, offset)[0])
                offset += 4
            
            # read the keys
            for _ in range(n):
                self.keys.append(struct.unpack_from('i', raw, offset)[0])
                offset += 4
    
    def is_overflow(self) -> bool:
        return self.num_keys > ORDER
    
    def insert(self, key: int, rid: tuple[int, int]):
        for i in range(self.num_keys):
            if key <= self.keys[i]:
                if key == self.keys[i]:
                    self.RIDs[i] = rid
                else:
                    self.keys.insert(i, key)
                    self.RIDs.insert(i, rid)
                    self.num_keys += 1
                return
        self.keys.append(key)
        self.RIDs.append(rid)
        self.num_keys += 1

    def lookup(self, key: int) -> tuple[int, int] | None:
        for i in range(self.num_keys):
            if key == self.keys[i]:
                return self.RIDs[i]
    
        return None
    
    def remove_key(self, key:int):
        for i in range(self.num_keys):
            if key == self.keys[i]:
                self.keys.pop(i)
                self.RIDs.pop(i)
                self.keys -= 1
                return

    def insert_pointer(self, min_key: int, pointer: int):

        # find the index for the insert
        for i in range(self.num_keys):
            if min_key < self.keys[i]:
                self.keys.insert(i, min_key)
                self.pointers.insert(i + 1, pointer)
                self.num_keys += 1
                return
            
        # key is the largest in the array
        self.keys.append(min_key)
        self.pointers.append(pointer)
        self.num_keys += 1