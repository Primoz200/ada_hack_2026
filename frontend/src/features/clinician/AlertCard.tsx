// Open-alert card with the human-in-the-loop actions: acknowledge, or close with a chosen outcome.
import { useState } from 'react'
import { toast } from 'sonner'
import { MessageSquareQuote, OctagonAlert, TriangleAlert } from 'lucide-react'
import { api, type Alert, type Checkin, type Meta, type Outcome } from '@/client/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  CONCERN_LABEL,
  SEVERITY_LABEL,
  alertConcernText,
  alertDivergence,
  alertTriggers,
  formatDateTime,
  formatDay,
} from './model'
import { DivergenceBadge } from './ui'

interface Props {
  alert: Alert
  meta: Meta | undefined
  latestCheckin: Checkin | undefined
  onChanged: () => void
}

export function AlertCard({ alert, meta, latestCheckin, onChanged }: Props) {
  const [busy, setBusy] = useState(false)
  const [closing, setClosing] = useState(false)
  const red = alert.severity === 'red'
  const Icon = red ? OctagonAlert : TriangleAlert
  const triggers = alertTriggers(alert)
  const divergence = alertDivergence(alert) ?? (alert.diverging ? 'Objektivna meritev in pacientovo poročanje se razhajata.' : null)
  const concernText = alertConcernText(alert) ?? latestCheckin?.concernText ?? null
  const concern = latestCheckin && latestCheckin.concern !== 'none' ? latestCheckin.concern : null
  const clinicianId = meta?.clinicians[0]?.id
  const clinicianName = (id: string | null | undefined) => meta?.clinicians.find((c) => c.id === id)?.name ?? id ?? ''

  async function submit(close: boolean, outcome?: Outcome, note?: string): Promise<boolean> {
    if (!clinicianId) {
      toast.error('Ni podatka o zdravniku (meta).')
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
      if (response.status === 501) {
        toast.info('Strežnik te funkcije še nima.')
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
    <section
      data-testid="alert-card"
      aria-label="Odprto opozorilo"
      className={cn('rounded-xl border-2 p-5', red ? 'border-red-300 bg-red-50/60' : 'border-amber-300 bg-amber-50/60')}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 space-y-1">
          <div className={cn('flex items-center gap-2 text-sm font-semibold', red ? 'text-red-800' : 'text-amber-900')}>
            <Icon className="size-4" aria-hidden />
            {SEVERITY_LABEL[alert.severity] ?? alert.severity}
            <span className="font-normal text-foreground/70">· odprto od {formatDay(alert.openedDay)}</span>
            {alert.diverging && <DivergenceBadge />}
          </div>
          <p className="text-lg leading-snug font-semibold">{alert.reason}</p>
          {alert.status === 'acknowledged' && alert.acknowledgedAt && (
            <p className="text-sm text-muted-foreground">
              Potrdil {clinicianName(alert.acknowledgedBy)}, {formatDateTime(alert.acknowledgedAt)}. Opozorilo še ni zaprto.
            </p>
          )}
        </div>
        <div className="flex shrink-0 gap-2">
          {alert.status === 'new' && (
            <Button variant="outline" disabled={busy} onClick={() => submit(false)}>
              Potrdi, da sem videl
            </Button>
          )}
          <Button disabled={busy} onClick={() => setClosing(true)}>
            Zapri z izidom
          </Button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
        <div>
          <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Sprožilci</h3>
          {triggers.length === 0 ? (
            <p className="text-muted-foreground">Sprožilci niso zabeleženi.</p>
          ) : (
            <ul className="space-y-1" data-testid="alert-triggers">
              {triggers.map((t, i) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-0.5 h-fit shrink-0 whitespace-nowrap rounded bg-background px-1.5 py-0.5 text-xs font-semibold ring-1 ring-border">
                    {SEVERITY_LABEL[t.severity] ?? t.severity}
                  </span>
                  <span>
                    {t.reason || t.rule}
                    {t.day && <span className="text-muted-foreground"> · {formatDay(t.day)}</span>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="space-y-3">
          <div>
            <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Kaj poroča pacient</h3>
            {concern || concernText ? (
              <div className="flex gap-2">
                <MessageSquareQuote className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                <p>
                  {concern && <span className="font-medium">Skrb: {CONCERN_LABEL[concern]}. </span>}
                  {concernText && <span>»{concernText}«</span>}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground">Pacient ne poroča skrbi.</p>
            )}
          </div>
          {divergence && (
            <div>
              <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Razhajanje</h3>
              <p data-testid="alert-divergence">{divergence}</p>
            </div>
          )}
        </div>
      </div>

      <CloseDialog
        open={closing}
        onOpenChange={setClosing}
        outcomes={meta?.outcomes ?? {}}
        busy={busy}
        onSubmit={async (o, n) => {
          if (await submit(true, o, n)) setClosing(false)
        }}
      />
    </section>
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
          <DialogTitle>Zapri opozorilo z izidom</DialogTitle>
          <DialogDescription>Opozorila ni mogoče zapreti brez izbranega izida. Izberi, kaj je bilo storjeno.</DialogDescription>
        </DialogHeader>
        <div role="radiogroup" aria-label="Izid" className="grid gap-2">
          {entries.length === 0 && <p className="text-sm text-muted-foreground">Seznam izidov ni na voljo.</p>}
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
                  'flex items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors hover:bg-muted',
                  on ? 'border-foreground bg-muted ring-1 ring-foreground' : 'border-border',
                )}
              >
                <span className={cn('flex size-4 shrink-0 items-center justify-center rounded-full border', on ? 'border-foreground' : 'border-muted-foreground')}>
                  {on && <span className="size-2 rounded-full bg-foreground" />}
                </span>
                {label}
              </button>
            )
          })}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="alert-note">Opomba (neobvezno)</Label>
          <Textarea id="alert-note" value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
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
