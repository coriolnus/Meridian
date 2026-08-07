"""broker.py — the paper broker. Realistic frictions or the agent learns a fantasy (Hard Rule 7).

Contract (§4):
  entry  = next bar OPEN + slippage
  exit   = on stop / target / trail / time-stop / regime-flip
  writes one JSON line per CLOSED trade.

This simulator is driven bar-by-bar by backtest.py and by the live loop (against real bars).
No clock reads, no network — it only knows the bars it is handed."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math

# 1.0R risks this fraction of current equity. position_size_r (in bounds.yaml) scales it.
RISK_PCT_PER_R = 0.01
MAX_ENTRY_GAP_PCT = 0.04   # skip an entry that gaps more than this above the planned trigger (no chasing)
ADV_CAP_PCT = 0.02         # a fill may not exceed this share of the name's average daily volume (liquidity)
IMPACT_COEF = 0.10         # linear price-impact: participation of ADV adds IMPACT_COEF·participation to the fill
MAX_NOTIONAL_PCT = 0.25    # a single position's notional (qty·entry) may not exceed this share of equity —
#                            bounds the gap-through-stop tail: a tight-ATR name otherwise buys huge share
#                            counts and a gap-down at bar-open loses NOTIONAL, not the intended 1R.
DERISK_FLOOR_DD = 0.08     # at/beyond this drawdown from peak, take no new size

# =================================================================================================
# E1 — GİRİŞ İCRA YASASI: TEK YASA, İKİ MOTOR (WP-E / kart EXE-2026-001, 2026-07-31)
# =================================================================================================
# BULGU (WP0 matrisi #1, canlı kanıt): iki motor FARKLI icra modeli koşuyordu.
#   * İÇ MOTOR (`fill_entry`): ertesi açılışta KOŞULSUZ dolum — açılış tetikten ne kadar yukarıda
#     olursa olsun (%4 max-chase tavanına dek) alınmış sayılıyordu.
#   * AYNA (`alpaca.submit_bracket`): buy-stop GTC bracket. `entry_trigger` sinyal barının
#     KAPANIŞIDIR (strategy.py: `entry_trigger=float(c_now)`), yani gönderim anında stop fiyatı
#     zaten son fiyata EŞİT ya da altındadır → Alpaca "stop price must be greater than current
#     price" ile reddediyordu. Canlı sonuç: 95/95 satırda `alpaca_fill_price` YOK, E2 slipaj
#     defteri hiç dolmadı, ayna hiçbir zaman gerçek bir dolum kanıtı üretmedi.
#
# YASA (tek yer, iki okuyucu — kopyalanmaz):
#   1. LİMİT   : limit = tetik + min(atr_mult·ATR14, pct_cap·tetik). ATR ölçülemezse yalnız
#                yüzde tavanı bağlar ve bu `offset_kaynak` alanıyla BEYAN EDİLİR (uydurma ATR yok).
#   2. DOLUM   : hiçbir motor limitin ÜSTÜNDE dolum yazamaz. İç motor: `next_open <= limit`.
#                Ayna: limit fiyatlı emir (limitin üstünde zaten dolmaz — sınır brokerdadır).
#   3. GAP     : gönderim anında referans fiyat tetiğin ÜSTÜNDEyse buy-stop GEÇERSİZDİR (bugünkü
#                retlerin kökü). Kart grid'inin iki noktası: `marketable_limit` (varsayılan —
#                limit fiyatlı emir, tavan yine limit) veya `cancel` (gap-risk vetosu).
#   4. TIF     : GTC — ve bu bir tercih değil KELEPÇEDİR (E1-v2, 2026-08-07).
#                MEKANİZMA: Alpaca bracket'ında `time_in_force` alanı TEKTİR ve emrin TAMAMINA
#                uygulanır. Giriş bacağı için seçtiğimiz ömür, KORUMA bacaklarının (take-profit +
#                stop-loss) da ömrüdür — ikisi ayrı ayrı seçilemez, çünkü ayrı ayrı gönderilmez.
#                ÖLÇÜLEN SONUÇ (canlı A1, 2026-08-06 20:00-20:02Z): `ENTRY_TIF="day"` yüzünden dört
#                motor pozisyonunun `limit sell` bacağı EXPIRED, OCO kardeşi `stop sell` CANCELED
#                oldu; dördü de gece boyunca ÇIPLAK kaldı. Hiçbir motor çağrısı iptal etmedi —
#                broker'ın gün-sonu sona-ermesi öldürdü. Yani DAY yalnız girişi seans-ömürlü
#                yapmıyordu, DOLMUŞ bir pozisyonun stop'unu da her akşam siliyordu.
#                SİSTEMİN KENDİ YASASININ İHLALİ: `alpaca.cancel_open_entries` belgesi "dolmuş
#                parent'lara DOKUNULMAZ — koruyucu bacakları canlı pozisyonu koruyor; onları iptal
#                etmek pozisyonu çıplak bırakır (yasak)" der. `tif=day` tam o yasağı her gece
#                broker üzerinden uyguluyordu; kod tarafında hiç görünmeyen bir ihlal.
#                ESKİ GEREKÇE — SİLİNMEDİ, SINIRI BEYAN EDİLDİ: "DAY. GTC bir sonraki seansa BAYAT
#                TETİK taşır (sinyal barı kapanışına sabitlenmiş bir seviye iki gün sonra artık o
#                kurulumu temsil etmez)". Bu cümle GİRİŞ bacağı için hâlâ doğrudur; kusuru
#                eksikliğiydi — çıkış bacağının TIF'ini ne bu blok ne kart EXE-2026-001 HİÇ
#                konuşmuyordu, dolayısıyla korumanın ömrü hiç kimsenin kararı olmadan girişin
#                yan etkisi olarak belirlendi.
#                BAYAT TETİK NEREYE GİTTİ: TIF'e HAVALE EDİLEMEZ, motorun kendi eline alındı.
#                `loop.daily_cycle` her turda, yeni planlar silahlanmadan ÖNCE
#                `alpaca.cancel_open_entries()` çağırır (yalnız motor önekli emirler, yalnız
#                `filled_qty=0` girişler, dolmuş parent'ın koruma bacaklarına DOKUNMADAN). Koruma
#                körelmiş bir aletten (emrin tamamını kesen bracket TIF'i) hedefli bir alete taşındı.
#                "day" BEYAZ-LİSTEDEN ÇIKARILDI (unutulmadı — kaldırıldı; bkz. ENTRY_TIF_ALLOWED):
#                tek bir TIF alanı olduğu sürece `execution_v2.tif: day` yazan bir yapılandırma
#                korumayı seans-ömürlü yapar. Bu bir arama değişkeni değil, bir emniyet sınırıdır.
#
# %4 MAX-CHASE İLE İLİŞKİSİ (kart: "ikisinin ilişkisini yorumla belgele"): ikisi AYNI YÖNDE iki
# tavandır ve DAİMA DAHA SIKI OLAN BAĞLAR. Bugünkü yapılandırmada limit tavanı (%1) chase
# tavanından (%4) sıkıdır, yani `MAX_ENTRY_GAP_PCT` fiilen DIŞ ZARFTIR ve pratikte hiç bağlamaz.
# Silinmedi çünkü: (a) `limit_pct_cap` config'ten %4'ün üstüne çıkarılırsa chase tavanı yeniden
# bağlayan taraf olur — iki tavan hiçbir yapılandırmada ÇELİŞMEZ, biri diğerini gevşetemez;
# (b) `counterfactual.advance` de aynı sabiti okuyor (karşı-olgusal defter BİLEREK daha gevşek
# kalır: "girseydik ne olurdu?" sorusunun paydası icra yasasıyla daralmamalı).
ENTRY_LIMIT_ATR_MULT = 0.5     # kart grid'inin VARSAYILAN noktası: min(0.5·ATR14, %1.0)
ENTRY_LIMIT_PCT_CAP = 0.01
ENTRY_TIF = "gtc"
# TIF BEYAZ-LİSTESİ — TEK NOKTA (E1-v2, 2026-08-07). "day" bu listeden ÇIKARILDI: madde 4'teki
# ölçülen vaka, DAY'in koruma bacaklarını her seans kapanışında öldürdüğünü gösterdi. Liste
# `entry_law`in kelepçesidir: yapılandırma "day" dese bile yasa onu KABUL ETMEZ ve `ENTRY_TIF`e
# düşer — çünkü korumanın ömrü bir arama değişkeni değildir. Yürürlükteki değer her gönderimde
# E2 defterine (`entry_execution.jsonl` → `tif`) yazıldığı için bu kelepçenin okuyucusu vardır.
ENTRY_TIF_ALLOWED = ("gtc",)
GAP_MARKETABLE = "marketable_limit"   # varsayılan: limit fiyatlı emir, tavan = limit
GAP_VETO = "cancel"                   # gap-risk vetosu: emir hiç gönderilmez, iç motor da doldurmaz
ENTRY_LAW_VERSION = "E1-v2"

# olay adları — İKİ motor da bu adları kullanır (grep'lenebilir tek sözlük)
EV_STOP_LIMIT = "entry_stop_limit"          # normal tetik: fiyat hâlâ tetiğin altında
EV_GAP_MARKETABLE = "entry_gap_marketable"  # tetik-üstü referans → limit fiyatlı emir
EV_GAP_VETO = "entry_gap_veto"              # tetik-üstü referans → gap-risk vetosu (emir yok)
EV_MISSED_LIMIT = "entry_missed_limit"      # açılış limitin üstünde → dolum YOK (kaçan işlem)


def entry_law(override: dict | None = None) -> dict:
    """Yürürlükteki giriş-icra yasası. Kaynak: `goal.yaml` → `execution_v2` (DEĞİŞMEZ dosya; icra
    yasası Hermes'in düğmesi DEĞİLDİR — bir arama değişkeni olsaydı ajan kendi dolum fiyatını
    seçebilirdi). Dosya/blok yoksa modül varsayılanları (kart grid'inin varsayılan noktası).

    Kelepçe: bozuk/negatif değer sessizce geçmez, varsayılana düşer — "config'te vardı ama
    anlamsızdı" hâli, yasanın olmadığı hâlden daha tehlikelidir."""
    cfg = {"limit_atr_mult": ENTRY_LIMIT_ATR_MULT, "limit_pct_cap": ENTRY_LIMIT_PCT_CAP,
           "gap_behavior": GAP_MARKETABLE, "tif": ENTRY_TIF, "version": ENTRY_LAW_VERSION}
    raw = override
    if raw is None:
        try:
            from . import config
            raw = (config.goal() or {}).get("execution_v2") or {}
        except Exception:  # sessiz-yutma: yapılandırma okunamadıysa YASA YOK olmaz, varsayılana düşer — ve `entry_law_source` alanı bunu dışarı söyler
            raw = {}
    if isinstance(raw, dict):
        try:
            m = float(raw.get("limit_atr_mult", cfg["limit_atr_mult"]))
            if m >= 0:
                cfg["limit_atr_mult"] = m
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz düğme varsayılana düşer; hangi değerin yürürlükte olduğu çıktının `law` bloğunda görünür
            pass
        try:
            p = float(raw.get("limit_pct_cap", cfg["limit_pct_cap"]))
            if 0 < p <= 0.10:
                cfg["limit_pct_cap"] = p
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz config değeri varsayılanda kalır (üstteki atr_mult bloğuyla aynı yasa)
            pass
        if str(raw.get("gap_behavior", "")).strip() in (GAP_MARKETABLE, GAP_VETO):
            cfg["gap_behavior"] = str(raw["gap_behavior"]).strip()
        # TIF: beyaz-liste ARTIK TEK UÇLU (`ENTRY_TIF_ALLOWED`). Listede olmayan bir değer —
        # "day" dahil — sessizce varsayılana düşer; `gap_behavior` dalıyla birebir aynı desen.
        # Bu düşüş bir kayıp değil KELEPÇEdir: yürürlükteki TIF her gönderimde E2 defterine
        # yazıldığı için "config'te day yazıyordu ama gtc gönderildi" hâli kayıttan okunur.
        if str(raw.get("tif", "")).strip().lower() in ENTRY_TIF_ALLOWED:
            cfg["tif"] = str(raw["tif"]).strip().lower()
    return cfg


def entry_limit_price(trigger: float, atr: float | None = None, cfg: dict | None = None) -> float:
    """Yasanın 1. maddesi — TEK hesap. ATR yoksa/0 ise yalnız yüzde tavanı bağlar; ATR'yi
    stoptan geri türetmek (stop = ref − mult·ATR) yapılmadı: `stop_mode=1` (pivot altı) yolunda
    o özdeşlik YANLIŞ olur ve ölçülmemiş bir ATR uydurmuş olurduk."""
    cfg = cfg or entry_law()
    t = float(trigger or 0.0)
    if t <= 0:
        return 0.0
    pct_off = t * float(cfg["limit_pct_cap"])
    try:
        a = float(atr) if atr is not None else 0.0
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz ATR = ölçülemedi; `offset_kaynak` alanı bunu satıra yazar
        a = 0.0
    off = min(float(cfg["limit_atr_mult"]) * a, pct_off) if a > 0 else pct_off
    return t + off


def entry_order_decision(trigger: float, ref_price: float | None = None,
                         atr: float | None = None, cfg: dict | None = None) -> dict:
    """Yasanın 3. maddesi — GÖNDERİM anındaki karar. Saf: ağ yok, saat yok, defter yok.

    `ref_price` = gönderim anında bilinen SON fiyat (canlı yolda sinyal barının kapanışı — emir o
    kapanıştan sonra, ertesi açılıştan önce gider). None = ÖLÇÜLEMEDİ ve bu satıra yazılır.

    ÖLÇÜLEMEYEN REFERANS GAP DALINA DÜŞER (bilinçli): buy-stop'un tek katkısı "fiyat tetiği YUKARI
    kırana kadar girme" teyididir; referans bilinmiyorsa o teyit zaten yapılamaz, ama stop-limit
    göndermek bugünkü retlerin (95/95) riskini geri getirir. Limit tavanı her iki dalda da aynı
    olduğu için ÖDENEN FİYAT değişmez — değişen yalnız teyidin kaybıdır ve `ref_kaynak` alanıyla
    beyan edilir."""
    cfg = cfg or entry_law()
    t = float(trigger or 0.0)
    limit = entry_limit_price(t, atr, cfg)
    try:
        rp = None if ref_price is None else float(ref_price)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz referans = ölçülemedi; `ref_kaynak` alanı satıra yazılıyor
        rp = None
    try:
        a = float(atr) if atr is not None else 0.0
    except (TypeError, ValueError):  # sessiz-yutma: aynı gerekçe — `offset_kaynak` alanı taşıyor
        a = 0.0
    gap = (rp is None) or (t > 0 and rp >= t)
    if not gap:
        mode, olay = "stop_limit", EV_STOP_LIMIT
    elif cfg["gap_behavior"] == GAP_VETO:
        mode, olay = "veto", EV_GAP_VETO
    else:
        mode, olay = "marketable_limit", EV_GAP_MARKETABLE
    return {
        "mode": mode, "olay": olay, "trigger": round(t, 4), "limit": round(limit, 4),
        "atr": (round(a, 4) if a > 0 else None),
        "offset_kaynak": ("atr" if (a > 0 and cfg["limit_atr_mult"] * a < t * cfg["limit_pct_cap"])
                          else ("pct_cap" if a > 0 else "pct_cap(atr_olculemedi)")),
        "ref_price": (round(rp, 4) if rp is not None else None),
        "ref_kaynak": ("olculemedi" if rp is None else "son_kapanis"),
        "gap_at_submit": bool(gap), "gap_behavior": cfg["gap_behavior"], "tif": cfg["tif"],
        "law": cfg["version"],
        "limit_bps": (round((limit / t - 1.0) * 10000, 2) if t > 0 else None),
    }


def bps_delta(a: float | None, b: float | None) -> float | None:
    """(a/b − 1) × 10000 — E2 slipaj defterinin TEK bps hesabı (iki okuyucu: loop yazarken,
    analytics özetlerken). Taraflardan biri ölçülemezse None: 0.0 yazmak "slipaj yoktu" demek
    olurdu, oysa "ölçemedik" demektir."""
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):  # sessiz-yutma: ölçülemeyen taraf None ile DIŞARI çıkıyor; sayaçlar payda olarak ayrı raporlanır
        return None
    if y == 0:
        return None
    return round((x / y - 1.0) * 10000.0, 3)


