"""test_mutborc_broker_derisk_mult_v148.py — H5 test-borcu: broker.derisk_mult mutasyon kümesi.

Bu dosya bir "mutasyon borcu" kapatma dosyası: mutmut'ın `meridian.broker.derisk_mult` üzerinde
HAYATTA BIRAKTIĞI 4 mutantı hedefler. derisk_mult, çekilme (drawdown) derinliğine göre YENİ pozisyon
boyunu kısan tek çarpandır; canlıda ve backtest'te aynı yerden okunur. Yani buradaki her sessiz
sapma, gerçek parayla alınan riskin boyunu değiştirir — bu yüzden testler "yaklaşık" değil, SINIR
DEĞERİ ve TAM SAYI iddiaları kurar.

BANT GÜNCELLEMESİ — BEYANLI (2026-08-12, OPT Faz-1 kablolaması): sözleşmenin ŞEKLİ aynı, iki UCU
değişti. Rampa artık gövdede gömülü değil; `broker.derisk_ramp()` goal.yaml `limits.derisk_full_dd`
/ `derisk_floor_dd`den okur ve operatör kararı bandı 0,03/0,08 → 0,15/0,36'ya taşıdı (ölçüm
EDG-2026-023, hüküm karar penceresi §E.1/§E.3). Bu dosyadaki her SAYI yeniden türetildi; her
mutantın hedefi ve gerekçesi DEĞİŞMEDİ (sınır sabiti, yuvarlama hanesi, iki eşdeğer). Aşağıdaki
"%3/%8" geçen eski gerekçe cümleleri yeni banda çevrildi — silinmedi, taşındı.

Sözleşme (meridian/broker.py::derisk_mult; bant goal.yaml `limits`ten):
    peak <= 0            -> 1.0                      (ölçülemeyen zirve cezalandırılmaz)
    dd <= full_dd (0.15) -> 1.0                      (ilk %15 çekilme tam boy)
    dd >= floor_dd(0.36) -> 0.0                      (tabanda yeni boy YOK)
    aksi halde           -> round(1 - (dd-0.15)/0.21, 4)   ([%15, %36] arası doğrusal rampa)

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

x_derisk_mult__mutmut_7  — EŞDEĞER, ÖLDÜRÜLEMEZ: `if dd <= full_dd` → `if dd < full_dd`.
    GEREKÇE (YASA 4 ruhu, sessiz-yutma değil ISPAT): iki dal yalnız dd == full_dd TAM noktasında
    ayrışır. O noktada mutant erken dönüşü atlar, ama rampaya düşer ve rampa tam orada
    1.0 - (full-full)/(floor-full) = 1.0 - 0.0 = 1.0 verir; pay birebir aynı float ifadesinden
    çıktığı için kayan nokta artığı da yok. Taban da aşılmadığından çıktı DEĞİŞMEZ. Argüman
    BANTTAN BAĞIMSIZDIR (0.03/0.08 ile de 0.15/0.36 ile de aynı cebir), yani 2026-08-12 bant
    değişikliği eşdeğerliği bozmadı. Test edilmedi; sınır yine de test_sinir_dd_tam_boy_ucu ile
    ÇİVİLENDİ (ileride rampa FORMÜLÜ değişirse bu eşdeğerlik biter).

x_derisk_mult__mutmut_10 — EŞDEĞER, ÖLDÜRÜLEMEZ: `if dd >= floor_dd` → `if dd > ...`.
    GEREKÇE (YASA 4 ruhu): ayrışma yalnız dd == floor_dd TAM noktasında olabilir. Orada mutant
    rampaya düşer ve rampa 1.0 - (floor-full)/(floor-full) = 1.0 - 1.0 = 0.0 verir; pay ve payda
    birebir aynı float ifadesi olduğu için oran TAM 1.0'dır, artık yoktur. Çıktı gerçek kodla
    özdeş (0.0). Bu argüman da banttan bağımsızdır. Test edilmedi; taban sınırı
    test_sinir_dd_taban_sifir ile çivilendi.

Kalan testler (SINIR/REGRESYON) gerçek kodda yeşildir ve fonksiyonun şekil sözleşmesini
(monotonluk, [0,1] aralığı, zirve üstü davranış, max_positions_at ile tutarlılık) korur.
Fikstür yok: derisk_mult saf fonksiyondur — state'e ne yazar ne okur.
"""
from __future__ import annotations

