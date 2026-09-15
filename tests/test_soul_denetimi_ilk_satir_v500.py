"""BRİFİNG SOUL DENETÇİSİ — TESLİM EDİLEN METNİN İLK SATIRI (v500, TSK-138 dilim-4, 2026-09-15).

ÖLÇÜLEN BOŞLUK (A1, olay `brifing_kural_denetimi`, 2026-09-15 10:05Z). Bekçi ve şef brifinglerinde
denetim iki turda da "ilk satır sade tek cümle DEĞİL" ihlalini bırakıp HAM teslim veriyor. Defterde
o hükmün YANINDA hükmün KONUSU yok: `cevap_bas` DENETÇİNİN cevabıdır, teslim edilen BRİFİNGİN ilk
satırı hiçbir yere yazılmıyor ve teslimat yalnız Telegram'a gidiyor. Yani kalan ihlalin gerçek mi
yanlış-pozitif mi olduğu SORULAMIYOR: bedel (ham teslim) ölçülüyor, kazanç ölçülmüyor — bedel
yasasının tam tersi hâli.

BU DOSYA BİR DÜZELTME ÇİVİLEMEZ, BİR ÖLÇÜM ALETİ ÇİVİLER. Denetçi istemi, şema, `cevap_bas`/
`cevaplayan_model` sözleşmeleri ve damga okuyucusu bu turda HİÇ DEĞİŞMEZ; eklenen tek şey olaya
giden `brifing_ilk_satir` alanıdır.

DÖRT SINIF ÇİVİLENİR:
  1. TESLİM EDİLEN metnin ilk BOŞ OLMAYAN satırı — "teslim edilen" sözleşmedir: bir yeniden-üretim
     olduğunda alan İKİNCİ metnin satırıdır, ilk turunki DEĞİL. Ters olsaydı defter operatöre
     GİTMEYEN bir metni gösterir ve yanlış-pozitif sorusu tam ters yönde cevaplanırdı.
  2. `None` ile `""` AYRI BİLGİDİR (uydurma yasağı, `cevap_bas` emsali): `None` "teslim edilen
     metin YOK" (ham dal · boş metin), `""` "metin VAR ama dolu satırı yok". İkisini tek değere
     katlamak, ham teslim edilen bir turu boş brifing sanmaktır.
  3. TAVAN + KATLAMA — alan bir teşhis alanıdır, bir sızıntı yüzeyi değil. Sıra ÖLÇÜLÜR: önce
     katla, sonra kırp (`cevap_bas` ile AYNI gerekçe, pencere boşluğa harcanmaz).
  4. SIR SÜZGECİ ve SIRASI — brifing metni model çıktısıdır ve bir hata dizgesi taşıyabilir.
     Süzgeç KIRPMADAN ÖNCE koşar: tersi, tavanın ortasından kesilen bir anahtarı desene
     uymaz hâle getirip HAM ÖNEKİNİ deftere yazardı (v467 desenlerinin sessizce delinmesi).

YASA 6 — OKUYUCU: `ops/olay_sorgu.py --sql` ile HAFTALIK SINIFLAMA, mevcut `ilk_ihlal`/`suzulen`
alanlarıyla AYNI yüzey ("kalan ihlalin konusu neydi" sorusu bu alandan cevaplanır). O okuyucu
defteri okuduğu için alanın GERÇEKTEN `events.jsonl`e serileştirildiği de ayrıca çivilenir —
yalnız `obs.log`a geçilmiş bir değer, okuyucusu olmayan bir değerdir.

YARDIMCILAR KOPYALANMAZ, İTHAL EDİLİR (tek-kaynak yasası): sahte profil evi/kuyruk/cevaplar v385'te,
`obs.log` yakalayıcısı v434'tedir. Kopyalansalardı o sözleşmeler değiştiğinde bu dosya ölçtüğünü
sandığı şeyi ölçmez olurdu.

ÖLÇÜLMEDİ, BEYAN EDİLİYOR: gerçek hermes profili ÇAĞRILMADI (ajan canlıya dokunmaz). Buradaki her
LLM davranışı sapla ölçülür — sınanan MODELİN cevabı değil, KOŞUMUN o cevaba verdiği tepkidir.
"""
from __future__ import annotations

import importlib

import pytest

