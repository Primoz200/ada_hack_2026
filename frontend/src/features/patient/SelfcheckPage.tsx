// Samopregled: one wizard page. Steps come from home.steps (ratings, then the games), then the
// result. Game steps render through GAMES[gameType], so a new game plugs in from the API.
import { ArrowRight, CircleCheck, CloudOff, Hand, LoaderCircle, RotateCcw, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { paths } from '@/app/paths'
import { api, unwrap, type PatientHome, type Question } from '@/client/api'
import { Panel } from '@/components/app/Panel'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { GAMES } from '@/games/registry'
import type { GameResult, GameType, Hand as HandSide } from '@/games/shared/types'
import { useAsync } from '@/lib/useAsync'
import { handPhrase } from './format'
import { RatingScale } from './RatingScale'
import { RecoveryChart } from './RecoveryChart'
import { StepBar, StepRail } from './StepIndicator'
import { Column, FeedbackMark, Heading, LoadError, PanelSkeleton, slateOutline } from './ui'
import { buildWizard, startIndex, type WizardStep } from './wizard'

/** How long the "Shranjeno" confirmation stays before the next step. */
const ADVANCE_MS = 1400

/** One line of instruction per game type; a game without an entry gets the generic one. */
const INSTRUCTIONS: Partial<Record<GameType, string>> = {
  trace: 'Sledite poti čim natančneje, v svojem tempu.',
}
const GENERIC_INSTRUCTION = 'Sledite navodilom na zaslonu, v svojem tempu.'

const DEFAULT_QUESTIONS = {
  wellbeing: { text: 'Kako se počutite danes?', minLabel: 'Zelo slabo', maxLabel: 'Odlično' },
  pain: { text: 'Kako močna je bolečina?', minLabel: 'Brez bolečine', maxLabel: 'Zelo močna' },
}

export function SelfcheckPage() {
  const { patientId = '' } = useParams()
  const home = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/home', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  const exit = (
    <Link
      to={paths.patientHome(patientId)}
      className="inline-flex h-12 items-center gap-2 rounded-lg px-3 text-base font-medium text-muted-foreground transition-colors hover:bg-card hover:text-primary"
    >
      <X className="size-5" aria-hidden />
      Prekini
    </Link>
  )

  if (home.error && !home.data) {
    return (
      <Column>
        <Heading aside={exit}>Samopregled</Heading>
        <Panel>
          <LoadError onRetry={home.reload} />
        </Panel>
      </Column>
    )
  }
  if (!home.data) {
    return (
      <Column>
        <Heading aside={exit}>Samopregled</Heading>
        <Panel>
          <div className="grid gap-10 lg:grid-cols-[250px_minmax(0,1fr)]">
            <div className="space-y-5">
              {[0, 1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
            <Skeleton className="aspect-square w-full max-w-[540px]" />
          </div>
        </Panel>
      </Column>
    )
  }
  // keyed by patient so switching patients starts a fresh wizard
  return <Wizard key={home.data.patientId} home={home.data} exit={exit} />
}

function Wizard({ home, exit }: { home: PatientHome; exit: React.ReactNode }) {
  const navigate = useNavigate()
  // frozen for this visit: a refetch of home must not move the patient
  const [steps] = useState(() => buildWizard(home.steps))
  const [index, setIndex] = useState(() => startIndex(home.steps))
  const step = steps[index]
  const atResult = step.kind === 'result'

  const frame = { steps, index, hand: home.hand }
  const advance = () => {
    setIndex((i) => Math.min(i + 1, steps.length - 1))
    window.scrollTo({ top: 0 })
  }

  return (
    <Column>
      <Heading aside={atResult ? null : exit}>
        {atResult ? (
          <>
            Samopregled je <span className="text-brand">končan</span>
          </>
        ) : (
          'Samopregled'
        )}
      </Heading>
      <Panel className="p-6 sm:p-8 md:p-8">
        {step.kind === 'ratings' ? (
          <RatingsStep
            key={step.key}
            frame={frame}
            patientId={home.patientId}
            pathwayCode={home.pathwayCode}
            onDone={advance}
          />
        ) : step.kind === 'game' ? (
          <GameStep
            key={step.key}
            frame={frame}
            step={step}
            hand={home.hand}
            patientId={home.patientId}
            next={steps[index + 1]}
            onDone={advance}
          />
        ) : (
          <ResultStep frame={frame} patientId={home.patientId} onHome={() => navigate(paths.patientHome(home.patientId))} />
        )}
      </Panel>
    </Column>
  )
}

function capitalise(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

interface Frame {
  steps: WizardStep[]
  index: number
  hand: HandSide
}

/**
 * Two columns on desktop: the step list with the current instruction (and any status) on the
 * left, the step itself on the right. On a phone the status goes under the step instead.
 */
function StepLayout({
  frame,
  status,
  statusKey,
  children,
}: {
  frame: Frame
  status?: React.ReactNode
  /** changes whenever the status content changes, so the phone view follows it */
  statusKey?: string
  children: React.ReactNode
}) {
  const step = frame.steps[frame.index]
  const note = <StepNote step={step} hand={frame.hand} />
  // on a phone the status sits under the canvas, often below the fold: bring it into view
  const phoneStatus = useRef<HTMLDivElement>(null)
  const hasStatus = Boolean(status)
  useEffect(() => {
    if (!hasStatus || window.matchMedia('(min-width: 1024px)').matches) return
    const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    phoneStatus.current?.scrollIntoView({ block: 'nearest', behavior: smooth ? 'smooth' : 'auto' })
  }, [hasStatus, statusKey])
  return (
    <div className="grid gap-7 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-12">
      <aside className="min-w-0">
        <div className="hidden lg:block">
          <StepRail steps={frame.steps} current={frame.index}>
            {note}
            {status ? <div className="mt-5">{status}</div> : null}
          </StepRail>
        </div>
        <div className="space-y-4 lg:hidden">
          <StepBar steps={frame.steps} current={frame.index} />
          {step.kind === 'result' ? null : (
            <div>
              <h2 className="text-2xl font-bold">{step.title}</h2>
              <div className="mt-1.5">{note}</div>
            </div>
          )}
        </div>
      </aside>
      <div className="min-w-0">
        {children}
        {status ? (
          <div ref={phoneStatus} className="mt-5 scroll-mb-6 lg:hidden">
            {status}
          </div>
        ) : null}
      </div>
    </div>
  )
}

/** The instruction under the current step's title. */
function StepNote({ step, hand }: { step: WizardStep; hand: HandSide }) {
  if (step.kind === 'ratings') {
    return <p className="text-muted-foreground">Za vsako vprašanje izberite eno številko.</p>
  }
  if (step.kind === 'result') {
    return <p className="text-muted-foreground">Hvala za današnji samopregled.</p>
  }
  return (
    <div className="space-y-2.5">
      <p className="text-muted-foreground">{INSTRUCTIONS[step.gameType] ?? GENERIC_INSTRUCTION}</p>
      <p className="inline-flex items-center gap-2 rounded-md bg-accent px-2.5 py-1 text-[0.95rem] font-semibold text-accent-foreground">
        <Hand className="size-[18px]" aria-hidden />
        {capitalise(handPhrase(hand))}
      </p>
    </div>
  )
}

// ---------------------------------------------------------------- ratings

function RatingsStep({
  frame,
  patientId,
  pathwayCode,
  onDone,
}: {
  frame: Frame
  patientId: string
  pathwayCode: string
  onDone: () => void
}) {
  // labels come from the pathway; the defaults are the same words
  const pathways = useAsync(() => unwrap(api.GET('/api/pathways')), [])
  const questions = pathways.data?.find((p) => p.code === pathwayCode)?.questions ?? []
  const q = (id: 'wellbeing' | 'pain') => {
    const found: Question | undefined = questions.find((x) => x.id === id)
    const d = DEFAULT_QUESTIONS[id]
    return { text: found?.text ?? d.text, minLabel: found?.minLabel ?? d.minLabel, maxLabel: found?.maxLabel ?? d.maxLabel }
  }
  const [wellbeing, setWellbeing] = useState<number>()
  const [pain, setPain] = useState<number>()
  const [saving, setSaving] = useState(false)
  const [failed, setFailed] = useState(false)
  const ready = wellbeing !== undefined && pain !== undefined

  const submit = async () => {
    if (!ready || saving) return
    setSaving(true)
    setFailed(false)
    try {
      await unwrap(api.POST('/api/checkins', { body: { patientId, wellbeing, pain } }))
      onDone()
    } catch {
      setFailed(true)
      setSaving(false)
    }
  }

  const w = q('wellbeing')
  const p = q('pain')
  return (
    <StepLayout frame={frame}>
      <div className="space-y-9">
        <RatingScale question={w.text} minLabel={w.minLabel} maxLabel={w.maxLabel} value={wellbeing} onChange={setWellbeing} />
        <div className="border-t border-border pt-8">
          <RatingScale question={p.text} minLabel={p.minLabel} maxLabel={p.maxLabel} value={pain} onChange={setPain} />
        </div>
        <div className="flex flex-col gap-4 border-t border-border pt-8 sm:flex-row sm:items-center">
          <Button variant="cta" size="xl" className="w-full sm:w-auto sm:min-w-56" disabled={!ready || saving} onClick={submit}>
            {saving ? <LoaderCircle className="animate-spin" aria-hidden /> : null}
            {failed ? 'Poskusi znova' : 'Naprej'}
            {saving ? null : <ArrowRight aria-hidden />}
          </Button>
          <p className="text-[0.95rem] text-muted-foreground" aria-live="polite">
            {failed
              ? 'Odgovorov ni bilo mogoče shraniti. Preverite povezavo in poskusite znova.'
              : ready
                ? 'Sledijo kratke naloge z roko.'
                : 'Izberite odgovor na obe vprašanji.'}
          </p>
        </div>
      </div>
    </StepLayout>
  )
}

// ---------------------------------------------------------------- games

type Phase = 'play' | 'saving' | 'saved' | 'incomplete' | 'error'

function GameStep({
  frame,
  step,
  hand,
  patientId,
  next,
  onDone,
}: {
  frame: Frame
  step: Extract<WizardStep, { kind: 'game' }>
  hand: HandSide
  patientId: string
  next: WizardStep | undefined
  onDone: () => void
}) {
  const [attempt, setAttempt] = useState(0)
  const [phase, setPhase] = useState<Phase>('play')
  const [reason, setReason] = useState<string>()
  // the result is kept until the server has it, so a network error loses nothing
  const pending = useRef<GameResult | undefined>(undefined)
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  useEffect(() => () => clearTimeout(advanceTimer.current), [])

  const config = useMemo(
    () => ({ gameType: step.gameType, level: step.level, hand, patientId }),
    [step.gameType, step.level, hand, patientId],
  )

  // posted from the game's callback, not from an effect (StrictMode runs effects twice)
  const send = async () => {
    const result = pending.current
    if (!result) return
    setPhase('saving')
    try {
      await unwrap(api.POST('/api/sessions', { body: { patientId, ...result } }))
      pending.current = undefined
      if (result.completed) {
        setPhase('saved')
        advanceTimer.current = setTimeout(onDone, ADVANCE_MS)
      } else {
        setPhase('incomplete')
      }
    } catch {
      setPhase('error')
    }
  }

  const onComplete = (result: GameResult) => {
    pending.current = result
    setReason(result.completed ? undefined : result.abortReason)
    void send()
  }
  // a new attempt remounts the game: its internal state never resets by itself
  const retry = () => {
    setPhase('play')
    setAttempt((a) => a + 1)
  }

  const Game = GAMES[step.gameType]
  const status =
    phase === 'play' ? undefined : (
      <GameStatus
        phase={phase}
        reason={reason}
        nextTitle={next?.kind === 'result' ? undefined : next?.title}
        onResend={send}
        onRetry={retry}
        onNext={onDone}
      />
    )
  return (
    <StepLayout frame={frame} status={status} statusKey={phase}>
      <Game key={`${step.key}#${attempt}`} config={config} onComplete={onComplete} onAbort={onDone} />
    </StepLayout>
  )
}

function GameStatus({
  phase,
  reason,
  nextTitle,
  onResend,
  onRetry,
  onNext,
}: {
  phase: Phase
  reason: string | undefined
  nextTitle: string | undefined
  onResend: () => void
  onRetry: () => void
  onNext: () => void
}) {
  const box = 'flex flex-col gap-4 rounded-xl bg-muted p-5'
  if (phase === 'saving') {
    return (
      <div className={box} aria-live="polite">
        <p className="flex items-center gap-3 text-lg font-medium">
          <LoaderCircle className="size-6 animate-spin text-primary" aria-hidden />
          Shranjujem …
        </p>
      </div>
    )
  }
  if (phase === 'saved') {
    return (
      <div className={box} aria-live="polite">
        <p className="flex items-center gap-3 text-lg">
          <CircleCheck className="size-7 shrink-0 text-brand" aria-hidden />
          <span>
            <span className="font-semibold">Shranjeno.</span>{' '}
            <span className="text-muted-foreground">{nextTitle ? `Sledi: ${nextTitle}.` : 'Sledi rezultat.'}</span>
          </span>
        </p>
      </div>
    )
  }
  if (phase === 'error') {
    return (
      <div className={box} role="alert">
        <p className="flex items-start gap-3">
          <CloudOff className="mt-0.5 size-6 shrink-0 text-primary" aria-hidden />
          <span>
            <span className="block font-semibold">Rezultata ni bilo mogoče poslati.</span>
            <span className="text-muted-foreground">Ostal je v tej napravi. Preverite povezavo in ga pošljite znova.</span>
          </span>
        </p>
        <Button size="lg" onClick={onResend} className="w-full sm:w-auto lg:w-full">
          <RotateCcw aria-hidden />
          Pošlji znova
        </Button>
      </div>
    )
  }
  // incomplete: time limit or "Danes ne morem"
  return (
    <div className={box} aria-live="polite">
      <p>
        <span className="block font-semibold">
          {reason === 'time_limit' ? 'Čas za to nalogo se je iztekel.' : 'Naloga ni bila dokončana.'}
        </span>
        <span className="text-muted-foreground">Lahko poskusite znova ali nadaljujete.</span>
      </p>
      <div className="flex flex-col gap-2.5 sm:flex-row lg:flex-col">
        <Button size="lg" onClick={onRetry}>
          <RotateCcw aria-hidden />
          Poskusi znova
        </Button>
        <Button size="lg" variant="outline" className={slateOutline} onClick={onNext}>
          Naprej
          <ArrowRight aria-hidden />
        </Button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- result

function ResultStep({ frame, patientId, onHome }: { frame: Frame; patientId: string; onHome: () => void }) {
  const { data, error, reload } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/selfcheck/summary', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  if (error && !data) {
    return (
      <StepLayout frame={frame}>
        <LoadError onRetry={reload} />
      </StepLayout>
    )
  }
  if (!data) {
    return (
      <StepLayout frame={frame}>
        <PanelSkeleton lines={5} />
      </StepLayout>
    )
  }
  return (
    <StepLayout frame={frame}>
      <div>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <h2 className="text-[1.75rem] leading-tight font-bold">{data.title}</h2>
          <div className="shrink-0">
            <FeedbackMark tone={data.tone} trend={data.trend} />
          </div>
        </div>
        <p className="mt-3 max-w-[52ch] text-xl leading-relaxed">{data.text}</p>
        {data.points.length >= 2 ? (
          <figure className="mt-7">
            <figcaption className="mb-1 text-[0.95rem] font-medium text-muted-foreground">Zadnjih 14 dni</figcaption>
            <div className="-ml-2">
              <RecoveryChart points={data.points} height={220} label="Graf vaših rezultatov v zadnjih 14 dneh" />
            </div>
          </figure>
        ) : null}
        <div className="mt-8 border-t border-border pt-8">
          <Button variant="cta" size="xl" className="w-full sm:w-auto sm:min-w-56" onClick={onHome}>
            Domov
            <ArrowRight aria-hidden />
          </Button>
        </div>
      </div>
    </StepLayout>
  )
}
