"""Deterministic ticker and company extraction."""

import re

from dailyfinance.models import RawDocument


DEFAULT_TICKER_COMPANY_MAP = {
    "AAPL": "Apple Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms, Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla, Inc.",
}

TICKER_PATTERN = re.compile(r"(?<![A-Za-z0-9])\$([A-Z]{1,5})(?![A-Za-z0-9])")


def extract_tickers(document: RawDocument) -> list[str]:
    """Extract ticker symbols from structured hints and explicit $TICKER text."""
    tickers: set[str] = set()
    tickers.update(_extract_ticker_values(document.metadata.get("tickers")))
    tickers.update(_extract_ticker_values(document.raw_payload.get("tickers")))

    ticker = document.metadata.get("ticker") or document.raw_payload.get("ticker")
    if isinstance(ticker, str):
        tickers.add(ticker.upper())

    text = " ".join(
        value for value in [document.title, document.content] if isinstance(value, str)
    )
    tickers.update(match.upper() for match in TICKER_PATTERN.findall(text))

    return sorted(tickers)


def map_companies(
    tickers: list[str],
    ticker_company_map: dict[str, str] | None = None,
) -> list[str]:
    """Map tickers to company names from a small configured dictionary."""
    mapping = ticker_company_map or DEFAULT_TICKER_COMPANY_MAP
    companies = [mapping[ticker] for ticker in tickers if ticker in mapping]
    return sorted(dict.fromkeys(companies))


def _extract_ticker_values(value: object) -> set[str]:
    if isinstance(value, str):
        return {value.upper()}
    if isinstance(value, list | tuple | set):
        return {item.upper() for item in value if isinstance(item, str)}
    return set()
