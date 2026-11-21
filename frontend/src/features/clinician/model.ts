// Pure data shaping for the clinician screens (no React, no fetching). Tested in model.test.ts.
import type {
  Alert,
  Checkin,
  Message,
  PatientListItem,
  Question,
  SessionSummary,
  Timeline,
  TrendPoint,
} from '@/client/api'

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

export function nextVisitText(days: number | null | undefined): string {
  if (days == null) return 'ni načrtovanega pregleda'
  if (days === 0) return 'naslednji pregled danes'
  if (days < 0) return `pregled je zamujen ${-days} ${plural(-days, 'dan', 'dneva', 'dni', 'dni')}`
  return `naslednji pregled čez ${days} ${plural(days, 'dan', 'dneva', 'dni', 'dni')}`
}

export function sparkRows(p: PatientListItem): { t: number; v: number | null }[] {
  return p.sparkline.map((s) => ({ t: dayMs(s.day), v: s.value ?? null }))
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

export function deltaWords(delta: number | null): string {
  if (delta == null) return 'ni izhodišča'
  const r = Math.round(delta)
  if (Math.abs(delta) < BAND) return `v pasu izhodišča (${r > 0 ? '+' : ''}${r} točk)`
  return `${r > 0 ? '+' : '−'}${Math.abs(r)} točk ${r > 0 ? 'nad' : 'pod'} izhodiščem`
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

/** Shared by the game chart and the symptom charts, so their x axes line up. */
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
  const days = Math.round((dom.end - dom.start) / DAY_MS)
  const step = Math.max(1, Math.ceil(days / maxTicks))
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
  return { rows: rows.slice(0, top), nBaseline, nRecent }
}

export function formatFeature(v: number): string {
  const a = Math.abs(v)
  return v.toLocaleString('sl-SI', { maximumFractionDigits: a >= 100 ? 0 : a >= 10 ? 1 : 2 })
}

// ------------------------------------------------------------------ symptoms

export const CONCERN_LABEL: Record<string, string> = { none: 'ne', little: 'malo', call: 'želi klic' }
export const ANSWERED_BY_LABEL: Record<string, string> = { self: 'sam', assisted: 's pomočjo', relative: 'svojec' }

export interface SymptomSeries {
  question: Question
  points: { t: number; day: string; value: number }[]
}

export function symptomSeries(questions: Question[], checkins: Checkin[]): SymptomSeries[] {
  const sorted = [...checkins].sort((a, b) => dayMs(a.day) - dayMs(b.day))
  return questions.map((q) => ({
    question: q,
    points: sorted.filter((c) => q.id in c.answers).map((c) => ({ t: dayMs(c.day), day: c.day, value: c.answers[q.id] })),
  }))
}

export function concernPoints(checkins: Checkin[]): { t: number; day: string; concern: 'little' | 'call'; level: 1 | 2 }[] {
  return checkins
    .filter((c) => c.concern === 'little' || c.concern === 'call')
    .map((c) => ({ t: dayMs(c.day), day: c.day, concern: c.concern as 'little' | 'call', level: (c.concern === 'call' ? 2 : 1) as 1 | 2 }))
    .sort((a, b) => a.t - b.t)
}

export function warningDays(checkins: Checkin[]): { t: number; day: string; signs: string[] }[] {
  return checkins
    .filter((c) => c.warningSigns.length > 0)
    .map((c) => ({ t: dayMs(c.day), day: c.day, signs: c.warningSigns }))
    .sort((a, b) => a.t - b.t)
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

export interface Trigger {
  rule: string
  severity: string
  day: string | null
  reason: string
}

const asStr = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)

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
}

export function alertConcernText(a: Pick<Alert, 'evidence'>): string | null {
  return asStr(a.evidence?.concernText)
}

export function alertDivergence(a: Pick<Alert, 'evidence'>): string | null {
  const d = a.evidence?.divergence
  if (typeof d === 'string') return asStr(d)
  if (d && typeof d === 'object') return asStr((d as Record<string, unknown>).text) ?? asStr((d as Record<string, unknown>).reason)
  return null
}

export const SEVERITY_LABEL: Record<string, string> = { red: 'Nujno', yellow: 'Za pregled', grey: 'Brez podatkov' }

// ------------------------------------------------------------------ action log

export interface LogEntry {
  at: string
  kind: 'opened' | 'acknowledged' | 'closed' | 'message'
  text: string
  detail?: string
}

export function assembleActionLog(
  alerts: Alert[],
  messages: Message[],
  outcomes: Record<string, string>,
  clinicianNames: Record<string, string> = {},
): LogEntry[] {
  const who = (id: string | null | undefined) => (id ? (clinicianNames[id] ?? id) : 'neznan')
  const out: LogEntry[] = []
  for (const a of alerts) {
    out.push({
      at: a.createdAt,
      kind: 'opened',
      text: `Odprto opozorilo (${SEVERITY_LABEL[a.severity] ?? a.severity}): ${a.reason}`,
    })
    if (a.acknowledgedAt) {
      out.push({ at: a.acknowledgedAt, kind: 'acknowledged', text: `Potrdil ${who(a.acknowledgedBy)}, da je videl opozorilo` })
    }
    if (a.closedAt) {
      out.push({
        at: a.closedAt,
        kind: 'closed',
        text: `Zaprl ${who(a.closedBy)} z izidom: ${a.outcome ? (outcomes[a.outcome] ?? a.outcome) : 'brez izida'}`,
        detail: a.note ?? undefined,
      })
    }
  }
  for (const m of messages) {
    out.push({
      at: m.createdAt,
      kind: 'message',
      text: m.direction === 'to_patient' ? `Sporočilo pacientu${m.author ? ` (${who(m.author)})` : ''}` : 'Sistemsko sporočilo pacientu',
      detail: m.text,
    })
  }
  return out.sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
}

// ------------------------------------------------------------------ check-in history

export const QUESTION_SHORT: Record<string, string> = {
  arm_function: 'Funkcija roke',
  fatigue: 'Utrujenost',
  fall: 'Padec',
  pain: 'Bolečina',
  tingling: 'Mravljinčenje',
  night_wakings: 'Nočno zbujanje',
}

export function questionLabel(q: Pick<Question, 'id' | 'text'>): string {
  return QUESTION_SHORT[q.id] ?? q.text
}

export function formatAnswer(q: Question, value: number): string {
  if (q.kind === 'yes_no') return value >= 1 ? 'da' : 'ne'
  return `${value}/${q.max}`
}
