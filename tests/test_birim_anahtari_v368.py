"""test_birim_anahtari_v368.py — PANODAN SERVİSE: İSTENEN DURUM ANAHTARI (2026-09-02).

OPERATÖR VAKASI (2026-09-02 gecesi, ×2): `meridian-learn` elle `disable --now` bırakılmıştı;
dağıtım onu geri açtı. dagit tarafı TSK-092'de kapandı (başlatma listesi artık `is-enabled`dan
türetiliyor). Kalan yarısı buydu: operatörün panodan servisi İSTENEN DURUMA çekebilmesi —
**kapat = `systemctl disable --now`**, **aç = `systemctl enable --now`**.

BU ÇİVİNİN KOVALADIĞI DÖRT KUSUR SINIFI:

1) YETKİSİZ AÇIK YAZMA YÜZEYİ. Bu uç bir OKUMA ucu değil: canlı makinede servis durduruyor.
   `_auth` çağrısı davranışla ölçülür (kaynakta `_auth(request)` görmek yetmez — çağrılmayan bir
   satır da kaynakta durur) ve reddin YUTULMADIĞI ayrıca ölçülür.

2) KEYFİ BİRİM ADI. Beyaz liste MODÜL SABİTİDİR ve `meridian` çekirdek birimi ona GİRMEZ: pano
   kendi altındaki dalı kesemez. Ad süzgeci kabuk-enjeksiyonu sınıfını kapatır — `subprocess`
   zaten LİSTE argv/`shell=False` kullanıyor, süzgeç ikinci kattır.

3) VARSAYILAN SONUÇ. "`enable` çağırdım, demek ki açıktır" bir ÖLÇÜM DEĞİL bir VARSAYIMDIR.
   Yanıttaki `enabled`/`active` `is-enabled` + `is-active` ÇIKTILARINDAN gelir; komut başarılı
   olsa bile makine başka bir şey söylüyorsa yanıt MAKİNEYİ söyler. Bu çivinin en sert dalı budur
   (aşağıda `test_geri_okuma_KOMUTU_DEGIL_MAKINEYI_soyler`): saplama `enable` sonrası hâlâ
   `disabled` der ve uç bunu AYNEN taşımalıdır.

4) SESSİZ ARIZA. `systemctl` yoksa komut HİÇ koşmamıştır; zaman aşımında koşmuş OLABİLİR ama
   sonucu bilinmez; rc≠0'da koşmuş ve REDDEDİLMİŞTİR. Üçü ÜÇ AYRI HÂLDİR ve üçü de 2xx DEĞİLDİR.

ARGV ÇİVİSİ ALT SÜRECİN KENDİSİNDE (v287 emsali, `_sahte_systemctl` şerhi): saplamayı bir üst
katmana (örn. `_systemctl_kos`) koymak komut satırını ölçüm DIŞINDA bırakırdı — uç `--now`u
düşürse ya da `sudo` eklese çivi yine yeşil kalırdı (vaka 2026-08-30: 18 çivi yeşilken `--uygula`
sessizce yok sayılıyordu).
"""
from __future__ import annotations

import re
import subprocess as _sp

import pytest
from fastapi.testclient import TestClient

from meridian import api

UC = "/api/infra/birim/{ad}/istek"
LEARN = "meridian-learn.service"


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287/v361 emsali): `with TestClient(app)`
    scheduler/hermes ipliklerini ayağa kaldırır ve bu uç için tamamen gereksizdir."""
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def _onbellekleri_bosalt(monkeypatch):
    """Sıra bağımsızlığı: `/api/infra` zarfı ve CPU delta örneği süreç-içi sözlüklerdir."""
    for ad in ("_INFRA_CACHE", "_INFRA_CPU_ORNEK"):
        kutu = getattr(api, ad, None)
        if isinstance(kutu, dict):
            monkeypatch.setattr(api, ad, {})
    yield


class _Casus:
    """`subprocess.run` saplaması — argv'yi ve kwargs'ı KAYDEDER.

    `enabled`/`active`: `is-enabled`/`is-active` çağrılarının döndüreceği stdout. systemd bu iki
    alt komutta rc≠0 döndürür (disabled → 1, inactive → 3) ve HÜKÜM STDOUT'TADIR; saplama bu
    gerçeği taşır, yoksa çivi ucun rc'ye bakmasını fark etmezdi."""

    def __init__(self, *, rc: int = 0, stderr: str = "", enabled: str = "enabled",
                 active: str = "active", patlat: Exception | None = None):
        self.rc, self.stderr = rc, stderr
        self.enabled, self.active = enabled, active
        self.patlat = patlat
        self.cagrilar: list[tuple[list[str], dict]] = []

    def __call__(self, argv, *a, **kw):
        argv = list(argv)
        self.cagrilar.append((argv, dict(kw)))
        if "is-enabled" in argv:
            return _sp.CompletedProcess(argv, 0 if self.enabled == "enabled" else 1, self.enabled + "\n", "")
        if "is-active" in argv:
            return _sp.CompletedProcess(argv, 0 if self.active == "active" else 3, self.active + "\n", "")
        if "enable" in argv or "disable" in argv:
            if self.patlat is not None:
                raise self.patlat
            return _sp.CompletedProcess(argv, self.rc, "", self.stderr)
        # `show`/`list-unit-files` bu dosyanın konusu DEĞİL — birinci bacak "ölçülemedi" geçsin.
        return _sp.CompletedProcess(argv, 1, "", "")

    def yazan(self) -> list[str]:
        """DURUMA DOKUNAN tek çağrının argv'si. Birden fazlaysa bu bir kusurdur: iki kez
        `enable` çağırmak sessizce iki iş yapmaktır."""
        yazanlar = [a for a, _ in self.cagrilar if "enable" in a or "disable" in a]
        assert len(yazanlar) == 1, f"duruma dokunan çağrı sayısı 1 değil: {yazanlar}"
        return yazanlar[0]


def _kur(monkeypatch, **kw) -> _Casus:
    casus = _Casus(**kw)
    monkeypatch.setattr(_sp, "run", casus)
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)
    return casus


