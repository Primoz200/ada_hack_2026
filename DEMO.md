# Zagon in snemanje dema

Raziskovalni prototip na sintetičnih podatkih. Vse teče lokalno.

## Zahteve

- `uv` (Python 3.12 si namesti sam), Node 22 + npm.

## Prvi zagon

```bash
cd backend && uv sync
cd ../frontend && npm ci
cd .. && ./scripts/setup_mediapipe.sh   # enkrat: modela in wasm za vaje s kamero (približno 25 MB, ni v gitu)
```

## Razvoj

```bash
./scripts/dev.sh
```

- Backend: `http://localhost:8000` (dokumentacija API: `/docs`).
- Frontend: `https://localhost:5173` (samopodpisano potrdilo; brskalnik enkrat pokaže opozorilo). `/api` gre prek Vite proxyja na backend.
- Brez HTTPS: `NO_HTTPS=1 npm run dev` v mapi `frontend`.

Baza je potrošna: ob vsakem zagonu backenda se ustvari na novo in deterministično napolni. Z `APP_KEEP_DB=1` se obstoječa baza ohrani.

## Glavni potek dema (snemanje na namizju)

1. Odpri `http://localhost:5173` (ali `https://`, če teče z HTTPS). Odpre se pacientov pogled; levo zgoraj je izbran **Ivan Zupan**.
2. Po želji najprej pokaži zdravnikov pogled (desno zgoraj »Pogled zdravnika«): Ivan je med stabilnimi, opozorila nima, naslednji pregled je čez 30 dni.
3. Nazaj v pogled pacienta → **Začni samopregled**: izberi počutje in bolečino, nato sledi trem potem **namerno površno** (vijugaj čez rob kanala, a ostani blizu poti, sicer se naloga konča šele ob izteku časa).
4. Sledi vaja **Dlan** pred kamero (»Vklopi kamero«, dovoli dostop; 21 sekund, vodijo jo piski in napisa »Odprite« / »Stisnite«). Vaji **Roke v stran** in **Dvig rok** lahko preskočiš z »Preskoči«. Če kamere ne dovoliš, se vse tri vaje izpustijo.
5. Na koncu pacient prebere miren stavek, da gre zadnje dni nekoliko slabše, in vidi graf za sledenje ter graf za vaje s kamero. Nobenega poziva h klicu.
6. »Pogled zdravnika«: Ivan je zdaj **Za pregled**. Na njegovi strani so padec na grafu, »14 točk pod izhodiščem«, naslednji pregled čez 30 dni, predvajanje pravkar posnete seje ob seji iz izhodišča in preklop **Sledenje | Vaje s kamero** s pravkar opravljeno vajo v »Zadnje seje«.

Pacientka z obema meritvama v padcu je Ana Potočnik (»Nujno«): njen okvir opozorila pokaže sledenje in vaje s kamero hkrati.

Koliko površno? Opozorilo se sproži, če je povprečna ocena treh stopenj pod približno 67 (skrbno sledenje z miško dobi okoli 92, vidno površno okoli 50). Skrben samopregled opozorila ne sproži in pacientu pove, da je šlo bolje. Pri kameri: ena slaba vaja ne sproži ničesar; dve vaji z oceno blizu nič bi pri Ivanu sprožili »Nujno«.

Pred vsakim snemanjem: zdravnikov pogled → **Ponastavi demo podatke** (`POST /api/admin/reset`). Ponastavi se tudi ob vsakem zagonu backenda.

## Telefon

Aplikacija je po novem najprej za namizje, na telefonu pa ostane uporabna. Za telefon v istem omrežju: `ipconfig getifaddr en0`, nato `https://<IP>:5173` (potrdi opozorilo o potrdilu).

## Vaje s kamero

Po sledenju samopregled nadaljuje z vajami pred kamero: **Dlan** (21 s), nato **Roke v stran** in **Dvig rok** (po 42 s), ki ju pacient lahko preskoči. Brez kamere ali brez dovoljenja se vaje s kamero preskočijo in samopregled se vseeno zaključi.

- Kamera v brskalniku deluje na `http://localhost` in prek HTTPS; na `http://<IP>` ne.
- Iz brskalnika gredo samo točke gibanja (MediaPipe), video ne zapusti naprave.
- Točkuje Primoževa koda s pravili (`backend/models/camera/`, most `backend/app/services/camera_model.py`): posnetek se primerja z zdravo referenco. Posnetek s slabo kakovostjo zajema (premalo zaznanih sličic, pod 15 sličic na sekundo) se shrani, a ne šteje v trend.
- Sledenje in vaje s kamero imata vsaka svoj trend; opozorilo lahko sproži katerakoli.
- Razvojni preizkus brez kamere: `?cameraVideo=<url>` igra namesto kamere predvaja video (samo v razvojnem načinu). V `backend/models/data/camera/recordings/` so Primoževi posnetki kot JSON (točke gibanja; berejo jih testi). Videi niso v tej veji; posamezen video dobiš z `git show origin/compvis:backend/models/data/camera/recordings/<ime>.webm > <ime>.webm`.

## Testi

```bash
cd backend && uv run pytest -q
cd frontend && npx tsc -b && npx vitest run && npm run build
./scripts/gen_contract.sh --check   # pogodba API in TS tipi sta usklajena
```

## Sprememba pogodbe API

Uredi `backend/app/models/schemas.py`, nato `./scripts/gen_contract.sh` in commitaj `contracts/openapi.json` ter `frontend/src/client/schema.d.ts`.

## Primožev model

Seje v živo točkuje Primožev model (gradient boosting na 20 značilkah, `backend/models/tracer/artifacts/tracer_gbm.joblib`). Most je `backend/app/services/tracer_model.py`: uporabi njegov `features.py` in naložen model. Če se model ne naloži ali vrže napako, `app/services/scoring.py` tiho preklopi na nadomestni točkovalnik; katera različica je aktivna, pove `GET /api/meta` (`modelVersion`) in kartica »i« pri zdravniku.

Sintetični pacienti imajo ocene iz krivulje zgodbe (ne iz modela), trend in opozorila pa tečejo skozi isto kodo kot v živo.
