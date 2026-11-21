# Ixtlan Team challenge brief — primary source (user-provided PDF)

Source: "Daljša predstavitev - Ixtlan Team AdaHack 2026.pdf" (22 slides), handed to teams by the sponsor; in the team's repo root. Everything below is taken directly from the slides (verified, primary source). Slovenian wording kept where it matters.

## Sponsor
- Ixtlan Team: 25+ years designing information systems and custom software for ministries, agencies and public administration.
- "Our contribution to Slovenian healthcare": portal **zVEM** has 700,000+ registered users; **zVEM+** application is used by 3,600+ healthcare workers. About 100 employees (slide shows "100").
- They frame work as two roles the teams must combine: business analyst (requirements/process analysis, UI, functional specs) and development engineer (architecture/microservices, code and databases, technical documentation). Shared: analytical thinking, **data model**, testing, teamwork. Motto: "Vse se začne z razumevanjem."
- Contact: izzivi@ixtlan-team.si

## The challenge
- Title: "Skrb za paciente po odpustu iz bolnišnice" — "Kako lahko z digitalno rešitvijo izboljšamo okrevanje pacientov po odpustu iz bolnišnice?"
- Background: at discharge, care for recovery moves to the patient and their relatives; recovery at home is affected by measurable and subjective factors; healthcare staff have limited insight into the course of recovery ("izgubljen vpogled").
- Task: design a digital solution for better recovery after discharge. FOR PATIENTS: better support in recovery outside the institution. FOR HEALTHCARE WORKERS: monitoring patients' progress.
- Starting questions (team decides, must justify): (1) who is it for and who will use it, (2) how will it collect recovery data, (3) which functions for patients and staff.

## Additional clarifications
1. Stakeholders: PATIENT ↔ relatives/caregivers (svojci, skrbniki) ↔ community nursing (patronaža, home visits) ↔ personal/family doctor ↔ HOSPITAL TEAM. Hint: "bližnji so pomemben deležnik" — care after discharge is often taken over by relatives; consider who needs which information and who can act.
2. Concrete hospitalisation examples: operations (hip/knee replacement), chronic diseases (heart failure, COPD, diabetes), vulnerable groups (elderly living alone). Hint: "raje ožje in dobro kot široko in površno" — choose ONE concrete scenario (one procedure type or one patient group) and work it out well.
3. Adoption and usability: needs of patients and relatives + needs of staff; "Uporaba v praksi je ključna" — the solution only has an effect if users want to use it in everyday recovery and work.

## Three extra hints
1. The solution does not replace the doctor. It MAY support monitoring at home and warn patient and staff about deviations. It may NOT diagnose or replace the doctor's professional judgement. "Kdaj in kako se v proces vključi človek?"
2. Staff time is limited: the solution must justify any extra time staff spend supporting patients.
3. Do not forget subjective factors: measurable (body temperature, wound state, taking medication) AND subjective (well-being, uncertainty, doubts) together. "Dejavniki so del izziva in tudi kriterij inovativnosti."

## Existing eZdravje solutions
- Portal zVEM (zvem.ezdrav.si/portal), eZdravje services and zVEM+ (ezdrav.si/resitve). Integration is not mandatory but is a plus if the team shows how the solution would fit into existing systems.

## Expected at the end: presentation with a working prototype
1. Chosen scenario and users (who it is for, which type of recovery)
2. Solution concept (key functions per stakeholder)
3. Data collection (how the solution captures and records data)
4. Working prototype (demonstration of the key usage flow)
5. Introduction into practice (why users will want to use it)

## Judging criteria
1. Potential for social impact
2. Degree of innovation
3. Presentation of the solution
4. Code or working demo

## From the team (user, 21 Nov 2026)
- Pitch is 2–3 minutes. Frontend is React. UI language Slovenian. Deadline Sunday ~12:00. Games are written by Primož as components in the same frontend. Patient reports via games + short questionnaire. Demo level (role switch, SQLite, synthetic patients, HTTPS).

## Team decisions after reading the brief (user, 21 Nov 2026 ~16:00) — these override the coordinator's reading below
- Scenario: the team keeps its framing. The "narrow scenario" is: conditions/injuries where deterioration of motor function is not unusual after discharge. The pitch will name stroke AND carpal tunnel release as two contrasting examples: after stroke, check-ups are frequent; after carpal tunnel release they are rare, so monitoring during the long gaps between visits and timely notification of negative trends matters even more. CIPN stays a possible extension. The report must respect this decision (it may note the risk and advise how to make the framing read as one coherent scenario, but must not re-argue for dropping conditions).
- Roles in the prototype: patient and doctor. Relatives/caregivers maybe later, not a priority (cover them in concept/pitch, e.g. via existing zVEM pooblastila, not as built functionality).
- Phone-as-controller game: not decided by the user; coordinator's working assumption is that it is NOT in the core build (mouse tracing + webcam games first), with the interface foreseen and built only if time remains.
- Timeline note from the hackathon site (found by a researcher): "Hacking stops — Sun 11.00 — No more commits!", demos Sun 13:00–15:00, 3 minutes on stage. The user said deadline is Sunday noon; treat 11:00 as the safe code freeze until the team confirms.

## Coordinator's reading of the gap versus the team's current plan
- Current plan targets three populations (stroke, carpal tunnel release, CIPN); the brief explicitly asks for one well-developed scenario.
- Current plan has no role for relatives/caregivers, community nurse or family doctor; the brief names them.
- Current plan argues against subjective reporting; the brief makes subjective factors (well-being, uncertainty, doubts) a criterion of innovation — the product should combine objective game measurements with subjective reporting.
- Showing where it plugs into zVEM (patient) and zVEM+ (staff) directly addresses the sponsor's own products.
