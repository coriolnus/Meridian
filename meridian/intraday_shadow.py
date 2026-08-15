"""intraday_shadow.py — seans içinde tetiği kesilen planın TAM icra kararını ("emir çıkar mıydı, kaç lot, hangi fiyattan") kendi defterine ölçen gölge katmanı.

NE YAPAR. Bir eşik geçişi tek başına karar değildir — kapılar, boyutlandırma, likidite tavanı ve
gap korumaları emri tamamen iptal edebilir; "tetik N kez kesildi" cümlesi kaçının gerçek emre
dönüşeceğini söylemez. Bu modül tetik kesildiği anda KOPYA bir PaperBroker üzerinde üretimin
dolgu yasasını (broker.fill_entry) koşturur, tam kararı (kapılar + kaynakları, qty, risk,
sim dolum, ret sebebi) satır olarak üretir ve nesneyi atar. İKİ KOL vardır ve ikisi de
`_satir()`in TEK gövdesinden çıkar: `silahli` (silahlanmış planlar — satırı burası yazar) ve
`planli` (silahlanmamış GO/REVIEW planları — satır burada hesaplanır, yazımı `intraday_cycle`
yapar). Planli kol AYRI defterdedir: çıkış-ölçümü kilidi silahli defteri kol süzgeci olmadan
okur ve karışan planli satırlar o ölçümü "ölçülemedi"ye geriletirdi; silahli satırın şeması bu
yüzden bayt düzeyinde korunur (`kol` alanı bile eklenmez, etiketi okuma anında basılır).

KİLİT GİRİŞLER. `record` (silahli kol: hesapla + yaz), `planli_satir`/`planli_yazildi` (planli
kol: hesapla; satır DİSKE indikten SONRA işaretle — sıra bir karardır), `summarize` (pano özeti;
satırları çağıran okur), `vs_eod` (gölge sim_fill × gerçek EOD dolumu kıyası, friksiyon-sonrası),
`kollar`/`planli_kol_uretimi`/`golge_cf_eslestirme` (iki kolun saf okuma yüzeyi), `reset_dedup`.

YASALAR — GÖLGE KATMANI. SIFIR YETKİ: EMİR GÖNDERMEZ; gerçek icra bayrağıyla (state/INTRADAY_ARM)
hiçbir ilişkisi yoktur — bayrak kapalıyken de ölçer, çünkü ölçüm yetki değildir; canlı karara ve
canlı defterlere hiçbir yazım yolu çıkmaz. İKİNCİ HESAP YAZILMAZ: boyutlandırma/ret sebebi
üretimin kendi broker'ından okunur — ikinci kopya zamanla ayrışır ve defter EOD'yi değil KENDİNİ
ölçmeye başlar (loop import edilmez, `_load_broker` deseni salt-okunur yeniden kurulur). SİM
FİYAT SÖZLEŞMESİ satıra da yazılır: `sim_price = max(bar_open, entry_trigger)` — bar içi sıralama
OHLC'den bilinemez, sözleşme bilinçle muhafazakârdır (asla tetikten ucuza dolmaz). Plan başına
seansta TEK satır (dedup restart'a karşı diskten tazelenir); ölçülemeyen kapı girdisi fail-open
sayılmaz, adıyla engeller.

OKUR: portfolio.json (salt-okunur; `entry_law` yan tablosu dahil), heartbeat/data_quality,
trades.jsonl, counterfactuals.jsonl, bar CSV'leri.
YAZAR: yalnız `state/intraday_shadow_orders.jsonl` — bu dosyanın tek lağımı odur (statik testle
çakılı); planli defteri (`intraday_shadow_planli_orders.jsonl`) `intraday_cycle` yazar.
"""
from __future__ import annotations

import os
import re

from . import barclock, config, health, obs, store
from .backtest import _adv as _adv_causal
from .broker import PaperBroker, Position, derisk_mult, max_positions_at
from .score import START_EQUITY

# Varsayılan AÇIK: tek yan etkisi kendi defterine yazmaktır, hiçbir yetki taşımaz. Kapatma anahtarı
# yine de vardır — ölçüm bile olsa, operatör bir katmanı susturabilmelidir.
ENABLED = os.environ.get("MERIDIAN_SHADOW", "1") != "0"
# PLANLI KOLUN KENDİ ANAHTARI (kill#1/kill#2): "kol kapatılır — gözlem, icrayı
# yavaşlatamaz" ve "20 seansta < 10 dolum → yazım durur, defter kalır" cümlelerinin ikisi de bir
# KAPATMA yolu ister. `MERIDIAN_SHADOW=0` iki kolu birden susturur; bu anahtar YALNIZ yeni kolu
# kapatır ve silahli kol (EXE-2026-002'nin kanıt zinciri) çalışmaya devam eder.
PLANLI_ENABLED = os.environ.get("MERIDIAN_SHADOW_PLANLI", "1") != "0"

ORDERS_FILE = "intraday_shadow_orders.jsonl"
# PLANLI KOLUN DEFTERİ — silahli defterle KARIŞTIRILMAZ (gerekçe modül başlığında: EXE-2026-002'nin
# kill#4'ü). Yazan `intraday_cycle`, okuyan burası.
PLANLI_ORDERS_FILE = "intraday_shadow_planli_orders.jsonl"
PORTFOLIO = "portfolio.json"

# KOL ETİKETİ (`universe`): iki kolun her satırı bir kol adı taşır. `silahli`
# bugünkü davranıştır ve DEĞİŞMEDİ; etiket okuma anında basılır (bkz. `kollar`).
KOL_SILAHLI = "silahli"
KOL_PLANLI = "planli"

