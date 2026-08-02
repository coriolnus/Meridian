"""EDG-2026-021 · QC DELİST-DAHİL DOĞRULAMA DEFTERİ · v2 (mimari yeniden yazım)

Kart : research/cards/EDG-2026-021-qc-delist-dogrulama.yaml (eşikler DEĞİŞMEDİ)
İkiz : EDG-2026-016 · Zemin: research/qc_dogrulama/QC_API_ZEMIN_GERCEGI.md (canlı ÖLÇÜM)
Koşum: OPERATOR_TALIMATI.md · Çıktı şeması ve tam gerekçe: cikti_semasi.md

v1 H2'de DURdu: FREE hesapta history(Fundamental)/history(CoarseFundamental) BOŞ dönüyor.
O yollar ÖLÜ ve çıkarıldı. v2 TEK KAYNAK: add_universe(secici) + universe_history(u,t0,t1)
→ Series, MultiIndex(evren-sembolü, zaman), her değer list[Fundamental]. Evren + fiyat +
hacim + as-of hisse AYNI çağrıdan; her gün kendi kesiti → İLERİ-BAKIŞ YOK, sağkalan
süzgeci YOK. Ayrı qb.history YALNIZ ölçülmüş gerekçeyle: H3 fiyat çapraz-kontrolü ve
(yalnız o kontrol paneli yetersiz bulursa) düzeltilmiş-kapanış tamiri.

YAPAR: sayı üretir. YAPMAZ: eşik koymaz, hüküm vermez (JSON'da SUCCESS/KILL yok); tek
istisna kartın guards maddesinin emrettiği pozitif-kontrol KAPISI (H5).
UYDURMA YASAĞI: ölçülemeyen her büyüklük None + `neden`; varsayılanla doldurma yok.

QC dosya başına 64.000 KARAKTER sınırı koyar → .py olarak yüklenir, notebook'ta tek satır:
    exec(open('qc_defter_021.py').read())
`# %%` hücre sınırıdır; durum tek `S` sözlüğünde, her hücre `_kapi()` ile kendini kapatır.

HÜCRELER: H0 ayarlar · H1 QuantBook+bar yardımcısı · H1b ölçüm araçları+determinizm ·
H2 PANEL (universe_history yıl yıl) · H3 fiyat çapraz-kontrolü · H4 öznitelikler+süreklilik
bekçileri+delist vekili · H5 POZİTİF KONTROL (KAPI) · H6 turnover21 · H7 kesit+dilim+taban ·
H8 ÖLÇÜM (fazla+CI+maliyet) · H9 alt-dönem · H10 delist muhasebesi · H11 JSON
"""

# %%
# --- H0 — AYARLAR, KAYNAK-KORUMA ANAHTARLARI, DURUM ---------------------------------
# Operatör uzun koşumda YALNIZ burayı daraltır; daraltılmış koşum JSON'a kendini yazar
# (anahtarlar + tanim_sapmalari) ve kart hükmünü TAŞIMAZ.

from datetime import datetime, timedelta

ANAHTAR = {
    # --- kartın beyanı (DEĞİŞTİRME: değişirse koşum kart-dışı olur) ---
    "PENCERE_BAS":  datetime(2020, 8, 1),
    "PENCERE_SON":  datetime(2026, 7, 28),
    "EVREN_N":      250,          # ÖLÇÜM evreni: günlük dolar-hacim üst-N
    "UST_PCT":      0.20,         # kayıtlı dilim: turnover üst %20
    "UFUKLAR":      (10, 20),

    # --- EDG-016 ile ortak ölçüm sabitleri (ikizlik şartı) ---
    "BLOK":         21,           # blok bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ
    "BOOT":         2000,
    "BOOT_IC":      600,
    "TOHUM":        20260801,
    "MIN_KESIT":    50,           # kesiti bundan az olan gün kullanılmaz
    "MIN_DILIM":    30,           # bir ölçümün asgari satır sayısı
    "MALIYET_BPS":  10.0,
    "MALIYET_BPS_DUYARLILIK": 20.0,
    "RVOL_PENCERE": 20,           # rvol20 = hacim / SMA20(hacim); payda BUGÜNÜ İÇERİR
    "TURNOVER_PENCERE": 21,       # medyan21(hacim)

    # --- pozitif kontrol kapısı (kart guards) ---
    "PK_CIVI":      0.064,        # yerel çivi (EDG-016 turunda 0.0642 ölçüldü)
    "PK_MERTEBE":   5.0,          # |IC| çivinin 1/5'i ile 5 katı arasında olmalı

    # --- boru hattı sabitleri (hüküm eşiği DEĞİL) ---
    "PANEL_CARPANI": 2,           # panel = üst-(EVREN_N×carpan); fazlası TAMPON (bkz. H2)
    "SPAN_TOLERANS": 2.0,         # k satırlık pencere en çok k×tolerans TAKVİM günü yayılır
    "SHARES_BAYAT_GUN": 200,      # as-of hisse kaydı bundan eskiyse hücre ölçülemez
    "TURNOVER_TAVAN": 1.0,        # ima edilen devir > 1 fiziksel olarak imkânsız
    "CAPRAZ_SEMBOL": 6,           # H3 çapraz-kontrol örneklemi
    "CAPRAZ_TOL":    0.001,       # günlük getiri farkı bunu aşarsa "sapan gün"
    "CAPRAZ_MAKS_ORAN": 0.005,    # sapan gün oranı bunu aşarsa panel serisi YETMEZ
    "CAPRAZ_BUYUK_TOL": 0.02,     # bu boyda TEK fark bile yapısal (bölünme) → panel YETMEZ
    "DELIST_TAMPON_GUN": 10,      # panel sonundan bu kadar önce biten isim = çıkış adayı

    # --- KAYNAK KORUMA — varsayılanlar sınırsızdır ---
    "YIL_LIMIT":    None,         # None = tüm yıl dilimleri; sayı → İLK n dilim
    "PARCA":        50,           # history çağrılarında sembol parça büyüklüğü
}

S = {"DUR": None, "uyarilar": [], "olculemedi": [], "tanim_sapmalari": [], "api_yolu": {}}


def _kapi(ad):
    """Hücre kapısı: S['DUR'] doluysa hücre KOŞMAZ."""
    if S["DUR"]:
        print(f"[H{ad}] KOŞTURULMADI — DUR: {S['DUR']}")
        return False
    print(f"[H{ad}] başlıyor...", flush=True)
    return True


def _uyar(m):
    S["uyarilar"].append(m)
    print(f"   UYARI: {m}", flush=True)


def _sapma(alan, ne, neden):
    """Kart tanımından SAPMA kaydı → JSON tanim_sapmalari (YASA: beyan)."""
    S["tanim_sapmalari"].append({"alan": alan, "kullanilan": ne, "neden": neden})
    print(f"   TANIM SAPMASI [{alan}] → {ne} · {neden}", flush=True)


def _olculemedi(alan, neden):
    S["olculemedi"].append({"alan": alan, "neden": neden})
    print(f"   ÖLÇÜLEMEDİ [{alan}] · {neden}", flush=True)


print("H0 tamam ·", ANAHTAR["PENCERE_BAS"].date(), "→", ANAHTAR["PENCERE_SON"].date(),
      "| ölçüm evreni üst-N:", ANAHTAR["EVREN_N"], "| panel üst-N:",
      ANAHTAR["EVREN_N"] * ANAHTAR["PANEL_CARPANI"], "| YIL_LIMIT:", ANAHTAR["YIL_LIMIT"])


# %%
# --- H1 — KÜTÜPHANELER, QuantBook, BAR-ÇEKME YARDIMCISI -----------------------------
# API adları TAHMİN DEĞİL — zemin sondası snake_case yüzeyi canlıda doğruladı; v1'in
# "adlar merdiveni" savunması bu yüzden KALDIRILDI (ölü koddu).

