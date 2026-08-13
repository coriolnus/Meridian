"""EDG-2026-038 · TCA tur-2 — ÖLÇÜM (yerel; canlıya dokunmaz).

GİRDİ:
  canli_ham.json      — canlıdan SALT-OKUMA çekim (canli_cek.py)
  massive_capraz.json — Massive (BAĞIMSIZ ikinci konsolide kaynak) çapraz kontrolü
  ../edg037_tca_2026-08-13/sonuc.json           — EDG-037'nin IEX sütunu (SİLİNMEZ, yan yana konur)
  ../edg032_final_paket_2026-08-12/islemler_cmb.json + state_cmb/bars — 885 işlemlik defter (PF)

ÜRÜN: sonuc.json — [A] üç payda kıyası + kanonik seçim · [B] çıkış bacağı · [C] asimetrik PF yüzeyi.

KART: research/cards/EDG-2026-038-tca-konsolide-cikis.yaml (ölçümden ÖNCE yazıldı, eşikler donuk).
UYDURMA YASAĞI: ölçülemeyen her kalem None + neden.
"""
import csv
import datetime as dt
import hashlib
import json
import os
import random
import statistics as st

BURASI = os.path.dirname(os.path.abspath(__file__))
HAM = os.path.join(BURASI, "canli_ham.json")
MASSIVE = os.path.join(BURASI, "massive_capraz.json")
EDG037 = os.path.join(BURASI, "..", "edg037_tca_2026-08-13", "sonuc.json")
EDG032 = os.path.join(BURASI, "..", "edg032_final_paket_2026-08-12")
ISLEMLER_032 = os.path.join(EDG032, "islemler_cmb.json")
BARS_032 = os.path.join(EDG032, "state_cmb", "bars")

SEANS = "2026-08-06"
DAKIKA_ACILIS = "2026-08-06T13:30:00Z"
BOOT_N, BOOT_SEED = 20000, 20260813          # EDG-037 ile AYNI (kıyas edilebilirlik)
KART_ESIK_OLCUT_BPS = 5.0                    # kartta DONDURULDU: |IEX−konsolide| > 5 bps ⇒ taşınmalı
KART_ESIK_CIKIS_N = 5                        # kartta DONDURULDU: n<5 ⇒ "ÖLÇÜLEMEDİ (n=X)"
KART_ESIK_CAPRAZ_BPS = 5.0                   # kartta DONDURULDU: iki konsolide kaynak >5 bps ⇒ ilan YOK
KART_ESIK_CIPLAK_SEANS = 1.0                 # kartta DONDURULDU: >1 tam seans korumasız ⇒ bulgu


# ------------------------------------------------------------------ yardımcılar (EDG-037 ile aynı)
def sha16(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return None


def bps(gercek: float | None, taban: float | None) -> float | None:
    if gercek is None or taban in (None, 0):
        return None
    return round((float(gercek) / float(taban) - 1.0) * 1e4, 3)


def betim(xs: list, agirlik: list | None = None) -> dict:
    xs = [float(x) for x in xs if x is not None]
    if not xs:
        return {"n": 0, "medyan": None, "ortalama": None, "p90": None, "min": None, "max": None,
                "agirlikli_ortalama": None}
    s = sorted(xs)
    def _p(q):
        if len(s) == 1:
            return s[0]
        k = (len(s) - 1) * q
        lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return s[lo] + (s[hi] - s[lo]) * (k - lo)
    w = None
    if agirlik and len(agirlik) == len(xs) and sum(agirlik) > 0:
        w = round(sum(a * b for a, b in zip(xs, agirlik)) / sum(agirlik), 3)
    return {"n": len(xs), "medyan": round(st.median(s), 3), "ortalama": round(sum(s) / len(s), 3),
            "p90": round(_p(0.9), 3), "min": round(s[0], 3), "max": round(s[-1], 3),
            "agirlikli_ortalama": w}


_T95 = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}


