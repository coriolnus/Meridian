"""test_mutborc_broker_entry_limit_price_v148.py — H5 TEST-BORCU: `broker.entry_limit_price`.

NEDEN: Bu fonksiyon giriş-icra yasasının 1. maddesinin TEK hesabıdır — İKİ motor da (iç
`PaperBroker.fill_entry` ve ayna `entry_order_decision` → Alpaca bracket) ödedikleri tavanı
buradan alır. Mutasyon taraması 6 mutantın HAYATTA kaldığını gösterdi: yani kapı eşiği kayabilir,
geçersiz-tetik dönüşü 0.0'dan 1.0'a çıkabilir ya da biçimsiz ATR'nin varsayılanı 0.0'dan 1.0'a
kayabilir ve suite YEŞİL kalırdı. Sonucu "test kırılır" değildir; sonucu "ajan hiç var olmayan bir
tetikten 1.01 dolar limitle emir yazar" ya da "ölçülemeyen ATR sessizce 1.0 sayılıp tavanı
yarıya indirir"dir — ikisi de UYDURMA YASAĞI ihlalidir, çünkü ölçülmemiş bir sayı hesaba girer.

Kaynak fonksiyon: meridian/broker.py::entry_limit_price
Mutant gövdeleri : mutants/meridian/broker.py::x_entry_limit_price__mutmut_N

------------------------------------------------------------------------------------------------
HAYATTA KALAN 6 MUTANT → HEDEFLENEN SINIFLAR (6/6 kapatıldı)
------------------------------------------------------------------------------------------------
 M1  sabit-yutan tetik   :  6 `float(trigger or 0.0)` → `float(trigger or 1.0)`
                            → A1 (falsy tetik 1.0 uydurulunca 0.0 yerine 1.01 döner)
 M2  kapı EŞİĞİ kayar    :  7 `if t <= 0` → `if t < 0`   → A3
                            8 `if t <= 0` → `if t <= 1`  → B1, B2 (1 doların altı + tam 1.00 SINIR)
 M3  geçersiz-tetik      :  9 `return 0.0` → `return 1.0` → A1, A2
     dönüşü sabit değişir
 M4  biçimsiz ATR'nin    : 19 `except: a = 0.0` → `a = None` (sonra `a > 0` TypeError atar)
     sessiz-yutma        : 20 `except: a = 0.0` → `a = 1.0` (ölçülemeyen ATR 1.0 UYDURULUR)
     varsayılanı bozulur   → C1, C2

------------------------------------------------------------------------------------------------
EŞDEĞER — ÖLDÜRÜLEMEZ: YOK. Ama 7 için ŞERH (YASA 4 ruhu: yutulan hiçbir şey sessiz kalmaz)
------------------------------------------------------------------------------------------------
 7  `t <= 0` → `t < 0`: DÖNEN DEĞER bakımından eşdeğerdir. t == 0'da mutant kapıdan geçer ama
    hesabın tamamı t ile çarpıldığı için yine 0.0 üretir (pct_off = 0·cap = 0, off = min(mult·a, 0)
    = 0 → 0 + 0 = 0.0). Öldürülebildiği TEK gözlenebilir kanal, kapının YASAYI OKUMADAN dönmesidir:
    orijinal `cfg["limit_pct_cap"]`e hiç dokunmaz, mutant dokunur. A3 tam olarak bunu sınar ve bu
    UYDURMA bir sözleşme değildir — geçersiz tetik yasa uygulanmadan elenmelidir; yarım bir yasa
    sözlüğüyle çağrılan sıfır tetik KeyError'a dönüşmemelidir (`fill_entry`/ayna yollarının ikisi de
    cfg'yi dışarıdan geçiriyor: broker.py:136 ve broker.py:334).

Fikstür sözleşmesi: hiçbir test canlı `state/`e YAZMAZ ve `goal.yaml` OKUMAZ — her çağrı cfg'yi
açıkça geçer. Limit hesabının sonucu dosyanın o günkü içeriğine bağlı olmamalıdır (yasanın kendi
okunması `test_mutborc_broker_entry_law_v148.py`nin işi).
"""
from __future__ import annotations

import pytest

from meridian import broker as BR


# kart grid'inin VARSAYILAN noktası — açıkça geçilir ki test goal.yaml'a bağlı olmasın
LAW = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01,
       "gap_behavior": "marketable_limit", "tif": "day", "version": "E1-v1"}


