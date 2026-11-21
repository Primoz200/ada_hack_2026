# Evidence-based design of the clinician side: triage list, single-patient view, alert model, wording

Research date: 21 Nov 2026. Notes on method and reliability:
- Every item under "Cited Findings" was read on the linked page during this session (full text or abstract, as marked). Items marked **[abstract only]** or **[truncated page]** were not read in full.
- PubMed Central blocked most automated access (reCAPTCHA), so several papers were read through the publisher mirror instead. Papers I could not open at all are listed under Gaps, never under Cited Findings.
- All wording is paraphrase; no numbers are from memory. First-author names "Ploderer" (JMIR Rehabil 2016 e9) and "Scheinker" (JMIR Diabetes 2022 e27284) are from memory and were not shown on the fetched pages; the URLs are verified. Design rules under "Inferences" are my own translation of the evidence into UI/rules for a 20-hour build and are not themselves validated.

---

## 1. Alert fatigue: size of the problem and which design measures reduce it

### Takeaway
Clinicians ignore most alerts when volume is high and specificity is low (override ranges of roughly 46–96% in CDS; in one RPM programme 57% of measurements raised an alert and 77% of the resulting nurse actions had no clinical consequence). The measures with quantified benefit are: severity tiering, fewer repeats per patient, trend-based instead of fixed-threshold rules, personal thresholds for the few high-volume patients, bundling per patient-day, auto-handling of missing-data alerts, and nurse-first routing.

### Cited Findings