if _kapi("1"):
    import gc
    import json

    import numpy as np
    import pandas as pd

    from AlgorithmImports import *
    S["api_yolu"]["import"] = "AlgorithmImports"

    RES_DAILY = getattr(Resolution, "DAILY", None) or getattr(Resolution, "Daily")
    S["api_yolu"]["Resolution"] = "DAILY"

    qb = QuantBook()
    S["api_yolu"]["quantbook"] = "QuantBook()"
    try:
        qb.set_start_date(ANAHTAR["PENCERE_BAS"])
        qb.set_end_date(ANAHTAR["PENCERE_SON"])
        S["api_yolu"]["tarih_baglami"] = "set_start_date/set_end_date"
    except Exception as e:
        S["api_yolu"]["tarih_baglami"] = f"uygulanamadı ({type(e).__name__})"
        _uyar("QuantBook tarih bağlamı kurulamadı — sembol çözümü ortam varsayılanıyla")

    _SID_HAVUZ = {}

    def _sid(sym):
        """Zamandan bağımsız kimlik — ticker DEĞİL (delist sonrası yeniden kullanılır)."""
        try:
            s = str(sym.id)
        except Exception:
            s = str(sym)
        return _SID_HAVUZ.setdefault(s, s)

    def _sut(df, *adaylar):
        """Sütun adını normalize ederek bulur (küçük harf, _ ve . atılmış)."""
        norm = {str(c).lower().replace("_", "").replace(".", ""): c for c in df.columns}
        for a in adaylar:
            k = a.lower().replace("_", "").replace(".", "")
            if k in norm:
                return norm[k]
        return None

    def _bar_cek(semboller, t0, t1):
        """qb.history → düz tablo (sid, tarih, close_h). Dönüş: (df|None, neden|None)."""
        try:
            h = qb.history(list(semboller), t0, t1, RES_DAILY)
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
        if h is None or not hasattr(h, "columns") or len(h) == 0:
            return None, "boş döndü"
        c = _sut(h, "close")
        if c is None:
            return None, f"close sütunu yok ({list(h.columns)[:6]})"
        adlar = [str(x).lower() if x is not None else "" for x in (h.index.names or [])]
        i_s = next((i for i, n in enumerate(adlar) if "symbol" in n), None)
        i_t = next((i for i, n in enumerate(adlar) if "time" in n or "date" in n), None)
        if i_s is None or i_t is None:
            return None, f"indeks düzeni tanınmadı: {list(h.index.names or [])}"
        out = pd.DataFrame({
            "sid": [_sid(s) for s in h.index.get_level_values(i_s)],
            "tarih": pd.to_datetime(h.index.get_level_values(i_t)).normalize(),
            "close_h": pd.to_numeric(h[c], errors="coerce").to_numpy(dtype="float64"),
        }).dropna(subset=["close_h"])
        return (out if len(out) else None), (None if len(out) else "satır kalmadı")

    print("   API:", json.dumps(S["api_yolu"], ensure_ascii=False))


# %%
# --- H1b — BAĞIMSIZ ÖLÇÜM ARAÇLARI (ithal edilmez, KOPYA taşınır) -------------------
# Kart guard'ı: deterministik (sabit tohum), tek dosya, DIŞ BAĞIMLILIKSIZ.
# gun_blok_bootstrap_ort ≡ ortak.py::mean_block_boot → HEADLINE · spearman_ic ≡ analytics.py

if _kapi("1b"):

    def gun_blok_bootstrap_ort(y, gunler, n_boot=None, blok=None, tohum=None, seviye=0.95):
        """21 ardışık GÜN bloğu bootstrap, ORTALAMA — kesitsel bağımlılık + örtüşen ileri
        getirilerin seri korelasyonu birlikte taşınır (ortak.mean_block_boot özdeşi)."""
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
                    "neden": f"gözlem günü {nd} < blok*3 ({blok * 3})"}
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
            "n": n, "n_gun": nd, "ort": float(y.mean()), "medyan": float(np.median(y)),
            "std": float(np.std(y, ddof=1)), "pozitif_oran": float((y > 0).mean()),
            "lo": lo, "hi": hi, "seviye": seviye, "sifir_disinda": bool(lo > 0 or hi < 0),
            "blok": int(blok), "B": int(n_boot), "B_gecerli": int(len(vals)),
            "atlanan": int(atlanan), "tohum": int(tohum), "n_sayi_olmayan_dusen": n_dusen,
            "yontem": f"gün-blok (moving) bootstrap · birim={blok} ardışık gün",
            "beyan": "sifir_disinda ARİTMETİK: aralık 0'ı kapsıyor mu — hüküm DEĞİL",
            "neden": None,
        }

    def _rank_avg(a):
        """analytics._rank_avg: beraberlikler ORTALAMA rütbeyle kırılır."""
        return pd.Series(np.asarray(a, dtype=float)).rank().to_numpy()

    def spearman_ic(x, y):
        """analytics::spearman_ic — rütbe değişimi yoksa None (0.0 DEĞİL: 'ilişki yok' ≠
        'ölçülemedi')."""
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
        """IC için gün-blok bootstrap (ortak.ic_with_ci şeması)."""
        n_boot = ANAHTAR["BOOT_IC"] if n_boot is None else n_boot
        blok = ANAHTAR["BLOK"] if blok is None else blok
        tohum = ANAHTAR["TOHUM"] if tohum is None else tohum
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        uniq, inv = np.unique(np.asarray(gunler), return_inverse=True)
        nd = int(len(uniq))
        if nd < blok * 3:
            return {"lo": None, "hi": None, "n_gun": nd, "neden": f"gözlem günü {nd} < {blok * 3}"}
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
            cb = np.concatenate([[0], np.cumsum(c)[:-1]])
            poz = np.arange(tot) - np.repeat(cb, c) + np.repeat(start[gun], c)
            v = spearman_ic(x[order[poz]], y[order[poz]])
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

    # determinizm kontrolü (kart guard'ı 'sabit tohum'): aynı girdi → aynı aralık
    _a, _b = np.arange(2000) % 7 - 3.0, np.repeat(np.arange(100), 20)
    _t1 = gun_blok_bootstrap_ort(_a, _b, n_boot=200)
    _t2 = gun_blok_bootstrap_ort(_a, _b, n_boot=200)
    S["determinizm_sinamasi"] = bool(_t1["lo"] == _t2["lo"] and _t1["hi"] == _t2["hi"])
    print("   determinizm sınaması (aynı girdi → aynı CI):", S["determinizm_sinamasi"])
    if not S["determinizm_sinamasi"]:
        S["DUR"] = "bootstrap deterministik değil — kart guard'ı 'sabit tohum' ihlal"


# %%
# --- H2 — PANEL: universe_history YIL YIL (TEK KAYNAK) ------------------------------
# DELİST-DAHİLLİK KENDİLİĞİNDEN: panel geçmiş bir GÜNÜN kesitinden kurulur (bugünün listesi
# geçmişe taşınmaz). TAMPON: seçici üst-(EVREN_N×PANEL_CARPANI) alır, ÖLÇÜM evreni yine

