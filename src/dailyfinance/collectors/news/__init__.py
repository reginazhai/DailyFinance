"""News collectors for DailyFinance."""

from dailyfinance.collectors.news.discovery import discover_feed_urls
from dailyfinance.collectors.news.mock import MockNewsCollector
from dailyfinance.collectors.news.rss import RssCollector

__all__ = ["MockNewsCollector", "RssCollector", "discover_feed_urls"]
