"""v486 — DENETÇİ KAPI ÇAĞRISI: reasoning kipi · 200-içinde-error gövdesi · çağrı ölçümü
(TSK-138 dilim-3, 2026-09-14).

ÖLÇÜLEN ARIZA (A1, 2026-09-14 — Rol-1 ölçtü, bu dosya ölçmez, ÇİVİLER). Bekçi 10:03Z koşumu:
`brifing_kural_denetimi` hukum=denetlenemedi · kaynak=llm_dustu · cagri_n=3, gerekçe
ReadTimeout. Kapı günlüğü aynı koşum için 75,5 s ve 138,7 s iki istek gösteriyor: birincil
örnek 0,3-0,4 s'de 429 verdi ("shared pool"), kapı yedeğe düştü, İSTEMCİ 120 s'de vazgeçti,
kapı isteği 138 s'de 200 ile bitirdi — boşa giden bir çağrı, ve denetim HİÇ yapılmadı.

İKİ AYRI SINIF, İKİ AYRI ÇİVİ KÜMESİ:

  (A/C) MUHAKEME BÜTÇESİ. Kontrollü ölçüm (aynı rota, aynı SOUL sistemi, 3.476 istem jetonu):
        varsayılan → 1.252 muhakeme jetonu / 30 s · reasoning kapalı → 24 jeton / 1,4 s, temiz
        JSON · muhakeme tavanı 400 → 6,7 s ama gerçek olay adlarını "uydurma" saydı (yani bir
        ORTA yol denendi ve ÖLÇÜLDÜ, seçilmedi). Karar: muhakeme VARSAYILAN OLARAK KAPALI,
        ortam değişkeniyle geri alınabilir. BEDEL: muhakemesiz denetçi "uydurma" sınıfını daha
        az yakalayabilir — bu yüzden C-serisi çağrı ölçümünü çiviler: kazanç (süre/jeton)
        ölçülüyorsa bedel de ölçülebilir olmalı, yoksa körlük sessizdir.

  (B) HTTP 200 İÇİNDE HATA GÖVDESİ. OpenRouter, üst-akımın "Service temporarily overloaded"
      hatasını 200 gövdesinde '{"error": {"code": 502, …}}' olarak döndürüyor ve "choices"
      HİÇ GELMİYOR. Kapının kendi yedekleme koşulu ("http_429"/"http_5xx") bunu GÖREMEZ, çünkü
      taşıyıcı durum kodu 200'dür. Bugünkü kodda bu gövde "kapı 200 döndü ama içerik YOK"
      hatasına, oradan `llm_dustu`ya düşüyordu — 09-05/06'nın "cevap JSON değil" sınıfının kökü
      budur ve hüküm YANLIŞ SINIFTAN okunuyordu: sorun denetçinin cevabı değil, üst-akımın hiç
      cevap vermemesiydi. Karar: hata ADIYLA deftere yazılır + TEK yeniden deneme.

YENİDEN DENEME SAYISI 1'DİR VE BU BİR DÖNGÜ DEĞİLDİR (CLAUDE.md §7 ayrımı). Yasak olan şey
KENDİ KURDUĞUN YOKLAMA DÖNGÜSÜDÜR; burada tek bir sınırlı bekleme ve tek bir tekrar vardır,
üçüncü çağrı ASLA yapılmaz. B2 tam olarak bunu ölçer: sahte kapı TAM 2 kez çağrılır.

GERÇEK KAPIYA İSTEK YOK (v455 sözleşmesi): her HTTP `httpx.post` saplamasıyla ölçülür ve
gerçek sır hiçbir yere girmez. YARDIMCILAR v385/v455'TEN İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak
yasası) — sahte profil evi, sahte kapı kuyruğu ve `@sef` kurulumu TEK yerde durur.
"""
from __future__ import annotations

import copy
import time as _gercek_zaman

import httpx
import pytest

from ops import denetci_rota
from tests.test_soul_denetimi_rota_v455 import (  # tek-kaynak: sahte kapı/profil TEK yerde
    SAHTE_KAPI_ANAHTARI, _Kapi, _config_yaz, _kapi_govdesi, _sirala, kurulum, sd)
from tests.test_soul_denetimi_v385 import _Kuyruk, _olaylar, _profil_evi, _temiz_cevap

