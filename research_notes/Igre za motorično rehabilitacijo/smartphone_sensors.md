# Smartphone motion sensors (accelerometer, gyroscope, IMU) and touchscreen tasks for motor assessment and rehab games

Scope: tremor, hand steadiness, balance/postural sway, gait, upper-limb movement, wrist ROM with the phone held in the hand. Populations: stroke, post carpal tunnel release (CTR), chemotherapy-induced peripheral neuropathy (CIPN). Context: hackathon web app with 3 games (tracing, webcam MediaPipe, and a third that may use motion sensors).

Note on method: PMC full-text pages returned a reCAPTCHA wall, so most numbers below come from Europe PMC REST abstracts (bibliographic data verified) or search-engine summaries of the papers. Where a number comes only from a search summary and I could not check it against an abstract, it is marked "(search summary, not verified against the abstract)".

---

## Q1. Validity numbers for smartphone tremor, balance and wrist ROM measurement

### Takeaway
Smartphone accelerometry agrees closely with lab accelerometers for tremor *frequency*, but tremor *amplitude* varies a lot within a person. Smartphone sway correlates moderately to strongly with force plates (rho about 0.42-0.81) but is less reliable test-retest (ICC about 0.72-0.75 for quiet stance), so it needs longer or repeated trials. Phone goniometry for the wrist is reliable in healthy adults (ICC about 0.76-0.96; r >= 0.80 against a universal goniometer). Validation in patients is thin.

