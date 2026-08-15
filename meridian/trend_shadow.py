"""trend_shadow.py — hükümlü uzun-ufuk trend kolunu canlı barlar üzerinde ileri yürüten sanal gölge-kitap.

NE YAPAR. Ölçülmüş bir hükmün (chandelier çıkış × geniş evren × N=10 slot, 12-1 momentum) canlı
birikimidir — yeni bir ölçüm değil; hükmün ölçüm şasisine (backtest/dataset/score/shadowlaw) hiç
dokunmaz. Her seans kitabı günlük M2M ile işaretler; her ay-sonu 12-1 momentum sıralamasıyla
karar alır ve kararı ERTESİ seans açılışında icra eder (bakma-ileri yok): çıkışlar → 1/N'e
denkleştirme → girişler. Referans şasinin sabitleri birebir taşınır (FRICTION_BPS=10, ATR22,
CHANDELIER_K=3.5, N_SLOTS=10); canlı çevirinin üç açık farkı vardır ve sessiz değildir —
sermaye 100k (oransal muhasebe, getiri aynı), uygunluk katmanı deponun kendi bütünlük defteri
(`adapters.data.bars_integrity`; ikinci kopya aynı yasanın iki sürümünü doğururdu) ve kitabın
GEÇMİŞSİZ doğması (geri-doldurma yok; ilk giriş ilk ay-sonunda).

KİLİT GİRİŞLER. `run_cycle(bars, index, on_date)` (loop.daily_cycle kancası — kitabı
`last_session`dan bugüne yürütür), `ozet` (pano/CLI özeti; doldurma kökeni rakamla birlikte),
`ay_sonu_mu` (fail-closed takvim kapısı), `_karar`/`_icra`/`_isaretle` (karar → icra → M2M),
`_dilim`/`dolduruldu_n`/`DOLDU_KOL` (ileri-doldurma köken bayrağı), `yeni_kitap`.

YASALAR — GÖLGE KATMANI. SIFIR YETKİ, YAPISAL (beyan değil): broker/alpaca/emir yolu IMPORT BİLE
EDİLMEZ — çivisi tests/test_trend_shadow_v144.py'de AST ile kurulu. Tek yan etkisi kendi
defteridir; portföy, plan, karne, silahlanma ve strateji dosyalarına, yani canlı karara hiçbir
yol çıkmaz. PIT şerhi kitabın İÇİNDE taşınır (`pit_serh`, her yazımda yeniden çakılır): ölçülen
fazlanın büyük kısmı evren-seçim yanlılığıdır ve rakam şerhsiz okunamaz. Takvim kapısı
FAIL-CLOSED: XNYS takvimi yoksa "ay-sonu mu" sorusu CEVAPSIZDIR ve karar alınmaz (olaylı
sessizlik); ay-sonunu barlardan türetmek canlıda yanlış olurdu. İleri-doldurulan hücre, eğri
satırı ve karar BAYRAKLA ayırt edilir; fiyatsız satış uydurulmaz, ölçülemeyen bayatlık iddia
edilmez, kırpmalar sayaçla beyanlıdır.

OKUR: çağıranın geçirdiği barlar + endeks; adapters.data (XNYS seansları, bütünlük defteri,
REPLAY_UNIVERSE).  YAZAR: yalnız kendi defteri `state/trend_book.json`.
"""
from __future__ import annotations

import datetime as dt
import math
import os

import pandas as pd

from . import obs, store
from .adapters import data as data_adapter

# ---------------------------------------------------------------- şasi sabitleri (BİREBİR)
FRICTION_BPS = 10.0        # engine.py:21  — 10 bps / bacak (alış ve satış)
ATR_LEN = 22               # engine.py:22  — ATR22
CHANDELIER_K = 3.5         # engine.py:23  — chandelier = tepe - 3.5 × ATR22
N_SLOTS = 10               # incumbent hücresi (N=10)
MOM_LOOKBACK = 12          # 12-1: P(ay-sonu t-1) / P(ay-sonu t-12) - 1  (engine.py:171-190)
INIT_EQUITY = 100_000.0    # SANAL sermaye (brief); şaside 1M — oransal muhasebe, getiri aynı

BOOK = "trend_book.json"
SCHEMA = 1
ENABLED = os.environ.get("MERIDIAN_TREND_SHADOW", "1") != "0"

