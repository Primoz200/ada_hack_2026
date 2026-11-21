from datetime import date

from app.services import queries


def test_days_with_entry_window():
    t = date(2026, 11, 21)
    days = {date(2026, 11, x) for x in (21, 15, 14, 22)}
    assert queries.days_with_entry(days, t, 7) == 2  # 15..21 inclusive; future day ignored
