"""v361 · KAPI YÜZEYİ — `/api/gateway` (TSK-090 Görev 1): APISIX'in SALT-OKUNUR pano vekili.

NEDEN BU DOSYA VAR. Bu uç, panonun tarayıcısıyla APISIX'in yönetim yüzeyi arasındaki TEK
duvardır. Tarayıcı 9180'e (Admin API) ve 9091'e (prometheus) ASLA gitmez; ikisini de sunucu
okur ve süzülmüş bir gövde döner. Bu duvarın iki tarafında iki ayrı yalan sınıfı yaşar:

  (1) SIR SINIFI — Admin API'ye giden istek `X-API-KEY` taşır ve rota gövdelerinin içinde
      `auth.header.Authorization` alanları vardır. Bir gün biri "ne var ki, gövdeyi olduğu gibi
      döndüreyim" derse, admin anahtarı ya da (etcd'ye kazara literal yazılmışsa) OpenRouter
      anahtarı panonun HTML'ine iner. Bu dosyanın en sert çivisi budur ve VAKUM DEĞİLDİR:
      anahtarın GERÇEKTEN gönderildiğini de ölçer (gönderilmemiş bir sırrın yokluğunu kanıtlamak
      hiçbir şey kanıtlamaz).

  (2) UYDURMA SINIFI — bu uç YEREL makinede hiçbir zaman ölçüm yapamaz: 9180 de 9091 de yalnız
      A1'de var, `/opt/apisix/.env-apisix` bu makinede YOK. Yani "erişilemedi" bu ucun NORMAL
      hâlidir ve `kaynak_ok: false` + dolu `neden` ile söylenmek zorundadır. `istek_n: 0` yazmak
      sözdizimsel olarak bedavadır ve panoda "kapıdan hiç istek geçmemiş" diye okunur — oysa
      ölçülen şey "ölçemedim"dir. `atlanan_satir` da aynı sınıftadır: prometheus hiç okunamadıysa
      0 değil `None` döner ("bozuk satır yok" ile "satır görmedim" AYNI ŞEY DEĞİLDİR).

BU DOSYA NEYİ ÇİVİLER
---------------------
A. KAYIT + YETKİ — uç rota tablosunda var, `_auth` ÇAĞIRIYOR (davranış çivisi: `_auth` satırını
   yoruma almak testi yeşil bırakmamalı), ve GERÇEK token yolundan da 401 veriyor. Kapı
   telemetrisi yetkisiz açılmaz: rota listesi altyapının haritasıdır.

B. ERİŞİLEMEZLİK YUTULMAZ — admin/prometheus düşükken uç 200 döner (pano asılı kalmaz) ama
   `saglik.*` YANLIŞ, `neden` DOLU, `rotalar` boş, `metrikler.kaynak_ok` yanlış. İstisna
   sınıflanır; 500'e çevirmek panonun tamamını kapının sağlığına bağlardı.

C. ROTA ŞEMASI BİREBİR — `deploy/apisix/routes.yaml`ın GERÇEK şekli Admin API zarfına
   (`{"list": [{"value": …}]}`) sarılıp beslenir. Böylece kaynak dosya bir gün şekil
   değiştirirse çivi ısırır. Admin API'nin eklediği gürültü alanları (`create_time`, `status`,
   `priority`) gövdeye SIZMAZ.

D. SIR DUVARI — üç ayrı yönden: (d1) admin anahtarı yanıtın hiçbir yerinde geçmez, ama İSTEKTE
   gerçekten gönderilmiştir; (d2) istisna METNİ anahtarı taşısa bile maskelenir (ikinci savunma
   hattı); (d3) rota gövdesindeki `auth.header.Authorization` alanı `$env://…` referansıysa
   AYNEN geçer (tasarım: "sırlar $ENV referansı olarak"), referans DEĞİLSE — yani etcd'ye
   kazara gerçek bir anahtar yazılmışsa — panoya ÇIKMAZ.

E. METRİK AYRIŞTIRMA + BOZUK SATIR SAYIMI — `apisix_http_status{…}` sayaçları rota başına
   toplanır; ayrıştırılamayan satır SESSİZCE atlanmaz, `atlanan_satir`e SAYILIR. İlgisiz satır
   (`# HELP`, başka metrik) atlanan DEĞİLDİR — o ayrım olmadan sayaç gürültüden ibaret olurdu.
   NaN/Inf değerler de atlanır — telde patladıkları için DEĞİL (`store.sanitize` onları `None`a
   çevirir, ölçüldü), toplamaya girerlerse rotanın `istek_n`ini KOMPLE NaN yapıp ölçülmüş
   sayaçları da "ölçülemedi"ye çevirdikleri için.

F. ZAMAN AŞIMI ≤ 2 sn — kapı düşükken (SYN yutulması) varsayılan soket zaman aşımı SONSUZDUR;
   pano 15 sn'de bir yoklayan bir uçta asılır. Çivi çağrı imzasından ölçer.

G. FAZLAR UYDURULMAZ — TSK-089'un dört fazı sabit metin DEĞİL, rota gövdelerindeki plugin
   imzalarından TÜRETİLİR ve ölçülemediğinde üçüncü hâle (`olculemedi`) düşer.
"""
from __future__ import annotations

