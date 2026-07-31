---
name: Meridian
description: A light, hairline-ruled operator console where colour is reserved for money.
colors:
  ink: "#050505"
  ink-muted: "#585450"
  paper: "#ffffff"
  paper-raised: "#fbfaf8"
  bone: "#f8f5f2"
  bone-deep: "#f1ece8"
  chip: "#f3f3f3"
  rule: "#e7e3df"
  rule-strong: "#d9d4cf"
  gain: "#0c6a3b"
  caution: "#6e4a00"
  loss: "#b3242c"
typography:
  display:
    fontFamily: "Geist, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "28px"
    fontWeight: 500
    lineHeight: 1.18
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Geist, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "20px"
    fontWeight: 500
    lineHeight: 1.18
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Geist, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Geist, system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.011em"
  label:
    fontFamily: "'Geist Mono', ui-monospace, SFMono-Regular, monospace"
    fontSize: "10px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.16em"
  figure:
    fontFamily: "'Geist Mono', ui-monospace, SFMono-Regular, monospace"
    fontSize: "28px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "-0.04em"
    fontFeature: "tabular-nums"
rounded:
  bar: "2px"
  control: "10px"
  card: "12px"
  pill: "999px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "20px"
  s6: "24px"
  s8: "32px"
  s10: "40px"
  s12: "48px"
components:
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "9px 15px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.ink}"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper-raised}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "9px 15px"
    height: "44px"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.loss}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "44px"
  card:
    backgroundColor: "{colors.bone}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "{spacing.s6}"
  drawer:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    width: "430px"
  label-eyebrow:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
---

# Design System: Meridian

## Overview

**Creative North Star: "The Clear Desk"**

Meridian is a solo operator's morning console. It answers one question — *is anything waiting for
me?* — and it answers it on a white ground with nothing hidden and nothing performing. The surface
is a clear desk: paper-white, warm bone panels ruled off by hairlines, and no shadow anywhere. Depth
comes from tone and rule alone, so a card sits *beside* the page rather than floating above it.
Nothing on this desk is decorative. If an element carries no measurement, it carries no colour.

The system was converted in full from a named reference — the Omega template
(`nextjsshop.com/templates/omega`) — chosen by the operator. What carried over is real and measured:
its two faces, its warm bone panel family, its hairline-and-tone separation, its full-pill controls,
its mono micro-label sitting above a large bare figure. What did not carry over is its scale.
Omega is a marketing surface with room to breathe; Meridian is a four-column setup×regime matrix a
person reads every morning. The grammar transferred; the spacing compressed.

The strictest inheritance is the absence of an interaction colour. Omega's primary action is a
black pill, not a blue one, and adopting that sharpened a rule Meridian already had into something
absolute: **colour now belongs to measurement alone.** There is no accent hue in this system. The
only chromatic values left are gain, caution and loss — and each of them means money.

**Key Characteristics:**
- White ground, warm bone panels, warm hairlines — never neutral grey
- Zero shadows; separation is rule plus tone
- No interaction colour; the primary action is black
- Colour appears only where a number means money
- Mono micro-label above a large, *light-weight* figure
- Nine type sizes, no half-steps
- Every measurement carries its sample size

## Colors

A warm neutral field — paper and bone with warm-grey rules — interrupted only by three chromatic
values that report outcomes.

### Primary
- **Ink** (`#050505`): every piece of body text, every heading, every figure, and the fill of the
  primary action. This is the interaction colour *and* the text colour; the system does not
  distinguish them. Contrast on paper is 20.38:1.

### Neutral
- **Paper** (`#ffffff`): the page ground and the fill of a raised surface. In a light system
  "raised" means *whiter*, not lighter-grey.
- **Paper Raised** (`#fbfaf8`): the drawer and secondary panels — a half-step off paper, warm.
- **Bone** (`#f8f5f2`): the standard card fill. Warm enough to read as a distinct plane against
  paper without a border doing all the work.
