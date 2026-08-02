"""EDG-2026-020 · BEKÇİLER — POZİTİF KONTROL + PIT-ASSERT + PK4 + PK5 + temiz_taban özdeşliği.

KART GUARD'LARI (harfiyen):
  * "pozitif kontrol: rvol20 @20 IC ≈0.0642 çivisi sandbox'ta yeniden üretilir (üretilemezse DUR)"
  * "PIT: yalnız e<=t; gelecek-tarih okuyan tek satır bile ihlaldir (test/assert ile çivilenir)"
  * "olay-takvimi kanıtı ölçüm klasörüne arşivlenir (scratchpad-kaybı sınıfı — EDG-016 dersi)"
  * "PK4/PK5 + temiz_taban zorunlu; eşik-dilbilgisi"

Bu dosya İLK KOŞAN İŞTİR. Çivi tutmazsa ya da PIT assert'i düşerse k020.py hiçbir hücre ölçmez.
Şablon: research/olcumler/wp1_rvol_form/pk017.py (aynı katman, aynı çivi, aynı tolerans).
"""
from __future__ import annotations

import datetime as _dt
import json

import numpy as np
import pandas as pd

import ortak020 as O

HORIZONS = (5, 10, 20)
CIVI_HEDEF = 0.0645     # pk017.py'nin kayıtlı hedefi; kart metni ≈0.0642 diyor (AYNI çivi).
CIVI_TOL = 0.005        # İKİSİ DE BU TURDA DEĞİŞTİRİLMEDİ.


# ==================================================================================================
# POZİTİF KONTROL — cf katmanı ham rvol20 @20 IC (pk017.py deseni, BİREBİR)
# ==================================================================================================
def population() -> tuple[list, dict]:
    """pk017/wp2-pk ile BİREBİR: cf entered=True (near_miss DÂHİL) + cf_open, SATIR düzeyi."""
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
        v = f["rvol20"][i]
        rec["rvol20"] = None if not np.isfinite(v) else float(v)
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
                       "pullback 0.0642, WP2/EDG-016 0.0642, EDG-017 0.0642, EDG-011 0.0642. "
                       "Çivi tutmazsa boru hattı GEÇERSİZ ve HİÇBİR hücre için sayı yazılmaz.",
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
    except Exception as e:                                   # noqa: BLE001 — sayılır, yutulmaz
        out["defterdeki_deger_cf_rvol20"] = f"okunamadı: {type(e).__name__}: {e}"
    return out, PKD