import pytest

from meridian.broker import DERISK_FLOOR_DD, DERISK_FULL_DD, derisk_mult, max_positions_at


# =================================================================================================
# M2 — `peak <= 0` sınır sabiti (mutmut_2: 0 → 1)
# =================================================================================================
def test_m2_peak_bir_birim_iken_derisk_yine_isler():
    """Zirve 1.0 iken %40 çekilme: taban aşıldı, yeni boy YOK.

    mutant_2 (`peak <= 1`) burada erken 1.0 döndürüp tam boy verirdi — yani küçük ölçekli her
    hesapta de-risk mekanizması tamamen kapalı olurdu.
    (BANT 15/36: eski %10'luk çekilme artık TAM BOY bölgesindedir ve mutantı öldürmezdi —
    bu, sayıların neden yeniden türetildiğinin en net örneği.)"""
    assert derisk_mult(0.60, 1.0) == 0.0
    assert derisk_mult(0.50, 1.0) == 0.0


@pytest.mark.parametrize(
    "equity,peak,beklenen",
    [
        (0.766, 1.0, 0.6),           # dd = %23.4 → 1 - 0.084/0.21
        (0.383, 0.5, 0.6),           # aynı dd, kesirli zirve
        (0.00766, 0.01, 0.6),        # sent ölçeği: ölçek çarpanı değil, ORAN belirler
        (0.80, 1.0, 0.7619),         # dd = %20 → rampanın üst yarısı
        (0.15, 0.25, 0.0),           # dd = %40 → taban
    ],
)
def test_m2_kucuk_zirvede_rampa_olceklenmez_oranla_calisir(equity, peak, beklenen):
    """derisk_mult ölçekten bağımsızdır: hüküm dd ORANINDAN çıkar, zirvenin mutlak
    büyüklüğünden değil. mutant_2 bu satırların hepsinde 1.0 döndürür."""
    assert derisk_mult(equity, peak) == beklenen


def test_m2_sinir_sifirdir_bir_degil():
    """peak == 0 muafiyetin TAM sınırı; peak > 0 olan her şey (0.5 dahil) ölçülür."""
    assert derisk_mult(0.0, 0.0) == 1.0          # ölçülemeyen zirve → ceza yok
    assert derisk_mult(0.30, 0.5) == 0.0         # ölçülebilir zirve → taban uygulanır
    assert derisk_mult(0.1915, 0.25) == 0.6      # ölçülebilir zirve → rampa uygulanır


def test_m2_kucuk_zirve_pozisyon_sayisi_kapisina_da_tasinir():
    """Çarpan tek başına kalmıyor: max_positions_at aynı sayıyı okuyor. mutant_2 ile küçük
    hesapta hem boy hem eşzamanlı pozisyon tavanı kısılmadan kalırdı."""
    assert max_positions_at(0.60, 1.0, 5) == 0           # taban → hiç yeni pozisyon
    assert max_positions_at(0.766, 1.0, 5) == 3          # rampa → 5 * 0.6 = 3
    assert max_positions_at(1.0, 1.0, 5) == 5            # çekilme yok → tam taban


# =================================================================================================
# M23 — yuvarlama hanesi (mutmut_23: 4 → 5)
# =================================================================================================
@pytest.mark.parametrize(
    "equity,beklenen",
    [
        (766666.0, 0.6032),   # ham 0.6031714… → 5 hane olsaydı 0.60317
        (741234.0, 0.4821),   # ham 0.4820666… → 5 hane olsaydı 0.48207
        (733333.0, 0.4444),   # ham 0.4444428… → 5 hane olsaydı 0.44444
    ],
)
def test_m23_rampa_tam_dort_haneye_kuantize_edilir(equity, beklenen):
    """Çarpan 4 haneye kuantizedir. 5 hane, boy hesabı ile karneyi farklı sayılara oturtur."""
    assert derisk_mult(equity, 1_000_000.0) == beklenen


