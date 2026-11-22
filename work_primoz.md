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

## 2026-11-21 — Tracer generator v2 + uskladitev z IMPLEMENTATION_PLAN

- `IMPLEMENTATION_PLAN.md` (na main): stopnje 1=line, 2=circle, 3=maze iz `shared/tracer_levels.json`; kvadratno platno (0–1 normalizacija); trend ločeno po igri+stopnji+vnosu; miška dovoljena za MVP/demo (`inputDevice: touch|mouse|camera`).
- Generator v2: odstopanje samo pravokotno na pot (tremor + OU "stock chart" jitter, brez zank); primer grafa `models/data/tracer_samples.jpg`. corr(score, rmsdev) = −0.93.
- Opombe za model: hitrost meriti kot napredek vzdolž poti (surova hitrost kurzorja pri hudi okvari zaradi jitterja naraste).
- **Odprto:** `docs/tracer_data_spec.md` in generator še nista prestavljena na format `GameResult` iz plana (series: targetX/targetY/t/x/y/strokeId, 0–1, `level` 1–3, surovi dogodki z vrzelmi namesto fiksnih 60 Hz).
- **Naslednji korak:** nevronska mreža za tracer (baseline na značilkah + 1D-CNN, izhod score 0–100 + razred, stopnja kot vhod).

## 2026-11-21 — Tracer: GameResult format + prva modela

- `models/` prestavljen v **`backend/models/`**. Venv zdaj v `~/venvs/ada_models` (na /mnt/c je namestitev torcha prepočasna); RTX 5050 + torch 2.11 cu128 dela.
- Generator izpisuje **`GameResult`** (level 1–3, series targetX/targetY/t/x/y/strokeId v 0–1, točke samo med držanjem gumba, postanek = vrzel v `t`, snap na piksle). Dodan osebni slog (hitro & nenatančno ↔ počasi & natančno) in šum oznake ±5 točk (`score` = učna, `score_clean` = resnica). `shared/tracer_levels.json` ima polje `level`. Spec `docs/tracer_data_spec.md` → v2.
- Nove datoteke: `common.py` (pragi 85/65/40, metrike), `features.py` (prevzorčenje 50 Hz + 20 značilk + zaporedje za CNN; uporabi ga tudi `score_session`), `dataset.py` (cache), `train_baseline.py`, `train_cnn.py`. 9000 poskusov (3000/stopnjo), split 70/15/15.
- Rezultati (test, MAE proti resnici): **GBM 6,45**, razred 78 %; **CNN 6,85**, razred 78 %; nobeden ne zgreši za več kot 1 razred. CNN se preprilega (train loss 1,2). Pričakovano: na sintetiki so ročne značilke skoraj vse, kar generator vsebuje.
- Naslednje: odločitev, kaj gre v backend (GBM / CNN / povprečje), `score_session`, snemalnik za realne poskuse.
- Primerjava velikosti CNN (graf `backend/models/data/tracer_training.jpg`, skripta `plot_training.py`): Dropout1d v konvolucijah odpravi preprileganje; manjše mreže (širina 32/16/8, dropout 0,3) se podprilegajo. Privzeto zdaj širina 64, dropout 0,1 → test MAE 6,76 (GBM 6,45). Nadaljnje izboljšave (daljši trening, povprečje GBM+CNN) počakajo na realne podatke.
- `score_session` (povezava backend ↔ model) bo verjetno naredil Matevž; vse potrebno je v `features.py` (preprocess, extract_features), `common.py` (score_to_class) in `artifacts/` (tracer_gbm.joblib, tracer_cnn.pt). Venv: `~/venvs/ada_models`.
- **Naslednji korak:** model za CV igro (MediaPipe: odpiranje dlani, abdukcija ramen, dvig rok).

## 2026-11-21 — CV igra: snemalnik + točkovanje s pravili (branch `compvis`)

