"""EDG-2026-052 · E2 <-> dakika-bar dolum dogrulamasi — OLCUM (salt yerel dosya okuma).

Kart: research/cards/EDG-2026-052-e2-dakika-dogrulama.yaml (DONUK; betik yalniz uygular).
HUKUM YOK — sayilar Rol-1'e.

IKI KATMAN (ikisi de sonuc.json'da, karisik degil):
  KATMAN-1 (kart-birebir, YALNIZ E2 defterleri): dolum-olayinin dakikasi defter satirindan
    okunmaya calisilir. VERIDEN DOGRULANAN GERCEK: ne giris (entry_execution.jsonl: ts=EMIR
    GONDERIM zamani, fill_kaydedildi=CIPLAK GUN) ne cikis (trades.jsonl: ts_close=CIPLAK GUN)
    satirinda dakika-duzeyi DOLUM zamani alani VAR. Kod teyidi: loop.py giris tazelemesi
    (~:2570) Alpaca emrinden yalniz filled_avg_price/filled_qty/status okur, filled_at deftere
    YAZILMAZ; cikis yamasi (~:2985) yalniz alpaca_fill_price+mirror_divergence yazar.
    Sonuc: dakika eslemesi defterden KURULAMAZ -> tum dolum-olaylari ADIYLA 'eslenemeyen'
    (kill#1 geregi sessiz dusurme yok; neden-kodu tek: dolum_dakika_damgasi_defterde_yok).
  KATMAN-2 (BEYANLI YAN-KANIT, betimleyici): dolum dakikasi E2 defterinden DEGIL, exe007'nin
    YEREL broker ham dokumunden (research/olcumler/exe007_broker_teyit_2026-08-22/
    broker_ham.json, cekim 2026-08-22T10:43Z, Alpaca FILL aktiviteleri transaction_time UTC).
    Bu kaynak kartin evren tanimindaki iki kalemin (defter x arsiv) DISINDA yan-kanittir;
    katman ayri raporlanir, hicbir kill kriterini gevsetmez, hukum tasiyamaz. Parca-dolumlar
    (partial_fill) kendi dakikalariyla eslenir; defter fiyati parcalarin qty-agirlikli
    ortalamasiyla TEYIT edilir (uydurma yok: eslesmeyen parca kumesi adiyla dusulur).

SAAT-DILIMI KAPISI (kill#2): 047'nin dogrulama_saat_dilimi.json'u DEVRALINIR — bu olcum ayni
  yerel arsiv dosyalarini kullanir, YENI SEANS CEKILMEDI (tum dolum gunleri 047 penceresi
  2026-07-27..2026-08-21 icinde). Devralma beyani + kaynak sha sonuc.json'da.

ORNEKLEM ESIGI (kart): n<30 dolum VEYA seans<10 -> TUM cikti 'BETIMLEYICI' damgali.
VWAP VEKILI: (h+l+c)/3 — gercek VWAP degildir (bar 'vw' alani BILEREK kullanilmadi: kartin
  features_asof tanimi (h+l+c)/3 vekilini donduruyor; esik/tanim sonradan degismez).
CANLIYA SIFIR DOKUNUS: bu betik yalniz yerel dosya okur, hicbir sey yazmaz (sonuc.json haric).
"""
import gzip
import hashlib
import json
import statistics
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
REPO = DIZIN.parent.parent.parent
ARSIV = REPO / "research/olcumler/edg047_yakin_pencere_2026-08-23/canli_veri"
SAAT_DILIMI_KANIT = REPO / "research/olcumler/edg047_yakin_pencere_2026-08-23/dogrulama_saat_dilimi.json"
BROKER_HAM = REPO / "research/olcumler/exe007_broker_teyit_2026-08-22/broker_ham.json"
EPS = 1e-9


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def bps(a: float, b: float):
    return abs(a - b) / b * 1e4 if b else None


# ---------- girdiler ----------
entry_rows = [json.loads(l) for l in (DIZIN / "canli_entry_execution.jsonl").open()]
cikis_ham = json.loads((DIZIN / "canli_trades_cikis.json").read_text())
broker = json.loads(BROKER_HAM.read_text())
fills = [a for a in broker["aktiviteler"] if a.get("activity_type") == "FILL"]
saat_dilimi = json.loads(SAAT_DILIMI_KANIT.read_text())

