"""Database tables (IMPLEMENTATION_PLAN.md section 6).

Shared hot file: only the orchestrator / Matevž edits it. Agents that need a new
column report back instead of editing.
"""
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Pathway(SQLModel, table=True):
    code: str = Field(primary_key=True)  # "stroke" | "ctr"
    name: str
    frequency: str  # human readable, e.g. "vsak dan"
    games: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))


class Patient(SQLModel, table=True):
    id: str = Field(primary_key=True)  # "p1" ... "p9", "demo"
    name: str  # fictional
    birth_year: int
    pathway_code: str = Field(foreign_key="pathway.code", index=True)
    side: str  # "left" | "right" (affected / operated side)
    discharge_date: date
    next_visit_date: Optional[date] = None
    is_demo: bool = False
    sort_order: int = 0


class Clinician(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    role: str


class Checkin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    day: date = Field(index=True)
    created_at: datetime
    # {"wellbeing": 1-10 (higher = better), "pain": 1-10 (higher = worse)}
    answers: dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))


class GameSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    game_type: str  # "trace" | "camera_tapping" | "camera_reach" | "motion"
    level: int
    hand: str
    started_at: datetime
    day: date = Field(index=True)
    duration_ms: int
    completed: bool
    abort_reason: Optional[str] = None  # e.g. "cannot_today", "time_limit"
    input_device: str  # "touch" | "mouse" | "camera"
    score: Optional[float] = None  # 0-100, None when not scored (aborted)
    impairment_class: Optional[str] = None  # "normal" | "mild" | "moderate" | "severe"
    model_version: Optional[str] = None
    features: dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    # False for aborted / low quality sessions: stored but excluded from the trend
    counts_for_trend: bool = True


class SessionRaw(SQLModel, table=True):
    """Raw time series, kept out of GameSession so list queries never load them."""

    session_id: int = Field(primary_key=True, foreign_key="gamesession.id")
    series: dict[str, list[float]] = Field(default_factory=dict, sa_column=Column(JSON))
    client_meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class TrendSnapshot(SQLModel, table=True):
    """One row per patient + metric + day. Metric keys: trace:1, trace:2, trace:3, trace:all."""

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    metric: str = Field(index=True)
    day: date = Field(index=True)
    n_sessions: int
    baseline: Optional[float] = None
    ewma: Optional[float] = None
    slope: Optional[float] = None
    # EWMA minus baseline in score points; for trace:all the mean of per-level deltas
    delta: Optional[float] = None
    delta_pct: Optional[float] = None
    direction: str = "insufficient_data"  # improving | stable | declining | insufficient_data


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.id", index=True)
    source: str  # "game" | "checkin" | "missing"
    rule: str  # machine id of the rule that opened it
    severity: str  # "red" | "yellow" | "grey"
    status: str = "new"  # "new" | "acknowledged" | "closed"
    reason: str  # one sentence in Slovenian for the clinician
    # {"triggers": [{rule, severity, day, reason, ...}], "sessionIds": [...], "checkinIds": [...], ...}
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    diverging: bool = False  # objective and subjective signals disagree
    created_at: datetime
    updated_at: datetime
    opened_day: date
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    closed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    note: Optional[str] = None

