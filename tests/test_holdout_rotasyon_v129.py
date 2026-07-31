"""test_holdout_rotasyon_v129.py — HOLDOUT ROTASYONU "R1" (2026-07-30, operatör onaylı).

NE ÇİVİLENİYOR VE NEDEN. Rotasyon, kodun en kolay SESSİZCE bozulan yerine dokunuyor: sınav kâğıdının
kendisine. Bir pencere değişimi yanlış yapıldığında hiçbir şey patlamaz — kapı çalışmaya devam eder,
pano sayı gösterir, testler yeşil kalır. Yalnız ölçtüğü şey artık başka bir şeydir. Bu dosyanın altı
çivisi tam bu sessiz kaymanın altı ayrı yolunu kapatır:

  ① PENCERE SABİTLERİ    — R1 geometrisi ve IS tabanının KORUNDUĞU (taşınan bir IS başlangıcı, tüm
                           kanıt tarihini yeniden yazardı)
  ② PARMAK İZİ → TAZE SAYAÇ — geometri değişince aşınma sayacının R1'de SIFIRDAN başladığı; ve
                           "sıfır" ile "ölçülmedi"nin ayrı tutulduğu
  ③ PENCERE_ID DAMGASI   — kapı kaydı, doğrulama defteri ve ön-eleme satırının hangi sınava ait
                           olduğunu SATIRIN İÇİNDE taşıdığı (habersiz kıyas yasağının dayanağı)
  ④ ARŞİV İŞARETİ        — R0 kayıtlarının SİLİNMEDİĞİ, içeriklerinin DEĞİŞMEDİĞİ, ve arşiv
                           sayacının yürürlükteki sayaca KARIŞMADIĞI
  ⑤ N-DENGELİ FOLD       — kesimin R1 geometrisinde kendiliğinden yeniden oluştuğu ve DETERMİNİST
                           olduğu (aynı girdi → aynı sınırlar, çağrıdan çağrıya)
  ⑥ HOLDOUT KABULE GİRMEZ — yeni tarihlerle mevcut çivi; ve holdout sonunun DONMUŞ olduğu

SAPMA ÇİVİSİ DE BURADA (⑥b): Rol 1 tasarımı holdout sonunun "yuvarlanmasını" istedi. Uygulanmadı ve
sebebi ÖLÇÜLEBİLİR: `oos_erosion.fingerprint` girdilerinin arasında `holdout_end` var, yani bugünü
izleyen bir holdout sonu parmak izini HER GÜN değiştirir ve aşınma sayacı hiç birikemez — rotasyonun
var olma sebebi olan ölçüm imkânsız hâle gelirdi. Test bu gerekçeyi DAVRANIŞLA kanıtlar (aynı gün
içinde iki farklı "bugün" → iki farklı parmak izi), yani sapma bir tercih değil bir ZORUNLULUK olarak
kayıtlıdır. Yuvarlanma isteği `holdout_report_end()`te yaşar ve pencerelemeye girmez.
"""
from __future__ import annotations

import inspect
import json
import pathlib

import pytest

from meridian import (analytics, backtest, config, dataset, ledgers, oos_erosion, reflect,
                      validation)
from tests import wf_fixtures as wf

# R1 GEOMETRİSİ — bu dosyanın çivilediği sayılar. Testin İÇİNDE literal olarak durmaları şart:
# `dataset.*`ı `dataset.*` ile karşılaştıran bir test hiçbir şey çivilemez (her değişimde yeşil kalır).
R1 = {"is_start": "2022-01-01", "oos_start": "2024-01-01", "oos_end": "2026-04-30",
      "holdout_end": "2026-07-30", "embargo_days": 10,
      "folds": ["2024-01-01", "2024-10-01", "2025-07-01", "2026-04-30"]}
R0 = {"is_start": "2022-01-01", "oos_start": "2023-07-01", "oos_end": "2025-12-31",
      "holdout_end": "2026-07-10", "embargo_days": 10,
      "folds": ["2023-07-01", "2024-04-01", "2025-01-01", "2025-12-31"]}


def _fp(g: dict) -> str:
    return oos_erosion.fingerprint(g["is_start"], g["oos_start"], g["oos_end"], g["holdout_end"],
                                   g["folds"], g["embargo_days"])


