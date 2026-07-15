"""FastAPI application for DailyFinance."""

import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from dailyfinance.config import get_default_recent_days, recent_cutoff
from dailyfinance.models import RawDocument
from dailyfinance.storage import (
    DatabaseDocumentStore,
    DocumentStore,
    LocalJsonlDocumentStore,
)
from dailyfinance.utils import derive_document_id


DEFAULT_DOCUMENT_STORE_PATH = "data/raw_documents.jsonl"
DEFAULT_DATABASE_URL = "sqlite:///data/dailyfinance.db"


def create_app(
    document_store_path: Path | str | None = None,
    *,
    document_store: DocumentStore | None = None,
    database_url: str | None = None,
    storage_backend: str | None = None,
) -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(title="DailyFinance")
    store = document_store or _build_document_store(
        document_store_path=document_store_path,
        database_url=database_url,
        storage_backend=storage_backend,
    )

    def load_documents() -> list[RawDocument]:
        return store.load_all()

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Return service health status."""
        return {"status": "ok"}

    @app.get("/documents")
    def list_documents(
        limit: int = Query(default=20, ge=1),
        source_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return recent raw documents."""
        if isinstance(store, DatabaseDocumentStore):
            documents = store.list_documents(limit=limit, source_name=source_name)
        else:
            documents = load_documents()
            if source_name:
                documents = [
                    document for document in documents if document.source_name == source_name
                ]
            documents = list(reversed(documents))[0:limit]
        return [_document_response(document) for document in documents]

    @app.get("/documents/sources")
    def list_document_sources() -> list[dict[str, Any]]:
        """Return source names with document counts."""
        if isinstance(store, DatabaseDocumentStore):
            return store.list_sources_with_counts()

        counts = Counter(document.source_name for document in load_documents())
        return [
            {"source_name": source_name, "document_count": count}
            for source_name, count in sorted(counts.items())
        ]

    @app.get("/documents/{document_id}")
    def get_document(document_id: str) -> dict[str, Any]:
        """Return one raw document by derived document ID."""
        if isinstance(store, DatabaseDocumentStore):
            document = store.get_document(document_id)
            if document is not None:
                return _document_response(document)
            raise HTTPException(status_code=404, detail="Document not found")

        for document in load_documents():
            if derive_document_id(document) == document_id:
                return _document_response(document)
        raise HTTPException(status_code=404, detail="Document not found")

    @app.get("/processed-documents")
    def list_processed_documents(
        source_name: str | None = None,
        ticker: str | None = None,
        document_type: str | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        recent_only: bool = True,
        recent_days: int | None = Query(default=None, ge=1),
        limit: int = Query(default=20, ge=1),
    ) -> list[dict[str, Any]]:
        """Return processed documents from the SQLite store."""
        if not isinstance(store, DatabaseDocumentStore):
            return []
        documents = store.list_processed_documents(
            source_name=source_name,
            ticker=ticker,
            document_type=document_type,
            published_from=published_from,
            published_to=published_to,
            recent_cutoff=recent_cutoff(recent_days or get_default_recent_days())
            if recent_only
            else None,
            limit=limit,
        )
        return [jsonable_encoder(document) for document in documents]

    @app.get("/processed-documents/{document_id}")
    def get_processed_document(document_id: str) -> dict[str, Any]:
        """Return one processed document by processed document ID."""
        if not isinstance(store, DatabaseDocumentStore):
            raise HTTPException(status_code=404, detail="Processed document not found")
        document = store.get_processed_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Processed document not found")
        return jsonable_encoder(document)

    return app


def _build_document_store(
    *,
    document_store_path: Path | str | None,
    database_url: str | None,
    storage_backend: str | None,
) -> DocumentStore:
    backend = storage_backend or os.getenv("DAILYFINANCE_STORAGE_BACKEND", "jsonl")
    if backend == "sqlite":
        return DatabaseDocumentStore(
            database_url=database_url
            or os.getenv("DAILYFINANCE_DATABASE_URL", DEFAULT_DATABASE_URL)
        )
    if backend == "jsonl":
        store_path = Path(
            document_store_path
            or os.getenv("DAILYFINANCE_DOCUMENT_STORE_PATH", DEFAULT_DOCUMENT_STORE_PATH)
        )
        return LocalJsonlDocumentStore(store_path)
    raise ValueError(f"Unsupported storage backend: {backend}")


def _document_response(document: RawDocument) -> dict[str, Any]:
    encoded_document = jsonable_encoder(document)
    return {
        "document_id": derive_document_id(document),
        **encoded_document,
    }


app = create_app()
