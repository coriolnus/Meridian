"""kaynak_8k.json — 8-K/Item-2.02 kazanc-tarihi vekilinin koken damgasi.

Icerik: url sablonlari, istek politikasi, indirme penceresi, kapsam ozeti, dogrulama
sonuclari, VEKIL-YANLILIK BEYANI (zorunlu okunur), cikti sha256'lari, ham indirme
manifesti (sha256'lar ham/sikistirilmamis JSON baytlari uzerinden).
"""
import csv, hashlib, json, os
from collections import Counter, defaultdict
from datetime import date

REPO = "/Users/erdemozturk/AI-Trading"
FACTS = f"{REPO}/research/edgar_facts"
WORK = f"{REPO}/scratchpad/edgar_8k"
CSV_YOL = f"{FACTS}/earnings_8k_tarihleri.csv"

man = json.load(open(f"{WORK}/download_manifest_8k.json"))
dog = json.load(open(f"{WORK}/dogrulama_8k.json"))
rows = list(csv.DictReader(open(CSV_YOL)))
amend = json.load(open(f"{WORK}/amend_2_02.json"))

by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(r["filed"])

zamanlar = sorted(m["indirme_utc"] for m in man if m.get("indirme_utc"))
sha = hashlib.sha256(open(CSV_YOL, "rb").read()).hexdigest()