def test_m23_esigin_hemen_ustunde_tam_boya_yuvarlanir():
    """dd = %15.00042 — kuantizasyon burada ANLAM taşıyor: 4 hanede çarpan TAM 1.0'dır, yani
    "eşiğin bir tık ötesi hâlâ tam boy" hükmü korunur. 5 hane 0.99998 üretip bu hükmü bozardı.
    (Eski karşılığı dd=%3.0001'di; yeni bantta aynı 0.99998 ham değerini veren nokta budur.)"""
    assert derisk_mult(849_995.8, 1_000_000.0) == 1.0


@pytest.mark.parametrize("equity", [766666.0, 741234.0, 733333.0, 826000.0, 755555.0, 763210.0])
def test_m23_donen_deger_kendi_dort_hane_yuvarlamasina_esittir(equity):
    """Sınıf düzeyi bekçi: dönen çarpan her zaman kendi 4-hane yuvarlamasına eşit olmalı.
    Hane sayısını büyüten HERHANGİ bir mutasyon (5, 6, None) bu iddiayı kırar."""
    m = derisk_mult(equity, 1_000_000.0)
    assert m == round(m, 4)


# =================================================================================================
# SINIR / REGRESYON — sözleşmenin şekli (eşdeğer ilan edilen 7 ve 10'un sınırları dahil)
# =================================================================================================
def test_sinir_dd_tam_boy_ucu():
    """dd == %15 TAM sınırında tam boy. (mutmut_7'nin dokunduğu nokta; rampa orada da 1.0
    verdiği için mutant eşdeğer — sınır yine de çivileniyor.)
    ESKİ AD: test_sinir_dd_yuzde_uc_tam_boy (bant 3/8 dünyasında %3'tü)."""
    assert (100.0 - 85.0) / 100.0 == DERISK_FULL_DD   # sınırın gerçekten TAM tutulduğunu ispatla
    assert derisk_mult(85.0, 100.0) == 1.0
    assert derisk_mult(85.001, 100.0) == 1.0     # eşiğin içi


def test_sinir_dd_taban_sifir():
    """dd == %36 TAM sınırında yeni boy YOK. (mutmut_10'un dokunduğu nokta; rampa orada da 0.0
    verdiği için mutant eşdeğer.) Bu satır EDG-2026-026 ölçüm şasisinin öz-sınamasıyla BİREBİR
    aynı noktadır (olcum.py:304 `derisk_mult(64.0, 100.0) == 0.0`) — kablo, ölçülen semantiği
    taşıyor mu sorusunun tek-nokta cevabı."""
    assert (100.0 - 64.0) / 100.0 == DERISK_FLOOR_DD
    assert derisk_mult(64.0, 100.0) == 0.0
    assert derisk_mult(60.0, 100.0) == 0.0       # tabanın ötesi de 0.0


def test_taban_hemen_altinda_pozitif_ama_minik():
    """Rampa tabana SIFIRDAN yaklaşır: %35.9958 çekilmede çarpan hâlâ > 0, ama neredeyse yok."""
    m = derisk_mult(64.0042, 100.0)
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
    """[%15, %36] aralığının ortası (%25.5) TAM 0.5 — rampanın doğrusallığının tek-nokta ispatı."""
    assert derisk_mult(74.5, 100.0) == 0.5


def test_rampa_monoton_azalan_ve_sinirlidir():
    """Çekilme derinleştikçe çarpan asla ARTMAZ ve [0, 1] dışına çıkmaz."""
    xs = [100.0 - i * 0.4 for i in range(0, 101)]      # dd: %0 → %40 (üç bölgeyi de geçer)
    vals = [derisk_mult(e, 100.0) for e in xs]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))
    assert vals[0] == 1.0 and vals[-1] == 0.0


def test_max_positions_carpanla_tutarli():
    """Pozisyon tavanı çarpanın türevi: 0 → 0, 1.0 → taban, ara → en az 1."""
    assert max_positions_at(64.0, 100.0, 9) == 0        # taban → hiç
    assert max_positions_at(100.0, 100.0, 7) == 7       # çekilme yok → tam taban
    assert max_positions_at(74.5, 100.0, 1) == 1        # boy varken asla 0'a düşmez
