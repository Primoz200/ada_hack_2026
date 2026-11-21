"""POST /api/admin/simulate: next N days continue every story; the selected patient declines."""
from datetime import timedelta

from sqlmodel import Session, select

from app import db as dbmod
from app import seed
from app.models import Alert, Checkin, GameSession

from .conftest import TODAY


def _seed(client):
    assert client.post("/api/admin/reset").json()["ok"] is True


def _by_id(client):
    return {p["id"]: p for p in client.get("/api/patients").json()["patients"]}


def test_simulate_demo_opens_yellow_alert(client):
    _seed(client)
    before = client.get("/api/patients/demo/timeline").json()
    res = client.post("/api/admin/simulate", json={"patientId": "demo", "days": 7})
    assert res.status_code == 200
    body = res.json()
    assert body["today"] == (TODAY + timedelta(days=7)).isoformat()
    assert body["daysAdded"] == 7 and body["sessionsAdded"] == 21 and body["checkinsAdded"] == 7
    assert client.get("/api/meta").json()["today"] == body["today"]

    after = client.get("/api/patients/demo/timeline").json()
    assert len(after["sessions"]) == len(before["sessions"]) + 21
    assert len(after["checkins"]) == len(before["checkins"]) + 7
    new_days = {s["day"] for s in after["sessions"]} - {s["day"] for s in before["sessions"]}
    assert new_days == {(TODAY + timedelta(days=i)).isoformat() for i in range(1, 8)}

    detail = client.get("/api/patients/demo").json()
    assert detail["status"] == "yellow"
    assert detail["openAlert"]["rule"] == "trend_drop" and detail["openAlert"]["severity"] == "yellow"

    ps = _by_id(client)
    assert _alerts(client, "p8") == []
    for pid in ("p1", "p2", "p5"):
        assert ps[pid]["status"] == "stable", pid
    assert ps["p7"]["status"] == "no_data"


def _alerts(client, pid):
    return client.get(f"/api/patients/{pid}/timeline").json()["alerts"]


def test_simulate_in_two_steps_and_reset_restores(client):
    _seed(client)
    original = _snapshot_counts()
    client.post("/api/admin/simulate", json={"patientId": "demo", "days": 3})
    r = client.post("/api/admin/simulate", json={"patientId": "demo", "days": 4})
    assert r.json()["today"] == (TODAY + timedelta(days=7)).isoformat()
    assert _snapshot_counts() != original
    client.post("/api/admin/reset")
    assert client.get("/api/meta").json()["today"] == TODAY.isoformat()
    assert _snapshot_counts() == original
    assert client.get("/api/patients/demo").json()["openAlert"] is None


def _snapshot_counts():
    with Session(dbmod.engine) as db:
        return (len(db.exec(select(GameSession)).all()), len(db.exec(select(Checkin)).all()),
                len(db.exec(select(Alert)).all()))


def test_unknown_patient_404(client):
    res = client.post("/api/admin/simulate", json={"patientId": "nope", "days": 3})
    assert res.status_code == 404


def test_simulate_does_not_decline_patient_with_open_alert(client):
    _seed(client)
    client.post("/api/admin/simulate", json={"patientId": "p4", "days": 3})
    from app.seed import simulate
    assert "p4" not in simulate.declining()
    assert "p3" not in simulate.declining()
    assert client.get("/api/patients/p4").json()["status"] == "red"
