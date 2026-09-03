"""test_mutborc_guard_ion_step_v148.py — H5 TEST-BORCU: guard._on_step mutant kümesi.

NEDEN BU DOSYA VAR: `_on_step` beş satırlık bir fonksiyon, ama guard'ın ADIM IZGARASI yasasının
TEK uygulaması. Hem `composite_shape_reasons` hem `validate_change` adım hükmünü buradan alır —
yani bounds.yaml'daki `step` alanının anlamı bu beş satırda yaşıyor. `mutmut` burada **8
hayatta-kalan mutant** saydı: kodu bozup hiçbir testin fark etmediği 8 nokta. Izgara yasası
YAZILIYDI ama KORUNMUYORDU; adım denetimini sessizce gevşeten bir değişiklik (ör. varsayılan
toleransın 1e-6 yerine ~1.0 olması) ızgara DIŞI her değeri "adım üstünde" ilan ederdi ve arama
uzayı sessizce sürekliye dönerdi.

GERÇEK KOD (guard.py::_on_step):
    k = round((new - lo) / step)
    nearest = lo + k * step
    if typ == "int":
        return abs(nearest - new) < tol and float(new).is_integer()
    return abs(nearest - new) <= tol * max(1.0, abs(step))

HEDEFLENEN MUTASYON SINIFLARI (mutmut numaralarıyla, hepsi `survived` damgalı):
  1  — varsayılan `tol=1e-6` → `tol=1.000001`   (TOLERANS BÜYÜKLÜĞÜ: mikro mu, birim mi)
  10 — `typ == "int"` → `typ == "XXintXX"`      (tip nöbetçisinin dizge literali)
  11 — `typ == "int"` → `typ == "INT"`          (aynı sınıf, BÜYÜK-KÜÇÜK HARF ekseni)
  12 — int dalında `and` → `or`                 (iki koşul da ŞART mı, biri yeter mi)
  15 — int dalında `<` → `<=`                   (tolerans sınırı DIŞLAYICI mı)
  19 — float dalında `<=` → `<`                 (tolerans sınırı KAPSAYICI mı)
  20 — `tol * max(...)` → `tol / max(...)`      (tolerans adımla ÇARPILIR mı, bölünür mü)
  25 — `max(1.0, |step|)` → `max(2.0, |step|)`  (ölçek TABANI 1.0)

TESTLERİN KESKİNLİK KURALI: `_on_step` bool döndürür, bu yüzden her yerde `is True` / `is False`
kullanılır — `assert _on_step(...)` bir mutant `1` ya da `0.0` döndürse de yeşil kalırdı. Ayrıca her
sınırın İKİ tarafı da yazılır (biraz içerisi + biraz dışarısı): tek taraflı bir iddia eşiği kaydıran
mutantı görmez.

TOLERANS SINIRLARI NEDEN `tol` AÇIKÇA VERİLEREK SINANIYOR: 15 ve 19 yalnız `abs(nearest-new)`
eşiğe TAM EŞİTKEN ayrışır. 1e-6 ile tam eşitliği kayan noktada yakalamak yuvarlama kumarıdır; 0.5
gibi ikilik tabanda TAM temsil edilen bir tolerans verilince eşitlik kesindir ve test kayan-nokta
şansına değil, karşılaştırma işaretinin kendisine bakar.

ÖLÇÜLEN SONUÇ (iddia değil, ölçüm — 2026-08-01): 8 hayatta-kalan mutantın gövdesi
`mutants/meridian/guard.py`'den tek tek çıkarılıp gerçek modülün ad uzayına (`meridian.guard._on_step`)
enjekte edildi ve bu dosya her biri için pytest ile koşturuldu: **8/8 ÖLDÜ**. Ölçüm yerel bir koşum
düzeneğiyle yapıldı (`mutmut` yeniden koşulmadı; tam mutasyon turu Rol-1'in tek-otoriter işidir),
dolayısıyla resmî mutmut skorunun tazelenmesi hâlâ Rol-1'e ait bir adımdır.

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: sessiz geçiştirme yok):
  * YOK. Bu kümedeki 8 mutantın hepsi gözlemlenebilir davranış değiştiriyor ve hepsi öldürüldü;
    "eşdeğer" ilan edilen tek bir mutant bile yok. (Diğer 18 `_on_step` mutantı — 2..9, 13, 14, 16,
    17, 18, 21..24, 26 — mutmut turunda ZATEN ölmüştü, bu dosyanın kapsamı dışındalar.)

KAPSAM DIŞI (bilerek): `validate_change` ve `composite_shape_reasons`'ın kendi mutant kümeleri
`tests/test_mutborc_guard_validate_change_v148.py`'de işlenir. Buradaki iki entegrasyon testi o
yüzeyleri sınamak için değil, `_on_step`'in ÇAĞRI YERİNDEKİ etkisini (b.get("type") ve bounds'tan
gelen step) çivilemek için var.

Fikstürler tamamen SENTETİK ve saftır: `_on_step` de `composite_shape_reasons` da defter/ağ/dosya
kanalı olmayan saf fonksiyonlardır (guard'ın SAF-KALMA yasası), dolayısıyla tmp-state'e bile gerek
yok — canlı `state/` okunmaz, yazılmaz.
"""
from __future__ import annotations

