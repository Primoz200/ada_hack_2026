// Patient overview sorted by urgency. Phase 0 placeholder (thin slice); agent D builds the real screen.
import { Link } from 'react-router'
import { api, unwrap } from '@/client/api'
import { paths } from '@/app/paths'
import { useAsync } from '@/lib/useAsync'

export function TriagePage() {
  const { data, error } = useAsync(() => unwrap(api.GET('/api/patients')), [])
  if (error) return <p>{error.message}</p>
  if (!data) return <p>Nalagam …</p>
  return (
    <ul className="space-y-2">
      {data.patients.map((p) => (
        <li key={p.id}>
          <Link to={paths.clinicianPatient(p.id)} className="underline">
            {p.name}
          </Link>{' '}
          · {p.pathwayName} · {p.reason}
        </li>
      ))}
    </ul>
  )
}
