"""Configured pathways and synthetic demo registry data."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, cast

from sqlalchemy import column
from sqlmodel import Session, select

from app.db import create_schema, reset_schema
from app.models.tables import Alert, Clinician, Pathway, Patient
from app.seed.camera import features as camera_seed_features
from app.seed.stories import STORIES, rng_for
from app.seed.traces import level_features, synthetic_trace
from app.services import clock
from app.services.alerts import sweep_missing_data_alerts
from app.services.ingest import ingest_checkin, ingest_game_session
from app.services.scoring import camera_duration_s

PATHWAY_ROWS: tuple[tuple[str, str], ...] = (
    ("stroke", "Možganska kap"),
    ("ctr", "Operacija karpalnega kanala"),
)

GAME_ROWS: list[dict[str, object]] = [
    {"gameType": "trace", "title": "Sledi poti", "levels": [1, 2, 3], "optionalLevels": []},
    {
        "gameType": "camera",
        "title": "Vaje s kamero",
        "levels": [1, 2, 3],
        "optionalLevels": [2, 3],
    },
]
QUESTION_ROWS: list[dict[str, object]] = [
    {
        "id": "wellbeing",
        "text": "Kako se počutite danes?",
        "shortLabel": "Počutje",
        "kind": "scale",
        "min": 1,
        "max": 10,
        "minLabel": "Zelo slabo",
        "maxLabel": "Odlično",
        "higherIsWorse": False,
    },
    {
        "id": "pain",
        "text": "Kako močna je bolečina?",
        "shortLabel": "Bolečina",
        "kind": "scale",
        "min": 1,
        "max": 10,
        "minLabel": "Brez bolečine",
        "maxLabel": "Zelo močna",
        "higherIsWorse": True,
    },
]

# id, name, birth year, pathway code, side, days since discharge, days to visit, order, demo flag
DEMO_PATIENTS: tuple[tuple[str, str, int, str, str, int, int | None, int, bool], ...] = (
    ("p1", "Marija Kovač", 1952, "stroke", "right", 28, 14, 1, False),
    ("p2", "Franc Horvat", 1948, "stroke", "left", 36, 9, 2, False),
    ("p3", "Ivan Zupan", 1955, "stroke", "right", 40, 30, 3, False),
    ("p4", "Ana Potočnik", 1961, "ctr", "right", 35, None, 4, False),
    ("p5", "Marta Novak", 1957, "ctr", "left", 28, 10, 5, False),
    ("p6", "Jože Kranjc", 1950, "stroke", "right", 30, 8, 6, False),
    ("p7", "Silvester Mlakar", 1946, "stroke", "left", 15, 13, 7, False),
    ("p8", "Tone Vidmar", 1953, "stroke", "right", 30, 12, 8, False),
    ("p9", "Nina Božič", 1969, "ctr", "right", 3, 25, 9, False),
    ("demo", "Janez Demo", 1958, "stroke", "right", 21, 20, 99, True),
)


def seed_demo(session: Session) -> int:
    """Populate registry data and optionally replay the deterministic demo histories."""
    for code, name in PATHWAY_ROWS:
        session.add(
            Pathway(
                code=code,
                name=name,
                frequency="vsak dan",
                games=GAME_ROWS,
                questions=QUESTION_ROWS,
            )
        )
    session.add(Clinician(id="c1", name="dr. Ana Novak", role="zdravnica"))
    today = clock.today()
    for pid, name, birth_year, pathway, side, elapsed, visit, order, is_demo in DEMO_PATIENTS:
        session.add(
            Patient(
                id=pid,
                name=name,
                birth_year=birth_year,
                pathway_code=pathway,
                side=side,
                sort_order=order,
                is_demo=is_demo,
                discharge_date=today - timedelta(days=elapsed),
                next_visit_date=today + timedelta(days=visit) if visit is not None else None,
            )
        )
    session.commit()
    if os.getenv("APP_SEED_HISTORY", "1") != "0":
        replay_demo_history(session, today)
    return len(DEMO_PATIENTS)


def _apply_clinician_action(
    session: Session, patient_id: str, day: date, action: tuple[bool, str | None, str | None]
) -> None:
    close, outcome, note = action
    alert = session.exec(
        select(Alert)
        .where(
            column("patient_id") == patient_id,
            column("status").in_(["new", "acknowledged"]),
        )
        .order_by(column("id").desc())
    ).first()
    if alert is None:
        return
    clinician = session.get(Clinician, "c1")
    if clinician is None:
        raise RuntimeError("Demo clinician c1 is missing while applying a story action")
    timestamp = datetime.combine(day, time(hour=12), tzinfo=UTC)
    if alert.acknowledged_at is None:
        alert.acknowledged_by = clinician.name
        alert.acknowledged_at = timestamp
    if alert.status == "new":
        alert.status = "acknowledged"
    if close:
        alert.status = "closed"
        alert.closed_by = clinician.name
        alert.closed_at = timestamp
        alert.outcome = outcome
    if note is not None:
        alert.note = note
    alert.updated_at = timestamp
    session.add(alert)
    session.commit()


def replay_demo_history(session: Session, today: date) -> None:
    """Replay story entries chronologically, then sweep missing data for today."""
    earliest_discharge = min(today - timedelta(days=story.discharge_ago) for story in STORIES)
    original_day = clock.today()
    replay_days = (
        earliest_discharge + timedelta(days=offset)
        for offset in range(1, (today - earliest_discharge).days)
    )
    for replay_day in replay_days:
        clock.shift_days((replay_day - clock.today()).days)
        for story in STORIES:
            patient = session.get(Patient, story.id)
            if patient is None:
                raise RuntimeError(f"Demo story references missing patient {story.id!r}")
            day_index = (replay_day - patient.discharge_date).days
            plan = story.plan(day_index)
            if plan is not None:
                answers, scores, camera_scores = plan
                hour = 8 + sum(map(ord, patient.id)) % 9
                ingest_checkin(
                    session,
                    patient.id,
                    answers["wellbeing"],
                    answers["pain"],
                    day=replay_day,
                    created_at=datetime.combine(replay_day, time(hour - 1, 30), tzinfo=UTC),
                )
                for level in (1, 2, 3):
                    generated_features = level_features(
                        level, scores[level], rng_for(patient.id, day_index, f"feat{level}")
                    )
                    duration_ms = int(generated_features["duration_s"] * 1000)
                    series = synthetic_trace(
                        level,
                        generated_features["mean_dev"] * 1.4,
                        duration_ms=duration_ms,
                        lifts=int(generated_features["lifts"]),
                        seed=f"{patient.id}:{day_index}:{level}",
                    )
                    features = {
                        "dev_mean": round(generated_features["mean_dev"] / 0.06, 3),
                        "duration_s": generated_features["duration_s"],
                        "n_pauses": float(
                            round(
                                generated_features["pause_rate_hz"]
                                * generated_features["duration_s"]
                                / 4
                            )
                        ),
                        "n_lifts": generated_features["lifts"],
                    }
                    input_device = story.input_device
                    client_meta = {
                        "inputDevice": input_device,
                        "canvasW": 360 if input_device == "touch" else 480,
                        "canvasH": 360 if input_device == "touch" else 480,
                        "devicePixelRatio": 3 if input_device == "touch" else 2,
                        "userAgent": f"seed ({input_device})",
                    }
                    started_at = datetime.combine(replay_day, time(hour, 5 * level), tzinfo=UTC)
                    ingest_game_session(
                        session,
                        patient_id=patient.id,
                        game_type="trace",
                        level=level,
                        hand=patient.side,
                        started_at=started_at,
                        duration_ms=duration_ms,
                        completed=True,
                        abort_reason=None,
                        series=cast(dict[str, list[float | None]], series),
                        client_meta=client_meta,
                        day=replay_day,
                        preset_score=scores[level],
                        preset_features=features,
                    )
                for level, score in sorted(camera_scores.items()):
                    generated_features = camera_seed_features(
                        level, score, rng_for(patient.id, day_index, f"camfeat{level}")
                    )
                    camera_client_meta: dict[str, Any] = {
                        "inputDevice": "camera",
                        "canvasW": 1280,
                        "canvasH": 720,
                        "devicePixelRatio": 1,
                        "userAgent": "seed (camera)",
                        "videoW": 1280,
                        "videoH": 720,
                        "fpsMeasured": generated_features["fps"],
                    }
                    ingest_game_session(
                        session,
                        patient_id=patient.id,
                        game_type="camera",
                        level=level,
                        hand=patient.side,
                        started_at=datetime.combine(
                            replay_day, time(hour, 20 + 4 * level), tzinfo=UTC
                        ),
                        duration_ms=int((camera_duration_s(level) or 30.0) * 1000),
                        completed=True,
                        abort_reason=None,
                        series={},
                        client_meta=camera_client_meta,
                        day=replay_day,
                        preset_score=score,
                        preset_features=generated_features,
                        preset_model_version="camera-seed",
                        preset_quality_ok=True,
                    )
        sweep_missing_data_alerts(session, replay_day)
        for story in STORIES:
            day_index = (replay_day - (today - timedelta(days=story.discharge_ago))).days
            action = story.acks.get(day_index)
            if action is not None:
                _apply_clinician_action(session, story.id, replay_day, action)
    clock.shift_days((original_day - clock.today()).days)
    sweep_missing_data_alerts(session, today)


def initialize_demo(session: Session, keep_existing: bool) -> None:
    """Initialize database unless configured to preserve existing demo rows."""
    if keep_existing:
        create_schema()
        has_patients = session.exec(select(Patient.id)).first() is not None
        has_pathways = session.exec(select(Pathway.code)).first() is not None
        has_clinicians = session.exec(select(Clinician.id)).first() is not None
        if not (has_patients or has_pathways or has_clinicians):
            seed_demo(session)
        return
    reset_schema()
    clock.clear_shift()
    seed_demo(session)


def reset_demo(session: Session) -> int:
    """Drop and recreate all tables, then seed from the application date."""
    reset_schema()
    clock.clear_shift()
    return seed_demo(session)
