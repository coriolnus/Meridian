# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Solo operator (the project owner) — the only user of every surface (dashboard, landing page,
workflow diagram). Not multi-tenant; no external investors, clients, or team members view this
system.

## Product Purpose

Meridian is a self-improving, paper-trading US-equity research agent. It screens the S&P 500,
plans swing-momentum trades, sizes and enters them on paper, grades every closed trade, and
rewrites its own strategy inside a fixed, code-enforced sandbox. Success means proving whether an
agent can learn a genuine trading edge honestly — not shipping a working money-maker. It is
explicitly a research system, not financial advice, and cannot trade real money at its shipped
autonomy level (L0).

## Positioning

Unlike a bot that just backtests and ships, Meridian enforces its own honesty in code, not
prompts: a strategy change only ships if it beats the incumbent on a walk-forward out-of-sample
backtest by a real margin; every hypothesis is logged with its prediction and later graded against
realized outcome (calibration); underperforming versions auto-rollback; new self-authored skills
run in shadow mode for 10 sessions before a human can promote them — the agent can never promote
its own skill. Live trading is *earned* through a strict, code-enforced autonomy ladder (L0 paper →
L1 every-order-approved live → L2 autonomous live), never toggled by the agent itself.

## Operating Context

- Runs as a 24/7 worker + FastAPI dashboard, either locally or on an Oracle Cloud A1 VM (systemd
  unit, IAP tunnel for remote access; the dashboard binds to localhost only).
- Three web surfaces, all served by `meridian/api.py` from `meridian/web/`:
  - `index.html` — the live operational dashboard ("Bugün" / Today).
  - `landing.html` — a marketing/intro page.
  - `workflow.html` — a workflow/architecture explainer ("Günlük Karar Hattı").
- The operator does a "day-after check-in" (heartbeat freshness, docker/tmux status) and holds a
  physical emergency stop (HALT file / dashboard button; a phone kill switch at L1+).
- UI copy is Turkish (`lang="tr"`) and stays Turkish through the redesign.

## Capabilities and Constraints

- Two config files the agent may never edit: `state/goal.yaml` (success/failure/risk contract) and
  `state/bounds.yaml` (parameter sandbox) — the UI should make it legible that these are
  human-owned, not agent-owned.
- Real-time state the dashboard surfaces: heartbeat, equity curve, open positions, regime, day P&L,
  circuit-breaker status, Hermes (brain) status/model, autonomy level, and progress toward the
  L0→L1 promotion gate.
- Shadow-mode skill promotion requires explicit human approval in the dashboard — this is a real,
  consequential control, not decoration.
- No fabricated data, testimonials, or performance claims — every number shown must trace to real
  state files under `state/`.

## Brand Commitments

