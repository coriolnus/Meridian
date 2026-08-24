"""test_topviews_v282.py — `/api/topviews`: TEK PAYDA, DOKUZ FACET, TAM METRİK.

ÖLÇÜLEN BOŞLUK (pano ajanının raporu, 2026-08-24): panonun "Top Views" yüzeyi üç facet ailesini
çiziyor ama YARIM ölçüyor. `n` her facette var; `toplam R` ve `kazanma` yalnız bazılarında;
**`PF` hiçbir tam-defter facetinde ölçülemiyor** — çünkü besleyen uçlar (`/api/plots`,
`/api/performance.per_regime`) hücrede yalnız ORTALAMA R veriyor ve ortalama R'den brüt kâr /
brüt zarar ayrımı GERİ ÇIKARILAMAZ. Üstüne yüzey üç ayrı paydayı (tam defter · son 40 işlem ·
plots hücresi) tek kartta yan yana basmak zorunda kalıyordu.

BU DOSYANIN ÇİVİLEDİĞİ SÖZLEŞME:

  [1] `gross_loss == 0` ⇒ `pf is None` + `pf_yok_nedeni` DOLU. PF SONSUZ DEĞİLDİR: `float('inf')`
      hem matematiksel bir uydurma (payda ölçülmedi, sıfır değil) hem de JSON'da BOZUK bir
      değerdir (`json.dumps` `Infinity` üretir, hiçbir katı ayrıştırıcı okumaz). Payloadın
      TAMAMINDA inf/nan taraması yapılır — tek bir hücre değil, yüzey.
  [2] `n == 0` satır BASILMAZ (v197 koşulsuz emisyon tavanı).
  [3] Etiketsiz satır sayıma GİRMEZ ama `etiketsiz_n` ile RAPORLANIR — sessizce düşürme yok.
  [4] `sum_r`, [5] `pf`, [6] `kazanma` fikstür üstünde BİREBİR (yuvarlamaya kadar).
  [7] Dokuz facetin HEPSİ yükte; ölçülemeyen `satirlar: None` + neden.
  [8] `kapi_reddi` ölçülemiyorsa `None` + neden — BOŞ LİSTE DÖNMÜYOR. Boş liste "reddedilen plan
      yok" der; kapı ölçütü hiç yazılmamış bir defterde bu YALANDIR.
  [9] Her facet `facet_kaynaklari`nda KENDİ kaynağını, penceresini ve paydasını bildirir.
  [10] `_auth` uygulanıyor — tokensiz istek 401.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` (tmp_path + `config.STATE`) içinde koşar.
"""
from __future__ import annotations

import json
import math

import pytest
from fastapi.testclient import TestClient

from meridian import api, store, topviews

# =================================================================================================
# FİKSTÜR — elle hesaplanabilir olacak kadar küçük, dokuz faceti de uyandıracak kadar zengin.
# =================================================================================================
# İŞLEMLER (5 satır). R değerleri TAM SAYIYA yakın seçildi ki beklenen toplam/PF/kazanma
# kayan-nokta gürültüsü olmadan elle yazılabilsin.
#   T5 setup TAŞIMIYOR → `kurulum` facetinde etiketsiz (çivi [3]).
#   T1+T2 `target` ile kapandı ve İKİSİ DE kârlı → `cikis_nedeni: target` hücresinde brüt zarar
#   SIFIR, yani çivi [1]'in gerçek vakası (canlı defterde de aynen böyle: `target` n=4, gl=0).
ISLEMLER = [
    {"id": "T00001", "ts_open": "2026-01-05", "ts_close": "2026-01-12", "ticker": "AAA",
     "r_multiple": 2.0, "exit_reason": "target", "regime": "trend_up", "setup": "breakout_vcp",
     "bars_held": 5, "plan_id": "P1"},
    {"id": "T00002", "ts_open": "2026-01-06", "ts_close": "2026-01-09", "ticker": "BBB",
     "r_multiple": 1.0, "exit_reason": "target", "regime": "trend_up", "setup": "breakout_vcp",
     "bars_held": 3, "plan_id": "P2"},
    {"id": "T00003", "ts_open": "2026-01-07", "ts_close": "2026-01-09", "ticker": "CCC",
     "r_multiple": -1.0, "exit_reason": "stop", "regime": "chop", "setup": "breakout_vcp",
     "bars_held": 2, "plan_id": "P3"},
    {"id": "T00004", "ts_open": "2026-01-08", "ts_close": "2026-01-09", "ticker": "DDD",
     "r_multiple": -0.5, "exit_reason": "stop", "regime": "chop", "setup": "pullback",
     "bars_held": 1, "plan_id": "P4"},
    # ETİKETSİZ: `setup` YOK. `regime` var — etiketsizlik FACET BAŞINADIR, satır başına değil.
    {"id": "T00005", "ts_open": "2026-01-08", "ts_close": "2026-01-09", "ticker": "EEE",
     "r_multiple": -1.0, "exit_reason": "stop", "regime": "chop",
     "bars_held": 1, "plan_id": "P5"},
]