# ================================================================================================
# ① PENCERE SABİTLERİ ÇİVİSİ
# ================================================================================================
def test_R1_pencere_sabitleri_civi():
    assert dataset.ROTATION_ID == "R1"
    assert dataset.ROTATION_DATE == "2026-07-30"
    assert dataset.ROTATION_PREV_ID == "R0"
    assert dataset.PENCERE_ID == dataset.ROTATION_ID
    assert dataset.OOS_START == R1["oos_start"]
    assert dataset.OOS_END == R1["oos_end"]
    assert dataset.HOLDOUT_END == R1["holdout_end"]
    assert list(dataset.OOS_FOLDS) == R1["folds"]
    assert dataset.EMBARGO_DAYS == R1["embargo_days"]


def test_IS_tabani_ROTASYONDA_TASINMADI():
    """IS başlangıcı R1'de AYNEN korundu ve bu bir tercih değil bir SÜREKLİLİK koşulu: IS tabanı
    taşınsaydı ısınma yılı (2021 → 252-günlük trend şablonu) ile hizası bozulur ve R0/R1 arasındaki
    'motor aynı mı?' sorusu CEVAPSIZ kalırdı — iki pencere iki farklı in-sample'dan öğrenmiş olurdu."""
    assert dataset.IS_START == R0["is_start"] == R1["is_start"] == "2022-01-01"
    assert dataset.FETCH_START < dataset.IS_START, "ısınma yılı IS'ten önce gelmeli"


def test_R1_siralama_ve_fold_sinirlari_tutarli():
    assert dataset.IS_START < dataset.OOS_START < dataset.OOS_END <= dataset.HOLDOUT_END
    f = list(dataset.OOS_FOLDS)
    assert f == sorted(f) and len(set(f)) == len(f), "fold sınırları artan ve tekil olmalı"
    assert f[0] == dataset.OOS_START and f[-1] == dataset.OOS_END, \
        "takvim fold'ları OOS penceresini TAM kaplamalı (uçları pencereyle aynı)"
    assert len(f) - 1 == 3, "R1 de R0 gibi 3 sıralı fold üretir (kanıt hacmi korunur)"


def test_R1_en_cok_kazilmis_dilim_Search_ten_CIKTI():
    """R1'in birinci kazancı: R0'ın 434 sorgusunun tamamının içinden geçtiği erken dilim
    [2023-07-01, 2024-01-01) artık kapı penceresinde DEĞİL."""
    assert dataset.OOS_START > R0["oos_start"], "OOS başlangıcı ileri taşınmadı"
    assert dataset.OOS_START == "2024-01-01"


def test_R1_eski_holdoutun_4_ayi_TAZE_OOS_oldu():
    """İkinci kazanç: R0'ın holdout'unun [2026-01-01, 2026-04-30] dilimi artık kapı penceresinde."""
    assert R0["oos_end"] < "2026-01-01" < dataset.OOS_END
    assert dataset.OOS_END > R0["oos_end"], "OOS sonu ileri taşınmadı — taze veri girmedi"


def test_YARI_TEMIZ_durustluk_notu_KODDA_durur():
    """Eski holdout'un YARI-TEMİZ sayılması bir yorum değil bir BEYANDIR ve kodda durmak zorundadır:
    rapordan silinebilir, docstring'den silinemez. Aşınma gerekçesi (limitin katı) da aynı şekilde."""
    src = pathlib.Path("meridian/dataset.py").read_text()
    assert "YARI-TEMİZ" in src, "eski holdout'un yarı-temiz sayıldığı beyanı kodda yok"
    assert "İNSANA RAPORLANDI" in src, "yarı-temizliğin SEBEBİ (insana raporlanmışlık) yazılı değil"
    assert "434" in src and "21,7" in src, "aşınma gerekçesi (ölçülmüş sorgu/limit) kodda yok"
    assert dataset.ARSIV_GEOMETRILER["R0"]["not"].find("YARI-TEMİZ") >= 0


def test_pencere_sabitleri_ENV_den_ayarlanamaz():
    """Mevcut koruma (test_gaps_batch_v51) R1 satırlarında da geçerli olmalı: pencere alışverişi
    (env'den geometri seçmek) kapıyı ayarlanabilir yapardı."""
    src = pathlib.Path("meridian/dataset.py").read_text()
    for token in ("IS_START", "OOS_START", "OOS_END", "HOLDOUT_END"):
        line = next(l for l in src.splitlines() if l.startswith(f"{token} ="))
        assert "environ" not in line and "getenv" not in line, f"{token} env'den ayarlanabilir"


