from dailyfinance.collectors import MockNewsCollector
from dailyfinance.models import RawDocument
from dailyfinance.processing import CollectionPipeline


def test_collection_pipeline_runs_one_collector() -> None:
    pipeline = CollectionPipeline()
    collector = MockNewsCollector()

    documents = pipeline.run(collector)

    assert len(documents) == 3
    assert all(isinstance(document, RawDocument) for document in documents)
    assert all(document.source_name == collector.source_name for document in documents)
