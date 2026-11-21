// Interface between games and the platform (IMPLEMENTATION_PLAN.md section 5).
// Shared hot file: changing it changes the contract with the backend (SessionIn).
import type { ComponentType } from 'react'

export type GameType = 'trace' | 'camera'
export type Hand = 'left' | 'right'
export type InputDevice = 'touch' | 'mouse' | 'camera'

export interface GameConfig {
  gameType: GameType
  /** A measurement round uses FIXED levels, otherwise the trend breaks. */
  level: number
  hand: Hand
  patientId: string
}

export interface GameResult {
  gameType: GameType
  level: number
  hand: Hand
  /** ISO, start of the test */
  startedAt: string
  /** from first touch to the end */
  durationMs: number
  /** false if the patient aborted or the time limit ran out */
  completed: boolean
  /** e.g. "cannot_today" | "time_limit" when completed is false */
  abortReason?: string
  /**
   * trace: targetX, targetY, t, x, y, strokeId (coordinates normalised 0-1 on a square canvas).
   * camera: t, lm{i}_x/_y/_z, w{i}_x/_y/_z, lm{i}_v, handScore, handMatch, cueT (null = no detection in that frame).
   */
  series: Record<string, (number | null)[]>
  clientMeta: {
    inputDevice: InputDevice
    canvasW: number
    canvasH: number
    devicePixelRatio: number
    userAgent: string
    /** camera sessions add videoW, videoH, fpsMeasured, mediapipe, detector, delegate, mirroredPreview */
    [extra: string]: unknown
  }
}

export interface GameProps {
  config: GameConfig
  /** Called once with the result, also for aborted attempts (completed: false). */
  onComplete: (result: GameResult) => void
  /** The patient left before starting; nothing is recorded. */
  onAbort: () => void
}

export type GameComponent = ComponentType<GameProps>
