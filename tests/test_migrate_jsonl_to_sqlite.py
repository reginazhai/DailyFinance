from datetime import datetime, timezone

from dailyfinance.migrate_jsonl_to_sqlite import migrate_jsonl_to_sqlite
from dailyfinance.models import RawDocument
from dailyfinance.storage import DatabaseDocumentStore, LocalJsonlDocumentStore


def make_document(external_id: str, title: str) -> RawDocument:
    return RawDocument(
        source_name="test_source",
        external_id=external_id,
        title=title,
        url=f"https://example.com/{external_id}",
        published_at=datetime(2026, 7, 1, 14, 30, tzinfo=timezone.utc),
        content=f"{title} content.",
        raw_payload={"title": title},
        metadata={"feed_url": "https://example.com/feed.xml"},
    )


def test_migrate_jsonl_to_sqlite_inserts_documents(tmp_path) -> None:
    input_path = tmp_path / "raw_documents.jsonl"
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    LocalJsonlDocumentStore(input_path).save_many(
        [
            make_document("doc-1", "First document"),
            make_document("doc-2", "Second document"),
        ]
    )

    result = migrate_jsonl_to_sqlite(input_path=input_path, database_url=database_url)

    database_store = DatabaseDocumentStore(database_url)
    assert result.inserted_count == 2
    assert result.skipped_count == 0
    assert [document.external_id for document in database_store.list_documents(limit=None)] == [
        "doc-2",
        "doc-1",
    ]


def test_migrate_jsonl_to_sqlite_skips_duplicates(tmp_path) -> None:
    input_path = tmp_path / "raw_documents.jsonl"
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    LocalJsonlDocumentStore(input_path).save_many(
        [
            make_document("doc-1", "First document"),
            make_document("doc-1", "First document"),
        ]
    )

    first_result = migrate_jsonl_to_sqlite(input_path=input_path, database_url=database_url)
    second_result = migrate_jsonl_to_sqlite(input_path=input_path, database_url=database_url)

    database_store = DatabaseDocumentStore(database_url)
    assert first_result.inserted_count == 1
    assert first_result.skipped_count == 1
    assert second_result.inserted_count == 0
    assert second_result.skipped_count == 2
    assert len(database_store.list_documents(limit=None)) == 1
