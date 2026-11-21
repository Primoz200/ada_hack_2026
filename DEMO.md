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

## Telefon

1. Telefon in prenosnik v istem omrežju (če omrežje blokira povezave med napravami, prenosnik poveži na dostopno točko telefona).
2. Poišči IP prenosnika: `ipconfig getifaddr en0`.
3. Na telefonu odpri `https://<IP>:5173` in potrdi opozorilo o potrdilu.
4. Izberi pacienta »Demo« in opravi dnevni vnos ter igro sledenja s prstom.

Alternativa za Android prek USB: `adb reverse tcp:5173 tcp:5173`, nato `https://localhost:5173`.

## Kontrole za demo (zdravnikov pregled, razdelek »Demo«)

- **Ponastavi demo podatke**: vrne začetno stanje (`POST /api/admin/reset`).
- **Simuliraj naslednjih 7 dni**: izbranemu pacientu doda 7 dni s počasnim padcem rezultatov igre, da se sproži rumeno opozorilo; ostali pacienti nadaljujejo svoje zgodbe (`POST /api/admin/simulate`).

## Seznam posnetkov

Po ponastavitvi demo podatkov, po seznamu v `IMPLEMENTATION_PLAN.md`, poglavje 13.

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