VEKIL_BEYAN = [
    "VEKIL-YANLILIK BEYANI — bu dosyayi kullanan HER olcum kartinda ZORUNLU OKUNUR:",
    "1) Bu dosya KAZANC DUYURU TAKVIMI DEGIL, 8-K Item-2.02 DOSYALAMA GUNLERIDIR. "
    "8-K filed ~ duyuru gunu ya da ERTESI IS GUNU; SEC kurali dort is gunu icinde dosyalamaya "
    "izin verir, pratikte ayni gun baskindir ama tek tek satirda garanti YOKTUR.",
    "2) BMO/AMC (piyasa oncesi/sonrasi) ALANI YOKTUR ve `acceptance` sutunundan "
    "TURETILEMEZ. Sutun EDGAR kabul zaman damgasinin HAM dizgesidir; saat dilimi bu turda "
    "sinandi ve COZULEMEDI: 'Z gercekten UTC' hipotezi 1347 satiri (%7.7) EDGAR'in kapali "
    "oldugu 01:00-05:59 ET'ye dusuruyor (PG 67/67, WBA 43/43, JNJ 67/70 gibi klasik BMO "
    "raporlayicilarda yigiliyor — bulten-oncesi dosyalama anlamina gelirdi); 'dizge zaten "
    "ET' hipotezi ise 6057 satiri (%34.5) 17:30 ET sonrasi kabul edilip AYNI GUN "
    "filingDate almis gosteriyor, bu da EDGAR'in ertesi-is-gunu kuraliyla celisiyor "
    "(AAPL 68/68, AMZN 67/67, GOOGL 45/45 gibi klasik AMC raporlayicilarda yigiliyor). "
    "Iki celiskili altkume neredeyse AYRIK (kesisim 1 sembol). Damga sirket duzeyinde cok "
    "kararlidir (PG hep 07:0x, AAPL hep 20:30, MSFT hep 16:0x) — yani sutun gercek sinyal "
    "tasir; ama kalibrasyonu birinci-el bulten zaman damgasi gerektirir. O tur yapilmadan "
    "seans-ici/sonrasi ayrimi YAPILMAZ.",
    "3) Item-2.02 ISARETSIZ kazanc duyurulari KACAR. Bazi sirketler sonuclari yalnizca basin "
    "bulteni (Item 7.01/8.01) ya da 10-Q/10-K ile duyurur; bu satirlar burada YOKTUR. "
    "Kapsam eksigi sembol bazinda `yillik` sutunundan gorulur (~4/yil beklenir).",
    "4) 8-K/A (duzeltme) satirlari CSV'ye ALINMADI — duzeltme yeni duyuru degildir.",
    "5) `report_date` (8-K 'period of report') olayin gunudur ve duyuru gunune `filed`'dan "
    "daha yakin bir adaydir; ama BOS olabilir ve dosyalayanin beyanidir. Hangi sutunun "
    "kullanildigi olcum kartinda ACIKCA yazilir.",
    "6) PIT NOTU: bu veri GECMISE DONUK dosyalama kaydidir. Bir olcumde 't gununde biliniyordu' "
    "demek icin filed <= t sarti kullanilir; ILERIYE DONUK takvim (beklenen kazanc tarihi) "
    "bu dosyadan URETILEMEZ — o bilgi ancak state/history/earnings_snapshots.jsonl birikince olusur.",
    "7) CIK HALEFIYETI — SESSIZ TARIH KESIGI: seri, cik_haritasi.json'daki BUGUNKU CIK'e "
    "baglidir. Yeniden yapilanma/holdco kuran sirketlerde eski gecmis SELEF CIK'te kalir ve "
    "bu dosyada YOKTUR. Dogrulanmis ornekler: BLK ilk 2.02 = 2024-10-11 (selef 'BlackRock, "
    "Inc.'), GOOG/GOOGL = 2015-10-22 (Alphabet holdco), DIS = 2019-05-08 ('TWDC Holdco 613'), "
    "CI = 2019-05-02 ('Halfmoon Parent'), DOW/LIN/AVGO/MDT/ETN/DD/KHC/BKR/CEG/APO/KVUE/MRVL "
    "benzeri. 41 sembolde ilk 2.02 > 2010-06-30; envanter kaynak_8k.json > "
    "dogrulama.C_anomali_sayilar ve scratchpad/edgar_8k/dogrulama_8k.json icinde. Bu "
    "semboller icin 2010-ilk_tarih araligi 'veri yok' demektir, 'kazanc duyurusu yok' DEMEZ.",
    "8) YABANCI IHRACCI (FPI) BOSLUGU: 6-K/20-F ile raporlayan sirketlerde 8-K/2.02 hic yoktur. "
    "SPOT: 259 sembol icinde 2.02 satiri OLMAYAN tek sembol. NXPI: CIK 2007'den beri var ama "
    "ilk 2.02 2019-10-29 (yerli-ihracci statusune gecis). Bu semboller kazanc-tabanli her "
    "dilimde None sayilir, sifir DEGIL.",
    "9) OLAY COKLUGU: ayni kazanc olayi icin birden cok 2.02 satiri olabilir (on-duyuru, "
    "ertesi-gun tamamlayici, ek materyal). 133 ayni-gun cift; 14 gunluk kumeleme 716 satiri "
    "birlestiriyor. Kumeleme penceresi bir MODEL SECIMIDIR — CSV ham birakildi, secim ve "
    "gerekcesi olcum kartinda beyan edilir.",
]