# Karar penceresi: 13 ay-sonu (12-1 çapası) + ATR22 ısınması. 340 seans ≈ 16 ay — kuyruk
# `loop.SCAN_TAIL_BARS` ile aynı büyüklükte bilinçli seçildi (ölçüldü: 12 ay-sonu geriye ≈ 252 seans).
TAIL_SESSIONS = 340
EQUITY_CAP = 2500          # ~10 yıl günlük M2M; kırpma SAYILIR (equity_dusen)
CLOSED_CAP = 500           # kapanan işlem kuyruğu; kırpma SAYILIR (closed_toplam)
CATCHUP_MAX = 40           # bu kadar seanstan büyük boşluk UYARI üretir (yine de işlenir)
DELIST_GRACE = 10          # tutulan sembolün son barı bu kadar seans geride kaldıysa "no_data"
# İLERİ-DOLDURMA BAYRAĞININ KOLON ADI. Alt çizgi bilerek: bu bir PİYASA kolonu
# değil, hücrenin KÖKENİ hakkında bir şerh. Kolon `_dilim`de üretilir ve `_karar` onu sayarak
# kararın kendi bayrağını yazar — böylece "hangi karar hangi doldurmayla alındı" cevaplanabilir.
DOLDU_KOL = "_dolduruldu"

PIT_SERH = (
    "KALICI PIT ŞERHİ (EDG-2026-009 hükmü, Rol-1, 2026-07-31): bu kolun ölçülen +13,1p/yıl "
    "fazlasının BÜYÜK KISMI evren-seçim yanlılığıdır. PIT-sağkalan evrende fazla C +6,03 (t=1,77) / "
    "D +7,25 (t=2,08); rakam bundan böyle 'yanlılık-düşülmüş ~6-7p/yıl' şerhiyle anılır. ÜST-SINIR "
    "beyanı geçerli: fiyatlar PIT değildir (ölü/çıkmış isimler fiyatlanamıyor), gerçek PIT getirisi "
    "bundan da DÜŞÜK olabilir. Bu defter SANALDIR: sıfır yetki, gerçek emir yoluyla teması yoktur."
)


# ---------------------------------------------------------------- kitap
def yeni_kitap(now: str | None = None) -> dict:
    return {"schema": SCHEMA, "created": now or _now(), "positions": {}, "closed": [],
            "equity": [], "last_run": None, "pit_serh": PIT_SERH,
            # --- şemanın taşıyıcı ekleri (brief'in çekirdeğinin üstüne) ---
            "cash": INIT_EQUITY,          # nakit olmadan M2M kurulamaz
            "last_session": None,         # birikim noktası (idempotanlık)
            "pending": None,              # ay-sonu kararı → ERTESİ seans açılışında icra
            "sayaclar": {"entries": 0, "exits": {}, "closed_toplam": 0, "equity_dusen": 0,
                         "friction_paid": 0.0, "kararsiz_gun": 0}}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _kaydet(kitap: dict) -> None:
    store.write_json(BOOK, kitap)


# ---------------------------------------------------------------- takvim
_AY_SONU: dict = {}      # (yıl, ay) → o ayın SON XNYS seansı (str) — süreç-içi


def ay_sonu_mu(d) -> bool | None:
    """d, kendi takvim ayının SON XNYS seansı mı? Takvim yoksa None (= cevap yok, fail-closed).

    Takvim kaynağı `adapters.data._sessions()`tir — depodaki TEK XNYS seans kümesi (süreç başına
    bir kez üretilir). İkinci bir `pandas_market_calendars` çağrısı açmak "aynı zaman iki kaynak"
    ayrışmasıdır; bu depoda belgeli kusur sınıfı (bkz. barclock.py başlığı)."""
    ses = data_adapter._sessions()
    if not ses:
        return None
    d = pd.Timestamp(d)
    key = (d.year, d.month)
    son = _AY_SONU.get(key)
    if son is None:
        onek = f"{d.year:04d}-{d.month:02d}-"
        ayin = [s for s in ses if s.startswith(onek)]
        if not ayin:
            return None                       # takvimin kapsamadığı ay hakkında HÜKÜM YOK
        son = max(ayin)
        _AY_SONU[key] = son
    return str(d.date()) == son


# ---------------------------------------------------------------- bar yardımcıları
def _norm(bars: dict) -> dict:
    """{sembol: tarih-indeksli, sıralı OHLCV}. Çağıran ham (date sütunlu) ya da indeksli verebilir."""
    per = {}
    for t, df in (bars or {}).items():
        if df is None or len(df) == 0:
            continue
        d = df.set_index("date") if "date" in getattr(df, "columns", []) else df
        per[str(t).upper()] = d.sort_index()
    return per


