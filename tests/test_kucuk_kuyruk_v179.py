"""test_kucuk_kuyruk_v179.py — KÜÇÜK-KUYRUK turunun üç kalemini çiviler (2026-08-02).

Üç kalem de "bir kez düzeltildi sanılan ama kaynağa girmemiş" sınıfındandır; bu yüzden üçünün de
ÇİVİSİ kaynağa yazılır, hükmü değil.

  1. STATİK ÖNBELLEK SÖZLEŞMESİ (`api.py`). "dagit'ten sonra değişikliği göremedim" vakası. Eski
     hâlde `If-None-Match` HİÇ okunmuyordu (starlette 1.3.1'de 304 dalı yalnız `StaticFiles`
     montajındadır ve bu dosyada montaj bilerek yok) ve ETag mtime'dan türüyordu. Testler ETag'in
     İÇERİKTEN türediğini ve 304 yolunun gerçekten koştuğunu ölçer.

  2. TICK-BEKÇİSİ EŞİĞİ (`deploy/oracle-a1/`). İki kusur birden: (a) eşik 10800 sn'de
     "3sa-GEÇİCİ" etiketiyle donmuştu, (b) mantık birim dosyasının ExecStart'ına gömülüydü ve
     systemd `$YAS`'ı bash'e vermeden ikame ettiği için bekçi HİÇ ateşleyemiyordu. Testler hem
     kalıcı 45 dk değerini hem de "birimde `$` yok" sınıf-kuralını çiviler; ayrıca betiği GERÇEKTEN
     koşturup beş senaryoyu ölçer (sahte `systemctl` ile — canlıya dokunmaz).

  3. RESTART-PATLAMASI MUAFİYETİ (`watchdog.py`). Canlı ölçümle (aşağıdaki sayılar) tepe GERÇEK ve
     restart kaynaklı çıktı; muafiyet eklendi. Testler muafiyetin YALNIZ tepe sayacına
     uygulandığını, 24 saatlik dağılımı DEĞİŞTİRMEDİĞİNİ ve BEYAN satırının her hâlde çıktığını
     ölçer — sessiz maskeleme yasağının çivisi.

CANLI SİSTEME DOKUNMAZ: SSH yok, `state/` yazımı yok (sandbox), depo dosyası yazımı yok
(statik testler `api.WEB`'i tmp_path'e yönlendirir).
"""
from __future__ import annotations

import json
import shutil
import os
import pathlib
import subprocess
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from meridian import api, watchdog

REPO = pathlib.Path(__file__).resolve().parent.parent
BIRIMLER = REPO / "deploy" / "oracle-a1"
BETIK = BIRIMLER / "tick_watchdog.sh"
SERVICE = BIRIMLER / "meridian-tick-watchdog.service"
TIMER = BIRIMLER / "meridian-tick-watchdog.timer"


# =================================================================================================
# 1) STATİK ÖNBELLEK SÖZLEŞMESİ — ETag + no-cache + 304
# =================================================================================================

# (rota yolu, WEB altındaki dosya adı). Kaynakla senkron kalması gereken liste: yeni bir ad-ad
# statik rota eklenip buraya eklenmezse `test_statik_rota_envanteri_tam` düşer.
STATIK_ROTALAR = [
    ("/", "index.html"),
    ("/app.js", "app.js"),
    ("/theme.js", "theme.js"),
    ("/landing.js", "landing.js"),
    ("/workflow.js", "workflow.js"),
    ("/palette.js", "palette.js"),
    ("/landing", "landing.html"),
    ("/workflow", "workflow.html"),
]


@pytest.fixture
def istemci():
    return TestClient(api.app)


@pytest.fixture
def sahte_web(tmp_path, monkeypatch):
    """`api.WEB`'i tmp dizine yönlendirir — depo dosyalarına DOKUNULMAZ.

    `_statik` `WEB`i çağrı anında okur (modül globali), yani yönlendirme rotaları da kapsar."""
    web = tmp_path / "web"
    web.mkdir()
    for _, ad in STATIK_ROTALAR:
        (web / ad).write_text(f"// {ad} sahte içerik\n")
    monkeypatch.setattr(api, "WEB", web)
    return web


@pytest.mark.parametrize("yol,ad", STATIK_ROTALAR)
def test_statik_rota_nocache_ve_etag_gonderir(istemci, sahte_web, yol, ad):
    r = istemci.get(yol)
    assert r.status_code == 200, yol
    cc = r.headers.get("cache-control", "")
    # Üçü birden: sakla-ama-doğrula (`no-cache`), sıfır tazelik (`max-age=0`), bayat servis yasağı.
    for parca in ("no-cache", "max-age=0", "must-revalidate"):
        assert parca in cc, f"{yol}: Cache-Control'de `{parca}` yok — {cc!r}"
    etag = r.headers.get("etag")
    assert etag and etag.startswith('"') and etag.endswith('"'), f"{yol}: güçlü ETag yok — {etag!r}"


