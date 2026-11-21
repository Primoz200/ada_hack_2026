// Stand-in game: returns a prepared GameResult after 3 seconds. Fallback for game types
// that have no real implementation yet.
import { useEffect } from 'react'
import type { GameProps } from '../shared/types'

export function StubGame({ config, onComplete }: GameProps) {
  useEffect(() => {
    const startedAt = new Date().toISOString()
    const id = setTimeout(() => {
      const n = 40
      const xs = Array.from({ length: n }, (_, i) => 0.1 + (0.8 * i) / (n - 1))
      onComplete({
        gameType: config.gameType,
        level: config.level,
        hand: config.hand,
        startedAt,
        durationMs: 3000,
        completed: true,
        series: {
          targetX: [0.1, 0.9],
          targetY: [0.5, 0.5],
          t: xs.map((_, i) => i * 75),
          x: xs,
          y: xs.map((_, i) => 0.5 + 0.01 * Math.sin(i)),
          strokeId: xs.map(() => 0),
        },
        clientMeta: {
          inputDevice: 'mouse',
          canvasW: 320,
          canvasH: 320,
          devicePixelRatio: window.devicePixelRatio,
          userAgent: navigator.userAgent,
        },
      })
    }, 3000)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return <div className="p-8 text-center text-lg">Nadomestna igra … (3 s)</div>
}
