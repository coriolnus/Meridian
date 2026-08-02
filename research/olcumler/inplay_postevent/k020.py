"""EDG-2026-020 · İKİ HÜCRE (K=2) + PEAD-AYRIŞMASI.

Kart: research/cards/EDG-2026-020-postevent-inplay.yaml (status: registered).
KARTA DOKUNULMAZ · HÜKÜM VERİLMEZ · EŞİK ÖLÇÜMDEN SONRA DEĞİŞMEZ.

ÖNCE pk020.py koşar. Bir kapı düşerse bu dosya HİÇBİR hücre ölçmez (kart: "üretilemezse DUR").

KARTIN UYGULAMASI (harfiyen, ölçüm başlamadan yazıldı):
  * dilim      : in_play(0 <= t − e <= P TAKVİM GÜNÜ) ∧ rvol20(t) >= 1.5
  * taban      : AYNI-GÜN aday-havuzunun in_play-DIŞI satırlarının ortalaması (kart horizon).
                 Hedef satırı yapısal olarak kendi tabanında DEĞİLDİR (Ders #5 kural 1 kendiliğinden
                 sağlanır: taban in_play=False satırlardan kurulur, hedef in_play=True'dur).
  * fazla      : fwd_h − o günün tabanı. HAM GETİRİ HÜKME GİRMEZ (Ders #3) — betimleyici sütun.
  * CI         : 21g HAREKETLİ blok bootstrap %95, 2000 tekrar (Ders #6; IID YASAK)
  * maliyet    : 10bps birincil + 20bps duyarlılık (kart cost_model)
  * K muhasebesi: pencere_gun ∈ {3,5} → K += 2. FWER kutbu (kapı p_req = 1 − α/K); bu ölçüm
                 kapıya dokunmaz, yalnız hücre sayısını beyan eder.
  * min_taban  : ÖLÇÜM ÖNCESİ BEYAN — birincil 1 (kartın harfi: "havuz ortalaması"), 5 duyarlılık
                 satırıdır ve HÜKME GİRMEZ (ortak020.MIN_TABAN / MIN_TABAN_DUYARLILIK).
"""
from __future__ import annotations

import datetime as _dt
import json
import pickle

import numpy as np
import pandas as pd

import ortak020 as O

UFUKLAR = O.UFUKLAR
HUKUM_UFUKLARI = (10, 20)          # kart success/kill bu ikisini okur; @5 betimleyicidir


# ==================================================================================================
# HAM BAR ÇERÇEVELERİ (pead'i koşturmak için gerekli — panel dizileri yetmez)
# ==================================================================================================
def raw_cached():
    p = O.CACHE / "raw020.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    per, acc = O.load_bars()
    with open(p, "wb") as fh:
        pickle.dump((per, acc), fh, protocol=4)
    return per, acc


# ==================================================================================================
# ADAY PANELİ
# ==================================================================================================
def aday_paneli(pan: dict, takvim: dict, aday: list) -> pd.DataFrame:
    """Aday-gün başına tek satır: rvol20, fwd/chain, gecikme (PIT-kapılı), in_play(P)."""
    olay_ord = {t: np.sort(np.array([O.iso_ord(d) for d in ds], dtype=np.int64))
                for t, ds in takvim.items()}
    idx = {t: {d: i for i, d in enumerate(v["dates"])} for t, v in pan.items()}
    rows = []
    for tk, ds in aday:
        f = pan[tk]
        i = idx[tk][ds]
        r = {"ticker": tk, "date": ds, "yil": int(ds[:4])}
        v = f["rvol20"][i]
        r["rvol20"] = float(v) if np.isfinite(v) else np.nan
        for h in UFUKLAR:
            a, b = f[f"fwd{h}"][i], f[f"chain{h}"][i]
            r[f"fwd{h}"] = float(a) if np.isfinite(a) else np.nan
            r[f"chain{h}"] = float(b) if np.isfinite(b) else np.nan
        rows.append(r)
    V = pd.DataFrame(rows)
    tords = np.array([O.iso_ord(d) for d in V["date"]], dtype=np.int64)
    gec = np.full(len(V), -1, dtype=np.int64)
    tk_arr = V["ticker"].to_numpy()
    for tk in np.unique(tk_arr):
        m = np.nonzero(tk_arr == tk)[0]
        ev = olay_ord.get(tk, np.empty(0, np.int64))
        gec[m] = O.gecikme_gunu(ev, tords[m])          # PIT KAPISI — yalnız e <= t
    V["gecikme"] = gec
    for P in O.PENCERELER:
        V[f"in_play{P}"] = (gec >= 0) & (gec <= P)
    V["rvol_ok"] = V["rvol20"] >= O.RVOL_ESIK
    return V