def _master(index) -> pd.DatetimeIndex | None:
    """Ana takvim = ENDEKS (SPY) seansları — şasinin `build_panel(calendar_symbol="SPY")` yolu."""
    if index is None or len(index) == 0:
        return None
    idx = index.set_index("date") if "date" in getattr(index, "columns", []) else index
    return pd.DatetimeIndex(idx.sort_index().index)


def _son_kapanis(df, s) -> tuple:
    """(kapanış, bar_tarihi) — s'te ya da ÖNCESİNDE bilinen son kapanış (şasinin ömür-içi ffill'i).
    Hiç bar yoksa (None, None). Bayatlık ÇAĞIRANA bırakılır (`_bayat_mi`): burası fiyat verir,
    o fiyatın hâlâ meşru olup olmadığına karar vermez."""
    if df is None or len(df) == 0:
        return None, None
    sub = df.index[df.index <= s]
    if len(sub) == 0:
        return None, None
    son = sub[-1]
    px = df.at[son, "close"]
    if px is None or (isinstance(px, float) and math.isnan(px)):
        return None, None
    return float(px), son


def _bayat_mi(bar_tarihi, s, mpos: dict) -> bool:
    """Sembolün son barı DELIST_GRACE seanstan fazla geride mi? (şasinin last_valid_index sonrası
    NaN bölgesinin canlı karşılığı — orada kapanış NaN'dır ve pozisyon `no_data` ile kapanır)."""
    i_s, i_b = mpos.get(s), mpos.get(bar_tarihi)
    if i_s is None or i_b is None:
        return False                          # ölçülemeyen bayatlık iddia EDİLMEZ
    return (i_s - i_b) > DELIST_GRACE


def _dilim(per: dict, semboller, tail: pd.DatetimeIndex) -> dict:
    """Şasinin `build_panel` semantiği, kuyruk penceresinde: her sembol ANA TAKVİME yeniden
    indekslenir ve KENDİ ÖMRÜ İÇİNDE ffill edilir (listelenmeden önce/sonrası NaN kalır —
    bakma-ileri yok, engine.py:55-61).

    HÜCRE DÜZEYİNDE KÖKEN BAYRAĞI. Bu ffill EKRANA
    ULAŞIYOR — sıralama buradan çıkıyor, karar oradan, defter oradan, `api.py`nin `trend_kitabi`
    alanı da oradan. Doldurma sınırlı ve docstring'de dürüstçe belgelenmişti, ama ETİKETSİZDİ:
    web katmanında "dolduruldu" dizesi SIFIR kez geçiyordu, yani okuyucu ileri-taşınmış bir
    kapanışla ölçülmüş bir kapanışı aynı mürekkeple okuyordu. Design rules: *"Null renders as an
    explicit gap with a reason — never interpolated."* Doldurmanın kendisi meşru (şasi ile birebir
    aynı semantik); ETİKETSİZ olması değildi.

    BAYRAK VERİNİN YANINDA DURUR, AYRI BİR SÖZLÜKTE DEĞİL: ikinci bir nesne dönmek hem imzayı
    (ve dış çağıranları) kırardı, hem de maske ile veri iki ayrı yerde yaşasaydı ilk düzenlemede
    ayrışırdı — bu deponun tekrar eden kusur sınıfı. `DOLDU_KOL` alt çizgiyle başlar: bir PİYASA
    kolonu değil, bir köken şerhidir.

    MASKE FFILL'DEN ÖNCE ALINIR: doldurulduktan sonra doldurulmuş hücre ölçülmüş hücreden ayırt
    edilemez. Sonra ömür penceresine kırpılır — ömür DIŞINDA kalan NaN'lar doldurulmadı, sayılmaz.
    """
    out = {}
    for t in semboller:
        df = per.get(t)
        if df is None or len(df) == 0:
            continue
        r = df.reindex(tail)
        fv, lv = r["close"].first_valid_index(), r["close"].last_valid_index()
        if fv is None:
            continue
        bosluk = r["close"].isna()                       # ffill'den ÖNCE: doldurulacak hücreler
        omur = pd.Series(False, index=r.index)
        omur.loc[fv:lv] = True
        r.loc[fv:lv] = r.loc[fv:lv].ffill()
        r[DOLDU_KOL] = bosluk & omur                     # ffill'den SONRA: maskenin kendisi dolmaz
        out[t] = r
    return out


