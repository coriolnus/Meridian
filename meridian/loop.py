"""loop.py — the live forward paper cycle. Runs once per trading day after the close: builds the
regime, manages open positions on the new bar, screens + plans + guards new entries, arms them for
the next session's open, and writes a heartbeat. Portfolio state persists in state/portfolio.json so
learning survives restarts. strategy.yaml is hot-reloaded on mtime change — no redeploy for a
parameter change (§4). Uses the SAME strategy.py / broker.py as the backtest, so live and simulated
behavior cannot diverge."""
from __future__ import annotations
import datetime as dt
import pandas as pd

from . import config, store, strategy as strat, regime as regime_mod, indicators as ind
from . import guard, health, skills, dataset, obs, earnings, rollback, ledgerstamp
from .adapters import data as data_adapter
from .backtest import SECTORS, _adv
from . import broker as BR                 # E1 giriş-icra yasası (olay adları + karar fonksiyonları)
from .broker import PaperBroker, derisk_mult, max_positions_at, bps_delta as _bps
from .score import START_EQUITY

PORTFOLIO = "portfolio.json"
# KEŞİF (mikro-sonda) bütçesi — rejim kilitlenmesini kırar: bütçe %0 rejimlerde kanıt birikmiyordu
# (chop: 3.5 yılda 8 işlem) → rejim-koşullu makine sonsuza dek aç kalıyordu. Sert tavanlar:
EXPLORE_MAX_R = 0.25       # keşif SONDASI başına risk tavanı (R)
EXPLORE_MAX_POS = 5        # öğrenme debisi (operatör, 2026-07-20 akşam): kâğıt modunda kanıt debisi öncelik
EXPLORE_TOTAL_R = 1.25     # 5 × 0.25R — toplam keşif riski hâlâ hesabın %1.25'i (kâğıt)
MIRROR_DRIFT_TOL = 0.005   # >0.5% gap between internal sim fill and actual Alpaca fill → mirror_drift alarm

# ---- E2: GİRİŞ İCRA / SLİPAJ DEFTERİ (WP-E, kart EXE-2026-001, 2026-07-31) --------------------
# NEDEN AYRI DEFTER: `trades.jsonl` KAPANMIŞ işlemi yazar; girişin İCRASI (hangi yasa, hangi limit,
# doldu mu, dolmadıysa neden, dolduysa resmî açılışa göre kaç bps) orada yeri olmayan ve çoğu zaman
# HİÇ KAPANMAYAN bir olgudur — kaçan bir giriş asla bir trade satırı doğurmaz, yani mevcut deftere
# yazılamazdı ve tam bu yüzden bugüne kadar ÖLÇÜLMÜYORDU. `broker_reconcile.json` ise anlık görüntü
# (tarihçe yok, üzerine yazılır); slipaj bir DAĞILIM sorusudur ve tek anlık görüntüyle sorulamaz.
# OKUYUCULAR (YASA 6 zinciri): analytics.entry_execution_summary → /api/diagnostics `icra` → pano;
# ayrıca E3 kalibratörü (analytics.pessimistic_band_update) ampirik bandı buradan üretir.
ENTRY_LEDGER = "entry_execution.jsonl"
ENTRY_LEDGER_CAP = 4000    # satır tavanı — defter büyür, sonsuza dek değil


def _entry_exec_write(row: dict) -> None:
    """E2 defterine tek satır. ASLA döngüyü bozmaz (ölçüm katmanı kararı bloklamaz), ama sessizce
    de kaybolmaz: yazım düşerse olay defterine uyarı düşer."""
    try:
        store.append_jsonl(ENTRY_LEDGER, {"ts": dt.datetime.now(dt.timezone.utc)
                                          .isoformat(timespec="seconds"), **row})
    except Exception as e:
        obs.warn("entry_exec_ledger_write_failed", error=f"{type(e).__name__}: {e}",
                 plan_id=row.get("plan_id"), ticker=row.get("ticker"))


def _reject_class(detail, veto=None, reachable=None) -> str:
    """Broker ret METNİNİ sınıfa indirger — özet yüzeyinde "ret dağılımı" ancak sınıflanabilir bir
    eksende anlamlıdır (ham metin sembol adı taşır, her satır tekil görünür). TANINMAYAN metin
    `diger` olur ve ham metin satırda KALIR: sınıflandırma bir özettir, kanıtın yerine geçmez."""
    if veto:
        return "gap_veto"
    if reachable is False:
        return "unreachable"
    s = str(detail or "").lower()
    if "stop price" in s and "current price" in s:
        return "stop_vs_current"        # E1'in kapattığı KÖK NEDEN — sayacı sıfıra inmeli
    if "insufficient" in s or "buying power" in s:
        return "buying_power"
    if "tradable" in s or "halted" in s or "inactive" in s:
        return "not_tradable"
    if "duplicate" in s or "client_order_id" in s:
        return "duplicate_coid"
    if "qty" in s or "quantity" in s:
        return "qty"
    if "wash" in s:
        return "wash_trade"
    if "limit price" in s or "limit_price" in s:
        return "limit_price"
    return "diger"


def _entry_exec_trim() -> None:
    """Tavanı aşan defteri en yeni ENTRY_LEDGER_CAP satıra indirir (döngü sonunda, ucuz)."""
    try:
        rows = store.read_jsonl(ENTRY_LEDGER)
        if len(rows) > ENTRY_LEDGER_CAP:
            store.write_jsonl(ENTRY_LEDGER, rows[-ENTRY_LEDGER_CAP:])
    except Exception as e:
        obs.warn("entry_exec_ledger_trim_failed", error=f"{type(e).__name__}: {e}")


UNIVERSE_MIN_COVERAGE = 0.90   # kararlar, evrenin en az bu oranının barı olan seansta alınır
UNIVERSE_LAG_MAX_D = 5         # bu kadar geriye bakılır; daha eskisi veri arızasıdır (uyarı)


class _MirrorUnreachable(Exception):
    """Ayna (Alpaca) ulaşılamıyor: gönderim atlanır, planlar SİLAHLI kalır — iç defter tek gerçek."""


def _universe_drift_check() -> None:
    """Elle bakımlı evren endeksten düşmüş isim taşıyor mu? 2026-07-21'de 7 ölü sembol ELLE
    bulunmuştu; artık bunu söyleyen bir mekanizma var (adapters.constituents denetimi, tur 3).
    Günde bir kez yeter — constituents.current() zaten günlük önbellekli. Asla döngüyü bozmaz."""
    try:
        from .adapters import constituents as _con
        rep = _con.universe_drift()
        store.write_json("universe_drift.json", {**rep, "date": dt.date.today().isoformat()})
        if rep.get("status") == "ok" and rep.get("n_stale"):
            obs.alarm("DATA_QUALITY",
                      f"evren sapması: {rep['n_stale']} sembol S&P 500'de yok — {', '.join(rep['stale'][:8])}",
                      n_stale=rep["n_stale"])
    except Exception as e:
        obs.warn("universe_drift_failed", error=f"{type(e).__name__}: {e}")


def _load_broker() -> tuple[PaperBroker, dict]:
    goal = config.goal()
    slip = float(goal.get("slippage_bps", 5))
    comm = float(goal.get("commission_per_share", 0.0))
    st = store.read_json(PORTFOLIO, None)
    b = PaperBroker(START_EQUITY, slip, comm)
    if st:
        b.cash = st["cash"]; b.realized_pnl = st["realized_pnl"]; b._id = st.get("last_id", 0)
        from .broker import Position
        for t, p in st.get("positions", {}).items():
            b.positions[t] = Position(**p)
    return b, (st or {"armed": [], "pending_exits": {}, "last_date": None, "day_start_equity": START_EQUITY})


_HOTSTATE_OFF_LOGGED: set = set()


def _hotstate_off_once(key: str, where: str, reader: str) -> None:
    """Kapatılmış sıcak-yazımın SÜREÇ BAŞINA BİR KEZ kaydı (sadeleştirme turu, 2026-07-30).

    Neden hiç kaydetmemek değil: sessizce kaldırılmış bir yazım, aylar sonra "Redis'te fiyat neden
    yok?" sorusunu kaynaksız bırakır. Neden her turda değil: statik bir olgu için günlük olay yazmak,
    obs defterini bilgi taşımayan satırlarla şişirir. Her restart'ta bir kez → durum güncel kalır,
    defter temiz kalır."""
    if key in _HOTSTATE_OFF_LOGGED:
        return
    _HOTSTATE_OFF_LOGGED.add(key)
    obs.log("hotstate_write_disabled", key=key, where=where, reader=reader,
            detail=f"yalnız-yazılır katman kapatıldı (2026-07-30): {reader} üretimde hiç çağrılmıyor; "
                   f"hotstate fonksiyonu SİLİNMEDİ, kanca yorumda — tüketici gelince tek satır")


def _save_broker(b: PaperBroker, meta: dict) -> None:
    from dataclasses import asdict
    st = {"cash": b.cash, "realized_pnl": b.realized_pnl, "last_id": b._id,
          "positions": {t: asdict(p) for t, p in b.positions.items()},
          "armed": meta.get("armed", []), "pending_exits": meta.get("pending_exits", {}),
          "last_date": meta.get("last_date"), "day_start_equity": meta.get("day_start_equity", START_EQUITY),
          # both survive restarts: alpaca_submitted is the double-submit dedup set (losing it re-fires
          # brackets after every restart — Alpaca's duplicate-client_order_id rejection was the only net);
          # broker_rejected is the failed-submission ledger the dashboard reads via broker_reconcile.
          "alpaca_submitted": meta.get("alpaca_submitted", []),
          "broker_rejected": meta.get("broker_rejected", []),
          # E1 (WP-E): silahlı planların icra kararı (limit/ATR/gap) — RESTART'I ATLATMALI. Yoksa
          # yeniden başlatma sonrası dolum yasası "ATR ölçülemedi"ye düşer ve aynı plan iki farklı
          # limitle iki motorda ayrışır (tam olarak bu turun kapattığı kusur).
          "entry_law": meta.get("entry_law", {}),
          # peak_equity MUST survive restarts/reloads: every cycle reloads meta from disk, so without
          # this the running peak collapsed to max(START_EQUITY, current) — drawdown always read ~0 and
          # the graded de-risk ramp + position throttle were PERMANENTLY inert (audit critical #10).
          "peak_equity": meta.get("peak_equity", START_EQUITY)}
    # AYNI KİLİT: Hermes'in görüş damgası da portfolio.json'a yazıyor (ayrı iş parçacığı) —
    # ikisi de store.file_lock(PORTFOLIO) altında olmalı, yoksa biri diğerinin defterini ezer.
    with store.file_lock(PORTFOLIO):
        store.write_json(PORTFOLIO, st)
    # SICAK KOPYA — DEVRE DIŞI (sadeleştirme turu, 2026-07-30). Bu satır pozisyonları `mrd:pos`a
    # yazıyordu ("intraday'de ms-latency erişim"). ÖLÇÜM: `hotstate.get_positions`ın PRODÜKSİYONDA
    # hiçbir çağıranı yok — yalnız testler okuyor. Yani katman YALNIZ-YAZILIRDI: her turda Redis'e
    # gidiliyor, kimse okumuyordu. Tüketici bağlamak pano/api tarafını ister (bu turun dokunma
    # yasağında), o yüzden karar KANITA göre verildi: bedava sadelik, yazımı kapat.
    #   GERİ AÇMA TEK SATIR: aşağıdaki iki satırın yorumunu kaldır. `hotstate.cache_positions`
    #   SİLİNMEDİ ve testleri duruyor — 4b/pano tüketicisi geldiği gün kanca hazır.
    # from . import hotstate
    # hotstate.cache_positions(st["positions"])
    _hotstate_off_once("mrd:pos", "_save_broker", "get_positions")


