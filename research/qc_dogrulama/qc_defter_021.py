"""EDG-2026-021 · QC DELIST-DAHİL DOĞRULAMA DEFTERİ (QuantConnect Research / QuantBook).

Kart: research/cards/EDG-2026-021-qc-delist-dogrulama.yaml (status: registered)
İkiz tasarım: EDG-2026-016 (research/olcumler/wp2_olcum/RAPOR_016.md) — bu defter onun
QC/delist-dahil karşılığıdır; tanımlar oraya elden geldiğince BİREBİR bağlanır, her sapma
`tanim_sapmalari` altında JSON'a YAZILIR.

BU DEFTER NE YAPAR / NE YAPMAZ
------------------------------
YAPAR : sayı üretir. Dilim fazlası, CI, maliyet satırları, evren/delist muhasebesi.
YAPMAZ: EŞİK KOYMAZ, HÜKÜM VERMEZ. "SUCCESS", "KILL", "anlamlı/anlamsız" kelimeleri
        çıktı JSON'unda YOKTUR. Aralığın sıfırı dışlayıp dışlamadığı ARİTMETİK bir
        özelliktir ve `sifir_disinda` alanında öyle raporlanır; hüküm Rol-1'dedir.
        TEK istisna, kartın `guards` maddesinin AÇIKÇA emrettiği pozitif-kontrol
        kapısıdır: PK işaret/mertebe tutmazsa defter SONRAKİ HÜCRELERİ KOŞTURMAZ.
        Bu bir hüküm eşiği değil, boru hattı geçerlilik kapısıdır.

UYDURMA YASAĞI: ölçülemeyen her büyüklük None + `neden` ile döner. Hiçbir yerde
varsayılanla doldurma yoktur.

KULLANIM
--------
QuantConnect → Research → yeni Python notebook → bu dosyanın TAMAMINI yapıştır ve koş.
Hücre sınırları `# %%` ile işaretlidir: istersen hücre hücre ayır, istersen tek hücre
olarak koş — İKİSİ DE çalışır (durum tek bir `S` sözlüğünde taşınır, hücreler `_kapi()`
ile kendini kapatır). Ayrıntı: OPERATOR_TALIMATI.md · Çıktı şeması: cikti_semasi.md

HÜCRE HARİTASI (13 blok)
------------------------
  H0   ayarlar + kaynak-koruma anahtarları + durum sözlüğü            [veri yok, ölçüm yok]
  H1   kütüphaneler, QuantBook, SAVUNMALI QC-API keşfi                [veri yok, ölçüm yok]
  H1b  bağımsız ölçüm araçları (bootstrap/Spearman kopyaları)         [+ determinizm sınaması]
  H2   evren: aylık dolar-hacim üst-N (delist DAHİL) + SPX/ETF kesişim denemesi
  H3   fiyat/hacim tarihi (parça parça; ham + düzeltilmiş)
  H4   fiyat-türevi öznitelikler: rvol20, mom21, medyan21(hacim), fwd10/fwd20
  H5   POZİTİF KONTROL — rvol20 @20 Spearman IC (kart guard'ı) → KAPI  ← İLK ÖLÇÜM İŞİ
  H6   shares_outstanding as-of → turnover21 (+ tanım sapmaları)       ← kapının ARKASINDA
  H7   kesit + üst-%20 dilim + aynı-gün evren tabanı
  H8   ÖLÇÜM: dilim evren-fazlası @10/@20 + 21g blok bootstrap CI + maliyet satırları
  H9   alt-dönem betimleyici tablo (CI YOK — kart grid'inde bacak değil)
  H10  evren/delist muhasebesi + survivorship-primi göstergeleri (CI YOK — betimleyici)
  H11  TEK JSON bloğu (DUR hâlinde de koşar)
"""

# %%
# =====================================================================================
# HÜCRE H0 — AYARLAR, KAYNAK-KORUMA ANAHTARLARI, DURUM
# =====================================================================================
# Bu hücrenin tamamı SABİTTİR ve en üstte durur: uzun koşum riskinde operatör yalnız
# buradaki anahtarları daraltır, defterin gerisine DOKUNMAZ.
# VARSAYILANLAR = KARTIN PENCERESİ. Daraltılırsa JSON'daki `anahtarlar` bloğu bunu
# olduğu gibi taşır; daraltılmış bir koşum hükme GİRMEZ, Rol-1 farkı orada görür.

from datetime import datetime, timedelta

ANAHTAR = {
    # --- kartın beyanı (DEĞİŞTİRME: değişirse koşum kart-dışı olur) ---
    "PENCERE_BAS":  datetime(2020, 8, 1),
    "PENCERE_SON":  datetime(2026, 7, 28),
    "EVREN_N":      250,          # aylık dolar-hacim üst-N (large-cap süzgeci)
    "UST_PCT":      0.20,         # kayıtlı dilim: turnover üst %20
    "UFUKLAR":      (10, 20),     # ileri getiri ufukları

    # --- EDG-016 ile ortak ölçüm sabitleri (ikizlik şartı) ---
    "BLOK":         21,           # blok bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ
    "BOOT":         2000,         # ortalama CI replikasyonu
    "BOOT_IC":      600,          # IC CI replikasyonu (pozitif kontrol)
    "TOHUM":        20260801,     # sabit tohum (ortak.RNG ile aynı sayı)
    "MIN_KESIT":    50,           # bir gözlem gününün kesiti bundan azsa gün kullanılmaz
    "MIN_DILIM":    30,           # bir ölçümün asgari satır sayısı (analytics.IC_MIN_SAMPLE tabanı)
    "MALIYET_BPS":  10.0,         # kart cost_model
    "MALIYET_BPS_DUYARLILIK": 20.0,
    "RVOL_PENCERE": 20,           # rvol20 = hacim / SMA20(hacim)  (payda BUGÜNÜ İÇERİR)
    "TURNOVER_PENCERE": 21,       # medyan21(hacim)
    "MOM_PENCERE":  21,           # mom21 = close[t]/close[t-21] - 1

    # --- pozitif kontrol kapısı (kart guards) ---
    "PK_CIVI":      0.064,        # yerel çivi (EDG-016 turunda 0.0642 ölçüldü)
    "PK_MERTEBE":   5.0,          # "işaret/mertebe": |IC| çivinin 1/5'i ile 5 katı arasında olmalı

    # --- KAYNAK KORUMA (uzun koşum riski) — varsayılanlar sınırsızdır ---
    "MAKS_SEMBOL":  None,         # None = evren birleşiminin tamamı. Sayı verilirse kırpılır.
    "AY_LIMIT":     None,         # None = penceredeki tüm aylar. Sayı verilirse İLK n ay.
    "PARCA":        25,           # tarih/fundamental çağrılarında sembol parça büyüklüğü
    "DELIST_TAMPON_GUN": 10,      # son barı pencere sonundan bu kadar önce biten isim = delist-vekili
}

# Durum: tüm hücreler bunu paylaşır (global bildirimi gerekmesin diye tek sözlük).
S = {
    "DUR": None,                  # doluysa sonraki hücreler KOŞMAZ
    "uyarilar": [],
    "olculemedi": [],
    "tanim_sapmalari": [],
    "api_yolu": {},               # hangi QC-API adı işledi (savunmalı keşfin kaydı)
}


def _kapi(ad):
    """Hücre kapısı. `S['DUR']` doluysa hücre KOŞMAZ ve nedenini basar."""
    if S["DUR"]:
        print(f"[H{ad}] KOŞTURULMADI — DUR: {S['DUR']}")
        return False
    print(f"[H{ad}] başlıyor...", flush=True)
    return True


def _uyar(m):
    S["uyarilar"].append(m)
    print(f"   UYARI: {m}", flush=True)


def _sapma(alan, ne, neden):
    """Kart tanımından SAPMA kaydı — JSON'a `tanim_sapmalari` olarak gider (YASA: beyan)."""
    S["tanim_sapmalari"].append({"alan": alan, "kullanilan": ne, "neden": neden})
    print(f"   TANIM SAPMASI [{alan}] → {ne} · {neden}", flush=True)


def _olculemedi(alan, neden):
    S["olculemedi"].append({"alan": alan, "neden": neden})
    print(f"   ÖLÇÜLEMEDİ [{alan}] · {neden}", flush=True)


print("H0 tamam — kart penceresi:",
      ANAHTAR["PENCERE_BAS"].date(), "→", ANAHTAR["PENCERE_SON"].date(),
      "| evren üst-N:", ANAHTAR["EVREN_N"],
      "| daraltma anahtarları:",
      {k: ANAHTAR[k] for k in ("MAKS_SEMBOL", "AY_LIMIT", "PARCA")})


# %%
# =====================================================================================
# HÜCRE H1 — KÜTÜPHANELER, QuantBook, SAVUNMALI QC-API KEŞFİ
# =====================================================================================
# NEDEN SAVUNMALI: LEAN'in Python yüzeyi iki adlandırma döneminden geçti (PascalCase →
# snake_case) ve bu defteri yazan ajanın koşacağı LEAN sürümünü DOĞRULAMA imkânı yoktu
# (ağ çağrısı yasak). Bu yüzden HER QC çağrısı "adlar listesi" üzerinden yapılır: hangi
# ad varsa o kullanılır, hangisinin işlediği JSON'da `api_yolu` altında RAPORLANIR.
# Hiçbir yol işlemezse defter DURur — sessizce vekil üretmez.

