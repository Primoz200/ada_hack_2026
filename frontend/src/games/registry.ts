// gameType -> component. Shared hot file: a new game is one line here.
import { CameraGame } from './camera'
import type { GameComponent, GameType } from './shared/types'
import { TraceGame } from './trace'

export const GAMES: Record<GameType, GameComponent> = {
  trace: TraceGame,
  camera: CameraGame,
}
