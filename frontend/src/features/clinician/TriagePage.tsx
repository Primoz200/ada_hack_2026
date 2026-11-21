// Patient overview sorted by urgency (the server sorts). Plan section 9, Zdravnik 1.
// A row is only: status, name, trendlines. Why a patient is flagged lives one click deeper.
import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ArrowRight, CircleSlash, RotateCcw, UsersRound, Inbox } from 'lucide-react'
import { api, unwrap, type PatientListItem } from '@/client/api'
import { paths } from '@/app/paths'
import { Panel, PageTitle } from '@/components/app/Panel'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAsync } from '@/lib/useAsync'
import { GAME_SPARK_DOMAIN, RATING_DOMAIN, defaultTab, filterPatients, plural, type TriageTab } from './model'
import { Sparkline } from './Sparkline'
import { EmptyState, ErrorState, StatusBadge, UnderlineTabs } from './ui'

// status | name | trendlines (one column each; a third, for the computer-vision games, fits later) | arrow
const ROW_GRID = 'grid grid-cols-[10.5rem_minmax(0,1fr)_auto_2rem] items-center gap-x-8'
const TREND_W = 176

const TABS: { id: TriageTab; label: string }[] = [
  { id: 'attention', label: 'Zahteva pozornost' },
  { id: 'all', label: 'Vsi' },
  { id: 'no_data', label: 'Brez podatkov' },
]

export function TriagePage() {
  const { data, error, loading, reload } = useAsync(() => unwrap(api.GET('/api/patients')), [])
  const [tab, setTab] = useState<TriageTab | null>(null)

  if (error && !data) {
    return (
      <>
        <PageTitle title="Pregled pacientov" />
        <Panel>
          <ErrorState title="Seznama pacientov ni mogoče naložiti." message={error.message} onRetry={reload} />
        </Panel>
      </>
    )
  }
  if (!data) return <ListSkeleton />

  const active = tab ?? defaultTab(data.patients)
  const shown = filterPatients(data.patients, active)
  const count = (t: TriageTab) => filterPatients(data.patients, t).length
  const c = data.counters

  return (
    <>
      <PageTitle title="Pregled pacientov" />
      <Panel className="p-0 md:p-0" aria-busy={loading || undefined}>
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-2 border-b border-border px-8 pt-6 md:px-10">
          <p data-testid="counter-line" className="text-lg leading-[2.75rem]">
            <Count n={c.needsAttention} /> za pregled
            <Dot />
            <Count n={c.noData} /> brez podatkov
            <Dot />
            <Count n={c.stable} /> {plural(c.stable, 'stabilen', 'stabilna', 'stabilni', 'stabilnih')}
          </p>
          <UnderlineTabs label="Filter pacientov" value={active} onChange={setTab} items={TABS.map((t) => ({ ...t, count: count(t.id) }))} />
        </div>

        <div>
          {shown.length === 0 ? (
            <TabEmpty tab={active} />
          ) : (
            <ul data-testid="patient-list">
              {shown.map((p) => (
                <PatientRow key={p.id} p={p} today={data.today} />
              ))}
            </ul>
          )}
        </div>
        <div className="h-4" aria-hidden />
      </Panel>

      <DemoControls onDone={reload} />
    </>
  )
}

function Count({ n }: { n: number }) {
  return <span className="tabular font-bold">{n}</span>
}

function Dot() {
  return (
    <span className="mx-2.5 text-input" aria-hidden>
      ·
    </span>
  )
}

function PatientRow({ p, today }: { p: PatientListItem; today: string }) {
  return (
    <li className="border-b border-border last:border-b-0">
      <Link
        to={paths.clinicianPatient(p.id)}
        data-testid={`patient-row-${p.id}`}
        className={`${ROW_GRID} group min-h-20 px-8 py-4 transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none md:px-10`}
      >
        <div>
          <StatusBadge status={p.status} />
        </div>
        <div className="min-w-0 truncate text-lg font-semibold">{p.name}</div>
        <div className="flex items-center gap-8">
          <Sparkline
            caption="Sledenje"
            description={`${p.name}: rezultati sledenja zadnjih 21 dni glede na lastno izhodišče`}
            points={p.gameSparkline}
            today={today}
            domain={GAME_SPARK_DOMAIN}
            reference={0}
            emptyText={p.status === 'insufficient_data' ? 'še ni izhodišča' : 'ni podatkov'}
            width={TREND_W}
          />
          <Sparkline
            caption="Počutje"
            description={`${p.name}: počutje zadnjih 21 dni na lestvici od 1 do 10`}
            points={p.wellbeingSparkline}
            today={today}
            domain={RATING_DOMAIN}
            width={TREND_W}
          />
        </div>
        <ArrowRight className="size-5 justify-self-end text-primary transition-transform group-hover:translate-x-0.5" strokeWidth={2} aria-hidden />
      </Link>
    </li>
  )
}

function TabEmpty({ tab }: { tab: TriageTab }) {
  if (tab === 'attention')
    return <EmptyState icon={Inbox} title="Nihče trenutno ne zahteva pozornosti." hint="Ko rezultati pacienta zdrsnejo pod lastno izhodišče ali se počutje poslabša, se pacient pojavi tukaj." />
  if (tab === 'no_data') return <EmptyState icon={CircleSlash} title="Vsi pacienti redno pošiljajo samopregled." hint="Tukaj se pojavi pacient, ki nekaj dni ne opravi samopregleda." />
  return <EmptyState icon={UsersRound} title="Ni pacientov." hint="Ko bo pacient vključen v spremljanje doma, se pojavi na tem seznamu." />
}

function ListSkeleton() {
  return (
    <>
      <PageTitle title="Pregled pacientov" />
      <Panel className="p-0 md:p-0" aria-busy>
        <div className="flex items-end justify-between border-b border-border px-8 pt-6 pb-3 md:px-10">
          <Skeleton className="h-7 w-96" />
          <Skeleton className="h-8 w-80" />
        </div>
        <div>
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className={`${ROW_GRID} min-h-20 border-b border-border px-8 py-4 last:border-b-0 md:px-10`}>
              <Skeleton className="h-8 w-28" />
              <Skeleton className="h-6 w-48" />
              <div className="flex gap-8">
                <Skeleton className="h-11" style={{ width: TREND_W }} />
                <Skeleton className="h-11" style={{ width: TREND_W }} />
              </div>
              <span />
            </div>
          ))}
        </div>
        <div className="h-4" aria-hidden />
      </Panel>
    </>
  )
}

function DemoControls({ onDone }: { onDone: () => void }) {
  const [busy, setBusy] = useState(false)

  async function reset() {
    setBusy(true)
    try {
      const { response, error } = await api.POST('/api/admin/reset')
      if (error !== undefined || !response.ok) {
        toast.error(`Ponastavitev ni uspela (${response.status}).`)
      } else {
        toast.success('Demo podatki so ponastavljeni na začetno stanje.')
        onDone()
      }
    } catch {
      toast.error('Strežnik ni dosegljiv.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-6 flex flex-wrap items-center justify-end gap-x-4 gap-y-2 px-2 text-[0.9375rem] text-muted-foreground">
      <span>Vsi podatki so sintetični.</span>
      <Button variant="ghost" className="text-primary hover:bg-card hover:text-primary" disabled={busy} onClick={reset}>
        <RotateCcw aria-hidden /> Ponastavi demo podatke
      </Button>
    </div>
  )
}