def _istek(cl: TestClient, ad: str = LEARN, hedef: str = "kapali", **kw):
    return cl.post(UC.format(ad=ad), json={"hedef": hedef}, **kw)


# ============================================================== A. KAYIT + YETKİ

def test_uc_rota_tablosunda_kayitli():
    yollar = {getattr(r, "path", None) for r in api.app.routes}
    assert UC in yollar, "birim anahtarı ucu kayıtlı değil — yüzey hiç doğmamış"


def test_uc_auth_cagiriyor(monkeypatch, sandbox_state):
    """Kaynak metni değil DAVRANIŞ: `_auth` casusu çağrılmazsa kırmızı."""
    _kur(monkeypatch)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _istek(_client())
    assert r.status_code == 200, r.text
    assert cagrildi == [1], "`_auth` çağrılmadı — canlı servisleri durduran yüzey yetkisiz açık"


def test_uc_auth_reddini_yutmaz(monkeypatch, sandbox_state):
    from fastapi import HTTPException

    casus = _kur(monkeypatch)

    def _red(request):
        raise HTTPException(status_code=401, detail="yetkisiz")

    monkeypatch.setattr(api, "_auth", _red)
    r = _istek(_client())
    assert r.status_code == 401, f"yetki reddi yutuldu (durum={r.status_code})"
    assert casus.cagrilar == [], "yetki reddedilmişken systemctl KOŞTU — fail-open"


def test_kimliksiz_istek_401_parola_kuruluyken(monkeypatch, sandbox_state):
    """GERÇEK yetki yolu (`_auth` casuslanmadan): parola kurulu, oturum yok → 401."""
    casus = _kur(monkeypatch)
    monkeypatch.setattr(api.auth, "password_set", lambda: True)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)
    monkeypatch.setattr(api, "DASH_TOKEN", "v368-pano-jetonu")

    cl = _client()
    assert _istek(cl).status_code == 401, "kimliksiz istek geçti"
    assert casus.cagrilar == [], "kimliksiz istek systemctl'e ulaştı"
    ok = _istek(cl, headers={"x-meridian-token": "v368-pano-jetonu"})
    assert ok.status_code == 200, ok.text


# ============================================================== B. BEYAZ LİSTE + AD SÜZGECİ

def test_beyaz_liste_MODUL_SABITI_ve_cekirdek_birim_DISINDA():
    beyaz = api.BIRIM_ANAHTAR_BEYAZ
    assert isinstance(beyaz, tuple) and beyaz, "beyaz liste modül sabiti değil"
    assert "meridian" not in beyaz and "meridian.service" not in beyaz, (
        "çekirdek birim beyaz listede — pano kendi altındaki dalı keserdi")
    assert set(beyaz) == {"meridian-learn", "meridian-barsarchive"}, beyaz


def test_beyaz_liste_disi_ad_403_ve_gerekce_LISTEYI_TASIR(monkeypatch, sandbox_state):
    """403 gövdesi keşfedilebilir olmalı: hangi birimlerin anahtarlanabildiğini SÖYLER."""
    casus = _kur(monkeypatch)
    r = _istek(_client(), ad="meridian.service")
    assert r.status_code == 403, r.text
    detay = r.json().get("detail") or ""
    for beyaz in api.BIRIM_ANAHTAR_BEYAZ:
        assert beyaz in detay, f"403 gerekçesi beyaz listeyi taşımıyor: {detay!r}"
    assert casus.cagrilar == [], "liste dışı ad systemctl'e ulaştı"


def test_beyaz_liste_KOMSU_BIRIM_TURUNU_kabul_etmez(monkeypatch, sandbox_state):
    """`.service` ekini soyup karşılaştıran bir uygulama `meridian-learn.timer`ı da geçirirdi —
    ve o BAŞKA bir birimdir. Ek soyulmaz, iki biçim de AÇIKÇA listelenir."""
    casus = _kur(monkeypatch)
    r = _istek(_client(), ad="meridian-learn.timer")
    assert r.status_code == 403, r.text
    assert casus.cagrilar == []


@pytest.mark.parametrize("ad", ["meridian-learn;rm", "meridian-learn%20", "MERIDIAN-LEARN",
                               "meridian-learn$(id)", "meridian-learn|sh",
                               # ARGV-BAYRAK SINIFI (görev incelemesi K4): `-` ile başlayan bir ad
                               # `systemctl`e birim değil BAYRAK olarak gider. Beyaz liste bunları
                               # zaten 403 ile durdururdu — ama o BAŞKA bir korumadır ve burada
                               # ölçülen şey SÜZGECİN KENDİSİdir (mutasyon-1 dersinin devamı).
                               # TEK BAŞINA "." BU LİSTEDE YOK VE SEBEBİ ÖLÇÜLDÜ: yol parçası
                               # olarak normalleştiriliyor ve isteği 404 yapıyor, yani UCA HİÇ
                               # ULAŞMIYOR. Listede tutmak, süzgeci ölçtüğünü sanan ama aslında
                               # yönlendiriciyi ölçen bir çivi olurdu.
                               "-h", "--version", "-", ".meridian-learn"])
def test_ad_suzgeci_kabuk_sinifini_400_ile_keser(ad, monkeypatch, sandbox_state):
    """`[a-z0-9@.-]+` DIŞI her ad reddedilir — ve systemctl'e HİÇ ulaşmaz.

    KOD 400 OLARAK ÇİVİLENDİ, "4xx" OLARAK DEĞİL — VE BU BİR MUTASYON ÖLÇÜMÜNÜN SONUCU: süzgeci
    kapatınca çivi YİNE YEŞİL kaldı, çünkü beyaz liste aynı adları 403 ile zaten reddediyordu.
    "4xx" diyen bir çivi iki AYRI korumayı tek kılığa sokuyor ve ikincisi düştüğünde ötmüyordu.
    400 (biçim) ile 403 (yetki) ayrı tutulunca süzgecin kendisi ölçülür hâle geldi."""
    casus = _kur(monkeypatch)
    r = _client().post(UC.format(ad=ad), json={"hedef": "kapali"})
    assert r.status_code == 400, (
        f"{ad!r} biçim süzgecine takılmadı ({r.status_code}) — 403 aldıysa adı BEYAZ LİSTE "
        f"reddetti, süzgeç değil: {r.text}")
    assert casus.cagrilar == [], f"{ad!r} systemctl'e ulaştı"


