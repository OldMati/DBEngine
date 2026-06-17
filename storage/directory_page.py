import struct

PAGE_SIZE = 4096

class DirectoryPage:
    page_count: int
    free_space: dict[int, int] # page_id -> free_space
    def __init__(self, dir_raw: bytearray, new_directory: bool = False):
        # store the bytearray of the page
        self.dir_raw = dir_raw
        self.free_space = {0: 0}
        if not new_directory:
            self.deserialize()
        else:
            self.page_count = 1
            struct.pack_into('H', self.dir_raw, 0, self.page_count)

    
    # Directory page format:
    # <header: [page_count: int (2 bytes)>, <directory: [page_id: int (2 bytes), free_space: int (2 bytes), tuple_count: int (2 bytes)]>
    #

    def deserialize(self):
        self.page_count = struct.unpack_from('H', self.dir_raw, 0)[0]
        offset = 2
        
        for _ in range(1, self.page_count):
            page_id = struct.unpack_from('H', self.dir_raw, offset)[0]
            self.free_space[page_id] = struct.unpack_from('H', self.dir_raw, offset + 2)[0]
            offset += 6
            
    def update_directory(self, page_id, free_space, tuple_count) -> bool | None:
        
        if page_id == 0 or page_id >= self.page_count or free_space < 0 or tuple_count < 0:
            return False

        self.free_space[page_id] = free_space
        offset = 6 * page_id - 4
        struct.pack_into('H', self.dir_raw, offset, page_id)
        struct.pack_into('H', self.dir_raw, offset + 2, free_space)
        struct.pack_into('H', self.dir_raw, offset + 4, tuple_count)
    
    def increase_page_count(self, page_id: int):
        self.page_count += 1
        struct.pack_into('H', self.dir_raw, 0, self.page_count)
        self.update_directory(page_id, PAGE_SIZE, 0)
    
    def find_page_with_enough_space(self, free_space):
        for page_id in self.free_space:
            if self.free_space[page_id] >= free_space:
                return page_id
        return None
    
    def __str__(self):
        print('########### DIRECTORY ###########')
        print('self.free_space: ', self.free_space)
        print('self.page_count: ', self.page_count)