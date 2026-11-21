// Role switch without login: pick a patient (phone view) or the clinician view.
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { api, unwrap } from '@/client/api'
import { useAsync } from '@/lib/useAsync'
import { paths } from './paths'
import { PrototypeBanner } from './PrototypeBanner'

export function RoleSelectPage() {
  const { data, error, loading } = useAsync(() => unwrap(api.GET('/api/patients')), [])
  return (
    <div className="min-h-dvh">
      <PrototypeBanner />
      <div className="mx-auto max-w-md space-y-6 px-4 py-8">
        <h1 className="text-2xl font-semibold">Okrevanje doma</h1>
        <section className="space-y-3">
          <h2 className="text-lg font-medium">Zdravnik</h2>
          <Button asChild size="lg" className="h-12 w-full">
            <Link to={paths.clinician}>Odpri pregled pacientov</Link>
          </Button>
        </section>
        <section className="space-y-3">
          <h2 className="text-lg font-medium">Pacient</h2>
          {loading && <p>Nalagam …</p>}
          {error && <p className="text-red-700">Strežnik ni dosegljiv: {error.message}</p>}
          {data?.patients.map((p) => (
            <Button key={p.id} asChild variant="outline" size="lg" className="h-12 w-full justify-between">
              <Link to={paths.patientToday(p.id)}>
                <span>{p.name}</span>
                <span className="text-sm text-muted-foreground">{p.pathwayName}</span>
              </Link>
            </Button>
          ))}
        </section>
      </div>
    </div>
  )
}
