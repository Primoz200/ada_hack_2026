import { describe, expect, it } from 'vitest'
import type { Alert, Checkin, PatientListItem, Question, SessionSummary, Timeline, TrendPoint } from '@/client/api'
import {
  alertDivergence,
  alertFacts,
  alertTriggers,
  assembleActionLog,
  chartMarkers,
  checkinRows,
  combinedRows,
  defaultTab,
  deltaWords,
  featureComparison,
  filterPatients,
  levelRows,
  nextVisitText,
  pickBaselineSession,
  pointsText,
  ratingSeries,
  sparkRows,
  splitStrokes,
  timeDomain,
  trendSummary,
  visitWhen,
  dayMs,
  GAME_SPARK_DOMAIN,
  SPARK_DAYS,
} from './model'

// A declining stroke patient with an open yellow alert (patient 3 story): 5 weeks, level 1 only for brevity.
const start = Date.parse('2026-10-12T00:00:00Z')
const iso = (i: number) => new Date(start + i * 86_400_000).toISOString().slice(0, 10)

const sessions: SessionSummary[] = Array.from({ length: 10 }, (_, i) => {
  const score = i < 6 ? 80 + i : 85 - (i - 5) * 4
  return {
    id: i + 1,
    gameType: 'trace',
    level: 1,
    hand: 'right',
    day: iso(i * 3),
    startedAt: `${iso(i * 3)}T09:00:00Z`,
    durationMs: 30000 + i * 1500,
    completed: true,
    abortReason: null,
    inputDevice: 'mouse',
    score,
    impairmentClass: 'mild',
    modelVersion: 'standin-1',
    features: { mean_dev: 0.02 + i * 0.004, duration_s: 30 + i * 1.5, pause_rate_hz: 0.1 },
    countsForTrend: i > 0,
  }
})

const trends: TrendPoint[] = [
  ...sessions.map((s, i): TrendPoint => ({
    metric: 'trace:1',
    day: s.day,
    nSessions: i + 1,
    baseline: i >= 3 ? 82 : null,
    ewma: s.score as number,
    delta: i >= 3 ? (s.score as number) - 82 : null,
    deltaPct: null,
    direction: i >= 8 ? 'declining' : 'stable',
  })),
  ...sessions.map((s, i): TrendPoint => ({
    metric: 'trace:all',
    day: s.day,
    nSessions: i + 1,
    baseline: null,
    ewma: null,
    delta: i >= 3 ? (s.score as number) - 82 : null,
    deltaPct: null,
    direction: i >= 8 ? 'declining' : 'stable',
  })),
]

const checkins: Checkin[] = [0, 1, 2, 3].map((i) => ({
  id: i + 1,
  patientId: 'p3',
  day: iso(i * 5),
  createdAt: `${iso(i * 5)}T08:00:00Z`,
  answers: (i === 3 ? { wellbeing: 5 } : { wellbeing: 8 - i, pain: 2 + i }) as Record<string, number>,
}))

const alert: Alert = {
  id: 7,
  patientId: 'p3',
  patientName: 'Marko Zupan',
  source: 'game',
  rule: 'trend_drop',
  severity: 'yellow',
  status: 'new',
  reason: 'Rezultati igre so 12 točk pod izhodiščem.',
  evidence: {
    triggers: [{ rule: 'trend_drop', severity: 'yellow', day: iso(27), reason: 'Sledenje je že 5 dni pod izhodiščem.' }, 'junk', { reason: 5 }],
    delta: -11.4,
    divergence: 'Rezultati igre padajo, pacient pa poroča enako ali boljše počutje.',
  },
  diverging: true,
  openedDay: iso(27),
  createdAt: `${iso(27)}T10:00:00Z`,
  updatedAt: `${iso(27)}T10:00:00Z`,
  acknowledgedBy: 'c1',
  acknowledgedAt: `${iso(28)}T09:00:00Z`,
  closedBy: null,
  closedAt: null,
  outcome: null,
  note: null,
}

const timeline: Timeline = {
  patientId: 'p3',
  today: iso(29),
  dischargeDate: iso(-20),
  nextVisitDate: iso(35),
  sessions,
  checkins,
  trends,
  alerts: [alert],
}

const questions: Question[] = [
  { id: 'pain', kind: 'scale', text: 'Bolečina?', shortLabel: 'Bolečina', min: 1, max: 10, higherIsWorse: true },
  { id: 'wellbeing', kind: 'scale', text: 'Počutje?', shortLabel: 'Počutje', min: 1, max: 10, higherIsWorse: false },
]

