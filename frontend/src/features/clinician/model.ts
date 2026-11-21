// Pure data shaping for the clinician screens (no React, no fetching). Tested in model.test.ts.
import type { Alert, Checkin, PatientDetail, PatientListItem, Question, SessionSummary, Timeline, TrendPoint } from '@/client/api'

export const DAY_MS = 86_400_000
export const BAND = 5 // "pas izhodišča": ±5 points
export const ALERT_THRESHOLD = -10 // "prag opozorila"

export type Status = PatientListItem['status']
export type Level = 1 | 2 | 3
export const LEVELS: Level[] = [1, 2, 3]

// ------------------------------------------------------------------ measurements (games)

/** Each game is its own measurement with its own baseline and trend; they are never mixed. */
export type Game = SessionSummary['gameType']
export const GAMES: Game[] = ['trace', 'camera']
export const GAME_TITLE: Record<Game, string> = { trace: 'Sledenje', camera: 'Vaje s kamero' }
export const GAME_LEVEL_NAMES: Record<Game, Record<number, string>> = {
  trace: { 1: 'Ravna črta', 2: 'Krog', 3: 'Labirint' },
  camera: { 1: 'Dlan', 2: 'Roke v stran', 3: 'Dvig rok' },
}
/** Tracing level names (kept for existing callers). */
export const LEVEL_NAMES = GAME_LEVEL_NAMES.trace

export function levelName(game: Game, level: number): string {
  return GAME_LEVEL_NAMES[game][level] ?? `stopnja ${level}`
}

export function gameSessions(sessions: SessionSummary[], game: Game): SessionSummary[] {
  return sessions.filter((s) => s.gameType === game)
}

/** Camera capture was too poor to score: stored and shown, never counted. */
export function isPoorQuality(s: Pick<SessionSummary, 'qualityOk'>): boolean {
  return s.qualityOk === false
}

/** Sessions that feed the trend and the feature table. */
export function countingSessions(sessions: SessionSummary[], game: Game): SessionSummary[] {
  return gameSessions(sessions, game).filter((s) => s.completed && !isPoorQuality(s))
}

export function hasGameData(tl: Pick<Timeline, 'sessions' | 'trends'>, game: Game): boolean {
  return tl.sessions.some((s) => s.gameType === game) || tl.trends.some((t) => t.metric.startsWith(`${game}:`))
}

export function gameMetric(game: Game, level: number | 'all'): string {
  return `${game}:${level}`
}

/** The newest session's model / rules version for a game, for the model info card. */
export function latestModelVersion(sessions: SessionSummary[], game: Game): string | null {
  const s = gameSessions(sessions, game)
    .filter((x) => x.modelVersion)
    .sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt))[0]
  return s?.modelVersion ?? null
}

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
export const GAME_SPARK_DOMAIN: [number, number] = [-20, 6]
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
  /** a session with poor capture quality (not counted): drawn hollow at this height */
  poor?: number | null
  sessionId?: number
}

/** Height of a scoreless poor-quality session on the 0-100 level axis: a lane at the bottom, not a result. */
export const POOR_LANE = 4

function poorRows(sessions: SessionSummary[], game: Game, level: number | null): ChartRow[] {
  return gameSessions(sessions, game)
    .filter((s) => isPoorQuality(s) && (level == null || s.level === level))
    .map((s) => ({ t: dayMs(s.day), day: s.day, poor: s.score ?? POOR_LANE, sessionId: s.id }))
}

/** The combined trend of one game; its poor-quality sessions come along so the chart can show them. */
export function combinedRows(trends: TrendPoint[], game: Game = 'trace', sessions: SessionSummary[] = []): ChartRow[] {
  const rows: ChartRow[] = trendSeries(trends, gameMetric(game, 'all')).map((p) => ({ t: dayMs(p.day), day: p.day, delta: p.delta }))
  return [...rows, ...poorRows(sessions, game, null)].sort((a, b) => a.t - b.t)
}