# BOT ÖNEKİ BİLEREK SENTETİK: olay adlarının önekten ÜRETİLDİĞİ (bir bota gömülü OLMADIĞI)
# bu dosyanın her olay çivisinde kendiliğinden ölçülür — gerçek bir bot adı kullanılsaydı
# "önek taşınıyor mu" sorusu tesadüfen yeşil kalabilirdi.
ONEK = "v486bot"


class _Zaman:
    """`ops/denetci_rota.py`nin `time` bağlaması — `sleep` ÖLÇÜLÜR, `monotonic` GERÇEKTİR.

    NEDEN MODÜL BAĞLAMASI, GLOBAL YAMA DEĞİL: stdlib'in `sleep`ini yamamak bu testin dışındaki
    her şeyi de (httpx, pytest iç yolları) etkilerdi. `monotonic` gerçek kalır, çünkü ölçülen
    alan (`sure_sn`) SAHTE bir saatten değil gerçek bir farktan gelmeli — sahte saat, ölçüm
    aletinin kendisini sınanmaz yapardı."""

    def __init__(self):
        self.uykular: list[float] = []

    def sleep(self, sn):
        self.uykular.append(sn)

    @staticmethod
    def monotonic():
        return _gercek_zaman.monotonic()


@pytest.fixture
def zaman(monkeypatch):
    z = _Zaman()
    monkeypatch.setattr(denetci_rota, "time", z)
    return z


@pytest.fixture
def rota(tmp_path, monkeypatch, sandbox_state):
    """Kapı rotası KURULU bir `DenetciRota` — sahte profil evi, sahte anahtar, temiz ortam.

    Ortam değişkenleri BİLEREK silinir: bu dosyanın hiçbir çivisi operatörün kabuğunda ne
    olduğuna bağlı olamaz (varsayılan davranışı ölçen A1 tam da o bağımlılıkta sessizce
    yeşil kalırdı)."""
    ev = _config_yaz(_profil_evi(tmp_path, "sef"))
    from meridian import secrets as _secrets
    monkeypatch.setattr(_secrets, "get",
                        lambda ad: SAHTE_KAPI_ANAHTARI if ad == "KAPI_APIKEY" else None)
    monkeypatch.delenv(denetci_rota.DENETIM_ROTA_ENV, raising=False)
    monkeypatch.delenv(denetci_rota.DENETIM_REASONING_ENV, raising=False)
    return denetci_rota.DenetciRota(profil_evi=ev, profil_cagir=lambda p: "PROFIL:" + p,
                                    olay_oneki=ONEK, model_timeout_s=120)


def _kapiyi_bagla(monkeypatch, *govdeler) -> _Kapi:
    kapi = _Kapi(*govdeler)
    monkeypatch.setattr(httpx, "post", kapi)
    return kapi


def _jetonlu(metin="METİN", *, prompt=3476, completion=24, reasoning=None,
             model="sahte/cevaplayan:free"):
    """`usage` bloğu TAŞIYAN kapı gövdesi. `reasoning=None` → "completion_tokens_details" BOŞ
    (alanın hiç gelmediği gerçek durum: muhakemesiz modeller bu ayrıntıyı yazmaz)."""
    g = _kapi_govdesi(metin, model=model)
    ayrinti = {} if reasoning is None else {"reasoning_tokens": reasoning}
    g["usage"] = {"prompt_tokens": prompt, "completion_tokens": completion,
                  "completion_tokens_details": ayrinti}
    return g


def _ustakim_govdesi(kod=502, mesaj="Provider returned error: Service temporarily overloaded"):
    """HTTP 200 + "error" + "choices" YOK — ölçülmüş OpenRouter/Nvidia gövdesinin asgarisi."""
    return {"error": {"code": kod, "message": mesaj}, "model": "sahte/cevaplayan:free"}


def _olcum():
    return _olaylar(f"{ONEK}_denetci_cagri")


# ================================================================================================
# A) REASONING KİPİ — VARSAYILAN KAPALI, ORTAMLA GERİ ALINABİLİR
# ================================================================================================

