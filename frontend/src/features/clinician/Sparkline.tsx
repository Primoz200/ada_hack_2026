// Trendlines for the triage list. Fixed windows (last 21 days, fixed y range) so the same slope
// looks the same in every row: a declining line looks declining, a flat one stays flat.
import { Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'
import { sparkRows, sparkValueCount, type SparkRow } from './model'

interface Props {
  caption: string
  /** for screen readers: what the line shows */
  description: string
  points: { day: string; value?: number | null }[]
  today: string
  domain: [number, number]
  /** a reference line (0 = own baseline for the tracing games) */
  reference?: number
  /** caption shown in place of the line when there is too little data */
  emptyText?: string
  width?: number
  height?: number
}

export function Sparkline({ caption, description, points, today, domain, reference, emptyText = 'ni podatkov', width = 220, height = 50 }: Props) {
  const rows: SparkRow[] = sparkRows(points, today, domain)
  const n = sparkValueCount(rows)
  const lastIdx = rows.findLastIndex((r) => r.v != null)
  return (
    <figure className="min-w-0" style={{ width }}>
      <figcaption className="mb-1 text-[0.8125rem] leading-none font-medium text-muted-foreground">{caption}</figcaption>
      {n < 2 ? (
        <div style={{ height }} className="flex items-center text-[0.8125rem] text-muted-foreground">
          <span className="mr-2 h-px w-6 bg-border" aria-hidden />
          {emptyText}
        </div>
      ) : (
        <LineChart width={width} height={height} data={rows} margin={{ top: 4, right: 5, bottom: 4, left: 1 }} role="img" aria-label={description}>
          <XAxis dataKey="t" type="number" domain={[rows[0].t, rows[rows.length - 1].t]} hide />
          <YAxis hide domain={domain} allowDataOverflow />
          {/* frame of the fixed range: faint top and bottom hairlines */}
          <ReferenceLine y={domain[1]} stroke="var(--border)" strokeOpacity={0.7} />
          <ReferenceLine y={domain[0]} stroke="var(--border)" strokeOpacity={0.7} />
          {reference != null && <ReferenceLine y={reference} stroke="var(--input)" strokeDasharray="3 3" />}
          {/* the fixed x window still shows a patient who stopped: the line simply ends early */}
          <Line
            type="linear"
            dataKey="v"
            stroke="var(--chart-1)"
            strokeWidth={2}
            connectNulls
            isAnimationActive={false}
            dot={(d: { cx?: number; cy?: number; index?: number }) =>
              d.index === lastIdx && d.cx != null && d.cy != null ? (
                <circle key="last" cx={d.cx} cy={d.cy} r={3} fill="var(--chart-1)" stroke="var(--card)" strokeWidth={1.5} />
              ) : (
                <g key={d.index} />
              )
            }
          />
        </LineChart>
      )}
    </figure>
  )
}
