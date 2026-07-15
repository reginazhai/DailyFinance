from datetime import datetime, timezone

from dailyfinance.models import RawDocument
from dailyfinance.storage import LocalJsonlDocumentStore


def make_raw_document() -> RawDocument:
    return RawDocument(
        source_name="test_source",
        external_id="doc-1",
        title="Markets climb after earnings results",
        url="https://example.com/markets/earnings-results",
        published_at=datetime(2026, 7, 1, 14, 30, tzinfo=timezone.utc),
        content="Stocks moved higher after several companies reported earnings.",
        raw_payload={
            "source": "Example News",
            "category": "earnings",
        },
        metadata={
            "topics": ["earnings", "equities"],
            "tickers": ["AAPL", "MSFT"],
        },
    )


def test_local_jsonl_document_store_saves_and_loads_raw_documents(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "documents.jsonl")
    document = make_raw_document()

    store.save(document)

    loaded_documents = store.load_all()
    loaded_document = loaded_documents[0]

    assert len(loaded_documents) == 1
    assert loaded_document.source_name == document.source_name
    assert loaded_document.external_id == document.external_id
    assert loaded_document.title == document.title
    assert str(loaded_document.url) == str(document.url)
    assert loaded_document.published_at == document.published_at
    assert loaded_document.content == document.content
    assert loaded_document.raw_payload == document.raw_payload
    assert loaded_document.metadata == document.metadata


def test_local_jsonl_document_store_saves_many_documents(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "nested" / "documents.jsonl")
    documents = [
        make_raw_document(),
        make_raw_document().model_copy(update={"external_id": "doc-2"}),
    ]

    store.save_many(documents)

    loaded_documents = store.load_all()

    assert [document.external_id for document in loaded_documents] == ["doc-1", "doc-2"]


def test_local_jsonl_document_store_returns_empty_list_for_missing_file(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "missing.jsonl")

    assert store.load_all() == []


def test_local_jsonl_document_store_keeps_saved_raw_data_unchanged(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "documents.jsonl")
    document = make_raw_document()

    store.save(document)
    document.raw_payload["category"] = "changed-after-save"

    loaded_document = store.load_all()[0]

    assert loaded_document.raw_payload["category"] == "earnings"
