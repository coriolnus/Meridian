"""test_f8_sayac_kalici_v499.py — TSK-070: F8 eşanlamlı-okuma sayaçlarının KALICI olması.

ÖLÇÜLEN BOŞLUK (ROADMAP TSK-070 Not, 2026-09-13 Rol-1). Sözlüğün eşanlamlı-okuma sayaçları
SÜREÇ-İÇİYDİ: her worker restart'ı onları sıfırlıyordu. "Eski adın okuyucusu öldü" hükmünün
tanımı ise ≥30 GÜN restart'sız bir penceredir ve dağıtımlar günlüktür — yani ölçüm yapılıyor,
hüküm YAPISAL OLARAK imkânsız kalıyordu. Sayaç kalıcı deftere (`durum_sozlugu.SAYAC_DEFTERI`)
taşındı; bu dosya o taşımanın çivisidir.

NE ÇİVİLENİR (her biri mutasyonla ısırtıldı — bkz. rapor):
  T1  ilk artış defteri DİSKE yazar; şema ve sayaç değeri sözleşmeye uyar.
  T2  "RESTART": modül belleği boşaltılır (dosya DURUR) → sayaçlar diskten geri gelir.
  T3  PENCERE: ilk kayıt bir kez çivilenir ve DEĞİŞMEZ, son kayıt her artışta güncellenir,
      hiç kayıt yokken `gun` None'dır (0 DEĞİL — uydurma yasağı).
  T4  BOZUK defter: `.bozuk-<ts>` yedeği alınır, sayım sıfırdan başlar, olay ADIYLA raporlanır.
  T5  YAZIM DÜŞERSE okuma yolu düşmez: bellek sayımı ayakta, uyarı süreç başına BİR kez.
  T6  SERVİS YÜZEYİ: `api._durum_sozlugu` çıktısı `pencere` taşır ve sayaçlarla TUTARLIDIR.
  T7  ATOMİK yazım: geçici dosya kalıntısı yok (başarılı yazımda da düşen yazımda da).
  T8  YASA 6 + TEST HİJYENİ: defterin muafiyeti beyanlı (ihlal listesi boş) ve sayaca dokunan
      test dosyaları `config.STATE`i sandbox'a alır — kapsam koşusu canlı yerel deftere yazamaz.

NOT: bu dosya worktree kapsam testidir — otoriter tam suite Rol-1'dedir.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib

import pytest

from meridian import codelaw, config, durum_sozlugu as dsz, obs

SRC = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _temiz(sandbox_state):
    """Her test TAZE bir sandbox defteriyle başlar ve biterken defteri bırakmaz. `sandbox_state`
    ZORUNLUDUR: sayaç artık diske yazıyor, sandbox'sız koşum canlı yerel state'i kirletirdi."""
    dsz._sifirla_test_icin()
    yield
    dsz._sifirla_test_icin()


def _defter() -> pathlib.Path:
    return config.STATE / dsz.SAYAC_DEFTERI


def _restart(monkeypatch) -> None:
    """SÜREÇ YENİDEN BAŞLADI (dosya DURUR, bellek GİDER). `importlib.reload` KULLANILMAZ: modül
    nesnesini değiştirmek `api` gibi onu ithal etmiş tarafların elindeki referansı bayatlatır ve
    ölçtüğümüz şey (diskten geri gelme) değil, ithal semantiği olurdu."""
    monkeypatch.setattr(dsz, "_ESANLAMLI_OKUMA", {})
    monkeypatch.setattr(dsz, "_PENCERE", {"ilk_kayit_utc": None, "son_kayit_utc": None,
                                          "son_yazim_utc": None})
    monkeypatch.setattr(dsz, "_YUKLU_DAMGA", None)
    monkeypatch.setattr(dsz, "_YAZIM_UYARILDI", False)


def _olaylar(ad: str) -> list[dict]:
    return [e for e in obs.recent(limit=200) if e.get("event") == ad]


# =============================================================================================
# T1 — İLK ARTIŞ DİSKE İNER
# =============================================================================================

def test_T1_ilk_artis_defteri_diske_yazar():
    """Sözleşme: `_say` bellekle YETİNMEZ. Dosya, şema ve sayaç değeri birlikte ölçülür —
    yalnız "dosya var" demek, içi boş bir defteri kalıcılık sanmak olurdu."""
    assert not _defter().exists(), "defter test ÖNCESİ vardı — hijyen bozuk"
    assert dsz.hukum_oku({"failed": True}) == (False, "failed")

    yol = _defter()
    assert yol.exists(), "eşanlamlı okuma sayıldı ama KALICI deftere yazılmadı"
    doc = json.loads(yol.read_text(encoding="utf-8"))
    assert doc["schema"] == dsz.SAYAC_SEMA
    assert doc["sayaclar"] == {"hukum:failed": 1}
    assert doc["ilk_kayit_utc"] and doc["son_kayit_utc"] and doc["son_yazim_utc"]
    # bellek ile disk AYNI gerçeği söyler (iki kopya değil, biri diğerinin nüshası)
    assert dsz.esanlamli_okumalar() == {"hukum:failed": 1}


def test_T1b_kanonik_okuma_defteri_HIC_yaratmaz():
    """POZİTİF KONTROL: kanonik yol sayaç oynatmaz — dolayısıyla defteri de DOĞURMAZ. Aksi hâlde
    "defter var" sinyali anlamsızlaşır ve her süreç açılışı sahte bir pencere başlatırdı."""
    assert dsz.hukum_oku({"ok": False, "failed": True}) == (False, "ok")
    assert dsz.neden_oku({"neden": "a", "detail": "b"}) == ("a", "neden")
    assert dsz.kol_adi("soft_halt") == "soft_halt"
    assert not _defter().exists(), "kanonik okuma kalıcı defter yarattı — sayaç 'çağrıyla' artıyor"
    assert dsz.esanlamli_okumalar() == {}
    assert dsz.esanlamli_pencere()["gun"] is None, "kayıt yokken gün 0 diye UYDURULDU"


# =============================================================================================
# T2 — RESTART: SAYAÇ DİSKTEN GERİ GELİR (kalemin BÜTÜN sebebi)
# =============================================================================================

def test_T2_restart_sayaclari_SIFIRLAMAZ(monkeypatch):
    """TSK-070'in tam hükmü: süreç yeniden başlar, sayaçlar YERİNDE kalır. Eski rejimde bu test
    `{}` görürdü ve "eski adın okuyucusu öldü" hükmü hiçbir zaman verilemezdi."""
    dsz.hukum_oku({"failed": True})
    dsz.neden_oku({"detail": "eski-yük"})
    dsz.kol_adi("learning_halted")
    onceki = dsz.esanlamli_okumalar()
    assert onceki == {"hukum:failed": 1, "neden:detail": 1, "kol:learning_halted": 1}

    _restart(monkeypatch)
    assert dsz.esanlamli_okumalar() == onceki, "RESTART sayaçları sıfırladı — defter kalıcı değil"


def test_T2b_restart_sonrasi_artis_diskteki_degerin_USTUNE_biner(monkeypatch):
    """Kayıp-güncelleme yasağı: yeni süreç 0'dan başlamaz, diskteki değeri devralır ve üstüne
    ekler. (İki AYRI süreç — worker ve api — aynı defteri paylaşır.)"""
    dsz.hukum_oku({"failed": True})
    dsz.hukum_oku({"failed": True})
    _restart(monkeypatch)
    dsz.hukum_oku({"failed": True})
    assert dsz.esanlamli_okumalar() == {"hukum:failed": 3}
    assert json.loads(_defter().read_text(encoding="utf-8"))["sayaclar"] == {"hukum:failed": 3}


def test_T2c_DIS_yazim_taze_okunur(monkeypatch):
    """Süreçler-arası TAZELİK: defteri başka bir süreç (burada: doğrudan disk) büyütürse okuyucu
    onu GÖRÜR. Bir kez yükleyip donsaydı pano restart'a kadar bayat bir sayı basardı."""
    dsz.hukum_oku({"failed": True})
    doc = json.loads(_defter().read_text(encoding="utf-8"))
    doc["sayaclar"]["hukum:failed"] = 41
    doc["sayaclar"]["kol:halted"] = 7
    _defter().write_text(json.dumps(doc), encoding="utf-8")
    assert dsz.esanlamli_okumalar() == {"hukum:failed": 41, "kol:halted": 7}


