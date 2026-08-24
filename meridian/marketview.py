"""marketview.py — izlenen evrenin tek bakışta okunan görüntüsü; pano "Piyasa" sekmesinin tek kaynağı.

NE YAPAR. Pano eskiden yalnız KARARA girmiş sembolleri gösteriyordu (aday, plan, pozisyon); kapının
elediği 250 sembol, elenmedikleri için değil hiç GÖRÜNMEDİKLERİ için yoktu. `build()` motorun bar
tuttuğu evreni (`state/bars/*.csv`) satır satır özetler — son kapanış, 1g/20g değişim, 52 haftalık
zirveye uzaklık, ADV20, spark — ve defterlerden bağlam ekler: pozisyon/silahlı bayrakları, plan
sayısı ve son plan tarihi, bir SONRAKİ kazanç-raporu tarihi. CSV çekirdekleri mtime anahtarlı
süreç-içi önbellekten okunur; okunamayan bar dosyası sembolü DÜŞÜRMEZ (ölçümsüz satır + uyarı —
"izleniyor ama okunamıyor" bilgisinin kendisi sinyaldir).

DEĞİŞMEZLER. Bu bir FİYAT SERVİSİ DEĞİLDİR: her sayı EOD (kapanmış günlük) bardan türer, canlı
fiyat iddia edilmez; en taze bar hangi seanstansa `as_of` odur ve geride kalanlar `stale_n` ile
ADIYLA sayılır — bayat kapanışı taze göstermek panonun okura yalan söylemesidir. `intraday_close`
bu çizgiyi bozmaz, DARALTIR: yalnız SİLAHLI sembollerde doludur (dakikalık akış yalnız onları
izler) ve değeri sıcak fiyat değil KAPANMIŞ dakikalık barın kapanışıdır; tazelik eşiği
(STALE_TOL_S) intraday_cycle'dan TEK KAYNAK alınır — ikinci bir eşik kopyası zamanla ayrışan iki
yasa demekti. ÖLÇÜLEMEYEN None KALIR (UYDURMA YASAĞI): 21 barı olmayan sembolün 20 günlük
değişimi yoktur, 0.0 "değişmedi" diye okunurdu. Emekli semboller satır olarak KALIR (bar geçmişi
gerçek) ama bayatlık ölçümüne GİRMEZ — delist gününde donmuş bar kalıcı gürültü üretirdi. Seans
içi kolonun boşluğu da nedenli beyan edilir: "silahlı yok" / "akış yok" / "akış bayat" aynı
sessizliğe indirgenmez.

SERİ (2026-08-24). Pano her satıra kıvılcım grafiği çizecek; `build(seri=True)` (uçta `?seri=1`)
her satıra son `_SERI_BARS` KAPANIŞI `seri` alanıyla ekler ve VARSAYILAN KAPALIDIR — seriyi
çizmeyen tüketicinin yükü büyümez. Aynı disiplin burada da geçerlidir: barı olmayan sembol boş
dizi DEĞİL `null` alır ve nedeni `seri_yok_nedeni`nde YAZILIR (boş dizi kıvılcımda düz çizgi
çizdirir — "fiyat kıpırdamadı" diye okunur), 40 barı olmayan sembolde eldeki kadarı DOLGUSUZ
gider ve `n` gerçek sayıdır. `bar_serisi()` aynı yasayı tek sembolün DERİN (OHLCV) serisi için
tekrarlar: tavanlı, tavanı beyan eden (`kirpildi`), bilinmeyen sembolde 404 yerine nedenli boşluk.
İKİSİ DE EOD'dur — `son_tarih`/`as_of` hangi seansa kadar ölçüldüğünü söyler, "canlı fiyat" DEĞİL.

NEYİ OKUR. `state/bars/*.csv`, `portfolio.json`, `trade_plans.jsonl`, `regime.json`,
`finviz_universe.json`, kazanç takvimi (earnings) ve sıcak katman (hotstate — yalnız silahlılar).
Hiçbir şey yazmaz.
"""
from __future__ import annotations

import datetime as dt
import math
import re as _re
from pathlib import Path

import pandas as pd

