#!/usr/bin/env bash
# Download MediaPipe Tasks Vision (JS + wasm) and the two .task models into recorder/vendor/ (gitignored).
# Served from our own origin, pinned versions (IMPLEMENTATION_PLAN: no CDN @latest).
set -euo pipefail
cd "$(dirname "$0")"
VER=1.2.3
OUT=recorder/vendor
mkdir -p "$OUT/wasm" "$OUT/models"
TMP=$(mktemp -d)
(cd "$TMP" && npm pack "@mediapipe/tasks-vision@$VER" -q >/dev/null && tar xzf "mediapipe-tasks-vision-$VER.tgz")
cp "$TMP/package/vision_bundle.mjs" "$OUT/"
cp "$TMP/package/wasm/"* "$OUT/wasm/"
rm -rf "$TMP"
BASE=https://storage.googleapis.com/mediapipe-models
[ -f "$OUT/models/hand_landmarker.task" ] || curl -sSfL -o "$OUT/models/hand_landmarker.task" \
  "$BASE/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
[ -f "$OUT/models/pose_landmarker_full.task" ] || curl -sSfL -o "$OUT/models/pose_landmarker_full.task" \
  "$BASE/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
echo "$VER" > "$OUT/VERSION"
ls -la "$OUT" "$OUT/models"
