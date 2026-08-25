"""v310 · ALTYAPI TABLOSU — "inactive" TEK BAŞINA BİR HÜKÜM DEĞİLDİR.

OPERATÖR KUSURU (2026-08-25): "neden kurulu değil, inaktif ve ölçülemedi gözüküyor". Tablo ÜÇ
AYRI DÜNYAYI tek kılıkta gösteriyordu ve SAĞLIKLI olan hâl ARIZA gibi okunuyordu.

CANLIDA ÖLÇÜLEN GERÇEK (A1, systemd 255):
    meridian-backup.service         Type=oneshot  TriggeredBy=meridian-backup.timer(active)
    meridian-tick-watchdog.service  Type=oneshot  TriggeredBy=meridian-tick-watchdog.timer(active)
    meridian-fail-notify.service    Type=oneshot  OnFailureOf=meridian.service   (timer'ı YOK)
    meridian-aylik-bucket-kopya.*   LoadState=not-found                          (KURULMALI)
    litestream.service              LoadState=not-found                          (envanter kopyası)
Üçü de panoda `inactive` / `kurulu değil` diye tek kılıkta görünüyordu. Oysa:
  · oneshot + timer'ı AKTİF  → "sırada" demektir, arıza değil.
  · oneshot + OnFailure bağı → inactive "HİÇBİR ŞEY ARIZALANMADI" demektir, mümkün olan EN İYİ hâl.
  · `not-found` + `deploy/oracle-a1/` altında → KURULMALI (operatör işi, sudo ister).
  · `not-found` + `deploy/` kökünde       → envanter gürültüsü (kurulması BEKLENMİYOR).

BU DOSYA NEYİ ÇİVİLER
---------------------
A. VERİ YOLU — hüküm UYDURULMUYOR, systemd'den geliyor: `systemctl show` çağrısı `Type`,
   `TriggeredBy` ve `OnFailureOf` özelliklerini İSTEMELİ. Çivi argüman listesine bakar (kaynak
   metnine değil): özelliği düşürmek testi kırar.

B. SAĞLIK İDDİASI ANCAK ÖLÇÜLDÜYSE — bu dosyanın en önemli çivisi. `Type` ölçülemediyse ya da
   `TriggeredBy` bilinmeyen bir birimi gösteriyorsa sınıf "sağlıklı" OLAMAZ; "ölçülemedi + neden"
   olur. UYDURMA YASAĞI'nın bu yüzeydeki biçimi budur: "muhtemelen timer'ı vardır" demek, panoya
   ölçülmemiş bir güvence yazmaktır.

C. GERÇEKTEN ÖLÜ SERVİS HÂLÂ DİKKAT ÇEKER — `Type=simple` bir birim `inactive` ise bu bir arızadır
   ve yumuşatma yapılmaz. (a) maddesinin ters yönü: gürültüyü sustururken sinyali de susturmak,
   kusuru düzeltmek değil ikiye katlamaktır.

D. "KURULU DEĞİL" İKİ AYRI İŞTİR — biri operatörden sudo bekler, öteki hiçbir şey beklemez. Tek
   rozet ikisini de "eksik" diye gösteriyordu; ayrımın kaynağı diskteki YOL: `dagit.sh` yalnız
   `deploy/oracle-a1/*.service` dosyalarını canlının birimleriyle kıyaslar — kurulum beklentisinin
   OTORİTESİ odur, bu dosya onun ayrımını izler.

E. ŞABLON BİRİM DOKUNULMADI — `meridian-sprint@.service` için "ölçülemedi" DOĞRU davranıştır
   (hafıza kaydı: "meridian-sprint şablon birim"). Bu turda onu "sağlıklı" saymaya çalışan bir
   iyileştirme, kapatılmış bir tuzağı geri açardı.

F. PANO SINIFI OKUR, HAM DURUMU BASMAZ — `Bilesenler.tsx` rozeti `durum_sinifi`ndan üretmeli.
   Ham `ActiveState` metnini tek başına basmak, kusurun ta kendisiydi.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from meridian import api

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO_KAYNAK = KOK / "ui/src/pano/yuzeyler/sistem/Bilesenler.tsx"
_GEREKCE_ASGARI = 20          # "yok" bir gerekçe değildir


@pytest.fixture(autouse=True)
def _onbellekleri_bosalt(monkeypatch):
    """Sıra bağımsızlığı: infra zarfı ve CPU delta örneği süreç-içi sözlüklerdir."""
    for ad in ("_INFRA_CACHE", "_INFRA_CPU_ORNEK"):
        kutu = getattr(api, ad, None)
        if isinstance(kutu, dict):
            monkeypatch.setattr(api, ad, {})
    yield


def _birim(ad: str, *, sablon: bool = False, beklenen: bool | None = True) -> dict:
    """`_infra_birim_adlari()` çıktısının tek satırı — diske gitmeden."""
    return {"ad": ad, "dosya": ad, "tur": ad.rsplit(".", 1)[-1], "sablon": sablon,
            "yol": f"deploy/oracle-a1/{ad}" if beklenen else f"deploy/{ad}",
            "beklenen": beklenen,
            "beklenen_neden": None if beklenen else "test kurgusu: `deploy/` kökünde duran kopya"}


def _cozumle(birimler: list[dict], ham: dict[str, dict | None], monkeypatch) -> dict[str, dict]:
    """`_infra_bilesenler`i sahte `systemctl show` çıktısıyla koşturur, satırları ada göre verir."""
    monkeypatch.setattr(api.shutil, "which", lambda ad: "/usr/bin/systemctl")
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: ham.get(birim))
    satirlar, neden = api._infra_bilesenler(birimler)
    assert neden is None and satirlar is not None
    return {s["ad"]: s for s in satirlar}


# ---------------------------------------------------------------- A. VERİ YOLU

def test_systemctl_sorgusu_tetikleyici_alanlarini_ister(monkeypatch):
    """Hüküm systemd'den gelmeli: `Type`, `TriggeredBy`, `OnFailureOf` İSTENMELİ.

    Çivi ARGÜMAN LİSTESİNE bakıyor — `_SYSTEMCTL_ALANLARI` içinde adın geçmesi yetmez, o dize
    yorumda da geçebilirdi; ölçülen şey `systemctl`e giden çağrının biçimidir."""
    gorulen: list[list[str]] = []

    class _Cp:
        returncode = 0
        stdout = "Type=oneshot\nLoadState=loaded\n"

    def _sahte_run(argv, **kw):
        gorulen.append(list(argv))
        return _Cp()

    monkeypatch.setattr(api.shutil, "which", lambda ad: "/usr/bin/systemctl")
    import subprocess as _sp
    monkeypatch.setattr(_sp, "run", _sahte_run)
    api._systemctl_show("meridian-backup.service")
    assert gorulen, "`systemctl show` hiç çağrılmadı"
    argv = gorulen[0]
    for alan in ("Type", "TriggeredBy", "OnFailureOf"):
        assert f"--property={alan}" in argv, (
            f"`{alan}` systemd'den İSTENMİYOR — o alan olmadan 'oneshot + timer aktif' hükmü "
            f"ölçülemez, uydurulur. Giden çağrı: {argv}")


def test_uc_govdesi_tetikleyici_alanlarini_tasiyor(monkeypatch, sandbox_state):
    """Uçtan UCA: `/api/infra` satırları sınıfı ve gerekçesini taşımalı (pano onları okuyor)."""
    from fastapi.testclient import TestClient
    monkeypatch.setattr(api.shutil, "which", lambda ad: "/usr/bin/systemctl")
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {
        "LoadState": "loaded", "ActiveState": "active", "SubState": "running",
        "Type": "simple", "TriggeredBy": "", "OnFailureOf": "", "NRestarts": "0"})
    yuk = TestClient(api.app).get("/api/infra?taze=1").json()
    for s in yuk["bilesenler"]:
        assert "durum_sinifi" in s and isinstance(s["durum_sinifi"], str) and s["durum_sinifi"]
        assert isinstance(s.get("durum_sinifi_neden"), str) and \
            len(s["durum_sinifi_neden"].strip()) >= _GEREKCE_ASGARI, \
            f"{s['ad']}: sınıf gerekçesiz — hüküm okuyucuya nedenini söylemiyor"
        assert "servis_turu" in s and "tetikleyen_timerlar" in s and "onfailure_kaynaklari" in s


# ---------------------------------------------------------------- B. SAĞLIK ANCAK ÖLÇÜLDÜYSE

def test_oneshot_timeri_aktifse_inactive_denmez(monkeypatch):
    """CANLI VAKA: `meridian-backup.service` oneshot, timer'ı aktif. `inactive` bir arıza DEĞİL."""
    satir = _cozumle(
        [_birim("meridian-backup.service"), _birim("meridian-backup.timer")],
        {"meridian-backup.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                     "SubState": "dead", "Type": "oneshot",
                                     "TriggeredBy": "meridian-backup.timer", "OnFailureOf": ""},
         "meridian-backup.timer": {"LoadState": "loaded", "ActiveState": "active",
                                   "SubState": "waiting", "Type": "", "TriggeredBy": "",
                                   "OnFailureOf": ""}},
        monkeypatch)["meridian-backup.service"]
    assert satir["durum_sinifi"] == "sirada_timer", (
        f"oneshot + AKTİF timer 'sırada' değil `{satir['durum_sinifi']}` diye sınıflandı — "
        "operatör sağlıklı hâli arıza sanıyor (2026-08-25 kusuru)")
    assert satir["tetikleyen_timerlar"] == ["meridian-backup.timer"]
    assert "meridian-backup.timer" in satir["durum_sinifi_neden"], \
        "gerekçe hangi timer'a dayandığını söylemiyor — okuyucu iddiayı doğrulayamaz"