from tests.test_soul_denetimi_teshis_v434 import _ObsYakala   # tek-kaynak: obs saplaması v434'te
from tests.test_soul_denetimi_v385 import (  # tek-kaynak: sahte profil/kuyruk/cevaplar v385'te
    _Kuyruk, _ihlalli_cevap, _olaylar, _profil_evi, _temiz_cevap)

# ALAN ADI TEK YERDE. Dizge her çiviye ayrı ayrı yazılsaydı, bir gün alan yeniden adlandırıldığında
# bazı çiviler sessizce `None` ölçmeye devam ederdi (ölçtüğünü sanan çivi sınıfı).
ALAN = "brifing_ilk_satir"

# SAHTE SIR — GERÇEK DEĞİL, ve bir SIR DEĞERİNE değil bir SIR BİÇİMİNE bağlıdır: `notify.scrub`ın
# desen katmanı (`openrouter`) 64 onaltılık karakterlik OpenRouter biçimini tanır. `secrets.get`
# saplamasına gerek YOKTUR — desen katmanı bilinen-değer katmanından bağımsız koşar.
SAHTE_ANAHTAR = "sk-or-v1-" + "a" * 64
# Aynı süzgecin İKİNCİ katmanı: env/birim dökümü satırı. Önek listesi beyanlıdır (`OPENROUTER…`),
# öneksiz bir ad bu katmandan GEÇER — sınır v467'de çivilidir, burada kopyalanmaz.
SAHTE_ENV_SATIRI = "OPENROUTER_API_KEY=abcdefgh12345678"


@pytest.fixture
def sd():
    return importlib.import_module("ops.soul_denetimi")


def _kos(sd, tmp_path, monkeypatch, kuyruk, ilk_metin, **kw):
    """`obs.log` saplanmış TEK bir `gecir` koşumu; (gecis, yakalayıcı) döner.

    NEDEN SAPLAMA: bu çivilerin çoğu `None` ile `""` ayrımını ölçer ve o ayrım serileştirmeden
    ÖNCE kurulur. Defterden okunsaydı, alanın hiç yazılmadığı hâl ile `None` yazıldığı hâl aynı
    görünürdü. Serileştirmenin kendisi AYRI bir çiviyle (Yasa 6 okuyucusu) ölçülür."""
    yakala = _ObsYakala()
    monkeypatch.setattr(sd.obs, "log", yakala)
    g = sd.gecir(profil_evi=_profil_evi(tmp_path), ilk_metin=ilk_metin, ilk_istem="İLK İSTEM",
                 veri_terimleri=[], cagir=kuyruk, bot="sef", **kw)
    return g, yakala


def _alanlar(yakala, sd) -> dict:
    """Olayın TÜM kwarg sözlüğü — `alan()` yardımcısı alanın VARLIĞINI ölçemez (yokluk da `None`
    döner), bazı çiviler tam olarak onu sorar."""
    for olay, alanlar in yakala.cagrilar:
        if olay == sd.OLAY:
            return dict(alanlar)
    raise AssertionError(f"`{sd.OLAY}` olayı hiç yazılmadı: {[o for o, _ in yakala.cagrilar]}")


# ================================================================================================
# T1 — TESLİM EDİLEN METNİN İLK SATIRI OLAYA YAZILIR
# ================================================================================================

def test_T1_TESLIM_EDILEN_ILK_SATIR_OLAYA_KATLANMIS_YAZILIR(sd, tmp_path, monkeypatch,
                                                            sandbox_state):
    """Boşluğun ölçtüğü şeyin ta kendisi: hüküm defterde vardı, hükmün KONUSU yoktu. İki satırlı
    bir brifingde alan İLK satırı taşır ve boşlukları katlanmıştır (defterin tek-satır JSONL
    biçimi korunur)."""
    metin = "Bugün  üç   kalem\tvar\nikinci satır: ayrıntılar burada"
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), metin)
    assert g.metin == metin, f"kurulum yanlış — temiz hükümde metin teslim edilmedi: {g!r}"
    alanlar = _alanlar(yakala, sd)
    assert ALAN in alanlar, f"olayda `{ALAN}` alanı HİÇ yok: {sorted(alanlar)}"
    assert alanlar[ALAN] == "Bugün üç kalem var", (
        f"ilk satır yazılmadı ya da boşluklar katlanmadı: {alanlar[ALAN]!r}")


