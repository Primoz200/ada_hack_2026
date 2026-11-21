import re

import pytest
from sqlmodel import select

from app.models import GameSession, SessionRaw
from tests.helpers import add_patient, baseline_days, checkin, d, open_alerts, play

FORBIDDEN = ("poslabšanje", "poslabšal")


def test_compared_to_usual_and_personal_best(db):
    add_patient(db)
    seen = [play(db, "p", d(i), 70)[2]["compared_to_usual"] for i in range(4)]
    assert seen == ["first"] * 4  # no baseline until the 4th session is in
    _, _, e = play(db, "p", d(4), 76)
    assert (e["compared_to_usual"], e["personal_best"]) == ("better", True)  # >= +5 vs baseline 70
    _, _, e = play(db, "p", d(5), 72)
    assert (e["compared_to_usual"], e["personal_best"]) == ("similar", False)
    _, _, e = play(db, "p", d(6), 64)
    assert e["compared_to_usual"] == "lower"
    _, _, e = play(db, "p", d(7), 90)
    assert e["personal_best"] is True


def test_levels_are_compared_separately(db):
    add_patient(db)
    for i in range(4):
        play(db, "p", d(i), 70, level=1)
    _, _, e = play(db, "p", d(4), 50, level=2)  # level 2 has no baseline yet
    assert e["compared_to_usual"] == "first" and e["offer_retry"] is False


def test_aborted_session_stored_not_scored(db):
    add_patient(db)
    row, fb, e = play(db, "p", d(0), 0, completed=False)
    assert (row.score, row.impairment_class, row.counts_for_trend) == (None, None, False)
    assert e == {"compared_to_usual": "not_scored", "offer_retry": False, "personal_best": False}
    assert fb.level == "thanks"
    assert db.get(SessionRaw, row.id) is not None


def test_day_and_created_at_overrides_and_scoring_without_preset(db):
    from app.models.schemas import SessionIn
    from app.services import ingest
    from tests.helpers import META

    add_patient(db)
    data = SessionIn(patient_id="p", game_type="trace", level=1, hand="right",
                     started_at="2026-09-01T10:00:00Z", duration_ms=9000, completed=True,
                     series={"targetX": [0.1, 0.9], "targetY": [0.5, 0.5], "t": [0, 1, 2],
                             "x": [0.1, 0.5, 0.9], "y": [0.5, 0.5, 0.5], "strokeId": [0, 0, 0]},
                     client_meta=META)
    row, fb, _ = ingest.ingest_session(db, data, day=d(3))
    assert row.day == d(3) and row.score is not None and row.model_version
    assert not re.search(r"\d", fb.text)  # never a bare number


@pytest.mark.parametrize("pathway,signs,level,title", [
    ("stroke", ["face"], "call_112", "Takoj pokličite 112"),
    ("stroke", ["headache", "vision"], "call_112", "Takoj pokličite 112"),
    ("ctr", ["discharge"], "call_clinic", "Še danes pokličite ambulanto"),
])
def test_checkin_warning_feedback(db, pathway, signs, level, title):
    add_patient(db, pathway=pathway)
    _, fb = checkin(db, "p", d(0), signs=signs)
    assert (fb.level, fb.title) == (level, title)


def test_checkin_feedback_levels_thanks_then_neutral(db):
    add_patient(db)
    _, fb = checkin(db, "p", d(0), answers={"arm_function": 4})
    assert fb.level == "thanks"
    nxt = baseline_days(db, start=1)
    for i in range(3):
        play(db, "p", d(nxt + i), 40)
    _, fb = checkin(db, "p", d(nxt + 2))
    assert fb.level == "neutral"
    assert fb.text == "Rezultati so ta teden nekoliko drugačni. Vaš zdravnik jih vidi."
    for word in FORBIDDEN:
        assert word not in (fb.title + fb.text).lower()


def test_session_with_open_yellow_gets_neutral_and_no_retry(db):
    add_patient(db)
    nxt = baseline_days(db)
    for i in range(3):
        play(db, "p", d(nxt + i), 40)
    assert open_alerts(db)[0].severity == "yellow"
    _, fb, e = play(db, "p", d(nxt + 3), 20)
    assert fb.level == "neutral" and e["offer_retry"] is False


def test_session_on_day_with_stroke_sign_still_says_112(db):
    add_patient(db)
    baseline_days(db)
    checkin(db, "p", d(4), signs=["speech"])
    _, fb, _ = play(db, "p", d(4), 70)
    assert fb.level == "call_112"


def test_thanks_texts_have_no_numbers_or_impairment_words(db):
    add_patient(db)
    texts = [play(db, "p", d(i), 70 + i)[1].text for i in range(8)]
    texts.append(play(db, "p", d(8), 40)[1].text)
    for t in texts:
        assert not re.search(r"\d", t)
        for w in ("blaga", "zmerna", "huda", "normal", "severe", "mild", *FORBIDDEN):
            assert w not in t.lower()


def test_raw_series_stored(db):
    add_patient(db)
    row, _, _ = play(db, "p", d(0), 70)
    raw = db.exec(select(SessionRaw).where(SessionRaw.session_id == row.id)).one()
    assert raw.series["x"] == [0.1, 0.9] and raw.client_meta["inputDevice"] == "touch"
    assert db.exec(select(GameSession)).one().id == row.id


def test_api_session_flow(client):
    pid = next(p["id"] for p in client.get("/api/patients").json()["patients"] if p["pathwayCode"] == "stroke")
    body = {
        "patientId": pid, "gameType": "trace", "level": 2, "hand": "right",
        "startedAt": "2026-11-21T10:00:00Z", "durationMs": 9000, "completed": False,
        "abortReason": "cannot_today", "series": {"x": [], "y": []},
        "clientMeta": {"inputDevice": "touch", "canvasW": 400, "canvasH": 400},
    }
    res = client.post("/api/sessions", json=body)
    assert res.status_code == 200
    assert res.json()["comparedToUsual"] == "not_scored"
    assert client.post("/api/sessions", json={**body, "patientId": "nope"}).status_code == 404
    assert client.post("/api/sessions", json={**body, "level": 9}).status_code == 422
    msg = client.post("/api/messages", json={"patientId": pid, "clinicianId": "c1", "text": "Pozdravljeni"})
    assert msg.status_code == 200 and msg.json()["author"]
    assert client.post("/api/messages", json={"patientId": pid, "clinicianId": "x", "text": "a"}).status_code == 404