def test_onfailure_birimi_ariza_yok_der(monkeypatch):
    """CANLI VAKA: `meridian-fail-notify.service` — timer'ı YOK, OnFailure ile tetiklenir.
    `inactive` burada "hiçbir şey arızalanmadı" demektir; mümkün olan EN İYİ hâl."""
    satir = _cozumle(
        [_birim("meridian-fail-notify.service")],
        {"meridian-fail-notify.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                          "SubState": "dead", "Type": "oneshot",
                                          "TriggeredBy": "",
                                          "OnFailureOf": "meridian.service"}},
        monkeypatch)["meridian-fail-notify.service"]
    assert satir["durum_sinifi"] == "ariza_yok_onfailure", (
        f"OnFailure birimi `{satir['durum_sinifi']}` diye sınıflandı — timer'ı olmadığı için "
        "'tetikleyicisi yok' sanılıyor olabilir; oysa tetikleyicisi ARIZANIN KENDİSİ")
    assert satir["onfailure_kaynaklari"] == ["meridian.service"]
    assert "meridian.service" in satir["durum_sinifi_neden"]


def test_timeri_oluyken_saglik_iddia_edilmez(monkeypatch):
    """Timer ÖLÇÜLDÜ ve aktif DEĞİL: bu gerçek bir boşluktur, 'sırada' diye yumuşatılamaz."""
    satir = _cozumle(
        [_birim("meridian-backup.service"), _birim("meridian-backup.timer")],
        {"meridian-backup.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                     "SubState": "dead", "Type": "oneshot",
                                     "TriggeredBy": "meridian-backup.timer", "OnFailureOf": ""},
         "meridian-backup.timer": {"LoadState": "loaded", "ActiveState": "inactive",
                                   "SubState": "dead", "Type": "", "TriggeredBy": "",
                                   "OnFailureOf": ""}},
        monkeypatch)["meridian-backup.service"]
    assert satir["durum_sinifi"] == "tetikleyici_bozuk", (
        f"ÖLÜ timer'lı oneshot `{satir['durum_sinifi']}` diye sınıflandı — yedek hiç koşmuyor "
        "olabilir ve pano bunu 'sırada' diye sustururdu")


