"""test_sohbet_cikti_atif_v449.py — TSK-012 dalga-B / B3 Task 1: ARAÇ ÇIKTISI ATIF İZİ.

NE ÇİVİLENİR (plan `docs/superpowers/plans/2026-09-08-pano-sohbet-b3.md` Task 1, kart
EDG-2026-086): `cikti_atiflari` dört sınıfı (sayı · kimlik · yol · sembol) AYIRIR ve deterministik
sıralı döner · `sohbet_dongusu` BAŞARILI her araç çağrısından sonra tur satırına birleşik atıf
kümesini yazar · ŞEMA-DIŞI ve ARIZALI çağrıda alan HİÇ EKLENMEZ (uydurma sayımının PAYDASI
şişmesin) · sınıf başına 200 öğe tavanı ve `cikti_atif_kesildi` beyanı · sır süzgeci ATIFTAN ÖNCE
koşar (sır hiçbir atıf kümesinde görünmez).

NEDEN VAR (ölçüm sözleşmesi): kartın `kill_list`i "uydurma sayımı araç çıktısını değil cevabı tek
başına okursa ölçüm geçersiz" der — PAYDA araç çıktısıdır. Defter araç çıktısının METNİNİ
saklamaz (8 KB × 6 tur × 100+ mesaj ve sır yüzeyi); bunun yerine bu alan LİTERAL ATIF KÜMESİNİ
saklar. Bu dosya o kümenin doğduğu yeri çiviler; sayan taraf `tests/test_edg086_sayim_v450.py`.

MODEL VE ARAÇLAR SAHTEDİR (v440 deseni): hiçbir gerçek kapı çağrısı, hiçbir dış süreç. Yazımlar
`sandbox_state` ile tmp'ye düşer — pytest DIŞI koşum bu depoda yasaktır (canlı deftere yazardı).
"""
from __future__ import annotations

import json

import pytest

from meridian import sohbet


# =================================================================================================
# SAHTE MODEL / ARAÇ YARDIMCILARI — v440 ile AYNI şekil (tek desen, iki dosya)
# =================================================================================================
class SahteModel:
    """`model_cagir(mesajlar, araclar) -> dict`in sahtesi; kuyruk bitince düz metin cevabı."""

    def __init__(self, *cevaplar):
        self.kuyruk = list(cevaplar)
        self.cagrilar: list[dict] = []

    def __call__(self, mesajlar, araclar):
        self.cagrilar.append({"mesajlar": [dict(m) for m in mesajlar], "araclar": araclar})
        if self.kuyruk:
            return self.kuyruk.pop(0)
        return _metin("son cevap")


def _tc(ad, args, cid="c1"):
    return {"id": cid, "type": "function",
            "function": {"name": ad, "arguments": json.dumps(args, ensure_ascii=False)}}


def _arac(*tool_calls, model="sahte-1"):
    return {"mesaj": {"content": "", "tool_calls": list(tool_calls)}, "model": model,
            "jeton_giris": 10, "jeton_cikis": 5}


def _metin(txt, model="sahte-1"):
    return {"mesaj": {"content": txt, "tool_calls": []}, "model": model,
            "jeton_giris": 10, "jeton_cikis": 5}


def _sahte_arac(ad: str, cikti):
    """Kayıt sözleşmesine uyan, `cikti`yi (ya da çağrılabilirse sonucunu) döndüren sahte araç."""
    return sohbet.Arac(
        ad=ad, cagir=(cikti if callable(cikti) else (lambda args, baglam=None: cikti)),
        sema={"type": "object", "properties": {}, "additionalProperties": False},
        aciklama="sahte", anahtar=lambda args: "-")


@pytest.fixture
def kum(sandbox_state):
    return sandbox_state


