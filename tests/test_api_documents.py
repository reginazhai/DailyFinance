from datetime import datetime, timezone

from fastapi.testclient import TestClient

from dailyfinance.api.app import create_app, derive_document_id
from dailyfinance.models import RawDocument
from dailyfinance.storage import DatabaseDocumentStore, LocalJsonlDocumentStore


def make_document(
    source_name: str,
    external_id: str | None,
    title: str,
    url: str | None = None,
) -> RawDocument:
    return RawDocument(
        source_name=source_name,
        external_id=external_id,
        title=title,
        url=url,
        published_at=datetime(2026, 7, 1, 14, 30, tzinfo=timezone.utc),
        content=f"{title} content.",
        raw_payload={"title": title},
        metadata={"kind": "test"},
    )


def make_client(tmp_path, documents: list[RawDocument]) -> TestClient:
    store_path = tmp_path / "documents.jsonl"
    LocalJsonlDocumentStore(store_path).save_many(documents)
    return TestClient(create_app(document_store_path=store_path))


def test_documents_endpoint_returns_recent_documents(tmp_path) -> None:
    documents = [
        make_document("rss_one", "doc-1", "First document"),
        make_document("rss_two", "doc-2", "Second document"),
        make_document("rss_one", "doc-3", "Third document"),
    ]
    client = make_client(tmp_path, documents)

    response = client.get("/documents", params={"limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert [document["external_id"] for document in body] == ["doc-3", "doc-2"]
    assert body[0]["document_id"] == derive_document_id(documents[2])
    assert body[0]["published_at"] in {
        "2026-07-01T14:30:00Z",
        "2026-07-01T14:30:00+00:00",
    }


def test_documents_endpoint_filters_by_source_name(tmp_path) -> None:
    client = make_client(
        tmp_path,
        [
            make_document("rss_one", "doc-1", "First document"),
            make_document("rss_two", "doc-2", "Second document"),
            make_document("rss_one", "doc-3", "Third document"),
        ],
    )

    response = client.get("/documents", params={"source_name": "rss_one"})

    assert response.status_code == 200
    assert [document["external_id"] for document in response.json()] == ["doc-3", "doc-1"]


def test_document_sources_endpoint_returns_counts(tmp_path) -> None:
    client = make_client(
        tmp_path,
        [
            make_document("rss_one", "doc-1", "First document"),
            make_document("rss_two", "doc-2", "Second document"),
            make_document("rss_one", "doc-3", "Third document"),
        ],
    )

    response = client.get("/documents/sources")

    assert response.status_code == 200
    assert response.json() == [
        {"source_name": "rss_one", "document_count": 2},
        {"source_name": "rss_two", "document_count": 1},
    ]


def test_document_detail_endpoint_returns_document_by_derived_id(tmp_path) -> None:
    document = make_document("rss_one", "doc-1", "First document")
    client = make_client(tmp_path, [document])

    response = client.get(f"/documents/{derive_document_id(document)}")

    assert response.status_code == 200
    assert response.json()["external_id"] == "doc-1"


def test_document_detail_endpoint_can_use_url_when_external_id_is_missing(tmp_path) -> None:
    document = make_document(
        source_name="rss_one",
        external_id=None,
        title="URL identified document",
        url="https://example.com/url-identified-document",
    )
    client = make_client(tmp_path, [document])

    response = client.get(f"/documents/{derive_document_id(document)}")

    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com/url-identified-document"


def test_document_detail_endpoint_returns_404_for_unknown_document(tmp_path) -> None:
    client = make_client(tmp_path, [])

    response = client.get("/documents/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_documents_endpoints_can_use_database_store(tmp_path) -> None:
    document = make_document("rss_one", "doc-1", "Database document")
    store = DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")
    store.save_documents([document])
    client = TestClient(create_app(document_store=store))

    list_response = client.get("/documents")
    detail_response = client.get(f"/documents/{derive_document_id(document)}")
    sources_response = client.get("/documents/sources")

    assert list_response.status_code == 200
    assert list_response.json()[0]["external_id"] == "doc-1"
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Database document"
    assert sources_response.status_code == 200
    assert sources_response.json() == [
        {
            "source_name": "rss_one",
            "source_type": "api",
            "url": None,
            "document_count": 1,
        }
    ]
