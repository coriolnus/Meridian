#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDG-2026-047 — yakın-pencere ölçümü (ÖLÇÜM AJANI; HÜKÜM YOK, sayı raporlanır).

Kart: research/cards/EDG-2026-047-yakin-pencere.yaml (DONUK — bu betik karta dokunmaz).
Veri: canli_veri/*.jsonl.gz — canlı /opt/meridian/state/bars_intraday/*.jsonl salt-okuma
      ssh-stdin çekimi (damga 2026-08-22T23:42:38Z; satır sayıları canlı wc -l ile birebir
      doğrulandı, bkz. CEKIM_ENVANTERI.json).

DONUK TANIMLAR (karttan, features_asof + universe):
  Pencereler (UTC, dakika barı [başlangıç,60sn)): A = 13:30..13:44 · B = 13:45..13:59
  Satır birimi: ticker×seans×pencere.
  m1 = (maks_high − min_low)/pencere_ilk_open × 1e4  (bps)
  m2 = (B_ilk_open − A_ilk_open)/A_ilk_open × 1e4    (bps, işaretli VE mutlak)
  m3 = pencere hacminin seans toplam hacmine oranı    (kapsam beyanı)
  Ö1: seans-kümeli eşlenik bootstrap (birim=SEANS, B=5000, seed=20260823) ile
      Δ%menzil = medyan_ticker[(m1_B − m1_A)/m1_A] dağılımı; nokta + CI95.

UYGULAMA BEYANLARI (kartın açık bırakmadığı mekanik ayrıntılar — burada sabitlenir):
  * "medyan_ticker": ticker-düzeyi gözlemler (her geçerli ticker×seans çiftinin
    r = (m1_B−m1_A)/m1_A oranı) havuzunun MEDYANI. Eşleniklik r'nin kendisinde
    (aynı ticker×seans'ın A'sı ve B'si birlikte); bootstrap SEANSLARI yerine-koymalı
    yeniden örnekler, seçilen seansların r-satırları (tekrarlı seans → satırlar tekrar)
    havuzlanıp medyan alınır; CI95 = yüzdelik(2.5, 97.5).
  * RNG: Python stdlib random.Random(20260823) (Mersenne Twister); numpy bağımlılığı yok.
  * Kenar durumları (sessiz yutma yok, hepsi sayılır):
    - pencere-içi satırda o/h/l alanı eksik/None ya da o<=0 → satır düşer (sayaç).
    - pencerede <5 geçerli bar → o ticker×seans×pencere satırı düşer (sayaç).
    - r yalnız İKİ pencere de geçerli (≥5 bar) VE m1_A>0 iken; m1_A==0 çifti düşer (sayaç).
    - m2 yalnız iki pencere de geçerliyken (A_ilk_open>0).
    - m3 paydası: o ticker×seansın v'si geçerli (v≥0) TÜM satırlarının toplamı; payda 0 → None (sayaç).
  * Saat-dilimi doğrulaması (kill#2): pencere kesiminden ÖNCE veriden — dakika-başına satır
    yoğunluğu; en büyük dakika-artışının 13:30 UTC'de olması beklenir (ET olsaydı 09:30'da
    görünürdü). Çıktı: dogrulama_saat_dilimi.json. Doğrulanamazsa betik pencere metriği YAZMAZ.

Çıktılar: dogrulama_saat_dilimi.json + sonuc.json (bu dizine). Karta/git'e/state'e yazım YOK.
"""
import gzip
import glob
import hashlib
import json
import os
import random
import statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(BASE, "canli_veri")
A_DAK = {f"13:{m:02d}" for m in range(30, 45)}   # 13:30..13:44
B_DAK = {f"13:{m:02d}" for m in range(45, 60)}   # 13:45..13:59
MIN_BAR = 5
BOOT_B = 5000
SEED = 20260823
PLANS = "/Users/erdemozturk/AI-Trading/state/trade_plans.jsonl"  # yerel DONUK defter


def yukle():
    """Seans → satır listesi. Satır: (ticker, hhmm, o, h, l, v). Ham alan sayaçlarıyla."""
    seanslar = {}
    sayac = {"toplam_satir": 0, "json_bozuk": 0, "t_eksik": 0}
    for yol in sorted(glob.glob(os.path.join(VERI, "*.jsonl.gz"))):
        seans = os.path.basename(yol).replace(".jsonl.gz", "")
        satirlar = []
        with gzip.open(yol, "rt") as f:
            for ham in f:
                sayac["toplam_satir"] += 1
                try:
                    d = json.loads(ham)
                except json.JSONDecodeError:
                    sayac["json_bozuk"] += 1
                    continue
                t = d.get("t")
                if not t or "T" not in t:
                    sayac["t_eksik"] += 1
                    continue
                hhmm = t.split("T")[1][:5]
                satirlar.append((d.get("ticker"), hhmm, d.get("o"), d.get("h"),
                                 d.get("l"), d.get("v")))
        seanslar[seans] = satirlar
    return seanslar, sayac


def saat_dilimi_dogrula(seanslar):
    """kill#2: 13:30 UTC açılış yoğunluk sıçraması VERİDEN, seans başına.

    Ölçüt (kartın şartına birebir): açılış verisi OLAN her seansta
    ort(13:30-13:34) / ort(13:00-13:29) >= 10; açılış verisi OLMAYAN seans
    (arşiv o gün geç başlamış) sıçrama hesabına giremez, AYRI beyan edilir.
    Karşı-hipotez: damgalar ET olsaydı sıçrama 09:30'da olurdu → 09:xx yoğunluğu raporlanır.
    NOT (beyan): ilk koşumdaki vekil ölçüt "20/20 seansta argmax-artış dakikası 13:30"
    idi; 2026-07-28 arşivi 13:55'te başladığı (açılış verisi YOK) için düştü. Ölçüt
    kartın şartına (açılış sıçraması + ET-çürütme) bağlandı; VERİ DEĞİŞMEDİ, kartın
    hiçbir eşiği değişmedi — bu betik-içi vekil ölçüt düzeltmesidir.
    """
    dak_toplam = defaultdict(int)
    seans_sicrama = {}
    acilissiz = []
    for seans, satirlar in sorted(seanslar.items()):
        dak = defaultdict(int)
        for _, hhmm, *_ in satirlar:
            dak[hhmm] += 1
            dak_toplam[hhmm] += 1
        acilis = sum(dak.get(f"13:{m:02d}", 0) for m in range(30, 35)) / 5.0
        onceki = sum(dak.get(f"13:{m:02d}", 0) for m in range(0, 30)) / 30.0
        if acilis == 0:
            acilissiz.append({"seans": seans,
                              "ilk_damga_dakikasi": min((h for h, c in dak.items() if c > 0),
                                                        default=None)})
            continue
        # onceki==0 → sıçrama sonsuz (açılış var, öncesi boş): "sonsuz" olarak beyan
        seans_sicrama[seans] = round(acilis / onceki, 1) if onceki > 0 else "sonsuz"
    ort = lambda ks: (sum(dak_toplam[k] for k in ks) / len(ks)) if ks else 0.0
    once = [f"13:{m:02d}" for m in range(0, 30)]     # 13:00-13:29 UTC (premarket kuyruğu)
    sonra = [f"13:{m:02d}" for m in range(30, 60)]   # 13:30-13:59 UTC (seans açılışı)
    et_once = [f"09:{m:02d}" for m in range(0, 60)]  # ET-damga hipotezi kontrolü
    hepsi_sicradi = bool(seans_sicrama) and all(
        (v == "sonsuz" or v >= 10) for v in seans_sicrama.values())
    et_curuk = dak_toplam.get("09:30", 0) * 10 < dak_toplam.get("13:30", 0)
    # sıçrama ölçütü yalnız açılış-verisi-olan seanslarda; en az 15 açılışlı seans
    # yoksa kill#3 kapsam kuralı zaten devrede — burada yalnız beyan edilir.
    rapor = {
        "yontem": "seans-başına ort(13:30-13:34)/ort(13:00-13:29) sıçrama oranı + ET karşı-hipotez (09:xx yoğunluğu); grafiksiz sayım",
        "vekil_olcut_beyani": "ilk koşum vekili (20/20 argmax=13:30) 2026-07-28'in açılış-verisi-yokluğuyla düştü; ölçüt kartın şartına bağlandı, veri ve kart eşiği değişmedi",
        "ort_satir_dk_1300_1329": round(ort(once), 1),
        "ort_satir_dk_1330_1359": round(ort(sonra), 1),
        "satir_1329": dak_toplam.get("13:29", 0),
        "satir_1330": dak_toplam.get("13:30", 0),
        "satir_0930": dak_toplam.get("09:30", 0),
        "ort_satir_dk_0900_0959": round(ort(et_once), 1),
        "seans_basina_acilis_sicrama_orani": seans_sicrama,
        "sicrama_min": min(seans_sicrama.values()) if seans_sicrama else None,
        "acilis_verisi_olmayan_seanslar": acilissiz,
        "acilisli_seans_sayisi": len(seans_sicrama),
        "seans_sayisi": len(seanslar),
        "kapanis_1959_satir": dak_toplam.get("19:59", 0),
        "kapanis_2000_satir": dak_toplam.get("20:00", 0),
        "sonuc_utc_mi": hepsi_sicradi and et_curuk,
    }
    return rapor


def pencere_metrikleri(seanslar):
    """ticker×seans başına m1_A, m1_B, r, m2, m3_A, m3_B + kenar sayaçları."""
    kenar = {
        "pencere_satir_alan_eksik_veya_open_sifir": 0,
        "pencere_A_bar_yetersiz_dusen": 0,   # <5 geçerli bar → ticker×seans×A düştü
        "pencere_B_bar_yetersiz_dusen": 0,
        "cift_m1A_sifir_dusen": 0,           # r tanımsız (m1_A==0)
        "m3_payda_sifir": 0,
        "seans_v_negatif_veya_eksik_satir": 0,
    }
    kayitlar = []       # dict: seans, ticker, m1_A, m1_B, r, m2, m3_A, m3_B
    for seans, satirlar in sorted(seanslar.items()):
        pencere = defaultdict(lambda: {"A": [], "B": []})   # ticker → pencere barları
        hacim = defaultdict(float)                          # ticker → seans toplam hacim
        for tk, hhmm, o, h, l, v in satirlar:
            if isinstance(v, (int, float)) and v >= 0:
                hacim[tk] += v
            else:
                kenar["seans_v_negatif_veya_eksik_satir"] += 1
            if hhmm in A_DAK or hhmm in B_DAK:
                p = "A" if hhmm in A_DAK else "B"
                gecerli = all(isinstance(x, (int, float)) for x in (o, h, l)) and o > 0
                if not gecerli:
                    kenar["pencere_satir_alan_eksik_veya_open_sifir"] += 1
                    continue
                vv = v if isinstance(v, (int, float)) and v >= 0 else 0.0
                pencere[tk][p].append((hhmm, o, h, l, vv))
        for tk, pc in pencere.items():
            kayit = {"seans": seans, "ticker": tk}
            for p in ("A", "B"):
                barlar = sorted(pc[p])                       # hhmm sıralı
                if len(barlar) < MIN_BAR:
                    kenar[f"pencere_{p}_bar_yetersiz_dusen"] += 1
                    kayit[f"m1_{p}"] = None
                    continue
                ilk_open = barlar[0][1]
                m1 = (max(b[2] for b in barlar) - min(b[3] for b in barlar)) / ilk_open * 1e4
                kayit[f"m1_{p}"] = m1
                kayit[f"ilk_open_{p}"] = ilk_open
                pv = sum(b[4] for b in barlar)
                if hacim.get(tk, 0.0) > 0:
                    kayit[f"m3_{p}"] = pv / hacim[tk]
                else:
                    kenar["m3_payda_sifir"] += 1
                    kayit[f"m3_{p}"] = None
            if kayit.get("m1_A") is not None and kayit.get("m1_B") is not None:
                if kayit["m1_A"] > 0:
                    kayit["r"] = (kayit["m1_B"] - kayit["m1_A"]) / kayit["m1_A"]
                else:
                    kenar["cift_m1A_sifir_dusen"] += 1
                    kayit["r"] = None
                kayit["m2"] = (kayit["ilk_open_B"] - kayit["ilk_open_A"]) / kayit["ilk_open_A"] * 1e4
            kayitlar.append(kayit)
    return kayitlar, kenar


def yuzdelik(veri, q):
    """Doğrusal enterpolasyonlu yüzdelik (numpy'siz)."""
    s = sorted(veri)
    if not s:
        return None
    k = (len(s) - 1) * q / 100.0
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def o1_bootstrap(kayitlar):
    """Seans-kümeli eşlenik bootstrap: birim=SEANS, B=5000, seed=20260823."""
    seans_r = defaultdict(list)
    for k in kayitlar:
        if k.get("r") is not None:
            seans_r[k["seans"]].append(k["r"])
    seanslar = sorted(seans_r)
    havuz = [r for s in seanslar for r in seans_r[s]]
    if not havuz:
        return None, None, 0, 0
    nokta = statistics.median(havuz)
    rng = random.Random(SEED)
    medyanlar = []
    for _ in range(BOOT_B):
        secim = [seanslar[rng.randrange(len(seanslar))] for _ in seanslar]
        orn = [r for s in secim for r in seans_r[s]]
        medyanlar.append(statistics.median(orn))
    ci = (yuzdelik(medyanlar, 2.5), yuzdelik(medyanlar, 97.5))
    return nokta, ci, len(havuz), len(seanslar)


def l2_dilim(kayitlar, seans_listesi):
    """Plan-çapalı mercek: arşiv penceresiyle kesişen planların sinyal-ertesi seansları."""
    if not os.path.exists(PLANS):
        return {"olculemedi": "state/trade_plans.jsonl yerel defteri bulunamadı"}
    planlar = []
    bozuk = 0
    with open(PLANS) as f:
        for ham in f:
            try:
                d = json.loads(ham)
                planlar.append((d.get("date"), d.get("ticker"), d.get("id"),
                                d.get("gate_verdict")))
            except json.JSONDecodeError:
                bozuk += 1
    ilk_arsiv, son_arsiv = seans_listesi[0], seans_listesi[-1]
    # sinyal-ertesi seans: plan tarihinden SONRAKİ ilk arşiv seansı
    ciftler = {}
    kesisen_plan = []
    for tarih, tk, pid, verdict in planlar:
        if not tarih or not tk:
            continue
        ertesi = next((s for s in seans_listesi if s > tarih), None)
        if ertesi is None or tarih < "2026-07-01":   # arşiv penceresi kesişimi
            continue
        # yalnız sinyal-ertesi gerçekten arşiv aralığındaysa (tarih >= ilk seansın öngünü)
        kesisen_plan.append({"id": pid, "date": tarih, "ticker": tk,
                             "gate_verdict": verdict, "sinyal_ertesi_seans": ertesi})
        ciftler[(tk, ertesi)] = True
    eslesen = [k for k in kayitlar if (k["ticker"], k["seans"]) in ciftler]
    r_l2 = [k["r"] for k in eslesen if k.get("r") is not None]
    m2_l2 = [k["m2"] for k in eslesen if k.get("m2") is not None]
    n = len(eslesen)
    sonuc = {
        "defter": PLANS, "defter_satir": len(planlar), "defter_bozuk_satir": bozuk,
        "defter_son_plan_tarihi": max((p[0] for p in planlar if p[0]), default=None),
        "arsiv_penceresi": [ilk_arsiv, son_arsiv],
        "kesisen_plan_sayisi": len(kesisen_plan),
        "uniq_ticker_seans_cifti": len(ciftler),
        "arsivde_eslesen_ticker_seans_n": n,
        "kesisen_planlar": kesisen_plan,
    }
    if n < 30:
        sonuc["istatistikler"] = None
        sonuc["istatistik_neden"] = (
            f"n={n} < 30 — kart kuralı: yalnız sayı beyanı (yerel defter 2026-07-28'de donuk, "
            f"arşiv penceresiyle kesişim doğal olarak dar)")
    else:
        sonuc["istatistikler"] = {
            "r_medyan": statistics.median(r_l2) if r_l2 else None,
            "m2_medyan": statistics.median(m2_l2) if m2_l2 else None,
            "m2_p25": yuzdelik(m2_l2, 25), "m2_p75": yuzdelik(m2_l2, 75),
            "abs_m2_medyan": statistics.median([abs(x) for x in m2_l2]) if m2_l2 else None,
            "n_r": len(r_l2), "n_m2": len(m2_l2),
        }
    return sonuc


def main():
    seanslar, ham_sayac = yukle()
    seans_listesi = sorted(seanslar)

    # kill#2 — saat dilimi, pencere kesiminden ÖNCE
    sd = saat_dilimi_dogrula(seanslar)
    with open(os.path.join(BASE, "dogrulama_saat_dilimi.json"), "w") as f:
        json.dump(sd, f, indent=1, ensure_ascii=False)
    if not sd["sonuc_utc_mi"]:
        with open(os.path.join(BASE, "sonuc.json"), "w") as f:
            json.dump({"olculemedi": "kill#2 — bar damgalarının UTC olduğu veriden doğrulanamadı",
                       "saat_dilimi": sd}, f, indent=1, ensure_ascii=False)
        print("KILL#2: saat dilimi doğrulanamadı — pencere metriği yazılmadı")
        return

    kayitlar, kenar = pencere_metrikleri(seanslar)

    # kapsam (kill#3 eşik kıyası mekanik olarak raporlanır; Ö1 OKUMASI ROL-1'İN)
    tickerlar = {k["ticker"] for k in kayitlar}
    tum_tickerlar = {tk for satirlar in seanslar.values() for tk, *_ in satirlar}
    r_seanslari = sorted({k["seans"] for k in kayitlar if k.get("r") is not None})
    kapsam = {
        "seans_sayisi_arsiv": len(seans_listesi),
        "seans_araligi": [seans_listesi[0], seans_listesi[-1]],
        "seans_sayisi_acilis_verili": sd["acilisli_seans_sayisi"],
        "seans_sayisi_r_ureten": len(r_seanslari),
        "uniq_ticker_arsiv_geneli": len(tum_tickerlar),
        "uniq_ticker_AB_penceresinde": len(tickerlar),
        "kill3_esik": {"seans_min": 15, "ticker_min": 200},
        "kill3_esik_karsilastirma_mekanik": {
            "seans_arsiv_esik_ustunde": len(seans_listesi) >= 15,
            "seans_r_ureten_esik_ustunde": len(r_seanslari) >= 15,
            "ticker_esik_ustunde": len(tickerlar) >= 200,
            "not": "mekanik kıyas — kill#3 okuması Rol-1'in",
        },
    }
    beyanlar = []
    for a in sd["acilis_verisi_olmayan_seanslar"]:
        beyanlar.append(
            f"{a['seans']}: arşiv {a['ilk_damga_dakikasi']}'te başlamış — A penceresi YOK "
            f"(r/m2 üretilmez); B penceresi kısmi kapsanabilir, ≥{MIN_BAR} barlı B satırları "
            f"kart kuralı gereği m1_B/m3_B betimleyicisine girer (kısmi-kapsam beyanı)")

    # Ö1
    nokta, ci, n_cift, n_seans = o1_bootstrap(kayitlar)

    # Ö2 (L1 evren-geneli, betimleyici)
    m2ler = [k["m2"] for k in kayitlar if k.get("m2") is not None]
    m1a = [k["m1_A"] for k in kayitlar if k.get("m1_A") is not None]
    m1b = [k["m1_B"] for k in kayitlar if k.get("m1_B") is not None]
    m3a = [k["m3_A"] for k in kayitlar if k.get("m3_A") is not None]
    m3b = [k["m3_B"] for k in kayitlar if k.get("m3_B") is not None]

    l2 = l2_dilim(kayitlar, seans_listesi)

    with open(__file__, "rb") as f:
        betik_sha = hashlib.sha256(f.read()).hexdigest()

    sonuc = {
        "kart": "EDG-2026-047", "hucre": "yakin_pencere_L1",
        "olcum_tarihi": "2026-08-23",
        "betik": "olcum.py", "betik_sha256": betik_sha,
        "veri": {"kaynak": "canlı /opt/meridian/state/bars_intraday (ssh-stdin salt-okuma, damga 2026-08-22T23:42:38Z)",
                 "toplam_satir": ham_sayac["toplam_satir"],
                 "json_bozuk_satir": ham_sayac["json_bozuk"],
                 "t_alani_eksik_satir": ham_sayac["t_eksik"]},
        "saat_dilimi_ozet": {"sonuc_utc_mi": sd["sonuc_utc_mi"],
                             "acilisli_seans": f"{sd['acilisli_seans_sayisi']}/{sd['seans_sayisi']}",
                             "sicrama_min": sd["sicrama_min"],
                             "detay": "dogrulama_saat_dilimi.json"},
        "kapsam": kapsam,
        "kenar_durumlari": kenar,
        "pencere_tanimi": {"A": "13:30-13:44 UTC", "B": "13:45-13:59 UTC",
                           "min_bar": MIN_BAR, "bar": "[başlangıç,60sn) dakika barı"},
        "O1": {
            "tanim": "Δ%menzil = medyan[(m1_B−m1_A)/m1_A] (ticker×seans havuzu); seans-kümeli eşlenik bootstrap birim=SEANS",
            "B": BOOT_B, "seed": SEED, "rng": "python random.Random (MT19937)",
            "n_cift": n_cift, "n_seans": n_seans,
            "nokta_oran": nokta, "nokta_yuzde": nokta * 100 if nokta is not None else None,
            "ci95_oran": list(ci) if ci else None,
            "ci95_yuzde": [c * 100 for c in ci] if ci else None,
            "okuma_notu": "Ö1 okuması Rol-1'in — burada yalnız sayı",
        },
        "O2_betimleyici": {
            "m2_isaretli_medyan_bps": statistics.median(m2ler) if m2ler else None,
            "m2_p25_bps": yuzdelik(m2ler, 25), "m2_p75_bps": yuzdelik(m2ler, 75),
            "abs_m2_medyan_bps": statistics.median([abs(x) for x in m2ler]) if m2ler else None,
            "n_m2": len(m2ler),
        },
        "m1_betimleyici_bps": {
            "A_medyan": statistics.median(m1a) if m1a else None, "n_A": len(m1a),
            "B_medyan": statistics.median(m1b) if m1b else None, "n_B": len(m1b),
        },
        "m3_betimleyici_seans_hacim_payi": {
            "A_medyan": statistics.median(m3a) if m3a else None,
            "B_medyan": statistics.median(m3b) if m3b else None,
        },
        "L2_plan_capali": l2,
        "beyanlar": beyanlar,
        "olculemeyenler": [],
    }
    with open(os.path.join(BASE, "sonuc.json"), "w") as f:
        json.dump(sonuc, f, indent=1, ensure_ascii=False)
    print(json.dumps({"O1_nokta_yuzde": sonuc["O1"]["nokta_yuzde"],
                      "O1_ci95_yuzde": sonuc["O1"]["ci95_yuzde"],
                      "n_cift": n_cift, "n_seans": n_seans,
                      "kapsam_ticker": kapsam["uniq_ticker_AB_penceresinde"],
                      "L2_n": l2.get("arsivde_eslesen_ticker_seans_n")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
