import json
import pytest
from ingestor.json_ingestor import JsonIngestor

def test_parse_file(tmp_path):
    data = [{"x": 1}, {"y": 2}]
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data))
    ing = JsonIngestor(folder=tmp_path, schema_name="public", table_name="t")
    recs = ing.parse_file(str(p))
    assert isinstance(recs, list)
    assert recs == data