# =================================================================================================
# 1) ÇIKARICI — dört sınıf AYRI, deterministik, sıralı (plan Task 1 / Çivi 1)
# =================================================================================================
def test_cikti_atiflari_dort_sinifi_ayirir():
    metin = ("T00842 kapandı, 1.103R, AAPL 189.5, "
             "research/cards/EDG-2026-086-pano-sohbet-kalite.yaml, P-2026-09-07-3")
    out = sohbet.cikti_atiflari(metin, evren=frozenset({"AAPL", "NVDA"}))

    assert set(out) == set(sohbet.ATIF_SINIFLARI), out
    assert {"1.103", "189.5"} <= set(out["sayi"]), out["sayi"]
    assert {"T00842", "EDG-2026-086", "P-2026-09-07-3"} <= set(out["kimlik"]), out["kimlik"]
    assert "research/cards/EDG-2026-086-pano-sohbet-kalite.yaml" in out["yol"], out["yol"]
    assert out["sembol"] == ["AAPL"], out["sembol"]
    # DETERMİNİK VE SIRALI: sayaç iki tarafı kıyaslar; sıra oynarsa defter satırı da oynardı.
    for sinif, deger in out.items():
        assert deger == sorted(set(deger)), (sinif, deger)
    assert sohbet.cikti_atiflari(metin, evren=frozenset({"AAPL", "NVDA"})) == out


def test_kimlik_parcalari_sayi_sayilmaz():
    """`EDG-2026-086`nın "2026"sı SAYI DEĞİLDİR — kimliğin parçasıdır.

    Bu ayrım ölçümün yönünü belirler: kimlik parçaları sayı sınıfına sızsaydı payda sahte
    değerlerle şişer ve uydurma oranı HAK ETMEDEN düşerdi (EXE-2026-006 sınıfı yanlılık)."""
    out = sohbet.cikti_atiflari("EDG-2026-086 ve P-2026-09-07-3 ve TSK-012 ve T00842",
                                evren=frozenset())
    assert out["sayi"] == [], out["sayi"]
    assert "2026" not in out["sayi"] and "086" not in out["sayi"]


def test_yuzde_ve_ondalik_virgul_sayi_sinifina_girmez():
    """`%12` ve `1,103` ÖLÇÜLEMEYEN biçimlerdir — sayı sınıfına GİRMEZLER.

    Yüzde türetilmiş bir değerdir (araç çıktısında literal geçmesi beklenmez); Türkçe ondalık
    virgülü ile binlik ayracı aynı karakteri kullanır ve ayırt edilemez. İkisini de sayı saymak
    UYDURMA YANLIŞ POZİTİFİ üretirdi; sayaç onları `belirsiz` kovasında sayar (v450)."""
    out = sohbet.cikti_atiflari("oran %12, tutar 1,103 ve 12,5 ile 7 adet", evren=frozenset())
    assert out["sayi"] == ["7"], out["sayi"]


def test_yuzde_yazili_ve_ayrik_yuzde_sayi_sinifina_girmez():
    """AYNI SEMANTİK DEĞER ÜÇ YAZIMDA: `%12` · `yüzde 12` · `12 %`. Üçü de TÜRETİLMİŞ orandır ve
    araç çıktısında literal geçmesi beklenmez.

    Tur-1'de yalnız `%12` eleniyordu: `yüzde 12` doğrudan sayı sınıfına giriyor (uydurma adayı),
    `12 %` ise HEM sayı HEM belirsiz sayılıyordu (çift sayım). Yazım biçimine göre üç ayrı kovaya
    düşen bir değer ölçülmüş değil, ölçüm artefaktıdır — sayaçtaki disjointlik çivisi v450'de."""
    out = sohbet.cikti_atiflari("yüzde 12 arttı, 34 % düştü, 5 adet kaldı", evren=frozenset())
    assert out["sayi"] == ["5"], out["sayi"]
    assert sohbet.cikti_atiflari("Yüzde 12 arttı", evren=frozenset())["sayi"] == []


def test_negatif_sayi_okunur_kimlik_tiresi_okunmaz():
    out = sohbet.cikti_atiflari("getiri -2.4 ve T00001", evren=frozenset())
    assert out["sayi"] == ["-2.4"], out["sayi"]
    assert out["kimlik"] == ["T00001"], out["kimlik"]


def test_sembol_kaynagi_olculmus_evrendir():
    """SEMBOL KAYNAĞI ÖLÇÜLDÜ: bu depoda `meridian/universe.py` ve `state/universe.json` YOKTUR;
    kod-sahipli tek kaynak `REPLAY_UNIVERSE`dur. Ayrışırsa bu çivi öter."""
    from meridian.adapters import data as _data

    assert sohbet._evren_sembolleri() == frozenset(str(t).upper() for t in _data.REPLAY_UNIVERSE)
    out = sohbet.cikti_atiflari("AAPL ve NVDA ve ZZZQQ yükseldi")
    assert "AAPL" in out["sembol"] and "NVDA" in out["sembol"]
    assert "ZZZQQ" not in out["sembol"], "evren dışı dizge sembol sayıldı"


