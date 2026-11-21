import { describe, expect, it } from 'vitest'
import type { GameConfig } from '../shared/types'
import { beepSchedule, cueTimes, PROMPT_WORDS, promptAt } from './cues'
import { exerciseCopy, FALLBACK_EXERCISES, findExercise, secondsPhrase } from './exercises'
import { FrameCheck } from './frameCheck'
import { framedWell, pickHand, pickPose } from './pick'
import { buildCameraResult, measuredFps, newSeries, pushFrame, r5, type Frame, type Point3 } from './series'
import { classifyMediaError } from './source'

// The teammate's real recordings (backend/models/data/camera/recordings). Matched by suffix, read as
// they are: the key set our series builder produces must be exactly theirs, or scoring silently breaks.
interface Recording {
  level: number
  hand: 'left' | 'right'
  series: Record<string, unknown[]>
  clientMeta: Record<string, unknown>
}
const HAND_REF = import.meta.glob<Recording>(
  '../../../../backend/models/data/camera/recordings/*_hand_open_close_right_reference_P01.json',
  { eager: true, import: 'default' },
)
const POSE_REF = import.meta.glob<Recording>(
  '../../../../backend/models/data/camera/recordings/*_shoulder_abduction_right_reference_P01.json',
  { eager: true, import: 'default' },
)

const hand = findExercise(FALLBACK_EXERCISES, 1)!
const arms = findExercise(FALLBACK_EXERCISES, 2)!
const config = (level: number): GameConfig => ({ gameType: 'camera', level, hand: 'right', patientId: 'P' })

const pt = (x: number, y: number, z = 0, visibility?: number): Point3 => ({ x, y, z, visibility })
const fakeFrame = (n: number, seed: number, visibility?: number): Frame => ({
  lm: Array.from({ length: n }, (_, i) => pt(0.3 + i * 0.01 + seed * 1e-3, 0.4 + i * 0.005, -0.01 * i, visibility)),
  world: Array.from({ length: n }, (_, i) => pt(0.001 * i, -0.002 * i, 0.003 * i)),
  score: 0.93,
  match: 1,
})

/** A series built from fake frames the way the session builds it: some detected, some not. */
function fakeSeries(kind: 'hand' | 'pose', frames: number) {
  const s = newSeries(kind)
  for (let k = 0; k < frames; k++) {
    const f = k % 7 === 3 ? null : fakeFrame(kind === 'hand' ? 21 : 33, k, kind === 'pose' ? 0.98 : undefined)
    pushFrame(s, kind, 9.94 + k * 48.5, f)
  }
  return s
}

describe('series keys match the teammate recordings', () => {
  it('finds the reference recordings', () => {
    expect(Object.keys(HAND_REF).length).toBeGreaterThan(0)
    expect(Object.keys(POSE_REF).length).toBeGreaterThan(0)
  })

  for (const [kind, refs, level] of [
    ['hand', HAND_REF, 1],
    ['pose', POSE_REF, 2],
  ] as const) {
    it(`${kind}: the result series has exactly the reference keys`, () => {
      const ref = Object.values(refs)[0]
      const result = buildCameraResult({
        config: config(level),
        kind,
        series: fakeSeries(kind, 30),
        cueT: cueTimes(findExercise(FALLBACK_EXERCISES, level)!),
        startedAt: new Date('2026-11-21T10:00:00Z'),
        durationMs: 21000,
        completed: true,
        videoW: 1280,
        videoH: 720,
        delegate: 'CPU',
        devicePixelRatio: 1,
        userAgent: 'test',
      })
      expect(Object.keys(result.series).sort()).toEqual(Object.keys(ref.series).sort())
      expect(Object.keys(result.clientMeta).sort()).toEqual(Object.keys(ref.clientMeta).sort())
      expect(result.series.cueT).toEqual(ref.series.cueT)
      // every per-frame array has the length of t (cueT is the one exception)
      const n = result.series.t.length
      for (const [k, v] of Object.entries(result.series)) if (k !== 'cueT') expect(v, k).toHaveLength(n)
      expect(result).toMatchObject({ gameType: 'camera', level, hand: 'right', completed: true })
      expect(result.clientMeta).toMatchObject({
        inputDevice: 'camera',
        canvasW: 1280,
        videoH: 720,
        mediapipe: 'tasks-vision 1.2.3',
        detector: kind === 'hand' ? 'hand_landmarker' : 'pose_landmarker_full',
        mirroredPreview: true,
      })
    })
  }
})

describe('series builder', () => {
  it('pushes null for every landmark key when nothing was detected', () => {
    const s = newSeries('hand')
    pushFrame(s, 'hand', 12.345, null)
    expect(s.t).toEqual([12.3])
    for (const [k, v] of Object.entries(s)) if (k !== 't') expect(v, k).toEqual([null])
  })

  it('rounds like the recorder and keeps raw values', () => {
    const s = newSeries('pose')
    pushFrame(s, 'pose', 100.06, fakeFrame(33, 0, 0.987654))
    expect(s.t).toEqual([100.1])
    expect(s.lm0_x).toEqual([0.3])
    expect(s.lm11_v).toEqual([0.98765])
    expect(s.w2_z).toEqual([0.006])
    expect(r5(Number.NaN)).toBeNull()
    expect(r5(undefined)).toBeNull()
  })

  it('measures fps from the median frame interval', () => {
    expect(measuredFps([0, 48.5, 97, 145.5, 300])).toBe(20.6)
    expect(measuredFps([5])).toBe(0)
  })
})

