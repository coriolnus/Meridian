"""v375 · HAFIZA YÜZEYİ — `/api/hindsight` (TSK-091 Görev 1): Hindsight'ın SALT-OKUNUR pano vekili.

NUMARA KAYDI (vNNN kimlik sınıfı): v374 (`test_session_refresh_gunluk_v374.py`) doluydu, sıradaki
boş numara v375 ölçüldü (`ls tests/ | grep -oE "v[0-9]+" | sort -t v -k2 -n | tail -1`). Çakışma
YOK.

NEDEN BU DOSYA VAR. Bu uç, panonun tarayıcısıyla Hindsight'ın kimlikli `/v1/*` yüzeyi arasındaki
TEK duvardır — v361'in APISIX için kurduğu duvarın kardeşi. Tarayıcı 8888'e ASLA gitmez: sunucu
okur, anahtarsız bir gövde döner. v361'in iki yalan sınıfı burada da aynen yaşar:

  (1) SIR SINIFI — `/v1/*` çağrıları `Authorization: Bearer <anahtar>` taşır ve anahtar
      `/opt/hindsight/.env` (0600) içinde yaşar. "Gövdeyi olduğu gibi döndüreyim" diyen bir gün,
      tenant anahtarını panonun HTML'ine indirir. Bu dosyanın en sert çivisi budur ve VAKUM
      DEĞİLDİR: anahtarın GERÇEKTEN gönderildiğini de ölçer — gönderilmemiş bir sırrın yanıtta
      olmaması hiçbir şey kanıtlamaz (v361'in ölçülmüş dersi).

  (2) UYDURMA SINIFI — `/opt/hindsight/.env` bu makinede YOKTUR ve olmaması ihlal değil ÖLÇÜM
      SONUCUDUR (v361 `KAPI_ENV_DOSYASI` emsali birebir). Yani "ölçemedim" bu ucun NORMAL hâlidir
      ve `neden` ile SÖYLENMEK zorundadır. Boş `bankalar: []` panoda "hiç banka yok" diye okunur —
      oysa bugün ölçülen iki banka var (`meridian-arsiv`, `smoke-067`). `None` ≠ `0` ≠ `[]`.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. KAYIT + YETKİ — üç uç da rota tablosunda, üçü de `_auth` kapılı, üçü de YALNIZ GET.
B. ÖLÇÜLEMEZLİK YUTULMAZ — env yokken/upstream düşükken 200 + DOLU `neden` (pano kararmaz).
C. ZARF AYNEN GEÇER — `stats`/`llm_stats`/`audit_stats` upstream gövdesinin aynısıdır (süzme yok).
D. SIR DUVARI — anahtar yanıtın hiçbir yerinde yok, ama istekte gerçekten gönderilmiş; istisna
   metnindeki anahtar da maskelenir (ikinci hat, `_kapi_maskele`).
E. LİSTE TAVANI SUNUCUDA — `limit=9999` upstream'e ≤200 gider (istemciye güven yok).
F. EKSİK PARAMETRE 400 DEĞİL — `bank` verilmezse pano KARARMAZ: 200 + neden.
G. YOL ENJEKSİYONU — `bank`/`kimlik` upstream URL'inin PATH'ine giriyor; kaçırılmazsa
   `../../` ile başka uca gidilir. Alıntılama çivili.
H. ZAMAN AŞIMI — her dış çağrı zaman aşımlı; sabit `_kapi_getir`in zorladığıyla AYNI (ayrışma
   çivisi: iki kopya sessizce ayrışır — tek-kaynak yasası).
I. TEK-KAYNAK ÇIKARIMI — `_env_anahtari(dosya, onek)` iki çağıranı da besler; v361 sarmalayıcısı
   davranışını KORUR.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api

# Testte kullanılan SAHTE tenant anahtarı. Gerçek bir anahtara benzemesi kasıtlı: sızıntı çivisi
# gövdede bu dizgeyi arar ve kısa/rastlantısal bir değer yanlış NEGATİF verirdi.
SAHTE_ANAHTAR = "sahte-hindsight-tenant-v375-Rq9Zt4Wm"
GEREKCE_ASGARI = 10          # "yok" bir gerekçe değildir


# --------------------------------------------------------------------------- yardımcılar

class _Casus:
    """`_kapi_getir` casusu: URL'e göre gövde döndürür, her çağrıyı saklar.

    EŞLEŞME EN UZUN PARÇAYA GİDER (sıraya değil): `/v1/default/banks` başka bir anahtarın
    (`/v1/default/banks/x/stats`) ÖN EKİdir; sıraya güvenen bir casus, testin ölçtüğünü sessizce
    değiştirir. Bilinmeyen URL'de `AssertionError` atmak KASITLI: uç yeni bir kaynağa gitmeye
    başlarsa çivi sessizce geçmez, patlar.

    Değer `bytes` ise başarı, `str` ise `_kapi_getir`in `(None, neden)` arızası demektir."""

    def __init__(self, esleme: dict[str, bytes | str]):
        self.esleme = esleme
        self.cagrilar: list[dict] = []

    def __call__(self, url, basliklar=None, sir=None):
        self.cagrilar.append({"url": url, "basliklar": basliklar or {}, "sir": sir})
        adaylar = [p for p in self.esleme if p in url]
        if not adaylar:
            raise AssertionError(f"uç BEKLENMEYEN bir kaynağa gitti: {url}")
        govde = self.esleme[max(adaylar, key=len)]
        if isinstance(govde, str):
            return None, govde
        return govde, None

    def url_ler(self) -> list[str]:
        return [c["url"] for c in self.cagrilar]

    def cagri(self, parca: str) -> dict:
        """Parçayı içeren TEK çağrı — yoksa/birden çoksa test kendi varsayımını kaybetmiş demektir."""
        eslesen = [c for c in self.cagrilar if parca in c["url"]]
        assert len(eslesen) == 1, f"{parca!r} için beklenen 1 çağrı, bulunan {len(eslesen)}"
        return eslesen[0]


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287/v361 emsali): `with TestClient(app)`
    scheduler/hermes ipliklerini ayağa kaldırır ve bu uç için tamamen gereksizdir."""
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def _ag_kapali(monkeypatch):
    """AĞ VARSAYILAN OLARAK KAPALI. Bu makinede 8888 bugün AYAKTA (ölçüldü 2026-09-02) — yani
    casusunu kurmayan bir test GERÇEK Hindsight'ı okur ve ölçtüğü şey artık kod değil o anki
    makine durumu olur. Her test kendi casusunu KENDİ kurar."""
    def _yasak(*a, **kw):
        raise AssertionError("test kendi `_kapi_getir` casusunu kurmadı — gerçek ağ çağrısı yasak")

    monkeypatch.setattr(api, "_kapi_getir", _yasak)
    yield


