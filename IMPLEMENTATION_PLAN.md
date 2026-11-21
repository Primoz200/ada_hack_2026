# Implementacijski načrt platforme (v6)

Stanje: **v8, 21. 11. 2026 ob 20.30.** Poglavje »v8« spodaj velja pred vsem ostalim; kjer se starejša poglavja z njim ne ujemajo (dnevni vnos z vprašalnikom, opozorilni znaki, pozivi h klicu, telefon kot prva naprava, »Simuliraj 7 dni«), velja v8. Avtor: Matevž + Claude.
Ozadje in viri: `reports/Platforma za spremljanje pacientov po odpustu.md` (platforma), `RESEARCH.md` (igre), `Daljša predstavitev - Ixtlan Team AdaHack 2026.pdf` (navodila naročnika). Oblikovanje: `PRODUCT.md`, `DESIGN.md`.

## v8: kaj se je spremenilo po prvem pregledu delujoče platforme

**Odločitve (Matevž, 21. 11. zvečer)**
- **Pacient nikoli ne dobi poziva h klicu** (ne 112, ne ambulanta) in ne vidi alarmov. Alarmna stanja so izključno zdravnikova stvar. Opozorilni znaki in vprašalnik so odstranjeni.
- **Desktop first** (lepši posnetki); telefon ostane uporaben, ni pa več prva naprava.
- **Pristajalna stran je pacientov pogled:** levo zgoraj izbirnik pacienta, desno zgoraj preklop na pogled zdravnika.
- **Pacient ima dve možnosti:** »Samopregled« in »Moj napredek«.
  - Samopregled: (1) počutje 1–10 in bolečina 1–10, (2) igre sledenja ena za drugo (črta, krog, labirint), (3) računalniški vid, ko ga Primož konča; na koncu en miren stavek, kako je šlo glede na pretekle dni, in gumb »Domov«. Brez statistike.
  - Moj napredek: zelo preprosta nadzorna plošča.
- **Zdravnik:** vrstica v seznamu je oznaka stanja + ime + krivulje (sledenje, počutje, kasneje računalniški vid); okvir opozorila je poenostavljen; predvajanje sej ostane; razdelka »Skrb pacienta« in »Odgovarjal« sta odstranjena.
- **»Simuliraj 7 dni« je odstranjen.** »Ponastavi demo podatke« ostane.
- **Videz po zgledu zVEM / zVEM+** (`DESIGN.md`).

**Pravila opozoril (nadomeščajo tabelo v poglavju 8)**

| Stopnja | Pravilo | Pomen |
|---|---|---|
| Za pregled (rumena) | `trend_drop` | skupni trend danes ≤ −10 in v vsaj 2 od prejšnjih 3 dni s sejo ≤ −5 |
| Za pregled (rumena) | `subjective_drop` | 7-dnevno povprečje počutja vsaj 2 nižje ali bolečine vsaj 2 višje kot teden prej |
| Nujno (rdeča) | `both`, `big_drop` | obe rumeni hkrati, ali skupni trend ≤ −20 |
| Brez podatkov (siva) | `no_data` | 4 dni brez vnosa |

En slab dan pri stabilnem pacientu ne sproži ničesar; pri pacientu, ki že nekaj dni drsi pod izhodišče, en slab samopregled prestopi prag.

**Glavni potek dema**
1. Ponastavitev. Glavni pacient (kap, privzeto izbran) je tri tedne lepo okreval, nato počasi pada (manj kot točka na dan); opozorila še nima, naslednji pregled je čez približno mesec.
2. V pacientovem pogledu opraviva samopregled z namerno slabim sledenjem. Pacient na koncu prebere miren stavek, da gre zadnje dni nekoliko slabše.
3. Preklop na pogled zdravnika: pacient je »Za pregled«, graf kaže počasen padec, naslednji pregled je šele čez mesec. Zdravnik lahko ukrepa prej.

**Omejitev, ki jo poveva na odru:** prototip pacienta nikoli ne usmeri po pomoč. To je zavestna poenostavitev za predstavitev; v pravem izdelku bi nujna navodila določil klinik.

## v8.1: vaje s kamero (21. 11. pozno zvečer)

- Primoževe vaje s kamero (`backend/models/camera/`, točkovanje s pravili glede na zdravo referenco, brez modela) so zadnji del samopregleda: **Dlan** (21 s) je prva, **Roke v stran** in **Dvig rok** (po 42 s) lahko pacient preskoči. Brez kamere ali dovoljenja se vaje s kamero preskočijo.
- Tip igre je `camera`, stopnje 1–3. Brskalnik pošlje surove točke gibanja (MediaPipe Hands / Pose), videa ne.
- **Več meritev, ne ena:** sledenje in vaje s kamero imata ločena trenda (`trace:*`, `camera:*`) in ločen prikaz pri pacientu in zdravniku. Pravilo `trend_drop` se ovrednoti za vsako posebej; opozorilo pove, katera meritev pada. Pacient brez podatkov kamere se spremlja samo s sledenjem.
- Glavni potek dema ostane na sledenju (površno sledenje pri Ivanu → »Za pregled«).

## 1. Kaj gradiva in zakaj

**En stavek:** spletni portal, ki pri okrevanjih s tveganjem za poslabšanje motorike združi pacientovo kratko dnevno poročilo (subjektivno) s 3-minutnimi igrami, ki merijo gibanje (objektivno), in zdravnika opozori samo takrat, ko se trend glede na pacientovo lastno izhodišče obrne navzdol.

**Naprave:** pacientov del teče na telefonu (brskalnik). Testi z vlečenjem se izvajajo s prstom ali z miško s pritisnjenim levim gumbom; **vnosa sta enakovredna**, ker preverjata praktično iste sposobnosti, zato gredo seje obeh v isti trend. Zdravnikov del je namenjen računalniku.

