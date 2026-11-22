"""Pydantic API models with camelCase JSON aliases."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def to_camel(value: str) -> str:
    """Convert snake_case field names to camelCase."""
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    """Shared API serialization configuration."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_serializer("*", when_used="json")
    def serialize_utc_datetimes(self, value: Any) -> Any:
        """Serialize datetimes as UTC ISO 8601 strings ending in Z."""
        if isinstance(value, datetime):
            utc_value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
            return utc_value.isoformat().replace("+00:00", "Z")
        return value


class QuestionOut(ApiModel):
    id: str
    text: str
    short_label: str
    kind: Literal["scale"] = "scale"
    min: int = 1
    max: int = 10
    min_label: str | None = None
    max_label: str | None = None
    higher_is_worse: bool = True


class PathwayGameOut(ApiModel):
    game_type: Literal["trace", "camera"]
    title: str
    levels: list[int]
    optional_levels: list[int] = Field(default_factory=list)


class PathwayOut(ApiModel):
    code: str
    name: str
    frequency: str
    games: list[PathwayGameOut]
    questions: list[QuestionOut]


class ClinicianOut(ApiModel):
    id: str
    name: str
    role: str


class MetaOut(ApiModel):
    today: date
    synthetic_data: bool = True
    clinicians: list[ClinicianOut]
    outcomes: dict[str, str]
    model_version: str
    default_patient_id: str


class ResetOut(ApiModel):
    ok: bool
    patients: int


class SparkPoint(ApiModel):
    day: date
    value: float | None


class TriageCounters(ApiModel):
    needs_attention: int
    no_data: int
    stable: int
    total: int


class PatientListItem(ApiModel):
    id: str
    name: str
    pathway_code: str
    pathway_name: str
    side: Literal["left", "right"]
    days_since_discharge: int
    status: Literal["red", "yellow", "no_data", "stable", "insufficient_data"]
    reason: str
    diverging: bool
    game_sparkline: list[SparkPoint]
    camera_sparkline: list[SparkPoint]
    wellbeing_sparkline: list[SparkPoint]
    days_to_next_visit: int | None
    open_alert_id: int | None
    is_demo: bool


class PatientListOut(ApiModel):
    today: date
    counters: TriageCounters
    patients: list[PatientListItem]


class CheckinOut(ApiModel):
    id: int
    patient_id: str
    day: date
    created_at: datetime
    answers: dict[str, float]


class PatientHomeStep(ApiModel):
    id: str
    kind: Literal["ratings", "game"]
    title: str
    game_type: str | None
    level: int | None
    done: bool
    skippable: bool = False
    duration_s: float | None = None


class PatientHomeOut(ApiModel):
    patient_id: str
    name: str
    pathway_code: str
    pathway_name: str
    hand: Literal["left", "right"]
    today: date
    steps: list[PatientHomeStep]
    selfcheck_done_today: bool
    last_selfcheck_day: date | None


class FeedbackOut(ApiModel):
    tone: Literal["first", "better", "similar", "lower"]
    trend: Literal["unknown", "stable", "improving", "declining"]
    title: str
    text: str


class FeedbackPoint(ApiModel):
    day: date
    value: float
    label: Literal["lower", "better", "usual"]


class PatientRatingPoint(ApiModel):
    day: date
    wellbeing: float | None
    pain: float | None


class GameProgress(ApiModel):
    game_type: Literal["trace", "camera"]
    title: str
    trend: Literal["unknown", "stable", "improving", "declining"]
    points: list[FeedbackPoint]
    personal_best_day: date | None


class SelfcheckGamePoints(ApiModel):
    game_type: Literal["trace", "camera"]
    title: str
    trend: Literal["unknown", "stable", "improving", "declining"]
    points: list[FeedbackPoint]
    personal_best_day: date | None


class SelfcheckSummaryOut(ApiModel):
    tone: Literal["first", "better", "similar", "lower"]
    trend: Literal["unknown", "stable", "improving", "declining"]
    title: str
    text: str
    patient_id: str
    day: date
    levels_done: int
    levels_total: int
    games: list[SelfcheckGamePoints]


class PatientProgressOut(ApiModel):
    tone: Literal["first", "better", "similar", "lower"]
    trend: Literal["unknown", "stable", "improving", "declining"]
    title: str
    text: str
    patient_id: str
    games: list[GameProgress]
    ratings: list[PatientRatingPoint]
    week_done: int
    week_goal: int
    clinician_reviewed_at: datetime | None