def test_tetikleyici_olculemezse_saglik_iddia_edilmez(monkeypatch):
    """`TriggeredBy` bu makinede ÖLÇÜLMEMİŞ bir birimi gösteriyor: sağlık kurulamaz.

    UYDURMA YASAĞI'nın bu yüzeydeki biçimi: "adı geçiyorsa vardır, varsa aktiftir" bir ÖLÇÜM
    değil, bir varsayımdır."""
    satir = _cozumle(
        [_birim("meridian-backup.service")],
        {"meridian-backup.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                     "SubState": "dead", "Type": "oneshot",
                                     "TriggeredBy": "bilinmeyen.timer", "OnFailureOf": ""}},
        monkeypatch)["meridian-backup.service"]
    assert satir["durum_sinifi"] == "tetikleyici_olculemedi", (
        f"ölçülmemiş tetikleyiciyle `{satir['durum_sinifi']}` hükmü kuruldu")
    assert "bilinmeyen.timer" in satir["durum_sinifi_neden"]


def test_tur_olculemezse_saglik_iddia_edilmez(monkeypatch):
    """`Type` gelmediyse birimin oneshot olup olmadığı BİLİNMİYOR — sessizce 'sırada' denemez."""
    satir = _cozumle(
        [_birim("meridian-backup.service"), _birim("meridian-backup.timer")],
        {"meridian-backup.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                     "SubState": "dead",
                                     "TriggeredBy": "meridian-backup.timer", "OnFailureOf": ""},
         "meridian-backup.timer": {"LoadState": "loaded", "ActiveState": "active",
                                   "SubState": "waiting"}},
        monkeypatch)["meridian-backup.service"]
    assert satir["servis_turu"] is None
    assert isinstance(satir.get("servis_turu_neden"), str) and \
        len(satir["servis_turu_neden"].strip()) >= _GEREKCE_ASGARI
    assert satir["durum_sinifi"] not in ("sirada_timer", "ariza_yok_onfailure"), (
        f"`Type` ölçülmeden sağlık sınıfı `{satir['durum_sinifi']}` verildi")