**Predstavitev:** dema v živo ne bo in platforma med nastopom ne bo odprta. Funkcionalnost pokaževa nadzorovano, v PowerPointu ali na statični spletni strani, s slikami zaslona in kratkim videom, ki jih posnameva sama. Vse, kar želiva pokazati, mora biti zato delujoče in posneto pred zamrznitvijo.

**Scenarij (odločitev ekipe):** stanja, kjer po odpustu ni nenavadno poslabšanje motoričnih funkcij. V predstavitvi dva kontrastna primera:
- možganska kap: pregledi so pogosti, a okrevanje je najhitrejše prav med njimi;
- operacija karpalnega kanala: po odstranitvi šivov pregledov skoraj ni, zato je spremljanje med dolgimi presledki še pomembnejše.

CIPN ostane omenjena razširitev. V kodi je vsako stanje le konfiguracija (»pot okrevanja«), zato več stanj ne pomeni več kode.

**Kako odgovoriva na navodila naročnika**

| Navodilo iz PDF | Odgovor v prototipu |
|---|---|
| Rešitev ne postavlja diagnoz, ne nadomešča zdravnika | Sistem kaže odstopanje od lastnega izhodišča, nikoli diagnoze. Vsako opozorilo zapre človek z izbranim ukrepom in opombo. |
| Čas osebja je omejen | Zdravnik odpre seznam, razvrščen po nujnosti; pozornost zahtevajo le označeni pacienti. En slab dan ne sproži opozorila. Manjkajoči vnosi gredo najprej pacientu kot opomnik, ne zdravniku. |
| Subjektivni dejavniki (počutje, negotovost, dvomi) so kriterij inovativnosti | Dnevni vnos vključuje počutje in vprašanje »Vas kaj skrbi?«. Graf pokaže subjektivno in objektivno krivuljo skupaj; razhajanje med njima je samostojen signal. |
| Bližnji so pomemben deležnik | V prototipu ne (odločitev ekipe). V konceptu: svojec dostopa prek obstoječih zVEM pooblastil (v uporabi od junija 2025). |
| Integracija z eZdravjem je plus | Pacientov del kot modul zVEM, zdravnikov kot modul zVEM+, podatki v obliki, usklajeni s FHIR (vprašalnik, opazovanje, opozorilo). En diapozitiv + po možnosti končna točka `fhir-preview`. |
| Raje ožje in dobro | Tveganje: naročnik lahko tri stanja bere kot »široko«. Zato v pitchu en scenarij (»motorika med pregledi«) in ena pacientova zgodba v demu. |

**Kaj ocenjujejo:** družbeni vpliv, inovativnost, predstavitev, koda oziroma delujoč demo. Ob zaključku pričakujejo: scenarij in uporabniki, koncept, zbiranje podatkov, delujoč prototip ključnega poteka, vpeljava v prakso.

## 2. Obseg

**Mora delovati (jedro)**
1. Preklop vloge pacient / zdravnik in izbira pacienta (brez prijave).
2. Pacient: domača stran »Danes«, dnevni vnos, zagon igre, rezultat v besedah, moj napredek.
3. Shranjevanje seje igre, točkovanje (Primožev model ali nadomestni točkovalnik), izračun trenda in opozoril.
4. Zdravnik: seznam pacientov po nujnosti, podroben pogled pacienta z grafom, opozorilo z razlago, potrditev z ukrepom in opombo.
5. Sintetični pacienti z večtedensko zgodovino, vključno z enim počasnim poslabšanjem.
6. Slovenski vmesnik, oznaka »sintetični podatki« in »raziskovalni prototip«.

**Če ostane čas (po vrsti)**
1. Gumb »Simuliraj naslednjih 7 dni«, da lahko posnameva trenutek, ko se opozorilo sproži.
2. Sporočilo zdravnika pacientu po potrditvi opozorila (zapiranje zanke).
3. Tedenski povzetek za zdravnika prek Azure OpenAI Responses API, iz že izračunanih številk (vnaprej pripravljen, označen kot osnutek UI). Ključe imava.
4. `fhir-preview` končna točka.
5. Igra z gibalnimi senzorji telefona. Ker se platforma odpre kar na telefonu, QR povezava in WebSocket nista potrebna, senzorji pa zahtevajo HTTPS (tunel).

**Ne gradiva:** prave prijave, vloge svojca, patronaže in osebnega zdravnika, prave integracije z zVEM, nameščene mobilne aplikacije, javnega gostovanja, Codeplainovega izziva.

## 3. Arhitektura

- **Frontend:** Vite + React 19 + TypeScript, React Router, Tailwind 4, shadcn/ui, Recharts 3. Samo odjemalska aplikacija (brez SSR), ker igre uporabljajo kamero in canvas.
- **Backend:** FastAPI + SQLModel + SQLite, Pydantic v2, Python 3.12 ali novejši. En proces, en delavec.
- **En izvor:** FastAPI streže API (`/api/*`) in zgrajen frontend. V razvoju Vite proxy na `localhost:8000`.
- **Baza je potrošna:** ob zagonu se ustvari in deterministično napolni; `POST /api/admin/reset` jo vrne v začetno stanje.
- **Pogodba:** `contracts/openapi.json` je v repozitoriju; iz nje se generirajo TypeScript tipi. Sprememba te datoteke pomeni spremembo pogodbe.
- **Vse teče lokalno** (odločitev), javnega gostovanja ni.
- **Telefon med razvojem in snemanjem:**
  - `vite --host` in `uvicorn --host 0.0.0.0` zadoščata, da telefon v istem omrežju odpre portal; dnevni vnos in sledenje s prstom tako delujeta takoj;
  - **kamera pa prek `http://<IP prenosnika>` ne deluje.** Brskalnik kamero dovoli samo v varnem kontekstu (HTTPS ali `localhost`); na navadnem HTTP naslovu `navigator.mediaDevices` sploh ne obstaja;
  - rešitev: Vite z vtičnikom `@vitejs/plugin-basic-ssl` (samopodpisano potrdilo; telefon enkrat pokaže opozorilo, ki ga potrdiš) in Vite proxy za `/api` na FastAPI. Telefon odpre `https://<IP prenosnika>:5173`, API gre prek istega naslova, zato backend ne potrebuje HTTPS;
  - alternativi: Android prek USB z `adb reverse tcp:5173 tcp:5173` (telefon odpre `http://localhost:5173`, kar je varen kontekst) ali začasen tunel (`cloudflared tunnel --url http://localhost:5173`);
  - če omrežje prizorišča blokira povezave med napravami, se prenosnik poveže na dostopno točko telefona.