class PatientSummary(ApiModel):
    n_sessions: int
    n_checkins: int
    last_session_day: date | None
    last_checkin_day: date | None
    combined_delta: float | None
    combined_direction: Literal["improving", "stable", "declining", "insufficient_data"]


class PatientDetail(ApiModel):
    id: str
    name: str
    birth_year: int
    pathway: PathwayOut
    side: Literal["left", "right"]
    discharge_date: date
    next_visit_date: date | None
    days_since_discharge: int
    days_to_next_visit: int | None
    status: Literal["red", "yellow", "no_data", "stable", "insufficient_data"]
    reason: str
    diverging: bool
    open_alert: AlertOut | None
    summary: PatientSummary
    is_demo: bool


class SessionSummary(ApiModel):
    id: int
    game_type: Literal["trace", "camera"]
    level: int
    hand: Literal["left", "right"]
    day: date
    started_at: datetime
    duration_ms: int
    completed: bool
    abort_reason: str | None
    input_device: Literal["touch", "mouse", "camera"]
    score: float | None
    impairment_class: Literal["normal", "mild", "moderate", "severe"] | None
    model_version: str | None
    features: dict[str, float]
    counts_for_trend: bool
    quality_ok: bool | None = None


class TrendPoint(ApiModel):
    metric: str
    day: date
    n_sessions: int
    baseline: float | None
    ewma: float | None
    delta: float | None
    delta_pct: float | None
    direction: Literal["improving", "stable", "declining", "insufficient_data"]


class TimelineOut(ApiModel):
    patient_id: str
    today: date
    discharge_date: date
    next_visit_date: date | None
    sessions: list[SessionSummary]
    checkins: list[CheckinOut]
    trends: list[TrendPoint]
    alerts: list[AlertOut]


class AlertAckIn(ApiModel):
    clinician_id: str
    close: bool = False
    note: str | None = None
    outcome: (
        Literal[
            "called_reassured",
            "adjusted_exercises",
            "visit_moved_earlier",
            "urgent_referral",
            "unreachable",
            "false_alarm",
        ]
        | None
    ) = None


class AlertOut(ApiModel):
    id: int
    patient_id: str
    patient_name: str
    source: Literal["game", "checkin", "missing"]
    rule: str
    severity: Literal["red", "yellow", "grey"]
    status: Literal["new", "acknowledged", "closed"]
    reason: str
    evidence: dict[str, Any]
    diverging: bool
    opened_day: date
    created_at: datetime
    updated_at: datetime
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    closed_by: str | None = None
    closed_at: datetime | None = None
    outcome: str | None = None
    note: str | None = None


class CheckinIn(ApiModel):
    """The two ratings at the start of a self-check."""

    patient_id: str
    wellbeing: int = Field(ge=1, le=10, strict=True)
    pain: int = Field(ge=1, le=10, strict=True)


class CheckinResult(ApiModel):
    checkin_id: int


class ClientMetaIn(ApiModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="allow",
    )

    input_device: Literal["touch", "mouse", "camera"]
    canvas_w: float
    canvas_h: float
    device_pixel_ratio: float = 1.0
    user_agent: str = ""


class SessionIn(ApiModel):
    patient_id: str
    game_type: Literal["trace", "camera"]
    level: int
    hand: Literal["left", "right"]
    started_at: datetime
    duration_ms: int = Field(ge=0, strict=True)
    completed: bool
    abort_reason: str | None = None
    series: dict[str, list[float | None]]
    client_meta: ClientMetaIn


class SessionResult(ApiModel):
    session_id: int
    scored: bool


class SessionRawOut(ApiModel):
    session_id: int
    patient_id: str
    game_type: Literal["trace", "camera"]
    level: int
    day: date
    score: float | None
    series: dict[str, list[float | None]]
    client_meta: dict[str, Any]


class CameraExerciseOut(ApiModel):
    level: int
    key: str
    name: str
    detector: Literal["hand", "pose"]
    duration_s: float
    first_cue_s: float
    cue_period_s: float
    n_cues: int
    up_s: float | None = None
    open_window_s: float | None = None
    instructions: str | None = None
