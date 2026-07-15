from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from dailyfinance.api.app import create_app
from dailyfinance.models import RawDocument
from dailyfinance.processing import ProcessingPipeline
from dailyfinance.storage import DatabaseDocumentStore


def make_client(tmp_path) -> tuple[TestClient, str]:
    store = DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")
    raw_document = RawDocument(
        source_name="rss_source",
        external_id="doc-1",
        title="$AAPL earnings update",
        content="Apple reported results.",
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )
    store.save_documents([raw_document])
    processed_document = ProcessingPipeline().process(raw_document)
    store.save_processed_document(processed_document)
    return TestClient(create_app(document_store=store)), processed_document.id


def test_processed_documents_endpoint_defaults_to_recent_records(tmp_path) -> None:
    store = DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")
    recent_raw = RawDocument(
        source_name="rss_source",
        external_id="recent-doc",
        title="$AAPL recent update",
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )
    old_raw = RawDocument(
        source_name="rss_source",
        external_id="old-doc",
        title="$MSFT old update",
        published_at=datetime.now(timezone.utc) - timedelta(days=30),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )
    store.save_documents([recent_raw, old_raw])
    processor = ProcessingPipeline()
    store.save_processed_document(processor.process(recent_raw))
    store.save_processed_document(processor.process(old_raw))
    client = TestClient(create_app(document_store=store))

    response = client.get("/processed-documents", params={"limit": 10})

    assert response.status_code == 200
    assert [document["normalized_title"] for document in response.json()] == [
        "$AAPL recent update"
    ]


def test_processed_documents_endpoint_can_include_historical_records(tmp_path) -> None:
    store = DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")
    old_raw = RawDocument(
        source_name="rss_source",
        external_id="old-doc",
        title="$MSFT old update",
        published_at=datetime.now(timezone.utc) - timedelta(days=30),
        metadata={"feed_url": "https://example.com/feed.xml"},
    )
    store.save_documents([old_raw])
    store.save_processed_document(ProcessingPipeline().process(old_raw))
    client = TestClient(create_app(document_store=store))

    response = client.get(
        "/processed-documents",
        params={"recent_only": "false", "limit": 10},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_processed_documents_endpoint_filters_results(tmp_path) -> None:
    client, _ = make_client(tmp_path)

    response = client.get(
        "/processed-documents",
        params={
            "source_name": "rss_source",
            "ticker": "AAPL",
            "document_type": "news",
            "published_from": "2026-07-01T00:00:00Z",
            "published_to": "2026-07-02T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["tickers"] == ["AAPL"]


def test_processed_document_detail_endpoint(tmp_path) -> None:
    client, processed_document_id = make_client(tmp_path)

    response = client.get(f"/processed-documents/{processed_document_id}")

    assert response.status_code == 200
    assert response.json()["id"] == processed_document_id
