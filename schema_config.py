from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ColumnConfig(BaseModel):
    """
    Represents a single column in a table with optional constraints.
    """
    name: str
    type: str
    primary_key: bool = False
    default: Optional[str] = None
    json_path: Optional[str] = None
    index: bool = False
    check: Optional[str] = None


class TableSchema(BaseModel):
    """
    Defines the schema of a table including columns and DDL generation logic.
    """
    schema_name: str = Field(default="public")
    table_name: str
    store_full_record_column: str = Field(default="full_record")
    columns: List[ColumnConfig]

    def to_ddl(self) -> str:
        """
        Generate PostgreSQL DDL string for creating table + indexes.
        """
        column_definitions = [self._build_column_ddl(col) for col in self.columns]
        column_definitions.append(f"{self.store_full_record_column} JSONB NOT NULL")

        ddl_statements = [
            f"CREATE SCHEMA IF NOT EXISTS {self.schema_name};",
            f"CREATE TABLE IF NOT EXISTS {self.schema_name}.{self.table_name} (",
            "  " + ",\n  ".join(column_definitions),
            ");"
        ]

        for col in self.columns:
            if col.index:
                ddl_statements.append(
                    f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_{col.name} "
                    f"ON {self.schema_name}.{self.table_name} ({col.name});"
                )

        return "\n".join(ddl_statements)

    def _build_column_ddl(self, col: ColumnConfig) -> str:
        parts = [col.name, col.type]
        if col.primary_key:
            parts.append("PRIMARY KEY")
        if col.default:
            parts.append(f"DEFAULT {col.default}")
        if col.check:
            parts.append(f"CHECK ({col.check})")
        return " ".join(parts)


def load_schema(config_name: str) -> TableSchema:
    """
    Load and parse a schema config from schema/<config_name>.json
    """
    cfg_path = Path(__file__).parent / "schema" / f"{config_name}.json"

    if not cfg_path.exists():
        raise FileNotFoundError(f"Schema config file not found: {cfg_path}")

    try:
        raw_json = cfg_path.read_text(encoding="utf-8")
        parsed = json.loads(raw_json)
        return TableSchema(**parsed)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON schema: {cfg_path}") from e
