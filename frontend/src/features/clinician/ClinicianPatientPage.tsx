// Patient detail for the clinician. Plan section 9, Zdravnik 2 and 3.
// Header (who, and when the next visit is) -> the alert -> the evidence -> how it was captured -> history.
// Each measurement (tracing, camera exercises) has its own trend; a two-way switch picks which one is shown.
import { useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft, CalendarClock, Camera, OctagonAlert, PenLine, TriangleAlert } from 'lucide-react'
import { api, unwrap, type Alert, type PatientDetail, type SessionSummary, type Timeline } from '@/client/api'
import { paths } from '@/app/paths'
import { Panel } from '@/components/app/Panel'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { useAsync } from '@/lib/useAsync'
import { AlertCard } from './AlertCard'
import { CameraSessions } from './CameraSessions'
import { Y_AXIS_WIDTH, CHART_MARGIN } from './chartLayout'
import { GameChart, PoorDot, regionWord, type View } from './GameChart'
import { ActionLog, CheckinHistory, ModelNote } from './PatientSections'
import { SessionReplay } from './SessionReplay'
import { SymptomPanel } from './SymptomPanel'
import {
  GAMES,
  GAME_TITLE,
  LEVELS,
  ageFrom,
  alertGameSet,
  countingSessions,
  dayMs,
  defaultMeasurement,
  deltaWords,
  featureComparison,
  formatDay,
  formatFeature,
  formatPct,
  gameMetric,
  gameSessions,
  hasGameData,
  isPoorQuality,
  latestModelVersion,
  levelName,
  nextVisitText,
  plural,
  timeDomain,
  trendSummary,
  visitWhen,
  type Game,
} from './model'
import { ErrorState, StatusBadge, UnderlineTabs } from './ui'

const MIN_SESSIONS_FOR_BASELINE = 4 // session 1 is practice, baseline = sessions 2-4
const SIDE_COL = 'grid gap-x-10 gap-y-6 lg:grid-cols-[minmax(0,1fr)_19rem]'

export function ClinicianPatientPage() {
  const { patientId = '' } = useParams()
  // a fresh page (measurement, level, selected session) for every patient
  return <PatientPage key={patientId} patientId={patientId} />
}

