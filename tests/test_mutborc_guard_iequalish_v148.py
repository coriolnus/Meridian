"""test_mutborc_guard_iequalish_v148.py — H5 TEST-BORCU: guard._equalish mutant kümesi.

NEDEN BU DOSYA VAR: `_equalish` beş satır, ama guard'ın "AYNI AYAR" tanımının TEK uygulaması.
`validate_change` iki ayrı hükmü buradan alır:
  * no-op hükmü        — `old is not None and not reasons and _equalish(old, new, typ)`
  * "zaten denendi"    — defterdeki reddedilmiş hipotezin `new`'i ile önerinin `new`'i aynı mı
Yani "bu düğme zaten bu değerde" ve "bu değer daha önce backtest'te reddedildi" cümlelerinin ikisi
de bu beş satırın verdiği karara dayanır. `mutmut` burada **5 hayatta-kalan mutant** saydı: eşitlik
tanımını bozup hiçbir testin fark etmediği 5 nokta. Eşitlik tanımı YAZILIYDI ama KORUNMUYORDU;
gevşeyen bir tanım (ör. None'ı "eşit" saymak) daha önce hiç denenmemiş bir öneriyi "zaten denendi"
diye reddeder, sıkılaşan bir tanım (ör. int düğmesini float gibi ölçmek) reddedilmiş bir değeri
tekrar tekrar canlıya sunar — ikisi de sessizdir, ikisi de defterde yanlış bir hikâye bırakır.

GERÇEK KOD (meridian/guard.py:211-216):
    if a is None or b is None:
        return False
    if typ == "int":
        return int(a) == int(b)
    return abs(float(a) - float(b)) < 1e-9

HEDEFLENEN MUTASYON SINIFLARI (mutmut numaralarıyla, hepsi `survived` damgalı):
  1  — `a is None or b is None` → `... and ...`   (None NÖBETİ: biri yeter mi, ikisi de mi şart)
  4  — None dalında `return False` → `return True` (BİLİNMEYEN "eşit" mi sayılır)
  6  — `typ == "int"` → `typ == "XXintXX"`         (tip nöbetçisinin dizge literali)
  7  — `typ == "int"` → `typ == "INT"`             (aynı sınıf, BÜYÜK-KÜÇÜK HARF ekseni)
  15 — `< 1e-9` → `<= 1e-9`                        (yakınlık eşiği DIŞLAYICI mı)

TESTLERİN KESKİNLİK KURALI: `_equalish` bool döndürür, bu yüzden her yerde `is True` / `is False`
kullanılır — çıplak `assert _equalish(...)` bir mutant `1` ya da `0.0` döndürse de yeşil kalırdı.
Her sınırın İKİ tarafı yazılır (biraz içerisi + biraz dışarısı): tek taraflı iddia, eşiği kaydıran
mutantı görmez. `_equalish` modül genelinden çağrıldığı için testler `guard._equalish` diye
NİTELENMİŞ erişir (`from ... import _equalish` DEĞİL) — mutant enjeksiyonu ancak böyle ölçülebilir.

6 ve 7 NEDEN "TRUNCATION" DEĞERLERİYLE SINANIYOR: bu iki mutant yalnız int dalı ile float dalı
AYRIŞTIĞINDA görünür. Ayrışma tam olarak iki yerde olur ve testler ikisini de yazar:
  (a) aynı tam-sayı kovası, farklı kesir (1.4 vs 1.6)  → int: EŞİT, float: DEĞİL
  (b) 1e-9'dan yakın ama tam-sayı sınırını aşan çift    → int: DEĞİL, float: EŞİT
Tek yön yazılsaydı mutant "yanlış dala düşme"yi bir tarafta gizleyebilirdi.

15 NEDEN 0.0 vs 1e-9 İLE SINANIYOR: `<` ile `<=` yalnız fark eşiğe TAM EŞİTKEN ayrışır. 2.5+1e-9
gibi bir toplamda fark, 2.5'in ulp'si yüzünden 1e-9'a tam eşit ÇIKMAYABİLİR — o bir yuvarlama
kumarıdır. 0.0 tabanında `abs(0.0 - 1e-9)` kayan noktada 1e-9'un KENDİSİDİR, eşitlik kesindir;
test şansa değil, karşılaştırma işaretinin kendisine bakar. Aynı sebeple entegrasyon (call-site)
testleri 15'i hedeflemez — 15 doğrudan testlerde çivilenir.

ÖLÇÜLEN SONUÇ (iddia değil, ölçüm — 2026-08-01): 5 hayatta-kalan mutantın gövdesi
`mutants/meridian/guard.py`'den tek tek çıkarılıp gerçek modülün ad uzayına
(`meridian.guard._equalish`) enjekte edildi ve bu dosya her biri için pytest ile koşturuldu:
**5/5 ÖLDÜ**. Ölçüm yerel bir koşum düzeneğiyle yapıldı (`mutmut` yeniden koşulmadı; tam mutasyon
turu Rol-1'in tek-otoriter işidir), dolayısıyla resmî mutmut skorunun tazelenmesi hâlâ Rol-1'e ait
bir adımdır.

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: sessiz geçiştirme yok):
  * YOK. Bu kümedeki 5 mutantın hepsi gözlemlenebilir davranış değiştiriyor ve hepsi öldürüldü;
    "eşdeğer" ilan edilen tek bir mutant bile yok. (Diğer 11 `_equalish` mutantı — 2, 3, 5, 8..14,
    16 — mutmut turunda ZATEN ölmüştü, bu dosyanın kapsamı dışındalar; 5 ve 16 buradaki
    testlerce de öldürülür, bu bir yan etki, hedef değil.)

KAPSAM DIŞI (bilerek): `validate_change`'in kendi mutant kümesi
`tests/test_mutborc_guard_validate_change_v148.py`'de, `_on_step`'inki
`tests/test_mutborc_guard_ion_step_v148.py`'de işlenir. Buradaki üç entegrasyon testi o yüzeyleri
sınamak için değil, `_equalish`'in ÇAĞRI YERİNDEKİ etkisini (no-op hükmü ve "zaten denendi" vetosu)
çivilemek için var.

Fikstürler tamamen SENTETİK ve saftır: `_equalish` de `validate_change` de defter/ağ/dosya kanalı
olmayan saf fonksiyonlardır (guard'ın SAF-KALMA yasası), dolayısıyla tmp-state'e bile gerek yok —
canlı `state/` okunmaz, yazılmaz.
"""
from __future__ import annotations

