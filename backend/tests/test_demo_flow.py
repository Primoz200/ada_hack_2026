"""The main demo flow (v8), end to end through the API with the REAL tracer model.

reset -> p3 (slow decline, visit in a month) has no alert -> one sloppy self-check ->
the patient is told calmly that it is going a bit worse lately, the clinician sees p3 as
"Za pregled" (yellow trend_drop). A careful or average self-check opens nothing.
"""
import pytest
from sqlmodel import Session, select

from app import db as dbmod
from app.models import GameSession, TrendSnapshot
from app.models.schemas import CheckinIn, ClientMeta, SessionIn
from app.seed.traces import BASE_DURATION_MS, TIME_LIMIT_MS, synthetic_trace
from app.services import alerts, clock, ingest
from app.services.scoring import score_to_class
from app.services.types import ScoreResult

# (lateral wobble in canvas units, pen lifts, duration in ms) per level
SLOPPY = {lv: (0.08 if lv == 1 else 0.10, 0 if lv == 1 else 4, int(TIME_LIMIT_MS[lv] * 0.9)) for lv in (1, 2, 3)}
CAREFUL = {lv: (0.006, 0, BASE_DURATION_MS[lv]) for lv in (1, 2, 3)}


def _session(level, wobble, lifts, duration_ms):
    return {
        "patientId": "p3", "gameType": "trace", "level": level, "hand": "right",
        "startedAt": clock.at(clock.today(), 10, level).isoformat(), "durationMs": duration_ms,
        "completed": True,
        "series": synthetic_trace(level, wobble, duration_ms=duration_ms, lifts=lifts, seed=f"demo:{level}"),
        "clientMeta": {"inputDevice": "mouse", "canvasW": 480, "canvasH": 480, "devicePixelRatio": 2,
                       "userAgent": "pytest"},
    }


def _p3(client):
    return next(p for p in client.get("/api/patients").json()["patients"] if p["id"] == "p3")


def _todays_sessions():
    with Session(dbmod.engine) as db:
        return db.exec(select(GameSession).where(GameSession.patient_id == "p3",
                                                 GameSession.day == clock.today())
                       .order_by(GameSession.level)).all()


def _combined_today():
    with Session(dbmod.engine) as db:
        return db.exec(select(TrendSnapshot).where(
            TrendSnapshot.patient_id == "p3", TrendSnapshot.metric == "trace:all",
            TrendSnapshot.day == clock.today())).one().delta


def _selfcheck(client, traces, wellbeing=7, pain=2):
    assert client.post("/api/checkins", json={"patientId": "p3", "wellbeing": wellbeing,
                                              "pain": pain}).status_code == 200
    states = []
    for level, (wobble, lifts, dur) in traces.items():
        r = client.post("/api/sessions", json=_session(level, wobble, lifts, dur))
        assert r.status_code == 200 and r.json()["scored"] is True
        detail = client.get("/api/patients/p3").json()
        states.append(detail["openAlert"] and (detail["openAlert"]["severity"], detail["openAlert"]["rule"]))
    return states


def _reset_and_check_start(client):
    assert client.post("/api/admin/reset").json()["ok"] is True
    p = _p3(client)
    assert p["status"] == "stable" and p["openAlertId"] is None
    assert p["daysToNextVisit"] >= 28
    assert client.get("/api/patients/p3/timeline").json()["alerts"] == []
    assert client.get("/api/patients/p3/home").json()["selfcheckDoneToday"] is False


def test_sloppy_selfcheck_opens_yellow_and_patient_hears_it_calmly(client):
    _reset_and_check_start(client)
    states = _selfcheck(client, SLOPPY)
    rows = _todays_sessions()
    scores = [r.score for r in rows]
    assert all(r.model_version.startswith("tracer-gbm") for r in rows)  # the real model, not the stand-in
    assert all(s < 60 for s in scores) and sum(scores) / 3 <= 55, scores
    assert all(s is None or s[0] != "red" for s in states), states  # never red on the way
    assert states[-1] == ("yellow", "trend_drop")
    assert -20 < _combined_today() <= -10

    p = _p3(client)
    assert p["status"] == "yellow" and p["openAlertId"] and p["daysToNextVisit"] >= 28
    ev = client.get("/api/patients/p3").json()["openAlert"]["evidence"]
    assert ev["delta"] == round(_combined_today(), 1)  # follows all three sessions, not the first
    assert {r.id for r in rows} <= set(ev["sessionIds"])
    assert client.get("/api/patients").json()["counters"]["needsAttention"] == 3
    summary = client.get("/api/patients/p3/selfcheck/summary").json()
    assert summary["trend"] == "declining" and summary["tone"] == "lower"
    assert summary["text"] == "Danes je šlo težje in zadnje dni gre nekoliko slabše kot prej. " \
                              "Vaš zdravnik ima vpogled v rezultate."
    assert (summary["levelsDone"], summary["levelsTotal"]) == (3, 3)
    assert client.get("/api/patients/p3/home").json()["selfcheckDoneToday"] is True


def test_careful_selfcheck_opens_nothing(client):
    _reset_and_check_start(client)
    states = _selfcheck(client, CAREFUL)
    scores = [r.score for r in _todays_sessions()]
    assert all(s >= 85 for s in scores), scores
    assert states == [None, None, None]
    assert _combined_today() > -5
    assert _p3(client)["status"] == "stable"
    summary = client.get("/api/patients/p3/selfcheck/summary").json()
    assert summary["trend"] != "declining" and summary["tone"] == "better"
    assert client.get("/api/patients/p3/home").json()["selfcheckDoneToday"] is True


def _ewma_yesterday(db):
    out = {}
    for lv in (1, 2, 3):
        snap = db.exec(select(TrendSnapshot).where(
            TrendSnapshot.patient_id == "p3", TrendSnapshot.metric == f"trace:{lv}",
            TrendSnapshot.day < clock.today()).order_by(TrendSnapshot.day.desc())).first()
        out[lv] = snap.ewma
    return out


@pytest.mark.parametrize("shift,opens", [(0.0, False), (+10.0, False), (-15.0, True)])
def test_p3_calibration_with_preset_scores(client, shift, opens):
    """At the current per-level EWMA (or better) nothing opens; 15 below it tips p3 over."""
    client.post("/api/admin/reset")
    meta = ClientMeta(input_device="mouse", canvasW=480, canvasH=480)
    with Session(dbmod.engine) as db:
        ewma = _ewma_yesterday(db)
        ingest.ingest_checkin(db, CheckinIn(patient_id="p3", wellbeing=7, pain=2))
        for lv in (1, 2, 3):
            score = ewma[lv] + shift
            ingest.ingest_session(
                db, SessionIn(patient_id="p3", game_type="trace", level=lv, hand="right",
                              started_at=clock.now(), duration_ms=10000, completed=True,
                              series={"x": [0.1], "y": [0.5]}, client_meta=meta),
                preset_score=ScoreResult({}, score, score_to_class(score), "preset"))
            a = alerts.open_alert(db, "p3")
            assert a is None or a.severity == "yellow"
        a = alerts.open_alert(db, "p3")
        assert (a is not None) is opens
        if opens:
            assert a.rule == "trend_drop"
