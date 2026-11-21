// "Which patient are you": the role switch without login, top left of the patient view.
import { useNavigate } from 'react-router'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api, unwrap } from '@/client/api'
import { useAsync } from '@/lib/useAsync'
import { paths } from './paths'

export function PatientSelect({ patientId }: { patientId: string }) {
  const navigate = useNavigate()
  // Names only: nothing about alerts or status may reach the patient view.
  const { data } = useAsync(() => unwrap(api.GET('/api/patients')), [])
  const patients = [...(data?.patients ?? [])].sort((a, b) => a.name.localeCompare(b.name, 'sl'))
  return (
    <Select value={patientId} onValueChange={(id) => navigate(paths.patientHome(id))}>
      <SelectTrigger aria-label="Izbira pacienta" className="min-w-56 border-input bg-card text-base text-primary data-[size=default]:h-11">
        <SelectValue placeholder="Izberite pacienta" />
      </SelectTrigger>
      <SelectContent>
        {patients.map((p) => (
          <SelectItem key={p.id} value={p.id} className="text-base">
            {p.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
