"""Unit tests for stand-in and external game scoring."""

from typing import Any

import pytest

import app.services.scoring as scoring


def test_standin_scores_trace_accuracy_and_speed() -> None:
    result = scoring._standin_score(
        8_000,
        {
            "targetX": [0.0, 1.0],
            "targetY": [0.0, 0.0],
            "x": [0.0, 0.5, 1.0],
            "y": [0.0, 0.0, 0.0],
        },
    )

    assert result == {
        "score": 100.0,
        "impairment_class": "normal",
        "features": {"mean_dev": 0.0, "duration_s": 8.0},
        "model_version": "standin-0.1",
    }


def test_standin_handles_missing_trace_or_target_points() -> None:
    result = scoring._standin_score(
        10_000, {"targetX": [0.0], "targetY": [0.0], "x": [0.0], "y": [0.0]}
    )

    assert result["score"] == 0.0
    assert result["impairment_class"] == "severe"
    assert result["features"] == {}


def test_external_scorer_receives_scaled_coordinates_and_replaces_bad_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, ...]] = []

    def external(
        game_type: str,
        level_id: str,
        hand: str,
        duration_ms: int,
        series: dict[str, list[float]],
        client_meta: dict[str, Any],
    ) -> dict[str, Any]:
        calls.append((game_type, level_id, hand, duration_ms, series, client_meta))
        return {
            "score": 88.26,
            "impairment_class": "unknown",
            "features": {"f": 1.0},
            "model_version": "m",
        }

    monkeypatch.setattr(scoring, "_load_external_scorer", lambda: external)
    result = scoring.score_session(
        "trace",
        2,
        "left",
        1200,
        {"x": [0.1], "y": [0.2], "targetX": [0.3], "targetY": [0.4], "t": [0.0, 1.0]},
        {"inputDevice": "touch"},
    )

    assert calls[0][1:4] == ("circle", "left", 1200)
    assert calls[0][4] == {
        "x": [100.0],
        "y": [200.0],
        "targetX": [300.0],
        "targetY": [400.0],
        "t": [0.0, 1.0],
    }
    assert result == {
        "score": 88.3,
        "impairment_class": "normal",
        "features": {"f": 1.0},
        "model_version": "m",
    }


@pytest.mark.parametrize("bad_score", [float("nan"), float("inf")])
def test_non_finite_external_score_falls_back_to_standin(
    monkeypatch: pytest.MonkeyPatch, bad_score: float
) -> None:
    def external(*args: Any) -> dict[str, Any]:
        return {"score": bad_score}

    monkeypatch.setattr(scoring, "_load_external_scorer", lambda: external)
    result = scoring.score_session(
        "trace",
        1,
        "right",
        8_000,
        {"targetX": [0.0, 1.0], "targetY": [0.0, 0.0], "x": [0.5], "y": [0.0]},
        {},
    )

    assert result["score"] == 100.0
    assert result["model_version"] == "standin-0.1"


def test_model_version_tracks_external_load_and_last_scoring_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def external(*args: Any) -> dict[str, Any]:
        raise RuntimeError("model inference failed")

    monkeypatch.setattr(scoring, "_load_external_scorer", lambda: external)
    monkeypatch.setattr(scoring, "_external_scorer", external)
    monkeypatch.setattr(scoring, "_external_model_version", "tracer-4")
    monkeypatch.setattr(scoring, "_external_last_call_failed", False)
    assert scoring.active_model_version() == "tracer-4"

    result = scoring.score_session("trace", 1, "right", 8_000, {}, {})

    assert result["model_version"] == "standin-0.1"
    assert scoring.active_model_version() == "standin-0.1"


def test_other_game_uses_standin_placeholder() -> None:
    result = scoring.score_session("motion", 8, "right", 2_000, {}, {})

    assert result == {
        "score": 50.0,
        "impairment_class": "moderate",
        "features": {},
        "model_version": "standin-0.1",
    }