from . import barclock, config, earnings, hotstate, store
# EMEKLİLİK DEFTERİ TEK KAYNAKTAN: hangi sembolün delist olduğu `adapters.data`da
# yazılıdır. Buraya ikinci bir liste kopyalamak, zamanla AYRIŞAN iki gerçek demekti.
from .adapters import data as _data
# TAZELİK YASASI TEK KAYNAKTAN: intraday_cycle karar verirken hangi eşiği kullanıyorsa ölçüm de
# onu kullanır. Buraya ikinci bir "120" yazmak, zamanla AYRIŞAN iki yasa demekti — pano "taze"
# derken motorun "bayat" dediği bir barı gösterebilirdi. intraday_cycle marketview'ü import
# ETMEZ (yalnız barclock/hotstate/store/obs/health), yani döngü yok.
from .intraday_cycle import STALE_TOL_S

# Pencereler. Hepsi BAR sayısıdır (takvim günü değil): 252 bar ≈ 52 hafta, 20 bar ≈ bir ay.
_SPARK_BARS = 60
_ADV_BARS = 20
_CHG20_BARS = 21          # 20 GÜNLÜK değişim 21 kapanış ister (t ile t-20)
_HIGH_BARS = 252

# SATIR-İÇİ KIVILCIM GRAFİĞİNİN (sparkline) PENCERESİ — `?seri=1` ile İSTENİR (aşağı bak).
# NEDEN 40: 40 seans ≈ iki takvim ayı (5 iş günü × 8 hafta). Alt sınır okunabilirlikten gelir —
# 20 barlık bir pencerede tek bir kazanç günü tüm eğriyi domine eder ve kıvılcım "bu hisse ne
# yapıyor?" sorusunu değil "dün ne oldu?" sorusunu cevaplar; üst sınır ise satır yüksekliğinden —
# 120 kapanış 40 piksellik bir satıra sıkıştığında çizgi okunmaz mürekkebe döner. `_SPARK_BARS`
# (60) ile BİLEREK AYRIŞIR: `spark` başka bir tüketicinin alanıdır ve birini diğerinin sabitine
# bağlamak, birini değiştirenin ötekini sessizce bozması demekti.
_SERI_BARS = 40

# YÜK ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (2026-08-24, 260 sembollük canlı `state/bars`, JSON bayt olarak,
# `store.sanitize` sonrası ve uçtaki gibi ayraçsız):
#     /api/market            195.959 bayt (191,4 KB)   ← DEĞİŞMEDİ
#     /api/market?seri=1     290.615 bayt (283,8 KB)   ← seri alanının payı 94.656 bayt (92,4 KB)
# 400 KB bütçesinin altında kalındığı için kapanışlar YUVARLANMADAN gider. Ölçülen alternatif:
# kuruşa yuvarlamak aynı 260×40 diziyi 93.125 → 92.990 bayta indiriyordu (135 bayt, %0,1) —
# hassasiyet kaybı bedava değil (bölünme/temettü düzeltmeli fiyatlar kuruş altı ondalık taşır) ve
# karşılığı ölçülebilir bir kazanç değil. Bütçe bir gün aşılırsa çözüm örneklem SEYRELTMEK
# DEĞİLDİR (seyreltilmiş bir grafik, olmayan bir fiyat yolu çizer): önce yuvarlama, sonra
# pencereyi kısaltma — ikisi de bu yorumda gerekçesiyle güncellenerek.

# {csv mutlak yolu: (mtime_ns, satır çekirdeği)} — SÜREÇ-İÇİ önbellek.
# İlk çağrı 260 CSV okur (kabul edilen bedel); sonraki her çağrı dosyanın mtime'ı DEĞİŞMEDİKÇE
# diske hiç inmez. EOD dosyaları günde bir kez yazıldığı için isabet oranı fiilen 1'dir — pano
# 15 saniyede bir tazelendiğinde aynı 260 dosyayı yeniden ayrıştırmak saf israftı.
# Anahtar MUTLAK yoldur: sandbox'lı testler canlı önbellekle aynı gözü paylaşmaz.
_CACHE: dict[str, tuple[int, dict]] = {}