# (plan_id, seans) → yazıldı. PLAN BAŞINA SEANSTA TEK satır: tetik kesildikten sonra o barın
# high'ı eşiğin üstünde kaldığı sürece HER olayda yeniden geçiş görünür; her birine satır yazmak
# defteri aynı kararın kopyalarıyla şişirir ve "kaç emir çıkardı" sayımını yalanlardı.
_SEEN: set = set()
_SEEN_SESSION: str | None = None
# İKİ KOL, İKİ BELLEK: tek küme paylaşılsaydı aynı plan iki kolda da izlenebildiğinde (silahlanma
# seans içinde olabilir) ikinci kol sessizce hiç yazmazdı — ve o eksik, kolun "nadir" görünmesi
# olarak okunurdu (kill#2 tam bu sayıya bakıyor).
_SEEN_PLANLI: set = set()
_SEEN_PLANLI_SESSION: str | None = None


def reset_dedup() -> None:
    """Tekilleştirme belleğini boşalt (testler + seans dönüşü) — İKİ KOL BİRLİKTE."""
    global _SEEN, _SEEN_SESSION, _SEEN_PLANLI, _SEEN_PLANLI_SESSION
    _SEEN = set()
    _SEEN_SESSION = None
    _SEEN_PLANLI = set()
    _SEEN_PLANLI_SESSION = None


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


def _load_seen_planli(session: str) -> None:
    """`_load_seen`in planli kol karşılığı — AYNI gerekçe (restart dedup'ı sıfırlar, sayım şişer).

    DEFTERİ BURASI OKUR, YAZAN `intraday_cycle`dır: tekilleştirme yalnız RAM'de yaşarsa seans
    ortasındaki bir yeniden başlatma aynı planı ikinci kez yazdırır ve kartın BİRİNCİL ölçütü
    ("20 seansta ≥ 40 dolum") kendi kopyalarıyla dolar."""
    global _SEEN_PLANLI, _SEEN_PLANLI_SESSION
    if _SEEN_PLANLI_SESSION == session:
        return
    _SEEN_PLANLI = {(r.get("plan_id"), r.get("date")) for r in store.read_jsonl(PLANLI_ORDERS_FILE)
                    if r.get("date") == session}
    _SEEN_PLANLI_SESSION = session


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


def _yan_tablo_kaynagi(plan_id, lw: dict, alan: str, none_ek: str) -> str:
    """`entry_law` yan tablosundan gelen BİR icra girdisinin ÜÇ HÂLİ, ÜÇ AYRI CÜMLE.

    Üçlü-ayrım C18'de ATR için yazıldı ve gerekçesi bacağa özel değildir: bir KOPUKLUK (plan yan
    tabloda hiç yok — kablo kopmuş) ile MEŞRU bir ölçümsüzlük (girdi o gün hesaplanamadı) tek
    cümleye katlanırsa, operatör gölge defterinde kopmuş bir kabloyu göremez. Aynı yasa artık
    `pivot` ve `gap_at_submit` bacaklarında da geçerli — üç bacak için üç kopya cümle yazmak,
    yarın birinin diğerlerinden sessizce ayrışması demekti.

    `none_ek`: o bacağa ÖZGÜ sonuç cümlesi — "ölçülemedi" hepsinde aynı şey İFADE ETMEZ (ATR'de
    limit gevşer, pivotta erken itlaf ateşlemez, gap'te veto ateşlemez) ve satırı okuyanın bilmesi
    gereken şey tam olarak bu farktır."""
    if not lw:
        return (f"{PORTFOLIO}.entry_law'da bu plan için satır YOK — {alan.upper()} ÖLÇÜLEMEDİ "
                f"(tohumlanmış defter ya da yasa öncesi silahlanmış plan)")
    if lw.get(alan) is None:
        return f"{PORTFOLIO}.entry_law[{plan_id}] var ama `{alan}` None — {none_ek}"
    return f"{PORTFOLIO}.entry_law[{plan_id}] — silahlanma anında sabitlendi"


def _kimlik(plan: dict) -> tuple | None:
    """(plan_id, TICKER) ya da None — kimliksiz plan İKİ KOLDA DA yazılmaz, aynı cümleyle.

    İki kol için iki kopya kimlik kontrolü yazmak, yarın birinin diğerinden sessizce ayrışması
    demekti (bu modülün başlığındaki "iki hesap zamanla AYRIŞIR" dersinin küçük hâli)."""
    plan_id = plan.get("id")
    ticker = str(plan.get("ticker") or "").upper()
    if not plan_id or not ticker:
        obs.warn("shadow_plan_kimliksiz", ticker=ticker or None,
                 detail="plan_id/ticker yok — gölge satırı EOD ile eşleştirilemezdi, yazılmadı")
        return None
    return plan_id, ticker


