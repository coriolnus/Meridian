"""adapters/edgar_shares.py — EDGAR as-of dolaşımdaki hisse sayımı: salt-okunur PIT veri köprüsü.

(a) Ne yapar: depo içindeki statik `research/edgar_facts/shares_outstanding.csv.gz` dosyasını
(SEC XBRL companyfacts dökümü; aylık olarak research/edgar_facts/betikler/ ile tazelenir) okur ve
tek soruyu cevaplar: "t gününde bu sembolün dolaşımdaki hisse sayısı — O GÜN BİLİNEBİLEN hâliyle —
kaçtı?" Varlık sebebi turnover ölçümüdür (turnover21 = medyan21(hacim) / as_of_shares(t) kesitsel
monoton bilgi taşıyor); ölçülmüş yolu canlıya bağlamanın önkoşulu PAYDANIN aynı kurallarla
okunmasıdır — altı kural ölçüm altyapısından (ortak.build_hisse) BİREBİR port edilmiştir, birinin
"sadeleştirilmesi" canlı paydayı ölçülmüş paydadan sessizce ayırır.
(b) Kilit girişler: as_of_shares(), as_of_shares_detay(), as_of_shares_series() (vektörel tek
uygulama), okuma_raporu(), _sifirla() (yalnız testler); SHARES_FILE, BAYAT_GUN, NEDEN_* kodları.
(c) Değişmezler — AS-OF/PIT DİSİPLİNİ: (1) t gününde bilinen küme `filed <= t`'dir; `end <= t` PIT
DEĞİLDİR, geleceği sızdırır (aynı `end`, iki `filed`, iki değer). (2) Yalnız iki ANLIK etiket
(dei:EntityCommonStockSharesOutstanding, us-gaap:CommonStockSharesOutstanding); `...Issued` ve
ağırlıklı-ortalama serileri SEVİYE olarak kullanılmaz. (3) Birincil etiket seçimi + uzun boşlukta
öteki etiketten yedek. (4) Bildirilen sayı o günkü hisse birimindedir; güncel baza çevrim, bölünme
takvimi EDGAR'ın KENDİ geriye-dönük yeniden-beyanından (bar serisi zaten düzeltilmiş, oradan
okunamaz). (5) Bayatlık bekçisi: son dosyalama BAYAT_GUN'den eskiyse değer YOK. (6) Ölçek-hatası
gidiş-dönüş penceresindeki kayıtlar geçersiz. Fiziksel devir bekçisi (devir>1 imkânsız) BURADA
DEĞİL `indicators.turnover21`dedir — orana bakar, sayıma değil. FAIL-OPEN sözleşme: ölçülemeyen
her hücre None + NEDEN kodudur; None "sıfır hisse" değil "ölçülemedi"dir, çağıran 0 gibi
kullanamaz. Sembol düzeyi olgular SAYILIR (skor yolunda obs.warn atılmaz — sembol başına olay, saf
hesabı canlı deftere yazan G/Ç yoluna çevirirdi; ölçülmüş ders), kaynak düzeyi olgular süreç
başına bir kez UYARIR.
(d) Okur/yazar: YAZMA YOLU YOKTUR — ne bu dosyaya ne state'e tek bayt (modül canlı tarama yolunda
çağrılır). Tablolar bir kez, sembol serileri TEMBEL kurulur ve süreç içinde önbelleklenir; sayaçlar
okuma_raporu() ile component_ic.json'ın `turnover_kaynak` alanına akar (okuyucusuz yazım yok)."""
from __future__ import annotations

import time
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from .. import config, obs

SHARES_FILE = config.ROOT / "research" / "edgar_facts" / "shares_outstanding.csv.gz"

# --- ortak.py sabitleri, BİREBİR (değer değişirse canlı payda ölçülmüş paydadan ayrılır) ---------
ANLIK_ETIKET = ("EntityCommonStockSharesOutstanding",     # dei — kapak, medyan 7g gecikme
                "CommonStockSharesOutstanding")           # us-gaap — bilanço, ~36g