# ============================================================== C. KOMUT: ARGV BİREBİR

@pytest.mark.parametrize("hedef,eylem", [("acik", "enable"), ("kapali", "disable")])
def test_argv_birebir(hedef, eylem, monkeypatch, sandbox_state):
    casus = _kur(monkeypatch)
    r = _istek(_client(), hedef=hedef)
    assert r.status_code == 200, r.text
    argv = casus.yazan()
    assert argv[0].endswith("systemctl"), f"argv[0] systemctl değil: {argv[0]!r}"
    assert argv[1:] == [eylem, "--now", LEARN], f"komut satırı ayrıştı: {argv}"


def test_sudo_YOK_ve_kabuk_YOK(monkeypatch, sandbox_state):
    """`meridian.service` `NoNewPrivileges` taşır: `sudo` sessizce düşerdi. Yetki polkit/DBus
    kural dosyasındadır ve o dosya BU turun işi değildir."""
    casus = _kur(monkeypatch)
    assert _istek(_client()).status_code == 200
    for argv, kw in casus.cagrilar:
        assert "sudo" not in argv, f"argv sudo taşıyor: {argv}"
        assert isinstance(argv, list), "argv liste değil — kabuk yorumu yolu açık"
        assert kw.get("shell") in (None, False), f"shell=True: {kw}"
        assert kw.get("timeout"), f"zaman aşımı yok — uç asılabilir: {kw}"


@pytest.mark.parametrize("hedef", ["", "acık", "on", "true", "AÇIK", None, 1])
def test_taninmayan_hedef_400_ve_komut_kosmaz(hedef, monkeypatch, sandbox_state):
    casus = _kur(monkeypatch)
    r = _client().post(UC.format(ad=LEARN), json={"hedef": hedef})
    assert r.status_code == 400, f"{hedef!r} 400 almadı: {r.status_code}"
    assert casus.cagrilar == [], f"{hedef!r} systemctl'e ulaştı"


def test_govdesiz_istek_400(monkeypatch, sandbox_state):
    casus = _kur(monkeypatch)
    r = _client().post(UC.format(ad=LEARN))
    assert r.status_code == 400, r.text
    assert casus.cagrilar == []


# ============================================================== D. GERİ OKUMA = ÖLÇÜM

def test_geri_okuma_yanitta(monkeypatch, sandbox_state):
    casus = _kur(monkeypatch, enabled="disabled", active="inactive")
    g = _istek(_client()).json()
    assert g["birim"] == LEARN and g["hedef"] == "kapali"
    assert g["enabled"] == "disabled" and g["active"] == "inactive"
    assert g["komut_rc"] == 0
    okunan = [a for a, _ in casus.cagrilar if "is-enabled" in a or "is-active" in a]
    assert len(okunan) == 2, f"geri okuma yapılmadı ya da tekrarlandı: {okunan}"
    for argv in okunan:
        assert argv[-1] == LEARN, f"geri okuma başka birime sordu: {argv}"


def test_geri_okuma_KOMUTU_DEGIL_MAKINEYI_soyler(monkeypatch, sandbox_state):
    """EN SERT DAL: `enable` rc=0 döndü ama makine hâlâ `disabled`/`inactive` diyor (mask'lı
    birim, preset çakışması, `--now` başlatmayı beceremedi). Yanıt HEDEFİ değil ÖLÇÜMÜ taşır."""
    _kur(monkeypatch, enabled="disabled", active="inactive")
    g = _istek(_client(), hedef="acik").json()
    assert g["hedef"] == "acik", "istek hedefi kayboldu"
    assert (g["enabled"], g["active"]) == ("disabled", "inactive"), (
        f"uç komuttan hüküm kurdu, makineden değil: {g}")


def test_geri_okuma_olculemezse_None_ve_gerekce(monkeypatch, sandbox_state):
    """`is-enabled` boş çıktı verirse "kapalı" DEĞİL "ölçülemedi" — uydurma yasağı."""
    _kur(monkeypatch, enabled="", active="")
    g = _istek(_client()).json()
    assert g["enabled"] is None and g["active"] is None, g
    for alan in ("enabled_neden", "active_neden"):
        assert isinstance(g.get(alan), str) and len(g[alan].strip()) >= 10, f"{alan}: {g.get(alan)!r}"


def test_komut_metni_operatorun_kosacagi_bicimde(monkeypatch, sandbox_state):
    """Operatör sonucu KENDİ ELİYLE doğrulayabilmeli ("pano öyle diyor" ile "makineye sordum"
    arasındaki fark) — `beklenmedik_olcum.komut` emsali."""
    _kur(monkeypatch)
    g = _istek(_client()).json()
    assert g["komut"] == f"systemctl disable --now {LEARN}", g.get("komut")


# ============================================================== E. ARIZA HÂLLERİ AYRI

def test_rc_sifir_disi_502_ve_stderr_kirpilir(monkeypatch, sandbox_state):
    uzun = "polkit reddetti: " + "x" * 500
    _kur(monkeypatch, rc=1, stderr=uzun)
    r = _istek(_client())
    assert r.status_code == 502, r.text
    detay = r.json().get("detail") or ""
    assert "polkit reddetti" in detay, f"stderr taşınmadı: {detay!r}"
    assert len(detay.encode("utf-8")) <= 400, f"gövde kırpılmadı ({len(detay)} karakter)"
    assert "x" * 300 not in detay, "stderr 200 baytın ötesine geçti"


def test_systemctl_yoksa_KOMUT_KOSMADI_hali_ayri(monkeypatch, sandbox_state):
    """`systemctl` PATH'te yoksa komut HİÇ koşmamıştır — bu, koşup reddedilmekten (502) BAŞKA
    bir gerçektir ve 2xx hiç değildir."""
    casus = _Casus()
    monkeypatch.setattr(_sp, "run", casus)
    monkeypatch.setattr(api.shutil, "which", lambda ad: None)
    r = _istek(_client())
    assert r.status_code == 503, f"systemctl yokken {r.status_code} döndü"
    assert casus.cagrilar == []
    assert "systemctl" in (r.json().get("detail") or "")