@pytest.mark.parametrize("yol,ad", STATIK_ROTALAR)
def test_if_none_match_304_dondurur_ve_govde_bostur(istemci, sahte_web, yol, ad):
    ilk = istemci.get(yol)
    etag = ilk.headers["etag"]
    ikinci = istemci.get(yol, headers={"If-None-Match": etag})
    assert ikinci.status_code == 304, f"{yol}: 304 yolu çalışmıyor"
    assert ikinci.content == b"", f"{yol}: 304 gövde taşıyor"
    # 304 de doğrulama başlıklarını taşımalı — yoksa tarayıcı bir sonraki turda etiketsiz kalır.
    assert ikinci.headers.get("etag") == etag
    assert "no-cache" in ikinci.headers.get("cache-control", "")


def test_yanlis_etag_200_ve_govde_dondurur(istemci, sahte_web):
    r = istemci.get("/app.js", headers={"If-None-Match": '"kesinlikle-baska-bir-etiket"'})
    assert r.status_code == 200
    assert r.content, "yanlış etiketle gövde gelmedi — 304 yanlış ateşliyor"


def test_etag_ICERIKTEN_turer_mtimeden_degil(istemci, sahte_web):
    """Vakanın çivisi: aynı içerik → aynı etiket (mtime değişse bile); farklı içerik → farklı etiket.

    Sıra A → B → A. Üçüncü adımda dosyanın mtime'ı ilk adımdakinden FARKLIDIR; etiket yine de ilk
    etikete DÖNMELİDİR. mtime tabanlı bir etiket bu testi geçemez."""
    hedef = sahte_web / "app.js"
    hedef.write_text("A" * 100)
    etag_a1 = istemci.get("/app.js").headers["etag"]
    hedef.write_text("B" * 250)                 # boyut da değişir → memo anahtarı kesin ıskalar
    etag_b = istemci.get("/app.js").headers["etag"]
    hedef.write_text("A" * 100)
    etag_a2 = istemci.get("/app.js").headers["etag"]
    assert etag_a1 != etag_b, "içerik değişti ama ETag aynı kaldı — bayat kopya servis edilirdi"
    assert etag_a1 == etag_a2, "içerik geri geldi ama ETag değişti — ETag içerikten türemiyor"


def test_etag_dosya_bazinda_ayrisir(istemci, sahte_web):
    etiketler = {yol: istemci.get(yol).headers["etag"] for yol, _ in STATIK_ROTALAR}
    assert len(set(etiketler.values())) == len(etiketler), \
        f"iki rota aynı ETag'i paylaşıyor — {etiketler}"


@pytest.mark.parametrize("baslik", [
    '*',                                                  # RFC 9110: her etiketle eşleşir
    'W/{etag}',                                           # ara katman zayıflatmış olabilir
    '"baska", {etag}',                                    # virgüllü liste
    '{etag} ',                                            # kenar boşluğu
])
def test_if_none_match_bicimleri(istemci, sahte_web, baslik):
    etag = istemci.get("/theme.js").headers["etag"]
    r = istemci.get("/theme.js", headers={"If-None-Match": baslik.format(etag=etag)})
    assert r.status_code == 304, f"If-None-Match biçimi tanınmadı: {baslik!r}"


def test_statik_rota_envanteri_tam():
    """Ad-ad statik rotaların TAMAMI `_statik`ten geçer — yeni bir rota `FileResponse`la eklenirse
    (eski desen) önbellek sözleşmesi o rotada SESSİZCE kaybolurdu."""
    import inspect
    kaynak = inspect.getsource(api)
    # Rota gövdelerinde ham `FileResponse(WEB / ...)` KALMAMALI (tek istisna `_statik`in kendi içi).
    ham = [s for s in kaynak.splitlines()
           if "FileResponse(WEB /" in s]
    assert not ham, f"ad-ad statik rota `_statik` dışına çıkmış: {ham}"
    yollar = {r.path for r in api.app.routes if hasattr(r, "path")}
    for yol, _ in STATIK_ROTALAR:
        assert yol in yollar, f"{yol} rotası kaybolmuş — envanter listesi kaynakla ayrıştı"


def test_eksik_dosya_304_uydurmaz(istemci, sahte_web):
    """Etiket üretilemeyen dosya için uydurma bir 200/etiket YOK — hüküm 404'tür."""
    (sahte_web / "app.js").unlink()
    r = istemci.get("/app.js")
    assert r.status_code == 404
    assert "etag" not in {k.lower() for k in r.headers}


# =================================================================================================
# 2) TICK-BEKÇİSİ — eşik 45 dk (kalıcı) + systemd `$` sınıfı + davranış
# =================================================================================================

