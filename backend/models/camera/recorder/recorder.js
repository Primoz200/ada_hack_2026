// Camera recorder: MediaPipe landmarks (+ optional local video) -> POST /api/camera/recordings -> score.
// Records RAW landmarks every video frame; all features and scoring happen in Python (scoring.py).
import { DrawingUtils, FilesetResolver, HandLandmarker, PoseLandmarker } from "./vendor/vision_bundle.mjs";

const MP_VERSION = "tasks-vision 1.2.3";
const $ = (id) => document.getElementById(id);
const video = $("video"), canvas = $("overlay"), ctx = canvas.getContext("2d");
const draw = new DrawingUtils(ctx);

let EX = {};                 // exercises from the server (exercises.py)
let fileset = null;
const detectors = {};        // "hand" | "pose" -> landmarker
const delegateUsed = {};
let stream = null, running = false, lastVideoTime = -1;
let rec = null;              // active recording state
const recent = [];           // last frames for the frame check: {t, ok}

// ---------- setup ----------
async function init() {
  EX = await (await fetch("/api/camera/exercises")).json();
  for (const [lv, e] of Object.entries(EX)) $("exercise").add(new Option(`${lv} – ${e.name}`, lv));
  $("exercise").onchange = onExerciseChange;
  onExerciseChange();
  fileset = await FilesetResolver.forVisionTasks("vendor/wasm");
  setStatus("pripravljeno", "");
  refreshList();
}

function ex() { return EX[$("exercise").value]; }
function hand() { return document.querySelector("input[name=hand]:checked").value; }
function setStatus(text, cls) { $("status").textContent = text; $("status").className = "pill " + (cls || ""); }

async function onExerciseChange() {
  $("instructions").textContent = ex().instructions;
  if (fileset) await getDetector(ex().detector);
}

async function getDetector(kind) {
  if (detectors[kind]) return detectors[kind];
  setStatus(`nalagam model (${kind}) …`, "warn");
  const opts = (delegate) => kind === "hand"
    ? { baseOptions: { modelAssetPath: "vendor/models/hand_landmarker.task", delegate },
        runningMode: "VIDEO", numHands: 2, minHandDetectionConfidence: 0.5, minTrackingConfidence: 0.5 }
    : { baseOptions: { modelAssetPath: "vendor/models/pose_landmarker_full.task", delegate },
        runningMode: "VIDEO", numPoses: 1, minPoseDetectionConfidence: 0.5, minTrackingConfidence: 0.5 };
  const Cls = kind === "hand" ? HandLandmarker : PoseLandmarker;
  for (const delegate of ["GPU", "CPU"]) {
    try {
      detectors[kind] = await Cls.createFromOptions(fileset, opts(delegate));
      delegateUsed[kind] = delegate;
      break;
    } catch (e) { console.warn(`${kind} ${delegate} failed`, e); }
  }
  setStatus(`model ${kind} (${delegateUsed[kind]})`, "ok");
  return detectors[kind];
}

// ---------- camera + detection loop ----------
$("btnCamera").onclick = async () => {
  if (stream) return;
  stream = await navigator.mediaDevices.getUserMedia({
    video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 }, facingMode: "user" },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  $("btnCamera").disabled = true; $("btnRecord").disabled = false;
  running = true;
  scheduleFrame();
};

function scheduleFrame() {
  if (!running) return;
  if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(onFrame);
  else requestAnimationFrame(onFrame);
}

async function onFrame() {
  if (video.currentTime !== lastVideoTime && video.readyState >= 2) {
    lastVideoTime = video.currentTime;
    const kind = ex().detector;
    const det = detectors[kind] || (fileset && await getDetector(kind));
    if (det) {
      const now = performance.now();
      const res = det.detectForVideo(video, now);
      const frame = kind === "hand" ? pickHand(res) : pickPose(res);
      drawFrame(kind, frame);
      trackQuality(now, !!frame);
      if (rec && rec.phase === "rec") pushFrame(kind, now - rec.t0, frame);
      if (rec) updatePrompt(now);
    }
  }
  scheduleFrame();
}

