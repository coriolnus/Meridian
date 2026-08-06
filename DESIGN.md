---
name: Meridian
description: A hairline-ruled operator console in two grounds — a daylight desk and a night desk — sharing one token vocabulary, where colour is reserved for money.
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

**Creative North Star: "The Desk, Lit Two Ways"**

Meridian is a solo operator's console. It answers one question — *is anything waiting for me?* —
and it answers it with nothing hidden and nothing performing. The surface is a clear desk: warm
panels ruled off by hairlines, no shadow anywhere, depth built from tone and rule alone so a card
sits *beside* the page rather than floating above it. Nothing on this desk is decorative. If an
element carries no measurement, it carries no colour.

**The desk has two lightings, not two designs.** The daylight ground is the system converted in
full from the Omega reference the operator chose (`nextjsshop.com/templates/omega`): paper-white,
warm bone panels, black primary action. The night ground is the same desk under a lamp: a warm
dark-grey field with off-white ink, built for the 24/7 low-light shift the operator actually keeps.
There is exactly **one set of token names**, two sets of values, and a switch at the foot of the
rail. Every rule below holds in both. Every geometry, every type size, every spacing step, every
radius, and the flat-elevation invariant are **identical** across the two — only colour values move.

**The rule that makes the second lighting possible is that no rule may contain a colour.** Every
value that carries colour lives in a token, including the ones that are easy to forget: hairlines
inside chips, the scrim behind a modal, matrix cell fills, and the translucent top bar. Twenty such
literals were sitting inside rule bodies when the night ground was built, and each one would have
survived the switch unchanged. The worst was the top bar: left as `rgba(255,255,255,.82)` it would
stay white over a dark page and take the HALT and KRİZ controls with it — the exact inverse of a
failure this system has already had once, measured at **1.27:1**.

The strictest inheritance from Omega is the absence of an interaction colour. Omega's primary
action is a black pill, not a blue one, and adopting that sharpened a rule Meridian already had
into something absolute: **colour belongs to measurement alone.** There is no accent hue in this
system, in either theme. The only chromatic values are gain, caution and loss — and each of them
means money.

**Key Characteristics:**
- Two grounds, one vocabulary: identical token names, identical geometry, only colour values differ
- Every neutral is warm in both themes — never neutral grey, never pure black, never pure white
- Zero shadows in both; separation is rule plus tone
- No interaction colour; the primary action is the ink of its own theme
- Colour appears only where a number means money
- Mono micro-label above a large, *light-weight* figure
- Nine type sizes, no half-steps
- Every measurement carries its sample size
- Every contrast figure in this document was computed, not estimated (WCAG 2.x relative
  luminance, with alpha compositing performed in 8-bit sRGB the way a browser performs it)

## Colors

A warm neutral field interrupted only by three chromatic values that report outcomes. The field
inverts between themes; the discipline does not.

The YAML frontmatter above carries the **daylight** values, because the schema admits one value per
token name. The night values are the second column of every table below and are normative — they
are not a derived or auto-generated variant.

### Token table — both grounds

| Token (CSS var) | Role | Daylight | Night |
|---|---|---|---|
| `--bg` (paper) | page ground | `#ffffff` | `#1c1a18` |
| `--bg2` (paper-raised) | drawer, secondary panel, grid gutters | `#fbfaf8` | `#232120` |
| `--card` (bone) | standard card fill | `#f8f5f2` | `#262320` |
| `--card-2` (bone-deep) | nested panel, slip inside a card | `#f1ece8` | `#2f2b27` |
| `--raise` | meter / donut track | `#ffffff` | `#38342f` |
| `--slip` | inline record slip | `#f1ece8` | `#2f2b27` |
| `--slip-ink` | text on a slip | `#050505` | `#d4d0cb` |
| `--line` (rule) | default hairline | `#e7e3df` | `#38342f` |
| `--line-2` (rule-strong) | hairline that must survive on a card | `#d9d4cf` | `#4a453f` |
| `--tx` (ink) | body text, headings, figures | `#050505` | `#d4d0cb` |
| `--tx2` (ink-muted) | secondary and supporting text | `#585450` | `#b0a9a0` |
| `--accent` | primary action fill; also the focus outline | `#050505` | `#d4d0cb` |
| `--accent-2` | accent as text | `#050505` | `#e8e4df` |
| `--accent-tint` | segmented control / nav pill micro-fill | `#f3f3f3` | `#302c28` |
| `--green` (gain) | a positive realised result | `#0c6a3b` | `#4cc38a` |
| `--amber` (caution) | a state that needs a human | `#6e4a00` | `#e0a82e` |
| `--red` (loss) | a negative result; the emergency controls | `#b3242c` | `#f58b8f` |
| `--green-t` / `--amber-t` / `--red-t` | 10% status tint | `rgba(12,106,59,.10)` · `rgba(110,74,0,.10)` · `rgba(179,36,44,.10)` | `rgba(76,195,138,.10)` · `rgba(224,168,46,.10)` · `rgba(245,139,143,.10)` |
| `--elev` | elevation | `none` | `none` |

**Pure black and pure white are forbidden on the night ground.** `#000` under off-white text
produces halation, and roughly 40–47% of adults have some astigmatism (handbook, Area 5). The
night field is `#1c1a18` and the night ink is `#d4d0cb` — inside the `#1E1E1E` ground / `#CCC`–`#D4D4D4`
text envelope the handbook specifies, with the warm cast carried over so the two themes are
recognisably the same product.

### The role layer — five roles, five token families (D1, 2026-08-07)

The table above is the **value layer**: each token is named after a *hue*. That naming was the
defect. An audit on 2026-08-06 measured what a hue-named token costs once a codebase has run for
a while: `--green` was carrying **at least four** distinct meanings, `--amber` **five**, `--red`
**five**, and the mode chroma the Design rules reserve had **no channel at all**. A rule that
reads `var(--red)` does not say which role it is playing, and a rule that does not say makes
borrowing a second meaning free.

So a second layer sits on top, named after *jobs*. **Component rules read only this layer**; the
value layer exists solely to feed it. Both grounds define the identical set of names — a token
present on one ground and absent on the other is a bug, not a shortcut, because the missing one
is silently inherited and the rule then runs with the wrong ground's colour. That equality is
nailed by test, not by eye (`tests/test_renk_rolleri_v197.py`).

| Role | Token family | What it may carry | What it may never carry |
|---|---|---|---|
| 1 · Structure | *(none — `--bg`/`--card`/`--tx`/`--line`)* | ground, panel, rule, text | any hue at all |
| 2 · Severity | `--sev-1` `--sev-2` `--sev-3` (+ `-t`, `-h`, `-h2`, `-damga`) | P1 act now · P2 needs a human · P3 nominal | anything that is not an alarm or risk level |
| 3 · Direction | `--yon-arti` `--yon-eksi` (+ `-t`, `-h`, `-zemin`) | the sign of a P&L reading | a price level, a magnitude, a parameter |
| 4 · Mode | `--mod-kagit` `--mod-canli` `--mod-kesif` (+ `-t`, `-h`) | paper / live / exploration | any other state |
| 5 · Data scales | `--kap-*`, `--dv-*`, `--olcek-guven` (+ `-t`, `-h`) | coverage ramp, drift divergence, sample confidence | a verdict |

