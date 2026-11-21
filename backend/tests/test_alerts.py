import pytest
from sqlmodel import select

from app.models import Alert, Message
from app.services import alerts, clock
from tests.helpers import (add_patient, all_alerts, baseline_days, checkin, d, open_alerts, play)


def drop_days(db, pid="p", start=0, n=3, score=40):
    """Baseline at 70 on days start..start+3, then n bad days. Returns the last day index."""
    nxt = baseline_days(db, pid, 70, start)
    for i in range(n):
        play(db, pid, d(nxt + i), score)
    return nxt + n - 1


def at(day_idx):
    clock.set_today(d(day_idx))


# ------------------------------------------------------------------ game yellow

def test_trend_drop_needs_two_of_last_three_session_days(db):
    add_patient(db)
    nxt = baseline_days(db)
    play(db, "p", d(nxt), 40)  # EWMA 61 -> delta -9: not yet 10 points
    play(db, "p", d(nxt + 1), 40)  # delta -15.3: one hit only
    assert open_alerts(db) == []
    play(db, "p", d(nxt + 2), 40)  # second hit
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source, a.status) == ("yellow", "trend_drop", "game", "new")
    assert a.reason == "Skupni trend je že 2 od zadnjih 3 dni vsaj 10 točk pod izhodiščem."
    assert a.evidence["delta"] < -10 and a.evidence["sessionIds"]
    assert a.evidence["triggers"][0]["rule"] == "trend_drop"


def test_one_bad_day_stays_silent_and_offers_retry(db):
    add_patient(db)
    nxt = baseline_days(db)
    _, fb, extras = play(db, "p", d(nxt), 30)
    assert open_alerts(db) == []
    assert extras["offer_retry"] is True and extras["compared_to_usual"] == "lower"
    assert fb.level == "thanks" and "še enkrat" in fb.text
    play(db, "p", d(nxt + 1), 70)
    play(db, "p", d(nxt + 2), 70)
    assert all_alerts(db) == []


def test_noisy_but_stable_series_opens_no_alert(db):
    add_patient(db)
    for i in range(4):
        play(db, "p", d(i), 70)
    for i in range(21):
        play(db, "p", d(4 + i), 70 + (8 if i % 2 else -8))
    assert all_alerts(db) == []


def test_slow_decline_opens_exactly_one_yellow(db):
    add_patient(db)
    nxt = baseline_days(db)
    for i in range(21):  # three good weeks
        play(db, "p", d(nxt + i), 70 + (1 if i % 2 else -1))
    nxt += 21
    first_day = None
    for i in range(25):
        play(db, "p", d(nxt + i), 70 - 1.5 * (i + 1))
        if first_day is None and all_alerts(db):
            first_day = i
    [a] = all_alerts(db)
    assert a.severity == "yellow" and a.rule == "trend_drop"
    assert 5 <= first_day <= 14  # opens on the way down, not on day one
    assert len(a.evidence["triggers"]) > 1  # later days were appended, not new alerts


# ------------------------------------------------------------------ red

@pytest.mark.parametrize("pathway,sign,level,title", [
    ("stroke", "face", "call_112", "Takoj pokličite 112"),
    ("stroke", "speech", "call_112", "Takoj pokličite 112"),
    ("ctr", "wound_red", "call_clinic", "Še danes pokličite ambulanto"),
    ("ctr", "fever", "call_clinic", "Še danes pokličite ambulanto"),
])
def test_warning_sign_is_red_with_matching_feedback(db, pathway, sign, level, title):
    add_patient(db, pathway=pathway)
    _, fb = checkin(db, "p", d(0), signs=[sign])
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("red", "warning_sign", "checkin")
    assert a.evidence["warningSigns"] == [sign]
    assert (fb.level, fb.title) == (level, title)
    assert "obveščen" not in fb.text or level == "call_clinic"
    if level == "call_112":
        assert "112" in fb.text and "Ne čakajte" in fb.text  # never only "the team was informed"


def test_warning_sign_overrides_a_quiet_trend(db):
    add_patient(db)
    for i in range(6):
        play(db, "p", d(i), 70)
    checkin(db, "p", d(6), signs=["limb"])
    assert open_alerts(db)[0].severity == "red"


def test_red_from_game_yellow_plus_checkin_yellow(db):
    add_patient(db)
    last = drop_days(db)
    assert open_alerts(db)[0].severity == "yellow"
    _, fb = checkin(db, "p", d(last), concern="call", text="Počutim se čudno")
    [a] = open_alerts(db)
    assert (a.severity, a.rule) == ("red", "double_yellow")
    rules = [t["rule"] for t in a.evidence["triggers"]]
    assert {"trend_drop", "concern_call", "double_yellow"} <= set(rules)
    assert a.evidence["concernText"] == "Počutim se čudno"