if _kapi("1"):
    import json
    import math
    import traceback

    import numpy as np
    import pandas as pd

    try:
        from AlgorithmImports import *          # QC Research standart girişi
        S["api_yolu"]["import"] = "AlgorithmImports"
    except Exception:                            # eski/ayrık ortam
        from QuantConnect import *               # noqa: F401,F403
        from QuantConnect.Data import *          # noqa: F401,F403
        from QuantConnect.Data.UniverseSelection import *   # noqa: F401,F403
        from QuantConnect.Research import *      # noqa: F401,F403
        S["api_yolu"]["import"] = "QuantConnect.* (AlgorithmImports yok)"

    _YOK = object()

    def _oz(nesne, *adlar, vars=_YOK):
        """İlk VAR OLAN özniteliği döndürür (PascalCase/snake_case ayrımını yutar)."""
        for a in adlar:
            try:
                return getattr(nesne, a)
            except Exception:
                continue
        if vars is _YOK:
            raise AttributeError(f"hiçbiri yok: {adlar}")
        return vars

    def _cagir(nesne, adlar, *args, **kw):
        """Adlardan İLK ÇALIŞANI çağırır. Dönüş: (sonuç, işleyen_ad). Hiçbiri olmazsa hata."""
        hatalar = []
        for a in adlar:
            f = getattr(nesne, a, None)
            if f is None:
                hatalar.append(f"{a}: yok")
                continue
            try:
                return f(*args, **kw), a
            except Exception as e:
                hatalar.append(f"{a}: {type(e).__name__}: {e}")
        raise RuntimeError("hiçbir QC-API yolu işlemedi → " + " | ".join(hatalar))

    def _enum(sinif, *adlar):
        """Enum üyesini savunmalı çöz (Resolution.DAILY vs Resolution.Daily)."""
        for a in adlar:
            v = getattr(sinif, a, None)
            if v is not None:
                return v, a
        return None, None

    def _sutun(df, *adaylar):
        """DataFrame sütun adını normalize ederek (küçük harf, _ ve . atılmış) bulur."""
        norm = {str(c).lower().replace("_", "").replace(".", ""): c for c in df.columns}
        for a in adaylar:
            k = a.lower().replace("_", "").replace(".", "")
            if k in norm:
                return norm[k]
        return None

    _SID_HAVUZ = {}

    def _sid(sym):
        """Sembolün ZAMANDAN BAĞIMSIZ kimliği. Ticker DEĞİL: ticker değişir, delist'te
        yeniden kullanılır; SecurityIdentifier bu defterin tek birleştirme anahtarıdır.

        HAVUZ (interning) BİLİNÇLİ: panelde milyonlarca satır olur ve her satır için yeni
        bir str nesnesi üretmek research düğümünde yüzlerce MB'a mal olur. Eşit sid'ler
        TEK nesneyi paylaşır → sütun sadece işaretçi taşır."""
        try:
            s = str(_oz(sym, "ID", "id"))
        except Exception:
            s = str(sym)
        return _SID_HAVUZ.setdefault(s, s)

    def _ticker(sym):
        try:
            return str(_oz(sym, "Value", "value"))
        except Exception:
            return str(sym)

    # ---------------- QuantBook ----------------
    qb = QuantBook()
    S["api_yolu"]["quantbook"] = "QuantBook()"

    # Ticker→Symbol çözümü QuantBook'un tarih bağlamını kullanır; pencere sonuna
    # sabitlemeyi DENERİZ (delist edilmiş isimlerin çözümü buna bağlı olabilir).
    try:
        _cagir(qb, ["set_end_date", "SetEndDate"], ANAHTAR["PENCERE_SON"])
        _cagir(qb, ["set_start_date", "SetStartDate"], ANAHTAR["PENCERE_BAS"])
        S["api_yolu"]["tarih_baglami"] = "set_start_date/set_end_date uygulandı"
    except Exception as e:
        S["api_yolu"]["tarih_baglami"] = f"uygulanamadı ({type(e).__name__})"
        _uyar("QuantBook tarih bağlamı kurulamadı — sembol çözümü ortam varsayılanıyla yapılır")

    # ---------------- enum'lar ----------------
    S["res_daily"], _ad = _enum(Resolution, "DAILY", "Daily")
    S["api_yolu"]["Resolution.Daily"] = _ad
    if S["res_daily"] is None:
        S["DUR"] = "Resolution.Daily/DAILY çözülemedi — QC ortamı beklenenden farklı"

    try:
        S["dnm_raw"], _a1 = _enum(DataNormalizationMode, "RAW", "Raw")
        S["dnm_adj"], _a2 = _enum(DataNormalizationMode, "ADJUSTED", "Adjusted")
        S["api_yolu"]["DataNormalizationMode"] = {"raw": _a1, "adjusted": _a2}
    except Exception:
        S["dnm_raw"] = S["dnm_adj"] = None
        S["api_yolu"]["DataNormalizationMode"] = None
        _uyar("DataNormalizationMode çözülemedi — tarih çağrıları ortam varsayılanıyla yapılır")

    print("   API keşfi:", json.dumps(
        {k: str(v) for k, v in S["api_yolu"].items()}, ensure_ascii=False))


# %%
# =====================================================================================
# HÜCRE H1b — BAĞIMSIZ ÖLÇÜM ARAÇLARI (repo'dan İTHAL EDİLMEZ, KOPYA TAŞINIR)
# =====================================================================================
# Kart guard'ı: "defter deterministik (sabit tohum), tek dosya, DIŞ BAĞIMLILIKSIZ".
# Aşağıdaki iki bootstrap ve Spearman, Meridian'daki karşılıklarının BİREBİR kopyasıdır:
#   · gun_blok_bootstrap_ort  ≡ research/olcumler/wp2_olcum/ortak.py :: mean_block_boot
#     (EDG-016'nın CI'sını üreten şema — HEADLINE budur, ikizlik şartı)
#   · blok_bootstrap_ci       ≡ meridian/olcum_araclari.py :: blok_bootstrap_ci
#     (repo'nun kanonik aracı — burada gün-ortalaması serisine uygulanan İKİNCİL okuma)
#   · spearman_ic             ≡ meridian/analytics.py :: spearman_ic
#
# İKİSİ NEDEN BİRDEN: `blok_bootstrap_ci` DÜZ bir seriyi blokluyor; EDG-016'nın CI'sı ise
# 21 ardışık GÖZLEM GÜNÜ bloğunu tüm satırlarıyla yeniden örneklüyor. Bunlar farklı
# istatistiklerdir (satır-ağırlıklı vs gün-ağırlıklı). Kıyaslanabilirlik gün-blok şemasını
# şart koşar; kanonik araç ikinci bir okuma olarak taşınır. İkisi de JSON'a girer.

if _kapi("1b"):

    def gun_blok_bootstrap_ort(y, gunler, n_boot=None, blok=None, tohum=None, seviye=0.95):
        """21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap — ORTALAMA istatistiği (satır-ağırlıklı).

        Yeniden örnekleme birimi ardışık gün bloğudur: aynı günün satırlarının kesitsel
        bağımlılığını VE örtüşen ileri getirilerin seri korelasyonunu birlikte taşır.
        ortak.mean_block_boot ile cebirsel özdeş; TEK fark: bu kopya HER ÇAĞRIDA kendi
        tohumunu kurar (ortak.RNG paylaşımlı-durumluydu; orada çağrı SIRASI CI'yı
        etkiliyordu, burada etkilemez — beyan).
        """
        n_boot = ANAHTAR["BOOT"] if n_boot is None else n_boot
        blok = ANAHTAR["BLOK"] if blok is None else blok
        tohum = ANAHTAR["TOHUM"] if tohum is None else tohum

        y = np.asarray(y, dtype=float)
        g = np.asarray(gunler)
        ok = np.isfinite(y)
        n_dusen = int((~ok).sum())
        y, g = y[ok], g[ok]
        n = int(len(y))
        if n < ANAHTAR["MIN_DILIM"]:
            return {"n": n, "ort": None, "lo": None, "hi": None, "sifir_disinda": None,
                    "neden": f"n={n} < MIN_DILIM={ANAHTAR['MIN_DILIM']}"}
        uniq, inv = np.unique(g, return_inverse=True)
        nd = int(len(uniq))
        if nd < blok * 3:
            return {"n": n, "ort": float(y.mean()), "lo": None, "hi": None,
                    "sifir_disinda": None, "n_gun": nd,
                    "neden": f"gözlem günü {nd} < blok*3 ({blok*3}) — blok bootstrap kurulamaz"}
        sums = np.bincount(inv, weights=y, minlength=nd)
        cnts = np.bincount(inv, minlength=nd).astype(float)
        n_blok = int(np.ceil(nd / blok))
        son_bas = nd - blok
        ofs = np.arange(blok)
        rng = np.random.default_rng(tohum)
        vals, atlanan = [], 0
        for _ in range(int(n_boot)):
            bas = rng.integers(0, son_bas + 1, n_blok)
            gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
            c = cnts[gun].sum()
            if c <= 0:
                atlanan += 1
                continue
            vals.append(sums[gun].sum() / c)
        if len(vals) < n_boot * 0.5:
            return {"n": n, "ort": float(y.mean()), "lo": None, "hi": None,
                    "sifir_disinda": None, "n_gun": nd,
                    "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
        a = np.asarray(vals, float)
        alt = (1.0 - seviye) / 2.0 * 100.0
        lo, hi = (float(q) for q in np.percentile(a, [alt, 100.0 - alt]))
        return {
            "n": n, "n_gun": nd, "ort": float(y.mean()),
            "medyan": float(np.median(y)), "std": float(np.std(y, ddof=1)),
            "pozitif_oran": float((y > 0).mean()),
            "lo": lo, "hi": hi, "seviye": seviye,
            "sifir_disinda": bool(lo > 0 or hi < 0),
            "blok": int(blok), "B": int(n_boot), "B_gecerli": int(len(vals)),
            "atlanan": int(atlanan), "tohum": int(tohum),
            "n_sayi_olmayan_dusen": n_dusen,
            "yontem": ("gün-blok (moving) bootstrap · yeniden örnekleme birimi = "
                       f"{blok} ardışık gözlem günü · satır-ağırlıklı ortalama"),
            "beyan": ("`sifir_disinda` ARİTMETİK bir özelliktir (aralık 0'ı kapsıyor mu), "
                      "hüküm DEĞİLDİR."),
            "neden": None,
        }

    def blok_bootstrap_ci(seri, blok=None, n_ornek=None, seviye=0.95, tohum=11):
        """meridian/olcum_araclari.py :: blok_bootstrap_ci BİREBİR KOPYASI (düz seri, moving blok).

        Bu defterde GÜN-ORTALAMASI serisine (her gün bir gözlem) uygulanır → gün-ağırlıklı
        ikincil okuma. Varsayılan tohum 11: repo'daki BOOTSTRAP_TOHUM ile aynı sayı.
        ÖLÇÜLEMEDİĞİNDE UYDURMAZ: n<2 ise lo/hi None + neden.
        """
        n_ornek = ANAHTAR["BOOT"] if n_ornek is None else n_ornek
        ham = list(seri) if seri is not None else []
        vals, n_cozulemeyen = [], 0
        for v in ham:
            try:
                f = float(v)
            except (TypeError, ValueError):
                n_cozulemeyen += 1
                continue
            if f != f or f in (float("inf"), float("-inf")):
                n_cozulemeyen += 1
                continue
            vals.append(f)
        n = len(vals)
        uyarilar = []
        if n_cozulemeyen:
            uyarilar.append(f"{n_cozulemeyen} gözlem sayı değildi (NaN/None/sonsuz) ve seriden "
                            f"düştü — aralık n={n} üzerinden kuruldu")
        if n < 2:
            return {"ort": (vals[0] if n == 1 else None), "lo": None, "hi": None,
                    "seviye": seviye, "n": n, "blok": None, "B": 0, "iid": None,
                    "sifiri_disliyor": None, "n_cozulemeyen": n_cozulemeyen, "tohum": tohum,
                    "yontem": "moving block bootstrap (koşulmadı)",
                    "neden": f"n={n} < 2 — ortalamanın örnekleme dağılımı kurulamaz",
                    "beyan": "aralık ÖLÇÜLEMEDİ; None bir sayı değildir ve 0 yerine geçmez",
                    "uyari": (" · ".join(uyarilar) if uyarilar else None)}
        if blok is None:
            L = max(1, min(n, int(round(n ** (1.0 / 3.0)))))
            blok_kaynagi = "n^(1/3) kuralı"
        else:
            L = max(1, min(int(blok), n))
            blok_kaynagi = "verildi" if L == int(blok) else f"verildi ({int(blok)}) ama n={n}'e kırpıldı"
        B = max(1, int(n_ornek))
        x = np.asarray(vals, dtype=float)
        k = -(-n // L)
        rng = np.random.default_rng(tohum)
        bas = rng.integers(0, n - L + 1, size=(B, k))
        idx = bas[:, :, None] + np.arange(L)[None, None, :]
        ort = x[idx].reshape(B, k * L)[:, :n].mean(axis=1)
        alt = (1.0 - seviye) / 2.0 * 100.0
        lo, hi = (float(q) for q in np.percentile(ort, [alt, 100.0 - alt]))
        if L == 1:
            uyarilar.append("blok=1 → BU BİR IID BOOTSTRAP'TIR; zaman-sıralı seride aralığı daraltır")
        if n < 4 * L:
            uyarilar.append(f"n={n}, blok={L} — seride yalnız ~{n / L:.1f} blok var")
        return {"ort": float(x.mean()), "lo": lo, "hi": hi, "seviye": seviye, "n": n,
                "blok": L, "blok_kaynagi": blok_kaynagi, "B": B, "iid": (L == 1),
                "sifiri_disliyor": bool(lo > 0 or hi < 0),
                "n_cozulemeyen": n_cozulemeyen, "tohum": tohum,
                "yontem": (f"moving (örtüşen) blok bootstrap · blok={L} ({blok_kaynagi}) · "
                           f"B={B} · tohum={tohum} · yüzdelik aralığı"),
                "neden": None,
                "beyan": "Bloklar sarılmaz; aralık ORTALAMA içindir.",
                "uyari": (" · ".join(uyarilar) if uyarilar else None)}

    def _rank_avg(a):
        """analytics._rank_avg ile aynı: beraberlikler ORTALAMA rütbeyle kırılır."""
        return pd.Series(np.asarray(a, dtype=float)).rank().to_numpy()

    def spearman_ic(x, y):
        """meridian/analytics.py :: spearman_ic ile aynı — rütbe değişimi yoksa None
        (0.0 DEĞİL: 'ölçtük, ilişki yok' ile 'ölçülemedi' aynı şey değildir)."""
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if x.size == 0 or x.size != y.size:
            return None
        rx, ry = _rank_avg(x), _rank_avg(y)
        den = rx.std() * ry.std()
        if den <= 0:
            return None
        return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / den)

    def ic_gun_blok_ci(x, y, gunler, n_boot=None, blok=None, tohum=None):
        """IC için gün-blok bootstrap (ortak.ic_with_ci / k016.ic_block_boot_fast şeması)."""
        n_boot = ANAHTAR["BOOT_IC"] if n_boot is None else n_boot
        blok = ANAHTAR["BLOK"] if blok is None else blok
        tohum = ANAHTAR["TOHUM"] if tohum is None else tohum
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        g = np.asarray(gunler)
        uniq, inv = np.unique(g, return_inverse=True)
        nd = int(len(uniq))
        if nd < blok * 3:
            return {"lo": None, "hi": None, "n_gun": nd,
                    "neden": f"gözlem günü {nd} < {blok * 3}"}
        order = np.argsort(inv, kind="stable")
        cnt = np.bincount(inv, minlength=nd)
        start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
        n_blok = int(np.ceil(nd / blok))
        son_bas = nd - blok
        ofs = np.arange(blok)
        rng = np.random.default_rng(tohum)
        vals, atlanan = [], 0
        for _ in range(int(n_boot)):
            bas = rng.integers(0, son_bas + 1, n_blok)
            gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
            c = cnt[gun]
            tot = int(c.sum())
            if tot < ANAHTAR["MIN_DILIM"]:
                atlanan += 1
                continue
            cikis_bas = np.concatenate([[0], np.cumsum(c)[:-1]])
            poz = np.arange(tot) - np.repeat(cikis_bas, c) + np.repeat(start[gun], c)
            idx = order[poz]
            v = spearman_ic(x[idx], y[idx])
            if v is None or not np.isfinite(v):
                atlanan += 1
                continue
            vals.append(v)
        if len(vals) < n_boot * 0.5:
            return {"lo": None, "hi": None, "n_gun": nd, "B_gecerli": len(vals),
                    "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
        a = np.asarray(vals, float)
        lo, hi = float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))
        return {"lo": lo, "hi": hi, "seviye": 0.95, "n_gun": nd, "blok": int(blok),
                "B": int(n_boot), "B_gecerli": int(len(vals)), "atlanan": int(atlanan),
                "tohum": int(tohum), "sifir_disinda": bool(lo > 0 or hi < 0), "neden": None}

    # kendi kendini sınayan mini kontrol (deterministiklik): aynı girdi aynı aralığı vermeli
    _t1 = gun_blok_bootstrap_ort(np.arange(2000) % 7 - 3.0,
                                 np.repeat(np.arange(100), 20), n_boot=200)
    _t2 = gun_blok_bootstrap_ort(np.arange(2000) % 7 - 3.0,
                                 np.repeat(np.arange(100), 20), n_boot=200)
    S["determinizm_sinamasi"] = bool(_t1["lo"] == _t2["lo"] and _t1["hi"] == _t2["hi"])
    print("   determinizm sınaması (aynı girdi → aynı CI):", S["determinizm_sinamasi"])
    if not S["determinizm_sinamasi"]:
        S["DUR"] = "bootstrap deterministik değil — kart guard'ı 'sabit tohum' ihlal"


