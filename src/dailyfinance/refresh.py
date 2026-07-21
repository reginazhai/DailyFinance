"""One-command local refresh workflow for DailyFinance."""

from argparse import ArgumentParser, Namespace
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from dailyfinance.cli import build_collectors
from dailyfinance.collectors import BaseCollector
from dailyfinance.migrate_jsonl_to_sqlite import (
    DEFAULT_DATABASE_URL,
    DEFAULT_INPUT_PATH,
    MigrationResult,
    migrate_jsonl_to_sqlite,
)
from dailyfinance.process_sqlite import ProcessingRunStats, process_sqlite_documents
from dailyfinance.processing import DEFAULT_PROCESSING_VERSION, IngestionResult, IngestionPipeline
from dailyfinance.storage import DatabaseDocumentStore, LocalJsonlDocumentStore


@dataclass(frozen=True)
class RefreshResult:
    """Counts from one end-to-end local refresh."""

    ingestion: IngestionResult
    migration: MigrationResult
    processing: ProcessingRunStats
    search_index: dict[str, int]


def run_refresh(
    collectors: Iterable[BaseCollector],
    *,
    jsonl_path: Path | str = DEFAULT_INPUT_PATH,
    database_url: str = DEFAULT_DATABASE_URL,
    limit: int | None = None,
    include_historical: bool = False,
    recent_days: int | None = None,
    processing_version: str = DEFAULT_PROCESSING_VERSION,
) -> RefreshResult:
    """Run collection, migration, processing, and search indexing."""
    ingestion_store = LocalJsonlDocumentStore(jsonl_path)
    ingestion_result = IngestionPipeline(store=ingestion_store).run(collectors)
    migration_result = migrate_jsonl_to_sqlite(
        input_path=jsonl_path,
        database_url=database_url,
    )
    processing_stats = process_sqlite_documents(
        database_url=database_url,
        limit=limit,
        processing_version=processing_version,
        include_historical=include_historical,
        recent_days=recent_days,
    )
    search_index_result = DatabaseDocumentStore(database_url).rebuild_search_index()
    return RefreshResult(
        ingestion=ingestion_result,
        migration=migration_result,
        processing=processing_stats,
        search_index=search_index_result,
    )


def build_parser() -> ArgumentParser:
    """Build the refresh CLI argument parser."""
    parser = ArgumentParser(
        description="Run DailyFinance ingestion, SQLite migration, processing, and search indexing."
    )
    parser.add_argument(
        "--jsonl-path",
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the local raw JSONL file. Defaults to {DEFAULT_INPUT_PATH}.",
    )
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help=f"SQLite database URL. Defaults to {DEFAULT_DATABASE_URL}.",
    )
    parser.add_argument("--source-name", help="Stable name for a direct or discovered RSS source.")
    parser.add_argument("--feed-url", help="Direct RSS or Atom feed URL to collect.")
    parser.add_argument("--website-url", help="Website URL to inspect for RSS or Atom feed links.")
    parser.add_argument(
        "--rss-config",
        default="config/rss_sources.yaml",
        help="Path to a YAML file containing configured RSS sources.",
    )
    parser.add_argument(
        "--all-configured-rss",
        action="store_true",
        help="Ingest all RSS sources from --rss-config.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        default=[],
        help="Ticker symbol to collect with yfinance. Can be used more than once.",
    )
    parser.add_argument(
        "--market-period",
        default="5d",
        help="yfinance history period for ticker collection.",
    )
    parser.add_argument(
        "--market-interval",
        default="1d",
        help="yfinance history interval for ticker collection.",
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
    """Run the refresh workflow from command line arguments."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        collectors = build_collectors(_collector_args(args))
    except ValueError as error:
        parser.error(str(error))

    result = run_refresh(
        collectors,
        jsonl_path=args.jsonl_path,
        database_url=args.database_url,
        limit=args.limit,
        include_historical=args.include_historical,
        recent_days=args.recent_days,
        processing_version=args.processing_version,
    )
    _print_result(result, args.jsonl_path)


def _collector_args(args: Namespace) -> Namespace:
    return Namespace(
        source_name=args.source_name,
        feed_url=args.feed_url,
        website_url=args.website_url,
        output_path=args.jsonl_path,
        rss_config=args.rss_config,
        all_configured_rss=args.all_configured_rss,
        ticker=args.ticker,
        market_period=args.market_period,
        market_interval=args.market_interval,
    )


def _print_result(result: RefreshResult, jsonl_path: str) -> None:
    print("Refresh complete")
    print(f"Collected {result.ingestion.stats.collected} documents")
    print(f"Saved {result.ingestion.stats.inserted} documents to {jsonl_path}")
    print(f"Skipped {result.ingestion.stats.skipped_duplicates} JSONL duplicates")
    print(f"Invalid during ingestion {result.ingestion.stats.invalid}")
    print(f"Collector failures {result.ingestion.stats.failed}")
    print(f"Inserted {result.migration.inserted_count} SQLite documents")
    print(f"Skipped {result.migration.skipped_count} SQLite duplicates")
    print(f"Examined {result.processing.examined} SQLite documents")
    print(f"Processed {result.processing.processed} documents")
    print(f"Already processed {result.processing.already_processed} documents")
    print(f"Invalid during processing {result.processing.invalid}")
    print(f"Processing failures {result.processing.failed}")
    print(
        "Search index "
        f"indexed={result.search_index['indexed']} "
        f"skipped={result.search_index['skipped']} "
        f"failed={result.search_index['failed']}"
    )


if __name__ == "__main__":
    main()