def test_bekci_uc_dosyasi_depoda_versiyonlu():
    """Bu turdan önce bekçi YALNIZ A1'in /etc/systemd/system'inde yaşıyordu: gözden geçirmeye,
    teste ve yeniden kuruluma dahil DEĞİLDİ. Üçü de depoda olmalı."""
    for p in (BETIK, SERVICE, TIMER):
        assert p.exists(), f"{p.name} depoda yok"
    assert os.access(BETIK, os.X_OK), "tick_watchdog.sh çalıştırılabilir değil"


def test_esik_45dk_kalici_ve_gecici_etiketi_yok():
    metin = BETIK.read_text()
    assert "BAYAT_VARSAYILAN=2700" in metin, "kalıcı eşik 2700 sn (45 dk) değil"
    # "10800" YALNIZ tarihçe anlatımında (kök-neden yorumu) geçebilir; hiçbir ATAMADA geçemez.
    atamalar = [s for s in metin.splitlines()
                if "=" in s and not s.lstrip().startswith("#")]
    assert not [s for s in atamalar if "10800" in s], \
        f"eski 3 saatlik eşik hâlâ bir atamada: {[s for s in atamalar if '10800' in s]}"
    # Kural: yürürlükteki DEĞER hiçbir yerde geçici etiketle anılmaz. Etiket yalnız kök-neden
    # yorumunda geçebilir; birim Description'ında GEÇEMEZ, çünkü `systemctl list-units` operatöre
    # tam onu gösterir (canlıda iki gün boyunca "3sa-GECICI(...sabah 45dk-normale döner)" yazıyordu).
    aciklama = [s for s in SERVICE.read_text().splitlines() if s.startswith("Description=")]
    assert aciklama, "birimde Description yok"
    for etiket in ("GEÇİCİ", "GECICI", "3sa"):
        assert etiket not in aciklama[0], f"birim Description'ı hâlâ geçici etiket taşıyor: {aciklama[0]}"
    assert "45 dk" in aciklama[0], f"Description kalıcı eşiği söylemiyor: {aciklama[0]}"


def test_birim_execstart_dolar_isareti_tasimaz():
    """SINIF KURALI (fail-notify çok-satır-Python + `Environment=` satır-sonu yorumu vakalarının
    üçüncü kuşağı): systemd, ExecStart'taki `$VAR`/`${VAR}`yı kabuğa VERMEDEN kendi sözlüğünden
    ikame eder ve bilinmeyeni BOŞ dizgeye çevirir. Mantık birimde yaşayamaz."""
    for satir in SERVICE.read_text().splitlines():
        if satir.startswith("ExecStart="):
            assert "$" not in satir, f"ExecStart `$` taşıyor — systemd ikamesi onu boşaltır: {satir}"
            assert satir.endswith(".sh"), f"ExecStart bir betik çağırmıyor: {satir}"
            break
    else:
        pytest.fail("birimde ExecStart yok")


def test_deploy_sh_bekciyi_KURAR():
    """TAKİP KALEMİ (2026-08-02): `deploy.sh` bekçiyi kurmuyordu — bekçi 2026-07-31'de CANLIDA elle
    doğmuş ve depoya hiç girmemişti. Taze kurulum ve `cutover.sh` (adım 4 bu betiği çağırır)
    panoyu asılı-tick korumasız canlıya çıkarırdı."""
    d = (BIRIMLER / "deploy.sh").read_text()
    for parca in ("meridian-tick-watchdog.service /etc/systemd/system/",
                  "meridian-tick-watchdog.timer   /etc/systemd/system/"):
        assert parca in d, f"deploy.sh birimi kopyalamıyor: {parca}"
    assert "enable --now meridian-tick-watchdog.timer" in d, "timer enable edilmiyor"
    # ÇALIŞTIRMA BİTİ: rsync izni her zaman taşımaz; `Type=oneshot` 203/EXEC ile SESSİZCE ölür.
    assert "chmod +x deploy/oracle-a1/tick_watchdog.sh" in d, "betiğin çalıştırma biti garanti edilmiyor"


def test_deploy_sh_bekciyi_TEST_ATESLER():
    """"Kurulu != çalışır" (fail-notify dersi: birim iki gün kuruluydu, ilk ateşlemede düştü).
    Kurulum adımı üç ayrı gerçeği ölçmeli ve hiçbiri diğerinin yerine geçmemeli."""
    d = (BIRIMLER / "deploy.sh").read_text()
    assert "systemctl start meridian-tick-watchdog.service" in d, "birim test-ateşlenmiyor"
    assert 'if [ ! -x /opt/meridian/deploy/oracle-a1/tick_watchdog.sh ]' in d, \
        "ExecStart hedefinin çalıştırılabilirliği ölçülmüyor"
    assert 'if [ "$TICK_TIMER" != "active" ]' in d, "timer aktifliği ölçülmüyor"
    # Çıktı kapısı: eski gömülü sürümün ölü olduğu YALNIZ çıktısından ("...ilerleme var (s)")
    # anlaşılıyordu. Hüküm satırı yaşı SAYIYLA basmazsa kurulum DURMALI.
    assert '*"ilerleme var ("[0-9]*' in d, "hüküm satırı desen kapısı yok (systemd `$` ikamesi sınıfı)"


