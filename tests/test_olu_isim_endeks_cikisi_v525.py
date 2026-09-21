"""v525 — TSK-207 (a): ENDEKSTEN ÇIKMIŞ SEMBOL "DELİST ADAYI" DEĞİLDİR (2026-09-21).

CANLI VAKA (Rol-1 ölçümü 2026-09-21, A1 salt-okur): `SEMBOL_OLU_ADAY` her gece
`semboller=["CAG","ENPH","MTCH","VFC"] · esik=5` diye ötüyordu ve metni "delist adayı olabilir"
diyordu. Dördü de DELİST DEĞİL: `adapters.data.ENDEKS_CIKISI_BEYANLI` sözlüğünde TAM OLARAK bu
dördü duruyor (2026-09-09 S&P 500 çıkışı, şirketler aktif). Canlı evren ENDEKS ÜYELİĞİNE bağlı
olduğu için bar akışının durması BEKLENEN sonuçtur — yani ÖLÇÜM doğruydu, SINIF yanlıştı.

SÖZLEŞME (bu dosya çiviler):
  * `watchdog.olu_isim_adaylari()` dönüşü YENİ bir kova taşır: `endeks_cikisi`, elemanı
    `{ticker, son_bar, seans_farki, beyan}` (`beyan` = `ENDEKS_CIKISI_BEYANLI` sözlüğünün
    GEREKÇE METNİ — tek kaynak, kopya değil). Sınıflama SIRASI donuktur:
    `RETIRED_SYMBOLS` → `zaten_emekli`; `data.is_index_exited` → `endeks_cikisi`; kalanı
    `adaylar`. `HIC_UYE_BEYANLI` üyeleri `adaylar`da KALIR (canlı taranıyorlar, barları
    durursa GERÇEKTEN delist adayıdırlar) — daraltma YOK.
  * BEYANLI ÇIKIŞ WARN ÜRETMEZ (emsal: `constituents.universe_drift` şerhindeki `hic_uye_canlida`
    — beyanlı sapma alarm üretmez ama GÖRÜNÜR kalır). BEDEL YASASI gereği görünürlük iki yoldan
    korunur: (a) gerçek `adaylar` varken atılan `SEMBOL_OLU_ADAY` payload'ına çıkış adları AYRI
    alanla girer (`semboller`e ve `detail` metnine KARIŞMAZ); (b) yalnız çıkış varken günde bir
    kez `obs.log("SEMBOL_ENDEKS_CIKISI", ...)` BİLGİ satırı.
  * AÇIK POZİSYON KESİŞİMİ WARN'DIR: `endeks_cikisi` ∩ açık pozisyonlar ≠ ∅ ise
    `obs.warn("SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON", ...)`. TSK-207 (b)'nin adlandırdığı risk
    sınıfı budur; bu tur YALNIZ ÖLÇER VE HABER VERİR — çıkış mantığı/bar çekimi/evren
    DEĞİŞMEDİ (operatör kararı).
  * UYDURMA YASAĞI: kesişim ölçülemezse (`portfolio.json` yok/bozuk ya da `positions` alanı yok)
    `acik_pozisyon_kesisim=None` + `acik_pozisyon_neden` döner — "kesişim yok" DEĞİLDİR. Bu
    hükümsüzlük SESSİZ GEÇMEZ: aynı günün bildirim satırında alan olarak görünür.
  * Günlük mandal TEK KAYNAK: `ALARM_GUNLUK_FILE` + `_gunluk_oku()` — yeni dosya YOK, yalnız
    `mekanizmalar` sözlüğünde İKİ YENİ ANAHTAR (mevcut `alarm`/`bastirilan`/`son_semboller`
    şemasıyla, ki `api._alarm_gunluk()` onları EK KOD OLMADAN okusun — YASA 6).

TUZAK (bu dosyanın en pahalı satırı, docstring'e brief'in emriyle yazıldı): `EVREN_DISI_BEYANLI`
modül İTHALİNDE kurulan bir BİRLEŞİMDİR (`{**ENDEKS_CIKISI_BEYANLI, **HIC_UYE_BEYANLI}`). Yalnız
`ENDEKS_CIKISI_BEYANLI`yi yamamak sembolü TARAMA EVRENİNE sokmaz (evren `EVREN_DISI_BEYANLI`den
beslenir) → test sembolü hiç görmeden SESSİZCE YEŞİL kalır. Yalnız `EVREN_DISI_BEYANLI`yi yamamak
ise `is_index_exited`i etkilemez → sembol `adaylar`a düşer. Sentetik çıkış kurarken İKİSİ BİRDEN
yamanır (`_beyanli_kur`). `monkeypatch.undo()` YASAK (autouse fikstürleri de geri alır).
"""
from __future__ import annotations