function PatientPage({ patientId }: { patientId: string }) {
  const patient = useAsync(() => unwrap(api.GET('/api/patients/{patient_id}', { params: { path: { patient_id: patientId } } })), [patientId])
  const timeline = useAsync(() => unwrap(api.GET('/api/patients/{patient_id}/timeline', { params: { path: { patient_id: patientId } } })), [patientId])
  const meta = useAsync(() => unwrap(api.GET('/api/meta')), [])
  // null = not chosen yet: follow the open alert (camera-only alert -> camera)
  const [chosen, setChosen] = useState<Game | null>(null)
  const [views, setViews] = useState<Record<Game, View>>({ trace: 'all', camera: 'all' })
  const [selectedIds, setSelectedIds] = useState<Record<Game, number | null>>({ trace: null, camera: null })

  const reload = () => {
    patient.reload()
    timeline.reload()
  }

  if ((patient.error && !patient.data) || (timeline.error && !timeline.data)) {
    return (
      <>
        <BackLink />
        <Panel>
          <ErrorState title="Podatkov o pacientu ni mogoče naložiti." message={(patient.error ?? timeline.error)?.message} onRetry={reload} />
        </Panel>
      </>
    )
  }
  if (!patient.data || !timeline.data) return <PageSkeleton />

  const p = patient.data
  const tl = timeline.data
  // one time axis for both measurements, so the ratings below never shift when switching
  const domain = timeDomain(tl)
  const hasCamera = hasGameData(tl, 'camera')
  const game: Game = hasCamera ? (chosen ?? defaultMeasurement(p.openAlert, true)) : 'trace'
  const view = views[game]
  const setView = (v: View) => setViews((cur) => ({ ...cur, [game]: v }))
  const sessions = gameSessions(tl.sessions, game)
  const latest = [...sessions].sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0]
  const selectedId = selectedIds[game]

  // tracing: the replay shows one level; camera: the list follows the level tab (all exercises on "Skupaj")
  const replayLevel = view !== 'all' ? view : (sessions.find((s) => s.id === selectedId)?.level ?? latest?.level ?? 1)
  const levelList = sessions.filter((s) => s.level === replayLevel).sort((a, b) => Date.parse(a.startedAt) - Date.parse(b.startedAt))
  const selected: SessionSummary | null =
    game === 'trace'
      ? (levelList.find((s) => s.id === selectedId) ?? levelList[levelList.length - 1] ?? null)
      : (sessions.find((s) => s.id === selectedId && (view === 'all' || s.level === view)) ??
        [...sessions].filter((s) => view === 'all' || s.level === view).sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0] ??
        null)
  // the next visit is often weeks beyond the chart: say so at the chart's right edge
  const visitBeyond = tl.nextVisitDate != null && dayMs(tl.nextVisitDate) > domain.end ? p.daysToNextVisit : null
  const hasPoor = sessions.some(isPoorQuality)

  const selectSession = (s: SessionSummary) => setSelectedIds((cur) => ({ ...cur, [game]: s.id }))
  const select = (s: SessionSummary) => {
    selectSession(s)
    document.getElementById('replay')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }

  const levelTabs = (
    <UnderlineTabs
      label={game === 'camera' ? 'Vaja' : 'Stopnja igre'}
      value={String(view)}
      onChange={(v) => setView(v === 'all' ? 'all' : (Number(v) as View))}
      items={[{ id: 'all', label: 'Skupaj' }, ...LEVELS.map((l) => ({ id: String(l), label: levelName(game, l) }))]}
    />
  )

  return (
    <>
      <BackLink />
      <PatientHeader p={p} today={tl.today} />

      <div className="space-y-6">
        {p.openAlert ? (
          <AlertCard
            alert={p.openAlert}
            patient={p}
            today={tl.today}
            meta={meta.data}
            onChanged={() => {
              // keep the measurement on screen when the alert it was derived from is closed
              setChosen(game)
              reload()
            }}
          />
        ) : (
          <Panel className="flex flex-wrap items-center gap-x-4 gap-y-2 py-6 md:py-7" data-testid="status-panel">
            <StatusBadge status={p.status} size="lg" />
            <p className="text-lg">{p.reason}</p>
            <span className="text-[0.9375rem] text-muted-foreground lg:ml-auto">Ni odprtega opozorila.</span>
          </Panel>
        )}

        <Panel>
          {hasCamera ? (
            <>
              <h2 className="text-2xl font-bold">Meritve glede na lastno izhodišče</h2>
              <div className="mt-5 flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
                <MeasurementSwitch value={game} onChange={setChosen} alert={p.openAlert} />
                {levelTabs}
              </div>
            </>
          ) : (
            <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
              <h2 className="text-2xl font-bold">Rezultati sledenja glede na lastno izhodišče</h2>
              {levelTabs}
            </div>
          )}

          <div className={cn(SIDE_COL, 'mt-6')}>
            <div className="relative min-w-0">
              {visitBeyond != null && (
                <span
                  className="pointer-events-none absolute -top-6 z-10 text-[0.875rem] font-semibold text-primary"
                  style={{ right: CHART_MARGIN.right }}
                >
                  naslednji pregled {visitWhen(visitBeyond)} →
                </span>
              )}
              <GameChart timeline={tl} game={game} view={view} domain={domain} selectedId={selected?.id ?? null} onSelectSession={select} />
              <ChartLegend game={game} isAll={view === 'all'} hasPoor={hasPoor} />
            </div>
            <BasisPanel tl={tl} game={game} view={view} />
          </div>

          <div className={cn(SIDE_COL, 'mt-8 border-t border-border pt-6')}>
            <div className="min-w-0">
              <h3 className="mb-3 text-lg font-bold" style={{ paddingLeft: Y_AXIS_WIDTH }}>
                Počutje in bolečina
              </h3>
              <SymptomPanel timeline={tl} questions={p.pathway.questions} domain={domain} />
            </div>
            <p className="self-center text-[0.9375rem] text-muted-foreground">
              Pacientova dnevna ocena od 1 do 10. Vsaka ocena ima svojo os, ker gresta lestvici v nasprotni smeri. Čas je poravnan z grafom zgoraj; navpične črte so opozorila.
            </p>
          </div>

          <div className="mt-6 border-t border-border pt-5">
            <ModelNote meta={meta.data} cameraVersion={hasCamera ? latestModelVersion(tl.sessions, 'camera') : null} />
          </div>
        </Panel>

        {game === 'trace' ? (
          <Panel id="replay">
            <h2 className="text-2xl font-bold">Predvajanje seje</h2>
            <p className="mt-1 mb-6 text-[0.9375rem] text-muted-foreground">Kako se zajame podatek: dejanska sled čez želeno črto, ob njej seja iz izhodišča.</p>
            <SessionReplay sessions={sessions} level={replayLevel} selected={selected} onSelect={selectSession} />
          </Panel>
        ) : (
          <Panel id="replay">
            <h2 className="text-2xl font-bold">Zadnje seje</h2>
            <p className="mt-1 mb-6 text-[0.9375rem] text-muted-foreground">
              Vaje s kamero: kako je pacient opravil posamezno vajo. Seja s slabim zajemom se shrani, a ne šteje v trend.
            </p>
            <CameraSessions sessions={sessions} level={view === 'all' ? null : view} selected={selected} onSelect={selectSession} />
          </Panel>
        )}

        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
          <Section title="Dnevne ocene" hint="Zadnjih 14 vnosov. Počutje: višje je bolje. Bolečina: višje je slabše.">
            <CheckinHistory checkins={tl.checkins} pathway={p.pathway} />
          </Section>
          <Section title="Dnevnik ukrepov" hint="Opozorila in kaj je zdravnik storil.">
            <ActionLog alerts={tl.alerts} meta={meta.data} />
          </Section>
        </div>
      </div>
    </>
  )
}