def _env_dosyasi(monkeypatch, tmp_path, anahtar: str | None = SAHTE_ANAHTAR) -> pathlib.Path:
    """Sahte `/opt/hindsight/.env`. `anahtar=None` → dosya HİÇ yazılmaz (bu makinenin gerçek hâli)."""
    yol = tmp_path / "hindsight.env"
    if anahtar is not None:
        yol.write_text(f"# yorum satiri\nHINDSIGHT_API_TENANT_API_KEY={anahtar}\nBASKA=deger\n")
    monkeypatch.setattr(api, "HAFIZA_ENV_DOSYASI", str(yol))
    return yol


#: Bugün A1'de ölçülen bank'ler (2026-09-02). Bot bank'leri YOK — "bank yok" ≠ "ölçülemedi".
BANKALAR_GOVDE = json.dumps({"banks": [{"bank_id": "meridian-arsiv"}, {"bank_id": "smoke-067"}]}).encode()

#: `/version` GERÇEK gövdesi — A1'de ÖLÇÜLDÜ 2026-09-02
#: (`.superpowers/sdd/2026-09-02-hafiza-sayfasi/upstream-govde-olcumu.txt`).
#: DÜZELTME TURU 1: burada önce `{"version": …}` yazıyordu — UYDURULMUŞ bir alan adı. Kod da aynı
#: adı bekliyordu, yani çivi KENDİ VARSAYIMINI doğruluyordu ve canlıda `surum` sonsuza dek `null`
#: kalırdı. Fixture'ın gerçeğe çekilmesi, çivinin artık kodu değil DÜNYAYI ölçtüğünün kanıtıdır.
SURUM_OLCULEN = "0.9.2"
VERSION_GOVDE = json.dumps({
    "api_version": SURUM_OLCULEN,
    "features": {"observations": True, "mcp": True, "worker": True, "bank_config_api": True,
                 "bank_llm_health": False, "file_upload_api": True},
}).encode()
STATS_GOVDE = json.dumps({"memory_count": 42, "size_bytes": 8192}).encode()
LLM_GOVDE = json.dumps({"request_count": 7, "total_tokens": 1234}).encode()
AUDIT_GOVDE = json.dumps({"event_count": 3}).encode()


def _tam_esleme(**degistir) -> dict[str, bytes | str]:
    """Sağlıklı bir Hindsight'ın tüm uçları. Tek tek ezilebilir (`**degistir`)."""
    esleme: dict[str, bytes | str] = {
        "/health": b'{"status":"ok"}',
        "/version": VERSION_GOVDE,
        "/v1/default/banks": BANKALAR_GOVDE,
    }
    for bank in ("meridian-arsiv", "smoke-067"):
        esleme[f"/banks/{bank}/stats"] = STATS_GOVDE
        esleme[f"/banks/{bank}/llm-requests/stats"] = LLM_GOVDE
        esleme[f"/banks/{bank}/audit-logs/stats"] = AUDIT_GOVDE
    esleme.update(degistir)
    return esleme


def _kurulum(monkeypatch, tmp_path, *, esleme=None, anahtar=SAHTE_ANAHTAR) -> _Casus:
    _env_dosyasi(monkeypatch, tmp_path, anahtar)
    casus = _Casus(_tam_esleme() if esleme is None else esleme)
    monkeypatch.setattr(api, "_kapi_getir", casus)
    return casus


