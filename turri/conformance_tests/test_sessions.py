# conformance tests of backend:sessions

from __future__ import annotations

import httpx


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


def session_payload(
    *, completed: bool, abort_reason: str | None = None, level: int = 1
) -> dict[str, object]:
    return {
        "patientId": "p9",
        "gameType": "trace",
        "level": level,
        "hand": "right",
        "startedAt": "2026-11-21T10:00:00Z",
        "durationMs": 10000,
        "completed": completed,
        "abortReason": abort_reason,
        "series": {
            "targetX": [0.1, 0.9],
            "targetY": [0.5, 0.5],
            "x": [0.1, 0.9],
            "y": [0.5, 0.5],
            "t": [0.0, 10000.0],
        },
        "clientMeta": {
            "inputDevice": "touch",
            "canvasW": 360,
            "canvasH": 360,
            "devicePixelRatio": 3,
            "userAgent": "conformance test",
        },
    }


# conformance scenario completed-trace-is-scored of backend:sessions
def test_completed_trace_is_scored(api: httpx.Client) -> None:
    reset_demo(api)
    payload = session_payload(completed=True)
    response = api.post("/api/sessions", json=payload)
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    result = response.json()
    session_id = result.get("sessionId")
    assert isinstance(session_id, int), (
        f"Expected integer sessionId, got {session_id!r}"
    )
    assert result.get("scored") is True, (
        f"Expected completed session scored true, got {result!r}"
    )

    raw_response = api.get(f"/api/sessions/{session_id}/raw")
    assert raw_response.status_code == 200, (
        f"Expected raw-session HTTP 200, got {raw_response.status_code}: {raw_response.text}"
    )
    raw = raw_response.json()
    assert raw.get("level") == 1, f"Expected raw level 1, got {raw.get('level')!r}"
    assert isinstance(raw.get("score"), (int, float)), (
        f"Expected numeric score, got {raw.get('score')!r}"
    )
    assert raw.get("series") == payload["series"], (
        f"Expected raw series {payload['series']!r}, got {raw.get('series')!r}"
    )


# conformance scenario aborted-is-not-scored of backend:sessions
def test_aborted_session_is_not_scored(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.post(
        "/api/sessions",
        json=session_payload(completed=False, abort_reason="cannot_today"),
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    result = response.json()
    session_id = result.get("sessionId")
    assert isinstance(session_id, int), (
        f"Expected integer sessionId, got {session_id!r}"
    )
    assert result.get("scored") is False, (
        f"Expected aborted session scored false, got {result!r}"
    )
    raw_response = api.get(f"/api/sessions/{session_id}/raw")
    assert raw_response.status_code == 200, (
        f"Expected raw-session HTTP 200, got {raw_response.status_code}: {raw_response.text}"
    )
    raw = raw_response.json()
    assert raw.get("score") is None, (
        f"Expected aborted session score null, got {raw.get('score')!r}"
    )


# acceptance scenario unknown-trace-level of backend:sessions
def test_unknown_trace_level(api: httpx.Client) -> None:
    response = api.post("/api/sessions", json=session_payload(completed=True, level=4))
    assert response.status_code == 422, (
        f"Expected HTTP 422 for unknown trace level, got {response.status_code}"
    )


# acceptance scenario unknown-session-raw of backend:sessions
def test_unknown_session_raw(api: httpx.Client) -> None:
    response = api.get("/api/sessions/999999/raw")
    assert response.status_code == 404, (
        f"Expected HTTP 404 for unknown session, got {response.status_code}"
    )
