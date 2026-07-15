"""Document models shared across collection and processing layers."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class RawDocument(BaseModel):
    """Raw immutable document returned by a collector."""

    source_name: str = Field(min_length=1)
    external_id: str | None = None
    title: str | None = None
    url: HttpUrl | None = None
    published_at: datetime | None = None
    content: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
