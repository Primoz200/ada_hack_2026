// What the patient sees after a check-in, by messageLevel (plan section 8: three alert levels + thanks).
import { Check, Info, Phone, PhoneCall } from 'lucide-react'
import { Link } from 'react-router'
import type { CheckinResult } from '@/client/api'
import { Button } from '@/components/ui/button'
import { CLINIC_PHONE, CLINIC_PHONE_LABEL } from './shared'

export function ResultScreen({ result, todayPath }: { result: CheckinResult; todayPath: string }) {
  const { messageLevel: level, messageTitle: title, messageText: text } = result

  if (level === 'call_112') {
    // Covers the whole viewport, including the layout chrome and the prototype banner.
    return (
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="emergency-title"
        className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 overflow-y-auto bg-red-800 p-6 text-center text-white"
      >
        <PhoneCall className="size-16" aria-hidden />
        <h1 id="emergency-title" className="text-4xl font-bold">
          Takoj pokličite 112
        </h1>
        <div className="space-y-2 text-xl">
          <p className="font-semibold">{title}</p>
          <p>{text}</p>
        </div>
        <Button
          asChild
          className="h-20 w-full max-w-sm bg-white text-2xl font-bold text-red-900 hover:bg-red-50"
        >
          <a href="tel:112">
            <Phone className="size-7" aria-hidden /> Pokliči 112
          </a>
        </Button>
        <Link to={todayPath} className="inline-flex min-h-12 items-center text-lg underline">
          Že sem poklical ali poklicala
        </Link>
      </div>
    )
  }

  if (level === 'call_clinic') {
    return (
      <div className="space-y-5">
        <div role="alert" className="space-y-4 rounded-xl border-2 border-amber-600 bg-amber-50 p-5 text-amber-950">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p>{text}</p>
          <Button asChild className="h-16 w-full bg-amber-900 text-xl text-white hover:bg-amber-950">
            <a href={`tel:${CLINIC_PHONE}`}>
              <Phone className="size-6" aria-hidden /> Pokliči ambulanto ({CLINIC_PHONE_LABEL})
            </a>
          </Button>
        </div>
        <Button asChild variant="outline" className="h-14 w-full text-lg">
          <Link to={todayPath}>Nazaj na Danes</Link>
        </Button>
      </div>
    )
  }

  if (level === 'neutral') {
    return (
      <div className="space-y-5">
        <div role="status" className="space-y-3 rounded-xl border bg-secondary p-5">
          <Info className="size-7" aria-hidden />
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p>{text}</p>
        </div>
        <Button asChild className="h-14 w-full text-lg">
          <Link to={todayPath}>Nazaj na Danes</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div role="status" className="space-y-3 rounded-xl border p-5">
        <Check className="size-8" aria-hidden />
        <p className="text-lg font-medium">Poslano vašemu zdravniku</p>
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p>{text}</p>
      </div>
      <Button asChild className="h-14 w-full text-lg">
        <Link to={todayPath}>Nazaj na Danes</Link>
      </Button>
    </div>
  )
}
