// Small drawing of a level's shape (the channel and its start / end markers), e.g. for the
// overview of today's self-check. Colours come from the design tokens.
import { getLevel, LEVEL_UNITS } from './levels'

export function LevelPreview({ level, className }: { level: number; className?: string }) {
  const l = getLevel(level)
  if (!l) return null
  const d = l.path.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]} ${p[1]}`).join(' ')
  const [sx, sy] = l.path[0]
  const [ex, ey] = l.path[l.path.length - 1]
  const same = Math.hypot(sx - ex, sy - ey) < l.channelWidth
  const w = l.channelWidth * 1.6
  return (
    <svg viewBox={`0 0 ${LEVEL_UNITS} ${LEVEL_UNITS}`} aria-hidden className={className}>
      <path d={d} fill="none" stroke="var(--input)" strokeWidth={w + 16} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke="var(--card)" strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />
      {same ? null : <circle cx={ex} cy={ey} r={w * 0.62} fill="var(--card)" stroke="var(--foreground)" strokeWidth="22" />}
      <circle cx={sx} cy={sy} r={w * 0.62} fill="var(--foreground)" />
      <path
        d={`M${sx - w * 0.16} ${sy - w * 0.26} L${sx + w * 0.26} ${sy} L${sx - w * 0.16} ${sy + w * 0.26} Z`}
        fill="var(--card)"
      />
    </svg>
  )
}