def test_A1_VARSAYILAN_MUHAKEME_KAPALI(rota, monkeypatch, zaman):
    """Ortamda hiçbir şey yokken gövde muhakemeyi KAPATIR.

    BEKLENEN DEĞER BİLEREK LİTERALDİR — üretim sabitinden TÜRETİLMEZ. Bu, v455 D5'in
    "sayıyı tekrarlama" dersinin İSTİSNASIDIR ve istisna ölçülebilir: `{"enabled": False}`
    bir depo-içi sayı değil, OpenRouter'ın TEL SÖZLEŞMESİDİR. Sabitten türetilen bir beklenti
    A5'in mutasyonuyla birlikte KAYAR ve çivi kendi hedefini kaybederdi (mutasyon bölümüne bak).

    Kazanç ölçüldü: aynı istemde 1.252 muhakeme jetonu / 30 s → 24 jeton / 1,4 s."""
    kapi = _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))
    assert rota.cagir("soru") == "METİN"
    assert kapi.cagrilar[0]["json"]["reasoning"] == {"enabled": False}, kapi.cagrilar[0]["json"]


def test_A2_ORTAMLA_DUSUK_MUHAKEMEYE_CEVRILIR(rota, monkeypatch, zaman):
    """ORTA YOL DAĞITIMSIZ AÇILABİLİR: 'dusuk' kipi muhakemeyi kapatmaz, KISAR.

    Ölçümde muhakeme tavanı denemesi (400 jeton) gerçek olay adlarını "uydurma" saydı; eğer
    kapalı kip denetim kalitesini düşürürse geri dönüş yolu iki uç arasında bir ara basamak
    olmalı — yoksa tek geri alma 30 saniyelik çağrıya dönmek olurdu."""
    monkeypatch.setenv(denetci_rota.DENETIM_REASONING_ENV, "dusuk")
    kapi = _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))
    rota.cagir("soru")
    assert kapi.cagrilar[0]["json"]["reasoning"] == {"effort": "low"}, kapi.cagrilar[0]["json"]


def test_A3_ACIK_KIPINDE_ALAN_HIC_YAZILMAZ(rota, monkeypatch, zaman):
    """TAM GERİ ALMA: 'acik' bu turdan ÖNCEKİ gövdeyi geri getirir — alan EKLENMEZ.

    `{"enabled": True}` yazmak geri alma DEĞİLDİR: sağlayıcının varsayılanı bir gün değişirse
    "açık" kipi artık eski davranış olmazdı. Alanın HİÇ olmaması tek dürüst geri dönüştür."""
    monkeypatch.setenv(denetci_rota.DENETIM_REASONING_ENV, "acik")
    kapi = _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))
    rota.cagir("soru")
    assert "reasoning" not in kapi.cagrilar[0]["json"], kapi.cagrilar[0]["json"]


def test_A4_TANINMAYAN_KIP_ADIYLA_KAYDA_GECER_VE_VARSAYILANA_DUSER(rota, monkeypatch, zaman):
    """Yazım hatası SESSİZ bir davranış değişikliği olamaz (Yasa 4) — rota kipinin AYNI deseni.

    `SOUL_DENETIM_REASONING=kapalı` (Türkçe ı) yazan bir operatör bugün hiçbir uyarı almadan
    varsayılanda kalırdı; kayıt olmadan bu ayrım ölçüm gecelerini sessizce bozardı ("kapattım"
    sanılan bir koşum aslında hangi kipte gitti?)."""
    monkeypatch.setenv(denetci_rota.DENETIM_REASONING_ENV, "kapalı")
    kapi = _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))
    rota.cagir("soru")
    assert kapi.cagrilar[0]["json"]["reasoning"] == {"enabled": False}, kapi.cagrilar[0]["json"]
    olaylar = _olaylar(f"{ONEK}_denetci_reasoning_taninmadi")
    assert olaylar, "tanınmayan kip ADIYLA deftere yazılmadı"
    assert olaylar[-1].get("deger") == "kapalı", olaylar[-1]


def test_A5_MUTASYON_VARSAYILAN_KIP_KAYARSA_A1_BEKLENTISI_TUTMAZ(rota, monkeypatch, zaman):
    """A1'İN ISIRDIĞININ KANITI, ÇİVİNİN İÇİNDE (çivi yeşili kanıt değildir).

    Varsayılan kip 'acik'a çevrildiğinde A1'in beklediği gövde ARTIK ÜRETİLMEZ. Mutasyon
    kaynak metnine değil sabite uygulanır (monkeypatch): kaynak-metin mutasyonu `.pyc`
    bayatlığı sınıfına açıktır ve aynı saniyede geri alınan bir düzenleme sessizce eski
    bayt kodunu geçerli bırakır."""
    monkeypatch.setattr(denetci_rota, "VARSAYILAN_DENETIM_REASONING", "acik")
    kapi = _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))
    rota.cagir("soru")
    govde = kapi.cagrilar[0]["json"]
    assert govde.get("reasoning") != {"enabled": False}, govde
    assert "reasoning" not in govde, govde


