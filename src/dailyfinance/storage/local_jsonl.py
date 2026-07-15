"""Local JSONL storage for raw documents."""

from collections.abc import Iterable
from pathlib import Path

from dailyfinance.models import RawDocument
from dailyfinance.storage.base import DocumentStore, StorageWriteResult


class LocalJsonlDocumentStore(DocumentStore):
    """Append-only JSONL store for raw documents."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def save(self, document: RawDocument) -> StorageWriteResult:
        """Append one raw document to the JSONL file."""
        return self.save_many([document])

    def save_many(self, documents: Iterable[RawDocument]) -> StorageWriteResult:
        """Append multiple raw documents to the JSONL file."""
        inserted_count = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            for document in documents:
                file.write(document.model_dump_json())
                file.write("\n")
                inserted_count += 1
        return StorageWriteResult(inserted_count=inserted_count)

    def load_all(self) -> list[RawDocument]:
        """Load all raw documents from the JSONL file."""
        if not self.path.exists():
            return []

        documents: list[RawDocument] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line:
                    documents.append(RawDocument.model_validate_json(stripped_line))
        return documents
