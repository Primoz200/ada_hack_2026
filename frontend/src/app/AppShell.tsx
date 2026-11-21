// One shell for both views. White header over the blue-grey page, like the public e-health portals.
// Patient view: patient selector top left, switch to the clinician view top right. Clinician view: the mirror.
import { Stethoscope, UserRound } from 'lucide-react'
import { useEffect } from 'react'
import { Link, Outlet, useParams } from 'react-router'
import { lastPatient, paths, rememberPatient } from './paths'
import { PatientSelect } from './PatientSelect'
import { PrototypeBanner } from './PrototypeBanner'
import { Wordmark } from './Wordmark'

const switchLink =
  'inline-flex h-11 items-center gap-2 rounded-lg border border-input bg-card px-4 text-base font-medium text-primary transition-colors hover:bg-accent'

function Frame({ left, right }: { left: React.ReactNode; right: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <PrototypeBanner />
      <header className="bg-card">
        <div className="mx-auto flex h-20 max-w-[1240px] items-center justify-between gap-4 px-6">
          <div className="flex min-w-0 items-center gap-6">{left}</div>
          <nav className="flex items-center gap-3">{right}</nav>
        </div>
      </header>
      {/* the header's white fades into the page, as on the portal */}
      <div className="h-16 bg-gradient-to-b from-card to-background" aria-hidden />
      <main className="mx-auto -mt-8 w-full max-w-[1240px] flex-1 px-6 pb-16">
        <Outlet />
      </main>
    </div>
  )
}

export function PatientShell() {
  const { patientId = '' } = useParams()
  useEffect(() => {
    if (patientId) rememberPatient(patientId)
  }, [patientId])
  return (
    <Frame
      left={
        <>
          <Wordmark to={paths.patientHome(patientId)} />
          <PatientSelect patientId={patientId} />
        </>
      }
      right={
        <Link to={paths.clinician} className={switchLink}>
          <Stethoscope className="size-5" aria-hidden />
          Pogled zdravnika
        </Link>
      }
    />
  )
}

export function ClinicianShell() {
  const back = lastPatient()
  return (
    <Frame
      left={
        <>
          <Wordmark to={paths.clinician} />
          <span className="hidden text-base text-muted-foreground md:inline">Pregled za zdravnika</span>
        </>
      }
      right={
        <Link to={back ? paths.patientHome(back) : paths.home} className={switchLink}>
          <UserRound className="size-5" aria-hidden />
          Pogled pacienta
        </Link>
      }
    />
  )
}