def test_cutover_dogrulama_listesinde_bekci_VAR():
    """Cutover doğrulama tablosu operatörün gördüğü SON tablodur; orada olmayan koruma,
    olmadığı fark edilmeden canlıya çıkar."""
    c = (BIRIMLER / "cutover.sh").read_text()
    assert "meridian-tick-watchdog.timer" in c, "cutover doğrulama listesinde bekçi yok"
    assert "tick-watchdog satır" in c, "cutover bekçinin hüküm satırını göstermiyor"


@pytest.mark.parametrize("ad", ["deploy.sh", "cutover.sh", "tick_watchdog.sh", "bakim_h9.sh"])
def test_dagitim_betikleri_sozdizimi_gecerli(ad):
    """`bash -n` çivisi. GEREKÇE CANLI VAKADIR (bu turda yaşandı): cutover.sh'ın uzak komutları
    TEK TIRNAKLI dizgilerdir ve içine yazılan tek bir kesme işareti ("adım 4'teki") dizgiyi
    kapatıp betiği sözdizimi hatasıyla düşürdü. Böyle bir betik ancak BAKIM PENCERESİNDE,
    canlı kesintinin ortasında patlardı — bu test onu masada yakalar."""
    p = subprocess.run(["bash", "-n", str(BIRIMLER / ad)], capture_output=True, text=True)
    assert p.returncode == 0, f"{ad} sözdizimi geçersiz: {p.stderr}"


def test_timer_kadansi_esikten_kucuk():
    metin = TIMER.read_text()
    assert "OnUnitActiveSec=15min" in metin
    # 15 dk < 45 dk: bayatlık en geç 60 dk'da hüküm görür. Kadans eşiğe eşit olsaydı en kötü hâl
    # 90 dk olurdu — kurucu vakanın (73 dk) tamamından uzun, yani bekçi vakayı kaçırırdı.
    assert 15 * 60 < 2700


def test_seans_farkindaligi_olculdu_ve_takvim_bagi_YOK():
    """Brief'in sorusu ölçüldü: hafta sonu tick yok → 45 dk sahte alarm üretir mi? HAYIR.
    Bu test iki şeyi birden korur: (a) betiğe sessizce bir takvim bağımlılığı eklenmesin
    (ölçülmemiş çözüm), (b) ölçümün SAYILARI kaynaktan silinmesin (iddia kanıtsız kalmasın)."""
    metin = BETIK.read_text()
    # YALNIZ KOŞAN SATIRLAR: yorumlarda `mcal` sözcüğü GEÇER (kararın gerekçesi orada anlatılıyor);
    # yasak olan onu çağıran koddur.
    kod = "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))
    for yasak in ("mcal", "market_calendar", "barclock", "pandas_market_calendars", "date +%u"):
        assert yasak not in kod, f"betiğe ölçülmemiş takvim bağı sızmış: {yasak}"
    for kanit in ("302 sn", "73,1 dk", "SEANS FARKINDALIĞI"):
        assert kanit in metin, f"ölçüm kanıtı kaynaktan silinmiş: {kanit!r}"


# ---- Betiğin GERÇEK koşumu (sahte systemctl; canlıya dokunmaz) --------------------------------

def _kos(tmp_path, *, yas_s: int | None, ortam: dict | None = None,
         ayakta_s: int = 9999, durum_bozuk: bool = False, durum_yok: bool = False):
    """Betiği izole bir kum havuzunda koşturur. `systemctl` SAHTEdir ve çağrıları dosyaya yazar."""
    kutu = tmp_path / "bin"
    kutu.mkdir(exist_ok=True)
    cagri = tmp_path / "systemctl_cagrilari.txt"
    # ActiveEnterTimestampMonotonic mikrosaniyedir; sahte /proc/uptime saniyedir.
    simdi_us = 10_000_000_000
    basladi_us = simdi_us - ayakta_s * 1_000_000
    (kutu / "systemctl").write_text(
        "#!/bin/sh\n"
        f'if [ "$1" = "show" ]; then echo {basladi_us}; exit 0; fi\n'
        f'echo "$@" >> {cagri}\n'
    )
    (kutu / "systemctl").chmod(0o755)
    mono = tmp_path / "uptime"
    mono.write_text(f"{simdi_us / 1_000_000:.2f} 0.00\n")

    durum = tmp_path / "scheduler_status.json"
    if durum_bozuk:
        durum.write_text("{ bu json degil")
    elif not durum_yok:
        t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=yas_s or 0)
        durum.write_text(json.dumps({"updated": t.isoformat(timespec="seconds")}))

    env = {**os.environ,
           "PATH": f"{kutu}:{os.environ.get('PATH','')}",
           "MERIDIAN_TICK_DURUM": str(durum),
           "MERIDIAN_TICK_MONO_KAYNAK": str(mono),
           "MERIDIAN_TICK_BIRIM": "meridian.service",
           **(ortam or {})}
    p = subprocess.run(["bash", str(BETIK)], capture_output=True, text=True, env=env, timeout=60)
    return p, (cagri.read_text() if cagri.exists() else "")


