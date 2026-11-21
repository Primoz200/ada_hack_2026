// Simple illustration of a level's shape for the instructions screen.
import { getLevel, LEVEL_UNITS } from './levels'

export function LevelPreview({ level, className }: { level: number; className?: string }) {
  const l = getLevel(level)
  if (!l) return null
  const d = l.path.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]} ${p[1]}`).join(' ')
  const [sx, sy] = l.path[0]
  const [ex, ey] = l.path[l.path.length - 1]
  const same = Math.hypot(sx - ex, sy - ey) < l.channelWidth
  return (
    <svg
      viewBox={`0 0 ${LEVEL_UNITS} ${LEVEL_UNITS}`}
      role="img"
      aria-label="Oblika poti, ki ji boste sledili"
      className={className}
    >
      <rect width={LEVEL_UNITS} height={LEVEL_UNITS} rx="40" fill="white" stroke="#cbd5e1" strokeWidth="6" />
      <path d={d} fill="none" stroke="#94a3b8" strokeWidth={l.channelWidth + 8} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke="#e2e8f0" strokeWidth={l.channelWidth} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={ex} cy={ey} r="36" fill="white" stroke="#0f172a" strokeWidth="10" />
      <circle cx={sx} cy={sy} r="30" fill="#0f172a" />
      <path d={`M${sx - 8} ${sy - 14} L${sx + 14} ${sy} L${sx - 8} ${sy + 14} Z`} fill="white" />
      <g fontSize="46" fontWeight="600" fill="#0f172a" textAnchor="middle" fontFamily="system-ui, sans-serif">
        {same ? (
          <text x={sx} y={sy - 52}>
            Začetek in konec
          </text>
        ) : (
          <>
            <text x={Math.max(110, sx)} y={sy - 52}>
              Začetek
            </text>
            <text x={Math.min(900, ex)} y={ey - 52}>
              Konec
            </text>
          </>
        )}
      </g>
    </svg>
  )
}
