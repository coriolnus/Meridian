---
name: edge-pipeline-orchestrator
description: Orchestrate the full edge research pipeline from candidate detection through strategy design, review, revision, and export. Use when coordinating multi-stage edge research workflows end-to-end.
---

# Edge Pipeline Orchestrator

Coordinate all edge research stages into a single automated pipeline run.

## When to Use

- Run the full edge pipeline from tickets (or OHLCV) to exported strategies
- Resume a partially completed pipeline from the drafts stage
- Review and revise existing strategy drafts with feedback loop
- Dry-run the pipeline to preview results without exporting

## Workflow

1. Load pipeline configuration from CLI arguments
2. Run auto_detect stage if --from-ohlcv is provided (generates tickets from raw OHLCV data)
3. Run hints stage to extract edge hints from market summary and anomalies
4. Run concepts stage to synthesize abstract edge concepts from tickets and hints
5. Run drafts stage to design strategy drafts from concepts
6. Run review-revision feedback loop:
   - Review all drafts (max 2 iterations)
   - PASS verdicts accumulated; REJECT verdicts accumulated
   - REVISE verdicts trigger apply_revisions and re-review
   - Remaining REVISE after max iterations downgraded to research_probe
7. Export eligible drafts (PASS + export_ready_v1 + exportable entry_family)
8. Write pipeline_run_manifest.json with full execution trace

## CLI Usage

```bash
# Full pipeline from tickets
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --output-dir reports/edge_pipeline/

# Full pipeline from OHLCV
python3 scripts/orchestrate_edge_pipeline.py \
  --from-ohlcv path/to/ohlcv.csv \
  --output-dir reports/edge_pipeline/

# Resume from drafts stage
python3 scripts/orchestrate_edge_pipeline.py \
  --resume-from drafts \
  --drafts-dir path/to/drafts/ \
  --output-dir reports/edge_pipeline/

# Review-only mode
python3 scripts/orchestrate_edge_pipeline.py \
  --review-only \
  --drafts-dir path/to/drafts/ \
  --output-dir reports/edge_pipeline/

# Dry run (no export)
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --output-dir reports/edge_pipeline/ \
  --dry-run
```

## Output

All artifacts are written to `--output-dir`:

```
output-dir/
├── pipeline_run_manifest.json
├── tickets/          (from auto_detect)
├── hints/hints.yaml  (from hints)
├── concepts/edge_concepts.yaml
├── drafts/*.yaml
├── exportable_tickets/*.yaml
├── reviews_iter_0/*.yaml
├── reviews_iter_1/*.yaml  (if needed)
└── strategies/<candidate_id>/
    ├── strategy.yaml
    └── metadata.json
```

## Claude Code LLM-Augmented Workflow

Run the LLM-augmented pipeline entirely within Claude Code:

1. Run auto_detect to produce `market_summary.json` + `anomalies.json`
2. Claude Code analyzes data and generates edge hints
3. Save hints to a YAML file:

```yaml
- title: Sector rotation into industrials
  observation: Tech underperforming while industrials show relative strength
  symbols: [CAT, DE, GE]
  regime_bias: Neutral
  mechanism_tag: flow
  preferred_entry_family: pivot_breakout
  hypothesis_type: sector_x_stock
```

4. Run orchestrator with `--llm-ideas-file` and `--promote-hints`:

```bash
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --llm-ideas-file llm_hints.yaml \
  --promote-hints \
  --as-of 2026-02-28 \
  --max-synthetic-ratio 1.5 \
  --strict-export \
  --output-dir reports/edge_pipeline/
```

### Optional Flags

- `--as-of YYYY-MM-DD` — forwarded to hints stage for date filtering
- `--strict-export` — export-eligible drafts with any warn finding get REVISE instead of PASS
- `--max-synthetic-ratio N` — cap synthetic tickets to N × real ticket count (floor: 3)
- `--overlap-threshold F` — condition overlap threshold for concept deduplication (default: 0.75)
- `--no-dedup` — disable concept deduplication

