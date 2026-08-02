"""kapsama_kys.py — KYS-2026-001 ADIM 2: OLAY-ETİKETLEME KAPSAMASI (kart kill #2).

KARTIN KILL MADDESİ (birebir): "temiz-kıyas aracı olay-pencerelerini takvim kapsamasındaki
boşluklar yüzünden evrenin >%20'sinde etiketleyemiyorsa → 'ölçülemedi' beyanı, kart askıya
(earnings kapsaması kalemine bağlanır); UYDURMA YASAK".

ETİKETLENEBİLİRLİK TANIMI (ölçümden önce yazıldı). Bir ölçüm satırı (t, g) ancak ve ancak takvim
[g, g+5] GÜN ARALIĞINI GERÇEKTEN GÖRMÜŞSE etiketlenebilir. Gerekçe: `in_blackout(t, g)` yalnız o
aralıkta t'nin rapor tarihi olup olmadığına bakar; takvim o aralığı hiç sorgulamamışsa dönen False
"karartma yok" DEĞİL "veri yok"tur (modülün beyanlı FAIL-OPEN'ı, `earnings.COVERAGE_NOTE`). İkisini
aynı saymak, tam da bu kartın avladığı hata sınıfıdır — ölçüm kendi körlüğünü "temiz" diye okur.

İKİ EKSEN, İKİ SINIR:
  * SEMBOL ekseni — evrenin kaçı takvimde HİÇ geçiyor.
  * SATIR ekseni  — ölçüm satırlarının kaçının [g, g+5] aralığı takvimin GÜN kapsamasında.
    Gün kapsaması yalnız GÜN BAZINDA sorgulanmış bir kaynakta kesin bilinir (Nasdaq önbelleği:
    sorulan iş günleri dosyada). `state/earnings.csv` bir BİRİKİMDİR ve hangi günlerin sorulduğu
    kaydı YOKTUR → iki sınır birden raporlanır:
       - CÖMERT: [ilk tarih, son tarih] aralığının tamamı görülmüş SAYILIR (gerçekte içi delik)
       - SIKI  : yalnız gözlenmiş bir takvim tarihinin ±5 günü görülmüş sayılır
    Gerçek ikisinin arasındadır; cömert sınır bile kapıdan geçemiyorsa hüküm tartışmasızdır.

BU DOSYA HÜKÜM VERMEZ: sayıyı üretir, kill kararını Rol-1 verir.
"""
from __future__ import annotations

import datetime as dt
import json

import ortak_kys as ok

ok.muhurle()

from meridian import earnings                    # noqa: E402
from meridian.adapters import data as da         # noqa: E402

CANLI_TAKVIM = ok.DEPO / "state" / "earnings.csv"
SPRINT_TAKVIM = (ok.DEPO / "state" / "sprint" / "20260722-093305" / "state" / "earnings.csv")


# ==================================================================================================
# ÖLÇÜM SATIRLARI (yüzeylerin popülasyonu)
# ==================================================================================================
def olcum_satirlari() -> dict:
    """{katman: [(ticker, 'YYYY-MM-DD'), ...]} — `component_ic._rows` ile AYNI tanım.

    cf katmanı `counterfactual.resolved_rows(entered_only=True)`; gerçek katman `trades.jsonl`in
    `plan_id` ayrıştırması (P-YYYY-MM-DD-TICKER). İki tanım kopyalanmadı, kaynak modülün kendi
    fonksiyonları çağrıldı — ikinci bir popülasyon tanımı iki farklı paydayı sessizce üretirdi."""
    from meridian import counterfactual as cf, store
    cf_rows = [(str(r["ticker"]).upper(), str(r["date"])[:10])
               for r in cf.resolved_rows(entered_only=True)
               if r.get("ticker") and r.get("date")]
    gercek = []
    for t in store.read_jsonl("trades.jsonl"):
        pid = str(t.get("plan_id") or "")
        parts = pid.split("-")
        if pid.startswith("P-") and len(parts) >= 5:
            gercek.append((parts[4].upper(), "-".join(parts[1:4])))
    return {"cf": cf_rows, "gercek": gercek}