import json
import pathlib
import urllib.request

import pytest
import yaml
from fastapi.testclient import TestClient

from meridian import api

REPO = pathlib.Path(__file__).resolve().parents[1]
ROTA_KAYNAGI = REPO / "deploy" / "apisix" / "routes.yaml"

# Testte kullanılan SAHTE admin anahtarı. Gerçek bir anahtara benzemesi kasıtlı: sızıntı çivisi
# gövdede bu dizgeyi arar ve "edvvvedvvv" gibi kısa/rastlantısal bir değer yanlış negatif verirdi.
SAHTE_ANAHTAR = "sahte-admin-anahtari-v361-KMx7Qd2p"
GEREKCE_ASGARI = 10          # "yok" bir gerekçe değildir


# --------------------------------------------------------------------------- yardımcılar

class _SahteYanit:
    """`urlopen` bağlam yöneticisi taklidi — yalnız `read()` gerekiyor."""

    def __init__(self, govde: bytes):
        self._govde = govde

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self) -> bytes:
        return self._govde


class _Casus:
    """`urlopen` casusu: URL'e göre gövde döndürür, her çağrının isteğini ve zaman aşımını saklar.

    Bilinmeyen URL'de `AssertionError` atmak KASITLI: uç yeni bir kaynağa gitmeye başlarsa çivi
    sessizce geçmez, patlar."""

    def __init__(self, **url_govde: bytes | Exception):
        self.eslesme = url_govde
        self.cagrilar: list[dict] = []

    def __call__(self, req, timeout=None, **kw):
        url = getattr(req, "full_url", req)
        self.cagrilar.append({"url": url, "timeout": timeout, "req": req})
        for anahtar, govde in self.eslesme.items():
            if anahtar in url:
                if isinstance(govde, Exception):
                    raise govde
                return _SahteYanit(govde)
        raise AssertionError(f"uç BEKLENMEYEN bir kaynağa gitti: {url}")


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287 emsali): `with TestClient(app)` scheduler/hermes
    ipliklerini ayağa kaldırır ve bu uç için tamamen gereksizdir."""
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def _ag_kapali(monkeypatch):
    """AĞ VARSAYILAN OLARAK KAPALI. Bu makinede 9180/9091 yok; ama bir gün biri kendi makinesinde
    APISIX koşarken suite'i çalıştırırsa test GERÇEK kapıyı okur ve ölçtüğü şey artık kod değil o
    makinenin durumu olur. Her test kendi casusunu KENDİ kurar; kurmayan hiçbir yere gidemez."""
    def _yasak(*a, **kw):
        raise AssertionError("test kendi `urlopen` casusunu kurmadı — gerçek ağ çağrısı yasak")

    monkeypatch.setattr(urllib.request, "urlopen", _yasak)
    yield


def _env_dosyasi(monkeypatch, tmp_path, anahtar: str | None = SAHTE_ANAHTAR) -> pathlib.Path:
    """Sahte `.env-apisix`. `anahtar=None` → dosya HİÇ yazılmaz (yerel makinenin gerçek hâli)."""
    yol = tmp_path / ".env-apisix"
    if anahtar is not None:
        yol.write_text(f"# yorum satiri\nAPISIX_ADMIN_KEY={anahtar}\nBASKA=deger\n")
    monkeypatch.setattr(api, "KAPI_ENV_DOSYASI", str(yol))
    return yol


def _admin_zarfi(rotalar: list[dict]) -> bytes:
    """Admin API'nin GERÇEK zarfı + GERÇEK gürültü alanları (`create_time` vb. gövdeye sızmamalı)."""
    return json.dumps({"list": [
        {"key": f"/apisix/routes/{r['id']}",
         "value": {**r, "create_time": 1756000000, "update_time": 1756000001, "status": 1,
                   "priority": 0}}
        for r in rotalar]}).encode()


