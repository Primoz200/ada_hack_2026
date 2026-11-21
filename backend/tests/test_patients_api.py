"""Read path tests. Rows are created directly; nothing here depends on the write path."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import db as dbmod
from app.main import app
from app.models import Alert, Checkin, GameSession, Message, Patient, TrendSnapshot
from app.services import clock


@pytest.fixture
def api(db):
    # one placeholder patient so the app lifespan does not seed the dev dataset
    with Session(dbmod.engine) as s:
        t = clock.today()
        s.add(Patient(id="base", name="Base", birth_year=1950, pathway_code="stroke", side="right",
                      discharge_date=t - timedelta(days=1), sort_order=50))
        s.commit()
    with TestClient(app) as c:
        yield c


def _s():
    return Session(dbmod.engine)


def mk_patient(pid, sort=10, discharged=20, demo=False, pathway="stroke", visit=10):
    t = clock.today()
    with _s() as s:
        s.add(Patient(id=pid, name=f"Pac {pid}", birth_year=1950, pathway_code=pathway, side="right",
                      discharge_date=t - timedelta(days=discharged), next_visit_date=t + timedelta(days=visit),
                      is_demo=demo, sort_order=sort))
        s.commit()


def mk_checkin(pid, back, **kw):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(Checkin(patient_id=pid, day=d, created_at=clock.at(d, 8), **kw))
        s.commit()


def mk_session(pid, back, level=1, completed=True, counts=True):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(GameSession(patient_id=pid, game_type="trace", level=level, hand="right",
                          started_at=clock.at(d, 9), day=d, duration_ms=9000, completed=completed,
                          input_device="touch", score=70.0 if completed else None,
                          counts_for_trend=counts))
        s.commit()


def mk_snap(pid, back, delta, direction="stable", metric="trace:all"):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(TrendSnapshot(patient_id=pid, metric=metric, day=d, n_sessions=5, baseline=70,
                            ewma=70 + (delta or 0), delta=delta, direction=direction))
        s.commit()


def mk_alert(pid, severity, back=0, status="new", diverging=False, reason="Razlog.", ack=None):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        a = Alert(patient_id=pid, source="game", rule="r", severity=severity, status=status, reason=reason,
                  diverging=diverging, created_at=clock.at(d, 10), updated_at=clock.at(d, 10), opened_day=d,
                  acknowledged_at=ack)
        s.add(a)
        s.commit()
        return a.id


def row(api, pid):
    return next(p for p in api.get("/api/patients").json()["patients"] if p["id"] == pid)


def test_contract_shapes_and_404(api):
    assert api.get("/api/patients").status_code == 200
    for suffix in ("", "/timeline", "/today", "/progress"):
        assert api.get(f"/api/patients/base{suffix}").status_code == 200
        assert api.get(f"/api/patients/nope{suffix}").status_code == 404
    assert '"series"' not in api.get("/api/patients").text
    assert '"series"' not in api.get("/api/patients/base/timeline").text


def test_pathways(api):
    r = api.get("/api/pathways").json()
    assert {p["code"] for p in r} >= {"stroke", "ctr"}
    assert r[0]["games"][0]["levels"] and r[0]["warningSignsPrompt"]


def test_status_red_yellow_grey(api):
    for pid in ("r", "y", "g"):
        mk_patient(pid)
        mk_checkin(pid, 0)
    mk_alert("r", "red", reason="Rdeč razlog.", diverging=True)
    mk_alert("y", "yellow")
    mk_alert("g", "grey")
    r = row(api, "r")
    assert (r["status"], r["reason"], r["diverging"]) == ("red", "Rdeč razlog.", True)
    assert row(api, "y")["status"] == "yellow"
    assert row(api, "g")["status"] == "no_data"
    assert r["openAlertId"]
    detail = api.get("/api/patients/r").json()
    assert detail["status"] == "red" and detail["openAlert"]["severity"] == "red"


def test_closed_alert_ignored(api):
    mk_patient("c")
    mk_checkin("c", 0)
    mk_alert("c", "red", status="closed")
    r = row(api, "c")
    assert r["status"] == "insufficient_data" and r["openAlertId"] is None


def test_no_data_and_insufficient_and_stable(api):
    mk_patient("old")
    mk_checkin("old", 5)
    r = row(api, "old")
    assert r["status"] == "no_data" and "5 dni" in r["reason"]
    mk_patient("fresh_dc", discharged=6)
    assert row(api, "fresh_dc")["status"] == "no_data"
    mk_patient("newbie", discharged=2)
    assert row(api, "newbie")["status"] == "insufficient_data"
    mk_patient("few")
    mk_checkin("few", 1)
    for b in (3, 2, 1):
        mk_session("few", b)
    r = row(api, "few")
    assert r["status"] == "insufficient_data" and "3 od 4" in r["reason"]
    mk_patient("ok")
    mk_checkin("ok", 1)
    mk_snap("ok", 1, 1.0)
    r = row(api, "ok")
    assert r["status"] == "stable" and "blizu izhodišča" in r["reason"]
    mk_patient("up")
    mk_checkin("up", 1)
    mk_snap("up", 1, 9.0, "improving")
    assert row(api, "up")["reason"] == "Rezultati so nad izhodiščem."
    assert api.get("/api/patients/up").json()["summary"]["combinedDirection"] == "improving"


def test_ordering_and_counters(api):
    for pid, sort in (("a_stable", 1), ("b_yellow", 2), ("c_red", 3), ("d_nodata", 4), ("e_insuf", 5),
                      ("f_red_old", 6)):
        mk_patient(pid, sort=sort, demo=(pid == "e_insuf"))
        if pid != "d_nodata":
            mk_checkin(pid, 0)
    mk_snap("a_stable", 0, 0.5)
    mk_alert("b_yellow", "yellow")
    mk_alert("c_red", "red", back=0)
    mk_alert("f_red_old", "red", back=3)
    # c_red was created later than f_red_old, so it has the higher alert id -> first
    body = api.get("/api/patients").json()
    ids = [p["id"] for p in body["patients"] if p["id"][1] == "_"]
    assert ids == ["c_red", "f_red_old", "b_yellow", "d_nodata", "e_insuf", "a_stable"] or \
        ids == ["f_red_old", "c_red", "b_yellow", "d_nodata", "e_insuf", "a_stable"]
    assert ids[:2] and set(ids[:2]) == {"c_red", "f_red_old"}
    c = body["counters"]
    assert c["total"] == len(body["patients"])
    assert c["needsAttention"] == 3 and c["noData"] == 1 and c["stable"] == 3  # incl. "base"
    assert c["needsAttention"] + c["noData"] + c["stable"] == c["total"]


def test_sparkline_and_checkins7d(api):
    mk_patient("sp")
    for b in (20, 13, 5, 3, 1):
        mk_snap("sp", b, float(b))
    mk_snap("sp", 2, 99.0, metric="trace:1")
    mk_snap("sp", 4, None)
    for b in (0, 1, 3, 6, 7, 9):
        mk_checkin("sp", b)
    mk_checkin("sp", 1)  # duplicate day counts once
    r = row(api, "sp")
    assert [p["value"] for p in r["sparkline"]] == [13.0, 5.0, 3.0, 1.0]
    assert [p["day"] for p in r["sparkline"]] == sorted(p["day"] for p in r["sparkline"])
    assert r["checkins7d"] == 4


def test_divergence_surfaces(api):
    mk_patient("dv")
    good = {"arm_function": 5, "fatigue": 0, "fall": 0}
    mk_checkin("dv", 0, answers=good)
    mk_checkin("dv", 1, answers=good)
    mk_checkin("dv", 9, answers={"arm_function": 3, "fatigue": 2, "fall": 0})
    mk_snap("dv", 0, -15.0, "declining")
    assert row(api, "dv")["diverging"] is True
    assert api.get("/api/patients/dv").json()["diverging"] is True
    mk_patient("dv2")
    mk_alert("dv2", "yellow", diverging=True)
    assert row(api, "dv2")["diverging"] is True


def test_timeline_ordering_no_series(api):
    mk_patient("tl")
    mk_session("tl", 1)
    mk_session("tl", 3)
    mk_checkin("tl", 2)
    mk_checkin("tl", 4)
    mk_snap("tl", 1, 1.0)
    mk_snap("tl", 3, 2.0)
    t = api.get("/api/patients/tl/timeline").json()
    for key in ("sessions", "checkins", "trends"):
        assert len(t[key]) == 2
        days = [x["day"] for x in t[key]]
        assert days == sorted(days)
    assert "series" not in str(t)


def test_today_tasks_streak_reminder(api):
    mk_patient("td")
    mk_session("td", 0, level=1)
    mk_session("td", 0, level=2, completed=False)
    t = api.get("/api/patients/td/today").json()
    done = {x["id"]: x["done"] for x in t["tasks"]}
    assert done == {"checkin": False, "trace:1": True, "trace:2": False, "trace:3": False}
    assert t["reminder"] is None and t["streakDays"] == 1
    mk_checkin("td", 0)
    assert api.get("/api/patients/td/today").json()["tasks"][0]["done"] is True


def test_streak_with_gap_and_week(api):
    mk_patient("st")
    for b in (1, 2, 3, 5, 6):
        mk_checkin("st", b)
    t = api.get("/api/patients/st/today").json()
    assert t["streakDays"] == 3  # today empty -> counts from yesterday; gap at 4
    assert t["weekDone"] == 5
    assert t["reminder"] is None
    p = api.get("/api/patients/st/progress").json()
    assert p["weekDone"] == 5 and p["weekGoal"] == 5


def test_reminder_after_two_missed_days(api):
    mk_patient("rm")
    mk_checkin("rm", 1)
    assert api.get("/api/patients/rm/today").json()["reminder"] is None
    mk_patient("rm2")
    mk_checkin("rm2", 2)
    assert "Pogrešali" in api.get("/api/patients/rm2/today").json()["reminder"]


def test_last_message_and_review(api):
    mk_patient("m")
    ack = clock.at(clock.today() - timedelta(days=1), 12)
    mk_alert("m", "yellow", status="acknowledged", ack=ack)
    with _s() as s:
        s.add(Message(patient_id="m", direction="to_patient", author="Dr", text="Pozdravljeni",
                      created_at=clock.at(clock.today() - timedelta(days=2), 9)))
        s.add(Message(patient_id="m", direction="system", text="Sistem", created_at=clock.now()))
        s.commit()
    t = api.get("/api/patients/m/today").json()
    assert t["lastMessage"]["text"] == "Pozdravljeni"
    assert t["clinicianReviewedAt"].startswith(str(clock.today() - timedelta(days=1)))
    assert api.get("/api/patients/m/progress").json()["clinicianReviewedAt"]


def test_progress_labels_and_best(api):
    mk_patient("pr")
    for b, d in ((5, -8.0), (4, 0.0), (3, 7.0), (2, 12.0), (1, 4.9)):
        mk_snap("pr", b, d)
    mk_snap("pr", 0, None)
    p = api.get("/api/patients/pr/progress").json()
    assert [x["label"] for x in p["points"]] == ["lower", "usual", "better", "better", "usual"]
    assert p["personalBestDay"] == str(clock.today() - timedelta(days=2))
