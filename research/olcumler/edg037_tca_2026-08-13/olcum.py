"""EDG-2026-037 · TCA — GERÇEK FRİKSİYON. Ölçüm modülü (YEREL; canlıya dokunmaz).

GİRDİ  : canli_ham.json   (bkz. canli_cek.py — canlıdan SALT-OKUMA çekim)
         ../edg032_final_paket_2026-08-12/islemler_cmb.json  (benimsenen C+mb defteri, 885 işlem)
         ../edg032_final_paket_2026-08-12/state_cmb/bars/*.csv (o koşumun KENDİ bar arşivi)
ÇIKTI  : sonuc.json

DÖRT ÖLÇÜM (kart features_asof):
  (a) GERÇEKLEŞEN SLİPAJ — bacak AYRI, bps; payda MERDİVENİ açıkça beyanlı
  (b) KOMİSYON/ÜCRET     — broker'ın GERÇEK ücret kayıtları (activities FEE) vs modelin varsayımı
  (c) REPLAY VARSAYIMI   — motorun kendi friksiyon modeli, kod alıntısıyla
  (d) FARK + PF ETKİSİ   — EDG-032'nin 885 işlemi friksiyon-düzeltilirse PF ne olur

İKİ KIYAS TABANI, İKİSİ DE RAPORLANIR (karıştırmak yanlış cümle üretir):
  * tetiğe göre  : plan `entry_trigger` ↔ gerçek dolum. GAP'İ İÇERİR — gece boşluğu bir icra
                   maliyeti DEĞİL, giriş yasasının konusudur; iç motor da aynı boşluğu öder.
  * resmî AÇILIŞA göre : replay'in KENDİ referans noktası (`base_fill = next_open × (1+slip)`).
                   Gap iki tarafta da sadeleşir → FRİKSİYONU İZOLE EDEN taban budur ve
                   "gerçek − varsayılan" farkı bu tabandan okunur.

UYDURMA YASAĞI: ölçülemeyen her kalem None + neden. n<10 eşleşmede kart kill'i ateşlenir ve
slipaj 'olculemedi' damgasıyla döner — sayılar BETİMLEYİCİ girdi olarak yine yazılır, hüküm YOK.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics as st
import datetime as dt

BURASI = os.path.dirname(os.path.abspath(__file__))
HAM = os.path.join(BURASI, "canli_ham.json")
EDG032 = os.path.abspath(os.path.join(BURASI, "..", "edg032_final_paket_2026-08-12"))
ISLEMLER_032 = os.path.join(EDG032, "islemler_cmb.json")
BARS_032 = os.path.join(EDG032, "state_cmb", "bars")

MIN_CIFT = 10                  # kart kill#1: eşleşen plan↔dolum çifti bu sayının altındaysa 'olculemedi'
BOOT_N = 20000
BOOT_SEED = 20260813           # tarih-tohumlu, DONUK (EDG-022/024 deseni)

# --- replay'in VARSAYDIĞI friksiyon (kod alıntıları; kart kill#2: okunamazsa kıyas YAPILMAZ) ---
REPLAY_ALINTI = {
    "giris": "meridian/broker.py:515 — `base_fill = next_open * (1.0 + self.slip)`  # long: pay up (fixed component)",
    "cikis": "meridian/broker.py:669 — `exit_fill = raw_exit * (1.0 - self.slip)`  # long exit: receive less",
    "kismi_cikis": "meridian/broker.py:638 — `fill = level * (1.0 - self.slip)`  # scale-out (C+mb'de frac=0.0 → ölü yol)",
    "slip_tanimi": "meridian/broker.py:414 — `self.slip = slippage_bps / 10000.0`",
    "komisyon_tanimi": "meridian/broker.py:415 — `self.commission = commission_per_share`",
    "likidite_etkisi": "meridian/broker.py:528 — `fill = base_fill * (1.0 + IMPACT_COEF * participation)`; "
                       "IMPACT_COEF=0.10 (:19), ADV_CAP_PCT=0.02 (:18) → katılım tavanda bile ek etki ≤ 20 bps",
    "costs_tanimi": "meridian/broker.py:674 — `costs = pos.entry_slippage_cost + exit_slip_dollars + "
                    "exit_commission   # informational total friction`",
    "net_uyarisi": "meridian/analytics.py:2079-2084 — `pnl_dollars` ZATEN NET; `costs` bilgi amaçlı, "
                   "friksiyon İKİ KEZ kesilmez",
}


# =================================================================================================
# yardımcılar
# =================================================================================================
def bps(gercek: float, taban: float) -> float | None:
    """(gerçek − taban)/taban, bps. İşaret ALEYHTE=+ (long girişte pahalıya doldu)."""
    if taban is None or gercek is None or float(taban) <= 0:
        return None
    return 10_000.0 * (float(gercek) - float(taban)) / float(taban)


def betim(xs: list[float], agirlik: list[float] | None = None) -> dict:
    """n / medyan / ortalama / p90 / min / max (+ ağırlıklı ortalama). n=0 → hepsi None + neden."""
    xs = [float(x) for x in xs if x is not None]
    if not xs:
        return {"n": 0, "medyan": None, "ortalama": None, "p90": None, "min": None, "max": None,
                "agirlikli_ortalama": None, "neden": "örneklem boş — betimleyici üretilmedi"}
    s = sorted(xs)
    # p90: doğrusal enterpolasyon; n<10'da p90 fiilen MAKSİMUMdur ve bu beyan edilir
    k = 0.90 * (len(s) - 1)
    lo, hi = math.floor(k), math.ceil(k)
    p90 = s[lo] if lo == hi else s[lo] + (k - lo) * (s[hi] - s[lo])
    out = {"n": len(s), "medyan": round(st.median(s), 3), "ortalama": round(sum(s) / len(s), 3),
           "p90": round(p90, 3), "min": round(s[0], 3), "max": round(s[-1], 3),
           "agirlikli_ortalama": None}
    if len(s) < 10:
        out["p90_serhi"] = f"n={len(s)} — p90 pratikte maksimuma eşittir, dağılım kuyruğu ÖLÇÜLMEDİ"
    if agirlik:
        w = [float(a) for a in agirlik]
        if len(w) == len(xs) and sum(w) > 0:
            out["agirlikli_ortalama"] = round(sum(x * a for x, a in zip(xs, w)) / sum(w), 3)
            out["agirlik_tabani"] = "notional (adet × referans fiyat)"
    return out


def t_ci(xs: list[float], guven: float = 0.95) -> dict | None:
    """Student-t %95 CI. n<2 → None (tek gözlemden CI uydurulmaz)."""
    xs = [float(x) for x in xs if x is not None]
    n = len(xs)
    if n < 2:
        return None
    ort = sum(xs) / n
    sd = st.stdev(xs)
    se = sd / math.sqrt(n)
    # t tablosu (çift kuyruk %95) — küçük n için; n>30'da normale yaklaşır
    T = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306,
         10: 2.262, 15: 2.145, 20: 2.093, 30: 2.045}
    sd_ = n - 1
    t = T.get(sd_) or (2.045 if sd_ > 30 else T[min(T, key=lambda k: abs(k - sd_))])
    return {"ortalama": round(ort, 3), "sd": round(sd, 3), "se": round(se, 3), "t": t,
            "lo": round(ort - t * se, 3), "hi": round(ort + t * se, 3),
            "sifiri_iceriyor": (ort - t * se) <= 0 <= (ort + t * se)}


def bootstrap_ci(xs: list[float], n_iter: int = BOOT_N, seed: int = BOOT_SEED) -> dict | None:
    """Yüzdelik bootstrap CI (ortalama). n<2 → None."""
    xs = [float(x) for x in xs if x is not None]
    if len(xs) < 2:
        return None
    import random
    rng = random.Random(seed)
    n = len(xs)
    ort = []
    for _ in range(n_iter):
        ort.append(sum(xs[rng.randrange(n)] for _ in range(n)) / n)
    ort.sort()
    return {"lo": round(ort[int(0.025 * n_iter)], 3), "hi": round(ort[int(0.975 * n_iter)], 3),
            "orta": round(ort[n_iter // 2], 3), "n_iter": n_iter, "seed": seed,
            "serh": "n<10'da bootstrap yalnız GÖZLENEN dört değeri yeniden örnekler — "
                    "dağılım varsayımı yok ama bilgi de yok; genişlik betimleyicidir" if len(xs) < 10 else None}


def isaret_testi(xs: list[float]) -> dict:
    """Tek-kuyruk binom işaret testi: 'hepsi aleyhte mi?' — büyüklükten BAĞIMSIZ tutarlılık."""
    xs = [float(x) for x in xs if x is not None]
    n = len(xs)
    k = sum(1 for x in xs if x > 0)
    if n == 0:
        return {"n": 0, "aleyhte": 0, "p_tek_kuyruk": None, "neden": "örneklem boş"}
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return {"n": n, "aleyhte": k, "lehte": n - k, "p_tek_kuyruk": round(p, 5),
            "yorum": "H0: dolumun tabanın üstünde/altında olması eşit olasılıklı (p=0,5)"}


def sha16(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return None


# =================================================================================================
# (a) GERÇEKLEŞEN SLİPAJ
# =================================================================================================
def slipaj_olc(ham: dict) -> dict:
    ee = ham.get("entry_execution") or {}
    satirlar = ee.get("satirlar") or []
    ayna = [r for r in satirlar if r.get("motor") == "ayna"]
    ic = [r for r in satirlar if r.get("motor") == "ic"]

    alp = (ham.get("alpaca") or {})
    emirler = ((alp.get("orders") or {}).get("satirlar") or [])
    fills = (((alp.get("activities") or {}).get("FILL") or {}).get("kayitlar") or [])

    # --- MOTOR emri mi? İKİ KEMER (alpaca.is_engine_order + ebeveyn bağı):
    #   (1) coid motor önekiyle başlıyor (`P-…`, `alpaca.ENGINE_COID_PREFIX`) — üst düzey emirler;
    #   (2) ebeveyni motor emri olan BACAK — bracket'ın TP/SL bacaklarının coid'i Alpaca UUID'sidir,
    #       önek TAŞIMAZ. Yalnız (1) kullanmak çıkış bacağının paydasını sessizce eksiltirdi.
    onek_motor = {o["id"] for o in emirler if str(o.get("client_order_id") or "").startswith("P-")}
    motor_emir_id = set(onek_motor)
    for _ in range(4):                                   # bacak zinciri için sabit nokta
        for o in emirler:
            if o.get("_parent_id") in motor_emir_id:
                motor_emir_id.add(o["id"])
    motor_emir = [o for o in emirler if o["id"] in motor_emir_id]
    dis_emir = [o for o in emirler if o["id"] not in motor_emir_id]

    motor_fill = [f for f in fills if f.get("order_id") in motor_emir_id]
    dis_fill = [f for f in fills if f.get("order_id") not in motor_emir_id]

    # --- resmî açılış tabanı: E2 icra defterinin AYNA satırından (broker'dan bağımsız kaynak)
    acilis = {r["ticker"]: r.get("resmi_acilis") for r in ayna if r.get("resmi_acilis") is not None}
    tetik = {r["ticker"]: r.get("entry_trigger") for r in ayna if r.get("entry_trigger") is not None}

    # ============ EMİR DÜZEYİ (giriş bacağı) ============
    emir_satir = []
    for r in ayna:
        t, fill = r["ticker"], r.get("fill")
        a, tg = acilis.get(t), tetik.get(t)
        # AYNI PLANIN iç-motor dolumu = replay'in VARSAYDIĞI friksiyon. Eşleşme `plan_id` üzerinden:
        # iki motorun `date` alanı BİLEREK farklıdır (ayna gönderim gününü, iç motor dolum gününü
        # taşır) — tarihle eşleştirmek dört çiftin dördünü de sessizce kaybederdi.
        ic_r = next((x for x in ic if x.get("plan_id") == r.get("plan_id")), None)
        emir_satir.append({
            "ticker": t, "plan_id": r.get("plan_id"), "date": r.get("date"),
            "qty_ayna": r.get("qty"), "fill_gercek": fill,
            "resmi_acilis": a, "entry_trigger": tg,
            "limit": r.get("limit"), "gap_at_submit": r.get("gap_at_submit"),
            "bps_vs_acilis_GERCEK": None if bps(fill, a) is None else round(bps(fill, a), 3),
            "bps_vs_tetik_GERCEK": None if bps(fill, tg) is None else round(bps(fill, tg), 3),
            "fill_ic_motor": (ic_r or {}).get("fill"),
            "qty_ic": (ic_r or {}).get("qty"),
            "bps_vs_acilis_MODEL": None if ic_r is None or bps(ic_r.get("fill"), a) is None
                                   else round(bps(ic_r.get("fill"), a), 3),
            "notional_gercek": (None if fill is None or r.get("qty") is None
                                else round(float(fill) * float(r["qty"]), 2)),
        })
    for s in emir_satir:
        g, m = s["bps_vs_acilis_GERCEK"], s["bps_vs_acilis_MODEL"]
        s["fark_bps"] = None if (g is None or m is None) else round(g - m, 3)
        s["slipaj_dolar_GERCEK"] = (None if s["fill_gercek"] is None or s["resmi_acilis"] is None
                                    or s["qty_ayna"] is None else
                                    round((float(s["fill_gercek"]) - float(s["resmi_acilis"]))
                                          * float(s["qty_ayna"]), 4))
        s["slipaj_dolar_MODEL_ayni_adet"] = (
            None if s["bps_vs_acilis_MODEL"] is None or s["resmi_acilis"] is None
            or s["qty_ayna"] is None else
            round(s["bps_vs_acilis_MODEL"] / 1e4 * float(s["resmi_acilis"]) * float(s["qty_ayna"]), 4))

    # ============ DOLUM-OLAYI DÜZEYİ (giriş bacağı) ============
    coid_by_id = {o["id"]: o.get("client_order_id") for o in emirler}
    sym_acilis_yok = 0
    olay_satir = []
    for f in sorted(motor_fill, key=lambda x: str(x.get("transaction_time"))):
        t = f.get("symbol")
        a = acilis.get(t)
        if a is None:
            sym_acilis_yok += 1
        olay_satir.append({
            "ts": f.get("transaction_time"), "ticker": t, "tip": f.get("type"),
            "side": f.get("side"), "qty": f.get("qty"), "price": f.get("price"),
            "coid": coid_by_id.get(f.get("order_id")),
            "resmi_acilis": a,
            "bps_vs_acilis": None if a is None else round(bps(float(f["price"]), a), 3),
        })

    giris_emir_bps = [s["bps_vs_acilis_GERCEK"] for s in emir_satir if s["bps_vs_acilis_GERCEK"] is not None]
    giris_emir_w = [float(s["qty_ayna"]) * float(s["resmi_acilis"]) for s in emir_satir
                    if s["bps_vs_acilis_GERCEK"] is not None]
    fark_bps = [s["fark_bps"] for s in emir_satir if s["fark_bps"] is not None]
    fark_w = [float(s["qty_ayna"]) * float(s["resmi_acilis"]) for s in emir_satir if s["fark_bps"] is not None]
    olay_bps = [o["bps_vs_acilis"] for o in olay_satir if o["bps_vs_acilis"] is not None]
    olay_w = [float(o["qty"]) for o in olay_satir if o["bps_vs_acilis"] is not None]
    tetik_bps = [s["bps_vs_tetik_GERCEK"] for s in emir_satir if s["bps_vs_tetik_GERCEK"] is not None]

    # ============ ÇIKIŞ BACAĞI ============
    satis_emir = [o for o in motor_emir if str(o.get("side")) == "sell"]
    satis_dolan = [o for o in satis_emir if float(o.get("filled_qty") or 0) > 0]
    satis_fill = [f for f in motor_fill if str(f.get("side")) == "sell"]

    n_cift = len(giris_emir_bps)
    kill1 = n_cift < MIN_CIFT

    return {
        "payda_merdiveni": {
            "1_kapanmis_islem": {
                "n_toplam": (ham.get("trades") or {}).get("n"),
                "kaynak_dagilim": (ham.get("trades") or {}).get("kaynak_dagilim"),
                "live_paper_n": ((ham.get("trades") or {}).get("kaynak_dagilim") or {}).get("live_paper"),
                "gercek_dolumlu_n": (ham.get("trades") or {}).get("alpaca_fill_price_dolu"),
                "hüküm": "KULLANILAMAZ — `alpaca_fill_price` 0/97. İki `live_paper` satırının "
                         "(ALL, VLO) aynada KARŞILIĞI YOK: mirror_orders'da ve Alpaca emir "
                         "geçmişinde bu iki sembol hiç geçmiyor → fiyatları İÇ SİMÜLASYONDAN. "
                         "Kapanmış-işlem paydası TCA'ya girmez (kart kill#3).",
            },
            "2_emir_duzeyi_GECERLI_PAYDA": {
                "motor_emri_toplam": len(motor_emir),
                "motor_emri_dolan": len([o for o in motor_emir if float(o.get("filled_qty") or 0) > 0]),
                "giris_bacagi_dolan": len([o for o in motor_emir
                                           if str(o.get("side")) == "buy"
                                           and float(o.get("filled_qty") or 0) > 0]),
                "cikis_bacagi_dolan": len(satis_dolan),
                "acik_pozisyon_girisleri_dahil": True,
                "beyan": "PAYDA GENİŞLETİLDİ (kart features_asof izniyle): kapanmış işlem yerine "
                         "GÖNDERİLEN/DOLAN EMİR. Açık 4 pozisyonun (NUE/EMR/BKNG/AMGN) GİRİŞ "
                         "bacakları paydaya DAHİL; bu dört isim hâlâ açık olduğu için çıkış "
                         "bacakları henüz hiç dolmadı.",
            },
            "3_dolum_olayi_duzeyi": {
                "motor_dolum_olayi": len(motor_fill),
                "kismi": len([f for f in motor_fill if f.get("type") == "partial_fill"]),
                "tam": len([f for f in motor_fill if f.get("type") == "fill"]),
                "beyan": "Alpaca `activities?activity_types=FILL` — bir emrin PARÇA dolumları "
                         "ayrı satırdır; kısmi-dolum fiyat dağılımı yalnız burada görünür.",
            },
            "dislanan": {
                "replay_seed_islem": ((ham.get("trades") or {}).get("kaynak_dagilim") or {}).get("replay_seed"),
                "replay_seed_neden": "simüle dolum — bu kartın ölçtüğü şeyin tam tersi (kart kill#3)",
                "motor_disi_emir": len(dis_emir),
                "motor_disi_dolum": len(dis_fill),
                "motor_disi_neden": "operatörün kendi NVDA alımı + F üzerinde tatbikat/smoke emirleri "
                                    "(client_order_id plan kimliği DEĞİL) — motorun icrası sayılmaz",
            },
        },
        "giris_bacagi": {
            "emir_duzeyi": {
                "satirlar": emir_satir,
                "GERCEK_vs_resmi_acilis_bps": {**betim(giris_emir_bps, giris_emir_w),
                                               "t_ci95": t_ci(giris_emir_bps),
                                               "bootstrap_ci95": bootstrap_ci(giris_emir_bps),
                                               "isaret_testi": isaret_testi(giris_emir_bps)},
                "GERCEK_vs_plan_tetigi_bps": {**betim(tetik_bps),
                                              "serh": "GAP DAHİL — dördünde de `gap_at_submit=true`; "
                                                      "gece boşluğu icra maliyeti değildir ve iç motor "
                                                      "da aynı boşluğu öder. Friksiyon kıyası için "
                                                      "AÇILIŞ tabanı kullanılır."},
                "FARK_gercek_eksi_model_bps": {**betim(fark_bps, fark_w),
                                               "t_ci95": t_ci(fark_bps),
                                               "bootstrap_ci95": bootstrap_ci(fark_bps),
                                               "isaret_testi": isaret_testi(fark_bps)},
                "dolar": {
                    "slipaj_GERCEK_toplam": round(sum(s["slipaj_dolar_GERCEK"] for s in emir_satir
                                                      if s["slipaj_dolar_GERCEK"] is not None), 4),
                    "slipaj_MODEL_ayni_adet_toplam": round(
                        sum(s["slipaj_dolar_MODEL_ayni_adet"] for s in emir_satir
                            if s["slipaj_dolar_MODEL_ayni_adet"] is not None), 4),
                    "notional_acilista": round(sum(float(s["qty_ayna"]) * float(s["resmi_acilis"])
                                                   for s in emir_satir
                                                   if s["qty_ayna"] and s["resmi_acilis"]), 2),
                },
            },
            "dolum_olayi_duzeyi": {
                "satirlar": olay_satir,
                "GERCEK_vs_resmi_acilis_bps": {
                    **betim(olay_bps, olay_w),
                    "t_ci95": t_ci(olay_bps),
                    "isaret_testi": isaret_testi(olay_bps),
                    "KUMELENME_UYARISI": "Bu 9 gözlem BAĞIMSIZ DEĞİLDİR: 4 ebeveyn emir, 4 sembol, "
                                         "TEK seans (2026-08-06 13:30-13:33Z = açılışın ilk 3 "
                                         "dakikası). t-CI'nin sıfırı içermemesi bağımsızlık "
                                         "varsayımının ürünüdür; efektif örneklem 9 değil ~1 "
                                         "GÜNdür. Bu satır kuyruğu GÖSTERİR, hüküm TAŞIMAZ.",
                },
                "acilis_tabani_yok_n": sym_acilis_yok,
            },
        },
        "cikis_bacagi": {
            "olculdu": False,
            "n": 0,
            "gonderilen_satis_emri": len(satis_emir),
            "dolan_satis_emri": len(satis_dolan),
            "satis_dolum_olayi": len(satis_fill),
            "satis_emir_status_dagilim": {s: len([o for o in satis_emir if str(o.get("status")) == s])
                                          for s in sorted({str(o.get("status")) for o in satis_emir})},
            "neden": "ÖLÇÜLEMEDİ (n=0): motorun gönderdiği HİÇBİR satış emri dolmadı. Koruma "
                     "bacakları ya `expired` (2026-08-06 akşamı, ENTRY_TIF=day kelepçesi — "
                     "broker.py:60-75 E1-v2 şerhi) ya `canceled` ya da hâlâ `new/held`. Dört "
                     "pozisyon AÇIK. Çıkış slipajı için tek bir gözlem bile yok; sayı UYDURULMAZ.",
            "sonuc_icin_anlami": "Round-trip friksiyonun YARISI ölçülmemiştir. Aşağıdaki PF "
                                 "düzeltmesi bu yüzden İKİ senaryo verir (yalnız-giriş / simetrik).",
        },
        "kill_bayraklari": {
            "kill1_eslesen_cift_10_alti": {
                "tetiklendi": kill1, "n_cift": n_cift, "esik": MIN_CIFT,
                "hüküm_metni": (f"SLİPAJ ÖLÇÜLEMEDİ (n={n_cift} < {MIN_CIFT}) — kart kill#1. "
                                "Aşağıdaki sayılar BETİMLEYİCİdir; istatistiksel hüküm taşımaz."
                                if kill1 else "kill#1 ateşlenmedi"),
            },
            "kill2_replay_modeli_okunamadi": {"tetiklendi": False,
                                              "not": "model koddan OKUNDU (alıntılar `replay_varsayimi`da)"},
            "kill3_kagit_icra_replay_ayni_potada": {
                "tetiklendi": False,
                "not": "95 `replay_seed` satırı ve 2 `live_paper` satırı TCA paydasından ÇIKARILDI; "
                       "ölçüm YALNIZ broker'ın gerçek dolum kayıtları üstünde yapıldı.",
            },
        },
    }


# =================================================================================================
# (b) KOMİSYON / ÜCRET
# =================================================================================================
def ucret_olc(ham: dict) -> dict:
    alp = ham.get("alpaca") or {}
    akt = alp.get("activities") or {}
    fee = (akt.get("FEE") or {}).get("kayitlar") or []
    cfee = (akt.get("CFEE") or {}).get("kayitlar") or []
    ptc = (akt.get("PTC") or {}).get("kayitlar") or []
    tr = ham.get("trades") or {}
    fr = ham.get("friksiyon_ayari") or {}

    toplam = sum(abs(float(f.get("net_amount") or 0.0)) for f in fee + cfee + ptc)
    motor_gunu = [f for f in fee if str(f.get("date")) == "2026-08-06"]
    return {
        "GERCEKLESEN": {
            "kayit_tipleri_okundu": ["FEE", "CFEE", "PTC"],
            "FEE_n": len(fee), "CFEE_n": len(cfee), "PTC_n": len(ptc),
            "kayitlar": fee + cfee + ptc,
            "toplam_dolar_hesap_omru": round(toplam, 4),
            "motor_dolumlarina_atfedilen": round(
                sum(abs(float(f.get("net_amount") or 0.0)) for f in motor_gunu), 4),
            "atif_gerekcesi": "2026-08-06 tarihli CAT ücreti — açıklaması 'proceed of 9 trades' ve "
                              "o gün hesapta gerçekleşen 9 dolum olayının TAMAMI motorun giriş "
                              "emirlerine ait (NVDA dolumu 2026-07-14'te, ayrı ücret kaydı var).",
            "komisyon": {"dolar": 0.0,
                         "kanit": "Alpaca kâğıt hesabında komisyon aktivitesi YOK; hisse senedi "
                                  "komisyonu 0$. Ücret yalnız düzenleyici CAT kalemi olarak göründü."},
            "bps_karsiligi": None,   # aşağıda notional bilinince doldurulur
        },
        "MODELIN_VARSAYIMI": {
            "commission_per_share": fr.get("commission_per_share"),
            "dolar": 0.0,
            "kod": REPLAY_ALINTI["komisyon_tanimi"],
        },
        "costs_ALANI_UYARISI": {
            "trades_costs_toplam": tr.get("costs_toplam"),
            "costs_dolu_satir": tr.get("costs_dolu"),
            "gercek_dolumlu_satir": tr.get("alpaca_fill_price_dolu"),
            "hüküm": "`costs` GERÇEKLEŞEN FRİKSİYON DEĞİLDİR. Defterin 97 satırının 97'sinde "
                     "`costs` dolu ama 0'ında gerçek dolum fiyatı var → `costs` tamamen İÇ MODELİN "
                     "kendi slipaj dolarıdır (broker.py:674). 625,19$'ı 'ödediğimiz friksiyon' diye "
                     "okumak, varsayımı ölçüm sanmaktır.",
            "iki_kez_kesme_uyarisi": REPLAY_ALINTI["net_uyarisi"],
        },
        "OZET": "Gerçek ÜCRET tarafı ihmal edilebilir (hesap ömrü boyunca 0,02$; motora atfedilen "
                "0,01$). Friksiyonun tamamı SLİPAJdır — komisyon/ücret PF tartışmasında gürültüdür.",
    }


# =================================================================================================
# (c) REPLAY'İN VARSAYDIĞI FRİKSİYON
# =================================================================================================
def replay_varsayimi(ham: dict) -> dict:
    fr = ham.get("friksiyon_ayari") or {}
    band = fr.get("pessimistic_band_v2") or {}
    return {
        "yururlukteki_model": {
            "slippage_bps": fr.get("slippage_bps"),
            "birim": "tek yön (bacak başına), fiyatın İÇİNE gömülü",
            "round_trip_bps": (None if fr.get("slippage_bps") is None else 2 * float(fr["slippage_bps"])),
            "commission_per_share": fr.get("commission_per_share"),
            "spread_bileseni": "AYRI BİR BİLEŞEN YOK — spread, `slippage_bps` içinde varsayılmış "
                               "tek sayıya gömülüdür (goal.yaml:56-58 'frictions' bloğu)",
            "likidite_bileseni": REPLAY_ALINTI["likidite_etkisi"],
            "kod_alintilari": REPLAY_ALINTI,
            "goal_sha256_16": fr.get("goal_sha256_16"),
        },
        "pessimistic_band_v2": {
            **band,
            "yorum": "E3 KÖTÜMSER BANT (goal.yaml:96-112): açılış efektif spread 20 bps → tek yönde "
                     "yarısı = 10 bps/bacak ödenir varsayımı. Yürürlükteki model 5 bps/bacak → "
                     "kötümser bant EK 5 bps/bacak demektir. `ampirik_bps: null`, `ampirik_n: 0` — "
                     "yani bu bant BUGÜNE DEK ÖLÇÜLMEMİŞ, literatürden alınmış bir varsayımdır. "
                     "BU KART O ALANIN İLK AMPİRİK GİRDİSİNİ ÜRETİR (n çok küçük — aşağıda).",
        },
        "ayni_islemler_icin_ne_derdi": {
            "kaynak": "state/entry_execution.jsonl — İÇ MOTOR (`motor: ic`) satırları, AYNI dört "
                      "isim, AYNI seans, AYNI resmî açılış tabanı",
            "olculen_bps": [{"ticker": r["ticker"], "fill": r.get("fill"),
                             "resmi_acilis": r.get("resmi_acilis"),
                             "bps_vs_resmi_acilis": r.get("fill_vs_resmi_acilis_bps")}
                            for r in ((ham.get("entry_execution") or {}).get("satirlar") or [])
                            if r.get("motor") == "ic"],
            "totoloji_serhi": "İç motorun bps'i TANIM GEREĞİ `slippage_bps`i yeniden üretir "
                              "(defterin kendi beyanı, VLO satırı: 'resmî açılışa göre bps tanımı "
                              "gereği slippage_bps sabitini yeniden üretir — totoloji, ölçüm "
                              "değil'). Burada bir ÖLÇÜM değil, VARSAYIMIN SAYISI okunmaktadır — "
                              "kıyasın 'varsayılan' ayağı tam olarak budur.",
        },
    }


# =================================================================================================
# (d) FARK → PF ETKİSİ (EDG-032 defteri üzerinde)
# =================================================================================================
def _bar_ac(ticker: str, tarih: str, onbellek: dict) -> float | None:
    """state_cmb/bars/<ticker>.csv'den `tarih` gününün AÇILIŞI. Yoksa None (uydurma yok)."""
    t = str(ticker).lower()
    if t not in onbellek:
        p = os.path.join(BARS_032, f"{t}.csv")
        d = {}
        if os.path.exists(p):
            with open(p, newline="") as f:
                for row in csv.DictReader(f):
                    d[row["date"]] = row
        onbellek[t] = d
    return None if tarih not in onbellek[t] else float(onbellek[t][tarih]["open"])


