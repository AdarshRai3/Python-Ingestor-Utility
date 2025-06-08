# ingestor/json_ingestor.py

import json
from pathlib import Path
from typing import Any, Dict, List

from ingestor.base_ingestor import IIngestor
from database import batch_insert
from schema_config import load_schema, TableSchema


class JsonIngestor(IIngestor):
    """
    Ingestor implementation for JSON files containing structured records.

    Responsibilities:
    - Discover all `.json` files in the specified folder.
    - Parse each file into a list of cleaned record dictionaries.
    - Persist those records to a PostgreSQL database using the provided schema.
    """

    def __init__(self, folder: str, schema_name: str, table_name: str) -> None:
        """
        Initialize the ingestor with JSON folder and schema metadata.

        Args:
            folder (str): Path to the directory containing JSON files.
            schema_name (str): PostgreSQL schema name (e.g., "public").
            table_name (str): PostgreSQL table name (e.g., "coding_questions").
        """
        self.folder = Path(folder)
        self.schema: TableSchema = load_schema(table_name)
        self.schema.schema_name = schema_name  # Ensure dynamic schema override

    def discover_files(self) -> List[str]:
        """
        Discover all .json files in the configured folder.

        Returns:
            List[str]: List of absolute file paths as strings.
        """
        return [str(file) for file in self.folder.glob("*.json")]

    def parse_file(self, path: str) -> List[Dict[str, Any]]:
        """
        Parse a single JSON file into structured and cleaned records.

        Args:
            path (str): Path to the JSON file.

        Returns:
            List[Dict[str, Any]]: List of records cleaned and ready for ingestion.
        """
        content = Path(path).read_text(encoding="utf-8")
        raw_data = json.loads(content)

        records = raw_data if isinstance(raw_data, list) else [raw_data]

        return [self._clean_record(record) for record in records]

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a single record by removing unnecessary fields.

        Args:
            record (Dict[str, Any]): The raw input record.

        Returns:
            Dict[str, Any]: Cleaned version of the record.
        """
        record.pop("question_id", None)  # Drop transient ID if present
        return record

    def ingest_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Persist parsed records to the database.

        Args:
            records (List[Dict[str, Any]]): A batch of records to insert.

        Side Effects:
            Inserts data into the configured PostgreSQL table.
        """
        if records:
            batch_insert(records, self.schema)
