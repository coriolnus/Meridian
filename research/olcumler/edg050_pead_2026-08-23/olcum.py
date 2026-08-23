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
        # pencere t0'dan koparsa ÖLÇÜLEMEZ (assert değil, None+neden — UYDURMA YASAĞI/YASA 4)
        if (_gun(d_next) - _gun(t0)).days > T0_MAKS_BOSLUK_GUN + 5:
            dus(s, t0, f"tepki_penceresi_t0dan_kopuk>{T0_MAKS_BOSLUK_GUN + 5}g "
                       "(bar boşluğu; ±1g penceresi daraltılmadı, olay düştü)")
            continue
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
               "tepki_evren": O._r6(r_univ), "d_prev": d_prev, "d_next": d_next,
               "evren_payda": n_univ, "neden": None}

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


# ------------------------------------------------------------------ [6] PIT ÖZ-SINAMASI (yıkıcı)
def pit_yikici_sinama(gecerli, pan, gidx, C):
    """YIKICI sınama: t0+1'DEN SONRAKİ HİÇBİR SATIR GÖRÜLMEDEN tepki yeniden hesaplanır.

    Sembol serisi close[:i+2]'ye, evren matrisi C[:gn+1]'e KESİLİR. Kesik girdiyle üretilen
    değer kayıtlı tepkiden farklıysa boru hattı geleceği okuyor demektir (ihlal sayılır).
    TÜM geçerli olaylarda koşar — örneklem değil."""
    ihlal, ayrisan_ornek, n = 0, [], 0
    gelecek_indeks_ihlali = 0
    for r in gecerli:
        v = pan[r["symbol"]]
        i = int(r["i"])
        gp, gn = gidx[r["d_prev"]], gidx[r["d_next"]]
        cl_kesik = v["close"][:i + 2]                    # t0+1 sonrası YOK
        C_kesik = C[:gn + 1]                             # t0+1 sonrası satırlar YOK
        if gp > gn or gn >= len(C):
            gelecek_indeks_ihlali += 1
        r_evt = float(cl_kesik[-1] / cl_kesik[-3] - 1.0)
        w = C_kesik[gn] / C_kesik[gp] - 1.0
        m = np.isfinite(w)
        yeniden = O._r6(r_evt - float(w[m].mean()))
        n += 1
        if yeniden != r["tepki"]:
            ihlal += 1
            if len(ayrisan_ornek) < 5:
                ayrisan_ornek.append({"symbol": r["symbol"], "t0": r["t0"],
                                      "kayitli": r["tepki"], "kesik_girdiyle": yeniden})
    return {"tanim": "tepki, sembol serisi close[:t0+1] ve evren matrisi C[:t0+1] KESİLEREK "
                     "yeniden hesaplandı; t0+1 kapanışından sonraki hiçbir satır girdi değil.",
            "kapsam": "TÜM geçerli olaylar (örneklem değil)",
            "sinanan_olay": n, "ihlal": ihlal, "gelecek_indeks_ihlali": gelecek_indeks_ihlali,
            "ayrisan_ornek": ayrisan_ornek,
            "gecti": bool(n > 0 and ihlal == 0 and gelecek_indeks_ihlali == 0)}


# ------------------------------------------------------------------ İSTATİSTİK (şablon cebiri, SEED 20260812)
def mean_block_boot_050(y, dates, rng, n_boot=O.BOOT, blok=O.BLOCK):
    """ortak.mean_block_boot ile AYNI cebir; tek fark RNG (seed 20260812, görev talimatı)."""
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
        bas = rng.integers(0, son_bas + 1, n_blok)
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


def hucre(y, dates, rng):
    n = int(len(y))
    if n < O.MIN_SLICE:
        return {"n": n, "ort": None, "ci": None, "neden": f"n<{O.MIN_SLICE}"}
    y = np.asarray(y, float)
    ci = mean_block_boot_050(y, dates, rng)
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
        if out["ci"] is not None:
            out[f"net_{int(b)}bps_ci_TANI"] = {"lo": O._r6(ci["lo"] - b / 10000.0),
                                               "hi": O._r6(ci["hi"] - b / 10000.0)}
    return out