def _dolu(neden) -> bool:
    return isinstance(neden, str) and len(neden) >= GEREKCE_ASGARI


UCLAR = ("/api/hindsight", "/api/hindsight/liste?bank=meridian-arsiv",
         "/api/hindsight/detay?bank=meridian-arsiv&kimlik=m1")


# --------------------------------------------------------------- A. KAYIT + YETKİ

def test_ucler_rota_tablosunda_kayitli():
    yollar = {getattr(r, "path", None) for r in api.app.routes}
    for yol in ("/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay"):
        assert yol in yollar, f"`{yol}` kayıtlı değil — pano yüzeyi hiç doğmamış"


def test_yalniz_get(monkeypatch, tmp_path, sandbox_state):
    """SALT-OKUNUR SÖZLEŞMESİ. Bu uç Hindsight'ın YAZAN fiillerine (memory ekleme/silme) bir köprü
    DEĞİLDİR; GET dışında hiçbir fiil tanımlı olmamalı. 405 rota eşleşmesinde doğar (yetkiden
    ÖNCE), yani kapı açık bir istemci de POST edemez."""
    _kurulum(monkeypatch, tmp_path)
    cl = _client()
    for yol in ("/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay"):
        for fiil in ("post", "put", "delete", "patch"):
            r = getattr(cl, fiil)(yol)
            assert r.status_code == 405, f"{fiil.upper()} {yol} → {r.status_code} (405 bekleniyordu)"


