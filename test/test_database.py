import pytest
from database import extract_value, batch_insert, count_rows, ensure_table, get_connection
from schema_config import load_schema
from config import settings

@pytest.fixture(scope="module")
def schema():
    return load_schema(settings.table_name)

def test_extract_value():
    rec = {"a": {"b": {"c": 5}}}
    assert extract_value(rec, "a.b.c") == 5
    assert extract_value(rec, "a.b.x") is None

def test_batch_insert_and_count(tmp_path, schema):
    ensure_table()
    records = [{"foo": "bar", "status": None}]
    batch_insert(records, schema, chunk_size=1)
    cnt = count_rows(schema.schema_name, schema.table_name)
    assert cnt >= 1