# ================================================================================================
# B) HTTP 200 İÇİNDE HATA GÖVDESİ — ADIYLA OLAY + TEK YENİDEN DENEME
# ================================================================================================

def test_B1_ERROR_GOVDESI_OLAY_YAZAR_VE_TEK_KEZ_YENIDEN_DENER(rota, monkeypatch, zaman):
    """Üst-akım hatası ADIYLA görünür ve İKİNCİ çağrı denetimi KURTARIR.

    Bugünkü kodda bu gövde "içerik YOK" hatasına düşüyordu: defterde denetçinin cevabı bozuk
    görünüyor, gerçekte üst-akım hiç cevap vermemişti. İki sınıf tek ada çöktüğü sürece hangi
    tarafın onarılacağı okunamaz."""
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(), _jetonlu("SAĞLAM METİN"))
    assert rota.cagir("soru") == "SAĞLAM METİN"
    assert len(kapi.cagrilar) == 2, kapi.urller
    olaylar = _olaylar(f"{ONEK}_denetci_ustakim_hatasi")
    assert olaylar, "üst-akım hatası ADIYLA deftere yazılmadı"
    assert olaylar[-1].get("kod") == 502, olaylar[-1]
    assert _olcum()[-1].get("yeniden_deneme") == 1, _olcum()[-1]


def test_B2_IKISI_DE_ERROR_ISE_UCUNCU_CAGRI_ASLA_YAPILMAZ(rota, monkeypatch, zaman):
    """YENİDEN DENEME SAYISI 1'DİR — bu bir döngü değil, SINIRLI ve TEK bir tekrardır.

    Kotasız bir yüzeyde "birkaç kez daha dene" operatörün bütçesini sessizce yakar; üstelik
    üst-akım doluyken ısrar etmek kuyruğu uzatır. Üçüncü çağrı olsaydı sahte kapı zaten
    patlardı, ama SAYI AÇIKÇA ölçülür: sessizce artan bir tavan çiviyi geçerdi."""
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(), _ustakim_govdesi(kod=503))
    with pytest.raises(RuntimeError) as hata:
        rota.cagir("soru")
    assert "üst-akım" in str(hata.value), str(hata.value)
    assert len(kapi.cagrilar) == 2, kapi.urller
    assert len(_olaylar(f"{ONEK}_denetci_ustakim_hatasi")) == 2, "iki düşüş de ADIYLA yazılmalı"


def test_B3_UST_AKIM_HATASI_TESLIMATI_DUSURMEZ(kurulum, monkeypatch, sd, zaman):
    """FAIL-OPEN SÖZLEŞMESİ DELİNMEZ: denetçi düşse de İLK metin gider (v385 D5).

    Yeni bir istisna sınıfı eklemek, teslimatı düşürmenin yeni bir yolunu eklemektir — bu çivi
    `soul_denetimi.gecir`in mevcut `llm_dustu` dalının bu sınıfı da yuttuğunu ölçer."""
    m, _ = kurulum
    monkeypatch.delenv(denetci_rota.DENETIM_REASONING_ENV, raising=False)
    kapi = _Kapi(_ustakim_govdesi(), _ustakim_govdesi())
    metin, kaynak = _sirala(m, monkeypatch, kapi)
    assert kaynak == "llm" and "MECHANISM_STALE" in metin, (kaynak, metin)
    assert _olaylar(sd.OLAY)[-1].get("kaynak") == "llm_dustu", _olaylar(sd.OLAY)[-1]
    assert _olaylar("sef_brifingi_denetci_ustakim_hatasi"), "olay BOT ÖNEKİYLE yazılmadı"


