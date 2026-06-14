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

class Record:
    values: tuple
    rid: tuple[int, int]

    def __init__(self, values, rid):
        self.values = values
        self.rid = rid

class Schema:
    columns: list[Column]
    column_names: dict[str, int] # column name -> index

    def __init__(self, columns: list[Column]):
        self.columns = columns.copy()

        # count varchars
        count = 0
        for column in columns:
            if column.type == DataType.VARCHAR:
                count += 1
        
        self.num_of_varchars = count

        # create the column_names dict
        self.column_names = {}
        for i in range(len(columns)):
            self.column_names[columns[i].name] = i


    def serialize(self, row: Record) -> bytes:
        raw_arr = ['' for _ in range(len(self.columns))]
        header = []
        #print('columns: ', self.columns)
        for column in self.columns:
            col_index = self.column_names[column.name]
            if column.type == DataType.VARCHAR:
                #print('SERIALIZING THE VARCHAR NOW, length of column: ', len(row.values[col_index]), 'max length: ', column.max_length, ' column: ', row.values[col_index])
                if column.max_length and len(row.values[col_index]) > column.max_length:
                    return False
                
                raw_data = row.values[col_index].encode('utf-8')
                raw_arr[col_index] = raw_data

                length = len(raw_data)
                raw_length = struct.pack('H', length)   # 2 byte metadata storing the length of the varchar
                header.append(raw_length)
            else:
                #print(f'row.values: {row.values}, col_index: {self.column_names[column.name]}')
                raw_data = struct.pack(column.type.value, row.values[col_index])
                raw_arr[col_index] = raw_data

        # combine the header and raw into sequence of bits
        raw = b"".join(header + raw_arr)
        return raw

    def deserialize(self, raw: bytes, rid: tuple[int, int]) -> Record:
        # get the number and length of the varchars:
        lengths = []
        for i in range(self.num_of_varchars):
            length = struct.unpack_from('H', raw, 2 * i)[0]
            lengths.append(length)

        # index of current varchar in lengths
        varchar_count = 0

        # data starts after the header
        offset = 2 * self.num_of_varchars
        values = [_ for _ in range(len(self.columns))]

        for column in self.columns:
            col_index = self.column_names[column.name]
            if column.type == DataType.VARCHAR:
                # get the length of the string
                length = lengths[varchar_count]
                varchar_count += 1

                values[col_index] = raw[offset: offset + length].decode()
                offset += length

            else:
                data = struct.unpack_from(column.type.value, raw, offset)[0]
                values[col_index] = data
                offset += struct.calcsize(column.type.value)
        
        return Record(tuple(values), rid)

    def get_index(self, column_name: str):
        if column_name in self.column_names:
            return self.column_names[column_name]
        
        raise KeyError(f"Column '{column_name}' not found in schema")

    def to_dict(self) -> dict:
        return {
            'columns': [
                {
                    'name': col.name,
                    'type': col.type.name,
                    'max_length': col.max_length
                }
                for col in self.columns
            ]
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Schema':
        columns = []
        for col in data['columns']:
            column = Column(name=col['name'], type=DataType[col['type']], max_length=col.get('max_length'))
            columns.append(column)
        
        return Schema(columns)
        
    
    def coerce(self, values: tuple):
        result = []
        #print('BEGGINING OF COERCE, VALUES: ', values)

        for value, col in zip(values, self.columns):
            #print('VALUE IN LOOP: ', value, 'column: ', col.name, 'col_type: ', col.type.name)
            col_type = col.type.name
            try:
                if col_type == 'INT':
                    result.append(int(value))
                elif col_type == 'FLOAT':
                    result.append(float(value))
                elif col_type == 'VARCHAR':
                    result.append(str(value))
                elif col_type == 'BOOL':
                    if isinstance(value, bool):
                        result.append(value)
                    else:
                        result.append(str(value).lower() in ('1', 'true'))
            except:
                raise TypeError(f'Cannot coerce {value} to {col_type} for column {col.name}')
        #print('RETURNING, result: ', result)
        return tuple(result)