function pickHand(res) {
  if (!res.landmarks || !res.landmarks.length) return null;
  const want = hand() === "left" ? "Left" : "Right";  // MediaPipe: subject's hand, not the image side
  let i = res.handedness.findIndex((h) => h[0] && h[0].categoryName === want);
  const match = i >= 0 ? 1 : 0;
  if (i < 0) i = 0;
  return { lm: res.landmarks[i], world: res.worldLandmarks[i], score: res.handedness[i][0]?.score ?? null, match };
}

function pickPose(res) {
  if (!res.landmarks || !res.landmarks.length) return null;
  return { lm: res.landmarks[0], world: res.worldLandmarks[0] };
}

function drawFrame(kind, frame) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!frame) return;
  const conns = kind === "hand" ? HandLandmarker.HAND_CONNECTIONS : PoseLandmarker.POSE_CONNECTIONS;
  draw.drawConnectors(frame.lm, conns, { color: "#4fc3f7", lineWidth: 3 });
  draw.drawLandmarks(frame.lm, { color: "#ffffff", fillColor: "#1f5fbf", radius: 4, lineWidth: 1 });
}

function trackQuality(now, ok) {
  recent.push({ t: now, ok });
  while (recent.length && now - recent[0].t > 1500) recent.shift();
  if (recent.length < 5) return;
  const fps = (recent.length - 1) / ((recent.at(-1).t - recent[0].t) / 1000);
  const det = recent.filter((r) => r.ok).length / recent.length;
  const good = det >= 0.9 && fps >= 15;
  $("frameCheck").innerHTML =
    `<span class="${good ? "ok" : "bad"}">${good ? "✔ kader OK" : "✖ kader ni OK"}</span> · ` +
    `${fps.toFixed(0)} fps · zaznano ${(det * 100).toFixed(0)} %` +
    (ex().detector === "hand" ? "" : " · zgornji del telesa naj bo v celoti viden");
}

// ---------- recording ----------
let audio = null;
function beep(atAudioTime, freq, dur = 0.12) {
  const o = audio.createOscillator(), g = audio.createGain();
  o.frequency.value = freq; o.connect(g); g.connect(audio.destination);
  g.gain.setValueAtTime(0.0001, atAudioTime);
  g.gain.exponentialRampToValueAtTime(0.3, atAudioTime + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, atAudioTime + dur);
  o.start(atAudioTime); o.stop(atAudioTime + dur + 0.02);
}

function newSeries(kind) {
  const n = kind === "hand" ? 21 : 33;
  const s = { t: [] };
  for (let i = 0; i < n; i++) {
    for (const a of ["x", "y", "z"]) { s[`lm${i}_${a}`] = []; s[`w${i}_${a}`] = []; }
    if (kind === "pose") s[`lm${i}_v`] = [];
  }
  if (kind === "hand") { s.handScore = []; s.handMatch = []; }
  return s;
}

const r5 = (v) => (v == null || Number.isNaN(v) ? null : Math.round(v * 1e5) / 1e5);

function pushFrame(kind, t, f) {
  const s = rec.series;
  s.t.push(Math.round(t * 10) / 10);
  const n = kind === "hand" ? 21 : 33;
  for (let i = 0; i < n; i++) {
    const p = f ? f.lm[i] : null, w = f ? f.world[i] : null;
    s[`lm${i}_x`].push(p ? r5(p.x) : null); s[`lm${i}_y`].push(p ? r5(p.y) : null); s[`lm${i}_z`].push(p ? r5(p.z) : null);
    s[`w${i}_x`].push(w ? r5(w.x) : null); s[`w${i}_y`].push(w ? r5(w.y) : null); s[`w${i}_z`].push(w ? r5(w.z) : null);
    if (kind === "pose") s[`lm${i}_v`].push(p ? r5(p.visibility) : null);
  }
  if (kind === "hand") { s.handScore.push(f ? r5(f.score) : null); s.handMatch.push(f ? f.match : null); }
}