Severity keeps the three measured hues from the value layer, so nothing in that channel moved.
The other three families are new and were measured from scratch.

**Direction is deliberately quieter than severity, and the constraint is numeric.** Direction is
the *third* signal — the sign and the arrow arrive first — so its chroma must sit visibly below
severity's, otherwise a profitable day competes for attention with a risk violation. The values
were produced by holding each hue's OKLCh lightness (so contrast did not move) and cutting its
chroma:

| Ground | severity min chroma | direction max chroma | ratio |
|---|---|---|---|
| Daylight | 0.0917 (`--sev-2`) | 0.0588 | 0.64 |
| Night | 0.1289 (`--sev-1`) | 0.0586 | 0.45 |

**Mode owns a hue band, not a badge.** 310° (violet-magenta) is reserved permanently: no other
token may enter 285–335°, and `--mod-*` may not resolve to a severity or direction token. Both
halves are tested. The carrier is structural — a 3px band on the top edge of the page, driven by
`body[data-mod]` — because the costliest accident in this domain is an operator who believes they
are in the other mode, and a corner badge only works while it is in view. **Paper is achromatic**:
the expected, safe state spends no chroma, which is how the reserved channel coexists with the
"colour only on anomaly" law. Chroma belongs to the states that are expensive to misread — live,
and exploration. There is a third band state, hatched: mode *unmeasured* does not fall back to
"paper", because a stale "paper" on a live account is exactly the lie the fabrication ban exists
to prevent.

**Measured — role tokens, both grounds.** Each value against the bare surfaces and against its own
10% tint over each surface (the ground a chip actually occupies); the figure quoted is the worst:

| Token | Daylight | worst real ground | Night | worst real ground |
|---|---|---|---|---|
| `--yon-arti` | `#40654c` | **4.71** | `#8ab59c` | **5.10** |
| `--yon-eksi` | `#784e4b` | **4.99** | `#d1a0a0` | **5.13** |
| `--mod-canli` | `#723a96` | **5.35** | `#c598e7` | **5.03** |
| `--mod-kesif` | `#635071` | **5.11** | `#b9a4ca` | **5.12** |
| `--olcek-guven` | `#585450` | **5.32** | `#b0a9a0` | **5.02** |

The matrix cell grounds moved with them, and moved the right way: lowering direction chroma
shifts the cell ground less, so the figure sitting on it gained contrast rather than losing it —
`--tx` on the positive cell measures 17.36 / 15.98 (daylight, over `bg` / `card`) and 9.89 / 8.82
(night), with `--tx2` at 6.39 / 5.88 and 6.52 / 5.82.

**Two non-text values were raised because 1.4.11 applies to them and not to a card edge.** The
declared hairline deviation below covers borders that *decorate*; these two *identify*:

| Element | Old | New | Daylight | Night |
|---|---|---|---|---|
| Thin-sample cell ring (`--olcek-guven-h`) | `--amber-h` @ .35 → 1.72–2.07 | ink @ **.45** | **3.12** | **3.03** |
| Paper mode band (`--mod-kagit`) | — | opacity **.65** | **3.11** | **3.91** |

The live mode band measures 7.25 / 7.45 and needs no floor. The mode chip's own inset hairline
measures 1.70 / 1.92 and **stays inside the declared hairline deviation**: it is identified by its
fill (5.72 / 5.61 for the text on it) and by the band, not by its border — the same reasoning the
status chips already run on.

### Measured contrast — daylight ground

Text tokens, against the flat surfaces they sit on, and against the **worst real composited
ground** they can reach anywhere in the interface:

| Token | Value | on `--bg` | on `--bg2` | on `--card` | on `--card-2` | on `--accent-tint` | worst real ground |
|---|---|---|---|---|---|---|---|
| `--tx` | `#050505` | 20.38 | 19.54 | 18.76 | 17.38 | 18.37 | **14.86** on `red-t`/`card-2` (`#ebd8d5`) |
| `--tx2` | `#585450` | 7.50 | 7.19 | 6.91 | 6.40 | 6.76 | **5.47** on `red-t`/`card-2` |
| `--accent-2` | `#050505` | 20.38 | 19.54 | 18.76 | 17.38 | 18.37 | **14.86** on `red-t`/`card-2` |

Money colours, each quoted against **its own 10% tint** — the ground it actually occupies inside a
status chip — and against bare surfaces:

| Token | Value | on own tint / `bg` | on own tint / `card` | on own tint / `card-2` | bare `bg` | bare `card-2` | worst real ground |
|---|---|---|---|---|---|---|---|
| `--green` | `#0c6a3b` | 5.75 | 5.31 | 4.94 | 6.69 | 5.70 | **4.88** |
| `--amber` | `#6e4a00` | 6.80 | 6.29 | 5.85 | 7.95 | 6.78 | **5.80** |
| `--red` | `#b3242c` | 5.55 | 5.13 | 4.78 | 6.55 | 5.59 | **4.78** |

Everything above clears WCAG 2.2 AA (4.5:1) at every real ground, including the 10px chips.

### Measured contrast — night ground

| Token | Value | on `--bg` | on `--bg2` | on `--card` | on `--card-2` | on `--accent-tint` | worst real ground |
|---|---|---|---|---|---|---|---|
| `--tx` | `#d4d0cb` | 11.31 | 10.45 | 10.18 | 9.15 | 9.02 | **7.51** on `amber-t`/`card-2` (`#413828`) |
| `--tx2` | `#b0a9a0` | 7.46 | 6.89 | 6.72 | 6.04 | 5.95 | **4.96** on `amber-t`/`card-2` |
| `--accent-2` | `#e8e4df` | 13.71 | 12.67 | 12.35 | 11.09 | 10.94 | **9.11** on `amber-t`/`card-2` |

| Token | Value | on own tint / `bg` | on own tint / `card` | on own tint / `card-2` | bare `bg` | bare `card-2` | worst real ground |
|---|---|---|---|---|---|---|---|
| `--green` | `#4cc38a` | 6.61 | 5.90 | 5.31 | 7.83 | 6.34 | **5.21** |
| `--amber` | `#e0a82e` | 6.79 | 6.06 | 5.39 | 8.11 | 6.56 | **5.39** |
| `--red` | `#f58b8f` | 6.29 | 5.62 | 5.01 | 7.41 | 6.00 | **4.93** |

Everything clears AA on the night ground too. Getting there was not free: the first night red
tried was `#f2555a`, the value the pre-Omega dark world used. It measures **4.12** on its own tint
over `--card` and **3.72** over `--card-2` — below AA at the 10px the chips are set in. It was
lightened to `#f58b8f`, which measures 5.62 and 5.01 on the same two grounds.

### Composited surfaces measured individually

