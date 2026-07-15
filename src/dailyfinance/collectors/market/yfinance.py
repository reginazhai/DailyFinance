"""Market data collector backed by yfinance."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any

import yfinance as yf

from dailyfinance.collectors.base import BaseCollector
from dailyfinance.models import RawDocument


class YFinanceMarketDataCollector(BaseCollector):
    """Collect recent market data for ticker symbols using yfinance."""

    def __init__(
        self,
        tickers: Sequence[str],
        period: str = "5d",
        interval: str = "1d",
        source_name: str = "yfinance",
    ) -> None:
        self.tickers = [ticker.upper() for ticker in tickers]
        self.period = period
        self.interval = interval
        self._source_name = source_name

    @property
    def source_name(self) -> str:
        """Return the stable source name for yfinance data."""
        return self._source_name

    def collect(self) -> Sequence[RawDocument]:
        """Collect recent market data for each configured ticker."""
        return [self._collect_ticker(ticker) for ticker in self.tickers]

    def _collect_ticker(self, ticker: str) -> RawDocument:
        history = yf.Ticker(ticker).history(period=self.period, interval=self.interval)
        records = _history_to_records(history)

        return RawDocument(
            source_name=self.source_name,
            external_id=f"{ticker}:{self.period}:{self.interval}",
            title=f"{ticker} recent market data",
            published_at=_latest_record_timestamp(records),
            content=f"Recent market data for {ticker} from yfinance.",
            raw_payload={
                "ticker": ticker,
                "history": records,
            },
            metadata={
                "provider": "yfinance",
                "ticker": ticker,
                "period": self.period,
                "interval": self.interval,
                "row_count": len(records),
            },
        )


def _history_to_records(history: Any) -> list[dict[str, Any]]:
    if history is None or getattr(history, "empty", False):
        return []

    records = history.reset_index().to_dict(orient="records")
    return [_to_plain_value(record) for record in records]


def _latest_record_timestamp(records: list[dict[str, Any]]) -> datetime | None:
    for record in reversed(records):
        value = record.get("Datetime") or record.get("Date")
        parsed_timestamp = _to_datetime(value)
        if parsed_timestamp:
            return parsed_timestamp
    return None


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo:
            return value
        return value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo:
            return parsed
        return parsed.replace(tzinfo=timezone.utc)
    return None


def _to_plain_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_plain_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