- **Bone Deep** (`#f1ece8`): nested panels and slips inside a bone card.
- **Chip** (`#f3f3f3`): the cool micro-fill under a segmented control or nav pill — the one
  cool neutral, borrowed directly from the reference's nav.
- **Rule** (`#e7e3df`): the default hairline. Warm-grey, never a white or black alpha.
- **Rule Strong** (`#d9d4cf`): borders that must survive on a bone card.
- **Ink Muted** (`#585450`): secondary and supporting text. **4.63:1** on the darkest tinted
  ground it appears on (the amber thin-cell fill), 6.91:1 on bone.

### Tertiary — the money colours
- **Gain** (`#0c6a3b`): a positive realised result. **5.31:1** on its own tint.
- **Caution** (`#6e4a00`): a warning that needs a human. **4.90:1** on the thin-cell ground.
- **Loss** (`#b3242c`): a negative result, and the two emergency controls. **5.13:1** on its own tint.

Each money colour is quoted against **its own 10% tint over bone** — the ground it actually sits on
inside a status chip — not against bone itself. That distinction is not pedantry: the first version
of this system quoted gain at 4.60:1 measured on bone, shipped it, and the chip measured **4.36:1**
in the browser, below AA at the 10px the chips are set in. Gain was darkened from `#0f7a45` to
`#0c6a3b` to fix it.

### Named Rules

**The Money Rule.** Colour means money. If a value is not a realised outcome, a risk state, or a
control that can lose money, it is ink or ink-muted. There is no decorative colour and no
interaction colour in this system — adding one breaks the only signal the operator scans for.

**The Warm Rule.** Every neutral is warm. Hairlines are `#e7e3df`, not `rgba(0,0,0,.08)`; panels
are `#f8f5f2`, not `#f5f5f5`. A single cool grey (`#f3f3f3`) is permitted, and only as a chip fill.
Introducing a cool border makes the whole page read as a different, colder product.

**The Measured-Not-Borrowed Rule.** The reference's own muted grey (`#8f8b86`) was rejected: it
measures 2.89:1 on the reference's own bone panel and the reference uses it at 10px. This system
uses `#585450` (6.91:1 on bone) and keeps the warm cast. Take a reference's grammar; verify its numbers.

**The Own-Ground Rule.** Measure a colour against the surface it will actually sit on, composited,
not against the page. A status chip fills itself with a 10% tint of its own ink, so the ink is
darker relative to *that*, never to bone. Every contrast figure in this document is quoted against
the worst real ground, and any new tinted component must be re-measured the same way before it
ships. Auditing a swatch against the page is how a failing chip passes review.

## Typography

**Display / Body Font:** Geist (with `system-ui`, `-apple-system`, `Segoe UI`)
**Label / Figure Font:** Geist Mono (with `ui-monospace`, `SFMono-Regular`)

**Character:** One family and its monospace sibling, nothing else. Geist is the reference's own
face, inherited rather than chosen. The pairing does all its work through weight and tracking:
headings are *medium* (500), never bold, and figures are *regular* (400) at large sizes — a big
number here is large and light, not heavy. Mono is reserved for two jobs only: micro-labels and
anything numeric.

### Hierarchy
- **Display** (500, 28px, 1.18, −0.02em): the largest heading on a view; one per view.
- **Headline** (500, 20px, 1.18, −0.02em): section and drawer titles.
- **Title** (500, 17px, 1.25, −0.02em): card titles.
- **Body** (400, 14px, 1.55, −0.011em): running prose and table cells.
- **Label** (mono, 700, 10px, 0.16em, UPPERCASE): the micro-label above a figure, and status
  badges. This is the signature idiom of the system.
- **Figure** (mono, 400, 28px, 1, −0.04em, tabular): the headline number in a stat card. Large
  and light. In the dense matrix grid the figure steps to 500 at 24px — the one weight concession
  the system makes, because a data grid is not a marketing statistic.