@pytest.mark.parametrize("yol", UCLAR)
def test_uc_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state, yol):
    """Kaynak metni değil DAVRANIŞ: `_auth` casusu çağrılmazsa kırmızı."""
    _kurulum(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert cagrildi == [1], f"`{yol}`: `_auth` çağrılmadı — hafıza yetkisiz açık"


@pytest.mark.parametrize("yol", UCLAR)
def test_auth_kapisi_cerezsiz_401(monkeypatch, tmp_path, sandbox_state, yol):
    """GERÇEK token yolu (`_auth` casuslanmadan): çerez/token yoksa 401, token varsa 200.
    Hafıza bankası operasyonun anlatısıdır — yetkisiz okunmaz."""
    _kurulum(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v375-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)

    cl = _client()
    assert cl.get(yol).status_code == 401, f"`{yol}`: token'sız istek geçti"
    ok = cl.get(yol, headers={"x-meridian-token": "v375-pano-jetonu"})
    assert ok.status_code == 200, ok.text


# ------------------------------------------------------ B. ÖLÇÜLEMEZLİK YUTULMAZ

@pytest.mark.parametrize("yol", UCLAR)
def test_env_yokken_200_ve_neden_dolu(monkeypatch, tmp_path, sandbox_state, yol):
    """`/opt/hindsight/.env` YOKKEN (bu makinenin gerçek hâli) üç uç da 200 döner ve ölçemediğini
    SÖYLER. 500 dönmek panonun Hafıza sayfasını komple karartırdı; sessiz `[]`/`{}` ise "hafızada
    hiçbir şey yok" YALANI olurdu."""
    _kurulum(monkeypatch, tmp_path, anahtar=None)
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    g = r.json()

    if yol == "/api/hindsight":
        assert g["bankalar"] == [], "anahtar yokken banka UYDURULDU"
        assert _dolu(g["bankalar_neden"]), f"ölçülemezlik sessiz: {g['bankalar_neden']!r}"
        assert ".env" in g["bankalar_neden"], "gerekçe anahtar dosyasını ADIYLA söylemiyor"
        assert g["kota"] == {} and g["operasyon"] == {}
    elif "liste" in yol:
        assert g["ogeler"] == [] and _dolu(g["neden"])
    else:
        assert g["oge"] is None and _dolu(g["neden"])


def test_env_yokken_saglik_BAGIMSIZ_olculur(monkeypatch, tmp_path, sandbox_state):
    """`/health` ve `/version` ANAHTARSIZDIR (ölçüldü 2026-09-02). Anahtar yokluğunun sağlık
    bacağını da düşürmesi, TEK arızayı İKİ körlüğe çevirirdi (v361'in prometheus dersi)."""
    casus = _kurulum(monkeypatch, tmp_path, anahtar=None)
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["erisilebilir"] is True, "anahtar yokluğu sağlık bacağını da düşürdü"
    assert g["saglik"]["surum"] == SURUM_OLCULEN
    assert g["saglik"]["neden"] is None
    assert not any("/v1/" in u for u in casus.url_ler()), \
        "anahtar yokken kimlikli `/v1/*` ucuna anahtarsız istek atıldı"


def test_surum_gercek_api_version_alanindan_okunur(monkeypatch, tmp_path, sandbox_state):
    """DÜZELTME TURU 1 — CANLI ÖLÇÜMLE KANITLI SINIF. Hindsight `/version` gövdesinde sürüm alanı
    `api_version`dır, `version` DEĞİL (ölçüldü 2026-09-02, A1). Kod `version` beklediği için
    canlıda `surum` sonsuza dek `null` kalıyordu — üstelik SESSİZCE: hiçbir `neden` üretilmiyordu.
    Bu çivi gerçek gövdeyi besler, yani uydurulmuş bir alan adını doğrulayamaz."""
    _kurulum(monkeypatch, tmp_path)
    s = _client().get("/api/hindsight").json()["saglik"]
    assert s["surum"] == SURUM_OLCULEN, f"gerçek `/version` gövdesinden sürüm okunamadı: {s}"
    assert s["neden"] is None


@pytest.mark.parametrize("govde", [
    b'{"surum":"9.9.9","features":{}}',       # tanınmayan alan adı (şema sürüklenmesi)
    b'{"api_version":123}',                   # alan var, str DEĞİL
    b'{"api_version":""}',                    # alan var, BOŞ
    b'["0.9.2"]',                             # gövde sözlük bile değil
])
def test_taninmayan_surum_alani_sessizce_null_kalmaz(monkeypatch, tmp_path, sandbox_state, govde):
    """SKALER ALANDA DA "TANIMADIĞINI SESSİZCE BOŞ SAYMA". Bu, düzeltme turu 1'in ASIL bulgusuydu:
    ilke dizi/kimlik zarflarına uygulanmıştı ama `surum`a UYGULANMAMIŞTI. `surum: null` + BOŞ
    `neden`, panoda "Hindsight sürümünü bildirmiyor" diye okunur; oysa ölçülen "alan adını
    tanımadım"dır ve bu bir ŞEMA SÜRÜKLENMESİ ALARMIdır.

    Gerekçe alan ADLARINI taşır (sır değildir), DEĞERLERİ değil."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/version": govde}))
    s = _client().get("/api/hindsight").json()["saglik"]

    assert s["erisilebilir"] is True, "sürüm okunamaması sağlık bacağını da düşürdü"
    assert s["surum"] is None, "tanınmayan alandan sürüm UYDURULDU"
    assert _dolu(s["neden"]), f"sürüm alanı tanınmadı ama SESSİZ kalındı: {s['neden']!r}"
    assert "9.9.9" not in (s["neden"] or ""), "gerekçe alan DEĞERİNİ gövdeye taşıdı"


def test_saglik_erisilemez_200_ama_durust(monkeypatch, tmp_path, sandbox_state):
    """Hindsight tamamen düşükken: 200, `erisilebilir` YANLIŞ, `surum` `None` (0 ya da "" değil),
    `neden` DOLU."""
    _kurulum(monkeypatch, tmp_path, esleme={
        "/health": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)",
        "/version": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)",
        "/v1/default/banks": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)"})
    r = _client().get("/api/hindsight")
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["saglik"]["erisilebilir"] is False
    assert g["saglik"]["surum"] is None, "ölçülemeyen sürüm UYDURULDU"
    assert _dolu(g["saglik"]["neden"])
    assert g["bankalar"] == [] and _dolu(g["bankalar_neden"])


def test_bozuk_json_yutulmaz(monkeypatch, tmp_path, sandbox_state):
    """Upstream 200 dönüp GÖVDESİ bozuksa: boş liste + DOLU neden. Sessiz `[]` panoda "banka yok"
    diye okunurdu — oysa ölçülen "gövdeyi anlamadım"dır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/v1/default/banks": b"{bu json degil"}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert _dolu(g["bankalar_neden"])


def test_beklenmeyen_zarf_sessizce_bos_donmez(monkeypatch, tmp_path, sandbox_state):
    """ŞEMA SÜRÜKLENMESİ ALARMI. Hindsight bir gün banka zarfını değiştirirse, dizi ARAYAN kod
    sessizce `[]` döner ve pano "hafıza boş" der. Tanınmayan zarf `neden` ÜRETİR."""
    _kurulum(monkeypatch, tmp_path,
             esleme=_tam_esleme(**{"/v1/default/banks": b'{"beklenmedik": {"a": 1}}'}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert _dolu(g["bankalar_neden"]), "tanınmayan zarf SESSİZCE boş listeye çevrildi"


def test_bos_banka_listesi_olculdu_sayilir(monkeypatch, tmp_path, sandbox_state):
    """ÜÇ-DURUM AYRIMI: Hindsight ayakta ve GERÇEKTEN bankası yoksa `bankalar: []` ama
    `bankalar_neden: None`. Bu, ölçülememiş boşluktan (dolu `neden`) AYRI bir hâldir ve panonun
    boş-durum bileşeninin dayanağıdır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/v1/default/banks": b'{"banks": []}'}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert g["bankalar_neden"] is None, "ÖLÇÜLMÜŞ boşluk 'ölçemedim' gibi gösterildi"
    assert g["kota"] == {} and g["operasyon"] == {}


def test_tek_banka_stats_arizasi_otekini_dusurmez(monkeypatch, tmp_path, sandbox_state):
    """İZOLASYON: bir bankanın `stats`i okunamazsa ÖTEKİ banka hâlâ ölçülür. Aksi hâlde tek bozuk
    banka bütün sayfayı karartırdı."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/banks/smoke-067/stats": "stats okunamadı (HTTPError: 500)"}))
    g = _client().get("/api/hindsight").json()
    kirilim = {b["bank_id"]: b for b in g["bankalar"]}

    assert kirilim["meridian-arsiv"]["stats"] == {"memory_count": 42, "size_bytes": 8192}
    assert kirilim["meridian-arsiv"]["stats_neden"] is None
    assert kirilim["smoke-067"]["stats"] is None, "ölçülemeyen stats için sahte gövde üretildi"
    assert _dolu(kirilim["smoke-067"]["stats_neden"])


# ------------------------------------------------------------ C. ZARF AYNEN GEÇER

def test_bankalar_stats_kota_operasyon_akisi(monkeypatch, tmp_path, sandbox_state):
    """Sözleşmenin ANA çivisi: dört bölüm de upstream gövdesini AYNEN taşır (süzme yok, maske var)
    ve zarfın şekli Görev 2'nin (UI) okuyacağı sözleşmedir."""
    casus = _kurulum(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight")
    assert r.status_code == 200, r.text
    g = r.json()

    assert set(g) == {"saglik", "bankalar", "bankalar_neden", "kota", "operasyon"}, sorted(g)
    assert g["saglik"] == {"erisilebilir": True, "surum": SURUM_OLCULEN, "neden": None}

    assert [b["bank_id"] for b in g["bankalar"]] == ["meridian-arsiv", "smoke-067"]
    for b in g["bankalar"]:
        assert set(b) == {"bank_id", "stats", "stats_neden"}, sorted(b)
        assert b["stats"] == {"memory_count": 42, "size_bytes": 8192}, "upstream gövdesi SÜZÜLDÜ"
        assert b["stats_neden"] is None
    assert g["bankalar_neden"] is None

    assert set(g["kota"]) == {"meridian-arsiv", "smoke-067"}
    assert g["kota"]["meridian-arsiv"] == {"llm_stats": {"request_count": 7, "total_tokens": 1234},
                                           "neden": None}
    assert set(g["operasyon"]) == {"meridian-arsiv", "smoke-067"}
    assert g["operasyon"]["smoke-067"] == {"audit_stats": {"event_count": 3}, "neden": None}

    # Ölçülen uçlar BİREBİR: uç yeni bir upstream'e gitmeye başlarsa (ya da bir bacağı düşürürse)
    # bu sayım ısırır. 2 (health+version) + 1 (banks) + 3×2 (banka başına stats/llm/audit) = 9.
    assert len(casus.cagrilar) == 9, casus.url_ler()


def test_upstream_yollari_olculen_openapi_ile_ayni(monkeypatch, tmp_path, sandbox_state):
    """Uç, 2026-09-02'de openapi'den ÖLÇÜLEN yollara gider — uydurulmuş bir yola değil."""
    casus = _kurulum(monkeypatch, tmp_path)
    _client().get("/api/hindsight")
    urller = casus.url_ler()

    assert f"{api.HAFIZA_TABAN_URL}/health" in urller
    assert f"{api.HAFIZA_TABAN_URL}/version" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/meridian-arsiv/stats" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/smoke-067/llm-requests/stats" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/smoke-067/audit-logs/stats" in urller


def test_liste_ve_detay_zarfi(monkeypatch, tmp_path, sandbox_state):
    """`/liste` ve `/detay` da upstream gövdesini AYNEN taşır."""
    ogeler = json.dumps({"items": [{"id": "m1", "text": "ilk"}, {"id": "m2", "text": "ikinci"}]})
    _kurulum(monkeypatch, tmp_path, esleme={
        "/memories/list": ogeler.encode(),
        "/memories/m1": json.dumps({"id": "m1", "text": "ilk", "metadata": {"k": "v"}}).encode()})

    liste = _client().get("/api/hindsight/liste?bank=meridian-arsiv").json()
    assert set(liste) == {"ogeler", "neden"}, sorted(liste)
    assert liste["ogeler"] == [{"id": "m1", "text": "ilk"}, {"id": "m2", "text": "ikinci"}]
    assert liste["neden"] is None

    detay = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=m1").json()
    assert set(detay) == {"oge", "neden"}, sorted(detay)
    assert detay["oge"] == {"id": "m1", "text": "ilk", "metadata": {"k": "v"}}
    assert detay["neden"] is None


def test_detay_bulunamayan_null_neden(monkeypatch, tmp_path, sandbox_state):
    """Bulunamayan kayıt: `oge` `None` (boş sözlük DEĞİL — "kayıt var ama içi boş" yalanı olurdu)
    ve `neden` DOLU."""
    _kurulum(monkeypatch, tmp_path,
             esleme={"/memories/yok": "detay okunamadı (HTTPError: 404 Not Found)"})
    r = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=yok")
    assert r.status_code == 200, "bulunamayan kayıt panoyu 404'e düşürdü"
    g = r.json()
    assert g["oge"] is None
    assert _dolu(g["neden"]) and "404" in g["neden"], g["neden"]


# ---------------------------------------------------------------- D. SIR DUVARI

@pytest.mark.parametrize("yol", UCLAR)
def test_anahtar_govdeye_sizamaz(monkeypatch, tmp_path, sandbox_state, yol):
    """SIZINTI ÇİVİSİ, VAKUM DEĞİL: anahtar yanıtın HİÇBİR yerinde geçmez, ama `/v1/*` isteğinde
    `Authorization: Bearer …` olarak GERÇEKTEN gönderilmiştir. Gönderilmemiş bir sırrın yanıtta
    olmaması hiçbir şey kanıtlamaz (v361'in ölçülmüş dersi)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/memories/list": b'{"items": []}', "/memories/m1": b'{"id": "m1"}'}))
    r = _client().get(yol)

    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "TENANT ANAHTARI PANOYA SIZDI"

    kimlikli = [c for c in casus.cagrilar if "/v1/" in c["url"]]
    assert kimlikli, "kimlikli hiçbir çağrı yapılmamış — sızıntı çivisi vakumda koşuyordu"
    for c in kimlikli:
        assert c["basliklar"].get("Authorization") == f"Bearer {SAHTE_ANAHTAR}", \
            f"{c['url']}: ölçülen kimlik deseni `Authorization: Bearer` DEĞİL: {c['basliklar']}"
        assert "X-API-Key" not in c["basliklar"], \
            "`X-API-Key` ÖLÇÜLDÜ ve 401 veriyor (2026-09-02) — yanlış başlıkla gidiliyor"


def test_anahtarsiz_uclara_anahtar_gonderilmez(monkeypatch, tmp_path, sandbox_state):
    """EN AZ YETKİ: `/health` ve `/version` anahtarsız 200 veriyor (ölçüldü). Sırrı gereksiz yere
    tele koymak, sızıntı yüzeyini bedelsiz büyütmektir."""
    casus = _kurulum(monkeypatch, tmp_path)
    _client().get("/api/hindsight")
    for parca in ("/health", "/version"):
        assert not casus.cagri(parca)["basliklar"], \
            f"{parca} anahtarsız bir uç — yine de başlık gönderildi"


@pytest.mark.parametrize("yol", UCLAR)
def test_istisna_metnindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state, yol):
    """İKİNCİ SAVUNMA HATTI (`_kapi_maskele`): alt katman bir gün anahtarı istisna metnine ya da
    upstream gövdesine koyarsa, o metin `neden`e/gövdeye AYNEN geçmemeli. Gerekçenin KENDİSİ
    silinmez — silmek sızıntıyı kapatıp körlüğü açardı."""
    sizan = f"401 — Authorization: Bearer {SAHTE_ANAHTAR} reddedildi"
    _kurulum(monkeypatch, tmp_path, esleme={
        "/health": b'{"status":"ok"}', "/version": VERSION_GOVDE,
        "/v1/default/banks": sizan, "/memories/list": sizan, "/memories/m1": sizan})

    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "istisna metniyle taşınan anahtar panoya sızdı"
    assert "***" in r.text, "maskeleme uğruna gerekçe komple silinmiş — körlük açıldı"


def test_upstream_govdesindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state):
    """Sır upstream'in KENDİ gövdesinden de gelebilir (Hindsight bir gün tenant anahtarını
    `stats`e yazarsa). Aynen-geçiş sözleşmesi maskeyi ISKALAMAZ."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/banks/meridian-arsiv/stats": json.dumps({"tenant_key": SAHTE_ANAHTAR}).encode()}))
    r = _client().get("/api/hindsight")
    assert SAHTE_ANAHTAR not in r.text, "upstream gövdesindeki anahtar aynen panoya basıldı"


