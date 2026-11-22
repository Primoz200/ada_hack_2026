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

## 2026-11-21 (20.15) — Primožev model vklopljen, zadnji pregled v brskalniku

- Združen `origin/main` (Primož: `backend/models/tracer` z naučenim GBM in CNN). Nov most `backend/app/services/tracer_model.py`: seje v živo točkuje `tracer-gbm-0.1`; ob napaki nadomestni točkovalnik. Dodana `scikit-learn` in `joblib`.
- V brskalniku (headless Chrome, simulirani dogodki) preverjeno: vse tri stopnje igre (dotik in miška), dnevni vnos do »Poslano vašemu zdravniku«, celozaslonski »Takoj pokličite 112«, zaprtje opozorila z izidom, simulacija 7 dni po seji v živo še vedno sproži rumeno opozorilo.
- Popravki: prazno platno igre v razvojnem načinu, podvojen naslov na zaslonu 112, razlog v seznamu po zaprtju opozorila, bolj gladke sintetične sledi, imena značilk usklajena s Primoževim modelom.
- `vite.config.ts`: cilj proxyja se nastavi z `API_URL` (privzeto `http://localhost:8000`).

## 2026-11-21 (22.15) — Redesign v8: samopregled, opozorila samo pri zdravniku, videz po zVEM

**Odločitve (Matevž):** pacient nikoli ne dobi poziva h klicu in ne vidi alarmov; desktop first; pristajalna stran je pacientov pogled z izbirnikom pacienta levo zgoraj in preklopom na zdravnika desno zgoraj; pacient ima samo »Samopregled« (počutje + bolečina 1–10, nato tri igre sledenja; računalniški vid, ko ga Primož konča) in »Moj napredek«; »Simuliraj 7 dni« odstranjen; slab test v živo sproži opozorilo; »Nujno« = igra in počutje padata hkrati.
**Način dela:** Fable orkestrira, trije agenti Opus (high) v worktreejih: backend, pacient, zdravnik. Oblikovanje s skillom impeccable; `PRODUCT.md` in `DESIGN.md` sta skupni oblikovni dogovor (po posnetkih zVEM: bela glava, modro-siva podlaga, veliki beli paneli, skrilasto modra, zelen poudarek, rdeč glavni gumb, Hanken Grotesk).

**Narejeno:**
- Pogodba v8 (`schemas.py`): `CheckinIn {wellbeing, pain}`, `/patients/{id}/home`, `/selfcheck/summary`, preprostejši `/progress`; brez opozorilnih znakov, skrbi, sporočil in simulacije.
- Pravila opozoril: `trend_drop` (danes ≤ −10 in 2 od prejšnjih 3 dni ≤ −5), `subjective_drop`, rdeča `both` / `big_drop`, siva `no_data`. Skupni trend upošteva tudi stopnje, ki danes še niso odigrane (z zadnjo vrednostjo).
- Mirna pacientova sporočila (`services/feedback.py`), brez številk; test preveri prepovedane besede.
- Novi sintetični pacienti: Ivan Zupan (p3) tri tedne okreva, nato pada 0,85 točke na dan, ob ponastavitvi −8,6 brez opozorila, pregled čez 30 dni.
- Pacient: Domov, čarovnik Samopregled, rezultat z mini grafom, Moj napredek. Zdravnik: vrstica = oznaka + ime + krivulji, poenostavljen okvir opozorila, poudarjen naslednji pregled, predvajanje sej ostane.

**Preverjeno v brskalniku s pravim backendom (headless Chrome, simulirana miška):** površen samopregled pri Ivanu (ocene 53 / 51 / 52) → sporočilo »Zadnje dni gre nekoliko slabše« → pri zdravniku »Za pregled«, 14,6 točke pod izhodiščem; skrben samopregled (92 / 91 / 93) → brez opozorila, »Danes je šlo bolje«. Testi: 97 backend, 43 frontend.

