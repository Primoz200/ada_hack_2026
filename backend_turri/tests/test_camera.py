"""Camera model loading, scoring, and API coverage."""

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.services.scoring as scoring

EXERCISE = {
    "level": 1,
    "key": "hand_open",
    "name": "Dlan",
    "detector": "hand",
    "duration_s": 12.0,
    "first_cue_s": 2.0,
    "cue_period_s": 3.0,
    "n_cues": 4,
    "up_s": None,
    "open_window_s": 1.5,
    "instructions": "Odprite dlan ob znaku.",
}


def test_camera_model_loads_once_and_passes_reference_and_complete_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    reference = {"reference": "data"}
    imported: list[str] = []
    called: list[tuple[Any, ...]] = []
    exercise_without_level = {key: value for key, value in EXERCISE.items() if key != "level"}

    def score_camera(
        game_type: str,
        level: int,
        hand: str,
        duration_ms: int,
        series: dict[str, list[float | None]],
        client_meta: dict[str, Any],
        *,
        reference: Any,
    ) -> dict[str, Any]:
        called.append((game_type, level, hand, duration_ms, series, client_meta, reference))
        return {
            "score": 92.25,
            "impairment_class": "normal",
            "features": {"f": 1.25, "bad": float("nan"), "flag": True},
            "breakdown": {"movement": 80, "not_finite": float("inf")},
            "model_version": "camera-test",
            "quality_ok": True,
        }

    def fake_import(name: str) -> Any:
        imported.append(name)
        if name == "exercises":
            return SimpleNamespace(EXERCISES={1: exercise_without_level})
        if name == "scoring":
            return SimpleNamespace(
                MODEL_VERSION="camera-test",
                load_reference=lambda: reference,
                score_camera=score_camera,
            )
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setenv("APP_MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(scoring.sys, "path", scoring.sys.path.copy())
    monkeypatch.setattr(scoring.importlib, "import_module", fake_import)
    monkeypatch.setattr(scoring, "_camera_load_attempted", False)
    monkeypatch.setattr(scoring, "_camera_scorer", None)
    monkeypatch.setattr(scoring, "_camera_exercises", {})
    monkeypatch.setattr(scoring, "_camera_model_version", scoring.CAMERA_UNAVAILABLE_VERSION)
    monkeypatch.setattr(scoring, "_camera_reference", None)

    assert scoring.camera_exercises() == [EXERCISE]
    raw_meta = {"inputDevice": "camera", "canvasW": 640, "fpsMeasured": 28.5}
    raw_series: dict[str, list[float | None]] = {"x": [0.1, None], "y": [0.2, 0.3]}
    result = scoring.score_session("camera", 1, "left", 12_000, raw_series, raw_meta)
    assert scoring.score_session("camera", 1, "left", 12_000, raw_series, raw_meta) == result

    assert imported == ["exercises", "scoring"]
    assert str(tmp_path / "camera") in scoring.sys.path
    assert called == [
        ("camera", 1, "left", 12_000, raw_series, raw_meta, reference),
        ("camera", 1, "left", 12_000, raw_series, raw_meta, reference),
    ]
    assert result == {
        "score": 92.2,
        "impairment_class": "normal",
        "features": {"f": 1.25, "part_movement": 80.0},
        "model_version": "camera-test",
        "quality_ok": True,
    }


def test_camera_score_quality_and_unavailable_model_are_not_scored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_loader() -> tuple[Any, dict[int, dict[str, Any]]]:
        return (
            lambda *args: {
                "score": 99.0,
                "impairment_class": "unknown",
                "features": {"deviation": 2},
                "breakdown": {"speed": 3},
                "model_version": "camera-v2",
                "quality_ok": False,
            },
            {1: EXERCISE},
        )

    monkeypatch.setattr(scoring, "_load_camera_model", fake_loader)
    result = scoring.score_session("camera", 1, "right", 1_000, {}, {"fpsMeasured": 10})
    assert result == {
        "score": None,
        "impairment_class": None,
        "features": {"deviation": 2.0, "part_speed": 3.0},
        "model_version": "camera-v2",
        "quality_ok": False,
    }

    monkeypatch.setattr(scoring, "_load_camera_model", lambda: (None, {}))
    assert scoring.camera_exercises() == []
    assert scoring.score_session("camera", 1, "right", 1_000, {}, {}) == {
        "score": None,
        "impairment_class": None,
        "features": {},
        "model_version": "camera-unavailable",
        "quality_ok": None,
    }


def test_camera_exercise_endpoint_returns_model_data_or_empty_list(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "_load_camera_model", lambda: (None, {1: EXERCISE}))
    response = client.get("/api/camera/exercises")
    assert response.status_code == 200
    assert response.json() == [
        {
            "level": 1,
            "key": "hand_open",
            "name": "Dlan",
            "detector": "hand",
            "durationS": 12.0,
            "firstCueS": 2.0,
            "cuePeriodS": 3.0,
            "nCues": 4,
            "upS": None,
            "openWindowS": 1.5,
            "instructions": "Odprite dlan ob znaku.",
        }
    ]
    monkeypatch.setattr(scoring, "_load_camera_model", lambda: (None, {}))
    assert client.get("/api/camera/exercises").json() == []


def test_camera_session_is_persisted_unscored_when_models_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "_load_camera_model", lambda: (None, {}))
    response = client.post(
        "/api/sessions",
        json={
            "patientId": "p3",
            "gameType": "camera",
            "level": 1,
            "hand": "right",
            "startedAt": "2026-11-21T10:00:00Z",
            "durationMs": 12000,
            "completed": True,
            "series": {"x": [0.1, None], "y": [0.2, 0.3]},
            "clientMeta": {
                "inputDevice": "camera",
                "canvasW": 640,
                "canvasH": 480,
                "devicePixelRatio": 1,
                "userAgent": "test-camera",
                "videoW": 1280,
                "fpsMeasured": 28,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["scored"] is False
    session_id = response.json()["sessionId"]
    raw = client.get(f"/api/sessions/{session_id}/raw").json()
    assert raw["series"] == {"x": [0.1, None], "y": [0.2, 0.3]}
    assert raw["clientMeta"]["videoW"] == 1280
    assert raw["clientMeta"]["fpsMeasured"] == 28