from meridian import guard


# --------------------------------------------------------------------------------------------
# SENTETİK FİKSTÜRLER — gerçek bounds.yaml'ın ŞEKLİNİ taklit eder, DEĞERLERİNİ değil.
# `sentetik.yarim_izgara` bilerek uydurma bir düğmedir: adım ızgarasının TAM SAYI hükmüyle
# ayrıştığı bölgeyi (int tipli bir düğmenin ızgarasına 1.5 düşmesi) sınamak için var; adı
# "sentetik." önekiyle o niyeti beyan eder.
# --------------------------------------------------------------------------------------------
BOUNDS = {
    "entry.min_score": {"min": 50, "max": 100, "step": 1, "type": "int"},
    "exit.profit_target_r": {"min": 2.0, "max": 5.0, "step": 0.25, "type": "float"},
    "sentetik.yarim_izgara": {"min": 0, "max": 10, "step": 0.5, "type": "int"},
}

GOAL = {"max_accepted_changes_per_month": 8}


def _step(new, lo, step, typ, *tol):
    """Modül ÜZERİNDEN çağrı — `from ... import _on_step` yapılsaydı mutasyon enjeksiyonu
    (ve gelecekteki bir monkeypatch) testleri hiç görmezdi; ad çözümü çağrı anında olmalı."""
    return guard._on_step(new, lo, step, typ, *tol)


# ============================================================================================
# SINIF 1 — VARSAYILAN TOLERANS MİKRO OLMAK ZORUNDA (`tol=1e-6`)
# ============================================================================================
def test_s1_float_dalinda_varsayilan_tolerans_izgara_disi_degeri_GECIRMEZ():
    """Sınıf 1 (`tol=1e-6` → `tol=1.000001`).

    Yasa: `step` bir ızgaradır, bir öneri değil. min=0.0, step=0.2 ızgarasında 0.3 YOK; en yakın
    ızgara noktası 0.2 ve uzaklık 0.1. Varsayılan tolerans birim mertebesine çıkarsa bu 0.1'lik
    sapma "adım üstünde" sayılır — yani bounds.yaml'daki step alanı hiçbir şey kısıtlamaz olur.

    Sınırın iki tarafı: 0.2 (ızgara noktası) GEÇER, 0.3 (ızgara dışı) GEÇMEZ. Tek taraflı bir
    iddia (yalnız "0.2 geçer") toleransı büyüten mutantı göremezdi.
    """
    assert _step(0.2, 0.0, 0.2, "float") is True
    assert _step(0.3, 0.0, 0.2, "float") is False


