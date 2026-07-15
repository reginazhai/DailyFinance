"""Data collection components for DailyFinance."""

from dailyfinance.collectors.base import BaseCollector, Collector
from dailyfinance.collectors.market.yfinance import YFinanceMarketDataCollector
from dailyfinance.collectors.news.discovery import discover_feed_urls
from dailyfinance.collectors.news.mock import MockNewsCollector
from dailyfinance.collectors.news.rss import RssCollector

__all__ = [
    "BaseCollector",
    "Collector",
    "MockNewsCollector",
    "RssCollector",
    "YFinanceMarketDataCollector",
    "discover_feed_urls",
]