describe('triage list', () => {
  const mk = (id: string, status: PatientListItem['status']): PatientListItem => ({
    id, name: id, pathwayCode: 'stroke', pathwayName: 'Kap', side: 'right', daysSinceDischarge: 10, status,
    reason: '', diverging: false, gameSparkline: [], wellbeingSparkline: [], daysToNextVisit: null, openAlertId: null, isDemo: false,
  })
  it('filters tabs and picks the default', () => {
    const ps = [mk('a', 'yellow'), mk('b', 'stable'), mk('c', 'no_data'), mk('d', 'red')]
    expect(filterPatients(ps, 'attention').map((p) => p.id)).toEqual(['a', 'd'])
    expect(filterPatients(ps, 'no_data').map((p) => p.id)).toEqual(['c'])
    expect(filterPatients(ps, 'all')).toHaveLength(4)
    expect(defaultTab(ps)).toBe('attention')
    expect(defaultTab([mk('b', 'stable')])).toBe('all')
  })
  it('formats the next visit', () => {
    expect(nextVisitText(null)).toBe('ni načrtovanega pregleda')
    expect(nextVisitText(14)).toBe('naslednji pregled čez 14 dni')
    expect(nextVisitText(1)).toBe('naslednji pregled čez 1 dan')
    expect(visitWhen(30)).toBe('čez 30 dni')
    expect(visitWhen(null)).toBe('ni načrtovan')
    expect(visitWhen(-2)).toBe('zamujen 2 dneva')
  })
  it('builds fixed-window sparklines that break at missing days and clamp', () => {
    const rows = sparkRows(
      [
        { day: iso(29), value: -35 },
        { day: iso(27), value: -4 },
        { day: iso(0), value: 3 }, // outside the window
      ],
      iso(29),
      GAME_SPARK_DOMAIN,
    )
    expect(rows).toHaveLength(SPARK_DAYS)
    expect(rows[rows.length - 1]).toEqual({ t: dayMs(iso(29)), v: -20 })
    expect(rows[rows.length - 3].v).toBe(-4)
    expect(rows[rows.length - 2].v).toBeNull()
    expect(rows.filter((r) => r.v != null)).toHaveLength(2)
  })
})

describe('trend shaping', () => {
  it('builds combined rows sorted by day', () => {
    const rows = combinedRows(trends)
    expect(rows).toHaveLength(10)
    expect(rows[0].t).toBeLessThan(rows[9].t)
    expect(rows[9].delta).toBe(-13)
  })
  it('merges sessions and EWMA for a level', () => {
    const rows = levelRows(1, sessions, trends)
    expect(rows.filter((r) => r.score != null)).toHaveLength(10)
    expect(rows.filter((r) => r.ewma != null)).toHaveLength(10)
    expect(levelRows(2, sessions, trends)).toEqual([])
  })
  it('summarises the latest trend point with its basis', () => {
    const s = trendSummary(trends, 'trace:all')
    expect(s).toMatchObject({ delta: -13, nSessions: 10, direction: 'declining' })
    expect(trendSummary([], 'trace:all').nSessions).toBe(0)
    expect(deltaWords(-14)).toBe('14 točk pod izhodiščem')
    expect(deltaWords(-11.4)).toBe('11,4 točke pod izhodiščem')
    expect(deltaWords(6)).toBe('6 točk nad izhodiščem')
    expect(deltaWords(2)).toBe('v pasu izhodišča')
    expect(pointsText(2)).toBe('2 točki')
    expect(pointsText(-1)).toBe('1 točka')
    expect(deltaWords(null)).toBe('ni izhodišča')
  })
})

describe('time axis and markers', () => {
  it('covers data and the upcoming visit, and keeps markers inside', () => {
    const dom = timeDomain(timeline)
    expect(dom.start).toBe(start)
    expect(dom.end).toBe(dayMs(iso(35)))
    const m = chartMarkers(timeline, dom)
    expect(m.map((x) => x.kind)).toEqual(['alert', 'visit'])
  })
  it('does not stretch to a far-away visit', () => {
    const dom = timeDomain({ ...timeline, nextVisitDate: iso(200) })
    expect(dom.end).toBe(dayMs(timeline.today))
  })
  it('copes with an empty timeline', () => {
    const dom = timeDomain({ ...timeline, sessions: [], checkins: [], trends: [], alerts: [] })
    expect(dom.end).toBeGreaterThan(dom.start)
  })
})

