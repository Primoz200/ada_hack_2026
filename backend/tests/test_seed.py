"""The ten patient stories (plan section 10) and their acceptance checks, via the API."""
import time
from datetime import timedelta

import pytest
from sqlmodel import Session, select

from app import db as dbmod
from app import seed
from app.models import Alert, Checkin, GameSession, Patient
from app.seed import stories as st
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
        checkins = [(c.patient_id, c.day, c.answers)
                    for c in db.exec(select(Checkin).order_by(Checkin.id)).all()]
        alerts = [(a.patient_id, a.rule, a.severity, a.status, a.opened_day, a.outcome, a.note,
                   a.diverging, a.reason, a.evidence) for a in db.exec(select(Alert).order_by(Alert.id)).all()]
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
    assert clock.today() == TODAY  # reset keeps a fixed test clock


def _by_id(client):
    return {p["id"]: p for p in client.get("/api/patients").json()["patients"]}


def _alerts(client, pid):
    return client.get(f"/api/patients/{pid}/timeline").json()["alerts"]


def _combined(client, pid):
    tl = client.get(f"/api/patients/{pid}/timeline").json()
    return [t for t in tl["trends"] if t["metric"] == "trace:all" and t["delta"] is not None]


def test_patient_ids_today_and_default(client):
    ps = _by_id(client)
    assert set(ps) == {f"p{i}" for i in range(1, 10)} | {"demo"}
    meta = client.get("/api/meta").json()
    assert meta["today"] == TODAY.isoformat() and meta["defaultPatientId"] == "p3"


def test_p3_main_demo_patient_at_reset(client):
    p = _by_id(client)["p3"]
    assert p["status"] == "stable" and p["openAlertId"] is None
    assert _alerts(client, "p3") == []  # no alert ever, not even grey
    detail = client.get("/api/patients/p3").json()
    assert detail["daysToNextVisit"] == 30 and detail["pathway"]["code"] == "stroke"
    deltas = [t["delta"] for t in _combined(client, "p3")]
    assert -9.5 <= deltas[-1] <= -8.0
    assert sum(1 for x in deltas[-4:-1] if x <= -5) >= 2
    assert min(deltas) > -10  # never reached the trend_drop line
    tl = client.get("/api/patients/p3/timeline").json()
    yesterday = (TODAY - timedelta(days=1)).isoformat()
    assert max(c["day"] for c in tl["checkins"]) == yesterday
    assert all(s["day"] < TODAY.isoformat() for s in tl["sessions"])
    last = {t["metric"]: t for t in tl["trends"] if t["day"] == yesterday}
    for lv in (1, 2, 3):
        assert 66 <= last[f"trace:{lv}"]["ewma"] <= 76  # a sloppy live trace (~45-65) tips it; a careful one (~95) does not
    ratings = [c["answers"] for c in tl["checkins"]]
    assert all(6 <= r["wellbeing"] <= 8 and 1 <= r["pain"] <= 4 for r in ratings)
    # three weeks of recovery first: the peak is clearly above the baseline
    assert max(deltas) >= 2
    home = client.get("/api/patients/p3/home").json()
    assert home["selfcheckDoneToday"] is False and home["lastSelfcheckDay"] == yesterday


def test_p4_red_both_open_before_today(client):
    assert _by_id(client)["p4"]["status"] == "red"
    detail = client.get("/api/patients/p4").json()
    a = detail["openAlert"]
    assert (a["severity"], a["rule"]) == ("red", "both")
    assert a["openedDay"] < TODAY.isoformat()
    assert a["evidence"]["delta"] <= -10 and a["evidence"]["painChange"] >= 2
    assert a["evidence"]["delta"] == round(_combined(client, "p4")[-1]["delta"], 1)
    assert detail["nextVisitDate"] is None


def test_p6_yellow_subjective_only_and_diverging(client):
    p = _by_id(client)["p6"]
    assert p["status"] == "yellow" and p["diverging"] is True
    a = client.get("/api/patients/p6").json()["openAlert"]
    assert (a["rule"], a["severity"], a["source"]) == ("subjective_drop", "yellow", "checkin")
    assert abs(_combined(client, "p6")[-1]["delta"]) < 5


def test_p7_no_data_only(client):
    ps = _by_id(client)
    assert ps["p7"]["status"] == "no_data"
    assert [a["severity"] for a in _alerts(client, "p7")] == ["grey"]


def test_p8_noisy_but_never_alerts(client):
    assert _alerts(client, "p8") == []
    assert _by_id(client)["p8"]["status"] == "stable"
    deltas = [t["delta"] for t in _combined(client, "p8")]
    assert max(deltas) - min(deltas) >= 5  # visibly noisy, incl. the bad days


def test_p9_insufficient(client):
    p9 = _by_id(client)["p9"]
    assert p9["status"] == "insufficient_data" and "2 od 4" in p9["reason"]  # two days, per level
    assert client.get("/api/patients/p9/selfcheck/summary").json()["tone"] == "first"


def test_stable_patients(client):
    ps = _by_id(client)
    for pid in ("p1", "p2", "p5", "demo"):
        assert ps[pid]["status"] == "stable", pid
        assert ps[pid]["openAlertId"] is None, pid


def test_demo_has_no_entry_today_or_open_alert(client):
    tl = client.get("/api/patients/demo/timeline").json()
    today = TODAY.isoformat()
    assert tl["sessions"] and tl["checkins"]
    assert all(s["day"] < today for s in tl["sessions"])
    assert all(c["day"] < today for c in tl["checkins"])
    assert max(c["day"] for c in tl["checkins"]) == (TODAY - timedelta(days=1)).isoformat()
    assert client.get("/api/patients/demo").json()["openAlert"] is None


def test_triage_counters(client):
    body = client.get("/api/patients").json()
    counters = body["counters"]
    assert counters["needsAttention"] == 2
    assert counters["noData"] == 1
    assert counters["total"] == 10
    assert [p["id"] for p in body["patients"][:3]] == ["p4", "p6", "p7"]


def test_history_has_a_closed_alert_with_outcome_and_note(client):
    closed = [a for pid in st.BY_ID for a in _alerts(client, pid) if a["status"] == "closed"
              and a["closedBy"] != "system"]
    assert closed and all(a["outcome"] and a["note"] for a in closed)
    p5 = [a for a in _alerts(client, "p5")]
    assert len(p5) == 1 and p5[0]["rule"] == "subjective_drop"  # no re-fire after the close
    assert client.get("/api/patients/p5/progress").json()["clinicianReviewedAt"]


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
    for pid in ("p1", "p2", "p3", "p5", "p8"):
        days = {c["day"] for c in client.get(f"/api/patients/{pid}/timeline").json()["checkins"]}
        first = min(days)
        d = __import__("datetime").date.fromisoformat(first)
        run = longest = 0
        while d < TODAY:
            run = 0 if d.isoformat() in days else run + 1
            longest = max(longest, run)
            d += timedelta(days=1)
        assert longest <= 2, pid