kaynak = {
    "ne": "SEC EDGAR submissions ucundan cikarilmis 8-K / Item 2.02 (Results of Operations and "
          "Financial Condition) dosyalama gunleri — TARIHSEL KAZANC-DUYURU TARIHI VEKILI.",
    "amac": "EDG-2026-011 (in-play onceliklendirme) askisinin (b) yeniden-acilma yolu. "
            "BU TUR OLCUM DEGIL; kart revizyonu Rol-1'e aittir.",
    "olusturma_utc_gun": date.today().isoformat(),
    "indirme_penceresi_utc": [zamanlar[0], zamanlar[-1]] if zamanlar else None,
    "url_sablonlari": {
        "submissions_ana": "https://data.sec.gov/submissions/CIK{cik:010d}.json",
        "submissions_eski_sayfa": "https://data.sec.gov/submissions/{filings.files[].name}",
        "not": "recent blogu yalnizca son ~1000 dosyalamayi tasir; 2010'a inmek icin "
               "filings.files sayfalari da cekildi (filingTo >= 2010-01-01 olanlar).",
    },
    "istek_politikasi": {
        "user_agent": "Meridian Research oztrkerdem@gmail.com",
        "istek_arasi_gecikme_sn": 0.15,
        "etkin_hiz": "<= ~6.7 istek/sn (SEC siniri 10/sn; brief siniri 8/sn)",
        "sirali": True, "yeniden_deneme": "yok — hata manifest'e yazilir, sessiz yutulmaz",
        "toplam_istek": len(man),
    },
    "evren": {
        "cik_haritasi": "research/edgar_facts/cik_haritasi.json",
        "sembol_sayisi_haritada": 259,
        "benzersiz_cik": len({m["cik"] for m in man}),
        "2.02_satiri_olan_sembol": len(by_sym),
        "2.02_satiri_OLMAYAN_sembol": dog["C_anomali"]["satirsiz_sembol"],
    },
    "kapsam_ozeti": dog["kapsam"],
    "filtre": {"form": "8-K (yalniz; 8-K/A haric)",
               "items": "virgul ile ayrilmis token'lardan biri '2.02' ile basliyor",
               "tarih": "filed >= 2010-01-01",
               "haric_tutulan_8KA_2.02_satiri": len(amend)},
    "VEKIL_YANLILIK_BEYANI": VEKIL_BEYAN,
    "dogrulama": {
        "A_ucuncu_taraf_takvim": {k: v for k, v in dog["A_ucuncu_taraf_takvim"].items()
                                  if k != "eslesme"},
        "A_eslesme_ornekleri": dog["A_ucuncu_taraf_takvim"]["eslesme"][:12],
        "B_companyfacts_accession": {k: v for k, v in dog["B_companyfacts_accession"].items()
                                     if k != "bulunmayan_ornek"},
        "C_anomali_sayilar": dog["C_anomali_sayilar"],
        "C_anomali_ayrinti": dog["C_anomali"],
        "E_kamuya_bilinen_gunler": dog["E_kamuya_bilinen_gunler"],
        "F_olay_kumeleme": dog["F_olay_kumeleme"],
        "filed_eksi_report_date": dog["filed_eksi_report_date"],
        "acceptance_saat_dilimi_testi": {
            k: ({kk: vv for kk, vv in v.items() if kk != "et_saat_histogram"}
                if isinstance(v, dict) else v)
            for k, v in dog["acceptance_saat_dilimi_testi"].items()},
        "acceptance_ham_saat_histogram": dog["acceptance_ham_saat_histogram"],
    },
    "cikti_dosyalari": [
        {"dosya": "earnings_8k_tarihleri.csv", "satir": len(rows),
         "bayt": os.path.getsize(CSV_YOL), "sha256": sha,
         "kolonlar": ["symbol", "cik", "filed", "report_date", "acceptance", "items", "accn"]},
    ],
    "ham_json_konumu": "scratchpad/edgar_8k/raw/ — ham submissions JSON'lari depoya KONULMADI "
                       "(~%d MB). Manifestteki sha256 ham (sikistirilmamis) JSON baytlarinindir."
                       % (sum(m["bytes"] for m in man) // 1_000_000),
    "yan_ciktilar": {
        "dogrulama_ayrintisi": "scratchpad/edgar_8k/dogrulama_8k.json",
        "8KA_envanteri": "scratchpad/edgar_8k/amend_2_02.json",
        "indirme_gunlugu": "scratchpad/edgar_8k/download.log",
    },
    "betikler": ["research/edgar_facts/betikler/download_8k.py",
                 "research/edgar_facts/betikler/extract_8k.py",
                 "research/edgar_facts/betikler/validate_8k.py",
                 "research/edgar_facts/betikler/make_kaynak_8k.py"],
    "ham_indirme_manifesti": [
        {k: m.get(k) for k in ("cik", "symbols", "tur", "url", "http", "bytes", "sha256",
                               "indirme_utc", "hata")}
        for m in man],
}

with open(f"{FACTS}/kaynak_8k.json", "w") as f:
    json.dump(kaynak, f, indent=1, ensure_ascii=False)
print("kaynak_8k.json yazildi:", os.path.getsize(f"{FACTS}/kaynak_8k.json"), "bayt")
print("hatali istek:", sum(1 for m in man if m.get("http") != 200))
print("csv sha256:", sha)
