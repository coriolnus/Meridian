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
  i. (TUR 2) HEAD = GET temsili (RFC 9110 §9.3.2): aynı `Accept-Encoding: gzip` ile HEAD ve GET
     aynı `Content-Encoding`/`ETag`/`Vary`/`Accept-Ranges`ı bildirir; HEAD `Content-Length`i ya
     yazmaz ya GET'inkine eşittir (§8.6). ÖLÇÜLDÜ (2026-09-25): bugün HEAD kabul eden TEK rota
     `/runbook`; statik varlıklar ve `/api/roadmap` `APIRoute` olduğu için HEAD'e 405 (`Allow: GET`)
     döner. Kuralın statik/JSON bacağı bu yüzden GERÇEK `_statik` ve `api_roadmap` gövdeleriyle
     HEAD'i de kabul eden küçük bir uygulamada ölçülür.
  a'. (TUR 2) Sıkıştırılmış tek-parça yanıtın `Content-Length`i teldeki gövdenin GERÇEK boyudur.

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
from starlette.responses import JSONResponse, Response
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


def _ham(c: TestClient, yol: str, basliklar: dict, yontem: str = "GET"):
    """Yanıt + TELDEKİ HAM gövde (httpx içerik açmasından ÖNCE)."""
    with c.stream(yontem, yol, headers=basliklar) as r:
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


# ============================ a' · Content-Length doğruluğu (tur 2) ============================

def _pano_js() -> str:
    """Manifestin beyan ettiği ilk `pano-*.js` yolu (hash'li ad derlemeye göre değişir)."""
    return "/" + sorted(a for a in api._pano_varliklari() if a.endswith(".js"))[0]


@pytest.mark.parametrize("yol", ["/api/roadmap", "/pano", "PANO_JS"])
def test_a_CONTENT_LENGTH_telden_gelen_sikistirilmis_govdenin_GERCEK_boyu(sandbox_state, monkeypatch, yol):
    """Tek parçalı yanıtta `Content-Length` = teldeki gzip baytları; akışta (>64 KB dosya) HİÇ yazılmaz
    (yanlış bir boy, uzunluğu bilinmeyen bir boydan kötüdür — istemci gövdeyi keser ya da bekler)."""
    akis = yol == "PANO_JS"
    yol = _pano_js() if akis else yol
    r, ham = _ham(_istemci(monkeypatch), yol, GZ)
    assert r.headers.get("content-encoding") == "gzip", f"ön koşul: {yol} sıkıştırılmadı"
    boy = r.headers.get("content-length")
    if akis:
        assert boy is None, f"akış yanıtı `Content-Length: {boy}` taşıyor"
    else:
        assert boy is not None and int(boy) == len(ham), (yol, boy, len(ham))


# ============================ i · HEAD = GET temsili (tur 2) ============================

TEMSIL = ("content-encoding", "etag", "vary", "accept-ranges")


def _head_mini() -> TestClient:
    """GERÇEK `_statik` (FileResponse + içerik-ETag) ve GERÇEK `api_roadmap` gövdesi, GET+HEAD
    kabul eden rotalarda, seçici gzip'in canlı ayarlarıyla sarılı. Canlı uygulamada bu iki yüzey
    HEAD'e 405 döndüğü için kuralın bu bacağı ancak burada ölçülebilir."""
    ad = _pano_js()[1:]

    async def statik(request):
        return api._statik(request, ad, "application/javascript")

    def roadmap(request):
        return JSONResponse(api.api_roadmap(request))

    uyg = Starlette(routes=[Route("/statik", statik, methods=["GET", "HEAD"]),
                            Route("/roadmap", roadmap, methods=["GET", "HEAD"])])
    return TestClient(api.SeciciGZipMiddleware(uyg, minimum_size=api.GZIP_ASGARI_BAYT,
                                               compresslevel=api.GZIP_SEVIYE))


