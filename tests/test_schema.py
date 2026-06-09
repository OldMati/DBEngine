import pytest
import math
from catalog.schema import Schema, Column, DataType

column_name = Column('Name', DataType.VARCHAR, 32)
column_surname = Column('Surname', DataType.VARCHAR, 32)
column_age = Column('Age', DataType.INT)
column_employed = Column('Employed', DataType.BOOL)
column_balance = Column('Balance', DataType.FLOAT)

schema = Schema([column_name, column_surname, column_age, column_employed, column_balance])


def test_increasing_id():
    # set first ID
    ID = 1
    schema_id = Schema([column_name])
    rows = [
        {'Name': f'{i}'} for i in range(100)
    ]
    for row in rows:
        row_deserialized = schema_id.deserialize(schema_id.serialize(row))
        assert row_deserialized['ID'] == ID
        ID += 1

def test_serialize_deserialize():
    row_1 = {
        'Name': 'John',
        'Surname': 'Kowalski',
        'Age': 34,
        'Employed': True,
        'Balance': 1250.32
    }

    row_2 = {
        'Name': 'Marek',
        'Surname': 'Lewandowski',
        'Age': 0,
        'Employed': False,
        'Balance': 000.0000
    }

    row_3 = {
        'Name': '',
        'Surname': '',
        'Age': 55,
        'Employed': True,
        'Balance': -9999.955
    }

    rows = [row_1, row_2, row_3]

    for row in rows:
        row_deserialized = schema.deserialize(schema.serialize(row))
        row_deserialized.pop('ID')
        assert row == row_deserialized


def test_max_varchar_length():
    schema_max_length = Schema([column_name])
    row_above_max = {'Name': 'ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ'}
    row_below_max = {'Name': 'ABCDE'}

    assert schema_max_length.serialize(row_above_max) == False
    assert type(schema_max_length.serialize(row_below_max)) == bytes