"""Injectable clock. Everything that needs "today" or "now" goes through here, never
date.today() / datetime.now() directly: seed stories, missed-day alerts, simulate and
tests all depend on a controllable "today".
"""
import os
from datetime import date, datetime, time, timedelta, timezone

_fixed_today: date | None = None
_offset_days: int = 0


def today() -> date:
    if _fixed_today is not None:
        base = _fixed_today
    elif os.environ.get("APP_TODAY"):
        base = date.fromisoformat(os.environ["APP_TODAY"])
    else:
        base = date.today()
    return base + timedelta(days=_offset_days)


def now() -> datetime:
    """UTC-aware datetime on the current (possibly shifted) day. All stored datetimes are UTC-aware."""
    real = datetime.now(timezone.utc)
    return datetime.combine(today(), real.time(), tzinfo=timezone.utc)


def at(day: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)


def set_today(day: date | None) -> None:
    """Fix "today" (tests, seed replay). None restores the real date."""
    global _fixed_today
    _fixed_today = day


def advance(days: int) -> None:
    """Shift "today" forward (admin simulate)."""
    global _offset_days
    _offset_days += days


def reset() -> None:
    global _fixed_today, _offset_days
    _fixed_today = None
    _offset_days = 0
