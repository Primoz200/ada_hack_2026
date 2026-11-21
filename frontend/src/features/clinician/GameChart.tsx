// Game chart for one measurement (tracing or camera exercises): combined trend (points vs own baseline)
// or one level (sessions as faded dots, EWMA line, baseline band). Poor-quality camera sessions are hollow grey dots.
// Shares its x axis (time, same domain, same margins) with the rating charts below.
import { CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceLine, Scatter, Tooltip, XAxis, YAxis } from 'recharts'
import type { SessionSummary, Timeline } from '@/client/api'
import { useChartWidth } from './useChartWidth'
import {
  ALERT_THRESHOLD,
  BAND,
  chartMarkers,
  combinedRows,
  dayTicks,
  deltaWords,
  formatDay,
  gameMetric,
  gameSessions,
  latestBaseline,
  levelName,
  levelRows,
  type ChartRow,
  type Game,
  type TimeDomain,
} from './model'
import { AXIS_LABEL_STYLE, AXIS_TICK, CHART_MARGIN, Y_AXIS_WIDTH, markerStyle, shortDay } from './chartLayout'

export type View = 'all' | 1 | 2 | 3

// a card-coloured halo behind chart labels, so they stay readable where they cross a line or dots
const HALO = { stroke: 'var(--card)', strokeWidth: 4, paintOrder: 'stroke' as const, strokeLinejoin: 'round' as const }

// "območje rezultata": descriptive regions on the 0-100 axis (never "razred okvare")
const REGIONS = [
  { y1: 85, y2: 100, label: 'običajno območje' },
  { y1: 65, y2: 85, label: 'rahlo odstopanje' },
  { y1: 40, y2: 65, label: 'zmerno odstopanje' },
  { y1: 0, y2: 40, label: 'izrazito odstopanje' },
]

export function regionWord(score: number | null | undefined): string {
  if (score == null) return 'ni ocene'
  return REGIONS.find((r) => score >= r.y1)?.label ?? REGIONS[3].label
}

/** A session that does not count (poor capture quality): hollow, grey, still clickable. */
export function PoorDot({ cx, cy, selected, onClick }: { cx: number; cy: number; selected?: boolean; onClick?: () => void }) {
  return (
    <circle
      cx={cx}
      cy={cy}
      r={selected ? 6.5 : 4.5}
      fill="var(--card)"
      stroke="var(--status-grey)"
      strokeWidth={selected ? 2.25 : 1.5}
      strokeDasharray={selected ? undefined : '2 1.5'}
      style={onClick ? { cursor: 'pointer' } : undefined}
      onClick={onClick}
    />
  )
}

interface Props {
  timeline: Timeline
  game?: Game
  view: View
  domain: TimeDomain
  selectedId: number | null
  onSelectSession: (s: SessionSummary) => void
  height?: number
}