describe('cue timeline', () => {
  it('matches exercises.py', () => {
    expect(cueTimes(hand)).toEqual([1000, 4000, 7000, 10000, 13000, 16000, 19000])
    expect(cueTimes(arms)).toEqual([1000, 9000, 17000, 25000, 33000])
  })

  it('hand: one high beep per cue; arms: high up, low down', () => {
    expect(beepSchedule(hand)).toHaveLength(7)
    expect(new Set(beepSchedule(hand).map((b) => b.hz)).size).toBe(1)
    const b = beepSchedule(arms)
    expect(b).toHaveLength(10)
    expect(b.slice(0, 2)).toEqual([
      { atMs: 1000, hz: 880 },
      { atMs: 5000, hz: 520 },
    ])
  })

  it('hand prompt: open around each beep, close in between, rest outside', () => {
    expect(promptAt(hand, 0)).toBe('rest')
    expect(promptAt(hand, 499)).toBe('rest')
    expect(promptAt(hand, 500)).toBe('open')
    expect(promptAt(hand, 1499)).toBe('open')
    expect(promptAt(hand, 1500)).toBe('close')
    expect(promptAt(hand, 3600)).toBe('open')
    expect(promptAt(hand, 19400)).toBe('open')
    expect(promptAt(hand, 19500)).toBe('rest')
  })

  it('arms prompt: up for upS after each cue, then down, rest at the ends', () => {
    expect(promptAt(arms, 900)).toBe('rest')
    expect(promptAt(arms, 1000)).toBe('up')
    expect(promptAt(arms, 4999)).toBe('up')
    expect(promptAt(arms, 5000)).toBe('down')
    expect(promptAt(arms, 9000)).toBe('up')
    expect(promptAt(arms, 40000)).toBe('down')
    expect(promptAt(arms, 41000)).toBe('rest')
  })
})

describe('hand picking', () => {
  const lmA = [pt(0.2, 0.5)]
  const lmB = [pt(0.7, 0.5)]
  const res = {
    landmarks: [lmA, lmB],
    worldLandmarks: [[pt(1, 1)], [pt(2, 2)]],
    handedness: [[{ categoryName: 'Left', score: 0.8 }], [{ categoryName: 'Right', score: 0.95 }]],
  }

  it('takes the hand with the wanted handedness', () => {
    expect(pickHand(res, 'right')).toMatchObject({ lm: lmB, score: 0.95, match: 1 })
    expect(pickHand(res, 'left')).toMatchObject({ lm: lmA, score: 0.8, match: 1 })
  })

  it('falls back to the first hand with match 0', () => {
    const one = { landmarks: [lmA], worldLandmarks: [[pt(1, 1)]], handedness: [[{ categoryName: 'Left', score: 0.7 }]] }
    expect(pickHand(one, 'right')).toMatchObject({ lm: lmA, score: 0.7, match: 0 })
  })

  it('returns null without a detection', () => {
    expect(pickHand({ landmarks: [], worldLandmarks: [], handedness: [] }, 'right')).toBeNull()
    expect(pickPose({ landmarks: [] })).toBeNull()
  })

  it('pose framing wants shoulders and elbows visible', () => {
    expect(framedWell('pose', fakeFrame(33, 0, 0.9))).toBe(true)
    expect(framedWell('pose', fakeFrame(33, 0, 0.2))).toBe(false)
    expect(framedWell('hand', fakeFrame(21, 0))).toBe(true)
    expect(framedWell('hand', null)).toBe(false)
  })
})

describe('frame check', () => {
  const run = (fc: FrameCheck, fromMs: number, toMs: number, stepMs: number, ok: (t: number) => boolean) => {
    let last = fc.push(fromMs, ok(fromMs))
    for (let t = fromMs + stepMs; t <= toMs; t += stepMs) last = fc.push(t, ok(t))
    return last
  }

  it('is ready after a steady second at a good frame rate', () => {
    const fc = new FrameCheck()
    expect(run(fc, 0, 900, 40, () => true).ready).toBe(false)
    const s = run(fc, 940, 1400, 40, () => true)
    expect(s.good).toBe(true)
    expect(s.ready).toBe(true)
  })

  it('is not ready while detections drop out', () => {
    const fc = new FrameCheck()
    const s = run(fc, 0, 5000, 40, (t) => Math.floor(t / 40) % 4 !== 0)
    expect(s.ready).toBe(false)
  })

  it('a slow device still starts, later', () => {
    const fc = new FrameCheck()
    const early = run(fc, 0, 2000, 100, () => true)
    expect(early.good).toBe(false)
    expect(early.ready).toBe(false)
    expect(run(fc, 2100, 5000, 100, () => true).ready).toBe(true)
  })

  it('a lost detection starts the hold again', () => {
    const fc = new FrameCheck()
    run(fc, 0, 800, 40, () => true)
    fc.push(840, false)
    expect(run(fc, 880, 1500, 40, () => true).ready).toBe(false)
  })
})

describe('wording and errors', () => {
  it('has formal copy for every exercise', () => {
    for (const ex of FALLBACK_EXERCISES) {
      const c = exerciseCopy(ex)
      expect(c.setup).toMatch(/^[A-ZČŠŽ]/)
      // the words on the intro are the words shown during the exercise
      for (const cue of c.cues) expect(Object.values(PROMPT_WORDS)).toContain(cue.word)
    }
    expect(secondsPhrase(21)).toBe('21 sekund')
    expect(secondsPhrase(42)).toBe('42 sekund')
    expect(secondsPhrase(2)).toBe('2 sekundi')
  })

  it('classifies getUserMedia errors', () => {
    expect(classifyMediaError({ name: 'NotAllowedError' })).toBe('denied')
    expect(classifyMediaError({ name: 'NotFoundError' })).toBe('no_camera')
    expect(classifyMediaError({ name: 'NotReadableError' })).toBe('busy')
  })
})
