// The three camera exercises. Timelines come from GET /api/camera/exercises (single source of truth:
// backend/models/camera/exercises.py); FALLBACK mirrors that file for when the request fails, so a
// flaky network never blocks the exercise. Patient-facing copy is ours (formal "vi").
import type { CameraExercise } from '@/client/api'

export type Detector = CameraExercise['detector']

export const FALLBACK_EXERCISES: readonly CameraExercise[] = [
  {
    level: 1,
    key: 'hand_open_close',
    name: 'Odpiranje in zapiranje dlani',
    detector: 'hand',
    durationS: 21,
    firstCueS: 1,
    cuePeriodS: 3,
    nCues: 7,
    upS: null,
    openWindowS: 0.5,
    instructions: '',
  },
  {
    level: 2,
    key: 'shoulder_abduction',
    name: 'Roke v stran',
    detector: 'pose',
    durationS: 42,
    firstCueS: 1,
    cuePeriodS: 8,
    nCues: 5,
    upS: 4,
    instructions: '',
  },
  {
    level: 3,
    key: 'arm_raise',
    name: 'Dvig rok čim višje',
    detector: 'pose',
    durationS: 42,
    firstCueS: 1,
    cuePeriodS: 8,
    nCues: 5,
    upS: 4,
    instructions: '',
  },
]

export function findExercise(list: readonly CameraExercise[], level: number): CameraExercise | undefined {
  return list.find((e) => e.level === level)
}

export interface CueCopy {
  /** when it happens: "Ob pisku", "Visok pisk" */
  when: string
  /** the word shown large during the exercise (cues.ts PROMPT_WORDS) */
  word: string
  /** what to do */
  what: string
}

export interface ExerciseCopy {
  /** how to sit before the camera starts */
  setup: string
  /** the cues as they will appear on screen */
  cues: CueCopy[]
  /** while the framing check waits */
  framing: string
  /** framing: nothing detected yet */
  notSeen: string
}

const HAND: ExerciseCopy = {
  setup: 'Komolec naslonite na mizo in dlan obrnite proti kameri.',
  cues: [
    { when: 'Ob pisku', word: 'Odprite', what: 'Dlan čim bolj odprite.' },
    { when: 'Med piski', word: 'Stisnite', what: 'Dlan stisnite v pest.' },
  ],
  framing: 'Dlan obrnite proti kameri, da je vsa v kadru.',
  notSeen: 'Dlani še ne vidimo. Dvignite jo pred kamero, z dlanjo proti zaslonu.',
}

const ARMS_SETUP = 'Sedite vzravnano, tako da so v kadru glava, rame in obe roki.'
const ARMS_FRAMING = 'Sedite vzravnano, da so v kadru glava, rame in obe roki.'
const ARMS_NOT_SEEN = 'Zgornjega dela telesa še ne vidimo. Odmaknite se malo od kamere.'
const DOWN: CueCopy = { when: 'Nizek pisk', word: 'Dol', what: 'Roki počasi spustite.' }

const COPY: Record<string, ExerciseCopy> = {
  hand_open_close: HAND,
  shoulder_abduction: {
    setup: ARMS_SETUP,
    cues: [{ when: 'Visok pisk', word: 'Gor', what: 'Iztegnjeni roki skozi stran dvignite čim višje.' }, DOWN],
    framing: ARMS_FRAMING,
    notSeen: ARMS_NOT_SEEN,
  },
  arm_raise: {
    setup: ARMS_SETUP,
    cues: [{ when: 'Visok pisk', word: 'Gor', what: 'Roki dvignite čim višje nad glavo.' }, DOWN],
    framing: ARMS_FRAMING,
    notSeen: ARMS_NOT_SEEN,
  },
}

export function exerciseCopy(ex: CameraExercise): ExerciseCopy {
  return (
    COPY[ex.key] ??
    (ex.detector === 'hand'
      ? HAND
      : {
          setup: ARMS_SETUP,
          cues: [{ when: 'Visok pisk', word: 'Gor', what: 'Roki dvignite.' }, DOWN],
          framing: ARMS_FRAMING,
          notSeen: ARMS_NOT_SEEN,
        })
  )
}

/** "21 sekund", "42 sekund" (Slovenian plural forms). */
export function secondsPhrase(s: number): string {
  const n = Math.round(s)
  const mod = n % 100
  const word = mod === 1 ? 'sekunda' : mod === 2 ? 'sekundi' : mod === 3 || mod === 4 ? 'sekunde' : 'sekund'
  return `${n} ${word}`
}
