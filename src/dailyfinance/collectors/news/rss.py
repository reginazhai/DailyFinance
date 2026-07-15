"""RSS news collector backed by feedparser."""

from __future__ import annotations

import calendar
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from time import struct_time
from typing import Any

import feedparser

from dailyfinance.collectors.base import BaseCollector
from dailyfinance.models import RawDocument


class RssCollector(BaseCollector):
    """Collect raw documents from an RSS or Atom feed."""

    def __init__(self, source_name: str, feed_url: str) -> None:
        self._source_name = source_name
        self.feed_url = feed_url

    @property
    def source_name(self) -> str:
        """Return the stable name of the RSS source."""
        return self._source_name

    def collect(self) -> Sequence[RawDocument]:
        """Collect raw documents from the configured feed URL."""
        parsed_feed = feedparser.parse(self.feed_url)
        return [self._entry_to_document(entry) for entry in parsed_feed.entries]

    def _entry_to_document(self, entry: Any) -> RawDocument:
        link = _get_value(entry, "link")
        return RawDocument(
            source_name=self.source_name,
            external_id=_get_first_value(entry, ("id", "guid", "link")),
            title=_get_value(entry, "title"),
            url=link,
            published_at=_get_published_at(entry),
            content=_get_content(entry),
            raw_payload=_to_plain_value(entry),
            metadata={"feed_url": self.feed_url},
        )


def _get_value(entry: Any, key: str) -> Any:
    if isinstance(entry, Mapping):
        return entry.get(key)
    return getattr(entry, key, None)


def _get_first_value(entry: Any, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = _get_value(entry, key)
        if value:
            return str(value)
    return None


def _get_published_at(entry: Any) -> datetime | None:
    parsed_time = _get_value(entry, "published_parsed") or _get_value(entry, "updated_parsed")
    if not parsed_time:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed_time), tz=timezone.utc)


def _get_content(entry: Any) -> str | None:
    content_items = _get_value(entry, "content")
    if content_items:
        first_item = content_items[0]
        value = _get_value(first_item, "value")
        if value:
            return str(value)

    summary = _get_value(entry, "summary") or _get_value(entry, "description")
    if summary:
        return str(summary)
    return None


def _to_plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _to_plain_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, struct_time):
        return list(value)
    return value
