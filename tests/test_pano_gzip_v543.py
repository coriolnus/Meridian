"""v543 · PANO YANIT SIKIŞTIRMASI (TSK-219, 2026-09-25) — uygulama katmanında seçici gzip.

ÖLÇÜLEN BOŞLUK (Rol-1, 2026-09-24): pano APISIX → uvicorn zincirinin HİÇBİR katmanında sıkıştırma
yoktu. `/api/roadmap` 774 KB, `pano-*.js` 2,14 MB telden ham geçiyordu; gzip-6 ile 191 KB / 606 KB.

BU DOSYA NEYİ ÇİVİLER (brief maddeleri a–g + yığın konumu):
  a. `Accept-Encoding: gzip` → `Content-Encoding: gzip` + `Vary: Accept-Encoding`; TELDEKİ ham
     baytlar açıldığında sıkıştırmasız gövdeyle BAYT-EŞİT (httpx'in otomatik açması atlanır —
     yoksa "açılmış gövde eşit" testi sıkıştırma hiç olmasa da yeşil kalırdı).
  b. Başlıksız / `identity` / yalnız `br` isteyen istemci → kodlama YOK.
  c. Güvenlik başlıkları (`GUVENLIK_BASLIKLARI`) sıkıştırılmış yanıtta sıkıştırmasızla AYNI.
  d. BREACH hariç tutması (yol-bazlı) + zaten-sıkıştırılmış türler + 206 kısmi yanıt SIKIŞTIRILMAZ.
  e. Statik varlığın 304 yolu DEĞİŞMEDİ; sıkıştırılmış temsil ZAYIF ETag taşır (RFC 9110 §8.8.3:
     farklı içerik kodlaması farklı temsildir, güçlü etiket paylaşılamaz) ve `Accept-Ranges`
     taşımaz (anında üretilen gzip temsili bayt aralığı sunamaz).
  f. `GZIP_ASGARI_BAYT` altındaki gövde sıkıştırılmaz.
  g. Kayan oturum çerezi sıkıştırılmış yanıtta da tazelenir.
  h. Yığın konumu: seçici gzip kullanıcı ara katmanlarının EN İÇİNDEDİR (gerekçe `api.py`deki
     sıkıştırma bloğunda).

BOŞ-YEŞİL KORUMASI: her "sıkıştırılmaz" iddiasının yanında ya gövdenin eşiğin ÜSTÜNDE olduğu ön
koşulu ya da aynı düzenekte sıkıştırmanın GERÇEKTEN olduğu bir kontrol isteği durur — eşik altı
bir gövdeyle "sıkıştırılmadı" demek hiçbir şey ölçmez.
"""
from __future__ import annotations

import gzip
import time

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

from meridian import api, auth

GZ = {"Accept-Encoding": "gzip"}
KIMLIK = {"Accept-Encoding": "identity"}
PAROLA = "cok-uzun-ve-guclu-parola-543"
#: Eşiğin çok üstünde, iyi sıkışan bir gövde (mekanizma testleri için).
BUYUK = ("sir-benzeri gövde, yansıtılan girdi " * 300).encode("utf-8")


def _istemci(monkeypatch) -> TestClient:
    """`with` KULLANILMAZ (lifespan `_autostart`ı koşturur); betik jetonu kapalı → `_auth` açık."""
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _ham(c: TestClient, yol: str, basliklar: dict):
    """Yanıt + TELDEKİ HAM gövde (httpx içerik açmasından ÖNCE)."""
    with c.stream("GET", yol, headers=basliklar) as r:
        return r, b"".join(r.iter_raw())


def _mini(tur: str, govde: bytes = BUYUK) -> TestClient:
    """Seçici gzip'i canlı ayarlarıyla saran, her yola aynı gövdeyi dönen küçük uygulama."""
    async def uc(request):
        return Response(govde, media_type=tur)

    uyg = Starlette(routes=[Route("/{yol:path}", uc)])
    return TestClient(api.SeciciGZipMiddleware(uyg, minimum_size=api.GZIP_ASGARI_BAYT,
                                               compresslevel=api.GZIP_SEVIYE))


# ============================ a · sıkıştırma + bayt eşitliği ============================

