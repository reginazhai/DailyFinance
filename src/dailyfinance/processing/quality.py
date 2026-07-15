"""Small data-quality helpers for raw document ingestion."""

from datetime import timezone

from dailyfinance.models import RawDocument
from dailyfinance.utils import normalize_url


def is_valid_raw_document(document: RawDocument) -> bool:
    """Return whether a raw document has at least one useful identity/content field."""
    return any(
        [
            bool(document.title),
            bool(document.content),
            bool(document.url),
            bool(document.external_id),
            bool(document.raw_payload),
        ]
    )


def normalize_raw_document(document: RawDocument) -> RawDocument:
    """Normalize URL and timestamp fields without changing raw payload."""
    updates = {}

    if document.url:
        updates["url"] = normalize_url(str(document.url))

    if document.published_at:
        if document.published_at.tzinfo:
            updates["published_at"] = document.published_at.astimezone(timezone.utc)
        else:
            updates["published_at"] = document.published_at.replace(tzinfo=timezone.utc)

    if not updates:
        return document
    document_data = document.model_dump(mode="python")
    document_data.update(updates)
    return RawDocument.model_validate(document_data)
