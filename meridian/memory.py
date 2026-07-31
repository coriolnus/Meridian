"""memory.py — the thing that makes it actually learn. Records every hypothesis with its full
lifecycle, closes the loop by writing the realized score delta back onto the hypothesis once
min_sample trades have run under a version, and distills lessons.md into blunt reusable lines.

hypothesis schema (§4):
  {id, ts, version_from, version_to, variable, old, new, rationale, predicted_direction,
   confidence, regime, status, predicted_delta?, realized_delta?, backtest?}
status ∈ {proposed, rejected_by_guard, rejected_by_backtest, live, promoted, rolled_back}
"""
from __future__ import annotations
import datetime as dt
import threading
from collections import defaultdict
from typing import Optional

from . import store, config, obs

HYP = "hypotheses.jsonl"
ID_HWM_FILE = "hypothesis_id_hwm.json"   # kimlik yüksek-su işareti (defterden bağımsız, monoton)
LESSONS = "lessons.md"

# One lock for every hypotheses.jsonl mutation. record() appends while update_status()/
# writeback_outcome() do full-file read-modify-rewrite — and they run on DIFFERENT daemon threads
# (scheduler cycle vs Hermes reflection). An unlocked interleave could atomically replace the file
# with a snapshot that predates a just-shipped hypothesis: strategy.yaml already bumped, its ledger
# row gone forever (audit #19).
_HYP_LOCK = threading.Lock()


def now_iso(ts: Optional[str] = None) -> str:
    if ts:
        return ts
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def all_hypotheses() -> list[dict]:
    return store.read_jsonl(HYP)


def next_id() -> str:
    """Hipotez kimliği ASLA yeniden kullanılmamalı: defterdeki her satır (ve lessons.md, scoreboard,
    rollback kayıtları) bu kimlikle birbirine bağlanıyor.

    ESKİ HÂL `len(...)+1` idi (denetim turu 17, 2026-07-21): defter kısalırsa (yeniden tohumlama,
    elle temizlik, kısmi bir yazım) kimlikler GERİ SARAR ve iki farklı hipotez aynı kimliği taşır —
    'H00042 neden hem reddedildi hem canlı?' sorusu böyle doğar. Artık EN BÜYÜK mevcut numara + 1:
    tek yönlü, kısalmaya dayanıklı."""
    mx = 0
    for h in all_hypotheses():
        s = str(h.get("id") or "")
        if s.startswith("H") and s[1:].isdigit():
            mx = max(mx, int(s[1:]))
    # YÜKSEK-SU İŞARETİ (2026-07-22, kusur #7): `max+1` KISALMAYA dayanıklıydı ama SİLİNMEYE değil.
    # Defter tamamen boşalırsa (elle temizlik, yarım restore) numaralar H00001'den başlar ve
    # ARŞİVLENMİŞ satırlarla çakışır — "H00042 neden hem reddedildi hem canlı?" sorusu geri gelir.
    # İşaret ayrı bir dosyada ve MONOTON: defterden bağımsız, asla geri sarmaz.
    # DİKKAT: bu fonksiyon SAF SORGUDUR — işareti `record()` yazar. Okuma yolunun kendi tabanını
    # yazması, bugün watchdog'da düzeltilen hata sınıfının ta kendisiydi (iki `next_id()` çağrısı
    # farklı kimlik döndürüyor ve "türevler deterministiktir" yasası kırılıyordu).
    hwm = int((store.read_json(ID_HWM_FILE, {}) or {}).get("max", 0))
    return f"H{max(mx, hwm) + 1:05d}"


def record(hyp: dict) -> dict:
    with _HYP_LOCK:
        hyp.setdefault("id", next_id())
        hyp.setdefault("ts", now_iso())
        store.append_jsonl(HYP, hyp)
        # YÜKSEK-SU İŞARETİNİ YAZAN TEK YER BURASI (yazma yolu). `next_id()` saf sorgudur.
        _s = str(hyp.get("id") or "")
        if _s.startswith("H") and _s[1:].isdigit():
            _n = int(_s[1:])
            if _n > int((store.read_json(ID_HWM_FILE, {}) or {}).get("max", 0)):
                store.write_json(ID_HWM_FILE, {"max": _n})
    return hyp


# Geçiş yasası (2026-07-22, kusur #5): `update_status` HERHANGİ bir dizgiyi kabul ediyordu —
# `promoted → proposed` geriye dönüşü de, `status:"muz"` de. Statü aylık kotayı, UCB ödülünü ve
# `lessons.md`'yi besliyor; geçersiz bir geçiş sessizce öğrenme muhasebesini bozar.
# rejected_by_backtest / rejected_by_confirmation: reflect.py:477,492 bunları `record()` ile YAZAR
# (kapı ve teyit yürüyüşü redleri) ve reflect.py:254,328,592 terminal-red olarak OKUR — ama
# LEGAL_STATUS'te yoklardı. record() doğrulamaz, dolayısıyla yazım geçiyordu; ne var ki böyle bir
# satır bir gün update_status'e girerse "tanınmayan statü" diye sessizce reddedilir ve iki uygulama
# (yazan vs geçiş-yasası) ayrışırdı. İkisi de meşru terminal reddir (2026-07-23, tarama bulgusu).
LEGAL_STATUS = {"proposed", "rejected_by_guard", "rejected_by_gate", "rejected_by_backtest",
                "rejected_by_confirmation", "live", "promoted", "rolled_back", "superseded", "expired"}
TERMINAL_STATUS = {"rejected_by_guard", "rejected_by_gate", "rejected_by_backtest",
                   "rejected_by_confirmation", "promoted", "rolled_back", "superseded", "expired"}


