# Tracer igra – specifikacija podatkov (v2, format `GameResult`)

Dogovor med frontendom (Matevž) in backendom/modeli (Primož). Isti format uporablja tudi generator sintetičnih podatkov.

## Pravila igre (kar vpliva na podatke)

- **Stopnje:** `line`, `circle`, `maze` – vedno iste oblike (fiksne, za primerljivost trenda čez dneve).
- **Ena roka**, **en poskus na stopnjo** na sejo.
- **Interakcija:** pacient pritisne in drži levi gumb miške (kasneje: prst na zaslonu) v začetni točki poti in sledi poti do konca.
  Spust gumba sredi poti je dovoljen, se pa zabeleži (nov `strokeId`).
- **Navodilo pacientu:** »Sledi poti čim natančneje, v svojem tempu.« Natančnost je glavni signal, čas sekundarni.
- **Konec poskusa:** ko kurzor (z držanim gumbom) doseže končno točko v radiju `channel_width / 2`
  in je pacient prevozil vsaj 90 % dolžine poti (preprečuje bližnjice, pomembno pri krogu, kjer sta začetek in konec ista točka).
  Poskus se prekine (`completed = false`), če poteče `time_limit_s` ali pacient klikne »Odneham«.
- **Pošiljanje:** ob koncu vsakega poskusa en `POST` na backend.

## Format: `GameResult` (iz IMPLEMENTATION_PLAN.md)

Frontend pošlje en `GameResult` na `POST /api/sessions`. Za sledenje:

```json
{
  "gameType": "trace",
  "level": 2,
  "hand": "right",
  "startedAt": "2026-11-21T15:02:11Z",
  "durationMs": 9120,
  "completed": true,
  "series": {
    "targetX":  [0.8, 0.7989, "..."],
    "targetY":  [0.5, 0.5261, "..."],
    "t":        [0, 16, 33, 50],
    "x":        [0.8, 0.79963, 0.79889, 0.79778],
    "y":        [0.5, 0.50412, 0.50831, 0.51259],
    "strokeId": [0, 0, 0, 0]
  },
  "clientMeta": { "inputDevice": "mouse", "canvasW": 800, "canvasH": 800, "devicePixelRatio": 1, "userAgent": "..." }
}
```

| Polje | Opis |
|---|---|
| `level` | 1 = `line`, 2 = `circle`, 3 = `maze` (polje `level` v `shared/tracer_levels.json`) |
| `durationMs` | od prvega pritiska do konca/prekinitve poskusa |
| `completed` | `true` = prišel do konca, `false` = časovna omejitev / »Odneham« |
| `series.targetX/Y` | pot stopnje iz `shared/tracer_levels.json`, deljeno s 1000 |
| `series.t` | ms od prvega pritiska, za **vsako** točko, naraščajoče |
| `series.x/y` | položaj na platnu, normaliziran **0–1** (lahko izven, če kurzor uide), izhodišče zgoraj levo, y navzdol |
| `series.strokeId` | poveča se ob vsakem spustu gumba / dvigu prsta |

## Zajem

- **Kvadratno platno**, pretvorba (nikoli ne pošiljamo pikslov):
  `x = (e.clientX - r.left) / r.width`, `y = (e.clientY - r.top) / r.height`.
- Pointer Events (`pointerdown/move/up`), `event.timeStamp`, dodatne točke iz `getCoalescedEvents()`.
  Pri miški se beleži samo med držanjem levega gumba.
- **Brez prevzorčenja ali glajenja na odjemalcu.** Ko kurzor miruje, ni dogodkov → postanek je vrzel v `t`.
  Model sam prevzorči na 50 Hz (znotraj potega vrzel = kurzor stoji, med potegi = gumb spuščen).
- Tipičen poskus: 5–60 s, nekaj sto do nekaj tisoč točk.

## Definicije stopenj

V `shared/tracer_levels.json` (bere ga frontend za izris in backend za izračun odstopanja):

```json
{ "level_id": "circle", "level": 2, "version": 1, "shape": "circle",
  "path": [[800.0, 500.0], [798.9, 526.1], "..."],
  "channel_width": 60, "time_limit_s": 30 }
```

- `path` = lomljena črta (polyline) v logičnih enotah; prva točka je začetek, zadnja konec. Pot se izriše kot kanal širine `channel_width`.
- `line`: vodoravna črta (100,500) → (900,500).
- `circle`: središče (500,500), polmer 300, začetek desno (800,500), smer v smeri urinega kazalca na zaslonu, točka na 5°.
- `maze`: kača (serpentina) s 4 vodoravnimi hodniki, začetek zgoraj levo, konec spodaj levo.
- Če se oblika stopnje spremeni, se poveča `version` (stari rezultati niso več neposredno primerljivi).

## Odgovor točkovanja (`score_session`)

`ScoreResult`: `score` (0–100), `impairment_class` ∈ `normal` / `mild` / `moderate` / `severe`
(pragi 85 / 65 / 40), `features` (npr. `dev_rms`, `pct_outside`, `duration_s`, `coverage`) in `model_version`.
Trend (`assess_trend`) teče ločeno po stopnji in vnosni napravi.

## Sintetični podatki

Generator (`backend/models/tracer/generator.py`) izpiše **enak `GameResult`**, z dodatnima poljema `id` in `label`
(frontend ju nikoli ne pošilja):

```json
"label": { "score": 72.4, "score_clean": 75.1, "impairment_class": "mild", "generator": { "base_speed": 180.2, "...": 0 } }
```

`score` = učna oznaka (z ±5 točk šuma), `score_clean` = latentna resnica (samo za evalvacijo).
