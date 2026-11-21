"""Deterministic demo data.

Phase 0: a tiny dev seed (2 patients). The Phase 2 agent replaces `seed_patients`
with the ten stories of plan section 10, replayed day by day through
app.services.ingest so trend and alerts come from the live code path.
"""
import math
from datetime import timedelta

from sqlmodel import Session, select

from app import db as dbmod
from app.models import Patient
from app.models.schemas import ClientMeta, SessionIn
from app.seed.pathways import fresh_clinicians, fresh_pathways
from app.services import clock, ingest
from app.services.scoring import STANDIN_VERSION, score_to_class
from app.services.types import ScoreResult


def synthetic_trace(level: int, wobble: float) -> dict[str, list[float]]:
    """A simple plan-section-5 trace (normalised 0-1) so the replay screen has data."""
    if level == 2:
        pts = [(0.5 + 0.3 * math.cos(a), 0.5 + 0.3 * math.sin(a))
               for a in [2 * math.pi * i / 72 for i in range(73)]]
    else:
        pts = [(0.1 + 0.8 * i / 60, 0.5) for i in range(61)]
    n = len(pts)
    return {
        "targetX": [round(p[0], 4) for p in pts],
        "targetY": [round(p[1], 4) for p in pts],
        "t": [float(i * 120) for i in range(n)],
        "x": [round(p[0] + wobble * math.sin(i * 0.9), 4) for i, p in enumerate(pts)],
        "y": [round(p[1] + wobble * math.cos(i * 0.7), 4) for i, p in enumerate(pts)],
        "strokeId": [0.0] * n,
    }


def seed_patients(db: Session) -> None:
    today = clock.today()
    db.add(Patient(id="p1", name="Marija Kovač", birth_year=1952, pathway_code="stroke", side="right",
                   discharge_date=today - timedelta(days=20), next_visit_date=today + timedelta(days=12),
                   sort_order=1))
    db.add(Patient(id="demo", name="Janez Demo", birth_year=1958, pathway_code="stroke", side="right",
                   discharge_date=today - timedelta(days=14), next_visit_date=today + timedelta(days=20),
                   is_demo=True, sort_order=99))
    db.commit()
    meta = ClientMeta(input_device="touch", canvasW=360, canvasH=360, device_pixel_ratio=3, user_agent="seed")
    for pid, base in (("p1", 70.0), ("demo", 62.0)):
        for back in range(8, 0, -1):
            day = today - timedelta(days=back)
            for level in (1, 2, 3):
                score = round(base + (8 - back) * 1.2 - level * 3 + (back % 3), 1)
                ingest.ingest_session(
                    db,
                    SessionIn(patient_id=pid, game_type="trace", level=level, hand="right",
                              started_at=clock.at(day, 9, level), duration_ms=9000 + level * 2000,
                              completed=True, series=synthetic_trace(level, 0.01), client_meta=meta),
                    day=day, created_at=clock.at(day, 9, level),
                    preset_score=ScoreResult({"mean_dev": 0.01}, score, score_to_class(score), STANDIN_VERSION),
                )


def seed(db: Session) -> int:
    for row in fresh_pathways() + fresh_clinicians():
        db.add(row)
    db.commit()
    seed_patients(db)
    return len(db.exec(select(Patient)).all())


def reset_database() -> int:
    """Drop everything, recreate, reseed. Returns the number of patients."""
    clock.reset()
    dbmod.drop_tables()
    dbmod.create_tables()
    with Session(dbmod.engine) as db:
        return seed(db)


def seed_if_empty() -> None:
    dbmod.create_tables()
    with Session(dbmod.engine) as db:
        if db.exec(select(Patient)).first() is None:
            seed(db)
