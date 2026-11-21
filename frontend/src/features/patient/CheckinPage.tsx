// Daily check-in: one question per screen, "Nazaj" always top left, under a minute.
import { useMemo, useState } from 'react'
import { Phone } from 'lucide-react'
import { useNavigate, useParams } from 'react-router'
import { api, unwrap, type CheckinIn, type CheckinResult, type Pathway, type Question } from '@/client/api'
import { paths } from '@/app/paths'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useAsync } from '@/lib/useAsync'
import { ChoiceButton, QuestionInput, WarningSignToggle } from './CheckinInputs'
import { ResultScreen } from './ResultScreen'
import { BackBar, CLINIC_PHONE, ErrorBlock, LoadingBlock } from './shared'

type Step = { type: 'warning' } | { type: 'question'; q: Question } | { type: 'concern' } | { type: 'who' }
type Concern = CheckinIn['concern']
type AnsweredBy = CheckinIn['answeredBy']

function CheckinFlow({ patientId, pathway }: { patientId: string; pathway: Pathway }) {
  const navigate = useNavigate()
  const todayPath = paths.patientToday(patientId)
  const steps = useMemo<Step[]>(
    () => [
      { type: 'warning' },
      ...pathway.questions.map((q) => ({ type: 'question', q }) as Step),
      { type: 'concern' },
      { type: 'who' },
    ],
    [pathway],
  )
  const [index, setIndex] = useState(0)
  const [signs, setSigns] = useState<string[]>([])
  const [noneChosen, setNoneChosen] = useState(false)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [concern, setConcern] = useState<Concern>()
  const [concernText, setConcernText] = useState('')
  const [answeredBy, setAnsweredBy] = useState<AnsweredBy>()
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string>()
  const [result, setResult] = useState<CheckinResult>()

  const step = steps[index]
  const next = () => setIndex((i) => Math.min(i + 1, steps.length - 1))
  const back = () => (index === 0 ? navigate(todayPath) : setIndex((i) => i - 1))

  async function submit(by: AnsweredBy) {
    if (sending) return
    setSending(true)
    setError(undefined)
    const body: CheckinIn = {
      patientId,
      warningSigns: signs,
      answers,
      concern: concern ?? 'none',
      answeredBy: by,
      ...(concernText.trim() ? { concernText: concernText.trim() } : {}),
    }
    try {
      setResult(await unwrap(api.POST('/api/checkins', { body })))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSending(false)
    }
  }

  if (result) return <ResultScreen result={result} todayPath={todayPath} />

  const selectedActions = new Set(pathway.warningSigns.filter((s) => signs.includes(s.id)).map((s) => s.action))

  if (error)
    return (
      <div className="space-y-4">
        <BackBar onClick={() => setError(undefined)} />
        {selectedActions.has('call_112') ? (
          <Button asChild className="h-16 w-full bg-red-800 text-xl text-white hover:bg-red-900">
            <a href="tel:112">
              <Phone className="size-6" aria-hidden /> Takoj pokličite 112
            </a>
          </Button>
        ) : null}
        {selectedActions.has('call_clinic') ? (
          <Button asChild variant="outline" className="h-14 w-full text-lg">
            <a href={`tel:${CLINIC_PHONE}`}>
              <Phone className="size-5" aria-hidden /> Pokličite ambulanto
            </a>
          </Button>
        ) : null}
        <ErrorBlock message={`Vnosa ni bilo mogoče poslati. ${error}`} onRetry={() => submit(answeredBy ?? 'self')} />
      </div>
    )

  return (
    <div className="space-y-5">
      <BackBar onClick={back} right={`Vprašanje ${index + 1} od ${steps.length}`} />
      <div
        role="progressbar"
        aria-label="Napredek vnosa"
        aria-valuemin={1}
        aria-valuemax={steps.length}
        aria-valuenow={index + 1}
        className="flex gap-1.5"
      >
        {steps.map((_, i) => (
          <span key={i} className={`h-2 flex-1 rounded-full ${i <= index ? 'bg-foreground' : 'bg-muted'}`} />
        ))}
      </div>

      {step.type === 'warning' ? (
        <div className="space-y-4">
          <h1 className="text-2xl font-semibold">{pathway.warningSignsPrompt}</h1>
          <p className="text-muted-foreground">Izberite vse, kar velja.</p>
          <div className="space-y-3">
            {pathway.warningSigns.map((s) => (
              <WarningSignToggle
                key={s.id}
                sign={s}
                selected={signs.includes(s.id)}
                onToggle={() => {
                  setNoneChosen(false)
                  setSigns((cur) => (cur.includes(s.id) ? cur.filter((x) => x !== s.id) : [...cur, s.id]))
                }}
              />
            ))}
            <ChoiceButton
              className="w-full"
              selected={noneChosen}
              onClick={() => {
                setSigns([])
                setNoneChosen(true)
                next()
              }}
            >
              Nič od tega
            </ChoiceButton>
          </div>
          <Button className="h-14 w-full text-lg" disabled={signs.length === 0} onClick={next}>
            Naprej
          </Button>
        </div>
      ) : null}

      {step.type === 'question' ? (
        <div className="space-y-5">
          <h1 className="text-2xl font-semibold">{step.q.text}</h1>
          <QuestionInput
            question={step.q}
            value={answers[step.q.id]}
            onSelect={(v) => {
              setAnswers((a) => ({ ...a, [step.q.id]: v }))
              next()
            }}
          />
        </div>
      ) : null}

      {step.type === 'concern' ? (
        <div className="space-y-4">
          <h1 className="text-2xl font-semibold">Vas glede okrevanja kaj skrbi ali ste v dvomih?</h1>
          <div className="space-y-3">
            <ChoiceButton className="w-full" selected={concern === 'none'} onClick={() => setConcern('none')}>
              Ne
            </ChoiceButton>
            <ChoiceButton className="w-full" selected={concern === 'little'} onClick={() => setConcern('little')}>
              Malo
            </ChoiceButton>
            <ChoiceButton className="w-full" selected={concern === 'call'} onClick={() => setConcern('call')}>
              Da, želim klic
            </ChoiceButton>
          </div>
          <label className="block space-y-2">
            <span className="text-base text-muted-foreground">Če želite, nam napišite več (neobvezno)</span>
            <Textarea
              value={concernText}
              maxLength={500}
              onChange={(e) => setConcernText(e.target.value)}
              className="min-h-24 text-[18px]"
            />
          </label>
          <Button className="h-14 w-full text-lg" disabled={!concern} onClick={next}>
            Naprej
          </Button>
        </div>
      ) : null}

      {step.type === 'who' ? (
        <div className="space-y-4">
          <h1 className="text-2xl font-semibold">Kdo je odgovarjal na vprašanja?</h1>
          <div className="space-y-3">
            <ChoiceButton className="w-full" selected={answeredBy === 'self'} onClick={() => setAnsweredBy('self')}>
              Sam ali sama
            </ChoiceButton>
            <ChoiceButton
              className="w-full"
              selected={answeredBy === 'assisted'}
              onClick={() => setAnsweredBy('assisted')}
            >
              S pomočjo
            </ChoiceButton>
            <ChoiceButton
              className="w-full"
              selected={answeredBy === 'relative'}
              onClick={() => setAnsweredBy('relative')}
            >
              Svojec
            </ChoiceButton>
          </div>
          <Button
            className="h-14 w-full text-lg"
            disabled={!answeredBy || sending}
            onClick={() => answeredBy && submit(answeredBy)}
          >
            {sending ? 'Pošiljam …' : 'Pošlji'}
          </Button>
        </div>
      ) : null}
    </div>
  )
}

export function CheckinPage() {
  const { patientId = '' } = useParams()
  const state = useAsync(async () => {
    const [today, pathways] = await Promise.all([
      unwrap(api.GET('/api/patients/{patient_id}/today', { params: { path: { patient_id: patientId } } })),
      unwrap(api.GET('/api/pathways')),
    ])
    const pathway = pathways.find((p) => p.code === today.pathwayCode)
    if (!pathway) throw new Error('Poti okrevanja ni bilo mogoče najti.')
    return pathway
  }, [patientId])

  if (state.error && !state.data) return <ErrorBlock message={state.error.message} onRetry={state.reload} />
  if (!state.data) return <LoadingBlock />
  return <CheckinFlow patientId={patientId} pathway={state.data} />
}