def t_ci(xs: list) -> dict | None:
    xs = [float(x) for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m, sd = sum(xs) / len(xs), st.stdev(xs)
    se = sd / (len(xs) ** 0.5)
    t = _T95.get(len(xs) - 1, 1.96)
    return {"ortalama": round(m, 3), "sd": round(sd, 3), "se": round(se, 3), "t": t,
            "lo": round(m - t * se, 3), "hi": round(m + t * se, 3),
            "sifiri_iceriyor": bool((m - t * se) <= 0 <= (m + t * se))}


def bootstrap_ci(xs: list, n_iter: int = BOOT_N, seed: int = BOOT_SEED) -> dict | None:
    xs = [float(x) for x in xs if x is not None]
    if len(xs) < 2:
        return None
    rnd = random.Random(seed)
    orts = sorted(sum(rnd.choices(xs, k=len(xs))) / len(xs) for _ in range(n_iter))
    return {"lo": round(orts[int(0.025 * n_iter)], 3), "hi": round(orts[int(0.975 * n_iter)], 3),
            "orta": round(sum(xs) / len(xs), 3), "n_iter": n_iter, "seed": seed,
            "serh": "n<10'da bootstrap yalnız GÖZLENEN değerleri yeniden örnekler — dağılım "
                    "varsayımı yok ama bilgi de yok; genişlik betimleyicidir"}


def isaret_testi(xs: list) -> dict:
    xs = [float(x) for x in xs if x is not None]
    aleyhte = sum(1 for x in xs if x > 0)
    lehte = sum(1 for x in xs if x < 0)
    n = aleyhte + lehte
    p = None
    if n:
        from math import comb
        p = round(sum(comb(n, k) for k in range(aleyhte, n + 1)) / (2 ** n), 5)
    return {"n": n, "aleyhte": aleyhte, "lehte": lehte, "p_tek_kuyruk": p,
            "yorum": "H0: dolumun tabanın üstünde/altında olması eşit olasılıklı (p=0,5)"}


def _bar(bloklar: dict, sym: str, ts: str | None = None) -> dict | None:
    """`{SYM: [bar,...]}` haritasından bar. ts verilirse O damgalı bar, yoksa ilk bar."""
    rows = (bloklar or {}).get(sym) or []
    if ts is None:
        return rows[0] if rows else None
    for r in rows:
        if str(r.get("t")) == ts:
            return r
    return None


# =================================================================================================
# [A] ÜÇ PAYDA — konsolide açılış / ilk-dk VWAP / ilk-dk orta-nokta (+ EDG-037'nin IEX sütunu)
# =================================================================================================
def a_olcut(ham: dict, mv: dict, e037: dict) -> dict:
    gun_sip = (ham.get("gunluk_bar_sip") or {}).get("bars") or {}
    gun_iex = (ham.get("gunluk_bar_iex") or {}).get("bars") or {}
    dk_sip = (ham.get("dakika_bar_sip") or {}).get("bars") or {}
    dk_iex = (ham.get("dakika_bar_iex") or {}).get("bars") or {}
    replay_bar = ((ham.get("replay_bar_arsivi") or {}).get("barlar") or {})

    # --- gerçek dolumlar: BROKER kaydından (emir düzeyi) — motor öneki + bracket giriş bacağı
    emirler = ((ham.get("alpaca") or {}).get("orders") or {}).get("satirlar") or []
    dolumlar = []
    for o in emirler:
        coid = str(o.get("client_order_id") or "")
        if (coid.startswith("P-2026-") and o.get("side") == "buy"
                and str(o.get("status")) == "filled" and o.get("filled_avg_price")):
            dolumlar.append({"plan_id": coid, "ticker": str(o.get("symbol")).upper(),
                             "qty": float(o.get("filled_qty") or 0),
                             "fill": float(o.get("filled_avg_price")),
                             "limit": float(o.get("limit_price") or 0) or None,
                             "type": o.get("type"), "tif": o.get("time_in_force"),
                             "submitted_at": o.get("submitted_at"), "filled_at": o.get("filled_at")})
    dolumlar.sort(key=lambda x: x["ticker"])

    # --- EDG-037'nin IEX paydası (kartın kendi sayısı, yeniden okunur — elle kopyalanmaz)
    e037_satir = {r["ticker"]: r for r in
                  (((e037.get("a_gerceklesen_slipaj") or {}).get("giris_bacagi") or {})
                   .get("emir_duzeyi") or {}).get("satirlar") or []}

    paydalar: dict = {}
    for d in dolumlar:
        s = d["ticker"]
        b_sip_g, b_iex_g = _bar(gun_sip, s), _bar(gun_iex, s)
        b_sip_d = _bar(dk_sip, s, DAKIKA_ACILIS)
        b_iex_d = _bar(dk_iex, s, DAKIKA_ACILIS)
        rb = replay_bar.get(s) or {}
        mv_g = (mv.get("gunluk") or {}).get(s) or {}
        mv_d = (mv.get("dakika_1330") or {}).get(s) or {}
        paydalar[s] = {
            "D1_konsolide_acilis": None if not b_sip_g else float(b_sip_g["o"]),
            "D2_konsolide_ilk_dk_vwap": None if not b_sip_d else float(b_sip_d["vw"]),
            "D3_konsolide_ilk_dk_orta_nokta": (None if not b_sip_d
                                               else round((float(b_sip_d["h"]) + float(b_sip_d["l"])) / 2, 6)),
            "D0_IEX_acilis_EDG037": None if not b_iex_g else float(b_iex_g["o"]),
            "DM_replay_bar_arsivi_acilis": None if not rb.get("open") else float(rb["open"]),
            "_massive_gunluk_acilis": mv_g.get("o"),
            "_massive_dk_vwap": mv_d.get("vw"),
            "_massive_dk_orta_nokta": (None if not mv_d else round((float(mv_d["h"]) + float(mv_d["l"])) / 2, 6)),
            "_sip_dk_bar": b_sip_d, "_iex_dk_bar": b_iex_d,
            "_iex_gunluk_islem_sayisi": None if not b_iex_g else b_iex_g.get("n"),
            "_sip_gunluk_islem_sayisi": None if not b_sip_g else b_sip_g.get("n"),
        }

    # --- ÇAPRAZ KONTROL (kart kill#2): Alpaca SIP vs Massive
    capraz = {"esik_bps": KART_ESIK_CAPRAZ_BPS, "satirlar": [], "max_sapma_bps": None,
              "tetiklendi": None}
    sapmalar = []
    for s, p in paydalar.items():
        r = {"ticker": s,
             "alpaca_sip_acilis": p["D1_konsolide_acilis"], "massive_acilis": p["_massive_gunluk_acilis"],
             "acilis_fark_bps": bps(p["D1_konsolide_acilis"], p["_massive_gunluk_acilis"]),
             "alpaca_sip_dk_vwap": p["D2_konsolide_ilk_dk_vwap"], "massive_dk_vwap": p["_massive_dk_vwap"],
             "vwap_fark_bps": bps(p["D2_konsolide_ilk_dk_vwap"], p["_massive_dk_vwap"]),
             "orta_nokta_fark_bps": bps(p["D3_konsolide_ilk_dk_orta_nokta"], p["_massive_dk_orta_nokta"])}
        capraz["satirlar"].append(r)
        for k in ("acilis_fark_bps", "vwap_fark_bps", "orta_nokta_fark_bps"):
            if r[k] is not None:
                sapmalar.append(abs(r[k]))
    if sapmalar:
        capraz["max_sapma_bps"] = round(max(sapmalar), 3)
        capraz["tetiklendi"] = bool(max(sapmalar) > KART_ESIK_CAPRAZ_BPS)
        capraz["acilis_max_sapma_bps"] = round(max(abs(r["acilis_fark_bps"]) for r in capraz["satirlar"]
                                                   if r["acilis_fark_bps"] is not None), 3)

    # --- ÖLÇÜT HATASI (kart kill#3): IEX vs konsolide açılış
    olcut_hatasi = {"esik_bps": KART_ESIK_OLCUT_BPS, "satirlar": []}
    for s, p in paydalar.items():
        olcut_hatasi["satirlar"].append({
            "ticker": s, "IEX_acilis": p["D0_IEX_acilis_EDG037"],
            "konsolide_acilis": p["D1_konsolide_acilis"],
            "IEX_eksi_konsolide_bps": bps(p["D0_IEX_acilis_EDG037"], p["D1_konsolide_acilis"]),
            "IEX_gunluk_islem_sayisi": p["_iex_gunluk_islem_sayisi"],
            "SIP_gunluk_islem_sayisi": p["_sip_gunluk_islem_sayisi"],
            "IEX_ilk_dk_islem_sayisi": (p["_iex_dk_bar"] or {}).get("n"),
            "SIP_ilk_dk_islem_sayisi": (p["_sip_dk_bar"] or {}).get("n"),
        })
    hat = [abs(r["IEX_eksi_konsolide_bps"]) for r in olcut_hatasi["satirlar"]
           if r["IEX_eksi_konsolide_bps"] is not None]
    olcut_hatasi["max_mutlak_bps"] = round(max(hat), 3) if hat else None
    olcut_hatasi["medyan_mutlak_bps"] = round(st.median(hat), 3) if hat else None
    olcut_hatasi["esigi_asan_satir"] = sum(1 for x in hat if x > KART_ESIK_OLCUT_BPS)
    olcut_hatasi["kill3_curudu_mu"] = bool(hat and all(x <= KART_ESIK_OLCUT_BPS for x in hat))

    # --- KANONİK SEÇİMİN SINANMASI: hangi payda MODELİN KENDİ paydasına (replay bar arşivi) yakın?
    #     Ölçtüğümüz şey "gerçek − modelin dediği". Payda modelin paydasından ne kadar saparsa,
    #     ölçüm o kadar model-hatası DIŞI bir şeyi ölçer. Bu tablo bir ARGÜMAN değil bir SAYIdır.
    yakinlik = {"aciklama": "her payda adayının MODELİN KENDİ paydasından (state/bars açılışı, "
                            "kaynak: Cboe — bars_source.json) sapması, mutlak bps",
                "satirlar": [], "ozet": {}}
    for s, p in paydalar.items():
        m = p["DM_replay_bar_arsivi_acilis"]
        r = {"ticker": s, "model_paydasi": m}
        for ad in ("D0_IEX_acilis_EDG037", "D1_konsolide_acilis", "D2_konsolide_ilk_dk_vwap",
                   "D3_konsolide_ilk_dk_orta_nokta"):
            r[ad] = p[ad]
            r[f"{ad}_sapma_bps"] = bps(p[ad], m)
        yakinlik["satirlar"].append(r)
    for ad in ("D0_IEX_acilis_EDG037", "D1_konsolide_acilis", "D2_konsolide_ilk_dk_vwap",
               "D3_konsolide_ilk_dk_orta_nokta"):
        v = [abs(r[f"{ad}_sapma_bps"]) for r in yakinlik["satirlar"] if r.get(f"{ad}_sapma_bps") is not None]
        yakinlik["ozet"][ad] = ({"n": len(v), "medyan_mutlak_bps": round(st.median(v), 3),
                                 "ortalama_mutlak_bps": round(sum(v) / len(v), 3),
                                 "max_mutlak_bps": round(max(v), 3)} if v else None)

    # --- ÜÇ ÖLÇÜT (+IEX) ile SLİPAJ ve MODELE GÖRE FARK
    slip_bps = float((ham.get("friksiyon_ayari") or {}).get("slippage_bps") or 0)
    olcutler: dict = {}
    ADLAR = {"D0_IEX_acilis_EDG037": "IEX günlük açılış (EDG-037'nin PAYDASI — yan yana kalsın diye)",
             "D1_konsolide_acilis": "KONSOLİDE resmî açılış basımı (SIP günlük bar `open` = 13:30 müzayede)",
             "D2_konsolide_ilk_dk_vwap": "KONSOLİDE ilk-dakika VWAP (13:30-13:31 barı `vw`)",
             "D3_konsolide_ilk_dk_orta_nokta": "KONSOLİDE ilk-dakika MENZİL orta-noktası ((h+l)/2)"}
    for ad, aciklama in ADLAR.items():
        satirlar = []
        for d in dolumlar:
            p = paydalar[d["ticker"]]
            taban = p[ad]
            b = bps(d["fill"], taban)
            # MODELİN aynı ölçütteki karşılığı: model fiyatı = modelin_paydasi × (1+slip);
            # aynı paydaya göre bps'i → farkA = gerçek_bps − model_bps
            m_fiyat = None if p["DM_replay_bar_arsivi_acilis"] is None else \
                p["DM_replay_bar_arsivi_acilis"] * (1.0 + slip_bps / 1e4)
            m_bps = bps(m_fiyat, taban)
            bar_hata = bps(p["DM_replay_bar_arsivi_acilis"], taban)   # modelin BARININ ölçüte sapması
            satirlar.append({
                "ticker": d["ticker"], "plan_id": d["plan_id"], "qty": d["qty"], "fill": d["fill"],
                "payda": taban, "bps_vs_payda": b,
                "model_fiyati": None if m_fiyat is None else round(m_fiyat, 4),
                "model_bps_vs_payda": m_bps,
                "model_BAR_hatasi_bps": bar_hata,
                "farkA_payda_ozdes_bps": None if (b is None or m_bps is None) else round(b - m_bps, 3),
                "farkB_yalniz_icra_bps": None if b is None else round(b - slip_bps, 3),
                "notional_fill": round(d["fill"] * d["qty"], 2),
                "slipaj_dolar_GERCEK": None if taban is None else round((d["fill"] - taban) * d["qty"], 4),
            })
        xs = [r["bps_vs_payda"] for r in satirlar]
        ws = [r["notional_fill"] for r in satirlar]
        fkA = [r["farkA_payda_ozdes_bps"] for r in satirlar]
        fkB = [r["farkB_yalniz_icra_bps"] for r in satirlar]
        bh = [r["model_BAR_hatasi_bps"] for r in satirlar]
        olcutler[ad] = {
            "aciklama": aciklama, "satirlar": satirlar,
            "GERCEK_vs_payda_bps": {**betim(xs, ws), "agirlik_tabani": "notional (fill × qty)",
                                    "t_ci95": t_ci(xs), "bootstrap_ci95": bootstrap_ci(xs),
                                    "isaret_testi": isaret_testi(xs)},
            "FARK_A_payda_ozdes": {**betim(fkA, ws), "agirlik_tabani": "notional (fill × qty)",
                                   "t_ci95": t_ci(fkA), "bootstrap_ci95": bootstrap_ci(fkA),
                                   "isaret_testi": isaret_testi(fkA),
                                   "tanim": "gerçek_bps − model_bps (İKİSİ DE aynı paydaya göre). "
                                            "Model fiyatı = MODELİN KENDİ barı × (1+5bps).",
                                   "serh": "Bu fark İKİ bileşen taşır: (a) icra sapması, (b) modelin "
                                           "BARININ ölçüte sapması. Ayrıştırması `MODEL_BAR_HATASI`."},
            "FARK_B_yalniz_icra": {**betim(fkB, ws), "agirlik_tabani": "notional (fill × qty)",
                                   "t_ci95": t_ci(fkB), "bootstrap_ci95": bootstrap_ci(fkB),
                                   "isaret_testi": isaret_testi(fkB),
                                   "tanim": f"gerçek_bps − {slip_bps} (modelin NOMİNAL slipaj "
                                            f"varsayımı). Modelin bar hatası DIŞARIDA.",
                                   "serh": "Kimlik: farkA = farkB − model_BAR_hatasi (birebir tutar)."},
            "MODEL_BAR_HATASI": {**betim(bh, ws),
                                 "tanim": "replay bar arşivi açılışı (Cboe) − bu ölçüt, bps",
                                 "t_ci95": t_ci(bh), "isaret_testi": isaret_testi(bh),
                                 "serh": "Bu bir İCRA kalemi DEĞİL, bir VERİ-SAĞLAYICI sapmasıdır. "
                                         "İşareti sistematik mi rastgele mi — n=4'te SÖYLENEMEZ."},
        }

    # --- EDG-037'nin yayınlanmış sayıları (SİLİNMEZ — yan yana)
    e037_ozet = ((e037.get("OZET_TABLO") or {}).get("slipaj_giris_bps_vs_resmi_acilis") or {})

    # --- KANONİK İLAN (kartta ÖN-KAYITLI; ölçüm yalnız çürütebilir)
    curutuldu = []
    if capraz.get("tetiklendi"):
        curutuldu.append("kill#2: iki konsolide kaynak >5 bps ayrıştı")
    kaynak_dagilim = ((ham.get("bars_source") or {}).get("dagilim") or {})
    if not kaynak_dagilim or set(kaynak_dagilim) & {"alpaca_iex", "iex"}:
        curutuldu.append("gerekce_1: replay bar arşivi KONSOLİDE değil (kaynak damgası IEX)")
    # açılış basımı gerçekten ilk-dakika bandının içinde mi?
    bant_disi = []
    for s, p in paydalar.items():
        b = p["_sip_dk_bar"] or {}
        if b and p["D1_konsolide_acilis"] is not None:
            if not (float(b["l"]) <= p["D1_konsolide_acilis"] <= float(b["h"])):
                bant_disi.append(s)
    if bant_disi:
        curutuldu.append(f"gerekce_2: SIP günlük açılış ilk-dk bandının DIŞINDA ({','.join(bant_disi)})")

    return {
        "payda_kunyesi": {
            "KONSOLİDE_KAYNAK_ADIYLA": {
                "uc": f"{(ham.get('feed_kunyesi') or {}).get('DATA_BASE')}/v2/stocks/bars",
                "feed_parametresi": "feed=sip",
                "kod_sabiti": "meridian/adapters/alpaca.py:1093 — `DATA_FEED_SIP = \"sip\"`",
                "gunluk": "timeframe=1Day, adjustment=split, start=end=2026-08-06",
                "dakika": "timeframe=1Min, 2026-08-06T13:25Z..14:05Z",
                "IKINCI_BAGIMSIZ_KAYNAK": "Massive /v2/aggs (grouped daily + 1/minute) — massive_capraz.json",
            },
            "EDG037_PAYDASI_ADIYLA": {
                "feed_parametresi": "feed=iex",
                "kod_sabiti": "meridian/adapters/alpaca.py:1092 — `DATA_FEED = \"iex\"`",
                "nasil_defterlere_girdi": "loop.py:1998 `per[ticker].loc[d,'open']` → loop.py:2290-2299 "
                                          "`_patch_entry_slippage` → state/entry_execution.jsonl "
                                          "`resmi_acilis`; kaynak zinciri alpaca.py:1092,1431",
                "IEX_NEDIR": "IEX tek bir borsanın kendi bandıdır; konsolide (SIP) hacmin medyan "
                             "%2,2-2,5'i (alpaca.py:1101 canlı ölçümü). 'IEX'in ilk basımı' ≠ "
                             "'resmî açılış müzayedesi basımı'.",
            },
            "MODELIN_PAYDASI_ADIYLA": {
                "kod": "meridian/broker.py:515 — `base_fill = next_open * (1.0 + self.slip)`",
                "next_open_nereden": "replay bar arşivi state/bars/<sym>.csv",
                "arsiv_kaynak_damgasi": kaynak_dagilim,
                "dort_sembol_damgasi": (ham.get("bars_source") or {}).get("dort_sembol"),
                "kaynak_kodu": "meridian/adapters/data.py — Cboe delayed_quotes historical (birincil) / "
                               "Nasdaq (yedek) / Massive grouped — ÜÇÜ DE KONSOLİDE, hiçbiri IEX değil",
            },
        },
        "dolumlar": dolumlar,
        "paydalar": paydalar,
        "capraz_kontrol_iki_konsolide_kaynak": capraz,
        "olcut_hatasi_IEX_vs_konsolide": olcut_hatasi,
        "kanonik_secim_sinamasi_MODELE_YAKINLIK": yakinlik,
        "olcutler": olcutler,
        "EDG037_YAYINLANMIS": {"kaynak": "../edg037_tca_2026-08-13/sonuc.json",
                               "sha256_16": sha16(os.path.join(BURASI, "..", "edg037_tca_2026-08-13", "sonuc.json")),
                               "slipaj_giris_bps_vs_resmi_acilis": e037_ozet,
                               "satir_sayisi": len(e037_satir)},
        "KANONIK": {
            "secim": "D1_konsolide_acilis",
            "on_kayit": "research/cards/EDG-2026-038-tca-konsolide-cikis.yaml → kanonik_olcut_on_kayit",
            "curutme_kosullari_gerceklesti_mi": curutuldu or "HAYIR — hiçbiri gerçekleşmedi",
            "gecerli": not curutuldu,
        },
    }


# =================================================================================================
# [B] ÇIKIŞ BACAĞI — anatomi, yaşam döngüsü, korumasız pencere, dolum (varsa)
# =================================================================================================
def _iso(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def b_cikis(ham: dict, mv: dict) -> dict:
    emirler = ((ham.get("alpaca") or {}).get("orders") or {}).get("satirlar") or []
    akt = ((ham.get("alpaca") or {}).get("activities") or {})
    fills = (akt.get("FILL") or {}).get("kayitlar") or []

    # --- (iii) GERÇEK ÇIKIŞ DOLUMU var mı? (dolum OLAYI düzeyi — kısmi dolumlar dahil)
    satis_dolum = [a for a in fills if str(a.get("side", "")).startswith("sell")]
    # --- emir düzeyi: motorun gönderdiği SATIŞ emirleri
    def _motor_satis(o):
        coid = str(o.get("client_order_id") or "")
        if o.get("side") != "sell":
            return False
        if coid.startswith("P-"):                        # koruma OCO limit bacağı (P-KORUMA-*)
            return True
        # bracket/OCO koruma bacakları Alpaca UUID coid'i taşır → EBEVEYN bağı ya da sembol/ölçek
        # ile tanınır. Burada: motor sembollerinde (dört isim) olan tüm sell'ler + F tatbikatları
        # DIŞLANIR (aşağıdaki `_tatbikat`).
        return str(o.get("symbol")).upper() in {"NUE", "EMR", "BKNG", "AMGN"}

    def _tatbikat(o):
        return str(o.get("symbol")).upper() == "F" or str(o.get("client_order_id") or "").startswith(
            ("RECON-SMOKE", "DRILL-", "STREAM-DRILL"))

    motor_satis = [o for o in emirler if _motor_satis(o) and not _tatbikat(o)]
    disi_satis = [o for o in emirler if o.get("side") == "sell" and _tatbikat(o)]
    from collections import Counter
    durum = dict(Counter(str(o.get("status")) for o in motor_satis))

    # --- (i) KORUMA BACAKLARININ ANATOMİSİ (canlı kayıttan, kod alıntısıyla)
    anatomi_satir = []
    for o in motor_satis:
        anatomi_satir.append({k: o.get(k) for k in
                              ("client_order_id", "symbol", "type", "order_class", "time_in_force",
                               "limit_price", "stop_price", "status", "created_at", "submitted_at",
                               "canceled_at", "expired_at", "filled_at", "filled_qty")})
    stop_bacaklari = [r for r in anatomi_satir if r["type"] == "stop"]
    limit_bacaklari = [r for r in anatomi_satir if r["type"] == "limit"]
    stop_limitsiz = [r for r in stop_bacaklari if r.get("limit_price") in (None, "", "None")]

    # --- (ii) KORUMA YAŞAM DÖNGÜSÜ ve KORUMASIZ PENCERE
    # pozisyon açılış anı = giriş emrinin filled_at'i; sonra koruma emirlerinin canlı olduğu
    # aralıklar hesaplanır. "Canlı" = [submitted/created, canceled/expired) ya da hâlâ açık.
    girisler = {}
    for o in emirler:
        coid = str(o.get("client_order_id") or "")
        if coid.startswith("P-2026-") and o.get("side") == "buy" and o.get("filled_at"):
            girisler[str(o.get("symbol")).upper()] = _iso(o.get("filled_at"))
    simdi = _iso(ham.get("cekim_zamani")) or dt.datetime.now(dt.timezone.utc)

    def _seans_saati(a: dt.datetime, b: dt.datetime) -> float:
        """[a,b) aralığının NORMAL SEANS saati (13:30-20:00Z, hafta içi). Tatil takvimi YOK —
        beyan: resmî tatiller düşülmemiştir (bu pencerede ABD tatili yok: 08-06..08-13)."""
        if b <= a:
            return 0.0
        top, gun = 0.0, a.date()
        while gun <= b.date():
            if gun.weekday() < 5:
                ac = dt.datetime.combine(gun, dt.time(13, 30), dt.timezone.utc)
                ka = dt.datetime.combine(gun, dt.time(20, 0), dt.timezone.utc)
                lo, hi = max(a, ac), min(b, ka)
                if hi > lo:
                    top += (hi - lo).total_seconds() / 3600.0
            gun += dt.timedelta(days=1)
        return round(top, 3)

    ciplak: dict = {}
    for sym, t0 in sorted(girisler.items()):
        araliklar = []
        for o in motor_satis:
            if str(o.get("symbol")).upper() != sym:
                continue
            bas = _iso(o.get("created_at")) or _iso(o.get("submitted_at"))
            son = _iso(o.get("canceled_at")) or _iso(o.get("expired_at")) or simdi
            if bas and son > bas:
                araliklar.append((max(bas, t0), son))
        araliklar.sort()
        birlesik = []
        for a, b in araliklar:
            if birlesik and a <= birlesik[-1][1]:
                birlesik[-1] = (birlesik[-1][0], max(birlesik[-1][1], b))
            else:
                birlesik.append((a, b))
        bosluk, imlec = [], t0
        for a, b in birlesik:
            if a > imlec:
                bosluk.append((imlec, a))
            imlec = max(imlec, b)
        if imlec < simdi:
            bosluk.append((imlec, simdi))
        ciplak[sym] = {
            "pozisyon_acildi": t0.isoformat(),
            "koruma_canli_araliklari": [[a.isoformat(), b.isoformat()] for a, b in birlesik],
            "korumasiz_pencereler": [{"bas": a.isoformat(), "son": b.isoformat(),
                                      "duvar_saati": round((b - a).total_seconds() / 3600, 3),
                                      "SEANS_saati": _seans_saati(a, b)} for a, b in bosluk],
            "korumasiz_toplam_duvar_saati": round(sum((b - a).total_seconds() / 3600 for a, b in bosluk), 3),
            "korumasiz_toplam_SEANS_saati": round(sum(_seans_saati(a, b) for a, b in bosluk), 3),
        }
    en_uzun = max((v["korumasiz_toplam_SEANS_saati"] for v in ciplak.values()), default=0.0)

    # --- korumanın YENİDEN kurulma yolu: OTOMATİK mi, OPERATÖR mü?
    yeniden_kurma = {
        "cagri_yeri": "meridian/api.py:4564 — `alpaca.submit_protective_oco(...)`",
        "tek_cagiran": "meridian/api.py:4513 `koruma_kur(onay, oneri_id, onaylayan)`",
        "http_ucu": "POST /api/alpaca/koruma_kur (api.py:4636)",
        "kapi_sayisi": 3,
        "kapilar": ["1) ölçüm — broker okunamazsa emir YOK",
                    "2) ONAY JETONU — jetonsuz çağrı KURU KOŞU (hiçbir emir gitmez)",
                    "3) ÖNERİ KİMLİĞİ — o ölçüme ait `oneri_id` eşleşmezse emir GİTMEZ"],
        "OTOMATIK_MI": False,
        "beyan": "Depoda `submit_protective_oco`yu çağıran BAŞKA yol YOK (tarama: yalnız api.py:4564 "
                 "+ testler). Yani `tif=day` korumayı öldürdüğünde koruma KENDİLİĞİNDEN kurulmaz — "
                 "operatörün panodan onay jetonuyla basması gerekir. Bekçi (`watchdog.py:2418-2583` "
                 "`korumasiz_pozisyon` alarmı) durumu GÖRÜR ve alarm üretir ama KURMAZ.",
        "bekci": "meridian/watchdog.py:2435-2522 — `korumasiz/toplam` + payda beyanı; alarm "
                 "`kind=korumasiz_pozisyon`",
    }

    # --- REPLAY'İN ÇIKIŞ VARSAYIMI (asimetri kalemi)
    asimetri = {
        "giris_bacagi_canli": "type=limit (bracket) — ödenen fiyat LİMİTLE TAVANLI "
                              "(alpaca.py:347-348; canlı 4/4 emir `type=limit`)",
        "cikis_stop_bacagi_canli": f"type=stop, limit_price=null → tetiklenince MARKET, TAVANSIZ "
                                   f"(alpaca.py:1024 gövdede yalnız `stop_price`; canlı kayıtta "
                                   f"{len(stop_limitsiz)}/{len(stop_bacaklari)} stop bacağında "
                                   f"limit_price boş)",
        "replay_giris": "broker.py:515 — `base_fill = next_open * (1.0 + self.slip)`  (slip=5 bps)",
        "replay_cikis": "broker.py:669 — `exit_fill = raw_exit * (1.0 - self.slip)`   (AYNI 5 bps)",
        "replay_stop_dokunusu": "broker.py:596 — bar-içi stop dokunuşunda çıkış `eff_stop` kabul "
                                "edilir; stop-tetik SLİPAJI SIFIR varsayılır, üstüne yalnız 5 bps düşülür",
        "HUKUM_YOK_SERHI": "Giriş LİMİT (tavanlı) ama çıkış MARKET (tavansız) olduğu için replay'in "
                           "SİMETRİK 5 bps varsayımı çıkış bacağında YAPISAL OLARAK daha iyimser "
                           "OLABİLİR. 'Olabilir' — çünkü ÖLÇÜLMEDİ (aşağıdaki n). Bu satır bir "
                           "mekanizma beyanıdır, bir sayı değildir.",
    }

    # --- n=0'IN MEKANİK NEDENİ: seviyeler HİÇ DEĞDİ Mİ? (ölü emir ≠ ulaşılmayan fiyat)
    # İki neden AYRI ölçülür: emir ölü olduğu için mi dolmadı, yoksa fiyat hiç ulaşmadığı için mi?
    seviyeler: dict = {}
    for sym in sorted({str(o.get("symbol")).upper() for o in motor_satis}):
        stops = [float(o["stop_price"]) for o in motor_satis
                 if str(o.get("symbol")).upper() == sym and o.get("stop_price")]
        limits = [float(o["limit_price"]) for o in motor_satis
                  if str(o.get("symbol")).upper() == sym and o.get("limit_price")]
        barlar = (mv.get("tutus_gunluk_0806_0812") or {}).get(sym) or []
        if not (stops and limits and barlar):
            seviyeler[sym] = {"_olculemedi": "stop/hedef seviyesi ya da tutuş barı yok"}
            continue
        stop, hedef = min(stops), max(limits)
        en_dusuk = min(float(b["l"]) for b in barlar)
        en_yuksek = max(float(b["h"]) for b in barlar)
        seviyeler[sym] = {
            "stop": stop, "hedef": hedef,
            "seans_n": len(barlar), "kapsam": [barlar[0]["d"], barlar[-1]["d"]],
            "en_dusuk": en_dusuk, "en_yuksek": en_yuksek,
            "stopa_en_yakin_bps": round((en_dusuk / stop - 1.0) * 1e4, 1),
            "hedefe_en_yakin_bps": round((en_yuksek / hedef - 1.0) * 1e4, 1),
            "stop_degdi_mi": bool(en_dusuk <= stop),
            "hedef_degdi_mi": bool(en_yuksek >= hedef),
        }
    hic_degmedi = all(not v.get("stop_degdi_mi") and not v.get("hedef_degdi_mi")
                      for v in seviyeler.values() if "_olculemedi" not in v)

    n = len(satis_dolum)
    return {
        "olculdu": bool(n >= KART_ESIK_CIKIS_N),
        "n": n,
        "DAMGA": (f"ÖLÇÜLEMEDİ (n={n}) — kart eşiği n≥{KART_ESIK_CIKIS_N}" if n < KART_ESIK_CIKIS_N
                  else f"ölçüldü (n={n})"),
        "neden": None if n >= KART_ESIK_CIKIS_N else (
            "Motorun gönderdiği HİÇBİR satış emri bugüne dek dolmadı. Hesabın TÜM dolum geçmişinde "
            f"({len(fills)} FILL olayı) satış tarafı SIFIRdır — dört pozisyon (NUE/EMR/BKNG/AMGN) "
            "2026-08-06'dan beri AÇIK, koruma bacakları ne stop'a ne hedefe değdi. Çıkış slipajı "
            "için tek bir gözlem bile yok; sayı UYDURULMAZ ve giriş sayısı çıkışa KOPYALANMAZ."),
        "gonderilen_motor_satis_emri": len(motor_satis),
        "dolan_motor_satis_emri": sum(1 for o in motor_satis if str(o.get("status")) == "filled"),
        "satis_emir_status_dagilim": durum,
        "dislanan_tatbikat_satis_emri": len(disi_satis),
        "tum_FILL_olayi": len(fills),
        "FILL_side_dagilim": dict(Counter(str(a.get("side")) for a in fills)),
        "i_koruma_bacagi_anatomisi": {
            "kod": {
                "gonderim": "meridian/adapters/alpaca.py:979-1035 `submit_protective_oco`",
                "govde": "alpaca.py:1021-1025 — {type:'limit', time_in_force:KORUMA_TIF, "
                         "order_class:'oco', take_profit:{limit_price}, stop_loss:{stop_price}}",
                "KORUMA_TIF": (ham.get("alpaca") or {}).get("KORUMA_TIF"),
                "KORUMA_TIF_kod": "alpaca.py:955 — `KORUMA_TIF = \"gtc\"` (ENTRY_TIF'ten TÜRETİLMEZ)",
                "stop_bacagi_limitsiz": "alpaca.py:1024 — `\"stop_loss\": {\"stop_price\": round(sl, 2)}` "
                                        "— gövdede `limit_price` YOK ⇒ tetiklenince MARKET",
                "giris_bracket_TIF": "broker.py:96 `ENTRY_TIF='gtc'` · :102 `ENTRY_TIF_ALLOWED=('gtc',)` "
                                     "(E1-v2, 2026-08-07 kelepçesi)",
            },
            "canli": {
                "stop_bacagi_n": len(stop_bacaklari), "limit_bacagi_n": len(limit_bacaklari),
                "stop_bacaginda_limit_price_bos": len(stop_limitsiz),
                "tif_dagilim": dict(Counter(str(r.get("time_in_force")) for r in anatomi_satir)),
                "order_class_dagilim": dict(Counter(str(r.get("order_class")) for r in anatomi_satir)),
                "acik_stop_bacagi_status": dict(Counter(str(r.get("status")) for r in stop_bacaklari
                                                        if r.get("status") in ("new", "held", "accepted"))),
                "acik_limit_bacagi_status": dict(Counter(str(r.get("status")) for r in limit_bacaklari
                                                         if r.get("status") in ("new", "held", "accepted"))),
                "satirlar": sorted(anatomi_satir, key=lambda r: str(r.get("created_at") or "")),
            },
            "OLCULEMEDI_held_semantigi": {
                "gozlem": "Yürürlükteki dört OCO'nun STOP bacağı `status=held`, LİMİT bacağı "
                          "`status=new`. Depo bu yapıyı 2026-08-09'da ölçmüş ve belgelemiş "
                          "(alpaca.py:435-448: primary=limit/accepted, legs[0]=stop/held).",
                "olculemeyen": "`held` bacağının tetiklendiğinde GERÇEKTEN piyasaya çıkıp çıkmadığı "
                               "BU VERİDEN doğrulanamaz — hiçbir stop bugüne dek tetiklenmedi (n=0). "
                               "'Koruma ayakta' cümlesi broker'ın belgelenmiş davranışına dayanıyor, "
                               "BİZİM ÖLÇÜMÜMÜZE değil. Uydurma yasağı: bu satır bir varsayımdır ve "
                               "öyle etiketlenmiştir.",
            },
        },
        "ii_koruma_yasam_dongusu": {
            "ciplak_pencere_esigi_seans": KART_ESIK_CIPLAK_SEANS,
            "seans_tanimi": "13:30-20:00Z hafta içi (6,5 saat/seans); resmî tatil düşülmedi "
                            "(2026-08-06..13 aralığında ABD borsa tatili yok)",
            "pozisyon_basina": ciplak,
            "en_uzun_korumasiz_SEANS_saati": en_uzun,
            "en_uzun_korumasiz_SEANS_orani": round(en_uzun / 6.5, 3),
            "esik_asildi_mi": bool(en_uzun / 6.5 > KART_ESIK_CIPLAK_SEANS),
            "yeniden_kurma_yolu": yeniden_kurma,
        },
        "iii_cikis_slipaji": {
            "n": n, "satirlar": satis_dolum,
            "payda": None if n == 0 else "kanonik ölçüt (konsolide) — çıkış günü barlarından",
            "cikis_gunu_barlari": (ham.get("cikis_gunu_barlari") or {}).get("n_gun"),
        },
        "n0_MEKANIK_NEDENI": {
            "soru": "Emir ölü olduğu için mi dolmadı, yoksa fiyat seviyeye hiç ulaşmadığı için mi? "
                    "İKİ AYRI NEDEN — ikisi de doğru olabilir, ikisi de ölçülür.",
            "kaynak": "Massive günlük barlar 2026-08-06..08-12 (massive_capraz.json; 2026-08-13 "
                      "seansı HENÜZ KAPANMADI, kapsam DIŞI)",
            "pozisyon_basina": seviyeler,
            "HICBIR_SEVIYE_DEGMEDI": hic_degmedi,
            "hüküm": ("BAĞLAYICI KISIT TUTUŞ SÜRESİ, EMİR ÖMRÜ DEĞİL: beş seansın hiçbirinde "
                      "hiçbir pozisyonun stop'u ya da hedefi DEĞMEDİ. Yani korumalar kesintisiz "
                      "canlı kalsaydı DA çıkış dolumu n=0 olurdu. EDG-037'nin n=0'ı `ENTRY_TIF=day` "
                      "kelepçesine bağlaması EKSİK bir teşhistir — kelepçe KORUMA boşluğu üretti "
                      "(§ii), ama ÖLÇÜM boşluğunu üreten şey o değil, fiyatın hiçbir seviyeye "
                      "ulaşmamasıdır." if hic_degmedi else
                      "EN AZ BİR SEVİYE DEĞDİ — emir ölü olduğu için kaçırılmış bir çıkış VAR; "
                      "aşağıdaki satırlara bak."),
        },
        "ASIMETRI": asimetri,
    }


# =================================================================================================
# [C] PF ETKİSİ — kanonik farkla, giriş/çıkış bacakları AYRI parametreli
# =================================================================================================
def _bar_ac(ticker: str, tarih: str, onbellek: dict) -> float | None:
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


def c_pf(ham: dict, a: dict, b: dict) -> dict:
    with open(ISLEMLER_032) as f:
        rows = json.load(f)
    slip_bps = float((ham.get("friksiyon_ayari") or {}).get("slippage_bps") or 0)
    kanonik = a["KANONIK"]["secim"]
    # BİRİNCİL FARK = B (yalnız icra). GEREKÇE, ÖLÇÜMDEN ÖNCE DEĞİL SONRA YAZILDIĞI İÇİN AÇIK:
    # A farkı modelin BAR hatasını da içeriyor ve o hata bir VERİ-SAĞLAYICI sapmasıdır — n=4'te
    # işareti belirlenemeyen, ortalaması ~0'a yakın bir gürültü. 4 gözlemlik bir bar-hatası
    # tahminini 885 işleme yaymak, ölçmediğimiz bir sistematiği varsaymak olurdu. İKİSİ DE
    # raporlanır; hangisi seçilirse seçilsin duyarlılık YÜZEYİ aynıdır (yalnız yüzeydeki NOKTA değişir).
    farkB = a["olcutler"][kanonik]["FARK_B_yalniz_icra"]
    farkA = a["olcutler"][kanonik]["FARK_A_payda_ozdes"]
    fark = farkB
    d_ort, d_med, d_w = fark.get("ortalama"), fark.get("medyan"), fark.get("agirlikli_ortalama")
    d_min, d_max = fark.get("min"), fark.get("max")
    a_ort, a_w = farkA.get("ortalama"), farkA.get("agirlikli_ortalama")

    onbellek: dict = {}
    n_bar_yok, n_ok, sadakat_ok, sadakat_test = 0, 0, 0, 0
    for t in rows:
        ac = _bar_ac(t["ticker"], t["ts_open"], onbellek)
        if ac is None or ac <= 0:
            n_bar_yok += 1
            t["_ng"] = t["_nc"] = None
            continue
        n_ok += 1
        ng = ac * (1.0 + slip_bps / 1e4) * float(t["qty"])
        nc = ng + float(t["pnl_dollars"])
        t["_ng"], t["_nc"] = ng, max(0.0, nc)
        kap = onbellek[str(t["ticker"]).lower()].get(str(t["ts_close"]))
        if kap:
            sadakat_test += 1
            px = nc / float(t["qty"])
            if float(kap["low"]) * 0.98 <= px <= float(kap["high"]) * 1.02:
                sadakat_ok += 1

    def _pf(pnls):
        p = sum(x for x in pnls if x > 0)
        n = sum(x for x in pnls if x < 0)
        return None if n == 0 else round(p / abs(n), 4)

    taban = [float(t["pnl_dollars"]) for t in rows]

    def senaryo(giris_bps: float, cikis_bps: float) -> dict:
        """ASİMETRİK: giriş bacağına `giris_bps`, çıkış bacağına `cikis_bps` EK friksiyon."""
        adj, atlanan = [], 0
        for t in rows:
            ng, nc = t.get("_ng"), t.get("_nc")
            if ng is None:
                atlanan += 1
                continue
            ek = giris_bps / 1e4 * ng + cikis_bps / 1e4 * nc
            adj.append(float(t["pnl_dollars"]) - ek)
        return {"giris_ek_bps": round(giris_bps, 4), "cikis_ek_bps": round(cikis_bps, 4),
                "n": len(adj), "atlanan_bar_yok": atlanan,
                "brut_kazanc": round(sum(x for x in adj if x > 0), 2),
                "brut_kayip": round(sum(x for x in adj if x < 0), 2),
                "net": round(sum(adj), 2), "pf": _pf(adj),
                "kazanan_n": sum(1 for x in adj if x > 0), "kaybeden_n": sum(1 for x in adj if x < 0)}

    def basabas_cikis(giris_bps: float) -> float | None:
        """Verilen giriş ek-friksiyonunda PF'i 1,0'a indiren ÇIKIŞ ek-friksiyonu (ikili arama)."""
        lo, hi = 0.0, 2000.0
        if (senaryo(giris_bps, 0.0)["pf"] or 0) <= 1.0:
            return 0.0                       # giriş tek başına zaten başabaşın altına indirmiş
        if (senaryo(giris_bps, hi)["pf"] or 0) > 1.0:
            return None
        for _ in range(60):
            orta = (lo + hi) / 2
            if (senaryo(giris_bps, orta)["pf"] or 0) > 1.0:
                lo = orta
            else:
                hi = orta
        return round((lo + hi) / 2, 2)

    def basabas_simetrik() -> float | None:
        lo, hi = 0.0, 500.0
        if (senaryo(hi, hi)["pf"] or 0) > 1.0:
            return None
        for _ in range(60):
            orta = (lo + hi) / 2
            if (senaryo(orta, orta)["pf"] or 0) > 1.0:
                lo = orta
            else:
                hi = orta
        return round((lo + hi) / 2, 2)

    def basabas_yalniz_giris() -> float | None:
        lo, hi = 0.0, 2000.0
        if (senaryo(hi, 0.0)["pf"] or 0) > 1.0:
            return None
        for _ in range(60):
            orta = (lo + hi) / 2
            if (senaryo(orta, 0.0)["pf"] or 0) > 1.0:
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
        "K1_kanonik_ORTALAMA_yalniz_giris": {
            **senaryo(d_ort, 0.0),
            "aciklama": "KANONİK (konsolide açılış) ortalama fark YALNIZ giriş bacağına — çıkış "
                        "ÖLÇÜLMEDİ (n=0), bu yüzden bu senaryo ALT SINIR",
        },
        "K2_kanonik_MEDYAN_yalniz_giris": {
            **senaryo(d_med, 0.0),
            "aciklama": "kanonik medyan fark yalnız girişe (uç gözlemin etkisi kırpılmış)",
        },
        "K3_kanonik_AGIRLIKLI_yalniz_giris": {
            **senaryo(d_w, 0.0),
            "aciklama": "kanonik notional-ağırlıklı fark yalnız girişe — dolar etkisine en yakın okuma",
        },
        "K4_kanonik_ORTALAMA_SIMETRIK_VARSAYIM": {
            **senaryo(d_ort, d_ort),
            "aciklama": "VARSAYIM (ölçüm DEĞİL): aynı fark her iki bacağa. Çıkış bacağı n=0 — bu "
                        "satır 'çıkış girişe benzeseydi' der, 'çıkış böyle' DEMEZ",
        },
        "K5_kanonik_AGIRLIKLI_SIMETRIK_VARSAYIM": {
            **senaryo(d_w, d_w),
            "aciklama": "VARSAYIM: notional-ağırlıklı fark her iki bacağa",
        },
        "K6_EN_IYI_gozlem_yalniz_giris": {
            **senaryo(d_min, 0.0),
            "aciklama": "dört gözlemin EN LEHTE olanı yalnız girişe — 'en iyimser okuma bile ne "
                        "yapar'. Kanonik ölçütte bu gözlem NEGATİF (NUE): dolum konsolide açılışın "
                        "ALTINDA gerçekleşti, yani o işlemde icra modelden İYİydi.",
        },
        "K7_E3_kotumser_bant_referans": {
            **senaryo(5.0, 5.0),
            "aciklama": "goal.pessimistic_band_v2'nin varsaydığı EK 5 bps/bacak — bu kart ÖNCESİ "
                        "elimizdeki en kötümser sayı; kıyas çıpası",
        },
        "A1_farkA_payda_ozdes_ORTALAMA_yalniz_giris": {
            **senaryo(a_ort, 0.0),
            "aciklama": "ALTERNATİF FARK TANIMI (A): modelin BAR hatası DAHİL. Aynı yüzeyin başka "
                        "bir noktası — okuyucu iki tanımın PF sonucunu yan yana görsün diye.",
        },
        "A2_farkA_payda_ozdes_AGIRLIKLI_yalniz_giris": {
            **senaryo(a_w, 0.0),
            "aciklama": "ALTERNATİF FARK TANIMI (A), notional-ağırlıklı",
        },
    }

    # --- ASİMETRİK DUYARLILIK YÜZEYİ: PF(giriş ek bps, çıkış ek bps)
    eksen = [0, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 75, 100]
    yuzey = {}
    for g in eksen:
        yuzey[str(g)] = {str(c): senaryo(float(g), float(c))["pf"] for c in eksen}

    # --- BAŞABAŞ EĞRİSİ: her giriş ek-bps'i için PF=1,0 veren çıkış ek-bps'i
    egri = {str(g): basabas_cikis(float(g)) for g in
            [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 19, 20, 25, 30, 40, 50]}

    return {
        "taban_defter": {"kaynak": os.path.relpath(ISLEMLER_032, BURASI), "n": len(rows),
                         "sha256_16": sha16(ISLEMLER_032),
                         "tarih_araligi": [min(t["ts_open"] for t in rows), max(t["ts_close"] for t in rows)]},
        "kanonik_olcut": kanonik,
        "kullanilan_fark": {
            "BIRINCIL": "FARK_B_yalniz_icra (gerçek_bps − 5 bps nominal)",
            "gerekce": "FARK_A modelin BAR hatasını da taşır; o hata bir veri-sağlayıcı sapmasıdır "
                       "ve n=4'te işareti belirlenemez (ortalama ~+2 bps, medyan ~0). Dört gözlemlik "
                       "bir bar-hatası tahminini 885 işleme yaymak, ölçmediğimiz bir sistematiği "
                       "varsaymak olurdu. İKİ TANIM DA senaryolarda var (K* = B, A* = A).",
            "B_ortalama": d_ort, "B_medyan": d_med, "B_notional_agirlikli": d_w,
            "B_min": d_min, "B_max": d_max, "B_n": fark.get("n"),
            "B_t_ci95": fark.get("t_ci95"), "B_bootstrap_ci95": fark.get("bootstrap_ci95"),
            "A_ortalama": a_ort, "A_notional_agirlikli": a_w, "A_t_ci95": farkA.get("t_ci95"),
            "model_bar_hatasi": a["olcutler"][kanonik]["MODEL_BAR_HATASI"],
            "serh": f"n={fark.get('n')} — NOKTA TAHMİNİ, dağılım değil",
        },
        "notional_turetme": {
            "yontem": "giriş notional = qty × açılış(ts_open) × (1+slippage_bps/1e4) — motorun KENDİ "
                      "dolum yasası (broker.py:515). çıkış notional = giriş notional + pnl_dollars "
                      "— KİMLİK (komisyon 0 + scale_out_frac 0,0).",
            "bar_kaynagi": os.path.relpath(BARS_032, BURASI), "bar_bulunan": n_ok, "bar_yok": n_bar_yok,
            "sadakat_sinamasi": {"test_edilen": sadakat_test, "gecen": sadakat_ok,
                                 "oran": None if not sadakat_test else round(sadakat_ok / sadakat_test, 4),
                                 "olcut": "türetilen çıkış fiyatı, ts_close barının [low×0,98, high×1,02] aralığında mı"},
        },
        "senaryolar": senaryolar,
        "asimetrik_duyarlilik_yuzeyi_pf": {
            "eksen_birim": "satır = GİRİŞ bacağına ek bps · sütun = ÇIKIŞ bacağına ek bps "
                           "(ikisi de yürürlükteki 5 bps'in ÜSTÜNE)",
            "yuzey": yuzey,
            "not": "PF her iki eksende MONOTON AZALANDIR — hiçbir friksiyon varsayımı S0'ın "
                   "üstüne çıkamaz; tartışma yalnız 'ne kadar aşağıda' sorusudur",
        },
        "basabas_egrisi": {
            "aciklama": "verilen GİRİŞ ek-friksiyonunda PF'i tam 1,0'a indiren ÇIKIŞ ek-friksiyonu "
                        "(bps/bacak). 0.0 = giriş TEK BAŞINA başabaşı zaten geçmiş; null = 2000 "
                        "bps'e kadar çıkış eklense bile PF>1 (gerçekleşmez).",
            "egri": egri,
            "basabas_simetrik": basabas_simetrik(),
            "basabas_yalniz_giris": basabas_yalniz_giris(),
        },
        "esik_baglami": {"RESULT_PF_MIN": 1.3, "kod": "meridian/analytics.py:2089-2093",
                         "not": "Bu kart HÜKÜM VERMEZ. Senaryolar eşik tartışmasının GİRDİSİdir."},
    }


# =================================================================================================
def main() -> None:
    with open(HAM) as f:
        ham = json.load(f)
    with open(MASSIVE) as f:
        mv = json.load(f)
    with open(EDG037) as f:
        e037 = json.load(f)

    a = a_olcut(ham, mv, e037)
    b = b_cikis(ham, mv)
    c = c_pf(ham, a, b)

    kanonik = a["KANONIK"]["secim"]
    ko = a["olcutler"][kanonik]
    out = {
        "kart": "EDG-2026-038",
        "kart_yolu": "research/cards/EDG-2026-038-tca-konsolide-cikis.yaml",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "modul": os.path.abspath(__file__),
        "ham_kanit": {
            "canli": {"dosya": "canli_ham.json", "sha256_16": sha16(HAM),
                      "cekim_zamani": ham.get("cekim_zamani"),
                      "cekim_betigi": "canli_cek.py (canlıda SALT-OKUMA, stdin deseni)"},
            "massive": {"dosya": "massive_capraz.json", "sha256_16": sha16(MASSIVE),
                        "kaynak": "Massive MCP — Alpaca'dan BAĞIMSIZ ikinci konsolide kaynak"},
            "edg037": {"dosya": "../edg037_tca_2026-08-13/sonuc.json", "sha256_16": sha16(EDG037)},
        },
        "K_sayimi": "K += 0 — betimsel ölçüm + ölçüt düzeltmesi (kart parameter_grid: yok)",
        "OZET_TABLO": {
            "kanonik_olcut": kanonik,
            "kanonik_gecerli": a["KANONIK"]["gecerli"],
            "kanonik_curutme": a["KANONIK"]["curutme_kosullari_gerceklesti_mi"],
            "olcut_kiyasi_medyan_bps": {ad: v["GERCEK_vs_payda_bps"]["medyan"]
                                        for ad, v in a["olcutler"].items()},
            "olcut_kiyasi_aleyhte_n": {ad: v["GERCEK_vs_payda_bps"]["isaret_testi"]["aleyhte"]
                                       for ad, v in a["olcutler"].items()},
            "olcut_hatasi_IEX_vs_konsolide_max_bps": a["olcut_hatasi_IEX_vs_konsolide"]["max_mutlak_bps"],
            "capraz_iki_kaynak_max_bps": a["capraz_kontrol_iki_konsolide_kaynak"]["max_sapma_bps"],
            "KANONIK_slipaj": ko["GERCEK_vs_payda_bps"],
            "KANONIK_farkB_yalniz_icra": ko["FARK_B_yalniz_icra"],
            "KANONIK_farkA_payda_ozdes": ko["FARK_A_payda_ozdes"],
            "KANONIK_model_bar_hatasi": ko["MODEL_BAR_HATASI"],
            "cikis_bacagi": {"n": b["n"], "DAMGA": b["DAMGA"],
                             "gonderilen_motor_satis_emri": b["gonderilen_motor_satis_emri"],
                             "en_uzun_korumasiz_SEANS_saati":
                                 b["ii_koruma_yasam_dongusu"]["en_uzun_korumasiz_SEANS_saati"],
                             "koruma_otomatik_kuruluyor_mu":
                                 b["ii_koruma_yasam_dongusu"]["yeniden_kurma_yolu"]["OTOMATIK_MI"],
                             "hicbir_seviye_degmedi": b["n0_MEKANIK_NEDENI"]["HICBIR_SEVIYE_DEGMEDI"]},
            "pf": {k: v.get("pf") for k, v in c["senaryolar"].items()},
            "basabas_simetrik": c["basabas_egrisi"]["basabas_simetrik"],
            "basabas_yalniz_giris": c["basabas_egrisi"]["basabas_yalniz_giris"],
            "kill": {
                "kill1_konsolide_cekilemedi": bool((ham.get("gunluk_bar_sip") or {}).get("_hata")),
                "kill2_iki_kaynak_ayristi": a["capraz_kontrol_iki_konsolide_kaynak"]["tetiklendi"],
                "kill3_olcut_krizi_curudu": a["olcut_hatasi_IEX_vs_konsolide"]["kill3_curudu_mu"],
                "kill4_cikis_n_5_alti": bool(b["n"] < KART_ESIK_CIKIS_N),
                "kill5_kanonik_post_hoc_degisti": bool(a["KANONIK"]["gecerli"] is False),
            },
        },
        "a_olcut": a,
        "b_cikis_bacagi": b,
        "c_pf_etkisi": c,
        "HUKUM": "YOK — bu kart eşiği DEĞİŞTİRMEZ, yapılandırma ÖNERMEZ (kart success_metric). "
                 "Ürün: sayı + künye + fark. Hükmü Rol-1 işler.",
    }
    with open(os.path.join(BURASI, "sonuc.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)

    # ---- konsol özeti
    print("=" * 100)
    print("EDG-2026-038 · TCA tur-2 — ÖLÇÜM ÖZETİ")
    print("=" * 100)
    print("\n[A] ÜÇ PAYDA + IEX (giriş bacağı, n=%d emir)" % len(a["dolumlar"]))
    print("%-34s %9s %9s %9s %9s %6s %20s" % ("ölçüt", "medyan", "ortalama", "ağırlık.", "p90",
                                              "aleyh", "t-CI95"))
    for ad, v in a["olcutler"].items():
        g = v["GERCEK_vs_payda_bps"]
        ci = g["t_ci95"] or {}
        print("%-34s %9s %9s %9s %9s %4d/%d %20s" % (ad, g["medyan"], g["ortalama"],
                                                     g["agirlikli_ortalama"], g["p90"],
                                                     g["isaret_testi"]["aleyhte"], g["isaret_testi"]["n"],
                                                     f"[{ci.get('lo')};{ci.get('hi')}]"))
    print("\n  ölçüt hatası (IEX−konsolide) max |bps| =",
          a["olcut_hatasi_IEX_vs_konsolide"]["max_mutlak_bps"],
          "· eşik", KART_ESIK_OLCUT_BPS, "· kill3 çürüdü mü:",
          a["olcut_hatasi_IEX_vs_konsolide"]["kill3_curudu_mu"])
    print("  çapraz (Alpaca SIP vs Massive) max |bps| =",
          a["capraz_kontrol_iki_konsolide_kaynak"]["max_sapma_bps"],
          "· açılışta:", a["capraz_kontrol_iki_konsolide_kaynak"].get("acilis_max_sapma_bps"))
    print("  MODELE YAKINLIK (medyan |bps| modelin kendi paydasına):")
    for ad, v in a["kanonik_secim_sinamasi_MODELE_YAKINLIK"]["ozet"].items():
        print("    %-34s %s" % (ad, v))
    print("  KANONİK:", a["KANONIK"]["secim"], "· geçerli:", a["KANONIK"]["gecerli"],
          "· çürütme:", a["KANONIK"]["curutme_kosullari_gerceklesti_mi"])

    print("\n[B] ÇIKIŞ BACAĞI —", b["DAMGA"])
    print("  motor satış emri:", b["gonderilen_motor_satis_emri"], "· dolan:",
          b["dolan_motor_satis_emri"], "·", b["satis_emir_status_dagilim"])
    print("  stop bacağı limit_price boş:",
          b["i_koruma_bacagi_anatomisi"]["canli"]["stop_bacaginda_limit_price_bos"], "/",
          b["i_koruma_bacagi_anatomisi"]["canli"]["stop_bacagi_n"], "· TIF:",
          b["i_koruma_bacagi_anatomisi"]["canli"]["tif_dagilim"])
    for sym, v in b["ii_koruma_yasam_dongusu"]["pozisyon_basina"].items():
        print("  %-5s korumasız: %.3f seans-saati (duvar %.2f s) · pencere n=%d"
              % (sym, v["korumasiz_toplam_SEANS_saati"], v["korumasiz_toplam_duvar_saati"],
                 len(v["korumasiz_pencereler"])))
    print("  en uzun korumasız:", b["ii_koruma_yasam_dongusu"]["en_uzun_korumasiz_SEANS_saati"],
          "seans-saati =", b["ii_koruma_yasam_dongusu"]["en_uzun_korumasiz_SEANS_orani"], "seans",
          "· eşik aşıldı mı:", b["ii_koruma_yasam_dongusu"]["esik_asildi_mi"])
    print("  koruma OTOMATİK kuruluyor mu:",
          b["ii_koruma_yasam_dongusu"]["yeniden_kurma_yolu"]["OTOMATIK_MI"])
    print("  n=0 MEKANİK NEDENİ — hiçbir seviye değmedi mi:",
          b["n0_MEKANIK_NEDENI"]["HICBIR_SEVIYE_DEGMEDI"])
    for sym, v in b["n0_MEKANIK_NEDENI"]["pozisyon_basina"].items():
        if "_olculemedi" in v:
            print("    %-5s ÖLÇÜLEMEDİ: %s" % (sym, v["_olculemedi"]))
        else:
            print("    %-5s stop %.2f (en yakın +%.0f bps) · hedef %.2f (en yakın %.0f bps)"
                  % (sym, v["stop"], v["stopa_en_yakin_bps"], v["hedef"], v["hedefe_en_yakin_bps"]))

    print("\n[C] PF (kanonik ölçütle, 885 işlem)")
    kf = c["kullanilan_fark"]
    print("  fark B (yalnız icra)      : ort %s · medyan %s · ağırlıklı %s · t-CI95 %s"
          % (kf["B_ortalama"], kf["B_medyan"], kf["B_notional_agirlikli"],
             [kf["B_t_ci95"].get("lo"), kf["B_t_ci95"].get("hi")] if kf["B_t_ci95"] else None))
    print("  fark A (payda-özdeş)      : ort %s · ağırlıklı %s" % (kf["A_ortalama"], kf["A_notional_agirlikli"]))
    print("  model BAR hatası          : ort %s · medyan %s"
          % (kf["model_bar_hatasi"]["ortalama"], kf["model_bar_hatasi"]["medyan"]))
    for k, v in c["senaryolar"].items():
        print("  %-38s pf=%-8s net=%-12s (giriş+%s / çıkış+%s bps)"
              % (k, v.get("pf"), v.get("net"), v.get("giris_ek_bps", "-"), v.get("cikis_ek_bps", "-")))
    print("  başabaş simetrik:", c["basabas_egrisi"]["basabas_simetrik"],
          "· yalnız giriş:", c["basabas_egrisi"]["basabas_yalniz_giris"])
    print("  başabaş eğrisi (giriş→gereken çıkış):", c["basabas_egrisi"]["egri"])
    print("\nsonuc.json yazıldı.")


if __name__ == "__main__":
    main()
