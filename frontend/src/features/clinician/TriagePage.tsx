// Patient overview sorted by urgency (the server sorts). Plan section 9, Zdravnik 1.
import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { FlaskConical } from 'lucide-react'
import { api, unwrap, type PatientListItem } from '@/client/api'
import { paths } from '@/app/paths'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAsync } from '@/lib/useAsync'
import { counterLine, defaultTab, filterPatients, nextVisitText, type TriageTab } from './model'
import { Sparkline } from './Sparkline'
import { DivergenceBadge, PageState, StatusBadge } from './ui'

export function TriagePage() {
  const { data, error, reload } = useAsync(() => unwrap(api.GET('/api/patients')), [])
  const [tab, setTab] = useState<TriageTab | null>(null)

  if (error && !data) return <PageState>Seznama ni mogoče naložiti: {error.message}</PageState>
  if (!data) return <ListSkeleton />

  const active = tab ?? defaultTab(data.patients)
  const shown = filterPatients(data.patients, active)
  const count = (t: TriageTab) => filterPatients(data.patients, t).length

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pregled pacientov</h1>
        <p data-testid="counter-line" className="mt-1 text-sm font-medium text-muted-foreground">
          {counterLine(data.counters)}
        </p>
      </div>

      <Tabs value={active} onValueChange={(v) => setTab(v as TriageTab)}>
        <TabsList>
          <TabsTrigger value="attention">Zahteva pozornost ({count('attention')})</TabsTrigger>
          <TabsTrigger value="all">Vsi ({count('all')})</TabsTrigger>
          <TabsTrigger value="no_data">Brez podatkov ({count('no_data')})</TabsTrigger>
        </TabsList>
      </Tabs>

      {shown.length === 0 ? (
        <PageState>
          {active === 'attention' ? 'Nihče trenutno ne zahteva pozornosti.' : active === 'no_data' ? 'Vsi pacienti pošiljajo podatke.' : 'Ni pacientov.'}
        </PageState>
      ) : (
        <ul className="divide-y rounded-lg border bg-card">
          {shown.map((p) => (
            <PatientRow key={p.id} p={p} />
          ))}
        </ul>
      )}

      <DemoControls patients={data.patients} onDone={reload} />
    </div>
  )
}

function PatientRow({ p }: { p: PatientListItem }) {
  const urgent = p.status === 'red' || p.status === 'yellow'
  return (
    <li>
      <Link
        to={paths.clinicianPatient(p.id)}
        data-testid={`patient-row-${p.id}`}
        className="grid grid-cols-[8.5rem_minmax(0,1fr)_7rem_11rem] items-center gap-4 px-4 py-3 transition-colors hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:outline-none"
      >
        <div>
          <StatusBadge status={p.status} />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-baseline gap-x-2">
            <span className="text-base font-semibold">{p.name}</span>
            <span className="text-sm text-muted-foreground">
              {p.pathwayName} · dan {p.daysSinceDischarge} po odpustu
            </span>
          </div>
          <div className="mt-0.5 flex flex-wrap items-center gap-2">
            <span className={urgent ? 'text-sm font-medium' : 'text-sm text-muted-foreground'}>{p.reason}</span>
            {p.diverging && <DivergenceBadge />}
          </div>
        </div>
        <Sparkline patient={p} />
        <div className="text-right text-xs text-muted-foreground">
          <div className="font-medium text-foreground">{p.checkins7d}/7 vnosov</div>
          <div>{nextVisitText(p.daysToNextVisit)}</div>
        </div>
      </Link>
    </li>
  )
}

function ListSkeleton() {
  return (
    <div className="space-y-3" aria-busy>
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-5 w-80" />
      {[0, 1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  )
}

function DemoControls({ patients, onDone }: { patients: PatientListItem[]; onDone: () => void }) {
  const [patientId, setPatientId] = useState<string>('')
  const [busy, setBusy] = useState(false)
  const chosen = patientId || patients.find((p) => p.isDemo)?.id || patients[0]?.id || ''

  async function run(label: string, call: () => Promise<{ response: Response; error?: unknown }>) {
    setBusy(true)
    try {
      const { response, error } = await call()
      if (response.status === 501) {
        toast.info(`${label}: strežnik te funkcije še nima.`)
      } else if (error !== undefined || !response.ok) {
        toast.error(`${label}: ni uspelo (${response.status}).`)
      } else {
        toast.success(`${label}: končano.`)
        onDone()
      }
    } catch {
      toast.error(`${label}: strežnik ni dosegljiv.`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-label="Demo" className="mt-8 flex flex-wrap items-center gap-3 rounded-lg border border-dashed bg-muted/30 px-4 py-3 text-sm">
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        <FlaskConical className="size-3.5" aria-hidden /> Demo
      </span>
      <Button variant="outline" size="sm" disabled={busy} onClick={() => run('Ponastavitev demo podatkov', () => api.POST('/api/admin/reset'))}>
        Ponastavi demo podatke
      </Button>
      <span className="mx-1 h-5 w-px bg-border" aria-hidden />
      <Select value={chosen} onValueChange={setPatientId}>
        <SelectTrigger size="sm" aria-label="Pacient za simulacijo" className="min-w-48">
          <SelectValue placeholder="Izberi pacienta" />
        </SelectTrigger>
        <SelectContent>
          {patients.map((p) => (
            <SelectItem key={p.id} value={p.id}>
              {p.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        variant="outline"
        size="sm"
        disabled={busy || !chosen}
        onClick={() => run('Simulacija 7 dni', () => api.POST('/api/admin/simulate', { body: { patientId: chosen, days: 7 } }))}
      >
        Simuliraj naslednjih 7 dni
      </Button>
    </section>
  )
}