def test_s1b_int_dalinda_da_varsayilan_tolerans_MIKRO():
    """Sınıf 1 (int dalı) + sınıf 12 (`and` → `or`).

    min=0, step=2 ızgarası {0, 2, 4, ...}; 3 TAM SAYI ama ızgara noktası DEĞİL. Varsayılan tolerans
    büyürse 3 ile 4 arasındaki 1.0 uzaklık toleransın altına düşer ve 3 kabul edilir. Aynı örnek
    `or` mutantını da düşürür: `float(3.0).is_integer()` True olduğu için `or` altında ızgara
    koşulu tamamen ANLAMSIZLAŞIR — int tipli her tam sayı adımdan bağımsız geçerdi.
    """
    assert _step(4.0, 0.0, 2.0, "int") is True
    assert _step(3.0, 0.0, 2.0, "int") is False


# ============================================================================================
# SINIF 10 / 11 / 12 — TİP NÖBETÇİSİ VE İKİ KOŞULUN BİRLİKTELİĞİ
# ============================================================================================
def test_s10_s11_s12_int_tipinde_IZGARA_YETMEZ_tam_sayi_da_sart():
    """Sınıf 10 (`"int"` → `"XXintXX"`), 11 (`"int"` → `"INT"`), 12 (`and` → `or`).

    Bu, iki dalın davranışının ayrıştığı TEK bölgedir ve tam da bu yüzden keskindir: 1.5 değeri
    min=0.0, step=0.5 ızgarasının ÜSTÜNDEDİR (uzaklık 0.0), ama TAM SAYI değildir.
      * gerçek kod, typ="int" → ızgara ✔ + tam sayı ✘ → False
      * typ="float" → yalnız ızgara sorulur → True
    Tip nöbetçisi bozulursa (10, 11) int tipli düğme sessizce float dalına düşer ve 1.5 geçer;
    `and` → `or` olursa (12) ızgara koşulu tek başına yeterli olur ve yine geçer. Üç mutant da
    ilk iddiayı True'ya çevirir.
    """
    assert _step(1.5, 0.0, 0.5, "int") is False
    assert _step(1.5, 0.0, 0.5, "float") is True
    assert _step(2.0, 0.0, 0.5, "int") is True      # ızgara ✔ + tam sayı ✔ → geçer


def test_s11_tip_nobetcisi_TAM_dizge_int_olmali_buyuk_harf_TETIKLEMEZ():
    """Sınıf 11 (`"int"` → `"INT"`) — dizge literalinin BÜYÜK-KÜÇÜK HARF ekseni.

    bounds.yaml sözleşmesinde tip adı küçük harf "int"tir. Nöbetçi "INT"e kayarsa, bugün hiçbir
    düğme int hükmüne uğramaz (10'la aynı sonuç) AMA yarın biri bounds'a "INT" yazarsa sessizce
    tam-sayı kısıtı UYGULANIR — iki yönlü bir sürüklenme. Test iki yönü de çiviler: yalnız tam
    olarak "int" dizgesi tam-sayı hükmünü açar; "INT", "Int", "integer" ve None açmaz.
    """
    assert _step(1.5, 0.0, 0.5, "int") is False
    for takma_tip in ("INT", "Int", "integer", "float", None):
        assert _step(1.5, 0.0, 0.5, takma_tip) is True, f"tip nöbetçisi {takma_tip!r} ile tetiklendi"


def test_s12_int_dalinda_TAM_SAYI_kosulu_tek_basina_yetmez():
    """Sınıf 12 (`and` → `or`) — koşulun DİĞER yönü.

    Üstteki test "ızgara ✔ / tam sayı ✘" yönünü kapatıyor; bu test "ızgara ✘ / tam sayı ✔"
    yönünü kapatır. min=0.5, step=1.0 ızgarası {0.5, 1.5, 2.5, ...}; 2 tam sayıdır ama ızgarada
    değildir (en yakın nokta 2.5, uzaklık 0.5). `or` altında tam-sayı olmak tek başına yeterdi.
    """
    assert _step(2.0, 0.5, 1.0, "int") is False
    assert _step(3.0, 1.0, 1.0, "int") is True     # kontrol: ızgara ✔ + tam sayı ✔