def test_zaman_asimi_502_ve_SONUC_BILINMIYOR_der(monkeypatch, sandbox_state):
    """Zaman aşımı "uygulanmadı" DEMEK DEĞİLDİR: komut başlamıştı. Gerekçe bunu SÖYLEMELİ."""
    _kur(monkeypatch, patlat=_sp.TimeoutExpired("systemctl", 15))
    r = _istek(_client())
    assert r.status_code == 502, r.text
    # `.lower()` KULLANILMIYOR VE BU BİR ÖLÇÜM SONUCU: "BİLİNMİYOR".lower() Python'da bileşik bir
    # `i̇` (i + birleşen nokta) üretir ve "bilinmiyor" ile EŞLEŞMEZ — çivi ilk koşumda tam bu
    # yüzden kırmızıydı, uç doğru cümleyi yazdığı hâlde. Kıyas büyük/küçük harfe DUYARLI.
    detay = r.json().get("detail") or ""
    assert "BİLİNMİYOR" in detay, f"belirsizlik beyan edilmedi: {detay!r}"


# ============================================================== F. OLAY + ÖNBELLEK

def _olaylar(sandbox_state) -> list[dict]:
    """Kum havuzundaki olay defteri (`obs._emit` → `store.append_jsonl`). Dosya adı ucun
    değil OBS'un sözleşmesidir; buradan okumak, olayın GERÇEKTEN deftere düştüğünü ölçer —
    `obs.warn`u saplayıp "çağrıldı mı" diye sormak, aynalamanın düştüğü hâli kaçırırdı."""
    import json
    yol = sandbox_state / "events.jsonl"
    if not yol.exists():
        return []
    out = []
    for satir in yol.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(satir))
        except ValueError:  # sessiz-yutma: defterde JSON olmayan satır olabilir, olay araması onu atlar
            continue
    return out


def test_obs_olayi_yazildi(monkeypatch, sandbox_state):
    _kur(monkeypatch)
    assert _istek(_client(), hedef="acik").status_code == 200
    olay = [o for o in _olaylar(sandbox_state) if o.get("event") == "birim_istek"]
    assert len(olay) == 1, f"`birim_istek` olayı yazılmadı ya da tekrarlandı: {olay}"
    o = olay[0]
    assert o.get("birim") == LEARN and o.get("hedef") == "acik" and o.get("rc") == 0, o
    # KİM SORDU (K3, `password_set`/`session_drop` emsali): canlı bir servisi durduran istekte
    # "kim" defterde durmalı. Bugün tek bir loopback adresi görünür — değeri, o beklentinin
    # BOZULDUĞU gün ortaya çıkar.
    assert isinstance(o.get("ip"), str) and o["ip"].strip(), f"olayda çağıran adresi yok: {o}"


def test_obs_olayi_ARIZADA_da_yazilir(monkeypatch, sandbox_state):
    """Sessiz arıza en pahalı hâl: reddedilen bir istek defterde HİÇ görünmezse operatör
    "tıkladım, olmadı" der ve kanıt kalmaz."""
    _kur(monkeypatch, rc=1, stderr="reddedildi")
    assert _istek(_client()).status_code == 502
    olay = [o for o in _olaylar(sandbox_state) if o.get("event") == "birim_istek"]
    assert len(olay) == 1 and olay[0].get("rc") == 1, olay


def test_basarili_istek_infra_onbellegini_bosaltir(monkeypatch, sandbox_state):
    """8 sn'lik zarf boşaltılmazsa pano anahtarı çevirdikten sonra DEĞİŞİKLİK ÖNCESİ satırı geri
    okur — "hiçbir şey olmadı" hissi (`_diag_onbellek_bosalt` emsali)."""
    _kur(monkeypatch)
    api._INFRA_CACHE["bayat"] = ({"bilesenler": None}, 0.0)
    assert _istek(_client()).status_code == 200
    assert api._INFRA_CACHE == {}, "istek sonrası altyapı zarfı bayat kaldı"


# ============================================================== G. /api/infra ALANI

def test_infra_satirlari_anahtar_var_tasir(monkeypatch, sandbox_state):
    """UI hangi satıra anahtar çizeceğini UÇTAN öğrenir — liste İKİNCİ kez panoda sabitlenmez."""
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {
        "LoadState": "loaded", "ActiveState": "active", "SubState": "running", "Type": "simple"})
    satirlar = _client().get("/api/infra?taze=1").json()["bilesenler"]
    assert satirlar, "bileşen satırı yok — alan çivisi hüküm kuramaz"
    esleme = {s["ad"]: s["anahtar_var"] for s in satirlar}
    assert esleme.get(LEARN) is True, f"beyaz listedeki birimde anahtar yok: {esleme.get(LEARN)!r}"
    assert esleme.get("meridian-barsarchive.service") is True
    assert esleme.get("meridian.service") is False, "çekirdek birimde anahtar çizilir görünüyor"
    assert all(isinstance(v, bool) for v in esleme.values()), f"alan üç değerli olmuş: {esleme}"


def test_infra_satirlari_ISTENEN_DURUMU_tasir(monkeypatch, sandbox_state):
    """Anahtarın durumu `etkin && active`ten türer; `etkin` yarısı `UnitFileState`tir.

    ALAN SYSTEMD'DEN ZATEN ÇEKİLİYORDU ama hiçbir yere yazılmıyordu (okuyucusuz ölçüm). Onsuz
    pano yalnız `ActiveState` görürdü ve operatörün vakası TAM O AYRIMDA doğdu: birim `disabled`
    bırakılmıştı, dağıtım `enabled` yaptı — ikisi de `active` görünürken."""
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {
        "LoadState": "loaded", "ActiveState": "active", "SubState": "running",
        "UnitFileState": "disabled", "Type": "simple"})
    satirlar = _client().get("/api/infra?taze=1").json()["bilesenler"]
    canli = [s for s in satirlar if not s["sablon"]]
    assert canli, "sorgulanan birim yok"
    for s in canli:
        assert s["etkin_durum"] == "disabled", f"istenen durum taşınmıyor: {s['ad']} → {s}"
        assert s["durum"] == "active", "şu anki durum ile istenen durum karıştı"