def test_turkce_buyuk_harfli_sozcukler_sembol_uretmez():
    """SOHBETİN DİLİ TÜRKÇEDİR (inceleme bulgusu, 2026-09-08). Tur-1'in ASCII lookaround'ları
    (`(?<![A-Za-z0-9])`) Türkçe büyük harfleri (Ç Ğ İ Ö Ş Ü) SINIR sayıyordu: `GEÇTİ` → `GE`+`T`,
    `DEĞİL` → `DE`+`T` gibi parçalar evrenle kesişip SAHTE uydurma üretiyordu. Cevap tarafı Türkçe,
    araç çıktısı ASCII/JSON olduğu için bu yanlış-pozitifler sistematikti ve 0,05 DONUK eşiğini
    tek başına aşabilirdi.

    EVREN SAHTELENMEZ: bu çivi GERÇEK `REPLAY_UNIVERSE`le koşar — sahte bir evren tam da bu
    arıza sınıfına kör kalırdı (tur-1'in bütün sembol çivilerinin kusuru)."""
    for cumle in ("SİSTEM DURDU, PIT kuralı, TAM erişim",
                  "Plan GEÇTİ mi? Kart KALDI diyor.",
                  "TÜM pozisyonlar KAPANDI, DEĞİL mi?",
                  "Bugün 3 emir GİRİLDİ ve 1 tanesi DÜŞTÜ.",
                  # ÖLÇÜLDÜ: ASCII sınırıyla `HALİ` → `HAL` (Halliburton) ve `TERİM` → `TER`
                  # (Teradyne) ADAYI olur ve İKİSİ DE GERÇEKTEN EVRENDEDİR. Yani arıza yalnız
                  # "kısa parça" arızası değildir: Türkçe harf, üç harfli GERÇEK sembollere de
                  # bölüyor. Asgari uzunluk kuralı bu sınıfı YAKALAMAZ — sınırın kendisi
                  # Unicode olmak zorundadır.
                  "MEVCUT HALİ korunuyor; TERİM sözlükte yok."):
        assert sohbet.cikti_atiflari(cumle)["sembol"] == [], cumle


def test_kisa_evren_kesisimleri_sembol_degil_BELIRSIZdir():
    """≤2 HARFLİ KESİŞİMLER AYIRT EDİLEMEZ. Evrende `T`, `V`, `D`, `O`, `MA`, `SO`, `MU`, `CI`,
    `DE`, `ON` gibi tek/iki harfli semboller var ve bunlar Türkçe metnin gündelik parçalarıdır
    ("K defterine", "SO-…" öneki, "MU planı", "CI kırmızı"). Sembol sayılsalardı araç çıktısında
    geçmedikleri için doğrudan UYDURMA olurlardı; sessizce atılsalardı ölçüm KÖR olurdu.

    SINIF TANIMI ÖLÇÜM PENCERESİ AÇILMADAN DARALTILDI (kart eşiği/penceresi DEĞİŞMEDİ): kısa
    kesişimler `belirsiz` kovasına gider — uydurma yasağının "ölçülemeyen değer 0 değildir"
    maddesi. Sayaç bunu `uydurma.belirsiz`e ekler (v450)."""
    metin = "MU planı ve CI kırmızı; T sütunu ile O yüzden."
    out = sohbet.cikti_atiflari(metin)
    assert out["sembol"] == [], out["sembol"]
    assert sohbet.belirsiz_semboller(metin) == ["CI", "MU", "O", "T"], \
        sohbet.belirsiz_semboller(metin)
    # UZUN KESİŞİM HÂLÂ SEMBOLDÜR — daraltma yalnız kısa adayları taşır.
    assert sohbet.cikti_atiflari("AAPL ve NVDA")["sembol"] == ["AAPL", "NVDA"]
    assert sohbet.belirsiz_semboller("AAPL ve NVDA") == []


def test_oneri_kimligi_uretiminden_turer():
    """SO-… deseni KOPYA DEĞİL TÜREVDİR: üretici ne yazıyorsa çıkarıcı onu tanır."""
    kimlik = sohbet.oneri_kimligi("20260908T120000Z", 3)
    out = sohbet.cikti_atiflari(f"öneri {kimlik} yazıldı", evren=frozenset())
    assert out["kimlik"] == [kimlik], out["kimlik"]


