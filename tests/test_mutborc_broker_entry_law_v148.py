"""test_mutborc_broker_entry_law_v148.py — H5 TEST-BORCU: `broker.entry_law` mutasyon kümesi.

NEDEN: `entry_law` giriş-icra yasasının TEK okuyucusudur (iki motor — iç `fill_entry` ve ayna
`alpaca.submit_bracket` — ödedikleri fiyatı buradan alır). Mutasyon taraması bu fonksiyonda 46
mutantın HAYATTA kaldığını gösterdi: yani sözlük anahtarı, eşik sınırı ya da beyaz-liste dizgesi
sessizce değişse suite YEŞİL kalıyordu. Sessiz değişimin sonucu "test kırılır" değil, "ajan farklı
bir fiyattan doldurulmuş sanır"dır. Bu dosya o 46 mutantın ÖLDÜRÜLEBİLİR olanlarını davranışla
kapatır; öldürülemeyenleri (eşdeğer) numarayla kayda geçirir — YASA 4 ruhu: sessizce yutulan hiçbir
şey yok, yutulan her şey gerekçesiyle yazılı.

Kaynak fonksiyon: meridian/broker.py::entry_law
Mutant gövdeleri : mutants/meridian/broker.py::x_entry_law__mutmut_N

------------------------------------------------------------------------------------------------
HEDEFLENEN MUTANT SINIFLARI (hayatta kalan 46'nın 35'i)
------------------------------------------------------------------------------------------------
 S1  cfg başlangıç sözlüğünün ANAHTAR ADI bozulur (6 "XXgap_behaviorXX", 7 "GAP_BEHAVIOR",
     8 "XXtifXX", 9 "TIF") → A1 (anahtar kümesi TAM eşitlikle sınanır)
 S2  config okuma zinciri koparılır (14 raw=None, 15 `or`→`and`, 16 .get(None), 17 goal() `and`,
     18 "XXexecution_v2XX", 19 "EXECUTION_V2") → F1 (goal() taklidi ile override=None yolu)
 S3  limit_atr_mult okuması koparılır (21 m=None, 22 float(None), 23 .get(None,…),
     25 .get(cfg[…]), 27/28 anahtar dizgesi bozulur) → B1
 S4  limit_atr_mult eşiği kayar (31 `>=0`→`>0`, 32 `>=0`→`>=1`) → B2 (m=0.0 SINIR), B1 (m=0.25)
 S5  limit_atr_mult YAZIM anahtarı bozulur (34, 35) → B1
 S6  limit_pct_cap aralığı kayar (47 `0<p`→`0<=p`, 48 `p<=0.10`→`p<0.10`, 49 tavan 0.10→1.1)
     → C2 (p=0.0), C3 (p=0.10 SINIR DAHİL), C4 (p=0.50 reddedilmeli)
 S7  tif beyaz-liste/okuma/yazımı bozulur (68 .lower()→.upper(), 69 str(None), 70 .get(None,…),
     72 .get(""), 74/75 anahtar dizgesi, 80/81 "gtc" dizgesi, 83/84 yazım anahtarı) → E1
 S8  tif beyaz-listesinin "day" ucu bozulur (78 "XXdayXX", 79 "DAY") → E2
     (yalnız ENTRY_TIF varsayılanı "day" DIŞINA alınınca gözlenebilir; bkz. E2 gerekçesi)

------------------------------------------------------------------------------------------------
EŞDEĞER — ÖLDÜRÜLEMEZ (11 mutant; test yazılmadı, gerekçe burada)
------------------------------------------------------------------------------------------------
 20  `except` dalında `raw = {}` → `raw = None`. Boş sözlükle döngü gövdesi hiçbir alanı
     DEĞİŞTİRMEZ (her alan zaten kendi varsayılanına eşitlenir), None ise `isinstance` kapısından
     döner. İki yol da BİREBİR aynı sözlüğü üretir.
 24  `raw.get("limit_atr_mult", None)`; 26 `raw.get("limit_atr_mult", )`
 39  `raw.get("limit_pct_cap", None)`;  41 `raw.get("limit_pct_cap", )`
     → Anahtar VARSA değer aynıdır. Anahtar YOKSA orijinal `float(varsayılan)` hesaplayıp aynı
     varsayılanı geri yazar; mutant TypeError alıp `pass` ile aynı varsayılanı bırakır. Gözlenebilir
     fark yok — "varsayılanı yeniden yazmak" ile "hiç yazmamak" bu fonksiyonda aynı şeydir.
 55  gap_behavior varsayılan nöbetçisi ""→None; 57 nöbetçi silinir; 60 ""→"XXXX"
 71  tif varsayılan nöbetçisi ""→None;      73 nöbetçi silinir;  76 ""→"XXXX"
     → Nöbetçi değerin TEK işlevi beyaz-listeye DÜŞMEMEKTİR. "", "None", "XXXX" — hiçbiri listede
     olmadığı için üçü de aynı dalı seçer.
     NOT (kırılganlık, bugün tetiklenmiyor): kapı `raw.get(anahtar, "")` ile okunuyor ama atama
     `raw[anahtar]` ile yapılıyor. Nöbetçi değer bir gün beyaz-listeye girerse (ör. GAP_MARKETABLE
     "" olursa) anahtarsız sözlük KeyError verir. Bugün olanaksız olduğu için test edilmedi, ama
     yasayı değiştiren kişinin görmesi için buraya yazıldı.

Fikstür sözleşmesi: hiçbir test canlı `state/`e YAZMAZ; config yolu (`config.goal`) yalnız
monkeypatch ile taklit edilir, gerçek `goal.yaml` okunmaz — yasa testinin sonucu dosyanın o günkü
içeriğine bağlı olmamalıdır.
"""
from __future__ import annotations

