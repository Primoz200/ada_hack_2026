"""Deterministic demo data: the ten patient stories of plan section 10.

The stories (app.seed.stories) are pure functions of (patient, day since discharge). The
replay below feeds them day by day through app.services.ingest and alerts.sweep, so trend
and alerts come from the live code path. Everything is relative to clock.today() at reset
time; the system date is never read directly.
"""
from datetime import date, timedelta

from sqlmodel import Session, select

from app import db as dbmod
from app.models import Message, Patient
from app.models.schemas import CheckinIn, ClientMeta, SessionIn
from app.seed import stories as st
from app.seed.pathways import fresh_clinicians, fresh_pathways
from app.seed.traces import level_features, synthetic_trace  # noqa: F401  (public: synthetic_trace)
from app.services import alerts, clock, ingest
from app.services.scoring import STANDIN_VERSION, score_to_class
from app.services.types import ScoreResult

_DEVICE_META = {
    "touch": dict(input_device="touch", canvasW=360, canvasH=360, device_pixel_ratio=3,
                  user_agent="seed (touch)"),
    "mouse": dict(input_device="mouse", canvasW=480, canvasH=480, device_pixel_ratio=2,
                  user_agent="seed (mouse)"),
}


def _hour(pid: str) -> int:
    return 8 + sum(map(ord, pid)) % 9


def _stored_features(feats: dict[str, float]) -> dict[str, float]:
    """Seeded features under the same names as Primož's model (backend/models/tracer/features.py),
    so seeded and live sessions show the same rows in the clinician's feature table."""
    return {
        "dev_mean": round(feats["mean_dev"] / 0.06, 3),  # in channel widths
        "duration_s": feats["duration_s"],
        "n_pauses": float(round(feats["pause_rate_hz"] * feats["duration_s"] / 4)),
        "n_lifts": feats["lifts"],
    }


def write_day(db: Session, story: st.Story, k: int, day: date,
              decline: tuple[int, float] | None = None) -> tuple[int, int]:
    """Write the story's entries for day index k through the real write path.
    Returns (check-ins, sessions) written."""
    plan = story.plan(k, decline)
    if plan is None:
        return 0, 0
    hour = _hour(story.id)
    c = plan.checkin
    ingest.ingest_checkin(
        db, CheckinIn(patient_id=story.id, warning_signs=c.signs, answers=c.answers, concern=c.concern,
                      concern_text=c.text),
        day=day, created_at=clock.at(day, hour - 1, 30))
    meta = ClientMeta(**_DEVICE_META[story.input_device])
    n_sessions = 0
    for level in st.LEVELS:
        score = plan.scores[level]
        rng = st.rng_for(story.id, k, f"feat{level}")
        feats = level_features(level, score, rng)
        duration_ms = int(feats["duration_s"] * 1000)
        series = synthetic_trace(level, feats["mean_dev"] * 1.4, duration_ms=duration_ms,
                                 lifts=int(feats["lifts"]), seed=f"{story.id}:{k}:{level}")
        when = clock.at(day, hour, 5 * level)
        ingest.ingest_session(
            db,
            SessionIn(patient_id=story.id, game_type="trace", level=level, hand=story.side,
                      started_at=when, duration_ms=duration_ms, completed=True, series=series,
                      client_meta=meta),
            day=day, created_at=when,
            preset_score=ScoreResult(_stored_features(feats), score, score_to_class(score), STANDIN_VERSION))
        n_sessions += 1
    return 1, n_sessions


def _clinician_actions(db: Session, story: st.Story, k: int, day: date) -> None:
    """Closed historical alerts and messages: the clock is fixed to that day meanwhile."""
    act = story.acks.get(k)
    if act is not None:
        alert = alerts.open_alert(db, story.id)
        if alert is not None:
            close, outcome, note = act
            alerts.acknowledge(db, alert.id, st.CLINICIAN_ID, close, outcome, note)
    for mk, text in story.messages:
        if mk == k:
            db.add(Message(patient_id=story.id, direction="to_patient", author="dr. Ana Novak",
                           text=text, created_at=clock.at(day, 10, 15)))
            db.commit()


def seed_patients(db: Session) -> None:
    today = clock.today()
    for s in st.STORIES:
        db.add(Patient(
            id=s.id, name=s.name, birth_year=s.birth_year, pathway_code=s.pathway, side=s.side,
            discharge_date=today - timedelta(days=s.discharge_ago),
            next_visit_date=today + timedelta(days=s.next_visit_in) if s.next_visit_in is not None else None,
            is_demo=s.is_demo, sort_order=s.sort_order))
    db.commit()

    first = min(-s.discharge_ago for s in st.STORIES)  # offset from today, most negative
    saved_fixed = clock._fixed_today
    try:
        for off in range(first + 1, 1):  # earliest discharge + 1 ... today
            day = today + timedelta(days=off)
            clock.set_today(day)  # acknowledge() stamps with the (replayed) day
            for s in st.STORIES:
                k = s.discharge_ago + off
                if k < 1 or (off == 0 and not s.includes_today):
                    continue
                write_day(db, s, k, day)
            alerts.sweep(db, day)
            for s in st.STORIES:
                k = s.discharge_ago + off
                if k >= 1 and off < 0:
                    _clinician_actions(db, s, k, day)
    finally:
        clock.set_today(saved_fixed)


def seed(db: Session) -> int:
    for row in fresh_pathways() + fresh_clinicians():
        db.add(row)
    db.commit()
    seed_patients(db)
    return len(db.exec(select(Patient)).all())


def reset_database() -> int:
    """Drop everything, recreate, reseed. Returns the number of patients.

    Clears the simulate offset and decline modes; a fixed "today" (tests, APP_TODAY) stays."""
    from app.seed import simulate

    clock.advance(-clock._offset_days)
    simulate.clear()
    dbmod.drop_tables()
    dbmod.create_tables()
    with Session(dbmod.engine) as db:
        return seed(db)


def seed_if_empty() -> None:
    dbmod.create_tables()
    with Session(dbmod.engine) as db:
        if db.exec(select(Patient)).first() is None:
            seed(db)
