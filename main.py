import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from config import settings
from database import ensure_table, batch_insert, count_rows
from schema_config import load_schema
from ingestor.json_ingestor import JsonIngestor


logger = logging.getLogger("ingestor")
logger.setLevel(logging.INFO)

# Avoid re-adding handler if this file is run multiple times (e.g., in Jupyter/multiprocessing)
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)


def parse_files_concurrently(ingestor: JsonIngestor, max_workers: int = 8) -> List[dict]:
    """Parse all JSON files using a thread pool. Returns a flat list of parsed records."""
    parsed_records = []
    files = ingestor.discover_files()

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(ingestor.parse_file, fp): fp for fp in files}
        for fut in as_completed(futures):
            fp = futures[fut]
            try:
                records = fut.result()
                parsed_records.extend(records)
                logger.info(f"[OK] Parsed {len(records)} from {fp}")
            except Exception as e:
                logger.error(f"[ERR] Failed parsing {fp}: {e}")
    return parsed_records


def chunk_and_insert(records: List[dict], chunk_size: int, schema) -> None:
    """Split records into chunks and insert each in parallel."""
    chunks = [records[i:i + chunk_size] for i in range(0, len(records), chunk_size)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(batch_insert, chunk, schema) for chunk in chunks]
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                logger.exception("Insert failed for a chunk")


def main() -> None:
    start_time = time.time()

    try:
        print(f"[DEBUG] PG_DSN (print): {settings.pg_dsn}")
        logger.info(f"Using PG_DSN: {settings.pg_dsn}")
    except Exception as e:
        print(f"[ERROR] Could not load PG_DSN: {e}")
        raise

    schema = load_schema(settings.table_name)
    ensure_table()

    ingestor = JsonIngestor(
        folder=settings.json_folder,
        schema_name=schema.schema_name,
        table_name=schema.table_name
    )

    logger.info("Parsing JSON files...")
    records = parse_files_concurrently(ingestor, max_workers=8)

    if not records:
        logger.warning("No records parsed from files. Skipping DB insertion.")
    else:
        logger.info(f"Finished parsing. Inserting records into DB...")
        try:
            chunk_and_insert(records, chunk_size=1000, schema=schema)
        except Exception as e:
            logger.exception("DB insert failed")

    try:
        total = count_rows(schema.schema_name, schema.table_name)
        logger.info(f"✅ Total rows currently in DB: {total}")
    except Exception as e:
        logger.exception("Failed to fetch total row count from DB")

    logger.info(f"⏱️ Done in {round(time.time() - start_time, 2)}s")


if __name__ == "__main__":
    main()
