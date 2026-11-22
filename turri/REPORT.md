# Building our backend with turri

*AdaHack 2026, Codeplain technical challenge: "Solve any challenge using turri"

## What we built with turri

Our platform has a FastAPI backend that serves the clinician's triage dashboard and the patient's daily self-check: tracing games, camera exercises and wellbeing ratings, plus trends and alerts (more about it our other pdf and demo). We first wrote it by hand (well, claude did). Then we **rebuilt the whole backend with turri from a single \*\*\*plain specification**, and made it match the hand-written basically one to one.

The ML models (the tracer model and the rule-based camera scorer in `backend/models/`) stay outside the module. The generated code only calls them.

| | |
|---|---|
| Specification | `turri/backend.plain`: only 267 lines |
| Test scenarios | `turri/tests/backend/`: 22 conformance and 8 acceptance scenarios |
| Generated code | `backend_turri/`: about 4,000 lines of app code and 2,400 lines of unit tests, all written by turri |
| Models used | OpenAI GPT on Amazon Bedrock: `gpt-6-astra` (planning, judging which was mostly replaced by claude)  and `gpt-6-luna` (coding) |
| turri runs | 13 regenerations over one night |

## How we worked

1. **Specify.** We described the existing backend in \*\*\*plain: concepts (Patient, GameSession, LevelTrend, Alert, ...), implementation requirements (FastAPI, SQLModel, errors as `{"detail": ...}`, settings from the environment) and one functional spec per behaviour, from `meta-and-pathways` to `demo-history`. Formal artifacts are linked, not transcribed: the OpenAPI contract the React frontend is built against, the demo stories and the tracer levels.
2. **Regenerate unattended.** `turri regenerate backend.plain --build-dir backend_turri` ran without a chat. The planner split the work into pulses, the coding agent wrote code and unit tests, and our own testing scripts (pytest, ruff, mypy) decided pass or fail.
3. **Verify against the original.** We started both backends with the same fixed date and compared every API response field by field (54 endpoints, later 70 with the camera exercises). We also posted 15 real camera recordings through both and compared the scores.
4. **Fix the spec, never the code.** Every difference went back into `backend.plain` as a more precise sentence: exact response fields, week windows, trigger order, random seeds. turri then regenerated only the functional specs that changed.

## Why we decided for this approach
- While we think turri and regeneratable code are a great idea, they are in the starting stages. Thats why we wanted to have a working backend
the original vibecoding way. Claude generating the code. Once we had a working backend, we told Claude, we wanted the thing made in \*\*\*plain and with turri cli. It wrote the \*\*\*plain specs, then used turri to make sure everything worked and turri for code regeneration and everything else that comes with turri
- The world has a LOT of code written and generated, and this is a showcase/POC that some of that code can be rewritten into \*\*\*plain specs 
and regeneratable code.

## Results
- All of the tests we had before, and the ones turri wrote passed. The backend endpoints returned the exact same thing for every request we sent.
- claude and turri made basically the exact same backend, but in \*\*\*plain specs, regenratable. 

## What we learned

- **The comparison loop is the real power.** A reference to diff against (our hand-written backend) turned vague differences into one-line spec fixes. Almost every round lifted the match of the tests: 9 → 40 → 46 → 49 → 54.
- **Conformance tests catch real bugs.** turri's conformance loop found on its own that the generated code misread the camera exercise levels, and fixed it before we did, and even found some bugs that we didn't know we have
- **Data is best stated, not linked as code.** When we linked the demo stories as a Python file, the agent rewrote it and dropped parameters. "Copy verbatim" and even a SHA-256 requirement were ignored. Writing each patient's camera parameters into the spec as plain facts fixed it in one run.

## Reproduce

```bash
cd turri
./run.sh doctor                                   # checks the Bedrock models answer
turri parse backend.plain                         # validates the spec, no model needed
./run.sh regenerate backend.plain --build-dir ../backend_turri
cd ../backend_turri && APP_MODELS_DIR=../backend/models uv run uvicorn app.main:app --port 8000
```

Credentials are never in the repository: `run.sh` loads them from `~/.config/turri/bedrock.env`.
