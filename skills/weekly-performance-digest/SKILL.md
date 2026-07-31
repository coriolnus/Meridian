---
name: weekly-performance-digest
description: The single operator-facing periodic performance report — win rate, expectancy, profit factor, R-multiple, MAE/MFE, plus win/loss pattern analysis by source skill, exit reason, thesis type, sector, and mechanism. Reads closed thesis YAML when such a state directory exists; in Meridian the live data path is the engine's selfreview/analytics/counterfactual output. Also carries the folded process-adherence review and setup-cohort study rubrics. No API required; pure local calculation.
---

# Weekly Performance Digest

## Overview

Weekly Performance Digest aggregates the trades you closed during a week into a single
performance report. It reads CLOSED theses tracked by `trader-memory-core`
(`state/theses/th_*.yaml`), computes headline metrics (win rate, expectancy, profit
factor, R-multiple, MAE/MFE), breaks results down across several pattern dimensions
(source skill, exit reason, thesis type, sector, mechanism tag, screening grade), and
surfaces the week's biggest winners, losers, and lessons. Output is a JSON record plus
a human-readable Markdown report. Pure calculation — no API key required.

## When to Use

- At the end of a trading week to review aggregate realized performance
- To measure win rate and expectancy across all closed positions
- To see which source skills, exit reasons, sectors, or mechanisms drove wins vs losses
- To feed a month-end review (combine four weekly digests) or a postmortem
- For a quick "what worked / what didn't" snapshot grounded in real closed trades

## When Not to Use

- For buy/sell recommendations or position sizing — this skill is descriptive only

(Single-trade process review and signal-level true/false-positive classification used to live in
`trade-performance-coach` and `signal-postmortem`. Both were archived on 2026-07-30: the coach's
rubric is folded in below, and the postmortem taxonomy moved to `backtest-expert`.)

## Prerequisites

- Python 3.9+ with `PyYAML` (already a repo dependency)
- A state directory of closed thesis YAML files (`state/theses/`), as produced by the archived
  `trader-memory-core`. **Meridian has never had this directory** — the script runs and honestly
  reports an empty period, so read the "Data source reality" note at the end before quoting numbers.
- No API key required

## Workflow

### Step 1: Run the digest for a week

```bash
python3 skills/weekly-performance-digest/scripts/generate_weekly_digest.py \
  --state-dir state/theses \
  --from-date 2026-06-13 --to-date 2026-06-20 \
  --output-dir reports/ -v
```

Defaults: `--state-dir state/theses`, `--from-date` = 7 days before `--to-date`,
`--to-date` = today, `--output-dir reports/`. With no date flags it digests the
trailing 7 days.

### Step 2: Read the report

The run writes `reports/weekly_digest_<to-date>.json` and
`reports/weekly_digest_<to-date>.md`. Review the Markdown for the executive summary,
metrics table, pattern breakdowns, and top winners/losers; consume the JSON downstream.

### Step 3 (optional): Feed downstream

Combine several weekly JSON digests for a monthly review, or pass the JSON to a
postmortem/coach step. The skill is descriptive — act on its findings via your normal
review process.

## How It Works

- **Trade selection.** A trade counts in a week if its `exit.actual_date` falls in
  `[from-date, to-date]` and `status == CLOSED`.
- **Win/loss.** `outcome.pnl_dollars > 0` is a winner, `< 0` a loser, `== 0` breakeven;
  `win_rate = winners / total_trades`.
- **R-multiple.** `pnl_dollars / ((entry.actual_price − exit.stop_loss) × position.shares)`.
  (Stop-loss is read from `exit.stop_loss`, per the real thesis schema.)
- **Double-counting safeguard.** A CLOSED thesis's `outcome.pnl_dollars` is the
  *cumulative* realized P&L across all trims plus the final leg. Headline metrics use
  that cumulative value over CLOSED theses only. The separate `partial_trims` block
  scans `status_history[]` of **PARTIALLY_CLOSED theses only** (still open) and is
  reported for information — it is **never** added into the headline totals/win-rate.
  A position trimmed in week 1 then closed in week 2 therefore shows as a partial trim
  in week 1 and inside week 2's CLOSED headline; that is intended, not a duplicate.

## Output Format

### JSON (`weekly_digest_<to-date>.json`)

```json
{
  "schema_version": "1.0",
  "report_type": "weekly_performance_digest",
  "period": {"from": "2026-06-13", "to": "2026-06-20"},
  "generated_at": "2026-06-20T21:39:07Z",
  "summary": {
    "total_trades": 2, "winners": 1, "losers": 1, "breakeven": 0,
    "win_rate": 0.5, "expectancy": 25.0, "profit_factor": 2.0,
    "total_realized_pnl": 50.0, "total_realized_pnl_pct": 4.17
  },
  "metrics": {
    "avg_winner": 100.0, "avg_loser": -50.0,
    "largest_winner": 100.0, "largest_loser": -50.0,
    "avg_holding_days_winners": 9.0, "avg_holding_days_losers": 6.0,
    "r_multiple_avg": 0.25, "r_multiple_stdev": 1.06,
    "avg_mae_pct": -3.75, "avg_mfe_pct": 4.5
  },
  "pattern_analysis": {
    "by_source_skill": {"...": {"wins": 1, "losses": 0, "total": 1, "win_rate": 1.0}},
    "by_exit_reason": {}, "by_thesis_type": {}, "by_sector": {},
    "by_mechanism_tag": {}, "by_screening_grade": {}
  },
  "partial_trims": {"count": 0, "total_realized_pnl": 0.0, "trims": []},
  "lessons": {"top_wins": [], "top_losses": [], "process_improvements": []}
}
```

