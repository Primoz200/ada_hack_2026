# conformance tests of backend:demo-history

from __future__ import annotations

import httpx


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


# conformance scenario history-is-replayed of backend:demo-history
def test_history_is_replayed(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients/p3/timeline")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    timeline = response.json()
    sessions = timeline.get("sessions", [])
    trace_levels = {
        session.get("level")
        for session in sessions
        if session.get("gameType") == "trace"
    }
    assert {1, 2, 3}.issubset(trace_levels), (
        f"Expected trace history at levels 1, 2, 3, got {trace_levels!r}"
    )
    today = "2026-11-21"
    trace_days = [
        session.get("day") for session in sessions if session.get("gameType") == "trace"
    ]
    assert trace_days and all(day < today for day in trace_days), (
        f"Expected trace sessions only before {today}, got {trace_days!r}"
    )
    checkins = timeline.get("checkins", [])
    checkin_days = [checkin.get("day") for checkin in checkins]
    assert checkin_days and all(day < today for day in checkin_days), (
        f"Expected check-ins only before {today}, got {checkin_days!r}"
    )


# conformance scenario clinician-closed-alert of backend:demo-history
def test_clinician_closed_alert(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/alerts", params={"status": "closed"})
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    alerts = response.json()
    matching = [
        alert
        for alert in alerts
        if alert.get("patientId") == "p5"
        and alert.get("closedBy") == "dr. Ana Novak"
        and alert.get("outcome") == "called_reassured"
    ]
    assert matching, (
        f"Expected p5 alert closed by dr. Ana Novak with called_reassured, got {alerts!r}"
    )


# conformance scenario open-alerts-need-attention of backend:demo-history
def test_open_alerts_need_attention(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    counters = response.json().get("counters", {})
    assert counters.get("needsAttention", 0) >= 1, (
        f"Expected at least one patient needing attention, got {counters!r}"
    )


# conformance scenario camera-history-is-replayed of backend:demo-history
def test_camera_history_is_replayed(api: httpx.Client) -> None:
    reset_demo(api)
    p3_response = api.get("/api/patients/p3/timeline")
    assert p3_response.status_code == 200, (
        f"Expected p3 timeline HTTP 200, got {p3_response.status_code}: {p3_response.text}"
    )
    p3_timeline = p3_response.json()
    camera_sessions = [
        session
        for session in p3_timeline.get("sessions", [])
        if session.get("gameType") == "camera"
    ]
    by_level = {session.get("level"): session for session in camera_sessions}
    assert {1, 2, 3}.issubset(by_level), (
        f"Expected camera history at levels 1, 2, 3, got {camera_sessions!r}"
    )
    for level in (1, 2, 3):
        session = by_level[level]
        assert session.get("modelVersion") == "camera-seed", (
            f"Expected camera-seed model for level {level}, got {session!r}"
        )
        assert session.get("qualityOk") is True, (
            f"Expected level {level} camera capture quality true, got {session!r}"
        )
        raw_response = api.get(f"/api/sessions/{session['id']}/raw")
        assert raw_response.status_code == 200, (
            f"Expected raw session HTTP 200 for {session!r}, got "
            f"{raw_response.status_code}: {raw_response.text}"
        )
        raw_session = raw_response.json()
        assert raw_session.get("series") == {}, (
            f"Expected empty camera series for level {level}, got {raw_session!r}"
        )
    trends = p3_timeline.get("trends", [])
    assert any(trend.get("metric") == "camera:all" for trend in trends), (
        f"Expected camera:all trend snapshot, got {trends!r}"
    )

    p8_response = api.get("/api/patients/p8/timeline")
    assert p8_response.status_code == 200, (
        f"Expected p8 timeline HTTP 200, got {p8_response.status_code}: {p8_response.text}"
    )
    p8_camera_sessions = [
        session
        for session in p8_response.json().get("sessions", [])
        if session.get("gameType") == "camera"
    ]
    assert not p8_camera_sessions, (
        f"Expected p8 to have no camera sessions, got {p8_camera_sessions!r}"
    )


# conformance scenario camera-false-alarm of backend:demo-history
def test_camera_false_alarm(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/alerts", params={"status": "closed"})
    assert response.status_code == 200, (
        f"Expected closed alerts HTTP 200, got {response.status_code}: {response.text}"
    )
    alerts = response.json()
    matches = [
        alert
        for alert in alerts
        if alert.get("patientId") == "p2" and alert.get("outcome") == "false_alarm"
    ]
    assert matches, f"Expected closed p2 false_alarm alert, got {alerts!r}"
    assert any(
        alert.get("evidence", {}).get("triggers")
        and all(
            trigger.get("game") == "camera" for trigger in alert["evidence"]["triggers"]
        )
        for alert in matches
    ), f"Expected p2 false_alarm with camera-only triggers, got {matches!r}"


# conformance scenario camera-sparkline of backend:demo-history
def test_camera_sparkline(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients")
    assert response.status_code == 200, (
        f"Expected patient list HTTP 200, got {response.status_code}: {response.text}"
    )
    patients = {
        patient.get("id"): patient for patient in response.json().get("patients", [])
    }
    assert patients.get("p3") is not None and patients["p3"].get("cameraSparkline"), (
        f"Expected p3 to have a non-empty cameraSparkline, got {patients.get('p3')!r}"
    )
    assert (
        patients.get("p8") is not None and patients["p8"].get("cameraSparkline") == []
    ), f"Expected p8 to have an empty cameraSparkline, got {patients.get('p8')!r}"