**Ključno naučeno:**
- Javne strani zVEM se ne da prebrati s preprostim fetchom (JavaScript); posnetki zaslona od Matevža so bili odločilni.
- Agenti za vmesnik so brez backenda delali z lastnim mock strežnikom in posnetki zaslona; prave podatke je treba preveriti ob integraciji (pri meni: odrezana oznaka na grafu, premajhne krivulje).
- Prag za demo: opozorilo se sproži pri povprečni oceni pod približno 67; zato je bila Ivanova raven dvignjena.

**Odprto:** igra z računalniškim vidom (mesto v čarovniku in pri zdravniku je pripravljeno); pravi telefon ni preverjen; `IMPLEMENTATION_PLAN.md` ima poglavje v8 na vrhu, starejša poglavja niso prepisana.

## 2026-11-21 — Vaje s kamero v backendu (agent, worktree)

- `scoring.py`: `gameType "camera"` gre na Primožev točkovalnik (`camera_model`); slaba kakovost posnetka, brez ocene ali napaka → seja shranjena (surovi podatki, značilke), brez ocene, ne šteje v trend. `ScoreResult.quality_ok` → `GameSession.quality_ok`; dodatni ključi `clientMeta` (videoW, fpsMeasured …) pridejo do točkovalnika in v `SessionRaw`.
- Trend: `camera:1..3`, `camera:all` po istih pravilih kot sledenje, nikoli mešano.
- Opozorila: `trend_drop` / `big_drop` za vsako igro posebej (sprožilec ima `game`), `both` = padec katerekoli igre + počutje; zatiranje po pravilu IN igri; razlog poimenuje meritev; `evidence.games`.
- Pacient: ton = povprečje razlik po igrah, odigranih na opisani dan (dan samo s sledenjem = kot prej); trend »slabše«, če pada katerakoli igra. `games` v `/progress` in `/selfcheck/summary`, 7 korakov v `/home`, kamera nikoli ne blokira zaključka.
- Seed: kamera pri p1–p7, p9 (p3 ≈ −4 brez opozorila, p4 pada tudi kamera, p2 ima zaprto preteklo rumeno opozorilo samo zaradi kamere – »težava s podatki«); p8 in demo brez kamere. Ponastavitev ~3,9 s (prej ~2,2 s).
- Testi: 131 (nov `tests/test_camera.py` s Primoževimi posnetki prek API-ja).

## 2026-11-21 (23.50) — Vaje s kamero v samopregledu (branch `matevz/camera`)

**Odločitve (Matevž):** v samopregled gredo vse tri Primoževe vaje s kamero; dlan je prva, roke v stran in dvig rok lahko pacient preskoči; brez kamere ali dovoljenja se vaje preskočijo; kamera vpliva na opozorila, sledenje in kamera imata ločena trenda in ločen prikaz.
**Način dela:** veja iz `main` + združen `compvis`; Fable pogodba in most, trije agenti Opus (high): backend, igra in pacient, zdravnik.

**Narejeno:**
- Pogodba: `gameType "camera"`, `null` v vrstah, dodatna polja `clientMeta`, preskočljivi koraki, napredek po igrah, `cameraSparkline`, `GET /api/camera/exercises`.
- `backend/app/services/camera_model.py`: most do Primoževega `score_camera` (njegova koda nespremenjena).
- Igra `frontend/src/games/camera/` (prenos Primoževega snemalnika v React, MediaPipe Hands / Pose iz lastnega izvora, `scripts/setup_mediapipe.sh`).
- Zdravnik: tretja krivulja, preklop Sledenje / Vaje s kamero, okvir opozorila z obema meritvama.

**Preverjeno v brskalniku s pravim backendom (headless Chrome):**
- Cel samopregled pri Ivanu: površno sledenje (50 / 51 / 52), vaja z dlanjo iz Primoževega testnega videa namesto kamere (`?cameraVideo=`) → ocena 57,2 (Primož 57,7), preskok obeh vaj z rokami → rezultat z dvema grafoma, pri zdravniku »Za pregled« zaradi sledenja.
- Dovoljenje za kamero zavrnjeno → pojasnilo, vse vaje s kamero izpuščene, samopregled zaključen; skrbno sledenje brez opozorila.
- Zdravnik s pravimi podatki: tri krivulje, pacientka z obema meritvama v padcu.
- Testi: 133 backend, 76 frontend, pogodba brez odstopanj.