# ================================================================== FAZ 1 — OLAY İNŞASI
def faz1():
    print("== FAZ1: [1] olay inşası + 14g kümeleme + kapsam ==")
    olaylar, kap = olaylar_kur()
    print(f"   tam CSV kümeleme: {kap['kumeleme_tam_csv_olay']} olay "
          f"(ref {REF_W14_OLAY}, uyum={kap['kumeleme_ref_uyum']})")
    print(f"   CIK-kesiği: {kap['cik_kesigi_sembol_n_tam_csv']} sembol "
          f"(ref 41, uyum={kap['cik_kesigi_ref_uyum_41']})")
    print(f"   evren-içi olay (kümeleme sonrası): {kap['evren_ici_olay_kumeleme_sonrasi']}")
    O.json_yaz(BURASI / "faz1_olay.json",
               {"kart": "EDG-2026-050", "faz": 1, "kapsam": kap,
                "kod_sha256": {"olcum": _sha(BURASI / "olcum.py")},
                "olaylar": [[s, t] for s, t in olaylar]})
    print("== yazıldı: faz1_olay.json ==")


# ================================================================== FAZ 2 — TEPKİ + SÜRÜKLENME HAM
def faz2():
    print("== FAZ2: [2] tepki + ham sürüklenme + kill#3 kapısı + [6] PIT yıkıcı sınama ==")
    f1 = json.load(open(BURASI / "faz1_olay.json"))
    olaylar = [(s, t) for s, t in f1["olaylar"]]
    kap = f1["kapsam"]

    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol yüklendi")
    bm = {k: v for k, v in bar_acc.items() if k not in ("kisa_semboller", "takvim_reddedilen")}
    bm["kisa_semboller"] = bar_acc["kisa_semboller"]
    bm["takvim_reddedilen_n"] = len(bar_acc["takvim_reddedilen"])

    tum_gun, gidx, C, runiv, rc = panel_matris(pan)
    kayit, neden_say = olay_olc(olaylar, pan, gidx, C, runiv, rc)
    gecerli = [r for r in kayit if r["tepki"] is not None]

    # olay tablosu HEMEN diske (kesinti dayanıklılığı — 049 dersi)
    pd.DataFrame(kayit).to_csv(BURASI / "olaylar.csv", index=False)
    print(f"   yazıldı: olaylar.csv ({len(kayit)} satır)")

    kap["olay_neden_histogram"] = neden_say
    kap["gecerli_olay_tepki"] = len(gecerli)
    kap["t0_kaydirilan_olay"] = int(sum(r.get("t0_kaydi", 0) for r in gecerli))
    pv = np.array([r["evren_payda"] for r in gecerli]) if gecerli else np.array([0])
    kap["tepki_evren_payda"] = {"min": int(pv.min()), "medyan": int(np.median(pv)),
                                "maks": int(pv.max())}
    if gecerli:
        kap["olay_takvim_araligi"] = [min(r["t0"] for r in gecerli),
                                      max(r["t0"] for r in gecerli)]
        kap["olay_sembol_n"] = len({r["symbol"] for r in gecerli})
    for H in UFUKLAR:
        kap[f"ufuk{H}_olculebilen"] = int(sum(1 for r in gecerli if r.get(f"fazla{H}") is not None))
        nd = {}
        for r in gecerli:
            if r.get(f"fazla{H}") is None:
                nd[r.get(f"fazla{H}_neden")] = nd.get(r.get(f"fazla{H}_neden"), 0) + 1
        kap[f"ufuk{H}_none_neden"] = nd
    print(f"   geçerli olay (tepki ölçülebilir): {len(gecerli)}  nedenler: {neden_say}")

    pit = pit_yikici_sinama(gecerli, pan, gidx, C)
    print(f"   PIT yıkıcı sınama: n={pit['sinanan_olay']} ihlal={pit['ihlal']} "
          f"geçti={pit['gecti']}")

    out = {"kart": "EDG-2026-050", "faz": 2, "bar_muhasebesi": bm, "kapsam": kap,
           "pit_yikici_sinama": pit,
           "kill3": {"esik": KILL3_ESIK, "gecerli_olay": len(gecerli),
                     "gecti": bool(len(gecerli) >= KILL3_ESIK)}}
    if len(gecerli) < KILL3_ESIK:
        out["ASKI"] = {"kill": 3, "esik": KILL3_ESIK, "gecerli_olay": len(gecerli),
                       "damga": "ASKI — kapsam yetersiz, K harcanmaz; dilim/sürüklenme "
                                "ÖLÇÜLMEDİ (kart kill#3)"}
    O.json_yaz(BURASI / "faz2_tepki.json", out)
    print("== yazıldı: faz2_tepki.json ==")
    if len(gecerli) < KILL3_ESIK:
        print("!! kill#3 → ASKI damgası, ölçüm DURDU (faz3/faz4 koşmaz)")