def _gercek_rotalar() -> list[dict]:
    veri = yaml.safe_load(ROTA_KAYNAGI.read_text())
    return veri["rotalar"]


def _kurulum(monkeypatch, tmp_path, *, admin=None, prom=b"", anahtar=SAHTE_ANAHTAR) -> _Casus:
    """Standart kurulum: sahte env dosyası + admin/prometheus casusu."""
    _env_dosyasi(monkeypatch, tmp_path, anahtar)
    if admin is None:
        admin = _admin_zarfi(_gercek_rotalar())
    casus = _Casus(**{"9180": admin, "9091": prom})
    monkeypatch.setattr(urllib.request, "urlopen", casus)
    return casus


# --------------------------------------------------------------- A. KAYIT + YETKİ

def test_uc_rota_tablosunda_kayitli():
    yollar = {getattr(r, "path", None) for r in api.app.routes}
    assert "/api/gateway" in yollar, "`/api/gateway` kayıtlı değil — pano yüzeyi hiç doğmamış"


def test_uc_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state):
    """Kaynak metni değil DAVRANIŞ: `_auth` casusu çağrılmazsa kırmızı."""
    _kurulum(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().get("/api/gateway")
    assert r.status_code == 200, r.text
    assert cagrildi == [1], "`_auth` çağrılmadı — kapı telemetrisi yetkisiz açık"


def test_uc_auth_reddini_yutmaz(monkeypatch, tmp_path, sandbox_state):
    from fastapi import HTTPException

    _kurulum(monkeypatch, tmp_path)

    def _red(request):
        raise HTTPException(status_code=401, detail="yetkisiz")

    monkeypatch.setattr(api, "_auth", _red)
    r = _client().get("/api/gateway")
    assert r.status_code == 401, f"yetki reddi yutuldu (durum={r.status_code})"


def test_tokensiz_istek_401(monkeypatch, tmp_path, sandbox_state):
    """GERÇEK token yolu (`_auth` casuslanmadan): `x-meridian-token` yoksa 401, varsa 200."""
    _kurulum(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v361-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)

    cl = _client()
    assert cl.get("/api/gateway").status_code == 401, "token'sız istek geçti"
    ok = cl.get("/api/gateway", headers={"x-meridian-token": "v361-pano-jetonu"})
    assert ok.status_code == 200, ok.text


# ------------------------------------------------------- B. ERİŞİLEMEZLİK YUTULMAZ

def test_admin_ve_prometheus_erisilemez_200_ama_durust(monkeypatch, tmp_path, sandbox_state):
    """Kapı yokken uç 200 döner (pano asılmaz) ama HİÇBİR ŞEY ÖLÇTÜĞÜNÜ İDDİA ETMEZ."""
    _env_dosyasi(monkeypatch, tmp_path)
    casus = _Casus(**{"9180": OSError("bağlantı reddedildi"),
                      "9091": OSError("bağlantı reddedildi")})
    monkeypatch.setattr(urllib.request, "urlopen", casus)

    r = _client().get("/api/gateway")
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["saglik"]["admin_api"] is False
    assert g["saglik"]["prometheus"] is False
    assert isinstance(g["saglik"]["neden"], str) and len(g["saglik"]["neden"]) >= GEREKCE_ASGARI
    assert g["rotalar"] == [], "erişilemezken rota UYDURULDU"
    assert g["metrikler"]["kaynak_ok"] is False
    assert g["metrikler"]["rota_basina"] == {}
    assert g["metrikler"]["atlanan_satir"] is None, \
        "prometheus hiç okunmadı — `atlanan_satir: 0` 'bozuk satır yok' YALANIDIR"
    assert isinstance(g["metrikler"]["neden"], str) and len(g["metrikler"]["neden"]) >= GEREKCE_ASGARI


def test_env_dosyasi_yoksa_admin_saglik_yanlis(monkeypatch, tmp_path, sandbox_state):
    """`/opt/apisix/.env-apisix` yoksa (YEREL makinenin gerçek hâli) admin okunamaz — ve bu
    `neden`de ADIYLA yazar. Prometheus anahtarsızdır, o BAĞIMSIZ ölçülür."""
    _env_dosyasi(monkeypatch, tmp_path, anahtar=None)
    casus = _Casus(**{"9091": b"# HELP apisix_http_status codes\n"})
    monkeypatch.setattr(urllib.request, "urlopen", casus)

    g = _client().get("/api/gateway").json()
    assert g["saglik"]["admin_api"] is False
    assert g["saglik"]["prometheus"] is True, "anahtar yokluğu prometheus bacağını da düşürdü"
    assert ".env-apisix" in g["saglik"]["neden"]
    assert not any("9180" in c["url"] for c in casus.cagrilar), \
        "anahtar yokken Admin API'ye anahtarsız istek atıldı"


def test_bozuk_admin_json_yutulmaz(monkeypatch, tmp_path, sandbox_state):
    """Admin 200 dönüp GÖVDESİ bozuksa: boş rota + dolu neden. Sessiz `[]` 'kapıda rota yok'
    diye okunurdu."""
    _kurulum(monkeypatch, tmp_path, admin=b"{bu json degil")
    g = _client().get("/api/gateway").json()
    assert g["saglik"]["admin_api"] is False
    assert g["rotalar"] == []
    assert len(g["saglik"]["neden"] or "") >= GEREKCE_ASGARI


# ------------------------------------------------------------ C. ROTA ŞEMASI BİREBİR

def test_rota_semasi_birebir_gercek_routes_yaml(monkeypatch, tmp_path, sandbox_state):
    """Girdi `deploy/apisix/routes.yaml`ın KENDİSİDİR (tek-kaynak): dosya şekil değiştirirse ısırır."""
    _kurulum(monkeypatch, tmp_path)
    g = _client().get("/api/gateway").json()

    assert g["saglik"]["admin_api"] is True
    assert g["saglik"]["neden"] is None
    idler = [r["id"] for r in g["rotalar"]]
    assert idler == [r["id"] for r in _gercek_rotalar()], idler

    danisma = next(r for r in g["rotalar"] if r["id"] == "llm-danisma")
    assert set(danisma) == {"id", "uri", "zincir", "fallback_tetikleri", "temizlenen_basliklar"}, \
        f"rota şeması ayrıştı: {sorted(danisma)}"
    assert danisma["uri"] == "/llm/v1/chat/completions"
    assert danisma["fallback_tetikleri"] == ["http_429", "http_5xx"]
    assert danisma["temizlenen_basliklar"] == ["Authorization", "X-Forwarded-For", "X-Real-IP"]

    assert set(danisma["zincir"][0]) == {"ad", "model", "oncelik", "auth_referansi"}
    assert [z["ad"] for z in danisma["zincir"]] == ["birincil-nemotron", "yedek-gemma"]
    assert danisma["zincir"][0]["model"] == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert danisma["zincir"][0]["oncelik"] == 10


def test_admin_gurultu_alanlari_govdeye_sizmaz(monkeypatch, tmp_path, sandbox_state):
    """Admin API `create_time`/`update_time`/`status` ekler; pano şeması onları TAŞIMAZ."""
    _kurulum(monkeypatch, tmp_path)
    metin = _client().get("/api/gateway").text
    for gurultu in ("create_time", "update_time"):
        assert gurultu not in metin, f"Admin API gürültüsü `{gurultu}` panoya sızdı"


def test_zincir_oncelige_gore_azalan(monkeypatch, tmp_path, sandbox_state):
    """Zincir SUNUCUDA sıralanır (öncelik desc) — UI sıralama sorumluluğu taşımaz. Girdi kasten
    ARTAN sırada verilir; dönen sıra AZALAN değilse çivi ısırır."""
    rota = {"id": "karisik", "uri": "/x", "plugins": {"ai-proxy-multi": {"instances": [
        {"name": "dusuk", "priority": 1, "options": {"model": "m-dusuk"}},
        {"name": "yuksek", "priority": 30, "options": {"model": "m-yuksek"}},
        {"name": "orta", "priority": 10, "options": {"model": "m-orta"}}]}}}
    _kurulum(monkeypatch, tmp_path, admin=_admin_zarfi([rota]))
    g = _client().get("/api/gateway").json()
    assert [z["ad"] for z in g["rotalar"][0]["zincir"]] == ["yuksek", "orta", "dusuk"]


def test_zincirsiz_rota_bos_liste_dondurur(monkeypatch, tmp_path, sandbox_state):
    """`ai-proxy-multi` TAŞIMAYAN rota (Faz 2/3'te doğacak sınıf) uç'u düşürmez; zinciri BOŞ'tur
    — bu ölçülmüş bir boşluktur, ölçülememiş bir boşluk değil."""
    rota = {"id": "duz", "uri": "/saglik", "plugins": {"limit-count": {"count": 250}}}
    _kurulum(monkeypatch, tmp_path, admin=_admin_zarfi([rota]))
    g = _client().get("/api/gateway").json()
    assert g["rotalar"][0]["zincir"] == []
    assert g["rotalar"][0]["fallback_tetikleri"] == []
    assert g["rotalar"][0]["temizlenen_basliklar"] == []


# ------------------------------------------------------------------ D. SIR DUVARI

def test_admin_anahtari_yanitta_hicbir_yerde_gecmez(monkeypatch, tmp_path, sandbox_state):
    """SIZINTI ÇİVİSİ. VAKUM DEĞİL: anahtarın İSTEKTE gerçekten gönderildiği de ölçülür —
    hiç kullanılmamış bir sırrın yanıtta olmaması hiçbir şey kanıtlamaz."""
    casus = _kurulum(monkeypatch, tmp_path)
    r = _client().get("/api/gateway")

    assert SAHTE_ANAHTAR not in r.text, "ADMIN ANAHTARI PANOYA SIZDI"
    admin_cagri = next(c for c in casus.cagrilar if "9180" in c["url"])
    gonderilen = list(getattr(admin_cagri["req"], "headers", {}).values())
    assert SAHTE_ANAHTAR in gonderilen, \
        "anahtar Admin API'ye HİÇ gönderilmemiş — sızıntı çivisi vakumda koşuyordu"


def test_istisna_metnindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state):
    """İKİNCİ SAVUNMA HATTI: alt katman bir gün anahtarı istisna metnine koyarsa (proxy/vekil
    kütüphaneleri URL'e gömülü kimlik bilgisini basar), o metin `neden` alanına AYNEN geçmemeli."""
    _env_dosyasi(monkeypatch, tmp_path)
    casus = _Casus(**{"9180": OSError(f"401 — X-API-KEY={SAHTE_ANAHTAR} reddedildi"),
                      "9091": OSError("baglanti yok")})
    monkeypatch.setattr(urllib.request, "urlopen", casus)

    r = _client().get("/api/gateway")
    assert r.status_code == 200
    assert SAHTE_ANAHTAR not in r.text, "istisna metniyle taşınan anahtar panoya sızdı"
    assert len(r.json()["saglik"]["neden"] or "") >= GEREKCE_ASGARI, \
        "maskeleme uğruna gerekçe komple silinmiş — sızıntı kapandı, körlük açıldı"