# %%
# =====================================================================================
# HÜCRE H2 — EVREN: AYLIK YENİDEN-ÖRNEKLENEN DOLAR-HACİM ÜST-N (DELİST DAHİL)
# =====================================================================================
# KARTIN BEYANI: "S&P500-benzeri large-cap süzgeci defterde TANIMLI ve raporda beyanlı
# (dolar-hacim üst-N; birebir SPX üyeliği QC'de ayrı veri — varsa kullanılır, yoksa
# süzgeç-vekili beyan edilir)".
#
# DELİST-DAHİL NEDEN KENDİLİĞİNDEN OLUYOR: evren, geçmiş bir GÜNÜN fundamental/universe
# anlık görüntüsünden kuruluyor. O gün borsada olan ama bugün olmayan isimler o anlık
# görüntüde VARDIR. Meridian'ın yerel arşivi tersine bugünün sembol listesini geçmişe
# taşıyor — EDG-016'nın Ç1 çekincesi tam olarak buydu.
#
# SAVUNMALI: universe verisine 4 ayrı QC-API yolu denenir; hangisi varsa o kullanılır ve
# `api_yolu["evren"]` alanına YAZILIR. Hiçbiri işlemezse defter DURur.

if _kapi("2"):

    _EVREN_SUTUNLAR = ["tarih", "sym", "dolar_hacim", "fiyat", "hacim",
                       "market_cap", "shares", "fund_var"]

    def _sayi(v):
        try:
            f = float(v)
            return f if np.isfinite(f) else None
        except (TypeError, ValueError):
            return None

    def _normalize_evren(h):
        """QC'nin döndürdüğü NE İSE onu tek bir DataFrame sözleşmesine çevirir.
        Sütunlar: tarih · sym · dolar_hacim · fiyat · hacim · market_cap · shares · fund_var
        Bulunmayan alanlar NaN/None kalır — DOLDURULMAZ (uydurma yasağı)."""
        bos = pd.DataFrame(columns=_EVREN_SUTUNLAR)
        if h is None:
            return bos
        # --- DataFrame yolu (VEKTÖREL — satır satır .iloc yüz binlerce satırda kabul edilemez) ---
        if hasattr(h, "index") and hasattr(h, "columns"):
            df = h
            if len(df) == 0:
                return bos
            names = [str(x).lower() if x is not None else "" for x in (df.index.names or [])]
            i_sym = next((i for i, nm in enumerate(names) if "symbol" in nm or nm == "sid"), None)
            i_t = next((i for i, nm in enumerate(names) if "time" in nm or "date" in nm), None)
            out = pd.DataFrame(index=range(len(df)))
            out["tarih"] = (pd.to_datetime(df.index.get_level_values(i_t)).normalize()
                            if i_t is not None else pd.NaT)
            out["sym"] = (list(df.index.get_level_values(i_sym)) if i_sym is not None
                          else list(df.index))
            for ad, adaylar in (("dolar_hacim", ("dollarvolume", "dollar_volume")),
                                ("fiyat", ("price", "adjustedprice", "close", "value")),
                                ("hacim", ("volume",)),
                                ("market_cap", ("marketcap", "market_cap")),
                                ("shares", ("sharesoutstanding",
                                            "companyprofile.sharesoutstanding")),
                                ("fund_var", ("hasfundamentaldata", "has_fundamental_data"))):
                c = _sutun(df, *adaylar)
                out[ad] = (pd.to_numeric(df[c], errors="coerce").to_numpy()
                           if c is not None else np.nan)
            return out[_EVREN_SUTUNLAR]
        # --- nesne / iç içe liste yolu ---
        satir = []
        yigin = [h]
        derinlik = 0
        while yigin and derinlik < 5_000_000:
            derinlik += 1
            o = yigin.pop()
            if o is None or isinstance(o, (str, bytes)):
                continue                                   # str iterable'dır → sonsuz döngü riski
            if hasattr(o, "Symbol") or hasattr(o, "symbol"):
                sym = _oz(o, "Symbol", "symbol", vars=None)
                if sym is None:
                    continue
                t = _oz(o, "EndTime", "end_time", "Time", "time", vars=None)
                prof = _oz(o, "CompanyProfile", "company_profile", vars=None)
                satir.append({
                    "tarih": (pd.Timestamp(t).normalize() if t is not None else pd.NaT),
                    "sym": sym,
                    "dolar_hacim": _sayi(_oz(o, "DollarVolume", "dollar_volume", vars=None)),
                    "fiyat": _sayi(_oz(o, "Price", "price", "AdjustedPrice",
                                       "adjusted_price", vars=None)),
                    "hacim": _sayi(_oz(o, "Volume", "volume", vars=None)),
                    "market_cap": _sayi(_oz(o, "MarketCap", "market_cap", vars=None)),
                    "shares": _sayi(_oz(prof, "SharesOutstanding", "shares_outstanding",
                                        vars=None) if prof is not None else None),
                    "fund_var": _oz(o, "HasFundamentalData", "has_fundamental_data", vars=None),
                })
                continue
            if isinstance(o, (list, tuple, set)) or hasattr(o, "__iter__"):
                try:
                    yigin.extend(list(o))
                except Exception:
                    continue
        return (pd.DataFrame(satir)[_EVREN_SUTUNLAR] if satir else bos)

    # ---- evren kaynağı: 4 yol, İLK İŞLEYEN kazanır ----
    S["_evren_universe_nesnesi"] = None

    def _yol_universe_history(t0, t1):
        if S["_evren_universe_nesnesi"] is None:
            secici = (lambda f: [(_oz(x, "Symbol", "symbol")) for x in f])
            u, ad = _cagir(qb, ["add_universe", "AddUniverse"], secici)
            S["_evren_universe_nesnesi"] = u
            S["api_yolu"]["add_universe"] = ad
        h, ad = _cagir(qb, ["universe_history", "UniverseHistory"],
                       S["_evren_universe_nesnesi"], t0, t1)
        return h, f"{ad}(add_universe)"

    def _yol_history_fundamental(t0, t1):
        h, ad = _cagir(qb, ["history", "History"], Fundamental, t0, t1, S["res_daily"])
        return h, f"{ad}(Fundamental)"

    def _yol_history_fundamental_kwsuz(t0, t1):
        h, ad = _cagir(qb, ["history", "History"], Fundamental, t0, t1)
        return h, f"{ad}(Fundamental, çözünürlüksüz)"

    def _yol_coarse(t0, t1):
        h, ad = _cagir(qb, ["history", "History"], CoarseFundamental, t0, t1, S["res_daily"])
        return h, f"{ad}(CoarseFundamental)"

    _YOLLAR = [("universe_history", _yol_universe_history),
               ("history(Fundamental)", _yol_history_fundamental),
               ("history(Fundamental) çözünürlüksüz", _yol_history_fundamental_kwsuz),
               ("history(CoarseFundamental)", _yol_coarse)]

    def evren_anlik(hedef):
        """`hedef` tarihinden itibaren İLK VERİ DÖNEN günün evren anlık görüntüsü.
        Pencere 6 gün açılır (tatil/hafta sonu payı) ama YALNIZ EN ERKEN GÜN alınır —
        aksi hâlde aynı sembol birkaç kez sayılır ve üst-N sıralaması bozulurdu."""
        t0 = hedef
        t1 = hedef + timedelta(days=6)
        denemeler = []
        for ad, fn in _YOLLAR:
            if S["api_yolu"].get("evren") and S["api_yolu"]["evren"] != ad:
                continue               # yol seçildi: yalnız onu kullan (tutarlılık)
            try:
                h, gercek_ad = fn(t0, t1)
                kayit = _normalize_evren(h)
                if kayit is not None and len(kayit):
                    if kayit["tarih"].notna().any():
                        ilk = kayit["tarih"].min()
                        kayit = kayit[kayit["tarih"] == ilk]
                    kayit = kayit.drop_duplicates(subset=["sym"], keep="first")
                    S["api_yolu"]["evren"] = ad
                    S["api_yolu"]["evren_cagri"] = gercek_ad
                    return kayit, None
                denemeler.append(f"{ad}: boş döndü")
            except Exception as e:
                denemeler.append(f"{ad}: {type(e).__name__}: {e}")
        return None, " | ".join(denemeler)

    # ---- aylık seçim tarihleri ----
    aylar = []
    _t = ANAHTAR["PENCERE_BAS"]
    while _t <= ANAHTAR["PENCERE_SON"]:
        aylar.append(_t)
        _t = (_t.replace(day=1) + timedelta(days=32)).replace(day=1)
    if ANAHTAR["AY_LIMIT"]:
        aylar = aylar[:int(ANAHTAR["AY_LIMIT"])]
        _sapma("evren_aylari", f"ilk {len(aylar)} ay",
               "AY_LIMIT anahtarı daraltıldı — koşum kart penceresinin TAMAMI DEĞİLDİR")

    uyelik = {}          # ay_indeksi -> {sid: sym}
    sym_kutugu = {}      # sid -> Symbol nesnesi
    ay_muhasebe = []
    for i, ay in enumerate(aylar):
        kayit, hata = evren_anlik(ay)
        if kayit is None:
            if i == 0:
                S["DUR"] = ("EVREN ÇEKİLEMEDİ — denenen QC-API yollarının hiçbiri veri "
                            f"döndürmedi. Denemeler: {hata}")
                break
            _uyar(f"{ay.date()} evren anlık görüntüsü alınamadı ({hata}) — ay atlandı")
            ay_muhasebe.append({"ay": str(ay.date()), "n_ham": 0, "n_secilen": 0,
                                "neden": "veri yok"})
            continue
        dv = pd.to_numeric(kayit["dolar_hacim"], errors="coerce")
        adaylar = kayit[dv.notna() & (dv > 0)].assign(_dv=dv[dv.notna() & (dv > 0)])
        if adaylar.empty:      # dolar hacim yoksa fiyat×hacim vekili
            px = pd.to_numeric(kayit["fiyat"], errors="coerce")
            vol = pd.to_numeric(kayit["hacim"], errors="coerce")
            m = px.notna() & vol.notna() & (px > 0) & (vol > 0)
            adaylar = kayit[m].assign(_dv=(px * vol)[m])
            if not adaylar.empty and "dolar_hacim_vekili" not in S["api_yolu"]:
                S["api_yolu"]["dolar_hacim_vekili"] = "fiyat × hacim (DollarVolume alanı yoktu)"
                _sapma("dolar_hacim", "fiyat × hacim",
                       "evren kaydında DollarVolume alanı bulunamadı")
        secilen = adaylar.sort_values("_dv", ascending=False).head(ANAHTAR["EVREN_N"])
        uyelik[i] = {}
        for sym in secilen["sym"].tolist():
            sid = _sid(sym)
            uyelik[i][sid] = sym
            sym_kutugu[sid] = sym
        ay_muhasebe.append({"ay": str(ay.date()), "n_ham": int(len(kayit)),
                            "n_aday": int(len(adaylar)), "n_secilen": int(len(secilen)),
                            "neden": None})
        if i % 6 == 0 or i == len(aylar) - 1:
            print(f"   evren {i+1}/{len(aylar)} · {ay.date()} · ham={len(kayit)} "
                  f"seçilen={len(secilen)}", flush=True)

    if not S["DUR"]:
        # ---- SPX / ETF üyelik KESİŞİM DENEMESİ (kart: "varsa kullanılır") ----
        spx = {"denendi": True, "basarili": False, "yol": None, "n_kesisim": None,
               "neden": None,
               "karar": ("kesişim BAŞARISIZSA süzgeç-vekili (dolar-hacim üst-N) KULLANILIR "
                         "ve bu alan beyandır — kartın izin verdiği yol")}
        try:
            _sp, _ad = _cagir(qb, ["add_equity", "AddEquity"], "SPY", S["res_daily"])
            _spy_sym = _oz(_sp, "Symbol", "symbol")
            _u, _ad2 = _cagir(_oz(qb, "universe", "Universe"), ["etf", "ETF"], _spy_sym)
            _h, _ad3 = _cagir(qb, ["universe_history", "UniverseHistory"],
                              _u, ANAHTAR["PENCERE_SON"] - timedelta(days=10),
                              ANAHTAR["PENCERE_SON"])
            _k = _normalize_evren(_h)
            _spx_sid = {_sid(x) for x in (_k["sym"].tolist() if len(_k) else [])}
            if _spx_sid:
                son_ay = max(uyelik) if uyelik else None
                kes = (_spx_sid & set(uyelik[son_ay])) if son_ay is not None else set()
                spx.update({"basarili": True, "yol": f"universe.etf(SPY)/{_ad3}",
                            "n_spx": len(_spx_sid), "n_kesisim": len(kes)})
                print(f"   SPX/ETF üyeliği ALINDI: n={len(_spx_sid)}, son ay kesişim={len(kes)}")
            else:
                spx["neden"] = "ETF üyelik verisi boş döndü"
        except Exception as e:
            spx["neden"] = f"{type(e).__name__}: {e}"
        if not spx["basarili"]:
            print(f"   SPX/ETF üyeliği ALINAMADI ({spx['neden']}) — SÜZGEÇ-VEKİLİ kullanılıyor")
            _sapma("large_cap_suzgeci",
                   f"aylık dolar-hacim üst-{ANAHTAR['EVREN_N']} (delist dahil)",
                   f"birebir SPX üyelik verisi alınamadı: {spx['neden']}")
        S["spx_uyelik_denemesi"] = spx

        # ---- birleşim ----
        birlesim = sorted(sym_kutugu.keys())
        if ANAHTAR["MAKS_SEMBOL"] and len(birlesim) > int(ANAHTAR["MAKS_SEMBOL"]):
            sik = {}
            for i in uyelik:
                for sid in uyelik[i]:
                    sik[sid] = sik.get(sid, 0) + 1
            birlesim = [s for s, _ in sorted(sik.items(), key=lambda kv: (-kv[1], kv[0]))
                        ][:int(ANAHTAR["MAKS_SEMBOL"])]
            _sapma("evren_birlesimi", f"en sık üye {len(birlesim)} sembol",
                   "MAKS_SEMBOL anahtarı daraltıldı — koşum kart evreninin TAMAMI DEĞİLDİR")
        S["aylar"] = aylar
        S["uyelik"] = uyelik
        S["sym_kutugu"] = sym_kutugu
        S["birlesim"] = birlesim
        S["ay_muhasebe"] = ay_muhasebe
        print(f"   EVREN HAZIR · {len(aylar)} ay · birleşim {len(birlesim)} sembol · "
              f"API yolu: {S['api_yolu'].get('evren')}")


