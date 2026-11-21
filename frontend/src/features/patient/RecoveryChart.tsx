// The patient's own results against their own usual level. The y axis is worded, there are
// no numeric ticks; the dashed line is "kot običajno". Used on the result step and in Moj napredek.
import {
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ProgressPoint } from '@/client/api'
import { longDate, parseDay, shortDate } from './format'

const LEVEL_WORDS = {
  lower: 'nižje kot običajno',
  usual: 'kot običajno',
  better: 'bolje kot običajno',
} as const

interface TickProps {
  x?: number | string
  y?: number | string
  payload?: { value: number }
}

/** Two-line word tick: "bolje kot" / "običajno". */
function WordTick({ x = 0, y = 0, payload }: TickProps) {
  const v = payload?.value ?? 0
  const text = v < 0 ? LEVEL_WORDS.lower : v > 0 ? LEVEL_WORDS.better : LEVEL_WORDS.usual
  const words = text.split(' ')
  const lines = words.length > 2 ? [words.slice(0, 2).join(' '), words.slice(2).join(' ')] : [text]
  const nx = Number(x) - 10
  return (
    <text x={nx} y={Number(y)} textAnchor="end" fontSize={13} fill="var(--muted-foreground)" fontWeight={v === 0 ? 600 : 500}>
      {lines.map((l, i) => (
        <tspan key={i} x={nx} dy={i === 0 ? (lines.length > 1 ? '-0.25em' : '0.35em') : '1.2em'}>
          {l}
        </tspan>
      ))}
    </text>
  )
}

interface TipProps {
  active?: boolean
  payload?: { payload?: { day: string; label?: keyof typeof LEVEL_WORDS } }[]
}

function Tip({ active, payload }: TipProps) {
  const p = payload?.[0]?.payload
  if (!active || !p || !p.label) return null
  return (
    <div className="rounded-lg bg-card px-3 py-2 text-[0.95rem] shadow-panel ring-1 ring-border">
      <div className="font-semibold">{longDate(parseDay(p.day))}</div>
      <div className="text-muted-foreground">{LEVEL_WORDS[p.label]}</div>
    </div>
  )
}

export function RecoveryChart({
  points,
  personalBestDay,
  height = 280,
  label = 'Graf vaših rezultatov skozi čas',
  days,
}: {
  points: readonly ProgressPoint[]
  personalBestDay?: string | null
  height?: number
  label?: string
  /** a shared x axis (sorted days), so charts of several games line up; days without a point stay empty */
  days?: readonly string[]
}) {
  const own = points.map((p) => ({ day: p.day, value: p.value, label: p.label }))
  const byDay = new Map(own.map((p) => [p.day, p]))
  type Row = { day: string; value: number | null; label?: ProgressPoint['label'] }
  const data: Row[] = days ? days.map((day) => byDay.get(day) ?? { day, value: null }) : own
  const extent = Math.max(6, ...points.map((p) => Math.abs(p.value)))
  const best = personalBestDay ? own.find((p) => p.day === personalBestDay) : undefined
  const last = own[own.length - 1]
  const showDots = data.length <= 21
  return (
    <div role="img" aria-label={label} className="select-none">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: best ? 30 : 14, right: 18, bottom: 4, left: 0 }}>
          <ReferenceLine y={extent} stroke="var(--border)" />
          <ReferenceLine y={-extent} stroke="var(--border)" />
          <XAxis
            dataKey="day"
            tickFormatter={(d: string) => shortDate(parseDay(d))}
            interval="preserveStartEnd"
            minTickGap={28}
            tick={{ fontSize: 13, fill: 'var(--muted-foreground)' }}
            tickLine={false}
            axisLine={false}
            tickMargin={10}
          />
          <YAxis
            width={96}
            domain={[-extent * 1.12, extent * 1.12]}
            ticks={[-extent, 0, extent]}
            tick={(p: TickProps) => <WordTick {...p} />}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine y={0} stroke="var(--input)" strokeDasharray="5 5" strokeWidth={1.5} />
          <Tooltip content={<Tip />} cursor={{ stroke: 'var(--border)', strokeWidth: 1.5 }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--chart-1)"
            strokeWidth={2.5}
            dot={showDots ? { r: 3.5, fill: 'var(--chart-1)', strokeWidth: 0 } : false}
            activeDot={{ r: 6, fill: 'var(--chart-1)', stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
          {last ? (
            <ReferenceDot x={last.day} y={last.value} r={6} fill="var(--chart-1)" stroke="var(--card)" strokeWidth={2.5} />
          ) : null}
          {best ? (
            <ReferenceDot
              x={best.day}
              y={best.value}
              r={9}
              fill="none"
              stroke="var(--brand)"
              strokeWidth={2.5}
              label={{ value: 'Osebni rekord', position: 'top', offset: 10, fontSize: 13, fontWeight: 600, fill: 'var(--brand-ink)' }}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
