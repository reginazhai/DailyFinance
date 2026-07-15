"""Ingestion pipeline for collecting and storing raw documents."""

from collections.abc import Iterable
from dataclasses import dataclass

from dailyfinance.collectors import BaseCollector
from dailyfinance.models import RawDocument
from dailyfinance.storage import DocumentStore


@dataclass(frozen=True)
class IngestionStats:
    """Counts from one ingestion run."""

    collected: int = 0
    inserted: int = 0
    skipped_duplicates: int = 0
    invalid: int = 0
    failed: int = 0


@dataclass(frozen=True)
class IngestionResult:
    """Documents and stats from one ingestion run."""

    documents: list[RawDocument]
    stats: IngestionStats


class IngestionPipeline:
    """Run collectors and persist their raw documents."""

    def __init__(self, store: DocumentStore) -> None:
        self.store = store

    def run(self, collectors: Iterable[BaseCollector]) -> IngestionResult:
        """Collect documents from one or more collectors and save them."""
        documents: list[RawDocument] = []
        collected = 0
        inserted = 0
        skipped_duplicates = 0
        invalid = 0
        failed = 0

        for collector in collectors:
            try:
                collected_documents = list(collector.collect())
            except Exception:
                failed += 1
                continue

            collected += len(collected_documents)
            write_result = self.store.save_many(collected_documents)
            inserted += write_result.inserted_count
            skipped_duplicates += write_result.skipped_duplicates_count
            invalid += write_result.invalid_count
            documents.extend(collected_documents)

        return IngestionResult(
            documents=documents,
            stats=IngestionStats(
                collected=collected,
                inserted=inserted,
                skipped_duplicates=skipped_duplicates,
                invalid=invalid,
                failed=failed,
            ),
        )