def test_env_referansi_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    """`$env://OPENROUTER_AUTH` bir SIR DEĞİL, sırra bir REFERANSTIR — tasarım kararı gereği
    olduğu gibi gösterilir (operatör 'hangi env okunuyor' sorusunu panodan cevaplar)."""
    _kurulum(monkeypatch, tmp_path)
    g = _client().get("/api/gateway").json()
    danisma = next(r for r in g["rotalar"] if r["id"] == "llm-danisma")
    assert danisma["zincir"][0]["auth_referansi"] == "$env://OPENROUTER_AUTH"


def test_referans_olmayan_auth_degeri_gizlenir(monkeypatch, tmp_path, sandbox_state):
    """Ve TERS YÖN: etcd'ye kazara GERÇEK bir anahtar yazılmışsa (tünel-CRUD sapması, TSK-089'un
    adlı riski) o değer panoya ÇIKMAZ. `$env://` ile başlamayan her şey sır muamelesi görür."""
    kacak = "sk-or-v1-KACAK-GERCEK-ANAHTAR-9f2b"
    rota = {"id": "sizinti", "uri": "/x", "plugins": {"ai-proxy-multi": {"instances": [
        {"name": "a", "priority": 1, "options": {"model": "m"},
         "auth": {"header": {"Authorization": kacak}}}]}}}
    _kurulum(monkeypatch, tmp_path, admin=_admin_zarfi([rota]))

    r = _client().get("/api/gateway")
    assert kacak not in r.text, "etcd'ye kaçmış LİTERAL anahtar panoya aynen basıldı"
    ref = r.json()["rotalar"][0]["zincir"][0]["auth_referansi"]
    assert ref is not None and "gizlend" in ref.lower(), \
        f"gizleme SESSİZ oldu — operatör alanın boş mu gizli mi olduğunu bilemez: {ref!r}"