# Bar'dan türeyen alanların ÖLÇÜLMEMİŞ hâli. Tek yerde durur ki "barı olmayan satır" (finviz
# ekstrası) ile "barı okunamayan satır" aynı dürüst şekli taşısın.
_EMPTY_CORE: dict = {"last_date": None, "close": None, "chg1_pct": None, "chg20_pct": None,
                     "dist_52w_high_pct": None, "adv20_usd": None, "spark": []}

# SERİ ALANLARI `_EMPTY_CORE`UN DIŞINDA DURUR ve bu bilinçlidir: satır kurulurken YALNIZ
# `_EMPTY_CORE` anahtarları kopyalanır (`_satir`), dolayısıyla seri istenmeyen çağrının yükü
# BİREBİR eskisi gibi kalır. Çekirdek yine de her zaman hesaplanır — çünkü çekirdek mtime
# anahtarlı önbelleğin İÇİNDEDİR; seriyi dışarıda hesaplamak, aynı CSV'yi ikinci bir yoldan
# okumak (ve önbelleği atlamak) demekti.
_SERI_YOK_DOSYA = "bar dosyası yok"
# BAŞLANGIÇ NEDENİ BOŞ DEĞİL: başarı yolunda seri en sonda doldurulur ve neden None'a çekilir.
# Buraya boş dizge koymak, ileride araya girecek bir erken `return`ün NEDENSİZ bir `null`
# üretmesi demekti — yani yasağın (nedensiz boşluk) kendi kodumuzda açtığı arka kapı.
_SERI_HESAPLANMADI = "seri hesaplanmadan dönüldü — çekirdek yarım kaldı (kod hatası)"


def _bos_cekirdek(seri_yok_nedeni: str) -> dict:
    """Ölçümsüz çekirdek + serinin NEDEN yok olduğunun beyanı. Boş dizi DÖNMEZ: `[]` bir kıvılcım
    grafiğinde düz çizgi çizdirir ve okuyucu onu "fiyat kıpırdamadı" diye okur — yokluk ile
    durgunluk aynı şekle indirgenemez (UYDURMA YASAĞI)."""
    return {**_EMPTY_CORE, "seri": None, "seri_yok_nedeni": seri_yok_nedeni}


def clear_cache() -> None:
    """Önbelleği boşalt. mtime değişmeden içeriğin değiştiği tek senaryo testlerdir; üretimde
    dosyayı yazan her yol mtime'ı da değiştirir."""
    _CACHE.clear()


def _f(x):
    """Sonlu float ya da None. NaN/±Inf 'ölçüldü' diye okunamaz (bkz. store.sanitize gerekçesi)."""
    try:
        v = float(x)
    except (TypeError, ValueError):  # sessiz-yutma: tek bir hücre sayı değil — YALNIZ o alan None olur, satır yaşar; 260 sembol × her tur uyarı asıl sinyali log seline gömerdi
        return None
    return v if math.isfinite(v) else None


def _pct(base, son):
    """`son`un `base`e göre yüzde farkı. base yoksa/0 ise ölçüm YOKTUR — None."""
    if base is None or son is None or base == 0:
        return None
    return (son / base - 1.0) * 100.0


def _read_csv(path: Path) -> pd.DataFrame:
    """TEK okuma boğazı: önbellek isabeti buradan ölçülür (ve testte sayılır). `usecols` ile üç
    kolon okunur — OHLC'nin tamamı bu görünümde kullanılmıyor, 260 dosyada boşuna ayrıştırılmaz."""
    return pd.read_csv(path, usecols=["date", "close", "volume"])