def test_oneshot_tetikleyicisiz_ise_saglikli_sayilmaz(monkeypatch):
    """oneshot ama HİÇ tetikleyicisi yok: bağlanmayı bekleyen bir birim olabilir. Sağlık YOK."""
    satir = _cozumle(
        [_birim("meridian-barsarchive.service")],
        {"meridian-barsarchive.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                          "SubState": "dead", "Type": "oneshot",
                                          "TriggeredBy": "", "OnFailureOf": ""}},
        monkeypatch)["meridian-barsarchive.service"]
    assert satir["durum_sinifi"] == "tetikleyici_yok"


# ---------------------------------------------------------------- C. ÖLÜ SERVİS SUSTURULMAZ

def test_gercekten_olu_servis_dikkat_cekmeye_devam_eder(monkeypatch):
    """(a)'nın TERS YÖNÜ: `Type=simple` bir birim `inactive` ise bu ARIZADIR, yumuşatılmaz."""
    satir = _cozumle(
        [_birim("meridian.service")],
        {"meridian.service": {"LoadState": "loaded", "ActiveState": "inactive", "SubState": "dead",
                              "Type": "simple", "TriggeredBy": "", "OnFailureOf": ""}},
        monkeypatch)["meridian.service"]
    assert satir["durum_sinifi"] == "olu", (
        f"koşması gereken servis `{satir['durum_sinifi']}` diye sınıflandı — gürültüyü "
        "susturayım derken SİNYALİ susturmak, kusuru ikiye katlamaktır")


def test_arizali_birim_ayri_sinif(monkeypatch):
    """`failed` ile `inactive` aynı kovaya girmez — biri koşmadı, öteki koştu ve DÜŞTÜ."""
    satir = _cozumle(
        [_birim("meridian-backup.service"), _birim("meridian-backup.timer")],
        {"meridian-backup.service": {"LoadState": "loaded", "ActiveState": "failed",
                                     "SubState": "failed", "Type": "oneshot",
                                     "TriggeredBy": "meridian-backup.timer", "OnFailureOf": ""},
         "meridian-backup.timer": {"LoadState": "loaded", "ActiveState": "active",
                                   "SubState": "waiting"}},
        monkeypatch)["meridian-backup.service"]
    assert satir["durum_sinifi"] == "arizali", (
        f"DÜŞMÜŞ oneshot `{satir['durum_sinifi']}` diye sınıflandı — timer aktif diye arıza "
        "'sırada' gibi gösterildi")


# ---------------------------------------------------------------- D. "KURULU DEĞİL" İKİ İŞTİR

