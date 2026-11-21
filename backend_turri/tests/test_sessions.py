"""Unit tests for session ingestion, raw storage, and API validation."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import column
from sqlmodel import Session, select

import app.db as database
import app.services.scoring as scoring
from app.models.tables import GameSession, GameSessionRaw, TrendSnapshot


@pytest.fixture(autouse=True)
def no_external_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the documented stand-in path without requiring external model files."""
    monkeypatch.setattr(scoring, "_load_external_scorer", lambda: None)


def session_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "patientId": "p3",
        "gameType": "trace",
        "level": 1,
        "hand": "right",
        "startedAt": "2026-11-21T10:00:00Z",
        "durationMs": 8000,
        "completed": True,
        "series": {
            "targetX": [0.0, 1.0],
            "targetY": [0.0, 0.0],
            "x": [0.0, 0.5, 1.0],
            "y": [0.0, 0.0, 0.0],
            "t": [0.0, 1.0, 2.0],
        },
        "clientMeta": {"inputDevice": "mouse", "canvasW": 800, "canvasH": 600},
    }
    payload.update(overrides)
    return payload


def test_completed_session_is_scored_keeps_raw_separate_and_snapshots_trend(
    client: TestClient,
) -> None:
    response = client.post("/api/sessions", json=session_payload())

    assert response.status_code == 200
    assert response.json() == {"sessionId": response.json()["sessionId"], "scored": True}
    session_id = response.json()["sessionId"]
    with Session(database.engine) as session:
        stored = session.get(GameSession, session_id)
        raw = session.get(GameSessionRaw, session_id)
        snapshots = list(session.exec(select(TrendSnapshot)).all())
        assert stored is not None
        assert stored.score == 100.0
        assert stored.impairment_class == "normal"
        assert stored.model_version == "standin-0.1"
        assert stored.counts_for_trend is True
        assert raw is not None
        assert raw.series["x"] == [0.0, 0.5, 1.0]
        assert raw.client_meta["inputDevice"] == "mouse"
        assert {snapshot.metric for snapshot in snapshots} == {"trace:1", "trace:all"}
        assert next(row for row in snapshots if row.metric == "trace:1").sessions == 1
        assert next(row for row in snapshots if row.metric == "trace:all").sessions == 1

    raw_response = client.get(f"/api/sessions/{session_id}/raw")
    assert raw_response.status_code == 200
    assert raw_response.json()["sessionId"] == session_id
    assert raw_response.json()["score"] == 100.0
    assert raw_response.json()["clientMeta"]["devicePixelRatio"] == 1.0


def test_aborted_session_is_saved_without_score_and_does_not_create_snapshots(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/sessions",
        json=session_payload(completed=False, abortReason="patient_left"),
    )

    assert response.status_code == 200
    assert response.json()["scored"] is False
    with Session(database.engine) as session:
        game = session.get(GameSession, response.json()["sessionId"])
        assert game is not None
        assert game.score is None
        assert game.impairment_class is None
        assert game.model_version is None
        assert game.features == {}
        assert game.counts_for_trend is False
        assert list(session.exec(select(TrendSnapshot)).all()) == []


def test_repeated_level_sessions_all_count_and_update_daily_snapshot(client: TestClient) -> None:
    ids: list[int] = []
    for index in range(4):
        started_at = datetime(2026, 11, 21, 10, index, tzinfo=UTC).isoformat()
        response = client.post("/api/sessions", json=session_payload(startedAt=started_at))
        assert response.status_code == 200
        ids.append(response.json()["sessionId"])

    with Session(database.engine) as session:
        games = list(session.exec(select(GameSession).where(column("id").in_(ids))).all())
        level_trend = session.exec(
            select(TrendSnapshot).where(TrendSnapshot.metric == "trace:1")
        ).one()
        combined = session.exec(
            select(TrendSnapshot).where(TrendSnapshot.metric == "trace:all")
        ).one()
        assert len(games) == 4
        assert level_trend.sessions == 4
        assert level_trend.baseline == 100.0
        assert level_trend.delta == 0.0
        assert combined.sessions == 1
        assert combined.delta == 0.0


def test_trace_level_validation_and_unknown_session_responses(client: TestClient) -> None:
    bad_level = client.post("/api/sessions", json=session_payload(level=4))
    missing = client.get("/api/sessions/99999/raw")

    assert bad_level.status_code == 422
    assert bad_level.json() == {"detail": "Neznana stopnja igre"}
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Seja ne obstaja"}


def test_unknown_patient_is_rejected(client: TestClient) -> None:
    response = client.post("/api/sessions", json=session_payload(patientId="unknown"))

    assert response.status_code == 404
    assert response.json() == {"detail": "Pacient ne obstaja"}
