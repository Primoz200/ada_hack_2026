"""Read path tests. Rows are created directly; nothing here depends on the write path."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import db as dbmod
from app.main import app
from app.models import Alert, Checkin, GameSession, Patient, TrendSnapshot
from app.services import clock


@pytest.fixture
def api(db):
    # one placeholder patient so the app lifespan does not seed the dev dataset
    with Session(dbmod.engine) as s:
        t = clock.today()
        s.add(Patient(id="base", name="Base", birth_year=1950, pathway_code="stroke", side="right",
                      discharge_date=t - timedelta(days=1), sort_order=50))
        s.commit()
    with TestClient(app) as c:
        yield c


def _s():
    return Session(dbmod.engine)


def mk_patient(pid, sort=10, discharged=20, demo=False, pathway="stroke", visit=10):
    t = clock.today()
    with _s() as s:
        s.add(Patient(id=pid, name=f"Pac {pid}", birth_year=1950, pathway_code=pathway, side="right",
                      discharge_date=t - timedelta(days=discharged), next_visit_date=t + timedelta(days=visit),
                      is_demo=demo, sort_order=sort))
        s.commit()


def mk_checkin(pid, back, wellbeing=7, pain=2):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(Checkin(patient_id=pid, day=d, created_at=clock.at(d, 8),
                      answers={"wellbeing": wellbeing, "pain": pain}))
        s.commit()


def mk_session(pid, back, level=1, completed=True, counts=True, game="trace"):  # noqa: D103
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(GameSession(patient_id=pid, game_type=game, level=level, hand="right",
                          started_at=clock.at(d, 9), day=d, duration_ms=9000, completed=completed,
                          input_device="camera" if game == "camera" else "touch",
                          score=70.0 if completed else None, counts_for_trend=counts,
                          quality_ok=(completed and counts) if game == "camera" else None))
        s.commit()


def mk_snap(pid, back, delta, direction="stable", metric="trace:all"):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        s.add(TrendSnapshot(patient_id=pid, metric=metric, day=d, n_sessions=5, baseline=70,
                            ewma=70 + (delta or 0), delta=delta, direction=direction))
        s.commit()


def mk_alert(pid, severity, back=0, status="new", diverging=False, reason="Razlog.", ack=None):
    d = clock.today() - timedelta(days=back)
    with _s() as s:
        a = Alert(patient_id=pid, source="game", rule="r", severity=severity, status=status, reason=reason,
                  diverging=diverging, created_at=clock.at(d, 10), updated_at=clock.at(d, 10), opened_day=d,
                  acknowledged_at=ack)
        s.add(a)
        s.commit()
        return a.id


def row(api, pid):
    return next(p for p in api.get("/api/patients").json()["patients"] if p["id"] == pid)


def test_contract_shapes_and_404(api):
    assert api.get("/api/patients").status_code == 200
    for suffix in ("", "/timeline", "/home", "/selfcheck/summary", "/progress"):
        assert api.get(f"/api/patients/base{suffix}").status_code == 200
        assert api.get(f"/api/patients/nope{suffix}").status_code == 404
    assert '"series"' not in api.get("/api/patients").text
    assert '"series"' not in api.get("/api/patients/base/timeline").text


def test_pathways(api):
    r = api.get("/api/pathways").json()
    assert {p["code"] for p in r} >= {"stroke", "ctr"}
    assert r[0]["games"][0]["levels"] == [1, 2, 3]
    assert [q["id"] for q in r[0]["questions"]] == ["wellbeing", "pain"]


def test_status_red_yellow_grey(api):
    for pid in ("r", "y", "g"):
        mk_patient(pid)
        mk_checkin(pid, 0)
    mk_alert("r", "red", reason="Rdeč razlog.", diverging=True)
    mk_alert("y", "yellow")
    mk_alert("g", "grey")
    r = row(api, "r")
    assert (r["status"], r["reason"], r["diverging"]) == ("red", "Rdeč razlog.", True)
    assert row(api, "y")["status"] == "yellow"
    assert row(api, "g")["status"] == "no_data"
    assert r["openAlertId"]
    detail = api.get("/api/patients/r").json()
    assert detail["status"] == "red" and detail["openAlert"]["severity"] == "red"


def test_closed_alert_ignored(api):
    mk_patient("c")
    mk_checkin("c", 0)
    mk_alert("c", "red", status="closed")
    r = row(api, "c")
    assert r["status"] == "insufficient_data" and r["openAlertId"] is None


def test_no_data_and_insufficient_and_stable(api):
    mk_patient("old")
    mk_checkin("old", 5)
    r = row(api, "old")
    assert r["status"] == "no_data" and "5 dni" in r["reason"]
    mk_patient("fresh_dc", discharged=6)
    assert row(api, "fresh_dc")["status"] == "no_data"
    mk_patient("newbie", discharged=2)
    assert row(api, "newbie")["status"] == "insufficient_data"
    mk_patient("few")
    mk_checkin("few", 1)
    for b in (3, 2, 1):
        mk_session("few", b)
    r = row(api, "few")
    assert r["status"] == "insufficient_data" and "3 od 4" in r["reason"]
    mk_patient("ok")
    mk_checkin("ok", 1)
    mk_snap("ok", 1, 1.0)
    r = row(api, "ok")
    assert r["status"] == "stable" and "blizu izhodišča" in r["reason"]
    mk_patient("up")
    mk_checkin("up", 1)
    mk_snap("up", 1, 9.0, "improving")
    assert row(api, "up")["reason"] == "Rezultati so nad izhodiščem."
    assert api.get("/api/patients/up").json()["summary"]["combinedDirection"] == "improving"


def test_ordering_and_counters(api):
    for pid, sort in (("a_stable", 1), ("b_yellow", 2), ("c_red", 3), ("d_nodata", 4), ("e_insuf", 5),
                      ("f_red_old", 6)):
        mk_patient(pid, sort=sort, demo=(pid == "e_insuf"))
        if pid != "d_nodata":
            mk_checkin(pid, 0)
    mk_snap("a_stable", 0, 0.5)
    mk_alert("b_yellow", "yellow")
    mk_alert("c_red", "red", back=0)
    mk_alert("f_red_old", "red", back=3)
    # c_red was created later than f_red_old, so it has the higher alert id -> first
    body = api.get("/api/patients").json()
    ids = [p["id"] for p in body["patients"] if p["id"][1] == "_"]
    assert ids == ["c_red", "f_red_old", "b_yellow", "d_nodata", "e_insuf", "a_stable"] or \
        ids == ["f_red_old", "c_red", "b_yellow", "d_nodata", "e_insuf", "a_stable"]
    assert ids[:2] and set(ids[:2]) == {"c_red", "f_red_old"}
    c = body["counters"]
    assert c["total"] == len(body["patients"])
    assert c["needsAttention"] == 3 and c["noData"] == 1 and c["stable"] == 3  # incl. "base"
    assert c["needsAttention"] + c["noData"] + c["stable"] == c["total"]


def test_sparklines(api):
    mk_patient("sp", discharged=60)
    for b in range(30, 0, -1):
        mk_snap("sp", b, float(b))
    mk_snap("sp", 2, 99.0, metric="trace:1")  # per-level rows are not in the sparkline
    mk_snap("sp", 0, None)  # no delta yet: skipped
    for b in (0, 1, 3, 6, 7, 9):
        mk_checkin("sp", b, wellbeing=10 - b if b < 9 else 1)
    r = row(api, "sp")
    # the last 21 days that have a combined trend
    assert [p["value"] for p in r["gameSparkline"]] == [float(b) for b in range(21, 0, -1)]
    assert [p["day"] for p in r["gameSparkline"]] == sorted(p["day"] for p in r["gameSparkline"])
    assert [p["value"] for p in r["wellbeingSparkline"]] == [1.0, 3.0, 4.0, 7.0, 9.0, 10.0]
    assert r["cameraSparkline"] == []  # no camera snapshots
    for b in range(25, 0, -1):
        mk_snap("sp", b, -float(b), metric="camera:all")
    mk_snap("sp", 1, 50.0, metric="camera:1")
    r = row(api, "sp")
    assert [p["value"] for p in r["cameraSparkline"]] == [-float(b) for b in range(21, 0, -1)]
    assert [p["value"] for p in r["gameSparkline"]] == [float(b) for b in range(21, 0, -1)]  # unchanged


def test_divergence_surfaces(api):
    mk_patient("dv")
    mk_checkin("dv", 0, wellbeing=8, pain=2)
    mk_checkin("dv", 1, wellbeing=8, pain=2)
    mk_checkin("dv", 9, wellbeing=6, pain=3)
    mk_snap("dv", 0, -15.0, "declining")
    assert row(api, "dv")["diverging"] is True
    assert api.get("/api/patients/dv").json()["diverging"] is True
    mk_patient("dv2")
    mk_alert("dv2", "yellow", diverging=True)
    assert row(api, "dv2")["diverging"] is True


def test_timeline_ordering_no_series(api):
    mk_patient("tl")
    mk_session("tl", 1)
    mk_session("tl", 3)
    mk_checkin("tl", 2)
    mk_checkin("tl", 4)
    mk_snap("tl", 1, 1.0)
    mk_snap("tl", 3, 2.0)
    t = api.get("/api/patients/tl/timeline").json()
    assert "messages" not in t
    for key in ("sessions", "checkins", "trends"):
        assert len(t[key]) == 2
        days = [x["day"] for x in t[key]]
        assert days == sorted(days)
    assert "series" not in str(t)
    assert all(s["qualityOk"] is None for s in t["sessions"])  # tracing: no capture quality
    mk_session("tl", 0, game="camera", counts=False)
    s = api.get("/api/patients/tl/timeline").json()["sessions"][-1]
    assert (s["gameType"], s["qualityOk"], s["countsForTrend"]) == ("camera", False, False)


def test_home_steps_and_done_today(api):
    mk_patient("hm")
    h = api.get("/api/patients/hm/home").json()
    assert [(s["id"], s["kind"], s["title"]) for s in h["steps"]] == [
        ("ratings", "ratings", "Počutje in bolečina"), ("trace:1", "game", "Ravna črta"),
        ("trace:2", "game", "Krog"), ("trace:3", "game", "Labirint"),
        ("camera:1", "game", "Dlan"), ("camera:2", "game", "Roke v stran"), ("camera:3", "game", "Dvig rok")]
    assert h["steps"][1]["gameType"] == "trace" and h["steps"][1]["level"] == 1
    assert [(s["gameType"], s["level"]) for s in h["steps"][4:]] == [("camera", 1), ("camera", 2), ("camera", 3)]
    # the hand exercise first and not skippable; the two arm exercises may be skipped
    assert [s["skippable"] for s in h["steps"]] == [False, False, False, False, False, True, True]
    assert [s["durationS"] for s in h["steps"]] == [None, None, None, None, 21.0, 42.0, 42.0]
    assert not any(s["done"] for s in h["steps"]) and h["selfcheckDoneToday"] is False
    assert h["lastSelfcheckDay"] is None and h["hand"] == "right"
    mk_checkin("hm", 2)
    mk_checkin("hm", 0)
    mk_session("hm", 0, level=1)
    mk_session("hm", 0, level=2, completed=False, counts=False)  # aborted: not done
    mk_session("hm", 1, level=3)  # yesterday: not done today
    mk_session("hm", 0, level=1, game="camera", completed=False, counts=False)  # aborted camera: not done
    h = api.get("/api/patients/hm/home").json()
    assert [s["done"] for s in h["steps"]] == [True, True, False, False, False, False, False]
    assert h["selfcheckDoneToday"] is False and h["lastSelfcheckDay"] == clock.today().isoformat()
    mk_session("hm", 0, level=2)
    mk_session("hm", 0, level=3)
    # ratings + every tracing level: done, although no camera exercise was done
    h = api.get("/api/patients/hm/home").json()
    assert h["selfcheckDoneToday"] is True
    assert [s["done"] for s in h["steps"]] == [True, True, True, True, False, False, False]
    # a completed camera session counts even when its capture quality was poor (it was done)
    mk_session("hm", 0, level=1, game="camera", counts=False)
    mk_session("hm", 0, level=3, game="camera")
    h = api.get("/api/patients/hm/home").json()
    assert [s["done"] for s in h["steps"][4:]] == [True, False, True] and h["selfcheckDoneToday"] is True


def test_camera_steps_alone_never_complete_the_selfcheck(api):
    mk_patient("cm")
    mk_checkin("cm", 0)
    for lv in (1, 2, 3):
        mk_session("cm", 0, level=lv, game="camera")
    h = api.get("/api/patients/cm/home").json()
    assert [s["done"] for s in h["steps"]] == [True, False, False, False, True, True, True]
    assert h["selfcheckDoneToday"] is False


def test_summary_without_data_and_with_points(api):
    mk_patient("sm")
    s = api.get("/api/patients/sm/selfcheck/summary").json()
    assert (s["tone"], s["trend"], s["levelsDone"], s["levelsTotal"], s["games"]) == ("first", "unknown", 0, 6, [])
    assert s["title"] and s["text"] and s["day"] == clock.today().isoformat()
    for b, v in ((20, -9.0), (13, -6.0), (5, 0.0), (3, 6.0), (1, -1.0)):
        mk_snap("sm", b, v)
    s = api.get("/api/patients/sm/selfcheck/summary").json()
    # today has nothing yet: describes the latest day; points are the last 14 days only
    [g] = s["games"]  # no camera data: tracing only
    assert (g["gameType"], g["title"]) == ("trace", "Sledenje")
    assert [(p["value"], p["label"]) for p in g["points"]] == [
        (-6.0, "lower"), (0.0, "usual"), (6.0, "better"), (-1.0, "usual")]
    assert g["trend"] == "stable" and g["personalBestDay"] == (clock.today() - timedelta(days=3)).isoformat()
    assert s["tone"] == "similar" and s["trend"] == "stable"  # -1 vs the mean of the previous days
    mk_session("sm", 0, level=1)
    mk_session("sm", 0, level=2, game="camera")
    s = api.get("/api/patients/sm/selfcheck/summary").json()
    assert (s["levelsDone"], s["levelsTotal"]) == (2, 6)  # game steps of all games


def test_summary_and_progress_with_camera_data(api):
    mk_patient("cg")
    for b, v in ((6, 0.0), (4, 1.0), (2, -1.0), (1, 0.5)):
        mk_snap("cg", b, v)
    for b, v in ((30, 2.0), (6, -2.0), (4, -4.0), (2, -6.0), (1, -9.0)):
        mk_snap("cg", b, v, metric="camera:all")
    mk_snap("cg", 1, -30.0, metric="camera:1")  # per-level rows are not shown to the patient
    s = api.get("/api/patients/cg/selfcheck/summary").json()
    assert [g["gameType"] for g in s["games"]] == ["trace", "camera"]  # tracing first
    trace, camera = s["games"]
    assert camera["title"] == "Vaje s kamero" and trace["title"] == "Sledenje"
    assert [p["value"] for p in trace["points"]] == [0.0, 1.0, -1.0, 0.5]
    assert [p["value"] for p in camera["points"]] == [-2.0, -4.0, -6.0, -9.0]  # last 14 days
    assert camera["points"][-1]["label"] == "lower"
    assert trace["trend"] == "stable" and camera["trend"] == "declining"
    assert camera["personalBestDay"] == (clock.today() - timedelta(days=30)).isoformat()  # whole history
    # any game declining: the overall trend is declining (said calmly)
    assert s["trend"] == "declining"
    p = api.get("/api/patients/cg/progress").json()
    assert [g["gameType"] for g in p["games"]] == ["trace", "camera"]
    assert [x["value"] for x in p["games"][1]["points"]] == [2.0, -2.0, -4.0, -6.0, -9.0]  # whole history
    assert p["trend"] == "declining" and p["games"][0]["trend"] == "stable"


def test_progress(api):
    mk_patient("pg")
    for b, v in ((10, -2.0), (8, 7.5), (2, 3.0)):
        mk_snap("pg", b, v)
    for b in (0, 1, 3, 9):
        mk_checkin("pg", b, wellbeing=6, pain=4)
    mk_session("pg", 5)
    p = api.get("/api/patients/pg/progress").json()
    [g] = p["games"]  # no camera data
    assert g["gameType"] == "trace" and [x["value"] for x in g["points"]] == [-2.0, 7.5, 3.0]
    assert g["personalBestDay"] == (clock.today() - timedelta(days=8)).isoformat()
    assert [(r["wellbeing"], r["pain"]) for r in p["ratings"]] == [(6.0, 4.0)] * 4
    assert (p["weekDone"], p["weekGoal"]) == (4, 5)  # days 0, 1, 3 (check-ins) + 5 (session)
    assert p["clinicianReviewedAt"] is None
    assert p["tone"] in ("better", "similar", "lower") and p["title"] and p["text"]
    mk_alert("pg", "yellow", ack=clock.at(clock.today(), 11))
    assert api.get("/api/patients/pg/progress").json()["clinicianReviewedAt"].startswith(
        clock.today().isoformat())