def test_a_roadmap_gzip_ile_sikisir_ve_acilan_govde_BAYT_ESIT(sandbox_state, monkeypatch):
    c = _istemci(monkeypatch)
    duz = c.get("/api/roadmap", headers=KIMLIK)
    assert duz.status_code == 200 and "content-encoding" not in duz.headers
    r, ham = _ham(c, "/api/roadmap", GZ)
    assert r.status_code == 200
    assert r.headers.get("content-encoding") == "gzip", "gzip isteyen istemciye sıkıştırma yok"
    assert "accept-encoding" in r.headers.get("vary", "").lower(), (
        "sıkıştırılmış yanıtta `Vary: Accept-Encoding` yok — ara önbellek gzip'i gzip "
        "istemeyen istemciye verebilir")
    assert gzip.decompress(ham) == duz.content, "açılan gövde sıkıştırmasız gövdeyle bayt-eşit değil"
    # Ölçüm 774 KB → ~191 KB (~%25); yarı eşiği "gerçekten sıkıştı mı" sorusunun gevşek alt sınırı.
    assert len(ham) < len(duz.content) // 2, (len(ham), len(duz.content))


def test_a_sikistirmasiz_buyuk_yanit_da_VARY_tasir(sandbox_state, monkeypatch):
    """Önbellek anlamı iki yönlüdür: sıkıştırmasız temsil de `Accept-Encoding`e göre değişir."""
    r = _istemci(monkeypatch).get("/api/roadmap", headers=KIMLIK)
    assert "accept-encoding" in r.headers.get("vary", "").lower()


# ============================ b · başlıksız istek ============================

def test_b_ACCEPT_ENCODING_basligi_hic_yoksa_kodlama_yok(sandbox_state, monkeypatch):
    c = _istemci(monkeypatch)
    del c.headers["accept-encoding"]                     # httpx varsayılanı `gzip, deflate`
    r, ham = _ham(c, "/api/roadmap", {})
    assert "accept-encoding" not in r.request.headers, "ön koşul: istek gerçekten başlıksız değil"
    assert "content-encoding" not in r.headers
    assert ham[:1] == b"{", "başlıksız istemciye gövde düz JSON olarak gitmedi"


@pytest.mark.parametrize("deger", ["identity", "br", "deflate"])
def test_b_gzip_istemeyen_istemciye_kodlama_yok(sandbox_state, monkeypatch, deger):
    r, ham = _ham(_istemci(monkeypatch), "/api/roadmap", {"Accept-Encoding": deger})
    assert "content-encoding" not in r.headers, deger
    assert ham[:1] == b"{"


# ============================ c · güvenlik başlıkları ============================

@pytest.mark.parametrize("yol", ["/api/roadmap", "/app.js", "/pano"])
def test_c_guvenlik_basliklari_SIKISTIRILMIS_yanitta_AYNEN(sandbox_state, monkeypatch, yol):
    c = _istemci(monkeypatch)
    duz = c.get(yol, headers=KIMLIK)
    gz = c.get(yol, headers=GZ)
    assert gz.headers.get("content-encoding") == "gzip", f"ön koşul: {yol} sıkıştırılmadı"
    assert "content-encoding" not in duz.headers
    for ad, deger in api.GUVENLIK_BASLIKLARI.items():
        assert gz.headers.get_list(ad) == [deger], f"{yol}: sıkıştırılmış yanıtta {ad} bozuk"
        assert duz.headers.get_list(ad) == [deger], f"{yol}: sıkıştırmasız yanıtta {ad} bozuk"


# ============================ d · hariç tutmalar ============================

#: KAYNAKTAN BAĞIMSIZ literal (bilinçli ikinci kopya, yalnız ALT KÜME yönünde): kaynağa yeni hariç
#: yol eklemek bu testi değiştirmeyi gerektirmez, ama buradaki bir yolu kaynaktan SESSİZCE düşürmek
#: kırmızıdır. Parametre kaynaktan alınsaydı silinen yol testten de sessizce düşerdi.
BREACH_HARIC = ("/api/login", "/api/logout", "/api/session", "/api/setup-password",
                "/api/secrets", "/api/debug_export", "/api/hermes/pool_key")


def test_d_BREACH_listesi_kaynakta_EKSIKSIZ():
    eksik = set(BREACH_HARIC) - set(api.GZIP_HARIC_YOLLAR)
    assert not eksik, f"BREACH hariç kümesinden yol düşmüş: {sorted(eksik)}"


