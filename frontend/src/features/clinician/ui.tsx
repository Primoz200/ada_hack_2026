// Small shared presentation pieces for the clinician screens.
import { CircleCheck, CircleSlash, GitCompareArrows, Hourglass, OctagonAlert, RotateCw, TriangleAlert, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import { STATUS_LABEL, type Status } from './model'

const STATUS_STYLE: Record<Status, { icon: LucideIcon; cls: string }> = {
  red: { icon: OctagonAlert, cls: 'bg-status-red-bg text-status-red' },
  yellow: { icon: TriangleAlert, cls: 'bg-status-amber-bg text-status-amber' },
  no_data: { icon: CircleSlash, cls: 'bg-status-grey-bg text-status-grey' },
  insufficient_data: { icon: Hourglass, cls: 'text-status-grey ring-1 ring-inset ring-border' },
  // grey and quiet, never green: the eye should pass over it
  stable: { icon: CircleCheck, cls: 'text-status-grey ring-1 ring-inset ring-border' },
}

/** Status as icon + word + colour, never colour alone. Stable patients are grey. */
export function StatusBadge({ status, label, size = 'md', className }: { status: Status; label?: string; size?: 'md' | 'lg'; className?: string }) {
  const { icon: Icon, cls } = STATUS_STYLE[status]
  return (
    <span
      data-status={status}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md font-semibold whitespace-nowrap',
        size === 'md' ? 'h-8 px-2.5 text-[0.9375rem]' : 'h-9 px-3 text-base',
        cls,
        className,
      )}
    >
      <Icon className={size === 'md' ? 'size-4' : 'size-[1.125rem]'} strokeWidth={2} aria-hidden />
      {label ?? STATUS_LABEL[status]}
    </span>
  )
}

/** Objective measurement and the patient's own report point in different directions. */
export function DivergenceNote({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p className={cn('flex items-start gap-2.5', className)} data-testid="alert-divergence">
      <GitCompareArrows className="mt-1 size-[1.125rem] shrink-0 text-primary" strokeWidth={1.75} aria-hidden />
      <span>{children}</span>
    </p>
  )
}

/** Calm empty state: an icon, one sentence that says what is going on, an optional hint. */
export function EmptyState({ icon: Icon, title, hint, className }: { icon: LucideIcon; title: string; hint?: string; className?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 px-6 py-12 text-center', className)}>
      <Icon className="mb-1 size-7 text-input" strokeWidth={1.75} aria-hidden />
      <p className="font-semibold">{title}</p>
      {hint && <p className="max-w-md text-[0.9375rem] text-muted-foreground">{hint}</p>}
    </div>
  )
}

export function ErrorState({ title, message, onRetry, className }: { title: string; message?: string; onRetry?: () => void; className?: string }) {
  return (
    <div role="alert" className={cn('flex flex-col items-center justify-center gap-2 px-6 py-12 text-center', className)}>
      <p className="font-semibold">{title}</p>
      {message && <p className="max-w-md text-[0.9375rem] text-muted-foreground">{message}</p>}
      {onRetry && (
        <Button variant="outline" className={cn('mt-2', outlineButton)} onClick={onRetry}>
          <RotateCw aria-hidden /> Poskusi znova
        </Button>
      )}
    </div>
  )
}

/** DESIGN.md "outline": white fill, slate border and text (the shared variant fills with the page colour). */
export const outlineButton = 'border-input bg-card text-primary hover:bg-accent hover:text-primary'

/** Underlined tabs in the portal's slate (the shared default is a small grey pill). */
export function UnderlineTabs<T extends string>({
  value,
  onChange,
  items,
  label,
}: {
  value: T
  onChange: (v: T) => void
  items: { id: T; label: string; count?: number }[]
  label: string
}) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as T)}>
      <TabsList variant="line" aria-label={label} className="h-11 gap-6 p-0 group-data-horizontal/tabs:h-11">
        {items.map((t) => (
          <TabsTrigger
            key={t.id}
            value={t.id}
            className="h-11 flex-none px-0 text-base text-muted-foreground after:bottom-[-1px]! data-active:text-foreground data-active:after:bg-primary"
          >
            {t.label}
            {t.count != null && <span className="tabular font-normal text-muted-foreground">{t.count}</span>}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}

/** A small labelled value: label above in meta size, value below. */
export function Labelled({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <div className={cn('min-w-0', className)}>
      <div className="text-[0.9375rem] font-medium text-muted-foreground">{label}</div>
      <div className="mt-0.5">{children}</div>
    </div>
  )
}
