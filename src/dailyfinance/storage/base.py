"""Storage interfaces for DailyFinance documents."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from dailyfinance.models import RawDocument


@dataclass(frozen=True)
class StorageWriteResult:
    """Result counts for a document storage write."""

    inserted_count: int = 0
    skipped_duplicates_count: int = 0
    invalid_count: int = 0


class DocumentStore(ABC):
    """Base interface for persisting raw documents."""

    @abstractmethod
    def save(self, document: RawDocument) -> StorageWriteResult:
        """Persist one raw document."""

    @abstractmethod
    def save_many(self, documents: Iterable[RawDocument]) -> StorageWriteResult:
        """Persist multiple raw documents."""

    @abstractmethod
    def load_all(self) -> list[RawDocument]:
        """Load all persisted raw documents."""