def _gecerli_oku():
    df = pd.read_csv(BURASI / "olaylar.csv", dtype={"t0": str, "symbol": str})
    df = df[df["tepki"].notna()].reset_index(drop=True)
    return df


# ================================================================== FAZ 3 — DİLİM EŞİKLERİ (ÖLÇÜM ÖNCESİ)
def faz3():
    print("== FAZ3: [3] dilim eşikleri — SÜRÜKLENME OKUNMADAN ÖNCE diske yazılır ==")
    f2 = json.load(open(BURASI / "faz2_tepki.json"))
    if not f2["kill3"]["gecti"]:
        print("!! kill#3 ASKI — faz3 koşmaz")
        return
    df = _gecerli_oku()
    tepki = df["tepki"].to_numpy(float)
    p20, p80 = float(np.percentile(tepki, 20)), float(np.percentile(tepki, 80))
    dokum = {"kart": "EDG-2026-050", "faz": 3,
             "yazim_zamani_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "n": int(len(tepki)), "p20": O._r6(p20), "p80": O._r6(p80),
             "ort": O._r6(float(tepki.mean())), "medyan": O._r6(float(np.median(tepki))),
             "std": O._r6(float(tepki.std(ddof=1))),
             "q": {str(q): O._r6(float(np.percentile(tepki, q)))
                   for q in (1, 5, 10, 25, 50, 75, 90, 95, 99)},
             "ust_dilim_olay_n": int((tepki >= p80).sum()),
             "alt_dilim_olay_n": int((tepki <= p20).sum()),
             "beyan": "yüzdelikler TÜM geçerli olay dağılımından (kart [3] donuk tasarımı); bu "
                      "döküm sürüklenme istatistikleri HESAPLANMADAN ÖNCE ayrı dosyaya yazıldı "
                      "(ölçüm-öncesi döküm beyanı; mtime sırası kanıt)."}
    O.json_yaz(BURASI / "faz3_esik_dokumu.json", dokum)
    print(f"   n={dokum['n']} p20={dokum['p20']} p80={dokum['p80']} "
          f"(üst n={dokum['ust_dilim_olay_n']}, alt n={dokum['alt_dilim_olay_n']})")
    print("== yazıldı: faz3_esik_dokumu.json ==")


# ================================================================== FAZ 4 — SÜRÜKLENME + CI + MALİYET
def _genisleyen_esik_tani(df):
    """TANI (hüküm-dışı, K harcamaz): eşikler AYLIK yenilenir ve YALNIZ o ayın ilk olayından
    ÖNCEKİ olaylardan türetilir — kart eşiğinin kesitsel tam-örneklem doğasını nicelemek için."""
    o = df.sort_values("t0").reset_index(drop=True)
    tep = o["tepki"].to_numpy(float)
    aylar = o["t0"].str.slice(0, 7).to_numpy()
    MIN_GECMIS = 500
    ust = np.zeros(len(o), bool)
    alt = np.zeros(len(o), bool)
    esik, olculemeyen = {}, 0
    for k in range(len(o)):
        ay = aylar[k]
        if ay not in esik:
            esik[ay] = None if k < MIN_GECMIS else (
                float(np.percentile(tep[:k], 20)), float(np.percentile(tep[:k], 80)), k)
        e = esik[ay]
        if e is None:
            olculemeyen += 1
            continue
        if tep[k] >= e[1]:
            ust[k] = True
        if tep[k] <= e[0]:
            alt[k] = True
    meta = {"tanim": "aylık yenilenen GENİŞLEYEN pencere eşiği; ay içindeki her olay, o ayın ilk "
                     "olayından ÖNCEKİ tüm olayların p20/p80'ini kullanır (ileriye bakış yok)",
            "min_gecmis_olay": MIN_GECMIS, "esiksiz_olay": olculemeyen,
            "ay_n": int(len(esik)), "not": "TANI — kart karar kuralı bunu OKUMAZ, K harcamaz"}
    return o, ust, alt, meta