# %%
# =====================================================================================
# HÜCRE H3 — FİYAT/HACİM TARİHİ (parça parça; HAM + DÜZELTİLMİŞ)
# =====================================================================================
# İKİ AYRI ÇAĞRI, İKİ AYRI İŞ:
#   · DÜZELTİLMİŞ (Adjusted) kapanış → İLERİ GETİRİ. Bölünme/temettü getiriyi kırmasın.
#   · HAM (Raw) hacim → TURNOVER PAYI. Kartın turnover tanımı hacim/hisse_sayısı; QC'nin
#     as-of hisse sayımı O GÜNÜN bazındadır. Ham hacim de o günün bazındadır → oran
#     bölünmeden bağımsızdır. EDG-016 aynı sorunu ters yönden çözmüştü (hisse sayımını
#     güncel baza çevirerek); sonuç aynı, yol farklı — beyan.
# Ham çağrı BAŞARISIZ olursa düzeltilmiş hacim kullanılır ve `tanim_sapmalari`na yazılır.

if _kapi("3"):

    def _normalize_barlar(df, etiket):
        """QC history DataFrame'ini düz tabloya çevirir: sid / tarih / close / volume."""
        if df is None or len(df) == 0:
            return None
        c_close = _sutun(df, "close")
        c_vol = _sutun(df, "volume")
        names = [str(x).lower() if x is not None else "" for x in (df.index.names or [])]
        i_sym = next((i for i, nm in enumerate(names) if "symbol" in nm or nm == "sid"), None)
        i_t = next((i for i, nm in enumerate(names) if "time" in nm or "date" in nm), None)
        if i_sym is None or i_t is None:
            raise RuntimeError(f"{etiket}: history indeks düzeni tanınmadı: {df.index.names}")
        syms = df.index.get_level_values(i_sym)
        out = pd.DataFrame({
            "sid": [_sid(s) for s in syms],
            "tarih": pd.to_datetime(df.index.get_level_values(i_t)).normalize(),
            "close": (df[c_close].to_numpy(dtype="float64") if c_close else np.nan),
            "volume": (df[c_vol].to_numpy(dtype="float64") if c_vol else np.nan),
        })
        return out

    def _tarih_cek(semboller, ham):
        """Savunmalı history çağrısı. Dönüş: (DataFrame|None, kullanılan_yol_metni)."""
        dnm = S["dnm_raw"] if ham else S["dnm_adj"]
        denemeler = []
        # (a) snake_case kwarg → (b) PascalCase kwarg → (c) kwarg'sız
        for kwad in ("data_normalization_mode", "dataNormalizationMode", None):
            if kwad is not None and dnm is None:
                continue
            kw = {kwad: dnm} if kwad else {}
            try:
                h, ad = _cagir(qb, ["history", "History"], semboller,
                               ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"],
                               S["res_daily"], **kw)
                return h, f"{ad}({kwad or 'normalizasyon-kwargsız'})"
            except Exception as e:
                denemeler.append(f"{kwad}: {type(e).__name__}: {e}")
        raise RuntimeError("history çağrısı işlemedi → " + " | ".join(denemeler))

    parcalar = [S["birlesim"][i:i + ANAHTAR["PARCA"]]
                for i in range(0, len(S["birlesim"]), ANAHTAR["PARCA"])]
    adj_p, ham_p = [], []
    ham_basarisiz = 0
    for pi, p in enumerate(parcalar):
        syms = [S["sym_kutugu"][s] for s in p]
        try:
            h, yol = _tarih_cek(syms, ham=False)
            t = _normalize_barlar(h, "adjusted")
            if t is not None:
                adj_p.append(t)
            S["api_yolu"].setdefault("history_adjusted", yol)
        except Exception as e:
            _uyar(f"parça {pi}: düzeltilmiş tarih alınamadı ({type(e).__name__}: {e})")
        if S["dnm_raw"] is not None:
            try:
                h2, yol2 = _tarih_cek(syms, ham=True)
                t2 = _normalize_barlar(h2, "raw")
                if t2 is not None:
                    ham_p.append(t2.rename(columns={"volume": "volume_ham",
                                                    "close": "close_ham"}))
                S["api_yolu"].setdefault("history_raw", yol2)
            except Exception:
                ham_basarisiz += 1
        if pi % 4 == 0 or pi == len(parcalar) - 1:
            print(f"   tarih {pi+1}/{len(parcalar)} parça · "
                  f"adj satır={sum(len(x) for x in adj_p)}", flush=True)

    if not adj_p:
        S["DUR"] = "FİYAT TARİHİ ÇEKİLEMEDİ — hiçbir parça veri döndürmedi"
    else:
        B = pd.concat(adj_p, ignore_index=True)
        B = B.dropna(subset=["close"]).drop_duplicates(subset=["sid", "tarih"])
        if ham_p:
            H = pd.concat(ham_p, ignore_index=True).drop_duplicates(subset=["sid", "tarih"])
            B = B.merge(H[["sid", "tarih", "volume_ham"]], on=["sid", "tarih"], how="left")
            S["hacim_bazi"] = "HAM (Raw) hacim — turnover payı bölünmeden bağımsız"
        else:
            B["volume_ham"] = np.nan
            S["hacim_bazi"] = "DÜZELTİLMİŞ hacim (ham çağrı işlemedi)"
            _sapma("turnover_hacim_bazi", "düzeltilmiş (Adjusted) hacim",
                   "DataNormalizationMode.Raw ile history çağrısı işlemedi; hacim ile "
                   "as-of hisse sayımı FARKLI bölünme bazında olabilir — turnover21 "
                   "bölünme tarihleri çevresinde sapabilir")
        if ham_basarisiz:
            _uyar(f"{ham_basarisiz} parçada ham (Raw) tarih alınamadı — o satırlarda "
                  f"düzeltilmiş hacme düşülür")
        B = B.sort_values(["sid", "tarih"]).reset_index(drop=True)
        S["barlar"] = B
        S["bellek_mb"] = {"H3_barlar": round(B.memory_usage(deep=True).sum() / 1e6, 1)}
        print(f"   panel belleği ≈ {S['bellek_mb']['H3_barlar']} MB "
              f"({len(B)} satır × {len(B.columns)} sütun)")
        S["bar_muhasebe"] = {
            "istenen_sembol": len(S["birlesim"]),
            "bar_donen_sembol": int(B["sid"].nunique()),
            "satir": int(len(B)),
            "tarih_araligi": [str(B["tarih"].min().date()), str(B["tarih"].max().date())],
            "ham_hacim_dolu_satir": int(B["volume_ham"].notna().sum()),
            "hacim_bazi": S["hacim_bazi"],
        }
        print("   BARLAR HAZIR ·", json.dumps(S["bar_muhasebe"], ensure_ascii=False))


