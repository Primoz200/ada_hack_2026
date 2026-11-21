// Pure geometry and timing of the intro demonstrations (ExerciseDemo.tsx draws them). One drawing
// space for all three: a 200 x 212 box, one stroke width, so the hand and the figures match.
// Joints are angles; positions come from forward kinematics in 3D (x right, y down, z towards the
// camera), so a limb keeps its length and its end travels on an arc. The picture plane is drawn true
// to size and depth slightly downwards (oblique projection, see OBLIQUE).
import type { Hand } from '../../shared/types'
import type { Prompt } from '../cues'

export type DemoKind = 'hand' | 'abduction' | 'raise'

export interface Pt {
  x: number
  y: number
}

interface Vec3 {
  x: number
  y: number
  z: number
}

export const BOX = { w: 200, h: 212 } as const
/** Limb, finger and torso width: one weight for everything. */
export const STROKE = 11
/** Panel-coloured outline that lets a part in front read against the part behind it. */
export const GAP = 2.25

const deg = Math.PI / 180

export function demoKind(exerciseKey: string, detector?: string): DemoKind | null {
  if (exerciseKey === 'hand_open_close') return 'hand'
  if (exerciseKey === 'shoulder_abduction') return 'abduction'
  if (exerciseKey === 'arm_raise') return 'raise'
  return detector === 'hand' ? 'hand' : null
}

// ---------------------------------------------------------------- loop timing

/** Full loop length: the hand moves briskly, the arms slowly, as in the exercise. */
export const LOOP_MS: Record<DemoKind, number> = { hand: 3000, abduction: 4000, raise: 4000 }

/**
 * One loop, phase 0..1: rise to the active end (0-0.30), hold it (0.30-0.50), return (0.50-0.80),
 * hold the rest position (0.80-1). The active word belongs to the first half, the rest word to the second.
 */
const RISE_END = 0.3
const HOLD_END = 0.5
const LOWER_END = 0.8

/** Minimum-jerk ease: zero speed and zero acceleration at both ends, how a calm human movement looks. */
export function ease(u: number): number {
  const v = Math.min(1, Math.max(0, u))
  return v * v * v * (10 + v * (-15 + 6 * v))
}

/** 0 = rest position (fist, arms down), 1 = active end position (open hand, arms up). */
export function progressAt(phase: number): number {
  const p = wrap(phase)
  if (p < RISE_END) return ease(p / RISE_END)
  if (p < HOLD_END) return 1
  if (p < LOWER_END) return 1 - ease((p - HOLD_END) / (LOWER_END - HOLD_END))
  return 0
}

export function wrap(phase: number): number {
  const p = phase % 1
  return p < 0 ? p + 1 : p
}

export function phaseAt(elapsedMs: number, kind: DemoKind): number {
  return wrap(elapsedMs / LOOP_MS[kind])
}

/** Is the figure at or moving to the active end? Then the active cue word is the emphasised one. */
export function isActive(phase: number): boolean {
  return wrap(phase) < HOLD_END
}

/** The cue word (cues.ts) for the active and the rest end of each demonstration. */
export function cuePrompt(kind: DemoKind, active: boolean): Prompt {
  if (kind === 'hand') return active ? 'open' : 'close'
  return active ? 'up' : 'down'
}

// ---------------------------------------------------------------- projection and mirroring

/**
 * Front view. Depth (towards the camera) is drawn slightly downwards, the oblique projection of
 * technical drawing: the camera looks a little down on the seated patient, so an arm reaching forward
 * still shows as a short arm in front of the body instead of vanishing into a dot.
 */
export const OBLIQUE = 0.4

function project(p: Vec3): Pt {
  return { x: p.x, y: p.y + OBLIQUE * p.z }
}

function add(a: Vec3, b: Vec3, k = 1): Vec3 {
  return { x: a.x + b.x * k, y: a.y + b.y * k, z: a.z + b.z * k }
}

