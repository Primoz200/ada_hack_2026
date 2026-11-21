// The looping demonstration on the intro of each camera exercise: a flat dark-grey pictogram (seated
// figure for the arms, a large hand for the hand) moving between its two healthy end positions. A faint
// ghost of the active end, and for the arms the path of the wrists, keep the target visible mid-loop.
// Geometry and timing: model.ts. With prefers-reduced-motion the two end positions stand side by side.
import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { cn } from '@/lib/utils'
import type { Hand } from '../../shared/types'
import { PROMPT_WORDS, type Prompt } from '../cues'
import {
  BOX,
  cuePrompt,
  DEMO_LABEL,
  demoKind,
  figurePose,
  GAP,
  handPose,
  isActive,
  mirrorPt,
  pathD,
  phaseAt,
  progressAt,
  STROKE,
  wristPath,
  type DemoKind,
  type Pt,
} from './model'

// Opaque mixes of the two tokens, so overlapping parts never darken each other.
const INK = 'color-mix(in oklab, var(--foreground) 80%, var(--muted))'
const GHOST = 'color-mix(in oklab, var(--foreground) 12%, var(--muted))'
const TRACE = 'color-mix(in oklab, var(--foreground) 30%, var(--muted))'
const PANEL = 'var(--muted)'

export interface ExerciseDemoProps {
  exerciseKey: string
  detector?: string
  /** the tested hand; the hand demonstration shows it as in the mirrored camera preview */
  hand: Hand
  /** fixed point of the loop (0..1): no animation (tests, screenshots) */
  phase?: number
  /** the cue word that belongs to the current movement; null when nothing moves (reduced motion) */
  onCue?: (prompt: Prompt | null) => void
  className?: string
}

