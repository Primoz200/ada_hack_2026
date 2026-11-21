"""Patient feedback at the end of the self-check: calm, honest, no numbers, no call prompts."""
import itertools

import pytest

from app.services import feedback
from tests.helpers import add_patient, baseline_days, d, play

FORBIDDEN = ("pokličite", "poklič", "112", "ambulant", "nujno", "takoj", "poslabšanje")


def test_every_patient_text_is_calm_and_has_no_numbers():
    produced = set(feedback.MESSAGES.values())
    for tone, trend in itertools.product(("first", "better", "similar", "lower"),
                                         ("unknown", "stable", "improving", "declining")):
        produced.add(feedback.message(tone, trend))
    assert len(produced) == len(set(feedback.MESSAGES.values()))  # message() only returns the table
    for title, text in produced:
        for s in (title, text):
            low = s.lower()
            assert not any(w in low for w in FORBIDDEN), s
            assert not any(ch.isdigit() for ch in s), s
            assert "razred" not in low and "okvar" not in low, s
            assert s.strip() and len(text) < 160
    # the honest declining sentence
    assert feedback.message("similar", "declining")[1] == (
        "Zadnje dni gre nekoliko slabše kot prej. Vaš zdravnik ima vpogled v rezultate.")
    # distinct wording for the combinations that matter
    keys = [("first", "unknown"), ("better", "stable"), ("similar", "stable"), ("lower", "stable"),
            ("similar", "declining"), ("similar", "improving")]
    assert len({feedback.message(*k) for k in keys}) == len(keys)


@pytest.mark.parametrize("today,previous,tone", [
    (-10.0, [-2.0, -3.0, -1.0], "lower"),
    (5.0, [0.0, 1.0], "better"),
    (1.0, [0.0], "similar"),
    (-2.9, [0.0], "similar"),
    (3.0, [], "better"),  # no previous day: compared with the baseline itself
])
def test_tone(today, previous, tone):
    assert feedback.tone_of(today, previous) == tone


@pytest.mark.parametrize("deltas,alert,trend", [
    ([0, 0, 0, 0, 0, -6], False, "declining"),
    ([-3, -4, -4, -5, -5, -6.5], False, "declining"),  # 3.5 lower than 5 session-days earlier
    ([-4, -4, -4, -5, -5, -6.5], False, "stable"),  # only 2.5 lower
    ([0, 0, 0, 0, 0, 0, -4], False, "stable"),  # inside the baseline band
    ([-8] * 6, False, "stable"),  # below baseline but not moving
    ([0, 0, 0, 0, 0, 6], False, "improving"),
    ([-1, 2], False, "stable"),
    ([0], False, "stable"),
    ([0, 0], True, "declining"),  # an open game alert
])
def test_trend(deltas, alert, trend):
    assert feedback.trend_of([float(x) for x in deltas], alert) == trend


def test_feedback_first_without_baseline(db):
    add_patient(db)
    play(db, "p", d(0), 70)
    fb = feedback.feedback_for(db, "p", d(0))
    assert (fb.tone, fb.trend, fb.day) == ("first", "unknown", None)


def test_feedback_stable_then_declining_after_drift_and_bad_day(db):
    add_patient(db)
    nxt = baseline_days(db)
    for i in range(5):
        play(db, "p", d(nxt + i), 70)
    fb = feedback.feedback_for(db, "p", d(nxt + 4))
    assert (fb.tone, fb.trend) == ("similar", "stable")
    for i in range(5, 11):
        play(db, "p", d(nxt + i), 62)
    play(db, "p", d(nxt + 11), 45)
    fb = feedback.feedback_for(db, "p", d(nxt + 11))
    assert (fb.tone, fb.trend) == ("lower", "declining")
    assert "Vaš zdravnik ima vpogled v rezultate." in fb.text
    # a later day without a session describes the latest session-day
    assert feedback.feedback_for(db, "p", d(nxt + 13)).day == d(nxt + 11)


def test_feedback_better_and_improving(db):
    add_patient(db)
    nxt = baseline_days(db, score=60)
    for i in range(6):
        play(db, "p", d(nxt + i), 60 + 3 * i)
    fb = feedback.feedback_for(db, "p", d(nxt + 5))
    assert (fb.tone, fb.trend) == ("better", "improving")
