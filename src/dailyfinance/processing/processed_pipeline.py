"""Deterministic raw-to-processed document pipeline."""

import hashlib
from datetime import datetime, timezone

from dailyfinance.models import ProcessedDocument, RawDocument
from dailyfinance.processing.classification import infer_document_type, infer_source_type
from dailyfinance.processing.entities import extract_tickers, map_companies
from dailyfinance.processing.processors import Processor
from dailyfinance.processing.quality import normalize_raw_document
from dailyfinance.processing.text import normalize_whitespace
from dailyfinance.utils import derive_document_id


DEFAULT_PROCESSING_VERSION = "deterministic-v1"


class ProcessingPipeline(Processor):
    """Create deterministic processed documents from immutable raw documents."""

    def __init__(
        self,
        *,
        processing_version: str = DEFAULT_PROCESSING_VERSION,
        ticker_company_map: dict[str, str] | None = None,
    ) -> None:
        self.processing_version = processing_version
        self.ticker_company_map = ticker_company_map

    def process(self, document: RawDocument) -> ProcessedDocument:
        """Process one raw document without mutating it."""
        normalized_document = normalize_raw_document(document)
        raw_document_id = derive_document_id(normalized_document)
        source_type = infer_source_type(normalized_document)
        document_type = infer_document_type(normalized_document, source_type)
        tickers = extract_tickers(normalized_document)

        return ProcessedDocument(
            id=derive_processed_document_id(raw_document_id, self.processing_version),
            raw_document_id=raw_document_id,
            document_type=document_type,
            normalized_title=normalize_whitespace(normalized_document.title),
            normalized_content=normalize_whitespace(normalized_document.content),
            source_type=source_type,
            tickers=tickers,
            companies=map_companies(tickers, self.ticker_company_map),
            published_at=normalized_document.published_at,
            processed_at=datetime.now(timezone.utc),
            processing_version=self.processing_version,
        )


def derive_processed_document_id(raw_document_id: str, processing_version: str) -> str:
    """Derive a stable processed document ID for one raw/version pair."""
    raw_id = f"{raw_document_id}:{processing_version}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
