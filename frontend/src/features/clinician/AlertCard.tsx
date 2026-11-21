// Open-alert box with the human-in-the-loop actions: acknowledge, or close with a chosen outcome.
// One status, one headline sentence, at most two key facts, then the actions. Triggers live behind "Podrobnosti".
import { useState } from 'react'
import { toast } from 'sonner'
import { Check, ChevronDown } from 'lucide-react'
import { api, type Alert, type Meta, type Outcome, type PatientDetail } from '@/client/api'
import { Panel } from '@/components/app/Panel'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  GAME_TITLE,
  SEVERITY_LABEL,
  SEVERITY_STATUS,
  alertDivergence,
  alertFacts,
  alertGameSet,
  alertTriggers,
  formatDateTime,
  formatDay,
  ruleLabel,
  type Fact,
  type Trigger,
} from './model'
import { DivergenceNote, StatusBadge, outlineButton } from './ui'

interface Props {
  alert: Alert
  patient: PatientDetail
  today: string
  meta: Meta | undefined
  onChanged: () => void
}

const TONE: Record<string, { panel: string; muted: string; rule: string }> = {
  red: { panel: 'bg-status-red-bg', muted: 'text-status-red', rule: 'border-status-red/20' },
  yellow: { panel: 'bg-status-amber-bg', muted: 'text-status-amber', rule: 'border-status-amber/20' },
  // grey on the blue-grey page would vanish: a white panel, the grey lives in the badge
  grey: { panel: 'bg-card', muted: 'text-status-grey', rule: 'border-border' },
}

