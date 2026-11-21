// "/" opens the patient view: the last selected patient, else the default demo patient.
import { Navigate } from 'react-router'
import { api, unwrap } from '@/client/api'
import { useAsync } from '@/lib/useAsync'
import { lastPatient, paths } from './paths'

export function RootRedirect() {
  const remembered = lastPatient()
  const { data, error } = useAsync(() => unwrap(api.GET('/api/meta')), [])
  if (remembered) return <Navigate to={paths.patientHome(remembered)} replace />
  if (error) return <p className="p-8 text-center">Strežnik ni dosegljiv: {error.message}</p>
  if (!data) return null
  return <Navigate to={paths.patientHome(data.defaultPatientId)} replace />
}
