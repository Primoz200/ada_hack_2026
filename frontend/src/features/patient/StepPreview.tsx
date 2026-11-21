// A small picture of one self-check step, for the overview on Domov.
import { Check, Hand } from 'lucide-react'
import { LevelPreview } from '@/games/trace/LevelPreview'
import { cn } from '@/lib/utils'
import type { WizardStep } from './wizard'

function RatingsPicture() {
  return (
    <svg viewBox="0 0 100 100" aria-hidden className="size-full">
      {[0, 1, 2, 3, 4].map((i) => (
        <circle
          key={i}
          cx={20 + i * 15}
          cy={50}
          r={5.5}
          fill={i === 3 ? 'var(--primary)' : 'var(--card)'}
          stroke={i === 3 ? 'var(--primary)' : 'var(--input)'}
          strokeWidth={2}
        />
      ))}
    </svg>
  )
}

function Picture({ step }: { step: WizardStep }) {
  if (step.kind === 'ratings') return <RatingsPicture />
  if (step.kind === 'game' && step.gameType === 'trace') return <LevelPreview level={step.level} className="size-full" />
  return <Hand className="m-auto size-1/2 text-primary" strokeWidth={1.75} aria-hidden />
}

export function StepPreview({ step, done }: { step: WizardStep; done: boolean }) {
  return (
    <li className="min-w-0">
      <div className="relative flex aspect-[4/3] items-center justify-center rounded-xl bg-muted p-3">
        <div className={cn('flex size-full items-center justify-center [&>svg]:h-full [&>svg]:w-auto', done && 'opacity-55')}>
          <Picture step={step} />
        </div>
        {done ? (
          <span className="absolute top-2 right-2 grid size-7 place-items-center rounded-full bg-brand text-white">
            <Check className="size-4" strokeWidth={3} aria-hidden />
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-[0.95rem] leading-snug font-medium">
        {step.title}
        {done ? <span className="sr-only"> (danes opravljeno)</span> : null}
      </p>
    </li>
  )
}