from meridian import guard


# --------------------------------------------------------------------------------------------
# Sentetik fikstürler — canlı bounds.yaml/strategy.yaml OKUNMAZ (saf fonksiyon, saf girdi).
# --------------------------------------------------------------------------------------------
BOUNDS = {
    "entry.min_score": {"min": 50, "max": 100, "step": 1, "type": "int"},
    "exit.profit_target_r": {"min": 2.0, "max": 5.0, "step": 0.25, "type": "float"},
}

PARAMS = {
    "entry.min_score": 62,
    "exit.profit_target_r": 2.5,
}

GOAL = {"max_accepted_changes_per_month": 8}


def _vc(proposal, *, params=None, hypotheses=None, accepted=0):
    """Tek çağrı sarmalayıcı — her testin YALNIZ değiştirdiği eksen okunur kalsın diye."""
    return guard.validate_change(
        proposal,
        dict(PARAMS) if params is None else params,
        dict(BOUNDS),
        dict(GOAL),
        [] if hypotheses is None else hypotheses,
        accepted,
        None,
    )


# ============================================================================================
# A. None NÖBETİ — mutant 1 (or→and) ve 4 (False→True)
# ============================================================================================
def test_e1_tek_taraflı_None_esit_DEGILDIR_ve_kod_COKMEZ():
    """BİLİNMEYEN bir taraf, eşitlik iddiasını imkânsız kılar — ve bunu ÇÖKEREK değil, False
    dönerek yapar. Nöbet `and`'e dönerse (mutant 1) akış int()/float() çağrısına düşer ve
    `int(None)` TypeError atar: guard'ın saf hükmü bir istisnaya dönüşür. `return True` olursa
    (mutant 4) bilinmeyen bir değer "zaten bu ayardasın" diye rapor edilir."""
    assert guard._equalish(None, 5, "int") is False
    assert guard._equalish(5, None, "int") is False
    assert guard._equalish(None, 2.5, "float") is False
    assert guard._equalish(2.5, None, "float") is False


