// Session replay: the actual trace drawn over the target line, next to a baseline session of the same level.
// This is the screenshot that shows how data capture works.
import { api, unwrap, type SessionRaw, type SessionSummary } from '@/client/api'
import { useAsync } from '@/lib/useAsync'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { LEVEL_NAMES, dayMs, durationText, formatDay, pickBaselineSession, pointsAttr, splitStrokes, targetPoints, type Series } from './model'
import { regionWord } from './GameChart'
import { shortDay } from './chartLayout'

interface Props {
  sessions: SessionSummary[] // trace sessions of the displayed level, any order
  level: number
  selected: SessionSummary | null
  onSelect: (s: SessionSummary) => void
}

export function SessionReplay({ sessions, level, selected, onSelect }: Props) {
  const levelSessions = sessions
    .filter((s) => s.level === level)
    .sort((a, b) => Date.parse(a.startedAt) - Date.parse(b.startedAt))
  const baseline = selected ? pickBaselineSession(levelSessions, level, selected.id) : null

  if (levelSessions.length === 0) {
    return <p className="py-6 text-center text-[0.9375rem] text-muted-foreground">Za to stopnjo še ni sej za predvajanje.</p>
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_13rem] gap-6">
      <div className="grid grid-cols-2 gap-6">
        <TraceCard title="Izbrana seja" session={selected} accent />
        <TraceCard
          title="Seja iz izhodišča"
          session={baseline}
          emptyText={selected ? 'Za primerjavo ni seje iz izhodišča (potrebne so vsaj 4 seje).' : undefined}
        />
        <Legend />
      </div>
      <div>
        <div className="mb-2 text-[0.9375rem] font-semibold">Seje: {LEVEL_NAMES[level] ?? `stopnja ${level}`}</div>
        <ul className="max-h-[22rem] space-y-1 overflow-y-auto pr-1" data-testid="session-list">
          {[...levelSessions].reverse().map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => onSelect(s)}
                aria-pressed={selected?.id === s.id}
                className={cn(
                  'tabular flex w-full items-center justify-between rounded-md border px-2.5 py-1.5 text-left text-[0.875rem] transition-colors hover:bg-muted',
                  selected?.id === s.id ? 'border-primary bg-accent font-semibold text-foreground' : 'border-transparent',
                )}
              >
                <span className="whitespace-nowrap">{shortDay(dayMs(s.day))}</span>
                <span className="whitespace-nowrap text-muted-foreground">{regionWord(s.score).replace(' območje', '')}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="col-span-2 flex flex-wrap items-center gap-x-6 gap-y-1 text-[0.875rem] text-muted-foreground">
      <span className="inline-flex items-center gap-2">
        <svg width="28" height="8" aria-hidden>
          <line x1="0" y1="4" x2="28" y2="4" stroke="var(--input)" strokeWidth="3" strokeDasharray="5 4" strokeLinecap="round" />
        </svg>
        želena črta
      </span>
      <span className="inline-flex items-center gap-2">
        <svg width="28" height="8" aria-hidden>
          <line x1="0" y1="4" x2="28" y2="4" stroke="var(--chart-1)" strokeWidth="2" strokeLinecap="round" />
        </svg>
        dejanska sled (vsak dvig prsta začne nov poteg)
      </span>
    </div>
  )
}

function TraceCard({ title, session, emptyText, accent }: { title: string; session: SessionSummary | null; emptyText?: string; accent?: boolean }) {
  const { data, error, loading } = useAsync<SessionRaw | null>(
    () => (session ? unwrap(api.GET('/api/sessions/{session_id}/raw', { params: { path: { session_id: session.id } } })) : Promise.resolve(null)),
    [session?.id],
  )
  return (
    <figure className="min-w-0">
      <figcaption className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="text-[0.9375rem] font-semibold">{title}</span>
        {session && (
          <span className="tabular text-[0.875rem] text-muted-foreground">
            {formatDay(session.day)} · {durationText(session.durationMs)} · {regionWord(session.score)}
          </span>
        )}
      </figcaption>
      <div className={cn('aspect-square w-full overflow-hidden rounded-lg border bg-card', accent && 'border-primary/50')}>
        {!session ? (
          <Empty>{emptyText ?? 'Izberite sejo na grafu ali s seznama.'}</Empty>
        ) : loading ? (
          <Skeleton className="h-full w-full rounded-none" />
        ) : error ? (
          <Empty>Surove sledi ni mogoče naložiti.</Empty>
        ) : data ? (
          <TraceSvg series={data.series} />
        ) : null}
      </div>
    </figure>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div className="flex h-full items-center justify-center p-4 text-center text-[0.875rem] text-muted-foreground">{children}</div>
}

export function TraceSvg({ series }: { series: Series }) {
  const target = targetPoints(series)
  const strokes = splitStrokes(series)
  if (target.length === 0 && strokes.length === 0) return <Empty>Seja nima shranjene sledi.</Empty>
  return (
    <svg viewBox="-0.03 -0.03 1.06 1.06" className="h-full w-full" role="img" aria-label="Dejanska sled čez želeno črto">
      <rect x="0" y="0" width="1" height="1" fill="none" stroke="var(--border)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <polyline
        points={pointsAttr(target)}
        fill="none"
        stroke="var(--input)"
        strokeOpacity={0.8}
        strokeWidth={5}
        strokeDasharray="10 8"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      {strokes.map((s, i) => (
        <polyline
          key={`${s.id}-${i}`}
          points={pointsAttr(s.points)}
          fill="none"
          stroke="var(--chart-1)"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      ))}
      {strokes[0]?.points[0] && <circle cx={strokes[0].points[0].x} cy={strokes[0].points[0].y} r={0.012} fill="var(--chart-1)" />}
    </svg>
  )
}