export function ExerciseDemo({ exerciseKey, detector, hand, phase, onCue, className }: ExerciseDemoProps) {
  const kind = demoKind(exerciseKey, detector)
  const reduced = usePrefersReducedMotion()
  const animate = kind !== null && phase === undefined && !reduced
  const [livePhase, setLivePhase] = useState(0)
  const shown = phase ?? livePhase

  useEffect(() => {
    if (!animate || !kind) return
    let raf = 0
    const t0 = performance.now()
    const tick = (now: number) => {
      setLivePhase(phaseAt(now - t0, kind))
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [animate, kind])

  // tell the intro which word goes with the movement, only when it changes
  const onCueRef = useRef(onCue)
  useEffect(() => {
    onCueRef.current = onCue
  }, [onCue])
  const cue = kind === null || reduced ? null : cuePrompt(kind, isActive(shown))
  useEffect(() => {
    onCueRef.current?.(cue)
  }, [cue])

  if (!kind) return null

  if (reduced) {
    return (
      // the two end positions side by side, in the order of the cue words (active first)
      <div role="img" aria-label={DEMO_LABEL[kind]} className={cn('grid grid-cols-2 gap-x-4', className)}>
        {[1, 0].map((t) => (
          <figure key={t} className="flex flex-col items-center gap-1.5">
            <Drawing kind={kind} hand={hand} t={t} ghost={false} className="aspect-[200/212] w-full" />
            <figcaption className="text-[1.0625rem] font-semibold text-foreground">
              {PROMPT_WORDS[cuePrompt(kind, t === 1)]}
            </figcaption>
          </figure>
        ))}
      </div>
    )
  }

  return (
    <Drawing
      kind={kind}
      hand={hand}
      t={progressAt(shown)}
      ghost
      role="img"
      ariaLabel={DEMO_LABEL[kind]}
      className={cn('aspect-[200/212]', className)}
    />
  )
}

function Drawing({
  kind,
  hand,
  t,
  ghost,
  role,
  ariaLabel,
  className,
}: {
  kind: DemoKind
  hand: Hand
  t: number
  ghost: boolean
  role?: 'img'
  ariaLabel?: string
  className?: string
}) {
  return (
    <svg
      viewBox={`0 0 ${BOX.w} ${BOX.h}`}
      role={role}
      aria-label={ariaLabel}
      aria-hidden={role ? undefined : true}
      className={cn('block overflow-visible', className)}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {kind === 'hand' ? <HandDrawing hand={hand} t={t} ghost={ghost} /> : <FigureDrawing kind={kind} t={t} ghost={ghost} />}
    </svg>
  )
}

// ---------------------------------------------------------------- seated figure

function FigureDrawing({ kind, t, ghost }: { kind: 'abduction' | 'raise'; t: number; ghost: boolean }) {
  const p = figurePose(kind, t)
  const end = figurePose(kind, 1)
  // the side arc says "through the side"; the forward path of the raise has no clean front-view trace
  const path = kind === 'abduction' ? wristPath(kind) : null
  const outline = STROKE + 2 * GAP * Math.min(1, p.forward * 2.5)
  return (
    <g>
      {ghost ? (
        <g>
          {path
            ? [path, path.map(mirrorPt)].map((pts, i) => (
                <path key={i} d={pathD(pts)} stroke={TRACE} strokeWidth={1.5} />
              ))
            : null}
          {[0, 1].map((i) => (
            <line
              key={i}
              x1={end.shoulders[i].x}
              y1={end.shoulders[i].y}
              x2={end.wrists[i].x}
              y2={end.wrists[i].y}
              stroke={GHOST}
              strokeWidth={STROKE}
            />
          ))}
        </g>
      ) : null}
      <Line a={p.seat[0]} b={p.seat[1]} stroke={GHOST} />
      <g stroke={INK} strokeWidth={STROKE}>
        <circle cx={p.head.x} cy={p.head.y} r={p.headR} fill={INK} stroke="none" />
        {p.legs.map((leg, i) => (
          <path key={i} d={pathD(leg)} />
        ))}
        <line x1={p.neck.x} y1={p.neck.y} x2={p.hip.x} y2={p.hip.y} />
        <line x1={p.shoulders[0].x} y1={p.shoulders[0].y} x2={p.shoulders[1].x} y2={p.shoulders[1].y} />
        {[0, 1].map((i) => (
          <g key={i}>
            {outline > STROKE ? (
              <line
                x1={p.shoulders[i].x}
                y1={p.shoulders[i].y}
                x2={p.wrists[i].x}
                y2={p.wrists[i].y}
                stroke={PANEL}
                strokeWidth={outline}
              />
            ) : null}
            <line x1={p.shoulders[i].x} y1={p.shoulders[i].y} x2={p.wrists[i].x} y2={p.wrists[i].y} />
          </g>
        ))}
      </g>
    </g>
  )
}

// ---------------------------------------------------------------- hand

function HandDrawing({ hand, t, ghost }: { hand: Hand; t: number; ghost: boolean }) {
  const p = handPose(t, hand)
  return (
    <g>
      <Line a={p.table[0]} b={p.table[1]} stroke={GHOST} />
      {ghost ? <HandShape hand={hand} t={1} color={GHOST} /> : null}
      <HandShape hand={hand} t={t} color={INK} />
    </g>
  )
}

function HandShape({ hand, t, color }: { hand: Hand; t: number; color: string }) {
  const p = handPose(t, hand)
  // the outline that separates curled fingers and the thumb from the palm grows as the hand closes
  const outline = STROKE + 2 * GAP * p.closed
  return (
    <g stroke={color} strokeWidth={STROKE}>
      <line
        x1={p.forearm[0].x}
        y1={p.forearm[0].y}
        x2={p.forearm[1].x}
        y2={p.forearm[1].y}
        strokeWidth={p.forearmWidth}
      />
      <path d={pathD(p.palm, true)} fill={color} />
      {[...p.fingers, p.thumb].map((f, i) => (
        <g key={i}>
          {p.closed > 0 && color === INK ? <path d={pathD(f)} stroke={PANEL} strokeWidth={outline} /> : null}
          <path d={pathD(f)} />
        </g>
      ))}
    </g>
  )
}

function Line({ a, b, stroke }: { a: Pt; b: Pt; stroke: string }) {
  return <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={stroke} strokeWidth={STROKE} />
}

// ---------------------------------------------------------------- reduced motion

const QUERY = '(prefers-reduced-motion: reduce)'

function subscribe(cb: () => void) {
  if (typeof window === 'undefined' || !window.matchMedia) return () => undefined
  const m = window.matchMedia(QUERY)
  m.addEventListener('change', cb)
  return () => m.removeEventListener('change', cb)
}

export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => (typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(QUERY).matches : false),
    () => false,
  )
}
