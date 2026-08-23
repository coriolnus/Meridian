"""EDG-2026-050 — PEAD 8-K ÖLÇÜMÜ (kart: research/cards/EDG-2026-050-pead-8k.yaml, DONUK).

BEYANLAR (kart + görev akışı AYNEN):
  · Olay: 8-K Item-2.02 `filed` günü (t0). Aynı-gün çiftler ve 14 GÜN İÇİNDEKİ ardışık
    dosyalamalar TEK OLAY (zincir-tabanlı kümeleme — validate_8k.py (F) tanımı BİREBİR;
    referans W14 toplamı 16.819'a karşı sınanır). Kümeleme atlanırsa kart geçersiz (kill#5).
  · Tepki: [t0−1, t0+1] kümülatif getiri − AYNI-PENCERE evren ortalaması (±1g ZORUNLU,
    BMO/AMC bilinmiyor — kill#4). Evren = o pencere iki ucunda da barı olan paneldeki
    semboller (payda olay başına kaydedilir; payda < 50 → olay None+neden, şablon MIN_KESIT).
  · Dilimler: tepki_ust_20pct / tepki_alt_20pct — yüzdelikler TÜM geçerli olay dağılımından;
    eşik dökümü sürüklenme ölçülmeden ÖNCE yazılır/basılır (ölçüm-önce döküm beyanı).
  · Sürüklenme: t0+2→t0+20 ve t0+2→t0+60 (İŞLEM GÜNÜ, sembolün kendi bar serisinde);
    fazla-getiri = sembol bileşik getirisi − aynı GÜNLERDEKİ evren-ortalama günlük
    getirilerin bileşiği ("aynı-gün evren ortalaması tabanı"; günlük payda beyanlı).
  · CI: 21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap (şablon cebiri), SEED 20260812 (görev).
  · Maliyet: 10bps ve 20bps TEK-YÖN, ortalamadan bir kez düşülür (kart cost_model +
    EDG-016 şablon emsali); gidiş-dönüş (×2) değerleri TANI olarak ayrıca yazılır.
  · kill#3: geçerli olay < 8.000 → ASKI damgası, ölçüm DURUR (dilim/sürüklenme yazılmaz).
  · CIK-kesiği: ilk 2.02 > 2010-06-30 olan semboller — erken dönemleri "veri yok" (duyuru
    yok DEĞİL); sembol-dönem None+neden kapsam beyanına yazılır (README §7).
  · UYDURMA YASAĞI: ölçülemeyen her hücre None + neden.
  · PIT öz-sınaması: hiçbir tepki/dilim hesabı t0+1 KAPANIŞINDAN sonraki bilgiyi t0-kararına
    sokmaz (kod-içi assert + yapısal dilimleme close[:i+2]); sürüklenme yalnız SONUÇ tarafıdır.
  · Bar yolu: wp2_olcum şablonu ortak.load_bars (takvim kapısı + bars_integrity, KANONİK
    defter yolu) — pozitif kontrol (pk.py) ile AYNI panel. state SALT-OKUNUR.
  · Survivorship: evren bugünün 251'i — her pozitif okuma ÜST-SINIR şerhlidir (raporda).

BU DOSYA HÜKÜM VERMEZ. Hüküm Rol-1'indir.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

import ortak as O
from meridian.adapters import data as dat

BURASI = pathlib.Path(__file__).resolve().parent
CSV = O.EDGAR / "earnings_8k_tarihleri.csv"

SEED = 20260812                      # görev talimatı: sürüklenme CI'ları bu tohumla
RNG050 = np.random.default_rng(SEED)
KUME_GUN = 14                        # kill#5: değiştirilemez
REF_W14_OLAY = 16_819                # validate_8k.py (F) W14 referansı (17.535 − 716)
CIK_KESIK_SINIR = "2010-06-30"       # README §7: ilk 2.02 bu tarihten sonra → sessiz kesik
KILL3_ESIK = 8_000
UFUKLAR = (20, 60)
MALIYET_BPS = (10.0, 20.0)           # tek-yön
T0_MAKS_BOSLUK_GUN = 3               # filed → ilk bar eşleşmesi için azami takvim boşluğu
MIN_PAYDA = O.MIN_KESIT              # 50 — şablon kesit tabanı, evren paydasına uygulanır


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _gun(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


# ------------------------------------------------------------------ [1] OLAY İNŞASI
def olaylar_kur() -> tuple[list, dict]:
    df = pd.read_csv(CSV, dtype=str)
    acc = {"ham_satir": int(len(df)), "csv_sha256": _sha(CSV)}
    df = df[df["items"].fillna("").str.contains("2.02", regex=False)]
    acc["item202_disi_dusen"] = acc["ham_satir"] - int(len(df))
    df = df.sort_values(["symbol", "filed", "accn"]).reset_index(drop=True)
    acc["csv_sembol"] = int(df["symbol"].nunique())

    def kumele(sub: pd.DataFrame) -> list[str]:
        """validate_8k.py (F) BİREBİR: ardışık satır arası > KUME_GUN gün → yeni olay;
        olayın t0'ı = kümenin İLK satırının filed'ı (zincir-tabanlı)."""
        t0lar, son = [], None
        for f in sub["filed"]:
            d = _gun(f)
            if son is None or (d - son).days > KUME_GUN:
                t0lar.append(f)
            son = d
        return t0lar

    tum_olay = {s: kumele(g) for s, g in df.groupby("symbol", sort=True)}
    n_tum = sum(len(v) for v in tum_olay.values())
    acc["kumeleme_tam_csv_olay"] = n_tum
    acc["kumeleme_birlestirilen_satir"] = int(len(df)) - n_tum
    acc["kumeleme_ref_uyum"] = bool(n_tum == REF_W14_OLAY)
    assert acc["kumeleme_ref_uyum"], (
        f"kümeleme referansla uyuşmadı: {n_tum} != {REF_W14_OLAY} — düzenek geçersiz")

    # CIK-kesiği envanteri (tam CSV üzerinde; README §7 kriteri BİREBİR)
    ilk = df.groupby("symbol")["filed"].min()
    kesik = sorted(ilk[ilk > CIK_KESIK_SINIR].index)
    acc["cik_kesigi_sembol_n_tam_csv"] = len(kesik)          # beklenen 41
    acc["cik_kesigi_ref_uyum_41"] = bool(len(kesik) == 41)
    acc["cik_kesigi"] = [
        {"symbol": s, "ilk_202": ilk[s],
         "none_donem": ["2010-01-01", ilk[s]],
         "neden": "CIK-kesiği/IPO: bu aralıkta VERİ YOK (duyuru yok değil — README §7); "
                  "sembol-dönem ölçülemez → None"}
        for s in kesik]

    evren = sorted(dat.REPLAY_UNIVERSE)
    acc["evren_n"] = len(evren)
    csv_sym = set(tum_olay)
    acc["evren_disi_csv_sembol"] = sorted(csv_sym - set(evren))
    acc["csv_de_olmayan_evren_sembol"] = [
        {"symbol": s, "neden": "8-K 2.02 serisi CSV'de yok → sembolün tümü None "
                               "(ör. yabancı ihraççı boşluğu, README §8)"}
        for s in evren if s not in csv_sym]

    olaylar = [(s, t0) for s in evren if s in tum_olay for t0 in tum_olay[s]]
    acc["evren_ici_olay_kumeleme_sonrasi"] = len(olaylar)
    return olaylar, acc


# ------------------------------------------------------------------ EVREN PANELİ
def panel_matris(pan: dict):
    syms = sorted(pan)
    tum_gun = sorted(set().union(*[set(v["dates"].tolist()) for v in pan.values()]))
    gidx = {d: i for i, d in enumerate(tum_gun)}
    C = np.full((len(tum_gun), len(syms)), np.nan)
    for j, s in enumerate(syms):
        v = pan[s]
        C[[gidx[d] for d in v["dates"]], j] = v["close"]
    # günlük evren-ortalama getiri (bitiş gününe yazılır; sembolün kendi ardışık barından)
    rs = np.zeros(len(tum_gun))
    rc = np.zeros(len(tum_gun))
    for j, s in enumerate(syms):
        v = pan[s]
        cl = v["close"]
        r = cl[1:] / cl[:-1] - 1.0
        idx = np.array([gidx[d] for d in v["dates"]])[1:]
        np.add.at(rs, idx, r)
        np.add.at(rc, idx, 1.0)
    runiv = np.where(rc > 0, rs / np.maximum(rc, 1.0), np.nan)
    return tum_gun, gidx, C, runiv, rc


# ------------------------------------------------------------------ [2] TEPKİ + [4] SÜRÜKLENME
def olay_olc(olaylar, pan, gidx, C, runiv, rc):
    kayit, neden_say = [], {}

    def dus(s, t0, neden):
        neden_say[neden] = neden_say.get(neden, 0) + 1
        kayit.append({"symbol": s, "t0": t0, "tepki": None, "neden": neden})

    for s, t0 in olaylar:
        v = pan.get(s)
        if v is None:
            dus(s, t0, "bar_paneli_yok (şablon bar yolu sembolü yüklemedi)")
            continue
        dates = v["dates"]
        i = int(np.searchsorted(dates, t0, side="left"))
        if i >= len(dates):
            dus(s, t0, "t0_bar_serisi_sonrasi")
            continue
        if dates[i] != t0 and (_gun(dates[i]) - _gun(t0)).days > T0_MAKS_BOSLUK_GUN:
            dus(s, t0, f"t0_bar_boslugu>{T0_MAKS_BOSLUK_GUN}g")
            continue
        if i - 1 < 0:
            dus(s, t0, "t0_oncesi_bar_yok (bar serisi başlangıcı/integrity kırpması)")
            continue
        if i + 1 >= len(dates):
            dus(s, t0, "t0_sonrasi_bar_yok (seri sonu)")
            continue

        # -------- PIT: tepki YALNIZ close[:i+2] görür (yapısal geriye-bakışsızlık)
        gecmis = v["close"][:i + 2]
        d_prev, d_bar, d_next = dates[i - 1], dates[i], dates[i + 1]
        assert d_prev < d_bar <= d_next and d_bar >= t0, "pencere sırası bozuk"
        assert (_gun(d_next) - _gun(t0)).days <= T0_MAKS_BOSLUK_GUN + 5, \
            "tepki penceresi t0'dan koptu"
        r_evt = float(gecmis[-1] / gecmis[-3] - 1.0)

        gp, gn = gidx[d_prev], gidx[d_next]
        w = C[gn] / C[gp] - 1.0
        m = np.isfinite(w)
        n_univ = int(m.sum())
        if n_univ < MIN_PAYDA:
            dus(s, t0, f"evren_paydasi<{MIN_PAYDA}")
            continue
        r_univ = float(w[m].mean())

        rec = {"symbol": s, "t0": t0, "t0_bar": d_bar, "t0_kaydi": int(d_bar != t0),
               "i": i, "tepki": O._r6(r_evt - r_univ), "tepki_ham": O._r6(r_evt),
               "pencere": [d_prev, d_next], "evren_payda": n_univ, "neden": None}

        # -------- sürüklenme (SONUÇ tarafı; t0-kararına girmez)
        n = len(dates)
        for H in UFUKLAR:
            if i + H >= n:
                rec[f"fazla{H}"] = None
                rec[f"fazla{H}_neden"] = "ufuk_penceresi_seri_disi"
                continue
            r_sym = float(v["close"][i + H] / v["close"][i + 1] - 1.0)
            g_son = [gidx[d] for d in dates[i + 2:i + H + 1]]
            if np.min(rc[g_son]) < MIN_PAYDA:
                rec[f"fazla{H}"] = None
                rec[f"fazla{H}_neden"] = f"gunluk_evren_paydasi<{MIN_PAYDA}"
                continue
            r_u = float(np.prod(1.0 + runiv[g_son]) - 1.0)
            rec[f"fazla{H}"] = O._r6(r_sym - r_u)
            rec[f"fazla{H}_neden"] = None
            rec[f"payda{H}_min"] = int(np.min(rc[g_son]))
        kayit.append(rec)
    return kayit, neden_say


# ------------------------------------------------------------------ İSTATİSTİK (şablon cebiri, SEED 20260812)
def mean_block_boot_050(y, dates, n_boot=O.BOOT, blok=O.BLOCK):
    """ortak.mean_block_boot ile AYNI cebir; tek fark RNG050 (seed 20260812, görev talimatı)."""
    y = np.asarray(y, float)
    dates = np.asarray(dates)
    uniq, inv = np.unique(dates, return_inverse=True)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3}"}
    sums = np.bincount(inv, weights=y, minlength=nd)
    cnts = np.bincount(inv, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG050.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnts[gun].sum()
        if c <= 0:
            atlanan += 1
            continue
        vals.append(sums[gun].sum() / c)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": O._r6(np.percentile(a, 2.5)), "hi": O._r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "seed": SEED, "neden": None}


def hucre(y, dates):
    n = int(len(y))
    if n < O.MIN_SLICE:
        return {"n": n, "ort": None, "ci": None, "neden": f"n<{O.MIN_SLICE}"}
    y = np.asarray(y, float)
    ci = mean_block_boot_050(y, dates)
    ort = float(np.mean(y))
    out = {"n": n, "ort": O._r6(ort), "medyan": O._r6(np.median(y)),
           "std": O._r6(np.std(y, ddof=1)), "pozitif_oran": O._r6(float((y > 0).mean())),
           "ci": None if ci["lo"] is None else {"lo": ci["lo"], "hi": ci["hi"], "seviye": 0.95},
           "ci_meta": ci,
           "anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0 or ci["hi"] < 0),
           "pozitif_anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0),
           "negatif_anlamli": None if ci["lo"] is None else bool(ci["hi"] < 0),
           "neden": None}
    for b in MALIYET_BPS:
        out[f"net_{int(b)}bps_tek_yon"] = O._r6(ort - b / 10000.0)
        out[f"net_{int(b)}bps_gidis_donus_TANI"] = O._r6(ort - 2 * b / 10000.0)
    return out


# ------------------------------------------------------------------ ANA AKIŞ
def main():
    print("== EDG-2026-050 PEAD-8K ölçümü ==")
    out = {"kart": "EDG-2026-050", "tarih": dt.date.today().isoformat(),
           "seed_ci": SEED, "kod": {
               "olcum_py_sha256": _sha(BURASI / "olcum.py"),
               "ortak_py_sha256": _sha(BURASI / "ortak.py"),
               "ortak_kaynak": "research/olcumler/wp2_olcum/ortak.py (BİREBİR kopya)",
               "pk_py_sha256": _sha(BURASI / "pk.py"),
               "pk_kaynak": "research/olcumler/wp2_olcum/pk.py (BİREBİR kopya)"}}

    print("== barlar (şablon yolu: takvim kapısı + integrity defteri) ==")
    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol yüklendi")
    out["bar_muhasebesi"] = {k: v for k, v in bar_acc.items()
                            if k not in ("kisa_semboller", "takvim_reddedilen")}
    out["bar_muhasebesi"]["kisa_semboller"] = bar_acc["kisa_semboller"]
    out["bar_muhasebesi"]["takvim_reddedilen_n"] = len(bar_acc["takvim_reddedilen"])

    print("== [1] olay inşası ==")
    olaylar, kap = olaylar_kur()
    print(f"   tam CSV kümeleme: {kap['kumeleme_tam_csv_olay']} olay "
          f"(ref {REF_W14_OLAY}, uyum={kap['kumeleme_ref_uyum']})")
    print(f"   CIK-kesiği: {kap['cik_kesigi_sembol_n_tam_csv']} sembol "
          f"(ref 41, uyum={kap['cik_kesigi_ref_uyum_41']})")
    print(f"   evren-içi olay (kümeleme sonrası): {kap['evren_ici_olay_kumeleme_sonrasi']}")

    tum_gun, gidx, C, runiv, rc = panel_matris(pan)
    kayit, neden_say = olay_olc(olaylar, pan, gidx, C, runiv, rc)
    gecerli = [r for r in kayit if r["tepki"] is not None]
    kap["olay_neden_histogram"] = neden_say
    kap["gecerli_olay_tepki"] = len(gecerli)
    kap["t0_kaydirilan_olay"] = int(sum(r.get("t0_kaydi", 0) for r in gecerli))
    pv = np.array([r["evren_payda"] for r in gecerli])
    kap["tepki_evren_payda"] = {"min": int(pv.min()), "medyan": int(np.median(pv)),
                                "maks": int(pv.max())}
    kap["olay_takvim_araligi"] = [min(r["t0"] for r in gecerli),
                                  max(r["t0"] for r in gecerli)]
    out["kapsam"] = kap
    print(f"   geçerli olay (tepki ölçülebilir): {len(gecerli)}  nedenler: {neden_say}")

    # -------------------------------------------------- kill#3 kapısı
    if len(gecerli) < KILL3_ESIK:
        out["ASKI"] = {"kill": 3, "esik": KILL3_ESIK, "gecerli_olay": len(gecerli),
                       "damga": "ASKI — kapsam yetersiz, K harcanmaz; dilim/sürüklenme "
                                "ÖLÇÜLMEDİ (kart kill#3)"}
        O.json_yaz(BURASI / "sonuc.json", out)
        print("!! kill#3 → ASKI damgası, ölçüm durdu")
        return
    out["kill3"] = {"esik": KILL3_ESIK, "gecerli_olay": len(gecerli), "gecti": True}

    # -------------------------------------------------- [3] dilim eşikleri (ölçüm-önce döküm)
    tepki = np.array([r["tepki"] for r in gecerli], float)
    p20, p80 = float(np.percentile(tepki, 20)), float(np.percentile(tepki, 80))
    dokum = {"n": len(tepki), "p20": O._r6(p20), "p80": O._r6(p80),
             "ort": O._r6(float(tepki.mean())), "medyan": O._r6(float(np.median(tepki))),
             "std": O._r6(float(tepki.std(ddof=1))),
             "q": {q: O._r6(float(np.percentile(tepki, q)))
                   for q in (1, 5, 25, 50, 75, 95, 99)},
             "beyan": "yüzdelikler TÜM geçerli olay dağılımından; bu döküm sürüklenme "
                      "istatistikleri okunmadan ÖNCE yazıldı (kart [3])"}
    out["dilim_esik_dokumu"] = dokum
    print(f"== [3] eşik dökümü: n={dokum['n']} p20={dokum['p20']} p80={dokum['p80']} ==")

    m_ust = tepki >= p80
    m_alt = tepki <= p20
    # PIT öz-sınaması: dilim kararı yalnız tepki'den (t0+1 kapanışına kadarki bilgi)
    assert len(tepki) == len(gecerli) and not np.isnan(tepki).any()

    # -------------------------------------------------- [4]+[5] dilim × ufuk
    print("== [4] sürüklenme + CI (seed 20260812) ==")
    out["sonuc"] = {}
    for ad, mask in (("tepki_ust_20pct", m_ust), ("tepki_alt_20pct", m_alt),
                     ("tum_olaylar_TANI", np.ones(len(tepki), bool))):
        blok = {"olay_n": int(mask.sum())}
        for H in UFUKLAR:
            rows = [(r[f"fazla{H}"], r["t0"]) for r, mm in zip(gecerli, mask)
                    if mm and r[f"fazla{H}"] is not None]
            dusen = int(mask.sum()) - len(rows)
            h = hucre(np.array([a for a, _ in rows], float),
                      np.array([b for _, b in rows]))
            h["ufuk_none_olay"] = dusen
            blok[f"@{H}g"] = h
            if ad != "tum_olaylar_TANI":
                print(f"   {ad} @{H}g: n={h['n']} ort={h['ort']} ci={h.get('ci')}")
        if ad == "tum_olaylar_TANI":
            blok["not"] = "hüküm-dışı bağlam; karar kuralı yalnız iki ucu okur"
        out["sonuc"][ad] = blok

    # -------------------------------------------------- [7] PIT öz-sınaması (beyan + sayım)
    out["pit_oz_sinamasi"] = {
        "tanim": "tepki = close[:i+2] dilimi üzerinden (yapısal geriye-bakışsızlık); pencere "
                 "assert'leri her olayda koştu; dilim eşikleri yalnız tepki dizisinden; "
                 "sürüklenme yalnız SONUÇ tarafında okunur, t0-kararına girmez. NOT: yüzdelik "
                 "eşikler TÜM dönem dağılımından (kartın [3] tasarımı) — kesitsel araştırma "
                 "ölçüsüdür, işlem-kuralı değildir; bu beyanla taşınır.",
        "sinanan_olay": len(gecerli), "assert_ihlali": 0, "gecti": True}

    # -------------------------------------------------- pozitif kontrol özeti (pk.json'dan)
    try:
        pk = json.load(open(BURASI / "pk.json"))
        out["pozitif_kontrol_ozet"] = {
            "civi_hedef": pk["pozitif_kontrol"]["civi_hedef"],
            "civi_olculen": pk["pozitif_kontrol"]["civi_olculen"],
            "GECTI": pk["pozitif_kontrol"]["GECTI"],
            "pk4_gecti": pk["pk4_yol_tutarliligi"]["gecti"],
            "pk5_gecti": pk["pk5_ozdeslikler"]["gecti"]}
    except Exception as e:
        out["pozitif_kontrol_ozet"] = {"None": True,
                                       "neden": f"pk.json okunamadı: {type(e).__name__}: {e}"}

    O.json_yaz(BURASI / "sonuc.json", out)
    olay_df = pd.DataFrame(kayit)
    olay_df.to_csv(BURASI / "olaylar.csv", index=False)
    print(f"== yazıldı: sonuc.json + olaylar.csv ({len(kayit)} satır) ==")


if __name__ == "__main__":
    main()
