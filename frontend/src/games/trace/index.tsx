// Trace game: follow a path with a finger or the mouse. Plan section 5; rules in docs/tracer_data_spec.md.
// Raw pointer events are recorded as they arrive (normalised 0-1 on the square canvas); nothing is
// resampled or smoothed on the client.
import { useCallback, useEffect, useRef, useState } from 'react'
import type { GameProps, InputDevice } from '../shared/types'
import { Button } from '@/components/ui/button'
import type { Pt } from './geometry'
import { normalise, partialPath } from './geometry'
import { getLevel, LEVEL_UNITS, type TraceLevel } from './levels'
import { PathTracker, START_RADIUS_FACTOR } from './progress'
import { TraceRecorder } from './recorder'
import { buildResult } from './result'

const INK = '#0f172a'
const CHANNEL_EDGE = '#94a3b8'
const CHANNEL_FILL = '#e2e8f0'
const COVERED = '#cbd5e1'

export function TraceGame(props: GameProps) {
  const level = getLevel(props.config.level)
  if (!level) {
    return (
      <div className="space-y-4">
        <p>Te stopnje ni mogoče prikazati.</p>
        <Button variant="outline" className="h-14 w-full text-lg" onClick={props.onAbort}>
          Nazaj
        </Button>
      </div>
    )
  }
  return <TraceCanvas {...props} level={level} />
}

type Status = 'idle' | 'drawing' | 'lifted' | 'missedStart'

