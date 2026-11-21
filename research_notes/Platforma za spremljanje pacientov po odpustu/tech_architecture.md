# Technical architecture and stack choices for a 20-hour demo build (patient portal + clinician dashboard + browser motor-assessment games)

All versions and terms below were checked on **2026-11-21** against package registries and official pages unless marked otherwise. "Measured" means I downloaded the npm tarball and measured file sizes myself. Items I could not verify this session are listed under *Gaps* and must not be treated as facts.

---

## 1. Frontend stack: Next.js vs Vite + React + router vs SvelteKit; Tailwind; component kit

### Takeaway
Least risky for this job is a **client-only SPA: Vite 8 + React 19 + TypeScript + React Router 8 (declarative or data mode) + Tailwind CSS 4 + shadcn/ui**, built to static files. The games (canvas, webcam + MediaPipe, device sensors, WebSocket) are all browser-only, the backend is a separate FastAPI service, and nothing in the demo needs SSR; Next.js App Router works but adds a server/client boundary that every game component has to be pushed across.

### Cited Findings

**Current versions (registry, 2026-11-21)**
- `next` 16.4.6 (published 2026-11-09), peer React `^18.2.0 || ^19.0.0` — [npm registry](https://registry.npmjs.org/next)
- `react` 19.3.1 (2026-10-14) — [npm registry](https://registry.npmjs.org/react)
- `vite` 8.3.8 (2026-11-11) — [npm registry](https://registry.npmjs.org/vite)
- `react-router` 8.5.2 (2026-11-18), peer **React >= 19.2.7** (so it cannot be paired with React 18) — [npm registry](https://registry.npmjs.org/react-router)
- `@tanstack/react-router` 1.170.46 (2026-10-22), peer React >= 18 — [npm registry](https://registry.npmjs.org/@tanstack/react-router)
- `@sveltejs/kit` 3.4.0 (2026-11-18), peers `vite ^8.0.12`, `svelte ^5.57.1`; `svelte` 5.59.1 (2026-11-20) — [npm registry](https://registry.npmjs.org/@sveltejs/kit), [npm registry](https://registry.npmjs.org/svelte)
- `tailwindcss` 4.3.5 and `@tailwindcss/vite` 4.3.5 (2026-11-06); the Vite plugin's peer range covers Vite 5.2 through 8 — [npm registry](https://registry.npmjs.org/tailwindcss), [npm registry](https://registry.npmjs.org/@tailwindcss/vite)
- `shadcn` CLI 4.23.0 (2026-10-27) — [npm registry](https://registry.npmjs.org/shadcn)
- `@tanstack/react-query` 5.108.2 (2026-11-20), peer React 18 or 19; `zustand` 5.1.0 (2026-11-06) — [npm registry](https://registry.npmjs.org/@tanstack/react-query), [npm registry](https://registry.npmjs.org/zustand)

**Vite**
- Vite docs show v8.3.7, require Node.js 20.19+ or 22.12+, and state that the production build bundles with Rolldown — [vite.dev/guide](https://vite.dev/guide/)
- Scaffold: `npm create vite@latest`, or with a template flag in the form `npm create vite@latest my-app -- --template <name>` (the page's example uses `vue`; `react-ts` is a listed template, so `-- --template react-ts` follows the documented pattern but was not shown verbatim) — [vite.dev/guide](https://vite.dev/guide/)

**Next.js 16**
- Minimum Node.js 20.9; `create-next-app@latest --yes` defaults to TypeScript, Tailwind CSS, ESLint, App Router, Turbopack, alias `@/*`, and generates an `AGENTS.md` for coding agents (docs lastUpdated 2026-10-02) — [nextjs.org installation](https://nextjs.org/docs/app/getting-started/installation)
- Turbopack is the default bundler for dev and build; webpack requires `--webpack`. `next build` no longer runs the linter since v16. The interactive "recommended defaults" also enable "Cache Components" — [nextjs.org installation](https://nextjs.org/docs/app/getting-started/installation)
- The `next` package ships its docs under `node_modules/next/dist/docs/`, so agents can read version-matched documentation — [nextjs.org installation](https://nextjs.org/docs/app/getting-started/installation)
- SSR pitfall: `next/dynamic` with `ssr: false` is only permitted inside Client Components; using it in a Server Component produces an error telling you to move it into a Client Component. Client Components are prerendered on the server by default (docs lastUpdated 2026-03-10) — [nextjs.org lazy loading](https://nextjs.org/docs/app/guides/lazy-loading)

**React Router 8**
- Three additive modes: Declarative (`<BrowserRouter>`), Data (`createBrowserRouter` + `<RouterProvider>`, adds loaders/actions), Framework (Vite plugin, typed route modules, SPA/SSR/static strategies). The docs recommend Declarative for the simplest setup or when a separate data layer already handles pending states — [reactrouter.com modes](https://reactrouter.com/start/modes)

**SvelteKit 3**
- Putting `export const ssr = false` in the root `+layout.js` renders the whole app only on the client (SPA); with `ssr` false the server sends an empty shell — [svelte.dev page options](https://svelte.dev/docs/kit/page-options)

**Tailwind CSS 4 + shadcn/ui on Vite**
- One-step scaffold: `pnpm dlx shadcn@latest init -t vite` (add `--monorepo` for a monorepo layout); presets from shadcn/create use `init --preset [CODE] --template vite` — [ui.shadcn.com Vite install](https://ui.shadcn.com/docs/installation/vite)
- Manual path on an existing Vite project: `pnpm add tailwindcss @tailwindcss/vite`; replace `src/index.css` with the single line `@import "tailwindcss";`; add `baseUrl`/`paths` (`@/*` → `./src/*`) to both `tsconfig.json` and `tsconfig.app.json`; `pnpm add -D @types/node`; register `react()` and `tailwindcss()` plugins plus the `@` alias in `vite.config.ts`; then `pnpm dlx shadcn@latest init` — [ui.shadcn.com Vite install](https://ui.shadcn.com/docs/installation/vite)
- Add components with `pnpm dlx shadcn@latest add button`; import from `@/components/ui/button` — [ui.shadcn.com Vite install](https://ui.shadcn.com/docs/installation/vite)
- shadcn's `chart` component is built on **Recharts v3**; install with `pnpm dlx shadcn@latest add chart`; colours are referenced as `var(--chart-1)` (not `hsl(var(--chart-1))`), and `ChartContainer` needs a height / `min-h-*` / `aspect-*` class so the responsive container can measure — [ui.shadcn.com chart](https://ui.shadcn.com/docs/components/chart)

**Tremor (alternative kit)**
- `@tremor/react` latest is 3.18.7, last published **2025-01-13**, with peer `react ^18.0.0` — [npm registry](https://registry.npmjs.org/@tremor/react)
- Tremor's install page states React 18.2+ and Tailwind CSS 3.4+ and carries a "joining Vercel" banner; it says nothing about React 19 or Tailwind 4 — [npm.tremor.so installation](https://npm.tremor.so/docs/getting-started/installation)

### Inferences
- **Recommended:** Vite + React 19.3 + TS + React Router 8 (declarative `<BrowserRouter>` with ~8 routes) + TanStack Query for server state + Tailwind 4 + shadcn/ui. Reasons: (1) no server render pass exists, so `window`, `navigator.mediaDevices`, `DeviceMotionEvent`, WebGL and WASM imports cannot crash a prerender; (2) output is a static `dist/` that can go to any static host **or be served by FastAPI itself**, which collapses the system to one origin (no CORS, one HTTPS URL for desktop, phone and WebSocket); (3) Primož's game components are plain React components with no `'use client'` / dynamic-import ceremony.
- **Next.js 16** is viable if Matevž is already fluent in it, but every game must be a Client Component loaded through `dynamic(..., { ssr: false })` from another Client Component, and module-level access to browser globals inside any imported file still breaks prerender. With a separate FastAPI backend, Server Components/Server Actions give no benefit here, and "Cache Components" in the default preset is one more behaviour to understand under time pressure.
- **SvelteKit 3** is technically fine in SPA mode, but it would force Primož to write the games in Svelte and loses shadcn/ui (React) and Recharts; with two people sharing one repo and AI agents that are strongest on React, it is the higher-risk option for this team.
- Because React Router 8 requires React >= 19.2.7 and Tremor's npm package pins React 18, **Tremor's npm package is a dead end** for a new React 19 / Tailwind 4 project; use shadcn's chart component (Recharts 3) instead.
- Tailwind 4 has no `tailwind.config.js` step in the documented shadcn flow (CSS-first `@import "tailwindcss"`); AI agents frequently generate Tailwind 3 setup (`npx tailwindcss init`, `@tailwind base;`), which should be rejected.
- Keep MediaPipe and the phone-controller page behind `React.lazy()` route-level code splitting so the dashboard bundle stays small.

### Gaps
- I did not verify whether shadcn's current default primitive library is Radix or Base UI; doc URLs now include `/components/base/…`, `/radix/…` and `/aria/…` variants, which implies a choice at init time — check the `init` prompt ([ui.shadcn.com chart, base variant](https://ui.shadcn.com/docs/components/base/chart)).
- Vite dev-server details I rely on from memory and did **not** re-verify: `server.proxy` with `ws: true` for proxying `/api` and `/ws` to FastAPI in dev, and `server.allowedHosts` needing the tunnel hostname when the dev server is exposed through ngrok/cloudflared. Verify in the Vite config reference before relying on them.
- Did not verify TanStack Router's current file-based routing setup; not needed if React Router declarative mode is used.

---

## 2. Charting for the clinician dashboard

### Takeaway
Use **Recharts 3 through shadcn/ui's `chart` component** for all dashboard charts (trend line, baseline band, alert markers, sparklines); it is React-native, React 19 compatible, and has first-class `ReferenceArea` / `ReferenceLine` / `ReferenceDot`. Reserve a canvas library (uPlot or plain `<canvas>`) only for replaying raw 60 Hz traces.

### Cited Findings
- `recharts` 3.11.0 (2026-11-17); peers React 16.8–19; runtime dependencies now include `@reduxjs/toolkit`, `react-redux`, `immer`, `reselect`, `es-toolkit`, `victory-vendor` — [npm registry](https://registry.npmjs.org/recharts), [tarball](https://registry.npmjs.org/recharts/-/recharts-3.11.0.tgz)
- Measured full UMD build of Recharts 3.11.0: 685,611 bytes raw / 180,424 bytes gzip (whole library, not tree-shaken) — [tarball](https://registry.npmjs.org/recharts/-/recharts-3.11.0.tgz)
- `ReferenceArea` takes `x1/x2/y1/y2` in data coordinates (omit an edge to extend to the plot boundary), `ifOverflow` (`discard` default, `hidden`, `visible`, `extendDomain`), `label`, `fill`, and `zIndex` (since Recharts 3.4); it works inside Line/Area/Bar/Composed/Scatter charts — [recharts ReferenceArea API](https://recharts.github.io/api/ReferenceArea)
- Recharts publishes a 3.0 migration guide — [recharts wiki](https://github.com/recharts/recharts/wiki/3.0-migration-guide)
- shadcn `chart` uses Recharts v3 and lists v3-specific notes (CSS variable form, `ChartTooltip.defaultIndex`, drop duplicate `layout` on `<Bar>`) — [ui.shadcn.com chart](https://ui.shadcn.com/docs/components/chart)
- `echarts` 6.1.0 (2026-05-19), Apache-2.0; measured `echarts.min.js` 1,121,883 raw / 367,915 gzip; `echarts.common.min.js` 715,020 / 239,503; `echarts.simple.min.js` 500,315 / 168,869 — [npm registry](https://registry.npmjs.org/echarts), [tarball](https://registry.npmjs.org/echarts/-/echarts-6.1.0.tgz)
- `echarts-for-react` 3.1.0 (2026-11-17), peers `echarts ^3–^6`, React `^15 || >=16` — [npm registry](https://registry.npmjs.org/echarts-for-react)
- `chart.js` 4.6.1 (2026-10-22); measured `chart.umd.min.js` 210,082 raw / 70,902 gzip. `react-chartjs-2` 5.3.1 (last published 2025-10-27), peers `chart.js ^4.1.1`, React 16.8–19 — [npm registry](https://registry.npmjs.org/chart.js), [npm registry](https://registry.npmjs.org/react-chartjs-2), [tarball](https://registry.npmjs.org/chart.js/-/chart.js-4.6.1.tgz)
- `@observablehq/plot` 0.6.19 (2026-11-05), ISC licence; measured `plot.umd.min.js` 211,860 raw / 69,454 gzip — [npm registry](https://registry.npmjs.org/@observablehq/plot), [tarball](https://registry.npmjs.org/@observablehq/plot/-/plot-0.6.19.tgz)
- `@visx/visx` and `@visx/xychart` 4.0.0 (2026-06-11), peers React 18 or 19 — [npm registry](https://registry.npmjs.org/@visx/visx), [npm registry](https://registry.npmjs.org/@visx/xychart)
- `uplot` 1.6.32 (last published 2025-03-14); measured `uPlot.iife.min.js` 51,081 raw / 22,009 gzip — [npm registry](https://registry.npmjs.org/uplot), [tarball](https://registry.npmjs.org/uplot/-/uplot-1.6.32.tgz)
- `@tremor/react` 3.18.7, last publish 2025-01-13, peer React 18 only — [npm registry](https://registry.npmjs.org/@tremor/react)

### Inferences
- Comparison for this job:

| Library | React fit | Baseline band / alert markers | Sparkline | Size (measured, full build gzip) | AI-codegen risk |
|---|---|---|---|---|---|
| Recharts 3.11 (via shadcn chart) | Native JSX, React 19 OK | `ReferenceArea` (band), `ReferenceLine` (threshold), `ReferenceDot` (alert) | `LineChart` with no axes in a small fixed-size box | ~180 KB | Low, but agents often emit Recharts 2 idioms; point them at the v3 migration guide and shadcn notes |
| ECharts 6.1 | Wrapper (`echarts-for-react`) or manual `useEffect` | `markArea` / `markLine` / `markPoint` in option object | Possible, verbose | ~169–368 KB | Medium: large option objects, v5→v6 drift |
| Chart.js 4.6 | Wrapper last published a year ago | Needs annotation plugin | OK | ~71 KB | Medium |
| Observable Plot 0.6 | Imperative (returns a DOM node) | Rule/rect marks | Good | ~69 KB (+ d3) | Medium: needs an effect wrapper |
| visx 4 | Low-level primitives | Hand-built | Hand-built | modular | High effort for 20 h |
| Tremor npm | React 18 only | — | has spark components | — | Do not use |

- Trend chart recipe (one `ComposedChart`): raw scores as faint dots, EWMA as the main line, baseline ± tolerance as a `ReferenceArea` (y1/y2), alert threshold as a dashed `ReferenceLine`, alert dates as `ReferenceDot`, missing days left as gaps (`connectNulls={false}`), questionnaire score on a second Y axis.
- Patient-list sparklines: 20+ Recharts instances in a table are acceptable at demo scale; if it stutters, render sparklines as a hand-written inline SVG `<polyline>` (15 lines of code, zero dependencies).
- Raw 60 Hz series (a 30 s game = ~1,800 points per channel) are fine in Recharts if animation is disabled and dots are off; uPlot is the fallback if several channels are overlaid.

### Gaps
- The sizes above are whole-library builds; tree-shaken sizes in a Vite/Rolldown build will be smaller and were not measured (bundlephobia was unreachable from my environment).
- Did not verify the current version/compatibility of `chartjs-plugin-annotation`, ECharts `markArea` API details in v6, or whether Plot's UMD bundle externalises d3.
- Did not verify whether Recharts 3 line props such as `connectNulls`, `isAnimationActive`, `dot` are unchanged from v2; check the API pages before generating code.

---

## 3. MediaPipe in the browser (Hand Landmarker / Pose Landmarker)

### Takeaway
Use **`@mediapipe/tasks-vision` 1.2.3** (note the jump from 0.10.x to 1.x; most tutorials are for 0.10), load it only in the browser, **self-host the WASM folder and `.task` models from your own origin**, run in `VIDEO` mode inside a `requestAnimationFrame` loop held in refs, and keep a CPU-delegate fallback for Safari/iOS.

### Cited Findings
- `@mediapipe/tasks-vision` `latest` = 1.2.3 (published 2026-11-11), Apache-2.0; a `nightly` dist-tag publishes daily release candidates (currently `1.3.0-rc.20261121`) — [npm registry](https://registry.npmjs.org/@mediapipe/tasks-vision)
- Package contents (measured): `vision_bundle.mjs` ~156 KB; `wasm/vision_wasm_internal.wasm` 14.67 MB and `wasm/vision_wasm_module_internal.wasm` 14.67 MB, each with a ~337 KB JS loader; ESM package (`"type": "module"`) with `exports` for the bundle and the four wasm files; unpacked size ~31.4 MB — [tarball](https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-1.2.3.tgz)
- Official web guide (last updated 2026-11-20): `npm install @mediapipe/tasks-vision`; resolve WASM with `FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm")`; create with `HandLandmarker.createFromOptions(vision, { baseOptions: { modelAssetPath, delegate: "GPU" }, runningMode, numHands })` — [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
- Running modes on web are `IMAGE` (default, `detect(image)`) and `VIDEO` (`detectForVideo(frame, timestampMs)` with monotonic timestamps); for a live webcam the sample calls `detectForVideo(video, performance.now())` from `requestAnimationFrame` whenever `video.currentTime` has advanced — [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
- Hand defaults: `numHands` 1; `minHandDetectionConfidence`, `minHandPresenceConfidence`, `minTrackingConfidence` all 0.5 — [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
- Hand result: per hand, 21 normalised `landmarks` (x,y in 0–1, z relative to wrist), 21 `worldLandmarks` in metres (origin at hand centre), and handedness categories. The guide's note names the web field `handednesses` while its samples use `handedness` — log the object once and check. Handedness is the subject's hand; a mirrored input flips it — [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
- Model location: the guide now links `hand_landmarker.task` to Hugging Face (`huggingface.co/litert-community/MediaPipe-HandLandmarker-Full/resolve/main/hand_landmarker.task`), while the README inside the 1.2.3 npm package still uses `storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task` — [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js), [tarball README](https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-1.2.3.tgz)
- Pose Landmarker (page updated 2026-11-20): `PoseLandmarker.createFromOptions(vision, { baseOptions: { modelAssetPath: "pose_landmarker_lite.task", delegate: "GPU" }, runningMode, numPoses })`; three bundles Lite / Full / Heavy (float16; detector input 224×224, landmarker input 256×256) hosted under `huggingface.co/litert-community/MediaPipe-PoseLandmarker-{Lite,Full,Heavy}`; defaults `numPoses` 1, three confidence thresholds 0.5, `outputSegmentationMasks` false; result is 33 landmarks (normalised and world, each with `visibility` and `presence`); web supports only `IMAGE` and `VIDEO` modes — [Pose Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/web_js)
- Licence: package Apache-2.0; guide code samples Apache-2.0, page text CC BY 4.0 — [npm registry](https://registry.npmjs.org/@mediapipe/tasks-vision), [Hand Landmarker web guide](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
- Known open issue: with the GPU delegate on iOS Safari (iOS 18.7.1, package 0.10.22-rc), Image Segmenter returned scrambled category masks while the CPU delegate on the same device and GPU on desktop were correct; a maintainer acknowledged it; still open — [mediapipe issue #6142](https://github.com/google-ai-edge/mediapipe/issues/6142)
- Known open issue: calling `handLandmarker.close()` froze the browser (reported on 0.10.0 with GPU delegate; maintainer asked to retest on a newer version; unresolved) — [mediapipe issue #5718](https://github.com/google-ai-edge/mediapipe/issues/5718)
- Next.js-specific: a component importing MediaPipe must be client-only (`ssr: false` from a Client Component) — [nextjs.org lazy loading](https://nextjs.org/docs/app/guides/lazy-loading)

### Inferences
- **Pin and self-host.** Copy `node_modules/@mediapipe/tasks-vision/wasm/` into `public/mediapipe/wasm/` (a postinstall script) and download the `.task` files into `public/models/`; pass `"/mediapipe/wasm"` and `"/models/hand_landmarker.task"`. This removes three demo risks at once: the docs' `@latest` CDN path drifting away from the installed npm version, the model host having moved (Google Cloud Storage → Hugging Face), and venue Wi-Fi blocking a CDN. If a CDN is used anyway, pin `@1.2.3` in the URL.
- **COOP/COEP is not needed**: the package ships only two single-threaded WASM builds (no threaded variant), so `SharedArrayBuffer` and cross-origin isolation headers should not be required. This is an inference from the file list, not a documented statement.
- **React pattern:** one `useEffect` that (a) calls `getUserMedia({ video: { width: 640, height: 480 } })`, (b) awaits `FilesetResolver` + `createFromOptions` once, storing the landmarker in a `useRef`, (c) runs the rAF loop writing landmarks to a ref / drawing on a canvas, and (d) on cleanup cancels rAF and stops media tracks. Never put per-frame landmarks into React state. In React 19 dev StrictMode effects run twice, so guard initialisation with a ref/promise; given issue #5718, prefer a module-level singleton that is created once and never `close()`d during the demo.
- Wrap creation in try/catch and retry with `delegate: "CPU"`; force CPU on iOS Safari if results look wrong (issue #6142 pattern).
- Use the ~15 MB WASM + model download as a visible "loading model…" state and preload it when the patient opens the game menu.
- Mirror the video with CSS (`transform: scaleX(-1)`) for display only; feed the un-mirrored frame to MediaPipe and swap handedness labels in code.
- For kinematic features use `worldLandmarks` (metres) for amplitudes and normalised `landmarks` for on-screen overlay; record `performance.now()` per frame because webcam frame rate (typically 30 fps) — not the display's 60 Hz — bounds the sampling rate.
- The legacy packages `@mediapipe/hands` / `@mediapipe/pose` (the "Solutions" API) appear in a lot of AI-generated code; reject them in favour of the Tasks API above.

### Gaps
- **Typical FPS on a laptop: no reliable current source found.** Neither landmarker guide publishes web latency benchmarks. Measure on the actual demo laptop in hour 1.
- I could not confirm that either model URL (Hugging Face or `storage.googleapis.com`) currently returns the file — both were blocked from my sandbox. Download them once from a normal network and commit/self-host.
- Model file sizes are not given on the guide pages.
- Found no current primary-source statement about Vite 8/Rolldown or Turbopack bundling problems with tasks-vision 1.x; untested.
- No documented statement found confirming COOP/COEP is unnecessary (see inference).

---

## 4. Phone-as-controller pairing (QR → WebSocket relay) and device sensors

### Takeaway
The fastest reliable design is a **FastAPI WebSocket relay with in-memory rooms**: the desktop shows a QR code containing `https://<host>/controller?s=<sessionId>`, the phone opens it, taps a "Start" button (which calls `requestPermission()` on iOS), and streams batched sensor samples over `wss://` to FastAPI, which forwards them to the desktop socket in the same room. It needs no third-party account and reuses the backend you already have; WebRTC/PeerJS adds NAT/signalling failure modes for no benefit at demo scale.

### Cited Findings
- `DeviceMotionEvent.requestPermission()` takes no arguments, resolves to `"granted"` or `"denied"`, and rejects with `NotAllowedError` if the permission state is "prompt" and the call lacks transient activation (i.e. it must be called from a UI event such as a click). It is secure-context only and marked "Limited availability", so feature-detect with `typeof DeviceMotionEvent.requestPermission === "function"` and attach the listener only after "granted" — [MDN requestPermission](https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/requestPermission_static)
- The W3C spec marks the device orientation/motion event handlers and interfaces `[SecureContext]`, and applies the same user-activation rule to both `DeviceOrientationEvent.requestPermission()` and `DeviceMotionEvent.requestPermission()` — [W3C DeviceOrientation Event spec (2022 WD)](https://www.w3.org/TR/2022/WD-orientation-event-20220919/)
- Units: `acceleration` and `accelerationIncludingGravity` in m/s², `rotationRate` in deg/s, precision no finer than 0.1; orientation angles alpha [0,360), beta [-180,180), gamma [-90,90). The spec fixes no event rate; `interval` is the hardware sampling interval in milliseconds and must be constant — [W3C DeviceOrientation Event spec (2022 WD)](https://www.w3.org/TR/2022/WD-orientation-event-20220919/), [MDN interval](https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/interval)
- Chromium caps sensor sampling at 60 Hz for most sensor types (10 Hz for ambient light and magnetometer) — [Chromium generic_sensor README](https://chromium.googlesource.com/chromium/src.git/+show/HEAD/services/device/generic_sensor/README.md)
- iOS Safari: a 2015 WebKit change raised DeviceOrientation event emission from 20 Hz to 1/60 s (~60 Hz) — [WebKit bug 145814](https://bugs.webkit.org/show_bug.cgi?id=145814)
- FastAPI WebSockets: install the `websockets` package; declare `@app.websocket("/ws/{id}")`, `await websocket.accept()`, loop on `receive_text()/receive_json()`, catch `WebSocketDisconnect`; path and query parameters and `Depends` work as in HTTP routes; raise `WebSocketException` rather than `HTTPException` — [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- FastAPI's in-memory `ConnectionManager` pattern only works within a single running process; for multi-process the docs point to `encode/broadcaster` — [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- `websockets` 17.4 (2026-10-30), `uvicorn` 0.54.0 (2026-09-25) — [PyPI](https://pypi.org/pypi/websockets/json), [PyPI](https://pypi.org/pypi/uvicorn/json)
- `qrcode.react` 4.2.0 (last published 2024-12-11), peers React 16.8–19 — [npm registry](https://registry.npmjs.org/qrcode.react)
- Alternatives: Supabase Realtime free plan allows 200 concurrent connections, 100 messages/s, 100 channels per connection, 256 KB broadcast payload; exceeding the message rate disconnects clients — [Supabase Realtime limits](https://supabase.com/docs/guides/realtime/limits)
- `peerjs` 1.5.5 was last published 2025-06-07; the `partykit` npm CLI 0.0.115 was last published 2025-05-21 — [npm registry](https://registry.npmjs.org/peerjs), [npm registry](https://registry.npmjs.org/partykit)

### Inferences
- **Effective sample rate is ~60 Hz on both Android Chrome and iOS Safari** (Chromium's cap; WebKit's 1/60 s interval). Do not assume it: read `event.interval` and timestamp every sample (`event.timeStamp` / `performance.now()`), then resample to a fixed grid on the backend before feature extraction.
- **Message design:** phone buffers samples and sends one JSON frame every ~50 ms (`{t0, dt, samples:[[ax,ay,az,gx,gy,gz,rα,rβ,rγ,α,β,γ], …]}`) → 20 messages/s instead of 60, far less sensitive to jitter; the desktop renders from the latest sample and appends everything to the raw series it will POST at the end of the game. Use `accelerationIncludingGravity` as the primary channel (plain `acceleration` can be null on some devices).
- **Server:** `rooms: dict[str, dict[str, WebSocket]]` keyed by session ID with roles `desktop` / `phone`; one endpoint `/ws/pair/{session_id}?role=phone|desktop`; forward phone → desktop; send `{"type":"peer_joined"}` / `peer_left` so the desktop UI can show "phone connected". Run **exactly one uvicorn worker** (and one instance on any PaaS) because rooms live in process memory.
- **iOS flow:** the controller page must open on a full-screen "Tap to start" button; its click handler calls `DeviceMotionEvent.requestPermission()` and `DeviceOrientationEvent.requestPermission()` (when present), then opens the WebSocket. If the user denies, iOS will not re-prompt in that page session; show instructions to reload. In-app browsers that open QR links (camera app is fine) may behave differently — test with the real demo phone.
- Also request a Screen Wake Lock on the phone and add a ping every ~15–20 s so idle proxies do not drop the socket; add automatic reconnect with the same session ID.
- The QR URL must be the **public HTTPS origin**, not `localhost`; derive it from `window.location.origin` so it works unchanged on PaaS and behind a tunnel.
- **Why not the alternatives:** WebRTC data channels/PeerJS need signalling plus STUN/TURN and fail on some conference/hospital networks; hosted realtime (Supabase Realtime, Ably, Liveblocks, PartyKit) would work but adds an account, keys and a second moving part, and Supabase's free 100 msg/s cap is close to an unbatched 60 Hz stream. They only become attractive if the backend host cannot do WebSockets — and all shortlisted hosts can.
- Latency over a same-region relay is typically tens of milliseconds, adequate for tilt control; if the game needs tight timing, compute kinematic features from the phone's own timestamps, not arrival times.

### Gaps
- No primary source found for the **current** `devicemotion` rate on iOS Safari specifically (the WebKit bug is from 2015 and concerns DeviceOrientation), nor for Android Chrome's DeviceMotion path (the Chromium README states the 60 Hz cap for sensors generally and does not mention DeviceMotion). Measure on the demo phones.
- Did not verify current free-tier terms for Ably, Liveblocks or PartyKit/Cloudflare; only Supabase Realtime limits were checked.
- Did not verify iOS behaviour after a denied permission prompt or in in-app browsers from a primary source.

---

## 5. HTTPS hosting for the demo (FastAPI + SQLite + WebSockets + frontend)

### Takeaway
Most demo-proof: **one process, one origin** — FastAPI serves the built SPA, the REST API and the WebSocket — deployed to one always-reachable host (a small paid PaaS instance or a VPS with Caddy), with the SQLite file **re-seeded deterministically at startup** so disk persistence does not matter; plus a rehearsed **local fallback**: the same process on a laptop exposed through a tunnel with a stable HTTPS URL (ngrok free dev domain or a Cloudflare named tunnel).

### Cited Findings

**Frontend hosting**
- Vercel Hobby (docs updated 2026-11-12) is free and includes 100 GB Fast Data Transfer, 1,000,000 function invocations, 4 CPU-hours Active CPU, 100 deployments/day, 200 projects and a 300 s function maximum duration; exceeding a limit generally means waiting up to 30 days — [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)

**Backend PaaS**
- Render free web services: spin down after 15 minutes without inbound traffic; wake-up takes about a minute; filesystem is ephemeral (lost on redeploy, restart or spin-down) and persistent disks are not available on free; WebSockets are supported, and messages on an existing WebSocket count as activity (an idle open socket does not); 750 free instance-hours per workspace per month; Render may restart a free service at any time; custom domains and managed TLS are included — [Render free docs](https://render.com/docs/free)
- Railway: Free plan = $1 of usage per month, no card, for apps that can sleep; Trial = one-time $5 credit; Free/Trial per-service limits 0.5–1 GB RAM and **0.5 GB volume**; Hobby = $5/month including $5 usage, 5 GB volumes; extra volume storage $0.15/GB/month — [Railway pricing plans](https://docs.railway.com/pricing/plans)
- Fly.io: free trial is $1 of credit for 7 days without a card; **trial Machines stop automatically after running 5 minutes**; adding a card lifts trial limits and months billed under $5 are waived; trial allows up to 20 GB of volumes — [Fly.io free trial](https://docs.fly.io/about/free-trial)
- Koyeb: one free web service per organisation (512 MB RAM, 0.1 vCPU, 2 GB SSD; Frankfurt or Washington DC); a credit card with a temporary $29 pre-authorisation is required; Pro is $29/month — [Koyeb pricing FAQ](https://www.koyeb.com/docs/faqs/pricing)
- Koyeb free instances always scale to zero after 1 hour without traffic (not configurable); deep-sleep cold starts take about 1–5 s; an open WebSocket prevents scale-down, and a WebSocket can wake a sleeping service but that connection may only last a few minutes — [Koyeb scale-to-zero](https://www.koyeb.com/docs/run-and-scale/scale-to-zero)
- Google Cloud Run (page updated 2026-11-18): WebSockets work without extra configuration; they are subject to the request timeout (default 5 min, max 60 min), so clients must reconnect; session affinity is best-effort; instances do not share state, so multi-instance setups need an external pub/sub; an instance with an open WebSocket is billed as active — [Cloud Run WebSockets](https://docs.cloud.google.com/run/docs/triggering/websockets)
- Hugging Face Spaces: CPU Basic hardware (2 vCPU, 16 GB RAM, 50 GB non-persistent disk) is listed as free and sleeps when unused, **but Gradio and Docker Spaces now require a paid plan to create (PRO for personal accounts); only static Spaces are free for everyone** — [HF Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview)
- User reports (no staff statement in the thread) date this Spaces change to around July 2026; most pre-existing free Spaces reportedly kept running — [HF forum thread](https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703)

**VPS**
- Caddy reverse proxy with automatic HTTPS is a two-line Caddyfile (`example.com` + `reverse_proxy :9000`) or `caddy reverse-proxy --from example.com --to :9000`; requires the domain's DNS to point at the machine and ports 80/443 open — [Caddy reverse-proxy quick start](https://caddyserver.com/docs/quick-starts/reverse-proxy)

**Tunnels (laptop fallback)**
- Cloudflare Quick Tunnel: `cloudflared tunnel --url http://localhost:8080`, no account or DNS setup, random `trycloudflare.com` subdomain, hard limit of 200 in-flight requests (HTTP 429 beyond), no Server-Sent Events, no uptime guarantee, will not start if a `config.yaml` exists in `.cloudflared` — [Cloudflare TryCloudflare docs](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- ngrok free plan: one automatically assigned dev domain that persists across restarts; 1 GB data transfer and 20,000 HTTP requests per month; 4,000 requests/min; up to 3 endpoints; endpoints have no session timeout; an interstitial warning page is shown before HTML browser traffic (clicking "Visit" suppresses it for 7 days per domain; a `ngrok-skip-browser-warning` request header bypasses it; API calls are unaffected) — [ngrok free plan limits](https://ngrok.com/docs/pricing-limits/free-plan-limits)
- A June 2026 comparison recommends Cloudflare named tunnels (own domain on Cloudflare) for durable free URLs and ngrok for the fastest first URL; also lists Tailscale Funnel (ports 443/8443/10000, `ts.net` hostname) and VS Code Dev Tunnels (5 GB/user/month, `devtunnels.ms`) — [MerginIT tunnel comparison, 2026-06-19](https://merginit.com/blog/19062026-free-developer-tunnels-comparison)

**CORS**
- An origin is scheme + host + port; FastAPI's `CORSMiddleware` takes `allow_origins`, `allow_origin_regex`, `allow_methods` (default `["GET"]`), `allow_headers`, `allow_credentials`; wildcards cannot be combined with `allow_credentials=True` — [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)

### Inferences
- **Recommended topology (single origin):** `vite build` → copy `dist/` into the backend image → FastAPI mounts it as static files with an SPA fallback, serves `/api/*` and `/ws/*`. One HTTPS URL then covers desktop, phone QR link and `wss://`; no CORS, no mixed-content, no env-specific API base URL; and the tunnel fallback needs to expose just one port.
- **Where to run it (ranked for demo reliability):**
  1. *Small paid always-on instance* (Railway Hobby $5, Fly.io with a card — sub-$5 months waived, or Render's cheapest paid instance): no cold start, WebSockets fine. Set instance count to 1.
  2. *VPS + Caddy*: most control and no platform quirks, but needs a domain and ~30–45 min setup; good if someone already has a server.
  3. *Render free*: workable because (a) the DB is re-seeded on boot so the ephemeral disk is harmless, and (b) WebSocket messages keep it awake — but the ~1 minute cold start means someone must open the site a few minutes before presenting, and Render can restart it at any time.
  4. *Koyeb free*: 1–5 s cold starts are attractive, but 0.1 vCPU is likely too weak for importing scikit-learn/torch and the card hold applies.
  5. *Cloud Run*: fine for WebSockets with `max-instances=1` and a long request timeout, but the container filesystem and GCP setup overhead make it slower to get right in 20 h.
  - **Avoid:** Fly.io *without* a card (machines stop after 5 minutes), Hugging Face Spaces (Docker Spaces are no longer free), Vercel for the backend (see Gaps), any multi-instance/autoscaled setting.
- **If the frontend is hosted separately on Vercel** (e.g. for preview deploys), set `VITE_API_URL`, add `CORSMiddleware` with the exact Vercel origin(s) or an `allow_origin_regex` for preview URLs, and remember WebSockets are not subject to CORS but must use `wss://`. This is strictly more moving parts than single-origin.
- **SQLite:** treat the file as disposable. On startup: if `DEMO_RESET=1` or the file is missing, create tables and run the deterministic seeder. New sessions recorded during the demo live until the next restart, which is fine. A "Reset demo data" button (POST `/api/admin/reset`) is worth 15 minutes.
- **Local fallback (rehearse it):** `uvicorn app.main:app --port 8000` serving the built SPA + `ngrok http 8000` (stable dev domain → the QR code and bookmarks never change; tap through the interstitial once on the demo phone beforehand) *or* `cloudflared tunnel --url http://localhost:8000` (no interstitial, but the URL changes on every start). The desktop browser can use `http://localhost:8000` for webcam/mouse games (localhost is a secure context), but the QR code must carry the tunnel's public origin — make the public base URL an env var (`PUBLIC_BASE_URL`) that overrides `window.location.origin` for QR generation.
- ngrok's 20,000 HTTP requests/month is easily consumed by aggressive polling (a dashboard refetching every 2 s uses ~1,800 requests/hour); disable refetch intervals when running through ngrok.
- Last-resort fallback: a 90-second screen recording of the full flow, including the phone game.
- **Production would differ:** Postgres instead of SQLite, real authentication/authorisation and audit logging, EU-region hosting and GDPR/health-data compliance, Redis (or similar) pub/sub for multi-instance WebSockets, object storage for raw series, migrations (Alembic), monitoring.

### Gaps
- Neither the Cloudflare Quick Tunnel page nor the ngrok free-plan page states WebSocket support explicitly; I could not verify it from a primary page this session, and I do not know whether ngrok counts WebSocket traffic against its HTTP request quota. **Test the phone game through the chosen tunnel on day 1.**
- Not verified: Vercel Hobby's non-commercial clause and Vercel's WebSocket support for functions (the fetched Hobby page lists quotas only); Cloud Run's current free-tier allowances; Render's current paid starter price; Koyeb volume support on free instances; current VPS prices (e.g. Hetzner).
- Hugging Face's Spaces restriction has no dated official announcement that I could find; the docs state the rule, the timing comes from forum users.
- The Railway page did not state the Free plan's sleep trigger or whether WebSockets keep a service awake.

---

## 6. Backend structure (FastAPI, ORM, typed client, ML serving, trend recomputation)

### Takeaway
**FastAPI 0.165 + SQLModel 0.0.50 (on SQLAlchemy 2.1) + Pydantic 2.14 on Python 3.12/3.13**, with the OpenAPI schema as the contract and a generated TypeScript client (**Hey API `@hey-api/openapi-ts`**, the generator FastAPI's own docs recommend; `openapi-typescript` + `openapi-fetch` is the lighter alternative). Load ML models once at startup and recompute a patient's trend synchronously whenever a session is saved.

### Cited Findings
- `fastapi` 0.165.0 (2026-11-18, Python >= 3.11); `starlette` 1.10.0 (2026-10-24); `pydantic` 2.14.4 (2026-11-19); `uvicorn` 0.54.0 — [PyPI fastapi](https://pypi.org/pypi/fastapi/json), [PyPI starlette](https://pypi.org/pypi/starlette/json), [PyPI pydantic](https://pypi.org/pypi/pydantic/json), [PyPI uvicorn](https://pypi.org/pypi/uvicorn/json)
- `sqlmodel` 0.0.50 (2026-11-13, Python >= 3.11); `sqlalchemy` 2.1.9 (2026-11-16); `alembic` 1.20.1; `aiosqlite` 0.22.1 — [PyPI sqlmodel](https://pypi.org/pypi/sqlmodel/json), [PyPI sqlalchemy](https://pypi.org/pypi/sqlalchemy/json), [PyPI alembic](https://pypi.org/pypi/alembic/json), [PyPI aiosqlite](https://pypi.org/pypi/aiosqlite/json)
- `scikit-learn` 1.9.1 (2026-09-10); `torch` 2.15.0 (2026-10-28); `onnxruntime` 1.32.0 (2026-11-13); `pandas` 3.1.1; **`numpy` 2.5.5 requires Python >= 3.12** — [PyPI scikit-learn](https://pypi.org/pypi/scikit-learn/json), [PyPI torch](https://pypi.org/pypi/torch/json), [PyPI onnxruntime](https://pypi.org/pypi/onnxruntime/json), [PyPI pandas](https://pypi.org/pypi/pandas/json), [PyPI numpy](https://pypi.org/pypi/numpy/json)
- FastAPI's SQL tutorial uses SQLModel (built on SQLAlchemy and Pydantic) with SQLite: `create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})`, a `get_session` generator dependency aliased as `SessionDep = Annotated[Session, Depends(get_session)]`, `SQLModel.metadata.create_all(engine)` at startup, and the multi-model pattern (`XBase`, `X(table=True)`, `XPublic`, `XCreate`, `XUpdate`); it suggests Alembic for production migrations — [FastAPI SQL databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- FastAPI's client-generation guide recommends **Hey API** for TypeScript and shows `npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/client`; generated code is grouped by route `tags`; it recommends a custom `generate_unique_id_function` (e.g. `f"{route.tags[0]}-{route.name}"`) so method names are clean, optionally stripping the tag prefix from operation IDs in a preprocessing script — [FastAPI generate clients](https://fastapi.tiangolo.com/advanced/generate-clients/)
- `@hey-api/openapi-ts` 0.99.0 (published 2026-06-22; still 0.x); `openapi-typescript` 7.13.0 and `openapi-fetch` 0.17.0 (both 2026-02-11); `orval` 8.48.0 (2026-11-14) — [npm registry hey-api](https://registry.npmjs.org/@hey-api/openapi-ts), [npm registry openapi-typescript](https://registry.npmjs.org/openapi-typescript), [npm registry openapi-fetch](https://registry.npmjs.org/openapi-fetch), [npm registry orval](https://registry.npmjs.org/orval)
- FastAPI dev server is started with `fastapi dev` (docs use `uv run fastapi dev`) — [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

### Inferences
- **SQLModel vs plain SQLAlchemy 2:** SQLModel is faster for this build because one class is both table and Pydantic schema, and it is the pattern in FastAPI's own tutorial (so agents reproduce it accurately). It is still 0.0.x; drop to SQLAlchemy `Column(JSON)` via `sa_column` for JSON fields and to raw SQLAlchemy for anything awkward. Skip Alembic: `create_all` + reseed.
- **Never return table models directly**; define `…Public` response models so the OpenAPI schema (and therefore the TS client) is explicit and stable. Give every route a tag and an explicit `response_model`; use `Literal`/`Enum` for `impairment_class`, `severity`, `status`, `game_type` so the TS types are unions.
- **Contract pipeline:** add a script that dumps `app.openapi()` to `contracts/openapi.json` without running the server, commit that file, and have the frontend run `openapi-ts -i ../contracts/openapi.json -o src/client` in `predev`/`prebuild`. A diff in `openapi.json` in a PR is the signal that the contract changed.
- **Generator choice:** Hey API gives a ready SDK (and optional TanStack Query helpers) with one command and is what the FastAPI docs show; because it is 0.x and moves fast, **pin the exact version**. If it misbehaves, `openapi-typescript` (types only) + `openapi-fetch` (tiny typed `fetch`) is the simplest fallback with the least generated code. Orval is the most actively released and can also generate MSW mocks, at the cost of more configuration.
- **ML serving:** load `joblib` scikit-learn pipelines / the 1D-CNN once in the app lifespan and keep them on `app.state`; expose a single `score_session(game_type, raw_series) -> {features, score, impairment_class, level, model_version}` function behind `POST /api/sessions`; use plain `def` (not `async def`) endpoints for CPU-bound scoring. A full `torch` install makes images and cold starts heavy — export the CNN to ONNX and serve with `onnxruntime`, or install the CPU-only torch wheel; on a 512 MB free instance torch may not fit at all. Always store `model_version` with each score.
- **A deterministic fallback scorer** (weighted features → 0–100) behind the same function signature lets Matevž integrate before the real models exist and is a safety net if a model fails to load on the host.
- **Trend recomputation:** per patient × game, the series is a few dozen points, so recompute baseline (median of first N sessions), EWMA, rolling slope and alert rule **synchronously in the same request** that stores the session, then upsert `trend_snapshot` and open/close alerts. No queue, no scheduler. FastAPI `BackgroundTasks` is the next step up if scoring becomes slow.
- Python 3.12 or 3.13 is the safe interpreter choice given NumPy's floor.

### Gaps
- Did not verify from the docs this session: the current recommended startup hook (the SQL tutorial summary showed an `on_event("startup")` example; `lifespan` is what I would expect to be preferred — check), `BackgroundTasks` semantics, and the rule that `def` endpoints run in a threadpool.
- Did not fetch Hey API's own documentation (configuration file, client packages, TanStack Query plugin names) — only the command shown in FastAPI's docs and the npm version are verified.
- Did not verify SQLModel's current JSON-column idiom or its compatibility notes with SQLAlchemy 2.1.
- Did not verify current torch CPU-wheel install instructions or sizes.

---

## 7. Data model and loose FHIR mapping

### Takeaway
A dozen relational tables are enough; name them and their status fields so they read as FHIR-shaped (Patient, Observation, QuestionnaireResponse, CarePlan, Flag, Task) and state in the pitch that the model is "FHIR-aligned, not FHIR-conformant".

### Cited Findings
- FHIR R5 defines **Flag** as a prospective warning of potential issues when providing care to the patient; it is meant for a small set of high-priority issues that deserve prominent display, can condense information from Observation/Condition and link to it; key elements: `status` (active | inactive | entered-in-error), `category`, `code` (the message), `subject`, `period`, `author`; maturity level 1 (trial use) — [HL7 FHIR R5 Flag](https://www.hl7.org/fhir/flag.html)
- Boundaries stated on the Flag page: **DetectedIssue** is for warnings about a reported or proposed action (e.g. drug–drug interaction, duplicate therapy), and **Communication / CommunicationRequest** is for conveying information to a specific individual or organisation; neither is what Flag is for — [HL7 FHIR R5 Flag](https://www.hl7.org/fhir/flag.html)
- The R4 resource index page identifies itself as FHIR v4.0.1 and notes that 5.0.0 supersedes it — [HL7 FHIR R4 resource list](https://hl7.org/fhir/R4/resourcelist.html)
- SQLite via SQLModel/SQLAlchemy is the pattern in FastAPI's tutorial — [FastAPI SQL databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### Inferences
**Pragmatic schema (SQLite; JSON columns as TEXT/JSON)**

| Table | Key columns | FHIR-ish analogue |
|---|---|---|
| `patient` | id, mrn, given_name, family_name, birth_date, sex, discharge_date, primary_condition_id, avatar, active | Patient |
| `clinician` | id, name, role, specialty | Practitioner / PractitionerRole |
| `condition` | id, patient_id, code, display (e.g. "stroke, right hemiparesis"), onset_date, affected_side | Condition |
| `care_plan` | id, patient_id, clinician_id, title, status (active/completed), start_date, end_date | CarePlan |
| `care_plan_activity` | id, care_plan_id, kind (game/questionnaire), game_type or questionnaire_id, frequency_per_week, target_level | CarePlan.activity / ServiceRequest (patient-facing to-dos ≈ Task) |
| `questionnaire` | id, code, title, version, items JSON `[{linkId, text, type, options, scoring}]` | Questionnaire |
| `questionnaire_response` | id, patient_id, questionnaire_id, authored_at, answers JSON `[{linkId, value}]`, total_score | QuestionnaireResponse (+ derived Observation for the total) |
| `game_session` | id, patient_id, care_plan_activity_id, game_type (trace/camera/phone), level, started_at, duration_ms, device_info JSON, input_meta JSON (sample rate, hand, screen size), status (completed/aborted), score (0–100), impairment_class, model_version, features JSON | Observation (code = assessment type, valueInteger = score, `component[]` = features, `interpretation` = class, `device` = input device) |
| `session_raw` | session_id (PK/FK), format, sample_rate_hz, n_samples, payload BLOB (gzip JSON or columnar arrays) | Observation.valueSampledData or an Attachment/Binary referenced from the Observation |
| `trend_snapshot` | id, patient_id, metric (game_type or questionnaire), computed_at, as_of_date, n_sessions, baseline, ewma, slope_per_week, pct_change_vs_baseline, adherence_7d, state (improving/stable/declining/insufficient_data), params JSON | derived Observation (`derivedFrom` the session Observations); conceptually close to RiskAssessment when it expresses risk |
| `alert` | id, patient_id, metric, rule_code, severity (info/warning/critical), status (open/acknowledged/resolved/dismissed), opened_at, trigger_snapshot_id, evidence JSON (session ids, values), acknowledged_by, acknowledged_at, note | **Flag** (status active/inactive, code = message, period, author = system) with supporting detail in a derived Observation |
| `alert_action` / `message` | id, alert_id or patient_id, clinician_id, kind (note/call/plan_change/message), text, created_at | Task (clinician follow-up) and Communication (message to patient) |
| `llm_summary` (optional) | id, patient_id, week_start, input_hash, model, output JSON, created_at | Composition / DocumentReference (narrative), clearly marked as AI-generated |

- **Flag is the right analogue for alerts, not DetectedIssue**: the alert is a persistent, prominently displayed warning about the patient, not a warning attached to a proposed order. Mention DetectedIssue only as "considered and rejected" — that nuance itself adds credibility.
- Keep raw series out of the main row (`session_raw` 1:1 table) so list endpoints never load blobs; store features as JSON plus two or three promoted numeric columns for anything charted directly.
- Store `as_of_date`-keyed trend snapshots (one per patient × metric × day with a session) rather than only the latest value: it makes the trend chart a single query and lets the demo show "what the system knew on day X".
- Credibility extras that cost minutes: a `GET /api/patients/{id}/fhir-preview` endpoint returning one hand-built FHIR-style JSON bundle (Patient + two Observations + Flag), and code fields shaped as `{system, code, display}` even if codes are local.
- Indexes: `(patient_id, started_at)` on `game_session`, `(patient_id, metric, as_of_date)` on `trend_snapshot`, `(status, severity)` on `alert`.

### Gaps
- Only the Flag page (R5) was read this session. The mappings to Observation (`component`, `valueSampledData`, `derivedFrom`, `interpretation`), Questionnaire/QuestionnaireResponse, CarePlan, Task, Communication, RiskAssessment and Condition are from my prior knowledge of FHIR and were **not re-verified** against hl7.org — check element names before putting them on a slide.
- The R4 resource index page did not expose per-resource summaries to my fetch, so R4-vs-R5 differences for these resources were not checked.
- No source consulted for clinically validated alert thresholds; the alert rule parameters are a product decision.

---

## 8. Synthetic longitudinal demo data

### Takeaway
A ~100-line seeded generator (parametric recovery curve + autocorrelated noise + scripted events + random missing days) run at startup is sufficient and reproducible; generate *features first* and derive scores with the same scoring function the live system uses so charts, scores and alerts are mutually consistent.

### Cited Findings
- `numpy` 2.5.5 (2026-11-15) and `pandas` 3.1.1 (2026-11-04) are current — [PyPI numpy](https://pypi.org/pypi/numpy/json), [PyPI pandas](https://pypi.org/pypi/pandas/json)
- A free-tier host's filesystem may be wiped on every restart/spin-down (e.g. Render free), which is why seeding at boot matters — [Render free docs](https://render.com/docs/free)

### Inferences
- **Generator design (deterministic):** `rng = np.random.default_rng(seed + patient_index)`; fixed "today" anchor = server date at seed time so histories always end yesterday.
  - *Latent ability* per patient × game: saturating recovery `s(t) = s_inf − (s_inf − s_0)·exp(−t/τ)` with `s_0` 30–55, `s_inf` 70–90, `τ` 10–25 days.
  - *Noise:* AR(1) day-to-day noise (φ ≈ 0.5, σ ≈ 3–5) plus small per-session noise; clip to 0–100.
  - *Missing days:* per-patient adherence probability (0.6–0.95) with lower weekend adherence and one or two multi-day gaps.
  - *Features:* map latent ability to plausible kinematic features (path error ↓, completion time ↓, speed-peak count/jerk ↓, tremor-band power ↓, range of motion ↑) with their own noise, then call the real `score_session`/fallback scorer to get score, class and level. Level progression: raise level after 3 consecutive scores above a threshold.
  - *Questionnaire:* daily items (pain, fatigue, mood, perceived difficulty) loosely anti-correlated with ability plus independent noise; a few skipped days.
- **Scripted archetypes (6–8 patients):** (1) steady recoverer; (2) fast recoverer who plateaus; (3) **slow decliner** — normal recovery for ~3 weeks, then a −1 to −1.5 points/day drift for 8–10 days so the "EWMA below baseline-band for N consecutive sessions" rule fires 2–3 days before "today" (alert open, unacknowledged); (4) abrupt drop with questionnaire pain spike (critical alert already acknowledged with a clinician note); (5) low adherence (adherence alert rather than performance alert); (6) noisy-but-stable (demonstrates that the alert rule does not fire on a single bad day); (7) new patient with too few sessions ("insufficient data" state).
- **Run the real trend/alert code over the synthetic history** day by day during seeding (replay), instead of inserting pre-computed alerts; this both tests the pipeline and guarantees consistency. Assert in a unit test that archetype 3 yields exactly one open alert and archetype 6 yields none.
- Raw series: synthesise only for the most recent 2–3 sessions per patient (e.g. target path + smoothed noise + tremor sinusoid at 4–6 Hz scaled by impairment) so session-replay views work; older sessions keep features only. Keeps the DB small and seeding fast (< 2 s).
- Use obviously fictional names and a visible "synthetic data" badge.
- Keep one "live demo" patient with history up to yesterday so the session played on stage visibly extends the chart; optionally a hidden "simulate next 7 days" button to show an alert firing live.

### Gaps
- No external sources were consulted for this question; everything above is design reasoning, not sourced fact. Recovery-curve shapes and parameter ranges are illustrative and not taken from clinical literature (another researcher's scope).
- Did not verify whether an off-the-shelf generator (e.g. Synthea for FHIR demographics) is worth using; for 6–8 patients hand-written demographics are quicker.

---

## 9. Optional LLM feature: plain-language weekly summary for the clinician

### Takeaway
A weekly summary generated from the structured trend data with **Claude Haiku 5.5 via `client.messages.parse()` and a Pydantic schema** costs a fraction of a cent per patient and is a few lines of code; make it safe by passing only computed facts, constraining the output schema, labelling it AI-generated, and **pre-generating/caching** so the live demo never depends on an API call.

### Cited Findings
- Anthropic structured outputs are stable on the Claude API: send `output_config.format` = `{type: "json_schema", schema: …}`; the Python SDK's `client.messages.parse(..., output_format=PydanticModel)` converts the model, validates the reply and returns `response.parsed_output` (the docs recommend this helper). The docs' curl example uses header `anthropic-version: 2026-10-21` — [Claude structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md)
- Supported models listed include `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-2`, and older ones such as `claude-haiku-4-5-20251001` — [Claude structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md)
- Schema limits: objects need `additionalProperties: false`; no recursive schemas; no numeric `minimum/maximum`, no string length constraints, array `minItems` only 0 or 1; `enum` allowed; use nested Pydantic models rather than free-form `dict` fields (a bare dict becomes an object that can only be `{}`); unsupported features return HTTP 400 — [Claude structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md)
- Pricing per million tokens: Haiku 5.5 $0.10 input / $0.50 output for prompts up to 100k tokens (5× higher above that); Sonnet 5.5 $2 / $10; Opus 5.5 $4 / $20; Fable 5.2 $8 / $40; Batch API is 50% off — [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- SDK versions: Python `anthropic` 2.12.0 (2026-11-20); npm `@anthropic-ai/sdk` 1.12.0; Python `openai` 3.57.0; npm `openai` 7.62.0 — [PyPI anthropic](https://pypi.org/pypi/anthropic/json), [npm registry](https://registry.npmjs.org/@anthropic-ai/sdk), [PyPI openai](https://pypi.org/pypi/openai/json), [npm registry](https://registry.npmjs.org/openai)
- OpenAI equivalent: Responses API with `text.format` = `{type: "json_schema", name, strict: true, schema}`; Python helper `client.responses.parse(..., text_format=PydanticModel)` → `response.output_parsed`; the guide's examples use model `gpt-6.2-astra`; apps must still handle refusals and incomplete responses — [OpenAI structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)

### Inferences
- **Cost:** a weekly summary prompt of ~2,000 input tokens and ~300 output tokens on Haiku 5.5 ≈ 2,000 × $0.10/M + 300 × $0.50/M ≈ **$0.00035 per summary**; even on Sonnet 5.5 it is ≈ $0.007. Cost is irrelevant at demo scale; choose on quality/latency.
- **Implementation sketch:** `POST /api/patients/{id}/summary?week=…` builds a compact JSON of *already computed* facts (sessions done vs planned, per-game baseline/EWMA/slope/% change, alert list with rule codes, questionnaire averages and deltas, missed days), calls `messages.parse` with a `WeeklySummary` Pydantic model — e.g. `headline: str`, `overall_trend: Literal["improving","stable","declining","insufficient_data"]`, `key_points: list[KeyPoint{text, metric, evidence_value}]`, `adherence_note: str`, `suggested_review_items: list[str]` — stores the result in `llm_summary` keyed by a hash of the input, and returns the cached row on repeat calls.
- **Guardrails:**
  1. The model receives numbers the backend computed; it must not compute trends itself. Instruct: use only supplied values; if data are insufficient, say so.
  2. No diagnosis, prognosis or treatment/medication advice; "suggested review items" are prompts for the clinician ("review tremor trend with patient"), not recommendations.
  3. `overall_trend` is **set by the backend's rule engine and passed in**, or validated against it after generation; reject/regenerate on mismatch so narrative can never contradict the chart.
  4. Post-validate that every number in `key_points.evidence_value` exists in the input payload.
  5. UI: "AI-generated draft from structured data — verify against charts", with the model name and timestamp; clinician-facing only (do not show LLM text to patients in the demo).
  6. Send no names or identifiers to the API (use an opaque patient key); with synthetic data this is moot, but say it in the pitch.
  7. Deterministic template fallback (string-formatted summary from the same facts) when the API key is missing or the call fails/times out.
- **Demo reliability:** pre-generate summaries for all seeded patients during seeding (or commit them as fixtures) and show a "Regenerate" button for the live effect.
- Pydantic `Field(ge=…, le=…)`/length constraints do not translate into supported schema constraints; validate ranges in code after parsing.

### Gaps
- Latency for Haiku 5.5 / Sonnet 5.5 was not verified from a primary source; measure once.
- The truncated fetch of the Anthropic page did not reach the section on refusals/`max_tokens` stop reasons with structured outputs; handle `stop_reason` defensively.
- Exact API model ID strings are listed on a separate "Model IDs" page that I did not open; the IDs above are as listed on the structured-outputs page.
- OpenAI pricing and its cheapest current model were not verified; the OpenAI "supported schemas" rules page was not read.

---

## 10. Workflow for two developers with AI coding agents in one repo

### Takeaway
Freeze the API contract in the first 60–90 minutes, commit it as `contracts/openapi.json` with a generated TS client and fixtures, and split ownership by directory so the two agents almost never touch the same files; integrate continuously on `main` behind route-level flags, and rehearse the demo script from hour ~14.

### Cited Findings
- FastAPI generates the OpenAPI schema from routes and models; TypeScript clients can be generated from it with one command, grouped by tags, with stable method names via `generate_unique_id_function` — [FastAPI generate clients](https://fastapi.tiangolo.com/advanced/generate-clients/)
- `msw` (Mock Service Worker) is at 3.0.7 (2026-11-18) with peer `vite >= 6` — [npm registry](https://registry.npmjs.org/msw)
- `orval` 8.48.0 is actively released (2026-11-14) — [npm registry](https://registry.npmjs.org/orval)
- `create-next-app` now generates an `AGENTS.md` to steer coding agents, and Next ships version-matched docs inside the package — evidence that per-repo agent instruction files are now a mainstream convention — [nextjs.org installation](https://nextjs.org/docs/app/getting-started/installation)
- shadcn's CLI supports a `--monorepo` scaffold and running `add` from the app directory or with `-c apps/web` — [ui.shadcn.com Vite install](https://ui.shadcn.com/docs/installation/vite)

### Inferences
- **Repo layout (single repo, no workspace tooling needed):**
  ```
  /backend            FastAPI app (app/main.py, routers/, models/, services/scoring, services/trends, seed/)
  /frontend           Vite app
     src/app/         routes, layouts, role switch            (Matevž)
     src/features/    patient/, clinician/, alerts/           (Matevž)
     src/games/       trace/, camera/, phone/, shared/        (Primož)
     src/client/      generated API client (never hand-edited)
     src/mocks/       fixtures + handlers
  /contracts          openapi.json (committed), fixtures/*.json
  /scripts            export_openapi.py, gen_client.sh, seed.py, dev.sh
  AGENTS.md           conventions, commands, pinned versions, "do not" list
  DEMO.md             demo script + fallback checklist
  ```
- **Game ↔ platform interface (agree in hour 1, then never change):** every game is `<Game sessionConfig={…} onComplete={(result: GameResult) => void} onAbort={…} />` where `GameResult = { gameType, level, startedAt, durationMs, sampleRateHz, series: {...typed arrays as number[]}, clientMeta }`. The platform owns the POST to `/api/sessions` and the results screen. Primož ships a stub game that returns a canned `GameResult` after 3 seconds so Matevž can build the whole flow immediately.
- **Contract-first sequence:** (1) write Pydantic/SQLModel response models and empty routers returning seeded data → (2) export `openapi.json` → (3) generate the client → (4) both proceed. Since the seeded SQLite backend *is* a realistic mock, the frontend can simply run against the local backend; add MSW only if the backend is unstable, or use static JSON fixtures in `contracts/fixtures` consumed by a `VITE_USE_FIXTURES=1` switch.
- **Agent hygiene:** in `AGENTS.md` pin the exact stack (React 19.3, React Router 8 declarative mode, Tailwind 4 CSS-first, shadcn CLI 4, Recharts 3, `@mediapipe/tasks-vision` 1.2.3 Tasks API, FastAPI 0.165, SQLModel, Pydantic v2) and list forbidden legacy patterns (Tailwind 3 config/init, `@mediapipe/hands`, Recharts 2 idioms, Pydantic v1 `.dict()`/`@validator`, `react-router-dom` v5/v6 imports, `@tremor/react`). Tell agents to read docs from `node_modules`/official URLs rather than memory, to never edit `src/client/` or the other developer's directories, and to run `typecheck` + `pytest -q` before finishing.
- **Branching:** trunk-based with very short-lived branches (or direct pushes to `main` with a pre-push typecheck); rebase often; one person owns each of the shared hot files (`backend/app/models`, router registration, `frontend/src/app/routes.tsx`). If both developers run multiple agents, give each agent its own git worktree.
- **Feature flags:** a tiny `flags.ts` reading `VITE_FLAG_*` env vars and a `?flags=` query override: `llmSummary`, `phoneGame`, `cameraGame`, `fhirPreview`. Anything not demo-ready by hour 16 is switched off rather than half-shown.
- **Suggested time budget (per person-hours of 20):** 0–1.5 contract, scaffold, deploy "hello world" to the real host *and* through the tunnel (prove HTTPS + camera + phone sensors + WebSocket end-to-end before building features); 1.5–8 vertical slice (one game → score → patient history → clinician chart); 8–14 remaining games, alerts workflow (acknowledge + note), questionnaire, seed archetypes; 14–17 polish, empty/loading/error states, LLM summary if time; 17–20 freeze, rehearsals, fallback recording.
- **Demo script (≈4 min):** (1) clinician dashboard: patient list with sparklines, one red alert → (2) open the declining patient: baseline band, EWMA crossing, alert evidence, AI weekly summary → acknowledge with note → (3) switch role to patient: today's tasks, 30 s questionnaire → (4) play game 1 (mouse), see score/level → (5) scan QR, play phone game live → (6) back to clinician view: the new session appears on the chart. **Fallback ladder:** hosted URL → laptop + tunnel → laptop on `localhost` with the phone game replaced by a recorded clip → full recording.
- Pre-demo checklist: warm the host 5 minutes before; camera permission pre-granted for the origin; phone on mobile data as backup to venue Wi-Fi with the tunnel/host URL already opened once (ngrok interstitial dismissed, iOS motion permission flow rehearsed); browser zoom and dark/light mode fixed; "Reset demo data" pressed.

### Gaps
- No external engineering sources were consulted on team workflow with AI agents; this section is practical reasoning anchored on the verified tool facts above.
- MSW 3's current setup API was not checked (only the version and peer range).
- The project already contains an `AGENTS.md` document; I did not read it (out of scope), so the conventions suggested here should be merged with whatever it already specifies.
