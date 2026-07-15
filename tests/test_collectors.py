from collections.abc import Sequence

from dailyfinance.collectors import BaseCollector, MockNewsCollector
from dailyfinance.models import RawDocument


class ExampleCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "example"

    def collect(self) -> Sequence[RawDocument]:
        return [
            RawDocument(
                source_name=self.source_name,
                external_id="example-1",
                title="Example market update",
                content="Markets moved on example data.",
            )
        ]


def test_collector_interface_returns_raw_documents() -> None:
    collector = ExampleCollector()

    documents = collector.collect()

    assert collector.source_name == "example"
    assert len(documents) == 1
    assert documents[0].source_name == "example"
    assert documents[0].external_id == "example-1"


def test_mock_news_collector_returns_realistic_raw_documents() -> None:
    collector = MockNewsCollector()

    documents = collector.collect()

    assert collector.source_name == "mock_news"
    assert len(documents) == 3
    assert all(isinstance(document, RawDocument) for document in documents)
    assert all(document.source_name == collector.source_name for document in documents)
    assert all(document.external_id for document in documents)
    assert all(document.title for document in documents)
    assert all(document.content for document in documents)
    assert {document.raw_payload["category"] for document in documents} == {
        "macro",
        "stocks",
        "commodities",
    }
