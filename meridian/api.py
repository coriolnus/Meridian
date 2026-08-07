"""api.py — FastAPI read-model over state/ + a tiny write surface (HALT / resume / approvals).
The dashboard NEVER talks to the broker directly; it reads state and posts operator intents.
Single-operator: reach it over an IAP tunnel (no inbound firewall on the VM). Optional shared-token
gate for local use. Research system. Paper mode. Not financial advice."""
from __future__ import annotations
import functools
import hmac
import html
import inspect
import json
import os
import re
import time as _time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

from . import auth

from . import store, storage, config, analytics, health, memory, obs, secrets as secrets_mod

def _auth_posture_check() -> None:
    """Açılışta yetki duruşunu DÜRÜSTÇE bildir (2026-07-22, yetki denetimi F2+F3).

    İki sessiz tuzak vardı:
      * Token ASCII-DIŞI ise HTTP başlığında hiç GÖNDERİLEMEZ — yani token "ayarlı" görünür ama
        operatör asla kimlik doğrulayamaz. Sevkiyat şablonu tam böyle bir değer koyuyordu.
      * Token HİÇ ayarlı değilse `_auth` bir no-op'tur: hesap durumu ve HALT/onay yazma yüzeyi ile
        çağıran arasında duran TEK şey `--host 127.0.0.1` bağlanmasıdır. Bugün o bağlanma doğru,
        ama tek noktaya bağlı bir savunma, savunma derinliği DEĞİLDİR — ve sessizse hiç yoktur.
    """
    if DASH_TOKEN:
        try:
            DASH_TOKEN.encode("ascii")
        except UnicodeEncodeError:
            obs.alarm("DATA_QUALITY",
                      "MERIDIAN_DASH_TOKEN ASCII-DIŞI: HTTP başlığında gönderilemez, yani pano "
                      "kimlik doğrulaması FİİLEN İMKÂNSIZ. ASCII bir token ile değiştir.",
                      detail="api._auth")
    else:
        obs.warn("dashboard_token_unset",
                 detail="tek koruma loopback bağlanması (127.0.0.1). Uzak/tünel erişimi açılacaksa "
                        "MERIDIAN_DASH_TOKEN ZORUNLU — aksi halde hesap durumu ve HALT yüzeyi yetkisiz açık.")

    # ---- GENEL ARAYÜZE PAROLASIZ AÇILMA: BAŞLATMAYI REDDET (2026-07-28) ----------------------
    # Yukarıdaki uyarı bir UYARIYDI ve uyarılar okunmaz. Oracle Cloud dağıtımı öncesi bu, sessiz
    # bir felaket yoluydu: operatör `--host 0.0.0.0` verir, `obs.warn` state'e düşer, kimse
    # bakmaz, ve hesap durumu + HALT/Flatten yüzeyi internete açılır.
    #
    # Kural: loopback DIŞINDA bir arayüze bağlanılıyorsa parola KURULU olmalı. Kurulu değilse
    # süreç açılmaz. Bu bir kolaylık kaybı değil — parolayı kurmak tek komut, ve alternatifi
    # yetkisiz bir broker denetim yüzeyi.
    #
    # HAYALET BAYRAK KALDIRILDI (K1, 2026-07-30): burada bir zamanlar "MERIDIAN_TRUST_PROXY=1 kaçış
    # kapısı BİLİNÇLİ olarak dar" yazıyordu. O bayrağı HİÇBİR KOD OKUMUYORDU — repo genelinde
    # (py/sh/md/yml/service/plist) tek geçtiği yer bu yorum satırıydı. Yani güvenlik duruşu
    # yorumunda var olmayan bir mekanizma anlatılıyordu ve bayrağı veren operatör hiçbir davranış
    # değişikliği görmezdi. Kaçış kapısı YOK ve olmasına gerek de yok: TLS sonlandıran bir vekil
    # kullanan operatör panoyu 127.0.0.1'de bırakır, o durumda zaten loopback'tedir ve bu kural
    # hiç tetiklenmez. Gerçekten bir kaçış kapısı gerekirse OKUNAN bir bayrak olarak eklenir —
    # güvenlik duruşu yorumla değil kodla gevşetilir.
    # TEK KAYNAK — OKUNAN DEĞER ARTIK GERÇEKTEN BAĞLANILAN ADRESTİR (denetim C1, 2026-08-02).
    # KUSUR NEYDİ: bu kapı `MERIDIAN_BIND_HOST`u okuyordu ama onu HİÇBİR başlatıcı YAZMIYORDU —
    # gerçek bağ her yerde `--host 127.0.0.1` sabitiydi. Kapının var olma nedeni olan TEK
    # senaryoda (operatör panoyu dışarı açmak için komut satırını elle `--host 0.0.0.0` yapar)
    # değişken boş kalır, `public_bind=False` olur ve ne aşağıdaki `RuntimeError` ne satır
    # 76'daki uyarı ateşlenirdi. Bu, 8 satır yukarıda kaldırılan HAYALET BAYRAK sınıfının bir
    # derece hafif hâliydi: TRUST_PROXY'yi SIFIR kod okuyordu, bunu İKİ yer okuyor (burası ve
    # auth_cli.status) ama SIFIR yer üretiyordu — ve okunan değer korunan olguyu belirlemiyordu.
    # DÜZELTME BAŞLATICIDADIR, BURADA DEĞİL: kapı mantığı BİT-BİT AYNI. Değişen, `--host`un artık
    # bu değişkenden gelmesi:
    #   * serve.sh          → `export MERIDIAN_BIND_HOST="${MERIDIAN_BIND_HOST:-127.0.0.1}"` +
    #                         uvicorn'a `os.environ['MERIDIAN_BIND_HOST']`
    #   * meridian.service  → `Environment=MERIDIAN_BIND_HOST=127.0.0.1` + `--host ${MERIDIAN_BIND_HOST}`
    # Yani panoyu dışarı açmanın DESTEKLENEN yolu artık kapıyı da kuruyor.
    # HÂLÂ KABLOLANMAMIŞ OLANLAR (uydurma yasağı — "tüm başlatıcılar" demiyoruz): docker-compose.yml,
    # Dockerfile, ops/com.meridian.agent.plist ve README.md örneği `--host 127.0.0.1` SABİTİDİR.
    # Hepsi loopback olduğu için bugün fiilî açık YOK, ama o yollarda değişken hâlâ bir BEYANdır,
    # bağ değil; ve elle `--host 0.0.0.0` yazan bir çağrı bu kapıyı yine atlar (kapı bağ adresini
    # ölçmez, beyan edileni okur). TERS YÖN FAIL-CLOSED: değişken 0.0.0.0 iken başlatıcı
    # loopback'te kalırsa süreç parolasız AÇILMAZ — yanlış alarm, ama muhafazakâr taraf.
    host = os.environ.get("MERIDIAN_BIND_HOST", "127.0.0.1")
    public_bind = host not in ("127.0.0.1", "localhost", "::1")
    if public_bind and not auth.password_set():
        raise RuntimeError(
            "GÜVENLİK: pano loopback DIŞINDA bir arayüze bağlanıyor (%s) ama operatör parolası "
            "kurulu değil. Hesap durumu, HALT/DEVAM ve Flatten yüzeyi yetkisiz açık olurdu.\n"
            "Çözüm: `.venv/bin/python -m meridian.auth_cli set` ile parolayı kur, sonra tekrar başlat.\n"
            "Tercih edilen dağıtım: panoyu 127.0.0.1'de bırak, TLS'i ters vekile yaptır "
            "(bkz. deploy/README-oracle.md)." % host)
    if public_bind:
        obs.warn("public_bind", detail=f"host={host} — TLS'in ters vekilde sonlandığından emin ol")


@asynccontextmanager
async def _lifespan(_app):
    """Açılışta süpervizör/zamanlayıcı/Hermes'i ayağa kaldır (yerel çalıştırmada serve.sh bayrakları).
    `@app.on_event("startup")` FastAPI'de kullanımdan kalktı ve her test koşusunda DeprecationWarning
    basıyordu — gürültü, gerçek uyarıları gizler (2026-07-22). Davranış birebir aynı."""
    _auth_posture_check()
    _autostart()
    yield


app = FastAPI(title="Meridian", docs_url=None, redoc_url=None, lifespan=_lifespan)


# ---- SERİLEŞTİRME SİGORTASI (2026-07-26) --------------------------------------------------------
# Tarihçe: OOS kapısı `cand > inc + marj`ı numpy değerleri üzerinde hesaplıyordu, yani `passes` bir
# `numpy.bool_`tü. /api/hermes onu serileştirmeye kalkınca uç HTTP 500 verdi ve Hermes sayfası
# tamamen öldü (anlatı: tests/test_api_contract.py). O VAKA kaynağında düzeltildi; ama SINIF açık
# kaldı — API'nin canlı-hesaplanan her yeni dönüşü aynı tuzağa yeniden düşebilir ve düştüğünde yine
# sessizce, yalnız BAŞARISIZ dalda görünür. Yazım yolu zaten korunuyordu (store.write_json →
# store.sanitize); korunmayan tek yüzey uçların canlı-hesap dönüşleriydi. Sigorta buraya konur.
class _NativeRoute(APIRoute):
    """Uç dönüşünü `store.sanitize`den geçiren rota sınıfı: numpy tipleri ve NaN/±Inf telden çıkamaz.

    NEDEN ROTA KATMANI, `response_class` DEĞİL: FastAPI önce `jsonable_encoder`ı çalıştırır, sonra
    yanıt sınıfının `render`ı gövdeyi yazar. Sarıcı rota katmanındayken encoder uç dönüşünü ZATEN
    temizlenmiş görür. `response_class` katmanı ise ancak encoder işini BİTİRDİKTEN sonra devreye
    girer — numpy'de patlayan şey encoder'ın kendisidir, yani o katman kaçınılmaz olarak GEÇ kalır.

    NEDEN `store.sanitize` (ikinci bir tanım değil): aynı yasanın iki kaynağı, zamanla AYRIŞAN iki
    yasa demektir — bu depodaki baskın hata deseni. Diskteki gerçek ile telden geçen gerçek aynı
    fonksiyondan çıkmalı; biri NaN'ı None yapıp diğeri yapmazsa pano ile dosya çelişir.

    dict/list DIŞINDAKİ dönüşler — düz `str` gövdeler ve `HTMLResponse`/`FileResponse`/
    `PlainTextResponse`/`JSONResponse` nesneleri — sanitize'ın mevcut fall-through'undan aynen
    geçer; ayrıca bir tip kontrolü GEREKMEZ.
    """

    def __init__(self, path: str, endpoint, **kwargs):
        if inspect.iscoroutinefunction(endpoint):
            @functools.wraps(endpoint)
            async def _sarili(*a, **k):
                return store.sanitize(await endpoint(*a, **k))
        else:
            @functools.wraps(endpoint)
            def _sarili(*a, **k):
                return store.sanitize(endpoint(*a, **k))
        # `functools.wraps` `__wrapped__` kurar; FastAPI bağımlılıkları `inspect.signature` ile
        # çözer ve o da `__wrapped__`i izler — yani `request: Request` gibi parametreler sarıcının
        # ardından ORİJİNAL imzadan çözülmeye devam eder (fastapi 0.139.0'da doğrulandı).
        super().__init__(path, _sarili, **kwargs)


# ROTA SINIFI İLK `@app.get`TEN ÖNCE ATANIR: `add_api_route` sınıfı KAYIT ANINDA okur, sonradan
# atamak daha önce kaydedilmiş rotaları kapsamaz (yani sigorta sessizce yarım takılırdı).
app.router.route_class = _NativeRoute

WEB = Path(__file__).resolve().parent / "web"

# ---- PANO TOKEN'I: systemd CREDENTIAL KANALI → ORTAM KANALI (WP-H/H3 tur-3, 2026-08-03) ---------
CRED_DOSYA_ADI = "dash_token"  # `LoadCredential=dash_token:/etc/meridian/dash_token` ile aynı ad


def _read_dash_token() -> str | None:
    """Pano token'ını ÖNCE systemd credential dizininden, YOKSA ortamdan okur.

    NEDEN İKİ KANAL (ve neden credential ÖNCE): `MERIDIAN_DASH_TOKEN` bugün süreç ORTAMINDA
    duruyor, ve bu depoda ortam çocuklara AKAR — `serve.sh` uvicorn'u `env=os.environ` ile,
    `hermes_composite` ajan alt süreçlerini devralınan ortamla doğurur. Yani token, pano
    sürecinin VE her LLM ajan sürecinin `/proc/<pid>/environ`ında okunur hâlde. systemd'nin
    `LoadCredential=`i sırrı ortama HİÇ koymaz: PID 1 olarak (sandbox'tan ÖNCE) okur,
    `$CREDENTIALS_DIRECTORY` altına 0400 bir tmpfs dosyası bırakır, süreç bitince siler.
    Gerekçenin tamamı: deploy/oracle-a1/meridian.service.d/50-dash-credential.conf.

    İKİ KANAL AYNI ANDA CANLI OLABİLİR (geçişin faz 1'i) — o hâlde credential KAZANIR, çünkü
    geçişin yönü ortamdan credential'a doğrudur; tersi, faz 2'de ortam kanalı kapandığında
    davranışın SESSİZCE değişmesi demek olurdu.

    BİÇİM TOLERANSI: credential kaynağı sözleşmede ÇIPLAK değerdir (`LoadCredential` dosyanın
    TAMAMINI değer olarak taşır), ama operatörün `.dash.env` alışkanlığı `MERIDIAN_DASH_TOKEN=...`
    biçimidir ve o dosyanın credential yoluna kopyalanması ÖNGÖRÜLEBİLİR bir kaza. Önek sessizce
    yutulmaz, TANINIR: aksi hâlde token "ayarlı" görünür, kimlik doğrulaması hep 401 döner ve
    operatör arızayı ağda arar. Aynı hoşgörü `dash_token_credential.sh::_token_oku`da da var —
    iki taraf aynı biçimi kabul eder.

    HİÇBİRİ YOKSA `None`: mevcut zorunlu-token kapısı (`_auth_posture_check` uyarısı ve
    `_auth`ın no-op dalı) BİREBİR korunur. Bu okuyucu bir kanal ekler, bir yasa değiştirmez.
    """
    kdir = os.environ.get("CREDENTIALS_DIRECTORY")
    if kdir:
        try:
            ham = (Path(kdir) / CRED_DOSYA_ADI).read_text(encoding="utf-8")
        # Kanal GERÇEKTEN zorunluyken sessiz kalmayan yer systemd'nin KENDİSİDİR: `LoadCredential=`
        # kaynak dosyası yoksa birim HİÇ başlamaz. Yani buradaki sessizlik bir arızayı gizlemez —
        # gizleyebileceği tek durum "bu kurulumda credential kanalı yok"tur, ve onun doğru yanıtı
        # zaten ortam kanalına düşmektir.
        # sessiz-yutma: credential kanalı isteğe bağlı — dosya-yok/izin/kodlama hatası "bu kurulumda o kanal yok" demektir, ortama düşmek bugünkü davranışı birebir korur
        except (OSError, ValueError):
            ham = ""
        # ÖNCE `strip()` SONRA ilk satır: `LoadCredential` dosyanın TAMAMINI taşır, sondaki yeni
        # satır serbesttir (kaynağı `printf '%s\n'` yazıyor) — kırpılmazsa token'a görünmez bir
        # `\n` yapışır ve `hmac.compare_digest` hep yanlış döner (en sinsi "ayarlı ama çalışmıyor").
        satirlar = ham.strip().splitlines()
        deger = satirlar[0].strip() if satirlar else ""
        if deger.startswith("MERIDIAN_DASH_TOKEN="):
            deger = deger[len("MERIDIAN_DASH_TOKEN="):].strip()
        if deger:
            return deger
    return os.environ.get("MERIDIAN_DASH_TOKEN")


DASH_TOKEN = _read_dash_token()  # required to reach the API over a network origin

# Cross-origin access — OFF unless MERIDIAN_CORS_ORIGINS is set (comma-separated origins, or "*"). Lets a
# frontend on ANOTHER origin (e.g. a local dashboard) call this agent's API. Only meaningful with a token.
_CORS = [o.strip() for o in os.environ.get("MERIDIAN_CORS_ORIGINS", "").split(",") if o.strip()]
if _CORS:
    app.add_middleware(CORSMiddleware, allow_origins=_CORS, allow_credentials=False,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["x-meridian-token", "content-type"])
    if not DASH_TOKEN:
        obs.warn("cors_without_token",
                 detail="CORS enabled but MERIDIAN_DASH_TOKEN unset — API is cross-origin AND unauthenticated")


# ---- GÜVENLİK BAŞLIKLARI — UYGULAMA KATMANI (v203, 2026-08-07) --------------------------------
# ÖLÇÜLEN BOŞLUK, varsayılan DEĞİL. Canlı A1'de `curl -D- http://127.0.0.1:8080/` HİÇBİR güvenlik
# başlığı döndürmüyordu: ne `Content-Security-Policy`, ne `X-Frame-Options`, ne
# `X-Content-Type-Options`. Sebep tek cümlede: bu başlıklar YALNIZ `deploy/Caddyfile`'da tanımlıydı
# ve **A1'de Caddy koşmuyor** (`systemctl is-active caddy` → inactive; `/etc/caddy/Caddyfile` yok).
# Yani depo boyunca "CSP-self yasası" diye anılan — ve ÜÇ ayrı test dosyasının (test_web_csp_uyum,
# test_yazitipi_v201, test_font_rotasi_v202) gerekçesini dayadığı — şey üretimde hiçbir başlıkla
# ZORLANMIYORDU. Testler doğruydu; yasa yoktu. Bu deponun en sık kusur sınıfı: kurulu ≠ çalışır.
#
# NEDEN UYGULAMA KATMANI TEK KAYNAK (ve vekil değil): ters vekil bir DAĞITIM TERCİHİDİR — bugün
# yok, yarın Caddy olur, öbür gün nginx ya da bir yük dengeleyici olur. Uygulamanın güvenlik
# duruşu o tercihten BAĞIMSIZ olmalı: başlığı uygulamanın kendisi yazarsa loopback'ten, SSH
# tünelinden, docker-compose'tan, `serve.sh`ten ve bir gün vekilden gelen her istek AYNI politikayı
# görür. Vekile bağlı bir yasa, vekil olmayan her ortamda SESSİZCE yoktur — ve bugün tam olarak o
# durumdayız. Vekilde kalması GEREKEN iki kalem `deploy/Caddyfile`'da AÇIK kaldı, gerekçesi orada:
# `Strict-Transport-Security` (TLS'i sonlandıran katmanın bilgisi; düz HTTP'de tarayıcı zaten yok
# sayar) ve `-Server` (aşağıda "AÇIK BORÇ" notu).
#
# ÇAKIŞMA/ZAYIFLATMA: Caddy'nin `header <ad> <değer>` biçimi SET'tir, yani üstteki vekil kopyası
# uygulamanınkini SESSİZCE değiştirir. İki canlı tanım, zamanla ayrışan iki yasa demektir. Bu
# yüzden Caddyfile'daki beş satır YORUMA ALINDI: değerleri ATIL bir REFERANS kopyası olarak durur
# (gerekçe metniyle birlikte) ve `tests/test_guvenlik_basliklari_v203.py` iki kaynağı DİZE
# EŞİTLİĞİYLE çiviler — biri değişip öteki kalırsa test kırılır. (Yan kazanç: Caddyfile'ı okuyan
# ESKİ iki bekçi — test_web_csp_uyum ve test_yazitipi_v201 — artık ATIL kopyayı ölçüyor, yani tek
# başlarına api.py'nin gevşemesini göremezlerdi; o boşluğu kapatan şey bu dize-eşitliği kapısıdır.)
#
# ---- CSP: DİREKTİFLER CADDYFILE'DAN SADAKATLE TAŞINDI, HİÇBİRİ UYDURULMADI ----
# `script-src 'self'` — GERÇEKTEN karşılanıyor (2026-08-01'de iki arıza kapatıldı: landing.html +
#   workflow.html satır içi `<script>` taşıyordu → landing.js/workflow.js'e alındı; app.js'te 34 +
#   index.html'de 6 = 40 satır içi olay özniteliği vardı → olay delegasyonuna çevrildi, `data-act`
#   KAYITLI izin listesinden çözülür). BU DİREKTİFE `'unsafe-inline'` GERİ EKLENMEZ; eklemek
#   zorunda kalındıysa bir yere satır içi işleyici geri gelmiş demektir ve çözüm eylemi kaydetmek.
#   Çivi: tests/test_web_csp_uyum.py.
# `style-src 'self' 'unsafe-inline'` — AYRI ve hâlâ AÇIK bir borç: app.js DOM'u satır içi stil
#   taşıyan şablon dizgileriyle üretiyor; kaldırmak app.js'in yeniden yazılması demek. Beyanlıdır,
#   gizlenmez.
# `font-src 'self'` — D4 sertleştirmesi (2026-08-07): `fonts.googleapis.com` ve `fonts.gstatic.com`
#   DÜŞTÜ, çünkü Recursive artık kendi-barındırılıyor (`meridian/web/fonts/*.woff2`, 79,3 KB, aynı
#   origin). BU İKİ HOST GERİ EKLENMEZ; bir CDN yazı tipi geri geldiyse çözüm başlığı gevşetmek
#   değil dosyayı `meridian/web/fonts/` altına koymaktır. Çivi: tests/test_yazitipi_v201.py.
#
# HANGİ YANITLARA GİDER — HEPSİNE, ve bu bir sadakat kararı: Caddy'nin `header` bloğu içerik tipine
# BAKMAZ, o sunucudan çıkan her yanıta yazar. Aynısını yapmak "HTML mi?" diye dallanan bir sezgiden
# daha az sürprizlidir (bir yeni rota yanlış `media_type` verdiğinde politikayı kaybetmez). JSON,
# CSV, `font/woff2` ve gövdesiz 304'ler de başlığı alır: CSP bir BELGE bağlamı politikasıdır,
# belge olmayan yanıtlarda tarayıcı onu zaten yok sayar — yani maliyet birkaç yüz bayt, kazanç tek
# yasa. `X-Content-Type-Options: nosniff` ise API yanıtlarında BAĞIMSIZ olarak değerlidir.
#
# AÇIK BORÇ — `-Server` TAŞINMADI (YASA 4: sessiz yutma yok). Caddy'nin `-Server`ı yanıttan sunucu
# parmak izini siler; bizim yanıtlarımızda o başlığı ASGI SUNUCUSU yazıyor (`server: uvicorn`),
# uygulama değil. Middleware'den silmek mümkün ama yanlış katman: uvicorn'un kendi anahtarı var
# (`server_header=False` / `--no-server-header`) ve doğru yer `serve.sh`/systemd birimidir — ikisi
# de bu turun yazma sınırının DIŞINDA. Yarım taşımak yerine adı konularak açık bırakıldı.
CSP_POLITIKASI = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
    "form-action 'self'"
)

# TEK KAYNAK. `deploy/Caddyfile`'daki karşılıkları yorumdadır ve testle bu sözlüğe çivilidir.
GUVENLIK_BASLIKLARI: dict[str, str] = {
    "Content-Security-Policy": CSP_POLITIKASI,
    # Tıklama hırsızlığı: HALT ve Flatten tek tıkla iş gören düğmeler; görünmez bir iframe içinde
    # başka bir sayfaya gömülmeleri gerçek bir senaryo. `frame-ancestors 'none'` modern tarayıcıda
    # zaten yeter, XFO eski olanlar için yanında durur (ikisi çelişmiyor, aynı şeyi söylüyorlar).
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    # URL'lerde artık sır yok (`?token=` 2026-07-28'de kaldırıldı) ama yol adları da bilgi taşır.
    "Referrer-Policy": "no-referrer",
    # Tarayıcı yetenekleri: panonun hiçbirine ihtiyacı yok.
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
}

_GB_BAYT: list[tuple[bytes, bytes]] = [
    (ad.lower().encode("latin-1"), deger.encode("latin-1"))
    for ad, deger in GUVENLIK_BASLIKLARI.items()
]
_GB_ADLAR: frozenset[bytes] = frozenset(ad for ad, _ in _GB_BAYT)


class GuvenlikBasliklariMiddleware:
    """Her HTTP yanıtına `GUVENLIK_BASLIKLARI`nı yazan SAF ASGI middleware'i.

    NEDEN `@app.middleware("http")` (BaseHTTPMiddleware) DEĞİL: o katman yanıtı bir
    `StreamingResponse`a sarar. Bu dosyanın statik yolu tam da gövde-akışı ve gövdesizlik
    üzerine kurulu — `FileResponse` (app.js 518 KB, iki `.woff2`) ve `Response(status_code=304)`.
    Saf ASGI sarıcısı `http.response.start` mesajının BAŞLIK LİSTESİNE dokunur, gövdeye HİÇ
    dokunmaz: ETag pazarlığı, 304'ün gövdesizliği ve `Content-Length` aynen korunur.

    SET semantiği (ekle-eğer-yoksa DEĞİL): Caddy'nin `header` yönergesi de SET'tir, yani aynı
    davranış. Sonucu: hiçbir rota kendi yanıtına daha GEVŞEK bir politika yazarak buradaki yasayı
    delemez. Bu bir kısıt değil, kaynağın TEK olmasının ta kendisi.

    KAPSAM SINIRI, dürüstçe ve ÖLÇÜLEREK (varsayılmadı — starlette 1.3.1'de üç yollu bir sonda
    koşuldu): Starlette `ServerErrorMiddleware`i kullanıcı middleware yığınının DIŞINDA kurar
    (`build_middleware_stack`), yani YAKALANMAMIŞ bir istisnanın ürettiği çıplak 500 bu sarıcıdan
    GEÇMEZ. Ölçüm: normal 200 → CSP VAR · `HTTPException` (418) → CSP VAR · `raise RuntimeError`
    → 500, CSP YOK. Yani `HTTPException` yolları (401/404/detaylı 500) kapsamdadır; kapsam dışı
    kalan tek şey çerçevenin kendi `Internal Server Error` yanıtıdır — sabit metin, `text/plain`,
    hiç kullanıcı verisi taşımaz, yani kaçırılan başlığın orada somut bir saldırı yüzeyi yoktur.
    Kapatmanın tek yolu ASGI uygulamasını dışarıdan sarmaktır (`uvicorn`a verilen nesneyi
    değiştirmek) ve o, `serve.sh`/systemd katmanının kalemidir. Çerçeve kısıtıdır, gizlenmiyor.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":       # lifespan/websocket: başlık kavramı yok
            await self.app(scope, receive, send)
            return

        async def _send(mesaj):
            if mesaj["type"] == "http.response.start":
                mesaj["headers"] = [
                    (ad, deger) for ad, deger in mesaj["headers"] if ad.lower() not in _GB_ADLAR
                ] + _GB_BAYT
            await send(mesaj)

        await self.app(scope, receive, _send)


# CORS'tan SONRA eklenir → yığında ONDAN DIŞTA kalır (Starlette `add_middleware`i başa ekler ve
# listeyi ters kurar). Sonuç: CORS'un kendi kısa-devre yaptığı preflight yanıtları da başlığı alır.
app.add_middleware(GuvenlikBasliklariMiddleware)


def _autostart():
    """When the operator opens the app locally (serve.sh sets the flags), bring the Hermes standby brain
    AND the paper-advance scheduler up automatically. Both off by default so tests/imports never spawn
    them. The scheduler is what keeps the local agent from freezing (stale heartbeat → Hermes idle)."""
    # EMEKLİ EDİLMEDİ — ÖLÜ DEĞİL (temizlik turu 2026-07-30, ölü-mekanizma avı adayı #çürütüldü).
    # AV İDDİASI: "MERIDIAN_SUPERVISED'ı kimse set etmiyor". ÇÜRÜTME: `ops/com.meridian.agent.plist`
    # satır 31 bu değişkeni `<string>1</string>` ile veriyor — yani Mac LaunchAgent altında koşan
    # her başlatma bu dalı GERÇEKTEN yürütür ve operatöre "süpervizör altında (yeniden) başladı"
    # bildirimi gider. Bu, süreç ölümünün operatöre ulaşan İKİ yolundan biri (öteki A1'deki
    # systemd OnFailure→fail-notify). Silinseydi sessizce kaybolan şey bir sarmalayıcı değil,
    # bir yeniden-başlatma HABERİ olurdu. OPERATÖR KALEMİ olarak belgelendi: ROADMAP §6.
    if os.environ.get("MERIDIAN_SUPERVISED") == "1":
        obs.log("supervised_start", detail="launchd süpervizörü altında başlatıldı")
        try:
            from . import notify
            if notify.configured():
                notify.send("🔁 Meridian süpervizör altında (yeniden) başladı")
        except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
            pass
    if os.environ.get("MERIDIAN_AUTOSTART_CYCLE") == "1":
        from . import scheduler
        scheduler.start(poll_seconds=int(os.environ.get("CYCLE_POLL_SECONDS", "300")))
    if os.environ.get("MERIDIAN_AUTOSTART_HERMES") == "1":
        from . import hermes_runtime
        hermes_runtime.start(poll_seconds=int(os.environ.get("HERMES_POLL_SECONDS", "300")))
    # olay-güdümlü yürütme-durumu katmanı: trade_updates dinleyicisi uvicorn'un kendi asyncio
    # loop'unda görev olarak koşar (ayna modunda varsayılan AÇIK; MERIDIAN_MIRROR_STREAM=0 kapatır).
    # Karar hattı EOD kalır — bu yalnız dolum/ret olaylarını ANINDA görünür kılar.
    if config.BROKER == "alpaca_paper" and os.environ.get("MERIDIAN_MIRROR_STREAM", "1") == "1":
        from .adapters import alpaca as _alp
        if _alp.paper_available():
            import asyncio
            from . import mirror_stream
            asyncio.get_event_loop().create_task(mirror_stream.MirrorStreamListener().run())
    # Faz 2: piyasa-verisi (dakikalık KAPANMIŞ bar) dinleyicisi → mrd:bars + sıcak fiyat. Data WS auth
    # key+secret ZORUNLU ister (REST key-only Bearer'a düşebiliyordu, WS düşemez). BROKER'dan BAĞIMSIZ
    # (veri=veri; dahili broker + Alpaca feed geçerli kombinasyon). MERIDIAN_MARKET_STREAM=0 kapatır.
    if os.environ.get("MERIDIAN_MARKET_STREAM", "1") != "0":
        from .adapters import alpaca as _alp2
        if _alp2.paper_available() and secrets_mod.present("ALPACA_PAPER_SECRET"):
            from . import marketstream
            marketstream.start()      # idempotent singleton; çift bağlantı=406 yapısal önlenir
            # Faz 3: DAYANIKLI bar-tetiği tüketicisi (mrd:barfeed consumer-group). marketstream'in
            # ürettiği "yeni bar" olaylarını okur.
            from . import barfeed
            # Faz 4: intraday_cycle (GÖZLEM-modu) tüketicisini barfeed'e REGISTER et — start()'tan ÖNCE,
            # yoksa ilk olaylar callback=None ile ACK'lenip kaybolurdu. Emir GÖNDERMEZ (Faz 4a gözlem).
            if os.environ.get("MERIDIAN_INTRADAY", "1") != "0":
                from . import intraday_cycle
                barfeed.register(intraday_cycle.consumer().on_barfeed_event)
            barfeed.start()           # idempotent daemon thread (redis-py senkron; event-loop'a dokunmaz)


def _client_ip(request: Request) -> str:
    """Ters vekil arkasındayken gerçek istemci X-Forwarded-For'un İLK girdisidir. Bu değere
    YALNIZ hız sınırı için güvenilir, yetkilendirme için ASLA — başlık istemci tarafından
    uydurulabilir. Uydurulursa saldırgan kendi kilidini atlatır ama başkasını kilitleyemez
    (kilit IP başınadır, global değil), yani kötüye kullanımın tavanı kendi hızını artırmaktır."""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _auth(request: Request):
    """Üç kabul yolu, öncelik sırasıyla:
      1) OTURUM ÇEREZİ — tarayıcının normal yolu. HttpOnly, JS okuyamaz.
      2) x-meridian-token BAŞLIĞI — betikler/CLI için; MERIDIAN_DASH_TOKEN ayarlıysa.
    `?token=` QUERY PARAMETRESİ KALDIRILDI (2026-07-28): URL'ler sunucu loglarına, tarayıcı
    geçmişine ve `Referer` başlığına düşer. İndirme bağlantıları artık çerezle çalışıyor —
    tarayıcı onu kendiliğinden gönderir, URL'e sır koymaya gerek yok."""
    if auth.verify_session(request.cookies.get(auth.COOKIE_NAME)):
        return
    if auth.password_set():
        # Parola kurulduysa oturum ZORUNLUDUR; başlık token'ı yalnız ek bir betik yoludur.
        if DASH_TOKEN and hmac.compare_digest(
                (request.headers.get("x-meridian-token") or "").encode("utf-8"),
                DASH_TOKEN.encode("utf-8")):
            return
        raise HTTPException(status_code=401, detail="unauthorized")
    if not DASH_TOKEN:
        return
    supplied = request.headers.get("x-meridian-token") or ""
    # hmac.compare_digest: constant-time comparison so the token can't be recovered byte-by-byte via
    # response-timing (CWE-208). `!=` short-circuits on the first mismatching byte (L4).
    # BAYT KARŞILAŞTIRMASI (2026-07-22, yetki denetimi bulgusu F3): `compare_digest` ASCII-DIŞI bir
    # `str` görünce TypeError atar — 401 değil, 500. Sevkiyat şablonu tam da böyle bir token koyuyordu
    # (`DEĞİŞTİR-...`), yani operatör onu olduğu gibi bırakınca TÜM API çöküyordu. Yön güvenliydi
    # (kapalı, veri sızmaz) ama operatörü "token'ı kaldırayım" çözümüne itiyordu — ki o da F2'ye,
    # yani yetkisiz açık bir yüzeye düşürürdü. Baytlara çevirince karşılaştırma her kodlamada çalışır.
    if not hmac.compare_digest(supplied.encode("utf-8"), DASH_TOKEN.encode("utf-8")):
        raise HTTPException(status_code=401, detail="unauthorized")


def _stream_health(mirror: dict | None = None) -> dict:
    """Ayna akışının DÜRÜST sağlığı. api.py ham `stream_ok` boole'sini okuyordu; o bayrak
    dinleyici öldüğünde diskte `true` donuyor ve pano ölü akışı canlı gösteriyordu.

    `mirror` verilirse dosya YENİDEN okunmaz: tek istekte dört ayrı okuma hem israftı hem de
    okumalar birbiriyle ÇELİŞEBİLİRDİ (arada yazan dinleyici → aynı yanıtta iki farklı gerçek)."""
    try:
        from . import mirror_stream
        return mirror_stream.stream_health(mirror)
    except Exception as e:
        obs.warn("stream_health_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="akış sağlığı OKUNAMADI — 'canlı' varsayılmaz")
        # Şekil TAM tutulur: eksik anahtar `.get()` ile sessizce None olur ve okuyucu "bilinmiyor"
        # ile "kopuk"u ayırt edemez. Okunamayan sağlık = bayat, kanıt yok.
        return {"ok": False, "flag": False, "stale": True, "checked_at": None,
                "checked_age_s": None, "down_since": None, "last_event_ts": None,
                "last_error": f"sağlık okunamadı: {type(e).__name__}"}


def _stream_view(mirror: dict | None = None) -> dict:
    """`_stream_health()`in pano yüküne giren DÜZ izdüşümü — uçların üçü de bunu servis eder.

    Ham `stream_ok` artık HİÇBİR uçta tek başına gitmez; buradaki `stream_ok` nabızla ÇARPILMIŞ
    değerdir. Yanına kopuşun BAŞLANGICI (`down_since`) ve nabzın YAŞI (`checked_age_s`) konur ki
    operatör "ne kadardır kopuk" sorusunu panodan yanıtlasın — bayrak tek başına bunu söyleyemez.

    Üçüncü hâl KORUNUR: hiç kanıt yoksa (ayna hiç koşmamış, dosya boş) `None` döner — pano "—" der,
    "KOPUK" değil. Ayna kullanmayan kurulumda yokluğu kopuş diye okumak da bir yalan olurdu."""
    h = _stream_health(mirror)
    # DİKKAT — bu bir şema takası DEĞİLDİR (parity yasası haklı olarak sorar): üç alan üç AYRI
    # kanıttır (nabız damgası · son olay · kopuş anı) ve biri diğerinin yerine GEÇMEZ. Burada
    # sorulan tek şey "ayna hiç koştu mu": herhangi biri varsa evet. Bu yüzden `or` zinciri değil
    # açık bir "herhangi biri" testi — zincir, iki adı eşanlamlı sanan okura yanlış şey öğretirdi.
    known = any((h.get("checked_at"), h.get("last_event_ts"), h.get("down_since")))
    return {"stream_ok": (h.get("ok") if known else None),   # nabızla ÇARPILMIŞ bayrak (ham değil)
            "stream_flag": h.get("flag"), "stream_stale": h.get("stale"),  # ham bayrak + düşme nedeni
            "stream_down_since": h.get("down_since"), "stream_checked_age_s": h.get("checked_age_s"),
            "stream_last_event_ts": h.get("last_event_ts"), "stream_last_error": h.get("last_error")}


# `max-age=0` EKLENDİ (küçük-kuyruk turu, 2026-08-02): `no-cache` tek başına RFC 9111'e göre zaten
# "her kullanımdan önce doğrula" demektir, ama saha gerçeği bu değil — bazı ara katmanlar ve eski
# tarayıcılar `no-cache`i sezgisel tazelik hesabına girmeyen bir öneri gibi işler. `max-age=0` aynı
# şeyi ikinci kez, tartışmasız bir sayıyla söyler. Üçü birlikte: sakla, ama HER İSTEKTE doğrula.
_NOCACHE = {"Cache-Control": "no-cache, max-age=0, must-revalidate"}

# ---- STATİK VARLIK ÖNBELLEK SÖZLEŞMESİ (küçük-kuyruk turu, 2026-08-02) -----------------------
# VAKA: "dagit'ten sonra değişikliği göremedim" — operatörün sert-yenilemeye mahkûm olduğu sınıf.
# ESKİ HÂL iki ayrı yerden kırıktı:
#   (a) 304 YOLU HİÇ YOKTU. `_NOCACHE` yalnız `Cache-Control` gönderiyordu; ETag'i starlette
#       1.3.1'in `FileResponse.set_stat_headers`ı `st_mtime + "-" + st_size` md5'inden yazıyor AMA
#       `If-None-Match`i okuyan kod YALNIZ `StaticFiles` montajındadır ve bu dosyada montaj
#       BİLEREK yok (yukarıdaki not: montaj WEB dizinine düşen her taslağı yayına açar). Yani
#       tarayıcı ETag'i sadakatle geri gönderiyor, sunucu onu görmezden gelip 518 KB'lık app.js'i
#       her doğrulamada BAŞTAN gövdeliyordu.
#   (b) ETAG İÇERİKTEN TÜRETİLMİYORDU. mtime tabanlı etiket iki yönde de yanılır: rsync içeriği
#       değiştirmeden mtime'ı ilerletirse aynı bayt yeniden iner (gereksiz trafik — zararsız);
#       mtime KORUNARAK içerik değişirse (kopyala-üzerine-yaz, `cp -p`, saat geri alınması)
#       tarayıcı ESKİ kopyayı saklar — vakanın tam kaynağı ve zararsız olmayan yön.
# YENİ HÂL: ETag dosya İÇERİĞİNİN sha256'sıdır (güçlü etiket) ve `If-None-Match` eşleşirse gövdesiz
# 304 döner. Sert-yenileme ihtiyacı yapısal olarak ölür.
_ETAG_MEMO: dict[str, tuple[int, int, str]] = {}


def _icerik_etag(p: Path) -> str | None:
    """Dosya İÇERİĞİNDEN güçlü ETag (sha256/32 hex). Dosya okunamıyorsa None.

    HASH MALİYETİ ve MEMO'NUN SINIRI (gerekçe, brief'in "ağır dosya" maddesine cevap): app.js 518
    KB'tır ve her istekte hash'lemek gereksizdir, bu yüzden sonuç `(mtime_ns, boyut)` anahtarıyla
    süreç-içi memolanır. DİKKAT — mtime+boyut burada YALNIZ ÖNBELLEK ANAHTARIDIR, ETag'in DEĞERİ
    DEĞİL. Fark önemlidir: anahtar ıskalarsa dosya yeniden hash'lenir (bir kez fazladan iş), ama
    zayıf etiketin yanlış-pozitifi — "aynı mtime, farklı içerik" — tarayıcıya ASLA çıkamaz, çünkü
    telden geçen değer her zaman o anki baytların özetidir. Zayıf etiket kabul edilseydi (a) fıkrası
    çözülür (b) fıkrası AYNEN kalırdı; yani vaka kapanmazdı."""
    try:
        st = p.stat()
    except OSError:  # sessiz-yutma: stat düşerse ETag ÜRETİLEMEZ ve hüküm burada verilmez — çağıran `_statik` yokluğu 404'e, okunamazlığı etiketsiz servise ayırır (uydurma etiket yasak)
        return None
    anahtar = _ETAG_MEMO.get(str(p))
    if anahtar is not None and anahtar[0] == st.st_mtime_ns and anahtar[1] == st.st_size:
        return anahtar[2]
    import hashlib
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for blok in iter(lambda: f.read(1 << 20), b""):
                h.update(blok)
    except OSError:  # sessiz-yutma: okuma yarıda düşerse yarım hash'ten etiket üretmek İÇERİK YALANI olurdu; etiketsiz dönülür ve gövdenin hükmünü FileResponse'un kendi hatası verir
        return None
    etag = f'"{h.hexdigest()[:32]}"'
    _ETAG_MEMO[str(p)] = (st.st_mtime_ns, st.st_size, etag)
    return etag


def _inm_eslesir(basligi: str | None, etag: str) -> bool:
    """RFC 9110 `If-None-Match` karşılaştırması — zayıf karşılaştırma (304 için doğru olan).

    `*` her etiketle eşleşir; virgüllü liste tek tek denenir; `W/` öneki ATILIR (biz güçlü etiket
    üretiyoruz ama bir ara katman etiketimizi zayıflatarak geri döndürebilir — o durumda gövdeyi
    yeniden göndermek doğru DEĞİL, çünkü zayıflatılmış etiket hâlâ AYNI içeriği adresliyor)."""
    if not basligi:
        return False
    for parca in basligi.split(","):
        p = parca.strip()
        if p == "*":
            return True
        if p.startswith("W/"):
            p = p[2:]
        if p == etag:
            return True
    return False


def _statik(request: Request, ad: str, media_type: str | None = None):
    """Ad-ad statik rotaların ORTAK gövdesi: içerik-ETag + no-cache + 304.

    NEDEN ORTAK FONKSİYON (sekiz kopya değil): "iki kaynak, zamanla ayrışan iki yasa" bu depodaki
    baskın hata deseni — `_NativeRoute`un gerekçesiyle aynı. Rotaların AD AD yazılması sözleşmesi
    korunur (montaj hâlâ yok); ortaklaşan şey yalnızca önbellek davranışıdır."""
    p = WEB / ad
    etag = _icerik_etag(p)
    if etag is None:
        # Etiket üretilemedi. İKİ AYRI HÂL ve ikisi AYNI cevabı almaz (uydurma yasağı):
        #   * DOSYA YOK → dürüst 404. (Starlette'in `FileResponse`u bu hâlde `RuntimeError`
        #     atar, yani operatöre 500 döner: "sunucu bozuldu" der, oysa gerçek "dosya
        #     dağıtılmamış"tır — dağıtım eksiğini bir çökme gibi gösteren bir yalan.)
        #   * DOSYA VAR AMA HASH'LENEMEDİ (izin/IO) → etiketsiz servis edilir. 304 pazarlığı o
        #     istekte yapılamaz; gövde her seferinde iner. Doğru olan budur — üretilemeyen etiket
        #     UYDURULMAZ, ve okunabilir bir dosyayı 404 saymak da ayrı bir yalan olurdu.
        if not p.is_file():
            return JSONResponse({"error": "not_found", "path": ad,
                                 "detail": "statik varlık sunucuda YOK — dağıtım eksik "
                                           "(sunucu arızası değil)"},
                                status_code=404, headers=_NOCACHE)
        return FileResponse(p, media_type=media_type, headers=_NOCACHE)
    basliklar = {**_NOCACHE, "ETag": etag}
    if _inm_eslesir(request.headers.get("if-none-match"), etag):
        # 304 GÖVDESİZDİR ve `Content-Length: 0` YAZILMAZ (RFC 9110 §15.4.5) — starlette'in
        # `Response(status_code=304)`u zaten gövde yazmaz.
        return Response(status_code=304, headers=basliklar)
    return FileResponse(p, media_type=media_type, headers=basliklar)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _statik(request, "index.html")


@app.get("/app.js")
def appjs(request: Request):
    return _statik(request, "app.js", "application/javascript")


# STATİK BETİKLER TEK TEK YÖNLENDİRİLİR (StaticFiles montajı YOK): montaj, WEB dizinine sonradan
# düşen her dosyayı — yedek, taslak, .orig — sessizce yayına açar. Ad ad yazmak sıkıcı ama
# yayına ne çıktığı okunabilir kalır.
#
# NEDEN SATIR İÇİ DEĞİL DE DOSYA: dağıtım CSP'si `script-src 'self'` (deploy/Caddyfile).
# Satır içi bloklar üretimde bloklanır — landing ve workflow bu yüzden dışarı taşındı; o iki
# sayfa aksi hâlde canlıda ölü açılırdı (workflow'un tüm diyagramı script'te üretiliyor).
@app.get("/theme.js")
def themejs(request: Request):
    return _statik(request, "theme.js", "application/javascript")


@app.get("/landing.js")
def landingjs(request: Request):
    return _statik(request, "landing.js", "application/javascript")


@app.get("/workflow.js")
def workflowjs(request: Request):
    return _statik(request, "workflow.js", "application/javascript")


# ⌘K komut paleti. Yol AD AD yazılmak ZORUNDA (yukarıdaki not: StaticFiles montajı yok) —
# index.html'e script etiketini eklemek TEK BAŞINA yetmez, bu satır olmadan üretimde 404
# döner ve palet sessizce hiç var olmaz.
@app.get("/palette.js")
def palettejs(request: Request):
    return _statik(request, "palette.js", "application/javascript")


# ---- YAZI TİPİ SUNUMU (D5, 2026-08-07) -------------------------------------------------------
# VAKA: D4 turu Recursive'i kendi-barındırmaya aldı — `meridian/web/fonts/` altına iki `.woff2`,
# üç yüzeye yerel yollu `@font-face`, ve CSP'den `fonts.googleapis.com` + `fonts.gstatic.com`
# DÜŞTÜ. Ama sunum yolu açılmadı: `/fonts/recursive-sans-vf.woff2` ve `/fonts/recursive-mono-vf.woff2`
# ölçülerek 404 dönüyordu (tests/test_yazitipi_v201.py'nin KATI xfail'i bunu çivilemişti; o blok
# bu turda gerçek teste çevrildi). `@font-face` yolu tek başına bir VAAT'tir — dosyanın diskte
# olması da öyle; sunulan şey rotadır. Rota olmadan dağıtım üç yüzeyi de sistem yüzüne düşürürdü
# ve CSP `font-src 'self'` olduğu için "CDN'den gelsin" kaçışı da yok (ki olmaması SERTLEŞTİRME).
#
# NEDEN MONTAJ DEĞİL: yukarıdaki not (satır 469) `StaticFiles` montajını BİLEREK reddediyor —
# montaj WEB dizinine düşen her taslağı/yedeği/.orig'i sessizce yayına açar. O hüküm burada da
# geçerli, hatta daha sert: bir `fonts/` montajı, dizine düşen HER baytı (ölçüm turunun ara TTF'leri,
# lisans dışı bir kesit, bir `.orig`) yayına açardı. Bunun yerine SUNULAN AD KÜMESİ KAYNAKTA
# LİTERALDİR: aşağıdaki iki dize dışında hiçbir şey 200 alamaz.
#
# DİZİN-DIŞI ERİŞİM (path traversal) BURADA BİR FİLTRE İŞİ DEĞİL: `..`, kodlanmış ayraç, mutlak yol,
# sembolik bağ — hiçbiri "temizlenmiyor", çünkü hiçbiri KÜMEYE GİREMİYOR. Tam-eşleşme bir izin
# listesi, kara listeden farklı olarak yeni bir kaçış biçimi keşfedildiğinde de kapalı kalır.
# Testle çivili: tests/test_font_rotasi_v202.py.
#
# ÖNBELLEK — `immutable` DEĞİL, ve bu bir tercih değil bir düzeltme: dosya adları SÜRÜMSÜZDÜR
# (`recursive-sans-vf.woff2`, hash'siz). `Cache-Control: immutable, max-age=1y` ancak adın içeriği
# adreslediği yerde doğrudur; burada bir sonraki yazı tipi turu AYNI ADLA farklı bayt dağıtır ve
# `immutable` o baytları tarayıcıda bir yıl boyunca ulaşılmaz kılardı — "dagit'ten sonra değişikliği
# göremedim" vakasının (yukarıdaki önbellek sözleşmesi) tam olarak yazı tipi hâli. Bu yüzden
# fontlar da öteki varlıklarla AYNI yasayı okur: içerik-sha256 ETag + `no-cache, must-revalidate`
# + eşleşmede gövdesiz 304. Doğrulama isteği başına maliyet ~0 bayt, bayatlama penceresi SIFIR.
_FONT_DOSYALARI = frozenset({"recursive-sans-vf.woff2", "recursive-mono-vf.woff2"})


@app.get("/fonts/{ad}")
def fontlar(request: Request, ad: str):
    """Kendi-barındırılan Recursive kesitleri. YALNIZ literal iki ad; başka her şey 404."""
    if ad not in _FONT_DOSYALARI:
        # `_statik`in 404 gövdesiyle AYNI dili konuşur ama AYNI CÜMLEYİ kurmaz: orada teşhis
        # "dağıtım eksik", burada "böyle bir yazı tipi YOK" — istenen ad hiç sunulmuyor, diskte
        # olup olmaması sonucu değiştirmiyor. İkisini aynı metne bağlamak operatörü yanlış yere
        # (rsync'e) bakmaya gönderirdi.
        return JSONResponse({"error": "not_found", "path": f"fonts/{ad}",
                             "detail": "sunulan yazı tipi kümesinde YOK — bu rota yalnız "
                                       "kaynakta literal olarak sayılan kesitleri sunar"},
                            status_code=404, headers=_NOCACHE)
    return _statik(request, f"fonts/{ad}", "font/woff2")


@app.get("/landing", response_class=HTMLResponse)
def landing(request: Request):
    """The original marketing landing page — the design reference the dashboard is cut from.

    ÖNBELLEK NOTU (küçük-kuyruk turu): bu rota ve `/workflow` `_NOCACHE`i HİÇ göndermiyordu — yani
    tanıtım sayfası, panonun aksine, tarayıcının sezgisel tazelik hesabına bırakılmıştı. C10
    bekçisinin canlı-sayı sözleşmesi (landing.js → /api/public/summary) tam da bu sayfada geçerli
    ve bayat bir HTML kabuğu o sözleşmeyi sessizce boşa çıkarırdı."""
    return _statik(request, "landing.html")


@app.get("/api/public/summary")
def api_public_summary():
    """TANITIM SAYFASI İÇİN DÜRÜST ÖZET — kimlik doğrulaması YOK, bilerek.

    Tanıtım sayfası herkese açıktır; `_auth`'lu bir uca bağlanırsa operatör DASH_TOKEN koyduğu an
    sayfa kırılır ve eski/sahte içeriğe düşer. Bu yüzden ayrı ve dar bir uç: yalnız araştırma
    sisteminin KAMUYA açık gerçekleri döner.

    DIŞARI VERİLMEZ: sermaye, açık pozisyon, hisse adı, broker, anahtar, günlük P&L. Bunlar
    operatörün hesabına aittir ve bir tanıtım sayfasının işi değildir.

    Buradaki her sayı `state/`ten hesaplanır. Hiçbiri elle yazılmaz — sayfanın daha önce
    taşıdığı uydurma "promoted / gerçekleşen +0.11" kayıtlarının yerini bu alır."""
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    hyp = store.read_jsonl("hypotheses.jsonl")
    trades = store.read_jsonl("trades.jsonl")
    hb = store.read_json("heartbeat.json", {})
    # Skill kütüphanesi sayıları — sermaye/pozisyon verisi değil, kamuya açık envanter gerçeği.
    # Tanıtım sayfasındaki eski sabit "66 skill" yazısının yerine bu gider: 2026-07-30 arşivi
    # (68 klasör → 31 canlı) sabit sayıyı bir gecede yalana çevirmişti. Salt okunur.
    sreg = store.read_json("skills_registry.json", {"skills": {}}).get("skills", {})
    by_status: dict[str, int] = {}
    for h in hyp:
        s = h.get("status") or "unknown"
        by_status[s] = by_status.get(s, 0) + 1
    # "Kapıyı geçen" = canlıya çıkmış sürüm. Bu sistemde henüz hiç olmadı ve sayfa bunu söylemeli.
    shipped = sum(n for s, n in by_status.items() if s in ("shipped", "promoted", "accepted"))
    return {
        "mode": hb.get("mode"),
        "autonomy_level": hb.get("autonomy_level"),
        "strategy_version": hb.get("version"),
        "closed_trades": len(trades),
        "score": hb.get("score"),
        "hypotheses_total": len(hyp),
        "hypotheses_by_status": by_status,
        "hypotheses_shipped": shipped,
        "hypotheses_with_realized": sum(1 for h in hyp if h.get("realized_delta") is not None),
        "variables_tried": len({h.get("variable") for h in hyp if h.get("variable")}),
        "skills_live": sum(1 for v in sreg.values() if not v.get("retired")),
        "skills_enabled": sum(1 for v in sreg.values() if v.get("enabled") and not v.get("retired")),
        # kurulum × rejim verim matrisi — araştırma çıktısı, hesap verisi değil; tanıtım
        # sayfasındaki ürün maketi bunu gösterir, uydurma bir örnek değil.
        "matrix": _setup_regime_matrix(trades),
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }


def _setup_regime_matrix(trades: list) -> dict:
    """Kapanmış işlemlerden kurulum × rejim matrisi. `/api/plots` ile aynı hesap, kimlik
    doğrulamasız yüzey için sadeleştirilmiş hali (işlem listesi taşımaz)."""
    cells: dict = {}
    setups: list[str] = []
    regimes: list[str] = []
    for t in trades:
        s, rg = t.get("setup"), t.get("regime")
        if not s or not rg:
            continue
        if s not in setups:
            setups.append(s)
        if rg not in regimes:
            regimes.append(rg)
        c = cells.setdefault((s, rg), {"n": 0, "sum_r": 0.0, "wins": 0})
        c["n"] += 1
        c["sum_r"] += float(t.get("r_multiple") or 0.0)
        c["wins"] += 1 if (t.get("r_multiple") or 0) > 0 else 0
    grid = []
    for s in setups:
        row = []
        for rg in regimes:
            c = cells.get((s, rg))
            row.append(None if not c else {
                "n": c["n"],
                "mean_r": round(c["sum_r"] / c["n"], 3),
                "hit": round(c["wins"] / c["n"], 3),
            })
        grid.append({"setup": s, "cells": row})
    return {"setups": setups, "regimes": regimes, "grid": grid}


@app.get("/workflow", response_class=HTMLResponse)
def workflow(request: Request):
    """İnteraktif günlük karar hattı diyagramı — kapanış sonrası tek döngünün tam akışı; bugünkü
    darboğaz turunda eklenen mekanizmalar YENİ rozetiyle işaretli. Bağımsız, dış bağımlılık yok."""
    return _statik(request, "workflow.html")


# ---- RUNBOOK YÜZEYİ (UIUX S1-T3, 2026-08-01) -------------------------------------------------
# J2 zinciri "alarm → teşhis → runbook → çözüm" son halkasızdı: pano alarm satırları ve sessiz-hat
# sapmaları bir hedef gösteremiyordu (WP0 borç #1). Hedef artık `docs/RUNBOOK.md` ve OKUYUCUSU bu
# rota (YASA 6: okuyucusuz yazım yok).
#
# NEDEN SUNUCUDA RENDER (istemci tarafı markdown ayrıştırıcı DEĞİL): dağıtım CSP'si
# `script-src 'self'` — istemci yolu ayrı bir /runbook.js dosyası + ayrı bir /api/runbook ucu +
# bir ayrıştırıcı isterdi. Üç hareketli parça yerine bir fonksiyon. Üretim anında HTML gömmek de
# elendi: gömülü kopya `docs/RUNBOOK.md` ile SESSİZCE ayrışabilirdi. Burada kaynak HER İSTEKTE
# diskten okunur, yani ayrışma imkânsızdır.
#
# YETKİ: `_auth` ZORUNLU. Runbook mekanizma adlarını, betik başlıklarını ve mühendislik
# günlüğünün açık-kalanlarını taşır — sistemin iç haritasıdır. `/landing` ve `/workflow` genel
# anlatım yüzeyleridir; bu değil.
_MD_SATIR_ICI = (
    # SIRA BAĞLAYICI: `**` tek `*`ten ÖNCE, yoksa kalın metin iki boş `<em>`e bölünür.
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"\*([^*]+)\*"), r"<em>\1</em>"),
    # YALNIZ BELGE-İÇİ ÇAPA BAĞLARI. Dış bağlantı üretilmez: runbook'un kendi kaynağı bu
    # depodadır ve bir belge üreticisinin dışarı bağlantı açması, denetlenmeyen bir yüzeydir.
    (re.compile(r"\[([^\]]+)\]\(#([A-Za-z0-9_\-]+)\)"), r'<a href="#\2">\1</a>'),
)


def _md_satir(s: str) -> str:
    """Satır içi biçimleme — ÖNCE kaçış, SONRA desenler. Ters sıra, md içindeki bir `<` işaretini
    etiket sanardı. Desenlerin kullandığı karakterler (`*`, backtick, köşeli parantez) kaçıştan
    etkilenmez, yani sıra güvenli."""
    s = html.escape(s, quote=False)
    for desen, yerine in _MD_SATIR_ICI:
        s = desen.sub(yerine, s)
    return s


_MD_BASLIK = re.compile(r"^(#{1,3})\s+(.*?)(?:\s*\{#([^}]+)\})?\s*$")
# `ops/runbook_uret.py::YAZILMADI` ile AYNI dizge. İki yerde durması bir kopya değil bir
# SÖZLEŞMEDİR (üretici yazar, okuyucu tanır) ve test onu çivili tutar — ayrışırsa işaret
# sessizce sönerdi, yani eksik girdiler çözülmüş girdilerle aynı tonda görünürdü.
_RUNBOOK_YAZILMADI = "runbook girdisi henüz yazılmadı"


def _md_render(md: str) -> tuple[str, str]:
    """`docs/RUNBOOK.md` → (gövde HTML, içindekiler HTML).

    KENDİ ÜRETTİĞİMİZ MARKDOWN'IN DAR AYRIŞTIRICISIDIR, genel amaçlı bir markdown motoru
    DEĞİL — ve bir bağımlılık eklememek için böyle: `ops/runbook_uret.py` yalnız şu yapıları
    üretir ve üretici ile ayrıştırıcı aynı turda yazıldı. Tanınmayan bir satır KAYBOLMAZ,
    paragraf olarak çıkar (sessiz yutma yok).

    ÇAPALAR `{#ad}` sözdiziminden gelir ve BAŞLIK ADININ KENDİSİDİR (slug'lanmaz): pano
    `/runbook#<mekanizma>` bağını çalışma anında API'den gelen adla kurar, araya bir dönüşüm
    girseydi iki ayrı slug kuralı doğar ve biri sessizce bayatlardı."""
    govde: list[str] = []
    toc: list[str] = []
    liste_derinlik = 0        # 0 = liste yok, 1 = <ul>, 2 = iç içe <ul>
    kod = False
    kod_tampon: list[str] = []
    alinti: list[str] = []

    def _liste_kapat():
        nonlocal liste_derinlik
        while liste_derinlik > 0:
            govde.append("</ul>")
            liste_derinlik -= 1

    def _alinti_kapat():
        if alinti:
            govde.append("<blockquote><p>" + " ".join(alinti) + "</p></blockquote>")
            alinti.clear()

    for ham in md.splitlines():
        if ham.startswith("```"):
            if kod:
                govde.append("<pre><code>" + html.escape("\n".join(kod_tampon), quote=False) + "</code></pre>")
                kod_tampon.clear()
            else:
                _liste_kapat(); _alinti_kapat()
            kod = not kod
            continue
        if kod:
            kod_tampon.append(ham)
            continue

        if not ham.strip():
            _liste_kapat(); _alinti_kapat()
            continue

        m = _MD_BASLIK.match(ham)
        if m:
            _liste_kapat(); _alinti_kapat()
            duzey, metin, capa = len(m.group(1)), m.group(2), m.group(3)
            kimlik = f' id="{html.escape(capa, quote=True)}"' if capa else ""
            govde.append(f"<h{duzey}{kimlik}>{_md_satir(metin)}</h{duzey}>")
            if capa and duzey <= 2:
                sinif = ' class="g"' if duzey == 1 else ""
                toc.append(f'<li{sinif}><a href="#{html.escape(capa, quote=True)}">'
                           f"{_md_satir(metin)}</a></li>")
            continue

        if ham.startswith("---"):
            _liste_kapat(); _alinti_kapat()
            govde.append("<hr>")
            continue

        if ham.startswith("> "):
            _liste_kapat()
            alinti.append(_md_satir(ham[2:]))
            continue
        _alinti_kapat()

        if ham.startswith("  - "):
            if liste_derinlik == 0:
                govde.append("<ul>"); liste_derinlik = 1
            if liste_derinlik == 1:
                govde.append("<ul>"); liste_derinlik = 2
            govde.append(f"<li>{_md_satir(ham[4:])}</li>")
            continue
        if ham.startswith("- "):
            while liste_derinlik > 1:
                govde.append("</ul>"); liste_derinlik -= 1
            if liste_derinlik == 0:
                govde.append("<ul>"); liste_derinlik = 1
            # "runbook girdisi henüz yazılmadı" satırı BU SAYFADAKİ TEK RENKLİ ÖĞEDİR: eksiğin
            # adı, çözülmüş bir satırla aynı tonda duramaz.
            sinif = ' class="yok"' if _RUNBOOK_YAZILMADI in ham else ""
            govde.append(f"<li{sinif}>{_md_satir(ham[2:])}</li>")
            continue

        _liste_kapat()
        govde.append(f"<p>{_md_satir(ham)}</p>")

    if kod:                       # kapanmamış çit — içerik YUTULMAZ, olduğu gibi basılır
        govde.append("<pre><code>" + html.escape("\n".join(kod_tampon), quote=False) + "</code></pre>")
    _liste_kapat(); _alinti_kapat()
    return "\n".join(govde), ("<ul>" + "\n".join(toc) + "</ul>" if toc else "")


RUNBOOK_MD = Path(__file__).resolve().parents[1] / "docs" / "RUNBOOK.md"
_RUNBOOK_YER_TUTUCU = ("<!--RUNBOOK-GOVDE-->", "<!--RUNBOOK-TOC-->")


@app.get("/runbook", response_class=HTMLResponse)
def runbook(request: Request):
    """`docs/RUNBOOK.md`'nin okunur yüzeyi — alarm satırlarının ve sessiz-hat sapmalarının hedefi.

    EKSİK KAYNAK SESSİZ GEÇMEZ. Belge yoksa ya da kabuk yer tutucularını kaybettiyse sayfa BOŞ
    dönmez: ne olduğunu ve nasıl düzeltileceğini (`python ops/runbook_uret.py`) söyleyen bir
    hata döner. Boş bir runbook, olay anında en kötü yalandır — "bakacak bir şey yok" der."""
    _auth(request)
    kabuk = (WEB / "runbook.html").read_text(encoding="utf-8")
    for yt in _RUNBOOK_YER_TUTUCU:
        if yt not in kabuk:
            raise HTTPException(status_code=500,
                                detail=f"runbook.html yer tutucusunu kaybetti: {yt}")
    if not RUNBOOK_MD.exists():
        raise HTTPException(
            status_code=503,
            detail="docs/RUNBOOK.md YOK — runbook henüz üretilmemiş. Üret: python ops/runbook_uret.py")
    govde, toc = _md_render(RUNBOOK_MD.read_text(encoding="utf-8"))
    sayfa = kabuk.replace(_RUNBOOK_YER_TUTUCU[0], govde).replace(_RUNBOOK_YER_TUTUCU[1], toc)
    return HTMLResponse(sayfa, headers=_NOCACHE)


# ---------- liveness / metrics (no auth — used by health checks & scrapers) ----------
# ---- KİMLİK: giriş / çıkış / oturum yoklama / ilk kurulum (2026-07-28) -----------------------
# Aşağıdaki DÖRT uç `_auth` ÇAĞIRMAZ ve çağırmamalıdır — kimlik doğrulamanın kendisi buradan
# geçer. Kapalı bir kapıya girmenin yolu kapının kendisi olamaz.
#
# LİSTE NEDEN ÜRETİM KODUNDA (2026-07-29): yetki denetimi testleri (test_api_audit_v21::test_p1,
# test_p1c ve test_authority_boundaries_v77::test_c7) "yetkisiz uç" ararken bu istisnaları bilmek
# zorunda. Liste iki test dosyasında AYRI AYRI tutulsaydı, tek bir yasanın iki kopyası olurdu ve
# zamanla ayrışırlardı — bu depodaki baskın hata deseni. Tek kaynak burada, gerekçeleriyle durur;
# testler onu OKUR. Buraya yeni bir yol eklemek, gerekçesini de buraya yazmak demektir ve bir
# istisna listesini büyütmek denetimde görünür bir harekettir.
KIMLIK_UCLARI = frozenset({
    # Parolayı doğrular ve oturumu VERİR — oturum İSTEYEMEZ. Yetkisiz olması sınırsız deneme
    # demek DEĞİL: `auth.locked_out` IP başına kayan pencereyle kilitler (429).
    "/api/login",
    # Yalnız çerezi SİLER, hiçbir şey okumaz/sızdırmaz. Yetki isteseydi süresi geçmiş bir
    # oturumla gelen operatör ÇIKIŞ bile yapamazdı — kapının dışında kalan kişiye kilidi
    # kapatma hakkı vermemek anlamsızdır.
    "/api/logout",
    # Panonun açılışta sorduğu tek soru: giriş ekranı mı, kurulum ekranı mı, uygulama mı?
    # Dönen alanlar YALNIZ {authenticated, password_set, tls} — hesap durumu, sermaye, pozisyon
    # YOK. `password_set`in dışarıya açık olması BİLİNÇLİ: kurulum ekranını sürükleyen bilgi
    # odur ve gizlenmesi sahte bir mahremiyet olurdu (bkz. api_login docstring'i).
    "/api/session",
    # İLK parolayı belirler ve YALNIZ parola kurulu DEĞİLKEN çalışır (kurulduktan sonra 409).
    # Yetki isteseydi ilk parola hiçbir zaman kurulamazdı — tavuk-yumurta. Bu bir "parolamı
    # unuttum" arka kapısı DEĞİLDİR; sıfırlama yalnız kabuktan yapılır (meridian.auth_cli).
    "/api/setup-password",
})


def _secure_cookie(request: Request) -> bool:
    """Çerez `Secure` işaretlenmeli mi? TLS altındaysak evet. Ters vekil arkasında bağlantı
    sunucuya düz HTTP gelir, gerçek şemayı `X-Forwarded-Proto` taşır. localhost'ta geliştirirken
    `Secure` koymak çerezi TAMAMEN kullanılamaz yapardı (tarayıcı http'de göndermez), o yüzden
    şemaya bakılır — kapatma anahtarına değil."""
    proto = request.headers.get("x-forwarded-proto", "") or request.url.scheme
    return proto == "https"


@app.post("/api/login")
def api_login(request: Request, body: dict):
    """Parolayı doğrula, imzalı oturum çerezi ver.

    ZAMANLAMA: parola kurulu değilse de scrypt çalıştırılmaz ama yanıt aynı 401'dir — kurulum
    durumu `GET /api/session` üzerinden ZATEN açıkça bildiriliyor, dolayısıyla burada gizlemeye
    çalışmak sahte bir mahremiyet olurdu."""
    ip = _client_ip(request)
    if auth.locked_out(ip):
        raise HTTPException(status_code=429, detail=f"cok fazla deneme — {auth.retry_after_s(ip)} sn sonra")
    pw = (body or {}).get("password") or ""
    if not auth.password_set() or not auth.verify_password(pw):
        auth.note_failure(ip)
        obs.warn("login_failed", detail=f"ip={ip}")
        raise HTTPException(status_code=401, detail="parola hatalı")
    auth.note_success(ip)
    tok = auth.issue_session()
    r = JSONResponse({"ok": True, "expires_in": auth.SESSION_TTL_S})
    r.set_cookie(auth.COOKIE_NAME, tok, max_age=auth.SESSION_TTL_S,
                 httponly=True, samesite="strict", secure=_secure_cookie(request), path="/")
    return r


@app.post("/api/logout")
def api_logout(request: Request):
    r = JSONResponse({"ok": True})
    r.delete_cookie(auth.COOKIE_NAME, path="/")
    return r


@app.get("/api/session")
def api_session(request: Request):
    """Panonun açılışta sorduğu tek soru: giriş ekranı mı, uygulama mı?
    `password_set` false ise pano KURULUM ekranını gösterir — ilk parolayı orada belirler."""
    return {"authenticated": auth.verify_session(request.cookies.get(auth.COOKIE_NAME)),
            "password_set": auth.password_set(),
            "tls": _secure_cookie(request)}


@app.post("/api/setup-password")
def api_setup_password(request: Request, body: dict):
    """İLK parolayı belirle. YALNIZ parola henüz kurulu DEĞİLKEN çalışır — kurulduktan sonra
    aynı uç 409 döner, yani bu bir "parolayı sıfırla" arka kapısı DEĞİLDİR. Unutulan parola
    kabuktan sıfırlanır: `python -m meridian.auth_cli set` (state/auth.json'a erişim gerekir,
    ki o da sunucuya erişim demektir — bu sınır bilinçlidir)."""
    if auth.password_set():
        raise HTTPException(status_code=409, detail="parola zaten kurulu")
    pw = (body or {}).get("password") or ""
    try:
        auth.set_password(pw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    obs.warn("password_set", detail=f"ip={_client_ip(request)}")
    tok = auth.issue_session()
    r = JSONResponse({"ok": True})
    r.set_cookie(auth.COOKIE_NAME, tok, max_age=auth.SESSION_TTL_S,
                 httponly=True, samesite="strict", secure=_secure_cookie(request), path="/")
    return r


@app.get("/healthz")
def healthz():
    hb = store.read_json("heartbeat.json", {})
    age = health.heartbeat_age_seconds()
    stale = health.stale()
    body = {"status": "stale" if stale else "ok", "heartbeat_age_seconds": age,
            "halted": health.halted(), "mode": config.MODE, "last_bar": hb.get("last_bar")}
    return JSONResponse(body, status_code=200 if not stale else 503)


def _local_request(request: Request) -> bool:
    """İstek bu makineden mi geliyor? (denetim turu 6) Tünel/uzak istekler için hassas ölçütler
    kısılır — panik sayfası tünelden açılabildiği için /metrics de dışarı bakabilir."""
    try:
        return (request.client.host if request.client else "") in ("127.0.0.1", "::1", "localhost")
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        return False


@app.get("/metrics", response_class=PlainTextResponse)
def metrics(request: Request):
    """Prometheus text exposition — zero dependencies. Scrape-friendly liveness + book state.

    GİZLİLİK SINIRI (denetim turu 6, 2026-07-21): bu uç YETKİSİZDİ ve öz sermaye, günlük P&L, açık
    pozisyon sayısı, LLM harcaması gibi HESAP BİLGİLERİNİ herkese açıyordu. Yerelde sorun değil, ama
    /halt sayfası bilinçli olarak tünelden açılıyor — tünel tüm uygulamayı dışarı verir. Artık:
    yerel istek VEYA doğru token → tam set; uzak+yetkisiz → yalnız CANLILIK (up/heartbeat/halted)."""
    full = _local_request(request)
    if not full:
        try:
            _auth(request)
            full = True
        except HTTPException:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            full = False
    hb = store.read_json("heartbeat.json", {}) if full else {}
    dq = store.read_json("data_quality.json", {}) if full else {}
    trades = store.read_jsonl("trades.jsonl") if full else []
    detail = analytics.score_mod.score_detail(trades, config.goal()) if full else {}
    age = health.heartbeat_age_seconds()
    def g(name, val, help_):
        v = 0 if val is None else (1 if val is True else (0 if val is False else val))
        return f"# HELP {name} {help_}\n# TYPE {name} gauge\n{name} {v}\n"
    live = "".join([
        # honest 'up': the AGENT is alive only if the daily cycle is advancing (heartbeat fresh) — a dead
        # cycle behind a live web process must NOT read as up=1.
        g("meridian_up", 0 if (age is None or age > 3600) else 1, "agent alive = heartbeat fresh (<1h)"),
        g("meridian_heartbeat_age_seconds", age if age is not None else -1, "seconds since last heartbeat"),
        g("meridian_halted", health.halted(), "kill switch active"),
    ])
    if not full:
        return live + "# NOTE: hesap ölçütleri gizlendi (uzak + yetkisiz istek)\n"
    out = "".join([
        live,
        g("meridian_autonomy_level", config.limits()["autonomy_level"], "0=paper 1=live-approval 2=live"),
        g("meridian_equity_usd", hb.get("equity", 0) or 0, "paper equity"),
        g("meridian_open_positions", hb.get("open_positions", 0) or 0, "open positions"),
        g("meridian_day_pnl_pct", hb.get("day_pnl_pct", 0) or 0, "day P&L fraction"),
        g("meridian_breaker_tripped", bool(hb.get("breaker_tripped")), "daily-loss breaker tripped"),
        g("meridian_data_ok", bool(dq.get("index_ok", True)) and not dq.get("data_halt", False), "data-quality gate ok"),
        g("meridian_trades_total", len(trades), "closed trades"),
        g("meridian_score", detail.get("score") if detail.get("score") is not None else -2, "composite score (-2 = undefined)"),
        g("meridian_strategy_version", config.load_strategy().get("version", 1), "live strategy version"),
        g("meridian_hermes_spend_usd", _spend_summary()["spent_usd"], "Hermes LLM spend this month (USD)"),
        g("meridian_hermes_budget_over", _spend_summary()["over_budget"], "monthly LLM budget exhausted"),
    ])
    return out


def _spend_summary():
    from . import spend
    return spend.summary()


# ---- YETİM GET UÇLARI: EMEKLİ AMA CANLI (K1, 2026-07-30) ------------------------------------
# Aşağıdaki dört uç panodan, ops'tan ve skill'lerden HİÇ çağrılmıyor (tek tur atan yer parite
# testi — o da tüketim değil). Verileri BAŞKA bir uçtan zaten akıyor, yani "servis ediliyor"
# yanılsaması bir kopya yüzey daha yaratıyordu:
#   /api/spend      → /api/hermes `spend` (+ /api/diagnostics mlops)
#   /api/selfreview → /api/diagnostics `selfreview_summary`
#   /api/scheduler  → /api/hermes `scheduler` (+ /api/diagnostics `scheduler`)
#   /api/sprint     → /api/hermes `sprint`
#   /api/pipeline_runs → /api/skills `recent_runs` (K1'de bağlandı)
#
# NEDEN SİLİNMEDİ (geri alınabilirlik, operatör kuralı): bir rotayı silmek, ona bugün inanan bir
# istemciyi (operatörün curl'ü, ileride bir ops betiği) SESSİZ 404'e düşürür. İşaretlemek maliyeti
# sıfıra indirmez ama iki şeyi yapar: (1) sonraki turda güvenle silinecekler artık YAZILI, (2)
# "yeni bir tüketici yazacaksam hangi uca bakmalıyım" sorusunun cevabı kodda duruyor.
# KURAL: bu uçlara YENİ tüketici bağlanmaz — kanonik uç yukarıda yazılı.
# K1-EMEKLİ: kanonik yüzey /api/hermes `spend`. Yeni tüketici bağlanmaz.
@app.get("/api/spend")
def api_spend(request: Request):
    _auth(request)
    from . import spend
    return {**spend.summary(), "recent": list(reversed(store.read_jsonl("spend.jsonl")[-30:]))}


@app.get("/api/events")
def api_events(request: Request):
    _auth(request)
    return {"events": list(reversed(obs.recent(80)))}


@app.get("/api/summary")
def summary(request: Request):
    _auth(request)
    goal = config.goal()
    detail = analytics.score_mod.score_detail(store.read_jsonl("trades.jsonl"), goal)
    return {
        "goal": goal, "mode": config.MODE, "autonomy_level": config.limits()["autonomy_level"],
        "strategy_version": config.load_strategy().get("version"),
        "score_detail": detail, "ladder": analytics.autonomy_ladder(goal),
        "footer": "Research system. Paper mode. Not financial advice.",
    }


# ---- SON DÖNGÜ ÖZETİ: OLAY PENCERESİNDEN BAĞIMSIZ (v190) ---------------------------------------
# KUSUR (operatör bulgusu): panonun "Dün gece" kartı `/api/events`in son 80 kaydında `daily_cycle`
# arıyordu. Olay günde BİR kez yazılır; gün içindeki poll/uyarı satırları onu o pencereden taşırınca
# kart "ölçülemedi" diyordu — döngü koşmuş olsa bile. Ölçüm değil PENCERE bozuktu.
# DÜZELTME OKUYUCU TARAFINDA: aynı olgu (döngünün kendi `daily_cycle` kaydı) defterin KUYRUĞUNDAN
# okunur — kaç olay yazıldığından bağımsız. İKİNCİ BİR DURUM DOSYASI AÇILMADI: döngünün yazdığı
# dosya kümesi bilinçli ve sınırlı bir listedir (test_loop_gaps_v48) ve aynı olgunun ikinci bir
# kopyası, iki sahipli bir gerçek demek olurdu. Yan fayda: düzeltme, canlıda ZATEN yazılmış
# kayıtlarla anında çalışır — bir sonraki döngüyü beklemez.
# TAM DOSYA OKUNMAZ: `events.jsonl` canlıda ~9 MB ve `/api/today` panonun en sık çağrılan ucu —
# her istekte 9 MB ayrıştırmak, kusurun yerine bir performans kusuru koymak olurdu. İki kademeli
# kuyruk + kısa ömürlü önbellek: günde bir değişen bir olguyu her istekte yeniden aramayız.
_SON_DONGU_KUYRUK = (512_000, 4_000_000)   # ~4 gün / ~1 ay (canlı ölçüm: ~120 KB olay/gün)
# ÖNBELLEK ANAHTARI ZAMAN DEĞİL DEFTERİN KENDİSİ (state yolu + boyut + mtime). Süreli bir önbellek
# testlerde ve sandbox'larda BAŞKA bir state'in cevabını servis edebilirdi; dosya değişmediyse
# cevabın değişmesi de imkânsızdır — `codelaw._src_stamp`/`ledgers.declared_writers` ile aynı desen.
_SON_DONGU_ONBELLEK: dict = {"anahtar": None, "yuk": None}


def _son_dongu_olaydan() -> dict | None:
    """Olay defterinin SONUNDAN sınırlı bir kuyruk okur ve son `daily_cycle` satırını döndürür."""
    p = Path(config.STATE) / "events.jsonl"
    for kuyruk in _SON_DONGU_KUYRUK:
        try:
            boyut = p.stat().st_size
            with open(p, "rb") as f:
                if boyut > kuyruk:
                    f.seek(boyut - kuyruk)
                    f.readline()              # kuyruğun başındaki YARIM satır atılır
                satirlar = f.read().decode("utf-8", "replace").splitlines()
        except OSError:  # sessiz-yutma: defter yok/okunamıyor — çağıran bunu "ölçülemedi" olarak BEYAN eder (var:false + neden), uydurma özet üretmez
            return None
        for s in reversed(satirlar):
            if '"daily_cycle"' not in s:
                continue
            try:
                ev = json.loads(s)
            except ValueError:  # sessiz-yutma: kırpılmış/bozuk tek satır — tarama bir sonraki satırla sürer, bozuk satır özet ÜRETEMEZ
                continue
            if isinstance(ev, dict) and ev.get("event") == "daily_cycle":
                return ev
        if boyut <= kuyruk:                   # defterin TAMAMI tarandı — ikinci kademe boşuna
            return None
    return None


def _son_dongu() -> dict:
    """Panonun "Dün gece" kartının kaynağı: son günlük döngünün KENDİ kaydı (pencere değil)."""
    import datetime as _dt
    try:
        _st = (Path(config.STATE) / "events.jsonl").stat()
        anahtar = (str(config.STATE), _st.st_size, _st.st_mtime_ns)
    except OSError:  # sessiz-yutma: damga alınamadı — önbellek DEVRE DIŞI kalır (anahtar None), okuma yine yapılır; körlük cevabı değil yalnız hızı etkiler
        anahtar = None
    if anahtar is not None and _SON_DONGU_ONBELLEK["anahtar"] == anahtar:
        doc = _SON_DONGU_ONBELLEK["yuk"]
    else:
        doc = _son_dongu_olaydan()
        _SON_DONGU_ONBELLEK.update(anahtar=anahtar,
                                   yuk=doc if isinstance(doc, dict) else None)
    if not isinstance(doc, dict) or not doc.get("date"):
        return {"var": False, "kaynak": None,
                "neden": "günlük döngü kaydı yok — olay defterinin kuyruğunda `daily_cycle` satırı "
                         "bulunamadı (döngü hiç koşmamış olabilir). 'Sıfır aday' DEĞİL: ölçülemedi."}
    yas = None
    try:
        t0 = _dt.datetime.fromisoformat(str(doc.get("ts")))
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=_dt.timezone.utc)
        yas = round((_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds() / 3600.0, 1)
    except (TypeError, ValueError):  # sessiz-yutma: damga yok/biçimsiz — yaş None kalır ve pano "yaş ölçülemedi" yazar (0 saat DEĞİL)
        yas = None
    return {"var": True, "kaynak": "events.jsonl", "date": doc.get("date"), "ts": doc.get("ts"),
            "yas_saat": yas, "candidates": doc.get("candidates"), "plans": doc.get("plans"),
            "armed": doc.get("armed"), "regime": doc.get("regime"),
            "open_positions": doc.get("open_positions"), "data_ok": doc.get("data_ok"),
            "halted": doc.get("halted")}


@app.get("/api/today")
def api_today(request: Request):
    _auth(request)
    d = analytics.today()
    # `inbox_count` AŞAĞIDA, `_enrich_stale_plans`TEN SONRA yazılır (v195-a): sayım artık onay
    # bekleyen REVIEW planlarını da içeriyor ve o ölçüt `expired` alanına bakıyor — burada
    # çağrılsaydı süresi dolmuş planlar da "onayını bekliyor" diye sayılırdı.
    # SON DÖNGÜ — olay penceresinden BAĞIMSIZ (v190; gerekçe `_son_dongu` başlığında).
    d["son_dongu"] = _son_dongu()
    _pf = store.read_json("portfolio.json", {}) or {}
    d["latest_session"] = _pf.get("last_date")
    # ---- KİTABIN ÜÇ ÖZET SAYISI (v191 · pano "Durum" kartı) -----------------------------------
    # NEDEN YENİ ALAN: "Durum · KİTAP" kartı dört sayıyı yan yana istiyor — sermaye, nakit,
    # GERÇEKLEŞMİŞ K/Z ve GÜN BAŞI tabanı. İlk ikisi zaten uçta (`equity`, `sermaye_koken.
    # gercek_canli_sermaye`); son ikisi kitapta VAR ama hiçbir uçtan servis edilmiyordu, yani
    # pano "gün X%" derken tabanı gösteremiyordu. `day_pnl_pct` bir ORAN; tabanı olmadan operatör
    # "neyin yüzdesi" sorusunu ekrandan cevaplayamaz.
    #
    # TÜRETME YOK, KİTAPTAN OKUMA VAR: `day_start_equity`i `equity/(1+day_pnl_pct)` diye HESAPLAMAK
    # ikinci bir taban yasası doğururdu (kitabınki ile panonunki aynı gün ayrışabilirdi — bu
    # deponun `sermaye.koken` docstring'inde yazılı "iki hesap" kusuru). Alan yoksa None kalır ve
    # kart "ölçülmedi" yazar; 0.0 yazmak "gün başında sermaye sıfırdı" demek olurdu.
    # BEYAN OFSETİ BURADA TEKRARLANMAZ: `sermaye_koken.ofset_usd/ayrisik/reset_tarihi` onu zaten
    # taşıyor ve aynı sayının iki alanı, ilk düzenlemede sessizce ayrışır.
    d["kitap"] = {"realized_pnl": _pf.get("realized_pnl"),
                  "day_start_equity": _pf.get("day_start_equity"),
                  "peak_equity": _pf.get("peak_equity")}
    # GERÇEK-CANLI SAYAÇ (BT-1, 2026-07-31). Panonun bugüne kadar gösterdiği "95 kapanmış işlem"
    # sayısı bir KARIŞIMDI: gövdesi replay tohumu (tek toplu yazım, bugünkü evrenle, survivorship'li)
    # ve satırlarda kaynak damgası yoktu — yani operatör "sistem 95 işlem yaptı" cümlesini okuyor,
    # gerçekte canlı kanıt sayısını hiçbir yerden öğrenemiyordu. Bu alan o üç sayıyı yan yana
    # koyar; hangi satırın kanıt, hangisinin training olduğu tek bakışta okunur.
    # ALAN ŞİMDİ HAZIR, PANO SONRAKİ TURDA BAĞLAR (web/* bu turda başka bir kolda).
    from . import ledgerstamp as _ls
    d["defter"] = _ls.counts()
    # SERMAYENİN KÖKENİ (sermaye tohum-ayrıştırması, 2026-08-01) — `d["equity"]`in YANINDA durmak
    # ZORUNDA. Ölçülen kusur: pano "Sermaye 94.457,91$" yazıyordu ve o sayı 100.000$ başlangıçtan
    # ANTRENMAN TOHUMUNUN (replay_seed, 95 satır) −5.542,09$'ı düşülmüş hâliydi; canlı-kâğıt işlem
    # sayısı ise SIFIR. Yani sayının kendisi doğru, ANLATTIĞI şey yanlıştı — operatör bir antrenman
    # artefaktını "sistemin kaybı" diye okuyordu. Blok üç soruyu tek bakışta cevaplar: bu para kimin
    # (gerçek-canlı sermaye), kaç gerçek işlemden geldi (canlı_islem_n), tohumun etkisi ne kadardı
    # ve hâlâ düşülüyor mu (tohum_etkisi_usd + durum + reset_tarihi).
    # HESAP `meridian.sermaye`DE, BURADA DEĞİL: `python -m meridian.sermaye --durum` ile bu uç AYNI
    # fonksiyonu çağırır — iki hesap olsaydı terminal ile pano aynı gün farklı bir "gerçek-canlı
    # sermaye" söyleyebilirdi.
    from . import sermaye as _sr
    d["sermaye_koken"] = _sr.koken()
    _enrich_stale_plans(d.get("todays_plans") or [], d["latest_session"])
    # ---- BEKLEYEN ONAY SAYIMI (v195-a · UX denetimi B2/Ö4) ------------------------------------
    # SIRA ZORUNLU: damgalama `expired`e bakar, o alan hemen yukarıda yazıldı. TEK KAYNAK:
    # `todays_plans` — sayaç da pano listesi de aynı damgalanmış listeyi okur, ikinci bir defter
    # okuması YOK.
    _onay_bekleyen_damgala(d.get("todays_plans") or [])
    d["inbox_count"] = _inbox_count(d.get("todays_plans") or [])
    return d


@app.get("/api/signals")
def api_signals(request: Request):
    _auth(request)
    # TAVAN DÜRÜSTÇE BİLDİRİLİR (2026-07-22): defterde 368 plan varken uç 120 döndürüyordu ve pano
    # "GEÇMİŞ SİNYALLER · DENETİM İZİ (110)" yazıyordu. Sayı iç tutarlıydı ama DENETİM İZİ olduğunu
    # iddia eden bir tablo, defterin üçte birini gösterip bunu söylememeliydi — operatör haklı olarak
    # "bu veri doğru değil" dedi. Tavan kalıyor (pano 368 satır çizmemeli) ama artık BEYAN ediliyor.
    _PLAN_CAP, _CAND_CAP = 120, 120
    _plans_all = store.read_jsonl("trade_plans.jsonl")
    _cands_all = store.read_jsonl("candidates.jsonl")
    cands = _cands_all[-_CAND_CAP:]
    plans = _plans_all[-_PLAN_CAP:]
    # freshness/forward-looking context: candidates are closed-bar signals ARMED FOR THE NEXT OPEN. Report
    # how fresh the data is (last processed session) and which is the newest session that produced a signal,
    # so the page can lead with "next session, data as of X" instead of reading like a backward-looking log.
    regime = store.read_json("regime.json", {})
    provider = "FMP" if __import__("meridian.adapters.fmp", fromlist=["available"]).available() else "Cboe (gecikmeli)"
    latest_signal = max([p.get("date") for p in plans if p.get("date")], default=None)
    latest_session = (store.read_json("portfolio.json", {}) or {}).get("last_date")
    _enrich_stale_plans([p for p in plans if p.get("date") == latest_signal], latest_session)
    return {
        "latest_session": latest_session,
        "candidates": list(reversed(cands)), "plans": list(reversed(plans)),
            "as_of": regime.get("date") or (store.read_json("portfolio.json", {}) or {}).get("last_date"),
            "latest_signal_date": latest_signal, "data_provider": provider,
            # yerel LLM ajanının aday İNCELEMESİ — danışma katmanı: kapı kararını asla değiştirmez
            "candidate_review": store.read_json("candidate_review.json", {}),
            # KIRPMA BEYANI: pano "denetim izi" derken defterin tamamını gösterdiğini sanmasın.
            "ledger": {"plans_total": len(_plans_all), "plans_shown": len(plans),
                       "candidates_total": len(_cands_all), "candidates_shown": len(cands),
                       "cap": _PLAN_CAP}}


@app.get("/api/market")
def api_market(request: Request):
    """İzlenen evrenin TAMAMI (state/bars/*.csv + finviz keşfinin bars'ta olmayan ekstraları).

    EOD KAPANIŞ verisidir — bu uç CANLI FİYAT SERVİS ETMEZ ve etmediğini `as_of` (evrendeki en
    taze seans) ile birlikte söyler. Barı `as_of`tan geride kalan semboller `stale_n` ile sayılır.
    Ölçülemeyen her alan None döner; pano onu "—" gösterir (bkz. marketview modül başlığı)."""
    _auth(request)
    from . import marketview
    return marketview.build()


@app.get("/api/agent")
def api_agent(request: Request):
    """Sürüm ekseninin kanonik yüzeyi: karne defteri + hipotezler + kalibrasyon.

    D3-UI'DA İKİ OKUMA EKLENDİ (C1-5, C1-6) VE İKİSİ DE BURAYA AİT: rollback sicili ile regresyon
    kırılımı `scoreboard.versions` üstünde yaşar, o da bu ucun ana yükü. Ayrı bir uca koymak,
    aynı defteri iki uçtan servis etmek olurdu. `analytics.agent_view()` DEĞİŞTİRİLMEDİ —
    zenginleştirme uç katmanında, yalnız okuma."""
    _auth(request)
    return {**analytics.agent_view(),
            "rollback": _rollback_sicili(),        # C1-5: "kendini gerçekten geri alıyor mu?"
            "regresyon": _regresyon_kirilimi()}    # C1-6: "neyi düzeltti, NEYİ BOZDU"


@app.get("/api/memory")
def api_memory(request: Request):
    _auth(request)
    p = config.STATE / "lessons.md"
    return {"lessons_md": p.read_text() if p.exists() else "_No lessons yet._",
            "hypotheses": memory.all_hypotheses()}


@app.get("/api/skills")
def api_skills(request: Request):
    from . import skill_evolve as _se
    _auth(request)
    from . import skills
    skills.reconcile_enablement()          # 'auto-enable when the key lands' — reflect current key state
    reg = store.read_json("skills_registry.json", {"skills": {}})
    sk = reg.get("skills", {})
    reg["counts"] = {                      # recompute LIVE so the top cards track reconcile, not a stale field
        "total": len(sk),
        "enabled": sum(1 for i in sk.values() if i.get("enabled")),
        "disabled": sum(1 for i in sk.values() if not i.get("enabled")),
        "active_in_pipelines": sum(1 for i in sk.values() if i.get("enabled") and i.get("pipeline")),
    }
    reg["catalog"] = skills.catalog()                       # names + descriptions + live avg_r per skill
    reg["recommendations"] = skills.pending_recommendations()   # Axis-2 notes awaiting the operator
    reg["revisions"] = _se.pending_drafts()                 # v10 #5: onay bekleyen revizyon taslakları
    reg["revision_history"] = __import__("meridian.skill_evolve", fromlist=["revisions"]).revisions()[-10:]
    # KOŞU DEFTERİ PANOYA BAĞLANIYOR (K1, 2026-07-30). `pipeline_runs.jsonl` her skill koşusunda
    # satır yazıyor ve tek okuyucusu /api/pipeline_runs'tı — o ucu ise HİÇBİR istemci çağırmıyordu.
    # Artefakt yasası tatmin görünüyordu (modüller-arası read_jsonl VAR), ama zincir bir kat
    # yukarıda, HTTP→DOM katmanında kopuktu: statik Python grafı JS'i göremez. skills.py:3'ün
    # "ajanın yaptığı hiçbir şey görünmez değildir" vaadi panoda karşılıksızdı.
    # `skills_declared_not_run` BİLEREK taşınıyor: "beyan edildi ama koşmadı" tam olarak Hermes'in
    # 14 düğmede dönmesiyle aynı sınıf bir körlük kanıtıdır ve yalnız bu defterde ölçülüyor.
    reg["recent_runs"] = list(reversed(store.read_jsonl("pipeline_runs.jsonl")[-12:]))
    return reg


@app.post("/api/skills/revision")
async def api_skill_revision(request: Request):
    """v10 #5 — skill revizyon taslağı: operatör onayı (apply) ya da ret (reject). Taslaklar ajan
    tarafından yazılır ama YALNIZ burada, insan kararıyla yürürlüğe girer."""
    _auth(request)
    body = await request.json()
    skill, action = str(body.get("skill") or ""), str(body.get("action") or "")
    from . import skill_evolve
    if action == "apply":
        out = skill_evolve.apply_revision(skill)
        _diag_onbellek_bosalt("skill_revision_apply")
        return out
    if action == "reject":
        out = skill_evolve.reject_revision(skill)
        _diag_onbellek_bosalt("skill_revision_reject")   # taslak kuyruğu kısaldı: eksen-2 sayacı değişti
        return out
    raise HTTPException(status_code=400, detail="action: apply|reject")


@app.post("/api/skills/apply")
async def api_skills_apply(request: Request):
    """Apply a reversible Axis-2 skill action (shadow/activate). Operator-gated — the deterministic
    backtest cannot validate LLM-skill impact, so a human approves what the brain recommends."""
    _auth(request)
    from . import skills
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="expected JSON {skill, action}")
    skill, action = (body or {}).get("skill"), (body or {}).get("action")
    res = skills.apply_skill_action(skill or "", action or "")
    if res.get("ok"):
        obs.log("skill_action_applied", skill=skill, action=action)
        _diag_onbellek_bosalt("skill_action")     # YALNIZ ok: reddedilen eylem hiçbir şeyi değiştirmedi
    return res


@app.get("/api/plots")
def api_plots(request: Request):
    """ŞERİT PARSEL HARİTASI — kurulum × rejim verim matrisi, kapanmış işlemlerden hesaplanır.

    Bir tarla denemesinin okuduğu şeyi okur: hangi uygulama (setup) hangi koşulda (regime) ne
    verdi, VE her hücrede kaç parsel var. `n` kasten dışarı verilir çünkü pano onu yoğunluk
    olarak çizer — 3 işlemlik bir hücre seyrek görünür, 55 işlemlik hücre dolu. Az örnekli bir
    ortalamayı çok örnekliymiş gibi göstermek bu sistemin reddettiği tek şeydir.

    Hiçbir değer uydurulmaz: veri yoksa hücre `null` döner ve ekilmemiş parsel olarak çizilir."""
    _auth(request)
    trades = store.read_jsonl("trades.jsonl")
    cells: dict[str, dict[str, dict]] = {}
    setups: list[str] = []
    regimes: list[str] = []
    for t in trades:
        s, rg = t.get("setup"), t.get("regime")
        if not s or not rg:
            continue                                   # eksik etiketli işlem sayıma girmez
        if s not in setups:
            setups.append(s)
        if rg not in regimes:
            regimes.append(rg)
        c = cells.setdefault(s, {}).setdefault(rg, {"n": 0, "sum_r": 0.0, "wins": 0, "t": []})
        c["n"] += 1
        c["sum_r"] += float(t.get("r_multiple") or 0.0)
        c["wins"] += 1 if (t.get("r_multiple") or 0) > 0 else 0
        c["t"].append(t)
    grid = []
    for s in setups:
        row = []
        for rg in regimes:
            c = cells.get(s, {}).get(rg)
            if not c:
                row.append(None)
                continue
            # çekmece için o parselin SON işlemleri — matris arayüzün kendisi olduğundan
            # hücreye tıklayınca inilecek kayıt buradan gelir, ayrı bir tur gerekmez.
            recent = [{
                "ticker": x.get("ticker"),
                "r": x.get("r_multiple"),
                "pnl_pct": x.get("pnl_pct"),
                "opened": (x.get("ts_open") or "")[:10],
                "closed": (x.get("ts_close") or "")[:10],
                "bars": x.get("bars_held"),
                "exit": x.get("exit_reason"),
            } for x in c["t"][-12:]][::-1]
            exits: dict[str, int] = {}
            for x in c["t"]:
                k = x.get("exit_reason") or "—"
                exits[k] = exits.get(k, 0) + 1
            row.append({
                "n": c["n"],
                "mean_r": round(c["sum_r"] / c["n"], 3),
                "hit": round(c["wins"] / c["n"], 3),
                "exits": sorted(exits.items(), key=lambda kv: -kv[1]),
                "recent": recent,
            })
        grid.append({"setup": s, "cells": row})
    return {
        "setups": setups,
        "regimes": regimes,
        "grid": grid,
        "n_trades": sum(1 for t in trades if t.get("setup") and t.get("regime")),
        "n_trades_total": len(trades),
    }


def _slippage_measured(trades: list[dict], goal: dict) -> dict:
    """ÖLÇÜLEN SLİPAJ vs VARSAYILAN SLİPAJ (K1, 2026-07-30).

    `loop.py:998-1000` kapanan işlemlere `alpaca_fill_price` + `mirror_divergence` geri-yazıyor ve
    gerekçesi açık: "real-world slippage vs the model is measurable". Ama ölçülen sapmayı
    `goal.slippage_bps`e (ya da herhangi bir kalibrasyon raporuna) geri besleyen tüketici YOKTU —
    döngünün kapanan ucu hiç kurulmamıştı. Model tarafı sabit: goal.yaml:27 slippage_bps: 5.

    UYDURMA YASAĞI: ayna henüz hiçbir satırı yamamadı (canlı sayım 2026-07-30: 0/95). O yüzden
    `measured_bps` None döner — 0.0 dönmek "ölçtük ve slipaj yok" gibi okunurdu, oysa doğru cümle
    "ayna daha hiç dolmadı". Ayna dolmaya başladığı GÜN bu satır kendiliğinden sayı gösterir ve
    sabit 5bps varsayımı ilk kez ölçüme karşı sınanabilir olur."""
    div = [float(t["mirror_divergence"]) for t in trades
           if t.get("mirror_divergence") is not None]
    assumed = float(goal.get("slippage_bps") or 0.0)
    if not div:
        return {"assumed_bps": assumed, "measured_bps": None, "n": 0,
                "note": "ayna hiç satır yamamadı — ölçülen slipaj YOK (0.0 değil, None)"}
    div.sort()
    mid = len(div) // 2
    med = div[mid] if len(div) % 2 else (div[mid - 1] + div[mid]) / 2.0
    return {"assumed_bps": assumed, "measured_bps": round(med, 2), "n": len(div),
            "worst_bps": round(div[-1], 2),
            "note": "medyan |ayna sapması|; varsayılan goal.slippage_bps ile yan yana okunur"}


def _y3_gate_row() -> dict:
    """Y3'ün iki PİYASA GÖSTERGESİNİN canlı hükmü + iki PORTFÖY tavanının knob durumu (3b).

    EDG-005 HÜKMÜ (2026-08-01): SMA/VIX bacakları KAPI DEĞİL, GÖSTERGEdir — ve bu satır artık onların
    TEK tüketicisidir (guard'daki tüketici ile `build_regime_json`daki üretici kaldırıldı). Yani
    burada gösterilen hüküm hiçbir karar yoluna girmez; `regime.entry_gates()` bunu `karar_yolu:
    False` + `beyan` alanlarıyla çıktının İÇİNDE söyler, pano metnine güvenmek zorunda kalmayalım.
    Hüküm kapı olmasa da HESAPLANIR: SPY'ın 200-SMA'sının altında mı üstünde mi olduğu, kapının
    elenmesinden bağımsız bir piyasa okumasıdır (ve o eleme kararının kanıt zinciri buradan geçti).
    Endeks barları okunamazsa satır `veri_yok` der, sessizce "hüküm üstünde" demez."""
    from . import regime as _rg, config as _cfg
    params = {}
    try:
        params = dict((_cfg.load_strategy() or {}).get("params") or {})
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        params = {}
    bars = None
    try:
        import datetime as _dt
        from .adapters import data as _d
        bars = _d.load_bars(_d.INDEX_SYMBOL, "2024-01-01", _dt.date.today().isoformat(),
                            use_cache=True)
    except Exception as e:
        from . import obs as _o
        _o.warn("y3_gate_row_bars_unavailable", error=f"{type(e).__name__}: {e}",
                detail="endeks barları okunamadı — SPY 200-SMA kapısının hükmü ÜRETİLMEDİ")
    out = _rg.entry_gates(bars, params)
    out["portfolio_caps"] = {
        "sector_cap_pct": float(params.get("portfolio.sector_cap", 0) or 0),
        "heat_cap_pct": float(params.get("portfolio.heat_cap", 0) or 0),
        "enabled": bool(float(params.get("portfolio.sector_cap", 0) or 0) > 0
                        or float(params.get("portfolio.heat_cap", 0) or 0) > 0),
        "not": ("ikisi de 0 = KAPALI. Isı tavanı açıldığı gün `analytics.portfolio_heat` ilk kez "
                "bir KAPIYA bağlanır; 3a'nın 'YALNIZ GÖSTERGE' beyanı o güne dek geçerlidir."),
    }
    return out


def _benchmark_veto_tally() -> dict:
    """`hypotheses.vs_benchmark_at_ship` SAYACI (K1, 2026-07-30).

    reflect.py:721 her ship'e `analytics.benchmark_relative()` anlık görüntüsü damgalıyor ve
    yorumu şunu söylüyor: "20-30 gözlem birikince kapıya eklenip eklenmeyeceğine VERİYLE karar
    verilir". Ama alanın repo genelinde tek okuyucusu damgalandığını doğrulayan bir testti — ne
    pano ne API servis ediyordu, ve o kararı tetikleyecek SAYAÇ hiç yazılmamıştı. Yani alan
    sonsuza dek sessizce birikecek, karar anı ASLA gelmeyecekti. Eşiğin görünür sayacı budur."""
    rows = [h.get("vs_benchmark_at_ship") for h in memory.all_hypotheses()]
    rows = [r for r in rows if isinstance(r, dict)]
    beat = sum(1 for r in rows if r.get("beat_benchmark") is True)
    lost = sum(1 for r in rows if r.get("beat_benchmark") is False)
    return {"n": len(rows), "beat": beat, "lost": lost,
            # Eşik reflect.py:721 yorumundan gelir; sayaç onu YENİDEN tanımlamaz, gösterir.
            "decision_n": 20,
            "ready": len(rows) >= 20,
            "note": ("her ship'e damgalanan 'SPY'ı geçti mi' anlık görüntüsü; 20 gözlemde kapıya "
                     "eklenip eklenmeyeceğine veriyle karar verilir (reflect.py:721)")}


@app.get("/api/performance")
def api_performance(request: Request):
    _auth(request)
    goal = config.goal()
    trades = store.read_jsonl("trades.jsonl")
    return {
        "equity_curve": store.read_json("equity_curve.json", {"points": []}),
        "score_detail": analytics.score_mod.score_detail(trades, goal),
        "kelly": analytics.score_mod.kelly_fraction(trades),          # realized-edge sizing ceiling (advisory)
        "tail_risk": analytics.score_mod.tail_risk(trades),           # block-bootstrap VaR/CVaR
        # ÖLÇÜLEN SLİPAJ (K1): sabit 5bps varsayımının yanına ölçülen medyan. Ayna dolana kadar
        # None — panoda "henüz ölçülmedi" olarak çizilir, sıfır olarak DEĞİL.
        "slippage_measured": _slippage_measured(trades, goal),
        "benchmark_relative": analytics.benchmark_relative(),         # alpha vs just holding SPY (#33)
        "per_regime": analytics.per_regime_scores(goal),
        "per_skill": analytics.per_skill_hit_rate(),
        "n_trades": len(trades),
        "recent_trades": list(reversed(trades[-40:])),
        "holdout_note": "Frozen holdout (2026) reported to human only; never drives acceptance.",
    }


@app.get("/api/report.csv")
def api_report_csv(request: Request):
    """Closed-trade ledger as CSV for the operator's own spreadsheet/records. Read-only export."""
    _auth(request)
    import csv
    import io
    trades = store.read_jsonl("trades.jsonl")
    cols = ["id", "ticker", "side", "ts_open", "ts_close", "entry", "exit", "qty", "r_multiple",
            "pnl_dollars", "pnl_pct", "costs", "exit_reason", "bars_held", "regime", "strategy_version"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for t in trades:
        w.writerow(t)
    return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=meridian_trades.csv"})


@app.get("/api/digest", response_class=PlainTextResponse)
def api_digest(request: Request):
    """A plain-language daily digest — the same numbers as the dashboard, as copy-pasteable text."""
    _auth(request)
    goal = config.goal()
    hb = store.read_json("heartbeat.json", {})
    rj = store.read_json("regime.json", {})
    pf = store.read_json("portfolio.json", {})
    ec = store.read_json("equity_curve.json", {"points": []}).get("points", [])
    tod = analytics.today()
    trades = store.read_jsonl("trades.jsonl")
    sd = analytics.score_mod.score_detail(trades, goal)
    dq = store.read_json("data_quality.json", {})
    # source live fields defensively — the seed heartbeat carries fewer keys than a live-cycle one
    date = hb.get("last_bar") or pf.get("last_date") or rj.get("date") or "?"
    regime = hb.get("regime") or rj.get("regime") or "?"
    budget = hb.get("exposure_budget_pct", rj.get("exposure_budget_pct", "?"))
    equity = hb.get("equity") or (ec[-1][1] if ec and isinstance(ec[-1], (list, tuple)) else "?")
    open_pos = hb.get("open_positions", len(pf.get("positions", {})))
    lines = [
        "MERIDIAN — GÜNLÜK ÖZET",
        f"Tarih         : {date}",
        f"Rejim         : {regime}  (risk bütçesi %{budget})",
        f"Sermaye       : ${equity}",
        f"Açık pozisyon : {open_pos}   Kurulan plan: {tod.get('pending_count', 0)}",
        f"Gün P&L       : {round(100 * hb.get('day_pnl_pct', 0.0), 2)}%",
        f"Devre kesici  : {'AÇIK' if hb.get('breaker_tripped') else 'kapalı'}   "
        f"Durdurma: {'AKTİF' if hb.get('halted') else 'hayır'}   "
        f"Veri: {'sağlam' if hb.get('data_ok', True) else 'ŞÜPHELİ'}",
        "",
        f"Kapanan işlem : {sd.get('n', 0)} (min örnek {sd.get('min_sample', goal.get('min_sample'))})",
        f"Skor          : {sd.get('score')}   avg_R: {sd.get('avg_r')}   isabet: {sd.get('win_rate')}",
        f"Maks. düşüş    : {sd.get('max_drawdown')}   Sharpe: {sd.get('sharpe')}",
        "",
        "Not: kağıt (paper) işlem — gerçek para yok. Frozen holdout kabule etki etmez.",
    ]
    return "\n".join(lines)


# ---------- secret entry (operator pastes keys; values never logged/echoed) ----------
@app.get("/api/secrets")
def api_secrets(request: Request):
    """Which known keys are set, their source, and a masked hint. Never returns a full value."""
    _auth(request)
    # VARSAYILAN MODEL ADLARI KODDAN TÜRETİLİR (K1, 2026-07-30). Pano "Boşsa gemini-2.5-pro."
            # yazıyordu; kod ise `GEMINI_DEFAULT_MODEL = "gemini-3.1-pro"` (operatör tercihi
            # 2026-07-19) kullanıyor. Yani operatör alanı boş bıraktığında panonun söylediği model
            # ile GERÇEKTE koşan model farklıydı — çelişik varsayılan dokümantasyonu, ve panoya
            # bakarak "hangi model koşuyor?" sorusunun cevabı YANLIŞ okunuyordu. Metin artık sabitin
            # KENDİSİNDEN gelir: sabit değişince pano kendiliğinden doğru söyler, elle senkron yok.
    from . import hermes as _hm_defaults
    return {"secrets": secrets_mod.status(),
            "live_enabled": config.live_enabled(),
            # MOD ÖLÇÜMDEN GELİR (v196/KALEM-1). Panonun "Güvenlik durumu" kartı modu KODA ÇAKILMIŞ
            # bir dizeden ("paper") basıyordu: modun doğruluğunu iddia eden kart, `MERIDIAN_MODE=live`
            # olduğu gün sessizce yanlış söylerdi. `live_enabled` bunu KAPATMAZ — o bayrak iki
            # koşulun VE'sidir (mod + risk kabulü); "mod live ama risk kabulü yok" hâlinde
            # `live_enabled` false döner ve kart yine "paper" derdi. İki alan iki ayrı soruya cevap.
            "mode": config.MODE,
            "autonomy_level": config.limits()["autonomy_level"],
            "model_defaults": {"GEMINI_MODEL": _hm_defaults.GEMINI_DEFAULT_MODEL,
                               "NOUS_MODEL": getattr(_hm_defaults, "NOUS_DEFAULT_MODEL", None)},
            "note": "Veri ve kağıt-broker anahtarı girmek CANLI işlemi açmaz; sistem L0 kağıt modunda kalır."}


@app.post("/api/secrets/{name}")
async def api_set_secret(name: str, request: Request):
    """Store one KNOWN key from the request BODY (never the URL). Whitelisted names only. The value is
    written to the local 0600 store and is never logged, echoed, or returned — only a masked status."""
    _auth(request)
    if name not in secrets_mod.ALLOWED:
        raise HTTPException(status_code=400, detail="unknown secret name")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="expected JSON body {\"value\": \"...\"}")
    value = body.get("value") if isinstance(body, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail="missing non-empty 'value'")
    secrets_mod.set(name, value)
    obs.log("secret_updated", name=name)          # NAME only — never the value
    from . import skills
    rec = skills.reconcile_enablement()           # a data/broker key may flip key-gated skills on
    local_agent = None
    if name in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        # tek giriş noktası ARAYÜZ: Gemini anahtarı/modeli panodan girilince YEREL hermes-agent'a da
        # otomatik taşınır (operatör isteği — terminal/.env adımı yok). Değer asla loglanmaz.
        try:
            from . import hermes
            local_agent = hermes.sync_local_agent_gemini(enable=True)
        except Exception as e:
            # `senkron_ts` BU DALDA DA ZORUNLU (ders (b), 2026-08-02). `sync_local_agent_gemini`
            # kendi dönüşlerinin üçünde de damga taşıyor; import/çağrı bacağı düşerse damgasız
            # bir sözlük dönerdi ve panonun okuduğu satır "damga yok" derdi — oysa ölçüm ANI
            # burada BİLİNİYOR. Damgayı atlamak, bilinen bir zamanı bilinmiyor göstermekti.
            local_agent = {"ok": False, "detail": f"senkron hatası ({type(e).__name__})",
                           "senkron_ts": memory.now_iso()}
    _diag_onbellek_bosalt("secret_set")           # sağlayıcı/beceri durumu değişti (maskeli alanlar)
    return {"ok": True, "name": name, "status": secrets_mod.status().get(name),
            "skills_enabled": rec["changed"], "local_agent": local_agent}


@app.delete("/api/secrets/{name}")
def api_delete_secret(name: str, request: Request):
    _auth(request)
    if name not in secrets_mod.ALLOWED:
        raise HTTPException(status_code=400, detail="unknown secret name")
    secrets_mod.delete(name)
    obs.log("secret_cleared", name=name)
    from . import skills
    rec = skills.reconcile_enablement()           # removing a key disables its dependent skills again
    local_agent = None
    if name == "GEMINI_API_KEY":
        try:
            from . import hermes
            local_agent = hermes.sync_local_agent_gemini(enable=False)   # yedeklenen Nous ayarına dön
        except Exception as e:
            local_agent = {"ok": False, "detail": f"senkron hatası ({type(e).__name__})",
                           "senkron_ts": memory.now_iso()}          # bkz. POST dalındaki gerekçe
    _diag_onbellek_bosalt("secret_cleared")       # POST dalıyla aynı gerekçe, ters yön
    return {"ok": True, "name": name, "status": secrets_mod.status().get(name),
            "skills_disabled": rec["changed"], "local_agent": local_agent}


@app.get("/api/secrets/test/{provider}")
def api_test_secret(provider: str, request: Request):
    """Live reachability + auth check for a stored key. Returns only {ok, detail} — never the key."""
    _auth(request)
    if provider == "fmp":
        from .adapters import fmp
        return fmp.ping()
    if provider == "fmp_backup":
        from .adapters import fmp
        return fmp.ping(which="FMP_API_KEY_2")      # YEDEK anahtarı hedefli test (rotasyon yok)
    if provider == "finviz":
        from .adapters import finviz
        return finviz.ping()
    if provider == "massive":
        from .adapters import massive
        return massive.ping()                       # /v3/reference/tickers?limit=1 — TEK ucuz çağrı
                                                    # (grouped ~12.400 satır indirirdi; 5/dk sınırı var)
    if provider == "alpaca":
        from .adapters import alpaca
        return alpaca.ping() if hasattr(alpaca, "ping") else {"ok": False, "detail": "test desteklenmiyor"}
    if provider in ("gemini", "nous"):
        from . import hermes
        return hermes.ping_brain(provider)
    raise HTTPException(status_code=400, detail="unknown provider")


@app.post("/api/control/halt")
async def api_control_halt(request: Request):
    """EMEKLİ İKİZ — DAVRANIŞI /api/halt'a DELEGE EDER (K1, 2026-07-30).

    Bu uç, `/api/halt`ın ölü ikiziydi ve tehlikeli biçimde SESSİZDİ: `/api/halt` obs.alarm +
    notify.halted + heartbeat notu üretirken bu yol yalnız `obs.log` basıyordu. Yani ikizden HALT
    basılsa Telegram bildirimi ve alarm HİÇ çıkmazdı. Pano ve telefon /halt sayfası her zaman
    `/api/halt`-`/api/resume` çağırdı; bu ucun repo genelinde çağıranı yoktu (yalnız yetki-sınırı
    testleri). Tuzak şuydu: aynı ailenin `control/learn_halt` ve `control/cancel_open` üyeleri
    KULLANILIYOR — simetriye bakan biri yarın halt'ı da `control/*`a taşırsa bildirim sessizce
    kaybolurdu. `guard.check_trade`'in "iki yüzey sessizce ayrıştı" dersinin HTTP katındaki hâli.

    NEDEN SİLİNMEDİ, DELEGE EDİLDİ: rota silinse ona bugün inanan bir istemci 404 alır ve HALT
    isteği SESSİZCE düşer — emeklilik, davranışı yok etmek değil TEKLEŞTİRMEK olmalı. Artık tek
    bir halt yolu var: gövde `/api/halt`/`/api/resume`a delege eder, yan etkiler (alarm+bildirim)
    otomatik olarak aynıdır ve bir daha ayrışamaz."""
    _auth(request)
    body = await request.json()
    on = bool(body.get("on"))
    obs.log("control_halt", on=on, source="dashboard",
            detail="EMEKLİ ikiz — /api/halt yoluna delege edildi (tek halt yolu)")
    # Tek yol: yetkilendirme yukarıda yapıldı, yan etkiler kanonik uçların içinde yaşıyor.
    return api_halt(request) if on else api_resume(request)


@app.post("/api/intraday-arm")
async def api_intraday_arm(request: Request):
    """Faz 4 INTRADAY SİLAHLANMA bayrağı (state/INTRADAY_ARM). Default KAPALI = yalnız gözlem. Açmak
    otonom intraday emrin KAPISINI kaldırır — ama Faz 4b (gerçek silahlanma bacağı) henüz uygulanmadı,
    o yüzden şu an açmak yalnız bir uyarı üretir. HALT tuşunun ikizi; yalnız operatör açar."""
    _auth(request)
    body = await request.json()
    on = bool(body.get("on"))
    now = health.set_intraday_arm(on)
    obs.log("intraday_arm", on=now, source="dashboard")
    _diag_onbellek_bosalt("intraday_arm")
    return {"intraday_armed": now}


@app.post("/api/control/learn_halt")
async def api_control_learn_halt(request: Request):
    """Faz 3 kademe-4 Halt Learning: işlemler sürer; Hermes yeni versiyon SHIP EDEMEZ (reflect.submit
    erken döner, bekleme döngüsü duraklar). Rollback güvenlik olarak açık kalır."""
    _auth(request)
    body = await request.json()
    on = bool(body.get("on"))
    now = health.set_learn_halt(on)
    obs.log("control_learn_halt", on=now, source="dashboard")
    _diag_onbellek_bosalt("learn_halt")
    return {"learn_halted": now}


@app.post("/api/control/cancel_open")
def api_control_cancel_open(request: Request):
    """Faz 3 kademe-2 Cancel-Open: yalnız DOLMAMIŞ giriş emirlerini iptal eder; dolu pozisyonların
    koruyucu bacaklarına asla dokunmaz (çıplak pozisyon yasağı)."""
    _auth(request)
    from .adapters import alpaca
    res = alpaca.cancel_open_entries()
    obs.log("control_cancel_open", cancelled=len(res.get("cancelled", [])),
            kept=len(res.get("kept", [])), ok=res.get("ok"))
    # YALNIZ GERÇEKTEN İPTAL VARSA: `ok` ama sıfır iptal, hiçbir teşhis alanını kıpırdatmaz.
    if res.get("ok") and res.get("cancelled"):
        _diag_onbellek_bosalt("cancel_open")
    return res


@app.get("/api/debug_export")
def api_debug_export(request: Request):
    """Faz 3 (5c) — Debug Export: state kök dosyaları (json/jsonl/yaml) + son olaylar tek zip.
    secrets.json ve bars/ KESİNLİKLE dışarıda: anahtar sızdırmayan, paylaşilabilir teşhis paketi."""
    _auth(request)
    import io, zipfile, datetime as _dt
    buf = io.BytesIO()
    skip = {"secrets.json"}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(config.STATE.iterdir()):
            if not f.is_file() or f.name in skip or f.suffix not in (".json", ".jsonl", ".yaml", ".csv"):
                continue
            if f.stat().st_size > 5_000_000:           # dev dosya (ör. tam events) → kuyruğu al
                with f.open("rb") as fh:
                    fh.seek(-2_000_000, 2)
                    z.writestr(f"state/{f.name}.tail", fh.read())
            else:
                z.write(f, f"state/{f.name}")
        z.writestr("manifest.json", json.dumps({
            "exported_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "mode": config.MODE, "broker": config.BROKER,
            "note": "secrets.json ve bars/ bilinçli olarak HARİÇ"}, indent=2))
    from fastapi.responses import Response
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition":
                             f"attachment; filename=meridian-debug-{_dt.date.today()}.zip"})


# K1-EMEKLİ: kanonik yüzey /api/diagnostics `selfreview_summary`. Yeni tüketici bağlanmaz.
@app.get("/api/selfreview")
def api_selfreview(request: Request):
    """v11 #2 — öz-değerlendirme: her çağrıda taze üretilir (ucuz okuma-sentezi); haftalık koşum
    ayrıca bildirim atar. Rapor ajanın kanıt paketine de girer."""
    _auth(request)
    from . import selfreview
    return selfreview.build()


@app.get("/api/alerts")
def api_alerts(request: Request):
    """YEREL ALARM GELEN KUTUSU (2026-07-26). Uzak kanal (Telegram/webhook) yapılandırılmamışsa
    alarmlar bugüne kadar yalnız bir SAYACA yazılıp kayboluyordu. Burada kaybolmuyorlar: kaynak
    yine `events.jsonl` (ikinci defter YOK), bu uç yalnız ACK'lenmemiş olanları imzaya göre
    gruplayıp gösterir."""
    _auth(request)
    from . import notify
    return notify.inbox()


@app.post("/api/alerts/ack")
def api_alerts_ack(request: Request):
    """'Gördüm' işareti — hiçbir alarmı SİLMEZ, yalnız gelen kutusunun okunma sınırını ilerletir.
    Kanalın YOKLUĞU bu işaretle kapanmaz (watchdog `notify_channel` satırı ayrı ve ACK'lenemez):
    operatörün 'okudum'u bir bildirim kanalını var edemez."""
    _auth(request)
    from . import notify, memory, obs
    _before = notify.inbox()
    # ACK ZAMANI 'ŞİMDİ' DEĞİL, GÖRÜLEN EN YENİ OLAYIN ZAMANIDIR (2026-07-26). `now_iso()` yazmak
    # aynı-saniye yarışını operatörün aleyhine çözüyordu: gelen kutusu okunduktan SONRA, ACK
    # yazılmadan ÖNCE düşen bir alarm (olaylar saniye çözünürlüklü) `ts <= ack_ts` olduğu için bir
    # daha hiç görünmeden "okundu" sayılıyordu — ve tam da o alarm, en taze olan, en kritik olabilir.
    # Sınır yalnız GERÇEKTEN GÖSTERİLMİŞ en yeni olaya kadar ilerler; ötesi görülmemiştir.
    _seen_max = max((str(g.get("last_ts") or "") for g in (_before.get("groups") or [])),
                    default="")
    doc = {"ack_ts": _seen_max or memory.now_iso(), "ack_by": "operator",
           # SOĞURULAN YIĞIN (2026-07-26): `notify_undelivered.json` KÜMÜLATİF bir sayaçtır ve
           # hiçbir zaman azalmaz; operatör hepsini okusa bile makullük satırı sonsuza dek kırmızı
           # kalıyordu — kalıcı kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır (kimse bakmaz).
           # Buraya YAZILAN sayı, "bu ana kadar birikmişi gördüm" demektir; bekçi kalıntıyı
           # (toplam − soğurulan) raporlar. Sayacın kendisi ASLA sıfırlanmaz: yapısal boşluğun
           # tarihi kaybolmaz, yalnız görülmüş kısmı düşülür.
           "absorbed": int((store.read_json("notify_undelivered.json", {}) or {}).get("_toplam") or 0)}
    store.write_json(notify.ACK_FILE, doc)
    # İZ: operatörün yaptığı her değişiklik kayıtlı olmalı — "bu alarmları kim, ne zaman kapattı"
    # sorusu cevapsız kalamaz. Kapanan alarm SAYISI da yazılır ki iz, eylemin büyüklüğünü taşısın.
    obs.log("alerts_acked", pending_before=_before.get("pending"),
            groups=len(_before.get("groups") or []), channel_configured=_before.get("channel_configured"),
            ack_ts=doc["ack_ts"], absorbed=doc["absorbed"], ack_by=doc["ack_by"])
    _diag_onbellek_bosalt("alerts_ack")
    return {"acked": True, **doc, "inbox": notify.inbox()}


@app.post("/api/broker_reject/ack")
async def api_broker_reject_ack(request: Request):
    """Reddedilen gönderimleri 'gördüm' diye kapat — hiçbirini SİLMEZ.

    Şerit beş gündür 'senden bir şey bekliyor · 4 emir reddedildi' diyordu ve kapatmanın yolu yoktu;
    kalıcı bir kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır. Kapatılan satır defterde tam
    alanlarıyla kalır (`acked` listesi + ack_ts), yalnız şeridi besleyen sayının dışına çıkar.

    Gövde: {"keys": ["plan_id·date", ...]} ya da {"all": true} (o anki AÇIK listenin tamamı).
    Tanınmayan anahtar SESSİZCE yutulmaz — yanıtta `unknown` olarak döner: operatörün kapattığını
    sandığı ama kapanmamış bir ret, tam da bu mekanizmanın önlemek için var olduğu şeydir."""
    _auth(request)
    body = await request.json()
    rc = store.read_json("broker_reconcile.json", {}) or {}
    mevcut = {health.reject_key(r): r for r in (rc.get("failed_submissions") or [])}
    if body.get("all"):
        # YALNIZ AÇIK OLANLAR: `all` "ekranda gördüğüm hepsi" demektir; zaten kapatılmışların
        # ack_ts'ini bugüne çekmek, kaydın ne zaman görüldüğü bilgisini bozardı.
        istenen = [health.reject_key(r) for r in health.split_rejections(
            rc.get("failed_submissions"))["open"]]
    else:
        istenen = [str(k) for k in (body.get("keys") or [])]
    bilinen = [k for k in istenen if k in mevcut]
    unknown = [k for k in istenen if k not in mevcut]
    ts = memory.now_iso()

    def _mut(doc):
        yeni = 0
        for k in bilinen:
            if k not in doc:                       # İDEMPOTENT: ikinci ack ilk görülme anını EZMEZ
                doc[k] = {"ack_ts": ts, "ack_by": "operator",
                          "ticker": (mevcut.get(k) or {}).get("ticker")}
                yeni += 1
        return bool(yeni)

    store.update_json(health.REJECT_ACK_FILE, _mut, default={})
    bolunmus = health.split_rejections(rc.get("failed_submissions"))
    # İZ: operatörün yaptığı her değişiklik kayıtlı olmalı — "bu retleri kim, ne zaman kapattı".
    obs.log("broker_rejects_acked", acked_n=len(bilinen), unknown_n=len(unknown), ack_ts=ts,
            open_after=len(bolunmus["open"]), ack_by="operator")
    # YALNIZ TANINAN ANAHTAR KAPANDIYSA: tamamı `unknown` olan bir istek defteri değiştirmez.
    if bilinen:
        _diag_onbellek_bosalt("broker_reject_ack")
    return {"acked_n": len(bilinen), "unknown": unknown, "ack_ts": ts,
            "open": len(bolunmus["open"]), "acked": len(bolunmus["acked"])}


# ==================================================================================================
# SAĞLAYICI SAĞLIK KARTI (temizlik turu, 2026-07-30 — ROADMAP 5.2'nin çekirdeği)
# ==================================================================================================
# TEŞHİS. Beş adaptörün her biri kendi `_HEALTH`/`_TRANSPORT` sözlüğünü TİTİZLİKLE dolduruyordu
# (çağrı sayısı, hata sayısı, son hata, damga) ve dördünün OKUYUCUSU YOKTU: `finviz.health` yalnız
# `finviz.status` içinden, `massive.health` hiç, `insider.health`/`shortinterest.health` yalnız
# kendi `durum()`larından, `alpaca.data_transport` hiç. Yani "hangi sağlayıcı ne zamandır bozuk?"
# sorusunun cevabı süreç belleğinde ölçülüyor ve hiçbir yüzeye çıkmıyordu — ölçüp atmak.
#
# TEK TOPLAYICI, TEK BİÇİM. Her satır aynı dört alanı taşır (ad, son_basari_ts, hata_orani,
# son_hata) ki sağlayıcılar YAN YANA okunabilsin; sağlayıcıya özgü olan her şey `ek` altında kalır.
#
# ÜÇ DÜRÜSTLÜK KURALI:
#   1. ÖLÇÜLEMEYEN None'DIR, 0 DEĞİL. Hiç çağrı yapılmamış bir sağlayıcının hata oranı 0,0 değil
#      None'dır — "hiç bozulmadı" ile "hiç denenmedi" aynı hücreye yazılamaz.
#   2. `son_basari_ts` yalnız `ok is True` iken doldurulur. Sağlık kayıtları SON çağrıyı damgalar,
#      son BAŞARIYI ayrıca tutmaz; `ok=False` iken `at` alanı son BAŞARISIZLIĞIN damgasıdır ve onu
#      "son başarı" diye sunmak uydurma olurdu. Bu yüzden ayrıca `son_cagri_ts` de verilir.
#   3. SÜREÇ-İÇİ OLDUĞU YAZILIDIR. Bu sözlükler diske yazılmaz: kart yalnız BU sürecin gördüğünü
#      anlatır ve süreç yeniden başladığında sıfırlanır (`kapsam: "surec-ici"`). A1'de worker
#      uvicorn ile AYNI süreçte koştuğu için pratikte canlı zincirin sağlığıdır; ayrı süreçle
#      koşulursa kart boş görünür ve bu bir ARIZA DEĞİL, ölçüm kapsamının kendisidir.
def _saglayici_satiri(ad: str, h: dict, ek: dict | None = None) -> dict:
    """Bir sağlayıcının ham sağlık sözlüğünü ORTAK biçime indirger. `ek`: sağlayıcıya ÖZGÜ alanlar —
    ortak dört alanla karışmasınlar diye AYRI anahtarda kalır (yan yana okunabilirliğin şartı)."""
    calls, fails = h.get("calls"), h.get("fails")
    ok, at = h.get("ok"), h.get("at")
    try:
        oran = round(float(fails) / float(calls), 4) if calls else None
    except (TypeError, ValueError, ZeroDivisionError):  # sessiz-yutma: sayaç biçimsizse hata oranı ÖLÇÜLEMEZ ve sonuç bunu None ile SÖYLER (0,0 yazmak "hiç bozulmadı" diye okunurdu); uyarı basmak her pano isteğinde tekrarlanırdı
        oran = None
    return {"ad": ad, "ok": ok,
            "son_basari_ts": at if ok is True else None,
            "son_cagri_ts": at,
            "hata_orani": oran, "cagri": calls, "hata": fails,
            "son_hata": (h.get("last_error") or None), "son_durum": h.get("last_status"),
            "ek": ek or {}}


def _saglayicilar(sched: dict) -> dict:
    """Beş sağlayıcının sağlık kartı. AĞ ÇAĞRISI YOK — hepsi süreç-içi sayaç okuması."""
    from .adapters import finviz as _fv, massive as _ms, insider as _in
    from .adapters import shortinterest as _si, alpaca as _alp
    y4 = sched.get("last_y4") or {}
    satirlar = []
    try:
        _fvh = _fv.health()
        satirlar.append(_saglayici_satiri("finviz", _fvh,
                                          ek={"kaynak": _fvh.get("source"),
                                              "son_aday_n": _fvh.get("n"),
                                              "elite_token": _fv.elite()}))
    except Exception as e:
        satirlar.append({"ad": "finviz", "ok": None, "olculemedi": f"{type(e).__name__}"})
    try:
        satirlar.append(_saglayici_satiri("massive", _ms.health(),
                                          ek={"mod": _ms.mode(),
                                              "yazim_kapisi": _ms.write_enabled(),
                                              "dogrulama": _ms.verify_basis()}))
    except Exception as e:
        satirlar.append({"ad": "massive", "ok": None, "olculemedi": f"{type(e).__name__}"})
    try:
        # Y4 İKİLİSİNDE `ek` KADANSTAN GELİR, `durum()` BURADA ÇAĞRILMAZ: insider'ın `defter_oku()`
        # 60.000 satıra kadar büyüyebilen ham defteri tamamen okur (bkz. scheduler._y4_collect'teki
        # gerekçe). Seans başına bir kez okunmuş özet, her istekte yeniden okumaktan hem ucuz hem
        # de AYNI DERECEDE doğrudur — defter zaten seansta bir kez değişiyor.
        satirlar.append(_saglayici_satiri("insider", _in.health(),
                                          ek={"seans": y4.get("session"),
                                              "kadans": y4.get("insider")}))
    except Exception as e:
        satirlar.append({"ad": "insider", "ok": None, "olculemedi": f"{type(e).__name__}"})
    try:
        satirlar.append(_saglayici_satiri("shortinterest", _si.health(),
                                          ek={"seans": y4.get("session"),
                                              "kadans": y4.get("shortinterest")}))
    except Exception as e:
        satirlar.append({"ad": "shortinterest", "ok": None, "olculemedi": f"{type(e).__name__}"})
    try:
        # ALPACA'NIN İKİ AYRI TAŞIMASI VAR ve karıştırılmaları mutabakatı yanıltır: `transport()`
        # TİCARET ucudur (emir/pozisyon), `data_transport()` VERİ ucudur (bar/snapshot). Kart
        # ikisini AYRI satır olarak taşır — biri sağlamken öteki bozuk olabilir ve tam da o hâl
        # "veri gelmiyor ama emirler gidiyor" gecesini açıklar.
        satirlar.append(_saglayici_satiri("alpaca_veri", _alp.data_transport(),
                                          ek={"anahtar": _alp.data_available()}))
        satirlar.append(_saglayici_satiri("alpaca_ticaret", _alp.transport(),
                                          ek={"anahtar": _alp.paper_available()}))
    except Exception as e:
        satirlar.append({"ad": "alpaca", "ok": None, "olculemedi": f"{type(e).__name__}"})
    return {"kapsam": "surec-ici",
            "beyan": ("sağlık sayaçları DİSKE YAZILMAZ — bu kart yalnız BU sürecin gördüğünü "
                      "anlatır ve yeniden başlatmada sıfırlanır. Boş bir kart 'sağlayıcı bozuk' "
                      "değil 'bu süreçte henüz çağrı yapılmadı' demektir."),
            "saglayicilar": satirlar}


# =================================================================================================
# SESSİZ HAT (WP-P/P1, 2026-08-01) — ÜÇ SAĞLIK YÜZEYİNİN LEVEL-1 TOPLAMASI
# -------------------------------------------------------------------------------------------------
# NİYE VAR: bekçi durumu, durdurma kilitleri ve veri tazeliği panoda ÜÇ AYRI yerde yaşıyordu (HUD
# rozeti · Bölüm 1 satırları · statuspill) ve üçü de SAĞLIKLIYKEN de konuşuyordu. ISA-101/HP-HMI'nın
# Level-1 kuralı bunun tersini söyler: sağlıklı sistem GÖRÜNMEZE yakın durmalı, çünkü her zaman
# konuşan bir gösterge sapma anında bir SES DEĞİŞİMİ üretemez. Toplama, alarm yorgunluğuna karşı
# kurulmuş tek yapısal savunmadır.
#
# YENİ MEKANİZMA İCAT EDİLMEDİ. Üç segmentin de girdisi ZATEN üretiliyordu:
#   bekçiler → `watchdog.report()` (aynı istekte bir kez hesaplanır, buraya ENJEKTE edilir)
#   kilitler → `health.halted()` / `health.learn_halted()` / heartbeat'in `breaker_tripped` alanı
#   veri     → `health.heartbeat_age_seconds()` + heartbeat'in `last_bar`/`data_ok` alanları
# Bu fonksiyon yalnız TOPLAR ve sapmayı ADIYLA + SÜRESİYLE + RUNBOOK İPUCUYLA dışarı verir.
#
# "KİLİT" BURADA FAZ-6 KİLİT ZİNCİRİ DEĞİLDİR ve olamaz: o zincir fail-closed'dır ve KAPALI olması
# NORMAL hâldir (Faz 6 açılmadı). Onu sessiz hatta koymak, hattı ilk günden kalıcı olarak kırmızıya
# boyardı — yani toplamanın amacını tam tersine çevirirdi. Buradaki kilitler DURDURMA kollarıdır:
# normal konumları "kapalı"dır ve AÇIK olmaları bir sapmadır.
_SESSIZ_HAT_NABIZ_ESIK_S = 900.0      # health.stale() varsayılanıyla AYNI eşik — ikinci bir gerçek yok


def _sure_metni(saniye: float | None) -> str | None:
    """Sapmanın SÜRESİ — "açık" bir bayrak, "3 sa 12 dk'dır açık" bir karardır."""
    if saniye is None or saniye < 0:
        return None
    dk = int(saniye // 60)
    if dk < 60:
        return f"{dk} dk"
    sa, kalan = divmod(dk, 60)
    return f"{sa} sa {kalan} dk" if sa < 48 else f"{sa // 24} gün {sa % 24} sa"


def _dosya_yasi_s(p) -> float | None:
    """Bayrak dosyasının yaşı = kilidin ne kadardır açık olduğu. Dosya yoksa/okunamıyorsa None —
    "0 saniyedir açık" yazmak uydurma olurdu."""
    try:
        return max(0.0, _time.time() - p.stat().st_mtime)
    except OSError:  # sessiz-yutma: SÜRE ölçülemedi ama KİLİDİN AÇIK OLDUĞU zaten çağıranda biliniyor — None dönüp "süre ölçülemedi" demek, uydurma bir süre yazmaktan iyidir
        return None


def _sessiz_hat(wd: dict, hb: dict) -> dict:
    """Level-1 toplama: üç segment, her biri {saglikli, ozet, sapmalar[]}.

    SÖZLEŞME: `saglikli` üç değerli DEĞİLDİR. Ölçülemeyen bir segment SAĞLIKSIZDIR (fail-open
    değil): "bakamadım"ı "iyi" saymak, sessiz hattın var olma sebebini ortadan kaldırır. Ama
    sapmanın METNİ ölçülemezliği ayrı söyler — operatörün eylemi ikisinde farklıdır."""
    segmentler = []

    # ---- 1) BEKÇİLER ---------------------------------------------------------------------------
    stale = list(wd.get("stale") or [])
    never = list(wd.get("never") or [])
    toplam = wd.get("total")
    b_sapma = [{"ad": s.get("name"),
                "sure": _sure_metni((s.get("gap_h") or 0) * 3600.0),
                "detay": f"pencere {s.get('expected_h')} sa",
                "ipucu": "mekanizma kadansı durdu — RUNBOOK: süreç canlı mı, kadans kapısı ne diyor"}
               for s in stale[:4]]
    b_sapma += [{"ad": n, "sure": None, "detay": "kurulumdan beri hiç koşmadı",
                 "ipucu": "nabız hiç atılmadı — mekanizma üretim yolunda mı (kablolama)"}
                for n in never[:4]]
    # ASKIDA (v192): pencereyi aşmış AMA sistemin kendi beyanıyla beklemeye alınmış mekanizma
    # (hermes kota soğuması / kimlik havuzu tükenmesi). SAPMA DEĞİLDİR — sessiz hattın kırmızısını
    # meşru bir beklemeyle boyamak, hattın anlamını yine alarm-yorgunluğuna çevirirdi. Ama GİZLİ de
    # değildir: `ok/total` oranında eksik görünen mekanizmanın nedeni burada yazar.
    askida = list(wd.get("askida") or [])
    segmentler.append({
        "ad": "bekçiler", "saglikli": not b_sapma,
        # KRİTİK = "hiç koşmadı". watchdog.report'un kendi ifadesiyle en yüksek sesli hâl:
        # geciken bir mekanizma yavaşlamıştır, hiç koşmamış bir mekanizma KABLOLANMAMIŞTIR.
        "kritik": bool(never),
        "ozet": (f"{wd.get('ok')}/{toplam}" if toplam is not None else "—"),
        "n_sapma": len(stale) + len(never), "sapmalar": b_sapma,
        "askida": [{"ad": a.get("name"), "neden": a.get("neden"), "detay": a.get("detay"),
                    "sure": _sure_metni((a.get("gap_h") or 0) * 3600.0)} for a in askida[:4]],
        "n_askida": len(askida)})

    # ---- 2) KİLİTLER ---------------------------------------------------------------------------
    # Normal konum "kapalı". Açık bir kol bir arıza DEĞİL bir DURUM olabilir (operatör eliyle
    # çekilmiştir) — ama her hâlükârda sessiz kalamaz: HALT açıkken sistemin "sessiz sağlıklı"
    # görünmesi, tam olarak bu turun kapattığı yanılsamadır.
    kollar = [
        ("soft_halt", health.halted(), health.halt_path(),
         "yeni giriş DURDU — kaldırmak için panoda Kademe 1 (Soft Halt) kolu"),
        ("halt_learning", health.learn_halted(), health.learn_halt_path(),
         "ship DURDU (işlem sürer) — Kademe 4 kolu; rollback güvenlik olarak açık kalır"),
    ]
    k_sapma = []
    for ad, acik, yol, ipucu in kollar:
        if acik:
            k_sapma.append({"ad": ad, "sure": _sure_metni(_dosya_yasi_s(yol)),
                            "detay": "kol ÇEKİLİ", "ipucu": ipucu})
    # Devre kesici bir DOSYA değil heartbeat alanı — süresi ölçülemez ve uydurulmaz.
    kesici = hb.get("breaker_tripped")
    n_kol = len(kollar) + (1 if kesici is not None else 0)
    if kesici:
        k_sapma.append({"ad": "devre_kesici", "sure": None,
                        "detay": "günlük zarar kesicisi ATEŞLEDİ",
                        "ipucu": "kesici bir sonraki seansta kendiliğinden sıfırlanır — "
                                 "sıfırlanmıyorsa risk defterine bak"})
    segmentler.append({
        "ad": "kilitler", "saglikli": not k_sapma,
        # ÇEKİLİ HER KOL KRİTİKTİR: makine ya durmuştur ya da öğrenmesi durmuştur. Bu segmentte
        # "hafif sapma" diye bir hâl yok — kol ya kapalıdır ya bir şeyi durduruyordur.
        "kritik": bool(k_sapma),
        "ozet": f"{n_kol - len(k_sapma)}/{n_kol}",
        "n_sapma": len(k_sapma), "sapmalar": k_sapma,
        "beyan": ("kilit = DURDURMA kolu (soft halt · halt learning · devre kesici). Normal konum "
                  "KAPALI; N/N 'hiçbiri çekili değil' demektir. Faz-6 kilit zinciri BU DEĞİLDİR — "
                  "o zincir fail-closed'dır ve kapalı olması normal hâldir.")})

    # ---- 3) VERİ TAZELİĞİ ----------------------------------------------------------------------
    yas = health.heartbeat_age_seconds()
    son_bar = hb.get("last_bar")
    v_sapma = []
    if yas is None:
        v_sapma.append({"ad": "nabız", "sure": None, "detay": "nabız damgası OKUNAMADI",
                        "ipucu": "heartbeat.json yok ya da bozuk — worker hiç tur atmadı mı"})
    elif yas > _SESSIZ_HAT_NABIZ_ESIK_S:
        v_sapma.append({"ad": "nabız", "sure": _sure_metni(yas), "detay": "nabız bayat",
                        "ipucu": f"eşik {int(_SESSIZ_HAT_NABIZ_ESIK_S // 60)} dk — "
                                 "zamanlayıcı döngüsü ilerliyor mu (tick bekçisi)"})
    if hb.get("data_ok") is False:
        v_sapma.append({"ad": "veri_kalitesi", "sure": None, "detay": "data_ok=False",
                        "ipucu": "veri kalitesi kapısı düştü — karantina ve kaynak sağlığı kartı"})
    segmentler.append({
        "ad": "veri", "saglikli": not v_sapma,
        # ÖZET SON BARI SÖYLER: "taze" tek başına neyin taze olduğunu söylemez. VE "taze" KELİMESİ
        # YALNIZ SAPMA YOKKEN YAZILIR — bayat bir nabzın yanında duran "taze" damgası, sessiz hattın
        # kapatmak için kurulduğu yanılsamanın ta kendisi olurdu.
        "ozet": ((f"taze — {son_bar}" if son_bar else "taze") if not v_sapma
                 else (str(son_bar) if son_bar else "—")),
        # KRİTİK = ÖLÇÜLEMEDİ. "Nabız 20 dk geride" beklenir bir gecikmedir; "nabız damgası
        # okunamadı" ölçüm aletinin kendisinin düştüğü hâldir ve ikisi aynı tonu alamaz.
        "kritik": bool(yas is None or hb.get("data_ok") is False),
        "asof": son_bar, "nabiz_yas_s": (round(yas) if yas is not None else None),
        "n_sapma": len(v_sapma), "sapmalar": v_sapma})

    saglikli = all(s["saglikli"] for s in segmentler)
    return {
        "saglikli": saglikli,
        "segmentler": segmentler,
        # TEK SATIRLIK OKUMA SUNUCUDA KURULUR: pano ikinci bir cümle kurmaz, yoksa aynı gerçeğin
        # iki metni doğar ve biri bayatlar (bu deponun tekrar eden kusur sınıfı).
        "satir": " · ".join(f"{s['ad']} {s['ozet']}" for s in segmentler),
        "beyan": ("LEVEL-1 TOPLAMA: hepsi sağlıklıyken TEK sönük satır çıkar ve renk taşımaz. "
                  "Sapan segment AÇILIR ve YALNIZ o segment renklenir — sağlıklı olanlar sönük "
                  "kalır. Sürekli konuşan bir gösterge, sapma anında ses değiştiremez."),
    }


# =============================================================================================
# GÖLGE-FİT GÖRÜNÜRLÜĞÜ (v192, 2026-08-06 — operatör: "pano antrenman hiç koşmamış diyor")
# =============================================================================================
# ÖLÇÜLEN KUSUR BİR YALAN DEĞİL, BİR BİTİŞİKLİK KAZASI. Panonun kırmızı "HİÇ KOŞMADI" rozeti
# `ogrenme.nabiz.shadow_fit`ten gelir ve o nabız `shadow_model.json:fit_attempt_ts`i ölçer —
# damgayı YALNIZ `shadow_model.maybe_refit()` (zamanlayıcının seans-sonrası KADANSI) yazar.
# Oysa canlıda fit'i atan taraf `refit_and_save()`tir (loop'un P5_LEARN kolu) ve o, deneme
# damgasına HİÇ dokunmaz. Sonuç: kadans gerçekten hiç koşmamıştır (rozet DOĞRU), ama yanında
# duran model taptazedir (canlı: 2026-08-05T22:10, n=2217, brier_train 0,2428) — ve kart bunu
# hiçbir yerde YAZMAZ. Operatör iki cümleyi tek cümle sanıp "antrenman ölmüş" okur.
#
# BU BLOK ÜÇÜNCÜ BİR GERÇEK ÜRETMEZ, VAR OLANI GÖRÜNÜR KILAR: `training_status()` zaten
# `son_fit_ts` (fit_ts ya da `_kaynak.generated`), `n_fit`, `brier_train` ve `terfi` demetini
# taşıyordu; okuyucusu yoktu (YASA 6 borcu). Eklenen tek YENİ şey terfi HÜKMÜNÜN NEDENİdir ve o
# da uydurulmaz: kuraklığın sınıfı `sieve` defterinin `shadow_model.terfi` aşamasından — yani
# ölçümün kendisinden — okunur.
_TERFI_ASAMA = "shadow_model.terfi"


def _terfi_hukmu(terfi: dict | None, sieve_rep: dict | None) -> dict:
    """Terfi neden oldu/olmadı — ÖLÇÜLMÜŞ neden, tahmin değil.

    UYDURMA YASAĞI: ölçülemeyen hâl `karar="ÖLÇÜLEMEDİ"`dir, `"HAYIR"` DEĞİL. İkisi operatör için
    bambaşka eylemlerdir: "hayır" modelin tabanı yenemediğini söyler (bilgi), "ölçülemedi" kıyas
    verisinin hiç birikmediğini söyler (kuraklık — beklenecek şey var)."""
    t = terfi or {}
    n_live, esik = t.get("n_live"), t.get("promote_min_n")
    live, taban = t.get("live_brier"), t.get("baseline_brier")
    if t.get("promoted"):
        return {"karar": "EVET", "sinif": "terfi_etti",
                "neden": f"canlı Brier {live} < taban {taban} ({n_live} taze çiftte)"}
    # Elenme sınıfı ÖLÇÜMDEN: `shadow_model.terfi` aşaması kaç satır aldı, kaçını neden düşürdü.
    asama = ((sieve_rep or {}).get("stages") or {}).get(_TERFI_ASAMA) or {}
    drops = asama.get("drops") or {}
    en_cok = max(drops.items(), key=lambda kv: kv[1])[0] if drops else None
    elenme = (f" · eleme defteri: {asama.get('in')} işlem girdi, {asama.get('out')} çift çıktı"
              f"{f' (en çok: {en_cok})' if en_cok else ''}") if asama else ""
    if live is None:
        if n_live in (0, None):
            return {"karar": "ÖLÇÜLEMEDİ", "sinif": "ornek_kurakligi",
                    "neden": ("live_brier ÖLÇÜLEMEDİ — canlı kıyas çifti birikmedi: gölge tahmini "
                              "damgalı bir plan henüz kapanmış bir işleme dönüşmedi" + elenme)}
        return {"karar": "ÖLÇÜLEMEDİ", "sinif": "brier_olculemedi",
                "neden": f"live_brier ölçülemedi ({n_live} çift var ama Brier hesaplanamadı)" + elenme}
    if esik is not None and (n_live or 0) < esik:
        return {"karar": "HAYIR", "sinif": "esik_dolmadi",
                "neden": f"canlı çift {n_live}/{esik} — terfi eşiği dolmadı" + elenme}
    if taban is None:
        return {"karar": "ÖLÇÜLEMEDİ", "sinif": "taban_olculemedi",
                "neden": "taban-oran Brier'i ölçülemedi — kıyas yapılamaz" + elenme}
    return {"karar": "HAYIR", "sinif": "tabani_yenemedi",
            "neden": f"canlı Brier {live} ≥ taban-oran Brier {taban} — model tabanı yenemedi "
                     f"({n_live} taze çift)"}


# =============================================================================================
# EKSEN-2'NİN "0 ÜRETİLDİ"Sİ — DOĞRU SAYI, GÖRÜNMEYEN NEDEN (v207, 2026-08-07)
# =============================================================================================
# ÖLÇÜM (Rol-1, canlı `last_learn.eksen2.teshis.sayim`): gercek_katman_olculmemis 57 · korumali 5 ·
# gercek_katman_olculmemis_cf_dolu 3 · esik_araliginda 1 · ornek_yetersiz_cf_de_yetersiz 1. Yani
# 67 skillin 60'ı üretimde HİÇ koşmamış, 5'i motor-içi (aday bile değil), ölçülmüş olan 2.
# Üreteç kanıt olmayan yerde öneri üretmiyor — bu DOĞRU davranıştır.
#
# KUSUR ÜRETEÇTE DEĞİL OKUMADA: pano satırı "0 üretildi · 0 kaydedildi · 0 bekleyen · 0 otomatik
# uygulandı" diyordu ve dört sıfır bir BAŞARISIZLIK gibi okunuyordu. Doğru okuma KANIT YOKLUĞUdur
# ve o okuma ancak kovalar ÖZETE bağlanınca doğar: değer = ölçülen/toplam, çubuğun paydası beyan
# edilen skill sayısı, meta kova dökümü.
#
# ÜÇÜNCÜ BİR GERÇEK ÜRETİLMEZ. Kovalar `skills.axis2_diagnosis()`in ÖLÇÜMÜDÜR; burada yalnız
# SINIFLANDIRILIR. Sınıflandırma kova adlarının kendi anlamından çıkar (`axis2_diagnosis` dal
# yapısı): `gercek_katman_olculmemis*` = avg_r None (ölçülmemiş), `korumali` = motor içi, geri
# kalan HER kova `avg_r is not None` dalından gelir, yani ÖLÇÜLMÜŞTÜR. Yarın doğacak bir kova adı
# da bu kurala uyar — sabit bir ad listesi tutmak, yeni kovayı sessizce yanlış saymak olurdu.
_EKSEN2_OLCULMEMIS_ONEK = "gercek_katman_olculmemis"
_EKSEN2_KORUMALI = "korumali"
_AXIS2_DEFTERI = "axis2_status.json"      # LİTERAL ad (codelaw.artifact_graph okuyabilsin)


def _eksen2_ozeti(ex: dict | None) -> dict:
    """Sıfır üretimin NEDENİ — kova sayımından türetilmiş özet.

    UYDURMA YASAĞI: kovalar yükte yoksa `durum="ÖLÇÜLEMEDİ"` ve bütün sayılar None döner —
    0 DEĞİL. "67 skillin 2'si ölçüldü" ile "kaç skill olduğunu bilmiyoruz" aynı ekranda aynı
    şeye benzeyemez."""
    kv = (ex or {}).get("kovalar")
    if not isinstance(kv, dict) or not kv:
        return {"durum": "ÖLÇÜLEMEDİ", "toplam_skill": None, "olculen": None,
                "olculmemis": None, "korumali": None, "oran": None, "payda": None, "dokum": [],
                "motor_ici_esik_asan": None,
                "neden": ("Eksen-2 teşhis kovaları yükte YOK — üretecin sessizliği ÖLÇÜLEMEDİ. "
                          "Bu bir 'kanıt yok' hükmü değildir: hükmü verecek sayım okunamadı.")}
    sayim = {str(k): int(v) for k, v in kv.items() if isinstance(v, (int, float))}
    toplam = sum(sayim.values())
    olculmemis = sum(n for k, n in sayim.items() if k.startswith(_EKSEN2_OLCULMEMIS_ONEK))
    korumali = sayim.get(_EKSEN2_KORUMALI, 0)
    olculen = toplam - olculmemis - korumali
    return {
        "durum": "dolu",
        "toplam_skill": toplam, "olculen": olculen,
        "olculmemis": olculmemis, "korumali": korumali,
        # ÇUBUK PAYDASI BEYANLI (kart sözleşmesi D2-a kapı 2): paydası yazılmayan bir doluluk,
        # okurun kendi uydurduğu tavana göre okunur.
        "oran": (round(olculen / toplam, 4) if toplam else None),
        "payda": f"katalogda beyan edilen skill sayısı ({toplam})",
        "dokum": sorted(sayim.items(), key=lambda kv_: (-kv_[1], kv_[0])),
        "motor_ici_esik_asan": None,      # `_eksen2_motor_ici` doldurur (ayrı defterden okunur)
        "neden": (f"{toplam} skillin {olculmemis}'i gerçek katmanda HİÇ ölçülmemiş, {korumali}'i "
                  f"motor-içi (aday değil); hüküm verilebilir olan {olculen}. Üreteç kanıt "
                  f"olmayan yerde öneri ÜRETMEZ — '0 üretildi' bir arıza değil, KANIT YOKLUĞUdur."),
    }


def _eksen2_motor_ici() -> list | None:
    """MOTOR-İÇİ EŞİĞİ AŞANLAR — `analytics.learning_automation()` bu kolu yayınlamıyor.

    NEDEN GÖRÜNMELİ: kanıt eşiğini aşan bir motor-içi skill için `skills.auto_shadow_from_evidence`
    BİLEREK bayrak yazmaz (motor bayraktan bağımsız koşar; yazmak "invoked yalanı"nın ters yönü
    olurdu). Bu bir KARARDIR ve karar görünmezse, ölçüm hiç olmamış gibi okunur. Canlıda bugün
    `pullback-screener` bu koldadır ve pano hiçbir yerinde yazmıyordu.

    Defter okunamazsa `None` döner (boş liste DEĞİL): "aşan yok" ile "bakamadık" ayrı hâllerdir."""
    ax = store.read_json(_AXIS2_DEFTERI, None)
    if not isinstance(ax, dict):
        return None
    mi = (ax.get("otomatik") or {}).get("motor_ici_esik_asan")
    return mi if isinstance(mi, list) else None


def _ogrenme_blogu(ogr: dict, sieve_rep: dict | None) -> dict:
    """`analytics.learning_automation()` yükünü DÜRÜSTLÜK alanlarıyla zenginleştirir.

    `nabiz.shadow_fit` KALDIRILMAZ; yanına, aynı karta, MODELİN son fiilî fit'i ve son DENEMESİ
    konur. Üç gerçek yan yana durduğunda operatör hangisinin ne olduğunu okuyabilir.

    v192 NOTU DÜZELTİLDİ (v207): burada eskiden "kadansın gerçekten koşmadığı doğrudur" yazıyordu.
    2026-08-07 ölçümü bunu YANLIŞLADI — kadans 2026-08-06T20:13'te koşup EĞİTMİŞTİ
    (`scheduler_status.last_learn.antrenman.fitted=True, n_fit=2217`); damgası
    `ShadowTradeOutcomeModel.save()`in üstüne-yazması yüzünden SİLİNMİŞTİ. Kusur rozette değil
    damgadaydı ve düzeltmesi `shadow_model.py`de. Eski cümleyi bırakmak, çürütülmüş bir hükmü
    kodda yaşatmak olurdu."""
    out = dict(ogr or {})
    an2 = out.get("antrenman") or {}
    hukum = _terfi_hukmu(an2.get("terfi"), sieve_rep)
    out["son_fit"] = {
        "ts": an2.get("son_fit_ts"),
        "n": an2.get("n_fit"), "n_real": an2.get("n_real"), "n_cf": an2.get("n_cf"),
        "brier_train": an2.get("brier_train"),
        "terfi": hukum,
        # DAMGA MI, ÇIKARIM MI (v207): `kunye` değeri "fit_ts damgası YOK, tarih künyeden
        # çıkarıldı" demektir — v207 öncesi canlının hâli buydu ve ayrımı yazmayan bir tarih,
        # çıkarımı damga gibi gösterirdi.
        "kaynak": an2.get("son_fit_kaynak"),
        # KADANS ≠ FİT: rozetin neyi ölçtüğü kartın kendi üstünde yazsın, dipnotta değil.
        # BEYAN v207'DE DÜZELTİLDİ: v192 "damgayı yalnız maybe_refit yazar" diyordu ve bu artık
        # YANLIŞ — damga fiilin yanına (refit_and_save) taşındı, yani fit'i kim atarsa atsın
        # deneme damgası düşer. Eski metni bırakmak, düzeltilmiş bir kusuru panoda yaşatmaktı.
        "beyan": ("`son_fit` MODELİN son fiilen KURULDUĞU andır (`fit_ts`). Yanındaki `son deneme` "
                  "(`fit_attempt_ts`) fit DENENDİĞİ andır ve fit edilmeyen denemeler de "
                  "(veri seti değişmedi · eşik altı) oraya damga bırakır. İkisi AYRI olgudur: "
                  "deneme ilerlerken fit yerinde kalabilir. Damgayı `shadow_model.refit_and_save` "
                  "atar — kadans (maybe_refit) da, loop.P5_LEARN de o yoldan geçer."),
    }
    # ---- SON DENEME (v207) --------------------------------------------------------------------
    # Fit ile DENEME panoda ayrı okunmak zorunda: "kadans koştu, veri değişmemişti" ile "kadans
    # hiç koşmadı" tek satıra sıkışırsa sessiz bir duruş taze görünür (kadans nabzının ölçtüğü
    # damga tam olarak budur).
    out["son_deneme"] = {
        "ts": an2.get("son_deneme_ts"),
        "atlama_nedeni": an2.get("son_atlama_nedeni"),
        "damga_var": bool(an2.get("son_deneme_ts")),
    }
    # ---- EKSEN-2 ÖZETİ (v207) -----------------------------------------------------------------
    ex = out.get("eksen2")
    if isinstance(ex, dict):
        ex = dict(ex)
        ozet = _eksen2_ozeti(ex)
        ozet["motor_ici_esik_asan"] = _eksen2_motor_ici()
        ex["ozet"] = ozet
        out["eksen2"] = ex
    return out


def _alarm_gunluk() -> dict:
    """v192 alarm hijyeninin GÜNLÜK sayacı — bekçi defterinin DIŞ okuyucusu burasıdır.

    Dosya adı LİTERAL yazılır: `codelaw.artifact_graph` "kendi yazdığını kendi okuyan modül tüketici
    sayılmaz" der ve sayaç `watchdog.py` içinde okunsaydı defter `artifact_unread` olurdu.

    NİYE PANOYA ÇIKAR: bastırma görünmezse hijyen ile KÖRLÜK ayırt edilemez. "Bugün 1 alarm" ile
    "bugün 1 alarm + 111 bastırıldı" aynı ekranda aynı şeye benzerse, tavanın kendisi bir sonraki
    turun gizli arızası olur."""
    doc = store.read_json("watchdog_alarm_gunluk.json", None)
    if not isinstance(doc, dict):
        return {"gun": None, "mekanizmalar": {}, "n_alarm": 0, "n_bastirilan": 0,
                "durum": "defter_yok",
                "beyan": "bugün hiç mekanizma-gecikme alarmı üretilmedi (defter yazılmadı)"}
    mek = {k: {"alarm": int((v or {}).get("alarm") or 0),
               "bastirilan": int((v or {}).get("bastirilan") or 0),
               "askida": int((v or {}).get("askida") or 0),
               "son_askida_neden": (v or {}).get("son_askida_neden")}
           for k, v in (doc.get("mekanizmalar") or {}).items() if isinstance(v, dict)}
    return {"gun": doc.get("gun"), "mekanizmalar": mek, "durum": "dolu",
            "n_alarm": sum(v["alarm"] for v in mek.values()),
            "n_bastirilan": sum(v["bastirilan"] for v in mek.values()),
            "n_askida": sum(v["askida"] for v in mek.values()),
            "tavan": __import__("meridian.watchdog",
                                fromlist=["GUNLUK_ALARM_TAVANI"]).GUNLUK_ALARM_TAVANI,
            "beyan": ("mekanizma başına GÜNLÜK alarm tavanı (v192). Tavana takılan satır SESSİZ "
                      "DEĞİL sayılıdır; 'askıda' ise alarm hiç üretmeyen MEŞRU bekleme hâlidir "
                      "(hermes kota soğuması / kimlik havuzu tükenmesi).")}


def _nous_fisler(limit: int = 12) -> dict:
    """Nous öneri FİŞLERİ — otomatik yönlendirme borusunun (b) sınıfının operatör kuyruğu.

    Boş defter SAHTE bir "her şey işlendi" göstermez: `durum` alanı ayrımı taşır ("fiş yok" ≠
    "boru hiç koşmadı"). `anahtar` alanı önerinin kimliğidir — pano rozeti bu alanla eşler."""
    doc = store.read_json("nous_fisler.json", None)
    if doc is None:
        return {"durum": "defter_yok", "n": 0, "fisler": [], "anahtarlar": [],
                "rol": ("boru henüz hiç koşmadı (haftalık nous_eval kadansının sonunda çalışır) — "
                        "'fiş yok' DEĞİL, 'defter hiç yazılmadı'")}
    fisler = [f for f in (doc.get("fisler") or []) if isinstance(f, dict)]
    acik = [f for f in fisler if str(f.get("durum") or "fislendi") == "fislendi"]
    return {"durum": "dolu" if fisler else "bos", "n": len(fisler), "n_acik": len(acik),
            "guncellendi": doc.get("guncellendi"),
            "anahtarlar": [str(f.get("anahtar")) for f in fisler],
            "fisler": list(reversed(fisler))[:limit],
            "rol": ("FİŞ = kod/doküman/mimari önerisinin GÖRÜNÜR operatör kalemi. Otomatik uygulama "
                    "yolu YOKTUR ve olmayacaktır — fiş bir onay değil, bir kuyruk kaydıdır.")}


# ---- /api/diagnostics KISA ÖMÜRLÜ YANIT ÖNBELLEĞİ (v181, 2026-08-03) -------------------------
# CANLI ŞİKÂYET: "pano çok yavaşlamış" — ölçüm: bu uç 8,8-10,4 sn. Kökün ikinci yarısı: uç,
# panonun HER anketinde ~60 üreticiyi (yedi bütünlük dedektörü, blok-bootstrap CI'lar, 61 JSONL +
# 97 CSV okuması) baştan koşturuyordu. İçeride iki parçanın kendi TTL'i vardı
# (`integrity_report_cached` 20 sn, `alarm_budget_cached` 30 sn) ama YÜKÜN GERİ KALANI korumasızdı.
#
# TTL NEDEN 45 SANİYE (ölçülmüş kadanslara göre, keyfi değil):
#   * ALT SINIR — pano `refreshStatus`u 15 sn'de bir bu ucu çağırıyor (app.js: sessiz hat şeridi,
#     her sayfada) ve `pollHUD` 20 sn'de bir; istemci `JCACHE`i 15 sn dedupe ediyor. Yani uca
#     ~15 sn'de bir gerçek istek düşüyor. 30 sn'lik bir TTL yalnız her ikinci isteği kurtarırdı ve
#     içerideki 20 sn'lik bütünlük TTL'ine sıkışırdı; 45 sn ÜÇ ankete karşılık bir hesap demektir.
#   * ÜST SINIR — bu uçtan okunan en dar tespit penceresi `watchdog.EXPECTED`in en küçüğüdür
#     (30 dk: scheduler_poll/hermes_poll). 45 sn onun %2,5'i; yani önbellek hiçbir mekanizma
#     durmasını operatörün fark edebileceği ölçüde gizleyemez. 60 sn'ye çıkarmadım: şerit 15 sn'de
#     bir tazeleniyor ve 60 sn ART ARDA DÖRT güncellemenin aynı sayıları göstermesi demek olurdu —
#     "pano donmuş" hissi, düzeltmeye çalıştığımız şikâyetin ta kendisi.
#
# BAYATLIK DÜRÜST TAŞINIR: yanıt `hesaplama_ts` (hesabın ANI) + `onbellekten` (bu istek hesapladı
# mı, yoksa kutudan mı geldi) alanlarını taşır. Ve İÇERİDEKİ YAŞ ALANLARI ZARFLA BİRLİKTE YAŞLANIR:
# `integrity_age_s` ile `alarm_butcesi.yas_s` önbellekten servis edilirken zarfın yaşı KADAR
# artırılır. Bu satır olmasaydı 40 saniyelik bir kopya `integrity_age_s: 0.0` diyerek "bu istekte
# hesaplandı" iddia ederdi — panoya taze gibi görünen bayat sayı, tam da bu deponun kovaladığı
# kusur. Hiçbir alan, içinde bulunduğu zarftan taze olduğunu iddia edemez.
_DIAG_CACHE: dict = {}
DIAG_TTL_S = 45.0


def _diag_yaslandir(yuk: dict, yas: float) -> dict:
    """Önbellekten servis edilen yükün yaş alanlarını zarfın yaşıyla toplar. Ölçülmemiş (None)
    bir yaş YAŞLANDIRILMAZ — yoksa 'ölçülemedi' sessizce bir sayıya dönüşürdü."""
    out = dict(yuk)
    _ia = out.get("integrity_age_s")
    if isinstance(_ia, (int, float)):
        out["integrity_age_s"] = round(_ia + yas, 1)
    _ab = out.get("alarm_butcesi")
    if isinstance(_ab, dict) and isinstance(_ab.get("yas_s"), (int, float)):
        out["alarm_butcesi"] = {**_ab, "yas_s": round(_ab["yas_s"] + yas, 1)}
    return out


def _diag_onbellek_oku(taze: bool) -> dict | None:
    """Geçerli (TTL içinde) bir kopya varsa yaşlandırılmış hâlini döndürür, yoksa None.
    `taze` zorla-tazeleme yoludur: operatör bir düzeltmenin canlıya değdiğini 45 sn beklemeden
    görebilmeli — aksi hâlde önbellek, teşhis ucunu teşhis edilemez yapardı."""
    if taze:
        return None
    hit = _DIAG_CACHE.get(str(getattr(config, "STATE", "")))
    if not hit:
        return None
    yuk, at = hit
    yas = _time.monotonic() - at
    if yas >= DIAG_TTL_S:
        return None
    return {**_diag_yaslandir(yuk, yas), "onbellekten": True}


def _diag_onbellege_yaz(yuk: dict) -> dict:
    """Taze hesabı damgalar, kutuya koyar ve döndürür."""
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    yuk = {**yuk, "onbellekten": False,
           "hesaplama_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")}
    # ANAHTAR `config.STATE` İÇERİR (alarm_budget_cached emsali, aynı gerekçe): ölçüm/test yolları
    # kum havuzuna yönlendiriyor ve anahtarsız bir süreç-içi kutu, kum havuzuna CANLI defterin
    # sayılarını servis ederdi. Tek girdi yeter — havuz anahtarları birikip sızıntı yapmasın.
    _DIAG_CACHE.clear()
    _DIAG_CACHE[str(getattr(config, "STATE", ""))] = (yuk, _time.monotonic())
    return yuk


def _diag_onbellek_bosalt(neden: str) -> None:
    """DURUM DEĞİŞTİ → teşhis zarfı geçersiz. Kontrol eylemleri BAŞARIYLA uygulandığında çağrılır.

    NİYE ŞART: 45 saniyelik zarf, operatörün AZ ÖNCE yaptığı şeyi gizleyebilir. HALT'a basıp
    Operasyon sayfasında `hud.halted: false` okumak önbelleğin en pahalı hatası olurdu — operatör
    düğmenin çalışmadığını sanıp ikinci kez basar. Bayatlık PASİF veri için kabul edilebilir;
    operatörün KENDİ eyleminin sonucu için asla.

    YALNIZ BAŞARIDA: reddedilen/no-op istek zarfı düşürmez. Düşürseydi her başarısız tıklama bir
    TAM teşhis hesabı tetiklerdi — panoyu yavaşlatan şey tam olarak o hesaptır, yani geçersizleştirme
    kendi çözdüğü sorunu geri getirirdi.

    NEDEN ROTA SINIFINDA (`_NativeRoute`) DEĞİL, ÇAĞRI YERİNDE: rota katmanından yalnız HTTP durumu
    görünür, oysa bu depoda kontrol uçlarının çoğu başarısızlığı 200 + `{"ok": false}` ile bildirir
    (submit_armed HALT'ta, notify_test kanalsızken, close_all onaysızken). Durum-kodu kancası o
    üçünü "başarı" sayardı.

    ENVANTER — ÇAĞRILDIĞI ROTALAR (hepsi POST/DELETE, hepsi teşhis yükünde bir alanı kıpırdatır):
      * kill-switch: `/api/halt`, `/api/resume` → hud.halted, risk.halted. `/api/control/halt`
        bu ikisine DELEGE eder, bu yüzden AYRICA çağırmaz (tek halt yolu sözleşmesi — o ucun notu).
      * bayraklar: `/api/control/learn_halt` → hud.learn_halted · `/api/intraday-arm` → intraday.*
      * icra: `/api/alpaca/submit_armed`, `/api/alpaca/close_all`, `/api/control/cancel_open`
        → reconcile.*, ledgers, mirror akışı · `/api/alpaca/koruma_kur` (v211) → koruma bekçisi
        (`watchdog.koruma_report`) aynı zarfta yaşıyor ve OCO gönderimi çıplak sayısını DÜŞÜRÜR;
        yalnız GERÇEKTEN emir gittiyse düşürülür (kuru koşu/bayat onay zarfa dokunmaz)
      * gelen kutusu/bildirim: `/api/alerts/ack`, `/api/broker_reject/ack` → sessiz_hat,
        reconcile.failed_submissions · `/api/notify/test` → alarm_butcesi
      * kadanslar: `/api/scheduler/advance`, `/api/hermes/reflect`,
        `/api/hermes/{start,stop,backfill,sync_integrations}`, `/api/sprint/{start,stop}`
        → scheduler.*, ogrenme.*, mlops.warmup
      * yapılandırma: `/api/secrets/{name}` (POST+DELETE), `/api/skills/apply`,
        `/api/skills/revision` → pipeline.finviz, saglayicilar, ogrenme.eksen2
      * onay: `/api/approvals/{id}` → onay defteri + damıtılan dersler
    ENVANTER DIŞI VE NEDENİ: `/api/login`, `/api/logout`, `/api/setup-password` (oturum kimliği
    teşhis yükünde tek bir alanı bile değiştirmez) ve `/api/hermes/pool_key` (anahtar hermes CLI
    havuzuna yazılır; teşhis yükünde karşılığı yok). İkisi de zarfı boşuna düşürmemeli.
    """
    if not _DIAG_CACHE:
        return                      # zaten boş — düşürülecek bir iddia yok
    _DIAG_CACHE.clear()
    try:
        obs.log("diag_cache_invalidated", neden=neden)
    except Exception:  # sessiz-yutma: kutu YUKARIDA boşaltıldı, asıl iş bitti; kayıt kanalının düşmesi bir HALT/onay isteğini 500'e çeviremez
        pass


# ==============================================================================================
# D3-UI · FIRSAT YÜZEYLERİ (C1'in on işi) — OKUYUCUSUZ DEFTERLERİN UÇ TARAFI
# ----------------------------------------------------------------------------------------------
# ÖLÇÜLEN KUSUR SINIFI (docs/PATTERN-ETUDU-2026-08-06.md §C1): "veri üretiliyor ama panoda
# görünmüyor". Aşağıdaki yardımcıların hepsi YALNIZ OKUR — hiçbiri state'e yazmaz, hiçbiri yeni
# bir ölçüm ÜRETMEZ; diskte zaten duran defterleri panonun okuyabileceği şekle sokar.
#
# NEDEN YENİ BİR "/api/firsat" KOVASI AÇILMADI: bu deponun kendi kuralı ("iki uç aynı alanı iki
# farklı şekilde servis edemez") tematik ev demektir. Her ölçüm KANONİK ucunun içine girer:
#   near_miss   → /api/diagnostics `mlops` (kardeşleri exit_efficiency + mae_profile; üçü de P5)
#   emir yaşamı → /api/diagnostics `reconcile` (emrin gerçekte ne olduğu — icra ailesi)
#   eylemsizlik → /api/diagnostics `risk`     (bütçe/karartma/erteleme aynı ailenin üç yüzü)
#   çizelge     → /api/diagnostics `cizelge`  (bekçi raporunun yanı; damgalar aynı dosyadan)
#   rollback    → /api/agent `rollback`       (karne defteri orada)
#   regresyon   → /api/agent `regresyon`      (sürüm ekseni orada)
#   maliyet     → /api/hermes `spend_detay`   (K1'in kanonik spend yüzeyi — /api/spend EMEKLİ)
# TEK İSTİSNA denetim izi: `/api/audit_trail` AYRI bir uçtur çünkü SORGULANABİLİR olmak zorunda
# (etüdün kendi hükmü: "çözüm tavanı kaldırmak değil, sorgulanabilir kılmak"). Sorgu parametresi
# taşıyan bir okuma, 45 sn önbellekli bir teşhis yükünün içine giremez.
#
# UYDURMA YASAĞI HER YARDIMCININ İÇİNDE: ölçülemeyen her dal `{"var": False, "neden": "<≥20
# karakter gerekçe>"}` döndürür. Boş sözlük ya da sıfır DÖNDÜRÜLMEZ — pano onu "ölçüldü, çıkmadı"
# diye çizerdi ve tam olarak bu turun kapattığı sınıf odur.
# ==============================================================================================
def _olculemedi(neden: str) -> dict:
    """ÖLÇÜLEMEDİ dalının TEK biçimi. Tek yerde durur ki pano tek bir şekil tanısın."""
    return {"var": False, "neden": neden}


def _near_miss_karne() -> dict:
    """C1-1 · Reddedilen kararların karnesi — `near_miss.json`ın İLK uç tüketicisi.

    KÜNYE ZORUNLU VE BURADA TAŞINIR: defter `source: "yalnız-simüle"` / `n_real: 0` damgasını
    taşıyor. Künyeyi düşürüp yalnız sayıları servis etmek, simüle bir kanıtı gerçek kanıt gibi
    göstermek olurdu (R8). Pano onu okumak ZORUNDA kalsın diye `_kaynak` aynı yükte gider."""
    doc = store.read_json("near_miss.json", None)
    if not isinstance(doc, dict):
        return _olculemedi("near_miss.json okunamadı — kapının reddettiklerinin karnesi bu turda "
                           "ölçülemedi (P5 kalibrasyonu hiç koşmamış olabilir). 'Ret yok' DEĞİL.")
    kovalar = doc.get("buckets") or {}
    if not kovalar:
        return _olculemedi("near_miss defteri var ama `buckets` boş — hangi kapının ne reddettiği "
                           "ölçülemedi; kova kırılımı olmadan karne bir sayıya iner ve yalan söyler.")
    # KOVALAR SIRALANIR: en çok reddeden üstte (kaldıraç sırası). Sıralama bir HÜKÜM değil bir
    # okuma kolaylığı; hiçbir eşik buna bağlı değil.
    satirlar = []
    for ad, k in kovalar.items():
        if not isinstance(k, dict):
            continue
        rej = k.get("by_regime") or {}
        satirlar.append({
            "blocked_by": ad, "n": k.get("n"), "entered": k.get("entered"),
            "n_r": k.get("n_r"), "avg_r": k.get("avg_r"),
            "rejim": [{"rejim": r, "n_r": (v or {}).get("n_r"), "avg_r": (v or {}).get("avg_r")}
                      for r, v in sorted(rej.items(), key=lambda t: -((t[1] or {}).get("n_r") or 0))],
        })
    satirlar.sort(key=lambda s: -(s["n"] or 0))
    return {"var": True, "resolved_total": doc.get("resolved_total"),
            "kaynak": doc.get("_kaynak") or None, "kovalar": satirlar,
            # KARŞI-OLGUSAL DEFTERİN BOYU: karnenin paydası burada. `ledgers.cf_resolved` ile AYNI
            # sayıdır ve iki kez okunmaz — teşhis yükü onu zaten hesaplıyor, burada TEKRARLANMAZ.
            "cf_defteri": "ledgers.cf_resolved"}


def _emir_yasam() -> dict:
    """C1-2 · Onaylanan planın emir yaşam-döngüsü izi — `mirror_orders.json`ın ilk panosal okuyucusu.

    BUGÜNE KADAR: dosya yalnız `_stream_view` (akış sağlığı) için okunuyordu; coid başına
    `status`/`filled_qty`/`filled_avg_price` panoya HİÇ ulaşmıyordu — yani "onayım aynaya ulaştı
    mı, KAÇA doldu?" sorusunun cevabı diskte duruyor, ekranda yoktu.

    PLANLANAN ↔ GERÇEKLEŞEN: `trade_plans.entry_trigger` ile dolum fiyatı yan yana konur ve fark
    emir-başına slipaj olarak beyan edilir. Fiyatın kendisi ÜRETİLMEZ: iki alandan biri yoksa
    `slipaj_bps` None kalır (0.0 yazmak "slipaj yoktu" demek olurdu)."""
    mirror = store.read_json("mirror_orders.json", None)
    if not isinstance(mirror, dict):
        return _olculemedi("mirror_orders.json okunamadı — emir yaşam-döngüsü bu turda ölçülemedi; "
                           "ayna defteri yoksa 'emir yok' değil 'bakamadık' doğru cümledir.")
    emirler = mirror.get("orders") or {}
    if not emirler:
        return {"var": True, "n": 0, "satirlar": [], "durum_dagilim": {},
                "updated": mirror.get("updated"), "last_event_ts": mirror.get("last_event_ts"),
                "bos_neden": "ayna defteri OKUNDU ve içinde emir yok — bu bir ÖLÇÜMdür "
                             "(silahlanan plan aynaya hiç gitmemiş ya da defter döndürülmüş)."}
    planlar = {p.get("id"): p for p in store.read_jsonl("trade_plans.jsonl")}
    satirlar, dagilim = [], {}
    for coid, o in emirler.items():
        if not isinstance(o, dict):
            continue
        st = str(o.get("status") or "?")
        dagilim[st] = dagilim.get(st, 0) + 1
        pln = planlar.get(coid) or {}
        tetik, dolum = pln.get("entry_trigger"), o.get("filled_avg_price")
        slipaj = None
        try:
            if tetik is not None and dolum is not None and float(tetik) > 0:
                slipaj = round(10_000 * (float(dolum) - float(tetik)) / float(tetik), 1)
        except (TypeError, ValueError):  # sessiz-yutma: sağlayıcı dizgisi sayıya dönmedi — slipaj ÖLÇÜLEMEDİ olarak kalır (None), uydurma 0.0 yazılmaz ve satırın geri kalanı yine servis edilir
            slipaj = None
        satirlar.append({
            "coid": coid, "symbol": o.get("symbol"), "side": o.get("side"),
            "status": st, "event": o.get("event"),
            "filled_qty": o.get("filled_qty"), "filled_avg_price": dolum,
            "order_id": o.get("order_id"), "updated": o.get("updated"),
            "plan_entry_trigger": tetik, "slipaj_bps": slipaj,
            # PLANIN KİMLİĞİ: coid bir plan id'siyle eşleşmiyorsa bu emir plandan doğmamıştır
            # (tatbikat/elle gönderim). Ayrımı SÖYLEMEK zorundayız — sessizce planlı saymak
            # denetim izini kirletirdi.
            "plan_var": bool(pln),
        })
    satirlar.sort(key=lambda s: str(s.get("updated") or ""), reverse=True)
    return {"var": True, "n": len(satirlar), "satirlar": satirlar[:40],
            "gosterilen": min(40, len(satirlar)), "durum_dagilim": dagilim,
            "updated": mirror.get("updated"), "last_event_ts": mirror.get("last_event_ts")}


def _eylemsizlik(hb: dict, rj: dict, gk_plans: list, radar) -> dict:
    """C1-8 · "Bugün neden hiçbir şey olmadı" — eylemsizliğin ADI, tek yerde toplanmış.

    HİÇBİR ALAN BURADA HESAPLANMAZ: dördü de çağıranın elinde zaten var (heartbeat, regime,
    gatekeeper planları, karartma radarı) ve ikinci kez okunmaları iki farklı gerçek riski
    doğururdu. Buranın işi TOPLAMAK ve nedeni ADLANDIRMAK.

    NEDEN SIRALIDIR: ilk eşleşen neden "birincil" olur. Sıra kaldıraç sırası değil ZORLAYICILIK
    sırasıdır — halt bir tercih değil bir durdurmadır; bütçe sıfırı bir tasarım kararıdır."""
    olaylar = obs.recent(3000)
    say = {}
    for e in olaylar:
        k = e.get("event")
        if k in ("session_deferred_for_coverage", "finviz_unavailable", "dormant_setup",
                 "scan_debt", "regime_budget_trigger"):
            say[k] = say.get(k, 0) + 1
    son_erteleme = next((e for e in reversed(olaylar)
                         if e.get("event") == "session_deferred_for_coverage"), None)
    butce = hb.get("exposure_budget_pct", rj.get("exposure_budget_pct"))
    verdict = {}
    for p in gk_plans or []:
        v = str(p.get("verdict") or "?")
        verdict[v] = verdict.get(v, 0) + 1
    kapi_nedenleri = {}
    for p in gk_plans or []:
        for r in (p.get("reasons") or []):
            ad = str(r).split(":")[0][:40]
            kapi_nedenleri[ad] = kapi_nedenleri.get(ad, 0) + 1
    # RADAR bir liste ya da sözlük olabilir (üretici sürümüne göre); ikisini de SAYABİLİRİZ ama
    # şeklini UYDURAMAYIZ — tanımadığımız şekilde sayı None kalır.
    karartma_n = len(radar) if isinstance(radar, (list, dict)) else None
    nedenler = []
    if health.halted():
        nedenler.append({"ad": "HALT", "aciklama": "sistem durdurulmuş — yeni risk alınmaz",
                         "kanit": "health.halted() = True"})
    try:
        _b = float(butce)
    except (TypeError, ValueError):  # sessiz-yutma: bütçe alanı hiç gelmediyse EŞİK DENENMEZ; bilinmeyeni "sıfır bütçe" saymak eylemsizliğe yanlış ad takardı
        _b = None
    if _b is not None and _b <= 0:
        nedenler.append({"ad": "REJİM BÜTÇESİ 0", "aciklama": "rejim maruziyet bütçesi sıfır — "
                                                              "bugün yeni risk açılmaz (tasarım)",
                         "kanit": f"exposure_budget_pct = {butce}"})
    if son_erteleme is not None:
        nedenler.append({"ad": "SEANS ERTELENDİ", "aciklama": str(son_erteleme.get("detail") or "")[:160],
                         "kanit": f"session_deferred_for_coverage · son 3000 olayda "
                                  f"{say.get('session_deferred_for_coverage', 0)} kez · "
                                  f"kapsama {son_erteleme.get('coverage')}"})
    if karartma_n:
        nedenler.append({"ad": "KAZANÇ KARARTMASI", "aciklama": "karartma penceresindeki sembol var",
                         "kanit": f"blackout_radar · {karartma_n} kayıt"})
    return {"var": True, "exposure_budget_pct": butce,
            "birincil": nedenler[0] if nedenler else None,
            "nedenler": nedenler,
            "neden_yok_aciklama": (None if nedenler else
                                   "ölçülen dört zorlayıcı nedenden HİÇBİRİ yok — eylemsizliğin "
                                   "sebebi bu dörtlüde DEĞİL; kapı kararlarına bakılmalı."),
            "verdict_counts": verdict, "gate_reasons": kapi_nedenleri,
            "olay_sayaci": say, "olay_penceresi": len(olaylar),
            "halted": health.halted(), "learn_halted": health.learn_halted(),
            "data_ok": hb.get("data_ok")}


def _hat_cizelgesi(wd: dict, sched: dict) -> dict:
    """C1-4 · Gece hattının CANLI zaman çizelgesi — damgalar nihayet uca açılıyor.

    D2-b `saglik#cizelge` yüzeyini kurarken şunu BEYAN ETMİŞTİ: "'bu adım saat 03:12'de koştu'
    bilgisi bu uçtan GELMİYOR — adım başına damga `state/mechanism_beats.json`da var ama panoya
    açılmamış. Damgaların uca açılması D3-UI'ın işi." Bu fonksiyon o borcu kapatır.

    UYDURMA YOK, TÜRETME DE YOK: damga dosyada epoch olarak duruyor ve OLDUĞU GİBİ taşınır
    (ISO'ya çevrilir, çünkü panonun geri kalanı ISO okur). Damgası olmayan mekanizma için saat
    ÜRETİLMEZ — `beat: None` gider ve pano "kendi damgası yok" der."""
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    beats = store.read_json("mechanism_beats.json", None)
    damgalar = {}
    if isinstance(beats, dict):
        for ad, ts in beats.items():
            try:
                damgalar[ad] = _dt.datetime.fromtimestamp(
                    float(ts), _dt.timezone.utc).isoformat(timespec="seconds")
            except (TypeError, ValueError, OSError, OverflowError):  # sessiz-yutma: bozuk/aralık-dışı epoch — o mekanizmanın damgası ÖLÇÜLEMEDİ kalır (anahtar hiç yazılmaz), diğerleri servis edilir
                continue
    # KOŞU DEFTERİ: `pipeline_runs.jsonl` her skill koşusuna başlangıç/bitiş damgası yazıyor —
    # yani hattın P-adımları için GERÇEK saat ve GERÇEK süre burada. Son 40 satır: bir gecenin
    # tamamı ~15 satır, iki-üç gece görünür kalsın diye.
    kosular = []
    for r in store.read_jsonl("pipeline_runs.jsonl")[-40:]:
        kosular.append({k: r.get(k) for k in
                        ("run_id", "pipeline", "started", "finished", "status", "error")}
                       | {"skills_invoked": len(r.get("skills_invoked") or []),
                          "skills_declared_not_run": len(r.get("skills_declared_not_run") or []),
                          "skills_skipped": len(r.get("skills_skipped") or []),
                          "artifacts": len(r.get("artifacts") or [])})
    kosular.reverse()
    # LLM ÇAĞRILARI: gecenin üçüncü ekseni. Pencere SINIRLI ve bu SÖYLENİR — `olay_penceresi`
    # yükle birlikte gider ki pano "son N olayda" diye yazabilsin. Boş liste "çağrı yapılmadı"
    # DEĞİLDİR, "bu pencerede görülmedi"dir; ayrımı pano cümlesi taşır.
    olaylar = obs.recent(3000)
    cagri = [{"ts": e.get("ts"), "kind": e.get("kind"), "model": e.get("model"),
              "attempt": e.get("attempt"), "empty": e.get("empty"),
              "tool_calls": e.get("tool_calls")}
             for e in olaylar if e.get("event") in ("agent_call", "agent_call_empty")][-30:]
    cagri.reverse()
    # DÖNGÜNÜN KENDİ KAYDI: `daily_cycle` GÜNDE BİR yazılır ve gün içindeki poll satırları onu
    # her olay penceresinden taşırır — v190'ın ölçtüğü kusurun ta kendisi ("kart 'ölçülemedi'
    # diyordu, döngü koşmuş olsa bile; ölçüm değil PENCERE bozuktu"). Bu yüzden çizelgenin
    # çıpası `_son_dongu()`dur: defterin KUYRUĞUNDAN pencereden bağımsız okur ve ÖNBELLEKLİDİR
    # (aynı istekte /api/today de onu çağırır — dosya damgası değişmediyse ikinci ayrıştırma yok).
    # Pencerede görülen ek döngü satırları ZENGİNLEŞTİRME olarak eklenir, çıpanın YERİNE geçmez.
    pencere_dongu = [{"ts": e.get("ts"), "date": e.get("date"), "regime": e.get("regime"),
                      "candidates": e.get("candidates"), "plans": e.get("plans"),
                      "armed": e.get("armed"), "open_positions": e.get("open_positions"),
                      "data_ok": e.get("data_ok"), "halted": e.get("halted")}
                     for e in olaylar if e.get("event") == "daily_cycle"][-8:]
    pencere_dongu.reverse()
    return {"var": True, "damgalar": damgalar,
            "damga_neden_yok": (None if damgalar else
                                "mechanism_beats.json okunamadı ya da boş — adım saatleri bu "
                                "turda ölçülemedi; bekçi penceresi yine de raporlanıyor."),
            "kosular": kosular, "cagrilar": cagri,
            "son_dongu": _son_dongu(), "donguler": pencere_dongu,
            "olay_penceresi": len(olaylar),
            "scheduler_updated": sched.get("updated"),
            "bekci_ok": wd.get("ok"), "bekci_total": wd.get("total")}


def _spend_detay() -> dict:
    """C1-3 · Gece koşusunun maliyet ve token karnesi.

    NEDEN /api/spend'E YENİ TÜKETİCİ BAĞLANMADI: o uç K1'de EMEKLİ edildi ve kaynağın kendi
    kuralı yazıyor — "bu uçlara YENİ tüketici bağlanmaz; kanonik yüzey /api/hermes `spend`".
    Kırılım o yüzden kanonik ucun içine, `spend.summary()`nin YANINA girer. Aynı defter iki uçtan
    iki farklı şekilde servis edilmez; yalnız kanonik olan zenginleşir.

    HESAP YOK, TOPLAM VAR: `cost_usd`/`in_tokens`/`out_tokens` satırlarda ZATEN yazılı; burada
    yalnız gruplanıyor. Alanı hiç taşımayan satır o toplama girmez ve `olculemeyen_satir` ile
    sayılır — eksik alanı 0 saymak "bedava çağrı" demek olurdu."""
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    rows = store.read_jsonl("spend.jsonl")
    if not rows:
        return _olculemedi("spend.jsonl boş ya da okunamadı — gece maliyeti bu turda ölçülemedi. "
                           "'Maliyet sıfır' DEĞİL: ölçüm defteri hiç yazılmamış olabilir.")
    ay = _dt.datetime.now(_dt.timezone.utc).isoformat()[:7]
    bu_ay = [r for r in rows if str(r.get("ts", ""))[:7] == ay]
    olculemeyen = 0

    def _topla(kume):
        nonlocal olculemeyen
        c = {"n": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0, "thought_tokens": 0}
        for r in kume:
            c["n"] += 1
            if r.get("cost_usd") is None:
                olculemeyen += 1
            for alan in ("in_tokens", "out_tokens", "cost_usd", "thought_tokens"):
                try:
                    c[alan] += float(r.get(alan) or 0)
                except (TypeError, ValueError):  # sessiz-yutma: dizgi/None token alanı — o SATIR toplama katılmaz ve `olculemeyen_satir` sayacı ayrıca beyan edilir; toplamın kendisi bozulmaz
                    continue
        c["cost_usd"] = round(c["cost_usd"], 4)
        return c

    def _grup(anahtar):
        out = {}
        for r in rows:
            k = str(r.get(anahtar) or "—")
            out.setdefault(k, []).append(r)
        return sorted(({"ad": k, **_topla(v)} for k, v in out.items()),
                      key=lambda d: (-d["cost_usd"], -d["n"]))

    # KOL = `note` alanının ilk sözcüğü ("reflect (gemini)" → "reflect"). Ham `note`u anahtar
    # yapmak her sağlayıcı için ayrı bir kol doğururdu; soru "hangi KOL yedi" (reflect/proposal/
    # backfill), "hangi model yedi" ayrı satırda zaten var.
    kollar = {}
    for r in rows:
        kol = str(r.get("note") or "—").split("(")[0].strip() or "—"
        kollar.setdefault(kol, []).append(r)
    gun = {}
    for r in rows:
        gun.setdefault(str(r.get("ts", ""))[:10] or "—", []).append(r)
    return {"var": True, "toplam": _topla(rows), "bu_ay": _topla(bu_ay), "ay": ay,
            "modeller": _grup("model"),
            "kollar": sorted(({"ad": k, **_topla(v)} for k, v in kollar.items()),
                             key=lambda d: (-d["cost_usd"], -d["n"])),
            "gunler": [{"gun": g, **_topla(v)} for g, v in sorted(gun.items())][-14:],
            "son": list(reversed(rows[-20:])),
            "olculemeyen_satir": olculemeyen, "satir_n": len(rows)}
            # KOTA DEFTERLERİ (`agent_budget.json` / `agent_tooluse.json`) BİLEREK BURADA DEĞİL.
            # İlk yazımda taşınıyorlardı ve bu YASA 6'nın kendi ihlaliydi: kartın hiçbir satırı
            # onları ÇİZMİYORDU — yani uç, okuyucusu olmayan iki alan üretecekti. Üstelik
            # `agent_tooluse.json` `codelaw.DECLARED_SINKS`te "iç okuyucusu var" diye muaf ve
            # buradan okumak o muafiyeti sessizce bayatlatırdı (test_codelaw_v59 ölçtü).
            # Kota YÜZÜ ayrı bir iştir (C2-1 ajan telemetrisi); bu kart harcamayı ölçer.


def _rollback_sicili() -> dict:
    """C1-5 · Otomatik geri-almanın sicili — PRODUCT.md'nin açık vaadinin İLK panosal kanıtı.

    ÖLÇÜLEN KUSUR: `app.js` içinde "rollback" kelimesi SIFIR kez geçiyordu. Vaadin görünmezliği
    vaadi ölçülemez yapar. Sicil ÜÇ kaynaktan derlenir ve üçü de bugün diskte duruyor:
      * `scoreboard.versions[].rolled_back / reinstated / source` — hangi sürüm geri alındı
      * `learning_loop_open.json` — şu an AÇIK bir öğrenme döngüsü var mı (boş sözlük = yok)
      * olay defteri `rollback_like_for_like_overturn` + `learning_loop_open` — çürütme kaydı

    HİÇBİRİ ÜRETİLMEZ: dosya yoksa dal ÖLÇÜLEMEDİ döner. "Hiç rollback olmadı" ile "bakamadık"
    aynı piksele düşemez — bu turun kapattığı sınıfın ta kendisi."""
    sb = store.read_json("scoreboard.json", None)
    if not isinstance(sb, dict) or not isinstance(sb.get("versions"), dict):
        return _olculemedi("scoreboard.json okunamadı ya da `versions` taşımıyor — geri-alma "
                           "sicili bu turda ölçülemedi; 'hiç geri alınmadı' DEĞİL.")
    surumler = []
    for v, info in sorted((sb.get("versions") or {}).items(), key=lambda t: -int(t[0])):
        if not isinstance(info, dict):
            continue
        surumler.append({
            "version": v, "rolled_back": info.get("rolled_back"),
            "reinstated": info.get("reinstated"), "source": info.get("source"),
            "note": info.get("note"), "parent": info.get("parent"),
            "live_score": info.get("live_score"), "backtest_oos": info.get("backtest_oos"),
            "baseline_verdict": info.get("baseline_verdict"),
            "baseline_source": info.get("baseline_source"),
            "baseline_n_trades": info.get("baseline_n_trades"),
            "n_trades": info.get("n_trades"), "live_since": info.get("live_since"),
            "guncel": str(v) == str(sb.get("current_version")),
        })
    acik = store.read_json("learning_loop_open.json", None)
    olaylar = obs.recent(3000)
    kayitlar = [{"ts": e.get("ts"), "event": e.get("event"), "version": e.get("version"),
                 "parent": e.get("parent"), "reason": e.get("reason"),
                 "detay": {k: v for k, v in e.items()
                           if k not in ("ts", "level", "event", "version", "parent", "reason")}}
                for e in olaylar
                if str(e.get("event") or "").startswith(("rollback", "learning_loop"))][-20:]
    kayitlar.reverse()
    return {"var": True, "current_version": sb.get("current_version"), "surumler": surumler,
            "geri_alinan_n": sum(1 for s in surumler if s["rolled_back"]),
            "acik_dongu": acik if isinstance(acik, dict) else None,
            "acik_dongu_neden": (None if isinstance(acik, dict) else
                                 "learning_loop_open.json okunamadı — AÇIK döngü olup olmadığı "
                                 "ölçülemedi (boş sözlük 'açık döngü yok' demektir, bu ondan farklı)."),
            "olaylar": kayitlar, "olay_penceresi": len(olaylar),
            "esik": (config.goal() or {}).get("rollback_if_worse_by")}


def _regresyon_kirilimi() -> dict:
    """C1-6 · "Bu sürüm neyi düzeltti, NEYİ BOZDU" — toplam skorun gizlediği tek şey.

    ÖLÇÜLEBİLİR OLANIN SINIRI BURADA YAZILI. `trades.jsonl` satırları `strategy_version` damgası
    TAŞIYOR — yani sürüm × rejim ve sürüm × çıkış-nedeni kırılımı GERÇEKTEN ölçülebilir. Ama iki
    şey ölçülemez ve söylenir:
      * Sürümlerin çoğunda örneklem 30'un altında; dilim ortalaması bir HÜKÜM değil bir GÖZLEMdir
        ve `az_ornek` bayrağıyla taşınır (eşik `IC_MIN_SAMPLE` DEĞİL — o sıralama korelasyonunun
        eşiği; burada kullanılan `AZ` yalnız bir görünürlük çizgisi, hiçbir karar ona bağlı değil).
      * `hypotheses` tahmin↔gerçekleşen çiftinde `realized_delta` yalnız kapanmış döngülerde var.
    UYDURMA YOK: n=0 dilim hiç yazılmaz, ortalama None kalır."""
    trades = store.read_jsonl("trades.jsonl")
    if not trades:
        return _olculemedi("trades.jsonl boş — sürüm başına regresyon kırılımı ölçülemedi; "
                           "kapanmış işlem olmadan 'neyi bozdu' sorusunun paydası kurulamaz.")
    AZ = 10        # yalnız GÖRÜNÜRLÜK çizgisi (app.js `AZ_ORNEK_N` ile aynı sayı, aynı gerekçe)

    def _ort(xs):
        xs = [float(x) for x in xs if isinstance(x, (int, float))]
        return round(sum(xs) / len(xs), 3) if xs else None

    surum = {}
    for t in trades:
        v = t.get("strategy_version")
        if v is None:
            continue
        s = surum.setdefault(str(v), {"n": 0, "r": [], "rejim": {}, "cikis": {}, "setup": {}})
        s["n"] += 1
        s["r"].append(t.get("r_multiple"))
        for eksen, alan in (("rejim", "regime"), ("cikis", "exit_reason"), ("setup", "setup")):
            k = str(t.get(alan) or "—")
            d = s[eksen].setdefault(k, [])
            d.append(t.get("r_multiple"))
    cikti = []
    for v, s in sorted(surum.items(), key=lambda t: -int(t[0]) if t[0].isdigit() else 0):
        def _dilim(d):
            return sorted(({"ad": k, "n": len(xs), "avg_r": _ort(xs), "az_ornek": len(xs) < AZ}
                           for k, xs in d.items()), key=lambda x: -x["n"])
        cikti.append({"version": v, "n": s["n"], "avg_r": _ort(s["r"]),
                      "az_ornek": s["n"] < AZ,
                      "rejim": _dilim(s["rejim"]), "cikis": _dilim(s["cikis"]),
                      "setup": _dilim(s["setup"])})
    # DÜZELTTİ/BOZDU: ardışık iki sürüm arasında dilim-başına delta. En az iki sürüm gerekir —
    # tek sürümde "neyi bozdu" sorusunun karşılaştırma tarafı YOKTUR ve uydurulamaz.
    fark = None
    if len(cikti) >= 2:
        yeni, eski = cikti[0], cikti[1]
        eski_rejim = {d["ad"]: d for d in eski["rejim"]}
        kalemler = []
        for d in yeni["rejim"]:
            o = eski_rejim.get(d["ad"])
            if not o or d["avg_r"] is None or o["avg_r"] is None:
                kalemler.append({"ad": d["ad"], "delta_r": None,
                                 "neden": "karşılaştırma dilimi yok ya da ortalama ölçülemedi"})
                continue
            kalemler.append({"ad": d["ad"], "delta_r": round(d["avg_r"] - o["avg_r"], 3),
                             "n_yeni": d["n"], "n_eski": o["n"],
                             "az_ornek": d["az_ornek"] or o["az_ornek"]})
        fark = {"yeni": yeni["version"], "eski": eski["version"], "rejim": kalemler}
    hip = []
    for h in store.read_jsonl("hypotheses.jsonl")[-12:]:
        g = h.get("backtest") or {}
        hip.append({"id": h.get("id"), "variable": h.get("variable"), "status": h.get("status"),
                    "version_to": h.get("version_to"), "version_from": h.get("version_from"),
                    "predicted_delta": h.get("predicted_delta"),
                    "realized_delta": h.get("realized_delta"),
                    "reject_reasons": h.get("reject_reasons") or [],
                    "candidate_oos": g.get("candidate_oos"), "dsr": (g.get("dsr") or {}).get("dsr"),
                    "dsr_dusuk": g.get("dsr_dusuk"), "ship_modu": g.get("ship_modu")})
    hip.reverse()
    return {"var": True, "surumler": cikti, "fark": fark, "hipotezler": hip,
            "az_ornek_esigi": AZ, "islem_n": len(trades),
            "sinir": "Kırılım YALNIZ `strategy_version` damgalı kapanmış işlemlerden türer. "
                     "Damgasız satır hiçbir sürüme yazılmaz; dilim n'i küçükse `az_ornek` "
                     "bayrağı taşır ve bir hüküm değil bir gözlemdir."}


# ---- C1-7 · DENETİM İZİNİN TAMAMI — SORGULANABİLİR UÇ -----------------------------------------
# ETÜDÜN KENDİ HÜKMÜ (§C1-7): "Tavanların kendisi bir performans kararıydı — çözüm tavanı
# kaldırmak değil, SORGULANABİLİR kılmak." `/api/signals` 390 planın son 120'sini veriyor ve
# tavanı dürüstçe beyan ediyor; eksik olan, defterin TAMAMI üstünde soru sorabilmekti.
#
# NEDEN AYRI UÇ: sorgu parametresi taşır. `/api/diagnostics` 45 sn önbelleklidir ve parametreli
# bir okuma o kutuya giremez (ilk sorgunun cevabı ikinci sorguya servis edilirdi — sessiz ve
# teşhisi zor). YALNIZ OKUMA: hiçbir dal state'e dokunmaz.
@app.get("/api/audit_trail")
def api_audit_trail(request: Request, sembol: str = "", verdict: str = "", limit: int = 60):
    """Plan defterinin TAMAMI üstünde filtrelenebilir denetim izi + sembol ekseni özeti."""
    _auth(request)
    limit = max(1, min(400, int(limit or 60)))
    hepsi = store.read_jsonl("trade_plans.jsonl")
    sembol_u = (sembol or "").strip().upper()
    verdict_u = (verdict or "").strip().lower()
    sayim, verdict_sayim = {}, {}
    for p in hepsi:
        t = str(p.get("ticker") or "—")
        v = str(p.get("gate_verdict") or "—")
        s = sayim.setdefault(t, {"ticker": t, "n": 0, "verdicts": {}, "ilk": None, "son": None})
        s["n"] += 1
        s["verdicts"][v] = s["verdicts"].get(v, 0) + 1
        d = p.get("date")
        if d:
            s["ilk"] = min(s["ilk"] or d, d)
            s["son"] = max(s["son"] or d, d)
        verdict_sayim[v] = verdict_sayim.get(v, 0) + 1
    secili = [p for p in hepsi
              if (not sembol_u or str(p.get("ticker") or "").upper() == sembol_u)
              and (not verdict_u or str(p.get("gate_verdict") or "").lower() == verdict_u)]
    satirlar = [{"date": p.get("date"), "ticker": p.get("ticker"), "setup": p.get("setup"),
                 "score": p.get("score"), "verdict": p.get("gate_verdict"),
                 "reasons": p.get("gate_reasons") or [],
                 "checks": p.get("gate_checks") or [],
                 "entry_trigger": p.get("entry_trigger"), "id": p.get("id"),
                 "exploration": bool(p.get("exploration")),
                 "llm_veto": bool(p.get("llm_veto"))}
                for p in secili[-limit:]]
    satirlar.reverse()
    return {
        "sorgu": {"sembol": sembol_u or None, "verdict": verdict_u or None, "limit": limit},
        # TAVAN BEYANI KORUNUR — ama artık PAYDAYLA: kaç satır eşleşti, kaçı gösterildi.
        "defter": {"plans_total": len(hepsi), "eslesen": len(secili),
                   "gosterilen": len(satirlar), "limit": limit},
        "satirlar": satirlar,
        "verdict_sayim": verdict_sayim,
        "semboller": sorted(sayim.values(), key=lambda s: -s["n"])[:60],
        "sembol_n": len(sayim),
        # DEFTER BOŞSA UYDURMA YOK: pano bunu okuyup ÖLÇÜLEMEDİ dalına girer.
        "neden": (None if hepsi else
                  "trade_plans.jsonl boş ya da okunamadı — denetim izi bu turda ölçülemedi; "
                  "'hiç plan kurulmadı' DEĞİL."),
    }


@app.get("/api/diagnostics")
def api_diagnostics(request: Request, taze: int = 0):
    """Faz 1 — Teşhis API'si: diskte zaten duran tüm operasyon telemetrisini TEK uçta toplar.
    Mutabakat (hayaletler, HWM çiftleri, force-sync), risk/bütçe, MLOps (diff, deflasyon, ısınma,
    UCB), veri hattı (sabır, karantina, IO gecikme, çapraz-doğrulama), defter sayaçları.

    YANIT 45 SANİYE ÖNBELLEKLİDİR (`hesaplama_ts` + `onbellekten` ile beyanlı; `?taze=1` zorlar) —
    gerekçe ve TTL'in nereden geldiği yukarıdaki blokta yazılı."""
    _auth(request)
    _kopya = _diag_onbellek_oku(bool(taze))
    if _kopya is not None:
        return _kopya
    from . import analytics as an, earnings
    from .adapters.data import REPLAY_UNIVERSE
    rc = store.read_json("broker_reconcile.json", {})
    pf = store.read_json("portfolio.json", {})
    mirror = store.read_json("mirror_orders.json", {})
    stream = _stream_view(mirror)          # ham `mirror["stream_ok"]` DEĞİL — nabızla çarpılmış hâli
    sched = store.read_json("scheduler_status.json", {})
    # DOSYA + CANLI BELLEK: hermes_status.json yalnız poll SONUNDA yazılır, dakikalarca süren bir
    # yansıma boyunca donuk kalır — pano "poll yapılmadı" diye okuyordu (2026-07-22). Aynı süreçteki
    # canlı `_state` gerçeği taşır; dosya yalnız döngü bu süreçte hiç başlamadıysa taban olur.
    hstat = store.read_json("hermes_status.json", {})
    try:
        from . import hermes_runtime as _hrt
        if _hrt._state:
            hstat = {**hstat, **_hrt._state}
    except Exception:  # sessiz-yutma: döngü modülü yoksa dosya zaten geçerli tabandır
        pass
    dq = store.read_json("data_quality.json", {})
    today = dq.get("date") or rc.get("date") or ""
    # 1b: iç HWM (pozisyonun trail_stop'u) vs Alpaca'ya giden son PATCH — yan yana + desync bayrağı
    last_patch = {t["ticker"]: t for t in (rc.get("trail_synced") or [])}
    hwm = []
    for tkr, p in (pf.get("positions") or {}).items():
        lp = last_patch.get(tkr, {})
        hwm.append({"ticker": tkr, "internal_trail": p.get("trail_stop"),
                    "last_patch_to": lp.get("to"), "patch_ok": lp.get("ok"),
                    "desync": bool(lp) and not lp.get("ok")})
    # 3a: tek-değişken diff — son hipotezler (old→new + arama/onay etkisi)
    diffs = []
    for h in store.read_jsonl("hypotheses.jsonl")[-10:]:
        # DSR DAMGASI SHIP GEÇMİŞİNE TAŞINIR (v130): kâğıt modunda düşük DSR ship'i BLOKLAMIYOR
        # (bilinçli — kâğıt evrimi ölçüm aracı), ama bloklamamak SUSMAK demek değildir. Damga
        # olmadan "hangi sürümler zayıf istatistiksel kanıtla canlıya çıktı?" sorusu ancak kapı
        # kaydını elle açarak cevaplanabilirdi. `dsr_dusuk` ÜÇ DEĞERLİDİR: True/False/None ve None
        # "ölçülemedi" demektir (0.0 ya da False DEĞİL — uydurma yasağı).
        _g = h.get("backtest") or {}
        diffs.append({"id": h.get("id"), "variable": h.get("variable"),
                      "old": h.get("old"), "new": h.get("new"), "status": h.get("status"),
                      "predicted_delta_search": h.get("predicted_delta_search"),
                      "predicted_delta": h.get("predicted_delta"),
                      "realized_delta": h.get("realized_delta"),
                      "dsr": (_g.get("dsr") or {}).get("dsr"),
                      "dsr_dusuk": _g.get("dsr_dusuk"), "dsr_durum": _g.get("dsr_durum"),
                      "ship_modu": _g.get("ship_modu")})
    # Faz 4 (1c): parçalı dolum R-ayrıştırma matrisi — WS'in gördüğü filled_qty ile planın
    # risk şeması birleşir: gerçekleşen R (dolan kısım) vs açık kalan R (bekleyen kısım).
    plans_by_id = {pln.get("id"): pln for pln in store.read_jsonl("trade_plans.jsonl")}
    partial = []
    for coid, o in (mirror.get("orders") or {}).items():
        try:
            fq, tq = float(o.get("filled_qty") or 0), float(o.get("qty") or 0)
        except (TypeError, ValueError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
            continue
        if tq <= 0 or fq <= 0 or fq >= tq or str(o.get("status", "")).lower() in ("filled", "canceled", "rejected", "expired"):
            continue
        pln = plans_by_id.get(coid) or {}
        sr = float(pln.get("size_r") or 1.0)
        partial.append({"ticker": o.get("symbol"), "coid": coid, "filled_qty": fq, "total_qty": tq,
                        "fill_pct": round(100 * fq / tq, 1),
                        "realized_risk_r": round(sr * fq / tq, 3),
                        "open_risk_r": round(sr * (1 - fq / tq), 3)})
    # Faz 4 (3b): son olasılıksal kapı koşusunun çan eğrisi (histogram hipotez kaydında taşınır)
    last_hist = None
    for h in reversed(store.read_jsonl("hypotheses.jsonl")):
        g = (h.get("backtest") or {})
        if g.get("search_hist"):
            last_hist = {"id": h.get("id"), "variable": h.get("variable"), **g["search_hist"]}
            break
    # 3d: UCB sıralaması (ısınma termometresinin 'öncelikler' yarısı) — defterden deterministik
    ucb_top = []
    try:
        from . import reflect
        ucb_top = [str(v) for v in reflect._ucb_rank(sorted(config.bounds().keys()),
                                                     memory.all_hypotheses())[:5]]
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        pass
    # Bölüm 2 (Gate Keeper): SON seansın planları, yapılandırılmış karar ağacıyla — "geçiş anı" izlenir
    all_plans = store.read_jsonl("trade_plans.jsonl")
    last_plan_date = all_plans[-1].get("date") if all_plans else None
    gk_plans = [{"ticker": pln.get("ticker"), "setup": pln.get("setup"), "score": pln.get("score"),
                 "verdict": pln.get("gate_verdict"), "reasons": pln.get("gate_reasons") or [],
                 "checks": pln.get("gate_checks") or [], "exploration": bool(pln.get("exploration")),
                 "llm_opinion": pln.get("llm_opinion"), "llm_veto": bool(pln.get("llm_veto"))}
                for pln in all_plans if pln.get("date") == last_plan_date][:12]
    hb = store.read_json("heartbeat.json", {})
    # TEK OKUMA ANI (v192 deseni): `regime.json` ve karartma radarı AŞAĞIDA İKİ tüketici tarafından
    # okunuyor — `risk.regime`/`risk.blackout_radar` ve eylemsizlik özeti (C1-8). İkisini ayrı ayrı
    # çağırmak aynı yanıtın içinde iki farklı gerçek doğurabilirdi (radar takvim tazelemesiyle
    # değişir) ve radar evren boyunda bir hesap — bedeli ikiye katlamanın karşılığı yok.
    _rejim_doc = store.read_json("regime.json", {})
    _radar = earnings.blackout_radar(list(REPLAY_UNIVERSE), today)
    warm_ticks = int(hstat.get("_warm_ticks") or 0)
    try:
        from .hermes_runtime import WARMUP_EVERY_POLLS as _wep
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        _wep = 12
    _sr = store.read_json("self_review.json", None)
    # REDIS SICAK KATMAN (intraday): available() bilerek PING atar — kesinti bir sonraki döngüyü
    # BEKLEMEDEN anlık görünmeli (hotstate.py ilkesi). Redis yoksa graceful: ok=False, veri kaybı YOK
    # (kalıcı gerçek dosya defterlerinde). Testlerde _redis None'a sabitli → ping sessizce ok=False.
    from . import hotstate as _hs
    _hs.available()
    hot = _hs.health()
    # Faz 4: intraday gözlem sağlığı + kararların ÖZETİ. intraday_decisions.jsonl'i DIŞ modül (api) okur —
    # 'kendi yazdığını kendi okuyan tüketici değildir' yasası (codelaw). Gözlem-modunun amacı bu ölçümleri
    # operatöre görünür kılmak; bu okuma o görünür tüketicidir.
    _integrity_rep, _integrity_age = __import__(
        "meridian.watchdog", fromlist=["integrity_report_cached"]).integrity_report_cached()
    # BEKÇİ RAPORU TEK KEZ (WP-P/P1): hem `watchdog` satırı hem sessiz hat okuyor. İki çağrı iki
    # okuma anı demektir ve aynı yanıtta iki farklı "kaç bekçi gecikti" cevabı doğabilirdi.
    _wd = __import__("meridian.watchdog",
                     fromlist=["report", "alarm_budget_cached"])
    _wd_rep = _wd.report()
    _alarm_rep, _alarm_age = _wd.alarm_budget_cached()
    _intra = __import__("meridian.intraday_cycle", fromlist=["health"]).health()
    _idec = store.read_jsonl("intraday_decisions.jsonl")
    _intra["decisions"] = {"total": len(_idec), "fired": sum(1 for r in _idec if r.get("fired")),
                           # BUGÜNÜN sayısı ayrı: toplam ömür boyu birikir ve "bugün akış çalıştı mı?"
                           # sorusunu ASLA cevaplayamaz — dünkü 400 satır bugünkü sessizliği gizler.
                           "today": sum(1 for r in _idec if str(r.get("ts") or "")[:10] == today),
                           "recent": list(reversed(_idec))[:8]}
    # SİLAHLI PLAN SAYISI ≠ INTRADAY SİLAHLANMA BAYRAĞI. `intraday.armed` operatörün Faz 4b bayrağıdır;
    # burası defterdeki EOD-silahlı plan sayısı — gözlem tüketicisinin ölçecek bir şeyi olup olmadığı.
    # Sıfırsa kart "seans silahsız açılıyor" der; bu bir arıza değil, o günün dürüst hâli.
    _intra["armed_plans"] = len((pf or {}).get("armed") or [])
    # FAZ 4B GÖLGE: "tetik kesilseydi NE olurdu" defterinin DIŞ okuyucusu burasıdır (kendi yazdığını
    # kendi okuyan tüketici sayılmaz — codelaw artifact_graph yasası; intraday_decisions.jsonl ile
    # AYNI desen). Gölge emir GÖNDERMEZ; bu blok yalnız kararı ve EOD dolgusuyla farkını panoya taşır.
    _ishadow = store.read_jsonl("intraday_shadow_orders.jsonl")
    _intra["shadow"] = __import__("meridian.intraday_shadow",
                                  fromlist=["summarize"]).summarize(_ishadow)
    # 5.3 SEANS-İÇİ KESİNTİ/BOŞLUK RAPORU — YASA 6 tüketicisi (pano `RENDER.intraday`).
    # BURADA YENİDEN HESAPLANMAZ: ölçümü zamanlayıcı kancası (`scheduler._intraday_gap_check`) her
    # poll'de bir kez yapar ve durum dosyasına yazar. Panonun her anketinde yeniden taramak, aynı
    # gerçeği iki farklı ANDA ölçüp iki farklı cevap üretirdi (ve dosya kuyruğunu her F5'te okurdu).
    # `None` = kanca bu süreçte hiç koşmadı — "boşluk yok" DEĞİL, "bakılmadı" (üçüncü hâl).
    _intra["akis_boslugu"] = sched.get("intraday_gap")
    # ---- FAZ-6 KİLİT ZİNCİRİNİN ÜÇ GİRDİSİ TEK KEZ HESAPLANIR (v130) ----------------------------
    # `edge_verdict`/`result_verdict` blok-bootstrap CI koşuyor ve `validation_trio` DSR hesaplıyor.
    # Üçü hem kendi satırlarında hem kilit zincirinde okunuyor; ikinci kez çağırmak aynı istekte aynı
    # bootstrap'i iki kez koşturmak olurdu. AYNI NESNE paylaşılır — yoksa tek yanıtta "EDGE 3/5" ile
    # "kilit: EDGE 4/5" gibi iki farklı gerçek belirebilirdi (aynı istekte iki ayrı okuma anı).
    _edge_v, _sonuc_v, _trio_v = an.edge_verdict(), an.result_verdict(), an.validation_trio()
    # HAFTALIK KANIT RAPORU: DIŞ okuyucu burasıdır (yazan scheduler._weekly_validation) — dosya adı
    # LİTERAL yazılır, `codelaw.artifact_graph` statik graf olduğu için sabitten türetilen adı
    # çözemez ve artefakt "okuyucusu yok" diye görünürdü.
    _vrep = store.read_json("validation_report.json", None)
    # ELEME DEFTERİ TEK KEZ (v192): hem `sieve` satırı hem `ogrenme.son_fit`in terfi hükmü okuyor.
    # İki çağrı iki okuma anı demektir ve aynı yanıtta "0 çift çıktı" ile "3 çift çıktı" gibi iki
    # farklı gerçek doğabilirdi (`_wd_rep` ile bire bir aynı gerekçe, WP-P/P1).
    _sieve_rep = __import__("meridian.sieve", fromlist=["report"]).report()
    # `_diag_onbellege_yaz`: taze yükü damgalar (hesaplama_ts + onbellekten=False) ve kutuya koyar.
    # SARMALAYICI RETURN'ÜN İÇİNDE: gövde fırlarsa hiçbir şey önbelleğe girmez — yarım/hatalı bir
    # teşhis 45 saniye boyunca servis edilemez.
    return _diag_onbellege_yaz({
        "selfreview_summary": ({"attention": (_sr.get("attention") or [])[:5],
                                "contradictions": (_sr.get("contradictions") or [])[:4],
                                "generated": _sr.get("generated")} if _sr else None),
        "hud": {"mode": config.MODE, "broker": config.BROKER,
                "regime": hb.get("regime"), "exposure_budget_pct": hb.get("exposure_budget_pct"),
                "explore_mode": bool(hb.get("explore_mode")), "equity": hb.get("equity"),
                "last_bar": hb.get("last_bar"), "heartbeat_age_s": health.heartbeat_age_seconds(),
                # HAM BAYRAK YALAN SÖYLEYEBİLİR (2026-07-22): dinleyici görevi ölse dosyadaki
                # `stream_ok: true` diskte DONAR ve pano "WS canlı" gösterir. Canlı kanıt:
                # stream_ok=true iken last_event_ts 3 gün eskiydi. Dürüst değer bayrağı nabız
                # tazeliğiyle çarpar; şerit "ne kadardır kopuk"u da buradan okur.
                **stream, "halted": health.halted(),
                "learn_halted": health.learn_halted(), "data_ok": hb.get("data_ok")},
        "scheduler": {"updated": sched.get("updated"), "last_tick": sched.get("last_tick"),
                      "poll_seconds": sched.get("poll_seconds"), "cycles": sched.get("cycles"),
                      # ÖĞRENME KADANSININ SEANS DAMGASI (2026-07-30): zamanlayıcı seans-sonrası
                      # kancasında antrenman/Eksen-2/dolgu koşturuyor. "Hangi seans için koştu"
                      # sorusu buradan cevaplanır; koşunun İÇERİĞİ `ogrenme` bloğunda.
                      "learn_session": sched.get("learn_session"),
                      # TEMİZLİK TURU KADANSLARININ DAMGALARI (2026-07-30): "hangi seans için Y4
                      # topladı" ve "hangi hafta doğrulama üçlüsünü koştu". İçerikleri sırasıyla
                      # `saglayicilar` ve `mlops.validation_report`/`shadowlaw_drift` bloklarında.
                      "y4_session": sched.get("y4_session"),
                      "validation_week": sched.get("validation_week")},
        # SAĞLAYICI SAĞLIK KARTI (ROADMAP 5.2) — beş adaptörün sağlık sayaçları TEK yerde,
        # ortak biçimde. app.js'e bu turda DOKUNULMADI: alanlar hazır, pano turu bağlayacak.
        "saglayicilar": _saglayicilar(sched),
        # ÖĞRENME OTOMASYONU (2026-07-30) — antrenman durumu + Eksen-2 üreteci + dolgu kuyruğu,
        # üçü TEK blokta. app.js'e bu turda DOKUNULMADI: alanlar hazır, pano turu bağlayacak.
        # Neden mlops'un içinde DEĞİL: mlops kalibrasyon ÇIKTILARINI taşır (Brier, IC, kapı çanı);
        # burası o çıktıları ÜRETEN kadansların sağlığıdır. İkisini karıştırmak, "ölçüm kötü" ile
        # "ölçüm hiç koşmadı"yı aynı karta koymak olurdu — bu turun bulduğu kusurun ta kendisi.
        # `son_fit` zenginleştirmesi v192: kadans nabzı ile MODELİN son fiili fit'i AYRI iki
        # gerçektir; kart ikisini yan yana göstermezse "antrenman hiç koşmamış" okunur (operatör
        # şikâyeti 2026-08-06). Zenginleştirme YENİ ÖLÇÜM ÜRETMEZ — `training_status`ın okuyucusuz
        # duran alanlarını (son_fit_ts/n_fit/brier_train) taşır ve terfi hükmünün NEDENİNİ eleme
        # defterinden (sieve) okur.
        "ogrenme": _ogrenme_blogu(an.learning_automation(), _sieve_rep),
        "gatekeeper": {"date": last_plan_date, "plans": gk_plans,
                       "arming": store.read_json("arming_report.json", {})},
        "reconcile": {"date": rc.get("date"), "api_ok": rc.get("api_ok"),
                      "ghosts": rc.get("ghosts") or [], "force_sync": rc.get("force_sync") or {},
                      "stripped": rc.get("stripped") or [], "drift": rc.get("drift") or [],
                      **stream,                 # kesinti süresi + son hata da görünür (hud ile AYNI
                      "hwm_pairs": hwm,         # okuma: tek yanıtta iki farklı gerçek olamaz)
                      "partial_fills": partial,
                      # AÇIK / KAPATILMIŞ AYRIMI (2026-07-27): şeridi besleyen sayı yalnız `open`.
                      # Kapatılanlar pakette KALIR (tarihçe silinmez, sesi kısılır) — /api/alpaca
                      # aynı ayrımı uygular, iki uç aynı alanı iki farklı şekilde servis edemez.
                      "failed_submissions": health.split_rejections(rc.get("failed_submissions")),
                      # EMİR YAŞAM-DÖNGÜSÜ (D3-UI · C1-2): `mirror_orders.json` bugüne kadar yalnız
                      # `_stream_view` için okunuyordu — coid başına status/filled_qty/
                      # filled_avg_price panoya HİÇ ulaşmıyordu. Evi `reconcile`: "emrin gerçekte
                      # ne olduğu" ailesi (partial_fills/failed_submissions ile aynı sözlük).
                      "emir_yasam": _emir_yasam()},
        # ---- İCRA GERÇEKLİĞİ (WP-E, kart EXE-2026-001, 2026-07-31) — YASA 6 ZİNCİRİ ------------
        # Üç ölçüm de bugüne kadar HİÇBİR uçtan servis edilmiyordu, çünkü ikisi bugün doğdu ve
        # üçüncüsü (gece/gündüz) hiç sorulmamıştı. Neden `mlops` içinde DEĞİL: mlops öğrenme
        # kalibrasyonunun çıktılarıdır; burası EMRİN GERÇEKTE NE OLDUĞUdur (gönderildi mi, doldu
        # mu, kaça doldu, kâr hangi bacaktan geldi) — `reconcile` ile aynı aile.
        "icra": {
            # E2: gönderim/ret/veto sayıları, RET NEDENİ dağılımı (kartın (a) ölçütü:
            # `stop_vs_current` sınıfı sıfıra inmeli), iki bps dağılımı, iki-motor mutabakatı.
            "slipaj": an.entry_execution_summary(),
            # E3: kötümser maliyet bandının yürürlükteki hâli + E2'den AMPİRİK güncelleme ölçümü.
            # `ampirik_bps` None ise ölçüm henüz yok — 0.0 yazmak "maliyet yok" demek olurdu.
            "kotumser_band": an.pessimistic_band_update(),
            # E4: her işlemin tutuş yolu gece (close→open) / gündüz (open→close) bacaklarına
            # ayrılmış hâli + kaynak damgası (training ayrı) × tutuş dilimi çapraz tablosu.
            "gece_gunduz": an.night_day_split(),
        },
        "risk": {"regime": _rejim_doc,
                 "blackout_radar": _radar,
                 # KAZANÇ TAKVİMİNİN PIT BİRİKİM DEFTERİ (D, 2026-08-01) — `earnings.csv` tek anlık
                 # görüntüdür ve her tazeleme geçmişi EZER; defter "bu tarihler bu fetch gününde
                 # biliniyordu"yu biriktirir. DIŞ OKUYUCU BURASIDIR (YASA 6): sayaç panoya çıkar,
                 # asıl tüketici gelecekteki ölçüm turlarıdır (EDG-011 kartı).
                 # DOSYA ADI LİTERAL OKUNUR (trend_book.json ile aynı desen ve aynı gerekçe):
                 # `codelaw.artifact_graph` statik bir graftır; okuma `earnings` modülünün içinde
                 # kalsaydı defter "yazılıyor ama kimse okumuyor" görünürdü. Maliyet ölçülü: kadans
                 # HAFTALIK, yani ~52 satır/yıl — anket başına birkaç ms'lik ayrıştırma.
                 "earnings_pit": earnings.snapshot_stats(
                     store.read_jsonl("history/earnings_snapshots.jsonl")),
                 "halted": health.halted(), "learn_halted": health.learn_halted(),
                 # "BUGÜN NEDEN HİÇBİR ŞEY OLMADI" (D3-UI · C1-8). Alanların HEPSİ bu blokta ZATEN
                 # vardı (bütçe, karartma radarı, halt) ama hiçbiri eylemsizliğin ADI olarak
                 # okunmuyordu — pano dürüsttü ("aday yok") ve NEDENSİZDİ. Dört kaynak ÇAĞIRANIN
                 # elinden geçer (hb/regime/gk_plans/radar); ikinci kez okunsalardı aynı yanıtta
                 # iki farklı gerçek doğardı.
                 "eylemsizlik": _eylemsizlik(hb, _rejim_doc, gk_plans, _radar)},
        "mlops": {"recent_hypotheses": diffs, "deflate": an.deflate_stats(),
                  "deflate_why": an.deflate_why(), "gate_hist": last_hist,
                  "llm_calibration": store.read_json("llm_calibration.json", {}),
                  "exit_efficiency": store.read_json("exit_efficiency.json", None),
                  # REDDEDİLEN KARARLARIN KARNESİ (D3-UI · C1-1): `near_miss.json`ın İLK uç
                  # tüketicisi. Kardeşleri `exit_efficiency` ve `mae_profile` ile AYNI üretici
                  # (P5 kalibrasyonları) — evi de bu yüzden burası. Künye (`yalnız-simüle`,
                  # `n_real: 0`) yükle BİRLİKTE gider; ayrılırsa simüle kanıt gerçek gibi okunur.
                  "near_miss": _near_miss_karne(),
                  "gate_calibration": store.read_json("gate_calibration.json", {}),
                  "score_calibration": store.read_json("score_calibration.json", None),
                  # ---- KENAR SAĞLIĞI (2026-07-27): dört ölçüt TEK yükte, çünkü pano Bölüm 3'te tek
                  # kartta yan yana okunuyor. Üçü bugüne kadar HİÇBİR uçtan servis edilmiyordu:
                  #   * score_calibration_history — IC'nin zaman serisi (anlık değer üzerine yazılır)
                  #   * regime_edge.json — analytics her P5'te YAZIYOR, hiçbir uç okumuyordu (YASA 6)
                  #   * prediction_hit — tahmin↔gerçekleşen işaret isabeti (öğrenme çarkının kapanan ucu)
                  # benchmark_relative /api/performance'ta da var ama BU sayfa (Operasyon) yalnız
                  # /api/diagnostics'ten besleniyor; ikisi de aynı saf fonksiyonu çağırdığı için
                  # "iki farklı gerçek" riski yok — bayatlayacak bir kopya üretilmiyor.
                  "score_calibration_history": store.read_jsonl("score_calibration_history.jsonl")[-60:],
                  "regime_edge": store.read_json("regime_edge.json", None),
                  "benchmark_relative": an.benchmark_relative(),
                  # SPY-VETO ADAYININ SAYACI (K1, 2026-07-30): `vs_benchmark_at_ship` her ship'e
                  # damgalanıyor ama hiçbir yerde raporlanmıyordu — "20-30 gözlem birikince veriyle
                  # karar verilir" eşiğinin sayacı yoktu, yani karar anı asla tetiklenmeyecekti.
                  "benchmark_veto_tally": _benchmark_veto_tally(),
                  "prediction_hit": an.prediction_hit_rate(),
                  # DÖRT ÖLÇÜTÜN TEK HÜKMÜ (2026-07-27): dört sayıyı yan yana koymak, okurdan her
                  # bakışta yazılı olmayan bir birleştirme işlemi ister — ve o işlem her seferinde
                  # farklı çıkar. Eşikler analytics'te tek yerde; buradan servis edilen cümle onlardan
                  # TÜREVDİR. Alt ölçütler yukarıda ayrıca duruyor: hüküm onların yerine geçmez.
                  "edge_verdict": _edge_v,
                  # SONUÇ HÜKMÜ — EDGE'İN İKİZİ, DOLAR MERCEĞİ (1B, Hafta 3a 2026-07-30). EDGE
                  # "kenar var mı?"yı R biriminde sorar; R birimi geniş stopa YAPISAL önyargılı
                  # (ROADMAP §4), yani sermaye kararı tek başına ona bırakılamaz. Bu hüküm aynı
                  # defteri DOLAR biriminde yargılar: friksiyon-sonrası işlem başına beklenti
                  # (blok-bootstrap CI) + profit factor + maks düşüş + net PnL vs ödenen friksiyon.
                  # KARAR KULLANIMI: rafineri kararları EDGE'e, sermaye/silahlanma İKİSİNE bakar.
                  "result_verdict": _sonuc_v,
                  # ATRİBÜSYON KABLOSU (AT-1, 2026-07-31): işlem-penceresi alfa/beta + aile ×
                  # rejim × tutuş-dilimi kırılımı. `result_verdict.beta_duzeltilmis` ile AYNI
                  # NESNEDİR (yeniden hesaplanmaz): `trade_alpha_beta` SPY barlarını diskten
                  # okuyor ve aynı istekte iki kez çağrılsaydı hem boşuna iş yapılır hem de tek
                  # yanıtta iki farklı okuma anı doğardı (edge/result/trio üçlüsüyle aynı gerekçe).
                  # ADVISORY: hiçbir kapıya bağlı değil, dört dolar ölçütünü DEĞİŞTİRMEZ.
                  "alpha_beta": _sonuc_v.get("beta_duzeltilmis"),
                  # DEFTERİN KAYNAK SAYAÇLARI (BT-1): teşhis sayfası "ölçüm zemini" sorusunu
                  # burada cevaplar — kaç satır canlı kanıt, kaç satır replay tohumu (training),
                  # kaç satır ayırt edilemedi. /api/today AYNI saf fonksiyonu çağırır.
                  "ledger_source": __import__("meridian.ledgerstamp",
                                              fromlist=["counts"]).counts(),
                  # PORTFÖY ISISI (3B): masadaki toplam açık risk tek sayı + NAV yüzdesi. YALNIZ
                  # GÖSTERGE — bu turda hiçbir kapıya bağlı değil (ısı tavanı Hafta 3b'nin
                  # default-OFF knob'u). `today.current_exposure_pct` GİRİŞTEKİ riski toplar;
                  # buradaki sayı YÜRÜRLÜKTEKİ stopa göredir ve ikisi bir kazananda ayrışır.
                  "portfolio_heat": an.portfolio_heat(),
                  # Y1 DOĞRULAMA ÜÇLÜSÜ (Hafta 3a): DSR (deneme-sayısı düzeltmeli Sharpe) + PBO/CSCV
                  # + sorgu sayacı yan yana. ÜÇÜ DE ADVISORY — kapı passes semantiği DEĞİŞMEDİ.
                  # `validation_ledger.jsonl`ın dış tüketicisi bu zincirdir (YASA 6): validation.py
                  # yazar → analytics.validation_trio okur → bu uç servis eder → pano gösterir.
                  "validation_trio": _trio_v,
                  # HAFTALIK KANIT RAPORUNUN ÖZETİ (temizlik turu 2026-07-30). `validation_report`
                  # modülü "hangi mekanizma/edge KANITLANIYOR?" tablosunu 2026-07-21'den beri
                  # üretebiliyordu ve TEK çağıranı kendi `__main__` bloğuydu — yani rapor ancak
                  # biri elle koşturursa vardı. Artık haftalık kadans üretiyor (scheduler), bu uç
                  # okuyor: YASA 6 zinciri tam (yazan scheduler → okuyan api → pano).
                  # ÖZET SERVİS EDİLİR, TAM METİN DEĞİL: `metin` alanı ~30 satırlık insan-okur bir
                  # rapordur ve her pano isteğinde taşınması saf yüktür; dosya state'te duruyor.
                  # `validation_trio` ile KARIŞTIRILMAMALI — o DSR/PBO kilitleridir, bu edge tablosu.
                  "validation_report": ({k: _vrep.get(k) for k in
                                         ("uretildi", "hafta", "evidence_base", "base_edge",
                                          "cf_fidelity")} if _vrep else None),
                  # MEASURED_V3 KAYMA BEKÇİSİNİN SON ÖLÇÜMÜ (temizlik turu 2026-07-30): yasa
                  # sabitlerinin (MONEY_GATE_MARGIN, DD_VETO_MARGIN) türetim tabanı hâlâ yerinde mi.
                  # `kayma` BOŞ LİSTE = sınandı ve geçti; None = bu süreçte/haftada HİÇ ölçülmedi.
                  "shadowlaw_drift": sched.get("shadowlaw_drift"),
                  # ---- FAZ-6 KİLİT ZİNCİRİ (v130): BEŞ KİLİT, TEK YERDE ADLANDIRILMIŞ ----------
                  # ROADMAP §3.5'in "dört kilit" cümlesi bugüne kadar hiçbir yerde makine okunur
                  # değildi — yani denetçisi yoktu. Beşinci kilit (yürürlükteki pencerede DSR > 0.95
                  # ölçülü ve geçer) bu turda eklendi ve zincir `health.faz6_kilitleri`de yazılı.
                  # SAF OKUMA: hiçbir şey silahlamaz. Eşik ship yoluyla AYNI sabitten gelir.
                  "faz6_kilitleri": health.faz6_kilitleri(edge=_edge_v, sonuc=_sonuc_v,
                                                          trio=_trio_v),
                  # BÜYÜKLÜK YASASI SATIRI — **TERS GÖLGELEME** (PARA-v3, 2026-07-30). DİKKAT: bu
                  # alanın anlamı 3b'ye göre TERSİNE döndü ve adı (`shadow_law`) tarihsel sebeple
                  # KORUNDU (tüketicisi app.js'te `ml.shadow_law`; anahtar yeniden adlandırılsa
                  # pano sessizce boş çizerdi). 3b'de "v2 OLSAYDI" alanıydı: karar eski bileşik
                  # skordaydı, v2 kayda geçiyordu. ARTIK: karar PARA-v3'te, ESKİ bileşik yasa kayda
                  # geçiyor. Satır DÖRT şeyi birlikte söyler: (a) yürürlükteki yasa PARA-v3'tür ve
                  # `passes`i O üretir (`law_transition: True`); (b) PARA'nın varyans payı %0,3 →
                  # %100; (c) skordan çıkan düşüş/Sharpe bacaklarının NEREYE gittiği (sert vetolar —
                  # yoksa "korumayı kaldırdılar" diye okunur); (d) eski yasanın son hükmü + ıraksama
                  # sayacı. Geçiş YAPILDI; operatör kararı ALINDI (2026-07-30 "1 numaradan başla").
                  "shadow_law": an.shadow_law_row(),
                  # MAE KARNESİ (K1 devri, 3b): `exit_efficiency`in ikizi — MFE çıkış kuralını,
                  # MAE STOP kuralını yargılar. `mae_r` 95 satırın hepsinde vardı ve tüketicisi
                  # YOKTU (YASA 6): stop mesafesinin karnesi hiç ölçülmüyordu.
                  "mae_profile": store.read_json("mae_profile.json", None),
                  # 2.4 GÖLGE-VARYANT ÖZET KARTI (3b devri): sadeleştirme turu bu defteri
                  # `codelaw.DECLARED_SINKS`e SÜRELİ beyanla koymuştu ("pano/api tüketicisi 3b'ye
                  # devredildi"). Devir BURADA tamamlandı ve o beyan satırı KALDIRILDI — varyant
                  # başına son karar + kümülatif ayrışma sayısı panoya çıkar.
                  "shadow_variants": an.shadow_variant_summary(),
                  # HERMES KARNESİ (H1+H2+H3): beynin KENDİ tahmin isabeti + ölü aileleri + hiç
                  # denenmemiş düğmeleri + bileşik kuyruk durumu. Aynı sözlük evidence_pack yoluyla
                  # PROMPT'a da giriyor — pano ve beyin AYNI karneyi görür (iki gerçek olmasın).
                  "hermes_scorecard": an.hermes_scorecard(),
                  # NOUS SİSTEM ÖNERİLERİ (Katman B/C/D, ROADMAP §3.2): beynin MEKANİZMA düzeyindeki
                  # haftalık önerileri + KALİTE KAPISI istatistiği (kaç öneri kanıt-atıfsız düştü).
                  # Düşme sayısı kartta GÖRÜNÜR: kapı sessiz çalışırsa "4 öneri üretti" ile "9
                  # üretti, 5'i düştü" aynı görünür ve ikincisi beynin karnesi hakkında çok daha
                  # fazla şey söyler. TELEMETRİ PAKETİ BURADA SERVİS EDİLMEZ: `system_telemetry`
                  # 12 üreticiyi (bootstrap CI'lar dahil) çağırır ve her pano isteğinde yeniden
                  # hesaplanması saf bir maliyet olurdu — paketin tüketicisi prompt ve `--ozet`.
                  "improvement_proposals": an.improvement_proposals_status(),
                  # NOUS ÖNERİ FİŞLERİ (v192, otomatik yönlendirme borusu). DOSYA ADI LİTERAL
                  # yazılır ve okuma DIŞ modülde (burada) yapılır — `codelaw.artifact_graph`
                  # "kendi yazdığını kendi okuyan tüketici değildir" der; `nous_eval` içinden
                  # okunsaydı defter `artifact_unread` olarak görünürdü (aynı gerekçe:
                  # analytics.improvement_proposals_status).
                  # NİYE AYRI DEFTER: `improvement_proposals.jsonl` KABUL EDİLENLERİN kaydıdır ve
                  # sözleşmesi "akıbet alanı YOKTUR" der (akıbet zamanla değişir, damga yalan
                  # söyler). Fiş ise operatörün İŞ KALEMİdir; durumu zamanla değişir ve kendi
                  # defterinde yaşamak zorundadır.
                  "nous_fisler": _nous_fisler(),
                  # Y3 REJİM/RİSK DÖRTLÜSÜ (3b): dördü de DEFAULT-OFF. VIX bacağı ayrıca `veri_yok`
                  # (Massive 403 / FMP boş — doğrulandı 2026-07-30) ve knob açılsa bile karar üretmez.
                  "y3_entry_gates": _y3_gate_row(),
                  # H5 OTOMATİK GÖLGE DUYURUSU (3b): otonom bir karar SESSİZ KALMAZ. Dosya adı
                  # literal (statik graf sabitten türetilmiş adı çözemez → artefakt "okuyucusu yok"
                  # görünürdü). PROTECTED beşlisi ASLA bu listede olamaz.
                  "skill_auto_shadow": store.read_json("skill_auto_shadow.json", None),
                  # 2C EMPİRİK BAYES KÜÇÜLTME (3b): küçük hücrenin ekstrem değeri büyük ölçüde
                  # GÜRÜLTÜDÜR ve "en kötü rejim" seçimi tam onu seçer. Panoda "küçültülmüş"
                  # ETİKETİYLE gösterilir; verdict TABANLARINA GİRMEZ (küçültme n'i büyütmez).
                  "shrunk_regime_cells": an.shrunk_regime_cells(),
                  "shrunk_component_ic": an.shrunk_component_ic(),
                  # 2D HOLDOUT ROTASYON ÖNERİSİ (3b): aşınma eşiği aşıldığında ÖNERİ üretir,
                  # UYGULAMAZ — pencere değişimi geçmiş kapı kayıtlarının karşılaştırılabilirliğini
                  # keser ve operatör kararıdır.
                  "holdout_rotation": an.holdout_rotation_advice(),
                  # BİLEŞEN IC TABLOSU (Aşama 1.2, 2026-07-28): "skorun IC'si sıfır" ile "skorun
                  # hiçbir parçası bilgi taşımıyor" aynı cümle değildir. Dört bileşenin ayrı IC'si
                  # ancak burada dışarı verilirse pano ve operatör onu görebilir (YASA 6 — üreten
                  # modülün kendi dosyasını okuması tüketici saymaz).
                  # Dosya adı LİTERAL yazılır (sabitten türetilmez): `codelaw.artifact_graph` statik
                  # bir graftır ve değişkenden gelen adı ÇÖZEMEZ — artefakt o zaman "okuyucusu yok"
                  # diye görünmez olur, YASA 6 denetimi de onu hiç göremez.
                  "component_ic": store.read_json("component_ic.json", None),
                  # MIN_SCORE EŞİK EĞRİSİ (Aşama 1.3, 2026-07-29): "kapıyı yükseltsek kâr artar mı?"
                  # sorusunun tek ölçüm yüzeyi. Dilim istatistiği ile tam replay 07-28'de ÇELİŞTİ
                  # (H2: 60→80 replay'de Δ-0.095); eğri o çelişkiyi panoda görünür tutar.
                  "threshold_curve": store.read_json("threshold_curve.json", None),
                  # KÂR ŞELALESİ (S1A, 2026-07-29): "edge var mı?" ile "para var mı?" ayrı sorular.
                  # Sinyalin sunduğu (MFE) → çıkışın geri verdiği → friksiyon → net ayrıştırması,
                  # exit_reason kırılımıyla. Saf hesap (dosya yok) — bu yüzden fonksiyon çağrısı.
                  "profit_waterfall": an.profit_waterfall(),
                  # OOS AŞINMASI (Aşama 2.2, 2026-07-28): kapı hükümlerinin ne kadar yıprandığı,
                  # kapı kaydının içine gömülü kalırsa yalnız o hipoteze bakan görür. Aşınma
                  # PENCERENİN durumudur, tek bir hipotezin değil — dış tüketicisi pano (YASA 6).
                  "oos_erosion": __import__("meridian.oos_erosion", fromlist=["report"]).report(),
                  "agent_skills": __import__("meridian.hermes", fromlist=["agent_skill_coverage"]).agent_skill_coverage(),
                  "agent_calls": {**{k: v for k, v in store.read_json("agent_budget.json", {}).items()
                                     if k in ("date", "day")},
                                  "rpm_limit": __import__("meridian.hermes", fromlist=["AGENT_RPM"]).AGENT_RPM,
                                  "rpd_limit": __import__("meridian.hermes", fromlist=["AGENT_RPD"]).AGENT_RPD},
                  "warmup": {"last": hstat.get("last_warmup"), "ucb_top": ucb_top,
                             "ticks": warm_ticks % _wep, "every": _wep,
                             "skip": hstat.get("_warm_skip"), "polled": bool(hstat.get("last_poll")),
                             "horizon_ready": hstat.get("horizon_ready")}},
        # `alarm_gunluk` v192'de EKLENDİ: bekçi raporu "şu an ne bayat" der, günlük sayaç "bugün kaç
        # alarm yazıldı, kaçı tavana takıldı, kaçı askıdaydı" der. İkincisi olmadan alarm hijyeni
        # ölçülemez — ve ölçülmeyen bir susturma, susturmanın kendisinden daha tehlikelidir.
        "watchdog": {**_wd_rep, "alarm_gunluk": _alarm_gunluk()},
        # CANLI ZAMAN ÇİZELGESİ (D3-UI · C1-4) — BEKÇİNİN YANINDA, İÇİNDE DEĞİL. Bekçi raporu
        # "geciken var mı?" der; çizelge "adım adım NE ZAMAN koştu?" der. İkisi aynı dosyadan
        # (mechanism_beats.json) beslenir ama farklı soruların cevabıdır; `watchdog` içine
        # gömmek, gecikme raporunu bir zaman serisiyle şişirmek olurdu.
        # D2-b'NİN BEYANLI BORCU BURADA KAPANIYOR: "adım başına damga … panoya açılmamış.
        # Damgaların uca açılması D3-UI'ın işi" (app.js `RENDER.cizelge` başlığı).
        "cizelge": _hat_cizelgesi(_wd_rep, sched),
        # SESSİZ HAT (WP-P/P1) — bekçi + kilit + tazelik TEK Level-1 toplaması. `_wd_rep` AYNI
        # NESNEDİR: bekçi raporunu ikinci kez çağırmak, aynı yanıtta "bekçi 17/17" ile
        # "sessiz hat 16/17" gibi iki farklı gerçek doğurabilirdi (iki ayrı okuma anı).
        "sessiz_hat": _sessiz_hat(_wd_rep, hb),
        # ALARM BÜTÇESİ (WP-P/P2) — EEMUA 191 merceğiyle son 24 sa. `_age` DIŞARI VERİLİR:
        # önbellekli bir sayıyı taze gibi göstermek bu deponun kovaladığı kusur sınıfıdır.
        "alarm_butcesi": {**_alarm_rep, "yas_s": _alarm_age},
        "hotstate": hot,          # Redis sıcak katman (intraday) — down GÖRÜNÜR olmalı, sessiz değil
        "marketstream": __import__("meridian.marketstream", fromlist=["health"]).health(),   # Faz 2 data akışı; ok:None/down görünür
        "barfeed": __import__("meridian.barfeed", fromlist=["health"]).health(),             # Faz 3 dayanıklı bar-tetiği (consumer-group)
        "intraday": _intra,          # Faz 4 gözlem-modu + intraday_decisions.jsonl özeti (dış okuma)
        # WP-K TREND KOLU GÖLGE-KİTABI (2026-07-31) — EDG-2026-009 incumbent kolunun CANLI sanal
        # defteri. DIŞ OKUYUCU BURASIDIR (YASA 6): defteri `trend_shadow` yazar, `intraday_shadow`
        # ile AYNI desen — dosya adı LİTERAL okunur ki `codelaw.artifact_graph` tüketiciyi görsün;
        # okuma modülün kendi içinde kalsaydı artefakt "yazılıyor ama kimse okumuyor" görünürdü.
        # `pit_serh` özetin İÇİNDE taşınır ve panoya rakamla BİRLİKTE çıkar: +13,1p/yıl'ı şerhsiz
        # okutmamak bu kolun hükmünün parçasıdır (yanlılık-düşülmüş ~6-7p/yıl).
        "trend_kitabi": __import__("meridian.trend_shadow", fromlist=["ozet"]).ozet(
            store.read_json("trend_book.json", None)),

        # BÜTÜNLÜK: "koşuyor mu" değil "üretiyor mu / kaybetmiyor mu / deterministik mi" (2026-07-21)
        # ÖNBELLEKLİ OKUMA (2026-07-28): `integrity_report_cached` yalnız BURASI için var; yan
        # etkili `persist=True` yolunu (taban ilerlemesi, mutasyon kararı) hiç kullanmaz.
        # `integrity_age_s` dışarı verilir: pano raporun kaç saniye önce hesaplandığını söyler,
        # taze gibi göstermez. 0.0 = bu istekte hesaplandı.
        "integrity": _integrity_rep,
        "integrity_age_s": _integrity_age,
        "coverage": __import__("meridian.integrity_registry", fromlist=["coverage_report"]).coverage_report(),
        # evren sapması: elle bakımlı 250'lik listede endeksten düşmüş isim var mı (denetim turu 3)
        "universe_drift": store.read_json("universe_drift.json", None),
        "pipeline": {"cf_fidelity": store.read_json("cf_fidelity.json", None),
                     "refetch_attempts": sched.get("refetch_attempts", 0), "refetch_max": 8,
                     "last_refetch_session": sched.get("last_refetch_session"),
                     "earnings_attempts": sched.get("earnings_attempts", 0),
                     "quarantine": dq.get("tickers_failed") or [],
                     # KAYNAK DİKİŞİ: uyarı susturuldu ama DURUM görünür kalmalı — kaç sembolün
                     # geçmişi artık yayın yapmayan bir kaynağa sabitli? (2026-07-22)
                     "bar_source_seams": __import__("meridian.adapters.data",
                                                    fromlist=["seam_report"]).seam_report(),
                     # VERİ DÖNMEYEN SEMBOLLER: "kaynak hatası" ile "sembol yok" AYRI şeylerdir —
                     # ilki geçici (429), ikincisi evren bakımı gerektirir. 18 sağlıklı sembol
                     # yalnız throttling yüzünden "ölü" sanılabilirdi (2026-07-22).
                     "symbol_no_data": __import__("meridian.adapters.data",
                                                  fromlist=["no_data_report"]).no_data_report(),
                     "crosscheck": store.read_json("index_crosscheck.json", {}),
                     # MASSIVE ÇAPRAZ-KONTROL — BEYAN EDİLEN OKUYUCU NİHAYET ÇAĞRILIYOR (K1,
                     # 2026-07-30). `codelaw.DECLARED_SINKS` massive_crosscheck.json'u
                     # "adapters.data.crosscheck_report() okur" diye AKLIYORDU; yasa okuyucunun
                     # VAR olduğuna bakar, ÇAĞRILDIĞINA bakamaz — ve üretimde tek çağıran yoktu
                     # (yalnız testler). Yani beyan, artifact_unread alarmını susturdu ama zinciri
                     # bağlamadı: learning_loop_open emsalinin birebir tekrarı. Kardeşi seam_report
                     # yukarıda AYNI blokta bağlı; bu satır o deseni tamamlıyor.
                     # DİKKAT: yukarıdaki "crosscheck" anahtarı FARKLI bir dosyadır
                     # (index_crosscheck.json — endeks düzeyi); bu ise sembol düzeyi Massive-vs-zincir
                     # hakemliği. İki ayrı gerçek, iki ayrı anahtar.
                     "massive_crosscheck": __import__("meridian.adapters.data",
                                                      fromlist=["crosscheck_report"]).crosscheck_report(),
                     # YASA 6 (2026-07-21): fmp_usage.json her istekte YAZILIYOR ama `fmp.usage()`
                     # erişimcisini kod içinde kimse çağırmıyordu — kota telemetrisi diskte birikip
                     # görünmez kalıyordu. 429 kesintileri tam bu sayıdan okunur.
                     "fmp_usage": __import__("meridian.adapters.fmp", fromlist=["usage"]).usage(),
                     # FINVIZ — /api/hermes'ten TAŞINDI (K1, 2026-07-30): evren keşif kaynağının
                     # sağlığı hermes yükünde servis ediliyordu ve hiçbir yüzeyi yoktu (app.js'teki
                     # finviz geçişleri /api/market src.finviz_extra ve sırlar ekranıydı). Kaynak
                     # sağlığı pipeline kartına aittir — seam_report/no_data_report'un yanına.
                     # Token son-4 maskeli döner (sır sızdırmaz).
                     "finviz": __import__("meridian.adapters.finviz", fromlist=["status"]).status(),
                     "io": store.io_stats()},
        "ledgers": {"cf_open": len(store.read_json("cf_open.json", [])), "cf_cap": 2500,
                    "cf_resolved": len(store.read_jsonl("counterfactuals.jsonl")),
                    "trades": len(store.read_jsonl("trades.jsonl"))},
        # DEFTER SÖZLEŞMESİ (2026-07-21): sayaç "defter dolu mu" der, sözleşme "içindekiler söz
        # verdiği alanları taşıyor mu" der. Bugünün altı hatasının kökü ikincisiydi.
        "ledger_contract": __import__("meridian.ledgers", fromlist=["report"]).report(),
        # ELEME MUHASEBESİ: "veri yok" ile "veri elendi" ayrı şeylerdir. Hangi satırın NEDEN
        # düştüğü sayılmazsa, sessiz eleme ekranda "henüz kanıt birikmedi" gibi okunur.
        "sieve": _sieve_rep})                 # tek okuma anı (v192) — yukarıda hesaplandı


# ---------- Hermes (the reflection brain) ----------
@app.get("/api/hermes")
def api_hermes(request: Request):
    """Hermes status + spend + last proposals for the dashboard's Hermes section."""
    _auth(request)
    from . import hermes_runtime, spend, skills, scheduler, sprint
    hyps = memory.all_hypotheses()
    from . import hermes as _hm
    return {"status": hermes_runtime.status(), "spend": spend.summary(),
            # GECE MALİYET/TOKEN KARNESİ (D3-UI · C1-3). `spend.summary()` aylık TOPLAMI verir;
            # "hangi kol yedi, hangi model yedi, hangi gece?" sorusu çağrı-başına kırılım ister ve
            # o kırılım `spend.jsonl`de ZATEN yazılı, hiçbir uçtan servis edilmiyordu.
            # NEDEN /api/spend'E BAĞLANMADI: o uç K1'de EMEKLİ ("bu uçlara YENİ tüketici bağlanmaz
            # — kanonik yüzey /api/hermes `spend`"). Kırılım o yüzden kanonik ucun İÇİNDE doğar.
            "spend_detay": _spend_detay(),
            "autostart": os.environ.get("MERIDIAN_AUTOSTART_HERMES") == "1",
            "recent": list(reversed(hyps))[:8],
            "skill_recommendations": skills.pending_recommendations(),   # Axis-2 (operator applies)
            "skill_count": len(skills.catalog()),
            "learning": analytics.learning_scorecard(),                  # honest "is it learning?" scorecard
            "scheduler": __import__("meridian.scheduler", fromlist=["status"]).status(),
            "sprint": sprint.status(),                                   # öğrenme antrenmanı (sandbox loop-closer)
            "integrations": _hm.integrations_status(),                   # MCP/hook/cache/pool + görüş dolgusu
            # ---- BEŞ ÖLÜ SAĞLIK BLOĞU EMEKLİ EDİLDİ (K1, 2026-07-30) ------------------------
            # Buradan beş blok servis ediliyordu: finviz, hotstate, marketstream, barfeed,
            # intraday. RENDER.hermes (app.js) hiçbirini okumuyordu — hotstate/marketstream/
            # barfeed/intraday panelleri verilerini /api/diagnostics'ten alıyor. Yani AYNI gerçek
            # iki uçtan servis ediliyor, biri hiç okunmuyordu; bu, api.py'nin KENDİ kuralının
            # ("iki uç aynı alanı farklı şekilde servis edemez") ihlaliydi ve her Hermes sayfası
            # açılışında dört gereksiz health() çağrısı koşuyordu.
            #
            # TEK KAYNAK: /api/diagnostics — "hotstate"/"marketstream"/"barfeed"/"intraday"
            # anahtarları orada duruyor ve pano onları ORADAN okuyor. Geri almak gerekirse dört
            # satır o bloktan birebir kopyalanabilir; davranış hiçbir yerde kaybolmadı.
            #
            # `finviz` SİLİNMEDİ, BAĞLANDI: onun tek farkı vardı — hiçbir yüzeyi YOKTU (ne hermes
            # ne diagnostics çiziyordu). Evren keşif kaynağının sağlığı görünmeye değer, o yüzden
            # /api/diagnostics'in `pipeline` bloğuna taşındı (aşağıda, seam_report'un yanına).
            "note": "Hermes bir fikir üretir; kabul/ret kararını backtest kapısı verir. L0'da kağıt."}


@app.post("/api/hermes/reflect")
def api_hermes_reflect(request: Request):
    """Operator-triggered single reflection cycle (a few seconds — runs the walk-forward gate)."""
    _auth(request)
    from . import hermes_runtime
    out = hermes_runtime.reflect_now()
    _diag_onbellek_bosalt("hermes_reflect")
    return out


@app.post("/api/hermes/pool_key")
async def api_hermes_pool_key(request: Request):
    """Kimlik havuzuna yedek anahtar ekle (429 rotasyonu). Gövdede {provider, key}; anahtar loglanmaz,
    yalnızca hermes auth add'e verilir. Prohibited-action DEĞİL: operatörün KENDİ isteğiyle, kendi
    anahtarını kendi ajanına ekliyor (kimlik oluşturma/kimlik doğrulama yok)."""
    _auth(request)
    body = await request.json()
    from . import hermes
    res = hermes.register_pool_key(str(body.get("provider", "")), str(body.get("key", "")),
                                   label=str(body.get("label", "meridian")))
    obs.log("pool_key_request", provider=str(body.get("provider", ""))[:20], ok=res.get("ok"))
    return res


@app.post("/api/hermes/{action}")
def api_hermes_control(action: str, request: Request):
    _auth(request)
    from . import hermes_runtime, hermes
    if action == "start":
        out = hermes_runtime.start(poll_seconds=int(os.environ.get("HERMES_POLL_SECONDS", "300")))
        _diag_onbellek_bosalt("hermes_start")
        return out
    if action == "stop":
        out = hermes_runtime.stop()
        _diag_onbellek_bosalt("hermes_stop")
        return out
    if action == "backfill":                       # çevrimdışı görüş dolgusu (kalibrasyon hızlandırma)
        # DÜĞME KALIR ama artık ELLE HIZLANDIRMADIR, tek tetik DEĞİL: varsayılan akış zamanlayıcının
        # seans-sonrası öğrenme kadansıdır (scheduler._learning_cadence). Tavan da sabit 40 değil —
        # `backfill_budget()` kalan ajan kotasından türetir ve env override edilmişse ona dokunmaz.
        # Bu uçtan `max_days` VERİLMEZ: iki yerde iki tavan, formül değiştiği gün sessizce ayrışırdı.
        bt = hermes.backfill_budget()
        hermes.backfill_opinions_async()
        if bt["tavan"] > 0:                        # bütçe kıstıysa dolgu KOŞMADI — zarf da düşmez
            _diag_onbellek_bosalt("hermes_backfill")
        return {"started": bt["tavan"] > 0, "butce": bt,
                "kuyruk": hermes.backfill_queue(),
                "detail": ("görüş dolgusu arka planda başladı" if bt["tavan"] > 0
                           else f"bütçe kıstı — dolgu koşmadı ({bt['formul']})")}
    if action == "sync_integrations":              # MCP/hook/cache/pool config'i elle tazele
        out = hermes.config_ensure_integrations()
        _diag_onbellek_bosalt("hermes_sync_integrations")
        return out
    raise HTTPException(status_code=400, detail="unknown action")


# ---------- paper-advance scheduler (keeps the local agent from freezing) ----------
# K1-EMEKLİ: kanonik yüzey /api/hermes `scheduler`. Yeni tüketici bağlanmaz.
@app.get("/api/scheduler")
def api_scheduler(request: Request):
    _auth(request)
    from . import scheduler
    return scheduler.status()


@app.post("/api/scheduler/advance")
def api_scheduler_advance(request: Request):
    """Run one daily cycle now (advance to the latest closed session). Operator-triggered catch-up."""
    _auth(request)
    from . import scheduler
    out = scheduler.advance_once()
    # İZ (2026-07-21 N/A sorgusu): operatörün elle ilerlettiği bir seans, defterde otomatik olandan
    # ayırt edilebilmeli — yoksa "bu gün neden iki kez işlendi" sorusu cevapsız kalır.
    obs.log("scheduler_advance_manual", result=str(out)[:200])
    _diag_onbellek_bosalt("scheduler_advance")     # bir döngü koştu: teşhis yükünün NEREDEYSE HEPSİ değişti
    return out


# ---------- learning sprint (öğrenme antrenmanı) — sandboxed loop-closer ----------
# K1-EMEKLİ: kanonik yüzey /api/hermes `sprint`. Yeni tüketici bağlanmaz.
@app.get("/api/sprint")
def api_sprint(request: Request):
    _auth(request)
    from . import sprint
    return sprint.status()


@app.post("/api/sprint/start")
async def api_sprint_start(request: Request):
    """Launch a sandboxed learning sprint (a subprocess; live book untouched). Body: {budget?, k_max?}."""
    _auth(request)
    from . import sprint
    try:
        body = await request.json()
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        body = {}
    out = sprint.start(body if isinstance(body, dict) else {})
    # `sprint.py`ye DOKUNULMADI (ayrık oturum): burada yalnız uç, kendi zarfını düşürür.
    if isinstance(out, dict) and out.get("ok") is not False and not out.get("error"):
        _diag_onbellek_bosalt("sprint_start")
    return out


@app.post("/api/sprint/stop")
def api_sprint_stop(request: Request):
    _auth(request)
    from . import sprint
    out = sprint.stop()
    _diag_onbellek_bosalt("sprint_stop")
    return out


# ---------- Alpaca PAPER execution mirror (opt-in, paper-only) ----------
@app.get("/api/alpaca")
def api_alpaca(request: Request):
    """The Alpaca PAPER account the agent mirrors to: equity, positions, open orders. Read-only."""
    _auth(request)
    from .adapters import alpaca
    return {"backend": config.BROKER, "paper_available": alpaca.paper_available(),
            "account": alpaca.dashboard_view() if alpaca.paper_available() else None,
            # Phase-1 reconciliation telemetry MUST reach the operator: drift alarms that only live in a
            # state file are invisible exactly when they matter (dashboard live-data audit).
            # `failed_submissions` BURADA DA açık/kapatılmış olarak ayrışır: bu uç ile
            # /api/diagnostics aynı alanı farklı şekillerde servis ederse pano hangi uçtan
            # okuduğuna göre farklı bir gerçek görür — tek yanıtta iki gerçek olamaz kuralının
            # uçlar arası hâli (2026-07-27).
            "reconcile": {**(_rcraw := store.read_json("broker_reconcile.json", {}) or {}),
                          "failed_submissions": health.split_rejections(_rcraw.get("failed_submissions"))},
            # `stream_ok` HAM hâliyle gitmez: dürüst değeri yanına ikinci bir anahtar olarak eklemek
            # yalanı birincil bırakırdı — `stream.stream_ok` okuyan pano donmuş `true`yu görmeye
            # devam ederdi. Anahtar aynı kaldı, ARKASINDAKİ DEĞER dürüstleşti.
            "stream": _stream_view(),
            "note": "Öğrenme/backtest her zaman içsel simülatörde; bu, canlı kararların Alpaca PAPER aynası."}


@app.post("/api/alpaca/submit_armed")
def api_alpaca_submit_armed(request: Request):
    """Submit the currently-armed plans to Alpaca paper now (manual trigger; the scheduler also does this
    each cycle when MERIDIAN_BROKER=alpaca_paper). Refuses when halted.

    E1 YASASI ARTIK TEK KAPIDAN (C8, denetim 2026-08-02): bu uç EskİDEN kendi gönderim mantığını
    kuruyordu — `alpaca.submit_plan(p, eq)` çıplak varsayılanlarıyla. Yani de-risk çarpanı YOK
    (%5 düşüşte döngü 0,6 ile doldururken düğme TAM boyut gönderiyordu), atr/ref_price YOK (aynı
    planda iki farklı limit tavanı + gap dalında kırılım teyidinin tümden kalkması), dedup YOK
    (`alpaca_submitted` ne okunuyor ne yazılıyordu → döngü aynı planı ikinci kez gönderip
    duplicate-coid reddi alınca planı SİLAHLI kümeden düşürüyordu), E2 satırı YOK, ve hesap
    okunamazken 100k sabitine düşüp hayali sermaye üzerinden boyutlandırma VARDI. Artık uç,
    döngünün kullandığı `loop.mirror_submit_armed` fonksiyonunu çağırır — ikinci bir emir yolu
    kalmadı.

    KALICILIK: fonksiyon `meta`yı yerinde değiştirir; burada portfolio.json'a TAM BELGE yazımı
    YASAK (canlı worker'ın o an güncellediği armed setini ezerdi). Yalnız iki alan KİLİT ALTINDA
    yamalanır: gönderilen kimlikler dedup kümesine EKLENİR, düşen (veto/ret) planlar armed'dan
    kimlikle ÇIKARILIR."""
    _auth(request)
    from . import loop as _loop
    if health.halted():
        return {"ok": False, "detail": "HALT aktif — emir gönderilmez"}
    meta = store.read_json("portfolio.json", {}) or {}
    # BOŞ TARİH YASAK: E2 penceresi `date >= cutoff` ile süzüyor — boş dize her pencereden SESSİZCE
    # düşerdi, yani düğmeden geçen gönderim slipaj özetinde hiç görünmezdi. Nabızda işlenmiş bar
    # yoksa gönderimin GERÇEK günü yazılır (uydurma değil: satırın tarihi eylemin tarihidir).
    import datetime as _dt
    dstr = str(meta.get("last_date") or _dt.date.today().isoformat())
    res = _loop.mirror_submit_armed(meta, dstr, source="pano")
    gonderilen, dusen = set(res.get("submitted_ids") or []), set(res.get("dropped_ids") or [])
    if gonderilen or dusen:
        def _yama(doc):
            if not isinstance(doc, dict):
                return False
            doc["alpaca_submitted"] = list(dict.fromkeys(
                list(doc.get("alpaca_submitted") or []) + sorted(gonderilen)))[-200:]
            doc["armed"] = [p for p in (doc.get("armed") or []) if p.get("id") not in dusen]
            doc["broker_rejected"] = meta.get("broker_rejected", doc.get("broker_rejected", []))
            return True
        store.update_json("portfolio.json", _yama, {})
    obs.log("alpaca_submit_armed_endpoint", ok=res.get("ok"), submitted=res.get("submitted"),
            dropped=len(dusen), detail=str(res.get("detail", ""))[:160])
    # HALT dalı YUKARIDA döndü (zarf düşmez). Burada da yalnız defter GERÇEKTEN kıpırdadıysa
    # düşürülür: gönderilen ya da düşen bir plan yoksa mutabakat yükü aynı kalır.
    if gonderilen or dusen:
        _diag_onbellek_bosalt("alpaca_submit_armed")
    return {"ok": bool(res.get("ok")), "submitted": res.get("submitted", 0),
            "results": res.get("results", []), "equity": res.get("equity"),
            "detail": res.get("detail", "")}


@app.post("/api/alpaca/close_all")
def api_alpaca_close_all(request: Request, confirm: str = ""):
    """Cancel orders + flatten all Alpaca PAPER positions — operator panic control for the mirror.
    SAHİPLİK (denetim 2026-07-21): bu hesapta operatörün KENDİ pozisyonları da var (bugün NVDA).
    Onay jetonu olmadan çağrı yalnız NEYİ düzleştireceğini raporlar (kuru koşu) — motorun sahibi
    olmadığı varlığa dokunması ancak insanın açık onayıyla olur."""
    _auth(request)
    from .adapters import alpaca
    res = alpaca.close_all(confirm=confirm)
    obs.log("alpaca_close_all", ok=res.get("ok"), dry_run=res.get("dry_run", False),
            foreign=len(res.get("foreign", [])))
    # KURU KOŞU DEĞİL: onay jetonu yoksa bu uç yalnız NE YAPACAĞINI raporlar, hiçbir şeye dokunmaz.
    if res.get("ok") and not res.get("dry_run", False):
        _diag_onbellek_bosalt("alpaca_close_all")
    return res


# ==================================================================================================
# KORUMAYI YENİDEN KURAN YOL (v211) — ÖNERİ ÜRETİCİ + ONAY KAPISI + İCRA
# --------------------------------------------------------------------------------------------------
# EKSİK MEKANİZMA (canlı A1, 2026-08-07): panoda üç uç vardı — `/api/alpaca` (oku),
# `submit_armed` (gir), `close_all` (düzleştir). "Korumayı yeniden kur" YOKTU. `watchdog
# .koruma_report()` (v209) çıplak motor pozisyonlarını GÖRÜYOR ama bekçi haber verir, düzeltmez;
# aradaki boşluğu tek dolduran şey operatörün elle Alpaca arayüzüne gitmesiydi.
#
# YETKİ ŞEKLİ — OPERATÖR KARARI (2026-08-07): "emri SİSTEM gönderir, operatör PANODAN onaylar".
# O yüzden bu blok İKİYE bölünmüştür ve bölünme bir üslup tercihi değil, yetkinin kendisidir:
#   `koruma_onerileri()` — SALT OKUMA. Broker'a yalnız GET atar, hiçbir emir üretmez, çağrılması
#                          hiçbir yan etki bırakmaz. Pano bunu okur.
#   `koruma_kur()`       — İCRA. Yalnız operatörün taşıdığı onay jetonu VE o ölçüme ait öneri
#                          kimliğiyle çalışır. İkisinden biri eksikse HİÇBİR emir çıkmaz.
#
# ONAY NEDEN "TURA ÖZEL" (kalıcı bir anahtar/toggle DEĞİL): kalıcı bir izin bayrağı, ilk gün
# verilen onayı yarının bilinmeyen dünyasına uygular. Buradaki onay bir DURUMA bağlanır —
# `oneri_id`, o an ölçülmüş önerinin (sembol/adet/stop/hedef listesinin) özetidir. Operatör ne
# gördüyse onu onaylar; icra anında dünya değiştiyse (adet kaydı, koruma çoktan kuruldu, yeni bir
# çıplak pozisyon doğdu) özet DEĞİŞİR, eşleşme düşer ve emir GİTMEZ. Bayat bir onayla emir
# göndermek, onay almamaktan farksız olurdu.
#
# HALT BU YOLU KAPATMAZ — VE BU BİLİNÇLİ. `/api/alpaca/submit_armed` HALT'ta reddeder çünkü o YENİ
# RİSK ALIR. Bu yol var olan riski AZALTIR: çıplak bir pozisyona stop koymak, acil durdurma
# sırasında yapılacak şeyin ta kendisidir. Kademe-2 (`cancel_open_entries`) zaten aynı ayrımı
# yapıyor — dolu pozisyonların koruma bacaklarına DOKUNMUYOR.
KORUMA_KART_SEV = "sev-1"
# Emir listesi tavanı — `watchdog.KORUMA_EMIR_TAVANI` ile AYNI gerekçe (sahiplik kanıtı tavanın
# dışında kalabilir) ama İKİNCİ BİR OKUMA: bu modül bekçinin `rows`unu kullanır, bekçi ise emir
# FİYATLARINI döndürmez ve `watchdog.py` bu turda yazma kapsamı dışındadır (v209 dokunulmaz).
# A4 denetimi (mevcut stop'un ÜSTÜNE çıkma) fiyatsız yapılamaz, o yüzden emirler burada bir kez
# daha OKUNUR. Bedeli beyanlıdır: tur başına bir fazla GET; kazancı, korumayı düşürmenin arka
# kapısının kapalı kalması.
KORUMA_EMIR_TAVANI = 500


def _koruma_sayi(v):
    """Sayıya çevir; çevrilemeyen değer None (0 DEĞİL). Bir stop seviyesi "okunamadı" ile "sıfır"
    aynı şey değildir: sıfır bir stop, hiç stop olmamasıdır."""
    try:
        f = float(v)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; None dönmek ÖLÇÜLEMEDİ dalıdır ve satırın `neden`inde görünür — uydurma bir seviye üretilmez
        return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


def _koruma_canli_stop_seviyeleri(ords: list) -> dict:
    """Sembol → broker'da CANLI duran koruyucu stop'ların EN YÜKSEĞİ (A4'ün tabanı).

    `watchdog._koruma_duz` ile aynı düzleştirme yapılır (bracket bacakları `legs` altındadır) ama
    o özel ada dokunulmaz — bekçi modülü bu turda salt okunur ve özel bir yardımcıya bağlanmak,
    v209'un iç düzenini bu dosyanın sözleşmesi hâline getirirdi.

    EN YÜKSEĞİ alınır çünkü soru "bu pozisyonun bugünkü koruma seviyesi ne?"dir; iki canlı stop
    varsa etkin koruma yüksekte olandır ve yeni öneri ONUN üstüne çıkmak zorundadır."""
    from .adapters import alpaca
    canli = set(alpaca._LIVE_ORDER_STATES)
    out: dict = {}
    duz = []
    for o in (ords or []):
        if not isinstance(o, dict):
            continue
        duz.append(o)
        for leg in (o.get("legs") or []):
            if isinstance(leg, dict):
                duz.append(leg)
    for o in duz:
        if str(o.get("type", "")).lower() not in ("stop", "stop_limit", "trailing_stop"):
            continue
        if str(o.get("status", "")).lower() not in canli:
            continue
        sym = str(o.get("symbol") or "")
        sev = _koruma_sayi(o.get("stop_price"))
        if not sym or sev is None or sev <= 0:
            continue
        out[sym] = max(out.get(sym, 0.0), sev)
    return out


def koruma_onerileri() -> dict:
    """Çıplak MOTOR pozisyonları için OCO önerileri — SALT OKUMA, hiçbir emir göndermez.

    KAYNAKLAR ve her birinin NEDEN o kaynak olduğu:
      · çıplak listesi → `watchdog.koruma_report()` (v209). Yeniden yazılmaz: ikinci bir "koruma
        var mı?" tanımı, ilk düzenlemede bekçininkinden ayrışır ve pano ile alarm iki farklı
        gerçeği anlatmaya başlardı.
      · ADET → BROKER (`koruma_report` satırlarındaki `adet`, kaynağı `alpaca.positions()`).
        İÇ DEFTERDEN ASLA: canlı ölçüm defterin 33/43/64/54 dediği yerde broker'ın 22/22/37/25
        dediğini gösterdi. Defterin adediyle satış emri göndermek, ELDE OLMAYAN hisseyi satmaktır
        — yani `shorting_enabled` hesapta bir açık pozisyon açmak.
      · STOP/HEDEF → `state/portfolio.json`. Broker'da bu seviyelerin karşılığı YOK (bacaklar
        öldü); kitabın beyan ettiği seviye tek kayıttır. Kayıt yoksa satır ÖLÇÜLEMEDİ olur —
        uydurma bir stop, korumasızlıktan beterdir (yanlış yerde bir güven).
      · SON FİYAT → broker pozisyon satırının `current_price`ı (aynı okumadan gelir, ikinci bir
        fiyat kaynağı açılmaz).

    ÖLÇÜLEMEDİ ≠ 0: broker okunamazsa `ok=None`, `olculemedi=True`, `neden` dolu ve öneri listesi
    BOŞ döner. "0 öneri" ile "ölçemedim" aynı ekrana düşerse operatör sessiz bir arızayı temizlik
    sanır."""
    from . import watchdog
    from .adapters import alpaca
    rep = watchdog.koruma_report()
    out = {"ok": None, "olculemedi": True, "kapsam_disi": bool(rep.get("kapsam_disi")),
           "neden": rep.get("neden") or "", "sev": KORUMA_KART_SEV,
           "payda_beyani": rep.get("payda_beyani") or "", "korumasiz": rep.get("korumasiz"),
           "toplam": rep.get("toplam"), "satirlar": [], "motor_disi_satirlar": [],
           "gonderilebilir": None, "oneri_id": None,
           "onay_jetonu_gerekli": True,
           "adet_kaynagi": "BROKER (alpaca.positions) — iç defter YALNIZ görünürlük için gösterilir"}
    # İKİ AYRI GERÇEK, İKİ AYRI DAL — tek satırda `or`lanmaz. `kapsam_disi` bir YAPILANDIRMA hâli
    # (ayna kapalı, sorunun referansı yok), `ok is None` bir ARIZA hâli (broker okunamadı). İki
    # sözlük okumasını tek `or` ifadesinde birleştirmek, şema-takası tarayıcısının
    # (test_parity_v56) kovaladığı "iki ad tek alan" desenine BENZER — ve benzemek yetmez: o desen
    # bu depoda gerçek bir şema ayrışmasının izidir, ona benzeyen her satır elle tartışılır.
    # (Deseni bu yorumda ÖRNEKLEMEK bile tarayıcıyı tetikliyordu; ölçüldü ve cümleyle anlatıldı.)
    if rep.get("kapsam_disi"):
        return out
    if rep.get("ok") is None:
        return out
    ords = alpaca.orders(status="all", limit=KORUMA_EMIR_TAVANI, nested=True)
    if not alpaca.transport()["ok"]:
        return {**out, "neden": "emir listesi okunamadı (A4 denetimi fiyatsız yapılamaz): "
                                + (alpaca.transport().get("error") or "alpaca transport down")[:160]}
    mevcut = _koruma_canli_stop_seviyeleri(ords)
    # Broker pozisyon satırı — `current_price` yalnız burada var (koruma_report onu taşımaz).
    fiyat = {}
    for p in (alpaca.positions() or []):
        sym = str(p.get("symbol") or "")
        if sym:
            fiyat[sym] = _koruma_sayi(p.get("current_price"))
    if not alpaca.transport()["ok"]:
        return {**out, "neden": "pozisyon listesi okunamadı: "
                                + (alpaca.transport().get("error") or "alpaca transport down")[:160]}
    defter = (store.read_json("portfolio.json", {}) or {}).get("positions") or {}

    satirlar, disi = [], []
    for r in (rep.get("rows") or []):
        sym = str(r.get("ticker") or "")
        broker_adet = _koruma_sayi(r.get("adet")) or 0.0
        d = defter.get(sym) if isinstance(defter, dict) else None
        defter_adet = _koruma_sayi((d or {}).get("qty")) if isinstance(d, dict) else None
        # KİTABIN BEYAN ETTİĞİ KORUMA SEVİYESİ. `trail_stop` iz süren stop'tur ve sert stop'un
        # ÜSTÜNDE olabilir; ikisinin BÜYÜĞÜ alınır çünkü A4 "koruma gevşetilmez" der — küçüğünü
        # seçmek, kitabın kendi yükselttiği korumayı aynada geri indirmek olurdu.
        sert = _koruma_sayi((d or {}).get("stop")) if isinstance(d, dict) else None
        iz = _koruma_sayi((d or {}).get("trail_stop")) if isinstance(d, dict) else None
        stop = max([x for x in (sert, iz) if x is not None], default=None)
        hedef = _koruma_sayi((d or {}).get("target")) if isinstance(d, dict) else None
        son = fiyat.get(sym)
        mstop = mevcut.get(sym)
        satir = {
            "ticker": sym, "motor": bool(r.get("motor")), "korumali": bool(r.get("korumali")),
            "kismi": bool(r.get("kismi")), "kapsanan": r.get("kapsanan"),
            "broker_adet": broker_adet, "defter_adet": defter_adet,
            "adet_ayrisik": bool(defter_adet is not None and abs(defter_adet - broker_adet) > 1e-9),
            "stop": stop, "hedef": hedef, "son_fiyat": son, "mevcut_stop": mstop,
            # STOPA UZAKLIK: (son − stop)/son. Son fiyat yoksa ÖLÇÜLEMEDİ — "0 uzaklık" yazmak
            # stopun dibinde duran bir pozisyon iddiası olurdu.
            "stop_uzakligi": ((son - stop) / son) if (son and son > 0 and stop is not None) else None,
            "gonderilir": False, "neden": "",
        }
        if not satir["motor"]:
            # A3: motor sahibi olmadığı pozisyona emir göndermez. GÖRÜNÜR olur, öneri ÜRETMEZ.
            satir["neden"] = ("motor-DIŞI pozisyon (operatörün kendi emri) — A3 sahiplik sınırı: "
                              "bu satır için emir ÜRETİLMEZ, yalnız görünürlük")
            disi.append(satir)
            continue
        if satir["korumali"]:
            # İDEMPOTANS: canlı koruma zaten var. İkinci kez onaylamak ikinci koruma kurmaz.
            satir["neden"] = "broker'da CANLI koruma zaten var — ikinci emir gönderilmez (idempotans)"
        elif broker_adet <= 0:
            satir["neden"] = "BROKER adedi 0/okunamadı — uydurma adetle satış emri gönderilmez"
        elif stop is None or hedef is None:
            eksik = " + ".join([a for a, v in (("stop", stop), ("hedef", hedef)) if v is None])
            satir["neden"] = (f"iç defterde {eksik} YOK (portfolio.json.positions[{sym}]) — "
                              f"seviye ÖLÇÜLEMEDİ, uydurulmaz")
        elif stop >= hedef:
            satir["neden"] = (f"kitabın stop'u hedefin üstünde/eşit (stop={stop:g} hedef={hedef:g}) — "
                              f"OCO kurulamaz, defter satırı denetlenmeli")
        elif mstop is not None and stop <= mstop:
            # A4 — ARKA KAPI KAPALI: bu yol var olan bir korumayı DÜŞÜREMEZ.
            satir["neden"] = (f"mevcut canlı stop {mstop:g}, önerilen {stop:g} — koruma yalnız "
                              f"YUKARI taşınır (A4), gevşetme reddedildi")
        else:
            satir["gonderilir"] = True
            satir["neden"] = ""
        satirlar.append(satir)

    gonderilecek = [s for s in satirlar if s["gonderilir"]]
    return {**out, "ok": True, "olculemedi": False, "neden": "",
            "satirlar": satirlar, "motor_disi_satirlar": disi,
            "gonderilebilir": len(gonderilecek),
            "oneri_id": _koruma_oneri_id(gonderilecek, rep)}


def _koruma_oneri_id(gonderilecek: list, rep: dict) -> str:
    """Önerinin PARMAK İZİ — onayın bağlandığı şey. Boş öneri için de üretilir (boşluk da bir hâldir).

    İçeriğe giren her alan bir GEREKÇEyle girer: sembol/adet/stop/hedef, operatörün ekranda GÖRÜP
    onayladığı dört sayıdır — biri değiştiyse onay artık başka bir şeye verilmiş demektir. Çıplak
    sayısı ve payda da girer: yeni bir çıplak pozisyon doğduysa ya da biri korunduysa ekrandaki
    cümle değişmiştir ve eski onay o cümleyi kapsamaz."""
    import hashlib
    govde = json.dumps(
        {"satirlar": [[s["ticker"], s["broker_adet"], s["stop"], s["hedef"]] for s in gonderilecek],
         "korumasiz": rep.get("korumasiz"), "toplam": rep.get("toplam")},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(govde.encode("utf-8")).hexdigest()[:16]


def _koruma_iz_maskele(s, sinir: int = 200) -> str:
    """Denetim satırına giden HER ham metin buradan geçer: onay jetonu maskelenir, uzunluk kırpılır.

    JETON BİR SIR DEĞİL AMA BİR YETKİ İŞARETİDİR (ucun kendi docstring'i bunu yazıyor): kayda
    düşen bir yetki işareti, defteri okuyan herkesin TEKRAR OYNATABİLECEĞİ bir onaydır. Aşağıdaki
    alanlar operatörün gönderdiği HAM gövdeden türüyor — jetonu yanlış kutuya (`oneri_id`)
    yapıştıran bir çağrı onu deftere yazdırabilmemeli. Kırpma ikinci iştir ve aynı sebeple burada:
    ham metin sınırsız uzunlukta gelebilir ve tek bir POST defteri şişirebilir.

    `KORUMA-` öneki taşıyan coid'ler (`P-…KORUMA-20260807-1230-EMR`) YANLIŞLIKLA maskelenmez:
    jetonun tamamı `KORUMA-KUR`dur ve coid'de `KORUMA-`den sonra rakam gelir."""
    from .adapters import alpaca
    return str(s or "").replace(alpaca.KORUMA_ONAY_JETONU, "«jeton-gizlendi»")[:max(1, sinir)]


def koruma_kur(onay: str = "", oneri_id: str = "", onaylayan: str = "?") -> dict:
    """ONAY SONRASI İCRA — her çıplak motor pozisyonuna TEK OCO. Kısmi başarı DÜRÜST raporlanır.

    ÜÇ KAPI, SIRASIYLA (hepsi geçilmeden hiçbir HTTP POST'u doğmaz):
      1. ÖLÇÜM — broker okunamıyorsa emir YOK + neden. "Sessiz başarı" burada SAHTE olurdu:
         ölçemediğimiz bir dünyaya emir göndermek, koruma kurduğumuzu SANMAMIZ demektir.
      2. ONAY JETONU — jetonsuz çağrı KURU KOŞUdur: ne göndereceğini raporlar, hiçbir şeye
         dokunmaz (`close_all` ile aynı desen, A3).
      3. ÖNERİ KİMLİĞİ — jeton doğru olsa bile kimlik EŞLEŞMEK zorunda. Eşleşmezse operatörün
         onayladığı liste ile şu an gönderilecek liste FARKLIDIR; emir gitmez.

    "2/4 gönderildi + 2 neden" der, "tamam" DEMEZ: dönen `ok` yalnız TÜM öneriler gittiğinde
    True'dur ve `satirlar` her satırın kendi sonucunu taşır."""
    from .adapters import alpaca
    rap = koruma_onerileri()
    out = {"ok": False, "gonderilen": 0, "toplam": 0, "satirlar": [], "ozet": "", "detail": "",
           "dry_run": False, "olculemedi": bool(rap.get("olculemedi")),
           "neden": rap.get("neden") or "", "oneri_id": rap.get("oneri_id"),
           "sev": KORUMA_KART_SEV}
    # KAPI 1 — ölçüm. İki dal AYRI (bkz. `koruma_onerileri` içindeki aynı gerekçe): arıza ile
    # yapılandırma hâli tek `or` ifadesinde birleştirilmez.
    olcum_yok = bool(rap.get("olculemedi"))
    if not olcum_yok:
        olcum_yok = bool(rap.get("kapsam_disi"))
    if olcum_yok:
        return {**out, "detail": "ÖLÇÜLEMEDİ — emir gönderilmedi: "
                                 + (rap.get("neden") or "broker durumu okunamadı")}
    gonderilecek = [s for s in rap.get("satirlar") or [] if s.get("gonderilir")]
    out["toplam"] = len(gonderilecek)
    # KAPI 2 — onay jetonu (kuru koşu)
    if onay != alpaca.KORUMA_ONAY_JETONU:
        return {**out, "dry_run": True,
                "detail": "onay jetonu YOK — hiçbir emir gönderilmedi (kuru koşu)",
                "satirlar": [{"ticker": s["ticker"], "adet": s["broker_adet"], "stop": s["stop"],
                              "hedef": s["hedef"], "ok": None,
                              "detail": "onay bekliyor — gönderilmedi"} for s in gonderilecek]}
    # KAPI 3 — öneri kimliği (TURA ÖZEL onay)
    if not oneri_id or oneri_id != rap.get("oneri_id"):
        obs.warn("koruma_onay_bayat", verilen=_koruma_iz_maskele(oneri_id, 32),
                 olculen=str(rap.get("oneri_id")),
                 detail="onay, ölçülen öneriden BAŞKA bir listeye verilmiş — emir gönderilmedi")
        return {**out, "bayat_onay": True,
                "detail": (f"öneri kimliği eşleşmedi (onay={str(oneri_id)[:16] or 'yok'} · "
                           f"ölçüm={rap.get('oneri_id')}) — ekrandaki liste onaydan sonra DEĞİŞTİ; "
                           f"hiçbir emir gönderilmedi, listeyi tazeleyip yeniden onayla")}
    if not gonderilecek:
        return {**out, "detail": "gönderilecek öneri yok — çıplak motor pozisyonu bulunamadı"}

    satirlar, gonderilen = [], 0
    for s in gonderilecek:
        coid = alpaca.koruma_coid(s["ticker"])
        res = alpaca.submit_protective_oco(s["ticker"], s["broker_adet"], s["stop"], s["hedef"],
                                           client_order_id=coid)
        kayit = {"ticker": s["ticker"], "adet": s["broker_adet"], "stop": s["stop"],
                 "hedef": s["hedef"], "plan_id": coid, "ok": bool(res.get("ok")),
                 "reachable": res.get("reachable", True),
                 "detail": str(res.get("detail") or "")[:200]}
        satirlar.append(kayit)
        if res.get("ok"):
            gonderilen += 1
            # DENETİM İZİ (YASA 6): bu satırın okuyucusu olay defteri ve gelen kutusudur — "kim,
            # neyi, hangi adetle, hangi seviyeye, hangi onayla" sorusu kayıttan cevaplanabilmeli.
            obs.log("koruma_oco_gonderildi", plan_id=coid, ticker=s["ticker"],
                    adet=s["broker_adet"], stop=s["stop"], hedef=s["hedef"],
                    tif=alpaca.KORUMA_TIF, onaylayan=onaylayan, oneri_id=oneri_id,
                    adet_kaynagi="broker")
        else:
            obs.warn("koruma_oco_dusuru", plan_id=coid, ticker=s["ticker"], adet=s["broker_adet"],
                     stop=s["stop"], hedef=s["hedef"], onaylayan=onaylayan,
                     reachable=res.get("reachable", True), hata=kayit["detail"],
                     detail="koruma OCO'su gönderilemedi — pozisyon HÂLÂ çıplak")
    ozet = f"{gonderilen}/{len(gonderilecek)} gönderildi"
    dusen = [k for k in satirlar if not k["ok"]]
    if dusen:
        ozet += " · " + " · ".join(f"{k['ticker']}: {k['detail'] or 'gerekçe bildirilmedi'}"
                                   for k in dusen)
    obs.log("koruma_kur_ozet", gonderilen=gonderilen, toplam=len(gonderilecek),
            onaylayan=onaylayan, oneri_id=oneri_id)
    return {**out, "ok": gonderilen == len(gonderilecek) and gonderilen > 0,
            "gonderilen": gonderilen, "satirlar": satirlar, "ozet": ozet,
            "detail": "" if not dusen else f"{len(dusen)} öneri gönderilemedi — pozisyon çıplak kaldı"}


def _koruma_kur_sonucu(res: dict) -> str:
    """İcranın hangi DALDA bittiği — tek jeton, denetim satırının omurgası.

    Dallar `koruma_kur`un KAPI SIRASIYLA okunur ve sıra bir üslup tercihi değildir: ölçüm düşükse
    uç jeton kapısına hiç varmaz, o yüzden "ölçülemedi" her şeyin önündedir; jeton yoksa öneri
    kimliği hiç denenmez, o yüzden "kuru koşu" bayatlıktan öncedir. Sıra ters olsaydı satır,
    çağrının GERÇEKTE nerede durduğunu değil, okuyucunun sandığı yeri yazardı."""
    if res.get("olculemedi"):
        return "olculemedi"
    if res.get("dry_run"):
        return "onaysiz-kuru-kosu"
    if res.get("bayat_onay"):
        return "bayat-oneri-kimligi"
    if not res.get("toplam"):
        return "gonderilecek-oneri-yok"
    if res.get("ok"):
        return "gonderildi"
    return "kismi-ya-da-dusuk"


def _koruma_onaylayan(request: Request) -> str:
    """Onayı KİM verdi — ölçülebilen tek gerçek: hangi kimlik yolundan geldiği. Bir kullanıcı adı
    UYDURULMAZ (bu depoda tek-operatör kimliği var, kişi adı taşıyan bir alan yok)."""
    try:
        if auth.verify_session(request.cookies.get(auth.COOKIE_NAME)):
            return "pano-oturumu"
        if request.headers.get("x-meridian-token"):
            return "betik-tokeni"
    except Exception:  # sessiz-yutma: kimlik yolu okunamadı — denetim izi "bilinmiyor" der, uydurma bir onaylayan yazmaz
        return "bilinmiyor"
    return "kimliksiz-yerel"


@app.get("/api/alpaca/koruma")
def api_alpaca_koruma(request: Request):
    """Çıplak motor pozisyonları + OCO önerileri. SALT OKUMA — çağrılması emir üretmez."""
    _auth(request)
    return koruma_onerileri()


@app.post("/api/alpaca/koruma_kur")
async def api_alpaca_koruma_kur(request: Request):
    """Onaylanmış koruma OCO'larını gönder. Gövde: {onay, oneri_id}.

    JETON GÖVDEDE, SORGUDA DEĞİL (`close_all`ın `?confirm=` deseninden BİLEREK ayrılır): sorgu
    dizeleri sunucu loglarına, tarayıcı geçmişine ve `Referer` başlığına düşer — `api._auth`ın
    2026-07-28'de `?token=`i kaldırma gerekçesinin aynısı. Buradaki jeton bir sır değil ama bir
    YETKİ işaretidir ve log'a düşen bir yetki işareti, tekrar oynatılabilir bir onaydır.

    UÇ DÜZEYİ DENETİM İZİ (2026-08-07, v211'in eksik yarısı). v211 Y8 "her GÖNDERİM olay bırakır"
    der ve o çivi tutuyor — ama bu ucun dallarının ÇOĞU hiçbir yere düşmüyordu: onaysız çağrı
    (kuru koşu), ölçüm düşükken dönen tur, gönderilecek öneri kalmamış tur ve JETONSUZ gelen bayat
    kimlik. Kalan tek kayıtlı ret (`koruma_onay_bayat`) yalnız jeton DOĞRUYKEN yazılıyordu.
    Oysa bu ucun cevapladığı soru "operatörün yaptığı her değişiklik kayıtlı mı"dır ve asıl kayda
    değer vaka REDDEDİLEN onaydır: düğmeye BASILDIĞI hiçbir yerde yazmıyorsa "bu neden olmadı"
    sorusunun kaynağı yoktur — ve o soru, çıplak duran bir pozisyonun karşısında sorulur.

    ÇOĞALTMA YOK: alt katman (`koruma_kur`) emir BAŞINA satır yazar (`koruma_oco_gonderildi` /
    `koruma_oco_dusuru`) ve tur özetini bırakır (`koruma_kur_ozet`). Buradaki iz onların kopyası
    değildir — HTTP çağrısı başına TEK satırdır, emir alanı (plan_id/stop/hedef/ticker) TAŞIMAZ ve
    tek soruyu cevaplar: "operatör bastı, ne oldu". Dört öneriyi gönderen bir tur beş satır bırakır
    (4 gönderim + 1 tur özeti), buna bir tane daha eklenmez — bu satır GÖNDERİMİN değil BASMANIN
    kaydıdır ve gönderim hiç olmadığında da vardır.

    SEVİYE TEK: hepsi `obs.log`. Reddedilen onayı `warn`a çıkarmak cazipti ve BİLEREK yapılmadı —
    bayat kimlik için uyarı ZATEN var (`koruma_onay_bayat`) ve aynı olguyu iki seviyede yazmak,
    gelen kutusunda tek bir basışı iki ayrı olay gibi gösterirdi. Bu satır bir alarm değil, bir
    BASIŞ KAYDIDIR; anormallik sinyali alt katmanın işidir."""
    _auth(request)
    from .adapters import alpaca
    try:
        body = await request.json()
    except Exception:  # sessiz-yutma: gövdesiz/bozuk JSON = onay YOK; aşağıdaki kapı bunu kuru koşu olarak raporlar
        body = {}
    if not isinstance(body, dict):
        body = {}
    onay = str(body.get("onay") or "")
    oneri_id = str(body.get("oneri_id") or "")
    onaylayan = _koruma_onaylayan(request)
    # ONAY VERİLDİ Mİ — JETONUN KENDİSİ DEĞİL, KARŞILAŞTIRMANIN SONUCU. Bir bool tekrar
    # oynatılamaz. Sonucun `dry_run`ından TÜRETİLMEZ: ölçüm düşükken uç jeton kapısına hiç varmaz
    # ve o dalda `dry_run` False döner — türetilen bayrak orada "onay vardı" diye UYDURURDU.
    onay_verildi = bool(onay) and onay == alpaca.KORUMA_ONAY_JETONU
    res = koruma_kur(onay=onay, oneri_id=oneri_id, onaylayan=onaylayan)
    sonuc = _koruma_kur_sonucu(res)
    # TOPLAM ÖLÇÜLEMEDİ DALINDA None — 0 DEĞİL. `koruma_kur` ölçüm kapısında geri döner ve "kaç
    # öneri gönderilmeliydi" hiç hesaplanmaz; oraya 0 yazmak, korumasız pozisyon olmadığını iddia
    # etmek olurdu (`koruma_onerileri` de aynı dalda `gonderilebilir: None` döndürüyor).
    # `gonderilen` ise HER dalda ölçülüdür: emir yüzeyine hiç girilmeyen dallarda gerçekten 0'dır.
    obs.log("koruma_kur_istegi",
            oneri_id=_koruma_iz_maskele(oneri_id, 64) or "—", onay_verildi=onay_verildi,
            onaylayan=onaylayan, sonuc=sonuc,
            gonderilen=res.get("gonderilen"),
            toplam=(None if sonuc == "olculemedi" else res.get("toplam")),
            ozet=_koruma_iz_maskele(res.get("ozet") or res.get("detail") or "", 240))
    if res.get("gonderilen"):
        _diag_onbellek_bosalt("koruma_kur")
    return res


# ---------- Batch N: ops & UX ----------
# ---- /halt SATIR İÇİ BETİĞİ DIŞARI ALINDI (v203, 2026-08-07) ---------------------------------
# ÖLÇÜLEN VE KAPATILAN GERİLEME. Bu sayfa gövdeli bir `<script>` taşıyordu ve `script-src 'self'`
# onu — `<script src>` olmayan HER bloğu — BLOKLAR. Başlık bugüne dek hiçbir yerde zorlanmadığı
# için (Caddy koşmuyor; yukarıdaki "GÜVENLİK BAŞLIKLARI" notu) arıza görünmüyordu; politikayı
# uygulama katmanına almak onu ANINDA görünür kılardı: sayfa çizilir, dev kırmızı düğme durur,
# ve TIKLAYINCA HİÇBİR ŞEY OLMAZ. Acil durdurma yüzeyinde sessizce ölü bir düğme, bu depoda
# üretilebilecek en kötü tek arızadır — panonun geri kalanı ölse "pano bozuk" denir, burada
# operatör "durdurdum" sanır.
#
# İKİ YOL VARDI ve seçilmeyeni de yazılı kalsın: (a) /halt'a CSP'yi `'sha256-…'` kaynağıyla
# genişleterek göndermek — `'unsafe-inline'` değil, yani sözleşmeyi ihlal etmezdi, AMA o sayfayı
# ötekilerden AYRI bir politikaya bağlardı: iki politika, zamanla ayrışan iki yasa, ve "birebir
# Caddyfile" ölçümü tam da orada anlamını yitirirdi. (b) betiği aynı-origin bir rotaya almak —
# `script-src 'self'`i GERÇEKTEN karşılamak. (b) seçildi; bu, landing.html ve workflow.html için
# 2026-08-01'de verilen kararın ve tests/test_web_csp_uyum.py'nin söylediğinin AYNISI.
#
# NEDEN DOSYA DEĞİL SABİT: `meridian/web/` altına yeni bir üretim dosyası bu turun yazma sınırının
# dışında; ayrıca sayfanın kendisi de bu dosyada üretiliyor — HTML burada, betiği orada olsaydı
# ikisi ayrı yerde bayatlayabilirdi. `_statik`in disk-bağlı ETag/304 makinesi burada YOK ve
# taklit de edilmedi (600 baytlık bir sabit için ikinci bir önbellek yasası yazmak, kazandığından
# çok sürükleme üretir); `_NOCACHE` HTML'in kendisiyle aynıdır, yani ikisi birlikte bayatlar.
_HALT_JS = """const t=new URLSearchParams(location.search).get('token');const H=t?{'x-meridian-token':t}:{};
async function hit(p){document.getElementById('s').textContent='...';const r=await fetch(p,{method:'POST',headers:H});
document.getElementById('s').textContent=r.ok?(p.includes('resume')?'DEVAM edildi':'DURDURULDU'):'hata '+r.status;
const b=document.getElementById('b');if(p.includes('halt')){b.textContent='▶ DEVAM';b.className='g';b.onclick=()=>hit('/api/resume')}
else{b.textContent='■ HALT';b.className='';b.onclick=()=>hit('/api/halt')}}
document.getElementById('b').onclick=()=>hit('/api/halt');"""


@app.get("/halt.js")
def mobile_halt_js():
    """`/halt` sayfasının betiği — aynı origin, yani `script-src 'self'` altında ÇALIŞIR.

    `/halt` gibi yetkisizdir ve olması gereken de budur: betiğin kendisi bir sır taşımaz (token'ı
    çalışma anında sayfanın URL'inden okur), ve arkasına bir kapı konsaydı acil durdurma sayfası
    kimlik doğrulamadan önce ölü açılırdı."""
    return PlainTextResponse(_HALT_JS, media_type="application/javascript", headers=_NOCACHE)


@app.get("/halt", response_class=HTMLResponse)
def mobile_halt():
    """#44 — a standalone, phone-friendly panic page. One giant button → POST /api/halt.
    Reads the token from ?token= so it works over the tunnel. No dependency on the SPA.

    "Self-contained" ARTIK TAM DOĞRU DEĞİL ve cümle bu yüzden düzeltildi (v203): betik
    `/halt.js`ten gelir. Bağımlılık AYNI ORIGIN'de, aynı süreçte, aynı dosyada üretilen tek bir
    rotadır — SPA'ya, diske ya da bir dış host'a bağlanmaz — ama "hiçbir şey istemez" demek
    yanlış olurdu: o rota düşerse düğme ölür (çivisi tests/test_guvenlik_basliklari_v203.py Ç5)."""
    return HTMLResponse("""<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<title>Meridian — HALT</title><style>body{margin:0;background:#0b0b0f;color:#eee;font-family:system-ui;
display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;gap:24px}
button{width:78vw;max-width:420px;height:34vh;border:none;border-radius:24px;font-size:8vw;font-weight:800;
color:#fff;background:#c0362c;box-shadow:0 8px 40px rgba(192,54,44,.4)}button:active{transform:scale(.97)}
#s{font-size:16px;color:#9aa}.g{background:#1c7a3f!important}</style>
<h2>Meridian · acil durdur</h2><button id=b>■ HALT</button><div id=s>hazır</div>
<script src="/halt.js"></script>""", headers=_NOCACHE)


@app.get("/api/state/snapshot")
def api_state_snapshot(request: Request):
    """#43 — download a tar.gz of the agent's learning state (trades, versions, ledger, lessons) for
    backup / off-box archival. Read-only; excludes bar caches and secrets."""
    _auth(request)
    import io
    import tarfile
    keep = ["trades.jsonl", "portfolio.json", "strategy.yaml", "scoreboard.json", "hypotheses.jsonl",
            "lessons.md", "equity_curve.json", "regime.json", "skills_registry.json", "goal.yaml", "bounds.yaml"]
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in keep:
            p = config.STATE / name
            if p.exists():
                tar.add(str(p), arcname=f"meridian_state/{name}")
            # SQLite GEÇİŞİ SONRASI YEDEK BOŞALMASIN (WP-H/H9, 2026-07-31): yukarıdaki listenin
            # dördü (`trades`, `portfolio`, `scoreboard`, `equity_curve`) DB'ye taşındığında
            # dosyaları `.migrated` ekiyle durur ve `p.exists()` False döner — yedek, öğrenmenin
            # yeniden üretilemez kısmını SESSİZCE dışarıda bırakırdı. `.migrated` arşivi de
            # eklenir: geçiş öncesi tarihin kanıtıdır ve `MERIDIAN_DB=off` yolunun girdisidir.
            pm = config.STATE / (name + ".migrated")
            if pm.exists():
                tar.add(str(pm), arcname=f"meridian_state/{name}.migrated")
        hist = config.STATE / "history"
        if hist.exists():
            tar.add(str(hist), arcname="meridian_state/history")
        # DEFTER ÇEKİRDEĞİ: TUTARLI kopya (çevrimiçi yedek API'si). Ham `meridian.db` dosyasını
        # tar'lamak WAL yüzünden EKSİK/yarışlı bir kopya üretirdi — bkz. storage.backup_to.
        if storage.active(storage.TRADES):
            import tempfile as _tf
            with _tf.TemporaryDirectory() as _d:
                _snap = storage.backup_to(Path(_d) / storage.DB_NAME)
                tar.add(str(_snap), arcname=f"meridian_state/{storage.DB_NAME}")
    buf.seek(0)
    return PlainTextResponse(buf.read(), media_type="application/gzip",
                             headers={"Content-Disposition": "attachment; filename=meridian_state.tar.gz"})


@app.post("/api/notify/test")
def api_notify_test(request: Request):
    """#42 — send a test alert to the configured Telegram/webhook so the operator can verify wiring."""
    _auth(request)
    from . import notify
    if not notify.configured():
        return {"ok": False, "detail": "no Telegram/webhook configured — set it in Ayarlar"}
    ok = notify.send("✅ Meridian test bildirimi — kanal çalışıyor.")
    obs.log("notify_test_sent", ok=bool(ok))     # dışarıya çıkan her mesaj kayıtlı (N/A sorgusu)
    _diag_onbellek_bosalt("notify_test")         # teslimat sayaçları + alarm bütçesi kıpırdadı
    return {"ok": bool(ok)}


@app.get("/api/digest/weekly", response_class=PlainTextResponse)
def api_digest_weekly(request: Request):
    """#41 — a 7-day plain-text digest: closed trades this week, their R, and the running score."""
    _auth(request)
    import datetime as dt
    goal = config.goal()
    trades = store.read_jsonl("trades.jsonl")
    cutoff = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    week = [t for t in trades if str(t.get("ts_close", ""))[:10] >= cutoff]
    wpnl = round(sum(float(t.get("pnl_dollars", 0)) for t in week), 2)
    wr = [float(t.get("r_multiple", 0)) for t in week]
    sd = analytics.score_mod.score_detail(trades, goal)
    lines = ["MERIDIAN — HAFTALIK ÖZET (son 7 gün)",
             f"Kapanan işlem : {len(week)}   ·   toplam P&L: ${wpnl}",
             f"Ort. R (hafta): {round(sum(wr)/len(wr), 3) if wr else '—'}   ·   kazanan: {sum(1 for r in wr if r>0)}/{len(wr)}",
             f"Genel skor    : {sd.get('score')}   avg_R {sd.get('avg_r')}   isabet {sd.get('win_rate')}",
             "", "İşlemler:"]
    for t in sorted(week, key=lambda x: str(x.get("ts_close", "")))[-15:]:
        lines.append(f"  {str(t.get('ts_close',''))[:10]}  {t.get('ticker',''):5}  {t.get('r_multiple',0):+.2f}R  {t.get('exit_reason','')}")
    lines.append("\nNot: kağıt işlem — gerçek para yok.")
    return "\n".join(lines)


@app.get("/api/trade/{trade_id}")
def api_trade(trade_id: str, request: Request):
    """#39 (light) — one closed trade's full detail + a recent price series for the drill-down view."""
    _auth(request)
    trades = store.read_jsonl("trades.jsonl")
    tr = next((t for t in reversed(trades) if t.get("id") == trade_id), None)
    if tr is None:
        raise HTTPException(status_code=404, detail="trade not found")
    series = []
    try:
        from .adapters import data
        bars = data.load_bars(tr["ticker"], str(tr.get("ts_open", ""))[:10], str(tr.get("ts_close", ""))[:10])
        if bars is not None and not bars.empty:
            series = [{"date": str(d)[:10], "o": float(o), "h": float(h), "l": float(lo), "c": float(cl)}
                      for d, o, h, lo, cl in zip(bars["date"], bars["open"], bars["high"], bars["low"], bars["close"])][-60:]
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        series = []
    return {"trade": tr, "series": series}


# K1-EMEKLİ: kanonik yüzey /api/skills `recent_runs` (K1'de bağlandı). Yeni tüketici bağlanmaz.
@app.get("/api/pipeline_runs")
def api_pipeline_runs(request: Request):
    _auth(request)
    return {"runs": list(reversed(store.read_jsonl("pipeline_runs.jsonl")[-60:]))}


@app.get("/api/approvals")
def api_approvals(request: Request):
    """v11 #4 — BİRLEŞİK GELEN KUTUSU: onay bekleyen HER karar türü tek listede (otonomi
    seviyesinden bağımsız): kapıyı geçmiş silahlanma ölçümleri, skill revizyon taslakları,
    Eksen-2 önerileri, (L1+) canlı emir onayları. Her öğe: kanıt + yapılabilir eylem."""
    _auth(request)
    from . import skill_evolve as _se
    inbox = []
    ar = store.read_json("arming_report.json", {}) or {}
    for setup, m in (ar.get("measurements") or {}).items():
        if m.get("status") == "gate_passed":
            rep = (ar.get("cf_report") or {}).get(setup) or {}
            inbox.append({"type": "arming", "id": f"arming:{setup}", "title": f"Kurulum silahlanmaya hazır: {setup}",
                          "evidence": f"kapı GEÇTİ · P={m.get('search_p')} · onay P={m.get('confirm_p', '—')} · "
                                      f"cf n={rep.get('n')} ort {rep.get('avg_r')}R",
                          "actions": [],
                          "note": "Silahlanma kod değişikliğidir (ARMED_SETUPS) — onayını Claude'a söyle."})
    for r in _se.pending_drafts():
        ev = r.get("evidence") or {}
        inbox.append({"type": "skill_revision", "id": f"rev:{r['skill']}", "title": f"Revizyon taslağı: {r['skill']}",
                      "evidence": f"{esc_ev(r.get('rationale'))} · kanıt n={ev.get('n')} ort {ev.get('avg_r')}R",
                      "actions": ["apply", "reject"], "skill": r["skill"]})
    from . import skills as _sk2
    for rec in _sk2.pending_recommendations():
        inbox.append({"type": "skill_rec", "id": f"rec:{rec.get('skill')}",
                      "title": f"Eksen-2: {rec.get('skill')} → {rec.get('action')}",
                      "evidence": rec.get("rationale") or "", "actions": ["apply"],
                      "skill": rec.get("skill"), "action": rec.get("action")})
    lvl = config.limits()["autonomy_level"]
    return {"level": lvl, "inbox": inbox,
            "pending": store.read_jsonl("approvals.jsonl") if lvl >= 1 else [],
            "note": "Gelen kutusu her seviyede aktif; canlı emir onayları yalnız L1+."}


def esc_ev(x):
    return str(x or "")[:200]


def _last_close(ticker: str):
    """Bayat-sinyal dürüstlüğü için güncel bağlam: önbellekteki son kapanış (ağ çağrısı YOK)."""
    try:
        import pandas as pd
        cp = config.BARS / f"{str(ticker).lower().replace('.', '-')}.csv"
        if not cp.exists():
            return None
        df = pd.read_csv(cp, usecols=["date", "close"])
        return {"date": str(df["date"].iloc[-1])[:10], "close": round(float(df["close"].iloc[-1]), 2)}
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        return None


def _enrich_stale_plans(plans: list, latest_session: str | None) -> None:
    """Operatör bulgusu (GS 1140): süresi dolmuş sinyal taze karar gibi okunuyordu. Her gösterilen plana
    dürüstlük alanları: expired (tek-seans geçerlilik: plan tarihi < son işlenmiş seans), age_days,
    last_close (önbellek), traded (plan_id gerçek işleme dönüştü mü). Kusur karardaydı değil sunumdaydı —
    bu alanlar sunumu karara eşitler."""
    if not plans:
        return
    import datetime as _dt
    traded_ids = {t.get("plan_id") for t in store.read_jsonl("trades.jsonl")}
    for p in plans:
        try:
            p["expired"] = bool(latest_session and p.get("date") and p["date"] < latest_session)
            if p["expired"]:
                p["age_days"] = (_dt.date.fromisoformat(latest_session)
                                 - _dt.date.fromisoformat(p["date"])).days
            p["traded"] = p.get("id") in traded_ids
            lc = _last_close(p.get("ticker"))
            if lc:
                p["last_close"] = lc["close"]
                trig = float(p.get("entry_trigger") or 0)
                if trig:
                    p["drift_pct"] = round((lc["close"] - trig) / trig * 100, 1)
        except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
            pass


def _onay_bekleyen_damgala(planlar: list) -> int:
    """Onay bekleyen REVIEW planlarını DAMGALAR (`onay_bekliyor`) ve sayar — TEK yasa, tek geçiş.

    KUSUR (UX denetimi 2026-08-06, B2): Genel Bakış'ın "Bugün ne var" kartı `inbox_count` okuyordu
    ve o sayım YALNIZ silahlanma ölçümü + skill revizyonu + Eksen-2 önerisini kapsıyordu. Operatörün
    onayını bekleyen REVIEW planları HİÇ girmiyordu: üç plan onay beklerken açılış ekranı
    "0 bekleyen onay — senden bir şey beklenmiyor" yazıyordu. Ölçülmüş bir gerçeğin yanlış
    olumsuzlanması — None ≠ 0 yasasının kardeşi: 0 ≠ "yok".

    NEDEN BAYRAK, NEDEN İKİNCİ BİR FİLTRE DEĞİL: aynı ölçütü hem burada hem panoda yazmak, aynı
    sorunun iki cevabını üretirdi (biri `expired` bilir, diğeri bilmez — bu deponun tekrar eden
    kusur sınıfı). Sunucu damgalar, pano YALNIZ bayrağı okur: sayaç ile liste ayrışamaz.

    ÖLÇÜT ÜÇ KOŞULLU: kapı hükmü REVIEW · operatör onayı YOK · seansı geçmemiş (`expired`).
      · GO onay beklemez (zaten giriş kuyruğunda), NO_GO ASLA onaylanamaz (guard'ın sert reddi).
      · Onayın varlığı `loop.operator_onayli` ile ölçülür — alanın VARLIĞI değil DAMGASI (o yasanın
        sahibi loop.py'dir; buraya kopyalanan ikinci bir tanım ilk düzenlemede ayrışırdı).
      · `expired` `_enrich_stale_plans` tarafından yazılır; bu fonksiyon ONDAN SONRA çağrılmalıdır
        (çağrı sırası api_today'de beyanlı). Süresi dolmuş plan onaylanamaz — uç da 409 verir.
    """
    from . import loop as _loop
    n = 0
    for p in planlar:
        bekliyor = (str(p.get("gate_verdict") or "") == "REVIEW"
                    and not _loop.operator_onayli(p)
                    and not p.get("expired"))
        p["onay_bekliyor"] = bekliyor
        n += 1 if bekliyor else 0
    return n


def _inbox_count(planlar: list | None = None) -> int:
    """Kenar çubuğu rozeti + "Bugün ne var" kartı: senden İŞ isteyen karar sayısı (ucuz sayım).

    DÖRT KAYNAK (v195-a'da dördüncü eklendi): silahlanma kapısını geçen ölçüm · skill revizyon
    taslağı · Eksen-2 önerisi · onay bekleyen REVIEW planı.

    PLAN SAYIMI ÇAĞIRANDAN GELİR, DEFTERDEN DEĞİL: `todays_plans` zaten `analytics.today()`de
    okundu ve damgalandı. Burada `trade_plans.jsonl`i ikinci kez okumak, aynı yanıtın içinde iki
    okuma anı (ve iki farklı cevap) demek olurdu.
    """
    # PLAN SAYIMI TRY'IN DIŞINDA: aşağıdaki üç kaynaktan biri patlarsa ÖLÇÜLMÜŞ plan sayısı da
    # sıfırlanmamalı — bir ölçümün hatası, başka bir ölçümün sonucunu silemez.
    n_plan = sum(1 for p in (planlar or []) if p.get("onay_bekliyor"))
    try:
        from . import skill_evolve as _se, skills as _sk3
        ar = store.read_json("arming_report.json", {}) or {}
        n = sum(1 for m2 in (ar.get("measurements") or {}).values() if m2.get("status") == "gate_passed")
        n += len(_se.pending_drafts())
        n += len(_sk3.pending_recommendations())
        return n_plan + n
    except Exception as e:
        # YASA 4 (2026-07-21): burada sessizce 0 dönmek, operatörün gelen kutusunda BEKLEYEN kararlar
        # varken rozetin "0" göstermesi demek — okunmamış onay = alınmamış karar. Rozet yine sayıyı
        # (plan tarafını) döner, sebebi artık olay akışında.
        obs.warn("inbox_count_failed", error=f"{type(e).__name__}: {e}")
        return n_plan


# ---------- write surface (operator intents only) ----------
@app.post("/api/halt")
def api_halt(request: Request):
    _auth(request)
    # TEK KAPI (temizlik turu 2026-07-30): eskiden burada `health.halt_path().touch()` vardı ve
    # `api_resume` de dosyayı KENDİ eliyle `unlink` ediyordu — yani kill-switch'in yasası İKİ
    # yerde uygulanıyordu: `health.set_halt` ve bu iki uç. `set_halt`in üretim çağıranı YOKTU
    # (çağıran taraması: yalnız testler), yani aynı kapının "resmî" hâli ölü, kopyası canlıydı.
    # Yön KARARLA seçildi: kardeş kapı `api_intraday_arm` ZATEN `health.set_intraday_arm`e
    # delege ediyor (bkz. aşağıdaki intraday ucu) ve bayrak dosyalarının yasası `health.py`de
    # yaşıyor. Uç noktalar artık niyeti bildirir, dosya işini bayrağın sahibi yapar.
    health.set_halt(True)
    # nabzı SIFIRDAN yazma — rejim/bütçe gibi alanlar silinip HUD "rejim: yok" gösteriyordu (2026-07-20)
    _hb = {k: v for k, v in store.read_json("heartbeat.json", {}).items()
           if k not in ("ts", "mode", "autonomy_level", "halted")}
    health.write_heartbeat(**{**_hb, "note": "HALT via dashboard"})
    obs.alarm(obs.ALARM_HALT, "HALT via dashboard")
    try:
        from . import notify
        notify.halted(True)
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass
    _diag_onbellek_bosalt("halt")
    return {"halted": True, "message": "state/HALT created — new entries stop within one bar."}


@app.post("/api/resume")
def api_resume(request: Request):
    _auth(request)
    health.set_halt(False)      # TEK KAPI — bkz. api_halt'taki gerekçe (idempotent: dosya yoksa no-op)
    obs.log("resume", via="dashboard")
    try:
        from . import notify
        notify.halted(False)
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass
    _diag_onbellek_bosalt("resume")
    return {"halted": False, "message": "HALT cleared."}


@app.post("/api/plan/{plan_id}/onayla")
def api_plan_onayla(plan_id: str, request: Request):
    """REVIEW planına operatör onayı — "review edebiliyorum, işlem yapamıyorum" şikâyetinin kapısı.

    YASA BURADA DEĞİL `loop.operator_onay_ver`DE: `trade_plans.jsonl`in yazar listesi
    `ledgers.CONTRACTS`ta yazılıdır (loop/run/hermes) ve uç noktanın deftere kendi eliyle yazması,
    o sözleşmenin var olma sebebi olan "haberi olmayan ikinci yazar" sınıfını yeniden açardı.
    Uç nokta NİYETİ bildirir (`api_halt` → `health.set_halt` deseni), kararı ve yazımı yasa verir.

    SÖZLEŞME: onay bir OLAYdır — `gate_verdict` GERİYE DÖNÜK DEĞİŞMEZ. NO_GO ASLA onaylanmaz;
    seansı geçmiş plan onaylanmaz; HALT'ta onaylanmaz. Reddin sebebi 409 gövdesinde metin olarak
    döner (sessiz "olmadı" yok). Bu uç EMİR GÖNDERMEZ: plan silahlı kuyruğa girer, aynaya gönderim
    mevcut TEK kapıdan (`/api/alpaca/submit_armed` → `loop.mirror_submit_armed`) geçer."""
    _auth(request)
    from . import loop as _loop
    res = _loop.operator_onay_ver(plan_id, kanal="pano")
    if not res.get("ok"):
        raise HTTPException(status_code=int(res.get("kod") or 409),
                            detail=str(res.get("neden") or "onaylanamadı"))
    # Defter GERÇEKTEN kıpırdadı (plan satırı + silahlı küme) → teşhis önbelleği düşer, yoksa pano
    # onayı bastıktan sonra onay-öncesi kitabı geri okur ("hiçbir şey olmadı" hissi).
    _diag_onbellek_bosalt("plan_operator_approved")
    return res


@app.post("/api/approvals/{approval_id}")
async def api_approve(approval_id: str, request: Request):
    _auth(request)
    if config.limits()["autonomy_level"] < 1:
        raise HTTPException(status_code=403, detail="approvals are L1+ only; system is L0 paper")
    body = await request.json()
    decision = body.get("decision")
    reason = body.get("reason", "")
    store.append_jsonl("approvals.jsonl", {"id": approval_id, "decision": decision,
                                           "reason": reason, "ts": memory.now_iso()})
    # Operatör kararı OLAY defterine de düşer: onay/ret, alarmların ve döngü olaylarının yanında
    # tek bir zaman çizgisinde okunabilmeli (N/A sorgusu, 2026-07-21).
    obs.log("approval_decision", approval_id=approval_id, decision=str(decision)[:40],
            has_reason=bool(reason))
    if reason:
        memory.distill_lessons()
    # L0'da 403 YUKARIDA fırladı (zarf düşmez); buraya gelen istek onay defterine satır yazmıştır.
    _diag_onbellek_bosalt("approval_decision")
    return {"ok": True, "id": approval_id, "decision": decision}