def test_e2_iki_taraf_da_None_ise_de_esit_DEGILDIR():
    """İki bilinmeyen birbirine eşit SAYILMAZ. Bu, deponun "bilinmeyen ≠ tanımlı" yasasının
    (bkz. score.py None sözleşmesi) eşitlik yüzeyindeki karşılığı: None bir değer değil, değerin
    YOKLUĞUdur; iki yokluk aynı ayar demek değildir."""
    assert guard._equalish(None, None, "int") is False
    assert guard._equalish(None, None, "float") is False


def test_e3_None_sifirla_KARISTIRILMAZ():
    """Pozitif kontrol ile birlikte: 0 gerçek bir değerdir ve kendisine eşittir; None değildir.
    Nöbet gevşerse (4) ikisi aynı cevabı verir ve fark kaybolur."""
    assert guard._equalish(None, 0, "int") is False
    assert guard._equalish(0, None, "float") is False
    assert guard._equalish(0, 0, "int") is True
    assert guard._equalish(0.0, 0.0, "float") is True


# ============================================================================================
# B. TİP NÖBETÇİSİNİN DİZGESİ — mutant 6 ("XXintXX") ve 7 ("INT")
# ============================================================================================
def test_e4_int_dugmesinde_ayni_tam_sayi_kovasi_AYNI_AYARDIR():
    """int dalı KIRPAR: aynı tam sayıya kırpılan iki değer, int bir düğme için aynı ayardır.
    Nöbetçi dizgesi bozulursa (6/7) akış float dalına düşer ve 0.2'lik fark "farklı ayar" olur —
    yani guard, aslında hiçbir şeyi değiştirmeyen bir öneriyi gerçek bir değişiklik sanar."""
    assert guard._equalish(1.4, 1.6, "int") is True
    assert guard._equalish(70.4, 70, "int") is True
    assert guard._equalish(-1.4, -1.6, "int") is True      # kırpma SIFIRA doğrudur, aşağı değil
    assert guard._equalish(1.4, 1.6, "float") is False     # aynı çift, float düğmede FARKLI


def test_e5_int_dalinda_tam_sayi_SINIRI_asilirsa_farkli_ayardir():
    """Ters yön: 1e-9'dan yakın ama tam-sayı sınırının iki yanında duran çift. float dalı bunlara
    "eşit" der, int dalı DEMEZ. Nöbetçi dizgesi bozulursa (6/7) 1 ile 2 aynı ayar ilan edilir ve
    gerçek bir eşik değişikliği "no-op" diye reddedilir."""
    assert guard._equalish(1.9999999999, 2.0000000001, "int") is False
    assert guard._equalish(1.9999999999, 2.0000000001, "float") is True


def test_e6_int_dalini_yalniz_TAM_int_dizgesi_secer():
    """Nöbetçinin kendisi: aynı çift (1.4, 1.6) yalnız `typ == "int"` iken True olmalı. Mutant 6
    "XXintXX", mutant 7 "INT" bekler; bu iddia o iki dizgeyle çağrıldığında gerçek kodun False
    dediğini çivileyerek ikisini de kırmızıya düşürür."""
    assert guard._equalish(1.4, 1.6, "int") is True
    assert guard._equalish(1.4, 1.6, "INT") is False
    assert guard._equalish(1.4, 1.6, "Int") is False
    assert guard._equalish(1.4, 1.6, "XXintXX") is False
    assert guard._equalish(1.4, 1.6, "float") is False


# ============================================================================================
# C. YAKINLIK EŞİĞİ — mutant 15 (< → <=)
# ============================================================================================
def test_e7_1e9_esigi_DISLAYICIDIR():
    """Fark TAM 1e-9 iken "eşit değil"; eşiğin hemen altında "eşit". `<` `<=`'ye kayarsa (15) sınır
    değerin kendisi eşitliğe girer ve yakınlık penceresi bir ulp genişler — küçük ama SESSİZ bir
    gevşeme. `abs(0.0 - 1e-9)` kayan noktada tam olarak 1e-9'dur; iddia yuvarlamaya bağlı değil."""
    assert abs(0.0 - 1e-9) == 1e-9                          # ön koşul: sınır TAM temsil ediliyor
    assert guard._equalish(0.0, 1e-9, "float") is False
    assert guard._equalish(0.0, 9.9e-10, "float") is True


