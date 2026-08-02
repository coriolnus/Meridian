"""EDG-2026-016 · TURNOVER ANA-ETKİSİ — SALT-ÖLÇÜM, SANDBOX.

Kart: research/cards/EDG-2026-016-turnover-ana-etkisi.yaml (status: registered).
KART DIŞINA ÖLÇÜM YOK; KARTA DOKUNULMAZ; eşik sonradan DEĞİŞMEZ.

as-of / etiket / temizlik / bekçi kuralları EDG-012 ve EDG-013 ile BİREBİR aynı altyapıdan
(ortak.py DEĞİŞTİRİLMEDİ — sha eşitliği sonuca yazılır; böylece pk.json'daki PK4/PK5 bu tur için
de geçerlidir). Yeni kodun tamamı bu dosyadadır.

KATMANLAR (kart parameter_grid, K+=2):
  1) turnover_ust20                      — o gün turnover21 üst %20; aynı-gün EVREN taban fazlası
  2) turnover_artik_rvol_mom_kontrollu   — rvol20 ve mom21 kontrolünde ARTIK katkı
                                           (çift-sıralama VE artık-IC; EDG-007 şablonu)
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

import ortak as O
import pk as PK

HORIZONS = (10, 20)          # kart: ileri getiri 10/20g
UST_PCT = 0.20               # kart katman adı: turnover_ust20
KONTROL_DILIM = 3            # kontrol kovaları: rvol20 terzili × mom21 terzili (3×3 = 9)
KOVA_MIN = 2                 # kova-içi merkezleme için gereken asgari üye (n=1'de merkezleme
#                              tanım gereği 0 üretir — bu bir ÖLÇÜM DEĞİL, o satır düşer)
PK_CIVI_HEDEF = 0.0645       # kart guard'ı 0.0642'yi anıyor; pk.py'nin kayıtlı hedefi 0.0645,
PK_CIVI_TOL = 0.005          # tolerans 0.005 — İKİSİ DE bu turda değiştirilmedi.

# ============================================================ hızlı Spearman (kanonikle özdeş)
def _rank_avg_np(a: np.ndarray) -> np.ndarray:
    """analytics._rank_avg ile aynı: beraberlikler ORTALAMA rütbeyle kırılır (pandas varsayılanı)."""
    return pd.Series(a).rank().to_numpy()


def spearman_fast(x: np.ndarray, y: np.ndarray):
    rx, ry = _rank_avg_np(x), _rank_avg_np(y)
    sx, sy = rx.std(), ry.std()
    if sx <= 0 or sy <= 0:
        return None
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _gun_indeksi(dates: np.ndarray):
    """Gün bazlı hızlı blok-örnekleme için satırları güne göre sıralı tutan indeks yapısı."""
    uniq, inv = np.unique(dates, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cnt = np.bincount(inv, minlength=len(uniq))
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    return uniq, order, start, cnt


def ic_block_boot_fast(x: np.ndarray, y: np.ndarray, dates: np.ndarray,
                       n_boot: int = O.BOOT_IC, blok: int = O.BLOCK) -> dict:
    """block_boot ile AYNI şema (21 ardışık GÖZLEM GÜNÜ bloğu), IC istatistiği için vektörel yol.

    Kanonik yol (ortak.ic_with_ci → block_boot → analytics.spearman_ic) gün başına ayrı liste
    kurar; bu ölçümde kesit ~886 bin satır ve 600 tekrar olduğu için o yol saatler sürerdi.
    Hızlı yolun kanonikle ÖZDEŞLİĞİ ayrıca sınanır (bekciler.hizli_spearman_ozdesligi)."""
    uniq, order, start, cnt = _gun_indeksi(dates)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3} (blok bootstrap için yetersiz)"}
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = O.RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnt[gun]
        tot = int(c.sum())
        if tot < O.MIN_SLICE:
            atlanan += 1
            continue
        cikis_bas = np.concatenate([[0], np.cumsum(c)[:-1]])
        poz = np.arange(tot) - np.repeat(cikis_bas, c) + np.repeat(start[gun], c)
        idx = order[poz]
        v = spearman_fast(x[idx], y[idx])
        if v is None or not np.isfinite(v):
            atlanan += 1
            continue
        vals.append(v)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": O._r6(np.percentile(a, 2.5)), "hi": O._r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "neden": None}


def ic_hizli(x: np.ndarray, y: np.ndarray, dates: np.ndarray, ci: bool = True) -> dict:
    """Nokta tahmini KANONİK analytics.spearman_ic ile; CI hızlı blok-bootstrap ile."""
    n = int(len(x))
    if n < O.MIN_SLICE:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": f"n<{O.MIN_SLICE}"}
    ic = O.spearman_ic(list(zip(x.tolist(), y.tolist())))
    if ic is None:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": "rütbe değişimi yok"}
    if not ci:
        return {"ic": round(float(ic), 4), "n": n, "ci": None, "anlamli": None,
                "neden": "CI istenmedi (tanı okuması — kart bacağı değil)"}
    c = ic_block_boot_fast(x, y, dates)
    return {"ic": round(float(ic), 4), "n": n,
            "ci": None if c["lo"] is None else {"lo": round(c["lo"], 4),
                                                "hi": round(c["hi"], 4), "seviye": 0.95},
            "ci_meta": c,
            "anlamli": None if c["lo"] is None else bool(c["lo"] > 0 or c["hi"] < 0),
            "pozitif_anlamli": None if c["lo"] is None else bool(c["lo"] > 0),
            "negatif_anlamli": None if c["lo"] is None else bool(c["hi"] < 0),
            "neden": None}


# ============================================================ PANEL (013 ile birebir + close)
def panel(pan, ser, OBS):
    parts, acc = [], {"sembol": 0, "gozlem_hucre": 0, "neden_sayimi": {},
                      "turnover_gecerli": 0, "rvol_gecerli": 0, "mom_gecerli": 0,
                      "ucu_de": 0, "pit_sizinti_satir": 0, "bayat_seri_sembol": {}}
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
               "rvol20": v["rvol20"][idx], "med_hacim21": v["med_hacim21"][idx],
               "close": v["close"][idx]}
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
            acc["pit_sizinti_satir"] += O._leak_kontrol(f, tdates)     # BEKÇİ: filed > t olamaz
            for k, c in zip(*np.unique(nd[nd != ""], return_counts=True)):
                acc["neden_sayimi"][str(k)] = acc["neden_sayimi"].get(str(k), 0) + int(c)
            acc["neden_sayimi"]["dosyalama_yok"] = acc["neden_sayimi"].get("dosyalama_yok", 0) + \
                int(np.sum(nd == "dosyalama_yok"))
            nb = int(np.sum(nd == "bayat_seri"))
            if nb:
                acc["bayat_seri_sembol"][sym] = nb
        parts.append(pd.DataFrame(row))
    D = pd.concat(parts, ignore_index=True)
    D["turnover21"] = D["med_hacim21"] / D["shares"]
    acc["turnover_gecerli"] = int(D["turnover21"].notna().sum())
    acc["rvol_gecerli"] = int(D["rvol20"].notna().sum())
    acc["mom_gecerli"] = int(D["mom21"].notna().sum())
    acc["ucu_de"] = int((D["turnover21"].notna() & D["rvol20"].notna()
                         & D["mom21"].notna()).sum())
    # TAM sözlük korunur (kırpılmış bir sayıyı "0" diye okumak UYDURMA olurdu); okunabilirlik
    # için ayrıca ilk 10 verilir.
    acc["bayat_seri_sembol_ilk10"] = dict(sorted(acc["bayat_seri_sembol"].items(),
                                                 key=lambda kv: -kv[1])[:10])
    return D, acc


# ============================================================ pozitif kontrol (İLK KOŞAN İŞ)
def pozitif_kontrol(pan) -> dict:
    """pk.py ile BİREBİR aynı katman ve aynı hedef; bu turda CANLI yeniden ölçülür."""
    rows, pop_acc = PK.population()
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
        rec["rvol20"] = None if not np.isfinite(f["rvol20"][i]) else float(f["rvol20"][i])
        for h in (5, 10, 20):
            v = f[f"fwd{h}"][i]
            rec[f"fwd{h}"] = None if not np.isfinite(v) else float(v)
        pk_rows.append(rec)
    PKD = pd.DataFrame(pk_rows)
    KAT = PKD[(PKD["kaynak"] == "cf") & (~PKD["near_miss"])]
    out = {"aciklama": "KART GUARD'I — ham rvol20 @20 cf-katman IC çivisi. Bu tur bars_integrity "
                       "DIŞLAMALI yolda; aynı yolda pullback turu 0.0642, WP2 turu 0.0642 ölçtü. "
                       "Çivi tutmazsa boru hattı GEÇERSİZ ve HİÇBİR kart için hüküm yazılmaz.",
           "katman": "counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)",
           "populasyon_muhasebesi": pop_acc, "eslesme_muhasebesi": elem}
    for h in (5, 10, 20):
        sub = KAT[["rvol20", f"fwd{h}", "date"]].dropna()
        out[str(h)] = O.ic_with_ci(sub["rvol20"].to_numpy(float),
                                   sub[f"fwd{h}"].to_numpy(float), sub["date"].to_numpy())
    civi = out["20"]["ic"]
    out["civi_hedef"] = PK_CIVI_HEDEF
    out["civi_olculen"] = civi
    out["civi_sapma"] = None if civi is None else O._r6(abs(civi - PK_CIVI_HEDEF))
    out["tolerans"] = PK_CIVI_TOL
    out["GECTI"] = None if civi is None else bool(abs(civi - PK_CIVI_HEDEF) <= PK_CIVI_TOL)
    return out


# ============================================================ ana ölçüm
def main() -> None:
    print("== 016: barlar ==", flush=True)
    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol", flush=True)

    sonuc = {
        "kart": "EDG-2026-016", "aile": "turnover_main_effect",
        "olcum_tarihi": pd.Timestamp.now("UTC").isoformat(), "sandbox": str(O.SANDBOX),
        "DURUM": None,
        "rol": "ölçüm ajanı — HÜKÜM VERMEZ, hüküm ÖNERİSİ yazar; kart dosyasına DOKUNULMADI",
    }

    # ---------- (0) POZİTİF KONTROL — İLK KOŞAN İŞ (kart guard) ----------
    print("== 016: pozitif kontrol (İLK) ==", flush=True)
    pkc = pozitif_kontrol(pan)
    print(f"   çivi={pkc['civi_olculen']} hedef={pkc['civi_hedef']} → GEÇTİ={pkc['GECTI']}",
          flush=True)

    # ---------- as-of altyapısı + bekçiler ----------
    S = O._shares_ham()
    ser, birincil, sh_acc = O.build_hisse(S)
    fiz = O.fiziksel_bekci(ser, pan)
    sh_acc["fiziksel_bekci"] = fiz
    OBS = O.ortak_takvim(pan)
    D, pacc = panel(pan, ser, OBS)
    print(f"   panel: {len(D)} satır, {D['date'].nunique()} gün", flush=True)

    sonuc["kart_metni_uygulamasi"] = {
        "universe": "full_251 — KAPSAM BEYANLI: bar önbelleğinde dosyası olan ve şablon asgari "
                    "uzunluğunu geçen semboller ölçüldü; düşenler bar_muhasebesi'nde sayılı.",
        "as_of_shares": "EDG-012/013 ile BİREBİR aynı altyapı (ortak.build_hisse, DEĞİŞTİRİLMEDİ): "
                        "dei→us-gaap Outstanding önceliği, Issued ve ağırlıklı-ortalama YOK, "
                        "val>0, donem_turu=anlik, 200g bayatlık bekçisi, split güncel-baz dönüşümü, "
                        "ölçek-hatası penceresi None+neden.",
        "turnover21": "medyan21(hacim) / as_of_shares(t). Bar hacmi GÜNCEL bazda split-düzeltilmiş "
                      "olduğu için hisse sayımı da GÜNCEL baza çevrildi — oran bölünmeden bağımsız.",
        "kontrol_degiskenleri": "rvol20 = ind.rvol20(hacim); mom21 = close[t]/close[t-21]-1. "
                               "TANIMLAR EDG-013 TURUNDAKİYLE BİREBİR (ortak.bar_paneli), "
                               "yeniden tanımlanmadı.",
        "kesit": "İKİ KATMAN DA AYNI KESİTTE: o gün turnover21 VE rvol20 VE mom21 tanımlı "
                 f"semboller, kesit>={O.MIN_KESIT}. Aksi hâlde artık-katkı farkı kapsam farkıyla "
                 "karışırdı.",
        "katman_1": f"turnover_ust20 = o gün turnover21 kesit üst %{int(UST_PCT*100)}",
        "katman_2": "turnover_artik_rvol_mom_kontrollu = AYNI dilim, kontrol kovası tabanıyla "
                    f"(rvol20 terzili × mom21 terzili, {KONTROL_DILIM}×{KONTROL_DILIM}) + artık-IC",
        "taban_katman_1": "aynı-gün EVREN ortalaması (o gün ileri getirisi tanımlı tüm yüklü "
                          "semboller) — EDG-013 ile birebir",
        "taban_katman_2": "aynı-gün AYNI KONTROL KOVASI ortalaması, DIŞARIDA-BIRAK (leave-one-out): "
                          "gözlemin kendisi tabana girmez. Gerekçe: kova ~23 üyeli, kendini içeren "
                          "taban etkiyi 1/n kadar kendine doğru büzerdi; evren tabanı (~210 üye) "
                          "ile kova tabanı arasındaki bu asimetri iki katmanı kıyaslanamaz yapardı. "
                          "Kendini-içeren varyant ayrıca rapor edilir (CI'sız aritmetik dayanıklılık).",
        "cift_siralama": "EDG-007 şablonu: kontrol kovası İÇİNDE turnover üst %20 vs kalanı; "
                         "9 kova hücresi + havuzlanmış kova-içi yayılım.",
        "artik_ic": "GÜN BAZLI kesit OLS: pctrank(turnover21) ~ 1 + pctrank(rvol20) + "
                    "pctrank(mom21); artık e(t,i). IC = havuzlanmış Spearman(e, FAZLA getiri). "
                    "FAZLA getiri kullanılır çünkü artık gün-içinde zaten merkezlidir; ham getiriyle "
                    "havuzlanmış IC gün-düzeyi varyansla sulandırılırdı (ham okuma tanı olarak var).",
        "ci": f"{O.BLOCK} ardışık gözlem günü blok-bootstrap, %95, ortalama {O.BOOT} / IC "
              f"{O.BOOT_IC} tekrar",
        "maliyet": f"kart cost_model: {O.MALIYET_BPS}bps + not. Kill#3 NET fazla üzerinden "
                   f"işletilir: net = brüt − {O.MALIYET_BPS}bps (kartın yazdığı model, birebir). "
                   f"Gidiş-dönüş ({2*O.MALIYET_BPS}bps) BEYANLI DUYARLILIK olarak ayrıca verilir; "
                   "hüküm kartın modeliyle okunur.",
        "K_beyani": "Kart grid'i 2 katman (K+=2). Ufuk 10/20 kartın horizon alanıdır, K çarpanı "
                    "DEĞİLDİR (EDG-013 ile aynı okuma). 9 kova hücresi ve 5'li turnover tablosu "
                    "TANI'dır — havuzlanmış/üst-dilim rakamları hükmü taşır.",
    }
    sonuc["bar_muhasebesi"] = {k: v for k, v in bar_acc.items() if k != "kisa_semboller"}
    sonuc["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])
    sonuc["hisse_muhasebesi"] = {k: v for k, v in sh_acc.items() if k != "split_takvimi"}
    sonuc["panel_muhasebesi"] = pacc

    # ---------------- tabanlar (EDG-013 ile birebir) ----------------
    tab = {}
    for h in HORIZONS:
        tab[h] = D[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"].mean()

    # ---------------- kesit ----------------
    V = D[D["turnover21"].notna() & D["rvol20"].notna() & D["mom21"].notna()].copy()
    kesit = V.groupby("date").size()
    kullanilan = kesit[kesit >= O.MIN_KESIT].index
    V = V[V["date"].isin(kullanilan)].copy()
    V["to_pct"] = V.groupby("date")["turnover21"].rank(pct=True, method="first")
    V["rvol_pct"] = V.groupby("date")["rvol20"].rank(pct=True, method="first")
    V["mom_pct"] = V.groupby("date")["mom21"].rank(pct=True, method="first")
    V["ust"] = V["to_pct"] > 1 - UST_PCT
    V["b_rvol"] = np.clip((V["rvol_pct"] * KONTROL_DILIM).astype(int), 0, KONTROL_DILIM - 1)
    V["b_mom"] = np.clip((V["mom_pct"] * KONTROL_DILIM).astype(int), 0, KONTROL_DILIM - 1)
    V["kova"] = V["b_rvol"] * KONTROL_DILIM + V["b_mom"]
    kesit_kullanilan = kesit[kesit >= O.MIN_KESIT]
    sonuc["kesit_muhasebesi"] = {
        "gozlem_gunu_toplam": int(D["date"].nunique()),
        "kesit_yeterli_gun": int(len(kullanilan)), "min_kesit": O.MIN_KESIT,
        "kesit_buyuklugu": {"medyan": O._r6(kesit_kullanilan.median()),
                            "min": int(kesit_kullanilan.min()),
                            "maks": int(kesit_kullanilan.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "n_satir": int(len(V)), "n_sembol": int(V["ticker"].nunique()),
        "turnover21_dagilimi": {str(q): O._r6(V["turnover21"].quantile(q))
                                for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
        "kova_buyuklugu": {"medyan": O._r6(V.groupby(["date", "kova"]).size().median()),
                           "n_kova": int(KONTROL_DILIM ** 2)},
    }

    # akrabalık beyanı (kart guard'ının arka planı — 013 ile aynı okuma)
    orn = V[["turnover21", "rvol20", "mom21"]].sample(n=min(200000, len(V)), random_state=11)
    sonuc["akrabalik_beyani"] = {
        "not": "rvol20 ZATEN skorda; kontrol değişkenleriyle akrabalık beyan edilir.",
        "n_ornek": int(len(orn)),
        "spearman_turnover_rvol20": O._r6(O.spearman_np(orn["turnover21"], orn["rvol20"])),
        "spearman_turnover_mom21": O._r6(O.spearman_np(orn["turnover21"], orn["mom21"])),
        "gun_ici_ortalama_spearman_turnover_rvol": O._r6(np.nanmean([
            O.spearman_np(g["turnover21"], g["rvol20"]) or np.nan
            for _, g in V.groupby("date") if len(g) >= 30])),
        "gun_ici_ortalama_spearman_turnover_mom": O._r6(np.nanmean([
            O.spearman_np(g["turnover21"], g["mom21"]) or np.nan
            for _, g in V.groupby("date") if len(g) >= 30])),
    }

    # ================= I. KATMAN — turnover_ust20, EVREN tabanı =================
    print("== 016: katman 1 (turnover_ust20) ==", flush=True)
    sub = V[V["ust"]]
    kat1 = {"n_sembol_gun": int(len(sub)), "n_gun": int(sub["date"].nunique()),
            "n_sembol": int(sub["ticker"].nunique()),
            "turnover21_medyan": O._r6(sub["turnover21"].median()),
            "turnover21_ort": O._r6(sub["turnover21"].mean()),
            "mom21_ort": O._r6(sub["mom21"].mean()), "rvol20_ort": O._r6(sub["rvol20"].mean()),
            "ufuklar": {}}
    fazla_kayit = {}
    for h in HORIZONS:
        s2 = sub[["date", f"fwd{h}"]].dropna()
        y = s2[f"fwd{h}"].to_numpy(float)
        dts = s2["date"].to_numpy()
        base = s2["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        kat1["ufuklar"][str(h)] = {"ham": O.mean_with_ci(y, dts),
                                   "evren_fazlasi": O.mean_with_ci((y - base)[ok], dts[ok])}
        fazla_kayit[h] = ((y - base)[ok], dts[ok])
    sonuc["i_katman_turnover_ust20"] = kat1

    # ================= II. KATMAN — ARTIK (kontrol: rvol20 × mom21) =================
    print("== 016: katman 2a (çift-sıralama) ==", flush=True)
    art = {"kontrol": "rvol20 terzili × mom21 terzili (gün bazlı kesit), 9 kova"}

    # --- A1: kontrol kovası tabanlı (leave-one-out) fazla, KAYITLI üst %20 dilimi ---
    a1 = {"tanim": "KAYITLI dilim (turnover üst %20) — taban EVREN yerine AYNI-GÜN AYNI-KOVA "
                   "leave-one-out ortalaması. Katman 1 ile TEK farkı tabandır; aradaki düşüş "
                   "doğrudan rvol/mom kontrolünün bedelidir.", "ufuklar": {}}
    a1_kayit = {}
    for h in HORIZONS:
        g = V[["date", "kova", "ust", f"fwd{h}"]].dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["date", "kova"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)                  # kendini DIŞARIDA bırakan kova tabanı
            ici = s_k / n_k                                  # kendini İÇEREN varyant (dayanıklılık)
        yeter = n_k >= KOVA_MIN
        m = g["ust"].to_numpy(bool) & yeter & np.isfinite(loo)
        a1["ufuklar"][str(h)] = {
            "kova_yetersiz_dusen_satir": int((~yeter).sum()),
            "loo_kova_fazlasi": O.mean_with_ci(yv[m] - loo[m], g["date"].to_numpy()[m]),
            "kendini_iceren_kova_fazlasi_ort_CI_YOK": O._r6(float(np.mean(
                (yv - ici)[g["ust"].to_numpy(bool) & yeter]))),
        }
        a1_kayit[h] = (yv[m] - loo[m], g["date"].to_numpy()[m])
    art["A1_kova_tabanli_ust20_fazlasi"] = a1

    # --- A2: EDG-007 şablonu — kova İÇİNDE üst %20 vs kalanı (9 hücre + havuzlanmış) ---
    a2 = {"tanim": "EDG-007 çift-sıralama şablonu: her kontrol kovasında O KOVANIN turnover üst "
                   "%20'si vs kalanı; hücre farkları + kova-içi merkezlenmiş havuzlanmış yayılım.",
          "ufuklar": {}}
    V["to_pct_kova"] = V.groupby(["date", "kova"])["turnover21"].rank(pct=True, method="first")
    V["ust_kova"] = V["to_pct_kova"] > 1 - UST_PCT
    for h in HORIZONS:
        g = V[["date", "kova", "b_rvol", "b_mom", "ust_kova", f"fwd{h}"]] \
            .dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["date", "kova"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)
        yeter = n_k >= KOVA_MIN
        g = g.assign(_merkezli=yv - loo, _yeter=yeter)
        hucre = {}
        for kv, gg in g[g["_yeter"]].groupby("kova"):
            hi = gg[gg["ust_kova"]]
            lo = gg[~gg["ust_kova"]]
            ad = f"rvol_t{int(gg['b_rvol'].iloc[0])+1}_mom_t{int(gg['b_mom'].iloc[0])+1}"
            if len(hi) < O.MIN_SLICE or len(lo) < O.MIN_SLICE:
                hucre[str(int(kv))] = {"ad": ad, "n_yuksek": int(len(hi)), "n_kalan": int(len(lo)),
                                       "fark": None, "ci": None, "anlamli": None,
                                       "neden": f"dilim < {O.MIN_SLICE}"}
                continue
            r = O.fark_with_ci(hi[f"fwd{h}"].to_numpy(float), hi["date"].to_numpy(),
                               lo[f"fwd{h}"].to_numpy(float), lo["date"].to_numpy())
            r["ad"] = ad
            r["ort_yuksek"] = O._r6(hi[f"fwd{h}"].mean())
            r["ort_kalan"] = O._r6(lo[f"fwd{h}"].mean())
            hucre[str(int(kv))] = r
        gy = g[g["_yeter"]]
        hi, lo = gy[gy["ust_kova"]], gy[~gy["ust_kova"]]
        hav = O.fark_with_ci(hi["_merkezli"].to_numpy(float), hi["date"].to_numpy(),
                             lo["_merkezli"].to_numpy(float), lo["date"].to_numpy())
        hav["aciklama"] = "kova-içi (leave-one-out) MERKEZLENMİŞ getirilerde üst%20 − kalan: " \
                          "kova bileşimi farkından arınmış havuzlanmış yayılım"
        a2["ufuklar"][str(h)] = {"kovalar": hucre, "havuzlanmis": hav}
    art["A2_edg007_kova_ici_ust20_eksi_kalan"] = a2

    # --- B: ARTIK-IC (gün bazlı kesit OLS artığı) ---
    print("== 016: katman 2b (artık-IC) ==", flush=True)
    e = np.full(len(V), np.nan)
    ortog = {"maks_mutlak_kova_korelasyon": 0.0, "maks_mutlak_gun_ici_ortalama": 0.0,
             "tekil_gun": 0, "gun": 0}
    x_all = V["to_pct"].to_numpy(float)
    z1_all = V["rvol_pct"].to_numpy(float)
    z2_all = V["mom_pct"].to_numpy(float)
    pos = 0
    kod = V["date"].to_numpy()
    _, inv = np.unique(kod, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cnt = np.bincount(inv)
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    for gi in range(len(cnt)):
        ii = order[start[gi]:start[gi] + cnt[gi]]
        if len(ii) < 4:
            ortog["tekil_gun"] += 1
            continue
        A = np.column_stack([np.ones(len(ii)), z1_all[ii], z2_all[ii]])
        try:
            beta, *_ = np.linalg.lstsq(A, x_all[ii], rcond=None)
        except np.linalg.LinAlgError:
            ortog["tekil_gun"] += 1
            continue
        e[ii] = x_all[ii] - A @ beta
        ortog["gun"] += 1
    V["artik"] = e
    # ortogonallik bekçisi: artık kontrol değişkenlerine dik ve gün-içi ortalaması 0 olmalı
    okv = V[["date", "artik", "rvol_pct", "mom_pct"]].dropna()
    c1, c2, m0 = [], [], []
    for _, gg in okv.groupby("date"):
        if len(gg) < 10:
            continue
        a = gg["artik"].to_numpy()
        c1.append(abs(np.corrcoef(a, gg["rvol_pct"].to_numpy())[0, 1]))
        c2.append(abs(np.corrcoef(a, gg["mom_pct"].to_numpy())[0, 1]))
        m0.append(abs(a.mean()))
    ortog["maks_mutlak_kova_korelasyon"] = O._r6(max(max(c1), max(c2)))
    ortog["maks_mutlak_gun_ici_ortalama"] = O._r6(max(m0))
    ortog["gecti"] = bool(max(max(c1), max(c2)) < 1e-8 and max(m0) < 1e-8)
    ortog["tanim"] = "gün bazlı OLS artığı: kontrol değişkenlerine kesit-içi TAM dik ve gün-içi " \
                     "ortalaması 0 olmalı; değilse artıklaştırma yapılmamıştır"

    icb = {"tanim": "havuzlanmış Spearman IC. HEADLINE: artık ↔ FAZLA getiri (evren tabanı "
                    "düşülmüş). Ham getiriye karşı okuma TANI (CI'sız).",
           "ufuklar": {}}
    for h in HORIZONS:
        g = V[["date", "artik", "to_pct", f"fwd{h}"]].dropna().copy()
        base = g["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        g = g[ok].copy()
        fz = g[f"fwd{h}"].to_numpy(float) - base[ok]
        dts = g["date"].to_numpy()
        icb["ufuklar"][str(h)] = {
            "artik_ic_fazla": ic_hizli(g["artik"].to_numpy(float), fz, dts),
            "ham_turnover_ic_fazla": ic_hizli(g["to_pct"].to_numpy(float), fz, dts),
            "artik_ic_HAM_getiri_TANI_CI_YOK": ic_hizli(
                g["artik"].to_numpy(float), g[f"fwd{h}"].to_numpy(float), dts, ci=False),
        }
    art["B_artik_ic"] = icb
    art["artik_ortogonallik_bekcisi"] = ortog
    sonuc["ii_katman_turnover_artik_rvol_mom_kontrollu"] = art

    # ================= III. MALİYET-SONRASI NET (kill#3) =================
    print("== 016: maliyet-sonrası net ==", flush=True)
    c1_ = O.MALIYET_BPS / 10000.0
    c2_ = 2 * O.MALIYET_BPS / 10000.0

    def net(blok, c):
        if blok.get("ort") is None or not blok.get("ci"):
            return {"brut": blok.get("ort"), "net": None, "ci": None,
                    "neden": blok.get("neden") or "brüt ölçülemedi"}
        return {"brut": blok["ort"], "maliyet": O._r6(c), "net": O._r6(blok["ort"] - c),
                "ci": {"lo": O._r6(blok["ci"]["lo"] - c), "hi": O._r6(blok["ci"]["hi"] - c),
                       "seviye": 0.95},
                "net_pozitif_anlamli": bool(blok["ci"]["lo"] - c > 0),
                "net_ort_pozitif": bool(blok["ort"] - c > 0), "neden": None}

    mal = {"tanim": "Maliyet bir SABİT olduğundan CI aynı sabitle ötelenir (bootstrap yeniden "
                    "koşulmaz — cebirsel özdeş). Kart modeli tek-yön; gidiş-dönüş BEYANLI "
                    "duyarlılıktır, hüküm kart modeliyle okunur.",
           "kart_modeli_tek_yon_bps": O.MALIYET_BPS, "duyarlilik_gidis_donus_bps": 2 * O.MALIYET_BPS,
           "ufuklar": {}}
    for h in HORIZONS:
        mal["ufuklar"][str(h)] = {
            "katman1_evren_fazlasi": {
                "kart_modeli": net(kat1["ufuklar"][str(h)]["evren_fazlasi"], c1_),
                "gidis_donus_duyarlilik": net(kat1["ufuklar"][str(h)]["evren_fazlasi"], c2_)},
            "katman2_kova_fazlasi_A1": {
                "kart_modeli": net(a1["ufuklar"][str(h)]["loo_kova_fazlasi"], c1_),
                "gidis_donus_duyarlilik": net(a1["ufuklar"][str(h)]["loo_kova_fazlasi"], c2_)},
        }
    # kartın "yüksek-turnover dilimi ucuz işlem görür" BEYANI — betimleyici kanıt
    V["dolar_hacim"] = V["med_hacim21"] * V["close"]
    mal["likidite_beyani"] = {
        "not": "Kart cost_model notu: 'yüksek-turnover diliminin kendisi ucuz işlem görür'. "
               "Betimleyici kanıt (CI YOK, kart bacağı DEĞİL): dilimin medyan-21g DOLAR hacmi.",
        "ust20_medyan_dolar_hacim": O._r6(V.loc[V["ust"], "dolar_hacim"].median()),
        "evren_medyan_dolar_hacim": O._r6(V["dolar_hacim"].median()),
        "ust20_medyan_dolar_hacim_orani": O._r6(
            V.loc[V["ust"], "dolar_hacim"].median() / V["dolar_hacim"].median()),
        "ust20_medyan_kapanis": O._r6(V.loc[V["ust"], "close"].median()),
        "evren_medyan_kapanis": O._r6(V["close"].median()),
    }
    sonuc["iii_maliyet_sonrasi_net"] = mal

    # ================= IV. TANI (K harcanmaz, CI YOK) =================
    tani = {"not": "TANI — kart grid'inde OLMAYAN kesitler. CI BİLEREK hesaplanmadı; CI'lı "
                   "sınansaydı K çarpılırdı. Üst %20 dilimi (=5'lik tablonun 4. kovası) kartın "
                   "KAYITLI katmanıdır ve CI'sı yukarıda I. bölümdedir."}
    V["to_q5"] = V.groupby("date")["turnover21"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    q5 = {}
    for h in HORIZONS:
        g = V[["to_q5", "date", "turnover21", f"fwd{h}"]].dropna()
        g = g.assign(fazla=g[f"fwd{h}"].to_numpy(float) - g["date"].map(tab[h]).to_numpy(float))
        g = g.dropna(subset=["fazla"])
        q5[str(h)] = {str(int(k)): {"n": int(len(v)), "fazla_ort": O._r6(v["fazla"].mean()),
                                    "turnover_ort": O._r6(v["turnover21"].mean())}
                      for k, v in g.groupby("to_q5")}
    tani["turnover_q5_evren_fazlasi"] = {"aciklama": "0 = en düşük turnover, 4 = en yüksek",
                                         "ufuklar": q5}
    # EDG-013 karşılaştırması: aynı kesitte mom-koşullu okuma (013'ün kayıtlı dilimi)
    tani["edg013_karsilastirmasi"] = {
        "aciklama": "013'ün kayıtlı dilimi (mom üst %20 ∧ turnover > gün medyanı) BU turun "
                    "kesitinde; 013 hükmünün bu ölçümle birlikte okunması için.",
        "ufuklar": {}}
    V["mom_ust"] = V["mom_pct"] > 1 - 0.20
    V["to_med_ust"] = V["turnover21"] > V.groupby("date")["turnover21"].transform("median")
    m013 = V[V["mom_ust"] & V["to_med_ust"]]
    for h in HORIZONS:
        s2 = m013[["date", f"fwd{h}"]].dropna()
        base = s2["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        tani["edg013_karsilastirmasi"]["ufuklar"][str(h)] = {
            "n": int(ok.sum()),
            "evren_fazlasi_ort_CI_YOK": O._r6(float(np.mean(
                (s2[f"fwd{h}"].to_numpy(float) - base)[ok]))),
        }
    sonuc["iv_tani"] = tani

    # ================= BEKÇİLER =================
    def _sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    eski = json.load(open(O.SANDBOX / "kod_damgasi.json"))
    ortak_ayni = _sha(O.SANDBOX / "ortak.py") == eski["olcum_kodu_sha256"]["ortak.py"]
    pk_ayni = _sha(O.SANDBOX / "pk.py") == eski["olcum_kodu_sha256"]["pk.py"]
    eski_pk = json.load(open(O.SANDBOX / "pk.json"))

    # kartın adıyla andığı SCHW vakası — bekçinin GERÇEKTEN o boşluğu kapattığının kanıtı
    schw = {"neden": "SCHW serisi yok"}
    _s = ser.get("SCHW")
    if _s is not None and len(_s.filed) > 1:
        fd = pd.to_datetime(_s.filed)
        bosluk = (fd[1:] - fd[:-1]).days
        j = int(np.argmax(bosluk))
        schw = {"en_buyuk_dosyalama_boslugu_gun": int(bosluk[j]),
                "bosluk_baslangic_filed": str(_s.filed[j]), "bosluk_bitis_filed": str(_s.filed[j + 1]),
                "esik_gun": O.BAYAT_GUN,
                "bosluk_esigi_asiyor": bool(bosluk[j] > O.BAYAT_GUN),
                "bu_turda_bayat_isaretlenen_hucre": int(pacc["bayat_seri_sembol"].get("SCHW", 0))}
        _m = D[(D["ticker"] == "SCHW") & (D["date"] > str(_s.filed[j])) &
               (D["date"] <= str(_s.filed[j + 1]))]
        schw["bosluk_penceresindeki_gozlem_gunu"] = int(len(_m))
        schw["bosluk_penceresinde_turnover_tanimli"] = int(_m["turnover21"].notna().sum())
        schw["yorum"] = ("Bekçi olmasaydı boşluğun BAŞINDAKİ hisse sayımı boşluk boyunca "
                         "taşınır ve bu pencerede uydurma turnover üretirdi; "
                         "'bosluk_penceresinde_turnover_tanimli' bekçinin kapattığı kadarını gösterir.")
    sonuc["bekciler"] = {
        "pozitif_kontrol_CANLI": pkc,
        "pk4_pk5_devralma": {
            "kural": "PK4 (yol tutarlılığı) ve PK5 (as-of/split/hızlı-ortalama/fundamentals "
                     "özdeşlikleri) ortak.py ve pk.py üzerinde tanımlıdır. Bu tur İKİ DOSYA DA "
                     "DEĞİŞTİRİLMEDİ (sha eşitliği aşağıda) ve girdi damgaları aynı — bu yüzden "
                     "pk.json'daki sonuçlar bu tur için de geçerlidir; yeniden koşmak aynı "
                     "sayıyı üretirdi (RNG tohumlu).",
            "ortak_py_sha_ayni": bool(ortak_ayni), "pk_py_sha_ayni": bool(pk_ayni),
            "pk4_gecti": eski_pk["pk4_yol_tutarliligi"]["gecti"],
            "pk5_gecti": eski_pk["pk5_ozdeslikler"]["gecti"],
            "pk5_alt": {k: v.get("gecti") for k, v in eski_pk["pk5_ozdeslikler"].items()
                        if isinstance(v, dict)},
            "onceki_tur_civi": eski_pk["pozitif_kontrol"]["civi_olculen"],
        },
        "fiziksel_devir_bekcisi": fiz,
        "bayatlik_bekcisi_200g": {
            "kural": f"son dosyalama t'den {O.BAYAT_GUN} günden eskiyse as-of None + neden="
                     f"'bayat_seri' (SCHW vakası: dei serisinde 2020-08 → 2025-02 boşluk)",
            "bayat_seri_hucre": pacc["neden_sayimi"].get("bayat_seri"),
            "en_cok_etkilenen_sembol_ilk10": pacc["bayat_seri_sembol_ilk10"],
            "etkilenen_sembol_sayisi": len(pacc["bayat_seri_sembol"]),
            "SCHW_vakasi": schw,
        },
        "pit_sizinti": {"kural": "seçilen as-of kaydının filed'ı gözlem gününü ASLA aşamaz",
                        "ihlal_satir": pacc["pit_sizinti_satir"],
                        "gecti": bool(pacc["pit_sizinti_satir"] == 0)},
        "artik_ortogonallik": ortog,
    }

    # hızlı Spearman ≡ kanonik spearman_ic (yeni hızlı yolun özdeşlik sınavı)
    rng = np.random.default_rng(16)
    gg = V[["artik", "fwd20"]].dropna()
    xs, ys = gg["artik"].to_numpy(float), gg["fwd20"].to_numpy(float)
    farklar = []
    for n in (5000, 50000, len(xs)):
        i = rng.choice(len(xs), size=n, replace=False) if n < len(xs) else np.arange(len(xs))
        kan = O.spearman_ic(list(zip(xs[i].tolist(), ys[i].tolist())))
        hiz = spearman_fast(xs[i], ys[i])
        farklar.append(abs(kan - hiz))
    sonuc["bekciler"]["hizli_spearman_ozdesligi"] = {
        "tanim": "IC bootstrap'ının hızlı yolu, kanonik analytics.spearman_ic ile BİREBİR aynı "
                 "sayıyı vermeli (nokta tahminleri zaten kanonik yoldan alınır; bu sınav CI'nın "
                 "dayandığı yolu doğrular)",
        "n_ornek": 3, "maks_mutlak_fark": O._r6(max(farklar)),
        "gecti": bool(max(farklar) < 1e-12)}

    # ================= HÜKÜM ÖNERİSİ =================
    def gk(d, *ks):
        for k in ks:
            if d is None:
                return None
            d = d.get(k)
        return d

    b1 = {str(h): {k: gk(kat1, "ufuklar", str(h), "evren_fazlasi", k)
                   for k in ("n", "ort", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli")}
          for h in HORIZONS}
    bA1 = {str(h): {k: gk(a1, "ufuklar", str(h), "loo_kova_fazlasi", k)
                    for k in ("n", "ort", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli")}
           for h in HORIZONS}
    bA2 = {str(h): {k: gk(a2, "ufuklar", str(h), "havuzlanmis", k)
                    for k in ("nA", "nB", "fark", "ci", "anlamli", "pozitif_anlamli",
                              "negatif_anlamli")} for h in HORIZONS}
    bIC = {str(h): {k: gk(icb, "ufuklar", str(h), "artik_ic_fazla", k)
                    for k in ("ic", "n", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli")}
           for h in HORIZONS}

    HEAD = "20"      # kart success_metric: "üst-dilim fazlası @20"
    bacak1 = bool(b1[HEAD]["pozitif_anlamli"])
    cs_a1 = bool(bA1[HEAD]["pozitif_anlamli"])
    cs_a2 = bool(bA2[HEAD]["pozitif_anlamli"])
    cift_siralama = bool(cs_a1 and cs_a2)            # İKİSİ birden — muhafazakâr okuma
    artik_ic = bool(bIC[HEAD]["pozitif_anlamli"])
    bacak2 = bool(cift_siralama and artik_ic)        # kart: "çift-sıralama VE artık-IC"
    net_kart = gk(mal, "ufuklar", HEAD, "katman1_evren_fazlasi", "kart_modeli")
    net_poz = bool(net_kart and net_kart.get("net") is not None and net_kart["net"] > 0)

    hukum = {
        "kart_success_metric": "üst-dilim fazlası @20 anlamlı POZİTİF VE artık-katkı anlamlı "
                               "(çift-sıralama VE artık-IC)",
        "degerlendirme_ufku": HEAD + " (kart success_metric'i @20 yazıyor; @10 raporda tam)",
        "bacaklar": {"i_ust20_evren_fazlasi": b1,
                     "ii_a1_kova_tabanli_fazla": bA1,
                     "ii_a2_edg007_havuzlanmis_yayilim": bA2,
                     "ii_b_artik_ic_fazla": bIC,
                     "iii_maliyet_sonrasi_net": {str(h): gk(mal, "ufuklar", str(h))
                                                 for h in HORIZONS}},
        "bacak1_ust20_pozitif_anlamli": bacak1,
        "cift_siralama_A1_pozitif_anlamli": cs_a1,
        "cift_siralama_A2_pozitif_anlamli": cs_a2,
        "cift_siralama_GECTI_ikisi_birden": cift_siralama,
        "artik_ic_pozitif_anlamli": artik_ic,
        "bacak2_artik_katki_GECTI": bacak2,
        "success_metric_KARSILANDI": bool(bacak1 and bacak2),
        "kill1_ust_dilim_CI_0_ici": bool(b1[HEAD]["anlamli"] is False),
        "kill2_artik_yok": bool(not bacak2),
        "kill3_maliyet_sonrasi_net_sifir_alti": bool(not net_poz),
        "pozitif_kontrol_GECTI": pkc["GECTI"],
    }
    if pkc["GECTI"] is not True:
        hukum["oneri"] = "HÜKÜM YAZILAMAZ — pozitif kontrol çivisi tutmadı, boru hattı geçersiz"
    elif hukum["kill1_ust_dilim_CI_0_ici"]:
        hukum["oneri"] = ("ARŞİV — kill#1 (üst dilim fazlası CI-0-içi; EDG-013 tanısı "
                          "yanılsamaydı, o da nota düşer)")
    elif hukum["kill3_maliyet_sonrasi_net_sifir_alti"]:
        hukum["oneri"] = "ARŞİV — kill#3 (brüt var, maliyet-sonrası net yok) + not"
    elif hukum["kill2_artik_yok"]:
        hukum["oneri"] = ("ARŞİV — kill#2 ('akraba sinyal': rvol/mom açıklıyor); EDG-013 de aynı "
                          "gerekçeyle arşive iner")
    elif hukum["success_metric_KARSILANDI"]:
        hukum["oneri"] = "SUCCESS — kart ölçütü karşılandı"
    else:
        hukum["oneri"] = "KARMA — bacaklar ayrışıyor, hüküm Rol-1'de"
    hukum["edg013_yansimasi"] = (
        "Kart tezi: ana etki bağımsız-anlamlıysa sinyal turnover'dır (013'ün etkileşim-tezi düşer, "
        "sinyal yaşar); artık yoksa ikisi de rvol/mom akrabalığına düşer. Yukarıdaki bayraklar bu "
        "iki dalın hangisinin geçerli olduğunu verir; 013'ün statü kararı Rol-1'dedir.")
    sonuc["hukum_onerisi"] = hukum
    sonuc["DURUM"] = "OLCULDU"

    O.json_yaz(O.SANDBOX / "sonuc_016.json", sonuc)
    print(f"== yazıldı: sonuc_016.json · öneri={hukum['oneri']} ==", flush=True)


if __name__ == "__main__":
    main()