import pytest

from meridian import store, watchdog
# FİKSTÜR/YARDIMCI YENİDEN KULLANIMI (tek-kaynak yasası: v416'nın düzeneği KOPYALANMAZ —
# kopya sessizce ayrışır ve iki dosya aynı sensörü farklı sentetik evrenlerde ölçmeye başlar).
from tests.test_olu_isim_adayi_v416 import (  # noqa: F401 — fikstür ithali pytest'e görünürlük içindir
    _arsiv_yaz,
    _bugun_ayarla,
    evren,
    takvim,
    warnlar,
)

# Sentetik gerekçe metinleri — canlı sözlüğün BİREBİR kopyası DEĞİL (canlı metin değişirse bu
# dosya kırılmamalı); ölçülen şey metnin KENDİSİNİN taşınması, içeriği değil.
CIKIS_BEYAN = "S&P 500 çıkışı 2026-09-09, şirket AKTİF — SmallCap 600'e indi (sentetik)"
HIC_UYE_BEYAN = "S&P 500'e hiç girmemiş, likit ve aktif (sentetik)"

BEKLENEN_ANAHTARLAR = {
    "adaylar", "endeks_cikisi", "zaten_emekli", "olculemedi", "esik", "n_tarandi", "bugun",
    "takvim_var", "acik_pozisyon_kesisim", "acik_pozisyon_neden",
}


@pytest.fixture
def loglar(monkeypatch):
    """`obs.log` çağrılarını yakalar. `warnlar` fikstürü yalnız `obs.warn`ı yakalar; beyanlı
    çıkışın bildirimi WARN DEĞİL BİLGİ satırıdır, yani ikisi AYRI yüzeylerdir ve bir testin
    "warn atılmadı" hükmü tek başına "hiçbir şey söylenmedi" anlamına GELMEZ."""
    from meridian import obs
    kayit: list[dict] = []

    def _yakala(event, **fields):
        kayit.append({"event": event, **fields})
        return {"event": event}

    monkeypatch.setattr(obs, "log", _yakala)
    return kayit


def _beyanli_kur(monkeypatch, cikis: dict, hic_uye: dict | None = None) -> None:
    """Sentetik beyanlı kümeler — ÜÇÜ BİRDEN yamanır (yukarıdaki TUZAK şerhi)."""
    from meridian.adapters import data
    hic_uye = dict(hic_uye or {})
    monkeypatch.setattr(data, "ENDEKS_CIKISI_BEYANLI", dict(cikis))
    monkeypatch.setattr(data, "HIC_UYE_BEYANLI", hic_uye)
    monkeypatch.setattr(data, "EVREN_DISI_BEYANLI", {**cikis, **hic_uye})


def _ad(satirlar) -> set:
    return {s["ticker"] for s in satirlar}


# ---- (1) beyanlı endeks-çıkışı `endeks_cikisi`ye düşer, `adaylar`a DEĞİL ---------------------

def test_endeks_cikisi_adaylardan_ayrilir_ve_beyani_tasir(takvim, monkeypatch):
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["TAZE"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["TAZE"])
    _arsiv_yaz("TAZE", "2026-08-31")          # 1 seans geride — aday değil
    _arsiv_yaz("CIK", "2026-08-20")           # 8 seans geride — eşiği AŞAR
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()

    assert set(rep) == BEKLENEN_ANAHTARLAR, "rapor sözleşmesi DONUK — sessiz genişleme/daralma yok"
    assert _ad(rep["endeks_cikisi"]) == {"CIK"}
    assert rep["adaylar"] == [], "beyanlı endeks-çıkışı 'delist adayı' SINIFINDA DEĞİLDİR"
    assert rep["zaten_emekli"] == []
    satir = rep["endeks_cikisi"][0]
    assert satir["beyan"] == CIKIS_BEYAN, "gerekçe metni sözlükten TAŞINIR (tek kaynak)"
    assert satir["son_bar"] == "2026-08-20" and satir["seans_farki"] == 8
    assert rep["n_tarandi"] == 2, "hiçbir sembol evrenden sessizce düşmemeli (YASA 6)"


# ---- (2) gerçek adaylar DARALTILMAZ: hiç-üye beyanlısı + düz canlı sembol --------------------

