# Work log — matevz

## 2026-11-21 — Pregled načrtov, raziskava platforme, osnutek implementacijskega načrta

**Narejeno:**
- Pregledan repo (kode še ni; PLAN.md, RESEARCH.md, work_primoz.md) in Ixtlanov PDF z navodili izziva.
- Deep research platforme (6 sklopov): AdaHack/Ixtlan, obstoječe platforme, zdravniški pogled, pacientov pogled, Slovenija in regulativa, tehnična arhitektura. Zapiski v `research_notes/Platforma za spremljanje pacientov po odpustu/`, poročilo v `reports/`.
- Osnutek `IMPLEMENTATION_PLAN.md` (obseg, arhitektura, vmesnik iger, podatkovni model, API, pravila opozoril, zasloni, sintetični pacienti, časovnica, pitch).

**Odločitve (Matevž):**
- Scenarij: stanja s tveganjem za poslabšanje motorike; v pitchu kap (pogosti pregledi) in karpalni kanal (redki pregledi).
- Vlogi v prototipu: pacient in zdravnik; svojci niso prioriteta.
- Pacient poroča z igrami + kratkim dnevnim vnosom. Demo raven (preklop vlog, SQLite, sintetični pacienti).
- Frontend React, vmesnik v slovenščini, igre kot komponente v istem frontendu. Pitch 2–3 min.

**Ključno naučeno:**
- Ixtlan Team dela zVEM in zVEM+; ocenjujejo družbeni vpliv, inovativnost, predstavitev, kodo/demo. Subjektivni dejavniki so kriterij inovativnosti; rešitev ne sme diagnosticirati; čas osebja je omejen.
- Uradna časovnica: konec kodiranja v nedeljo ob 11.00 ("No more commits!"), demo 13.00–15.00, 3 min na odru. Preveriti pri organizatorjih.
- Priporočen sklad: Vite + React 19 + Tailwind 4 + shadcn + Recharts 3; FastAPI + SQLModel + SQLite; en izvor. Brez @tremor/react (ne podpira React 19).

**Odprto:** poglavje 12 v IMPLEMENTATION_PLAN.md (kdo dela platformni backend, rok, igra s telefonom, gostovanje, LLM povzetek, prag opozoril).
**Naslednji korak:** uskladiti vmesnik iger s Primožem (poglavje 5), nato ogrodje repozitorija.

## 2026-11-21 (16.30) — Načrt v3

**Odločitve (Matevž):**
- Pacientov del teče na telefonu (brskalnik, dotik); igra sledenja se igra s prstom. Beležijo se trajanje testa, želena črta in dejanska sled s časi; platforma surove podatke shrani in jih z vso zgodovino posreduje modelu, ki pokaže trend.
- Delitev potrjena: Primož igre, modeli in točkovanje; Matevž platforma (backend + frontend).
- Lokalni demo zadošča. Za povzetek sta na voljo ključa za Azure OpenAI Responses API. Codeplainovega izziva ne rešujeva.

**Spremembe v IMPLEMENTATION_PLAN.md:** vmesnik iger (poglavje 5) z obliko podatkov sledenja in funkcijama `score_session` + `assess_trend`; telefon v lokalnem demu (poglavje 3); posodobljene odprte točke (poglavje 12).
**Ključno naučeno:** kamera in gibalni senzorji v brskalniku delujejo samo prek HTTPS ali localhost, sledenje s prstom pa tudi prek navadnega HTTP v lokalnem omrežju.
**Naslednji korak:** Primož potrdi poglavje 5 in odprte točke 2–6; nato ogrodje repozitorija.

## 2026-11-21 (16.40) — Načrt v4

**Odločitve (Matevž):**
- Dema v živo ne bo; platformo posnameva sama (slike zaslona, kratek video) in posnetke vključiva v predstavitev.
- Testov z miško ni; vlečenje je izključno s prstom na telefonu.

**Ključno naučeno:** `vite --host` zadošča za dotik, kamera na telefonu pa zahteva varen kontekst (HTTPS ali localhost). Rešitev: `@vitejs/plugin-basic-ssl` + Vite proxy za `/api`; alternativi `adb reverse` (Android) ali tunel.
**Spremembe v IMPLEMENTATION_PLAN.md:** poglavje 3 (telefon, HTTPS, zajem), poglavje 5 (samo dotik), poglavje 12 (odprte točke), poglavje 13 (predstavitev s posnetki in seznam posnetkov).

## 2026-11-21 (16.45) — Načrt v5

**Odločitve (Matevž):**
- Testi s kamero: telefon naslonjen na mizi (knjiga, skodelica), snema sprednja kamera, pacient se vidi na zaslonu.
- Platforma med predstavitvijo ni odprta; funkcionalnost se pokaže v PowerPointu ali na statični spletni strani s posnetki.

**Spremembe v IMPLEMENTATION_PLAN.md:** poglavje 5 (postavitev za teste s kamero, značilke neodvisne od naklona, mera kakovosti kadra), poglavji 12 in 13.

## 2026-11-21 (17.45) — Oblikovalski skilli

