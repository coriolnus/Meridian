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

TAZE-QB KURALI (v3, canlı ölçümle zorunlu oldu): QuantBook örneği AMAÇ BAŞINA ayrıdır ve
PAYLAŞILMAZ — durumu değişmiş bir örnekte universe_history sessizce 0 satır döndürüyor
(v2'nin H2-DUR'unun kök nedeni). QB_BAR (H1) · QB_PANEL (H2, taze) · QB_SPX (H2b, taze).
H2 panel çekiminden ÖNCE 10 günlük MİNİ-SONDA koşar; satır dönmezse HEMEN DUR der.

KOŞUM — defter QC'nin dosya başına sınırı için ÜÇ PARÇAYA bölündü. Üçünü de projeye yükle
ve notebook'ta TEK hücrede, AYNI namespace'e sırayla koştur:

    for _p in ("a", "b", "c"):
        exec(open(f"qc_defter_021_{_p}.py").read(), globals())

`globals()` ŞART: parçalar tek bir durum sözlüğünü (`S`) paylaşır. Sıra a → b → c'dir;
_b ve _c önce _a koşmadıysa hata verir. _c (JSON) DUR hâlinde de koşturulmalıdır.

HÜCRELER — [a] H0 ayarlar · H1 QB_BAR+bar yardımcısı · H1b ölçüm araçları+determinizm |
[b] H2 evren+MİNİ-SONDA · H2b panel çekimi · H3 fiyat çapraz-kontrolü · H4 öznitelikler+
süreklilik bekçileri+delist vekili | [c] H5 POZİTİF KONTROL (KAPI) · H6 turnover21 ·
H7 kesit+dilim+taban · H8 ÖLÇÜM (fazla+CI+maliyet) · H9 alt-dönem · H10 delist muhasebesi ·
H11 SONUÇ JSON
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
    "SONDA_GUN":     10,          # H2 mini-sondası: panel çekiminden ÖNCE bu kadar günlük dene

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
# API adları TAHMİN DEĞİL — zemin sondası snake_case yüzeyi canlıda doğruladı.
# TAZE-QB KURALI: QuantBook örneği amaç başına ayrıdır, PAYLAŞILMAZ (aşağıda gerekçe).

if _kapi("1"):
    import gc
    import json

    import numpy as np
    import pandas as pd

    from AlgorithmImports import *
    S["api_yolu"]["import"] = "AlgorithmImports"

    RES_DAILY = getattr(Resolution, "DAILY", None) or getattr(Resolution, "Daily")
    S["api_yolu"]["Resolution"] = "DAILY"

    # TAZE-QB KURALI (canlı ölçüm, QC_API_ZEMIN_GERCEGI.md "EK ÖLÇÜM"): durumu değişmiş bir
    # QuantBook örneğinde universe_history SESSİZCE 0 satır döndürüyor. Bu yüzden HER AMAÇ
    # KENDİ TAZE ÖRNEĞİNİ kurar ve örnek PAYLAŞILMAZ:
    #   QB_BAR   → yalnız qb.history (bar) çağrıları           [burada]
    #   QB_PANEL → yalnız evren/universe_history               [H2, taze]
    #   QB_SPX   → yalnız SPX/ETF tanısı (add_equity kirletir)  [H2b, taze]
    QB_BAR = QuantBook()
    S["api_yolu"]["qb_bar"] = "QuantBook() — yalnız bar (history) çağrıları"
    S["api_yolu"]["tarih_baglami"] = (
        "KURULMADI (bilinçli) — set_start_date/set_end_date örnek durumunu değiştiriyor ve "
        "v2'de evreni sessizce boşalttı; semboller Fundamental'dan geldiği için ticker "
        "çözümüne gerek yok")

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
        """QB_BAR.history → düz tablo (sid, tarih, close_h). Dönüş: (df|None, neden|None).
        SADECE QB_BAR kullanır — evren örneğine (QB_PANEL) DOKUNMAZ (taze-qb kuralı)."""
        try:
            h = QB_BAR.history(list(semboller), t0, t1, RES_DAILY)
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