### Named Rules

**The Ramp Rule.** Nine sizes exist and no others: **10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28** px.
No half-steps, no `15px` because something looked slightly small. If a new element needs a size
that isn't on the ramp, it needs a different element.

**The Tabular Rule.** Every figure is Geist Mono with `tabular-nums`, so a column of numbers reads
as a column and a value that changes does not shift its neighbours.

**The Label-Above Rule.** A figure never appears without a mono micro-label above it naming what
it measures. A bare number on this desk is an unlabelled instrument.

## Layout

A single centred column against a fixed 208px index rail on the left and a fixed top bar of live
readings. The rail is always labelled; nothing overlays the sheet on hover.

Spacing runs on a strict 4px base: **4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48**. Cards pad at 24px;
the gap between major blocks is 40px.

Density is the point. This is a console read daily, not a page browsed once — the reference's 20px
card padding and 21px radii were compressed to 24px and 12px so a four-column matrix still fits a
laptop screen without scrolling.

Below 560px the rail wraps to two rows of chips rather than scrolling horizontally, and the drawer
takes the full width and locks body scroll. Horizontal overflow is clipped at the root
(`overflow-x: clip`, not `hidden` — `hidden` would create a scroll container and kill the rail's
`position: sticky`).

## Elevation & Depth

**There are no shadows in this system.** Not on cards, not on the drawer, not on modals. This was
measured off the reference, where every card computes to `box-shadow: none`, and it is now an
invariant: the elevation token `--elev` is literally `none`.

Depth is built two ways. **Tone**: paper → paper-raised → bone → bone-deep is a four-step warm
ramp, and a surface reads as nearer by being warmer and lower in value, not by casting a shadow.
**Rule**: a 1px warm hairline closes the edge that a shadow would otherwise imply.

The one apparent exception is not one. `box-shadow: 0 3px 0 -2px var(--line)` under the top bar has
zero blur and negative spread — it draws a hairline 3px below the border, doubling the rule. It is
line work, not elevation.

### Named Rules

**The Flat Rule.** No `box-shadow` with a blur radius, anywhere, for any reason. If a surface needs
to feel nearer, move it up the tonal ramp or give it a stronger rule. A shadow in this system reads
as a bug, and the detector will flag it as one.

**The Inset-Is-A-Border Rule.** `box-shadow: inset 0 0 0 1px …` is permitted and common — it is how
status pills draw a coloured hairline without changing their box size. Inset with zero blur is a
border. Anything else is elevation.

## Shapes

Corners are gentle and consistent: cards at 12px, controls and badges at 10px, and interactive
pills fully round (`999px`). Bars and meters stay nearly square at 2px so a thin measurement reads
as a measurement rather than a lozenge.

Borders are always exactly 1px and always a warm neutral, except where a status colour draws its
own inset hairline. Nothing is dashed. Nothing is doubled except the top bar's deliberate rule pair.

Full-pill geometry is reserved for things a person clicks. A pill that cannot be clicked is
misleading; use the 10px control radius instead.

## Components

### Buttons
- **Shape:** gently curved (10px), 44px minimum height for every interactive control.
- **Secondary (default):** transparent fill, 1px `rule-strong` border, ink text at 13px/600,
  padding `9px 15px`.
- **Primary:** ink fill (`#050505`), paper-raised text — the reference's black pill.
- **Hover / Focus:** hover lifts the fill to `chip`; `:focus-visible` draws a 2px ink outline at
  2px offset. Transition is 150ms `ease`.
- **Danger:** transparent fill with a `loss` border and `loss` mono text — the HALT and KRİZ
  controls. These are the only buttons that carry colour, and they measure 6.55:1.
- **Disabled:** 45% opacity, hover suppressed.

