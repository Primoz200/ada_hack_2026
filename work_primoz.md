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