import pytest

from meridian import broker as BR
from meridian import config


VARSAYILAN = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01,
              "gap_behavior": "marketable_limit", "tif": "day", "version": "E1-v1"}


# =============================== A — varsayılan sözleşme =========================================

def test_a1_varsayilan_sozlesme_anahtar_kumesi_ve_degerleri():
    """S1: cfg sözlüğünün ANAHTAR ADLARI yasanın dışa dönük arayüzüdür — `fill_entry`,
    `entry_order_decision` ve ayna hepsi bu adlarla okuyor. Anahtar sessizce değişirse okuyucu
    KeyError almaz, `cfg["gap_behavior"]` diye erişen taraf patlar ya da yanlış dala düşer.
    TAM eşitlik: fazladan/eksik anahtar da hüküm."""
    law = BR.entry_law({})
    assert set(law) == {"limit_atr_mult", "limit_pct_cap", "gap_behavior", "tif", "version"}
    assert law == VARSAYILAN
    # yasanın kart grid'indeki VARSAYILAN noktası — buradaki bir değişim kart olmadan gelmez
    assert (BR.ENTRY_LIMIT_ATR_MULT, BR.ENTRY_LIMIT_PCT_CAP) == (0.5, 0.01)
    assert (BR.GAP_MARKETABLE, BR.GAP_VETO, BR.ENTRY_TIF) == ("marketable_limit", "cancel", "day")


# =============================== B — limit_atr_mult =============================================

def test_b1_atr_mult_override_gercekten_uygulanir():
    """S3+S5+S4(32): config'ten gelen geçerli çarpan YÜRÜRLÜĞE girmeli. Okuma zinciri (anahtar
    adı, .get imzası, float dönüşümü) ya da yazım anahtarı bozulursa değer sessizce varsayılanda
    kalır — 'config'te yazıyordu ama etkisizdi' hâli, yasanın hiç olmadığı hâlden tehlikelidir."""
    assert BR.entry_law({"limit_atr_mult": 1.25})["limit_atr_mult"] == 1.25
    assert BR.entry_law({"limit_atr_mult": 0.25})["limit_atr_mult"] == 0.25   # 1'in ALTINDA: 32'yi keser
    assert BR.entry_law({"limit_atr_mult": "0.75"})["limit_atr_mult"] == 0.75  # dizge de sayıya çevrilir


def test_b2_atr_mult_sifir_kabul_edilir_sinir():
    """S4(31): eşik `m >= 0`, `m > 0` DEĞİL. 0.0 anlamlı bir yasa noktasıdır — 'ATR ofsetini
    kapat, yalnız yüzde tavanı bağlasın'. `>` olsaydı bu istek sessizce 0.5'e dönerdi."""
    assert BR.entry_law({"limit_atr_mult": 0.0})["limit_atr_mult"] == 0.0
    assert BR.entry_law({"limit_atr_mult": 0})["limit_atr_mult"] == 0.0


def test_b3_atr_mult_negatif_reddedilir():
    """Negatif çarpan limiti tetiğin ALTINA indirirdi (dolum hiç olmazdı). Kelepçe: varsayılana düş."""
    for kotu in (-0.001, -1.0, -1e9):
        assert BR.entry_law({"limit_atr_mult": kotu})["limit_atr_mult"] == 0.5


def test_b4_atr_mult_bozuk_deger_varsayilanda_kalir():
    """YASA 4 sessiz-yutma: biçimsiz düğme yasayı yok etmez, varsayılana düşer."""
    for kotu in ("abc", None, [], {}, object()):
        law = BR.entry_law({"limit_atr_mult": kotu})
        assert law["limit_atr_mult"] == 0.5 and law["version"] == "E1-v1"