def test_istenen_durum_olculemezse_KAPALI_SAYILMAZ(monkeypatch, sandbox_state):
    """`UnitFileState` gelmezse `disabled` BASILMAZ: anahtar kapalı görünür ve operatör
    kapatılmamış bir birimi kapalı sanardı (uydurma yasağı)."""
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {
        "LoadState": "loaded", "ActiveState": "active"})
    satirlar = _client().get("/api/infra?taze=1").json()["bilesenler"]
    for s in [x for x in satirlar if not x["sablon"]]:
        assert s["etkin_durum"] is None, f"ölçülmeyen istenen durum sayıya döndü: {s['etkin_durum']!r}"
        assert isinstance(s["etkin_durum_neden"], str) and len(s["etkin_durum_neden"].strip()) >= 10


def test_anahtar_var_TEK_KAYNAKTAN_turer(monkeypatch, sandbox_state):
    """Beyaz liste tek kaynaktır: sabiti daraltmak ALANI da daraltmalı. İki kopya sessizce
    ayrışırsa pano yetkisi olmayan bir satıra anahtar çizer ve tıklama 403 alır."""
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {"LoadState": "loaded"})
    monkeypatch.setattr(api, "BIRIM_ANAHTAR_BEYAZ", ("meridian-barsarchive",))
    satirlar = _client().get("/api/infra?taze=1").json()["bilesenler"]
    esleme = {s["ad"]: s["anahtar_var"] for s in satirlar}
    assert esleme.get(LEARN) is False, "sabit daraldı ama alan eski listeyi taşıyor (kopya)"
    assert esleme.get("meridian-barsarchive.service") is True


# ==================================================================== H. PANO TARAFI
#
# ÇİVİ YEŞİLİ KANIT DEĞİLDİR — VE BU YÜZEYDE İKİ AYRI ŞEY ÖLÇÜLMELİ (v354'ün ölçtüğü ders):
# saf okuyucu DOĞRU hüküm kurabilir ve o hüküm EKRANA HİÇ ÇIKMAYABİLİR. Bu dosyada anahtar
# `BilesenGovdesi`nin İÇİNDE duruyor ve o gövde üç yerde erken çıkıyor — o yüzden aşağıda
# okuyucular node'da GERÇEKTEN koşturulur VE kart `react-dom/server` ile GERÇEKTEN çizilir.
#
# Alt-dize tuzağı: bir alan adının kaynakta geçmesi OKUNDUĞUNU kanıtlamaz.

import shutil                                                                # noqa: E402
import subprocess                                                            # noqa: E402
from pathlib import Path                                                     # noqa: E402

from tests.conftest import (                                                 # noqa: E402
    ESBUILD_YOLU,
    tsx_bileseni_cizdir,
    tsx_islev_cagir,
    tsx_saf_islevleri_cevir,
    tsx_yorumlari_soy,
)

KOK = Path(__file__).resolve().parent.parent
SISTEM = KOK / "ui" / "src" / "pano" / "yuzeyler" / "sistem"
ANAHTAR_TSX = SISTEM / "BirimAnahtari.tsx"

#: Panoya eklenen SAF okuyucular — hepsi JSX'siz ve kancasız, davranışları ölçülebilir.
OKUYUCULAR = ("anahtarOku", "onayMetni", "anahtarsizNeden", "sonucGecerliMi")

#: `subprocess.run` bu dosyada süreç genelinde saplanıyor (komut satırı sözleşmenin parçası).
#: Ölçüm aracının KENDİ alt süreçleri o saplamaya düşerse çivi, ölçtüğü şey yüzünden DEĞİL
#: kendi hattı yüzünden kırmızıya dönerdi (v354 aynı tuzağa ilk koşumda düştü).
_GERCEK_RUN = subprocess.run

_arac_yok = shutil.which("node") is None or not ESBUILD_YOLU.exists()
arac_gerek = pytest.mark.skipif(_arac_yok, reason="node/esbuild yok — pano davranışı koşturulamaz")
ui_gerek = pytest.mark.skipif(not ANAHTAR_TSX.exists(), reason="ui/ bu ağaçta yok")

_CEVRILMIS: str | None = None


def _cevir() -> str:
    global _CEVRILMIS
    if _CEVRILMIS is None:
        kaynak = tsx_yorumlari_soy(ANAHTAR_TSX.read_text(encoding="utf-8"))
        _CEVRILMIS = tsx_saf_islevleri_cevir(kaynak, OKUYUCULAR, kosucu=_GERCEK_RUN)
    return _CEVRILMIS


def _cagir(ad: str, *argumanlar):
    return tsx_islev_cagir(_cevir(), ad, *argumanlar, kosucu=_GERCEK_RUN)


def _satir(**ek) -> dict:
    """Beyaz listedeki bir bileşen satırının ölçülmüş şekli (uçtan gelen alan adlarıyla)."""
    return {"ad": LEARN, "sablon": False, "tur": "service", "anahtar_var": True,
            "etkin_durum": "enabled", "durum": "active", **ek}


@arac_gerek
@ui_gerek
def test_olcum_hatti_GERCEKTEN_KOSUYOR():
    """Pozitif kontrol: sıfır bulgunun anlamı olması için hattın koştuğu kanıtlanmalı. Sökme +
    esbuild + node zinciri sessizce boş dönseydi aşağıdaki her hüküm ANLAMSIZ YEŞİL olurdu."""
    js = _cevir()
    for ad in OKUYUCULAR:
        assert f"function {ad}" in js, f"`{ad}` çeviriye girmemiş"
    assert _cagir("anahtarOku", _satir(), None)["hal"] == "acik"


