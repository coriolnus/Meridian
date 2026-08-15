"""adapters/shortinterest.py — FINRA Equity Short Interest: kaçınma filtresinin veri ayağı —
anahtarsız çekim, evren kesişimi, gün-kapatma ve SI%float türetimi.

(a) Ne yapar: FINRA'nın consolidatedShortInterest veri kümesini POST
https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest ile çeker — ANAHTARSIZ,
ücretsiz, kotasız (FMP bütçesine sıfır etki). Gövde `compareFilters` (settlementDate GTE penceresi)
+ `domainFilters` (symbolCode listesi) taşır; alan adları canlı yanıttan alınmıştır (tahmin değil:
symbolCode, settlementDate, currentShortPositionQuantity, daysToCoverQuantity, ...). `sortFields`
bu uçta reddedilir — "son yayın" sunucuda sıralanarak değil, pencere çekilip YEREL
max(settlementDate) ile bulunur. Evren `parca` (varsayılan 125) sembollük dilimlere bölünür:
250 sembol = 2 istek. Rol: ölçmek ve yazmak; bugün hiçbir üretim kararına bağlı değildir.
(b) Kilit girişler: fetch(), ozet() (ağ yok), adv20() (bar önbelleğinden salt-okuma), float_cek()
(FMP profile — sembol başına 1 istek, TAVANLI, varsayılan kapalı), durum(), health(); CLI:
--fetch/--ozet/--durum/--float-cek N.
(c) Değişmezler — BAYATLIK GÖRÜNÜR: FINRA ayda iki kez, mutabakat tarihinden ~9 iş günü SONRA
yayımlar; veri en iyi ihtimalle ~9 iş günü eskidir. `yayin` bloğu gecikmeyi ve `bayat_mi` bayrağını
dosyanın İÇİNDE taşır — türetilmesi okura bırakılmaz. İKİ AYRI gün-kapatma bilerek yazılır:
gun_kapatma_meridian (kısa pozisyon / bar-önbelleği ADV20) bizim ölçümümüz, gun_kapatma_finra
sağlayıcının kendi tanımı — ikisi aynı şey değildir, ayrıştıkları yerde soru sorulabilsin. UYDURMA
YOK: ADV20/float ölçülemiyorsa alan None kalır ve kaynak/sebep alanı söyler (0 ya da tahmin
yazılmaz). Okuyucusuz-yazım yasağına BEYANLI ERTELEME: bugünkü tek tüketici CLI + testler; kaçınma
filtresi, karşı-olgusal defterde ölçülmeden kapıya bağlanmaz.
(d) Okur/yazar: state/short_interest.json (özet) ve state/short_interest_float.json (kalıcı float
önbelleği; mevcut sembol yeniden çekilmez) — TEK YAZAR bu CLI'dır, canlı worker dokunmaz; yazım
store.write_json ile atomiktir. ADV20 bar önbelleğini yalnız OKUR (data.load_bars çağrılmaz — o ağ
yapabilir)."""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

import httpx

BASE = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
SIGNAL_FILE = "short_interest.json"          # TEK YAZAR: bu CLI
FLOAT_FILE = "short_interest_float.json"     # TEK YAZAR: bu CLI

VARSAYILAN_GUN_GERI = 60      # settlementDate >= today-60g → son 2-4 yayın penceresi
VARSAYILAN_PARCA = 125        # domainFilters sembol dilimi (250 evren = 2 istek)
SATIR_TAVANI = 5000           # istek başına limit
ADV_PENCERE = 20              # ADV20
BAYATLIK_ESIGI_GUN = 25       # mutabakat tarihi bundan eskiyse `bayat_mi=True`
YAYIN_GECIKME_ISGUNU = 9      # FINRA'nın ilan ettiği tipik yayın gecikmesi (~9 iş günü)

_HEALTH: dict = {"ok": None, "calls": 0, "fails": 0, "last_status": None, "last_error": "",
                 "at": None, "rows": 0}


def health() -> dict:
    """FINRA HTTP yolunun son durumunun kopyası (ok, çağrı/hata sayaçları, son HTTP kodu ve hata,
    dönen satır sayısı, damga). Anahtarsız uç olduğu için maskelenecek sır yoktur."""
    return dict(_HEALTH)


