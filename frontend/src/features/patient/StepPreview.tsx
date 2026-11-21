// A small picture of one self-check step, for the overview on Domov. The camera exercises share
// one tile (a viewfinder around a hand) so the overview stays calm.
import { Check, Hand } from 'lucide-react'
import { LevelPreview } from '@/games/trace/LevelPreview'
import { cn } from '@/lib/utils'
import { exercisesPhrase } from './format'
import type { PreviewItem, WizardStep } from './wizard'

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

/** Viewfinder corners around a hand: "the camera watches the movement". */
function CameraPicture() {
  const corners = ['M22 38 V26 H34', 'M66 26 H78 V38', 'M78 62 V74 H66', 'M34 74 H22 V62']
  return (
    <div className="relative grid h-full aspect-square place-items-center">
      <svg viewBox="0 0 100 100" aria-hidden className="absolute inset-0 size-full">
        {corners.map((d) => (
          <path key={d} d={d} fill="none" stroke="var(--primary)" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
        ))}
      </svg>
      <Hand className="size-[38%] text-primary" strokeWidth={1.75} aria-hidden />
    </div>
  )
}

function Picture({ step }: { step: WizardStep }) {
  if (step.kind === 'ratings') return <RatingsPicture />
  if (step.kind === 'game' && step.gameType === 'trace') return <LevelPreview level={step.level} className="size-full" />
  if (step.kind === 'game' && step.gameType === 'camera') return <CameraPicture />
  return <Hand className="m-auto size-1/2 text-primary" strokeWidth={1.75} aria-hidden />
}

export function StepPreview({ item }: { item: PreviewItem }) {
  const group = item.kind === 'group'
  return (
    <li className={cn('min-w-0', group && 'max-sm:col-span-2')}>
      <div
        className={cn(
          'relative flex aspect-[4/3] items-center justify-center rounded-xl bg-muted p-3',
          group && 'max-sm:aspect-[8/3]',
        )}
      >
        <div className={cn('flex size-full items-center justify-center [&>svg]:h-full [&>svg]:w-auto', item.done && 'opacity-55')}>
          {group ? <CameraPicture /> : <Picture step={item.step} />}
        </div>
        {item.done ? (
          <span className="absolute top-2 right-2 grid size-7 place-items-center rounded-full bg-brand text-white">
            <Check className="size-4" strokeWidth={3} aria-hidden />
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-[0.95rem] leading-snug font-medium">
        {group ? item.title : item.step.title}
        {group && item.count > 1 ? (
          <span className="block font-normal text-muted-foreground">{exercisesPhrase(item.count)}</span>
        ) : null}
        {item.done ? <span className="sr-only"> (danes opravljeno)</span> : null}
      </p>
    </li>
  )
}
