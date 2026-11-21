"""The ten patient stories (plan section 10, v8), as pure functions.

`Story.plan(k)` gives the entries of one day from (patient, k = days since discharge) and a
fixed RNG seed per (patient, day): the result never depends on call order or on the
system date. A day is one self-check: the two ratings (wellbeing 1-10, higher = better;
pain 1-10, higher = worse) and one session of each trace level. All scores are story
curves + noise; nothing is scored from a trace.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

LEVELS = (1, 2, 3)
LEVEL_OFFSET = {1: 5.0, 2: 0.0, 3: -7.0}  # level 3 (maze) is harder
CLINICIAN_ID = "c1"

Ratings = dict[str, float]


def rng_for(pid: str, k: int, tag: str = "") -> random.Random:
    return random.Random(f"{pid}:{k}:{tag}")


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _r(x: float) -> int:
    return int(_clip(round(x), 1, 10))


def ratings(wellbeing: float, pain: float, rng: random.Random, sd: float = 0.5) -> Ratings:
    return {"wellbeing": _r(wellbeing + rng.gauss(0, sd)), "pain": _r(pain + rng.gauss(0, sd))}


@dataclass
class DayPlan:
    ratings: Ratings
    scores: dict[int, float]  # level -> score


# ----------------------------------------------------------------- ratings per story
# each: (k, rng) -> Ratings

def rt_p1(k, rng):  # recovering: feels better, less pain
    return ratings(5.0 + min(3.0, k / 9), max(2.0, 4.5 - k / 10), rng, 0.5)


def rt_p2(k, rng):
    return ratings(5.5 + 2.0 * (1 - math.exp(-k / 6)), 3.5 - 1.5 * (1 - math.exp(-k / 6)), rng, 0.5)


def rt_p3(k, rng):  # calm and constant while the game score slowly falls
    return ratings(7.0, 2.5, rng, 0.35)


def rt_p4(k, rng):  # ctr: post-op pain eases, then from day 27 pain up and wellbeing down
    if k < 27:
        return ratings(5.5 + 1.5 * min(1.0, k / 14), 5.0 - 3.0 * min(1.0, k / 14), rng, 0.4)
    f = min(1.0, (k - 26) / 4)
    return ratings(7.0 - 3.0 * f, 2.0 + 3.5 * f, rng, 0.4)


def rt_p5(k, rng):  # ctr: a week of more pain in week 2 (expected after the operation)
    if k <= 7:
        pain = 3.0
    elif k <= 14:
        pain = 6.0
    else:
        pain = max(1.5, 4.0 - 0.2 * (k - 14))
    return ratings(6.5, pain, rng, 0.4)


def rt_p6(k, rng):  # game stable, but from day 24 the patient feels worse
    if k < 24:
        return ratings(7.0, 2.0, rng, 0.4)
    return ratings(4.0, 3.5, rng, 0.4)


def rt_p7(k, rng):
    return ratings(6.0, 3.0, rng)


def rt_p8(k, rng):  # noisy but stable
    return ratings(6.5, 3.0, rng, 0.9)


def rt_p9(k, rng):
    return ratings(5.5, 4.0, rng)


def rt_demo(k, rng):
    return ratings(7.0, 2.0, rng, 0.4)


# ----------------------------------------------------------------- the story

@dataclass(frozen=True)
class Story:
    id: str
    name: str
    birth_year: int
    pathway: str
    side: str
    discharge_ago: int  # days before "today" at reset time
    next_visit_in: Optional[int]
    sort_order: int
    curve: Callable[[int], float]  # base score of level 2 on day k
    ratings: Callable[[int, random.Random], Ratings]
    noise: float = 2.5
    skip_prob: float = 0.07
    reliable_from: int = 10 ** 6  # from this k on, no skipped days
    always: frozenset = frozenset()  # days that must have entries (they carry the story)
    days: Optional[frozenset] = None  # explicit entry days (silent / sparse patients)
    from_k: int = 1
    bad_days: dict = field(default_factory=dict)  # k -> score shift, all levels
    level_offset: Optional[dict] = None  # per-level offsets (default LEVEL_OFFSET)
    is_demo: bool = False
    # clinician actions: k -> (close, outcome, note); applied during replay on the open alert
    acks: dict = field(default_factory=dict)
    input_device: str = "touch"

    # --- adherence
    def _missed(self, k: int) -> bool:
        return rng_for(self.id, k, "skip").random() < self.skip_prob

    def active(self, k: int) -> bool:
        if k < self.from_k:
            return False
        if self.days is not None:
            return k in self.days
        if k >= self.reliable_from or k <= 3 or k in self.always:
            return True
        # a missed day here and there, never two in a row
        return not (self._missed(k) and not self._missed(k - 1) and not self._missed(k + 1))

    def plan(self, k: int) -> Optional[DayPlan]:
        """Entries of day k, or None."""
        if not self.active(k):
            return None
        level2 = self.curve(k) + self.bad_days.get(k, 0.0)
        offsets = self.level_offset or LEVEL_OFFSET
        scores = {}
        for lv in LEVELS:
            g = rng_for(self.id, k, f"score{lv}").gauss(0, self.noise)
            scores[lv] = round(_clip(level2 + offsets[lv] + g, 4.0, 98.0), 1)
        return DayPlan(self.ratings(k, rng_for(self.id, k, "ratings")), scores)


def _ramp(start: float, slope: float, cap: float) -> Callable[[int], float]:
    return lambda k: min(cap, start + slope * k)


P3_PEAK_DAY = 21  # three weeks of good recovery ...
P3_RISE = 0.25  # ... points per day ...
P3_DECLINE = 0.85  # ... then a slow decline, points per day (hard to see day to day)


def _p3_curve(k: int) -> float:
    if k <= P3_PEAK_DAY:
        return 69.0 + P3_RISE * k
    return 69.0 + P3_RISE * P3_PEAK_DAY - P3_DECLINE * (k - P3_PEAK_DAY)


def _p4_curve(k: int) -> float:
    return 66.0 if k <= 26 else 66.0 - 2.5 * (k - 26)


def _demo_curve(k: int) -> float:
    return 63.0 + 0.1 * k


STORIES: list[Story] = [
    Story("p1", "Marija Kovač", 1952, "stroke", "right", 28, 14, 1,
          curve=_ramp(50, 0.85, 76), ratings=rt_p1, noise=2.5, reliable_from=24),
    Story("p2", "Franc Horvat", 1948, "stroke", "left", 36, 9, 2,
          curve=lambda k: 52 + 28 * (1 - math.exp(-k / 5)), ratings=rt_p2, noise=2.0, reliable_from=30,
          input_device="mouse"),
    # the main demo patient: about a month to the next visit, drifting below baseline, no alert yet
    Story("p3", "Ivan Zupan", 1955, "stroke", "right", 40, 30, 3,
          curve=_p3_curve, ratings=rt_p3, noise=0.7, reliable_from=P3_PEAK_DAY,
          level_offset={1: 2.0, 2: 0.0, 3: -2.0}, input_device="mouse"),
    Story("p4", "Ana Potočnik", 1961, "ctr", "right", 35, None, 4,
          curve=_p4_curve, ratings=rt_p4, noise=2.0, reliable_from=24),
    Story("p5", "Marta Novak", 1957, "ctr", "left", 28, 10, 5,
          curve=_ramp(52, 0.9, 76), ratings=rt_p5, noise=2.5, reliable_from=22,
          always=frozenset({4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}),
          acks={13: (False, None, None),
                14: (True, "called_reassured",
                     "Poklicala pacientko: močnejša bolečina v drugem tednu po operaciji je pričakovana, "
                     "brez posebnih ukrepov.")}),
    Story("p6", "Jože Kranjc", 1950, "stroke", "right", 30, 8, 6,
          curve=lambda k: 64.0, ratings=rt_p6, noise=2.0, reliable_from=20),
    Story("p7", "Silvester Mlakar", 1946, "stroke", "left", 15, 13, 7,
          curve=lambda k: 58.0 + 0.5 * k, ratings=rt_p7, noise=2.5,
          days=frozenset({1, 2, 3, 5, 6, 9}), input_device="mouse"),
    Story("p8", "Tone Vidmar", 1953, "stroke", "right", 30, 12, 8,
          curve=lambda k: 62.0 + 0.15 * k, ratings=rt_p8, noise=4.0, reliable_from=8,
          always=frozenset({11, 21}), bad_days={11: -12.0, 21: -20.0}),
    Story("p9", "Nina Božič", 1969, "ctr", "right", 3, 25, 9,
          curve=lambda k: 55.0, ratings=rt_p9, noise=2.5, skip_prob=0.0),
    Story("demo", "Janez Demo", 1958, "stroke", "right", 21, 20, 99,
          curve=_demo_curve, ratings=rt_demo, noise=1.2, reliable_from=6, is_demo=True),
]
BY_ID = {s.id: s for s in STORIES}