def _satir(plan: dict, plan_id, ticker: str, bar: dict, as_of, session: str, kol: str) -> dict | None:
    """İKİ KOLUN ORTAK GÖVDESİ: tam icra kararını hesapla ve SATIRI DÖNDÜR (yazmaz).

    KOL FARKI YALNIZ ETİKETTİR. Kapılar, boyutlandırma, ADV penceresi, `entry_law` yan tablosu ve
    en önemlisi `sim_price = max(bar_open, entry_trigger)` iki kolda BİREBİR aynıdır — çünkü tek
    gövde. Kartın sözü ("iki kolda birebir aynı kural") burada bir söz değil, YAPIDIR: ikinci bir
    gövde yazılsaydı iki kol zamanla ayrışır ve kol karşılaştırması ölçtüğünü sandığı şeyi (nüfus
    farkını) değil, iki kod yolunun farkını ölçerdi.

    `kol == KOL_SILAHLI` iken satır BUGÜNKÜ hâliyle, TEK BİR ALAN BİLE EKLENMEDEN döner (kart
    kill#3: silahli kolun şemasında/sayımında HERHANGİ bir fark → geri alınır). Etiket yalnız yeni
    kola yazılır; silahli kolun etiketi okuma anında basılır (`kollar`)."""
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

    # C18 — E1 GİRİŞ YASASININ ATR BACAĞI. ÖNCESİ: `fill_entry`e `atr=` HİÇ
    # geçmiyordu → limit DAİMA %1 yüzde tavanındaydı, canlı EOD motoru ise min(0,5·ATR14, %1) ile
    # koşuyordu. Kırılma TEK YÖNLÜ: gölge, canlının REDDEDECEĞİ dolumları "would_submit" diye yazar
    # → Faz 4b'nin kanıt tabanı (bu defterin varlık sebebi) iyimser bir icra modeli üzerine kurulur.
    # ATR BURADA YENİDEN HESAPLANMAZ — `_copy_broker`ın zaten okuduğu portfolio.json'daki
    # `entry_law` yan tablosundan gelir. O tablo SİLAHLANMA ANINDA (sinyal barı kapanışı)
    # loop.py tarafından yazılır ve `_save_broker` ile restart'ı atlatır. İkinci bir ATR hesabı
    # tam olarak bu modülün başlığındaki hatanın kendisi olurdu: "iki hesap zamanla AYRIŞIR ve
    # gölge defteri EOD'yi değil KENDİNİ ölçmeye başlar".
    # Yan tabloda satır yoksa (eski silahlı plan / tohumlanmış defter) None KALIR = "ölçülemedi":
    # limit yalnız yüzde tavanıyla kurulur ve satır bunu `atr_kaynak` ile BEYAN eder — uydurma ATR
    # yok, sessiz varsayım da yok.
    _lw = (meta.get("entry_law") or {}).get(plan_id) or {}
    atr_icra = _lw.get("atr")
    # ÜÇ HÂL, ÜÇ CÜMLE — ikisini birleştirmek "ölçülemedi"yi "tablo yok" ile karıştırırdı ve bir
    # KOPUKLUK (plan yan tabloda hiç yok) ile MEŞRU bir ölçümsüzlük (ATR o gün hesaplanamadı)
    # okuyucuya aynı görünürdü.
    atr_kaynak = _yan_tablo_kaynagi(
        plan_id, _lw, "atr",
        "silahlanma anında ÖLÇÜLEMEDİ; limit yalnız yüzde tavanıyla kuruldu")

    # ---- AYNI YAN TABLONUN OKUNMAYAN İKİ BACAĞI -----------------------------------------------
    # C18 ATR'yi bağladı; `entry_law` satırı ise ÜÇ icra girdisi taşıyor. Kalan ikisi burada
    # okunmuyordu ve ikisinin kırılma sınıfı AYRI:
    #
    #   * `gap_at_submit` — ÖLÇÜM DEĞİŞTİRİR, C18'in ATR bacağıyla BİREBİR aynı yönde. `cancel`
    #     grid noktasında canlı iki motor da girmez (`fill_entry` EV_GAP_VETO ile reddeder);
    #     gölge, argümanı hiç geçirmediği için None ile koşuyordu, yani veto ateşlemiyordu ve
    #     canlının REDDEDECEĞİ dolumları `would_submit` diye yazıyordu. Faz 4b'nin kanıt tabanı
    #     yine iyimser bir icra modeli üzerine kurulurdu — bu defterin varlık sebebine aykırı.
    #     BUGÜNKÜ YÜRÜRLÜKTEKİ NOKTA `marketable_limit` (goal.yaml execution_v2), yani bugün
    #     davranış farkı SIFIR; kırılma grid `cancel`a çevrildiği gün SESSİZCE açılırdı — düzeltme
    #     o güne ertelenirse ölçüm bozulduğu gün fark edilmez.
    #
    #   * `pivot` — bugün `fill_entry`in HÜKMÜNÜ DEĞİŞTİRMEZ ve bu böyle YAZILIYOR (uydurma yasağı:
    #     bağlanan her bacak "kaçan dolum" bulur diye sunulamaz). Yalnız `Position.pivot` alanına
    #     düşer, gölge de kopya broker'ı atar. Yine de geçirilir, İKİ SEBEPLE: (1) çağrı canlı
    #     `loop.py:820` ile ARGÜMAN ARGÜMAN aynı olur — C13'ün kapattığı kopukluk ("replay taşıyor,
    #     canlı taşımıyor → knob terfi edince bir motorda SESSİZ NO-OP") tam olarak bir motorun
    #     eksik argümanla çağrılmasından doğmuştu ve gölge o listede kalan son motordu;
    #     (2) yapı çizgisi satıra yazılır — hangi girdiyle karar verildiği, kararın kendisi kadar
    #     önemlidir (bkz. `_gates`).
    pivot_icra = _lw.get("pivot")
    gap_icra = _lw.get("gap_at_submit")
    pivot_kaynak = _yan_tablo_kaynagi(
        plan_id, _lw, "pivot",
        "silahlanma anında pivot ÖLÇÜLEMEDİ (0'dan büyük değildi); `fill_entry`e 0.0 gider = "
        "'bilinmiyor' → `early_kill_pivot` ateşlemez")
    gap_kaynak = _yan_tablo_kaynagi(
        plan_id, _lw, "gap_at_submit",
        "GÖNDERİM ANI kaydı yok; gap-risk vetosu ateşlemez — beyan edilmiş kapsam farkı "
        "(broker.fill_entry: None = 'bu motorda gönderim anı YOK'), sessiz bir 'gap yoktu' değil")

    qty = risk_dollars = sim_fill = None
    red_nedeni = None
    if engel is None:
        # KOPYA broker üzerinde GERÇEK boyutlandırma: aynı fonksiyon, aynı korumalar.
        _rej: dict = {}
        pos = b.fill_entry(plan, sim_price, as_of.isoformat(), b.equity(),
                           size_mult=gates["size_mult"], adv=_daily_adv(ticker, session),
                           atr=atr_icra,
                           # `pivot or 0.0` = canlı loop.py:823 ile BİREBİR aynı ifade; 0.0 orada da
                           # "bilinmiyor" demektir (broker.fill_entry docstring'i).
                           pivot=float(pivot_icra or 0.0),
                           # None BİLEREK None kalır: `False`a çevirmek "gap YOKTU" iddiasını
                           # uydurmak olurdu, oysa hâl "gönderim anı ölçülmedi"dir.
                           gap_at_submit=gap_icra, reject_out=_rej)
        if pos is None:
            # fill_entry'nin ret sebebini (gap / stop-altı açılış / likidite / notional) DIŞARIDA
            # yeniden hesaplamıyoruz: o mantığın ikinci kopyası zamanla ayrışır ve gölge defteri
            # EOD'yi değil kendini ölçmeye başlar. Sürüklenme riski > teşhis değeri.
            # C18: ama artık BROKER'IN KENDİSİ sebebi söylüyor (`reject_out`) — bu bir ikinci kopya
            # DEĞİL, aynı hesabın çıktısıdır ve satıra `red_nedeni` olarak yazılır. `status` jetonu
            # BİLEREK `broker_kurali` kalır: pano (app.js SH_TR) sabit bir jeton sözlüğü çeviriyor
            # ve yeni jeton orada çevrilmeden ham görünürdü — teşhis ayrı alanda, sınıf yerinde.
            engel = "broker_kurali"
            red_nedeni = _rej.get("reason")
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
        # C18: hangi ATR ile ve NEREDEN gelen bir limitle karar verildiği satırda durur — bir
        # kapının hangi girdiyle değerlendirildiği, kapının kendisi kadar önemlidir (bkz. `_gates`).
        "atr": atr_icra, "limit": _lw.get("limit"), "atr_kaynak": atr_kaynak,
        # Yan tablonun diğer iki icra girdisi de satırda durur —
        # `atr`/`atr_kaynak` ile AYNI desen, aynı gerekçe. JETON ADLARI DEĞİŞMEZ: `status` hâlâ
        # `would_submit`/`blocked:*` sözlüğünden gelir (pano app.js SH_TR sabit bir jeton sözlüğü
        # çeviriyor; yeni jeton orada çevrilmeden ham görünürdü — C18'in kararı, aynen korunuyor).
        "pivot": pivot_icra, "pivot_kaynak": pivot_kaynak,
        "gap_at_submit": gap_icra, "gap_at_submit_kaynak": gap_kaynak,
        "red_nedeni": red_nedeni,
        "gates": gates, "gate_inputs_as_of": kaynak,
        "status": "would_submit" if engel is None else f"blocked:{engel}",
        # ÜÇ DAMGA (intraday_cycle ile aynı desen): as_of >= close_ts sonradan denetlenebilir.
        "decision_as_of": as_of.isoformat(), "bar_t": bar.get("t"),
        "close_ts": ct.isoformat() if ct else None,
    }
    # ETİKET YALNIZ YENİ KOLA (kill#3). Silahli kolun sözlüğü buraya kadar bayt bayt eskisidir ve
    # öyle kalır; `kol` anahtarını ona da eklemek "şemada fark yok" iddiasını çürütürdü.
    if kol != KOL_SILAHLI:
        satir["kol"] = kol
    return satir