def test_B4_ERRORSUZ_BOS_CEVAP_YENIDEN_DENENMEZ(rota, monkeypatch, zaman):
    """"choices" boş ama "error" YOK → bu ÜST-AKIM arızası DEĞİLDİR, yeniden denenmez.

    Ayrım bedava değil: her yeniden deneme bir çağrıdır. Boş bir cevabı tekrar istemek aynı
    boş cevabı ikinci kez ödemektir — üst-akım hatası ise geçicidir ve tekrar İŞE YARAR."""
    kapi = _kapiyi_bagla(monkeypatch, {"choices": [], "model": "sahte/cevaplayan:free"})
    with pytest.raises(RuntimeError) as hata:
        rota.cagir("soru")
    assert "içerik YOK" in str(hata.value), str(hata.value)
    assert len(kapi.cagrilar) == 1, kapi.urller
    assert zaman.uykular == [], zaman.uykular
    assert not _olaylar(f"{ONEK}_denetci_ustakim_hatasi"), "üst-akım OLMAYAN gövde öyle sayıldı"


def test_B6_CEVABI_DA_HATAYI_DA_TASIYAN_GOVDE_SAGLAM_SAYILIR(rota, monkeypatch, zaman):
    """İKİ ŞARTIN İKİNCİSİ: `choices` GELDİYSE gövdedeki `error` bir DÜŞÜŞ değildir.

    MUTASYON TURUNUN BULDUĞU BOŞLUK (2026-09-14): B4 yalnız "error yok" tarafını ölçüyordu,
    yani `choices` koruması düşürüldüğünde hiçbir çivi kırılmıyordu. Sağlayıcılar kısmi
    gövdelerde (ör. yedeklenen bir akışın uyarısı) her iki alanı birden yazabilir; yalnız
    `error`a bakan bir kapı, ELİNDEKİ SAĞLAM CEVABI atıp ikinci bir çağrı öderdi."""
    govde = _kapi_govdesi("SAĞLAM METİN")
    govde["error"] = {"code": 502, "message": "yedeklenen akışın uyarısı"}
    kapi = _kapiyi_bagla(monkeypatch, govde)
    assert rota.cagir("soru") == "SAĞLAM METİN"
    assert len(kapi.cagrilar) == 1, kapi.urller
    assert zaman.uykular == [], zaman.uykular
    assert not _olaylar(f"{ONEK}_denetci_ustakim_hatasi"), "sağlam cevap üst-akım düşüşü sayıldı"


def test_B5_BEKLEME_TEK_ATIM_VE_SABITTEN(rota, monkeypatch, zaman):
    """Bekleme TEK ATIMDIR ve süresi ADLANDIRILMIŞ SABİTTEN gelir (CLAUDE.md §7).

    Süre testin içinde TEKRARLANMAZ, üretimden okunur: iki kopya sessizce ayrışır ve "5 sn
    bekliyoruz" cümlesi bir gün yalnız burada doğru kalırdı."""
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(), _kapi_govdesi("METİN"))
    rota.cagir("soru")
    assert zaman.uykular == [denetci_rota.USTAKIM_YENIDEN_DENEME_SN], zaman.uykular
    assert len(kapi.cagrilar) == 2, kapi.urller


# ================================================================================================
# C) ÇAĞRI ÖLÇÜMÜ — KAZANÇ VE BEDEL AYNI OLAYDAN OKUNUR
# ================================================================================================

def test_C1_BASARILI_CAGRI_SURE_VE_JETON_OLCUMU_YAZAR(rota, monkeypatch, zaman):
    """YASA 6 OKUYUCUSU: Rol-1'in TSK-138 ölçüm satırı (A1 `events.jsonl` grep'i) bu olayı okur.

    Muhakemeyi kapatmanın KAZANCI (süre, jeton) ile BEDELİ (denetim kalitesi) ancak yan yana
    okunabilirse karşılaştırılır; kazancı ölçüp bedeli ölçmemek körlüğün sessiz biçimidir."""
    _kapiyi_bagla(monkeypatch, _jetonlu(prompt=3476, completion=24, reasoning=0))
    rota.cagir("soru")
    o = _olcum()[-1]
    assert isinstance(o.get("sure_sn"), float) and o["sure_sn"] >= 0.0, o
    assert (o.get("prompt_tok"), o.get("completion_tok"), o.get("reasoning_tok")) == (3476, 24, 0), o
    assert o.get("cevaplayan_model") == "sahte/cevaplayan:free", o
    assert o.get("reasoning_kipi") == denetci_rota.VARSAYILAN_DENETIM_REASONING, o
    assert o.get("yeniden_deneme") == 0, o


