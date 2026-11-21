"""Build artifacts/camera_reference.json from our own correct recordings (label.role == "reference").

Per level: "left" / "right" (if recorded) and "any" (both hands pooled, fallback).
Each entry: mean, sd, n of every feature. The sd shows how much a healthy person varies naturally.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from scoring import REFERENCE_FILE, TEST_DIR, measure

RECORDINGS = (Path(TEST_DIR) if TEST_DIR else Path(__file__).resolve().parents[1] / "data" / "camera") / "recordings"


def build(rec_dir=RECORDINGS, out=REFERENCE_FILE, verbose=True):
    groups = defaultdict(list)
    for f in sorted(Path(rec_dir).glob("*.json")):
        r = json.loads(f.read_text())
        if r.get("label", {}).get("role") != "reference":
            continue
        feats, _ = measure(r["level"], r["hand"], r["series"], r["clientMeta"])
        if not feats["quality_ok"]:
            if verbose:
                print(f"skip (bad quality) {f.name}")
            continue
        for key in (r["hand"], "any"):
            groups[(str(r["level"]), key)].append(feats)
    ref = defaultdict(dict)
    for (lv, key), rows in groups.items():
        names = rows[0].keys()
        arr = {k: np.array([np.nan if r[k] is None else r[k] for r in rows], float) for k in names}
        ref[lv][key] = {
            "n": len(rows),
            "mean": {k: float(np.nanmean(v)) if np.isfinite(v).any() else None for k, v in arr.items()},
            "sd": {k: float(np.nanstd(v)) if np.isfinite(v).any() else None for k, v in arr.items()},
        }
        if verbose:
            m = ref[lv][key]["mean"]
            main = "open_range" if "open_range" in m else "top_level"
            print(f"level {lv} {key:5s}: n={len(rows)}  {main}={m[main]:.3f} ± {ref[lv][key]['sd'][main]:.3f}")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(ref, indent=1))
    if verbose:
        print(f"saved {out}")
    return dict(ref)


if __name__ == "__main__":
    build()
