"""KANCALAR — motoru DEĞİŞTİRMEDEN defter toplama.

KAYNAK: research/olcumler/karne_tazeleme_2026-08-03/kosum_kanca.py — AYNEN, tek EK ile:
`fill_entry` kancası artık plan `stop`/`size_r`ını, çağrıya geçen `atr`/`gap_at_submit`
argümanlarını ve yasanın o çağrıdaki limit fiyatını da SATIRA YAZAR. Bu bir ÖLÇÜM eklentisidir:
sarmalayıcı yine orijinali çağırır, dönüşünü AYNEN geri verir, hiçbir dalı değiştirmez.
(`entry_limit_price` üretim fonksiyonudur ve saf hesaptır — ikinci bir icra modeli YAZILMADI.)

HÜKÜM DEĞİŞTİRMEZ: tek istisna `fill_entry`e `reject_out={}` geçirilmesidir — motorun KENDİ
parametresi (broker.py:283), varsayılanı None'dır ve verildiğinde YALNIZ ret nedenini dışarı yazar.

ÇAĞIRAN ÖNCE `config.STATE` (+ BARS/HISTORY) KURAR, SONRA bu modülü import eder.
"""
from __future__ import annotations

import pathlib

from meridian import backtest, dataset, shadowlaw          # noqa: F401
from meridian import broker as brk_mod                     # noqa: F401
from meridian import score as sc                           # noqa: F401
from meridian import config                                # noqa: F401
from meridian import analytics as an                       # noqa: F401
from meridian.adapters import data as data_adapter         # noqa: F401

MOTOR = pathlib.Path(backtest.__file__).resolve()
assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI çıktı — ölçüm geçersiz olurdu"

seanslar: list[dict] = []          # seans başına durum + huni bağlamı
fill_cagrilari: list[dict] = []    # fill_entry'e ULAŞAN her plan (dolan + reddedilen)
kapanislar: list[dict] = []        # close_position çağrıları
acik: set = set()                  # broker.positions'ın AYNASI (huni yeniden kurulumu için)
gap_gozlemi: dict = {"cagri": 0, "gap_at_submit_none": 0, "gap_at_submit_true": 0,
                     "gap_at_submit_false": 0}
_son_size_mult = [1.0]
_replay_res = [None]
_scan_sayaci = [0, 0]              # [scan_entry çağrısı, dönen sinyal] — seans başına sıfırlanır

_KURULU = [False]


def _kapat_seans_sayaclari() -> None:
    if seanslar and seanslar[-1]["n_scan_cagri"] is None:
        seanslar[-1]["n_scan_cagri"], seanslar[-1]["n_sinyal"] = _scan_sayaci[0], _scan_sayaci[1]
    _scan_sayaci[0] = _scan_sayaci[1] = 0