| Surface | Daylight | Night |
|---|---|---|
| Top bar (translucent, 8px backdrop blur) composites to | `#ffffff` | `#1c1a18` |
| `--red` on the top bar — the HALT / KRİZ controls | 6.55 | 7.41 |
| `--tx` on the top bar | 20.38 | 11.31 |
| HALT hover (red fill, `--bg2` text) | 6.28 | 6.85 |
| Primary action (accent fill, `--bg2` text) | 19.54 | 10.45 |
| Triage band `attn` — `--tx` on `amber-t`/`bg` | 17.43 | 9.48 |
| Triage band `act` — `--tx` on `red-t`/`bg` | 17.27 | 9.60 |
| Matrix cell `pos` ground (`green` @8% over `bg`) | `#ecf3ef` | `#202821` |
| `--tx2` on that cell ground | 6.66 | 6.51 |
| `--green` on that cell ground | 5.93 | — |
| Under-sown stake — `--amber` on `amber-t` over the `pos` cell | 6.05 | 5.86 |
| Section eyebrow — `--accent-2` on `--accent-tint` | 18.37 | 10.94 |

### Non-text contrast, measured and declared

WCAG 2.2 1.4.11 asks 3:1 for information required to identify a component. **The hairlines do not
reach it, in either theme, and this is a declared deviation rather than an oversight:**

| Hairline | on `bg` | on `bg2` | on `card` | on `card-2` |
|---|---|---|---|---|
| `--line` daylight `#e7e3df` | 1.28 | 1.22 | 1.18 | 1.09 |
| `--line-2` daylight `#d9d4cf` | 1.47 | 1.41 | 1.36 | 1.25 |
| `--line` night `#38342f` | 1.40 | 1.30 | 1.27 | 1.14 |
| `--line-2` night `#4a453f` | 1.83 | 1.69 | 1.65 | 1.48 |

Status-chip inset hairlines at 35% alpha against their own fill measure 1.50 / 1.53 / 1.54
(daylight, gain / caution / loss) and 1.69 / 1.74 / 1.66 (night). The meter track `--raise`
against `--card` measures 1.09 (daylight) and 1.27 (night).

What carries the burden instead: chips and cards are identified by their **fill** and their text,
not by their border; every interactive control draws a 2px `--accent` `:focus-visible` outline at
2px offset, which measures 18.76 (daylight) and 10.18 (night) against a card.

**The one real exposure — the text input — is now closed, and it did not require moving
`--line-2`.** The previous version of this section identified the field boundary as the single
place where a hairline is the *only* thing identifying a component, and deferred the fix on the
grounds that raising `--line-2` would change every surface. That framing was the mistake: 1.4.11
asks for 3:1 on *information required to identify a component*, which is a narrower set than
*every line in the interface*. So form controls got their own token instead.

| Token | Daylight | Night | worst real ground |
|---|---|---|---|
| `--field` (form control border) | `#8a8580` | `#7e776e` | **3.12** / **3.18** on `--card-2` |

Applied to every text input, password field, number field and `select`, on all three surfaces,
including the ones `app.js` styles inline — one of which was using `--line` (1.28), weaker still
than the value this section was worried about. Decorative and structural hairlines stay at
1.09–1.83 by choice: a card edge is not a component boundary, and making every rule in the system
shout would destroy the quiet the ramp exists to produce.

The tonal ramp that replaces shadow is deliberately shallow — daylight `bg→bg2` 1.043, `bg2→card`
1.041, `card→card-2` 1.080, `bg→card-2` 1.173; night 1.082 / 1.026 / 1.113 / 1.236. A tonal step
is not a contrast device; it is a *plane* device, and the hairline closes the edge.

**The overlay scrim does not survive the theme change, and the fix was not a bigger number.**
Measured from the shipped tokens: on the daylight ground a 42% warm-black scrim dims the page to
`#969696`, which separates it from the modal card by **2.72**. On the night ground the page is
already dark, so the same scrim reaches only `#100f0d` and separates by **1.23** — and pure black
would cap at **1.34**. The mechanism simply has no room to work. The night alpha was raised to 66%
to take all of the available separation, but the honest statement is that at night the modal is
told apart by its **backdrop blur and its own hairline**, not by luminance. Never read the daylight
scrim figure as evidence that the night overlay is fine.

### Named Rules

**The Money Rule.** Colour means money. If a value is not a realised outcome, a risk state, or a
control that can lose money, it is `--tx` or `--tx2`. There is no decorative colour and no
interaction colour in this system — adding one breaks the only signal the operator scans for.

**The Second-Channel Rule.** Because colour carries meaning here, colour may never carry it
**alone**. Every gain/loss figure states its direction in a mark as well as a hue: losses already
had a minus from the formatter, so gains now take an explicit `+`. The absence of a sign is not a
sign — a reader with a colour vision deficiency, or anyone looking at a greyscale screenshot, was
being asked to infer *gain* from a missing character. The convention was already in the codebase
for `R` and IC values (`+0,214R`); percentage and currency readouts had simply been left outside
it. The sign goes **inside** the unit — `%+12,34`, not `+%12,34`. No arrow glyph was introduced:
the system already had a sign vocabulary, and a second one would need its own justification.

**The Warm Rule.** Every neutral is warm in both themes. Daylight hairlines are `#e7e3df`, not
`rgba(0,0,0,.08)`; night hairlines are `#38342f`, not `#333`. A single cool grey (`#f3f3f3`) is
permitted on the daylight ground, and only as a chip fill. A cool neutral makes the page read as a
different, colder product — and a cool *dark* one makes it read as a different product entirely.

**The Own-Ground Rule.** Measure a colour against the surface it will actually sit on, composited,
not against the page. A status chip fills itself with a 10% tint of its own ink, so the ink is
darker relative to *that*, never to the card. Every contrast figure in this document is quoted
against the worst real ground, and any new tinted component must be re-measured the same way
before it ships. Auditing a swatch against the page is how a failing chip passes review.

**The Tint-Direction Rule.** A status tint moves the ground *toward its own ink* — so on the
daylight ground a tint darkens the surface and **helps** the ink, and on the night ground the same
10% tint lightens the surface and **hurts** it. This is why the night money colours are lighter
than a naive inversion would suggest, and why `#f2555a` failed. Never derive a night value by
inverting a daylight one; derive it by measuring against the composited night chip.

**The Measured-Not-Borrowed Rule.** The Omega reference's own muted grey (`#8f8b86`) was rejected:
it measures **3.12:1** on the reference's own bone panel and the reference uses it at 10px. Take a
reference's grammar; verify its numbers. This applies to this document's own history too — see
*Measurement provenance* below.

**The Polarity-Honesty Rule.** The night ground exists for **24/7 low-light ergonomics**, not for
readability. The evidence runs the other way: Piepenbrock et al. (*Ergonomics*, 2013/2014) found
**positive** polarity — dark text on a light ground — superior in reading speed and accuracy, and
the most-cited halation source (Harrison, UBC) is not peer-reviewed. Roughly 40–47% of adults have
some astigmatism and see halation around light glyphs on a dark field. So: the daylight ground is
the default and the reading-performance choice; the night ground is the ambient-comfort choice for
a shift worked in a dark room, and the switch is the operator's to throw. If halation is ever
reported, the response is to lower the text luminance toward `#cccccc` and raise the weight — not
to argue that dark is easier to read.

