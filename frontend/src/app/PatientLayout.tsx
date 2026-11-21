// Phone-first shell for the patient part: narrow column, large text, emergency notice always visible.
import { Link, Outlet } from 'react-router'
import { paths } from './paths'
import { PrototypeBanner } from './PrototypeBanner'

export function PatientLayout() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-background text-[18px]">
      <PrototypeBanner />
      <main className="flex-1 px-4 py-4">
        <Outlet />
      </main>
      <footer className="border-t px-4 py-3 text-center text-sm text-muted-foreground">
        Aplikacija ne nadomešča nujne pomoči. V nujnem primeru pokličite 112.
        <div className="mt-1">
          <Link to={paths.home} className="underline">
            Zamenjaj vlogo
          </Link>
        </div>
      </footer>
    </div>
  )
}
