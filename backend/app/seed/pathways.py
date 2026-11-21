"""Recovery pathways as configuration (plan sections 1, 8, 9). A new condition is a
new entry here, not new code.

v8: every pathway asks the same two daily ratings (wellbeing, pain; 1-10) and has no
warning signs: the patient is never prompted to call anyone.
"""
from app.models import Clinician, Pathway

TRACE_GAME = {"gameType": "trace", "title": "Sledi poti", "levels": [1, 2, 3]}
# Camera exercises (Primož, backend/models/camera): hand first, the two arm exercises may be skipped.
CAMERA_GAME = {"gameType": "camera", "title": "Vaje s kamero", "levels": [1, 2, 3], "optionalLevels": [2, 3]}

LEVEL_TITLES = {("trace", 1): "Ravna črta", ("trace", 2): "Krog", ("trace", 3): "Labirint",
                ("camera", 1): "Dlan", ("camera", 2): "Roke v stran", ("camera", 3): "Dvig rok"}
GAME_TITLES = {"trace": "Sledenje", "camera": "Vaje s kamero"}  # patient- and clinician-facing

RATINGS = [
    {"id": "wellbeing", "kind": "scale", "text": "Kako se počutite danes?", "shortLabel": "Počutje",
     "min": 1, "max": 10, "minLabel": "Zelo slabo", "maxLabel": "Odlično", "higherIsWorse": False},
    {"id": "pain", "kind": "scale", "text": "Kako močna je bolečina?", "shortLabel": "Bolečina",
     "min": 1, "max": 10, "minLabel": "Brez bolečine", "maxLabel": "Zelo močna", "higherIsWorse": True},
]

PATHWAYS = [
    Pathway(code="stroke", name="Možganska kap", frequency="vsak dan", games=[TRACE_GAME, CAMERA_GAME], questions=RATINGS),
    Pathway(code="ctr", name="Operacija karpalnega kanala", frequency="vsak dan",
            games=[TRACE_GAME, CAMERA_GAME], questions=RATINGS),
]

CLINICIANS = [Clinician(id="c1", name="dr. Ana Novak", role="zdravnica")]

# the patient selected when the app opens: the main demo story (slow decline)
DEFAULT_PATIENT_ID = "p3"


def fresh_pathways() -> list[Pathway]:
    return [Pathway(**p.model_dump()) for p in PATHWAYS]


def fresh_clinicians() -> list[Clinician]:
    return [Clinician(**c.model_dump()) for c in CLINICIANS]
