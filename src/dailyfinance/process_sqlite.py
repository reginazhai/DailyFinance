"""CLI for processing raw SQLite documents into processed documents."""

import argparse
from dataclasses import dataclass

from dailyfinance.config import get_default_recent_days, recent_cutoff
from dailyfinance.processing import DEFAULT_PROCESSING_VERSION, ProcessingPipeline
from dailyfinance.processing.quality import is_valid_raw_document
from dailyfinance.storage import DatabaseDocumentStore
from dailyfinance.utils import derive_document_id


DEFAULT_DATABASE_URL = "sqlite:///data/dailyfinance.db"


@dataclass(frozen=True)
class ProcessingRunStats:
    """Counts from a SQLite processing run."""

    examined: int = 0
    processed: int = 0
    already_processed: int = 0
    invalid: int = 0
    failed: int = 0


def process_sqlite_documents(
    *,
    database_url: str = DEFAULT_DATABASE_URL,
    limit: int | None = None,
    processing_version: str = DEFAULT_PROCESSING_VERSION,
    include_historical: bool = False,
    recent_days: int | None = None,
) -> ProcessingRunStats:
    """Process unprocessed raw documents from SQLite."""
    store = DatabaseDocumentStore(database_url)
    processor = ProcessingPipeline(processing_version=processing_version)
    documents = store.list_documents(limit=None)
    cutoff = None if include_historical else recent_cutoff(recent_days or get_default_recent_days())

    examined = 0
    processed = 0
    already_processed = 0
    invalid = 0
    failed = 0

    for document in documents:
        if limit is not None and examined >= limit:
            break
        if cutoff and (document.published_at is None or document.published_at < cutoff):
            continue
        examined += 1
        raw_document_id = derive_document_id(document)

        if store.has_processed_document(raw_document_id, processing_version):
            already_processed += 1
            continue
        if not is_valid_raw_document(document):
            invalid += 1
            continue

        try:
            processed_document = processor.process(document)
            if store.save_processed_document(processed_document):
                processed += 1
            else:
                already_processed += 1
        except Exception:
            failed += 1

    return ProcessingRunStats(
        examined=examined,
        processed=processed,
        already_processed=already_processed,
        invalid=invalid,
        failed=failed,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the processing CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Process raw SQLite documents into deterministic metadata records."
    )
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy SQLite database URL.",
    )
    parser.add_argument("--limit", type=int, help="Maximum raw documents to examine.")
    parser.add_argument(
        "--include-historical",
        action="store_true",
        help="Process all raw documents instead of only the recent daily window.",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        help="Recent daily window in days. Defaults to DAILYFINANCE_RECENT_DAYS or 7.",
    )
    parser.add_argument(
        "--processing-version",
        default=DEFAULT_PROCESSING_VERSION,
        help="Processing version used for idempotency.",
    )
    return parser


def main() -> None:
    """Run deterministic metadata processing."""
    args = build_parser().parse_args()
    stats = process_sqlite_documents(
        database_url=args.database_url,
        limit=args.limit,
        processing_version=args.processing_version,
        include_historical=args.include_historical,
        recent_days=args.recent_days,
    )
    print(f"Examined {stats.examined} documents")
    print(f"Processed {stats.processed} documents")
    print(f"Already processed {stats.already_processed} documents")
    print(f"Invalid {stats.invalid} documents")
    print(f"Failed {stats.failed} documents")