def _compute_core(path: Path) -> dict:
    """Bir sembolün BAR'dan türeyen alanları. Dosya okunamazsa satır DÜŞMEZ, alanları None kalır:
    "izleniyor ama barı okunamadı" bilgisinin kendisi operatör için sinyaldir; sembolü evrenden
    sessizce silmek, sorunu görünmez kılardı."""
    try:
        df = _read_csv(path)
    except Exception as e:
        from . import obs
        obs.warn("marketview_bars_unreadable", file=path.name, error=f"{type(e).__name__}: {e}",
                 detail="sembol evrende ÖLÇÜMSÜZ satır olarak kalır — listeden düşmez")
        return _bos_cekirdek(f"bar dosyası okunamadı ({type(e).__name__}) — sembol evrende "
                             f"ölçümsüz satır olarak kalır, seri UYDURULMAZ")

    closes = [_f(v) for v in df["close"].tolist()]
    vols = [_f(v) for v in df["volume"].tolist()]
    dates = [str(v)[:10] for v in df["date"].tolist()]
    # Kapanışı olmayan bar bir bar DEĞİLDİR: pencere sayımına girerse "20 barım var" yalanı olur.
    keep = [i for i, c in enumerate(closes) if c is not None]
    if not keep:
        return _bos_cekirdek("dosyada kapanışı ölçülebilen tek bar yok — seri çizilemez")
    closes = [closes[i] for i in keep]
    vols = [vols[i] for i in keep]
    dates = [dates[i] for i in keep]

    n = len(closes)
    out = _bos_cekirdek(_SERI_HESAPLANMADI)   # seri aşağıda DOLDURULUR, neden orada None'a çekilir
    out["last_date"] = dates[-1]
    out["close"] = closes[-1]
    if n >= 2:
        out["chg1_pct"] = _pct(closes[-2], closes[-1])
    if n >= _CHG20_BARS:
        out["chg20_pct"] = _pct(closes[-_CHG20_BARS], closes[-1])
    if n >= _HIGH_BARS:
        # 52 haftalık zirveye uzaklık KAPANIŞ üzerinden ölçülür (intraday high değil): bu görünümün
        # tamamı kapanış verisidir, iki farklı fiyat tanımını tek kolonda karıştırmak olurdu.
        out["dist_52w_high_pct"] = _pct(max(closes[-_HIGH_BARS:]), closes[-1])
    if n >= _ADV_BARS:
        pen_c, pen_v = closes[-_ADV_BARS:], vols[-_ADV_BARS:]
        if all(v is not None for v in pen_v):
            out["adv20_usd"] = sum(c * v for c, v in zip(pen_c, pen_v)) / _ADV_BARS
    out["spark"] = closes[-_SPARK_BARS:]
    # SERİ: eldeki kadarı, DOLGUSUZ. 40 barı olmayan sembolde eksik uçları interpole etmek
    # (ya da ilk kapanışla doldurmak) grafiğe var olmayan bir geçmiş çizerdi; `n` GERÇEK sayıdır
    # ve `ilk_tarih` de dizinin gerçek başlangıcıdır — okuyucu pencerenin kısa olduğunu görür.
    # Bu bir EOD serisidir: `son_tarih` hangi SEANSA kadar ölçüldüğünü söyler (yük başındaki
    # `as_of` ile aynı disiplin) — "canlı fiyat" değildir ve öyle adlandırılmaz.
    kap = closes[-_SERI_BARS:]
    out["seri"] = {"kapanis": kap, "ilk_tarih": dates[-len(kap)], "son_tarih": dates[-1],
                   "n": len(kap)}
    out["seri_yok_nedeni"] = None
    return out


def _bar_core(path: Path) -> dict:
    """Önbellekli `_compute_core`. Anahtar yol, geçerlilik ölçüsü mtime_ns."""
    key = str(path)
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as e:
        from . import obs
        obs.warn("marketview_bars_stat_failed", file=path.name, error=f"{type(e).__name__}: {e}",
                 detail="önbellek geçerliliği ölçülemedi — çekirdek bu turda yeniden hesaplanır")
        return _compute_core(path)
    hit = _CACHE.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    core = _compute_core(path)
    _CACHE[key] = (mtime, core)
    return core


# Silahlı bir sembol için okunacak bar sayısı. `admissible_bars` en yenisini seçtiği için derin
# geçmişe gerek YOK: 10 bar, kapanmamış son barı elemeye ve bir öncekine düşmeye fazlasıyla yeter.
# intraday_cycle 390 okur çünkü o KURULUM hesaplar; burada tek soru "en yeni kapanmış kapanış ne?".
_INTRADAY_BARS = 10


