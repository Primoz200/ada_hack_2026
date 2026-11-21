// Pure geometry for the trace game. All coordinates here are in level units (0-1000).
export type Pt = readonly [number, number]

export function dist(a: Pt, b: Pt): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1])
}

/** Cumulative arc length at each vertex; cum[0] = 0, last = total length. */
export function cumulativeLengths(path: readonly Pt[]): number[] {
  const cum = [0]
  for (let i = 1; i < path.length; i++) cum.push(cum[i - 1] + dist(path[i - 1], path[i]))
  return cum
}

export function pathLength(path: readonly Pt[]): number {
  const cum = cumulativeLengths(path)
  return cum[cum.length - 1] ?? 0
}

export interface Projection {
  /** arc length along the path of the closest point */
  s: number
  /** distance from the query point to that closest point */
  d: number
}

/** Closest point of segment a-b to p, as fraction t in [0, 1] and distance. */
export function projectOnSegment(p: Pt, a: Pt, b: Pt): { t: number; d: number } {
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const len2 = dx * dx + dy * dy
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2))
  return { t, d: Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy)) }
}

/**
 * Nearest point on the polyline whose arc length lies in [sMin, sMax].
 * Returns undefined when no segment intersects the window.
 */
export function nearestInWindow(
  path: readonly Pt[],
  cum: readonly number[],
  p: Pt,
  sMin: number,
  sMax: number,
): Projection | undefined {
  let best: Projection | undefined
  for (let i = 0; i < path.length - 1; i++) {
    const segStart = cum[i]
    const segLen = cum[i + 1] - cum[i]
    if (segStart + segLen < sMin || segStart > sMax) continue
    const { t, d } = projectOnSegment(p, path[i], path[i + 1])
    const s = segStart + t * segLen
    if (s < sMin || s > sMax) continue // projects outside the window: not a candidate
    if (!best || d < best.d) best = { s, d }
  }
  return best
}

/** The part of the polyline from the start up to arc length s (for drawing progress). */
export function partialPath(path: readonly Pt[], cum: readonly number[], s: number): Pt[] {
  if (path.length === 0) return []
  if (s <= 0) return [path[0]]
  const out: Pt[] = [path[0]]
  for (let i = 1; i < path.length; i++) {
    if (cum[i] <= s) {
      out.push(path[i])
      continue
    }
    const segLen = cum[i] - cum[i - 1]
    const t = segLen === 0 ? 0 : (s - cum[i - 1]) / segLen
    out.push([path[i - 1][0] + t * (path[i][0] - path[i - 1][0]), path[i - 1][1] + t * (path[i][1] - path[i - 1][1])])
    break
  }
  return out
}

/** Normalise a client pointer position to 0-1 relative to the canvas rect (may fall outside 0-1). */
export function normalise(
  clientX: number,
  clientY: number,
  rect: { left: number; top: number; width: number; height: number },
): { x: number; y: number } {
  return { x: (clientX - rect.left) / rect.width, y: (clientY - rect.top) / rect.height }
}
