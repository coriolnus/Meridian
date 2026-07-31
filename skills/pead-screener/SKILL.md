---
name: pead-screener
description: Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns. Analyzes weekly candle formation to detect red candle pullbacks and breakout signals. Supports two input modes - FMP earnings calendar (Mode A) or earnings-trade-analyzer JSON output (Mode B). Use when user asks about PEAD screening, post-earnings drift, earnings gap follow-through, red candle breakout patterns, or weekly earnings momentum setups.
---

# PEAD Screener - Post-Earnings Announcement Drift

Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns using weekly candle analysis to detect red candle pullbacks and breakout signals.

## When to Use

- User asks for PEAD screening or post-earnings drift analysis
- User wants to find earnings gap-up stocks with follow-through potential
- User requests red candle breakout patterns after earnings
- User asks for weekly earnings momentum setups
- User provides earnings-trade-analyzer JSON output for further screening

## Prerequisites

- FMP API key (set `FMP_API_KEY` environment variable or pass `--api-key`)
  ```bash
  export FMP_API_KEY=your_api_key_here
  ```
- Free tier (250 calls/day) is sufficient for default screening
- For Mode B: earnings-trade-analyzer JSON output file with schema_version "1.0"

## Workflow

### Step 1: Prepare and Execute Screening

Run the PEAD screener script in one of two modes:

**Mode A (FMP earnings calendar):**
```bash
# Default: last 14 days of earnings, 5-week monitoring window
python3 skills/pead-screener/scripts/screen_pead.py --output-dir reports/

# Custom parameters
python3 skills/pead-screener/scripts/screen_pead.py \
  --lookback-days 21 \
  --watch-weeks 6 \
  --min-gap 5.0 \
  --min-market-cap 1000000000 \
  --output-dir reports/
```

**Mode B (earnings-trade-analyzer JSON input):**
```bash
# From earnings-trade-analyzer output
python3 skills/pead-screener/scripts/screen_pead.py \
  --candidates-json reports/earnings_trade_analyzer_YYYY-MM-DD_HHMMSS.json \
  --min-grade B \
  --output-dir reports/
```

**Scheduled US-equity routine pitfall:** Prefer Mode B for pre-market / US-equity cron briefs after running `earnings-trade-analyzer`. Mode A can pull the global FMP earnings calendar, spend the API budget on non-US symbols, and return weak/non-actionable foreign listings before reaching the intended US watchlist. If Mode A is used anyway and the script reports budget trimming or non-US symbols, mark PEAD output as degraded and treat it as manual-review only rather than a clean candidate source.

### Step 2: Review Results

1. Read the generated JSON and Markdown reports
2. Load `references/pead_strategy.md` for PEAD theory and pattern context
3. Load `references/entry_exit_rules.md` for trade management rules

### Step 3: Present Analysis

For each candidate, present:
- Stage classification (MONITORING, SIGNAL_READY, BREAKOUT, EXPIRED)
- Weekly candle pattern details (red candle location, breakout status)
- Composite score and rating
- Trade setup: entry, stop-loss, target, risk/reward ratio
- Liquidity metrics (ADV20, average volume)

### Step 4: Provide Actionable Guidance

Based on stages and ratings:
- **BREAKOUT + Strong Setup (85+):** High-conviction PEAD trade, full position size
- **BREAKOUT + Good Setup (70-84):** Solid PEAD setup, standard position size
- **SIGNAL_READY:** Red candle formed, set alert for breakout above red candle high
- **MONITORING:** Post-earnings, no red candle yet, add to watchlist
- **EXPIRED:** Beyond monitoring window, remove from watchlist

## Output

- `pead_screener_YYYY-MM-DD_HHMMSS.json` - Structured results with stage classification
- `pead_screener_YYYY-MM-DD_HHMMSS.md` - Human-readable report grouped by stage

## Resources

- `references/pead_strategy.md` - PEAD theory and weekly candle approach
- `references/entry_exit_rules.md` - Entry, exit, and position sizing rules

---

## Folded in: earnings-trade-analyzer (2026-07-30 skill audit)

`earnings-trade-analyzer` was archived to `skills/_emekli/earnings-trade-analyzer/` (not deleted):
its post-earnings momentum scope overlapped this screener one-to-one and its style gate was already
off. Mode B above still works — the producer script is now at
`skills/_emekli/earnings-trade-analyzer/scripts/analyze_earnings_trades.py`.

**The 5-factor pre-filter worth keeping.** Gap size, pre-earnings 20-day trend, volume ratio (20-day
vs 60-day average), position vs the 200-day MA, position vs the 50-day MA → composite 0-100 with
grades A 85+, B 70-84, C 55-69, D <55. A/B are the actionable band, C is caution, D is avoid. Always
read the weakest and strongest component, not just the total: a good total carried by gap size alone
is a different setup from one carried by trend and MA position.

**Two honesty rules it carried, worth keeping.** (1) When the earnings endpoint degrades or the API
budget runs out, present names as **preliminary / ungraded** — never assign A-D grades from fallback
quote data the 5-factor scorer never saw. (2) `Candidates after filtering: 0` exits *successfully*
without writing a JSON file; say plainly that no scored file was produced instead of pointing Mode B
at a nonexistent path.

**Engine reality.** This screener is engine-implemented (`skills.py ENGINE_IMPLEMENTED`) and
`state/earnings.csv` fills from a keyless Nasdaq source, so PEAD measurement never depended on the
archived scorer.
