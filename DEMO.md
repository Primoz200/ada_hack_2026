# Zagon in snemanje dema

Raziskovalni prototip na sintetičnih podatkih. Vse teče lokalno.

## Zahteve

- `uv` (Python 3.12 si namesti sam), Node 22 + npm.

## Prvi zagon

```bash
cd backend && uv sync
cd ../frontend && npm ci
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
4. Na koncu pacient prebere miren stavek, da gre zadnje dni nekoliko slabše. Nobenega poziva h klicu.
5. »Pogled zdravnika«: Ivan je zdaj **Za pregled**. Na njegovi strani so padec na grafu, »14 točk pod izhodiščem«, naslednji pregled čez 30 dni in predvajanje pravkar posnete seje ob seji iz izhodišča.

Koliko površno? Opozorilo se sproži, če je povprečna ocena treh stopenj pod približno 67 (skrbno sledenje z miško dobi okoli 92, vidno površno okoli 50). Skrben samopregled opozorila ne sproži in pacientu pove, da je šlo bolje.

Pred vsakim snemanjem: zdravnikov pogled → **Ponastavi demo podatke** (`POST /api/admin/reset`). Ponastavi se tudi ob vsakem zagonu backenda.

## Telefon

Aplikacija je po novem najprej za namizje, na telefonu pa ostane uporabna. Za telefon v istem omrežju: `ipconfig getifaddr en0`, nato `https://<IP>:5173` (potrdi opozorilo o potrdilu).

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