# =============================== C — limit_pct_cap ==============================================

def test_c1_pct_cap_gecerli_deger_uygulanir():
    assert BR.entry_law({"limit_pct_cap": 0.02})["limit_pct_cap"] == 0.02
    assert BR.entry_law({"limit_pct_cap": 0.005})["limit_pct_cap"] == 0.005


def test_c2_pct_cap_sifir_reddedilir_sinir():
    """S6(47): aralık `0 < p`, `0 <= p` DEĞİL. p=0 limiti tetiğe EŞİTLERDİ; ATR ofseti de 0 ise
    hiçbir emir dolmazdı (sessiz 'işlem yok' rejimi). Sıfır bir yasa noktası değil, bozuk değerdir."""
    assert BR.entry_law({"limit_pct_cap": 0.0})["limit_pct_cap"] == 0.01
    assert BR.entry_law({"limit_pct_cap": -0.01})["limit_pct_cap"] == 0.01


def test_c3_pct_cap_ust_sinir_dahildir():
    """S6(48): tavan KAPALI aralıktır — p=0.10 GEÇERLİDİR. `p < 0.10` olsaydı tam %10 isteyen
    config sessizce %1'e düşerdi (istenen tavanın onda biri)."""
    assert BR.entry_law({"limit_pct_cap": 0.10})["limit_pct_cap"] == 0.10
    assert BR.entry_law({"limit_pct_cap": 0.0999})["limit_pct_cap"] == 0.0999


def test_c4_pct_cap_tavan_ustu_reddedilir():
    """S6(49): tavan 0.10'dur, 1.1 değil. Tavan gevşerse %50'lik bir 'limit' fiilen limitsiz olur —
    icra yasasının 2. maddesi (hiçbir motor limitin üstünde dolum yazamaz) anlamını yitirir."""
    for kotu in (0.1001, 0.5, 1.0, 1.1, 12.0):
        assert BR.entry_law({"limit_pct_cap": kotu})["limit_pct_cap"] == 0.01


def test_c5_pct_cap_bozuk_deger_varsayilanda_kalir():
    for kotu in ("yuzde bir", None, [], object()):
        assert BR.entry_law({"limit_pct_cap": kotu})["limit_pct_cap"] == 0.01


# =============================== D — gap_behavior ===============================================

def test_d1_gap_veto_uygulanir_ve_bosluk_kirpilir():
    assert BR.entry_law({"gap_behavior": "cancel"})["gap_behavior"] == BR.GAP_VETO
    assert BR.entry_law({"gap_behavior": "  cancel  "})["gap_behavior"] == "cancel"


def test_d2_gap_marketable_acikca_secilebilir():
    assert BR.entry_law({"gap_behavior": " marketable_limit "})["gap_behavior"] == "marketable_limit"


def test_d3_gap_beyaz_liste_disi_reddedilir():
    """Beyaz liste TAM iki noktadır (kart grid'i). 'CANCEL' BÜYÜK harfle REDDEDİLİR — bu dal tif
    dalının aksine küçültme yapmaz; asimetri bilinçli olarak sabitleniyor ki bir gün değişirse
    test söylesin, canlı davranış değil."""
    for kotu in ("market", "CANCEL", "Cancel", "veto", "", None, 5, ["cancel"]):
        assert BR.entry_law({"gap_behavior": kotu})["gap_behavior"] == "marketable_limit"


# =============================== E — tif ========================================================

def test_e1_tif_gtc_uygulanir_normalize_edilerek():
    """S7: 'gtc' beyaz-listede olmalı, okuma anahtarı 'tif' olmalı, karşılaştırma KÜÇÜK harfe
    indirgenerek yapılmalı ve sonuç `cfg["tif"]`e yazılmalı. Bu zincirin herhangi bir halkası
    kopunca config 'gtc' der, yasa 'day' uygular — ayna bir sonraki seansa bayat tetik taşımaz
    sanırken taşır (ya da tersi)."""
    assert BR.entry_law({"tif": "gtc"})["tif"] == "gtc"
    assert BR.entry_law({"tif": " GTC "})["tif"] == "gtc"
    assert BR.entry_law({"tif": "Gtc"})["tif"] == "gtc"


