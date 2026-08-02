"""takvim_cek.py — KAZANÇ TAKVİMİNİN GEÇMİŞİ (kum havuzuna, anahtarsız, 0 kota).

NEDEN GEREKİYOR. Kartın 2. kill maddesi olay-ETİKETLEME kapsamasını şart koşuyor. Yerelde duran
`state/earnings.csv` yalnız İLERİ takvimdir (194 satır, 2026-07/08) — yani ölçüm yüzeylerinin
(component_ic satırları ve cf defteri: 2022-01 → 2026-07) neredeyse tamamında bir satırın olay
penceresinde olup olmadığı BİLİNEMEZ. `in_blackout` orada False döner ama bu "temiz" demek değil,
"veri yok" demektir (modülün beyanlı fail-open'ı) ve ikisini aynı saymak tam da bu kartın avladığı
hata sınıfıdır.

NEDEN BU KAYNAK. `earnings.refresh`in BİRİNCİL kaynağı Nasdaq'ın ANAHTARSIZ takvimidir
(`adapters.data.nasdaq_earnings_window`) ve geçmiş günleri de servis eder. Kaynak yeniden
YAZILMADI, ÇAĞRILDI. FMP'ye gidilmez: ticker başına bir istek = 250 evren = günlük kotanın tamamı.
EAP turu (2026-07-31) aynı yolu koştu: 3.283 gün-isteği, 0 hata, 0 FMP çağrısı.

NEREYE YAZAR. YALNIZ kum havuzuna (`ortak_kys.TAKVIM_ONBELLEK`). Canlı `state/earnings.csv`e,
`state/history/`ye ve `fmp_usage.json`a TEK BAYT yazılmaz — mühür `ortak_kys.muhurle` ile kurulur
ve `muhur_dogrula` ile kanıtlanır.

YENİDEN BAŞLATILABİLİR: her gün bir JSONL satırıdır; var olan günler atlanır. Yarıda kesilen bir
koşum, kaçan günü "boş gün" diye YAZMAZ — dosyada satırı olmayan gün, sorulmamış gündür.
"""
from __future__ import annotations

import json
import sys

import ortak_kys as ok

ok.muhurle()

import pandas as pd                              # noqa: E402
from meridian.adapters import data as da         # noqa: E402

BASLANGIC = "2022-01-01"      # cf defterinin ilk satırı 2022-01-03
BITIS = "2026-08-05"          # cf defterinin son satırı 2026-07-23 (+ ufuk payı)

# PARALEL DİLİM: gün başına ~3 sn yanıt süresi ölçüldü (1.198 iş günü ≈ 64 dk seri). Dilim başına
# AYRI dosya yazılır; `_yapilmis` TÜM dilimleri okur, yani iki işçi aynı günü iki kez sormaz ve
# yarıda kesilen koşum kaldığı yerden devam eder. Eşzamanlılık DÖRTLE sınırlı — anahtarsız bir
# kamu ucuna karşı görgü kuralı (adaptörün kendi 0,25 sn gecikmesi de yerinde durur).


def _yapilmis() -> set:
    out = set()
    for p in sorted(ok.TAKVIM_ONBELLEK.glob("gunler*.jsonl")):
        for satir in p.read_text(encoding="utf-8").splitlines():
            try:
                out.add(json.loads(satir)["date"])
            except Exception:  # noqa: BLE001 — bozuk satır YOK sayılır; gün yeniden sorulur (uydurma yok)
                continue
    return out


def kos(baslangic: str = BASLANGIC, bitis: str = BITIS, dosya_adi: str = "gunler.jsonl") -> dict:
    DOSYA = ok.TAKVIM_ONBELLEK / dosya_adi
    ok.TAKVIM_ONBELLEK.mkdir(parents=True, exist_ok=True)
    evren = {s.upper() for s in da.REPLAY_UNIVERSE}
    gunler = [str(d.date()) for d in pd.bdate_range(baslangic, bitis)]
    yapilmis = _yapilmis()
    kalan = [g for g in gunler if g not in yapilmis]
    print(f"[takvim] istenen={len(gunler)} yapılmış={len(yapilmis)} kalan={len(kalan)}", flush=True)

    ok_gun = dusen = 0
    dusen_gunler: list = []
    with open(DOSYA, "a", encoding="utf-8") as fh:
        for i, g in enumerate(kalan):
            st: dict = {}
            r = da.nasdaq_earnings_window(g, g, with_time=True, stats=st)
            if st.get("cevaplayan"):
                # EVREN FİLTRESİ: ham takvim ~78k satır (tüm borsa); bize yalnız 251 sembol lazım.
                # Filtre BURADA yapılır ki önbellek dosyası küçük ve okunabilir kalsın; düşen
                # sembol sayısı da yazılır ki "boş gün" ile "evrenimizden kimse yok" ayrılabilsin.
                kayit = {t: [x[0] if isinstance(x, (tuple, list)) else x for x in ds]
                         for t, ds in r.items() if t in evren}
                fh.write(json.dumps({"date": g, "n_ham_sembol": len(r),
                                     "syms": sorted(kayit)}, ensure_ascii=False) + "\n")
                fh.flush()
                ok_gun += 1
            else:
                dusen += 1
                if len(dusen_gunler) < 40:
                    dusen_gunler.append(g)
            if (i + 1) % 100 == 0:
                print(f"[takvim] {i + 1}/{len(kalan)} · ok={ok_gun} düşen={dusen}", flush=True)

    toplam = _yapilmis()
    dilim_kapsama = len([g for g in gunler if g in toplam]) / len(gunler) if gunler else None
    ozet = {"dilim": [baslangic, bitis], "istenen_is_gunu": len(gunler),
            "dilim_kapsama": round(dilim_kapsama, 4) if dilim_kapsama is not None else None,
            "onbellekte_toplam_gun": len(toplam),
            "bu_kosumda_ok": ok_gun, "bu_kosumda_dusen": dusen,
            "dusen_gunler_ornek": dusen_gunler,
            "kaynak": "nasdaq (anahtarsız) · 0 FMP çağrısı",
            "muhur": ok.muhur_dogrula()}
    (ok.TAKVIM_ONBELLEK / f"cekim_ozeti_{baslangic}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in ozet.items() if k != "dusen_gunler_ornek"},
                     ensure_ascii=False), flush=True)
    return ozet


if __name__ == "__main__":
    a = sys.argv[1:]
    o = kos(a[0] if a else BASLANGIC, a[1] if len(a) > 1 else BITIS,
            a[2] if len(a) > 2 else "gunler.jsonl")
    sys.exit(0 if (o["dilim_kapsama"] or 0) >= 0.99 else 4)
