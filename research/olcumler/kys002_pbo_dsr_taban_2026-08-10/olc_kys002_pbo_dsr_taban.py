"""KYS-2026-002 — PBO/DSR R1 TABAN ÖLÇÜM MODÜLÜ (kart: research/cards/KYS-2026-002-pbo-dsr-r1-taban.yaml)

NE YAPAR. Donmuş canlı kopyadan (canli_kopya/) YALNIZ pencere_id=="R1" popülasyonunu alır ve
kapının KENDİ motoru `meridian/validation.py` fonksiyonlarıyla (pbo_cscv + pbo_kapi + dsr_kapi +
_moments; yeniden-implementasyon YOK) pencere-başına PBO tabanını hesaplar, mod-farkındalıklı
kapı-tablosu hücrelerini işaretler ve sonucu `sonuc.json`a yazar.

OKUYUCU (YASA 6): sonuc.json'un okuyucusu Rol-1 hükmü + kartın §4 işleme adımıdır; bu modülün
kendisi yeniden-koşum aracıdır (aynı kopya → aynı sayılar).

KILL DAVRANIŞLARI (kart kill_criteria AYNEN):
  kill#1 — pencere-başına aday < PBO_MIN_ADAY(8) → o pencere 'olculemedi' (pbo_cscv zaten böyle
           davranır; modül ekstra eşik uygulamaz).
  kill#2 — motor fonksiyonu değişiklik GEREKTİRMEDEN kullanılamıyorsa (imza/VERİ-ŞEKLİ uyuşmazlığı)
           → o ölçüm DURUR, 'araç turu gerekir' yazılır. BU KOŞUMDA TETİKLENDİ (DSR yarısı):
           kapının DSR girdisi `_ret` = pnl_dollars/START_EQUITY, TÜM arama işlemleri
           (reflect.py:559); kopyadaki `seri` ise (kapanış günü, r_multiple) ve ts_close'suz
           işlemleri dışlar (reflect.py:710-711). Sharpe/skew/kurtosis ölçek-değişmez olduğundan
           eşdeğerlik ancak işlem-başına risk sabitse mümkündü — bu VARSAYILMADI, ÖLÇÜLDÜ:
           motorun kendi `_moments`'ıyla seri-Sharpe her satırda damga `sharpe_gozlem`den sapıyor
           (asgari sapma bile 4-hane yuvarlama düzeyinin üstünde). `seri`den "taze küme-DSR"
           üretmek kapının GERÇEKTE GÖRMEYECEĞİ bir sayı üretirdi (kartın yasakladığı
           basitleştirilmiş ikame). → taze aday-kümesi DSR: OLCULEMEDI + araç turu gerekir.
  kill#3 — kopya satır sayısı != 383 → ölçüm GEÇERSİZ, hiçbir değer üretilmez.

EŞİK İCAT EDİLMEDİ: kapı hücreleri motorun donuk eşikleriyle (PBO_HARD_MAX=0.20, DSR_HARD_MIN=0.95,
fail-closed) motorun kendi `pbo_kapi`/`dsr_kapi` fonksiyonlarından okunur. `YUVARLAMA_DUZEYI`
bir hüküm eşiği DEĞİL, kopya-veri özdeşlik ölçütüdür: `seri` 4 haneye yuvarlanarak yazılır
(reflect.py:710) ve |R|≈O(1) serilerde bunun Sharpe'a taşıyabileceği hata ~1e-4 mertebesindedir;
sapma bunun üstündeyse iki seri AYNI ölçümün iki yazımı değil, İKİ FARKLI SERİdir.

CANLIYA DOKUNMAZ: girdi yalnız canli_kopya/ dosyaları; state/ okunmaz-yazılmaz; kart dosyasına
dokunulmaz. `validation` YALNIZ ithal edilir; satır listeleri fonksiyonlara AÇIKÇA geçirilir
(varsayılan `ledger()` yolu state okurdu — bilinçli olarak hiç çağrılmaz).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
REPO = KOK.parents[2]
sys.path.insert(0, str(REPO))

from meridian import validation as V  # noqa: E402  (motor — YALNIZ OKU/İTHAL)

KOPYA = KOK / "canli_kopya"
LEDGER_KOPYA = KOPYA / "validation_ledger.jsonl"
EROSION_KOPYA = KOPYA / "oos_erosion.json"
SONUC = KOK / "sonuc.json"

PENCERE = "R1"
BEKLENEN_TOPLAM = 383   # kart evidence_refs: kanonik canlı sayım 2026-08-10 (kill#3 referansı)
BEKLENEN_R1 = 179       # kart: R1-damgalı yeni akış
# Kopya-veri özdeşlik ölçütü (hüküm eşiği DEĞİL — docstring'e bakınız): seri 4-hane yuvarlı,
# yuvarlamanın Sharpe'a taşıyabileceği hata mertebesi ~1e-4; bir kat pay ile 1e-3.
YUVARLAMA_DUZEYI = 1e-3


def _hucre(kapi: dict) -> dict:
    """Motorun kapı dönüşünü tablo hücresine indirger — hüküm METNİ motorundur, BLOKLAR/BLOKLAMAZ
    yalnız `ret` alanının okunuşudur (True=BLOKLAR)."""
    return {"mod": kapi.get("mod"), "hucre": "BLOKLAR" if kapi.get("ret") else "BLOKLAMAZ",
            "motor_hukum": kapi.get("hukum"), "ret": bool(kapi.get("ret")),
            "neden": kapi.get("neden"), "esik": kapi.get("esik")}


def main() -> int:
    rows = [json.loads(s) for s in LEDGER_KOPYA.read_text().splitlines() if s.strip()]
    sonuc: dict = {
        "kart": "KYS-2026-002", "olcum_tarihi": "2026-08-10", "pencere_id": PENCERE,
        "motor": "meridian/validation.py (pbo_cscv + pbo_kapi + dsr_kapi + _moments) — yeniden-implementasyon YOK",
        "girdi": {"ledger_kopya": str(LEDGER_KOPYA.relative_to(REPO)),
                  "oos_erosion_kopya": str(EROSION_KOPYA.relative_to(REPO))},
        "okuyucu": "Rol-1 hüküm + kart §4 (bu dosya ölçümdür, hüküm içermez)",
    }

    # ---- kill#3: kopya bütünlüğü --------------------------------------------------------------
    sonuc["kopya_butunluk"] = {"satir": len(rows), "beklenen": BEKLENEN_TOPLAM,
                               "tutuyor": len(rows) == BEKLENEN_TOPLAM}
    if len(rows) != BEKLENEN_TOPLAM:
        sonuc["durum"] = "GECERSIZ"
        sonuc["neden"] = (f"kill#3: kopya {len(rows)} satır != {BEKLENEN_TOPLAM} — kopya bozuk, "
                          f"tazelenmeli; hiçbir değer üretilmedi")
        SONUC.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps(sonuc, ensure_ascii=False, indent=1))
        return 2

    # ---- evren: YALNIZ pencere_id == R1 (damgasızlar tanımca dışarıda; sayıları raporlanır) ----
    r1_idx = [i for i, r in enumerate(rows) if r.get("pencere_id") == PENCERE]
    r1 = [rows[i] for i in r1_idx]
    damgasiz = sum(1 for r in rows if r.get("pencere_id") is None)
    diger = len(rows) - len(r1) - damgasiz
    sonuc["evren"] = {
        "r1_satir": len(r1), "beklenen_r1": BEKLENEN_R1, "tutuyor": len(r1) == BEKLENEN_R1,
        "damgasiz_satir_R1_oncesi": damgasiz, "baska_pencere_satiri": diger,
        "beyan": "damgasız 204 satır retro-damga yasağı gereği evren DIŞI — sayısı raporlanır, hükümde yok",
        # ship-yolu eşdeğerliği: reflect.py:1034 `ledger(limit=200)` SON 200 satırı alıp R1 süzer.
        "ship_yolu_esdegerligi": {
            "r1_bitisik": r1_idx == list(range(r1_idx[0], r1_idx[0] + len(r1_idx))) if r1_idx else None,
            "ilk_r1_dosya_indeksi": r1_idx[0] if r1_idx else None,
            "son200_kesiti_r1i_tam_kapsar": bool(r1_idx and r1_idx[0] >= len(rows) - V.LEDGER_CAP),
            "beyan": ("bu koşulda pbo_cscv(r1) girdisi, ship-yolunun (reflect.py:1034-1035) "
                      "göreceği girdiyle BİREBİR aynıdır")},
    }
    if len(r1) != BEKLENEN_R1:
        sonuc["durum"] = "GECERSIZ"
        sonuc["neden"] = (f"R1 sayımı {len(r1)} != {BEKLENEN_R1} — kopya, kartın kanonik sayımıyla "
                          f"uyuşmuyor; kopya tazelenmeli")
        SONUC.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps(sonuc, ensure_ascii=False, indent=1))
        return 2

    fp_sayim: dict = {}
    for r in r1:
        fp_sayim[r.get("fingerprint")] = fp_sayim.get(r.get("fingerprint"), 0) + 1
    sonuc["evren"]["fingerprint_dagilimi"] = fp_sayim
    sonuc["evren"]["tekil_etiket"] = len({r.get("etiket") for r in r1})
    sonuc["evren"]["passes_true"] = sum(1 for r in r1 if r.get("passes"))
    sonuc["evren"]["ts_araligi"] = [min(r["ts"] for r in r1), max(r["ts"] for r in r1)]

    # ---- PENCERE-BAŞINA PBO (havuzlama YASAK; R1 popülasyonunda tek pencere_id var: R1) --------
    # kill#1: aday < PBO_MIN_ADAY(8) hâlini pbo_cscv'nin KENDİSİ 'olculemedi' döndürerek işler.
    pbo = V.pbo_cscv(r1)
    pbo_paper, pbo_live = V.pbo_kapi(pbo, live=False), V.pbo_kapi(pbo, live=True)
    sonuc["pbo_pencere_basina"] = {
        PENCERE: {
            "motor_cikti": pbo,
            "kill1_pbo_min_aday_alti": bool((pbo.get("n_aday") or 0) < V.PBO_MIN_ADAY),
            "kapi_tablosu": {"paper": _hucre(pbo_paper), "gercek_para": _hucre(pbo_live)},
        }
    }

    # ---- ADAY-KÜMESİ DSR — VERİ-ŞEKLİ EŞDEĞERLİK ÖLÇÜMÜ (varsayım değil, ölçüm) ---------------
    # Kapının DSR girdisi: `_ret` = pnl_dollars/START_EQUITY, TÜM _trades_search (reflect.py:559).
    # Kopyadaki `seri`: (ts_close günü, r_multiple 4-hane yuvarlı), ts_close'suzlar DIŞLANMIŞ
    # (reflect.py:710-711). Sharpe ölçek-değişmezdir → seri ancak işlem-başına risk sabitse ve
    # küme aynıysa `_ret`in eşdeğeridir. Test: motorun `_moments`'ıyla seri-Sharpe ↔ damga
    # `sharpe_gozlem` (motorun `_ret`ten hesapladığı değer, satıra damgalı).
    sapmalar = []
    damga_yok = moments_yok = 0
    for r in r1:
        vals = [c[1] for c in (r.get("seri") or []) if isinstance(c, (list, tuple)) and len(c) >= 2]
        mom = V._moments(vals)
        sg = r.get("sharpe_gozlem")
        if sg is None:
            damga_yok += 1          # kapının kendi DSR'ı o değerlendirmede ölçülememişti (_ret kısa)
            continue
        if mom is None:
            moments_yok += 1        # seri motor momenti üretemeyecek kadar kısa/degenerate
            continue
        sapmalar.append(abs(mom["mean"] / mom["std"] - float(sg)))
    sapmalar.sort()
    esdeger = bool(sapmalar) and sapmalar[-1] <= YUVARLAMA_DUZEYI
    esdegerlik = {
        "kiyaslanan_satir": len(sapmalar), "damga_none": damga_yok, "moments_none": moments_yok,
        "sapma_min": round(sapmalar[0], 6) if sapmalar else None,
        "sapma_medyan": round(sapmalar[len(sapmalar) // 2], 6) if sapmalar else None,
        "sapma_max": round(sapmalar[-1], 6) if sapmalar else None,
        "yuvarlama_duzeyi": YUVARLAMA_DUZEYI,
        "esdeger": esdeger,
        "beyan": ("ölçüt hüküm eşiği DEĞİL, kopya-veri özdeşlik sınırı: sapma yuvarlama "
                  "düzeyini aşıyorsa `seri`, kapının DSR girdisi `_ret`in başka bir yazımı değil "
                  "BAŞKA BİR SERİdir ve ondan DSR üretmek kapının görmeyeceği sayı üretir"),
    }

    if esdeger:
        # (Bu koşulda beklenmiyor — sonda aksini ölçtü; yol yine de dürüst yazılır.)
        en_iyi = max((r for r in r1 if r.get("sharpe_gozlem") is not None),
                     key=lambda r: float(r["sharpe_gozlem"]))
        seri_vals = [c[1] for c in (en_iyi.get("seri") or [])
                     if isinstance(c, (list, tuple)) and len(c) >= 2]
        trial_sh = [r.get("sharpe_gozlem") for r in r1 if r.get("sharpe_gozlem") is not None]
        try:
            eros = json.loads(EROSION_KOPYA.read_text())
            n_eros = sum(int(w.get("queries") or 0) for w in (eros.get("windows") or {}).values()
                         if w.get("pencere_id") == PENCERE)
        except Exception as e:
            n_eros = 0
        n_trials = n_eros + int(en_iyi.get("k_probes") or 1)
        dsr_res = V.deflated_sharpe(seri_vals, n_trials, trial_sh)
        dsr_deger = None if not dsr_res else dsr_res.get("dsr")
        sonuc["aday_kumesi_dsr"] = {
            "durum": "olculdu" if dsr_deger is not None else "olculemedi",
            "deger": dsr_deger, "motor_cikti": dsr_res,
            "aday_kumesi": (f"R1 penceresinin {len(r1)} resmî değerlendirme satırı; deneme-Sharpe "
                            f"kaynağı = {len(trial_sh)} sharpe_gozlem damgası; seçilen = en yüksek "
                            f"sharpe_gozlem satırı ({en_iyi.get('etiket')})"),
            "n_trials": n_trials, "esdegerlik_olcumu": esdegerlik,
        }
    else:
        # kill#2 — DSR YARISI İÇİN: kopya, kapının DSR girdi serisini taşımıyor (veri-şekli
        # uyuşmazlığı). Basitleştirilmiş ikame (seri'den DSR) YASAK → taze küme-DSR üretilmez.
        sonuc["aday_kumesi_dsr"] = {
            "durum": "olculemedi",
            "deger": None,
            "neden": ("kill#2 (veri-şekli uyuşmazlığı): kapının DSR girdisi `_ret` = "
                      "pnl_dollars/START_EQUITY, TÜM arama işlemleri (reflect.py:559); kopyadaki "
                      "`seri` = (kapanış günü, r_multiple) ve ts_close'suz işlemleri dışlıyor "
                      "(reflect.py:710-711). Motorun `_moments`'ıyla ölçüldü: seri-Sharpe ↔ damga "
                      f"sharpe_gozlem sapması min {esdegerlik['sapma_min']}, medyan "
                      f"{esdegerlik['sapma_medyan']}, max {esdegerlik['sapma_max']} — tamamı "
                      "yuvarlama düzeyinin üstünde; `seri` kapı-serisinin ölçek-eşdeğeri DEĞİL. "
                      "Bu seriden DSR hesaplamak kapının GÖRMEYECEĞİ bir taban üretirdi."),
            "arac_turu": ("GEREKİR: taze aday-kümesi DSR ancak kapı-serisi `_ret` kopyaya taşınırsa "
                          "(ör. defter şemasına pnl/START_EQUITY serisinin damgalanması ya da "
                          "Rol-1'in işlem-düzeyi pnl içeren yeni bir donmuş çekimi) hesaplanabilir"),
            "aday_kumesi": (f"hedeflenen küme R1 penceresinin {len(r1)} satırıydı "
                            f"({sonuc['evren']['tekil_etiket']} tekil etiket, "
                            f"{len(fp_sayim)} fingerprint) — taze hesap yapılamadı"),
            "esdegerlik_olcumu": esdegerlik,
        }

    # Taze küme-DSR'ın kapı-tablosu hücreleri (girdi None → motorun kendi 'ölçülemedi' hükümleri):
    sonuc["aday_kumesi_dsr"]["kapi_tablosu_taze_hesap"] = {
        "paper": _hucre(V.dsr_kapi(sonuc["aday_kumesi_dsr"]["deger"], live=False)),
        "gercek_para": _hucre(V.dsr_kapi(sonuc["aday_kumesi_dsr"]["deger"], live=True)),
        "beyan": ("girdi = bu ölçümün taze küme-DSR durumu (None=ölçülemedi); canlı kapının kendi "
                  "değerlendirme anında DSR'ı AYRICA hesapladığı unutulmamalı (damga bağlamı altta)"),
    }

    # ---- BAĞLAM (hüküm girdisi DEĞİL): motorun DAMGALADIĞI DSR'lar — kapının gerçekten -----
    # gördüğü değerler; kartın 'kapı canlıda ne görüyor' sorusuna kopyanın taşıyabildiği kayıt.
    damgali = [r.get("dsr") for r in r1 if r.get("dsr") is not None]
    damgali_sirali = sorted(float(x) for x in damgali)
    son = r1[-1]
    son_dsr = son.get("dsr")
    sonuc["baglam_motor_damgali_dsr"] = {
        "beyan": ("KART-DIŞI BAĞLAM — taze hesap değil: bu değerler motorun (deflated_sharpe) "
                  "resmî değerlendirme ANINDA hesaplayıp deftere damgaladığı DSR'lardır; kapının "
                  "o an gerçekten gördüğü sayılardır. Hüküm girdisi değildir, Rol-1'e taşınır."),
        "n_damga": len(damgali), "n_none": len(r1) - len(damgali),
        "min": damgali_sirali[0] if damgali_sirali else None,
        "medyan": damgali_sirali[len(damgali_sirali) // 2] if damgali_sirali else None,
        "max": damgali_sirali[-1] if damgali_sirali else None,
        "son_resmi_degerlendirme": {
            "ts": son.get("ts"), "etiket": son.get("etiket"), "dsr": son_dsr,
            "sharpe_gozlem": son.get("sharpe_gozlem"), "n_trials": son.get("n_trials"),
            "k_probes": son.get("k_probes"), "erosion_queries": son.get("erosion_queries"),
            "varyans_kaynagi": son.get("varyans_kaynagi"),
            "kapi_tablosu_damga": {
                "paper": _hucre(V.dsr_kapi(son_dsr, live=False)),
                "gercek_para": _hucre(V.dsr_kapi(son_dsr, live=True)),
            },
        },
    }

    # aşınma bağlamı: R1-damgalı pencerelerin ömür-boyu sorgu toplamı (n_trials'ın küme-ölçekli
    # iki-kanal yasasındaki birinci kanalı — taze DSR hesaplanamadığı için yalnız bağlam)
    try:
        eros = json.loads(EROSION_KOPYA.read_text())
        r1_win = {k: int(w.get("queries") or 0) for k, w in (eros.get("windows") or {}).items()
                  if w.get("pencere_id") == PENCERE}
        sonuc["baglam_asinma_r1"] = {
            "pencere_sorgulari": r1_win, "toplam_sorgu": sum(r1_win.values()),
            "beyan": ("oos_erosion kopyasından; R1 rotasyonu 4 fingerprint penceresi taşıyor, "
                      "defterde bunların 3'ü resmî değerlendirme satırı bırakmış")}
    except Exception as e:  # YASA 4: bağlam okunamadıysa sessiz düşmez, nedeniyle yazılır
        sonuc["baglam_asinma_r1"] = {"hata": f"{type(e).__name__}: {e}",
                                     "beyan": "aşınma bağlamı okunamadı — ölçümün kendisi etkilenmez"}

    # ---- kill özeti ----------------------------------------------------------------------------
    sonuc["kill_ozeti"] = {
        "kill1_pbo_min_aday": {"tetiklendi": bool((pbo.get("n_aday") or 0) < V.PBO_MIN_ADAY),
                               "n_aday": pbo.get("n_aday"), "esik": V.PBO_MIN_ADAY},
        "kill2_arac_turu": {"tetiklendi": not esdeger,
                            "kapsam": "YALNIZ aday-kümesi DSR yarısı — PBO girdisi (etiket+seri) "
                                      "ship-yolu girdisiyle birebir, uyuşmazlık yok",
                            "rapor": None if esdeger else "araç turu gerekir (ayrıntı aday_kumesi_dsr.arac_turu)"},
        "kill3_kopya_butunluk": {"tetiklendi": False, "satir": len(rows)},
    }
    sonuc["durum"] = "TAMAM"
    SONUC.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
