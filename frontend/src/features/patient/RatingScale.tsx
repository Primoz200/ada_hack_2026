// Ten large round buttons for a 1-10 rating, with the ends named in words. Native radios
// underneath, so arrow keys and screen readers work as expected. No slider.
import { useId } from 'react'
import { cn } from '@/lib/utils'

export function RatingScale({
  question,
  minLabel,
  maxLabel,
  value,
  onChange,
  min = 1,
  max = 10,
}: {
  question: string
  minLabel: string
  maxLabel: string
  value: number | undefined
  onChange: (v: number) => void
  min?: number
  max?: number
}) {
  const name = useId()
  const values = Array.from({ length: max - min + 1 }, (_, i) => min + i)
  return (
    <fieldset className="min-w-0">
      <legend className="text-xl font-bold">{question}</legend>
      <div className="mt-4 grid grid-cols-5 gap-2.5 sm:grid-cols-10 sm:gap-2">
        {values.map((v) => (
          <label key={v} className="relative block">
            <input
              type="radio"
              name={name}
              value={v}
              checked={value === v}
              onChange={() => onChange(v)}
              className="peer sr-only"
              aria-label={v === min ? `${v}, ${minLabel}` : v === max ? `${v}, ${maxLabel}` : String(v)}
            />
            <span
              className={cn(
                'mx-auto grid aspect-square w-full max-w-14 min-w-12 cursor-pointer place-items-center rounded-full text-lg font-semibold tabular transition-colors select-none',
                'bg-card text-primary ring-1 ring-input ring-inset hover:bg-accent',
                'peer-checked:bg-primary peer-checked:text-primary-foreground peer-checked:ring-primary',
                'peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ring/55',
              )}
            >
              {v}
            </span>
          </label>
        ))}
      </div>
      <div className="mt-2.5 flex justify-between gap-4 text-[0.95rem] font-medium text-muted-foreground">
        <span>{minLabel}</span>
        <span className="text-right">{maxLabel}</span>
      </div>
    </fieldset>
  )
}