- **Odločitev:** za kamero **ni modela ne sintetike**. Posnameva pravilne gibe (referenca), posnetek »pacienta« se oceni s pravili kot % reference (0–100, pragi 85/65/40). Točkovanje samo v backendu (Python), v brskalniku samo zajem + izris točk.
- Vaje: 1 odpiranje/zapiranje dlani v ritmu piska 1 Hz (razpon odpiranja + časovna usklajenost s piski), 2 roke v stran, 3 dvig rok (razpon nad lastnim mirovanjem, št. ponovitev, kazen za nagib trupa in dvig rame).
- `backend/models/camera/`: `server.py` (FastAPI, shrani posnetek + video, točkuje, gradi referenco), `recorder/` (vanilla JS + MediaPipe Tasks 1.2.3, lokalno iz `vendor/`), `exercises.py`, `signals.py`, `scoring.py` (`score_camera` – isti podpis kot `score_session`), `build_reference.py`, `plot_recording.py`, `README.md`.
- Posnetki gredo v `backend/models/data/camera/recordings/` (gitignored); shranjeni so surovi landmarki + `.webm`, zato lahko značilke kasneje spremeniva brez ponovnega snemanja.
- Za Matevža: predlagan `gameType "camera"` + `level` 1–3 (v planu sta še `camera_tapping`/`camera_reach`) – uskladiti.
- **Naslednji korak:** posneti reference (≈3 na vajo in roko), nato nekaj namerno slabših posnetkov in nastaviti uteži.
- **Točkovanje v0.2 (`camera-rules-0.2`)** na referencah (dlan 2× D + 1× L, roke v stran 2×, dvig 1×; časi: dlan pisk = odprta, 3 s cikel; roke 4 s gor / 4 s dol). Pozicija je glavno, čez referenco ni kazni, ritem se ne točkuje (samo število ponovitev). Dlan iz **3D world landmarkov** (2D je nagnjeno pest kazal kot napol odprto). Dlan: √(odpri × stisni); roke: vrh ponovitve med zdravim mirovanjem in vrhom, kazen za nagib trupa (do 20 %) in dvig rame (do 10 %).
- `validate_scoring.py`: leave-one-out 96–100; degradirani zdravi posnetki → 40 % giba ≈ 60, 75 % ≈ 85; hitreje / izpad sličic / šum ne spremeni ocene. Graf `data/camera/plots/score_validation.jpg`.
- **Naslednje:** preizkus na pravih »pacientih« prek Matevževe strani; po potrebi še posnetki dviga rok in leve dlani (referenca dviga ima n=1).
- **v0.3 (strožje):** pri dlani je bil razpon preblag (delni gibi niso padli pod ~50). Dodan `ZERO_AT` – polovica zdravega giba dlani (četrtina pri rokah) = 0 točk, linearno do 100. Testni posnetki: delna pest 78 → 58, slabše odpiranje + zapiranje 83 → 68, brez giba 21 → 0; zdravi ostanejo 92–100.

## 2026-11-21 (pozno) — Turri: backend iz ***plain specifikacije (izziv Codeplain)

