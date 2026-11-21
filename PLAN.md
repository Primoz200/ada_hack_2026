# PLAN za izvedbo rešitve

### Smernice podjetja Ixtlan za hackathon ADAHACK 2026 [https://hack.klub-ada.si/en]

Izziv se osredotoča na razvoj digitalnega sistema, ki pacientom omogoča preprosto poročanje o počutju in zdravstvenem stanju, 
zdravstvenemu osebju pa pomaga pravočasno prepoznati morebitne zaplete in ukrepati.

## Rešitev naše ekipe

Načrt je izdelati spletni portal za spremljanje zdravstvenega stanja pacientov po odpustitvi iz bolnišnične oskrbe, 
s tem da je pozornost namenjena pacientom pri katerih je možno poslabšanje motoričnih  (gibalnih) sposobnosti.

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

#### Pridobitev čim bolj reprezentativnih in objektivnih podatkov