DEI, USGAAP = ANLIK_ETIKET
BIRINCIL_MIN_FILED = 8      # birincil etiket seçimi: dei'de en az bu kadar farklı filed
BAYAT_GUN = 200             # son filed t'den bu kadar eskiyse as-of None (bayat seri)
SICRAMA_ESIK = 5.0          # split ile açıklanamayan bu büyüklükteki sıçrama şüpheli
JUMP_TARAMA = 1.4           # split adayı taraması için sıçrama alt sınırı
SNAP_TOL = 0.04             # split oranı "temiz orana" bu bağıl toleransla oturmalı
_FWD_ORAN = [1.25, 4 / 3, 1.5, 1.6, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]
SPLIT_ADAY_ORAN = sorted(_FWD_ORAN + [1.0 / x for x in _FWD_ORAN])

# NEDEN KODLARI — ölçümdeki adlarla aynı (sonuc_016.json panel_muhasebesi.neden_sayimi ile
# karşılaştırılabilir kalsın diye; farklı ad koymak iki tabloyu kıyaslanamaz yapardı).
NEDEN_DOSYA_YOK = "edgar_dosyasi_yok"
NEDEN_SERI_YOK = "anlik_hisse_serisi_yok"
NEDEN_DOSYALAMA_YOK = "dosyalama_yok"
NEDEN_BAYAT = "bayat_seri"
NEDEN_OLCEK = "olcek_hatasi_gidis_donus"
NEDEN_TARIH_YOK = "tarih_yok"

_TABLO: dict | None = None        # ortak tablolar (bir kez kurulur): birincil/kayıt/split kanıtı
_SERILER: dict = {}               # sembol → _Seri | None (TEMBEL: ilk sorulduğunda kurulur)
_YUKLEME: dict = {}               # yükleme muhasebesi (okuma_raporu'nun içinde görünür)
_SAYAC: dict = {"cagri": 0, "olculdu": 0, "olculemedi": 0, "neden": {}}
_KAPSAM_DISI: set = set()        # EDGAR anlık serisi olmayan semboller (rapora ADIYLA girer)

# OKUNAN SÜTUNLAR. Dosya 16 sütunlu ve 44 MB (sıkıştırılmamış); ölçümün kullandığı kurallar bu
# sekizine dokunur (`accn`/`form`/`fy`/`fp`/`frame`/`cik`/`donem_gun` HİÇBİR kuralda geçmez).
# Okunmayan sütun ayrıştırılmaz — canlı tarama yolunda duran bir maliyet gereksiz yere ödenmez.
_OKUNAN_SUTUN = ["symbol", "tag", "unit", "start", "end", "filed", "val", "donem_turu"]


class _Seri:
    """Bir sembolün as-of hisse serisi. `filed` ARTAN sıralı; `asof` searchsorted ile okur."""

    __slots__ = ("birincil_tag", "filed", "val", "gecersiz", "B", "B_son", "kirik_filed")

    def __init__(self, birincil_tag, filed, val, gecersiz, B, B_son, kirik_filed):
        """Bir sembolün hazır as-of serisini alanlara bağlar (birincil etiket, artan `filed` dizisi,
        dosyalama günündeki bazda `val`, ölçek-hatası maskesi, baz çarpanları ve kırık dosyalamalar).
        Hesap yapmaz; seriyi `_seri()` kurar."""
        self.birincil_tag = birincil_tag
        self.filed = filed          # np.array[str] — artan
        self.val = val              # np.array[float] — dosyalama günündeki bazda
        self.gecersiz = gecersiz    # np.array[bool] — ölçek-hatası penceresi
        self.B = B                  # np.array[float] — o dosyalamanın baz çarpanı
        self.B_son = B_son          # float — tüm kabul edilmiş bölünmelerin çarpımı
        self.kirik_filed = kirik_filed


def _snap(r: float) -> float | None:
    """Ham oranı en yakın "temiz" bölünme oranına (SPLIT_ADAY_ORAN) oturtur; bağıl sapma SNAP_TOL'ü
    aşarsa None — yani oran bir bölünme olarak SAYILMAZ (birleşme/ihraç kaynaklı sıçramayı eler)."""
    best, bd = None, 9e99
    for c in SPLIT_ADAY_ORAN:
        d = abs(r - c) / c
        if d < bd:
            bd, best = d, c
    return best if bd <= SNAP_TOL else None


