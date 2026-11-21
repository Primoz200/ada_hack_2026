// Game host: instructions -> game component -> POST /api/sessions -> worded result.
import { useRef, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { useNavigate, useParams } from 'react-router'
import { api, unwrap, type SessionResult, type Today } from '@/client/api'
import { paths } from '@/app/paths'
import { Button } from '@/components/ui/button'
import { GAMES } from '@/games/registry'
import type { GameResult, GameType, Hand } from '@/games/shared/types'
import { getLevel } from '@/games/trace/levels'
import { LevelPreview } from '@/games/trace/LevelPreview'
import { emptyAbortResult } from '@/games/trace/result'
import { useAsync } from '@/lib/useAsync'
import { BackBar, ErrorBlock, handLabel, levelLabel, LoadingBlock } from './shared'

type Phase = 'intro' | 'playing' | 'sending' | 'result'

function nextTask(today: Today | undefined, gameType: string, level: number) {
  return today?.tasks.find((t) => t.kind === 'game' && t.gameType === gameType && t.level !== level && !t.done)
}

export function GamePage() {
  const { patientId = '', gameType = 'trace', level = '1' } = useParams()
  const levelNo = Number(level)
  const navigate = useNavigate()
  const todayPath = paths.patientToday(patientId)
  const [phase, setPhase] = useState<Phase>('intro')
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<SessionResult>()
  const [error, setError] = useState<string>()
  const [refreshed, setRefreshed] = useState<Today>()
  // The result that is being / has to be sent: kept so a network error never loses the trace.
  const pending = useRef<GameResult | undefined>(undefined)
  const today = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )

  const Game = GAMES[gameType as GameType]
  if (!Game) return <p>Neznana igra.</p>
  if (today.error && !today.data) return <ErrorBlock message={today.error.message} onRetry={today.reload} />
  if (!today.data) return <LoadingBlock />
  const hand = today.data.hand as Hand
  const config = { gameType: gameType as GameType, level: levelNo, hand, patientId }

  async function send() {
    const r = pending.current
    if (!r) return
    setPhase('sending')
    setError(undefined)
    try {
      const res = await unwrap(api.POST('/api/sessions', { body: { patientId, ...r } }))
      pending.current = undefined
      if (r.abortReason === 'cannot_today') {
        navigate(todayPath)
        return
      }
      setResult(res)
      setPhase('result')
      // best effort: which level is next
      unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } }))
        .then(setRefreshed)
        .catch(() => undefined)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function onComplete(r: GameResult) {
    pending.current = r
    void send()
  }

  function cannotTodayBeforeStart() {
    const lvl = getLevel(levelNo)
    pending.current =
      lvl && gameType === 'trace'
        ? emptyAbortResult(config, lvl)
        : {
            gameType: config.gameType,
            level: levelNo,
            hand,
            startedAt: new Date().toISOString(),
            durationMs: 0,
            completed: false,
            abortReason: 'cannot_today',
            series: {},
            clientMeta: {
              inputDevice: 'touch',
              canvasW: 0,
              canvasH: 0,
              devicePixelRatio: window.devicePixelRatio || 1,
              userAgent: navigator.userAgent,
            },
          }
    void send()
  }

  // --- sending (and network error with retry)
  if (phase === 'sending') {
    if (error)
      return (
        <div className="space-y-4">
          <ErrorBlock message={`Rezultata ni bilo mogoče poslati. Vaša sled je shranjena. ${error}`} onRetry={() => void send()} />
          <Button variant="outline" className="h-14 w-full text-lg" onClick={() => navigate(todayPath)}>
            Nazaj na Danes
          </Button>
        </div>
      )
    return (
      <p role="status" className="py-10 text-center text-xl">
        Pošiljam rezultat …
      </p>
    )
  }

  // --- worded result
  if (phase === 'result' && result) {
    const next = nextTask(refreshed ?? today.data, gameType, levelNo)
    return (
      <div className="space-y-5">
        <div role="status" className="space-y-3 rounded-xl border p-5">
          <h1 className="text-2xl font-semibold">{result.messageTitle}</h1>
          <p>{result.messageText}</p>
          {result.personalBest ? (
            <p className="flex items-center gap-2 font-medium">
              <Sparkles className="size-5" aria-hidden /> Nov osebni rekord. Čestitamo!
            </p>
          ) : null}
        </div>
        {result.offerRetry ? (
          <Button
            variant="outline"
            className="h-14 w-full text-lg"
            onClick={() => {
              setResult(undefined)
              setAttempt((a) => a + 1)
              setPhase('playing')
            }}
          >
            Poskusi znova
          </Button>
        ) : null}
        {next ? (
          <Button
            className="h-14 w-full text-lg"
            onClick={() => {
              setResult(undefined)
              setPhase('intro')
              navigate(paths.patientGame(patientId, next.gameType ?? 'trace', next.level ?? 1))
            }}
          >
            Naprej: {gameType === 'trace' ? levelLabel(next.level) : next.title}
          </Button>
        ) : null}
        <Button variant={next ? 'ghost' : 'default'} className="h-14 w-full text-lg" onClick={() => navigate(todayPath)}>
          Nazaj na Danes
        </Button>
      </div>
    )
  }

  // --- the game itself
  if (phase === 'playing')
    return <Game key={attempt} config={config} onComplete={onComplete} onAbort={() => setPhase('intro')} />

  // --- instructions
  const lvl = gameType === 'trace' ? getLevel(levelNo) : undefined
  return (
    <div className="space-y-5">
      <BackBar to={todayPath} />
      <h1 className="text-2xl font-semibold">
        {gameType === 'trace' ? `Sledi poti: ${levelLabel(levelNo)}` : `Stopnja ${levelNo}`}
      </h1>
      {gameType === 'trace' ? <LevelPreview level={levelNo} className="mx-auto w-full max-w-72" /> : null}
      <div className="space-y-3">
        <p>Sledite poti čim natančneje, v svojem tempu.</p>
        <p>
          Uporabite roko: <strong>{handLabel(hand)}</strong>. Začnite pri označeni začetni točki in
          držite prst na zaslonu, dokler ne pridete do konca.
        </p>
        {lvl ? <p className="text-muted-foreground">Na voljo imate {lvl.timeLimitS} sekund.</p> : null}
      </div>
      <Button className="h-16 w-full text-xl" onClick={() => setPhase('playing')}>
        Začni
      </Button>
      <Button variant="outline" className="h-14 w-full text-lg" onClick={cannotTodayBeforeStart}>
        Danes ne morem
      </Button>
    </div>
  )
}
