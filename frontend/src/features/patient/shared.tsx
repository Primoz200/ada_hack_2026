// Small helpers shared by the patient screens.
import type { ReactNode } from 'react'
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

/** Demo clinic number. The contract has no clinic phone yet (see report); replace with real data. */
export const CLINIC_PHONE = '+38610000000'
export const CLINIC_PHONE_LABEL = '01 000 00 00'

export const TRACE_LEVEL_LABELS: Record<number, string> = { 1: 'Ravna črta', 2: 'Krog', 3: 'Labirint' }

export function levelLabel(level: number | null | undefined): string {
  return level ? (TRACE_LEVEL_LABELS[level] ?? `Stopnja ${level}`) : ''
}

export function handLabel(hand: string): string {
  return hand === 'left' ? 'z levo roko' : 'z desno roko'
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('sl-SI', { day: 'numeric', month: 'long', year: 'numeric' })
}

/** Top bar with "Nazaj" always at the same place (top left, 48 px target). */
export function BackBar({ to, onClick, right }: { to?: string; onClick?: () => void; right?: ReactNode }) {
  return (
    <div className="mb-4 flex min-h-12 items-center justify-between gap-3">
      {to ? (
        <Button asChild variant="ghost" className="-ml-3 h-12 px-3 text-lg">
          <Link to={to}>
            <ArrowLeft className="size-5" aria-hidden /> Nazaj
          </Link>
        </Button>
      ) : (
        <Button variant="ghost" className="-ml-3 h-12 px-3 text-lg" onClick={onClick}>
          <ArrowLeft className="size-5" aria-hidden /> Nazaj
        </Button>
      )}
      {right ? <div className="text-base text-muted-foreground">{right}</div> : null}
    </div>
  )
}

export function LoadingBlock() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Nalagam">
      <Skeleton className="h-9 w-2/3" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
    </div>
  )
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="space-y-4 rounded-xl border p-4">
      <p className="font-medium">Podatkov ni bilo mogoče naložiti.</p>
      <p className="text-base text-muted-foreground">{message}</p>
      <Button className="h-14 w-full text-lg" onClick={onRetry}>
        Poskusi znova
      </Button>
    </div>
  )
}