def _split_olaylari(filed0: np.ndarray, val0: np.ndarray, ev: tuple | None) -> tuple[list, list, list]:
    """Bir sembolün BÖLÜNME TAKVİMİ — EDGAR'IN KENDİ GERİYE-DÖNÜK YENİDEN-BEYANINDAN.

    (ortak.build_split_takvimi'nin sembol-içi çekirdeği, BİREBİR.) Bar serisi (FMP/Cboe) zaten
    split-düzeltilmiştir; bölünme günü BARDAN OKUNAMAZ. Yol:
      (a) TESPİT — birincil as-of seride ardışık iki dosyalama arasındaki oran >=1.4 (veya <=1/1.4)
          ise aday; oran "temiz" bir bölünme oranına %4 toleransla oturmalı.
      (b) DOĞRULAMA — aynı sembolde herhangi bir (tag,start,end) üçlüsünün DAHA ÖNCE dosyalanmış
          değeri, sıçrama dosyalamasında ~aynı oranla yeniden beyan edilmiş olmalı. Bölünme geçmişi
          geriye dönük düzeltir; BİRLEŞME/İHRAÇ DÜZELTMEZ — ayrım budur.
      (c) Yürürlük tarihi = sıçramanın görüldüğü DOSYALAMA günü (ex-date'e ihtiyaç yok; pay ve payda
          aynı bazda olduğu için dönüşüm o pencerede DE doğrudur).
    Ağırlıklı-ortalama etiketleri burada YALNIZ (b) kanıtı olarak okunur, SEVİYE olarak asla.
    → (olaylar, kirik_filed, gecersiz_aralik[(lo_filed, hi_filed)])"""
    olay, kirik = [], []
    ef_old, ef_new, er = ev if ev is not None else (None, None, None)
    for i in range(1, len(val0)):
        r = val0[i] / val0[i - 1]
        if 1 / JUMP_TARAMA < r < JUMP_TARAMA or not np.isfinite(r):
            continue
        sn = _snap(r)
        n_kanit = 0
        if ef_old is not None and sn is not None:
            k = (ef_old < filed0[i]) & (ef_new >= filed0[i])
            if k.any():
                oran = er[k] / r
                n_kanit = int(((oran >= 0.9) & (oran <= 1.1)).sum())
        if sn is not None and n_kanit > 0:
            olay.append((str(filed0[i]), float(sn)))
        elif r >= SICRAMA_ESIK or r <= 1 / SICRAMA_ESIK:
            kirik.append((i, str(filed0[i]), float(r)))
    # ÖLÇEK-HATASI GİDİŞ-DÖNÜŞ: >=5× sıçrama 6 dosyalama içinde ~1/oran ile geri dönüyorsa aradaki
    # kayıtlar GEÇERSİZ (kabuk-sayısı/ölçek hatası penceresi — CSX 3 hisse, ETN 100, SPG 8.000...).
    gecersiz = []
    for a_ in range(len(kirik)):
        for b_ in range(a_ + 1, len(kirik)):
            if kirik[b_][0] - kirik[a_][0] > 6:
                break
            if abs(kirik[a_][2] * kirik[b_][2] - 1.0) < 0.1:
                gecersiz.append((kirik[a_][1], kirik[b_][1]))
                break
    return olay, [k[1] for k in kirik], gecersiz


