# Work log — primoz

## 2026-11-21 — Grilling + raziskava iger

**Odločitve (grilling):**
- MVP: spletna stran z miško; telefon (touch, senzorji gibanja) kasneje.
- 3 igre različnih tipov: (1) sledenje/risanje (tracing), (2) računalniški vid z MediaPipe (zgornji ali celo telo), (3) tretja – izbrana glede na dokaze, enostavnost in "wow" faktor (kandidat: senzorji gibanja telefona).
- Cilj: spremljanje napredka/regresije pacienta; igre hkrati pomagajo pri okrevanju.
- Podatki: pretežno sintetični (generirani po pravilih za naše igre), javni podatki če obstajajo.
- Modeli: vsaj eden na igro; izhod = ocena 0–100 + razred okvare (normal/blaga/zmerna/huda), nivo kot vhod; trend čez dneve izračunan nad ocenami.
- Vhod modelov: x/y statistike, koti med udi (CV), čas → baseline (ročne značilke) + 1D-CNN.
- Stack: Python FastAPI backend. Matevž: spletna stran. Primož: modeli.

**V teku:** deep research (5 vzporednih raziskav) → `RESEARCH.md` (slovensko, z linki/DOI) + povzetek v `PLAN.md`.

**Opravljeno:** deep research končan. `RESEARCH.md` (≈10k besed, slovensko, ~190 virov z linki/DOI; kopija v `reports/`, zapiski v `research_notes/`). Povzetek dodan v `PLAN.md`.
**Ključno naučeno:** ni javnih podatkov za kap/CTR/CIPN pri takih igrah → sintetika + trend glede na lastno izhodišče; validiranega testa na miško ni (MVP je prilagoditev); iOS senzorji rabijo requestPermission + HTTPS.
**Naslednji korak:** generator sintetičnih podatkov za igro 1 (tracing) + baseline model.

## 2026-11-21 — Odločitev o igrah za MVP

**Obseg MVP:** samo 2 igri – (1) tracer igra (en NN model za vse stopnje/oblike, ker so si podobne), (2) igra z računalniškim vidom (MediaPipe). Tretje igre (telefon/senzorji) zaenkrat ni.

**CV igra – 3 vaje:**
1. **Odpiranje/zapiranje dlani** (pest → razprti prsti) – MediaPipe Hands. Metrika: povprečna razdalja konic prstov do zapestja / velikost dlani → razpon, hitrost, št. ponovitev, gladkost, razlika levo/desno. Izvaja se v ritmu (~1 Hz) + »odpri čim bolj«, NE na maksimalno hitrost (webcam ~15–30 fps, motion blur).
2. **Abdukcija ramen (roke v stran)** – MediaPipe Pose, frontalna kamera. Metrika: kot kolk–rama–komolec (% lastnega izhodišča), nagib trupa (kompenzacija), simetrija L/D, gladkost. Najbolje validiran kot (ICC 0,86–0,96).
3. **Dvig rok čim višje** – MediaPipe Pose. Pozor: dvig naprej (fleksija) je za eno kamero problematičen (globina). Zato meriti **višino zapestja nad ramo, normalizirano z dolžino trupa** (2D, neodvisno od globine), ne kota ramena; + nagib trupa / dvig na prste kot kompenzacija, simetrija.

**Modeli za CV:** vaje imajo različne landmarke (Hands vs Pose) → verjetno 2 modela (dlan, roke) ali en model s tipom vaje kot vhodom. Vhod: normalizirane relativne vrednosti in koti (% izhodišča).

**Tehnične opombe:** v vsaki seji meriti dejanski fps (timestampi), pod ~20 fps opozorilo/nizka kakovost; uporabljati timestampe in prevzorčiti na 30 Hz; v sintetičnem generatorju simulirati 15–30 fps z jitterjem, izpadi sličic in šumom landmarkov.

**Naslednji korak:** generator sintetičnih podatkov za tracer igro + baseline model.

## 2026-11-21 — Tracer: specifikacija podatkov (branch `tracer-synthetic-data`)

- Napisan `docs/tracer_data_spec.md` (format poskusa: patient_id, level_id, started_at, completed, samples t/x/y/down v logičnih enotah 0–1000, ~60 Hz rAF) in `shared/tracer_levels.json` (line, circle, maze; kanal 60 enot).
- Odločitve: fiksne oblike, ena roka, en poskus na stopnjo, držanje gumba, natančnost glavni signal, POST po vsakem poskusu.
- Naslednji korak: generator sintetičnih podatkov v istem formatu + `label`.
