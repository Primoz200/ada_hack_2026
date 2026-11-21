# Public datasets and synthetic-data parameters for ML motor-performance scoring in rehab games

Scope: (1) public datasets usable to train/validate models that score motor performance in a tracing game, a webcam pose game and a tapping/IMU game; (2) quantitative parameters for rule-based synthetic impaired vs. healthy data; (3) methods papers on synthetic generation, augmentation and ML scoring of drawings.

Source note: items marked **[verified]** were confirmed via web search/fetch in this session. Items marked **[bg]** are well-known references cited from background knowledge with DOIs, and were NOT re-opened in this session (PMC and Springer full texts were blocked by captcha/login redirects). The report writer should treat [bg] numbers as needing a spot-check before publication.

## Key Question 1: Which public datasets can train/validate ML motor scoring (drawing/spiral, tapping, mouse, rehab pose, stroke kinematics, IMU tremor)?

### Takeaway
No public dataset matches the target population (stroke / post-CTS release / CIPN) and the game modalities exactly. The closest proxies are: **Parkinson spiral/handwriting tablet datasets** (x, y, t, pressure) for the tracing game; **KIMORE** (has stroke patients and continuous clinician scores 0–50) plus **IntelliRehabDS** and **UI-PRMD** for the pose game; and **mPower** tapping and **Tappy** for the tapping game. They are all small (tens of subjects) and mostly Parkinson's disease (PD). That supports the plan to pretrain on rule-based synthetic data and use these datasets for sanity checks or fine-tuning, not as the main training set.

### Cited Findings

**Drawing / spiral / handwriting (for the tracing game)**

