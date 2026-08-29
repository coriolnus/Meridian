"""test_ucretsiz_katman_fiyati_v325.py — ÖLÇÜLEN UYDURMA: ücretsiz katman Opus fiyatına yazıldı.

ÖLÇÜM (2026-08-27, canlı A1 state/spend.jsonl):
    10 çağrı   6.49 USD   nvidia/nemotron-3-super-120b-a12b:free
     3 çağrı   1.40 USD   nvidia/nemotron-3-ultra-550b-a55b:free
İkisi de OpenRouter ÜCRETSİZ katman; gerçek maliyet 0. Deftere ve panoya 7.89 USD UYDURULDU.

KÖK NEDEN: `price_for` (meridian/spend.py) model adını PRICES anahtarlarıyla ALT-DİZGE
eşleştirir: opus/sonnet/haiku/gemini/hermes-4/nous. Canlı slug `nvidia/nemotron-...:free`
bunların HİÇBİRİNİ tutmaz — "nous" da GEÇMEZ — ve muhafazakâr varsayılana, yani tam olarak
Opus listesine `(15.0, 75.0)` düşer. Modülün KENDİ docstring'i bu arıza SINIFINI zaten
yazmıştı ("harcanmamış para bütçeyi doldurur ve LLM katmanı sessizce kapanırdı"); sınıf
kapanmadı çünkü tablo o güne kadar tek tek SATICI ADIYLA büyüdü — kapanan şey sınıf değil,
o günkü örneklerdi.

NEDEN SATICI ADI DEĞİL, `:free` VARYANT SONEKİ (bu çivinin asıl hükmü): tabloya "nemotron"
ya da "nvidia" eklemek arızayı TERSİNE çevirirdi — OpenRouter'da aynı satıcının ÜCRETLİ
varyantları da var (aynı slug, soneksiz) ve onlar 0'a fiyatlanırdı. Bu da aynı yasanın
(UYDURMA YASAĞI) öbür yönden ihlali olurdu: bu kez harcanmış para deftere HİÇ girmezdi.
`:free` soneki OpenRouter'ın kendi sözleşmesinde "bu varyantın ücreti sıfırdır" demektir —
yarın eklenen ücretsiz bir model de, adı hiç bilinmeden, doğru fiyatlanır. Zincirin bugünkü
öbür ücretsiz uçları (`tencent/hy3:free`, `openai/gpt-oss-20b:free`) aynı kuralla kapanır.

ÇİVİLER:
  UK1  canlı slug'lar 0 fiyatlanır; defter satırı 0 taşır ve bütçeyi yemez
  UK2  ÇÜRÜTME — çivi boş DEĞİL: gerçekten ücretli slug hâlâ 0'ın ÜSTÜNDE fiyatlanır
  UK3  kural PRICES sırasına bağlı değil: tabloda adı geçen bir ailenin `:free` varyantı da 0
  UK4  eşleşme SEGMENTtir, alt-dizge değil: adında "free" geçen ücretli slug bedava sayılmaz
"""
from __future__ import annotations

import pytest

from meridian import spend, store


# ÖLÇÜLDÜ: 2026-08-27 canlı defterinde uydurma maliyet taşıyan iki slug + zincirin öbür
# ücretsiz uçları (ROADMAP 2026-08-14 beyin-zinciri taşınması).
CANLI_UCRETSIZ = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openai/gpt-oss-20b:free",
    "tencent/hy3:free",
]


# ---------- UK1: canlı ücretsiz slug'lar sıfır fiyatlanır ----------
@pytest.mark.parametrize("slug", CANLI_UCRETSIZ)
def test_uk1_canli_ucretsiz_slug_sifir_fiyatlanir(slug):
    assert spend.price_for(slug) == (0.0, 0.0), f"{slug} ücretsiz katman ama fiyatlı"
    assert spend.estimate_cost(1_000_000, 1_000_000, slug) == 0.0


@pytest.mark.parametrize("slug", CANLI_UCRETSIZ)
def test_uk1b_defter_satiri_sifir_tasir_ve_butceyi_yemez(sandbox_state, slug):
    """Zarar fiyat fonksiyonunda DEĞİL, deftere düşen satırda ve panoda görünüyordu."""
    row = spend.record(500_000, 200_000, slug, note="reflect (openrouter)")
    assert row["cost_usd"] == 0.0
    assert store.read_jsonl("spend.jsonl")[-1]["cost_usd"] == 0.0
    assert spend.month_spend() == 0.0, "harcanmamış para bütçeyi dolduruyor"
    assert spend.over_budget() is False
    assert spend.summary()["spent_usd"] == 0.0        # /api/spend → pano


