// Pure data shaping for the clinician screens (no React, no fetching). Tested in model.test.ts.
import type { Alert, Checkin, PatientDetail, PatientListItem, Question, SessionSummary, Timeline, TrendPoint } from '@/client/api'

export const DAY_MS = 86_400_000
export const BAND = 5 // "pas izhodišča": ±5 points
export const ALERT_THRESHOLD = -10 // "prag opozorila"

export type Status = PatientListItem['status']
export type Level = 1 | 2 | 3
export const LEVELS: Level[] = [1, 2, 3]
export const LEVEL_NAMES: Record<number, string> = { 1: 'Ravna črta', 2: 'Krog', 3: 'Labirint' }

/** ISO date (YYYY-MM-DD) or datetime -> UTC-midnight ms, so the x axis is timezone independent. */
export function dayMs(iso: string): number {
  return Date.parse(iso.slice(0, 10) + 'T00:00:00Z')
}

export function formatDay(iso: string | number): string {
  const d = typeof iso === 'number' ? new Date(iso) : new Date(dayMs(iso))
  return d.toLocaleDateString('sl-SI', { timeZone: 'UTC' })
}

/** "18. december" style, for prominent dates. */
export function formatDayLong(iso: string): string {
  return new Date(dayMs(iso)).toLocaleDateString('sl-SI', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' })
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('sl-SI', { dateStyle: 'short', timeStyle: 'short' })
}

export function ageFrom(birthYear: number, today: string): number {
  return Number(today.slice(0, 4)) - birthYear
}

export function plural(n: number, one: string, two: string, few: string, other: string): string {
  const m = Math.abs(n) % 100
  if (m === 1) return one
  if (m === 2) return two
  if (m === 3 || m === 4) return few
  return other
}

const days = (n: number) => `${n} ${plural(n, 'dan', 'dneva', 'dni', 'dni')}`

/** "1 točka", "2 točki", "3 točke", "11 točk"; decimals take "točke" ("2,5 točke"). */
export function pointsText(value: number): string {
  const r = Math.round(Math.abs(value) * 10) / 10
  const n = r.toLocaleString('sl-SI', { maximumFractionDigits: 1 })
  if (!Number.isInteger(r)) return `${n} točke`
  return `${n} ${plural(r, 'točka', 'točki', 'točke', 'točk')}`
}

// ------------------------------------------------------------------ triage list

export const STATUS_LABEL: Record<Status, string> = {
  red: 'Nujno',
  yellow: 'Za pregled',
  no_data: 'Brez podatkov',
  insufficient_data: 'Premalo sej',
  stable: 'Stabilno',
}

export type TriageTab = 'attention' | 'all' | 'no_data'

export function filterPatients(patients: PatientListItem[], tab: TriageTab): PatientListItem[] {
  if (tab === 'attention') return patients.filter((p) => p.status === 'red' || p.status === 'yellow')
  if (tab === 'no_data') return patients.filter((p) => p.status === 'no_data')
  return patients
}

export function defaultTab(patients: PatientListItem[]): TriageTab {
  return filterPatients(patients, 'attention').length > 0 ? 'attention' : 'all'
}

export function counterLine(c: { needsAttention: number; noData: number; stable: number }): string {
  const parts = [
    `${c.needsAttention} za pregled`,
    `${c.noData} brez podatkov`,
    `${c.stable} ${plural(c.stable, 'stabilen', 'stabilna', 'stabilni', 'stabilnih')}`,
  ]
  return parts.join(' · ')
}

export function nextVisitText(daysTo: number | null | undefined): string {
  if (daysTo == null) return 'ni načrtovanega pregleda'
  if (daysTo === 0) return 'naslednji pregled danes'
  if (daysTo < 0) return `pregled je zamujen ${days(-daysTo)}`
  return `naslednji pregled čez ${days(daysTo)}`
}

/** Short form for the prominent next-visit figure: "čez 30 dni", "danes", "zamujen 2 dni". */
export function visitWhen(daysTo: number | null | undefined): string {
  if (daysTo == null) return 'ni načrtovan'
  if (daysTo === 0) return 'danes'
  if (daysTo === 1) return 'jutri'
  if (daysTo < 0) return `zamujen ${days(-daysTo)}`
  return `čez ${days(daysTo)}`
}

/** Fixed windows, so a decline looks like a decline in every row (no auto-zoom). */
export const SPARK_DAYS = 21
export const GAME_SPARK_DOMAIN: [number, number] = [-20, 10]
export const RATING_DOMAIN: [number, number] = [1, 10]

export interface SparkRow {
  t: number
  v: number | null
}

/**
 * One row per day of the last SPARK_DAYS days ending `today`. Missing days are null so the line
 * breaks (a patient who stopped sending visibly ends early). Values are clamped into `domain`.
 */
export function sparkRows(points: { day: string; value?: number | null }[], today: string, domain: [number, number]): SparkRow[] {
  const end = dayMs(today)
  const start = end - (SPARK_DAYS - 1) * DAY_MS
  const byDay = new Map<number, number>()
  for (const p of points) if (p.value != null) byDay.set(dayMs(p.day), p.value)
  const rows: SparkRow[] = []
  for (let t = start; t <= end; t += DAY_MS) {
    const v = byDay.get(t)
    rows.push({ t, v: v == null ? null : Math.min(domain[1], Math.max(domain[0], v)) })
  }
  return rows
}

export function sparkValueCount(rows: SparkRow[]): number {
  return rows.filter((r) => r.v != null).length
}

// ------------------------------------------------------------------ trends

export function trendSeries(trends: TrendPoint[], metric: string): TrendPoint[] {
  return trends.filter((t) => t.metric === metric).sort((a, b) => dayMs(a.day) - dayMs(b.day))
}

export interface ChartRow {
  t: number
  day: string
  /** combined chart: points vs own baseline */
  delta?: number | null
  /** level chart: smoothed score */
  ewma?: number | null
  /** level chart: an individual session score */
  score?: number | null
  sessionId?: number
}

export function combinedRows(trends: TrendPoint[]): ChartRow[] {
  return trendSeries(trends, 'trace:all').map((p) => ({ t: dayMs(p.day), day: p.day, delta: p.delta }))
}

/** Sessions as faded dots + EWMA as the line, merged on the day axis. */
export function levelRows(level: number, sessions: SessionSummary[], trends: TrendPoint[]): ChartRow[] {
  const rows: ChartRow[] = trendSeries(trends, `trace:${level}`).map((p) => ({
    t: dayMs(p.day),
    day: p.day,
    ewma: p.ewma,
  }))
  for (const s of sessions) {
    if (s.level !== level || s.score == null) continue
    rows.push({ t: dayMs(s.day), day: s.day, score: s.score, sessionId: s.id })
  }
  return rows.sort((a, b) => a.t - b.t)
}

export function latestBaseline(trends: TrendPoint[], metric: string): number | null {
  const s = trendSeries(trends, metric).filter((p) => p.baseline != null)
  return s.length ? (s[s.length - 1].baseline as number) : null
}

export interface TrendSummary {
  delta: number | null
  nSessions: number
  baseline: number | null
  direction: TrendPoint['direction'] | null
  day: string | null
}

export function trendSummary(trends: TrendPoint[], metric: string): TrendSummary {
  const s = trendSeries(trends, metric)
  const last = s[s.length - 1]
  if (!last) return { delta: null, nSessions: 0, baseline: null, direction: null, day: null }
  return {
    delta: last.delta ?? null,
    nSessions: last.nSessions,
    baseline: latestBaseline(trends, metric),
    direction: last.direction,
    day: last.day,
  }
}

/** A change vs the patient's own baseline, in words: "11 točk pod izhodiščem". */
export function deltaWords(delta: number | null | undefined): string {
  if (delta == null) return 'ni izhodišča'
  if (Math.abs(delta) < BAND) return 'v pasu izhodišča'
  return `${pointsText(delta)} ${delta > 0 ? 'nad' : 'pod'} izhodiščem`
}

// ------------------------------------------------------------------ x axis and markers

export interface Marker {
  t: number
  kind: 'alert' | 'visit' | 'discharge'
  label: string
  severity?: string
}

export interface TimeDomain {
  start: number
  end: number
}

/** Shared by the game chart and the rating charts, so their x axes line up. */
export function timeDomain(tl: Timeline): TimeDomain {
  const ts: number[] = []
  for (const s of tl.sessions) ts.push(dayMs(s.day))
  for (const c of tl.checkins) ts.push(dayMs(c.day))
  for (const p of tl.trends) ts.push(dayMs(p.day))
  const today = dayMs(tl.today)
  const start = ts.length ? Math.min(...ts) : today - 14 * DAY_MS
  let end = today
  if (tl.nextVisitDate) {
    const nv = dayMs(tl.nextVisitDate)
    if (nv >= today && nv <= today + 14 * DAY_MS) end = nv
  }
  return { start: Math.min(start, today - DAY_MS), end: Math.max(end, start + DAY_MS) }
}

export function chartMarkers(tl: Timeline, dom: TimeDomain): Marker[] {
  const out: Marker[] = []
  for (const a of tl.alerts) {
    out.push({ t: dayMs(a.openedDay), kind: 'alert', label: 'opozorilo', severity: a.severity })
  }
  if (tl.nextVisitDate) out.push({ t: dayMs(tl.nextVisitDate), kind: 'visit', label: 'pregled' })
  out.push({ t: dayMs(tl.dischargeDate), kind: 'discharge', label: 'odpust' })
  return out.filter((m) => m.t >= dom.start && m.t <= dom.end).sort((a, b) => a.t - b.t)
}

export function dayTicks(dom: TimeDomain, maxTicks = 8): number[] {
  const n = Math.round((dom.end - dom.start) / DAY_MS)
  const step = Math.max(1, Math.ceil(n / maxTicks))
  const ticks: number[] = []
  for (let t = dom.start; t <= dom.end; t += step * DAY_MS) ticks.push(t)
  return ticks
}

// ------------------------------------------------------------------ features

export const FEATURE_LABELS: Record<string, string> = {
  mean_dev: 'Povprečen odmik od želene črte',
  // names from Primož's model (backend/models/tracer/features.py)
  dev_rms: 'Odmik od želene črte (RMS)',
  dev_mean: 'Povprečen odmik od želene črte',
  dev_p90: 'Odmik od črte (90. percentil)',
  dev_max: 'Največji odmik od črte',
  pct_outside: 'Delež izven kanala',
  lat_hf_rms: 'Drobno tresenje sledi',
  tremor_ratio: 'Delež tresenja (4–8 Hz)',
  coverage: 'Pokritost poti',
  completed: 'Dokončano',
  time_ratio: 'Delež porabljenega časa',
  prog_speed: 'Hitrost napredovanja',
  prog_speed_cv: 'Neenakomernost hitrosti',
  pause_frac: 'Delež časa v postankih',
  n_pauses: 'Število postankov',
  n_lifts: 'Dvigi prsta',
  up_frac: 'Delež časa z dvignjenim prstom',
  path_ratio: 'Dolžina sledi glede na pot',
  sparc: 'Gladkost gibanja (SPARC)',
  ldlj: 'Gladkost gibanja (LDLJ)',
  duration_s: 'Trajanje testa (s)',
  base_speed: 'Osnovna hitrost',
  corner_slowdown: 'Upočasnitev v ovinkih',
  speed_fluct: 'Nihanje hitrosti',
  pause_rate_hz: 'Pogostost postankov',
  lifts: 'Dvigi prsta',
  pause_max_s: 'Najdaljši postanek (s)',
  lateral_sd_frac: 'Bočno odstopanje',
  overshoot_frac: 'Prekoračitve',
  tremor_hz: 'Frekvenca tresenja',
  tremor_amp: 'Amplituda tresenja',
  lift_rate: 'Dvigi prsta',
  give_up_prob: 'Prekinitve',
}

export function featureLabel(key: string): string {
  return FEATURE_LABELS[key] ?? key.replace(/_/g, ' ')
}

export interface FeatureChange {
  key: string
  label: string
  level: number
  baseline: number
  recent: number
  change: number
  changePct: number | null
}

export interface FeatureComparison {
  rows: FeatureChange[]
  /** sessions used for the baseline / recent windows; empty `rows` + these counts explain why */
  nBaseline: number
  nRecent: number
}

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length

function levelSessions(sessions: SessionSummary[], level: number): SessionSummary[] {
  return sessions
    .filter((s) => s.level === level && s.completed)
    .sort((a, b) => Date.parse(a.startedAt) - Date.parse(b.startedAt))
}

/** Baseline = sessions 2-4 of the level (session 1 is practice), recent = the last 3 sessions. */
export function baselineSessions(sessions: SessionSummary[], level: number): SessionSummary[] {
  return levelSessions(sessions, level).slice(1, 4)
}

/** The baseline session shown next to a replay: the one whose score is closest to the baseline median. */
export function pickBaselineSession(sessions: SessionSummary[], level: number, excludeId?: number): SessionSummary | null {
  const base = baselineSessions(sessions, level).filter((s) => s.id !== excludeId)
  if (!base.length) return null
  const scores = base.map((s) => s.score).filter((x): x is number => x != null)
  if (!scores.length) return base[0]
  const sorted = [...scores].sort((a, b) => a - b)
  const med = sorted[Math.floor(sorted.length / 2)]
  return base.reduce((best, s) =>
    Math.abs((s.score ?? Infinity) - med) < Math.abs((best.score ?? Infinity) - med) ? s : best,
  )
}

/** The features that moved most (relative to their baseline mean). level=null: all levels, each against its own baseline. */
export function featureComparison(sessions: SessionSummary[], level: number | null, top = 3): FeatureComparison {
  const levels = level == null ? LEVELS : [level]
  const rows: FeatureChange[] = []
  let nBaseline = 0
  let nRecent = 0
  for (const lv of levels) {
    const all = levelSessions(sessions, lv)
    if (all.length < 5) continue // need 3 baseline + 3 recent without overlap (session 1 is practice)
    const base = all.slice(1, 4)
    const recent = all.slice(-3)
    nBaseline += base.length
    nRecent += recent.length
    const keys = Object.keys(base[0].features).filter((k) => recent.every((s) => k in s.features) && base.every((s) => k in s.features))
    for (const key of keys) {
      const b = mean(base.map((s) => s.features[key]))
      const r = mean(recent.map((s) => s.features[key]))
      rows.push({
        key,
        label: featureLabel(key),
        level: lv,
        baseline: b,
        recent: r,
        change: r - b,
        changePct: b !== 0 ? ((r - b) / Math.abs(b)) * 100 : null,
      })
    }
  }
  rows.sort((a, b) => Math.abs(b.changePct ?? 0) - Math.abs(a.changePct ?? 0))
  // across all levels: each feature once (on the level where it moved most), so the list says three different things
  const seen = new Set<string>()
  const distinct = level == null ? rows.filter((r) => !seen.has(r.key) && seen.add(r.key)) : rows
  return { rows: distinct.slice(0, top), nBaseline, nRecent }
}

export function formatFeature(v: number): string {
  const a = Math.abs(v)
  // small values keep two significant digits, so 0.003 does not print as "0"
  if (a > 0 && a < 0.1) return v.toLocaleString('sl-SI', { maximumSignificantDigits: 2 })
  return v.toLocaleString('sl-SI', { maximumFractionDigits: a >= 100 ? 0 : a >= 10 ? 1 : 2 })
}

export function formatPct(pct: number | null): string {
  if (pct == null) return '–'
  const r = Math.round(pct)
  return `${r > 0 ? '+' : r < 0 ? '−' : ''}${Math.abs(r)} %`
}

// ------------------------------------------------------------------ ratings (wellbeing, pain)

export const RATING_IDS = ['wellbeing', 'pain'] as const
export type RatingId = (typeof RATING_IDS)[number]

const RATING_FALLBACK: Record<RatingId, Question> = {
  wellbeing: { id: 'wellbeing', kind: 'scale', text: 'Kako se počutite danes?', shortLabel: 'Počutje', min: 1, max: 10, minLabel: 'zelo slabo', maxLabel: 'odlično', higherIsWorse: false },
  pain: { id: 'pain', kind: 'scale', text: 'Kako močna je bolečina?', shortLabel: 'Bolečina', min: 1, max: 10, minLabel: 'brez bolečine', maxLabel: 'najhujša', higherIsWorse: true },
}

/** The two ratings in a fixed order, taken from the pathway when present. */
export function ratingQuestions(questions: Question[]): Question[] {
  return RATING_IDS.map((id) => questions.find((q) => q.id === id) ?? RATING_FALLBACK[id])
}

export interface RatingSeries {
  question: Question
  points: { t: number; day: string; value: number }[]
}

export function ratingSeries(questions: Question[], checkins: Checkin[]): RatingSeries[] {
  const sorted = [...checkins].sort((a, b) => dayMs(a.day) - dayMs(b.day) || a.id - b.id)
  return ratingQuestions(questions).map((q) => ({
    question: q,
    points: sorted.filter((c) => typeof c.answers[q.id] === 'number').map((c) => ({ t: dayMs(c.day), day: c.day, value: c.answers[q.id] })),
  }))
}

export function ratingText(value: number | undefined, max = 10): string {
  if (value == null) return '–'
  return `${value.toLocaleString('sl-SI', { maximumFractionDigits: 1 })} od ${max}`
}

/** "višje je bolje" / "višje je slabše", with the end labels when the pathway has them. */
export function scaleHint(q: Question): string {
  return q.higherIsWorse ? 'višje je slabše' : 'višje je bolje'
}

// ------------------------------------------------------------------ session replay

export interface Stroke {
  id: number
  points: { x: number; y: number }[]
}

/** Raw trace series -> strokes (strokeId separates pen-up/pen-down). Coordinates are normalised 0-1. */
export function splitStrokes(series: Record<string, number[]>): Stroke[] {
  const xs = series.x ?? []
  const ys = series.y ?? []
  const ids = series.strokeId ?? []
  const n = Math.min(xs.length, ys.length)
  const strokes: Stroke[] = []
  for (let i = 0; i < n; i++) {
    const id = ids[i] ?? 0
    let s = strokes[strokes.length - 1]
    if (!s || s.id !== id) {
      s = { id, points: [] }
      strokes.push(s)
    }
    s.points.push({ x: xs[i], y: ys[i] })
  }
  return strokes
}

export function targetPoints(series: Record<string, number[]>): { x: number; y: number }[] {
  const xs = series.targetX ?? []
  const ys = series.targetY ?? []
  return xs.slice(0, ys.length).map((x, i) => ({ x, y: ys[i] }))
}

export function pointsAttr(pts: { x: number; y: number }[]): string {
  return pts.map((p) => `${p.x.toFixed(4)},${p.y.toFixed(4)}`).join(' ')
}

export function durationText(ms: number): string {
  const s = ms / 1000
  return `${s.toLocaleString('sl-SI', { maximumFractionDigits: 1 })} s`
}

// ------------------------------------------------------------------ alert evidence (defensive: evidence is free-form JSON)

export const SEVERITY_LABEL: Record<string, string> = { red: 'Nujno', yellow: 'Za pregled', grey: 'Brez podatkov' }
export const SEVERITY_STATUS: Record<string, Status> = { red: 'red', yellow: 'yellow', grey: 'no_data' }

export const RULE_LABEL: Record<string, string> = {
  trend_drop: 'Sledenje pod izhodiščem',
  subjective_drop: 'Slabše počutje ali več bolečine',
  both: 'Sledenje in počutje hkrati',
  big_drop: 'Velik padec sledenja',
  no_data: 'Ni novih podatkov',
}

export interface Trigger {
  rule: string
  severity: string
  day: string | null
  reason: string
}

const asStr = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)
const asNum = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

