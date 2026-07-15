from collections.abc import Sequence

from dailyfinance.collectors import BaseCollector
from dailyfinance.models import RawDocument
from dailyfinance.processing import IngestionPipeline
from dailyfinance.storage import LocalJsonlDocumentStore


class FakeCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "fake_source"

    def collect(self) -> Sequence[RawDocument]:
        return [
            RawDocument(
                source_name=self.source_name,
                external_id="fake-1",
                title="First fake article",
                content="First fake article content.",
            ),
            RawDocument(
                source_name=self.source_name,
                external_id="fake-2",
                title="Second fake article",
                content="Second fake article content.",
            ),
        ]


class OtherFakeCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "other_fake_source"

    def collect(self) -> Sequence[RawDocument]:
        return [
            RawDocument(
                source_name=self.source_name,
                external_id="other-fake-1",
                title="Other fake article",
                content="Other fake article content.",
            )
        ]


class FailingCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "failing_source"

    def collect(self) -> Sequence[RawDocument]:
        raise RuntimeError("collector failed")


def test_ingestion_pipeline_runs_one_collector_and_saves_documents(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "documents.jsonl")
    pipeline = IngestionPipeline(store=store)

    result = pipeline.run([FakeCollector()])

    loaded_documents = store.load_all()
    assert [document.external_id for document in result.documents] == ["fake-1", "fake-2"]
    assert [document.external_id for document in loaded_documents] == ["fake-1", "fake-2"]
    assert result.stats.collected == 2
    assert result.stats.inserted == 2
    assert result.stats.skipped_duplicates == 0
    assert result.stats.invalid == 0
    assert result.stats.failed == 0


def test_ingestion_pipeline_runs_multiple_collectors_and_saves_documents(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "documents.jsonl")
    pipeline = IngestionPipeline(store=store)

    result = pipeline.run([FakeCollector(), OtherFakeCollector()])

    loaded_documents = store.load_all()
    assert [document.external_id for document in result.documents] == [
        "fake-1",
        "fake-2",
        "other-fake-1",
    ]
    assert [document.external_id for document in loaded_documents] == [
        "fake-1",
        "fake-2",
        "other-fake-1",
    ]
    assert result.stats.collected == 3
    assert result.stats.inserted == 3


def test_ingestion_pipeline_counts_failed_collectors(tmp_path) -> None:
    store = LocalJsonlDocumentStore(tmp_path / "documents.jsonl")
    pipeline = IngestionPipeline(store=store)

    result = pipeline.run([FailingCollector(), FakeCollector()])

    assert result.stats.failed == 1
    assert result.stats.collected == 2
    assert result.stats.inserted == 2
