"""v292 — ÖZ-DEĞERLENDİRMENİN KALICI YALANCI POZİTİFLERİ: "eşik doldu" ≠ "karar bekliyor".

CANLI ARIZA (2026-08-25 ölçümü): `self_review.json` dikkat listesi her gün DÖRT "yüksek" satır
taşıyordu ve dördü de ZATEN ALINMIŞ kararları "karar hazır" diye ilan ediyordu:
  · "silahlanma kanıtı doldu: momentum_burst (1093/30)" → `strategy.ARMED_SETUPS` üyesi, SİLAHLI
  · "silahlanma kanıtı doldu: breakout_vcp (1012/30)"   → aynı, SİLAHLI
  · "cf_fidelity: eşik doldu (306/10) — karar hazır"    → `cf_fidelity.json::fidelity_ok` = true
  · "llm_promotion: eşik doldu (100/30) — karar hazır"  → `llm_calibration.json::promoted` = true
Dikkat listesi 8 satırla kırpılır; dört kalıcı yalancı pozitif tek GERÇEK kalemi ("6 bekçi olayı")
listenin dibine itiyordu. Bir dikkat listesini değersizleştirmek, onu hiç yazmamaktan pahalıdır.

KÖK NEDEN İKİ AYRI YÜZEYDE AYNI: "eşiğin dolması" ile "bir kararın BEKLEMESİ" özdeş sayılmıştı.
  (1) `progress["setup_arming"]` ham `arming_report.json::cf_report` üzerinde kuruluyordu; o sözlük
      SİLAHLI ve UYUYAN kurulumların HEPSİNİ taşır. `arming._dormant_setups()` ayrımı zaten DOĞRU
      yapıyor (motor listesi − ARMED_SETUPS) — selfreview ona hiç sormuyordu.
  (2) `cf_fidelity`/`llm_promotion` kararlarını ÜRETİCİLERİ (analytics) eşik dolar dolmaz kendileri
      verir ve hükmü artefakta yazar; bekleyen bir insan kararı YOKTUR.

ÇİVİLENEN İDDİA (uygulama değil): (a) SİLAHLI bir kurulum dikkat listesine düşmez, (d) UYUYAN ve
eşiği dolmuş bir kurulum HÂLÂ düşer (kapı büsbütün kapanmadı), (b) `fidelity_ok: true` iken
cf_fidelity satırı yok, (c) `promoted: true` iken llm satırı yok, (e) karar İŞARETİ hiç yoksa satır
ÇIKAR ve "ölçülemedi" der (susmak da uydurmaktır), (f) karar işareti OLMAYAN kalemler ("gerçekten
bekleyen") hâlâ "karar hazır" der, (g) beklemeyen kalemler `progress` GÖVDESİNDE kalır.
"""
from __future__ import annotations

import pytest

from meridian import arming, selfreview, store, strategy

# `_dormant_setups()` motor listesinden ARMED_SETUPS'ı düşer; bu testin fikstürü o listenin
# TAMAMINI (silahlı + uyuyan) cf karnesine koyar — yalancı pozitifin canlıdaki üretim koşulu buydu.
UYUYAN = tuple(arming._dormant_setups())
SILAHLI = tuple(s for s in strategy.ARMED_SETUPS)
NEED = arming.MIN_CF_ENTERED
DOLU = NEED * 36            # canlı büyüklük sınıfı (1012-1093 civarı): eşik tartışmasız dolu


def _cf_karne(setuplar, n=DOLU) -> dict:
    """`arming.setup_report()` ŞEKLİNDE bir cf karnesi (n · win_rate · avg_r · rejim dağılımı)."""
    return {s: {"n": n, "win_rate": 0.52, "avg_r": 0.41, "regimes": {"neutral": n}} for s in setuplar}


def _dikkat(rep: dict, parca: str) -> list:
    """DİKKAT listesinde `parca` metnini içeren satırlar."""
    return [a for a in rep["attention"] if parca in a["why"]]


def test_fikstur_anlamli():
    """Fikstür KORUMASI: hem silahlı hem uyuyan kurulum VARSA bu dosyadaki iddialar bir şey ölçer.
    Küme boşalırsa (ör. hepsi silahlanırsa) testler sessizce 'geçer' hâle gelirdi."""
    assert SILAHLI and UYUYAN, "silahlı/uyuyan ayrımı boş — çiviler ölçmeyi bırakır"
    assert not (set(SILAHLI) & set(UYUYAN)), "bir kurulum aynı anda hem silahlı hem uyuyan olamaz"