# ------------------------------------------- E. METRİK AYRIŞTIRMA + BOZUK SATIR SAYIMI

_PROM = """\
# HELP apisix_http_status HTTP status codes per service
# TYPE apisix_http_status counter
apisix_http_status{code="200",route="llm-danisma",matched_uri="/llm/v1/chat/completions"} 10
apisix_http_status{code="429",route="llm-danisma",matched_uri="/llm/v1/chat/completions"} 2
apisix_http_status{code="200",route="llm-hizli",matched_uri="/llm/hizli"} 5
apisix_bandwidth{type="egress",route="llm-danisma"} 4096
apisix_http_status{code="200",route="llm-danisma" 7
apisix_http_status{code="500",route="llm-danisma"} bu-sayi-degil
apisix_http_status{code="503"} 9
"""


def test_metrikler_rota_basina_toplanir(monkeypatch, tmp_path, sandbox_state):
    _kurulum(monkeypatch, tmp_path, prom=_PROM.encode())
    m = _client().get("/api/gateway").json()["metrikler"]

    assert m["kaynak_ok"] is True and m["neden"] is None
    assert m["rota_basina"]["llm-danisma"] == {"istek_n": 12, "durum_kirilimi": {"200": 10, "429": 2}}
    assert m["rota_basina"]["llm-hizli"] == {"istek_n": 5, "durum_kirilimi": {"200": 5}}