/** Mirror about the vertical centre line of the box. */
export function mirrorPt(p: Pt): Pt {
  return { x: BOX.w - p.x, y: p.y }
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t

// ---------------------------------------------------------------- seated figure (front view)

export const FIGURE = {
  cx: 100,
  shoulderY: 82,
  /** half the shoulder width: wide enough that raised arms clear the head */
  shoulder: 24,
  headR: 13.5,
  /** clear space between the head and the shoulder line */
  neck: 4,
  /** neck to hip */
  spine: 58,
  arm: 64,
  hip: 11,
  thigh: 30,
  shin: 46,
  /** half the width of the seat */
  seat: 34,
} as const

/** Arm elevation (deg from hanging straight down) at rest and at the healthy active end. */
export const ARM_RANGE: Record<'abduction' | 'raise', { rest: number; active: number }> = {
  // out through the side, to a little above shoulder height
  abduction: { rest: 11, active: 98 },
  // forward in front of the body and on up until the arms point straight at the ceiling
  raise: { rest: 11, active: 177 },
}

/** Rest: the arms hang a little away from the body (in the side plane), the same in both exercises. */
const REST_OUT = Math.sin(ARM_RANGE.abduction.rest * deg)

/** How far the hands draw in towards the middle as the raised arms pass in front of the body. */
const TOE_IN = 0.22

const smoothstep = (a: number, b: number, v: number) => ease((v - a) / (b - a))

/**
 * Unit direction of the arm on the right-hand side of the picture (x outward, y down, z towards the
 * camera) at progress t. Abduction stays in the side plane. The raise swings forward: its sideways part
 * never grows past the rest pose, it turns slightly inwards on the way up (the hands pass in front of
 * the chest, which is what tells this raise apart from the one through the side) and is zero overhead.
 * Whatever the elevation leaves over points at the camera.
 */
export function armDirection(kind: 'abduction' | 'raise', t: number): Vec3 {
  const { rest, active } = ARM_RANGE[kind]
  const e = lerp(rest, active, t) * deg
  if (kind === 'abduction') return { x: Math.sin(e), y: Math.cos(e), z: 0 }
  // drawn in while the hands are low in front of the body, straight again before they pass the face
  const raw = REST_OUT * (1 - smoothstep(0, 0.35, t)) - TOE_IN * Math.sin(Math.PI * Math.min(1, t / 0.7)) ** 2
  const out = Math.max(-Math.sin(e), Math.min(raw, Math.sin(e)))
  return { x: out, y: Math.cos(e), z: Math.sqrt(Math.max(0, Math.sin(e) ** 2 - out * out)) }
}

export interface FigurePose {
  head: Pt
  headR: number
  neck: Pt
  hip: Pt
  shoulders: [Pt, Pt]
  wrists: [Pt, Pt]
  /** how far the arms point towards the camera, 0..1 (the in-front outline follows it) */
  forward: number
  legs: [Pt[], Pt[]]
  /** front edge of the seat, behind the shins */
  seat: [Pt, Pt]
}

export function figurePose(kind: 'abduction' | 'raise', t: number): FigurePose {
  const F = FIGURE
  const dir = armDirection(kind, t)
  const side = (s: 1 | -1) => {
    const shoulder: Vec3 = { x: F.cx + s * F.shoulder, y: F.shoulderY, z: 0 }
    const wrist = add(shoulder, { x: s * dir.x, y: dir.y, z: dir.z }, F.arm)
    return { shoulder: project(shoulder), wrist: project(wrist) }
  }
  const l = side(-1)
  const r = side(1)
  const hipY = F.shoulderY + F.spine
  // seated, seen from the front: the thighs point at the camera (short, drawn by the same oblique
  // projection), the shins hang to the floor in front of the seat
  const leg = (s: 1 | -1): Pt[] => {
    const hip: Vec3 = { x: F.cx + s * F.hip, y: hipY, z: 0 }
    const knee = add(hip, { x: s * 0.196, y: 0, z: 0.981 }, F.thigh)
    const foot = add(knee, { x: 0, y: 1, z: 0 }, F.shin)
    return [{ x: F.cx, y: hipY }, project(hip), project(knee), project(foot)]
  }
  return {
    head: { x: F.cx, y: F.shoulderY - STROKE / 2 - F.neck - F.headR },
    headR: F.headR,
    neck: { x: F.cx, y: F.shoulderY },
    hip: { x: F.cx, y: hipY },
    shoulders: [l.shoulder, r.shoulder],
    wrists: [l.wrist, r.wrist],
    forward: Math.max(0, dir.z),
    legs: [leg(-1), leg(1)],
    seat: [
      { x: F.cx - F.seat, y: hipY + OBLIQUE * F.thigh * 0.55 },
      { x: F.cx + F.seat, y: hipY + OBLIQUE * F.thigh * 0.55 },
    ],
  }
}

/** The wrist's path from rest to the active end (the figure's right-hand side of the picture). */
export function wristPath(kind: 'abduction' | 'raise', samples = 48): Pt[] {
  return Array.from({ length: samples + 1 }, (_, i) => figurePose(kind, i / samples).wrists[1])
}

// ---------------------------------------------------------------- hand (palm towards the camera)

// Drawn as the RIGHT hand as it appears in the mirrored camera preview: on the right of the picture,
// thumb towards the middle (left). The left hand is the exact mirror image.

export const HAND = {
  /** right of centre: the tested hand sits on its own side of the mirrored picture */
  cx: 112,
  /** palm: top (knuckle line) and bottom (wrist), half widths */
  palmTop: 80,
  wristY: 134,
  /** the elbow rests on the table */
  elbowY: 182,
  palmHalf: 25,
  wristHalf: 18,
  forearmHalf: 15.5,
} as const

interface FingerSpec {
  /** knuckle position relative to the hand centre / absolute y */
  bx: number
  by: number
  /** proximal, middle and distal phalanx */
  len: [number, number, number]
  /** sideways angle (deg, + = towards the little finger) when open and when closed */
  spread: [number, number]
}

// index, middle, ring, little finger
const FINGERS: FingerSpec[] = [
  { bx: -19.5, by: 82, len: [24, 15, 12], spread: [-13, -2] },
  { bx: -6.5, by: 79, len: [27, 17, 13], spread: [-3, 0] },
  { bx: 6.5, by: 81, len: [25, 16, 12], spread: [8, 2] },
  { bx: 19.5, by: 86, len: [19, 12, 10], spread: [20, 4] },
]

/** Flexion of the three finger joints (deg) in a tight fist; 0 = straight. */
const FIST_FLEX: [number, number, number] = [90, 105, 55]

interface ThumbSpec {
  base: Pt
  len: [number, number, number]
  /** in-picture angle of each segment, from straight up, + = towards the fingers (deg) */
  open: [number, number, number]
  closed: [number, number, number]
}

const THUMB: ThumbSpec = {
  base: { x: -17, y: 122 },
  len: [24, 18, 15],
  open: [-36, -52, -58],
  // the thumb crosses over the curled index and middle finger
  closed: [-8, 72, 98],
}

export interface HandPose {
  /** palm outline, a closed polygon to be drawn with round joins */
  palm: Pt[]
  /** forearm: centre line from the wrist to the elbow (drawn with round ends) */
  forearm: [Pt, Pt]
  forearmWidth: number
  /** the table top the elbow rests on */
  table: [Pt, Pt]
  fingers: Pt[][]
  thumb: Pt[]
  /** 0 open .. 1 fist: the in-front outline follows it */
  closed: number
}

function handLocal(t: number): HandPose {
  const H = HAND
  const closed = 1 - t
  const fingers = FINGERS.map((f) => {
    const spread = lerp(f.spread[0], f.spread[1], closed) * deg
    // the finger's own up direction in the picture plane; flexion turns it towards the camera
    const up: Vec3 = { x: Math.sin(spread), y: -Math.cos(spread), z: 0 }
    const toCam: Vec3 = { x: 0, y: 0, z: 1 }
    let p: Vec3 = { x: H.cx + f.bx, y: f.by, z: 0 }
    let bend = 0
    const pts = [project(p)]
    f.len.forEach((len, j) => {
      bend += FIST_FLEX[j] * closed * deg
      const d = add({ x: up.x * Math.cos(bend), y: up.y * Math.cos(bend), z: 0 }, toCam, Math.sin(bend))
      p = add(p, d, len)
      pts.push(project(p))
    })
    return pts
  })
  let q: Pt = { x: H.cx + THUMB.base.x, y: THUMB.base.y }
  const thumb = [q]
  THUMB.len.forEach((len, j) => {
    const a = lerp(THUMB.open[j], THUMB.closed[j], closed) * deg
    q = { x: q.x + Math.sin(a) * len, y: q.y - Math.cos(a) * len }
    thumb.push(q)
  })
  const r = STROKE / 2
  const palm: Pt[] = [
    { x: H.cx - H.palmHalf + r, y: H.palmTop },
    { x: H.cx + H.palmHalf - r, y: H.palmTop + 4 },
    { x: H.cx + H.wristHalf - r, y: H.wristY },
    { x: H.cx - H.wristHalf + r, y: H.wristY },
  ]
  return {
    palm,
    forearm: [
      { x: H.cx, y: H.wristY - 6 },
      { x: H.cx, y: H.elbowY },
    ],
    forearmWidth: 2 * H.forearmHalf,
    table: [
      { x: H.cx - 62, y: H.elbowY + H.forearmHalf + r + 0.5 },
      { x: H.cx + 62, y: H.elbowY + H.forearmHalf + r + 0.5 },
    ],
    fingers,
    thumb,
    closed,
  }
}

/** The hand at progress t (0 = fist, 1 = wide open), as seen in the mirrored preview of `hand`. */
export function handPose(t: number, hand: Hand): HandPose {
  const p = handLocal(t)
  if (hand === 'right') return p
  const m = (pts: Pt[]) => pts.map(mirrorPt)
  return {
    ...p,
    palm: m(p.palm),
    forearm: [mirrorPt(p.forearm[0]), mirrorPt(p.forearm[1])],
    table: [mirrorPt(p.table[1]), mirrorPt(p.table[0])],
    fingers: p.fingers.map(m),
    thumb: m(p.thumb),
  }
}

// ---------------------------------------------------------------- accessible description

export const DEMO_LABEL: Record<DemoKind, string> = {
  hand: 'Prikaz vaje: dlan, obrnjena proti kameri, se široko odpre z razprtimi prsti in se nato stisne v pest.',
  abduction: 'Prikaz vaje: sedeča oseba iztegnjeni roki skozi stran dvigne do višine ramen ali malo više in ju spusti.',
  raise: 'Prikaz vaje: sedeča oseba iztegnjeni roki dvigne spredaj in visoko nad glavo ter ju spusti.',
}

/** SVG path data for a polyline. */
export function pathD(pts: Pt[], close = false): string {
  const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ')
  return close ? `${d} Z` : d
}