def faz4():
    print("== FAZ4: [4] sürüklenme + 21g blok-bootstrap CI + [5] maliyet ==")
    f2 = json.load(open(BURASI / "faz2_tepki.json"))
    if not f2["kill3"]["gecti"]:
        print("!! kill#3 ASKI — faz4 koşmaz")
        return
    dok = json.load(open(BURASI / "faz3_esik_dokumu.json"))
    df = _gecerli_oku()
    tepki = df["tepki"].to_numpy(float)
    p20, p80 = dok["p20"], dok["p80"]          # FAZ3'te DONDURULMUŞ eşikler (yeniden hesaplanmaz)
    rng = np.random.default_rng(SEED)

    sonuc = {}
    for ad, mask, kaynak in (("tepki_ust_20pct", tepki >= p80, df),
                             ("tepki_alt_20pct", tepki <= p20, df),
                             ("tum_olaylar_TANI", np.ones(len(tepki), bool), df)):
        blok = {"olay_n": int(mask.sum())}
        for H in UFUKLAR:
            sub = kaynak[mask]
            sub = sub[sub[f"fazla{H}"].notna()]
            h = hucre(sub[f"fazla{H}"].to_numpy(float), sub["t0"].to_numpy(), rng)
            h["ufuk_none_olay"] = int(mask.sum()) - int(len(sub))
            blok[f"@{H}g"] = h
            print(f"   {ad} @{H}g: n={h['n']} ort={h['ort']} ci={h.get('ci')} "
                  f"net10={h.get('net_10bps_tek_yon')}")
        if ad == "tum_olaylar_TANI":
            blok["not"] = "hüküm-dışı bağlam; kart karar kuralı yalnız iki ucu okur"
        sonuc[ad] = blok

    # ---- TANI: genişleyen (PIT) eşikle aynı iki dilim
    o, gust, galt, gmeta = _genisleyen_esik_tani(df)
    gtani = {"meta": gmeta}
    for ad, mask in (("tepki_ust_20pct_GENISLEYEN_ESIK_TANI", gust),
                     ("tepki_alt_20pct_GENISLEYEN_ESIK_TANI", galt)):
        blok = {"olay_n": int(mask.sum())}
        for H in UFUKLAR:
            sub = o[mask]
            sub = sub[sub[f"fazla{H}"].notna()]
            h = hucre(sub[f"fazla{H}"].to_numpy(float), sub["t0"].to_numpy(), rng)
            h["ufuk_none_olay"] = int(mask.sum()) - int(len(sub))
            blok[f"@{H}g"] = h
            print(f"   [TANI] {ad} @{H}g: n={h['n']} ort={h['ort']} ci={h.get('ci')}")
        gtani[ad] = blok

    O.json_yaz(BURASI / "faz4_sonuc.json",
               {"kart": "EDG-2026-050", "faz": 4, "seed_ci": SEED,
                "esik_kaynagi": {"dosya": "faz3_esik_dokumu.json", "p20": p20, "p80": p80,
                                 "not": "eşikler FAZ3'te dondu; faz4 yeniden hesaplamaz"},
                "sonuc": sonuc, "genisleyen_esik_TANI": gtani})
    print("== yazıldı: faz4_sonuc.json ==")