def test_bozuk_satir_sayilir_ilgisiz_satir_sayilmaz(monkeypatch, tmp_path, sandbox_state):
    """ÜÇ bozuk `apisix_http_status` satırı var (kapanmamış süslü parantez · sayı olmayan değer ·
    `route` etiketi YOK → hiçbir rotaya yazılamaz). `# HELP`/`# TYPE`/`apisix_bandwidth` ise
    BOZUK DEĞİL, İLGİSİZDİR — onları saymak sayacı gürültüye boğar ve alarmı işe yaramaz kılar."""
    _kurulum(monkeypatch, tmp_path, prom=_PROM.encode())
    m = _client().get("/api/gateway").json()["metrikler"]
    assert m["atlanan_satir"] == 3, f"atlanan satır sayımı yanlış: {m['atlanan_satir']}"


def test_nan_metrik_govdeyi_bozmaz(monkeypatch, tmp_path, sandbox_state):
    """`NaN`/`+Inf` toplamaya girerse rotanın `istek_n`i KOMPLE NaN olur ve `store.sanitize` onu
    `null`a çevirir — yani ÖLÇÜLMÜŞ sayaçlar da "ölçülemedi" diye görünür. Bozuk satır sınıfı."""
    prom = ('apisix_http_status{code="200",route="r"} NaN\n'
            'apisix_http_status{code="201",route="r"} +Inf\n'
            'apisix_http_status{code="202",route="r"} 3\n')
    _kurulum(monkeypatch, tmp_path, prom=prom.encode())
    r = _client().get("/api/gateway")
    assert r.status_code == 200, r.text
    assert "NaN" not in r.text and "Infinity" not in r.text
    m = r.json()["metrikler"]
    assert m["rota_basina"]["r"] == {"istek_n": 3, "durum_kirilimi": {"202": 3}}
    assert m["atlanan_satir"] == 2
    json.loads(r.text)          # sözleşme: gövde GEÇERLİ JSON


