import { describe, expect, it } from 'vitest'
import { PROMPT_WORDS } from '../cues'
import {
  ARM_RANGE,
  armDirection,
  BOX,
  cuePrompt,
  demoKind,
  ease,
  FIGURE,
  figurePose,
  handPose,
  isActive,
  LOOP_MS,
  mirrorPt,
  phaseAt,
  progressAt,
  wristPath,
  type Pt,
} from './model'

const dist = (a: Pt, b: Pt) => Math.hypot(a.x - b.x, a.y - b.y)
const steps = (n: number) => Array.from({ length: n + 1 }, (_, i) => i / n)

describe('loop timing', () => {
  it('eases monotonically from 0 to exactly 1, gently at both ends', () => {
    expect(ease(0)).toBe(0)
    expect(ease(1)).toBe(1)
    expect(ease(-1)).toBe(0)
    expect(ease(2)).toBe(1)
    const v = steps(200).map(ease)
    for (let i = 1; i < v.length; i++) expect(v[i]).toBeGreaterThanOrEqual(v[i - 1])
    // no overshoot (no bounce, no elastic) and a soft start
    expect(Math.max(...v)).toBe(1)
    expect(ease(0.05)).toBeLessThan(0.01)
  })

  it('rises, holds the active end, returns and holds the rest position', () => {
    expect(progressAt(0)).toBe(0)
    expect(progressAt(0.15)).toBeCloseTo(0.5, 5)
    expect(progressAt(0.3)).toBe(1)
    expect(progressAt(0.4)).toBe(1)
    expect(progressAt(0.65)).toBeCloseTo(0.5, 5)
    expect(progressAt(0.8)).toBe(0)
    expect(progressAt(0.95)).toBe(0)
    for (const p of steps(400)) {
      expect(progressAt(p)).toBeGreaterThanOrEqual(0)
      expect(progressAt(p)).toBeLessThanOrEqual(1)
    }
    // continuous across the loop seam
    expect(progressAt(0.9999)).toBeCloseTo(progressAt(1.0001), 5)
  })

  it('takes three to four seconds per loop', () => {
    for (const ms of Object.values(LOOP_MS)) {
      expect(ms).toBeGreaterThanOrEqual(3000)
      expect(ms).toBeLessThanOrEqual(4000)
    }
    expect(phaseAt(LOOP_MS.abduction * 2.25, 'abduction')).toBeCloseTo(0.25)
  })

  it('switches the emphasised word only at the start and the middle of the loop', () => {
    const flips: number[] = []
    const ph = steps(1000)
    for (let i = 1; i < ph.length; i++) if (isActive(ph[i]) !== isActive(ph[i - 1])) flips.push(ph[i])
    expect(flips).toEqual([0.5, 1])
    // the active word belongs to the way up and the hold at the top
    expect(isActive(0.1)).toBe(true)
    expect(isActive(0.45)).toBe(true)
    expect(isActive(0.6)).toBe(false)
  })

  it('names the cue words used during the exercise', () => {
    expect(PROMPT_WORDS[cuePrompt('hand', true)]).toBe('Odprite')
    expect(PROMPT_WORDS[cuePrompt('hand', false)]).toBe('Stisnite')
    expect(PROMPT_WORDS[cuePrompt('abduction', true)]).toBe('Gor')
    expect(PROMPT_WORDS[cuePrompt('raise', false)]).toBe('Dol')
  })

  it('knows the three exercises', () => {
    expect(demoKind('hand_open_close')).toBe('hand')
    expect(demoKind('shoulder_abduction')).toBe('abduction')
    expect(demoKind('arm_raise')).toBe('raise')
    expect(demoKind('something_new', 'pose')).toBeNull()
  })
})