# ================================================================== FAZ 6 — TANI: CI KARARLILIĞI
def faz6():
    """TANI (hüküm-dışı): kart tohumu (20260812) DONUK karardır. Bu faz onu DEĞİŞTİRMEZ; yalnız
    blok-bootstrap alt sınırının tohum/blok seçimine ne kadar duyarlı olduğunu ölçer — sınırda
    çıkan bir hücrenin ne kadar sağlam olduğunu Rol-1 görebilsin diye."""
    print("== FAZ6 (TANI): CI kararlılığı — kart tohumu DEĞİŞMEZ, yalnız duyarlılık ölçülür ==")
    dok = json.load(open(BURASI / "faz3_esik_dokumu.json"))
    df = _gecerli_oku()
    tepki = df["tepki"].to_numpy(float)
    dilimler = {"tepki_ust_20pct": tepki >= dok["p80"], "tepki_alt_20pct": tepki <= dok["p20"]}
    out = {"kart": "EDG-2026-050", "faz": 6, "kart_tohumu": SEED,
           "not": "TANI — kart karar kuralı YALNIZ faz4_sonuc.json'daki (seed 20260812) hücreleri "
                  "okur; buradaki alternatif tohum/blok değerleri hüküm girdisi DEĞİLDİR."}
    for ad, mask in dilimler.items():
        blok = {}
        for H in UFUKLAR:
            sub = df[mask]
            sub = sub[sub[f"fazla{H}"].notna()]
            y = sub[f"fazla{H}"].to_numpy(float)
            d = sub["t0"].to_numpy()
            lo_list, hi_list = [], []
            for sd in (20260812, 1, 7, 20260801, 424242, 999983):
                r = mean_block_boot_050(y, d, np.random.default_rng(sd))
                lo_list.append(r["lo"]); hi_list.append(r["hi"])
            # tohumdan BAĞIMSIZ ölçü: bootstrap dağılımının sıfırın altında kalan oranı
            r0 = np.random.default_rng(SEED)
            uniq, inv = np.unique(d, return_inverse=True)
            nd = len(uniq)
            sums = np.bincount(inv, weights=y, minlength=nd)
            cnts = np.bincount(inv, minlength=nd).astype(float)
            n_blok = int(np.ceil(nd / O.BLOCK)); ofs = np.arange(O.BLOCK)
            vals = []
            for _ in range(20000):
                bas = r0.integers(0, nd - O.BLOCK + 1, n_blok)
                g = (bas[:, None] + ofs[None, :]).ravel()[:nd]
                vals.append(sums[g].sum() / cnts[g].sum())
            v = np.asarray(vals)
            blok[f"@{H}g"] = {
                "n": int(len(y)), "ort": O._r6(float(y.mean())),
                "alt_sinir_6_tohum": lo_list, "ust_sinir_6_tohum": hi_list,
                "alt_sinir_min": O._r6(min(lo_list)), "alt_sinir_maks": O._r6(max(lo_list)),
                "alt_sinir_isaret_tutarli": bool(all(x > 0 for x in lo_list)
                                                 or all(x <= 0 for x in lo_list)),
                "boot20k_sifirin_altinda_oran": O._r6(float((v <= 0).mean())),
                "boot20k_p2_5": O._r6(float(np.percentile(v, 2.5))),
                "boot20k_p97_5": O._r6(float(np.percentile(v, 97.5)))}
            print(f"   {ad} @{H}g: lo(6 tohum)={lo_list} işaret_tutarli="
                  f"{blok[f'@{H}g']['alt_sinir_isaret_tutarli']} "
                  f"P(boot<=0)={blok[f'@{H}g']['boot20k_sifirin_altinda_oran']}")
        out[ad] = blok
    O.json_yaz(BURASI / "faz6_ci_kararlilik.json", out)
    print("== yazıldı: faz6_ci_kararlilik.json ==")