**Spremembe:** v `.claude/skills/` ustvarjeni simbolni povezavi `impeccable` in `hallmark` → `.agents/skills/…`, da sta skilla na voljo tako v Codexu kot v Claude Code (`/impeccable`, `/hallmark`).
**Ključno naučeno:** Claude Code bere skille iz `.claude/skills`, Codex iz `.agents/skills`; simbolna povezava odpravi podvajanje. Zaganjalnik skilla impeccable ob prvi uporabi prenese binarno datoteko.

## 2026-11-21 (18.45) — Ogrodje platforme in orkestracija agentov (branch `matevz/platform`)

**Odločitve (Matevž):**
- Vso kodo platforme in ves frontend (tudi igro sledenja) implementira Matevž z agenti; Primož prispeva raziskavo, kontekst in ML modele v backendu. `IMPLEMENTATION_PLAN.md` posodobljen na v7.
- Obseg tega zagona: jedro (poglavje 2) + »Simuliraj naslednjih 7 dni«. Igra s kamero ni vključena.
- Način dela: Fable orkestrira, Sonnet agenti v ločenih worktreejih gradijo neodvisne komponente.

**Narejeno (faza 0, commit `f7fe053`):**
- `backend/`: FastAPI + SQLModel, tabele (`app/models/tables.py`), pogodba API v camelCase (`app/models/schemas.py`), routerji, podpisi storitev (`scoring`, `trend`, `alerts`, `ingest`, `clock`, `divergence`), majhen razvojni seed, dimni test.
- `contracts/openapi.json` + `scripts/gen_contract.sh` (izvoz in generiranje TS tipov, `--check` za odstopanje pogodbe), `scripts/dev.sh`.
- `frontend/`: Vite + React 19 + Tailwind 4 + shadcn + Recharts, vse poti registrirane, tipiziran odjemalec API, vmesnik iger (`games/shared/types.ts`), register iger, nadomestna igra.
- Navpični rez deluje prek Vite proxyja (HTTPS): seja se shrani in vrne v časovnici.

**V teku (faza 1, vzporedno):** pisalna pot (točkovanje, trend, opozorila), bralna pot (seznam za triažo, danes, napredek), pacientov vmesnik + igra sledenja, zdravnikov vmesnik. Sledi seed z 10 pacienti + simulacija, nato integracija.

**Ključno naučeno:**
- Python pripet na 3.12 z `uv` (sistemski je 3.15). SQLModel 0.0.50 zahteva časovne žige s časovnim pasom (UTC).
- `openapi-typescript` zahteva TypeScript 5, aplikacija uporablja 7, zato se generator zažene zunaj projekta z `npx -p typescript@5`.
- Kamera na telefonu: Vite teče s samopodpisanim HTTPS (`@vitejs/plugin-basic-ssl`), `/api` gre prek proxyja.

## 2026-11-21 (19.45) — Platforma zgrajena z agenti in integrirana (branch `matevz/platform`)

**Narejeno:** pet Sonnet agentov v worktreejih (pisalna pot, bralna pot, pacientov vmesnik + igra sledenja, zdravnikov vmesnik, seed + simulacija), vse združeno. Jedro iz poglavja 2 + »Simuliraj naslednjih 7 dni« deluje.
- Backend: točkovalnik z adapterjem za Primožev model (`models.tracer.score.score_session`, sicer nadomestni), trend (izhodišče = mediana sej 2–4, EWMA 0,3, skupni trend), opozorila (rdeča / rumena / siva, eno odprto na pacienta, zaprtje samo z izidom), 10 determinističnih pacientov, ponastavitev in simulacija. 96 testov.
- Frontend: Danes, dnevni vnos, igra sledenja (prst ali miška), Moj napredek; zdravnikov seznam za triažo in pogled pacienta z grafi, predvajanjem seje in zaprtjem opozorila. 30 testov.
- `DEMO.md`: zagon, telefon, kontrole za demo.

**Preverjeno v brskalniku (headless Chrome):** igra z miško od začetka do rezultata, zaprtje opozorila z izidom, seznam in pogled pacienta 3 s pravimi podatki; simulacija 7 dni pri demo pacientu sproži rumeno opozorilo.
**Ni preverjeno:** dotik na pravem telefonu prek HTTPS.

**Ključno naučeno:**
- Agentovi worktreeji so nastali iz starejšega commita; vsak agent je moral najprej narediti fast-forward na `matevz/platform`. V navodilih agentu to zahtevaj izrecno.
- React StrictMode v razvoju komponento priklopi dvakrat; platno igre je ostalo prazno, ker se ID animacijskega okvira ob odklopu ni ponastavil.
- Baza se ob vsakem zagonu backenda ponastavi (`APP_KEEP_DB=1` jo ohrani); »danes« po simulaciji živi samo v pomnilniku.
- Telefonska številka ambulante v pacientovem delu je nadomestna (`features/patient/shared.tsx`).

**Odprto:** preizkus na telefonu; Primožev model (vmesnik v `scoring.py`); igra s kamero in ostali dodatki iz poglavja 2 niso narejeni.