# ============================================================================================
# SINIF 15 / 19 — TOLERANS SINIRININ İŞARETİ (int dalı DIŞLAYICI, float dalı KAPSAYICI)
# ============================================================================================
def test_s15_int_dalinda_tolerans_siniri_DISLAYICI_kalir():
    """Sınıf 15 (int dalında `<` → `<=`).

    Bu mutant yalnız uzaklık toleransa TAM EŞİTKEN görünür. Bu yüzden tolerans açıkça 0.5 verilir
    (ikilik tabanda tam temsil edilir; 1e-6 ile tam eşitlik kayan-nokta kumarı olurdu):
    min=0.5, step=2.0 ızgarasında en yakın nokta 2.5, new=2.0 → uzaklık TAM 0.5.
      * gerçek kod: 0.5 < 0.5 → False (sınır dışarıda kalır)
      * mutant 15:  0.5 <= 0.5 → True (sınır içeri alınır)
    Kontrol iddiası toleransın biraz üstünde (0.51) değerin GEÇTİĞİNİ gösterir — yani test
    "her şey False" diye ucuza yeşil olmuyor, gerçekten sınırın işaretine bakıyor.
    """
    assert _step(2.0, 0.5, 2.0, "int", 0.5) is False
    assert _step(2.0, 0.5, 2.0, "int", 0.51) is True


def test_s19_float_dalinda_tolerans_siniri_KAPSAYICI_kalir():
    """Sınıf 19 (float dalında `<=` → `<`) — 15'in AYNADAKİ tersi.

    İki dal bilerek farklı işaret taşır ve bu fark ölçülmeden duruyordu. min=0.0, step=1.0,
    new=0.5 → en yakın ızgara noktasına uzaklık TAM 0.5; tol=0.5 ve max(1.0, |1.0|)=1.0 olduğu
    için eşik de TAM 0.5.
      * gerçek kod: 0.5 <= 0.5 → True (sınır İÇERİDE)
      * mutant 19:  0.5 <  0.5 → False
    Kontrol: eşik 0.49'a çekilince aynı değer düşer — sınır gerçekten burada.
    """
    assert _step(0.5, 0.0, 1.0, "float", 0.5) is True
    assert _step(0.5, 0.0, 1.0, "float", 0.49) is False


# ============================================================================================
# SINIF 20 / 25 — TOLERANSIN ADIMLA ÖLÇEKLENMESİ
# ============================================================================================
def test_s20_tolerans_adimla_CARPILIR_bolunmez():
    """Sınıf 20 (`tol * max(1.0, |step|)` → `tol / max(1.0, |step|)`).

    Ölçekleme kaba adımlarda kayan-nokta birikimini soğurmak için var: step=10 iken eşik
    1e-6*10 = 1e-5 olmalı. Bölmeye dönerse eşik 1e-7'ye DÜŞER — yani kaba ızgaralı düğmeler
    (büyük step) toplama hatası yüzünden kendi ızgara noktalarında bile reddedilmeye başlar.
    new=10.000005 → uzaklık 5e-6: gerçek eşiğin (1e-5) altında, mutant eşiğin (1e-7) üstünde.
    Kontrol: 2e-5'lik sapma gerçek kodda da REDDEDİLİR — ölçekleme toleransı sınırsız açmıyor.
    """
    assert _step(10.000005, 0.0, 10.0, "float") is True
    assert _step(10.00002, 0.0, 10.0, "float") is False