# ==================================================================================================
# KAPSAMA
# ==================================================================================================
def _gun_kapsamasi_nasdaq() -> set:
    """Nasdaq önbelleğinde GERÇEKTEN sorulmuş iş günleri (dosyada satırı olan gün)."""
    gunler = set()
    for p in sorted(ok.TAKVIM_ONBELLEK.glob("gunler*.jsonl")):
        for satir in p.read_text(encoding="utf-8").splitlines():
            try:
                gunler.add(json.loads(satir)["date"])
            except Exception:  # noqa: BLE001 — bozuk satır sorulmamış sayılır (uydurma yok)
                continue
    return gunler


def nasdaq_takvimi() -> tuple[dict, set]:
    """Önbellekten {TICKER: [tarih]} + sorulmuş gün kümesi. Yalnız evren sembolleri."""
    takvim: dict = {}
    gunler = set()
    for p in sorted(ok.TAKVIM_ONBELLEK.glob("gunler*.jsonl")):
        for satir in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(satir)
            except Exception:  # noqa: BLE001
                continue
            gunler.add(r["date"])
            for t in r.get("syms") or []:
                takvim.setdefault(t, []).append(r["date"])
    return {t: sorted(set(ds)) for t, ds in takvim.items()}, gunler


def _etiketlenebilir(satirlar, gorulen_gunler: set, pencere_gun: int = ok.BLACKOUT_DAYS) -> dict:
    """[g, g+pencere] aralığının TAMAMI görülmüş mü? Kısmi görülen aralık da ETİKETLENEMEZ sayılır:
    aralığın görülmeyen yarısında bir rapor tarihi olabilir ve 'karartmada değil' cevabı o ihtimali
    ölçmeden reddederdi."""
    tam = kismi = hic = 0
    for _t, g in satirlar:
        d0 = dt.date.fromisoformat(g)
        araliktaki = [(d0 + dt.timedelta(days=i)).isoformat() for i in range(pencere_gun + 1)]
        # yalnız İŞ GÜNLERİ sorulur; hafta sonları kapsama sorusunun dışındadır (rapor tarihi de
        # iş günüdür — Nasdaq takvimi hafta sonu satırı üretmez)
        is_gunleri = [x for x in araliktaki if dt.date.fromisoformat(x).weekday() < 5]
        gorulen = sum(1 for x in is_gunleri if x in gorulen_gunler)
        if not is_gunleri or gorulen == len(is_gunleri):
            tam += 1
        elif gorulen:
            kismi += 1
        else:
            hic += 1
    n = len(satirlar)
    return {"n": n, "tam_gorulen": tam, "kismi": kismi, "hic_gorulmemis": hic,
            "etiketlenebilir_oran": round(tam / n, 4) if n else None,
            "etiketlenemeyen_oran": round((n - tam) / n, 4) if n else None}


# ÖLÇÜM AÇIKLIĞI (yüzeylerin tarih aralığı) — tamlık bu aralıkta ölçülür
OLCUM_ILK, OLCUM_SON = "2022-01-03", "2026-07-23"
YIL = (dt.date.fromisoformat(OLCUM_SON) - dt.date.fromisoformat(OLCUM_ILK)).days / 365.25
CEYREK_YIL = 4.0          # halka açık şirket yılda ~4 kez rapor verir (tamlık paydası)