**The WCAG-Is-The-Standard Rule.** WCAG 2.2 AA is the compliance bar for both themes. APCA may be
used as a design-time assistant, especially when tuning the night ground, but **never as a
substitute**: APCA is not an approved WCAG 3 method, it was removed from the Working Draft in
July 2023, and as of April 2026 its status is undetermined. A colour that passes APCA and fails
WCAG 2.2 does not ship.

### Measurement provenance

Every figure above was computed from the token values by the WCAG 2.x relative-luminance formula,
with alpha composited in 8-bit sRGB. Re-auditing the previous version of this document against the
same method found three figures that **could not be reproduced** and are corrected here:

- "ink-muted 4.63:1 on the amber thin-cell fill" — the thin cell has no amber fill, only an amber
  inset hairline. `--tx2` on `amber-t`/`card` measures **5.93**; its true worst real ground is
  **5.47** on `red-t`/`card-2`.
- "caution 4.90:1 on the thin-cell ground" — not reproducible; `--amber` on its own tint over
  `card` measures **6.29**, over the matrix `pos` cell **6.05**.
- "the reference's grey measures 2.89:1 on bone" — measures **3.12**. Still far below AA at 10px,
  so the rejection stands; the number was wrong.

Two figures inside `index.html`'s own direction contract are also wrong and should be corrected
when that file is next touched: `#585450` is annotated "(4.51:1)" but measures **7.50** on paper,
and the top bar comment cites 5.64 for loss-on-white where the measurement is **6.55**. The same
comment's historical claim — that loss measured 1.27:1 on the old dark bar `rgba(8,9,10,.72)` over
white — **is confirmed at 1.27**.

## Design rules

*Adopted 2026-08-06 from the trading-platform brief, with three deviations named below. These
outrank general web-design instinct; they do not outrank the binding Omega two-ground world.*

**Redesign scope (operator mandate, 2026-08-06): no UI element is exempt, and neither is its
place or its form.** Open for redesign: every visual and interaction element (status strip,
command palette, scoreboard matrix, cell language, cards, navigation rail, type, tokens, table
layouts) — *and* **which surface shows a given piece of information, and in what representation
it is shown** (table vs. card vs. matrix vs. sparkline vs. chip vs. nothing at all). Page and
section structure is open with it. "It already ships" is not a reason to preserve a form, a
placement, or an inclusion.

**Direction (operator, 2026-08-06):** the interface should be **as user-friendly as it can be**,
designed against what platforms in this category — autonomous / algorithmic trading agents under
human supervision — actually offer. The starting assumption is that the components and data the design needs already exist, so the
first pass is recombination — what is asked, where it is answered, in what form. **But new
modules are permitted (operator, 2026-08-06): a valuable job is never dropped merely because
today's data does not cover it.** It is carried as a candidate with its cost (derivable from
existing state / needs an external source / needs a new data path) and Rol-1 decides which get
built.

Two limits survive that permission. A new module may never open a second order path, resurrect
a dopamine pattern, imply real money while the ladder says paper, or fabricate what was not
measured — those are product laws, not budget questions. And a module that makes an *edge
claim* (asserting a signal earns money) still requires a pre-registered card; pure view and
derivation modules do not.

Calibration, stated because it is a real tension: user-friendly here does not mean
consumer-friendly. The user is one expert on long shifts, so friendliness is measured as *fewer
steps to the answer, no hunting, states that never lie, an obvious next action, and mistakes
that are recoverable* — not as reduced density, tutorials, or decorative reassurance. Density
that earns its keep stays; density that hides the answer does not.

The consequence for method: the system is inventoried by **job**, not by widget. For each item
the record is *what question the operator is asking · which data answers it · where it lives
today · in what form · what that form measurably buys*. The redesign then re-maps jobs →
surfaces → representations from scratch. A shipped element carries forward only its measured
value, never its shape, its address, or its right to exist.

What does **not** change is the product underneath, because a UI/UX redesign is not a category
change: the single order path, the honesty laws (unmeasured ≠ 0, no undeclared denominators,
no fabrication), the two grounds with daylight default, the no-dopamine rule, CSP-self, and the
Turkish interface. Those bound the *content*; the *form* is fully open.

- **Surface class: supervision console for an autonomous paper-trading agent.** Operator
  decision 2026-08-06: Meridian does **not** get manual order entry. Orders exist only on one
  path — agent plans → gates → operator approval of REVIEW verdicts → the single mirror-submit
  gate. A second order path is forbidden by construction (E1 two-engine law: both engines read
  `broker.entry_law()`). Density, precision and state honesty outrank visual appeal.
- **Gray-first, with five colour roles that never bleed into each other:** (1) structure —
  achromatic; (2) risk/alarm severity — high chroma, three hues, used for nothing else;
  (3) direction — P&L sign, low chroma, CVD-safe, and always the *third* signal after sign and
  arrow; (4) **mode chrome** — reserved permanently for paper-vs-live and used for nothing else;
  (5) data scales — single-hue sequential and CVD-safe diverging, never rainbow. There is no
  brand accent colour in the product UI.
- **Mode must be legible from any pixel.** Today the system is paper (L0). When the autonomy
  ladder moves to L1, a structural treatment — not a corner badge — carries it, because the
  costliest accident class in this domain is an operator who believes they are in the other mode.
- **Forbidden:** gradients, glassmorphism, decorative shadows, gradient text, hero imagery,
  illustration, nested rounded cards, celebratory motion, sound, gamification of any kind.
- **Motion:** ≤300ms, anomaly-signalling only, always inside a `prefers-reduced-motion` guard.
- Backgrounds are never `#000`; text is never `#FFF`.
- **Numerics:** tabular figures, right-aligned, fixed decimals per column, explicit currency.
- **Charts:** bars and bullet graphs. Radial gauges, donuts and pie charts are forbidden.
- **Null renders as an explicit gap with a reason** — never `0`, never interpolated, never blank.

**Three deviations from the source brief, and why:**

1. **Radius stays on the Omega scale (10px control radius, the black-pill idiom), not 0/2px.**
   Radius is geometry, and geometry is identical across the two grounds by binding decision;
   flattening it would reopen the visual world rather than tighten the console. The brief's
   0/2px belongs to an ISA-101 canvas Meridian did not adopt.
2. **`slashed-zero` is not declared.** Measured: the current mono bakes the slash into the
   default glyph and exposes no `zero` feature, so the declaration is inert — writing it would
   be work that reads as done but changes nothing. Re-verify if the typeface changes.
3. **Two grounds stay, daylight default.** The brief assumes a dark-only canvas; the binding
   decision (2026-07-31, operator) is two grounds with daylight as default and night as a
   low-light shift choice. The brief's colour-*role* architecture is ground-agnostic and is
   adopted in full; its specific dark canvas values are not.

## Typography

