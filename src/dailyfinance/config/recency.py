"""Recency policy configuration."""

import os
from datetime import datetime, timedelta, timezone


DEFAULT_RECENT_DAYS = 7


def get_default_recent_days() -> int:
    """Return the configured default recent-document window in days."""
    value = os.getenv("DAILYFINANCE_RECENT_DAYS")
    if not value:
        return DEFAULT_RECENT_DAYS
    try:
        return max(1, int(value))
    except ValueError:
        return DEFAULT_RECENT_DAYS


def recent_cutoff(days: int | None = None) -> datetime:
    """Return the UTC cutoff for recent daily-finance records."""
    recent_days = days if days is not None else get_default_recent_days()
    return datetime.now(timezone.utc) - timedelta(days=recent_days)
