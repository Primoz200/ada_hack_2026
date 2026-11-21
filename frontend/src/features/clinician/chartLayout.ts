// Layout constants shared by the game chart and the rating charts so their plot areas line up.
import { formatDay, type Marker } from './model'

export const Y_AXIS_WIDTH = 64
export const CHART_MARGIN = { top: 8, right: 40, bottom: 2, left: 0 } // right: room for a marker label on the last day
export const AXIS_TICK = { fontSize: 13, fill: 'var(--muted-foreground)' }
export const AXIS_LABEL_STYLE = { fontSize: 13, textAnchor: 'middle' as const, fill: 'var(--muted-foreground)' }

export function shortDay(t: number): string {
  return formatDay(t).replace(/\s/g, '').replace(/\.\d{4}$/, '.')
}

const SEVERITY_STROKE: Record<string, string> = {
  red: 'var(--status-red)',
  yellow: 'var(--status-amber)',
  grey: 'var(--status-grey)',
}

export function markerStyle(m: Marker): { stroke: string; dash?: string } {
  if (m.kind === 'alert') return { stroke: SEVERITY_STROKE[m.severity ?? ''] ?? 'var(--status-grey)' }
  if (m.kind === 'visit') return { stroke: 'var(--primary)', dash: '4 3' }
  return { stroke: 'var(--muted-foreground)', dash: '1 3' }
}