describe('features', () => {
  it('compares sessions 2-4 with the last 3 and ranks by relative change', () => {
    const c = featureComparison(sessions, 1)
    expect(c.nBaseline).toBe(3)
    expect(c.nRecent).toBe(3)
    expect(c.rows).toHaveLength(3)
    expect(c.rows[0].change).toBeGreaterThan(0)
    expect(c.rows[0].key).toBe('mean_dev')
    expect(c.rows[2].key).toBe('pause_rate_hz')
    expect(c.rows[2].change).toBeCloseTo(0)
  })
  it('lists each feature once across levels', () => {
    const lv2 = sessions.map((s) => ({ ...s, id: s.id + 100, level: 2 }))
    const keys = featureComparison([...sessions, ...lv2], null).rows.map((r) => r.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
  it('returns nothing when there are too few sessions', () => {
    expect(featureComparison(sessions.slice(0, 4), 1).rows).toEqual([])
    expect(featureComparison([], null).rows).toEqual([])
  })
  it('picks a baseline session among sessions 2-4', () => {
    const b = pickBaselineSession(sessions, 1)
    expect([2, 3, 4]).toContain(b?.id)
    expect(pickBaselineSession([], 1)).toBeNull()
  })
})

describe('ratings', () => {
  it('keeps wellbeing first and pain second, each on its own series', () => {
    const s = ratingSeries(questions, checkins)
    expect(s.map((x) => x.question.id)).toEqual(['wellbeing', 'pain'])
    expect(s[0].points.map((p) => p.value)).toEqual([8, 7, 6, 5])
    expect(s[1].points.map((p) => p.value)).toEqual([2, 3, 4])
  })
  it('falls back to default questions when the pathway has none', () => {
    expect(ratingSeries([], checkins).map((x) => x.question.shortLabel)).toEqual(['Počutje', 'Bolečina'])
  })
  it('lists check-ins newest first', () => {
    expect(checkinRows(checkins).map((c) => c.id)).toEqual([4, 3, 2, 1])
  })
})

describe('replay', () => {
  it('splits strokes by strokeId', () => {
    const strokes = splitStrokes({ x: [0, 0.1, 0.2, 0.3], y: [0, 0, 1, 1], strokeId: [0, 0, 1, 1] })
    expect(strokes).toHaveLength(2)
    expect(strokes[1].points).toEqual([{ x: 0.2, y: 1 }, { x: 0.3, y: 1 }])
    expect(splitStrokes({})).toEqual([])
  })
})

describe('alert evidence and action log', () => {
  it('reads evidence defensively', () => {
    const t = alertTriggers(alert)
    expect(t).toHaveLength(1) // the junk entries are dropped
    expect(t[0]).toMatchObject({ rule: 'trend_drop', severity: 'yellow' })
    expect(alertDivergence(alert)).toContain('padajo')
    expect(alertTriggers({ evidence: {} })).toEqual([])
    expect(alertDivergence({ evidence: {} })).toBeNull()
  })
  it('picks at most two key facts: change vs baseline and the next visit', () => {
    const p = { daysToNextVisit: 30, nextVisitDate: iso(59), summary: { nSessions: 10, nCheckins: 4, lastSessionDay: iso(27), lastCheckinDay: iso(15), combinedDelta: -9, combinedDirection: 'declining' as const } }
    const f = alertFacts(alert, p, iso(29))
    expect(f.map((x) => x.value)).toEqual(['11,4 točke pod izhodiščem', 'čez 30 dni'])
    // no delta in the evidence: fall back to the patient summary
    expect(alertFacts({ ...alert, evidence: {} }, p, iso(29))[0].value).toBe('9 točk pod izhodiščem')
    // nothing to say about the change: only the visit
    expect(alertFacts({ ...alert, evidence: {} }, { ...p, summary: { ...p.summary, combinedDelta: null } }, iso(29))).toHaveLength(1)
    const subj = alertFacts({ rule: 'subjective_drop', evidence: { wellbeingChange: -1, painChange: 3 } }, p, iso(29))
    expect(subj[0]).toMatchObject({ label: 'Bolečina', value: '3 točke višje kot teden prej' })
    const nd = alertFacts({ rule: 'no_data', evidence: {} }, { ...p, daysToNextVisit: null, nextVisitDate: null }, iso(29))
    expect(nd.map((x) => x.value)).toEqual(['pred 2 dneva', 'ni načrtovan'])
  })
  it('assembles the log newest first', () => {
    const closed: Alert = { ...alert, status: 'closed', closedBy: 'c1', closedAt: `${iso(29)}T09:00:00Z`, outcome: 'called_reassured', note: 'Pomiril.' }
    const log = assembleActionLog([closed], { called_reassured: 'Poklical, pomiril' }, { c1: 'dr. Novak' })
    expect(log.map((l) => l.kind)).toEqual(['closed', 'acknowledged', 'opened'])
    expect(log[0].text).toContain('Poklical, pomiril')
    expect(log[0].detail).toBe('Pomiril.')
    expect(log[1].text).toContain('dr. Novak')
  })
})