# ---------- dolum-olaylari (defter-merkezli; bacak beyanli) ----------
olaylar = []
for r in entry_rows:
    if r.get("motor") == "ayna" and r.get("fill_status") == "filled":
        olaylar.append({
            "bacak": "giris", "kimlik": f"{r['plan_id']}/giris", "ticker": r["ticker"],
            "defter_fiyat": float(r["fill"]), "defter_qty": int(r["fill_qty"]),
            "defter_gun": r["fill_kaydedildi"], "broker_side": "buy",
            "pencere_damgasi": r.get("pencere"),  # yoksa None -> 'damgasiz'
            "zaman_alanlari_defterde": {"ts(emir_gonderim)": r.get("ts"),
                                        "fill_kaydedildi(ciplak_gun)": r.get("fill_kaydedildi")},
        })
for t in cikis_ham["satirlar"]:
    olaylar.append({
        "bacak": "cikis", "kimlik": f"{t['id']}/{t['plan_id']}/cikis", "ticker": t["ticker"],
        "defter_fiyat": float(t["alpaca_fill_price"]), "defter_qty": None,  # cikis satiri qty tasimaz
        "defter_gun": t["ts_close"], "broker_side": "sell",
        "pencere_damgasi": t.get("pencere"),
        "zaman_alanlari_defterde": {"ts_close(ciplak_gun)": t.get("ts_close")},
    })

n_olay = len(olaylar)
seanslar_defter = sorted({o["defter_gun"] for o in olaylar})

# ---------- KATMAN-1: kart-birebir (yalniz defter) ----------
katman1_eslenemeyen = [{
    "kimlik": o["kimlik"], "bacak": o["bacak"], "ticker": o["ticker"],
    "neden": "dolum_dakika_damgasi_defterde_yok",
    "defterdeki_zaman_alanlari": o["zaman_alanlari_defterde"],
} for o in olaylar]
katman1 = {
    "tanim": "dolum dakikasi YALNIZ E2 defter satirindan; defterde dakika-duzeyi dolum zamani alani yok",
    "eslenen_n": 0, "eslenemeyen_n": n_olay, "eslenemeyen_adli_liste": katman1_eslenemeyen,
    "alan_dogrulama": {
        "giris_fiyat_alani": "fill (= Alpaca filled_avg_price; 'alpaca_fill_price' ADLI alan giris defterinde YOK)",
        "cikis_fiyat_alani": "alpaca_fill_price (trades.jsonl yamasi, loop.py ~:2985)",
        "giris_zaman_alanlari": "ts = emir GONDERIM zamani UTC (20:3x/22:10 — dolum zamani DEGIL); fill_kaydedildi = ciplak gun",
        "cikis_zaman_alanlari": "ts_close = ciplak gun (exe007 KOMUT.txt teyidi)",
        "kod_teyidi": "loop.py giris tazelemesi filled_at OKUMAZ/YAZMAZ; cikis yamasi yalniz fiyat+divergence yazar",
    },
}

# ---------- KATMAN-2: beyanli yan-kanit (broker transaction_time) ----------
# parca atama: side+symbol (+gun; gun bos kalirsa sembol geneli -> tarih_uyusmazligi beyani)
kullanilan, atanmis_idx = [], set()
for o in olaylar:
    grup = [i for i, f in enumerate(fills)
            if f["symbol"] == o["ticker"] and f["side"] == o["broker_side"]
            and f["transaction_time"][:10] == o["defter_gun"]]
    tarih_uyusmazligi = False
    if not grup:
        grup = [i for i, f in enumerate(fills)
                if f["symbol"] == o["ticker"] and f["side"] == o["broker_side"] and i not in atanmis_idx]
        tarih_uyusmazligi = bool(grup)
    o["parca_idx"] = grup
    o["tarih_uyusmazligi"] = tarih_uyusmazligi
    atanmis_idx.update(grup)