| Dataset | Subjects | Sensor / signals | Labels | Access / license | Source |
|---|---|---|---|---|---|
| UCI "Parkinson Disease Spiral Drawings Using Digitized Graphics Tablet" (Isenkul, Sakar, Kursun 2014) | 62 PD + 15 healthy (77 instances) | Wacom Cintiq 12WX; Static Spiral Test, Dynamic Spiral Test, Stability Test; text files of x, y, z, pressure, grip angle, timestamp, test ID; PWP spiral images also included | PD vs healthy | UCI, DOI 10.24432/C5Q01S; loader `ucimlrepo` id 395; UCI datasets are CC BY 4.0 | [verified] [UCI 395](https://archive.ics.uci.edu/dataset/395/parkinson+disease+spiral+drawings+using+digitized+graphics+) |
| UCI "Improved Spiral Test Using Digitized Graphics Tablet" (Kursun) | 25 PD + 15 healthy (per survey) | Same tablet SST/DST; images of PWP drawings | PD vs healthy | UCI DOI 10.24432/C5HW3N | [verified] [UCI 358](https://archive.ics.uci.edu/dataset/358/improved+spiral+test+using+digitized+graphics+tablet+for+monitoring+parkinson+s+disease); counts from [arXiv 2502.10703 survey](https://arxiv.org/pdf/2502.10703) |
| HandPD (Pereira et al. 2016) | 92 (18 healthy, 74 PD) | Form with 4 spirals + 4 meanders, scanned and cropped to JPG; 736 images | PD vs healthy | Free for research from UNESP page | [verified] [HandPD page](https://wwwp.fc.unesp.br/~papa/pub/datasets/Handpd/); paper [bg] Pereira et al. 2016, Comput Methods Programs Biomed 136:79–88, DOI 10.1016/j.cmpb.2016.08.005 |
| NewHandPD | 66 (35 healthy, 31 PD); 264 images + 12 smart-pen signal recordings per person | Images (spirals, meanders, circles) + BiSP smart-pen signals | PD vs healthy | Same UNESP page | [verified] [HandPD page](https://wwwp.fc.unesp.br/~papa/pub/datasets/Handpd/). Counts differ across papers (e.g. 37 PD / 35 HC): [arXiv 2505.00525](https://arxiv.org/pdf/2505.00525) |
| PaHaW (Drotár et al. 2016) | 37 PD + 38 age/sex-matched HC | Wacom Intuos 4M; x, y, time, button (on-surface/in-air), pressure, altitude, azimuth; 150 vs 200 Hz reported inconsistently; Archimedean spiral + Czech letters/words/sentences | PD vs HC (+ UPDRS) | On request from Brno group (licence agreement) | [verified] details via [arXiv 2311.11756](https://arxiv.org/pdf/2311.11756) and [arXiv 2309.14288](https://arxiv.org/pdf/2309.14288); primary [bg] Drotár et al. 2016, Artif Intell Med 67:39–46, DOI 10.1016/j.artmed.2016.01.004 |
| DraWritePD | 49 participants, mean age about 74 | Tablet; x, y, timestamp, pressure, azimuth, altitude | PD vs HC | Not public. I found no primary release page | [verified] [arXiv 2311.11756](https://arxiv.org/pdf/2311.11756); [arXiv 2309.14288](https://arxiv.org/pdf/2309.14288) |

- On the UCI ParkinsonHW data, a geometric-feature spiral classifier reached AUC 0.999. That is a ceiling effect on a tiny dataset, so treat it with caution — [Brain Sci 2021, PMC8533717](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8533717/) [verified snippet]
- LSTM-CNN reported 96.2% accuracy on DraWritePD vs 90.7% on PaHaW — [arXiv 2311.11756](https://arxiv.org/pdf/2311.11756) [verified snippet]
- A NewHandPD preprint reported about 97% accuracy on seen patients and about 95% on unseen patients — [arXiv 2510.17703](https://www.arxiv.org/pdf/2510.17703) [verified snippet]

**Finger tapping / keystroke (for the tapping game)**

| Dataset | Subjects / size | Signals | Labels | Access | Source |
|---|---|---|---|---|---|
| mPower (Bot et al. 2016, Sci Data 3:160011) | Tapping: 8,003 participants, 78,887 records (first 6 months) | iPhone two-button alternating tap for 20 s; tap x,y + timestamps + accelerometer. Also voice, gait/balance, memory tasks | Self-reported PD diagnosis, MDS-UPDRS-derived survey items, medication timing | Synapse (synapse.org/mPower), qualified-researcher registration, broad-sharing participants only | [verified] [Bot et al. 2016, DOI 10.1038/sdata.2016.11](https://www.doi.org/10.1038/SDATA.2016.11); [PMC4776701](https://pmc.ncbi.nlm.nih.gov/articles/PMC4776701) |
| Tappy Keystroke Data (Adams 2017) | about 200 subjects (PD and controls), natural typing | Key hold time, latency, flight time, hand side | PD yes/no, severity, medication | PhysioNet / Kaggle | [bg] Adams WR 2017, "High-accuracy detection of early Parkinson's disease using multiple characteristics of finger movement while typing," PLoS ONE 12(11):e0188226, DOI 10.1371/journal.pone.0188226 |

**Rehabilitation-exercise pose datasets (for the MediaPipe pose game)**

| Dataset | Subjects | Sensor | Exercises | Labels | License / URL | Source |
|---|---|---|---|---|---|---|
| KIMORE (Capecci et al. 2019, IEEE TNSRE) | 78: 44 healthy + 34 with motor dysfunction (stroke, PD, low back pain) | Kinect v2: RGB, depth, 25-joint skeleton positions + orientations | 5 low-back-pain exercises | **Clinical questionnaire scores in [0, 50]** per exercise (total, primary-outcome and control-factor sub-scores). The same score applies to all repetitions of a subject | Free download from UNIVPM VRAI page | [verified] [KIMORE page](https://vrai.dii.univpm.it/node/204704); [PubMed 31217121](https://www.pubmed.gov/31217121/); score detail from [Liao et al. arXiv 1901.10435](https://arxiv.org/pdf/1901.10435). DOI [bg] 10.1109/TNSRE.2019.2923060 |
| UI-PRMD (Vakanski et al. 2018, Data 3(1):2) | 10 healthy | Vicon optical (high accuracy) + Kinect v2, simultaneous; joint positions and angles as CSV | 10 exercises (deep squat, hurdle step, inline lunge, side lunge, sit-to-stand, standing active straight-leg raise, shoulder abduction, extension, internal-external rotation, scaption), 10 reps each, plus "_inc" incorrect versions imitating patients | Binary correct/incorrect | ODC Public Domain Dedication (PDDL) v1.0 | [verified] [UI-PRMD site](https://webpages.uidaho.edu/ui-prmd/); [PMC5773117](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5773117/) |
| IntelliRehabDS (IRDS) (Miron et al. 2021, Data 6(5):46) | 29 (15 patients, 14 healthy) | Kinect One skeleton | 9 gestures (upper-limb/body) | Correct/incorrect per repetition, body position (standing/sitting), patient or healthy | Open (MDPI data descriptor) | [verified] [MDPI Data 6(5):46](https://www.mdpi.com/2306-5729/6/5/46/htm); [Crossref DOI 10.3390/data6050046](https://api.crossref.org/works/10.3390%2FDATA6050046) |

- Liao, Vakanski and Xian built a deep-learning framework on UI-PRMD and KIMORE. It uses a deviation-from-reference performance metric (GMM log-likelihood) as a continuous quality score and a spatio-temporal NN to regress it. For KIMORE, predictions "closely follow the ground truth scores provided by the clinicians." This is a template for a 0–100 score head — [Liao et al. 2020, arXiv 1901.10435](https://arxiv.org/pdf/1901.10435) [verified snippet]

**Stroke upper-limb kinematics (validation / pose game)**

| Dataset | Subjects | Sensors | Tasks | Source |
|---|---|---|---|---|
| Zenodo 3713448/3713449 (Schwarz et al.) | 20 chronic stroke + 5 healthy controls (NCT03135093) | Inertial sensors (Xsens), .mvnx | 30 daily-living activities (gestures, grasp, tool use) | [verified] [Zenodo 3713449](https://zenodo.org/records/3713449); [DataCite 10.5281/zenodo.3713448](https://commons.datacite.org/doi.org/10.5281/zenodo.3713448) |
| Zenodo 3930751 / 3930752 (SoftPro, Univ. Zurich/Twente) | 10 chronic stroke | 8 IMUs + fingertip force sensors | ARAT-adapted reach-to-grasp and displacement | [verified] [Zenodo 3930751](https://zenodo.org/record/3930751); [Zenodo 3930752](https://zenodo.org/record/3930752) |
| Zenodo 6075092 | 14 stroke + 12 healthy | 3 mocap systems (healthy). Some healthy sessions include labelled simulated anomalies | Repetitive COMB, RECT, POUR, **TAP** (extracted features) | [verified] [Zenodo 6075092](https://zenodo.org/record/6075092) |
| ENHANCE trial (Mendeley Data) | Subacute stroke | Clinical + kinematic | Upper-limb robot/kinematic assessment | [verified] [Mendeley 3d9sgmghm5 v2](https://data.mendeley.com/datasets/3d9sgmghm5/2) |
| Lucchetti et al. 2025, Sci Data | 10 post-stroke + 10 healthy | Kinematics + EMG | Upper-limb tasks | [verified snippet] mentioned in the [same search](https://zenodo.org/record/3930751). Hosting not confirmed |

- The licenses of the Zenodo stroke datasets were not checked. Zenodo records usually state CC BY 4.0, but each record must be checked — [Zenodo 3713449](https://zenodo.org/records/3713449)

### Inferences
- **Tracing game:** use the UCI spiral and PaHaW (x, y, t) series to check that synthetic tremor and slowness features are in a realistic range, and to fine-tune a 1D-CNN with a "PD-like tremor" auxiliary class. HandPD/NewHandPD images suit a 2D-CNN on rasterised traces. None of these contain stroke, CTS or CIPN patients.
- **Pose game:** KIMORE is the only open pose dataset with stroke patients and continuous clinician scores. Rescaling 0–50 to 0–100 maps directly onto the 0–100 output. The joint layout (Kinect 25 joints) must be remapped to MediaPipe's 33 landmarks (shoulder/elbow/wrist/hip overlap cleanly). UI-PRMD's "_inc" sequences are a ready-made "impaired-like" class.
- **Tapping game:** mPower is huge but PD-only and needs Synapse registration, which may not be feasible within a hackathon. Use it mainly as a reference for tapping-rate distributions in smartphone two-target tapping.

### Gaps
- I found no public dataset of mouse or touch tracing by stroke, post-CTS-release or CIPN patients.
- I found no public finger-tapping dataset for stroke, CTS or CIPN.
- I did not locate a dedicated public **IMU tremor dataset** (e.g. wrist accelerometer, ET vs PD) in this session. Candidates for follow-up are the PD-specific Levodopa Response Study and the MJFF/CIS-PD BEAT-PD challenge (Synapse). These were not verified here.
- I did not find a public **mouse-dynamics dataset with motor-impairment labels**. General mouse-dynamics datasets (e.g. Balabit) are for biometrics and unlabelled for impairment. Not verified.
- The PaHaW sampling rate (150 vs 200 Hz) and the HandPD/NewHandPD subject counts are inconsistent across secondary sources.

## Key Question 2: What quantitative parameters can drive realistic synthetic healthy vs impaired movement data?

### Takeaway
There is solid literature for **tremor frequency bands**, **normal joint ROM** and **direction-of-effect** findings: stroke reduces speed, smoothness, tapping rate, circle area and roundness, and Fitts information rate. Exact stroke-vs-healthy effect sizes for game-like tracing and tapping are scattered, and several full texts could not be opened. The synthetic generator should therefore be parameterised with ranges (below), and the "mild/moderate/severe" thresholds treated as design assumptions to be calibrated later.

### Cited Findings

**Tremor frequency (for adding oscillatory noise to x,y or joint angles)**

| Tremor type | Frequency | Notes | Source |
|---|---|---|---|
| Physiological | 6–12 Hz (one table), "8–12 Hz central oscillator" component; low amplitude | Usually asymptomatic | [verified] [PMC6923291 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC6923291/table/t0005); [Overview of human tremor physiology, PubMed 9827594](https://pubmed.ncbi.nlm.nih.gov/9827594/); [Frontiers Neurol 2021 review, 10.3389/fneur.2021.684835](https://www.frontiersin.org/articles/10.3389/fneur.2021.684835/endNote) |
| Enhanced physiological | 4–12 Hz | Mechanical or mechanical-reflex | [verified] [PMC6923291 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC6923291/table/t0005) |
| Essential tremor | 4–12 Hz (frequency falls with age) | Postural/kinetic | [verified] [PMC6923291 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC6923291/table/t0005) |
| Parkinsonian | 4–6 Hz rest; re-emergent postural 3–5 Hz | Rest > action | [verified] [PMC6923291 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC6923291/table/t0005); [Frontiers 2021](https://www.frontiersin.org/articles/10.3389/fneur.2021.684835/endNote) |

- Tremor is not a typical primary feature of stroke, CTS or CIPN. For these groups, low-frequency jitter or irregularity (sensory ataxia in CIPN, spasticity/synergy in stroke) is more appropriate than a clean 4–6 Hz sinusoid (inference, see below).

**Smoothness metrics (stroke vs healthy)**
- In a systematic review and simulation study, SPARC was the only metric judged valid for reach-to-point and reach-to-grasp smoothness after stroke — [Smoothness metric during reach-to-grasp after stroke (series), PMC8461930](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8461930/); [JNER 10.1186/s12984-021-00949-6](https://link.springer.com/doi/10.1186/s12984-021-00949-6) [verified snippets]
- In moderate-to-severe subacute stroke, SPARC and LDLJ both had excellent reliability. SPARC is recommended for reaches without a controlled duration — [JNER 2024, 10.1186/s12984-024-01382-1; PMC11134951](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11134951/) [verified snippet. Numeric means not retrievable: captcha]
- In healthy reaching, SPARC had the lowest inter- and intra-subject CV of the metrics tested (SPARC, NARJ, LDLJ, zero-crossings) — [PMC9919347](https://pmc.ncbi.nlm.nih.gov/articles/PMC9919347) [verified snippet]
- SPARC definition: the negative arc length of the normalised Fourier magnitude spectrum of the speed profile, cut off at an adaptive frequency (amplitude threshold 0.05, max cutoff 10 Hz). Values are more negative for less smooth movement — [bg] Balasubramanian S, Melendez-Calderon A, Roby-Brami A, Burdet E. 2015, "On the analysis of movement smoothness," JNER 12:112, DOI 10.1186/s12984-015-0090-9
- Stroke recovery increases smoothness: the number of speed peaks falls and sub-movements merge over recovery — [bg] Rohrer B et al. 2002, "Movement smoothness changes during stroke recovery," J Neurosci 22(18):8297–8304, DOI 10.1523/JNEUROSCI.22-18-08297.2002

**Tracing / drawing performance (stroke vs healthy)**
- Circle drawing: stroke survivors drew circles with smaller area and lower roundness and used more synergistic (shoulder-elbow coupled) patterns. The circle metrics correlated strongly with proximal Fugl-Meyer UE scores — [Krabben et al. 2011, JNER 8:15, DOI 10.1186/1743-0003-8-15](https://link.springer.com/doi/10.1186/1743-0003-8-15) [verified snippet]
- Tablet maze (20 chronic stroke vs 20 controls): stroke participants made more boundary errors at every difficulty level and had lower speed at several levels. Error time rose with complexity in stroke but stayed flat in controls — [Univ. Delaware tablet maze study](https://udspace.udel.edu/server/api/core/bitstreams/d0088afd-03de-43ee-8150-db7a0f5cccdb/content) [verified snippet]
- Stroke patients at Brunnstrom stage V (n=15) vs 10 healthy: significantly different movement time and peak velocity, plus more erratic trajectory variation — [Kobe Univ. thesis](https://da.lib.kobe-u.ac.jp/da/kernel/D1006905/D1006905.pdf) [verified snippet]
- Square-path drawing in a 2 cm-wide channel (10 stroke vs 30 healthy): precision error = area outside the path, plus speed per side. This is a usable metric definition for the tracing game — Kostić & Popović (Univ. Belgrade), found via the [same search](https://jneuroengrehab.biomedcentral.com/articles/10.1186/1743-0003-8-15/tables/1) [verified snippet. Full citation not retrieved]

**Finger tapping**
- Stroke patients (n=10 vs 10 controls) showed a reduced tapping rate, less accurate force control, reduced finger independence and more erroneous taps and overflow — [Frontiers Hum Neurosci 2015, 10.3389/fnhum.2015.00260](https://www.frontiersin.org/articles/10.3389/fnhum.2015.00260/full) [verified snippet]
- Paretic finger control during paced tapping (1, 2, 3 Hz targets) was compromised. Nonparetic control was similar to controls except in bilateral conditions — [JNER 2015, 10.1186/s12984-015-0054-0](https://jneuroengrehab.biomedcentral.com/track/pdf/10.1186/s12984-015-0054-0) [verified snippet]
- Tapping after peripheral nerve injury was much less reduced than after central (stroke) injury — [PMC4429569](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4429569/) [verified snippet]
- Repetitive finger movements after stroke are slowed and less regular (higher inter-tap-interval variability) — [PMC4522286](https://pmc.ncbi.nlm.nih.gov/articles/PMC4522286) [verified snippet]
- Healthy maximal index-finger tapping is commonly about 5–7 taps/s. Halstead-Reitan norms are about 50 taps per 10 s for the dominant hand in young adults — [Wikipedia "Tapping rate"](https://en.wikipedia.org/wiki/Tapping_rate) [verified link, low-quality source]. Primary norms not retrieved.

**CIPN dexterity**
- Adult survivors exposed to neurotoxic chemotherapy were 5.9 s slower on the Grooved Pegboard than lab controls (95% CI 1.6–10.1, p=.008) — [JAMA Oncol figure, PMC6142928](https://pmc.ncbi.nlm.nih.gov/articles/PMC6142928/figure/noi180026f2) [verified snippet]
- In breast cancer survivors, Grooved Pegboard completion time (both hands) correlated with Meissner corpuscle density (p ≤ .02) — [PMC5496793](https://pmc.ncbi.nlm.nih.gov/articles/PMC5496793/table/T6) [verified snippet]
- In taxane-induced neuropathy (n=43), hand-dexterity impairment correlated with age, grip-force control and PNQ sensory score — [Support Care Cancer 2024, 10.1007/s00520-024-08504-4](https://link.springer.com/content/pdf/10.1007/s00520-024-08504-4.pdf) [verified snippet]
- In an auricular-acupressure CIPN trial, baseline dominant-hand Grooved Pegboard was about 117–122 s. Typical healthy adult norms are about 60–70 s (norm not verified) — [NCT04920097](https://clinicaltrials.gov/study/NCT04920097) [verified snippet]

**Fitts' law throughput**
- Chronic stroke patients (n=19) reaching vs healthy young controls (n=19) followed Fitts' law, but with a lower information rate and more variability — [Frontiers Neurol 2018, 10.3389/fneur.2018.00300](https://www.frontiersin.org/articles/10.3389/fneur.2018.00300/full) [verified snippet]
- Stroke vs able-bodied throughput (bit/s), with slopes of MT vs effective ID, is shown in [PMC7956990 Fig 6](https://pmc.ncbi.nlm.nih.gov/articles/PMC7956990/figure/F6) [verified snippet. Values not extracted]
- Mouse pointing throughput was 4.7% lower for people with limited fine motor function — [Sharif, Pao, Reinecke, Wobbrock, ASSETS 2020](https://faculty.washington.edu/wobbrock/pubs/assets-20.pdf) [verified snippet]
- Healthy desktop mouse throughput is typically about 3.7–4.9 bits/s across ISO 9241-9 studies — [bg] Soukoreff RW, MacKenzie IS 2004, "Towards a standard for pointing device evaluation," Int J Hum-Comput Stud 61(6):751–789, DOI 10.1016/j.ijhcs.2004.09.001

**Joint range of motion (normal reference)**

| Joint motion | Textbook normal | Measured adult means | Source |
|---|---|---|---|
| Shoulder flexion | 180° | 168.4° (Boone-based table) | [verified] [Physiopedia ROM norms](https://www.physio-pedia.com:443/Range_of_Motion_Normative_Values); [PMC1713230 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC1713230/table/T2) |
| Elbow flexion / extension | 140–150° / 0° | 145.4° | same sources; [PMC9218764 table](https://pmc.ncbi.nlm.nih.gov/articles/PMC9218764/table/T1) |
| Wrist flexion / extension | 60–80° / 60–70° | — | [SNCC normal values](https://www.sncc.ca/resources/Documents/Dragon%20Boat/2024%20CCWCs/range%20of%20motion%20normal%20values.pdf); [NASM](https://blog.nasm.org/upper-extremities-range-of-motion) |
| Age/sex-specific norms | CDC Joint ROM Study (Soucie et al.) | — | [CDC JointROM](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) |

### Inferences
Suggested rule-based generator ranges for the synthetic data. These are design assumptions grounded in the directions above. They are not literature-verified cut-offs and must be labelled as such in the app.

| Parameter | Normal | Mild | Moderate | Severe |
|---|---|---|---|---|
| Speed scaling vs minimum-jerk template | 1.0 | 0.75–0.9 | 0.5–0.75 | 0.25–0.5 |
| Extra sub-movements (velocity peaks, added Gaussian speed bumps) | 1–2 | 3–4 | 5–8 | >8 |
| Lateral path deviation (RMS, as % of target width) | <10% | 10–25% | 25–50% | >50% |
| Tremor component (only for a tremor-type class) | 8–12 Hz, ~0.1 mm | 4–12 Hz small | 4–8 Hz | 4–6 Hz large |
| Max tapping rate | 5–7 Hz | 4–5 Hz | 2.5–4 Hz | <2.5 Hz |
| Inter-tap interval CV | <10% | 10–20% | 20–35% | >35% |
| Active ROM as % of normal (shoulder flexion 180°, elbow 145°, wrist ext 70°) | >90% | 75–90% | 50–75% | <50% |

- Population-specific shaping:
  - **Stroke:** low speed, many sub-movements, low SPARC, reduced shoulder flexion/abduction ROM, trunk compensation in the pose game.
  - **CTS post-release:** mostly reduced wrist ROM, grip and pinch, and fine-precision error. Gross speed is near normal.
  - **CIPN:** sensory-ataxic irregularity (higher path-deviation variance, slower fine dexterity, e.g. about +6 s on the pegboard). Proximal ROM is near normal.

### Gaps
- I could not retrieve numeric SPARC, LDLJ or velocity-peak means for stroke vs healthy: the PMC/Springer full texts were blocked. Commonly reported healthy SPARC for discrete reaches is roughly −1.4 to −1.8, with stroke more negative. This is from memory, unverified.
- I found no source for tremor **amplitude** values (physiological vs pathological).
- I found no verified numbers for stroke **reaction-time** increase, absolute stroke tapping rates in Hz, stroke Fitts throughput in bit/s, **ROM deficits after CTS release** (typical recovery timelines), or tapping and ROM in CIPN.
- Mild/moderate/severe thresholds are not standardised in the literature for game metrics. They must be calibrated against clinical scales (Fugl-Meyer UE, Box & Block, 9-Hole Peg Test).

## Key Question 3: Which methods exist for synthetic movement data generation, augmentation and ML scoring of drawings and rehab movement?

### Takeaway
Three generator families exist. **Model-based** generation uses a minimum-jerk template plus submovement and tremor noise. **Rule-based "error-guided" pose augmentation** injects reduced ROM and compensation. **GANs** generate skeleton sequences. For time-series CNNs, simple augmentations (jitter, scaling, rotation, time-warp, magnitude-warp) are well-established. Drawing scoring commonly uses CNNs on rasterised spirals or 1D/LSTM-CNN on pen signals, and GMM/DTW deviation from a reference provides a continuous quality score.

### Cited Findings
- **Error-Guided Pose Augmentation (EGPA), 2025:** generates synthetic skeletons that simulate clinically relevant errors, such as limited ROM and compensatory movements, instead of random transforms. Combined with an attention-based GCN it improves rehab-exercise assessment metrics. This maps closely onto the planned rule-based approach — [Sherif & Hamdi 2025, arXiv 2506.09833](https://arxiv.org/abs/2506.09833v1) [verified snippet]
- **GANs for physical-therapy movements:** compares GAN architectures for generating movement sequences and uses deviation from consistent reference movements as soft labels for correctness — [arXiv 1812.06307](https://arxiv.org/pdf/1812.06307.pdf) [verified snippet]
- **HP-GAN trained on KIMORE** to generate sequences for under-represented patient classes (squat), with visual comparison only — [HPI thesis, Balancing Medical Human Pose Datasets using GANs](https://hpi.de/en/arnrich/teaching/gloeckner/) [verified snippet]
- **Skeleton database enrichment** with a pose generator for physiotherapy video — [Segal & Hadar 2022, BGU](https://cris.bgu.ac.il/en/publications/constructing-a-skeleton-database-and-enriching-it-using-a-generat-2/) [verified snippet]
- **Musculoskeletal-simulation-based IMU synthesis** (Spilz et al. 2025). The authors note that purely data-driven generators risk biomechanically invalid samples — [arXiv 2505.24415](https://arxiv.org/pdf/2505.24415v1) [verified snippet]
- **Continuous scoring from deviation:** a GMM log-likelihood performance metric plus a deep spatio-temporal model on UI-PRMD/KIMORE — [Liao, Vakanski, Xian 2020, arXiv 1901.10435](https://arxiv.org/pdf/1901.10435) [verified snippet]
- **Minimum-jerk trajectory model:** x(t) = x0 + (xf − x0)(10τ³ − 15τ⁴ + 6τ⁵), τ = t/T, which gives a bell-shaped single-peak speed profile for healthy point-to-point moves — [bg] Flash T, Hogan N 1985, "The coordination of arm movements," J Neurosci 5(7):1688–1703, DOI 10.1523/JNEUROSCI.05-07-01688.1985
- **Stroke as overlapping sub-movements:** a submovement superposition model, consistent with Rohrer et al. — [bg] Rohrer B et al. 2002, DOI 10.1523/JNEUROSCI.22-18-08297.2002
- **Wearable time-series augmentation for PD CNNs:** jittering, scaling, rotation, permutation, time-warping and magnitude-warping. Rotation plus permutation/time-warp gave the largest gains (accuracy 77.5% → 86.9%) — [bg] Um TT et al. 2017, "Data augmentation of wearable sensor data for Parkinson's disease monitoring using convolutional neural networks," ICMI 2017, arXiv 1706.00527
- **Survey of time-series augmentation for NNs** (jitter, window warping, DTW-barycentre/guided warping) — [bg] Iwana BK, Uchida S 2021, PLoS ONE 16(7):e0254841, DOI 10.1371/journal.pone.0254841
- **Drawing scoring with CNNs:** 1D vs 2D vs 3D CNNs compared for drawing-test PD diagnostics — [arXiv 2309.14288](https://arxiv.org/pdf/2309.14288). Lightweight CNN — [arXiv 2302.00973](https://arxiv.org/pdf/2302.00973). LSTM-CNN on dynamic handwriting — [arXiv 2311.11756](https://arxiv.org/pdf/2311.11756). Time-series-to-image conversion for cross-corpus handwriting — [arXiv 2509.16474](https://arxiv.org/pdf/2509.16474) [verified links/snippets]
- **Deep-learning rehab assessment reviews:** [Liao et al., arXiv 2003.08767](https://arxiv.org/pdf/2003.08767). Action Quality Assessment survey — [arXiv 2502.02817](https://arxiv.org/pdf/2502.02817) [verified links]

### Inferences
- Recommended synthetic pipeline for the tracing game:
  1. Take the target path (spiral, line, shape) and parametrise it by arc length.
  2. Generate a minimum-jerk speed profile with duration T scaled by severity.
  3. Superimpose N sub-movements (Gaussian speed bumps or pauses).
  4. Add lateral deviation as low-pass filtered noise (OU process) with severity-scaled σ.
  5. Optionally add sinusoidal tremor (frequency per the tremor table).
  6. Sample at a browser-like 60 Hz with timing jitter.
  7. Apply Um et al.-style augmentations.
  
  Labels come from the generating parameters, which gives the 0–100 score directly (e.g. a weighted combination of speed, SPARC and deviation).
- Pose game: apply EGPA-style ROM caps and compensation (trunk lean, shoulder elevation) to normal templates (e.g. UI-PRMD Kinect correct reps remapped to MediaPipe). Validate on KIMORE stroke subjects against the clinician score.
- Risk: a CNN trained only on rule-based synthetic data learns the generator's rules. Report this honestly and include a small real-data sanity check (UCI spiral, KIMORE).

### Gaps
- I found no published study that trains a motor-score model purely on minimum-jerk synthetic data and validates it on stroke patients.
- DTW-based scoring papers specifically for spiral/tracing games were not retrieved in this session.