def dolduruldu_n(r) -> int:
    """Bir dilim karesinde ileri-doldurulmuş hücre sayısı. Bayrak kolonu yoksa 0 — bu bir
    'ölçülemedi' değil, 'bu kare `_dilim`den geçmedi' hâlidir (çağıranlar hepsi geçirir)."""
    if r is None or DOLDU_KOL not in getattr(r, "columns", []):
        return 0
    return int(r[DOLDU_KOL].sum())


def _atr(r: pd.DataFrame):
    """ATR22 — şasi ile aynı: TR = max(h-l, |h-pc|, |l-pc|), rolling(22, min_periods=22).mean()
    (engine.py:75-78). Son değeri NaN ise aday/çıkış kuralı onu 'ölçülemedi' sayar."""
    pc = r["close"].shift(1)
    tr = pd.concat([(r["high"] - r["low"]).abs(), (r["high"] - pc).abs(), (r["low"] - pc).abs()],
                   axis=1).max(axis=1)
    return tr.rolling(ATR_LEN, min_periods=ATR_LEN).mean()


def _ay_sonlari(tail: pd.DatetimeIndex) -> list:
    """Kuyruk penceresindeki ay-sonu seansları (şasi: master.groupby([year, month]).max())."""
    s = pd.Series(tail, index=tail)
    return sorted(pd.Timestamp(x) for x in s.groupby([tail.year, tail.month]).max().tolist())


def _uygunluk() -> dict:
    """Canlı bütünlük defteri: {SEMBOL: güvenli_başlangıç}. Defter yoksa boş (kısıt yok — deponun
    kendi fail-open kuralı; bkz. adapters.data.bars_integrity)."""
    try:
        sem = (data_adapter.bars_integrity().get("semboller") or {})
        return {str(k).upper(): (v or {}).get("guvenli_baslangic") for k, v in sem.items()}
    except Exception as e:
        obs.warn("trend_shadow_uygunluk_okunamadi", error=f"{type(e).__name__}: {e}",
                 detail="bütünlük defteri okunamadı — kısıtsız devam (defterin yokluğu evreni susturmaz)")
        return {}


def _uygun(harita: dict, t: str, rd) -> bool:
    gs = harita.get(t.upper())
    return (not gs) or str(pd.Timestamp(rd).date()) >= str(gs)