# ----------------------------------------------------------- E. LİSTE TAVANI SUNUCUDA

def test_liste_limit_tavani_kirpar(monkeypatch, tmp_path, sandbox_state):
    """KIRPMA SUNUCUDA. `limit` istemciden gelir ve istemciye GÜVENİLMEZ: `limit=9999` bir
    Hindsight sorgusunu ve pano yükünü sınırsız büyütür. Tavan `HAFIZA_LISTE_TAVANI`dır ve
    upstream URL'inde ÖLÇÜLÜR — "UI zaten 50 gönderiyor" bir güvence DEĞİLDİR."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=9999")

    url = casus.cagri("/memories/list")["url"]
    assert "9999" not in url, f"kırpılmamış limit upstream'e gitti: {url}"
    assert f"limit={api.HAFIZA_LISTE_TAVANI}" in url, url
    assert api.HAFIZA_LISTE_TAVANI == 200


def test_liste_makul_limit_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    """Kırpma bir TAVANdır, sabit değil: tavanın altındaki değer AYNEN geçer (aksi hâlde sayfalama
    çalışmazdı)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=25&offset=75")
    url = casus.cagri("/memories/list")["url"]
    assert "limit=25" in url and "offset=75" in url, url


def test_liste_sacma_limit_offset_alt_sinira_oturur(monkeypatch, tmp_path, sandbox_state):
    """`limit=0`/negatif değerler upstream'e SIZMAZ: kimi API'de `limit=0` "hepsi" demektir ve
    tavanı sessizce delerdi. `offset` de negatif olamaz."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=0&offset=-5")
    url = casus.cagri("/memories/list")["url"]
    assert "limit=0" not in url and "limit=-" not in url, url
    assert "offset=-" not in url and "offset=0" in url, url


@pytest.mark.parametrize("sorgu", ["limit=abc", "limit=1.5", "offset=xyz", "limit=&offset="])
def test_liste_bozuk_sayi_400_degil_tavana_oturur(monkeypatch, tmp_path, sandbox_state, sorgu):
    """EKSİK PARAMETRENİN KARDEŞİ: `limit`i `int` yazmak FastAPI'ye 422 ürettirir ve pano o cevabı
    gövde sanıp KARARIR — `bank` için kapatılan sınıf `limit` için açık kalamaz. Ayrıştırılamayan
    sayı bir ÖLÇÜM DEĞİLDİR: sessizce 0'a değil, beyan edilmiş varsayılana oturur."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    r = _client().get(f"/api/hindsight/liste?bank=meridian-arsiv&{sorgu}")

    assert r.status_code == 200, f"{sorgu!r}: {r.status_code} — pano karardı"
    url = casus.cagri("/memories/list")["url"]
    assert f"limit={api.HAFIZA_LISTE_TAVANI}" in url or "limit=1" in url, url
    assert "offset=0" in url, url


