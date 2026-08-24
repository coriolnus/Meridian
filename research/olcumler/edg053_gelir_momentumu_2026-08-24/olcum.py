"""EDG-2026-053 — GELİR MOMENTUMU (YoY büyüme + İVME) ÖLÇÜMÜ.

Kart: research/cards/EDG-2026-053-gelir-momentumu.yaml (DONUK, status: registered).
Düzenek: research/olcumler/edg050_pead_2026-08-23/ (ortak.py + pk.py BİREBİR kopya; sha256
sonuc.json'da). BU DOSYA HÜKÜM VERMEZ — hüküm ve kart status geçişi Rol-1'indir.

BEYANLAR (kartın features_asof/guards maddeleri AYNEN):
  · Gözlem: AYLIK sembol-ay paneli. Gözlem günü = ORTAK TAKVİMİN ay-sonu işlem günü.
    Sembolün o gün kendi barı YOKSA gözlem ölçülemez (None + neden) — uydurma yok.
  · İLK-İFŞA FİLTRESİ (ZORUNLU, kill#2): her (symbol, tag, start, end) dörtlüsünün YALNIZ
    en küçük `filed`li satırı alınır. Sonraki satırlar yeniden-beyan/düzeltmedir; silinmez,
    ölçüme girmez (restatement panzehiri). Muhasebesi faz1'de.
  · ETİKET ÖNCELİĞİ TEK YERDE (kill#3): sıra `ortak.GELIR_ONCELIK` — Revenues →
    RevenueFromContractWithCustomerExcludingAssessedTax → ...IncludingAssessedTax.
    Bu dosya kendi listesini TANIMLAMAZ; ortak.py'dekini okur ve sırasını assert eder.
  · MALİ-YIL HİZASI `frame` İLE: her dönemin takvim-çeyreği anahtarı (cq), SEC'in `frame`
    alanından alınır (aynı (symbol,start,end) döneminin HERHANGİ bir satırındaki frame —
    frame DÖNEMİN özelliğidir, dosyalamanın değil; start/end ilk ifşada zaten bilinir, bu
    yüzden PIT sızıntısı DEĞİLDİR). frame yoksa dönem ortasının takvim çeyreği türetilir;
    iki yolun uyum oranı faz1'de TANI olarak yazılır.
  · YoY büyüme: rev(q)/rev(q−4Ç) − 1. İVME: yoy(q) − yoy(q−1Ç). Dört çeyreğin de (q, q−1,
    q−4, q−5) `filed` günü gözlem gününden KÜÇÜK-EŞİT olmalıdır (PIT).
  · Dilimler: yoy_buyume_ust_30pct · ivme_ust_30pct — yüzdelikler AY-İÇİ KESİTTEN
    (p70; ay kesiti < MIN_AY_KESIT ise o ay dilimsiz, None + neden).
  · Ufuklar: 20g ve 60g fazla-getiri = sembolün t→t+H bileşik getirisi − AYNI GÜNLERDEKİ
    evren-ortalama günlük getirilerin bileşiği ("aynı-gün evren ortalaması tabanı",
    050 ile aynı cebir; günlük payda < MIN_PAYDA ise hücre None + neden).
  · CI: 21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap (şablon cebiri), SEED 20260812 (kart).
    Bu panelde "gözlem günü" = ay-sonu gözlem tarihi; blok = 21 ardışık gözlem tarihi
    (≈21 ay takvim karşılığı). Blok/tohum duyarlılığı faz6'da TANI olarak verilir.
  · Maliyet: 10bps ve 20bps TEK-YÖN, ortalamadan bir kez düşülür; gidiş-dönüş (×2) TANI.
  · A4 DOSYALAMA-GECİKMESİ: (filed − end) ve (gözlem günü − filed) sütunları EŞİKSİZ TANI
    olarak panelde taşınır ve rapora özetlenir; hiçbir hücre bu sütuna göre elenmez.
  · BAYAT ÇEYREK GUARD'ı (veri hijyeni, karar eşiği DEĞİL): gözlem gününde görünür en
    yeni çeyreğin `filed`i BAYAT_CEYREK_GUN'den eskiyse gözlem None + neden. Beyanlıdır ve
    kaç gözlem düştüğü rapora yazılır.
  · kill#1: sembol-ay < 3.000 → ASKI, K harcanmaz, dilim/sonuç YAZILMAZ.
  · kill#4: pozitif kontrol (rvol20 @20 cf-katman IC, 050 düzeneğiyle AYNI pk.py) yeniden
    üretilemezse düzenek geçersiz.
  · UYDURMA YASAĞI: ölçülemeyen her hücre None + neden.
  · Survivorship: evren bugünün 251'i — her pozitif okuma ÜST-SINIR şerhlidir.
  · 014-AYRIŞMASI: bu kart kârlılık SEVİYESİNİ değil gelir DEĞİŞİMİNİ ölçer.
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

SEED = 20260812                 # kart: CI tohumu
UFUKLAR = (20, 60)
MALIYET_BPS = (10.0, 20.0)      # tek-yön
UST_YUZDELIK = 70.0             # "üst %30" → ay-içi p70 ve üstü
ALT_YUZDELIK = 30.0             # YALNIZ TANI (kart karar kuralı okumaz)
KILL1_SEMBOL_AY = 3_000
BAYAT_CEYREK_GUN = 200          # beyanlı veri-hijyeni guard'ı (çeyreklik ritim ~90g)
MIN_AY_KESIT = O.MIN_SLICE      # 30 — ay-içi yüzdelik için asgari kesit
MIN_PAYDA = O.MIN_KESIT         # 50 — günlük evren paydası tabanı (şablon)

# ETİKET ÖNCELİĞİ TEK KAYNAK: ortak.GELIR_ONCELIK (kill#3). Burada YENİDEN TANIMLANMAZ.
assert O.GELIR_ONCELIK[0] == "Revenues", "etiket önceliği bozuldu (kill#3)"
assert O.GELIR_ONCELIK[1] == "RevenueFromContractWithCustomerExcludingAssessedTax"
assert O.GELIR_ONCELIK[2] == "RevenueFromContractWithCustomerIncludingAssessedTax"
assert len(O.GELIR_ONCELIK) == 3


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _qidx(cq: str) -> int:
    """'CY2018Q3' → 2018*4+2 (0-tabanlı çeyrek)."""
    return int(cq[2:6]) * 4 + int(cq[7]) - 1


# ------------------------------------------------------------------ [1] TEMEL SERİ
def temel_kur() -> tuple[pd.DataFrame, dict]:
    """Çeyreklik gelir serisi: İLK-İFŞA + etiket önceliği (tek yer) + frame hizası."""
    F = pd.read_csv(O.EDGAR / "fundamentals.csv.gz")
    acc = {"ham_satir": int(len(F)), "csv_sha256": _sha(O.EDGAR / "fundamentals.csv.gz"),
           "etiket_onceligi_kaynak": "ortak.GELIR_ONCELIK",
           "etiket_onceligi": list(O.GELIR_ONCELIK)}

    q = F[(F.unit == "USD") & (F.val > 0) & (F.donem_turu == "ceyrek")
          & (F.tag.isin(O.GELIR_ONCELIK))].copy()
    acc["ceyrek_gelir_ham_satir"] = int(len(q))
    acc["ceyrek_gelir_sembol"] = int(q.symbol.nunique())
    acc["birim_val_donem_etiket_dusen"] = int(len(F) - len(q))

    evren = sorted(dat.REPLAY_UNIVERSE)
    acc["evren_n"] = len(evren)
    q = q[q.symbol.isin(evren)].copy()
    acc["evren_ici_satir"] = int(len(q))

    # ---- İLK-İFŞA FİLTRESİ (kill#2)
    q = q.sort_values(["symbol", "tag", "start", "end", "filed", "accn"])
    grp = q.groupby(["symbol", "tag", "start", "end"], as_index=False)
    ilk = grp.first()
    acc["ilk_ifsa_satir"] = int(len(ilk))
    acc["ilk_ifsa_dusen_yeniden_beyan_satir"] = int(len(q) - len(ilk))
    coklu = q.groupby(["symbol", "tag", "start", "end", "filed"]).val.nunique()
    acc["ayni_filed_icinde_coklu_val"] = int((coklu > 1).sum())
    acc["ilk_ifsa_gecikme_gun"] = {
        "medyan": float((pd.to_datetime(ilk.filed) - pd.to_datetime(ilk.end)).dt.days.median()),
        "p10": float((pd.to_datetime(ilk.filed) - pd.to_datetime(ilk.end)).dt.days
                     .quantile(0.10)),
        "p90": float((pd.to_datetime(ilk.filed) - pd.to_datetime(ilk.end)).dt.days
                     .quantile(0.90)),
        "not": "A4 tanısı — EŞİKSİZ, hiçbir satır bu sütuna göre elenmedi"}

    # ---- MALİ-YIL HİZASI: frame (dönem özelliği) → yoksa dönem-ortası takvim çeyreği
    st, en = pd.to_datetime(ilk.start), pd.to_datetime(ilk.end)
    mid = st + (en - st) / 2
    ilk["cq_turetilen"] = "CY" + mid.dt.year.astype(str) + "Q" + mid.dt.quarter.astype(str)
    fr = (q.dropna(subset=["frame"]).groupby(["symbol", "start", "end"]).frame.first()
          .rename("frame_donem"))
    ilk = ilk.merge(fr, on=["symbol", "start", "end"], how="left")
    m = ilk.frame_donem.notna()
    acc["frame_kaynakli_donem"] = int(m.sum())
    acc["frame_yok_turetilen_donem"] = int((~m).sum())
    acc["frame_turetilen_uyum_orani"] = O._r6(
        float((ilk.frame_donem[m] == ilk.cq_turetilen[m]).mean())) if int(m.sum()) else None
    acc["frame_turetilen_uyumsuz_n"] = int((ilk.frame_donem[m] != ilk.cq_turetilen[m]).sum())
    ilk["cq"] = ilk.frame_donem.fillna(ilk.cq_turetilen)
    ilk["cq_kaynak"] = np.where(m, "sec_frame", "donem_ortasi_turetilen")

    # ---- ETİKET ÖNCELİĞİ (TEK YER): (symbol, cq) başına en yüksek öncelikli etiket
    pri = {t: i for i, t in enumerate(O.GELIR_ONCELIK)}
    ilk["oncelik"] = ilk.tag.map(pri)
    cakisma = ilk.groupby(["symbol", "cq"]).size()
    acc["ayni_sembol_ceyrek_coklu_kayit_grup"] = int((cakisma > 1).sum())
    sel = (ilk.sort_values(["symbol", "cq", "oncelik", "filed"])
           .groupby(["symbol", "cq"], as_index=False).first())
    acc["sembol_ceyrek_n"] = int(len(sel))
    acc["sembol_n"] = int(sel.symbol.nunique())
    acc["etiket_dagilimi"] = sel.tag.value_counts().to_dict()
    acc["cq_kaynak_dagilimi"] = sel.cq_kaynak.value_counts().to_dict()

    sel["qidx"] = sel.cq.map(_qidx)
    sel["gecikme_filed_eksi_end"] = (pd.to_datetime(sel.filed)
                                     - pd.to_datetime(sel.end)).dt.days
    sel = sel.sort_values(["symbol", "qidx"]).reset_index(drop=True)

    # ---- kapsam beyanı: evrende olup serisi olmayan semboller (None + neden)
    var = set(sel.symbol)
    tum_fund = set(F.symbol)
    acc["kapsam_disi_sembol"] = []
    for s in evren:
        if s in var:
            continue
        if s not in tum_fund:
            neden = ("fundamentals arşivinde HİÇ satır yok (CIK/us-gaap boşluğu — yabancı "
                     "ihraççı 20-F yolu); sembolün TÜM dönemleri ölçülemez → None")
        else:
            etk = sorted(F[F.symbol == s].tag.unique())
            neden = (f"arşivde var ama ÇEYREKLİK gelir etiketi yok (mevcut etiketler: {etk}); "
                     "finansal sektör gelir tablosu us-gaap Revenues ile raporlanmıyor → None")
        acc["kapsam_disi_sembol"].append({"symbol": s, "neden": neden})
    acc["kapsam_disi_sembol_n"] = len(acc["kapsam_disi_sembol"])
    acc["evren_kapsam"] = f"{acc['sembol_n']}/{len(evren)}"
    return sel[["symbol", "cq", "qidx", "start", "end", "filed", "val", "tag",
                "cq_kaynak", "gecikme_filed_eksi_end"]], acc


# ------------------------------------------------------------------ EVREN PANELİ (050 BİREBİR)
def panel_matris(pan: dict):
    """edg050_pead_2026-08-23/olcum.py::panel_matris ile BİREBİR (aynı-gün evren tabanı)."""
    syms = sorted(pan)
    tum_gun = sorted(set().union(*[set(v["dates"].tolist()) for v in pan.values()]))
    gidx = {d: i for i, d in enumerate(tum_gun)}
    C = np.full((len(tum_gun), len(syms)), np.nan)
    for j, s in enumerate(syms):
        v = pan[s]
        C[[gidx[d] for d in v["dates"]], j] = v["close"]
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


# ------------------------------------------------------------------ PIT as-of (SAF YOL)
def _asof_saf(kayitlar: list[dict], t: str):
    """SAF/naif PIT yolu — yıkıcı sınamanın referansı. `filed <= t` süzülür, en büyük qidx
    seçilir, yoy/ivme yeniden kurulur. Hızlı yolla AYNI sayıyı vermek ZORUNDADIR."""
    gor = [r for r in kayitlar if r["filed"] <= t]
    if not gor:
        return None
    d = {}
    for r in gor:                      # aynı qidx tekrarı yok (faz1 tekilleştirdi)
        d[r["qidx"]] = r
    q = max(d)
    def v(k):
        r = d.get(k)
        return None if r is None else float(r["val"])
    v0, v1, v4, v5 = v(q), v(q - 1), v(q - 4), v(q - 5)
    yoy = None if (v0 is None or v4 is None or v4 <= 0) else v0 / v4 - 1.0
    yoy_p = None if (v1 is None or v5 is None or v5 <= 0) else v1 / v5 - 1.0
    ivme = None if (yoy is None or yoy_p is None) else yoy - yoy_p
    return {"qidx": q, "filed": d[q]["filed"], "end": d[q]["end"], "cq": d[q]["cq"],
            "tag": d[q]["tag"], "gecikme_filed_eksi_end": int(d[q]["gecikme_filed_eksi_end"]),
            "yoy": yoy, "yoy_onceki": yoy_p, "ivme": ivme,
            "etiket_yoy_ayni_mi": (None if (d.get(q) is None or d.get(q - 4) is None)
                                   else bool(d[q]["tag"] == d[q - 4]["tag"]))}


# ------------------------------------------------------------------ [2] AYLIK PANEL
def panel_kur(temel: pd.DataFrame, pan: dict, gidx, C, runiv, rc, gozlem_gunleri):
    kayit_by_sym: dict[str, list[dict]] = {}
    for s, sub in temel.groupby("symbol", sort=False):
        kayit_by_sym[s] = sub.to_dict("records")

    satirlar, neden = [], {}

    def dus(k):
        neden[k] = neden.get(k, 0) + 1

    for s, kayitlar in kayit_by_sym.items():
        v = pan.get(s)
        if v is None:
            dus("bar_paneli_yok (şablon bar yolu sembolü yüklemedi)")
            continue
        dates = v["dates"]
        pos = {d: i for i, d in enumerate(dates)}
        n = len(dates)
        for t in gozlem_gunleri:
            i = pos.get(t)
            if i is None:
                dus("sembolun_o_ay_sonu_gununde_bari_yok")
                continue
            a = _asof_saf(kayitlar, t)
            if a is None:
                dus("gozlem_gununde_gorunur_ceyrek_yok (PIT: filed<=t kayıt yok)")
                continue
            yas = (dt.date.fromisoformat(t) - dt.date.fromisoformat(a["filed"])).days
            if yas > BAYAT_CEYREK_GUN:
                dus(f"bayat_ceyrek>{BAYAT_CEYREK_GUN}g (beyanlı veri-hijyeni guard'ı)")
                continue
            if a["yoy"] is None:
                dus("yoy_olculemez (q veya q-4 PIT-görünür değil / payda<=0)")
                continue
            rec = {"symbol": s, "t": t, "i": i, "cq": a["cq"], "qidx": a["qidx"],
                   "filed": a["filed"], "end": a["end"], "tag": a["tag"],
                   "yoy": O._r6(a["yoy"]),
                   "ivme": None if a["ivme"] is None else O._r6(a["ivme"]),
                   "ivme_neden": None if a["ivme"] is not None else
                                 "q-1 veya q-5 PIT-görünür değil (10-K Q4 boşluğu dâhil)",
                   "gecikme_filed_eksi_end": a["gecikme_filed_eksi_end"],
                   "gozlem_eksi_filed_gun": yas,
                   "etiket_yoy_ayni_mi": a["etiket_yoy_ayni_mi"]}
            for H in UFUKLAR:
                if i + H >= n:
                    rec[f"fazla{H}"] = None
                    rec[f"fazla{H}_neden"] = "ufuk_penceresi_seri_disi"
                    continue
                g_son = [gidx[d] for d in dates[i + 1:i + H + 1]]
                if np.min(rc[g_son]) < MIN_PAYDA:
                    rec[f"fazla{H}"] = None
                    rec[f"fazla{H}_neden"] = f"gunluk_evren_paydasi<{MIN_PAYDA}"
                    continue
                r_sym = float(v["close"][i + H] / v["close"][i] - 1.0)
                r_u = float(np.prod(1.0 + runiv[g_son]) - 1.0)
                rec[f"fazla{H}"] = O._r6(r_sym - r_u)
                rec[f"fazla{H}_neden"] = None
                rec[f"payda{H}_min"] = int(np.min(rc[g_son]))
            satirlar.append(rec)
    return satirlar, neden


# ------------------------------------------------------------------ [6] PIT YIKICI SINAMA
def pit_yikici_sinama(satirlar, temel):
    """YIKICI: her panel satırı için sembolün TÜM kayıt listesi `filed > t` olanlar ATILARAK
    yeniden kurulur ve yoy/ivme SIFIRDAN hesaplanır. Kayıtlı değerden farklıysa boru hattı
    geleceği okuyor demektir. TÜM satırlarda koşar — örneklem değil."""
    kayit_by_sym = {s: sub.to_dict("records") for s, sub in temel.groupby("symbol", sort=False)}
    ihlal_yoy = ihlal_ivme = 0
    leak = 0
    ayrisan = []
    for r in satirlar:
        kes = [k for k in kayit_by_sym[r["symbol"]] if k["filed"] <= r["t"]]
        if any(k["filed"] > r["t"] for k in kes):
            leak += 1
        a = _asof_saf(kes, r["t"])
        y = None if a is None or a["yoy"] is None else O._r6(a["yoy"])
        iv = None if a is None or a["ivme"] is None else O._r6(a["ivme"])
        if y != r["yoy"]:
            ihlal_yoy += 1
            if len(ayrisan) < 5:
                ayrisan.append({"symbol": r["symbol"], "t": r["t"], "kayitli": r["yoy"],
                                "kesik": y, "alan": "yoy"})
        if iv != r["ivme"]:
            ihlal_ivme += 1
            if len(ayrisan) < 5:
                ayrisan.append({"symbol": r["symbol"], "t": r["t"], "kayitli": r["ivme"],
                                "kesik": iv, "alan": "ivme"})
    dogrudan_leak = sum(1 for r in satirlar if r["filed"] > r["t"])
    return {"tanim": "her satırda sembolün kayıt listesinden filed>t olanlar ATILIP yoy/ivme "
                     "sıfırdan kuruldu; hiçbir gelecek dosyalama girdi değil.",
            "kapsam": "TÜM panel satırları (örneklem değil)",
            "sinanan_satir": len(satirlar), "ihlal_yoy": ihlal_yoy, "ihlal_ivme": ihlal_ivme,
            "dogrudan_filed_buyuk_t": dogrudan_leak, "kesik_girdide_leak": leak,
            "ayrisan_ornek": ayrisan,
            "gecti": bool(len(satirlar) > 0 and ihlal_yoy == 0 and ihlal_ivme == 0
                          and dogrudan_leak == 0 and leak == 0)}


# ------------------------------------------------------------------ İSTATİSTİK (SEED 20260812)
def mean_block_boot_053(y, dates, rng, n_boot=O.BOOT, blok=O.BLOCK):
    """ortak.mean_block_boot ile AYNI cebir; RNG kart tohumundan (20260812)."""
    y = np.asarray(y, float)
    dates = np.asarray(dates)
    uniq, inv = np.unique(dates, return_inverse=True)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem tarihi sayısı < {blok * 3}"}
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


def fark_block_boot_053(yA, dA, yB, dB, rng, n_boot=O.BOOT, blok=O.BLOCK):
    """ortak.fark_with_ci ile AYNI cebir (ORTAK gün dizisi iki dilime de uygulanır), RNG kart
    tohumundan. TANI amaçlıdır — kart karar kuralı bu istatistiği OKUMAZ."""
    yA, yB = np.asarray(yA, float), np.asarray(yB, float)
    dA, dB = np.asarray(dA), np.asarray(dB)
    uniq = np.unique(np.concatenate([dA, dB]))
    nd = len(uniq)
    if nd < blok * 3:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": f"ortak gözlem tarihi < {blok * 3}"}
    ia, ib = np.searchsorted(uniq, dA), np.searchsorted(uniq, dB)
    sA = np.bincount(ia, weights=yA, minlength=nd)
    cA = np.bincount(ia, minlength=nd).astype(float)
    sB = np.bincount(ib, weights=yB, minlength=nd)
    cB = np.bincount(ib, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = rng.integers(0, nd - blok + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        ca, cb = cA[gun].sum(), cB[gun].sum()
        if ca <= 0 or cb <= 0:
            atlanan += 1
            continue
        vals.append(sA[gun].sum() / ca - sB[gun].sum() / cb)
    if len(vals) < n_boot * 0.5:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    lo, hi = O._r6(np.percentile(a, 2.5)), O._r6(np.percentile(a, 97.5))
    return {"nA": int(len(yA)), "nB": int(len(yB)),
            "fark": O._r6(float(yA.mean()) - float(yB.mean())),
            "ci": {"lo": lo, "hi": hi, "seviye": 0.95}, "n_gun": nd, "blok": blok,
            "n_boot_gecerli": len(vals), "atlanan": atlanan, "seed": SEED,
            "anlamli": bool(lo > 0 or hi < 0), "pozitif_anlamli": bool(lo > 0), "neden": None}


def hucre(y, dates, rng):
    n = int(len(y))
    if n < O.MIN_SLICE:
        return {"n": n, "ort": None, "ci": None, "neden": f"n<{O.MIN_SLICE}"}
    y = np.asarray(y, float)
    ci = mean_block_boot_053(y, dates, rng)
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


# ================================================================== FAZ 1
def faz1():
    print("== FAZ1: [1] çeyreklik gelir serisi — İLK-İFŞA + etiket önceliği + frame hizası ==")
    sel, acc = temel_kur()
    sel.to_csv(BURASI / "temel_ceyrek.csv", index=False)
    print(f"   ilk-ifşa satır: {acc['ilk_ifsa_satir']} "
          f"(düşen yeniden-beyan: {acc['ilk_ifsa_dusen_yeniden_beyan_satir']})")
    print(f"   sembol-çeyrek: {acc['sembol_ceyrek_n']}  sembol: {acc['evren_kapsam']}")
    print(f"   frame kaynaklı dönem: {acc['frame_kaynakli_donem']} "
          f"(türetilen: {acc['frame_yok_turetilen_donem']}, "
          f"uyum={acc['frame_turetilen_uyum_orani']})")
    print(f"   kapsam dışı sembol: {[x['symbol'] for x in acc['kapsam_disi_sembol']]}")
    O.json_yaz(BURASI / "faz1_temel.json",
               {"kart": "EDG-2026-053", "faz": 1, "kapsam": acc,
                "kod_sha256": {"olcum": _sha(BURASI / "olcum.py")}})
    print("== yazıldı: faz1_temel.json + temel_ceyrek.csv ==")


# ================================================================== FAZ 2
def faz2():
    print("== FAZ2: [2] aylık panel + PIT as-of + fazla getiri + kill#1 + PIT yıkıcı sınama ==")
    temel = pd.read_csv(BURASI / "temel_ceyrek.csv", dtype={"filed": str, "end": str,
                                                            "start": str, "cq": str})
    f1 = json.load(open(BURASI / "faz1_temel.json"))
    kap = dict(f1["kapsam"])

    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol yüklendi")
    bm = {k: v for k, v in bar_acc.items() if k not in ("takvim_reddedilen",)}
    bm["takvim_reddedilen_n"] = len(bar_acc["takvim_reddedilen"])

    tum_gun, gidx, C, runiv, rc = panel_matris(pan)
    gozlem = O.ay_sonu_gunleri(np.array(tum_gun))
    kap["gozlem_gunu_n"] = int(len(gozlem))
    kap["gozlem_araligi"] = [str(gozlem[0]), str(gozlem[-1])]
    print(f"   gözlem günü (ay-sonu): {len(gozlem)}  [{gozlem[0]} .. {gozlem[-1]}]")

    satirlar, neden = panel_kur(temel, pan, gidx, C, runiv, rc, list(gozlem))
    pd.DataFrame(satirlar).to_csv(BURASI / "panel.csv", index=False)
    print(f"   yazıldı: panel.csv ({len(satirlar)} satır)")

    kap["panel_none_neden_histogram"] = neden
    kap["sembol_ay_yoy"] = len(satirlar)
    kap["sembol_ay_ivme"] = int(sum(1 for r in satirlar if r["ivme"] is not None))
    kap["panel_sembol_n"] = len({r["symbol"] for r in satirlar})
    if satirlar:
        kap["panel_takvim_araligi"] = [min(r["t"] for r in satirlar),
                                       max(r["t"] for r in satirlar)]
    for H in UFUKLAR:
        kap[f"ufuk{H}_olculebilen"] = int(sum(1 for r in satirlar
                                              if r.get(f"fazla{H}") is not None))
        nd = {}
        for r in satirlar:
            if r.get(f"fazla{H}") is None:
                nd[r.get(f"fazla{H}_neden")] = nd.get(r.get(f"fazla{H}_neden"), 0) + 1
        kap[f"ufuk{H}_none_neden"] = nd

    # ---- A4 TANI: dosyalama gecikmesi (EŞİKSİZ)
    if satirlar:
        g1 = np.array([r["gecikme_filed_eksi_end"] for r in satirlar], float)
        g2 = np.array([r["gozlem_eksi_filed_gun"] for r in satirlar], float)
        kap["A4_dosyalama_gecikmesi_TANI"] = {
            "tanim": "EŞİKSİZ tanı — hiçbir satır bu sütunlara göre elenmedi (bayat guard'ı "
                     "AYRI ve beyanlıdır).",
            "filed_eksi_end_gun": {"medyan": float(np.median(g1)), "p10": float(np.percentile(g1, 10)),
                                   "p90": float(np.percentile(g1, 90)), "min": float(g1.min()),
                                   "maks": float(g1.max())},
            "gozlem_eksi_filed_gun": {"medyan": float(np.median(g2)),
                                      "p10": float(np.percentile(g2, 10)),
                                      "p90": float(np.percentile(g2, 90)),
                                      "min": float(g2.min()), "maks": float(g2.max())}}
        ea = [r["etiket_yoy_ayni_mi"] for r in satirlar if r["etiket_yoy_ayni_mi"] is not None]
        kap["etiket_yoy_ciftinde_ayni_TANI"] = {
            "n": len(ea), "ayni_oran": O._r6(float(np.mean(ea))) if ea else None,
            "not": "TANI — q ve q-4 çeyreklerinin etiket önceliği aynı etikete düşme oranı; "
                   "eşiksiz, hiçbir satır elenmedi"}

    pit = pit_yikici_sinama(satirlar, temel)
    print(f"   PIT yıkıcı sınama: n={pit['sinanan_satir']} ihlal_yoy={pit['ihlal_yoy']} "
          f"ihlal_ivme={pit['ihlal_ivme']} geçti={pit['gecti']}")

    out = {"kart": "EDG-2026-053", "faz": 2, "bar_muhasebesi": bm, "kapsam": kap,
           "pit_yikici_sinama": pit,
           "kill1": {"esik": KILL1_SEMBOL_AY, "sembol_ay_yoy": len(satirlar),
                     "sembol_ay_ivme": kap["sembol_ay_ivme"],
                     "gecti": bool(len(satirlar) >= KILL1_SEMBOL_AY)}}
    if len(satirlar) < KILL1_SEMBOL_AY:
        out["ASKI"] = {"kill": 1, "esik": KILL1_SEMBOL_AY, "sembol_ay": len(satirlar),
                       "damga": "ASKI — kapsam yetersiz, K harcanmaz; dilim/sonuç ÖLÇÜLMEDİ"}
    O.json_yaz(BURASI / "faz2_panel.json", out)
    print(f"   sembol-ay: yoy={len(satirlar)}  ivme={kap['sembol_ay_ivme']} "
          f"(kill#1 eşik {KILL1_SEMBOL_AY} → geçti={out['kill1']['gecti']})")
    print("== yazıldı: faz2_panel.json ==")
    if len(satirlar) < KILL1_SEMBOL_AY:
        print("!! kill#1 → ASKI damgası, ölçüm DURDU")


def _panel_oku() -> pd.DataFrame:
    return pd.read_csv(BURASI / "panel.csv", dtype={"t": str, "symbol": str, "cq": str,
                                                    "filed": str, "end": str})


# ================================================================== FAZ 3 — DİLİM EŞİKLERİ
def _ay_ici_dilim(df: pd.DataFrame, kol: str):
    """AY-İÇİ kesitten p70 (üst %30) ve p30 (alt %30 — TANI). Kesit < MIN_AY_KESIT ise o ay
    dilimsizdir (None + neden)."""
    ust = np.zeros(len(df), bool)
    alt = np.zeros(len(df), bool)
    esikler, atlanan_ay, atlanan_satir = {}, [], 0
    v = df[kol].to_numpy(float)
    for t, idx in df.groupby("t").indices.items():
        idx = np.asarray(idx)
        sub = v[idx]
        m = np.isfinite(sub)
        if int(m.sum()) < MIN_AY_KESIT:
            atlanan_ay.append(t)
            atlanan_satir += int(len(idx))
            continue
        p70 = float(np.percentile(sub[m], UST_YUZDELIK))
        p30 = float(np.percentile(sub[m], ALT_YUZDELIK))
        esikler[t] = {"n": int(m.sum()), "p70": O._r6(p70), "p30": O._r6(p30)}
        ust[idx[np.where(m & (sub >= p70))[0]]] = True
        alt[idx[np.where(m & (sub <= p30))[0]]] = True
    return ust, alt, {"esik_ay_n": len(esikler), "dilimsiz_ay": atlanan_ay,
                      "dilimsiz_ay_n": len(atlanan_ay), "dilimsiz_satir": atlanan_satir,
                      "min_ay_kesit": MIN_AY_KESIT,
                      "neden": f"ay kesiti < {MIN_AY_KESIT} → o ayın satırları dilimsiz (None)",
                      "esikler": esikler}


def faz3():
    print("== FAZ3: [3] AY-İÇİ dilim eşikleri — fazla-getiri istatistiği OKUNMADAN yazılır ==")
    f2 = json.load(open(BURASI / "faz2_panel.json"))
    if not f2["kill1"]["gecti"]:
        print("!! kill#1 ASKI — faz3 koşmaz")
        return
    df = _panel_oku()
    dokum = {"kart": "EDG-2026-053", "faz": 3,
             "yazim_zamani_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "ust_yuzdelik": UST_YUZDELIK, "alt_yuzdelik_TANI": ALT_YUZDELIK,
             "beyan": "yüzdelikler AY-İÇİ KESİTTEN (kart features_asof); bu döküm fazla-getiri "
                      "istatistikleri HESAPLANMADAN ÖNCE ayrı dosyaya yazıldı (mtime kanıt)."}
    for kol in ("yoy", "ivme"):
        ust, alt, meta = _ay_ici_dilim(df, kol)
        v = df[kol].to_numpy(float)
        v = v[np.isfinite(v)]
        dokum[kol] = {"n_olculebilen": int(len(v)),
                      "havuz_dagilimi": {str(q): O._r6(float(np.percentile(v, q)))
                                         for q in (1, 5, 10, 25, 50, 70, 75, 90, 95, 99)},
                      "ort": O._r6(float(v.mean())), "std": O._r6(float(v.std(ddof=1))),
                      "ust_dilim_satir_n": int(ust.sum()), "alt_dilim_satir_n_TANI": int(alt.sum()),
                      "ay_ici_esik_meta": meta}
        print(f"   {kol}: n={len(v)} p70(havuz)={dokum[kol]['havuz_dagilimi']['70']} "
              f"üst dilim satır={int(ust.sum())} dilimsiz ay={meta['dilimsiz_ay_n']}")
    O.json_yaz(BURASI / "faz3_esik_dokumu.json", dokum)
    print("== yazıldı: faz3_esik_dokumu.json ==")


# ================================================================== FAZ 4 — SONUÇ + CI + MALİYET
def faz4():
    print("== FAZ4: [4] dilim fazla-getirileri + 21g blok-bootstrap CI + [5] maliyet ==")
    f2 = json.load(open(BURASI / "faz2_panel.json"))
    if not f2["kill1"]["gecti"]:
        print("!! kill#1 ASKI — faz4 koşmaz")
        return
    json.load(open(BURASI / "faz3_esik_dokumu.json"))     # eşik dökümü FAZ3'te donmuş olmalı
    df = _panel_oku()
    rng = np.random.default_rng(SEED)

    sonuc, tani = {}, {}
    for kol, ad in (("yoy", "yoy_buyume_ust_30pct"), ("ivme", "ivme_ust_30pct")):
        ust, alt, meta = _ay_ici_dilim(df, kol)
        for isim, mask, hedef in ((ad, ust, sonuc),
                                  (f"{kol}_alt_30pct_TANI", alt, tani)):
            blok = {"gozlem_n": int(mask.sum()),
                    "dilim_meta": {"esik_ay_n": meta["esik_ay_n"],
                                   "dilimsiz_ay_n": meta["dilimsiz_ay_n"],
                                   "dilimsiz_satir": meta["dilimsiz_satir"]}}
            for H in UFUKLAR:
                sub = df[mask]
                sub = sub[sub[f"fazla{H}"].notna()]
                h = hucre(sub[f"fazla{H}"].to_numpy(float), sub["t"].to_numpy(), rng)
                h["ufuk_none_gozlem"] = int(mask.sum()) - int(len(sub))
                blok[f"@{H}g"] = h
                print(f"   {isim} @{H}g: n={h['n']} ort={h['ort']} ci={h.get('ci')} "
                      f"net10={h.get('net_10bps_tek_yon')}")
            if isim.endswith("_TANI"):
                blok["not"] = "TANI — kart karar kuralı bu dilimi OKUMAZ, K harcamaz"
            hedef[isim] = blok

    # tüm gözlemler (bağlam TANI)
    blok = {"gozlem_n": int(len(df))}
    for H in UFUKLAR:
        sub = df[df[f"fazla{H}"].notna()]
        h = hucre(sub[f"fazla{H}"].to_numpy(float), sub["t"].to_numpy(), rng)
        blok[f"@{H}g"] = h
        print(f"   tum_gozlem_TANI @{H}g: n={h['n']} ort={h['ort']} ci={h.get('ci')}")
    blok["not"] = "hüküm-dışı bağlam; kart karar kuralı yalnız iki üst dilimi okur"
    tani["tum_gozlem_TANI"] = blok

    # ---- YAYILIM TANI (üst%30 − alt%30, ORTAK gün eşleştirmeli). Kayıtlı hücrelerin RNG
    # akışını BOZMAMAK için EN SONA eklenir ve TAZE default_rng(SEED) kullanır.
    yay = {"not": "TANI — kart karar kuralı OKUMAZ. Kapsanan alt-evrenin tabanı negatiftir "
                  "(tum_gozlem_TANI); yayılım bu taban kaymasından arınmış tek-yönlü okumadır. "
                  "TAZE default_rng(20260812) ile hesaplandı; kayıtlı hücrelerin akışına "
                  "dokunmaz."}
    for kol, ad in (("yoy", "yoy_buyume"), ("ivme", "ivme")):
        ust, alt, _ = _ay_ici_dilim(df, kol)
        b = {}
        for H in UFUKLAR:
            a_ = df[ust]; a_ = a_[a_[f"fazla{H}"].notna()]
            b_ = df[alt]; b_ = b_[b_[f"fazla{H}"].notna()]
            r = fark_block_boot_053(a_[f"fazla{H}"].to_numpy(float), a_["t"].to_numpy(),
                                    b_[f"fazla{H}"].to_numpy(float), b_["t"].to_numpy(),
                                    np.random.default_rng(SEED))
            for bp in MALIYET_BPS:
                r[f"net_{int(bp)}bps_iki_bacak_TANI"] = (
                    None if r["fark"] is None else O._r6(r["fark"] - 2 * bp / 10000.0))
            b[f"@{H}g"] = r
            print(f"   [TANI] {ad} ust30−alt30 @{H}g: fark={r['fark']} ci={r.get('ci')}")
        yay[f"{ad}_ust30_eksi_alt30_TANI"] = b
    tani["yayilim_TANI"] = yay

    O.json_yaz(BURASI / "faz4_sonuc.json",
               {"kart": "EDG-2026-053", "faz": 4, "seed_ci": SEED,
                "esik_kaynagi": {"dosya": "faz3_esik_dokumu.json",
                                 "not": "ay-içi p70/p30 eşikleri FAZ3'te dondu ve aynı fonksiyonla "
                                        "(_ay_ici_dilim) yeniden üretildi; eşik tanımı değişmedi"},
                "sonuc": sonuc, "TANI": tani})
    print("== yazıldı: faz4_sonuc.json ==")


# ================================================================== FAZ 6 — TANI: CI KARARLILIĞI
def faz6():
    """TANI (hüküm-dışı): kart tohumu (20260812) ve şablon bloğu (21) DONUK karardır. Bu faz
    onları DEĞİŞTİRMEZ; yalnız alt sınırın tohum/blok seçimine duyarlılığını ölçer."""
    print("== FAZ6 (TANI): CI kararlılığı — kart tohumu/bloğu DEĞİŞMEZ, duyarlılık ölçülür ==")
    f2 = json.load(open(BURASI / "faz2_panel.json"))
    if not f2["kill1"]["gecti"]:
        print("!! kill#1 ASKI — faz6 koşmaz")
        return
    df = _panel_oku()
    out = {"kart": "EDG-2026-053", "faz": 6, "kart_tohumu": SEED, "kart_blogu": O.BLOCK,
           "not": "TANI — kart karar kuralı YALNIZ faz4_sonuc.json'daki (seed 20260812, blok 21 "
                  "gözlem tarihi) hücreleri okur; buradaki alternatifler hüküm girdisi DEĞİLDİR. "
                  "Bu panelde bir 'gözlem tarihi' = bir ay-sonu; blok 21 ≈ 21 ay takvim karşılığı."}
    for kol, ad in (("yoy", "yoy_buyume_ust_30pct"), ("ivme", "ivme_ust_30pct")):
        ust, _, _ = _ay_ici_dilim(df, kol)
        blok = {}
        for H in UFUKLAR:
            sub = df[ust]
            sub = sub[sub[f"fazla{H}"].notna()]
            y = sub[f"fazla{H}"].to_numpy(float)
            d = sub["t"].to_numpy()
            if len(y) < O.MIN_SLICE:
                blok[f"@{H}g"] = {"n": int(len(y)), "neden": f"n<{O.MIN_SLICE}"}
                continue
            tohum = {}
            for sd in (20260812, 1, 7, 20260801, 424242, 999983):
                r = mean_block_boot_053(y, d, np.random.default_rng(sd))
                tohum[str(sd)] = {"lo": r["lo"], "hi": r["hi"]}
            blk = {}
            for bb in (1, 3, 6, 12, 21):
                r = mean_block_boot_053(y, d, np.random.default_rng(SEED), blok=bb)
                blk[str(bb)] = {"lo": r["lo"], "hi": r["hi"], "n_gun": r["n_gun"],
                                "neden": r["neden"]}
            los = [v["lo"] for v in tohum.values() if v["lo"] is not None]
            blok[f"@{H}g"] = {
                "n": int(len(y)), "ort": O._r6(float(y.mean())),
                "tohum_duyarliligi_blok21": tohum,
                "blok_duyarliligi_tohum20260812": blk,
                "alt_sinir_isaret_tutarli_6_tohum":
                    bool(los and (all(x > 0 for x in los) or all(x <= 0 for x in los)))}
            print(f"   {ad} @{H}g: blok duyarlılığı lo = "
                  f"{ {k: v['lo'] for k, v in blk.items()} }")
        out[ad] = blok
    O.json_yaz(BURASI / "faz6_ci_kararlilik.json", out)
    print("== yazıldı: faz6_ci_kararlilik.json ==")


# ================================================================== FAZ 5 — BİRLEŞTİRME
def _karar_girdileri(f4):
    """Kartın DONUK karar kuralının GİRDİLERİ (mekanik boolean'lar). HÜKÜM DEĞİLDİR."""
    g = {}
    for ad in ("yoy_buyume_ust_30pct", "ivme_ust_30pct"):
        h60 = f4["sonuc"].get(ad, {}).get("@60g", {})
        h20 = f4["sonuc"].get(ad, {}).get("@20g", {})
        ci60 = h60.get("ci")
        net10 = h60.get("net_10bps_tek_yon")
        g[ad] = {
            "@60g_ort": h60.get("ort"), "@60g_ci": ci60,
            "@60g_ci_sifir_disi": None if ci60 is None else bool(ci60["lo"] > 0 or ci60["hi"] < 0),
            "@60g_pozitif_anlamli": h60.get("pozitif_anlamli"),
            "@60g_net_10bps": net10,
            "@60g_net_10bps_pozitif": None if net10 is None else bool(net10 > 0),
            "@20g_ort": h20.get("ort"), "@20g_ci": h20.get("ci"),
            "@20g_ci_sifir_disi": None if h20.get("ci") is None else
                bool(h20["ci"]["lo"] > 0 or h20["ci"]["hi"] < 0),
            "kart_atesleme_kosulu(@60g CI 0-dışı POZİTİF VE net10bps>0)":
                None if (ci60 is None or net10 is None)
                else bool(ci60["lo"] > 0 and net10 > 0)}
    return g


def _karar_dallari(g, f4, f6):
    """Kartın success_metric'indeki ÜÇ dalın mekanik değerlendirmesi. HÜKÜM DEĞİLDİR —
    Rol-1'in okuyacağı girdidir. Dalların hiçbiri eşleşmiyorsa BUNU DA açıkça söyler
    (yutulmaz; kart metni bu ara durumu adlandırmıyor)."""
    adlar = ("yoy_buyume_ust_30pct", "ivme_ust_30pct")
    atesle = any(g[a]["kart_atesleme_kosulu(@60g CI 0-dışı POZİTİF VE net10bps>0)"] is True
                 for a in adlar)
    ici = []
    for a in adlar:
        for u in ("@20g", "@60g"):
            c = g[a][f"{u}_ci_sifir_disi"]
            ici.append(c is False)
    bilgisiz = all(ici)
    ters = []
    for a in adlar:
        for u in ("@20g", "@60g"):
            h = f4["sonuc"][a][u]
            ters.append(h.get("negatif_anlamli") is True)
    return {
        "dal_1_ATESLEME (herhangi dilim @60g CI 0-dışı POZİTİF VE 10bps net>0)": atesle,
        "dal_2_BILGISIZ (İKİ dilim de @20 VE @60'ta CI 0-İÇİ)": bilgisiz,
        "dal_3_TERS_ANLAMLI (herhangi hücre CI 0-dışı NEGATİF)": any(ters),
        "hicbir_dal_eslesmedi": bool(not atesle and not bilgisiz and not any(ters)),
        "ci_sifir_disi_hucreler": [f"{a} {u}" for a in adlar for u in ("@20g", "@60g")
                                   if g[a][f"{u}_ci_sifir_disi"] is True],
        "ara_durum_beyani":
            ("Kartın ateşleme dalı @60g şartını istediği için ATEŞLEMİYOR; BİLGİSİZ dalı ise "
             "'İKİ dilim de @20 VE @60 CI-0-içi' dediği ve yukarıdaki ci_sifir_disi_hucreler "
             "listesi BOŞ OLMADIĞI için TAM eşleşmiyor. Bu ara durumu ADLANDIRMAK Rol-1'in "
             "işidir; ölçüm onu yutmaz.")
            if (not atesle and not bilgisiz and not any(ters)) else None,
        "@20g_bulgusunun_blok_duyarliligi_TANI": {
            a: (f6.get(a, {}).get("@20g", {}) or {}).get("blok_duyarliligi_tohum20260812")
            for a in adlar},
        "duyarlilik_serhi": "kart bloğu 21 gözlem tarihidir (DONUK). faz6, alt sınırın blok "
                            "seçimine duyarlı olduğunu ölçer — @20g'deki 0-dışılık blok 1/3/6'da "
                            "kayboluyorsa bu Rol-1'in görmesi gereken bir kırılganlıktır."}


def faz5():
    print("== FAZ5: birleştirme → sonuc.json ==")
    out = {"kart": "EDG-2026-053", "tarih": dt.date.today().isoformat(), "seed_ci": SEED,
           "HUKUM": "YOK — hüküm ve kart status geçişi Rol-1'indir; bu dosya yalnız ÖLÇÜMDÜR",
           "kod": {"olcum_py_sha256": _sha(BURASI / "olcum.py"),
                   "ortak_py_sha256": _sha(BURASI / "ortak.py"),
                   "pk_py_sha256": _sha(BURASI / "pk.py"),
                   "ortak_pk_kaynak": "research/olcumler/edg050_pead_2026-08-23/ (BİREBİR kopya; "
                                      "sha256 eşitliği kabuktan doğrulandı)"}}
    f1 = json.load(open(BURASI / "faz1_temel.json"))
    f2 = json.load(open(BURASI / "faz2_panel.json"))
    out["bar_muhasebesi"] = f2["bar_muhasebesi"]
    out["kapsam"] = f2["kapsam"]
    out["kill1_sembol_ay"] = f2["kill1"]
    if "ASKI" in f2:
        out["ASKI"] = f2["ASKI"]
    out["guard_muhasebesi"] = {
        "ilk_ifsa_filtresi": {
            "uygulandi": True,
            "ilk_ifsa_satir": f1["kapsam"]["ilk_ifsa_satir"],
            "dusen_yeniden_beyan_satir": f1["kapsam"]["ilk_ifsa_dusen_yeniden_beyan_satir"],
            "tanim": "her (symbol, tag, start, end) dörtlüsünün en küçük filed'li satırı"},
        "etiket_onceligi_tek_yer": {
            "kaynak": "ortak.GELIR_ONCELIK (olcum.py kendi listesini tanımlamaz; modül "
                      "yüklenirken sıra assert edilir)",
            "sira": f1["kapsam"]["etiket_onceligi"],
            "secilen_etiket_dagilimi": f1["kapsam"]["etiket_dagilimi"]},
        "frame_mali_yil_hizasi": {
            "frame_kaynakli_donem": f1["kapsam"]["frame_kaynakli_donem"],
            "frame_yok_turetilen_donem": f1["kapsam"]["frame_yok_turetilen_donem"],
            "frame_ile_turetilenin_uyum_orani": f1["kapsam"]["frame_turetilen_uyum_orani"],
            "uyumsuz_donem_n": f1["kapsam"]["frame_turetilen_uyumsuz_n"]},
        "A4_dosyalama_gecikmesi": f2["kapsam"].get("A4_dosyalama_gecikmesi_TANI"),
        "bayat_ceyrek_guard": {"gun": BAYAT_CEYREK_GUN,
                               "not": "veri hijyeni; karar eşiği DEĞİL. Düşen gözlem sayısı "
                                      "kapsam.panel_none_neden_histogram'da."}}
    out["pit_oz_sinamasi"] = {
        "yikici_sinama": f2["pit_yikici_sinama"],
        "yapisal_beyan": "yoy/ivme YALNIZ filed<=t kayıtlardan kurulur (_asof_saf tek yol); "
                         "dilim eşikleri ay-içi kesitten, o ayın kendi satırlarından türetilir "
                         "(ileriye bakış yok) ve fazla-getiri istatistiği okunmadan ÖNCE "
                         "faz3_esik_dokumu.json'a donduruldu (mtime sırası kanıt); fazla-getiri "
                         "yalnız SONUÇ tarafıdır."}
    out["evren_kapsam_beyani"] = {
        "evren_n": f1["kapsam"]["evren_n"], "olculebilen_sembol": f1["kapsam"]["sembol_n"],
        "kapsam": f1["kapsam"]["evren_kapsam"],
        "olculemeyen_sembol": f1["kapsam"]["kapsam_disi_sembol"]}
    try:
        out["dilim_esik_dokumu_ozet"] = {
            k: {kk: vv for kk, vv in v.items() if kk != "ay_ici_esik_meta"}
            for k, v in json.load(open(BURASI / "faz3_esik_dokumu.json")).items()
            if k in ("yoy", "ivme")}
        f4 = json.load(open(BURASI / "faz4_sonuc.json"))
        out["sonuc"] = f4["sonuc"]
        out["TANI"] = f4["TANI"]
        out["karar_kurali_girdileri"] = _karar_girdileri(f4)
        try:
            f6 = json.load(open(BURASI / "faz6_ci_kararlilik.json"))
        except FileNotFoundError:
            f6 = {}
        out["karar_kurali_dallari"] = _karar_dallari(out["karar_kurali_girdileri"], f4, f6)
    except FileNotFoundError as e:
        out["sonuc"] = {"None": True, "neden": f"faz3/faz4 çıktısı yok: {e}"}
    try:
        out["ci_kararlilik_TANI"] = {
            "okuma_serhi": "faz4 hücreleri TEK bir RNG akışını sırayla tüketir (kart tohumu "
                           "20260812); faz6 her hücreye TAZE default_rng verir. Aynı tohumun iki "
                           "farklı akış konumu aynı sayıyı VERMEZ — hükme giren değer "
                           "faz4_sonuc.json'dakidir.",
            "olcum": json.load(open(BURASI / "faz6_ci_kararlilik.json"))}
    except FileNotFoundError as e:
        out["ci_kararlilik_TANI"] = {"None": True, "neden": f"faz6 çıktısı yok: {e}"}
    try:
        pk = json.load(open(BURASI / "pk.json"))
        out["pozitif_kontrol_ozet"] = {
            "duzenek": "edg050_pead_2026-08-23/pk.py BİREBİR (sha256 eşit) — AYNI bar yolu, "
                       "AYNI cf katmanı, AYNI çivi",
            "civi_hedef": pk["pozitif_kontrol"]["civi_hedef"],
            "civi_olculen": pk["pozitif_kontrol"]["civi_olculen"],
            "civi_sapma": pk["pozitif_kontrol"]["civi_sapma"],
            "tolerans": pk["pozitif_kontrol"]["tolerans"],
            "GECTI": pk["pozitif_kontrol"]["GECTI"],
            "ic_5_10_20": {h: pk["pozitif_kontrol"][h]["ic"] for h in ("5", "10", "20")},
            "pk4_gecti": pk["pk4_yol_tutarliligi"]["gecti"],
            "pk5_gecti": pk["pk5_ozdeslikler"]["gecti"],
            "YENIDEN_URETILDI_DAMGASI": bool(pk["pozitif_kontrol"]["GECTI"]
                                             and pk["pk4_yol_tutarliligi"]["gecti"]
                                             and pk["pk5_ozdeslikler"]["gecti"]),
            "kill4": "pozitif kontrol yeniden üretildi → ölçüm düzeneği GEÇERLİ"
                     if pk["pozitif_kontrol"]["GECTI"] else
                     "pozitif kontrol TUTMADI → düzenek GEÇERSİZ (kart kill#4)"}
    except Exception as e:
        out["pozitif_kontrol_ozet"] = {"None": True,
                                       "neden": f"pk.json okunamadı: {type(e).__name__}: {e}"}
    out["beyanli_sinirlar"] = {
        "survivorship": "evren bugünün 251'i — her pozitif okuma ÜST-SINIR'dır (kart zorunlu "
                        "kelimesi); delist olmuş isimler evrende yok.",
        "014_ayrismasi": "bu kart kârlılık SEVİYESİNİ (EDG-2026-014) değil gelir DEĞİŞİMİNİ "
                         "(YoY büyüme ve ivme) ölçer; iki kartın tezleri ayrı ailedendir.",
        "portfoy_baglamsizligi": "fazla-getiri portföy-bağlamsızdır; paket-içi etki ayrı kartın "
                                 "işidir. CANLI SİSTEM DEĞİŞMEZ.",
        "Q4_bosluğu": "10-K'lar Q4'ü ayrı çeyrek olarak raporlamayabilir; bu yüzden ivme (q ile "
                      "q-1 gerektirir) kapsamı yoy'dan düşüktür — sayılar kapsam bloğunda.",
        "etiket_ikiligi": "ASC 606 sonrası Revenues → contract-revenue geçişi q ile q-4 arasında "
                          "etiket değiştirebilir; oran kapsam.etiket_yoy_ciftinde_ayni_TANI'da.",
        "blok_yorumu": "21 blok birimi = 21 ardışık AY-SONU gözlem tarihi (≈21 ay); 050'de bir "
                       "birim ≈ bir işlem günüydü. Blok duyarlılığı faz6'da TANI."}
    O.json_yaz(BURASI / "sonuc.json", out)
    print("== yazıldı: sonuc.json ==")


FAZLAR = {"faz1": faz1, "faz2": faz2, "faz3": faz3, "faz4": faz4, "faz6": faz6, "faz5": faz5}

if __name__ == "__main__":
    import sys
    ad = sys.argv[1] if len(sys.argv) > 1 else ""
    if ad not in FAZLAR:
        raise SystemExit(f"kullanım: python olcum.py {{{'|'.join(FAZLAR)}}}")
    FAZLAR[ad]()
