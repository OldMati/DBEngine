from dataclasses import dataclass
from enum import Enum
import struct

class DataType(Enum):
    INT = 'i'       # 4 bytes
    FLOAT = 'd'     # 8 bytes
    BOOL = '?'      # 1 byte
    VARCHAR = 's'   # variable length


@dataclass
class Column:
    name: str
    type: DataType
    max_length: int | None = None


class Schema:
    def __init__(self, columns: list[Column]):
        ID_column = Column('ID', DataType.INT)
        self.columns = [ID_column] + columns
        self.next_id = 1

        # count varchars
        count = 0
        for column in columns:
            if column.type == DataType.VARCHAR:
                count += 1
        
        self.NUM_OF_VARCHARS = count


    def serialize(self, row: dict) -> bytes:
        raw_arr = []
        header = []

        # add the id column
        row = row.copy()
        row['ID'] = self.next_id
        self.next_id += 1

        for column in self.columns:
            if column.type == DataType.VARCHAR:
                if column.max_length and len(row[column.name]) > column.max_length:
                    return False
                
                raw_data = row[column.name].encode('utf-8')
                raw_arr.append(raw_data)

                length = len(raw_data)
                raw_length = struct.pack('H', length)   # 2 byte metadata storing the length of the varchar
                header.append(raw_length)
            else:
                raw_data = struct.pack(column.type.value, row[column.name])
                raw_arr.append(raw_data)

        
        # combine the header and raw into sequence of bits
        raw = b"".join(header + raw_arr)
        return raw



    def deserialize(self, raw: bytes) -> dict:
        # get the number and length of the varchars:
        lengths = []
        for i in range(self.NUM_OF_VARCHARS):
            length = struct.unpack_from('H', raw, 2 * i)[0]
            lengths.append(length)

        # index of current varchar in lengths
        varchar_count = 0

        # create the dict with deserialized data:
        row = {}

        # data starts after the header
        offset = 2 * self.NUM_OF_VARCHARS

        for column in self.columns:
            if column.type == DataType.VARCHAR:
                # get the length of the string
                length = lengths[varchar_count]
                varchar_count += 1

                row[column.name] = raw[offset: offset + length].decode()
                offset += length

            else:
                data = struct.unpack_from(column.type.value, raw, offset)[0]
                row[column.name] = data
                offset += struct.calcsize(column.type.value)
        
        return row