# ================================================================================================
# ② PARMAK İZİ DEĞİŞİMİ → TAZE SAYAÇ
# ================================================================================================
def test_R1_parmak_izi_R0_dan_FARKLI():
    assert _fp(R1) != _fp(R0), "geometri değişti ama parmak izi aynı — sayaç eski sınavı sayardı"
    assert _fp(R1) == _fp({**R1}), "parmak izi kararsız"


def test_yururlukteki_geometri_R1_parmak_izini_uretir():
    """Kapının HESAPLADIĞI parmak izi ile bu dosyanın çivilediği R1 aynı olmalı — yoksa çivi
    kodun koştuğu şeyi değil kendi kopyasını test ediyor olurdu."""
    w = reflect._default_windows()
    assert oos_erosion.fingerprint(w[0], w[1], w[2], w[3], w[4], w[5]) == _fp(R1)


def test_taze_sayac_R1_de_SIFIRDAN_baslar(sandbox_state):
    """R0'ın 434 sorgusu defterde DURUYOR ama R1'in sayacı 0'dan başlar ve ek marj YOKTUR."""
    doc = {"windows": {_fp(R0): {"queries": 434, "first_seen": "2026-07-28T22:46:17+00:00",
                                 "last_seen": "2026-07-30T11:03:55+00:00", "pencere": dict(R0)}},
           "sayac_baslangici": "2026-07-28T21:34:03+00:00", "beyan": "x"}
    (config.STATE / oos_erosion.EROSION_FILE).write_text(json.dumps(doc))
    st = oos_erosion.status(_fp(R1))
    assert st["queries"] == 0, "R1 sayacı R0'dan miras aldı"
    assert st["extra_margin"] == 0.0, "R1'de ek marj var — aşınma cezası devredilmiş"
    assert st["pencere_id"] == "R1"
    # ...ve R0'ın kendi sayacı hâlâ okunabilir (silinmedi)
    assert oos_erosion.status(_fp(R0))["queries"] == 434
    assert oos_erosion.status(_fp(R0))["extra_margin"] == oos_erosion.EROSION_EXTRA_MARGIN


def test_SIFIR_ile_OLCULMEDI_ayri_hallerdir(sandbox_state):
    """Rotasyondan hemen sonra 'aşınma yok' DEMEK YASAK: doğru cümle 'R1'de henüz ölçülmedi'.
    `report()` yürürlükteki pencerede kayıt yoksa toplamı None döner (0 DEĞİL) ve 2D
    değerlendiricisi de öneriyi 'ölçmüyor' diye gerekçelendirir."""
    doc = {"windows": {_fp(R0): {"queries": 434, "pencere": dict(R0)}}, "sayac_baslangici": "x"}
    (config.STATE / oos_erosion.EROSION_FILE).write_text(json.dumps(doc))
    rep = oos_erosion.report()
    assert rep["toplam_sorgu"] is None, "ölçülmemiş pencere SIFIR ölçülmüş gibi sunuluyor"
    assert rep["en_cok"] is None and rep["n_pencere"] == 0
    adv = analytics.holdout_rotation_advice()
    assert adv["oran"] is None and adv["oneri"] is None
    assert "ÖLÇMÜYOR" in adv["hukum"].upper() or "ölçülmedi" in adv["hukum"]


# ================================================================================================
# ③ PENCERE_ID DAMGASI — kapı kaydı / doğrulama defteri / ön-eleme
# ================================================================================================
def _iki_taraf():
    """Kapıya verilecek incumbent+aday: ÜRETİCİYLE aynı şekil (wf_fixtures), dilimli → gerçek yasa."""
    inc = wf.wf_from_trades(wf.trades(90, 11, wf.OOS_START, wf.OOS_END, 0.10))
    cand = wf.wf_from_trades(wf.trades(90, 12, wf.OOS_START, wf.OOS_END, 0.12))
    return inc, cand