### Chips / Status Badges
- **Style:** mono 10px/700, uppercase, `0.09em`, 10px radius, `4px 9px` padding.
- **State:** a status tint fill at 10% alpha plus a matching inset hairline at 35% — green for
  passed, amber for needs-a-human, red for rejected, and a plain `rule-strong` inset for neutral.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** `bone` (`#f8f5f2`); nested slips step to `bone-deep`.
- **Shadow Strategy:** none — see Elevation & Depth.
- **Border:** 1px `rule-strong`.
- **Internal Padding:** 24px.

### Inputs / Fields
- **Style:** 1px `rule-strong` border, paper fill, 10px radius, placeholder in `ink-muted`.
- **Focus:** border shifts to ink and the fill lifts to `bone`. No glow, no ring beyond the
  standard focus outline.

### Navigation
- 208px fixed index rail: each entry is a 20px inline SVG glyph at 1.5px stroke in
  `currentColor`, the view name at 14px/500, an optional count badge, and — clamped to two lines
  beneath — that view's one-line live reading, so the rail answers "what's in there?" before it
  is opened. Exactly one item carries `aria-current` at a time.
- **The rail was 56px with a hover label that rode over the sheet, and that failed twice in
  practice.** The overlay covered the triage band, got clipped by paint order, and read as a
  rendering bug rather than an affordance. A permanently visible label costs 152px of content
  width and buys an index that never overlaps anything. If a future change tempts you back
  toward an overlay, this is the record of why it was abandoned.
- Top bar is `rgba(255,255,255,.82)` with an 8px backdrop blur, closed by a hairline pair. It sits
  at the same value as the page so it reads as the sheet's ruled top edge, not a separate chrome.

### The Setup × Regime Matrix (signature)
The interface's centrepiece: a grid of setup against market regime where each cell is a real
`<button>` announcing setup · regime · mean · n · hit-rate. The cell figure is mono 24px/500 at
−0.045em. A 2px confidence bar under each cell encodes sample size logarithmically, so a
three-trade mean can never look as firm as a fifty-five-trade one.

Clicking a cell opens the drawer. This click→drawer pattern is the system's primary interaction and
is applied uniformly to matrix cells, closed trades, plans, hypotheses and events.

### The Drawer (signature)
A 430px right-hand panel on `paper-raised` with a single left hairline, sliding in over 280ms on
`cubic-bezier(.16,1,.3,1)`. It is `role="dialog"` with `aria-modal`, traps focus, and returns focus
to the originating row on Escape. It starts *below* the top bar and sits *under* the nav in z-order,
so it can never occlude the emergency stop.

## Do's and Don'ts

### Do:
- **Do** keep colour for money. Gain `#0c6a3b`, caution `#6e4a00`, loss `#b3242c` — and nothing else
  chromatic anywhere on the page.
- **Do** put a mono 10px uppercase label at `0.16em` above every figure.
- **Do** pick sizes from the ramp: 10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28 px.
- **Do** set figures in Geist Mono with `tabular-nums`, weight 400 at large sizes.
- **Do** build depth from the tonal ramp and 1px warm hairlines.
- **Do** show sample size next to any average — the confidence bar or an explicit `n`.
- **Do** give every interactive control a 44px minimum touch target.
- **Do** verify a borrowed value's contrast before adopting it.

### Don't:
- **Don't** add a `box-shadow` with a blur radius. `--elev` is `none` and stays `none`.
- **Don't** introduce an accent hue. There is no interaction colour; the primary action is black.
- **Don't** use a cool neutral for a border or panel. Warm only; `#f3f3f3` is permitted as a chip
  fill and nowhere else.
- **Don't** set a heading bolder than 500 or a large figure bolder than 400.
- **Don't** invent a type size that isn't on the ramp.
- **Don't** use full-pill geometry on something that isn't clickable.
- **Don't** inherit the reference's spacing. Its 20px padding and 21px radii belong to a marketing
  page; this is a console.
- **Don't** render a number the state file cannot produce. An unavailable value shows its absence,
  never a placeholder.
