from datetime import datetime, timedelta, timezone

from dailyfinance.models import RawDocument
from dailyfinance.process_sqlite import process_sqlite_documents
from dailyfinance.storage import DatabaseDocumentStore


def test_process_sqlite_documents_is_idempotent(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    store = DatabaseDocumentStore(database_url)
    store.save_documents(
        [
            RawDocument(
                source_name="rss_source",
                external_id="doc-1",
                title="$AAPL earnings update",
                published_at=datetime.now(timezone.utc) - timedelta(days=1),
                metadata={"feed_url": "https://example.com/feed.xml"},
            )
        ]
    )

    first_stats = process_sqlite_documents(database_url=database_url)
    second_stats = process_sqlite_documents(database_url=database_url)

    assert first_stats.examined == 1
    assert first_stats.processed == 1
    assert first_stats.already_processed == 0
    assert second_stats.examined == 1
    assert second_stats.processed == 0
    assert second_stats.already_processed == 1


def test_process_sqlite_documents_skips_historical_by_default(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    store = DatabaseDocumentStore(database_url)
    store.save_documents(
        [
            RawDocument(
                source_name="rss_source",
                external_id="old-doc",
                title="$AAPL old update",
                published_at=datetime.now(timezone.utc) - timedelta(days=30),
                metadata={"feed_url": "https://example.com/feed.xml"},
            )
        ]
    )

    default_stats = process_sqlite_documents(database_url=database_url)
    historical_stats = process_sqlite_documents(
        database_url=database_url,
        include_historical=True,
    )

    assert default_stats.examined == 0
    assert default_stats.processed == 0
    assert historical_stats.examined == 1
    assert historical_stats.processed == 1