def test_red_from_game_yellow_plus_pain_rise(db):
    add_patient(db, pathway="ctr")
    for i in range(15):  # pain 1, then 4 from day 10; game: baseline d8-d11, drop d12-d14
        if 8 <= i <= 11:
            play(db, "p", d(i), 70)
        elif i > 11:
            play(db, "p", d(i), 40)
        checkin(db, "p", d(i), answers={"pain": 1 if i < 10 else 4})
    [a] = open_alerts(db)
    assert a.severity == "red" and a.rule == "double_yellow"
    assert {"symptom_rise", "trend_drop"} <= {t["rule"] for t in a.evidence["triggers"]}


# ------------------------------------------------------------------ check-in yellow

def test_concern_call_opens_yellow(db):
    add_patient(db)
    _, fb = checkin(db, "p", d(0), concern="call", text="Prosim za klic")
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("yellow", "concern_call", "checkin")
    assert a.evidence["concernText"] == "Prosim za klic"
    assert fb.level == "neutral"
    checkin(db, "p", d(1), concern="little")  # "little" alone does not alert
    assert len(all_alerts(db)) == 1


@pytest.mark.parametrize("qid,before,after,fires", [
    ("pain", 2, 4, True), ("pain", 2, 3, False), ("tingling", 1, 2, True), ("tingling", 1, 1.5, False),
])
def test_symptom_rise_thresholds(db, qid, before, after, fires):
    add_patient(db, pathway="ctr")
    for i in range(14):
        checkin(db, "p", d(i), answers={qid: before if i < 7 else after})
    assert bool(open_alerts(db)) is fires
    if fires:
        assert open_alerts(db)[0].rule == "symptom_rise"


def test_muted_ctr_pain_pattern_early_after_discharge(db):
    # pain 1 -> 4 (<= maxValue 5) in the first 21 days after discharge: expected, no alert
    add_patient(db, pathway="ctr", discharge=d(0))
    for i in range(14):
        checkin(db, "p", d(i), answers={"pain": 1 if i < 7 else 4})
    assert all_alerts(db) == []
    # the same pattern later in recovery does alert
    add_patient(db, pid="q", pathway="ctr", discharge=d(-60))
    for i in range(14):
        checkin(db, "q", d(i), answers={"pain": 1 if i < 7 else 4})
    assert len(open_alerts(db, "q")) == 1
    # early but above the ceiling still alerts
    add_patient(db, pid="r", pathway="ctr", discharge=d(0))
    for i in range(14):
        checkin(db, "r", d(i), answers={"pain": 2 if i < 7 else 7})
    assert len(open_alerts(db, "r")) == 1


def test_divergence_flag_when_game_drops_but_patient_feels_fine(db):
    add_patient(db)
    for i in range(10):
        checkin(db, "p", d(i), answers={"arm_function": 4})
    nxt = baseline_days(db, start=10)
    for i in range(3):
        play(db, "p", d(nxt + i), 40)
        checkin(db, "p", d(nxt + i), answers={"arm_function": 4})
    [a] = open_alerts(db)
    assert a.rule == "trend_drop" and a.diverging is True
    assert "Rezultati igre padajo" in a.evidence["divergence"]


# ------------------------------------------------------------------ grey

def test_grey_after_four_missed_days_and_auto_close(db):
    add_patient(db, discharge=d(-30))
    checkin(db, "p", d(0))
    alerts.sweep(db, d(3))
    assert all_alerts(db) == []
    alerts.sweep(db, d(4))
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("grey", "no_data", "missing")
    alerts.sweep(db, d(5))
    assert len(all_alerts(db)) == 1  # a sweep never duplicates
    play(db, "p", d(6), 70)  # new data closes it by itself
    [a] = all_alerts(db)
    assert (a.status, a.closed_by, a.outcome) == ("closed", "system", None)
    assert open_alerts(db) == []


def test_grey_counts_from_discharge_and_not_for_new_discharges(db):
    add_patient(db, pid="old", discharge=d(-10))
    add_patient(db, pid="new", discharge=d(-3))
    alerts.sweep(db, d(0))
    assert len(open_alerts(db, "old")) == 1 and open_alerts(db, "new") == []
    alerts.sweep(db, d(1))
    assert len(open_alerts(db, "new")) == 1  # discharged 4 days ago now


def test_grey_is_escalated_by_yellow_not_duplicated(db):
    add_patient(db, discharge=d(-30))
    alerts.sweep(db, d(0))
    [grey] = open_alerts(db)
    checkin(db, "p", d(1), concern="call")
    [a] = all_alerts(db)
    assert a.id == grey.id and (a.severity, a.rule, a.status) == ("yellow", "concern_call", "new")
    assert [t["rule"] for t in a.evidence["triggers"]] == ["no_data", "concern_call"]


