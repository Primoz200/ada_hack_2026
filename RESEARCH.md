# Raziskava: igre za objektivno spremljanje motoričnega okrevanja

Kratek povzetek. Celotno poročilo z vsemi številkami, tabelami in ~190 viri je v
[`reports/Igre za motorično rehabilitacijo.md`](reports/Igre%20za%20motori%C4%8Dno%20rehabilitacijo.md),
surovi zapiski po temah pa v [`research_notes/Igre za motorično rehabilitacijo/`](research_notes/Igre%20za%20motori%C4%8Dno%20rehabilitacijo/).

## Zakaj igre namesto lestvic 1–10

Samoporočanje je za zaznavanje majhnih, postopnih motoričnih sprememb slabo orodje. V študiji s skritimi pospeškomeri so
dnevniki precenili število vaj, samoocena na lestvici 0–10 pa je imela omejeno veljavnost in nezadostno test-retest
zanesljivost ([Nicolson 2018](https://europepmc.org/article/MED/30053792)). Lestvica je ordinalna, ljudje jo uporabljajo
različno, sprememba za 1 točko pa je znotraj šuma. Okrevanje roke po kapi je najhitrejše v prvih 6–10 tednih, torej ravno po
odpustu ([Kwakkel](https://research.vu.nl/ws/files/2237827/196230.pdf)), zato redki klinični pregledi potek vzorčijo
preredko. Dnevne objektivne meritve iz igre dajo krivuljo za posameznega bolnika in zgodnje opozorilo ob poslabšanju.
RCT, ki bi neposredno primerjal tako spremljanje s samoporočanjem pri kapi, CTR ali CIPN, ne obstaja – to je naša priložnost.

## Igrificirana rehabilitacija deluje

Cochranov pregled 2025 (190 RCT, 7.188 udeležencev): igre in VR, **dodane** običajni terapiji, izboljšajo funkcijo zgornjega
uda z zmernim učinkom (SMD 0,42), pri ravnotežju še bolj (SMD 0,68) ([Laver 2025](https://europepmc.org/article/MED/40537150)).
Igre, ki upoštevajo načela nevrorehabilitacije (stopnjevanje težavnosti, povratna informacija), imajo večje učinke
([Doumas 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8204490/)). Domača telerehabilitacija z igrami je bila po kapi
enakovredna kliniki, z 98 % adherenco ([Cramer 2019](https://pubmed.ncbi.nlm.nih.gov/31233135/)). Pri CIPN vadba zmanjša
simptome (SMD −0,62, [Huang 2023](https://europepmc.org/article/MED/38283674)), senzomotorični trening pa je incidenco CIPN
znižal s 71 % na 30 % ([Streckmann 2024](https://europepmc.org/article/MED/38949824)). Po CTR so dokazi manjši, a vadba z
aplikacijo je izboljšala QuickDASH za 21 točk bolj kot papirnata navodila (Blanquero 2019, avtorja/DOI preveriti).

## Priporočene tri igre

**1. Sledi poti (tracing + Fittsovo ciljanje).** Stopnje: črta → kvadrat v kanalu → krog → spirala → labirint. Meri čas,
RMS odstopanje od poti, gladkost (jerk, SPARC), vrhove hitrosti in throughput. Pri kapi se kinematika dosega na zaslonu
ujema s Fugl-Meyer ([Goizueta 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11817959/)), jerk je najbolj koreliral z
okrevanjem (r = 0,48, [Rohrer 2002](https://www.jneurosci.org/content/jneuro/22/18/8297.full.pdf)). Pri CTS je spirala s
SVM dosegla 82 % občutljivosti in 71 % specifičnosti ([Watanabe 2021](https://www.mdpi.com/2077-0383/10/19/4437)).
Opozorilo: validiranega testa na miško ni, MVP z miško je naša prilagoditev. Wow: toplotni zemljevid hitrosti na sledi in
»duh« izhodiščnega poskusa.

**2. MediaPipe kamera.** Način »ritem prstov« (razdalja palec–kazalec, MediaPipe Hands) je najzrelejša videonaloga: pri PD
80 % točno in 93 % ±1 točnost, medtem ko sta se dva nevrologa ujemala le v 52 %
([Yu 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10674854/)); pri CIPN je tapping nosil 85 % pomembnosti modela rok
([Chen 2025](https://www.jmir.org/2025/1/e65615)). Način »doseži zvezde« (MediaPipe Pose) meri abdukcijo ramena,
kompenzacijo trupa in simetrijo pri kapi. MediaPipe je zanesljiv (ICC 0,75–0,96), absolutni koti pa imajo napako do
15–20°, zato rezultat podajamo kot % lastnega izhodišča. Wow: okostje v živo in »EKG prstov«.

**3. Telefon kot krmilnik (DeviceOrientation/DeviceMotion).** »Zapestni sef« za ROM po CTR (WristCheck ICC 0,76–0,95,
boljše od goniometra; [Engstrand 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8649412/)), »drži kozarec« za tremor
in »ravnotežni surfer« za CIPN (nihanje z zaprtimi očmi 94 % slabše, [Zahiri 2019](https://doi.org/10.1016/j.jgo.2019.01.010);
igra s senzorsko povratno informacijo je zmanjšala nihanje, [Schwenk 2016](https://doi.org/10.1159/000442253)). Wow: QR koda
na zaslonu, telefon postane krmilnik. Omejitve: iOS zahteva `requestPermission()` prek HTTPS, frekvenco vzorčenja na iOS
je treba izmeriti. Rezerva, če zmanjka časa: tapping na dotik.

## Podatki in ML

Javnega niza z bolniki po kapi, CTR ali CIPN pri takih igrah **ni**. Najbližji približki so UCI spirale in HandPD (PD,
igra 1), KIMORE (edini z bolniki po kapi in kliničnimi ocenami, igra 2) ter mPower/Tappy (tapping). Uporabni so za
preverjanje razumnosti, ne za glavno učenje – zato je načrt s sintetičnimi podatki iz pravil smiseln. Generator temelji na
trajektoriji minimalnega jerka, ki ji po resnosti dodamo počasnejšo hitrost, podgibe, lateralno odstopanje in tremor
(4–12 Hz). Smeri učinkov so podprte z literaturo, pragi blago/zmerno/hudo pa so naše predpostavke.

Priporočen pristop: značilčni baseline (gradient boosting) + 1D-CNN na zaporedjih, stopnja kot vhod, izhod ocena 0–100 in
razred. Glavni klinični signal je **trend glede na bolnikovo lastno izhodišče** (z-vrednost/RCI, EWMA), ker se amplituda
tremorja med ljudmi razlikuje za 331 %
([van Brummelen 2020](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7137336/)).

## Omejitve

CNN, naučen samo na sintetiki, se nauči pravil generatorja – preveriti ga je treba na realnih nizih in na lastnih posnetkih
s simulirano okvaro (nedominantna roka, utež). Igre niso validirani diagnostični inštrumenti, temveč spremljajo spremembe.
Pri več številkah celotno besedilo ni bilo dostopno; v polnem poročilu so označene.
