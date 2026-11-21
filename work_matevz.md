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
