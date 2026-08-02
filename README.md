# Meridian

A self-improving US-equity **research** agent. It screens the S&P 500, plans swing-momentum trades,
sizes and enters them **on paper**, grades every closed trade, and rewrites its own strategy inside a
fixed sandbox — and it **cannot touch a dollar until it has earned it**.

> **Research system. Paper mode. Not financial advice.** Meridian is a research harness for studying
> whether an agent can learn an edge honestly. It does not provide investment advice, and it does not
> trade real money at its shipped autonomy level (L0).

---

## What it is

Three layers on one VM sharing one state directory:

- **Skill layer** — 66 Claude trading skills (regime, screeners, planners, post-mortem, edge
  research, meta/skill-authoring), bound into 5 deterministic, auditable pipelines.
- **Engine layer** — deterministic Python: `strategy.py` (pure signal, closed bars only), `broker.py`
  (realistic frictions), `backtest.py` (walk-forward OOS — the learning gate), `guard.py` (the real
  constraint layer), `score.py`, `memory.py`, `rollback.py`, `regime.py`, `health.py`.
- **Brain layer** — Hermes: reads state, forms one-variable hypotheses, and submits them through the
  engine's gate. It never edits the strategy by hand.
- **Control plane** — a FastAPI read-model + dashboard in the Meridian design language.

The product is **the loop, not the alpha**. The engine's job is to make the agent's learning honest:
realistic frictions, out-of-sample gates, written-back outcomes, automatic rollback. A "score went up"
is never confused with "an edge was found".

## The learning loop (why this exists)

1. Hermes may **propose** a change every `reflection_every` (5) closed trades.
2. A change only **ships** if it beats the incumbent on a **walk-forward out-of-sample backtest** by
   >0.02 AND there are ≥ `min_sample` (30) closed trades. Otherwise it's fitting noise.
3. Every hypothesis is logged with its prediction. Once enough live trades run under a version, the
   realised delta is written back and compared to what was predicted (calibration).
4. If a version underperforms its parent, `rollback.py` reverts it automatically.

Enforcement lives in **code, not prompts**. Everything Hermes is told, `guard.py` enforces.

## Two axes of self-improvement

- **Axis 1 — parameters.** `strategy.yaml` moves inside `bounds.yaml`, gated by the backtest.
- **Axis 2 — capability.** Hermes may author new skills for itself. Every new/modified skill runs in
  `skills/shadow/` for **10 sessions** on live data — scored against outcomes, unable to influence a
  trade — and is promoted only with **explicit human approval** in the dashboard. The agent may never
  promote its own skill.

## Autonomy ladder — how live trading is *earned*

```
L0  PAPER, FULLY AUTONOMOUS      ← ships today. Human watches. Zero real money.
L1  LIVE, EVERY ORDER APPROVED   ← every order waits in a queue, expires in 5 min.
L2  LIVE, AUTONOMOUS             ← real money inside the limits block.
```

Promotion L0 → L1 requires, and `guard.py` enforces: ≥ 60 closed paper trades · a positive score in
≥ 2 regimes · max drawdown within `goal.max_drawdown` for the whole paper period · ≥ 3 accepted
hypotheses whose realised outcome matched their prediction · zero unexplained circuit-breaker trips in
the last 20 sessions · a broker key with withdrawals disabled and this VM's IP allow-listed · **two
env flags flipped by hand** (`MERIDIAN_MODE=live`, `MERIDIAN_I_ACCEPT_RISK=true`) · a phone kill
switch. Meridian ships at **L0** and never flips a flag itself. The dashboard's **Today** page renders
exactly how far it is from being trusted with money.

---

## Run it locally

```bash
uv sync --extra dev
# seed real state from a historical replay on real bars (Cboe daily OHLCV, no key needed)
uv run python -m meridian.run --dry-run --replay 2023-01-01:2026-07-10
# tests (purity, frictions, guard rejections, score=None, rollback)
uv run pytest -q
# dashboard (read-only) → http://127.0.0.1:8080
uv run uvicorn meridian.api:app --host 127.0.0.1 --port 8080
# one live paper cycle
uv run python -m meridian.run --once
# THE 24/7 PATH — dashboard + in-process scheduler. `./serve.sh` does exactly this (plus keepalive).
MERIDIAN_AUTOSTART_CYCLE=1 CYCLE_POLL_SECONDS=300 \
  uv run uvicorn meridian.api:app --host 127.0.0.1 --port 8080
# force a reflection cycle (deterministic proposer — no LLM)
uv run python -m meridian.reflect --auto
```

