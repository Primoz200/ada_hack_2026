// Where the patient is in the self-check. Desktop: a vertical list whose current step opens up
// to carry the instruction. Phone: a row of segments with "Korak 2 od 8".
import { Check, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WizardStep } from './wizard'

const NONE: ReadonlySet<string> = new Set()

export function StepRail({
  steps,
  current,
  skipped = NONE,
  children,
}: {
  steps: readonly WizardStep[]
  current: number
  /** steps passed without doing them (skipped, or no camera) */
  skipped?: ReadonlySet<string>
  /** instruction for the current step */
  children?: React.ReactNode
}) {
  // eight steps must fit beside the step itself: a little tighter when the list is long
  const compact = steps.length > 6
  return (
    <ol className="relative" aria-label="Koraki samopregleda">
      {steps.map((s, i) => {
        const passed = i < current
        const wasSkipped = passed && skipped.has(s.key)
        const done = passed && !wasSkipped
        const active = i === current
        const last = i === steps.length - 1
        const duration = s.kind === 'game' && s.durationS ? `${Math.round(s.durationS)} s` : null
        return (
          <li key={s.key} className="relative flex gap-4" aria-current={active ? 'step' : undefined}>
            {!last ? (
              <span
                aria-hidden
                className={cn(
                  'absolute bottom-0 left-[15px] w-0.5 rounded-full',
                  compact ? 'top-8' : 'top-9',
                  done ? 'bg-brand' : 'bg-border',
                )}
              />
            ) : null}
            <span
              className={cn(
                'relative z-10 mt-0.5 grid size-8 shrink-0 place-items-center rounded-full text-[0.9rem] font-semibold tabular',
                done && 'bg-brand text-white',
                wasSkipped && 'bg-muted text-muted-foreground ring-2 ring-border ring-inset',
                active && 'bg-primary text-primary-foreground ring-4 ring-accent',
                !passed && !active && 'bg-card text-muted-foreground ring-2 ring-border ring-inset',
              )}
            >
              {done ? (
                <Check className="size-4" strokeWidth={3} aria-hidden />
              ) : wasSkipped ? (
                <Minus className="size-4" strokeWidth={2.5} aria-hidden />
              ) : (
                i + 1
              )}
            </span>
            <div className={cn('min-w-0 flex-1', last ? 'pb-0' : compact ? 'pb-3.5' : 'pb-5')}>
              <p
                className={cn(
                  'flex flex-wrap items-baseline gap-x-2 pt-1 leading-snug',
                  active ? 'text-xl font-bold text-foreground' : 'text-[1.0625rem] font-medium',
                  done && 'text-foreground',
                  (wasSkipped || (!passed && !active)) && 'text-muted-foreground',
                )}
              >
                <span>{s.title}</span>
                {duration && !passed ? (
                  <span className="text-[0.9rem] font-medium text-muted-foreground tabular">{duration}</span>
                ) : null}
                {done ? <span className="sr-only"> (opravljeno)</span> : null}
                {wasSkipped ? <span className="sr-only"> (izpuščeno)</span> : null}
              </p>
              {active && children ? <div className="mt-2">{children}</div> : null}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export function StepBar({
  steps,
  current,
  skipped = NONE,
}: {
  steps: readonly WizardStep[]
  current: number
  skipped?: ReadonlySet<string>
}) {
  return (
    <div>
      <p className="text-[0.95rem] font-medium text-muted-foreground">
        Korak <span className="tabular">{current + 1}</span> od <span className="tabular">{steps.length}</span>
      </p>
      <ol className="mt-2 flex gap-1.5" aria-hidden>
        {steps.map((s, i) => (
          <li
            key={s.key}
            className={cn(
              'h-1.5 flex-1 rounded-full',
              i < current ? (skipped.has(s.key) ? 'bg-input' : 'bg-brand') : i === current ? 'bg-primary' : 'bg-border',
            )}
          />
        ))}
      </ol>
    </div>
  )
}
