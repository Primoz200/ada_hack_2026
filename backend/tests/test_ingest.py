"""The write path: sessions and the two daily ratings (v8)."""
from sqlmodel import select

from app.models import Checkin, GameSession, SessionRaw, TrendSnapshot
from app.models.schemas import SessionIn
from app.services import ingest
from tests.helpers import META, add_patient, checkin, d, play


def test_aborted_session_stored_not_scored(db):
    add_patient(db)
    row = play(db, "p", d(0), 0, completed=False)
    assert (row.score, row.impairment_class, row.counts_for_trend) == (None, None, False)
    assert db.get(SessionRaw, row.id) is not None
    assert db.exec(select(TrendSnapshot)).all() == []


def test_day_and_created_at_overrides_and_scoring_without_preset(db):
    add_patient(db)
    data = SessionIn(patient_id="p", game_type="trace", level=1, hand="right",
                     started_at="2026-09-01T10:00:00Z", duration_ms=9000, completed=True,
                     series={"targetX": [0.1, 0.9], "targetY": [0.5, 0.5], "t": [0, 1, 2],
                             "x": [0.1, 0.5, 0.9], "y": [0.5, 0.5, 0.5], "strokeId": [0, 0, 0]},
                     client_meta=META)
    row = ingest.ingest_session(db, data, day=d(3))
    assert row.day == d(3) and row.score is not None and row.model_version


def test_repeated_level_same_day_both_count(db):
    add_patient(db)
    play(db, "p", d(0), 70, hour=9)
    play(db, "p", d(0), 60, hour=10)
    rows = db.exec(select(GameSession)).all()
    assert len(rows) == 2 and all(r.counts_for_trend for r in rows)
    snap = db.exec(select(TrendSnapshot).where(TrendSnapshot.metric == "trace:1")).one()
    assert snap.n_sessions == 2


def test_checkin_stores_two_ratings_and_replaces_same_day(db):
    add_patient(db)
    first = checkin(db, "p", d(0), wellbeing=6, pain=3)
    assert first.answers == {"wellbeing": 6.0, "pain": 3.0}
    second = checkin(db, "p", d(0), wellbeing=8, pain=1)
    rows = db.exec(select(Checkin)).all()
    assert len(rows) == 1 and second.id == first.id and rows[0].answers == {"wellbeing": 8.0, "pain": 1.0}
    checkin(db, "p", d(1), wellbeing=5, pain=5)
    assert len(db.exec(select(Checkin)).all()) == 2


def test_raw_series_stored(db):
    add_patient(db)
    row = play(db, "p", d(0), 70)
    raw = db.exec(select(SessionRaw).where(SessionRaw.session_id == row.id)).one()
    assert raw.series["x"] == [0.1, 0.9] and raw.client_meta["inputDevice"] == "touch"
    assert db.exec(select(GameSession)).one().id == row.id


def test_api_session_and_checkin(client):
    pid = next(p["id"] for p in client.get("/api/patients").json()["patients"] if p["pathwayCode"] == "stroke")
    body = {
        "patientId": pid, "gameType": "trace", "level": 2, "hand": "right",
        "startedAt": "2026-11-21T10:00:00Z", "durationMs": 9000, "completed": False,
        "abortReason": "cannot_today", "series": {"x": [], "y": []},
        "clientMeta": {"inputDevice": "touch", "canvasW": 400, "canvasH": 400},
    }
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 200 and res.json()["scored"] is False and res.json()["sessionId"]
    assert client.post("/api/sessions", json={**body, "patientId": "nope"}).status_code == 404
    assert client.post("/api/sessions", json={**body, "level": 9}).status_code == 422
    r = client.post("/api/checkins", json={"patientId": pid, "wellbeing": 7, "pain": 3})
    assert r.status_code == 200 and set(r.json()) == {"checkinId"}
    assert client.post("/api/checkins", json={"patientId": pid, "wellbeing": 11, "pain": 3}).status_code == 422
    assert client.post("/api/checkins", json={"patientId": pid, "wellbeing": 5, "pain": 0}).status_code == 422
    assert client.post("/api/checkins", json={"patientId": "nope", "wellbeing": 5, "pain": 5}).status_code == 404
