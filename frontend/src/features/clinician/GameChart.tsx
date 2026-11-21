// Game chart: combined trend (points vs own baseline) or one level (sessions as faded dots, EWMA line, baseline band).
// Shares its x axis (time, same domain, same margins) with the rating charts below.
import { CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceLine, Scatter, Tooltip, XAxis, YAxis } from 'recharts'
import type { SessionSummary, Timeline } from '@/client/api'
import { useChartWidth } from './useChartWidth'
import {
  ALERT_THRESHOLD,
  BAND,
  LEVEL_NAMES,
  chartMarkers,
  combinedRows,
  dayTicks,
  deltaWords,
  formatDay,
  latestBaseline,
  levelRows,
  type ChartRow,
  type TimeDomain,
} from './model'
import { AXIS_LABEL_STYLE, AXIS_TICK, CHART_MARGIN, Y_AXIS_WIDTH, markerStyle, shortDay } from './chartLayout'

export type View = 'all' | 1 | 2 | 3

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

interface Props {
  timeline: Timeline
  view: View
  domain: TimeDomain
  selectedId: number | null
  onSelectSession: (s: SessionSummary) => void
  height?: number
}

export function GameChart({ timeline, view, domain, selectedId, onSelectSession, height = 320 }: Props) {
  const [ref, width] = useChartWidth()
  const markers = chartMarkers(timeline, domain)
  const ticks = dayTicks(domain)
  const isAll = view === 'all'
  const rows: ChartRow[] = isAll ? combinedRows(timeline.trends) : levelRows(view, timeline.sessions, timeline.trends)
  const baseline = isAll ? 0 : latestBaseline(timeline.trends, `trace:${view}`)
  const hasData = rows.some((r) => (isAll ? r.delta != null : r.ewma != null || r.score != null))

  const vals = rows.map((r) => r.delta).filter((v): v is number => v != null)
  // fixed floor and ceiling, widened only when the data goes beyond them
  const yDomain: [number, number] = isAll
    ? [Math.min(-25, Math.floor(Math.min(...vals, 0) / 5) * 5 - 5), Math.max(15, Math.ceil(Math.max(...vals, 0) / 5) * 5 + 5)]
    : [0, 100]
  const byId = new Map(timeline.sessions.map((s) => [s.id, s]))

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
                label={{ value: r.label, position: 'insideBottomRight', fontSize: 13, fill: 'var(--muted-foreground)', dy: -2 }}
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
              label={{ value: 'pas izhodišča', position: 'insideTopLeft', fontSize: 13, fill: 'var(--primary)', dx: 4 }}
            />
          )}
          {isAll && (
            <>
              <ReferenceLine y={0} stroke="var(--input)" />
              <ReferenceLine
                y={ALERT_THRESHOLD}
                stroke="var(--status-amber)"
                strokeDasharray="6 4"
                label={{ value: 'prag opozorila: 10 točk pod izhodiščem', position: 'insideBottomLeft', fontSize: 13, fill: 'var(--status-amber)', dx: 4, dy: 18 }}
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
                label={{ value: m.label, position: 'top', fontSize: 13, fill: st.stroke }}
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
                  {isAll && r.delta != null && <div>Skupni trend: {deltaWords(r.delta)}</div>}
                  {!isAll && r.ewma != null && <div>Glajen rezultat: {regionWord(r.ewma)}</div>}
                  {s && (
                    <div>
                      Seja: {regionWord(s.score)} ({Math.round(s.score ?? 0)} od 100)
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
        </ComposedChart>
      )}
      {!hasData && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center pl-16 text-[0.9375rem] text-muted-foreground">
          <span className="rounded-lg bg-card px-3 py-1.5">{isAll ? 'Skupnega trenda še ni: najprej se mora oblikovati izhodišče.' : `Za stopnjo »${LEVEL_NAMES[view]}« še ni sej.`}</span>
        </div>
      )}
    </div>
  )
}
