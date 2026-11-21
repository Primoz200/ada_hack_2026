// The two daily ratings (wellbeing, pain), each on its own axis, on the game chart's time axis.
// Opposite scales (higher = better / higher = worse) never share an axis.
import { CartesianGrid, ComposedChart, Line, ReferenceLine, Tooltip, XAxis, YAxis } from 'recharts'
import type { Question, Timeline } from '@/client/api'
import { AXIS_TICK, CHART_MARGIN, Y_AXIS_WIDTH, markerStyle, shortDay } from './chartLayout'
import { chartMarkers, dayTicks, formatDay, ratingSeries, ratingText, scaleHint, type TimeDomain } from './model'
import { useChartWidth } from './useChartWidth'

interface Props {
  timeline: Timeline
  questions: Question[]
  domain: TimeDomain
}

export function SymptomPanel({ timeline, questions, domain }: Props) {
  const [ref, width] = useChartWidth()
  const series = ratingSeries(questions, timeline.checkins)
  const markers = chartMarkers(timeline, domain).filter((m) => m.kind !== 'discharge')
  const ticks = dayTicks(domain)

  return (
    <div ref={ref} className="w-full" data-testid="symptom-panel">
      {timeline.checkins.length === 0 ? (
        <p className="py-6 text-[0.9375rem] text-muted-foreground" style={{ paddingLeft: Y_AXIS_WIDTH }}>
          Pacient še ni ocenil počutja in bolečine.
        </p>
      ) : (
        width > 0 &&
        series.map(({ question: q, points }, idx) => {
          const last = idx === series.length - 1
          return (
            <div key={q.id} className={idx > 0 ? 'mt-3' : ''}>
              <div className="flex items-baseline justify-between gap-4" style={{ paddingLeft: Y_AXIS_WIDTH, paddingRight: CHART_MARGIN.right }}>
                <span className="text-[0.9375rem] font-semibold">{q.shortLabel}</span>
                <span className="text-[0.8125rem] text-muted-foreground">
                  1–10, {scaleHint(q)}
                </span>
              </div>
              <ComposedChart width={width} height={last ? 118 : 92} data={points} margin={CHART_MARGIN}>
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
                  hide={!last}
                  allowDataOverflow
                />
                <YAxis
                  width={Y_AXIS_WIDTH}
                  domain={[q.min, q.max]}
                  ticks={[q.min, 5, q.max]}
                  tick={AXIS_TICK}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                  interval={0}
                />
                {markers.map((m, i) => {
                  const st = markerStyle(m)
                  return <ReferenceLine key={`m${i}`} x={m.t} stroke={st.stroke} strokeDasharray={st.dash} strokeOpacity={0.7} strokeWidth={m.kind === 'alert' ? 1.5 : 1} />
                })}
                <Tooltip
                  cursor={{ stroke: 'var(--input)', strokeOpacity: 0.6 }}
                  content={({ active, payload }) => {
                    const r = payload?.[0]?.payload as { day: string; value: number } | undefined
                    if (!active || !r) return null
                    return (
                      <div className="rounded-lg border bg-popover px-3 py-2 text-[0.875rem] shadow-panel">
                        <div className="font-semibold">{formatDay(r.day)}</div>
                        <div>
                          {q.shortLabel}: {ratingText(r.value, q.max)}
                        </div>
                      </div>
                    )
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  dot={{ r: 2.5, fill: 'var(--chart-1)', strokeWidth: 0 }}
                  activeDot={{ r: 4.5, fill: 'var(--chart-1)', stroke: 'var(--card)', strokeWidth: 2 }}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </div>
          )
        })
      )}
    </div>
  )
}