# --------------------------------------------------- F. EKSİK PARAMETRE 400 DEĞİL

def test_liste_bank_parametresiz_400_degil_neden(monkeypatch, tmp_path, sandbox_state):
    """FastAPI'nin varsayılanı ZORUNLU parametrede 422'dir ve pano o cevabı gövde sanıp KARARIR.
    Sözleşme: 200 + boş `ogeler` + DOLU `neden`. Ayrıca upstream'e HİÇ gidilmez."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    r = _client().get("/api/hindsight/liste")

    assert r.status_code == 200, f"eksik parametre {r.status_code} üretti — pano karardı"
    g = r.json()
    assert g["ogeler"] == []
    assert _dolu(g["neden"]) and "bank" in g["neden"], g["neden"]
    assert casus.cagrilar == [], "parametre eksikken yine de upstream'e gidildi"


@pytest.mark.parametrize("sorgu", ["", "?bank=meridian-arsiv", "?kimlik=m1", "?bank=&kimlik="])
def test_detay_eksik_parametre_400_degil_neden(monkeypatch, tmp_path, sandbox_state, sorgu):
    """`/detay` İKİ parametre ister; hangisi eksikse eksik — ve BOŞ dizge de eksiktir
    (`?bank=` bir değer DEĞİLDİR, upstream'e `/banks//memories/` diye giderdi)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/m1": b'{"id":"m1"}'})
    r = _client().get(f"/api/hindsight/detay{sorgu}")

    assert r.status_code == 200, f"{sorgu!r}: {r.status_code}"
    g = r.json()
    assert g["oge"] is None
    assert _dolu(g["neden"])
    assert casus.cagrilar == [], f"{sorgu!r}: parametre eksikken upstream'e gidildi"


# --------------------------------------------------------------- G. YOL ENJEKSİYONU

@pytest.mark.parametrize("kotu", ["../../v1/default/banks", "a/../../etc", "a b", "a?x=1", "a#f"])
def test_bank_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state, kotu):
    """`bank` KULLANICI GİRDİSİDİR ve upstream URL'inin PATH'ine giriyor. Kaçırılmazsa `../../`
    ile Hindsight'ın BAŞKA bir ucuna gidilir (yazan bir uca bile) — salt-okunur sözleşmesi
    istemcinin insafına kalırdı. `/` `%2F` olarak kaçırılmalı, çıplak kalmamalı."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    # GİRDİ İSTEMCİ TARAFINDA KAÇIRILIR, yoksa test VAKUMDA koşar: ölçüldü (mutasyon turu,
    # 2026-09-02) — `?bank=a#f` içindeki `#` bir FRAGMAN'dır, sunucuya hiç ulaşmaz ve çivi
    # kaçırılmamış `#`i "geçti" sanardı. Sunucunun GERÇEKTEN gördüğü değer `kotu` olmalı.
    import urllib.parse
    _client().get(f"/api/hindsight/liste?bank={urllib.parse.quote(kotu, safe='')}")

    url = casus.cagri("/memories/list")["url"]
    govde = url[len(f"{api.HAFIZA_TABAN_URL}/v1/default/banks/"):]
    kimlik = govde.split("/memories/list")[0]
    for ham in ("/", "..", " ", "?", "#"):
        assert ham not in kimlik, f"kaçırılmamış {ham!r} upstream PATH'ine girdi: {url}"


def test_detay_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state):
    """Aynı sınıf, `kimlik` parametresinde."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/": b'{"id": "x"}'})
    _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=../../../stats")

    url = casus.cagrilar[0]["url"]
    kuyruk = url.split("/memories/", 1)[1]
    assert "/" not in kuyruk and ".." not in kuyruk, f"kaçırılmamış kimlik: {url}"


