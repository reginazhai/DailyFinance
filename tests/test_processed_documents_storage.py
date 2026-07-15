from datetime import datetime, timedelta, timezone

from dailyfinance.models import RawDocument
from dailyfinance.processing import ProcessingPipeline
from dailyfinance.storage import DatabaseDocumentStore
from dailyfinance.utils import derive_document_id


def make_store(tmp_path) -> DatabaseDocumentStore:
    return DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")


def make_raw_document(external_id: str = "doc-1") -> RawDocument:
    return RawDocument(
        source_name="rss_source",
        external_id=external_id,
        title="$AAPL earnings update",
        content="Apple reported results.",
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )


def test_processed_document_persistence_is_idempotent(tmp_path) -> None:
    store = make_store(tmp_path)
    raw_document = make_raw_document()
    store.save_documents([raw_document])
    processed_document = ProcessingPipeline().process(raw_document)

    assert store.save_processed_document(processed_document) is True
    assert store.save_processed_document(processed_document) is False
    assert len(store.list_processed_documents()) == 1


def test_processed_document_persistence_and_filters(tmp_path) -> None:
    store = make_store(tmp_path)
    first_raw_document = make_raw_document("doc-1")
    second_raw_document = RawDocument(
        source_name="yfinance",
        external_id="MSFT:5d:1d",
        title="MSFT recent market data",
        raw_payload={"ticker": "MSFT", "history": []},
        metadata={"provider": "yfinance"},
    )
    store.save_documents([first_raw_document, second_raw_document])
    processor = ProcessingPipeline()
    store.save_processed_document(processor.process(first_raw_document))
    store.save_processed_document(processor.process(second_raw_document))

    ticker_results = store.list_processed_documents(ticker="AAPL")
    type_results = store.list_processed_documents(document_type="market_data")
    source_results = store.list_processed_documents(source_name="rss_source")
    detail = store.get_processed_document(ticker_results[0].id)

    assert len(ticker_results) == 1
    assert ticker_results[0].tickers == ["AAPL"]
    assert len(type_results) == 1
    assert type_results[0].raw_document_id == derive_document_id(second_raw_document)
    assert len(source_results) == 1
    assert detail is not None
    assert detail.id == ticker_results[0].id


def test_processed_document_listing_supports_recent_cutoff(tmp_path) -> None:
    store = make_store(tmp_path)
    recent_raw = make_raw_document("recent-doc").model_copy(
        update={"published_at": datetime.now(timezone.utc) - timedelta(days=1)}
    )
    old_raw = make_raw_document("old-doc").model_copy(
        update={"published_at": datetime.now(timezone.utc) - timedelta(days=30)}
    )
    store.save_documents([recent_raw, old_raw])
    processor = ProcessingPipeline()
    store.save_processed_document(processor.process(recent_raw))
    store.save_processed_document(processor.process(old_raw))

    documents = store.list_processed_documents(
        recent_cutoff=datetime.now(timezone.utc) - timedelta(days=7),
        limit=10,
    )

    assert [document.raw_document_id for document in documents] == [
        derive_document_id(recent_raw)
    ]
