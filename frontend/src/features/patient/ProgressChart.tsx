// One line chart of the patient's own results against their own usual level. The y axis is
// labelled in words; there are no numeric ticks (plan section 9, Pacient item 4).
import { Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Progress } from '@/client/api'

const WORDS = { lower: 'nižje kot običajno', usual: 'kot običajno', better: 'bolje kot običajno' } as const

function shortDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getDate()}. ${d.getMonth() + 1}.`
}

function longDate(iso: string): string {
  return new Date(iso).toLocaleDateString('sl-SI', { day: 'numeric', month: 'long' })
}

/** Two-line word tick, e.g. "nižje kot" / "običajno". */
function WordTick(props: { x?: number; y?: number; payload?: { value: number } }) {
  const { x = 0, y = 0, payload } = props
  const v = payload?.value ?? 0
  const text = v < 0 ? WORDS.lower : v > 0 ? WORDS.better : WORDS.usual
  const words = text.split(' ')
  const mid = Math.ceil(words.length / 2)
  const lines = [words.slice(0, mid).join(' '), words.slice(mid).join(' ')].filter(Boolean)
  return (
    <text x={x - 6} y={y} textAnchor="end" fontSize={13} fill="currentColor">
      {lines.map((l, i) => (
        <tspan key={i} x={x - 6} dy={i === 0 ? (lines.length > 1 ? '-0.2em' : '0.35em') : '1.2em'}>
          {l}
        </tspan>
      ))}
    </text>
  )
}

export function ProgressChart({ points, personalBestDay }: Pick<Progress, 'points' | 'personalBestDay'>) {
  const data = points.map((p) => ({ day: p.day, value: p.value, label: p.label }))
  const extent = Math.max(10, ...points.map((p) => Math.abs(p.value)))
  const best = personalBestDay ? data.find((p) => p.day === personalBestDay) : undefined
  return (
    <div className="text-foreground" role="img" aria-label="Graf vaših rezultatov skozi čas">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 24, right: 16, bottom: 8, left: 0 }}>
          <XAxis dataKey="day" tickFormatter={shortDate} interval="preserveStartEnd" tick={{ fontSize: 13 }} />
          <YAxis
            width={92}
            domain={[-extent, extent]}
            ticks={[-extent, 0, extent]}
            tick={<WordTick />}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine y={0} stroke="currentColor" strokeDasharray="4 4" strokeOpacity={0.5} />
          <Tooltip
            formatter={(_v, _n, item) => [WORDS[(item.payload as { label: keyof typeof WORDS }).label], 'Rezultat']}
            labelFormatter={(d) => longDate(String(d))}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="currentColor"
            strokeWidth={3}
            dot={{ r: 4, fill: 'currentColor' }}
            activeDot={{ r: 6 }}
            isAnimationActive={false}
          />
          {best ? (
            <ReferenceDot
              x={best.day}
              y={best.value}
              r={9}
              fill="none"
              stroke="currentColor"
              strokeWidth={3}
              label={{ value: 'Osebni rekord', position: 'top', fontSize: 13, fill: 'currentColor' }}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