/** Sessions as faded dots + EWMA as the line, merged on the day axis. Only the given game's sessions. */
export function levelRows(level: number, sessions: SessionSummary[], trends: TrendPoint[], game: Game = 'trace'): ChartRow[] {
  const rows: ChartRow[] = trendSeries(trends, gameMetric(game, level)).map((p) => ({
    t: dayMs(p.day),
    day: p.day,
    ewma: p.ewma,
  }))
  for (const s of gameSessions(sessions, game)) {
    if (s.level !== level || s.score == null || isPoorQuality(s)) continue
    rows.push({ t: dayMs(s.day), day: s.day, score: s.score, sessionId: s.id })
  }
  return [...rows, ...poorRows(sessions, game, level)].sort((a, b) => a.t - b.t)
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

/**
 * Camera exercises (backend/models/camera/scoring.py: `features`, plus the score `breakdown` as `part_*`).
 * Hand: openness = fingertip-wrist distance / palm length. Arms: shoulder angle in degrees (level 2)
 * or wrist height above the shoulder in shoulder widths (level 3).
 */
export const CAMERA_FEATURE_LABELS: Record<string, string> = {
  open_level: 'Odpiranje dlani',
  fist_level: 'Stisk v pest',
  open_range: 'Razpon odpiranja dlani',
  open_range_2d: 'Razpon odpiranja (2D)',
  n_reps: 'Ponovitve',
  timing_lag_ms: 'Zamik za piskom (ms)',
  timing_jitter_ms: 'Nihanje ritma (ms)',
  top_level: 'Doseg dviga',
  rest_level: 'Položaj v mirovanju',
  lean_deg: 'Nagib trupa (°)',
  hike: 'Dvig rame',
  symmetry: 'Simetrija rok',
  top_visibility: 'Vidnost zapestja zgoraj',
  fps: 'Sličice na sekundo',
  detect_frac: 'Delež zaznanih sličic',
  visibility: 'Vidnost točk',
  quality_ok: 'Kakovost zajema',
  part_position: 'Delež zdravega giba',
  part_open: 'Delež zdravega odpiranja',
  part_close: 'Delež zdravega stiska',
  part_reps: 'Delež opravljenih ponovitev',
  part_lean_penalty: 'Odbitek za nagib trupa',
  part_hike_penalty: 'Odbitek za dvig rame',
}

const CAMERA_LEVEL_LABELS: Record<number, Record<string, string>> = {
  2: { top_level: 'Kot odmika roke (°)', rest_level: 'Kot roke v mirovanju (°)' },
  3: { top_level: 'Višina zapestja nad ramo', rest_level: 'Zapestje v mirovanju' },
}

/** Camera features that describe the movement; capture-quality and timing values are information only. */
export const CAMERA_TABLE_FEATURES = [
  'open_level',
  'fist_level',
  'open_range',
  'n_reps',
  'top_level',
  'lean_deg',
  'hike',
  'part_position',
  'part_open',
  'part_close',
  'part_reps',
]

export function featureLabel(key: string, game: Game = 'trace', level?: number): string {
  if (game === 'camera') {
    return (level != null ? CAMERA_LEVEL_LABELS[level]?.[key] : undefined) ?? CAMERA_FEATURE_LABELS[key] ?? key.replace(/_/g, ' ')
  }
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

/**
 * The features that moved most (relative to their baseline mean). level=null: all levels, each against its own baseline.
 * Only the given game's counted sessions are used (poor-quality camera sessions are left out).
 */
export function featureComparison(sessions: SessionSummary[], level: number | null, top = 3, game: Game = 'trace'): FeatureComparison {
  const levels = level == null ? LEVELS : [level]
  const counted = countingSessions(sessions, game)
  const allowed = game === 'camera' ? new Set(CAMERA_TABLE_FEATURES) : null
  const rows: FeatureChange[] = []
  let nBaseline = 0
  let nRecent = 0
  for (const lv of levels) {
    const all = levelSessions(counted, lv)
    if (all.length < 5) continue // need 3 baseline + 3 recent without overlap (session 1 is practice)
    const base = all.slice(1, 4)
    const recent = all.slice(-3)
    nBaseline += base.length
    nRecent += recent.length
    const keys = Object.keys(base[0].features).filter(
      (k) => (!allowed || allowed.has(k)) && recent.every((s) => k in s.features) && base.every((s) => k in s.features),
    )
    for (const key of keys) {
      const b = mean(base.map((s) => s.features[key]))
      const r = mean(recent.map((s) => s.features[key]))
      rows.push({
        key,
        label: featureLabel(key, game, lv),
        level: lv,
        baseline: b,
        recent: r,
        change: r - b,
        changePct: b !== 0 ? ((r - b) / Math.abs(b)) * 100 : null,
      })
    }
  }
  rows.sort((a, b) => Math.abs(b.changePct ?? 0) - Math.abs(a.changePct ?? 0))
  // across all levels: each feature once (on the level where it moved most), so the list says three different things.
  // By label, not key: the camera's top_level is an angle on one exercise and a height on another.
  const seen = new Set<string>()
  const distinct = level == null ? rows.filter((r) => !seen.has(r.label) && seen.add(r.label)) : rows
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

// ------------------------------------------------------------------ camera sessions in words

export function qualityText(s: Pick<SessionSummary, 'qualityOk'>): string {
  if (s.qualityOk === false) return 'slab'
  if (s.qualityOk === true) return 'dober'
  return '–'
}

const sharePct = (v: number) => `${Math.round(Math.min(1, Math.max(0, v)) * 100)} %`

/** "Ponovitve": the count, and whether all expected ones were done (part_reps is the share). */
function repsWords(f: Record<string, number>): string | null {
  const n = f.n_reps
  const part = f.part_reps
  if (n == null && part == null) return null
  if (n == null) return `${sharePct(part)} predvidenih`
  if (part == null) return String(Math.round(n))
  return part >= 0.995 ? `${Math.round(n)}, vse predvidene` : `${Math.round(n)} (${sharePct(part)} predvidenih)`
}

function penaltyWords(penalty: number | undefined, raw: number | undefined, unit: string): string | null {
  if (penalty != null) return penalty > 0.005 ? `odbitek ${sharePct(penalty)}` : 'kot pri zdravem gibu'
  if (raw != null) return `${formatFeature(raw)}${unit}`
  return null
}

/**
 * The 3-4 things a clinician wants to know about one camera session, in words, from whichever
 * features are present (seeded sessions carry only a few). Poor capture is said first.
 */
export function cameraSessionFacts(s: Pick<SessionSummary, 'level' | 'features' | 'qualityOk'>, max = 4): Fact[] {
  const f = s.features ?? {}
  const out: Fact[] = []
  const said = new Set<string>() // feature keys already put into words
  const add = (label: string, value: string | null, keys: string[]) => {
    if (value == null || out.length >= max) return
    out.push({ label, value })
    for (const k of keys) said.add(k)
  }
  const healthy = (v: number | undefined) => (v != null ? `${sharePct(v)} zdravega giba` : null)
  if (isPoorQuality(s)) {
    const parts = [
      f.detect_frac != null ? `zaznanih ${sharePct(f.detect_frac)} sličic` : null,
      f.fps != null ? `${formatFeature(f.fps)} sličic na sekundo` : null,
    ].filter(Boolean)
    add('Kakovost zajema', `slaba${parts.length ? ` (${parts.join(', ')})` : ''}, seja ne šteje v trend`, [])
  }
  if (s.level === 1) {
    add('Odpiranje dlani', healthy(f.part_open), ['part_open'])
    add('Stisk v pest', healthy(f.part_close), ['part_close'])
    if (f.part_open == null && f.part_close == null) add('Doseženi gib', healthy(f.part_position), ['part_position'])
    add('Ponovitve', repsWords(f), ['n_reps', 'part_reps'])
  } else {
    add(s.level === 2 ? 'Odmik roke' : 'Dvig rok', healthy(f.part_position), ['part_position'])
    add('Ponovitve', repsWords(f), ['n_reps', 'part_reps'])
    add('Nagib trupa', penaltyWords(f.part_lean_penalty, f.lean_deg, '°'), ['part_lean_penalty', 'lean_deg'])
    add('Dvig rame', penaltyWords(f.part_hike_penalty, undefined, ''), ['part_hike_penalty'])
  }
  // sparse sessions (the demo seed stores only a few features): top up to three with the raw movement values
  for (const key of CAMERA_TABLE_FEATURES) {
    if (out.length >= Math.min(3, max)) break
    const label = featureLabel(key, 'camera', s.level)
    if (f[key] != null && !said.has(key) && !out.some((x) => x.label === label)) add(label, formatFeature(f[key]), [key])
  }
  return out
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

export type Series = Record<string, (number | null)[]>

/** Raw trace series -> strokes (strokeId separates pen-up/pen-down). Coordinates are normalised 0-1; null samples are skipped. */
export function splitStrokes(series: Series): Stroke[] {
  const xs = series.x ?? []
  const ys = series.y ?? []
  const ids = series.strokeId ?? []
  const n = Math.min(xs.length, ys.length)
  const strokes: Stroke[] = []
  for (let i = 0; i < n; i++) {
    const x = xs[i]
    const y = ys[i]
    if (x == null || y == null) continue
    const id = ids[i] ?? 0
    let s = strokes[strokes.length - 1]
    if (!s || s.id !== id) {
      s = { id, points: [] }
      strokes.push(s)
    }
    s.points.push({ x, y })
  }
  return strokes
}

export function targetPoints(series: Series): { x: number; y: number }[] {
  const xs = series.targetX ?? []
  const ys = series.targetY ?? []
  const out: { x: number; y: number }[] = []
  for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
    const x = xs[i]
    const y = ys[i]
    if (x != null && y != null) out.push({ x, y })
  }
  return out
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

/** Game-specific names of the trend rules (the rules are evaluated per game). */
const CAMERA_RULE_LABEL: Record<string, string> = {
  trend_drop: 'Vaje s kamero pod izhodiščem',
  both: 'Vaje s kamero in počutje hkrati',
  big_drop: 'Velik padec pri vajah s kamero',
}

export function ruleLabel(rule: string, game: Game | null): string | undefined {
  return (game === 'camera' ? CAMERA_RULE_LABEL[rule] : undefined) ?? RULE_LABEL[rule]
}

export interface Trigger {
  rule: string
  severity: string
  day: string | null
  reason: string
  /** which measurement the trigger is about; null for ratings and missing data */
  game: Game | null
}

const asStr = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)
const asNum = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const asGame = (v: unknown): Game | null => (v === 'trace' || v === 'camera' ? v : null)

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
      game: asGame(t.game),
    }))
    .filter((t) => t.reason || t.rule)
}