def test_bos_prometheus_govdesi_olculdu_sayilir(monkeypatch, tmp_path, sandbox_state):
    """Kapı ayakta ama hiç trafik geçmemişse: `kaynak_ok` DOĞRU, `rota_basina` BOŞ,
    `atlanan_satir` 0. Bu, erişilemezlik hâlinden (None) AYRI bir durumdur — üç-durum ayrımı
    UI'ın boş-durum bileşeninin dayanağıdır."""
    _kurulum(monkeypatch, tmp_path, prom=b"# HELP apisix_http_status codes\n")
    m = _client().get("/api/gateway").json()["metrikler"]
    assert m["kaynak_ok"] is True
    assert m["rota_basina"] == {}
    assert m["atlanan_satir"] == 0


# ---------------------------------------------------------------- F. ZAMAN AŞIMI

def test_her_dis_cagri_zaman_asimli(monkeypatch, tmp_path, sandbox_state):
    """Kapı SYN'i yutarsa varsayılan soket zaman aşımı SONSUZdur ve pano asılır."""
    casus = _kurulum(monkeypatch, tmp_path)
    _client().get("/api/gateway")

    assert len(casus.cagrilar) == 2, [c["url"] for c in casus.cagrilar]
    for c in casus.cagrilar:
        assert isinstance(c["timeout"], (int, float)), f"{c['url']}: zaman aşımı VERİLMEDİ"
        assert 0 < c["timeout"] <= 2.0, f"{c['url']}: zaman aşımı {c['timeout']} sn (tavan 2)"


def test_zaman_asimi_sabiti_beyanli():
    assert 0 < api.KAPI_ZAMAN_ASIMI_S <= 2.0


# ------------------------------------------------------------------- G. FAZLAR

def test_fazlar_plugin_imzasindan_turetilir(monkeypatch, tmp_path, sandbox_state):
    """Faz 1/2/3 canlı (routes.yaml'da `ai-proxy-multi` + `limit-count` + `limit-req` VAR),
    Faz 4 bekliyor. Sabit metin olsaydı Faz 2 indiği gün pano yalan söylemeye başlardı ve
    kimse fark etmezdi."""
    _kurulum(monkeypatch, tmp_path)
    f = _client().get("/api/gateway").json()["fazlar"]
    assert set(f) == {"faz1_llm", "faz2_fmp", "faz3_ingress", "faz4_filo"}, sorted(f)
    assert f["faz1_llm"] == "canli"
    assert f["faz2_fmp"] == "canli"  # 2026-09-01: fmp-veri rotası limit-count ile indi
    assert f["faz3_ingress"] == "canli"  # imza limit-req (2026-09-01: kapı basic-auth'u emekli — kimlik uygulama oturumunda)
    assert f["faz4_filo"] == "bekliyor"