# ---------------------------------------------------------------- seans işleme
def _icra(kitap: dict, xd, per: dict, mpos: dict) -> None:
    """AY-SONU KARARININ İCRASI — ERTESİ SEANS AÇILIŞI (engine.py:198-260 ile aynı sıra):
    çıkışlar → 1/N'e denkleştirme → girişler. Açılış yoksa şasinin yedeği: karar gününün kapanışı."""
    bekleyen = kitap.get("pending") or {}
    rd = pd.Timestamp(bekleyen["date"])
    fee = FRICTION_BPS / 10_000.0
    pos = kitap["positions"]
    say = kitap["sayaclar"]

    def _acilis(t):
        df = per.get(t)
        if df is not None and xd in df.index:
            p = df.at[xd, "open"]
            if p is not None and not (isinstance(p, float) and math.isnan(p)) and float(p) > 0:
                return float(p)
        px, _ = _son_kapanis(per.get(t), rd)            # şasinin close_v.at[rd,t] yedeği
        return px

    # ---- 1) ÇIKIŞLAR
    for t, sebep in bekleyen.get("exits") or []:
        p0 = pos.pop(t, None)
        if p0 is None:
            continue
        p = _acilis(t)
        if p is None or p <= 0:
            pos[t] = p0                                  # fiyatsız satış UYDURULMAZ — pozisyon durur
            obs.warn("trend_shadow_cikis_fiyatsiz", ticker=t, session=str(xd.date()),
                     detail="açılış ve son kapanış yok — çıkış ertelendi, sanal pozisyon korundu")
            continue
        gelir = p0["shares"] * p
        kitap["cash"] += gelir * (1 - fee)
        say["friction_paid"] = round(float(say.get("friction_paid", 0.0)) + gelir * fee, 4)
        say["exits"][sebep] = int(say["exits"].get(sebep, 0)) + 1
        maliyet = p0["shares"] * p0["entry_price"]
        kitap["closed"].append({
            "sym": t, "entry": p0["entry_date"], "exit": str(xd.date()), "reason": sebep,
            "entry_px": round(p0["entry_price"], 6), "exit_px": round(p, 6),
            "shares": round(p0["shares"], 6),
            "getiri_pct": round((p / p0["entry_price"] - 1.0) * 100.0, 4),
            "pnl_dollars": round(gelir - maliyet, 2)})
        say["closed_toplam"] = int(say.get("closed_toplam", 0)) + 1

    px_open = {t: _acilis(t) for t in set(list(pos) + list(bekleyen.get("entries") or []))}
    eq = kitap["cash"] + sum(p["shares"] * px_open[t] for t, p in pos.items()
                             if px_open.get(t))
    per_slot = eq / N_SLOTS

    # ---- 2) 1/N'e DENKLEŞTİRME (sizing="rebalance" — incumbent birincil boyutlandırma)
    for t in list(pos):
        p = px_open.get(t)
        if not p or p <= 0:
            continue
        d = per_slot / p - pos[t]["shares"]
        if abs(d * p) < 1e-9:
            continue
        notional = abs(d) * p
        if d > 0:
            cost = notional * (1 + fee)
            if cost > kitap["cash"]:
                d = (kitap["cash"] / (1 + fee)) / p
                notional, cost = abs(d) * p, abs(d) * p * (1 + fee)
            kitap["cash"] -= cost
        else:
            kitap["cash"] += notional * (1 - fee)
        say["friction_paid"] = round(float(say.get("friction_paid", 0.0)) + notional * fee, 4)
        pos[t]["shares"] += d

    # ---- 3) GİRİŞLER
    for t in bekleyen.get("entries") or []:
        if t in pos:
            continue
        p = px_open.get(t)
        if not p or p <= 0:
            continue
        butce = min(per_slot, kitap["cash"] / (1 + fee))
        if butce <= 0:
            break
        q = butce / p
        kitap["cash"] -= q * p * (1 + fee)
        say["friction_paid"] = round(float(say.get("friction_paid", 0.0)) + q * p * fee, 4)
        pos[t] = {"shares": q, "entry_date": str(xd.date()), "entry_price": p,
                  "peak_high": p,                       # şasi: peak_high[t] = giriş fiyatı
                  "last_close": p}
        say["entries"] = int(say.get("entries", 0)) + 1

    # KIRPMA SESSİZ DEĞİL: kuyruk `CLOSED_CAP` satırla sınırlı ama `closed_toplam` sayacı ömür
    # boyu artar — defterin "kaç işlem kapandı" cevabı kırpmadan bağımsız kalır.
    if len(kitap["closed"]) > CLOSED_CAP:
        kitap["closed"] = kitap["closed"][-CLOSED_CAP:]
    kitap["pending"] = None


def _isaretle(kitap: dict, s, per: dict) -> list:
    """GÜNLÜK M2M + chandelier tepe takibi. Barı olmayan sembol için ŞASİNİN ffill'i uygulanır
    (son bilinen kapanış); atlanan sembol SAYILIR ve olayla duyurulur — sessiz boşluk yok.

    SATIR DÜZEYİNDE KÖKEN BAYRAĞI: olay defterine yazılan sayı bir OLAYdır, satırın
    kendisinde durmuyordu — yani eğrideki bir noktaya bakıp "bu değer ölçüldü mü, taşındı mı"
    sorusu ekrandan da defterden de cevaplanamıyordu. Bayrak artık SATIRIN İÇİNDE: `dolduruldu` =
    o seans kendi barı olmadığı için SON BİLİNEN KAPANIŞLA işaretlenen pozisyon sayısı.

    ÜÇ HÂL AYIRT EDİLEBİLİR OLMAK ZORUNDA ve alan HER YENİ SATIRDA yazılır (0 olsa bile):
      * `dolduruldu` yok      → satır bu bayraktan ÖNCE yazıldı; doldurma ÖLÇÜLEMEZ (uydurma yok)
      * `dolduruldu` == 0     → ölçüldü, hiçbir pozisyon taşınmadı
      * `dolduruldu` > 0      → ölçüldü, N pozisyon ileri taşındı
    SCHEMA BİLEREK ARTIRILMADI: `run_cycle` şema uyuşmazlığında kitabı SIFIRDAN doğuruyor
    (`yeni_kitap()`), yani bir sürüm artışı CANLI gölge-defteri silerdi. Eski satırların bayraksız
    kalması bir kusur değil ölçülmüş bir sınırdır ve `ozet()` onu ADIYLA dışarı verir.
    """
    v = kitap["cash"]
    eksik = []
    for t, p in kitap["positions"].items():
        df = per.get(t)
        if df is not None and s in df.index:
            c, h = df.at[s, "close"], df.at[s, "high"]
            if c is not None and not (isinstance(c, float) and math.isnan(c)):
                p["last_close"] = float(c)
            if h is not None and not (isinstance(h, float) and math.isnan(h)):
                p["peak_high"] = max(float(p.get("peak_high") or 0.0), float(h))
        else:
            eksik.append(t)
        lc = p.get("last_close")
        if lc:
            v += p["shares"] * lc
    kitap["equity"].append({"date": str(s.date()), "equity": round(float(v), 2),
                            "dolduruldu": len(eksik)})
    if len(kitap["equity"]) > EQUITY_CAP:
        kitap["sayaclar"]["equity_dusen"] = int(kitap["sayaclar"].get("equity_dusen", 0)) + (
            len(kitap["equity"]) - EQUITY_CAP)
        kitap["equity"] = kitap["equity"][-EQUITY_CAP:]
    return eksik


