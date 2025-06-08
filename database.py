from typing import Any, Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values, Json
from config import settings
from schema_config import TableSchema, load_schema

# Load schema once
TABLE_SCHEMA: TableSchema = load_schema(settings.table_name)

def get_connection() -> psycopg2.extensions.connection:
    """Create a new PostgreSQL connection using DSN from settings."""
    return psycopg2.connect(settings.pg_dsn)

def ensure_table() -> None:
    """Create schema, table, and indexes based on config."""
    ddl = TABLE_SCHEMA.to_ddl()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()

def extract_value(record: Dict[str, Any], path: str) -> Any:
    """Traverse nested dictionary using dot-separated path."""
    node = record
    for seg in path.split('.'):
        if not isinstance(node, dict):
            return None
        node = node.get(seg)
    return node

def batch_insert(
    records: List[Dict[str, Any]],
    schema: TableSchema = TABLE_SCHEMA,
    chunk_size: int = 1000
) -> None:
    """Insert records into Postgres in chunks using `execute_values`."""
    if not records:
        return

    insert_cols = [col.name for col in schema.columns if not (col.primary_key and col.default)]
    insert_cols.append(schema.store_full_record_column)
    full_table = f"{schema.schema_name}.{schema.table_name}"
    insert_sql = f"INSERT INTO {full_table} ({', '.join(insert_cols)}) VALUES %s"

    def prepare_row(rec: Dict[str, Any]) -> Tuple[Any, ...]:
        vals = []
        for col in schema.columns:
            if col.primary_key and col.default:
                continue
            val = extract_value(rec, col.json_path) if col.json_path else None
            if col.name == "status" and not val:
                val = "active"
            vals.append(val)
        vals.append(Json(rec))
        return tuple(vals)

    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                rows = [prepare_row(rec) for rec in chunk]
                execute_values(cur, insert_sql, rows)
        conn.commit()

def count_rows(schema: str, table: str) -> int:
    """Return the row count of the given schema.table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            return cur.fetchone()[0]
