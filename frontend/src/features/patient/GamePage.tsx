// Game host: instructions -> game component -> POST /api/sessions -> worded result.
// Phase 0 placeholder (thin slice); agent C builds the real screen.
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { api, unwrap, type SessionResult } from '@/client/api'
import { paths } from '@/app/paths'
import { GAMES } from '@/games/registry'
import type { GameResult, GameType, Hand } from '@/games/shared/types'
import { useAsync } from '@/lib/useAsync'

export function GamePage() {
  const { patientId = '', gameType = 'trace', level = '1' } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState<SessionResult>()
  const [error, setError] = useState<string>()
  const today = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  const Game = GAMES[gameType as GameType]
  if (!Game) return <p>Neznana igra.</p>
  if (!today.data) return <p>Nalagam …</p>

  async function submit(r: GameResult) {
    try {
      setResult(await unwrap(api.POST('/api/sessions', { body: { patientId, ...r } })))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  if (error) return <p className="text-red-700">{error}</p>
  if (result)
    return (
      <div className="space-y-4 text-center">
        <h1 className="text-2xl font-semibold">{result.messageTitle}</h1>
        <p>{result.messageText}</p>
        <Link to={paths.patientToday(patientId)} className="underline">
          Nazaj na Danes
        </Link>
      </div>
    )
  return (
    <Game
      config={{ gameType: gameType as GameType, level: Number(level), hand: today.data.hand as Hand, patientId }}
      onComplete={submit}
      onAbort={() => navigate(paths.patientToday(patientId))}
    />
  )
}