# =============================================================================================
# T3 — PENCERE META (sayaç "0"ı ancak bir pencereyle anlamlıdır)
# =============================================================================================

def test_T3_pencere_ilk_kayit_CIVILENIR_son_kayit_gunceller(monkeypatch):
    dsz.hukum_oku({"failed": True})
    p1 = dsz.esanlamli_pencere()
    assert p1["ilk_kayit_utc"] and p1["son_kayit_utc"] == p1["ilk_kayit_utc"]
    assert p1["kaynak_dosya"] == dsz.SAYAC_DEFTERI

    # ikinci artışı GELECEĞE damgalayıp ilk kaydın DEĞİŞMEDİĞİNİ ölçeriz (zaman akışını
    # beklemeden: damga tek kaynaktan gelir, onu değiştirmek gerçek ilerleme yerine geçer)
    ileri = (dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
             + dt.timedelta(days=31)).isoformat()
    monkeypatch.setattr(dsz, "_simdi", lambda: ileri)
    dsz.hukum_oku({"failed": True})
    p2 = dsz.esanlamli_pencere()
    assert p2["ilk_kayit_utc"] == p1["ilk_kayit_utc"], "ilk kayıt damgası KAYDI — pencere sürüklenir"
    assert p2["son_kayit_utc"] == ileri, "son kayıt damgası güncellenmiyor"