export function alertTriggers(a: Pick<Alert, 'evidence'>): Trigger[] {
  const raw = a.evidence?.triggers
  if (!Array.isArray(raw)) return []
  return raw
    .filter((t): t is Record<string, unknown> => typeof t === 'object' && t !== null)
    .map((t) => ({
      rule: asStr(t.rule) ?? '',
      severity: asStr(t.severity) ?? '',
      day: asStr(t.day),
      reason: asStr(t.reason) ?? '',
    }))
    .filter((t) => t.reason || t.rule)
}

export function alertDivergence(a: Pick<Alert, 'evidence'>): string | null {
  const d = a.evidence?.divergence
  if (typeof d === 'string') return asStr(d)
  if (d && typeof d === 'object') return asStr((d as Record<string, unknown>).text) ?? asStr((d as Record<string, unknown>).reason)
  return null
}

export function evidenceNumber(a: Pick<Alert, 'evidence'>, key: string): number | null {
  return asNum(a.evidence?.[key])
}

export interface Fact {
  label: string
  value: string
  /** a quieter second line, e.g. the date */
  detail?: string
}

function ratingChangeFact(kind: 'wellbeing' | 'pain', change: number): Fact | null {
  if (Math.abs(change) < 0.05) return null
  const up = change > 0
  return {
    label: kind === 'wellbeing' ? 'Počutje' : 'Bolečina',
    value: `${pointsText(change)} ${up ? 'višje' : 'nižje'} kot teden prej`,
  }
}