# ==================================================================================================
# PEAD — motorun KENDİ değerlendiricisi, kum havuzunda, ölçüm barlarıyla
# ==================================================================================================
def pead_kos(per: dict, pan: dict, V: pd.DataFrame) -> tuple[pd.Series, dict]:
    """`strategy.evaluate_pead` her aday-gün için ÇAĞRILIR (kopyalanmaz).

    PIT ŞERHİ: pead'in çapası `earnings.days_since_report` ve o da YAPISAL olarak tek yönlüdür
    (`earnings.py:193` → `0 <= (d − e).days <= max_days`) — yani gelecek tarih okumaz. Bu kartın
    in_play kapısıyla AYNI yön sözleşmesi; ikisi de e <= t dalıdır.

    Bar dilimi motorla BİREBİR: `backtest.py:320` `scan_entry(sub.tail(340), …)` — aynı kuyruk
    uzunluğu kullanılır ki 'pead ateşledi mi' sorusu motorun gördüğü pencerede sorulsun.
    """
    from meridian import indicators as ind
    from meridian import strategy as strat

    params = {}
    try:
        import yaml
        sy = yaml.safe_load((O.LIVE_STATE / "strategy.yaml").read_text())
        params = dict(sy.get("params") or {})
        ver = sy.get("version")
    except Exception as e:                             # noqa: BLE001 — sayılır, yutulmaz
        params, ver = {}, f"okunamadı: {type(e).__name__}: {e}"

    # ---- RS çapraz-kesiti: backtest.py:290-295 ile AYNI tanım (63 barlık geriye getiri, yüzdelik)
    gerekli_gunler = sorted(set(V["date"]))
    gun_set = set(gerekli_gunler)
    rets_by_day: dict = {d: {} for d in gerekli_gunler}
    for t, f in pan.items():
        dts, r63 = f["dates"], f["ret63"]
        for i, d in enumerate(dts):
            if d in gun_set and np.isfinite(r63[i]):
                rets_by_day[d][t] = float(r63[i])
    rs_by_day = {d: ind.rs_rating(r) for d, r in rets_by_day.items()}

    acc = {"cagri": 0, "atesledi": 0, "bar_kisa": 0, "hata": 0,
           "strategy_yaml_version": ver, "params_okunan_anahtar": len(params),
           "pead_params_varsayilan": {"pead.watch_days": params.get("pead.watch_days", 35),
                                      "pead.min_gap_pct": params.get("pead.min_gap_pct", 3.0),
                                      "pead.min_volume_ratio": params.get("pead.min_volume_ratio",
                                                                          1.2)},
           "rs_gun": len(rs_by_day),
           "rs_kesit_medyan": float(np.median([len(r) for r in rets_by_day.values()]))
           if rets_by_day else None}
    idx = {t: {d: i for i, d in enumerate(v["dates"])} for t, v in pan.items()}
    out = np.zeros(len(V), bool)
    skor = np.full(len(V), np.nan)
    for j, (tk, ds) in enumerate(zip(V["ticker"], V["date"])):
        df = per.get(tk)
        if df is None:
            acc["bar_kisa"] += 1
            continue
        i = idx[tk][ds]
        sub = df.iloc[:i + 1].tail(340)
        if len(sub) < 60:
            acc["bar_kisa"] += 1
            continue
        acc["cagri"] += 1
        try:
            sig = strat.evaluate_pead(sub, params, int(rs_by_day.get(ds, {}).get(tk, 50)),
                                      ticker=tk)
        except Exception as e:                         # noqa: BLE001 — sayılır, yutulmaz
            acc["hata"] += 1
            if acc["hata"] <= 3:
                print(f"  ! pead {tk} {ds}: {type(e).__name__}: {e}", flush=True)
            continue
        if sig is not None:
            out[j] = True
            skor[j] = float(sig.score)
            acc["atesledi"] += 1
    V["pead_skor"] = skor
    return pd.Series(out, index=V.index, name="pead"), acc