**Ključno naučeno:**
- Zamenljiv vir videa (`?cameraVideo=`, samo v razvojnem načinu) omogoča preverjanje igre s kamero brez kamere: isti cevovod, ocena se ujema s Primoževo na pol točke.
- Headless Chrome z `--use-fake-ui-for-media-stream` na tem računalniku vklopi PRAVO kamero. Za pot brez kamere uporabi `--deny-permission-prompts`.
- Najina shema je tiho zavrgla dodatna polja `clientMeta` (`fpsMeasured`, `videoW`), ki jih točkovanje bere; zdaj jih ohrani.

**Ni preverjeno:** prava kamera v živo (piski, hitrost zajema, osvetlitev), telefon. **Odprto:** videi posnetkov (115 MB) so v veji; referenca za vaji z rokami je samo za desno stran.

## 2026-11-22 (00.45) — Animacije izvedbe pri vajah s kamero (ločena veja `matevz/camera-animations`)

**Odločitve (Matevž):** na uvodu vsake vaje s kamero animacija, ki se ponavlja do začetka vaje; lasten dizajn v slogu piktograma »stickman«, temno siv, brez Primoževih podatkov; delo na ločeni veji, da se lahko zavrže.
**Narejeno (agent Opus, high):** `frontend/src/games/camera/demo/` — `model.ts` (figura iz kotov sklepov, potek zanke, katera beseda je poudarjena, zrcaljenje; testi) in `ExerciseDemo.tsx` (čisti SVG, brez novih odvisnosti). Tri animacije: velika dlan pest ↔ razprti prsti (zrcalna za levo roko), figura z rokama v stran do malo nad višino ramen (z lokom poti), figura z rokama naprej in nad glavo. Bleda sled skrajne lege kaže zdrav razpon; poudarjena beseda (»Odprite« / »Gor«) sledi fazi; pri `prefers-reduced-motion` dve mirujoči legi.
**Preverjeno:** tsc, 94 frontend testov, build; posnetki zaslona v več fazah pri 1440×900 in 390×844 v pravem čarovniku, brez vklopa kamere. Gibanja v živo nisem gledal, samo posamezne faze.
**Znana šibkost:** pri »Dvig rok« so vmesne faze (roki kažeta proti kameri) na mirujoči sliki dvoumne; možna zamenjava je pogled s strani.
**Kako zavreči:** `git switch matevz/camera`; veja `matevz/camera` animacij nima.

## 2026-11-22 (07.06) — Statična predstavitev (branch `matevz/demo-predstavitev`)

**Narejeno:** `predstavitev/`: 9 diapozitivov za 3 minute po petih točkah iz Ixtlanovega PDF (scenarij, koncept, zbiranje podatkov, prototip, vpeljava), ena zgodba (Ivan Zupan). Čisti HTML, CSS in JS brez gradnje in zunanjih virov; objavi se mapa `predstavitev/`.
**Upravljanje:** puščice, preslednica ali daljinec; `F` cel zaslon; `#5` odpre diapozitiv; na pokončnem telefonu je stran za branje; Natisni → PDF je rezerva.
**Ključno naučeno:**
- Zasloni in grafi so iz izolirane kopije aplikacije (ponastavitev, površen samopregled pri Ivanu, 22. 11.): 14,1 točke pod izhodiščem, 35 od 40 dni počutje 7. Če se seed ali pravila spremenijo, jih je treba posodobiti.
- Integracija z zVEM / zVEM+, svojci, patronaža in osebni zdravnik so označeni kot predlog, ne kot narejeno.
- Posnetki z obrazom niso vključeni, ker bo stran javna.
**Odločil agent, potrdi Matevž:** podpis »Matevž in Primož«, naslednji korak »prostovoljci, nato pilot z enim oddelkom«, brez Ixtlanovega logotipa.
**Preverjeno:** Chrome, WebKit in Firefox (brez okna), 5 velikosti zaslona, telefon 390 in 360 px, gostovanje v podmapi, PDF 9 strani; testi 133 backend + 94 frontend. Neodvisen pregled: najdbe popravljene; zadnjih besedilnih popravkov recenzent ni več videl.
**Ni preverjeno:** projektor in prenosnik za nastop, prava objava, vaje s pravo kamero. `index.html` se odslej ureja ročno (generator grafov je bil enkraten).

