from datetime import datetime, timezone

from dailyfinance.models import RawDocument
from dailyfinance.refresh import main, run_refresh
from dailyfinance.storage import DatabaseDocumentStore


class MockCollector:
    """Offline collector used for refresh tests."""

    def collect(self):
        return [
            RawDocument(
                source_name="rss_source",
                external_id="doc-1",
                title="$NVDA daily market update",
                content="Nvidia shares moved after artificial intelligence demand rose.",
                published_at=datetime.now(timezone.utc),
                metadata={"feed_url": "https://example.com/feed.xml"},
            )
        ]


def test_run_refresh_collects_migrates_processes_and_indexes(tmp_path) -> None:
    jsonl_path = tmp_path / "raw_documents.jsonl"
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"

    result = run_refresh(
        [MockCollector()],
        jsonl_path=jsonl_path,
        database_url=database_url,
        limit=100,
    )

    store = DatabaseDocumentStore(database_url)
    total, search_results = store.search_processed_documents(query="NVDA")

    assert result.ingestion.stats.collected == 1
    assert result.ingestion.stats.inserted == 1
    assert result.migration.inserted_count == 1
    assert result.processing.processed == 1
    assert result.search_index["indexed"] == 1
    assert total == 1
    assert search_results[0].tickers == ["NVDA"]


def test_run_refresh_is_idempotent(tmp_path) -> None:
    jsonl_path = tmp_path / "raw_documents.jsonl"
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"

    first_result = run_refresh(
        [MockCollector()],
        jsonl_path=jsonl_path,
        database_url=database_url,
        limit=100,
    )
    second_result = run_refresh(
        [MockCollector()],
        jsonl_path=jsonl_path,
        database_url=database_url,
        limit=100,
    )

    assert first_result.migration.inserted_count == 1
    assert second_result.ingestion.stats.inserted == 1
    assert second_result.migration.inserted_count == 0
    assert second_result.migration.skipped_count == 2
    assert second_result.processing.processed == 0
    assert second_result.processing.already_processed == 1
    assert second_result.search_index["indexed"] == 1


def test_refresh_cli_prints_combined_summary(tmp_path, monkeypatch, capsys) -> None:
    jsonl_path = tmp_path / "raw_documents.jsonl"
    database_url = f"sqlite:///{tmp_path / 'dailyfinance.db'}"
    monkeypatch.setattr("dailyfinance.refresh.build_collectors", lambda args: [MockCollector()])
    monkeypatch.setattr(
        "sys.argv",
        [
            "dailyfinance-refresh",
            "--all-configured-rss",
            "--jsonl-path",
            str(jsonl_path),
            "--database-url",
            database_url,
            "--limit",
            "100",
        ],
    )

    main()

    output = capsys.readouterr().out
    assert "Refresh complete" in output
    assert "Collected 1 documents" in output
    assert "Inserted 1 SQLite documents" in output
    assert "Processed 1 documents" in output
    assert "Search index indexed=1 skipped=0 failed=0" in output