### Markdown (`weekly_digest_<to-date>.md`)

Sections: `# Weekly Performance Digest`, `## Executive Summary`,
`## Performance Metrics`, `## Pattern Analysis`, `## Lessons Learned`
(`### Top Winners` / `### Top Losers` / `### Process Improvements`).

An empty week still produces a valid report with zeroed metrics (exit code 0).

## Resources

- `scripts/generate_weekly_digest.py` — digest generator (JSON + Markdown)
- `references/weekly-digest-metrics.md` — metric formulas and interpretation

## Key Principles

1. **Closed trades only for headline numbers** — cumulative `outcome.*`, keyed on exit date.
2. **No double-counting** — partial trims are informational and excluded from totals.
3. **Pattern attribution** — every win/loss is attributed across multiple dimensions.
4. **Descriptive, not prescriptive** — the digest reports; you decide.

---

## Folded in: trade-performance-coach (2026-07-30 skill audit)

`trade-performance-coach` was archived to `skills/_emekli/trade-performance-coach/` (not deleted): it
duplicated this skill's role — the periodic, human-readable performance review — in the same P5 chain,
and neither had ever run. This skill is now the **single operator report**, and the coach's review
rubric is its qualitative half.

**Process adherence — what to check against the written plan.** Missing pre-entry thesis; setup
confirmation skipped; trade taken against the regime gate; stop moved without a pre-defined rule;
exit or partial close inconsistent with the plan; incomplete record quality.

**Risk discipline.** Per-trade risk above max; portfolio heat above max; weekly-loss or
consecutive-loss escalation; oversized trade right after a winner or a loser; correlated exposure.

**Execution quality.** Classify entry / stop / exit / add / trim behavior, and above all **separate a
clean-process loss from an execution mistake** — a losing trade that followed every rule is not a
finding.

**Behavior tags (evidence-bound, non-diagnostic language only).** `fomo_entry`, `revenge_trade`,
`premature_exit`, `overconfidence_after_winner`, `stop_moved`, `size_creep`, `hesitation`,
`rule_drift`, `no_pattern_detected`. Every tag must cite the record that produced it.

**Output shape.** Convert findings into *temporary, concrete* next-session guardrails (e.g. cap risk
at 0.5R for the next two trades after a rule violation; review-only mode after repeated revenge
evidence), then end with a human decision gate — `accept_rules` / `modify_rules` / `defer` /
`journal_only`, defaulting to `journal_only`. The report never changes system rules by itself.

## Folded in: stockbee-setup-fluency-trainer (2026-07-30 skill audit)

`stockbee-setup-fluency-trainer` was archived to `skills/_emekli/stockbee-setup-fluency-trainer/`
(not deleted): its forward-outcome measurement is exactly what `counterfactual.py` +
`analytics.skill_attribution` already do deterministically, on a much larger sample. What survives is
its **cohort-labelling vocabulary**, which the pattern-analysis section of this report can adopt.

**Cohort study loop.** Ingest screener candidates as study records (optionally including rejects as
negative examples), then update them once the 3-day and 5-day windows mature: forward close return,
MFE, MAE, stop-hit status and first stop-hit date per horizon.

**Outcome labels.** `STRONG_WINNER` (5-day return ≥ 8% or MFE ≥ 12%, no stop hit) · `WORKED` (≥ 4% or
MFE ≥ 6%, no stop hit) · `FAILED_STOP` (stop touched in the horizon) · `FAILED_FADE` (return ≤ -2%
with no stop hit) · `CHOPPY_FAILURE` (large adverse excursion, poor progress) · `NEUTRAL` · `PENDING`
(not enough future bars). Group by rating / trigger / setup tags with a minimum sample (5) per cohort.

**Its discipline, which the engine must keep.** Cohort findings are **evidence prompts, not automatic
rule changes** — promote a tag only on positive 5-day expectancy with acceptable average MAE, and
downgrade on repeated stop-hits or fades. In Meridian the accepted-lesson sink is the counterfactual
ledger and the hypothesis book, not the archived `trader-memory-core`.

## Data source reality (2026-07-30)

This SKILL.md describes a script that reads `state/theses/*.yaml` written by `trader-memory-core` —
which was retired in the same audit, and whose thesis store never existed in Meridian. So: the
**report template above is the deliverable**, and its live inputs are the engine's own measurement
layer (`selfreview`, `analytics.skill_attribution`, the counterfactual ledger). Do not present digest
numbers unless a real thesis directory is supplied on the command line; an empty run is honest output,
not a zeroed performance week.
