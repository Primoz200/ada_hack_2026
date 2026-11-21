"""v8 alert rules (clinician only) and the human-in-the-loop state machine."""
import pytest

from app.services import alerts, clock
from tests.helpers import add_patient, all_alerts, baseline_days, checkin, d, open_alerts, play


def at(day_idx):
    clock.set_today(d(day_idx))


def stable(db, start, end, score=70):
    for i in range(start, end):
        play(db, "p", d(i), score)


def drifting(db):
    """Baseline 70, then six days at 62: the combined trend drifts to about -7 (below the
    baseline band, not yet -10). Returns the next day index."""
    nxt = baseline_days(db)
    for i in range(6):
        play(db, "p", d(nxt + i), 62)
    return nxt + 6


# ------------------------------------------------------------------ rule table

def test_constants():
    assert (alerts.TREND_DROP_POINTS, alerts.BELOW_BAND_POINTS, alerts.PREVIOUS_DAYS_HIT,
            alerts.PREVIOUS_DAYS_WINDOW, alerts.BIG_DROP_POINTS) == (10.0, 5.0, 2, 3, 20.0)
    assert (alerts.WELLBEING_DROP_POINTS, alerts.PAIN_RISE_POINTS, alerts.MIN_CHECKINS_PER_WEEK,
            alerts.GREY_AFTER_MISSED_DAYS) == (2.0, 2.0, 2, 4)


def test_stable_patient_with_one_bad_day_opens_nothing(db):
    add_patient(db)
    nxt = baseline_days(db)
    stable(db, nxt, nxt + 6)
    play(db, "p", d(nxt + 6), 20)  # delta -15, but the previous days were at baseline
    stable(db, nxt + 7, nxt + 12)
    assert all_alerts(db) == []


def test_drifting_patient_plus_one_bad_day_opens_yellow_trend_drop(db):
    add_patient(db)
    nxt = drifting(db)
    assert all_alerts(db) == []  # drifting alone (about -7) opens nothing
    play(db, "p", d(nxt), 45)
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source, a.status) == ("yellow", "trend_drop", "game", "new")
    assert a.reason == "Rezultati sledenja so že več dni pod pacientovim izhodiščem."
    assert a.evidence["delta"] <= -10 and a.evidence["sessionIds"]
    assert len(a.evidence["previousDeltas"]) == 3 and all(x <= -5 for x in a.evidence["previousDeltas"])
    assert a.evidence["triggers"][0]["rule"] == "trend_drop"
    assert not any(ch.isdigit() for ch in a.reason)


def test_big_drop_is_red_on_its_own(db):
    add_patient(db)
    nxt = baseline_days(db)
    stable(db, nxt, nxt + 3)
    play(db, "p", d(nxt + 3), 0)  # EWMA 70 -> 49: delta -21
    [a] = open_alerts(db)
    assert (a.severity, a.rule) == ("red", "big_drop")
    assert a.evidence["delta"] <= -20


def test_both_is_red_and_escalates_the_open_alert(db):
    add_patient(db)
    for i in range(4):
        checkin(db, "p", d(i), wellbeing=7, pain=2)
    for i in range(4, 11):
        checkin(db, "p", d(i), wellbeing=4, pain=2)
    nxt = drifting(db)
    [a] = open_alerts(db)
    assert (a.severity, a.rule) == ("yellow", "subjective_drop")  # the ratings came first
    play(db, "p", d(nxt), 45)
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("red", "both", "game")
    assert a.reason == "Padajo rezultati sledenja in počutje hkrati."
    rules = {t["rule"] for t in a.evidence["triggers"]}
    assert {"subjective_drop", "trend_drop", "both"} <= rules
    assert a.evidence["wellbeingChange"] <= -2 and a.evidence["delta"] <= -10
    assert len(all_alerts(db)) == 1


def test_subjective_drop_alone_is_yellow_and_diverging(db):
    add_patient(db)
    nxt = baseline_days(db)
    stable(db, nxt, 14)
    for i in range(14):
        if i < 7:
            checkin(db, "p", d(i), wellbeing=7, pain=2)
        else:
            checkin(db, "p", d(i), wellbeing=4, pain=4)
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("yellow", "subjective_drop", "checkin")
    # the sentence of the first trigger (wellbeing crossed first); later triggers are appended
    assert a.reason == "Pacient poroča slabše počutje kot prejšnji teden."
    assert a.evidence["triggers"][-1]["reason"] == (
        "Pacient poroča slabše počutje in močnejšo bolečino kot prejšnji teden.")
    assert a.diverging is True and a.evidence["divergence"]
    assert a.evidence["checkinIds"]


def test_pain_rise_alone(db):
    add_patient(db)
    for i in range(14):
        checkin(db, "p", d(i), wellbeing=7, pain=2 if i < 7 else 5)
    [a] = open_alerts(db)
    assert a.rule == "subjective_drop"
    assert a.reason == "Pacient poroča močnejšo bolečino kot prejšnji teden."
    assert a.evidence["painChange"] >= 2