export function GameChart({ timeline, game = 'trace', view, domain, selectedId, onSelectSession, height = 320 }: Props) {
  const [ref, width] = useChartWidth()
  const markers = chartMarkers(timeline, domain)
  const ticks = dayTicks(domain)
  const isAll = view === 'all'
  const sessions = gameSessions(timeline.sessions, game)
  const rawRows: ChartRow[] = isAll ? combinedRows(timeline.trends, game, sessions) : levelRows(view, sessions, timeline.trends, game)
  const baseline = isAll ? 0 : latestBaseline(timeline.trends, gameMetric(game, view))
  const hasData = rawRows.some((r) => (isAll ? r.delta != null : r.ewma != null || r.score != null))

  const vals = rawRows.map((r) => r.delta).filter((v): v is number => v != null)
  // fixed floor and ceiling, widened only when the data goes beyond them
  const yDomain: [number, number] = isAll
    ? [Math.min(-25, Math.floor(Math.min(...vals, 0) / 5) * 5 - 5), Math.max(15, Math.ceil(Math.max(...vals, 0) / 5) * 5 + 5)]
    : [0, 100]
  // on the combined chart a poor-quality session has no place on the points axis: a lane along the bottom
  const rows = isAll ? rawRows.map((r) => (r.poor != null ? { ...r, poor: yDomain[0] + 2 } : r)) : rawRows
  const hasPoor = rows.some((r) => r.poor != null)
  const byId = new Map(sessions.map((s) => [s.id, s]))
  const gameWord = game === 'camera' ? 'vaj s kamero' : 'sledenja'

  return (
    <div ref={ref} className="relative w-full" style={{ height }} data-testid="game-chart">
      {width > 0 && (
        <ComposedChart width={width} height={height} data={rows} margin={{ ...CHART_MARGIN, top: 26 }}>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={[domain.start, domain.end]}
            ticks={ticks}
            tickFormatter={shortDay}
            tick={AXIS_TICK}
            stroke="var(--border)"
            tickLine={false}
            allowDataOverflow
          />
          <YAxis
            width={Y_AXIS_WIDTH}
            domain={yDomain}
            ticks={isAll ? undefined : [0, 40, 65, 85, 100]}
            allowDataOverflow
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => (isAll && v > 0 ? `+${v}` : v < 0 ? `−${-v}` : String(v))}
            label={{
              value: isAll ? 'točke glede na izhodišče' : 'rezultat seje (0–100)',
              angle: -90,
              position: 'insideLeft',
              offset: 4,
              style: AXIS_LABEL_STYLE,
            }}
          />

          {!isAll &&
            REGIONS.map((r) => (
              <ReferenceLine
                key={r.label}
                y={r.y1}
                stroke="none"
                ifOverflow="hidden"
                // with poor-quality sessions, the lowest label moves above the bottom lane where they are drawn
                label={{ value: r.label, position: 'insideBottomRight', fontSize: 13, fill: 'var(--muted-foreground)', dy: r.y1 === 0 && hasPoor ? -18 : -2, ...HALO }}
              />
            ))}

          {baseline != null && (
            <ReferenceArea
              y1={baseline - BAND}
              y2={baseline + BAND}
              fill="var(--primary)"
              fillOpacity={0.09}
              stroke="none"
              ifOverflow="hidden"
              label={{ value: 'pas izhodišča', position: 'insideTopLeft', fontSize: 13, fill: 'var(--primary)', dx: 4, ...HALO }}
            />
          )}
          {isAll && (
            <>
              <ReferenceLine y={0} stroke="var(--input)" />
              <ReferenceLine
                y={ALERT_THRESHOLD}
                stroke="var(--status-amber)"
                strokeDasharray="6 4"
                label={{ value: 'prag opozorila: 10 točk pod izhodiščem', position: 'insideBottomLeft', fontSize: 13, fill: 'var(--status-amber)', dx: 4, dy: 18, ...HALO }}
              />
            </>
          )}

          {markers.map((m, i) => {
            const st = markerStyle(m)
            return (
              <ReferenceLine
                key={`${m.kind}-${i}`}
                x={m.t}
                stroke={st.stroke}
                strokeDasharray={st.dash}
                strokeWidth={1.25}
                strokeOpacity={m.kind === 'alert' ? 0.75 : 1}
                label={{ value: m.label, position: 'top', fontSize: 13, fill: st.stroke, ...HALO }}
              />
            )
          })}

          <Tooltip
            cursor={{ stroke: 'var(--input)', strokeOpacity: 0.6 }}
            content={({ active, payload }) => {
              const r = payload?.[0]?.payload as ChartRow | undefined
              if (!active || !r) return null
              const s = r.sessionId != null ? byId.get(r.sessionId) : undefined
              return (
                <div className="rounded-lg border bg-popover px-3 py-2 text-[0.875rem] shadow-panel">
                  <div className="font-semibold">{formatDay(r.t)}</div>
                  {isAll && r.delta != null && <div>Skupni trend {gameWord}: {deltaWords(r.delta)}</div>}
                  {!isAll && r.ewma != null && <div>Glajen rezultat: {regionWord(r.ewma)}</div>}
                  {s && r.poor != null && (
                    <div>
                      {levelName(game, s.level)}: slaba kakovost zajema, seja ne šteje v trend
                    </div>
                  )}
                  {s && r.poor == null && s.score != null && (
                    <div>
                      {isAll ? '' : 'Seja: '}
                      {regionWord(s.score)} ({Math.round(s.score)} od 100)
                    </div>
                  )}
                </div>
              )
            }}
          />

          {isAll ? (
            <Line
              type="monotone"
              dataKey="delta"
              name="Skupni trend"
              stroke="var(--chart-1)"
              strokeWidth={2.5}
              dot={{ r: 2.5, fill: 'var(--chart-1)', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: 'var(--chart-1)', stroke: 'var(--card)', strokeWidth: 2 }}
              connectNulls
              isAnimationActive={false}
            />
          ) : (
            <>
              <Scatter
                dataKey="score"
                name="Posamezne seje"
                isAnimationActive={false}
                shape={(p: { cx?: number; cy?: number; payload?: ChartRow }) => {
                  if (p.cx == null || p.cy == null || p.payload?.score == null) return <g />
                  const sel = p.payload.sessionId === selectedId
                  const s = p.payload.sessionId != null ? byId.get(p.payload.sessionId) : undefined
                  return (
                    <circle
                      cx={p.cx}
                      cy={p.cy}
                      r={sel ? 6.5 : 4.5}
                      fill="var(--chart-1)"
                      fillOpacity={sel ? 1 : 0.25}
                      stroke={sel ? 'var(--card)' : 'none'}
                      strokeWidth={2}
                      style={{ cursor: 'pointer' }}
                      onClick={() => s && onSelectSession(s)}
                    />
                  )
                }}
              />
              <Line
                type="monotone"
                dataKey="ewma"
                name="Glajen rezultat"
                stroke="var(--chart-1)"
                strokeWidth={2.5}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
            </>
          )}

          {hasPoor && (
            <Scatter
              dataKey="poor"
              name="Slaba kakovost zajema"
              isAnimationActive={false}
              shape={(p: { cx?: number; cy?: number; payload?: ChartRow }) => {
                if (p.cx == null || p.cy == null || p.payload?.poor == null) return <g />
                const sel = p.payload.sessionId === selectedId
                const s = p.payload.sessionId != null ? byId.get(p.payload.sessionId) : undefined
                return <PoorDot cx={p.cx} cy={p.cy} selected={sel} onClick={() => s && onSelectSession(s)} />
              }}
            />
          )}
        </ComposedChart>
      )}
      {!hasData && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center pl-16 text-[0.9375rem] text-muted-foreground">
          <span className="rounded-lg bg-card px-3 py-1.5">
            {isAll
              ? 'Skupnega trenda še ni: najprej se mora oblikovati izhodišče.'
              : `Za ${game === 'camera' ? 'vajo' : 'stopnjo'} »${levelName(game, view)}« še ni sej.`}
          </span>
        </div>
      )}
    </div>
  )
}
