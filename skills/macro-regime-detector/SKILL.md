---
name: macro-regime-detector
description: Detect structural macro regime transitions (1-2 year horizon) using cross-asset ratio analysis. Analyze RSP/SPY concentration, yield curve, credit conditions, size factor, equity-bond relationship, and sector rotation to identify regime shifts between Concentration, Broadening, Contraction, Inflationary, and Transitional states. Run when user asks about macro regime, market regime change, structural rotation, or long-term market positioning.
---

# Macro Regime Detector

Detect structural macro regime transitions using monthly-frequency cross-asset ratio analysis. This skill identifies 1-2 year regime shifts that inform strategic portfolio positioning.

## When to Use

- User asks about current macro regime or regime transitions
- User wants to understand structural market rotations (concentration vs broadening)
- User asks about long-term positioning based on yield curve, credit, or cross-asset signals
- User references RSP/SPY ratio, IWM/SPY, HYG/LQD, or other cross-asset ratios
- User wants to assess whether a regime change is underway

## Workflow

1. Load reference documents for methodology context:
   - `references/regime_detection_methodology.md`
   - `references/indicator_interpretation_guide.md`

2. Execute the main analysis script:
   ```bash
   uv run python3 skills/macro-regime-detector/scripts/macro_regime_detector.py --output-dir reports/
   ```
   This fetches 600 days of data for 9 ETFs + Treasury rates (~10 API calls total).
   An **FMP API key is required** to run this skill (the client raises if it is
   missing). For individual ETFs whose FMP historical-price endpoint returns
   nothing, the client automatically falls back to yfinance — this fallback
   needs no additional API key, but it does not remove the FMP key requirement.

3. Read the generated Markdown report and present findings to user.

4. Provide additional context using `references/historical_regimes.md` when user asks about historical parallels.

## Prerequisites

- **FMP API Key** (required): Set `FMP_API_KEY` environment variable or pass `--api-key`
- Free tier (250 calls/day) is sufficient (script uses ~10 calls)

## 6 Components

| # | Component | Ratio/Data | Weight | What It Detects |
|---|-----------|------------|--------|-----------------|
| 1 | Market Concentration | RSP/SPY | 25% | Mega-cap concentration vs market broadening |
| 2 | Yield Curve | 10Y-2Y spread | 20% | Interest rate cycle transitions |
| 3 | Credit Conditions | HYG/LQD | 15% | Credit cycle risk appetite |
| 4 | Size Factor | IWM/SPY | 15% | Small vs large cap rotation |
| 5 | Equity-Bond | SPY/TLT + correlation | 15% | Stock-bond relationship regime |
| 6 | Sector Rotation | XLY/XLP | 10% | Cyclical vs defensive appetite |

## 5 Regime Classifications

- **Concentration**: Mega-cap leadership, narrow market
- **Broadening**: Expanding participation, small-cap/value rotation
- **Contraction**: Credit tightening, defensive rotation, risk-off
- **Inflationary**: Positive stock-bond correlation, traditional hedging fails
- **Transitional**: Multiple signals but unclear pattern

## Output

- `macro_regime_YYYY-MM-DD_HHMMSS.json` — Structured data for programmatic use
- `macro_regime_YYYY-MM-DD_HHMMSS.md` — Human-readable report with:
  1. Current Regime Assessment
  2. Transition Signal Dashboard
  3. Component Details
  4. Regime Classification Evidence
  5. Portfolio Posture Recommendations

## Relationship to Other Skills

| Aspect | Macro Regime Detector | Market Top Detector | Market Breadth Analyzer |
|--------|----------------------|--------------------|-----------------------|
| Time Horizon | 1-2 years (structural) | 2-8 weeks (tactical) | Current snapshot |
| Data Granularity | Monthly (6M/12M SMA) | Daily (25 business days) | Daily CSV |
| Detection Target | Regime transitions | 10-20% corrections | Breadth health score |
| API Calls | ~10 | ~33 | 0 (Free CSV) |

## Script Arguments

```bash
python3 macro_regime_detector.py [options]

Options:
  --api-key KEY       FMP API key (default: $FMP_API_KEY)
  --output-dir DIR    Output directory (default: current directory)
  --days N            Days of history to fetch (default: 600)
```

## Resources

- `references/regime_detection_methodology.md` — Detection methodology and signal interpretation
- `references/indicator_interpretation_guide.md` — Guide for interpreting cross-asset ratios
- `references/historical_regimes.md` — Historical regime examples for context

---

## Folded in: ftd-detector (2026-07-30 skill audit)

`ftd-detector` was archived to `skills/_emekli/ftd-detector/` (not deleted). Its function already
exists in the engine as a crude proxy, so its methodology is kept here as that proxy's *specification*
— the regime layer's bottom-confirmation counterpart to this skill's structural read.

**What it is.** O'Neil's Follow-Through Day: confirmation that a correction has bottomed. Offensive
(when may exposure rise again), where `market-top-detector` is defensive. Dual index: S&P 500 + NASDAQ.

**State machine.** NO_SIGNAL → CORRECTION (3%+ decline with 3+ down days) → RALLY_ATTEMPT (days 1-3
off the swing low) → FTD_WINDOW (days 4-10, waiting for a qualifying follow-through) → FTD_CONFIRMED.
Failure exits: RALLY_FAILED (rally breaks the swing low) and FTD_INVALIDATED (close below the FTD
day's low). Days 1-3 are explicitly *not* a buy window.

**Quality score → exposure guidance.** 80-100 strong FTD (75-100%), 60-79 moderate (50-75%), 40-59
weak (25-50%), below 40 no/failed FTD (0-25%).

**Engine reality (do not overstate this).** `regime.py follow_through()` is a proxy — a single
>1.2% up-session within the last 5 sessions plus rising volume — writing the `ftd` field of
`state/regime.json`. The day-counting state machine, the invalidation rules and the post-FTD health
checks are NOT implemented, and Y3's regime quartet (SPY 200-SMA gate, VIX vs VIX3M, sector, heat)
deliberately excludes FTD. This section documents what a full implementation would owe; it does not
describe current behavior.
