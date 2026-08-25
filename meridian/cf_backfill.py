"""cf_backfill.py — karşı-olgusal defteri TÜM TARİHİ SEANSLARA koşturarak dolduran tek-seferlik motor.

KÖK NEDEN. counterfactual.collect/advance yalnız canlı daily_cycle'da çağrılır; tarihi replay
gerçek işlemler üretmişken SIFIR karşı-olgusal kanıt bırakmıştı — kanıt motoru tarihin üstünden hiç
geçmemişti. Bu modül o boşluğu kapatır: `run(start, end)` her tarihi seansta daily_cycle'ın P2
(tarama) + P3 (plan+kapı) bloklarını BİREBİR AYNI CANLI FONKSİYONLARLA yeniden koşar
(`_plans_for_session`: regime_mod.build_regime_json, config.resolve_params, strat.scan_all,
guard.classify_gate; sonra cf.collect + cf.advance) — P4/P5 (dolum/kalibrasyon) yükü OLMADAN.
Sonuç: yüzlerce simüle aday sonucu, bir gecede, tarihten.

KİLİT GİRİŞLER: önbellekli barlar (ağa çıkılmaz — taze veri çekmek barları değiştirir ve replay'i
bozar), goal/bounds/params, strategy.ARMED_SETUPS (uyuyan/silahlı ayrımı), near-miss gevşek
eşikleri tek kaynaktan (strat.relax_for_near_miss).

DÜRÜSTLÜK DEĞİŞMEZLERİ:
  • İleri-yönlü sim — cf.advance her satırı yalnız KENDİ giriş-sonrası barlarıyla çözer
    (look-ahead yok); rastgelelik yok, aynı barlar + aynı aralık → aynı satırlar.
  • SIFIR kapı yetkisi — cf yalnız ölçüm besler (skor kalibrasyonu, skill katkısı, near-miss,
    fidelity); hiçbir kararı/kapıyı etkilemez (counterfactual.py yasası).
  • Portföy-BAĞIMSIZ kapı — gate'e düz portföy (0 pozisyon) verilir: cf, PER-ADAY seçim kalitesini
    ölçer, o günkü tesadüfi holdinglerin ısı/korelasyon durumunu değil — bilinçli bir seçim.
Yeniden mekanizma DEĞİL — mevcut motoru tasarlandığı derinlikte çalıştırma.
OKUR: bar önbelleği, state sözleşme dosyaları. YAZAR: yalnız karşı-olgusal defter (cf motoru
üzerinden) — portföye, işlem defterine, stratejiye ve karneye ASLA dokunmaz."""
from __future__ import annotations
import pandas as pd

from . import config, store, strategy as strat, regime as regime_mod, indicators as ind
from . import guard, skills, obs, counterfactual as cf, loop
from . import broker as broker_mod
from .backtest import SECTORS
from .score import START_EQUITY
from .adapters import data as data_adapter

# C12: Y3 tavanlarının plan-tarafı girdisi (`notional`/`risk_dollars`) BOYUTLANDIRMA YASASINI ister.
# Yasa broker'ındır ve KOPYALANMAZ: `size_position` örnek durumuna hiç dokunmaz (yalnız
# argümanlarının fonksiyonudur), o yüzden tek bir ATIL broker örneği üzerinden çağrılır — bu örnek
# hiçbir emir taşımaz, hiçbir pozisyon tutmaz, hiçbir yere yazmaz.
_SIZE_FN = broker_mod.PaperBroker(START_EQUITY, 0.0, 0.0).size_position


