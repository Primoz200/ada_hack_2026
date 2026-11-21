import { describe, expect, it } from 'vitest'
import type { SelfcheckStep } from '@/client/api'
import { exercisesPhrase, firstName, joinAnd, longDate, parseDay, relativeDay } from './format'
import { buildWizard, isPartlyDone, previewItems, skipGame, startIndex } from './wizard'

const steps = (done: boolean[]): SelfcheckStep[] =>
  [
    { id: 'ratings', kind: 'ratings', title: 'Počutje in bolečina' },
    { id: 'trace:1', kind: 'game', title: 'Ravna črta', gameType: 'trace', level: 1 },
    { id: 'trace:2', kind: 'game', title: 'Krog', gameType: 'trace', level: 2 },
    { id: 'trace:3', kind: 'game', title: 'Labirint', gameType: 'trace', level: 3 },
  ].map((s, i) => ({ ...s, done: done[i] }) as SelfcheckStep)

const camera = (done: boolean[]): SelfcheckStep[] =>
  (['Dlan', 'Roke v stran', 'Dvig rok'] as const).map((title, i) => ({
    id: `camera:${i + 1}`,
    kind: 'game',
    title,
    gameType: 'camera',
    level: i + 1,
    done: done[i],
    skippable: i > 0,
    durationS: i === 0 ? 21 : 42,
  }))

describe('wizard steps', () => {
  it('appends the result step and keeps the API order', () => {
    const w = buildWizard(steps([false, false, false, false]))
    expect(w.map((s) => s.key)).toEqual(['ratings', 'trace:1', 'trace:2', 'trace:3', 'result'])
    expect(w[2]).toMatchObject({ kind: 'game', gameType: 'trace', level: 2 })
  })

  it('takes a new game type without code changes', () => {
    const s = [...steps([true, true, true, true]), ...camera([false, false, false])]
    expect(buildWizard(s)[4]).toMatchObject({ kind: 'game', gameType: 'camera', skippable: false, durationS: 21 })
    expect(buildWizard(s)[5]).toMatchObject({ skippable: true, durationS: 42 })
    expect(startIndex(s)).toBe(4)
  })

  it('without a camera skips every remaining camera step and goes on', () => {
    const w = buildWizard([...steps([false, false, false, false]), ...camera([false, false, false])])
    expect(skipGame(w, 4)).toEqual({ skipped: ['camera:1', 'camera:2', 'camera:3'], next: 7 })
    expect(skipGame(w, 5)).toEqual({ skipped: ['camera:2', 'camera:3'], next: 7 })
    expect(w[7].kind).toBe('result')
    // a step after the camera steps is not lost
    const later = buildWizard([...camera([false, false, false]), ...steps([false, false, false, false])])
    expect(skipGame(later, 0)).toMatchObject({ next: 3 })
  })

  it('shows the camera exercises as one tile on Domov', () => {
    const items = previewItems([...steps([true, false, false, false]), ...camera([true, false, false])])
    expect(items.map((i) => i.key)).toEqual(['ratings', 'trace:1', 'trace:2', 'trace:3', 'camera'])
    expect(items[4]).toMatchObject({ kind: 'group', title: 'Vaje s kamero', count: 3, done: true })
    expect(items[0]).toMatchObject({ kind: 'step', done: true })
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

  it('counts exercises in Slovenian', () => {
    expect(exercisesPhrase(2)).toBe('2 kratki vaji')
    expect(exercisesPhrase(3)).toBe('3 kratke vaje')
    expect(exercisesPhrase(5)).toBe('5 kratkih vaj')
  })
})