def test_C2_USAGE_YOKSA_JETON_ALANLARI_NONE_SIFIR_DEGIL(rota, monkeypatch, zaman):
    """UYDURMA YASAĞI: ölçülemeyen jeton `None`dır. Sıfır "bedava çağrı" demektir — bir yalan.

    Ölçüm gecelerinin toplamı bu alanlardan alınacak; `0` yazan tek bir gövde, ortalamayı
    aşağı çeker ve muhakemesiz kipin kazancını OLDUĞUNDAN BÜYÜK gösterirdi."""
    _kapiyi_bagla(monkeypatch, _kapi_govdesi("METİN"))     # `usage` bloğu HİÇ YOK
    rota.cagir("soru")
    o = _olcum()[-1]
    assert (o.get("prompt_tok"), o.get("completion_tok"), o.get("reasoning_tok")) == (None,) * 3, o
    assert o.get("sure_sn") is not None, o                 # süre yine ÖLÇÜLÜR


def test_C3_SON_OLCUM_CAGRI_BASINDA_SIFIRLANIR(rota, monkeypatch, zaman):
    """BAYAT ÖLÇÜM SIZAMAZ (v455 B4 deseni): düşen bir çağrıdan sonra önceki turun ölçümü kalmaz.

    Tutucu sıfırlanmasaydı, düşen bir denetim defterde bir ÖNCEKİ çağrının süresi ve jetonuyla
    görünürdü: hiç yapılmamış bir ölçüm, yapılmış gibi okunurdu."""
    _kapiyi_bagla(monkeypatch, _jetonlu("METİN"))
    rota.cagir("soru")
    assert rota.son_olcum is not None and rota.son_olcum["cevaplayan_model"], rota.son_olcum
    _kapiyi_bagla(monkeypatch, RuntimeError("kapı düştü"))
    with pytest.raises(RuntimeError):
        rota.cagir("ikinci soru")
    assert rota.son_olcum is None, rota.son_olcum


def test_C4_UST_AKIM_MESAJI_SIR_SUZGECINDEN_GECER(rota, monkeypatch, zaman):
    """Üst-akım mesajı BİZİM YAZMADIĞIMIZ bir metindir ve deftere GİRER — süzgeçsiz olamaz.

    Gerçek bir vaka sınıfı: sağlayıcı hata metnine isteğin URL'ini gömer ve o URL sorgu
    parametresinde bir anahtar taşır. Süzgeç olmasaydı sır, kendi defterimize kendi elimizle
    yazılırdı (`meridian/notify.py` sır süzgecinin var oluş gerekçesi)."""
    sirli = "upstream https://ornek.invalid/v1?apikey=COK-GIZLI-DEGER-123 reddetti"
    _kapiyi_bagla(monkeypatch, _ustakim_govdesi(mesaj=sirli), _kapi_govdesi("METİN"))
    rota.cagir("soru")
    olay = _olaylar(f"{ONEK}_denetci_ustakim_hatasi")[-1]
    assert "COK-GIZLI-DEGER-123" not in str(olay), olay
    assert "apikey=***" in str(olay.get("mesaj")), olay


def test_C5_MESAJ_TAVANI_UYGULANIR_VE_SABITTEN_OKUNUR(rota, monkeypatch, zaman):
    """Üst-akım mesajı SINIRSIZ uzunlukta olabilir ve defteri şişirir — tavan ÜRETİMDEN okunur."""
    _kapiyi_bagla(monkeypatch, _ustakim_govdesi(mesaj="x" * 500), _kapi_govdesi("METİN"))
    rota.cagir("soru")
    olay = _olaylar(f"{ONEK}_denetci_ustakim_hatasi")[-1]
    assert len(str(olay.get("mesaj"))) == denetci_rota.USTAKIM_MESAJ_TAVANI, olay


# ================================================================================================
# D) BÜTÇE — YENİDEN DENEME AYNI SÖZLEŞMEDE KALIR
# ================================================================================================