def _tablolar() -> dict:
    """DOSYAYI BİR KEZ OKUR ve üç ortak tabloyu kurar (sembol serileri TEMBEL kurulur, `_seri`).

    NEDEN VEKTÖREL VE NEDEN TEMBEL. Ölçüm sandbox'ı 161.856 satırı pandas groupby/boolean-maske
    ile geziyordu; orada maliyet önemsizdi (tek koşum, disk önbelleği). BURASI CANLI TARAMA
    YOLUDUR: aynı desen sembol başına tam-çerçeve maskesi demek olurdu (252 sembol × 161k satır).
    Bu yüzden (a) sıralama/gruplama tamsayı kodlar üzerinde `lexsort` ile yapılır, (b) sembolün
    kendi `_Seri`si ancak O SEMBOL SORULDUĞUNDA kurulur. Üretilen SAYILAR aynıdır — değişen yalnız
    aynı kuralların hangi veri yapısıyla işletildiğidir (çivi: test_turnover_kablolama_v149)."""
    global _TABLO
    if _TABLO is not None:
        return _TABLO
    t0 = time.time()
    if not SHARES_FILE.exists():
        _TABLO = {"kayit": {}, "birincil": {}, "ev": {}}
        _YUKLEME.update({"dosya": str(SHARES_FILE), "durum": NEDEN_DOSYA_YOK, "sembol": 0})
        obs.warn("edgar_shares_file_missing", path=str(SHARES_FILE),
                 detail="as-of hisse sayımı OKUNAMADI — turnover bileşeni ölçülemez (fail-open)")
        return _TABLO
    try:
        S = pd.read_csv(SHARES_FILE, usecols=_OKUNAN_SUTUN)
        m = (S["unit"].to_numpy() == "shares") & (S["val"].to_numpy(dtype=float) > 0)
        acc = {"ham_satir": int(len(S)), "birim_veya_val_dusen": int(len(S) - int(m.sum()))}
        sym_c, sym_u = pd.factorize(S["symbol"][m], sort=True)
        tag_c, tag_u = pd.factorize(S["tag"][m], sort=True)
        st_c = pd.factorize(S["start"][m].fillna(""), sort=True)[0]
        en_c = pd.factorize(S["end"][m].fillna(""), sort=True)[0]
        filed = S["filed"][m].to_numpy(dtype=object).astype("U10")
        fl_c = pd.factorize(pd.Series(filed), sort=True)[0]     # sıralı kod: lexsort tamsayıda kalsın
        val = S["val"][m].to_numpy(dtype=float)
        anlik = (S["donem_turu"][m].to_numpy() == "anlik")

        # (1) SPLIT KANITI — TÜM etiketler ve TÜM dönem türleri üzerinden (ağırlıklı-ortalama
        #     serileri yalnız BURADA, kanıt olarak okunur; seviye olarak asla).
        o = np.lexsort((fl_c, en_c, st_c, tag_c, sym_c))
        sy, tg, s2, e2, f2, v2 = sym_c[o], tag_c[o], st_c[o], en_c[o], filed[o], val[o]
        ayni = np.zeros(len(o), bool)
        ayni[1:] = ((sy[1:] == sy[:-1]) & (tg[1:] == tg[:-1])
                    & (s2[1:] == s2[:-1]) & (e2[1:] == e2[:-1]))
        r = np.full(len(o), np.nan)
        r[1:] = v2[1:] / v2[:-1]
        sec = ayni & np.isfinite(r) & ((r >= JUMP_TARAMA) | (r <= 1 / JUMP_TARAMA))
        f_onceki = np.empty_like(f2)
        f_onceki[0] = ""
        f_onceki[1:] = f2[:-1]
        ev_sym, ev_old, ev_new, ev_r = sy[sec], f_onceki[sec], f2[sec], r[sec]
        ev: dict = {}
        for j in range(len(ev_sym)):
            ev.setdefault(int(ev_sym[j]), ([], [], []))
            b = ev[int(ev_sym[j])]
            b[0].append(ev_old[j]); b[1].append(ev_new[j]); b[2].append(ev_r[j])
        ev = {sym_u[k]: (np.array(a_, dtype="U10"), np.array(b_, dtype="U10"),
                         np.array(c_, dtype=float)) for k, (a_, b_, c_) in ev.items()}
        acc["split_kanit_satir"] = int(sec.sum())

        # (2) ANLIK İKİ ETİKET — `filed` başına TEK kayıt (aynı gün birden çok `end` varsa EN SONU).
        tag_ad = {t: i for i, t in enumerate(tag_u)}
        istenen = [tag_ad[t] for t in ANLIK_ETIKET if t in tag_ad]
        m2 = anlik & np.isin(tag_c, istenen)
        acc["anlik_iki_etiket_satir"] = int(m2.sum())
        o2 = np.lexsort((en_c[m2], fl_c[m2], tag_c[m2], sym_c[m2]))
        sy2, tg2, fc2 = sym_c[m2][o2], tag_c[m2][o2], fl_c[m2][o2]
        f3, v3 = filed[m2][o2], val[m2][o2]
        son = np.ones(len(o2), bool)
        son[:-1] = (sy2[1:] != sy2[:-1]) | (tg2[1:] != tg2[:-1]) | (fc2[1:] != fc2[:-1])
        sy2, tg2, f3, v3 = sy2[son], tg2[son], f3[son], v3[son]
        kayit: dict = {}
        if len(sy2):
            sinir = np.flatnonzero((sy2[1:] != sy2[:-1]) | (tg2[1:] != tg2[:-1])) + 1
            for lo, hi in zip(np.r_[0, sinir], np.r_[sinir, len(sy2)]):
                kayit[(sym_u[sy2[lo]], tag_u[tg2[lo]])] = (f3[lo:hi], v3[lo:hi])

        # (3) BİRİNCİL ETİKET: dei'de >=8 farklı filed varsa dei; yoksa us-gaap; o da yoksa dei.
        birincil = {}
        for sym in sym_u:
            n_dei = len(kayit.get((sym, DEI), ((), ()))[0])
            n_us = len(kayit.get((sym, USGAAP), ((), ()))[0])
            if n_dei >= BIRINCIL_MIN_FILED:
                birincil[sym] = DEI
            elif n_us > 0:
                birincil[sym] = USGAAP
            elif n_dei > 0:
                birincil[sym] = DEI
        acc.update({"birincil_dei": sum(1 for v in birincil.values() if v == DEI),
                    "birincil_usgaap": sum(1 for v in birincil.values() if v == USGAAP),
                    "sembol": len(birincil), "dosya": str(SHARES_FILE), "durum": "yuklendi",
                    "yukleme_sn": round(time.time() - t0, 3)})
        _YUKLEME.update(acc)
        _TABLO = {"kayit": kayit, "birincil": birincil, "ev": ev}
    except Exception as e:                    # noqa: BLE001 — hangi hata olursa olsun ADIYLA görünür
        _TABLO = {"kayit": {}, "birincil": {}, "ev": {}}
        _YUKLEME.update({"dosya": str(SHARES_FILE), "durum": "okunamadi",
                         "hata": f"{type(e).__name__}: {e}"})
        obs.warn("edgar_shares_unreadable", path=str(SHARES_FILE),
                 error=f"{type(e).__name__}: {e}")
    return _TABLO