def test_T1B_IHLAL_LISTESI_VE_HUKUM_ETKILENMEZ(sd, tmp_path, monkeypatch, sandbox_state):
    """Alan SALT OKUR bir teşhis künyesidir: hiçbir dal ona bakarak karar vermez. Ekleme hükmü ya
    da ihlal listesini kımıldatsaydı, ölçüm aleti ölçtüğü şeyi değiştirmiş olurdu."""
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), "tek satırlık brifing")
    alanlar = _alanlar(yakala, sd)
    assert alanlar["hukum"] == "temiz" and alanlar["kaynak"] == "llm", f"hüküm kaydı: {alanlar!r}"
    assert alanlar["ihlal"] == [] and alanlar["ilk_ihlal"] == [], (
        f"ihlal listesi etkilendi: {alanlar!r}")
    assert g.beyan == "", f"beyan satırı kirlendi: {g.beyan!r}"


def test_T1C_BASTAKI_BOS_SATIRLAR_ATLANIR(sd, tmp_path, monkeypatch, sandbox_state):
    """"İlk satır" DOLU ilk satırdır. Ham `splitlines()[0]` alınsaydı, başında bir boş satır olan
    her brifing defterde `""` görünür ve "ilk satır sade tek cümle DEĞİL" ihlali hep konusuz
    kalırdı — tam da bu turun kapatmaya çalıştığı boşluk."""
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()),
                     "\n   \n  Dolu olan ilk satır  \nüçüncü satır")
    assert g.metin.startswith("\n"), "kurulum yanlış: metin baştaki boş satırı kaybetti"
    assert _alanlar(yakala, sd)[ALAN] == "Dolu olan ilk satır", (
        f"baştaki boş satırlar atlanmadı: {_alanlar(yakala, sd)[ALAN]!r}")


# ================================================================================================
# T2 — YENİDEN ÜRETİMDE ALAN İKİNCİ (TESLİM EDİLEN) METNİN SATIRIDIR
# ================================================================================================

def test_T2_YENIDEN_URETIMDE_ALAN_TESLIM_EDILEN_IKINCI_METINDENDIR(sd, tmp_path, monkeypatch,
                                                                   sandbox_state):
    """SÖZLEŞMENİN KALBİ. `ilk_ihlal` zaten İLK turu anlatır; bu alan TESLİM EDİLENİ anlatmalıdır.
    `ilk_metin`e bağlansaydı defter operatöre GİTMEYEN bir metnin ilk satırını gösterir ve
    "kalan ihlal yanlış-pozitif miydi" sorusu ters metinden cevaplanırdı."""
    ilk = "ilk turun bozuk ilk satırı\nikinci satır"
    yeni = "düzeltilmiş metnin ilk satırı\nyine ikinci satır"
    kuyruk = _Kuyruk(_ihlalli_cevap(), yeni, _temiz_cevap())
    g, yakala = _kos(sd, tmp_path, monkeypatch, kuyruk, ilk)
    assert (g.metin, g.yeniden_uretim) == (yeni, True), f"yeniden-üretim dalına girilmedi: {g!r}"
    alanlar = _alanlar(yakala, sd)
    assert alanlar[ALAN] == "düzeltilmiş metnin ilk satırı", (
        f"alan İLK turun metninden alındı (teslim edilen İKİNCİsiydi): {alanlar[ALAN]!r}")
    assert alanlar["ilk_ihlal"], "kurulum yanlış: ilk turda ihlal ölçülmemiş"


def test_T2B_DENETLENEMEYEN_IKINCI_METIN_DE_TESLIM_EDILENDIR(sd, tmp_path, monkeypatch,
                                                             sandbox_state):
    """BEŞİNCİ DAL (Ö-3): yeniden-üretim DENETLENEMEDİ ama düzeltilmiş metin GİTTİ. Alan giden
    metni göstermelidir — burada ilk metne düşmek, beyanın "düzeltilmiş metin gitti" cümlesiyle
    defterin İÇİNDE çelişmek olurdu."""
    yeni = "denetlenemeyen ama giden metin\nikinci"
    kuyruk = _Kuyruk(_ihlalli_cevap(), yeni, "şema dışı cevap")
    g, yakala = _kos(sd, tmp_path, monkeypatch, kuyruk, "ilk turun metni")
    assert g.metin == yeni and not g.hukum.olculdu, f"beşinci dala girilmedi: {g!r}"
    assert _alanlar(yakala, sd)[ALAN] == "denetlenemeyen ama giden metin", (
        f"giden metnin ilk satırı yazılmadı: {_alanlar(yakala, sd)[ALAN]!r}")