def derisk_mult(equity: float, peak: float) -> float:
    """Graded de-risk: shrink new-position size CONTINUOUSLY as the book draws down from its peak — a
    smooth linear ramp (was a 4-step cliff: full at 2.99% dd, −34% at 3.01%). Full size until 3% dd,
    then linearly to 0 at DERISK_FLOOR_DD. Applied identically in live and backtest at fill time."""
    if peak <= 0:
        return 1.0
    dd = (peak - equity) / peak
    if dd <= 0.03:
        return 1.0
    if dd >= DERISK_FLOOR_DD:
        return 0.0
    return round(1.0 - (dd - 0.03) / (DERISK_FLOOR_DD - 0.03), 4)   # linear 1.0 → 0.0 across [3%, 8%]


def max_positions_at(equity: float, peak: float, base_max: int) -> int:
    """Concurrent-position throttle: as the book draws down, cut not just size but the NUMBER of open
    positions allowed — de-gross concentration, not only per-trade size. Never below 1 while any size
    is permitted; 0 once the de-risk floor is hit."""
    m = derisk_mult(equity, peak)
    if m <= 0.0:
        return 0
    if m >= 1.0:
        return int(base_max)
    return max(1, int(round(base_max * m)))


@dataclass
class Position:
    plan_id: str
    ticker: str
    side: str
    entry: float
    stop: float          # hard stop (never loosens)
    trail_stop: float
    target: float
    qty: int
    r_per_share: float
    risk_dollars: float
    size_r: float
    ts_open: str
    bars_held: int = 0
    regime_at_plan: str = "?"
    skill_chain: list = field(default_factory=list)
    strategy_version: int = 1
    entry_slippage_cost: float = 0.0   # informational total ENTRY friction (slippage $ + commission); NOT re-charged
    entry_commission: float = 0.0      # entry commission, deferred to close so realized_pnl == Σ row.pnl_dollars
    scaled_out: bool = False      # #8 partial scale-out already banked?
    banked_pnl: float = 0.0       # realized P&L from the scaled-out portion (folded into the final row)
    setup: str = "?"              # gölge modelin özellikleri — kapanış satırına damgalanır ki
    plan_score: float | None = None    # eğitim join'siz olsun (v3 shadow_model)
    rr_expected: float | None = None
    exploration: bool = False     # keşif sondası (bütçe %0 rejimde kanıt işlemi — 0.25R tavanlı)
    hi_water: float = 0.0         # öneri #2: pozisyon ömrü boyunca görülen en yüksek high (MFE için)
    lo_water: float = 0.0         # ve en düşük low (MAE için); 0.0 = eski kayıt, damga atlanır
    # G3b (2026-07-30): kurulumun YAPI çizgisi (sinyal barında hesaplanan pivot), pozisyonla birlikte
    # taşınır. `strategy.early_kill_pivot_exit` bunu okur. 0.0 = "çağıran pivot geçirmedi" (canlı yol
    # bugün geçirmiyor; loop.py bu turun yüzeyi değil) → erken itlaf ateşlemez, UYDURMA seviye yok.
    # Yönetim barında YENİDEN hesaplanmaz: `ind.pivot_high` yuvarlanan bir seri olduğu için sonraki
    # barlarda BAŞKA bir sayı verir ve pozisyon, girerken sınadığı seviyeden farklı bir seviyeye göre
    # itlaf edilirdi — iki motorun ayrışmasından beter, TEK motorun kendi kendinden ayrışması olurdu.
    pivot: float = 0.0


