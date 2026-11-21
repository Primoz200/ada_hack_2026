# PLAN za izvedbo rešitve

### Smernice podjetja Ixtlan za hackathon ADAHACK 2026 [https://hack.klub-ada.si/en]

Izziv se osredotoča na razvoj digitalnega sistema, ki pacientom omogoča preprosto poročanje o počutju in zdravstvenem stanju,
zdravstvenemu osebju pa pomaga pravočasno prepoznati morebitne zaplete in ukrepati.

## Rešitev naše ekipe

Načrt je izdelati spletni portal za spremljanje zdravstvenega stanja pacientov po odpustitvi iz bolnišnične oskrbe,
s tem da je pozornost namenjena pacientom pri katerih je možno poslabšanje motoričnih (gibalnih) sposobnosti.

Tukaj predvsem ciljava na paciente, ki okrevajo po možganski kapi, paciente ki okrevajo po operaciji karpalnega tunela,
pacienti na onkološkem oddelku pri katerih lahko nastanejo komplikacije kot so periferna nevropatija zaradi kemoterapije (CIPN).

### Pridobljeni podatki

Problemi na katere naletimo ko paciente sprašujemo o njihovem zdravstvenem stanju je objektivnost podatkov.

Vnosna polja kjer rabi pacient napisati kako se počuti danes v primerjavi z včeraj niso objektivne narave. Prav tako do tega problema
naletimo pri klasičnih "oceni svoje počutje od 1-10" kar je po sami naravi izredno težko oceniti s tem da se vrednosti
pogosto zgostijo ob vrednosti 7 ki predstavlja neko mejo med "srednje dobrim" in "dobrim" počutjem.

Povprečen človek tudi nima vse oprema za izvajanje zdravniških testov kot so merjenje krvnega tlaka kaj šele
opreme za MRI, X-ray in CT scane. Zato je pomemben vidik sploh prepoznati katere podatke (po možnosti čim bolj objektivne) lahko
pacient priskrbi zdravniku brez da bi moral iti osebno v zdravstveni dom ali bolnišnico, saj so zdravniki in terapevti preobremenjeni.

Ampak kaj sploh pomeni "vredu počutje", če si predstavljamo da pacient v domači oskrbi okreva po možganski kapi se lahko pojavijo
težave z natančnimi premiki rok in prstov ki na začetku niso nujno takoj opazne oziroma je degradacija motornih funkcij postopna in
ne nujno vidna iz dneva v dan zato je še posebaj pomembno da se stanje spremlja spremlja in čim hitreje opazi že najmanjše spremembe
in se tako čim prej obvesti zdravnika specialista, ki ima ustrezno znanje in zna pravilno razpolagati z vsemi informacijami, ki jih
ima na voljo. Hkrati lahko spremljamo napredek pacientov, zdravnik lahko na hitro pogleda podatke, in ocene napredka na podlagi machine learning modelov.

#### Monitoring po sami izpustitvi iz bolnišnice
Pregledi po možganski kapi so veliko bolj pogosti in intezivni kot po operaciji karpalnega kanala, kjer je schedeuled monitoring
navadno le kratek čas po sami operaciji in to navadno za odstranitev šivov in splošen pregled in za tem šele če pacient sam presodi, da mora obiskati zdravnika.

Pri vsaki bolezni, stanju ali poškodbi, kjer je pričakovano poslabšanje motoričnih funkcij, je zelo pomembna rehabilitacija in čim
hitrejša in učinkovita vadba, da do degradacije spretnosti ne pride.

Ker so časovna obdobja od obiska do obiska vedno daljša in če se stanje počasi in postopno slabša ni nujno da bom pacient to opazil.
Ljudje težko zaznamo majhne spremembe v daljšem časovnem obdobju zato je pomembno, da zdravniki dobijo tekoče podatke brez da
po nepotrebnem delamo gnečo v zdravstevnih domovih in bolnišnicah, ki že tako trpijo zaradi prenatrpanosti.

Idealno bi bilo da zdravniki ne bi imeli preveč dodatnega dela s pregledom podatkov nabranih tekom okrevanja
izven bolnišnice (doma; v domači oskrbi) ampak bi bili obveščeni če se v okrevanju kaže nek negativni trend - na primer.
iz dneva v dan se rezultati testov za fino motorične spretnosti slabšajo - prvi dan izgledajo vredu oziroma niso najboljši ampak je to pričakovano nato pa je začetna izbolšava stanja ki se nato počasi preobrne.


