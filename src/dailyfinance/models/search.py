"""Search response models."""

from datetime import datetime

from pydantic import BaseModel, Field

from dailyfinance.models.processed_documents import DocumentType, ProcessedDocument


class SearchResult(BaseModel):
    """Public search result for a processed document."""

    document_id: str
    raw_document_id: str
    title: str | None = None
    snippet: str | None = None
    source_name: str
    document_type: DocumentType
    tickers: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    url: str | None = None
    relevance_score: float


class SearchResponse(BaseModel):
    """Paginated search response."""

    total: int
    limit: int
    offset: int
    results: list[SearchResult]


class ProcessedDocumentListResponse(BaseModel):
    """Paginated processed-document response."""

    total: int
    limit: int
    offset: int
    results: list[ProcessedDocument]