# =================================================================================================
# KİTABIN BEYAN ÖLÇÜSÜ — TEK YASA, İKİ TÜKETİCİ (2026-08-04 "portföy sıfırlaması" vakası)
# =================================================================================================
# NE ÖLÇER: `portfolio.json`daki SERMAYE BEYANININ (`sermaye_resetleri`) büyüklüğü. Beyan, kitabın
# tabanının defterin tabanından ne kadar ve NEDEN ayrıldığını söyleyen kayıttır; `recompute`in üç
# kimliği (realized_pnl · cash_identity · equity_curve_tail) ofseti ondan okur. Kayıt kaybolursa
# ofset 0'a düşer ve üç kimlik birden kırılır — canlıda tam olarak bu oldu (KOKNEDEN §1).
#
# NEDEN BURADA (leaf) YAŞIYOR: İKİ tüketicisi var — `loop._save_broker`ın yazım kapısı (D2) ve
# `watchdog.monotonicity_report`ın monotonluk tabanı (D4). Ölçüyü iki yerde ayrı ayrı yazmak, bu
# deponun adıyla kovaladığı kusurun ta kendisi olurdu ("aynı yasanın iki uygulaması"): biri
# güncellenir, diğeri unutulur ve kapı ile dedektör AYNI olayda farklı şey söyler. `broker.py`
# ikisinin de döngüsüz ithal edebildiği tek modüldür (watchdog → loop bir ithal halkası olurdu).
# KAYITLARI OKUYAN TEK YER YİNE `sermaye.resetler`dir: burada ikinci bir okuyucu doğmaz, yalnız
# TOPLAM alınır.