## 2026-11-22 (09.20) — Videi aplikacije (branch `matevz/demo-predstavitev`)

**Odločitve (Matevž):** Primožev posnetek z obrazom (nadomesti prejšnje »brez obraza«); kratki videi v predstavitvi in celotni posebej; samo lokalni commit; zamrznitev ob 11.00 ne velja.
**Narejeno:** diapozitivi 5–7 so videi: sledenje 16 s, kamera 19 s, zdravnik 20 s (začnejo se sami; klik ali `V` ustavi oziroma ponovi). Celotni so v `posnetki/`: 45 s, 2 min 22 s, 53 s. H.264 1080p brez zvoka.
**Kako so nastali:** izolirana kopija aplikacije s svojo bazo, Ivan Zupan, prava zaznava in točkovanje. Namesto kamere Primoževi posnetki z `origin/compvis`: `202548` (Dlan 95,1), `202912` (Roke v stran 100), `203103` (Dvig rok 42,8). Sledenje je namenoma slabše: −14,1, »Za pregled«. Med kadriranjem in odštevanjem se predvaja začetek istega posnetka naprej in nazaj.
**Najdeno, NI popravljeno:**
- Kadriranje vaj z rokami zahteva vidna oba komolca (`games/camera/pick.ts`). Pri rokah ob telesu tega v prvi sekundi ne doseže 6 od 7 Primoževih posnetkov: vaja se lahko v živo ne začne, dokler pacient rok malo ne dvigne.
- Dnevnik ukrepov piše »dr. Ana Novak je zaprl / potrdil« (moški spol), vidno tudi v videu.
- Po zaprtju opozorila je Ivan takoj »Stabilno«, čeprav je 14 točk pod izhodiščem.
- `_load_hook` v `scoring.py`: sočasne prve zahteve po zagonu dobijo nadomestni točkovalnik.
**Preverjeno:** sličice vseh šestih videov, predvajanje v Chromu, WebKitu in Firefoxu, 5 velikosti zaslona, telefonska postavitev, PDF 9 strani. **Ni preverjeno:** projektor, pravi Safari ali telefon, objava.

## 2026-11-22 (10.18) — En demo video (branch `matevz/single-video`)

**Odločitev (Matevž):** zadošča združitev obstoječih treh videov; rezultat na svoji veji.
**Narejeno:** `demo-video/okrevanje-doma-demo.mp4` (3:59,97; 44,0 MB) iz `posnetki/` 1 → 2 → 3 brez prekodiranja, `demo-video/OPIS.md` s poglavji in razkritji. Worktree: `.claude/worktrees/single-video`. Brez novih napisov, naslova ali dodatnega snemanja.
**Ključno naučeno:** `AVAssetExportPresetPassthrough` pri lepljenju pusti praznino na vsakem stiku in več vnosov v `elst`. Zvezna os nastane s kopiranjem vzorcev prek `AVAssetWriter` in novimi časovnimi oznakami.
**Preverjeno:** vseh 7199 sličic je po pikslih enakih izvirnikom, enakomerno 30 fps; celotno predvajanje v Chromu brez okna brez zastojev in izpuščenih sličic; stika, začetek in konec pregledani.
**Najdeno, NI popravljeno:**
- V vaji Dlan je druga oseba z delno vidnim, zamegljenim obrazom (0:56–0:57, rob glave in telesa še do 1:04). Za hip je tudi v `predstavitev/video/kamera.mp4` (okoli 3. sekunde). Pred javno objavo vprašaj oba.
- V sliki ni razkritja o namenoma slabšem sledenju (samo v opisu); napis o posnetku namesto kamere je viden le okoli 0:50–0:53.
- Video ne pokaže »Moj napredek«, zdravnikovega zavihka »Vaje s kamero«, preskoka vaj / poti brez kamere, podrobnosti »Nujno«, dobrega dne in telefona.
**Ni preverjeno:** Google Drive, Safari, telefon.