# ------------------------------------------------------------------ H. ZAMAN AŞIMI

def test_zaman_asimi_sabiti_beyanli():
    assert 0 < api.HAFIZA_ZAMAN_ASIMI_S <= 2.0


def test_zaman_asimi_kopyasi_ayrisirsa_isirir():
    """TEK-KAYNAK / AYRIŞMA ÇİVİSİ. Zaman aşımını GERÇEKTEN zorlayan sabit `_kapi_getir`in
    okuduğu `KAPI_ZAMAN_ASIMI_S`dir; `HAFIZA_ZAMAN_ASIMI_S` sözleşmenin BEYANIdır. İki kopya
    sessizce ayrışabilir: biri 2.0 kalıp öteki 30.0 olursa gövdedeki beyan YALAN söyler ve pano
    15 sn'lik yoklamada asılır. Ayrışma burada ÖTER."""
    assert api.HAFIZA_ZAMAN_ASIMI_S == api.KAPI_ZAMAN_ASIMI_S, (
        "beyan edilen hafıza zaman aşımı, `_kapi_getir`in zorladığından AYRIŞTI — "
        "beyan ya düzeltilmeli ya da `_kapi_getir` parametrikleştirilmeli")


def test_uc_state_defterine_yazmaz(monkeypatch, tmp_path, sandbox_state):
    """SALT-OKUNUR sözleşmesi: pano 15 sn'de bir yokluyor — yazan bir uç canlı defteri kirletirdi
    (v361 emsali)."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/memories/list": b'{"items": []}', "/memories/m1": b'{"id":"m1"}'}))
    once = sorted(p.name for p in sandbox_state.rglob("*"))
    cl = _client()
    for yol in UCLAR:
        cl.get(yol)
    assert sorted(p.name for p in sandbox_state.rglob("*")) == once


# ------------------------------------------------------- I. TEK-KAYNAK ÇIKARIMI

def test_env_anahtari_iki_cagirani_da_besler(monkeypatch, tmp_path):
    """`_env_anahtari(dosya, onek)` TEK kaynaktır: aynı ayrıştırma iki yerde kopyalanırsa
    (v361 + v375) sessizce ayrışır — tek-kaynak yasası."""
    yol = tmp_path / "x.env"
    yol.write_text("# yorum\nONEK_A=deger-a\nONEK_B=deger-b\n")

    assert api._env_anahtari(str(yol), "ONEK_A=") == ("deger-a", None)
    assert api._env_anahtari(str(yol), "ONEK_B=") == ("deger-b", None)

    deger, neden = api._env_anahtari(str(yol), "YOK_ONEK=")
    assert deger is None and _dolu(neden) and "YOK_ONEK=" in neden

    deger, neden = api._env_anahtari(str(tmp_path / "hic-yok.env"), "ONEK_A=")
    assert deger is None and _dolu(neden) and "hic-yok.env" in neden


def test_bos_deger_anahtar_sayilmaz(monkeypatch, tmp_path):
    """`ANAHTAR=` satırı bir anahtar DEĞİLDİR — boş dizgeyle `Bearer ` göndermek 401 döndürür ve
    arıza "yanlış anahtar" gibi görünürdü; gerçek arıza "anahtar hiç yok"tur."""
    yol = tmp_path / "bos.env"
    yol.write_text("HINDSIGHT_API_TENANT_API_KEY=\n")
    deger, neden = api._env_anahtari(str(yol), api.HAFIZA_ANAHTAR_ONEKI)
    assert deger is None and _dolu(neden) and "BOŞ" in neden


def test_v361_sarmalayicisi_davranisini_korur(monkeypatch, tmp_path):
    """ÇIKARIM REGRESYON ÇİVİSİ: `_kapi_admin_anahtari` artık `_env_anahtari`nin sarmalayıcısıdır
    ama SÖZLEŞMESİ değişmedi — v361 çivileri bu davranışa yaslanıyor."""
    yol = tmp_path / ".env-apisix"
    yol.write_text(f"# yorum\nAPISIX_ADMIN_KEY={SAHTE_ANAHTAR}\n")
    monkeypatch.setattr(api, "KAPI_ENV_DOSYASI", str(yol))
    assert api._kapi_admin_anahtari() == (SAHTE_ANAHTAR, None)

    monkeypatch.setattr(api, "KAPI_ENV_DOSYASI", str(tmp_path / "yok"))
    deger, neden = api._kapi_admin_anahtari()
    assert deger is None and ".env-apisix" not in (deger or "")
    assert _dolu(neden) and "yok" in neden


def test_hafiza_sabitleri_olculen_degerlerde():
    """Sabitler brief'in ÖLÇÜLMÜŞ gerçeklerinden gelir — uydurma değil."""
    assert api.HAFIZA_TABAN_URL == "http://127.0.0.1:8888"
    assert api.HAFIZA_ENV_DOSYASI == "/opt/hindsight/.env"
    assert api.HAFIZA_ANAHTAR_ONEKI == "HINDSIGHT_API_TENANT_API_KEY="
    assert api.HAFIZA_LISTE_TAVANI == 200