# %%
# =====================================================================================
# HÜCRE H4 — FİYAT-TÜREVİ ÖZNİTELİKLER (rvol20, mom21, medyan21(hacim), fwd10/20)
# =====================================================================================
# TANIMLAR EDG-016 / meridian.indicators ile BİREBİR:
#   rvol20(t) = hacim(t) / SMA20(hacim)[t]      ← PAYDA BUGÜNÜ İÇERİR (ölçülen tanım bu)
#   mom21(t)  = close(t)/close(t-21) - 1
#   med_hacim21(t) = medyan(hacim[t-20..t])
#   fwd_h(t)  = close(t+h)/close(t) - 1         ← DÜZELTİLMİŞ kapanışla
# İleri-dönük DEĞİL: tüm pencereler [t-k, t] kapanışında bilinir.

if _kapi("4"):
    B = S["barlar"]
    hac_turnover = B["volume_ham"].where(B["volume_ham"].notna(), B["volume"])
    B = B.assign(hacim_t=hac_turnover)

    g = B.groupby("sid", sort=False)
    B["sma20_hacim"] = g["volume"].transform(
        lambda s: s.rolling(ANAHTAR["RVOL_PENCERE"], min_periods=ANAHTAR["RVOL_PENCERE"]).mean())
    B["rvol20"] = B["volume"] / B["sma20_hacim"]
    B["med_hacim21"] = g["hacim_t"].transform(
        lambda s: s.rolling(ANAHTAR["TURNOVER_PENCERE"],
                            min_periods=ANAHTAR["TURNOVER_PENCERE"]).median())
    B["mom21"] = g["close"].transform(
        lambda s: s / s.shift(ANAHTAR["MOM_PENCERE"]) - 1.0)
    for h in ANAHTAR["UFUKLAR"]:
        B[f"fwd{h}"] = g["close"].transform(lambda s, h=h: s.shift(-h) / s - 1.0)

    # delist-vekili: son barı pencere sonundan TAMPON kadar önce biten isim
    son_bar = B.groupby("sid")["tarih"].max()
    ilk_bar = B.groupby("sid")["tarih"].min()
    panel_son = B["tarih"].max()
    esik = panel_son - pd.Timedelta(days=int(ANAHTAR["DELIST_TAMPON_GUN"] * 1.6))
    delist_sid = set(son_bar[son_bar < esik].index)
    S["delist_sid"] = delist_sid
    S["son_bar"] = son_bar
    S["ilk_bar"] = ilk_bar
    S["delist_yontemi"] = (
        f"VEKİL: sembolün son günlük barı panel sonundan (>{ANAHTAR['DELIST_TAMPON_GUN']} işgünü ≈ "
        f"{int(ANAHTAR['DELIST_TAMPON_GUN']*1.6)} takvim günü) önce bitiyorsa 'sonradan-delist'. "
        "QC'nin map-file/Delisting olayı bu defterde SORULMADI (API yolu doğrulanamadı) — "
        "bu bir VEKİLDİR ve veri kesintisi ile gerçek delist'i ayıramaz.")
    _sapma("delist_tespiti", "son-bar vekili", S["delist_yontemi"])

    # DELİST + İLERİ GETİRİ: delist olan ismin son h günü için fwd TANIMSIZ (bar yok).
    # Bu satırlar düşer; kaç tane olduğunu SAYIYORUZ (sessiz düşüş YASAK) ve ayrıca
    # 'son fiyattan tasfiye' duyarlılığını H10'da ayrı okuyoruz.
    dusen = {}
    sonf = B.groupby("sid")["close"].transform("last")     # sembolün SON düzeltilmiş kapanışı
    for h in ANAHTAR["UFUKLAR"]:
        m = B["sid"].isin(delist_sid) & B[f"fwd{h}"].isna() & B["close"].notna()
        dusen[str(h)] = int(m.sum())
        # duyarlılık serisi: son kapanıştan tasfiye varsayımı (VARSAYIM — H10'da beyanlı)
        B[f"fwd{h}_delist_kapatilmis"] = B[f"fwd{h}"].where(
            B[f"fwd{h}"].notna(), (sonf / B["close"] - 1.0).where(m))
    S["delist_fwd_dusen"] = dusen
    # BELLEK: ara sütunlar düşer, türev öznitelikler float32'ye iner. Rütbe/dilim işlemleri
    # float32'de aynı sonucu verir; CI hesapları zaten float64'e yükseltilerek yapılır.
    B = B.drop(columns=[c for c in ("sma20_hacim", "hacim_t", "volume_ham") if c in B.columns])
    for c in ("rvol20", "med_hacim21", "mom21") + tuple(
            [f"fwd{h}" for h in ANAHTAR["UFUKLAR"]]
            + [f"fwd{h}_delist_kapatilmis" for h in ANAHTAR["UFUKLAR"]]):
        if c in B.columns:
            B[c] = B[c].astype("float32")
    S["barlar"] = B
    S.setdefault("bellek_mb", {})["H4_oznitelikli"] = round(
        B.memory_usage(deep=True).sum() / 1e6, 1)
    print(f"   panel belleği ≈ {S['bellek_mb']['H4_oznitelikli']} MB (ara sütunlar düşürüldü)")
    print(f"   öznitelikler hazır · rvol20 dolu={int(B['rvol20'].notna().sum())} "
          f"med_hacim21 dolu={int(B['med_hacim21'].notna().sum())} "
          f"fwd20 dolu={int(B['fwd20'].notna().sum())}")
    print(f"   delist-vekili sembol={len(delist_sid)} · delist yüzünden fwd düşen satır={dusen}")


# %%
# =====================================================================================
# HÜCRE H5 — POZİTİF KONTROL (KART GUARD'I) — İLK KOŞAN ÖLÇÜM İŞİ · KAPI
# =====================================================================================
# Kart guards: "pozitif kontrol defterin İÇİNDE: rvol20 @20 IC işareti/mertebesi (yerel
# çivi ≈0.064) QC evreninde yeniden üretilir — üretilemezse defter DUR der ve nedenini
# basar."
#
# NEDEN BU ÖLÇÜM İLK: H2-H4 yalnız VERİ TAŞIR, hiçbir hüküm sayısı üretmez. İlk ÖLÇÜM
# işi budur ve tutmazsa boru hattı geçersizdir; H6'daki pahalı fundamentals çağrısı bile
# koşmaz (kaynak koruma bilinçli olarak kapının ARKASINA yerleştirildi).
#
# BU BİR HÜKÜM EŞİĞİ DEĞİLDİR: kart "işaret/mertebe" diyor. Uygulaması: IC pozitif olmalı
# ve büyüklüğü yerel çivinin 1/5'i ile 5 katı arasında kalmalı. Ölçülen sayı, kapı geçse
# de geçmese de JSON'a OLDUĞU GİBİ yazılır — Rol-1 ham sayıyı görür.
# EVRENLER FARKLIDIR (yerel çivi Meridian'ın karşı-olgusal katmanında ölçüldü, buradaki
# kesit tüm evren) — bu yüzden nokta eşitliği DEĞİL, mertebe aranır.

