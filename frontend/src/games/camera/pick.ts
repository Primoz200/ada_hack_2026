// Which detection of a MediaPipe result is recorded (the recorder's pickHand / pickPose).
import type { Hand } from '../shared/types'
import type { Frame, Point3 } from './series'

export interface HandResultLike {
  landmarks?: readonly (readonly Point3[])[]
  worldLandmarks?: readonly (readonly Point3[])[]
  handedness?: readonly (readonly { categoryName: string; score: number }[])[]
}

export interface PoseResultLike {
  landmarks?: readonly (readonly Point3[])[]
  worldLandmarks?: readonly (readonly Point3[])[]
}

/**
 * The tested hand by MediaPipe's handedness label (the subject's hand, used as-is, no flip); when
 * that hand is not found, the first hand with match = 0.
 */
export function pickHand(res: HandResultLike, hand: Hand): Frame | null {
  if (!res.landmarks || res.landmarks.length === 0) return null
  const want = hand === 'left' ? 'Left' : 'Right'
  const handedness = res.handedness ?? []
  let i = handedness.findIndex((h) => h[0] && h[0].categoryName === want)
  const match = i >= 0 ? 1 : 0
  if (i < 0) i = 0
  return {
    lm: res.landmarks[i],
    world: res.worldLandmarks?.[i] ?? [],
    score: handedness[i]?.[0]?.score ?? null,
    match,
  }
}

export function pickPose(res: PoseResultLike): Frame | null {
  if (!res.landmarks || res.landmarks.length === 0) return null
  return { lm: res.landmarks[0], world: res.worldLandmarks?.[0] ?? [] }
}

/** Pose landmarks the framing check wants visible: both shoulders and both elbows. */
export const POSE_FRAMING_POINTS = [11, 12, 13, 14] as const

/** Is the picked frame good enough for the framing check? Hand: detected. Pose: upper body visible. */
export function framedWell(kind: 'hand' | 'pose', f: Frame | null): boolean {
  if (!f) return false
  if (kind === 'hand') return true
  return POSE_FRAMING_POINTS.every((i) => {
    const p = f.lm[i]
    return p !== undefined && (p.visibility ?? 1) >= 0.5 && p.x >= 0 && p.x <= 1 && p.y >= 0 && p.y <= 1
  })
}