# =================================================================================================
# 2) DEFTER ALANI — başarılı çağrıda YAZILIR (plan Task 1 / Çivi 2)
# =================================================================================================
def test_basarili_arac_turunda_atif_kumesi_deftere_yazilir(kum):
    araclar = dict(sohbet.ARACLAR)
    araclar["sahte_oku"] = _sahte_arac("sahte_oku", "T00001 12.5")
    m = SahteModel(_arac(_tc("sahte_oku", {})), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    tur = out["turlar"][0]
    assert tur["cikti_atiflari"]["kimlik"] == ["T00001"], tur
    assert tur["cikti_atiflari"]["sayi"] == ["12.5"], tur
    assert tur["cikti_atiflari"]["yol"] == [] and tur["cikti_atiflari"]["sembol"] == [], tur
    assert "cikti_atif_kesildi" not in tur, tur
    # DEFTERE DE DÜŞTÜ (dönüş ile satır TEK şekildir).
    from meridian import store
    satir = [r for r in store.read_jsonl(sohbet.SOHBET_DEFTERI) if isinstance(r, dict)][-1]
    assert satir["turlar"][0]["cikti_atiflari"] == tur["cikti_atiflari"], satir


def test_ayni_turdaki_iki_arac_ciktisi_birlestirilir(kum):
    araclar = dict(sohbet.ARACLAR)
    araclar["a_oku"] = _sahte_arac("a_oku", "T00001")
    araclar["b_oku"] = _sahte_arac("b_oku", "T00002 5.5")
    m = SahteModel(_arac(_tc("a_oku", {}, "c1"), _tc("b_oku", {}, "c2")), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    assert out["turlar"][0]["cikti_atiflari"]["kimlik"] == ["T00001", "T00002"], out["turlar"]
    assert out["turlar"][0]["cikti_atiflari"]["sayi"] == ["5.5"], out["turlar"]


def test_sema_disi_turda_atif_alani_hic_eklenmez(kum):
    """Model yanlış konuştu, hiçbir veri okunmadı — PAYDA ŞİŞMEZ, alan YOKTUR."""
    m = SahteModel(_arac(_tc("emir_gonder", {"ticker": "NVDA"})), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m)

    assert out["sema_disi_n"] == 1, out
    assert "cikti_atiflari" not in out["turlar"][0], out["turlar"][0]


def test_arizali_ve_reddedilen_aracta_atif_alani_hic_eklenmez(kum):
    """`AracReddi` (istek reddedildi) ve araç arızası: veri OKUNMADI → atıf YOK.

    Reddin metni araç adını ve gerekçeyi taşır; onu payda saymak "hiç veri döndürmemiş bir aracı
    kaynak saymak" olurdu (`AracReddi` sınıfının kendi gerekçesi)."""
    def _red(args, baglam=None):
        raise sohbet.AracReddi("T09999 sayısı 42 olan bir ret metni")

    def _ariza(args, baglam=None):
        raise RuntimeError("T08888 ve 7.5")

    araclar = dict(sohbet.ARACLAR)
    araclar["reddeden"] = _sahte_arac("reddeden", _red)
    araclar["arizali"] = _sahte_arac("arizali", _ariza)
    m = SahteModel(_arac(_tc("reddeden", {}, "c1"), _tc("arizali", {}, "c2")), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    assert out["sema_disi_n"] == 0, out
    assert "cikti_atiflari" not in out["turlar"][0], out["turlar"][0]


# =================================================================================================
# 3) TAVAN — sınıf başına 200, taşma SINIF ADIYLA BEYAN EDİLİR (plan Task 1 / Çivi 3)
# =================================================================================================
def test_atif_tavani_200de_kesilir_ve_TASAN_SINIF_adiyla_beyan_edilir(kum):
    """TAŞMA SINIF BAŞINADIR, SATIR BAŞINA DEĞİL (inceleme bulgusu, 2026-09-08).

    Tur-1'de bayrak tek bir `True`ydu ve sayaç onu görünce SATIRIN TAMAMINI ölçüm dışına atıyordu:
    `sayi` taşan bir `bar_sorgu` cevabında `kimlik`/`yol`/`sembol` paydaları TAM olduğu hâlde
    ölçülmüyordu. Daha ağırı SEÇİM YANLILIĞIydı — en çok sayı taşıyan (yani uydurma riski en
    yüksek) cevaplar tam da elenenlerdi ve oran hak etmeden düşüyordu."""
    # 300 FARKLI sayı, `ARAC_CIKTI_TAVANI`nın ALTINDA bir gövdede: kesen şey BAYT tavanı değil,
    # atıf tavanıdır (aksi hâlde çivi yanlış dalı ısırırdı).
    govde = " ".join(str(1000 + i) for i in range(300)) + " T00001 AAPL"
    assert len(govde) < sohbet.ARAC_CIKTI_TAVANI
    araclar = dict(sohbet.ARACLAR)
    araclar["cok_sayi"] = _sahte_arac("cok_sayi", govde)
    m = SahteModel(_arac(_tc("cok_sayi", {})), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    tur = out["turlar"][0]
    assert len(tur["cikti_atiflari"]["sayi"]) == sohbet.ATIF_SINIF_TAVANI == 200, tur
    assert tur["cikti_atif_kesildi"] == ["sayi"], tur
    # TAŞMAYAN SINIFLAR TAMDIR — payda eksik değil, o sınıflar ölçülebilir.
    assert tur["cikti_atiflari"]["kimlik"] == ["T00001"], tur
    assert tur["cikti_atiflari"]["sembol"] == ["AAPL"], tur


# =================================================================================================
# 4) SIR SÜZGECİ ATIFTAN ÖNCE KOŞAR (plan Task 1 / Çivi 4)
# =================================================================================================
def test_sir_arac_ciktisindan_atif_kumesine_sizmaz(kum, monkeypatch):
    """Sahte iki sır araç çıktısına konur; hiçbir atıf sınıfında DEĞERLERİ görünmez.

    POZİTİF KONTROL ÖNCE: çıkarıcı bu değerleri süzgeçsiz metinde GERÇEKTEN görüyor — aksi hâlde
    "sızmadı" iddiası boş bir yeşil olurdu (v59 deseni)."""
    from meridian import secrets as _sec
    sir_anahtar = "sk-T88888-AAPL-token-xyz"
    sir_sayi = "9998887776665554"

    pk = sohbet.cikti_atiflari(f"anahtar={sir_anahtar} deger={sir_sayi}")
    assert "T88888" in pk["kimlik"] and "AAPL" in pk["sembol"] and sir_sayi in pk["sayi"], pk

    monkeypatch.setattr(_sec, "ALLOWED",
                        tuple(getattr(_sec, "ALLOWED", ())) + ("SOHBET_SIR_A", "SOHBET_SIR_B"))
    monkeypatch.setattr(_sec, "get", lambda ad, *a, **k: {"SOHBET_SIR_A": sir_anahtar,
                                                          "SOHBET_SIR_B": sir_sayi}.get(ad))
    araclar = dict(sohbet.ARACLAR)
    araclar["sizinti"] = _sahte_arac("sizinti", f"anahtar={sir_anahtar} deger={sir_sayi} son")
    m = SahteModel(_arac(_tc("sizinti", {})), _metin("cevap"))
    out = sohbet.sohbet_dongusu("sır", "S1", model_cagir=m, araclar=araclar)

    atiflar = out["turlar"][0]["cikti_atiflari"]
    duz = json.dumps(atiflar, ensure_ascii=False)
    assert sir_anahtar not in duz and sir_sayi not in duz, atiflar
    assert "T88888" not in atiflar["kimlik"] and "AAPL" not in atiflar["sembol"], atiflar


# =================================================================================================
# 5) KESİNTİ BEYANI VE ÇİT PAYDAYA GİRMEZ (inceleme bulgusu, 2026-09-08)
# =================================================================================================
def test_kesinti_beyanindaki_N_ve_cit_jetonu_paydaya_girmez(kum):
    """MODELE GİDEN METİN ≠ PAYDA. `ARAC_CIKTI_TAVANI` aşılınca modele "…(N satır daha kesildi)"
    beyanı ve `<<<VERI:ad>>>` çiti gider; ikisi de VERİ DEĞİLDİR.

    NEDEN ÇİVİLENİR: `_arac_kos` başarı kolunun 4. dönüşü `kesit`tir (çitsiz, beyansız) ve tur-1'de
    bu dalı `metin`e çeviren bir mutasyon HİÇBİR çiviyi kırmıyordu — tavan çivisi gövdeyi bilerek
    bayt tavanının ALTINDA tutuyor, diğer çivilerde ise çit jetonu evrende olmadığı için sembol
    sınıfına girmiyordu. Somut zarar: 8 KB üstü bir çıktı "…(142 satır daha kesildi)" üretir ve N
    paydaya sızarsa cevaptaki uydurma "142" DAYANAKLI sayılır — kaçırılan uydurma."""
    # TEK RAKAM 7: gövdedeki tek sayı odur. Kesilen satır sayısı (N) gövdede GEÇMEZ, yani atıf
    # kümesinde görünürse tek kaynağı kesinti BEYANI olabilir.
    ham = "yedi 7\n" * 1200
    kesit, kesilen = sohbet.arac_kesiti(ham)
    assert len(ham) > sohbet.ARAC_CIKTI_TAVANI and kesilen > 1, (len(ham), kesilen)
    assert str(kesilen) != "7", kesilen

    modele_giden = sohbet.arac_bloku("cok_satir", ham)
    assert f"({kesilen} satır daha kesildi)" in modele_giden, modele_giden[-200:]
    assert sohbet.VERI_ACILIS.split("{")[0] in modele_giden or "VERI" in modele_giden

    araclar = dict(sohbet.ARACLAR)
    araclar["cok_satir"] = _sahte_arac("cok_satir", ham)
    m = SahteModel(_arac(_tc("cok_satir", {})), _metin("cevap"))
    out = sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    atiflar = out["turlar"][0]["cikti_atiflari"]
    assert atiflar == {"sayi": ["7"], "kimlik": [], "yol": [], "sembol": []}, atiflar
    assert str(kesilen) not in atiflar["sayi"], (kesilen, atiflar["sayi"])


# =================================================================================================
# 6) BEDEL — ATIF KÜMESİ CANLI UÇTAN ÇIKAR (inceleme bulgusu, 2026-09-08)
# =================================================================================================
def test_gecmis_yaniti_cikti_atiflarini_TASIMAZ_defter_TASIR(kum):
    """BEDEL YASASI: `GET /api/sohbet` (yani `gecmis`) `n`i 200'e kadar servis eder ve pano bu ucu
    düzenli okur. Sınıf başına 200 öğe × 4 sınıf × tur × 200 satır ölçülmemiş bir büyümedir.

    KAZANÇ ölçülü (payda), BEDEL ölçüsüzdü — alan uçtan ÇIKARILDI. Sayaç defteri DOĞRUDAN okur
    (`--defter`), uca ihtiyacı yoktur; defterde alan DURUR."""
    araclar = dict(sohbet.ARACLAR)
    araclar["sahte_oku"] = _sahte_arac("sahte_oku", "T00001 12.5")
    m = SahteModel(_arac(_tc("sahte_oku", {})), _metin("cevap"))
    sohbet.sohbet_dongusu("soru", "S1", model_cagir=m, araclar=araclar)

    from meridian import store
    ham = [r for r in store.read_jsonl(sohbet.SOHBET_DEFTERI) if isinstance(r, dict)][-1]
    assert ham["turlar"][0]["cikti_atiflari"]["kimlik"] == ["T00001"], ham["turlar"]

    servis = sohbet.gecmis("S1")[-1]
    assert "cikti_atiflari" not in servis["turlar"][0], servis["turlar"][0]
    # DEFTER KİRLENMEDİ: kırpma KOPYA üzerindedir, dosyadaki satır olduğu gibi durur.
    tekrar = [r for r in store.read_jsonl(sohbet.SOHBET_DEFTERI) if isinstance(r, dict)][-1]
    assert tekrar["turlar"][0]["cikti_atiflari"]["kimlik"] == ["T00001"], tekrar["turlar"]


# =================================================================================================
# 7) BELİRSİZ BİÇİMİN YAZIM VARYANTLARI — BÜYÜK HARF ve ÇOK BOŞLUK (yeniden inceleme, 2026-09-08)
# =================================================================================================
def test_BUYUK_HARFLI_ve_COK_BOSLUKLU_yuzde_yazimlari_da_sayi_sinifina_girmez():
    """AYNI SEMANTİK DEĞERİN BEŞİNCİ VE ALTINCI YAZIMI. Tur-2'de `yüzde 12` (tek boşluk, iki
    yazım) elenmişti; `YÜZDE 12`, `yüzde  12` ve `12  %` hâlâ SAYI sınıfına giriyordu ve aynı
    değer yazımına göre iki ayrı kovaya düşüyordu — ölçüm değil ölçüm ARTEFAKTI.

    BOŞLUK TAVANI ÜÇTÜR VE BEYANLIDIR: Python `re` DEĞİŞKEN GENİŞLİKLİ geriye bakış derlemez, o
    yüzden ret kuralı sabit genişlikli üç geriye bakışa açılır (1·2·3 boşluk). Dört ve daha fazla
    boşluk ölçülmemiş bir KALINTIdır ve iki kova için AYNI sınırı taşır: o hâlde değer `sayi`dır
    ve `belirsiz` DEĞİLDİR (ayrıklık her genişlikte korunur, çivisi v450'de)."""
    for metin in ("YÜZDE 12 arttı", "yüzde  12 arttı", "Yüzde   12 arttı",
                  "12  % düştü", "34\t% düştü", "%  12 oldu"):
        assert sohbet.cikti_atiflari(metin, evren=frozenset())["sayi"] == [], metin
    # POZİTİF KONTROL: kural yalnız YÜZDE BAĞLAMINI eler, sayıları değil.
    assert sohbet.cikti_atiflari("5 adet kaldı", evren=frozenset())["sayi"] == ["5"]
    assert sohbet.cikti_atiflari("getiri -2.4", evren=frozenset())["sayi"] == ["-2.4"]


# =================================================================================================
# 8) SEMBOL SINIFI BAĞLAM ÇAPASI İSTER (B1 kapanışı, yeniden inceleme 2026-09-08)
# =================================================================================================
def test_uc_harfli_evren_kesisimi_CAPASIZ_ise_sembol_DEGIL_belirsizdir():
    """DARALTMA SINIFI KÜÇÜLTTÜ, KAPATMADI (ölçüldü: evrenin 248 sembolünün 142'si ÜÇ harfli).
    `DAL` (Delta Air Lines) bu deponun kendi sözlüğünde günlük bir kelimedir ("dal ucu", "dal
    kapanışı"); `HAL` ve `TER` de aynı sınıftadır. Unicode sınırı yalnız Türkçe harfe KOMŞU
    hâlleri (`HALİ`, `TERİM`) kapattı — tek başına büyük harfle yazılmış hâlleri değil.

    HÜKÜM: aday ancak AYNI SATIRDA bir bağlam çapası varsa (`$`, fiyat biçimi, "sembol"
    kelimesi) ya da satırın KAYNAK künyelerinde geçiyorsa sembol sayılır; aksi hâlde `belirsiz`
    kovasına gider — ölçülemeyen değer uydurma DEĞİLDİR (uydurma yasağı)."""
    for cumle in ("DAL kapandı, kartı KALDI olarak işaretledim.",
                  "HAL hazırda bekliyoruz.", "TER dökmeden olmaz."):
        out = sohbet.cikti_atiflari(cumle, capa_gerek=True)
        assert out["sembol"] == [], (cumle, out["sembol"])
    belirsiz = sohbet.belirsiz_semboller("DAL kapandı, kartı KALDI olarak işaretledim.",
                                         capa_gerek=True)
    assert "DAL" in belirsiz, belirsiz


def test_CAPALI_aday_sembol_sayilir_ve_belirsiz_kovasindan_CIKAR():
    """Üç çapa da ÖLÇÜLÜR: `$` öneki · fiyat biçimi · "sembol" kelimesi. Çapalı aday `belirsiz`
    kovasına DÜŞMEZ (iki kova AYRIKTIR, aksi hâlde aynı atıf iki kez sayılırdı)."""
    for cumle, beklenen in (("$HAL 12.5 seviyesinde", "HAL"),
                            ("DAL 47.20 kapanışı", "DAL"),
                            ("sembol: TER", "TER")):
        out = sohbet.cikti_atiflari(cumle, capa_gerek=True)
        assert out["sembol"] == [beklenen], (cumle, out["sembol"])
        assert beklenen not in sohbet.belirsiz_semboller(cumle, capa_gerek=True), cumle


def test_KAYNAK_kunyesi_de_capadir_satirin_kendi_sorgusu():
    """Model bir sembolü GERÇEKTEN sorgulamışsa satırın `kaynaklar` künyesi onu taşır; o hâlde
    cevaptaki düz yazımı da sembol saymak DOĞRUdur (araç çıktısı zaten paydadadır)."""
    cumle = "DAL kapandı."
    assert sohbet.cikti_atiflari(cumle, capa_gerek=True)["sembol"] == []
    out = sohbet.cikti_atiflari(cumle, capa_gerek=True, ek_capa="bar_sorgu / DAL 2026-09")
    assert out["sembol"] == ["DAL"], out["sembol"]
    assert sohbet.belirsiz_semboller(cumle, capa_gerek=True,
                                     ek_capa="bar_sorgu / DAL 2026-09") == []


def test_capa_kapisi_PAYDA_tarafinda_KAPALIDIR_asimetri_BEYANLIDIR():
    """ASİMETRİ BİLEREKTİR VE YÖNÜ ÖLÇÜLÜDÜR. Araç çıktısı `indent=1` ile basılan JSON'dur ve
    sembol kendi satırında, fiyatından AYRI durur (`"ticker": "HAL",`). Çapa kuralı PAYDA
    tarafında da koşsaydı sembol paydadan düşer, cevaptaki ÇAPALI yazımı ("$HAL 12.5") dayanaksız
    görünür ve SAHTE bir uydurma doğardı. Payda GENİŞ kalır (yanlış pozitif üretmez), pay DAR
    olur — `capa_gerek` varsayılan olarak KAPALIDIR ve yalnız sayaç cevap tarafında açar."""
    json_satirlari = '{\n "son_planlar": [\n  {\n   "ticker": "HAL",\n   "score": 0.72\n  }\n ]\n}'
    assert sohbet.cikti_atiflari(json_satirlari)["sembol"] == ["HAL"], "payda daraldı"
    # MUTASYON İZİ: kapı açıkken AYNI metinde sembol DÜŞER — kapının gerçekten iş yaptığının kanıtı.
    assert sohbet.cikti_atiflari(json_satirlari, capa_gerek=True)["sembol"] == []
    assert sohbet.cikti_atiflari("DAL kapandı.")["sembol"] == ["DAL"], "payda daraldı"


# =================================================================================================
# 9) BEDEL — POST UCU DA ATIF KÜMESİNİ SERVİS ETMEZ (yeniden inceleme, 2026-09-08)
# =================================================================================================
def test_POST_api_sohbet_yaniti_da_cikti_atiflarini_TASIMAZ_defter_TASIR(kum, monkeypatch):
    """ÜÇ ŞEKİL OLMAZ. Tur-2'de alan `gecmis`ten (GET) çıkarıldı ama `POST /api/sohbet` ham satırı
    döndürmeye devam ediyordu: dosya (alan VAR) · GET (alan YOK) · POST (alan VAR). Aynı nesnenin
    iki ucu iki şey diyorsa pano hangi tazelemede ne göreceğini bilemez; bedel de POST'ta ödenir
    (tur başına 4 sınıf × 200 dizgeye kadar, HER mesaj yanıtında)."""
    from fastapi.testclient import TestClient

    from meridian import api, store

    monkeypatch.setattr(api, "DASH_TOKEN", None)
    araclar = dict(sohbet.ARACLAR)
    araclar["sahte_oku"] = _sahte_arac("sahte_oku", "T00001 12.5")
    monkeypatch.setattr(sohbet, "ARACLAR", araclar)
    monkeypatch.setattr(sohbet, "_kapi_cagir",
                        SahteModel(_arac(_tc("sahte_oku", {})), _metin("cevap")))

    r = TestClient(api.app).post("/api/sohbet", json={"mesaj": "soru", "oturum": "S1"})
    assert r.status_code == 200, r.text
    govde = r.json()
    assert govde["turlar"], govde
    assert "cikti_atiflari" not in govde["turlar"][0], govde["turlar"][0]
    # DEFTER TAŞIR (sayaç oradan okur) ve GET ile POST AYNI ŞEKLİ döner.
    ham = [x for x in store.read_jsonl(sohbet.SOHBET_DEFTERI) if isinstance(x, dict)][-1]
    assert ham["turlar"][0]["cikti_atiflari"]["kimlik"] == ["T00001"], ham["turlar"]
    assert "cikti_atiflari" not in sohbet.gecmis("S1")[-1]["turlar"][0]
