// Small building blocks shared by the patient screens.
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { feedbackMark, type Feedback } from './marks'

/**
 * DESIGN.md's outline button: slate text and border on white. The shared `outline` variant is
 * neutral grey, so patient screens add this on top.
 */
export const slateOutline = 'border-input bg-card text-primary hover:bg-accent hover:text-primary'

/** Page heading like PageTitle, but it can carry a green emphasis word. */
export function Heading({ children, aside }: { children: React.ReactNode; aside?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-x-6 gap-y-3 px-2">
      <h1 className="text-[2rem] leading-tight font-bold sm:text-[2.25rem]">{children}</h1>
      {aside}
    </div>
  )
}

/** The patient column: centred, never wider than the design allows. */
export function Column({ className, ...props }: React.ComponentProps<'div'>) {
  return <div className={cn('mx-auto w-full max-w-[920px]', className)} {...props} />
}

export function BackHome({ to, label = 'Domov' }: { to: string; label?: string }) {
  return (
    <Link
      to={to}
      className="inline-flex h-12 items-center gap-2 rounded-lg px-3 text-base font-medium text-primary transition-colors hover:bg-card"
    >
      <ArrowLeft className="size-5" aria-hidden />
      {label}
    </Link>
  )
}

export function FeedbackMark(props: Feedback) {
  const m = feedbackMark(props)
  const Icon = m.icon
  return (
    <span className={cn('inline-flex h-9 items-center gap-2 rounded-md bg-muted px-3 text-[0.95rem] font-semibold', m.className)}>
      <Icon className="size-5" strokeWidth={2.25} aria-hidden />
      {m.word}
    </span>
  )
}

export function PanelSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Nalagam">
      <Skeleton className="h-8 w-2/3" />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} className="h-5 w-full" />
      ))}
    </div>
  )
}

/** A calm, recoverable load error. */
export function LoadError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Podatkov trenutno ni mogoče naložiti</h2>
      <p className="text-muted-foreground">Preverite povezavo z internetom in poskusite znova.</p>
      <Button variant="outline" size="lg" className={slateOutline} onClick={onRetry}>
        Poskusi znova
      </Button>
    </div>
  )
}
