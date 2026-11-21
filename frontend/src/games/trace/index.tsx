// Trace game entry point. Phase 0 placeholder: agent C replaces this with the real game
// (keep the export name `TraceGame` and the GameProps signature).
import { StubGame } from '../_stub/StubGame'
import type { GameProps } from '../shared/types'

export function TraceGame(props: GameProps) {
  return <StubGame {...props} />
}
