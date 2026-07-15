"""Deterministic source and document classification."""

from dailyfinance.models import DocumentType, RawDocument


def infer_source_type(document: RawDocument) -> str:
    """Infer source type from existing metadata and source hints."""
    source_type = document.metadata.get("source_type")
    if isinstance(source_type, str) and source_type:
        return source_type
    if document.metadata.get("provider") == "yfinance" or "ticker" in document.raw_payload:
        return "market_data"
    if "feed_url" in document.metadata:
        return "rss"
    source_name = document.source_name.lower()
    if "sec" in source_name:
        return "sec"
    if "fred" in source_name or "macro" in source_name:
        return "macro"
    return "unknown"


def infer_document_type(document: RawDocument, source_type: str) -> DocumentType:
    """Infer document type from source type and existing metadata."""
    metadata_type = document.metadata.get("document_type")
    if isinstance(metadata_type, str):
        try:
            return DocumentType(metadata_type)
        except ValueError:
            pass

    if source_type == "market_data":
        return DocumentType.MARKET_DATA
    if source_type == "rss":
        return DocumentType.NEWS
    if source_type == "sec":
        return DocumentType.FILING
    if source_type == "macro":
        return DocumentType.MACRO
    return DocumentType.UNKNOWN