def test_s25_olcek_TABANI_birdir_kucuk_adimda_tolerans_buyumez():
    """Sınıf 25 (`max(1.0, |step|)` → `max(2.0, |step|)`).

    Taban 1.0'dır: adım 1'den küçükken tolerans ölçeklenmez, çıplak `tol` kalır. Taban 2.0'a
    kayarsa ince ızgaralı düğmelerde (step=0.5 gibi — gerçek bounds.yaml'da exit.trail_atr tam
    olarak böyle) tolerans SESSİZCE İKİYE KATLANIR ve ızgara dışı değerler kabul edilmeye başlar.
    new=0.5000015 → uzaklık 1.5e-6: gerçek eşiğin (1e-6) üstünde, mutant eşiğin (2e-6) altında.
    Kontrol: 5e-7'lik sapma gerçek kodda GEÇER — yani mikro tolerans hâlâ var, mesele büyüklüğü.
    """
    assert _step(0.5000015, 0.0, 0.5, "float") is False
    assert _step(0.5000005, 0.0, 0.5, "float") is True


# ============================================================================================
# ÇAĞRI YERİ — `_on_step`'in guard yüzeylerindeki GÖZLENEBİLİR etkisi
# (bu üç test aynı sınıfları bounds.yaml şeklindeki gerçek argümanlarla bir kez daha çiviler)
# ============================================================================================
def test_cy1_bilesik_int_dugme_izgaraya_otursa_bile_ONDALIK_ise_reddedilir():
    """Sınıf 10, 11, 12 — çağrı yerinde (`composite_shape_reasons` → `b.get("type")`).

    `sentetik.yarim_izgara` int tipli ama adımı 0.5: 1.5 ızgarada OTURUYOR, yine de tam sayı
    olmadığı için düşmeli. Tip nöbetçisi ya da `and` bozulursa bu düğme sessizce kuyruğa girer.
    """
    nedenler = guard.composite_shape_reasons(
        {"sentetik.yarim_izgara": 1.5, "entry.min_score": 60}, BOUNDS)
    assert any("sentetik.yarim_izgara" in n and "adım üstünde değil" in n for n in nedenler), nedenler
    assert not any("entry.min_score" in n for n in nedenler), nedenler   # geçerli düğme temiz kalmalı


def test_cy2_bilesik_float_dugme_izgara_disi_degeri_reddedilir():
    """Sınıf 1 — çağrı yerinde. step=0.25 ızgarasında 2.3 yok (en yakın 2.25, uzaklık 0.05).
    Varsayılan tolerans büyürse bu sapma yutulur ve bileşik demet ŞEKİL hükmünü geçer."""
    nedenler = guard.composite_shape_reasons(
        {"exit.profit_target_r": 2.3, "entry.min_score": 60}, BOUNDS)
    assert any("exit.profit_target_r" in n and "adım üstünde değil" in n for n in nedenler), nedenler
    assert guard.composite_shape_reasons(
        {"exit.profit_target_r": 2.25, "entry.min_score": 60}, BOUNDS) == []   # ızgara noktası temiz


def test_cy3_validate_change_izgara_disi_oneriyi_GEREKCESIYLE_dusurur():
    """Sınıf 1 — en dış yüzeyde. Adım hükmü `validate_change`'in tek kullanıcıya dönük çıktısıdır;
    tolerans gevşerse burada ok=True'ya döner, yani ızgara dışı bir değer CANLIYA aday olur."""
    v = guard.validate_change({"variable": "exit.profit_target_r", "new": 2.3},
                              {"exit.profit_target_r": 2.5}, BOUNDS, GOAL, [], 0)
    assert v.ok is False
    assert any("off-step" in r for r in v.reasons), v.reasons
    temiz = guard.validate_change({"variable": "exit.profit_target_r", "new": 2.25},
                                  {"exit.profit_target_r": 2.5}, BOUNDS, GOAL, [], 0)
    assert temiz.ok is True, temiz.reasons
