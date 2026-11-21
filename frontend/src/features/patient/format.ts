// Small Slovenian wording helpers for the patient screens. Pure, tested in format.test.ts.
import type { Hand } from '@/games/shared/types'

const MONTHS_GENITIVE = [
  'januarja',
  'februarja',
  'marca',
  'aprila',
  'maja',
  'junija',
  'julija',
  'avgusta',
  'septembra',
  'oktobra',
  'novembra',
  'decembra',
]

/** "Marija Kovač" -> "Marija" */
export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] ?? ''
}

/** A calendar day "2026-11-18" as a local Date at noon (no time-zone shift). */
export function parseDay(day: string): Date {
  const [y, m, d] = day.slice(0, 10).split('-').map(Number)
  return new Date(y, (m ?? 1) - 1, d ?? 1, 12)
}

/** "18. novembra" (genitive, as used in a sentence). */
export function longDate(d: Date): string {
  return `${d.getDate()}. ${MONTHS_GENITIVE[d.getMonth()]}`
}

/** "18. 11." for chart axes. */
export function shortDate(d: Date): string {
  return `${d.getDate()}. ${d.getMonth() + 1}.`
}

/** "danes" / "včeraj" / "18. novembra", relative to the server's today. */
export function relativeDay(day: string, today: string): string {
  const diff = Math.round((parseDay(today).getTime() - parseDay(day).getTime()) / 86_400_000)
  if (diff === 0) return 'danes'
  if (diff === 1) return 'včeraj'
  return longDate(parseDay(day))
}

export function handPhrase(hand: Hand): string {
  return hand === 'left' ? 'z levo roko' : 'z desno roko'
}

/** "a", "a in b", "a, b in c" */
export function joinAnd(items: readonly string[]): string {
  if (items.length <= 1) return items[0] ?? ''
  return `${items.slice(0, -1).join(', ')} in ${items[items.length - 1]}`
}

/** "4 od 7 dni" */
export function daysOf(done: number, total: number): string {
  return `${done} od ${total} dni`
}