**Display / Body Font:** Geist (with `system-ui`, `-apple-system`, `Segoe UI`) — *incumbent, not a
commitment; a typeface change is open (operator, 2026-08-06). The functional bar any replacement
must clear is in PRODUCT.md's brand block.*
**Label / Figure Font:** Geist Mono (with `ui-monospace`, `SFMono-Regular`) — same status.

### Type scale

Nine steps, and no others. This list is the ramp; the Ramp Rule below states it as law.

| Step | Size | Role |
|---|---|---|
| Label | `font-size: 10px` | mono micro-label above a figure; status badges (UPPERCASE, 0.16em) |
| Micro | `font-size: 11px` | dense table meta, chip text, secondary row detail |
| Small | `font-size: 12px` | table cells and controls in dense grids |
| Compact | `font-size: 13px` | default UI text in cards and drawers |
| Body | `font-size: 14px` | running prose and roomy table cells |
| Title | `font-size: 17px` | card titles |
| Headline | `font-size: 20px` | section and drawer titles |
| Grid figure | `font-size: 24px` | the figure inside a dense matrix cell (weight steps to 500) |
| Display / Figure | `font-size: 28px` | the largest heading on a view; the headline number in a stat card |

**Character:** One family and its monospace sibling, nothing else, in both themes. The pairing
does all its work through weight and tracking: headings are *medium* (500), never bold, and figures
are *regular* (400) at large sizes — a big number here is large and light, not heavy. Mono is
reserved for two jobs only: micro-labels and anything numeric.

### The numeric-typography requirement, and how Geist Mono meets it

The requirement is a **capability**, not a font name. A console that updates numbers in place needs
figures that do not jitter, and glyphs that cannot be misread at 10–11px. Geist Mono was kept
rather than migrated to Inter / IBM Plex, and the decision rests on a direct inspection of the
font binary (`GeistMono-Medium.ttf` v1.401, `unitsPerEm` 1000, 846 glyphs):

| Requirement | Finding | Evidence |
|---|---|---|
| Figures do not shift width | **Met, structurally.** Every digit has advance width 600/1000 — the family is genuinely monospaced, so a column of numbers is already a column. | `hmtx` advance = 600 for all of `0`–`9` |
| `tabular-nums` feature | **Absent as a feature.** The GSUB feature list is `aalt case ccmp dnom frac liga locl numr ordn sinf ss01 ss02 ss03 ss04 ss06 ss07 ss08 ss09 subs sups` — there is no `tnum`. The CSS declaration is inert *for this face* and is kept only because it still governs the `ui-monospace` / `SFMono-Regular` fallbacks. | GSUB FeatureList, 20 unique tags |
| Disambiguated zero | **Met by default, no feature needed.** `zero` (gid 477) has **three** contours where `O` (gid 74) has two; the extra contour is a 4-point parallelogram spanning x[124,476] y[101,609] across the counter — a **slash, baked into the default glyph**. | `glyf` contour dump |
| `slashed-zero` feature | **Absent — and unnecessary.** There is no `zero` feature in GSUB, because the slash is not optional. **Do not declare `font-variant-numeric: slashed-zero` and expect it to do anything.** | GSUB FeatureList |
| `0` vs `O` | **Separated.** Slash present, and `0` is narrower (outer bowl 504 units vs 528). | contour bounding boxes |
| `1` vs `I` | **Separated at the top.** `I` is one contour with a full-width crossbar (444 units wide); `1` is a flagged stem plus a 488-unit foot serif. | 12 pts / 1 contour vs 15 pts / 2 contours |
| `1` vs `l` | **Weak — not certifiable.** Both are two contours, both 710 units tall, both with a 488-unit foot serif. The measured differences are a 15-unit stem offset (**0.15 px at 10px**) and a 14-unit foot-bar height difference (**0.14 px**), plus one extra outline point. | contour dump |
| Small-size metrics | x-height 532/1000 → **5.32 px at 10px**, 5.85 px at 11px. Cap height 710/1000 → 7.10 px / 7.81 px. | `OS/2` v4 `sxHeight`, `sCapHeight` |

**Ruling: Geist Mono is kept.** The two properties that actually matter for a money console —
non-shifting figures and an unmistakable zero — are met by the font's construction rather than by
optional features, which is a stronger guarantee than a feature flag. There is no font migration.

**What the earlier pass could not measure, and how it was settled.** Two things were left open
when this section was first written; both were closed on 2026-08-01 by rendering in a browser
rather than by reading the font binary.

1. **The `1`/`l` pair at real rendering size.** Geometry put the two glyphs within a fifth of a
   pixel of each other at 10px, and geometry could not decide whether they are *perceptually*
   separable. A render-and-observe test settled it — see below.
2. **The Google-served build — now measured, in the browser.** The earlier pass could only
   inspect the local Vercel/Raycast build v1.401 and flagged the Google `geistmono/v6` subset as
   unverified. It has since been tested where it actually matters: rendered by the browser, from
   Google, at the sizes the interface uses.

**Both open font questions are closed, and both closed against the declaration:**

- **`cv11` and `ss01` do nothing, in either family.** The same string was set twice — once plain,
  once with `font-feature-settings:'cv11','ss01'` — in Geist Sans and Geist Mono, at 40px, and
  the renderings were **identical**: the double-storey `a` stayed double-storey, the digits did
  not change, and the advance widths matched to three decimals (Sans 488.234 both ways, Mono
  566.883 both ways). `cv11` is an Inter convention that survived the move off Inter. **Both
  declarations were deleted from all three surfaces on 2026-08-01.** A declaration that changes
  nothing still reads as work done — the typographic form of claiming an unmeasured number.
- **`1` versus `l` is legible at 10–11px, and the exposure was never where it looked.** Rendered
  at 10, 11, 12, 13, 16 and 28px: `1` carries an angled flag and a full-width foot bar, `l` a
  narrower top flag and a curved right foot, `I` two crossbars. They are tight at 10px but they
  are distinct. More to the point, **`--label-size` mono is `text-transform: uppercase` by rule**,
  so a lowercase `l` never renders at 10px in this interface at all; the pair can only meet in
  `code` and drawer identifiers, which are set at 12px or larger. The earlier instruction to
  avoid mixed-case identifiers in mono is lifted.
- The `0` slash was confirmed visually at every size, which independently re-confirms that
  `slashed-zero` would be redundant even if the feature existed.

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

Type does not change between themes. The night ground does **not** get a heavier weight by
default; weight is the *remedy* held in reserve if halation is ever reported.

### Named Rules

**The Ramp Rule.** Nine sizes exist and no others: **10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28** px.
No half-steps, no `15px` because something looked slightly small. If a new element needs a size
that isn't on the ramp, it needs a different element.

**The Tabular Rule.** Every figure is Geist Mono, and every figure declares `tabular-nums`. The
declaration is defensive, not decorative: it is inert on Geist Mono itself (no `tnum` feature,
alignment already structural) and load-bearing on the `ui-monospace` fallback. Never rely on
`slashed-zero` — the slash is already in the default glyph and the feature does not exist.

**The Label-Above Rule.** A figure never appears without a mono micro-label above it naming what
it measures. A bare number on this desk is an unlabelled instrument.