def test_kapi_kaydi_pencere_id_damgasi_tasir(sandbox_state):
    inc, cand = _iki_taraf()
    _, gate, _ = reflect._gate_eval(inc, cand, k_probes=1)
    assert gate["pencere_id"] == "R1"
    assert gate["pencere_rotasyon_tarihi"] == "2026-07-30"
    assert "KARŞILAŞTIRILAMAZ" in gate["pencere_kiyas_uyarisi"]
    assert gate["erosion"]["pencere_id"] == "R1"


def test_dogrulama_defteri_satiri_pencere_id_damgasi_tasir(sandbox_state):
    """Defter satırı PBO/DSR'nin ham maddesi. Damgasız satır, iki sınavın tek popülasyonda
    havuzlanmasına açık kapı bırakır."""
    inc, cand = _iki_taraf()
    _, gate, _ = reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    rows = validation.ledger()
    assert rows, "resmî değerlendirme doğrulama defterine satır yazmadı"
    assert rows[-1]["pencere_id"] == "R1"
    # PARMAK İZİ, TÜRETİLMİŞ FOLD SINIRLARINI DA KAPSAR (tasarım: n-dengeli kesim sınırları
    # incumbent'tan türüyor, yani geometrinin parçası). O yüzden çivi `dataset.OOS_FOLDS`e DEĞİL
    # kapının kendi kullandığı sınırlara bağlanır — ama PENCERE TARİHLERİ R1 olmak zorunda.
    folds = gate["fold_bounds"] or list(dataset.OOS_FOLDS)
    assert rows[-1]["fingerprint"] == _fp({**R1, "folds": folds}), \
        "satırın parmak izi yürürlükteki pencere tarihlerinden türemiyor"
    assert rows[-1]["fingerprint"] != _fp({**R0, "folds": folds}), \
        "AYNI fold sınırlarıyla R0 ve R1 aynı parmak izini veriyor — pencere tarihleri hash'e girmiyor"


def test_oneleme_satiri_ve_raporu_pencere_id_damgasi_tasir():
    """Ön-eleme satırları tur raporlarına ELLE taşınıyor; damga satırın kendisinde durmak zorunda
    (rapor envelope'u kopyalanınca geride kalır)."""
    src = pathlib.Path("meridian/prescreen.py").read_text()
    assert '"pencere_id": gate.get("pencere_id")' in src, "aday satırında pencere damgası yok"
    assert '"pencere_id": dataset.ROTATION_ID' in src, "rapor `pencereler` bloğunda damga yok"
    assert "kiyas_uyarisi" in src, "ön-eleme raporunda habersiz-kıyas uyarısı yok"


def test_asinma_defteri_kaydi_pencere_id_damgasi_tasir(sandbox_state):
    st = oos_erosion.record(_fp(R1), {"oos_start": dataset.OOS_START, "oos_end": dataset.OOS_END})
    assert st["pencere_id"] == "R1"
    doc = json.loads((config.STATE / oos_erosion.EROSION_FILE).read_text())
    assert doc["windows"][_fp(R1)]["pencere_id"] == "R1"


def test_ledgers_sozlesmesi_habersiz_kiyasi_YASAKLAR():
    note = ledgers.CONTRACTS["validation_ledger.jsonl"].note
    assert "pencere_id" in note, "sözleşme pencere damgasını beyan etmiyor"
    assert "KARŞILAŞTIRILAMAZ" in note
    assert "arsiv_R0" in note, "arşiv işareti sözleşmede yazılı değil"
    # ...ama ZORUNLU alan OLMAMALI: R1 öncesi satırlar retro damgalanmaz
    assert "pencere_id" not in ledgers.CONTRACTS["validation_ledger.jsonl"].required, \
        "pencere_id zorunlu yapıldı → tüm R1-öncesi satırlar ihlalli ilan edilir (retro damga yasağı)"


def test_pano_dogrulama_satiri_pencereyi_gosterir():
    """Pano satırı, PBO'nun paydasının HANGİ pencereden geldiğini yazmak zorunda: R0'da 12 kayıtla
    ölçülmüş bir PBO ile R1'de 2 kayıtla ölçülmüş bir PBO panoda AYNI görünürdü."""
    js = pathlib.Path("meridian/web/app.js").read_text()
    assert "v.pencere_id" in js, "pano doğrulama satırında pencere kimliği yok"
    assert "n_kayit_guncel_pencere" in js, "PBO paydası pencere başına gösterilmiyor"
    assert "v.kiyas_uyarisi" in js and "er.kiyas_uyarisi" in js
    # 2D kartı: uygulanmış rotasyon + donmuş holdout + arşiv AYRI AYRI görünür
    assert "uygulanan_rotasyon" in js, "pano uygulanmış rotasyonu göstermiyor"
    assert "dondurulmus_holdout" in js, "pano donmuş holdout dilimini göstermiyor"
    assert "henüz ÖLÇÜLMEDİ" in js, "pano 'ölçülmedi' ile 'aşınma yok'u ayırt etmiyor"
    assert "er.arsiv" in js, "pano aşınma arşivini göstermiyor"