if _kapi("5"):
    B = S["barlar"]
    # kesit: aynı-gün evren üyeliği + rvol20 ve fwd20 tanımlı
    ay_idx = {}
    for i, ay in enumerate(S["aylar"]):
        ay_idx[i] = pd.Timestamp(ay).normalize()

    def _uyelik_maskesi(df):
        """Aylık yeniden-örneklenen üyelik: gün t, t'den önceki EN SON seçim ayının listesi."""
        aylik_ts = pd.Series({i: ay_idx[i] for i in sorted(ay_idx)}).sort_values()
        kes = np.searchsorted(aylik_ts.to_numpy(), df["tarih"].to_numpy(), side="right") - 1
        gecerli = kes >= 0
        ay_no = np.where(gecerli, kes, 0)
        uye = np.zeros(len(df), dtype=bool)
        sids = df["sid"].to_numpy()
        for i in np.unique(ay_no[gecerli]):
            m = gecerli & (ay_no == i)
            if not m.any():
                continue
            uyeler = S["uyelik"].get(int(aylik_ts.index[i]), {})
            uye[m] = pd.Series(sids[m]).isin(list(uyeler.keys())).to_numpy()
        return uye, ay_no, gecerli

    uye, ay_no, gecerli = _uyelik_maskesi(B)
    B["evren_uye"] = uye
    B["ay_no"] = np.where(gecerli, ay_no, -1)
    S["barlar"] = B

    pk_df = B[B["evren_uye"] & B["rvol20"].notna() & B["fwd20"].notna()]
    kesit = pk_df.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    pk_df = pk_df[pk_df["tarih"].isin(kullan)]

    pk = {
        "tanim": "rvol20 = hacim / SMA20(hacim) (payda bugünü içerir) — meridian.indicators.rvol20",
        "olcum": "havuzlanmış Spearman IC (rvol20, fwd20) · aynı kesit kuralları",
        "yerel_civi": ANAHTAR["PK_CIVI"],
        "mertebe_carpani": ANAHTAR["PK_MERTEBE"],
        "beyan": ("Yerel çivi Meridian'ın karşı-olgusal katmanında ölçüldü; buradaki evren "
                  "delist-dahil QC kesitidir. NOKTA EŞİTLİĞİ ARANMAZ — kartın yazdığı gibi "
                  "İŞARET ve MERTEBE aranır. Bu bir hüküm eşiği DEĞİL, boru hattı kapısıdır."),
        "n": int(len(pk_df)),
        "n_gun": int(pk_df["tarih"].nunique()),
    }
    if len(pk_df) < ANAHTAR["MIN_DILIM"]:
        pk["ic"] = None
        pk["neden"] = f"n={len(pk_df)} < MIN_DILIM"
        pk["GECTI"] = None
    else:
        ic = spearman_ic(pk_df["rvol20"].to_numpy(float), pk_df["fwd20"].to_numpy(float))
        pk["ic"] = None if ic is None else float(ic)
        pk["ci"] = ic_gun_blok_ci(pk_df["rvol20"].to_numpy(float),
                                  pk_df["fwd20"].to_numpy(float),
                                  pk_df["tarih"].to_numpy())
        # ek okuma (TANI, kapı değil): @10
        p10 = B[B["evren_uye"] & B["rvol20"].notna() & B["fwd10"].notna()]
        p10 = p10[p10["tarih"].isin(kullan)]
        pk["ic_10_tani"] = (None if len(p10) < ANAHTAR["MIN_DILIM"] else
                            spearman_ic(p10["rvol20"].to_numpy(float),
                                        p10["fwd10"].to_numpy(float)))
        if ic is None:
            pk["GECTI"] = None
            pk["neden"] = "rütbe değişimi yok — IC tanımsız"
        else:
            alt = ANAHTAR["PK_CIVI"] / ANAHTAR["PK_MERTEBE"]
            ust = ANAHTAR["PK_CIVI"] * ANAHTAR["PK_MERTEBE"]
            pk["bant"] = [alt, ust]
            pk["GECTI"] = bool(ic > 0 and alt <= ic <= ust)
            pk["neden"] = None if pk["GECTI"] else (
                f"IC={ic:.4f} · beklenen işaret POZİTİF ve mertebe bandı [{alt:.4f}, {ust:.4f}]")
    S["pk"] = pk
    print(f"   PK · IC@20={pk.get('ic')} · n={pk['n']} · gün={pk['n_gun']} · "
          f"çivi={ANAHTAR['PK_CIVI']} → GEÇTİ={pk.get('GECTI')}")
    if pk.get("ci"):
        print(f"   PK CI: {pk['ci'].get('lo')} .. {pk['ci'].get('hi')}")

    if pk.get("GECTI") is not True:
        S["DUR"] = ("POZİTİF KONTROL TUTMADI (kart guard'ı) — "
                    f"IC@20={pk.get('ic')}, beklenen: pozitif ve ≈{ANAHTAR['PK_CIVI']} "
                    f"mertebesinde (×{ANAHTAR['PK_MERTEBE']} bandı). "
                    f"Ayrıntı: {pk.get('neden')}. Boru hattı geçersiz sayılır; SONRAKİ "
                    "HÜCRELER KOŞTURULMAZ ve hiçbir kart sayısı üretilmez.")
        print("\n" + "=" * 78)
        print("PK-DUR: DEFTER DURDU. Son hücreyi (H11) yine de koş — DUR nedenini taşıyan")
        print("        JSON'u basar. O JSON'u operatör talimatındaki gibi Rol-1'e ilet.")
        print("=" * 78)


# %%
# =====================================================================================
# HÜCRE H6 — shares_outstanding AS-OF → turnover21
# =====================================================================================
# KART: turnover21(t) = medyan21(hacim) / shares_outstanding(t) — EDG-016 tanımına en
# yakın QC karşılığı; sapma varsa defter BEYAN EDER.
#
# YOL MERDİVENİ (ilk çalışan kullanılır, hangisi olduğu JSON'a yazılır):
#   1) get_fundamental(semboller, "CompanyProfile.SharesOutstanding", t0, t1)   ← tercih
#   2) history(Fundamental, semboller, t0, t1) → SharesOutstanding sütunu
#   3) VEKİL: MarketCap / Price (ikisi de AYNI GÜNÜN alanları → as-of tutarlı)  ← BEYANLI
#   4) VEKİL: EarningReports.BasicAverageShares (AĞIRLIKLI ORTALAMA — EDG-016 bunu SEVİYE
#      olarak REDDEDİYOR; yalnız 1-3 yoksa, ağır beyanla)                       ← BEYANLI
#   hiçbiri yoksa → 'ölçülemedi' + kart askıya (UYDURMA VEKİL YASAK, kart kill_criteria)
#
# AS-OF NEDEN SAĞLANIYOR: QC'nin fundamental verisi GÜN GÜN teslim edilir; t günü satırı
# t günü bilinen değerdir. Meridian'ın EDGAR `filed<=t` kuralının QC karşılığı budur.
# Bu, defterin DOĞRULAYAMADIĞI bir QC belgeleme iddiasıdır — beyan olarak JSON'a girer.