### Cited Findings
**Tremor**
- van Brummelen EMJ, Ziagkos D, de Boon WMI, et al. (2020). "Quantification of tremor using consumer product accelerometry is feasible in patients with essential tremor and Parkinson's disease: a comparative study." *J Clin Mov Disord* 7:4. DOI 10.1186/s40734-020-00086-7. N = 10 PD + 10 ET. Seven consumer devices (iPhone, iPod Touch, Apple Watch, etc.) were compared with a Biometrics ACL300 lab accelerometer. Peak frequency did not differ significantly from the lab device (limits of agreement). Between- vs within-subject variability: frequency 25.1% vs 13.4%, amplitude 331% vs 53.6%. Intra-individual variability at rest vs extended arm: frequency 13.4% vs 17.8%, amplitude 53.5% vs 58.1%. — [Europe PMC / PMC7137336](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7137336/)
- Barrantes S, Sánchez Egea AJ, González Rojas HA, et al. (2017). "Differential diagnosis between Parkinson's disease and essential tremor using the smartphone's accelerometer." *PLoS ONE* 12(8):e0183843. DOI 10.1371/journal.pone.0183843. iPhone 5S, 30 s at rest + 30 s arm stretched. N = 17 PD, 16 ET, 12 healthy, 7 undecided. Tremor vs no tremor: 49/52 correctly classified (sensitivity 97.96%, specificity 83.3%). PD vs ET: 27/32 (84.38% accuracy). — [PMC5571972](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5571972/)
- Sahin G, Halje P, Uzun S, et al. (2022). "Tremor evaluation using smartphone accelerometry in standardized settings." *Front Neurosci* 16:861668. DOI 10.3389/fnins.2022.861668. Compared smartphone recordings with finger-worn inertial sensors and clinical ratings in PD and ET. Amplitude and regularity had a correlation coefficient of 1 with the reference, and frequency-domain features (median power frequency, power dispersion, harmonic index) had r > 0.95 (search summary, not verified against the abstract). The authors concluded the descriptors are reliable enough for closed-loop DBS control. — [PubMed 35979340](https://pubmed.ncbi.nlm.nih.gov/35979340/)
- An International Parkinson and Movement Disorder Society task force, Haubenberger D, Abbruzzese G, ... Elble RJ (2016). "Transducer-based evaluation of tremor." *Mov Disord*. DOI 10.1002/mds.26671. Accelerometry, gyroscopy, EMG and digitizing tablets met its validity criteria. Transducers are "far more sensitive to changes in tremor amplitude and frequency" than rating scales. — [doi.org/10.1002/mds.26671](https://doi.org/10.1002/mds.26671)

**Balance / postural sway**
- Shafi H, Awan WA, Olsen S, et al. (2023). "Assessing Gait & Balance in Adults with Mild Balance Impairment: G&B App Reliability and Validity." *Sensors* 23(24):9718. DOI 10.3390/s23249718. N = 83, aged 50-75, Berg Balance Scale 46-54. ICCs: eyes-closed steadiness 0.72 (firm) and 0.75 (compliant); gait symmetry 0.65; walking speed 0.93; step length 0.94; step time 0.84. Walking speed vs Timed Up and Go r = -0.70; vs Berg r = 0.55. — [PDF](https://vbn.aau.dk/ws/files/626082594/sensors-23-09718-v2.pdf)
- A smartphone study in 30 older adults found moderate-to-strong correlations with a force plate under challenging balance conditions (rho = 0.42-0.81) (search summary, not verified against the abstract). — [PMC10747653](https://pmc.ncbi.nlm.nih.gov/articles/PMC10747653)
- In about 100 older adults, smartphone test-retest ICC was lower than the force plate's, but both detected differences between conditions equally well. The authors advised more repetitions or longer trials with a smartphone (search summary, not verified against the abstract). — [bioRxiv 2020.05.29.123620](https://www.biorxiv.org/content/10.1101/2020.05.29.123620.full.pdf)
- "Smartphone technology can measure postural stability and discriminate fall risk in older adults" (Gait & Posture, 2019). — [PubMed 30340129](https://pubmed.ncbi.nlm.nih.gov/30340129/)
- SWAY Balance (accelerometer app) vs Biodex force plate: valid for progressively harder single-leg stance, but not sensitive enough for smaller sway changes in double-leg stance (search summary, not verified against the abstract). — [PMC6942738](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6942738/)

**Wrist ROM (phone in hand / on the forearm)**
- Engstrand F, Tesselaar E, Gestblom R, et al. (2021). "Validation of a smartphone application and wearable sensor for measurements of wrist motions." *J Hand Surg Eur* 46(10):1057-1063. DOI 10.1177/17531934211004454. N = 33 healthy adults, compared with a goniometer. Test-retest ICC 0.76-0.95 (0.90-0.96 on day 2). Day-to-day mean ICC: wearable sensor 0.87, app alone 0.82, goniometer 0.60. The app ("WristCheck") uses the phone's built-in motion sensors. — [PMC8649412](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8649412/)
- Goniometer Pro iPhone app (2017), asymptomatic adults: intra-rater ICC >= 0.83 (universal goniometer >= 0.82), inter-rater ICC >= 0.79 (0.73), concurrent validity r >= 0.80 (search summary, not verified against the abstract). — [PMC5314391](https://pmc.ncbi.nlm.nih.gov/articles/PMC5314391) / [PubMed 27910103](https://pubmed.ncbi.nlm.nih.gov/27910103/)
- Angulus app (Cureus, 2024), 64 volunteers: validity against a goniometer 0.44-0.81, depending on the motion (search summary, not verified against the abstract). — [PMC11088398](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11088398/)
- Protractor app in outpatients after fracture: excellent within-visit reliability for most wrist motions but weak for wrist flexion (search summary, not verified against the abstract). — [Sport TK](https://revistas.um.es/sportk/article/download/589561/361531/2306581)

### Inferences
- For a game score, peak tremor frequency is robust, but raw amplitude is noisy (about 54% intra-subject variability). Use within-person baselines, several trials and a median, and show progress relative to the user's own baseline.
- A balance score from a hand-held phone is weaker than one from a phone strapped at the lumbar spine or sternum. Smartphone sway work usually fixes the phone to the trunk.
- Wrist ROM from phone orientation (beta/gamma angles) is the best-validated "phone in hand" measure for a demo.

### Gaps
- No ICC or validity data found for phone sensors accessed through a **web browser** (all studies used native apps).
- Smartphone tremor correlations with clinical scales (TETRAS, MDS-UPDRS item 3.15-3.18) were not extracted, because full texts were blocked.

---

## Q2. CIPN studies with smartphone or wearable balance/tremor

### Takeaway
CIPN clearly impairs sway and gait as measured by wearables. A smartphone app (NeuroDetect) separated CIPN cases from controls with gait/sway acceleration features and a virtual 9-hole peg test in a small pilot. Sensor-feedback balance *games* improved sway in a pilot RCT in older cancer patients with CIPN, which is the closest precedent for a balance game.

### Cited Findings
- Chen CS, Kim J, Garg N, ... Hertz DL (2021). "Chemotherapy-Induced Peripheral Neuropathy Detection via a Smartphone App: Cross-sectional Pilot Study." *JMIR mHealth uHealth* 9(7):e27502. DOI 10.2196/27502. iPhone ResearchKit app "NeuroDetect", N = 26 (17 CIPN, 9 controls by CIPN20). Step length 0.54 m vs 0.78 m (P = .007, n = 12). Sway-axis acceleration in cases: higher median frequency (P = .009), lower max frequency (P = .007), lower skewness (P = .004) and kurtosis (P = .007), higher Shannon entropy (P = .01). PLS-DA leave-one-out R² = 0.590. Virtual 9-hole peg test on the touchscreen: peg-removal distance and speed variability lower in cases (P = .001 to <.001). Exploratory, no multiple-comparison correction. 7 of 23 recordings were excluded because of phone handling, which shows that phone placement matters. — [PMC8406129](https://pmc.ncbi.nlm.nih.gov/articles/PMC8406129)
- A 2025 observational cohort with NeuroDetect supported longitudinal remote CIPN monitoring (search summary, not verified against the abstract). — [JMIR 2025;e65615](https://www.jmir.org/2025/1/e65615)
- Zahiri M, Chen KM, Zhou H, et al. (2019). "Using wearables to screen motor performance deterioration because of cancer and CIPN in adults - Toward an early diagnosis of CIPN." *J Geriatr Oncol* 10(6):960-967. DOI 10.1016/j.jgo.2019.01.010. N = 84 cancer patients vs 57 controls. Stride time 11% worse (Cohen's d = 1.00, p < .001). **Eyes-closed ankle sway 94% worse (d = 0.49, p = .001)**. Vibration threshold correlated with stride time (rho = 0.37). Severe CIPN worse than mild (p < .05). — [doi.org/10.1016/j.jgo.2019.01.010](https://doi.org/10.1016/j.jgo.2019.01.010)
- Schwenk M, Grewal GS, Holloway D, et al. (2016). "Interactive Sensor-Based Balance Training in Older Cancer Patients with CIPN: A Randomized Controlled Trial." *Gerontology*. DOI 10.1159/000442253. N = 22, mean age 70.3. Wearable sensors gave real-time visual/auditory feedback during **game-based** weight-shifting exercises. Hip, ankle and CoM sway (feet together, eyes open) fell more than in controls (p = .010-.022). Semi-tandem sway also fell (p = .008-.035). No effect on eyes-closed balance, gait speed or fear of falling. — [doi.org/10.1159/000442253](https://doi.org/10.1159/000442253)
- Winters-Stone KM, Horak F, Jacobs PG, et al. (2017). "Falls, Functioning, and Disability Among Women With Persistent Symptoms of CIPN." *J Clin Oncol*. DOI 10.1200/JCO.2016.71.3552. N = 512 survivors, 47% with CIPN symptoms. **1.8x fall risk** (P < .0001). Slower gait with shorter steps. Severity was linearly associated with function and falls. — [doi.org/10.1200/JCO.2016.71.3552](https://doi.org/10.1200/JCO.2016.71.3552)
- Lumbar APDM Opal IMU in 434 older female survivors: sway components relate to CIPN and falls. In a 425-woman analysis, CIPN-symptomatic survivors had **higher sway frequency**, while past fallers had larger sway area and slower gait (search summary; I could not verify which of the two PMC links holds which analysis). — [PMC6639160](https://pmc.ncbi.nlm.nih.gov/articles/PMC6639160), [PMC6579642](https://pmc.ncbi.nlm.nih.gov/articles/PMC6579642)

### Inferences
- In CIPN the signal shows up most in **eyes-closed** stance and in sway *frequency*, not only amplitude. An "eyes-closed hold" mode with audio feedback, and frequency features in the ML model, are well supported.
- Fine-motor deficits are detectable on the touchscreen (virtual 9-hole peg). The tracing game already covers this for CIPN.

### Gaps
- No smartphone **tremor** studies in CIPN were found. CIPN tremor is not a primary feature in the literature retrieved.
- No browser-based CIPN tool was found.

---

## Q3. Stroke upper-limb smartphone/IMU tasks and games

### Takeaway
The evidence is mostly small and preliminary. Phones used as motion controllers for arm games are feasible and show FMA-UE gains in pilot work. Wearable-accelerometer home games beat paper home programs in an RCT. No large validation of a smartphone-sensor upper-limb *score* against FMA-UE was found.

### Cited Findings
- A preliminary Korean study used a smartphone's built-in sensors to track arm movement and drive a tablet game over Bluetooth. Upper-limb function improved significantly, but quality of life did not (search summary, not verified against the abstract). — [KoreaScience JAKO201535151757328](https://koreascience.kr/article/JAKO201535151757328.page?lang=en)
- Frontiers in Rehabilitation Sciences (2023): 12 stroke survivors did a serious mobile game session vs a conventional session. The game activated motor cortex but did not directly raise muscle activity. Levels were mapped to FMA severity bands (search summary, not verified against the abstract). — [Frontiers 10.3389/fresc.2023.1234216](https://www.frontiersin.org/articles/10.3389/fresc.2023.1234216/endNote)
- JMIR Serious Games (2021): a cellphone-based augmented-reality serious game vs conventional occupational therapy, with FMA-UE, ARAT, MMT and Brunnstrom as outcomes. Long-term effects were reported (search summary, not verified against the abstract). — [games.jmir.org 2021/4/e30184](https://games.jmir.org/2021/4/e30184/PDF)
- An RCT of "puck" accelerometer game devices in subacute stroke: greater UE Fugl-Meyer gains than a paper home program (search summary, not verified against the abstract). — [Neurorehabil Neural Repair 10.1177/15459683221146995](https://journals.sagepub.com/doi/10.1177/15459683221146995)
- A smartwatch + smartphone system used a CNN on accelerometer/gyroscope data to recognize home exercises, with UEFM tracked over 12 months (search summary, not verified against the abstract). — [PMC9999258](https://pmc.ncbi.nlm.nih.gov/articles/PMC9999258)
- El-Sherbini AEIEM, Taha SI, Habib DAA (2026). "Smartphone-Based Semi-Immersive Virtual Reality Enhances Upper Extremity Function in Subacute Stroke: RCT." *NeuroRehabilitation*. DOI 10.1177/10538135261456309. N = 57 (FMA-UE 20-50). The VR group improved more on FMA-UE, Purdue Pegboard and grip strength, with large effects. Gaze-driven interaction, not motion sensors. — [doi.org/10.1177/10538135261456309](https://doi.org/10.1177/10538135261456309)
- Cochrane: Laver KE et al. (2020). "Telerehabilitation services for stroke." DOI 10.1002/14651858.CD010255.pub3. Upper-limb function (3 studies, 170 participants): MD 1.23 (95% CI -2.17 to 4.64). Low-quality evidence, no clear difference from in-person care. — [doi.org/10.1002/14651858.CD010255.pub3](https://doi.org/10.1002/14651858.CD010255.pub3)
- Chile pilot: smartphone exergames for balance in 10 stroke patients, 6-8 weeks post-stroke, at home. — [PMC7690853](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7690853/)

### Inferences
- A phone held in the paretic hand works as a "motion controller" (tilt, rotate, reach) and fits the existing evidence for stroke. Grip safety (a strap or lanyard) and a seated position are sensible for a demo.
- Level difficulty can be adapted to the user (for example, tilt range needed) in the way the Frontiers study mapped levels to FMA bands.

### Gaps
- No smartphone-IMU upper-limb score with a published correlation to FMA-UE/ARAT was retrieved.

---

## Q4. Smartphone gyroscope goniometry for wrist ROM after carpal tunnel release

### Takeaway
No study was found that tracks wrist ROM with phone sensors over time after CTR. Phone wrist goniometry is validated in healthy people (WristCheck, ICC 0.76-0.96), and a validation in CTS/RA patients is registered. Post-CTR app/tablet programs exist: one RCT found the ReHand tablet app better than a home exercise program for function.

### Cited Findings
- WristCheck: Engstrand et al. 2021 (see Q1), healthy adults only. — [PMC8649412](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8649412/)
- NCT05819242: Angulus smartphone app vs goniometer in rheumatoid arthritis and carpal tunnel syndrome. No results posted. — [ClinicalTrials.gov NCT05819242](https://clinicaltrials.gov/study/NCT05819242)
- ReHand tablet app RCT after CTR (J Physiother, 2019): more effective for functional recovery than a conventional home program. Benefit for grip, pain and dexterity was unclear (search summary, not verified against the abstract). — [Australian Physiotherapy Assoc. summary](https://australian.physio/inmotion/tablet-based-exercise-after-carpal-tunnel-release); [DOAJ](https://doaj.org/article/1f302258f47c48398a203b73c604bfcc)
- Post-CTR smartphone care app (J Telemed Telecare 2020, 26(4):223-231): wound photo, symptom report, and finger ROM video. 14 of 16 patients captured the ROM video (search summary, not verified against the abstract). — [Univ. Iowa record](https://iro.uiowa.edu/esploro/outputs/journalArticle/Postoperative-care-via-smartphone-following-carpal/9984001230402771)
- NCT07899203: "Effect of Progressive Gamified Motor Rehabilitation After Carpal Tunnel Release." Registered, no results seen. — [ClinicalTrials.gov NCT07899203](https://clinicaltrials.gov/study/NCT07899203)

### Inferences
- Post-CTR rehab uses tendon/nerve-gliding and wrist flexion/extension. A "phone in hand" wrist-rotation game that reports peak flexion, extension, pronation and supination angles each session is a plausible, novel demo, built on validated measurement principles.
- Measurement caveat: with the phone held in the hand, forearm rotation and elbow motion can contaminate the wrist angle. Ask the user to rest the forearm on a table edge (as goniometry protocols do).

### Gaps
- No longitudinal post-CTR phone-sensor ROM data, and no MCID for phone-measured wrist ROM, were found.

---

## Q5. Tremor frequency bands, required sampling rates, browser sensor rates and iOS permission

### Takeaway
Pathological tremor sits at about 3-12 Hz (PD rest about 4-6 Hz, ET 4-12 Hz, physiological/enhanced physiological about 6-12 / 8-12 Hz). A filter band of about 2-30 Hz is recommended, so about 60 Hz sampling (Nyquist 30 Hz) is just enough. Browsers usually deliver DeviceMotion at about 60 Hz on Chrome/Android (16.6 ms interval). iOS Safari historically delivered less (a 2015 report says 20 Hz for orientation events). The current rate must be measured on the device. iOS 13+ requires `DeviceMotionEvent.requestPermission()` / `DeviceOrientationEvent.requestPermission()` from a user gesture over HTTPS.

### Cited Findings
- Tremor bands: PD tremor 4-6 Hz (3-6 Hz in an ML paper), ET 4-12 Hz with frequency falling with age, physiological tremor 6-12 Hz with enhanced physiological 8-12 Hz (search summary, not verified against the abstract). — [PMC6923291 (table)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6923291/table/t0005); [arXiv 2501.18671](https://arxiv.org/pdf/2501.18671); [PubMed 9827594 "Overview of human tremor physiology"](https://pubmed.ncbi.nlm.nih.gov/9827594/)
- Accelerometry peak frequency: ET 10.6 ± 2.5 Hz vs classic parkinsonian tremor 5.4 ± 0.8 Hz (20 per group) (search summary, not verified against the abstract). — [PMC10611060 / related](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10611060/)
- An NINDS-based methods review recommends a 2 Hz high-pass and 30 Hz low-pass filter for accelerometer tremor recordings, with slow voluntary movement to keep it separate from tremor (search summary, not verified against the abstract). — [PMC5901940](https://pmc.ncbi.nlm.nih.gov/articles/PMC5901940)
- PD and ET frequencies overlap (4-6 Hz), so classifiers combine frequency with amplitude, posture and other features. — [Barrantes 2017, PLoS ONE](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5571972/)
- MDN: `DeviceMotionEvent.interval` is the read-only interval in ms at which data comes from the hardware. The web API has no way to set the rate. — [MDN DeviceMotionEvent.interval](https://developer.mozilla.org/docs/Web/API/DeviceMotionEvent/interval)
- MDN: `DeviceOrientationEvent.requestPermission(absolute?)` returns a Promise of "granted" or "denied". It needs transient activation (for example, a button click), or it rejects with NotAllowedError. Secure context (HTTPS) only. Not Baseline ("limited availability"). Check `typeof ... === "function"` before calling, because browsers that don't need permission don't implement it. `DeviceMotionEvent.requestPermission()` is the equivalent for motion data. — [MDN requestPermission](https://developer.mozilla.org/en-US/docs/Web/API/DeviceOrientationEvent/requestPermission_static); [MDN DeviceMotionEvent](https://developer.mozilla.org/docs/Web/API/DeviceMotionEvent)
- W3C Device Orientation and Motion spec: access now integrates with Permissions Policy and requires explicit user consent through requestPermission(). — [W3C WD 2024](https://www.w3.org/TR/2024/WD-orientation-event-20240509/)
- Chrome/Android uses 60 Hz for these sensors, and a Chrome 76 test showed about 60 fps. Firefox Android's rate was changed from 200 Hz to 60 Hz "like Chrome". — [Mozilla Bug 1515780](https://bugzilla.mozilla.org/show_bug.cgi?id=1515780)
- 2015: `DeviceMotionEvent.interval` reported 16.6 ms on Chrome and 100 ms on Firefox Android. — [Mozilla Bug 1217942](https://bugzilla.mozilla.org/show_bug.cgi?id=1217942)
- 2015 WebKit bug: iOS Safari emitted DeviceOrientation at 20 Hz, and the reporter requested 60 Hz. Current status not confirmed. — [WebKit Bug 145814](https://bugs.webkit.org/show_bug.cgi?id=145814)
- Native iOS (not web): third-party apps get accelerometer data at up to about 100 Hz (forum report of an Apple DTS statement). Requested 60/80 Hz gave actual intervals of 19/15 ms. — [Apple forum 813136](https://developer.apple.com/forums/thread/813136); [Apple forum 122765](https://developer.apple.com/forums/thread/122765)

### Inferences
- At 60 Hz a browser can resolve tremor up to 30 Hz, which covers all clinical bands, but leaves little margin. If iOS delivers less than about 25-30 Hz, the 8-12 Hz band will alias, so the tremor ("hold steady") score is less reliable on iOS. Log `event.interval` and actual timestamps, and resample to a uniform grid before an FFT/Welch analysis.
- Tilt-control games (maze, balance-the-ball) work fine at 20-60 Hz because they need orientation, not spectral detail.
- Implementation: a "Start / Enable motion" button that calls `DeviceMotionEvent.requestPermission()` and `DeviceOrientationEvent.requestPermission()` in the same click handler; HTTPS (also needed for webcam/MediaPipe); a desktop fallback (mouse/keyboard or a QR code to open on the phone); and a screen orientation lock or a hint, because beta/gamma axes swap in landscape.

### Gaps
- No recent, authoritative measurement of iOS Safari's DeviceMotion rate (2024-2026) was found. Test on real devices.
- The Generic Sensor API (`Accelerometer`, `Gyroscope` with a `frequency` option) is an alternative on Chromium, not researched here.

---

## Q6. Phone-tilt exergames: effectiveness, engagement and game designs

### Takeaway
No RCT of a "tilt-maze" phone game for rehab was found. The building blocks are evidence-based: an iPhone-accelerometer tilt-feedback balance trainer (JNER 2012), sensor-feedback balance games in CIPN (Schwenk 2016), smartphone exergames in stroke (pilot), and phone-as-controller arm games in stroke (pilots). The game ideas below are inferences.

### Cited Findings
- "Cell phone based balance trainer" (J NeuroEng Rehabil, Feb 2012): an iPhone accelerometer estimated trunk tilt and gave vibrotactile cues when tilt crossed a threshold, for clinic and home balance rehab. — [PMC3340298](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3340298/)
- Schwenk et al. 2016 (CIPN, game-based sensor-feedback weight shifting) improved sway (see Q2). — [doi.org/10.1159/000442253](https://doi.org/10.1159/000442253)
- Smartphone exergames + telerehab for balance after stroke, pilot with 10 patients. — [PMC7690853](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7690853/)
- NCT04146454 protocol: smartphone-linked wearable for in-home weight-shifting exercises in PD (22 planned), measuring bidirectional tilt. — [protocol PDF](https://cdn.clinicaltrials.gov/large-docs/54/NCT04146454/Prot_SAP_000.pdf)
- A systematic search on smartphone/tablet balance and gait rehab started from 806 records, and the inclusion criteria narrowed this to a small evidence base. — [PMC10604191](https://pmc.ncbi.nlm.nih.gov/articles/PMC10604191)

### Inferences (game designs for the demo, built on the evidence above)
1. **Tilt-maze / balance-the-ball (wrist + upper-limb control).** The phone is held flat in the hand. A marble rolls through a maze with physics (`gamma`/`beta` give acceleration). Targets are placed at the edges of the user's calibrated ROM, so they reach their limits. Metrics: time, wall hits, path smoothness (jerk), max tilt reached per direction (proxy ROM). For stroke and post-CTR. Wow factor: realistic 3D marble physics (three.js/cannon-es), haptics via `navigator.vibrate` on Android (iOS Safari doesn't support it).
2. **"Hold Steady" / candle or water-glass game (tremor and steadiness).** The arm is held outstretched with the phone. A virtual glass of water spills or a candle flame flickers in proportion to high-pass acceleration RMS. A live spectrum shows the peak frequency (4-6 Hz vs 8-12 Hz band). Metrics: RMS amplitude in the 3-12 Hz band, peak frequency, spectral entropy (CIPN data favour frequency/entropy features). Caveat: on iOS the sampling rate may limit this.
3. **Wrist rotation "dial" or "safe-cracker" (pronation/supination, flexion/extension).** The forearm rests on a table. The user rotates the phone to turn a dial or steer, and must hit and hold target angles. Metrics: peak angles (directly comparable with goniometer norms, validated by WristCheck), time to target, overshoot. Fits post-CTR well.
4. **Phone-on-chest "Balance surfer" (postural sway, CIPN).** The phone is held against the sternum or in a waistband. Standing sway moves a surfer or tightrope walker. Progressive stances (feet together, then semi-tandem, then eyes closed with audio feedback) mirror the Schwenk 2016 protocol. Metrics: sway area, path length, mean frequency. Safety: stand near a wall or chair.
- ML hook: features (RMS, peak frequency, jerk, ROM, sway area) per attempt go into a per-user progress model, normalized to the first-session baseline, because between-subject amplitude variability is huge (331%; van Brummelen 2020).

### Gaps
- No engagement or adherence data specific to phone-tilt games were found.
- No direct evidence that a tilt-maze improves outcomes. Present it as a measurement plus motivation tool, not a proven therapy.