# ==================================================================================================
# TABAN + FAZLA
# ==================================================================================================
def fazla_hesapla(V: pd.DataFrame, inplay_kolon: str, h: int, min_taban: int,
                  ek_maske=None) -> dict:
    """Fazla = fwd_h − AYNI GÜN in_play-DIŞI havuz ortalaması.

    `ek_maske` verilirse HEM dilim HEM taban o maskeyle daraltılır (pead-kontrollü artık için:
    'pead ateşlememiş satırlar' alt-evreni). Taban ve dilim aynı evrenden gelmezse kıyas kirlenir.
    """
    g = V[["date", "ticker", inplay_kolon, "rvol_ok", f"fwd{h}"]].copy()
    if ek_maske is not None:
        g = g[ek_maske.to_numpy()]
    g = g.dropna(subset=[f"fwd{h}"])
    ip = g[inplay_kolon].to_numpy(bool)
    y = g[f"fwd{h}"].to_numpy(float)
    d = g["date"].to_numpy()
    uniq, inv = np.unique(d, return_inverse=True)
    nd = len(uniq)

    temiz = ~ip
    s = np.bincount(inv, weights=y * temiz, minlength=nd)
    c = np.bincount(inv, weights=temiz.astype(float), minlength=nd)
    with np.errstate(divide="ignore", invalid="ignore"):
        taban = np.where(c > 0, s / c, np.nan)
    # KİRLİ taban (Ders #5 kural 3 — SIKIŞMA ölçüsü; HÜKME GİRMEZ)
    s_k = np.bincount(inv, weights=y, minlength=nd)
    c_k = np.bincount(inv, minlength=nd).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        taban_kirli = np.where(c_k > 0, s_k / c_k, np.nan)

    dilim = ip & (g["rvol_ok"].to_numpy(bool))
    yeter = c[inv] >= min_taban
    kullan = dilim & yeter & np.isfinite(taban[inv])
    n_taban_yok = int((dilim & ~(yeter & np.isfinite(taban[inv]))).sum())

    fz = y[kullan] - taban[inv][kullan]
    fz_kirli = y[kullan] - taban_kirli[inv][kullan]
    dd = d[kullan]
    r = O.mean_with_ci(fz, dd)
    r.update({
        "n_dilim_ham": int(dilim.sum()), "n_taban_yok": n_taban_yok,
        "ham_getiri_betimleyici": O.mean_with_ci(y[kullan], dd) if kullan.sum() else None,
        "taban_seviyesi_betimleyici": {
            "dilim_gunlerinin_taban_ort": O._r6(float(np.mean(taban[inv][kullan])))
            if kullan.sum() else None,
            "havuz_geneli_in_play_disi_ort": O._r6(float(np.mean(y[temiz]))) if temiz.any() else None,
            "beyan": "BETİMLEYİCİ — hükme girmez. 'dilim günlerinin tabanı' ile 'havuz geneli' "
                     "arasındaki fark, olay günlerinin piyasa-genelinde nasıl günler olduğunu "
                     "gösterir (gün-bazlı tabanın var oluş sebebi: Ders #5)."},
        "taban_gun_sayisi": int(np.isfinite(taban).sum()),
        "taban_gun_basina_n_medyan": O._r6(float(np.median(c[c > 0]))) if (c > 0).any() else None,
        "sikisma": {"kirli_taban_fazlasi_ort": O._r6(float(np.mean(fz_kirli)))
                    if kullan.sum() else None,
                    "fark_temiz_eksi_kirli": O._r6(float(np.mean(fz) - np.mean(fz_kirli)))
                    if kullan.sum() else None,
                    "beyan": "kirli taban = O GÜNÜN TÜM aday satırları (in_play dâhil). HÜKME "
                             "GİRMEZ; yalnız temizliğin etkiyi ne kadar açtığını gösterir "
                             "(Ders #5 kural 3)."},
        "maliyet": {
            "10bps_net_ort": O._r6(float(np.mean(fz)) - O.MALIYET_BPS / 1e4)
            if kullan.sum() else None,
            "20bps_net_ort": O._r6(float(np.mean(fz)) - O.MALIYET_BPS_DUYARLILIK / 1e4)
            if kullan.sum() else None,
            "beyan": "tek-yön bps, fazladan DÜŞÜLÜR. Kart cost_model: '10bps + 20bps duyarlılık; "
                     "olay-sonrası spread-genişlemesi beyan-notu'. BEYAN-NOTU: kazanç sonrası "
                     "ilk günlerde spread GENİŞLER ve gerçek maliyet 10bps'in ÜSTÜNDE olabilir; "
                     "bu ölçümde spread verisi YOK, dolayısıyla 20bps satırı bir ÜST OKUMA "
                     "değil yalnız bir duyarlılıktır."},
        "min_taban": min_taban,
    })
    return r