# ==================================================================================================
# PIT-ASSERT — kartın en sert guard'ı, ÜÇ BAĞIMSIZ BACAK
# ==================================================================================================
def pit_assert(takvim: dict, aday: list, pan: dict) -> dict:
    """"gelecek-tarih (e>t) erişimi koda YAPISAL kapalı" iddiasının KANITI.

    Bacaklar:
      (1) YAPISAL BEYAN — `ortak020.gecikme_gunu` searchsorted(side='right') ile diziyi t'de
          KESER; yalnız `ev[:j]` diliminin son öğesi okunur. Fonksiyonun içindeki satır-başına
          assert bu turda 0 kez tetiklendi (tetiklenseydi AssertionError ile ölçüm dururdu).
      (2) KESME-DEĞİŞMEZLİĞİ — ASIL KANIT. Her aday satırı için takvim O SATIRIN t'sinde kesilir
          (yalnız e<=t olan olaylar bırakılır) ve gecikme YENİDEN hesaplanır. Tam takvimle
          kesilmiş takvim BİREBİR aynı sonucu vermelidir: veriyorsa, gelecek tarihlerin sonuca
          KATKISI SIFIRDIR — yani hiçbir gelecek tarih okunmuş olamaz.
      (3) BAĞIMSIZ SAF-PYTHON İKİZ — `gecikme_gunu_saf` (liste taraması, farklı kod yolu) aynı
          sayıyı vermeli.

    Ayrıca NEGATİF KONTROL: kasten gelecek-dallı bir hesap yapılırsa sonucun DEĞİŞTİĞİ gösterilir
    — yoksa "kapı tuttu" ifadesi boş bir tavtolojidir (kapının bir şeyi gerçekten kestiğini
    kanıtlamayan bir kapı, kapı değildir). NEGATİF KONTROL SAYISI HÜKME GİRMEZ ve in_play
    hesabında KULLANILMAZ; yalnız kapının etkin olduğunu gösterir.
    """
    olay_ord = {t: np.array([O.iso_ord(d) for d in ds], dtype=np.int64)
                for t, ds in takvim.items()}
    for t in olay_ord:
        olay_ord[t].sort()

    # ---- vektörel yol (asıl hesap yolu) ----
    tickers = np.array([a[0] for a in aday])
    tords = np.array([O.iso_ord(a[1]) for a in aday], dtype=np.int64)
    gec = np.full(len(aday), -1, dtype=np.int64)
    for t in np.unique(tickers):
        m = np.nonzero(tickers == t)[0]
        ev = olay_ord.get(t)
        gec[m] = O.gecikme_gunu(ev if ev is not None else np.empty(0, np.int64), tords[m])

    # ---- (2) KESME-DEĞİŞMEZLİĞİ (TÜM satırlarda, alt örnek DEĞİL) ----
    kesme_ayrisan = 0
    for i, (tk, _ds) in enumerate(aday):
        ev = olay_ord.get(tk)
        if ev is None or ev.size == 0:
            kesilmis = np.empty(0, np.int64)
        else:
            kesilmis = ev[ev <= tords[i]]          # TAKVİM t'DE KESİLDİ: gelecek fizikî olarak YOK
        v = O.gecikme_gunu(kesilmis, tords[i:i + 1])[0]
        if int(v) != int(gec[i]):
            kesme_ayrisan += 1

    # ---- (3) BAĞIMSIZ SAF-PYTHON İKİZ ----
    saf_ayrisan = 0
    for i, (tk, _ds) in enumerate(aday):
        ev = olay_ord.get(tk)
        v = O.gecikme_gunu_saf([int(x) for x in (ev if ev is not None else [])], int(tords[i]))
        if int(v) != int(gec[i]):
            saf_ayrisan += 1

    # ---- NEGATİF KONTROL (kapının etkinliği; HÜKME GİRMEZ, in_play'de KULLANILMAZ) ----
    #      "en yakın olay, YÖNÜ ne olursa olsun" hesabı kaç satırda FARKLI bir sayı verirdi?
    neg_farkli = 0
    for i, (tk, _ds) in enumerate(aday):
        ev = olay_ord.get(tk)
        if ev is None or ev.size == 0:
            continue
        iki_yonlu = int(np.min(np.abs(ev - tords[i])))
        if iki_yonlu != int(gec[i]):
            neg_farkli += 1

    # ---- kapsama muhasebesi ----
    takvimsiz = int(sum(1 for tk, _ in aday if tk not in takvim))
    olaysiz_gecmis = int((gec < 0).sum())
    return {
        "bacak_1_yapisal": {
            "tanim": "gecikme_gunu: searchsorted(side='right') → ev[:j] dilimi; yalnız o dilimin "
                     "SON öğesi okunur. j==0 satırlarda diziye HİÇ dokunulmaz (maskeli indeksleme).",
            "satir_basi_assert_tetiklendi": 0,
            "gecti": True},
        "bacak_2_kesme_degismezligi": {
            "tanim": "Her satır için takvim O SATIRIN t'sinde KESİLİR (ev[ev<=t]) ve gecikme "
                     "yeniden hesaplanır. Fark 0 ⇒ gelecek tarihlerin sonuca katkısı SIFIR.",
            "n_satir": len(aday), "ayrisan": kesme_ayrisan, "alt_ornek_mi": False,
            "gecti": bool(kesme_ayrisan == 0)},
        "bacak_3_bagimsiz_saf_python": {
            "tanim": "gecikme_gunu_saf (liste taraması, ayrı kod yolu) ile birebir aynı sayı.",
            "n_satir": len(aday), "ayrisan": saf_ayrisan, "gecti": bool(saf_ayrisan == 0)},
        "negatif_kontrol_kapi_etkin_mi": {
            "tanim": "İKİ YÖNLÜ (EDG-011'in |t−e| lafzı) hesap kaç satırda FARKLI sayı verirdi? "
                     "0 çıksaydı kapı hiçbir şeyi kesmiyor demekti ve 'PIT-temiz' beyanı boş "
                     "olurdu. BU SAYI HÜKME GİRMEZ ve in_play hesabında KULLANILMAZ.",
            "n_satir_farkli": neg_farkli,
            "oran": O._r6(neg_farkli / len(aday)) if aday else None,
            "kapi_etkin": bool(neg_farkli > 0)},
        "kapsama": {"aday_satiri": len(aday), "takvimde_olmayan_sembol_satiri": takvimsiz,
                    "gecmis_olayi_olmayan_satir": olaysiz_gecmis},
        "GECTI": bool(kesme_ayrisan == 0 and saf_ayrisan == 0),
    }


