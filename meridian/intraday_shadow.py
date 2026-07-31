"""intraday_shadow.py — FAZ 4B GÖLGE MODU (2026-07-27). SIFIR YETKİ, TAM KARAR.

Faz 4a "tetik kesildi mi?"yi ölçüyordu. Cevaplayamadığı soru şuydu: **kesildiğinde NE OLURDU?**
Bir eşik geçişi tek başına bir karar değildir — kapılar, boyutlandırma, likidite tavanı ve gap
korumaları bir emri tamamen iptal edebilir. "Tetik 14 kez kesildi" cümlesi, o 14 geçişin kaçının
gerçek bir emre dönüşeceğini SÖYLEMEZ; Faz 4b'yi bu kanıt olmadan açmak, ölçülmemiş bir yetkiyi
açmak olurdu.

BU MODÜL EMİR GÖNDERMEZ. Tek yazdığı kendi defteridir (`intraday_shadow_orders.jsonl`).
Canlı defteri (portfolio.json) OKUR, asla YAZMAZ; broker'ı KOPYA bir nesne üzerinde çalıştırır ve
nesneyi atar. `state/INTRADAY_ARM` (gerçek icra bayrağı) ile HİÇBİR İLİŞKİSİ yoktur — bayrak kapalı
olsa da gölge ölçer, çünkü ölçüm yetki değildir.

NEDEN KOPYA BROKER, "boyutlandırmayı yeniden yaz" DEĞİL: qty/risk hesabı gap koruması, ADV tavanı,
katılım etkisi ve notional tavanını içerir (broker.fill_entry). İkinci bir kopya yazmak, iki hesabın
zamanla AYRIŞMASI demekti — ve ayrıştığı gün gölge defteri EOD'yi değil KENDİNİ ölçüyor olurdu.
Aynı fonksiyon çağrılır; sonuç okunur; nesne atılır.

SİM FİYAT SÖZLEŞMESİ (satıra da yazılır): `sim_price = max(bar_open, entry_trigger)`.
Bar tetiğin ÜSTÜNDE açıldıysa açılışı ödersin; altında açtıysa tetikte dolarsın. Bar İÇİ sıralama
OHLC'den bilinemez, o yüzden sözleşme bilinçli olarak muhafazakârdır (asla tetikten ucuza dolmaz).

loop.py'ye SIFIR TEMAS: canlı EOD motoru bu turda hiç değişmedi. `_load_broker` DESENİ burada
yeniden kurulur (fonksiyon import edilmez) ki gölge katmanı canlı hattın çağrı grafiğine girmesin.
"""
from __future__ import annotations

import os

from . import barclock, config, health, obs, store
from .backtest import _adv as _adv_causal
from .broker import PaperBroker, Position, derisk_mult, max_positions_at
from .score import START_EQUITY

# Varsayılan AÇIK: tek yan etkisi kendi defterine yazmaktır, hiçbir yetki taşımaz. Kapatma anahtarı
# yine de vardır — ölçüm bile olsa, operatör bir katmanı susturabilmelidir.
ENABLED = os.environ.get("MERIDIAN_SHADOW", "1") != "0"

ORDERS_FILE = "intraday_shadow_orders.jsonl"
PORTFOLIO = "portfolio.json"

# (plan_id, seans) → yazıldı. PLAN BAŞINA SEANSTA TEK satır: tetik kesildikten sonra o barın
# high'ı eşiğin üstünde kaldığı sürece HER olayda yeniden geçiş görünür; her birine satır yazmak
# defteri aynı kararın kopyalarıyla şişirir ve "kaç emir çıkardı" sayımını yalanlardı.
_SEEN: set = set()
_SEEN_SESSION: str | None = None


def reset_dedup() -> None:
    """Tekilleştirme belleğini boşalt (testler + seans dönüşü)."""
    global _SEEN, _SEEN_SESSION
    _SEEN = set()
    _SEEN_SESSION = None


