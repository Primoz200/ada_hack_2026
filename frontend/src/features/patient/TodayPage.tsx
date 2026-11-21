// "Danes": today's tasks, streak, reminder, last team message, help.
import { BellRing, Check, ChevronRight, ClipboardList, LineChart, MessageSquare, PenLine } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { api, unwrap, type Today, type TodayTask } from '@/client/api'
import { paths } from '@/app/paths'
import { Button } from '@/components/ui/button'
import { useAsync } from '@/lib/useAsync'
import { HelpDialog } from './HelpDialog'
import { ErrorBlock, formatDate, LoadingBlock, levelLabel } from './shared'

function taskTitle(t: TodayTask): string {
  if (t.kind === 'checkin') return 'Kako ste danes?'
  if (t.gameType === 'trace') return `Sledi poti: ${levelLabel(t.level)}`
  return t.level ? `${t.title}: stopnja ${t.level}` : t.title
}

function taskHref(patientId: string, t: TodayTask): string {
  return t.kind === 'checkin' ? paths.patientCheckin(patientId) : paths.patientGame(patientId, t.gameType ?? 'trace', t.level ?? 1)
}

function TaskButton({ patientId, task }: { patientId: string; task: TodayTask }) {
  const Icon = task.kind === 'checkin' ? ClipboardList : PenLine
  return (
    <Button
      asChild
      variant={task.done ? 'secondary' : 'default'}
      className="h-auto min-h-16 w-full justify-between px-4 py-3 text-left text-lg"
    >
      <Link to={taskHref(patientId, task)}>
        <span className="flex items-center gap-3">
          <Icon className="size-6" aria-hidden />
          {taskTitle(task)}
        </span>
        <span className="flex items-center gap-1 text-base font-normal">
          {task.done ? (
            <>
              <Check className="size-5" aria-hidden /> Opravljeno
            </>
          ) : (
            <ChevronRight className="size-6" aria-hidden />
          )}
        </span>
      </Link>
    </Button>
  )
}

function WeekDots({ done }: { done: number }) {
  return (
    <div className="flex gap-1.5" aria-hidden>
      {Array.from({ length: 7 }, (_, i) => (
        <span
          key={i}
          className={`size-4 rounded-full border-2 border-foreground ${i < done ? 'bg-foreground' : 'bg-transparent'}`}
        />
      ))}
    </div>
  )
}

function Content({ data, patientId }: { data: Today; patientId: string }) {
  const allDone = data.tasks.length > 0 && data.tasks.every((t) => t.done)
  const first = data.name.split(' ')[0]
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Pozdravljeni, {first}</h1>

      {data.reminder ? (
        <div role="status" className="flex gap-3 rounded-xl border-2 border-foreground p-4">
          <BellRing className="mt-0.5 size-6 shrink-0" aria-hidden />
          <p>{data.reminder}</p>
        </div>
      ) : null}

      {allDone ? (
        <div role="status" className="rounded-xl bg-secondary p-5 text-center">
          <Check className="mx-auto size-8" aria-hidden />
          <p className="mt-2 text-xl font-semibold">Za danes ste opravili vse.</p>
          <p className="mt-1 text-muted-foreground">Hvala. Vidimo se jutri.</p>
        </div>
      ) : null}

      <section aria-label="Današnje naloge" className="space-y-3">
        <h2 className="text-lg font-semibold">Današnje naloge</h2>
        {data.tasks.length === 0 ? <p className="text-muted-foreground">Danes ni nalog.</p> : null}
        {data.tasks.map((t) => (
          <TaskButton key={t.id} patientId={patientId} task={t} />
        ))}
      </section>

      <section aria-label="Ta teden" className="space-y-2 rounded-xl border p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="font-medium">{data.weekDone} od 7 dni</p>
          <WeekDots done={data.weekDone} />
        </div>
        {data.streakDays > 0 ? (
          <p className="text-muted-foreground">Zaporedni dnevi: {data.streakDays}</p>
        ) : null}
      </section>

      {data.lastMessage ? (
        <section aria-label="Sporočilo vašega tima" className="space-y-2 rounded-xl border p-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <MessageSquare className="size-5" aria-hidden /> Sporočilo vašega tima
          </h2>
          <p>{data.lastMessage.text}</p>
          <p className="text-base text-muted-foreground">
            {data.lastMessage.author ? `${data.lastMessage.author}, ` : ''}
            {formatDate(data.lastMessage.createdAt)}
          </p>
        </section>
      ) : null}

      <HelpDialog />

      <Button asChild variant="ghost" className="h-14 w-full text-lg">
        <Link to={paths.patientProgress(patientId)}>
          <LineChart className="size-5" aria-hidden /> Moj napredek
        </Link>
      </Button>
    </div>
  )
}

export function TodayPage() {
  const { patientId = '' } = useParams()
  const { data, error, loading, reload } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  if (error && !data) return <ErrorBlock message={error.message} onRetry={reload} />
  if (loading && !data) return <LoadingBlock />
  if (!data) return <LoadingBlock />
  return <Content data={data} patientId={patientId} />
}
