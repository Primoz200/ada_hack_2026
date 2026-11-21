// Patient detail for the clinician. Phase 0 placeholder (thin slice); agent D builds the real screen.
import { useParams } from 'react-router'
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { api, unwrap } from '@/client/api'
import { useAsync } from '@/lib/useAsync'

export function ClinicianPatientPage() {
  const { patientId = '' } = useParams()
  const { data, error } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/timeline', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  if (error) return <p>{error.message}</p>
  if (!data) return <p>Nalagam …</p>
  const points = data.sessions
    .filter((s) => s.score != null)
    .map((s) => ({ t: new Date(s.startedAt).getTime(), score: s.score, level: s.level }))
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Pacient {patientId}</h1>
      <p data-testid="session-count">{points.length} sej</p>
      <div className="h-72">
        <ResponsiveContainer>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={(v: number) => new Date(v).toLocaleDateString('sl-SI')}
            />
            <YAxis dataKey="score" domain={[0, 100]} />
            <Tooltip />
            <Scatter data={points} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