## Layout

A single centred column against a fixed 208px index rail on the left and a fixed top bar of live
readings. The rail is always labelled; nothing overlays the sheet on hover. Layout is identical in
both themes — the switch changes colour values only, so no reflow, no shift, no relearning.

Spacing runs on a strict 4px base: **4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48**. Cards pad at 24px;
the gap between major blocks is 40px.

Density is the point. This is a console read daily, not a page browsed once — the reference's 20px
card padding and 21px radii were compressed to 24px and 12px so a four-column matrix still fits a
laptop screen without scrolling. There is one density, tuned for a single expert operator; a
"comfortable" mode would trade away the only advantage a dense console has.

Below 560px the rail wraps to two rows of chips rather than scrolling horizontally, and the drawer
takes the full width and locks body scroll. Horizontal overflow is clipped at the root
(`overflow-x: clip`, not `hidden` — `hidden` would create a scroll container and kill the rail's
`position: sticky`).

**Information hierarchy.** The surface follows an overview→detail ladder, and each rung has one
job: the triage band is the single-screen "is anything waiting for me?" reading; the view pages are
daily operation; the drawer is per-record detail; the diagnostics panels are troubleshooting. A
reading belongs on exactly one rung. The most common failure mode of an operator console is
answering the same question on two rungs, and the previous eight-page structure did exactly that
before it was consolidated to five.

### Named Rules

**The Aggregation Rule.** A bank of repeated health signals collapses to a single summary while
every member is healthy, and opens only the members that deviate — "bekçi 17/17" while all is well,
"3 geciken · <name> 4.2sa" when it is not. A wall of green indicators is not reassurance; it is
noise that trains the eye to skip the row, and the eye then skips it on the day it turns amber.

**The Alarm Budget Rule.** Signals that demand a human are a budget, and the budget is displayed as
a live reading, not assumed. The targets are the process-industry ones (EEMUA 191 / ISA-18.2 /
IEC 62682): roughly **80% low / 15% high-medium / 5% emergency**, **fewer than 10 signals per 10
minutes** at peak, and **fewer than 10 standing** on average. When the rate is chronically over
budget the response is to re-rationalise thresholds, never to raise the operator's tolerance. A
condition that is *always* red has stopped being a signal — that is normalization of deviance, and
it is the failure mode that made "AOA DISAGREE" an optional extra on the 737 MAX.

**The Not-Every-Event-Is-An-Alarm Rule.** If a human response is not required, the record belongs
in the event log, not in the alarm channel. The test is not "is this interesting?" but "does
someone have to do something?"

## Elevation & Depth

**There are no shadows in this system, in either theme.** Not on cards, not on the drawer, not on
modals. This was measured off the reference, where every card computes to `box-shadow: none`, and
it is now an invariant: the elevation token `--elev` is literally `none` in both value sets.

Depth is built two ways, and both survive the theme switch. **Tone**: `bg → bg2 → card → card-2` is
a four-step warm ramp in each theme, and a surface reads as nearer by moving along the ramp, not by
casting a shadow. Daylight moves *down* in value as it comes forward; night moves *up*. **Rule**: a
1px warm hairline closes the edge that a shadow would otherwise imply.

The one apparent exception is not one. `box-shadow: 0 3px 0 -2px var(--line)` under the top bar has
zero blur and negative spread — it draws a hairline 3px below the border, doubling the rule. It is
line work, not elevation.

### Named Rules

**The Flat Rule.** No `box-shadow` with a blur radius, anywhere, for any reason, in any theme. If a
surface needs to feel nearer, move it along the tonal ramp or give it a stronger rule. A shadow in
this system reads as a bug, and the detector will flag it as one.

**The Inset-Is-A-Border Rule.** `box-shadow: inset 0 0 0 1px …` is permitted and common — it is how
status pills draw a coloured hairline without changing their box size. Inset with zero blur is a
border. Anything else is elevation.

## Shapes

Corners are gentle and consistent, and identical in both themes: cards at 12px, controls and badges
at 10px. Bars and meters stay nearly square at 2px so a thin measurement reads as a measurement
rather than a lozenge. **There are exactly three radii.**

Borders are always exactly 1px and always a warm neutral, except where a status colour draws its
own inset hairline. Nothing is dashed. Nothing is doubled except the top bar's deliberate rule pair.

**There is no pill geometry, and this document used to claim otherwise.** Earlier versions listed a
`--r-pill: 999px` token and a rule reserving full-round corners for clickable things. The token was
removed from `index.html` during the Omega conversion because no rule referenced it, and a re-count
on 2026-08-01 found **zero** uses of `var(--r-pill)` across all three surfaces — while a dead
definition still sat in `landing.html`. Both the claim and the dead token are now gone. Every
control, including the primary action, is the 10px control radius.

The word *pill* survives in this document only as a shape-of-speech for a small filled control
(“the black pill”); it never denotes a 999px radius. If a future surface wants true full-round
geometry, it adds the token **and** a rule that uses it, in the same change.

**Meters are linear.** A quantity is drawn as a bar on a common baseline, never as an arc, a dial
or a ring — see *The Gauge Ban* below. The 2px confidence track under a matrix figure and the 5px
filled tube are the two permitted meter forms.

### Named Rules

**The Gauge Ban.** No radial gauges, no dials, no donuts, no rings, no speedometers, and no
decorative chrome around a number. Position on a common scale is the most accurately read visual
encoding (Cleveland & McGill 1984; Heer & Bostock 2010) and a radial meter throws that away in
exchange for pixels that carry no data.

*This rule was written while the interface still contained two of them.* A 92×92 `_donut` reported
model deflation and a 92×92 `_ring` reported the EOD refetch counter; both were replaced by bullet
graphs on 2026-08-01. Few is explicit that this is what the form is for — the bullet graph was
developed to replace the meters and gauges dashboards reach for by habit.

**The ban is on radial encoding, not on vertical bars.** The warm-up thermometer stays: it is
already linear, merely rotated. Deleting it would have been obedience to the word of the rule
against its reason. Cleveland & McGill's ranking is also **not universal** — McColeman et al. found
it task-dependent — so the ban rests on the stronger, simpler argument: an arc spends most of its
pixels on no data, and two arcs cannot be compared the way two bars on one axis can.

**The Bullet-Graph Rule.** Where a measure needs context — a target, a threshold, a healthy band —
draw Stephen Few's bullet graph, to spec: a text label; a single linear quantitative scale; the
featured measure as a visually prominent bar; one or two comparative measures as a short line
running **perpendicular** to the bar; and **two to five** qualitative ranges, ideally three.
Encode those ranges as **distinct intensities of a single hue**, never as distinct hues — distinct
hues are exactly what a colour-blind reader cannot separate. A bullet graph replaces a gauge; it
does not sit next to one.

**The Absent-Comparison Rule.** The perpendicular line is drawn only where a comparison value
genuinely exists. The EOD patience counter has one — `refetch_max` is the count at which the system
gives up — so it gets the line. Model deflation has no defined target, so it gets none. Drawing a
reference line at a made-up number would state a threshold the system does not have, and it would
look exactly like the one that is real.