def record(plan: dict, bar: dict, as_of) -> dict | None:
    """SİLAHLI KOL — tetik kesildiği ANDA tam icra kararını hesapla ve deftere yaz. HİÇBİR ŞEY
    GÖNDERMEZ.

    `plan`/`bar`/`as_of` intraday_cycle'ın ZATEN ölçtüğü üçlüdür — look-ahead mantığı burada İKİNCİ
    kez yazılmaz (aynı admissible bar, aynı karar anı). Dönüş: yazılan satır ya da None (kapalı /
    tekrar / biçimsiz girdi).

    DAVRANIŞI DEĞİŞMEDİ: gövde `_satir`e taşındı, sıra (kapalı → kimlik → seans → dedup →
    biçim → hesap → yazım → sayaç → log) korundu ve yazılan satır BAYT olarak aynıdır (çivisi:
    tests/test_golge_planli_kol_v217.py, değişiklikten ÖNCE alınmış altın satır)."""
    if not ENABLED:
        return None
    kimlik = _kimlik(plan)
    if kimlik is None:
        return None
    plan_id, ticker = kimlik
    session = barclock.session_date(as_of)
    _load_seen(session)
    if (plan_id, session) in _SEEN:
        return None
    satir = _satir(plan, plan_id, ticker, bar, as_of, session, KOL_SILAHLI)
    if satir is None:
        return None
    store.append_jsonl(ORDERS_FILE, satir)
    _SEEN.add((plan_id, session))
    obs.log("intraday_shadow_order", ticker=ticker, plan_id=plan_id, status=satir["status"],
            qty=satir["qty"], sim_price=satir["sim_price"], detail="GÖLGE — emir gönderilmedi")
    return satir


def planli_satir(plan: dict, bar: dict, as_of) -> dict | None:
    """PLANLI KOL — satırı HESAPLAR, YAZMAZ.

    Silahlanmamış (GO/REVIEW ama `portfolio.json.armed` dışındaki) bir planın tetiği seans içinde
    kesildiğinde "ne olurdu"yu ölçer. SIFIR EK PAZAR RİSKİ: silahlanmamış bir plan bu satır
    yüzünden silahlanmaz, emir üretmez, hiçbir bayrağa dokunmaz — ölçüm yetki değildir.

    NEDEN YAZMIYOR: yazım `intraday_cycle`dadır (gerekçe modül başlığında — bu dosyanın TEK
    lağımı `ORDERS_FILE`dır ve o çivi silahli kolun bayt-değişmezliğinin bir parçasıdır). Çağıran
    sözleşmesi İKİ ADIMDIR ve sırası ÖNEMLİDİR: satır DİSKE indikten SONRA `planli_yazildi(satir)`.
    Ters sırada bir yazım hatası planı "yazılmış" sayardı ve o plan o seans bir daha denenmezdi.

    Dönüş: yazılacak satır, ya da None (kol kapalı / gölge kapalı / bu seans zaten yazıldı /
    biçimsiz girdi)."""
    if not (ENABLED and PLANLI_ENABLED):
        return None
    kimlik = _kimlik(plan)
    if kimlik is None:
        return None
    plan_id, ticker = kimlik
    session = barclock.session_date(as_of)
    _load_seen_planli(session)
    if (plan_id, session) in _SEEN_PLANLI:
        return None
    return _satir(plan, plan_id, ticker, bar, as_of, session, KOL_PLANLI)