def pf_etkisi(ham: dict, slip: dict) -> dict:
    with open(ISLEMLER_032) as f:
        rows = json.load(f)

    fark = slip["giris_bacagi"]["emir_duzeyi"]["FARK_gercek_eksi_model_bps"]
    d_ort = fark.get("ortalama")
    d_med = fark.get("medyan")
    d_w = fark.get("agirlikli_ortalama")

    onbellek: dict = {}
    n_bar_yok, n_ok = 0, 0
    sadakat_ok, sadakat_test = 0, 0
    for t in rows:
        ac = _bar_ac(t["ticker"], t["ts_open"], onbellek)
        if ac is None or ac <= 0:
            n_bar_yok += 1
            t["_notional_giris"] = None
            t["_notional_cikis"] = None
            continue
        n_ok += 1
        # motorun kendi dolum yasası: fill = açılış × (1 + slippage_bps/1e4) (+ likidite etkisi)
        giris_fiyat = ac * (1.0 + float((ham.get("friksiyon_ayari") or {}).get("slippage_bps") or 0) / 1e4)
        n_g = giris_fiyat * float(t["qty"])
        # çıkış notional'ı DEFTERDEN türer: komisyon 0 ve scale_out_frac=0 olduğu için
        # pnl_dollars = qty×(exit − entry) → qty×exit = qty×entry + pnl  (kimlik, tahmin değil)
        n_c = n_g + float(t["pnl_dollars"])
        t["_notional_giris"], t["_notional_cikis"] = n_g, max(0.0, n_c)
        # SADAKAT SINAMASI: türetilen çıkış fiyatı, kapanış barının [low, high] aralığında mı?
        kap = onbellek[str(t["ticker"]).lower()].get(str(t["ts_close"]))
        if kap:
            sadakat_test += 1
            px = n_c / float(t["qty"])
            if float(kap["low"]) * 0.98 <= px <= float(kap["high"]) * 1.02:
                sadakat_ok += 1

    def _pf(pnls: list[float]) -> float | None:
        p = sum(x for x in pnls if x > 0)
        n = sum(x for x in pnls if x < 0)
        return None if n == 0 else round(p / abs(n), 4)

    taban = [float(t["pnl_dollars"]) for t in rows]

    def senaryo(ek_bps_bacak: float, bacak: str) -> dict:
        """bacak: 'giris' (yalnız giriş bacağı) | 'her_iki' (simetrik varsayım)."""
        adj, atlanan = [], 0
        for t in rows:
            ng, nc = t.get("_notional_giris"), t.get("_notional_cikis")
            if ng is None:
                atlanan += 1
                continue
            ek = ek_bps_bacak / 1e4 * (ng if bacak == "giris" else (ng + nc))
            adj.append(float(t["pnl_dollars"]) - ek)
        return {"ek_bps_bacak": ek_bps_bacak, "bacak": bacak, "n": len(adj), "atlanan_bar_yok": atlanan,
                "brut_kazanc": round(sum(x for x in adj if x > 0), 2),
                "brut_kayip": round(sum(x for x in adj if x < 0), 2),
                "net": round(sum(adj), 2), "pf": _pf(adj),
                "kazanan_n": sum(1 for x in adj if x > 0), "kaybeden_n": sum(1 for x in adj if x < 0)}

    # PF'i 1,0'a indiren ek friksiyon (başabaş noktası) — ikili arama
    def basabas(bacak: str) -> float | None:
        lo, hi = 0.0, 500.0
        if (senaryo(hi, bacak)["pf"] or 0) > 1.0:
            return None
        for _ in range(60):
            orta = (lo + hi) / 2
            if (senaryo(orta, bacak)["pf"] or 0) > 1.0:
                lo = orta
            else:
                hi = orta
        return round((lo + hi) / 2, 2)

    senaryolar = {
        "S0_taban_replay_varsayimi": {
            "aciklama": "EDG-032'nin yayınlanmış hâli — friksiyon = 5 bps/bacak (fiyata gömülü)",
            "n": len(rows), "brut_kazanc": round(sum(x for x in taban if x > 0), 2),
            "brut_kayip": round(sum(x for x in taban if x < 0), 2),
            "net": round(sum(taban), 2), "pf": _pf(taban),
        },
        "S1_gerceklesen_ORTALAMA_yalniz_giris": {
            **senaryo(d_ort, "giris"),
            "aciklama": "ölçülen ortalama FARK yalnız giriş bacağına — çıkış bacağı ölçülmediği için "
                        "muhafazakâr (alt sınır) senaryo",
        },
        "S2_gerceklesen_ORTALAMA_simetrik": {
            **senaryo(d_ort, "her_iki"),
            "aciklama": "aynı fark her iki bacağa — VARSAYIM: çıkış bacağı girişe benzer davranır "
                        "(ÖLÇÜLMEDİ; n=0)",
        },
        "S3_gerceklesen_MEDYAN_simetrik": {
            **senaryo(d_med, "her_iki"),
            "aciklama": "medyan fark (uç gözlem BKNG'nin etkisi kırpılmış), simetrik",
        },
        "S4_gerceklesen_NOTIONAL_AGIRLIKLI_simetrik": {
            **senaryo(d_w, "her_iki"),
            "aciklama": "notional-ağırlıklı fark, simetrik — dolar etkisine en yakın okuma",
        },
        "S5_E3_kotumser_bant_referans": {
            **senaryo(5.0, "her_iki"),
            "aciklama": "goal.pessimistic_band_v2'nin varsaydığı EK 5 bps/bacak — bu kart ÖNCESİ "
                        "elimizdeki en kötümser sayı; kıyas çıpası",
        },
        "S6_gozlenen_EN_IYI_nokta_simetrik": {
            **senaryo(fark.get("min"), "her_iki"),
            "aciklama": "dört gözlemin EN LEHTE olanı (AMGN) her iki bacağa — 'en iyimser okuma bile "
                        "ne yapar' sınaması; sonucun tek bir uç gözleme (BKNG) dayanmadığını gösterir",
        },
    }

    # --- DUYARLILIK EĞRİSİ: PF, ek friksiyonun fonksiyonu olarak (eşik tartışmasının çıpası)
    egri = {"yalniz_giris": {}, "simetrik": {}}
    for b, ad in (("giris", "yalniz_giris"), ("her_iki", "simetrik")):
        for x in (0, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 75, 100):
            egri[ad][x] = senaryo(float(x), b)["pf"]
    return {
        "taban_defter": {"kaynak": os.path.relpath(ISLEMLER_032, BURASI), "n": len(rows),
                         "sha256_16": sha16(ISLEMLER_032),
                         "tarih_araligi": [min(t["ts_open"] for t in rows), max(t["ts_close"] for t in rows)]},
        "notional_turetme": {
            "yontem": "giriş notional = qty × açılış(ts_open) × (1+slippage_bps/1e4) — motorun KENDİ "
                      "dolum yasası (broker.py:515). çıkış notional = giriş notional + pnl_dollars — "
                      "KİMLİK (komisyon 0 + scale_out_frac 0,0 → pnl = qty×(exit−entry)).",
            "bar_kaynagi": os.path.relpath(BARS_032, BURASI),
            "bar_bulunan": n_ok, "bar_yok": n_bar_yok,
            "sadakat_sinamasi": {
                "test_edilen": sadakat_test, "gecen": sadakat_ok,
                "oran": None if sadakat_test == 0 else round(sadakat_ok / sadakat_test, 4),
                "olcut": "türetilen çıkış fiyatı, ts_close barının [low×0,98 , high×1,02] aralığında mı",
            },
            "serh": "Likidite etkisi (IMPACT_COEF·katılım) notional'da İHMAL EDİLDİ — ADV tavanında "
                    "bile ≤20 bps'lik bir fiyat farkı notional'ı %0,2 oynatır; PF hassasiyetini "
                    "etkilemez. Bar bulunamayan satır düzeltmeden DÜŞER (uydurma yasağı) ve sayısı "
                    "yukarıda beyanlıdır.",
        },
        "olculen_fark_bps_bacak": {"ortalama": d_ort, "medyan": d_med, "notional_agirlikli": d_w,
                                   "n": fark.get("n"),
                                   "serh": "n=4 — bu sayı bir NOKTA TAHMİNİdir, dağılım değil"},
        "senaryolar": senaryolar,
        "duyarlilik_egrisi_pf": {**egri,
                                 "birim": "anahtar = EK bps/bacak (yürürlükteki 5 bps'in ÜSTÜNE)",
                                 "not": "PF ek friksiyonda MONOTON AZALANDIR — hiçbir friksiyon "
                                        "varsayımı 1,1119'un üstüne çıkaramaz; eşik tartışması "
                                        "yalnız 'ne kadar aşağıda' sorusudur"},
        "basabas_ek_bps_bacak": {
            "yalniz_giris": basabas("giris"), "simetrik": basabas("her_iki"),
            "anlami": "PF'i tam 1,0'a (başabaş) indiren EK friksiyon. Ölçülen fark bu sayının "
                      "üstündeyse benimsenen paket friksiyon-düzeltilmiş hâlde PARA KAYBEDER.",
        },
        "esik_baglami": {
            "RESULT_PF_MIN": 1.3,
            "kod": "meridian/analytics.py:2089-2093",
            "esigin_b_ayagi": "\"Alpaca paper dolumları iyimser — Y2/TCA hâlâ ölçülmedi\"",
            "not": "Bu kart HÜKÜM VERMEZ. Yukarıdaki senaryolar eşik tartışmasının GİRDİSİdir.",
        },
    }