# ================================================================================================
# ④ ARŞİV İŞARETİ — silinmez, içeriği değişmez, karışmaz
# ================================================================================================
def test_arsiv_isareti_ICERIGI_DEGISTIRMEZ():
    """RETRO DAMGA YASAĞI: arşiv bir ETİKETtir, ölçüm değil. Sayılar, tarihler ve geometri
    aynen kalır — yalnız `arsiv*` alanları eklenir."""
    w = {"queries": 434, "first_seen": "A", "last_seen": "B", "pencere": dict(R0)}
    doc = {"windows": {_fp(R0): w}}
    assert oos_erosion.arsivle(doc) == 1
    assert w["queries"] == 434 and w["first_seen"] == "A" and w["last_seen"] == "B"
    assert w["pencere"] == R0, "arşivleme geometri meta'sını değiştirdi"
    assert w["arsiv"] == "arsiv_R0" and w["arsiv_tarihi"] == "2026-07-30"


def test_arsivleme_IDEMPOTENT():
    doc = {"windows": {_fp(R0): {"queries": 5, "pencere": dict(R0)}}}
    assert oos_erosion.arsivle(doc) == 1
    assert oos_erosion.arsivle(doc) == 0, "ikinci geçiş yeniden işaretledi"


def test_yururlukteki_pencere_ARSIVLENMEZ():
    doc = {"windows": {_fp(R1): {"queries": 3, "pencere_id": "R1", "pencere": dict(R1)}}}
    assert oos_erosion.arsivle(doc) == 0
    assert "arsiv" not in doc["windows"][_fp(R1)]


def test_taninmayan_geometri_R0_SANILMAZ():
    """UYDURMA YASAĞI: hangi pencere olduğunu bilmediğimiz bir satıra 'R0' demek, aşınma
    modülünün (1) numaralı beyanının ihlali olurdu."""
    doc = {"windows": {"deadbeef": {"queries": 9},                            # meta YOK
                       "cafe": {"queries": 2, "pencere": {"oos_start": "2019-01-01"}}}}
    assert oos_erosion.arsivle(doc) == 2
    assert doc["windows"]["deadbeef"]["arsiv"] == "arsiv_bilinmeyen"
    assert doc["windows"]["cafe"]["arsiv"] == "arsiv_bilinmeyen"


def test_arsiv_sayaci_YURURLUKTEKI_sayaca_KARISMAZ(sandbox_state):
    """EN İNCE TUZAK. Eski `report()` defterin TAMAMINDA maksimum arıyordu; rotasyondan sonra bu
    arşivlenmiş R0'ı (434 sorgu) 'en çok sorulan pencere' diye gösterir, ek marjı YÜRÜRLÜKTE sanır
    ve rotasyonun ÇÖZDÜĞÜ sorunu hâlâ açık gibi sunardı — panonun okuduğu sayı, kapının uyguladığı
    marjın tam tersini söylerdi."""
    doc = {"windows": {_fp(R0): {"queries": 434, "pencere": dict(R0), "arsiv": "arsiv_R0"},
                       _fp(R1): {"queries": 3, "pencere_id": "R1", "pencere": dict(R1)}},
           "sayac_baslangici": "x"}
    (config.STATE / oos_erosion.EROSION_FILE).write_text(json.dumps(doc))
    rep = oos_erosion.report()
    assert rep["en_cok"]["queries"] == 3, "arşiv satırı yürürlükteki pencere gibi okundu"
    assert rep["en_cok"]["fingerprint"] == _fp(R1)
    assert rep["toplam_sorgu"] == 3, "iki sınavın sorguları toplandı"
    assert rep["n_pencere"] == 1
    assert rep["extra_margin_yururlukte"] == 0.0, "arşivlenmiş aşınmadan ek marj türetildi"
    # ...ama arşiv KAYBOLMADI, kendi adıyla duruyor
    assert rep["arsiv"]["toplam_sorgu"] == 434 and rep["arsiv"]["n_pencere"] == 1
    # ...ve kapının GERÇEKTEN uyguladığı marj ile pano AYNI şeyi söylüyor
    assert oos_erosion.status(_fp(R1))["extra_margin"] == rep["extra_margin_yururlukte"]


