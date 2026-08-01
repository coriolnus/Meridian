"""earnings_8k_tarihleri.csv dogrulama + kapsam/anomali envanteri.

Uc bagimsiz capraz kontrol:
 (A) state/earnings.csv (ucuncu-taraf takvim: Nasdaq/FMP) — bugune kadar GECMISE
     dusmus tarihlerle kesisim; 8-K filed ile fark dagilimi.
 (B) research/edgar_facts/fundamentals.csv.gz + shares_outstanding.csv.gz icindeki
     form='8-K' satirlarinin accession'lari — AYRI bir SEC ucundan (companyfacts XBRL)
     gelen ayni olaylar; accession eslesmesi bicimsel dogrulama.
 (C) mevsimsellik/siklik mantik kontrolu — sembol x yil sayimlari, ~4/yil beklenir.

Cikti: scratchpad/edgar_8k/dogrulama_8k.json + ekrana ozet.
"""
import csv, gzip, json, os
from collections import defaultdict, Counter
from datetime import date, timedelta

REPO = "/Users/erdemozturk/AI-Trading"
CSV_YOL = f"{REPO}/research/edgar_facts/earnings_8k_tarihleri.csv"
WORK = f"{REPO}/scratchpad/edgar_8k"
BUGUN = date.today().isoformat()

rows = list(csv.DictReader(open(CSV_YOL)))
by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(r)
for s in by_sym:
    by_sym[s].sort(key=lambda r: r["filed"])

rapor = {"olusturma_utc_gun": BUGUN}

# ---------------------------------------------------------------- kapsam
yil_say = defaultdict(Counter)
for r in rows:
    yil_say[r["symbol"]][r["filed"][:4]] += 1
tum_yillar = sorted({r["filed"][:4] for r in rows})
rapor["kapsam"] = {
    "satir": len(rows), "sembol": len(by_sym),
    "filed_min": min(r["filed"] for r in rows), "filed_maks": max(r["filed"] for r in rows),
    "yil_basina_satir": {y: sum(1 for r in rows if r["filed"][:4] == y) for y in tum_yillar},
}

# sembol basina yillik ortalama: yalnizca sembolun AKTIF penceresi uzerinden
sym_ozet = []
for s, rs in by_sym.items():
    ilk, son = rs[0]["filed"], rs[-1]["filed"]
    gun = (date.fromisoformat(son) - date.fromisoformat(ilk)).days
    yil = max(gun / 365.25, 1e-9)
    sym_ozet.append({"symbol": s, "n": len(rs), "ilk": ilk, "son": son,
                     "aktif_yil": round(yil, 2),
                     "yillik": round((len(rs) - 1) / yil, 2) if gun > 400 else None})
