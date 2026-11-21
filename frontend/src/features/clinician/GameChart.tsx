// Game chart: combined trend (points vs own baseline) or one level (sessions as faded dots, EWMA line, baseline band).
// Shares its x axis (time, same domain, same margins) with the symptom panel below.
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
import { CHART_MARGIN, Y_AXIS_WIDTH, markerStyle, shortDay } from './chartLayout'

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

export function GameChart({ timeline, view, domain, selectedId, onSelectSession, height = 300 }: Props) {
  const [ref, width] = useChartWidth()
  const markers = chartMarkers(timeline, domain)
  const ticks = dayTicks(domain)
  const isAll = view === 'all'
  const rows: ChartRow[] = isAll ? combinedRows(timeline.trends) : levelRows(view, timeline.sessions, timeline.trends)
  const baseline = isAll ? 0 : latestBaseline(timeline.trends, `trace:${view}`)
  const hasData = rows.some((r) => (isAll ? r.delta != null : r.ewma != null || r.score != null))

  const vals = rows.map((r) => r.delta).filter((v): v is number => v != null)
  const yDomain: [number, number] = isAll
    ? [Math.floor(Math.min(-20, ...vals) / 5) * 5 - 5, Math.ceil(Math.max(12, ...vals) / 5) * 5 + 5]
    : [0, 100]
  const byId = new Map(timeline.sessions.map((s) => [s.id, s]))

  return (
    <div ref={ref} className="relative w-full" style={{ height }} data-testid="game-chart">
      {width > 0 && (
        <ComposedChart width={width} height={height} data={rows} margin={{ ...CHART_MARGIN, top: 22 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={[domain.start, domain.end]}
            ticks={ticks}
            tickFormatter={shortDay}
            tick={{ fontSize: 11 }}
            allowDataOverflow
          />
          <YAxis
            width={Y_AXIS_WIDTH}
            domain={yDomain}
            allowDataOverflow
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => (isAll && v > 0 ? `+${v}` : String(v))}
            label={{
              value: isAll ? 'točke glede na izhodišče' : 'rezultat sej (0–100)',
              angle: -90,
              position: 'insideLeft',
              offset: 8,
              style: { fontSize: 11, textAnchor: 'middle', fill: 'var(--muted-foreground)' },
            }}
          />

          {!isAll &&
            REGIONS.map((r, i) => (
              <ReferenceArea
                key={r.label}
                y1={r.y1}
                y2={r.y2}
                fill="var(--muted)"
                fillOpacity={i % 2 === 0 ? 0.55 : 0.2}
                stroke="none"
                ifOverflow="hidden"
                label={{ value: r.label, position: 'insideBottomRight', fontSize: 10, fill: 'var(--muted-foreground)' }}
              />
            ))}

          {baseline != null && (
            <ReferenceArea
              y1={baseline - BAND}
              y2={baseline + BAND}
              fill="var(--primary)"
              fillOpacity={0.13}
              stroke="var(--primary)"
              strokeOpacity={0.25}
              strokeDasharray="3 3"
              ifOverflow="hidden"
              label={{ value: 'pas izhodišča', position: 'insideTopLeft', fontSize: 10, fill: 'var(--foreground)' }}
            />
          )}
          {isAll && (
            <>
              <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
              <ReferenceLine
                y={ALERT_THRESHOLD}
                stroke="#b45309"
                strokeDasharray="6 4"
                label={{ value: 'prag opozorila (−10)', position: 'insideBottomRight', fontSize: 10, fill: '#b45309' }}
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
                strokeWidth={m.kind === 'alert' ? 1.5 : 1}
                label={{ value: m.label, position: 'top', fontSize: 10, fill: st.stroke }}
              />
            )
          })}

          <Tooltip
            cursor={{ stroke: 'var(--muted-foreground)', strokeOpacity: 0.3 }}
            content={({ active, payload }) => {
              const r = payload?.[0]?.payload as ChartRow | undefined
              if (!active || !r) return null
              const s = r.sessionId != null ? byId.get(r.sessionId) : undefined
              return (
                <div className="rounded-md border bg-popover px-2.5 py-1.5 text-xs shadow">
                  <div className="font-medium">{formatDay(r.t)}</div>
                  {isAll && r.delta != null && <div>Skupni trend: {deltaWords(r.delta)}</div>}
                  {!isAll && r.ewma != null && <div>Glajen rezultat: {regionWord(r.ewma)}</div>}
                  {s && (
                    <div>
                      Seja: {regionWord(s.score)} ({Math.round(s.score ?? 0)}/100)
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
              stroke="var(--foreground)"
              strokeWidth={2.5}
              dot={{ r: 3, fill: 'var(--foreground)' }}
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
                      r={sel ? 6 : 4.5}
                      fill="var(--foreground)"
                      fillOpacity={sel ? 0.9 : 0.28}
                      stroke={sel ? 'var(--foreground)' : 'none'}
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
                name="Glajen rezultat (EWMA)"
                stroke="var(--foreground)"
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
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
          {isAll ? 'Še ni skupnega trenda.' : `Za stopnjo »${LEVEL_NAMES[view]}« še ni sej.`}
        </div>
      )}
    </div>
  )
}
