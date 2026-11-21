"""Public request / response models (IMPLEMENTATION_PLAN.md section 7).

This file IS the API contract: contracts/openapi.json and the TypeScript types are
generated from it. Shared hot file: only the orchestrator / Matevž edits it.
JSON is camelCase (matches GameResult in plan section 5).
"""
from datetime import date, datetime, timezone
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel


def _utc_iso(d: datetime) -> str:
    # SQLite aggregates (e.g. max()) return naive datetimes; everything stored is UTC.
    d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_utc_iso, return_type=str, when_used="json")]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


GameType = Literal["trace", "camera_tapping", "camera_reach", "motion"]
Hand = Literal["left", "right"]
InputDevice = Literal["touch", "mouse", "camera"]
ImpairmentClass = Literal["normal", "mild", "moderate", "severe"]
TrendDirection = Literal["improving", "stable", "declining", "insufficient_data"]
Severity = Literal["red", "yellow", "grey"]
AlertStatus = Literal["new", "acknowledged", "closed"]
AlertSource = Literal["game", "checkin", "missing"]
# status shown in the triage list; "stable" patients are grey-neutral in the UI, not green
PatientStatus = Literal["red", "yellow", "no_data", "stable", "insufficient_data"]
Concern = Literal["none", "little", "call"]
AnsweredBy = Literal["self", "assisted", "relative"]
# four patient-facing message levels (plan section 9, Pacient, item 5)
MessageLevel = Literal["thanks", "neutral", "call_clinic", "call_112"]
Outcome = Literal[
    "called_reassured",  # poklical, pomiril
    "adjusted_exercises",  # prilagodil vaje
    "visit_moved_earlier",  # pregled prestavljen naprej
    "urgent_referral",  # nujna napotitev
    "unreachable",  # nedosegljiv
    "false_alarm",  # lažni alarm ali težava s podatki
]
QuestionKind = Literal["faces5", "scale", "yes_no", "count"]


# ---------------------------------------------------------------- pathways

class PathwayGame(ApiModel):
    game_type: GameType
    title: str  # e.g. "Sledi poti"
    levels: list[int]  # one session per level in a measurement round


class Question(ApiModel):
    id: str
    kind: QuestionKind
    text: str
    min: int = 0
    max: int = 1
    min_label: Optional[str] = None
    max_label: Optional[str] = None
    higher_is_worse: bool = True


class WarningSign(ApiModel):
    id: str
    text: str
    action: Literal["call_112", "call_clinic"]


class PathwayOut(ApiModel):
    code: str
    name: str
    frequency: str
    games: list[PathwayGame]
    questions: list[Question]
    warning_signs: list[WarningSign]
    warning_signs_prompt: str  # the first check-in question


# ---------------------------------------------------------------- alerts

class AlertOut(ApiModel):
    id: int
    patient_id: str
    patient_name: str
    source: AlertSource
    rule: str
    severity: Severity
    status: AlertStatus
    reason: str
    evidence: dict[str, Any]
    diverging: bool
    opened_day: date
    created_at: UtcDatetime
    updated_at: UtcDatetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[UtcDatetime] = None
    closed_by: Optional[str] = None
    closed_at: Optional[UtcDatetime] = None
    outcome: Optional[Outcome] = None
    note: Optional[str] = None


class AlertAckIn(ApiModel):
    clinician_id: str
    # close=False: acknowledge only. close=True requires an outcome (422 otherwise).
    close: bool = False
    outcome: Optional[Outcome] = None
    note: Optional[str] = None


# ---------------------------------------------------------------- messages

class MessageOut(ApiModel):
    id: int
    patient_id: str
    direction: Literal["to_patient", "system"]
    author: Optional[str] = None
    text: str
    created_at: UtcDatetime


class MessageIn(ApiModel):
    patient_id: str
    clinician_id: str
    text: str = Field(min_length=1, max_length=1000)


# ---------------------------------------------------------------- patients (triage list)

class SparkPoint(ApiModel):
    day: date
    value: Optional[float]  # combined trend: points vs own baseline


class PatientListItem(ApiModel):
    id: str
    name: str
    pathway_code: str
    pathway_name: str
    side: Hand
    days_since_discharge: int
    status: PatientStatus
    reason: str  # one sentence, in words
    diverging: bool
    sparkline: list[SparkPoint]
    checkins_7d: int = Field(alias="checkins7d")
    days_to_next_visit: Optional[int]
    open_alert_id: Optional[int]
    is_demo: bool


class TriageCounters(ApiModel):
    needs_attention: int
    no_data: int
    stable: int
    total: int


class PatientListOut(ApiModel):
    today: date
    counters: TriageCounters
    patients: list[PatientListItem]  # sorted by urgency


class PatientSummary(ApiModel):
    n_sessions: int
    n_checkins: int
    last_session_day: Optional[date]
    last_checkin_day: Optional[date]
    combined_delta: Optional[float]
    combined_direction: TrendDirection