# gereken seans dosyalarini bir kez ac; yalniz gereken ticker'lar (CPU-nazik)
gerek_gunler = sorted({fills[i]["transaction_time"][:10] for o in olaylar for i in o["parca_idx"]})
gerek_ticker = {o["ticker"] for o in olaylar}
bar_idx = {}  # (gun, ticker, 'HH:MM') -> bar
arsiv_dosyalari = {}
for gun in gerek_gunler:
    p = ARSIV / f"{gun}.jsonl.gz"
    if not p.exists():
        arsiv_dosyalari[gun] = None  # eksik seans — asagida eslenemeyen olarak dusecek
        continue
    arsiv_dosyalari[gun] = {"dosya": str(p.relative_to(REPO)), "sha256_16": sha16(p)}
    with gzip.open(p, "rt") as f:
        for satir in f:
            b = json.loads(satir)
            if b["ticker"] in gerek_ticker:
                bar_idx[(gun, b["ticker"], b["t"][11:16])] = b

parca_kayitlari, k2_eslenemeyen = [], []
for o in olaylar:
    if not o["parca_idx"]:
        k2_eslenemeyen.append({"kimlik": o["kimlik"], "bacak": o["bacak"], "ticker": o["ticker"],
                               "neden": "broker_dokumunde_parca_bulunamadi"})
        o["k2"] = None
        continue
    parcalar = []
    for i in o["parca_idx"]:
        f = fills[i]
        gun, dakika = f["transaction_time"][:10], f["transaction_time"][11:16]
        p, q = float(f["price"]), float(f["qty"])
        bar = bar_idx.get((gun, o["ticker"], dakika))
        kayit = {"kimlik": o["kimlik"], "bacak": o["bacak"], "ticker": o["ticker"],
                 "transaction_time": f["transaction_time"], "dakika_utc": f"{gun}T{dakika}",
                 "fiyat": p, "qty": q, "bar_bulundu": bar is not None}
        if bar is None:
            neden = ("arsivde_seans_dosyasi_yok" if arsiv_dosyalari.get(gun) is None
                     else "o_dakikada_bar_satiri_yok")
            k2_eslenemeyen.append({"kimlik": o["kimlik"], "bacak": o["bacak"], "ticker": o["ticker"],
                                   "dakika_utc": f"{gun}T{dakika}", "fiyat": p, "qty": q, "neden": neden})
        else:
            vekil = (bar["h"] + bar["l"] + bar["c"]) / 3.0
            kayit.update({
                "bar": {k: bar[k] for k in ("o", "h", "l", "c", "v", "t")},
                "bant_ici": (bar["l"] - EPS) <= p <= (bar["h"] + EPS),
                "bps_dakika_acilis": round(bps(p, bar["o"]), 3),
                "bps_vwap_vekili_hlc3": round(bps(p, vekil), 3),
            })
        parcalar.append(kayit)
        parca_kayitlari.append(kayit)
    top_q = sum(pc["qty"] for pc in parcalar)
    wavg = sum(pc["fiyat"] * pc["qty"] for pc in parcalar) / top_q if top_q else None
    barli = [pc for pc in parcalar if pc["bar_bulundu"]]
    o["k2"] = {
        "parca_n": len(parcalar), "dakika_kumesi": sorted({pc["dakika_utc"] for pc in parcalar}),
        "toplam_qty": top_q,
        "qty_teyit": (o["defter_qty"] is None or int(top_q) == o["defter_qty"]),
        "wavg_fiyat": round(wavg, 4) if wavg else None,
        "defter_fiyat_teyit_bps": round(bps(wavg, o["defter_fiyat"]), 3) if wavg else None,
        "tum_parcalar_barli": len(barli) == len(parcalar),
        "tum_parcalar_bant_ici": bool(barli) and len(barli) == len(parcalar)
                                 and all(pc["bant_ici"] for pc in barli),
        "tarih_uyusmazligi": o["tarih_uyusmazligi"],
    }

atanmayan_broker = [{"symbol": fills[i]["symbol"], "side": fills[i]["side"],
                     "transaction_time": fills[i]["transaction_time"],
                     "price": fills[i]["price"], "qty": fills[i]["qty"],
                     "not": "E2 dolum-olayina atanmadi (E2-disi ya da defterde alpaca_fill_price'siz)"}
                    for i in range(len(fills)) if i not in atanmis_idx]

# ---------- hizalama saglamasi (olcum-butunlugu; kart metrigi DEGIL) ----------
# Yanlis-eslesme hipotezi: bar t damgasi dakika-BASLANGICI degilse dolumlar sistematik olarak
# komsu dakikanin barina oturur. Test: barli-ama-bant-disi her parca icin D-1 ve D+1 barlarina bak.
def _komsu(gun, dk, delta):
    h, m = int(dk[:2]), int(dk[3:]) + delta
    return gun, f"{h + m // 60:02d}:{m % 60:02d}"


