// Smaller sections of the patient page: check-in history, action log, model info.
import { Info, Send, ShieldCheck, ShieldQuestion, Siren, UserCheck } from 'lucide-react'
import type { Alert, Checkin, Message, Meta, Pathway } from '@/client/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ANSWERED_BY_LABEL, CONCERN_LABEL, assembleActionLog, dayMs, formatAnswer, formatDateTime, formatDay, questionLabel } from './model'

export function CheckinHistory({ checkins, pathway }: { checkins: Checkin[]; pathway: Pathway }) {
  const rows = [...checkins].sort((a, b) => dayMs(b.day) - dayMs(a.day) || b.id - a.id).slice(0, 14)
  if (rows.length === 0) return <p className="py-4 text-sm text-muted-foreground">Pacient še nima dnevnih vnosov.</p>
  const signText = (id: string) => pathway.warningSigns.find((w) => w.id === id)?.text ?? id
  return (
    <Table data-testid="checkin-history">
      <TableHeader>
        <TableRow>
          <TableHead className="w-24">Datum</TableHead>
          <TableHead>Odgovori</TableHead>
          <TableHead className="w-56">Opozorilni znaki</TableHead>
          <TableHead className="w-72">Skrb pacienta</TableHead>
          <TableHead className="w-24">Odgovarjal</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((c) => (
          <TableRow key={c.id} className="align-top">
            <TableCell className="font-medium">{formatDay(c.day)}</TableCell>
            <TableCell className="whitespace-normal">
              <ul className="space-y-0.5">
                {pathway.questions
                  .filter((q) => q.id in c.answers)
                  .map((q) => (
                    <li key={q.id}>
                      <span className="text-muted-foreground">{questionLabel(q)}:</span> {formatAnswer(q, c.answers[q.id])}
                    </li>
                  ))}
              </ul>
            </TableCell>
            <TableCell className="whitespace-normal">
              {c.warningSigns.length === 0 ? (
                <span className="text-muted-foreground">brez</span>
              ) : (
                <span className="font-medium text-red-800">{c.warningSigns.map(signText).join(', ')}</span>
              )}
            </TableCell>
            <TableCell className="whitespace-normal">
              {c.concern === 'none' && !c.concernText ? (
                <span className="text-muted-foreground">ne</span>
              ) : (
                <>
                  <span className="font-medium">{CONCERN_LABEL[c.concern]}</span>
                  {c.concernText && <span className="block text-muted-foreground">»{c.concernText}«</span>}
                </>
              )}
            </TableCell>
            <TableCell>{ANSWERED_BY_LABEL[c.answeredBy] ?? c.answeredBy}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

const LOG_ICON = { opened: Siren, acknowledged: UserCheck, closed: ShieldCheck, message: Send }

export function ActionLog({ alerts, messages, meta }: { alerts: Alert[]; messages: Message[]; meta: Meta | undefined }) {
  const names = Object.fromEntries((meta?.clinicians ?? []).map((c) => [c.id, c.name]))
  const log = assembleActionLog(alerts, messages, meta?.outcomes ?? {}, names)
  if (log.length === 0) return <p className="py-4 text-sm text-muted-foreground">Za tega pacienta še ni zabeleženih ukrepov.</p>
  return (
    <ol className="space-y-3" data-testid="action-log">
      {log.map((e, i) => {
        const Icon = LOG_ICON[e.kind]
        return (
          <li key={i} className="flex gap-3 text-sm">
            <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
            <div>
              <div>{e.text}</div>
              {e.detail && <div className="text-muted-foreground">{e.kind === 'closed' ? `Opomba: ${e.detail}` : `»${e.detail}«`}</div>}
              <div className="text-xs text-muted-foreground">{formatDateTime(e.at)}</div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

export function ModelNote({ meta }: { meta: Meta | undefined }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground" data-testid="model-note">
      <ShieldQuestion className="size-4 shrink-0" aria-hidden />
      <span>Podpora odločanju brez klinične validacije; primerja pacienta z njegovimi prejšnjimi sejami.</span>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label="O modelu">
            <Info />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>O modelu</DialogTitle>
            <DialogDescription>Kratko o tem, kaj ocena pomeni in česa ne.</DialogDescription>
          </DialogHeader>
          <ul className="list-disc space-y-1.5 pl-5 text-sm">
            <li>Model oceni posamezen test sledenja (0–100) iz sledi prsta ali miške. Pacienta in njegove zgodovine ne pozna.</li>
            <li>Trend je pravilo brez modela: primerja glajene ocene z izhodiščem pacienta (mediana sej 2–4; prva seja je vaja).</li>
            <li>Model je učen na sintetičnih podatkih. Pragovi opozoril so inženirska izbira, ne klinično validirani.</li>
            <li>Sistem kaže odstopanje od pacientovega lastnega izhodišča, ne postavlja diagnoz. Opozorilo vedno zapre zdravnik.</li>
          </ul>
          <p className="text-xs text-muted-foreground">Različica modela: {meta?.modelVersion ?? 'neznana'}</p>
        </DialogContent>
      </Dialog>
    </div>
  )
}
