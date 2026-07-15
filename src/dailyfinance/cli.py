"""Command line entry points for DailyFinance."""

import argparse
from pathlib import Path

from dailyfinance.collectors import BaseCollector, RssCollector, YFinanceMarketDataCollector
from dailyfinance.collectors.news import discover_feed_urls
from dailyfinance.config import load_rss_sources
from dailyfinance.processing import IngestionPipeline
from dailyfinance.storage import LocalJsonlDocumentStore


def build_parser() -> argparse.ArgumentParser:
    """Build the ingestion CLI argument parser."""
    parser = argparse.ArgumentParser(description="Ingest finance data into a local JSONL file.")
    parser.add_argument("--source-name", help="Stable name for a direct or discovered RSS source.")
    parser.add_argument("--feed-url", help="Direct RSS or Atom feed URL to collect.")
    parser.add_argument("--website-url", help="Website URL to inspect for RSS or Atom feed links.")
    parser.add_argument("--output-path", required=True, help="Path to the output JSONL file.")
    parser.add_argument(
        "--rss-config",
        default="config/rss_sources.yaml",
        help="Path to a YAML file containing configured RSS sources.",
    )
    parser.add_argument(
        "--all-configured-rss",
        action="store_true",
        help="Ingest all RSS sources from --rss-config.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        default=[],
        help="Ticker symbol to collect with yfinance. Can be used more than once.",
    )
    parser.add_argument(
        "--market-period",
        default="5d",
        help="yfinance history period for ticker collection.",
    )
    parser.add_argument(
        "--market-interval",
        default="1d",
        help="yfinance history interval for ticker collection.",
    )
    return parser


def build_rss_collectors(args: argparse.Namespace) -> list[RssCollector]:
    """Build RSS collectors from direct, discovered, and configured sources."""
    collectors: list[RssCollector] = []

    if args.all_configured_rss:
        collectors.extend(
            RssCollector(source_name=source.source_name, feed_url=source.feed_url)
            for source in load_rss_sources(args.rss_config)
        )

    if args.feed_url:
        if not args.source_name:
            raise ValueError("--source-name and --feed-url must be provided together.")
        collectors.append(RssCollector(source_name=args.source_name, feed_url=args.feed_url))

    if args.website_url:
        if not args.source_name:
            raise ValueError("--source-name must be provided with --website-url.")
        collectors.extend(
            RssCollector(source_name=args.source_name, feed_url=feed_url)
            for feed_url in discover_feed_urls(args.website_url)
        )

    if args.source_name and not args.feed_url and not args.website_url:
        raise ValueError("--source-name requires --feed-url or --website-url.")

    return collectors


def build_market_collectors(args: argparse.Namespace) -> list[YFinanceMarketDataCollector]:
    """Build market data collectors from ticker arguments."""
    if not args.ticker:
        return []
    return [
        YFinanceMarketDataCollector(
            tickers=args.ticker,
            period=args.market_period,
            interval=args.market_interval,
        )
    ]


def build_collectors(args: argparse.Namespace) -> list[BaseCollector]:
    """Build all collectors requested by CLI arguments."""
    collectors: list[BaseCollector] = []
    collectors.extend(build_rss_collectors(args))
    collectors.extend(build_market_collectors(args))

    if not collectors:
        raise ValueError(
            "Provide RSS args, use --all-configured-rss, provide --website-url, or add --ticker."
        )

    return collectors


def main() -> None:
    """Run ingestion from command line arguments."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        collectors = build_collectors(args)
    except ValueError as error:
        parser.error(str(error))

    store = LocalJsonlDocumentStore(Path(args.output_path))
    result = IngestionPipeline(store=store).run(collectors)
    print(f"Saved {result.stats.inserted} documents to {args.output_path}")