def test_faz2_imzasi_dogunca_canli_olur(monkeypatch, tmp_path, sandbox_state):
    """TÜRETİMİN kendisi çivili: `limit-count` taşıyan bir rota doğduğu an Faz 2 canlıya döner."""
    rota = {"id": "fmp", "uri": "/fmp", "plugins": {"limit-count": {"count": 250}}}
    _kurulum(monkeypatch, tmp_path, admin=_admin_zarfi([rota]))
    f = _client().get("/api/gateway").json()["fazlar"]
    assert f["faz2_fmp"] == "canli"
    assert f["faz1_llm"] == "bekliyor"


def test_fazlar_olculemedigi_zaman_ucuncu_hal(monkeypatch, tmp_path, sandbox_state):
    """Admin okunamadığında faz "bekliyor" DEĞİLDİR — o bir ölçüm iddiasıdır. Üçüncü hâl şart."""
    _env_dosyasi(monkeypatch, tmp_path)
    casus = _Casus(**{"9180": OSError("yok"), "9091": OSError("yok")})
    monkeypatch.setattr(urllib.request, "urlopen", casus)
    f = _client().get("/api/gateway").json()["fazlar"]
    assert set(f.values()) == {"olculemedi"}, f


def test_faz_kanitlari_beyanli(monkeypatch, tmp_path, sandbox_state):
    """Her fazın hangi imzadan türetildiği GÖVDEDE yazılı — yoksa panodaki rozet sihirdir ve
    operatör 'bekliyor' rozetine neye dayanarak güveneceğini bilemez."""
    _kurulum(monkeypatch, tmp_path)
    g = _client().get("/api/gateway").json()
    assert set(g["fazlar_kanit"]) == set(g["fazlar"])
    for alan, aciklama in g["fazlar_kanit"].items():
        assert isinstance(aciklama, str) and len(aciklama) >= GEREKCE_ASGARI, alan
    assert len(g["fazlar_kapsam_neden"]) >= GEREKCE_ASGARI, \
        "fazların YALNIZ /routes'tan türediği (consumer_groups/ssl görünmez) beyan edilmemiş"


# ------------------------------------------------------- H. KAYNAK BEYANI + SÖZLEŞME

def test_kaynak_beyani_govdede(monkeypatch, tmp_path, sandbox_state):
    """Pano "kaynağı repo'da aç" bağını UYDURMAZ, gövdeden okur (tek-kaynak yasası)."""
    _kurulum(monkeypatch, tmp_path)
    k = _client().get("/api/gateway").json()["kaynak"]
    assert k["rota_kaynagi_repo"] == "deploy/apisix/routes.yaml"
    assert (REPO / k["rota_kaynagi_repo"]).exists(), "beyan edilen repo yolu diskte YOK"
    assert "9180" in k["admin_url"] and "9091" in k["prometheus_url"]
    assert k["zaman_asimi_s"] == api.KAPI_ZAMAN_ASIMI_S


def test_uc_state_defterine_yazmaz(monkeypatch, tmp_path, sandbox_state):
    """SALT-OKUNUR sözleşmesi: bu uç `state/` altına hiçbir şey yazmaz (pano 15 sn'de bir yokluyor
    — yazan bir uç canlı defteri kirletirdi)."""
    _kurulum(monkeypatch, tmp_path)
    once = sorted(p.name for p in sandbox_state.rglob("*"))
    _client().get("/api/gateway")
    assert sorted(p.name for p in sandbox_state.rglob("*")) == once
