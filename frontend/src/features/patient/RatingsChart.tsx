// One small chart for one daily rating (1-10). Wellbeing and pain run in opposite directions,
// so each gets its own chart with its ends named in words.
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { RatingPoint } from '@/client/api'
import { longDate, parseDay, shortDate } from './format'

interface TickProps {
  x?: number | string
  y?: number | string
  payload?: { value: number }
}

interface TipProps {
  active?: boolean
  payload?: { payload?: { day: string; v: number | null } }[]
}

function EndTick({ x = 0, y = 0, payload, lowWord, highWord }: TickProps & { lowWord: string; highWord: string }) {
  return (
    <text x={Number(x) - 8} y={Number(y)} dy="0.35em" textAnchor="end" fontSize={13} fill="var(--muted-foreground)">
      {payload?.value === 10 ? highWord : lowWord}
    </text>
  )
}

function Tip({ active, payload, title }: TipProps & { title: string }) {
  const p = payload?.[0]?.payload
  if (!active || !p || p.v === null) return null
  return (
    <div className="rounded-lg bg-card px-3 py-2 text-[0.95rem] shadow-panel ring-1 ring-border">
      <div className="font-semibold">{longDate(parseDay(p.day))}</div>
      <div className="text-muted-foreground">
        {title}: <span className="tabular">{p.v}</span> od 10
      </div>
    </div>
  )
}

export function RatingsChart({
  ratings,
  field,
  title,
  direction,
  lowWord,
  highWord,
}: {
  ratings: readonly RatingPoint[]
  field: 'wellbeing' | 'pain'
  title: string
  direction: string
  lowWord: string
  highWord: string
}) {
  const data = ratings.map((r) => ({ day: r.day, v: r[field] ?? null }))
  return (
    <figure className="min-w-0">
      <figcaption className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3">
        <span className="text-lg font-semibold">{title}</span>
        <span className="text-[0.95rem] text-muted-foreground">{direction}</span>
      </figcaption>
      <div role="img" aria-label={`${title} skozi čas, ${direction}`} className="select-none">
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={data} margin={{ top: 10, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis
              dataKey="day"
              tickFormatter={(d: string) => shortDate(parseDay(d))}
              interval="preserveStartEnd"
              minTickGap={36}
              tick={{ fontSize: 13, fill: 'var(--muted-foreground)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border)' }}
              tickMargin={6}
            />
            <YAxis
              width={96}
              domain={[1, 10]}
              ticks={[1, 10]}
              tick={(p: TickProps) => <EndTick {...p} lowWord={lowWord} highWord={highWord} />}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<Tip title={title} />} cursor={{ stroke: 'var(--border)', strokeWidth: 1.5 }} />
            <Line
              type="linear"
              dataKey="v"
              stroke="var(--chart-1)"
              strokeWidth={2.5}
              dot={data.length <= 21 ? { r: 3, fill: 'var(--chart-1)', strokeWidth: 0 } : false}
              activeDot={{ r: 5, fill: 'var(--chart-1)', stroke: 'var(--card)', strokeWidth: 2 }}
              connectNulls
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