$("btnRecord").onclick = async () => {
  const e = ex(), kind = e.detector;
  await getDetector(kind);
  audio = audio || new AudioContext();
  await audio.resume();
  lockUi(true);
  $("result").innerHTML = '<span class="muted">snemam …</span>';
  const cues = Array.from({ length: e.n_cues }, (_, k) => 1000 * (e.first_cue_s + k * e.cue_period_s));
  rec = { phase: "countdown", ex: e, level: Number($("exercise").value), hand: hand(), kind, cues,
          countdownEnd: performance.now() + 3000, series: newSeries(kind), chunks: [] };
  const a0 = audio.currentTime;
  for (let k = 0; k < 3; k++) beep(a0 + k, 440);
  setTimeout(startRecording, 3000);
};

function startRecording() {
  if (!rec || rec.phase !== "countdown") return;
  const e = rec.ex;
  rec.phase = "rec";
  rec.t0 = performance.now();
  rec.startedAt = new Date().toISOString();
  const a0 = audio.currentTime;
  for (const c of rec.cues) {
    beep(a0 + c / 1000, e.up_s ? 880 : 1000);
    if (e.up_s) beep(a0 + c / 1000 + e.up_s, 520);
  }
  if ($("saveVideo").checked) {
    const mime = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"].find((m) => MediaRecorder.isTypeSupported(m));
    rec.recorder = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 2_500_000 } : {});
    rec.recorder.ondataavailable = (ev) => ev.data.size && rec.chunks.push(ev.data);
    rec.recorder.start(1000);
  }
  rec.timer = setTimeout(() => finish(true), e.duration_s * 1000);
}

function updatePrompt(now) {
  const p = $("prompt"), bar = $("progress").firstElementChild;
  if (rec.phase === "countdown") { p.textContent = Math.ceil((rec.countdownEnd - now) / 1000) || ""; return; }
  const e = rec.ex, t = now - rec.t0;
  bar.style.width = `${Math.min(100, (100 * t) / (e.duration_s * 1000))}%`;
  if (!e.up_s) {  // hand: ODPRI around each beep (beep = fully open), stisni in between
    const w = 1000 * (e.open_window_s ?? 0.5);
    const first = rec.cues[0], last = rec.cues.at(-1);
    if (t < first - w || t >= last + w) { p.textContent = "mirno"; return; }
    const near = rec.cues.some((c) => t >= c - w && t < c + w);
    p.textContent = near ? "ODPRI" : "stisni";
    return;
  }
  if (t < rec.cues[0]) { p.textContent = "mirno"; return; }
  const k = Math.floor((t - rec.cues[0]) / (1000 * e.cue_period_s));
  const since = t - rec.cues[Math.min(k, rec.cues.length - 1)];
  p.textContent = k >= rec.cues.length ? "mirno" : since < e.up_s * 1000 ? `GOR ${k + 1}/${e.n_cues}` : "dol";
}

$("btnStop").onclick = () => finish(false);
$("btnCancel").onclick = () => { stopRecorder(); resetRec(); $("result").innerHTML = '<span class="muted">preklicano</span>'; };

function stopRecorder() {
  if (!rec) return Promise.resolve();
  clearTimeout(rec.timer);
  if (!rec.recorder || rec.recorder.state === "inactive") return Promise.resolve();
  return new Promise((res) => { rec.recorder.onstop = res; rec.recorder.stop(); });
}

function resetRec() {
  rec = null; lockUi(false);
  $("prompt").textContent = ""; $("progress").firstElementChild.style.width = "0";
}

async function finish(completed) {
  if (!rec || rec.phase !== "rec") return resetRec();
  rec.phase = "saving";
  const durationMs = Math.round(performance.now() - rec.t0);
  await stopRecorder();
  const s = rec.series, kind = rec.kind;
  s.cueT = rec.cues;
  const dts = s.t.slice(1).map((v, i) => v - s.t[i]).sort((a, b) => a - b);
  const result = {
    gameType: "camera",
    level: rec.level,
    exercise: rec.ex.key,
    hand: rec.hand,
    startedAt: rec.startedAt,
    durationMs,
    completed,
    series: s,
    clientMeta: {
      inputDevice: "camera",
      canvasW: video.videoWidth, canvasH: video.videoHeight,
      videoW: video.videoWidth, videoH: video.videoHeight,
      devicePixelRatio: window.devicePixelRatio,
      userAgent: navigator.userAgent,
      fpsMeasured: dts.length ? Math.round(10000 / dts[Math.floor(dts.length / 2)]) / 10 : 0,
      mediapipe: MP_VERSION,
      detector: kind === "hand" ? "hand_landmarker" : "pose_landmarker_full",
      delegate: delegateUsed[kind],
      mirroredPreview: true,
    },
    label: { role: $("role").value, subject: $("subject").value.trim(), note: $("note").value.trim() },
  };
  const fd = new FormData();
  fd.append("meta", new Blob([JSON.stringify(result)], { type: "application/json" }), "meta.json");
  if (rec.chunks.length) fd.append("video", new Blob(rec.chunks, { type: "video/webm" }), "video.webm");
  $("result").innerHTML = '<span class="muted">shranjujem in točkujem …</span>';
  resetRec();
  try {
    const r = await fetch("/api/camera/recordings", { method: "POST", body: fd });
    if (!r.ok) throw new Error(await r.text());
    showResult(await r.json());
  } catch (err) {
    $("result").innerHTML = `<span class="bad">napaka pri shranjevanju: ${err.message}</span>`;
  }
  refreshList();
}

