# conformance tests of backend:camera-exercises
# conformance tests of backend:camera-scoring

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


# conformance scenario three-exercises of backend:camera-exercises
def test_three_camera_exercises(api: httpx.Client) -> None:
    response = api.get("/api/camera/exercises")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    exercises = response.json()
    assert [exercise.get("level") for exercise in exercises] == [1, 2, 3], (
        f"Expected camera exercises at levels 1, 2, 3, got {exercises!r}"
    )
    first, second, third = exercises
    assert (
        first.get("key") == "hand_open_close"
        and first.get("detector") == "hand"
        and first.get("durationS") == 21
        and first.get("nCues") == 7
        and first.get("openWindowS") == 0.5
    ), f"Expected specified level 1 exercise, got {first!r}"
    assert (
        second.get("key") == "shoulder_abduction"
        and second.get("detector") == "pose"
        and second.get("durationS") == 42
        and second.get("cuePeriodS") == 8
        and second.get("upS") == 4
    ), f"Expected specified level 2 exercise, got {second!r}"
    assert third.get("key") == "arm_raise", f"Expected arm_raise level 3, got {third!r}"
    assert all(
        isinstance(item.get("instructions"), str) and item["instructions"]
        for item in exercises
    ), f"Expected non-empty instructions for every exercise, got {exercises!r}"


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


def camera_recording(filename: str) -> dict[str, Any]:
    recordings_dir_value = os.environ.get("CAMERA_RECORDINGS_DIR")
    if recordings_dir_value is None:
        raise RuntimeError("CAMERA_RECORDINGS_DIR must point to the camera recordings")
    recording_path = Path(recordings_dir_value) / filename
    with recording_path.open(encoding="utf-8") as recording_file:
        recording: dict[str, Any] = json.load(recording_file)
    return recording


def submit_recording(
    api: httpx.Client, filename: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    recording = camera_recording(filename)
    payload = {
        "patientId": "p9",
        "gameType": "camera",
        "level": recording["level"],
        "hand": recording["hand"],
        "startedAt": "2026-11-21T10:00:00Z",
        "durationMs": recording["durationMs"],
        "completed": True,
        "abortReason": None,
        "series": recording["series"],
        "clientMeta": recording["clientMeta"],
    }
    response = api.post("/api/sessions", json=payload)
    assert response.status_code == 200, (
        f"Expected camera session HTTP 200 for {filename}, got "
        f"{response.status_code}: {response.text}"
    )
    result = response.json()
    session_id = result.get("sessionId")
    assert isinstance(session_id, int), (
        f"Expected integer sessionId for {filename}, got {result!r}"
    )
    timeline_response = api.get("/api/patients/p9/timeline")
    assert timeline_response.status_code == 200, (
        f"Expected timeline HTTP 200, got {timeline_response.status_code}: {timeline_response.text}"
    )
    sessions = timeline_response.json().get("sessions", [])
    session = next((item for item in sessions if item.get("id") == session_id), None)
    assert session is not None, (
        f"Expected session {session_id} in timeline, got {sessions!r}"
    )
    return result, session


# conformance scenario real-partial-fist of backend:camera-scoring
def test_real_partial_fist(api: httpx.Client) -> None:
    reset_demo(api)
    result, session = submit_recording(
        api, "20261121-202620-848_hand_open_close_right_test_P01.json"
    )
    assert result.get("scored") is True, f"Expected scored true, got {result!r}"
    assert session.get("score") == 57.7, f"Expected score 57.7, got {session!r}"
    assert session.get("qualityOk") is True, f"Expected qualityOk true, got {session!r}"
    assert session.get("modelVersion") == "camera-rules-0.3", (
        f"Expected camera-rules-0.3, got {session!r}"
    )
    features = session.get("features", {})
    assert "open_level" in features and "part_position" in features, (
        f"Expected open_level and part_position features, got {features!r}"
    )


# conformance scenario real-healthy-hand of backend:camera-scoring
def test_real_healthy_hand(api: httpx.Client) -> None:
    reset_demo(api)
    result, session = submit_recording(
        api, "20261121-194808-033_hand_open_close_right_reference_P01.json"
    )
    assert result.get("scored") is True, (
        f"Expected healthy hand scored true, got {result!r}"
    )
    assert session.get("score") == 100.0, f"Expected score 100.0, got {session!r}"
    assert session.get("impairmentClass") == "normal", (
        f"Expected impairmentClass normal, got {session!r}"
    )


# conformance scenario real-arms-to-the-side of backend:camera-scoring
def test_real_arms_to_the_side(api: httpx.Client) -> None:
    reset_demo(api)
    result, session = submit_recording(
        api, "20261121-203004-748_shoulder_abduction_right_test_P01.json"
    )
    assert result.get("scored") is True, (
        f"Expected arms-to-the-side scored true, got {result!r}"
    )
    assert session.get("score") == 56.2, f"Expected score 56.2, got {session!r}"


# acceptance scenario poor-capture-not-scored of backend:camera-scoring
def test_poor_capture_not_scored(api: httpx.Client) -> None:
    reset_demo(api)
    result, session = submit_recording(
        api, "20261121-203631-595_shoulder_abduction_right_test_P01.json"
    )
    assert result.get("scored") is False, (
        f"Expected poor capture scored false, got {result!r}"
    )
    assert session.get("score") is None, (
        f"Expected poor-capture score null, got {session!r}"
    )
    assert session.get("qualityOk") is False, (
        f"Expected poor-capture qualityOk false, got {session!r}"
    )
    assert session.get("countsForTrend") is False, (
        f"Expected poor-capture countsForTrend false, got {session!r}"
    )
