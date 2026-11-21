// Monotonic progress along the target path and the completion rule.
import { cumulativeLengths, dist, nearestInWindow, type Pt } from './geometry'

/** The finish needs this share of the path covered (docs/tracer_data_spec.md). */
export const MIN_COVERAGE = 0.9
/** Spec says channel_width / 2; a little generous because a finger covers the end marker. */
export const END_RADIUS_FACTOR = 0.75
/** A press this close (in channel widths) to the start point begins the recording. */
export const START_RADIUS_FACTOR = 2
/** Points further than this (in channel widths) from the path do not advance progress. */
export const TRACK_TOLERANCE_FACTOR = 2

export interface ProgressState {
  /** arc length covered so far (monotonic) */
  s: number
  /** s / total length, 0-1 */
  fraction: number
  /** distance from the latest point to the end point, level units */
  distToEnd: number
  complete: boolean
}

export class PathTracker {
  readonly total: number
  readonly cum: number[]
  private s = 0

  readonly path: readonly Pt[]
  readonly channelWidth: number

  constructor(path: readonly Pt[], channelWidth: number) {
    this.path = path
    this.channelWidth = channelWidth
    this.cum = cumulativeLengths(path)
    this.total = this.cum[this.cum.length - 1] ?? 0
  }

  /** arc length covered so far */
  get progress(): number {
    return this.s
  }

  get end(): Pt {
    return this.path[this.path.length - 1]
  }

  get start(): Pt {
    return this.path[0]
  }

  isNearStart(p: Pt): boolean {
    return dist(p, this.start) <= this.channelWidth * START_RADIUS_FACTOR
  }

  /**
   * Feed a pressed pointer position. Progress only moves forward and only looks a limited
   * distance ahead, so a circle (start = end) cannot be finished by touching the end point.
   */
  update(p: Pt): ProgressState {
    const cw = this.channelWidth
    const ahead = Math.max(6 * cw, 0.3 * this.total)
    const hit = nearestInWindow(this.path, this.cum, p, this.s - cw, this.s + ahead)
    if (hit && hit.d <= TRACK_TOLERANCE_FACTOR * cw) this.s = Math.max(this.s, hit.s)
    return this.state(p)
  }

  state(p: Pt): ProgressState {
    const fraction = this.total === 0 ? 0 : this.s / this.total
    const distToEnd = dist(p, this.end)
    return {
      s: this.s,
      fraction,
      distToEnd,
      complete: fraction >= MIN_COVERAGE && distToEnd <= this.channelWidth * END_RADIUS_FACTOR,
    }
  }
}
