# Design System: Okrevanje doma

## Overview
A calm public-health portal in the spirit of Slovenia's zVEM: a white header that fades into a cool blue-grey page, large white panels with generous rounding, slate-blue controls, a green brand accent and one red hero action. Light theme only. Desktop first (content column 1240 px), usable on a phone. Tokens live in `frontend/src/index.css`; use the Tailwind classes named below, never raw hex in components.

## Colors
### Primary — slate blue `--primary` #3d6880
Links, field borders and text inside fields, default buttons, chart main line. Classes: `text-primary`, `bg-primary`, `border-input`.
### Brand — green `--brand` #4c8f2f, `--brand-ink` #3c7624
Emphasis words inside headings (as zVEM does: "Portal **zVEM** je …"), positive marks, "done" states. `text-brand` for large text only; `text-brand-ink` for text under 24 px.
### Hero action — red `--cta` #c9403b
Exactly one per patient screen: the action that moves the patient forward (`<Button variant="cta" size="xl">`). Never on clinician screens.
### Status (clinician only)
`status-red` / `status-red-bg` ("Nujno"), `status-amber` / `status-amber-bg` ("Za pregled"), `status-grey` / `status-grey-bg` ("Brez podatkov", "Stabilno", "Premalo sej"). Always icon + word + colour.
### Neutral
Page `bg-background` #edf1f4; panels `bg-card` white; ink `text-foreground` #1b2328; secondary text `text-muted-foreground` #566772; hairlines `border-border` #d5dee5; quiet fills `bg-muted`, `bg-accent`.
### Named rules
- **Red means two different things on two sides and they never meet.** Patient side: the hero button. Clinician side: "Nujno". No red anything else.
- **No green for "stable".** Stable patients are grey.
- **Colour on a tinted surface:** secondary text takes the surface's hue (e.g. `text-status-amber` on `bg-status-amber-bg`), never grey.

## Typography
Hanken Grotesk (self-hosted variable, 400–700), one family for everything.
### Hierarchy
- Page title: 36 px / 700, tracking −0.02em, sits on the page background above the first panel (`PageTitle`).
- Panel heading: 24 px / 700.
- Body: 17 px / 400, line-height 1.55. Patient screens may go to 20 px for the key sentence.
- Label / meta: 14–15 px / 500, `text-muted-foreground`. No uppercase eyebrow labels above headings.
- Numbers in tables and charts: `tabular` utility.

## Layout
- Shell (`src/app/AppShell.tsx`): prototype strip, white header (wordmark and patient selector left, view switch right), gradient fade, then content.
- A screen is a `PageTitle` followed by one to three `Panel`s (`src/components/app/Panel.tsx`) with 24 px gaps. Do not nest panels; inside a panel separate groups with space and hairlines (`border-t border-border`), as zVEM's timeline rows do.
- Patient screens: a single centred column, at most ~880 px of content, one decision at a time.
- Clinician screens: full 1240 px column; rows and tables with hairline separators and a trailing arrow, not cards per row.

## Elevation & Depth
One soft shadow for panels (`shadow-panel`), nothing else. Popovers use the shadcn default. No borders on panels.

## Shapes
Panels `rounded-panel` (28 px). Controls and buttons `rounded-lg` (8 px). Badges `rounded-md`. Circles only for avatars, dots and the rating buttons.

## Components
### Buttons
`variant="cta" size="xl"` (red hero), `variant="default"` (slate, filled), `variant="outline"` (slate text, slate border, white fill), `variant="ghost"`. Sizes: default 40 px, `lg` 48 px, `xl` 56 px. Patient screens use `lg` and `xl` only.
### Fields
White fill, 1 px `border-input`, text in `text-primary`, 44 px high.
### Rows
Hairline-separated, 72–88 px high, leading status, name in 600, trailing arrow (`ArrowRight`) in `text-primary`; whole row is the link; hover `bg-muted`.
### Charts (Recharts)
Main line `--chart-1` slate 2.5 px, comparison `--chart-4`, baseline band `bg-muted`-like fill, grid hairlines `--border`, axis text 13 px `--muted-foreground`. Words on axes where the plan asks for them. No gradients under lines.
### Icons
lucide-react, 1.75–2 px stroke, slate or ink; never emoji.

## Do not
Gradient text, glass, side-stripe borders on boxes, nested cards, emoji as icons, uppercase kicker labels, any call-to-phone element on patient screens.