def test_PBO_paydasi_YALNIZ_yururlukteki_pencereden(sandbox_state, monkeypatch):
    """Sözleşme uyarısı, yalnız onu UYGULAYAN bir tüketiciyle birlikte gerçektir. `_matris`
    ızgaraları BİRLEŞTİRİR: kesişmeyen iki dönemi havuzlamak matrisi sıfırlarla doldurur ve PBO
    gürültüyü 'aşırı-uydurma yok' diye okur."""
    rows = ([{"ts": f"2026-01-{i:02d}", "pencere_id": "R1", "etiket": f"a{i}",
              "seri": [["2026-02-01", 0.5]], "sharpe_gozlem": 1.0, "n_trials": 1, "passes": False}
             for i in range(1, 4)]
            + [{"ts": f"2025-01-{i:02d}", "etiket": f"b{i}",          # DAMGASIZ = R1 öncesi
                "seri": [["2025-02-01", 0.4]], "sharpe_gozlem": 0.9, "n_trials": 1, "passes": False}
               for i in range(1, 10)])
    (config.STATE / validation.LEDGER_FILE).write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n")
    monkeypatch.setattr(analytics, "_trades", lambda *a, **k: [])
    trio = analytics.validation_trio()
    assert trio["pencere_id"] == "R1"
    assert trio["defter"]["n_kayit_guncel_pencere"] == 3
    assert trio["defter"]["n_kayit_onceki_pencereler"] == 9
    # 3 aday PBO_MIN_ADAY(8) altında → DÜRÜSTÇE ölçülmez. Havuzlanmış olsaydı 12 aday görünür ve
    # PBO iki farklı ızgaradan bir sayı UYDURURDU.
    assert trio["pbo"]["pbo"] is None, "PBO iki pencereyi havuzladı"
    assert "pencere" in trio["defter"]["beyan"]


# ================================================================================================
# ⑤ N-DENGELİ FOLD KESİMİ — R1 geometrisinde kendiliğinden oluşur, determinist
# ================================================================================================
def _r1_search_end() -> str:
    from meridian.oos_pipeline import split_date
    return split_date(dataset.OOS_START, dataset.OOS_END)


def test_R1_search_dilimi_en_az_2_takvim_foldu_tasir():
    """Kapının fold çoğunluğu `fold_total >= 2` ister. R1'in takvim fold'ları Search dilimine
    daraltıldığında bu taban tutmalı — tutmazsa çoğunluk İDDİA EDİLEMEZ ve her aday reddedilirdi."""
    se = _r1_search_end()
    search_folds = [b for b in dataset.OOS_FOLDS if b < se] + [se]
    assert len(search_folds) - 1 >= 2, f"R1 Search dilimi {len(search_folds)-1} fold üretiyor"


def test_n_dengeli_kesim_R1_geometrisinde_DETERMINIST():
    """Aynı girdi → aynı sınırlar, çağrıdan çağrıya. Determinizm burada bir konfor değil KAPI
    ŞARTIDIR: sınırlar incumbent'tan türetilip İKİ TARAFA DA uygulanıyor, yani kararsız bir kesim
    aday ile incumbent'ı FARKLI pencerelerde yargılardı."""
    se = _r1_search_end()
    trades = wf.trades(120, 77, dataset.OOS_START, se, 0.10)
    a = backtest.balanced_fold_bounds(trades, se, dataset.EMBARGO_DAYS)
    b = backtest.balanced_fold_bounds(list(trades), se, dataset.EMBARGO_DAYS)
    assert a and a == b, "n-dengeli kesim kararsız"
    assert a == sorted(a), "sınırlar artan değil"
    assert a[-1] == se, "üst sınır Search dilimini kapatmıyor"
    assert len(a) - 1 >= 2, "R1 geometrisinde 2'den az dengeli fold — çoğunluk iddia edilemez"
    # sınırlar YENİ pencerenin içinde: R0 tarihlerine kaçmış bir sınır sessiz bir kayma olurdu
    assert all(dataset.OOS_START <= x <= dataset.OOS_END for x in a[1:]), \
        f"fold sınırı R1 penceresinin dışında: {a}"


