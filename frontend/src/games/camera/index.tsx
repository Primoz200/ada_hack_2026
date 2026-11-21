// Camera exercises: config.level 1 = hand open/close, 2 = arms to the side, 3 = arms up. The camera
// pipeline lives in session.ts (a port of the teammate's recorder); this file only shows its phases:
// intro -> starting -> framing -> countdown -> recording -> done, or "unavailable" (onAbort, the
// wizard then skips every camera step). Only landmark numbers leave the device, never video.
import { ArrowRight, CircleCheck, LoaderCircle, ScanEye, ShieldCheck, Timer, VideoOff } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, unwrap, type CameraExercise } from '@/client/api'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { GameProps, Hand } from '../shared/types'
import { PROMPT_WORDS, promptAt, type Prompt } from './cues'
import { exerciseCopy, FALLBACK_EXERCISES, findExercise, secondsPhrase, type ExerciseCopy } from './exercises'
import { ExerciseDemo, usePrefersReducedMotion } from './demo/ExerciseDemo'
import { demoKind } from './demo/model'
import { CameraSession, type SessionPhase } from './session'
import { devVideo, type Unavailable } from './source'

// ---------------------------------------------------------------- exercise definitions

let exercisesPromise: Promise<readonly CameraExercise[]> | undefined

/** GET /api/camera/exercises once per page; the built-in copy of exercises.py if it fails. */
function loadExercises(): Promise<readonly CameraExercise[]> {
  exercisesPromise ??= unwrap(api.GET('/api/camera/exercises'))
    .then((list) => (list.length > 0 ? list : FALLBACK_EXERCISES))
    .catch(() => {
      exercisesPromise = undefined
      return FALLBACK_EXERCISES
    })
  return exercisesPromise
}

function useExercises(): readonly CameraExercise[] | undefined {
  const [list, setList] = useState<readonly CameraExercise[]>()
  useEffect(() => {
    let alive = true
    void loadExercises().then((l) => alive && setList(l))
    return () => {
      alive = false
    }
  }, [])
  return list
}

export function CameraGame(props: GameProps) {
  const exercises = useExercises()
  if (!exercises) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Nalagam">
        <Skeleton className="h-7 w-full max-w-[52ch]" />
        <Skeleton className="h-7 w-2/3" />
        <Skeleton className="mt-6 h-14 w-56" />
      </div>
    )
  }
  const exercise = findExercise(exercises, props.config.level)
  if (!exercise) return <UnavailableView reason="model" onContinue={props.onAbort} />
  return <CameraExerciseView {...props} exercise={exercise} />
}

// ---------------------------------------------------------------- the exercise

type Stage = 'intro' | SessionPhase | 'unavailable'

/** After this long without a good frame, offer a quiet way on without the camera. */
const FRAMING_ESCAPE_MS = 25_000

