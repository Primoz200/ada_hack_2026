def test_slice(client):
    patients = client.get("/api/patients").json()
    assert patients["counters"]["total"] >= 2
    pid = patients["patients"][0]["id"]
    assert client.get(f"/api/patients/{pid}").status_code == 200
    assert client.get(f"/api/patients/{pid}/today").json()["tasks"]
    before = len(client.get(f"/api/patients/{pid}/timeline").json()["sessions"])
    body = {
        "patientId": pid, "gameType": "trace", "level": 1, "hand": "right",
        "startedAt": "2026-11-21T10:00:00Z", "durationMs": 9000, "completed": True,
        "series": {"targetX": [0.1, 0.9], "targetY": [0.5, 0.5], "t": [0, 100, 200],
                   "x": [0.1, 0.5, 0.9], "y": [0.5, 0.51, 0.5], "strokeId": [0, 0, 0]},
        "clientMeta": {"inputDevice": "mouse", "canvasW": 400, "canvasH": 400,
                       "devicePixelRatio": 2, "userAgent": "pytest"},
    }
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 200, res.text
    sid = res.json()["sessionId"]
    timeline = client.get(f"/api/patients/{pid}/timeline").json()
    assert len(timeline["sessions"]) == before + 1
    assert "series" not in timeline["sessions"][0]
    assert client.get(f"/api/sessions/{sid}/raw").json()["series"]["x"] == [0.1, 0.5, 0.9]
    assert client.get("/api/pathways").json()[0]["warningSigns"]
    assert client.get("/api/meta").json()["outcomes"]
    assert client.post("/api/admin/reset").json()["ok"] is True
