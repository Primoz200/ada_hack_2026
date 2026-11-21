from datetime import date

from app.services import queries


def test_streak():
    t = date(2026, 11, 21)

    def d(*n):
        return {date(2026, 11, x) for x in n}

    assert queries.streak(d(), t) == 0
    assert queries.streak(d(21, 20, 19), t) == 3
    assert queries.streak(d(20, 19, 17), t) == 2
    assert queries.streak(d(18, 17), t) == 0


def test_days_with_entry_window():
    t = date(2026, 11, 21)
    days = {date(2026, 11, x) for x in (21, 15, 14, 22)}
    assert queries.days_with_entry(days, t, 7) == 2  # 15..21 inclusive; future day ignored
