import data from '@shared/tracer_levels.json'
import type { Pt } from './geometry'

export interface TraceLevel {
  levelId: string
  shape: string
  /** level units 0-1000 */
  path: Pt[]
  channelWidth: number
  timeLimitS: number
}

const UNITS = data.canvas_units || 1000
const BY_LEVEL: Record<number, string> = { 1: 'line', 2: 'circle', 3: 'maze' }

export function getLevel(level: number): TraceLevel | undefined {
  const l = data.levels.find((x) => x.level_id === BY_LEVEL[level])
  if (!l) return undefined
  return {
    levelId: l.level_id,
    shape: l.shape,
    path: l.path.map((p) => [p[0], p[1]] as Pt),
    channelWidth: l.channel_width,
    timeLimitS: l.time_limit_s,
  }
}

/** targetX / targetY series: the level path / 1000 in drawing order. */
export function targetSeries(level: TraceLevel): { targetX: number[]; targetY: number[] } {
  return {
    targetX: level.path.map((p) => p[0] / UNITS),
    targetY: level.path.map((p) => p[1] / UNITS),
  }
}

export { UNITS as LEVEL_UNITS }
