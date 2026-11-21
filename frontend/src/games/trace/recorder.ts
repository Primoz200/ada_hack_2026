// Raw stroke bookkeeping. No resampling, no smoothing: every pointer sample is stored as given.
export interface TraceSeries {
  t: number[]
  x: number[]
  y: number[]
  strokeId: number[]
}

export class TraceRecorder {
  readonly series: TraceSeries = { t: [], x: [], y: [], strokeId: [] }
  private t0: number | undefined
  private stroke = -1
  private down = false

  /** timeStamp (ms) of the first recorded point, undefined before the first touch. */
  get startedAtStamp(): number | undefined {
    return this.t0
  }

  get isDown(): boolean {
    return this.down
  }

  get started(): boolean {
    return this.t0 !== undefined
  }

  get strokeCount(): number {
    return this.stroke + 1
  }

  get lastT(): number {
    return this.series.t[this.series.t.length - 1] ?? 0
  }

  /** A new press: starts a new stroke and records its first point. */
  press(timeStamp: number, x: number, y: number): void {
    this.stroke += 1
    this.down = true
    this.add(timeStamp, x, y)
  }

  /** A sample while pressed. Ignored when no stroke is active. */
  move(timeStamp: number, x: number, y: number): void {
    if (this.down) this.add(timeStamp, x, y)
  }

  /** The pointer was lifted: the stroke ends, the gap until the next press is kept in `t`. */
  release(): void {
    this.down = false
  }

  private add(timeStamp: number, x: number, y: number): void {
    if (this.t0 === undefined) this.t0 = timeStamp
    // t is non-decreasing even if the browser delivers slightly out-of-order coalesced events
    const t = Math.max(this.lastT, timeStamp - this.t0)
    const s = this.series
    s.t.push(t)
    s.x.push(x)
    s.y.push(y)
    s.strokeId.push(this.stroke)
  }
}
