"""EDG-2026-013 · KISA-DÖNEM MOMENTUM × TURNOVER — SALT-ÖLÇÜM, SANDBOX.

Kart: research/cards/EDG-2026-013-mom-turnover.yaml (status: registered). KART DIŞINA ÖLÇÜM YOK.
as-of/etiket/temizlik kuralları EDG-012 ile BİREBİR aynı altyapıdan (ortak.build_hisse).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import ortak as O

HORIZONS = (10, 20)          # kart: ileri getiri 10/20g
MOM_PCT = 0.20               # kart: mom21 üst %20
KATMANLAR = ("mom_ust20_kosulsuz", "mom_ust20_turnover_ustu")


def panel(pan, ser, OBS):
    parts, acc = [], {"sembol": 0, "gozlem_hucre": 0, "neden_sayimi": {},
                      "turnover_gecerli": 0, "mom_gecerli": 0, "ikisi_de": 0}
    for sym, v in pan.items():
        d = v["dates"]
        pos = np.searchsorted(d, OBS)
        pos_c = np.minimum(pos, len(d) - 1)
        ok = (pos < len(d)) & (d[pos_c] == OBS)
        idx = pos[ok]
        tdates = OBS[ok]
        if len(idx) == 0:
            continue
        acc["sembol"] += 1
        acc["gozlem_hucre"] += int(len(idx))
        row = {"date": tdates, "ticker": sym, "mom21": v["mom21"][idx],
               "rvol20": v["rvol20"][idx], "med_hacim21": v["med_hacim21"][idx]}
        for h in HORIZONS:
            row[f"fwd{h}"] = v[f"fwd{h}"][idx]
        s = ser.get(sym)
        if s is None:
            row["shares"] = np.full(len(idx), np.nan)
            acc["neden_sayimi"]["anlik_hisse_serisi_yok"] = \
                acc["neden_sayimi"].get("anlik_hisse_serisi_yok", 0) + len(idx)
        else:
            sh, f, nd = s.asof(tdates)
            row["shares"] = sh
            for k, c in zip(*np.unique(nd[nd != ""], return_counts=True)):
                acc["neden_sayimi"][str(k)] = acc["neden_sayimi"].get(str(k), 0) + int(c)
            acc["neden_sayimi"]["dosyalama_yok"] = acc["neden_sayimi"].get("dosyalama_yok", 0) + \
                int(np.sum(nd == "dosyalama_yok"))
        parts.append(pd.DataFrame(row))
    D = pd.concat(parts, ignore_index=True)
    D["turnover21"] = D["med_hacim21"] / D["shares"]
    acc["turnover_gecerli"] = int(D["turnover21"].notna().sum())
    acc["mom_gecerli"] = int(D["mom21"].notna().sum())
    acc["ikisi_de"] = int((D["turnover21"].notna() & D["mom21"].notna()).sum())
    return D, acc


def main() -> None:
    pan, bar_acc = O.bars_cached()
    S = O._shares_ham()
    ser, birincil, sh_acc = O.build_hisse(S)
    sh_acc["fiziksel_bekci"] = O.fiziksel_bekci(ser, pan)
    OBS = O.ortak_takvim(pan)
    print(f"== 013: {len(OBS)} günlük gözlem noktası, {len(pan)} sembol ==")

    D, pacc = panel(pan, ser, OBS)
    sonuc = {
        "kart": "EDG-2026-013", "aile": "short_momentum_turnover",
        "olcum_tarihi": pd.Timestamp.now("UTC").isoformat(), "sandbox": str(O.SANDBOX),
        "DURUM": None,
        "kart_metni_uygulamasi": {
            "as_of_shares": "EDG-012 ile BİREBİR aynı altyapı (ortak.build_hisse): dei→us-gaap "
                            "Outstanding önceliği, Issued ve ağırlıklı-ortalama YOK, val>0, "
                            "donem_turu=anlik, bayatlık bekçisi, split güncel-baz dönüşümü, "
                            "ölçek-hatası penceresi None.",
            "turnover21": "medyan21(hacim) / as_of_shares(t). Bar hacmi GÜNCEL bazda "
                          "split-düzeltilmiş olduğu için hisse sayımı da GÜNCEL baza çevrildi — "
                          "oran böylece bölünmeden bağımsız (pay ve payda aynı bazda).",
            "mom21": "close[t]/close[t-21]-1 (21 İŞLEM günü, t dâhil geriye)",
            "kesit": "İKİ KATMAN DA AYNI KESİTTE sıralanır: o gün mom21 VE turnover21 tanımlı "
                     "semboller. Aksi hâlde artımlılık farkı kapsam farkıyla karışırdı. "
                     "'Koşulsuz, tam evren' okuması AYRICA tanı olarak verildi.",
            "katmanlar": "mom_ust20_kosulsuz = o gün mom21 üst %20; mom_ust20_turnover_ustu = "
                         "aynı dilim ∧ turnover21 > o günün kesit MEDYANI",
            "taban": "aynı-gün EVREN ortalaması (o gün ileri getirisi tanımlı tüm yüklü semboller)",
            "ci": f"{O.BLOCK} ardışık gözlem günü (=21 işlem günü) blok-bootstrap, %95, {O.BOOT} tekrar",
            "artimlilik": "koşullu dilim fazlası − koşulsuz dilim fazlası; bootstrap AYNI gün "
                          "dizisini iki dilime de uygular (eşleştirilmiş fark)",
            "maliyet": f"{O.MALIYET_BPS}bps tek-yön; hüküm BRÜT üzerinden",
        },
        "bar_muhasebesi": {k: v for k, v in bar_acc.items() if k != "kisa_semboller"},
        "hisse_muhasebesi": {k: v for k, v in sh_acc.items() if k != "split_takvimi"},
        "panel_muhasebesi": pacc,
    }
    sonuc["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])

    # ---------------- tabanlar ----------------
    tab = {}
    for h in HORIZONS:
        tab[h] = D[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"].mean()

    # ---------------- kesit ----------------
    V = D[D["mom21"].notna() & D["turnover21"].notna()].copy()
    kesit = V.groupby("date").size()
    kullanilan = kesit[kesit >= O.MIN_KESIT].index
    V = V[V["date"].isin(kullanilan)].copy()
    V["mom_pct"] = V.groupby("date")["mom21"].rank(pct=True, method="first")
    V["to_med"] = V.groupby("date")["turnover21"].transform("median")
    V["ust_mom"] = V["mom_pct"] > 1 - MOM_PCT
    V["ust_to"] = V["turnover21"] > V["to_med"]
    sonuc["kesit_muhasebesi"] = {
        "gozlem_gunu_toplam": int(D["date"].nunique()),
        "kesit_yeterli_gun": int(len(kullanilan)), "min_kesit": O.MIN_KESIT,
        "kesit_buyuklugu": {"medyan": O._r6(kesit.median()), "min": int(kesit.min()),
                            "maks": int(kesit.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "turnover21_dagilimi": {q: O._r6(V["turnover21"].quantile(q))
                                for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
        "mom21_dagilimi": {q: O._r6(V["mom21"].quantile(q)) for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
    }

    # akrabalık beyanı (kart guard): turnover ~ rvol20 korelasyonu
    sub = V[["turnover21", "rvol20", "mom21"]].dropna()
    ornek = sub.sample(n=min(200000, len(sub)), random_state=11)
    sonuc["akrabalik_beyani"] = {
        "not": "kart guard: rvol20 ZATEN skorda; turnover ile akrabalığı beyan edilir.",
        "n_ornek": int(len(ornek)),
        "spearman_turnover21_rvol20": O._r6(
            O.spearman_np(ornek["turnover21"], ornek["rvol20"])),
        "spearman_turnover21_mom21": O._r6(
            O.spearman_np(ornek["turnover21"], ornek["mom21"])),
        "gun_ici_ortalama_spearman_turnover_rvol": O._r6(np.nanmean([
            O.spearman_np(g["turnover21"], g["rvol20"]) or np.nan
            for _, g in V.groupby("date") if len(g) >= 30])),
    }

    # ---------------- katmanlar ----------------
    maskeler = {"mom_ust20_kosulsuz": V["ust_mom"],
                "mom_ust20_turnover_ustu": V["ust_mom"] & V["ust_to"]}
    dilim, fazla_kayit = {}, {}
    for ad, m in maskeler.items():
        sub = V[m]
        blok = {"n_sembol_gun": int(len(sub)), "n_gun": int(sub["date"].nunique()),
                "n_sembol": int(sub["ticker"].nunique()),
                "mom21_ort": O._r6(sub["mom21"].mean()),
                "turnover21_medyan": O._r6(sub["turnover21"].median()), "ufuklar": {}}
        for h in HORIZONS:
            s2 = sub[["date", f"fwd{h}"]].dropna()
            y = s2[f"fwd{h}"].to_numpy(float)
            dts = s2["date"].to_numpy()
            base = s2["date"].map(tab[h]).to_numpy(float)
            ok = np.isfinite(base)
            blok["ufuklar"][str(h)] = {"ham": O.mean_with_ci(y, dts),
                                       "evren_fazlasi": O.mean_with_ci((y - base)[ok], dts[ok])}
            fazla_kayit[(ad, h)] = ((y - base)[ok], dts[ok])
        dilim[ad] = blok
    sonuc["i_dilim_tablosu"] = dilim

    # ---------------- artımlılık ----------------
    art = {}
    for h in HORIZONS:
        ya, da = fazla_kayit[("mom_ust20_turnover_ustu", h)]
        yb, db = fazla_kayit[("mom_ust20_kosulsuz", h)]
        art[str(h)] = O.fark_with_ci(ya, da, yb, db)
    sonuc["ii_artimlilik_kosullu_eksi_kosulsuz"] = art

    # ---------------- tanı: turnover ALTI dilim + tam-evren koşulsuz okuma ----------------
    tani = {}
    alt = V[V["ust_mom"] & ~V["ust_to"]]
    tani["mom_ust20_turnover_ALTI"] = {"n": int(len(alt)), "ufuklar": {}}
    for h in HORIZONS:
        s2 = alt[["date", f"fwd{h}"]].dropna()
        base = s2["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        tani["mom_ust20_turnover_ALTI"]["ufuklar"][str(h)] = O.mean_with_ci(
            (s2[f"fwd{h}"].to_numpy(float) - base)[ok], s2["date"].to_numpy()[ok])
    W = D[D["mom21"].notna()].copy()
    kw = W.groupby("date").size()
    W = W[W["date"].isin(kw[kw >= O.MIN_KESIT].index)]
    W["pct"] = W.groupby("date")["mom21"].rank(pct=True, method="first")
    ws = W[W["pct"] > 1 - MOM_PCT]
    tani["mom_ust20_kosulsuz_TAM_EVREN"] = {"n": int(len(ws)), "ufuklar": {}}
    for h in HORIZONS:
        s2 = ws[["date", f"fwd{h}"]].dropna()
        base = s2["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        tani["mom_ust20_kosulsuz_TAM_EVREN"]["ufuklar"][str(h)] = O.mean_with_ci(
            (s2[f"fwd{h}"].to_numpy(float) - base)[ok], s2["date"].to_numpy()[ok])
    # turnover ANA ETKİSİ — CI BİLEREK YOK (kartın grid'inde olmayan bir dilim; CI'lı sınamak
    # K'yı çarpardı. Betimleyici tablo, şablon geleneği: max_olcum decile_table).
    V["to_q5"] = V.groupby("date")["turnover21"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    ana = {}
    for h in HORIZONS:
        g = V[["to_q5", "date", "turnover21", f"fwd{h}"]].dropna()
        g = g.assign(fazla=g[f"fwd{h}"].to_numpy(float) - g["date"].map(tab[h]).to_numpy(float))
        g = g.dropna(subset=["fazla"])
        ana[str(h)] = {str(int(k)): {"n": int(len(v)), "fazla_ort": O._r6(v["fazla"].mean()),
                                     "turnover_ort": O._r6(v["turnover21"].mean())}
                       for k, v in g.groupby("to_q5")}
    sonuc["iii_tani_dilimleri"] = {
        "not": "TANI — kart bacağı DEĞİL, K harcanmaz. 'mom_ust20_turnover_ALTI' kayıtlı iki "
               "dilimin TÜMLEYENİDİR (yeni grid noktası değil), CI'sı okunabilir. "
               "'turnover_ANA_ETKI_q5' ise kartın grid'inde OLMAYAN bir kesittir: CI BİLEREK "
               "hesaplanmadı — CI'lı sınansaydı K çarpılırdı. Test isteniyorsa KENDİ kartını ister.",
        **tani,
        "turnover_ANA_ETKI_q5_CI_YOK": {"aciklama": "0 = en düşük turnover, 4 = en yüksek; "
                                                    "momentum koşulu YOK, tüm kesit",
                                        "ufuklar": ana}}

    # ---------------- HÜKÜM ÖNERİSİ ----------------
    def leg(ad, h):
        return dilim[ad]["ufuklar"].get(str(h), {}).get("evren_fazlasi", {})

    kos = {h: leg("mom_ust20_turnover_ustu", h) for h in HORIZONS}
    kss = {h: leg("mom_ust20_kosulsuz", h) for h in HORIZONS}
    bacak1 = any(kos[h].get("pozitif_anlamli") is True for h in HORIZONS)
    bacak2 = any((art[str(h)].get("pozitif_anlamli") is True) for h in HORIZONS)
    bacak2_ayni_ufuk = any((kos[h].get("pozitif_anlamli") is True and
                            art[str(h)].get("pozitif_anlamli") is True) for h in HORIZONS)
    bilgisiz = all(kos[h].get("anlamli") is False for h in HORIZONS)
    reversal = any(kos[h].get("negatif_anlamli") is True for h in HORIZONS)
    hukum = {
        "kart_success_metric": "turnover-koşullu mom diliminin fazlası @10 VEYA @20 anlamlı "
                               "POZİTİF VE koşulsuz mom fazlasını anlamlı AŞIYOR (artımlılık)",
        "bacaklar": {
            "kosullu_fazla": {str(h): {k: kos[h].get(k) for k in
                                       ("n", "ort", "ci", "anlamli", "pozitif_anlamli",
                                        "negatif_anlamli")} for h in HORIZONS},
            "kosulsuz_fazla": {str(h): {k: kss[h].get(k) for k in
                                        ("n", "ort", "ci", "anlamli", "pozitif_anlamli",
                                         "negatif_anlamli")} for h in HORIZONS},
            "artimlilik": art,
        },
        "bacak1_kosullu_pozitif_anlamli": bacak1,
        "bacak2_artimlilik_pozitif_anlamli": bacak2,
        "iki_bacak_AYNI_ufukta": bacak2_ayni_ufuk,
        "success_metric_KARSILANDI": bool(bacak2_ayni_ufuk),
        "kill1_kosullu_CI_0_ici": bool(bilgisiz),
        "kill2_artimlilik_yok": bool(not bacak2),
        "kill3_reversal_anlamli_negatif": bool(reversal),
    }
    if hukum["success_metric_KARSILANDI"]:
        hukum["oneri"] = "SUCCESS — kart ölçütü karşılandı"
    elif reversal:
        hukum["oneri"] = "ARŞİV — kill#3 (bu ufukta ters-dönüş baskın: fazla anlamlı NEGATİF) + not"
    elif bilgisiz:
        hukum["oneri"] = "ARŞİV — kill#1 (koşullu dilim fazlası CI-0-içi, bilgisiz)"
    elif not bacak2:
        hukum["oneri"] = "ARŞİV — kill#2 (artımlılık yok: turnover bilgi katmıyor)"
    else:
        hukum["oneri"] = "KARMA — bacaklar ayrışıyor, hüküm Rol-1'de"
    sonuc["hukum_onerisi"] = hukum
    sonuc["DURUM"] = "OLCULDU"

    O.json_yaz(O.SANDBOX / "sonuc_013.json", sonuc)
    print(f"   öneri={hukum['oneri']}")


if __name__ == "__main__":
    main()
