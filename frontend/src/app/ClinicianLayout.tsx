// Desktop shell for the clinician part.
import { Link, Outlet } from 'react-router'
import { paths } from './paths'
import { PrototypeBanner } from './PrototypeBanner'

export function ClinicianLayout() {
  return (
    <div className="min-h-dvh bg-background">
      <PrototypeBanner />
      <header className="flex items-center justify-between border-b px-6 py-3">
        <Link to={paths.clinician} className="text-lg font-semibold">
          Okrevanje doma · pregled pacientov
        </Link>
        <Link to={paths.home} className="text-sm underline">
          Zamenjaj vlogo
        </Link>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
      <footer className="px-6 py-4 text-center text-xs text-muted-foreground">
        Podpora odločanju brez klinične validacije; primerja pacienta z njegovimi prejšnjimi sejami.
      </footer>
    </div>
  )
}
