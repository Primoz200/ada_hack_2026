// Domov: a greeting and exactly two choices, Samopregled (the hero) and Moj napredek.
import { ArrowRight, CircleCheck, RotateCcw } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { paths } from '@/app/paths'
import { api, unwrap, type PatientHome } from '@/client/api'
import { Panel } from '@/components/app/Panel'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/lib/useAsync'
import { firstName, relativeDay } from './format'
import { StepPreview } from './StepPreview'
import { Column, Heading, LoadError, PanelSkeleton, slateOutline } from './ui'
import { buildWizard, isPartlyDone } from './wizard'

function greeting(now = new Date()): string {
  const h = now.getHours()
  if (h < 10) return 'Dobro jutro'
  if (h >= 18) return 'Dober večer'
  return 'Dober dan'
}

export function HomePage() {
  const { patientId = '' } = useParams()
  const { data, error, reload } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/home', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )

  if (error && !data) {
    return (
      <Column>
        <Heading>{greeting()}</Heading>
        <Panel>
          <LoadError onRetry={reload} />
        </Panel>
      </Column>
    )
  }
  if (!data) {
    return (
      <Column>
        <div className="mb-6 px-2">
          <Skeleton className="h-11 w-80" />
        </div>
        <Panel>
          <PanelSkeleton />
        </Panel>
      </Column>
    )
  }

  return (
    <Column>
      <Heading>
        {greeting()}, <span className="text-brand">{firstName(data.name)}</span>
      </Heading>
      {data.selfcheckDoneToday ? <DoneToday home={data} /> : <SelfcheckChoice home={data} />}
    </Column>
  )
}

function SelfcheckChoice({ home }: { home: PatientHome }) {
  const wizard = buildWizard(home.steps).filter((s) => s.kind !== 'result')
  const doneKeys = new Set(home.steps.filter((s) => s.done).map((s) => s.id))
  const resume = isPartlyDone(home.steps)
  return (
    <div className="space-y-6">
      <Panel>
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <h2 className="text-2xl font-bold">{resume ? 'Nadaljujte današnji samopregled' : 'Današnji samopregled'}</h2>
          {home.lastSelfcheckDay ? (
            <p className="text-[0.95rem] text-muted-foreground">
              Zadnji samopregled: {relativeDay(home.lastSelfcheckDay, home.today)}
            </p>
          ) : null}
        </div>
        <p className="mt-2 max-w-[60ch] text-lg text-muted-foreground">
          {resume
            ? 'Del ste že opravili. Nadaljujete tam, kjer ste ostali.'
            : 'Dve kratki oceni in nekaj nalog z roko. Vzame približno dve minuti.'}
        </p>
        <ol className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4" aria-label="Koraki samopregleda">
          {wizard.map((s) => (
            <StepPreview key={s.key} step={s} done={doneKeys.has(s.key)} />
          ))}
        </ol>
        <div className="mt-8 border-t border-border pt-8">
          <Button asChild variant="cta" size="xl" className="w-full sm:w-auto sm:min-w-72">
            <Link to={paths.selfcheck(home.patientId)}>
              {resume ? 'Nadaljuj samopregled' : 'Začni samopregled'}
              <ArrowRight aria-hidden />
            </Link>
          </Button>
        </div>
      </Panel>

      <Link
        to={paths.progress(home.patientId)}
        className="group flex items-center justify-between gap-6 rounded-panel bg-card px-8 py-7 shadow-panel transition-colors hover:bg-muted md:px-10"
      >
        <span>
          <span className="block text-2xl font-bold">Moj napredek</span>
          <span className="mt-1 block text-lg text-muted-foreground">Kako vam gre iz dneva v dan.</span>
        </span>
        <ArrowRight className="size-7 shrink-0 text-primary transition-transform group-hover:translate-x-1" aria-hidden />
      </Link>
    </div>
  )
}

function DoneToday({ home }: { home: PatientHome }) {
  return (
    <Panel>
      <div className="flex items-start gap-5">
        <CircleCheck className="mt-0.5 size-10 shrink-0 text-brand" strokeWidth={2} aria-hidden />
        <div>
          <h2 className="text-2xl font-bold">Današnji samopregled je opravljen</h2>
          <p className="mt-2 max-w-[56ch] text-lg text-muted-foreground">
            Hvala. Vaše rezultate si lahko ogledate v Mojem napredku. Naslednji samopregled vas čaka jutri.
          </p>
        </div>
      </div>
      <div className="mt-8 flex flex-col gap-3 border-t border-border pt-8 sm:flex-row sm:items-center">
        <Button asChild variant="cta" size="xl" className="sm:min-w-64">
          <Link to={paths.progress(home.patientId)}>
            Moj napredek
            <ArrowRight aria-hidden />
          </Link>
        </Button>
        <Button asChild variant="outline" size="xl" className={slateOutline}>
          <Link to={paths.selfcheck(home.patientId)}>
            <RotateCcw aria-hidden />
            Ponovi samopregled
          </Link>
        </Button>
      </div>
    </Panel>
  )
}