# ==================================================================================================
# PK4 — YOL TUTARLILIĞI
# ==================================================================================================
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


# ==================================================================================================
# PK5 — ÖZDEŞLİKLER
# ==================================================================================================
def pk5(pan, takvim: dict, aday: list) -> dict:
    """KAPSAM BEYANI: WP2 dalgasının PK5-B (split bazı) ve PK5-D (fundamentals as-of) bacakları
    BU KARTTA UYGULANMAZ — kart yalnız OHLCV + olay TARİHİ kullanır, hiçbir fundamentals/as-of
    serisi okumaz. Uygulanmayan bir bekçiyi 'geçti' diye raporlamak UYDURMA olurdu.

    Bu kartın PK5'i BEŞ bacaktır:
      A — rvol20 GERİYE-BAKIŞSIZ: tam seri ile df.iloc[:i+1] kesilmiş seride aynı değer
      C — hızlı ortalama-bootstrap ≡ satır-toplayan kanonik yol
      E — hızlı Spearman ≡ kanonik analytics.spearman_ic
      F — in_play maskesi ≡ KANONİK meridian.olcum_araclari.temiz_taban(pencere=(0,P)) tümleyeni
      G — takvim yükleyici: arşivlenmiş JSONL ayrıştırması ≡ deponun kendi earnings._load()'u
    """
    semboller = sorted(pan)
    out = {"kapsam_beyani": pk5.__doc__.strip()}

    # ---- (A) rvol20 GERİYE-BAKIŞSIZ ----
    rng = np.random.default_rng(20260803)
    from meridian import indicators as ind
    a_max, a_n = 0.0, 0
    for t in rng.choice(semboller, size=min(8, len(semboller)), replace=False):
        v = pan[t]
        n = len(v["volume"])
        for i in rng.choice(np.arange(60, n), size=min(4, max(1, n - 60)), replace=False):
            kesik = ind.rvol20(pd.Series(v["volume"][:i + 1])).to_numpy(float)[-1]
            tam = v["rvol20"][i]
            if np.isfinite(tam) or np.isfinite(kesik):
                a_max = max(a_max, abs(float(np.nan_to_num(tam)) - float(np.nan_to_num(kesik))))
                a_n += 1
    out["A_rvol20_geriye_bakissiz"] = {
        "n": a_n, "maks_mutlak_fark": O._r6(a_max), "gecti": bool(a_n > 0 and a_max < 1e-12),
        "tanim": "indicators.rvol20 TAM seride ve df.iloc[:i+1] KESİLMİŞ seride AYNI değeri vermeli"}

    # ---- (C) hızlı ortalama-bootstrap ≡ satır-toplayan yol ----
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
        c_max = max(c_max, abs(float(np.mean(yy[idx])) - float(sums[gun].sum() / cnts[gun].sum())))
        c_n += 1
    out["C_hizli_ortalama"] = {
        "n_ornek": c_n, "maks_mutlak_fark": O._r6(c_max), "gecti": bool(c_n > 0 and c_max < 1e-12),
        "tanim": "mean_block_boot (gün-toplamı/gün-adedi) ile block_boot (satır toplayıp mean) "
                 "AYNI gün dizisinde birebir aynı sayıyı vermeli"}

    # ---- (E) hızlı Spearman ≡ kanonik ----
    rng2 = np.random.default_rng(17)
    xs, ys = [], []
    for t in semboller[:40]:
        v = pan[t]
        mm = np.isfinite(v["rvol20"]) & np.isfinite(v["fwd20"])
        xs.append(v["rvol20"][mm])
        ys.append(v["fwd20"][mm])
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    farklar = []
    for n in (5000, 50000, len(xs)):
        i = rng2.choice(len(xs), size=n, replace=False) if n < len(xs) else np.arange(len(xs))
        kan = O.spearman_ic(list(zip(xs[i].tolist(), ys[i].tolist())))
        hiz = O.spearman_fast(xs[i], ys[i])
        farklar.append({"n": int(n), "kanonik": O._r6(kan), "hizli": O._r6(hiz),
                        "mutlak_fark": O._r6(abs(kan - hiz))})
    out["E_hizli_spearman"] = {
        "olcumler": farklar, "gecti": bool(all(f["mutlak_fark"] < 1e-9 for f in farklar)),
        "tanim": "IC bootstrap'ının hızlı yolu kanonik analytics.spearman_ic ile BİREBİR aynı"}

    # ---- (F) in_play maskesi ≡ KANONİK temiz_taban(pencere=(0,P)) tümleyeni ----
    #  temiz_taban KİRLİ sayar:  -once <= (gun - olay) <= sonra.  once=0, sonra=P
    #  ⇒ 0 <= t - e <= P  — bu KARTIN in_play tanımının TA KENDİSİ. İkisi ayrışırsa in_play
    #    tanımı deponun kanonik pencere aritmetiğinden sapmış demektir.
    olay_ord = {t: sorted(O.iso_ord(d) for d in ds) for t, ds in takvim.items()}
    f_bacak = {}
    for P in O.PENCERELER:
        gec = np.array([O.gecikme_gunu_saf(olay_ord.get(tk, []), O.iso_ord(ds))
                        for tk, ds in aday], dtype=np.int64)
        hizli_inplay = (gec >= 0) & (gec <= P)
        satirlar = [(tk, ds, 0.0) for tk, ds in aday]
        rap = O.temiz_taban(satirlar, takvim, (0, P))
        kanonik_temiz = {(k, g) for k, g, _ in rap["taban"]}
        kanonik_inplay = np.array([(tk, ds) not in kanonik_temiz for tk, ds in aday])
        ayrisan = int((hizli_inplay != kanonik_inplay).sum())
        f_bacak[str(P)] = {
            "ayrisan": ayrisan, "gecti": bool(ayrisan == 0),
            "hizli_inplay": int(hizli_inplay.sum()), "kanonik_inplay": int(kanonik_inplay.sum()),
            "kanonik_kirlilik_orani": rap["kirlilik_orani"], "kanonik_gun_birimi": rap["gun_birimi"],
            "kanonik_pencere": rap["pencere"], "kanonik_n_olay": rap["n_olay"],
            "kanonik_n_olaysiz_kimlik": rap["n_olaysiz_kimlik"],
            "kanonik_n_cozulemeyen": rap["n_cozulemeyen"], "kanonik_n_temiz": rap["n_temiz"],
            "kanonik_uyari": rap["uyari"]}
    out["F_temiz_taban_ozdesligi"] = {
        "tanim": "in_play(0<=t−e<=P) maskesi, KANONİK olcum_araclari.temiz_taban(pencere=(0,P)) "
                 "fonksiyonunun KİRLİ saydığı satırlarla BİREBİR aynı olmalı (aynı pencere "
                 "aritmetiği, iki bağımsız uygulama). Gün birimi TAKVİM GÜNÜdür.",
        "pencereler": f_bacak,
        "gecti": bool(all(v["gecti"] for v in f_bacak.values()))}

    # ---- (G) takvim yükleyici özdeşliği ----
    from meridian import earnings as earn
    earn._CACHE_MTIME = None                          # önbelleği tazele (kum havuzu CSV'si yeni)
    kanonik_tak = earn._load()
    ayr_sembol = int(len(set(takvim) ^ set(kanonik_tak)))
    ayr_tarih = int(sum(len(set(takvim.get(t, [])) ^ set(kanonik_tak.get(t, [])))
                        for t in set(takvim) | set(kanonik_tak)))
    out["G_takvim_yukleyici"] = {
        "bagimsiz_sembol": len(takvim), "kanonik_sembol": len(kanonik_tak),
        "ayrisan_sembol": ayr_sembol, "ayrisan_tarih": ayr_tarih,
        "gecti": bool(ayr_sembol == 0 and ayr_tarih == 0),
        "tanim": "arşivlenmiş JSONL ayrıştırması (ortak020.takvim_yukle) ile DEPONUN kendi "
                 "earnings._load()'u (kum havuzu CSV'sinden) BİREBİR aynı takvimi vermeli"}

    out["gecti"] = bool(all(out[k]["gecti"] for k in
                            ("A_rvol20_geriye_bakissiz", "C_hizli_ortalama", "E_hizli_spearman",
                             "F_temiz_taban_ozdesligi", "G_takvim_yukleyici")))
    return out


