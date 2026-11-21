# Webcam markerless pose and hand tracking (MediaPipe and similar) for rehab assessment and exergames

Scope: stroke upper limb, carpal tunnel (post-surgery wrist/hand ROM, dexterity), CIPN (hand function, balance). Researched 2026-11-21 with about 16 search/fetch calls. Items marked "(snippet)" were confirmed only from search-result summaries, not full text. Items marked "(fetched)" were read on the source page. Several full texts (MDPI, ResearchGate) blocked automated fetches.

## Q1. Accuracy of MediaPipe-type tracking for joint angles and ROM (vs goniometer, Vicon/optical mocap, Kinect)

### Takeaway
Single-camera MediaPipe gives good *reliability* and *correlation*, with ICC often 0.75-0.96. *Absolute* angle error is moderate to poor: about 4° in the best case (finger PIP, lateral view) and 10-20° for the shoulder and elbow in hard conditions. Multi-camera or biomechanically constrained markerless pipelines reach 2-5° RMSE in stroke patients. Practical upshot: track change over time against the user's own baseline, and do not report clinical-grade absolute ROM.

### Cited Findings
**Upper limb (shoulder/elbow) vs optical reference**
- Upper-limb MediaPipe vs optical reference across full and partial ROM tasks: shoulder-angle ICC 0.86-0.96 across all ROM levels. Errors were larger in mid- and late-range trials. One search summary also reports an elbow RMSE of about 13° and a shoulder RMSE of about 15-20° in Paralympic athletes (snippet; the full text returned 403, so these numbers are unverified). The search summary also flagged an unresolved "(citation required)" placeholder in the paper, which is a quality warning. — [Accuracy and Reliability of Markerless Human Pose Estimation for Upper Limb Kinematic Analysis Across Full and Partial Range of Motion Tasks, Applied Sciences 2026, 16(3):1202](https://www.mdpi.com/2076-3417/16/3/1202)
- Unger, Sal Moslehian, Peiffer, Ullrich, Gassert, Lambercy, Cotton, Easthope (2024). 15 stroke patients doing the drinking task. Synchronized webcams plus differentiable biomechanics, compared with marker-based optical mocap. Median RMSE 2-5° across joint angles; median correlation >0.95 for most kinematic trajectories (fetched abstract). This is multi-camera with a biomechanical model, not single-camera MediaPipe. — [Differentiable Biomechanics for Markerless Motion Capture in Upper Limb Stroke Rehabilitation: A Comparison with Optical Motion Capture, arXiv:2411.14992](https://arxiv.org/abs/2411.14992)
- A multi-camera markerless study reports ICC >0.91 for shoulder joints in static poses and studies how camera placement affects results (snippet). — [Optimizing camera placement in multi-view markerless motion capture, BMC Research Notes 2026](https://link.springer.com/article/10.1186/s13104-026-07886-4)
- A 2026 review states that MediaPipe outperformed Kinect in joint-angle estimation, with lower error (snippet; the underlying data was not verified). — [Shenoy et al. 2026, Advancements in markerless motion capture systems for upper limb functional assessment in stroke rehabilitation: A comprehensive review, Digital Health, doi:10.1177/20552076251412636](https://journals.sagepub.com/doi/10.1177/20552076251412636)
- Other MediaPipe rehab-motion reliability and validity studies exist but were not read in full: [Reliability and validity analysis of MediaPipe-based measurement system for some human rehabilitation motions (ResearchGate)](https://www.researchgate.net/publication/369734417_Reliability_and_validity_analysis_of_MediaPipe-based_measurement_system_for_some_human_rehabilitation_motions); [Assessing the Reliability of AI-Based Angle Detection for Shoulder and Elbow Rehabilitation (ResearchGate)](https://www.researchgate.net/publication/377948452_Assessing_the_Reliability_of_AI-Based_Angle_Detection_for_Shoulder_and_Elbow_Rehabilitation); [MediaPipe-based extraction of joint ROM and position (USA Univ., SOAR)](https://soar.usa.edu/cgi/viewcontent.cgi?article=1097&context=phjpt)
- Comparator: Azure Kinect vs digital goniometer for joint ROM was reported as valid and reliable (in weightlifters). — [Azure Kinect for joint range of motion analysis, PMC12637979](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12637979/)

**Lower limb (useful for the full-body option)**
- Single-camera BlazePose vs goniometer for knee flexion at static targets of 30/60/90/120°, with Bland-Altman analysis and ICC(2,1) absolute agreement (snippet; numbers not extracted). — [Validation of Single-Camera MediaPipe BlazePose for Knee Joint Angle Measurement Across Multiple Functional Tasks, PMC13730411](https://pmc.ncbi.nlm.nih.gov/articles/PMC13730411)
- Knee valgus during single-leg drop landing: low concurrent validity for absolute angle. The authors recommend using change relative to a time point. — [Reliability and validity of knee valgus angle calculation at single-leg drop landing by posture estimation using machine learning, Heliyon 2024, PMC11399566](https://pmc.ncbi.nlm.nih.gov/articles/PMC11399566/)

**Hand and fingers (MediaPipe Hands, 21 landmarks)**
- AR smartphone web app built on MediaPipe Hands vs goniometer, 48 healthy hands. Test-retest ICC >0.75 for all joints in flexion. Agreement within 10° of goniometry only for some views and joints (for example index MCP/PIP/DIP from the ulnar view). MCP angles are biased because there is a single wrist landmark and no metacarpal or CMC landmarks. Ring and little fingers track worse. — [Augmented Reality-Based Finger Joint Range of Motion Measurement: Assessment of Reliability and Concurrent Validity, J Hand Surg Am 2024/2025, PubMed 39665730](https://pubmed.ncbi.nlm.nih.gov/39665730/) / [JHS full text](https://www.jhandsurg.org/article/S0363-5023(24)00514-8/fulltext)
- Index-finger PIP during mouse use, MediaPipe vs electrogoniometer: best agreement in lateral view, RMSE 4.22°, ICC 0.92. Frontal view was worse. OpenPose was also compared. — [Validation of AI-Based Finger Joint Angle Estimation Using MediaPipe and OpenPose during Computer Mouse Use, J Biomed Phys Eng](https://jbpe.sums.ac.ir/article_51738.html)
- MediaPipe on smartphone images of 32 hand ROM parameters vs manual goniometry: mean deviation −2.21 ± 9.29°, which the authors call low accuracy. A secondary snippet reports ICC 0.75 and Pearson r ≈0.6 for 84% of parameters (snippet; the paper's bibliographic details were not retrieved). — [ResearchGate table: The 32 ROM parameters and the measurement of MediaPipe and manual methods](https://www.researchgate.net/figure/The-32-ROM-parameters-and-the-measurement-of-MediaPipe-and-manual-methods_tbl1_367784837)
- A multi-plane comparison of finger angles and ROM found the median plane most accurate and reliable (snippet). — [Multi-Plane Comparative Study of Finger Angles and ROM Using MediaPipe, IEEE 11182193](https://ieeexplore.ieee.org/document/11182193/)
- The authors of a markerless hand tracking device study note that MediaPipe's 21 landmarks lack metacarpals, which limits MCP accuracy. — [Verification of Criterion-Related Validity for Developing a Markerless Hand Tracking Device, Biomimetics 2024, 9(7):400, doi:10.3390/biomimetics9070400](https://pmc.ncbi.nlm.nih.gov/articles/PMC11274637/)

**Wrist (carpal tunnel relevance)**
- No MediaPipe wrist-ROM-vs-goniometer study was found. Non-MediaPipe smartphone references: smartphone photography of the wrist (32 people, 64 wrists) showed high concordance with goniometry ([Wagner, Conti Mica, Shin 2018, J Hand Surg Eur, doi:10.1177/1753193417729140](https://doi.org/10.1177/1753193417729140)). A smartphone sensor app and a wearable were accurate in 33 participants ([Engstrand et al. 2021, J Hand Surg Eur, doi:10.1177/17531934211004454](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8649412/)). An app (Angulus) correlated with goniometry at r 0.44-0.81 ([PMC11088398](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11088398/)). A wearable-controlled serious game for wrist fracture rehab was validated against a goniometer ([PMC9001232](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9001232/)).

### Inferences
- For a hackathon game, MediaPipe angles are good enough for a relative score: rep counting, % of the user's own max ROM, and trend over sessions. They are not good enough to claim degrees comparable to a goniometer, especially for shoulder flexion seen frontally, where depth matters, and for MCP/wrist.
- Camera view matters a great deal. Shoulder abduction and elbow flexion are in the frontal plane, so a front-facing webcam works best for them. Shoulder flexion and finger flexion need a side or lateral view, or the error grows.
- Hand ROM is most trustworthy for PIP/DIP with a lateral or ulnar view. Avoid relying on MCP and wrist flexion/extension angles from a frontal palm view.

### Gaps
- No MediaPipe wrist flexion/extension or radial/ulnar deviation validation against a goniometer was found. Nothing in carpal tunnel or CIPN populations.
- The exact MAE/RMSE per joint for the 2026 Applied Sciences study and for the BlazePose knee study could not be verified (403 or snippet only).
- No head-to-head single-webcam MediaPipe vs Kinect RMSE study for shoulder/elbow in rehab was verified.

## Q2. Automated clinical-scale scoring from video keypoints (stroke FMA/ARAT, Parkinson finger tapping)

### Takeaway
Finger tapping (MDS-UPDRS 3.4) is the most mature video task. MediaPipe thumb-index distance features plus an interpretable classifier reach about 80% exact and about 93% within ±1 accuracy, comparable to expert agreement, but on small test sets. Automated FMA from cameras reports 78-99% accuracy depending on item and setup. Most of that work uses Kinect or small samples, and MediaPipe-only FMA is still proof-of-principle.

### Cited Findings
**Finger tapping (Parkinson's)**
- Yu, Park, McKeown, Wang (2023), *Sensors* 23(22):9149, doi:10.3390/s23229149 (fetched). 75 videos from 50 PD patients, with 60 for training and 15 for testing. Pipeline: MediaPipe 3D hand, thumb-tip (K4) to index-tip (K8) distance normalized by palm size, then EMD denoising, then peak detection, then 15 features (amplitude, velocity, hesitation, count, age, sex), then a Decision Tree. Exact accuracy 80%, ±1 accuracy 93.3%, F1 0.797. Baselines reached 26.7-46.7% exact. Two neurologists agreed exactly on only 52% of videos and within ±1 on 97%. Limitations: tiny test set, controlled settings, data not public. — [Clinically Informed Automated Assessment of Finger Tapping Videos in Parkinson's Disease](https://pmc.ncbi.nlm.nih.gov/articles/PMC10674854/)
- Inter-rater ICC between neurologists for MDS-UPDRS finger tapping was only 0.53-0.65 in 250 participants. A 2025 arXiv model reached 55.95% accuracy vs 47.51% for Islam et al., whose model used MediaPipe wrist, thumb-tip and index-tip (snippet). — [arXiv 2506.18925](https://arxiv.org/html/2506.18925)
- In a MediaPipe Hand study of 183 videos, the automated score correlated with the MDS-UPDRS FT score at r = 0.819 (right) and r = 0.783 (left) (snippet; the specific paper among the results was not confirmed). — [search result cluster incl. Characterizing Disease Progression in PD from Videos of the Finger Tapping Test, PMC11260436](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11260436/)
- 2026 npj Parkinson's Disease paper: interpretable, granular finger-tapping quantification. It introduces a large finger-tapping dataset of 4,073 videos and reports higher accuracy in MDS-UPDRS prediction (snippet). — [Interpretable and granular video-based quantification of motor characteristics from the finger-tapping test in PD, npj Parkinson's Dis 2026](https://www.nature.com/articles/s41531-026-01307-w)
- 2026 JNER: 51 people with PD (normal or slight on the FT item) and 43 healthy controls, filmed across 15 sites under non-standardized conditions to detect early bradykinesia (snippet). — [Automated video analysis for early detection of bradykinesia in PD, J NeuroEng Rehabil 2026](https://link.springer.com/article/10.1186/s12984-026-01885-z)
- Video-based hand pose for remote bradykinesia assessment. — [arXiv 2308.14679](https://arxiv.org/pdf/2308.14679)

**Stroke FMA / upper-limb**
- Vision-based automated FMA-UE scoring system (camera motion features plus MLP): about 98.9% accuracy on 15 volunteers and about 97.7% on a patient dataset (snippet; patient n unclear). — [Vision-based Automated Fugl-Meyer Assessment System for Upper Limb Motor Function, IEEE 10442224](https://ieeexplore.ieee.org/document/10442224)
- Kinect-based automated FMA, 10 stroke patients: 92% scoring accuracy and 85% less clinician time (snippet). — [Automated Evaluation of Upper-Limb Motor Function Impairment Using Fugl-Meyer Assessment, IEEE TNSRE 2017/2018, PubMed 28952944](https://pubmed.ncbi.nlm.nih.gov/28952944/)
- Kinect depth camera FMA-UE scoring in 41 hemiplegic patients. — [Upper Extremity Functional Evaluation by FMA Scoring Using Depth-Sensing Camera, PMC4930182](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4930182/)
- Video-based scoring of 16 FMA items in acute stroke: 78.1-82.7% average per-item accuracy depending on the model (snippet). — [Abnormal Motion Capture In Acute Stroke (Bionics), UTHealth](https://digitalcommons.library.tmc.edu/cgi/viewcontent.cgi?article=1481&context=uthmed_docs)
- MediaPipe used to track reaching after stroke in a proof-of-principle study (n = 7) (snippet). — [Using MediaPipe to track upper-limb reaching movements after stroke: a proof-of-principle study](https://www.researchgate.net/publication/397952994_Using_MediaPipe_to_track_upper-limb_reaching_movements_after_stroke_a_proof-of-principle_study)
- Hawe, Ziccardi, Asante, Guy (2025), *Restorative Neurology and Neuroscience* 44(1):37-48, doi:10.1177/09226028251408783 (fetched). MediaPipe Pose v0.10.13, a single frontal GoPro, the CAHAI-7 bilateral tasks, and 3 participants (1 control, 2 chronic stroke with FMA-UE 61 and 44). Measures: the shoulder/elbow/wrist position point-cloud area (minimum-volume ellipse, normalized by shoulder width) and a laterality index. The more impaired patient had a wrist LI of −0.32 vs −0.08 for the control, and shoulder area 9.4-10.9× the control's (compensation). No correlation with clinical scales was computed. CAHAI showed a ceiling effect (49/49) while the video showed differences. — [A Picture is Worth a Thousand Clinical Assessments, PMC13044263](https://pmc.ncbi.nlm.nih.gov/articles/PMC13044263/)
- Human FMA inter-rater reliability is a baseline worth comparing against (ESTREL study). — [Interrater reliability of the Fugl-Meyer Motor assessment in stroke patients, PMC11034517](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11034517/)
- 3D motion capture for FMA testing. — [Eichler et al. 2018, IET Computer Vision, doi:10.1049/iet-cvi.2018.5274](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-cvi.2018.5274)

### Inferences
- The best-supported browser-implementable "clinical-like" metric is MediaPipe-Hands finger tapping (thumb-index distance time series). Use amplitude, speed, decrement and hesitations, normalized by hand size. It applies directly to CIPN and post-CTS dexterity, even though it was validated in PD.
- For stroke, a realistic hackathon claim is "proxy features correlated with impairment": ROM, smoothness, trunk compensation (shoulder displacement) and asymmetry. Automated FMA itself is out of reach.
- Interpretable features plus a simple classifier matched or beat deep end-to-end models on small data (Yu 2023). This argues for engineered features alongside or instead of a CNN in a hackathon.

### Gaps
- No MediaPipe-based automated ARAT study was found.
- No study validates video finger tapping in CIPN or carpal tunnel populations.
- The patient sample size for the 98.9%/97.7% IEEE FMA system was not confirmed.

## Q3. Validated, simple exercises implementable in the browser (MediaPipe JS / tasks-vision)

### Takeaway
The best-supported exercises, with the camera view each needs:
- Shoulder abduction and lateral raise: frontal view; shoulder ICC 0.86-0.96.
- Elbow flexion/extension: frontal view.
- Drinking or reach-to-mouth task: validated in stroke with markerless mocap.
- Finger tapping (thumb-index): best validated scoring.
- Finger flexion/extension (hand open/close): PIP/DIP reliable, MCP not; lateral view is better.
- Bilateral ADL-like tasks: for asymmetry and compensation.

Sit-to-stand and balance have smartphone-sensor validation, but no MediaPipe validation was found.

### Cited Findings
- Shoulder flexion/abduction ROM tracked reliably across full and partial ROM (ICC 0.86-0.96). — [Applied Sciences 2026, 16(3):1202](https://www.mdpi.com/2076-3417/16/3/1202)
- Drinking task in stroke: markerless mocap with 2-5° median RMSE. — [Unger et al. 2024, arXiv:2411.14992](https://arxiv.org/abs/2411.14992)
- Reaching after stroke with MediaPipe (proof of principle). — [ResearchGate 397952994](https://www.researchgate.net/publication/397952994_Using_MediaPipe_to_track_upper-limb_reaching_movements_after_stroke_a_proof-of-principle_study)
- Bilateral CAHAI-7 tasks (ruler line, pouring, buttoning, towel drying) with MediaPipe Pose: no frames where pose extraction failed (snippet). Fingers were not tracked because of occlusion. — [Hawe et al. 2025, PMC13044263](https://pmc.ncbi.nlm.nih.gov/articles/PMC13044263/)
- Finger tapping via MediaPipe Hands, thumb-index distance (K4-K8) normalized by palm size. — [Yu et al. 2023, Sensors, doi:10.3390/s23229149](https://pmc.ncbi.nlm.nih.gov/articles/PMC10674854/)
- Finger flexion ROM via MediaPipe Hands in a smartphone web app (so it is feasible in a browser). Test-retest ICC >0.75. Best with ulnar or lateral view. — [J Hand Surg, PubMed 39665730](https://pubmed.ncbi.nlm.nih.gov/39665730/)
- Sit-to-stand: smartphone accelerometer timing agreed with force plate/mocap (mean difference 0.04 s, ages 65-89) ([J Aging Phys Act 2021, 30(1)](https://journals.humankinetics.com/view/journals/japa/30/1/article-p3.xml)). A smartphone app correlated with force plate at r = 0.86-0.93 ([Gait & Posture, S0966636214007541](https://www.sciencedirect.com/science/article/abs/pii/S0966636214007541)). A sit-to-stand *video-analysis* app was used for sarcopenia diagnosis in JMIR 2023 ([doi:10.2196/47873](https://doi.org/10.2196/47873)).
- Balance: smartphone postural stability was valid in 97 older adults, with lower test-retest reliability than a force plate. — [PMC7961526](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7961526/)

### Inferences (design suggestions, not validated claims)
- **Upper-body game, front webcam (MediaPipe Pose Landmarker):**
  - Lateral raise/abduction "reach the stars": shoulder angle = angle(hip-shoulder-elbow).
  - Elbow flexion "pump": angle(shoulder-elbow-wrist).
  - Reach-to-target in 2D, scoring path smoothness (jerk), time and trunk compensation (shoulder-midpoint displacement).
  - Scoring: reps, max angle as % of baseline, symmetry index between left and right.
- **Hand game (MediaPipe Hand Landmarker):**
  - Finger tapping "rhythm" game: thumb-index distance / palm size, scoring amplitude, frequency and decrement. Relevant to CIPN and CTS.
  - Finger-thumb opposition sequence (thumb tip touching each fingertip in order): distance thresholds between landmark 4 and landmarks 8, 12, 16, 20.
  - Hand open/close "squeeze": a mean fingertip-to-wrist distance or a PIP angle sum.
  - Wrist flexion/extension: forearm-to-middle-MCP vector angle. This one has the weakest validation.
- **Full-body option:** sit-to-stand counting via hip y-coordinate (30-s STS), and a tandem/single-leg stance balance game scoring hip/shoulder-midpoint sway. Present these as unvalidated MediaPipe proxies.
- Use MediaPipe's world landmarks (metric 3D, hip-centered) for angles, but treat z as unreliable. Prefer planar angles in the plane facing the camera.

### Gaps
- No MediaPipe validation found for sit-to-stand, standing balance or finger-thumb opposition.
- No studies of MediaPipe exergames in CIPN were found (not specifically searched in depth because of the call budget).

## Q4. Public datasets with keypoints and quality scores

### Takeaway
KIMORE is the main dataset with continuous expert quality scores (0-100; Kinect RGB-D plus skeleton; low-back exercises). UI-PRMD has 10 healthy subjects with correct/incorrect reps and distance-derived scores. IntelliRehabDS has binary correct/incorrect labels. Toronto Rehab Stroke Pose has stroke upper-body compensation labels. StrokeRehab is IMU-based ADL action segmentation. None was captured with MediaPipe, so you would need to map Kinect joints to MediaPipe landmarks, or re-extract MediaPipe landmarks from RGB where it is provided (KIMORE includes RGB).

### Cited Findings
- **KIMORE**: Capecci et al. 2019, IEEE TNSRE 27(7):1436-1448, doi:10.1109/TNSRE.2019.2923060. Kinect v2 RGB, depth and skeleton data; 5 low-back-pain exercises; clinician scores (continuous 0-100); hosted on a UNIVPM OneDrive link; described as free, but no explicit license found ([KIMORE page, UNIVPM VRAI](https://vrai.dii.univpm.it/node/204704)). Subject count conflicts: 78 subjects (44 healthy, 34 with motor dysfunction) per one summary vs 71 (40 healthy, 31 unhealthy) per [arXiv 2507.21018](https://arxiv.org/pdf/2507.21018). One score per exercise is shared by all repetitions ([arXiv 2507.21018](https://arxiv.org/pdf/2507.21018)).
- **UI-PRMD**: Vakanski et al. 2018, *Data* 3(1):2, doi:10.3390/data3010002. 10 healthy subjects, 10 exercises, correct and incorrect reps; Vicon plus Kinect full-body joint positions and angles; scores in benchmarks are derived from distance functions, not experts ([arXiv 2507.21018](https://arxiv.org/pdf/2507.21018)). The article is CC BY 4.0; the data license was not confirmed ([Crossref](https://api.crossref.org/works/10.3390%2FDATA3010002)).
- **IntelliRehabDS (IRDS)**: 29 individuals (15 patients), 9 exercises, Kinect 25 joints, binary correct/incorrect labels. — [arXiv 2507.21018](https://arxiv.org/pdf/2507.21018). (The data descriptor is believed to be Miron et al. 2021, *Data* 6(5):46. This citation is from training memory and was not verified this session.)
- **Toronto Rehab Stroke Pose (TRSP)**: 10 healthy and 9 stroke participants doing seated upper-limb motions with a rehab robot; Kinect 3D positions and orientations of upper-body joints; compensation annotated by 2 experts; healthy participants also simulated compensations. A later classifier reached 92%. Distributed on Kaggle. — [Dolatabadi et al. 2017, PervasiveHealth, doi:10.1145/3154862.3154925](https://dl.acm.org/doi/pdf/10.1145/3154862.3154925); [Applied Sciences 2024, 14(15):6700](https://www.mdpi.com/2076-3417/14/15/6700)
- **StrokeRehab**: benchmark for sub-second action identification (functional primitives) in stroke ADLs (face washing, deodorant, hair combing, glasses, eating bread, drinking, tooth brushing, target-array object moving); 9 Noraxon IMUs on the upper body. Video availability was not confirmed. The page fetch was blocked by a bot check. — [StrokeRehab: A Benchmark Dataset for Sub-second Action Identification, NeurIPS 2022 Datasets, PMC10530637](https://pmc.ncbi.nlm.nih.gov/articles/PMC10530637/)
- **Others**: University of Liverpool Rehabilitation Exercise Dataset ([PMC12062305](https://pmc.ncbi.nlm.nih.gov/articles/PMC12062305)); UL-RED, with 3 upper-body exercises from 21 people (12 with low back pain, 9 healthy) (snippet); an NRC upper-limb RGB-D plus IMU dataset ([arXiv 2510.00049](https://arxiv.org/pdf/2510.00049)). A standardized deep-learning benchmark across KIMORE, UI-PRMD and IRDS: [arXiv 2507.21018](https://arxiv.org/pdf/2507.21018). Quality assessment with contrastive learning on these datasets: [arXiv 2403.02772](https://arxiv.org/html/2403.02772v1). Point-cloud transformer for rehab assessment: [arXiv 2606.30309](https://arxiv.org/pdf/2606.30309). Repetition segmentation and counting: [arXiv 2304.09735](https://arxiv.org/pdf/2304.09735). Lee et al. stroke exercise quality (IUI 2019): [PDF](https://vislab.isr.tecnico.ulisboa.pt/wp-content/uploads/2019/05/mlee-iui2019.pdf).
- Finger tapping: the 2026 npj paper describes a 4,073-video dataset; whether it is public was not verified ([Nature](https://www.nature.com/articles/s41531-026-01307-w)). The Yu 2023 data is not public ([PMC10674854](https://pmc.ncbi.nlm.nih.gov/articles/PMC10674854/)).

### Inferences
- For a CNN/1D-conv or temporal model on angle time series, KIMORE is the best pretraining and validation source. Compute the same joint angles (shoulder, elbow, trunk) from Kinect joints and from MediaPipe so the feature space is shared.
- With 1-day data, a team could self-record a small labelled set (good / compensated / partial reps), copying the TRSP idea of simulated compensation.

### Gaps
- Exact licenses for KIMORE, IRDS and TRSP were not confirmed. Check the download pages.
- No public dataset of MediaPipe-captured upper-limb rehab exercises with clinical quality scores was found.

## Q5. Limitations (lighting, occlusion, depth, 2D vs 3D)

### Takeaway
The main failure modes are depth ambiguity with a single frontal camera (sagittal-plane motion such as shoulder flexion is poorly estimated), self- and object-occlusion of the hands and fingers, view dependence of finger angles, a missing metacarpal/CMC model, model-version drift, and untested robustness to lighting. Relative measures (change from baseline) are more trustworthy than absolute angles.

### Cited Findings
- Single camera and frontal plane: poor sagittal motion estimation, no depth captured by the area metric, fingers not tracked because of occlusion, object occlusion and lighting variation noted, and results tied to the MediaPipe version (v0.10.13). — [Hawe et al. 2025, PMC13044263](https://pmc.ncbi.nlm.nih.gov/articles/PMC13044263/)
- Finger angles are accurate only in some views. MCP is biased by the single wrist landmark. Ring and little fingers are worse. — [J Hand Surg, PubMed 39665730](https://pubmed.ncbi.nlm.nih.gov/39665730/); [Biomimetics 2024, PMC11274637](https://pmc.ncbi.nlm.nih.gov/articles/PMC11274637/)
- Frontal view was much worse than lateral for finger PIP. — [JBPE](https://jbpe.sums.ac.ir/article_51738.html)
- Larger errors in mid and late ROM. — [Applied Sciences 2026](https://www.mdpi.com/2076-3417/16/3/1202)
- Low validity for absolute frontal-plane knee angle; use change scores. — [Heliyon 2024, PMC11399566](https://pmc.ncbi.nlm.nih.gov/articles/PMC11399566/)
- Lighting, positioning and camera angle were not examined. Low-quality videos had to be excluded manually. — [Yu et al. 2023, PMC10674854](https://pmc.ncbi.nlm.nih.gov/articles/PMC10674854/)
- Multi-camera setups with a biomechanical model reduce error to 2-5°. — [Unger et al. 2024, arXiv:2411.14992](https://arxiv.org/abs/2411.14992); camera placement matters ([BMC Res Notes 2026](https://link.springer.com/article/10.1186/s13104-026-07886-4))

### Inferences
- In the app, add a calibration/setup screen: distance from the camera, full upper body in frame, lighting check, and a side view for flexion tasks. Also show the per-frame landmark visibility score and reject low-visibility frames.
- Normalize by body scale (shoulder width, palm size), smooth landmarks (for example a One-Euro or Savitzky-Golay filter), and compute angles in 2D for frontal-plane movements.
- Present outputs as "progress vs your baseline", not as clinical ROM degrees or scale scores.

### Gaps
- No quantitative study isolating the effect of lighting or skin tone on MediaPipe joint-angle error was found within the call budget.
- No primary BlazePose or MediaPipe Hands technical paper (Bazarevsky et al. 2020; Zhang et al. 2020) was fetched in this session.