**The Empty-Bar Rule.** A bar of zero length means *measured, and it came out zero*. When there is
no measurement, no bar is drawn at all: the axis and its ranges stay (the scale belongs to the
metric, not to the data), the readout is an em dash, and the words **ölçüm yok** appear beneath.
This is inherited from the donut it replaced, which drew an empty ring rather than a fake angle.
Ranges must therefore never be filled in as a background that could be mistaken for a value.
Where a call site previously wrote `attempts || 0`, it now passes `null` — `0/8` and *no reading*
are different claims and the interface must not merge them.

## Components

Every component below is identical in geometry across the two themes. Only the token values change.

### Theme Switch (rail foot, not the top bar)
- A single control at the **end of the left rail**, in the same group as Sign out, that swaps the
  value set. It shares that group's single separator rule.
- **It is not in the top bar, and that is a correction.** This document specified the top bar; the
  build put it in the rail because the top bar holds HALT and KRİZ, and HALT has a written rule
  giving it a fixed home — the bar was already forbidden from re-wrapping so the one lever a person
  reaches for by muscle memory never moves. Adding a control would have shifted it by roughly 44px.
  The rail foot is where session preferences already live, so the switch joined its own family.
- The switch is **explicit and persistent** — the operator's choice is remembered across sessions
  and is not silently overridden by `prefers-color-scheme`. A system preference seeds the first
  visit; after that the operator owns it, and a later change to the OS setting does not reach in.
- The two states are named for what they are, not for their colour: daylight / night.
- **The button names its destination, not its state:** in daylight it reads *Gece teması* with a
  moon. A single toggle that names its current state forces the reader to invert it to work out
  what pressing it does.
- It is a preference control, not an operational one. It carries no colour — hover is the neutral
  accent tint, never the red used by Sign out, because changing theme reports no loss.
- Only the button re-renders on switch, not the whole rail: a full redraw drops focus and a
  keyboard operator falls off the control they just used.

### Data Tables (`.tbl`)
- **This class had no stylesheet at all until 2026-08-01.** `app.js` emitted four
  `<table class="tbl">` and `index.html` defined nothing for it, so all four rendered with browser
  defaults — and because the global reset zeroes padding, their cells were touching. The class
  name existed; the contract behind it did not. Worth stating plainly: a named class is not
  evidence that anything styles it.
- **Header:** the mono 10px uppercase micro-label, left-aligned, over a single `--line-2` rule.
- **Rows:** separated by `--line` hairlines, none after the last row. No zebra striping, no
  vertical rules, no outer box — the card already closes the edge.
- **Numeric columns carry `.num`:** right-aligned, mono, `tabular-nums`. The header takes the
  class too, so the column reads from the same edge as its values. Decimals must line up or the
  column cannot be compared down its length, which is the only reason to put numbers in a column.
- Alignment is applied per cell, not per table: a table's text columns stay left-aligned.

### Bullet Graph (replaces the two radial gauges)
- **Fixed geometry: a 150px axis and a 54px readout, 212px in total.** Both are fixed on purpose.
  Two bullets with different axis lengths cannot be compared by length, which is the only advantage
  the form has over the donut it replaced. The readout box is fixed because the first build sized
  it to content and `%42,0` was clipped to `%42,`.
- **Label above, bare.** Mono, 10px, uppercase, `--label-track`. Not the boxed `.slabel` section
  chip — that gave every bullet the outline of a control and invited a click that does nothing.
- **Ranges:** two to five, ideally three, drawn as an intensity ladder over `--card-2` → `--line`
  → `--line-2` → `--tx3`. `--raise` is excluded: it measures 1.09 against a card and an invisible
  first range would make the range count a claim on paper only. **No separate night ladder exists** —
  the tokens invert, so the ladder runs light-to-dark in daylight and dark-to-light at night by
  itself.
- **The featured bar** is 6px inside a 12px range track, so the measure reads as distinct from the
  qualitative bands rather than as another band.
- **Colour follows state, not decoration:** neutral `--accent` while comfortable, `--amber` past
  60% of the axis, `--red` once the give-up threshold is reached. This is the alarm channel, not
  the money channel — see *The Money Rule*.

### Buttons
- **Shape:** gently curved (10px), 44px minimum height for every interactive control.
- **Secondary (default):** transparent fill, 1px `--line-2` border, `--tx` text at 13px/600,
  padding `9px 15px`.
- **Primary:** `--accent` fill, `--bg2` text — the black pill on the daylight ground, its
  off-white inverse at night. Measured 19.54 / 10.45.
- **Hover / Focus:** hover lifts the fill to `--accent-tint`; `:focus-visible` draws a 2px
  `--accent` outline at 2px offset. Transition is 150ms `ease`.
- **Danger:** transparent fill with a `--red` border and `--red` mono text — the HALT and KRİZ
  controls. These are the only buttons that carry colour, and they measure 6.55 (daylight) and
  7.41 (night) against the composited top bar.
- **Disabled:** 45% opacity, hover suppressed.

### Chips / Status Badges
- **Style:** mono 10px/700, uppercase, `0.09em`, 10px radius, `4px 9px` padding.
- **State:** a status tint fill at 10% alpha plus a matching inset hairline at 35% — gain for
  passed, caution for needs-a-human, loss for rejected, and a plain `--line-2` inset for neutral.
- **Never hue alone.** Every chip carries a word; every signed figure carries its sign; a
  directional reading carries a glyph as well as a hue. Around 8% of men have a colour-vision
  deficiency and red/green is the most commonly affected pair — a chip that means something only
  by being green has no meaning for them.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** `--card`; nested slips step to `--card-2`.
- **Shadow Strategy:** none — see Elevation & Depth.
- **Border:** 1px `--line-2`.
- **Internal Padding:** 24px.

### Inputs / Fields
- **Style:** 1px `--line-2` border, `--bg` fill, 10px radius, placeholder in `--tx2`.
- **Focus:** border shifts to `--accent` and the fill lifts to `--card`. No glow, no ring beyond
  the standard focus outline.
- The resting border measures 1.47 (daylight) / 1.65 (night) and is the system's one acknowledged
  1.4.11 exposure — see *Non-text contrast, measured and declared*.

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
- Top bar is `--bg` at 82% alpha with an 8px backdrop blur, closed by a hairline pair. It sits
  at the same value as the page so it reads as the sheet's ruled top edge, not a separate chrome.
  **The alpha must resolve from `--bg`, not from a literal.** A hard-coded `rgba(255,255,255,.82)`
  survives a theme switch and leaves a white bar over a dark page; the previous inverse of exactly
  this bug measured loss-on-bar at **1.27:1** and made the emergency stops invisible.

### Keyboard
- `1`–`7` switch views, **derived from the view list** rather than a literal key string, so the
  map cannot drift from the rail. `R` refreshes the active view. `?` opens the shortcut panel.
  `Esc` closes whatever is open.
