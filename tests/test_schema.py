import pytest
from catalog.schema import Schema, Column, DataType, Record

column_name = Column('Name', DataType.VARCHAR, 32)
column_surname = Column('Surname', DataType.VARCHAR, 32)
column_age = Column('Age', DataType.INT)
column_employed = Column('Employed', DataType.BOOL)
column_balance = Column('Balance', DataType.FLOAT)

schema = Schema([column_name, column_surname, column_age, column_employed, column_balance])

test_count = 20

def test_serialize_deserialize():
    rows = [
        Record((f'Mateusz{i}', f'Drozdz{i}', i + 15, i % 2 == 0, i * 1523.527), (i, i)) for i in range(test_count)
    ]

    for row in rows:
        row_deserialized = schema.deserialize(schema.serialize(row), row.rid)
        assert row.values == row_deserialized.values
        assert row.rid == row_deserialized.rid


def test_max_varchar_length():
    schema_max_length = Schema([column_name, column_age])
    row_above_max = Record(('ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ', 15), (0, 0))
    row_below_max = Record(('ABCDE', 11), (1, 1))

    assert schema_max_length.serialize(row_above_max) == False
    assert type(schema_max_length.serialize(row_below_max)) == bytes