@pytest.mark.parametrize("onek", BREACH_HARIC)
def test_d_BREACH_haric_yol_ve_alt_yollari_SIKISTIRILMAZ(onek):
    c = _mini("application/json")
    for yol in (onek, onek + "/alt"):
        r = c.get(yol, headers=GZ)
        assert "content-encoding" not in r.headers, f"BREACH hariç yolu sıkıştırıldı: {yol}"
        assert r.content == BUYUK
    kontrol = c.get("/api/roadmap", headers=GZ)
    assert kontrol.headers.get("content-encoding") == "gzip", "kontrol: düzenek hiç sıkıştırmıyor"


def test_d_CANLI_uygulamada_sir_ucu_SIKISTIRILMAZ(sandbox_state, monkeypatch):
    """Tel (kablolama) bacağı: gerçek uygulamada `/api/secrets` (maskeli anahtar ipuçları)."""
    r = _istemci(monkeypatch).get("/api/secrets", headers=GZ)
    assert r.status_code == 200
    assert len(r.content) >= api.GZIP_ASGARI_BAYT, "ön koşul: gövde eşik altında, test boş-yeşil olur"
    assert "content-encoding" not in r.headers, "sır uç ailesi sıkıştırıldı (BREACH)"


def test_d_CANLI_uygulamada_debug_export_SIKISTIRILMAZ(sandbox_state, monkeypatch):
    r = _istemci(monkeypatch).get("/api/debug_export", headers=GZ)
    assert r.status_code == 200 and len(r.content) >= api.GZIP_ASGARI_BAYT
    assert "content-encoding" not in r.headers


@pytest.mark.parametrize("tur", ["application/zip", "application/gzip", "font/woff2",
                                 "image/png", "image/svg+xml"])
def test_d_zaten_sikistirilmis_turler_YENIDEN_sikistirilmaz(tur):
    c = _mini(tur)
    r = c.get("/herhangi", headers=GZ)
    assert "content-encoding" not in r.headers, f"{tur} yeniden sıkıştırıldı"
    assert r.content == BUYUK


@pytest.mark.parametrize("tur", ["application/json", "text/html; charset=utf-8",
                                 "application/javascript", "text/css", "text/csv"])
def test_d_metin_turleri_SIKISTIRILIR(tur):
    """Kontrol: tür süzgeci metni de yutmuyor (aşırı hariç tutma da bir arızadır)."""
    r = _mini(tur).get("/herhangi", headers=GZ)
    assert r.headers.get("content-encoding") == "gzip", tur
    assert r.content == BUYUK


@pytest.mark.parametrize("yol", ["/fonts/inter-vf.woff2", "/favicon.svg"])
def test_d_CANLI_ikili_statik_varliklar_SIKISTIRILMAZ(monkeypatch, yol):
    r = _istemci(monkeypatch).get(yol, headers=GZ)
    assert r.status_code == 200 and len(r.content) >= api.GZIP_ASGARI_BAYT
    assert "content-encoding" not in r.headers


def test_d_KISMI_yanit_206_SIKISTIRILMAZ(monkeypatch):
    """206'nın `Content-Range`i SIKIŞTIRMASIZ baytları sayar; gövdeyi gzip'lemek aralığı yalan yapar."""
    dosya = (api.WEB / "app.js").read_bytes()
    r, ham = _ham(_istemci(monkeypatch), "/app.js", {**GZ, "Range": "bytes=0-4095"})
    assert r.status_code == 206, "ön koşul: aralık isteği 206 almadı"
    assert "content-encoding" not in r.headers, "206 kısmi yanıt sıkıştırıldı"
    assert ham == dosya[:4096]


# ============================ e · ETag / 304 ============================