class _CasusYasa(dict):
    """Okunan anahtarları kaydeden yasa sözlüğü. `dict` alt sınıfı ve DOLU olduğu için
    `cfg = cfg or entry_law()` satırında yerinde kalır (boş sözlük falsy olup düşerdi)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.okunan: list = []

    def __getitem__(self, key):
        self.okunan.append(key)
        return super().__getitem__(key)


# ===================== A — geçersiz tetik kapısı (mutant 6, 7, 9) ================================

def test_a1_falsy_tetik_sifir_doner_uydurulmaz():
    """M1(6) + M3(9): tetik yoksa/sıfırsa dönüş 0.0'dır — "ölçülemedi" hâli. `trigger or 1.0`
    sessizce 1 dolarlık bir tetik UYDURUR ve fonksiyon 1.01 döner; çağıran taraf bunu geçerli bir
    limit sanıp emir yazar. `return 1.0` aynı yalanı kapının içinden söyler."""
    for tetik in (0.0, 0, None, "", False):
        assert BR.entry_limit_price(tetik, None, LAW) == 0.0
        assert BR.entry_limit_price(tetik, 12.0, LAW) == 0.0   # ATR ölçülmüş olsa bile


def test_a2_negatif_tetik_sifir_doner():
    """M3(9): negatif tetik de geçersizdir ve 0.0 döner — 1.0 gibi 'makul görünen' bir sabit
    dönseydi, negatif tetikli bozuk bir sinyal canlı yolda 1.01'lik gerçek bir limite dönüşürdü."""
    for tetik in (-0.01, -3.5, -1e9, "-2.5"):
        assert BR.entry_limit_price(tetik, None, LAW) == 0.0
        assert BR.entry_limit_price(tetik, 12.0, LAW) == 0.0


def test_a3_gecersiz_tetik_yasayi_hic_okumadan_elenir():
    """M2(7): kapı `t <= 0`, `t < 0` DEĞİL. t == 0'da dönen sayı iki yolda da 0.0 olduğu için
    (bkz. dosya başındaki şerh) tek gözlenebilir fark budur: orijinal kapı yasaya HİÇ dokunmadan
    döner. Sözleşme: geçersiz tetik yasa uygulanmadan elenir; yarım bir yasa sözlüğü sıfır tetiği
    KeyError'a çeviremez."""
    casus = _CasusYasa(LAW)
    assert BR.entry_limit_price(0.0, 12.0, casus) == 0.0
    assert casus.okunan == []                       # tek bir alan bile okunmadı

    casus2 = _CasusYasa(LAW)
    assert BR.entry_limit_price(-5.0, 12.0, casus2) == 0.0
    assert casus2.okunan == []

    # aynı hüküm değer tarafından: `limit_pct_cap` içermeyen YARIM yasa patlatmamalı
    yarim = {"limit_atr_mult": 0.5}
    assert BR.entry_limit_price(0.0, 12.0, yarim) == 0.0

    # karşı-kontrol: GEÇERLİ tetikte yasa GERÇEKTEN okunuyor (testin ayırt ediciliği)
    casus3 = _CasusYasa(LAW)
    assert BR.entry_limit_price(100.0, None, casus3) == pytest.approx(101.0)
    assert "limit_pct_cap" in casus3.okunan


# ===================== B — düşük fiyatlı tetik / kapı sınırı (mutant 8) ==========================

def test_b1_bir_dolarin_altindaki_tetik_de_limit_uretir():
    """M2(8): kapı `t <= 1`e kaysaydı 1 doların altındaki HER tetik sessizce 0.0 döndürürdü —
    yani limit 'yok' sayılır, emir ya hiç gitmez ya da tavansız yazılır. Evrende ucuz sembol
    bugün olmasa bile kapı fiyat seviyesine göre değil GEÇERLİLİĞE göre kararını verir."""
    assert BR.entry_limit_price(0.80, None, LAW) == pytest.approx(0.808)
    assert BR.entry_limit_price(0.25, None, LAW) == pytest.approx(0.2525)
    # ATR dalı da aynı rejimde çalışır: min(0.5·0.02, 0.5·%1) = 0.005
    assert BR.entry_limit_price(0.50, 0.02, LAW) == pytest.approx(0.505)