def _intraday(ticker: str, as_of: dt.datetime) -> tuple:
    """(kapanış, damga, durum) — durum: "ok" | "akis_yok" | "bayat".

    DİSİPLİN, intraday_cycle'ın AYNISI ve bilinçli olarak dardır:
      * yalnız KAPANMIŞ (admissible) dakikalık bar okunur — sıcak/anlık fiyat DEĞİL. Kapanmamış bir
        barın kapanışı diye bir şey yoktur; onu göstermek look-ahead'i panoya taşımak olurdu.
      * en yeni kapanmış bar STALE_TOL_S'ten eskiyse ölçüm YOKTUR (None). Bayat bir fiyatı "seans
        içi" diye göstermek, akış koptuğunda operatöre canlı bir sayı gösterirdi — sessiz yalan.
    """
    raw = hotstate.read_bars(ticker, _INTRADAY_BARS)
    if raw is None:                      # Redis yok/erişilemiyor — dosyaya düşülür, uydurulmaz
        return None, None, "akis_yok"
    bars = barclock.admissible_bars(raw, as_of)
    if not bars:
        return None, None, "bayat"       # akış var ama KAPANMIŞ bar yok — ölçüm yine yok
    son = bars[-1]
    if not barclock.is_fresh(son.get("t"), STALE_TOL_S, as_of):
        return None, None, "bayat"
    return _f(son.get("c")), son.get("t"), "ok"


def _next_report(dates: list, on_date: str | None):
    """`on_date`ten itibaren BİR SONRAKİ rapor tarihi; yoksa None.

    GEÇMİŞ RAPOR YAZILMAZ: bu kolonun cevapladığı soru "önümde bir bilanço riski var mı?"dır.
    Geçmiş bir tarihi aynı hücrede göstermek, geçmiş ile gelecek riski tek sayıya karıştırırdı."""
    if not dates or not on_date:
        return None
    return next((d for d in sorted(dates) if d >= on_date), None)