# PLANLAR (6 satır — P6 hiç işleme dönüşmedi). `sector` YALNIZ burada yaşar; işlem defterinde
# böyle bir alan YOKTUR ve `sektor` faceti bu birleştirmeden doğar.
PLANLAR = [
    {"id": "P1", "date": "2026-01-04", "ticker": "AAA", "sector": "tech", "gate_verdict": "GO",
     "gate_checks": [{"check": "score_band", "passed": True}]},
    {"id": "P2", "date": "2026-01-05", "ticker": "BBB", "sector": "tech", "gate_verdict": "REVIEW",
     "gate_checks": [{"check": "score_band", "passed": False}]},
    {"id": "P3", "date": "2026-01-06", "ticker": "CCC", "sector": "health", "gate_verdict": "REVIEW",
     "gate_checks": [{"check": "score_band", "passed": False},
                     {"check": "leading_sector", "passed": False}]},
    {"id": "P4", "date": "2026-01-07", "ticker": "DDD", "sector": "health", "gate_verdict": "NO_GO",
     "gate_checks": [{"check": "heat_hard", "passed": False}]},
    # SEKTÖRSÜZ PLAN → `sektor` facetinde T5 etiketsiz sayılır.
    {"id": "P5", "date": "2026-01-07", "ticker": "EEE", "sector": "", "gate_verdict": "GO",
     "gate_checks": [{"check": "score_band", "passed": True}]},
    {"id": "P6", "date": "2026-01-08", "ticker": "FFF", "sector": "tech", "gate_verdict": "NO_GO",
     "gate_checks": [{"check": "heat_hard", "passed": False}]},
]


@pytest.fixture
def defterli(sandbox_state):
    store.write_jsonl("trades.jsonl", ISLEMLER)
    store.write_jsonl("trade_plans.jsonl", PLANLAR)
    return sandbox_state


def _facet(yuk: dict, ad: str) -> dict:
    for aile in yuk["aileler"].values():
        if ad in aile:
            return aile[ad]
    raise AssertionError(f"facet yükte yok: {ad}")


def _satir(yuk: dict, facet: str, deger: str) -> dict:
    sat = _facet(yuk, facet)["satirlar"]
    assert sat is not None, f"{facet} ölçülemedi sayıldı: {_facet(yuk, facet)['olculemedi_neden']}"
    for s in sat:
        if s["deger"] == deger:
            return s
    raise AssertionError(f"{facet} facetinde '{deger}' satırı yok: {[s['deger'] for s in sat]}")


def _tum_satirlar(yuk: dict):
    for aile in yuk["aileler"].values():
        for ad, f in aile.items():
            for s in (f["satirlar"] or []):
                yield ad, s


# =================================================================================================
# [1] PF SONSUZ OLAMAZ — brüt zarar sıfırsa ÖLÇÜLEMEDİ, "sonsuz kâr faktörü" DEĞİL
# =================================================================================================
def test_1_brut_zarar_sifirken_pf_none_ve_nedeni_dolu(defterli):
    """`cikis_nedeni: target` iki KÂRLI işlemden oluşur → brüt zarar tam sıfır. PF'in matematiksel
    hâli tanımsızdır; `inf` yazmak "sonsuz iyi" diye okunurdu ve JSON'da da bozuktur."""
    yuk = topviews.topviews()
    hedef = _satir(yuk, "cikis_nedeni", "target")
    assert hedef["n"] == 2 and hedef["wins"] == 2
    assert hedef["gross_loss"] == 0.0, "fikstür varsayımı düştü: target hücresinde zarar var"
    assert hedef["pf"] is None, f"brüt zarar sıfırken PF üretildi: {hedef['pf']!r}"
    assert hedef["pf_yok_nedeni"], "PF ölçülemedi ama NEDEN yazılmadı (YASA 4)"
    assert len(hedef["pf_yok_nedeni"]) >= 20, "neden ≥20 karakter olmalı (YASA 4)"