def test_e_statik_varlik_304_yolu_DEGISMEDI_ve_gzip_temsili_ZAYIF_etiketli(monkeypatch):
    c = _istemci(monkeypatch)
    ad = sorted(a for a in api._pano_varliklari() if a.endswith(".js"))[0]
    yol, dosya = "/" + ad, (api.WEB / ad).read_bytes()
    guclu = api._icerik_etag(api.WEB / ad)
    assert guclu and guclu.startswith('"')

    duz = c.get(yol, headers=KIMLIK)
    assert duz.headers.get("etag") == guclu, "sıkıştırmasız temsilin güçlü etiketi değişti"
    assert duz.headers.get("accept-ranges") == "bytes"

    r, ham = _ham(c, yol, GZ)
    assert r.headers.get("content-encoding") == "gzip"
    assert gzip.decompress(ham) == dosya
    assert r.headers.get("etag") == "W/" + guclu, (
        "gzip temsili güçlü etiketi sıkıştırmasızla paylaşıyor (RFC 9110 §8.8.3)")
    assert "accept-ranges" not in r.headers, "anında sıkıştırılan temsil aralık sunamaz"

    # 304 YOLU DEĞİŞMEDİ: tarayıcı hangi etiketi saklamışsa onu geri yollar; ikisi de 304 alır.
    for inm in (r.headers["etag"], guclu):
        y = c.get(yol, headers={**GZ, "If-None-Match": inm})
        assert y.status_code == 304, f"If-None-Match {inm} → {y.status_code}"
        assert y.content == b""
        assert "content-length" not in y.headers and "content-encoding" not in y.headers
        assert y.headers.get("etag") == guclu
    yanlis = c.get(yol, headers={**GZ, "If-None-Match": '"boyle-bir-etiket-yok"'})
    assert yanlis.status_code == 200 and yanlis.content == dosya


# ============================ f · asgari boyut ============================

def test_f_esik_altindaki_gercek_yanit_SIKISTIRILMAZ(sandbox_state, monkeypatch):
    """`/healthz` (~90 B) — BREACH kümesinde OLMAYAN bir uç seçildi: `/api/session` gibi hariç bir
    uç eşik kuralını ölçmez, çünkü o yol sıkıştırmaya hiç girmez (mutasyonla görüldü). Durum kodu
    sandbox'ta 503 olabilir (bayat nabız) — sıkıştırma kararı koddan bağımsızdır."""
    yol = "/healthz"
    assert not api._gzip_haric_yol(yol), "ön koşul: yol BREACH kümesinde, test eşiği ölçmez"
    r = _istemci(monkeypatch).get(yol, headers=GZ)
    assert 0 < len(r.content) < api.GZIP_ASGARI_BAYT
    assert "content-encoding" not in r.headers


def test_f_esik_SINIRI_bir_bayt_altı_sikismaz_esigin_kendisi_sikisir():
    alti = _mini("application/json", b"a" * (api.GZIP_ASGARI_BAYT - 1)).get("/x", headers=GZ)
    tam = _mini("application/json", b"a" * api.GZIP_ASGARI_BAYT).get("/x", headers=GZ)
    assert "content-encoding" not in alti.headers
    assert tam.headers.get("content-encoding") == "gzip"


# ============================ g · kayan oturum ============================

def test_g_oturum_cerezi_SIKISTIRILMIS_yanitta_da_tazelenir(sandbox_state, monkeypatch):
    auth.set_password(PAROLA)
    simdi = int(time.time())
    iat = simdi - 7 * 3600                                # yarı-ömrü geçmiş → tazelenmeli
    eski = auth._sign(iat + 12 * 3600, iat)
    c = _istemci(monkeypatch)
    r = c.get("/api/roadmap", headers={**GZ, "cookie": f"{auth.COOKIE_NAME}={eski}"})
    assert r.status_code == 200
    assert r.headers.get("content-encoding") == "gzip", "ön koşul: yanıt sıkıştırılmadı"
    ck = [v for v in r.headers.get_list("set-cookie") if v.startswith(auth.COOKIE_NAME + "=")]
    assert len(ck) == 1, f"sıkıştırılmış yanıtta oturum çerezi tazelenmedi: {ck}"
    assert "httponly" in ck[0].lower() and "samesite=strict" in ck[0].lower()
    assert auth.verify_session(ck[0].split(";")[0].split("=", 1)[1]) is True


# ============================ h · yığın konumu ============================

def test_h_secici_gzip_kullanici_yigininin_EN_ICINDE_ve_TEK():
    kayit = api.app.user_middleware
    gz = [m for m in kayit if m.cls is api.SeciciGZipMiddleware]
    assert len(gz) == 1, "seçici gzip ya yok ya iki kez eklenmiş"
    assert kayit[-1].cls is api.SeciciGZipMiddleware, (
        "seçici gzip en içte değil: " + " → ".join(m.cls.__name__ for m in kayit))
    assert gz[0].kwargs == {"minimum_size": api.GZIP_ASGARI_BAYT, "compresslevel": api.GZIP_SEVIYE}