def build(*, seri: bool = False) -> dict:
    """İzlenen evrenin tamamı — pano 'Piyasa' sekmesinin tek kaynağı.

    `seri=True` her satıra `seri` (son `_SERI_BARS` KAPANIŞ + ilk/son seans + gerçek `n`) ve
    `seri_yok_nedeni` ekler. VARSAYILAN KAPALI ve bu bir performans süsü değil sözleşme:
    seriyi hiç çizmeyen mevcut tüketicilerin yükü büyümez, üstelik "üretilen her alanın tüketicisi
    var" (YASA 6) çivisi de satır şeklini istemeden genişletmekle bozulmaz.

    Evren = `state/bars/*.csv` (motorun fiilen bar tuttuğu semboller). `finviz_universe.json`
    keşfi bars'ta OLMAYAN bir sembol getirirse o da satır olur ama bar alanları None kalır ve
    `source="finviz"` etiketiyle işaretlenir — "keşfedildi" ile "ölçülüyor" aynı şey değildir.

    EMEKLİ SEMBOLLER satır olarak KALIR (bar geçmişi gerçek, CSV replay determinizmi için silinmez)
    ama BAYATLIK ÖLÇÜMÜNE GİRMEZ: son barı delist gününde donmuş bir sembol her gün "bayat" sayılır
    ve o kalıcı gürültü, gerçek bayatlığı (bar hattı bugün durdu) görünmez kılardı.
    """
    bars_dir = config.BARS
    files = sorted(bars_dir.glob("*.csv")) if bars_dir.exists() else []

    # ---- bar çekirdekleri (önbellekli) + evrenin `as_of`u -----------------------------------
    cores: dict[str, dict] = {}
    for p in files:
        # Dosya adı küçük harf ('.' → '-' ile yazılır, bkz. api.py bar indirme yolu); defterler
        # (portfolio/plan/earnings) BÜYÜK harf kullanır. Eşleme tek yönde normalize edilir.
        cores[p.stem.upper()] = _bar_core(p)
    tarihler = [c["last_date"] for c in cores.values() if c["last_date"]]
    as_of = max(tarihler) if tarihler else None

    # ---- defterlerden gelen bağlam ------------------------------------------------------------
    portfolio = store.read_json("portfolio.json", {}) or {}
    pozisyonlar = {str(t).upper() for t in (portfolio.get("positions") or {})}
    silahli = {str((pl or {}).get("ticker") or "").upper()
               for pl in (portfolio.get("armed") or []) if isinstance(pl, dict)}
    silahli.discard("")

    plan_n: dict[str, int] = {}
    plan_son: dict[str, str] = {}
    for satir in store.read_jsonl("trade_plans.jsonl"):
        t = str(satir.get("ticker") or "").upper()
        if not t:
            continue
        plan_n[t] = plan_n.get(t, 0) + 1
        d = str(satir.get("date") or "")
        if d and d > plan_son.get(t, ""):
            plan_son[t] = d

    # Kazanç takvimi earnings modülünün KENDİ yükleyicisinden okunur (mtime önbellekli, biçim
    # toleransı orada yazılı). CSV'yi burada ikinci kez ayrıştırmak, aynı yasanın iki kaynağı
    # demektir — bu depodaki baskın hata deseni tam olarak budur.
    takvim = earnings._load()
    takvim_gunu = as_of or dt.date.today().isoformat()

    fv = store.read_json("finviz_universe.json", {}) or {}
    fv_tickers = {str(t).upper() for t in (fv.get("tickers") or []) if str(t).strip()}
    fv_ekstra = sorted(fv_tickers - set(cores))

    # ---- seans içi ölçüm — YALNIZ silahlı semboller -------------------------------------------
    # barfeed zaten YALNIZ silahlı planların sembollerini izler; 260 sembol için sıcak katmana
    # gitmek hem israf (260 Redis çağrısı/tazeleme) hem de disiplin ihlali olurdu: izlenmeyen bir
    # sembolde "seans içi fiyat" göstermek, olmayan bir ölçümü varmış gibi sunmaktır.
    as_of_ts = barclock.now()
    intraday: dict[str, tuple] = {}
    durumlar: list[str] = []
    for t in sorted(silahli):
        kapanis, damga, durum = _intraday(t, as_of_ts)
        intraday[t] = (kapanis, damga)
        durumlar.append(durum)

    def _satir(ticker: str, source: str, core: dict) -> dict:
        """Tek tickerın pano satırını kurar: çekirdek bar alanları + gün-içi kapanış/damgası, pozisyon /
        silahlı / emekli bayrakları, plan sayımı ve sıradaki bilanço tarihi."""
        ic_kapanis, ic_damga = intraday.get(ticker, (None, None))
        satir = {
            "ticker": ticker, "source": source,
            **{k: core[k] for k in _EMPTY_CORE},
            "intraday_close": ic_kapanis, "intraday_ts": ic_damga,
            "position": ticker in pozisyonlar,
            "armed": ticker in silahli,
            "retired": ticker in _data.RETIRED_SYMBOLS,
            "plans_n": plan_n.get(ticker, 0),
            "last_plan_date": plan_son.get(ticker),
            "earnings_date": _next_report(takvim.get(ticker) or [], takvim_gunu),
        }
        if seri:
            # İKİ ALAN BİRLİKTE GİDER: `seri` None ise nedeni DOLU, doluysa nedeni None. Yokluğu
            # nedensiz bırakmak, panoya "çizemedim" ile "çizecek bir şey yok"u aynı boşlukla
            # anlattırırdı.
            satir["seri"] = core.get("seri")
            satir["seri_yok_nedeni"] = core.get("seri_yok_nedeni")
        return satir

    rows = [_satir(t, "bars", cores[t]) for t in sorted(cores)]
    rows += [_satir(t, "finviz", _bos_cekirdek(_SERI_YOK_DOSYA)) for t in fv_ekstra]

    # BAYATLIK YALNIZ YAŞAYAN SEMBOLE SORULUR. Emekli bir sembolün barı as_of'un gerisinde olmak
    # ZORUNDADIR — delist gününden sonra bar YOK. Onu saymak, sayacı hiç düşmeyen bir tabana
    # oturtur ve "8 hisse bayat" uyarısı kalıcı dekora dönüşürdü.
    stale_n = sum(1 for r in rows
                  if not r["retired"] and r["last_date"] and as_of and r["last_date"] < as_of)
    # Yalnız bars'ta GERÇEKTEN CSV'si olan emekliler sayılır: defterde adı geçip diskte karşılığı
    # olmayan bir sembol panoda hiçbir satır üretmiyor demektir, onu saymak sayıyı şişirirdi.
    retired_n = sum(1 for r in rows if r["retired"] and r["source"] == "bars")

    # Rejim ÖZETİ dosyada GERÇEKTEN duran alanlarla sınırlıdır: olmayan bir anahtarı None ile
    # doldurmak, panoda "ölçüldü ve boş çıktı" diye okunurdu (UYDURMA YASAĞI).
    ham_rejim = store.read_json("regime.json", {}) or {}
    rejim = {k: ham_rejim[k] for k in ("date", "regime", "exposure_budget_pct", "distribution_days")
             if k in ham_rejim}

    # BOŞLUĞUN SEBEBİ ÖLÇÜLÜ OLARAK YAZILIR: "seans içi kolon boş" üç AYRI şey olabilir ve üçü
    # farklı iş gerektirir — izlenecek sembol yok (normal), akış hiç yok (Redis/altyapı), akış var
    # ama bayat (bağlantı koptu). Tek bir boş kolon üçünü de aynı sessizliğe indirirdi.
    olculen = sum(1 for r in rows if r["intraday_close"] is not None)
    if not durumlar:
        neden = "silahlı plan yok"
    elif olculen:
        neden = ""
    elif all(d == "akis_yok" for d in durumlar):
        neden = "bar akışı yok — sıcak katman (Redis) okunamıyor"
    else:
        neden = f"bar akışı bayat — en yeni kapanmış bar {STALE_TOL_S} sn'den eski"

    return {
        "as_of": as_of,
        "n": len(rows),
        "stale_n": stale_n,
        "retired_n": retired_n,
        "source": {"bars": len(files), "finviz_extra": len(fv_ekstra),
                   "finviz_reason": fv.get("reason") or ""},
        # `stale_tol_s` DIŞA VERİLİR ki pano eşiği METİNDE tekrar yazmasın: "≤120 sn" cümlesini
        # arayüze elle gömmek, motorun eşiği değişince panonun sessizce yalan söylemesi olurdu.
        "intraday": {"tracked_n": len(durumlar), "measured_n": olculen,
                     "reason": neden, "stale_tol_s": STALE_TOL_S},
        "regime": rejim,
        "rows": rows,
    }


