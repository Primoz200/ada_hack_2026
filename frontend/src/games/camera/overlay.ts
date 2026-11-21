// Landmark overlay in the design tokens: slate lines on a soft white halo, white joints with a slate
// ring. Drawn in the unmirrored frame; the canvas is mirrored with CSS together with the video.
import type { Detector } from './exercises'
import type { Point3 } from './series'

export interface OverlayPalette {
  line: string
  joint: string
  halo: string
}

export function readOverlayPalette(): OverlayPalette {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string, fallback: string) => css.getPropertyValue(name).trim() || fallback
  return { line: v('--primary', '#3d6880'), joint: v('--card', '#ffffff'), halo: 'rgb(255 255 255 / 0.55)' }
}

/** Pose: only the upper body is drawn (shoulders, arms, trunk); the face and legs would be noise. */
const POSE_DRAWN = new Set([11, 12, 13, 14, 15, 16, 23, 24])
const POSE_JOINTS = [11, 12, 13, 14, 15, 16]

export function drawOverlay(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  kind: Detector,
  lm: readonly Point3[] | null,
  connections: readonly { start: number; end: number }[],
  c: OverlayPalette,
): void {
  ctx.clearRect(0, 0, w, h)
  if (!lm || lm.length === 0) return
  const scale = Math.max(1, Math.min(w, h) / 360)
  const visible = (i: number) => {
    const p = lm[i]
    return p !== undefined && (kind === 'hand' || (p.visibility ?? 1) >= 0.5)
  }
  const drawn = kind === 'hand' ? null : POSE_DRAWN
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  const segs = connections.filter(
    ({ start, end }) => (!drawn || (drawn.has(start) && drawn.has(end))) && visible(start) && visible(end),
  )
  for (const [stroke, width] of [
    [c.halo, (kind === 'hand' ? 5 : 7) * scale],
    [c.line, (kind === 'hand' ? 2.5 : 3.5) * scale],
  ] as const) {
    ctx.strokeStyle = stroke
    ctx.lineWidth = width
    ctx.beginPath()
    for (const { start, end } of segs) {
      ctx.moveTo(lm[start].x * w, lm[start].y * h)
      ctx.lineTo(lm[end].x * w, lm[end].y * h)
    }
    ctx.stroke()
  }
  const joints = kind === 'hand' ? lm.map((_, i) => i) : POSE_JOINTS.filter(visible)
  const r = (kind === 'hand' ? 3.5 : 5.5) * scale
  ctx.fillStyle = c.joint
  ctx.strokeStyle = c.line
  ctx.lineWidth = 1.75 * scale
  for (const i of joints) {
    const p = lm[i]
    ctx.beginPath()
    ctx.arc(p.x * w, p.y * h, r, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
  }
}
