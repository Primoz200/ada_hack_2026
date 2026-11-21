// "Danes": today's tasks. Phase 0 placeholder (thin slice); agent C builds the real screen.
import { Link, useParams } from 'react-router'
import { Button } from '@/components/ui/button'
import { api, unwrap } from '@/client/api'
import { paths } from '@/app/paths'
import { useAsync } from '@/lib/useAsync'

export function TodayPage() {
  const { patientId = '' } = useParams()
  const { data, error } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  if (error) return <p>{error.message}</p>
  if (!data) return <p>Nalagam …</p>
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Pozdravljeni, {data.name.split(' ')[0]}</h1>
      {data.tasks.map((t) => (
        <Button key={t.id} asChild variant={t.done ? 'secondary' : 'default'} className="h-14 w-full text-lg">
          <Link
            to={
              t.kind === 'checkin'
                ? paths.patientCheckin(patientId)
                : paths.patientGame(patientId, t.gameType ?? 'trace', t.level ?? 1)
            }
          >
            {t.title}
            {t.level ? ` (${t.level})` : ''} {t.done ? '✓' : ''}
          </Link>
        </Button>
      ))}
      <Link to={paths.patientProgress(patientId)} className="block text-center underline">
        Moj napredek
      </Link>
    </div>
  )
}
