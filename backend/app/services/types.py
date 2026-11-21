"""Value types shared by the services (plan section 5). Shared hot file."""
from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

ImpairmentClass = Literal["normal", "mild", "moderate", "severe"]
Direction = Literal["improving", "stable", "declining", "insufficient_data"]


@dataclass
class ScoreResult:
    features: dict[str, float]
    score: Optional[float]  # 0-100; None = not scorable (camera: no reference, scorer failed)
    impairment_class: Optional[ImpairmentClass]
    model_version: str
    # camera: capture quality from the scorer (detection rate, frame rate); None for trace.
    # False -> stored, but no score and not in the trend.
    quality_ok: Optional[bool] = None


@dataclass
class ScoredSession:
    """One past session of ONE game and ONE level, as input to assess_trend."""

    day: date
    duration_ms: int
    level: int
    score: float
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class TrendResult:
    direction: Direction
    baseline: Optional[float]
    smoothed: Optional[float]  # EWMA
    delta_vs_baseline: Optional[float]
    n_sessions: int
    model_version: str


@dataclass
class Feedback:
    """Patient-facing message after a submission."""

    level: Literal["thanks", "neutral", "call_clinic", "call_112"]
    title: str
    text: str