@pytest.mark.parametrize("yol", ["/statik", "/roadmap"])
def test_i_HEAD_ve_GET_ayni_TEMSIL_basliklarini_bildirir(sandbox_state, monkeypatch, yol):
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    c = _head_mini()
    g = c.get(yol, headers=GZ)
    h, ham = _ham(c, yol, GZ, "HEAD")
    assert g.status_code == h.status_code == 200
    assert g.headers.get("content-encoding") == "gzip", "ön koşul: GET sıkıştırılmadı"
    for ad in TEMSIL:
        assert h.headers.get(ad) == g.headers.get(ad), f"{yol}: HEAD {ad}={h.headers.get(ad)!r} ≠ GET {g.headers.get(ad)!r}"
    boy = h.headers.get("content-length")
    assert boy is None or boy == g.headers.get("content-length"), (
        f"{yol}: HEAD `Content-Length: {boy}` GET'inkinden farklı (RFC 9110 §8.6)")


@pytest.mark.parametrize("yol", ["PANO_JS", "/app.js", "/api/roadmap"])
def test_i_CANLI_GET_rotalari_HEADe_ya_405_ya_ESIT_temsil(sandbox_state, monkeypatch, yol):
    """Canlı uygulamada bugün 405 dalı koşar (HEAD hiç temsil bildirmez → çelişki imkânsız). Bir gün
    bu rotalara HEAD eklenirse ikinci dal devreye girer ve eşitlik aynı çiviyle ölçülür."""
    yol = _pano_js() if yol == "PANO_JS" else yol
    c = _istemci(monkeypatch)
    g = c.get(yol, headers=GZ)
    h = c.head(yol, headers=GZ)
    if h.status_code == 405:
        assert "HEAD" not in h.headers.get("allow", ""), h.headers.get("allow")
        assert not any(ad in h.headers for ad in ("content-encoding", "etag", "accept-ranges"))
    else:
        for ad in TEMSIL:
            assert h.headers.get(ad) == g.headers.get(ad), f"{yol}: HEAD/GET {ad} ayrışıyor"


def test_i_CANLI_runbook_HEAD_GET_ile_ayni_TEMSILI_bildirir(sandbox_state, monkeypatch):
    """Canlıda HEAD kabul eden TEK rota. HEAD gövdeyi render ETMEZ ve boyu bilmez; gzip katmanı
    `Content-Length` yokluğunu "GET eşiğin üstünde" diye okur (varsayımın dayanağı aşağıdaki çivi)."""
    c = _istemci(monkeypatch)
    g = c.get("/runbook", headers=GZ)
    h, ham = _ham(c, "/runbook", GZ, "HEAD")
    assert g.status_code == h.status_code == 200
    assert g.headers.get("content-encoding") == "gzip", "ön koşul: GET /runbook sıkıştırılmadı"
    for ad in TEMSIL:
        assert h.headers.get(ad) == g.headers.get(ad), f"/runbook: HEAD {ad}={h.headers.get(ad)!r} ≠ GET {g.headers.get(ad)!r}"
    assert "content-length" not in h.headers, "HEAD GET'in boyunu bilmeden `Content-Length` yazıyor"
    assert ham == b"", "HEAD telde gövde yaydı"


def test_i_CANLI_runbook_HEAD_kimlik_isteginde_YANLIS_boy_yazmaz(sandbox_state, monkeypatch):
    """gzip istemeyen istemcide de HEAD, GET'in boyundan farklı bir `Content-Length` yazmaz (§8.6).
    Eskiden `0` yazıyordu; bu çivi o yanlış değerin geri gelmesini yakalar. (`Vary` burada
    karşılaştırılmaz: boy eşiğine bağlı geç karar — RFC 9110 §9.3.2'nin kendi örneği.)"""
    c = _istemci(monkeypatch)
    g = c.get("/runbook", headers=KIMLIK)
    h = c.head("/runbook", headers=KIMLIK)
    assert g.status_code == h.status_code == 200
    assert "content-encoding" not in g.headers and "content-encoding" not in h.headers
    boy = h.headers.get("content-length")
    assert boy is None or boy == g.headers.get("content-length"), f"HEAD yanlış boy yazdı: {boy}"


