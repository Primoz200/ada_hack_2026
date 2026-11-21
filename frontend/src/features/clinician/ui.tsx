// Small shared presentation pieces for the clinician screens.
import { CircleCheck, CircleSlash, GitCompareArrows, Hourglass, OctagonAlert, TriangleAlert } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { STATUS_LABEL, type Status } from './model'

const STATUS_STYLE: Record<Status, { icon: typeof OctagonAlert; cls: string }> = {
  red: { icon: OctagonAlert, cls: 'border-red-300 bg-red-50 text-red-800' },
  yellow: { icon: TriangleAlert, cls: 'border-amber-300 bg-amber-50 text-amber-900' },
  no_data: { icon: CircleSlash, cls: 'border-dashed border-border bg-background text-muted-foreground' },
  insufficient_data: { icon: Hourglass, cls: 'border-border bg-background text-muted-foreground' },
  stable: { icon: CircleCheck, cls: 'border-border bg-muted text-muted-foreground' }, // grey, not green
}

/** Status as icon + word + colour, never colour alone. Stable patients are grey. */
export function StatusBadge({ status, label, className }: { status: Status; label?: string; className?: string }) {
  const { icon: Icon, cls } = STATUS_STYLE[status]
  return (
    <span
      data-status={status}
      className={cn('inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-semibold whitespace-nowrap', cls, className)}
    >
      <Icon className="size-3.5" aria-hidden />
      {label ?? STATUS_LABEL[status]}
    </span>
  )
}

export function DivergenceBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border border-indigo-300 bg-indigo-50 px-2 py-0.5 text-xs font-semibold whitespace-nowrap text-indigo-900',
        className,
      )}
      title="Objektivna meritev in pacientovo poročanje se razhajata"
    >
      <GitCompareArrows className="size-3" aria-hidden />
      razhajanje
    </span>
  )
}

export function PageState({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{children}</div>
}
