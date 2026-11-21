// gameType -> component. Shared hot file: a new game is one line here.
import { StubGame } from './_stub/StubGame'
import type { GameComponent, GameType } from './shared/types'
import { TraceGame } from './trace'

export const GAMES: Record<GameType, GameComponent> = {
  trace: TraceGame,
  camera_tapping: StubGame,
  camera_reach: StubGame,
  motion: StubGame,
}