# Kayıt-başına mutlak ofset toplamındaki karşılaştırma toleransı. Kayıtlar 2 ondalığa yuvarlı
# yazılır; eşik kayan-nokta gürültüsünü eler, gerçek bir kaybı (en küçüğü sentlerce) elemez.
BEYAN_TOL = 0.01


def _abs_ofset(v) -> float:
    try:
        return abs(float(v))
    except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — kayıt `n` sayacında GÖRÜNÜR ve kimlik kapısı onu saymaya devam eder; ölçülemeyen bir ofseti sayıya çevirmek UYDURMA olurdu, 0 katkı "bu kaydın büyüklüğü ölçülmedi" demektir
        return 0.0


def beyan_olcusu(pf: dict | None) -> dict:
    """Kitabın beyan ölçüsü: `{"n": kayıt sayısı, "abs_ofset": Σ|ofset|, "ids": [...]}`.

    TOPLAM NEDEN MUTLAK VE KAYIT BAŞINA: kayıtlar deftere yalnız EKLENİR, yani Σ|ofset| monoton
    artan bir büyüklüktür ve bir ratchet tabanı olabilir. İşaretli toplam (`sermaye.ofset`)
    monoton DEĞİLDİR — ters işaretli ikinci bir reset onu küçültür ve kapı o gün sahte alarm
    üretirdi. `ids` ayrıca taşınır: sayı aynı kalıp kaydın DEĞİŞMESİ de bir kayıptır."""
    from . import sermaye as _sm       # kayıtları okuyan TEK yer; burada ikinci bir okuyucu yok
    kayitlar = _sm.resetler(pf if isinstance(pf, dict) else {})
    return {"n": len(kayitlar),
            "abs_ofset": round(sum(_abs_ofset(k.get("ofset")) for k in kayitlar), 2),
            "ids": [str(k.get("id")) for k in kayitlar if k.get("id") is not None]}