@arac_gerek
@ui_gerek
@pytest.mark.parametrize("etkin,durum,beklenen,cizili", [
    ("enabled", "active", "acik", True),
    ("enabled-runtime", "active", "acik", True),
    ("disabled", "inactive", "kapali", False),
    ("disabled", "failed", "kapali", False),
    # AYRIŞMA: ikisi "kapalı" diye çizilseydi iki farklı gerçek tek kılığa girerdi.
    ("enabled", "inactive", "karisik", True),
    ("disabled", "active", "karisik", False),
    # `static`/`masked` açılabilir birim tarif etmez — "açık" sayılmaz.
    ("static", "active", "karisik", False),
    ("masked", "inactive", "kapali", False),
])
def test_anahtar_hali_iki_olcumden_turer(etkin, durum, beklenen, cizili):
    oku = _cagir("anahtarOku", _satir(etkin_durum=etkin, durum=durum), None)
    assert oku["hal"] == beklenen, f"{etkin}/{durum} → {oku}"
    assert oku["cizili"] is cizili, f"anahtar yanlış konumda: {oku}"


@arac_gerek
@ui_gerek
@pytest.mark.parametrize("eksik", ["etkin_durum", "durum"])
def test_olculmeyen_yari_KAPALI_SAYILMAZ(eksik):
    """Yarım ölçümle "kapalı" çizmek, kapatılmamış bir birimi kapalı göstermekti."""
    s = _satir(**{eksik: None, f"{eksik}_neden": "bu istekte sorulamadı"})
    oku = _cagir("anahtarOku", s, None)
    assert oku["hal"] == "bilinmiyor", f"{eksik} yokken hüküm kuruldu: {oku}"
    assert "sorulamadı" in (oku["teknik"] or ""), f"gerekçe taşınmadı: {oku}"


@arac_gerek
@ui_gerek
def test_SUNUCU_CEVABI_bayat_satiri_ezer():
    """İYİMSER GÜNCELLEME YOK ama BAYAT SATIR DA OKUNMAZ: uç 8 sn'ye kadar bayat olabilir ve
    tıklamadan hemen sonra eski değeri geri okumak anahtarı yerine sektirirdi. Kazanan, ucun
    komuttan DEĞİL makineden geri okuduğu cevaptır — o da bir ölçümdür."""
    bayat = _satir(etkin_durum="enabled", durum="active")
    sonuc = {"hedef": "kapali", "enabled": "disabled", "active": "inactive"}
    oku = _cagir("anahtarOku", bayat, sonuc)
    assert (oku["hal"], oku["cizili"], oku["kaynak"]) == ("kapali", False, "sunucu"), oku


@arac_gerek
@ui_gerek
def test_sunucu_cevabi_HEDEFTEN_DEGIL_OLCUMDEN_okunur():
    """EN SERT DAL, ekran tarafı: istek "aç" idi, uç `enable`i başarıyla koştu, ama makine hâlâ
    kapalı diyor. Anahtar HEDEFİ değil ÖLÇÜMÜ göstermeli — yoksa pano kapalı bir servisi açık
    gösterir ve bu, bu yüzeyin söyleyebileceği en pahalı yalandır."""
    sonuc = {"hedef": "acik", "enabled": "disabled", "active": "inactive"}
    oku = _cagir("anahtarOku", _satir(), sonuc)
    assert oku["hal"] == "kapali" and oku["cizili"] is False, f"hedef sonuç sanıldı: {oku}"


@arac_gerek
@ui_gerek
def test_onay_metni_ISTENEN_DURUM_dilini_kullanir():
    """Onay cümlesi yaptığı işi EKSİK anlatırsa onay bir onay değildir: operatörün vakası tam
    olarak durdurmanın kalıcı OLMAMASIYDI, o yüzden dağıtım etkisi cümlede DURMALI."""
    kapat = _cagir("onayMetni", LEARN, "kapali")
    assert LEARN in kapat["baslik"] and "kapatılsın mı" in kapat["baslik"], kapat
    assert "Dağıtımlar da onu kapalı" in kapat["govde"], kapat
    assert "açılışta" in kapat["govde"], "kalıcılık anlatılmıyor — 'durdur' ile karışır"
    ac = _cagir("onayMetni", LEARN, "acik")
    assert "açılsın mı" in ac["baslik"] and "açılışta" in ac["govde"], ac


@arac_gerek
@ui_gerek
def test_anahtarsiz_satir_KISA_NEDEN_tasir():
    """Boş hücre "burada bir şey yok" diye okunur; oysa söylenecek şey var ve kısa."""
    cekirdek = _cagir("anahtarsizNeden", {"ad": "meridian.service", "tur": "service"})
    assert "çekirdek" in cekirdek, cekirdek
    assert "anahtar yok" in _cagir("anahtarsizNeden", {"ad": "meridian-backup.timer", "tur": "timer"})


# --- MONTAJ: KART GERÇEKTEN ÇİZİLİYOR MU ---------------------------------------------------
# Saf işlev çağrısı bir MONTAJ kanıtı DEĞİLDİR (v354'te ölçüldü: 18 çivi yeşilken blok ekrana
# hiç düşmüyordu). Anahtar `BilesenGovdesi`nin içinde ve o gövde üç yerde erken çıkıyor.

_GIRIS = """
import { renderToStaticMarkup } from "react-dom/server";
import { Bilesenler } from "./Bilesenler";
const govde = JSON.parse(process.env.GOVDE ?? "{}");
console.log(renderToStaticMarkup(
  <Bilesenler durum={{ veri: govde, hata: null, oturumDustu: false, tazele: () => {} }} />));
"""


def _ciz(bilesenler: list[dict]) -> str:
    import json as _json
    govde = {"bilesenler": bilesenler, "bilesen_kaynagi": {"dizin": "deploy/", "birim_n": len(bilesenler)}}
    html = tsx_bileseni_cizdir(_GIRIS, SISTEM, {"GOVDE": _json.dumps(govde, ensure_ascii=False)},
                               kosucu=_GERCEK_RUN)
    assert "Meridian bileşenleri" in html, (
        f"kart hiç çizilmedi — aşağıdaki 'var/yok' hükümleri anlamsız olurdu: {html[:200]!r}")
    return html


