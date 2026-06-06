import struct

PAGE_SIZE = 1024

class DirectoryPage:
    page_count: int
    free_space: dict[int, int] # page_id -> free_space
    def __init__(self, dir_raw = bytearray(PAGE_SIZE)):
        # store the bytearray of the page
        self.dir_raw = dir_raw

        self.deserialize()
    
    # Directory page format:
    # <header: [page_count: int (2 bytes)>, <directory: [page_id: int (2 bytes), free_space: int (2 bytes), tuple_count: int (2 bytes)]>
    #

    def deserialize(self):
        self.free_space = {0: 0}
        self.page_count = struct.unpack_from('H', self.dir_raw, 0)[0]
        print('directory: page_count: ', self.page_count)
        offset = 2
        # print('########## directory ##########')
        # print('page_count: ', self.page_count)
        # print('\nfree space:')
        for _ in range(1, self.page_count):
            page_id = struct.unpack_from('H', self.dir_raw, offset)[0]
            self.free_space[page_id] = struct.unpack_from('H', self.dir_raw, offset + 2)[0]
            offset += 4
            #print(f'page_id: {page_id}, free_space: {self.free_space[page_id]}')


    def update_directory(self, page_id, free_space, tuple_count):
        offset = 4 * page_id - 2
        struct.pack_into('H', self.dir_raw, offset, page_id)
        struct.pack_into('H', self.dir_raw, offset + 2, free_space)
        struct.pack_into('H', self.dir_raw, offset + 4, tuple_count)
    
    def update_num_pages(self, num_pages):
        struct.pack_into('H', self.dir_raw, 0, num_pages)

    # def createDirectory(self):
    #     struct.pack_into('H', self.dir_raw, 0, 1)