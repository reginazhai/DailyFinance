from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from dailyfinance.api.app import create_app
from dailyfinance.models import RawDocument
from dailyfinance.processing import ProcessingPipeline
from dailyfinance.rebuild_search_index import main as rebuild_search_index_main
from dailyfinance.storage import DatabaseDocumentStore


def make_store(tmp_path) -> DatabaseDocumentStore:
    return DatabaseDocumentStore(f"sqlite:///{tmp_path / 'dailyfinance.db'}")


def save_processed_documents(
    store: DatabaseDocumentStore,
    documents: list[RawDocument],
) -> None:
    processor = ProcessingPipeline()
    store.save_documents(documents)
    for document in documents:
        store.save_processed_document(processor.process(document))


def raw_document(
    external_id: str,
    title: str,
    content: str,
    *,
    source_name: str = "rss_source",
    published_at: datetime | None = None,
    metadata: dict | None = None,
    raw_payload: dict | None = None,
) -> RawDocument:
    return RawDocument(
        source_name=source_name,
        external_id=external_id,
        title=title,
        content=content,
        published_at=published_at or datetime.now(timezone.utc),
        raw_payload=raw_payload or {},
        metadata=metadata or {"feed_url": "https://example.com/feed.xml"},
    )


def test_search_finds_title_keywords(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [raw_document("doc-1", "Nvidia shares rally", "Chip demand rises.")],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get("/search", params={"q": "nvidia"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["title"] == "Nvidia shares rally"
    assert "raw_payload" not in body["results"][0]


def test_search_finds_content_keywords(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [raw_document("doc-1", "Morning update", "Liquidity conditions improved.")],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get("/search", params={"q": "liquidity"})

    assert response.status_code == 200
    assert response.json()["results"][0]["document_type"] == "news"


def test_search_finds_tickers_and_company_names(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [
            raw_document(
                "doc-1",
                "AI chip demand rises",
                "Data center demand increased.",
                metadata={"feed_url": "https://example.com/feed.xml", "tickers": ["NVDA"]},
            )
        ],
    )
    client = TestClient(create_app(document_store=store))

    ticker_response = client.get("/search", params={"q": "NVDA"})
    company_response = client.get("/search", params={"q": "Corporation"})

    assert ticker_response.status_code == 200
    assert ticker_response.json()["results"][0]["tickers"] == ["NVDA"]
    assert company_response.status_code == 200
    assert company_response.json()["results"][0]["companies"] == ["NVIDIA Corporation"]


def test_search_applies_source_ticker_type_and_date_filters(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [
            raw_document(
                "doc-1",
                "Inflation update",
                "$AAPL supply costs changed.",
                source_name="marketwatch",
                published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            ),
            raw_document(
                "doc-2",
                "Inflation update",
                "$MSFT cloud costs changed.",
                source_name="nasdaq",
                published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            ),
        ],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get(
        "/search",
        params={
            "q": "inflation",
            "source_name": "marketwatch",
            "ticker": "AAPL",
            "document_type": "news",
            "published_from": "2026-07-09T00:00:00Z",
            "published_to": "2026-07-11T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["source_name"] == "marketwatch"


def test_search_supports_pagination(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [
            raw_document("doc-1", "Earnings update one", "Revenue rose."),
            raw_document("doc-2", "Earnings update two", "Revenue rose."),
            raw_document("doc-3", "Earnings update three", "Revenue rose."),
        ],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get("/search", params={"q": "earnings", "limit": 1, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["results"]) == 1


def test_search_sorts_by_relevance(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [
            raw_document("doc-1", "Moderate relevance", "Nvidia demand rose."),
            raw_document(
                "doc-2",
                "High relevance",
                "Nvidia Nvidia Nvidia demand rose.",
            ),
        ],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get("/search", params={"q": "nvidia", "sort": "relevance"})

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["relevance_score"] >= results[1]["relevance_score"]


def test_search_sorts_by_published_date(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [
            raw_document(
                "doc-1",
                "Rates update",
                "Rates were steady.",
                published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            ),
            raw_document(
                "doc-2",
                "Rates update",
                "Rates moved higher.",
                published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            ),
        ],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get("/search", params={"q": "rates", "sort": "published_at"})

    assert response.status_code == 200
    assert response.json()["results"][0]["published_at"].startswith("2026-07-10")


def test_search_returns_empty_results_for_no_match_or_malformed_input(tmp_path) -> None:
    store = make_store(tmp_path)
    save_processed_documents(
        store,
        [raw_document("doc-1", "Nvidia shares rally", "Chip demand rises.")],
    )
    client = TestClient(create_app(document_store=store))

    no_match_response = client.get("/search", params={"q": "nonexistent"})
    malformed_response = client.get("/search", params={"q": '"unterminated'})

    assert no_match_response.status_code == 200
    assert no_match_response.json()["results"] == []
    assert malformed_response.status_code == 200
    assert malformed_response.json()["results"] == []


def test_processed_documents_endpoint_supports_total_offset_and_sorting(tmp_path) -> None:
    store = make_store(tmp_path)
    now = datetime.now(timezone.utc)
    save_processed_documents(
        store,
        [
            raw_document("doc-1", "$AAPL update", "Apple news.", published_at=now),
            raw_document(
                "doc-2",
                "$MSFT update",
                "Microsoft news.",
                published_at=now - timedelta(days=1),
            ),
        ],
    )
    client = TestClient(create_app(document_store=store))

    response = client.get(
        "/processed-documents",
        params={
            "recent_only": "false",
            "limit": 1,
            "offset": 1,
            "sort_by": "published_at",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert body["results"][0]["tickers"] == ["MSFT"]


def test_rebuild_search_index_cli_is_idempotent(tmp_path, capsys, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    store = DatabaseDocumentStore(database_url)
    save_processed_documents(
        store,
        [raw_document("doc-1", "Nvidia shares rally", "Chip demand rises.")],
    )
    monkeypatch.setattr(
        "sys.argv",
        ["dailyfinance-rebuild-search-index", "--database-url", database_url],
    )

    rebuild_search_index_main()
    rebuild_search_index_main()

    captured = capsys.readouterr()
    assert "indexed=1 skipped=0 failed=0" in captured.out
    total, results = store.search_processed_documents(query="nvidia")
    assert total == 1
    assert len(results) == 1
