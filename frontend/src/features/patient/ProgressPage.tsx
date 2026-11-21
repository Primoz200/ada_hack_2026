// "Moj napredek": own results in words, personal best, forgiving weekly streak.
import { BadgeCheck, TrendingUp } from 'lucide-react'
import { useParams } from 'react-router'
import { api, unwrap } from '@/client/api'
import { paths } from '@/app/paths'
import { useAsync } from '@/lib/useAsync'
import { ProgressChart } from './ProgressChart'
import { BackBar, ErrorBlock, formatDate, LoadingBlock } from './shared'

export function ProgressPage() {
  const { patientId = '' } = useParams()
  const { data, error, reload } = useAsync(
    () => unwrap(api.GET('/api/patients/{patient_id}/progress', { params: { path: { patient_id: patientId } } })),
    [patientId],
  )
  return (
    <div className="space-y-5">
      <BackBar to={paths.patientToday(patientId)} />
      <h1 className="text-2xl font-semibold">Moj napredek</h1>
      {error && !data ? <ErrorBlock message={error.message} onRetry={reload} /> : null}
      {!data && !error ? <LoadingBlock /> : null}
      {data ? (
        <>
          {data.points.length === 0 ? (
            <div className="space-y-2 rounded-xl border p-5 text-center">
              <TrendingUp className="mx-auto size-8" aria-hidden />
              <p className="text-lg font-medium">Tukaj bo prikazan vaš napredek.</p>
              <p className="text-muted-foreground">Opravite dnevni vnos in igro, pa se bo prikazal prvi rezultat.</p>
            </div>
          ) : (
            <section aria-label="Rezultati skozi čas" className="space-y-2">
              <ProgressChart points={data.points} personalBestDay={data.personalBestDay} />
              <p className="text-base text-muted-foreground">
                Rezultati so primerjani z vašimi lastnimi običajnimi rezultati.
              </p>
            </section>
          )}

          <section aria-label="Ta teden" className="space-y-3 rounded-xl border p-4">
            <p className="text-lg font-medium">
              {data.weekDone} od 7 dni
              {data.weekGoal ? <span className="font-normal text-muted-foreground"> (cilj: {data.weekGoal})</span> : null}
            </p>
            <div className="flex gap-1.5" aria-hidden>
              {Array.from({ length: 7 }, (_, i) => (
                <span
                  key={i}
                  className={`size-5 rounded-full border-2 border-foreground ${i < data.weekDone ? 'bg-foreground' : 'bg-transparent'}`}
                />
              ))}
            </div>
            <p className="text-muted-foreground">
              {data.weekGoal && data.weekDone >= data.weekGoal
                ? 'Tedenski cilj je dosežen. Izpuščen dan ni težava.'
                : 'Izpuščen dan ni težava. Pomembno je, da redno nadaljujete.'}
            </p>
          </section>

          {data.clinicianReviewedAt ? (
            <div role="status" className="flex items-start gap-3 rounded-xl bg-secondary p-4">
              <BadgeCheck className="mt-0.5 size-6 shrink-0" aria-hidden />
              <p>
                <strong>Zdravnik je pregledal vaše rezultate</strong>
                <br />
                <span className="text-muted-foreground">{formatDate(data.clinicianReviewedAt)}</span>
              </p>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