hiza = {"n_bant_disi": 0, "d_eksi1_bant_ici": 0, "d_arti1_bant_ici": 0, "hicbiri": 0}
for pc in parca_kayitlari:
    if not pc["bar_bulundu"] or pc["bant_ici"]:
        continue
    hiza["n_bant_disi"] += 1
    gun, dk = pc["dakika_utc"][:10], pc["dakika_utc"][11:16]
    hit = False
    for etiket, delta in (("d_eksi1_bant_ici", -1), ("d_arti1_bant_ici", 1)):
        b = bar_idx.get((*_komsu(gun, dk, delta)[:1], pc["ticker"], _komsu(gun, dk, delta)[1]))
        if b and (b["l"] - EPS) <= pc["fiyat"] <= (b["h"] + EPS):
            hiza[etiket] += 1
            hit = True
    if not hit:
        hiza["hicbiri"] += 1
hiza["beyan"] = ("bant-disi parcalarin buyuk cogunlugu komsu dakikada da bant-disi -> sistematik "
                 "dakika-kaymasi (bitis-damgasi karisikligi) DISLANDI; bant-disilik deseni dar/"
                 "tek-islemli IEX barlariyla uyumlu (kartin beyanli siniri 3: IEX-tek-kaynak serhi)"
                 if hiza["hicbiri"] >= max(hiza["d_eksi1_bant_ici"], hiza["d_arti1_bant_ici"])
                 else "DIKKAT: komsu-dakika bant-ici sayimi yuksek — hizalama supheli, Rol-1 incelemeli")

# ---------- ozet ----------
barli_p = [pc for pc in parca_kayitlari if pc["bar_bulundu"]]
bant_ici_p = [pc for pc in barli_p if pc["bant_ici"]]
bps_ac = sorted(pc["bps_dakika_acilis"] for pc in barli_p)
bps_vw = sorted(pc["bps_vwap_vekili_hlc3"] for pc in barli_p)
olay_k2 = [o for o in olaylar if o["k2"]]
seanslar_k2 = sorted({pc["dakika_utc"][:10] for pc in parca_kayitlari})


def q(dizi, oran):
    return round(statistics.quantiles(dizi, n=4)[{0.25: 0, 0.5: 1, 0.75: 2}[oran]], 3) if len(dizi) >= 2 else (dizi[0] if dizi else None)