@arac_gerek
@ui_gerek
def test_anahtar_EKRANA_GERCEKTEN_DUSUYOR():
    html = _ciz([_satir()])
    assert 'data-slot="switch"' in html, (
        "anahtar çizilmedi — saf okuyucu doğru hüküm kursa da ekranda görünmüyor (montaj kusuru)")
    assert "anahtar yok" not in html


@arac_gerek
@ui_gerek
def test_liste_disi_satirda_ANAHTAR_CIZILMEZ_ama_neden_yazilir():
    html = _ciz([{"ad": "meridian.service", "sablon": False, "tur": "service",
                  "anahtar_var": False, "etkin_durum": "enabled", "durum": "active"}])
    assert 'data-slot="switch"' not in html, "liste dışı satıra anahtar çizildi"
    assert "çekirdek birim" in html, "anahtarsızlığın nedeni ekranda yok — boş hücre kalırdı"


@arac_gerek
@ui_gerek
def test_ALAN_HIC_GELMEZSE_izin_VARSAYILMAZ():
    """Eski gövde (alan yok) ile açık izin AYNI ŞEY DEĞİL: varsaymak, olmayan bir yetkiyi
    ekranda vaat etmek olurdu ve tıklama reddedilirdi."""
    html = _ciz([{"ad": LEARN, "sablon": False, "tur": "service",
                  "etkin_durum": "enabled", "durum": "active"}])
    assert 'data-slot="switch"' not in html, "anahtar hakkı bildirilmeden anahtar çizildi"


# ==================================================================== I. OLAY DÖNGÜSÜ
#
# Bu uç `async` olmak ZORUNDA (gövdeyi `await request.json()` ile okuyor) ve `async` bir uçta
# yapılan ENGELLEYİCİ çağrı olay döngüsünü tutar. `enable --now` birimi BAŞLATIR ve saniyeler
# sürebilir; o süre boyunca panonun TAMAMI donardı — yani bir servisi açma isteği, acil müdahale
# yüzeyini (HALT) kapatırdı. Ölçüm KAYNAK METNİ DEĞİL DAVRANIŞ: alt süreç, uç gövdesini koşturan
# iplikten BAŞKA bir iplikte çalışmalı.

def test_alt_surec_OLAY_DONGUSUNU_TUTMAZ(monkeypatch, sandbox_state):
    import threading

    casus = _kur(monkeypatch)
    iplikler: dict[str, int] = {}
    asil_auth = api._auth
    monkeypatch.setattr(api, "_auth", lambda request: (
        iplikler.__setitem__("uc", threading.get_ident()), asil_auth(request))[1])

    asil_kos = api._systemctl_kos

    def _izli(*a, **kw):
        iplikler.setdefault("komut", threading.get_ident())
        return asil_kos(*a, **kw)

    monkeypatch.setattr(api, "_systemctl_kos", _izli)
    assert _istek(_client()).status_code == 200
    assert "uc" in iplikler and "komut" in iplikler, f"ölçüm hattı koşmadı: {iplikler}"
    assert iplikler["komut"] != iplikler["uc"], (
        "alt süreç, ucun kendi ipliğinde koştu — engelleyici çağrı olay döngüsünü tutuyor ve "
        "komut sürerken panonun tamamı (nabız, acil durdurma yüzeyi) donar")
    assert casus.cagrilar, "alt süreç hiç çağrılmadı — çivi boş ölçtü"


# ==================================================================== J. CEVABIN ÖMRÜ (K1)
#
# GÖREV İNCELEMESİNİN BULDUĞU GERÇEK KUSUR: sunucu cevabı bir kez saklandığında ÖMÜR BOYU
# kazanıyordu. İlk tıklamadan sonra anahtar o tek geri-okumaya çivilenirdi; birim sonradan DÜŞSE
# (`active` → `failed`) ya da başka bir yoldan açılıp kapansa pano hâlâ eski cevabı gösterirdi —
# ve `karisik` tespiti, yani BU GÖREVİ DOĞURAN operatör vakasının ta kendisi, sessizce ölürdü.

@arac_gerek
@ui_gerek
@pytest.mark.parametrize("sonucTs,veriTs,beklenen", [
    (None, 1_000, False),        # hiç istek yapılmadı → cevap yok
    (1_000, None, True),         # satır hiç okunamadı → cevap eldeki TEK ölçüm
    (2_000, 1_000, True),        # satır cevaptan ESKİ → cevap hâlâ daha taze
    (2_000, 2_000, True),        # aynı an → cevap korunur (satır cevabı henüz geçmedi)
    (2_000, 2_001, False),       # satır cevaptan YENİ → öncelik satıra geçer
])
def test_cevabin_onceligi_YASLA_dusuyor(sonucTs, veriTs, beklenen):
    assert _cagir("sonucGecerliMi", sonucTs, veriTs) is beklenen


@arac_gerek
@ui_gerek
def test_TAZE_SATIR_GELINCE_sunucu_cevabinin_onceligi_DUSER():
    """K1'in davranış çivisi, uçtan uca: cevap "açık" diyordu; sonra birim DÜŞTÜ ve taze satır
    bunu bildirdi. Cevap hâlâ kazansaydı pano düşmüş bir servisi açık gösterirdi."""
    taze_satir = _satir(etkin_durum="enabled", durum="failed")
    cevap = {"hedef": "acik", "enabled": "enabled", "active": "active"}

    # (a) Cevap satırdan TAZEYKEN kazanır — iyimserlik değil, YAŞ.
    assert _cagir("sonucGecerliMi", 2_000, 1_000) is True
    assert _cagir("anahtarOku", taze_satir, cevap)["hal"] == "acik"

    # (b) Satır cevabı GEÇTİĞİNDE öncelik satıra döner ve ayrışma yeniden GÖRÜLÜR.
    assert _cagir("sonucGecerliMi", 2_000, 3_000) is False
    oku = _cagir("anahtarOku", taze_satir, None)
    assert oku["hal"] == "karisik", (
        f"taze satır kazanmadı — cevap ömür boyu çivili kalırsa düşen birim fark edilmez: {oku}")
    assert oku["kaynak"] == "satir"