def test_hic_uye_ve_duz_canli_sembol_adaylarda_kalir(takvim, monkeypatch):
    """`HIC_UYE_BEYANLI` `EVREN_DISI_BEYANLI`nin İÇİNDEDİR ama `is_index_exited` ona KAPALIDIR:
    bu altı sembol CANLI evrende taranır, yani barları durursa GERÇEKTEN delist adayıdırlar.
    Aynı ağaçta düz bir LIVE sembolü de aday kalmalı — düzeltme bir SINIF ayrımıdır, bir
    susturma değil."""
    from meridian.adapters import data
    # "IKILI" HEM emekli HEM beyanlı çıkış: sınıflama SIRASI (RETIRED → ÇIKIŞ → aday) ancak
    # böyle bir sembolle ölçülebilir; sırasız bir uygulama onu `endeks_cikisi`ye koyar ve eski
    # `zaten_emekli` sözleşmesi (v416) sessizce daralırdı.
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN, "IKILI": CIKIS_BEYAN}, {"HIC": HIC_UYE_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["DUZ", "HIC"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["DUZ", "HIC"])
    monkeypatch.setattr(data, "RETIRED_SYMBOLS", {"EMEKLI": "2026-01-01 delist — sentetik",
                                                  "IKILI": "2026-02-02 delist — sentetik"})
    for t in ("DUZ", "HIC", "CIK", "EMEKLI", "IKILI"):
        _arsiv_yaz(t, "2026-08-20")           # BEŞİ DE 8 seans geride
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()

    assert _ad(rep["adaylar"]) == {"DUZ", "HIC"}, "yalnız beyanlı ÇIKIŞ ayrılır, gerisi aday kalır"
    assert _ad(rep["endeks_cikisi"]) == {"CIK"}
    assert _ad(rep["zaten_emekli"]) == {"EMEKLI", "IKILI"}, \
        "SINIFLAMA SIRASI DONUK: RETIRED hükmü beyanlı çıkıştan ÖNCE gelir"
    assert rep["n_tarandi"] == 5


# ---- (3) yalnız çıkış varken: WARN YOK, BİLGİ satırı günde BİR --------------------------------

def test_yalniz_cikis_warn_atmaz_bilgi_satiri_gunde_bir(takvim, monkeypatch, warnlar, loglar):
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    _bugun_ayarla(monkeypatch, "2026-09-01")

    watchdog.check_olu_isim_and_alarm()
    watchdog.check_olu_isim_and_alarm()        # AYNI gün — mandal

    assert [w["event"] for w in warnlar] == [], \
        "beyanlı çıkış WARN ÜRETMEZ (emsal: hic_uye_canlida beyanlı sapması)"
    cikis = [g for g in loglar if g["event"] == "SEMBOL_ENDEKS_CIKISI"]
    assert len(cikis) == 1, "günlük mandal: ikinci çağrı ikinci satır ÜRETMEMELİ"
    assert cikis[0]["semboller"] == ["CIK"]
    assert cikis[0]["beyanlar"] == {"CIK": CIKIS_BEYAN}
    metin = cikis[0]["detail"].lower()
    assert "beklenen" in metin and "endeks" in metin, \
        "bilgi satırı 'bar akışının durması beklenen davranış: evren endekse bağlı' demeli"
    assert "delist adayı" not in metin, "yanlış sınıf metni bu satıra SIZMAMALI"

    # MANDAL TEK KAYNAKTA: aynı defter, aynı şema — yeni dosya YOK.
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    satir = doc["mekanizmalar"][watchdog._OLU_ISIM_ENDEKS_MEK_ADI]
    assert satir["alarm"] == 1 and satir["bastirilan"] == 1, \
        "bastırılan satır SESSİZ DEĞİL, sayaçta GÖRÜNÜR (YASA 6)"
    assert satir["son_semboller"] == ["CIK"]
    assert watchdog._OLU_ISIM_MEK_ADI not in doc["mekanizmalar"], \
        "gerçek aday YOKKEN ölü-isim mekanizma satırı hiç AÇILMAMALI"


# ---- (3b) YASA 6 okuyucu: yeni mekanizma satırlarını `api._alarm_gunluk()` EK KOD OLMADAN okur -

def test_yeni_mandal_satirini_api_alarm_gunlugu_okur(takvim, monkeypatch, warnlar, loglar):
    """Yeni sayaç yazılıp OKUNMUYORSA üretilmemiş sayılır (YASA 6). Okuyucu `api.py`de ZATEN
    var ve mekanizma adına göre GENELDİR — bu çivi o genelliğin yeni anahtarları da kapsadığını
    ölçer (yeni okuyucu YAZILMADI)."""
    from meridian.adapters import data
    from meridian import api
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    _bugun_ayarla(monkeypatch, "2026-09-01")

    watchdog.check_olu_isim_and_alarm()

    gunluk = api._alarm_gunluk()
    assert gunluk["durum"] == "dolu"
    assert watchdog._OLU_ISIM_ENDEKS_MEK_ADI in gunluk["mekanizmalar"], \
        "yeni mandal satırının OKUYUCUSU yok — sayaç yazılıyor ama panoya çıkmıyor (YASA 6)"
    assert gunluk["mekanizmalar"][watchdog._OLU_ISIM_ENDEKS_MEK_ADI]["alarm"] == 1


# ---- (4) aday + çıkış birlikte: warn ATILIR, çıkış adları AYRI ALANDA -------------------------

def test_aday_varken_warn_atilir_cikis_ayri_alanda(takvim, monkeypatch, warnlar, loglar):
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["DUZ"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["DUZ"])
    _arsiv_yaz("DUZ", "2026-08-20")
    _arsiv_yaz("CIK", "2026-08-19")           # ÇIKIŞ daha eski — sıralamaya sızarsa yakalanır
    _bugun_ayarla(monkeypatch, "2026-09-01")

    watchdog.check_olu_isim_and_alarm()

    assert len(warnlar) == 1 and warnlar[0]["event"] == "SEMBOL_OLU_ADAY"
    w = warnlar[0]
    assert w["semboller"] == ["DUZ"], "çıkış adı `semboller` alanına KARIŞMAMALI"
    assert w["n"] == 1, "`n` GERÇEK aday sayısıdır"
    assert w["en_eski"]["ticker"] == "DUZ", "en_eski GERÇEK adaylar arasından seçilir"
    assert w["endeks_cikisi"] == ["CIK"], "çıkış adları AYRI ALANLA görünür (BEDEL YASASI)"
    assert "CIK" not in w["detail"], "çıkış adı 'delist adayı' metnine SIZMAMALI"
    assert "delist adayı olabilir" in w["detail"], "gerçek aday metni AYNEN kalır"
    assert [g["event"] for g in loglar] == [], \
        "aday varken ayrıca BİLGİ satırı atılmaz — tek satır, iki alan"


# ---- (5a) çıkış ∩ açık pozisyon ≠ ∅ → WARN ---------------------------------------------------

def test_cikis_acik_pozisyonla_kesisirse_warn(takvim, monkeypatch, warnlar, loglar):
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN, "CIK2": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    _arsiv_yaz("CIK2", "2026-08-20")
    store.write_json("portfolio.json", {"last_date": "2026-09-01",
                                        "positions": {"CIK": {"qty": 10}, "BASKA": {"qty": 3}}})
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] == ["CIK"] and rep["acik_pozisyon_neden"] is None
    poz = [w for w in warnlar if w["event"] == "SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON"]
    assert len(poz) == 1, "kesişim WARN sınıfıdır (TSK-207 (b)'nin adlandırdığı risk)"
    assert poz[0]["semboller"] == ["CIK"], "yalnız KESİŞEN sembol — CIK2 pozisyonsuz"
    assert "BASKA" not in str(poz[0]), "pozisyon defterinin tamamı satıra dökülmez"

    watchdog.check_olu_isim_and_alarm()        # AYNI gün — mandal
    assert len([w for w in warnlar if w["event"] == "SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON"]) == 1
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    assert doc["mekanizmalar"][watchdog._OLU_ISIM_ENDEKS_POZ_MEK_ADI]["bastirilan"] == 1


