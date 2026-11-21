// Framing check before the recording, as in the recorder's trackQuality: over the last 1.5 s, at
// least 90 % of the frames have a detection and the frame rate is at least 15 fps. The exercise may
// start once that has held for a moment. A slow device must never block the patient: when the
// detection is steady but the frame rate stays low, it starts anyway after a longer hold (the
// backend marks the capture quality itself).

export const WINDOW_MS = 1500
export const MIN_FRAMES = 5
export const MIN_DETECTED = 0.9
export const MIN_FPS = 15
/** "good" must hold this long before the countdown starts */
export const HOLD_MS = 1000
/** detected steadily but below MIN_FPS: start after this long */
export const SLOW_HOLD_MS = 4000

export interface FrameCheckState {
  fps: number
  detected: number
  /** enough frames in the window to judge */
  judged: boolean
  /** detection steady and the frame rate is fine */
  good: boolean
  /** detected steadily (frame rate aside) */
  steady: boolean
  ready: boolean
}

export class FrameCheck {
  private recent: { t: number; ok: boolean }[] = []
  private goodSince: number | undefined
  private steadySince: number | undefined

  push(now: number, ok: boolean): FrameCheckState {
    const r = this.recent
    r.push({ t: now, ok })
    while (r.length && now - r[0].t > WINDOW_MS) r.shift()
    if (r.length < MIN_FRAMES) {
      this.goodSince = undefined
      this.steadySince = undefined
      return { fps: 0, detected: 0, judged: false, good: false, steady: false, ready: false }
    }
    const span = (r[r.length - 1].t - r[0].t) / 1000
    const fps = span > 0 ? (r.length - 1) / span : 0
    const detected = r.filter((x) => x.ok).length / r.length
    const steady = detected >= MIN_DETECTED && ok
    const good = steady && fps >= MIN_FPS
    this.goodSince = good ? (this.goodSince ?? now) : undefined
    this.steadySince = steady ? (this.steadySince ?? now) : undefined
    const ready =
      (this.goodSince !== undefined && now - this.goodSince >= HOLD_MS) ||
      (this.steadySince !== undefined && now - this.steadySince >= SLOW_HOLD_MS)
    return { fps, detected, judged: true, good, steady, ready }
  }

  reset(): void {
    this.recent = []
    this.goodSince = undefined
    this.steadySince = undefined
  }
}
