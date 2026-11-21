"""Dev server for the camera recorder: serves the page, saves recordings, scores them.

Run (from backend/models/camera):
    ~/venvs/ada_models/bin/uvicorn server:app --port 8010 --reload
then open http://localhost:8010  (localhost counts as a secure context, so the webcam works).

The real platform (Matevž) will call scoring.score_camera() the same way POST /api/camera/recordings does.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

import build_reference
from exercises import EXERCISES
from scoring import load_reference, score_camera

HERE = Path(__file__).resolve().parent
RECORDINGS = build_reference.RECORDINGS
RECORDINGS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="camera recorder")


def _slug(s):
    return re.sub(r"[^A-Za-z0-9-]+", "-", str(s)).strip("-")[:24] or "x"


@app.get("/")
def index():
    return RedirectResponse("/recorder/index.html")


@app.get("/api/camera/exercises")
def exercises():
    return EXERCISES


@app.post("/api/camera/recordings")
async def save_recording(meta: UploadFile = File(...), video: UploadFile | None = File(None)):
    rec = json.loads(await meta.read())
    for k in ("level", "hand", "series", "clientMeta"):
        if k not in rec:
            raise HTTPException(400, f"missing {k}")
    ex = EXERCISES[int(rec["level"])]
    label = rec.get("label", {})
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    rid = f"{stamp}_{ex['key']}_{rec['hand']}_{_slug(label.get('role', 'test'))}_{_slug(label.get('subject', 'anon'))}"
    rec["id"] = rid
    result = score_camera(rec.get("gameType", "camera"), rec["level"], rec["hand"],
                          rec.get("durationMs", 0), rec["series"], rec["clientMeta"])
    rec["result"] = result
    (RECORDINGS / f"{rid}.json").write_text(json.dumps(rec))
    if video is not None:
        (RECORDINGS / f"{rid}.webm").write_bytes(await video.read())
    return {"id": rid, **result}


@app.get("/api/camera/recordings")
def list_recordings():
    out = []
    for f in sorted(RECORDINGS.glob("*.json"), reverse=True):
        r = json.loads(f.read_text())
        res = r.get("result", {})
        out.append({"id": r["id"], "level": r["level"], "hand": r["hand"], "label": r.get("label", {}),
                    "score": res.get("score"), "quality_ok": res.get("quality_ok"),
                    "video": f.with_suffix(".webm").exists()})
    return out


@app.post("/api/camera/reference/rebuild")
def rebuild_reference():
    """Rebuild the reference from all role=reference recordings, then rescore every saved recording."""
    ref = build_reference.build(verbose=False)
    for f in RECORDINGS.glob("*.json"):
        r = json.loads(f.read_text())
        r["result"] = score_camera(r.get("gameType", "camera"), r["level"], r["hand"], r.get("durationMs", 0),
                                   r["series"], r["clientMeta"], reference=ref)
        f.write_text(json.dumps(r))
    return {lv: {k: v["n"] for k, v in d.items()} for lv, d in ref.items()}


@app.get("/api/camera/reference")
def reference():
    return load_reference()


@app.delete("/api/camera/recordings/{rid}")
def delete_recording(rid: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", rid):
        raise HTTPException(400, "bad id")
    for suf in (".json", ".webm"):
        (RECORDINGS / f"{rid}{suf}").unlink(missing_ok=True)
    return {"deleted": rid}


app.mount("/recorder", StaticFiles(directory=HERE / "recorder"), name="recorder")
