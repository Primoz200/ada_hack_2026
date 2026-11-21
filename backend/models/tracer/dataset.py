"""Build (and cache) training arrays from the synthetic GameResult jsonl.

Cache: models/data/tracer_cache.npz with
  X [n, F] features (FEATURE_NAMES), level [n], completed [n], time_ratio [n],
  y [n] noisy score label, y_clean [n] latent score, split [n] (0 train, 1 val, 2 test),
  seq_flat [sum T, C] float16 sequences concatenated, seq_off [n + 1] offsets.
"""
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from features import FEATURE_NAMES, extract_features, preprocess, sequence
from levels import levels_by_number

DATA = Path(__file__).resolve().parents[1] / "data"
_LEVELS = None


def _process(line: str):
    global _LEVELS
    if _LEVELS is None:
        _LEVELS = levels_by_number()
    r = json.loads(line)
    lv = _LEVELS[r["level"]]
    pre = preprocess(r["series"], lv, r["durationMs"])
    f = extract_features(pre, lv, r["completed"])
    return ([f[k] for k in FEATURE_NAMES], r["level"], r["label"]["score"], r["label"]["score_clean"],
            sequence(pre, lv).T.astype(np.float16), f["time_ratio"], f["completed"])


def build(src: Path = DATA / "tracer_synth.jsonl", out: Path = DATA / "tracer_cache.npz", seed: int = 0):
    with src.open(encoding="utf-8") as fh:
        lines = fh.readlines()
    with Pool() as pool:
        rows = pool.map(_process, lines, chunksize=64)
    X, level, y, y_clean, seqs, time_ratio, completed = map(list, zip(*rows))
    level = np.array(level)
    rng = np.random.default_rng(seed)
    split = np.zeros(len(rows), int)
    for lv in np.unique(level):  # 70 / 15 / 15 per level
        idx = rng.permutation(np.nonzero(level == lv)[0])
        n = len(idx)
        split[idx[int(0.70 * n):int(0.85 * n)]] = 1
        split[idx[int(0.85 * n):]] = 2
    np.savez_compressed(
        out, X=np.array(X, np.float32), level=level, y=np.array(y, np.float32), y_clean=np.array(y_clean, np.float32),
        time_ratio=np.array(time_ratio, np.float32), completed=np.array(completed, np.float32), split=split,
        seq_flat=np.concatenate(seqs), seq_off=np.concatenate([[0], np.cumsum([len(s) for s in seqs])]),
        feature_names=np.array(FEATURE_NAMES))
    print(f"cached {len(rows)} attempts -> {out}")


def load(path: Path = DATA / "tracer_cache.npz", rebuild: bool = False) -> dict:
    if rebuild or not path.exists():
        build(out=path)
    with np.load(path) as z:
        return {k: z[k] for k in z.files}


if __name__ == "__main__":
    build()