def test_i_runbook_GET_govdesi_HER_ZAMAN_esigin_ustunde():
    """`_head_temsili`nin `Content-Length`siz HEAD varsayımının dayanağı: GET gövdesi kabuğun
    kendisinden küçük olamaz (yer tutucular yalnız içerikle DEĞİŞİR, kabuk metni kalır)."""
    kabuk = (api.WEB / "runbook.html").read_bytes()
    assert len(kabuk) - sum(len(y) for y in api._RUNBOOK_YER_TUTUCU) >= api.GZIP_ASGARI_BAYT


def test_i_HEAD_304_GET_304_ile_ayni_ve_KODLAMASIZ(sandbox_state, monkeypatch):
    """Koşullu HEAD 304 alır; 304'e temsil kodlaması yazılmaz — GET 304 ile birebir."""
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    c = _head_mini()
    etiket = c.get("/statik", headers=GZ).headers["etag"]
    g = c.get("/statik", headers={**GZ, "If-None-Match": etiket})
    h = c.head("/statik", headers={**GZ, "If-None-Match": etiket})
    assert g.status_code == h.status_code == 304
    for ad in TEMSIL:
        assert h.headers.get(ad) == g.headers.get(ad), f"304: HEAD {ad}={h.headers.get(ad)!r} ≠ GET {g.headers.get(ad)!r}"
    assert "content-encoding" not in h.headers


def test_i_HEAD_esik_altindaki_dosyada_GET_gibi_KODLAMASIZ(tmp_path):
    """`Content-Length` eşik altındaysa GET sıkıştırılmaz; HEAD de kodlama/`Vary` bildirmez."""
    from starlette.responses import FileResponse
    kucuk = tmp_path / "kucuk.js"
    kucuk.write_bytes(b"x" * (api.GZIP_ASGARI_BAYT - 1))

    async def uc(request):
        return FileResponse(kucuk, media_type="application/javascript")

    uyg = Starlette(routes=[Route("/k", uc, methods=["GET", "HEAD"])])
    c = TestClient(api.SeciciGZipMiddleware(uyg, minimum_size=api.GZIP_ASGARI_BAYT,
                                            compresslevel=api.GZIP_SEVIYE))
    g = c.get("/k", headers=GZ)
    h = c.head("/k", headers=GZ)
    assert "content-encoding" not in g.headers, "ön koşul: eşik altı GET sıkıştırıldı"
    for ad in TEMSIL:
        assert h.headers.get(ad) == g.headers.get(ad), f"HEAD {ad}={h.headers.get(ad)!r} ≠ GET {g.headers.get(ad)!r}"
    assert h.headers.get("content-length") == g.headers.get("content-length")


def test_i_HEAD_KABUL_EDEN_ROTALAR_sabit_ve_BILINCLI():
    """Rol-1 ruling 2026-09-24 (TSK-219 tur 2 kaygı-2): gövdesiz HEAD'de gzip kararı `Content-Length`ten
    verilir; boyunu BİLDİRMEYEN bir HEAD rotasında GET'in sıkıştırılacağı VARSAYILIR (bugün tek örnek
    `/runbook`, kabuğu eşiğin çok üstünde). HEAD kabul eden yeni bir rota bu varsayımı sessizce yanlış
    yapabilir — küçük gövdeli bir rota HEAD'de gzip bildirirdi. Liste bu yüzden SABİTTİR: yeni HEAD rotası
    eklemek bu çiviyi kırar ve varsayımın o rotada doğru olup olmadığı bilinçli olarak sorulur."""
    head_rotalari = sorted(getattr(r, "path", "?") for r in api.app.routes
                           if "HEAD" in (getattr(r, "methods", None) or set()))
    assert head_rotalari == ["/runbook"], head_rotalari