def test_n_dengeli_kesim_R1_de_takvimden_FARKLI_kesim_uretir():
    """Kesim gerçekten incumbent'ın DAĞILIMINDAN türüyor mu, yoksa takvimi mi tekrar ediyor?
    (Tekrar ediyorsa 'n-dengeli' etiketi bir iddia olur, ölçüm olmaz.)"""
    se = _r1_search_end()
    # işlemleri pencerenin ilk yarısına TOPLA: dengeli kesim sınırları oraya çekmek ZORUNDA
    yigin = wf.trades(120, 91, dataset.OOS_START, "2024-12-01", 0.10)
    a = backtest.balanced_fold_bounds(yigin, se, dataset.EMBARGO_DAYS)
    assert a, "yığılmış dağılımda kesim taban tutmadı"
    assert a != ([b for b in dataset.OOS_FOLDS if b < se] + [se]), \
        "n-dengeli kesim takvim sınırlarını tekrarlıyor — dengeleme fiilen yok"


# ================================================================================================
# ⑥ HOLDOUT: KABULE GİRMEZ + DONMUŞ
# ================================================================================================
def test_holdout_KABULE_GIRMEZ_R1_tarihleriyle():
    """Mevcut çivi, YENİ tarihlerle. Holdout dilimindeki işlemler kapı hükmünü değiştirmemeli;
    `holdout_score` yalnız RAPOR alanıdır."""
    goal = config.goal()
    base = wf.trades(90, 21, wf.OOS_START, wf.OOS_END, 0.10)
    inc = wf.wf_from_trades(base, goal)
    cand_t = wf.trades(90, 22, wf.OOS_START, wf.OOS_END, 0.12)
    cand_a = wf.wf_from_trades(cand_t, goal)
    # AYNI aday + holdout diliminde MUAZZAM kazançlar (R1 holdout'u: OOS_END → HOLDOUT_END)
    holdout = wf.trades(40, 23, dataset.OOS_END, dataset.HOLDOUT_END, 5.0)
    cand_b = wf.wf_from_trades(cand_t + holdout, goal)
    p_a, g_a, _ = reflect._gate_eval(inc, cand_a, k_probes=1)
    p_b, g_b, _ = reflect._gate_eval(inc, cand_b, k_probes=1)
    assert p_a == p_b, "holdout işlemleri kapı hükmünü DEĞİŞTİRDİ — kabule giriyor"
    assert g_a["candidate_oos"] == g_b["candidate_oos"], "holdout OOS skoruna sızdı"
    assert g_a["candidate_para"] == g_b["candidate_para"], "holdout PARA karar skoruna sızdı"
    assert g_a["fold_wins"] == g_b["fold_wins"] and g_a["tail_ok"] == g_b["tail_ok"]


def test_holdout_sonu_DONMUS_bugunu_izlemez():
    """SAPMA ÇİVİSİ. Rol 1 tasarımı 'yuvarlanır' dedi; uygulanmadı çünkü uygulanamaz."""
    import datetime as dt
    assert dataset.HOLDOUT_END == "2026-07-30"
    src = pathlib.Path("meridian/dataset.py").read_text()
    line = next(l for l in src.splitlines() if l.startswith("HOLDOUT_END ="))
    assert "fetch_end" not in line and "today" not in line, \
        "HOLDOUT_END bugünü izliyor → parmak izi her gün değişir, aşınma sayacı hiç birikemez"
    # ...ve yuvarlanma İSTEĞİ kaybolmadı: rapor yolu bugünü döner, pencerelemeye GİRMEZ
    assert dataset.holdout_report_end() == dt.date.today().isoformat()
    assert "holdout_report_end" not in inspect.getsource(reflect._default_windows)
    # YASA 6: yuvarlanan sonun GERÇEK bir insan tüketicisi var (dekor değil)
    assert "holdout_report_end" in inspect.getsource(analytics.holdout_rotation_advice)


