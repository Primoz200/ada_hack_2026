"""Centralized application clock."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta

_day_shift = 0


def today() -> date:
    """Return configured application date, adjusted by the runtime clock shift."""
    configured = os.getenv("APP_TODAY")
    base = date.fromisoformat(configured) if configured else datetime.now(UTC).date()
    return base + timedelta(days=_day_shift)


def now() -> datetime:
    """Return current UTC time of day on application today."""
    actual = datetime.now(UTC)
    return datetime.combine(today(), actual.timetz(), tzinfo=UTC)


def shift_days(days: int) -> None:
    """Move the application's effective date by a number of days."""
    global _day_shift
    _day_shift += days


def clear_shift() -> None:
    """Reset the application clock shift."""
    global _day_shift
    _day_shift = 0