# ------------------------------------------------------------------ anti-noise + state machine

def test_one_open_alert_with_appended_triggers_and_escalation(db):
    add_patient(db)
    last = drop_days(db)
    checkin(db, "p", d(last), concern="call")
    play(db, "p", d(last + 1), 40)
    checkin(db, "p", d(last + 1), signs=["face"])
    [a] = all_alerts(db)
    assert a.severity == "red" and a.rule == "warning_sign"
    assert len(a.evidence["triggers"]) >= 4
    for t in a.evidence["triggers"]:
        assert set(t) >= {"rule", "severity", "day", "reason"}


def test_no_refire_after_ack_or_close_for_same_episode(db):
    add_patient(db)
    last = drop_days(db)
    at(last)
    [a] = open_alerts(db)
    a = alerts.acknowledge(db, a.id, "c1", False, None, None)
    assert a.status == "acknowledged" and a.acknowledged_by == "dr. Ana Novak" and a.acknowledged_at
    play(db, "p", d(last + 1), 40)  # still the same episode: appended, no new alert
    assert len(all_alerts(db)) == 1
    at(last + 1)
    alerts.acknowledge(db, a.id, "c1", True, "called_reassured", "Klic opravljen")
    for i in range(2, 6):
        play(db, "p", d(last + i), 40)
    assert len(all_alerts(db)) == 1 and open_alerts(db) == []
    # a worse severity is a new step and does open a new alert
    checkin(db, "p", d(last + 6), signs=["face"])
    [new] = open_alerts(db)
    assert new.id != a.id and new.severity == "red"


def test_acknowledged_alert_escalated_returns_to_new(db):
    add_patient(db)
    last = drop_days(db)
    at(last)
    [a] = open_alerts(db)
    alerts.acknowledge(db, a.id, "c1", False, None, None)
    checkin(db, "p", d(last + 1), signs=["face"])
    [a] = open_alerts(db)
    assert a.severity == "red" and a.status == "new" and a.acknowledged_at is None


def test_acknowledge_fields_and_system_message_once(db):
    add_patient(db)
    checkin(db, "p", d(0), signs=["face"])
    at(0)
    [a] = open_alerts(db)
    a = alerts.acknowledge(db, a.id, "c1", True, "urgent_referral", "Napoteno")
    assert a.status == "closed" and a.closed_by == "dr. Ana Novak" and a.outcome == "urgent_referral"
    assert a.note == "Napoteno" and a.acknowledged_by == "dr. Ana Novak"  # close fills ack fields too
    msgs = db.exec(select(Message).where(Message.patient_id == "p")).all()
    assert [(m.direction, m.text) for m in msgs] == [("system", "Zdravnik je pregledal vaše rezultate.")]


def test_close_requires_outcome_and_closed_alert_stays_closed(db):
    add_patient(db)
    checkin(db, "p", d(0), signs=["face"])
    [a] = open_alerts(db)
    with pytest.raises(alerts.AlertError, match="izid"):
        alerts.acknowledge(db, a.id, "c1", True, None, None)
    assert db.get(Alert, a.id).status == "new"
    alerts.acknowledge(db, a.id, "c1", True, "false_alarm", None)
    with pytest.raises(alerts.AlertError):
        alerts.acknowledge(db, a.id, "c1", False, None, None)


# ------------------------------------------------------------------ API

def test_api_close_without_outcome_is_422(client):
    patients = client.get("/api/patients").json()["patients"]
    pid = next(p["id"] for p in patients if p["pathwayCode"] == "stroke")
    res = client.post("/api/checkins", json={"patientId": pid, "warningSigns": ["face"]})
    assert res.status_code == 200 and res.json()["messageLevel"] == "call_112"
    alert = next(a for a in client.get("/api/alerts?status=open").json() if a["patientId"] == pid)
    assert alert["severity"] == "red"
    url = f"/api/alerts/{alert['id']}/ack"
    bad = client.post(url, json={"clinicianId": "c1", "close": True})
    assert bad.status_code == 422 and "izid" in bad.json()["detail"]
    assert client.post(url, json={"clinicianId": "nope"}).status_code == 404
    assert client.post("/api/alerts/999999/ack", json={"clinicianId": "c1"}).status_code == 404
    ack = client.post(url, json={"clinicianId": "c1"})
    assert ack.status_code == 200 and ack.json()["status"] == "acknowledged"
    done = client.post(url, json={"clinicianId": "c1", "close": True, "outcome": "called_reassured"})
    assert done.status_code == 200 and done.json()["status"] == "closed"
    assert client.post("/api/checkins", json={"patientId": "zzz"}).status_code == 404