def _seri(sym: str) -> "_Seri | None":
    """Sembolün as-of serisi (TEMBEL kurulur, süreç ömrü boyunca kalır). Serisi yoksa None.

    `ortak.build_hisse`in sembol-içi adımları, BİREBİR: yedek-etiket boşluk doldurma → bölünme
    takvimi → güncel-baz çarpanları → ölçek-hatası penceresi."""
    if sym in _SERILER:
        return _SERILER[sym]
    tab = _tablolar()
    tg = tab["birincil"].get(sym)
    if tg is None:
        _SERILER[sym] = None
        return None
    filed0, val0 = tab["kayit"][(sym, tg)]
    filed, val = filed0, val0
    # YEDEK ETİKET: birincilde >200g boşluk varsa o boşluğa ÖTEKİ etiketten kayıt eklenir.
    oth = USGAAP if tg == DEI else DEI
    o_f, o_v = tab["kayit"].get((sym, oth), (np.array([], dtype="U10"), np.array([], dtype=float)))
    if len(o_f):
        ekle_f, ekle_v = [], []
        for k in range(len(o_f)):
            j = int(np.searchsorted(filed, o_f[k], side="right")) - 1
            onceki = filed[j] if j >= 0 else None
            sonraki = filed[j + 1] if j + 1 < len(filed) else None
            bosluk = ((pd.Timestamp(str(o_f[k])) - pd.Timestamp(str(onceki))).days
                      if onceki is not None else 10 ** 6)
            if bosluk > BAYAT_GUN and (sonraki is None or o_f[k] < sonraki):
                ekle_f.append(o_f[k]); ekle_v.append(o_v[k])
        if ekle_f:
            _YUKLEME["yedek_etiket_eklenen_kayit"] = (
                _YUKLEME.get("yedek_etiket_eklenen_kayit", 0) + len(ekle_f))
            filed = np.concatenate([filed, np.array(ekle_f, dtype="U10")])
            val = np.concatenate([val, np.array(ekle_v, dtype=float)])
            sr = np.argsort(filed, kind="stable")
            filed, val = filed[sr], val[sr]
    olay, kirik, gecersiz_aralik = _split_olaylari(filed0, val0, tab["ev"].get(sym))
    if olay:
        of_ = np.array([x[0] for x in olay], dtype="U10")
        cum = np.cumprod(np.array([x[1] for x in olay], dtype=float))
        B = np.concatenate([[1.0], cum])[np.searchsorted(of_, filed, side="right")]
        B_son = float(cum[-1])
    else:
        B, B_son = np.ones(len(filed)), 1.0
    gec = np.zeros(len(filed), bool)
    for lo, hi in gecersiz_aralik:
        gec |= (filed >= lo) & (filed < hi)
    s = _Seri(tg, filed, val, gec, B, B_son, kirik)
    _SERILER[sym] = s
    return s