def test_b2_tetik_tam_bir_dolar_sinir_degeri():
    """M2(8) SINIR: `t <= 1` mutantı tam 1.00'ı da yutar. Sınırın iki yakası da sabitlenir."""
    assert BR.entry_limit_price(1.0, None, LAW) == pytest.approx(1.01)
    assert BR.entry_limit_price(0.999999, None, LAW) == pytest.approx(1.00999899)
    assert BR.entry_limit_price(1.000001, None, LAW) == pytest.approx(1.01000101)


# ===================== C — biçimsiz ATR'nin sessiz-yutma varsayılanı (19, 20) ====================

BICIMSIZ_ATR = ("abc", "n/a", "", [], {}, object(), complex(1, 2))


def test_c1_bicimsiz_atr_olculemedi_demektir_yuzde_tavani_baglar():
    """M4(19, 20): biçimsiz ATR = ÖLÇÜLEMEDİ. Sözleşme a = 0.0'dır, yani ATR dalı hiç açılmaz ve
    yalnız yüzde tavanı bağlar (satıra `offset_kaynak = pct_cap(atr_olculemedi)` yazılır).
      - 19 (`a = None`): fonksiyon `a > 0` karşılaştırmasında TypeError atar — ölçülemeyen ATR
        limit hesabını çökertemez, o yüzden 'istisna yok' da hükmün parçası.
      - 20 (`a = 1.0`): ÖLÇÜLMEMİŞ bir ATR uydurulur. t=100'de tavanı 1.00'dan 0.50'ye indirir;
        limit sessizce sıkışır ve dolmayan emir 'piyasa kaçtı' diye okunur. UYDURMA YASAĞI."""
    for kotu in BICIMSIZ_ATR:
        assert BR.entry_limit_price(100.0, kotu, LAW) == pytest.approx(101.0)
        assert BR.entry_limit_price(200.0, kotu, LAW) == pytest.approx(202.0)


def test_c2_bicimsiz_atr_ile_hic_verilmemis_atr_ayni_yola_duser():
    """Sözleşmenin ikinci yarısı: 'biçimsiz' ile 'hiç verilmemiş' AYNI daldır (ikisi de ölçülemedi).
    20 bu eşitliği bozar (None → 101.0, "abc" → 100.5). Karşı-kontrol olarak ÖLÇÜLMÜŞ küçük bir ATR
    farklı — daha sıkı — bir limit vermeli; yoksa test 'her şey pct_cap' diye de geçerdi."""
    for tetik in (50.0, 100.0, 137.42):
        olculemedi = BR.entry_limit_price(tetik, None, LAW)
        for kotu in BICIMSIZ_ATR:
            assert BR.entry_limit_price(tetik, kotu, LAW) == pytest.approx(olculemedi)
    # ölçülmüş ATR gerçekten başka bir sayı üretiyor (0.5·0.4 = 0.20 < %1·100 = 1.00)
    assert BR.entry_limit_price(100.0, 0.4, LAW) == pytest.approx(100.2)


# ===================== D — yasanın 1. maddesi (çapa; iki tavanın sıkısı bağlar) ==================

def test_d1_iki_tavandan_DAHA_SIKI_olan_baglar():
    """Çapa testi: limit = tetik + min(mult·ATR, cap·tetik). Yukarıdaki C testlerinin ayırt edici
    olması bu kuralın yürürlükte olmasına dayanıyor; kural burada açıkça yazılı."""
    assert BR.entry_limit_price(100.0, 1.0, LAW) == pytest.approx(100.5)    # ATR bağlar
    assert BR.entry_limit_price(100.0, 10.0, LAW) == pytest.approx(101.0)   # yüzde tavanı bağlar
    assert BR.entry_limit_price(100.0, 2.0, LAW) == pytest.approx(101.0)    # SINIR: ikisi eşit


def test_d2_sifir_ve_negatif_atr_olcumsuz_sayilir():
    """a > 0 kapısı: 0.0 ya da negatif ATR bir ölçüm değildir; ATR dalı açılmaz, yüzde tavanı
    bağlar. (Negatif ATR dalı açılsaydı off negatif olur, limit TETİĞİN ALTINA inerdi.)"""
    for atr in (0.0, 0, -0.5, -12.0):
        assert BR.entry_limit_price(100.0, atr, LAW) == pytest.approx(101.0)
