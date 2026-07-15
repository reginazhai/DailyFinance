from datetime import datetime, timezone

from dailyfinance.models import RawDocument
from dailyfinance.storage import DatabaseDocumentStore
from dailyfinance.utils import derive_document_id


def make_document(
    source_name: str = "test_rss",
    external_id: str | None = "doc-1",
    title: str = "Markets climb after earnings results",
    url: str | None = "https://example.com/markets/earnings-results",
    metadata: dict | None = None,
) -> RawDocument:
    return RawDocument(
        source_name=source_name,
        external_id=external_id,
        title=title,
        url=url,
        published_at=datetime(2026, 7, 1, 14, 30, tzinfo=timezone.utc),
        content="Stocks moved higher after several companies reported earnings.",
        raw_payload={
            "source": "Example News",
            "category": "earnings",
        },
        metadata=metadata or {"feed_url": "https://example.com/feed.xml"},
    )


def make_store(tmp_path) -> DatabaseDocumentStore:
    return DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")


def test_database_document_store_saves_documents(tmp_path) -> None:
    store = make_store(tmp_path)
    document = make_document()

    store.save_documents([document])

    loaded_document = store.get_document(derive_document_id(document))
    assert loaded_document is not None
    assert loaded_document.source_name == document.source_name
    assert loaded_document.external_id == document.external_id
    assert loaded_document.title == document.title
    assert str(loaded_document.url) == str(document.url)
    assert loaded_document.content == document.content
    assert loaded_document.raw_payload == document.raw_payload
    assert loaded_document.metadata == document.metadata


def test_database_document_store_avoids_duplicate_documents(tmp_path) -> None:
    store = make_store(tmp_path)
    document = make_document()

    first_result = store.save_documents([document, document])
    second_result = store.save_documents([document])

    assert first_result.inserted_count == 1
    assert first_result.skipped_duplicates_count == 1
    assert second_result.inserted_count == 0
    assert second_result.skipped_duplicates_count == 1
    assert len(store.list_documents(limit=None)) == 1


def test_database_document_store_lists_recent_documents(tmp_path) -> None:
    store = make_store(tmp_path)
    documents = [
        make_document(external_id="doc-1", title="First document"),
        make_document(external_id="doc-2", title="Second document"),
        make_document(external_id="doc-3", title="Third document"),
    ]

    store.save_documents(documents)

    loaded_documents = store.list_documents(limit=2)
    assert [document.external_id for document in loaded_documents] == ["doc-3", "doc-2"]


def test_database_document_store_filters_by_source_name(tmp_path) -> None:
    store = make_store(tmp_path)
    store.save_documents(
        [
            make_document(source_name="rss_one", external_id="doc-1"),
            make_document(source_name="rss_two", external_id="doc-2"),
            make_document(source_name="rss_one", external_id="doc-3"),
        ]
    )

    documents = store.list_documents(limit=None, source_name="rss_one")

    assert [document.external_id for document in documents] == ["doc-3", "doc-1"]


def test_database_document_store_lists_sources_with_counts(tmp_path) -> None:
    store = make_store(tmp_path)
    store.save_documents(
        [
            make_document(source_name="rss_one", external_id="doc-1"),
            make_document(source_name="rss_two", external_id="doc-2"),
            make_document(source_name="rss_one", external_id="doc-3"),
        ]
    )

    assert store.list_sources_with_counts() == [
        {
            "source_name": "rss_one",
            "source_type": "rss",
            "url": "https://example.com/feed.xml",
            "document_count": 2,
        },
        {
            "source_name": "rss_two",
            "source_type": "rss",
            "url": "https://example.com/feed.xml",
            "document_count": 1,
        },
    ]


def test_database_document_store_derives_id_from_url_without_external_id(tmp_path) -> None:
    store = make_store(tmp_path)
    document = make_document(
        external_id=None,
        title="URL identified document",
        url="https://example.com/url-identified-document",
    )

    store.save_documents([document])

    assert store.get_document(derive_document_id(document)) is not None


def test_database_document_store_skips_invalid_documents(tmp_path) -> None:
    store = make_store(tmp_path)
    invalid_document = RawDocument(source_name="empty_source")

    result = store.save_documents([invalid_document])

    assert result.invalid_count == 1
    assert result.inserted_count == 0
    assert store.list_documents(limit=None) == []


def test_database_document_store_normalizes_url_before_deduplication(tmp_path) -> None:
    store = make_store(tmp_path)
    first_document = make_document(
        external_id=None,
        title=None,
        url="HTTPS://Example.com:443/news/story/?b=2&a=1#section",
    )
    second_document = make_document(
        external_id=None,
        title=None,
        url="https://example.com/news/story?a=1&b=2",
    )

    result = store.save_documents([first_document, second_document])

    documents = store.list_documents(limit=None)
    assert result.inserted_count == 1
    assert result.skipped_duplicates_count == 1
    assert str(documents[0].url) == "https://example.com/news/story?a=1&b=2"


def test_database_document_store_normalizes_published_at_to_utc(tmp_path) -> None:
    store = make_store(tmp_path)
    document = make_document(
        external_id="timezone-doc",
        url=None,
        metadata={"source_type": "api"},
    ).model_copy(
        update={
            "published_at": datetime(2026, 7, 1, 10, 30),
        }
    )

    store.save_documents([document])

    loaded_document = store.list_documents(limit=None)[0]
    assert loaded_document.published_at == datetime(2026, 7, 1, 10, 30, tzinfo=timezone.utc)


def test_document_id_uses_title_and_published_at_when_external_id_and_url_missing() -> None:
    first_document = RawDocument(
        source_name="title_source",
        title="Same title",
        published_at=datetime(2026, 7, 1, 10, 30, tzinfo=timezone.utc),
        raw_payload={"id": 1},
    )
    second_document = RawDocument(
        source_name="title_source",
        title="Same title",
        published_at=datetime(2026, 7, 1, 11, 30, tzinfo=timezone.utc),
        raw_payload={"id": 2},
    )

    assert derive_document_id(first_document) != derive_document_id(second_document)