def test_kurulu_degil_iki_alt_sebebe_ayrilir(monkeypatch):
    """`meridian-aylik-bucket-kopya` KURULMALI (sudo, operatör işi); `litestream.service`
    `deploy/` kökünde duran eski kopyadır ve kurulması BEKLENMİYOR."""
    satirlar = _cozumle(
        [_birim("meridian-aylik-bucket-kopya.service", beklenen=True),
         _birim("litestream.service", beklenen=False)],
        {"meridian-aylik-bucket-kopya.service": {"LoadState": "not-found",
                                                 "ActiveState": "inactive", "SubState": "dead"},
         "litestream.service": {"LoadState": "not-found", "ActiveState": "inactive",
                                "SubState": "dead"}},
        monkeypatch)
    assert satirlar["meridian-aylik-bucket-kopya.service"]["durum_sinifi"] == "kurulmali"
    assert satirlar["litestream.service"]["durum_sinifi"] == "envanter_gurultusu"
    assert satirlar["meridian-aylik-bucket-kopya.service"]["durum_sinifi"] != \
        satirlar["litestream.service"]["durum_sinifi"], (
        "iki 'kurulu değil' aynı sınıfa düştü — biri operatörden sudo bekliyor, öteki hiçbir şey")


def test_kurulum_beklentisi_disk_yolundan_gelir_uydurulmaz():
    """Beklentinin OTORİTESİ `dagit.sh`: yalnız `deploy/oracle-a1/*.service` canlıyla kıyaslanır.
    Bu çivi GERÇEK diski okur — kurgu bir listeyle geçmek imkânsız olmalı."""
    kaynak = api._infra_birim_adlari()
    tablo = {b["ad"]: b for b in kaynak["birimler"]}
    assert "litestream.service" in tablo and "meridian-backup.service" in tablo, \
        f"deploy/ taraması beklenen dosyaları bulamadı: {sorted(tablo)}"
    assert tablo["litestream.service"]["beklenen"] is False, \
        "`deploy/` kökündeki kopya KURULMASI BEKLENEN sayıldı — panoya sahte bir eksik yazar"
    assert isinstance(tablo["litestream.service"].get("beklenen_neden"), str) and \
        len(tablo["litestream.service"]["beklenen_neden"].strip()) >= _GEREKCE_ASGARI
    assert tablo["meridian-backup.service"]["beklenen"] is True, \
        "`deploy/oracle-a1/` altındaki birim 'kurulması beklenmiyor' sayıldı — gerçek eksik susardı"
    # ADI İKİ YERDE GEÇEN BİRİM: `deploy/meridian.service` (eski/genel) VE
    # `deploy/oracle-a1/meridian.service` (kurulan). Beklenti host dizininden gelmeli, tarama
    # sırasından değil — yoksa canlının ana birimi "envanter gürültüsü" diye susturulurdu.
    assert tablo["meridian.service"]["beklenen"] is True


# ---------------------------------------------------------------- E. ŞABLON DOKUNULMADI

def test_sablon_birim_hala_olculemedi_der(monkeypatch):
    """Hafıza kaydı "meridian-sprint şablon birim": düz adla sorgu SAHTE `inactive` verir.
    Bu turun iyileştirmesi o kapatılmış tuzağı GERİ AÇMAMALI."""
    satir = _cozumle(
        [_birim("meridian-sprint@.service", sablon=True)],
        {"meridian-sprint@.service": {"LoadState": "loaded", "ActiveState": "inactive",
                                      "SubState": "dead", "Type": "oneshot"}},
        monkeypatch)["meridian-sprint@.service"]
    assert satir["durum"] is None, "şablon birimin durumu UYDURULDU"
    assert satir["durum_sinifi"] == "olculemedi", (
        f"şablon birim `{satir['durum_sinifi']}` diye sınıflandı — 'koşmuyor' ile 'koştu, aday "
        "geçmedi' bir kez karıştı, ikinci kez karışmasın")
    # SINIF YETMEZ, GEREKÇE DE ŞABLONA ÖZGÜ OLMALI: genel bir "ölçülemedi" metni, operatörü
    # systemctl arızası aramaya gönderir ve gerçek cevabın nerede olduğunu (`/api/sprint`)
    # söylemez. Şablon dalı silindiğinde sınıf tesadüfen doğru kalır — gerekçe kalmaz.
    gerekce = satir["durum_sinifi_neden"]
    assert "ŞABLON" in gerekce, f"gerekçe şablon tuzağını adlandırmıyor: {gerekce!r}"
    assert "/api/sprint" in gerekce, (
        f"gerekçe gerçek durumun NEREDEN okunacağını söylemiyor: {gerekce!r}")