export function visitFact(p: Pick<PatientDetail, 'daysToNextVisit' | 'nextVisitDate'>): Fact {
  return {
    label: 'Naslednji pregled',
    value: visitWhen(p.daysToNextVisit),
    detail: p.nextVisitDate ? formatDay(p.nextVisitDate) : undefined,
  }
}

/**
 * At most two key facts for the alert box. The point is the contrast: how far the patient has
 * moved from their own baseline, and how far away the next planned visit is.
 */
export function alertFacts(
  a: Pick<Alert, 'evidence' | 'rule'>,
  p: Pick<PatientDetail, 'daysToNextVisit' | 'nextVisitDate' | 'summary'>,
  today: string,
): Fact[] {
  const facts: Fact[] = []
  if (a.rule === 'subjective_drop') {
    const w = evidenceNumber(a, 'wellbeingChange')
    const pain = evidenceNumber(a, 'painChange')
    // the bigger move, as "worse": wellbeing down or pain up
    const wf = w != null && w < 0 ? ratingChangeFact('wellbeing', w) : null
    const pf = pain != null && pain > 0 ? ratingChangeFact('pain', pain) : null
    const pick = wf && pf ? (Math.abs(w!) >= Math.abs(pain!) ? wf : pf) : (wf ?? pf)
    if (pick) facts.push(pick)
  } else if (a.rule === 'no_data') {
    const last = [p.summary.lastSessionDay, p.summary.lastCheckinDay].filter((d): d is string => !!d).sort().pop()
    if (last) {
      const ago = Math.round((dayMs(today) - dayMs(last)) / DAY_MS)
      facts.push({ label: 'Zadnji samopregled', value: ago <= 0 ? 'danes' : `pred ${days(ago)}`, detail: formatDay(last) })
    } else {
      facts.push({ label: 'Zadnji samopregled', value: 'še nobenega' })
    }
  } else {
    const delta = evidenceNumber(a, 'delta') ?? p.summary.combinedDelta
    if (delta != null) facts.push({ label: 'Sledenje', value: deltaWords(delta) })
  }
  facts.push(visitFact(p))
  return facts.slice(0, 2)
}

