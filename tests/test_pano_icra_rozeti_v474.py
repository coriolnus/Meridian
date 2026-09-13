"""test_pano_icra_rozeti_v474.py — TSK-012 B1: onay defteri sütunu İCRA GERÇEĞİNİ söylüyor mu?

ÖLÇÜLMÜŞ YANLIŞ CÜMLE (kapatılan boşluk): pano `OnayDefteri.tsx`in "Davranışsal mı" sütunu TEK
bir alana bakıyordu — `davranissal`. O alanın anlamı `KAPI_OKUYAN_ONEKLER`e bağlıdır ("bu kimliği
bir L1+ uygulama kapısı okur mu") ve sohbet önerisinin kimliğini HİÇBİR kapı okumaz; yani alan o
satırlarda HER ZAMAN `False` gelir ve sütun her sohbet kararına "kayıt — icra açmaz" yazıyordu.
Oysa onaylanan bir `plan_onayi` gerçekten plan onay yolunu çağırır, onaylanan bir `alarm_ack`
gerçekten alarmı kapatır: sunucu bunu `SOHBET_KARAR_ALANLARI` (`icra_eder`/`icra_ok`) ve `not`
künyesiyle ZATEN yazıyordu, panoda OKUYUCUSU yoktu (Yasa 6'nın okuyucu tarafı).

NEDEN METİN ÇİVİSİ: panonun test koşucusu YOK — `ui/package.json` yalnız `kontrol` (tsc) ve
`build` (vite) betikleri taşıyor, vitest/jest bağımlılığı hiç yok (ölçüldü 2026-09-13). O yüzden
mantık saf bir yardımcıya (`ui/src/pano/yuzeyler/kuyruk/icra_rozeti.ts`) çıkarıldı ve iki kapı
birden ısırıyor: TS tarafında tip denetimi (varyant sözlüğü `Badge`in alt kümesi), Python
tarafında BU dosya.

TEK KAYNAK: alan adları burada ELLE YAZILMAZ, `api.SOHBET_KARAR_ALANLARI`dan türetilir. Sunucu
adı değiştirdiği gün pano sessizce boş alan okumaya başlardı; bu çivi o günü KIRMIZI yapar.
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import api

# Yorum soyucu TEK KAYNAKTAN: `ui/` düzyazısı YASAKLANAN ŞEYİ ALINTILAR (bu depo geleneği), ve
# alıntıyı kullanım sanan çivi kendi belgesini suçlar. İkinci bir soyucu yazmak aynı hatayı
# ikinci kez yapmak olurdu.
from tests.test_ui_pilot_kapilari_v286 import _soy

KOK = pathlib.Path(__file__).resolve().parents[1]
KUYRUK = KOK / "ui" / "src" / "pano" / "yuzeyler" / "kuyruk"
YARDIMCI = KUYRUK / "icra_rozeti.ts"
DEFTER = KUYRUK / "OnayDefteri.tsx"
TIPLER = KUYRUK / "onaylar.ts"

#: Sütunun ÜÇ HÂLİ — metin + `Badge` varyantı. Metinler burada literal durur BİLEREK: çivinin
#: işi tam olarak "ekranda hangi cümle yazıyor"u dondurmaktır. Varyant ise bir ROL: "icra düştü"
#: sessiz bir `outline` rozetle geçiştirilemez.
UC_HAL = (
    ("ICRA_EDILDI_METNI", "sohbet — icra EDİLDİ", "secondary"),
    ("ICRA_DUSTU_METNI", "sohbet — icra DÜŞTÜ", "destructive"),
    ("ICRA_ACMAZ_METNI", "kayıt — icra açmaz", "outline"),
    # beşinci hâl (inceleme ORTA bulgusu 2026-09-13): icra_eder=true ama icra_ok boolean değil → uydurma yasağı,
    # "açmaz" da "edildi" de denmez; adıyla "ölçülemedi"
    ("ICRA_OLCULEMEDI_METNI", "sohbet — icra sonucu ölçülemedi", "outline"),
)


def _kaynak(yol: pathlib.Path) -> str:
    if not yol.is_file():
        pytest.fail(f"pano kaynağı YOK: {yol} — kapı ölçülemedi (bu bir 'geçti' değildir)")
    return yol.read_text(encoding="utf-8")


def _kod(yol: pathlib.Path) -> str:
    """Yorumsuz kaynak. Bir cümlenin YALNIZ şerhte geçmesi, ekranda yazdığı anlamına gelmez."""
    return _soy(_kaynak(yol))


# =================================================================================================
# (a) TEK KAYNAK — alan adları sunucudan türer
# =================================================================================================


@pytest.mark.parametrize("alan", api.SOHBET_KARAR_ALANLARI)
def test_yardimci_SUNUCUNUN_alan_ADINI_okur(alan):
    """`icra_eder`/`icra_ok` adları `api.SOHBET_KARAR_ALANLARI`dan gelir; pano onları BİREBİR
    okumalı. Türkçeleştirme/kısaltma, ad değiştiği gün ayrışmayı SESSİZ yapardı."""
    kod = _kod(YARDIMCI)
    assert f'"{alan}"' in kod, (
        f"pano yardımcısı sunucunun `{alan}` alanını OKUMUYOR — sütun icra gerçeğini "
        f"göremez ve `davranissal`dan yanlış cümle kurar. Kaynak: {YARDIMCI}")


@pytest.mark.parametrize("alan", api.SOHBET_KARAR_ALANLARI)
def test_tip_SUNUCUNUN_alan_ADINI_beyan_eder(alan):
    """Tip beyanı da aynı kaynaktan: `onaylar.ts` alanı taşımıyorsa tsc yardımcıyı koruyamaz."""
    kod = _kod(TIPLER)
    assert f"{alan}?:" in kod, (
        f"`onaylar.ts` defter satırı tipinde `{alan}` alanı YOK — tip denetimi bu alanda kör")


def test_kunye_ALANI_da_okunur_cumleyi_SUNUCU_kurar():
    """`not` künyesi rozetin `title`ıdır. Pano kendi açıklamasını yazsaydı, aynı gerçeğin ikinci
    kopyası doğar ve "icra DÜŞTÜ: …" sebebi ekrandan düşerdi."""
    kod = _kod(YARDIMCI)
    assert '"not"' in kod, "künye alanı (`not`) okunmuyor — düşüş sebebi ekranda görünmez"
    assert "title" in kod, "künye rozetin `title`ına taşınmıyor"


# =================================================================================================
# (b) ÜÇ HÂL — metin VE rol
# =================================================================================================


@pytest.mark.parametrize("sabit,metin,varyant", UC_HAL)
def test_UC_HAL_metni_ve_ROLU_kaynakta(sabit, metin, varyant):
    """Her hâl KENDİ cümlesini ve KENDİ rolünü taşır. Biri silinirse bu çivi kırmızı olur."""
    kod = _kod(YARDIMCI)
    assert f'{sabit} = "{metin}"' in kod, (
        f"`{sabit}` hâli kaynakta yok ya da metni değişti — beklenen: {metin!r}")
    assert f'metin: {sabit}, varyant: "{varyant}"' in kod, (
        f"`{sabit}` hâli `{varyant}` rozetiyle dönmüyor — rol bir süs değil, şiddet işaretidir")


def test_UC_HAL_metinleri_BIRBIRINDEN_FARKLI():
    """Defteri okuyan "icra edildi" ile "icra düştü"yü AYIRABİLMELİ; aynı cümle iki hâli
    birleştirirse sütun hiçbir şey ölçmüyor demektir."""
    metinler = [m for _, m, _ in UC_HAL]
    assert len(set(metinler)) == len(UC_HAL), metinler


def test_ONCELIK_icra_eder_ONCE_okunur():
    """SIRA HÜKÜMDÜR: `icra_eder === false` (icra DENENMEDİ) hâli, `icra_ok` dallarından ÖNCE
    kapanmalı. Ters sırada, denenmemiş bir kararın `icra_ok=false`ı "icra DÜŞTÜ" diye okunur ve
    pano hiç olmamış bir düşüşü beyan eder."""
    kod = _kod(YARDIMCI)
    i_eder = kod.find("icra_eder === false")
    i_ok = kod.find("icra_ok === true")
    assert i_eder >= 0, "`icra_eder === false` dalı YOK — denenmemiş icra hâli ayrılmıyor"
    assert i_ok >= 0, "`icra_ok === true` dalı YOK"
    assert i_eder < i_ok, (
        "öncelik ters: `icra_ok` dalı `icra_eder === false` dalından ÖNCE okunuyor — "
        "denenmemiş bir karar 'icra DÜŞTÜ' diye gösterilir")


def test_ALAN_YOKSA_yardimci_SUSAR_null_doner():
    """`null` "icra yok" DEĞİL "bu satırda ölçemedim"dir: defterde sohbet-dışı satırlar da var
    (`kayit:`, `arming:`) ve onların cümlesi `davranissal`dan kurulur. Yardımcı burada bir hâl
    uydurursa, kapı-bağlayıcı bir karar sessizce sohbet cümlesiyle etiketlenir."""
    kod = _kod(YARDIMCI)
    assert "icra_eder === undefined" in kod and "return null" in kod, (
        "alan yokluğu `null` ile değil, bir varsayımla karşılanıyor — uydurma yasağı")


# =================================================================================================
# (c) OKUYUCU — sütun gerçekten yardımcıyı çağırıyor mu (Yasa 6)
# =================================================================================================


def test_DEFTER_SUTUNU_yardimciyi_CAGIRIR():
    """Yardımcı okunmadan doğru olması hiçbir şey değiştirmez — okuyucusuz yazım yok."""
    kod = _kod(DEFTER)
    assert "./icra_rozeti" in kod, "yardımcı import edilmiyor"
    # IMPORT ÇAĞRI DEĞİLDİR: ölçüldü (mutasyon 3, 2026-09-13) — çağrı `const icra = null` ile
    # söküldüğünde `icraRozeti` adı import satırında KALIYOR ve salt-ad araması yeşil kalıyordu.
    # Hüküm çağrı yerinden okunur.
    assert "icraRozeti(" in kod, (
        "`OnayDefteri.tsx` `icraRozeti`yi ÇAĞIRMIYOR (ad yalnız import'ta olabilir) — yardımcı "
        "okuyucusuz kalır (Yasa 6) ve sütun eski yanlış cümlesini kurmaya devam eder")
    # Rozet GERÇEKTEN çizilmeli: dönüşün üç alanı da satıra basılmazsa cümle yarım kalır.
    for parca in ("icra.metin", "icra.varyant", "icra.title"):
        assert parca in kod, f"rozetin `{parca}` alanı sütuna basılmıyor"


def test_ACMAZ_METNI_DEFTERDE_ikinci_kez_YAZILMAZ():
    """TEK KAYNAK: "kayıt — icra açmaz" cümlesi hem yardımcıda hem `davranissal` dalında geçiyor.
    İkinci bir literal, yarın birinin düzeltilip ötekinin kalmasıyla biterdi."""
    kod = _kod(DEFTER)
    acmaz = UC_HAL[2][1]
    assert acmaz not in kod, (
        f"`OnayDefteri.tsx` {acmaz!r} cümlesini KENDİ literali olarak taşıyor — sabit "
        "(`ICRA_ACMAZ_METNI`) üzerinden okunmalı, yoksa iki kopya ayrışır")
    assert "ICRA_ACMAZ_METNI" in kod, "sütun ortak sabiti kullanmıyor"


# =================================================================================================
# (d) SUNUCU ↔ PANO AYRIŞMASI — düşüş künyesinin sözcüğü
# =================================================================================================


def test_DUSUS_sozcugu_SUNUCUYLA_ayni():
    """Sunucu künyeye "… | icra DÜŞTÜ: …" ekini yazıyor (`api.api_approve`). Rozet aynı sözcüğü
    kullanmazsa operatör tooltip'teki sebebi rozetle eşleştiremez; sunucu sözcüğü değişirse bu
    çivi ayrışmayı SESLİ yapar."""
    sunucu = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")
    assert "icra DÜŞTÜ" in sunucu, (
        "sunucu künyesindeki 'icra DÜŞTÜ' eki kayboldu — pano rozetiyle ayrıştı")
    assert "icra DÜŞTÜ" in UC_HAL[1][1], UC_HAL[1]