# ==================================================================================================
def main() -> dict:
    print("[pk020] barlar yükleniyor…", flush=True)
    pan, bar_acc = O.bars_cached()
    print(f"[pk020] bar sembolü: {bar_acc['yuklendi']}/{bar_acc['istenen']}", flush=True)

    print("[pk020] takvim arşivden okunuyor…", flush=True)
    takvim, tak_acc = O.takvim_yukle()
    n_csv = O.takvim_csv_yaz(takvim, O.config.STATE / "earnings.csv")
    print(f"[pk020] takvim: {tak_acc['sembol']} sembol · {tak_acc['olay_gunu']} olay-günü · "
          f"kum havuzu CSV {n_csv} satır", flush=True)

    aday, aday_acc = O.aday_havuzu()
    aday = [(t, d) for t, d in aday if t in pan and d in set(pan[t]["dates"].tolist())]
    print(f"[pk020] bar eşleşen aday-gün: {len(aday)}", flush=True)

    print("[pk020] pozitif kontrol…", flush=True)
    pk, PKD = pozitif_kontrol(pan)
    print(f"[pk020]   çivi={pk['civi_olculen']} hedef={CIVI_HEDEF} GEÇTİ={pk['GECTI']}", flush=True)

    print("[pk020] PIT-assert…", flush=True)
    pit = pit_assert(takvim, aday, pan)
    print(f"[pk020]   kesme-değişmezliği ayrışan={pit['bacak_2_kesme_degismezligi']['ayrisan']} · "
          f"saf-python ayrışan={pit['bacak_3_bagimsiz_saf_python']['ayrisan']} · "
          f"GEÇTİ={pit['GECTI']}", flush=True)

    print("[pk020] PK4…", flush=True)
    p4 = pk4(pan, PKD)
    print("[pk020] PK5…", flush=True)
    p5 = pk5(pan, takvim, aday)

    out = {"kart": "EDG-2026-020", "olcum_zamani": _dt.datetime.now(_dt.timezone.utc).isoformat(),
           "kod_surumu": O.kod_surumu_damgasi(O.REPO), "motor_damgasi": O.motor_damgasi(),
           "muhur": {"config_STATE": str(O.config.STATE), "config_BARS": str(O.config.BARS),
                     "canli_state": str(O.LIVE_STATE),
                     "beyan": "config.STATE kum havuzuna çevrildi; barlar CANLI önbellekten "
                              "SALT-OKUNUR okunur; kum havuzu earnings.csv TARİHSEL takvimle "
                              "dolduruldu (canlı dosyaya TEK BAYT yazılmadı)"},
           "bar_muhasebesi": bar_acc, "takvim_muhasebesi": tak_acc,
           "aday_muhasebesi": {**aday_acc, "bar_eslesen_aday_gun": len(aday)},
           "pozitif_kontrol": pk, "pit_assert": pit, "pk4": p4, "pk5": p5,
           "KAPILAR": {"pozitif_kontrol": pk["GECTI"], "pit_assert": pit["GECTI"],
                       "pk4": p4["gecti"], "pk5": p5["gecti"]}}
    out["DUR"] = not all(v for v in out["KAPILAR"].values())
    O.json_yaz(O.KLASOR / "pk_020.json", out)
    print(json.dumps(out["KAPILAR"], ensure_ascii=False), flush=True)
    print(f"[pk020] DUR={out['DUR']}", flush=True)
    return out


if __name__ == "__main__":
    r = main()
    raise SystemExit(4 if r["DUR"] else 0)