# =================================================================================================
def main() -> None:
    with open(HAM) as f:
        ham = json.load(f)

    slip = slipaj_olc(ham)
    ucret = ucret_olc(ham)
    varsayim = replay_varsayimi(ham)
    pf = pf_etkisi(ham, slip)

    # ücretin bps karşılığı — notional bilindikten sonra
    nt = slip["giris_bacagi"]["emir_duzeyi"]["dolar"]["notional_acilista"]
    u = ucret["GERCEKLESEN"]["motor_dolumlarina_atfedilen"]
    ucret["GERCEKLESEN"]["bps_karsiligi"] = (None if not nt else round(1e4 * u / nt, 4))
    ucret["GERCEKLESEN"]["bps_karsiligi_taban"] = f"motor giriş notional'ı {nt}$"

    sonuc = {
        "kart": "EDG-2026-037",
        "kart_yolu": "research/cards/EDG-2026-037-tca-gercek-friksiyon.yaml",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "modul": os.path.abspath(__file__),
        "ham_kanit": {"dosya": os.path.relpath(HAM, BURASI), "sha256_16": sha16(HAM),
                      "cekim_zamani": ham.get("cekim_zamani"),
                      "cekim_betigi": "canli_cek.py (canlıda SALT-OKUMA, stdin deseni)"},
        "K_sayimi": "K += 0 — betimsel ölçüm, hipotez sınamıyor (kart parameter_grid: yok)",
        "OZET_TABLO": {
            "payda_kunyesi": {
                "kullanilan_payda": "EMİR düzeyi (giriş bacağı) — kart features_asof izniyle "
                                    "kapanmış-işlemden genişletildi",
                "eslesen_plan_dolum_cifti": slip["giris_bacagi"]["emir_duzeyi"]
                                            ["GERCEK_vs_resmi_acilis_bps"]["n"],
                "dolum_olayi": slip["giris_bacagi"]["dolum_olayi_duzeyi"]
                               ["GERCEK_vs_resmi_acilis_bps"]["n"],
                "cikis_bacagi_cifti": 0,
                "dislanan_replay_seed": ((ham.get("trades") or {}).get("kaynak_dagilim") or {}).get("replay_seed"),
                "dislanan_live_paper": ((ham.get("trades") or {}).get("kaynak_dagilim") or {}).get("live_paper"),
                "seans": "TEK seans — 2026-08-06 13:30-13:33Z (açılışın ilk 3 dakikası)",
            },
            "slipaj_giris_bps_vs_resmi_acilis": {
                k: slip["giris_bacagi"]["emir_duzeyi"]["GERCEK_vs_resmi_acilis_bps"].get(k)
                for k in ("n", "medyan", "ortalama", "p90", "min", "max", "agirlikli_ortalama")},
            "slipaj_cikis": "ÖLÇÜLEMEDİ (n=0) — 24 motor satış emri gönderildi, 0'ı doldu",
            "replay_varsayimi_bps_bacak": (ham.get("friksiyon_ayari") or {}).get("slippage_bps"),
            "kotumser_bant_bps_bacak": 10.0,
            "FARK_bps_bacak": {
                k: slip["giris_bacagi"]["emir_duzeyi"]["FARK_gercek_eksi_model_bps"].get(k)
                for k in ("n", "medyan", "ortalama", "agirlikli_ortalama", "min", "max")},
            "FARK_dolar_dort_emirde": {
                "gercek": slip["giris_bacagi"]["emir_duzeyi"]["dolar"]["slipaj_GERCEK_toplam"],
                "model_ayni_adet": slip["giris_bacagi"]["emir_duzeyi"]["dolar"]["slipaj_MODEL_ayni_adet_toplam"],
                "notional": slip["giris_bacagi"]["emir_duzeyi"]["dolar"]["notional_acilista"],
            },
            "ucret_gercek_dolar": ucret["GERCEKLESEN"]["motor_dolumlarina_atfedilen"],
            "pf": {k: v.get("pf") for k, v in pf["senaryolar"].items()},
            "pf_basabas_ek_bps": pf["basabas_ek_bps_bacak"],
            "kill": {k: v.get("tetiklendi") for k, v in slip["kill_bayraklari"].items()},
        },
        "a_gerceklesen_slipaj": slip,
        "b_komisyon_ucret": ucret,
        "c_replay_varsayimi": varsayim,
        "d_fark_ve_pf_etkisi": pf,
        "HUKUM": "YOK — bu kart eşiği DEĞİŞTİRMEZ (kart success_metric). Ürün: sayı + künye + fark.",
    }
    yol = os.path.join(BURASI, "sonuc.json")
    with open(yol, "w") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1, default=str)
    print("YAZILDI:", yol)

    # --- konsol özeti
    e = slip["giris_bacagi"]["emir_duzeyi"]
    print("\n== GİRİŞ BACAĞI · GERÇEK slipaj (resmî açılışa göre, bps) ==")
    print(json.dumps(e["GERCEK_vs_resmi_acilis_bps"], ensure_ascii=False, indent=1))
    print("\n== FARK (gerçek − replay varsayımı), bps/bacak ==")
    print(json.dumps(e["FARK_gercek_eksi_model_bps"], ensure_ascii=False, indent=1))
    print("\n== ÇIKIŞ BACAĞI ==")
    print(json.dumps({k: v for k, v in slip["cikis_bacagi"].items() if k != "satirlar"},
                     ensure_ascii=False, indent=1))
    print("\n== KILL ==")
    print(json.dumps(slip["kill_bayraklari"], ensure_ascii=False, indent=1))
    print("\n== DOLUM-OLAYI DÜZEYİ (n=9) ==")
    print(json.dumps(slip["giris_bacagi"]["dolum_olayi_duzeyi"]["GERCEK_vs_resmi_acilis_bps"],
                     ensure_ascii=False, indent=1))
    print("\n== PAYDA MERDİVENİ ==")
    for k, v in slip["payda_merdiveni"].items():
        print(f"  {k}: " + json.dumps({kk: vv for kk, vv in v.items()
                                       if kk not in ("hüküm", "beyan", "replay_seed_neden",
                                                     "motor_disi_neden")},
                                      ensure_ascii=False))
    print("\n== ÜCRET ==")
    print(json.dumps({k: v for k, v in ucret["GERCEKLESEN"].items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    print("\n== PF SENARYOLARI ==")
    for k, v in pf["senaryolar"].items():
        print(f"  {k:42s} pf={v.get('pf')}  net={v.get('net')}  "
              f"(+{v.get('brut_kazanc')} / {v.get('brut_kayip')})")
    print("  başabaş ek bps/bacak:", pf["basabas_ek_bps_bacak"])
    print("  duyarlılık (simetrik):", pf["duyarlilik_egrisi_pf"]["simetrik"])
    print("  duyarlılık (yalnız giriş):", pf["duyarlilik_egrisi_pf"]["yalniz_giris"])
    print("  notional sadakat:", pf["notional_turetme"]["sadakat_sinamasi"])


if __name__ == "__main__":
    main()