- **`j` / `k` move between record rows.** The set is exactly `[data-rk]` — every row bound to the
  record ledger and nothing else — filtered to what is actually visible. Opening was already
  possible (rows are real `<button>`s, so Enter and Space worked); what was missing was moving
  *between* rows, because Tab stops at every focusable fragment inside a row rather than stepping
  row to row.
- **No wrapping at the ends.** `j` at the last row stays on the last row. A list that loops
  silently teleports the eye to the other end of the page.
- **Focus is set with `preventScroll` and the scroll is done by hand**, offset by `--navh`. The
  browser's own scrolling parks the focused row *underneath* the fixed top bar, so the row the
  operator just moved to would be the one row they cannot see.
- Guarded three ways, all verified: the handler does not fire inside `INPUT`/`TEXTAREA`/`SELECT`,
  does not fire while the drawer is open (a modal whose backdrop still responds to keys is not
  modal), and does not fire with a modifier held — `⌘K`/`⌘J` are deliberately left free.

### The Triage Band (signature)
The first element on the day view and the system's Level-1 reading: one sentence answering "is
anything waiting for me?", with the outstanding items as chips beside it. Calm is a quiet ruled
sentence you can read past; a state needing action is the loudest mark on the page.

**No warning is ever suppressed by the presence of another warning.** A liveness signal — a stale
heartbeat, a dead execution loop, a tripped breaker — cannot be dropped because something louder
exists. All of them are listed, the loudest first, and the band takes the colour of the loudest.
This rule is written from two real failures: a default view that discarded every amber signal, and
a rule that dropped all ambers as soon as one red appeared — which deleted the "the feed is down"
line at the exact moment the breaker tripped.

### The Setup × Regime Matrix (signature)
The interface's centrepiece: a grid of setup against market regime where each cell is a real
`<button>` announcing setup · regime · mean · n · hit-rate. The cell figure is mono 24px/500 at
−0.045em. A 2px confidence bar under each cell encodes sample size logarithmically, so a
three-trade mean can never look as firm as a fifty-five-trade one.

An unsown cell is drawn as bare ground with the word for "no measurement" — never as a zero, and
never interpolated from its neighbours. Clicking a cell opens the drawer. This click→drawer pattern
is the system's primary interaction and is applied uniformly to matrix cells, closed trades, plans,
hypotheses and events.

### The Drawer (signature)
A 430px right-hand panel on `--bg2` with a single left hairline, sliding in over 280ms on
`cubic-bezier(.16,1,.3,1)`. It is `role="dialog"` with `aria-modal`, traps focus, and returns focus
to the originating row on Escape. It starts *below* the top bar and sits *under* the nav in z-order,
so it can never occlude the emergency stop.

### Destructive Controls
- Irreversible actions are guarded twice: a cover that must be opened before the control is
  reachable, then an explicit confirmation naming exactly what will happen. The most destructive
  action in the system — flattening every position — confirms twice, and the second confirmation
  says "cannot be undone" in those words.
- Deliberate friction here is the feature, not a usability defect. A kill switch that can be hit
  by accident is not a kill switch.

### Named Rules

**The Confirmed-State Rule.** Nothing is drawn as done until the system that does it has confirmed
it. An order shows as pending until the fill is verified; an optimistic "filled" that later
reverses is worse than a slow truthful one, because the operator has already made the next decision
on it. Optimistic UI is for social apps, not for money.

**The No-Gamification Rule.** No celebration, no confetti, no streaks, no badges, no leaderboards,
no "most popular", no push notification tuned to provoke engagement, and no visual reward tied to
the frequency of trading. This is not a taste preference: it is the specific list of practices the
Massachusetts Securities Division charged and the SEC named in its digital-engagement-practices
release. A research console that rewards its operator for looking at it has started optimising the
wrong number.

**The Provenance-Is-Never-Optional Rule.** Data-health, source-stamp and reconciliation-drift
readings are always visible, never behind a setting and never an optional extra. The reason is on
the record: MCAS was fed by a single AoA sensor and the AOA DISAGREE alert was an optional extra
that most of the fleet did not have enabled, so no crew ever saw the data problem. A reading the
operator cannot see is a reading the operator does not have.

**The Honest-Absence Rule.** An unavailable value renders as an em dash and, where there is room, a
reason. Never zero, never a placeholder, never interpolated, and never a value carried forward from
a previous run. Where a value is imputed or repaired rather than observed, it says so and shows its
uncertainty.

## Do's and Don'ts

### Do:
- **Do** keep colour for money — gain, caution and loss, and nothing else chromatic anywhere.
- **Do** give every token a value in *both* value sets. A token with only one is a theme bug
  waiting for a switch.
- **Do** measure a new colour against its own composited ground, in both themes, before shipping.
- **Do** put a mono 10px uppercase label at `0.16em` above every figure.
- **Do** pick sizes from the ramp: 10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28 px.
- **Do** set figures in Geist Mono with `tabular-nums`, weight 400 at large sizes.
- **Do** build depth from the tonal ramp and 1px warm hairlines.
- **Do** show sample size next to any average — the confidence bar or an explicit `n`.
- **Do** give every interactive control a 44px minimum touch target.
- **Do** collapse a healthy bank of signals to one summary and open only what deviates.
- **Do** dual-code every state: word plus sign plus hue, never hue alone.
- **Do** keep provenance and data-health readings permanently visible.
- **Do** verify a borrowed value's contrast before adopting it — including values borrowed from an
  earlier version of this document.

### Don't:
- **Don't** hard-code a colour literal anywhere. A literal is invisible to the switch, and the
  night theme will inherit a daylight value in the one place it matters most.
- **Don't** derive a night value by inverting a daylight one. Measure it on its own ground.
- **Don't** use pure black or pure white on the night ground.
- **Don't** add a `box-shadow` with a blur radius. `--elev` is `none` and stays `none`.
- **Don't** introduce an accent hue. There is no interaction colour in either theme.
- **Don't** use a cool neutral for a border or panel. Warm only; `#f3f3f3` is permitted as a chip
  fill on the daylight ground and nowhere else.
- **Don't** draw a gauge, dial, donut or ring. Use a bar on a common baseline, or a bullet graph.
- **Don't** encode a bullet graph's qualitative ranges as distinct hues — use intensities of one.
- **Don't** set a heading bolder than 500 or a large figure bolder than 400.
- **Don't** invent a type size that isn't on the ramp.
- **Don't** add a fourth radius. There are three — 2px, 10px, 12px — and no pill.
- **Don't** promise `slashed-zero`. Geist Mono has no `zero` feature; the slash is already in the
  default glyph.
- **Don't** declare a font feature without rendering it both ways first. `cv11` and `ss01` sat on
  `body` for months and did nothing.
- **Don't** justify the night theme as "easier to read". It is a low-light ergonomics choice and
  the reading-performance evidence runs the other way.
- **Don't** substitute APCA for WCAG 2.2 AA.
- **Don't** let a warning be suppressed by the presence of a louder one.
- **Don't** show an action as complete before it is confirmed.
- **Don't** celebrate anything.
- **Don't** render a number the state file cannot produce. An unavailable value shows its absence,
  never a placeholder.
