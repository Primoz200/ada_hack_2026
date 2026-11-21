// Cue timeline of an exercise, exactly as the teammate's recorder (backend/models/camera/recorder) builds
// it: cues at 1000 * (firstCueS + k * cuePeriodS) ms from the start of the recording.
//   hand: one beep per cue = hand fully open; "Odprite" from cue - openWindow to cue + openWindow.
//   arms: high beep at the cue = up (held for upS), low beep at cue + upS = down.
import type { CameraExercise } from '@/client/api'

export type Prompt = 'rest' | 'open' | 'close' | 'up' | 'down'

export const PROMPT_WORDS: Record<Prompt, string> = {
  rest: 'Mirno',
  open: 'Odprite',
  close: 'Stisnite',
  up: 'Gor',
  down: 'Dol',
}

/** Beep pitches of the recorder (Hz). */
export const BEEP_HZ = { open: 1000, up: 880, down: 520, countdown: 440 } as const

type Timeline = Pick<CameraExercise, 'firstCueS' | 'cuePeriodS' | 'nCues' | 'upS' | 'openWindowS'>

export function cueTimes(ex: Timeline): number[] {
  return Array.from({ length: ex.nCues }, (_, k) => 1000 * (ex.firstCueS + k * ex.cuePeriodS))
}

export interface Beep {
  /** ms from the start of the recording */
  atMs: number
  hz: number
}

export function beepSchedule(ex: Timeline): Beep[] {
  const out: Beep[] = []
  for (const c of cueTimes(ex)) {
    if (ex.upS) {
      out.push({ atMs: c, hz: BEEP_HZ.up })
      out.push({ atMs: c + ex.upS * 1000, hz: BEEP_HZ.down })
    } else {
      out.push({ atMs: c, hz: BEEP_HZ.open })
    }
  }
  return out
}

/** What the patient should be doing at t ms into the recording (the recorder's updatePrompt). */
export function promptAt(ex: Timeline, tMs: number): Prompt {
  const cues = cueTimes(ex)
  if (cues.length === 0) return 'rest'
  if (!ex.upS) {
    const w = 1000 * (ex.openWindowS ?? 0.5)
    const first = cues[0]
    const last = cues[cues.length - 1]
    if (tMs < first - w || tMs >= last + w) return 'rest'
    return cues.some((c) => tMs >= c - w && tMs < c + w) ? 'open' : 'close'
  }
  if (tMs < cues[0]) return 'rest'
  const k = Math.floor((tMs - cues[0]) / (1000 * ex.cuePeriodS))
  if (k >= cues.length) return 'rest'
  const since = tMs - cues[k]
  return since < ex.upS * 1000 ? 'up' : 'down'
}
