import { describe, expect, it } from 'vitest'
import { cumulativeLengths, nearestInWindow, normalise, partialPath, pathLength, projectOnSegment, type Pt } from './geometry'
import { getLevel } from './levels'
import { PathTracker } from './progress'
import { TraceRecorder } from './recorder'
import { buildResult } from './result'

const line: Pt[] = [
  [100, 500],
  [900, 500],
]

describe('geometry', () => {
  it('computes path length', () => {
    expect(pathLength(line)).toBe(800)
    expect(cumulativeLengths([[0, 0], [3, 4], [3, 10]])).toEqual([0, 5, 11])
  })

  it('projects onto a segment and clamps', () => {
    expect(projectOnSegment([500, 540], line[0], line[1])).toEqual({ t: 0.5, d: 40 })
    expect(projectOnSegment([0, 500], line[0], line[1]).t).toBe(0)
  })

  it('finds nearest point within an arc-length window', () => {
    const cum = cumulativeLengths(line)
    const hit = nearestInWindow(line, cum, [700, 510], 0, 300)
    expect(hit).toBeUndefined() // projects at s = 600, outside the window
    expect(nearestInWindow(line, cum, [700, 510], 0, 800)?.s).toBe(600)
  })

  it('builds a partial path', () => {
    const cum = cumulativeLengths(line)
    expect(partialPath(line, cum, 400)).toEqual([[100, 500], [500, 500]])
    expect(partialPath(line, cum, 0)).toEqual([[100, 500]])
  })

  it('normalises to 0-1, also outside the canvas', () => {
    const rect = { left: 10, top: 20, width: 200, height: 200 }
    expect(normalise(110, 120, rect)).toEqual({ x: 0.5, y: 0.5 })
    expect(normalise(0, 20, rect).x).toBeLessThan(0)
  })
})

describe('PathTracker completion rule', () => {
  it('completes on the line only after walking it', () => {
    const t = new PathTracker(line, 60)
    expect(t.update([880, 500]).complete).toBe(false) // jump to the end: too far ahead, no coverage
    for (let x = 100; x <= 900; x += 20) t.update([x, 505])
    expect(t.update([900, 500]).complete).toBe(true)
  })

  it('requires 90 % coverage even at the end point', () => {
    const t = new PathTracker(line, 60)
    for (let x = 100; x <= 500; x += 20) t.update([x, 500])
    expect(t.update([900, 500]).complete).toBe(false)
  })

  it('cannot finish the circle (start = end) instantly', () => {
    const circle = getLevel(2)!
    const t = new PathTracker(circle.path, circle.channelWidth)
    expect(t.isNearStart([800, 500])).toBe(true)
    expect(t.update([800, 500]).complete).toBe(false)
    expect(t.update([801, 502]).complete).toBe(false)
  })

  it('finishes the circle after a full lap', () => {
    const circle = getLevel(2)!
    const t = new PathTracker(circle.path, circle.channelWidth)
    let last = t.state([800, 500])
    for (const p of circle.path) last = t.update(p)
    expect(last.fraction).toBeGreaterThan(0.99)
    expect(last.complete).toBe(true)
  })

  it('progress is monotonic and ignores far-off points', () => {
    const t = new PathTracker(line, 60)
    for (let x = 100; x <= 500; x += 20) t.update([x, 500])
    const s = t.state([500, 500]).s
    t.update([200, 500]) // moving back does not reduce progress
    expect(t.state([200, 500]).s).toBe(s)
    t.update([700, 900]) // far off the channel does not advance
    expect(t.state([700, 900]).s).toBe(s)
  })

  it('maze corridors: staying in the first corridor does not skip ahead', () => {
    const maze = getLevel(3)!
    const t = new PathTracker(maze.path, maze.channelWidth)
    t.update([100, 150])
    const st = t.update([100, 383]) // far ahead along the path though close in the plane to the corner
    expect(st.fraction).toBeLessThan(0.5)
  })
})

describe('TraceRecorder', () => {
  it('increments strokeId on every press and keeps pauses', () => {
    const r = new TraceRecorder()
    r.move(5, 0, 0) // ignored: not pressed
    r.press(1000, 0.1, 0.1)
    r.move(1010, 0.2, 0.1)
    r.release()
    r.move(1020, 0.9, 0.9) // ignored: lifted
    r.press(1500, 0.3, 0.1)
    r.move(1510, 0.4, 0.1)
    expect(r.series.strokeId).toEqual([0, 0, 1, 1])
    expect(r.series.t).toEqual([0, 10, 500, 510])
    expect(r.strokeCount).toBe(2)
  })

  it('records points outside the canvas and keeps t non-decreasing', () => {
    const r = new TraceRecorder()
    r.press(100, -0.2, 1.4)
    r.move(99, 0.5, 0.5)
    expect(r.series.x[0]).toBe(-0.2)
    expect(r.series.t).toEqual([0, 0])
  })
})

describe('buildResult', () => {
  it('produces equal-length trace arrays and normalised targets', () => {
    const level = getLevel(1)!
    const r = new TraceRecorder()
    r.press(0, 0.1, 0.5)
    r.move(16, 0.2, 0.5)
    const res = buildResult({
      config: { gameType: 'trace', level: 1, hand: 'right', patientId: 'p' },
      level,
      recorded: r.series,
      startedAt: new Date(0),
      durationMs: 16,
      completed: true,
      inputDevice: 'touch',
      canvasW: 300,
      canvasH: 300,
      devicePixelRatio: 2,
      userAgent: 'x',
    })
    expect(res.series.targetX).toEqual([0.1, 0.9])
    expect(res.series.targetY).toEqual([0.5, 0.5])
    const lens = ['t', 'x', 'y', 'strokeId'].map((k) => res.series[k].length)
    expect(new Set(lens).size).toBe(1)
    expect(res.abortReason).toBeUndefined()
  })
})