- Product name: Meridian.
- **Standing visual preference — TWO GROUNDS (revised 2026-07-31 by the operator, binding;
  amends the 2026-07-27 light-only decision, which remains binding for the daylight ground):**
  the Omega conversion stands and is not reopened; a **second, night ground is added beside it**,
  and the operator switches between them with a control in the top bar.
  - **One token vocabulary, two value sets.** There is exactly one set of CSS variable names.
    Geometry, type scale, spacing, radii and the zero-shadow invariant are identical across the
    two grounds — **only colour values change**. A theme switch must cause no reflow and no
    relearning. Any token that exists in one set and not the other is a bug.
  - **Why a night ground, stated honestly:** it is a **24/7 low-light ergonomics** choice, not a
    readability claim. The reading-performance evidence runs the *other* way (Piepenbrock et al.,
    *Ergonomics* 2013/2014: positive polarity — dark text on light — is faster and more accurate),
    and roughly 40–47% of adults have some astigmatism and see halation around light glyphs on a
    dark field. The daylight ground therefore stays the **default**; the night ground is for a
    shift worked in a dark room and is the operator's to choose.
  - **Night ground constraints:** no pure black (`#000`) and no pure white (`#fff`); a warm
    dark-grey field around `#1E1E1E` with off-white text in the `#CCC`–`#D4D4D4` band. Warm
    neutrals throughout, so the two grounds read as one product.
  - **The night ground is NOT a return to "CAM KOKPİT."** The rejected dark world was a cold
    blue-black instrument panel with an instrument-cyan accent and IBM Plex. This is the Omega
    grammar re-lit: same warm neutrals, same absence of an interaction colour, same black-pill
    logic inverted to an off-white pill. Do not resurrect the old palette.
  - Concrete token values, per-theme, with measured contrast ratios: `DESIGN.md`.
  - Confirmed 2026-07-27 and unchanged: **all three surfaces convert** (landing, dashboard,
    workflow) and **all seven Omega section patterns** are adopted.
  - Measured from the live preview at `omega.nextjsshop-preview.workers.dev`, not guessed:
    type **Geist + Geist Mono** (identical to what Meridian already loads — no font migration);
    ground `#ffffff`, warm bone panels `#f8f5f2` / `#fbfaf8` / `#f1ece8`, cool chip `#f3f3f3`;
    warm hairlines `#e7e3df` / `#d9d4cf`; ink `#050505`, pure `#000` for the primary pill;
    card radius **16–21px**, controls **full pill**; **no shadows anywhere** — separation is
    hairline + tint only; headline Geist **500** at `-0.02em`; big numbers Geist **400**,
    `line-height:1`, `-0.04em`; signature label idiom **Geist Mono 10px UPPERCASE `0.16em`**
    in `#8f8b86`.
  - **Licence boundary:** the design *language* is the reference; Omega's code is not copied.
    Meridian is vanilla HTML/CSS/JS against their Next.js/Tailwind/React, so all CSS is authored
    fresh. Do not vendor, paste, or reconstruct their source.
  - **Density is not inherited.** Omega is a Persuade (marketing) surface; `index.html` and
    `workflow.html` are Operate. Take Omega's grammar, compress its scale — 21px radius and 20px
    padding on a four-column setup×regime matrix cell destroys the density the operator needs.
  - Prior rejected directions, kept as anti-references: a cyanotype specimen ledger, an
    agricultural experiment station, and the dark Linear/Vercel/Raycast canon that this replaces.
    Do not propose a themed or historical world; Omega is a straight product-software reference.
    Adding a night ground does **not** reopen any of these — it re-lights Omega, it does not
    replace it. If a future pass wants to depart from this, ask first — this is a preference, not
    a guess.
- The current dashboard (`index.html`) already carries a named, deliberate visual language — "CAM
  KOKPİT" (glass cockpit): cold blue-black instrument-panel surfaces, hairline rules, no
  shadows/gradients, IBM Plex Sans + Mono, one instrument-cyan accent, state-only green/amber/red.
  Confirmed as anti-reference for this redesign, not a constraint to preserve — full replacement is
  in scope.
- `landing.html` and `workflow.html` currently carry two further, mutually inconsistent visual
  languages (Space Grotesk/Inter/violet; Segoe UI/multicolor category badges). Redesign should
  unify all three under one chosen world.

## Evidence on Hand

- Live state files under `state/` (`heartbeat.json`, `hermes_status.json`, `equity_curve.json`,
  `events.jsonl`, `hypotheses.jsonl`, etc.) are the only source of real numbers/content — never
  invent metrics.
- `README.md` is the authoritative product description.

## Product Principles

1. Instrument, not marketing — the operational dashboard must read like a control panel a solo
   operator trusts at a glance, not a pitch.
2. Enforcement is visible — the gates, immutable configs, and autonomy ladder that keep this a
   research system (not a live-money bot) should be legible in the UI, not buried.
3. One coherent world across all three surfaces — dashboard, landing, and workflow explainer read
   as one product, not three.
4. Real data only — every visualized number traces to a real state file; never dress up
   placeholders as live data.
5. Turkish-first copy — voice and labels stay in Turkish; the visual language changes, the language
   does not.

## Accessibility & Inclusion

No externally required standard applies (single private operator, no public users). The bar the
project holds itself to is **WCAG 2.2 AA**, and it now applies to **both grounds** — every text
token clears 4.5:1 against the worst surface it actually composites onto, measured rather than
estimated (see `DESIGN.md`). APCA may inform night-ground tuning but never replaces WCAG 2.2 as
the standard; it is not an approved WCAG 3 method.

Two known deviations are declared rather than hidden: hairline borders do not reach the 3:1
non-text bar in either ground (the text-input border is the one real exposure), and full ARIA
live-region coverage is deliberately partial — a console streaming continuous numbers would drown
a screen reader, so only critical state changes announce.
