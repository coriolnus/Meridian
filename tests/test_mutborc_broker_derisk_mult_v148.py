"""test_mutborc_broker_derisk_mult_v148.py — H5 test-borcu: broker.derisk_mult mutasyon kümesi.

Bu dosya bir "mutasyon borcu" kapatma dosyası: mutmut'ın `meridian.broker.derisk_mult` üzerinde
HAYATTA BIRAKTIĞI 4 mutantı hedefler. derisk_mult, çekilme (drawdown) derinliğine göre YENİ pozisyon
boyunu kısan tek çarpandır; canlıda ve backtest'te aynı yerden okunur. Yani buradaki her sessiz
sapma, gerçek parayla alınan riskin boyunu değiştirir — bu yüzden testler "yaklaşık" değil, SINIR
DEĞERİ ve TAM SAYI iddiaları kurar.

Sözleşme (meridian/broker.py:178):
    peak <= 0            -> 1.0                      (ölçülemeyen zirve cezalandırılmaz)
    dd <= 0.03           -> 1.0                      (ilk %3 çekilme tam boy)
    dd >= 0.08           -> 0.0                      (tabanda yeni boy YOK)
    aksi halde           -> round(1 - (dd-0.03)/0.05, 4)   ([%3, %8] arası doğrusal rampa)

HAYATTA KALAN MUTANTLAR VE HÜKÜMLERİ
------------------------------------
x_derisk_mult__mutmut_2  — SINIR SABİTİ: `if peak <= 0` → `if peak <= 1`.
    ÖLDÜRÜLÜR (M2 testleri). Zirvesi 1 birim veya altında olan her hesapta de-risk tamamen
    devre dışı kalırdı: mutant %10 çekilmede bile 1.0 döndürüyor, gerçek kod 0.0.
    Kesirli/küçük ölçekli öz sermaye (birim-normalize backtest, hisse-fiyatı ölçeği, kesir
    hesaplar) bu kapıdan sessizce tam boy geçerdi.

x_derisk_mult__mutmut_23 — YUVARLAMA HANESİ: `round(..., 4)` → `round(..., 5)`.
    ÖLDÜRÜLÜR (M23 testleri). Çarpanın kuantizasyonu sözleşmenin bir parçası: 4 hane, karne ve
    boy hesabında iki tarafın AYNI sayıyı görmesini sağlar. 5 hane, dd=%3.0001'de 1.0 yerine
    0.99998 üretip "tam boy" hükmünü de bozar.

x_derisk_mult__mutmut_7  — EŞDEĞER, ÖLDÜRÜLEMEZ: `if dd <= 0.03` → `if dd < 0.03`.
    GEREKÇE (YASA 4 ruhu, sessiz-yutma değil ISPAT): iki dal yalnız dd == 0.03 TAM noktasında
    ayrışır. O noktada mutant erken dönüşü atlar, ama rampaya düşer ve rampa tam orada
    1.0 - (0.03-0.03)/(0.08-0.03) = 1.0 - 0.0 = 1.0 verir; pay birebir aynı float ifadesinden
    çıktığı için kayan nokta artığı da yok. 0.08 tabanı da aşılmadığından çıktı DEĞİŞMEZ.
    300k rastgele + ızgara taramasında tek bir ayrışan girdi bulunamadı. Test edilmedi;
    sınır yine de test_sinir_dd_yuzde_uc_tam_boy ile ÇİVİLENDİ (ileride rampa formülü
    değişirse bu eşdeğerlik biter ve mutant öldürülebilir hale gelir).

x_derisk_mult__mutmut_10 — EŞDEĞER, ÖLDÜRÜLEMEZ: `if dd >= DERISK_FLOOR_DD` → `if dd > ...`.
    GEREKÇE (YASA 4 ruhu): ayrışma yalnız dd == 0.08 TAM noktasında olabilir. Orada mutant
    rampaya düşer ve rampa 1.0 - (0.08-0.03)/(0.08-0.03) = 1.0 - 1.0 = 0.0 verir; pay ve payda
    birebir aynı float ifadesi olduğu için oran TAM 1.0'dır, artık yoktur. Çıktı gerçek kodla
    özdeş (0.0). Aynı tarama burada da ayrışan girdi bulamadı. Test edilmedi; taban sınırı
    test_sinir_dd_taban_sifir ile çivilendi.

Kalan testler (SINIR/REGRESYON) gerçek kodda yeşildir ve fonksiyonun şekil sözleşmesini
(monotonluk, [0,1] aralığı, zirve üstü davranış, max_positions_at ile tutarlılık) korur.
Fikstür yok: derisk_mult saf fonksiyondur — state'e ne yazar ne okur.
"""
from __future__ import annotations

