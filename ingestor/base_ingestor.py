"""
Defines the interface for all ingestor implementations.
An ingestor is responsible for discovering, parsing, and persisting
records from a set of source files.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IIngestor(ABC):
    """
    Abstract base class for ingestor implementations.

    An IIngestor must be able to:
      1. Discover the file paths it should process.
      2. Parse each file into a list of record dictionaries.
      3. Persist those records to the target storage.
    """

    @abstractmethod
    def discover_files(self) -> List[str]:
        """
        Discover all source files to ingest.

        Returns:
            A list of filesystem paths (as strings) pointing to the files
            that should be processed.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_file(self, path: str) -> List[Dict[str, Any]]:
        """
        Parse a single file into a list of record dicts.

        Args:
            path: The filesystem path to the file to parse.

        Returns:
            A list of dictionaries, each representing a single record
            extracted and cleaned from the source file.
        """
        raise NotImplementedError

    @abstractmethod
    def ingest_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Persist a batch of parsed records.

        Args:
            records: A list of dictionaries, each representing a record
                     to write to the target data store.

        Side Effects:
            Writes data to the destination (e.g., a database or blob store).

        Raises:
            ValueError: If `records` is empty or invalid.
            RuntimeError: On underlying persistence failure.
        """
        raise NotImplementedError