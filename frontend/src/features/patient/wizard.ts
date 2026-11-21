// Pure logic of the self-check wizard: which steps it walks through and where it starts.
// Steps come from the API (home.steps) so a new game is a new step there, not new code here.
import type { SelfcheckStep } from '@/client/api'
import type { GameType } from '@/games/shared/types'

export type WizardStep =
  | { key: string; kind: 'ratings'; title: string }
  | { key: string; kind: 'game'; title: string; gameType: GameType; level: number }
  | { key: 'result'; kind: 'result'; title: string }

export const RESULT_TITLE = 'Rezultat'

/** home.steps in order, plus the result screen at the end. Game steps without a game are skipped. */
export function buildWizard(steps: readonly SelfcheckStep[]): WizardStep[] {
  const out: WizardStep[] = []
  for (const s of steps) {
    if (s.kind === 'ratings') out.push({ key: s.id, kind: 'ratings', title: s.title })
    else if (s.kind === 'game' && s.gameType) {
      out.push({ key: s.id, kind: 'game', title: s.title, gameType: s.gameType, level: s.level ?? 1 })
    }
  }
  out.push({ key: 'result', kind: 'result', title: RESULT_TITLE })
  return out
}

/**
 * Index (into buildWizard(steps)) of the first step not done today. When every step is done
 * the self-check is a repeat and starts from the beginning. Computed once per visit: a later
 * refetch of home must not move the patient.
 */
export function startIndex(steps: readonly SelfcheckStep[]): number {
  const wizard = buildWizard(steps)
  const doneKeys = new Set(steps.filter((s) => s.done).map((s) => s.id))
  const i = wizard.findIndex((w) => w.kind !== 'result' && !doneKeys.has(w.key))
  return i === -1 ? 0 : i
}

/** Some but not all steps done today: the patient continues where they stopped. */
export function isPartlyDone(steps: readonly SelfcheckStep[]): boolean {
  const done = steps.filter((s) => s.done).length
  return done > 0 && done < steps.length
}