# ---------------------------------------------------------------- (a) + (d) silahlı vs uyuyan
def test_silahli_kurulum_dusmez_uyuyan_kurulum_hala_duser(sandbox_state):
    """CANLI VAKANIN BİREBİRİ: cf karnesinde HEM silahlı HEM uyuyan kurulumlar eşiği dolduruyor.

    İki iddia AYNI koşumda ölçülür — bu bilinçli: yalnız 'silahlı satır yok' demek, dikkat listesi
    boş kaldığında da geçerdi. Uyuyan satırın AYNI listede bulunması, kapının büsbütün kapanmadığını
    (yani sessizliğin bir kırpma/çökme artefaktı olmadığını) kanıtlar."""
    store.write_json("arming_report.json",
                     {"cf_report": _cf_karne(SILAHLI + UYUYAN), "measurements": {}})

    rep = selfreview.build()

    for s in SILAHLI:
        assert not _dikkat(rep, s), f"SİLAHLI kurulum dikkat listesine düştü: {s}"
        assert s not in rep["progress"]["setup_arming"], \
            f"{s} silahlı — 'silahlanmaya ne kadar kaldı' sayacında işi yok"
    for s in UYUYAN:
        rows = _dikkat(rep, f"silahlanma kanıtı doldu: {s}")
        assert len(rows) == 1 and rows[0]["sev"] == "yüksek", \
            f"UYUYAN + eşiği dolmuş kurulum dikkat listesinden düştü: {s}"
        assert rep["progress"]["setup_arming"][s] == {"have": DOLU, "need": NEED}


def test_uyuyan_kume_ikinci_kez_tanimlanmadi(sandbox_state):
    """TEK TANIM: uyuyan küme `arming._dormant_setups()`ten gelir. selfreview ikinci bir tanım
    yazarsa (ya da ham cf_report anahtarlarına dönerse) bu satır kırmızı yanar."""
    store.write_json("arming_report.json",
                     {"cf_report": _cf_karne(SILAHLI + UYUYAN + ("uydurma_kurulum",)),
                      "measurements": {}})
    rep = selfreview.build()
    assert set(rep["progress"]["setup_arming"]) == set(UYUYAN), \
        "setup_arming anahtarları arming'in uyuyan türetmesiyle birebir olmalı"


def test_cf_karnesinde_hic_olmayan_uyuyan_kurulum_sifirla_gorunur(sandbox_state):
    """UYDURMA YASAĞI'nın tersi de geçerli: kanıtı henüz olmayan uyuyan kurulum sayaçtan SİLİNMEZ,
    0/NEED olarak durur — 'ilerleme yok' bir ölçümdür, yokluk değil."""
    store.write_json("arming_report.json", {"cf_report": {}, "measurements": {}})
    rep = selfreview.build()
    assert rep["progress"]["setup_arming"] == {s: {"have": 0, "need": NEED} for s in UYUYAN}
    assert not _dikkat(rep, "silahlanma kanıtı doldu")


# ------------------------------------------------------------------ (b) + (c) + (g) karar alınmış
def test_karari_verilmis_kalemler_dikkate_dusmez_ama_progresste_kalir(sandbox_state):
    """`fidelity_ok: true` ve `promoted: true` = karar VERİLMİŞ. Dikkat satırı YOK; ama ilerleme
    ölçüsü olarak `progress` gövdesinde AYNEN kalır (kalemi gömmek, ölçüyü de gömerdi)."""
    store.write_json("cf_fidelity.json",
                     {"n": 306, "corr": 0.899, "mean_diff_r": 0.039, "fidelity_ok": True})
    store.write_json("llm_calibration.json", {"n_pairs": 100, "promoted": True, "cf_pairs": 7})

    rep = selfreview.build()

    assert not _dikkat(rep, "cf_fidelity:"), "karar verilmiş kalem 'karar hazır' diyemez"
    assert not _dikkat(rep, "llm_promotion:"), "terfi YAPILMIŞ kalem 'karar hazır' diyemez"
    assert rep["progress"]["cf_fidelity"]["have"] == 306
    assert rep["progress"]["llm_promotion"]["have"] == 100
    assert rep["progress"]["cf_fidelity"][selfreview.KARAR_ANAHTARI] is True
    assert rep["progress"]["llm_promotion"][selfreview.KARAR_ANAHTARI] is True