def alt_donem(V: pd.DataFrame, inplay_kolon: str, h: int, min_taban: int) -> dict:
    """BETİMLEYİCİ alt-dönem satırı (grid'e DAHİL DEĞİL, K harcamaz — EDG-017 emsali)."""
    out = {}
    for yil, sub in V.groupby("yil"):
        if len(sub) < 50:
            out[str(yil)] = {"n_aday_gun": int(len(sub)), "fazla": None,
                             "neden": "aday-gün < 50 (betimleyici satır kurulmuyor)"}
            continue
        r = fazla_hesapla(sub, inplay_kolon, h, min_taban)
        # CI ölçülemediyse NEDENİ yazılır (UYDURMA YASAĞI: boş hücre sebepsiz bırakılmaz).
        ci_neden = (r.get("ci_meta") or {}).get("neden") if r.get("ci") is None else None
        out[str(yil)] = {"n_aday_gun": int(len(sub)), "n": r["n"], "fazla_ort": r["ort"],
                         "ci": r["ci"], "ci_neden": ci_neden,
                         "n_gozlem_gunu": (r.get("ci_meta") or {}).get("n_gun"),
                         "neden": r.get("neden")}
    return out


# ==================================================================================================
# PEAD AYRIŞMASI (kill#2 verisi)
# ==================================================================================================
def jaccard(a: np.ndarray, b: np.ndarray) -> dict:
    kesisim = int((a & b).sum())
    birlesim = int((a | b).sum())
    return {"n_A": int(a.sum()), "n_B": int(b.sum()), "kesisim": kesisim, "birlesim": birlesim,
            "jaccard": O._r6(kesisim / birlesim) if birlesim else None,
            "A_icinde_B_orani": O._r6(kesisim / int(a.sum())) if a.sum() else None,
            "B_icinde_A_orani": O._r6(kesisim / int(b.sum())) if b.sum() else None}