def _tamlik(takvim: dict, evren: set) -> dict:
    """TAKVİM TAMLIĞI — ölçüm aralığında ticker başına GÖZLENEN olay / BEKLENEN olay (~4/yıl).

    NEDEN GÜN-KAPSAMASININ YANINDA BU DA GEREKLİ. Gün kapsaması yalnız GÜN BAZINDA sorgulanan bir
    kaynakta (Nasdaq önbelleği) kesin bilinir. `state/earnings.csv` gibi BİRİKİM dosyalarında hangi
    günün sorulduğu kayıtlı değildir ve "yakınında bir tarih var" ölçütü yanıltıcıdır: dosyada
    BAŞKA bir sembolün tarihi bulunması, ELDEKİ sembolün o çeyrekteki raporunun bilindiğini
    göstermez. Tamlık bu boşluğu doğrudan ölçer ve uydurmaya yer bırakmaz."""
    beklenen = CEYREK_YIL * YIL
    gozlenen = {t: len([d for d in ds if OLCUM_ILK <= d <= OLCUM_SON])
                for t, ds in takvim.items() if t in evren}
    if not gozlenen:
        return {"olculemedi": "takvimde evren sembolü yok", "beklenen_ticker_basina": round(beklenen, 1)}
    dizi = sorted(gozlenen.values())
    toplam = sum(dizi)
    return {"beklenen_ticker_basina": round(beklenen, 1),
            "gozlenen_medyan": dizi[len(dizi) // 2],
            "gozlenen_ortalama": round(toplam / len(dizi), 2),
            "tamlik_orani": round((toplam / len(dizi)) / beklenen, 4) if beklenen else None,
            "hic_tarihi_olmayan_evren_sembolu": len(evren) - len([v for v in dizi if v]),
            "aralik": [OLCUM_ILK, OLCUM_SON],
            "beyan": "gözlenen/beklenen; beklenen = 4 rapor/yıl × ölçüm aralığı (yıl)"}


def _cesitli(takvim: dict, evren: set) -> dict:
    tarihler = [d for ds in takvim.values() for d in ds]
    return {"n_ticker": len(takvim), "n_satir": len(tarihler),
            "ilk_tarih": min(tarihler) if tarihler else None,
            "son_tarih": max(tarihler) if tarihler else None,
            "evren_kesisimi": len(set(takvim) & evren),
            "sembol_kapsamasi": round(len(set(takvim) & evren) / len(evren), 4) if evren else None,
            "takvim_tamligi": _tamlik(takvim, evren)}


def kos() -> dict:
    evren = {s.upper() for s in da.REPLAY_UNIVERSE}
    satirlar = olcum_satirlari()
    hepsi = satirlar["cf"] + satirlar["gercek"]

    out: dict = {"adim": "2 — olay-etiketleme kapsaması (kart kill #2)",
                 "evren": len(evren),
                 "olcum_satirlari": {k: len(v) for k, v in satirlar.items()},
                 "tarih_araligi": {k: [min(d for _, d in v), max(d for _, d in v)]
                                   for k, v in satirlar.items() if v},
                 "esik": {"kill_2": "etiketlenemeyen > %20 → 'ölçülemedi'",
                          "tanim": "satır (t,g) etiketlenebilir ⟺ takvim [g, g+5] iş günlerinin "
                                   "TAMAMINI görmüş"},
                 "kaynaklar": {}}

    # --- 1) CANLI state/earnings.csv --------------------------------------------------------------
    canli = ok.takvim_oku(CANLI_TAKVIM)
    canli_gunler = {d for ds in canli.values() for d in ds}
    comert = set()
    if canli_gunler:
        a, b = dt.date.fromisoformat(min(canli_gunler)), dt.date.fromisoformat(max(canli_gunler))
        comert = {(a + dt.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)}
    siki = set()
    for d in canli_gunler:
        d0 = dt.date.fromisoformat(d)
        siki |= {(d0 + dt.timedelta(days=i)).isoformat()
                 for i in range(-ok.BLACKOUT_DAYS, ok.BLACKOUT_DAYS + 1)}
    out["kaynaklar"]["state/earnings.csv"] = {
        **_cesitli(canli, evren),
        "gun_kapsamasi_kaydi": None,
        "gun_kapsamasi_kaydi_neden": ("birikim dosyası — hangi günlerin sorulduğu kaydı YOK "
                                      "(PIT defteri state/history/earnings_snapshots.jsonl yerelde "
                                      "mevcut değil); iki SINIR raporlanır"),
        "comert_sinir": _etiketlenebilir(hepsi, comert),
        "siki_sinir": _etiketlenebilir(hepsi, siki)}

    # --- 2) SPRINT kum havuzundaki eski kopya ------------------------------------------------------
    if SPRINT_TAKVIM.exists():
        sp = ok.takvim_oku(SPRINT_TAKVIM)
        sp_gunler = {d for ds in sp.values() for d in ds}
        sp_siki = set()
        for d in sp_gunler:
            d0 = dt.date.fromisoformat(d)
            sp_siki |= {(d0 + dt.timedelta(days=i)).isoformat()
                        for i in range(-ok.BLACKOUT_DAYS, ok.BLACKOUT_DAYS + 1)}
        # ticker başına 2022+ tarih sayısı — "derin geçmiş kaç sembolde" sorusunun cevabı
        derin = {t: len([d for d in ds if d >= "2022-01-01"]) for t, ds in sp.items()}
        out["kaynaklar"]["state/sprint/.../earnings.csv"] = {
            **_cesitli(sp, evren),
            "2022+_tarihi_olan_ticker": sum(1 for v in derin.values() if v),
            "ticker_basina_2022+_medyan": sorted(derin.values())[len(derin) // 2] if derin else None,
            "siki_sinir": _etiketlenebilir(hepsi, sp_siki)}

    # --- 3) NASDAQ (bu turda kum havuzuna çekilen geçmiş) -----------------------------------------
    nas, sorulan = nasdaq_takvimi()
    if sorulan:
        out["kaynaklar"]["nasdaq_kum_havuzu"] = {
            **_cesitli(nas, evren),
            "sorulan_is_gunu": len(sorulan),
            "sorulan_ilk": min(sorulan), "sorulan_son": max(sorulan),
            "gun_kapsamasi_kaydi": "VAR — sorulan iş günleri dosyada satır satır duruyor",
            "kesin": _etiketlenebilir(hepsi, sorulan),
            "katman_kirilimi": {k: _etiketlenebilir(v, sorulan) for k, v in satirlar.items()}}

        # --- TARİH DOĞRULUĞU: bilinen gerçeğe karşı sağlama (UYDURMA YASAĞI) ----------------------
        # Bir takvimin "tam" olması onu DOĞRU yapmaz. EAP turunun kullandığı aynı sağlama burada da
        # koşar: bilinen 2024 duyuru tarihleri, kaynağın döndürdükleriyle karşılaştırılır.
        bilinen = {"AAPL": ["2024-02-01", "2024-05-02", "2024-08-01", "2024-10-31"],
                   "MSFT": ["2024-01-30", "2024-04-25", "2024-07-30", "2024-10-30"],
                   "JPM": ["2024-01-12", "2024-04-12", "2024-07-12", "2024-10-11"],
                   "NVDA": ["2024-02-21", "2024-05-22", "2024-08-28", "2024-11-20"]}
        sag = {}
        for t, dogru in bilinen.items():
            bulunan = [d for d in nas.get(t, []) if d.startswith("2024")]
            sag[t] = {"beklenen": dogru, "bulunan": bulunan, "birebir": bulunan == dogru}
        out["tarih_dogrulugu"] = {"semboller": sag,
                                  "hepsi_birebir": all(v["birebir"] for v in sag.values()),
                                  "beyan": "kaynak 2024 duyuru tarihleri bilinen gerçeğe karşı "
                                           "sağlandı (EAP turunun aynı sağlaması)"}

        # --- OLAY YAYGINLIĞI: ölçüm satırlarının kaçı KENDİ penceresinde (EAP'nin %64/%74 ikizi) ---
        yol = ok.KUM_HAVUZU / "state" / "earnings.csv"
        ok.takvim_yaz(nas, yol)
        earnings.clear_cache()
        kirli = sum(1 for t, g in hepsi if earnings.in_blackout(t, g))
        out["olay_yayginligi"] = {
            "n_satir": len(hepsi), "penceresinde": kirli,
            "oran": round(kirli / len(hepsi), 4) if hepsi else None,
            "yontem": "earnings.in_blackout, kum havuzuna yazılan Nasdaq takvimiyle",
            "beyan": "ölçüm satırlarının kendi kazanç penceresinde olma oranı (hedef tarafı); "
                     "TABAN tarafının kirliliği ölçüm adımında gün gün raporlanır"}
    else:
        out["kaynaklar"]["nasdaq_kum_havuzu"] = {"durum": "önbellek BOŞ — çekim koşmadı"}

    out["muhur"] = ok.muhur_dogrula()
    out["hukum_yok"] = "sayı üretildi; kill #2 hükmü Rol-1'dedir"
    return out


if __name__ == "__main__":
    r = kos()
    (ok.CIKTI / "kapsama_kys001.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2)[:4000])