# ================================================================== FAZ 5 — BİRLEŞTİRME
def faz5():
    print("== FAZ5: birleştirme → sonuc.json ==")
    out = {"kart": "EDG-2026-050", "tarih": dt.date.today().isoformat(), "seed_ci": SEED,
           "HUKUM": "YOK — hüküm Rol-1'indir; bu dosya yalnız ÖLÇÜMDÜR",
           "kod": {"olcum_py_sha256": _sha(BURASI / "olcum.py"),
                   "ortak_py_sha256": _sha(BURASI / "ortak.py"),
                   "ortak_kaynak": "research/olcumler/wp2_olcum/ortak.py (BİREBİR kopya)",
                   "pk_py_sha256": _sha(BURASI / "pk.py"),
                   "pk_kaynak": "research/olcumler/wp2_olcum/pk.py (BİREBİR kopya)"}}
    f1 = json.load(open(BURASI / "faz1_olay.json"))
    f2 = json.load(open(BURASI / "faz2_tepki.json"))
    out["bar_muhasebesi"] = f2["bar_muhasebesi"]
    out["kapsam"] = f2["kapsam"]
    out["kill3"] = f2["kill3"]
    if "ASKI" in f2:
        out["ASKI"] = f2["ASKI"]
    out["pit_oz_sinamasi"] = {
        "yikici_sinama": f2["pit_yikici_sinama"],
        "yapisal_beyan": "tepki close[:i+2] dilimi üzerinden kurulur; pencere sıra assert'i her "
                         "olayda koştu; dilim eşikleri YALNIZ tepki dizisinden türetildi ve "
                         "sürüklenme okunmadan ÖNCE ayrı dosyaya donduruldu (faz3_esik_dokumu."
                         "json mtime < faz4_sonuc.json mtime); sürüklenme yalnız SONUÇ tarafıdır.",
        "esik_kesitsel_serhi": "kart [3] eşikleri TÜM dönem dağılımından okur — kesitsel ARAŞTIRMA "
                               "ölçüsüdür, uygulanabilir işlem kuralı DEĞİLDİR; genişleyen-pencere "
                               "eşik TANIsı faz4_sonuc.json'da ayrıca verilmiştir."}
    try:
        out["dilim_esik_dokumu"] = json.load(open(BURASI / "faz3_esik_dokumu.json"))
        f4 = json.load(open(BURASI / "faz4_sonuc.json"))
        out["sonuc"] = f4["sonuc"]
        out["genisleyen_esik_TANI"] = f4["genisleyen_esik_TANI"]
    except FileNotFoundError as e:
        out["sonuc"] = {"None": True, "neden": f"faz3/faz4 çıktısı yok: {e}"}
    try:
        out["ci_kararlilik_TANI"] = {
            "okuma_serhi": "faz4 hücreleri TEK bir RNG akışını sırayla tüketir (kart tohumu "
                           "20260812); faz6 her hücreye TAZE default_rng(tohum) verir. Aynı "
                           "tohumun iki farklı akış konumu aynı sayıyı VERMEZ — kart hükmüne "
                           "giren değer faz4_sonuc.json'dakidir, faz6 yalnız duyarlılık ölçer.",
            "olcum": json.load(open(BURASI / "faz6_ci_kararlilik.json"))}
    except FileNotFoundError as e:
        out["ci_kararlilik_TANI"] = {"None": True, "neden": f"faz6 çıktısı yok: {e}"}
    try:
        pk = json.load(open(BURASI / "pk.json"))
        out["pozitif_kontrol_ozet"] = {
            "civi_hedef": pk["pozitif_kontrol"]["civi_hedef"],
            "civi_olculen": pk["pozitif_kontrol"]["civi_olculen"],
            "civi_sapma": pk["pozitif_kontrol"]["civi_sapma"],
            "tolerans": pk["pozitif_kontrol"]["tolerans"],
            "GECTI": pk["pozitif_kontrol"]["GECTI"],
            "ic_5_10_20": {h: pk["pozitif_kontrol"][h]["ic"] for h in ("5", "10", "20")},
            "pk4_gecti": pk["pk4_yol_tutarliligi"]["gecti"],
            "pk5_gecti": pk["pk5_ozdeslikler"]["gecti"],
            "kill6": "pozitif kontrol yeniden üretildi → ölçüm düzeneği GEÇERLİ"}
    except Exception as e:
        out["pozitif_kontrol_ozet"] = {"None": True,
                                       "neden": f"pk.json okunamadı: {type(e).__name__}: {e}"}
    out["beyanli_sinirlar"] = {
        "survivorship": "evren bugünün 251'i — her pozitif okuma ÜST-SINIR'dır (kart zorunlu "
                        "kelimesi); delist olmuş isimler evrende yok, PEAD sürüklenmesi bu "
                        "yüzden iyimser tarafa saplıdır.",
        "item202_isaretsiz": "2.02 işareti taşımayan kazanç duyuruları kapsam dışıdır (CSV "
                             "items alanına dayanır).",
        "cik_kesigi": "CIK-halefiyet kesikli semboller erken dönemlerinde VERİ YOK (duyuru yok "
                      "değil) — faz1_olay.json/kapsam.cik_kesigi listesinde None+neden.",
        "pencere_bulaniklıgı": "BMO/AMC bilinmediği için ±1g pencere ZORUNLU tutuldu (kart "
                               "kill#4); daraltma yapılmadı.",
        "portfoy_baglamsizligi": "fazla-getiri portföy-bağlamsızdır; paket-içi etki ayrı kartın "
                                 "işidir."}
    O.json_yaz(BURASI / "sonuc.json", out)
    print("== yazıldı: sonuc.json ==")


FAZLAR = {"faz1": faz1, "faz2": faz2, "faz3": faz3, "faz4": faz4, "faz6": faz6,
          "faz5": faz5}

if __name__ == "__main__":
    import sys
    ad = sys.argv[1] if len(sys.argv) > 1 else ""
    if ad not in FAZLAR:
        raise SystemExit(f"kullanım: python olcum.py {{{'|'.join(FAZLAR)}}}")
    FAZLAR[ad]()