if _kapi("2"):
    PANEL_N = int(ANAHTAR["EVREN_N"] * ANAHTAR["PANEL_CARPANI"])

    def _secici(fundamental):
        try:
            s = sorted(fundamental, key=lambda f: -(f.dollar_volume or 0.0))
        except Exception:
            s = list(fundamental)
        return [f.symbol for f in s[:PANEL_N]]

    u = qb.add_universe(_secici)
    S["api_yolu"]["evren"] = "add_universe(secici) + universe_history"

    SYM_KUTUGU, TICKER = {}, {}

    def _f_sayi(f, ad):
        try:
            v = float(getattr(f, ad))
        except Exception:
            return None
        return v if np.isfinite(v) else None

    def _f_hisse(f):
        """as-of hisse → (deger|None, kaynak): 1=company_profile.shares_outstanding (BİRİNCİL,
        SEVİYE) · 2=basic_average_shares.value (VEKİL, AĞIRLIKLI ORT.) · 0=ölçülemedi."""
        try:
            v = float(f.company_profile.shares_outstanding)
            if np.isfinite(v) and v > 0:
                return v, 1
        except Exception:
            pass
        try:
            v = float(f.earning_reports.basic_average_shares.value)
            if np.isfinite(v) and v > 0:
                return v, 2
        except Exception:
            pass
        return None, 0

    _SONDA_YOLLARI = ("price", "value", "adjusted_price", "price_factor", "split_factor",
                      "price_scale_factor", "dollar_volume", "volume", "market_cap",
                      "has_fundamental_data", "company_profile.shares_outstanding",
                      "earning_reports.basic_average_shares.value",
                      "security_reference.exchange_id")

    def _sonda(f):
        """Alan sondası: hangi alanlar GERÇEKTEN var? H3'ün bölünme kararı buna dayanır."""
        rap = {}
        for yol in _SONDA_YOLLARI:
            o = f
            try:
                for p in yol.split("."):
                    o = getattr(o, p)
                rap[yol] = (o if isinstance(o, (int, float, bool)) or o is None else str(o))
            except Exception as e:
                rap[yol] = f"<yok: {type(e).__name__}>"
        return rap

    dilimler = []
    _t = ANAHTAR["PENCERE_BAS"]
    while _t <= ANAHTAR["PENCERE_SON"]:
        _son = min(datetime(_t.year, 12, 31), ANAHTAR["PENCERE_SON"])
        dilimler.append((_t, _son))
        _t = datetime(_t.year + 1, 1, 1)
    if ANAHTAR["YIL_LIMIT"]:
        dilimler = dilimler[:int(ANAHTAR["YIL_LIMIT"])]
        _sapma("panel_dilimleri", f"ilk {len(dilimler)} yıl dilimi",
               "YIL_LIMIT daraltıldı — koşum kart penceresinin TAMAMI DEĞİLDİR")

    S["fiyat_alani"] = "price"          # H3 gerekirse değiştirir
    parcalar, dilim_muh = [], []
    for di, (t0, t1) in enumerate(dilimler):
        try:
            seri = qb.universe_history(u, t0, t1)
        except Exception as e:
            _uyar(f"{t0.date()}–{t1.date()} universe_history başarısız ({type(e).__name__}: {e})")
            dilim_muh.append({"dilim": f"{t0.date()}/{t1.date()}", "n_gun": 0, "n_satir": 0,
                              "neden": f"{type(e).__name__}: {e}"})
            continue
        kayit = []
        n_gun, n_ham = 0, []
        try:
            ogeler = list(seri.items())
        except Exception:
            ogeler = []
        for anahtar, deger in ogeler:
            if deger is None:
                continue
            try:
                lst = list(deger)
            except Exception:
                continue
            if not lst:
                continue
            if "fund_alan_sondasi" not in S:
                S["fund_alan_sondasi"] = _sonda(lst[0])
                _ap = S["fund_alan_sondasi"].get("adjusted_price")
                if isinstance(_ap, (int, float)) and not isinstance(_ap, bool) \
                        and np.isfinite(float(_ap)) and float(_ap) > 0:
                    S["fiyat_alani"] = "adjusted_price"
                print("   ALAN SONDASI:", json.dumps(S["fund_alan_sondasi"], ensure_ascii=False),
                      "\n   → panel fiyat alanı:", S["fiyat_alani"], flush=True)
            PXA = S["fiyat_alani"]
            ts = pd.Timestamp(anahtar[-1] if isinstance(anahtar, tuple) else anahtar).normalize()
            # 1) TÜM üyeden yalnız dollar_volume okunur ve üst-N kırpılır (nesne tutulmaz)
            aday = []
            for f in lst:
                dv = _f_sayi(f, "dollar_volume")
                if dv is None or dv <= 0:
                    continue
                aday.append((dv, f))
            if not aday:
                continue
            n_ham.append(len(lst))
            n_gun += 1
            aday.sort(key=lambda z: -z[0])
            # 2) kalan alanlar YALNIZ üst-N için okunur
            for dv, f in aday[:PANEL_N]:
                px = _f_sayi(f, PXA)
                if px is None or px <= 0:
                    continue
                sym = f.symbol
                sid = _sid(sym)
                if sid not in SYM_KUTUGU:
                    SYM_KUTUGU[sid] = sym
                    try:
                        TICKER[sid] = str(sym.value)
                    except Exception:
                        TICKER[sid] = sid
                sh, sk = _f_hisse(f)
                kayit.append((ts, sid, dv, px, _f_sayi(f, "volume"), sh, sk))
        del seri, ogeler
        gc.collect()
        if kayit:
            d = pd.DataFrame(kayit, columns=["tarih", "sid", "dolar_hacim", "fiyat",
                                            "hacim", "shares", "shares_kaynak"])
            for c, tp in (("dolar_hacim", "float64"), ("fiyat", "float64"),
                          ("hacim", "float64"), ("shares", "float64"),
                          ("shares_kaynak", "int8")):
                d[c] = pd.to_numeric(d[c], errors="coerce").astype(tp)
            parcalar.append(d)
        dilim_muh.append({"dilim": f"{t0.date()}/{t1.date()}", "n_gun": n_gun,
                          "n_satir": len(kayit),
                          "n_ham_medyan": (float(np.median(n_ham)) if n_ham else None),
                          "neden": (None if kayit else "satır çıkmadı")})
        print(f"   panel dilim {di + 1}/{len(dilimler)} · {t0.date()}→{t1.date()} · gün={n_gun} "
              f"satır={len(kayit)} ham_medyan={(int(np.median(n_ham)) if n_ham else None)}",
              flush=True)
        del kayit

    if not parcalar:
        S["DUR"] = ("PANEL KURULAMADI — universe_history hiçbir yıl diliminde satır döndürmedi. "
                    f"Dilim muhasebesi: {dilim_muh}")
        _olculemedi("panel", S["DUR"])
        S["dilim_muhasebe"] = dilim_muh
    else:
        B = pd.concat(parcalar, ignore_index=True)
        del parcalar
        gc.collect()
        B = B.drop_duplicates(subset=["sid", "tarih"], keep="first")
        B = B.sort_values(["tarih", "sid"], kind="mergesort").reset_index(drop=True)
        # ÖLÇÜM EVRENİ: gün içi dolar-hacim rütbesi ≤ EVREN_N (tampon HARİÇ)
        B["dv_rutbe"] = B.groupby("tarih")["dolar_hacim"].rank(ascending=False,
                                                              method="first").astype("int32")
        B["evren_uye"] = (B["dv_rutbe"] <= ANAHTAR["EVREN_N"]).to_numpy()
        B = B.sort_values(["sid", "tarih"], kind="mergesort").reset_index(drop=True)
        S["panel"] = B
        S["sym_kutugu"] = SYM_KUTUGU
        S["ticker"] = TICKER
        S["dilim_muhasebe"] = dilim_muh
        kesit = B.groupby("tarih")["evren_uye"].sum()
        S["panel_muhasebe"] = {
            "satir": int(len(B)), "gun": int(B["tarih"].nunique()),
            "sembol": int(B["sid"].nunique()),
            "tarih_araligi": [str(B["tarih"].min().date()), str(B["tarih"].max().date())],
            "panel_ust_n": PANEL_N, "olcum_evreni_ust_n": ANAHTAR["EVREN_N"],
            "evren_uye_satir": int(B["evren_uye"].sum()),
            "gunluk_evren_buyuklugu": {"medyan": float(kesit.median()), "min": int(kesit.min()),
                                       "maks": int(kesit.max())},
            "fiyat_alani": S["fiyat_alani"],
            "hacim_dolu_satir": int(B["hacim"].notna().sum()),
            "shares_kaynak_dagilimi": {str(k): int(v) for k, v in
                                       B["shares_kaynak"].value_counts().sort_index().items()},
            "shares_kaynak_kodlari": {
                "0": "ölçülemedi (her iki alan da boş/0) → hücre None",
                "1": "company_profile.shares_outstanding — BİRİNCİL, nokta-zamanlı SEVİYE",
                "2": "earning_reports.basic_average_shares.value — VEKİL, AĞIRLIKLI ORTALAMA"},
            "dilim_muhasebesi": dilim_muh,
            "bellek_mb": round(B.memory_usage(deep=True).sum() / 1e6, 1),
        }
        print("   PANEL HAZIR ·", json.dumps(S["panel_muhasebe"], ensure_ascii=False))
        _nv = int((B["shares_kaynak"] == 2).sum())
        if _nv:
            _sapma("shares_outstanding", f"{_nv} hücrede basic_average_shares vekili",
                   "company_profile boş/0 idi; basic_average_shares AĞIRLIKLI ORTALAMA'dır ve "
                   "EDG-016 bunu SEVİYE olarak REDDEDER")

        # SPX/ETF kesişimi: yalnız vekilin SPX'e ne kadar yaklaştığını ÖLÇER (TANI).
        spx = {"denendi": True, "basarili": False, "yol": None, "n_kesisim": None, "neden": None,
               "karar": "kesişim yalnız TANIDIR; evren dolar-hacim üst-N vekilidir"}
        try:
            _sp = qb.add_equity("SPY", RES_DAILY)
            _h = qb.universe_history(qb.universe.etf(_sp.symbol),
                                     ANAHTAR["PENCERE_SON"] - timedelta(days=10),
                                     ANAHTAR["PENCERE_SON"])
            _sids = set()
            for _a, _d in list(_h.items()):
                try:
                    for _c in list(_d):
                        _sids.add(_sid(_c.symbol))
                except Exception:
                    continue
            if _sids:
                _uye = set(B.loc[(B["tarih"] == B["tarih"].max()) & B["evren_uye"], "sid"])
                spx.update({"basarili": True, "yol": "universe.etf(SPY)/universe_history",
                            "n_spx": len(_sids), "n_kesisim": len(_sids & _uye),
                            "n_son_gun_evren": len(_uye)})
                print(f"   SPX/ETF üyeliği ALINDI: n={len(_sids)} · kesişim={len(_sids & _uye)}"
                      f"/{len(_uye)}")
            else:
                spx["neden"] = "ETF üyelik verisi boş döndü"
        except Exception as e:
            spx["neden"] = f"{type(e).__name__}: {e}"
        if not spx["basarili"]:
            print(f"   SPX/ETF üyeliği ALINAMADI ({spx['neden']})")
        _sapma("large_cap_suzgeci", f"günlük dolar-hacim üst-{ANAHTAR['EVREN_N']} (delist dahil)",
               "evren birebir SPX üyeliği DEĞİL, süzgeç-vekilidir (kartın izin verdiği yol); "
               f"SPX kesişim tanısı: {spx.get('n_kesisim')}")
        S["spx_uyelik_denemesi"] = spx