def test_karar_isareti_false_da_bir_karardir(sandbox_state):
    """İŞARETİN VARLIĞI karardır, YÖNÜ değil: `promoted: false` da üreticinin verdiği bir hükümdür
    (eşik dolmuş, terfi ETMEMİŞ) — bekleyen bir insan kararı yoktur, satır çıkmaz."""
    store.write_json("llm_calibration.json", {"n_pairs": 100, "promoted": False, "cf_pairs": 7})
    rep = selfreview.build()
    assert not _dikkat(rep, "llm_promotion:")
    assert rep["progress"]["llm_promotion"][selfreview.KARAR_ANAHTARI] is False


# ------------------------------------------------------------------------ (e) işaret ölçülemedi
@pytest.mark.parametrize("kalem", sorted(selfreview.KARAR_ISARETI))
def test_karar_isareti_yoksa_satir_cikar_ve_olculemedi_der(sandbox_state, kalem):
    """SUSMAK DA UYDURMAKTIR: alan hiç yoksa 'karar verildi' de 'karar bekliyor' da uydurmadır.
    Satır ÇIKAR, 'karar işareti ölçülemedi' der ve BAKILAN KAYNAĞI adıyla söyler."""
    dosya, alan = selfreview.KARAR_ISARETI[kalem]
    # aynı belge, karar alanı OLMADAN: eşik dolu (satır çıkmalı), hüküm yok (adı konmalı)
    store.write_json("cf_fidelity.json", {"n": 306, "corr": 0.899, "mean_diff_r": 0.039})
    store.write_json("llm_calibration.json", {"n_pairs": 100, "cf_pairs": 7})

    rep = selfreview.build()

    rows = _dikkat(rep, f"{kalem}:")
    assert len(rows) == 1 and rows[0]["sev"] == "yüksek", f"{kalem} işaretsizken sessiz kaldı"
    assert "ölçülemedi" in rows[0]["why"] and "karar hazır" not in rows[0]["why"]
    assert f"{dosya}::{alan}" in rows[0]["why"], "hangi kaynağa bakıldığı satırda YAZILI olmalı"
    assert rep["progress"][kalem][selfreview.KARAR_ANAHTARI] is None


def test_karar_isareti_tablosu_iki_yonu_de_besliyor(sandbox_state):
    """İKİ KAYNAK AYRIŞMASIN: tabloda adı geçen HER kalem `progress`te vardır ve karar damgasını
    TAŞIR. Biri eklenip diğeri unutulursa (bu deponun baskın hata deseni) burası kırmızı yanar."""
    rep = selfreview.build()
    for kalem in selfreview.KARAR_ISARETI:
        assert kalem in rep["progress"], f"karar işareti tablosunda olmayan kalem: {kalem}"
        assert selfreview.KARAR_ANAHTARI in rep["progress"][kalem], \
            f"{kalem} karar damgası taşımıyor — 'ölçülemedi' cevabı bir kusuru örterdi"


# ------------------------------------------------------- (f) gerçekten bekleyen karar susturulmadı
def test_gercekten_bekleyen_karar_hala_karar_hazir_diyor(sandbox_state):
    """KAPI BÜSBÜTÜN KAPANMADI: karar işareti TANIMLANMAMIŞ kalemler (ör. shadow_promotion) eşiği
    doldurduğunda eskisi gibi 'karar hazır' der. Genel kural yalnız BEKLEMEYEN kalemleri susturur."""
    store.write_json("shadow_model.json", {"promotion": {"n_live": 50}})
    rep = selfreview.build()
    rows = _dikkat(rep, "shadow_promotion:")
    assert len(rows) == 1 and "karar hazır" in rows[0]["why"] and rows[0]["sev"] == "yüksek"


# -------------------------------------------------------------------- danışma sınırı korunuyor
def test_katman_hala_danisma_katmani(sandbox_state):
    """Bu tur hiçbir karar yüzeyine dokunmadı: yazılan tek karar dosyası yok."""
    store.write_json("arming_report.json",
                     {"cf_report": _cf_karne(SILAHLI + UYUYAN), "measurements": {}})
    before = {p.name for p in sandbox_state.glob("*")}
    selfreview.build()
    touched = {p.name for p in sandbox_state.glob("*")} - before
    assert touched <= {"self_review.json", "events.jsonl", "skill_revisions.json",
                       "near_miss.json", "sieve.json", ".locks"}, f"beklenmeyen yazım: {touched}"
    assert not (sandbox_state / "strategy.yaml").exists()