function lockUi(on) {
  for (const id of ["exercise", "role", "subject", "note", "saveVideo", "btnRecord"]) $(id).disabled = on;
  document.querySelectorAll("input[name=hand]").forEach((el) => (el.disabled = on));
  $("btnStop").disabled = !on; $("btnCancel").disabled = !on;
}

// ---------- results + list ----------
const fmt = (v) => (v == null ? "–" : Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(3));

function showResult(r) {
  const f = r.features || {};
  const q = r.quality_ok ? '<span class="ok">kakovost OK</span>' : '<span class="bad">slaba kakovost – ne šteje v trend</span>';
  let html = `<div class="muted">${r.id}</div>`;
  if (r.score == null) html += `<p>${r.note || "brez ocene"} · ${q}</p>`;
  else {
    html += `<div class="score">${r.score.toFixed(0)}</div><div>${r.impairment_class} · ${q}</div>`;
    html += "<h2 style='margin-top:12px'>Razčlenitev</h2>";
    for (const [k, v] of Object.entries(r.breakdown)) {
      html += `<div>${k} ${(v * 100).toFixed(0)} %</div><div class="bar"><div style="width:${v * 100}%"></div></div>`;
    }
  }
  html += "<h2 style='margin-top:12px'>Značilke</h2><table>";
  for (const [k, v] of Object.entries(f)) html += `<tr><td>${k}</td><td>${fmt(v)}</td></tr>`;
  $("result").innerHTML = html + "</table>";
}

async function refreshList() {
  const rows = await (await fetch("/api/camera/recordings")).json();
  const ref = await (await fetch("/api/camera/reference")).json();
  $("refInfo").textContent = Object.keys(ref).length
    ? "referenca: " + Object.entries(ref).map(([lv, d]) => `${lv}: ` + Object.entries(d).map(([k, v]) => `${k} n=${v.n}`).join(", ")).join(" | ")
    : "referenca še ni zgrajena – posnemi nekaj posnetkov z vlogo »reference« in klikni »Ponovno zgradi referenco«";
  const tb = $("list").tBodies[0];
  tb.innerHTML = "";
  for (const r of rows) {
    const tr = tb.insertRow();
    tr.innerHTML = `<td>${r.id}</td><td>${r.label.role || ""}</td><td>${r.score == null ? "–" : r.score.toFixed(0)}</td>` +
      `<td>${r.quality_ok ? "OK" : '<span class="bad">slaba</span>'}</td><td>${r.video ? "✔" : ""}</td>`;
    const td = tr.insertCell(), b = document.createElement("button");
    b.textContent = "izbriši"; b.className = "ghost";
    b.onclick = async () => { if (confirm(`Izbrišem ${r.id}?`)) { await fetch(`/api/camera/recordings/${r.id}`, { method: "DELETE" }); refreshList(); } };
    td.append(b);
  }
}

$("btnRefresh").onclick = refreshList;
$("btnRebuild").onclick = async () => {
  const r = await (await fetch("/api/camera/reference/rebuild", { method: "POST" })).json();
  setStatus("referenca zgrajena", "ok");
  console.log(r);
  refreshList();
};

init().catch((e) => { console.error(e); setStatus("napaka: " + e.message, "bad"); });