# =================================================================================================
# TEK SEMBOLÜN DERİN SERİSİ — `/api/bars/{ticker}` (aday çekmecesinin çizdiği grafik)
# =================================================================================================
# Satır-içi kıvılcım 40 kapanışla yetinir; çekmece açıldığında operatör "bu hisse son yarım yılda
# ne yaptı?" diye sorar ve o soru OHLC ister (gövde/fitil), yalnız kapanış değil.
BAR_UCU_VARSAYILAN = 120      # ≈ altı ay — çekmecenin varsayılan sorusu bu ölçekte cevaplanır
BAR_UCU_TAVAN = 500           # ≈ iki yıl. TAVAN ZORUNLU: bu depodaki CSV'ler 2004'ten beri
                              # birikiyor (≈5.600 bar) ve tavansız bir uç tek istekle defterin
                              # TAMAMINI tele koyardı. Tavan SESSİZ DE OLAMAZ (`kirpildi`):
                              # 900 isteyip 500 alan bir pano, eksik grafiği tam sanardı.

# Yol parametresi diskte bir DOSYA ADINA çevriliyor. Kapalı bir izin listesi olmadan bu uç bir
# dizin gezintisi yüzeyidir (`/api/bars/%2e%2e`, `/api/bars/..%2f..%2fetc%2fpasswd`). Sembol adları
# harf/rakamla BAŞLAR ve devamında yalnız harf/rakam/nokta/tire taşır (`BRK.B`) — desen bunu
# ZORLAR, adı temizlemeye ÇALIŞMAZ: temizleyen bir kod, temizlemeyi unuttuğu ilk karakterde sessizce
# açık kapı bırakır. İlk karakterin alfanümerik olma şartı `..` ve `-x` gibi adları daha kapıda
# eler (dosya adı kurulurken '.' → '-' zaten dönüştürülüyor, yani bu İKİNCİ hattır, tek hat değil).
_TICKER_DESENI = _re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,11}$")


