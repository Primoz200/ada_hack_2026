// Answer inputs for the daily check-in. Large buttons only: no sliders, no dropdowns.
import type { ReactNode } from 'react'
import {
  Annoyed,
  Brain,
  Check,
  Droplets,
  EyeOff,
  Fingerprint,
  Flame,
  Frown,
  Hand,
  Laugh,
  Meh,
  MessageCircleWarning,
  Smile,
  Thermometer,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react'
import type { Question, WarningSign } from '@/client/api'
import { cn } from '@/lib/utils'

export function ChoiceButton({
  selected,
  onClick,
  children,
  className,
}: {
  selected?: boolean
  onClick: () => void
  children: ReactNode
  className?: string
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cn(
        'relative flex min-h-14 min-w-12 items-center justify-center gap-2 rounded-xl border-2 px-3 py-2 text-lg font-medium transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
        selected ? 'border-foreground bg-foreground text-background' : 'border-border bg-background hover:bg-muted',
        className,
      )}
    >
      {children}
      {selected ? <Check className="size-5 shrink-0" aria-hidden /> : null}
    </button>
  )
}

const SIGN_ICONS: Record<string, LucideIcon> = {
  face: Frown,
  limb: Hand,
  speech: MessageCircleWarning,
  vision: EyeOff,
  headache: Brain,
  wound_red: Flame,
  discharge: Droplets,
  fever: Thermometer,
  new_numbness: Fingerprint,
}

export function WarningSignToggle({
  sign,
  selected,
  onToggle,
}: {
  sign: WarningSign
  selected: boolean
  onToggle: () => void
}) {
  const Icon = SIGN_ICONS[sign.id] ?? TriangleAlert
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onToggle}
      className={cn(
        'flex min-h-16 w-full items-center gap-3 rounded-xl border-2 px-4 py-3 text-left text-lg font-medium transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
        selected ? 'border-foreground bg-foreground text-background' : 'border-border bg-background hover:bg-muted',
      )}
    >
      <Icon className="size-7 shrink-0" aria-hidden />
      <span className="flex-1">{sign.text}</span>
      <span
        aria-hidden
        className={cn(
          'flex size-7 shrink-0 items-center justify-center rounded-md border-2',
          selected ? 'border-background' : 'border-foreground',
        )}
      >
        {selected ? <Check className="size-5" /> : null}
      </span>
      <span className="sr-only">{selected ? 'Izbrano' : 'Ni izbrano'}</span>
    </button>
  )
}

const FACES: LucideIcon[] = [Frown, Annoyed, Meh, Smile, Laugh]

function EndLabels({ min, max }: { min?: string | null; max?: string | null }) {
  if (!min && !max) return null
  return (
    <div className="mt-3 flex justify-between gap-4 text-base text-muted-foreground">
      <span>{min}</span>
      <span className="text-right">{max}</span>
    </div>
  )
}

export function QuestionInput({
  question,
  value,
  onSelect,
}: {
  question: Question
  value: number | undefined
  onSelect: (v: number) => void
}) {
  const { kind, min, max } = question
  if (kind === 'yes_no') {
    return (
      <div className="grid grid-cols-2 gap-3">
        <ChoiceButton className="min-h-20 text-xl" selected={value === 0} onClick={() => onSelect(0)}>
          Ne
        </ChoiceButton>
        <ChoiceButton className="min-h-20 text-xl" selected={value === 1} onClick={() => onSelect(1)}>
          Da
        </ChoiceButton>
      </div>
    )
  }
  if (kind === 'faces5') {
    return (
      <div>
        <div className="grid grid-cols-5 gap-2">
          {FACES.map((Icon, i) => {
            const v = min + i
            return (
              <ChoiceButton
                key={v}
                className="min-h-20 flex-col gap-1 px-1"
                selected={value === v}
                onClick={() => onSelect(v)}
              >
                <Icon className="size-8" aria-hidden />
                <span className="text-base">{v}</span>
              </ChoiceButton>
            )
          })}
        </div>
        <EndLabels min={question.minLabel} max={question.maxLabel} />
      </div>
    )
  }
  const values = Array.from({ length: max - min + 1 }, (_, i) => min + i)
  if (kind === 'count') {
    return (
      <div className="space-y-3">
        {values.map((v) => (
          <ChoiceButton
            key={v}
            className="w-full"
            selected={value === v}
            onClick={() => onSelect(v)}
          >
            {v === max && question.maxLabel ? question.maxLabel : v}
          </ChoiceButton>
        ))}
      </div>
    )
  }
  // scale: numbered buttons, two rows when long (0-10)
  const cols = values.length > 6 ? 6 : values.length
  return (
    <div>
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
        {values.map((v) => (
          <ChoiceButton key={v} className="min-h-14 px-0" selected={value === v} onClick={() => onSelect(v)}>
            {v}
          </ChoiceButton>
        ))}
      </div>
      <EndLabels min={question.minLabel} max={question.maxLabel} />
    </div>
  )
}
