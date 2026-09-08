import pytest

from catalog.schema import Column, DataType, Record, Schema


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def schema():
    return Schema([
        Column("Name", DataType.VARCHAR, 32),
        Column("Surname", DataType.VARCHAR, 32),
        Column("Age", DataType.INT),
        Column("Employed", DataType.BOOL),
        Column("Balance", DataType.FLOAT),
    ])


@pytest.fixture
def person():
    return Record(("Mateusz", "Drozdz", 21, True, 1523.527), (3, 7))


def roundtrip(schema, record):
    return schema.deserialize(schema.serialize(record), record.rid)


# --- serialization round trip -----------------------------------------------

def test_values_survive_a_round_trip(schema, person):
    assert roundtrip(schema, person).values == person.values


def test_rid_survives_a_round_trip(schema, person):
    assert roundtrip(schema, person).rid == person.rid


def test_many_rows_survive_a_round_trip(schema):
    rows = [
        Record((f"Name{i}", f"Surname{i}", i + 15, i % 2 == 0, i * 1523.527), (i, i))
        for i in range(20)
    ]

    for row in rows:
        assert roundtrip(schema, row).values == row.values


def test_serialize_returns_bytes(schema, person):
    assert isinstance(schema.serialize(person), bytes)


@pytest.mark.parametrize(
    "values",
    [
        ("", "", 0, False, 0.0),
        ("A", "B", -40, True, -0.5),
        ("Zażółć", "gęślą jaźń", 1, False, 3.25),
    ],
)
def test_edge_case_values_survive_a_round_trip(schema, values):
    record = Record(values, (0, 0))

    assert roundtrip(schema, record).values == values


def test_variable_length_strings_do_not_bleed_into_each_other(schema):
    record = Record(("a", "bbbbbbbbbbbbbbbbbbbb", 1, True, 1.0), (0, 0))

    assert roundtrip(schema, record).values == record.values


# --- varchar limits ---------------------------------------------------------

def test_string_at_the_limit_is_accepted():
    schema = Schema([Column("Name", DataType.VARCHAR, 5)])
    record = Record(("ABCDE",), (0, 0))

    assert isinstance(schema.serialize(record), bytes)


def test_string_over_the_limit_is_refused():
    schema = Schema([Column("Name", DataType.VARCHAR, 5)])
    record = Record(("ABCDEF",), (0, 0))

    assert schema.serialize(record) is False


def test_varchar_without_a_limit_accepts_any_length():
    schema = Schema([Column("Notes", DataType.VARCHAR)])
    record = Record(("x" * 500,), (0, 0))

    assert roundtrip(schema, record).values == record.values


# --- column lookup ----------------------------------------------------------

def test_get_index_returns_the_column_position(schema):
    assert schema.get_index("Age") == 2


def test_get_index_raises_for_an_unknown_column(schema):
    with pytest.raises(KeyError):
        schema.get_index("Nickname")


# --- catalog round trip -----------------------------------------------------

def test_schema_survives_a_dict_round_trip(schema):
    restored = Schema.from_dict(schema.to_dict())

    assert [(c.name, c.type, c.max_length) for c in restored.columns] == [
        (c.name, c.type, c.max_length) for c in schema.columns
    ]


def test_a_restored_schema_reads_rows_written_by_the_original(schema, person):
    raw = schema.serialize(person)

    restored = Schema.from_dict(schema.to_dict())

    assert restored.deserialize(raw, person.rid).values == person.values


# --- coercion ---------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        (("21",), (21,)),
        ((21,), (21,)),
        ((21.9,), (21,)),
    ],
)
def test_coerce_to_int(raw, expected):
    schema = Schema([Column("Age", DataType.INT)])

    assert schema.coerce(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        (("true",), (True,)),
        (("1",), (True,)),
        (("false",), (False,)),
        (("no",), (False,)),
        ((True,), (True,)),
    ],
)
def test_coerce_to_bool(raw, expected):
    schema = Schema([Column("Employed", DataType.BOOL)])

    assert schema.coerce(raw) == expected


def test_coerce_to_float():
    schema = Schema([Column("Balance", DataType.FLOAT)])

    assert schema.coerce(("1523.527",)) == (1523.527,)


def test_coerce_to_varchar():
    schema = Schema([Column("Name", DataType.VARCHAR, 32)])

    assert schema.coerce((42,)) == ("42",)


@pytest.mark.parametrize("bad", [("abc",), (None,)])
def test_coerce_raises_on_unconvertible_values(bad):
    schema = Schema([Column("Age", DataType.INT)])

    with pytest.raises(TypeError):
        schema.coerce(bad)


def test_coerced_values_are_serializable(schema):
    values = schema.coerce(("Mateusz", "Drozdz", "21", "true", "1523.527"))
    record = Record(values, (0, 0))

    assert roundtrip(schema, record).values == values