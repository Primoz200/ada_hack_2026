// Pure logic of the self-check wizard: which steps it walks through and where it starts.
// Steps come from the API (home.steps) so a new game is a new step there, not new code here.
import type { SelfcheckStep } from '@/client/api'
import type { GameType } from '@/games/shared/types'

export type GameStep = {
  key: string
  kind: 'game'
  title: string
  gameType: GameType
  level: number
  /** the patient may skip it ("Preskoči") */
  skippable: boolean
  /** fixed length in seconds, when the exercise has one */
  durationS: number | null
}

export type WizardStep =
  | { key: string; kind: 'ratings'; title: string }
  | GameStep
  | { key: 'result'; kind: 'result'; title: string }

export const RESULT_TITLE = 'Rezultat'

/** Patient-facing name of a game, for grouped previews. */
export const GAME_TITLES: Partial<Record<GameType, string>> = { camera: 'Vaje s kamero' }

/** home.steps in order, plus the result screen at the end. Game steps without a game are skipped. */
export function buildWizard(steps: readonly SelfcheckStep[]): WizardStep[] {
  const out: WizardStep[] = []
  for (const s of steps) {
    if (s.kind === 'ratings') out.push({ key: s.id, kind: 'ratings', title: s.title })
    else if (s.kind === 'game' && s.gameType) {
      out.push({
        key: s.id,
        kind: 'game',
        title: s.title,
        gameType: s.gameType,
        level: s.level ?? 1,
        skippable: s.skippable ?? false,
        durationS: s.durationS ?? null,
      })
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

/**
 * A game could not run at all (e.g. no camera): the keys of the current and every later step of
 * that game, and the index to continue at (the next step of another kind, at the latest the result).
 */
export function skipGame(wizard: readonly WizardStep[], index: number): { skipped: string[]; next: number } {
  const current = wizard[index]
  if (!current || current.kind !== 'game') return { skipped: [], next: Math.min(index + 1, wizard.length - 1) }
  const skipped: string[] = []
  let next = wizard.length - 1
  for (let i = index; i < wizard.length; i++) {
    const s = wizard[i]
    if (s.kind === 'game' && s.gameType === current.gameType) skipped.push(s.key)
    else if (i > index && next === wizard.length - 1 && s.kind !== 'result') next = i
  }
  return { skipped, next: Math.min(next, wizard.length - 1) }
}

export type PreviewItem =
  | { key: string; kind: 'step'; step: WizardStep; done: boolean }
  | { key: string; kind: 'group'; gameType: GameType; title: string; count: number; done: boolean }

/**
 * The overview on Domov: one tile per step, but the steps of a grouped game (camera) share one
 * tile so the overview stays calm. A group is done when its first step is done.
 */
export function previewItems(steps: readonly SelfcheckStep[]): PreviewItem[] {
  const doneKeys = new Set(steps.filter((s) => s.done).map((s) => s.id))
  const out: PreviewItem[] = []
  for (const step of buildWizard(steps)) {
    if (step.kind === 'result') continue
    const groupTitle = step.kind === 'game' ? GAME_TITLES[step.gameType] : undefined
    if (step.kind === 'game' && groupTitle) {
      const prev = out[out.length - 1]
      if (prev?.kind === 'group' && prev.gameType === step.gameType) {
        prev.count += 1
        continue
      }
      out.push({ key: step.gameType, kind: 'group', gameType: step.gameType, title: groupTitle, count: 1, done: doneKeys.has(step.key) })
      continue
    }
    out.push({ key: step.key, kind: 'step', step, done: doneKeys.has(step.key) })
  }
  return out
}