def _llm_veto_filter(meta: dict) -> None:
    """Kademe-3 (LLM danışman): YALNIZ terfili ajan (analytics.llm_promoted — yazılı kalibrasyon kuralı),
    YALNIZ 'REVIEW + karşı' planı DOLUMDAN düşürebilir. GO'ya dokunamaz, NO_GO'yu açamaz, boyut/çıkış
    yetkisi yok. AYNA TUTARLILIK YASASI: plan Alpaca'ya gönderildiyse önce ORADA iptal doğrulanır;
    doğrulanamazsa plan düşürülMEZ — iki defterin ayrışması vetodan büyük risktir."""
    from . import analytics as _an_llm
    if not _an_llm.llm_promoted():
        return
    kept_armed = []
    for pl in meta.get("armed", []):
        veto = pl.get("gate_verdict") == "REVIEW" and pl.get("llm_opinion") == "karşı"
        if not veto:
            kept_armed.append(pl); continue
        if pl["id"] in set(meta.get("alpaca_submitted", [])):
            from .adapters import alpaca as _alp_v
            ok_cancel = False
            try:
                for o in _alp_v.orders(status="open", limit=100, nested=True):
                    if o.get("client_order_id") == pl["id"] and float(o.get("filled_qty") or 0) <= 0:
                        ok_cancel = bool(_alp_v.cancel_order(o.get("id")).get("ok"))
                        break
            except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                ok_cancel = False
            if not ok_cancel:
                kept_armed.append(pl)
                obs.warn("llm_veto_kept_mirror", ticker=pl.get("ticker"),
                         detail="ayna iptali doğrulanamadı — tutarlılık için dolum sürüyor")
                continue
        obs.log("llm_veto_strip", ticker=pl.get("ticker"), plan_id=pl.get("id"),
                detail="terfili ajan vetosu: REVIEW + karşı → dolum düşürüldü")
        # KİLİTLİ oku-değiştir-yaz (B3, 2026-07-31): eskiden çıplak read+write idi ve AYNI
        # deftere Hermes'in görüş damgası (`store.update_jsonl`, kilitli) ile `merge_dated_jsonl`
        # de yazıyor. Kilit tek taraflıysa kilit yoktur: kaybeden yazar bütün araya girmiş
        # satırları eski kopyasıyla geri alırdı ve hiçbir yerde iz kalmazdı.
        def _veto_patch(rows, _pid=pl["id"]):
            hit = False
            for _pr in rows:
                if _pr.get("id") == _pid:
                    _pr["llm_veto"] = True
                    hit = True
            return hit

        store.update_jsonl("trade_plans.jsonl", _veto_patch)
    meta["armed"] = kept_armed


SCAN_DEBT_FILE = "scan_debt.json"
SCAN_DEBT_MAX_AGE_D = 7    # takvim günü; bu yaşta hâlâ bar yoksa borç olaylı düşer (ölü sembol şüphesi)
SCAN_DEBT_CAP = 300


def _scan_debt_add(ticker: str, dstr: str) -> None:
    """Güncellik denetiminde elenen (seans barı henüz yayınlanmamış) sembol borç defterine yazılır —
    bar gelince kaçan kesişim karşı-olgusala işlenir. Kayıp artık görünmez değil, ölçülü."""
    debts = store.read_json(SCAN_DEBT_FILE, [])
    if any(r["ticker"] == ticker and r["date"] == dstr for r in debts):
        return
    if len(debts) >= SCAN_DEBT_CAP:
        return
    debts.append({"ticker": ticker, "date": dstr})
    store.write_json(SCAN_DEBT_FILE, debts)