def test_e8_esik_iki_yonlu_ve_ISARETTEN_bagimsizdir():
    """abs() yüzünden eşik simetriktir: argüman sırası ve farkın işareti sonucu değiştirmez, ama
    DIŞLAYICILIK her iki yönde de korunur."""
    assert guard._equalish(1e-9, 0.0, "float") is False
    assert guard._equalish(-1e-9, 0.0, "float") is False
    assert guard._equalish(0.0, -1e-9, "float") is False
    assert guard._equalish(-9.9e-10, 0.0, "float") is True


# ============================================================================================
# D. ÇAĞRI YERİ (validate_change) — hükmün DAVRANIŞA dönüştüğü yer
# ============================================================================================
def test_e9_defterdeki_degersiz_hipotez_yeni_bir_oneriyi_VETO_ETMEZ():
    """Defterde `new` alanı olmayan (ya da None yazılmış) reddedilmiş bir hipotez, aynı düğmeye
    gelen HER yeni öneriyi öldürmemeli. Mutant 4 (None → True) tam olarak bunu yapardı: arama
    uzayı, bir tek bozuk defter satırı yüzünden o düğmede kalıcı olarak kapanırdı. Mutant 1 ise
    aynı yolda `int(None)` ile ÇÖKERDİ."""
    hyps = [{"id": "H-bozuk", "variable": "entry.min_score", "new": None,
             "status": "rejected_by_backtest"}]
    v = _vc({"variable": "entry.min_score", "new": 66}, hypotheses=hyps)
    assert v.ok is True
    assert v.reasons == []


def test_e10_daha_once_reddedilen_deger_defterde_KESIRLI_yazilsa_da_veto_eder():
    """int bir düğmede 66.4 ile 66 AYNI ayardır; defter hangi biçimde yazmış olursa olsun aynı
    değeri ikinci kez canlıya süremeyiz. Nöbetçi dizgesi bozulursa (6/7) karşılaştırma float
    dalına düşer, 0.4'lük fark "yeni bir fikir" sayılır ve reddedilmiş bir değer geri döner."""
    hyps = [{"id": "H-7", "variable": "entry.min_score", "new": 66.4,
             "status": "rejected_by_backtest"}]
    v = _vc({"variable": "entry.min_score", "new": 66}, hypotheses=hyps)
    assert v.ok is False
    assert any("already tried and failed" in r for r in v.reasons)


def test_e11_noop_hukmu_int_dugmesinde_TAM_SAYI_KOVASINA_bakar():
    """Canlı param 62.4 yazılıysa, 62 önerisi gerçek bir değişiklik DEĞİLDİR — int düğmede ikisi
    de 62'dir. 6/7 float dalına düşürseydi guard bu boş öneriyi onaylar, ship yolu hiçbir şeyi
    değiştirmeyen bir 'kabul' kaydeder ve aylık kota boşa harcanırdı."""
    v = _vc({"variable": "entry.min_score", "new": 62}, params={"entry.min_score": 62.4})
    assert v.ok is False
    assert any("no-op" in r for r in v.reasons)

    # karşı taraf: gerçekten farklı bir kova = gerçek değişiklik
    v2 = _vc({"variable": "entry.min_score", "new": 63}, params={"entry.min_score": 62.4})
    assert v2.ok is True
    assert v2.reasons == []


def test_e12_float_dugmesinde_noop_hukmu_ayni_degeri_yakalar_farkliyi_birakir():
    """float çağrı yerinin pozitif/negatif kontrolü: aynı değer no-op, bir adım ötesi değil.
    (15'in sınır ayrışması burada ölçülmez — call-site'ta fark 1e-9'a TAM eşitlenemez; o iddia
    doğrudan testlerde, 0.0 tabanında yapılır.)"""
    v = _vc({"variable": "exit.profit_target_r", "new": 2.5})
    assert v.ok is False
    assert any("no-op" in r for r in v.reasons)

    v2 = _vc({"variable": "exit.profit_target_r", "new": 2.75})
    assert v2.ok is True
    assert v2.reasons == []