def test_YUVARLANAN_holdout_SAYACI_HER_GUN_SIFIRLARDI():
    """Sapmanın gerekçesi DAVRANIŞLA kanıtlanır, iddiayla değil: holdout sonu iki farklı 'bugün'
    olduğunda parmak izi de iki farklı değer alır → aynı sınav iki ayrı sayaca yazılır."""
    d1 = _fp({**R1, "holdout_end": "2026-07-30"})
    d2 = _fp({**R1, "holdout_end": "2026-07-31"})
    assert d1 != d2, ("holdout_end parmak izini etkilemiyor — o hâlde yuvarlanabilirdi; "
                      "sapma gerekçesi geçersiz, gözden geçir")
    assert "holdout" in inspect.getsource(oos_erosion.fingerprint)


def test_kapi_pencerelerini_dataset_ten_okur_KOPYA_TUTMAZ():
    """Rotasyonun TEK yerden yürümesinin çivisi: `_default_windows` altı değeri de `dataset.*`tan
    okur. Bir kopya tutulsaydı rotasyon yarım uygulanır ve iki farklı 'yürürlükteki pencere' olurdu."""
    w = reflect._default_windows()
    assert w == (dataset.IS_START, dataset.OOS_START, dataset.OOS_END, dataset.HOLDOUT_END,
                 dataset.OOS_FOLDS, dataset.EMBARGO_DAYS)
    assert w[1] == R1["oos_start"] and w[2] == R1["oos_end"] and w[3] == R1["holdout_end"]


# ================================================================================================
# 2D DEĞERLENDİRİCİSİ — "R1 UYGULANDI" durumunu bilir
# ================================================================================================
def test_2D_degerlendirici_R1_in_UYGULANDIGINI_bilir(sandbox_state):
    doc = {"windows": {_fp(R0): {"queries": 434, "pencere": dict(R0), "arsiv": "arsiv_R0"}},
           "sayac_baslangici": "x"}
    (config.STATE / oos_erosion.EROSION_FILE).write_text(json.dumps(doc))
    adv = analytics.holdout_rotation_advice()
    u = adv["uygulanan_rotasyon"]
    assert u["pencere_id"] == "R1" and u["tarih"] == "2026-07-30" and u["onceki"] == "R0"
    assert "UYGULANDI" in u["durum"]
    assert u["yeni_geometri"]["oos_start"] == R1["oos_start"]
    assert u["yeni_geometri"]["oos_end"] == R1["oos_end"]
    assert adv["uygular_mi"] is False, "değerlendirici UYGULAR hâle geldi — operatör kararı elinden alındı"
    assert "R1" in adv["hukum"]
    # ARŞİVLENMİŞ 434, öneriyi BİR DAHA tetiklemez (yoksa her tur 'döndür' der: ölü sayaç hiç düşmez)
    assert adv["oneri"] is None, "arşivlenmiş aşınma yeni bir rotasyon önerisi doğurdu"


def test_2D_sonraki_rotasyon_icin_sayac_YENI_pencerede_birikir(sandbox_state):
    """④: bir SONRAKİ rotasyon önerisi için sayaç R1'de birikmeye devam eder."""
    fp1 = _fp(R1)
    for _ in range(oos_erosion.EROSION_QUERY_LIMIT + 1):
        oos_erosion.record(fp1, {"oos_start": dataset.OOS_START, "oos_end": dataset.OOS_END,
                                 "holdout_end": dataset.HOLDOUT_END})
    rep = oos_erosion.report()
    assert rep["en_cok"]["queries"] == oos_erosion.EROSION_QUERY_LIMIT + 1
    assert rep["extra_margin_yururlukte"] == oos_erosion.EROSION_EXTRA_MARGIN
    adv = analytics.holdout_rotation_advice()
    assert adv["oneri"] is not None, "R1 aşınsa bile sonraki rotasyon önerilmiyor"
    assert "R1" in adv["oneri"]["eylem"]
    assert adv["oneri"]["yururlukteki_rotasyon"]["pencere_id"] == "R1"


@pytest.mark.parametrize("fn", ["report", "status", "record"])
def test_asinma_yuzeyi_pencere_id_beyan_eder(fn):
    """Üç erişimcinin HEPSİ pencere kimliğini döner: biri dönmezse o yol habersiz kıyasa açık kalır."""
    assert "pencere_id" in inspect.getsource(getattr(oos_erosion, fn))