def _load_seen(session: str) -> None:
    """Seans başına BİR kez defterden mevcut anahtarları yükle. Süreç seans ortasında yeniden
    başlarsa bellek boş olur ve aynı plan ikinci kez yazılırdı — dedup yalnız RAM'de yaşarsa
    restart onu sıfırlar ve sayım sessizce şişer."""
    global _SEEN, _SEEN_SESSION
    if _SEEN_SESSION == session:
        return
    _SEEN = {(r.get("plan_id"), r.get("date")) for r in store.read_jsonl(ORDERS_FILE)
             if r.get("date") == session}
    _SEEN_SESSION = session


def _copy_broker() -> tuple[PaperBroker, dict]:
    """`loop._load_broker` DESENİ — KOPYA nesne üzerinde, loop'a hiç dokunmadan.

    Neden import değil kopya desen: loop'u import etmek gölge katmanını canlı EOD motorunun modül
    grafiğine bağlardı; bu tur loop.py'ye SIFIR temas sözü verildi. Desen tek yerde (burada)
    yaşıyor ve durumu SALT OKUNUR kuruyor: portfolio.json okunur, PaperBroker belleğe kurulur,
    hiçbir yazım yolu (`_save_broker`) çağrılmaz."""
    goal = config.goal()
    slip = float(goal.get("slippage_bps", 5))
    comm = float(goal.get("commission_per_share", 0.0))
    st = store.read_json(PORTFOLIO, None)
    b = PaperBroker(START_EQUITY, slip, comm)
    if st:
        b.cash = st.get("cash", START_EQUITY)
        b.realized_pnl = st.get("realized_pnl", 0.0)
        b._id = st.get("last_id", 0)
        for t, p in (st.get("positions") or {}).items():
            b.positions[t] = Position(**p)
    return b, (st or {"armed": [], "peak_equity": START_EQUITY, "day_start_equity": START_EQUITY})


