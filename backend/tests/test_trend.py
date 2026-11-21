import pytest
from sqlmodel import select

from app.models import TrendSnapshot
from app.services import trend
from app.services.types import ScoredSession
from tests.helpers import add_patient, d, play, play_round


def hist(*scores):
    return [ScoredSession(d(i), 9000, 1, s) for i, s in enumerate(scores)]


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_insufficient_before_baseline(n):
    # practice + fewer than 3 baseline sessions
    r = trend.assess_trend(hist(*[60.0] * n))
    assert r.direction == "insufficient_data"
    assert r.baseline is None and r.delta_vs_baseline is None
    assert r.n_sessions == n


def test_first_session_is_practice_and_baseline_is_median_of_2_to_4():
    # session 1 (99) is discarded; median(60, 70, 80) = 70, an outlier in session 5 is not baseline
    r = trend.assess_trend(hist(99, 60, 70, 80))
    assert r.baseline == 70.0
    r2 = trend.assess_trend(hist(99, 60, 70, 80, 10))
    assert r2.baseline == 70.0


def test_ewma_numeric():
    # scores after practice: 70, 70, 70, 50, 60 -> EWMA seeded with 70
    r = trend.assess_trend(hist(10, 70, 70, 70, 50, 60))
    e = 70.0
    for x in (70, 70, 50, 60):
        e = 0.3 * x + 0.7 * e
    assert r.smoothed == pytest.approx(e)
    assert r.smoothed == pytest.approx(62.8)
    assert r.delta_vs_baseline == pytest.approx(e - 70.0)


@pytest.mark.parametrize("last,direction", [(70, "stable"), (40, "declining"), (100, "improving")])
def test_direction_by_stable_band(last, direction):
    r = trend.assess_trend(hist(70, 70, 70, 70, last, last, last, last))
    assert r.direction == direction


def test_combined_delta_helper():
    assert trend.combined_delta({1: -10.0, 2: None, 3: -4.0}) == -7.0
    assert trend.combined_delta({1: None}) is None


def snaps(db, metric):
    return {s.day: s for s in db.exec(select(TrendSnapshot).where(TrendSnapshot.metric == metric)).all()}


def test_recompute_writes_level_and_combined_rows_one_per_day(db):
    add_patient(db)
    for i in range(5):
        play_round(db, "p", d(i), 70)
    a, l1 = snaps(db, "trace:all"), snaps(db, "trace:1")
    assert set(a) == set(l1) == {d(i) for i in range(5)}
    assert a[d(1)].delta is None and a[d(3)].delta == pytest.approx(0.0)
    assert a[d(3)].baseline is None and a[d(3)].ewma is None
    assert a[d(4)].n_sessions == 5  # session-days
    assert l1[d(3)].baseline == 75.0 and l1[d(3)].n_sessions == 4
    # replaying the same day does not duplicate rows
    play_round(db, "p", d(4), 70)
    assert len(db.exec(select(TrendSnapshot).where(TrendSnapshot.day == d(4))).all()) == 4


def test_combined_ignores_level_not_played_that_day(db):
    add_patient(db)
    for i in range(5):
        play_round(db, "p", d(i), 70)
    # day 5: level 1 drops by 20, level 2 and 3 are not played -> combined = level 1 delta only
    play(db, "p", d(5), 55, level=1)
    a = snaps(db, "trace:all")[d(5)]
    l1 = snaps(db, "trace:1")[d(5)]
    assert a.delta == pytest.approx(l1.delta) and a.delta < 0
    assert d(5) not in snaps(db, "trace:2")


def test_aborted_sessions_do_not_count(db):
    add_patient(db)
    play(db, "p", d(0), 70)
    row, _, extras = play(db, "p", d(1), 0, completed=False)
    assert row.score is None and row.counts_for_trend is False
    assert extras["compared_to_usual"] == "not_scored"
    assert snaps(db, "trace:1").keys() == {d(0)}


def test_same_day_sessions_in_order(db):
    add_patient(db)
    for i in range(4):
        play(db, "p", d(i), 70)
    play(db, "p", d(4), 40, hour=9)
    play(db, "p", d(4), 80, hour=10)
    s = snaps(db, "trace:1")[d(4)]
    e = 70.0
    for x in (70, 70, 40, 80):
        e = 0.3 * x + 0.7 * e
    assert s.ewma == pytest.approx(e) and s.n_sessions == 6