- **Kaj:** celoten `backend/app` (brez `backend/models/`) zgrajen s turri iz specifikacije `turri/backend.plain` (16 funkcionalnih specifikacij, 8 datotek s scenariji za black-box teste, lastni skripti za teste v `turri/test_scripts/`). Modeli: OpenAI GPT na Amazon Bedrock (`gpt-6-astra` načrtuje, `gpt-6-luna` piše kodo). Ključ je zunaj repozitorija v `~/.config/turri/bedrock.env`, nalaga ga `turri/run.sh`.
- **Kje:** veja `turri-build` (worktree `.claude/worktrees/turri`), izvoz kode v `backend_turri/`. Turri teče na Linux strani v `~/ada-turri` (na `/mnt/c` bi bil `uv sync` prepočasen).
- **Potek:** 1. zagon: koraki 1–7 uspešni, korak 8 (replay zgodovine) padel na 120 s limitu, ker je vsak unit test na novo predvajal celo zgodovino → v specifikacijo dodan `APP_SEED_HISTORY=0` za teste, limit 600 s. 2. zagon: vse zgrajeno, conformance testi zeleni.
- **Primerjava s starim backendom** (54 GET odgovorov pri `APP_TODAY=2026-11-21`, skripte v `~/ada-orig/`): seznam pacientov, poti, ocene, trendi in večina opozoril enaki; agent pa si je izmislil imena polj za home/summary/progress (kljub povezanemu openapi.json) → v specifikacijo vpisana točna polja, okna tednov, vrstni red sprožilcev, semena RNG. 3. zagon teče.
- **Naučeno:** turri bere samo to, kar je eksplicitno v pravem razdelku; povezan vir (openapi) ni dovolj za imena polj. Popravke delam v `.plain`, nikoli v generirani kodi; turri regenerira le spremenjene specifikacije.
- **Rezultat (6 zagonov turri, ~2 h):** generirani backend (`backend_turri/`) se pri `APP_TODAY=2026-11-21` ujema s ročno pisanim v **54/54 GET odgovorih** (polje za polje). Unit testi 55/55, conformance testi 20/20 (scenariji v `turri/tests/backend/`, generirani testi v `turri/conformance_tests/`), ruff + mypy čisti. Smoke test z zgrajenim frontendom: SPA, samopregled demo pacienta, točkovanje z mojim tracer modelom (`tracer-gbm-0.1`) delujejo.
- Zagon: `cd backend_turri && APP_MODELS_DIR=../backend/models uv run uvicorn app.main:app --port 8000`. Zamenjava `backend/app` še ni narejena: počaka na dogovor z Matevžem (integracija kamere).

## 2026-11-22 (noč) — Turri: Matevževe vaje s kamero prenesene v generirani backend

- `origin/main` (Matevževa integracija kamere, `181d29d`) zlit v `turri-build`; njegov ročni `backend/app` služi samo kot referenca za primerjavo, vsa nova koda je generirana s turri iz `turri/backend.plain`.
- **Krog A (najpomembnejše):** igra `camera` v poteh in korakih samopregleda (stopnji 2, 3 preskočljivi, kamera nikoli ne blokira zaključka), `GET /api/camera/exercises`, točkovanje s pravili prek `backend/models/camera` (`quality_ok`, `part_*` značilke, brez nadomestka), ločeni trendi po igri, `cameraSparkline`, `games` v povzetku in napredku. **Krog B:** opozorila, razhajanje in povratna informacija po igri (sprožilci z `game`, stavki po igrah, `evidence.games`, utišanje po (pravilo, igra)). **Krog C:** zgodovina vaj s kamero v demu (krivulje zgodb, preskoki, p2 lažni alarm).
- **Rezultat (zagoni 7–13):** primerjava z Matevževim backendom pri `APP_TODAY=2026-11-21`: **70/70 odgovorov enakih** (vsi zasloni, opozorila, 15 pravih posnetkov kamere z istimi ocenami in značilkami). Unit testi 67/67, conformance 30/30 (tudi pravi posnetki: 57,7 / 100 / 56,2 / slaba kakovost → brez ocene), ruff + mypy čisti. Smoke test z novim frontendom (kamera) brez napak.
- **Naučeno:** agent prepiše povezane Python vire po svoje (izgubil je parametre zgodb) in ignorira »kopiraj dobesedno« ali SHA zahtevo; deluje šele, ko so dejstva izrecno v specifikaciji (krivulje, šum, preskoki po zgodbi). Turrijev conformance krog je sam našel in popravil napako s stopnjo vaje.
- Izklopljen spanec ob zaprtem pokrovu (powercfg: lid AC/DC = nič, standby/hibernate AC = 0). Vrnitev: Nadzorna plošča → Možnosti napajanja, ali `powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 1`.
- Odprto: zamenjava `backend/app` z `backend_turri` (dogovor z Matevžem); po zamenjavi spremembe samo prek `backend.plain`.