def test_1b_yukun_hicbir_yerinde_inf_ya_da_nan_yok(defterli):
    """Tek hücre değil YÜZEY taranır: `inf`/`nan` yükün HERHANGİ bir yerinden sızarsa pano onu
    ya `Infinity` diye basar ya da katı bir ayrıştırıcı yükü tamamen reddeder."""
    yuk = topviews.topviews()
    metin = json.dumps(yuk, allow_nan=False)      # allow_nan=False: inf/nan varsa BURADA patlar
    assert "Infinity" not in metin and "NaN" not in metin

    def _tara(x, yol=""):
        if isinstance(x, float):
            assert math.isfinite(x), f"sonlu olmayan değer: {yol} = {x!r}"
        elif isinstance(x, dict):
            for k, v in x.items():
                _tara(v, f"{yol}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                _tara(v, f"{yol}[{i}]")
    _tara(yuk)


# =================================================================================================
# [2] n == 0 SATIR BASILMAZ (v197 koşulsuz emisyon tavanı)
# =================================================================================================
def test_2_bos_kova_satiri_yukte_yok(defterli):
    """R kovaları ÖNCEDEN SABİTTİR (altı kova) ama fikstür yalnız üçünü doldurur. Boş kovanın
    `n: 0` satırı basılsaydı pano üç boş satır çizer ve okur onları "ölçüldü, sıfır çıktı" diye
    okurdu."""
    yuk = topviews.topviews()
    for _, s in _tum_satirlar(yuk):
        assert s["n"] > 0, f"n==0 satırı yükte: {s}"

    dolu = {s["deger"] for s in _facet(yuk, "r_kovasi")["satirlar"]}
    # Sabit kova listesinin BAŞKA elemanları var ve onlar basılmadı — pozitif kontrol: test bir
    # şeyi gerçekten dışarıda bırakıyor, boş bir kümeye "hepsi pozitif" demiyor.
    assert dolu < {ad for ad, _, _ in topviews.R_KOVALARI}
    assert dolu == {"-1..0R", "1..2R", "2..3R"}


# =================================================================================================
# [3] ETİKETSİZ SATIR SAYIMA GİRMEZ AMA RAPORLANIR
# =================================================================================================
def test_3_etiketsiz_islem_sayima_girmez_ama_raporlanir(defterli):
    """T5'in `setup`u yok. Onu bir kovaya ("?" ya da "diğer") koymak, ETİKETLENMEMİŞ bir işlemi
    etiketlenmiş gibi gösterirdi; sessizce düşürmek ise 5 satırlık defteri 4 satır gibi okuturdu."""
    yuk = topviews.topviews()
    kur = _facet(yuk, "kurulum")
    assert kur["etiketsiz_n"] == 1, f"etiketsiz sayacı yanlış: {kur['etiketsiz_n']}"
    assert sum(s["n"] for s in kur["satirlar"]) == 4, "etiketsiz satır kovaya sızdı"
    assert "?" not in {s["deger"] for s in kur["satirlar"]}
    assert kur["etiketsiz_neden"], "etiketsizlik sayıldı ama NEDENİ yazılmadı"

    # AYNI SATIR BAŞKA FACETTE ETİKETLİDİR: etiketsizlik FACET BAŞINADIR, satır başına değil.
    assert _facet(yuk, "rejim")["etiketsiz_n"] == 0
    assert sum(s["n"] for s in _facet(yuk, "rejim")["satirlar"]) == 5

    # SEKTÖR: etiket PLAN defterinden gelir (işlem defterinde `sector` alanı YOKTUR); P5 sektörsüz.
    sek = _facet(yuk, "sektor")
    assert sek["etiketsiz_n"] == 1
    assert sum(s["n"] for s in sek["satirlar"]) == 4


# =================================================================================================
# [4] sum_r BİREBİR · [5] pf BİREBİR · [6] kazanma BİREBİR
# =================================================================================================
def test_4_sum_r_birebir(defterli):
    yuk = topviews.topviews()
    vcp = _satir(yuk, "kurulum", "breakout_vcp")        # T1 +2,0 · T2 +1,0 · T3 −1,0
    assert vcp["n"] == 3 and vcp["r_n"] == 3
    assert vcp["sum_r"] == pytest.approx(2.0)
    assert vcp["gross_win"] == pytest.approx(3.0)
    assert vcp["gross_loss"] == pytest.approx(-1.0)
    # ÖZDEŞLİK: brüt kâr + brüt zarar = net toplam. Ayrıştırma bir YENİDEN ANLATIM olmalı, yeni
    # bir sayı değil — özdeşlik düşerse ayrıştırma defteri terk etmiştir.
    assert vcp["gross_win"] + vcp["gross_loss"] == pytest.approx(vcp["sum_r"])

    pb = _satir(yuk, "kurulum", "pullback")             # T4 −0,5
    assert pb["n"] == 1 and pb["sum_r"] == pytest.approx(-0.5)

    # TÜM DEFTER TOPLAMI: 2,0 + 1,0 − 1,0 − 0,5 − 1,0 = 0,5 (etiketsiz T5 DAHİL, çünkü `rejim`
    # facetinde etiketsiz satır yok).
    rej = _facet(yuk, "rejim")["satirlar"]
    assert sum(s["sum_r"] for s in rej) == pytest.approx(0.5)


def test_5_pf_birebir(defterli):
    yuk = topviews.topviews()
    vcp = _satir(yuk, "kurulum", "breakout_vcp")
    assert vcp["pf"] == pytest.approx(3.0)              # 3,0 / |−1,0|
    assert vcp["pf_yok_nedeni"] is None

    pb = _satir(yuk, "kurulum", "pullback")
    assert pb["pf"] == pytest.approx(0.0)               # 0,0 / |−0,5| → SIFIR, None DEĞİL:
    assert pb["pf_yok_nedeni"] is None                  # payda ölçüldü, sonuç gerçekten sıfır

    dur = _satir(yuk, "cikis_nedeni", "stop")           # 0,0 / |−2,5|
    assert dur["pf"] == pytest.approx(0.0)

    tr = _satir(yuk, "rejim", "trend_up")               # 3,0 / 0 → tanımsız
    assert tr["pf"] is None and tr["pf_yok_nedeni"]


def test_6_kazanma_birebir(defterli):
    yuk = topviews.topviews()
    vcp = _satir(yuk, "kurulum", "breakout_vcp")
    assert vcp["wins"] == 2
    assert vcp["kazanma"] == pytest.approx(2 / 3)
    assert vcp["kazanma"] == pytest.approx(vcp["wins"] / vcp["r_n"])
    assert vcp["r_n"] == vcp["n"], "işlem faceti paydası: her satır R taşır"

    ch = _satir(yuk, "rejim", "chop")                   # T3 −1,0 · T4 −0,5 · T5 −1,0
    assert ch["n"] == 3 and ch["wins"] == 0 and ch["kazanma"] == pytest.approx(0.0)


# =================================================================================================
# KAPI AİLESİ — plan defteri paydası, çok etiketli facet, işleme dönüşmemiş plan
# =================================================================================================
def test_kapi_reddi_cok_etiketli_ve_sonucsuz_plani_dogru_sayar(defterli):
    """Bir plan BİRDEN ÇOK ölçütte takılabilir (P3: score_band + leading_sector) → `n` toplamı
    plan sayısını AŞAR ve bu BEYANLIDIR. İşleme dönüşmemiş plan (P6) sonuç taşımaz: `n`e girer,
    `r_n`e girmez."""
    yuk = topviews.topviews()
    red = _facet(yuk, "kapi_reddi")
    assert red["cok_etiketli"] is True

    sb = _satir(yuk, "kapi_reddi", "score_band")        # P2→T2 (+1,0) · P3→T3 (−1,0)
    assert sb["n"] == 2 and sb["r_n"] == 2
    assert sb["sum_r"] == pytest.approx(0.0)
    assert sb["pf"] == pytest.approx(1.0)

    hh = _satir(yuk, "kapi_reddi", "heat_hard")         # P4→T4 (−0,5) · P6 işleme DÖNMEDİ
    assert hh["n"] == 2, "işleme dönüşmemiş plan sayımdan düştü"
    assert hh["r_n"] == 1, "sonuçsuz plan R paydasına sızdı"
    assert hh["sum_r"] == pytest.approx(-0.5)

    # HİÇBİR ÖLÇÜTTE TAKILMAYAN PLAN bir RET DEĞİLDİR ve bir facet satırı olarak basılmaz —
    # ama sayılır, yoksa 6 planlık defter 4 plan gibi okunurdu.
    assert red["ek"]["hicbir_olcutte_takilmayan_plan_n"] == 2


def test_kapi_hukmu_plan_defterinden_gercek_degerlerle_gelir(defterli):
    """Hüküm etiketleri UYDURULMAZ, defterden gelir: bu sistemde `GO`/`REVIEW`/`NO_GO`."""
    yuk = topviews.topviews()
    hk = _facet(yuk, "kapi_hukmu")
    assert {s["deger"] for s in hk["satirlar"]} == {"GO", "REVIEW", "NO_GO"}
    assert sum(s["n"] for s in hk["satirlar"]) == len(PLANLAR)
    ng = _satir(yuk, "kapi_hukmu", "NO_GO")             # P4→T4 (−0,5) · P6 sonuçsuz
    assert ng["n"] == 2 and ng["r_n"] == 1


def test_r_tasimayan_facet_satirinda_toplamlar_none_neden_dolu(sandbox_state):
    """Hiçbir planı işleme dönüşmemiş bir kapı ölçütünde `sum_r: 0.0` yazmak "başabaş kapandı"
    diye okunurdu. Boş kümenin toplamı matematikte sıfırdır; DEFTERDE ölçülmemiştir."""
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("trade_plans.jsonl", [PLANLAR[5]])   # P6: işleme dönüşmemiş NO_GO
    yuk = topviews.topviews()
    hh = _satir(yuk, "kapi_reddi", "heat_hard")
    assert hh["n"] == 1 and hh["r_n"] == 0
    assert hh["sum_r"] is None and hh["gross_win"] is None and hh["gross_loss"] is None
    assert hh["kazanma"] is None and hh["pf"] is None
    assert hh["pf_yok_nedeni"] and len(hh["pf_yok_nedeni"]) >= 20


# =================================================================================================
# [7] DOKUZ FACET · [8] BOŞ LİSTE YASAĞI · [9] HER FACET KENDİ KAYNAĞINI BEYAN EDER
# =================================================================================================
def test_7_dokuz_facetin_hepsi_yukte(defterli):
    yuk = topviews.topviews()
    assert set(yuk["aileler"]) == {"KAYNAK", "SONUC", "KAPI"}
    bulunan = {ad for aile in yuk["aileler"].values() for ad in aile}
    assert bulunan == set(topviews.FACETLER), f"eksik/fazla facet: {bulunan ^ set(topviews.FACETLER)}"
    assert len(topviews.FACETLER) == 9
    for aile in yuk["aileler"].values():
        for ad, f in aile.items():
            # ÜÇ HÂL: ölçüldü (liste) · ölçülemedi (None + neden). Dördüncü hâl (boş liste) YOK.
            assert f["satirlar"] is None or f["satirlar"], f"{ad} BOŞ LİSTE döndü"
            if f["satirlar"] is None:
                assert f["olculemedi_neden"], f"{ad} ölçülemedi ama neden yok"
            else:
                assert f["olculemedi_neden"] is None


def test_7b_dokuz_facet_bos_defterde_de_yukte_none_ve_nedenle(sandbox_state):
    """Defter boşken facetler yükten DÜŞMEZ. Düşselerdi pano dokuz kartın üçünü hiç çizmez ve
    okur eksikliği "böyle bir kırılım yok" diye okurdu."""
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("trade_plans.jsonl", [])
    yuk = topviews.topviews()
    bulunan = {ad for aile in yuk["aileler"].values() for ad in aile}
    assert bulunan == set(topviews.FACETLER)
    for aile in yuk["aileler"].values():
        for ad, f in aile.items():
            assert f["satirlar"] is None, f"{ad} boş defterde satır üretti"
            assert len(f["olculemedi_neden"]) >= 20, f"{ad} nedeni yetersiz (YASA 4)"


def test_8_kapi_reddi_olculemiyorsa_none_bos_liste_degil(sandbox_state):
    """Planlar var ama YAPISAL kapı ölçütü (`gate_checks`) taşımıyorlar. Boş liste dönmek
    "hiçbir plan reddedilmedi" derdi; gerçek "hangi ölçütte takıldıkları YAZILMAMIŞ"tır."""
    store.write_jsonl("trades.jsonl", ISLEMLER)
    store.write_jsonl("trade_plans.jsonl",
                      [{"id": p["id"], "date": p["date"], "ticker": p["ticker"],
                        "sector": p["sector"], "gate_verdict": p["gate_verdict"],
                        "gate_reasons": ["skor alt bantta"]} for p in PLANLAR])
    yuk = topviews.topviews()
    red = _facet(yuk, "kapi_reddi")
    assert red["satirlar"] is None, f"boş/uydurma liste döndü: {red['satirlar']!r}"
    assert red["satirlar"] != []
    assert "gate_checks" in red["olculemedi_neden"], \
        f"neden hangi alanın eksik olduğunu söylemiyor: {red['olculemedi_neden']!r}"

    # KARŞI-KONTROL: aynı defterde `kapi_hukmu` ÖLÇÜLÜR — ret ölçülemedi diye tüm aile düşmez.
    assert _facet(yuk, "kapi_hukmu")["satirlar"]


def test_9_her_facet_kendi_kaynagini_ve_penceresini_bildirir(defterli):
    yuk = topviews.topviews()
    kay = yuk["facet_kaynaklari"]
    assert set(kay) == set(topviews.FACETLER)
    for ad, k in kay.items():
        assert k["kaynak"] and len(k["kaynak"]) >= 10, f"{ad}: kaynak beyanı yok"
        assert k["pencere"], f"{ad}: pencere beyanı yok"
        assert isinstance(k["n"], int), f"{ad}: payda sayısı yok"
    # PAYDALAR AYRIDIR VE AYRI OLDUKLARI GÖRÜNÜR: yedi facet işlem defterini, iki facet plan
    # defterini sayar. Tek bir sayıymış gibi göstermek "ölçüm bağlamı tuzağı"dır.
    assert kay["kurulum"]["n"] == len(ISLEMLER) == 5
    assert kay["kapi_hukmu"]["n"] == len(PLANLAR) == 6
    assert "trades.jsonl" in kay["kurulum"]["kaynak"]
    assert "trade_plans.jsonl" in kay["kapi_hukmu"]["kaynak"]
    # SEKTÖR İKİ DEFTERİ BİRLEŞTİRİR — beyanı bunu SÖYLEMELİ, yoksa okur onu saf işlem faceti sanar.
    assert "trade_plans.jsonl" in kay["sektor"]["kaynak"] and "trades.jsonl" in kay["sektor"]["kaynak"]
    # PENCERE GERÇEK TARİHLERDEN TÜRER (sabit metin değil).
    assert "2026-01-12" in kay["kurulum"]["pencere"]
    assert "2026-01-08" in kay["kapi_hukmu"]["pencere"]
    # İKİ FACET KENDİ ÖLÇÜM TUZAĞINI DA BEYAN EDER — beyan düşerse okur sayıyı yanlış okur:
    #   kapi_reddi → `n` toplamı paydayı AŞAR (çok etiketli)
    #   r_kovasi   → PF tautolojiktir (kova zaten R'nin işaretine göre bölünmüştür)
    assert "ÇOK ETİKETLİ" in kay["kapi_reddi"]["payda"]
    assert "TAUTOLOJİK" in kay["r_kovasi"]["payda"]
    for ad in topviews.FACETLER:
        assert len(kay[ad]["payda"]) >= 20, f"{ad}: payda cümlesi yok"


# =================================================================================================
# [10] YETKİ
# =================================================================================================
def test_10_uc_tokensiz_istegi_reddeder(defterli, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "GIZLI-JETON")
    with TestClient(api.app) as c:
        assert c.get("/api/topviews").status_code == 401
        ok = c.get("/api/topviews", headers={"x-meridian-token": "GIZLI-JETON"})
    assert ok.status_code == 200
    assert set(ok.json()["aileler"]) == {"KAYNAK", "SONUC", "KAPI"}


def test_10b_uc_500_donmez_ve_json_serilesir(defterli, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    with TestClient(api.app) as c:
        r = c.get("/api/topviews")
    assert r.status_code == 200, r.text[:300]
    json.dumps(r.json(), allow_nan=False)