# ================================================================================================
# T3 — `None` ile `""` AYRI BİLGİDİR (uydurma yasağı)
# ================================================================================================

def test_T3_HAM_TESLIMDE_ALAN_NONE(sd, tmp_path, monkeypatch, sandbox_state):
    """2/2 ihlal → `metin is None`, yani TESLİM EDİLEN METİN YOKTUR. `""` yazmak "brifing gitti ve
    ilk satırı boştu" derdi; oysa brifing HİÇ gitmedi (bot HAM yoluna düştü)."""
    kuyruk = _Kuyruk(_ihlalli_cevap(), "yine bozuk metin", _ihlalli_cevap(("tetti", "zıpzıp")))
    g, yakala = _kos(sd, tmp_path, monkeypatch, kuyruk, "ilk metin")
    assert g.metin is None, f"kurulum yanlış — ham dala düşülmedi: {g!r}"
    alanlar = _alanlar(yakala, sd)
    assert ALAN in alanlar, f"ham dalda alan HİÇ yazılmadı: {sorted(alanlar)}"
    assert alanlar[ALAN] is None, f"teslimat yokken ilk satır uyduruldu: {alanlar[ALAN]!r}"


def test_T3B_BOS_METIN_NONE(sd, tmp_path, monkeypatch, sandbox_state):
    """SESSİZ tur (söylenecek bir şey yok): teslim edilen metin boş dizgedir ve bu "metin YOK"
    demektir. Boş bir brifingin "ilk satırı" diye bir şey ölçülmemiştir."""
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), "")
    assert g.metin == "", f"kurulum yanlış: {g!r}"
    assert _alanlar(yakala, sd)[ALAN] is None, (
        f"boş metin için ilk satır uyduruldu: {_alanlar(yakala, sd)[ALAN]!r}")


def test_T3C_METIN_VAR_AMA_DOLU_SATIRI_YOKSA_BOS_DIZGE(sd, tmp_path, monkeypatch, sandbox_state):
    """`""`in TEK meşru hâli: metin VAR (baytları var, Telegram'a gitti) ama tek bir dolu satırı
    yok. `None` yazılsaydı "teslimat olmadı" ile "teslimat oldu ama boştu" defterde ayırt
    edilemezdi — `cevap_bas`ın ölçülmüş ayrımının aynısı."""
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), "   \n\t \n  ")
    assert g.metin == "   \n\t \n  ", f"kurulum yanlış: {g!r}"
    assert _alanlar(yakala, sd)[ALAN] == "", (
        f"boşluk-metni `None` sayıldı (ölçüldü ≠ ölçülemedi): {_alanlar(yakala, sd)[ALAN]!r}")


# ================================================================================================
# T4 — TAVAN, KATLAMA SIRASI VE SIR SÜZGECİ
# ================================================================================================

def test_T4_UZUN_ILK_SATIR_TAVANA_KIRPILIR_ONCE_KATLANARAK(sd, tmp_path, monkeypatch,
                                                           sandbox_state):
    """SIRA ÖLÇÜLÜR, VARSAYILMAZ (`cevap_bas` emsali). 400 karakterlik bu girdide önce kırpmak
    pencerenin dörtte birini boşluklara harcardı; teşhis metni sebepsiz kısalır."""
    g, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()),
                     "ab  " * 100 + "\nikinci satır")
    deger = _alanlar(yakala, sd)[ALAN]
    assert isinstance(deger, str) and len(deger) == sd.BRIFING_ILK_SATIR_TAVANI, (
        f"tavan tutmadı ya da kırpma katlamadan ÖNCE yapıldı: {len(deger or '')}")
    assert "  " not in deger, f"boşluklar katlanmadı: {deger!r}"
    assert g.metin.startswith("ab  "), "teslim edilen metin DEĞİŞTİRİLDİ (alan salt okur olmalı)"


def test_T4B_TAVAN_TEK_SABITTEN_TURETILIR(sd, tmp_path, monkeypatch, sandbox_state):
    """Tavan bir LİTERAL değil ADLANDIRILMIŞ sabittir (`CEVAP_BAS_TAVANI` deseni). Gövdeye 160
    yazılsaydı, sabit bir gün değiştiğinde iki sayı sessizce ayrışırdı (tek-kaynak yasası)."""
    assert sd.BRIFING_ILK_SATIR_TAVANI == 160, (
        f"tavan sözleşmesi değişti: {sd.BRIFING_ILK_SATIR_TAVANI!r}")
    monkeypatch.setattr(sd, "BRIFING_ILK_SATIR_TAVANI", 20)
    _, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), "x" * 400 + "\nikinci")
    assert len(_alanlar(yakala, sd)[ALAN]) == 20, (
        f"kırpma sabitten türetilmiyor (literal gömülü): {_alanlar(yakala, sd)[ALAN]!r}")