# %%
# --- H3 — FİYAT SERİSİ ÇAPRAZ-KONTROLÜ (zaman kayması + bölünme) --------------------
# SORU (varsayım değil, ÖLÇÜM): panelin fiyat serisi ileri getiri için yeterli mi?
#  (a) ZAMAN KAYMASI ölçümü bozmaz — öznitelik de ileri getiri de AYNI indeksten kurulur;

if _kapi("3"):
    B = S["panel"]
    ornek = list(B.groupby("sid").size().sort_values(ascending=False)
                 .index[:int(ANAHTAR["CAPRAZ_SEMBOL"])])
    cap = {"ornek_sembol": [S["ticker"].get(s, s) for s in ornek],
           "fiyat_alani": S["fiyat_alani"], "tol": ANAHTAR["CAPRAZ_TOL"],
           "maks_oran": ANAHTAR["CAPRAZ_MAKS_ORAN"],
           "beyan": "günlük GETİRİ kıyası (seviye değil); kayma k=0,1,2,-1 taranır"}
    H, hata = _bar_cek([S["sym_kutugu"][s] for s in ornek],
                       ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
    S["fiyat_kaynagi"] = "panel"
    if H is None:
        cap["kosuldu"] = False
        cap["neden"] = f"qb.history çağrısı: {hata}"
        _uyar(f"fiyat çapraz-kontrolü KOŞMADI ({hata}) — panel serisi DOĞRULANMADI")
        _sapma("fiyat_serisi", f"panel {S['fiyat_alani']} (doğrulanmadı)",
               "çapraz-kontrol çağrısı işlemedi; bölünme düzeltmesi ve zaman kayması "
               "ÖLÇÜLEMEDİ — ileri getiri bölünme günlerinde sapabilir")
        _olculemedi("fiyat_capraz_kontrolu", cap["neden"])
        B["px"] = B["fiyat"]
    else:
        cap["kosuldu"] = True
        P = B[B["sid"].isin(ornek)][["sid", "tarih", "fiyat"]].sort_values(["sid", "tarih"])
        gp = P.groupby("sid", sort=False)
        P["ret_p"] = gp["fiyat"].pct_change()
        P["_bos"] = (P["tarih"] - gp["tarih"].shift(1)).dt.days
        P = P[(P["_bos"] <= 5) & P["ret_p"].notna()]        # yalnız ardışık seans çiftleri
        H = H.sort_values(["sid", "tarih"])
        gh = H.groupby("sid", sort=False)
        H["ret_h"] = gh["close_h"].pct_change()
        taramalar = {}
        for k in (0, 1, 2, -1):
            Hk = H.assign(tarih=gh["tarih"].shift(-k))[["sid", "tarih", "ret_h"]].dropna()
            m = P.merge(Hk, on=["sid", "tarih"], how="inner").dropna(subset=["ret_p", "ret_h"])
            if len(m) == 0:
                taramalar[str(k)] = {"n": 0, "sapan_oran": None, "neden": "kesişim boş"}
                continue
            fark = np.abs(m["ret_p"].to_numpy() - m["ret_h"].to_numpy())
            taramalar[str(k)] = {"n": int(len(m)),
                                 "sapan_oran": float((fark > ANAHTAR["CAPRAZ_TOL"]).mean()),
                                 "n_sapan_buyuk": int((fark > ANAHTAR["CAPRAZ_BUYUK_TOL"]).sum()),
                                 "maks_fark": float(fark.max()),
                                 "fark_medyan": float(np.median(fark))}
        cap["kayma_taramasi"] = taramalar
        gecerli = {k: v for k, v in taramalar.items() if v.get("sapan_oran") is not None}
        if not gecerli:
            cap["en_iyi_kayma"] = None
            cap["neden"] = "hiçbir kaymada kesişim kurulamadı"
            _uyar("fiyat çapraz-kontrolü kesişim kuramadı — panel serisi DOĞRULANMADI")
            _sapma("fiyat_serisi", f"panel {S['fiyat_alani']} (doğrulanmadı)", cap["neden"])
            B["px"] = B["fiyat"]
        else:
            k_iyi, v_iyi = min(gecerli.items(), key=lambda kv: (kv[1]["sapan_oran"], -kv[1]["n"]))
            k_iyi = int(k_iyi)
            cap["en_iyi_kayma"] = k_iyi
            cap["en_iyi"] = v_iyi
            # İKİ KAPI: (i) küçük farkların ORANI (temettü/yuvarlama) eşiği aşmayacak,
            # (ii) BÜYÜK fark SIFIR olacak. Bölünme seyrektir (sembol başına bir gün) ve
            cap["yeter"] = bool(v_iyi["sapan_oran"] <= ANAHTAR["CAPRAZ_MAKS_ORAN"]
                                and v_iyi["n_sapan_buyuk"] == 0)
            print(f"   çapraz-kontrol · en iyi kayma={k_iyi} · n={v_iyi['n']} · "
                  f"sapan_oran={v_iyi['sapan_oran']:.5f} · büyük sapan="
                  f"{v_iyi['n_sapan_buyuk']} (maks {v_iyi['maks_fark']:.4f}) → "
                  f"panel yeter={cap['yeter']}")
            if k_iyi != 0:
                _sapma("panel_zaman_kaymasi", f"{k_iyi} gün",
                       "öznitelik ve ileri getiri aynı indeksten kurulduğu için ölçüm içsel "
                       "tutarlı ve ileri-bakış yok — sinyal bu kadar GECİKMELİ okunmuş sayılır")
            if cap["yeter"]:
                B["px"] = B["fiyat"]
                S["fiyat_kaynagi"] = f"panel {S['fiyat_alani']} (çapraz-kontrol GEÇTİ)"
            elif k_iyi != 0:
                S["DUR"] = (f"FİYAT SERİSİ YETERSİZ *VE* ZAMAN KAYMASI VAR (k={k_iyi}): panel "
                            "bölünme/temettü düzeltmesi taşımıyor, history tamiri ise kaymalı "
                            "birleştirme gerektiriyor — bu defterde TANIMLI DEĞİL. Uydurma "
                            "hizalama YASAK; düzeltme Rol-1 kararıdır.")
                _olculemedi("ileri_getiri", S["DUR"])
            else:
                _sapma("fiyat_serisi", "qb.history düzeltilmiş kapanış (tam tamir)",
                       f"panel {S['fiyat_alani']} çapraz-kontrolde sapan_oran="
                       f"{v_iyi['sapan_oran']:.5f} ve {v_iyi['n_sapan_buyuk']} BÜYÜK sapma "
                       f"(maks {v_iyi['maks_fark']:.4f}) verdi → bölünme/temettü düzeltmesi "
                       "taşımıyor; ileri getiri history'den kuruldu")
                sids = list(B["sid"].unique())
                parca = [sids[i:i + ANAHTAR["PARCA"]] for i in range(0, len(sids), ANAHTAR["PARCA"])]
                topla, basarisiz = [], 0
                for pi, p in enumerate(parca):
                    d, e = _bar_cek([S["sym_kutugu"][s] for s in p],
                                    ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
                    if d is None:
                        basarisiz += 1
                    else:
                        topla.append(d)
                    if pi % 5 == 0 or pi == len(parca) - 1:
                        print(f"   history tamiri {pi + 1}/{len(parca)} parça", flush=True)
                if not topla:
                    S["DUR"] = ("FİYAT TAMİRİ BAŞARISIZ — panel serisi yetersiz ve qb.history "
                                "hiçbir parçada veri döndürmedi; ileri getiri ÖLÇÜLEMEZ")
                    _olculemedi("ileri_getiri", S["DUR"])
                else:
                    HH = pd.concat(topla, ignore_index=True).drop_duplicates(
                        subset=["sid", "tarih"], keep="last")
                    B = B.merge(HH, on=["sid", "tarih"], how="left")
                    n_bos = int(B["close_h"].isna().sum())
                    B["px"] = B["close_h"]
                    S["fiyat_kaynagi"] = "qb.history düzeltilmiş kapanış (tamir)"
                    cap["tamir"] = {"parca": len(parca), "basarisiz_parca": basarisiz,
                                    "eslesmeyen_panel_satiri": n_bos,
                                    "beyan": "eşleşmeyen satırda px None → ileri getiri "
                                             "ÖLÇÜLEMEZ (doldurulmadı)"}
                    print(f"   history tamiri tamam · eşleşmeyen satır={n_bos}")
    S["fiyat_capraz_kontrol"] = cap
    if not S["DUR"]:
        if "px" not in B.columns:
            B["px"] = B["fiyat"]
        S["panel"] = B
        print("   fiyat kaynağı:", S["fiyat_kaynagi"])


# %%
# --- H4 — ÖZNİTELİKLER + SÜREKLİLİK BEKÇİLERİ + DELİST VEKİLİ -----------------------
# EDG-016 / meridian.indicators birebir: rvol20(t)=hacim(t)/SMA20(hacim)[t] (payda BUGÜNÜ
# İÇERİR) · med_hacim21(t)=medyan(hacim[t-20..t]) · fwd_h(t)=px(t+h)/px(t)-1. Geriye

if _kapi("4"):
    B = S["panel"]
    g = B.groupby("sid", sort=False)
    TOL = float(ANAHTAR["SPAN_TOLERANS"])
    bekci = {}

    def _geri_gecerli(k):
        """k satırlık GERİYE pencerenin takvim yayılımı tolerans içinde mi?"""
        return ((B["tarih"] - g["tarih"].shift(k - 1)).dt.days <= (k - 1) * TOL).to_numpy()

    kr = int(ANAHTAR["RVOL_PENCERE"])
    sma = g["hacim"].transform(lambda s: s.rolling(kr, min_periods=kr).mean())
    ok = _geri_gecerli(kr)
    ham = B["hacim"] / sma
    B["rvol20"] = ham.where(ok & (sma > 0))
    bekci["rvol20_span_kapatti"] = int((ham.notna() & ~ok).sum())

    kt = int(ANAHTAR["TURNOVER_PENCERE"])
    med = g["hacim"].transform(lambda s: s.rolling(kt, min_periods=kt).median())
    ok = _geri_gecerli(kt)
    B["med_hacim21"] = med.where(ok)
    bekci["med_hacim21_span_kapatti"] = int((med.notna() & ~ok).sum())

    for h in ANAHTAR["UFUKLAR"]:
        ileri = g["px"].transform(lambda s, h=h: s.shift(-h) / s - 1.0)
        okf = ((g["tarih"].shift(-h) - B["tarih"]).dt.days <= h * TOL).to_numpy()
        B[f"fwd{h}"] = ileri.where(okf)
        bekci[f"fwd{h}_span_kapatti"] = int((ileri.notna() & ~okf).sum())

    # DELİST VEKİLİ: erken biten sembol "çıkış adayı"dır ama çıkış SEBEBİ panelden ayırt
    # edilemez (delist mi, dolar-hacim sıralamasından düşüş mü). Ayırt edici ÇIKIŞ RÜTBESİ:
    # üst-EVREN_N içindeyken kaybolan isim, kuyrukta solarak çıkandan delist'e yakındır.
    son_bar = B.groupby("sid")["tarih"].max()
    panel_son = B["tarih"].max()
    esik = panel_son - pd.Timedelta(days=int(ANAHTAR["DELIST_TAMPON_GUN"] * 1.6))
    cikis_rutbe = B.sort_values(["sid", "tarih"]).groupby("sid").tail(1).set_index("sid")["dv_rutbe"]
    erken = set(son_bar[son_bar < esik].index)
    aday = {s for s in erken if int(cikis_rutbe.get(s, 10 ** 9)) <= ANAHTAR["EVREN_N"]}
    delist_sid = set(aday)
    S["delist_sid"] = delist_sid
    S["cikis_muhasebe"] = {"erken_cikan": len(erken), "yuksek_rutbe_aday": len(aday),
                           "dusuk_rutbe_cikis": len(erken) - len(aday)}
    S["delist_yontemi"] = (
        f"VEKİL: son panel günü panel sonundan >{ANAHTAR['DELIST_TAMPON_GUN']} iş günü önce "
        f"biten VE o gün dolar-hacim rütbesi üst-{ANAHTAR['EVREN_N']} içinde olan semboller "
        "(kuyrukta solarak evrenden düşenler böylece elenir). "
        "QC map-file/Delisting olayı SORULMADI (API yolu ölçülmedi) ve çıkış sonrası bar "
        "aranmadı — bu bir VEKİLDİR; gerçek delist'i veri/likidite kesintisinden ya da "
        "evrenden düşüşten kesin AYIRAMAZ.")
    _sapma("delist_tespiti", "panel-çıkış + çıkış-rütbesi vekili", S["delist_yontemi"])

    # Delist isminin son h günü için fwd TANIMSIZ (bar yok) → satır düşer, SAYILIR.
    # H10'da 'son fiyattan tasfiye' duyarlılığı ayrı satır olarak okunur.
    dusen = {}
    sonf = g["px"].transform("last")
    for h in ANAHTAR["UFUKLAR"]:
        m = B["sid"].isin(delist_sid) & B[f"fwd{h}"].isna() & B["px"].notna()
        dusen[str(h)] = int(m.sum())
        B[f"fwd{h}_delist_kapatilmis"] = B[f"fwd{h}"].where(
            B[f"fwd{h}"].notna(), (sonf / B["px"] - 1.0).where(m))
    S["delist_fwd_dusen"] = dusen
    S["span_bekcisi"] = bekci

    for c in (["rvol20", "med_hacim21"]
              + [f"fwd{h}" for h in ANAHTAR["UFUKLAR"]]
              + [f"fwd{h}_delist_kapatilmis" for h in ANAHTAR["UFUKLAR"]]):
        if c in B.columns:
            B[c] = B[c].astype("float32")
    B = B.drop(columns=[c for c in ("close_h",) if c in B.columns])
    S["panel"] = B
    S["bellek_mb"] = {"H4_oznitelikli": round(B.memory_usage(deep=True).sum() / 1e6, 1)}
    print(f"   öznitelikler · rvol20={int(B['rvol20'].notna().sum())} "
          f"med_hacim21={int(B['med_hacim21'].notna().sum())} "
          f"fwd20={int(B['fwd20'].notna().sum())} · bellek≈{S['bellek_mb']['H4_oznitelikli']} MB")
    print(f"   süreklilik bekçisi kapattı: {bekci}")
    print(f"   çıkış muhasebesi: {S['cikis_muhasebe']} · delist vekili={len(delist_sid)} · "
          f"delist yüzünden fwd düşen satır={dusen}")


# %%
# --- H5 — POZİTİF KONTROL (KART GUARD'I) · KAPI -------------------------------------
# Kart guards: rvol20 @20 IC işaret/mertebesi (çivi ≈0.064) yeniden üretilmeli, yoksa DUR.
# H2–H4 yalnız VERİ TAŞIR — ilk ÖLÇÜM işi budur; tutmazsa kayıtlı hücre (H6–H8) KOŞMAZ.

if _kapi("5"):
    B = S["panel"]
    pk_df = B[B["evren_uye"] & B["rvol20"].notna() & B["fwd20"].notna()]
    kesit = pk_df.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    pk_df = pk_df[pk_df["tarih"].isin(kullan)]
    pk = {"tanim": "rvol20 = hacim / SMA20(hacim), payda bugünü içerir (meridian.indicators)",
          "olcum": "havuzlanmış Spearman IC (rvol20, fwd20) · aynı kesit kuralları",
          "yerel_civi": ANAHTAR["PK_CIVI"], "mertebe_carpani": ANAHTAR["PK_MERTEBE"],
          "beyan": "yerel çivi karşı-olgusal katmanda ölçüldü; İŞARET ve MERTEBE aranır "
                   "(nokta eşitliği değil). Hüküm eşiği DEĞİL, boru hattı kapısı.",
          "n": int(len(pk_df)), "n_gun": int(pk_df["tarih"].nunique())}
    if len(pk_df) < ANAHTAR["MIN_DILIM"]:
        pk["ic"] = None
        pk["neden"] = f"n={len(pk_df)} < MIN_DILIM={ANAHTAR['MIN_DILIM']}"
        pk["GECTI"] = None
    else:
        ic = spearman_ic(pk_df["rvol20"].to_numpy(float), pk_df["fwd20"].to_numpy(float))
        pk["ic"] = None if ic is None else float(ic)
        pk["ci"] = ic_gun_blok_ci(pk_df["rvol20"].to_numpy(float),
                                  pk_df["fwd20"].to_numpy(float), pk_df["tarih"].to_numpy())
        if ic is None:
            pk["GECTI"] = None
            pk["neden"] = "rütbe değişimi yok — IC tanımsız"
        else:
            alt = ANAHTAR["PK_CIVI"] / ANAHTAR["PK_MERTEBE"]
            ust = ANAHTAR["PK_CIVI"] * ANAHTAR["PK_MERTEBE"]
            pk["bant"] = [alt, ust]
            pk["GECTI"] = bool(ic > 0 and alt <= ic <= ust)
            pk["neden"] = None if pk["GECTI"] else (
                f"IC={ic:.4f} · beklenen POZİTİF ve bant [{alt:.4f}, {ust:.4f}]")
    S["pk"] = pk
    print(f"   PK · IC@20={pk.get('ic')} · n={pk['n']} · gün={pk['n_gun']} · "
          f"çivi={ANAHTAR['PK_CIVI']} → GEÇTİ={pk.get('GECTI')}")
    if pk.get("ci"):
        print(f"   PK CI: {pk['ci'].get('lo')} .. {pk['ci'].get('hi')}")
    if pk.get("GECTI") is not True:
        S["DUR"] = (f"POZİTİF KONTROL TUTMADI (kart guard'ı) — IC@20={pk.get('ic')}; beklenen: "
                    f"pozitif ve ≈{ANAHTAR['PK_CIVI']} mertebesinde (×{ANAHTAR['PK_MERTEBE']} "
                    f"bandı). Ayrıntı: {pk.get('neden')}. Boru hattı geçersiz sayılır; sonraki "
                    "hücreler KOŞTURULMAZ, hiçbir kart sayısı üretilmez.")
        print("\n" + "=" * 78)
        print("PK-DUR: DEFTER DURDU. Son hücreyi (H11) yine de koş — DUR nedenini taşıyan")
        print("        JSON'u basar. O JSON'u operatör talimatındaki gibi Rol-1'e ilet.")
        print("=" * 78)


# %%
# --- H6 — turnover21 = medyan21(hacim) / as-of hisse sayısı -------------------------
# Hisse ayrı çağrıdan değil PANELİN KENDİ SATIRINDAN gelir (H2). AS-OF: yalnız İLERİ doldurma.
# Bayatlık bekçisi (EDG-016 SCHW dersi) + fiziksel bekçi (devir > TURNOVER_TAVAN imkânsız).

if _kapi("6"):
    B = S["panel"]
    n_ham_dolu = int(B["shares"].notna().sum())
    if n_ham_dolu == 0:
        S["DUR"] = ("shares_outstanding AS-OF ALINAMADI — panelin hiçbir satırında ne "
                    "company_profile.shares_outstanding ne earning_reports."
                    "basic_average_shares.value ölçülebildi. Kart kill_criteria: 'ölçülemedi' "
                    "beyanı, kart askıya (uydurma vekil YASAK).")
        _olculemedi("shares_outstanding_as_of", S["DUR"])
        S["shares_muhasebe"] = {"shares_ham_dolu_hucre": 0, "neden": S["DUR"]}
    else:
        gg = B.groupby("sid", sort=False)
        B["_ks"] = B["tarih"].where(B["shares"].notna())
        B["shares"] = gg["shares"].ffill()
        B["shares_bayatlik_gun"] = (B["tarih"] - gg["_ks"].ffill()).dt.days
        bayat = B["shares_bayatlik_gun"] > ANAHTAR["SHARES_BAYAT_GUN"]
        n_bayat = int((bayat & B["shares"].notna()).sum())
        B.loc[bayat, "shares"] = np.nan
        B = B.drop(columns=["_ks"])
        B["turnover21"] = B["med_hacim21"].astype("float64") / B["shares"]
        fiziksel = B["turnover21"] > ANAHTAR["TURNOVER_TAVAN"]
        n_fiziksel = int((fiziksel & B["turnover21"].notna()).sum())
        B.loc[fiziksel, "turnover21"] = np.nan
        B["turnover21"] = B["turnover21"].astype("float32")
        S["panel"] = B
        S.setdefault("bellek_mb", {})["H6_turnoverli"] = round(
            B.memory_usage(deep=True).sum() / 1e6, 1)
        n_dolu = int(B["shares"].notna().sum())
        S["shares_muhasebe"] = {
            "kaynak": "panel (universe_history): company_profile birincil, "
                      "basic_average_shares vekil",
            "shares_ham_dolu_hucre": n_ham_dolu,
            "shares_kaynak_dagilimi": S["panel_muhasebe"]["shares_kaynak_dagilimi"],
            "shares_kaynak_kodlari": S["panel_muhasebe"]["shares_kaynak_kodlari"],
            "ffill_sonrasi_dolu_hucre": n_dolu,
            "bayatlik_bekcisi_kapatti": n_bayat,
            "bayatlik_esik_gun": ANAHTAR["SHARES_BAYAT_GUN"],
            "bayatlik_medyan_gun": (float(B.loc[B["shares"].notna(),
                                                "shares_bayatlik_gun"].median())
                                    if n_dolu else None),
            "fiziksel_bekci_kapatti": n_fiziksel,
            "fiziksel_tavan": ANAHTAR["TURNOVER_TAVAN"],
            "turnover21_dolu_hucre": int(B["turnover21"].notna().sum()),
            "as_of_beyani": "QC evren verisi gün gün teslim edilir; t satırı t günü bilinen "
                            "değer sayıldı (EDGAR filed<=t karşılığı). BAĞIMSIZ DOĞRULANMADI.",
        }
        print("   TURNOVER ·", json.dumps(S["shares_muhasebe"], ensure_ascii=False))
        n_to = int(B["turnover21"].notna().sum())
        if n_to < ANAHTAR["MIN_DILIM"]:
            S["DUR"] = (f"turnover21 ÖLÇÜLEMEDİ — kullanılabilir hücre {n_to} < MIN_DILIM="
                        f"{ANAHTAR['MIN_DILIM']} (bayatlık/fiziksel bekçileri ya da hacim "
                        "penceresi kapattı). Uydurma doldurma YASAK.")
            _olculemedi("turnover21", S["DUR"])


# %%
# --- H7 — KESİT + ÜST-%20 DİLİM + AYNI-GÜN EVREN TABANI -----------------------------
# EDG-016 ile birebir: kesit = o gün ÖLÇÜM EVRENİ üyesi ve turnover21 tanımlı semboller
# (kesit ≥ MIN_KESIT); dilim = gün içi turnover21 yüzdelik rütbesi > 0.80; taban = AYNI GÜN

if _kapi("7"):
    B = S["panel"]
    V = B[B["evren_uye"] & B["turnover21"].notna()].copy()
    kesit = V.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    V = V[V["tarih"].isin(kullan)].copy()
    V["to_pct"] = V.groupby("tarih")["turnover21"].rank(pct=True, method="first")
    V["ust"] = V["to_pct"] > (1.0 - ANAHTAR["UST_PCT"])
    taban = {}
    for h in ANAHTAR["UFUKLAR"]:
        t = B[B["evren_uye"]][["tarih", f"fwd{h}"]].dropna()
        taban[h] = t.groupby("tarih")[f"fwd{h}"].mean()
    S["taban"] = taban
    S["V"] = V
    if len(V) == 0:
        S["DUR"] = ("KESİT KURULAMADI — hiçbir günde turnover21 tanımlı evren üyesi sayısı "
                    f"MIN_KESIT={ANAHTAR['MIN_KESIT']} eşiğine ulaşmadı")
        _olculemedi("kesit", S["DUR"])
    else:
        kk = kesit[kesit >= ANAHTAR["MIN_KESIT"]]
        S["kesit_muhasebe"] = {
            "gozlem_gunu_toplam": int(B[B["evren_uye"]]["tarih"].nunique()),
            "kesit_yeterli_gun": int(len(kullan)), "min_kesit": ANAHTAR["MIN_KESIT"],
            "kesit_buyuklugu": {"medyan": float(kk.median()), "min": int(kk.min()),
                                "maks": int(kk.max())},
            "tarih_araligi": [str(V["tarih"].min().date()), str(V["tarih"].max().date())],
            "n_satir": int(len(V)), "n_sembol": int(V["sid"].nunique()),
            "turnover21_dagilimi": {str(q): float(V["turnover21"].quantile(q))
                                    for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
            "dilim_satir": int(V["ust"].sum()),
            "dilim_sembol": int(V.loc[V["ust"], "sid"].nunique()),
        }
        print("   KESİT ·", json.dumps(S["kesit_muhasebe"], ensure_ascii=False))


# %%
# --- H8 — ÖLÇÜM: ÜST-%20 DİLİM EVREN-FAZLASI + 21g BLOK CI + MALİYET ----------------
# Kartın TEK kayıtlı hücresi: qc_turnover_ust20_fazlasi (K+=1). Maliyet SABİTTİR → CI aynı
# sabitle ötelenir (bootstrap yeniden koşulmaz; cebirsel özdeş, EDG-016 ile aynı okuma).

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
            "tanim": f"gün içi turnover21 üst %{int(ANAHTAR['UST_PCT'] * 100)} dilimi; taban "
                     "= AYNI GÜN evren ortalaması (delist DAHİL)",
            "n_sembol_gun": int(len(fazla)), "n_gun": int(len(gun_ort)),
            "n_sembol": int(pd.Series(sub["sid"].to_numpy()[ok]).nunique()),
            "dilim_turnover21_medyan": float(V.loc[V["ust"], "turnover21"].median()),
            "ham_getiri": gun_blok_bootstrap_ort(y, d),
            "evren_fazlasi": gun_blok_bootstrap_ort(fazla, d),
            "evren_fazlasi_gun_agirlikli_CI": gun_blok_bootstrap_ort(
                gun_ort.to_numpy(), gun_ort.index.to_numpy()),
            "taban_ort": (float(np.mean(b)) if len(b) else None),
        }
        blok = olcum[str(h)]["evren_fazlasi"]
        print(f"   @{h} · n={len(fazla)} gün={len(gun_ort)} · fazla ort={blok['ort']} "
              f"CI[{blok.get('lo')}, {blok.get('hi')}]", flush=True)
        satirlar = {}
        for etiket, bps in (("kart_modeli_10bps", ANAHTAR["MALIYET_BPS"]),
                            ("duyarlilik_20bps", ANAHTAR["MALIYET_BPS_DUYARLILIK"])):
            c = bps / 10000.0
            satirlar[etiket] = {
                "bps": bps, "brut": blok["ort"],
                "net": (None if blok["ort"] is None else blok["ort"] - c),
                "net_ci": (None if blok.get("lo") is None else
                           {"lo": blok["lo"] - c, "hi": blok["hi"] - c, "seviye": 0.95,
                            "sifir_disinda": bool((blok["lo"] - c) > 0 or (blok["hi"] - c) < 0)}),
                "beyan": "maliyet SABİT → CI aynı sabitle ötelendi (bootstrap koşulmadı)",
            }
        maliyet[str(h)] = satirlar
    S["olcum"] = olcum
    S["maliyet"] = maliyet
    S["fazla_kayit"] = fazla_kayit


# %%
# --- H9 — ALT-DÖNEM BETİMLEYİCİ TABLO (CI YOK) --------------------------------------
# EDG-016 çekince Ç2. Kart grid'inde alt-dönem bacağı YOK → CI BİLEREK hesaplanmadı
# (CI'lı sınansaydı K çarpılırdı). Hüküm bacağı DEĞİLDİR.

if _kapi("9"):
    alt = {"beyan": "BETİMLEYİCİ — kart grid'inde alt-dönem bacağı yok; CI bilerek "
                    "hesaplanmadı (K çarpılmasın).", "ufuklar": {}}
    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, _ = S["fazla_kayit"][h]
        yil = pd.DatetimeIndex(d).year
        tab = {}
        for y in sorted(set(yil.tolist())):
            m = (yil == y)
            tab[str(y)] = {"n": int(m.sum()), "n_gun": int(pd.Series(d[m]).nunique()),
                           "fazla_ort": float(np.mean(fazla[m])) if m.sum() else None,
                           "fazla_medyan": float(np.median(fazla[m])) if m.sum() else None,
                           "pozitif_oran": float((fazla[m] > 0).mean()) if m.sum() else None}
        alt["ufuklar"][str(h)] = tab
        print(f"   @{h} alt-dönem:", {k: (round(v["fazla_ort"], 5)
                                          if v["fazla_ort"] is not None else None)
                                      for k, v in tab.items()})
    S["alt_donem"] = alt


# %%
# --- H10 — EVREN / DELİST MUHASEBESİ · SURVIVORSHIP GÖSTERGELERİ (CI YOK) -----------
# Kartın asıl sorusu: dilimdeki sonradan-delist isimler ne kadar yer tutuyor, fazlaya ne
# katıyor? tum (kayıtlı hücre) · yalniz_hayatta_kalanlar (EDG-016'nın gördüğü dünya) ·

if _kapi("10"):
    V = S["V"]
    dl = S["delist_sid"]
    B = S["panel"]
    dm = {
        "yontem": S["delist_yontemi"],
        "beyan": "BETİMLEYİCİ — CI hesaplanmadı (kayıtlı hücre TEK). Hüküm bacağı değildir.",
        "panel_sembol": int(B["sid"].nunique()),
        "cikis_muhasebesi": S["cikis_muhasebe"],
        "delist_vekili_sembol": int(len(dl)),
        "delist_vekili_pay": float(len(dl)) / max(1, int(B["sid"].nunique())),
        "kesit_delist_satir": int(V["sid"].isin(dl).sum()), "kesit_satir": int(len(V)),
        "dilim_delist_satir": int((V["ust"] & V["sid"].isin(dl)).sum()),
        "dilim_satir": int(V["ust"].sum()),
        "dilim_delist_sembol": int(V.loc[V["ust"] & V["sid"].isin(dl), "sid"].nunique()),
        "delist_fwd_olculemeyen_satir": S["delist_fwd_dusen"],
        "span_bekcisi_kapatti": S["span_bekcisi"],
        "ufuklar": {},
    }
    dm["dilim_delist_satir_pay"] = dm["dilim_delist_satir"] / max(1, dm["dilim_satir"])
    dm["delist_dilime_yogunlasiyor_mu"] = {
        "dilimdeki_delist_payi": dm["dilim_delist_satir_pay"],
        "kesitteki_delist_payi": dm["kesit_delist_satir"] / max(1, dm["kesit_satir"]),
        "okuma": "dilim payı kesit payından BÜYÜKSE yüksek-turnover dilimi delist isimleri "
                 "fazladan topluyor (EDG-016 Ç1 göstergesi; yorum Rol-1)",
    }
    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, sid_ar = S["fazla_kayit"][h]
        is_dl = pd.Series(sid_ar).isin(dl).to_numpy()

        def _bet(mask, fazla=fazla, sid_ar=sid_ar):
            if mask.sum() == 0:
                return {"n": 0, "ort": None, "neden": "satır yok"}
            return {"n": int(mask.sum()), "n_sembol": int(pd.Series(sid_ar[mask]).nunique()),
                    "ort": float(np.mean(fazla[mask])), "medyan": float(np.median(fazla[mask])),
                    "pozitif_oran": float((fazla[mask] > 0).mean())}

        tum, hay, dlt = _bet(np.ones(len(fazla), bool)), _bet(~is_dl), _bet(is_dl)
        dm["ufuklar"][str(h)] = {
            "tum": tum, "yalniz_hayatta_kalanlar": hay, "yalniz_sonradan_delist": dlt,
            "survivorship_primi_vekili": (None if (hay["ort"] is None or tum["ort"] is None)
                                          else hay["ort"] - tum["ort"]),
            "okuma": "prim_vekili > 0 → delist isimleri fazlayı AŞAĞI çekiyor, yani "
                     "sağkalan-evrende ölçülen sayı yukarı çarpıktı. SAYIDIR, hüküm değil.",
        }
        sut = f"fwd{h}_delist_kapatilmis"
        if sut in V.columns:
            sub = V[V["ust"]][["tarih", "sid", sut]].dropna(subset=[sut])
            base = sub["tarih"].map(S["taban"][h])
            m2 = base.notna().to_numpy()
            fz2 = sub[sut].to_numpy(float)[m2] - base.to_numpy(float)[m2]
            dm["ufuklar"][str(h)]["duyarlilik_delist_son_fiyattan_tasfiye"] = {
                "n": int(len(fz2)), "ort": (float(np.mean(fz2)) if len(fz2) else None),
                "beyan": "delist isminin son h gününde bar yok → fwd ölçülemez; bu satır o "
                         "boşluğu 'son kapanıştan tasfiye' VARSAYIMIYLA doldurur. CI YOK, "
                         "hüküm bacağı DEĞİL.",
            }
    S["delist_muhasebe"] = dm
    print("   delist payı — dilim:", round(dm["dilim_delist_satir_pay"], 5), "kesit:",
          round(dm["delist_dilime_yogunlasiyor_mu"]["kesitteki_delist_payi"], 5))
    for h in ANAHTAR["UFUKLAR"]:
        uu = dm["ufuklar"][str(h)]
        print(f"   @{h} tüm={uu['tum']['ort']} hayatta={uu['yalniz_hayatta_kalanlar']['ort']} "
              f"delist={uu['yalniz_sonradan_delist']['ort']} "
              f"prim_vekili={uu['survivorship_primi_vekili']}")


# %%
# --- H11 — TEK JSON BLOĞU (şema: cikti_semasi.md) -----------------------------------
# DUR hâlinde de koşar: operatörün elinde iletilecek kanıt olur. JSON'da HÜKÜM YOKTUR.

def _json_guvenli(o):
    import numpy as _np
    if isinstance(o, dict):
        return {str(k): _json_guvenli(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_json_guvenli(v) for v in o]
    if isinstance(o, _np.integer):
        return int(o)
    if isinstance(o, _np.floating):
        f = float(o)
        return None if (f != f or f in (float("inf"), float("-inf"))) else f
    if isinstance(o, _np.bool_):
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
    "defter_surumu": "2.0",
    "defter_mimarisi": "TEK KAYNAK add_universe+universe_history → list[Fundamental]; evren, "
                       "fiyat, hacim, as-of hisse aynı çağrıdan. v1'in history(Fundamental)/"
                       "CoarseFundamental/get_fundamental yolları FREE hesapta BOŞ dönüyor "
                       "(QC_API_ZEMIN_GERCEGI.md) → çıkarıldı.",
    "defter_sha256": None,
    "defter_sha256_neden": "koşan defter kendi kaynağını okumaz; sha256 REPO tarafında alınır",
    "rol": "ölçüm defteri — SAYI üretir, HÜKÜM VERMEZ. Eşik içermez. Hüküm Rol-1'de.",
    "kosum": {
        "zaman_utc": str(datetime.utcnow()) + "Z",
        "ortam": "QuantConnect Research (QuantBook)",
        "api_yolu": S.get("api_yolu"),
        "fundamental_alan_sondasi": S.get("fund_alan_sondasi"),
        "determinizm_sinamasi": S.get("determinizm_sinamasi"),
        "bellek_mb": S.get("bellek_mb"),
    },
    "anahtarlar": {k: (str(v) if isinstance(v, datetime) else v) for k, v in ANAHTAR.items()},
    "DUR": S.get("DUR"),
    "pozitif_kontrol": S.get("pk"),
    "evren": {
        "beyan": f"GÜNLÜK dolar-hacim üst-{ANAHTAR['EVREN_N']} — DELİST DAHİL (geçmiş günün QC "
                 "evren kesiti; o gün borsada olan, bugün olmayan isimler İÇERİDEDİR). Panel "
                 f"üst-{ANAHTAR['EVREN_N'] * ANAHTAR['PANEL_CARPANI']} taşır; fazlası pencere "
                 "sürekliliği TAMPONUDUR, ölçüm satırı yalnız evren_uye olanlardır.",
        "spx_uyelik_denemesi": S.get("spx_uyelik_denemesi"),
        "panel_muhasebesi": S.get("panel_muhasebe"),
        "kesit_muhasebesi": S.get("kesit_muhasebe"),
        "shares_muhasebesi": S.get("shares_muhasebe"),
    },
    "fiyat_capraz_kontrol": S.get("fiyat_capraz_kontrol"),
    "tanimlar": {
        "turnover21": "medyan21(hacim) / shares_outstanding(as-of t)",
        "rvol20": "hacim(t)/SMA20(hacim)[t] — payda BUGÜNÜ İÇERİR (meridian.indicators)",
        "dilim": f"gün içi turnover21 yüzdelik rütbesi > {1 - ANAHTAR['UST_PCT']}",
        "taban": "AYNI GÜN evren ortalaması (ileri getirisi tanımlı tüm evren üyeleri)",
        "fwd_h": "px(t+h)/px(t) - 1",
        "px_kaynagi": S.get("fiyat_kaynagi"),
        "sureklilik_bekcisi": f"satır-tabanlı pencere takvimde k×{ANAHTAR['SPAN_TOLERANS']} günü "
                              "aşarsa hücre ÖLÇÜLEMEZ (panelden düşüp dönen sembolde pencere "
                              "sessizce uzamasın diye)",
        "ci": f"{ANAHTAR['BLOK']} ardışık gözlem günü blok-bootstrap, %95, B={ANAHTAR['BOOT']} "
              f"(IC: {ANAHTAR['BOOT_IC']}), tohum={ANAHTAR['TOHUM']}; HEADLINE satır-ağırlıklı "
              "gün-blok (EDG-016 ile aynı). İkincil okuma AYNI araca gün-ortalaması serisi "
              "verilerek üretilir (satır=gün → gün-ağırlıklı); v1'deki kanonik "
              "olcum_araclari.blok_bootstrap_ci kopyası KARAKTER SINIRI nedeniyle çıkarıldı — "
              "fark: tohum (20260801 vs 11) ve blok kuralı (sabit 21 vs n^(1/3))",
        "maliyet": f"kart cost_model {ANAHTAR['MALIYET_BPS']}bps tek-yön; "
                   f"{ANAHTAR['MALIYET_BPS_DUYARLILIK']}bps BEYANLI DUYARLILIK",
        "K_beyani": "kart grid'i TEK katman (K+=1): qc_turnover_ust20_fazlasi. Ufuk 10/20 "
                    "horizon alanıdır, K çarpanı DEĞİL. Alt-dönem ve delist ayrıştırması "
                    "BETİMLEYİCİ, CI TAŞIMAZ.",
    },
    "tanim_sapmalari": S.get("tanim_sapmalari"),
    "olcum": {"ust20_evren_fazlasi": S.get("olcum")},
    "maliyet": S.get("maliyet"),
    "alt_donem_betimleyici": S.get("alt_donem"),
    "delist_muhasebesi": S.get("delist_muhasebe"),
    "kiyas_notu": {
        "edg_016": {"ust20_evren_fazlasi_10": 0.0031, "ust20_evren_fazlasi_20": 0.00648,
                    "net_10bps_20": 0.00548,
                    "kaynak": "wp2_olcum/RAPOR_016.md (sağkalan evren, full_251)"},
        "beyan": "EDG-016 sayıları BURADA HESAPLANMADI, kıyas için taşındı. İki ölçüm FARKLI "
                 "evrende yapıldı; fark yalnız survivorship'e atfedilemez.",
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
