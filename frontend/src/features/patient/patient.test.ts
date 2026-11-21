import { describe, expect, it } from 'vitest'
import type { SelfcheckStep } from '@/client/api'
import { firstName, joinAnd, longDate, parseDay, relativeDay } from './format'
import { buildWizard, isPartlyDone, startIndex } from './wizard'

const steps = (done: boolean[]): SelfcheckStep[] =>
  [
    { id: 'ratings', kind: 'ratings', title: 'Počutje in bolečina' },
    { id: 'trace:1', kind: 'game', title: 'Ravna črta', gameType: 'trace', level: 1 },
    { id: 'trace:2', kind: 'game', title: 'Krog', gameType: 'trace', level: 2 },
    { id: 'trace:3', kind: 'game', title: 'Labirint', gameType: 'trace', level: 3 },
  ].map((s, i) => ({ ...s, done: done[i] }) as SelfcheckStep)

describe('wizard steps', () => {
  it('appends the result step and keeps the API order', () => {
    const w = buildWizard(steps([false, false, false, false]))
    expect(w.map((s) => s.key)).toEqual(['ratings', 'trace:1', 'trace:2', 'trace:3', 'result'])
    expect(w[2]).toMatchObject({ kind: 'game', gameType: 'trace', level: 2 })
  })

  it('takes a new game type without code changes', () => {
    const s = [...steps([true, true, true, true]), { id: 'camera_tapping:1', kind: 'game', title: 'Gibanje roke', gameType: 'camera_tapping', level: 1, done: false } as SelfcheckStep]
    expect(buildWizard(s)[4]).toMatchObject({ kind: 'game', gameType: 'camera_tapping' })
    expect(startIndex(s)).toBe(4)
  })

  it('skips a game step without a game type', () => {
    const s = [...steps([false, false, false, false]), { id: 'x', kind: 'game', title: 'X', done: false } as SelfcheckStep]
    expect(buildWizard(s)).toHaveLength(5)
  })

  it('starts at the first step not done today', () => {
    expect(startIndex(steps([false, false, false, false]))).toBe(0)
    expect(startIndex(steps([true, true, false, false]))).toBe(2)
    expect(startIndex(steps([true, false, true, false]))).toBe(1)
  })

  it('starts from the beginning when everything is done (a repeat)', () => {
    expect(startIndex(steps([true, true, true, true]))).toBe(0)
  })

  it('knows a partly done self-check', () => {
    expect(isPartlyDone(steps([true, false, false, false]))).toBe(true)
    expect(isPartlyDone(steps([false, false, false, false]))).toBe(false)
    expect(isPartlyDone(steps([true, true, true, true]))).toBe(false)
  })
})

describe('wording', () => {
  it('takes the first name', () => {
    expect(firstName('Marija Kovač')).toBe('Marija')
  })

  it('writes dates in the genitive', () => {
    expect(longDate(parseDay('2026-11-18'))).toBe('18. novembra')
    expect(relativeDay('2026-11-21', '2026-11-21')).toBe('danes')
    expect(relativeDay('2026-11-20', '2026-11-21')).toBe('včeraj')
    expect(relativeDay('2026-10-30', '2026-11-21')).toBe('30. oktobra')
  })

  it('joins with "in"', () => {
    expect(joinAnd(['Ravna črta', 'Krog', 'Labirint'])).toBe('Ravna črta, Krog in Labirint')
    expect(joinAnd(['Krog'])).toBe('Krog')
  })
})
