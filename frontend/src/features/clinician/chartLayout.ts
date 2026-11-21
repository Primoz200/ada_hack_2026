// Layout constants shared by the game chart and the symptom charts so their plot areas line up.
import { formatDay, type Marker } from './model'

export const Y_AXIS_WIDTH = 56
export const CHART_MARGIN = { top: 8, right: 30, bottom: 2, left: 0 }

export function shortDay(t: number): string {
  return formatDay(t).replace(/\s/g, '').replace(/\.\d{4}$/, '.')
}

export function markerStyle(m: Marker): { stroke: string; dash?: string } {
  if (m.kind === 'alert') return { stroke: m.severity === 'red' ? '#b91c1c' : '#b45309' }
  if (m.kind === 'visit') return { stroke: 'var(--muted-foreground)', dash: '4 3' }
  return { stroke: 'var(--muted-foreground)', dash: '1 3' }
}
