// Trace game: follow a path with a finger or the mouse. Plan section 5; rules in docs/tracer_data_spec.md.
// Raw pointer events are recorded as they arrive (normalised 0-1 on the square canvas); nothing is
// resampled or smoothed on the client.
import { useCallback, useEffect, useRef, useState } from 'react'
import type { GameProps, InputDevice } from '../shared/types'
import { Button } from '@/components/ui/button'
import type { Pt } from './geometry'
import { normalise, partialPath } from './geometry'
import { getLevel, LEVEL_UNITS, type TraceLevel } from './levels'
import { PathTracker } from './progress'
import { TraceRecorder } from './recorder'
import { buildResult } from './result'

interface Palette {
  ink: string
  trace: string
  edge: string
  fill: string
  covered: string
  card: string
}

/** Canvas colours from the design tokens (index.css); read once per mount. */
function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string, fallback: string) => css.getPropertyValue(name).trim() || fallback
  return {
    ink: v('--foreground', 'black'),
    trace: v('--primary', 'navy'),
    edge: v('--input', 'grey'),
    fill: v('--muted', 'whitesmoke'),
    covered: v('--secondary', 'lightgrey'),
    card: v('--card', 'white'),
  }
}

const FONT = '600 15px "Hanken Grotesk", system-ui, sans-serif'
/** Never larger than this, never taller than this share of the window, and leave room for the page around it. */
const MAX_PX = 560
const MAX_VH = 0.62
const PAGE_RESERVE_PX = 350

export function TraceGame(props: GameProps) {
  const level = getLevel(props.config.level)
  if (!level) {
    return (
      <div className="space-y-4">
        <p>Te naloge trenutno ni mogoče prikazati.</p>
        <Button variant="outline" size="lg" onClick={props.onAbort}>
          Nazaj
        </Button>
      </div>
    )
  }
  return <TraceCanvas {...props} level={level} />
}

type Status = 'idle' | 'drawing' | 'lifted' | 'missedStart' | 'done'

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
  const palette = useRef<Palette | undefined>(undefined)
  // the time-limit timer is armed at the first press; read the latest callback when it fires
  const onCompleteRef = useRef(onComplete)
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // ---------------------------------------------------------------- drawing
  const draw = useCallback(() => {
    raf.current = undefined
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const c = (palette.current ??= readPalette())
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
    ctx.strokeStyle = c.edge
    ctx.lineWidth = cw + 4
    ctx.stroke()
    ctx.strokeStyle = c.fill
    ctx.lineWidth = cw
    ctx.stroke()
    const covered = partialPath(level.path, tracker.current.cum, tracker.current.progress)
    if (covered.length > 1) {
      tracePath(covered)
      ctx.strokeStyle = c.covered
      ctx.lineWidth = cw
      ctx.stroke()
    }

    const [sx, sy] = level.path[0]
    const [ex, ey] = level.path[level.path.length - 1]

    // the drawn trace exactly as recorded, one polyline per stroke (no smoothing)
    const s = recorder.current.series
    ctx.strokeStyle = c.trace
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
    ctx.fillStyle = c.card
    ctx.fill()
    ctx.strokeStyle = c.ink
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.beginPath()
    ctx.arc(ex * u, ey * u, r * 0.35, 0, Math.PI * 2)
    ctx.fillStyle = c.ink
    ctx.fill()

    ctx.beginPath()
    ctx.arc(sx * u, sy * u, r * 0.8, 0, Math.PI * 2)
    ctx.fillStyle = c.ink
    ctx.fill()
    ctx.beginPath()
    const tr = r * 0.35
    ctx.moveTo(sx * u - tr * 0.6, sy * u - tr)
    ctx.lineTo(sx * u + tr, sy * u)
    ctx.lineTo(sx * u - tr * 0.6, sy * u + tr)
    ctx.closePath()
    ctx.fillStyle = c.card
    ctx.fill()

    // text labels (never colour alone)
    ctx.font = FONT
    ctx.fillStyle = c.ink
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
      const ih = window.innerHeight
      const px = Math.max(220, Math.floor(Math.min(w, MAX_PX, ih * MAX_VH, Math.max(ih * 0.5, ih - PAGE_RESERVE_PX))))
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
      // Reset, or React StrictMode's mount/unmount/mount leaves a cancelled id here and
      // requestDraw never schedules again (blank canvas).
      raf.current = undefined
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
      setStatus('done')
      onCompleteRef.current(
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
    [config, level],
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
    idle: 'Začnite pri točki „Začetek“.',
    missedStart: 'Najprej pritisnite na točko „Začetek“.',
    drawing: 'Sledite poti do konca.',
    lifted: 'Nadaljujte tam, kjer ste ostali.',
    done: 'Končano.',
  }[status]
  const pct = Math.round(fraction * 100)
  // a calm pulse around the start marker until the first press
  const [sx, sy] = level.path[0]
  const ring = Math.max(44, (level.channelWidth / LEVEL_UNITS) * size * 1.7)
  const showStart = status === 'idle' || status === 'missedStart'

  return (
    <div className="flex flex-col items-center gap-3" ref={wrapRef}>
      <div className="relative" style={{ width: size, height: size }}>
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
          className="rounded-xl bg-card ring-1 ring-border"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          onLostPointerCapture={onPointerUp}
          onContextMenu={(e) => e.preventDefault()}
        />
        {showStart ? (
          <span
            aria-hidden
            className="pointer-events-none absolute rounded-full border-[3px] border-primary motion-safe:animate-pulse"
            style={{
              width: ring,
              height: ring,
              left: (sx / LEVEL_UNITS) * size - ring / 2,
              top: (sy / LEVEL_UNITS) * size - ring / 2,
            }}
          />
        ) : null}
      </div>
      <div
        role="progressbar"
        aria-label="Prevožena pot"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="h-2 w-full overflow-hidden rounded-full bg-muted ring-1 ring-border ring-inset"
        style={{ maxWidth: size }}
      >
        <div className="h-full rounded-full bg-primary transition-[width] duration-150" style={{ width: `${pct}%` }} />
      </div>
      <div className="flex w-full items-center justify-between gap-4" style={{ maxWidth: size }}>
        <p className="text-[1.0625rem] font-medium" aria-live="polite">
          {hint}
        </p>
        {status === 'done' ? null : (
          <button
            type="button"
            className="-mr-2 shrink-0 rounded-lg px-2 py-1 text-[0.95rem] text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-primary"
            onClick={() => finish(false, 'cannot_today')}
          >
            Danes ne morem
          </button>
        )}
      </div>
    </div>
  )
}
