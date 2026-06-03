import struct

class Page:
    PAGE_SIZE = 4096
    HEADER_SIZE = 6
    SLOT_SIZE = 6

    # Page format:
    # <header: [num_slots: 2 bytes, free_space_pointer: 2 bytes, free_space: 2 bytes]> <slot array: [offset: 2 bytes, length: 2 bytes, is_valid: 2 bytes]
    #
    #
    # <tuples>
    #
    # is_valid = 1: True
    # is_valid = 0: False

    def __init__(self, data: bytes | None = None):
        if data is None:
            self.page = bytearray(self.PAGE_SIZE)
            self.num_slots = 0
            self.free_space_pointer = self.PAGE_SIZE
            self.free_space = self.PAGE_SIZE - self.HEADER_SIZE
            struct.pack_into('H', self.page, 2, self.free_space_pointer)
            struct.pack_into('H', self.page, 4, self.free_space)

        else:
            self.page = data
            self.num_slots = struct.unpack_from('H', self.page, 0)[0]
            self.free_space_pointer = struct.unpack_from('H', self.page, 2)[0]
            self.free_space = struct.unpack_from('H', self.page, 4)[0]


    def insert_tuple(self, data: bytes) -> int:
        length = len(data)

        # find the offset
        offset = self.free_space_pointer - length

        # write the data into the page
        self.page[offset: offset + length] = data

        slot_arr_offset = self.HEADER_SIZE + self.num_slots * self.SLOT_SIZE

        # write offset, length, is_valid to slot array
        struct.pack_into('H', self.page, slot_arr_offset, offset)
        struct.pack_into('H', self.page, slot_arr_offset + 2, length)
        struct.pack_into('H', self.page, slot_arr_offset + 4, 1)


        print('####### FREE SPACE BEFORE SUBTRACTING: ', self.free_space)
        self.free_space_pointer -= length
        self.free_space -= (length + self.SLOT_SIZE)
        self.num_slots += 1
        struct.pack_into('H', self.page, 0, self.num_slots)
        struct.pack_into('H', self.page, 2, self.free_space_pointer)
        print('####### FREE SPACE AFTER SUBTRACTING: ', self.free_space)
        struct.pack_into('H', self.page, 4, self.free_space)



    def get_tuple(self, slot_id:int) -> bytes | None:
        slot_offset = self.HEADER_SIZE + slot_id * self.SLOT_SIZE

        tuple_offset = struct.unpack_from('H', self.page, slot_offset)[0]
        length = struct.unpack_from('H', self.page, slot_offset + 2)[0]
        is_valid = struct.unpack_from('H', self.page, slot_offset + 4)[0]

        if is_valid == 0:
            return None
        
        raw = self.page[tuple_offset: tuple_offset + length]
        return raw

    def delete_tuple(self, slot_id:int) -> bool:
        slot_offset = self.HEADER_SIZE + slot_id * self.SLOT_SIZE
        is_valid = struct.unpack_from('H', self.page, slot_offset + 4)[0]

        if is_valid:
            struct.pack_into('H', self.page, slot_offset + 4, 0)
            # removed the tuple
            return True

        # no tuple to remove
        return False

    # def to_bytes(self) -> bytes:
    #     pass