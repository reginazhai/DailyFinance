"""Collector interfaces for external financial information sources."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from dailyfinance.models.documents import RawDocument


class BaseCollector(ABC):
    """Base interface for collecting raw financial documents."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the stable name of the external source."""

    @abstractmethod
    def collect(self) -> Sequence[RawDocument]:
        """Collect raw documents from the source."""


Collector = BaseCollector