if _kapi("6"):
    sids = list(S["birlesim"])
    parcalar = [sids[i:i + ANAHTAR["PARCA"]] for i in range(0, len(sids), ANAHTAR["PARCA"])]

    def _genis_uzun(df, deger_adi):
        """get_fundamental'ın GENİŞ tablosunu (satır=zaman, sütun=sembol) uzun forma çevirir.

        `stack`in imzası pandas sürümleri arasında DEĞİŞTİ (`dropna=` kimi sürümde TypeError,
        kimi sürümde ValueError atıyor). Bu yüzden ÇIPLAK `stack()` + ayrı `dropna()`
        kullanılır — her sürümde aynı sonucu verir."""
        if not hasattr(df, "columns"):
            raise RuntimeError("get_fundamental beklenen tabloyu döndürmedi")
        st = None
        for cagri in (lambda: df.stack(), lambda: df.stack(future_stack=True)):
            try:
                st = cagri()
                break
            except Exception:
                continue
        if st is None:
            raise RuntimeError("geniş tablo uzun forma çevrilemedi (stack işlemedi)")
        uzun = st.dropna().reset_index()
        if uzun.shape[1] != 3:
            raise RuntimeError(f"geniş→uzun dönüşümü {uzun.shape[1]} sütun verdi, 3 bekleniyordu")
        uzun.columns = ["tarih", "sym", deger_adi]
        return uzun

    def _yol1(syms):
        h, ad = _cagir(qb, ["get_fundamental", "GetFundamental"],
                       syms, "CompanyProfile.SharesOutstanding",
                       ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
        return _genis_uzun(h, "shares"), f"{ad}(CompanyProfile.SharesOutstanding)"

    def _yol2(syms):
        h, ad = _cagir(qb, ["history", "History"], Fundamental, syms,
                       ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"], S["res_daily"])
        uzun = _normalize_evren(h)
        if uzun.empty:
            raise RuntimeError("history(Fundamental) boş döndü")
        uzun = uzun[["tarih", "sym", "shares", "market_cap", "fiyat"]].copy()
        if uzun["shares"].notna().sum() == 0:
            if (uzun["market_cap"].notna() & uzun["fiyat"].notna()).sum() == 0:
                raise RuntimeError("history(Fundamental) ne shares ne market_cap taşıyor")
            uzun["shares"] = uzun["market_cap"] / uzun["fiyat"].replace(0, np.nan)
            return uzun[["tarih", "sym", "shares"]], f"{ad}(Fundamental) → MarketCap/Price VEKİLİ"
        return uzun[["tarih", "sym", "shares"]], f"{ad}(Fundamental).SharesOutstanding"

    def _yol3(syms):
        h, ad = _cagir(qb, ["get_fundamental", "GetFundamental"],
                       syms, "MarketCap", ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
        return _genis_uzun(h, "market_cap"), f"{ad}(MarketCap) → fiyata bölünecek VEKİL"

    def _yol4(syms):
        h, ad = _cagir(qb, ["get_fundamental", "GetFundamental"], syms,
                       "EarningReports.BasicAverageShares.ThreeMonths",
                       ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
        return (_genis_uzun(h, "shares"),
                f"{ad}(BasicAverageShares.ThreeMonths) AĞIRLIKLI ORTALAMA VEKİLİ")

    YOLLAR = [("get_fundamental(SharesOutstanding)", _yol1, None),
              ("history(Fundamental)", _yol2, None),
              ("get_fundamental(MarketCap)/fiyat", _yol3,
               "MarketCap / o günün fiyatı — ikisi de AYNI GÜNÜN alanı, as-of tutarlı; "
               "ama hisse sayımının kendisi değil TÜRETİLMİŞİDİR (fiyat gürültüsü taşır)"),
              ("get_fundamental(BasicAverageShares)", _yol4,
               "AĞIRLIKLI ORTALAMA hisse — EDG-016 bunu SEVİYE olarak REDDEDER; yalnız "
               "diğer yollar yokken, ağır beyanla kullanıldı")]

    secilen_yol, parcalar_ok, hatalar = None, [], []
    for ad, fn, sapma_notu in YOLLAR:
        try:
            deneme, gercek = fn([S["sym_kutugu"][s] for s in parcalar[0]])
            if deneme is None or len(deneme) == 0:
                hatalar.append(f"{ad}: boş")
                continue
            secilen_yol = (ad, fn, sapma_notu, gercek)
            parcalar_ok.append(deneme)
            break
        except Exception as e:
            hatalar.append(f"{ad}: {type(e).__name__}: {e}")

    if secilen_yol is None:
        S["DUR"] = ("shares_outstanding AS-OF ALINAMADI — denenen tüm yollar başarısız. "
                    "Kart kill_criteria: 'defter evren/tanım sapmasını kapatamıyorsa → "
                    "ölçülemedi beyanı, kart askıya (uydurma vekil YASAK)'. "
                    f"Denemeler: {' | '.join(hatalar)}")
        _olculemedi("shares_outstanding_as_of", S["DUR"])
    else:
        ad, fn, sapma_notu, gercek = secilen_yol
        S["api_yolu"]["shares"] = gercek
        if sapma_notu:
            _sapma("shares_outstanding", ad, sapma_notu)
        if "VEKİL" in gercek and not sapma_notu:
            _sapma("shares_outstanding", gercek,
                   "seçilen yol hisse sayımını doğrudan değil TÜRETEREK verdi (beyan)")
        for pi, p in enumerate(parcalar[1:], start=1):
            try:
                d, _ = fn([S["sym_kutugu"][s] for s in p])
                if d is not None and len(d):
                    parcalar_ok.append(d)
            except Exception as e:
                _uyar(f"shares parça {pi}: {type(e).__name__}: {e}")
            if pi % 4 == 0 or pi == len(parcalar) - 1:
                print(f"   shares {pi+1}/{len(parcalar)} parça", flush=True)

        SH = pd.concat(parcalar_ok, ignore_index=True)
        SH["sid"] = [_sid(x) for x in SH["sym"]]
        SH["tarih"] = pd.to_datetime(SH["tarih"]).dt.normalize()
        if "market_cap" in SH.columns and "shares" not in SH.columns:
            SH = SH.merge(S["barlar"][["sid", "tarih", "close"]], on=["sid", "tarih"], how="left")
            SH["shares"] = SH["market_cap"] / SH["close"].replace(0, np.nan)
        SH = SH[["sid", "tarih", "shares"]].dropna()
        SH = SH[SH["shares"] > 0].drop_duplicates(subset=["sid", "tarih"], keep="last")

        B = S["barlar"]
        B = B.merge(SH, on=["sid", "tarih"], how="left")
        # AS-OF: yalnız İLERİ doldurma — son BİLİNEN değer taşınır, GERİYE BAKIŞ YOK.
        # Kaynak tarihi ayrıca taşınır ki "bu sayı kaç gün eski" ölçülebilsin.
        B["_kaynak_tarih"] = B["tarih"].where(B["shares"].notna())
        B["shares"] = B.groupby("sid")["shares"].ffill()
        B["shares_asof_tarih"] = B.groupby("sid")["_kaynak_tarih"].ffill()
        B["shares_bayatlik_gun"] = (B["tarih"] - B["shares_asof_tarih"]).dt.days
        # BAYATLIK BEKÇİSİ (EDG-016'nın SCHW dersi): son bilinen kayıt 200 günden eskiyse
        # o hücre ÖLÇÜLEMEZ. Bekçi olmasa boşluğun BAŞINDAKİ hisse sayımı boşluk boyunca
        # taşınır ve uydurma turnover üretirdi.
        bayat = B["shares_bayatlik_gun"] > 200
        n_bayat = int((bayat & B["shares"].notna()).sum())
        B.loc[bayat, "shares"] = np.nan
        B = B.drop(columns=["_kaynak_tarih"])

        B["turnover21"] = (B["med_hacim21"].astype("float64") / B["shares"])
        # FİZİKSEL BEKÇİ (EDG-016): ima edilen devir > 1.0 fiziksel olarak imkânsız
        # (bir günde tüm hisse senedinin medyan 21g hacmi kadar el değiştirmesi ölçek hatası)
        fiziksel = B["turnover21"] > 1.0
        n_fiziksel = int((fiziksel & B["turnover21"].notna()).sum())
        B.loc[fiziksel, "turnover21"] = np.nan
        B = B.drop(columns=[c for c in ("shares_asof_tarih",) if c in B.columns])
        B["turnover21"] = B["turnover21"].astype("float32")
        S["barlar"] = B
        S.setdefault("bellek_mb", {})["H6_turnoverli"] = round(
            B.memory_usage(deep=True).sum() / 1e6, 1)
        S["shares_muhasebe"] = {
            "yol": gercek,
            "shares_kayit_satir": int(len(SH)),
            "shares_dolu_hucre": int(B["shares"].notna().sum()),
            "bayatlik_bekcisi_kapatti": n_bayat,
            "bayatlik_esik_gun": 200,
            "fiziksel_bekci_kapatti": n_fiziksel,
            "turnover21_dolu_hucre": int(B["turnover21"].notna().sum()),
            "as_of_beyani": ("QC fundamental verisi gün gün teslim edilir; t satırı t günü "
                             "bilinen değer sayıldı. Bu, QC'nin belgelediği bir özelliktir ve "
                             "bu defter tarafından BAĞIMSIZ DOĞRULANMADI — beyan."),
        }
        print("   TURNOVER HAZIR ·", json.dumps(S["shares_muhasebe"], ensure_ascii=False))


# %%
# =====================================================================================
# HÜCRE H7 — KESİT + ÜST-%20 DİLİM + AYNI-GÜN EVREN TABANI
# =====================================================================================
# EDG-016 ile birebir:
#   · gün kesiti = o gün EVREN ÜYESİ ve turnover21 tanımlı semboller, kesit >= MIN_KESIT
#   · dilim      = gün içi turnover21 yüzdelik rütbesi > 0.80
#   · taban      = AYNI GÜN evren ortalaması (o gün ileri getirisi tanımlı TÜM evren üyeleri)
# TEK FARK: burada evren delist-DAHİL. Kartın ölçmek istediği fark tam olarak budur.

if _kapi("7"):
    B = S["barlar"]
    V = B[B["evren_uye"] & B["turnover21"].notna()].copy()
    kesit = V.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    V = V[V["tarih"].isin(kullan)].copy()
    V["to_pct"] = V.groupby("tarih")["turnover21"].rank(pct=True, method="first")
    V["ust"] = V["to_pct"] > (1.0 - ANAHTAR["UST_PCT"])

    # taban: aynı-gün evren ortalaması — TÜM evren üyeleri (turnover şartı YOK, EDG-016 ile aynı)
    taban = {}
    for h in ANAHTAR["UFUKLAR"]:
        t = B[B["evren_uye"]][["tarih", f"fwd{h}"]].dropna()
        taban[h] = t.groupby("tarih")[f"fwd{h}"].mean()
    S["taban"] = taban
    S["V"] = V

    kesit_kul = kesit[kesit >= ANAHTAR["MIN_KESIT"]]
    S["kesit_muhasebe"] = {
        "gozlem_gunu_toplam": int(B[B["evren_uye"]]["tarih"].nunique()),
        "kesit_yeterli_gun": int(len(kullan)),
        "min_kesit": ANAHTAR["MIN_KESIT"],
        "kesit_buyuklugu": {"medyan": float(kesit_kul.median()),
                            "min": int(kesit_kul.min()), "maks": int(kesit_kul.max())},
        "tarih_araligi": [str(V["tarih"].min().date()), str(V["tarih"].max().date())],
        "n_satir": int(len(V)), "n_sembol": int(V["sid"].nunique()),
        "turnover21_dagilimi": {str(q): float(V["turnover21"].quantile(q))
                                for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
        "dilim_satir": int(V["ust"].sum()),
        "dilim_sembol": int(V.loc[V["ust"], "sid"].nunique()),
    }
    print("   KESİT ·", json.dumps(S["kesit_muhasebe"], ensure_ascii=False))


# %%
# =====================================================================================
# HÜCRE H8 — ÖLÇÜM: ÜST-%20 DİLİM EVREN-FAZLASI + 21g BLOK CI + MALİYET
# =====================================================================================
# Kartın TEK kayıtlı hücresi: qc_turnover_ust20_fazlasi (K+=1).
# Maliyet: sabit bir sayıdır → CI aynı sabitle ötelenir (bootstrap yeniden koşulmaz,
# cebirsel özdeş — EDG-016 ile aynı okuma). Kart modeli 10bps; 20bps BEYANLI DUYARLILIK.

if _kapi("8"):
    V = S["V"]
    taban = S["taban"]
    olcum, maliyet, fazla_kayit = {}, {}, {}
    for h in ANAHTAR["UFUKLAR"]:
        sub = V[V["ust"]][["tarih", "sid", f"fwd{h}"]].dropna(subset=[f"fwd{h}"])
        base = sub["tarih"].map(taban[h])
        ok = base.notna().to_numpy()
        y = sub[f"fwd{h}"].to_numpy(float)[ok]
        b = base.to_numpy(float)[ok]
        d = sub["tarih"].to_numpy()[ok]
        fazla = y - b
        fazla_kayit[h] = (fazla, d, sub["sid"].to_numpy()[ok])

        gun_ort = pd.Series(fazla, index=pd.Index(d, name="tarih")).groupby(level=0).mean()
        olcum[str(h)] = {
            "tanim": (f"o gün turnover21 kesit üst %{int(ANAHTAR['UST_PCT']*100)} dilimi; "
                      f"taban = AYNI GÜN evren ortalaması (delist DAHİL evren)"),
            "n_sembol_gun": int(len(fazla)),
            "n_gun": int(len(gun_ort)),
            "n_sembol": int(pd.Series(sub["sid"].to_numpy()[ok]).nunique()),
            "dilim_turnover21_medyan": float(V.loc[V["ust"], "turnover21"].median()),
            "ham_getiri": gun_blok_bootstrap_ort(y, d),
            "evren_fazlasi": gun_blok_bootstrap_ort(fazla, d),
            "evren_fazlasi_ikincil_gun_serisi_CI": blok_bootstrap_ci(
                gun_ort.to_numpy(), blok=ANAHTAR["BLOK"]),
            "taban_ort": float(np.mean(b)),
        }
        print(f"   @{h} · n={len(fazla)} gün={len(gun_ort)} · fazla ort="
              f"{olcum[str(h)]['evren_fazlasi']['ort']} "
              f"CI[{olcum[str(h)]['evren_fazlasi']['lo']}, "
              f"{olcum[str(h)]['evren_fazlasi']['hi']}]", flush=True)

        blok = olcum[str(h)]["evren_fazlasi"]
        satirlar = {}
        for etiket, bps in (("kart_modeli_10bps", ANAHTAR["MALIYET_BPS"]),
                            ("duyarlilik_20bps", ANAHTAR["MALIYET_BPS_DUYARLILIK"])):
            c = bps / 10000.0
            satirlar[etiket] = {
                "bps": bps,
                "brut": blok["ort"],
                "net": (None if blok["ort"] is None else blok["ort"] - c),
                "net_ci": (None if blok["lo"] is None else
                           {"lo": blok["lo"] - c, "hi": blok["hi"] - c, "seviye": 0.95,
                            "sifir_disinda": bool((blok["lo"] - c) > 0 or (blok["hi"] - c) < 0)}),
                "beyan": "maliyet SABİT → CI aynı sabitle ötelendi (bootstrap yeniden koşulmadı)",
            }
        maliyet[str(h)] = satirlar
    S["olcum"] = olcum
    S["maliyet"] = maliyet
    S["fazla_kayit"] = fazla_kayit


# %%
# =====================================================================================
# HÜCRE H9 — ALT-DÖNEM BETİMLEYİCİ TABLO (CI YOK)
# =====================================================================================
# EDG-016 çekince Ç2: alt-dönem kararlılığı kartın grid'inde YOKTUR. Bu tablo BETİMLEYİCİ:
# CI BİLEREK hesaplanmaz — CI'lı sınansaydı K çarpılırdı (kart disiplini). Sayılar Rol-1'e
# bilgi olarak gider, hüküm bacağı DEĞİLDİR.

if _kapi("9"):
    alt = {"beyan": ("BETİMLEYİCİ — kart parameter_grid'inde alt-dönem bacağı YOK; CI "
                     "BİLEREK hesaplanmadı (K çarpılmasın). Hüküm bacağı değildir."),
           "ufuklar": {}}
    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, _sid_ar = S["fazla_kayit"][h]
        yil = pd.DatetimeIndex(d).year
        tab = {}
        for y in sorted(set(yil.tolist())):
            m = (yil == y)
            tab[str(y)] = {"n": int(m.sum()),
                           "n_gun": int(pd.Series(d[m]).nunique()),
                           "fazla_ort": float(np.mean(fazla[m])) if m.sum() else None,
                           "fazla_medyan": float(np.median(fazla[m])) if m.sum() else None,
                           "pozitif_oran": float((fazla[m] > 0).mean()) if m.sum() else None}
        alt["ufuklar"][str(h)] = tab
        print(f"   @{h} alt-dönem:",
              {k: round(v["fazla_ort"], 5) if v["fazla_ort"] is not None else None
               for k, v in tab.items()})
    S["alt_donem"] = alt


# %%
# =====================================================================================
# HÜCRE H10 — EVREN / DELİST MUHASEBESİ · SURVIVORSHIP GÖSTERGELERİ (CI YOK)
# =====================================================================================
# KARTIN ASIL SORUSU BURADA GÖRÜNÜR HÂLE GELİR: dilimdeki SONRADAN-DELİST olan isimler
# ne kadar yer tutuyor ve fazlaya ne katıyor?
#   · tum                    → kartın kayıtlı hücresi (CI'sı H8'de)
#   · yalniz_hayatta_kalanlar→ EDG-016'nın gördüğü dünyanın QC içindeki karşılığı
#   · yalniz_sonradan_delist → EDG-016'nın HİÇ göremediği kuyruk
#   · survivorship_primi_vekili = (yalnız hayatta kalanlar) − (tümü)
# CI YOK: bunlar kartın kayıtlı hücresi DEĞİL, BETİMLEYİCİ ayrıştırmadır (K çarpılmasın).
# Ayrıca: delist yüzünden ileri getirisi ÖLÇÜLEMEYEN satırlar sayılır ve 'son fiyattan
# tasfiye' duyarlılığı ayrı bir satır olarak okunur (yine CI'sız).

if _kapi("10"):
    V = S["V"]
    dl = S["delist_sid"]
    dm = {
        "yontem": S["delist_yontemi"],
        "beyan": ("BETİMLEYİCİ ayrıştırma — CI hesaplanmadı (kartın kayıtlı hücresi TEK: "
                  "üst-%20 dilim fazlası). Hüküm bacağı değildir."),
        "evren_birlesim_sembol": int(len(S["birlesim"])),
        "bar_donen_sembol": int(S["barlar"]["sid"].nunique()),
        "delist_vekili_sembol": int(len(dl)),
        "delist_vekili_pay": (float(len(dl)) / max(1, S["barlar"]["sid"].nunique())),
        "aylik_uyelik_muhasebesi": {"ay_sayisi": len(S["aylar"]),
                                    "ilk_ay": str(S["aylar"][0].date()),
                                    "son_ay": str(S["aylar"][-1].date())},
        "kesit_delist_satir": int(V["sid"].isin(dl).sum()),
        "kesit_satir": int(len(V)),
        "dilim_delist_satir": int((V["ust"] & V["sid"].isin(dl)).sum()),
        "dilim_satir": int(V["ust"].sum()),
        "dilim_delist_sembol": int(V.loc[V["ust"] & V["sid"].isin(dl), "sid"].nunique()),
        "delist_fwd_olculemeyen_satir": S["delist_fwd_dusen"],
        "ufuklar": {},
    }
    dm["dilim_delist_satir_pay"] = (dm["dilim_delist_satir"] / max(1, dm["dilim_satir"]))
    dm["delist_dilime_yogunlasiyor_mu"] = {
        "dilimdeki_delist_payi": dm["dilim_delist_satir_pay"],
        "kesitteki_delist_payi": dm["kesit_delist_satir"] / max(1, dm["kesit_satir"]),
        "okuma": ("dilim payı kesit payından BÜYÜKSE yüksek-turnover dilimi delist edilen "
                  "isimleri fazladan topluyor demektir — EDG-016'nın Ç1 çekincesinin "
                  "doğrudan göstergesi (sayı; yorum Rol-1'de)"),
    }

    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, sid_ar = S["fazla_kayit"][h]
        is_dl = pd.Series(sid_ar).isin(dl).to_numpy()
        def _bet(mask):
            if mask.sum() == 0:
                return {"n": 0, "ort": None, "neden": "satır yok"}
            return {"n": int(mask.sum()),
                    "n_sembol": int(pd.Series(sid_ar[mask]).nunique()),
                    "ort": float(np.mean(fazla[mask])),
                    "medyan": float(np.median(fazla[mask])),
                    "pozitif_oran": float((fazla[mask] > 0).mean())}
        tum = _bet(np.ones(len(fazla), dtype=bool))
        hay = _bet(~is_dl)
        dlt = _bet(is_dl)
        dm["ufuklar"][str(h)] = {
            "tum": tum, "yalniz_hayatta_kalanlar": hay, "yalniz_sonradan_delist": dlt,
            "survivorship_primi_vekili": (
                None if (hay["ort"] is None or tum["ort"] is None) else hay["ort"] - tum["ort"]),
            "okuma": ("survivorship_primi_vekili > 0 → delist isimleri dilimin fazlasını "
                      "AŞAĞI çekiyor, yani sağkalan-evrende ölçülen sayı yukarı çarpıktı. "
                      "SAYIDIR, hüküm değildir."),
        }
        # duyarlılık: delist isminde son kapanıştan tasfiye varsayımıyla kapatılmış fwd
        sut = f"fwd{h}_delist_kapatilmis"
        if sut in V.columns:
            sub = V[V["ust"]][["tarih", "sid", sut]].dropna(subset=[sut])
            base = sub["tarih"].map(S["taban"][h])
            m2 = base.notna().to_numpy()
            fz2 = sub[sut].to_numpy(float)[m2] - base.to_numpy(float)[m2]
            dm["ufuklar"][str(h)]["duyarlilik_delist_son_fiyattan_tasfiye"] = {
                "n": int(len(fz2)), "ort": (float(np.mean(fz2)) if len(fz2) else None),
                "beyan": ("delist isminin son h günü için ileri getiri BAR YOK diye ölçülemez; "
                          "bu satır o boşluğu 'son kapanıştan tasfiye' varsayımıyla doldurur. "
                          "VARSAYIMDIR (gerçek tasfiye fiyatı bu defterde bilinmiyor), CI YOK, "
                          "hüküm bacağı DEĞİL — kayıtlı hücrenin eksik-veri ele alışı duyarlılığı."),
            }
    S["delist_muhasebe"] = dm
    print("   delist payı — dilim:", round(dm["dilim_delist_satir_pay"], 5),
          "kesit:", round(dm["delist_dilime_yogunlasiyor_mu"]["kesitteki_delist_payi"], 5))
    for h in ANAHTAR["UFUKLAR"]:
        u = dm["ufuklar"][str(h)]
        print(f"   @{h} tüm={u['tum']['ort']} hayatta={u['yalniz_hayatta_kalanlar']['ort']} "
              f"delist={u['yalniz_sonradan_delist']['ort']} "
              f"prim_vekili={u['survivorship_primi_vekili']}")


# %%
# =====================================================================================
# HÜCRE H11 — TEK JSON BLOĞU  (ŞEMA: cikti_semasi.md)
# =====================================================================================
# BU HÜCRE DUR HÂLİNDE DE KOŞAR — PK tutmadıysa bile operatörün elinde iletilecek bir
# kanıt olur. JSON'da HÜKÜM YOKTUR: SUCCESS/KILL/anlamlı kelimeleri geçmez.

def _json_guvenli(o):
    import numpy as _np
    if isinstance(o, dict):
        return {str(k): _json_guvenli(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_json_guvenli(v) for v in o]
    if isinstance(o, (_np.integer,)):
        return int(o)
    if isinstance(o, (_np.floating,)):
        f = float(o)
        return None if (f != f or f in (float("inf"), float("-inf"))) else f
    if isinstance(o, (_np.bool_,)):
        return bool(o)
    if isinstance(o, float):
        return None if (o != o or o in (float("inf"), float("-inf"))) else o
    if isinstance(o, (int, str, bool)) or o is None:
        return o
    try:
        import pandas as _pd
        if isinstance(o, (_pd.Timestamp, datetime)):
            return str(o)
        if isinstance(o, _pd.Series):
            return _json_guvenli(o.to_dict())
    except Exception:
        pass
    return str(o)


CIKTI = {
    "kart": "EDG-2026-021",
    "aile": "qc_delist_dogrulama",
    "defter_surumu": "1.0",
    "defter_sha256": None,
    "defter_sha256_neden": ("yapıştırılan defter kendi kaynağını okuyamaz — repo "
                            "dosyasının (research/qc_dogrulama/qc_defter_021.py) sha256'sı "
                            "hüküm yazılırken REPO tarafında alınır"),
    "rol": ("ölçüm defteri — SAYI üretir, HÜKÜM VERMEZ. Eşik içermez; kill karşılığı yoktur. "
            "Hüküm Rol-1'de."),
    "kosum": {
        "zaman_utc": str(datetime.utcnow()) + "Z",
        "ortam": "QuantConnect Research (QuantBook)",
        "api_yolu": S.get("api_yolu"),
        "determinizm_sinamasi": S.get("determinizm_sinamasi"),
        "bellek_mb": S.get("bellek_mb"),
    },
    "anahtarlar": {k: (str(v) if isinstance(v, datetime) else v) for k, v in ANAHTAR.items()},
    "DUR": S.get("DUR"),
    "pozitif_kontrol": S.get("pk"),
    "evren": {
        "beyan": (f"aylık yeniden-örneklenen dolar-hacim üst-{ANAHTAR['EVREN_N']} — DELİST DAHİL "
                  "(evren geçmiş bir günün QC universe anlık görüntüsünden kurulur; o gün "
                  "borsada olan, bugün olmayan isimler İÇERİDEDİR)"),
        "spx_uyelik_denemesi": S.get("spx_uyelik_denemesi"),
        "ay_muhasebesi": S.get("ay_muhasebe"),
        "bar_muhasebesi": S.get("bar_muhasebe"),
        "kesit_muhasebesi": S.get("kesit_muhasebe"),
        "shares_muhasebesi": S.get("shares_muhasebe"),
    },
    "tanimlar": {
        "turnover21": "medyan21(hacim) / shares_outstanding(as-of t)",
        "rvol20": "hacim(t) / SMA20(hacim)[t] — payda BUGÜNÜ İÇERİR (meridian.indicators)",
        "mom21": "close(t)/close(t-21) - 1 (düzeltilmiş kapanış)",
        "dilim": f"gün içi turnover21 yüzdelik rütbesi > {1 - ANAHTAR['UST_PCT']}",
        "taban": "AYNI GÜN evren ortalaması (o gün ileri getirisi tanımlı tüm evren üyeleri)",
        "fwd_h": "close(t+h)/close(t) - 1 (düzeltilmiş kapanış)",
        "ci": (f"{ANAHTAR['BLOK']} ardışık gözlem günü blok-bootstrap, %95, "
               f"B={ANAHTAR['BOOT']} (IC: {ANAHTAR['BOOT_IC']}), tohum={ANAHTAR['TOHUM']} · "
               "HEADLINE satır-ağırlıklı gün-blok şeması (EDG-016 ile aynı); ikincil okuma "
               "gün-ortalaması serisine uygulanmış kanonik blok_bootstrap_ci (tohum 11)"),
        "maliyet": (f"kart cost_model {ANAHTAR['MALIYET_BPS']}bps tek-yön; "
                    f"{ANAHTAR['MALIYET_BPS_DUYARLILIK']}bps BEYANLI DUYARLILIK"),
        "K_beyani": ("kart grid'i TEK katman (K+=1): qc_turnover_ust20_fazlasi. Ufuk 10/20 "
                     "kartın horizon alanıdır, K çarpanı değildir. Alt-dönem tablosu ve "
                     "delist ayrıştırması BETİMLEYİCİ'dir ve CI TAŞIMAZ."),
        "hacim_bazi": S.get("hacim_bazi"),
    },
    "tanim_sapmalari": S.get("tanim_sapmalari"),
    "olcum": {"ust20_evren_fazlasi": S.get("olcum")},
    "maliyet": S.get("maliyet"),
    "alt_donem_betimleyici": S.get("alt_donem"),
    "delist_muhasebesi": S.get("delist_muhasebe"),
    "kiyas_notu": {
        "edg_016": {"ust20_evren_fazlasi_10": 0.0031, "ust20_evren_fazlasi_20": 0.00648,
                    "net_10bps_20": 0.00548,
                    "kaynak": "research/olcumler/wp2_olcum/RAPOR_016.md (sağkalan evren, full_251)"},
        "beyan": ("EDG-016 sayıları BURADA HESAPLANMADI, kıyas kolaylığı için taşındı. "
                  "İki ölçüm FARKLI evrende yapıldı (full_251 sağkalan vs QC delist-dahil "
                  f"üst-{ANAHTAR['EVREN_N']}); fark yalnız survivorship'e atfedilemez — "
                  "evren/tanım sapmaları `tanim_sapmalari` altında."),
    },
    "uyarilar": S.get("uyarilar"),
    "olculemedi": S.get("olculemedi"),
}

print("\n" + "=" * 78)
print("EDG-2026-021 · SONUÇ JSON")
print("KOPYALANACAK ŞEY: aşağıdaki iki işaret ARASINDAKİ metin (işaretler DAHİL DEĞİL).")
print("kaydet: research/olcumler/qc_dogrulama/sonuc_021.json")
print("=" * 78)
print("<<<SONUC_021_JSON_BASLANGIC>>>")
print(json.dumps(_json_guvenli(CIKTI), ensure_ascii=False, indent=2, sort_keys=False))
print("<<<SONUC_021_JSON_SON>>>")
print("=" * 78)
print("JSON SONU · DUR =", S.get("DUR"))
