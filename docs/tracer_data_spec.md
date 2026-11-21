# Tracer igra – specifikacija podatkov (v1)

Dogovor med frontendom (Matevž) in backendom/modeli (Primož). Isti format uporablja tudi generator sintetičnih podatkov.

## Pravila igre (kar vpliva na podatke)

- **Stopnje:** `line`, `circle`, `maze` – vedno iste oblike (fiksne, za primerljivost trenda čez dneve).
- **Ena roka**, **en poskus na stopnjo** na sejo.
- **Interakcija:** pacient pritisne in drži levi gumb miške (kasneje: prst na zaslonu) v začetni točki poti in sledi poti do konca.
  Spust gumba sredi poti je dovoljen, se pa zabeleži (`down = 0`).
- **Navodilo pacientu:** »Sledi poti čim natančneje, v svojem tempu.« Natančnost je glavni signal, čas sekundarni.
- **Konec poskusa:** ko kurzor (z držanim gumbom) doseže končno točko v radiju `channel_width / 2`
  in je pacient prevozil vsaj 90 % dolžine poti (preprečuje bližnjice, pomembno pri krogu, kjer sta začetek in konec ista točka).
  Poskus se prekine (`completed = false`), če poteče `time_limit_s` ali pacient klikne »Odneham«.
- **Pošiljanje:** ob koncu vsakega poskusa en `POST` na backend.

## Koordinatni sistem

- Logične enote **0–1000** v obeh oseh, izhodišče **zgoraj levo**, y raste **navzdol**.
- Igralno polje (canvas) je kvadratno, pomanjšano/povečano na zaslon z ohranjenim razmerjem.
- Pretvorba v frontendu (nikoli ne pošiljamo pikslov zaslona):

```js
const r = canvas.getBoundingClientRect();
const x = (e.clientX - r.left) / r.width  * 1000;
const y = (e.clientY - r.top)  / r.height * 1000;
```

## Vzorčenje

- Vzorčenje v zanki `requestAnimationFrame` (~60 Hz): vsak frame zapiše **zadnji znani položaj kurzorja** (iz `pointermove`),
  tudi če se miška ne premika – tako se vidijo postanki.
- `t` = milisekunde od začetka poskusa (`performance.now() - startTime`), za **vsak** vzorec – frekvenca ni zanesljivo konstantna,
  backend prevzorči sam.
- Snemanje se začne ob prvem pritisku gumba v začetni točki in konča ob koncu/prekinitvi poskusa.
- Uporabljati **Pointer Events** (`pointerdown/move/up`), da isto deluje za miško in dotik.

## Format poskusa (POST body)

```json
{
  "patient_id": "p_001",
  "level_id": "circle",
  "started_at": "2026-11-21T15:02:11Z",
  "completed": true,
  "samples": {
    "t":    [0, 16, 33, 50],
    "x":    [800.0, 799.6, 798.9, 797.8],
    "y":    [500.0, 504.1, 508.3, 512.6],
    "down": [1, 1, 1, 1]
  },
  "device": {
    "pointer_type": "mouse",
    "canvas_css_px": 900
  }
}
```

| Polje | Tip | Obvezno | Opis |
|---|---|---|---|
| `patient_id` | string | da | ID pacienta (za trend) |
| `level_id` | string | da | `line` / `circle` / `maze` (iz `shared/tracer_levels.json`) |
| `started_at` | ISO 8601 UTC | da | čas začetka poskusa |
| `completed` | bool | da | `true` = prišel do konca, `false` = časovna omejitev / odnehal |
| `samples.t` | int[] | da | ms od začetka poskusa, naraščajoče |
| `samples.x`, `samples.y` | float[] | da | logične enote 0–1000 (lahko izven polja, če kurzor uide) |
| `samples.down` | 0/1[] | da | ali je gumb/prst pritisnjen |
| `device.pointer_type` | string | ne | `mouse` / `touch` / `pen` (iz `PointerEvent.pointerType`) |
| `device.canvas_css_px` | int | ne | velikost canvasa v CSS pikslih (za zaznavo menjave naprave) |

Vsi štirje nizi v `samples` morajo biti enako dolgi. Tipičen poskus: 10–30 s × 60 Hz ≈ 600–1800 vzorcev (~20–50 KB JSON).

## Definicije stopenj

V `shared/tracer_levels.json` (bere ga frontend za izris in backend za izračun odstopanja):

```json
{ "level_id": "circle", "version": 1, "shape": "circle",
  "path": [[800.0, 500.0], [798.9, 526.1], "..."],
  "channel_width": 60, "time_limit_s": 30 }
```

- `path` = lomljena črta (polyline) v logičnih enotah; prva točka je začetek, zadnja konec. Pot se izriše kot kanal širine `channel_width`.
- `line`: vodoravna črta (100,500) → (900,500).
- `circle`: središče (500,500), polmer 300, začetek desno (800,500), smer v smeri urinega kazalca na zaslonu, točka na 5°.
- `maze`: kača (serpentina) s 4 vodoravnimi hodniki, začetek zgoraj levo, konec spodaj levo.
- Če se oblika stopnje spremeni, se poveča `version` (stari rezultati niso več neposredno primerljivi).

## Odgovor backenda

```json
{
  "score": 78,
  "class": "mild",
  "features": { "rms_dev_pct": 14.2, "duration_s": 9.1, "pct_outside": 3.5 },
  "trend": { "baseline": 82, "z": -1.3, "flag": false }
}
```

`class` ∈ `normal` / `mild` / `moderate` / `severe`. `trend` je `null`, dokler pacient nima dovolj sej za izhodišče (2–3).

## Sintetični podatki

Generator izpiše **enak format** poskusa, z dodatnim poljem `label` (frontend ga nikoli ne pošilja):

```json
"label": { "severity": "mild", "score": 74, "generator": { "speed_factor": 0.8, "lateral_noise": 12.0, "tremor_hz": 0 } }
```
