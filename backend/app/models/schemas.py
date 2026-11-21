"""Public request / response models (IMPLEMENTATION_PLAN.md section 7, v8).

This file IS the API contract: contracts/openapi.json and the TypeScript types are
generated from it. Shared hot file: only the orchestrator / Matevž edits it.
JSON is camelCase (matches GameResult in plan section 5).

v8: the patient only does a self-check (two ratings + games) and never gets a call
prompt. Alerts are the clinician's business only.
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


GameType = Literal["trace", "camera"]
Hand = Literal["left", "right"]
InputDevice = Literal["touch", "mouse", "camera"]
ImpairmentClass = Literal["normal", "mild", "moderate", "severe"]
TrendDirection = Literal["improving", "stable", "declining", "insufficient_data"]
Severity = Literal["red", "yellow", "grey"]
AlertStatus = Literal["new", "acknowledged", "closed"]
AlertSource = Literal["game", "checkin", "missing"]
# status shown in the triage list; "stable" patients are grey-neutral in the UI, not green
PatientStatus = Literal["red", "yellow", "no_data", "stable", "insufficient_data"]
Outcome = Literal[
    "called_reassured",  # poklical, pomiril
    "adjusted_exercises",  # prilagodil vaje
    "visit_moved_earlier",  # pregled prestavljen naprej
    "urgent_referral",  # nujna napotitev
    "unreachable",  # nedosegljiv
    "false_alarm",  # lažni alarm ali težava s podatki
]
# how today went compared with the patient's own recent days (never a number)
Tone = Literal["first", "better", "similar", "lower"]
# direction of the last days, in patient-facing terms; "unknown" until there is a baseline
PatientTrend = Literal["improving", "stable", "declining", "unknown"]


# ---------------------------------------------------------------- pathways

class PathwayGame(ApiModel):
    game_type: GameType
    title: str  # e.g. "Sledi poti", "Vaje s kamero"
    levels: list[int]  # one session per level in a self-check
    optional_levels: list[int] = []  # levels the patient may skip


class Question(ApiModel):
    """A daily rating. v8: every pathway has `wellbeing` and `pain`, both 1-10."""

    id: str
    kind: Literal["scale"] = "scale"
    text: str
    short_label: str  # e.g. "Počutje"
    min: int = 1
    max: int = 10
    min_label: Optional[str] = None
    max_label: Optional[str] = None
    higher_is_worse: bool = True


class PathwayOut(ApiModel):
    code: str
    name: str
    frequency: str
    games: list[PathwayGame]
    questions: list[Question]


# ---------------------------------------------------------------- alerts

class AlertOut(ApiModel):
    id: int
    patient_id: str
    patient_name: str
    source: AlertSource
    rule: str  # "trend_drop" | "subjective_drop" | "both" | "big_drop" | "no_data"
    # A trend rule is evaluated per game ("trace", "camera"); each trigger says which one.
    severity: Severity
    status: AlertStatus
    reason: str  # one sentence
    # {"triggers": [{rule, severity, day, reason, game?}], "games": {"trace": {"delta": float},
    #  "camera": {"delta": float}} (only the games that are below baseline), "delta": float|None
    #  (the worst of them), "wellbeingChange", "painChange", "sessionIds", "checkinIds",
    #  "divergence": str|None}
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


# ---------------------------------------------------------------- patients (triage list)

class SparkPoint(ApiModel):
    day: date
    value: Optional[float]


class PatientListItem(ApiModel):
    id: str
    name: str
    pathway_code: str
    pathway_name: str
    side: Hand
    days_since_discharge: int
    status: PatientStatus
    reason: str  # one short sentence, in words
    diverging: bool
    # last 21 days. game / camera: combined trend of that game, points vs own baseline
    # (camera is empty when the patient has no camera sessions). wellbeing: the 1-10 rating.
    game_sparkline: list[SparkPoint]
    camera_sparkline: list[SparkPoint]
    wellbeing_sparkline: list[SparkPoint]
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
    quality_ok: Optional[bool]  # camera: capture quality (detection rate, frame rate); None for trace


class CheckinOut(ApiModel):
    id: int
    patient_id: str
    day: date
    created_at: UtcDatetime
    answers: dict[str, float]  # {"wellbeing": 1-10, "pain": 1-10}


class TrendPoint(ApiModel):
    metric: str  # "<game>:<level>" or "<game>:all", game = "trace" | "camera"
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


# ---------------------------------------------------------------- patient home, self-check, progress

class SelfcheckStep(ApiModel):
    id: str  # "ratings" | "trace:1" | "trace:2" | "trace:3" | "camera:1" | "camera:2" | "camera:3"
    kind: Literal["ratings", "game"]
    title: str  # e.g. "Počutje in bolečina", "Ravna črta", "Dlan"
    game_type: Optional[GameType] = None
    level: Optional[int] = None
    done: bool  # already done today
    skippable: bool = False  # the patient may skip it (camera levels 2 and 3)
    duration_s: Optional[float] = None  # fixed length of the exercise, when it has one


class PatientHomeOut(ApiModel):
    patient_id: str
    name: str
    pathway_code: str
    pathway_name: str
    hand: Hand
    today: date
    steps: list[SelfcheckStep]  # in order; the self-check wizard walks through them
    # ratings and every trace level done; camera steps never block completion (no camera,
    # no permission and skipped exercises are all fine)
    selfcheck_done_today: bool
    last_selfcheck_day: Optional[date]


class ProgressPoint(ApiModel):
    day: date
    value: float  # combined trend, points vs own baseline (chart y; axis is labelled in words)
    label: Literal["lower", "usual", "better"]


class RatingPoint(ApiModel):
    day: date
    wellbeing: Optional[float]
    pain: Optional[float]


class PatientFeedback(ApiModel):
    """What the patient sees. Calm and honest: never a number, an impairment class or a
    prompt to call anyone."""

    tone: Tone
    trend: PatientTrend
    title: str
    text: str


class GameProgress(ApiModel):
    """One game's own trend for the patient. Tracing and camera exercises are shown separately."""

    game_type: GameType
    title: str  # "Sledenje" | "Vaje s kamero"
    trend: PatientTrend
    points: list[ProgressPoint]
    personal_best_day: Optional[date]


