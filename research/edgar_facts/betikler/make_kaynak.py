"""kaynak.json: koken (URL sablonlari, indirme zamani, UA), kapsam ozeti, sha256 toplamlari."""
import gzip, hashlib, json, os, time

import pandas as pd

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = "/Users/erdemozturk/AI-Trading/research/edgar_facts"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    man = json.load(open(os.path.join(WORK, "download_manifest.json")))
    cikmap = json.load(open(os.path.join(WORK, "cikmap.json")))
    rapor = json.load(open(os.path.join(WORK, "validate_rapor.json")))
    kap = pd.read_csv(os.path.join(OUT, "kapsam.csv"))

    import calendar
    ts = sorted(calendar.timegm(time.strptime(m["indirme_utc"], "%Y-%m-%dT%H:%M:%SZ"))
                for m in man)
    sn_araligi = ts[-1] - ts[0]

    dosyalar = []
    for fn in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, fn)
        if os.path.isfile(p) and fn not in ("kaynak.json",):
            dosyalar.append({"dosya": fn, "bayt": os.path.getsize(p), "sha256": sha(p)})

    kaynak = {
        "ne": "SEC EDGAR XBRL companyfacts'ten cikarilmis PIT hisse-adedi ve temel-veri serileri",
        "olusturma_utc": max(m["indirme_utc"] for m in man),
        "indirme_penceresi_utc": [min(m["indirme_utc"] for m in man),
                                  max(m["indirme_utc"] for m in man)],
        "url_sablonlari": {
            "companyfacts": "https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json",
            "ticker_cik_haritasi": "https://www.sec.gov/files/company_tickers.json",
            "delist_ticker_cozumu":
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<ticker>&type=10-K&output=atom",
        },
        "istek_politikasi": {
            "user_agent": "Meridian Research oztrkerdem@gmail.com",
            "istek_arasi_gecikme_sn": 0.15,
            "olculen_hiz_yogun_cekim_istek_sn": 1.47,
            "olculen_hiz_notu": (
                "1.47 = 257 istek / 175 sn, download.log ilerleme satirlarindan. Dosya "
                "mtime araligindan hesaplanan 0.6 istek/sn ise XOM oncul CIK'inin daha "
                "sonra elle eklenmesini de icerdigi icin YANILTICIDIR."),
            "sirali_tek_baglanti": True,
            "sec_fair_use": (
                "SEC EDGAR fair-access politikasi: otomatik erisimde 10 istek/sn ust siniri ve "
                "kimlik bildiren User-Agent (isim + e-posta) ZORUNLUDUR. Bu cekim sirali, tek "
                "baglantili ve 1.47 istek/sn olcumuyle o sinirin cok altinda kaldi. Veri kamuya "
                "acik ve telifsizdir (ABD federal kurum yayini); yeniden dagitimda kaynak "
                "belirtilir. Tekrar cekimde ayni gecikmeyi KORU."),
        },
        "evren": {
            "kaynak": "meridian.adapters.data.REPLAY_UNIVERSE (251) + RETIRED_SYMBOLS (8)",
            "benzersiz_sembol_n": len({r["symbol"] for r in cikmap["eslesen"]}),
            "harita_kayit_n": len(cikmap["eslesen"]),
            "harita_kayit_notu": "XOM iki CIK ile kayitli (guncel 2115436 + oncul 34088)",
            "benzersiz_cik_n": len({r["cik"] for r in cikmap["eslesen"]}),
            "cik_paylasilan_gruplar": cikmap["paylasilan_cik"],
            "eslesmeyen": cikmap["eslesmeyen"],
            "not_spy": "SPY (state/bars'ta var) bir ETF trostu; sirket temel-verisi yok, cekilmedi",
        },
        "kapsam_ozeti": kap.to_dict("records"),
        "spot_dogrulama": rapor["spot"],
        "tutarsizlik_ozeti": {k: (len(v) if isinstance(v, list) else v)
                              for k, v in rapor["tutarsizlik"].items()},
        "cikti_dosyalari": dosyalar,
        "ham_indirme_manifesti": man,
        "ham_json_konumu": (
            "scratchpad/edgar_ingest/raw/CIK##########.json.gz — ham companyfacts depoya "
            "KONULMADI (~1 GB). Manifestteki sha256 ham (sikistirilmamis) JSON baytlarinindir."),
    }
    with open(os.path.join(OUT, "kaynak.json"), "w") as f:
        json.dump(kaynak, f, indent=1, ensure_ascii=True)
    print("kaynak.json yazildi;", len(dosyalar), "cikti dosyasi")
    for d in dosyalar:
        print(f"  {d['dosya']:32s} {d['bayt']/1e6:8.2f} MB  {d['sha256'][:16]}")


if __name__ == "__main__":
    main()
