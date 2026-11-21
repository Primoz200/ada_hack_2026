"""Recovery pathways as configuration (plan sections 1, 8, 9). A new condition is a
new entry here, not new code. Warning-sign wording must be confirmed by a clinician.
"""
from app.models import Clinician, Pathway

TRACE_GAME = {"gameType": "trace", "title": "Sledi poti", "levels": [1, 2, 3]}

PATHWAYS = [
    Pathway(
        code="stroke",
        name="Možganska kap",
        frequency="vsak dan",
        games=[TRACE_GAME],
        questions=[
            {"id": "arm_function", "kind": "faces5", "text": "Kako je danes delala vaša prizadeta roka?",
             "min": 1, "max": 5, "minLabel": "Zelo slabo", "maxLabel": "Zelo dobro", "higherIsWorse": False},
            {"id": "fatigue", "kind": "scale", "text": "Kako utrujeni ste danes?",
             "min": 0, "max": 4, "minLabel": "Nič", "maxLabel": "Zelo", "higherIsWorse": True},
            {"id": "fall", "kind": "yes_no", "text": "Ste od včeraj padli?",
             "min": 0, "max": 1, "higherIsWorse": True},
        ],
        warning_signs=[
            {"id": "face", "text": "Povešen obraz", "action": "call_112"},
            {"id": "limb", "text": "Šibka ali omrtvela roka ali noga", "action": "call_112"},
            {"id": "speech", "text": "Težave z govorom", "action": "call_112"},
            {"id": "vision", "text": "Nenadna izguba vida", "action": "call_112"},
            {"id": "headache", "text": "Zelo hud glavobol", "action": "call_112"},
        ],
        muted_patterns=[],
    ),
    Pathway(
        code="ctr",
        name="Operacija karpalnega kanala",
        frequency="vsak dan",
        games=[TRACE_GAME],
        questions=[
            {"id": "pain", "kind": "scale", "text": "Kako močna je zdaj bolečina v roki?",
             "min": 0, "max": 10, "minLabel": "Brez bolečine", "maxLabel": "Najhujša", "higherIsWorse": True},
            {"id": "tingling", "kind": "scale", "text": "Kako močno je mravljinčenje ali omrtvelost prstov?",
             "min": 0, "max": 4, "minLabel": "Nič", "maxLabel": "Zelo močno", "higherIsWorse": True},
            {"id": "night_wakings", "kind": "count", "text": "Kolikokrat so vas simptomi ponoči zbudili?",
             "min": 0, "max": 3, "maxLabel": "3 ali več", "higherIsWorse": True},
        ],
        warning_signs=[
            {"id": "wound_red", "text": "Roka je rdeča, vroča, bolj otekla ali bolj boleča", "action": "call_clinic"},
            {"id": "discharge", "text": "Izcedek iz rane ali razprta rana", "action": "call_clinic"},
            {"id": "fever", "text": "Vročina", "action": "call_clinic"},
            {"id": "new_numbness", "text": "Nova omrtvelost", "action": "call_clinic"},
        ],
        # expected early pattern: pain on grip in the first weeks does not alert on its own
        muted_patterns=[{"question": "pain", "untilDay": 21, "maxValue": 5}],
    ),
]

WARNING_PROMPTS = {
    "stroke": "Ali je od včeraj kaj novega in nenadnega?",
    "ctr": "Ali opažate kaj od naštetega?",
}

CLINICIANS = [Clinician(id="c1", name="dr. Ana Novak", role="zdravnica")]


def fresh_pathways() -> list[Pathway]:
    return [Pathway(**p.model_dump()) for p in PATHWAYS]


def fresh_clinicians() -> list[Clinician]:
    return [Clinician(**c.model_dump()) for c in CLINICIANS]
