import argparse

from dailyfinance.cli import build_collectors, build_market_collectors, build_rss_collectors
from dailyfinance.collectors import RssCollector, YFinanceMarketDataCollector


def test_build_rss_collectors_from_config_file(tmp_path) -> None:
    config_path = tmp_path / "rss_sources.yaml"
    config_path.write_text(
        """
rss_sources:
  - source_name: configured_source
    feed_url: https://example.com/configured.xml
""",
        encoding="utf-8",
    )
    args = argparse.Namespace(
        source_name=None,
        feed_url=None,
        website_url=None,
        output_path=str(tmp_path / "documents.jsonl"),
        rss_config=str(config_path),
        all_configured_rss=True,
        ticker=[],
        market_period="5d",
        market_interval="1d",
    )

    collectors = build_rss_collectors(args)

    assert len(collectors) == 1
    assert collectors[0].source_name == "configured_source"
    assert collectors[0].feed_url == "https://example.com/configured.xml"


def test_build_rss_collectors_keeps_direct_feed_ingestion(tmp_path) -> None:
    args = argparse.Namespace(
        source_name="direct_source",
        feed_url="https://example.com/direct.xml",
        website_url=None,
        output_path=str(tmp_path / "documents.jsonl"),
        rss_config="config/rss_sources.yaml",
        all_configured_rss=False,
        ticker=[],
        market_period="5d",
        market_interval="1d",
    )

    collectors = build_rss_collectors(args)

    assert len(collectors) == 1
    assert collectors[0].source_name == "direct_source"
    assert collectors[0].feed_url == "https://example.com/direct.xml"


def test_build_rss_collectors_discovers_feeds_from_website(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "dailyfinance.cli.discover_feed_urls",
        lambda website_url: [
            "https://example.com/feed.xml",
            "https://example.com/atom.xml",
        ],
    )
    args = argparse.Namespace(
        source_name="discovered_source",
        feed_url=None,
        website_url="https://example.com",
        output_path=str(tmp_path / "documents.jsonl"),
        rss_config="config/rss_sources.yaml",
        all_configured_rss=False,
        ticker=[],
        market_period="5d",
        market_interval="1d",
    )

    collectors = build_rss_collectors(args)

    assert len(collectors) == 2
    assert all(isinstance(collector, RssCollector) for collector in collectors)
    assert [collector.feed_url for collector in collectors] == [
        "https://example.com/feed.xml",
        "https://example.com/atom.xml",
    ]
    assert all(collector.source_name == "discovered_source" for collector in collectors)


def test_build_market_collectors_from_tickers(tmp_path) -> None:
    args = argparse.Namespace(
        source_name=None,
        feed_url=None,
        website_url=None,
        output_path=str(tmp_path / "documents.jsonl"),
        rss_config="config/rss_sources.yaml",
        all_configured_rss=False,
        ticker=["AAPL", "MSFT"],
        market_period="1mo",
        market_interval="1d",
    )

    collectors = build_market_collectors(args)

    assert len(collectors) == 1
    assert isinstance(collectors[0], YFinanceMarketDataCollector)
    assert collectors[0].tickers == ["AAPL", "MSFT"]
    assert collectors[0].period == "1mo"
    assert collectors[0].interval == "1d"


def test_build_collectors_combines_rss_and_yfinance(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "dailyfinance.cli.discover_feed_urls",
        lambda website_url: ["https://example.com/feed.xml"],
    )
    args = argparse.Namespace(
        source_name="combined_source",
        feed_url="https://example.com/direct.xml",
        website_url="https://example.com",
        output_path=str(tmp_path / "documents.jsonl"),
        rss_config="config/rss_sources.yaml",
        all_configured_rss=False,
        ticker=["AAPL"],
        market_period="5d",
        market_interval="1d",
    )

    collectors = build_collectors(args)

    assert len(collectors) == 3
    assert isinstance(collectors[0], RssCollector)
    assert isinstance(collectors[1], RssCollector)
    assert isinstance(collectors[2], YFinanceMarketDataCollector)