class SelfcheckSummary(PatientFeedback):
    """Shown once at the end of the self-check: how it went compared with previous days."""

    patient_id: str
    day: date
    levels_done: int  # game steps done today (all games)
    levels_total: int
    # last 14 days per game; only games the patient has data for (tracing first)
    games: list[GameProgress]


class ProgressOut(PatientFeedback):
    """"Moj napredek": a very simple dashboard."""

    patient_id: str
    games: list[GameProgress]  # whole history per game; only games with data (tracing first)
    ratings: list[RatingPoint]  # whole history
    week_done: int  # days with a self-check in the last 7
    week_goal: int  # 5 of 7
    clinician_reviewed_at: Optional[UtcDatetime]


# ---------------------------------------------------------------- submissions

class CheckinIn(ApiModel):
    """The two ratings at the start of a self-check."""

    patient_id: str
    wellbeing: int = Field(ge=1, le=10)  # higher = better
    pain: int = Field(ge=1, le=10)  # higher = worse


class CheckinResult(ApiModel):
    checkin_id: int


class ClientMeta(ApiModel):
    # extra keys are kept: camera sessions send videoW, videoH, fpsMeasured, detector ...
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True,
                              extra="allow")

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
    started_at: datetime
    duration_ms: int = Field(ge=0)
    completed: bool
    abort_reason: Optional[str] = None
    # trace: targetX, targetY, t, x, y, strokeId. camera: t, lm{i}_x/_y/_z, w{i}_x/_y/_z, lm{i}_v,
    # handScore, handMatch, cueT (null = no detection in that frame)
    series: dict[str, list[Optional[float]]]
    client_meta: ClientMeta


class SessionResult(ApiModel):
    session_id: int
    scored: bool  # False for aborted attempts


class SessionRawOut(ApiModel):
    session_id: int
    patient_id: str
    game_type: GameType
    level: int
    day: date
    score: Optional[float]
    series: dict[str, list[Optional[float]]]
    client_meta: dict[str, Any]


# ---------------------------------------------------------------- camera exercises

class CameraExercise(ApiModel):
    """Cue timeline of one camera exercise (single source of truth: backend/models/camera/exercises.py).
    Cues are at first_cue_s + k * cue_period_s, k = 0..n_cues-1; the time before the first cue is the
    rest pose. hand: cue = hand fully open. arms: cue = "up", held for up_s, then "down"."""

    level: int
    key: str  # "hand_open_close" | "shoulder_abduction" | "arm_raise"
    name: str
    detector: Literal["hand", "pose"]
    duration_s: float
    first_cue_s: float
    cue_period_s: float
    n_cues: int
    up_s: Optional[float] = None
    open_window_s: Optional[float] = None
    instructions: str


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
    default_patient_id: str  # the patient selected when the app opens


class ResetOut(ApiModel):
    ok: bool
    patients: int
