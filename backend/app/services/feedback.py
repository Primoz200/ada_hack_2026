"""What the patient is told at the end of the self-check and on "Moj napredek" (v8).

One calm, honest sentence or two about how it went compared with the patient's own
previous days. Never a number, never an impairment class, never a prompt to call anyone.
A declining trend is said honestly and calmly; alerts stay the clinician's business.

Every game (tracing, camera exercises) has its own combined trend (<game>:all); each game
weighs the same and nothing mixes their scores.

tone  (today vs the previous days): for each game played on the described day, that day's
      combined delta minus the mean of the game's previous up-to TONE_WINDOW session-days;
      the mean of these differences decides: better / lower by TONE_BAND, else similar
      (= today's mean over the games vs the previous days' mean over the same games).
      "first" while no game has a baseline. A day of tracing only is judged exactly as before
      camera exercises existed.
trend (the last days), per game: "declining" when the latest combined delta <= -TREND_BELOW
      and it is at least TREND_CHANGE lower than TREND_LOOKBACK session-days earlier (or the
      open alert has a trend trigger of that game); "improving" for the mirror case; else
      "stable"; "unknown" without a baseline. Overall: "declining" if ANY game is declining,
      "improving" only if none is declining and at least one is improving.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlmodel import Session, select

from app.models import TrendSnapshot
from app.services import alerts
from app.services.trend import GAMES

TONE_WINDOW = 5  # previous session-days the day is compared with
TONE_BAND = 3.0  # points of combined trend that count as better / lower
TREND_BELOW = 5.0  # the latest combined trend is outside the baseline band ...
TREND_CHANGE = 3.0  # ... and moved at least this much ...
TREND_LOOKBACK = 5  # ... since this many session-days earlier

# every patient-facing (title, text) the module can produce; keyed by (tone, trend)
MESSAGES: dict[tuple[str, str], tuple[str, str]] = {
    ("first", "unknown"): (
        "Hvala, samopregled je opravljen",
        "Prvi rezultati nam pomagajo spoznati, kaj je za vas običajno."),
    ("better", "stable"): (
        "Danes je šlo bolje",
        "Danes vam je šlo bolje kot prejšnje dni."),
    ("similar", "stable"): (
        "Danes je šlo podobno kot običajno",
        "Rezultati so podobni kot prejšnje dni. Hvala, ker redno opravljate samopregled."),
    ("lower", "stable"): (
        "Danes je šlo malo težje",
        "Danes je šlo malo težje kot prejšnje dni. Tak dan se zgodi; šteje potek skozi več dni."),
    ("better", "improving"): (
        "Lepo napredujete",
        "Danes vam je šlo bolje, tudi zadnje dni gre bolje kot prej."),
    ("similar", "improving"): (
        "Lepo napredujete",
        "Zadnje dni vam gre bolje kot prej."),
    ("lower", "improving"): (
        "Zadnje dni gre bolje",
        "Danes je šlo malo težje, a zadnje dni vam na splošno gre bolje kot prej."),
    ("better", "declining"): (
        "Danes je šlo bolje",
        "Danes je šlo bolje, zadnje dni pa gre nekoliko slabše kot prej. "
        "Vaš zdravnik ima vpogled v rezultate."),
    ("similar", "declining"): (
        "Zadnje dni gre nekoliko slabše",
        "Zadnje dni gre nekoliko slabše kot prej. Vaš zdravnik ima vpogled v rezultate."),
    ("lower", "declining"): (
        "Zadnje dni gre nekoliko slabše",
        "Danes je šlo težje in zadnje dni gre nekoliko slabše kot prej. "
        "Vaš zdravnik ima vpogled v rezultate."),
}


@dataclass
class FeedbackResult:
    tone: str
    trend: str
    title: str
    text: str
    day: Optional[date]  # the session-day described (None before any baseline)


def combined_points(db: Session, patient_id: str, upto: Optional[date] = None,
                    game: str = "trace") -> list[TrendSnapshot]:
    """<game>:all snapshots with a delta (the patient has a baseline), oldest first."""
    stmt = select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == f"{game}:all",
        TrendSnapshot.delta != None)  # noqa: E711
    if upto is not None:
        stmt = stmt.where(TrendSnapshot.day <= upto)
    return list(db.exec(stmt.order_by(TrendSnapshot.day)).all())


def points_by_game(db: Session, patient_id: str, upto: Optional[date] = None) -> dict[str, list[TrendSnapshot]]:
    """{game: combined snapshots} for the games that have any, tracing first."""
    out = {g: combined_points(db, patient_id, upto, g) for g in GAMES}
    return {g: s for g, s in out.items() if s}


def tone_diff(today: float, previous: list[float]) -> float:
    """today minus the mean of the previous days (0 = the baseline itself when there are none)."""
    ref = sum(previous) / len(previous) if previous else 0.0
    return today - ref


def _tone(diff: float) -> str:
    return "better" if diff >= TONE_BAND else "lower" if diff <= -TONE_BAND else "similar"


def tone_of(today: float, previous: list[float]) -> str:
    return _tone(tone_diff(today, previous))


def trend_of(deltas: list[float], game_alert: bool) -> str:
    """deltas: combined trend of all session-days so far, oldest first (non-empty)."""
    latest = deltas[-1]
    earlier = deltas[max(0, len(deltas) - 1 - TREND_LOOKBACK)] if len(deltas) > 1 else None
    if game_alert:
        return "declining"
    if earlier is not None:
        if latest <= -TREND_BELOW and latest <= earlier - TREND_CHANGE:
            return "declining"
        if latest >= TREND_BELOW and latest >= earlier + TREND_CHANGE:
            return "improving"
    return "stable"


def message(tone: str, trend: str) -> tuple[str, str]:
    if trend == "unknown" or tone == "first":
        return MESSAGES[("first", "unknown")]
    return MESSAGES[(tone, trend)]


def overall_trend(trends: list[str]) -> str:
    known = [t for t in trends if t != "unknown"]
    if not known:
        return "unknown"
    if "declining" in known:
        return "declining"
    return "improving" if "improving" in known else "stable"


def game_trends(db: Session, patient_id: str, day: date,
                per_game: Optional[dict[str, list[TrendSnapshot]]] = None) -> dict[str, str]:
    """{game: PatientTrend} for the games with a baseline as of `day`, tracing first."""
    per_game = points_by_game(db, patient_id, day) if per_game is None else per_game
    alert_games = alerts.open_alert_games(db, patient_id)
    return {g: trend_of([s.delta for s in snaps], g in alert_games) for g, snaps in per_game.items()}


def feedback_for(db: Session, patient_id: str, day: date) -> FeedbackResult:
    """Feedback as of `day`: describes that day if any game has a combined trend on it,
    otherwise the latest earlier session-day."""
    per_game = points_by_game(db, patient_id, day)
    if not per_game:
        title, text = message("first", "unknown")
        return FeedbackResult("first", "unknown", title, text, None)
    described = max(snaps[-1].day for snaps in per_game.values())
    diffs = []
    for snaps in per_game.values():
        if snaps[-1].day == described:
            deltas = [s.delta for s in snaps]
            diffs.append(tone_diff(deltas[-1], deltas[-1 - TONE_WINDOW:-1]))
    tone = _tone(sum(diffs) / len(diffs))
    trend = overall_trend(list(game_trends(db, patient_id, day, per_game).values()))
    title, text = message(tone, trend)
    return FeedbackResult(tone, trend, title, text, described)