def pead_ayrismasi(V: pd.DataFrame, P: int, min_taban: int) -> dict:
    ipk = f"in_play{P}"
    dilim = (V[ipk] & V["rvol_ok"]).to_numpy(bool)
    pead = V["pead"].to_numpy(bool)
    out = {
        "tanim": "Kartın varlık gerekçesi: bu eksen evaluate_pead'den AYRIŞAN bilgi taşıyor mu? "
                 "İki bacak: (1) küme ÖRTÜŞMESİ (Jaccard), (2) pead-KONTROLLÜ artık "
                 "(çift-sıralama + artık-IC, EDG-016 şablonu).",
        "ortusme": {
            "dilim_vs_pead": jaccard(dilim, pead),
            "yalniz_inplay_vs_pead": jaccard(V[ipk].to_numpy(bool), pead),
            "beyan": "kümeler (ticker,date) aday-günleridir; evren aday havuzudur "
                     f"(n={len(V)}). A = in_play{P}∧rvol>=1.5 dilimi, B = evaluate_pead ateşleyen "
                     "aday-günler."},
    }

    # --- BACAK A: ÇİFT SIRALAMA — pead kovası İÇİNDE dilim vs kalan -------------------------------
    cift = {"tanim": "EDG-016/EDG-007 şablonu: kontrol kovası = pead∈{0,1}. Her kovada dilim "
                     "satırlarının AYNI-GÜN in_play-dışı taban fazlası ayrı ayrı ölçülür. "
                     "pead=False kovası ASIL artık okumasıdır: 'PEAD ateşlememiş satırlarda "
                     "in_play hâlâ bilgi taşıyor mu?'"}
    for h in HUKUM_UFUKLARI:
        hh = {}
        for ad, mask in (("pead_yok", ~pead), ("pead_var", pead)):
            hh[ad] = fazla_hesapla(V, ipk, h, min_taban, ek_maske=pd.Series(mask, index=V.index))
        # iki kova arasındaki fark (dilim satırlarında)
        hh["kova_farki_beyan"] = ("iki kova AYRI evrenlerde (pead=0 / pead=1) kendi tabanlarına "
                                  "karşı ölçülür; kovalar arası fark İSTATİSTİK OLARAK "
                                  "kıyaslanmaz — tabanlar farklıdır.")
        cift[str(h)] = hh
    out["A_cift_siralama"] = cift

    # --- BACAK B: ARTIK-IC — gün-içi pead-kova merkezlemesi sonrası dilim göstergesinin IC'si -----
    art = {"tanim": "GÜN BAZLI kesitte fwd getirinin YÜZDELİK RÜTBESİ, (gün × pead) kovası "
                    "ortalamasından ARINDIRILIR (kova merkezleme = ikili regresörle gün-içi OLS'in "
                    "cebirsel özdeşi). Artık ile dilim göstergesi arasındaki Spearman IC, "
                    "pead-kontrollü artık katkıdır. Kova üyesi n=1 ise merkezleme artığı TANIM "
                    "GEREĞİ 0'dır ve o satır DIŞLANIR (sayılır: n_tek_uyeli_kova_dusen)."}
    for h in HUKUM_UFUKLARI:
        g = V[["date", f"fwd{h}"]].copy()
        g["dilim"] = dilim
        g["pead"] = pead
        g = g.dropna(subset=[f"fwd{h}"])
        if len(g) < O.MIN_SLICE:
            art[str(h)] = {"artik_ic": None, "neden": f"n<{O.MIN_SLICE}"}
            continue
        g["pr"] = g.groupby("date")[f"fwd{h}"].rank(pct=True)
        grp = g.groupby(["date", "pead"])["pr"]
        g["_n"] = grp.transform("size")
        g["_m"] = grp.transform("mean")
        yeter = g["_n"] >= 2
        n_dusen = int((~yeter).sum())
        gg = g[yeter]
        artik = (gg["pr"] - gg["_m"]).to_numpy(float)
        x = gg["dilim"].to_numpy(float)
        r = O.ic_hizli(x, artik, gg["date"].to_numpy())
        r.update({"n_tek_uyeli_kova_dusen": n_dusen,
                  "n_dilim_artikta": int(gg["dilim"].sum())})
        # KONTROLSÜZ ikiz (aynı yöntem, pead kovası OLMADAN) — kontrolün ne kadar aldığı görünsün
        g2 = g.copy()
        g2["_m2"] = g2.groupby("date")["pr"].transform("mean")
        g2["_n2"] = g2.groupby("date")["pr"].transform("size")
        gg2 = g2[g2["_n2"] >= 2]
        r_ham = O.ic_hizli((gg2["dilim"].to_numpy(float)),
                           (gg2["pr"] - gg2["_m2"]).to_numpy(float), gg2["date"].to_numpy())
        art[str(h)] = {"pead_kontrollu": r, "kontrolsuz_ikiz": r_ham}
    out["B_artik_ic"] = art
    return out