export interface GameDrop {
  game: Game
  delta: number
}

/** `evidence.games`: the games currently below baseline, tracing first. Empty when absent or malformed. */
export function alertGames(a: Pick<Alert, 'evidence'>): GameDrop[] {
  const g = a.evidence?.games
  if (!g || typeof g !== 'object' || Array.isArray(g)) return []
  const out: GameDrop[] = []
  for (const game of GAMES) {
    const entry = (g as Record<string, unknown>)[game]
    const delta = entry && typeof entry === 'object' ? asNum((entry as Record<string, unknown>).delta) : asNum(entry)
    if (delta != null) out.push({ game, delta })
  }
  return out
}

/** The measurements an alert is about: from `evidence.games`, else from the triggers' `game`. */
export function alertGameSet(a: Pick<Alert, 'evidence'>): Game[] {
  const fromGames = alertGames(a).map((g) => g.game)
  if (fromGames.length) return fromGames
  const fromTriggers = new Set(alertTriggers(a).map((t) => t.game).filter((g): g is Game => g != null))
  return GAMES.filter((g) => fromTriggers.has(g))
}

/**
 * Which measurement the patient page opens on: the camera when the open alert is about the camera
 * only; tracing otherwise (also when both games are dropping, tracing being the primary measurement).
 */
export function defaultMeasurement(alert: Pick<Alert, 'evidence'> | null | undefined, hasCamera: boolean): Game {
  if (!hasCamera || !alert) return 'trace'
  const games = alertGameSet(alert)
  return games.length === 1 && games[0] === 'camera' ? 'camera' : 'trace'
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
 * The key facts for the alert box. The point is the contrast: how far the patient has moved from
 * their own baseline, and how far away the next planned visit is. With `evidence.games`, one fact
 * per dropping measurement (at most two) plus the visit; otherwise at most two facts.
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
    const games = alertGames(a)
    if (games.length) {
      for (const g of games.slice(0, 2)) facts.push({ label: GAME_TITLE[g.game], value: deltaWords(g.delta) })
      facts.push(visitFact(p))
      return facts
    }
    // no per-game evidence: the triggers may still say which game it is; combinedDelta is about tracing only
    const set = alertGameSet(a)
    const game: Game = set.length === 1 ? set[0] : 'trace'
    const delta = evidenceNumber(a, 'delta') ?? (game === 'trace' ? p.summary.combinedDelta : null)
    if (delta != null) facts.push({ label: GAME_TITLE[game], value: deltaWords(delta) })
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
