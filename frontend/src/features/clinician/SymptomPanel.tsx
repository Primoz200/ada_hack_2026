// Symptom panel: one small chart per check-in question, each on its own axis, on the game chart's time axis.
import { CartesianGrid, ComposedChart, Line, ReferenceLine, Scatter, XAxis, YAxis } from 'recharts'
import type { Question, Timeline } from '@/client/api'
import { CHART_MARGIN, Y_AXIS_WIDTH, markerStyle, shortDay } from './chartLayout'
import {
  CONCERN_LABEL,
  chartMarkers,
  concernPoints,
  dayTicks,
  formatDay,
  questionLabel,
  symptomSeries,
  warningDays,
  type TimeDomain,
} from './model'
import { useChartWidth } from './useChartWidth'

interface Props {
  timeline: Timeline
  questions: Question[]
  domain: TimeDomain
}

export function SymptomPanel({ timeline, questions, domain }: Props) {
  const [ref, width] = useChartWidth()
  const series = symptomSeries(questions, timeline.checkins)
  const warnings = warningDays(timeline.checkins)
  const concerns = concernPoints(timeline.checkins)
  const markers = chartMarkers(timeline, domain).filter((m) => m.kind !== 'discharge')
  const ticks = dayTicks(domain)

  if (timeline.checkins.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">Pacient še nima dnevnih vnosov.</p>
  }

  const xAxis = (last: boolean) => (
    <XAxis
      dataKey="t"
      type="number"
      scale="time"
      domain={[domain.start, domain.end]}
      ticks={ticks}
      tickFormatter={shortDay}
      tick={{ fontSize: 11 }}
      hide={!last}
      allowDataOverflow
    />
  )

  const guides = (
    <>
      {markers.map((m, i) => {
        const st = markerStyle(m)
        return <ReferenceLine key={`m${i}`} x={m.t} stroke={st.stroke} strokeDasharray={st.dash} strokeOpacity={0.55} />
      })}
      {warnings.map((w) => (
        <ReferenceLine key={`w${w.t}`} x={w.t} stroke="#b91c1c" strokeDasharray="2 2" strokeWidth={1.5} />
      ))}
    </>
  )

  return (
    <div ref={ref} className="w-full" data-testid="symptom-panel">
      {width > 0 &&
        series.map(({ question: q, points }, idx) => {
          const last = idx === series.length - 1 && concerns.length === 0
          const worse = q.higherIsWorse ? 'višje je slabše' : 'višje je bolje'
          const scale = [q.minLabel && `${q.min} = ${q.minLabel}`, q.maxLabel && `${q.max} = ${q.maxLabel}`].filter(Boolean).join(' · ')
          return (
            <div key={q.id} className="border-t first:border-t-0">
              <div className="flex items-baseline justify-between pt-2" style={{ paddingLeft: Y_AXIS_WIDTH, paddingRight: 30 }}>
                <span className="text-xs font-semibold">{questionLabel(q)}</span>
                <span className="text-[11px] text-muted-foreground">
                  {scale && `${scale} · `}
                  {worse}
                </span>
              </div>
              <ComposedChart width={width} height={last ? 100 : 78} data={points} margin={CHART_MARGIN}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                {xAxis(last)}
                <YAxis
                  width={Y_AXIS_WIDTH}
                  domain={[q.min, q.max]}
                  ticks={q.kind === 'yes_no' ? [q.min, q.max] : [q.min, q.max]}
                  tickFormatter={(v: number) => (q.kind === 'yes_no' ? (v >= 1 ? 'da' : 'ne') : String(v))}
                  tick={{ fontSize: 11 }}
                  allowDecimals={false}
                  interval={0}
                />
                {guides}
                <Line
                  type={q.kind === 'yes_no' ? 'stepAfter' : 'monotone'}
                  dataKey="value"
                  stroke="var(--foreground)"
                  strokeWidth={1.75}
                  dot={{ r: 2.5, fill: 'var(--foreground)' }}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </div>
          )
        })}

      {concerns.length > 0 && (
        <div className="border-t">
          <div className="flex items-baseline justify-between pt-2" style={{ paddingLeft: Y_AXIS_WIDTH, paddingRight: 30 }}>
            <span className="text-xs font-semibold">Skrb pacienta</span>
            <span className="text-[11px] text-muted-foreground">
              označeni so le dnevi, ko je pacient navedel skrb · rdeča črta = opozorilni znak
            </span>
          </div>
          <ComposedChart width={width} height={100} data={concerns} margin={CHART_MARGIN}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            {xAxis(true)}
            <YAxis
              width={Y_AXIS_WIDTH}
              type="number"
              dataKey="level"
              domain={[0.4, 2.6]}
              ticks={[1, 2]}
              tickFormatter={(v: number) => (v === 1 ? CONCERN_LABEL.little : CONCERN_LABEL.call)}
              tick={{ fontSize: 11 }}
            />
            {guides}
            <Scatter
              dataKey="level"
              isAnimationActive={false}
              shape={(p: { cx?: number; cy?: number; payload?: { concern: string; day: string } }) =>
                p.cx == null || p.cy == null ? (
                  <g />
                ) : (
                  <g>
                    <title>{`${formatDay(p.payload?.day ?? '')}: skrb »${CONCERN_LABEL[p.payload?.concern ?? 'little']}«`}</title>
                    <rect
                      x={p.cx - 5}
                      y={p.cy - 5}
                      width={10}
                      height={10}
                      transform={`rotate(45 ${p.cx} ${p.cy})`}
                      fill={p.payload?.concern === 'call' ? '#b45309' : 'var(--background)'}
                      stroke={p.payload?.concern === 'call' ? '#b45309' : 'var(--foreground)'}
                      strokeWidth={1.75}
                    />
                  </g>
                )
              }
            />
          </ComposedChart>
        </div>
      )}
    </div>
  )
}