# ---- (5b) kesişim boşken o warn YOK ----------------------------------------------------------

def test_kesisim_boskken_pozisyon_warni_yok(takvim, monkeypatch, warnlar, loglar):
    """POZİTİF KONTROL: (5a) ile TEK farkı pozisyon defterinin içeriğidir. Bu test olmasaydı
    "her çıkışta warn atan" bir uygulama da (5a)'yı geçerdi."""
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    store.write_json("portfolio.json", {"last_date": "2026-09-01",
                                        "positions": {"BASKA": {"qty": 3}}})
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] == [], "ÖLÇÜLDÜ ve boş — None DEĞİL"
    assert rep["acik_pozisyon_neden"] is None
    assert [w["event"] for w in warnlar] == []
    assert [g["event"] for g in loglar] == ["SEMBOL_ENDEKS_CIKISI"], "bilgi satırı YİNE atılır"


# ---- (5c) portföy ölçülemezse: None + neden, ve SESSİZ GEÇMEZ --------------------------------

def test_portfoy_olculemezse_none_neden_ve_sessiz_gecmez(takvim, monkeypatch, warnlar, loglar):
    """UYDURMA YASAĞI: defter yoksa "kesişim yok" DENMEZ. Ve hükümsüzlük SESSİZ KALMAZ —
    o günün bildirim satırı nedeni ALAN olarak taşır."""
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    # portfolio.json HİÇ YAZILMADI — sandbox defterinde yok.
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] is None, "ölçülemeyen kesişim SIFIR DEĞİLDİR"
    assert rep["acik_pozisyon_neden"], "UYDURMA YASAĞI: neden BOŞ olamaz"
    assert [w["event"] for w in warnlar] == [], "ölçülemeyen kesişim warn ÜRETMEZ"
    cikis = [g for g in loglar if g["event"] == "SEMBOL_ENDEKS_CIKISI"]
    assert len(cikis) == 1
    assert cikis[0]["acik_pozisyon_kesisim"] is None
    assert cikis[0]["acik_pozisyon_neden"] == rep["acik_pozisyon_neden"], \
        "hükümsüzlük SESSİZ GEÇMEZ: bildirim satırı nedeni taşır"