def _say(neden: str) -> None:
    """Tek bir hücre sonucunu `_SAYAC`a işler: neden kodu varsa "ölçülemedi" + neden kırılımı,
    boşsa "ölçüldü". UYDURMA YASAĞI'nın muhasebesi — okuma_raporu bu sayaçları yayımlar."""
    if neden:
        _SAYAC["olculemedi"] += 1
        _SAYAC["neden"][neden] = _SAYAC["neden"].get(neden, 0) + 1
    else:
        _SAYAC["olculdu"] += 1


def as_of_shares_series(ticker: str, dates: Sequence[str] | Iterable) -> tuple[np.ndarray, np.ndarray]:
    """VEKTÖREL as-of: (değerler, nedenler). Ölçülemeyen hücre NaN + neden kodu (UYDURMA YASAĞI).

    TEK UYGULAMA, İKİ TÜKETİCİ: `component_ic._component_frame` bütün bar takvimini bir çağrıda
    okur, `as_of_shares` ise bunun tek-noktalı sarmalayıcısıdır. İkinci bir as-of yazmak, canlı
    skorun ve gecelik ölçüm tablosunun aynı adı taşıyan iki farklı sayı üretmesi demekti."""
    d = np.asarray([str(x)[:10] for x in dates], dtype=object)
    n = len(d)
    out = np.full(n, np.nan)
    neden = np.full(n, "", dtype=object)
    _SAYAC["cagri"] += n
    tab = _tablolar()
    if not tab["birincil"]:              # dosya yok / okunamadı → HEPSİ ölçülemedi, sebebi adıyla
        k = str(_YUKLEME.get("durum") or NEDEN_DOSYA_YOK)
        neden[:] = k
        _SAYAC["olculemedi"] += n
        _SAYAC["neden"][k] = _SAYAC["neden"].get(k, 0) + n
        return out, neden
    sr = _seri(str(ticker).upper())
    if sr is None:
        # KAPSAM DIŞI SEMBOL: SAYILIR VE ADI KAYDEDİLİR, `obs.warn` ATILMAZ — ve bu bir sessiz-yutma
        # DEĞİLDİR (gerekçe): (a) dönen değer None + neden koduyla çağırana zaten gider; (b) sembolün
        # ADI `okuma_raporu().kapsam_disi_sembol` listesinde, sayısı `neden` kovasında durur ve ikisi
        # de gecelik `component_ic` olayına + `component_ic.json` → `turnover_kaynak` alanına düşer.
        # NEDEN OLAY DEĞİL: bu satır SKOR yolunda, sembol döngüsünün içinde çalışır. `obs.warn`
        # DEFTERE EKLEME yapar — yani saf skor hesabı, evrende EDGAR kapsamı dışındaki her sembol
        # için canlı `events.jsonl`a yazan bir G/Ç yoluna dönerdi. Ölçüldü: bu tur eklendiğinde
        # sentetik sembollü mevcut testler (S0..S19/X/TST) canlı deftere yazmaya başladı ve sızıntı
        # bekçisi haklı olarak kırmızıya döndü. Kaynağın kendisi (dosya yok / okunamadı) HÂLÂ
        # uyarır: o SÜREÇ BAŞINA BİR KEZdir ve gerçekten alarmdır.
        neden[:] = NEDEN_SERI_YOK
        _SAYAC["olculemedi"] += n
        _SAYAC["neden"][NEDEN_SERI_YOK] = _SAYAC["neden"].get(NEDEN_SERI_YOK, 0) + n
        _KAPSAM_DISI.add(str(ticker).upper())
        return out, neden
    if n == 0:
        return out, neden
    i = np.searchsorted(sr.filed, d.astype(str), side="right") - 1
    ok = i >= 0
    neden[~ok] = NEDEN_DOSYALAMA_YOK
    if ok.any():
        ii = i[ok]
        f = sr.filed[ii]
        yas = (pd.to_datetime(pd.Series(d[ok].astype(str))).to_numpy()
               - pd.to_datetime(pd.Series(f)).to_numpy()).astype("timedelta64[D]").astype(int)
        bayat = yas > BAYAT_GUN
        gec = sr.gecersiz[ii]
        deger = sr.val[ii] * sr.B_son / sr.B[ii]
        deger = np.where(bayat | gec, np.nan, deger)
        nd = np.where(gec, NEDEN_OLCEK, np.where(bayat, NEDEN_BAYAT, ""))
        out[ok] = deger
        neden[ok] = nd
    for k in neden:
        _say(str(k))
    return out, neden


