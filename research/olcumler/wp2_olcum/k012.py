"""EDG-2026-012 · NET HİSSE İHRACI — SALT-ÖLÇÜM, SANDBOX.

Kart: research/cards/EDG-2026-012-net-issuance.yaml (status: registered). KART DIŞINA ÖLÇÜM YOK.
Eşikler karttan; kart dosyasına DOKUNULMAZ. Hüküm ÖNERİSİ üretilir, hükmü Rol-1 işler.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import ortak as O

HORIZONS = (20, 60)             # kart: ileri getiri 20/60g
LOOKBACK = 252                  # kart: net_ihrac(t) = shares(t)/shares(t-252ig) − 1
DILIM_PCT = 0.20                # kart parameter_grid: iki uç dilim %20
MIN_SEMBOL_AY = 3000            # kart kill#3: geçerli sembol-ay < 3000 → askı


def panel(pan, ser, OBS):
    """Aylık gözlem paneli: her (gözlem günü, sembol) için net_ihrac + ileri getiriler."""
    parts, acc = [], {"sembol": 0, "gozlem_hucre": 0, "idx_yetersiz": 0,
                      "neden_sayimi": {}, "kirik_dusen": 0, "gecerli": 0,
                      "filed_gecikme_gun": [], "yedek_etiket_hucre": 0}
    for sym, v in pan.items():
        d = v["dates"]
        pos = np.searchsorted(d, OBS)
        pos_c = np.minimum(pos, len(d) - 1)
        ok = (pos < len(d)) & (d[pos_c] == OBS)
        idx = pos[ok]
        tdates = OBS[ok]
        acc["sembol"] += 1
        acc["gozlem_hucre"] += int(len(idx))
        s = ser.get(sym)
        yeter = idx >= LOOKBACK
        acc["idx_yetersiz"] += int((~yeter).sum())
        idx, tdates = idx[yeter], tdates[yeter]
        if len(idx) == 0:
            continue
        row = {"date": tdates, "ticker": sym}
        for h in HORIZONS:
            row[f"fwd{h}"] = v[f"fwd{h}"][idx]
        if s is None:
            row["net"] = np.full(len(idx), np.nan)
            row["neden"] = "anlik_hisse_serisi_yok"
            row["filed"] = ""
            acc["neden_sayimi"]["anlik_hisse_serisi_yok"] = \
                acc["neden_sayimi"].get("anlik_hisse_serisi_yok", 0) + len(idx)
        else:
            tprev = d[idx - LOOKBACK]
            s2, f2, n2 = s.asof(tdates)
            s1, f1, n1 = s.asof(tprev)
            fin = np.isfinite(s1) & np.isfinite(s2)
            kirik = np.zeros(len(idx), bool)
            if fin.any():
                kirik[fin] = s.kirik_arada(f1[fin].astype(str), f2[fin].astype(str))
            net = np.where(fin & ~kirik, s2 / np.where(fin, s1, np.nan) - 1.0, np.nan)
            neden = np.where(fin & ~kirik, "",
                             np.where(kirik & fin, "aciklanamayan_5x_sinir",
                                      np.where(np.isfinite(s2), "t-252_asof_yok:" + n1.astype(str),
                                               "t_asof_yok:" + n2.astype(str))))
            for k, c in zip(*np.unique(neden[neden != ""], return_counts=True)):
                acc["neden_sayimi"][str(k)] = acc["neden_sayimi"].get(str(k), 0) + int(c)
            acc["kirik_dusen"] += int(kirik.sum())
            row["net"] = net
            row["neden"] = neden
            row["filed"] = f2
            g = (pd.to_datetime(tdates[fin]) - pd.to_datetime(f2[fin].astype(str))).days
            acc["filed_gecikme_gun"].extend(g.tolist())
            tg = s.kaynak_tag[s.idx_asof(tdates)] if len(s.filed) else None
            if tg is not None:
                acc["yedek_etiket_hucre"] += int(np.sum(tg != s.birincil_tag))
        parts.append(pd.DataFrame(row))
    D = pd.concat(parts, ignore_index=True)
    acc["gecerli"] = int(D["net"].notna().sum())
    gg = np.array(acc.pop("filed_gecikme_gun"), float)
    acc["filed_gecikme_ozeti"] = ({"n": int(len(gg)), "medyan": O._r6(np.median(gg)),
                                   "p10": O._r6(np.percentile(gg, 10)),
                                   "p90": O._r6(np.percentile(gg, 90)),
                                   "maks": O._r6(gg.max()), "negatif_n": int((gg < 0).sum())}
                                  if len(gg) else {"n": 0, "neden": "gözlem yok"})
    return D, acc


def main() -> None:
    pan, bar_acc = O.bars_cached()
    S = O._shares_ham()
    ser, birincil, sh_acc = O.build_hisse(S)
    sh_acc["fiziksel_bekci"] = O.fiziksel_bekci(ser, pan)
    takvim = O.ortak_takvim(pan)
    OBS = O.ay_sonu_gunleri(takvim)
    print(f"== 012: {len(OBS)} aylık gözlem günü, {len(pan)} sembol ==")

    D, pacc = panel(pan, ser, OBS)
    sonuc = {
        "kart": "EDG-2026-012", "aile": "net_share_issuance",
        "olcum_tarihi": pd.Timestamp.now("UTC").isoformat(), "sandbox": str(O.SANDBOX),
        "DURUM": None,
        "kart_metni_uygulamasi": {
            "as_of_shares": "unit=shares & val>0 & donem_turu=anlik & tag ∈ {dei:Entity"
                            "CommonStockSharesOutstanding, us-gaap:CommonStockSharesOutstanding}; "
                            "Issued KULLANILMADI (hazine farkı), ağırlıklı-ortalama seriler SEVİYE "
                            "olarak KULLANILMADI. Aynı dosyalamada birden çok `end` varsa EN TAZE "
                            "`end`. Birincil etiket: dei (>=8 farklı filed varsa), yoksa us-gaap "
                            "Outstanding; birincilde >200 günlük boşluk varsa o boşluğa YEDEK "
                            "etiketten kayıt eklendi (etiket karışımı hücre bazında sayıldı).",
            "bayatlik_bekcisi": f"son filed gözlem gününden {O.BAYAT_GUN} günden eskiyse as-of "
                                f"None + 'bayat_seri' (tutarsizlik.json #6, SCHW'de 4,5 yıllık dei "
                                f"boşluğu bu bekçi kapatıyor)",
            "split_normalizasyonu": "shares_guncel(t) = as_of_val(t) × B_son / B(filed_t); B(f) = "
                                    "f gününe kadar kabul edilmiş bölünme oranlarının çarpımı. "
                                    "Bölünme takvimi EDGAR'ın geriye-dönük YENİDEN-BEYANINDAN "
                                    "türetildi (bar serisi split-DÜZELTİLMİŞ olduğu için bölünme "
                                    "günü bar verisinden okunamıyor — pk.json → "
                                    "split_takvimi_bar_serisi_duz_mu).",
            "supheli_sicrama": f"kart: split ile açıklanamayan >={O.SICRAMA_ESIK}× sıçrama → o "
                               f"sembol-dönem None + neden ('aciklanamayan_5x_sinir'); ayrıca "
                               f"ölçek-hatası gidiş-dönüş penceresindeki as-of değerler None "
                               f"('olcek_hatasi_penceresi', CCI/ON/ORCL/PKG/PSA/QCOM deseni)",
            "net_ihrac": f"shares_guncel(t)/shares_guncel(t-{LOOKBACK} işlem günü) − 1",
            "gozlem": "her takvim ayının SON işlem günü (ortak bar takvimi)",
            "dilim": f"aynı gün kesitinde net_ihrac üst %{int(DILIM_PCT*100)} = ihraç dilimi, "
                     f"alt %{int(DILIM_PCT*100)} = geri-alım dilimi",
            "taban": "kart: aynı-gün EVREN ortalaması — o gün ileri getirisi tanımlı TÜM yüklü "
                     "evren sembolleri (248). Kendi alt-evreninin tabanı AYRICA tanı olarak verildi.",
            "ci": f"{O.BLOCK} ardışık GÖZLEM GÜNÜ blok-bootstrap (%95, {O.BOOT} tekrar). Aylık "
                  f"panelde bu {O.BLOCK} AY demektir — 60g örtüşmesinin gerektirdiğinden GENİŞ, "
                  f"yani MUHAFAZAKÂR. Örtüşmeye denk blok (3 ay) tanı olarak ayrıca verildi.",
            "maliyet": f"{O.MALIYET_BPS}bps tek-yön; hüküm BRÜT üzerinden (kart success_metric "
                       f"maliyet yazmıyor), maliyet düşülmüş değer ayrıca raporlanır",
        },
        "bar_muhasebesi": {k: v for k, v in bar_acc.items() if k != "kisa_semboller"},
        "hisse_muhasebesi": {k: v for k, v in sh_acc.items() if k != "split_takvimi"},
        "split_takvimi_muhasebesi": sh_acc["split_takvimi"],
        "panel_muhasebesi": pacc,
    }
    sonuc["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])

    # ---------------- KILL#3 KAPISI ----------------
    kill3 = {"gecerli_sembol_ay": pacc["gecerli"], "esik": MIN_SEMBOL_AY,
             "yeterli": bool(pacc["gecerli"] >= MIN_SEMBOL_AY)}
    sonuc["kill3_ornekem"] = kill3
    if not kill3["yeterli"]:
        sonuc["DURUM"] = "OLCULMEDI"
        sonuc["neden"] = (f"kart kill#3: geçerli sembol-ay {pacc['gecerli']} < {MIN_SEMBOL_AY} — "
                          f"tanım GEVŞETİLMEZ, kart ASKIDA (K harcanmaz)")
        O.json_yaz(O.SANDBOX / "sonuc_012.json", sonuc)
        print("== KILL#3: askı ==")
        return

    # ---------------- TABANLAR ----------------
    tab_evren, tab_alt = {}, {}
    for h in HORIZONS:
        g = D[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"]
        tab_evren[h] = g.mean()
        g2 = D.loc[D["net"].notna(), ["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"]
        tab_alt[h] = g2.mean()

    # ---------------- DİLİMLER ----------------
    V = D[D["net"].notna()].copy()
    kesit = V.groupby("date").size()
    kullanilan = kesit[kesit >= O.MIN_KESIT].index
    sonuc["kesit_muhasebesi"] = {
        "gozlem_gunu_toplam": int(D["date"].nunique()),
        "gecerli_net_gunu": int(V["date"].nunique()),
        "kesit_yeterli_gun": int(len(kullanilan)),
        "min_kesit": O.MIN_KESIT,
        "kesit_buyuklugu": {"medyan": O._r6(kesit.median()), "min": int(kesit.min()),
                            "maks": int(kesit.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "net_ihrac_dagilimi": {q: O._r6(V["net"].quantile(q))
                               for q in (0.01, 0.05, 0.2, 0.5, 0.8, 0.95, 0.99)},
    }
    V = V[V["date"].isin(kullanilan)].copy()
    V["pct"] = V.groupby("date")["net"].rank(pct=True, method="first")
    V["dilim"] = np.where(V["pct"] > 1 - DILIM_PCT, "ihrac_ust_20pct",
                          np.where(V["pct"] <= DILIM_PCT, "gerialim_alt_20pct", "orta"))

    dilim_out = {}
    for ad in ("ihrac_ust_20pct", "gerialim_alt_20pct"):
        sub = V[V["dilim"] == ad]
        blok = {"n_sembol_ay": int(len(sub)), "n_gun": int(sub["date"].nunique()),
                "n_sembol": int(sub["ticker"].nunique()),
                "net_ihrac_ort": O._r6(sub["net"].mean()),
                "net_ihrac_medyan": O._r6(sub["net"].median()), "ufuklar": {}}
        for h in HORIZONS:
            s2 = sub[["date", f"fwd{h}"]].dropna()
            if len(s2) < O.MIN_SLICE:
                blok["ufuklar"][str(h)] = {"n": int(len(s2)), "neden": f"n<{O.MIN_SLICE}"}
                continue
            y = s2[f"fwd{h}"].to_numpy(float)
            dts = s2["date"].to_numpy()
            base = s2["date"].map(tab_evren[h]).to_numpy(float)
            base2 = s2["date"].map(tab_alt[h]).to_numpy(float)
            m = np.isfinite(base)
            m2 = np.isfinite(base2)
            blok["ufuklar"][str(h)] = {
                "ham": O.mean_with_ci(y, dts),
                "evren_fazlasi": O.mean_with_ci((y - base)[m], dts[m]),
                "evren_fazlasi_blok3": O.mean_with_ci((y - base)[m], dts[m], blok=3),
                "kendi_altkume_fazlasi": O.mean_with_ci((y - base2)[m2], dts[m2]),
            }
        dilim_out[ad] = blok
    sonuc["i_dilim_tablosu"] = dilim_out

    # yayılım (tanı): geri-alım − ihraç
    yay = {}
    for h in HORIZONS:
        a = V[(V["dilim"] == "gerialim_alt_20pct")][["date", f"fwd{h}"]].dropna()
        b = V[(V["dilim"] == "ihrac_ust_20pct")][["date", f"fwd{h}"]].dropna()
        yay[str(h)] = O.fark_with_ci(a[f"fwd{h}"].to_numpy(float), a["date"].to_numpy(),
                                     b[f"fwd{h}"].to_numpy(float), b["date"].to_numpy())
    sonuc["i_yayilim_gerialim_eksi_ihrac"] = {
        "not": "kart success_metric'in bacağı DEĞİL — iki uç dilimin ayrışmasını gösteren TANI.",
        "ufuklar": yay}

    # ---------------- BEŞLİ DİLİM TABLOSU (TANI — CI YOK, hipotez testi DEĞİL, K harcanmaz) -----
    V["q5"] = V.groupby("date")["net"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    tab = {}
    for h in HORIZONS:
        g = V[["q5", "date", f"fwd{h}"]].dropna()
        base = g["date"].map(tab_evren[h]).to_numpy(float)
        g = g.assign(fazla=g[f"fwd{h}"].to_numpy(float) - base).dropna()
        tab[str(h)] = {str(int(k)): {"n": int(v["fazla"].size),
                                     "fazla_ort": O._r6(v["fazla"].mean()),
                                     "net_ort": O._r6(V.loc[v.index, "net"].mean())}
                       for k, v in g.groupby("q5")}
    sonuc["i_besli_dilim_TANI"] = {
        "not": "0 = en çok GERİ-ALAN, 4 = en çok İHRAÇ EDEN. Monotonluk gözle görülsün diye; "
               "CI/anlamlılık BİLEREK hesaplanmadı — hüküm bacağı değil, K HARCANMAZ.",
        "ufuklar": tab}
    sonuc["i_ihrac_diliminde_en_sik_semboller_TANI"] = (
        V[V["dilim"] == "ihrac_ust_20pct"]["ticker"].value_counts().head(15).to_dict())

    # ---------------- HÜKÜM ÖNERİSİ (kart ölçütü) ----------------
    def leg(ad, h, key="evren_fazlasi"):
        return dilim_out[ad]["ufuklar"].get(str(h), {}).get(key, {})

    ih60, ga60 = leg("ihrac_ust_20pct", 60), leg("gerialim_alt_20pct", 60)
    ih20, ga20 = leg("ihrac_ust_20pct", 20), leg("gerialim_alt_20pct", 20)
    basari = bool(ih60.get("negatif_anlamli") or ga60.get("pozitif_anlamli"))
    ters = bool(ih60.get("pozitif_anlamli") or ga60.get("negatif_anlamli"))
    bilgisiz = bool(all(x.get("anlamli") is False for x in (ih20, ih60, ga20, ga60)))
    hukum = {
        "kart_success_metric": "ihraç-dilimi fazlası @60 anlamlı NEGATİF VEYA geri-alım-dilimi "
                               "fazlası @60 anlamlı POZİTİF (CI 0-dışı) VE yön literatürle tutarlı",
        "bacaklar": {"ihrac@60": {k: ih60.get(k) for k in ("n", "ort", "ci", "anlamli",
                                                           "negatif_anlamli", "pozitif_anlamli")},
                     "gerialim@60": {k: ga60.get(k) for k in ("n", "ort", "ci", "anlamli",
                                                              "negatif_anlamli", "pozitif_anlamli")},
                     "ihrac@20": {k: ih20.get(k) for k in ("n", "ort", "ci", "anlamli")},
                     "gerialim@20": {k: ga20.get(k) for k in ("n", "ort", "ci", "anlamli")}},
        "success_metric_KARSILANDI": basari,
        "kill1_iki_uc_de_CI_0_ici": bilgisiz,
        "kill2_yon_literaturun_TERSI_ve_anlamli": ters,
        "kill3_ornek_yetersiz": bool(not kill3["yeterli"]),
    }
    if basari and not ters:
        hukum["oneri"] = "SUCCESS — kart ölçütü karşılandı"
    elif ters and not basari:
        hukum["oneri"] = "ARŞİV — kill#2 (yön literatürün TERSİ ve anlamlı; 'bu evrende ters' notu)"
    elif bilgisiz:
        hukum["oneri"] = "ARŞİV — kill#1 (iki uç dilim de @20 ve @60'ta CI-0-içi, bilgisiz)"
    else:
        hukum["oneri"] = "KARMA — bacaklar ayrışıyor, hüküm Rol-1'de"
    sonuc["hukum_onerisi"] = hukum
    sonuc["DURUM"] = "OLCULDU"

    O.json_yaz(O.SANDBOX / "sonuc_012.json", sonuc)
    V.to_csv(O.SANDBOX / "panel_012.csv.gz", index=False, compression="gzip")
    print(f"   geçerli sembol-ay={pacc['gecerli']}  öneri={hukum['oneri']}")


if __name__ == "__main__":
    main()
