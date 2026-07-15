"""Processor interfaces."""

from abc import ABC, abstractmethod

from dailyfinance.models import ProcessedDocument, RawDocument


class Processor(ABC):
    """Base interface for deterministic raw-document processors."""

    @abstractmethod
    def process(self, document: RawDocument) -> ProcessedDocument:
        """Process one raw document."""
