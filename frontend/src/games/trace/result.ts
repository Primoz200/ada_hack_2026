// Assembles the GameResult exactly as games/shared/types.ts describes it.
import type { GameConfig, GameResult, InputDevice } from '../shared/types'
import { targetSeries, type TraceLevel } from './levels'
import type { TraceSeries } from './recorder'

export interface BuildResultInput {
  config: GameConfig
  level: TraceLevel
  recorded: TraceSeries
  startedAt: Date
  durationMs: number
  completed: boolean
  abortReason?: string
  inputDevice: InputDevice
  canvasW: number
  canvasH: number
  devicePixelRatio: number
  userAgent: string
}

export function buildResult(i: BuildResultInput): GameResult {
  const target = targetSeries(i.level)
  return {
    gameType: i.config.gameType,
    level: i.config.level,
    hand: i.config.hand,
    startedAt: i.startedAt.toISOString(),
    durationMs: Math.max(0, Math.round(i.durationMs)),
    completed: i.completed,
    ...(i.abortReason ? { abortReason: i.abortReason } : {}),
    series: {
      targetX: target.targetX,
      targetY: target.targetY,
      t: [...i.recorded.t],
      x: [...i.recorded.x],
      y: [...i.recorded.y],
      strokeId: [...i.recorded.strokeId],
    },
    clientMeta: {
      inputDevice: i.inputDevice,
      canvasW: i.canvasW,
      canvasH: i.canvasH,
      devicePixelRatio: i.devicePixelRatio,
      userAgent: i.userAgent,
    },
  }
}

/** Result for "Danes ne morem" before anything was drawn. */
export function emptyAbortResult(config: GameConfig, level: TraceLevel): GameResult {
  return buildResult({
    config,
    level,
    recorded: { t: [], x: [], y: [], strokeId: [] },
    startedAt: new Date(),
    durationMs: 0,
    completed: false,
    abortReason: 'cannot_today',
    inputDevice: 'touch',
    canvasW: 0,
    canvasH: 0,
    devicePixelRatio: typeof window === 'undefined' ? 1 : window.devicePixelRatio || 1,
    userAgent: typeof navigator === 'undefined' ? '' : navigator.userAgent,
  })
}