const GAME_ICON = { trace: PenLine, camera: Camera }

/** Two-way switch between the measurements. A measurement the open alert is about carries the alert's icon. */
function MeasurementSwitch({ value, onChange, alert }: { value: Game; onChange: (g: Game) => void; alert: Alert | null | undefined }) {
  const flagged = new Set(alert && alert.severity !== 'grey' ? alertGameSet(alert) : [])
  const FlagIcon = alert?.severity === 'red' ? OctagonAlert : TriangleAlert
  const flagColor = alert?.severity === 'red' ? 'text-status-red' : 'text-status-amber'
  return (
    <div role="radiogroup" aria-label="Meritev" className="flex w-full rounded-lg border border-input bg-card p-1 sm:inline-flex sm:w-auto" data-testid="measurement-switch">
      {GAMES.map((g) => {
        const on = value === g
        const Icon = GAME_ICON[g]
        return (
          <button
            key={g}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(g)}
            className={cn(
              'inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-md px-3 text-base font-semibold whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/45 sm:flex-none sm:px-4',
              on ? 'bg-primary text-primary-foreground' : 'text-primary hover:bg-accent',
            )}
          >
            <Icon className="hidden size-[1.125rem] sm:block" strokeWidth={1.75} aria-hidden />
            {GAME_TITLE[g]}
            {flagged.has(g) && (
              <span className={cn('-mr-1 inline-flex size-6 items-center justify-center rounded-full', on ? 'bg-card' : '', flagColor)}>
                <FlagIcon className="size-4" strokeWidth={2} aria-hidden />
                <span className="sr-only">(pod izhodiščem, odprto opozorilo)</span>
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

function BackLink() {
  return (
    <Link
      to={paths.clinician}
      className="mb-3 ml-2 inline-flex items-center gap-1.5 rounded-md text-[0.9375rem] font-medium text-primary hover:underline"
    >
      <ArrowLeft className="size-4" aria-hidden /> Pregled pacientov
    </Link>
  )
}

/** Who the patient is, and, prominently, how far away the next planned visit is. */
function PatientHeader({ p, today }: { p: PatientDetail; today: string }) {
  const side = p.side === 'left' ? 'leva roka' : 'desna roka'
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-x-10 gap-y-4 px-2">
      <div className="min-w-0">
        <h1 className="text-[2.25rem] leading-tight font-bold">{p.name}</h1>
        <p className="mt-1 text-lg text-muted-foreground" data-testid="patient-meta">
          {ageFrom(p.birthYear, today)} let<Sep />
          {p.pathway.name}<Sep />
          {side}<Sep />
          <span className="text-foreground">{p.daysSinceDischarge}. dan po odpustu</span>
        </p>
      </div>
      <div className="flex items-center gap-3.5" data-testid="next-visit" aria-label={nextVisitText(p.daysToNextVisit)}>
        <CalendarClock className="size-8 text-primary" strokeWidth={1.75} aria-hidden />
        <div>
          <div className="text-[0.9375rem] font-medium text-muted-foreground">Naslednji pregled</div>
          <div className="text-[1.625rem] leading-tight font-bold">
            {visitWhen(p.daysToNextVisit)}
            {p.nextVisitDate && <span className="tabular ml-2 text-lg font-medium text-muted-foreground">{formatDay(p.nextVisitDate)}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

function Sep() {
  return (
    <span className="mx-2 text-input" aria-hidden>
      ·
    </span>
  )
}

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <Panel>
      <h2 className="text-2xl font-bold">{title}</h2>
      {hint && <p className="mt-1 text-[0.9375rem] text-muted-foreground">{hint}</p>}
      <div className="mt-5">{children}</div>
    </Panel>
  )
}

function ChartLegend({ game, isAll, hasPoor }: { game: Game; isAll: boolean; hasPoor: boolean }) {
  const text =
    game === 'camera'
      ? isAll
        ? 'Črta: skupni trend vseh vaj s kamero glede na lastno izhodišče. Modri pas: izhodišče ±5 točk. Črtkano: prag opozorila.'
        : 'Bledi krogi: posamezne seje (klik odpre podrobnosti). Črta: glajen rezultat. Modri pas: izhodišče ±5 točk.'
      : isAll
        ? 'Črta: skupni trend vseh treh stopenj glede na lastno izhodišče. Modri pas: izhodišče ±5 točk. Črtkano: prag opozorila.'
        : 'Bledi krogi: posamezne seje (klik odpre predvajanje). Črta: glajen rezultat. Modri pas: izhodišče ±5 točk.'
  return (
    <p className="mt-2 text-[0.875rem] text-muted-foreground" style={{ paddingLeft: Y_AXIS_WIDTH }}>
      {text}
      {hasPoor && (
        <span className="ml-1 inline-flex items-center gap-1.5 whitespace-nowrap">
          <svg width="14" height="14" aria-hidden className="shrink-0">
            <PoorDot cx={7} cy={7} />
          </svg>
          slaba kakovost zajema, ne šteje
        </span>
      )}
    </p>
  )
}

/** "Never a bare score": change vs baseline, number of sessions, and the features that moved most. */
function BasisPanel({ tl, game, view }: { tl: Timeline; game: Game; view: View }) {
  const sum = trendSummary(tl.trends, gameMetric(game, view))
  const counted = countingSessions(tl.sessions, game)
  const scoped = view === 'all' ? counted : counted.filter((s) => s.level === view)
  const n = view === 'all' ? counted.length : sum.nSessions || scoped.length
  const nPoor = gameSessions(tl.sessions, game).filter((s) => isPoorQuality(s) && (view === 'all' || s.level === view)).length
  const fc = featureComparison(tl.sessions, view === 'all' ? null : view, 3, game)
  const noBaseline = sum.delta == null
  const latestScore = view === 'all' ? null : [...scoped].sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0]?.score
  const perLevel = game === 'camera' ? 'na vajo' : 'na stopnjo'

  return (
    <aside className="min-w-0 space-y-7" data-testid="basis-panel">
      <div>
        <h3 className="text-[0.9375rem] font-medium text-muted-foreground">Sprememba glede na izhodišče</h3>
        <p className="mt-1 text-[1.625rem] leading-tight font-bold">{noBaseline ? 'Še ni izhodišča' : capitalize(deltaWords(sum.delta))}</p>
        {n === 0 && nPoor === 0 ? (
          <p className="mt-1.5 text-[0.9375rem] text-muted-foreground">Za {game === 'camera' ? 'to vajo' : 'to stopnjo'} še ni sej.</p>
        ) : (
        <p className="mt-1.5 text-[0.9375rem] text-muted-foreground">
          Na podlagi {n} {plural(n, 'seje', 'sej', 'sej', 'sej')}
          {view !== 'all' && sum.baseline != null && <>; izhodišče: {regionWord(sum.baseline)}</>}
          {latestScore != null && <>; zadnja seja: {regionWord(latestScore)}</>}.
          {nPoor > 0 && (
            <>
              {' '}
              {nPoor} {plural(nPoor, 'seja', 'seji', 'seje', 'sej')} s slabim zajemom ne {plural(nPoor, 'šteje', 'štejeta', 'štejejo', 'šteje')}.
            </>
          )}
          {noBaseline && <> Prva seja je vaja, izhodišče je mediana sej 2–4, zato so potrebne vsaj {MIN_SESSIONS_FOR_BASELINE} seje.</>}
        </p>
        )}
      </div>

      <div>
        <h3 className="text-[0.9375rem] font-medium text-muted-foreground">Kaj se je najbolj premaknilo</h3>
        {fc.rows.length === 0 ? (
          <p className="mt-1.5 text-[0.9375rem]">Za primerjavo značilk je premalo sej (potrebnih je vsaj 5 {perLevel}).</p>
        ) : (
          <>
            <table className="mt-2 w-full text-[0.9375rem]" data-testid="feature-table">
              <thead>
                <tr className="text-left text-[0.8125rem] text-muted-foreground">
                  <th className="pb-1.5 font-medium">Značilka</th>
                  <th className="pb-1.5 pl-2 text-right font-medium">Prej</th>
                  <th className="pb-1.5 pl-2 text-right font-medium">Zdaj</th>
                  <th className="pb-1.5 pl-2 text-right font-medium">Sprememba</th>
                </tr>
              </thead>
              <tbody>
                {fc.rows.map((r) => (
                  <tr key={`${r.level}-${r.key}`} className="border-t border-border align-top">
                    <td className="py-2 pr-1 leading-snug">
                      {r.label}
                      {view === 'all' && <span className="block text-[0.8125rem] text-muted-foreground">{levelName(game, r.level)}</span>}
                    </td>
                    <td className="tabular py-2 pl-2 text-right text-muted-foreground">{formatFeature(r.baseline)}</td>
                    <td className="tabular py-2 pl-2 text-right text-muted-foreground">{formatFeature(r.recent)}</td>
                    <td className="tabular py-2 pl-2 text-right font-semibold">{formatPct(r.changePct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-[0.8125rem] text-muted-foreground">Prej: povprečje sej 2–4. Zdaj: zadnje tri seje.</p>
          </>
        )}
      </div>
    </aside>
  )
}

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

function PageSkeleton() {
  return (
    <div aria-busy>
      <BackLink />
      {/* on the blue-grey page the skeleton bars are white; inside panels they are the muted fill */}
      <div className="mb-6 flex items-end justify-between px-2">
        <div className="space-y-3">
          <Skeleton className="h-10 w-72 bg-card" />
          <Skeleton className="h-6 w-96 bg-card" />
        </div>
        <Skeleton className="h-14 w-56 bg-card" />
      </div>
      <div className="space-y-6">
        <Panel className="space-y-4">
          <Skeleton className="h-9 w-40" />
          <Skeleton className="h-8 w-[28rem]" />
          <Skeleton className="h-12 w-80" />
        </Panel>
        <Panel className="space-y-6">
          <Skeleton className="h-8 w-96" />
          <Skeleton className="h-80 w-full" />
        </Panel>
      </div>
    </div>
  )
}