def _karar(kitap: dict, rd, per: dict, master: pd.DatetimeIndex, mpos: dict, uni: list) -> dict | None:
    """AY-SONU KARARI (engine.py:151-196 ile aynı sıra): çıkış kararı → 12-1 sıralaması → slot dolumu.
    İcra ETMEZ; kararı `pending` olarak bırakır (icra ertesi seans açılışında — bakma-ileri yok)."""
    i = mpos[rd]
    tail = master[max(0, i - TAIL_SESSIONS + 1): i + 1]
    me = _ay_sonlari(tail)
    gk = len(me) - 1
    if gk < MOM_LOOKBACK or me[-1] != rd:
        obs.log("trend_shadow_isinma", session=str(rd.date()), ay_sonu=len(me),
                gerekli=MOM_LOOKBACK + 1,
                detail="12-1 çapası için yeterli ay-sonu yok — karar alınmadı (uydurma sıralama yerine sessizlik)")
        kitap["sayaclar"]["kararsiz_gun"] = int(kitap["sayaclar"].get("kararsiz_gun", 0)) + 1
        return None
    a1, a12 = me[gk - 1], me[gk - MOM_LOOKBACK]

    tutulan = list(kitap["positions"])
    dilim = _dilim(per, sorted(set(uni) | set(tutulan)), tail)
    dolu = {t: dolduruldu_n(r) for t, r in dilim.items() if dolduruldu_n(r)}
    atr_son = {}
    for t, r in dilim.items():
        a = _atr(r)
        val = a.iloc[-1] if len(a) else float("nan")
        atr_son[t] = None if (val is None or math.isnan(float(val))) else float(val)
    harita = _uygunluk()

    # ---- 1) ÇIKIŞ KARARI (zorunlu + chandelier)
    to_close = []
    for t in tutulan:
        px, bar_t = _son_kapanis(per.get(t), rd)
        if px is None or (bar_t is not None and _bayat_mi(bar_t, rd, mpos)):
            to_close.append((t, "no_data")); continue
        if not _uygun(harita, t, rd):
            to_close.append((t, "integrity")); continue
        p = kitap["positions"][t]
        tepe = float(p.get("peak_high") or 0.0)
        a = atr_son.get(t)
        if a is None or tepe <= 0:
            continue                                   # ölçülemeyen durakla pozisyon kapatılmaz
        if px < tepe - CHANDELIER_K * a:
            to_close.append((t, "chandelier"))

    # ---- 2) 12-1 MOMENTUM SIRALAMASI
    rows = []
    for t in uni:
        r = dilim.get(t)
        if r is None:
            continue
        # ÇAPALAR YAPISAL OLARAK KUYRUĞUN İÇİNDEDİR (`me` zaten `tail`den türetildi); kontrol
        # bir istisna yakalayıcısı DEĞİL bir üyelik kapısıdır — sessiz yutma yüzeyi açmaz.
        if not (a1 in r.index and a12 in r.index and rd in r.index):
            continue
        p1, p12, pnow = r.at[a1, "close"], r.at[a12, "close"], r.at[rd, "close"]
        if any(x is None or (isinstance(x, float) and math.isnan(x)) for x in (p1, p12, pnow)):
            continue
        if float(p12) <= 0:
            continue
        df = per.get(t)
        if df is None or rd not in df.index:            # şasi: panel.real.at[rd, t]
            continue
        if atr_son.get(t) is None:                      # şasi: ATR22 NaN → aday değil
            continue
        if not _uygun(harita, t, rd):                   # şasi: elig (bütünlük katmanı)
            continue
        rows.append((t, float(p1) / float(p12) - 1.0))
    rows.sort(key=lambda x: -x[1])
    picks = [t for t, _ in rows]

    # ---- 3) SLOT DOLUMU: listeden düşen KAPANMAZ (incumbent akış — rotasyon çıkışı YOK)
    cikan = {t for t, _ in to_close}
    kalan = [t for t in tutulan if t not in cikan]
    slots = N_SLOTS - len(kalan)
    entries = [t for t in picks if t not in kitap["positions"]][:max(slots, 0)] if slots > 0 else []
    # KARARIN KÖKEN BAYRAĞI. Sıralama penceresinde kaç hücre İLERİ DOLDURULDU ve
    # kaç sembol en az bir doldurulmuş hücre taşıdı — karar nesnesinin İÇİNDE, ayrı bir defterde
    # değil. Ayrı yazılsaydı ilk düzenlemede karardan ayrışır ve "hangi karar hangi doldurmayla
    # alındı" sorusu cevapsız kalırdı. `dolduruldu_sembol` sıralamaya GİREN sembol sayısı değildir:
    # pencerede doldurulmuş hücresi olan sembol sayısıdır (aday olmayanlar da dahil) — çünkü ffill
    # sıralamanın PAYDASINI da (kimin p1/p12'si var) etkiler.
    return {"date": str(rd.date()), "exits": to_close, "entries": entries,
            "aday": len(picks), "en_iyi": picks[:N_SLOTS],
            "dolduruldu": int(sum(dolu.values())), "dolduruldu_sembol": len(dolu)}


