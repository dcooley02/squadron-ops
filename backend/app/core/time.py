"""UTC clock helpers.

Stored timestamps remain naive UTC (TIMESTAMP WITHOUT TIME ZONE), matching the
existing schema. Prefer these helpers over the deprecated datetime.utcnow().
"""
from __future__ import annotations

from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (UTC wall clock)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_today() -> date:
    """Current UTC calendar date."""
    return utc_now().date()