def _plans_for_session(d, dstr, per, idx, params, by_regime, goal, version, eg: dict | None = None):
    """Bir seansın P2+P3 çıktısını üret: (plans, armed_ids, dormant_sigs, near_miss, regime).
    daily_cycle'ın 264-545 satırlarını yansıtır; mirror-busy/shadow-veto/explore-arming ATLANIR
    (bunlar SİLAHLANMAYI etkiler, cf TOPLAMAYI değil).

    `eg`: KAZANÇ-KAPISI SAYACI (2026-08-03, kardeş-PIT düzeltmesi). Verilirse yerinde doldurulur —
    dönüş beşlisi DEĞİŞMEZ (`tests/test_cf_backfill_v14.py` o biçime çakılı ve arity değişikliği
    ölçümle ilgisiz bir kırmızı üretirdi). Boş bırakılırsa sayaç tutulmaz, davranış aynıdır."""
    # PERFORMANS: canlı daily_cycle her seans 250 sembolü validate_bars'tan geçirir (seansta 1 kez ucuz);
    # ~1000 tarihi seansta bu O(250×bar×seans) = felç. cf SIFIR-yetkili olduğundan pahalı per-sembol veri
    # kapısı DÜŞÜRÜLÜR — güncellik denetimi (d in index) + tarama NaN korumaları bozuk barı zaten eler.
    # Yalnız endeks (SPY) kapısı korunur (ucuz, tek sembol): bozuksa seans atlanır (canlı gibi).
    idx_ok, _ = data_adapter.validate_bars(idx.loc[:d].reset_index(), "SPY")
    if not idx_ok:
        return [], set(), [], [], None
    quarantine = set()

    rj = regime_mod.build_regime_json(idx.loc[:d].reset_index(), params, dstr)
    srets = {t: float(dfp.loc[:d]["close"].iloc[-1] / dfp.loc[:d]["close"].iloc[-22] - 1.0)
             for t, dfp in per.items() if len(dfp.loc[:d]) > 22}
    rj["leading_sectors"] = regime_mod.sector_momentum(srets, SECTORS)
    eff = config.resolve_params(params, by_regime, rj["regime"])
    budget_ok = rj["exposure_budget_pct"] > 0
    explore_mode = not budget_ok

    # RS: güncellik denetimli (bu seansın barı olmayan sembol havuza girmez — canlı ile birebir)
    rets = {t: float(dfp.loc[:d]["close"].iloc[-1] / dfp.loc[:d]["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
            for t, dfp in per.items()
            if t not in quarantine and d in dfp.index and len(dfp.loc[:d]) > strat.RS_LOOKBACK + 1}
    rs_map = ind.rs_rating(rets)

    # gevşek gölge eşikleri (near-miss) — daily_cycle ile TEK KAYNAKTAN (strategy.relax_for_near_miss)
    rx = strat.relax_for_near_miss(eff)

    candidates, dormant_sigs, near_miss = [], [], []
    for t, dfp in per.items():
        if t in quarantine or d not in dfp.index:
            continue
        tail = dfp.loc[:d].reset_index(drop=True).tail(340)
        rsv = rs_map.get(t, 50)
        allsig = strat.scan_all(tail, eff, rsv, ticker=t)
        for su, s3 in strat.scan_all(tail, rx, rsv, ticker=t).items():
            if su in strat.ARMED_SETUPS and su not in allsig:
                near_miss.append((s3, loop._near_miss_blockers(s3, eff)))
        for s2 in allsig.values():
            if s2.setup not in strat.ARMED_SETUPS:
                dormant_sigs.append(s2)
                candidates.append({"date": dstr, "sector": SECTORS.get(t, "?"),
                                   "dormant_setup": True, **s2.as_row()})
        sig = next((allsig[su] for su in strat.ARMED_SETUPS if su in allsig), None)
        if sig:
            candidates.append({"date": dstr, "sector": SECTORS.get(t, "?"), **sig.as_row()})
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # P3: kapı (düz portföy → per-aday intrinsik verdict). mirror/shadow atlanır; kazanç karartması
    # bu motorda ÖLÇÜLEMEZ (aşağıdaki kardeş-PIT bloğu — PIT takvim yok, kapı KONUŞMAZ).
    plans, armed_ids = [], set()
    slots = int(goal["limits"]["max_open_positions"])
    # C12: Y3 alanları DÜZ kitapla da gönderilir. Kitap boş olduğu için `sector_notional` {} ve ısı
    # 0,0'dır — bu bir ölçüm boşluğu DEĞİL ölçülmüş gerçektir (masada gerçekten hiçbir şey yok);
    # None dönmek "bilmiyoruz" derdi. NAV simülasyonun başlangıç sermayesidir: payda olmadan
    # `sector_cap` her adaya "NAV ölçülemedi" soft bayrağı takar ve cf'in hükümlerini kirletirdi.
    # Portföy-BAĞIMSIZLIK beyanı (yukarıda) korunur: eklenen alanlar boş kitabın alanlarıdır.
    flat_pf = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0,
               "open_risk_r": 0.0, "max_corr": 0.0,
               **guard.y3_portfolio_inputs([], equity=START_EQUITY, size_fn=_SIZE_FN)}
    for c in candidates:
        pid = (f"P-{dstr}-{c['ticker']}-{c.get('setup', '')}" if c.get("dormant_setup")
               else f"P-{dstr}-{c['ticker']}")
        rps = c["entry_trigger"] - c["stop"]
        plan = {"id": pid, "date": dstr, "ticker": c["ticker"], "side": "long",
                "entry_trigger": c["entry_trigger"], "stop": c["stop"],
                "targets": [c["profit_target"]], "size_r": min(c["size_r"], goal["limits"]["max_position_r"]),
                "r_multiple_expected": round((c["profit_target"] - c["entry_trigger"]) / rps, 2) if rps > 0 else 0,
                "regime_at_plan": rj["regime"], "sector": c["sector"], "score": c["score"],
                "setup": c.get("setup", "breakout_vcp"), "dormant_setup": bool(c.get("dormant_setup")),
                "profit_target": c["profit_target"], "strategy_version": version,
                "skill_chain": [skills.screener_for(c.get("setup", "breakout_vcp")),
                                "position-sizer", "pre-trade-discipline-gate"]}
        # C12: plan şeması DEĞİŞMEZ — kapıya zenginleştirilmiş kopya gider (canlı/replay ile aynı
        # desen; `plans` listesine ve cf defterine yazılan sözlük `plan`ın kendisidir).
        _gate_plan = {**plan, **guard.y3_plan_inputs(plan, equity=START_EQUITY, size_fn=_SIZE_FN)}
        verdict, reasons = guard.classify_gate(_gate_plan, flat_pf, rj, goal, eff)
        # ---- KARDEŞ-PIT DÜZELTMESİ — `backtest.replay`in kararı 2'sinin
        # BİREBİR KARDEŞİ. Burada eskiden `earnings.in_blackout(c["ticker"], dstr)` vardı ve `dstr`
        # 2022→bugün aralığındaki TARİHSEL bir seanstı; `state/earnings.csv` ise PIT DEĞİL, bugünün
        # ~21 günlük İLERİ-PENCERE snapshot'ı (sembol başına 1,0 tarih; geçmiş çapa biriktirmiyor).
        # Yani bu satır "2023-03-14 kararına 2026-08-03 takvimini" uyguluyordu: cf defterinin karartma
        # etkisi UYGULANMIŞ GİBİ taşınıyor, gerçekte ise seansların ezici çoğunluğunda `in_blackout`
        # yapısal olarak False dönüyordu (ölçüldü: replay tarafında 390 planın 380'i, %97,4).
        # ARTIK: bugünün takvimini geçmiş bir karara uygulayan yol TAMAMEN KAPALI — ne veto, ne etiket.
        # NEDEN "DOĞRU TAKVİMLE" HESAPLAMIYORUZ: PIT kazanç takvimi bu depoda YOK; üretmeden veto
        # koymak, ölçülmemiş bir kapıyı ölçülmüş gibi göstermek olurdu (UYDURMA YASAĞI).
        # CANLI MOTOR ETKİLENMEZ: `loop.daily_cycle`ın karartma vetosu aynen durur (orada takvim
        # PIT'tir — bugünün kararı bugünün takvimiyle verilir) ve bu modülün canlı yolu YOKTUR.
        if eg is not None:
            eg["plan"] = eg.get("plan", 0) + 1
            eg["olculemedi_cf"] = eg.get("olculemedi_cf", 0) + 1
        plan["gate_verdict"], plan["gate_reasons"] = verdict, reasons
        plans.append(plan)
        # taken ≈ o gün silahlanacak olan: uyuyan yalnız keşif-GO; normal GO/REVIEW slot dahilinde
        if plan["dormant_setup"]:
            if verdict == "GO" and explore_mode:
                armed_ids.add(pid)
        elif explore_mode:
            if verdict == "GO":
                armed_ids.add(pid)
        elif verdict != "NO_GO" and len(armed_ids) < slots:
            armed_ids.add(pid)
    return plans, armed_ids, dormant_sigs, near_miss, rj


def run(start: str | None = None, end: str | None = None, progress_every: int = 50) -> dict:
    """Tarihi seansları sırayla işle; her seansta cf.collect + cf.advance. config.STATE'e (sandbox'ta
    sandbox state) yazar. Dönüş: {sessions, opened, resolved}."""
    strat_cfg = config.load_strategy()
    params = strat_cfg["params"]
    by_regime = strat_cfg.get("params_by_regime")
    version = int(strat_cfg.get("version", 1))
    goal = config.goal()
    time_stop = int(float(params.get("exit.time_stop_days", 15)))

    # AĞ YOK: dataset.load, end=bugün için önbelleği "bayat" sayıp 250 sembolü ağdan çekmeye çalışıyor
    # (corporate-action churn → asılma). Backfill'in TAZE veriye ihtiyacı yok; önbellek CSV'lerini
    # DOĞRUDAN okur (load_bars'ın yaptığı sanitize onarımıyla). Endeks = SPY'ın kendi barları.
    per = {}
    for t in data_adapter.REPLAY_UNIVERSE:
        cp = data_adapter._cache_path(t)
        if not cp.exists():
            continue
        try:
            df, _ = data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
            # BÜTÜNLÜK DEFTERİ (hayalet-round-2): çözülmemiş ölçek/kimlik kırılmasından
            # önceki dönem cf evreninden düşer — `component_ic` ile AYNI çağrı, aynı defter. cf
            # satırları geçmiş seansların KARŞI-OLGUSUdur; yanlış ölçekte bir geçmiş, olmamış bir
            # işlemin "ne olurdu"sunu üretir ve tablo o uydurmayı gerçek gibi taşır.
            df = data_adapter.measurement_bars(df, t)
            if df is not None and len(df) > 320:
                per[t] = df.set_index("date").sort_index()
        except Exception as e:
            # YASA 4: `continue` ticker'ı karşı-olgu evreninden SESSİZCE düşürür —
            # cf kapsaması küçülür, hiçbir hata görünmez ve "cf neden bu kadar az satır üretti?"
            # sorusu cevapsız kalır. Davranış aynı (atla), ama artık kim atlandı belli.
            obs.warn("cf_bars_unreadable", ticker=t, error=f"{type(e).__name__}: {e}")
            continue
    if "SPY" in per:
        idx = per["SPY"]
    else:                                                # SPY evren dışı → endeks barlarını ayrı oku
        cp = data_adapter._cache_path("SPY")
        idx = data_adapter.measurement_bars(
            data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), "SPY")[0],
            "SPY").set_index("date").sort_index()
    sessions = [d for d in idx.index]
    if start:
        sessions = [d for d in sessions if str(d.date()) >= start]
    if end:
        sessions = [d for d in sessions if str(d.date()) <= end]

    n_open = 0
    # KAZANÇ-KAPISI SAYACI (kardeş-PIT). YASA 6: üretilen kanıt TÜKETİLİR — bu sayaç
    # `out`a girer, `cf_backfill_done` olayına yazılır ve defteri okuyan her yer "bu tabloda karartma
    # etkisi SIFIRDIR, çünkü kapı hiç konuşmadı" bilgisini oradan görür. Sessiz sıfır değil, beyanlı.
    eg: dict[str, int] = {}
    for i, d in enumerate(sessions):
        dstr = str(d.date())
        try:
            cf.advance(per, d, dstr)                        # önce önceki günleri ilerlet/çöz
            plans, armed_ids, dormant, nmiss, rj = _plans_for_session(
                d, dstr, per, idx, params, by_regime, goal, version, eg)
            if rj is not None:
                # SÜRÜM DAMGASI: `version` bu fonksiyonun başında ZATEN okunuyordu
                # (`strat_cfg["version"]`) ama satıra basılmıyordu — bilgi elde, bir adım
                # ötede kayboluyordu. Damgasız defter "kanıt bugünün stratejisini yansıtıyor
                # mu?" sorusunu cevaplayamıyordu (2026-08-25: 7260/7260 damgasız).
                added = cf.collect(dstr, plans, armed_ids, dormant, time_stop, near_miss=nmiss,
                           regime=rj["regime"],   # tur 2: uyuyan/eşik-altı satırlar da rejim taşır
                           strategy_version=version)
                n_open += added
        except Exception as e:
            obs.warn("cf_backfill_session_failed", date=dstr, error=f"{type(e).__name__}: {e}")
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  {i + 1}/{len(sessions)} seans · {dstr} · açılan toplam {n_open}", flush=True)

    resolved = len(store.read_jsonl(cf.LEDGER))
    still_open = len(store.read_json(cf.OPEN_FILE, []))
    # BAR TABANI DAMGASI (component_ic ile AYNI gerekçe, YASA 6): `bars_integrity` defteri cf
    # evreninden DÖNEM düşürdüyse bu satır onu SAYIYLA söyler. Yazılmazsa "cf neden bu kadar az
    # satır üretti?" sorusu yine cevapsız kalırdı — bu dosyanın YASA 4 notunun aynı ailesi.
    out = {"sessions": len(sessions), "opened": n_open, "resolved": resolved,
           "still_open": still_open, "bars_integrity": data_adapter.integrity_report(),
           # kaç plan, kazanç-karartma kapısı KONUŞAMADAN karar aldı (bkz. kardeş-PIT bloğu).
           "earnings_gate": eg}
    obs.log("cf_backfill_done", **out)
    return out
