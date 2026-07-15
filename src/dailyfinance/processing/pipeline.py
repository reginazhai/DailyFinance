"""Simple collection pipeline for running collectors."""

from dailyfinance.collectors import BaseCollector
from dailyfinance.models import RawDocument


class CollectionPipeline:
    """Run a collector and return raw documents."""

    def run(self, collector: BaseCollector) -> list[RawDocument]:
        """Collect raw documents from one collector."""
        return list(collector.collect())
