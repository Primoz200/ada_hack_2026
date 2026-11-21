#!/usr/bin/env bash
# Put MediaPipe Tasks Vision (wasm) and the two landmark models under frontend/public/vendor/mediapipe/
# so the camera game loads them from our own origin (no CDN). Pinned to the version the app imports.
# Run once after `npm ci`; the folder is gitignored (about 25 MB).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/frontend/public/vendor/mediapipe"
PKG="$ROOT/frontend/node_modules/@mediapipe/tasks-vision"
[ -d "$PKG/wasm" ] || { echo "Run 'npm ci' in frontend/ first." >&2; exit 1; }
mkdir -p "$OUT/wasm" "$OUT/models"
cp "$PKG/wasm/"* "$OUT/wasm/"
BASE=https://storage.googleapis.com/mediapipe-models
[ -f "$OUT/models/hand_landmarker.task" ] || curl -sSfL -o "$OUT/models/hand_landmarker.task" \
  "$BASE/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
[ -f "$OUT/models/pose_landmarker_full.task" ] || curl -sSfL -o "$OUT/models/pose_landmarker_full.task" \
  "$BASE/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
node -e "console.log(require('$PKG/package.json').version)" > "$OUT/VERSION"
echo "MediaPipe $(cat "$OUT/VERSION") ready in $OUT"
