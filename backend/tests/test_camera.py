"""Camera exercises: real recordings through the API, a trend of their own, alerts per game."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.main import app
from app.models import GameSession, SessionRaw, TrendSnapshot
from app.services import alerts, camera_model, clock, divergence, feedback, scoring
from tests.helpers import add_patient, all_alerts, checkin, d, open_alerts, play, play_camera

RECORDINGS = Path(__file__).resolve().parents[1] / "models" / "data" / "camera" / "recordings"


def rec(name: str) -> dict:
    [path] = RECORDINGS.glob(f"*{name}*.json")
    return json.loads(path.read_text())


def body(r: dict, pid: str = "p") -> dict:
    """The recording exactly as the frontend sends it (the recorder's GameResult) + patientId."""
    return {**{k: r[k] for k in ("gameType", "level", "hand", "startedAt", "durationMs", "completed",
                                 "series", "clientMeta")}, "patientId": pid}


@pytest.fixture
def api(db):
    add_patient(db)  # a patient exists, so the app lifespan does not seed the demo data
    with TestClient(app) as c:
        yield c


def stored(sid: int, db) -> GameSession:
    db.expire_all()
    return db.get(GameSession, sid)


# ------------------------------------------------------------------ real recordings

@pytest.mark.parametrize("name", [
    "202548-519_hand_open_close_right_test",  # normal (94.8)
    "202812-303_hand_open_close_right_test",  # mild (67.5)
    "202620-848_hand_open_close_right_test",  # moderate (57.7)
    "203537-926_hand_open_close_right_test",  # moderate (40.3)
    "202735-843_hand_open_close_right_test",  # severe (0.0)
    "203004-748_shoulder_abduction_right_test",  # arms to the side (56.2)
    "203103-492_arm_raise_right_test",  # arms up (42.8)
    "195021-564_hand_open_close_left_reference",  # left hand
])
def test_recording_through_the_api_scores_like_the_recorder(api, db, name):
    r = rec(name)
    res = api.post("/api/sessions", json=body(r))
    assert res.status_code == 200, res.text
    assert res.json()["scored"] is True
    row = stored(res.json()["sessionId"], db)
    assert row.score == pytest.approx(r["result"]["score"], abs=0.1)
    assert (row.game_type, row.level, row.quality_ok, row.counts_for_trend) == ("camera", r["level"], True, True)
    assert row.impairment_class == r["result"]["impairment_class"]
    assert row.model_version == r["result"]["model_version"] and row.input_device == "camera"
    # the scorer's features (and the parts of the score) are stored for the clinician
    expected = {k for k, v in r["result"]["features"].items() if v is not None}
    assert expected <= set(row.features)
    assert {f"part_{k}" for k in r["result"]["breakdown"]} <= set(row.features)
    tl = api.get("/api/patients/p/timeline").json()
    s = next(x for x in tl["sessions"] if x["id"] == row.id)
    assert s["qualityOk"] is True and s["countsForTrend"] is True and s["gameType"] == "camera"
    assert any(t["metric"] == f"camera:{r['level']}" for t in tl["trends"])
    assert not any(t["metric"].startswith("trace") for t in tl["trends"])


def test_poor_quality_recording_is_stored_without_score_or_trend(api, db):
    r = rec("203631-595_shoulder_abduction_right_test")
    assert r["result"]["quality_ok"] is False and r["result"]["score"] is not None  # the scorer still scores it
    res = api.post("/api/sessions", json=body(r))
    assert res.status_code == 200 and res.json()["scored"] is False
    row = stored(res.json()["sessionId"], db)
    assert (row.score, row.impairment_class, row.quality_ok, row.counts_for_trend) == (None, None, False, False)
    assert row.features["detect_frac"] == pytest.approx(r["result"]["features"]["detect_frac"])  # features kept
    raw = api.get(f"/api/sessions/{row.id}/raw").json()
    assert raw["score"] is None and len(raw["series"]["t"]) == len(r["series"]["t"])
    assert db.exec(select(TrendSnapshot)).all() == []
    s = api.get("/api/patients/p/timeline").json()["sessions"][0]
    assert (s["qualityOk"], s["countsForTrend"], s["score"]) == (False, False, None)


def test_series_with_nulls_and_extra_client_meta_survive(api):
    r = rec("202548-519_hand_open_close_right_test")
    b = body(r)
    series = copy.deepcopy(b["series"])
    for key in series:  # three frames without a detection
        if key.startswith(("lm", "w", "hand")):
            for i in (10, 11, 12):
                series[key][i] = None
    b["series"] = series
    res = api.post("/api/sessions", json=b)
    assert res.status_code == 200, res.text
    assert res.json()["scored"] is True
    raw = api.get(f"/api/sessions/{res.json()['sessionId']}/raw").json()
    assert raw["series"]["lm0_x"][10:13] == [None, None, None]
    meta = raw["clientMeta"]
    for k in ("videoW", "videoH", "fpsMeasured", "detector", "mediapipe", "delegate", "mirroredPreview"):
        assert meta[k] == r["clientMeta"][k], k
    assert meta["inputDevice"] == "camera" and meta["canvasW"] == 1280


def test_scorer_sees_the_extra_client_meta(api, monkeypatch):
    seen = {}
    real = camera_model.score_session

    def spy(game_type, level, hand, duration_ms, series, client_meta):
        seen.update(client_meta)
        return real(game_type, level, hand, duration_ms, series, client_meta)

    monkeypatch.setattr(camera_model, "score_session", spy)
    assert api.post("/api/sessions", json=body(rec("202548-519_hand"))).status_code == 200
    assert seen["videoW"] == 1280 and seen["videoH"] == 720 and seen["fpsMeasured"] > 0


@pytest.mark.parametrize("out", [RuntimeError("boom"), {"score": None, "quality_ok": True, "features": {"fps": 20.0},
                                                         "model_version": "camera-x"}])
def test_scoring_failure_or_no_score_is_stored_not_counted(api, db, monkeypatch, out):
    def fake(*a):
        if isinstance(out, Exception):
            raise out
        return out

    monkeypatch.setattr(camera_model, "score_session", fake)
    res = api.post("/api/sessions", json=body(rec("202548-519_hand")))
    assert res.status_code == 200 and res.json()["scored"] is False
    row = stored(res.json()["sessionId"], db)
    assert row.score is None and row.counts_for_trend is False
    assert db.get(SessionRaw, row.id).series["t"]
    if isinstance(out, dict):
        assert row.features == {"fps": 20.0} and row.quality_ok is True


def test_camera_levels_validated_and_model_version_stays_tracer(api):
    b = body(rec("202548-519_hand"))
    assert api.post("/api/sessions", json={**b, "level": 4}).status_code == 422
    assert api.post("/api/sessions", json={**b, "gameType": "camera_tapping"}).status_code == 422
    before = api.get("/api/meta").json()["modelVersion"]
    assert api.post("/api/sessions", json=b).status_code == 200
    assert api.get("/api/meta").json()["modelVersion"] == before == scoring.current_model_version()
    assert not before.startswith("camera")


def test_aborted_camera_session(api, db):
    b = {**body(rec("202548-519_hand")), "completed": False, "abortReason": "no_camera", "series": {}}
    res = api.post("/api/sessions", json=b)
    assert res.status_code == 200 and res.json()["scored"] is False
    row = stored(res.json()["sessionId"], db)
    assert (row.score, row.quality_ok, row.counts_for_trend) == (None, None, False)


# ------------------------------------------------------------------ trend separation

def _snaps(db, prefix):
    return sorted((s.metric, s.day, s.n_sessions, s.baseline, s.ewma, s.delta)
                  for s in db.exec(select(TrendSnapshot)).all() if s.metric.startswith(prefix))


def test_camera_and_trace_trends_never_mix(db):
    add_patient(db)
    for i in range(6):
        for lv in (1, 2, 3):
            play(db, "p", d(i), 70 + lv, level=lv)
    trace_before = _snaps(db, "trace:")
    for i in range(6):
        for lv in (1, 2, 3):
            play_camera(db, "p", d(i), 95 - 20 * (i == 5), level=lv)
    assert _snaps(db, "trace:") == trace_before  # camera sessions never touch the tracing trend
    camera_before = _snaps(db, "camera:")
    assert {m for m, *_ in camera_before} == {"camera:1", "camera:2", "camera:3", "camera:all"}
    for lv in (1, 2, 3):
        play(db, "p", d(6), 20, level=lv)
    assert _snaps(db, "camera:") == camera_before  # and tracing sessions never touch the camera trend
    l1 = {s.day: s for s in db.exec(select(TrendSnapshot).where(TrendSnapshot.metric == "camera:1")).all()}
    assert l1[d(3)].baseline == 95.0 and l1[d(5)].delta == pytest.approx(0.3 * -20)
    a = {s.day: s for s in db.exec(select(TrendSnapshot).where(TrendSnapshot.metric == "camera:all")).all()}
    assert a[d(5)].delta == pytest.approx(0.3 * -20) and a[d(5)].n_sessions == 6


def test_camera_combined_carries_skipped_arm_levels(db):
    add_patient(db)
    for i in range(5):
        for lv in (1, 2, 3):
            play_camera(db, "p", d(i), 90, level=lv)
    play_camera(db, "p", d(5), 70, level=1)  # arm exercises skipped that day
    a = db.exec(select(TrendSnapshot).where(TrendSnapshot.metric == "camera:all",
                                            TrendSnapshot.day == d(5))).one()
    assert a.delta == pytest.approx(0.3 * -20 / 3)


def test_poor_quality_preset_is_not_in_the_trend(db):
    add_patient(db)
    row = play_camera(db, "p", d(0), 90, quality_ok=False)
    assert (row.score, row.counts_for_trend, row.quality_ok) == (None, False, False)
    assert db.exec(select(TrendSnapshot)).all() == []


# ------------------------------------------------------------------ alerts per game

def camera_drifting(db, start=0, base=90, drift=82):
    """Camera hand exercise: practice + baseline (4 days), then six days below baseline
    (about -7, not yet -10). Returns the next day index."""
    for i in range(start, start + 4):
        play_camera(db, "p", d(i), base)
    for i in range(start + 4, start + 10):
        play_camera(db, "p", d(i), drift)
    return start + 10


def trace_stable(db, start, end, score=70):
    for i in range(start, end):
        play(db, "p", d(i), score)


def test_camera_only_drift_and_bad_day_opens_yellow_for_camera(db):
    add_patient(db)
    trace_stable(db, 0, 11)
    nxt = camera_drifting(db)
    assert all_alerts(db) == []  # drifting alone opens nothing
    play_camera(db, "p", d(nxt), 60)
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("yellow", "trend_drop", "game")
    assert a.reason == "Rezultati vaj s kamero so že več dni pod pacientovim izhodiščem."
    assert [t["game"] for t in a.evidence["triggers"]] == ["camera"]
    assert set(a.evidence["games"]) == {"camera"} and a.evidence["delta"] == a.evidence["games"]["camera"]["delta"]
    assert a.evidence["delta"] <= -10 and len(a.evidence["previousDeltas"]) == 3
    cam_ids = {r.id for r in db.exec(select(GameSession).where(GameSession.game_type == "camera")).all()}
    assert set(a.evidence["sessionIds"]) <= cam_ids  # the camera sessions, not the tracing ones
    assert not any(ch.isdigit() for ch in a.reason)
    assert alerts.open_alert_games(db, "p") == {"camera"}


def test_trace_and_camera_drop_one_alert_with_both_games(db):
    add_patient(db)
    for i in range(4):
        play(db, "p", d(i), 70)
    for i in range(4, 10):
        play(db, "p", d(i), 62)
    camera_drifting(db)
    play(db, "p", d(10), 45)  # tracing tips over first
    [a] = open_alerts(db)
    assert a.reason == "Rezultati sledenja so že več dni pod pacientovim izhodiščem."
    assert set(a.evidence["games"]) == {"trace"}
    play_camera(db, "p", d(10), 60)  # then the camera exercise on the same day
    [a] = open_alerts(db)
    assert (a.severity, a.rule) == ("yellow", "trend_drop") and len(all_alerts(db)) == 1
    assert a.reason == "Padajo rezultati sledenja in vaj s kamero."
    games = a.evidence["games"]
    assert set(games) == {"trace", "camera"}
    assert a.evidence["delta"] == min(games["trace"]["delta"], games["camera"]["delta"])
    assert {(t["rule"], t["game"]) for t in a.evidence["triggers"]} == {("trend_drop", "trace"),
                                                                       ("trend_drop", "camera")}


def test_camera_drop_with_worse_wellbeing_is_red_both(db):
    add_patient(db)
    for i in range(4):
        checkin(db, "p", d(i), wellbeing=7, pain=2)
    for i in range(4, 11):
        checkin(db, "p", d(i), wellbeing=4, pain=2)
    trace_stable(db, 0, 11)
    nxt = camera_drifting(db)
    play_camera(db, "p", d(nxt), 60)
    [a] = open_alerts(db)
    assert (a.severity, a.rule, a.source) == ("red", "both", "game")
    assert a.reason == "Padajo rezultati meritev in počutje hkrati."
    assert set(a.evidence["games"]) == {"camera"} and a.evidence["wellbeingChange"] <= -2
    assert ("both", "camera") in {(t["rule"], t.get("game")) for t in a.evidence["triggers"]}


def test_closing_a_tracing_alert_does_not_silence_a_later_camera_drop(db):
    add_patient(db)
    for i in range(4):
        play(db, "p", d(i), 70)
        play_camera(db, "p", d(i), 90)
    for i in range(4, 10):
        play(db, "p", d(i), 62)
        play_camera(db, "p", d(i), 90 if i < 6 else 82)  # camera starts drifting on day 6
    play(db, "p", d(10), 45)
    [a] = open_alerts(db)
    assert set(a.evidence["games"]) == {"trace"}
    clock.set_today(d(10))
    alerts.acknowledge(db, a.id, "c1", True, "adjusted_exercises", "Vaje prilagojene.")
    play_camera(db, "p", d(10), 82)
    for i in (11, 12):
        clock.set_today(d(i))
        play(db, "p", d(i), 57)  # tracing stays below: same episode, no re-fire
    assert open_alerts(db) == []
    play_camera(db, "p", d(12), 55)  # two days after the close: a camera drop is a new episode
    [b] = open_alerts(db)
    assert b.id != a.id and (b.severity, b.rule) == ("yellow", "trend_drop")
    assert {t["game"] for t in b.evidence["triggers"]} == {"camera"}
    assert b.reason == "Rezultati vaj s kamero so že več dni pod pacientovim izhodiščem."
    assert set(b.evidence["games"]) == {"camera"}  # the suppressed tracing trigger is not evidence


def test_closing_a_camera_alert_suppresses_the_same_camera_episode(db):
    add_patient(db)
    nxt = camera_drifting(db)
    play_camera(db, "p", d(nxt), 60)
    [a] = open_alerts(db)
    clock.set_today(d(nxt))
    alerts.acknowledge(db, a.id, "c1", True, "false_alarm", "Kamera slabo postavljena.")
    for i in range(1, 4):
        clock.set_today(d(nxt + i))
        play_camera(db, "p", d(nxt + i), 70)
    assert open_alerts(db) == [] and len(all_alerts(db)) == 1


def test_camera_big_drop_is_red_and_named(db):
    add_patient(db)
    for i in range(7):
        play_camera(db, "p", d(i), 90)
    play_camera(db, "p", d(7), 20)  # one level only: EWMA 90 -> 69, delta -21
    [a] = open_alerts(db)
    assert (a.severity, a.rule) == ("red", "big_drop")
    assert a.reason == "Rezultati vaj s kamero so močno padli pod pacientovo izhodišče."
    assert a.evidence["games"]["camera"]["delta"] <= -20


def test_pathways_list_the_camera_game_with_optional_levels(api):
    stroke = next(p for p in api.get("/api/pathways").json() if p["code"] == "stroke")
    assert [(g["gameType"], g["levels"], g["optionalLevels"]) for g in stroke["games"]] == [
        ("trace", [1, 2, 3], []), ("camera", [1, 2, 3], [2, 3])]


def test_legacy_trigger_without_game_counts_as_tracing():
    assert alerts._trigger_key({"rule": "trend_drop"}) == ("trend_drop", "trace")
    assert alerts._trigger_key({"rule": "subjective_drop"}) == ("subjective_drop", None)
    assert alerts._trigger_key({"rule": "big_drop", "game": "camera"}) == ("big_drop", "camera")


# ------------------------------------------------------------------ divergence and feedback

def test_divergence_uses_every_measurement(db):
    add_patient(db)
    for i in range(14):
        checkin(db, "p", d(i), wellbeing=7, pain=2)
    trace_stable(db, 0, 14)
    assert divergence.assess(db, "p", d(13)) == (False, None)
    for i in range(4):
        play_camera(db, "p", d(i), 90)
    for i in range(4, 14):
        play_camera(db, "p", d(i), 60)
    diverging, sentence = divergence.assess(db, "p", d(13))
    assert diverging and sentence == "Rezultati meritev padajo, pacient pa poroča enako ali boljše počutje."


def test_feedback_follows_each_game(db):
    add_patient(db)
    for i in range(10):
        play(db, "p", d(i), 70)
        play_camera(db, "p", d(i), 90 if i < 5 else 90 - 3 * (i - 4))
    fb = feedback.feedback_for(db, "p", d(9))
    # tracing stable, camera declining: overall declining (said calmly), per game apart
    assert fb.trend == "declining"
    assert feedback.game_trends(db, "p", d(9)) == {"trace": "stable", "camera": "declining"}
    # a day with tracing only is judged on the tracing alone
    play(db, "p", d(10), 80)
    only_trace = [s.delta for s in feedback.combined_points(db, "p", d(10))]
    fb = feedback.feedback_for(db, "p", d(10))
    assert fb.tone == feedback.tone_of(only_trace[-1], only_trace[-6:-1]) and fb.day == d(10)


def test_a_hand_recording_marks_its_step_done_and_opens_nothing(api):
    res = api.post("/api/sessions", json=body(rec("194808-033_hand_open_close_right_reference")))
    assert res.json()["scored"] is True
    assert api.get("/api/patients/p").json()["openAlert"] is None
    home = api.get("/api/patients/p/home").json()
    assert [s["done"] for s in home["steps"]][4:] == [True, False, False]
    assert home["selfcheckDoneToday"] is False  # camera never completes the self-check on its own
    # a recording on a day without tracing: the patient has camera data but no baseline yet
    assert api.get("/api/patients/p/progress").json()["games"] == []