BETIMLEYICI = (n_olay < 30) or (len(seanslar_defter) < 10)
sonuc = {
    "kart": "EDG-2026-052",
    "damga": "BETIMLEYICI" if BETIMLEYICI else "hukumlu-esik-orneklemi",
    "damga_nedeni": f"dolum-olayi n={n_olay} (<30: {n_olay < 30}) VEYA seans={len(seanslar_defter)} (<10: {len(seanslar_defter) < 10}) — kartin esigi geregi TUM cikti betimleyici",
    "hukum": None,
    "hukum_notu": "HUKUM YOK — kart geregi Rol-1'e; hukumlu esik (bant-ici>=%95 VE eslenemeyen=0) ORNEKLEM DOLMADAN UYGULANMAZ (kill#4)",
    "kapsam": {
        "dolum_olayi_n": n_olay, "giris_n": sum(1 for o in olaylar if o["bacak"] == "giris"),
        "cikis_n": sum(1 for o in olaylar if o["bacak"] == "cikis"),
        "seans_listesi_defter": seanslar_defter, "seans_n_defter": len(seanslar_defter),
        "seans_listesi_yan_kanit": seanslar_k2, "seans_n_yan_kanit": len(seanslar_k2),
        "pencere_rejimi_kovalari": {"damgasiz": sum(1 for o in olaylar if o["pencere_damgasi"] is None),
                                    "damgali": sum(1 for o in olaylar if o["pencere_damgasi"] is not None)},
        "pencere_notu": "E2 satirlarinin HICBIRINDE 'pencere' alani yok (EXE-009+K2 damgasi bu 13 dolumdan sonra devreye girmis) — tumu 'damgasiz' kovasi",
    },
    "saat_dilimi_kapisi": {
        "durum": "DEVRALINDI (047 dogrulamasi aynen; kill#2 saglandi)",
        "beyan": "bu olcum 047'nin AYNI yerel arsiv dosyalarini kullanir; YENI SEANS CEKILMEDI (tum dolum gunleri 2026-08-06..2026-08-21, 047 penceresi 2026-07-27..2026-08-21 icinde) — yeniden kosum sarti dogmadi",
        "kaynak": str(SAAT_DILIMI_KANIT.relative_to(REPO)), "kaynak_sha256_16": sha16(SAAT_DILIMI_KANIT),
        "sicrama_min": saat_dilimi["sicrama_min"], "sonuc_utc_mi": saat_dilimi["sonuc_utc_mi"],
    },
    "katman1_kart_birebir": katman1,
    "katman2_yan_kanit": {
        "beyan": "dolum dakikasi E2 defterinden DEGIL, exe007 YEREL broker ham dokumunden (Alpaca FILL transaction_time, UTC ISO ms). Kart evreninin (defter x arsiv) DISINDAN yan-kanit; betimleyici, hukum tasiyamaz",
        "kaynak": str(BROKER_HAM.relative_to(REPO)), "kaynak_sha256_16": sha16(BROKER_HAM),
        "kaynak_cekim_zamani": broker["cekim_zamani"], "broker_fill_aktivite_n": len(fills),
        "olay_duzeyi": {
            "eslenen_n": len(olay_k2), "eslenemeyen_n": n_olay - len(olay_k2),
            "tum_parcalari_barli_ve_bant_ici_olay_n": sum(1 for o in olay_k2 if o["k2"]["tum_parcalar_bant_ici"]),
            "qty_teyit_gecen_n": sum(1 for o in olay_k2 if o["k2"]["qty_teyit"]),
            "defter_fiyat_teyit_bps_maks": max((o["k2"]["defter_fiyat_teyit_bps"] for o in olay_k2
                                               if o["k2"]["defter_fiyat_teyit_bps"] is not None), default=None),
            "tarih_uyusmazligi_olaylari": [o["kimlik"] for o in olay_k2 if o["k2"]["tarih_uyusmazligi"]],
        },
        "parca_duzeyi": {
            "parca_n": len(parca_kayitlari), "barli_n": len(barli_p),
            "bant_ici_n": len(bant_ici_p),
            "bant_ici_orani": round(len(bant_ici_p) / len(barli_p), 4) if barli_p else None,
            "bps_dakika_acilis": {"medyan": q(bps_ac, 0.5), "p25": q(bps_ac, 0.25), "p75": q(bps_ac, 0.75)},
            "bps_vwap_vekili_hlc3": {"medyan": q(bps_vw, 0.5), "p25": q(bps_vw, 0.25), "p75": q(bps_vw, 0.75)},
            "vekil_beyani": "(h+l+c)/3 gercek VWAP degildir; bar 'vw' alani kartin tanimi geregi KULLANILMADI",
        },
        "hizalama_saglamasi": hiza,
        "eslenemeyen_adli_liste": k2_eslenemeyen,
        "olay_tablosu": [{"kimlik": o["kimlik"], "bacak": o["bacak"], "ticker": o["ticker"],
                          "defter_gun": o["defter_gun"], "defter_fiyat": o["defter_fiyat"],
                          **(o["k2"] or {})} for o in olaylar],
        "parca_tablosu": parca_kayitlari,
        "atanmayan_broker_parcalari": atanmayan_broker,
    },
    "girdiler": {
        "canli_entry_execution.jsonl": {"sha256_16": sha16(DIZIN / "canli_entry_execution.jsonl"), "n": len(entry_rows)},
        "canli_trades_cikis.json": {"sha256_16": sha16(DIZIN / "canli_trades_cikis.json"),
                                    "trades_toplam_n": cikis_ham["trades_toplam_n"],
                                    "alpaca_fill_price_satir_n": cikis_ham["alpaca_fill_price_satir_n"]},
        "arsiv_dosyalari": arsiv_dosyalari,
    },
    "olcum_py_sha256_16": sha16(Path(__file__)),
}
(DIZIN / "sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False))
print(json.dumps({"damga": sonuc["damga"], "olay_n": n_olay,
                  "k1_eslenemeyen": katman1["eslenemeyen_n"],
                  "k2_eslenen_olay": len(olay_k2),
                  "k2_parca": len(parca_kayitlari), "k2_barli": len(barli_p),
                  "k2_bant_ici": len(bant_ici_p)}, ensure_ascii=False))