class PatientDetail(ApiModel):
    id: str
    name: str
    birth_year: int
    pathway: PathwayOut
    side: Hand
    discharge_date: date
    next_visit_date: Optional[date]
    days_since_discharge: int
    days_to_next_visit: Optional[int]
    status: PatientStatus
    reason: str
    diverging: bool
    open_alert: Optional[AlertOut]
    summary: PatientSummary
    is_demo: bool


# ---------------------------------------------------------------- timeline

class SessionSummary(ApiModel):
    """A game session WITHOUT raw series."""

    id: int
    game_type: GameType
    level: int
    hand: Hand
    day: date
    started_at: UtcDatetime
    duration_ms: int
    completed: bool
    abort_reason: Optional[str]
    input_device: InputDevice
    score: Optional[float]
    impairment_class: Optional[ImpairmentClass]
    model_version: Optional[str]
    features: dict[str, float]
    counts_for_trend: bool


class CheckinOut(ApiModel):
    id: int
    patient_id: str
    day: date
    created_at: UtcDatetime
    warning_signs: list[str]
    answers: dict[str, float]
    concern: Concern
    concern_text: Optional[str]
    answered_by: AnsweredBy


class TrendPoint(ApiModel):
    metric: str  # "trace:1" | "trace:2" | "trace:3" | "trace:all"
    day: date
    n_sessions: int
    baseline: Optional[float]
    ewma: Optional[float]
    delta: Optional[float]
    delta_pct: Optional[float]
    direction: TrendDirection


class TimelineOut(ApiModel):
    patient_id: str
    today: date
    discharge_date: date
    next_visit_date: Optional[date]
    sessions: list[SessionSummary]
    checkins: list[CheckinOut]
    trends: list[TrendPoint]
    alerts: list[AlertOut]  # all alerts incl. closed (chart markers + action log)
    messages: list[MessageOut]


# ---------------------------------------------------------------- patient "Danes" + progress

class TodayTask(ApiModel):
    id: str  # "checkin" | "trace:1" ...
    kind: Literal["checkin", "game"]
    title: str
    game_type: Optional[GameType] = None
    level: Optional[int] = None
    done: bool


class TodayOut(ApiModel):
    patient_id: str
    name: str
    pathway_code: str
    hand: Hand
    today: date
    tasks: list[TodayTask]
    streak_days: int
    week_done: int  # days with any entry in the last 7
    last_message: Optional[MessageOut]
    reminder: Optional[str]  # automatic reminder after 2 missed days
    clinician_reviewed_at: Optional[UtcDatetime]


class ProgressPoint(ApiModel):
    day: date
    value: float  # combined trend, points vs own baseline (chart y; axis is labelled in words)
    label: Literal["lower", "usual", "better"]


class ProgressOut(ApiModel):
    patient_id: str
    points: list[ProgressPoint]
    personal_best_day: Optional[date]
    week_done: int
    week_goal: int  # 5 of 7
    clinician_reviewed_at: Optional[UtcDatetime]


# ---------------------------------------------------------------- check-ins

class CheckinIn(ApiModel):
    patient_id: str
    warning_signs: list[str] = []
    answers: dict[str, float] = {}
    concern: Concern = "none"
    concern_text: Optional[str] = None
    answered_by: AnsweredBy = "self"


class PatientFeedback(ApiModel):
    """What the patient sees after submitting. Never a bare number or impairment class."""

    message_level: MessageLevel
    message_title: str
    message_text: str


class CheckinResult(PatientFeedback):
    checkin_id: int


# ---------------------------------------------------------------- game sessions

class ClientMeta(ApiModel):
    input_device: InputDevice
    canvas_w: float = Field(alias="canvasW")
    canvas_h: float = Field(alias="canvasH")
    device_pixel_ratio: float = 1.0
    user_agent: str = ""


class SessionIn(ApiModel):
    """GameResult (plan section 5) + patientId."""

    patient_id: str
    game_type: GameType
    level: int
    hand: Hand
    started_at: UtcDatetime
    duration_ms: int = Field(ge=0)
    completed: bool
    abort_reason: Optional[str] = None
    series: dict[str, list[float]]
    client_meta: ClientMeta


class SessionResult(PatientFeedback):
    session_id: int
    compared_to_usual: Literal["first", "better", "similar", "lower", "not_scored"]
    offer_retry: bool  # a single poor result offers a repeat; the clinician gets nothing
    personal_best: bool


class SessionRawOut(ApiModel):
    session_id: int
    patient_id: str
    game_type: GameType
    level: int
    day: date
    score: Optional[float]
    series: dict[str, list[float]]
    client_meta: dict[str, Any]


# ---------------------------------------------------------------- meta + admin

class ClinicianOut(ApiModel):
    id: str
    name: str
    role: str


class MetaOut(ApiModel):
    today: date
    synthetic_data: bool = True
    clinicians: list[ClinicianOut]
    outcomes: dict[str, str]  # outcome id -> Slovenian label
    model_version: str


class ResetOut(ApiModel):
    ok: bool
    patients: int


class SimulateIn(ApiModel):
    patient_id: str
    days: int = Field(default=7, ge=1, le=30)


class SimulateOut(ApiModel):
    patient_id: str
    days_added: int
    sessions_added: int
    checkins_added: int
    today: date  # the (shifted) "today" after simulation