def update_status(hyp_id: str, status: str, **extra) -> Optional[dict]:
    if status not in LEGAL_STATUS:
        obs.warn("illegal_hypothesis_status", hyp_id=hyp_id, status=status,
                 legal=sorted(LEGAL_STATUS),
                 detail="tanınmayan statü REDDEDİLDİ — defter uydurma durum taşıyamaz")
        return None
    with _HYP_LOCK:
        rows = all_hypotheses()
        updated = None
        for r in rows:
            if r.get("id") == hyp_id:
                _cur = r.get("status")
                if _cur in TERMINAL_STATUS and status != _cur:
                    # TERMİNAL DURUM GERİ ALINMAZ: `promoted → proposed` öğrenme geçmişini yeniden
                    # yazardı ve aynı değişiklik ikinci kez kotadan slot yakardı.
                    obs.warn("illegal_status_transition", hyp_id=hyp_id, **{"from": _cur, "to": status},
                             detail="terminal durumdan geri dönüş REDDEDİLDİ")
                    return None
                if _cur != status:
                    r["status_ts"] = now_iso()   # stamp TRANSITIONS only — a neutral-hold refresh must
                r["status"] = status             # not re-date the ship (it burned a monthly-quota slot
                r.update(extra)                  # forever and destroyed the audit trail — audit #20)
                updated = r
        if updated is not None:
            store.write_jsonl(HYP, rows)
        return updated


def accepted_this_month(ts: Optional[str] = None) -> int:
    """Count changes that went live/promoted in the current UTC month (anti-overfit throttle)."""
    month = (ts or now_iso())[:7]
    n = 0
    for h in all_hypotheses():
        if h.get("status") in ("live", "promoted") and str(h.get("status_ts", h.get("ts", "")))[:7] == month:
            n += 1
    return n


def writeback_outcome(version_to: int, realized_delta: float, realized_detail: dict) -> Optional[dict]:
    """Once min_sample trades have run under a version, write the realized score delta back onto
    the hypothesis that shipped it. This closes the loop — the entire point (§5 step 6)."""
    with _HYP_LOCK:
        rows = all_hypotheses()
        target = None
        for r in rows:
            if r.get("version_to") == version_to and r.get("status") in ("live", "promoted"):
                target = r
        if target is None:
            return None
        if target.get("status") == "promoted" and target.get("realized_delta") is not None:
            # Promotion is a one-way ratchet — its recorded outcome must be too. Rewriting a promoted
            # hypothesis's realized_delta/calibration_hit with every later market drift flip-flopped the
            # autonomy ladder's calibration gate and lessons.md while 'promoted' stayed frozen (audit #21).
            return target
        predicted = target.get("predicted_delta")
        target["realized_delta"] = round(realized_delta, 4)
        target["realized_detail"] = realized_detail
        # P3.d telemetry: market_regime must be a TOP-LEVEL, greppable field on the hypothesis row (the
        # eval-window regime the realized delta was measured in), not only nested inside realized_detail.
        if isinstance(realized_detail, dict) and realized_detail.get("market_regime"):
            target["market_regime"] = realized_detail["market_regime"]
        if predicted is not None:
            target["calibration_hit"] = bool((predicted > 0) == (realized_delta > 0))
        target["outcome_ts"] = now_iso()
        store.write_jsonl(HYP, rows)
        return target


def distill_lessons(trade_stats: Optional[dict] = None) -> str:
    """Regenerate lessons.md from the hypothesis ledger. Blunt, reusable, regime-aware lines that
    are injected into every reflection so the agent stops repeating dead ends."""
    hyps = all_hypotheses()
    lines = ["# Meridian — lessons.md",
             "_Durable memory distilled from the hypothesis ledger. Injected into every reflection._",
             "_Research system. Paper mode. Not financial advice._", ""]

    # failed dead-ends grouped by variable + direction + regime
    dead = defaultdict(list)
    for h in hyps:
        if h.get("status") in ("rejected_by_backtest", "rolled_back"):
            key = (h.get("variable"), h.get("predicted_direction"), h.get("regime", "any"))
            dead[key].append(h)
    if dead:
        lines.append("## Dead ends — do not retry")
        for (var, direction, regime), hs in sorted(dead.items(), key=lambda x: str(x[0])):
            vals = ", ".join(str(h.get("new")) for h in hs)
            lines.append(f"- **{var}** ({direction}, regime={regime}): tried {len(hs)}× "
                         f"[{vals}], all failed the gate/rollback. Do not retry these values.")
        lines.append("")

    # confirmed wins
    wins = [h for h in hyps if h.get("status") == "promoted" and h.get("calibration_hit")]
    if wins:
        lines.append("## Confirmed edges")
        for h in wins:
            lines.append(f"- **{h.get('variable')}** {h.get('old')}→{h.get('new')} "
                         f"(regime={h.get('regime','any')}): predicted {h.get('predicted_direction')}, "
                         f"realized_delta={h.get('realized_delta')}. Held up.")
        lines.append("")

    # calibration miss (proposed right direction of change but wrong outcome)
    misses = [h for h in hyps if h.get("calibration_hit") is False]
    if misses:
        lines.append("## Calibration misses — belief updated")
        for h in misses:
            lines.append(f"- **{h.get('variable')}** {h.get('old')}→{h.get('new')}: predicted "
                         f"delta {h.get('predicted_delta')}, got {h.get('realized_delta')}. "
                         f"Direction wrong — the thesis was off.")
        lines.append("")

    if trade_stats:
        lines.append("## Live trade stats")
        for k, v in trade_stats.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    if len(lines) <= 5:
        lines.append("_No lessons yet — the ledger is empty. The first reflection will populate this._")

    text = "\n".join(lines) + "\n"
    (config.STATE / LESSONS).write_text(text)
    return text
