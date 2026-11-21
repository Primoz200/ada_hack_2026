// Raw landmark series, ported key for key from the teammate's recorder (backend/models/camera/recorder).
// The backend scorer reads these keys: one entry per video frame, null for every landmark key when
// nothing was detected, no resampling, no smoothing. Coordinates are as MediaPipe gives them for the
// UNMIRRORED video frame (the preview is mirrored with CSS only).
import type { GameConfig, GameResult } from '../shared/types'
import type { Detector } from './exercises'

export interface Point3 {
  x: number
  y: number
  z: number
  visibility?: number
}

/** One detection picked from a MediaPipe result (see pick.ts). */
export interface Frame {
  lm: readonly Point3[]
  world: readonly Point3[]
  /** hand only: handedness score of the picked hand */
  score?: number | null
  /** hand only: 1 when the picked hand has the wanted handedness, else 0 */
  match?: number
}

export type Series = Record<string, (number | null)[]>

export const N_LANDMARKS: Record<Detector, number> = { hand: 21, pose: 33 }

export function newSeries(kind: Detector): Series {
  const s: Series = { t: [] }
  for (let i = 0; i < N_LANDMARKS[kind]; i++) {
    for (const a of ['x', 'y', 'z']) {
      s[`lm${i}_${a}`] = []
      s[`w${i}_${a}`] = []
    }
    if (kind === 'pose') s[`lm${i}_v`] = []
  }
  if (kind === 'hand') {
    s.handScore = []
    s.handMatch = []
  }
  return s
}

/** 5 decimals, NaN / undefined -> null (the recorder's r5). */
export function r5(v: number | null | undefined): number | null {
  return v == null || Number.isNaN(v) ? null : Math.round(v * 1e5) / 1e5
}

/** Append one video frame at t ms from the start; frame null = no detection. */
export function pushFrame(s: Series, kind: Detector, tMs: number, f: Frame | null): void {
  s.t.push(Math.round(tMs * 10) / 10)
  for (let i = 0; i < N_LANDMARKS[kind]; i++) {
    const p = f ? f.lm[i] : undefined
    const w = f ? f.world[i] : undefined
    s[`lm${i}_x`].push(p ? r5(p.x) : null)
    s[`lm${i}_y`].push(p ? r5(p.y) : null)
    s[`lm${i}_z`].push(p ? r5(p.z) : null)
    s[`w${i}_x`].push(w ? r5(w.x) : null)
    s[`w${i}_y`].push(w ? r5(w.y) : null)
    s[`w${i}_z`].push(w ? r5(w.z) : null)
    if (kind === 'pose') s[`lm${i}_v`].push(p ? r5(p.visibility) : null)
  }
  if (kind === 'hand') {
    s.handScore.push(f ? r5(f.score) : null)
    s.handMatch.push(f ? (f.match ?? 0) : null)
  }
}

/** Frame rate from the median frame interval, 1 decimal (the recorder's fpsMeasured). */
export function measuredFps(t: readonly (number | null)[]): number {
  const ts = t.filter((v): v is number => v != null)
  const dts = ts
    .slice(1)
    .map((v, i) => v - ts[i])
    .sort((a, b) => a - b)
  if (dts.length === 0) return 0
  const median = dts[Math.floor(dts.length / 2)]
  return median > 0 ? Math.round(10000 / median) / 10 : 0
}

export interface ResultInput {
  config: GameConfig
  kind: Detector
  series: Series
  cueT: readonly number[]
  startedAt: Date
  durationMs: number
  completed: boolean
  abortReason?: string
  videoW: number
  videoH: number
  delegate: string
  devicePixelRatio: number
  userAgent: string
}

export const MEDIAPIPE_VERSION = 'tasks-vision 1.2.3'

export function buildCameraResult(i: ResultInput): GameResult {
  return {
    gameType: 'camera',
    level: i.config.level,
    hand: i.config.hand,
    startedAt: i.startedAt.toISOString(),
    durationMs: Math.max(0, Math.round(i.durationMs)),
    completed: i.completed,
    ...(i.abortReason ? { abortReason: i.abortReason } : {}),
    series: { ...i.series, cueT: [...i.cueT] },
    clientMeta: {
      inputDevice: 'camera',
      canvasW: i.videoW,
      canvasH: i.videoH,
      videoW: i.videoW,
      videoH: i.videoH,
      devicePixelRatio: i.devicePixelRatio,
      userAgent: i.userAgent,
      fpsMeasured: measuredFps(i.series.t),
      mediapipe: MEDIAPIPE_VERSION,
      detector: i.kind === 'hand' ? 'hand_landmarker' : 'pose_landmarker_full',
      delegate: i.delegate,
      mirroredPreview: true,
    },
  }
}