def test_D1_YENIDEN_DENEME_AYNI_BUTCEYI_VE_AYNI_GOVDEYI_TASIR(rota, monkeypatch, zaman):
    """İkinci çağrı BİRİNCİNİN AYNISIDIR: aynı rota, aynı gövde, aynı 120 sn bütçe.

    v455 D1 bütçeyi İLK çağrı için çiviliyor; yeniden deneme o çivinin KÖR NOKTASIDIR — ikinci
    çağrı sessizce bütçesiz (ya da farklı bir gövdeyle) gitseydi hiçbir mevcut çivi kırılmazdı.
    Sayı burada da TEKRARLANMAZ, örnekten okunur.

    GÖVDE GÖNDERİM ANINDA KOPYALANIR — MUTASYON TURUNUN BULDUĞU İKİNCİ BOŞLUK (2026-09-14):
    `_Kapi` çağrı sözlüğünü REFERANSLA saklar, yani iki kayıttaki "json" AYNI NESNEDİR ve
    `ikinci == ilk` karşılaştırması üretim gövdeyi araya girip DEĞİŞTİRSE BİLE doğru çıkardı
    (boş bir çivi). Anlık görüntü olmadan bu satır hiçbir şey ölçmüyordu."""
    kapi = _Kapi(_ustakim_govdesi(), _kapi_govdesi("METİN"))
    goruntuler: list[dict] = []

    def _arsivle(url, **kw):
        goruntuler.append(copy.deepcopy(kw["json"]))
        return kapi(url, **kw)

    monkeypatch.setattr(httpx, "post", _arsivle)
    rota.cagir("soru")
    ilk, ikinci = kapi.cagrilar
    assert ikinci["url"] == ilk["url"], (ilk["url"], ikinci["url"])
    assert goruntuler[1] == goruntuler[0], goruntuler
    assert ikinci["timeout"] == rota.model_timeout_s == ilk["timeout"], ikinci["timeout"]


def test_D2_PROFIL_YOLUNDA_HIC_MUHAKEME_ALANI_URETILMEZ(rota, monkeypatch, zaman):
    """Rota `profil`e alındığında bu turun HİÇBİR parçası koşmaz — geri alma TAM olmalı.

    Kip okuma, ölçüm olayı ve yeniden deneme kapı gövdesine bağlıdır; hermes yolunda gövde
    YOKTUR ve bu yolda üretilecek bir ölçüm "yapılmamış bir çağrının ölçümü" olurdu."""
    monkeypatch.setenv(denetci_rota.DENETIM_ROTA_ENV, "profil")
    _kapiyi_bagla(monkeypatch)                     # tek HTTP çağrısında patlar
    assert rota.cagir("soru") == "PROFIL:soru"
    assert _olcum() == [], _olcum()
    assert rota.son_olcum is None, rota.son_olcum


def test_D3_DUSUS_YOLUNDA_DA_OLCUM_URETILMEZ(tmp_path, monkeypatch, sandbox_state, zaman):
    """Kapı ölçülemeyip hermes'e DÜŞÜLDÜĞÜNDE de ölçüm yoktur (uydurma yasağı).

    `_Kuyruk` sahte profil çağrısıdır: düşüş yolunun GERÇEKTEN sürüldüğünü kuyruğun sayacı
    ölçer, dönen dizge değil."""
    kuyruk = _Kuyruk("PROFIL-METNI")
    r = denetci_rota.DenetciRota(profil_evi=tmp_path, profil_cagir=kuyruk,   # config.yaml YOK
                                 olay_oneki=ONEK, model_timeout_s=120)
    monkeypatch.delenv(denetci_rota.DENETIM_ROTA_ENV, raising=False)
    _kapiyi_bagla(monkeypatch)
    assert r.cagir("soru") == "PROFIL-METNI" and kuyruk.n == 1, kuyruk.n
    assert _olcum() == [], _olcum()
    assert r.son_olcum is None, r.son_olcum


def test_D4_TEMIZ_CEVAP_HALA_DENETIMDEN_GECER(kurulum, monkeypatch, sd, zaman):
    """POZİTİF KONTROL: üç kazanımın hiçbiri MUTLU YOLU kırmadı — temiz metin AYNEN teslim edilir.

    Üç davranış birden ekleyen bir tur için en pahalı gerileme biçimi, denetimin sessizce
    kapanmasıdır: bütün B/C çivileri yeşilken teslimat yolu ölmüş olabilirdi."""
    m, _ = kurulum
    monkeypatch.delenv(denetci_rota.DENETIM_REASONING_ENV, raising=False)
    metin, kaynak = _sirala(m, monkeypatch, _Kapi(_jetonlu(_temiz_cevap())))
    assert (kaynak, "MECHANISM_STALE" in metin) == ("llm", True), (kaynak, metin)
    assert _olaylar("sef_brifingi_denetci_cagri"), "ölçüm olayı BOT ÖNEKİYLE yazılmadı"
