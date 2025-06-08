import pytest
from main import parse_files_concurrently, chunk_and_insert
from schema_config import load_schema
from config import settings

def test_end_to_end(tmp_path, monkeypatch):
    # monkeypatch JSON files
    p = tmp_path / "x.json"
    p.write_text('[{"a":1},{"a":2}]')
    monkeypatch.setattr(settings, "json_folder", str(tmp_path))
    schema = load_schema(settings.table_name)
    from ingestor.json_ingestor import JsonIngestor
    ing = JsonIngestor(str(tmp_path), schema.schema_name, schema.table_name)

    recs = parse_files_concurrently(ing, max_workers=1)
    assert len(recs) == 2

    # test chunking logic runs without error
    chunk_and_insert(recs, chunk_size=1, schema=schema)