import pytest

from meridian.broker import DERISK_FLOOR_DD, derisk_mult, max_positions_at


# =================================================================================================
# M2 — `peak <= 0` sınır sabiti (mutmut_2: 0 → 1)
# =================================================================================================
def test_m2_peak_bir_birim_iken_derisk_yine_isler():
    """Zirve 1.0 iken %10 çekilme: taban aşıldı, yeni boy YOK.

    mutant_2 (`peak <= 1`) burada erken 1.0 döndürüp tam boy verirdi — yani küçük ölçekli her
    hesapta de-risk mekanizması tamamen kapalı olurdu."""
    assert derisk_mult(0.90, 1.0) == 0.0
    assert derisk_mult(0.50, 1.0) == 0.0


@pytest.mark.parametrize(
    "equity,peak,beklenen",
    [
        (0.9487655, 1.0, 0.5753),    # dd = %5.12345 → rampanın ortasının biraz üstü
        (0.47438275, 0.5, 0.5753),   # aynı dd, kesirli zirve
        (0.95, 1.0, 0.6),            # dd = %5 → 1 - 0.02/0.05
        (0.0095, 0.01, 0.6),         # sent ölçeği: ölçek çarpanı değil, ORAN belirler
        (0.20, 0.25, 0.0),           # dd = %20 → taban
    ],
)
def test_m2_kucuk_zirvede_rampa_olceklenmez_oranla_calisir(equity, peak, beklenen):
    """derisk_mult ölçekten bağımsızdır: hüküm dd ORANINDAN çıkar, zirvenin mutlak
    büyüklüğünden değil. mutant_2 bu satırların hepsinde 1.0 döndürür."""
    assert derisk_mult(equity, peak) == beklenen


def test_m2_sinir_sifirdir_bir_degil():
    """peak == 0 muafiyetin TAM sınırı; peak > 0 olan her şey (0.5 dahil) ölçülür."""
    assert derisk_mult(0.0, 0.0) == 1.0          # ölçülemeyen zirve → ceza yok
    assert derisk_mult(0.45, 0.5) == 0.0         # ölçülebilir zirve → taban uygulanır
    assert derisk_mult(0.2375, 0.25) == 0.6      # ölçülebilir zirve → rampa uygulanır


def test_m2_kucuk_zirve_pozisyon_sayisi_kapisina_da_tasinir():
    """Çarpan tek başına kalmıyor: max_positions_at aynı sayıyı okuyor. mutant_2 ile küçük
    hesapta hem boy hem eşzamanlı pozisyon tavanı kısılmadan kalırdı."""
    assert max_positions_at(0.90, 1.0, 5) == 0           # taban → hiç yeni pozisyon
    assert max_positions_at(0.9487655, 1.0, 5) == 3      # rampa → 5 * 0.5753 ≈ 3
    assert max_positions_at(1.0, 1.0, 5) == 5            # çekilme yok → tam taban


# =================================================================================================
# M23 — yuvarlama hanesi (mutmut_23: 4 → 5)
# =================================================================================================
@pytest.mark.parametrize(
    "equity,beklenen",
    [
        (948765.5, 0.5753),   # ham 0.57531   → 5 hane olsaydı 0.57531
        (941234.0, 0.4247),   # ham 0.42468   → 5 hane olsaydı 0.42468
        (933333.0, 0.2667),   # ham 0.266659… → 5 hane olsaydı 0.26666
    ],
)
def test_m23_rampa_tam_dort_haneye_kuantize_edilir(equity, beklenen):
    """Çarpan 4 haneye kuantizedir. 5 hane, boy hesabı ile karneyi farklı sayılara oturtur."""
    assert derisk_mult(equity, 1_000_000.0) == beklenen