def test_e2_tif_day_beyaz_listede_varsayilandan_bagimsiz(monkeypatch):
    """S8(78, 79): beyaz-listenin 'day' ucu, ENTRY_TIF varsayılanı da 'day' olduğu için normalde
    GÖZLENEMEZ — 'kabul edip day yazmak' ile 'reddedip varsayılan day'de kalmak' aynı çıktıyı verir.
    Varsayılanı geçici olarak 'gtc'ye alıp beyaz-listeyi tek başına sınıyoruz: config 'day' derse
    yasa 'day' UYGULAMALIDIR, varsayılana geri düşmemelidir."""
    monkeypatch.setattr(BR, "ENTRY_TIF", "gtc")
    assert BR.entry_law({})["tif"] == "gtc"                    # varsayılan gerçekten değişti
    assert BR.entry_law({"tif": "day"})["tif"] == "day"        # beyaz liste 'day'i KABUL ediyor
    assert BR.entry_law({"tif": " DAY "})["tif"] == "day"      # normalize edilerek


def test_e3_tif_beyaz_liste_disi_reddedilir():
    for kotu in ("opg", "cls", "ioc", "fok", "", "  ", None, 5, ["day"]):
        assert BR.entry_law({"tif": kotu})["tif"] == "day"


# =============================== F — config yolu (override=None) ================================

def test_f1_config_execution_v2_blogu_gercekten_okunur(monkeypatch):
    """S2: override verilmediğinde yasa `goal.yaml → execution_v2` bloğundan gelir. Zincirin
    koptuğu mutantlarda fonksiyon SESSİZCE modül varsayılanlarını döndürür — yani operatörün
    dosyaya yazdığı yasa hiç yürürlüğe girmez ve hiçbir test bunu söylemez."""
    monkeypatch.setattr(config, "goal", lambda: {"execution_v2": {
        "limit_atr_mult": 0.75, "limit_pct_cap": 0.03, "gap_behavior": "cancel", "tif": "gtc"}})
    law = BR.entry_law()
    assert law == {"limit_atr_mult": 0.75, "limit_pct_cap": 0.03,
                   "gap_behavior": "cancel", "tif": "gtc", "version": "E1-v1"}


def test_f2_config_bloktaki_tek_alan_digerlerini_varsayilanda_birakir(monkeypatch):
    """Kısmi blok: yalnız yazılan alan değişir, yazılmayanlar varsayılanda kalır (blok bir
    'hepsi ya da hiçbiri' anahtarı değildir)."""
    monkeypatch.setattr(config, "goal", lambda: {"execution_v2": {"tif": "gtc"}})
    assert BR.entry_law() == dict(VARSAYILAN, tif="gtc")


def test_f3_config_okunamazsa_yasa_yok_olmaz_varsayilana_duser(monkeypatch):
    """YASA 4 sessiz-yutma hükmü: config okunamadığında (dosya yok / bozuk YAML / import hatası)
    yasa YOK olmaz, varsayılan noktaya düşer. Bu 'except' dalının davranışı sözleşmedir."""
    def _patla():
        raise RuntimeError("goal.yaml okunamadi")
    monkeypatch.setattr(config, "goal", _patla)
    assert BR.entry_law() == VARSAYILAN


def test_f4_bloksuz_veya_bos_config_varsayilan_verir(monkeypatch):
    for sahte in ({}, {"execution_v2": None}, {"execution_v2": {}}, {"baska": 1}, None):
        monkeypatch.setattr(config, "goal", lambda s=sahte: s)
        assert BR.entry_law() == VARSAYILAN


# =============================== G — sağlamlık ==================================================

def test_g1_dict_olmayan_override_yok_sayilir():
    """Sözlük olmayan override sessizce ATLANIR (isinstance kapısı) — ama yasa yine tam döner."""
    for kotu in ("abc", 5, [("tif", "gtc")], (1, 2), 0.5, True):
        assert BR.entry_law(kotu) == VARSAYILAN


def test_g2_donen_sozluk_cagrilar_arasinda_paylasilmaz():
    """Yasa her çağrıda TAZE üretilmeli. Paylaşılan bir sözlük dönseydi tek bir okuyucunun
    `law["tif"] = ...` yazması sonraki HER okuyucuyu (iç motor + ayna) etkilerdi — `config.goal()`
    derin-kopya gerekçesinin aynısı."""
    a = BR.entry_law({})
    a["tif"] = "SAHTE"
    a["limit_pct_cap"] = 9.9
    assert BR.entry_law({}) == VARSAYILAN
    assert BR.entry_law({"tif": "gtc"})["limit_pct_cap"] == 0.01


def test_g3_yasa_saf_ve_tekrarlanabilir():
    """Aynı girdi → aynı sözlük (ağ yok, saat yok, defter yok). İki motor aynı yasayı okuduğu
    için tekrarlanabilirlik sözleşmenin parçasıdır."""
    ov = {"limit_atr_mult": 0.3, "limit_pct_cap": 0.02, "gap_behavior": "cancel", "tif": "gtc"}
    assert BR.entry_law(ov) == BR.entry_law(dict(ov)) == BR.entry_law(ov)
