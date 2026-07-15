"""Processed document models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    """Supported processed document types."""

    NEWS = "news"
    MARKET_DATA = "market_data"
    FILING = "filing"
    MACRO = "macro"
    UNKNOWN = "unknown"


class ProcessedDocument(BaseModel):
    """Deterministically enriched representation of a raw document."""

    id: str = Field(min_length=1)
    raw_document_id: str = Field(min_length=1)
    document_type: DocumentType
    normalized_title: str | None = None
    normalized_content: str | None = None
    source_type: str
    tickers: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    processed_at: datetime
    processing_version: str = Field(min_length=1)