describe('seated figure', () => {
  it('abduction stays in the side plane: the drawn arm keeps its length on a circular arc', () => {
    for (const t of steps(20)) {
      const p = figurePose('abduction', t)
      expect(dist(p.shoulders[1], p.wrists[1])).toBeCloseTo(FIGURE.arm, 6)
      expect(dist(p.shoulders[0], p.wrists[0])).toBeCloseTo(FIGURE.arm, 6)
    }
    // healthy end: a little above shoulder height
    const end = figurePose('abduction', 1)
    expect(end.wrists[1].y).toBeLessThan(FIGURE.shoulderY)
    expect(end.wrists[1].y).toBeGreaterThan(FIGURE.shoulderY - 0.2 * FIGURE.arm)
  })

  it('the raise keeps the arm length in 3D and ends straight overhead', () => {
    for (const t of steps(40)) {
      const d = armDirection('raise', t)
      expect(Math.hypot(d.x, d.y, d.z)).toBeCloseTo(1, 9)
      expect(d.z).toBeGreaterThanOrEqual(0) // never behind the body
    }
    const end = figurePose('raise', 1)
    expect(end.wrists[1].y).toBeLessThan(FIGURE.shoulderY - 0.95 * FIGURE.arm)
    expect(Math.abs(end.wrists[1].x - end.shoulders[1].x)).toBeLessThan(5)
    expect(ARM_RANGE.raise.active).toBeGreaterThan(170)
  })

  it('the raise never goes out to the side: its path differs from abduction', () => {
    const rest = figurePose('raise', 0).wrists[1].x
    for (const t of steps(40)) expect(figurePose('raise', t).wrists[1].x).toBeLessThanOrEqual(rest + 1e-9)
    // halfway up, the abducted wrist is far out to the side, the raised one in front of the body
    const a = figurePose('abduction', 0.5).wrists[1]
    const r = figurePose('raise', 0.5).wrists[1]
    expect(a.x - FIGURE.cx).toBeGreaterThan(FIGURE.shoulder + 0.6 * FIGURE.arm)
    expect(r.x - FIGURE.cx).toBeLessThan(FIGURE.shoulder)
  })

  it('both exercises start from the same rest position, symmetric about the centre line', () => {
    const a = figurePose('abduction', 0)
    const r = figurePose('raise', 0)
    expect(a.wrists[1].x).toBeCloseTo(r.wrists[1].x, 9)
    expect(a.wrists[1].y).toBeCloseTo(r.wrists[1].y, 9)
    for (const t of [0, 0.3, 0.7, 1]) {
      const p = figurePose('raise', t)
      expect(mirrorPt(p.wrists[0]).x).toBeCloseTo(p.wrists[1].x, 9)
    }
  })

  it('fits the drawing box with the arms overhead', () => {
    for (const kind of ['abduction', 'raise'] as const) {
      for (const w of wristPath(kind)) {
        expect(w.x).toBeGreaterThan(0)
        expect(w.x).toBeLessThan(BOX.w)
        expect(w.y).toBeGreaterThan(0)
      }
    }
  })
})

describe('hand', () => {
  const palmCentreX = (pts: Pt[]) => pts.reduce((s, p) => s + p.x, 0) / pts.length

  it('right hand: on the right of the picture, thumb towards the middle', () => {
    for (const t of [0, 1]) {
      const p = handPose(t, 'right')
      const cx = palmCentreX(p.palm)
      expect(cx).toBeGreaterThan(BOX.w / 2 + 5)
      const thumbTip = p.thumb[p.thumb.length - 1]
      if (t === 1) expect(thumbTip.x).toBeLessThan(cx - 30)
      // index finger on the thumb side, little finger on the outer side
      expect(p.fingers[0][0].x).toBeLessThan(p.fingers[3][0].x)
    }
  })

  it('left hand is the exact mirror image', () => {
    for (const t of [0, 0.4, 1]) {
      const r = handPose(t, 'right')
      const l = handPose(t, 'left')
      r.fingers.forEach((f, i) =>
        f.forEach((p, j) => {
          expect(l.fingers[i][j].x).toBeCloseTo(BOX.w - p.x, 9)
          expect(l.fingers[i][j].y).toBeCloseTo(p.y, 9)
        }),
      )
      expect(l.thumb.at(-1)!.x).toBeCloseTo(BOX.w - r.thumb.at(-1)!.x, 9)
    }
  })

  it('open: fingers straight and spread; fist: fingers curled down over the palm, thumb across them', () => {
    const open = handPose(1, 'right')
    const fist = handPose(0, 'right')
    open.fingers.forEach((f) => expect(f.at(-1)!.y).toBeLessThan(f[0].y - 35))
    // fingertips fan out wider than the knuckles
    const tipSpan = open.fingers[3].at(-1)!.x - open.fingers[0].at(-1)!.x
    const knuckleSpan = open.fingers[3][0].x - open.fingers[0][0].x
    expect(tipSpan).toBeGreaterThan(knuckleSpan * 1.4)
    // in the fist every fingertip is below its knuckle (curled towards the camera and down)
    fist.fingers.forEach((f) => expect(f.at(-1)!.y).toBeGreaterThan(f[0].y))
    // the thumb tip crosses to the far side of the index finger
    expect(fist.thumb.at(-1)!.x).toBeGreaterThan(fist.fingers[0][0].x)
    expect(fist.closed).toBe(1)
    expect(open.closed).toBe(0)
  })
})