def _scan_debt_collect(per: dict, d, eff: dict) -> dict:
    """Barı SONRADAN gelen borçlar için kaçan seansı o günkü kuyruk + o günkü RS ile değerlendir.
    Dönüş: {seans: [(sinyal, ["geç_bar"]), ...]} — yalnız karşı-olgusal deftere gider (sıfır yetki)."""
    import datetime as _dt2
    debts = store.read_json(SCAN_DEBT_FILE, [])
    if not debts:
        return {}
    from . import indicators as ind2
    keep, out = [], {}
    rs_cache: dict = {}
    for row in debts:
        t, ds = row["ticker"], row["date"]
        df_t = per.get(t)
        target = pd.Timestamp(ds)
        if df_t is None:
            continue                                     # evrenden çıkmış — borç düşer
        if target not in df_t.index:
            age = (d.date() - _dt2.date.fromisoformat(ds)).days
            if age > SCAN_DEBT_MAX_AGE_D:
                obs.warn("scan_debt_expired", ticker=t, date=ds,
                         detail=f"{age} gündür bar yok — ölü sembol şüphesi, borç düşürüldü")
            else:
                keep.append(row)
            continue
        if ds not in rs_cache:                           # RS o GÜNÜN evren kesitiyle — bugünküyle değil
            rets = {t2: float(df2.loc[:target]["close"].iloc[-1]
                              / df2.loc[:target]["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
                    for t2, df2 in per.items()
                    if target in df2.index and len(df2.loc[:target]) > strat.RS_LOOKBACK + 1}
            rs_cache[ds] = ind2.rs_rating(rets)
        tail = df_t.loc[:target].reset_index().tail(340)
        for su, sig in strat.scan_all(tail, eff, rs_cache[ds].get(t, 50), ticker=t).items():
            if su in strat.ARMED_SETUPS:
                out.setdefault(ds, []).append((sig, ["geç_bar"]))
        obs.log("scan_debt_resolved", ticker=t, date=ds, found=len(out.get(ds, [])))
    store.write_json(SCAN_DEBT_FILE, keep)
    return out


def _near_miss_blockers(sig, eff: dict) -> list:
    """Gevşek gölge taramasında doğan ama SIKI eşiklerde ölen sinyal için ölüm nedenleri.
    vr/prox EntrySignal alanı değil — notes içinden okunur (best-effort; bulunamazsa "diğer")."""
    import re as _re
    out = []
    if sig.rs_rating < eff.get("entry.rs_rating_min", 70):
        out.append("rs")
    if sig.score < eff.get("entry.min_score", 60):
        out.append("skor")
    m = _re.search(r"vr=([\d.]+)", sig.notes or "")
    if m and float(m.group(1)) < eff.get("entry.min_volume_ratio", 1.5):
        out.append("hacim")
    m = _re.search(r"prox=([\d.-]+)%", sig.notes or "")
    if m and float(m.group(1)) > eff.get("entry.pivot_proximity_pct", 2.0):
        out.append("uzamış")
    return out or ["diğer"]


def _carry_armed_without_bar(armed: list, has_bar) -> tuple[list, list]:
    """P4 dolum ayrıştırıcısı — GS-1140 kök nedeni (canlıda 2026-07-15): dolum anında bar henüz
    YAYINLANMAMIŞSA plan sessizce buharlaşıyordu, hiçbir olay yazılmadan. Tek-seans yasası "bayat
    sinyalle girme" içindir; YAYINLANMAMIŞ seans görülmemiş seanstır. Bar'ı olan planlar dolum
    adayı; olmayanlar BİR seans taşınır (olaylı), ikinci seansta da bar yoksa olaylı düşer."""
    fillable, carried = [], []
    for plan in armed:
        t = plan.get("ticker")
        if has_bar(t):
            fillable.append(plan)
            continue
        c2 = int(plan.get("carried") or 0)
        if c2 < 1:
            plan["carried"] = c2 + 1
            carried.append(plan)
            obs.log("armed_no_bar_carried", ticker=t, plan_id=plan.get("id"),
                    detail="bar yayınlanmadı — plan bir seans taşındı")
        else:
            obs.warn("armed_expired_no_bar", ticker=t, plan_id=plan.get("id"),
                     detail="ikinci seansta da bar yok — plan düşürüldü (kayıtlı)")
    return fillable, carried


def daily_cycle(bars: dict, index: pd.DataFrame, on_date: str | None = None) -> dict:
    """Process the latest closed trading day. Returns a summary dict."""
    # goal/bounds lru_cache'i uzun ömürlü süreçte dosyayı DONDURUYORDU: operatörün goal.yaml'da
    # elle değiştirdiği limit, sunucu yeniden başlatılana dek hiç görülmezdi (denetim turu 10).
    config.reload_config()
    goal = config.goal()
    limits = goal["limits"]
    strat_cfg = config.load_strategy()           # hot-reloaded each cycle
    params = strat_cfg["params"]
    version = int(strat_cfg.get("version", 1))
    skills.reconcile_enablement()                # pick up any key added/removed since the last cycle

    idx = index.set_index("date").sort_index()
    per = {t: df.set_index("date").sort_index() for t, df in bars.items()}
    all_dates = list(idx.index)
    if on_date:
        all_dates = [d for d in all_dates if str(d.date()) <= on_date]
    if not all_dates:
        return {"error": "no dates"}
    d = all_dates[-1]
    # ---- EVREN BÜTÜNLÜĞÜ KAPISI (2026-07-21, canlı kanıtla bulundu) ----
    # Seans tarihini ENDEKSİN son barı belirliyordu. Ama ücretsiz kaynaklar sembol bazında farklı
    # hızda güncelleniyor: canlıda SPY 07-21 barına sahipken 250 sembolün yalnız 46'sı sahipti.
    # Tazelik koruması kalan 204'ü "bayat kuyruk" diye ATLIYOR — yani motor evrenin %18'ini tarayıp
    # "aday: 0" yazıyordu (son 5 seansın beşinde de öyle oldu). Üstelik o %18 rastgele değil,
    # HANGİ KAYNAĞIN önce güncellediğine bağlı: kapı 250 sembollük evrende ölçüyor, canlı taraf
    # yanlı bir alt kümede karar veriyor — kapı≠canlı ayrışmasının en kötü biçimi.
    # Çözüm: evrenin ÇOĞUNLUĞUNUN barı olan EN SON seansı işle. Gecikmeli ücretsiz veriyle bir gün
    # geride olmak dürüsttür; %18'lik yanlı bir kesitte karar vermek değildir.
    _n_uni, _deferred_for_coverage = max(1, len(per)), False
    for _cand in reversed(all_dates[-UNIVERSE_LAG_MAX_D:] or [d]):
        _cov = sum(1 for _df in per.values() if _cand in _df.index)
        if _cov / _n_uni >= UNIVERSE_MIN_COVERAGE:
            if _cand != d:
                _deferred_for_coverage = True
                obs.log("session_deferred_for_coverage", index_session=str(d.date()),
                        chosen=str(_cand.date()), coverage=round(_cov / _n_uni, 3),
                        detail="endeksin son barı evrenin çoğunda yok — kararlar tam evrende alınır")
            d = _cand
            break
    else:
        _cov0 = sum(1 for _df in per.values() if all_dates[-1] in _df.index)
        obs.warn("universe_coverage_low", date=str(all_dates[-1].date()),
                 coverage=round(_cov0 / _n_uni, 3), min_required=UNIVERSE_MIN_COVERAGE,
                 detail="hiçbir yakın seansta evren kapsaması yeterli değil — endeksin seansıyla devam")
    dstr = str(d.date())

    # KAPSAMA ERTELEMESİ ile MONOTONLUK BEKÇİSİ çarpışması (2026-07-21): kitap, düzeltme öncesi
    # %18 kapsamalı bir seansta ilerletilmiş olabilir. O zaman tam-kapsamalı seans kitabın GERİSİNDE
    # kalır ve bekçi haklı olarak reddeder — ama sebep "bayat/yedek kaynak" DEĞİL, "evren henüz
    # yetişmedi"dir. İkisini aynı alarmla anlatmak teşhisi bozar: bu bir BEKLEME, bir arıza değil.
    _book_at0 = store.read_json("portfolio.json", {}).get("last_date")
    if _deferred_for_coverage and _book_at0 and dstr < str(_book_at0):
        obs.log("waiting_for_universe", chosen=dstr, book_at=str(_book_at0),
                index_session=str(all_dates[-1].date()),
                detail="tam kapsamalı seans kitabın gerisinde — barlar yetişince o seans işlenecek")
        return {"status": "waiting_for_universe", "date": dstr, "book_at": str(_book_at0),
                "index_session": str(all_dates[-1].date())}

    # ---- monotonluk bekçisi: kitap asla GERİYE işlemez (GS'yi öldüren halka, 2026-07-15 10:29) ----
    # Bayat yedek kaynak endeksi geriletmişti; döngü sorgulamadan 07-13'ü işleyip kitabı geri sardı ve
    # silahlı planı geçmiş bir seansta yaktı. İşlenecek seans kitabın son tarihinden ESKİYSE reddet
    # (eşit güne izin var: re-seed sonu + elle buton aynı günü yineleyebilir — mevcut davranış).
    _book_at = store.read_json("portfolio.json", {}).get("last_date")
    if _book_at and dstr < str(_book_at):
        obs.warn("regressive_session_refused", date=dstr, book_at=str(_book_at),
                 detail="endeks kitabın gerisinde — bayat/yedek kaynak şüphesi; kitap geri sarılmaz")
        return {"status": "refused_regressive", "date": dstr, "book_at": str(_book_at)}

    # ---- data-quality gate: bad bars must never drive trades (Hard Rule 7) ----
    idx_ok, idx_issues = data_adapter.validate_bars(idx.loc[:d].reset_index(), "SPY")
    tick_bad = []
    for t, dfp in per.items():
        ok, iss = data_adapter.validate_bars(dfp.loc[:d].reset_index(), t)
        if not ok:
            tick_bad.append(t)
    data_bad = (not idx_ok) or (len(tick_bad) > len(per) * 0.25)
    # öneri #5b: bağımsız kaynak AYNI seans kapanışında >%1.5 sapma raporladıysa bar güvenilmez —
    # gecikme/kaynak-yok durumları ('source_lagging', 'fetch_failed') ASLA halt sebebi değildir.
    _xc = store.read_json("index_crosscheck.json", {})
    xc_bad = (_xc.get("date") == dstr and _xc.get("status") == "diverged")
    if xc_bad:
        data_bad = True
        obs.alarm(obs.ALARM_DATA_QUALITY, f"endeks çapraz-doğrulama sapması: {_xc.get('divergence')}",
                  date=dstr, primary=_xc.get("primary_close"), cboe=_xc.get("cboe_close"))
    store.write_json("data_quality.json", {"date": dstr, "index_ok": idx_ok,
                     "index_issues": idx_issues, "tickers_failed": tick_bad,
                     "universe": len(per), "crosscheck": _xc.get("status"),
                     "data_halt": data_bad})
    if data_bad:
        obs.alarm(obs.ALARM_DATA_QUALITY, f"veri kalitesi kapısı: index_ok={idx_ok}, {len(tick_bad)} hisse başarısız",
                  date=dstr, index_ok=idx_ok, tickers_failed=tick_bad[:10])

    b, meta = _load_broker()
    if meta.get("last_date") == dstr:
        # already processed this bar; just refresh heartbeat.
        # REJİM DE TAZELENİR (2026-07-22, sahiplik dedektörü yakaladı): bu kısa yol rejimi ve
        # bütçeyi damgalamıyordu. Nabız çok yazarlı olduğu için alanlar bir kez düştüğünde HUD
        # "rejim yok / bütçe yok" gösteriyor ve bir daha kendiliğinden dolmuyordu — seans zaten
        # işlenmişse rejim BİLİNMİYOR değildir, diskte durur.
        _rg = store.read_json("regime.json", {}) or {}
        health.write_heartbeat(version=version, open_positions=len(b.positions),
                               equity=round(b.equity(_marks(per, d)), 2), last_bar=dstr,
                               regime=_rg.get("regime"),
                               exposure_budget_pct=_rg.get("exposure_budget_pct"),
                               note="bar already processed")
        return {"status": "noop", "date": dstr}

    marks = _marks(per, d)
    # OPEN-phase risk decisions (breaker, de-risk, sizing) mark at D's OPEN — the close isn't known at
    # the open (audit #1: close-marks here let the morning decisions see the afternoon's move).
    marks_open = {t: per[t].loc[d, "open"] for t in b.positions if t in per and d in per[t].index}
    day_start_equity = meta.get("day_start_equity", b.equity(marks_open))

    # ---- 1. OPEN(D): pending exits + armed entries from the prior cycle ----
    for t, reason in list(meta.get("pending_exits", {}).items()):
        if t in b.positions and t in per and d in per[t].index:
            b.close_position(t, per[t].loc[d, "open"], reason, dstr)
            _persist_trade(b.closed[-1])
    meta["pending_exits"] = {}

    halted = health.halted()
    day_pnl_pct = (b.equity(marks_open) - day_start_equity) / day_start_equity if day_start_equity else 0.0
    breaker = health.circuit_breaker_tripped(day_pnl_pct, goal)
    if breaker:
        obs.alarm(obs.ALARM_CIRCUIT_BREAKER, f"günlük kayıp devre kesici: {day_pnl_pct:.2%}",
                  date=dstr, day_pnl_pct=round(day_pnl_pct, 4), limit_pct=goal["limits"]["max_daily_loss_pct"])
        try:
            from . import notify
            notify.breaker(day_pnl_pct)
        except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
            pass
    eq_now = b.equity(marks_open)
    meta["peak_equity"] = max(meta.get("peak_equity", START_EQUITY), eq_now)
    size_mult = derisk_mult(eq_now, meta["peak_equity"])   # graded de-risk on running drawdown
    eff_max_open = max_positions_at(eq_now, meta["peak_equity"], limits["max_open_positions"])  # + throttle
    with skills.pipeline_run("P4_EXECUTE", artifact="state/trades.jsonl"):   # executions must be auditable (#39)
        try:
            _llm_veto_filter(meta)   # Kademe-3: yalnız TERFİLİ ajanın dar vetosu (fonksiyona bak)
        except Exception as e:
            obs.warn("llm_veto_layer_failed", error=f"{type(e).__name__}: {e}")
        carried = []
        if not halted and not breaker and not data_bad and size_mult > 0:
            fillable, carried = _carry_armed_without_bar(
                meta.get("armed", []), lambda t: t in per and d in per[t].index)
            _law_tbl = meta.get("entry_law") or {}
            for plan in fillable:
                t = plan["ticker"]
                if len(b.positions) < eff_max_open and t not in b.positions:
                    # E1: İCRA GİRDİLERİ PLANDAN DEĞİL YAN TABLODAN. `entry_law` sözlüğü silahlanma
                    # anında (sinyal barı kapanışı) yazılır — as-of ihlali yok, plan DEFTERİ şeması
                    # da iki motorda aynı kalır (pivot ile aynı desen, bkz. broker.fill_entry).
                    _lw = _law_tbl.get(plan.get("id")) or {}
                    _open = float(per[t].loc[d, "open"])
                    _rej: dict = {}
                    _pos = b.fill_entry(plan, _open, dstr, eq_now, size_mult=size_mult,
                                        adv=_adv(per[t], d), atr=_lw.get("atr"),
                                        gap_at_submit=_lw.get("gap_at_submit"), reject_out=_rej)
                    _base = {"date": dstr, "plan_id": plan.get("id"), "ticker": t, "motor": "ic",
                             "entry_trigger": plan.get("entry_trigger"), "limit": _lw.get("limit"),
                             "atr": _lw.get("atr"), "law": _lw.get("law"),
                             "gap_at_submit": _lw.get("gap_at_submit"),
                             "resmi_acilis": round(_open, 4)}
                    if _pos is not None:
                        _entry_exec_write({**_base, "karar": "fill", "fill": round(_pos.entry, 4),
                                           "qty": _pos.qty,
                                           "fill_vs_resmi_acilis_bps": _bps(_pos.entry, _open),
                                           "fill_vs_limit_bps": _bps(_pos.entry, _lw.get("limit"))})
                    else:
                        _reason = _rej.get("reason") or "bilinmiyor"
                        _entry_exec_write({**_base, "karar": _reason, "fill": None,
                                           "fill_vs_resmi_acilis_bps": None,
                                           "fill_vs_limit_bps": None,
                                           "red_detay": {k: v for k, v in _rej.items()
                                                         if k not in ("reason", "ticker", "plan_id")}})
                        # KAÇAN İŞLEM ÖLÇÜLÜR, YUTULMAZ. Karşı-olgusal defter bu planın kaydını
                        # P3'te ZATEN açtı (counterfactual.collect her planı açar) — yani "girseydik
                        # ne olurdu?" sorusunun cevabı aynı `plan_id` ile orada birikiyor. Buradaki
                        # olay o kaydın İCRA sebebini adlandırır; ikisi plan_id ile birleşir.
                        if _reason in (BR.EV_MISSED_LIMIT, BR.EV_GAP_VETO):
                            obs.warn(_reason, ticker=t, plan_id=plan.get("id"),
                                     entry_trigger=plan.get("entry_trigger"),
                                     limit=_lw.get("limit"), open=round(_open, 4),
                                     asim_bps=_rej.get("asim_bps"),
                                     detail="E1 giriş yasası: dolum yazılmadı — cf defteri aynı "
                                            "plan_id ile kaçan işlemin sonucunu ölçmeye devam eder")
        meta["armed"] = carried

    # ---- 2. INTRADAY(D): touch exits ----
    # regime-resolved params for intraday consumers: at this point P1 hasn't recomputed yet, so the
    # regime known intraday is the PREVIOUS session's (regime.json on disk) — same semantics as the
    # backtest's prev_eff. Flat `params` here silently ignored exit.scale_out_*@regime overrides.
    prev_regime = store.read_json("regime.json", {}).get("regime", "any")
    eff_intraday = config.resolve_params(params, strat_cfg.get("params_by_regime"), prev_regime)
    for t in list(b.positions.keys()):
        if t in per and d in per[t].index:
            bar = per[t].loc[d]
            _pos = b.positions[t]                       # öneri #2: MFE/MAE su işaretleri her seans güncellenir
            _pos.hi_water = max(_pos.hi_water, float(bar["high"]))
            _pos.lo_water = min(_pos.lo_water or float(bar["low"]), float(bar["low"]))
            b.scale_out(b.positions[t], {"high": bar["high"], "low": bar["low"], "open": bar["open"]},
                        eff_intraday)   # #8 bank partial before full exit (stop-first conservatism inside)
            ex = b._touch_exit(b.positions[t], {"open": bar["open"], "high": bar["high"], "low": bar["low"]})
            if ex:
                b.close_position(t, ex[0], ex[1], dstr); _persist_trade(b.closed[-1])
            else:
                b.positions[t].bars_held += 1

    try:                                   # öneri #1: karşı-olgusal defter ilerler — dönüş görmezden gelinir,
        from . import counterfactual, watchdog as _wd   # hiçbir karar bu deftere bakmaz (sıfır yetki)
        counterfactual.advance(per, d, dstr)
        _wd.beat("cf_advance")
    except Exception as e:
        obs.warn("cf_advance_failed", error=f"{type(e).__name__}: {e}")

    # ---- 3. CLOSE(D): P1 regime, manage trails, P2 screen, P3 plan+guard, arm ----
    with skills.pipeline_run("P1_REGIME", artifact="state/regime.json"):
        rj = regime_mod.build_regime_json(idx.loc[:d].reset_index(), params, dstr)
        srets = {t: float(dfp.loc[:d]["close"].iloc[-1] / dfp.loc[:d]["close"].iloc[-22] - 1.0)
                 for t, dfp in per.items() if len(dfp.loc[:d]) > 22}
        rj["leading_sectors"] = regime_mod.sector_momentum(srets, SECTORS)
        store.write_json("regime.json", rj)
    regime_ok = rj["regime"] in ("trend_up", "chop") and rj["exposure_budget_pct"] > 0
    eff = config.resolve_params(params, strat_cfg.get("params_by_regime"), rj["regime"])  # regime-conditional

    for t in list(b.positions.keys()):
        if t in per and d in per[t].index:
            pos = b.positions[t]
            df_t = per[t].loc[:d].reset_index()
            pos_regime_ok = (rj["regime"] in ("trend_up", "chop")) if getattr(pos, "exploration", False) else regime_ok
            dec = strat.manage_position(df_t, {"entry": pos.entry, "stop": pos.stop,
                    "trail_stop": pos.trail_stop, "r_per_share": pos.r_per_share},
                    eff, pos.bars_held, pos_regime_ok)
            pos.trail_stop = dec.trail_stop
            if dec.exit_now:
                meta["pending_exits"][t] = dec.exit_reason

    candidates, plans, dormant_sigs, explore_pool = [], [], [], []
    near_miss_sigs = []
    explore_mode = (not halted and not data_bad and rj["exposure_budget_pct"] <= 0)
    if not halted and not data_bad and (rj["exposure_budget_pct"] > 0 or explore_mode) \
            and len(b.positions) < limits["max_open_positions"]:
        with skills.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
            # Faz 0 KARANTİNA: validate_bars'ın 'hard' düşürdüğü ticker'lar bugüne dek yalnız
            # LİSTELENİYORDU (%25 eşiği aşılmadıkça) — bozuk barlı tek hisse aday üretebiliyordu.
            # Artık taramadan ve RS havuzundan dışlanır; mevcut pozisyon yönetimi etkilenmez.
            _quarantine = set(tick_bad)
            rets = {}
            for t, df_t in per.items():
                if t in _quarantine or d not in df_t.index:
                    continue
                sub = df_t.loc[:d]
                if len(sub) > strat.RS_LOOKBACK + 1:
                    rets[t] = float(sub["close"].iloc[-1] / sub["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
            rs_map = ind.rs_rating(rets)
            # darboğaz turu (2026-07-20): huni ölçümü, aday kuraklığında ölümlerin ezici kısmının
            # kırılım-SONRASI eşiklerde (hacim×1.5, RS 70) olduğunu gösterdi. Gevşek bir GÖLGE taraması
            # eşiğin hemen altında ölenleri karşı-olgusal deftere yazar ki "hangi eşik masada para
            # bırakıyor?" ÖLÇÜLSÜN. Sıfır yetki: karar/kapı bu satırları asla okumaz; eşik değişikliği
            # ancak kanıt biriktikten sonra OOS kapısından geçerek gelebilir.
            _rx = strat.relax_for_near_miss(eff)             # TEK KAYNAK (strategy.py) — cf_backfill ile aynı
            late_by_date = _scan_debt_collect(per, d, eff)   # barı sonradan gelenlerin kaçan kesişimleri
            for t, df_t in per.items():
                if t in b.positions or t in _quarantine:
                    continue
                if d not in df_t.index:                      # güncellik: bu seansın barı henüz yok →
                    _cut = df_t.loc[:d]                      # bayat kuyrukla taranMAZ (GS-1140 sınıfı
                    if len(_cut) and (d.date() - _cut.index[-1].date()).days <= SCAN_DEBT_MAX_AGE_D:
                        _scan_debt_add(t, dstr)              # taze gecikme → borç; kadim kuyruk → sessiz geç
                    continue
                _tail = _scan_tail(df_t, d)
                _all = strat.scan_all(_tail, eff, rs_map.get(t, 50), ticker=t)
                for _su, _s3 in strat.scan_all(_tail, _rx, rs_map.get(t, 50), ticker=t).items():
                    if _su in strat.ARMED_SETUPS and _su not in _all:
                        near_miss_sigs.append((_s3, _near_miss_blockers(_s3, eff)))
                for _s2 in _all.values():              # öneri #1: uyuyan kurulum ateşlemeleri karşı-olgusala
                    if _s2.setup not in strat.ARMED_SETUPS:
                        dormant_sigs.append(_s2)
                        # operatör öğrenme-modu (2026-07-20): uyuyan kurulumun ateşlemesi ADAY da olur —
                        # kapıdan geçer, ama YALNIZ keşif sondası olarak (0.25R) silahlanabilir. Gerçek-R
                        # kanıtı yalnız cf simülasyonundan değil küçük gerçek işlemlerden de birikir;
                        # tam silahlanma kararı yine haftalık değerlendirme + kapı ölçümünündür.
                        row2 = {"date": dstr, "source_skill": skills.screener_for(_s2.setup),
                                "sector": SECTORS.get(t, "?"), "dormant_setup": True, **_s2.as_row()}
                        candidates.append(row2)
                sig = next((_all[su] for su in strat.ARMED_SETUPS if su in _all), None)
                if sig:
                    row = {"date": dstr, "source_skill": skills.screener_for(sig.setup),   # the screener that actually fired
                           "sector": SECTORS.get(t, "?"), **sig.as_row()}
                    candidates.append(row)
            candidates.sort(key=lambda c: c["score"], reverse=True)
            store.merge_dated_jsonl("candidates.jsonl", dstr, candidates)

        from .shadow_model import ShadowTradeOutcomeModel
        try:
            _shadow = ShadowTradeOutcomeModel.load()
        except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            _shadow = None
        # aynadaki meşgul semboller (canlı emir + motor yetimi) — yalnız alpaca_paper modunda dolu;
        # iç-broker modunda boş küme = davranış değişmez.
        _rc_snap = store.read_json("broker_reconcile.json", {}) if config.BROKER == "alpaca_paper" else {}
        _mirror_busy = set(_rc_snap.get("alive_order_syms") or []) | \
                       set((_rc_snap.get("positions") or {}).get("engine_orphans") or [])
        if config.BROKER == "alpaca_paper":
            try:                                     # olay-güdümlü katman: ANLIK bekleyenler (websocket)
                from .mirror_stream import pending_symbols_snapshot
                _mirror_busy |= pending_symbols_snapshot()
            except Exception as e:
                # YASA 4 (2026-07-21): bu düşerse _mirror_busy EKSİK kalır ve aynada zaten bekleyen
                # bir sembole İKİNCİ emir gidebilir. Sessizken tek belirtisi "bir gün fazladan bir
                # emir" olurdu — yani hata değil, miktar değişimi.
                obs.warn("mirror_pending_snapshot_failed", error=f"{type(e).__name__}: {e}",
                         detail="meşgul sembol kümesi disk anlık görüntüsüyle sınırlı")
        with skills.pipeline_run("P3_PLAN", artifact="state/trade_plans.jsonl"):
            sector_ct = {}
            for t in b.positions:
                sector_ct[SECTORS.get(t, "?")] = sector_ct.get(SECTORS.get(t, "?"), 0) + 1
            slots = limits["max_open_positions"] - len(b.positions)
            _plan_law: dict = {}     # plan_id → E1 icra kararı (aşağıda silahlananlar için saklanır)
            others_rets = [ind.returns_tail(per[o].loc[:d, "close"]) for o in b.positions if o in per]  # once/day
            for c in candidates:
                portfolio = {"open_positions": len(b.positions) + len(meta["armed"]),
                             # 0.0 at ARM time — identical to the backtest (backtest.py "breaker enforced
                             # at fill, not at arm"): the live loop passing the real day P&L here NO_GO'd
                             # candidates the walk-forward would have armed on the same bars, silently
                             # diverging live from simulated behavior (audit #15). The breaker still
                             # blocks the FILL next open in both engines.
                             "sector_counts": sector_ct, "day_pnl_pct": 0.0,
                             "open_risk_r": sum(p.size_r for p in b.positions.values())
                                            + sum(a["size_r"] for a in meta["armed"]),
                             "max_corr": ind.corr_max(per[c["ticker"]].loc[:d, "close"], others_rets)}
                _pid = (f"P-{dstr}-{c['ticker']}-{c.get('setup','')}" if c.get("dormant_setup")
                        else f"P-{dstr}-{c['ticker']}")   # uyuyan: kurulum ekli kimlik (çakışma + ayrışma)
                plan = {"id": _pid, "date": dstr, "ticker": c["ticker"], "side": "long",
                        "entry_trigger": c["entry_trigger"], "stop": c["stop"],
                        "targets": [c["profit_target"]], "size_r": min(c["size_r"], limits["max_position_r"]),
                        "r_multiple_expected": round((c["profit_target"] - c["entry_trigger"]) / c["r_per_share"], 2),
                        "regime_at_plan": rj["regime"], "sector": c["sector"], "score": c["score"],
                        "setup": c.get("setup", "breakout_vcp"),
                        "dormant_setup": bool(c.get("dormant_setup")),
                        "profit_target": c["profit_target"], "strategy_version": version,
                        "skill_chain": [skills.screener_for(c.get("setup", "breakout_vcp")), "position-sizer", "pre-trade-discipline-gate"]}
                _checks = []                            # Faz 3 (5b): yapılandırılmış karar ağacı
                verdict, greasons = guard.classify_gate(plan, portfolio, rj, goal, eff, detail_out=_checks)
                _bl = earnings.in_blackout(c["ticker"], dstr)
                # DOĞRULANDI mı yoksa VERİ YOK mu? İkisi de "passed" görünüyordu; canlıda evrenin
                # %28'inde (250'nin 69'u) takvim yok, yani guard o isimlerde sessizce kapalı. Plan
                # kaydı artık bunu taşıyor (denetim turu 11).
                _ek = earnings.known(c["ticker"])
                _checks.append({"check": "earnings_blackout", "passed": not _bl, "severity": "hard",
                                "value": c["ticker"], "threshold": None,
                                "coverage": "known" if _ek else "no_calendar_data",
                                "note": ("kazanç öncesi karartma (earnings blackout)" if _bl
                                         else (None if _ek else "kazanç takvimi YOK — kontrol edilemedi"))})
                if verdict != "NO_GO" and _bl:
                    verdict = "NO_GO"; greasons = list(greasons) + ["kazanç öncesi karartma (earnings blackout)"]
                # SENKRON KORUMASI (v3 kriter-1): aynada bu hisse için hâlâ CANLI bir emir ya da motor
                # yetimi pozisyon varken YENİ karar üretilmez — çifte maruziyet/karışık defter riski.
                # Kaynak: son uzlaştırmanın anlık görüntüsü (her döngü sonunda tazelenir).
                _mb = c["ticker"] in _mirror_busy
                _checks.append({"check": "mirror_busy", "passed": not _mb, "severity": "hard",
                                "value": c["ticker"], "threshold": None,
                                "note": "aynada bekleyen emir/yetim pozisyon var" if _mb else None})
                if verdict != "NO_GO" and _mb:
                    verdict = "NO_GO"; greasons = list(greasons) + ["aynada bekleyen emir/yetim pozisyon var"]
                plan["gate_verdict"], plan["gate_reasons"] = verdict, greasons
                plan["gate_checks"] = _checks           # panodaki karar-ağacı tablosu buradan okur
                try:                                   # v3 gölge kanıtı — kapı kararına dokunmaz
                    pw = _shadow.predict_proba(plan) if _shadow else None
                    if pw is not None:
                        plan["p_win_shadow"] = pw
                        # TERFİLİ modelin TEK yetkisi (öneri #3): REVIEW + çok düşük P(kazanç) → NO_GO.
                        # GO ve NO_GO kararlarına hiçbir koşulda dokunmaz; terfi kriteri shadow_model'de
                        # yazılı (canlı Brier taban-oranı yenmeden bu blok hiç çalışmaz).
                        from .shadow_model import ShadowTradeOutcomeModel as _SMv
                        _sv = verdict == "REVIEW" and pw < _SMv.REVIEW_VETO_P and _SMv.is_promoted()
                        _checks.append({"check": "shadow_veto", "passed": not _sv, "severity": "hard",
                                        "value": pw, "threshold": f">={_SMv.REVIEW_VETO_P}",
                                        "note": "gölge model (terfili) vetosu" if _sv else None})
                        if _sv:
                            verdict = "NO_GO"
                            greasons = list(greasons) + [f"gölge model (terfili): P(kazanç) %{int(pw*100)} < %{int(_SMv.REVIEW_VETO_P*100)}"]
                            plan["gate_verdict"], plan["gate_reasons"] = verdict, greasons
                except Exception as e:
                    # YASA 4 (2026-07-21) — EN TEHLİKELİ SINIF: burası bir KAPI KARARI. Sessizce
                    # düşerse gölge model vetosu HİÇ uygulanmaz, plan GO kalır ve karar ağacında
                    # "shadow_veto" satırı da hiç görünmez (gate_checks 144/144 boş kalmasının aynısı).
                    obs.warn("shadow_veto_check_failed", plan_id=plan.get("id"),
                             ticker=plan.get("ticker"), error=f"{type(e).__name__}: {e}")
                plans.append(plan)
                # E1 İCRA GİRDİLERİ — SİNYAL BARI KAPANIŞINDA SABİTLENİR (kart: "emir parametreleri
                # plan anında sabitlenir; as-of ihlali yok"). Referans fiyat o kapanıştır: emir
                # kapanıştan SONRA, ertesi açılıştan ÖNCE gider. `entry_trigger` çoğu kurulumda tam
                # olarak bu kapanıştır — buy-stop'un "stop price must be greater than current price"
                # ile reddedilmesinin (95/95) kökü budur ve karar `gap_at_submit` ile kayda geçer.
                try:
                    _ref = float(per[c["ticker"]].loc[d, "close"])
                except Exception:  # sessiz-yutma: referans ÖLÇÜLEMEDİ ve karar sözlüğü bunu `ref_kaynak` ile beyan eder (uydurma fiyat yok)
                    _ref = None
                _plan_law[plan["id"]] = BR.entry_order_decision(
                    float(c["entry_trigger"]), ref_price=_ref, atr=c.get("atr"))
                if plan["dormant_setup"]:
                    # uyuyan kurulum: normal slot ASLA — yalnız keşif sondası (GO şartı, çıta yüksek)
                    if verdict == "GO":
                        explore_pool.append(plan)
                elif explore_mode:
                    # KEŞİF: yalnız GO notu aday olur — silahlama döngü SONUNDA (havuzdan seçim).
                    # REVIEW keşifte silahlanMAZ (çıta yüksek kalır).
                    if verdict == "GO":
                        explore_pool.append(plan)
                elif verdict != "NO_GO" and slots > 0:   # GO/REVIEW arm at L0; NO_GO never trades
                    meta["armed"].append(plan)
                    sector_ct[c["sector"]] = sector_ct.get(c["sector"], 0) + 1
                    slots -= 1
            # KEŞİF SLOT SEÇİMİ: kapıyı geçmiş eşitler arasından tek sonda. ≥2 adayda yerel ajan
            # SIRALAYICI olarak sorulur (yetkisi yalnız bu seçim; boyut/karar üretemez); cevap yoksa
            # skor sırası (havuz zaten skor-sıralı adaylardan doldu) — fail-open.
            if explore_pool:
                open_expl = [pos for pos in b.positions.values() if getattr(pos, "exploration", False)]
                armed_expl = [a for a in meta["armed"] if a.get("exploration")]
                n_explore = len(open_expl) + len(armed_expl)
                used_r = sum(float(getattr(p2, "size_r", 0)) for p2 in open_expl) + \
                         sum(float(a.get("size_r") or 0) for a in armed_expl)
                # sıralama: ≥2 adayda yerel ajanın seçimi başa, kalanlar skor sırası (havuz zaten sıralı)
                ordered = list(explore_pool)
                if len(ordered) > 1:
                    try:
                        from . import hermes as _hm
                        pick = _hm.rank_explore([{"ticker": p2["ticker"], "setup": p2.get("setup"),
                                                  "score": p2.get("score"),
                                                  "rr": p2.get("r_multiple_expected")}
                                                 for p2 in ordered])
                        if pick:
                            ordered.sort(key=lambda p2: 0 if p2["ticker"] == pick else 1)
                    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
                        pass
                for chosen in ordered:
                    if n_explore >= EXPLORE_MAX_POS or used_r + EXPLORE_MAX_R > EXPLORE_TOTAL_R + 1e-9:
                        break
                    chosen["size_r"] = min(float(chosen["size_r"]), EXPLORE_MAX_R)
                    chosen["exploration"] = True
                    chosen["gate_reasons"] = list(chosen.get("gate_reasons") or []) + \
                        [f"keşif sondası ({'uyuyan kurulum' if chosen.get('dormant_setup') else 'bütçe %0'}): "
                         f"kanıt toplama, {EXPLORE_MAX_R}R tavan"]
                    meta["armed"].append(chosen)
                    n_explore += 1
                    used_r += float(chosen["size_r"])
                    obs.log("exploration_armed", ticker=chosen["ticker"], regime=rj["regime"],
                            size_r=chosen["size_r"], slot=n_explore, llm_ranked=len(explore_pool) > 1)
            # E1 YAN TABLOSU: yalnız SİLAHLI planların icra kararı taşınır (taşınan/carried planlar
            # dahil — onların kararı ÖNCEKİ seansta sabitlendi ve YENİDEN hesaplanmaz: yeniden
            # hesaplasaydık aynı plan iki farklı limitle iki farklı motorda dolabilirdi).
            # Sınırlıdır (silahlı sayısı ≤ max_open_positions + keşif tavanı) → sonsuz büyüme yok.
            _prev_law = dict(meta.get("entry_law") or {})
            _prev_law.update(_plan_law)
            meta["entry_law"] = {a["id"]: _prev_law[a["id"]] for a in meta["armed"]
                                 if a.get("id") in _prev_law}
            store.merge_dated_jsonl("trade_plans.jsonl", dstr, plans)
            try:                                   # öneri #1: günün TÜM planları + uyuyan ateşlemeler
                from . import counterfactual       # karşı-olgusal deftere açılır (dönüş görmezden gelinir)
                counterfactual.collect(dstr, plans, {a["id"] for a in meta["armed"]}, dormant_sigs,
                                       int(float(eff.get("exit.time_stop_days", 15))),
                                       near_miss=near_miss_sigs, regime=rj["regime"])
                for _ds, _rows in (late_by_date or {}).items():    # kaçan seanslar kendi tarihleriyle
                    counterfactual.collect(_ds, [], set(), [],
                                           int(float(eff.get("exit.time_stop_days", 15))),
                                           near_miss=_rows, regime=rj["regime"])
            except Exception as e:
                obs.warn("cf_collect_failed", error=f"{type(e).__name__}: {e}")
            if meta["armed"]:                              # #42 push a single new-plans alert (no-op if unconfigured)
                try:
                    from . import notify
                    if notify.configured():
                        top = meta["armed"][0]
                        # K1 DEVRİ (3b): ham `notify.send` metni yerine `notify.new_plan` — üretilip
                        # HİÇ çağrılmayan sarmalayıcı buraya bağlandı ve metin TEK yerde kaldı.
                        # Kapı hükmü de metne girer (GO ile REVIEW aynı bildirim değil).
                        notify.new_plan(top["ticker"], top.get("gate_verdict") or "?",
                                        top.get("r_multiple_expected"),
                                        n=len(meta["armed"]), date=dstr)
                except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
                    pass
            # mirror the agent's armed BUY decisions to the Alpaca PAPER account (opt-in backend, paper-only)
            if config.BROKER == "alpaca_paper" and not halted and meta["armed"]:
                try:
                    from .adapters import alpaca
                    acct = alpaca.account()
                    if acct is None and not alpaca.transport()["ok"]:
                        # ULAŞILAMADI ≠ 100k. Hesap okunamıyorken START_EQUITY'ye düşmek, hayali bir
                        # sermaye üzerinden boyutlandırmak demekti; üstelik gönderimler de ağ hatasıyla
                        # düşüp geçerli planları 'broker reddi' diye siliyordu. Aynayı ATLA, planlar
                        # SİLAHLI kalsın — iç defter zaten tek gerçek (denetim 2026-07-21).
                        obs.alarm(obs.ALARM_BROKER_REJECT,
                                  f"Alpaca ulaşılamıyor — ayna atlandı, {len(meta['armed'])} plan silahlı kaldı",
                                  detail=alpaca.transport().get("error", "")[:160])
                        raise _MirrorUnreachable()
                    eq = float(acct["equity"]) if acct and "equity" in acct else START_EQUITY
                    submitted, sent, rejected, kept = set(meta.get("alpaca_submitted", [])), 0, [], []
                    vetoed: list = []              # E1 gap-risk vetosu — ret DEĞİL, kendi kararımız
                    for pl in meta["armed"]:
                        if pl["id"] in submitted:
                            kept.append(pl); continue
                        # E1: ayna İÇ MOTORLA AYNI icra girdilerini alır — ATR ve referans fiyat
                        # yan tablodan (silahlanma anında sabitlendi), yasa `broker.entry_law`dan.
                        _lw = (meta.get("entry_law") or {}).get(pl.get("id")) or {}
                        res = alpaca.submit_plan(pl, eq,   # mirror the SAME drawdown de-risk as the internal fill (#50)
                                                 size_mult=derisk_mult(eq_now, meta.get("peak_equity", START_EQUITY)),
                                                 atr=_lw.get("atr"), ref_price=_lw.get("ref_price"))
                        _law_out = res.get("law") or _lw
                        _entry_exec_write({
                            "date": dstr, "plan_id": pl.get("id"), "ticker": pl.get("ticker"),
                            "motor": "ayna", "entry_trigger": pl.get("entry_trigger"),
                            "limit": _law_out.get("limit"), "atr": _law_out.get("atr"),
                            "law": _law_out.get("law"), "emir_tipi": _law_out.get("mode"),
                            "tif": _law_out.get("tif"), "gap_at_submit": _law_out.get("gap_at_submit"),
                            "karar": ("submitted" if res.get("ok")
                                      else ("gap_veto" if res.get("veto")
                                            else ("unreachable" if res.get("reachable") is False
                                                  else "rejected"))),
                            "red_nedeni": (None if res.get("ok") else str(res.get("detail", ""))[:200]),
                            "red_sinifi": (None if res.get("ok")
                                           else _reject_class(res.get("detail"), veto=res.get("veto"),
                                                              reachable=res.get("reachable"))),
                            "qty": res.get("qty"), "fill": None,
                            "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None})
                        if res.get("veto"):
                            # GAP-RİSK VETOSU: bizim kararımız, broker reddi DEĞİL. Plan silahlı
                            # KALMAZ (iç motor da `gap_at_submit` üzerinden aynı vetoyu uygular —
                            # tek yasa) ve ret dağılımına yazılmaz, yoksa broker sağlığı hakkında
                            # yanlış bir sayı üretirdi. Plan SATIRI damgalanır: silahlı bir planın
                            # kaybolma sebebi defterden okunabilmeli (broker_status ile aynı desen).
                            pl["broker_status"] = "gap_veto"
                            vetoed.append(pl)
                            obs.log(BR.EV_GAP_VETO, ticker=pl.get("ticker"), plan_id=pl.get("id"),
                                    trigger=pl.get("entry_trigger"), limit=_law_out.get("limit"))
                            continue
                        if res.get("ok"):
                            submitted.add(pl["id"]); sent += 1; kept.append(pl)
                        elif res.get("reachable") is False:
                            # ağ arızası — plan SİLAHLI kalır, 'reddedildi' diye düşürülmez
                            kept.append(pl)
                            obs.log("alpaca_submit_unreachable", ticker=pl["ticker"],
                                    detail=str(res.get("detail", ""))[:160])
                        else:
                            # STRICT (Phase 1.1): a rejected order is NOT marked submitted and is DROPPED from
                            # the armed set, so the internal broker never fills a phantom trade next open.
                            pl["broker_status"] = "failed_broker_rejection"
                            rejected.append({"date": dstr, "plan_id": pl["id"], "ticker": pl["ticker"],
                                             "detail": str(res.get("detail", ""))[:200]})
                            obs.alarm(obs.ALARM_BROKER_REJECT, f"Alpaca reddi: {pl['ticker']} — {res.get('detail','')}",
                                      ticker=pl["ticker"], plan_id=pl["id"])
                        obs.log("alpaca_submit", ticker=pl["ticker"], ok=res.get("ok"), detail=res.get("detail", ""))
                    meta["armed"] = kept                       # phantom-free: only Alpaca-accepted plans stay armed
                    meta["alpaca_submitted"] = list(submitted)[-200:]
                    if rejected or vetoed:
                        # DURABLE failed_broker_rejection: trade_plans.jsonl was serialized BEFORE this branch,
                        # so re-merge the (same, now-mutated) plan dicts — the on-disk rows gain broker_status.
                        # Also keep a bounded ledger in portfolio meta; reconcile surfaces it to the dashboard.
                        store.merge_dated_jsonl("trade_plans.jsonl", dstr, plans)
                        meta["broker_rejected"] = (meta.get("broker_rejected", []) + rejected)[-50:]
                    if sent:
                        obs.log("alpaca_orders_sent", n=sent, equity=eq)
                except _MirrorUnreachable:  # sessiz-yutma: ayna erişilemezliğinin alarmı submit_plan içinde ZATEN yazıldı; burada ikinci kez uyarmak aynı olayı çiftler
                    pass                                    # planlar silahlı kaldı; alarm zaten yazıldı
                except Exception as e:
                    obs.warn("alpaca_submit_failed", error=f"{type(e).__name__}: {e}")

        # ---- 2.4 GÖLGE-VARYANT PORTFÖYLERİ: tek kanca, SIFIR yetki, kendi defteri ----------------
        # P3'ün DIŞINDA (pipeline_run bloğu kapandıktan sonra): ölçüm katmanının maliyeti/arızası
        # denetlenen P3 açıklığına yazılmasın. Nüfus canlı akışın ÜST KÜMESİ (aday ∪ near-miss;
        # gerekçe shadow_variants başlığında). Dilim/RS/sektör/korelasyon girdileri ÇAĞRILABİLİR
        # olarak geçer — gölge onların ikinci bir sürümünü tutmaz. Hata gölgede kalır: bu blok
        # düşerse günlük tur aynen devam eder (planlar ZATEN diske yazıldı).
        try:
            from . import shadow_variants as _sv
            _sv.record_cycle(
                dstr,
                sorted({c["ticker"] for c in candidates} | {s.ticker for s, _ in near_miss_sigs}),
                tail_of=lambda t: _scan_tail(per[t], d),
                rs_of=lambda t: rs_map.get(t, 50),
                sector_of=lambda t: SECTORS.get(t, "?"),
                max_corr_of=lambda t: ind.corr_max(per[t].loc[:d, "close"], others_rets),
                eff=eff, regime=rj, goal=goal, limits=limits, bounds=config.bounds(),
                version=version,
                book={"positions": {t: {"sector": SECTORS.get(t, "?"), "size_r": p.size_r}
                                    for t, p in b.positions.items()},
                      "equity": eq_now, "peak_equity": meta.get("peak_equity", START_EQUITY)},
                live_armed=[a["ticker"] for a in meta["armed"]], explore_mode=bool(explore_mode),
                # GÖLGE-v2 (2026-07-30): barlar + indeks + rejim bayrağı GEÇİLİRSE aynı kanca
                # yaşam-döngüsü motorunu da koşturur (fill → yönetim → çıkış → mark, varyant başına
                # kalıcı kâğıt kitap). `per`/`idx` ZATEN burada; ikinci bir bar yükleyici YOK.
                bars=per, index_bars=idx, regime_ok=regime_ok)
        except Exception as e:
            obs.warn("shadow_variants_failed", error=f"{type(e).__name__}: {e}")

    if plans:
        # yerel LLM ajanından aday İKİNCİ GÖRÜŞÜ — arka planda (danışma katmanı; kapıyı değiştirmez,
        # döngüyü bloklamaz, hata verirse sessizce düşer)
        try:
            from . import hermes
            hermes.review_candidates_async(dstr)
        except Exception:  # sessiz-yutma: danışma katmanı — LLM ikinci görüşü kapıyı DEĞİŞTİRMEZ; yokluğu kararı bozmaz, hatası da günlük turu bloklayamaz
            pass

    meta["last_date"] = dstr
    # SICAK FİYAT — DEVRE DIŞI (sadeleştirme turu, 2026-07-30). Bu blok seansın kapanış fiyatlarını
    # `mrd:price`a yazıyordu. ÖLÇÜM: `hotstate.get_price`ın PRODÜKSİYONDA hiçbir çağıranı yok (yalnız
    # testler); intraday tüketicisi bilerek sıcak fiyatı DEĞİL admissible barın OHLC'sini okuyor
    # (intraday_cycle: "ASLA sıcak fiyattan"). Yani EOD kapanışlarını Redis'e kopyalamak evrenin
    # tamamı için her tur pipeline yazımı yapıp kimseye okutmamaktı — bedava sadelik, kapatıldı.
    #   NOT: `mrd:price`ın DİĞER yazıcısı (`hotstate.ingest_bars`, kapanmış bar → sıcak fiyat) YERİNDE
    #   DURUYOR; kapanan yalnız EOD kopyasıdır. GERİ AÇMA: aşağıdaki dört satırın yorumunu kaldır.
    # try:
    #     from . import hotstate
    #     _closes = {t: float(per[t].loc[d, "close"]) for t in per if d in per[t].index}
    #     if _closes:
    #         hotstate.set_prices(_closes, ts=dstr)
    # except Exception:  # sessiz-yutma: hotstate uçucu türev; fiyat kopyalama hatası günlük turu düşüremez
    #     pass
    _hotstate_off_once("mrd:price", "daily_cycle", "get_price")
    meta["day_start_equity"] = b.equity(_marks(per, d))
    mirror = {}
    try:
        mirror = reconcile_broker_state(meta, dstr, b.closed,   # Phase 1: reconcile internal book ↔ Alpaca mirror
                                        open_positions={t: {"qty": p.qty, "scaled_out": p.scaled_out,
                                                            "trail_stop": p.trail_stop, "plan_id": p.plan_id}
                                                        for t, p in b.positions.items()},
                                        # E2: RESMÎ AÇILIŞ bu seansın barlarından gelir — mutabakat
                                        # katmanı ikinci bir bar kaynağı açmaz (tek gerçek).
                                        opens={t: float(df.loc[d, "open"]) for t, df in per.items()
                                               if d in df.index})
    except Exception as e:
        obs.warn("reconcile_failed", error=f"{type(e).__name__}: {e}")
    _entry_exec_trim()
    _save_broker(b, meta)

    try:
        with skills.pipeline_run("P5_LEARN", artifact="state/hypotheses.jsonl"):   # learning is auditable too (#39)
            outcome = rollback.evaluate_outcomes(goal)   # close the learning loop: promote/rollback + writeback
            try:
                from .shadow_model import ShadowTradeOutcomeModel as _SM
                _SM.refit_and_save()                     # v3 gölge model — her döngü ucuz yeniden-eğitim
                from .regime_trigger import DeferredRegimeBudgetTrigger
                DeferredRegimeBudgetTrigger().evaluate() # v3 ertelenmiş bütçe tetikleyicisi (yalnız sinyal)
                from . import analytics as _an           # öneri #3: skor kalibrasyonu — rapor, karar değil
                _cal = _an.score_calibration()
                if _cal:
                    store.write_json("score_calibration.json", _cal)
                    obs.log("score_calibration", n=_cal["n"], rank_ic=_cal["rank_ic"])
                    # ANLIK DEĞER ÜZERİNE YAZILIR, TREND BİRİKİR: bar günü başına tek nokta
                    # (idempotent — aynı gün ikinci koşu yazmaz). "IC yükseliyor mu?" sorusu
                    # ancak defterde tarih tarih duran bir seriyle cevaplanabilir.
                    _an.record_score_calibration_point(dstr, _cal)
                from . import probgate as _pg            # öneri #4: kapı meta-kalibrasyonu (kendini sıkılaştırır)
                _pg.refresh_meta_calibration()
                _an.llm_opinion_calibration()            # Kademe-2: LLM görüş kalibrasyonu (terfi kuralı yazılı)
                _an.exit_efficiency()                    # #4: MFE/MAE muhasebesi (rapor + UCB dürtme bayrağı)
                _an.cf_fidelity()                        # v10 #2: cf simülasyonunun canlıya sadakati
                # Aşama 1.2: bileşen IC'si (rs/tight/vol/prox × 5/10/20 bar × katman). Bileşenler
                # defterde alan olarak durmadığı için barlardan yeniden hesaplanır — bu yüzden
                # P5'in en pahalı adımı (evren CSV'leri okunur). Günde bir koşar ve SIFIR yetkisi
                # vardır; düşerse döngü aynen devam eder (dış try zaten sarıyor, ama bu adımın
                # maliyeti diğerlerini rehin almasın diye kendi koruması var).
                try:
                    from . import component_ic as _cic
                    _cic.component_ic()
                except Exception as e:
                    obs.warn("component_ic_failed", error=f"{type(e).__name__}: {e}")
                # Aşama 1.3: min_score eşik eğrisi. Bileşen IC'siyle AYNI bar evrenini okur (bu
                # yüzden hemen ardından koşar — CSV'ler işletim sistemi önbelleğinde sıcak) ve
                # onun gibi SIFIR yetkilidir. Ayrı korumada: eğri düşerse bileşen tablosu yaşar.
                try:
                    from . import threshold_curve as _tc
                    _tc.build()
                except Exception as e:
                    obs.warn("threshold_curve_failed", error=f"{type(e).__name__}: {e}")
                # H4 — ÖNER→ÖLÇ→ÖĞREN OTOMASYONU (Hermes paketi, 2026-07-30). Kuyrukta bekleyen
                # bileşik varsa HAFTALIK YOKLAMA BÜTÇESİ içinde prescreen AYRI BİR SÜREÇTE başlar.
                # GECE DÖNGÜSÜNÜ BLOKLAMAZ: prescreen dakikalar sürer, senkron çağrılsaydı EOD işleri
                # gecikirdi (ops/barsarchive-run.sh nohup deseni). Kendi korumasında: kuyruk yolu
                # düşse bile P5'in geri kalanı yaşar.
                try:
                    from . import hermes_composite as _hc
                    _sp = _hc.spawn_pending(limit=1)
                    if _sp.get("spawned"):
                        obs.log("composite_queue_spawned", n=len(_sp["spawned"]),
                                butce_kalan=_sp.get("butce_kalan"))
                except Exception as e:
                    obs.warn("composite_spawn_hook_failed", error=f"{type(e).__name__}: {e}")
                # H5 — SKILL ÖZ-YÖNETİMİ: atıf kanıtı eşiğini aşan skiller. PROTECTED beşlisi ASLA;
                # motor-içi skiller yalnız RAPORLANIR (bayrak yazımı davranışı değiştirmez).
                try:
                    from . import skills as _sk5
                    _sk5.auto_shadow_from_evidence()
                except Exception as e:
                    obs.warn("skill_auto_shadow_failed", error=f"{type(e).__name__}: {e}")
                _an.mae_profile()                        # K1 devri: stopların kör ikizi (MAE muhasebesi)
                _an.near_miss_report()                   # darboğaz: hangi eşik masada para bırakıyor?
                _an.regime_edge()                        # cf-bootstrap bulgusu: rejim başına edge (ajana besleme)
                _universe_drift_check()                  # denetim turu 3: evren ölü isim taşıyor mu?
                from . import watchdog as _wd5
                _wd5.check_integrity_and_alarm()         # ÜRETKENLİK+KORUNUM+DETERMİNİZM (sessiz hata avı)
                _wd5.beat("p5_calibrations")
            except Exception as e:
                obs.warn("v3_learn_layer_failed", error=f"{type(e).__name__}: {e}")
        if outcome:
            obs.log("outcome_evaluated", **{k: outcome[k] for k in ("version", "delta", "promoted", "rolled_back") if k in outcome})
    except Exception as e:
        obs.warn("evaluate_outcomes_failed", error=f"{type(e).__name__}: {e}")

    equity = round(b.equity(_marks(per, d)), 2)
    health.write_heartbeat(version=version, open_positions=len(b.positions), equity=equity,
                           last_bar=dstr, regime=rj["regime"], exposure_budget_pct=rj["exposure_budget_pct"],
                           armed=len(meta["armed"]), day_pnl_pct=round(day_pnl_pct, 4),
                           breaker_tripped=breaker, halted=halted, data_ok=not data_bad,
                           explore_mode=bool(explore_mode),
                           mirror_drift=bool(mirror.get("drift")))
    obs.log("daily_cycle", date=dstr, regime=rj["regime"], candidates=len(candidates), plans=len(plans),
            armed=len(meta["armed"]), open_positions=len(b.positions), equity=equity,
            halted=halted, breaker=breaker, data_ok=not data_bad)
    return {"status": "ok", "date": dstr, "regime": rj["regime"], "candidates": len(candidates),
            "plans": len(plans), "armed": len(meta["armed"]), "open_positions": len(b.positions),
            "equity": equity, "halted": halted, "breaker": breaker, "data_ok": not data_bad}


SCAN_TAIL_BARS = 340       # P2 tarama penceresi: 252-bar ısınma + haftalık resample payı


def _scan_tail(df_t, d):
    """P2'nin tarama dilimi — TEK TANIM (sadeleştirme turu, 2026-07-30).

    `.loc[:d]` NEDENSELLİK kesimidir (d'den sonrası görünmez), `.tail(SCAN_TAIL_BARS)` maliyet
    kesimidir. Bu ikisi bir tarife: gölge-varyant katmanı AYNI dilim üzerinde ölçmek zorundadır,
    yoksa varyantın "aynı aday akışı" iddiası ilk pencere kaymasında yalan olur. Reçete iki yerde
    elle yazılıydı; tek tanıma indi ve çağıranlar onu paylaşıyor."""
    return df_t.loc[:d].reset_index().tail(SCAN_TAIL_BARS)


def _marks(per, d):
    return {t: per[t].loc[d, "close"] for t in per if d in per[t].index}


def _persist_trade(trade: dict) -> None:
    """Append a closed trade — DEDUPED against recent rows. Trades are appended mid-cycle but broker
    state (the position's existence + last_date) is saved only at cycle end; if the cycle dies in
    between, every 300s retry reloads the old state, re-closes the same position, and would append the
    identical row again — one crash-day could stack dozens of duplicates into the learning ledger
    (audit #11). Identity = (plan_id|ticker, ts_close, exit_reason, exit price).

    KAYNAK DAMGASI (BT-1, 2026-07-31): BURASI defterin İLERİ yoludur — bu fonksiyondan geçen her
    satır canlı kâğıt döngünün GERÇEKTEN kapattığı bir işlemdir. Tohum yolu (`run.replay_seed`)
    defterin tamamını tek seferde yazar ve kendi damgasını basar. Damga satır diske DÜŞMEDEN
    basılır: sonradan damgalamak, damgasız bir aralık doğurur ve BT-1 tam olarak o aralıktı."""
    ledgerstamp.stamp(trade, ledgerstamp.LIVE_PAPER)
    key = (trade.get("plan_id") or trade.get("ticker"), str(trade.get("ts_close")),
           str(trade.get("exit_reason")), round(float(trade.get("exit") or 0.0), 6))
    for r in store.read_jsonl("trades.jsonl")[-30:]:
        if (r.get("plan_id") or r.get("ticker"), str(r.get("ts_close")),
                str(r.get("exit_reason")), round(float(r.get("exit") or 0.0), 6)) == key:
            obs.warn("duplicate_trade_suppressed", ticker=trade.get("ticker"), ts_close=trade.get("ts_close"))
            return
    store.append_jsonl("trades.jsonl", trade)


def _trail_patch_alarm(sym: str, res: dict, frm: float, to: float) -> None:
    """Faz 0: iç HWM yükseldi ama broker PATCH'i reddetti → iç stop ile Alpaca stopu AYRIŞTI.
    Eski kod bunu yalnız logluyordu; ayrışma bir sonraki reconcile'a dek görünmezdi. Artık alarm."""
    if not res.get("ok"):
        obs.alarm(obs.ALARM_TRAIL_DESYNC,
                  f"trail PATCH reddedildi: {sym} {frm}→{to}",
                  ticker=sym, from_stop=frm, to_stop=to, detail=str(res.get("detail", ""))[:200])


def _entry_fill_price(order: dict) -> float | None:
    """Bir bracket PARENT emrinin GİRİŞ dolum fiyatı. `exit_fill_price`in ikizi: o BACAKLARA bakar
    (çıkış), bu parent'ın kendisine (giriş). `partially_filled` de gerçek bir `filled_avg_price`
    taşır ve atlanırsa slipaj ölçümü tam icra karıştığında sessizce boşalır (denetim #54'ün dersi)."""
    if not isinstance(order, dict):
        return None
    if str(order.get("status", "")).lower() not in ("filled", "partially_filled"):
        return None
    v = order.get("filled_avg_price")
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; satır `fill: None` ile kalır ve payda sayacında görünür
        return None


def _patch_entry_slippage(by_coid: dict, opens: dict | None, dstr: str) -> dict:
    """E2 — SLİPAJ DEFTERİNİN DOLUM YARISI. Aynadaki GİRİŞ emri dolduğunda ilgili satıra iki bps
    yazılır ve satır bir daha yazılmaz (idempotent: `fill` doluysa atlanır).

      * `fill_vs_resmi_acilis_bps` — ödediğimiz fiyat, o seansın RESMÎ AÇILIŞINA göre. Açılış
        mikroyapısının faturası tam olarak budur (E3 bandının ampirik girdisi).
      * `fill_vs_limit_bps`        — ödediğimiz fiyat, yasanın tavanına göre. Negatif = tavanın
        altında doldu (yasa para bıraktı), 0'a yakın = tavanda dolduk (limit BAĞLADI).

    Resmî açılış yoksa (bar gelmemiş) o bps None kalır — açılışı dolum fiyatıyla ikame etmek,
    ölçmek istediğimiz farkı tanımı gereği sıfır yapardı."""
    out = {"eslesen": 0, "yazilan": 0, "acilis_yok": 0}
    try:
        rows = store.read_jsonl(ENTRY_LEDGER)
    except Exception as e:
        obs.warn("entry_exec_ledger_read_failed", error=f"{type(e).__name__}: {e}")
        return out
    changed = False
    for r in rows:
        if r.get("motor") != "ayna" or r.get("fill") is not None:
            continue
        o = by_coid.get(r.get("plan_id"))
        af = _entry_fill_price(o) if o else None
        if af is None:
            continue
        out["eslesen"] += 1
        op = (opens or {}).get(r.get("ticker"))
        if op is None:
            op = r.get("resmi_acilis")
        if op is None:
            out["acilis_yok"] += 1
        r["fill"] = round(af, 4)
        r["fill_qty"] = o.get("filled_qty")
        r["fill_status"] = str(o.get("status", "")).lower()
        r["resmi_acilis"] = (round(float(op), 4) if op is not None else None)
        r["fill_vs_resmi_acilis_bps"] = _bps(af, op)
        r["fill_vs_limit_bps"] = _bps(af, r.get("limit"))
        r["fill_kaydedildi"] = dstr
        changed = True
        out["yazilan"] += 1
    if changed:
        try:
            store.write_jsonl(ENTRY_LEDGER, rows)     # atomik (mkstemp + os.replace)
        except Exception as e:
            obs.warn("entry_exec_ledger_patch_failed", error=f"{type(e).__name__}: {e}")
    return out


def reconcile_broker_state(meta: dict, dstr: str, closed_this_cycle: list,
                           open_positions: dict | None = None,
                           opens: dict | None = None) -> dict:
    """Phase 1 reconciliation — bring the internal book into agreement with the Alpaca PAPER mirror.

      * strip locally-armed plans whose Alpaca order is DEAD (rejected/canceled/expired) so the internal
        broker doesn't fill a phantom next open (complements the strict-submit path);
      * POSITION reconciliation — internal open positions vs alpaca.positions(): an internal position with
        no Alpaca position AND no live entry order is split-brain (alarm); a shared symbol whose quantities
        diverge >25% is sizing drift (alarm); an Alpaca position the engine never opened (e.g. the
        operator's own holdings) is listed as external — informational only, NEVER an alarm;
      * audit execution DIVERGENCE — the internal simulator's gap-aware exit vs the ACTUAL Alpaca fill. A gap
        beyond MIRROR_DRIFT_TOL fires an alarm + sets a dashboard mirror_drift flag, and the real Alpaca fill
        is written to the trade row (alpaca_fill_price) so real-world slippage vs the model is measurable.

    Matched by client_order_id == plan_id. Guarded to BROKER==alpaca_paper; any Alpaca API failure is logged,
    never fatal to the cycle. Writes state/broker_reconcile.json for the dashboard."""
    out = {"checked": False, "stripped": [], "drift": [],
           "positions": {"missing_on_alpaca": [], "qty_drift": [], "external": []}}
    # ATLAMA DA BİR SONUÇTUR. Bu iki dal HİÇBİR ŞEY YAZMADAN dönüyordu: broker_reconcile.json dünkü
    # içeriğiyle diskte kalıyor, pano onu GÜNCEL mutabakat sanıp okuyordu — "kontrol edilmedi" ile
    # "kontrol edildi, temiz" ayırt edilemiyordu. Arıza dalı (aşağıda) zaten api_ok=False yazıyor;
    # atlama dalları da nedenini yazmalı, yoksa bayat artefakt taze konuşur (2026-07-22).
    def _skip(reason: str) -> dict:
        prev = store.read_json("broker_reconcile.json", {})
        store.write_json("broker_reconcile.json", {**prev, "checked": False, "skip_reason": reason,
                         "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        return out

    if config.BROKER != "alpaca_paper":
        return _skip(f"broker={config.BROKER} — ayna mutabakatı yalnız alpaca_paper'da anlamlı")
    from .adapters import alpaca
    if not alpaca.paper_available():
        return _skip("paper_available()=False — kimlik/erişim yok, ayna okunamadı")
    try:
        # nested=True is REQUIRED: the flat list endpoint splits a bracket into 3 top-level orders with
        # legs=[], so exit_fill_price() (which reads the parent's legs) would always see nothing and the
        # divergence audit below would silently no-op. nested returns the parent carrying its TP/SL legs.
        all_orders = alpaca.orders(status="all", limit=200, nested=True)
        # A1 (denetim 2026-07-21): alpaca.orders() İSTİSNA FIRLATMAZ — hata durumunda [] döner. Yani
        # aşağıdaki `except` ÖLÜ KOD'du ve API arızası "hiç emir yok" gibi okunuyordu: a_by_sym da boş
        # kalıp AÇIK HER POZİSYON 'Alpaca'da kayıp' diye split-brain alarmı üretiyor, pano ise
        # api_ok=True gösteriyordu. Arızayı artık taşıma kaydı söylüyor.
        if not alpaca.transport()["ok"]:
            raise RuntimeError(alpaca.transport().get("error") or "alpaca transport down")
    except Exception as e:
        obs.warn("reconcile_orders_failed", error=f"{type(e).__name__}: {e}")
        # SAFE-FAIL görünürlüğü: broker API'sine ulaşılamadı — sessiz kalma, panoya işle (şerit amber)
        prev = store.read_json("broker_reconcile.json", {})
        store.write_json("broker_reconcile.json", {**prev, "api_ok": False, "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        return out
    out["checked"] = True
    by_coid = {o.get("client_order_id"): o for o in (all_orders or []) if o.get("client_order_id")}
    DEAD = {"rejected", "canceled", "cancelled", "expired", "done_for_day"}

    # (1.1) E2 — GİRİŞ SLİPAJ DEFTERİNİN DOLUM YARISI. Emirler ZATEN okundu; ikinci bir çağrı yok.
    out["entry_slippage"] = _patch_entry_slippage(by_coid, opens, dstr)

    # (1.2) strip armed plans whose mirror order is dead
    kept = []
    for pl in meta.get("armed", []):
        o = by_coid.get(pl.get("id"))
        if o and str(o.get("status", "")).lower() in DEAD:
            out["stripped"].append(pl.get("ticker"))
            obs.log("reconcile_strip_armed", ticker=pl.get("ticker"), status=o.get("status"))
        else:
            kept.append(pl)
    if len(kept) != len(meta.get("armed", [])):
        meta["armed"] = kept

    # (1.2b) POSITION reconciliation — Alpaca-reported positions vs the internal book's open positions.
    # A symbol can legitimately be internal-only while its Alpaca stop-entry hasn't triggered yet, so
    # "missing" requires no position AND no live (non-dead, non-filled) order for that symbol.
    try:
        apos = alpaca.positions()
        if not alpaca.transport()["ok"]:                 # A1: [] burada 'pozisyon yok' DEĞİL, arıza
            raise RuntimeError(alpaca.transport().get("error") or "alpaca transport down")
    except Exception as e:
        obs.warn("reconcile_positions_failed", error=f"{type(e).__name__}: {e}")
        # pozisyon listesi okunamadıysa POZİSYON mutabakatını hiç yapma: boş listeyle karşılaştırmak
        # her açık pozisyon için sahte 'Alpaca'da kayıp' alarmı üretir (denetim 2026-07-21).
        out["positions"]["api_ok"] = False
        store.write_json("broker_reconcile.json", {**store.read_json("broker_reconcile.json", {}),
                         "api_ok": False, "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        return out
    a_by_sym = {str(p.get("symbol")): p for p in (apos or [])}
    alive_order_syms = {o.get("symbol") for o in (all_orders or [])
                        if str(o.get("status", "")).lower() not in DEAD | {"filled"}}
    local = {str(t): (dict(q) if isinstance(q, dict) else {"qty": float(q), "scaled_out": False})
             for t, q in (open_positions or {}).items()}
    for sym, info in local.items():
        qty, scaled = float(info.get("qty") or 0.0), bool(info.get("scaled_out"))
        ap = a_by_sym.get(sym)
        if ap is None:
            if sym not in alive_order_syms:
                out["positions"]["missing_on_alpaca"].append(sym)
                obs.alarm(obs.ALARM_MIRROR_DRIFT,
                          f"ayna pozisyonu kayıp: {sym} içeride açık, Alpaca'da ne pozisyon ne emir var",
                          ticker=sym, local_qty=qty)
            continue
        try:
            aq = float(ap.get("qty") or 0.0)
        except (TypeError, ValueError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
            continue
        if scaled:
            continue   # internal book banked a partial (qty reduced by design); the mirror bracket still
                       # holds full size — a KNOWN, intentional gap, not drift (audit #16 false alarm)
        # sizing runs off two slightly different equities (internal book vs Alpaca account), so small qty
        # gaps are expected; >25% relative gap is real drift, not rounding.
        if qty > 0 and abs(aq - qty) / qty > 0.25:
            out["positions"]["qty_drift"].append({"ticker": sym, "local_qty": qty, "alpaca_qty": aq})
            obs.alarm(obs.ALARM_MIRROR_DRIFT,
                      f"ayna adet sapması: {sym} — içeride {qty:g}, Alpaca'da {aq:g}",
                      ticker=sym, local_qty=qty, alpaca_qty=aq)
    # engine-orphans vs true externals: a bracket the ENGINE submitted (client_order_id 'P-…') can fill
    # on Alpaca after the internal side dropped its plan (breaker day, slot race, gap guard) — that is
    # split-brain and must ALARM, not hide under 'external' with the operator's own holdings (audit #14).
    engine_syms = {o.get("symbol") for o in (all_orders or [])
                   if str(o.get("client_order_id", "")).startswith("P-")
                   and str(o.get("status", "")).lower() in ("filled", "partially_filled")}
    orphans = sorted(sym for sym in a_by_sym if sym not in local and sym in engine_syms)
    for sym in orphans:
        obs.alarm(obs.ALARM_MIRROR_DRIFT,
                  f"motor yetimi: {sym} Alpaca'da açık (motorun emri dolmuş) ama iç defterde yok",
                  ticker=sym)
    out["positions"]["engine_orphans"] = orphans
    out["positions"]["external"] = sorted(sym for sym in a_by_sym
                                          if sym not in local and sym not in engine_syms)  # info only, no alarm

    # (1.2c) DİNAMİK TRAILING-STOP AYNA SENKRONU: iç defterin iz süren stop'u yükseldiyse, aynadaki
    # bracket'ın stop bacağı da yükseltilir (PATCH) — YALNIZ YUKARI, koruma asla gevşetilmez. Bu,
    # trail sıkılaştıkça aynanın eski stop'ta kalıp sapma alarmı üretmesini kökten keser.
    out["trail_synced"] = []
    for sym, info in local.items():
        ts = info.get("trail_stop")
        pid = info.get("plan_id")
        if not ts or not pid:
            continue
        parent = by_coid.get(pid)
        if not parent:
            continue
        for leg in (parent.get("legs") or []):
            if str(leg.get("type")) != "stop" or str(leg.get("status")).lower() not in ("new", "held", "accepted", "open"):
                continue
            try:
                cur_stop = float(leg.get("stop_price") or 0.0)
            except (TypeError, ValueError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                continue
            if float(ts) > cur_stop * 1.001:               # anlamlı yükseliş; asla aşağı çekme
                res = alpaca.replace_order_stop(leg.get("id"), float(ts), cur_stop=cur_stop)  # A4: sınır da reddeder
                out["trail_synced"].append({"ticker": sym, "from": cur_stop, "to": round(float(ts), 2),
                                            "ok": bool(res.get("ok"))})
                obs.log("mirror_trail_synced", ticker=sym, from_stop=cur_stop, to_stop=round(float(ts), 2),
                        ok=bool(res.get("ok")), detail=str(res.get("detail", ""))[:120])
                _trail_patch_alarm(sym, res, cur_stop, float(ts))

    # (1.3) execution-divergence audit on trades closed THIS cycle
    #
    # KİLİTLİ YAMA (B3, 2026-07-31): eskiden defter burada okunuyor, ARADA Alpaca çağrıları
    # yapılıyor ve sonunda TAMAMI geri yazılıyordu — kilitsiz, üstelik uzun bir pencerede. O
    # pencerede `_persist_trade` bir satır eklerse (canlı döngü) yeni satır SESSİZCE siliniyordu.
    # Yamalar artık toplanıp tek kilitli `update_jsonl` ile uygulanır: kilit penceresi ağ
    # çağrılarını KAPSAMAZ (süreçler-arası kilidi ağ gecikmesi kadar tutmak yeni bir kilitlenme
    # sınıfı açardı) ve defter yeniden okunduğu için araya giren satırlar korunur.
    trades = store.read_jsonl("trades.jsonl")
    last_row = {}
    for i, t in enumerate(trades):
        if t.get("plan_id"):
            last_row[t["plan_id"]] = i           # newest row per plan_id (the one just persisted this cycle)
    _yamalar: dict = {}
    for tr in closed_this_cycle:
        o = by_coid.get(tr.get("plan_id"))
        af = alpaca.exit_fill_price(o) if o else None
        if af is None:
            continue
        sim = float(tr.get("exit") or 0.0)
        div = abs(af - sim) / sim if sim else 0.0
        i = last_row.get(tr.get("plan_id"))
        if i is not None and "alpaca_fill_price" not in trades[i]:
            _yamalar[tr.get("plan_id")] = {"alpaca_fill_price": round(af, 4),
                                           "mirror_divergence": round(div, 5)}
        if div > MIRROR_DRIFT_TOL:
            out["drift"].append({"ticker": tr.get("ticker"), "sim": round(sim, 4), "alpaca": round(af, 4),
                                 "div_pct": round(div * 100, 3)})
            obs.alarm(obs.ALARM_MIRROR_DRIFT,
                      f"ayna sapması: {tr.get('ticker')} — sim {sim} vs Alpaca {af} (%{div*100:.2f})",
                      ticker=tr.get("ticker"), sim=sim, alpaca_fill=af, divergence=round(div, 4))
    if _yamalar:
        def _fill_patch(rows, _y=_yamalar):
            son: dict = {}
            for _i, _t in enumerate(rows):        # plan başına EN YENİ satır (bu turda yazılan)
                if _t.get("plan_id") in _y:
                    son[_t["plan_id"]] = _i
            hit = False
            for _pid, _i in son.items():
                if "alpaca_fill_price" not in rows[_i]:
                    rows[_i].update(_y[_pid])
                    hit = True
            return hit

        store.update_jsonl("trades.jsonl", _fill_patch)   # kilitli oku-değiştir-yaz (telemetri)

    # Faz 1 (1a): HAYALET emirler — Alpaca'da canlı görünen ama yerel izde (armed/alpaca_submitted/
    # mirror durum makinesi) karşılığı olmayan coid'ler. Motor bunları AÇMADI: ya operatör elle emir
    # girdi ya da defter/tarihçe ayrıştı. Kırmızı etiket panoda; asla otomatik iptal edilmez (politika).
    _known = set(meta.get("alpaca_submitted", []) or []) | {a.get("id") for a in meta.get("armed", [])}
    try:
        _known |= set((store.read_json("mirror_orders.json", {}) or {}).get("orders", {}).keys())
    except Exception as e:
        # YASA 4 (2026-07-21): bu okuma sessizce düşerse _known EKSİK kalır ve motorun kendi emirleri
        # "hayalet" diye panoya kırmızı düşer — yani sessiz yutma burada YANLIŞ ALARM üretiyordu.
        obs.warn("mirror_orders_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="hayalet listesi eksik bilinen-emir kümesiyle hesaplandı")
    out["ghosts"] = [{"symbol": o.get("symbol"), "coid": o.get("client_order_id"),
                      "status": o.get("status")}
                     for o in (all_orders or [])
                     if str(o.get("status", "")).lower() not in DEAD | {"filled"}
                     and o.get("client_order_id") and o.get("client_order_id") not in _known][:20]
    if out["ghosts"]:
        obs.warn("reconcile_ghost_orders", n=len(out["ghosts"]),
                 symbols=[g["symbol"] for g in out["ghosts"]][:8])
    # Faz 1 (1d): bu reconcile turunun zorlama-senkron özeti — saydamlık paneli buradan okur
    out["force_sync"] = {"stripped": len(out["stripped"]),
                         "trail_patched": sum(1 for x in out.get("trail_synced", []) if x.get("ok")),
                         "trail_failed": sum(1 for x in out.get("trail_synced", []) if not x.get("ok"))}
    pos = out["positions"]
    from . import watchdog as _wd6
    _wd6.beat("mirror_reconcile")
    store.write_json("broker_reconcile.json", {
        "date": dstr, "mirror_drift": bool(out["drift"]), "stripped": out["stripped"], "drift": out["drift"][:10],
        "ghosts": out["ghosts"], "force_sync": out["force_sync"],
        "position_drift": bool(pos["missing_on_alpaca"] or pos["qty_drift"]), "positions": pos,
        "failed_submissions": (meta.get("broker_rejected") or [])[-10:],
        # v3 senkron kriterleri: canlı emirli semboller (P3 aynı hisseyi yeniden silahlamasın) +
        # broker API sağlığı (kesinti panoda görünür olmalı) + trail senkron kaydı
        "alive_order_syms": sorted(s for s in alive_order_syms if s),
        "api_ok": True, "trail_synced": out.get("trail_synced", []),
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    return out
