// Moj napredek: one sentence, one recovery chart per game, the two ratings, this week, and whether
// the doctor has looked. Nothing else.
import { ArrowRight, CalendarCheck, Stethoscope } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { paths } from '@/app/paths'
import { api, unwrap, type Progress } from '@/client/api'
import { Panel } from '@/components/app/Panel'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useAsync } from '@/lib/useAsync'
import { daysOf, longDate } from './format'
import { ProgressCharts } from './GameCharts'
import { RatingsChart } from './RatingsChart'
import { BackHome, Column, FeedbackMark, Heading, LoadError, PanelSkeleton } from './ui'

export function ProgressPage() {
  const { patientId = '' } = useParams()
  const { data, error, reload } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/progress', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  const back = <BackHome to={paths.patientHome(patientId)} />

  return (
    <Column>
      <Heading aside={back}>
        Moj <span className="text-brand">napredek</span>
      </Heading>
      {error && !data ? (
        <Panel>
          <LoadError onRetry={reload} />
        </Panel>
      ) : !data ? (
        <Panel>
          <PanelSkeleton lines={6} />
        </Panel>
      ) : data.games.every((g) => g.points.length === 0) ? (
        <EmptyProgress progress={data} />
      ) : (
        <Dashboard progress={data} />
      )}
    </Column>
  )
}

function Reviewed({ at }: { at: string }) {
  return (
    <p className="flex items-center gap-2.5 text-[0.95rem] font-medium text-primary">
      <Stethoscope className="size-5 shrink-0" aria-hidden />
      Zdravnik je pregledal vaše rezultate {longDate(new Date(at))}.
    </p>
  )
}

function Week({ done, goal }: { done: number; goal: number }) {
  const reached = done >= goal
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <CalendarCheck className={cn('size-6 shrink-0', reached ? 'text-brand' : 'text-primary')} aria-hidden />
        <p className="text-lg">
          <span className="font-semibold tabular">{daysOf(done, 7)}</span> ta teden
          <span className="text-muted-foreground">
            {reached ? ' · cilj dosežen' : ` · cilj je ${goal} dni`}
          </span>
        </p>
      </div>
      <ol className="flex gap-1.5" aria-hidden>
        {Array.from({ length: 7 }, (_, i) => (
          <li
            key={i}
            className={cn(
              'h-3 w-8 rounded-full',
              i < done ? (reached ? 'bg-brand' : 'bg-primary') : 'bg-muted ring-1 ring-border ring-inset',
            )}
          />
        ))}
      </ol>
    </div>
  )
}

function Dashboard({ progress: p }: { progress: Progress }) {
  return (
    <div className="space-y-6">
      <Panel>
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div className="max-w-[54ch]">
            <h2 className="text-2xl font-bold">{p.title}</h2>
            <p className="mt-2 text-xl leading-relaxed">{p.text}</p>
          </div>
          <div className="shrink-0">
            <FeedbackMark tone={p.tone} trend={p.trend} />
          </div>
        </div>
        <ProgressCharts games={p.games} overallTrend={p.trend} />
        <div className="mt-8 space-y-5 border-t border-border pt-7">
          <Week done={p.weekDone} goal={p.weekGoal} />
          {p.clinicianReviewedAt ? <Reviewed at={p.clinicianReviewedAt} /> : null}
        </div>
      </Panel>

      {p.ratings.some((r) => r.wellbeing !== null || r.pain !== null) ? (
        <Panel>
          <h2 className="text-2xl font-bold">Počutje in bolečina</h2>
          <p className="mt-1 text-muted-foreground">Kako ste ju ocenili ob samopregledih.</p>
          <div className="mt-6 grid gap-x-10 gap-y-8 md:grid-cols-2">
            <RatingsChart
              ratings={p.ratings}
              field="wellbeing"
              title="Počutje"
              direction="višje je bolje"
              lowWord="zelo slabo"
              highWord="odlično"
            />
            <RatingsChart
              ratings={p.ratings}
              field="pain"
              title="Bolečina"
              direction="nižje je bolje"
              lowWord="brez"
              highWord="zelo močna"
            />
          </div>
        </Panel>
      ) : null}
    </div>
  )
}

function EmptyProgress({ progress: p }: { progress: Progress }) {
  return (
    <Panel>
      <div className="max-w-[56ch]">
        <h2 className="text-2xl font-bold">Tu boste videli, kako napredujete</h2>
        <p className="mt-2 text-xl leading-relaxed">
          Po nekaj samopregledih se bo tu pokazal graf, ki vaše rezultate primerja z vašimi običajnimi.
        </p>
      </div>
      <div className="mt-8 rounded-xl bg-muted p-6" aria-hidden>
        <svg viewBox="0 0 600 120" className="h-28 w-full" preserveAspectRatio="none">
          <line x1="0" y1="60" x2="600" y2="60" stroke="var(--input)" strokeWidth="2" strokeDasharray="8 8" />
        </svg>
        <p className="-mt-4 text-center text-[0.95rem] font-medium text-muted-foreground">kot običajno</p>
      </div>
      <div className="mt-8 space-y-5 border-t border-border pt-7">
        {p.weekDone > 0 ? <Week done={p.weekDone} goal={p.weekGoal} /> : null}
        {p.clinicianReviewedAt ? <Reviewed at={p.clinicianReviewedAt} /> : null}
        <Button asChild variant="cta" size="xl" className="w-full sm:w-auto">
          <Link to={paths.selfcheck(p.patientId)}>
            Začni samopregled
            <ArrowRight aria-hidden />
          </Link>
        </Button>
      </div>
    </Panel>
  )
}
