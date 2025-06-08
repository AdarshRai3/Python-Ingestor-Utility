import time
from config import settings
from database import ensure_table, count_rows
from schema_config import load_schema
from ingestor.json_ingestor import JsonIngestor
from main import parse_files_concurrently, chunk_and_insert

def main():
    schema = load_schema(settings.table_name)
    ensure_table()
    ingestor = JsonIngestor(settings.json_folder, schema.schema_name, schema.table_name)

    start_time = time.time()
    records = parse_files_concurrently(ingestor, max_workers=8)
    parse_time = time.time() - start_time

    insert_start = time.time()
    chunk_and_insert(records, chunk_size=1000, schema=schema)
    insert_time = time.time() - insert_start

    total = count_rows(schema.schema_name, schema.table_name)
    total_time = time.time() - start_time
    rate = total / total_time if total_time > 0 else 0

    print(f"Parsed {len(records)} records in {parse_time:.2f}s")
    print(f"Inserted in {insert_time:.2f}s")
    print(f"Total Time: {total_time:.2f}s — Rate: {rate:.0f} rec/s")

if __name__ == "__main__":
    main()