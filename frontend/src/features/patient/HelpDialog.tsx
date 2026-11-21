import { LifeBuoy, Phone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { CLINIC_PHONE, CLINIC_PHONE_LABEL } from './shared'

export function HelpDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="h-14 w-full text-lg">
          <LifeBuoy className="size-5" aria-hidden /> Potrebujem pomoč
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-dvh overflow-y-auto text-[18px]">
        <DialogHeader>
          <DialogTitle className="text-xl">Potrebujem pomoč</DialogTitle>
          <DialogDescription className="text-[18px]">Izberite, kar ustreza vašemu stanju.</DialogDescription>
        </DialogHeader>
        <section className="space-y-3 rounded-xl border-2 border-foreground p-4">
          <h3 className="text-lg font-semibold">Nujno: takoj pokličite 112</h3>
          <p>
            Povešen obraz, šibka ali omrtvela roka ali noga, težave z govorom, nenadna izguba vida ali zelo hud
            glavobol.
          </p>
          <Button asChild className="h-14 w-full text-lg">
            <a href="tel:112">
              <Phone className="size-5" aria-hidden /> Pokliči 112
            </a>
          </Button>
        </section>
        <section className="space-y-3 rounded-xl border p-4">
          <h3 className="text-lg font-semibold">Drugače: pokličite ambulanto</h3>
          <p>
            Rdeča, vroča ali otekla roka ali rana, izcedek, vročina, nova omrtvelost ali kar koli, kar vas skrbi.
          </p>
          <Button asChild variant="secondary" className="h-14 w-full text-lg">
            <a href={`tel:${CLINIC_PHONE}`}>
              <Phone className="size-5" aria-hidden /> Pokliči ambulanto ({CLINIC_PHONE_LABEL})
            </a>
          </Button>
        </section>
        <DialogClose asChild>
          <Button variant="ghost" className="h-12 w-full text-lg">
            Zapri
          </Button>
        </DialogClose>
      </DialogContent>
    </Dialog>
  )
}