def test_m23_esigin_hemen_ustunde_tam_boya_yuvarlanir():
    """dd = %3.0001 — kuantizasyon burada ANLAM taşıyor: 4 hanede çarpan TAM 1.0'dır, yani
    "eşiğin bir tık ötesi hâlâ tam boy" hükmü korunur. 5 hane 0.99998 üretip bu hükmü bozardı."""
    assert derisk_mult(969_999.0, 1_000_000.0) == 1.0


@pytest.mark.parametrize("equity", [948765.5, 941234.0, 933333.0, 926000.0, 955555.0, 963210.0])
def test_m23_donen_deger_kendi_dort_hane_yuvarlamasina_esittir(equity):
    """Sınıf düzeyi bekçi: dönen çarpan her zaman kendi 4-hane yuvarlamasına eşit olmalı.
    Hane sayısını büyüten HERHANGİ bir mutasyon (5, 6, None) bu iddiayı kırar."""
    m = derisk_mult(equity, 1_000_000.0)
    assert m == round(m, 4)


# =================================================================================================
# SINIR / REGRESYON — sözleşmenin şekli (eşdeğer ilan edilen 7 ve 10'un sınırları dahil)
# =================================================================================================
def test_sinir_dd_yuzde_uc_tam_boy():
    """dd == %3 TAM sınırında tam boy. (mutmut_7'nin dokunduğu nokta; rampa orada da 1.0
    verdiği için mutant eşdeğer — sınır yine de çivileniyor.)"""
    assert (100.0 - 97.0) / 100.0 == 0.03        # sınırın gerçekten TAM tutulduğunu ispatla
    assert derisk_mult(97.0, 100.0) == 1.0
    assert derisk_mult(97.001, 100.0) == 1.0     # eşiğin içi


def test_sinir_dd_taban_sifir():
    """dd == %8 TAM sınırında yeni boy YOK. (mutmut_10'un dokunduğu nokta; rampa orada da 0.0
    verdiği için mutant eşdeğer.)"""
    assert (100.0 - 92.0) / 100.0 == DERISK_FLOOR_DD
    assert derisk_mult(92.0, 100.0) == 0.0
    assert derisk_mult(90.0, 100.0) == 0.0       # tabanın ötesi de 0.0


def test_taban_hemen_altinda_pozitif_ama_minik():
    """Rampa tabana SIFIRDAN yaklaşır: %7.999 çekilmede çarpan hâlâ > 0, ama neredeyse yok."""
    m = derisk_mult(92.001, 100.0)
    assert m == 0.0002
    assert 0.0 < m < 0.01


def test_peak_pozitif_degilse_carpan_bir():
    """Zirve ölçülemiyorsa (0 veya negatif) ceza yok — ve bölme YAPILMAZ."""
    assert derisk_mult(0.0, 0.0) == 1.0
    assert derisk_mult(50_000.0, 0.0) == 1.0
    assert derisk_mult(50_000.0, -5.0) == 1.0


def test_zirvenin_ustunde_tam_boy():
    """Yeni zirve / zirveye eşit: dd negatif ya da sıfır → tam boy."""
    assert derisk_mult(105_000.0, 100_000.0) == 1.0
    assert derisk_mult(100_000.0, 100_000.0) == 1.0


def test_rampa_orta_noktasi_tam_yarim():
    """[%3, %8] aralığının ortası (%5.5) TAM 0.5 — rampanın doğrusallığının tek-nokta ispatı."""
    assert derisk_mult(94.5, 100.0) == 0.5


def test_rampa_monoton_azalan_ve_sinirlidir():
    """Çekilme derinleştikçe çarpan asla ARTMAZ ve [0, 1] dışına çıkmaz."""
    xs = [100.0 - i * 0.1 for i in range(0, 101)]      # dd: %0 → %10
    vals = [derisk_mult(e, 100.0) for e in xs]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))
    assert vals[0] == 1.0 and vals[-1] == 0.0


def test_max_positions_carpanla_tutarli():
    """Pozisyon tavanı çarpanın türevi: 0 → 0, 1.0 → taban, ara → en az 1."""
    assert max_positions_at(92.0, 100.0, 9) == 0        # taban → hiç
    assert max_positions_at(100.0, 100.0, 7) == 7       # çekilme yok → tam taban
    assert max_positions_at(94.5, 100.0, 1) == 1        # boy varken asla 0'a düşmez
