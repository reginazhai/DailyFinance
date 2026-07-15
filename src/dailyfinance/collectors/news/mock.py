"""Mock news collector for local development and tests."""

from collections.abc import Sequence
from datetime import datetime, timezone

from dailyfinance.collectors.base import BaseCollector
from dailyfinance.models import RawDocument


class MockNewsCollector(BaseCollector):
    """Return deterministic sample financial news documents."""

    @property
    def source_name(self) -> str:
        """Return the stable name of the mock news source."""
        return "mock_news"

    def collect(self) -> Sequence[RawDocument]:
        """Collect mock financial news documents."""
        return [
            RawDocument(
                source_name=self.source_name,
                external_id="mock-news-2026-07-01-fed",
                title="Federal Reserve officials signal patience on rate cuts",
                url="https://example.com/markets/fed-rate-outlook",
                published_at=datetime(2026, 7, 1, 13, 30, tzinfo=timezone.utc),
                content=(
                    "Federal Reserve officials indicated they want more evidence that "
                    "inflation is moving toward target before changing interest rates."
                ),
                raw_payload={
                    "source": "Example Markets",
                    "category": "macro",
                },
                metadata={
                    "topics": ["federal_reserve", "interest_rates", "inflation"],
                    "region": "US",
                },
            ),
            RawDocument(
                source_name=self.source_name,
                external_id="mock-news-2026-07-01-chipmaker",
                title="Chipmaker shares rise after stronger data center demand",
                url="https://example.com/equities/chipmaker-data-center-demand",
                published_at=datetime(2026, 7, 1, 14, 45, tzinfo=timezone.utc),
                content=(
                    "Shares of major semiconductor companies rose as analysts pointed "
                    "to resilient demand from cloud and AI infrastructure customers."
                ),
                raw_payload={
                    "source": "Example Equities",
                    "category": "stocks",
                },
                metadata={
                    "topics": ["semiconductors", "ai_infrastructure", "equities"],
                    "tickers": ["NVDA", "AMD"],
                },
            ),
            RawDocument(
                source_name=self.source_name,
                external_id="mock-news-2026-07-01-oil",
                title="Oil prices edge higher as inventories tighten",
                url="https://example.com/commodities/oil-inventory-update",
                published_at=datetime(2026, 7, 1, 16, 0, tzinfo=timezone.utc),
                content=(
                    "Crude prices moved higher after inventory data suggested stronger "
                    "near-term demand and lower available supply."
                ),
                raw_payload={
                    "source": "Example Commodities",
                    "category": "commodities",
                },
                metadata={
                    "topics": ["oil", "commodities", "inventories"],
                    "region": "global",
                },
            ),
        ]
