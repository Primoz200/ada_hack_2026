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