# ---------------------------------------------------------------- dış yüzey
def ozet(kitap: dict | None) -> dict:
    """daily_cycle olayının + panonun okuduğu ÖZET. Kitap yoksa 'doğmadı' der (boş kart dürüsttür).

    DOLDURMA KÖKENİ RAKAMLA BİRLİKTE ÇIKAR. `equity` alanı EĞRİNİN SON
    SATIRIDIR ve o satır ileri-doldurulmuş olabilir; şerhi ayrı bir uca koymak, rakamı şerhsiz
    okutmanın en kolay yoluydu (aynı gerekçe `pit_serh` için de yazılı — bu kartın kendi dersi).
      son_dolduruldu    → BASILAN sayının kendi bayrağı: o seans kaç pozisyon taşındı
                          (None = satır bayraktan önce yazıldı, ÖLÇÜLEMEZ — 0 DEĞİL)
      dolduruldu_gun    → eğride en az bir pozisyonu taşınmış seans sayısı
      dolduruldu_olcumsuz → bayraksız (eski) satır sayısı; sessizce 0'a katlanmaz
      karar_dolduruldu  → bekleyen ay-sonu kararının sıralama penceresindeki doldurulmuş hücre
                          sayısı (None = bekleyen karar yok ya da karar bayraktan önce alındı)
    """
    if not kitap:
        return {"var": False, "pozisyon": 0, "equity": None}
    eq = kitap.get("equity") or []
    son = eq[-1]["equity"] if eq else None
    ilk = eq[0]["equity"] if eq else None
    # `in` TESTİ ŞART, `get(...) or 0` DEĞİL: ikincisi "ölçüldü, sıfır" ile "bayrak yok"u aynı
    # piksele düşürürdü — bu deponun ÖLÇÜLEMEDİ≠0 yasasının tam ihlali.
    son_satir = eq[-1] if eq else {}
    bekleyen = kitap.get("pending") or {}
    return {"var": True, "pozisyon": len(kitap.get("positions") or {}),
            "equity": son, "nakit": round(float(kitap.get("cash") or 0.0), 2),
            "getiri_pct": (round((son / ilk - 1.0) * 100.0, 3) if son and ilk else None),
            "kapanan": int((kitap.get("sayaclar") or {}).get("closed_toplam", 0)),
            "last_session": kitap.get("last_session"), "last_run": kitap.get("last_run"),
            "gun": len(eq), "pit_serh": kitap.get("pit_serh"),
            "son_dolduruldu": (int(son_satir["dolduruldu"]) if "dolduruldu" in son_satir else None),
            "dolduruldu_gun": sum(1 for r in eq if int(r.get("dolduruldu") or 0) > 0),
            "dolduruldu_olcumsuz": sum(1 for r in eq if "dolduruldu" not in r),
            "karar_dolduruldu": (int(bekleyen["dolduruldu"]) if "dolduruldu" in bekleyen else None)}


