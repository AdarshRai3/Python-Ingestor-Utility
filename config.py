import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    def __init__(self) -> None:
        _ = self.pg_dsn  # Trigger validation early

    @property
    def pg_dsn(self) -> str:
        value = os.getenv("PG_DSN")
        if not value:
            self._missing("PG_DSN")
        return value

    @property
    def json_folder(self) -> str:
        return os.getenv("JSON_FOLDER", "company_wise_leetcode")

    @property
    def schema_name(self) -> str:
        return os.getenv("SCHEMA_NAME", "public")

    @property
    def table_name(self) -> str:
        return os.getenv("TABLE_NAME", "coding_questions")

    @staticmethod
    def _missing(name: str) -> None:
        raise RuntimeError(f"Missing required environment variable: {name}")


# Step 1: Load and use env settings
settings = Settings()
print(f"[DEBUG] Loaded PG_DSN from .env: {settings.pg_dsn}")