def bar_serisi(ticker: str, n: int | None = None) -> dict:
    """Tek sembolün son `n` GÜNLÜK barı (EOD, kapanmış). Yük:

        {"ticker", "istenen_n", "n", "kirpildi", "as_of", "bar": [{"t","o","h","l","c","v"}…],
         "neden"}

    `n` GERÇEK sayıdır (dönen bar adedi), `istenen_n` ise sorulan sayı — ikisini tek alana
    indirmek "500 istedim 500 aldım" ile "500 istedim 12 var"ı aynı şekle sokardı.

    BİLİNMEYEN/OKUNAMAYAN SEMBOL 404 DEĞİLDİR: `bar: null` + `neden`. 404 alan bir çekmece
    "sunucu bozuk" ile "bu sembolün barı yok"u ayırt edemez; ikincisi bir ARIZA değil bir
    ÖLÇÜM YOKLUĞUDUR ve panoda öyle çizilir.

    ÖNBELLEKSİZ ve bilinçli: `_bar_core`ın gözü satır ÖZETLERİNİ tutar (260 sembol × birkaç
    alan). 500 barlık OHLCV kareleri aynı göze konsaydı süreç belleği evren büyüklüğüyle
    çarpılırdı; bu uç ise tek sembol için, çekmece açıldığında, seyrek çağrılır.
    """
    ham = str(ticker or "").strip()
    ad = ham.upper()
    istenen = int(n) if n is not None else BAR_UCU_VARSAYILAN
    kirpildi = istenen > BAR_UCU_TAVAN
    etkin = min(istenen, BAR_UCU_TAVAN)

    def _yok(neden: str) -> dict:
        return {"ticker": ad, "istenen_n": istenen, "n": 0, "kirpildi": kirpildi,
                "as_of": None, "bar": None, "neden": neden}

    if not _TICKER_DESENI.match(ham):
        return _yok("geçersiz sembol adı — harf/rakam/nokta/tire dışında karakter var")
    # Dosya adı küçük harf ve '.' → '-' ile yazılır (adapters.data._bar_path ile AYNI kural;
    # oradaki tek kaynağı import etmek marketview'e bir adapter bağımlılığı daha eklerdi).
    p = config.BARS / f"{ham.lower().replace('.', '-')}.csv"
    if not p.exists():
        return _yok(_SERI_YOK_DOSYA)
    try:
        df = pd.read_csv(p, usecols=["date", "open", "high", "low", "close", "volume"])
    except Exception as e:
        from . import obs
        obs.warn("marketview_bar_ucu_unreadable", file=p.name, error=f"{type(e).__name__}: {e}",
                 detail="derin seri ucu boş DÖNMEZ, nedenini beyan eder — pano 'ölçülemedi' çizer")
        return _yok(f"bar dosyası okunamadı ({type(e).__name__}) — biçim bozuk ya da kolon eksik")

    kuyruk = df.tail(etkin)
    bar = []
    for d, o, h, lo, c, v in zip(kuyruk["date"], kuyruk["open"], kuyruk["high"],
                                 kuyruk["low"], kuyruk["close"], kuyruk["volume"]):
        cf = _f(c)
        if cf is None:
            continue      # kapanışı olmayan bar bir bar DEĞİLDİR (`_compute_core` ile aynı kural)
        bar.append({"t": str(d)[:10], "o": _f(o), "h": _f(h), "l": _f(lo), "c": cf, "v": _f(v)})
    if not bar:
        return _yok("dosyada kapanışı ölçülebilen tek bar yok — çizilecek seri çıkmadı")
    # `as_of` DÖNEN serinin son seansıdır: bu uç EOD servis eder ve hangi seansa kadar ölçtüğünü
    # söylemek zorundadır — sembolün barı günler önce durmuşsa grafik "bugün" diye okunmamalı.
    return {"ticker": ad, "istenen_n": istenen, "n": len(bar), "kirpildi": kirpildi,
            "as_of": bar[-1]["t"], "bar": bar, "neden": None}
