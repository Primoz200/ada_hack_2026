// "Zadnje seje" for the camera exercises: what each session showed, in words. No landmark rendering:
// the clinician needs the result, the exercise and whether the capture was good enough to count.
import { CircleAlert } from 'lucide-react'
import type { SessionSummary } from '@/client/api'
import { cn } from '@/lib/utils'
import { shortDay } from './chartLayout'
import { regionWord } from './GameChart'
import { cameraSessionFacts, dayMs, durationText, formatDay, isPoorQuality, levelName } from './model'

const ROW = 'grid grid-cols-[4.25rem_minmax(0,1fr)_minmax(0,1.3fr)_3.75rem_4.5rem] items-center gap-x-4'
const LIMIT = 12

interface Props {
  sessions: SessionSummary[] // camera sessions, any order
  level: number | null // null: all exercises
  selected: SessionSummary | null
  onSelect: (s: SessionSummary) => void
}

export function CameraSessions({ sessions, level, selected, onSelect }: Props) {
  const list = sessions
    .filter((s) => level == null || s.level === level)
    .sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))
    .slice(0, LIMIT)

  if (list.length === 0) {
    return (
      <p className="py-6 text-center text-[0.9375rem] text-muted-foreground">
        {level == null ? 'Pacient še ni opravil vaj s kamero.' : `Za vajo »${levelName('camera', level)}« še ni sej.`}
      </p>
    )
  }

  return (
    <div className="grid gap-x-10 gap-y-6 lg:grid-cols-[minmax(0,1fr)_19rem]">
      <div className="min-w-0">
        <div className={cn(ROW, 'border-b border-border px-3 pb-2 text-[0.8125rem] font-medium text-muted-foreground')} aria-hidden>
          <span>Datum</span>
          <span>Vaja</span>
          <span>Rezultat</span>
          <span className="text-right">Trajanje</span>
          <span>Zajem</span>
        </div>
        <ul data-testid="camera-session-list">
          {list.map((s) => {
            const on = selected?.id === s.id
            const poor = isPoorQuality(s)
            return (
              <li key={s.id} className="border-b border-border last:border-b-0">
                <button
                  type="button"
                  onClick={() => onSelect(s)}
                  aria-pressed={on}
                  aria-label={`${formatDay(s.day)}, ${levelName('camera', s.level)}: ${poor ? 'ni ocene, slab zajem' : regionWord(s.score)}`}
                  className={cn(
                    ROW,
                    'min-h-11 w-full rounded-md px-3 py-1.5 text-left text-[0.9375rem] transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/45',
                    on && 'bg-accent font-semibold hover:bg-accent',
                  )}
                >
                  <span className="tabular whitespace-nowrap">{shortDay(dayMs(s.day))}</span>
                  <span className="truncate">{levelName('camera', s.level)}</span>
                  <span className={cn('truncate', poor && 'text-muted-foreground')}>{poor ? 'ni ocene' : regionWord(s.score)}</span>
                  <span className="tabular text-right whitespace-nowrap text-muted-foreground">{durationText(s.durationMs)}</span>
                  <span className={cn('inline-flex items-center gap-1 whitespace-nowrap', poor ? 'font-semibold text-status-grey' : 'text-muted-foreground')}>
                    {poor && <CircleAlert className="size-3.5 shrink-0" strokeWidth={2} aria-hidden />}
                    {poor ? 'slab' : s.qualityOk ? 'dober' : '–'}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
        {sessions.filter((s) => level == null || s.level === level).length > LIMIT && (
          <p className="mt-2 px-3 text-[0.8125rem] text-muted-foreground">Prikazanih je zadnjih {LIMIT} sej.</p>
        )}
      </div>
      <SessionDetail session={selected} />
    </div>
  )
}

function SessionDetail({ session }: { session: SessionSummary | null }) {
  if (!session) {
    return <p className="self-center text-[0.9375rem] text-muted-foreground">Izberite sejo na grafu ali s seznama.</p>
  }
  const poor = isPoorQuality(session)
  const facts = cameraSessionFacts(session)
  return (
    <aside className="min-w-0" data-testid="camera-session-detail">
      <h3 className="text-[0.9375rem] font-medium text-muted-foreground">Izbrana seja</h3>
      <p className="mt-1 text-xl leading-tight font-bold">
        {levelName('camera', session.level)}
        <span className="tabular ml-2 text-base font-medium text-muted-foreground">{formatDay(session.day)}</span>
      </p>
      <p className="mt-1 text-[0.9375rem]">
        {poor ? (
          <span className="text-muted-foreground">Ni ocene: posnetek ni bil dovolj dober za oceno.</span>
        ) : (
          <>
            Rezultat: <span className="font-semibold">{regionWord(session.score)}</span>
            {session.score != null && <span className="tabular text-muted-foreground"> ({Math.round(session.score)} od 100)</span>}
          </>
        )}
      </p>
      {facts.length > 0 ? (
        <dl className="mt-4 divide-y divide-border border-t border-border text-[0.9375rem]">
          {facts.map((f) => (
            <div key={f.label} className="grid grid-cols-[8.5rem_minmax(0,1fr)] gap-3 py-2">
              <dt className="text-muted-foreground">{f.label}</dt>
              <dd className="font-medium">{f.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-4 text-[0.9375rem] text-muted-foreground">Za to sejo ni shranjenih značilk.</p>
      )}
      {!poor && <p className="mt-2 text-[0.8125rem] text-muted-foreground">Delež zdravega giba: primerjava z zdravim referenčnim posnetkom.</p>}
    </aside>
  )
}