Note: `--llm-ideas-file` and `--promote-hints` are effective only during full pipeline runs.
`--resume-from drafts` and `--review-only` skip hints/concepts stages, so these flags are ignored.

## Resources

- `references/pipeline_flow.md` — Pipeline stages, data contracts, and architecture
- `references/revision_loop_rules.md` — Review-revision feedback loop rules and heuristics

---

## Folded in: the edge-* stage skills (2026-07-30 skill audit)

Five skills that were separate registry entries — each declaring itself enabled while never running —
are now documented here, because they are **stages of this one workflow**, not independent skills:
`edge-hint-extractor`, `edge-concept-synthesizer`, `edge-strategy-designer`, `edge-candidate-agent`
and `trade-hypothesis-ideator`. Their folders moved to `skills/_emekli/<name>/` (archived, not
deleted) and `SCRIPT_PATHS` in `scripts/orchestrate_edge_pipeline.py` resolves each stage script from
the live folder first, then the archive — so a restored folder needs no code edit.
`edge-strategy-reviewer` stays a live skill: it is the one family member Hermes actually preloads.

**Stage 1 — hints (was edge-hint-extractor).** Turns raw observations (`market_summary.json`,
`anomalies.json`, optional news reactions) into a canonical `hints.yaml`. Rule-based hints by default;
LLM ideation is opt-in via `--llm-ideas-file` (Claude writes the YAML) or `--llm-ideas-cmd` (external
CLI) — mutually exclusive. This is the `observe → abstract → design → pipeline` chain's first link.

**Stage 2 — concepts (was edge-concept-synthesizer).** Clusters ticket evidence into *mechanism-level*
concepts, each with an explicit thesis AND invalidation signals, plus support statistics and an export
readiness flag. Its purpose is to stop ticket→strategy overfitting: concepts are deduplicated by
condition containment (`--overlap-threshold`, default 0.75) and only high-support concepts
(`--min-ticket-support`) should be promoted to drafting.

**Stage 3 — drafts (was edge-strategy-designer).** Turns each concept into strategy variants under a
risk profile (conservative / balanced / aggressive), calibrating exits per hypothesis type via
`HYPOTHESIS_EXIT_OVERRIDES` (stop-loss, reward-to-risk, time-stop, trailing-stop for breakout,
earnings_drift, panic_reversal, …) and clamping reward-to-risk at `RR_FLOOR = 1.5` so drafts do not
fail the reviewer's C5 check by construction.

**Stage 4 — export + validate (was edge-candidate-agent).** Writes
`strategies/<candidate_id>/strategy.yaml` + `metadata.json` against the `edge-finder-candidate/v1`
interface. Its guardrails are the load-bearing part: keep `validation.method: full_sample` and leave
`validation.oos_ratio` null; export only supported entry families (`pivot_breakout` with
`vcp_detection`, `gap_up_continuation` with `gap_up_detection`) and mark everything else research-only;
reject schema-bound violations (risk, exits, empty conditions) and any folder-name/`id` mismatch;
require deterministic metadata carrying the interface version; always dry-run the pipeline first.

**Ideation contract (was trade-hypothesis-ideator).** Its distinctive contribution is not "more
ideas" — Hermes already generates single-variable hypotheses in-engine with a guard and a backtest
gate — but the **card shape**: every hypothesis carries a falsifiable statement, an experiment design,
explicit **kill criteria**, and a verdict of `pursue` / `revise` / `discard`. When this pipeline feeds
Hermes, keep that shape: a hypothesis without kill criteria is not a hypothesis, and evidence quality
(sample size, snippet provenance) is rated before a card is ranked.

**Activation gate — do not skip this.** This orchestrator is engine-*declared* only: `loop.py`'s P5
run never invokes it, and no manifest has ever been produced. Per ROADMAP it may only be activated
AFTER Y1 (DSR/PSR + PBO/CSCV), with its drafts wired into the 2.4 shadow-variant ledger. Activating
it before that measurement link exists would recreate the "invoked lie" one layer up, in the research
layer — see `aktivasyon_kosulu` on this skill's registry entry.
