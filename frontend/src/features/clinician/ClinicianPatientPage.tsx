// Patient detail for the clinician. Plan section 9, Zdravnik 2 and 3.
import { useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft } from 'lucide-react'
import { api, unwrap, type SessionSummary, type Timeline } from '@/client/api'
import { paths } from '@/app/paths'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAsync } from '@/lib/useAsync'
import { AlertCard } from './AlertCard'
import { GameChart, regionWord, type View } from './GameChart'
import { ActionLog, CheckinHistory, ModelNote } from './PatientSections'
import { SessionReplay } from './SessionReplay'
import { SymptomPanel } from './SymptomPanel'
import {
  LEVELS,
  LEVEL_NAMES,
  ageFrom,
  deltaWords,
  featureComparison,
  formatDay,
  formatFeature,
  nextVisitText,
  plural,
  timeDomain,
  trendSummary,
} from './model'
import { PageState, StatusBadge } from './ui'

const MIN_SESSIONS_FOR_BASELINE = 4 // session 1 is practice, baseline = sessions 2-4

export function ClinicianPatientPage() {
  const { patientId = '' } = useParams()
  const patient = useAsync(() => unwrap(api.GET('/api/patients/{patient_id}', { params: { path: { patient_id: patientId } } })), [patientId])
  const timeline = useAsync(() => unwrap(api.GET('/api/patients/{patient_id}/timeline', { params: { path: { patient_id: patientId } } })), [patientId])
  const meta = useAsync(() => unwrap(api.GET('/api/meta')), [])
  const [view, setView] = useState<View>('all')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const reload = () => {
    patient.reload()
    timeline.reload()
  }

  if ((patient.error && !patient.data) || (timeline.error && !timeline.data)) {
    return (
      <div className="space-y-4">
        <BackLink />
        <PageState>Pacienta ni mogoče naložiti: {(patient.error ?? timeline.error)?.message}</PageState>
      </div>
    )
  }
  if (!patient.data || !timeline.data) return <PageSkeleton />

  const p = patient.data
  const tl = timeline.data
  const domain = timeDomain(tl)
  const traceSessions = tl.sessions.filter((s) => s.gameType === 'trace')
  const latest = [...traceSessions].sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0]
  const replayLevel = view !== 'all' ? view : (traceSessions.find((s) => s.id === selectedId)?.level ?? latest?.level ?? 1)
  const levelList = traceSessions.filter((s) => s.level === replayLevel).sort((a, b) => Date.parse(a.startedAt) - Date.parse(b.startedAt))
  const selected: SessionSummary | null = levelList.find((s) => s.id === selectedId) ?? levelList[levelList.length - 1] ?? null
  const latestCheckin = [...tl.checkins].sort((a, b) => b.day.localeCompare(a.day) || b.id - a.id)[0]

  const select = (s: SessionSummary) => {
    setSelectedId(s.id)
    document.getElementById('replay')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }

  return (
    <div className="space-y-6">
      <BackLink />

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{p.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground" data-testid="patient-meta">
            {ageFrom(p.birthYear, tl.today)} let · {p.pathway.name} · {p.side === 'left' ? 'leva' : 'desna'} roka · dan {p.daysSinceDischarge} po odpustu
            (odpust {formatDay(p.dischargeDate)}) · {nextVisitText(p.daysToNextVisit)}
            {p.nextVisitDate && ` (${formatDay(p.nextVisitDate)})`}
          </p>
        </div>
        <StatusBadge status={p.status} className="text-sm" />
      </header>

      {p.openAlert ? (
        <AlertCard alert={p.openAlert} meta={meta.data} latestCheckin={latestCheckin} onChanged={reload} />
      ) : (
        <div className="flex items-center gap-3 rounded-lg border bg-card px-4 py-3 text-sm">
          <StatusBadge status={p.status} />
          <span className={p.status === 'stable' ? 'text-muted-foreground' : ''}>{p.reason}</span>
        </div>
      )}

      <ModelNote meta={meta.data} />

      <Section title="Rezultati iger glede na lastno izhodišče">
        <Tabs value={String(view)} onValueChange={(v) => setView(v === 'all' ? 'all' : (Number(v) as View))}>
          <TabsList>
            <TabsTrigger value="all">Skupaj</TabsTrigger>
            {LEVELS.map((l) => (
              <TabsTrigger key={l} value={String(l)}>
                {LEVEL_NAMES[l]}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="mt-3 grid grid-cols-[minmax(0,1fr)_18rem] gap-6">
          <div>
            <GameChart timeline={tl} view={view} domain={domain} selectedId={selected?.id ?? null} onSelectSession={select} />
            <ChartLegend isAll={view === 'all'} />
          </div>
          <BasisPanel tl={tl} view={view} />
        </div>

        <h3 className="mt-6 mb-1 text-sm font-semibold">Simptomi iz dnevnih vnosov</h3>
        <div className="grid grid-cols-[minmax(0,1fr)_18rem] gap-6">
          <SymptomPanel timeline={tl} questions={p.pathway.questions} domain={domain} />
          <p className="pt-3 text-xs text-muted-foreground">
            Vsako vprašanje ima svojo os; lestvici z nasprotno smerjo nista nikoli na isti osi. Čas je poravnan z grafom zgoraj.
            Rdeča črtkana črta označuje dan z opozorilnim znakom.
          </p>
        </div>
      </Section>

      <div id="replay">
        <Section title="Predvajanje seje" subtitle="Kako se zajame podatek: dejanska sled čez želeno črto, ob njej seja iz izhodišča.">
          <SessionReplay sessions={traceSessions} level={replayLevel} selected={selected} onSelect={(s) => setSelectedId(s.id)} />
        </Section>
      </div>

      <Section title="Dnevni vnosi">
        <CheckinHistory checkins={tl.checkins} pathway={p.pathway} />
      </Section>

      <Section title="Dnevnik ukrepov">
        <ActionLog alerts={tl.alerts} messages={tl.messages} meta={meta.data} />
      </Section>
    </div>
  )
}

function BackLink() {
  return (
    <Link to={paths.clinician} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
      <ArrowLeft className="size-4" aria-hidden /> Pregled pacientov
    </Link>
  )
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border bg-card p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      {subtitle && <p className="mb-3 text-sm text-muted-foreground">{subtitle}</p>}
      <div className={subtitle ? '' : 'mt-3'}>{children}</div>
    </section>
  )
}

function ChartLegend({ isAll }: { isAll: boolean }) {
  return (
    <p className="mt-1 text-xs text-muted-foreground" style={{ paddingLeft: 56 }}>
      {isAll
        ? 'Črta: skupni trend (povprečen odmik stopenj od lastnega izhodišča). Siv pas: izhodišče ±5 točk. Črtkano: prag opozorila.'
        : 'Bledi krogi: posamezne seje (klik odpre predvajanje). Črta: glajen rezultat. Moder pas: izhodišče ±5 točk. Navpične črte: opozorila in pregledi.'}
    </p>
  )
}

/** "Never a bare score": change vs baseline, number of sessions, and the features that moved most. */
function BasisPanel({ tl, view }: { tl: Timeline; view: View }) {
  const metric = view === 'all' ? 'trace:all' : `trace:${view}`
  const sum = trendSummary(tl.trends, metric)
  const traceSessions = tl.sessions.filter((s) => s.gameType === 'trace' && s.completed)
  const scoped = view === 'all' ? traceSessions : traceSessions.filter((s) => s.level === view)
  const n = view === 'all' ? traceSessions.length : sum.nSessions || scoped.length
  const fc = featureComparison(traceSessions, view === 'all' ? null : view)
  const noBaseline = sum.delta == null
  const latestScore = view === 'all' ? null : [...scoped].sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0]?.score

  return (
    <aside className="space-y-4 text-sm" data-testid="basis-panel">
      <div>
        <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Sprememba glede na izhodišče</h3>
        {noBaseline ? (
          <p className="mt-1 font-medium">Premalo sej za izhodišče</p>
        ) : (
          <p className="mt-1 text-lg leading-tight font-semibold">{deltaWords(sum.delta)}</p>
        )}
        <p className="mt-1 text-muted-foreground">
          Temelji na {n} {plural(n, 'seji', 'sejah', 'sejah', 'sejah')}
          {view !== 'all' && sum.baseline != null && <>; izhodišče: {regionWord(sum.baseline)}</>}
          {latestScore != null && <>; zadnja seja: {regionWord(latestScore)}</>}.
        </p>
        {noBaseline && (
          <p className="mt-1 text-xs text-muted-foreground">
            Prva seja je vaja; izhodišče je mediana sej 2–4, torej so potrebne vsaj {MIN_SESSIONS_FOR_BASELINE} seje (zdaj: {n}).
          </p>
        )}
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Kaj se je najbolj premaknilo</h3>
        {fc.rows.length === 0 ? (
          <p className="mt-1 text-muted-foreground">Za primerjavo značilk je premalo sej (potrebnih je vsaj 5 na stopnjo).</p>
        ) : (
          <>
            <table className="mt-1 w-full text-xs" data-testid="feature-table">
              <thead>
                <tr className="text-left text-muted-foreground">
                  <th className="pb-1 font-medium">Značilka</th>
                  <th className="pb-1 pl-2 text-right font-medium">Izhodišče</th>
                  <th className="pb-1 pl-2 text-right font-medium">Zadnje</th>
                  <th className="pb-1 pl-2 text-right font-medium">Sprememba</th>
                </tr>
              </thead>
              <tbody>
                {fc.rows.map((r) => (
                  <tr key={`${r.level}-${r.key}`} className="border-t align-top">
                    <td className="py-1 pr-1">
                      {r.label}
                      {view === 'all' && <span className="block text-muted-foreground">{LEVEL_NAMES[r.level]}</span>}
                    </td>
                    <td className="py-1 pl-2 text-right tabular-nums">{formatFeature(r.baseline)}</td>
                    <td className="py-1 pl-2 text-right tabular-nums">{formatFeature(r.recent)}</td>
                    <td className="py-1 pl-2 text-right font-medium tabular-nums">
                      {r.changePct == null ? '–' : `${r.changePct > 0 ? '+' : '−'}${Math.abs(Math.round(r.changePct))} %`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-1 text-xs text-muted-foreground">Povprečje sej 2–4 proti zadnjim trem sejam.</p>
          </>
        )}
      </div>
    </aside>
  )
}

function PageSkeleton() {
  return (
    <div className="space-y-4" aria-busy>
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-8 w-72" />
      <Skeleton className="h-40 w-full" />
      <Skeleton className="h-80 w-full" />
    </div>
  )
}