@arac_gerek
@ui_gerek
def test_anahtar_TAZE_SATIRI_cizer_MONTAJDA():
    """Saf okuyucu doğru olsa da bileşen damgayı bağlamamış olabilir (montaj kusuru). Kart
    GERÇEKTEN çizilir: hiç istek yapılmamışken anahtar SATIRDAN çizilmeli."""
    html = _ciz([_satir(etkin_durum="disabled", durum="inactive")])
    assert 'data-slot="switch"' in html
    assert 'data-checked' not in html or 'data-unchecked' in html, (
        "kapalı satırda anahtar açık çizildi")


@ui_gerek
def test_bilesen_OKUMA_DAMGASINI_bagliyor():
    """MONTAJIN KAYNAK TARAFI: damga bileşene GEÇİRİLMEZSE cevap ömür boyu geçerli kalır ve
    yukarıdaki saf çiviler bunu göremez (onlar damgayı KENDİLERİ veriyor). Burada ölçülen şey
    kablonun BAĞLI olduğudur — `Bilesenler` damgayı gövdeye, gövde de anahtara veriyor mu."""
    from tests.conftest import tsx_yorumlari_soy as _soy
    bil = _soy((SISTEM / "Bilesenler.tsx").read_text(encoding="utf-8"))
    assert "durum.zaman" in bil, (
        "`Bilesenler` okuma damgasını hiç okumuyor — anahtar cevabın yaşını ölçemez")
    assert "veriTs={veriTs}" in bil, "damga satır bileşenine geçirilmiyor"
    anahtar = _soy(ANAHTAR_TSX.read_text(encoding="utf-8"))
    assert "sonucGecerliMi(sonuc.ts, veriTs)" in anahtar, (
        "anahtar damgayı hükme bağlamıyor — cevap ömür boyu öncelikli kalır")


# ==================================================================== K. AYRIŞMA: POLKIT KURALI
#
# TSK-100. Beyaz liste artık İKİ YERDE yaşıyor: `api.py::BIRIM_ANAHTAR_BEYAZ` ve polkit kural
# dosyası. Türetme kurulamaz (iki dil, iki makine, kural dosyası dağıtımla iniyor) — o yüzden
# tek-kaynak yasasının ikinci yolu işletiliyor: KOPYA KAÇINILMAZSA AYRIŞMA ÇİVİSİ.
#
# AYRIŞMANIN BEDELİ SESSİZ DEĞİL AMA GEÇ: listeyi `api.py`de genişletip kurala yazmayan biri,
# hatayı ancak İLK CANLI DENEMEDE 502 + polkit stderr olarak görür. Bu çivi onu bugün, yerelde
# ve saniyeler içinde gösterir.

KURAL_DOSYASI = KOK / "deploy" / "oracle-a1" / "51-meridian-birim-anahtari.rules"


def test_polkit_kurali_VAR():
    """DOSYANIN VARLIĞI DA SÖZLEŞMEDİR — bu yüzden `skip` DEĞİL `fail`. Kural inmezse uç
    çalışmaz; "dosya yok, testi atla" demek, kurulumun eksikliğini ölçüm dışına çıkarmaktı."""
    assert KURAL_DOSYASI.exists(), (
        f"polkit kural dosyası yok: {KURAL_DOSYASI.relative_to(KOK)} — uç yetkisiz kalır ve "
        f"her istek 502 + polkit hatası döner")


def test_polkit_kurali_BEYAZ_LISTEYLE_AYRISMAZ():
    """Kuraldaki `unit == "<ad>"` kümesi ile `BIRIM_ANAHTAR_BEYAZ` BİREBİR eşit olmalı.

    İKİ YÖN DE ÖLÇÜLÜR: kuralda EKSİK ad "panoda düğme var, tıklayınca 502" demektir; kuralda
    FAZLA ad, uçun asla izin vermediği bir birime makine düzeyinde yetki açılmış demektir —
    ikincisi bir güvenlik genişlemesidir ve sessiz kalırsa hiç fark edilmez.

    `reload-daemon` bloğu birim ayrıntısı TAŞIMAZ (dosyanın kendi şerhi bunu söylüyor), o yüzden
    bu tarama yalnız `unit ==` eşleşmelerini sayar."""
    metin = KURAL_DOSYASI.read_text(encoding="utf-8")
    # Şerhler ölçüm dışı: dosyanın yorumlarında birim adları AÇIKLAMA olarak geçiyor ve onları
    # kural sanmak, kaldırılmış bir izni hâlâ var göstermek olurdu.
    kod = re.sub(r"//.*$", "", metin, flags=re.M)
    kuraldakiler = set(re.findall(r'unit\s*==\s*"([^"]+)"', kod))
    beklenen = {f"{a}.service" for a in api.BIRIM_ANAHTAR_BEYAZ}
    assert kuraldakiler == beklenen, (
        f"polkit kuralı ile beyaz liste AYRIŞTI.\n"
        f"  kuralda: {sorted(kuraldakiler)}\n"
        f"  uçta   : {sorted(beklenen)}\n"
        f"  kuralda eksik (panoda düğme var, tıklayınca 502): {sorted(beklenen - kuraldakiler)}\n"
        f"  kuralda fazla (uçun izin vermediği birime makine yetkisi): "
        f"{sorted(kuraldakiler - beklenen)}")


def test_polkit_kurali_SUDO_ILE_DEGIL_DBUS_ILE_yetki_veriyor():
    """Uç bilerek `sudo` kullanmıyor (`NoNewPrivileges`). Kural dosyası da o yolu açmamalı —
    açsaydı iki farklı yetki modeli yan yana yaşar ve hangisinin işlediği belirsizleşirdi."""
    kod = re.sub(r"//.*$", "", KURAL_DOSYASI.read_text(encoding="utf-8"), flags=re.M)
    assert "org.freedesktop.systemd1" in kod, "kural systemd eylemlerine bağlanmamış"
    assert "polkit.Result.YES" in kod, "kural hiçbir şeye izin vermiyor"