def _daily_adv(ticker: str, session: str):
    """EOD ile AYNI ADV: `backtest._adv` — "d barından KESİNLİKLE ÖNCEKİ" 20 seansın hacim ortalaması.

    NEDEN YER TUTUCU SATIR: `_adv` pencereyi `df.loc[:d]["volume"].iloc[:-1]` ile keser, yani `d`nin
    KENDİ satırının frame'de olduğunu varsayar (EOD'de öyledir: o seansın günlük barı yazılmıştır).
    Seans İÇİNDE ise `d` (bugün) henüz CSV'de yoktur; `_adv`i olduğu gibi çağırmak `.iloc[:-1]` ile
    DÜNÜ de düşürür ve pencere bir bar geriye kayardı — EOD'nin kullanacağından farklı, sessizce.
    Bugün için hacimsiz bir yer tutucu satır eklenir; değeri `.iloc[:-1]` tarafından zaten atılır
    (ortalamaya ASLA girmez) ve dilim EOD ile birebir aynı 20 bara oturur. Test bunu kilitler.
    """
    import pandas as pd
    p = config.BARS / f"{str(ticker).lower().replace('.', '-')}.csv"
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p, usecols=["date", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        d = pd.Timestamp(session)
        if d not in df.index:
            df.loc[d, "volume"] = float("nan")   # yer tutucu — `.iloc[:-1]` düşürür, okunmaz
            df = df.sort_index()
        return _adv_causal(df, d)
    except Exception as e:
        obs.warn("shadow_adv_unavailable", ticker=ticker, error=f"{type(e).__name__}: {e}",
                 detail="likidite tavanı ölçülemedi — gölge sabit-slipaj dalını işletir (adv=None)")
        return None


def _gates(b: PaperBroker, meta: dict, ticker: str) -> tuple[dict, dict]:
    """EOD dolgu kapısının (loop.py:368 + 373) gölgedeki karşılığı + her girdinin KAYNAĞI.

    Kapı yasası burada yeniden ÖLÇÜLÜR, kopyalanmaz: `halted`/`circuit_breaker_tripped`/`derisk_mult`
    /`max_positions_at` üretimin kendi fonksiyonlarıdır. Ama girdilerin bir kısmı seans içinde
    birebir yeniden ölçülemez (veri kalitesi kapısı o sabahki günlük bar doğrulamasından gelir,
    gün P&L'i tüm açık pozisyonların marklarını ister). O girdiler EN TAZE KAYITLI kaynaktan okunur
    ve kaynağı satıra yazılır — sessizce atlanmaz, uydurulmaz: bir kapının hangi tarihli girdiyle
    değerlendirildiği, kapının kendisi kadar önemlidir."""
    goal = config.goal()
    hb = store.read_json("heartbeat.json", {}) or {}
    dq = store.read_json("data_quality.json", {}) or {}

    day_pnl_pct = hb.get("day_pnl_pct")
    breaker = health.circuit_breaker_tripped(float(day_pnl_pct), goal) if day_pnl_pct is not None else None
    # Seans içi mark ölçülmediği için sermaye DEFTER değeridir (nakit + pozisyonlar giriş fiyatından).
    # EOD `b.equity(marks_open)` kullanır; fark satırda kaynak damgasıyla görünür.
    eq_now = b.equity()
    peak = meta.get("peak_equity", START_EQUITY)
    size_mult = derisk_mult(eq_now, peak)
    eff_max_open = max_positions_at(eq_now, peak, config.limits()["max_open_positions"])

    gates = {
        "halt": bool(health.halted()),
        "breaker": breaker,
        "data_bad": bool(dq.get("data_halt")) if dq else None,
        "size_mult": size_mult,
        "position_exists": ticker in b.positions,
        "max_open_ok": len(b.positions) < eff_max_open,
    }
    kaynak = {
        "halt": "health.halted() — canlı",
        "breaker": f"heartbeat.json.day_pnl_pct @ {hb.get('ts') or '—'}",
        "data_bad": f"data_quality.json.data_halt @ {dq.get('date') or '—'}",
        "equity": f"{PORTFOLIO} — defter değeri (seans içi mark ölçülmedi)",
        "peak_equity": PORTFOLIO,
    }
    return gates, kaynak


def _blocking(gates: dict) -> str | None:
    """İlk engelleyen kapının ADI — loop.py:368/373'teki sırayla.

    `breaker`/`data_bad` None ise (kaynak dosya hiç yok) kapı ÖLÇÜLEMEDİ demektir; bu durumda
    'geçti' saymak fail-open olurdu, o yüzden ölçülemeyen kapı da engeller ve adıyla yazılır."""
    if gates["halt"]:
        return "halt"
    if gates["breaker"] is None:
        return "breaker_olculemedi"
    if gates["breaker"]:
        return "breaker"
    if gates["data_bad"] is None:
        return "data_bad_olculemedi"
    if gates["data_bad"]:
        return "data_bad"
    if not (gates["size_mult"] > 0):
        return "size_mult"
    if gates["position_exists"]:
        return "position_exists"
    if not gates["max_open_ok"]:
        return "max_open"
    return None


def record(plan: dict, bar: dict, as_of) -> dict | None:
    """Tetik kesildiği ANDA tam icra kararını hesapla ve deftere yaz. HİÇBİR ŞEY GÖNDERMEZ.

    `plan`/`bar`/`as_of` intraday_cycle'ın ZATEN ölçtüğü üçlüdür — look-ahead mantığı burada İKİNCİ
    kez yazılmaz (aynı admissible bar, aynı karar anı). Dönüş: yazılan satır ya da None (kapalı /
    tekrar / biçimsiz girdi)."""
    if not ENABLED:
        return None
    plan_id = plan.get("id")
    ticker = str(plan.get("ticker") or "").upper()
    if not plan_id or not ticker:
        obs.warn("shadow_plan_kimliksiz", ticker=ticker or None,
                 detail="plan_id/ticker yok — gölge satırı EOD ile eşleştirilemezdi, yazılmadı")
        return None
    session = barclock.session_date(as_of)
    _load_seen(session)
    if (plan_id, session) in _SEEN:
        return None

    try:
        trigger = float(plan.get("entry_trigger"))
        bar_open = float(bar.get("o"))
    except (TypeError, ValueError):
        obs.warn("shadow_girdi_bicimsiz", ticker=ticker, plan_id=plan_id,
                 entry_trigger=plan.get("entry_trigger"), bar_open=bar.get("o"),
                 detail="sim fiyat hesaplanamadı — satır yazılmadı (uydurma fiyat üretilmez)")
        return None
    sim_price = max(bar_open, trigger)

    b, meta = _copy_broker()
    gates, kaynak = _gates(b, meta, ticker)
    engel = _blocking(gates)

    qty = risk_dollars = sim_fill = None
    if engel is None:
        # KOPYA broker üzerinde GERÇEK boyutlandırma: aynı fonksiyon, aynı korumalar.
        pos = b.fill_entry(plan, sim_price, as_of.isoformat(), b.equity(),
                           size_mult=gates["size_mult"], adv=_daily_adv(ticker, session))
        if pos is None:
            # fill_entry'nin ret sebebini (gap / stop-altı açılış / likidite / notional) DIŞARIDA
            # yeniden hesaplamıyoruz: o mantığın ikinci kopyası zamanla ayrışır ve gölge defteri
            # EOD'yi değil kendini ölçmeye başlar. Sürüklenme riski > teşhis değeri.
            engel = "broker_kurali"
        else:
            qty, risk_dollars, sim_fill = pos.qty, pos.risk_dollars, pos.entry
    # Kopya broker'ın ömrü burada biter: nesne atılır, hiçbir kalıcılık yolu çağrılmaz.

    ct = barclock.close_ts(bar.get("t"))
    satir = {
        "plan_id": plan_id, "ticker": ticker, "date": session,
        "entry_trigger": trigger, "bar_open": bar_open,
        "sim_price": sim_price, "sim_price_rule": "max(bar_open, entry_trigger)",
        # `sim_fill` = sim_price + slipaj + katılım etkisi (pos.entry). vs_eod KIYASI BUNU kullanır:
        # trades.jsonl'in `entry` alanı da friksiyon SONRASI fiyattır; sim_price ile kıyaslamak
        # friksiyonu sistematik bir "fark" gibi gösterirdi (bkz. vs_eod gerekçesi).
        "sim_fill": sim_fill, "qty": qty, "risk_dollars": risk_dollars,
        "stop": plan.get("stop"), "target": plan.get("profit_target"),
        "gates": gates, "gate_inputs_as_of": kaynak,
        "status": "would_submit" if engel is None else f"blocked:{engel}",
        # ÜÇ DAMGA (intraday_cycle ile aynı desen): as_of >= close_ts sonradan denetlenebilir.
        "decision_as_of": as_of.isoformat(), "bar_t": bar.get("t"),
        "close_ts": ct.isoformat() if ct else None,
    }
    store.append_jsonl(ORDERS_FILE, satir)
    _SEEN.add((plan_id, session))
    obs.log("intraday_shadow_order", ticker=ticker, plan_id=plan_id, status=satir["status"],
            qty=qty, sim_price=sim_price, detail="GÖLGE — emir gönderilmedi")
    return satir


def vs_eod(limit: int = 10, rows: list[dict] | None = None) -> dict:
    """OKUMA-ZAMANLI KIYAS: gölge kararı ile GERÇEK EOD dolgusu arasındaki fark.

    Kanıt sorusu: "intraday icra açık olsaydı, ertesi-açılış dolgusuna göre farkı ne olurdu?"
    Eşleşme `plan_id` üzerinden; EOD tarafı kapanmış işlemlerden (trades.jsonl) ve hâlâ açık
    pozisyonlardan (portfolio.json) okunur — pozisyon açıkken de kıyas yapılabilmeli.

    NEDEN `sim_fill` (sim_price DEĞİL): `trades.jsonl.entry` = `pos.entry`, yani slipaj ve katılım
    etkisi İÇİNDE olan dolum fiyatıdır. Onu gölgenin friksiyon ÖNCESİ referansıyla kıyaslamak, her
    satıra slipaj kadar sabit bir sapma eker ve "intraday erken girdi" gibi okunurdu — ölçülen şey
    zamanlama farkı değil, muhasebe farkı olurdu. İki taraf da friksiyon SONRASI karşılaştırılır.

    Eşleşmeyen satır `n_unpaired`e girer; sebebine (kapı reddetti / plan hiç dolmadı / başka fiyat)
    GİRİLMEZ — ölçülemeyen ölçülmemiş kalır.

    `rows` verilirse defter YENİDEN okunmaz: api tek istekte hem özeti hem kıyası derler ve iki
    okuma arasında dosyaya düşen bir satır yüzünden aynı yanıtta iki farklı gerçek belirmez."""
    ham = store.read_jsonl(ORDERS_FILE) if rows is None else rows
    rows = [r for r in ham if r.get("status") == "would_submit"]
    eod: dict = {}
    for tr in store.read_jsonl("trades.jsonl"):
        pid, e = tr.get("plan_id"), tr.get("entry")
        if pid and e is not None:
            eod[pid] = float(e)
    pf = store.read_json(PORTFOLIO, {}) or {}
    for p in (pf.get("positions") or {}).values():
        pid, e = p.get("plan_id"), p.get("entry")
        if pid and e is not None:
            eod.setdefault(pid, float(e))

    pairs, unpaired = [], 0
    for r in rows:
        pid, sf = r.get("plan_id"), r.get("sim_fill")
        f = eod.get(pid)
        if f is None or not sf:
            unpaired += 1
            continue
        pairs.append({"plan_id": pid, "ticker": r.get("ticker"), "date": r.get("date"),
                      "sim_fill": sf, "eod_fill": f,
                      "delta_pct": round((f - sf) / sf * 100.0, 4)})
    mean = round(sum(p["delta_pct"] for p in pairs) / len(pairs), 4) if pairs else None
    return {"n_paired": len(pairs), "n_unpaired": unpaired,
            "mean_delta_pct": mean, "recent": pairs[-limit:]}


def summarize(rows: list[dict], limit: int = 12) -> dict:
    """Gölge defterinin pano özeti — satırları ÇAĞIRAN okur, bu fonksiyon yalnız derler.

    NEDEN DEFTERİ BURADA OKUMUYORUZ (2026-07-27): `intraday_cycle.health` ile aynı yasa —
    "kendi yazdığını kendi geri okuyan modül TÜKETİCİ SAYILMAZ" (codelaw.artifact_graph). Defteri
    dışarıdan okuyan api.py'dir; okuma orada kalırsa artefakt grafiği gerçek tüketiciyi görür.
    Buraya bir `read_jsonl` koymak, kanıtı kendi içine kapatıp yasayı statik olarak ihlal ederdi."""
    bugun = barclock.session_date()
    today_rows = [r for r in rows if r.get("date") == bugun]
    return {
        "enabled": ENABLED,
        "total": len(rows),
        "today_n": len(today_rows),
        "would_submit_n": sum(1 for r in today_rows if r.get("status") == "would_submit"),
        "blocked_n": sum(1 for r in today_rows if str(r.get("status", "")).startswith("blocked")),
        "today": list(reversed(today_rows))[:limit],
        "vs_eod": vs_eod(rows=rows),
    }
