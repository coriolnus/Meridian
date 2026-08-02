"""EDG-2026-017 · BEKÇİLER — POZİTİF KONTROL + PK4 + PK5 + temiz_taban ÖZDEŞLİĞİ.

KART GUARD'I (harfiyen): "pozitif kontrol: ham rvol20 @20 IC ≈0.0642 çivisi sandbox'ta yeniden
üretilir (ÜRETİLEMEZSE ÖLÇÜM DURUR)" ve "PK4/PK5 yol-tutarlılık kontrolleri + temiz_taban
(aynı-gün evren) zorunlu".

Bu dosya İLK KOŞAN İŞTİR. Çivi tutmazsa k017.py hiçbir hücre ölçmez.
Şablon: scratchpad/wp2_olcum/pk.py (aynı katman, aynı hedef, aynı tolerans — DEĞİŞTİRİLMEDİ).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import ortak017 as O

HORIZONS = (5, 10, 20)
CIVI_HEDEF = 0.0645     # pk.py'nin kayıtlı hedefi; kart metni ≈0.0642 diyor (aynı çivi, aynı
CIVI_TOL = 0.005        # tolerans). İKİSİ DE BU TURDA DEĞİŞTİRİLMEDİ.
RVOL_ESIK = 2.5         # kart: rvol>=2.5 bölgesi (üçgenin 0'ladığı sağ kol)


def population() -> tuple[list, dict]:
    """wp2/pk.py ile BİREBİR: cf entered=True (near_miss dâhil) + cf_open."""
    rows, acc = [], {"cf_satir": 0, "cf_girilmemis": 0, "cf_eksik_alan": 0,
                     "open_satir": 0, "open_eksik_alan": 0}
    with open(O.LIVE_STATE / "counterfactuals.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            acc["cf_satir"] += 1
            if not r.get("entered"):
                acc["cf_girilmemis"] += 1
                continue
            if not r.get("ticker") or not r.get("date"):
                acc["cf_eksik_alan"] += 1
                continue
            rows.append({"kaynak": "cf", "ticker": str(r["ticker"]).upper(),
                         "date": str(r["date"])[:10], "near_miss": bool(r.get("near_miss"))})
    with open(O.LIVE_STATE / "cf_open.json") as fh:
        for r in json.load(fh):
            acc["open_satir"] += 1
            if not r.get("ticker") or not r.get("date"):
                acc["open_eksik_alan"] += 1
                continue
            rows.append({"kaynak": "cf_open", "ticker": str(r["ticker"]).upper(),
                         "date": str(r["date"])[:10], "near_miss": bool(r.get("near_miss"))})
    return rows, acc


def cf_tablosu(pan):
    """cf katmanı satırlarını bar paneline eşle (pozitif kontrol + EDG-002 yeniden üretimi)."""
    rows, pop_acc = population()
    idx_cache = {t: {d: i for i, d in enumerate(v["dates"])} for t, v in pan.items()}
    pk_rows, elem = [], {"bar_yok_sembol": 0, "bar_yok_tarih": 0, "kabul": 0}
    for r in rows:
        f = pan.get(r["ticker"])
        if f is None:
            elem["bar_yok_sembol"] += 1
            continue
        i = idx_cache[r["ticker"]].get(r["date"])
        if i is None:
            elem["bar_yok_tarih"] += 1
            continue
        elem["kabul"] += 1
        rec = dict(r)
        for k in ("rvol20", "rvol20_medyan"):
            v = f[k][i]
            rec[k] = None if not np.isfinite(v) else float(v)
        for h in HORIZONS:
            v = f[f"fwd{h}"][i]
            rec[f"fwd{h}"] = None if not np.isfinite(v) else float(v)
            cv = f[f"chain{h}"][i]
            rec[f"chain{h}"] = None if not np.isfinite(cv) else float(cv)
        pk_rows.append(rec)
    return pd.DataFrame(pk_rows), pop_acc, elem


def pozitif_kontrol(pan) -> tuple[dict, pd.DataFrame]:
    PKD, pop_acc, elem = cf_tablosu(pan)
    KAT = PKD[(PKD["kaynak"] == "cf") & (~PKD["near_miss"])]
    out = {"aciklama": "KART GUARD'I — ham rvol20 @20 cf-katman IC çivisi. AYNI boru hattı "
                       "(bars_integrity DIŞLAMALI yol): max_olcum 0.0645, resmom 0.0637, "
                       "pullback 0.0642, WP2/EDG-016 0.0642. Çivi tutmazsa boru hattı GEÇERSİZ "
                       "ve HİÇBİR hücre için sayı yazılmaz.",
           "katman": "counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)",
           "populasyon_muhasebesi": pop_acc, "eslesme_muhasebesi": elem}
    for h in HORIZONS:
        sub = KAT[["rvol20", f"fwd{h}", "date"]].dropna()
        out[str(h)] = O.ic_with_ci(sub["rvol20"].to_numpy(float),
                                   sub[f"fwd{h}"].to_numpy(float), sub["date"].to_numpy())
    civi = out["20"]["ic"]
    out["civi_hedef"] = CIVI_HEDEF
    out["civi_olculen"] = civi
    out["civi_sapma"] = None if civi is None else O._r6(abs(civi - CIVI_HEDEF))
    out["tolerans"] = CIVI_TOL
    out["GECTI"] = None if civi is None else bool(abs(civi - CIVI_HEDEF) <= CIVI_TOL)
    try:
        ref = json.load(open(O.LIVE_STATE / "component_ic.json"))
        out["defterdeki_deger_cf_rvol20"] = {h: ref["tablo"]["cf"]["rvol20"][h]["ic"]
                                             for h in ("5", "10", "20")}
    except Exception as e:
        out["defterdeki_deger_cf_rvol20"] = f"okunamadı: {type(e).__name__}: {e}"

    # --- GENİŞLETİLMİŞ ÜRETİM KONTROLÜ: EDG-002'nin ÖLÇÜLMÜŞ nesnesi (yeni K DEĞİL) ---
    # s1_retro/RAPOR.md §3: "üçgenin 0 puan verdiği rvol>=2.5 bölgesi — n=433, ort. 20-bar getiri
    # +1.61%, CI [+0.64, +2.54]". Bu satır HÜKÜM TAŞIMAZ; boru hattının EDG-002'nin sayısını da
    # yeniden ürettiğini gösterir (aynı katman, aynı HAM getiri tanımı, birebir).
    reg = KAT[KAT["rvol20"] >= RVOL_ESIK][["rvol20", "fwd20", "date"]].dropna()
    out["edg002_bolge_yeniden_uretimi"] = {
        "tanim": f"cf katmanı, rvol20>={RVOL_ESIK}, HAM 20-bar ileri getiri (taban DÜŞÜLMEDİ) — "
                 "EDG-002 raporundaki nesnenin BİREBİR aynısı. Yeni K harcamaz: ölçülmüş bir "
                 "nesnenin yeniden üretimidir, yeni bir deneme değil.",
        "hedef_edg002": {"n": 433, "ort": 0.0161, "ci": {"lo": 0.0064, "hi": 0.0254}},
        "olculen": O.mean_with_ci(reg["fwd20"].to_numpy(float), reg["date"].to_numpy()),
    }
    return out, PKD


def pk4(pan, PKD) -> dict:
    out = {"tanim": "close[t+h]/close[t]-1 ile aradaki GÜNLÜK getirilerin bileşiği ÖZDEŞ olmalı. "
                    "Takvim kapısı / integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma "
                    "bir gün kaysaydı özdeşlik bozulurdu.",
           "kapsam": "pozitif kontrol satırları + TÜM bar paneli (her sembol, her bar)"}
    for h in HORIZONS:
        d0 = []
        s2 = PKD[[f"fwd{h}", f"chain{h}"]].dropna()
        if len(s2):
            d0.append((s2[f"fwd{h}"] - s2[f"chain{h}"]).abs().to_numpy())
        for t, v in pan.items():
            a, b = v[f"fwd{h}"], v[f"chain{h}"]
            m = np.isfinite(a) & np.isfinite(b)
            if m.any():
                d0.append(np.abs(a[m] - b[m]))
        allv = np.concatenate(d0)
        out[f"fwd{h}"] = {"n": int(len(allv)), "maks_mutlak_fark": O._r6(allv.max()),
                          "gecti": bool(allv.max() < 1e-9)}
    out["gecti"] = bool(all(out[f"fwd{h}"]["gecti"] for h in HORIZONS))
    return out


def pk5(pan) -> dict:
    """PK5 — bu KARTIN kullandığı özdeşlikler.

    KAPSAM BEYANI: WP2 dalgasının PK5-A (as-of geriye-bakışsızlık), PK5-B (split bazı) ve PK5-D
    (fundamentals as-of) bacakları BU KARTTA UYGULANMAZ — kart yalnız OHLCV kullanır, hiçbir
    as-of/fundamentals serisi okumaz (kart notu: "yeni as-of gerektirmez, yalnız OHLCV").
    Uygulanmayan bir bekçiyi "geçti" diye raporlamak UYDURMA olurdu. Bu kartın PK5'i üç bacaktır:
      C  — hızlı ortalama-bootstrap ≡ satır-toplayan kanonik yol
      E  — hızlı Spearman ≡ kanonik analytics.spearman_ic
      F  — vektörel temiz-taban maskesi ≡ kanonik meridian.olcum_araclari.temiz_taban
    """
    semboller = sorted(pan)
    out = {"kapsam_beyani": pk5.__doc__.strip()}

    # (C) hızlı ortalama-bootstrap yolu ≡ satır-toplayan yol
    d = pan[semboller[0]]
    m = np.isfinite(d["fwd20"])
    yy, dd = d["fwd20"][m], d["dates"][m]
    uniq, inv = np.unique(dd, return_inverse=True)
    rows_by_date = [np.where(inv == i)[0] for i in range(len(uniq))]
    sums = np.bincount(inv, weights=yy, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    nd_ = len(uniq)
    n_blok = int(np.ceil(nd_ / O.BLOCK))
    c_max, c_n = 0.0, 0
    for _ in range(50):
        bas = O.RNG.integers(0, max(nd_ - O.BLOCK, 0) + 1, n_blok)
        gun = np.concatenate([np.arange(b, b + O.BLOCK) for b in bas])[:nd_]
        idx = np.concatenate([rows_by_date[g] for g in gun])
        v1 = float(np.mean(yy[idx]))
        v2 = float(sums[gun].sum() / cnts[gun].sum())
        c_max = max(c_max, abs(v1 - v2))
        c_n += 1
    out["C_hizli_ortalama"] = {
        "n_ornek": c_n, "maks_mutlak_fark": O._r6(c_max), "gecti": bool(c_n > 0 and c_max < 1e-12),
        "tanim": "mean_block_boot (gün-toplamı/gün-adedi) ile block_boot (satır toplayıp mean) "
                 "AYNI gün dizisinde birebir aynı sayıyı vermeli"}

    # (E) hızlı Spearman ≡ kanonik analytics.spearman_ic
    rng = np.random.default_rng(17)
    xs, ys = [], []
    for t in semboller[:40]:
        v = pan[t]
        mm = np.isfinite(v["rvol20"]) & np.isfinite(v["fwd20"])
        xs.append(v["rvol20"][mm])
        ys.append(v["fwd20"][mm])
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    farklar = []
    for n in (5000, 50000, len(xs)):
        i = rng.choice(len(xs), size=n, replace=False) if n < len(xs) else np.arange(len(xs))
        kan = O.spearman_ic(list(zip(xs[i].tolist(), ys[i].tolist())))
        hiz = O.spearman_fast(xs[i], ys[i])
        farklar.append({"n": int(n), "kanonik": O._r6(kan), "hizli": O._r6(hiz),
                        "mutlak_fark": O._r6(abs(kan - hiz))})
    out["E_hizli_spearman"] = {
        "olcumler": farklar, "gecti": bool(all(f["mutlak_fark"] < 1e-9 for f in farklar)),
        "tanim": "IC bootstrap'ının hızlı yolu kanonik analytics.spearman_ic ile BİREBİR aynı "
                 "sayıyı vermeli (bağ kırma dâhil)"}
    return out


def pk5_f_temiz_taban(sym_ad, sym_kod, seans, olay, h, n_ornek=120_000) -> dict:
    """(F) VEKTÖREL temiz-taban maskesi ≡ KANONİK meridian.olcum_araclari.temiz_taban.

    Kanonik fonksiyon satır × olay döngüsüdür; 1,2 milyon satırda saatler sürerdi. Bu yüzden
    özdeşlik RASTGELE bir ALT ÖRNEKTE sınanır ve alt örneğin büyüklüğü ADIYLA raporlanır
    ("tümünde sınandı" denmez — sınanmadı). Gün birimi: SEANS ORDİNALİ (int) → temiz_taban
    `gun_birimi` alanında 'sira/bar indeksi' der; pencere (h, h) da o birimdedir.
    """
    rng = np.random.default_rng(19)
    n = len(sym_kod)
    k = min(n_ornek, n)
    idx = rng.choice(n, size=k, replace=False)
    hizli = O.temiz_maske(sym_kod, seans, olay, h)[idx]

    olay_gunleri = {}
    for s in range(int(sym_kod.max()) + 1):
        ev = seans[(sym_kod == s) & olay]
        olay_gunleri[sym_ad[s]] = [int(x) for x in np.sort(ev)]
    satirlar = [(sym_ad[sym_kod[i]], int(seans[i]), 0.0) for i in idx]
    rap = O.temiz_taban(satirlar, olay_gunleri, (h, h))
    kanonik = np.zeros(k, bool)
    kanonik_kimlik = {(a, b) for a, b, _ in rap["taban"]}
    for j, i in enumerate(idx):
        kanonik[j] = (sym_ad[sym_kod[i]], int(seans[i])) in kanonik_kimlik
    ayrisan = int((hizli != kanonik).sum())
    return {"h": h, "n_ornek": int(k), "n_toplam_satir": int(n), "ayrisan": ayrisan,
            "gecti": bool(ayrisan == 0),
            "kanonik_temiz": int(kanonik.sum()), "hizli_temiz": int(hizli.sum()),
            "kanonik_kirlilik_orani": rap["kirlilik_orani"],
            "kanonik_gun_birimi": rap["gun_birimi"], "kanonik_pencere": rap["pencere"],
            "kanonik_n_olay": rap["n_olay"], "kanonik_n_olaysiz_kimlik": rap["n_olaysiz_kimlik"],
            "kanonik_n_cozulemeyen": rap["n_cozulemeyen"], "kanonik_uyari": rap["uyari"],
            "tanim": "ortak017.temiz_maske (vektörel) ile meridian.olcum_araclari.temiz_taban "
                     "(kanonik, satır×olay döngüsü) AYNI satırları temiz saymalı"}