sym_ozet.sort(key=lambda x: x["symbol"])
yilliklar = [x["yillik"] for x in sym_ozet if x["yillik"] is not None]
rapor["kapsam"]["sembol_basina_yillik_ortalama"] = round(sum(yilliklar) / len(yilliklar), 3)
rapor["kapsam"]["yillik_dagilim"] = {
    "min": min(yilliklar), "maks": max(yilliklar),
    "medyan": sorted(yilliklar)[len(yilliklar) // 2],
    "3.5_alti": sum(1 for v in yilliklar if v < 3.5),
    "3.5_4.5_arasi": sum(1 for v in yilliklar if 3.5 <= v <= 4.5),
    "4.5_ustu": sum(1 for v in yilliklar if v > 4.5),
}

# ---------------------------------------------------------------- (A) earnings.csv kesisimi
earn = defaultdict(list)
with open(f"{REPO}/state/earnings.csv") as f:
    for r in csv.DictReader(f):
        earn[r["ticker"]].append(r["date"])

A = {"kaynak": "state/earnings.csv (Nasdaq/FMP ucundan dolan ileriye-donuk takvim anlik gorüntüsu)",
     "gecmise_dusmus_sembol": 0, "eslesme": [], "fark_dagilimi": Counter()}
for t, ds in sorted(earn.items()):
    for d in ds:
        if d > BUGUN or t not in by_sym:
            continue
        A["gecmise_dusmus_sembol"] += 1
        hedef = date.fromisoformat(d)
        en_yakin = min(by_sym[t], key=lambda r: abs((date.fromisoformat(r["filed"]) - hedef).days))
        fark = (date.fromisoformat(en_yakin["filed"]) - hedef).days
        A["fark_dagilimi"][fark] += 1
        A["eslesme"].append({"symbol": t, "takvim_tarihi": d, "8k_filed": en_yakin["filed"],
                             "8k_report_date": en_yakin["report_date"],
                             "fark_gun": fark, "accn": en_yakin["accn"]})
A["fark_dagilimi"] = dict(sorted(A["fark_dagilimi"].items()))
rapor["A_ucuncu_taraf_takvim"] = A

# ---------------------------------------------------------------- (B) companyfacts accession eslesmesi
accn_8k = defaultdict(set)
for r in rows:
    accn_8k[r["symbol"]].add(r["accn"])
cf_8k = defaultdict(set)
for dosya in ("fundamentals.csv.gz", "shares_outstanding.csv.gz"):
    p = f"{REPO}/research/edgar_facts/{dosya}"
    if not os.path.exists(p):
        continue
    with gzip.open(p, "rt") as f:
        for r in csv.DictReader(f):
            if r.get("form", "").startswith("8-K") and r.get("filed", "") >= "2010-01-01":
                cf_8k[r["symbol"]].add((r["accn"], r["filed"], r["form"]))

tut, kacan, cf_top = 0, [], 0
for s, kume in cf_8k.items():
    for accn, filed, form in kume:
        cf_top += 1
        if accn in accn_8k.get(s, ()):
            tut += 1
        else:
            kacan.append({"symbol": s, "accn": accn, "filed": filed, "form": form})
rapor["B_companyfacts_accession"] = {
    "kaynak": "SEC XBRL companyfacts (AYRI uc) icindeki form=8-K satirlari",
    "cf_8k_benzersiz_accn": cf_top, "2.02_listemizde_bulunan": tut,
    "oran": round(tut / cf_top, 4) if cf_top else None,
    "bulunmayan_ornek": kacan[:25], "bulunmayan_toplam": len(kacan),
    "YORUM": "DUSUK ORAN BEKLENIYOR ve HATA DEGIL: companyfacts yalnizca XBRL etiketli "
             "finansal tasiyan 8-K'leri gorur; bunlarin neredeyse tamami Item 8.01 "
             "(yeniden duzenlenmis/recast finansallar), Item 2.02 kazanc bulteni degil. "
             "Ayri tani (scratchpad/edgar_8k/tani.py): 228 companyfacts 8-K accession'inin "
             "228'i (%100) ham submissions verisinde BULUNDU; items dagilimi 8.01,9.01=209 / "
             "8.01=7 / 7.01,8.01,9.01=4 / 2.02,8.01,9.01=3 / 9.01=3 / digeri=2. Yani bu test "
             "AYRISTIRMA BUTUNLUGUNU dogrular (accession evreni tam, items alani dogru "
             "okunuyor), 2.02 KAPSAMINI degil.",
}

# ---------------------------------------------------------------- (C) siklik / bosluk anomalileri
anom = {"yil_basina_4_disi": [], "buyuk_bosluk": [], "ayni_gun_cift": [],
        "gec_baslayan": [], "erken_biten": [], "satirsiz_sembol": []}
cikmap = json.load(open(f"{REPO}/research/edgar_facts/cik_haritasi.json"))
tum_sembol = {r["symbol"] for r in cikmap["eslesen"]}
anom["satirsiz_sembol"] = sorted(tum_sembol - set(by_sym))

for x in sym_ozet:
    s = x["symbol"]
    if x["yillik"] is not None and not (3.4 <= x["yillik"] <= 4.6):
        anom["yil_basina_4_disi"].append(x)
    if x["ilk"] > "2010-06-30":
        anom["gec_baslayan"].append({"symbol": s, "ilk": x["ilk"]})
    if x["son"] < "2026-02-01":
        anom["erken_biten"].append({"symbol": s, "son": x["son"]})
    rs = by_sym[s]
    for a, b in zip(rs, rs[1:]):
        g = (date.fromisoformat(b["filed"]) - date.fromisoformat(a["filed"])).days
        if g > 200:
            anom["buyuk_bosluk"].append({"symbol": s, "from": a["filed"], "to": b["filed"], "gun": g})
        if g == 0:
            anom["ayni_gun_cift"].append({"symbol": s, "filed": a["filed"],
                                          "accn": [a["accn"], b["accn"]]})
rapor["C_anomali"] = {k: (v if len(v) <= 60 else v[:60] + [{"...": f"toplam {len(v)}"}])
                      for k, v in anom.items()}
rapor["C_anomali_sayilar"] = {k: len(v) for k, v in anom.items()}

# ---------------------------------------------------------------- filed vs report_date (vekil yanliligi olcusu)
d_rd = Counter()
bos_rd = 0
for r in rows:
    if not r["report_date"]:
        bos_rd += 1
        continue
    d_rd[(date.fromisoformat(r["filed"]) - date.fromisoformat(r["report_date"])).days] += 1
rapor["filed_eksi_report_date"] = {"dagilim": dict(sorted(d_rd.items())[:15]),
                                   "report_date_bos": bos_rd,
                                   "gun0_orani": round(d_rd[0] / max(sum(d_rd.values()), 1), 4),
                                   "gun0_1_orani": round((d_rd[0] + d_rd[1]) / max(sum(d_rd.values()), 1), 4)}

# acceptance saati dagilimi (ham) + saat dilimi HIPOTEZ TESTI
saat = Counter(r["acceptance"][11:13] for r in rows if r["acceptance"])
rapor["acceptance_ham_saat_histogram"] = dict(sorted(saat.items()))

# SAAT DILIMI: IKI HIPOTEZ, IKISI DE KENDI ALTKUMESINDE CELISIYOR -> COZULEMEDI.
#  U: dizgedeki 'Z' gercek UTC -> ET = UTC-4 (yaz) / -5 (kis)
#  E: dizge zaten ET (EDGAR'in tarihsel aliskanligi; 'Z' yaniltici)
# Iki bagimsiz olcut:
#  (i) EDGAR kabul penceresi 06:00-22:00 ET disina dusen satir  -> fiziksel imkansiz
#  (ii) 17:30 ET sonrasi kabul edilip AYNI GUN filingDate almis satir -> EDGAR'in
#       "17:30 sonrasi ertesi is gunu" kuraliyla celisir
from datetime import datetime, timedelta
tz = {}
for hyp in ("UTC", "ET"):
    pencere_disi = kural_ihlali = topl = kayma = 0
    saat = Counter()
    sembol_disi = Counter()
    for r in rows:
        a = r["acceptance"]
        if not a:
            continue
        topl += 1
        dt = datetime.fromisoformat(a.replace("Z", "+00:00")).replace(tzinfo=None)
        e = dt if hyp == "ET" else dt - timedelta(hours=4 if 3 < dt.month < 11 else 5)
        saat[e.hour] += 1
        if not (6 <= e.hour <= 21):
            pencere_disi += 1
            sembol_disi[r["symbol"]] += 1
        if e.hour * 60 + e.minute > 17 * 60 + 30 and e.date().isoformat() == r["filed"]:
            kural_ihlali += 1
        if e.date().isoformat() != r["filed"]:
            kayma += 1
    tz[hyp] = {"pencere_disi_06_22_ET": pencere_disi,
               "pencere_disi_orani": round(pencere_disi / topl, 4),
               "17_30_kurali_ihlali": kural_ihlali,
               "ihlal_orani": round(kural_ihlali / topl, 4),
               "kabul_gunu_filed_ile_ayni_degil": kayma,
               "pencere_disi_en_yogun_sembol": sembol_disi.most_common(12),
               "et_saat_histogram": dict(sorted(saat.items()))}
tz["toplam"] = len(rows)
tz["sonuc"] = "COZULEMEDI"
tz["gerekce"] = (
    "Iki hipotez de veri ALTKUMELERINDE imkansiz sonuc uretiyor ve iki altkume neredeyse "
    "AYRIK (kesisim 1 sembol): UTC yorumunda 1347 satir (%7.7) 01:00-05:59 ET'ye dusuyor "
    "(EDGAR o saatte kapali) ve bunlar klasik BMO raporlayicilarda yigiliyor (PG 67/67, "
    "WBA 43/43, K 67/68, MDT 46/47, JNJ 67/70) — PG'nin bulteni ~06:55 ET cikarken 8-K'nin "
    "03:02 ET'de kabul edilmesi bulten-oncesi dosyalama demek olurdu. ET yorumunda ise "
    "6057 satir (%34.5) 17:30 ET'den sonra kabul edilmis gorunup AYNI GUN filingDate almis; "
    "bu EDGAR'in ertesi-is-gunu kuraliyla celisiyor ve klasik AMC raporlayicilarda yigiliyor "
    "(AAPL 68/68, AMZN 67/67, GOOGL 45/45, META 57/57) — AAPL'in bulteni 16:30 ET'de cikarken "
    "damga 20:30Z. Sirket duzeyinde damga COK KARARLI (PG hep 07:0x, AAPL hep 20:30, MSFT hep "
    "16:0x), yani sutun gercek bir sinyal tasiyor; ama hangi saat diliminde oldugu bu turda "
    "birinci-el kanitla (gercek bulten zaman damgasi) sinanmadi. HUKUM: acceptance'tan "
    "BMO/AMC TURETILMEZ.")
rapor["acceptance_saat_dilimi_testi"] = tz

# ---------------------------------------------------------------- (E) kamuya bilinen duyuru gunleri
# KAYNAK BEYANI: asagidaki tarihler MODEL BILGISIDIR (egitim verisi) — birinci-el kayit DEGIL.
# Amac: 8-K/2.02 filed gunlerinin bilinen duyuru gunleriyle ORTUSUP ORTUSMEDIGINI gormek.
BILINEN = {
    "AAPL": ["2023-02-02", "2023-05-04", "2023-08-03", "2023-11-02",
             "2024-02-01", "2024-05-02", "2024-08-01", "2024-10-31"],
    "NVDA": ["2023-02-22", "2023-05-24", "2023-08-23", "2023-11-21",
             "2024-02-21", "2024-05-22", "2024-08-28", "2024-11-20"],
}
E = {"kaynak_beyani": "MODEL BILGISI (egitim verisi) — birinci-el kayit degil, hata payi vardir",
     "kontrol": []}
for s, ds in BILINEN.items():
    for d in ds:
        if s not in by_sym:
            E["kontrol"].append({"symbol": s, "bilinen": d, "durum": "sembol yok"})
            continue
        h = date.fromisoformat(d)
        en = min(by_sym[s], key=lambda r: abs((date.fromisoformat(r["filed"]) - h).days))
        E["kontrol"].append({"symbol": s, "bilinen_duyuru": d, "8k_filed": en["filed"],
                             "8k_report_date": en["report_date"],
                             "fark_gun": (date.fromisoformat(en["filed"]) - h).days})
E["tam_isabet"] = sum(1 for k in E["kontrol"] if k.get("fark_gun") == 0)
E["toplam"] = len(E["kontrol"])
rapor["E_kamuya_bilinen_gunler"] = E

# ---------------------------------------------------------------- (F) olay kumeleme
# Yuksek frekansli semboller ayni kazanc olayi icin birden cok 2.02 dosyalar (on-duyuru,
# ertesi-gun tamamlayici, ek materyal). W gun icindeki ardisik satirlar tek OLAY sayilirsa
# yillik oran ~4'e oturuyor mu? (W bir MODEL SECIMIDIR; olcum kartinda beyan edilir,
# bu dosyada yalnizca tanidir — CSV'ye kume kimligi YAZILMADI, ham veri korundu.)
F = {"not": "kumeleme yalnizca tani amacli; CSV ham birakildi. W = kumeleme penceresi (gun)."}
for W in (3, 5, 7, 14):
    oranlar = []
    toplam_kume = 0
    for s, rs in by_sym.items():
        kume, son = 0, None
        for r in rs:
            d = date.fromisoformat(r["filed"])
            if son is None or (d - son).days > W:
                kume += 1
            son = d
        toplam_kume += kume
        gun = (date.fromisoformat(rs[-1]["filed"]) - date.fromisoformat(rs[0]["filed"])).days
        if gun > 400:
            oranlar.append((kume - 1) / (gun / 365.25))
    oranlar.sort()
    F[f"W{W}"] = {"toplam_olay": toplam_kume,
                  "yillik_medyan": round(oranlar[len(oranlar) // 2], 3),
                  "yillik_ortalama": round(sum(oranlar) / len(oranlar), 3),
                  "4.5_ustu_sembol": sum(1 for v in oranlar if v > 4.5),
                  "3.5_alti_sembol": sum(1 for v in oranlar if v < 3.5)}
rapor["F_olay_kumeleme"] = F

with open(f"{WORK}/dogrulama_8k.json", "w") as f:
    json.dump(rapor, f, indent=1, default=str)

print(json.dumps({k: v for k, v in rapor.items() if k != "C_anomali"},
                 indent=1, ensure_ascii=False, default=str)[:6000])
print("\nANOMALI SAYILAR:", json.dumps(rapor["C_anomali_sayilar"], indent=1))