def as_of_shares_detay(ticker: str, date: str | None) -> tuple[float | None, str]:
    """(değer, neden). Değer None ise neden BOŞ DEĞİLDİR — "ölçülemedi"nin sebebi adıyla döner."""
    if not date:
        _SAYAC["cagri"] += 1
        _say(NEDEN_TARIH_YOK)
        return None, NEDEN_TARIH_YOK
    v, nd = as_of_shares_series(ticker, [date])
    x = float(v[0])
    return (None if not np.isfinite(x) else x), str(nd[0])


def as_of_shares(ticker: str, date: str | None) -> float | None:
    """t gününde BİLİNEBİLEN dolaşımdaki hisse sayısı (güncel bölünme bazında) — yoksa None."""
    return as_of_shares_detay(ticker, date)[0]


def okuma_raporu() -> dict:
    """Sayaç + yükleme muhasebesi. TÜKETİCİSİ VAR (YASA 6): `component_ic.json` → `turnover_kaynak`.

    `oran_olculdu` payda sıfırken None'dur — "hiç çağrı yapılmadı" ile "hepsi ölçülemedi" aynı
    cümle değildir ve 0.0 yazmak ikisini birbirine karıştırırdı."""
    cagri = _SAYAC["cagri"]
    return {
        "dosya": str(SHARES_FILE), "dosya_var": SHARES_FILE.exists(),
        "yukleme": dict(_YUKLEME),
        "cagri": cagri, "olculdu": _SAYAC["olculdu"], "olculemedi": _SAYAC["olculemedi"],
        "neden": dict(_SAYAC["neden"]),
        # KAPSAM DIŞI SEMBOLLERİN ADI (olay yerine liste — gerekçe `as_of_shares_series`in içinde):
        # "6 sembolde ölçülemedi" cümlesi hangi 6 sembol olduğunu söylemezse eyleme dönüşmez.
        "kapsam_disi_sembol": sorted(_KAPSAM_DISI),
        "oran_olculdu": (None if not cagri else round(_SAYAC["olculdu"] / cagri, 4)),
        "beyan": ("SALT-OKUNUR köprü; ölçülemeyen hücre None + neden (fail-open). Fiziksel devir "
                  "bekçisi BURADA DEĞİL `indicators.turnover21`dedir (orana bakar, sayıma değil)."),
    }


def _sifirla() -> None:
    """Önbelleği ve sayaçları boşaltır. YALNIZ TESTLER İÇİN — canlı yolda çağıran yoktur."""
    global _TABLO
    _TABLO = None
    _SERILER.clear()
    _YUKLEME.clear()
    _SAYAC.update({"cagri": 0, "olculdu": 0, "olculemedi": 0, "neden": {}})
    _KAPSAM_DISI.clear()
