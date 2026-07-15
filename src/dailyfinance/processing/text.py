"""Text normalization helpers."""

import re


def normalize_whitespace(value: str | None) -> str | None:
    """Collapse repeated whitespace and trim text."""
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None