def _yas_oku(stdout: str) -> int:
    """Hüküm satırından yaşı SAYI olarak söker. Yoksa test düşer — çünkü eski gömülü sürümün
    kusuru tam olarak burada sayı OLMAMASIydı (`(s)`)."""
    import re as _re
    m = _re.search(r"\((\d+)s / eşik (\d+)s\)", stdout)
    assert m, f"yaş sayısı çıktıda yok (eski `$` ikamesi kusuru): {stdout!r}"
    return int(m.group(1))


def test_taze_damga_restart_etmez(tmp_path):
    p, cagrilar = _kos(tmp_path, yas_s=120)
    assert p.returncode == 0, p.stderr
    assert "ilerleme var" in p.stdout, p.stdout
    assert "eşik 2700s" in p.stdout, f"eşik çıktıda beyan edilmiyor: {p.stdout}"
    assert "restart" not in cagrilar, f"taze damgada restart çağrıldı: {cagrilar}"


def test_yasin_gercekten_okundugu__eski_gomulu_surumun_kusuru(tmp_path):
    """Eski gömülü sürümün kanıtı `(s)` basmasıydı: `${YAS}` boş genişliyordu. Yeni sürüm SAYI basar.

    TOLERANS 0..3 sn: damga saniye çözünürlüklüdür ve alt-süreç başlatma ölçülebilir zaman alır.
    Sıfır toleranslı bir eşitlik, testi kendi gürültü kaynağına çevirirdi."""
    p, _ = _kos(tmp_path, yas_s=137)
    yas = _yas_oku(p.stdout)
    assert 137 <= yas <= 140, f"okunan yaş beklenen aralıkta değil: {yas}"


def test_bayat_damga_restart_eder(tmp_path):
    p, cagrilar = _kos(tmp_path, yas_s=2701)          # eşiğin 1 sn üstü
    assert p.returncode == 0, p.stderr
    assert "bayat" in p.stdout and "yeniden başlatılıyor" in p.stdout, p.stdout
    assert "restart meridian.service" in cagrilar, f"restart çağrılmadı: {cagrilar!r}"


def test_esik_alti_sinir_restart_etmez(tmp_path):
    """Eşiğin hemen ALTI ateşlemez. (Tam eşik saniyesi sınanmaz: damga saniye çözünürlüklüdür ve
    betiğin koşumu ölçülebilir zaman alır — ±1 sn'lik bir yarışı teste gömmek, testin kendisini
    gürültü kaynağı yapardı. Karşı uç `test_bayat_damga_restart_eder`te 2701 ile çivili.)"""
    p, cagrilar = _kos(tmp_path, yas_s=2690)
    assert "ilerleme var" in p.stdout, p.stdout
    assert "restart" not in cagrilar
    assert "eşik 2700s" in p.stdout


def test_olculemeyen_durum_restart_ETMEZ_ve_sessiz_kalmaz(tmp_path):
    """Uydurma yasağı: dosya okunamıyorsa "0 sn bayat" (yani sağlıklı) demek bir İDDİAdır.
    Eski gömülü sürüm `|| echo 0` ile tam bunu yapıyordu."""
    for kw in ({"durum_bozuk": True}, {"durum_yok": True}):
        p, cagrilar = _kos(tmp_path, yas_s=None, **kw)
        assert "ÖLÇÜLEMEDİ" in p.stdout, f"{kw}: ölçülemeyen hâl sessiz — {p.stdout!r}"
        assert "restart" not in cagrilar, f"{kw}: ölçülemeyen hâlde restart edildi"
        assert p.returncode == 0


def test_YAS_lutfu_taze_dogmus_sureci_yeniden_baslatmaz(tmp_path):
    """Restart'tan hemen sonra durum dosyası HÂLÂ eski `updated`ı taşır. Lütuf olmasaydı bu
    kendini besleyen bir restart döngüsü olurdu."""
    p, cagrilar = _kos(tmp_path, yas_s=99999, ayakta_s=30)
    assert "YAS lütfu" in p.stdout and "hüküm VERİLMEDİ" in p.stdout, p.stdout
    assert "restart" not in cagrilar, f"lütuf penceresinde restart edildi: {cagrilar!r}"


def test_YAS_lutfu_disinda_bayatlik_hukum_gorur(tmp_path):
    p, cagrilar = _kos(tmp_path, yas_s=99999, ayakta_s=301)   # lütuf 300 sn
    assert "restart meridian.service" in cagrilar, p.stdout


