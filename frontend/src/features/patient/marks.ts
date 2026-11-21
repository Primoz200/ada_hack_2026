// Tone / trend of the patient feedback as an icon and a word (never colour alone).
import { Minus, Sprout, TrendingDown, TrendingUp, type LucideIcon } from 'lucide-react'
import type { SelfcheckSummary } from '@/client/api'

export type Feedback = Pick<SelfcheckSummary, 'tone' | 'trend'>

interface Mark {
  icon: LucideIcon
  word: string
  className: string
}

/** Direction of the last days in words and an icon; tone as a fallback before there is a trend. */
export function feedbackMark({ tone, trend }: Feedback): Mark {
  const up = { icon: TrendingUp, className: 'text-brand-ink' }
  const flat = { icon: Minus, className: 'text-muted-foreground' }
  // a decline is said plainly, in ink: never red or amber on the patient side
  const down = { icon: TrendingDown, className: 'text-foreground' }
  if (trend === 'improving') return { ...up, word: 'Zadnje dni navzgor' }
  if (trend === 'stable') return { ...flat, word: 'Zadnje dni enakomerno' }
  if (trend === 'declining') return { ...down, word: 'Zadnje dni navzdol' }
  if (tone === 'better') return { ...up, word: 'Bolje kot običajno' }
  if (tone === 'similar') return { ...flat, word: 'Kot običajno' }
  if (tone === 'lower') return { ...down, word: 'Nižje kot običajno' }
  return { icon: Sprout, className: 'text-brand-ink', word: 'Prvi dnevi' }
}