# ---------------------------------------------------------------- F. PANO SINIFI OKUR

def _pano() -> str:
    return PANO_KAYNAK.read_text(encoding="utf-8")


def test_pano_rozeti_durum_sinifindan_uretir():
    """Rozet `durum_sinifi`ndan okunmalı — ham `ActiveState` metnini basmak kusurun ta kendisiydi."""
    s = _pano()
    assert re.search(r"b\.durum_sinifi", s), \
        "`Bilesenler.tsx` `durum_sinifi` alanını hiç okumuyor — uçtaki hüküm panoya ulaşmıyor"
    # Rozetin GÖVDESİNDE ham durum tek başına basılmamalı. `{b.durum}` bir JSX ÇOCUĞU olarak
    # geçiyorsa "inactive" yine ekrana düşer.
    assert not re.search(r"^\s*\{b\.durum\}\s*$", s, re.M), (
        "ham `ActiveState` hâlâ rozet metni olarak basılıyor — 'inactive' tek başına bir hüküm "
        "değildir (2026-08-25 operatör kusuru)")


def test_pano_saglikli_bekleyisi_arizadan_ayri_etiketler():
    """Üç sınıfın ÜÇÜ DE panoda AYRI etikete sahip olmalı; aynı metne düşerlerse kusur sürer."""
    s = _pano()
    etiketler = {}
    for sinif in ("sirada_timer", "ariza_yok_onfailure", "olu", "kurulmali",
                  "envanter_gurultusu", "tetikleyici_olculemedi"):
        m = re.search(rf'{sinif}:\s*\{{[^}}]*etiket:\s*"([^"]+)"', s)
        assert m, f"`{sinif}` sınıfı pano etiket tablosunda YOK — uç hüküm veriyor, pano basmıyor"
        etiketler[sinif] = m.group(1)
    assert len(set(etiketler.values())) == len(etiketler), \
        f"iki sınıf AYNI etikete düştü, ayrım ekranda kayboldu: {etiketler}"
    assert "inactive" not in etiketler["sirada_timer"].lower()
    assert "inactive" not in etiketler["ariza_yok_onfailure"].lower()
    assert etiketler["kurulmali"] != etiketler["envanter_gurultusu"], \
        "iki 'kurulu değil' ekranda hâlâ tek kılıkta"


def test_pano_kurulmali_ve_gurultuyu_ayri_sayar():
    """Üst özet de ayrılmalı: "kurulu değil: 3" operatöre ÜÇ iş varmış gibi görünüyordu; gerçekte
    bir tanesi (aylık bucket kopyası) eylem, ikisi envanter gürültüsü.

    Çivi ETİKET TABLOSUNU SÖKÜP bakıyor: iki sınıf adının orada geçmesi kolaydır ve hiçbir şey
    kanıtlamaz — sayım mantığında da geçmeleri gerekir."""
    s = _pano()
    kalan = re.sub(r"const SINIF[\s\S]*?\n\};\n", "", s, count=1)
    assert "const SINIF" not in kalan, "etiket tablosu sökülemedi — çivi yanlış yeri ölçüyor"
    for sinif in ("kurulmali", "envanter_gurultusu"):
        assert f'"{sinif}"' in kalan, (
            f"`{sinif}` yalnız etiket tablosunda geçiyor, SAYIM mantığında değil — üst özet iki "
            "'kurulu değil'i hâlâ tek sayıya topluyor, gerçek eylem gürültüde kayboluyor")
    etiketler = re.findall(r'<Satir etiket="([^"]+)"', s)
    assert not any("Kurulu değil" in e for e in etiketler), \
        f"birleşik 'Kurulu değil' satırı duruyor — ayrım ekranda görünmüyor: {etiketler}"
    assert any("Kurulmalı" in e for e in etiketler) and any("Envanter" in e for e in etiketler), \
        f"üst özette iki ayrı satır yok: {etiketler}"
