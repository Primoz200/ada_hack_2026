# Uvoz v Google Predstavitve

Vse datoteke so v tej mapi: `okrevanje-doma.pptx`, `media/` (5 MP4 in 2 GIF) ter `preview.png` za primerjavo z izvirnikom.

> **Primožev obraz** je v `media/kamera.mp4`, na 6. diapozitivu PPTX in v `preview.png`. Nobene od teh datotek ne deli z javno povezavo in ne dodajaj je v javen repozitorij.

Imena menijev so angleška, kot v [Googlovi pomoči](https://support.google.com/docs/answer/97447), ki je v slovenščini ni. Če imaš slovenski vmesnik, poišči enakovreden ukaz ali začasno preklopi jezik računa.

## Koraki

### 1. Uvozi PPTX

1. Naloži `okrevanje-doma.pptx` v Google Drive.
2. Odpri z **Open with → Google Slides**.
3. Izberi **File → Save as Google Slides** in delaj naprej v novi datoteki.
4. Preveri:
   - **File → Page setup**: 13,333 × 7,5 in (33,867 × 19,05 cm). Če je stran 10 × 5,625 in, vse mere iz tabele pomnoži z 0,75.
   - Pisava v naslovih je **Hanken Grotesk**.
   - Prelomi vrstic so kot v srednjem stolpcu `preview.png`.
   - Na 1. diapozitivu je »doma« na isti višini kot v `preview.png`. Razmik vrstic je umerjen v PowerPointu in ga Google morda računa drugače: če so vse vrstice enakomerno preveč narazen (»doma« do približno 24 px nižje), v **Format → Line & paragraph spacing → Custom spacing** vsak razmik pomnoži z 0,92.
   - Povezave spodaj delujejo. Če jih uvoz izgubi, označi gumb in z **Insert → Link → Slides in this presentation** izberi 2, 3, 4, 5 oziroma 8.

### 2. Naloži in deli videe

1. Vseh pet MP4 iz `media/` naloži v eno mapo na Drivu.
2. V **Share** dodaj Primoža in račun, s katerega bosta predstavljala, poimensko. **General access** naj ostane **Restricted**.
3. Enako deli predstavitev.
4. Počakaj, da se vsak video predvaja v Drivu (obdelava lahko traja nekaj minut).

### 3. Vstavi vsak video

Mesta so označena s slikami `REPLACE: <datoteka>`. Tudi brez videov je vsak diapozitiv pravilen, samo miruje.

1. Odpri diapozitiv in izberi **Insert → Video → Google Drive**, video in **Select**.
2. Desni klik na video → **Format options**:
   - **Size & rotation**: izklopi **Lock aspect ratio**, vpiši širino in višino.
   - **Position**: izberi **From: Top left**, vpiši X in Y.
3. Šele zdaj pobriši sliko pod videom:
   1. video → **Arrange → Order → Send to back**,
   2. klikni sliko, ki je zdaj zgoraj, in pritisni Delete,
   3. video → **Arrange → Order → Bring to front**. Tega ne izpusti.

Mere v **palcih** od zgornjega levega kota (px / 144):

| Diapozitiv | Datoteka | X | Y | Širina | Višina |
|---:|---|---:|---:|---:|---:|
| 1 | `sled-kroga.mp4` | 8,778 | 2,319 | 4,069 | 4,069 |
| 3 | `trend-sledenja.mp4` | 5,556 | 3,750 | 6,139 | 2,431 |
| 5 | `sledenje.mp4` | 3,167 | 1,444 | 9,333 | 5,250 |
| 6 | `kamera.mp4` | 3,167 | 1,444 | 9,333 | 5,250 |
| 7 | `zdravnik.mp4` | 3,167 | 1,444 | 9,333 | 5,250 |

Če vmesnik kaže **centimetre**:

| Diapozitiv | Datoteka | X | Y | Širina | Višina |
|---:|---|---:|---:|---:|---:|
| 1 | `sled-kroga.mp4` | 22,296 | 5,891 | 10,336 | 10,336 |
| 3 | `trend-sledenja.mp4` | 14,111 | 9,525 | 15,593 | 6,174 |
| 5 | `sledenje.mp4` | 8,043 | 3,669 | 23,707 | 13,335 |
| 6 | `kamera.mp4` | 8,043 | 3,669 | 23,707 | 13,335 |
| 7 | `zdravnik.mp4` | 8,043 | 3,669 | 23,707 | 13,335 |

Če vmesnik ne sprejme vejice, uporabi piko.

### 4. Samodejno predvajanje brez zvoka

Pri **vseh petih** videih v **Format options → Video playback**:

- izberi **Play (automatically)** (privzeto je *Play (on click)*),
- vklopi **Mute audio**.

### 5. Rezerva za animirani črti: GIF

Če se črta kot video ne predvaja prav, ima črne robove, gumbe ali okvir druge barve:

1. pobriši ta video,
2. **Insert → Image → Upload from computer** → `media/sled-kroga.gif` (diapozitiv 1) ali `media/trend-sledenja.gif` (diapozitiv 3),
3. vpiši iste mere in, če je placeholder še tam, ga pobriši kot v koraku 3.

GIF je zapisan za eno predvajanje, vendar se v Google Predstavitvah lahko ponavlja ali začne, preden prideš na diapozitiv.

### 6. Generalka

Predstavitev predvajaj čez cel zaslon **z računom in prenosnikom za nastop**, najbolje tudi na projektorju:

- vseh pet videov se začne samih, brez zvoka in brez opozorila o dostopu;
- na 1. in 3. diapozitivu ni vidnega pravokotnika okoli animacije;
- povezave spodaj vodijo na 2, 3, 4, 5 in 8;
- po vrnitvi na diapozitiv preveri, ali se video začne znova.

Videi potrebujejo internet. **Rezerva brez interneta je `predstavitev/index.html`**: na prenosnik kopiraj celo mapo `predstavitev/`, odpri datoteko v Chromu in pritisni `F`.

## Česar ni bilo mogoče ohraniti

**Videz**

- **Razmik med črkami:** Google ga ne podpira, zato so veliki naslovi približno 5 % širši (na 9. diapozitivu do 79 px). Prelomi so isti in velikosti ni bilo treba zmanjšati. Na naslovnici je med »Okrevanje« in krogom zato približno 17 px namesto 59 px. Če je v Googlu pretesno, naslov zmanjšaj z 82 na 80 pt.
- **Debeline pisave:** 500 je postala navadna (datumi v koledarju, oznake grafa), 600 krepka (»Počutje«, »Bolečina«).
- **Samodejno uravnotežen prelom** (`balance`, `pretty`): naslovi in nekateri odstavki imajo ročne prelome. Ob urejanju besedila jih popravi ročno.
- **Višina vrstic** je umerjena v PowerPointu, ne v Googlu (glej korak 1).
- **Zaobljeni robovi videov** na 5–7 so ravni, ker videov v Googlu ni mogoče zaobliti.
- **Besedilo v slikah:**
  - diapozitiv 1: »22. november«, »ista naloga, ista roka«, »(sintetični podatki)«;
  - diapozitiv 3: »njegovo izhodišče ± 5 točk«, »prag opozorila ob večdnevnem padcu«.

  Ta besedila so del animacije in niso urejljiva. Besedilo na sliki vaje z dlanjo in v zaslonskih posnetkih je bilo del slike že v izvirniku.
- **Grafika** (sledi, črte grafa, časovni trak, puščici) je v slikah PNG in se ne ureja po delih.
- **Barva videa na 1. diapozitivu** se z ozadjem ujema (do 1 stopnje) samo pri izvirni datoteki v Chromu oziroma na Macu. Predvajalnik brez Applovega barvnega upravljanja (npr. Windows) bo pokazal temnejši pravokotnik (približno `35,63,79` namesto `39,71,90`), preizkusna pretvorba v 640 px pa svetlejšega (`45,74,89`). Drive videe pretvarja, zato to preveri najprej. Če se pravokotnik vidi, uporabi GIF, ki ima točno barvo. Bel 3. diapozitiv te težave nima.

**Obnašanje**

- **Telefonska postavitev** za branje ne obstaja. Diapozitivi se samo pomanjšajo.
- **Tipka V** in klik za premor ali ponovitev po pravilih HTML odpadeta. Veljajo Googlove kontrole predvajalnika. Tudi tipka `F`, poteg in naslovi `#5` niso preneseni.
- **Zmanjšano gibanje:** nastavitev sistema se ne upošteva. Za različico brez gibanja pusti slike `REPLACE`.
- **Videi** se ne nalagajo vnaprej po pravilih HTML, se ob skritem zavihku ne ustavijo zanesljivo in lahko pokažejo Googlove gumbe.
- **Animaciji sta videa:** po 120 s se končata. Ob vrnitvi na diapozitiv se morda ne začneta znova.
- **Navigacija in števec** sta kopirana na vsak diapozitiv. Če dodaš ali premakneš diapozitiv, ju popravi ročno. Podčrtave ob prehodu miške ni.
- **Opis za bralnike zaslona** izgine s pobrisano sliko `REPLACE`. Če ga potrebuješ, ga prej kopiraj iz **Alt text** in prilepi na video.

## Kaj je bilo preverjeno in kaj ne

- Preverjeno na Macu: PowerPoint (izvoz v PDF), besedilo znak za znakom, povezave, animaciji v Chromu, HTML rezerva brez interneta.
- Hanken Grotesk na tem Macu ni nameščen. PowerPoint oddano datoteko pokaže v **Calibriju**, z ožjim besedilom in drugimi prelomi (desni stolpec `preview.png`). Za pravo primerjavo je bila pisava vdelana samo v preizkusno kopijo (srednji stolpec).
- **Ni preizkušeno:** uvoz v Google Predstavitve, videi iz Driva in njihova pretvorba, imena menijev v živem vmesniku, Windows, projektor.
