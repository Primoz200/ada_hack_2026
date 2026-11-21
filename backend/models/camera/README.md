# Camera exercises: recorder + rule-based scoring

No ML. Our own correct recordings = **reference**; a recording is scored 0–100 as % of the reference
(`scoring.py`). Levels: 1 = hand open/close (MediaPipe Hands), 2 = arms out to the side, 3 = arms up (Pose).

## Run
```bash
cd backend/models/camera
./setup_vendor.sh                                   # once: MediaPipe JS/wasm + models -> recorder/vendor/ (gitignored)
~/venvs/ada_models/bin/uvicorn server:app --port 8010
# open http://localhost:8010 in Chrome/Edge (Windows browser works, WSL forwards localhost)
```
Recordings → `backend/models/data/camera/recordings/<id>.json` (+ `.webm`), gitignored.
Button "Ponovno zgradi referenco" (or `python build_reference.py`) → `artifacts/camera_reference.json` and rescoring.
`python plot_recording.py [file.json ...]` → `data/camera/plots/`. Tests: set `CAMERA_DATA_DIR=<tmp>` so nothing touches the real data.

## Recording format (GameResult + extras)
`gameType "camera"`, `level` 1–3, `exercise`, `hand` (tested side), `startedAt`, `durationMs`, `completed`,
`series`: `t` (ms from start), `lm{i}_x/_y/_z` (normalized to the unmirrored video frame), `w{i}_x/_y/_z`
(MediaPipe world coords), pose also `lm{i}_v` (visibility), hand also `handScore`, `handMatch`; `cueT` = beep times.
Missing detection = `null`. `clientMeta`: `videoW/H`, `fpsMeasured`, `mediapipe`, `detector`, `delegate`, ...
`label`: `role` (reference / patient / test), `subject`, `note`. Server adds `id` and `result`
(= `score_camera()` output: `score`, `impairment_class`, `breakdown`, `features`, `quality_ok`, `model_version`).

## Scoring (v0.3, `camera-rules-0.3`)
Principles: **position** is what counts; going **beyond** the reference (higher, wider, tighter fist) is never
penalised; **timing is not scored** (patients may be fast / off-beat), only whether all repetitions were done.
Within the natural healthy variation (reference sd, min. 5 % of the movement span) = full marks.

| exercise | signal | score |
|---|---|---|
| 1 hand | 3D openness = mean fingertip–wrist / palm length (MediaPipe world landmarks, robust to hand tilt) | 85 % position = √(open × close), each per cycle: how far towards the healthy open / fist level; 15 % repetitions |
| 2 arms to the side | shoulder abduction angle vs. trunk axis | 85 % position (each rep peak from healthy rest to healthy top); 15 % repetitions; − up to 20 % trunk lean, − up to 10 % shoulder hiking (beyond healthy) |
| 3 arms up | wrist height above shoulder / shoulder width | same as 2 |

- **Strictness (`ZERO_AT`)**: reaching only 50 % (hand) / 25 % (arms) of the healthy movement already gives
  0 position points, linear up to 100 % (v0.2 started at 0 % → partial hand movements never fell below ~50).
- A repetition counts only if the movement covers ≥ 25 % of the healthy span (noise is not a repetition).
- `quality_ok` = ≥ 80 % frames detected, ≥ 15 fps, (arms) wrist visible at the top. Otherwise don't use in the trend.
- Timing lag / jitter, 2D range, symmetry are in `features` for information only.
- `python validate_scoring.py`: leave-one-out on the references (96–100) and degraded healthy recordings
  (partial opening / closing / smaller angle / trunk lean / faster / dropped frames) → `data/camera/plots/score_validation.jpg`.
  Hand: 60 % of the healthy range ≈ 35–65, 80 % ≈ 77–88, ≥ 90 % ≈ 90+. Arms: 60 % ≈ 50–60, 80 % ≈ 77–93.

### Pravila v besedah (za zdravnika / predstavitev)
- **Dlan:** merimo, kako daleč so konice prstov od zapestja glede na velikost dlani – pri odprti dlani in pri pesti.
  Ocena pove, kolikšen del zdravega giba pacient doseže v obe smeri (odpre in stisne); kdor doseže le polovico
  zdravega giba, dobi 0. Hitrost in ritem ne štejeta.
- **Roke v stran / gor:** merimo kot rame oziroma višino zapestja nad ramo (v širinah ramen, zato razdalja od kamere
  ni pomembna). Ocena pove, kolikšen del zdravega dviga pacient doseže. Višje od reference ni napaka.
  Odbitek, če pacient pri dvigu nagne trup v stran ali dvigne ramo bolj kot zdrav človek.
- 85+ normalno, 65–84 blago, 40–64 zmerno, < 40 hudo zmanjšan gib.