def test_T3b_gun_ilk_kayittan_bugune_tam_gundur():
    """`gun` ÖLÇÜLÜR, uydurulmaz: 30 gün önceden başlamış bir defter 30 gün der; damga
    çözülemiyorsa None döner (sıfır ile "bilmiyorum" aynı şey değildir)."""
    dsz.hukum_oku({"failed": True})
    doc = json.loads(_defter().read_text(encoding="utf-8"))
    doc["ilk_kayit_utc"] = (dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
                            - dt.timedelta(days=30, hours=1)).isoformat()
    _defter().write_text(json.dumps(doc), encoding="utf-8")
    assert dsz.esanlamli_pencere()["gun"] == 30

    doc["ilk_kayit_utc"] = "dün gibi bir şey"
    _defter().write_text(json.dumps(doc), encoding="utf-8")
    assert dsz.esanlamli_pencere()["gun"] is None, "çözülemeyen damgadan gün UYDURULDU"


# =============================================================================================
# T4 — BOZUK DEFTER: YEDEKLE, SIFIRLA, SÖYLE
# =============================================================================================

@pytest.mark.parametrize("icerik,neden", [
    ("{bu json degil", "cozulemedi"),
    (json.dumps({"schema": 99, "sayaclar": {}}), "sema_uyusmadi"),
    (json.dumps({"schema": 1, "sayaclar": {"hukum:failed": "üç"}}), "sema_uyusmadi"),
])
def test_T4_bozuk_defter_yedeklenir_ve_ADIYLA_raporlanir(icerik, neden):
    """Bozuk defter SESSİZCE EZİLMEZ: `.bozuk-<ts>` adına taşınır (kanıt durur), sayım sıfırdan
    başlar ve olay adıyla gözlem kanalına düşer — sayacın neden geri saydığı kayıtlı olur."""
    _defter().parent.mkdir(parents=True, exist_ok=True)
    _defter().write_text(icerik, encoding="utf-8")

    assert dsz.esanlamli_okumalar() == {}, "bozuk defterden sayaç UYDURULDU"
    assert not _defter().exists(), "bozuk defter yerinde bırakıldı — bir sonraki okuma da bozulur"
    yedekler = list(config.STATE.glob(f"{dsz.SAYAC_DEFTERI}.bozuk-*"))
    assert len(yedekler) == 1, f"bozuk defterin yedeği alınmadı: {yedekler}"
    assert yedekler[0].read_text(encoding="utf-8") == icerik, "yedek İÇERİĞİ taşımıyor"

    ol = _olaylar("f8_sayac_defteri_bozuk")
    assert len(ol) == 1, f"bozukluk sessizce yutuldu (YASA 4): {ol}"
    assert ol[0]["neden"] == neden and ol[0]["yedek"] == yedekler[0].name

    # sıfırdan devam: yeni artış TEMİZ defter kurar
    dsz.hukum_oku({"failed": True})
    assert json.loads(_defter().read_text(encoding="utf-8"))["sayaclar"] == {"hukum:failed": 1}


# =============================================================================================
# T5 — YAZIM DÜŞERSE: OKUMA YOLU DÜŞMEZ, UYARI BİR KEZ
# =============================================================================================

def test_T5_yazim_dusunce_okuma_yasar_uyari_BIR_kez(monkeypatch):
    """Kalıcılık bir DAYANIKLILIKTIR, sayacın KOŞULU değil: disk yazamazken de eşanlamlı okuma
    sayılır ve okuyucu yolu (hüküm çevirisi) olduğu gibi çalışır. Uyarı süreç başına bir kez —
    arızalı diskte her okuma bir satır bassaydı defter gürültüye boğulurdu."""
    def _patlat(*a, **k):
        raise OSError("çivi: replace düştü")

    monkeypatch.setattr(os, "replace", _patlat)
    assert dsz.hukum_oku({"failed": True}) == (False, "failed"), "yazım hatası OKUMA yolunu düşürdü"
    assert dsz.hukum_oku({"failed": False}) == (True, "failed")
    assert dsz.esanlamli_okumalar() == {"hukum:failed": 2}, "bellek sayımı yazımla birlikte düştü"
    assert not _defter().exists()
    assert len(_olaylar("f8_sayac_yazilamadi")) == 1, "yazım arızası ya sessiz ya da her okumada"


