from datetime import datetime, timezone

from dailyfinance.models import DocumentType, RawDocument
from dailyfinance.processing import ProcessingPipeline
from dailyfinance.processing.entities import extract_tickers
from dailyfinance.processing.text import normalize_whitespace


def test_whitespace_normalization() -> None:
    assert normalize_whitespace("  Markets\n\n rise\t today  ") == "Markets rise today"
    assert normalize_whitespace(" \n\t ") is None


def test_processing_pipeline_classifies_rss_as_news() -> None:
    document = RawDocument(
        source_name="rss_source",
        external_id="rss-1",
        title="  Market   update ",
        content=" Stocks\nrose. ",
        metadata={"feed_url": "https://example.com/feed.xml"},
    )

    processed = ProcessingPipeline().process(document)

    assert processed.document_type == DocumentType.NEWS
    assert processed.source_type == "rss"
    assert processed.normalized_title == "Market update"
    assert processed.normalized_content == "Stocks rose."


def test_processing_pipeline_classifies_yfinance_as_market_data() -> None:
    document = RawDocument(
        source_name="yfinance",
        external_id="AAPL:5d:1d",
        title="AAPL recent market data",
        raw_payload={"ticker": "AAPL", "history": []},
        metadata={"provider": "yfinance"},
    )

    processed = ProcessingPipeline().process(document)

    assert processed.document_type == DocumentType.MARKET_DATA
    assert processed.source_type == "market_data"
    assert processed.tickers == ["AAPL"]


def test_ticker_extraction_is_conservative() -> None:
    document = RawDocument(
        source_name="rss_source",
        external_id="rss-1",
        title="AAPL and FED are uppercase but $MSFT is explicit",
        content="Also watching $NVDA.",
        raw_payload={},
        metadata={"tickers": ["AAPL"]},
    )

    assert extract_tickers(document) == ["AAPL", "MSFT", "NVDA"]


def test_processing_pipeline_maps_companies_from_configured_mapping() -> None:
    document = RawDocument(
        source_name="rss_source",
        external_id="rss-1",
        title="$ABCD announces earnings",
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )

    processed = ProcessingPipeline(ticker_company_map={"ABCD": "ABCD Corp."}).process(document)

    assert processed.tickers == ["ABCD"]
    assert processed.companies == ["ABCD Corp."]