// ------------------------------------------------------------------ action log

export interface LogEntry {
  at: string
  kind: 'opened' | 'acknowledged' | 'closed'
  text: string
  detail?: string
}

export function assembleActionLog(alerts: Alert[], outcomes: Record<string, string>, clinicianNames: Record<string, string> = {}): LogEntry[] {
  const who = (id: string | null | undefined) => (id ? (clinicianNames[id] ?? id) : 'neznan')
  const out: LogEntry[] = []
  for (const a of alerts) {
    out.push({
      at: a.createdAt,
      kind: 'opened',
      text: `Odprto opozorilo »${SEVERITY_LABEL[a.severity] ?? a.severity}«`,
      detail: a.reason,
    })
    if (a.acknowledgedAt) {
      out.push({ at: a.acknowledgedAt, kind: 'acknowledged', text: `${who(a.acknowledgedBy)} je potrdil, da je videl opozorilo` })
    }
    if (a.closedAt) {
      out.push({
        at: a.closedAt,
        kind: 'closed',
        text: `${who(a.closedBy)} je zaprl opozorilo z izidom »${a.outcome ? (outcomes[a.outcome] ?? a.outcome) : 'brez izida'}«`,
        detail: a.note ?? undefined,
      })
    }
  }
  return out.sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
}

// ------------------------------------------------------------------ check-in history

export function checkinRows(checkins: Checkin[], limit = 14): Checkin[] {
  return [...checkins].sort((a, b) => dayMs(b.day) - dayMs(a.day) || b.id - a.id).slice(0, limit)
}