def _simdi() -> str:
    """Şu anın UTC ISO-8601 damgası (saniye çözünürlüğünde) — sağlık kaydı ve dosya damgaları için."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _store():
    """`meridian.store` modülünü geç (tembel) içe aktarıp döndürür — modül yükleme sırasında döngüsel
    içe aktarmayı önlemek için. Tüm disk okuma/yazma bu kapıdan geçer."""
    from .. import store
    return store


def _universe() -> list[str]:
    """Kesişimde kullanılacak sembol evreni: `adapters.data.REPLAY_UNIVERSE`ün kopyası (elle bakımlı
    liste). FINRA tüm piyasayı döndürür; kapsam bu evrenle sınırlanır."""
    from . import data
    return list(data.REPLAY_UNIVERSE)


# ------------------------------------------------------------------ FINRA çekimi
def _post(govde: dict, timeout: float = 40.0) -> list[dict]:
    """TEK HTTP kapısı. YASA 4: hata YUTULMAZ — çağırana çıkar, sağlık kaydı sebebi tutar.
    Anahtar yok, dolayısıyla maskelenecek sır da yok (FMP'den farkı budur)."""
    _HEALTH["calls"] += 1
    _HEALTH["at"] = _simdi()
    _HEALTH["last_status"] = None
    try:
        r = httpx.post(BASE, json=govde, timeout=timeout,
                       headers={"Accept": "application/json", "Content-Type": "application/json"})
        _HEALTH["last_status"] = r.status_code
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        _HEALTH["fails"] += 1
        _HEALTH.update({"ok": False, "last_error": f"{type(e).__name__}: {e}"[:200]})
        raise
    _HEALTH.update({"ok": True, "last_error": ""})
    rows = rows if isinstance(rows, list) else []
    _HEALTH["rows"] += len(rows)
    return rows


def fetch(gun_geri: int = VARSAYILAN_GUN_GERI, parca: int = VARSAYILAN_PARCA,
          semboller: list[str] | None = None) -> dict:
    """Evren kesişimi için son `gun_geri` gündeki TÜM mutabakat tarihlerini çeker (ham satırlar).
    Sıralama sunucuda YAPILAMADIĞI için (bkz. docstring) pencere çekilir, son yayın yerel bulunur."""
    evren = [s.upper() for s in (semboller if semboller is not None else _universe())]
    esik = (_dt.date.today() - _dt.timedelta(days=int(gun_geri))).isoformat()
    rapor = {"cagri": 0, "satir": 0, "hata": None, "esik_tarih": esik, "dilim": 0}
    satirlar: list[dict] = []
    for i in range(0, len(evren), max(1, int(parca))):
        dilim = evren[i:i + max(1, int(parca))]
        govde = {
            "limit": SATIR_TAVANI,
            "compareFilters": [{"fieldName": "settlementDate", "fieldValue": esik,
                                "compareType": "GTE"}],
            "domainFilters": [{"fieldName": "symbolCode", "values": dilim}],
        }
        try:
            rows = _post(govde)
        except Exception as e:
            # Kısmi sonuç saklanır AMA sebep adıyla raporlanır — sessiz boş dönüş YOK.
            rapor["hata"] = f"{type(e).__name__}: {e}"[:200]
            break
        rapor["cagri"] += 1
        rapor["dilim"] += 1
        satirlar.extend(r for r in rows if isinstance(r, dict))
    rapor["satir"] = len(satirlar)
    rapor["satirlar"] = satirlar
    return rapor


# ------------------------------------------------------------------ ADV20 (bar önbelleği, ağ YOK)
def adv20(ticker: str, pencere: int = ADV_PENCERE) -> tuple[float | None, str, str | None]:
    """(adv, kaynak/sebep, son_bar_tarihi). Bar önbelleğinden SON `pencere` seansın ortalama hacmi.
    OKUMA-ONLY: hiçbir şey yazmaz, hiçbir yere gitmez (data.load_bars ÇAĞRILMAZ — o ağ yapabilir)."""
    from . import data
    try:
        cp = data._cache_path(ticker)
        if not cp.exists():
            return None, "bar_onbellegi_yok", None
        import pandas as pd
        df = pd.read_csv(cp)
        if df.empty or "volume" not in df.columns:
            return None, "bar_onbellegi_bos", None
        son_tarih = str(df["date"].iloc[-1])[:10] if "date" in df.columns else None
        vol = pd.to_numeric(df["volume"], errors="coerce").dropna()
        if vol.empty:
            return None, "hacim_yok", son_tarih
        if len(vol) < pencere:
            # KISMİ pencere sessizce tam pencere gibi sunulmaz.
            return float(vol.mean()), f"kismi_{len(vol)}_seans", son_tarih
        return float(vol.tail(pencere).mean()), f"bar_onbellek_{pencere}", son_tarih
    except Exception as e:
        return None, f"okuma_hatasi:{type(e).__name__}", None


def _isgunu_farki(d0: _dt.date, d1: _dt.date) -> int:
    """Hafta içi gün sayısı. TATİLLER HARİÇ DEĞİLDİR — alan adı bunu söyler (`_tatilsiz`); tatil
    takvimini burada varsaymak, ölçümü olduğundan kesin gösterirdi."""
    n, d = 0, d0
    while d < d1:
        d += _dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


# ------------------------------------------------------------------ float (isteğe bağlı, TAVANLI)
def float_onbellek() -> dict:
    """state/short_interest_float.json önbelleğini okur (sembol → float/sharesOutstanding).
    Dosya yoksa veya biçimi bozuksa boş iskelet döner — AĞ ÇAĞRISI YOK."""
    d = _store().read_json(FLOAT_FILE, None)
    return d if isinstance(d, dict) else {"surum": 1, "guncellendi": None, "semboller": {}}


def float_cek(semboller: list[str], tavan: int = 25) -> dict:
    """FMP `profile` ucundan float/sharesOutstanding — SEMBOL BAŞINA 1 İSTEK, bu yüzden TAVANLI.
    Zaten önbellekte olan sembol TEKRAR ÇEKİLMEZ. Kota bloğu varsa hiç istek atılmaz."""
    from . import fmp
    rapor = {"cagri": 0, "yeni": 0, "atlanan": 0, "hata": None}
    if not fmp.available():
        rapor["hata"] = "FMP_API_KEY yok — float çekimi devre dışı"
        return rapor
    if fmp.quota_blocked():
        rapor["hata"] = "FMP tüm anahtarlar kota-bloklu — istek atılmadı"
        return rapor
    ob = float_onbellek()
    sem = dict(ob.get("semboller") or {})
    for s in [x.upper() for x in semboller]:
        if len(sem) and s in sem:
            rapor["atlanan"] += 1
            continue
        if rapor["cagri"] >= int(tavan):
            break
        rapor["cagri"] += 1
        p = fmp.profile(s)     # fmp.profile hatayı kendi içinde yutup None döner
        if not isinstance(p, dict):
            continue
        fl = p.get("floatShares") or p.get("float")
        so = p.get("sharesOutstanding") or p.get("outstandingShares")
        try:
            fl = float(fl) if fl not in (None, "") else None
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz float alanı; None kalması TASARIM — hemen aşağıda ikisi de None ise önbelleğe SAHTE kayıt yazılmaz ve `si_yuzde_float` None kalarak bilinmezliği görünür kılar
            fl = None
        try:
            so = float(so) if so not in (None, "") else None
        except (TypeError, ValueError):  # sessiz-yutma: yukarıdaki `fl` ile aynı gerekçe — sharesOutstanding biçimsizse uydurulmuş bir paydaya değil, None'a düşülür
            so = None
        if fl is None and so is None:
            continue           # UYDURMA YOK: alan gelmediyse önbelleğe sahte kayıt yazılmaz
        sem[s] = {"float": fl, "sharesOutstanding": so, "cekildi": _simdi(),
                  "kaynak": "fmp_profile"}
        rapor["yeni"] += 1
    st = _store()
    with st.file_lock(FLOAT_FILE):
        st.write_json(FLOAT_FILE, {"surum": 1, "guncellendi": _simdi(), "semboller": sem})
    return rapor


# ------------------------------------------------------------------ özet
def _sayi(v):
    """FINRA'nın metin sayısal alanını float'a çevirir; boş/biçimsiz/NaN/sonsuz ise None.
    UYDURMA YASAĞI: ölçülemeyen alan 0 değil None olur ve bilinmezlik türetilen alanlara taşınır."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):  # sessiz-yutma: FINRA'nın biçimsiz TEK sayısal alanı; None 'ölçülemedi'nin dürüst temsilidir ve türetilen gün-kapatma/SI%%float da None'a düşerek bilinmezliği TAŞIR (0 yazmak ölçülmemiş bir değeri ölçülmüş gösterirdi)
        return None
    return f if f == f and abs(f) != float("inf") else None


def ozet(satirlar: list[dict], cagri: int = 0, hata: str | None = None,
         bugun: _dt.date | None = None, yaz: bool = True) -> dict:
    """Ham FINRA satırlarından `short_interest.json` belgesini kurar. AĞ ÇAĞRISI YOK.
    SON YAYIN = satırlardaki max(settlementDate); bir ÖNCEKİ yayın da taşınır ki değişim
    sağlayıcının `changePercent`ine körü körüne güvenmeden doğrulanabilsin."""
    bugun = bugun or _dt.date.today()
    tarihler = sorted({str(r.get("settlementDate") or "")[:10] for r in satirlar
                       if r.get("settlementDate")})
    son = tarihler[-1] if tarihler else None
    onceki = tarihler[-2] if len(tarihler) > 1 else None

    fl_ob = (float_onbellek().get("semboller") or {})
    evren = _universe()
    semboller: dict[str, dict] = {}
    for r in satirlar:
        if str(r.get("settlementDate") or "")[:10] != son:
            continue
        sym = str(r.get("symbolCode") or "").strip().upper()
        if not sym:
            continue
        kisa = _sayi(r.get("currentShortPositionQuantity"))
        adv, adv_kaynak, adv_son_bar = adv20(sym)
        fl_kayit = fl_ob.get(sym) or {}
        fl = _sayi(fl_kayit.get("float")) or _sayi(fl_kayit.get("sharesOutstanding"))
        semboller[sym] = {
            "issue_name": r.get("issueName"),
            "market_class": r.get("marketClassCode"),
            "kisa_pozisyon": kisa,
            "onceki_kisa_pozisyon": _sayi(r.get("previousShortPositionQuantity")),
            "degisim_pct_finra": _sayi(r.get("changePercent")),
            "adv20_bar_onbellek": round(adv, 1) if adv is not None else None,
            "adv20_kaynak": adv_kaynak,
            "adv20_son_bar": adv_son_bar,
            # BİZİM ölçümümüz (bar önbelleği ADV20) — FINRA'nınkiyle AYNI ŞEY DEĞİL, bkz. docstring
            "gun_kapatma_meridian": round(kisa / adv, 3) if (kisa and adv) else None,
            "gun_kapatma_finra": _sayi(r.get("daysToCoverQuantity")),
            "adv_finra": _sayi(r.get("averageDailyVolumeQuantity")),
            "float": fl,
            "float_kaynak": (fl_kayit.get("kaynak") if fl else None),
            "si_yuzde_float": round(100.0 * kisa / fl, 3) if (kisa and fl) else None,
            "revision_flag": r.get("revisionFlag"),
            "stock_split_flag": r.get("stockSplitFlag"),
        }

    gecikme_gun = (bugun - _dt.date.fromisoformat(son)).days if son else None
    doc = {
        "surum": 1,
        "uretildi": _simdi(),
        "kaynak": {"saglayici": "FINRA", "dataset": "otcMarket/consolidatedShortInterest",
                   "uc": BASE, "anahtar_gerekli_mi": False, "cagri_n": int(cagri)},
        "yayin": {
            # BAYATLIK DAMGASI — dosyanın İÇİNDE, türetilmesi okura bırakılmaz.
            "settlement_date": son,
            "onceki_settlement_date": onceki,
            "gecikme_gun": gecikme_gun,
            "gecikme_isgunu_tatilsiz": (_isgunu_farki(_dt.date.fromisoformat(son), bugun)
                                        if son else None),
            "beklenen_yayin_gecikmesi_isgunu": YAYIN_GECIKME_ISGUNU,
            "bayat_mi": (gecikme_gun is not None and gecikme_gun > BAYATLIK_ESIGI_GUN),
            "bayatlik_esigi_gun": BAYATLIK_ESIGI_GUN,
            "not": "FINRA kısa pozisyonu ayda İKİ KEZ, mutabakat tarihinden ~9 iş günü SONRA "
                   "yayımlar. Bu veri hiçbir zaman 'bugün' değildir.",
            "pencerede_gorulen_tarihler": tarihler,
        },
        "kapsam": {
            "evren_n": len(evren),
            "eslesen_n": len(semboller),
            "eksik_n": len([s for s in evren if s not in semboller]),
            "eksik_ornek": [s for s in evren if s not in semboller][:20],
            "adv20_olcelemeyen_n": sum(1 for v in semboller.values()
                                       if v["adv20_bar_onbellek"] is None),
            "float_bilinen_n": sum(1 for v in semboller.values() if v["float"] is not None),
        },
        "hata": hata,
        "semboller": dict(sorted(semboller.items())),
    }
    if yaz:
        st = _store()
        with st.file_lock(SIGNAL_FILE):
            st.write_json(SIGNAL_FILE, doc)
    return doc


def durum() -> dict:
    """Ağa gitmeden durum özeti: son yazılan short_interest.json'ın üretim/yayın/kapsam alanları,
    float önbelleğindeki sembol sayısı ve health(). Dosya yoksa alanlar None kalır."""
    d = _store().read_json(SIGNAL_FILE, None) or {}
    return {"dosya": {"uretildi": d.get("uretildi"), "yayin": d.get("yayin"),
                      "kapsam": d.get("kapsam")},
            "float_onbellek_n": len((float_onbellek().get("semboller") or {})),
            "health": health()}


# ------------------------------------------------------------------ CLI (YASA 6 tüketicisi)
def main(argv=None) -> int:
    """CLI girişi (YASA 6 tüketicisi): --fetch (FINRA'dan çek + özeti yaz), --ozet, --durum,
    --float-cek. AĞ ÇAĞRISI YALNIZ BURADAN yapılır; sonuç JSON basılır.
    Çıkış kodu: herhangi bir bölümde "hata" alanı doluysa 1, argümansız çağrıda 2, aksi hâlde 0."""
    ap = argparse.ArgumentParser(
        prog="python -m meridian.adapters.shortinterest",
        description="FINRA Equity Short Interest (ücretsiz/anahtarsız) — son yayını çeker, evren "
                    "kesişimini alır, gün-kapatma ve SI%%float türetir. AĞ ÇAĞRISI YALNIZ BURADAN.")
    ap.add_argument("--fetch", action="store_true", help="FINRA'dan çek ve özeti yaz")
    ap.add_argument("--ozet", action="store_true",
                    help="son yazılan dosyayı göster (ağ YOK) — --fetch olmadan yeniden üretmez")
    ap.add_argument("--durum", action="store_true", help="dosya/bayatlık durumu (ağ YOK)")
    ap.add_argument("--float-cek", type=int, default=0, metavar="N",
                    help="FMP profile ile N sembolün float'ını doldur (SEMBOL BAŞINA 1 FMP İSTEĞİ; "
                         "varsayılan 0 = kapalı)")
    ap.add_argument("--gun-geri", type=int, default=VARSAYILAN_GUN_GERI,
                    help=f"settlementDate penceresi (varsayılan {VARSAYILAN_GUN_GERI} gün)")
    ap.add_argument("--parca", type=int, default=VARSAYILAN_PARCA,
                    help="domainFilters sembol dilimi (istek sayısını belirler)")
    a = ap.parse_args(argv)

    if not any((a.fetch, a.ozet, a.durum, a.float_cek)):
        ap.print_help()
        return 2
    cikti: dict = {}
    if a.float_cek:
        cikti["float_cek"] = float_cek(_universe(), tavan=a.float_cek)
    if a.fetch:
        f = fetch(gun_geri=a.gun_geri, parca=a.parca)
        satirlar = f.pop("satirlar", [])
        d = ozet(satirlar, cagri=f["cagri"], hata=f.get("hata"))
        cikti["fetch"] = f
        cikti["ozet"] = {"yayin": d["yayin"], "kapsam": d["kapsam"]}
    if a.ozet and not a.fetch:
        d = _store().read_json(SIGNAL_FILE, None)
        cikti["ozet"] = ({"yayin": d.get("yayin"), "kapsam": d.get("kapsam")} if d
                         else {"hata": f"{SIGNAL_FILE} yok — önce --fetch"})
    if a.durum:
        cikti["durum"] = durum()
    print(json.dumps(cikti, ensure_ascii=False, indent=2, default=str))
    hatali = any(isinstance(v, dict) and v.get("hata") for v in cikti.values())
    return 1 if hatali else 0


if __name__ == "__main__":
    sys.exit(main())
