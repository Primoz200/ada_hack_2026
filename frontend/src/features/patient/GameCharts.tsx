// One small recovery chart per game (Sledenje, Vaje s kamero). With a single game the screens read
// exactly as before; with more, each chart carries its game's name from the API and all charts share
// one time axis, so the same day sits at the same place.
import type { GameProgress } from '@/client/api'
import { RecoveryChart } from './RecoveryChart'
import { FeedbackMark } from './ui'

/** Games with enough points for a line. */
function chartable(games: readonly GameProgress[]): GameProgress[] {
  return games.filter((g) => g.points.length >= 2)
}

/** Every day any of the games has a point, sorted: the shared x axis. */
function sharedDays(games: readonly GameProgress[]): string[] {
  return [...new Set(games.flatMap((g) => g.points.map((p) => p.day)))].sort()
}

/** Result step: "Zadnjih 14 dni", then one chart per game. No statistics. */
export function ResultCharts({ games }: { games: readonly GameProgress[] }) {
  const shown = chartable(games)
  if (shown.length === 0) return null
  if (shown.length === 1) {
    return (
      <figure className="mt-7">
        <figcaption className="mb-1 text-[0.95rem] font-medium text-muted-foreground">Zadnjih 14 dni</figcaption>
        <div className="-ml-2">
          <RecoveryChart points={shown[0].points} height={220} label={`Graf: ${shown[0].title}, zadnjih 14 dni`} />
        </div>
      </figure>
    )
  }
  const days = sharedDays(shown)
  return (
    <div className="mt-6 space-y-3">
      {shown.map((g) => (
        <figure key={g.gameType}>
          <figcaption className="text-[1.0625rem] font-semibold">
            {g.title} <span className="text-[0.95rem] font-medium text-muted-foreground">· zadnjih 14 dni</span>
          </figcaption>
          <div className="-ml-2">
            <RecoveryChart points={g.points} days={days} height={128} label={`Graf: ${g.title}, zadnjih 14 dni`} />
          </div>
        </figure>
      ))}
    </div>
  )
}

/**
 * Moj napredek: the whole history, one chart per game. With several games each gets its name, and
 * its own trend word when that differs from the overall one at the top of the panel.
 */
export function ProgressCharts({ games, overallTrend }: { games: readonly GameProgress[]; overallTrend?: string }) {
  const shown = chartable(games)
  if (shown.length === 0) {
    return (
      <p className="mt-8 rounded-xl bg-muted p-6 text-muted-foreground">Graf se bo pokazal po naslednjih samopregledih.</p>
    )
  }
  if (shown.length === 1) {
    return (
      <div className="mt-8 -ml-2">
        <RecoveryChart points={shown[0].points} personalBestDay={shown[0].personalBestDay} height={300} />
      </div>
    )
  }
  const days = sharedDays(shown)
  return (
    <div className="mt-8 space-y-7">
      {shown.map((g, i) => (
        <section key={g.gameType} className={i > 0 ? 'border-t border-border pt-7' : undefined} aria-label={g.title}>
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
            <h3 className="text-xl font-bold">{g.title}</h3>
            {g.trend !== 'unknown' && g.trend !== overallTrend ? <FeedbackMark tone="similar" trend={g.trend} /> : null}
          </div>
          <div className="mt-3 -ml-2">
            <RecoveryChart
              points={g.points}
              personalBestDay={g.personalBestDay}
              days={days}
              height={230}
              label={`Graf: ${g.title}, vaši rezultati skozi čas`}
            />
          </div>
        </section>
      ))}
    </div>
  )
}
