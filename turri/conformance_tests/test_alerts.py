# conformance tests of backend:alert-api

from __future__ import annotations

import httpx


# conformance scenario list-alerts of backend:alert-api
def test_list_alerts(api: httpx.Client) -> None:
    response = api.get("/api/alerts", params={"status": "all"})
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    alerts = response.json()
    assert isinstance(alerts, list), f"Expected alert list, got {alerts!r}"
    alert_ids = [alert.get("id") for alert in alerts]
    assert alert_ids == sorted(alert_ids, reverse=True), (
        f"Expected alerts ordered by descending id, got {alert_ids!r}"
    )
    for alert in alerts:
        assert isinstance(alert.get("patientName"), str), (
            f"Expected patientName string, got {alert!r}"
        )
        assert alert.get("severity") in {"red", "yellow", "grey"}, (
            f"Expected recognized alert severity, got {alert!r}"
        )
        assert alert.get("status") in {"new", "acknowledged", "closed"}, (
            f"Expected recognized alert status, got {alert!r}"
        )


# acceptance scenario unknown-alert of backend:alert-api
def test_unknown_alert(api: httpx.Client) -> None:
    response = api.post("/api/alerts/999999/ack", json={"clinicianId": "c1"})
    assert response.status_code == 404, (
        f"Expected HTTP 404 for unknown alert, got {response.status_code}"
    )