def beyan_gerilemesi(eski: dict, yeni: dict) -> dict | None:
    """BEYAN YALNIZ EKLENEBİLİR. Gerileme varsa NEDENİYLE döner (alarm alanları hazır), yoksa None.

    `watchdog.grant_amnesty` ailesinin aynı deseni: meşru bir küçülme YAZILI olmak zorundadır;
    sessizce düşen bir beyan, üç gün sonra üç kırık kimlik olarak ortaya çıkar (teşhis maliyeti
    bir kök-neden dosyasıdır)."""
    ortak = {"eski_n": int(eski.get("n", 0)), "yeni_n": int(yeni.get("n", 0)),
             "eski_ofset": float(eski.get("abs_ofset", 0.0)),
             "yeni_ofset": float(yeni.get("abs_ofset", 0.0))}
    if ortak["yeni_n"] < ortak["eski_n"]:
        return {"neden": "kayit_sayisi_dustu", **ortak}
    if ortak["yeni_ofset"] + BEYAN_TOL < ortak["eski_ofset"]:
        return {"neden": "ofset_kuculdu", **ortak}
    kayip = [i for i in (eski.get("ids") or []) if i not in set(yeni.get("ids") or [])]
    if kayip:
        return {"neden": "kayit_kayboldu", "kayip_id": kayip, **ortak}
    return None