@pytest.mark.parametrize("before,after,fires", [(7, 5, True), (7, 6, False), (5, 8, False)])
def test_wellbeing_threshold(db, before, after, fires):
    add_patient(db)
    for i in range(14):
        checkin(db, "p", d(i), wellbeing=before if i < 7 else after, pain=2)
    assert bool(open_alerts(db)) is fires


def test_each_week_needs_two_checkins(db):
    add_patient(db)
    checkin(db, "p", d(0), wellbeing=9, pain=1)
    for i in (7, 8, 9):
        checkin(db, "p", d(i), wellbeing=2, pain=9)
    assert all_alerts(db) == []


# ------------------------------------------------------------------ state machine

def test_one_open_alert_with_appended_triggers(db):
    add_patient(db)
    nxt = drifting(db)
    play(db, "p", d(nxt), 45)
    play(db, "p", d(nxt + 1), 55)
    play(db, "p", d(nxt + 2), 55)
    [a] = open_alerts(db)
    assert len(all_alerts(db)) == 1
    assert [t["rule"] for t in a.evidence["triggers"]].count("trend_drop") >= 2


def test_no_refire_after_close_same_episode_but_worse_opens_new(db):
    add_patient(db)
    nxt = drifting(db)
    play(db, "p", d(nxt), 45)
    [a] = open_alerts(db)
    at(nxt)
    alerts.acknowledge(db, a.id, "c1", True, "adjusted_exercises", "Vaje prilagojene.")
    for i in range(1, 7):  # trend stays below -10 for days: same episode, no re-fire
        at(nxt + i)
        play(db, "p", d(nxt + i), 57)
    assert open_alerts(db) == [] and len(all_alerts(db)) == 1
    at(nxt + 7)
    play(db, "p", d(nxt + 7), 0)  # much worse: red big_drop is a new alert
    [b] = open_alerts(db)
    assert (b.severity, b.rule) == ("red", "big_drop") and b.id != a.id


def test_grey_after_four_missed_days_and_auto_close(db):
    add_patient(db)
    checkin(db, "p", d(0))
    alerts.sweep(db, d(3))
    assert all_alerts(db) == []
    alerts.sweep(db, d(4))
    [g] = open_alerts(db)
    assert (g.severity, g.rule, g.source) == ("grey", "no_data", "missing")
    assert g.evidence["missedDays"] == 4 and not any(ch.isdigit() for ch in g.reason)
    alerts.sweep(db, d(5))
    assert len(all_alerts(db)) == 1  # grey never piles on
    checkin(db, "p", d(6))
    [g] = all_alerts(db)
    assert (g.status, g.closed_by, g.outcome) == ("closed", "system", None)


def test_grey_is_escalated_by_a_yellow_not_duplicated(db):
    add_patient(db)
    nxt = drifting(db)  # last entry on day nxt - 1
    alerts.sweep(db, d(nxt + 3))
    [g] = open_alerts(db)
    assert g.severity == "grey"
    play(db, "p", d(nxt + 3), 45)  # the first new entry is itself a yellow
    [a] = open_alerts(db)
    assert a.id == g.id and (a.severity, a.rule) == ("yellow", "trend_drop")


def test_acknowledge_then_escalation_returns_to_new(db):
    add_patient(db)
    nxt = drifting(db)
    play(db, "p", d(nxt), 45)
    [a] = open_alerts(db)
    a = alerts.acknowledge(db, a.id, "c1", False, None, "Pogledam jutri.")
    assert (a.status, a.acknowledged_by, a.note) == ("acknowledged", "dr. Ana Novak", "Pogledam jutri.")
    assert a.acknowledged_at is not None and a.closed_at is None
    play(db, "p", d(nxt + 1), 0)
    [b] = open_alerts(db)
    assert b.id == a.id and b.severity == "red" and b.status == "new"


def test_close_requires_outcome_and_closed_alert_stays_closed(db):
    add_patient(db)
    nxt = drifting(db)
    play(db, "p", d(nxt), 45)
    [a] = open_alerts(db)
    with pytest.raises(alerts.AlertError):
        alerts.acknowledge(db, a.id, "c1", True, None, None)
    with pytest.raises(alerts.AlertError):
        alerts.acknowledge(db, a.id, "c1", True, "made_up", None)
    a = alerts.acknowledge(db, a.id, "c1", True, "false_alarm", None)
    assert (a.status, a.outcome, a.closed_by) == ("closed", "false_alarm", "dr. Ana Novak")
    with pytest.raises(alerts.AlertError):
        alerts.acknowledge(db, a.id, "c1", True, "false_alarm", None)


def test_api_close_without_outcome_is_422(client):
    alert = client.get("/api/alerts").json()[0]
    r = client.post(f"/api/alerts/{alert['id']}/ack", json={"clinicianId": "c1", "close": True})
    assert r.status_code == 422
    assert client.post("/api/alerts/999999/ack", json={"clinicianId": "c1"}).status_code == 404
    r = client.post(f"/api/alerts/{alert['id']}/ack",
                    json={"clinicianId": "c1", "close": True, "outcome": "called_reassured", "note": "Ok."})
    assert r.status_code == 200 and r.json()["status"] == "closed" and r.json()["outcome"] == "called_reassured"
    assert all(a["id"] != alert["id"] for a in client.get("/api/alerts").json())