## 2026-11-22 (10.30) — Predstavitev za Google Predstavitve (branch `matevz/demo-predstavitev`)

**Narejeno:** `predstavitev-google-slides/`: urejljiv PPTX (9 diapozitivov, povezave, opombe), `media/` (3 videi, 2 animirani črti kot MP4 in GIF), `UVOZ.md` z ročnimi koraki, `preview.png`. `predstavitev/` nespremenjena. Nič objavljeno ali commitano; skripte so bile začasne.
**Ključno naučeno:**
- Chrome na Macu BT.709 bere z gamo 1,961: `#27475a` postane `rgb(43,80,101)`. Animaciji sta zato barvno predkompenzirani; za Windows je rezerva GIF.
- Hanken Grotesk ni nameščen, PowerPoint ga zamenja s Calibrijem. Za preverjanje se lahko vdela v preizkusno kopijo PPTX.
- Google nima razmika med črkami: naslovi so ~5 % širši, prelomi isti.
- PPTX, `preview.png` in `kamera.mp4` vsebujejo Primožev obraz: ne v javno objavo.
**Preverjeno:** besedilo znak za znakom, izris v PowerPointu, sličice animacij nad diapozitivom, povezave. **Ni preverjeno:** uvoz v Google, videi iz Driva, Windows, projektor.

## 2026-11-22 (10.59) — Kratek demo video (branch `matevz/single-video`)

**Odločitev (Matevž):** krajša različica z eno nalogo sledenja, eno vajo s kamero in zdravnikovim pogledom.
**Narejeno:** `demo-video/okrevanje-doma-demo-kratek.mp4` (52,7 s; 13,9 MB): počutje, Krog, Dlan, povzetek, zdravnik. Rezi s prelivi 0,2 s, brez pospeševanja. Prekodirano (H.264). Novi napisi: skrajšano, namenoma slabše sledenje, posnetek namesto kamere med celo prikazano vajo. Dolgi video je nespremenjen.
**Ključno naučeno:** za reze in napise zadoščata Swift in AVFoundation (prenos ffmpeg v tej seji ni bil dovoljen).
**Preverjeno:** 1581 sličic glede na načrtovano montažo (povprečni PSNR 54,8 dB), predvajanje v Chromu brez zastojev, vsi rezi; druga oseba iz vaje Dlan je izrezana (levi rob kadra pregledan pri vsaki sličici).
**Znano:** »Stabilno« po zaprtju je na koncu še vidno; dnevnik ukrepov z »je zaprl« je zaradi krajšanja izpuščen. **Ni preverjeno:** Drive, Safari, telefon.

## 2026-11-22 (11.13) — Združitev vej za `main`

**Odločitev (Matevž):** delo v `matevz/demo-predstavitev` se commita, združi z `matevz/single-video` in nato v `main`.
**Narejeno:** commitana `predstavitev-google-slides/` (brez začasne `~$` datoteke PowerPointa), združena veja z demo videi (v dnevniku ohranjeni vsi vnosi po času), nato lokalna združitev v `main` prek začasnega worktreeja.
**Pozor pred pushem:** repozitorij je javen, `UVOZ.md` in vnos ob 10.30 pa pravita, da PPTX, `preview.png` in `kamera.mp4` ne gredo v javno objavo (Primožev obraz). Enak `kamera.mp4` je že javen na `origin/matevz/single-video` v `predstavitev/video/`.
**Ključno naučeno:** ne preklapljaj glavne mape na vejo brez `predstavitev-google-slides/`, dokler ima PowerPoint odprt PPTX iz nje.

## 2026-11-22 (11.48) — Poročilo za oddajo in povezave v README

**Narejeno:** `temp.md` izvožen v PDF (levo poravnano, modri naslovi); v README povezavi do `IXTLAN-ODDAJA-POROCILO.pdf` in `Turri-report.pdf`.
**Ključno naučeno:** za izvoz Markdowna v PDF zadoščata Swift in CoreText (npx + Chrome v tej seji ni bil dovoljen).
**Odprto:** poročilo Ixtlan, README in ta vnos niso commitani; povezava do poročila na GitHubu deluje šele po pushu.