> **`python -m meridian.run` is NOT the 24/7 worker (retired 2026-08-02, C3).** Its `worker()` was a
> *second* implementation of the daily cadence that never ran in production — every real start path
> (`serve.sh`, `ops/com.meridian.agent.plist`, `deploy/oracle-a1/meridian.service`) has always been
> uvicorn + the in-process scheduler. Because it never ran, it never got the fixes the scheduler did
> (session-close definition, `load_live` data path, ladder/repair progress gating). Calling it now
> refuses loudly and points here; the module docstring in `meridian/run.py` carries the full
> reasoning and the reversibility note. **Two cadence laws cannot live in one repository.**

Config lives in two **immutable** files Hermes may never edit: `state/goal.yaml` (success/failure/risk
contract) and `state/bounds.yaml` (the parameter sandbox).

## Deploy (GCP Compute Engine) — ⚠️ STALE, NOT the canonical path (marked 2026-07-30, K1)

> **Bu bölüm ve `Dockerfile`/`docker-compose.yml` GÜNCEL MİMARİDEN KOPMUŞTUR.** Kanonik dağıtım
> hedefi **Oracle Cloud A1**'dir: `deploy/oracle-a1/` (+ `RUNBOOK.md`, `meridian.service`), yerel
> işletim ise `./serve.sh` + `ops/keepalive.sh`. Bu yığın geri alınabilirlik için duruyor; ölçülen
> üç sapma, kullanılmadan önce düzeltilmelidir:
>
> 1. **Bağımlılıklar ayrışmış:** `Dockerfile` bağımlılık listesini EL İLE sayıyor ve
>    `pyproject.toml`'a sonradan giren `websockets` ile `redis` orada YOK. Konteyner, intraday
>    (Faz 2–4) ve WS ayna zincirini çalıştıramaz. Liste `pyproject.toml`'dan türetilmeli.
> 2. **Pano dışarıdan erişilemez:** `docker-compose.yml` uvicorn'u konteyner İÇİNDE `127.0.0.1`'e
>    bağlayıp portu publish ediyor — yayınlanan port konteyner loopback'ine ulaşmaz.
> 3. **Broker varsayılanı yanlış:** compose `MERIDIAN_BROKER` set etmiyor → `config.py` varsayılanı
>    `internal`. Diğer TÜM başlatma yolları (`serve.sh`, launchd plist, `oracle-a1/meridian.service`)
>    `alpaca_paper` kullanıyor — operatör kararı 2026-07-18. Sessiz bir broker sapması.
>
> Ayrıca `monitoring.sh` yalnız GCP'de anlamlıdır (bkz. o dosyanın başındaki not) ve **Redis hiçbir
> ops katmanında kurulmuyor** — A1'e deploy edilirse sıcak-durum zinciri kalıcı `down` başlar.

See `deploy/`. In order: `gcp_provision.sh` (VM + Cloud NAT + GCS bucket + Secret Manager, each create
confirmation-gated and cost-stated), `push_secret.sh` (secrets → Secret Manager, never to disk),
`deploy.sh` (code → VM over IAP), install the systemd unit (`deploy/meridian.service`), cron
`state_backup.sh` nightly, `monitoring.sh` for a stale-heartbeat alert, and — **last** —
`install_hermes.sh`. The dashboard binds to localhost only; reach it over an IAP tunnel:

```bash
gcloud compute ssh --tunnel-through-iap $VM_NAME --zone $VM_ZONE -- -L 8080:localhost:8080
```

## Day-after check-in

```bash
# heartbeat should be < 2 min old
gcloud compute ssh --tunnel-through-iap $VM_NAME --zone $VM_ZONE --command "cat /opt/meridian/state/heartbeat.json"
gcloud compute ssh --tunnel-through-iap $VM_NAME --zone $VM_ZONE --command "cd /opt/meridian && sudo docker compose ps"
tmux attach -t hermes            # watch the brain (on the VM); detach with Ctrl-b d
```

## Emergency stop

```bash
# stops all new entries within one bar (the big red button on the dashboard does the same)
gcloud compute ssh --tunnel-through-iap $VM_NAME --zone $VM_ZONE --command "touch /opt/meridian/state/HALT"
# resume
gcloud compute ssh --tunnel-through-iap $VM_NAME --zone $VM_ZONE --command "rm -f /opt/meridian/state/HALT"
```

## Locked strategy (this deployment)

S&P 500 · swing momentum · target +7% / 30d · max drawdown 8% · min Sharpe 1.2 · 5 positions · 1.0R
each · 3% max daily loss · reflect every 5 trades · min sample 30 · 5 bps slippage · skill evolution
on (shadow-mode). FMP and Alpaca keys not yet present — FMP screeners auto-enable when a key lands;
until then the engine trades on its internal broker using its self-contained momentum-breakout signal.

_Meridian is a research system. Paper mode. Not financial advice._
