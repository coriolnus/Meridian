"""olcum_edg025.py — EDG-2026-025 (momentum_burst kanonik karne) ÜÇ BACAK ölçümü.

BU DOSYA HÜKÜM VERMEZ, KARTA DOKUNMAZ, ARMED_SETUPS'A DOKUNMAZ, GERÇEK STATE'E YAZMAZ.
Silahlanma kararını kartın donuk eşiğiyle Rol-1 işler; burada yalnız sayılar + ölçüt-durumları
(mekanik okumayla) üretilir. UYDURMA YASAĞI: ölçülemeyen None + neden.

--- OKUNAN (salt-okunur) ---
  * /Users/erdemozturk/AI-Trading/state/counterfactuals.jsonl — cf defterinin YEREL KOPYASI
    (mtime/sha256 künyesi sonuc.json'da). counterfactual.py İTHAL EDİLMEZ (paralel ajan);
    tüketici mantığı SATIR-ATIFLA aynalanır (N4 emsali: olcum_cf_sadakat.py:104-110):
      - counterfactual.py:247-254 `resolved_rows(entered_only=True)`:
          near_miss VARSAYILAN DIŞARIDA (satır 252-253: `if not include_near_miss:
          rows = [r for r in rows if not r.get("near_miss")]`), sonra
          `entered` süzgeci (satır 254: `[r for r in rows if r.get("entered")]`).
      - tüketiciler r_multiple None satırı da düşürür (analytics.py:103, arming.py:134'ün
        `float(... or 0.0)` yerine BURADA N4 gibi açık süzgeç: r_multiple is not None).
  * kol_taban.json / kol_taban_pk.json / kol_mb_silahli.json — replay_kol.py çıktıları
    (bacak b; sandbox koşumları, gerçek state'e yazmadılar).
  * EDG-019/EDG-025 kartları + ROADMAP/doküman satırları (bacak c, belgesel köken).

--- YÖNTEM AYNALARI (kaynak satırlarıyla) ---
  * Tarih-kümeli blok bootstrap %95 CI: olcum_cf_sadakat.py:161-183 `_cluster_bootstrap_ci`
    BİREBİR (yerine-koymalı KÜME örneklemesi, percentile 2.5/97.5, n<2 ya da küme<2 → CI None).
    Küme yasası N4 foundation ile aynı: ÇIKIŞ GÜNÜ (olcum_cf_sadakat.py:365 "cf_R − gercek_R,
    tarih-kümeli (çıkış günü)"); cf satırında çıkış günü = `resolved`, replay işleminde = ts_close.
    Duyarlılık için giriş-günü (`date`) kümelemesi de raporlanır.
  * Bileşik P&L farkı CI'ı: aynı küme yasası, TOPLAM modunda — kümeler seans günleri, değerler
    o günün P&L farkı; yeniden örneklenen K günün toplamı → toplam-fark dağılımı. (Ortalama yerine
    toplam: ölçüt "bileşik portföy P&L farkı" — success_metric (ii).)

KART EŞİKLERİ (EDG-2026-025 success_metric — ölçümden ÖNCE donmuş; buradan YALNIZ okunur):
  (i)   replay bacağı ort-R tarih-kümeli %95 CI 0-ÜSTÜNDE (ci_low > 0)
  (ii)  bileşik portföy P&L farkı negatif DEĞİL VE slot-çalma diğer kurulumların kârını CI ile
        düşürmüyor. MEKANİK OKUMA (beyanlı): ΔP&L_nokta >= 0 VE diğer-kurulum ΔP&L CI-üstü < 0
        DEĞİL (yani "düşürdüğü CI ile KURULMUŞ" değil). Yorum belirsizliği sonuc.json'da beyan
        edilir; nihai okuma Rol-1'in.
  (iii) çelişki teşhisi −0.114R'yi açıklıyor — bacak (c) bulgusu; "açıklıyor mu" HÜKMÜ Rol-1'in.
  kill#2: replay'de mb işlem < 30 → 'olculemedi' (otomatik silahlanma tetiklenmez)
  kill#3: şasi taban davranışı yeniden üretemezse ölçüm geçersiz — burada iki kanıt: (a) taban
        vs taban_pk digest eşitliği (determinizm PK, karne_tazeleme `tam_guncel_pk` emsali),
        (b) taban kolunda yalnız ARMED_SETUPS kurulumlarının işlem üretmesi.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import random
from collections import Counter, defaultdict

BURASI = pathlib.Path(__file__).resolve().parent
CF_YOLU = pathlib.Path("/Users/erdemozturk/AI-Trading/state/counterfactuals.jsonl")

BOOT_N = 20000
random.seed(20260812)

# N4 değerleri (research/olcumler/cf_cikis_sadakati_2026-08-09/sonuc.json metric_c per_setup[0])
N4_MB = {"cf_n": 1080, "cf_avg_r": 0.0921}


# ==================================================================================================
# TARİH-KÜMELİ BLOK BOOTSTRAP — olcum_cf_sadakat.py:161-183 AYNASI (+ toplam modu)
# ==================================================================================================
def _cluster_bootstrap_ci(values_by_cluster: list, n_boot: int = BOOT_N, mode: str = "mean"):
    """values_by_cluster = [[v,...],...] her küme bir liste. Kümeleri yerine-koymalı örnekle;
    mode="mean": örneklem ortalaması (N4 birebir) · mode="sum": örneklem toplamı (P&L farkı)."""
    flat = [v for c in values_by_cluster for v in c]
    n = len(flat)
    if n < 2 or len(values_by_cluster) < 2:
        deger = (sum(flat) / n if (n and mode == "mean") else (sum(flat) if n else None))
        return {"mean" if mode == "mean" else "toplam": deger,
                "ci_low": None, "ci_high": None, "n": n, "n_cluster": len(values_by_cluster),
                "ci_excludes_0": None,
                "neden": "n<2 ya da küme<2 — aralık kurulamadı (olcum_cf_sadakat.py:166-170 yasası)"}
    K = len(values_by_cluster)
    stats = []
    for _ in range(n_boot):
        sample = []
        for _ in range(K):
            sample.extend(values_by_cluster[random.randrange(K)])
        if mode == "mean":
            stats.append(sum(sample) / len(sample) if sample else 0.0)
        else:
            stats.append(sum(sample))
    stats.sort()
    lo = stats[int(0.025 * n_boot)]
    hi = stats[int(0.975 * n_boot) - 1]
    out_key = "mean" if mode == "mean" else "toplam"
    nokta = (sum(flat) / n) if mode == "mean" else sum(flat)
    return {out_key: round(nokta, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "n": n, "n_cluster": K, "ci_excludes_0": bool(lo > 0 or hi < 0)}


def _kumele(rows, anahtar_fn, deger_fn):
    by = defaultdict(list)
    for r in rows:
        by[anahtar_fn(r)].append(deger_fn(r))
    return list(by.values())


# ==================================================================================================
# BACAK (a) — CF KARNE
# ==================================================================================================
def bacak_a() -> dict:
    ham = CF_YOLU.read_bytes()
    kunye = {"yol": str(CF_YOLU), "sha256_16": hashlib.sha256(ham).hexdigest()[:16],
             "mtime": dt.datetime.fromtimestamp(CF_YOLU.stat().st_mtime).isoformat(timespec="seconds"),
             "n_satir": ham.count(b"\n")}
    rows = [json.loads(l) for l in ham.decode().splitlines() if l.strip()]

    # TÜKETİCİ AYNASI — counterfactual.py:247-254 (near_miss dışarıda, entered süzgeci) + N4'ün
    # r_multiple None düşürmesi (olcum_cf_sadakat.py:109-110 birebir).
    cf_ent = [r for r in rows
              if r.get("entered") and not r.get("near_miss") and r.get("r_multiple") is not None]
    mb = [r for r in cf_ent if r.get("setup") == "momentum_burst"]
    mb_nm_sayisi = sum(1 for r in rows if r.get("setup") == "momentum_burst"
                       and r.get("entered") and r.get("near_miss"))

    rs = [float(r["r_multiple"]) for r in mb]
    rs_s = sorted(rs)
    n = len(rs)

    def q(p):
        return round(rs_s[min(n - 1, int(p * n))], 3) if n else None

    ci_cikis = _cluster_bootstrap_ci(_kumele(mb, lambda r: r.get("resolved"),
                                             lambda r: float(r["r_multiple"])))
    ci_giris = _cluster_bootstrap_ci(_kumele(mb, lambda r: r.get("date"),
                                             lambda r: float(r["r_multiple"])))

    yil = defaultdict(list)
    for r in mb:
        yil[str(r.get("date", "????"))[:4]].append(float(r["r_multiple"]))

    avg = round(sum(rs) / n, 4) if n else None
    return {
        "cf_defteri_kunye": kunye,
        "tuketici_evren_aynasi": "counterfactual.py:247-254 (near_miss dışarıda + entered) "
                                 "+ r_multiple is not None (olcum_cf_sadakat.py:109-110)",
        "n_cf_toplam": len(rows),
        "n_tuketici_gorunur": len(cf_ent),
        "mb": {
            "n": n, "avg_r": avg,
            "median_r": q(0.50), "p10": q(0.10), "p90": q(0.90),
            "win_rate": round(sum(1 for x in rs if x > 0) / n, 4) if n else None,
            "toplam_r": round(sum(rs), 2),
            "near_miss_entered_mb_satiri": mb_nm_sayisi,
            "not_near_miss": ("mb'de near_miss-entered satır sayısı 0 — N4 dışlama kuralı mb "
                              "örneklemini DEĞİŞTİRMİYOR (evren farkı −0.114'ü near_miss ile "
                              "açıklayamaz)") if mb_nm_sayisi == 0 else None,
            "ci95_tarih_kumeli_cikis_gunu": ci_cikis,      # birincil (N4 çıkış-günü yasası)
            "ci95_tarih_kumeli_giris_gunu": ci_giris,      # duyarlılık
            "exit_reason_dagilimi": dict(Counter(r.get("exit_reason") for r in mb).most_common()),
            "yil_bazinda": {y: {"n": len(v), "avg_r": round(sum(v) / len(v), 4)}
                            for y, v in sorted(yil.items())},
        },
        "n4_tutarlilik": {
            "n4_cf_n": N4_MB["cf_n"], "n4_cf_avg_r": N4_MB["cf_avg_r"],
            "bu_olcum_n": n, "bu_olcum_avg_r": avg,
            "birebir": bool(n == N4_MB["cf_n"] and avg is not None
                            and abs(avg - N4_MB["cf_avg_r"]) < 5e-5),
        },
    }


# ==================================================================================================
# BACAK (b) — REPLAY KARNE (kol JSON'larından)
# ==================================================================================================
def _kol(ad: str) -> dict:
    return json.loads((BURASI / f"kol_{ad}.json").read_text())


def _gunluk_pnl_fark(eq_a: list, eq_b: list) -> list:
    """İki özkaynak eğrisinden gün-başına P&L farkı [(gun, fark$)]. Gün kümesi birleşim;
    eksik günde ilgili eğrinin son bilinen değeri taşınır (artım 0)."""
    def _artimlar(eq):
        art = {}
        onceki = None
        for g, v in eq:
            art[g] = (float(v) - onceki) if onceki is not None else 0.0
            onceki = float(v)
        return art
    aa, bb = _artimlar(eq_a), _artimlar(eq_b)
    gunler = sorted(set(aa) | set(bb))
    return [(g, aa.get(g, 0.0) - bb.get(g, 0.0)) for g in gunler]


def bacak_b() -> dict:
    taban, pk, mb_kol = _kol("taban"), _kol("taban_pk"), _kol("mb_silahli")

    # ---- kill#3 şasi doğrulaması ----
    determinizm = {
        "trade_digest_esit": taban["trade_digest"] == pk["trade_digest"],
        "equity_digest_esit": taban["equity_digest"] == pk["equity_digest"],
        "taban_trade_digest": taban["trade_digest"][:16], "pk_trade_digest": pk["trade_digest"][:16],
    }
    taban_setuplar = sorted({t.get("setup") for t in taban["trades"]})
    silahli_disi = [s for s in taban_setuplar if s not in taban["armed_setups_repo"]]
    sasi = {
        "determinizm_pk": determinizm,
        "taban_setup_kumesi": taban_setuplar,
        "taban_yalniz_armed_setups": not silahli_disi,
        "armed_setups_repo": taban["armed_setups_repo"],
        "gecerli": bool(determinizm["trade_digest_esit"] and determinizm["equity_digest_esit"]
                        and not silahli_disi),
        "not": ("determinizm ikizi + silahlı-küme disiplini. 2026-08-03 karne rakamlarıyla bire bir "
                "kıyas MÜMKÜN DEĞİL ve beklenmez: o karne walk_forward geometrisiyle ve "
                "exhaustion_hammer SİLAHSIZKEN koştu (silahlanma 2026-08-11, strategy.py:1002-1009); "
                "bu beyan bir bulgu, bir başarısızlık değil."),
    }

    mb_trades = [t for t in mb_kol["trades"] if t.get("setup") == "momentum_burst"]
    diger_mbkol = [t for t in mb_kol["trades"] if t.get("setup") != "momentum_burst"]
    n_mb = len(mb_trades)

    # ---- mb işlemlerinin GERÇEK-yasalı R'si ----
    mb_r = [float(t["r_multiple"]) for t in mb_trades if t.get("r_multiple") is not None]
    ci_mb = _cluster_bootstrap_ci(_kumele(
        [t for t in mb_trades if t.get("r_multiple") is not None],
        lambda t: str(t.get("ts_close"))[:10], lambda t: float(t["r_multiple"])))

    # ---- bileşik portföy etkisi ----
    pnl = lambda ts: round(sum(float(t.get("pnl_dollars") or 0.0) for t in ts), 2)
    eq_son = lambda k: (k["equity"][-1][1] if k["equity"] else None)
    fark_gunluk = _gunluk_pnl_fark(mb_kol["equity"], taban["equity"])
    ci_bilesik = _cluster_bootstrap_ci([[f] for _, f in fark_gunluk], mode="sum")

    # slot-çalma: diğer kurulumların GERÇEKLEŞEN P&L'i iki kolda, kapanış gününe kümeli fark
    def _gun_pnl(ts):
        by = defaultdict(float)
        for t in ts:
            if t.get("pnl_dollars") is not None:
                by[str(t.get("ts_close"))[:10]] += float(t["pnl_dollars"])
        return by
    g_mb, g_tb = _gun_pnl(diger_mbkol), _gun_pnl(taban["trades"])
    gunler = sorted(set(g_mb) | set(g_tb))
    diger_fark = [[g_mb.get(g, 0.0) - g_tb.get(g, 0.0)] for g in gunler]
    ci_diger = _cluster_bootstrap_ci(diger_fark, mode="sum")

    def _setup_ozet(ts):
        by = defaultdict(lambda: {"n": 0, "pnl": 0.0, "sum_r": 0.0})
        for t in ts:
            b = by[t.get("setup")]
            b["n"] += 1
            b["pnl"] += float(t.get("pnl_dollars") or 0.0)
            if t.get("r_multiple") is not None:
                b["sum_r"] += float(t["r_multiple"])
        return {s: {"n": v["n"], "pnl": round(v["pnl"], 2),
                    "avg_r": round(v["sum_r"] / v["n"], 4) if v["n"] else None}
                for s, v in sorted(by.items())}

    out = {
        "sasi_dogrulamasi_kill3": sasi,
        "pencere": taban["pencere"],
        "takvim": {"ilk": taban["calendar_ilk"], "son": taban["calendar_son"]},
        "n_sembol": taban["n_sembol"],
        "koslar": {k["kol"]: {"n_trades": k["n_trades"], "n_plans": k["n_plans"],
                              "sure_sn": k["sure_sn"], "son_equity": eq_son(k),
                              "toplam_pnl": pnl(k["trades"]),
                              "entry_rejects": k["entry_rejects"]}
                   for k in (taban, pk, mb_kol)},
        "mb_islemleri": {
            "n": n_mb,
            "kill2_esik30": ("olculemedi — mb işlem sayısı <30, otomatik silahlanma TETİKLENMEZ "
                             "(kart kill#2)") if n_mb < 30 else "esik_ustu",
            "avg_r": round(sum(mb_r) / len(mb_r), 4) if mb_r else None,
            "win_rate": round(sum(1 for x in mb_r if x > 0) / len(mb_r), 4) if mb_r else None,
            "toplam_pnl": pnl(mb_trades),
            "ci95_tarih_kumeli_cikis_gunu": ci_mb,
            "exit_reason_dagilimi": dict(Counter(t.get("exit_reason") for t in mb_trades).most_common()),
            "yil_bazinda": {y: {"n": len(v), "avg_r": round(sum(v) / len(v), 4)}
                            for y, v in sorted(
                                ((y, [float(t["r_multiple"]) for t in mb_trades
                                      if str(t.get("ts_open"))[:4] == y and t.get("r_multiple") is not None])
                                 for y in sorted({str(t.get("ts_open"))[:4] for t in mb_trades})),
                            ) if v},
        },
        "bilesik_portfoy": {
            "son_equity_taban": eq_son(taban), "son_equity_mb": eq_son(mb_kol),
            "delta_son_equity": (round(eq_son(mb_kol) - eq_son(taban), 2)
                                 if eq_son(mb_kol) is not None and eq_son(taban) is not None else None),
            "delta_toplam_pnl_islemlerden": round(pnl(mb_kol["trades"]) - pnl(taban["trades"]), 2),
            "ci95_gun_kumeli_toplam_fark": ci_bilesik,
            "n_trades_taban": taban["n_trades"], "n_trades_mb_kolu": mb_kol["n_trades"],
        },
        "slot_calma": {
            "diger_kurulumlar_pnl_taban": pnl(taban["trades"]),
            "diger_kurulumlar_pnl_mb_kolunda": pnl(diger_mbkol),
            "delta_diger_pnl": round(pnl(diger_mbkol) - pnl(taban["trades"]), 2),
            "n_diger_taban": taban["n_trades"], "n_diger_mb_kolunda": len(diger_mbkol),
            "ci95_gun_kumeli_toplam_fark": ci_diger,
            "setup_bazinda_taban": _setup_ozet(taban["trades"]),
            "setup_bazinda_mb_kolu": _setup_ozet(mb_kol["trades"]),
        },
    }
    return out


# ==================================================================================================
# BACAK (c) — ÇELİŞKİ TEŞHİSİ (sayısal tarama kısmı; belgesel köken sonuc'ta)
# ==================================================================================================
def bacak_c_sayisal(mb_rows: list | None = None) -> dict:
    """−0.114'ü cf defterinden üretmeye çalış: standart dilimler + pencere taraması.
    BULURSA 'aday-açıklama' der (kanıt değil); BULAMAZSA açıkça 'dilim bulunamadı' der."""
    if mb_rows is None:
        rows = [json.loads(l) for l in CF_YOLU.read_text().splitlines() if l.strip()]
        mb_rows = [r for r in rows if r.get("setup") == "momentum_burst"
                   and r.get("entered") and not r.get("near_miss")
                   and r.get("r_multiple") is not None]
    mb_rows = sorted(mb_rows, key=lambda r: r.get("date", ""))
    rs = [(r["date"], float(r["r_multiple"])) for r in mb_rows]
    HEDEF = -0.114
    TOL = 0.0005          # ≈ üçüncü haneye yuvarlama yarıçapı
    adaylar = []

    # (1) kuyruk pencereleri: son k satır (k=5..1080)
    s = 0.0
    kuyruk = []
    for i, (_, r) in enumerate(reversed(rs), 1):
        s += r
        kuyruk.append(s / i)
    for k, m in enumerate(kuyruk, 1):
        if k >= 5 and abs(m - HEDEF) <= TOL:
            adaylar.append({"dilim": f"son {k} girilmiş mb satırı", "n": k, "avg_r": round(m, 4)})

    # (2) takvim dilimleri: yıl, yarıyıl, çeyrek
    def _avg(sel):
        v = [r for d, r in rs if sel(d)]
        return (len(v), round(sum(v) / len(v), 4)) if v else (0, None)
    dilimler = {}
    for y in sorted({d[:4] for d, _ in rs}):
        dilimler[y] = _avg(lambda d, y=y: d[:4] == y)
        for yy, aralik in (("H1", ("01", "06")), ("H2", ("07", "12"))):
            dilimler[f"{y}-{yy}"] = _avg(lambda d, y=y, a=aralik: d[:4] == y and a[0] <= d[5:7] <= a[1])
        for q, aralik in (("Q1", ("01", "03")), ("Q2", ("04", "06")),
                          ("Q3", ("07", "09")), ("Q4", ("10", "12"))):
            dilimler[f"{y}-{q}"] = _avg(lambda d, y=y, a=aralik: d[:4] == y and a[0] <= d[5:7] <= a[1])
    for ad, (nn, m) in dilimler.items():
        if m is not None and nn >= 5 and abs(m - HEDEF) <= TOL:
            adaylar.append({"dilim": ad, "n": nn, "avg_r": m})

    son37 = kuyruk[36] if len(kuyruk) >= 37 else None
    return {
        "hedef": HEDEF, "tolerans": TOL,
        "taranan": "kuyruk pencereleri (son k, k=5..n) + yıl/yarıyıl/çeyrek dilimleri (n>=5)",
        "aday_dilimler": adaylar or None,
        "bulundu": bool(adaylar),
        "yakin_pencere_ornegi": {"son_37_giris_avg_r": round(son37, 4) if son37 is not None else None,
                                 "not": "yakın pencerede mb GERÇEKTEN negatif (işaret çevrilir) ama "
                                        "−0.114'ün kendisi bu taramalardan çıkmadıysa sayısal köken "
                                        "kurulamamıştır"},
        "takvim_dilim_ozeti": {k: {"n": v[0], "avg_r": v[1]} for k, v in dilimler.items() if v[0]},
    }


if __name__ == "__main__":
    a = bacak_a()
    c_say = bacak_c_sayisal()
    b = bacak_b()
    (BURASI / "ara_sonuc.json").write_text(json.dumps(
        {"bacak_a": a, "bacak_b": b, "bacak_c_sayisal": c_say}, ensure_ascii=False, indent=1))
    print("ara_sonuc.json yazıldı")
