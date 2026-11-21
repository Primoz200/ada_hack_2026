# Product

Okrevanje doma: a research prototype (AdaHack 2026, challenge by Ixtlan Team, makers of zVEM and zVEM+) for following patients between check-ups when motor function may deteriorate (stroke, carpal tunnel release). Direction below was inferred from the team's written brief and zVEM screenshots, not from an interview.

## Platform
Web, desktop first (it is recorded on a laptop for a 3-minute pitch). Must stay usable on a phone.

## Stack
Vite, React 19, TypeScript, Tailwind 4, shadcn/ui (radix), Recharts 3, lucide-react. FastAPI backend.

## Users
- **Patient at home**, often older, recovering, possibly using the affected hand. Wants to be done in two minutes and to know, in plain words, how it went.
- **Clinician** (doctor or nurse) with very little time. Opens the list, wants to see in seconds who needs attention and why, then decides whether to call the patient before the planned visit.

## Product Purpose
The patient does a short daily self-check ("Samopregled"): two ratings (wellbeing, pain; 1–10) and three tracing games that measure hand movement. The system compares each patient with their own baseline and flags a slow decline to the clinician, who may be weeks away from the next visit.

## Positioning
A module that could live inside zVEM (patient) and zVEM+ (clinician). It should look at home there.

## Operating Context
Shown through screenshots and a short screen recording in a pitch. The key story: one poor self-check by a slowly declining patient → the patient is told calmly that the trend is going down → the clinician sees "Za pregled" while the next visit is a month away.

## Capabilities and Constraints
- The patient is NEVER told to call anyone and never sees alarms, red screens, scores or impairment classes. Alert states belong to the clinician only.
- The patient sees no exhaustive statistics: one sentence and a small chart.
- The system does not diagnose; it shows deviation from the patient's own baseline. All data is synthetic and labelled so.
- All copy is Slovenian, formal "vi".

## Brand Commitments
Calm, trustworthy, public-health. Visual kinship with zVEM (see DESIGN.md) without copying its logo.

## Product Principles
1. One obvious next step on every patient screen.
2. Words before numbers; a number always comes with what it is compared to.
3. Status is never colour alone: icon and word too. Stable is neutral grey, not green.
4. The clinician reads the list in half a minute; detail lives one click deeper.

## Accessibility & Inclusion
Large targets (≥ 48 px on patient screens), body text ≥ 17 px, contrast ≥ 4.5:1, visible keyboard focus, no sliders or drag controls outside the tracing game itself.