def test_env_gevsetmesi_HER_KOSUDA_beyan_edilir(tmp_path):
    """"Geçici" gevşetmenin iki gün sessizce yürürlükte kalması bu turun kapattığı kusurdur."""
    p, cagrilar = _kos(tmp_path, yas_s=5000, ortam={"MERIDIAN_TICK_BAYAT_S": "10800"})
    assert "BEYAN: eşik ENV ile" in p.stdout, f"gevşetme sessiz kaldı: {p.stdout!r}"
    assert "MERIDIAN_TICK_BAYAT_S=10800s" in p.stdout
    assert "restart" not in cagrilar, "gevşetilmiş eşiğin altında restart edildi"


def test_env_gevsetmesi_yokken_beyan_gurultusu_yok(tmp_path):
    p, _ = _kos(tmp_path, yas_s=60)
    assert "BEYAN:" not in p.stdout, "varsayılan eşikte gereksiz beyan gürültüsü"


# =================================================================================================
# 3) RESTART-PATLAMASI MUAFİYETİ — ölçülmüş karar (tepe GERÇEK çıktı)
# =================================================================================================

def test_muafiyet_sabitleri_ve_olcum_kaynakta():
    assert watchdog.ALARM_RESTART_MUAFIYET_S == 300, "muafiyet penceresi 5 dk değil"
    assert watchdog.ALARM_RESTART_JETONU == "scheduler_state_rehydrated"
    import inspect
    kaynak = inspect.getsource(watchdog)
    # Ölçüm SAYILARI kaynakta durmalı — kararın gerekçesi silinirse muafiyet keyfî bir sabite döner.
    for kanit in ("ham 10 dk tepesi          = 18", "3,1×", "11/11", "tepe = 5"):
        assert kanit in kaynak, f"ölçüm kanıtı kaynaktan silinmiş: {kanit!r}"


def test_restart_jetonu_uretimde_GERCEKTEN_yaziliyor():
    """Uydurma sinyal yasağı: muafiyetin dayandığı jetonu üreten kod VAR olmalı."""
    import inspect
    from meridian import scheduler
    assert watchdog.ALARM_RESTART_JETONU in inspect.getsource(scheduler), \
        "muafiyet, hiçbir yerde yazılmayan bir jetona dayanıyor"


def _defter_yaz(state, satirlar):
    (state / "events.jsonl").write_text("".join(json.dumps(s) + "\n" for s in satirlar))


def _an(saniye_once: float) -> str:
    return (dt.datetime.now(dt.timezone.utc)
            - dt.timedelta(seconds=saniye_once)).isoformat(timespec="seconds")


def _patlama(merkez_s: float, n: int, adim: float = 5.0) -> list[dict]:
    """`merkez_s` saniye önce başlayan n satırlık warn patlaması (adım sn arayla)."""
    return [{"ts": _an(merkez_s - i * adim), "level": "warn", "event": f"patlama_{i}"}
            for i in range(n)]


def test_restart_penceresindeki_patlama_TEPEDEN_dusulur_ve_BEYAN_edilir(sandbox_state):
    state = sandbox_state
    restart_once = 3600.0
    satirlar = ([{"ts": _an(restart_once), "level": "info",
                  "event": watchdog.ALARM_RESTART_JETONU}]
                + _patlama(restart_once - 10, 14))       # restart'tan +10s sonra başlayan 14 satır
    _defter_yaz(state, satirlar)
    r = watchdog.alarm_budget()

    assert r["tepe_ham_10dk"] == 14, r
    assert r["tepe_10dk"] == 0, f"muafiyet uygulanmadı: {r['tepe_10dk']}"
    assert r["tepe_muafiyet_uygulandi"] is True
    assert r["tepe_muaf_satir"] == 14
    assert r["tepe_restart_n"] == 1
    assert "restart-muafiyetli" in r["tepe_beyan"], r["tepe_beyan"]
    assert "ham 14" in r["tepe_beyan"], r["tepe_beyan"]
    # SESSİZ MASKELEME YASAĞI: 24 saatlik dağılım ve toplam AYNEN durur — muafiyet YALNIZ tepe
    # sayacına uygulanır, satırlar bütçeden silinmez.
    assert r["dagilim"]["low"] == 14 and r["toplam"] == 14, r["dagilim"]


def test_muafiyet_penceresinin_DISINDA_patlama_sayilir(sandbox_state):
    """Restart'tan 8 dk sonra başlayan bir fırtına GERÇEK arızadır ve tavanı delmelidir."""
    state = sandbox_state
    restart_once = 3600.0
    satirlar = ([{"ts": _an(restart_once), "level": "info",
                  "event": watchdog.ALARM_RESTART_JETONU}]
                + _patlama(restart_once - 480, 14))      # restart + 8 dk
    _defter_yaz(state, satirlar)
    r = watchdog.alarm_budget()
    assert r["tepe_10dk"] == 14, f"pencere dışı patlama muaf tutuldu: {r}"
    assert r["tepe_muafiyet_uygulandi"] is False
    assert r["asim"]["tepe"] is True, "tavan aşımı bildirilmedi"
    assert "muafiyet uygulanmadı" in r["tepe_beyan"], r["tepe_beyan"]