# ==================================================================================================
def main() -> dict:
    pkj = json.loads((O.KLASOR / "pk_020.json").read_text())
    if pkj.get("DUR"):
        raise SystemExit("pk020 KAPISI DÜŞTÜ — hiçbir hücre ölçülmez (kart: 'üretilemezse DUR')")

    print("[k020] barlar…", flush=True)
    pan, bar_acc = O.bars_cached()
    per, _ = raw_cached()
    takvim, tak_acc = O.takvim_yukle()
    O.takvim_csv_yaz(takvim, O.config.STATE / "earnings.csv")
    aday, aday_acc = O.aday_havuzu()
    aday = [(t, d) for t, d in aday if t in pan and d in set(pan[t]["dates"].tolist())]
    print(f"[k020] aday-gün={len(aday)}", flush=True)

    V = aday_paneli(pan, takvim, aday)
    print("[k020] evaluate_pead koşuyor…", flush=True)
    V["pead"], pead_acc = pead_kos(per, pan, V)
    print(f"[k020]   pead ateşleyen aday-gün: {pead_acc['atesledi']}/{pead_acc['cagri']}",
          flush=True)

    # ---- Ders #4 muhasebesi (kanonik temiz_taban) ----
    ders4 = {}
    for P in O.PENCERELER:
        rap = O.temiz_taban([(t, d, 0.0) for t, d in aday], takvim, (0, P))
        ders4[str(P)] = {k: rap[k] for k in
                         ("n_toplam", "n_temiz", "n_kirli", "n_cozulemeyen", "n_olculebilir",
                          "kirlilik_orani", "pencere", "gun_birimi", "n_kimlik", "n_olay",
                          "n_olaysiz_kimlik", "uyari")}

    # ---- HÜCRELER ----
    hucreler = {}
    for P in O.PENCERELER:
        ipk = f"in_play{P}"
        cell = {"pencere_gun": P,
                "dilim_tanimi": f"in_play(0 <= t−e <= {P} takvim günü, YALNIZ e<=t) ∧ rvol20>=1.5",
                "n_in_play": int(V[ipk].sum()),
                "n_dilim": int((V[ipk] & V["rvol_ok"]).sum()),
                "n_havuz": int(len(V)),
                "gecikme_dagilimi": {str(k): int(v) for k, v in
                                     V.loc[V[ipk], "gecikme"].value_counts().sort_index().items()},
                "tarih_araligi": [str(V.loc[V[ipk] & V["rvol_ok"], "date"].min()),
                                  str(V.loc[V[ipk] & V["rvol_ok"], "date"].max())]}
        for h in UFUKLAR:
            cell[f"@{h}"] = fazla_hesapla(V, ipk, h, O.MIN_TABAN)
            cell[f"@{h}_min_taban{O.MIN_TABAN_DUYARLILIK}_DUYARLILIK"] = fazla_hesapla(
                V, ipk, h, O.MIN_TABAN_DUYARLILIK)
        cell["alt_donem_@20_BETIMLEYICI"] = alt_donem(V, ipk, 20, O.MIN_TABAN)
        cell["pead_ayrismasi"] = pead_ayrismasi(V, P, O.MIN_TABAN)
        hucreler[f"P{P}"] = cell
        print(f"[k020] P={P}: dilim n={cell['n_dilim']} · @20 fazla={cell['@20']['ort']} "
              f"CI={cell['@20']['ci']}", flush=True)

    # ---- Ders #7: EN İYİ HÜCRE küçültülmeden yazılmaz ----
    from meridian.olcum_araclari import eb_kucult
    etkiler, seler = {}, {}
    for P in O.PENCERELER:
        for h in HUKUM_UFUKLARI:
            r = hucreler[f"P{P}"][f"@{h}"]
            if r.get("ort") is not None and r.get("ci"):
                etkiler[f"P{P}@{h}"] = r["ort"]
                seler[f"P{P}@{h}"] = (r["ci"]["hi"] - r["ci"]["lo"]) / (2 * 1.959964)
    ders7 = eb_kucult(etkiler, seler) if len(etkiler) >= 2 else {
        "neden": "küçültme için en az 2 ölçülebilir hücre gerek"}

    out = {"kart": "EDG-2026-020", "aile": "postevent_inplay",
           "olcum_zamani": _dt.datetime.now(_dt.timezone.utc).isoformat(),
           "kod_surumu": O.kod_surumu_damgasi(O.REPO), "motor_damgasi": O.motor_damgasi(),
           "motor_damgasi_pk_ile_ayni_mi": (
               O.motor_damgasi()["olcume_giren_moduller"]
               == (pkj.get("motor_damgasi") or {}).get("olcume_giren_moduller")),
           "K_muhasebesi": {"parameter_grid": {"pencere_gun": list(O.PENCERELER)},
                            "K_bu_turda": len(O.PENCERELER),
                            "carpim_kurali": "grid'de ÇARPILARAK sayılır; bu kartta tek eksen "
                                             "(pencere_gun) → K = 2",
                            "kutup": "FWER (kapı p_req = 1 − α_family/K, gerçek Bonferroni). Bu "
                                     "ölçüm kapıya DOKUNMAZ; kutbu yalnız beyan eder.",
                            "grid_disi_satirlar": ["alt-dönem (betimleyici)", "@5 (betimleyici)",
                                                   "min_taban=5 (duyarlılık)",
                                                   "kirli-taban sıkışma (Ders #5 k.3)",
                                                   "kontrolsüz artık-IC ikizi"]},
           "muhur": pkj["muhur"], "bar_muhasebesi": bar_acc, "takvim_muhasebesi": tak_acc,
           "aday_muhasebesi": {**aday_acc, "bar_eslesen_aday_gun": len(aday),
                               "havuz_gun_sayisi": int(V["date"].nunique()),
                               "gun_basina_aday_medyan": O._r6(
                                   float(V.groupby("date").size().median())),
                               "rvol_olculemez_aday_gun": int(V["rvol20"].isna().sum()),
                               "gecmis_olayi_olmayan_aday_gun": int((V["gecikme"] < 0).sum())},
           "ders4_temiz_taban": ders4, "pead_kosum_muhasebesi": pead_acc,
           "hucreler": hucreler, "ders7_eb_kucultme": ders7,
           "KAPILAR": pkj["KAPILAR"], "pozitif_kontrol_civi": pkj["pozitif_kontrol"]["civi_olculen"],
           "pit_assert_ozet": {k: pkj["pit_assert"][k] for k in
                               ("bacak_2_kesme_degismezligi", "bacak_3_bagimsiz_saf_python",
                                "negatif_kontrol_kapi_etkin_mi", "GECTI")}}
    O.json_yaz(O.KLASOR / "sonuc_020.json", out)
    V.to_csv(O.CACHE / "panel020.csv", index=False)
    print("[k020] sonuc_020.json yazıldı", flush=True)
    return out


if __name__ == "__main__":
    main()