# ---- (5d) `positions` alanı VARLIĞIYLA ölçülür (`.get` None ≠ anahtar yok) --------------------

def test_bos_positions_olculmus_sayilir(takvim, monkeypatch, warnlar, loglar):
    """`positions: {}` bir ÖLÇÜMDÜR ("hiç pozisyon yok"), alanın YOKLUĞU ise hükümsüzlüktür.
    `.get("positions") or {}` deseni ikisini AYNI şeye çökertirdi."""
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    store.write_json("portfolio.json", {"last_date": "2026-09-01", "positions": {}})
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()
    assert rep["acik_pozisyon_kesisim"] == [] and rep["acik_pozisyon_neden"] is None

    store.write_json("portfolio.json", {"last_date": "2026-09-01"})   # `positions` YOK
    rep2 = watchdog.olu_isim_adaylari()
    assert rep2["acik_pozisyon_kesisim"] is None and rep2["acik_pozisyon_neden"]


# ---- (6) çıkış YOKKEN kesişim portföyden BAĞIMSIZ olarak ölçülüdür ---------------------------

def test_cikis_yokken_kesisim_portfoysuz_da_olculur(takvim, monkeypatch):
    """∅ ∩ herhangi-bir-küme = ∅ — bu hüküm için portföyü okumaya GEREK YOKTUR. Aksi hâlde
    defteri olmayan her sandbox/koşum sahte bir "ölçülemedi" üretir ve gerçek hükümsüzlük
    gürültüye karışırdı (bedel yasası: uyarıyı ucuzlatmak onu görünmez kılar)."""
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["DUZ"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["DUZ"])
    _arsiv_yaz("DUZ", "2026-08-20")
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()
    assert rep["endeks_cikisi"] == []
    assert rep["acik_pozisyon_kesisim"] == [] and rep["acik_pozisyon_neden"] is None


# ---- (7) olay adları: warn/log SINIFI — bildirim jetonu DEĞİL (v98 türetmesi) -----------------

def test_yeni_olay_adlari_bildirim_jetonu_degildir():
    """`obs.NOTIFY_TOKENS` EL LİSTESİ DEĞİL TÜRETMEdir: yalnız `ALARM_*` sabitleri girer (v98).
    Yeni iki ad `warn`/`log` sınıfındadır, yani operatörün telefonuna DÜŞMEZ — mevcut
    `SEMBOL_OLU_ADAY` emsaliyle AYNI karar (emeklilik/endeks hükmü operatörün, "bak" demenin
    kendisi alarm SEVİYESİNDE aciliyet taşımaz). Bu çivi kararı DONDURUR: biri bu satırları
    `obs.alarm`a çevirirse jeton türetmesi değişir ve burası kırılır."""
    from meridian import obs
    for ad in ("SEMBOL_OLU_ADAY", "SEMBOL_ENDEKS_CIKISI", "SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON"):
        assert ad not in obs.NOTIFY_TOKENS, f"{ad} bildirim jetonu SINIFINA girmemeli"
        assert not hasattr(obs, f"ALARM_{ad}")
    # `durum_sozlugu` (v271) KANONİK DURUM adlarını dondurur (goal_failure/kitap_damga/…) —
    # bir olay ADI o sözlüğün konusu DEĞİLDİR; kayıt gerekmediği BURADA ölçülür, varsayılmaz.
    from meridian import durum_sozlugu as dsz
    assert not any("SEMBOL_ENDEKS" in str(x) for x in dir(dsz)), \
        "olay adı durum sözlüğüne kaydedilmez (sınıf farkı) — sözlük GEVŞETİLMEDİ"