def test_restart_damgasi_YOKKEN_muafiyet_uygulanmaz_ve_bunu_SOYLER(sandbox_state):
    state = sandbox_state
    _defter_yaz(state, _patlama(3600.0, 14))
    r = watchdog.alarm_budget()
    assert r["tepe_10dk"] == r["tepe_ham_10dk"] == 14
    assert r["tepe_restart_n"] == 0
    assert r["tepe_muafiyet_uygulandi"] is False
    assert "damgası YOK" in r["tepe_beyan"] and "sayı HAM" in r["tepe_beyan"], r["tepe_beyan"]


def test_muafiyet_sinirlari_tam_kapali_aralik(sandbox_state):
    """Sınır davranışı: [restart, restart+300] KAPALI aralıktır; +301 sn muaf DEĞİLDİR."""
    state = sandbox_state
    r0 = 3600.0
    satirlar = [
        {"ts": _an(r0), "level": "info", "event": watchdog.ALARM_RESTART_JETONU},
        {"ts": _an(r0), "level": "warn", "event": "tam_baslangic"},        # +0 sn  → MUAF
        {"ts": _an(r0 - 300), "level": "warn", "event": "tam_sinir"},      # +300 sn → MUAF
        {"ts": _an(r0 - 301), "level": "warn", "event": "sinir_disi"},     # +301 sn → sayılır
    ]
    _defter_yaz(state, satirlar)
    r = watchdog.alarm_budget()
    assert r["tepe_muaf_satir"] == 2, r
    assert r["tepe_10dk"] == 1, r


def test_restart_jetonu_butce_sayacina_GIRMEZ(sandbox_state):
    """`info` seviyesindedir; muafiyet için okunur ama alarm sayısını şişirmez."""
    state = sandbox_state
    _defter_yaz(state, [{"ts": _an(600), "level": "info",
                         "event": watchdog.ALARM_RESTART_JETONU}] * 3)
    r = watchdog.alarm_budget()
    assert r["toplam"] == 0 and r["dagilim"]["low"] == 0
    assert r["tepe_restart_n"] == 3


def test_bozuk_damgali_restart_satiri_muafiyet_URETMEZ(sandbox_state):
    """Sıkı tarafta hata: ölçülemeyen restart damgası maskeleme yönünde çalışamaz."""
    state = sandbox_state
    satirlar = ([{"ts": "bu-bir-tarih-degil", "level": "info",
                  "event": watchdog.ALARM_RESTART_JETONU}]
                + _patlama(3600.0, 12))
    _defter_yaz(state, satirlar)
    r = watchdog.alarm_budget()
    assert r["tepe_restart_n"] == 0
    assert r["tepe_10dk"] == 12, "bozuk damgalı restart satırı muafiyet üretti"


APP_JS = REPO / "meridian" / "web" / "app.js"


def test_pano_muafiyeti_GOSTERIR_iki_render_yerinde_de():
    """YASA 6 pano-yüzü: alanın JSON'da bulunması onu OKUNMUŞ yapmaz. Muafiyet panoda görünmezse
    pano 'tepe 5, aşım yok' derken defterde 18 satır durur — sessiz maskelemenin ta kendisi.
    İKİ render yeri var (`gbAlarmSatiri` gözetim şeridi + `alarmButce` KPI satırı) ve ikisi de
    aynı bütçeyi basıyor; birinde gösterip diğerinde göstermemek, panonun kendi içinde çelişmesi
    olurdu (bu depoda 'iki kaynak, ayrışan iki yasa' diye adlandırılan baskın hata deseni)."""
    js = APP_JS.read_text()
    for fn in ("function gbAlarmSatiri(ab) {", "function alarmButce(ab) {"):
        assert fn in js, f"render yeri kaybolmuş: {fn}"
    # Rozet METNİ ve HAM sayı iki yerde de basılmalı; tam beyan `title`da taşınır.
    assert js.count("restart-muafiyetli") == 2, \
        f"rozet iki render yerinde de yok (sayım {js.count('restart-muafiyetli')})"
    assert js.count("tepe_ham_10dk") == 2, "ham tepe iki render yerinde de basılmıyor"
    assert js.count("tepe_beyan") == 2, "tam beyan `title` olarak taşınmıyor"
    # KOŞULLU olmalı: muafiyet uygulanmadığında rozet basılmaz (gürültü de bir yalandır).
    assert js.count("tepe_muafiyet_uygulandi") >= 2, "rozet koşulsuz basılıyor olabilir"
    # CSP: rozet bir `title` özniteliğidir, satır içi işleyici DEĞİL (script-src 'self').
    assert "onmouseover" not in js.split("function alarmButce")[1][:1200]