export function AlertCard({ alert, patient, today, meta, onChanged }: Props) {
  const [busy, setBusy] = useState(false)
  const [closing, setClosing] = useState(false)
  const tone = TONE[alert.severity] ?? TONE.grey
  const facts = alertFacts(alert, patient, today)
  const triggers = alertTriggers(alert)
  const games = alertGameSet(alert)
  const divergenceFallback =
    games.length > 1
      ? 'Meritve in pacientovo poročanje se razhajajo.'
      : games[0] === 'camera'
        ? 'Vaje s kamero in pacientovo poročanje se razhajajo.'
        : 'Rezultati sledenja in pacientovo poročanje se razhajata.'
  const divergence = alertDivergence(alert) ?? (alert.diverging ? divergenceFallback : null)
  // two measurement facts + the visit share one compact row
  const factCols = facts.length >= 3 ? 'sm:grid-cols-[repeat(3,minmax(0,max-content))] gap-x-10' : 'sm:grid-cols-[repeat(2,minmax(0,max-content))] gap-x-12'
  const clinicianId = meta?.clinicians[0]?.id
  const clinicianName = (id: string | null | undefined) => meta?.clinicians.find((c) => c.id === id)?.name ?? id ?? ''

  async function submit(close: boolean, outcome?: Outcome, note?: string): Promise<boolean> {
    if (!clinicianId) {
      toast.error('Podatki o zdravniku se še nalagajo. Poskusite znova.')
      return false
    }
    setBusy(true)
    try {
      const { response } = await api.POST('/api/alerts/{alert_id}/ack', {
        params: { path: { alert_id: alert.id } },
        body: { clinicianId, close, outcome: outcome ?? null, note: note?.trim() || null },
      })
      if (response.status === 422) {
        toast.error('Opozorila ni mogoče zapreti brez izbranega izida.')
        return false
      }
      if (!response.ok) {
        toast.error(`Ukrep ni uspel (${response.status}).`)
        return false
      }
      toast.success(close ? 'Opozorilo je zaprto.' : 'Potrjeno, da ste opozorilo videli.')
      onChanged()
      return true
    } catch {
      toast.error('Strežnik ni dosegljiv.')
      return false
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel data-testid="alert-card" aria-label="Odprto opozorilo" className={tone.panel}>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <StatusBadge
          status={SEVERITY_STATUS[alert.severity] ?? 'no_data'}
          label={SEVERITY_LABEL[alert.severity]}
          size="lg"
          className={alert.severity === 'grey' ? undefined : 'bg-card'}
        />
        <span className={cn('text-[0.9375rem] font-medium', tone.muted)}>odprto od {formatDay(alert.openedDay)}</span>
        {alert.status === 'acknowledged' && alert.acknowledgedAt && (
          <span className={cn('inline-flex items-center gap-1.5 text-[0.9375rem] font-medium', tone.muted)}>
            <Check className="size-4" aria-hidden />
            Videno: {clinicianName(alert.acknowledgedBy)}, {formatDateTime(alert.acknowledgedAt)}
          </span>
        )}
      </div>

      <div className="mt-5 grid gap-x-12 gap-y-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="min-w-0">
          <h2 className="max-w-[44ch] text-[1.625rem] leading-tight font-bold">{alert.reason}</h2>
          {divergence && <DivergenceNote className="mt-3 max-w-[62ch]">{divergence}</DivergenceNote>}
        </div>
        <div className="flex flex-wrap gap-3 lg:justify-end">
          {alert.status === 'new' && (
            <Button variant="outline" size="lg" className={outlineButton} disabled={busy} onClick={() => submit(false)}>
              Potrdi, da sem videl
            </Button>
          )}
          <Button size="lg" disabled={busy} onClick={() => setClosing(true)}>
            Zapri z izidom
          </Button>
        </div>
      </div>

      {facts.length > 0 && (
        <dl className={cn('mt-7 grid gap-y-4 border-t pt-6', factCols, tone.rule)} data-testid="alert-facts">
          {facts.map((f) => (
            <FactItem key={f.label} fact={f} muted={tone.muted} />
          ))}
        </dl>
      )}

      {triggers.length > 0 && (
        <details className="group mt-6">
          <summary
            className={cn(
              'inline-flex cursor-pointer list-none items-center gap-1.5 rounded-md text-[0.9375rem] font-semibold [&::-webkit-details-marker]:hidden',
              tone.muted,
            )}
          >
            <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
            Podrobnosti
            <span className="font-medium">
              ({triggers.length} {triggers.length === 1 ? 'sprožilec' : triggers.length === 2 ? 'sprožilca' : triggers.length < 5 ? 'sprožilci' : 'sprožilcev'})
            </span>
          </summary>
          <ul className="mt-3 max-w-[84ch] space-y-2.5 text-[0.9375rem]" data-testid="alert-triggers">
            {triggers.map((t, i) => (
              <li key={i} className="grid grid-cols-[6.5rem_8.5rem_minmax(0,1fr)] gap-3">
                <span className={cn('tabular font-medium', tone.muted)}>{t.day ? formatDay(t.day) : '–'}</span>
                <span className={cn('font-medium', tone.muted)} data-testid="trigger-measurement">
                  {triggerMeasurement(t)}
                </span>
                <span>
                  <span className="font-semibold">{ruleLabel(t.rule, t.game) ?? SEVERITY_LABEL[t.severity] ?? 'Sprožilec'}.</span> {t.reason}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}

      <CloseDialog
        open={closing}
        onOpenChange={setClosing}
        outcomes={meta?.outcomes ?? {}}
        busy={busy}
        onSubmit={async (o, n) => {
          if (await submit(true, o, n)) setClosing(false)
        }}
      />
    </Panel>
  )
}

/** What a trigger is about: a measurement, the ratings, or missing self-checks. */
function triggerMeasurement(t: Trigger): string {
  if (t.game) return GAME_TITLE[t.game]
  if (t.rule === 'subjective_drop') return 'Počutje, bolečina'
  if (t.rule === 'no_data') return 'Samopregled'
  // older evidence without `game`: the trend rules were about tracing
  if (t.rule === 'trend_drop' || t.rule === 'big_drop' || t.rule === 'both') return GAME_TITLE.trace
  return '–'
}

function FactItem({ fact, muted }: { fact: Fact; muted: string }) {
  return (
    <div className="min-w-0">
      <dt className={cn('text-[0.9375rem] font-medium', muted)}>{fact.label}</dt>
      <dd className="mt-0.5 text-xl font-bold">
        {fact.value}
        {fact.detail && <span className={cn('ml-2 text-base font-medium', muted)}>{fact.detail}</span>}
      </dd>
    </div>
  )
}

function CloseDialog({
  open,
  onOpenChange,
  outcomes,
  busy,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  outcomes: Record<string, string>
  busy: boolean
  onSubmit: (outcome: Outcome, note: string) => void
}) {
  const [outcome, setOutcome] = useState<Outcome | null>(null)
  const [note, setNote] = useState('')
  const entries = Object.entries(outcomes) as [Outcome, string][]
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Zapri opozorilo z izidom</DialogTitle>
          <DialogDescription>Opozorila ni mogoče zapreti brez izida. Izberite, kaj je bilo storjeno.</DialogDescription>
        </DialogHeader>
        <div role="radiogroup" aria-label="Izid" className="grid gap-2" data-testid="outcome-options">
          {entries.length === 0 && <p className="text-[0.9375rem] text-muted-foreground">Seznam izidov se še nalaga.</p>}
          {entries.map(([id, label]) => {
            const on = outcome === id
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setOutcome(id)}
                className={cn(
                  'flex min-h-12 items-center gap-3 rounded-lg border px-4 py-2.5 text-left text-base font-medium transition-colors hover:bg-accent',
                  on ? 'border-primary bg-accent text-foreground ring-1 ring-primary' : 'border-border',
                )}
              >
                <span className={cn('flex size-[1.125rem] shrink-0 items-center justify-center rounded-full border-2', on ? 'border-primary' : 'border-input')}>
                  {on && <span className="size-2 rounded-full bg-primary" />}
                </span>
                {label}
              </button>
            )
          })}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="alert-note" className="text-[0.9375rem]">
            Opomba (neobvezno)
          </Label>
          <Textarea id="alert-note" value={note} onChange={(e) => setNote(e.target.value)} rows={3} className="border-input bg-card text-base" />
        </div>
        <DialogFooter>
          <Button variant="outline" className={outlineButton} onClick={() => onOpenChange(false)}>
            Prekliči
          </Button>
          <Button disabled={!outcome || busy} onClick={() => outcome && onSubmit(outcome, note)}>
            Zapri opozorilo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
