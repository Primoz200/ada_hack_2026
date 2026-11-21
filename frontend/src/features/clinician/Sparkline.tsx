// Mini trend chart for the triage list: combined trend (points vs own baseline) with a zero reference line.
import { Line, LineChart, ReferenceLine, YAxis } from 'recharts'
import type { PatientListItem } from '@/client/api'
import { sparkRows } from './model'

export function Sparkline({ patient, width = 112, height = 36 }: { patient: PatientListItem; width?: number; height?: number }) {
  const rows = sparkRows(patient)
  const vals = rows.map((r) => r.v).filter((v): v is number => v != null)
  if (vals.length < 2) {
    return (
      <div style={{ width, height }} className="flex items-center justify-center text-[11px] text-muted-foreground">
        ni trenda
      </div>
    )
  }
  const lo = Math.min(-12, ...vals) - 2
  const hi = Math.max(8, ...vals) + 2
  return (
    <LineChart
      width={width}
      height={height}
      data={rows}
      margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
      aria-label="Trend glede na lastno izhodišče"
      role="img"
    >
      <YAxis hide domain={[lo, hi]} />
      <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeDasharray="2 2" strokeOpacity={0.7} />
      <Line type="monotone" dataKey="v" stroke="var(--foreground)" strokeWidth={1.5} dot={false} connectNulls isAnimationActive={false} />
    </LineChart>
  )
}