def planli_yazildi(satir: dict) -> None:
    """Planli satır DİSKE indi: tekilleştirmeyi işaretle + görünür kıl.

    Ayrı fonksiyon, çünkü sıra bir karardır: `planli_satir` hesaplar, çağıran yazar, burası
    işaretler. Yazım düşerse işaret de düşmez ve plan bir sonraki barda yeniden denenir."""
    _SEEN_PLANLI.add((satir.get("plan_id"), satir.get("date")))
    obs.log("intraday_shadow_planli_order", ticker=satir.get("ticker"),
            plan_id=satir.get("plan_id"), status=satir.get("status"), qty=satir.get("qty"),
            sim_price=satir.get("sim_price"), kol=satir.get("kol"),
            detail="GÖLGE (planli kol) — plan SİLAHLANMADI, emir gönderilmedi")


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

    NEDEN DEFTERİ BURADA OKUMUYORUZ: `intraday_cycle.health` ile aynı yasa —
    "kendi yazdığını kendi geri okuyan modül TÜKETİCİ SAYILMAZ" (codelaw.artifact_graph). Defteri
    dışarıdan okuyan api.py'dir; okuma orada kalırsa artefakt grafiği gerçek tüketiciyi görür.
    Buraya bir `read_jsonl` koymak, kanıtı kendi içine kapatıp yasayı statik olarak ihlal ederdi.

    PLANLI KOL BURAYA GİRMEZ (bilerek): bu özet `/api/diagnostics` → panonun 4b kartıdır ve
    `total`/`today_n`/`would_submit_n` sayıları SİLAHLI kolun sayımıdır. Yeni kolu bu sözlüğe
    katmak kartın kill#3'ünü ("silahli kolun ... SAYIMINDA herhangi bir fark") ihlal eder ve
    panodaki "gölge kararı" satırı sessizce anlam değiştirirdi. Planli kolun raporu ayrı yüzeydedir
    (`planli_kol_uretimi` / `golge_cf_eslestirme`)."""
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


# ==================================================================================================
# İKİ KOL — OKUMA YÜZEYİ
# ==================================================================================================
# Aşağısı SAF OKUMADIR: hiçbir dosyaya yazmaz, hiçbir bayrağa dokunmaz, Faz-5 kilidine BAĞLANMAZ.
KART = "EXE-2026-003"
CF_DEFTERI = "counterfactuals.jsonl"

# KART SABİTLERİ — ölçümden ÖNCE donduruldu, kod bunları değiştiremez.
IKINCIL_N_MIN = 40           # ikincil hattın asgari eşleşmiş çifti (EXE-2026-002'nin İKİ KATI)
IKINCIL_CI = 0.95
PLANLI_PENCERE_SEANS = 20    # BİRİNCİL ölçütün penceresi
PLANLI_HEDEF_DOLUM = 40      # "20 seansta ≥ 40 gölge dolumu"
PLANLI_KILL_DOLUM = 10       # kill#2: "20 seansta < 10 dolum → kol arşivlenir"
AD_TAVANI = 50               # ad listelerinin BEYANLI tavanı; sayaçlar hep TAM (faz5_cikis deseni)

# `P-{gün}-{ticker}…` — plan kimliği gölge ile cf arasındaki TEK ortak çapadır (aşağıda gerekçe).
_PLAN_ID_RE = re.compile(r"^P-(\d{4}-\d{2}-\d{2})-(.+)$")


def kollar(silahli: list[dict] | None = None, planli: list[dict] | None = None) -> dict:
    """İKİ KOLUN SATIRLARI TEK LİSTEDE — HER SATIRDA ZORUNLU `kol` ETİKETİ.

    Silahli kolun defterine `kol` alanı YAZILMADI (kart kill#3: şemada fark yok) — etiket TAM
    BURADA, okuma anında basılır. Yani "kol etiketi zorunludur" cümlesi kolların KARŞILAŞTIRILDIĞI
    yüzeyde tutulur, silahli kolun diskteki satırı ise bayt bayt eskisi kalır.

    ETİKETSİZ SATIR UYDURULMAZ: planli defterde `kol` taşımayan bir satır bulunursa (elle
    tohumlanmış ya da yazımı yarım kalmış) `etiketsiz` kovasına ADIYLA girer ve evrene ALINMAZ —
    "herhalde planlidir" demek, kolun nüfusunu uydurmak olurdu."""
    ham_s = store.read_jsonl(ORDERS_FILE) if silahli is None else list(silahli)
    ham_p = store.read_jsonl(PLANLI_ORDERS_FILE) if planli is None else list(planli)
    satirlar = [{**r, "kol": KOL_SILAHLI} for r in ham_s]
    etiketsiz = []
    for r in ham_p:
        if r.get("kol") != KOL_PLANLI:
            etiketsiz.append(f"{r.get('plan_id') or '?'}·{r.get('date') or '?'}")
            continue
        satirlar.append(dict(r))
    return {"satirlar": satirlar, "etiketsiz": etiketsiz[:AD_TAVANI],
            "etiketsiz_n": len(etiketsiz),
            "n": {KOL_SILAHLI: len(ham_s), KOL_PLANLI: len(ham_p) - len(etiketsiz)},
            "defterler": {KOL_SILAHLI: f"state/{ORDERS_FILE}",
                          KOL_PLANLI: f"state/{PLANLI_ORDERS_FILE}"}}


def planli_kol_uretimi(planli: list[dict] | None = None) -> dict:
    """BİRİNCİL ÖLÇÜT (kart): planli kol PENCEREDE kaç gölge DOLUMU üretti?

    "Dolum" = `status == "would_submit"` (kapıda bloklanan satır bir dolum DEĞİLDİR; onu saymak
    kolun verimini şişirirdi). Pencere SEANS sayılır, takvim günü değil: defterde 20 ayrı seans
    yoksa hüküm `olculemedi`dir — 12 seansta 8 dolum görüp "kill#2 ateşledi" demek, dolmamış bir
    pencereden hüküm çıkarmak olurdu."""
    rows = store.read_jsonl(PLANLI_ORDERS_FILE) if planli is None else list(planli)
    seanslar = sorted({r.get("date") for r in rows if r.get("date")})
    pencere = set(seanslar[-PLANLI_PENCERE_SEANS:])
    dolum = [r for r in rows if r.get("date") in pencere and r.get("status") == "would_submit"]
    tam = len(seanslar) >= PLANLI_PENCERE_SEANS
    n = len(dolum)
    if not tam:
        hukum = (f"PENCERE DOLMADI ({len(seanslar)}/{PLANLI_PENCERE_SEANS} seans) — kartın "
                 f"birincil ölçütü de kill#2 de bu pencereye bakar; şu ana kadar {n} dolum")
    elif n < PLANLI_KILL_DOLUM:
        hukum = (f"KILL#2 — {PLANLI_PENCERE_SEANS} seansta {n} dolum < {PLANLI_KILL_DOLUM}: "
                 "tetik-kesme planlı planlarda nadir; kol düşük değerli, ARŞİVLENİR "
                 "(yazım durur, defter kalır)")
    elif n < PLANLI_HEDEF_DOLUM:
        hukum = (f"ÖLÇÜLDÜ — {n}/{PLANLI_HEDEF_DOLUM} dolum: kol yaşıyor ama kartın birincil "
                 "hedefi henüz dolmadı")
    else:
        hukum = f"ÖLÇÜLDÜ — birincil hedef doldu ({n} ≥ {PLANLI_HEDEF_DOLUM})"
    return {"kart": KART, "pencere_seans": PLANLI_PENCERE_SEANS, "seans_n": len(seanslar),
            "pencere_tam_mi": tam, "dolum_n": n, "satir_n": len(rows),
            "hedef": PLANLI_HEDEF_DOLUM, "kill_esigi": PLANLI_KILL_DOLUM,
            "durum": "olculdu" if tam else "olculemedi", "hukum": hukum}


def _plan_tarihi(plan_id) -> str | None:
    """`P-YYYY-AA-GG-TICKER…` → plan tarihi. Çözülemezse None (uydurma yok).

    NEDEN GEREKLİ: gölge satırının `date`i TETİĞİN KESİLDİĞİ SEANSTIR, cf satırının `date`i ise
    PLANIN KURULDUĞU gündür (planlar kapanışta kurulur, ertesi açılışta dolar). İkisini doğrudan
    eşleştirmek satırların neredeyse tamamını bir gün kaydırır ve "eşleşme yok" diye okunurdu."""
    m = _PLAN_ID_RE.match(str(plan_id or ""))
    return m.group(1) if m else None


def _cf_dizini(cf_rows: list[dict]) -> dict:
    """(plan_tarihi, TICKER) → cf satırları. Yalnız GİRİŞ DOLUMU ölçülmüş satırlar.

    cf defteri giriş dolumunu simüle eder; `no_fill_gap`/`no_fill_gap_stop` satırlarında `entry`
    YOKTUR (counterfactual._resolve: yalnız `entered` satırlar fiyat taşır). Onları 0 saymak ya da
    atlamak aynı şey değildir: atlanırsa eşleşmeyen kovasında ADIYLA görünür, 0 sayılsaydı ölçüme
    uydurma bir fiyat girerdi."""
    out: dict = {}
    for r in cf_rows:
        d, tk = r.get("date"), str(r.get("ticker") or "").upper()
        if not d or not tk:
            continue
        out.setdefault((str(d), tk), []).append(r)
    return out


def _cf_sec(adaylar: list[dict], trigger) -> tuple:
    """Aynı (gün, ticker) altındaki cf satırlarından PLAN satırını seç → (satır, neden).

    Aynı anahtarda üç sınıf birden olabilir: gerçek plan, `DORMANT` (uyuyan kurulum) ve `NEAR_MISS`
    (eşik-altı). Gölge satırı GERÇEK plandan doğdu, o yüzden karşılığı da gerçek plan satırıdır.

    İKİNCİ ELEK — `entry_trigger`. Ölçüldü (canlı korpus, 7161 satır): yalnız (gün, ticker) ile
    eşleştirince örneklemin ~%13'ü BELİRSİZ kalıyor, çünkü aynı gün aynı ticker İKİ KURULUMDAN
    (setup) plan üretebiliyor ve ikisi de doluyor. Eşik fiyatı iki tarafta da YAZILI ve iki kolda
    da AYNI alandır (`entry_trigger`) — yani ayrım şema değişikliği istemez. `setup` alanını gölge
    satırına eklemek de bir seçenekti ve REDDEDİLDİ: silahli kolun şemasına alan eklemek kartın
    kill#3'üdür, yalnız planli kola eklemek ise iki kolu farklı anahtarlarla eşleştirmek olurdu.

    Eleme sonrası hâlâ birden fazla aday kalırsa ÖLÇÜLEMEDİ denir — "ilkini al" demek, hangi
    kurulumun fiyatıyla kıyasladığını bilmeden bir sayı yazmak olurdu."""
    gercek = [r for r in adaylar
              if not r.get("near_miss") and not r.get("dormant")
              and str(r.get("verdict") or "") not in ("DORMANT", "NEAR_MISS")]
    if not gercek:
        return None, "cf defterinde plan satırı yok (yalnız uyuyan/eşik-altı kayıt)"
    dolan = [r for r in gercek if r.get("entry") is not None]
    if not dolan:
        return None, (f"cf satırı var ama GİRİŞ DOLUMU yok (status="
                      f"{gercek[0].get('status')!r}) — no_fill sınıfı, kıyas paydası kurulamaz")
    if len(dolan) > 1 and trigger is not None:
        try:
            esik = [r for r in dolan if abs(float(r.get("entry_trigger")) - float(trigger)) < 1e-6]
        except (TypeError, ValueError):  # sessiz-yutma: bir adayın eşiği okunamıyor — ikinci elek UYGULANMAZ, aday kümesi olduğu gibi kalır ve aşağıdaki belirsizlik dalı adıyla raporlar
            esik = []
        if len(esik) == 1:
            return esik[0], None
        if esik:
            dolan = esik
    if len(dolan) > 1:
        # ÖLÇÜM-ÖZDEŞ BELİRSİZLİK, BELİRSİZLİK DEĞİLDİR. Canlı korpusta ölçüldü: çok-adaylı 157
        # anahtarın 157'sinde iki satır AYNI sinyalin iki kurulum adı altındaki kopyasıdır
        # (`breakout_vcp` + `momentum_burst`), `entry_trigger` ve `entry` BİREBİR aynıdır. Hangi
        # satırın seçildiği `kazanc_bps`i DEĞİŞTİRMEZ, o yüzden ölçüm kurulabilir. Fiyatlar
        # AYRIŞIYORSA seçim ölçümü değiştirir ve o zaman ölçülemedi denir — aday sayısı çiftin
        # üstünde `cf_aday_n` olarak durur, yani belirsizlik gizlenmez, ADLANDIRILIR.
        try:
            fiyatlar = {round(float(r["entry"]), 6) for r in dolan}
        except (TypeError, ValueError):  # sessiz-yutma: bir adayın fiyatı okunamıyor — "hepsi aynı" iddiası kurulamaz, aşağıdaki belirsizlik dalına düşer ve adıyla raporlanır
            fiyatlar = {None, False}
        if len(fiyatlar) > 1:
            return None, (f"aynı (gün, ticker) altında {len(dolan)} dolmuş cf satırı FARKLI giriş "
                          "fiyatlarıyla — hangi kurulumla kıyaslandığı bilinmeden sayı yazılamaz, "
                          "eşleşme BELİRSİZ")
    return dolan[0], None


def golge_cf_eslestirme(satirlar: list[dict] | None = None,
                        cf_rows: list[dict] | None = None) -> dict:
    """İKİNCİL HAT: gölge dakika-sim × cf EOD-sim eşleştirilmiş farkı.

    FAZ-5 KİLİDİNİ AÇMAZ VE KİLİT KODUNA DOKUNMAZ. Kilidin hükmü `faz5_cikis.cikis_olcumu`ta,
    GERÇEK-ÇİFT hattında yaşar ve o hat YALNIZ silahli kolun defterini okur. Burası ayrı bir rapor
    alanıdır: destekleyici kanıt üretir, hüküm vermez. Kartın açık sınırı (Rol-1'in kendi
    düzeltmesi): silahlanmamış planın GERÇEK iç dolumu yoktur, o yüzden bu hat EXE-2026-002'nin
    n_min'ini DOLDURAMAZ.

    FORMÜL KARTTAN, BİREBİR:  kazanc_bps = (cf_giris − golge_sim_fill) / cf_giris × 10⁴

    İŞARET TERİMİ YOK — VE BU BİR EKSİKLİK DEĞİL, ÖLÇÜLMÜŞ BİR SINIR. `faz5_cikis` kısa tarafta
    işareti çevirir çünkü iç EOD defteri `side` taşır. cf defterinde `side` alanı HİÇ YOKTUR
    (counterfactual._push) ve kartın formülünde de işaret terimi yoktur; formül olduğu gibi
    uygulanır ve sınır satırda BEYAN EDİLİR. Bugün canlı yol yalnız long üretiyor (loop.py:1374),
    ama bu varsayım koda gömülmez — cf defterine `side` geldiği gün burası da düzeltilmelidir.

    EŞLEŞME ANAHTARI (kart: `plan_id`) — cf tarafında `plan_id` ALANI YOKTUR (ölçüldü: 0 kayıt).
    Kimlikler aynı ikiliden türer: plan `P-{gün}-{ticker}`, cf `CF-{gün}-{ticker}-{setup}`. Bu
    yüzden anahtar plan_id'DEN ÇÖZÜLÜR: (plan tarihi, ticker). Ayrıştırılamayan plan_id eşleşmez
    sayılır ve adıyla raporlanır.

    ARALIK: `faz5_cikis.tarih_kumeli_bootstrap` — İKİNCİ BİR GÖVDE YAZILMADI. Aynı seansta dolan
    planlar aynı açılışı paylaşır; düz (IID) bootstrap aralığı daraltır ve hep "daha anlamlı"
    yönde yanılır. İki hattın aralığı aynı gövdeden çıkmazsa iki sayı zamanla ayrışır ve kartın
    "iki hat UYUŞUYOR mu" sorusu ölçüm farkını gerçek fark sanardı.
    GEÇ IMPORT: `faz5_cikis` gölge defterinin adını bu modülden alıyor (`_golge_defteri`); modül
    düzeyinde bağlamak ithal grafiğinde halka kurardı."""
    from .faz5_cikis import BOOTSTRAP_N, tarih_kumeli_bootstrap

    if satirlar is None:
        satirlar = kollar()["satirlar"]
    ham_cf = store.read_jsonl(CF_DEFTERI) if cf_rows is None else list(cf_rows)
    evren = [r for r in satirlar if r.get("sim_fill") is not None]
    dizin = _cf_dizini(ham_cf)

    sinir = ("İKİ SİMÜLASYON karşılaştırması (gölge dakika-sim × cf EOD-sim): ölçülen ZAMANLAMA "
             "etkisidir, gerçek icra kalitesi değil. cf defterinde `side` yok — kart formülü "
             "işaretsiz uygulanır (bugün canlı yol yalnız long üretiyor, ama bu varsayım koda "
             "gömülmedi). Bu hat FAZ-5 KİLİDİNİ AÇMAZ.")
    ortak = {"kart": KART, "kilidi_acmaz": True, "n_min": IKINCIL_N_MIN, "seviye": IKINCIL_CI,
             "n_golge": len(satirlar), "n_evren": len(evren), "n_cf": len(ham_cf),
             "kaynaklar": {"golge_silahli": f"state/{ORDERS_FILE}",
                           "golge_planli": f"state/{PLANLI_ORDERS_FILE}",
                           "cf": f"state/{CF_DEFTERI}"},
             "formul": "kazanc_bps = (cf_giris − golge_sim_fill) / cf_giris × 10000",
             "bootstrap": f"tarih-kümeli (faz5_cikis.tarih_kumeli_bootstrap) · B={BOOTSTRAP_N}",
             "sinir": sinir}

    if not evren:
        return {**ortak, "durum": "olculemedi", "kollar": None, "toplam": None, "eslesmeyen": None,
                "neden": ("gölge defterlerinde DOLUM ÜRETMİŞ satır YOK — eşleştirilmiş fark "
                          "ÖLÇÜLEMEDİ (sıfır çift 'kazanç 0 bps' DEĞİLDİR)")}
    if not ham_cf:
        return {**ortak, "durum": "olculemedi", "kollar": None, "toplam": None, "eslesmeyen": None,
                "neden": (f"cf defteri (state/{CF_DEFTERI}) BOŞ ya da yok — ikincil hattın karşı "
                          "bacağı ÖLÇÜLEMEDİ; gölge tarafı tek başına bir fark üretemez")}

    ciftler, eslesmeyen = [], []
    for r in evren:
        pid = r.get("plan_id")
        ad = f"{pid or '?'}·{r.get('date') or '?'}·{r.get('kol') or '?'}"
        pd_ = _plan_tarihi(pid)
        if pd_ is None:
            eslesmeyen.append({"ad": ad, "sinif": "plan_id_cozulemedi",
                               "neden": f"plan_id `P-GG-TICKER` biçiminde değil: {pid!r}"})
            continue
        adaylar = dizin.get((pd_, str(r.get("ticker") or "").upper()))
        if not adaylar:
            eslesmeyen.append({"ad": ad, "sinif": "cf_yok",
                               "neden": f"cf defterinde ({pd_}, {r.get('ticker')}) karşılığı YOK"})
            continue
        cf, neden = _cf_sec(list(adaylar), r.get("entry_trigger"))
        if cf is None:
            eslesmeyen.append({"ad": ad, "sinif": "cf_dolum_yok", "neden": neden})
            continue
        try:
            giris, sf = float(cf["entry"]), float(r["sim_fill"])
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz fiyat çifti ölçülemez yapar; satır ADIYLA eşleşmez kovasına girer ve sayımda görünür, sessizce düşmez
            eslesmeyen.append({"ad": ad, "sinif": "fiyat_bicimsiz",
                               "neden": f"cf entry={cf.get('entry')!r} / sim_fill={r.get('sim_fill')!r}"})
            continue
        if not giris:
            eslesmeyen.append({"ad": ad, "sinif": "fiyat_bicimsiz",
                               "neden": "cf giriş fiyatı 0 — bps paydası kurulamaz"})
            continue
        ciftler.append({"ad": ad, "kol": r.get("kol"), "plan_id": pid, "ticker": r.get("ticker"),
                        "date": r.get("date"), "plan_tarihi": pd_, "cf_id": cf.get("id"),
                        "cf_giris": giris, "sim_fill": sf, "cf_status": cf.get("status"),
                        # Kaç aday arasından seçildi: 1'den büyükse anahtar çok-adaylıydı ve
                        # seçim ölçüm-özdeşti (fiyatlar aynıydı) — okuyucu bunu görebilmeli.
                        "cf_aday_n": len(adaylar),
                        "kazanc_bps": round((giris - sf) / giris * 10000.0, 4)})

    def _kol_ozeti(alt: list[dict]) -> dict:
        ci = tarih_kumeli_bootstrap([c["kazanc_bps"] for c in alt], [c["date"] for c in alt],
                                    seviye=IKINCIL_CI)
        return {"n": len(alt), "n_min_dolu_mu": len(alt) >= IKINCIL_N_MIN,
                "ort_bps": None if ci["ort"] is None else round(ci["ort"], 4),
                "ci": {"alt": None if ci["lo"] is None else round(ci["lo"], 4),
                       "ust": None if ci["hi"] is None else round(ci["hi"], 4),
                       "n_kume": ci["n_kume"], "B": ci["B"],
                       "sifiri_disliyor": ci["sifiri_disliyor"], "neden": ci["neden"]},
                "ciftler": alt[-AD_TAVANI:], "ciftler_kirpildi": max(0, len(alt) - AD_TAVANI)}

    return {**ortak, "durum": "olculdu", "neden": None,
            "kollar": {k: _kol_ozeti([c for c in ciftler if c["kol"] == k])
                       for k in (KOL_SILAHLI, KOL_PLANLI)},
            "toplam": _kol_ozeti(ciftler),
            "eslesmeyen": {"n": len(eslesmeyen),
                           "oran": round(len(eslesmeyen) / len(evren), 4),
                           "sinif_dagilimi": {s: sum(1 for c in eslesmeyen if c["sinif"] == s)
                                              for s in sorted({c["sinif"] for c in eslesmeyen})},
                           "nedenler": eslesmeyen[:AD_TAVANI],
                           "adlar_kirpildi": max(0, len(eslesmeyen) - AD_TAVANI)}}


def main(argv: list[str] | None = None) -> int:
    """İKİ KOLUN RAPORU — ÇAĞIRAN BİR İNSANDIR (üretim yolu bu raporu okumaz).

    Kartın ikincil hattı bilerek `/api/diagnostics`e bağlanmadı: kilit zinciri (`health.faz6_
    kilitleri`) gerçek-çift hattını okur ve yanına ikinci bir bps sayısı koymak, iki hattın panoda
    tek bir "kazanç" gibi okunmasına davetiye olurdu. Bağlanması bir KART REVİZYONU kararıdır."""
    import json as _json
    k = kollar()
    rapor = {"kollar": k["n"], "etiketsiz": k["etiketsiz_n"],
             "birincil_planli_uretim": planli_kol_uretimi(),
             "ikincil_golge_cf": golge_cf_eslestirme(satirlar=k["satirlar"])}
    print(_json.dumps(rapor, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover — CLI girişi
    raise SystemExit(main())