def test_T4C_ILK_SATIR_SIR_SUZGECINDEN_GECER(sd, tmp_path, monkeypatch, sandbox_state):
    """BRİFİNG METNİ DE BİR MODEL ÇIKTISIDIR (`cevap_bas` ile aynı sınıf) ve bir hata dizgesi
    taşıyabilir. Defter bir veri yüzeyidir: yedeklenir, `olay_sorgu` ile okunur, panoya taşınır —
    süzgeçsizse sır `events.jsonl`e YAZILIR ve orada KALIR."""
    for ham, kalinti in ((SAHTE_ANAHTAR, "sk-or-v1-"), (SAHTE_ENV_SATIRI, "abcdefgh12345678")):
        _, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()),
                         f"denetci notu: {ham} sizdi\nikinci satır")
        deger = _alanlar(yakala, sd)[ALAN]
        assert kalinti not in str(deger), f"SIR deftere yazıldı ({ham!r}): {deger!r}"
        assert "***" in str(deger), f"süzgeç hiç koşmadı (maske yok): {deger!r}"


def test_T4D_SUZGEC_KIRPMADAN_ONCE_KOSAR(sd, tmp_path, monkeypatch, sandbox_state):
    """SIRA BURADA BİR GÜVENLİK SÖZLEŞMESİDİR. Anahtar tavanın ÜSTÜNDE başlar: önce kırpılsaydı
    geriye anahtarın desene UYMAYAN bir öneki kalır, `scrub` onu tanımaz ve ham baytlar deftere
    düşerdi. Önce süzülürse anahtarın tamamı `***` olur ve kırpma zararsız kalır."""
    onek = "x" * (sd.BRIFING_ILK_SATIR_TAVANI - 20)
    _, yakala = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()),
                     f"{onek}{SAHTE_ANAHTAR}\nikinci satır")
    deger = _alanlar(yakala, sd)[ALAN]
    assert "sk-or-v1-" not in str(deger), f"kırpılmış anahtar öneki deftere sızdı: {deger!r}"
    assert str(deger).endswith("***"), f"süzgeç kırpmadan SONRA koştu: {deger!r}"


# ================================================================================================
# O4 + YASA 6 — ALAN YALNIZ OLAYA GİDER, VE OKUYUCUSU DEFTERDEN OKUR
# ================================================================================================

def test_O4_ALAN_DAMGAYA_GIRMEZ(sd, tmp_path, monkeypatch, sandbox_state):
    """`Gecis.kayit()` damgaya da akar ve damganın okuyucusu bu alanı bilmez (v385 O4 emsali).
    Okunmayacak bir alanı damgaya yazmak, Yasa 6'yı tam da onu zorlayan dosyada delmektir."""
    g, _ = _kos(sd, tmp_path, monkeypatch, _Kuyruk(_temiz_cevap()), "bir brifing satırı")
    assert ALAN not in g.kayit("sef"), f"okunmayacak alan damgaya yazıldı: {sorted(g.kayit('sef'))}"


def test_YASA6_ALAN_DEFTERE_SERILESTIRILIR(sd, tmp_path, sandbox_state):
    """OKUYUCU TARAFI: alanın okuyucusu `ops/olay_sorgu.py --sql` haftalık sınıflamasıdır ve o
    okuyucu `events.jsonl`i okur. `obs.log`a geçilmiş ama deftere düşmeyen bir değer, okuyucusu
    olmayan bir değerdir — bu çivi sapsız koşar, tam da o yüzden."""
    sd.gecir(profil_evi=_profil_evi(tmp_path), ilk_metin="deftere düşen ilk satır\nikinci",
             ilk_istem="İLK İSTEM", veri_terimleri=[], cagir=_Kuyruk(_temiz_cevap()), bot="sef")
    olaylar = _olaylar()
    assert olaylar, "kural denetimi olayı hiç yazılmadı"
    assert olaylar[-1].get(ALAN) == "deftere düşen ilk satır", (
        f"alan deftere serileştirilmedi: {olaylar[-1]!r}")