function CameraExerciseView({ config, onComplete, onAbort, exercise }: GameProps & { exercise: CameraExercise }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const barRef = useRef<HTMLDivElement>(null)
  const session = useRef<CameraSession | null>(null)
  const [dev] = useState(() => devVideo())
  const [stage, setStage] = useState<Stage>(dev ? 'starting' : 'intro')
  const [reason, setReason] = useState<Unavailable>('no_camera')
  const [ratio, setRatio] = useState(16 / 9)
  const [framed, setFramed] = useState({ seen: false, steady: false })
  const [seen, setSeen] = useState(true)
  const [prompt, setPrompt] = useState<Prompt>('rest')
  const [count, setCount] = useState(3)
  const [escape, setEscape] = useState(false)
  const [granted, setGranted] = useState(false)
  const [stopped, setStopped] = useState(false)
  const copy = exerciseCopy(exercise)
  const isHand = exercise.detector === 'hand'

  // the latest callbacks, read by the session's listener
  const onCompleteRef = useRef(onComplete)
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // one session per mount; StrictMode's second mount gets a fresh one, cleanup releases the camera
  useEffect(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    const s = new CameraSession({
      video,
      canvas,
      exercise,
      config,
      dev,
      listener: {
        phase: (p) => setStage(p),
        videoSize: (w, h) => setRatio(w > 0 && h > 0 ? w / h : 16 / 9),
        framing: (f) =>
          setFramed((prev) => (prev.seen === f.seen && prev.steady === f.steady ? prev : { seen: f.seen, steady: f.steady })),
        seen: setSeen,
        unavailable: (r) => {
          setReason(r)
          setStage('unavailable')
        },
        complete: (result) => onCompleteRef.current(result),
      },
    })
    session.current = s
    if (dev) void s.start()
    return () => {
      s.dispose()
      if (session.current === s) session.current = null
    }
  }, [exercise, config, dev])

  // was the camera allowed before? then the button says "Začni vajo"
  useEffect(() => {
    let alive = true
    navigator.permissions
      ?.query({ name: 'camera' as PermissionName })
      .then((p) => alive && setGranted(p.state === 'granted'))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  // prompt word, countdown number and the time bar follow the session's clock
  useEffect(() => {
    if (stage !== 'countdown' && stage !== 'recording') return
    let raf = 0
    const tick = () => {
      const s = session.current
      if (!s) return
      if (stage === 'countdown') {
        setCount(Math.max(1, Math.ceil(s.countdownLeftMs() / 1000)))
      } else {
        const t = s.elapsedMs()
        setPrompt(promptAt(exercise, t))
        if (barRef.current) barRef.current.style.width = `${Math.min(100, (100 * t) / (exercise.durationS * 1000))}%`
      }
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [stage, exercise])

  useEffect(() => {
    // framing happens once per mount, so escape starts false and only ever turns on
    if (stage !== 'framing') return
    const t = setTimeout(() => setEscape(true), FRAMING_ESCAPE_MS)
    return () => clearTimeout(t)
  }, [stage])

  const begin = () => {
    const s = session.current
    if (!s) return
    s.unlockAudio()
    void s.start()
  }

  if (stage === 'unavailable') return <UnavailableView reason={reason} onContinue={onAbort} />

  const live = stage !== 'intro'
  const recording = stage === 'recording'
  return (
    <div className="flex flex-col items-center">
      {stage === 'intro' ? (
        <Intro exercise={exercise} copy={copy} hand={config.hand} granted={granted} onStart={begin} />
      ) : null}

      <div
        className={cn(
          'relative overflow-hidden rounded-xl bg-muted transition-shadow duration-200',
          stage === 'framing' && framed.steady ? 'ring-2 ring-brand' : 'ring-1 ring-border',
          live ? '' : 'hidden',
        )}
        style={{ aspectRatio: ratio, width: `min(100%, calc(${ratio.toFixed(4)} * min(48vh, 440px)))` }}
      >
        <video
          ref={videoRef}
          muted
          playsInline
          aria-label={isHand ? 'Slika s kamere: vaša dlan' : 'Slika s kamere: zgornji del telesa'}
          className={cn('size-full -scale-x-100 object-cover', stage === 'done' && 'opacity-0')}
        />
        <canvas
          ref={canvasRef}
          aria-hidden
          className={cn('pointer-events-none absolute inset-0 size-full -scale-x-100', stage === 'done' && 'opacity-0')}
        />
        {stage === 'starting' ? (
          <FrameMessage>
            <LoaderCircle className="size-7 animate-spin text-primary" aria-hidden />
            <span>Vklapljam kamero …</span>
          </FrameMessage>
        ) : null}
        {stage === 'countdown' ? (
          <div className="absolute inset-0 grid place-items-center" aria-live="assertive">
            <span className="grid size-28 place-items-center rounded-full bg-card/90 text-[3.5rem] font-bold text-primary tabular shadow-panel">
              {count}
            </span>
          </div>
        ) : null}
        {stage === 'done' ? (
          <FrameMessage>
            {stopped ? null : <CircleCheck className="size-9 text-brand" aria-hidden />}
            <span className="text-lg font-semibold text-foreground">{stopped ? 'Vaja je ustavljena.' : 'Vaja je končana.'}</span>
          </FrameMessage>
        ) : null}
      </div>

      {stage === 'framing' ? (
        <div className="mt-4 flex w-full max-w-[60ch] flex-col items-start gap-2 sm:items-center">
          <p className="flex items-start gap-2.5 text-[1.0625rem] font-medium" aria-live="polite">
            {framed.steady ? (
              <CircleCheck className="mt-0.5 size-5 shrink-0 text-brand" aria-hidden />
            ) : (
              <ScanEye className="mt-0.5 size-5 shrink-0 text-primary" aria-hidden />
            )}
            <span>{framed.steady ? 'Dobro. Ostanite tako, vaja se začne.' : framed.seen ? copy.framing : copy.notSeen}</span>
          </p>
          {escape ? (
            <button type="button" className={quietLink} onClick={onAbort}>
              Danes brez vaj s kamero
            </button>
          ) : null}
        </div>
      ) : null}

      {stage === 'countdown' || recording ? (
        <div className="mt-4 flex w-full flex-col items-center gap-3" style={{ maxWidth: 'min(100%, 640px)' }}>
          <p
            key={stage === 'countdown' ? 'ready' : prompt}
            className={cn(
              'text-center text-[2.75rem] leading-none font-bold tracking-[-0.02em] motion-safe:animate-in motion-safe:fade-in motion-safe:duration-150 sm:text-[3.25rem]',
              prompt === 'rest' || stage === 'countdown' ? 'text-muted-foreground' : 'text-foreground',
            )}
            aria-live="assertive"
          >
            {stage === 'countdown' ? 'Pripravite se' : PROMPT_WORDS[prompt]}
          </p>
          <div
            role="progressbar"
            aria-label="Čas vaje"
            className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted ring-1 ring-border ring-inset"
          >
            <div ref={barRef} className="h-full w-0 rounded-full bg-primary" />
          </div>
          <div className="flex min-h-10 w-full items-center justify-between gap-4">
            <p className="text-[0.95rem] text-muted-foreground" aria-live="polite">
              {recording && !seen ? (isHand ? 'Dlani trenutno ne vidimo.' : 'Trenutno vas ne vidimo v celoti.') : ''}
            </p>
            {recording ? (
              <button type="button" className={cn(quietLink, '-mr-2')} onClick={() => {
                  setStopped(true)
                  session.current?.stop()
                }}>
                Prekini
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}

const quietLink =
  'shrink-0 rounded-lg px-2 py-3 text-[0.95rem] text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-primary'

function FrameMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-muted text-[1.0625rem] font-medium text-muted-foreground">
      {children}
    </div>
  )
}

/**
 * Before the camera starts: how to sit, then the cue words exactly as they will appear during the
 * exercise (large, in the same weight), so the screen teaches itself.
 */
function Intro({
  exercise,
  copy,
  hand,
  granted,
  onStart,
}: {
  exercise: CameraExercise
  copy: ExerciseCopy
  hand: Hand
  granted: boolean
  onStart: () => void
}) {
  const row = 'flex items-start gap-3'
  const icon = 'mt-0.5 size-5 shrink-0 text-primary'
  // the word that goes with what the demonstration is doing right now; null = both (reduced motion)
  const [cue, setCue] = useState<Prompt | null>(null)
  const hasDemo = demoKind(exercise.key, exercise.detector) !== null
  // moving: one figure; reduced motion: both end positions side by side, a little smaller
  const still = usePrefersReducedMotion()
  return (
    <div className="w-full">
      <p className="max-w-[52ch] text-xl leading-relaxed">{copy.setup}</p>
      <div className="mt-5 flex flex-col rounded-xl bg-muted px-5 sm:flex-row sm:items-center sm:gap-3 sm:pr-4">
        {hasDemo ? (
          <ExerciseDemo
            exerciseKey={exercise.key}
            detector={exercise.detector}
            hand={hand}
            onCue={setCue}
            className={
              still
                ? 'mx-auto mt-4 w-60 shrink-0 sm:order-last sm:my-4'
                : 'mx-auto mt-4 h-48 shrink-0 sm:order-last sm:my-4 sm:h-56'
            }
          />
        ) : null}
        <dl className="min-w-0 flex-1 divide-y divide-border">
          {copy.cues.map((c) => (
            <div key={c.word} className="flex items-center gap-5 py-3.5">
              <dt
                className={cn(
                  'w-[6.5rem] shrink-0 text-[1.5rem] leading-none font-bold tracking-[-0.02em] transition-colors duration-200 sm:w-28 sm:text-[1.75rem]',
                  cue === null || PROMPT_WORDS[cue] === c.word ? 'text-foreground' : 'text-muted-foreground',
                )}
              >
                {c.word}
              </dt>
              <dd className="min-w-0">
                <span className="block text-[0.95rem] font-medium text-muted-foreground">{c.when}</span>
                <span className="block text-[1.0625rem] text-pretty">{c.what}</span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
      <ul className="mt-5 space-y-2.5 text-[1.0625rem]">
        <li className={row}>
          <Timer className={icon} aria-hidden />
          <span>Vaja traja {secondsPhrase(exercise.durationS)}. Naj bo zvok vklopljen.</span>
        </li>
        <li className={row}>
          <ShieldCheck className={icon} aria-hidden />
          <span className="text-muted-foreground">Posnetek ne zapusti vaše naprave; shranijo se samo točke gibanja.</span>
        </li>
      </ul>
      <div className="mt-7 border-t border-border pt-7">
        <Button size="xl" className="w-full sm:w-auto sm:min-w-56" onClick={onStart}>
          {granted ? 'Začni vajo' : 'Vklopi kamero'}
          <ArrowRight aria-hidden />
        </Button>
      </div>
    </div>
  )
}

const UNAVAILABLE: Record<Unavailable, { title: string; body: string }> = {
  unsupported: {
    title: 'Kamera v tem brskalniku ni na voljo',
    body: 'Ta brskalnik ne omogoča uporabe kamere.',
  },
  no_camera: {
    title: 'Kamere nismo našli',
    body: 'V tej napravi ni kamere ali pa ni priključena.',
  },
  denied: {
    title: 'Dostop do kamere ni dovoljen',
    body: 'Dovoljenje lahko kadar koli spremenite v nastavitvah brskalnika.',
  },
  busy: {
    title: 'Kamera je zasedena',
    body: 'Morda jo uporablja drug program. Ob naslednjem samopregledu bo verjetno spet na voljo.',
  },
  model: {
    title: 'Vaj s kamero ni bilo mogoče pripraviti',
    body: 'Morda je povezava z internetom prešibka. Ob naslednjem samopregledu bodo spet na voljo.',
  },
}

function UnavailableView({ reason, onContinue }: { reason: Unavailable; onContinue: () => void }) {
  const m = UNAVAILABLE[reason]
  return (
    <div className="w-full" role="status">
      <div className="flex items-start gap-4">
        <span className="grid size-12 shrink-0 place-items-center rounded-full bg-muted text-primary">
          <VideoOff className="size-6" aria-hidden />
        </span>
        <div className="min-w-0">
          <h3 className="text-2xl font-bold">{m.title}</h3>
          <p className="mt-1.5 text-[1.0625rem] text-muted-foreground">{m.body}</p>
        </div>
      </div>
      <p className="mt-6 max-w-[52ch] text-xl leading-relaxed">
        Vaje s kamero danes izpustimo. Samopregled lahko vseeno zaključite.
      </p>
      <div className="mt-8 border-t border-border pt-8">
        <Button size="xl" className="w-full sm:w-auto sm:min-w-56" onClick={onContinue}>
          Nadaljuj
          <ArrowRight aria-hidden />
        </Button>
      </div>
    </div>
  )
}
