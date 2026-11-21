"""The ten patient stories (plan section 10) and their acceptance checks, via the API."""
import time
from datetime import timedelta

import pytest
from sqlmodel import Session, select

from app import db as dbmod
from app import seed
from app.models import Alert, Checkin, GameSession, Message, Patient
from app.services import clock

from .conftest import TODAY


@pytest.fixture(scope="module")
def seeded_engine():
    """One seeded database shared by the read-only tests of this module."""
    old = dbmod.engine
    dbmod.set_engine(dbmod.make_engine("sqlite://"))
    clock.reset()
    clock.set_today(TODAY)
    seed.reset_database()
    yield dbmod.engine
    clock.reset()
    dbmod.set_engine(old)


@pytest.fixture(autouse=True)
def _fresh_db(seeded_engine):  # replaces the conftest fixture of the same name
    dbmod.set_engine(seeded_engine)
    clock.reset()
    clock.set_today(TODAY)
    yield
    clock.reset()


def _snapshot():
    """All data by value (ids and wall-clock stamps left out)."""
    with Session(dbmod.engine) as db:
        sessions = [(s.patient_id, s.day, s.level, s.score, s.duration_ms, s.features)
                    for s in db.exec(select(GameSession).order_by(GameSession.id)).all()]
        checkins = [(c.patient_id, c.day, c.answers, c.warning_signs, c.concern, c.concern_text)
                    for c in db.exec(select(Checkin).order_by(Checkin.id)).all()]
        alerts = [(a.patient_id, a.rule, a.severity, a.status, a.opened_day, a.outcome, a.note,
                   a.diverging, a.reason) for a in db.exec(select(Alert).order_by(Alert.id)).all()]
        patients = [(p.id, p.name, p.discharge_date, p.next_visit_date)
                    for p in db.exec(select(Patient).order_by(Patient.id)).all()]
    return sessions, checkins, alerts, patients


def test_two_resets_are_identical():
    t = time.perf_counter()
    seed.reset_database()
    elapsed = time.perf_counter() - t
    first = _snapshot()
    seed.reset_database()
    assert _snapshot() == first
    assert first[0] and first[1] and first[2]
    assert elapsed < 10


def _by_id(client):
    return {p["id"]: p for p in client.get("/api/patients").json()["patients"]}


def _alerts(client, pid):
    return client.get(f"/api/patients/{pid}/timeline").json()["alerts"]


def test_patient_ids_and_today(client):
    ps = _by_id(client)
    assert set(ps) == {f"p{i}" for i in range(1, 10)} | {"demo"}
    assert client.get("/api/meta").json()["today"] == TODAY.isoformat()


def test_p3_main_demo_story(client):
    p = _by_id(client)["p3"]
    assert p["status"] == "yellow" and p["diverging"] is True
    detail = client.get("/api/patients/p3").json()
    alert = detail["openAlert"]
    assert alert["rule"] == "trend_drop" and alert["severity"] == "yellow"
    assert alert["diverging"] is True
    opened = clock.today() - __import__("datetime").date.fromisoformat(alert["openedDay"])
    assert 1 <= opened.days <= 3
    open_ones = [a for a in _alerts(client, "p3") if a["status"] != "closed"]
    assert len(open_ones) == 1 and len(_alerts(client, "p3")) == 1


def test_p8_never_alerts(client):
    assert _alerts(client, "p8") == []
    assert _by_id(client)["p8"]["status"] == "stable"


def test_p4_red_from_questionnaire(client):
    assert _by_id(client)["p4"]["status"] == "red"
    detail = client.get("/api/patients/p4").json()
    assert detail["openAlert"]["severity"] == "red" and detail["openAlert"]["source"] == "checkin"
    assert detail["nextVisitDate"] is None
    tl = client.get("/api/patients/p4/timeline").json()
    last = tl["checkins"][-1]
    assert last["concern"] == "call" and last["concernText"] and last["warningSigns"]


def test_p7_no_data_only(client):
    ps = _by_id(client)
    assert ps["p7"]["status"] == "no_data"
    red_yellow = {pid for pid, p in ps.items() if p["status"] in ("red", "yellow")}
    assert "p7" not in red_yellow


def test_p9_insufficient(client):
    assert _by_id(client)["p9"]["status"] == "insufficient_data"


def test_stable_patients(client):
    ps = _by_id(client)
    for pid in ("p1", "p2", "p5", "demo"):
        assert ps[pid]["status"] == "stable", pid
        assert ps[pid]["openAlertId"] is None, pid


def test_p6_diverging_not_red(client):
    p = _by_id(client)["p6"]
    assert p["diverging"] is True and p["status"] != "red"
    tl = client.get("/api/patients/p6/timeline").json()
    assert any(c["concernText"] for c in tl["checkins"])


def test_demo_has_no_entry_today_or_open_alert(client):
    tl = client.get("/api/patients/demo/timeline").json()
    today = TODAY.isoformat()
    assert tl["sessions"] and tl["checkins"]
    assert all(s["day"] < today for s in tl["sessions"])
    assert all(c["day"] < today for c in tl["checkins"])
    assert max(c["day"] for c in tl["checkins"]) == (TODAY - timedelta(days=1)).isoformat()
    assert client.get("/api/patients/demo").json()["openAlert"] is None


def test_triage_counters(client):
    counters = client.get("/api/patients").json()["counters"]
    assert counters["needsAttention"] == 2
    assert counters["noData"] == 1
    assert counters["total"] == 10


def test_history_has_closed_alerts_and_messages(client):
    closed = [a for pid in ("p1", "p5") for a in _alerts(client, pid)]
    assert closed and all(a["status"] == "closed" and a["outcome"] and a["note"] for a in closed)
    with Session(dbmod.engine) as db:
        msgs = db.exec(select(Message).where(Message.patient_id == "p1")).all()
    assert {m.direction for m in msgs} == {"to_patient", "system"}


def test_no_raw_series_in_lists_and_raw_endpoint(client):
    assert "series" not in str(client.get("/api/patients").json())
    tl = client.get("/api/patients/p1/timeline").json()
    assert "series" not in str(tl)
    from app.seed.traces import LEVEL_PATHS
    for level in (1, 2, 3):
        s = next(x for x in tl["sessions"] if x["level"] == level)
        raw = client.get(f"/api/sessions/{s['id']}/raw").json()["series"]
        assert len(raw["targetX"]) == len(LEVEL_PATHS[level]) == len(raw["targetY"])
        n = len(raw["x"])
        assert 60 <= n <= 200 and len(raw["y"]) == len(raw["t"]) == len(raw["strokeId"]) == n
        assert all(0 <= v <= 1 for v in raw["x"] + raw["y"] + raw["targetX"] + raw["targetY"])


def test_adherence_has_gaps_but_no_long_runs(client):
    for pid in ("p1", "p2", "p5", "p8"):
        days = {c["day"] for c in client.get(f"/api/patients/{pid}/timeline").json()["checkins"]}
        first = min(days)
        d = __import__("datetime").date.fromisoformat(first)
        run = longest = 0
        while d < TODAY:
            run = 0 if d.isoformat() in days else run + 1
            longest = max(longest, run)
            d += timedelta(days=1)
        assert longest <= 2, pid
