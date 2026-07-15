from datetime import datetime, timezone

import yfinance as yf

from dailyfinance.collectors import YFinanceMarketDataCollector
from dailyfinance.models import RawDocument


class FakeHistory:
    empty = False

    def reset_index(self):
        return self

    def to_dict(self, orient: str):
        assert orient == "records"
        return [
            {
                "Date": datetime(2026, 7, 1, tzinfo=timezone.utc),
                "Open": 200.0,
                "High": 205.0,
                "Low": 198.5,
                "Close": 204.25,
                "Volume": 1234567,
            },
            {
                "Date": datetime(2026, 7, 2, tzinfo=timezone.utc),
                "Open": 204.0,
                "High": 207.5,
                "Low": 202.75,
                "Close": 206.0,
                "Volume": 2345678,
            },
        ]


class EmptyHistory:
    empty = True


class FakeTicker:
    requested: list[tuple[str, str, str]] = []

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    def history(self, period: str, interval: str):
        self.requested.append((self.ticker, period, interval))
        if self.ticker == "EMPTY":
            return EmptyHistory()
        return FakeHistory()


def test_yfinance_collector_returns_raw_documents_for_tickers(monkeypatch) -> None:
    FakeTicker.requested = []
    monkeypatch.setattr(yf, "Ticker", FakeTicker)
    collector = YFinanceMarketDataCollector(["aapl", "msft"], period="5d", interval="1d")

    documents = collector.collect()

    assert FakeTicker.requested == [("AAPL", "5d", "1d"), ("MSFT", "5d", "1d")]
    assert len(documents) == 2
    assert all(isinstance(document, RawDocument) for document in documents)
    assert documents[0].source_name == "yfinance"
    assert documents[0].external_id == "AAPL:5d:1d"
    assert documents[0].title == "AAPL recent market data"
    assert documents[0].published_at == datetime(2026, 7, 2, tzinfo=timezone.utc)
    assert documents[0].raw_payload["ticker"] == "AAPL"
    assert documents[0].raw_payload["history"][0]["Close"] == 204.25
    assert documents[0].raw_payload["history"][0]["Date"] == "2026-07-01T00:00:00+00:00"
    assert documents[0].metadata == {
        "provider": "yfinance",
        "ticker": "AAPL",
        "period": "5d",
        "interval": "1d",
        "row_count": 2,
    }


def test_yfinance_collector_handles_empty_history(monkeypatch) -> None:
    FakeTicker.requested = []
    monkeypatch.setattr(yf, "Ticker", FakeTicker)
    collector = YFinanceMarketDataCollector(["EMPTY"])

    documents = collector.collect()

    assert len(documents) == 1
    assert documents[0].external_id == "EMPTY:5d:1d"
    assert documents[0].published_at is None
    assert documents[0].raw_payload == {"ticker": "EMPTY", "history": []}
    assert documents[0].metadata["row_count"] == 0