def run_cycle(bars: dict, index, on_date: str | None = None) -> dict:
    """GÜNLÜK ÇAĞRI (loop.daily_cycle kancası). Kitabı `last_session`dan `on_date`e kadar yürütür.

    Çağıranı ASLA düşürmez sözleşmesi ÇAĞIRANDA durur (loop try/except + obs.warn): burada
    yutulan tek şey yok — hata yukarı çıkar ve kancada ADIYLA kaydedilir."""
    if not ENABLED:
        return {"status": "disabled"}
    per = _norm(bars)
    master = _master(index)
    if master is None or len(master) < 2:
        obs.warn("trend_shadow_endeks_yok",
                 detail="ana takvim (endeks barları) yok — gölge-kitap bu tur işlemedi")
        return {"status": "no_index"}
    if on_date:
        master = master[master <= pd.Timestamp(on_date)]
    if len(master) < 2:
        return {"status": "no_index"}
    mpos = {d: i for i, d in enumerate(master)}
    uni = [t for t in data_adapter.REPLAY_UNIVERSE if t in per]

    kitap = store.read_json(BOOK, None)
    if not kitap or int(kitap.get("schema") or 0) != SCHEMA:
        kitap = yeni_kitap()
        s0 = master[-1]
        kitap["last_session"] = str(s0.date())
        kitap["equity"] = [{"date": str(s0.date()), "equity": INIT_EQUITY}]
        kitap["last_run"] = _now()
        _kaydet(kitap)
        obs.log("trend_book_dogdu", session=str(s0.date()), evren=len(uni),
                sermaye=INIT_EQUITY, n_slot=N_SLOTS,
                detail="gölge-kitap BOŞ doğdu (geri-doldurma yok); ilk giriş ilk ay-sonunda")
        return {"status": "born", **ozet(kitap)}

    son = str(kitap.get("last_session") or "")
    yeni = [d for d in master if str(d.date()) > son]
    if not yeni:
        return {"status": "noop", **ozet(kitap)}
    if len(yeni) > CATCHUP_MAX:
        obs.warn("trend_shadow_bosluk", session=str(yeni[-1].date()), atlanan=len(yeni),
                 son_islenen=son, detail="kitap uzun süre işlemedi — tüm ara seanslar yürütülüyor")

    kararlar, eksikler = 0, {}
    for s in yeni:
        if kitap.get("pending"):
            _icra(kitap, s, per, mpos)
        eks = _isaretle(kitap, s, per)
        if eks:
            eksikler[str(s.date())] = eks
        ae = ay_sonu_mu(s)
        if ae is None:
            obs.warn("trend_shadow_takvim_yok", session=str(s.date()),
                     detail="XNYS takvimi yok — 'ay-sonu mu' sorusu CEVAPSIZ, karar alınmadı (fail-closed)")
            kitap["sayaclar"]["kararsiz_gun"] = int(kitap["sayaclar"].get("kararsiz_gun", 0)) + 1
        elif ae:
            karar = _karar(kitap, s, per, master, mpos, uni)
            if karar:
                kitap["pending"] = karar
                kararlar += 1
                obs.log("trend_book_karar", session=str(s.date()), aday=karar["aday"],
                        cikis=len(karar["exits"]), giris=len(karar["entries"]),
                        en_iyi=",".join(karar["en_iyi"]),
                        detail="ay-sonu kararı — icra ERTESİ seans açılışında (bakma-ileri yok)")

    if eksikler:
        obs.log("trend_shadow_bar_eksik", seans=len(eksikler),
                ornek=",".join(sorted({t for v in eksikler.values() for t in v}))[:200],
                detail="tutulan sembolün o gün barı yok — son bilinen kapanışla işaretlendi (şasi ffill'i)")
    kitap["last_session"] = str(yeni[-1].date())
    kitap["last_run"] = _now()
    kitap["pit_serh"] = PIT_SERH        # şerh KİTAPTAN düşemez: her yazımda yeniden çakılır
    _kaydet(kitap)
    o = ozet(kitap)
    obs.log("trend_book_cycle", session=kitap["last_session"], seans=len(yeni), karar=kararlar,
            pozisyon=o["pozisyon"], equity=o["equity"])
    return {"status": "ok", "sessions": len(yeni), "kararlar": kararlar, **o}