class PaperBroker:
    def __init__(self, equity: float, slippage_bps: float, commission_per_share: float):
        self.start_equity = equity
        self.cash = equity
        self.realized_pnl = 0.0
        self.slip = slippage_bps / 10000.0
        self.commission = commission_per_share
        self.positions: dict[str, Position] = {}
        self.closed: list[dict] = []
        self._id = 0

    # ---- equity ----
    # ÇIKARILDI 2026-07-30 (temizlik turu): `open_risk_dollars()` — açık pozisyonların
    # `risk_dollars` toplamı. ÇAĞIRAN TARAMASI (meridian/ + tests/): tek eşleşme tanımın kendisiydi.
    # NEDEN ÖLÜ KALDI: canlı risk tavanı DOLAR değil R birimindedir ve `guard.py` onu portföy
    # defterinden okur; bu metot broker nesnesinin İÇ toplamını veriyordu, yani ikinci bir
    # "açık risk" gerçeği — kullanılsaydı iki sayı ayrışabilirdi.
    # GERİ-AL: `def open_risk_dollars(self) -> float:
    #              return sum(p.risk_dollars for p in self.positions.values())` — bu yorumun yerine.

    def equity(self, marks: dict[str, float] | None = None) -> float:
        """Realized equity + unrealized mark-to-market of open positions."""
        eq = self.start_equity + self.realized_pnl
        if marks:
            for t, p in self.positions.items():
                if t in marks:
                    eq += p.qty * (marks[t] - p.entry)
        return eq

    # ---- entries ----
    def size_position(self, entry_fill: float, stop: float, size_r: float, equity: float) -> tuple[int, float]:
        risk_dollars = size_r * RISK_PCT_PER_R * equity
        per_share = entry_fill - stop
        if per_share <= 0:
            return 0, 0.0
        qty = int(math.floor(risk_dollars / per_share))
        return qty, risk_dollars

    def fill_entry(self, plan: dict, next_open: float, ts: str, equity: float,
                   size_mult: float = 1.0, adv: float | None = None,
                   pivot: float = 0.0, atr: float | None = None,
                   gap_at_submit: bool | None = None,
                   reject_out: dict | None = None) -> Optional[Position]:
        """Fill a passing plan at next bar open + slippage. Returns the Position or None if unsizable
        or blocked by a gap guard. size_mult (<=1) scales risk down for graded de-risk. `adv` (average
        daily volume in SHARES) enables liquidity realism (Hard Rule 7): the order is capped at
        ADV_CAP_PCT of ADV, and its participation of ADV adds linear price impact on top of the base
        slippage — so a size the market couldn't absorb can't fill at a fantasy price. adv=None keeps
        the original fixed-slippage behavior (unit tests, thin/synthetic bars).

        `pivot` (G3b, 2026-07-30): kurulumun YAPI çizgisi, `strategy.early_kill_pivot_exit`in okuduğu
        seviye. PLAN SÖZLÜĞÜNDEN DEĞİL AYRI ARGÜMANDAN gelir — plan defteri şeması iki motorda AYNI
        kalmak zorundadır (test_differential_v60), pivot ise bir defter alanı değil icra girdisidir.
        Geçirmeyen çağıran için 0.0 = "bilinmiyor" → erken itlaf ateşlemez. C13 (2026-08-02): canlı
        `loop.py` de artık geçiriyor (`entry_law` yan tablosu) — bu satır eskiden "canlı geçirmez"
        diyordu ve tam olarak o kopukluk, knob terfi ederse canlıda sessiz no-op üretiyordu.

        E1 (WP-E, 2026-07-31) — AYNI YASA, İKİ MOTOR. `atr` / `gap_at_submit` de PLAN SÖZLÜĞÜNDEN
        DEĞİL ayrı argümandan gelir (pivot ile aynı gerekçe: ikisi de defter alanı değil İCRA
        girdisidir ve plan şeması iki motorda AYNI kalmak zorundadır — test_differential_v60).
          * `atr`          : sinyal barında hesaplanmış ATR14. None = ölçülemedi → limit yalnız
                             yüzde tavanıyla kurulur (uydurma ATR yok).
          * `gap_at_submit`: gönderim anında referans fiyat tetiğin üstünde miydi? YALNIZ
                             `gap_behavior=cancel` grid noktasında karar değiştirir. None =
                             "bu motorda gönderim anı YOK" (replay) ve veto ateşlemez — bu bir
                             BEYAN EDİLMİŞ kapsam farkıdır, sessiz bir ayrışma değil.
          * `reject_out`   : verilirse ret NEDENİ buraya yazılır. `entry_missed_limit` kaçan bir
                             işlemdir ve çağıran onu olay + defter satırı olarak ölçer (yutulmaz).
        """
        def _red(reason: str, **ek):
            if reject_out is not None:
                reject_out.clear()
                reject_out.update({"reason": reason, "ticker": plan.get("ticker"),
                                   "plan_id": plan.get("id"), **ek})
            return None

        if plan["ticker"] in self.positions:
            return _red("already_open")
        stop = plan["stop"]
        trigger = plan.get("entry_trigger", next_open)
        # E1 GAP VETOSU: gönderim anında fiyat zaten tetiğin üstündeyse (buy-stop geçersiz) ve
        # yürürlükteki grid noktası `cancel` ise İKİ motor da girmez. Aynada emir hiç gönderilmedi;
        # iç motorun yine de doldurması, tam olarak bu turun kapattığı ayrışmayı yeniden açardı.
        _law = entry_law()
        if gap_at_submit and _law["gap_behavior"] == GAP_VETO:
            return _red(EV_GAP_VETO, trigger=round(float(trigger or 0.0), 4),
                        open=round(float(next_open), 4), gap_behavior=GAP_VETO)
        # gap guards (same in live + backtest): don't chase a big gap-up above the trigger, and never
        # enter if the bar opened at/below the planned stop (a gap through the stop = no valid entry).
        if trigger > 0 and next_open > trigger * (1.0 + MAX_ENTRY_GAP_PCT):
            return _red("max_chase", trigger=round(float(trigger), 4),
                        open=round(float(next_open), 4), tavan_pct=MAX_ENTRY_GAP_PCT)
        # E1 LİMİT TAVANI — `MAX_ENTRY_GAP_PCT`ten SIKI olan taraf bağlar (bkz. modül başlığı).
        # AYNADAKİ limit fiyatlı emrin BİREBİR karşılığı: limitin üstünde dolum yazılamaz.
        if trigger > 0:
            _limit = entry_limit_price(trigger, atr, _law)
            if next_open > _limit:
                return _red(EV_MISSED_LIMIT, trigger=round(float(trigger), 4),
                            limit=round(_limit, 4), open=round(float(next_open), 4),
                            asim_bps=round((float(next_open) / _limit - 1.0) * 10000, 2)
                                     if _limit > 0 else None,
                            atr=(round(float(atr), 4) if atr else None),
                            law=_law["version"])
        if next_open <= stop:
            return _red("open_below_stop", stop=round(float(stop), 4),
                        open=round(float(next_open), 4))
        base_fill = next_open * (1.0 + self.slip)  # long: pay up (fixed component)
        qty, risk_dollars = self.size_position(base_fill, stop, plan["size_r"] * max(0.0, size_mult), equity)
        if qty <= 0:
            return _red("qty_zero", size_mult=round(float(size_mult), 4))
        # liquidity: cap the order at ADV_CAP_PCT of ADV, then charge participation-based price impact
        if adv and adv > 0:
            cap = int(ADV_CAP_PCT * adv)
            if cap <= 0:
                return _red("illiquid", adv=float(adv))   # too illiquid to take any real size
            if qty > cap:
                qty = cap
                risk_dollars = qty * (base_fill - stop)   # re-derive risk to the shares we can actually get
            participation = qty / adv
            fill = base_fill * (1.0 + IMPACT_COEF * participation)
        else:
            fill = base_fill
        # notional cap: bound single-name concentration + gap-through-stop tail (loss scales with notional)
        max_shares = int(MAX_NOTIONAL_PCT * equity / base_fill) if base_fill > 0 else qty
        if qty > max_shares:
            qty = max_shares
            risk_dollars = qty * (base_fill - stop)
        if qty <= 0:
            return _red("notional_cap", equity=round(float(equity), 2))
        # H1 — slippage is EMBEDDED in `fill` (= pos.entry), so it is already reflected in every mark-to-market
        # (equity uses mark-entry) and in the exit P&L (gross uses pos.entry). Charging it a SECOND time as a
        # cash cost double-counted it: broker equity, the trade-row pnl_dollars, and the true round-trip all
        # disagreed by exactly the slippage, and the gate (reads pnl_dollars) ran off a different equity than
        # the circuit-breaker (reads realized_pnl). Keep slippage in the price only; defer commission to close.
        entry_slip_dollars = qty * (fill - next_open)
        entry_commission = qty * self.commission
        pos = Position(
            plan_id=plan["id"], ticker=plan["ticker"], side="long", entry=fill, stop=stop,
            trail_stop=stop, target=plan["profit_target"], qty=qty,
            r_per_share=fill - stop, risk_dollars=risk_dollars, size_r=plan["size_r"], ts_open=ts,
            regime_at_plan=plan.get("regime_at_plan", "?"), skill_chain=plan.get("skill_chain", []),
            strategy_version=plan.get("strategy_version", 1),
            entry_slippage_cost=round(entry_slip_dollars + entry_commission, 4),
            entry_commission=round(entry_commission, 4),
            setup=plan.get("setup", "?"), plan_score=plan.get("score"),
            rr_expected=plan.get("r_multiple_expected"), exploration=bool(plan.get("exploration")),
            hi_water=fill, lo_water=fill,
            # G3b: çağıran pivot geçirmediyse 0.0 — "bilinmiyor" ile "sıfır" aynı şey değil, ama bu
            # alan yalnız `pivot > 0` koşuluyla okunduğu için 0.0 dürüstçe "ölçülemedi" anlamına gelir.
            pivot=float(pivot or 0.0),
        )
        self.positions[pos.ticker] = pos
        return pos

    # ---- exits ----
    def _touch_exit(self, pos: Position, bar: dict) -> Optional[tuple[float, str]]:
        """Gap-aware intrabar exit against a bar. İKİ KADEME:
          1) AÇILIŞ — barın İLK basılan fiyatı, sırası KESİN. Açılışta zaten aşılmış bir emir
             (stop altında ya da hedef üstünde açılış) barın içindeki BELİRSİZ sıradan ÖNCE çözülür.
          2) bar içi — high/low sırası OHLC'den bilinemez → stop önce (muhafazakârlık).

        DENETİM (2026-07-22, v75): eski sıra `l <= eff_stop`ı `o >= target`ın ÖNÜNE koyuyordu, yani
        bar-içi BELİRSİZ bir stop dokunuşu, açılışta GARANTİ dolmuş bir hedef boşluğunu eziyordu.
        Hedefin ÜSTÜNDE açılan bir bar, gün içinde stop'a da uğrarsa işlem tam stop zararı olarak
        yazılıyordu — oysa pozisyon o barın ilk fiyatında zaten kapanmıştı; low'a ulaşan bir pozisyon
        YOKTU. Kanıt: trail 108 / hedef 115 / bar(o=116, h=118, l=107) → 1.6R yazılıyordu, doğrusu
        3.2R (hata 1.6R); uç örnekte (o=118, l=94) -1.0R yerine +3.6R (hata 4.6R). Canlı karşı-olgusal
        defterde de gerçekleşmişti: CF-2025-10-28-SWKS (o=83.14 ≥ hedef 82.74, l=78.59 ≤ stop 79.27)
        -1.01R yazılmış, doğrusu ≈-0.02R. Muhafazakârlık bar İÇİNDE geçerlidir; açılışta değil."""
        o, h, l = bar["open"], bar["high"], bar["low"]
        # öneri #2 su işaretleri BURADA güncellenir: backtest.replay bunu HİÇ yapmıyordu, dolayısıyla
        # canlı defterin 129 satırının TAMAMI mfe_r=0.0/mae_r=0.0 ile yazılmıştı (hedefte kapanan bir
        # işlemin MFE'si tanımı gereği ≥2.5R'dir). close_position'daki "yoksa None" koruması hiç
        # ateşlenemiyordu, çünkü hi_water girişte fill'e kuruluyor — sıfır değil, UYDURMA sıfır.
        # Tek ortak dikiş burasıdır (backtest.py + loop.py ikisi de her bar için çağırır).
        if pos.hi_water > 0:
            pos.hi_water = max(pos.hi_water, float(h))
        if pos.lo_water > 0:
            pos.lo_water = min(pos.lo_water, float(l))
        eff_stop = max(pos.stop, pos.trail_stop)
        # 1) açılış — kesin sıra
        if o <= eff_stop:
            return o, "stop_gap"
        if o >= pos.target:
            return o, "target_gap"
        # 2) bar içi — sıra bilinemez, stop önce
        if l <= eff_stop:
            return eff_stop, "stop"
        if h >= pos.target:
            return pos.target, "target"
        return None

    def scale_out(self, pos: Position, bar: dict, params: dict) -> bool:
        """#8 partial scale-out: once the bar's high reaches entry + exit.scale_out_r·R, bank
        exit.scale_out_frac of the position at that level and ratchet the stop to breakeven for the rest.
        The banked P&L is folded into the SINGLE final closed-trade row (one trade, qty-weighted R), so
        min_sample / per-fold n are unaffected. exit.scale_out_frac=0 → off (default)."""
        if pos.scaled_out:
            return False
        frac = float(params.get("exit.scale_out_frac", 0.0))
        if frac <= 0.0:
            return False
        level = pos.entry + float(params.get("exit.scale_out_r", 2.0)) * pos.r_per_share
        if bar["high"] < level:
            return False
        # HEDEF ÖNCE (2026-07-22, v75): kısmi satış seviyesi hedefin ÜSTÜNDEyse o seviyeye giden yol
        # hedefin İÇİNDEN geçer — hedef emri önce dolar ve pozisyonun TAMAMINI kapatır; `level`de
        # satılacak hisse KALMAZ. Eski kod yine de bankalıyordu ve işlem hem +scale_out_r'yi hem
        # +hedefi yazıyordu. bounds.yaml bunu SERBEST bırakıyor (scale_out_r ≤ 4.0, profit_target_r
        # ≥ 2.0), yani mutasyon araması bedava R üreten bu kombinasyonu ARAYARAK bulurdu:
        # giriş 100 / stop 95 / hedef 110 / level 120, bar(o=105,h=125,l=104) → 3.0R yazılıyordu,
        # doğrusu 2.0R. Aynı şekilde bar HEDEFİN üstünde açıldıysa pozisyon ilk fiyatta kapanmıştır.
        if pos.target and level >= pos.target:
            return False
        if bar.get("open") is not None and pos.target and float(bar["open"]) >= pos.target:
            return False
        # STOP-BEFORE-TARGET conservatism (the same convention _touch_exit documents): when the bar's
        # open or low breached the effective stop, the intrabar order of stop-vs-high is unknowable from
        # OHLC — banking the +NR partial first (and ratcheting to breakeven before the stop check) would
        # book optimistic profit on a bar that may have stopped out first (audit #2/#8). Skip the
        # scale-out; _touch_exit then resolves the bar conservatively as a full stop exit.
        eff_stop = max(pos.stop, pos.trail_stop or pos.stop)
        if bar.get("open") is not None and float(bar["open"]) <= eff_stop:
            return False
        if bar.get("low") is not None and float(bar["low"]) <= eff_stop:
            return False
        sell_qty = int(pos.qty * frac)
        if sell_qty <= 0:
            return False
        fill = level * (1.0 - self.slip)                      # bank at the scale level (slippage IN the price)
        partial_commission = sell_qty * self.commission
        pnl_partial = sell_qty * (fill - pos.entry) - partial_commission   # H1: slippage already in `fill`; charge commission once
        self.realized_pnl += pnl_partial
        self.cash += pnl_partial
        pos.banked_pnl += pnl_partial
        pos.qty -= sell_qty
        pos.trail_stop = max(pos.trail_stop, pos.entry)       # lock the runner at breakeven
        pos.scaled_out = True
        return True

    def close_position(self, ticker: str, raw_exit: float, reason: str, ts: str) -> dict:
        """Kapanmış işlem satırını ÜRETİR — ama `kaynak` damgasını BİLEREK basmaz (BT-1, 2026-07-31).

        Bu fabrika ORTAKTIR: canlı döngü (`loop.daily_cycle`), replay tohumu (`backtest.replay`),
        gölge varyant kitapları ve karşı-olgusal defter aynı `PaperBroker`ı kullanır. Buraya sabit
        bir damga koymak, üretilen satırın NEREYE yazıldığını bilmeyen bir katmanın o soruyu
        cevaplaması olurdu — ve yanlış cevap tam olarak BT-1'in yarattığı hasarı üretirdi
        (simülasyon satırı "canlı" damgasıyla öğrenme defterine girer).

        Damgayı YAZAR basar, üretici değil: `loop._persist_trade` → `live_paper`,
        `run.replay_seed` → `replay_seed`. Damga sözlüğü ve migrasyonu `ledgerstamp.py`de."""
        pos = self.positions.pop(ticker)
        exit_fill = raw_exit * (1.0 - self.slip)  # long exit: receive less (slippage IN the price)
        exit_slip_dollars = pos.qty * (raw_exit - exit_fill)
        exit_commission = pos.qty * self.commission
        gross = pos.qty * (exit_fill - pos.entry)                # true round-trip P&L — both slippages in the fills
        pnl_remaining = gross - pos.entry_commission - exit_commission   # H1: charge commission ONCE (each side); slippage already priced in
        costs = pos.entry_slippage_cost + exit_slip_dollars + exit_commission   # informational total friction
        self.realized_pnl += pnl_remaining
        self.cash += pnl_remaining
        self._id += 1
        pnl = pnl_remaining + pos.banked_pnl                  # combine scaled + final into ONE trade
        r_multiple = pnl / pos.risk_dollars if pos.risk_dollars else 0.0
        row = {
            "id": f"T{self._id:05d}", "ts_open": pos.ts_open, "ts_close": ts,
            "ticker": pos.ticker, "side": pos.side, "entry": round(pos.entry, 4),
            "exit": round(exit_fill, 4), "qty": pos.qty, "r_multiple": round(r_multiple, 3),
            "pnl_pct": round((exit_fill - pos.entry) / pos.entry, 5),
            "pnl_dollars": round(pnl, 2), "costs": round(costs, 2), "exit_reason": reason,
            "strategy_version": pos.strategy_version, "regime": pos.regime_at_plan,
            "setup": pos.setup, "score": pos.plan_score, "r_multiple_expected": pos.rr_expected,
            "exploration": pos.exploration,
            "plan_id": pos.plan_id, "skill_chain": pos.skill_chain,
            "bars_held": pos.bars_held, "scaled_out": pos.scaled_out,
            # öneri #2: maksimum lehte/aleyhte hareket (R) — çıkış tarafını KANITLA tunlamanın ham maddesi.
            # Watermark yoksa (eski portfolio.json'dan yüklenen pozisyon) uydurma yok: None.
            "mfe_r": round((pos.hi_water - pos.entry) / pos.r_per_share, 3)
                     if pos.hi_water > 0 and pos.r_per_share > 0 else None,
            "mae_r": round((pos.entry - pos.lo_water) / pos.r_per_share, 3)
                     if pos.lo_water > 0 and pos.r_per_share > 0 else None,
        }
        self.closed.append(row)
        return row