- **Zajem za predstavitev:** pacientov del posnameva z vgrajenim snemanjem zaslona na telefonu, zdravnikovega s slikami zaslona na prenosniku. Posnetki gredo v PowerPoint ali na statično spletno stran.

Različice, preverjene v registrih 21. 11. 2026 (agenti naj jih pred namestitvijo potrdijo z `npm view` / `pip index`): Vite 8.3, React 19.3, React Router 8.5, Tailwind 4.3, shadcn CLI 4.23, Recharts 3.11, `@mediapipe/tasks-vision` 1.2.3, FastAPI 0.165, SQLModel 0.0.50, Pydantic 2.14.

**Povzetek z jezikovnim modelom (dodatek):** Azure OpenAI Responses API prek paketa `openai` z `base_url=https://<vir>.openai.azure.com/openai/v1/`; `model` je ime najine namestitve (deployment). Strukturiran izhod s `responses.parse(..., text_format=PydanticModel)`. Ključ in naslov sta v `.env` (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`), `.env` je v `.gitignore`. Model dobi samo številke, ki jih je izračunal backend; smer trenda določi pravilo, ne model; povzetki so ustvarjeni vnaprej in shranjeni, da demo ne visi na klicu.

Znane pasti:
- `@tremor/react` ne podpira React 19; ne uporabljaj.
- Tailwind 4 nima več `tailwind.config.js` in `init`; nastavitev je v CSS.
- MediaPipe: uporabi Tasks API (`HandLandmarker`, `PoseLandmarker`, način `VIDEO`), ne starih paketov `@mediapipe/hands`. Datoteke `wasm/` in modele `.task` streži iz lastnega izvora, ne s CDN `@latest`.
- Pydantic v2: brez `.dict()` in `@validator`.
- Surovih časovnih vrst ne vračaj v seznamih; hrani jih v ločeni tabeli.

## 4. Struktura repozitorija in lastništvo

```
/backend
  app/main.py            zagon, statične datoteke, lifespan (seed)
  app/models/            tabele in javni odzivni modeli        (Matevž)
  app/routers/           patients, checkins, sessions, alerts  (Matevž)
  app/services/alerts.py pravila opozoril                      (Matevž)
  app/services/trend.py  assess_trend, skupni trend (pravila, brez modela)  (Matevž)
  app/services/scoring.py  adapter: pokliče Primožev model, sicer nadomestni točkovalnik  (Matevž)
  app/services/ingest.py   enotna pisalna pot (API, seed, simulacija)                    (Matevž)
  models/                modeli strojnega učenja, generator sintetike (Primož; zdaj še vrhnja mapa /models)
  app/seed/              generator sintetičnih pacientov       (Matevž, značilke uskladi s Primožem)
/frontend/src
  app/                   usmerjanje, postavitev, preklop vlog  (Matevž)
  features/patient/      pacientov del, najprej za telefon     (Matevž)
  features/clinician/    zdravnikov del                        (Matevž)
  games/                 trace/, shared/, registry.ts          (Matevž)
  games/_stub/           nadomestna igra                       (Matevž)
  client/                generirani tipi, ne urejaj ročno
/shared/tracer_levels.json   oblike stopenj; bereta igra (frontend) in model (backend)  (Primož)
/docs/tracer_data_spec.md    Primoževa specifikacija sledenja; ob neskladju velja poglavje 5
/contracts/openapi.json
/scripts                 export_openapi.py, dev.sh
IMPLEMENTATION_PLAN.md, AGENTS.md, DEMO.md
```

Pravilo: nihče (ne človek ne agent) ne ureja map drugega. Primoževe so `backend/models/` (oziroma vrhnja `/models`), `shared/` in `docs/`; vse ostalo je Matevževo. Skupne vroče datoteke (`app/models/`, registracija routerjev, `routes.tsx`) ureja Matevž. Pozor na imeni: `backend/app/models/` so tabele (Matevž), `backend/models/` je strojno učenje (Primož).

## 5. Vmesnik med igrami in platformo

Delitev (v7): Matevž implementira platformo in igre (ves frontend); Primož prispeva raziskavo, kontekst in modele strojnega učenja, ki jih platforma kliče prek adapterja `app/services/scoring.py`. Platforma surove podatke vsake seje shrani in jih modelu posreduje skupaj z vso zgodovino.

Vsaka igra je React komponenta z enakim podpisom. Platforma poskrbi za navodila pred igro, pošiljanje na API in zaslon z rezultatom.

```ts
type GameType = "trace" | "camera_tapping" | "camera_reach" | "motion";

interface GameConfig {
  gameType: GameType;
  level: number;            // merilni krog ima FIKSNO stopnjo (sicer se pokvari trend); glej odprto točko 5
  hand: "left" | "right";   // prizadeta ali operirana stran
  patientId: string;
}

interface GameResult {
  gameType: GameType;
  level: number;
  hand: "left" | "right";
  startedAt: string;        // ISO, začetek testa
  durationMs: number;       // koliko časa je trajal test (od prvega dotika do konca)
  completed: boolean;       // false, če je pacient prekinil
  series: Record<string, number[]>;   // vsebina je odvisna od igre, glej spodaj
  clientMeta: {
    inputDevice: "touch" | "mouse" | "camera";  // prst in miška enakovredna; polje je le metapodatek
    canvasW: number; canvasH: number;   // CSS piksli
    devicePixelRatio: number;
    userAgent: string;
  };
}

// <TraceGame config={...} onComplete={(r: GameResult) => void} onAbort={() => void} />
```

**Igra sledenja: kaj se beleži** (zahteva: čas, želena črta, dejanska sled)

| Ključ v `series` | Pomen |
|---|---|
| `targetX`, `targetY` | želena črta kot zaporedje točk, v vrstnem redu risanja (iz `shared/tracer_levels.json`, deljeno s 1000) |
| `t` | čas vsake točke dejanske sledi v ms od prvega dotika |
| `x`, `y` | dejanska sled prsta |
| `strokeId` | zaporedna številka potega; poveča se ob vsakem dvigu prsta oziroma spustu gumba miške |

Stopnje sledenja (fiksne oblike, definirane v `shared/tracer_levels.json`, ki ga bereta igra in model): `level` 1 = `line`, 2 = `circle`, 3 = `maze`. Merilni krog = vse tri stopnje, vsaka enkrat (ena seja na stopnjo). Pravila igre (začetek, konec po ≥ 90 % poti, časovna omejitev, navodilo »čim natančneje, v svojem tempu«) so v `docs/tracer_data_spec.md`.

Pravila zajema:
- Koordinate so normalizirane na 0–1 glede na platno (ista oblika na vsakem zaslonu); velikost platna je v `clientMeta`. **Platno je kvadratno** (`canvasW == canvasH`), da sta obe osi v enakem merilu; sicer se krog v podatkih pokvari v elipso in razdalje od črte niso primerljive.
- Ko prst ali miška miruje, brskalnik ne pošilja dogodkov; postanek se vidi kot vrzel v `t` (zato je `t` za vsako točko obvezen). Prevzorčenje naredi model.
- Prst ali miška: Pointer Events (`pointerdown/move/up`), upoštevajo se dogodki s `pointerType` `"touch"` ali `"mouse"` (pri miški se sled beleži le med držanjem levega gumba). `inputDevice` v `clientMeta` pove, s čim je bila seja narejena, vendar je le metapodatek: prst in pritisnjena miška sta enakovredna vnosa in njune seje gredo v isti trend. Na platnu `touch-action: none` in `setPointerCapture`, da stran med risanjem ne drsi.
- Čas iz `event.timeStamp`; dodatne točke iz `getCoalescedEvents()`, kjer jih brskalnik ponudi. Brez prevzorčenja ali glajenja na odjemalcu: model dobi surovo sled.
- Dvigi prsta oziroma spusti gumba in prekinitev se zabeležijo, ne zavržejo.

**Backend funkciji** (`score_session` dostavi Primož, `assess_trend` je pravilo brez modela pri Matevžu)

```python
def score_session(game_type: str, level: int, hand: str,
                  duration_ms: int, series: dict[str, list[float]],
                  client_meta: dict) -> ScoreResult:
    # ScoreResult: features: dict[str, float], score: float (0-100),
    # impairment_class: Literal["normal","mild","moderate","severe"], model_version: str

def assess_trend(history: list[ScoredSession]) -> TrendResult:
    # BREZ MODELA: izhodišče + EWMA iz shranjenih ocen (poglavje 8).
    # history: VSE pretekle seje iste igre IN iste stopnje za pacienta, urejene po času
    #          (ocene različnih stopenj niso primerljive, zato trend teče ločeno po stopnji)
    #          (datum, trajanje, stopnja, značilke, ocena)
    # TrendResult: direction: Literal["improving","stable","declining","insufficient_data"],
    #              baseline: float | None, smoothed: float | None,
    #              delta_vs_baseline: float | None, n_sessions: int, model_version: str
```

**Delitev (odločitev 21. 11.):** model oceni samo posamezno sejo (en test) iz njene sledi; pacienta in njegove zgodovine ne pozna. Platforma oceno shrani pri pacientu, trend pa se računa iz te zgodovine s pravili, brez modela.

Platforma ob vsaki novi seji pokliče `score_session`, shrani rezultat, nato za vsako stopnjo pokliče `assess_trend`, ločene trende združi v **skupni trend** (poglavje 8) in na njem uporabi pravila opozoril.

Da nihče ne čaka:
- **Nadomestna igra** (`games/_stub`) po 3 sekundah vrne vnaprej pripravljen `GameResult`; ostane kot varovalka za igre brez implementacije.
- **Nadomestni točkovalnik** (povprečna razdalja sledi od želene črte + čas → 0–100) in **privzeti trend** (izhodišče + EWMA, poglavje 8) z istima podpisoma. Oba ostaneta kot varovalka, če se model na demo računalniku ne naloži.
- Za kamero se na strežnik pošljejo samo točke telesa oziroma izpeljane vrste, nikoli video.

**Testi s kamero: postavitev** (odločitev)
- Telefon stoji na mizi pod naklonom (naslonjen na knjigo ali skodelico), snema sprednja kamera (`facingMode: "user"`), pacient se med testom vidi na zaslonu (zrcaljen predogled).
- Pred testom zaslon za postavitev: slika, kako nasloniti telefon, in preverjanje kadra (roka oziroma zgornji del telesa je v celoti viden, dovolj svetlobe). Test se začne šele, ko je kader ustrezen.
- Naklon in razdalja bosta vsak dan nekoliko drugačna. Da to ne pokvari trenda, naj značilke temeljijo na kotih in razmerjih (normalizacija na velikost dlani ali širino ramen), ne na pikslih. V `series` naj gre tudi mera kakovosti kadra, da platforma slabo posneto sejo označi in je ne šteje v trend.

## 6. Podatkovni model

| Tabela | Ključna polja | FHIR ustreznik |
|---|---|---|
| `pathway` | koda (`stroke`, `ctr`), naziv, seznam iger, vprašanja, opozorilni znaki, pogostost | PlanDefinition |
| `patient` | ime (izmišljeno), rojstno leto, pot okrevanja, stran, datum odpusta, datum naslednjega pregleda | Patient, CarePlan |
| `clinician` | ime, vloga | Practitioner |
| `checkin` | pacient, datum, opozorilni znaki, odgovori JSON, skrb (ne / malo / želim klic) + prosto besedilo, kdo je odgovarjal (sam / s pomočjo / svojec) | QuestionnaireResponse |
| `game_session` | pacient, igra, stopnja, začetek, trajanje v ms, dokončano, naprava (dotik / miška / kamera), ocena, razred, različica modela, značilke JSON | Observation |
| `session_raw` | seja, surove vrste (pri sledenju: želena črta, dejanska sled s časi, potegi), `clientMeta` | Observation.valueSampledData |
| `trend_snapshot` | pacient, metrika, datum, št. sej, izhodišče, EWMA, naklon, sprememba v %, stanje | izpeljan Observation |
| `alert` | pacient, vir (igra / vprašalnik), pravilo, stopnja (rdeča / rumena / siva), stanje (novo / potrjeno / zaprto), dokazi JSON, kdo in kdaj, izid, opomba | Flag |
| `message` | pacient, smer, besedilo, čas | Communication |

V pitchu: model je »usklajen s FHIR«, ne »skladen s FHIR«. Opozorilo je `Flag` (trajno opozorilo o pacientu), ne `DetectedIssue`.

## 7. API (v0)

| Metoda in pot | Namen |
|---|---|
| `GET /api/pathways` | poti okrevanja s konfiguracijo |
| `GET /api/patients` | seznam za triažo: stanje, razlog v besedah, mini graf, vnosi v 7 dneh, dnevi do pregleda, odprta opozorila |
| `GET /api/patients/{id}` | glava pacienta in povzetek |
| `GET /api/patients/{id}/timeline` | seje, vnosi in posnetki trenda za grafe |
| `GET /api/patients/{id}/today` | današnje naloge in zadnje sporočilo tima |
| `POST /api/checkins` | shrani dnevni vnos, preveri opozorilne znake |
| `POST /api/sessions` | sprejme `GameResult`, shrani surove podatke, točkuje, z vso zgodovino preračuna trend, odpre ali zapre opozorila, vrne rezultat za pacienta |
| `GET /api/sessions/{id}/raw` | surova seja za prikaz sledi čez želeno črto pri zdravniku |
| `GET /api/alerts?status=open` | odprta opozorila |
| `POST /api/alerts/{id}/ack` | potrditev; zaprtje je mogoče samo z izbranim izidom (in neobvezno opombo) |
| `POST /api/messages` | sporočilo zdravnika pacientu |
| `POST /api/admin/reset` | ponastavi demo podatke |
| `POST /api/admin/simulate` | doda N sintetičnih dni izbranemu pacientu (za demo) |

Trend in opozorila se preračunajo sinhrono v istem zahtevku, ki shrani sejo; vrsta ima le nekaj deset točk.

## 8. Logika trenda in opozoril

Privzete vrednosti so inženirska izbira; validiranih pragov za te igre ni in to poveva tudi na odru. Vse so parametri v `alerts.py`.

**Trend igre** (`assess_trend`, pravilo brez modela, ločeno za vsako stopnjo)
- **Izhodišče:** prva seja je vaja in se zavrže; izhodišče je mediana sej 2–4. Do takrat je stanje »premalo podatkov«.
- **Glajenje:** EWMA z utežjo 0,3 na oceni 0–100.
- **Učinek vaje:** če je mediana najboljših treh od zadnjih sedmih sej višja od izhodišča, se primerja z njo (če ostane čas; sicer samo izhodišče).
- Ob vsakem trendu piše, na koliko sejah temelji. Manjkajoči dnevi se ne zapolnjujejo.

**Skupni trend** (odločitev 21. 11.: iz ločenih trendov po stopnjah nastane en povprečni trend)
- Za vsako stopnjo se izračuna odmik EWMA od lastnega izhodišča te stopnje (v točkah).
- Skupni trend dneva je povprečje teh odmikov po stopnjah, ki že imajo izhodišče in so bile ta dan opravljene. Povpreči se odmik, ne surova ocena, ker imajo stopnje različna izhodišča in ker tako manjkajoča stopnja ne premakne rezultata.
- Pravila opozoril, mini graf v seznamu, glavni graf pri zdravniku in sporočilo pacientu uporabljajo skupni trend; trendi posameznih stopenj so pri zdravniku v zavihkih.
- V `trend_snapshot` se shranijo trendi po stopnjah in skupni (`metrika` = `trace:1`, `trace:2`, `trace:3`, `trace:all`).

**Tri stopnje opozoril**

| Stopnja | Sprožilec | Pacient vidi | Zdravnik vidi |
|---|---|---|---|
| Rdeča | pritrdilen odgovor na opozorilni znak; ali dve hkratni rumeni (igra + vprašalnik) | kap: celozaslonsko »Takoj pokličite 112«; rana ali padec: »Še danes pokličite ambulanto« | na vrhu seznama; obide logiko trenda |
| Rumena | skupni trend vsaj 10 točk pod izhodiščem v 2 od zadnjih 3 dni s sejo; ali bolečina oziroma mravljinčenje vztrajno višje (bolečina +2 ali več glede na prejšnji teden) | nevtralno: »Rezultati so ta teden nekoliko drugačni. Vaš zdravnik jih vidi.« | vrstica z razlogom v enem stavku |
| Siva | ni vnosa | samodejni opomnik po 2 izpuščenih dneh | oznaka »brez podatkov« šele po 4 dneh |

**Pravila proti hrupu**
- Eno odprto opozorilo na pacienta; novi sprožilci se mu pripnejo.
- Po potrditvi se isti vzrok ne sproži znova, razen če se stanje poslabša za stopnjo.
- En sam slab rezultat pacientu ponudi ponovitev; zdravnik ne dobi ničesar.
- Opozarja se samo na poslabšanje. Izboljšanje se prikaže tiho.
- Pričakovani vzorci se utišajo po poti okrevanja (karpalni kanal: bolečina ob prijemu in šibkejši stisk v prvih tednih sama ne sprožita opozorila).

**Razhajanje** (objektivna ocena pada, pacient poroča enako ali boljše počutje, ali obratno) se pokaže kot oznaka pri pacientu in v razlagi opozorila. To je najina glavna trditev o inovativnosti.

**Človek v zanki:** novo → potrjeno (kdo, kdaj) → zaprto z izidom. Izidi: »poklical, pomiril«, »prilagodil vaje«, »pregled prestavljen naprej«, »nujna napotitev«, »nedosegljiv«, »lažni alarm ali težava s podatki«. Brez izbranega izida opozorila ni mogoče zapreti.

**Opozorilni znaki** (po britanskih navodilih za paciente; besedilo mora potrditi slovenski klinik):
- kap: povešen obraz, šibka ali omrtvela roka ali noga, težave z govorom, nenadna izguba vida, zelo hud glavobol;
- karpalni kanal (do zacelitve rane): roka rdeča, vroča, bolj otekla ali bolj boleča, izcedek, razprta rana, vročina, nova omrtvelost.

Zakaj tako: v nizozemskem programu spremljanja je opozorilo sprožilo 57 % meritev, 77 % ročnih ukrepov pa je bilo administrativnih; v simulaciji so pravila na trendu dala približno pol manj epizod opozoril kot fiksni prag. Številke pred uporabo na diapozitivu preveri na povezavah v poročilu.

## 9. Zasloni

### Pacient (telefon v pokončni legi, velike tipke, ena roka, brez časovnega pritiska)

1. **Danes:** pozdrav, 2–3 naloge (»Kako ste danes?«, »Sledi poti«, »Ritem prstov«), niz zaporednih dni, zadnje sporočilo tima, gumb »Potrebujem pomoč«.
2. **Dnevni vnos** (manj kot minuto, eno vprašanje na zaslon, lastna vprašanja, ne licenčni vprašalnik):

   | | Kap | Karpalni kanal |
   |---|---|---|
   | 1. Opozorilni znaki (da / ne, s piktogrami; vedno prvo vprašanje) | od včeraj kaj novega in nenadnega: obraz, roka ali noga, govor, vid, hud glavobol | roka rdeča, vroča, bolj otekla ali boleča; izcedek; vročina |
   | 2. Funkcija ali bolečina | kako je danes delala prizadeta roka (5 obrazov) | bolečina v roki zdaj (0–10, gumbi) |
   | 3. Simptom | utrujenost danes | mravljinčenje ali omrtvelost prstov (0–4) |
   | 4. Dogodek | ste od včeraj padli | kolikokrat so vas simptomi ponoči zbudili |
   | 5. Skrb | vas glede okrevanja kaj skrbi ali ste v dvomih (ne / malo / da, želim klic) + neobvezno besedilo | enako |

   Na koncu: kdo je odgovarjal (sam / s pomočjo / svojec) in potrditev »Poslano vašemu zdravniku«.
3. **Igra:** kratka navodila s sliko (pri kameri tudi postavitev telefona in preverjanje kadra) → Primoževa komponenta → rezultat v besedah (»Danes je šlo podobno kot običajno«), brez gole številke in brez razreda okvare.
4. **Moj napredek:** en črtni graf lastnih rezultatov z besednimi oznakami, osebni rekord, tedenski niz, ki odpusti izpuščen dan (5 od 7), in »Zdravnik je pregledal vaše rezultate«, ko se to zgodi.
5. **Sporočila po oddaji** (štiri ravni): zahvala in napredek → nevtralno »rezultati so nekoliko drugačni, zdravnik jih vidi« (brez rdeče barve in besede »poslabšanje«) → »še danes pokličite ambulanto« → »takoj pokličite 112«. Pri znakih kapi sistem nikoli ne sporoči le, da je obvestil tim.
6. **Dostopnost:** gumbi vsaj 48 px, besedilo 18–20 px, brez drsnikov in spustnih menijev, »Nazaj« vedno na istem mestu, izhod »danes ne morem« pri igri (zabeleži se kot razlog). Stalno obvestilo, da aplikacija ne nadomešča nujne pomoči.

### Zdravnik (pregled v pol minute)

1. **Pregled pacientov:** zavihki »Zahteva pozornost«, »Vsi«, »Brez podatkov«. Vrstica: ime, pot okrevanja, dan po odpustu, barva stanja z razlogom v besedah, mini graf, vnosi v 7 dneh, »naslednji pregled čez N dni«.
2. **Pacient:**
   - kartica opozorila: kaj se je zgodilo, od kdaj, katere seje, kaj pacient sam poroča;
   - graf igre: posamezne ocene kot blede pike, EWMA kot glavna črta, pas izhodišča, označeni dnevi opozoril in pregledov;
   - pod njim ločena plošča simptomov, poravnana po času (bolečina, mravljinčenje, počutje, skrbi). Lestvici z nasprotno smerjo nikoli nista na isti osi;
   - zavihki po igrah, tabela značilk s spremembo glede na izhodišče (kaj je prispevalo k padcu);
   - pri sledenju predvajanje izbrane seje: dejanska sled čez želeno črto, ob njej seja iz izhodišča za primerjavo;
   - zgodovina dnevnih vnosov, vključno s pacientovimi skrbmi;
   - potrditev in zaprtje z izidom (seznam v poglavju 8) + opomba; dnevnik ukrepov.
3. **Prikaz ocene modela:** nikoli gola številka. Ob oceni stojijo sprememba glede na izhodišče, 2–3 značilke, ki so se najbolj premaknile, in število sej. »Razred okvare« se v vmesniku imenuje »območje rezultata« in je le opisna oznaka na osi. Stalno viden stavek: »Podpora odločanju brez klinične validacije; primerja pacienta z njegovimi prejšnjimi sejami.« Za ikono »i« kratka kartica o modelu (kaj je, učen na sintetiki, različica).

Pravila prikaza: besedne oznake na osi, status z ikono in besedo (ne samo z barvo), stabilni pacienti sivi (ne zeleni), števec na vrhu v slogu »2 za pregled · 1 brez podatkov · 7 stabilnih«.

## 10. Sintetični podatki

Generator je determinističen (seme) in gre skozi **isto kodo za trend in opozorila** kot živi sistem, dan za dnem. Tako so grafi, ocene in opozorila vedno skladni.

| Pacient | Pot | Zgodba |
|---|---|---|
| 1 | kap | enakomerno okrevanje (stabilno) |
| 2 | kap | hitro okrevanje, nato plato (stabilno) |
| 3 | kap | tri tedne napredka, nato počasen padec ocene igre, vprašalnik ostaja miren (razhajanje) → rumeno opozorilo tik pred »danes«. **Glavna zgodba dema: signal iz meritve.** |
| 4 | karpalni kanal | 5. teden po operaciji, nobene načrtovane kontrole več; naraščajoča omrtvelost in znak na rani → rdeče opozorilo iz vprašalnika, skrb »želim klic«. **Kontrastni primer: signal iz subjektivnega poročila.** |
| 5 | karpalni kanal | okrevanje po pričakovanjih (stabilno) |
| 6 | kap | objektivno stabilen, a poroča slabo počutje in skrbi (razhajanje; zdravnik vidi pacientovo vprašanje) |
| 7 | kap | malo vnosov (zavihek »Brez podatkov«) |
| 8 | kap | hrupni, a stabilni rezultati (dokaz, da en slab dan ne sproži opozorila) |
| 9 | karpalni kanal | nov pacient, premalo sej |
| Demo | kap | zgodovina do včeraj; z njim posnameva sejo na telefonu, nova točka se pojavi na zdravnikovem grafu |

Nujni so pacienti 1, 3, 4, 7 in 8 ter demo pacient; ostali so dodatek. Preizkus: pacient 3 ima natanko eno odprto opozorilo, pacient 8 nobenega.

## 11. Časovnica

Po uradni časovnici se kodiranje konča **v nedeljo ob 11.00 (»No more commits!«)**; predstavitve so 13.00–15.00, 3 minute na odru. Preverita pri organizatorjih. Načrt cilja na 11.00.

| Kdaj | Matevž | Primož |
|---|---|---|
| Sob 16.30–18.00 | uskladitev poglavij 5 in 12; ogrodje backend + frontend; modeli in prazni routerji; `openapi.json`; preklop vlog | nadomestna igra s podpisom iz poglavja 5; podpis `score_session` |
| Sob 18.00–21.30 | navpični rez na pravem telefonu (HTTPS): Danes → vnos → igra → `POST /sessions` → nadomestna ocena → graf pri zdravniku | igra 1 (sledenje) v `games/trace`, značilke |
| Sob 21.30–01.00 | `alerts.py`, pravila opozoril, generator s ponovitvijo, seznam za triažo, potrditev opozorila | model za igro 1, igra 2 (kamera) |
| Ned 07.00–09.00 | pacientova sporočila, besedila, prazna stanja, »Simuliraj 7 dni«, povzetek prek Azure | vklop pravih modelov, umerjanje stopenj |
| Ned 09.00–10.00 | eden na delavnici za pitch (Impact Hub), drugi zaključuje | |
| Ned 10.00–11.00 | zamrznitev, zadnji commit; snemanje: slike zaslona in video celotnega poteka po seznamu iz poglavja 13 | |
| Ned 11.00–13.00 | diapozitivi s posnetki in vaja 3-minutne predstavitve | |

Mejnik, ki ne sme zdrsniti: **sobota 21.30, navpični rez deluje od konca do konca z nadomestno igro, odprt na pravem telefonu.** Kar do nedelje 9.00 ni zanesljivo, se izklopi z zastavico.

## 12. Odprte točke

Rešeno 21. 11.: Primož dela igre, modele in točkovanje, Matevž platformo; vse teče lokalno; za povzetek imava ključe Azure; Codeplainovega izziva ne rešujeva; pacientov del teče na telefonu, testi s prstom ali pritisnjeno miško (enakovredna vnosa, isti trend); model točkuje le posamezno sejo, trend se računa iz shranjenih ocen brez modela; iz trendov po stopnjah nastane en skupni povprečni trend; Primoževa koda gre v `backend/models/`; dema v živo ni, platformo posnameva in pokaževa v PowerPointu ali na statični strani; pri testih s kamero je telefon naslonjen na mizi, snema sprednja kamera.

1. **Rok:** 11.00 ali 12.00? Vprašajta organizatorje.
2. **Kdo izračuna trend?** ~~Odprto~~ Rešeno: trend je pravilo brez modela (izhodišče lastnega pacienta + EWMA), ločeno po igri in stopnji, nato povprečen v skupni trend (poglavje 8). Model točkuje samo sejo.
3. **Oblika surovih podatkov sledenja** (tabela v poglavju 5): ~~Odprto~~ Potrjeno (Primož): ključi `targetX/targetY/t/x/y/strokeId`, normalizacija 0–1 na kvadratnem platnu, stopnje 1–3 iz `shared/tracer_levels.json`. Generator sintetike bo Primož v naslednjem commitu spremenil, da izpiše to obliko (zdaj še staro iz `docs/tracer_data_spec.md`: enote 0–1000, 60 Hz, `down`). Posnema sled miške, kar zadošča, ker sta vnosa enakovredna.
4. **Prag 10 točk:** Primož naj sporoči, koliko ocena modela niha pri isti resnosti (ponovljeni sintetični poskusi), da prag ni pod šumom. Od tega je odvisno tudi, ali generator pacientov lahko vsak dan ustvari novo sled in jo točkuje, ali pa ocene zapiše neposredno.
5. **Stopnja igre in trend:** ~~Odprto~~ Potrjeno (Primož): stopnje so fiksne oblike in se ne spreminjajo z napredkom. Model dobi stopnjo kot vhod, trend pa se računa ločeno po stopnji (primerja se le ista stopnja). Ločenega vadbenega kroga ni.
6. **Igra s kamero na telefonu:** ritem prstov, doseg z ramo ali oboje? Primož naj potrdi, da so značilke neodvisne od naklona in razdalje telefona, in doda mero kakovosti kadra. HTTPS na telefonu preizkusita danes.
7. **Opozorilni znaki:** ali imata dostop do zdravnika ali mentorja, ki bi potrdil besedilo?

## 13. Predstavitev (3 minute, zdrži tudi kot 2)

Brez dema v živo in brez odprte platforme: v PowerPointu ali na statični spletni strani so slike zaslona in kratek video, ki ga posnameva sama. Posnetki delovanja stojijo pred diapozitivom o umestitvi, da sta ob prekinitvi po dveh minutah problem in celotna zanka že pokazana.

| Čas | Vsebina | Točka naročnika |
|---|---|---|
| 0:00–0:25 | Ena pacientka: po operaciji karpalnega kanala je edina kontrola po dveh tednih, nato je sama. Pri kapi je kontrol več, a so vrzeli med njimi dolge. Vmes nihče ne vidi, če roka počasi popušča. | scenarij in uporabniki; družbeni vpliv |
| 0:25–0:40 | En stavek: okrevanje funkcije roke doma, ena pot za obe stanji. Pacient pove, kako se počuti; igra izmeri, česar sam ne opazi. | koncept; inovativnost |
| 0:40–1:25 | Video s telefona: opozorilni znaki, tri ocene, vprašanje o skrbeh, sledenje s prstom, »Poslano vašemu zdravniku«. Ob njem slika zajetih podatkov: želena črta, dejanska sled, čas. | zbiranje podatkov; delujoč prototip |
| 1:25–2:05 | Slike zdravnikovega pogleda: »2 za pregled«, pacient 3 s padajočim trendom in mirnim vprašalnikom, razlog v enem stavku, zaprtje z izbranim izidom; rdeče opozorilo iz vprašalnika pri pacientki 4. | človek v zanki; čas osebja |
| 2:05–2:35 | Diapozitiv: kdo kaj vidi in kdo ukrepa; zVEM za pacienta in pooblaščenega svojca, zVEM+ za tim, podatki v CRPP. | vpeljava v prakso; eZdravje |
| 2:35–3:00 | Poštenost: raziskovalni prototip na sintetičnih podatkih, brez oznake CE, ne diagnosticira; za klinično rabo bi bil medicinski pripomoček. Naslednji korak: ponovljene meritve na peščici ljudi in pilot z enim oddelkom. | zaupanje; predstavitev |

**Seznam posnetkov** (po ponastavitvi demo podatkov):
1. Telefon: zaslon »Danes« z nalogami.
2. Telefon: vprašanje o opozorilnih znakih in vprašanje o skrbeh.
3. Telefon (video): sledenje s prstom od začetka do konca in potrditev »Poslano vašemu zdravniku«.
3a. Fotografija postavitve za test s kamero (telefon naslonjen na knjigo, pacient v kadru) in posnetek zaslona med testom.
4. Telefon: »Moj napredek«.
5. Telefon: celozaslonsko navodilo ob opozorilnem znaku.
6. Prenosnik: seznam pacientov s števcem in razlogi.
7. Prenosnik: pacient 3, graf z izhodiščem in EWMA ter plošča simptomov.
8. Prenosnik: predvajanje seje, dejanska sled čez želeno črto, ob njej seja iz izhodišča. **To je slika, ki pokaže, kako zajem podatkov deluje.**
9. Prenosnik: zaprtje opozorila z izbranim izidom.
10. Prenosnik: pacientka 4 z rdečim opozorilom iz vprašalnika.
11. Prenosnik: nova točka na grafu demo pacienta po posneti seji.

Besede, ki se jim izogneva: »validirano«, »diagnosticira«, »anonimno«, »izboljša preživetje«, »wellness aplikacija«, »skladno z MDR / EHDS / FHIR«, »validirana slovenska različica vprašalnika«. Pred tem občinstvom uporabiva naročnikovi številki za zVEM (700.000+ uporabnikov, 3.600+ zdravstvenih delavcev).
