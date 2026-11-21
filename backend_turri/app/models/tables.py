"""SQLModel database tables."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class Pathway(SQLModel, table=True):
    """Recovery pathway configuration."""

    code: str = Field(primary_key=True)
    name: str
    frequency: str
    games: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))


class Clinician(SQLModel, table=True):
    """Clinician who handles patient alerts."""

    id: str = Field(primary_key=True)
    name: str
    role: str


class Checkin(SQLModel, table=True):
    """A patient's daily wellbeing and pain ratings."""

    __table_args__ = (UniqueConstraint("patient_id", "day"),)

    id: int | None = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    day: date = Field(index=True)
    created_at: datetime
    answers: dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))


class GameSession(SQLModel, table=True):
    """Metadata and score for one played game level; raw inputs are stored separately."""

    id: int | None = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    game_type: str = Field(index=True)
    level: int
    hand: str
    started_at: datetime
    day: date = Field(index=True)
    duration_ms: int
    completed: bool
    abort_reason: str | None = None
    input_device: str
    score: float | None = None
    impairment_class: str | None = None
    model_version: str | None = None
    features: dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    counts_for_trend: bool = False


class GameSessionRaw(SQLModel, table=True):
    """Raw series and client metadata, keyed by the associated game session."""

    session_id: int = Field(foreign_key="gamesession.id", primary_key=True)
    series: dict[str, list[float]] = Field(default_factory=dict, sa_column=Column(JSON))
    client_meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class TrendSnapshot(SQLModel, table=True):
    """Persisted trend values for one patient, game metric, and day."""

    __table_args__ = (UniqueConstraint("patient_id", "metric", "day"),)

    id: int | None = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    metric: str = Field(index=True)
    day: date = Field(index=True)
    sessions: int
    baseline: float | None = None
    ewma: float | None = None
    slope: float | None = None
    delta: float | None = None
    delta_percent: float | None = None
    direction: str


class Alert(SQLModel, table=True):
    """Clinician-facing patient alert and merged rule evidence."""

    id: int | None = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    patient_name: str
    source: str
    rule: str
    severity: str
    status: str = Field(default="new", index=True)
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    diverging: bool = False
    opened_day: date = Field(index=True)
    created_at: datetime
    updated_at: datetime
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    closed_by: str | None = None
    closed_at: datetime | None = None
    outcome: str | None = None
    note: str | None = None


class Patient(SQLModel, table=True):
    """Demo patient registry entry."""

    id: str = Field(primary_key=True)
    name: str
    birth_year: int
    pathway_code: str
    side: str
    sort_order: int = Field(default=0, index=True)
    is_demo: bool
    discharge_date: date
    next_visit_date: date | None = None