def kur() -> None:
    """Kancaları TAK. İki kez çağrılırsa sarmalayıcı sarmalanırdı — kelepçe."""
    assert not _KURULU[0], "kancalar zaten kurulu"
    _KURULU[0] = True

    # --- 1. replay sonucu (walk_forward onu dışarı vermez) ---
    _orig_replay = backtest.replay

    def _replay_kayitli(*a, **kw):
        res = _orig_replay(*a, **kw)
        _replay_res[0] = res
        return res

    backtest.replay = _replay_kayitli

    # --- 2. seans durumu: derisk_mult (seans başında) + max_positions_at (hemen ardından) ---
    _orig_derisk = backtest.brk.derisk_mult
    _orig_maxpos = backtest.brk.max_positions_at

    def _derisk_kayitli(equity, peak):
        m = _orig_derisk(equity, peak)
        _son_size_mult[0] = float(m)
        return m

    def _maxpos_kayitli(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)
        _kapat_seans_sayaclari()          # ÖNCEKİ seansın tarama sayaçları kapanır
        seanslar.append({"date": None, "eq_open": round(float(equity), 2),
                         "peak_equity": round(float(peak), 2), "size_mult": _son_size_mult[0],
                         "eff_max_open": int(n), "base_max_open": int(base_max),
                         "n_acik_seans_basi": len(acik), "acik_seans_basi": sorted(acik),
                         "regime": None, "exposure_budget_pct": None,
                         "n_scan_cagri": None, "n_sinyal": None})
        return n

    backtest.brk.derisk_mult = _derisk_kayitli
    backtest.brk.max_positions_at = _maxpos_kayitli

    # --- 3. fill_entry: ÇAĞRIYA ULAŞAN her plan + motorun KENDİ ret nedeni ---
    _orig_fill = backtest.PaperBroker.fill_entry

    def _fill_kayitli(self, plan, next_open, ts, equity, **kw):
        # ÇAĞIRANIN KENDİ `reject_out` SÖZLÜĞÜ KORUNUR (karne_tazeleme kancasından TEK ayrım):
        # o kanca çağıranın sözlüğünü POP edip yerine kendisininkini veriyordu ve motorun KENDİ
        # sayacı (`BacktestResult.entry_rejects`) bu yüzden BOŞ dönüyordu. Hüküm etkisi YOK
        # (sayaç yalnız sonuç nesnesine yazılır, hiçbir dalı beslemez); ama bağımsız çapraz
        # kontrolü geri kazandırır: motorun sayacı ile bu kancanın sayımı EŞİT olmalıdır.
        red = kw.get("reject_out")
        if red is None:
            red = {}
        kw["reject_out"] = red
        atr = kw.get("atr")
        gas = kw.get("gap_at_submit")
        gap_gozlemi["cagri"] += 1
        gap_gozlemi["gap_at_submit_" + ("none" if gas is None else str(bool(gas)).lower())] += 1
        pos = _orig_fill(self, plan, next_open, ts, equity, **kw)
        trig = plan.get("entry_trigger")
        law = brk_mod.entry_law()
        limit = (brk_mod.entry_limit_price(float(trig), atr, law)
                 if trig is not None else None)
        fill_cagrilari.append({
            "date": str(ts)[:10], "ticker": plan.get("ticker"), "plan_id": plan.get("id"),
            "plan_date": str(plan.get("date"))[:10], "next_open": round(float(next_open), 4),
            "trigger": (round(float(trig), 4) if trig is not None else None),
            "stop": (round(float(plan["stop"]), 4) if plan.get("stop") is not None else None),
            "size_r": plan.get("size_r"),
            "atr_gecen": (round(float(atr), 6) if atr is not None else None),
            "gap_at_submit": gas,
            "limit": (round(float(limit), 4) if limit is not None else None),
            "sonuc": ("dolu" if pos is not None else str(red.get("reason") or "?")),
            "red": (None if pos is not None else {k: v for k, v in red.items() if k != "reason"}),
        })
        if pos is not None:
            acik.add(plan.get("ticker"))
        return pos

    backtest.PaperBroker.fill_entry = _fill_kayitli

    # --- 4. close_position: aynayı güncel tut ---
    _orig_close = backtest.PaperBroker.close_position

    def _close_kayitli(self, ticker, raw_exit, reason, ts):
        row = _orig_close(self, ticker, raw_exit, reason, ts)
        acik.discard(ticker)
        kapanislar.append({"date": str(ts)[:10], "ticker": ticker, "reason": reason,
                           "r_multiple": row.get("r_multiple") if isinstance(row, dict) else None})
        return row

    backtest.PaperBroker.close_position = _close_kayitli

    # --- 5. rejim: seansın TARİHİ + maruziyet bütçesi (gün kapısının girdisi) ---
    _orig_regime = backtest.regime_mod.build_regime_json

    def _regime_kayitli(idx_df, params, asof):
        rj = _orig_regime(idx_df, params, asof)
        if seanslar:
            seanslar[-1]["date"] = str(asof)[:10]
            seanslar[-1]["regime"] = rj.get("regime")
            seanslar[-1]["exposure_budget_pct"] = rj.get("exposure_budget_pct")
        return rj

    backtest.regime_mod.build_regime_json = _regime_kayitli

    # --- 6. scan_entry: kaç sembol tarandı / kaç sinyal doğdu (huninin AĞZI) ---
    _orig_scan = backtest.strat.scan_entry

    def _scan_kayitli(*a, **kw):
        _scan_sayaci[0] += 1
        sig = _orig_scan(*a, **kw)
        if sig:
            _scan_sayaci[1] += 1
        return sig

    backtest.strat.scan_entry = _scan_kayitli


def bitir() -> None:
    """Koşum bittiğinde SON seansın sayaçlarını kapat (kapanışı bir sonraki seans yapardı)."""
    _kapat_seans_sayaclari()