def _fn_cikar(js: str, imza: str) -> str:
    """`imza` ile başlayan fonksiyonu süslü-parantez eşleyerek söker (kaynak grep'i değil,
    KOŞTURULABİLİR gövde elde etmek için)."""
    i = js.index(imza)
    a = js.index("{", i)
    derinlik, j = 0, a
    while j < len(js):
        if js[j] == "{":
            derinlik += 1
        elif js[j] == "}":
            derinlik -= 1
            if derinlik == 0:
                return js[i:j + 1]
        j += 1
    raise AssertionError(f"fonksiyon kapanmadı: {imza}")


@pytest.mark.parametrize("imza,cagri", [
    ("function gbAlarmSatiri(ab)", "gbAlarmSatiri"),
    ("function alarmButce(ab)", "alarmButce"),
])
def test_pano_rozeti_GERCEKTEN_render_edilir(imza, cagri):
    """KAYNAK GREP'İ DEĞİL, ÇIKTI. Bir alanın dosyada geçmesi onun BASILDIĞINI kanıtlamaz —
    yanlış dala konmuş bir `${...}` da grep'i geçer. Fonksiyon node'da koşturulur ve iki hâl
    ölçülür: muafiyet varken rozet+ham sayı+title ÇIKAR, yokken hiçbiri çıkmaz (gürültü de bir
    yalandır). Tarayıcı açılmaz, yerel sunucu koşulmaz (çift-emir riski) — palette.js testinin
    kurduğu desenle aynı."""
    if shutil.which("node") is None:
        pytest.skip("node yok — pano render ölçümü koşulamadı (kaynak çivileri ayrıca duruyor)")
    js = APP_JS.read_text()
    govde = _fn_cikar(js, imza)
    muaflı = {"dagilim": {"low": 20, "high": 1}, "tepe_10dk": 5, "tepe_ham_10dk": 18,
              "tavan_10dk": 10, "duran": 0, "tavan_duran": 10, "asim": {"tepe": False},
              "asim_var": False, "tepe_muafiyet_uygulandi": True,
              "tepe_beyan": "tepe: 5 (restart-muafiyetli) — ham 18"}
    muafsız = {**muaflı, "tepe_10dk": 18, "tepe_muafiyet_uygulandi": False, "tepe_beyan": "tepe: 18"}
    betik = (
        "const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')"
        ".replace(/\"/g,'&quot;');\n"
        "const ALAN_ADI = {gozetim: 'Gözetim'};\n"
        f"{govde}\n"
        f"console.log(JSON.stringify({{muafli: {cagri}({json.dumps(muaflı)}), "
        f"muafsiz: {cagri}({json.dumps(muafsız)})}}));\n")
    p = subprocess.run(["node", "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"render düştü: {p.stderr}"
    cikti = json.loads(p.stdout)

    assert "restart-muafiyetli" in cikti["muafli"], f"rozet basılmadı: {cikti['muafli']}"
    assert "ham 18" in cikti["muafli"], "ham tepe basılmadı — muafiyetin sakladığı sayı görünmüyor"
    assert 'title="tepe: 5 (restart-muafiyetli) &mdash; ham 18"' in cikti["muafli"].replace("—", "&mdash;"), \
        f"tam beyan `title` olarak taşınmadı: {cikti['muafli']}"
    assert ">5<" in cikti["muafli"] or ">5</b>" in cikti["muafli"], "muafiyetli tepe basılmadı"

    assert "restart-muafiyetli" not in cikti["muafsiz"], \
        f"muafiyet YOKKEN rozet basıldı (gürültü): {cikti['muafsiz']}"
    assert "title=" not in cikti["muafsiz"].split("tepe")[1][:200], \
        "muafiyet yokken beyan title'ı basıldı"


def test_pano_beyani_KACISSIZ_basilir():
    """`tepe_beyan` sunucudan gelen bir dizgedir ve `title=` içine girer — `esc()`süz basılırsa
    öznitelik kaçışı olurdu. (Bu dosyadaki beyan bugün sabit metindir, ama bir sonraki turda
    jeton adı taşımaya başlarsa kural çoktan yürürlükte olmalı.)"""
    js = APP_JS.read_text()
    for parca in js.split("tepe_beyan")[1:]:
        onceki = js[:js.index("tepe_beyan")]
        assert "esc(" in parca[:40] or "esc(ab.tepe_beyan" in js, \
            "tepe_beyan kaçışsız basılıyor"
        del onceki
    assert js.count("esc(ab.tepe_beyan") == 2, "iki render yerinde de esc() yok"


def test_beyan_alani_HER_KOSUDA_dolu(sandbox_state):
    """Beyan alanı hiçbir dalda boş kalamaz — okuyucu 'muafiyet var mıydı' sorusunu daima sorabilmeli."""
    state = sandbox_state
    for satirlar in ([], _patlama(600.0, 3),
                     [{"ts": _an(600), "level": "info", "event": watchdog.ALARM_RESTART_JETONU}]):
        _defter_yaz(state, satirlar)
        r = watchdog.alarm_budget()
        assert isinstance(r["tepe_beyan"], str) and r["tepe_beyan"].startswith("tepe: "), r
