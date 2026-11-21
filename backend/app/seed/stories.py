"""The ten patient stories of plan section 10, as pure functions.

`Story.plan(k, ...)` gives the entries of one day from (patient, k = days since discharge)
and a fixed RNG seed per (patient, day): the result never depends on call order or on the
system date. All scores are story curves + noise; nothing is scored from a trace.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

LEVELS = (1, 2, 3)
LEVEL_OFFSET = {1: 5.0, 2: 0.0, 3: -7.0}  # level 3 (maze) is harder
DECLINE_PER_DAY = 2.5  # simulate: slow decline of the game score, points per day
CLINICIAN_ID = "c1"


def rng_for(pid: str, k: int, tag: str = "") -> random.Random:
    return random.Random(f"{pid}:{k}:{tag}")


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _r(x: float, lo: int, hi: int) -> int:
    return int(_clip(round(x), lo, hi))


@dataclass
class CheckinSpec:
    answers: dict[str, float]
    concern: str = "none"
    text: Optional[str] = None
    signs: list[str] = field(default_factory=list)


@dataclass
class DayPlan:
    checkin: CheckinSpec
    scores: dict[int, float]  # level -> score


# ----------------------------------------------------------------- check-in generators
# each: (k, rng) -> CheckinSpec

def _stroke(arm: float, fatigue: float, rng: random.Random, sd: float = 0.5) -> dict[str, float]:
    return {"arm_function": _r(arm + rng.gauss(0, sd), 1, 5), "fatigue": _r(fatigue + rng.gauss(0, sd), 0, 4),
            "fall": 0}


def _ctr(pain: float, tingling: float, nights: float, rng: random.Random, sd: float = 0.5) -> dict[str, float]:
    return {"pain": _r(pain + rng.gauss(0, sd), 0, 10), "tingling": _r(tingling + rng.gauss(0, sd * 0.6), 0, 4),
            "night_wakings": _r(nights + rng.gauss(0, sd * 0.6), 0, 3)}


def ck_p1(k, rng):
    return CheckinSpec(_stroke(2.6 + k / 12, 2.4 - k / 15, rng,
                               0.45), concern="call" if k == 12 else "none",
                       text="Ali lahko vaje za roko nadaljujem tudi doma, brez fizioterapevta?" if k == 12 else None)


def ck_p2(k, rng):
    return CheckinSpec(_stroke(2.8 + 1.4 * (1 - math.exp(-k / 5)), 2.2 - 1.0 * (1 - math.exp(-k / 6)), rng))


def ck_p3(k, rng):  # calm and good while the game score falls: this is the divergence
    return CheckinSpec(_stroke(4.1 + (0.2 if k > 28 else 0.0), 1.0, rng, 0.35))


def ck_p4(k, rng):
    pain = 5.0 - 3.0 * min(1.0, k / 14)
    ting = {29: 0, 30: 1, 31: 1, 32: 1, 33: 2, 34: 2, 35: 3}.get(k, 0 if k < 29 else 3)
    ans = _ctr(pain, 0, 0.3, rng)
    ans["tingling"] = ting
    if k == 35:
        return CheckinSpec(ans, concern="call", signs=["discharge"],
                           text="Rana je danes začela puščati in prsti so vedno bolj otrpli. "
                                "Prosim, pokličite me.")
    if k > 35:
        return CheckinSpec(ans, concern="little", text="Prsti so še vedno otrpli.")
    return CheckinSpec(ans)


def ck_p5(k, rng):
    if k <= 7:
        pain = 1.8
    elif k <= 14:
        pain = 4.3
    else:
        pain = max(0.8, 4.3 - 0.22 * (k - 14))
    ans = _ctr(pain, max(0.0, 2.2 - k / 10), max(0.0, 2.0 - k / 8), rng, 0.4)
    return CheckinSpec(ans, concern="call" if k == 19 else "none",
                       text="Bolečina se mi je prvi teden povečala. Ali je to običajno?" if k == 19 else None)


def ck_p6(k, rng):
    if k < 24:
        return CheckinSpec(_stroke(4.0, 1.0, rng, 0.4))
    little = rng.random() < 0.5 or k >= 28
    text = ("Ali bo roka še kdaj tako kot prej? Skrbi me, da ne napredujem." if k % 3 == 0
            else "Počutim se utrujeno in negotovo pri vajah.")
    return CheckinSpec(_stroke(2.2, 3.2, rng, 0.4), concern="little" if little else "none",
                       text=text if little else None)


def ck_p7(k, rng):
    return CheckinSpec(_stroke(3.2, 2.0, rng))


def ck_p8(k, rng):
    return CheckinSpec(_stroke(3.5 + k / 40, 1.8, rng))


def ck_p9(k, rng):
    return CheckinSpec(_ctr(4.0, 1.5, 1.0, rng))


def ck_demo(k, rng):
    return CheckinSpec(_stroke(3.8, 1.2, rng))


def calm_checkin(pathway: str, rng: random.Random) -> CheckinSpec:
    if pathway == "ctr":
        return CheckinSpec(_ctr(1.0, 0.0, 0.0, rng, 0.3))
    return CheckinSpec(_stroke(4.0, 1.0, rng, 0.3))


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
    checkin: Callable[[int, random.Random], CheckinSpec]
    noise: float = 2.5
    skip_prob: float = 0.07
    reliable_from: int = 10 ** 6  # from this k on, no skipped days
    always: frozenset = frozenset()  # days that must have entries (they carry the story)
    days: Optional[frozenset] = None  # explicit entry days (silent / sparse patients)
    from_k: int = 1
    includes_today: bool = False  # the replay also writes "today" (patient 4)
    declining: bool = False  # the story already declines: simulate adds no decline mode
    silent: bool = False  # never produces new entries (patient 7)
    bad_days: dict = field(default_factory=dict)  # k -> score shift, all levels
    is_demo: bool = False
    # clinician actions: k -> (close, outcome, note); applied during replay on the open alert
    acks: dict = field(default_factory=dict)
    messages: tuple = ()  # (k, text)
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

    def plan(self, k: int, decline: Optional[tuple[int, float]] = None) -> Optional[DayPlan]:
        """Entries of day k, or None. decline = (k0, base): simulate's decline mode, the game
        score falls DECLINE_PER_DAY points per day from `base` and check-ins are calm."""
        if not self.active(k):
            return None
        rng = rng_for(self.id, k, "checkin")
        if decline is not None and k >= decline[0]:
            k0, base = decline
            level2 = base - DECLINE_PER_DAY * (k - k0 + 1)
            ck = calm_checkin(self.pathway, rng)
            noise = 1.2
        else:
            level2 = self.curve(k) + self.bad_days.get(k, 0.0)
            ck = self.checkin(k, rng)
            noise = self.noise
        scores = {}
        for lv in LEVELS:
            g = rng_for(self.id, k, f"score{lv}").gauss(0, noise)
            scores[lv] = round(_clip(level2 + LEVEL_OFFSET[lv] + g, 4.0, 98.0), 1)
        return DayPlan(ck, scores)


def _ramp(start: float, slope: float, cap: float) -> Callable[[int], float]:
    return lambda k: min(cap, start + slope * k)


def _p3_curve(k: int) -> float:
    if k <= 21:
        return 60.0 + 0.5 * k
    return max(20.0, 70.5 - 1.45 * (k - 21))


def _demo_curve(k: int) -> float:
    if k <= 4:
        return 63.0
    return 63.0 - 3.0 * min(1.0, (k - 4) / 5)


STORIES: list[Story] = [
    Story("p1", "Marija Kovač", 1952, "stroke", "right", 28, 14, 1,
          curve=_ramp(50, 0.85, 76), checkin=ck_p1, noise=2.5, reliable_from=24,
          always=frozenset({12, 13, 14}), acks={13: (False, None, None),
                14: (True, "adjusted_exercises",
                     "Telefonski pogovor: vaje za roko nadaljuje doma po načrtu, dodani dve kratki vaji za prste.")},
          messages=((14, "Lepo napredujete. Vaje nadaljujte kot doslej; kontrola ostaja po načrtu."),)),
    Story("p2", "Franc Horvat", 1948, "stroke", "left", 36, 9, 2,
          curve=lambda k: 52 + 28 * (1 - math.exp(-k / 5)), checkin=ck_p2, noise=2.0, reliable_from=30,
          input_device="mouse"),
    Story("p3", "Ivan Zupan", 1955, "stroke", "right", 40, 6, 3,
          curve=_p3_curve, checkin=ck_p3, noise=1.3, reliable_from=33, declining=True),
    Story("p4", "Ana Potočnik", 1961, "ctr", "right", 35, None, 4,
          curve=lambda k: 66.0, checkin=ck_p4, noise=2.5, reliable_from=26, includes_today=True),
    Story("p5", "Marta Novak", 1957, "ctr", "left", 28, 10, 5,
          curve=_ramp(52, 0.9, 76), checkin=ck_p5, noise=2.5, reliable_from=22,
          always=frozenset({19, 20}), acks={20: (True, "called_reassured",
                     "Poklicala pacientko: bolečina v prvih tednih po operaciji je pričakovana, brez posebnih ukrepov.")}),
    Story("p6", "Jože Kranjc", 1950, "stroke", "right", 30, 8, 6,
          curve=lambda k: 64.0, checkin=ck_p6, noise=2.0, reliable_from=20),
    Story("p7", "Silvester Mlakar", 1946, "stroke", "left", 15, 13, 7,
          curve=lambda k: 58.0 + 0.5 * k, checkin=ck_p7, noise=2.5,
          days=frozenset({1, 2, 3, 5, 6, 9}), silent=True, input_device="mouse"),
    Story("p8", "Tone Vidmar", 1953, "stroke", "right", 30, 12, 8,
          curve=lambda k: 62.0 + 0.15 * k, checkin=ck_p8, noise=4.0, reliable_from=8,
          always=frozenset({11, 21}), bad_days={11: -12.0, 21: -20.0}),
    Story("p9", "Nina Božič", 1969, "ctr", "right", 3, 25, 9,
          curve=lambda k: 55.0, checkin=ck_p9, noise=2.5, days=None, skip_prob=0.0,
          from_k=1),
    Story("demo", "Janez Demo", 1958, "stroke", "right", 21, 20, 99,
          curve=_demo_curve, checkin=ck_demo, noise=1.2, reliable_from=6, is_demo=True),
]
BY_ID = {s.id: s for s in STORIES}