# =============================================================================================
# T6 — SERVİS YÜZEYİ: /api/diagnostics bloğu `pencere` taşır
# =============================================================================================

def test_T6_api_blogu_pencere_tasir_ve_sayaclarla_tutarlidir():
    from meridian import api
    bd = {"goal_failure": {"failed": True, "detail": "eski-yük"},
          "kitap_damga": {"ok": True, "olculemedi": False}}
    dz = api._durum_sozlugu(bd)

    assert "pencere" in dz, "`pencere` servis edilmiyor — kalıcı sayacın zaman ekseni görünmez"
    p = dz["pencere"]
    assert set(p) == {"ilk_kayit_utc", "son_kayit_utc", "son_yazim_utc", "gun", "kaynak_dosya"}
    assert p["kaynak_dosya"] == dsz.SAYAC_DEFTERI
    assert dz["esanlamli_okumalar"]["hukum:failed"] == 1
    assert p["ilk_kayit_utc"] is not None and p["gun"] == 0
    assert "kalıcı" in dz["sayac_rejimi"], "rejim beyanı hâlâ 'süreç-içi' diyor — beyan bayat"


def test_T6b_sayac_bosken_pencere_OLCULEMEDI_der():
    """Boş defterde pencere alanları None'dır — "0 gündür ölçülüyor" diye UYDURULMAZ."""
    from meridian import api
    dz = api._durum_sozlugu({})
    assert dz["esanlamli_okumalar"] == {}
    assert dz["pencere"] == {"ilk_kayit_utc": None, "son_kayit_utc": None, "son_yazim_utc": None,
                             "gun": None, "kaynak_dosya": dsz.SAYAC_DEFTERI}


# =============================================================================================
# T7 — ATOMİK YAZIM (geçici dosya kalıntısı yok)
# =============================================================================================

def test_T7_atomik_yazim_tmp_kalintisi_birakmaz(monkeypatch):
    """Defter `store` kapısından geçer, yani tmp+fsync+replace. İki yol da ölçülür: başarılı
    yazımdan sonra ve DÜŞEN yazımdan sonra `state/` altında `.tmp` kalıntısı OLMAMALI."""
    dsz.hukum_oku({"failed": True})
    assert list(config.STATE.glob("*.tmp")) == [], "başarılı yazım geçici dosya bıraktı"

    def _patlat(*a, **k):
        raise OSError("çivi: replace düştü")

    monkeypatch.setattr(os, "replace", _patlat)
    dsz.hukum_oku({"failed": True})
    assert list(config.STATE.glob("*.tmp")) == [], "düşen yazım geçici dosya bıraktı"


# =============================================================================================
# T8 — YASA 6 BEYANI + TEST HİJYENİ (sınıfın MEKANİK kapanışı)
# =============================================================================================

def test_T8_defterin_muafiyeti_BEYANLI_ve_ihlal_listesi_bos():
    """Kalıcı defterin yazanı da okuyanı da AYNI modüldür; statik graf dış tüketiciyi göremez ve
    artefakt `unread` olur. Beyan `codelaw` kaydındadır — beyansız bırakmak YASA 6 ihlaliydi."""
    assert dsz.SAYAC_DEFTERI in codelaw.DECLARED_SINKS, "kalıcı defter beyansız (YASA 6)"
    g = codelaw.artifact_graph()
    assert g["violations"] == [] and g["stale_sinks"] == [], (g["violations"], g["stale_sinks"])
    assert codelaw.stale_claims() == [], "beyan çürük — gerekçe gerçek tüketici zincirini anlatmalı"
    assert dsz.SAYAC_DEFTERI in g["artifacts"], "defter grafiğe hiç girmedi (ad çözülemedi)"


@pytest.mark.parametrize("dosya", [
    "test_f8_durum_sozlugu_v271.py", "test_kucuk_paket_v275.py", "test_f8_sayac_kalici_v499.py"])
def test_T8b_sayaca_dokunan_testler_STATE_i_sandboxa_alir(dosya):
    """TEKRARLAYAN KUSUR SINIFININ KAPISI: sayaç artık diske yazıyor. Sayaca dokunan bir test
    dosyası `config.STATE`i sandbox'a almazsa kapsam koşusu CANLI YEREL deftere yazar (bu depoda
    ölçülmüş bir vaka sınıfı). Üç dosyanın da autouse fikstürü yönlendirmeyi kurar."""
    metin = (SRC / "tests" / dosya).read_text(encoding="utf-8")
    assert "autouse=True" in metin
    assert ('monkeypatch.setattr(config, "STATE"' in metin
            or "def _temiz(sandbox_state)" in metin), \
        f"{dosya}: sayaç fikstürü state'i sandbox'a almıyor"
