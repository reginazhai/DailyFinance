"""Document ID helpers."""

import hashlib
from datetime import timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dailyfinance.models import RawDocument


def derive_document_id(document: RawDocument) -> str:
    """Derive a stable document ID from source name and source identifier."""
    identifier = document.external_id or _normalized_url_identifier(document)
    if identifier is None:
        identifier = _title_timestamp_identifier(document)
    raw_id = f"{document.source_name}:{identifier}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


def normalize_url(url: str) -> str:
    """Normalize a URL for stable document identity."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    port = parts.port

    netloc = hostname
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"

    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((scheme, netloc, path, query, ""))


def _normalized_url_identifier(document: RawDocument) -> str | None:
    if not document.url:
        return None
    return normalize_url(str(document.url))


def _title_timestamp_identifier(document: RawDocument) -> str:
    published_at = document.published_at
    if published_at and published_at.tzinfo:
        published_at = published_at.astimezone(timezone.utc)
    elif published_at:
        published_at = published_at.replace(tzinfo=timezone.utc)
    timestamp = published_at.isoformat() if published_at else ""
    return f"{document.title or ''}:{timestamp}"
