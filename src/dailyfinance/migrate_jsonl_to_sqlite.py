"""CLI for migrating JSONL documents into SQLite."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from dailyfinance.storage import DatabaseDocumentStore, LocalJsonlDocumentStore
from dailyfinance.utils import derive_document_id


DEFAULT_INPUT_PATH = "data/raw_documents.jsonl"
DEFAULT_DATABASE_URL = "sqlite:///data/dailyfinance.db"


@dataclass(frozen=True)
class MigrationResult:
    """Result counts for a JSONL to SQLite migration."""

    inserted_count: int
    skipped_count: int


def migrate_jsonl_to_sqlite(
    input_path: Path | str = DEFAULT_INPUT_PATH,
    database_url: str = DEFAULT_DATABASE_URL,
) -> MigrationResult:
    """Migrate JSONL documents into SQLite, skipping duplicates."""
    jsonl_store = LocalJsonlDocumentStore(input_path)
    database_store = DatabaseDocumentStore(database_url)

    inserted_count = 0
    skipped_count = 0

    for document in jsonl_store.load_all():
        document_id = derive_document_id(document)
        if database_store.has_document(document_id):
            skipped_count += 1
            continue

        database_store.save_documents([document])
        inserted_count += 1

    return MigrationResult(inserted_count=inserted_count, skipped_count=skipped_count)


def build_parser() -> argparse.ArgumentParser:
    """Build the migration CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Migrate JSONL RawDocument records into SQLite."
    )
    parser.add_argument(
        "--input-path",
        default=DEFAULT_INPUT_PATH,
        help="Path to the input JSONL file.",
    )
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL for the output SQLite database.",
    )
    return parser


def main() -> None:
    """Run the JSONL to SQLite migration."""
    args = build_parser().parse_args()
    result = migrate_jsonl_to_sqlite(
        input_path=args.input_path,
        database_url=args.database_url,
    )
    print(f"Inserted {result.inserted_count} documents")
    print(f"Skipped {result.skipped_count} duplicate documents")