**Size of the problem (CDS in general)**
- A systematic review of 23 studies put medication-alert override rates between 46.2% and 96.2%; by type, dose alerts 82–96.8%, drug-interaction alerts 56.3–95.6%. Only 29.4–100% of overrides were judged appropriate. Inappropriate overrides carried an odds ratio of 6.14 (95% CI 4.63–7.71) for adverse drug events. **[page truncated at ~80%]** — [Poly et al., JMIR Med Inform 2020;8(7):e15653, doi 10.2196/15653](https://medinform.jmir.org/2020/7/e15653/)
- AHRQ's patient-safety primer reports one hospital's 66 adult ICU beds generating over 2 million monitor alerts in a month (about 187 per patient per day), and VA primary-care clinicians receiving more than 100 alerts a day. It also cites a newspaper investigation linking 200+ deaths over five years to unheeded monitor alarms. — [AHRQ PSNet, Alert Fatigue primer](https://psnet.ahrq.gov/primer/alert-fatigue)
- In 112 primary-care clinicians (1.27 million reminders, 326,203 drug alerts), acceptance fell 30% for each extra reminder shown in the same encounter (IRR 0.70) and 10% for every 5-percentage-point increase in the share of repeated reminders (IRR 0.90). About a quarter to a third of alerts were repeats for the same patient within a year (median 26.2% of reminders, 31.8% of drug alerts). Once a first reminder was overridden, its repeats were overridden 87.9% of the time. Number of patients seen did not predict acceptance; alert load and repetition did. Nurse practitioners were about 4.56 times as likely as physicians to accept drug alerts. — [Ancker et al., BMC Med Inform Decis Mak 2017;17:36, doi 10.1186/s12911-017-0430-8](https://link.springer.com/10.1186/s12911-017-0430-8)

**Size of the problem (ML risk scores)**
- External validation of a widely deployed proprietary sepsis score: AUC 0.63, sensitivity 33%, PPV 12%; alerts fired on 18% of all hospitalisations (6,971/38,455) while 67% of true sepsis cases got no alert. Number needed to evaluate was 8 with one alert per patient and 109 if every re-crossing of the threshold was re-evaluated. The authors named alert fatigue as a consequence. — [Wong et al., JAMA Intern Med 2021](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781307)

**Size of the problem (RPM and ePRO specifically)**
- Dutch hospital RPM programme (174 users, June 2022–May 2023): 30,184 measurements produced 17,293 alerts (57% of measurements). 79% (13,647) were processed automatically, 86% of those being overdue/inactivity alerts. The 3,646 manual alerts equalled 21 per user per year. Of 2,101 resulting monitoring actions, 77% (1,626) were administrative with no clinical consequence; 71% of blood-pressure alerts were closed administratively. 15% of users (25 people) produced 61% of manual simple alerts and 48% of complex ones. — [JMIR Med Inform 2025;13:e66066, doi 10.2196/66066](https://medinform.jmir.org/2025/1/e66066)
- PRO-TECT oncology trial (593 patients, weekly home symptom surveys, 91% of expected surveys completed): 34% of surveys generated an alert to a nurse; 59% of alerts led to immediate nurse action; patients themselves rated only 10% of alerts as urgent. A suppression algorithm based on patient-rated urgency plus predicted nurse-rated urgency marked 38% of alerts as suppressible, with 80% sensitivity (CI 76–84%) and 52% specificity (CI 49–55%) for nurse-urgent alerts. **[abstract only]** — [Optimization of alert notifications in ePRO remote symptom monitoring (PRO-TECT, AFT-39), PMID 38771558](https://mijn.bsl.nl/optimization-of-alert-notifications-in-electronic-patient-report/27117700)
- Memorial Sloan Kettering PRO alerting 2016–2021: 7.82% of completed assessments (36,838/470,841) triggered an alert and 13.28% of patients ever triggered one; median 35 alerts per care-team inbox, median 5 staff per inbox. — [Strachna, Asan, Stetson, JMIR Med Inform 2022;10(11):e38483, doi 10.2196/38483](https://medinform.jmir.org/2022/11/e38483)

**Measures with quantified effect**
- *Severity tiering.* At a site that tiered drug-interaction alerts (only the top tier interruptive), clinicians complied with 100% of the most severe alerts versus 34% at a non-tiered site, and 29% versus 10% for moderately severe ones (71,350 alerts). — [Paterno et al., JAMIA 2009;16(1):40–46](https://academic.oup.com/jamia/article/16/1/40/865495)
- *Visible colour labels.* At MSK, clinicians themselves asked for red / red-yellow / yellow labels after months of unlabelled messages. Red alerts were then documented in the EHR 56.83% of the time versus 27.68% for unlabelled alerts. Mix: yellow 61.6%, red-yellow 13.3%, red 12.4%. — [Strachna et al. 2022](https://medinform.jmir.org/2022/11/e38483)
- *Context-aware suppression.* The same team muted certain pain questions for 2–3 days after surgery once dashboards showed a flood of expected post-operative pain alerts. — [Strachna et al. 2022](https://medinform.jmir.org/2022/11/e38483)
- *Trend algorithms instead of fixed thresholds.* In a simulated heart-failure telemonitoring study (16 clinicians), a fixed rule (weight gain of 2 kg or more in 3 days) produced 556 alert episodes versus 314 for a moving-average-crossover rule and 287 for a CUSUM rule. Total review time was 149 ± 82 min versus 80 ± 42 min (p = .038) while time per alert was unchanged (about 30 s). Share of alerts rated top importance rose from 3.5% to 18.6%. Clinician agreement on what to do was low in both arms (Fleiss kappa 0.33 and 0.31). Small exploratory pilot. — [Simulated case management of home telemonitoring, PMC5240411](https://pmc.ncbi.nlm.nih.gov/articles/PMC5240411/)
- *Threshold tuning.* Raising a population blood-pressure threshold by one step (5–10 mmHg) roughly halved alerts (diastolic −47%, systolic −54%); two steps cut 77–85%. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- *Personal thresholds for outliers.* In the same programme 13 of the 25 high-volume users received individual thresholds; in just 3 of them a medically justified change removed 265 manual alerts. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- *Bundling.* Grouping all of one user's alerts on one day into a single action turned 3,646 manual alerts into 2,101 actions (about 42% fewer); weekend alerts became one Monday action. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- *Auto-processing of non-clinical alerts.* 79% of alerts (mostly missed measurements) never reached a human; average nurse workload was 6.2 minutes per user per month, assuming 5 min per administrative and 10 min per clinical action. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- *Personal baseline rules.* The Stanford TIDE diabetes dashboard flags a patient when the weekly mean exceeds the patient's own baseline by a fixed margin or time-in-range falls more than 10 percentage points below baseline (later: last week versus prior 4 weeks), alongside generic targets. It cut patients needing review by about 43% at 99% sensitivity (242/245), though weekly specificity was only 19–50% and 50–63% of the panel was still flagged each week. The paper's weekly table is internally inconsistent, so treat weekly figures cautiously. — [Scheinker et al., JMIR Diabetes 2022;7(2):e27284](https://diabetes.jmir.org/2022/2/e27284)
- *General principles (AHRQ):* raise specificity, tailor to patient characteristics, tier by severity, make only the top tier interruptive, apply human-factors design to format and colour. — [AHRQ PSNet](https://psnet.ahrq.gov/primer/alert-fatigue)

### Inferences
- A defensible volume target for the demo: aim for well under 10% of sessions producing a clinician-visible alert (MSK ran at 7.8% of assessments; PRO-TECT at 34% was high enough that the trial group built a suppression algorithm).
- Concrete alert model for the build:
  1. **Three tiers only.** RED = red-flag symptom (immediate, interruptive, bypasses trend logic). AMBER = sustained negative trend (shown in the list, non-interruptive, daily digest). GREY = missing data (handled by automatic patient reminder first; shown to staff only after N days).
  2. **One open alert per patient.** New triggers on the same patient append to the open alert (bundling, about 42% fewer actions in the Dutch data).
  3. **No repeats after acknowledgement.** After "acknowledge" or "snooze 7 days", the same cause must not re-fire unless the patient worsens by a further step. Ancker's data show repeats are overridden about 88% of the time once the first was dismissed.
  4. **Persistence requirement** for AMBER (see section 2) and **personal baseline**, both of which have supporting numbers above.
  5. **Expected-pattern suppression**: do not alert on pain/weak grip in the first days after carpal tunnel surgery or on the first 2–3 game sessions (analogous to MSK's post-surgery mute).
  6. **Nurse-first routing** with explicit escalate-to-doctor button.
- Give each patient a per-patient "sensitivity" override (default / less sensitive) because a small minority of patients generates most alerts (15% of users produced 61% of alerts).
- Track and show the team its own alert statistics (alerts per week, % actioned): both MSK and the Dutch group tuned rules from exactly this feedback.

### Gaps
- No controlled study was found that isolates the effect of "N consecutive breaches" on alert volume in RPM; the Dutch framework recommends it but gives no number.
- No evidence was found specifically on snooze/acknowledge functions and their effect on fatigue or safety.
- I could not open the 2026 alert-fatigue systematic review hosted at metrohealth.org (Ray Wilson et al.) or the full PRO-TECT alert paper (PMC11825061), so newer pooled numbers may exist.
- All quantified tiering evidence is from medication alerts, not RPM; transfer to RPM is by analogy.

---

## 2. Statistical alerting methods for individual longitudinal data: defaults and pitfalls

### Takeaway
Use a personal baseline plus a smoothed statistic (EWMA or CUSUM) and require the change to exceed measurement error (MDC or RCI) before calling it real. Textbook defaults exist (EWMA weight 0.2–0.3 with 3-sigma limits; CUSUM k = half the shift to detect, h about 4–5 sigma; RCI cut-off ±1.645 or MDC95 = 1.96 × SEM × √2). The main pitfalls for game-based tests are practice effects that make the first sessions an artificially low baseline, regression to the mean after an unusually good or bad session, and missing sessions.

### Cited Findings
- **EWMA.** Statistic: new value = λ × today's observation + (1 − λ) × previous EWMA, started at the historical mean. NIST gives λ between 0.2 and 0.3 as the usual choice and a limit multiplier of 3; limit variance is s² × λ/(2 − λ). It reacts to small or gradual drift, whereas a plain (Shewhart) limit only looks at the latest point. λ = 1 collapses to a plain threshold. — [NIST/SEMATECH e-Handbook, EWMA control charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm)
- **CUSUM.** One-sided lower sum for detecting decline: S = max(0, previous S + baseline − k − today's value); signal when S exceeds h. NIST's guidance sets k to half the shift one wants to detect (0.5 sigma for a 1-sigma shift) and h to roughly 4 or 5 sigma, and states CUSUM outperforms Shewhart charts for shifts of 2 sigma or less. — [NIST/SEMATECH e-Handbook, CUSUM control charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm)
- **CUSUM and moving-average crossover in practice.** In the simulated telemonitoring study the trend rules produced about half the alert episodes of the fixed rule and five times the share of alerts that clinicians rated as highly important (see section 1). — [PMC5240411](https://pmc.ncbi.nlm.nih.gov/articles/PMC5240411/)
- **SEM and MDC.** SEM = baseline SD × √(1 − ICC); MDC95 = 1.96 × SEM × √2. The Shirley Ryan AbilityLab reference asks for test-retest ICC above 0.9 when a measure drives decisions about an individual (0.7 suffices for group research). MCID is a separate concept: the smallest change a patient or clinician considers important. — [Shirley Ryan AbilityLab, Statistical terms and use](https://www.sralab.org/statistical-terms-use)
- **RCI and practice effects.** A 2025 normative study of 16 neuropsychological tests retested at 1–24 months computed RCI as (retest − baseline) divided by the standard error of the difference with ±1.645 limits (90% interval), and a practice-adjusted variant that first subtracts the mean retest gain seen in controls. Scores improved significantly on retest at most intervals purely from prior exposure, and regression-based formulas adjusting for baseline score were offered as a third option; regression to the mean is described as extreme scores drifting toward the average on retest. **[page truncated]** — [Sáez-Atxukarro et al., Neurología 2025](https://www.elsevier.es/es-revista-neurologia-295-articulo-reliable-change-indices-for-16-S0213485324000756)
- **Aggregate score with graded response (NEWS2).** Bands: 0 routine; 1–4 nurse assesses and decides on escalation; any single parameter scoring 3 triggers urgent medical-team review; 5–6 urgent review by a clinician competent in acute illness; 7 or more emergency assessment by a critical-care-capable team. Monitoring frequency rises with each band (12-hourly, 4–6-hourly, hourly, continuous). — [Royal College of Physicians, NEWS2 chart 4](https://www.rcp.ac.uk/media/mrllczrj/news2-chart-4_clinical-response-to-news-trigger-thresholds_0.pdf)
- **Traffic-light logic with a combination rule.** The UK oncology triage tool: all green = self-care advice; one amber = review within 24 hours; two or more ambers count as red; red = urgent face-to-face assessment. — [UKONS 24-hour triage tool v3 poster](https://www.ukons.org/site/assets/files/1224/ukons_triage_tool_poster_a3_v3_final.pdf)
- **Personal versus generic rules in one system.** TIDE ran both: generic targets (for example time-in-range below 60%) and personal deterioration rules (drop of more than 10 points versus the patient's own baseline week, later versus the previous 4 weeks). Patients without enough data sit in a separate tab; 6–10% of patients per week had insufficient data. — [JMIR Diabetes 2022 e27284](https://diabetes.jmir.org/2022/2/e27284)
- **Missing data is the dominant alert type.** 11,769 of 17,293 alerts in the Dutch RPM programme were overdue/inactivity alerts, handled automatically. Overall questionnaire compliance in MSK's routine PRO programme was only 36.89%; PRO-TECT, a trial with reminders, reached 91%. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066); [Strachna 2022](https://medinform.jmir.org/2022/11/e38483); [PRO-TECT alerts abstract](https://mijn.bsl.nl/optimization-of-alert-notifications-in-electronic-patient-report/27117700)

### Inferences
Recommended defaults for the hackathon (assumptions, not validated; state them as such in the pitch):
- **Baseline:** median of sessions 2–4 (discard session 1 as a practice run), stored per game and per hand. Because practice effects raise scores over the first sessions, also keep a "rolling reference" = median of the best 3 of the last 7 sessions, and compare against whichever is higher; otherwise a real decline after a learning-inflated period is masked by a low initial baseline.
- **Noise estimate:** a personal SD from 2–3 sessions is too unstable for z-scores. Use a pooled within-person SD (from pilot data or healthy volunteers during the hackathon) to derive SEM and MDC; fall back to a fixed margin (for example 10 score points) and label it "provisional threshold".
- **Smoothing:** EWMA with λ = 0.3 on the 0–100 score.
- **AMBER rule:** EWMA below (reference − MDC) on at least 2 of the last 3 sessions, or raw score below the limit on 3 consecutive sessions, or impairment class worse by one category on 2 consecutive sessions. A CUSUM with k = 0.5 SD and h = 4 SD is an equivalent alternative and makes a nice "accumulated deficit" bar.
- **Single-session crash rule:** one session more than 2 × MDC below reference raises a soft "repeat test today" prompt to the patient rather than a clinician alert; this absorbs regression to the mean, fatigue and bad-lighting sessions.
- **NEWS2-style "single parameter" escape:** any single game in the severe class, or a new severe class in one hand only, flags AMBER even if the aggregate looks fine (mirrors the "3 in one parameter" rule).
- **Combination rule from UKONS:** two simultaneous AMBER signals (for example declining game trend plus rising numbness score) are promoted to RED-review-today.
- **Missing data:** after 2 missed days send an automatic patient reminder; after 4–5 days show a GREY "no data" badge; never impute; compute trend only on available sessions and show "n sessions in last 7 days" beside every trend. Missingness right after a decline should raise priority, not lower it.
- **Asymmetry:** alert only on decline; show improvement positively but silently.

### Gaps
- No source was found giving validated defaults (baseline length, number of consecutive breaches) for motor game or tablet-based kinematic tests specifically; the numbers above are engineering defaults from SPC texts.
- Recommendations on dual baselines or alternate forms to control practice effects could not be opened (PMC pages on serial neuropsychological assessment were blocked), so that advice is not cited here.
- I did not locate a published review of control charts applied to individual patients that I could read in full; the evidence above is NIST guidance plus one small telemonitoring simulation.
- No evidence was retrieved on how missing-not-at-random sessions (patients skipping when they feel worse) bias trend alerts.

---

## 3. What clinicians want from RPM / PRO dashboards, and PRO display guidance

### Takeaway
Clinicians consistently ask for an overview first with drill-down second, simple familiar charts (line or bar), trends over days and weeks against a baseline, context for odd values, colour-coded severity, and as little navigation as possible; second-by-second detail and exotic chart types are rejected. Consensus guidance on PRO display adds: line graphs over time, never mix score directions in one display, label the axis with descriptive severity words, and flag concerning absolute values the same way lab results are flagged.

### Cited Findings

**PRO display consensus (Snyder et al., modified Delphi, 2 panels of 28 and 27, endorsement 88–100%)** — [Snyder et al., Qual Life Res 2019, doi 10.1007/s11136-018-2020-3 (PMC6363861)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6363861)
- Individual-patient PRO scores over time should be drawn as line graphs, in one consistent representation.
- Do not re-score existing instruments, but avoid showing measures with opposite directions (higher = better and higher = worse) in the same display; where unavoidable, use very explicit labelling, titles and annotations.
- Put descriptive words on the y-axis (none / mild / moderate / severe) where evidence supports the cut-points; at minimum label the two extremes.
- Possibly concerning absolute scores should be highlighted where supporting data exist, in the same visual style the institution uses for other clinical results such as lab values.
- The panel discussed flagging concerning change (worsening) but reached no recommendation and called for research.
- Reference-population values may be shown and should be labelled as "average" rather than "norm".
- For clinician audiences, clinically important differences should be marked with a symbol explained in a legend, never an asterisk (reads as statistical significance).
- Colour is fine but the display must remain readable in greyscale.

**Therapists reviewing upper-limb data after stroke (8 OTs/physios, Melbourne, simulated wearable data)** — [Ploderer et al., JMIR Rehabil Assist Technol 2016;3(2):e9](https://rehab.jmir.org/2016/2/e9)
- Five of eight preferred the overview screen (weekly movement counts, daily quality score, averages, notes) for a quick check.
- Wanted: summary first, trends across days and weeks, context for what a movement or score means in daily life, goals and targets, simple familiar visuals, everything on one page to reduce navigation.
- Rejected for routine use: the second-by-second timeline (no time on a busy ward), the raw spreadsheet, and inspection of single movements or outliers.
- A bare quality score was hard to interpret without knowing the task that produced it.
- Used the data to open conversations with patients, check adherence and show progress.

**Clinician-centred wearable dashboard (CarePortal; 8 clinicians, 5 participatory workshops)** — [JMIR Form Res 2023;7:e46866](https://formative.jmir.org/2023/1/e46866)
- Requirements: quickly readable visuals, daily and multi-day trends rather than raw data, overview then drill-down, a baseline to compare against, absolute units (minutes) rather than percentages, and context for peaks (for example overlay of patient self-report).
- Bar charts beat radar charts and pie charts; box plots were considered research tools.
- Layout: patient cards on the entry page; per-patient daily cards with min/max/average and red colouring for out-of-range days, which clinicians wanted to click through to that day's detail.
- Lowest usability item was clarity, attributed to having to navigate several graphs; a clinician asked for visible indication of when the device was not worn, which the tool lacked.

**Population triage dashboard (TIDE)** — [JMIR Diabetes 2022 e27284](https://diabetes.jmir.org/2022/2/e27284)
- Four tabs: all patients; patients with alerts; patients with no data; patients with data and no alerts.
- Redesign after user feedback: show only the triggered metrics highlighted (first version coloured triggered red and untriggered green), drop rarely used columns, rename metrics in plain words, make the table more compact.

**Inbox-style PRO alerting (MSK)** — [Strachna et al. 2022](https://medinform.jmir.org/2022/11/e38483)
- Clinicians asked for colour severity labels to triage their inbox; governance had to define who reviews, reminders, escalation and documentation; acknowledgement rates were monitored.

**NHS expectations** — [NHS England, virtual wards technology platform guidance](https://www.england.nhs.uk/long-read/virtual-wards-enabled-by-technology-guidance-on-selecting-and-procuring-a-technology-platform/); [NHS England, virtual wards operational framework](https://www.england.nhs.uk/long-read/virtual-wards-operational-framework/)
- Patient data should flow to a dashboard reviewed remotely by a clinical team, which is alerted when a patient leaves agreed parameters; the platform should be able to record questionnaires such as PROMs.
- Remote-monitoring data should be visible in the electronic patient record.

### Inferences
**Patient list / triage view**
- Default sort: RED, then AMBER, then GREY (no data), then stable; within a tier by time since alert opened. Offer TIDE-style tabs or filter chips: "Needs review (n)", "No data (n)", "Stable (n)", "All".
- Columns (one row per patient, no horizontal scroll): status dot + one-line reason ("Trace score −18 vs baseline for 3 sessions"); condition and days since discharge/surgery; sparkline of the composite score for the last 14 days with the baseline as a faint band; change versus baseline and versus last clinic visit; adherence ("5/7 sessions"); last questionnaire flags; owner/acknowledged-by; last contact.
- Highlight only what is abnormal (TIDE lesson): stable rows are plain grey text; do not paint them green.
- Show a small header counter ("3 need review · 2 no data · 19 stable") so an empty list visibly means "nothing to do".

**Single-patient view (one screen)**
- Top banner: status, plain-language reason, when it started, suggested next step, and action buttons (Acknowledge, Call/message patient, Add note, Snooze, Escalate to doctor).
- Row of three small-multiple line charts (one per game), identical axes, **higher = better everywhere**, y-axis labelled with the four impairment classes, baseline band and MDC band drawn, alert-triggering sessions marked with a symbol explained in a legend (not an asterisk).
- Symptom chart below (pain, numbness/tingling, 0–10). These are "higher = worse", so do not overlay them on the game charts; keep them in a separate panel with an explicit "higher = worse" label and descriptive axis words.
- Adherence strip (calendar dots: done / missed) and red-flag log with timestamps.
- Drill-down on click of a session: the kinematic features for that session versus the patient's baseline (see section 4). Keep raw traces behind a second click only.
- Timeline of clinician actions and notes on the right (closes the loop, section 6).
- Design for greyscale: status carried by icon shape and text as well as colour.

### Gaps
- I did not retrieve an oncology ePRO clinician-dashboard co-design paper with a full feature list (the JMIR Formative 2020 paper found was a patient-facing portal). A 2026 JMIR Formative paper (e79694) appeared in search but was not read.
- The Snyder panel explicitly left "how to flag worsening" unresolved, so the change-flagging design above has no consensus backing.
- No formal usability benchmark (for example SUS) was found for a clinician RPM triage list; CarePortal used UEQ with n = 5.
- NHS's detailed example platform specification (Appendix 2) sits behind FutureNHS login and was not accessible.
- PROMIS-in-EHR dashboard studies were not retrieved.

---

## 4. Presenting an ML-derived score safely

### Takeaway
Clinicians do not trust a bare number. What they ask for is which inputs drove the score, how it has changed over time, and how certain the model is; similar-patient and counterfactual explanations are not valued under time pressure. A poorly calibrated score that fires often destroys trust and creates workload, while an ML alert coupled to a defined human response (a structured check) has shown benefit. A short "model facts" label stating intended use, validation status and warnings is the established transparency format.

### Cited Findings
- Interviews with 10 ICU and emergency clinicians (Toronto): they wanted to see which variables drove a prediction so they could compare it with their own judgement; they valued a certainty score and suggested the system only speak up when confident; ICU staff wanted to see what changed over time to cause the prediction. Overall accuracy alone did not secure continued use: predictions had to fit the clinical picture, and an imperfect model was acceptable when its failure reasons were clear. Similar-patient explanations and counterfactuals were judged unhelpful when time is short. Alarm and click fatigue were named as a major barrier. One junior clinician's complaint was that otherwise all you have is a number. — [Tonekaboni et al., "What Clinicians Want", MLHC 2019, arXiv:1905.05134](https://arxiv.org/pdf/1905.05134)
- "Model Facts" label (Duke): a one-page sheet with model name/version/locale, summary, mechanism (how the score is computed), validation and performance with local data, uses and directions (target population and task), and warnings (settings where it was not evaluated; not to be used for automated treatment decisions). The authors argue AUC alone tells a front-line clinician nothing about calibration or what to do, and that labels must be localised and versioned. They present it as a proposal needing testing. — [Sendak et al., npj Digit Med 2020;3:41, doi 10.1038/s41746-020-0253-3](https://www.nature.com/articles/s41746-020-0253-3)
- Cautionary case: the proprietary sepsis score with AUC 0.63 alerted on 18% of admissions and missed two thirds of cases (section 1). — [Wong et al. 2021](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781307)
- Positive case for human-in-the-loop: at Stanford, a 0–100 deterioration index with one alert threshold (65) notified both nurse and physician and prompted a structured huddle with a checklist, with no mandated treatment. A regression-discontinuity analysis found 10.4 percentage points fewer escalations of care (95% CI −20.1 to −0.8) near the threshold; the mortality effect was not significant and the result was not robust across every bandwidth. — [Gallo et al., JAMA Intern Med 2024](https://jamanetwork.com/journals/jama/fullarticle/2816758)
- Therapists found an unexplained movement-quality score hard to judge without knowing the task behind it. — [Ploderer et al. 2016](https://rehab.jmir.org/2016/2/e9)
- Measurement guidance asks for test-retest ICC above 0.9 before a measure is used for decisions about individuals. — [Shirley Ryan AbilityLab](https://www.sralab.org/statistical-terms-use)

### Inferences
- **Never show the 0–100 score alone.** Beside it show (a) the impairment class, (b) change versus personal baseline with the MDC band, (c) the 2–3 kinematic features that moved most, in clinical words and units ("movement time +0.8 s", "tremor amplitude ×1.6", "path deviation +35%"), each with a mini before/after bar. This is the "feature importance + temporal" combination clinicians asked for.
- **Uncertainty:** show a confidence indicator per session (high / low) driven by data quality (tracking loss, too few repetitions, incomplete game) and suppress trend alerts built on low-confidence sessions; say "based on 4 of 7 expected sessions".
- **Framing text** (always visible near the score): "Decision support, not a diagnosis. The score summarises game performance compared with this patient's own earlier sessions. It has not been clinically validated. Confirm by contacting or examining the patient."
- **Model facts panel** (an "i" icon, one modal): what the model is, inputs, training data and its size, known limits (learning effect, device differences, dominant vs non-dominant hand, not validated per diagnosis), version/date, who to contact.
- **Couple every alert to a human action** rather than an automated consequence: the alert offers a checklist ("call patient; ask about new weakness, falls, wound; decide: reassure / bring forward appointment / urgent referral") and requires an outcome to be recorded. The Stanford result suggests the benefit comes from the structured response, not the score.
- Do not build "patients like this one" panels; evidence suggests they are not valued under time pressure and they take build time.
- Alert wording template: "[Name]: declining hand control. Tracing score 54 (moderate), down 21 from personal baseline 75, below the expected range in 3 consecutive sessions (12–16 Nov). Main changes: slower movement (+0.8 s), more path deviation (+35%). Pain 3/10 unchanged; no red-flag answers. Confidence: high (3/3 sessions complete). Suggested: phone check within 2 working days."

### Gaps
- No study was found testing explanation formats for kinematic or motor-assessment ML scores with clinicians; the evidence is from ICU/ED risk models and is transferred by analogy.
- Regulatory framing (EU MDR software-as-medical-device classification, EU AI Act obligations for high-risk clinical AI) was not researched here and matters for any claim beyond a prototype.
- No quantitative evidence was retrieved on whether showing uncertainty changes clinician decisions or trust.

---

## 5. Red-flag symptoms that should bypass trend logic

### Takeaway
Questionnaire red flags should alert immediately and independently of game trends, and for stroke-type symptoms the patient must be told on screen to call emergency services rather than wait for a clinician. Sources support a short list per population: FAST and related sudden neurological symptoms (stroke); wound infection signs, excessive bleeding, severe or increasing pain and a hand not moving normally by two weeks (carpal tunnel release); neuropathy that interferes with function or is intolerable (CIPN), which is the ASCO trigger for reconsidering chemotherapy dosing.

### Cited Findings

**Stroke** — [NHS, Stroke symptoms](https://www.nhs.uk/conditions/stroke/symptoms/)
- Core signs: facial droop, inability to raise and hold both arms because of weakness or numbness in one, slurred or confused speech; act by calling the emergency number at once.
- Additional symptoms listed: weakness or numbness down one side, blurred vision or loss of sight in one or both eyes, trouble speaking or finding words, confusion and memory loss, dizziness or falling, severe headache, nausea or vomiting.
- Emergency call is advised even when signs appeared in the last 24 hours and have already resolved; patients should not drive themselves.

**Carpal tunnel release**
- An NHS trust aftercare leaflet lists as reasons to seek advice: redness, increasing pain or discharge at the wound (infection); bleeding beyond a little dried blood on the dressing; a hand that is not moving normally by two weeks (stiffness); any severe or increasing discomfort. Expected course: discomfort settling over a few weeks, occasional stabbing or scar pain and aching on gripping for up to 3–4 months. — [Hull University Teaching Hospitals, Carpal tunnel decompression: what to expect following surgery](https://www.hey.nhs.uk/patient-leaflet/28836/)
- Another trust's hand-therapy leaflet sets expectations useful for "normal versus abnormal": full fist and light use by day 14; scar tenderness and reduced power can persist but should resolve by about six months, by which time most people have no pins and needles or numbness; lack of improvement by six months warrants review. — [Cambridge University Hospitals, Hand therapy advice following carpal tunnel release](https://www.cuh.nhs.uk/patient-information/hand-therapy-advice-following-your-carpal-tunnel-release-surgery/)
- The British Society for Surgery of the Hand leaflet says tingling often improves quickly after surgery while grip strength can take several months, and that scar tenderness and stiffness are common and usually settle. — [BSSH, Carpal tunnel syndrome leaflet](https://www.bssh.ac.uk/_userfiles/pages/files/Patients/Conditions/Carpal%20tunnel%20syndrome%20with%20logos.pdf)

**CIPN**
- ASCO's 2020 guideline update: when a patient develops intolerable neuropathy and/or functional impairment, clinicians should assess whether to delay, reduce, substitute or stop chemotherapy. No agent is recommended for prevention; duloxetine is the only drug with supporting evidence for established painful CIPN and its benefit is limited. **[abstract only]** — [Loprinzi et al., J Clin Oncol 2020, PMID 32663120, doi 10.1200/JCO.20.01399](https://pubmed.ncbi.nlm.nih.gov/32663120)
- UK oncology telephone-triage tool, neurosensory/motor row: grade 1 mild paraesthesia or subjective weakness with no loss of function; grade 2 mild–moderate sensory loss, moderate paraesthesia, mild weakness, still no loss of function; grade 3 severe sensory loss, paraesthesia or weakness that interferes with function; grade 4 paralysis. Pain row: moderate pain interfering with daily activities is grade 2; severe is grade 3. Action logic: one amber = clinical review within 24 hours; two ambers = red; red = urgent face-to-face assessment. For anyone on systemic anticancer therapy, temperature of 37.5 °C or above, or below 36.0 °C, or feeling generally unwell requires urgent assessment. (The fetched text did not state which grade maps to which colour for each row.) — [UKONS triage tool v3 poster](https://www.ukons.org/site/assets/files/1224/ukons_triage_tool_poster_a3_v3_final.pdf)

### Inferences
Proposed immediate-alert (RED) questionnaire items; each is a yes/no on the daily form and fires on a single "yes":
- **All patients:** new face droop, new arm or leg weakness, new speech difficulty, sudden vision loss, sudden severe headache, new confusion → patient screen shows "Call 112 now" (EU emergency number; verify locally) and the clinician gets a RED alert for follow-up. The platform must never be the only route for these.
- **Stroke:** add a fall since last report, new swallowing difficulty, sudden worsening of the affected hand noticed by the patient.
- **Carpal tunnel release:** wound redness spreading, discharge or pus, fever, bleeding through dressing, pain increasing rather than decreasing day to day, fingers cold/pale/blue, new complete numbness, fingers cannot be moved, disproportionate burning pain with swelling/colour/temperature change and stiffness (possible CRPS; see Gaps).
- **CIPN:** numbness/tingling now interferes with daily tasks (buttons, writing, walking), a fall or near-fall, new weakness, pain rated severe, and for patients on active chemotherapy fever or feeling generally unwell.
- AMBER (same-day or next-working-day review, not emergency): CIPN symptoms rising to "moderate" without functional loss; carpal tunnel hand not making a full fist by day 14; numbness score rising on 2 consecutive days.
- For CIPN, time the alert to the treatment cycle: the actionable moment is before the next chemotherapy dose, so show "next cycle date" beside the alert.
- Use expected-recovery timelines to suppress false alarms: scar/gripping pain up to 3–4 months and slowly returning grip strength after carpal tunnel release are normal and should not by themselves fire trend alerts.

### Gaps
- **CTCAE v5.0 grade definitions** (grade 2 = limiting instrumental ADL, grade 3 = limiting self-care ADL) could not be read from the NCI source (the PDF link redirected), so the "grade ≥2" trigger in the brief is not cited here; the UKONS grading above is the closest verified wording.
- **Complex regional pain syndrome after carpal tunnel release:** none of the three leaflets opened mentions CRPS or gives incidence; the CRPS item above is uncited clinical reasoning. Budapest criteria and incidence figures need a source.
- **Falls as a CIPN red flag** and **stroke-specific discharge red flags** (beyond the NHS public symptom list) were not confirmed in a guideline read during this session.
- Finger colour/circulation and fever after hand surgery are standard post-operative warnings but were not present in the leaflets retrieved.
- Slovenian or other local guidance and emergency routing were not checked.

---

## 6. Roles and workflow in successful programmes

### Takeaway
Working programmes put a nurse (or equivalent non-physician clinician) in front of the alert queue during defined hours, with a named senior clinician accountable and reachable for escalation; they define response-time classes, require the action taken to be documented, close the loop with a message or call to the patient, and tell patients plainly that the system is not an emergency service.

### Cited Findings
- Dutch RPM centre: dedicated monitoring e-nurses work the alert queue centrally in office hours under daily supervision of a nurse specialist or medical specialist; physicians are pulled in only when needed. Workload planning assumed 5 minutes per administrative and 10 minutes per clinical action. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- TIDE: a certified diabetes care and education specialist reviews only flagged patients, spending on average 4.5 minutes each (about 1.5 reviewing data, 1 documenting in the record, 2 writing the patient a secure asynchronous message), and tracks whether the patient opened the message. During the study a physician first safety-checked the flagged list. — [JMIR Diabetes 2022 e27284](https://diabetes.jmir.org/2022/2/e27284)
- PRO-TECT: alerts for severe or worsening symptoms go to nurses in real time; 59% triggered immediate nurse action. **[abstract only]** — [PRO-TECT alerts abstract](https://mijn.bsl.nl/optimization-of-alert-notifications-in-electronic-patient-report/27117700)
- MSK: alerts land in a shared care-team inbox (median 5 staff); median response time in business hours was 1 hour; red alerts were documented in the EHR in 57% of cases; the organisation set rules for who reviews, reminders, escalation and documentation, trained staff and monitored acknowledgement rates. — [Strachna et al. 2022](https://medinform.jmir.org/2022/11/e38483)
- UKONS response-time classes: amber reviewed within 24 hours; red assessed urgently face to face; life-threatening presentations sent to emergency services. — [UKONS triage tool](https://www.ukons.org/site/assets/files/1224/ukons_triage_tool_poster_a3_v3_final.pdf)
- NEWS2 embeds nurse-first escalation: low aggregate scores are assessed by a registered nurse who decides whether to involve the medical team; higher bands go straight to the medical or critical-care team. — [RCP NEWS2 chart 4](https://www.rcp.ac.uk/media/mrllczrj/news2-chart-4_clinical-response-to-news-trigger-thresholds_0.pdf)
- NHS England virtual wards: a named consultant or GP is accountable for each patient; staffing at least 8am–8pm seven days a week with locally arranged out-of-hours cover; daily board round reviewing every patient under a senior decision-maker; at least daily monitoring; patients and carers must be told whom to contact if symptoms worsen, including out of hours; incident reporting and regular safety review required. No numeric response times are specified. — [NHS England, Virtual wards operational framework](https://www.england.nhs.uk/long-read/virtual-wards-operational-framework/)
- Stanford deterioration-index workflow: alert to nurse and physician together triggers a short structured huddle with a checklist; no specific treatment is mandated. — [Gallo et al. 2024](https://jamanetwork.com/journals/jama/fullarticle/2816758)
- Low agreement between clinicians on what an alert warrants (kappa about 0.3) in simulated telemonitoring. — [PMC5240411](https://pmc.ncbi.nlm.nih.gov/articles/PMC5240411/)

### Inferences
- Model two roles in the UI: **triage nurse/therapist** (owns the queue) and **responsible doctor** (named per patient; receives escalations and RED copies). A single toggle is enough for the demo.
- Alert life-cycle states: New → Acknowledged (who, when) → Action recorded → Closed, plus Snoozed-until. Closing requires picking an outcome from a short list: "Contacted, reassured", "Exercise/therapy plan adjusted", "Appointment brought forward", "Referred urgently", "Could not reach patient (retry)", "False alarm / data problem". The last option feeds threshold tuning.
- Target response times to display as a countdown: RED same day (within about 1 hour in working hours, matching MSK's median), AMBER within 24 hours or next working day, GREY weekly digest.
- Because clinicians disagree on what an alert means, attach a 3–4 item checklist script to each alert type so different staff act consistently.
- Close the loop with the patient: one-tap templated message ("We noticed a change in your results and will call you today") and show "seen by your care team" on the patient side; patients want to know their reports are read.
- Budget argument for the pitch: at about 4.5–10 minutes per flagged patient and a design target of under 10% of patients flagged per week, a 100-patient panel costs roughly 45–100 nurse-minutes per week (10 flagged patients × 4.5–10 min) (arithmetic on the cited per-action times; the flag rate is a design target, not a measured result).
- Put a permanent patient-side notice: the app is not monitored around the clock; for emergencies call 112.

### Gaps
- No programme-level evidence was found for post-discharge motor-function monitoring specifically (stroke, hand surgery, CIPN); all workflow evidence is from oncology symptom monitoring, cardiometabolic RPM, diabetes and hospital early warning.
- Explicit response-time standards for RPM alerts were not found in NHS guidance; only UKONS gives a concrete 24-hour class.
- Symptom Care at Home (Mooney et al.), which uses nurse practitioners with decision-support guidance, could not be opened.

---

## 7. Concrete examples worth imitating (layouts in words)

### Takeaway
Five published designs give directly reusable patterns: TIDE's four-tab flagged-patient table, MSK's colour-labelled alert inbox with documentation tracking, the UKONS one-page RAG grid with a combination rule, the NEWS2 band-to-response chart, and therapist/clinician dashboards that lead with an overview card and keep detail one click away.

### Cited Findings
- **TIDE (Stanford paediatric diabetes).** A table of patients, one row each, with a handful of weekly metrics as columns; only the metrics that broke a rule are highlighted. Tabs split the panel into all / with alerts / no data / data but no alerts. Rules mix fixed targets with personal-baseline deterioration rules. The reviewer picks the review window (default: week ending last Sunday, or last 7 days). The reviewer works down the flagged tab, opens the detailed data only for those, documents, and sends an asynchronous message. An open-source reimplementation exists on GitHub. — [JMIR Diabetes 2022 e27284](https://diabetes.jmir.org/2022/2/e27284); [community reimplementation (unverified code, not reviewed)](https://github.com/flaviagiammarino/stanford-tide-dashboard)
- **MSK PRO alert inbox.** Each alert is a message in a team inbox carrying a colour label (yellow moderate, red-yellow, red severe) set by rule (value plus direction per question). Separate summary dashboards show alert rates and workload for governance; these were used to retune thresholds, for example muting expected post-operative pain. — [Strachna et al. 2022](https://medinform.jmir.org/2022/11/e38483)
- **UKONS triage grid.** A single page: rows are symptoms (pain, neurosensory/motor, infection, fever, fatigue/performance status, consciousness, and others), columns are grades 0–4 with short behavioural descriptions, and a fixed legend converts colours to actions (self-care advice; review within 24 h; urgent assessment), including the rule that two ambers equal a red. — [UKONS poster](https://www.ukons.org/site/assets/files/1224/ukons_triage_tool_poster_a3_v3_final.pdf)
- **NEWS2 chart.** A four-band table linking aggregate score to monitoring frequency, who must be informed and what they must do, with a separate rule for one extreme parameter. — [RCP NEWS2 chart 4](https://www.rcp.ac.uk/media/mrllczrj/news2-chart-4_clinical-response-to-news-trigger-thresholds_0.pdf)
- **Dutch RPM centre.** Alerts typed as simple (one threshold), complex (multi-condition) and overdue/inactivity, with automated workflows closing most of the last type and a per-day-per-user bundle for the rest. — [JMIR Med Inform 2025 e66066](https://medinform.jmir.org/2025/1/e66066)
- **Stroke upper-limb therapist dashboard.** Overview page (weekly counts, daily quality score 1–10, averages, therapist notes) preferred by most therapists; separate tabs for timeline, joints/range of motion, heatmaps and spreadsheet, of which the fine-grained ones were little used; authors recommend consolidating useful views on one page. — [Ploderer et al. 2016](https://rehab.jmir.org/2016/2/e9)
- **CarePortal.** Patient cards → per-patient page with daily summary cards (red for out-of-range) and a line-plus-points trend with range slider; side menu per data type. — [JMIR Form Res 2023 e46866](https://formative.jmir.org/2023/1/e46866)

### Inferences
- Fastest credible layout to build in 20 hours: **TIDE table + MSK colour labels + UKONS legend**. One page with filter chips (Needs review / No data / Stable / All), a table with highlighted-only-if-abnormal cells and a sparkline, and a legend strip stating what each colour obliges the clinician to do and by when.
- Borrow NEWS2's presentation for the rules page: a small table "signal → who is notified → expected response time", which doubles as the explanation of the alert model for judges and clinicians.
- Add a tiny "alert statistics" card (alerts this week, % actioned, median time to acknowledge, % marked false alarm) to demonstrate that the system measures its own burden, as MSK and the Dutch programme did.
- For the demo dataset, seed three patients who tell the story: one stable (no alert), one with a slow EWMA decline crossing the persistence rule (AMBER with explanation), one with a red-flag answer (RED, bypassing trends), plus one with missing data (GREY).

### Gaps
- No RPM vendor documentation or design case study was reviewed in this session, so there are no vendor claims to report or flag.
- Screenshots were not inspected; layouts are described from article text, and TIDE's figure content in particular was not visible.
- Oncology ePRO dashboards used in the eRAPID trial and commercial tools were not retrieved.