function TraceCanvas({ config, onComplete, level }: GameProps & { level: TraceLevel }) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const recorder = useRef(new TraceRecorder())
  const tracker = useRef(new PathTracker(level.path, level.channelWidth))
  const startedAt = useRef<Date | undefined>(undefined)
  const activePointer = useRef<number | undefined>(undefined)
  const device = useRef<InputDevice>('touch')
  const finished = useRef(false)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const raf = useRef<number | undefined>(undefined)
  const sizeRef = useRef(300)
  const [size, setSize] = useState(300)
  const [status, setStatus] = useState<Status>('idle')
  const [fraction, setFraction] = useState(0)

  // ---------------------------------------------------------------- drawing
  const draw = useCallback(() => {
    raf.current = undefined
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const px = sizeRef.current
    const dpr = window.devicePixelRatio || 1
    const u = px / LEVEL_UNITS
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, px, px)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    const tracePath = (pts: readonly Pt[]) => {
      ctx.beginPath()
      pts.forEach((p, i) => (i === 0 ? ctx.moveTo(p[0] * u, p[1] * u) : ctx.lineTo(p[0] * u, p[1] * u)))
    }
    const cw = level.channelWidth * u

    // channel: edge, fill, covered part
    tracePath(level.path)
    ctx.strokeStyle = CHANNEL_EDGE
    ctx.lineWidth = cw + 4
    ctx.stroke()
    ctx.strokeStyle = CHANNEL_FILL
    ctx.lineWidth = cw
    ctx.stroke()
    const covered = partialPath(level.path, tracker.current.cum, tracker.current.progress)
    if (covered.length > 1) {
      tracePath(covered)
      ctx.strokeStyle = COVERED
      ctx.lineWidth = cw
      ctx.stroke()
    }

    // where to press before the first touch
    const [sx, sy] = level.path[0]
    const [ex, ey] = level.path[level.path.length - 1]
    if (!recorder.current.started) {
      ctx.beginPath()
      ctx.setLineDash([6, 6])
      ctx.arc(sx * u, sy * u, level.channelWidth * START_RADIUS_FACTOR * u, 0, Math.PI * 2)
      ctx.strokeStyle = INK
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.setLineDash([])
    }

    // the drawn trace, one polyline per stroke
    const s = recorder.current.series
    ctx.strokeStyle = INK
    ctx.lineWidth = 4
    let i = 0
    while (i < s.t.length) {
      let j = i
      ctx.beginPath()
      ctx.moveTo(s.x[i] * px, s.y[i] * px)
      while (j < s.t.length && s.strokeId[j] === s.strokeId[i]) {
        ctx.lineTo(s.x[j] * px, s.y[j] * px)
        j++
      }
      if (j - i === 1) ctx.lineTo(s.x[i] * px + 0.1, s.y[i] * px)
      ctx.stroke()
      i = j
    }

    // markers: start = filled disc with a triangle, end = ring around a dot
    const r = Math.max(14, cw * 0.55)
    ctx.beginPath()
    ctx.arc(ex * u, ey * u, r, 0, Math.PI * 2)
    ctx.fillStyle = '#ffffff'
    ctx.fill()
    ctx.strokeStyle = INK
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.beginPath()
    ctx.arc(ex * u, ey * u, r * 0.35, 0, Math.PI * 2)
    ctx.fillStyle = INK
    ctx.fill()

    ctx.beginPath()
    ctx.arc(sx * u, sy * u, r * 0.8, 0, Math.PI * 2)
    ctx.fillStyle = INK
    ctx.fill()
    ctx.beginPath()
    const tr = r * 0.35
    ctx.moveTo(sx * u - tr * 0.6, sy * u - tr)
    ctx.lineTo(sx * u + tr, sy * u)
    ctx.lineTo(sx * u - tr * 0.6, sy * u + tr)
    ctx.closePath()
    ctx.fillStyle = '#ffffff'
    ctx.fill()

    // text labels (never colour alone)
    ctx.font = '600 14px system-ui, sans-serif'
    ctx.fillStyle = INK
    ctx.textAlign = 'center'
    const sameSpot = Math.hypot(sx - ex, sy - ey) < level.channelWidth
    const label = (text: string, x: number, y: number) => {
      const w = ctx.measureText(text).width / 2 + 4
      const lx = Math.max(w, Math.min(px - w, x * u))
      const ly = y * u - r - 8 < 16 ? y * u + r + 20 : y * u - r - 8
      ctx.fillText(text, lx, ly)
    }
    if (sameSpot) label('Začetek in konec', sx, sy)
    else {
      label('Začetek', sx, sy)
      label('Konec', ex, ey)
    }
  }, [level])

  const requestDraw = useCallback(() => {
    if (raf.current === undefined) raf.current = requestAnimationFrame(draw)
  }, [draw])

  // ---------------------------------------------------------------- sizing (square, crisp on high DPR)
  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    const measure = () => {
      const w = wrap.clientWidth
      const px = Math.max(220, Math.floor(Math.min(w, window.innerHeight * 0.6)))
      sizeRef.current = px
      setSize(px)
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(wrap)
    window.addEventListener('resize', measure)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', measure)
    }
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.round(size * dpr)
    canvas.height = Math.round(size * dpr)
    requestDraw()
  }, [size, requestDraw])

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current)
      if (raf.current !== undefined) cancelAnimationFrame(raf.current)
    },
    [],
  )

  // ---------------------------------------------------------------- finishing
  const finish = useCallback(
    (completed: boolean, abortReason?: string) => {
      if (finished.current) return
      finished.current = true
      if (timer.current) clearTimeout(timer.current)
      const rec = recorder.current
      rec.release()
      const t0 = rec.startedAtStamp
      const durationMs = t0 === undefined ? 0 : completed ? rec.lastT : performance.now() - t0
      const rect = canvasRef.current?.getBoundingClientRect()
      onComplete(
        buildResult({
          config,
          level,
          recorded: rec.series,
          startedAt: startedAt.current ?? new Date(),
          durationMs,
          completed,
          abortReason,
          inputDevice: device.current,
          canvasW: rect?.width ?? sizeRef.current,
          canvasH: rect?.height ?? sizeRef.current,
          devicePixelRatio: window.devicePixelRatio || 1,
          userAgent: navigator.userAgent,
        }),
      )
    },
    [config, level, onComplete],
  )

  // ---------------------------------------------------------------- pointer input
  const sample = (e: PointerEvent | React.PointerEvent, rect: DOMRect, move: boolean) => {
    const { x, y } = normalise(e.clientX, e.clientY, rect)
    if (move) recorder.current.move(e.timeStamp, x, y)
    else recorder.current.press(e.timeStamp, x, y)
    return tracker.current.update([x * LEVEL_UNITS, y * LEVEL_UNITS])
  }

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (finished.current || activePointer.current !== undefined) return
    if (e.pointerType === 'mouse' && e.button !== 0) return
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    const { x, y } = normalise(e.clientX, e.clientY, rect)
    if (!recorder.current.started && !tracker.current.isNearStart([x * LEVEL_UNITS, y * LEVEL_UNITS])) {
      setStatus('missedStart')
      return
    }
    activePointer.current = e.pointerId
    try {
      e.currentTarget.setPointerCapture(e.pointerId)
    } catch {
      /* capture is best effort */
    }
    if (!recorder.current.started) {
      device.current = e.pointerType === 'mouse' ? 'mouse' : 'touch'
      startedAt.current = new Date()
      timer.current = setTimeout(() => finish(false, 'time_limit'), level.timeLimitS * 1000)
    }
    const st = sample(e, rect, false)
    setStatus('drawing')
    setFraction(st.fraction)
    requestDraw()
    if (st.complete) finish(true)
  }

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (finished.current || e.pointerId !== activePointer.current) return
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    const native = e.nativeEvent
    const events = typeof native.getCoalescedEvents === 'function' ? native.getCoalescedEvents() : []
    const list = events.length > 0 ? events : [native]
    let st = sample(list[0], rect, true)
    for (let k = 1; k < list.length && !st.complete; k++) st = sample(list[k], rect, true)
    setFraction(st.fraction)
    requestDraw()
    if (st.complete) finish(true)
  }

  const onPointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (e.pointerId !== activePointer.current) return
    activePointer.current = undefined
    recorder.current.release()
    if (!finished.current) setStatus('lifted')
    requestDraw()
  }

  const hint = {
    idle: 'Dotaknite se začetne točke in sledite poti.',
    missedStart: 'Začnite pri označeni začetni točki.',
    drawing: 'Sledite poti čim natančneje, v svojem tempu.',
    lifted: 'Prst ste dvignili. Nadaljujte tam, kjer ste ostali.',
  }[status]
  const pct = Math.round(fraction * 100)

  return (
    <div className="space-y-4">
      <div ref={wrapRef} className="flex w-full justify-center">
        <canvas
          ref={canvasRef}
          role="img"
          aria-label="Polje za sledenje poti"
          style={{
            width: size,
            height: size,
            touchAction: 'none',
            userSelect: 'none',
            WebkitUserSelect: 'none',
            WebkitTouchCallout: 'none',
          }}
          className="rounded-xl border bg-white"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          onLostPointerCapture={onPointerUp}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
      <p className="text-center" aria-live="polite">
        {hint}
      </p>
      <div
        role="progressbar"
        aria-label="Prevožena pot"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="mx-auto h-2 w-full overflow-hidden rounded-full bg-muted"
        style={{ maxWidth: size }}
      >
        <div className="h-full bg-foreground transition-[width]" style={{ width: `${pct}%` }} />
      </div>
      <Button variant="outline" className="h-14 w-full text-lg" onClick={() => finish(false, 'cannot_today')}>
        Danes ne morem
      </Button>
    </div>
  )
}
