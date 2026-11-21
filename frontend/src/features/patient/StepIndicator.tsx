// Where the patient is in the self-check. Desktop: a vertical list whose current step opens up
// to carry the instruction. Phone: a row of segments with "Korak 2 od 5".
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WizardStep } from './wizard'

export function StepRail({
  steps,
  current,
  children,
}: {
  steps: readonly WizardStep[]
  current: number
  /** instruction for the current step */
  children?: React.ReactNode
}) {
  return (
    <ol className="relative" aria-label="Koraki samopregleda">
      {steps.map((s, i) => {
        const done = i < current
        const active = i === current
        const last = i === steps.length - 1
        return (
          <li key={s.key} className="relative flex gap-4" aria-current={active ? 'step' : undefined}>
            {!last ? (
              <span
                aria-hidden
                className={cn('absolute top-9 bottom-0 left-[15px] w-0.5 rounded-full', done ? 'bg-brand' : 'bg-border')}
              />
            ) : null}
            <span
              className={cn(
                'relative z-10 mt-0.5 grid size-8 shrink-0 place-items-center rounded-full text-[0.9rem] font-semibold tabular',
                done && 'bg-brand text-white',
                active && 'bg-primary text-primary-foreground ring-4 ring-accent',
                !done && !active && 'bg-card text-muted-foreground ring-2 ring-border ring-inset',
              )}
            >
              {done ? <Check className="size-4" strokeWidth={3} aria-hidden /> : i + 1}
            </span>
            <div className={cn('min-w-0 flex-1', last ? 'pb-0' : 'pb-5')}>
              <p
                className={cn(
                  'pt-1 leading-snug',
                  active ? 'text-xl font-bold text-foreground' : 'text-[1.0625rem] font-medium',
                  done && 'text-foreground',
                  !done && !active && 'text-muted-foreground',
                )}
              >
                {s.title}
                {done ? <span className="sr-only"> (opravljeno)</span> : null}
              </p>
              {active && children ? <div className="mt-2">{children}</div> : null}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export function StepBar({ steps, current }: { steps: readonly WizardStep[]; current: number }) {
  return (
    <div>
      <p className="text-[0.95rem] font-medium text-muted-foreground">
        Korak <span className="tabular">{current + 1}</span> od <span className="tabular">{steps.length}</span>
      </p>
      <ol className="mt-2 flex gap-1.5" aria-hidden>
        {steps.map((s, i) => (
          <li
            key={s.key}
            className={cn('h-1.5 flex-1 rounded-full', i < current ? 'bg-brand' : i === current ? 'bg-primary' : 'bg-border')}
          />
        ))}
      </ol>
    </div>
  )
}
