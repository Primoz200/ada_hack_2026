// Smaller sections of the patient page: check-in history, action log, model info.
import { Info, ShieldCheck, Siren, UserCheck } from 'lucide-react'
import type { Alert, Checkin, Meta, Pathway } from '@/client/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { assembleActionLog, checkinRows, formatDateTime, formatDay, ratingQuestions } from './model'

/** Date, wellbeing and pain. Nothing else is asked any more. */
export function CheckinHistory({ checkins, pathway }: { checkins: Checkin[]; pathway: Pathway }) {
  const rows = checkinRows(checkins)
  const [wq, pq] = ratingQuestions(pathway.questions)
  if (rows.length === 0) return <p className="py-2 text-[0.9375rem] text-muted-foreground">Pacient še ni ocenil počutja in bolečine.</p>
  return (
    <table className="w-full text-base" data-testid="checkin-history">
      <thead>
        <tr className="border-b border-border text-left text-[0.9375rem] text-muted-foreground">
          <th className="pb-2 font-medium">Datum</th>
          <th className="pb-2 text-right font-medium">{wq.shortLabel}</th>
          <th className="pb-2 text-right font-medium">{pq.shortLabel}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((c) => (
          <tr key={c.id} className="border-b border-border last:border-b-0">
            <td className="tabular py-1.5">{formatDay(c.day)}</td>
            <td className="tabular py-1.5 text-right">
              <Rating value={c.answers[wq.id]} max={wq.max} />
            </td>
            <td className="tabular py-1.5 text-right">
              <Rating value={c.answers[pq.id]} max={pq.max} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Rating({ value, max }: { value: number | undefined; max: number }) {
  if (value == null) return <span className="text-muted-foreground">ni ocene</span>
  return (
    <>
      <span className="font-semibold">{value.toLocaleString('sl-SI', { maximumFractionDigits: 1 })}</span>
      <span className="text-muted-foreground"> od {max}</span>
    </>
  )
}

const LOG_ICON = { opened: Siren, acknowledged: UserCheck, closed: ShieldCheck }

export function ActionLog({ alerts, meta }: { alerts: Alert[]; meta: Meta | undefined }) {
  const names = Object.fromEntries((meta?.clinicians ?? []).map((c) => [c.id, c.name]))
  const log = assembleActionLog(alerts, meta?.outcomes ?? {}, names)
  if (log.length === 0)
    return <p className="py-2 text-[0.9375rem] text-muted-foreground">Za tega pacienta še ni bilo opozoril, zato tudi ni zabeleženih ukrepov.</p>
  return (
    <ol data-testid="action-log">
      {log.map((e, i) => {
        const Icon = LOG_ICON[e.kind]
        return (
          <li key={i} className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-3 border-b border-border py-3 first:pt-0 last:border-b-0">
            <Icon className="mt-0.5 size-[1.125rem] text-primary" strokeWidth={1.75} aria-hidden />
            <div>
              <div className="font-medium">{e.text}</div>
              {e.detail && <div className="text-[0.9375rem] text-muted-foreground">{e.kind === 'closed' ? `Opomba: ${e.detail}` : e.detail}</div>}
              <div className="tabular mt-0.5 text-[0.875rem] text-muted-foreground">{formatDateTime(e.at)}</div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export function ModelNote({ meta }: { meta: Meta | undefined }) {
  return (
    <div className="flex items-center gap-2 text-[0.9375rem] text-muted-foreground" data-testid="model-note">
      <span>Podpora odločanju brez klinične validacije: pacienta primerja z njegovimi prejšnjimi sejami, ne postavlja diagnoz.</span>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon-sm" className="text-primary hover:bg-accent hover:text-primary" aria-label="O modelu">
            <Info />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-xl font-bold">O modelu</DialogTitle>
            <DialogDescription>Kaj ocena pomeni in česa ne.</DialogDescription>
          </DialogHeader>
          <ul className="list-disc space-y-2 pl-5 text-[0.9375rem]">
            <li>Model oceni posamezen test sledenja (0–100) iz sledi prsta ali miške. Pacienta in njegove zgodovine ne pozna.</li>
            <li>Trend je pravilo brez modela: primerja glajene ocene z izhodiščem pacienta (mediana sej 2–4; prva seja je vaja).</li>
            <li>Model je učen na sintetičnih podatkih. Pragovi opozoril so inženirska izbira, ne klinično validirani.</li>
            <li>Sistem kaže odstopanje od pacientovega lastnega izhodišča, ne postavlja diagnoz. Opozorilo vedno zapre zdravnik.</li>
          </ul>
          <p className="text-[0.875rem] text-muted-foreground">Različica modela: {meta?.modelVersion ?? 'neznana'}</p>
        </DialogContent>
      </Dialog>
    </div>
  )
}