def test_uk1c_olculen_vaka_yeniden_uretilir(sandbox_state):
    """13 çağrılık canlı kesit: eskiden 7.89 USD yazıyordu, doğrusu 0."""
    for _ in range(10):
        spend.record(10_000, 2_000, "nvidia/nemotron-3-super-120b-a12b:free", note="reflect")
    for _ in range(3):
        spend.record(10_000, 2_000, "nvidia/nemotron-3-ultra-550b-a55b:free", note="reflect")
    s = spend.summary()
    assert s["calls_this_month"] == 13, "çağrılar deftere düşmüyor — çivi boşa geçerdi"
    assert s["spent_usd"] == 0.0


# ---------- UK2: ÇÜRÜTME — çivi boş değil ----------
@pytest.mark.parametrize("slug", [
    "claude-opus-4-8",                          # tabloda: ücretli
    "claude-sonnet-5",                          # tabloda: ücretli
    "nvidia/nemotron-3-super-120b-a12b",        # AYNI aile, ÜCRETLİ varyant (soneksiz)
    "bilinmeyen-model-x",                       # bilinmeyen → muhafazakâr varsayılan
])
def test_uk2_ucretli_slug_hala_sifirin_ustunde_fiyatlanir(slug):
    """Boş çivi sınavı: `price_for` her şeye 0 dönerse UK1 bedavaya geçerdi.

    Üçüncü satır kasıtlı: tabloya "nemotron"/"nvidia" eklenmiş olsaydı BU satır düşerdi —
    yani bu parametre, reddedilen alternatif çözümün çürütmesidir."""
    p_in, p_out = spend.price_for(slug)
    assert p_in > 0 and p_out > 0, f"{slug} ücretli ama 0 fiyatlanıyor — harcama deftere girmez"
    assert spend.estimate_cost(1_000_000, 1_000_000, slug) > 0


def test_uk2b_bilinmeyen_model_muhafazakar_varsayilanda_kalir():
    """Ücretsiz kuralı varsayılanı GEVŞETMEMELİ: sonek yoksa eski davranış aynen sürer."""
    assert spend.price_for("bilinmeyen-model-x") == (spend.PRICE_IN_PER_M, spend.PRICE_OUT_PER_M)


# ---------- UK3: kural PRICES sırasına bağlı değil ----------
def test_uk3_tabloda_adi_gecen_ailenin_free_varyanti_da_sifirdir():
    """`:free` soneki OTORİTERdir, alt-dizge tablosundan ÖNCE gelir.

    Kural yalnız tabloya bir anahtar eklemekle kurulsaydı hüküm dict SIRASINA bağlı olurdu:
    "opus" anahtarı önce gelirse `...opus...:free` Opus listesinden fiyatlanırdı. Sıra
    görünmez bir sözleşmedir; bu çivi onu görünür kılar."""
    assert spend.price_for("anthropic/claude-opus-4.8:free") == (0.0, 0.0)
    assert spend.price_for("google/gemini-3.1-pro:free") == (0.0, 0.0)


def test_uk3b_buyuk_harf_ve_bosluk_kurali_bozmaz():
    assert spend.price_for("NVIDIA/Nemotron-3-Ultra-550B-A55B:FREE") == (0.0, 0.0)
    assert spend.price_for("  nvidia/nemotron-3-ultra-550b-a55b:free  ") == (0.0, 0.0)


# ---------- UK4: segment eşleşmesi, alt-dizge değil ----------
@pytest.mark.parametrize("slug", [
    "vendor/model:freeform",        # sonek "free" DEĞİL, "freeform"
    "vendor/free-tier-clone-7b",    # adında "free" geçiyor ama varyant soneki yok
    "freebase/some-model",
])
def test_uk4_adinda_free_gecen_ucretli_slug_bedava_sayilmaz(slug):
    """`":free" in m` alt-dizge testi bu üç slug'ı da bedava sayardı — ölçülmemiş bir
    indirim, yine UYDURMA. Eşleşme iki nokta ile ayrılmış SEGMENT üzerindedir."""
    assert spend.price_for(slug) != (0.0, 0.0), f"{slug} ücretsiz sayıldı — harcama kaybolur"
