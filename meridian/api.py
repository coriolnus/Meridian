"""api.py — state/ üzerinde FastAPI okuma-modeli ve dar bir operatör yazma yüzeyi (HALT/DEVAM, onaylar).

Pano sunucusudur: motorun state/ altına yazdığı defter ve anlık görüntüleri okuyup JSON/HTML olarak
servis eder, pano statik dosyalarını (app.js, theme.js, fontlar) dağıtır. Pano broker'la ASLA
doğrudan konuşmaz — tarayıcı durumu okur, yalnız operatör NİYETİ gönderir (HALT/devam, plan ve
koruma onayı, skill kararları, sır yönetimi). Tek-operatör tasarımı: erişim loopback/IAP tüneli
üzerinden; parola oturumu + isteğe bağlı x-meridian-token başlığı. Araştırma sistemi, kâğıt mod;
yatırım tavsiyesi değildir.

Kilit girişler: `app` (uvicorn'un yüklediği FastAPI uygulaması), `_lifespan`→`_autostart` (bayraklara
göre scheduler, hermes_runtime, mirror_stream, marketstream/barfeed ve intraday_cycle tüketicisini
ayağa kaldırır), `_auth` (oturum çerezi + başlık token'ı), `_auth_posture_check` (açılış yetki
duruşu), `_NativeRoute` (her uç dönüşü `store.sanitize`den geçer: numpy tipleri ve NaN/±Inf telden
çıkamaz). Uç aileleri: /healthz, /metrics, /api/summary, /api/diagnostics, /api/hermes,
/api/scheduler, /api/alpaca, /api/approvals, /api/halt, /api/resume, /api/infra, /api/roadmap…
Son ikisi state/ DIŞINA bakan tek okuma yüzeyleridir: `/api/infra` işletim sistemine (çekirdek,
bellek, disk, systemd birimleri), `/api/roadmap` depo kökündeki `ROADMAP.md`ye. İkisi de yalnız
standart kütüphaneyle ölçer (psutil bağımlılığı YOK) ve ölçemediği alanı None + neden döndürür.

Değişmezler: loopback DIŞINA parolasız bağlanma süreci BAŞLATMAZ (fail-closed RuntimeError); okuma
uçları durum ÜRETMEZ (hesabı analytics/health/scheduler yapar); yazma yüzeyi operatör niyetiyle
sınırlıdır ve karar/onay kayıtları deftere düşer. Okur: state/ (store üzerinden) + analytics
türevleri; yazar: HALT/onay/sır gibi niyetleri yine store/secrets üzerinden. Komşular: auth,
analytics, health, obs, scheduler, hermes_runtime."""
from __future__ import annotations
import functools
import hmac
import html
import inspect
import json
import os
import re
import shutil
import time as _time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

from . import auth

from . import store, storage, config, analytics, health, memory, obs, secrets as secrets_mod
from . import topviews as topviews_mod

def _auth_posture_check() -> None:
    """Açılışta yetki duruşunu DÜRÜSTÇE bildir.

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

    # ---- GENEL ARAYÜZE PAROLASIZ AÇILMA: BAŞLATMAYI REDDET ----------------------
    # Yukarıdaki uyarı bir UYARIYDI ve uyarılar okunmaz. Oracle Cloud dağıtımı öncesi bu, sessiz
    # bir felaket yoluydu: operatör `--host 0.0.0.0` verir, `obs.warn` state'e düşer, kimse
    # bakmaz, ve hesap durumu + HALT/Flatten yüzeyi internete açılır.
    #
    # Kural: loopback DIŞINDA bir arayüze bağlanılıyorsa parola KURULU olmalı. Kurulu değilse
    # süreç açılmaz. Bu bir kolaylık kaybı değil — parolayı kurmak tek komut, ve alternatifi
    # yetkisiz bir broker denetim yüzeyi.
    #
    # HAYALET BAYRAK KALDIRILDI: burada bir zamanlar "MERIDIAN_TRUST_PROXY=1 kaçış
    # kapısı BİLİNÇLİ olarak dar" yazıyordu. O bayrağı HİÇBİR KOD OKUMUYORDU — repo genelinde
    # (py/sh/md/yml/service/plist) tek geçtiği yer bu yorum satırıydı. Yani güvenlik duruşu
    # yorumunda var olmayan bir mekanizma anlatılıyordu ve bayrağı veren operatör hiçbir davranış
    # değişikliği görmezdi. Kaçış kapısı YOK ve olmasına gerek de yok: TLS sonlandıran bir vekil
    # kullanan operatör panoyu 127.0.0.1'de bırakır, o durumda zaten loopback'tedir ve bu kural
    # hiç tetiklenmez. Gerçekten bir kaçış kapısı gerekirse OKUNAN bir bayrak olarak eklenir —
    # güvenlik duruşu yorumla değil kodla gevşetilir.
    # TEK KAYNAK — OKUNAN DEĞER ARTIK GERÇEKTEN BAĞLANILAN ADRESTİR.
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
    basıyordu — gürültü, gerçek uyarıları gizler. Davranış birebir aynı."""
    _auth_posture_check()
    _autostart()
    yield


# `openapi_url=None` DE KAPALI — docs_url/redoc_url'i kapatmak YETMEZ. FastAPI her rota
# gövdesinin docstring'ini OpenAPI şemasının `description` alanına AYNEN kopyalar ve
# /openapi.json varsayılan olarak KİMLİK DOĞRULAMASIZ servis edilir (ölçüldü: 200, ~45 KB;
# aynı anda /api/diagnostics 401 veriyordu). Docstring turunda rota açıklamaları 49'dan 73'e
# çıkınca bu yüzey iç mühendislik gerekçelerini — hangi korumanın neden zayıf olduğunu
# anlatan notlar dahil — dışarı yayınlar hâle geldi. Yani burada docstring YORUM DEĞİL,
# YAYINLANAN ÇIKTIDIR. Şema kapalı; pano kendi uçlarını zaten adıyla biliyor.
app = FastAPI(title="Meridian", docs_url=None, redoc_url=None, openapi_url=None, lifespan=_lifespan)


# ---- SERİLEŞTİRME SİGORTASI --------------------------------------------------------
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
        """Uç fonksiyonunu `store.sanitize` sarıcısıyla değiştirip rotayı O SARICIYLA kaydeder.

        Eş-yordam ve düz fonksiyon ayrı sarılır. `functools.wraps` `__wrapped__` kurduğu için
        FastAPI bağımlılıkları sarıcının ardındaki ORİJİNAL imzadan çözmeye devam eder."""
        if inspect.iscoroutinefunction(endpoint):
            @functools.wraps(endpoint)
            async def _sarili(*a, **k):
                """Eş-yordam ucu bekler, dönüşünü `store.sanitize`den geçirip verir."""
                return store.sanitize(await endpoint(*a, **k))
        else:
            @functools.wraps(endpoint)
            def _sarili(*a, **k):
                """Düz (senkron) ucu çağırır, dönüşünü `store.sanitize`den geçirip verir."""
                return store.sanitize(endpoint(*a, **k))
        # `functools.wraps` `__wrapped__` kurar; FastAPI bağımlılıkları `inspect.signature` ile
        # çözer ve o da `__wrapped__`i izler — yani `request: Request` gibi parametreler sarıcının
        # ardından ORİJİNAL imzadan çözülmeye devam eder (fastapi 0.139.0'da doğrulandı).
        super().__init__(path, _sarili, **kwargs)


# ROTA SINIFI İLK `@app.get`TEN ÖNCE ATANIR: `add_api_route` sınıfı KAYIT ANINDA okur, sonradan
# atamak daha önce kaydedilmiş rotaları kapsamaz (yani sigorta sessizce yarım takılırdı).
app.router.route_class = _NativeRoute

WEB = Path(__file__).resolve().parent / "web"

# ---- PANO TOKEN'I: systemd CREDENTIAL KANALI → ORTAM KANALI ---------
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


# ---- GÜVENLİK BAŞLIKLARI — UYGULAMA KATMANI --------------------------------
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
# `script-src 'self'` — GERÇEKTEN karşılanıyor (iki arıza kapatıldı: landing.html +
#   workflow.html satır içi `<script>` taşıyordu → landing.js/workflow.js'e alındı; app.js'te 34 +
#   index.html'de 6 = 40 satır içi olay özniteliği vardı → olay delegasyonuna çevrildi, `data-act`
#   KAYITLI izin listesinden çözülür). BU DİREKTİFE `'unsafe-inline'` GERİ EKLENMEZ; eklemek
#   zorunda kalındıysa bir yere satır içi işleyici geri gelmiş demektir ve çözüm eylemi kaydetmek.
#   Çivi: tests/test_web_csp_uyum.py.
# `style-src 'self' 'unsafe-inline'` — AYRI ve hâlâ AÇIK bir borç: app.js DOM'u satır içi stil
#   taşıyan şablon dizgileriyle üretiyor; kaldırmak app.js'in yeniden yazılması demek. Beyanlıdır,
#   gizlenmez.
# `font-src 'self'` — sertleştirme: `fonts.googleapis.com` ve `fonts.gstatic.com`
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
    # URL'lerde artık sır yok (`?token=` kaldırıldı) ama yol adları da bilgi taşır.
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
        """Sarılacak ASGI uygulamasını saklar (başka durum tutmaz)."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """HTTP isteklerinde `send`i sarar; HTTP dışı kapsamları (lifespan/websocket) aynen geçirir.

        Gövdeye HİÇ dokunmaz — yalnız `http.response.start` mesajının başlık listesi değişir."""
        if scope["type"] != "http":       # lifespan/websocket: başlık kavramı yok
            await self.app(scope, receive, send)
            return

        async def _send(mesaj):
            """Yanıt başlangıcında aynı adlı başlıkları atıp `GUVENLIK_BASLIKLARI`nı SET eder."""
            if mesaj["type"] == "http.response.start":
                mesaj["headers"] = [
                    (ad, deger) for ad, deger in mesaj["headers"] if ad.lower() not in _GB_ADLAR
                ] + _GB_BAYT
            await send(mesaj)

        await self.app(scope, receive, _send)


# CORS'tan SONRA eklenir → yığında ONDAN DIŞTA kalır (Starlette `add_middleware`i başa ekler ve
# listeyi ters kurar). Sonuç: CORS'un kendi kısa-devre yaptığı preflight yanıtları da başlığı alır.
app.add_middleware(GuvenlikBasliklariMiddleware)

# ÜÇÜNCÜ BİR MIDDLEWARE DAHA VAR ve bilerek BURADA DEĞİL: `KayanOturumMiddleware` (oturum çerezini
# kullanımla tazeler) kimlik uçlarının — `/api/login`, `/api/logout`, `/api/setup-password` —
# HEMEN YANINDA durur. Gerekçe orada yazılı: çerezi YAZAN dört yol (giriş · ilk kurulum · çıkış ·
# tazeleme) tek bir ekranda okunabilmeli, yoksa biri ötekinin başlığını sessizce ezer.


def _autostart():
    """When the operator opens the app locally (serve.sh sets the flags), bring the Hermes standby brain
    AND the paper-advance scheduler up automatically. Both off by default so tests/imports never spawn
    them. The scheduler is what keeps the local agent from freezing (stale heartbeat → Hermes idle)."""
    # EMEKLİ EDİLMEDİ — ÖLÜ DEĞİL (ölü-mekanizma avı adayı #çürütüldü).
    # AV İDDİASI: "MERIDIAN_SUPERVISED'ı kimse set etmiyor". ÇÜRÜTME: `ops/com.meridian.agent.plist`
    # satır 31 bu değişkeni `<string>1</string>` ile veriyor — yani Mac LaunchAgent altında koşan
    # her başlatma bu dalı GERÇEKTEN yürütür ve operatöre "süpervizör altında (yeniden) başladı"
    # bildirimi gider. Bu, süreç ölümünün operatöre ulaşan İKİ yolundan biri (öteki A1'deki
    # systemd OnFailure→fail-notify). Silinseydi sessizce kaybolan şey bir sarmalayıcı değil,
    # bir yeniden-başlatma HABERİ olurdu. OPERATÖR KALEMİ olarak belgelendi.
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
    `?token=` QUERY PARAMETRESİ KALDIRILDI: URL'ler sunucu loglarına, tarayıcı
    geçmişine ve `Referer` başlığına düşer. İndirme bağlantıları artık çerezle çalışıyor —
    tarayıcı onu kendiliğinden gönderir, URL'e sır koymaya gerek yok."""
    cerez = request.cookies.get(auth.COOKIE_NAME)
    if auth.verify_session(cerez):
        return
    if auth.password_set():
        # Parola kurulduysa oturum ZORUNLUDUR; başlık token'ı yalnız ek bir betik yoludur.
        if DASH_TOKEN and hmac.compare_digest(
                (request.headers.get("x-meridian-token") or "").encode("utf-8"),
                DASH_TOKEN.encode("utf-8")):
            return
        # OTURUM DÜŞÜŞÜ — YALNIZ ÇEREZ GELMİŞKEN (kayıt boşluğu). Ayrım kasıtlı:
        # çerezsiz bir 401 sıradan bir yetkisiz çağrıdır (bot taraması, açılıştaki `/api/session`),
        # ÇEREZLİ bir 401 ise bir oturumun DÜŞTÜĞÜ andır — operatörün "arayüz kayboldu" dediği
        # olay tam olarak budur ve bugüne dek hiçbir yere yazılmıyordu. İkisini aynı satırla
        # bassaydık defter gürültüden ibaret olur, gerçek düşüş orada kaybolurdu.
        # SEL KAPISI `auth.note_session_drop`ta: pano 15 sn'de bir yokluyor ve `rotate_key()`
        # sonrası tarayıcı ölü çerezi max-age dolana kadar göndermeye devam eder.
        # JETON GEÇMEZ — düşmüş bir çerez bile bir sırdır ve deftere yazılan sır, sızan sırdır.
        if cerez and auth.note_session_drop(_client_ip(request)):
            obs.warn("session_drop", ip=_client_ip(request), yol=request.url.path)
        raise HTTPException(status_code=401, detail="unauthorized")
    if not DASH_TOKEN:
        return
    supplied = request.headers.get("x-meridian-token") or ""
    # hmac.compare_digest: constant-time comparison so the token can't be recovered byte-by-byte via
    # response-timing (CWE-208). `!=` short-circuits on the first mismatching byte (L4).
    # BAYT KARŞILAŞTIRMASI: `compare_digest` ASCII-DIŞI bir
    # `str` görünce TypeError atar — 401 değil, 500. Sevkiyat şablonu tam da böyle bir token koyuyordu
    # (`DEĞİŞTİR-...`), yani operatör onu olduğu gibi bırakınca TÜM API çöküyordu. Yön güvenliydi
    # (kapalı, veri sızmaz) ama operatörü "token'ı kaldırayım" çözümüne itiyordu — ki o da
    # yetkisiz açık bir yüzeye düşürürdü. Baytlara çevirince karşılaştırma her kodlamada çalışır.
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


# `max-age=0` EKLENDİ: `no-cache` tek başına RFC 9111'e göre zaten
# "her kullanımdan önce doğrula" demektir, ama saha gerçeği bu değil — bazı ara katmanlar ve eski
# tarayıcılar `no-cache`i sezgisel tazelik hesabına girmeyen bir öneri gibi işler. `max-age=0` aynı
# şeyi ikinci kez, tartışmasız bir sayıyla söyler. Üçü birlikte: sakla, ama HER İSTEKTE doğrula.
_NOCACHE = {"Cache-Control": "no-cache, max-age=0, must-revalidate"}

# ---- STATİK VARLIK ÖNBELLEK SÖZLEŞMESİ -----------------------
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
    """`/` ucu: YENİ panoyu (`pano.html`) ETag/304 pazarlığıyla döndürür (salt-okuma).

    KÖK ÇEVRİLDİ (2026-08-25, operatör kararı: "yeni panoya geçelim"). Çevrimin önündeki
    tek engel kriz kollarıydı — HALT · Cancel-Open · Flatten · Halt-Learning yeni panonun
    ÜST BARINDA, çift adımlı onayla (`ui/src/pano/kabuk/KrizKollari.tsx`). Acil bir anda
    operatörün kas hafızasının gittiği yerde kolun bulunması, çevrimin ön şartıydı.

    ESKİ PANO SİLİNMEDİ, ADRESİ DEĞİŞTİ → `/eski`. Gövdesi (`app.js`, 12.600 satır) hâlâ
    bazı yolların TEK kaynağı; öksüz bırakmak, diskte tutup ulaşılamaz kılmak olurdu ve o
    hata bu turda `pilot-workflow.html`de bir kez yaşandı (rotası yoktu, dağıtıma biniyordu).
    Çivi: tests/test_kok_cevrimi_v298.py"""
    return _statik(request, "pano.html")


@app.get("/eski", response_class=HTMLResponse)
def eski_pano(request: Request):
    """`/eski` ucu: ÖNCEKİ pano kabuğu (`index.html`). Yetki `/` ile AYNI (yok) — kabuk bir
    sır taşımaz, açılışta `/api/session`ı sorar ve giriş ekranını mı uygulamayı mı çizeceğine
    ona göre karar verir.

    NEDEN DURUYOR: göç bitmedi. Yeni panoda henüz karşılığı olmayan yollar var (ajana mesaj
    ucu yok, belge arşivinin sunum ucu yok, oturum ömrü `/api/session`da dönmüyor) ve bu
    bölümlerin gövdesi yalnız burada. Emeklilik, o boşluklar kapandığında ve kendi turunda."""
    return _statik(request, "index.html")


@app.get("/app.js")
def appjs(request: Request):
    """`/app.js` ucu: pano uygulama betiğini ETag/304 pazarlığıyla döndürür (salt-okuma)."""
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
    """`/theme.js` ucu: tema betiğini ETag/304 pazarlığıyla döndürür (salt-okuma)."""
    return _statik(request, "theme.js", "application/javascript")


@app.get("/landing.js")
def landingjs(request: Request):
    """`/landing.js` ucu: karşılama sayfasının betiğini ETag/304 ile döndürür (salt-okuma)."""
    return _statik(request, "landing.js", "application/javascript")


@app.get("/workflow.js")
def workflowjs(request: Request):
    """`/workflow.js` ucu: iş akışı diyagramını üreten betiği ETag/304 ile döndürür (salt-okuma)."""
    return _statik(request, "workflow.js", "application/javascript")


# ⌘K komut paleti. Yol AD AD yazılmak ZORUNDA (yukarıdaki not: StaticFiles montajı yok) —
# index.html'e script etiketini eklemek TEK BAŞINA yetmez, bu satır olmadan üretimde 404
# döner ve palet sessizce hiç var olmaz.
@app.get("/palette.js")
def palettejs(request: Request):
    """`/palette.js` ucu: ⌘K komut paleti betiğini ETag/304 ile döndürür (salt-okuma)."""
    return _statik(request, "palette.js", "application/javascript")


# ---- YENİ PANO (studio-admin göçü, 2026-08-25) ------------------------------
# ÜÇ ROTA: sayfa, tercih önyükleyicisi, derleme varlıkları. Eski panonun rotaları
# (`/`, `/app.js`, `/palette.js`, …) YERİNDE DURUYOR — göç bitene kadar iki pano yan
# yana yaşıyor ve canlı olan hâlâ eskisi.
#
# NEDEN MONTAJ DEĞİL (yukarıdaki notun devamı): Vite'ın çıktı adları içerik-hash'li
# (`pano-C2lINJAW.js`), yani kaynağa LİTERAL yazılamazlar — her derlemede değişirler.
# `StaticFiles` montajı bu ikilemin kolay cevabı olurdu ama aynı bedeli getirirdi:
# dizine düşen HER bayt yayına açılır. Bunun yerine SUNULAN AD KÜMESİ DERLEMENİN
# KENDİ BEYANINDAN okunuyor — `pano-assets/manifest.json`, Vite'ın ürettiği manifest.
# Manifestte olmayan hiçbir ad 200 alamaz; dizine elle bırakılmış bir dosya da,
# eski bir derlemenin artığı da. Bu, "montaj yok" sözleşmesini bozmadan hash'li
# adları sunmanın tek dürüst yolu.
#
# MANİFEST YOKSA HİÇBİR VARLIK SUNULMAZ ve 404 bunu ADIYLA söyler: "derleme koşmamış".
# Boş küme dönmek sessizce yarım bir sayfa açardı — kabuk gelir, uygulama hiç gelmez.
_PANO_MANIFEST = WEB / "pano-assets" / "manifest.json"


def _pano_varliklari() -> frozenset[str]:
    """Manifestin BEYAN ETTİĞİ varlık adları (`pano-assets/...` göreli yollar).

    HER İSTEKTE OKUNUR, import anında ÖNBELLEĞE ALINMAZ: dağıtım (`dagit.sh`) dosyaları
    rsync'ler ve servisi yeniden başlatmayabilir. Import anında donmuş bir küme, yeni
    derlemenin varlıklarını 404'lerdi — sayfa açılır, uygulama hiç yüklenmez, ve hata
    tarayıcı konsolunda kalırdı. Manifest 200 baytlık bir dosya; okuma maliyeti ihmal
    edilebilir, bayatlama maliyeti bir gecelik ölü panodur."""
    try:
        ham = json.loads(_PANO_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # sessiz-yutma: manifest yoksa/bozuksa BOŞ küme döner ve çağıran dürüst bir 404 yazar; tek eksik derleme artefaktını 500'e çevirmek teşhisi zorlaştırır, sonucu değiştirmez
        # sessiz-yutma İŞARETLİ (YASA 4): manifest yoksa ya da bozuksa BOŞ küme döner ve
        # çağıran taraf dürüst bir 404 yazar. Burada istisna fırlatmak, tek bir eksik
        # derleme artefaktını 500'e çevirirdi — teşhisi zorlaştırır, sonucu değiştirmez.
        return frozenset()
    adlar: set[str] = set()
    for girdi in ham.values():
        if not isinstance(girdi, dict):
            continue
        dosya = girdi.get("file")
        if isinstance(dosya, str):
            adlar.add(dosya)
        for css in girdi.get("css") or ():
            if isinstance(css, str):
                adlar.add(css)
    return frozenset(adlar)


@app.get("/pano", response_class=HTMLResponse)
def pano(request: Request):
    """`/pano` ucu: yeni pano kabuğu `pano.html`i ETag/304 pazarlığıyla döndürür.

    YETKİ `/` İLE AYNI (yani burada `_auth` YOK) ve bu bilinçli: kabuk kendisi bir sır
    taşımaz, açılır açılmaz `/api/session`ı sorar ve cevaba göre giriş ekranını mı
    uygulamayı mı çizeceğine karar verir. Kabuğu yetkiye bağlamak, giriş ekranını da
    yetkiye bağlamak olurdu — kapalı bir kapıya girmenin yolu kapının kendisi olamaz."""
    return _statik(request, "pano.html")


@app.get("/pano-onyuk.js")
def pano_onyuk(request: Request):
    """`/pano-onyuk.js` ucu: tercih önyükleyicisini ETag/304 ile döndürür (salt-okuma).

    AD AD YAZILMAK ZORUNDA — `theme.js`/`palette.js` ile aynı sebep: montaj yok. Bu satır
    olmadan `pano.html`deki `<script src>` üretimde 404 döner ve pano YANLIŞ TEMADA,
    sessizce açılır (hata yok, yanlış sonuç var)."""
    return _statik(request, "pano-onyuk.js", "application/javascript")


@app.get("/pano-assets/{ad}")
def pano_varlik(request: Request, ad: str):
    """Derlenmiş pano varlıkları. YALNIZ manifestin beyan ettiği adlar; başka her şey 404."""
    yol = f"pano-assets/{ad}"
    if yol not in _pano_varliklari():
        # `_statik`in 404'üyle AYNI dili konuşur ama AYNI CÜMLEYİ kurmaz: orada teşhis
        # "dağıtım eksik", burada "bu ad derlemenin beyanında YOK" — istenen dosya diskte
        # olsa bile sunulmaz. İkisini aynı metne bağlamak operatörü yanlış yere (rsync'e)
        # bakmaya gönderirdi; doğru yer derlemenin kendisidir.
        return JSONResponse({"error": "not_found", "path": yol,
                             "detail": "pano derleme manifestinde YOK — `cd ui && npm run build` "
                                       "koşmamış ya da manifest eski"},
                            status_code=404, headers=_NOCACHE)
    tur = ("application/javascript" if ad.endswith(".js")
           else "text/css" if ad.endswith(".css")
           else "application/json" if ad.endswith(".json")
           else None)
    return _statik(request, yol, tur)


# ---- YAZI TİPİ SUNUMU -------------------------------------------------------
# VAKA: bir önceki tur Recursive'i kendi-barındırmaya aldı — `meridian/web/fonts/` altına iki `.woff2`,
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
# 2026-08-24 · KARMA DEVRALMA (docs/HUKUM-2026-08-24-YAZITIPI.md): `--sans` Inter oldu,
# `--mono` Recursive KALDI. Ölçüm iki yönlüydü ve iki yönü de alındı: sans'ta Inter kazandı
# (1/l @28px 0,968 vs 0,931), mono'da Recursive kazandı (0,817 vs Geist 0,570). Recursive Sans
# LİSTEDEN DÜŞMEDİ ve bu bilinçli: dört yüzeyin dağıtımı atomik değil (rsync sırası), yani
# yeni HTML eski font dosyasını isteyebilir ya da tersi. Aradaki pencerede 404 dönmek sayfayı
# sistem yüzüne düşürürdü. Emeklilik ayrı bir turda, dağıtım oturduktan SONRA.
_FONT_DOSYALARI = frozenset({"inter-vf.woff2",
                             "recursive-sans-vf.woff2",   # emekli ama SUNULUYOR (yukarı bkz.)
                             "recursive-mono-vf.woff2"})


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


# MARKA İŞARETİ — `/favicon.svg` (2026-08-26). Beş HTML yüzeyin HİÇBİRİNDE favicon YOKTU:
# ne `<link rel="icon">`, ne dosya. Beşi de sekmede boş sayfa ikonuyla duruyordu.
# ROTA AD AD YAZILIR, `StaticFiles` MONTAJI YOK — `_FONT_DOSYALARI` üstündeki montaj-yasağı hükmü burada da
# geçerli. Ve v202 dersi birebir tekrar etmesin diye rota dosyayla AYNI turda açılıyor:
# `@font-face` yolu tek başına bir VAAT'tir, dosyanın diskte olması da öyle; SUNULAN ŞEY ROTADIR.
# Orada dosyalar aylarca diskteydi ve üç yüzey 404 alıyordu.
# `{ad}` PARAMETRESİ YOK, tek literal yol: parametre olsaydı dizin-dışı erişim bir FİLTRE işi
# olurdu; tek yolda o yüzey hiç doğmuyor.
# MIME AÇIK YAZILIR: `_statik` uzantıdan tahmin etmez ve `image/svg+xml` olmadan tarayıcı
# ikonu sessizce yok sayar — "dosya 200 dönüyor ama sekme hâlâ boş" sınıfı.
@app.get("/favicon.svg")
def favicon(request: Request):
    """Meridian marka işareti (C · M Monogramı v0). Yetkisiz — sekme ikonu herkese açıktır.

    Karanlık/aydınlık ayrımı DOSYANIN İÇİNDEDİR (`prefers-color-scheme`): favicon ayrı bir
    belge olarak yüklenir ve sayfanın rengini miras alamaz. Çivi: tests/test_favicon_v320.py."""
    return _statik(request, "favicon.svg", "image/svg+xml")


@app.get("/landing", response_class=HTMLResponse)
def landing(request: Request):
    """The original marketing landing page — the design reference the dashboard is cut from.

    ÖNBELLEK NOTU: bu rota ve `/workflow` `_NOCACHE`i HİÇ göndermiyordu — yani
    tanıtım sayfası, panonun aksine, tarayıcının sezgisel tazelik hesabına bırakılmıştı. Bekçinin
    canlı-sayı sözleşmesi (landing.js → /api/public/summary) tam da bu sayfada geçerli
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
    # ---- TOHUM/CANLI AYRIMI ----------------------------------------------------
    # Bu özet 96 "kapanmış işlem" diyordu ve landing onu manşete taşıyordu; oysa gövdesi replay
    # TOHUMU (training, survivorship'li) ve GERÇEK canlı yalnız 1 işlem. Ayrım defterin KAYNAK
    # DAMGASINDAN okunur (ledgerstamp — learning_scorecard'ın da paydası, panonun "gerçek canlıyı
    # göster, defter toplamını DEĞİL" doktriniyle aynı; v191 test_gerceklesmis_KZ_karti). Sabit sayı
    # YAZILMAZ. $ P&L dışarı verilmez (uç sözleşmesi); canlı sonuç R-multiple olarak taşınır —
    # `matrix`in ve `score`un zaten kamuya açtığı araştırma metriğiyle aynı sınıf, hesap verisi değil.
    from . import ledgerstamp as _ls
    _defter = _ls.counts(trades)
    _live_rows = _ls.split(trades)[_ls.LIVE_PAPER]
    _live_rs = [float(t["r_multiple"]) for t in _live_rows if t.get("r_multiple") is not None]
    _live_sum_r = round(sum(_live_rs), 4) if _live_rs else None
    _live_mean_r = round(sum(_live_rs) / len(_live_rs), 4) if _live_rs else None
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
        # Ham toplam GERİYE UYUM için kalır (matrix paydası da bu) AMA artık tek
        # başına DURMAZ — tohum/canlı ayrımı ve payda beyanı yanında. Halka açık yüzey yanıltmasın.
        "closed_trades": len(trades),
        "closed_trades_live": _defter["live_paper_n"],
        "closed_trades_seed": _defter["replay_seed_n"],
        "closed_trades_belirsiz": _defter["belirsiz_n"],
        "closed_trades_kapsam": _defter["kapsam"],
        "live": {"n": _defter["live_paper_n"], "sum_r": _live_sum_r, "mean_r": _live_mean_r,
                 "note": ("canlı kâğıt döngünün kapattığı işlem; R-multiple (riske göre getiri), "
                          "$ P&L uç sözleşmesi gereği dışarı verilmez")},
        "seed": {"n": _defter["replay_seed_n"],
                 "note": "replay tohumu (training, survivorship'li) — canlı kanıt SAYILMAZ"},
        "score": hb.get("score"),
        "score_kapsam": ("başarı notu (score) state/heartbeat'ten gelen strateji kompozitidir; "
                         "closed_trades TOHUM DAHİL ham toplamdır — canlı kanıt için "
                         "closed_trades_live'a bakılır"),
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


# ---- RUNBOOK YÜZEYİ -------------------------------------------------
# Zincir "alarm → teşhis → runbook → çözüm" son halkasızdı: pano alarm satırları ve sessiz-hat
# sapmaları bir hedef gösteremiyordu. Hedef artık `docs/RUNBOOK.md` ve OKUYUCUSU bu
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
        """Açık kalmış `<ul>` katmanlarını (iç içe olanlar dahil) gövdeye kapatır."""
        nonlocal liste_derinlik
        while liste_derinlik > 0:
            govde.append("</ul>")
            liste_derinlik -= 1

    def _alinti_kapat():
        """Biriken alıntı satırlarını tek bir `<blockquote>` olarak gövdeye yazar ve tamponu boşaltır."""
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


# HEAD AYRI BİR DEKORATÖRLE KAYDEDİLİR (2026-08-25, ölçülmüş kusur): pano belge rafı bu yüzeyi
# HEAD ile yokluyor — 184 KB'lık bir sayfayı indirmeden "kapı açık mı" diye sormak DOĞRU olandır.
# Ama `@app.get` FastAPI'de YALNIZ GET kaydeder (Starlette'in düz `Route`u HEAD'i kendiliğinden
# ekler, `APIRoute` EKLEMEZ) ve yoklama canlıda 405 alıyordu: rafta belge yerinde dururken satır
# kırmızı yanıyordu. Yani panel doğru soruyu soruyor, rota cevap veremiyordu.
#
# NEDEN İKİ DEKORATÖR, `api_route(methods=["GET","HEAD"])` DEĞİL: yetki denetimi
# (`test_api_audit_v21::test_p1c`) rotaları KAYNAK METİNDEN, `@app.get("...")` deseniyle sayar.
# Tek rotaya çevirmek `/runbook`u o envanterden düşürürdü — yarın `_auth` satırı silinse denetim
# artık ötmezdi. HEAD dekoratörü GET'in ÜSTÜNE konur ki kaynak bloğu bölünürken gövde (ve içindeki
# `_auth`) GET kaydının yanında kalsın; bu sıra bir stil tercihi değil, o denetimin çalışma şartı.
@app.head("/runbook", response_class=HTMLResponse)
@app.get("/runbook", response_class=HTMLResponse)
def runbook(request: Request):
    """`docs/RUNBOOK.md`'nin okunur yüzeyi — alarm satırlarının ve sessiz-hat sapmalarının hedefi.

    EKSİK KAYNAK SESSİZ GEÇMEZ. Belge yoksa ya da kabuk yer tutucularını kaybettiyse sayfa BOŞ
    dönmez: ne olduğunu ve nasıl düzeltileceğini (`python ops/runbook_uret.py`) söyleyen bir
    hata döner. Boş bir runbook, olay anında en kötü yalandır — "bakacak bir şey yok" der.

    HEAD AYNI KAPIDAN GEÇER, AYNI DURUMU DÖNER: `_auth` önce çağrılır (yetkisiz bir HEAD'in 200
    dönmesi, sistemin iç haritasının orada durduğunu yetkisiz çağırana doğrulamak olurdu) ve iki
    hata yolu da (yer tutucu kaybı 500 · belge yok 503) HEAD'de aynen işler. Tek fark GÖVDEDİR:
    markdown HEAD'de HİÇ render EDİLMEZ — yoklamanın tüm anlamı o hesabı ödememektir. Bu yüzden
    `Content-Length` 0'dır, GET'in uzunluğu değil; RFC 9110 içerik üretilirken belirlenen
    başlıkların HEAD yanıtında atlanmasına izin verir."""
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
    if request.method == "HEAD":
        # Durum SORULARININ tamamı yukarıda cevaplandı; geriye yalnız gövde kalıyordu ve yoklayan
        # onu istemiyor. Erken dönüş buradan ÖNCEYE alınamaz: alınsaydı HEAD "açık" derken GET
        # 503 verirdi ve raf, üretilmemiş bir belgeyi yeşil gösterirdi.
        return HTMLResponse("", headers=_NOCACHE)
    govde, toc = _md_render(RUNBOOK_MD.read_text(encoding="utf-8"))
    sayfa = kabuk.replace(_RUNBOOK_YER_TUTUCU[0], govde).replace(_RUNBOOK_YER_TUTUCU[1], toc)
    return HTMLResponse(sayfa, headers=_NOCACHE)


# ---------- liveness / metrics (no auth — used by health checks & scrapers) ----------
# ---- KİMLİK: giriş / çıkış / oturum yoklama / ilk kurulum -----------------------
# Aşağıdaki DÖRT uç `_auth` ÇAĞIRMAZ ve çağırmamalıdır — kimlik doğrulamanın kendisi buradan
# geçer. Kapalı bir kapıya girmenin yolu kapının kendisi olamaz.
#
# LİSTE NEDEN ÜRETİM KODUNDA: yetki denetimi testleri (test_api_audit_v21::test_p1,
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


def _oturum_cerez_basligi(tok: str, max_age: int, secure: bool) -> str:
    """Oturum çerezinin `Set-Cookie` başlığı — ÇEREZİ YAZAN HERKESİN TEK KAYNAĞI.

    NEDEN FONKSİYON, ÜÇ KEZ `set_cookie(...)` DEĞİL: öznitelikler (HttpOnly · SameSite=Strict ·
    Secure · path) bir GÜVENLİK DURUŞUDUR ve test_kimlik_v114 onları YALNIZ `/api/login`in
    yanıtında ölçüyor. Üç ayrı çağrı yeri, üç ayrı sürüklenme yolu demektir: tazeleyicinin
    `HttpOnly`ı düşmesi hiçbir yerde kırmızıya dönmez ama tek bir XSS'i kalıcı erişime çevirirdi.
    Kaynak tek olduğunda o ölçüm üçünü birden çiviler.

    NEDEN ÖZNİTELİKLERİ ELLE KURMUYOR: biçimlendirmeyi Starlette'in kendi `set_cookie`i yapsın —
    kaçış kuralları ve `SameSite` yazımı çerçevenin sözleşmesidir, bizim taklidimiz değil.
    Tek kullanımlık bir `Response` yalnız başlığı ÜRETMEK için kurulur; hiçbir yere gönderilmez."""
    tasiyici = Response()
    tasiyici.set_cookie(auth.COOKIE_NAME, tok, max_age=max_age,
                        httponly=True, samesite="strict", secure=secure, path="/")
    return tasiyici.headers["set-cookie"]


def _oturum_cerezi_yazilmis(basliklar) -> bool:
    """Yanıt oturum çerezini ZATEN yazıyor mu? (ham ASGI başlık listesi üzerinde)"""
    onek = (auth.COOKIE_NAME + "=").encode("latin-1")
    return any(ad.lower() == b"set-cookie" and deger.lstrip().startswith(onek)
               for ad, deger in basliklar)


# ---- session_refresh SEL KESİMİ (2026-08-23 canlı pano ihlal triyajı) --------------------------
# ÖLÇÜLEN SEL: canlıda 127.0.0.1'den gelen çerezli yoklayıcı (repo-içi iz: deploy/cutover.sh +
# deploy.sh'ın önerdiği `ssh -L 8080:127.0.0.1:8080` tüneli üzerinden açık pano sekmesi — tünelde
# XFF yoktur, istemci 127.0.0.1 görünür; pano 15 sn'de bir birden çok ucu anketler) saatte ~420
# `session_refresh` olayı bastırıyordu. Olay defteri gelen kutusunun ve TÜM makullük
# dedektörlerinin okuduğu kaynaktır — sel, sinyali gömer (notify_suppressed'in pencere-başına-tek-
# satır dersiyle aynı sınıf). KESİM ÖRNEKLEMEDİR, SANSÜR DEĞİL: aynı (ip, yol) çifti için en fazla
# ~5 dk'da BİR olay yazılır; aradakiler sayaçta birikir ve bir SONRAKİ örneklem olayına
# `atlanan_n` alanıyla girer — bilgi kaybı yok (toplam = satır sayısı + Σ atlanan_n), sel yok.
REFRESH_ORNEKLEM_S = 300.0
_REFRESH_SON: dict[tuple[str, str], list] = {}   # (ip, yol) → [son_kayit_monotonic, atlanan_n]
_REFRESH_TAVAN = 4096                            # bellek tavanı: en eski kayıt düşer (aşağıda)


def _session_refresh_ornekle(ip: str, yol: str, now: float | None = None) -> int | None:
    """Bu tazeleme olayı LOGLANMALI MI? None → pencere içinde, sayaç birikti (yazma);
    int → yaz, dönen değer bu örneklemin kapsadığı ATLANAN olay sayısıdır (0 dahil — ölçülmüş sıfır).

    Saat `time.monotonic`tir (duvar saati geri alınırsa pencere şişmez). Sözlük (ip, yol) başına
    TEK girdi tutar; `_REFRESH_TAVAN` aşılırsa en eski girdi düşer — düşen girdinin biriken sayacı
    bir olay olarak DEĞİL, yeni penceresinin ilk örnekleminde 0'dan sayılır (tavan ancak binlerce
    ayrık (ip, yol) çiftiyle aşılır; pano yoklayıcısı tek çifttir)."""
    import time as _t
    now = _t.monotonic() if now is None else now
    k = (str(ip), str(yol))
    rec = _REFRESH_SON.get(k)
    if rec is None:
        if len(_REFRESH_SON) >= _REFRESH_TAVAN:
            _REFRESH_SON.pop(min(_REFRESH_SON, key=lambda x: _REFRESH_SON[x][0]), None)
        _REFRESH_SON[k] = [now, 0]
        return 0
    if now - rec[0] >= REFRESH_ORNEKLEM_S:
        atlanan, rec[0], rec[1] = rec[1], now, 0
        return atlanan
    rec[1] += 1
    return None


class KayanOturumMiddleware:
    """KAYAN OTURUM — yetkili istek geldikçe çerezi tazeler.

    ARIZA (operatör bildirdi): "arayüz bir süre sonra kayboluyor, bütün sekmeler için geçerli".
    Kök neden bir çizim hatası değildi: `SESSION_TTL_S` SABİT bir pencereydi ve çerezi yenileyen
    hiçbir yol yoktu. 12 saat dolduğunda `_auth` 401 verir, `app.js`in `_yetkisizYakala`sı kapağı
    açar; çerez sekmeler arasında ORTAK olduğu için hepsi AYNI ANDA düşer ve pano 15 saniyede bir
    yokladığı için düşüş saniyeler içinde görünür. Tarif birebir buydu.

    NEDEN MIDDLEWARE, `_auth` İÇİNDE DEĞİL: `_auth` yaklaşık 80 uçta çağrılır ve `Request`ten
    başka bir şey görmez — `Response`a erişimi YOKTUR. Çerezi oradan yazmak için seksen imzayı
    değiştirmek gerekirdi ve her yeni uç, imzayı unutabilecek yeni bir yer olurdu. Tazeleme bir
    UÇ meselesi değil BAĞLANTI meselesidir; yeri taşıma katmanıdır.

    NEDEN SAF ASGI, `@app.middleware("http")` DEĞİL: `GuvenlikBasliklariMiddleware`in gerekçesinin
    AYNISI — BaseHTTPMiddleware yanıtı `StreamingResponse`a sarar ve bu dosyanın statik yolu
    `FileResponse` + gövdesiz 304 üzerine kuruludur. Burada da yalnız `http.response.start`
    mesajının BAŞLIK LİSTESİNE bir satır EKLENİR, gövdeye hiç dokunulmaz.

    ZATEN ÇEREZ YAZAN YANITA DOKUNULMAZ — ve bu kural bir zarafet değil, bir HATA KAPISIDIR:
    `/api/logout` çerezi SİLER (`delete_cookie`). Bu middleware yığının EN DIŞINDA olduğu için
    onun başlığından SONRA yazardı; tarayıcı aynı ada iki `Set-Cookie` görünce SONUNCUYU uygular,
    yani çıkış SESSİZCE çalışmaz olurdu. Aynı tuzak `/api/login` ve `/api/setup-password` için de
    geçerli (taze çerezin üstüne eski oturumun tazelenmişini yazmak). Yol ADI listelemek yerine
    OLGUYA bakılır — "yanıt bu çerezi zaten yazıyor mu" — çünkü yol listesi zamanla sürüklenir,
    olgu sürüklenmez.

    ÖLÇÜLEN MALİYET — İDDİA DEĞİL, SAYI (bu makinede sayaçla): maliyet birimi
    `auth._read()`tir (imza anahtarı `state/auth.json`dan gelir) ve tek okuma **19,4 µs**.
      * çerezsiz istek           → **0** ek okuma (middleware çerez yokken hiç dallanmaz)
      * çerezli, yarı-ömür içi   → **+1** (1 → 2). `refresh_session` imzayı ÖNCE doğrular; imzadan
                                   önce `exp`/`iat` okumak doğrulanmamış veriye dayanarak
                                   dallanmak olurdu ve auth.py'nin yazılı sıra kuralını bozardı.
      * çerezli, tazeleme anı    → **+2** (1 → 3; ikincisi yeni jetonu imzalamak için) — oturum
                                   başına ~6 saatte BİR kez.
    Sayılar `test_kayan_oturum_v245.py::test_tazeleyicinin_disk_maliyeti_OLCULDU`de çivilidir;
    biri artarsa test söyler, yorum sessizce eskimez."""

    def __init__(self, app):
        """Sarılacak ASGI uygulamasını saklar (başka durum tutmaz)."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Çerezli HTTP isteklerinde oturumu tazeleyip yanıta yeni `set-cookie` iliştirir.

        Çerezsiz istek ve HTTP dışı kapsamlar hiç dallanmadan geçer — o yolda tek bir disk
        okuması bile yapılmaz. Tazeleme yalnız `auth.refresh_session` bir jeton döndürürse olur."""
        if scope["type"] != "http":       # lifespan/websocket: çerez kavramı yok
            await self.app(scope, receive, send)
            return
        istek = Request(scope)
        tok = istek.cookies.get(auth.COOKIE_NAME)
        if not tok:                        # çerezsiz istek: tek bir disk okuması bile yapılmaz
            await self.app(scope, receive, send)
            return
        tazelenmis = auth.refresh_session(tok)
        if tazelenmis is None:             # düşmüş · yarı-ömrü geçmemiş · tavana varmış · ESKİ biçim
            await self.app(scope, receive, send)
            return
        yeni_tok, kalan = tazelenmis
        baslik = _oturum_cerez_basligi(yeni_tok, kalan, _secure_cookie(istek)).encode("latin-1")
        ip = _client_ip(istek)
        yazildi = False

        async def _send(mesaj):
            """Yanıt başlığına tazelenmiş oturum çerezini ekler (uç zaten yazmışsa dokunmaz).

            Yalnız İLK `http.response.start` mesajında iş görür; çerez gönderildikten SONRA
            `session_refresh` kaydını düşer (kayıt arızası tazelemeyi geri almasın diye)."""
            nonlocal yazildi
            if mesaj["type"] != "http.response.start" or yazildi:
                await send(mesaj)
                return
            yazildi = True
            yazilacak = not _oturum_cerezi_yazilmis(mesaj["headers"])
            if yazilacak:
                mesaj["headers"] = list(mesaj["headers"]) + [(b"set-cookie", baslik)]
            await send(mesaj)
            # KAYIT GÖNDERİMDEN SONRA — sıra bilinçli: taşıyan şey çerezdir, kayıt onun yanındaki
            # ikinci iştir. `obs` yazımı (stdout + jsonl) patlarsa bu sırada operatörün oturumu
            # ZATEN tazelenmiş olur; önce yazsaydık bir kayıt arızası, düzeltmeye çalıştığımız
            # arızanın ta kendisini (oturum düşmesi) geri getirebilirdi.
            # PAROLA DA JETON DA GEÇMEZ — yalnız kim/nereye/ne kadar kaldı.
            # SEL KESİMİ: aynı (ip, yol) çifti ~5 dk'da bir yazılır; aradakiler `atlanan_n`
            # sayacında taşınır (gerekçe `_session_refresh_ornekle` üstündeki blokta). Tazelemenin
            # KENDİSİ örneklenmez — çerez her istekte yenilenir; yalnız KAYDI seyreltilir.
            if yazilacak:
                _yol = scope.get("path", "")
                _atlanan = _session_refresh_ornekle(ip, _yol)
                if _atlanan is not None:
                    obs.log("session_refresh", ip=ip, kalan_s=kalan, yol=_yol,
                            atlanan_n=_atlanan, orneklem_s=int(REFRESH_ORNEKLEM_S))

        await self.app(scope, receive, _send)


# EN SON EKLENİR → yığının EN DIŞINDA kalır. Bilinçli: `GuvenlikBasliklariMiddleware` yanıt
# başlıklarını kendi adlarıyla SET eder (`set-cookie` o listede yok, yani çerez ondan zarar
# görmez), ama en dışta durmak tazeleyicinin gördüğü başlık listesinin NİHAİ liste olmasını
# garanti eder — "yanıt çerezi zaten yazıyor mu" sorusunun doğru cevaplanması buna bağlıdır.
app.add_middleware(KayanOturumMiddleware)


@app.post("/api/login")
def api_login(request: Request, body: dict):
    """Parolayı doğrula, imzalı oturum çerezi ver.

    ZAMANLAMA: parola kurulu değilse de scrypt çalıştırılmaz ama yanıt aynı 401'dir — kurulum
    durumu `GET /api/session` üzerinden ZATEN açıkça bildiriliyor, dolayısıyla burada gizlemeye
    çalışmak sahte bir mahremiyet olurdu."""
    ip = _client_ip(request)
    if auth.locked_out(ip):
        # KİLİT DE BİR OLAYDIR: `login_failed` sekiz kez yazılır, sonra kilit devreye
        # girer ve o andan sonra HİÇBİR SATIR düşmezdi — yani defteri okuyan kişi saldırının tam
        # DEVAM ETTİĞİ pencerede sessizlik görürdü. En çok kayda değer dal, en sessiz olanıydı.
        obs.warn("login_locked_out", ip=ip, retry_after_s=auth.retry_after_s(ip))
        raise HTTPException(status_code=429, detail=f"cok fazla deneme — {auth.retry_after_s(ip)} sn sonra")
    pw = (body or {}).get("password") or ""
    if not auth.password_set() or not auth.verify_password(pw):
        auth.note_failure(ip)
        obs.warn("login_failed", detail=f"ip={ip}")
        raise HTTPException(status_code=401, detail="parola hatalı")
    auth.note_success(ip)
    # BAŞARILI GİRİŞ KAYDEDİLİR (kayıt boşluğu): bu yüzey bir broker hesabına bakıyor ve HALT/
    # Flatten taşıyor, ama "kim ne zaman girdi" sorusunun cevabı HİÇBİR YERDE yoktu — yalnız
    # başarısız giriş ve ilk parola kurulumu olay basıyordu. Başarısızı kaydedip başarılıyı
    # kaydetmemek, defteri tam da işe yarayacağı soruda kör bırakır: bir sızıntıdan sonra sorulan
    # şey "kaç kez yanlış denendi" değil, "başka biri İÇERİ GİRDİ Mİ"dir.
    # PAROLA VE JETON ASLA GEÇMEZ — kayıt yalnız kimliği DOĞRULANMIŞ olgunun kendisidir.
    obs.log("login_ok", ip=ip, ttl_s=auth.SESSION_TTL_S)
    tok = auth.issue_session()
    r = JSONResponse({"ok": True, "expires_in": auth.SESSION_TTL_S})
    r.headers.append("set-cookie",
                     _oturum_cerez_basligi(tok, auth.SESSION_TTL_S, _secure_cookie(request)))
    return r


@app.post("/api/logout")
def api_logout(request: Request):
    """`POST /api/logout`: oturum çerezini siler ve `{"ok": true}` döner.

    Yetki İSTEMEZ (zaten düşmüş bir oturumun da kapatılabilmesi için); sunucu tarafında
    hiçbir duruma yazmaz, tek yan etkisi çerezin silinmesidir."""
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
    r.headers.append("set-cookie",
                     _oturum_cerez_basligi(tok, auth.SESSION_TTL_S, _secure_cookie(request)))
    return r


@app.get("/healthz")
def healthz():
    """`GET /healthz`: yetkisiz sağlık ucu — kalp atışı yaşı, HALT, mod ve son bar.

    Salt-okuma. Kalp atışı bayatsa HTTP 503 (`status: "stale"`), değilse 200 döner —
    dış izleyicinin (systemd/uptime) sonda olarak kullandığı sözleşme budur."""
    hb = store.read_json("heartbeat.json", {})
    age = health.heartbeat_age_seconds()
    stale = health.stale()
    body = {"status": "stale" if stale else "ok", "heartbeat_age_seconds": age,
            "halted": health.halted(), "mode": config.MODE, "last_bar": hb.get("last_bar")}
    return JSONResponse(body, status_code=200 if not stale else 503)


def _local_request(request: Request) -> bool:
    """İstek bu makineden mi geliyor? Tünel/uzak istekler için hassas ölçütler
    kısılır — panik sayfası tünelden açılabildiği için /metrics de dışarı bakabilir."""
    try:
        return (request.client.host if request.client else "") in ("127.0.0.1", "::1", "localhost")
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        return False


@app.get("/metrics", response_class=PlainTextResponse)
def metrics(request: Request):
    """Prometheus text exposition — zero dependencies. Scrape-friendly liveness + book state.

    GİZLİLİK SINIRI: bu uç YETKİSİZDİ ve öz sermaye, günlük P&L, açık
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
        """Tek bir Prometheus gauge bloğu (HELP+TYPE+değer) üretir; None→0, bool→1/0 çevrilir."""
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
    """Hermes/LLM harcama özetini döndürür; `spend` modülünü gecikmeli (fonksiyon içi) içe alır."""
    from . import spend
    return spend.summary()


# ---- YETİM GET UÇLARI: EMEKLİ AMA CANLI ------------------------------------
# Aşağıdaki dört uç panodan, ops'tan ve skill'lerden HİÇ çağrılmıyor (tek tur atan yer parite
# testi — o da tüketim değil). Verileri BAŞKA bir uçtan zaten akıyor, yani "servis ediliyor"
# yanılsaması bir kopya yüzey daha yaratıyordu:
#   /api/spend      → /api/hermes `spend` (+ /api/diagnostics mlops)
#   /api/selfreview → /api/diagnostics `selfreview_summary`
#   /api/scheduler  → /api/hermes `scheduler` (+ /api/diagnostics `scheduler`)
#   /api/sprint     → /api/hermes `sprint`
#   /api/pipeline_runs → /api/skills `recent_runs`
#
# NEDEN SİLİNMEDİ (geri alınabilirlik, operatör kuralı): bir rotayı silmek, ona bugün inanan bir
# istemciyi (operatörün curl'ü, ileride bir ops betiği) SESSİZ 404'e düşürür. İşaretlemek maliyeti
# sıfıra indirmez ama iki şeyi yapar: (1) sonraki turda güvenle silinecekler artık YAZILI, (2)
# "yeni bir tüketici yazacaksam hangi uca bakmalıyım" sorusunun cevabı kodda duruyor.
# KURAL: bu uçlara YENİ tüketici bağlanmaz — kanonik uç yukarıda yazılı.
# K1-EMEKLİ: kanonik yüzey /api/hermes `spend`. Yeni tüketici bağlanmaz.
@app.get("/api/spend")
def api_spend(request: Request):
    """`GET /api/spend` (EMEKLİ): aylık LLM harcama özeti + son 30 harcama kaydı, yeniden eskiye.

    Yetki gerektirir, salt-okuma. Kanonik yüzey `/api/hermes` `spend` alanıdır — buraya YENİ
    tüketici bağlanmaz."""
    _auth(request)
    from . import spend
    return {**spend.summary(), "recent": list(reversed(store.read_jsonl("spend.jsonl")[-30:]))}


@app.get("/api/events")
def api_events(request: Request):
    """`GET /api/events`: son 80 gözlem olayını yeniden eskiye döndürür. Yetkili, salt-okuma."""
    _auth(request)
    return {"events": list(reversed(obs.recent(80)))}


@app.get("/api/summary")
def summary(request: Request):
    """`GET /api/summary`: hedef, mod, özerklik düzeyi, strateji sürümü, skor kırılımı ve merdiven.

    Yetki gerektirir, salt-okuma — hiçbir duruma yazmaz."""
    _auth(request)
    goal = config.goal()
    detail = analytics.score_mod.score_detail(store.read_jsonl("trades.jsonl"), goal)
    return {
        "goal": goal, "mode": config.MODE, "autonomy_level": config.limits()["autonomy_level"],
        "strategy_version": config.load_strategy().get("version"),
        "score_detail": detail, "ladder": analytics.autonomy_ladder(goal),
        "footer": "Research system. Paper mode. Not financial advice.",
    }


# ---- SON DÖNGÜ ÖZETİ: OLAY PENCERESİNDEN BAĞIMSIZ ---------------------------------------
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
            "halted": doc.get("halted"),
            # Kadanslı eğri yazarının MAKBUZU. `loop._persist_equity_point`
            # onu `daily_cycle` satırına damgalıyor (`loop.py` → `daily_cycle` olay damgası) ve bu fonksiyon o satırın TEK
            # okuyucusudur — ikinci bir defter taraması açmak, aynı dosyayı iki kez okumak olurdu.
            # Tüketici: `_egri_beyani` (aşağıda) → `/api/performance.equity_curve_beyani.son_yazim`
            # → panonun eğri altı beyan şeridi. Alan YOKSA None kalır: makbuzsuz bir tur "yazıldı"
            # diye okunamaz (eski kayıtlar bu alanı taşımıyor ve bu bir olgu, sıfır değil).
            "egri_nokta": (doc.get("egri_nokta") if isinstance(doc.get("egri_nokta"), dict) else None)}


@app.get("/api/today")
def api_today(request: Request):
    """`GET /api/today`: panonun ana yükü — günün görünümü + son döngü + kitap + sermaye kökeni.

    Yetki gerektirir, salt-okuma. `analytics.today()` çıktısını uç katmanında zenginleştirir:
    `son_dongu`, `latest_session`, `kitap`, `defter`, `sermaye_koken`, planlarda bayatlık/onay
    damgaları ve `inbox_count`. SIRA ZORUNLU — `inbox_count` damgalamadan SONRA hesaplanır,
    yoksa süresi dolmuş planlar da "onay bekliyor" diye sayılır."""
    _auth(request)
    d = analytics.today()
    # `inbox_count` AŞAĞIDA, `_enrich_stale_plans`TEN SONRA yazılır: sayım artık onay
    # bekleyen REVIEW planlarını da içeriyor ve o ölçüt `expired` alanına bakıyor — burada
    # çağrılsaydı süresi dolmuş planlar da "onayını bekliyor" diye sayılırdı.
    # SON DÖNGÜ — olay penceresinden BAĞIMSIZ (gerekçe `_son_dongu` başlığında).
    d["son_dongu"] = _son_dongu()
    _pf = store.read_json("portfolio.json", {}) or {}
    d["latest_session"] = _pf.get("last_date")
    # ---- KİTABIN ÜÇ ÖZET SAYISI (pano "Durum" kartı) -----------------------------------
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
    # GERÇEK-CANLI SAYAÇ. Panonun bugüne kadar gösterdiği "95 kapanmış işlem"
    # sayısı bir KARIŞIMDI: gövdesi replay tohumu (tek toplu yazım, bugünkü evrenle, survivorship'li)
    # ve satırlarda kaynak damgası yoktu — yani operatör "sistem 95 işlem yaptı" cümlesini okuyor,
    # gerçekte canlı kanıt sayısını hiçbir yerden öğrenemiyordu. Bu alan o üç sayıyı yan yana
    # koyar; hangi satırın kanıt, hangisinin training olduğu tek bakışta okunur.
    # ALAN ŞİMDİ HAZIR, PANO SONRAKİ TURDA BAĞLAR (web/* bu turda başka bir kolda).
    from . import ledgerstamp as _ls
    d["defter"] = _ls.counts()
    # SERMAYENİN KÖKENİ (sermaye tohum-ayrıştırması) — `d["equity"]`in YANINDA durmak
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
    # BROKER ↔ KİTAP MUTABAKATI (operatör şikâyeti 2026-08-21: "Alpaca'daki para panodakinden
    # farklı"). Şikâyet HAKLIYDI ve fark tek bir sayı DEĞİL: broker mark-to-market ve hesap-ömrü
    # kümülatif, kitap ise gerçekleşmiş ve 2026-08-01 reset'inden sonra yeniden tabanlanmış.
    # Sistem ayrışmayı ZATEN biliyordu (`sermaye_koken.ayrisik`) ama KÖPRÜYÜ kurmuyordu — operatör
    # iki sayı görüp aradaki terimleri göremiyordu. Bir farkı BİLMEK ile AÇIKLAYABİLMEK ayrı şey.
    # HER TERİM ÖLÇÜLÜR: broker geçmişi okunamazsa `aciklanamayan` None kalır + neden yazılır;
    # bilgisizliğimiz para farkı gibi okunamaz (uydurma yasağı).
    try:
        from .adapters import alpaca as _alp
        _ko = d["sermaye_koken"] or {}
        _rt = (_ko.get("reset_tarihi") or "")[:10] or None
        _bre, _brn = (_alp.equity_on(_rt) if _rt else (None, "reset tarihi YOK — köprü kurulamaz"))
        _acct = _alp.account() or {}
        _bpos = _alp.positions()
        _upl = sum(float(x.get("unrealized_pl") or 0.0) for x in (_bpos or []))
        # Ö-53 (2026-08-22): köprü farkın BÜYÜKLÜĞÜNÜ verir, bu alan NEREDEN geldiğini. Ölçüldü ki
        # yedi açık pozisyonun yedisinde de adet ayrışıyordu ve panoda hiçbir izi yoktu.
        # `positions` OKUNAMAZSA `None` gider — `pozisyon_mutabakati` onu "0 ayrışma"ya ÇEVİRMEZ.
        _kpos = {t: (v or {}).get("qty") for t, v in ((_pf or {}).get("positions") or {}).items()}
        # ADAPTÖR SÖZLEŞMESİ: `positions()` ARIZA hâlinde de `[]` döner (None değil). Taşımaya
        # bakmadan boş listeyi "broker'da pozisyon yok" diye okumak, broker düştüğü an kitaptaki
        # HER pozisyonu `yalniz_kitapta` saymak olurdu — yedi sahte ayrışma. `watchdog.koruma_report`
        # aynı dalı `transport()["ok"]` ile çözüyor; burası da o kapıdan geçer.
        _tasima_ok = bool((_alp.transport() or {}).get("ok"))
        # Ö-52: defterin broker-teyit sayaçları — "canlı" damgasının kaçı GERÇEKTEN broker'da.
        # Damgayı reconcile basar (loop._defter_teyit_yamasi); burası yalnız sayar (okuyucu).
        from . import ledgerstamp as _lst
        d["defter_teyit"] = _lst.teyit_counts()
        d["pozisyon_mutabakati"] = _sr.pozisyon_mutabakati(
            kitap_pozisyonlar=(_kpos if (_pf or {}).get("positions") is not None else None),
            broker_pozisyonlar=({x["symbol"]: float(x["qty"]) for x in _bpos}
                                if (_bpos is not None and _tasima_ok) else None))
        d["broker_mutabakati"] = {
            **_sr.broker_mutabakati(
                broker_equity=(float(_acct["equity"]) if _acct.get("equity") is not None else None),
                gerceklesmemis_pnl=(_upl if _acct.get("equity") is not None else None),
                broker_reset_gunu_equity=_bre,
                kitap_cash=(_pf or {}).get("cash"),
                sermaye_tabani=_ko.get("sermaye_tabani")),
            "reset_tarihi": _rt, "broker_gecmis_neden": _brn}
    except Exception as e:   # sessiz-yutma: mutabakat bir GÖRÜNÜRLÜK yüzeyidir; broker/ağ düşerse panonun geri kalanı ayakta kalmalı ve sebep alanda görünür
        d["broker_mutabakati"] = {"aciklanamayan": None,
                                  "olculemedi_neden": f"{type(e).__name__}: {e}"}
        d["pozisyon_mutabakati"] = {"ayrisan_sayisi": None, "ayrisan": [],
                                    "yalniz_kitapta": [], "yalniz_brokerda": [],
                                    "olculemedi_neden": f"köprü düştü: {type(e).__name__}: {e}"}
    _enrich_stale_plans(d.get("todays_plans") or [], d["latest_session"])
    # ---- BEKLEYEN ONAY SAYIMI ------------------------------------
    # SIRA ZORUNLU: damgalama `expired`e bakar, o alan hemen yukarıda yazıldı. TEK KAYNAK:
    # `todays_plans` — sayaç da pano listesi de aynı damgalanmış listeyi okur, ikinci bir defter
    # okuması YOK.
    _onay_bekleyen_damgala(d.get("todays_plans") or [])
    d["inbox_count"] = _inbox_count(d.get("todays_plans") or [])
    return d


@app.get("/api/signals")
def api_signals(request: Request):
    """`GET /api/signals`: son 120 aday + son 120 planı yeniden eskiye, kırpma BEYANIYLA birlikte.

    Yetki gerektirir, salt-okuma. Defterin tamamı dönmez; `ledger` bloğu toplam/gösterilen
    sayıları ve tavanı açıkça bildirir. En taze sinyal gününün planları bayatlık damgası alır."""
    _auth(request)
    # TAVAN DÜRÜSTÇE BİLDİRİLİR: defterde 368 plan varken uç 120 döndürüyordu ve pano
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
def api_market(request: Request, seri: int = 0):
    """İzlenen evrenin TAMAMI (state/bars/*.csv + finviz keşfinin bars'ta olmayan ekstraları).

    EOD KAPANIŞ verisidir — bu uç CANLI FİYAT SERVİS ETMEZ ve etmediğini `as_of` (evrendeki en
    taze seans) ile birlikte söyler. Barı `as_of`tan geride kalan semboller `stale_n` ile sayılır.
    Ölçülemeyen her alan None döner; pano onu "—" gösterir (bkz. marketview modül başlığı).

    `?seri=1` her satıra kıvılcım grafiğinin serisini ekler (`seri` + `seri_yok_nedeni`; son 40
    KAPANIŞ, ölçülen seans aralığıyla birlikte). VARSAYILAN KAPALI: 260 sembol × 40 kapanış
    (~91 KB, ölçüldü) her tazelemede seriyi çizmeyen tüketicilere ödettirilmez. Seri de EOD'dur —
    `seri.son_tarih` hangi seansa kadar olduğunu söyler; burada "canlı" olan tek şey silahlı
    sembollerin `intraday_close`u ve o da yalnız KAPANMIŞ + TAZE dakikalık bar demektir."""
    _auth(request)
    from . import marketview
    return marketview.build(seri=bool(seri))


@app.get("/api/bars/{ticker}")
def api_bars(ticker: str, request: Request, n: int | None = None):
    """Tek sembolün DERİN günlük (EOD/OHLCV) serisi — aday çekmecesinin çizdiği grafik.

    `?n=` bar sayısı (varsayılan 120, tavan 500; tavanı aşan istek tavanla döner ve `kirpildi`
    der). Yük ve dürüstlük sözleşmesi `marketview.bar_serisi()`de yazılı — özellikle: BİLİNMEYEN
    SEMBOL 404 DEĞİLDİR, `bar: null` + `neden` döner ki pano onu "ölçülemedi" diye çizebilsin.

    `n < 1` ise 400: sessizce 1'e (ya da varsayılana) çevirmek, çağıranın sorduğundan BAŞKA bir
    soruyu cevaplayıp cevabı doğruymuş gibi sunmak olurdu. Tavan ise sessiz değil BEYANLIDIR."""
    _auth(request)
    from . import marketview
    if n is not None and n < 1:
        raise HTTPException(status_code=400, detail="n en az 1 olmalı")
    return marketview.bar_serisi(ticker, n)


@app.get("/api/agent")
def api_agent(request: Request):
    """Sürüm ekseninin kanonik yüzeyi: karne defteri + hipotezler + kalibrasyon.

    İKİ OKUMA EKLENDİ VE İKİSİ DE BURAYA AİT: rollback sicili ile regresyon
    kırılımı `scoreboard.versions` üstünde yaşar, o da bu ucun ana yükü. Ayrı bir uca koymak,
    aynı defteri iki uçtan servis etmek olurdu. `analytics.agent_view()` DEĞİŞTİRİLMEDİ —
    zenginleştirme uç katmanında, yalnız okuma."""
    _auth(request)
    return {**analytics.agent_view(),
            "rollback": _rollback_sicili(),        # "kendini gerçekten geri alıyor mu?"
            "regresyon": _regresyon_kirilimi()}    # "neyi düzeltti, NEYİ BOZDU"


@app.get("/api/memory")
def api_memory(request: Request):
    """`GET /api/memory`: `state/lessons.md` ham metni + tüm hipotezler. Yetkili, salt-okuma.

    Dosya yoksa ders metni yerine `_No lessons yet._` döner (uydurma değil, açık boşluk beyanı)."""
    _auth(request)
    p = config.STATE / "lessons.md"
    return {"lessons_md": p.read_text() if p.exists() else "_No lessons yet._",
            "hypotheses": memory.all_hypotheses()}


@app.get("/api/skills")
def api_skills(request: Request):
    """`GET /api/skills`: skill kayıt defteri + katalog + öneriler + revizyonlar + son koşular.

    Yetki gerektirir. TEK YAN ETKİSİ `skills.reconcile_enablement()`tır: anahtar durumuna göre
    skill'lerin açık/kapalı alanını defterde günceller (uç bunun dışında salt-okuma). Sayımlar
    kayıttaki bayat alandan değil, o uzlaştırmadan SONRA canlı hesaplanır."""
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
    reg["revisions"] = _se.pending_drafts()                 # onay bekleyen revizyon taslakları
    reg["revision_history"] = __import__("meridian.skill_evolve", fromlist=["revisions"]).revisions()[-10:]
    # KOŞU DEFTERİ PANOYA BAĞLANIYOR. `pipeline_runs.jsonl` her skill koşusunda
    # satır yazıyor ve tek okuyucusu /api/pipeline_runs'tı — o ucu ise HİÇBİR istemci çağırmıyordu.
    # Artefakt yasası tatmin görünüyordu (modüller-arası read_jsonl VAR), ama zincir bir kat
    # yukarıda, HTTP→DOM katmanında kopuktu: statik Python grafı JS'i göremez. `skills.py` modül başlığının
    # "ajanın yaptığı hiçbir şey görünmez değildir" vaadi panoda karşılıksızdı.
    # `skills_declared_not_run` BİLEREK taşınıyor: "beyan edildi ama koşmadı" tam olarak Hermes'in
    # 14 düğmede dönmesiyle aynı sınıf bir körlük kanıtıdır ve yalnız bu defterde ölçülüyor.
    reg["recent_runs"] = list(reversed(store.read_jsonl("pipeline_runs.jsonl")[-12:]))
    # GÖRÜŞ DEFTERİ — skill katmanının kanıt yüzeyi Eksen-2'nin YANINDA durur:
    # önerilerin (`recommendations`) neden 0 olduğunu söyleyen sayım ile o boşluğu doldurmaya
    # çalışan ölçüm aynı ekranda okunmazsa, ikisi de ayrı ayrı anlamsız görünür.
    reg["gorus_defteri"] = _eksen2_gorus()
    # ENVANTER: "kaç skill var?" sorusunun paydası da yükte dursun — pano hiçbir yerde
    # sabit sayı yazmasın. `counts.total` kayıt TOPLAMIDIR (aktif+arşiv) ve tek başına
    # yaşam döngüsünü gizler; `envanter` üç paydayı da ayrı ayrı taşır.
    reg["envanter"] = skills.envanter()
    # 25b SON DAMGA (WP7-24h · denetim D-2 "En acil damga"): `shadow` bayrağının davranışsızlık
    # BEYANI kayıt yüzeyinde taşınır — pano "gölge" rozeti bu metni tooltip'te basar (YASA 6
    # okuyucusu app.js RENDER.skiller). Metin tek kaynaktan (skills.GOLGE_BEYANI) gelir ki rozet
    # ile registry aynı cümleyi kursun; davranışsızlık çivisi tests/test_kucuk_paket_v275.py'de.
    reg["golge_beyani"] = skills.GOLGE_BEYANI
    return reg


# =================================================================================================
# ONAY KAPISI — onay defterini UYGULAMA YOLUNA bağlar
# =================================================================================================
# ÖLÇÜLEN KUSUR (docs/ARTEFAKT-TARAMASI-2026-08-07.md). `approvals.jsonl`in YAZARI vardı
# (`POST /api/approvals/{id}`, aşağıda) ve OKUYUCUSU vardı (`GET /api/approvals` → panonun "Canlı
# emir onayları" kartı) — ama okuyan DAVRANMIYORDU. Hiçbir uygulama yolu deftere bakmıyordu, yani
# L1'e geçildiği gün operatörün kararı icraya bağlı OLMAYACAKTI: "onayla" yazmayan bir öneri de
# uygulanabilirdi, "reddet" yazan bir satır da hiçbir şeyi durdurmazdı. `dormant_setup` ile aynı
# sınıf — defter var, okuyucu var, DAVRANIŞSAL tüketici yok. Kusur L1 günü DOĞMAYACAK, GÖRÜNECEKTİ.
#
# EŞLEŞME ANAHTARI — ÖLÇEREK SEÇİLDİ, İCAT EDİLMEDİ. Yazıcı `approval_id`yi URL yolundan HARFİ
# HARFİNE alır (hiçbir şema dayatmaz), yani anahtarı yazıcı tarafı TANIMLAMIYOR. Sistemde
# onaylanabilir öğelere kimlik BASAN tek yer `GET /api/approvals` gelen kutusudur ve orada üç kalıp
# vardır: `arming:{setup}` · `rev:{skill}` · `rec:{skill}`. Anahtar bu yüzden GELEN KUTUSU
# KİMLİĞİdir: operatörün EKRANDA gördüğü dizge, onayladığı dizge ve kapının aradığı dizge aynı olur.
# Dizge artık `onay_kimligi()`den ÇIKAR ve gelen kutusu da onu çağırır — iki yerde iki üretim,
# önek bir gün değiştiğinde kapıyı sessizce ayrıştırırdı.
#
# KAPININ GİRDİĞİ YOLLAR (ölçüm: bu iki uç, gelen kutusunun EYLEMLİ iki türünü uygulayan TEK
# yollardır — `apply_skill_action`/`apply_revision` çağıran başka bir HTTP yüzeyi yok):
#   * `POST /api/skills/revision` action=apply → `skill_evolve.apply_revision`  (kimlik `rev:{skill}`)
#   * `POST /api/skills/apply`                → `skills.apply_skill_action`     (kimlik `rec:{skill}`)
#
# KAPI GİRMEYEN YOLLAR VE NEDENLERİ (sessiz muafiyet yok — hepsi burada yazılı):
#   * `arming:{setup}` gelen kutusu öğesi: `actions: []`. Silahlanma bir KOD değişikliğidir
#     (`ARMED_SETUPS`) — uygulayan bir çalışma-zamanı yolu YOKTUR, dolayısıyla kapılacak bir çağrı
#     da yoktur. Kimlik yine de `onay_kimligi` üretir ki yarın bir yol açılırsa anahtar hazır olsun.
#   * `POST /api/approvals/{id}`: ÖLÇÜLDÜ — onay ve uygulama AYNI UÇTA DEĞİL. Uç yalnız deftere
#     satır yazar (+ ders damıtır); hiçbir şey uygulamaz. Kapı oraya konsaydı uç kendi kendini
#     onaylatırdı.
#   * `POST /api/skills/revision` action=reject: RET hiçbir şeyi YÜRÜRLÜĞE KOYMAZ — taslağı siler,
#     yani sistemin yapacağı işi AZALTIR. Reddi onaya bağlamak, güvenli yönü tören şartına
#     bağlamak olurdu; ayrıca defterde `reject` yazan bir kararın uygulanması zaten budur.
#   * HALT / acil durdurma ailesi — `POST /api/halt`, `/api/control/halt`, `/api/control/learn_halt`,
#     `/api/control/cancel_open`, `/api/alpaca/close_all`: hepsi VAR OLAN riski AZALTIR. Deponun
#     zaten yazılı ilkesi (api.py, `koruma_kur` bloğu): "submit_armed YENİ RİSK ALIR, bu yol var
#     olan riski AZALTIR". Riski azaltan eylemin onay beklemesi, acil durdurmayı onay kuyruğunun
#     arkasına koymak demektir — kapının kendisi bir arıza olurdu.
#   * `POST /api/alpaca/koruma_kur`: riski AZALTIR (çıplak pozisyona stop koyar) VE zaten kendi
#     DURUMA-BAĞLI onay jetonuna sahiptir (`onay` + `oneri_id`). İkinci bir kapı, aynı eylem için
#     iki hüküm demekti.
#   * `POST /api/alpaca/submit_armed` ve `POST /api/plan/{id}/onayla`: emirlerin onayı BU DEFTERDE
#     DEĞİL. O yol ayrıdır, gerçektir ve davranışsaldır: `loop.operator_onay_ver` → plan satırına
#     onay damgası → `loop.girise_uygun` → silahlı küme. İlgili denetim kaydının kendi "ayırt edici notu" bu
#     karışıklığı açıkça yasaklıyor. Buraya `approvals.jsonl` kapısı koymak, çalışan bir onay
#     mekanizmasının üstüne İKİNCİ bir onay yolu açmak olurdu (app.js:8470'in reddettiği desen).
#   * `skills.auto_shadow_from_evidence` (`skills.py`, süreç-içi, HTTP değil): operatör kararı
#     DEĞİLDİR — gelen kutusunda kimliği yoktur (`pending: False` yazar), dolayısıyla ona ait bir
#     onay satırı HİÇBİR ZAMAN var olamaz; kapı oraya konsaydı L1'de skill öz-yönetim döngüsünü kalıcı ve
#     açılamaz biçimde dondururdu. Ayrıca tek yönlüdür (yalnız `shadow`, PROTECTED hariç, koşu
#     başına en çok 1) — kanıtı negatif çıkan bir skill'i incelemeye almak, kullanmayı bırakma
#     yönüdür.
#
# NEDEN `shadow` DA KAPILI (uç tarafında): skill bayrakları PAZAR riskine dokunmaz — `shadow` da
# `activate` de deterministik motoru DEĞİŞTİRMEZ (motor LLM skill'i hiç çalıştırmaz). Yani
# "riski azaltan eylem" istisnası bu aileye HİÇ uygulanmaz; iki yön de operatör kararıdır ve iki
# yön de kayıtlı olmalıdır. `shadow`u muaf tutmak, gelen kutusunun önerilerinin neredeyse tamamı
# `shadow` olduğu için kapıyı ATIL bırakırdı.
#
# ---- KARAR KAYDI — uygulanabilir karşılığı OLMAYAN öneriye KARAR YOLU --------
# OPERATÖR VAKASI: `lean_in` düğmesi kaldırıldı (ölçüldü: registry'de karşılık yok, motor
# kayıt defterini okumuyor). Doğruydu ama YARIMDI — öneri gelen kutusunda GÖRÜNÜYOR, operatörün
# yapabileceği HİÇBİR ŞEY yok. "Butonu işler hale getireceğine komple kaldırmışsın, bunu nasıl
# onaylayacağım?" Yani eksik olan davranış değil KARAR YOLUYDU.
#
# İKİNCİ ONAY YOLU AÇILMADI — ve bu bilinçli. Karar aynı deftere (`approvals.jsonl`), aynı uçtan
# (`POST /api/approvals/{id}`), aynı kimlik üreticisinden (`onay_kimligi`) yazılır. DEĞİŞEN TEK ŞEY
# KİMLİK UZAYI: `kayit:{skill}:{action}`. Neden AYRI uzay, neden `rec:` DEĞİL:
#   (1) `rec:{skill}` DİZGESİNİ L1 UYGULAMA KAPISI OKUYOR (`_onay_kapisi` ← `POST /api/skills/apply`).
#       Bugün L0'da `lean_in` için yazılacak bir `approve` satırı, yarın L1'de aynı skill'e gelen
#       bir `shadow` önerisinin uygulamasını AÇARDI — çünkü kapının kendi beyanı şu: "onay KİMLİĞE
#       bağlıdır, öneri ÖRNEĞİNE değil". Davranışsal olmayan bir kaydın davranışsal bir kapıyı
#       açması, bu bloğun kapatmak için var olduğu kusurun ta kendisi olurdu.
#   (2) EYLEM DE KİMLİĞE GİRER (`{skill}:{action}`). Kayıt uzayını hiçbir kapı okumadığı için
#       burada daha SIKI olabiliriz: `lean_in`e verilen karar, aynı skill'in `shadow` önerisini
#       "karar verilmiş" göstermez. Gelen kutusunda yanlış bir "hallolmuş" damgası, kararı
#       kaybetmekle aynı şeydir.
# BU KAYIT HİÇBİR ŞEYİ UYGULAMAZ ve bunu hem API yanıtı hem pano AÇIKÇA yazar (`KAYIT_KARARI_NOT`).
APPROVALS_LEDGER = "approvals.jsonl"

# Gelen kutusu tür kodu → kimlik öneki. `api_approvals` bu sözlükten geçer; kapı da öyle.
ONAY_ONEK = {"arming": "arming", "skill_revision": "rev", "skill_rec": "rec",
             "skill_rec_kayit": "kayit"}

#: Bir UYGULAMA KAPISININ okuduğu önekler — yani kararı yazmak yarın bir icrayı AÇAN kimlikler.
#: Ölçüm (çağrı yeri taraması): `_onay_kapisi` yalnız iki yerden çağrılıyor — `POST /api/skills/
#: revision` (`rev:`) ve `POST /api/skills/apply` (`rec:`). `arming:` ve `kayit:` uzaylarını
#: HİÇBİR kapı okumaz. Bu küme elle yazılı olmak zorunda (statik graf "hangi önek okunuyor"u
#: göremez) ve bu yüzden bir TESTLE çivilenir: kaynak `_onay_kapisi(onay_kimligi(...))` çağrıları
#: bu kümeden başka bir tür kullanırsa kırmızı verir.
KAPI_OKUYAN_ONEKLER = frozenset({"rev", "rec"})

#: Karar kaydının operatöre kurduğu TEK cümle — API yanıtında da panoda da BİREBİR aynı okunur.
#: İki yerde iki cümle, yarın birinin "uygulandı" imâsı taşımasıyla biterdi.
KAYIT_KARARI_NOT = ("kayıt-önerisi; karar defterde, davranış DEĞİŞMEZ — gerçek aksiyon knob/kapı "
                    "düzeyindedir (bkz. motor_ici_esik_asan)")


def onay_kimligi(tur: str, ad: str) -> str:
    """Gelen kutusu öğesinin KİMLİĞİ — hem listeleyen uç hem kapı buradan üretir (tek kaynak).

    Bilinmeyen tür SESSİZCE geçilmez: `KeyError` yerine tanınabilir bir dizge üretmek, yarın
    eklenen bir türün kapıya `None:x` diye görünmesi ve eşleşmeyi sessizce imkânsız kılması olurdu.
    """
    if tur not in ONAY_ONEK:
        raise KeyError(f"bilinmeyen gelen kutusu türü: {tur!r} — ONAY_ONEK'e ekle")
    return f"{ONAY_ONEK[tur]}:{ad}"


def _onay_defteri_karari(kimlik: str) -> dict:
    """`approvals.jsonl`da `kimlik` için EN SON operatör kararı — FAIL-CLOSED okuma.

    DÖNÜŞ: {"karar": "approve"|"reject"|"bozuk"|None, "bozuk": int, "atfedilemeyen": int,
            "okunamadi": str|None}

    SIRA DOSYA SIRASIDIR, `ts` DEĞİL: defter salt-ekleme yazılır, yani dosya sırası zaman sırasıdır.
    `ts` alanına sıralama yükü bindirmek, biçimi bozuk ya da eksik bir damganın sıralamayı sessizce
    ters çevirmesi demekti (onayı reddin ÖNÜNE geçirebilirdi). Operatör önce onaylayıp sonra
    reddederse SON satır kazanır — kararın kendisi bir olaydır ve son karar yürürlüktedir.

    BOZUK SATIR = ONAY YOK (fail-closed). Üç ayrı bozukluk sınıfı ayrı sayılır:
      * `atfedilemeyen`: satır sözlük değil ya da `id` okunabilir bir dizge değil → KİMSEYE onay
        vermez. Başkasının onayını da İPTAL ETMEZ: kime ait olduğu bilinmeyen bir satırı "bu ret
        olabilir" diye herkesin üstüne yürütmek, tek bozuk satırla defteri kalıcı olarak
        kullanılamaz kılardı. Sayısı olaya taşınır, yani defterin kirliliği GÖRÜNÜR.
      * `bozuk`: `id` EŞLEŞİYOR ama `decision` okunamıyor (dizge değil / approve|reject dışında) →
        o kimliğin hükmü "bozuk" olur ve kapı REDDEDER. Atfedilebilen bir satırı yorumlayamamak,
        tam olarak "okunamayan onay = onay YOK" halidir.
      * `okunamadi`: defterin kendisi okunamadı (G/Ç, bozuk depo) → onay YOK.
    JSON olarak hiç ayrıştırılamayan satırları `store.read_jsonl` zaten atar ve bir kez
    `jsonl_rows_skipped` uyarısı bırakır — o sınıfın izi orada, bu kapının gördüğü küme ise
    ayrıştırılabilmiş ama şeması bozuk satırlardır.
    """
    t = _defter_tarama()
    if t["okunamadi"]:
        return {"karar": None, "bozuk": 0, "atfedilemeyen": 0, "okunamadi": t["okunamadi"]}
    k = t["kararlar"].get(kimlik) or {"karar": None, "bozuk": 0}
    return {"karar": k["karar"], "bozuk": k["bozuk"],
            "atfedilemeyen": t["atfedilemeyen"], "okunamadi": None}


def _defter_tarama() -> dict:
    """Defterin TEK GEÇİŞLİ taraması: `{"kararlar": {id: {karar, bozuk, ts, reason, satir}},
    "atfedilemeyen": int, "okunamadi": str|None}`.

    NEDEN AYRI BİR FONKSİYON: karar kaydı ile birlikte defterin İKİNCİ bir
    okuyucusu doğdu — gelen kutusu artık her öğe için "bu öneriye karar verilmiş mi" sorusunu
    soruyor. O soruyu ikinci bir döngüyle cevaplasaydık, deponun en pahalı hatası olan
    "aynı defteri iki yerde iki farklı yorumlayan iki okuyucu" sınıfını KAPI ile GÖRÜNÜM arasında
    açmış olurduk (kapı "reject" derken pano "bekliyor" gösterebilirdi). Döngü TEK; `_onay_
    defteri_karari` bu taramadan TÜRER ve semantiği birebir korunur (dosya sırası = zaman sırası,
    son satır kazanır, bozuk `decision` = "bozuk", atfedilemeyen satır kimseye onay vermez).

    GÖRÜNÜM TARAFI KARAR VERMEZ: bu fonksiyon yalnız OKUR. Kapı hâlâ `_onay_kapisi`dir ve
    fail-closed davranışı orada; buradan dönen `ts`/`reason`/`satir` alanları SADECE ekrana çıkar.
    """
    try:
        satirlar = store.read_jsonl(APPROVALS_LEDGER)
    except Exception as e:
        return {"kararlar": {}, "atfedilemeyen": 0, "okunamadi": f"{type(e).__name__}: {e}"[:120]}
    kararlar, atfedilemeyen = {}, 0
    for r in satirlar:
        if not isinstance(r, dict):
            atfedilemeyen += 1
            continue
        rid = r.get("id")
        if not isinstance(rid, str) or not rid:
            atfedilemeyen += 1
            continue
        k = kararlar.setdefault(rid, {"karar": None, "bozuk": 0, "ts": None, "reason": "",
                                      "satir": None})
        d = r.get("decision")
        if not isinstance(d, str) or d.strip().lower() not in ("approve", "reject"):
            k["bozuk"] += 1
            k["karar"] = "bozuk"
            continue
        k["karar"] = d.strip().lower()
        k["ts"], k["reason"], k["satir"] = r.get("ts"), str(r.get("reason") or "")[:200], r
    return {"kararlar": kararlar, "atfedilemeyen": atfedilemeyen, "okunamadi": None}


def kayit_karar_kimligi(skill: str, action: str) -> str:
    """Karar-kaydı kimliği: `kayit:{skill}:{action}`. Üretim TEK yerde (`onay_kimligi`) kalır —
    gelen kutusu, yazma ucu ve pano AYNI dizgeyi görmek zorunda (kimlik dersi)."""
    return onay_kimligi("skill_rec_kayit", f"{skill}:{action}")


def _oneriler_karar_damgali() -> list[dict]:
    """Bekleyen Eksen-2 önerileri + (uygulanabilir karşılığı olmayanlar için) KARAR DAMGASI.

    NEDEN BURADA DA: öğrenme kartı ile onay gelen kutusu AYNI öneri listesini gösteriyor. Karar
    damgası yalnız gelen kutusunda olsaydı, operatör kararını verdikten sonra öğrenme kartında
    aynı satır hâlâ kararsız görünürdü — "iki yüzey aynı gerçeği farklı anlatır" sınıfı.
    DÜĞME YİNE TEK YERDE (gelen kutusu): burası damgayı OKUR, karar YAZDIRMAZ — `planOnayla`nın
    tek-onay-yolu deseniyle aynı (app.js `planKart` beyanı)."""
    from . import skills as _sk
    recs = _sk.pending_recommendations()
    if not any(not r.get("uygulanabilir") for r in recs):
        return recs                                   # defteri boşuna okuma
    t = _defter_tarama()
    out = []
    for r in recs:
        if not r.get("uygulanabilir"):
            r = {**r, "karar_kaydi": _karar_kaydi(str(r.get("skill")), str(r.get("action")),
                                                  tarama=t)}
        out.append(r)
    return out


def _kayit_karar_kunyesi(approval_id: str) -> dict:
    """`kayit:{skill}:{action}` kimliği için KARAR ANINDAKİ kanıt künyesi (skill · action · öneri
    satırının örneklem damgası). Kararın neye karşı verildiği defterden okunabilmeli: aynı öneri
    yarın başka bir n ile yeniden doğduğunda operatör "ben neyi reddetmiştim?" diyebilmeli.

    KÜNYE ÖNERİ SATIRINDAN GELİR, YENİDEN ÖLÇÜLMEZ: `skills.record_recommendation` künyeyi öneri
    ANINDA basıyor; burada `catalog()`u yeniden çağırmak, karar anındaki (daha yeni) bir ölçümü
    "öneri kanıtı" diye kaydetmek olurdu. Öneri bulunamazsa UYDURULMAZ: `bulunamadi` yazılır."""
    ad = str(approval_id).split(":", 1)[1] if ":" in str(approval_id) else ""
    skill, _, action = ad.partition(":")
    try:
        from . import skills as _sk
        rec = next((r for r in _sk.pending_recommendations()
                    if str(r.get("skill")) == skill and str(r.get("action")) == action), None)
    except Exception as e:
        return {"skill": skill, "action": action,
                "olculemedi": f"{type(e).__name__}: {e}"[:120]}
    if rec is None:
        return {"skill": skill, "action": action,
                "bulunamadi": "karar anında bu öneri BEKLEYEN listesinde değildi — künye yok"}
    return {"skill": skill, "action": action, "rationale": str(rec.get("rationale") or "")[:200],
            "ornek": rec.get("ornek"), "ornek_yeterli": rec.get("ornek_yeterli"),
            "oneri_ts": rec.get("ts"), "kaynak": rec.get("source")}


def _karar_kaydi(skill: str, action: str, *, tarama: dict | None = None) -> dict:
    """Bir öneri için KARAR KAYDI bloğu: kimlik + (varsa) verilmiş karar + künyesi.

    "BEKLİYOR" DEĞİL "KARAR VERİLMİŞ" (brief madde 3): karar verilmiş bir öneri gelen kutusunda
    duruyor olabilir (üreteç aynı öneriyi yarın yeniden yazabilir) ama BEKLİYOR gibi SAYILMAZ ve
    damgasıyla görünür. Aynı öneri tekrar üretilirse operatör önceki kararını ve o günkü künyeyi
    tekrar okur — aynı satırı iki kez incelemek zorunda kalmaz.

    DEFTER OKUNAMAZSA KARAR "YOK" SAYILIR ve bu YÖN BİLİNÇLİ: görünüm tarafında fail-closed
    demek "kararı unut, yine sor" demektir (kaybolan karar > gereksiz soru). Kapı tarafındaki
    fail-closed ile karışmasın diye `okunamadi` alanı çıktıda AÇIKÇA taşınır."""
    t = tarama if tarama is not None else _defter_tarama()
    kimlik = kayit_karar_kimligi(skill, action)
    k = (t.get("kararlar") or {}).get(kimlik) or {}
    satir = k.get("satir") or {}
    return {"id": kimlik, "karar": k.get("karar"), "ts": k.get("ts"),
            "gerekce": k.get("reason") or "",
            # KARAR ANINDAKİ KÜNYE — kararın hangi kanıta karşı verildiği. Yazan taraf
            # (`api_approve`) ölçer; burada yalnız okunur, YENİDEN ÖLÇÜLMEZ.
            "kunye": satir.get("kunye"),
            "okunamadi": t.get("okunamadi"),
            "davranissal": False, "not": KAYIT_KARARI_NOT}


# Kapının reddederken yazdığı gerekçeler. YASA 4: her sessiz-olmayan ret ≥20 karakter gerekçe
# taşır ve gerekçe HTTP gövdesine de düşer — operatör "neden olmadı"yı olay akışını açmadan görür.
_ONAY_RET_NEDEN = {
    None: ("onay defterinde bu öneriye ait KARAR YOK — L1+'ta uygulama, `POST /api/approvals/{id}` "
           "ile yazılmış bir `approve` satırı gerektirir (fail-closed)"),
    "reject": ("onay defterindeki SON karar `reject` — operatör bu öneriyi reddetmiş; uygulama "
               "yapılmadı (kararı değiştirmek için yeni bir `approve` satırı yaz)"),
    "bozuk": ("onay defterinde bu kimliğe ait satır var ama `decision` alanı OKUNAMIYOR — "
              "okunamayan onay onay DEĞİLDİR (fail-closed); satırı düzelt ya da yeniden onayla"),
}


def _onay_kapisi(kimlik: str, *, yol: str, **ek) -> dict:
    """L1+ UYGULAMA KAPISI: defterde `approve` satırı yoksa uygulama YAPILMAZ.

    L0-NÖTRLÜK BİR YAN ETKİ DEĞİL, FONKSİYONUN İLK SATIRI: `autonomy_level < 1` iken kapı deftere
    HİÇ BAKMAZ, hiçbir olay yazmaz, hiçbir istisna atmaz ve her zaman `gecti=True` döner. Yani
    bugünkü canlı (L0 kâğıt) yolda tek bir dosya okuması bile eklenmez — davranış BİREBİR aynıdır
    ve regresyon yüzeyi sıfırdır. Kapı YALNIZ L1'de bağlar; zaten L1'de doğacak kusur içindir.

    TEKRAR OYNATMA SINIRI BEYANLIDIR: onay KİMLİĞE bağlıdır, öneri ÖRNEĞİNE değil — `rec:foo` için
    yazılmış bir `approve`, sonraki bir `reject` gelene kadar `rec:foo`nun sonraki uygulamalarını
    da yetkilendirir. `koruma_kur`daki gibi bir DURUM özetine (`oneri_id`) bağlamak daha sıkı
    olurdu ama bugün gelen kutusu öğelerinin taşıdığı böyle bir özet YOK; uydurmak, bu depoda
    yasak olan "eşiği sonradan seç" hamlesinin aynısı olurdu. Sıkılaştırma bir ölçüm kartına bağlı.
    """
    lvl = config.limits()["autonomy_level"]
    if lvl < 1:
        return {"gecti": True, "gerekli": False, "seviye": lvl, "kimlik": kimlik, "neden": ""}
    d = _onay_defteri_karari(kimlik)
    if d["okunamadi"]:
        neden = (f"onay defteri OKUNAMADI ({d['okunamadi']}) — okunamayan defter onay içermez; "
                 f"uygulama reddedildi (fail-closed)")
    elif d["karar"] == "approve":
        obs.log("approval_gate_passed", kimlik=kimlik, yol=yol, seviye=lvl,
                atfedilemeyen=d["atfedilemeyen"], **ek)
        return {"gecti": True, "gerekli": True, "seviye": lvl, "kimlik": kimlik, "neden": ""}
    else:
        neden = _ONAY_RET_NEDEN[d["karar"]]
    # KİMLİK GEREKÇENİN İÇİNDE: 409 gövdesi operatörün gördüğü TEK metin olabilir ve "onay yok"
    # cümlesi, NEYİ onaylayacağını söylemiyorsa yarım bir cevaptır. Aranan dizge burada yazılıdır
    # ki operatör onu doğrudan `POST /api/approvals/{id}`ye geçirebilsin.
    neden = f"[{kimlik}] {neden}"
    obs.warn("approval_missing_refused", kimlik=kimlik, yol=yol, seviye=lvl,
             karar=str(d["karar"] or "yok"), bozuk=d["bozuk"], atfedilemeyen=d["atfedilemeyen"],
             neden=neden, **ek)
    return {"gecti": False, "gerekli": True, "seviye": lvl, "kimlik": kimlik, "neden": neden}


@app.post("/api/skills/revision")
async def api_skill_revision(request: Request):
    """Skill revizyon taslağı: operatör onayı (apply) ya da ret (reject). Taslaklar ajan
    tarafından yazılır ama YALNIZ burada, insan kararıyla yürürlüğe girer.

    `apply` kolu L1+'ta ONAY DEFTERİNE bakar (`rev:{skill}`); `reject` kolu bakmaz —
    ret hiçbir şeyi yürürlüğe koymaz. Gerekçeler `_onay_kapisi` bloğunda yazılı."""
    _auth(request)
    body = await request.json()
    skill, action = str(body.get("skill") or ""), str(body.get("action") or "")
    from . import skill_evolve
    if action == "apply":
        kapi = _onay_kapisi(onay_kimligi("skill_revision", skill),
                            yol="skill_evolve.apply_revision")
        if not kapi["gecti"]:
            # 409, 403 DEĞİL: kimlik doğrulandı (`_auth` geçildi), yetki de yerinde — çakışan şey
            # DÜNYANIN DURUMU (defterde onay yok/ret var). Kardeş operatör-reddi
            # `/api/plan/{id}/onayla` da aynı kodu ve aynı "neden gövdede metin" desenini kullanır.
            raise HTTPException(status_code=409, detail=kapi["neden"])
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
    backtest cannot validate LLM-skill impact, so a human approves what the brain recommends.

    L1+'ta "insan onaylar" artık bir NİYET değil bir KAYIT — kapı, uygulamadan önce
    onay defterinde `rec:{skill}` için `approve` satırı arar. L0'da davranış birebir aynıdır.

    RET SÖZLEŞMESİ. Başarı 200 + `{"ok": true, ...}` (DEĞİŞMEDİ); her ret artık
    durum koduyla FIRLAR — 400 istek bozuk, 409 dünyanın durumu çakışıyor — ve `detail` operatörün
    okuyacağı `[kimlik] gerekçe` metnini taşır. Eskiden ret HTTP 200 gövdesinde geliyordu ve pano
    onu görmüyordu (aşağıdaki blokta ölçüm ve üç seçeneğin gerekçesi)."""
    _auth(request)
    from . import skills
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="expected JSON {skill, action}")
    skill, action = (body or {}).get("skill"), (body or {}).get("action")
    # KAPI `apply_skill_action`DAN ÖNCE, İÇİNDE DEĞİL: aynı fonksiyonu süreç-içi otomatik yol da
    # çağırıyor (`skills.auto_shadow_from_evidence`) ve o yolun gelen kutusunda kimliği YOK — kapıyı
    # fonksiyonun içine koymak L1'de o döngüyü kalıcı olarak dondururdu (gerekçe: kapı bloğu).
    kapi = _onay_kapisi(onay_kimligi("skill_rec", str(skill or "")),
                        yol="skills.apply_skill_action", eylem=str(action or "")[:20])
    if not kapi["gecti"]:
        raise HTTPException(status_code=409, detail=kapi["neden"])
    res = skills.apply_skill_action(skill or "", action or "")
    if res.get("ok"):
        obs.log("skill_action_applied", skill=skill, action=action)
        _diag_onbellek_bosalt("skill_action")     # YALNIZ ok: reddedilen eylem hiçbir şeyi değiştirmedi
        return res
    # ---- `ok:False` ARTIK HTTP 200 İLE GEÇMEZ -------------------------------
    # ÖLÇÜLEN ARIZA (operatör vakası): `apply_skill_action` `lean_in` için
    # `{"ok": False, "reason": "unknown action 'lean_in'"}` döndürüyordu, bu uç onu HTTP **200**
    # ile gövdede yolluyordu ve `app.js:applySkillRec` yalnız FIRLATILAN hatayı yazdığı için
    # (sözleşme: 2xx dışı = `ApiHata`) ekranda HİÇBİR ŞEY olmuyordu. Bu, daha önce kapatılan
    # "sessiz ret" sınıfının ikinci örneği — bu kez boş `catch`ten değil, 200-gövde-ret yolundan.
    #
    # DÜZELTMENİN YERİ NEDEN BU KATMAN (üç seçenek tartıldı, bu ölçüye dayanıyor):
    #   * `apply_skill_action`ın KENDİSİ istisna fırlatsaydı: süreç-içi otomatik yol
    #     (`skills.auto_shadow_from_evidence`) reddi bir KANIT SATIRI olarak yazıyor
    #     ("UYGULANAMADI: <reason>" → `atlanan`); orayı istisnaya çevirmek, ölçüm döngüsünü
    #     bir bayrak reddi yüzünden düşürürdü. Sözlük sözleşmesi o çağıran için DOĞRU.
    #   * YALNIZ ön yüzde gövde okumak: aynı yanlışın üçüncü kopyası olurdu — `/api/skills/apply`
    #     dışındaki her istemci (curl, betik, gelecekteki yüzey) reddi yine sessizce yutardı.
    #   * BU KATMAN: HTTP sözleşmesinde ret = durum kodu. Kardeş uç `/api/skills/revision` ve
    #     onay kapısı zaten aynı deseni kullanıyor (409 + `detail` metni), yani pano tarafında
    #     YENİ bir yol açılmıyor — var olan `eylemHatasiYaz` dalı reddi olduğu gibi basıyor.
    #
    # DURUM KODU `kod` ALANINDAN TÜRETİLİR, SERBEST METİNDEN DEĞİL: `reason` operatöre yazılmış bir
    # cümledir ve değişebilir; ona göre dallanmak kapıyı bir gün sessizce yanlış koda kaydırırdı.
    #   400 — istemci hatalı bir eylem gönderdi (yazım hatası/eski istemci). Aynı ucun gövde
    #         ayrıştırma hatası da 400 (yukarıda) — istek BOZUK, dünya değil.
    #   409 — kimlik ve yetki yerinde; ÇAKIŞAN ŞEY DÜNYANIN DURUMU: skill korumalı, kayıtta yok,
    #         ya da eylemin (lean_in) uygulayıcısı yok. `/api/skills/revision`ın 409 gerekçesiyle
    #         birebir aynı sınıf ("kimlik doğrulandı … çakışan şey DÜNYANIN DURUMU").
    _KOD_DURUM = {"bilinmeyen_eylem": 400, "korumali": 409, "kayitsiz": 409,
                  "uygulayicisi_yok": 409}
    kod = str(res.get("kod") or "")
    obs.warn("skill_action_refused", skill=skill, action=action, kod=kod or None,
             detail=str(res.get("reason") or "")[:300])
    raise HTTPException(status_code=_KOD_DURUM.get(kod, 409),
                        detail=f"[{onay_kimligi('skill_rec', str(skill or ''))}] "
                               f"{res.get('reason') or 'eylem UYGULANMADI (sunucu sebep bildirmedi)'}")


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


# ---- TOP VIEWS — DOKUZ FACET, TEK PAYDA, TAM METRİK ------------------------------------------
# NEDEN AYRI UÇ (ve neden `/api/plots` genişletilmedi): `/api/plots` bir MATRİS ucudur — kurulum ×
# rejim ızgarası + hücre çekmecesi. Dokuz facetin yedisi o ızgaranın ekseni DEĞİL; sekizinci ve
# dokuzuncusu ise başka bir defteri (plan/kapı) sayar. İkisini tek yüke sıkıştırmak, panonun
# matris kartını her facet eklenişinde büyütür ve iki farklı paydayı tek yanıtta ayrımsız
# gösterirdi. Matris ucu OLDUĞU GİBİ KALIR (kırılmaz sözleşme); bu uç onun yanına gelir.
#
# BU UCUN KAZANDIRDIĞI TEK ŞEY: **PF**. `/api/plots` hücrede yalnız ortalama R veriyor ve ortalama
# R'den brüt kâr / brüt zarar ayrımı GERİ ÇIKARILAMAZ — bu bir eksiklik değil bilgi kaybıdır.
# Pano bugüne dek her PF hücresine dürüstçe `ölçülemedi + neden` basıyordu; yüzeyin değeri buna
# takılıydı. Hesap `meridian/topviews.py`de, kova sınırları orada GEREKÇESİYLE sabit.
@app.get("/api/topviews")
def api_topviews(request: Request):
    """Dokuz facet (KAYNAK: kurulum·rejim·sektör · SONUÇ: çıkış nedeni·tutma·R kovası ·
    KAPI: kapı reddi·kapı hükmü·kaynak damgası), her satırda `n · toplam R · brüt kâr · brüt
    zarar · PF · kazanma` ve her facette KENDİ kaynağı/penceresi/paydası.

    UYDURMA YOK: `gross_loss == 0` ise PF `None` + neden (sonsuz DEĞİL); R taşımayan hücrede
    toplamlar `None` (0.0 DEĞİL); `n == 0` satır basılmaz; ölçülemeyen facet `satirlar: null` +
    neden döner ve BOŞ LİSTE dönmez (boş liste "hiç yok" der, ölçülemedi ise başka bir cümledir).
    YALNIZ OKUMA: hiçbir dal state'e dokunmaz."""
    _auth(request)
    return topviews_mod.topviews()


def _slippage_measured(trades: list[dict], goal: dict) -> dict:
    """ÖLÇÜLEN SLİPAJ vs VARSAYILAN SLİPAJ.

    `loop.py` → `reconcile_broker_state` kapanan işlemlere `alpaca_fill_price` + `mirror_divergence` geri-yazıyor ve
    gerekçesi açık: "real-world slippage vs the model is measurable". Ama ölçülen sapmayı
    `goal.slippage_bps`e (ya da herhangi bir kalibrasyon raporuna) geri besleyen tüketici YOKTU —
    döngünün kapanan ucu hiç kurulmamıştı. Model tarafı sabit: goal.yaml:62 slippage_bps: 5
    (A17: eski `:27` çapası bayattı — satır kaydı, değer değişmedi).

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
    """İki PİYASA GÖSTERGESİNİN canlı hükmü + iki PORTFÖY tavanının knob durumu.

    HÜKÜM: SMA/VIX bacakları KAPI DEĞİL, GÖSTERGEdir — ve bu satır artık onların
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
    """`hypotheses.vs_benchmark_at_ship` SAYACI.

    `reflect.py` → `_submit_locked` her ship'e `analytics.benchmark_relative()` anlık görüntüsü damgalıyor ve
    yorumu şunu söylüyor: "20-30 gözlem birikince kapıya eklenip eklenmeyeceğine VERİYLE karar
    verilir". Ama alanın repo genelinde tek okuyucusu damgalandığını doğrulayan bir testti — ne
    pano ne API servis ediyordu, ve o kararı tetikleyecek SAYAÇ hiç yazılmamıştı. Yani alan
    sonsuza dek sessizce birikecek, karar anı ASLA gelmeyecekti. Eşiğin görünür sayacı budur."""
    rows = [h.get("vs_benchmark_at_ship") for h in memory.all_hypotheses()]
    rows = [r for r in rows if isinstance(r, dict)]
    beat = sum(1 for r in rows if r.get("beat_benchmark") is True)
    lost = sum(1 for r in rows if r.get("beat_benchmark") is False)
    return {"n": len(rows), "beat": beat, "lost": lost,
            # Eşik `reflect._submit_locked` yorumundan gelir; sayaç onu YENİDEN tanımlamaz, gösterir.
            "decision_n": 20,
            "ready": len(rows) >= 20,
            # ÇAPA SEMBOLE ÇEVRİLDİ (2026-08-16): burada `reflect.py:721` yazıyordu ve `reflect.py`ye  # çapa-mezar-taşı
            # dokuz satır eklenince çapa bir YORUM satırını göstermeye başladı — `stale_line_anchors`
            # onu aynı turda yakaladı. Sembol kayar, satır kaymaz: kaynak `reflect._submit_locked`
            # içindeki "SPY-üstü alfa DAMGASI" bloğudur (`base["vs_benchmark_at_ship"]` yazımı).
            "note": ("her ship'e damgalanan 'SPY'ı geçti mi' anlık görüntüsü; 20 gözlemde kapıya "
                     "eklenip eklenmeyeceğine veriyle karar verilir "
                     "(reflect._submit_locked → 'SPY-üstü alfa DAMGASI' bloğu)")}


# ---- EĞRİNİN PENCERE BEYANI ---------------------------------------
# ÖLÇÜLEN KUSUR (canlı, 2026-08-14): `equity_curve.json` 882 nokta taşıyor ve sonuncusu 2026-07-20 —
# eğri 24 gündür donuktu, pano bunu HİÇBİR YERDE söylemiyordu ve operatör grafiğe bakıp "P&L
# yansıtmıyor" diye okuyordu. Aynı zarfta 1 sermaye reset işareti var (`SR-20260801T151429+0000`,
# `egri_son_nokta ["2026-07-20", 94457.91]`): yani çizilen tek çizgi bir sermaye tabanı
# değişiminin ÖNCESİNİ ve SONRASINI birlikte kapsıyor. Ve 24 günlük boşluk KAPANMAYACAK — geriye
# doldurmak uydurma olurdu (`loop._persist_equity_point` bloğu bunu adıyla yazıyor) — yani eğri yeni noktalarla
# sürerken ortada kalıcı bir delik kalacak.
#
# ÜÇ OLGU DA ZATEN ÖLÇÜLÜYDÜ, HİÇBİRİNİN PANODA OKUYUCUSU YOKTU:
#   * reset işaretleri zarfın `sermaye.CURVE_MARK_KEY` anahtarında yaşıyor ve `/api/performance`
#     zarfı OLDUĞU GİBİ servis ediyor — yani tel üzerinde vardı, çizilmiyordu;
#   * kadanslı yazarın makbuzu (`durum`: yazildi · tazelendi · idempotent_atlandi · yazilmadi)
#     `daily_cycle` satırında ve `_son_dongu()` o satırı ZATEN okuyor (ikinci defter taraması YOK);
#   * donukluk ve boşluk noktaların KENDİSİNDEN ölçülür.
# Bu blok üçünü tek yüzeyde toplar. HESAP BURADA, PANODA DEĞİL: pano ikinci bir "kaç gün geride"
# yasası kursaydı, ilk düzenlemede uçtan sessizce ayrışırdı (`sermaye.koken` docstring'indeki
# "iki hesap" kusuru).
#
# HİÇBİR SAYI UYDURULMAZ: çözülemeyen nokta sayılır (`okunamayan_nokta`) ama seriye 0 olarak
# GİRMEZ; ölçülemeyen her alan None döner ve panonun karşılığı "ölçülemedi"dir.

# BOŞLUK EŞİĞİ — TAKVİM GÜNÜ, SEANS DEĞİL. Burada bir seans takvimi ÇALIŞTIRILMAZ: repo'nun takvimi
# (earnings/exchange) bu uca bağlı değil ve onu buraya çekmek, panonun eğri beyanını takvim
# sağlığına rehin ederdi. Ölçülen büyüklük bu yüzden dürüstçe TAKVİM GÜNÜdür ve eşik doğal
# aralıkların ÜSTÜNE konur: hafta sonu Cuma→Pazartesi 3 gün, hafta sonu + tek tatil Cuma→Salı 4
# gün. 5 gün ve üstü, ARDIŞIK en az iki seansın seride olmadığı anlamına gelir. Eşik bir HÜKÜM
# değil bir MERCEKtir — dışarı `bosluk_esigi_gun` olarak beyan edilir ki okuyucu neyin sayıldığını
# bilsin (yıl sonu gibi çok-tatilli aralıklar bu mercekte "boşluk" görünebilir ve görünmelidir:
# eğri onları gerçekten atlamıştır).
_EGRI_BOSLUK_ESIK_GUN = 5
# Yük tavanı: pano her boşluğa bir işaret çiziyor. Tavan aşılırsa `bosluk_kirpildi` ile BEYAN edilir
# — sessizce kısaltılmış bir liste, "başka boşluk yok" diye okunurdu.
_EGRI_BOSLUK_TAVAN = 24


def _egri_beyani(ec: dict | None, pf: dict | None, sinir: dict | None = None) -> dict:
    """Pano eğrisinin PENCERE BEYANI: hangi seri, hangi tabanda, ne kadar geride, nerede kırık.

    Girdiler ÇAĞIRANIN ELİNDEKİ okumalardır (`equity_curve.json` zarfı + `portfolio.json`) — bu
    fonksiyon hiçbir dosyayı ikinci kez okumaz. Tek istisnası `_son_dongu()`dur ve o da olay
    defterinin damgasına göre ÖNBELLEKLİdir. `sinir` da aynı yasanın gereğidir (v264): tohum
    penceresinin sınırı BURADA HESAPLANMAZ — çağıran onu `ledgerstamp.seed_boundary(rows, eq=…)`
    ile elindeki okumalardan hesaplar ve verir; verilmezse beyan None taşır (ölçüm yok ≠ sağlam)."""
    import datetime as _dt
    from . import sermaye as _sr

    def _coz(p):
        """Tek noktayı (date, float) çiftine çöz. Çözülemeyen bacak None döner — 0 DEĞİL."""
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            return None, None
        try:
            t = _dt.date.fromisoformat(str(p[0])[:10])
        except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — çözülemeyen nokta `okunamayan_nokta` sayacına girer ve beyanla birlikte panoya çıkar; burada uyarı basmak her istekte aynı bozuk satır için gürültü üretirdi
            t = None
        try:
            v = float(p[1])
        except (TypeError, ValueError):  # sessiz-yutma: aynı sayaç — değeri okunamayan nokta seriye 0 olarak GİRMEZ, sayılır ve beyan edilir
            v = None
        return t, v

    ec = ec if isinstance(ec, dict) else {}
    pts = ec.get("points") if isinstance(ec.get("points"), list) else []
    tarihli, okunamayan = [], 0
    for i, p in enumerate(pts):
        t, v = _coz(p)
        if t is None or v is None:
            okunamayan += 1
            continue
        tarihli.append((i, t, round(v, 2)))

    ilk = [tarihli[0][1].isoformat(), tarihli[0][2]] if tarihli else None
    son = [tarihli[-1][1].isoformat(), tarihli[-1][2]] if tarihli else None

    # DONUKLUK EĞRİNİN DIŞINDAN ÖLÇÜLÜR. Serinin kendi son tarihi "geride mi?" sorusunu cevaplayamaz;
    # ölçüt kitabın işlediği son seanstır (`portfolio.last_date`). İkisinden biri yoksa cevap 0 değil
    # None'dur — "geride değil" ile "kıyas yapılamadı" aynı cümle değildir.
    son_seans = (pf or {}).get("last_date") if isinstance(pf, dict) else None
    gecikme = None
    try:
        if son and son_seans:
            gecikme = (_dt.date.fromisoformat(str(son_seans)[:10])
                       - _dt.date.fromisoformat(son[0])).days
    except (TypeError, ValueError):  # sessiz-yutma: kitabın son seansı biçimsiz — gecikme ÖLÇÜLEMEDİ olarak None kalır ve pano bunu adıyla yazar (0 gün YAZMAZ)
        gecikme = None

    bosluklar = []
    for (i0, t0, _v0), (_i1, t1, _v1) in zip(tarihli, tarihli[1:]):
        gun = (t1 - t0).days
        if gun >= _EGRI_BOSLUK_ESIK_GUN:
            # `i` = boşluğun SOLUNDAKİ noktanın dizini — pano işareti tam oraya koyar (seri dizin
            # ekseninde çizilir, yani boşluk grafikte normal bir adım gibi görünür; işaret olmadan
            # delik GÖRÜNMEZ, tam da bu turun kapattığı hâl).
            bosluklar.append({"onceki": t0.isoformat(), "sonraki": t1.isoformat(),
                              "gun": gun, "i": i0})
    n_bosluk = len(bosluklar)
    en_buyuk = max(bosluklar, key=lambda b: b["gun"]) if bosluklar else None
    bosluk_kirpildi = n_bosluk > _EGRI_BOSLUK_TAVAN
    if bosluk_kirpildi:
        bosluklar = bosluklar[-_EGRI_BOSLUK_TAVAN:]      # EN YENİLER kalır (operatörün baktığı uç)

    # RESET İŞARETLERİ — anahtar `sermaye.CURVE_MARK_KEY`den okunur, burada İKİNCİ bir literal
    # yazılmaz (`test_defter_kaynak_damgasi_v140` o adı tek kaynakta çiviliyor).
    isaretler = []
    for m in (ec.get(_sr.CURVE_MARK_KEY) or []):
        if not isinstance(m, dict):
            continue
        et, ev = _coz(m.get("egri_son_nokta"))
        idx = next((i for i, t, _v in tarihli if t == et), None) if et is not None else None
        isaretler.append({
            "id": m.get("id"), "tarih": m.get("tarih"),
            "onceki_deger": m.get("onceki_deger"), "yeni_deger": m.get("yeni_deger"),
            "egri_son_nokta": ([et.isoformat(), ev] if et is not None else None),
            "i": idx,
            # KONUM ÖLÇÜLEMEZSE İŞARET YİNE LİSTELENİR, sadece grafiğe konmaz: bir reset'i "yeri
            # bulunamadı" diye gizlemek, beyanın kendisini yutmak olurdu.
            "konum_neden": (None if idx is not None else
                            "işaretin `egri_son_nokta` tarihi seride bulunamadı — kırılma "
                            "LİSTELENİR ama grafiğe konumlandırılamaz"),
        })

    # TOHUM SINIRI — DÖRDÜNCÜ PENCERE (WP2-D artığı, v264). Beyan üç pencereyi zaten söylüyordu
    # (donukluk, delikler, resetler) ama serinin hangi kısmının ANTRENMAN TOHUMU (`replay_seed`,
    # survivorship'li training) ve hangi kısmının kadanslı yazarın CANLI noktaları olduğunu
    # söylemiyordu — 882 tohum noktası ile canlı kuyruk TEK çizgide, sınır beyansızdı. Sınırın
    # yasası `ledgerstamp.seed_boundary`de kalır (TEK hesap; ikincisini kurmak `sermaye.koken`
    # docstring'indeki "iki hesap" kusurunun aynısı olurdu); burada yalnız GRAFİK İNDİSİ eklenir —
    # reset işaretleriyle aynı mekanik: indis sunucudan gider, bulunamazsa None + neden (yer
    # uydurulmaz; damga yolunun tarihi eğri noktasına denk gelmeyebilir ve bu NORMALDİR).
    # `yollar_ayrisik` OLDUĞU GİBİ taşınır: ROADMAP §2-37'nin ölçtüğü ayrışmanın (reset işareti ↔
    # damga) panodaki tek görünürlüğü budur; hangi yolun otorite olduğu Rol-1 kararıdır ve bu
    # blok o kararı VERMEZ — donmuş yolun seçili kaldığını beyan eder.
    if sinir is None:
        tohum = None
    else:
        _rd = sinir.get("replay_end")
        _idx = None
        if _rd is not None:
            try:
                _rdt = _dt.date.fromisoformat(str(_rd)[:10])
                _idx = next((i for i, t, _v in tarihli if t == _rdt), None)
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz sınır tarihi konumlanamaz — sınır yine LİSTELENİR, `konum_neden` durumu adıyla taşır; 0. noktaya çivilemek yer uydurmak olurdu
                _idx = None
        tohum = {
            "replay_end": _rd, "kaynak": sinir.get("kaynak"), "guven": sinir.get("guven"),
            "yollar": sinir.get("yollar"),
            "yollar_ayrisik": bool(sinir.get("yollar_ayrisik")),
            "i": _idx,
            "konum_neden": (None if _idx is not None else
                            ("tohum sınırı ölçülemedi — grafiğe konum konmaz" if _rd is None else
                             "sınır tarihi seride bulunamadı (damga yolu eğri noktasına denk "
                             "gelmeyebilir) — sınır LİSTELENİR ama grafiğe konumlandırılamaz")),
        }

    # SON YAZIM MAKBUZU — kadanslı yazarın kendi hükmü (`loop._persist_equity_point`), olay
    # defterinden `_son_dongu()` ile. Makbuz yoksa None: "yazılmadı" DİYEMEYİZ, ölçemedik.
    sd = _son_dongu()
    son_yazim = sd.get("egri_nokta") if isinstance(sd, dict) else None

    return {
        "n_nokta": len(pts), "okunamayan_nokta": okunamayan,
        "ilk": ilk, "son": son,
        "son_seans": son_seans, "gecikme_gun": gecikme,
        "bosluk_esigi_gun": _EGRI_BOSLUK_ESIK_GUN, "n_bosluk": n_bosluk,
        "bosluklar": bosluklar, "en_buyuk_bosluk": en_buyuk,
        "bosluk_kirpildi": bosluk_kirpildi, "bosluk_tavani": _EGRI_BOSLUK_TAVAN,
        "reset_isaretleri": isaretler, "n_isaret": len(isaretler),
        "tohum_siniri": tohum,
        "son_yazim": son_yazim if isinstance(son_yazim, dict) else None,
        "son_dongu_tarih": (sd or {}).get("date") if isinstance(sd, dict) else None,
        "beyan": ("seri, kitabın BEYANLI sermaye ofseti düşülmüş TEK tabanda çizilir "
                  "(loop._persist_equity_point); seans sonunda günde tek nokta eklenir. Reset "
                  "işaretleri kırılmayı BEYAN eder, nokta olarak eklenmez; geçmiş boşluklar "
                  "geriye doldurulmaz — doldurmak uydurma olurdu."),
    }


@app.get("/api/performance")
def api_performance(request: Request):
    """`GET /api/performance`: sermaye eğrisi + pencere beyanı, skor kırılımı, Kelly, kuyruk riski,
    ölçülen slipaj, benchmark farkı, rejim/skill kırılımları ve son 40 işlem.

    Yetki gerektirir, salt-okuma. Ölçülemeyen alanlar (ör. `slippage_measured`) sıfır değil None
    döner — pano onları "henüz ölçülmedi" diye çizer."""
    _auth(request)
    goal = config.goal()
    trades = store.read_jsonl("trades.jsonl")
    _ec = store.read_json("equity_curve.json", {"points": []})
    # TOHUM SINIRI TEK HESAPTAN (v264): sınır yasası `ledgerstamp.seed_boundary`de; bu uç ona
    # ELİNDEKİ iki okumayı verir (defter `rows`, zarf `eq`) — aynı istekte ikinci bir okuma anı
    # doğmaz. /api/hermes'in karnesi (`learning.defter.sinir`) AYNI saf fonksiyonu çağırır.
    from . import ledgerstamp as _ls
    _sinir = _ls.seed_boundary(trades, eq=_ec)
    return {
        "equity_curve": _ec,
        # Eğrinin PENCERE BEYANI — hangi seri, ne kadar geride, nerede kırık.
        # Aynı zarftan türetilir (ikinci okuma YOK) ve panonun eğri altı şeridini besler.
        "equity_curve_beyani": _egri_beyani(_ec, store.read_json("portfolio.json", {}),
                                            sinir=_sinir),
        "score_detail": analytics.score_mod.score_detail(trades, goal),
        "kelly": analytics.score_mod.kelly_fraction(trades),          # realized-edge sizing ceiling (advisory)
        "tail_risk": analytics.score_mod.tail_risk(trades),           # block-bootstrap VaR/CVaR
        # ÖLÇÜLEN SLİPAJ: sabit 5bps varsayımının yanına ölçülen medyan. Ayna dolana kadar
        # None — panoda "henüz ölçülmedi" olarak çizilir, sıfır olarak DEĞİL.
        "slippage_measured": _slippage_measured(trades, goal),
        "benchmark_relative": analytics.benchmark_relative(),         # alpha vs just holding SPY
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
    # VARSAYILAN MODEL ADLARI KODDAN TÜRETİLİR. Pano "Boşsa gemini-2.5-pro."
            # yazıyordu; kod ise `GEMINI_DEFAULT_MODEL = "gemini-3.1-pro"` (operatör
            # tercihi) kullanıyor. Yani operatör alanı boş bıraktığında panonun söylediği model
            # ile GERÇEKTE koşan model farklıydı — çelişik varsayılan dokümantasyonu, ve panoya
            # bakarak "hangi model koşuyor?" sorusunun cevabı YANLIŞ okunuyordu. Metin artık sabitin
            # KENDİSİNDEN gelir: sabit değişince pano kendiliğinden doğru söyler, elle senkron yok.
    from . import hermes as _hm_defaults
    return {"secrets": secrets_mod.status(),
            "live_enabled": config.live_enabled(),
            # MOD ÖLÇÜMDEN GELİR. Panonun "Güvenlik durumu" kartı modu KODA ÇAKILMIŞ
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
            # `senkron_ts` BU DALDA DA ZORUNLU. `sync_local_agent_gemini`
            # kendi dönüşlerinin üçünde de damga taşıyor; import/çağrı bacağı düşerse damgasız
            # bir sözlük dönerdi ve panonun okuduğu satır "damga yok" derdi — oysa ölçüm ANI
            # burada BİLİNİYOR. Damgayı atlamak, bilinen bir zamanı bilinmiyor göstermekti.
            local_agent = {"ok": False, "detail": f"senkron hatası ({type(e).__name__})",
                           "senkron_ts": memory.now_iso()}
    # [6] LİTESTREAM ÇİFTİ: iki anahtar da mevcutsa env dosyası üretilir, değilse kaldırılır —
    # değer asla loglanmaz; olayı `litestream_env_sync` kendisi basar (durum, değer değil).
    litestream_env = (secrets_mod.litestream_env_sync()
                      if name in secrets_mod.LITESTREAM_PAIR else None)
    _diag_onbellek_bosalt("secret_set")           # sağlayıcı/beceri durumu değişti (maskeli alanlar)
    return {"ok": True, "name": name, "status": secrets_mod.status().get(name),
            "skills_enabled": rec["changed"], "local_agent": local_agent,
            "litestream_env": litestream_env}


@app.delete("/api/secrets/{name}")
def api_delete_secret(name: str, request: Request):
    """`DELETE /api/secrets/{name}`: saklanan anahtarı siler. YETKİLİ ve YAZAN uç.

    Yalnız `secrets_mod.ALLOWED` içindeki adlar kabul edilir (aksi 400). Yan etkileri: anahtara
    bağlı skill'ler yeniden kapatılır, `secret_cleared` olayı yazılır, teşhis önbelleği boşaltılır
    ve `GEMINI_API_KEY` silinirse yerel ajan yedeklenen Nous ayarına döndürülür. Anahtarın
    kendisini DÖNMEZ, yalnız durum özetini."""
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
    # [6] LİTESTREAM ÇİFTİ: üyelerden biri silindiyse env dosyası KALDIRILIR — yarım kimlik
    # dosyası bırakmak birimi eski/eksik kimlikle koşturmak olurdu (POST dalıyla aynı kanca).
    litestream_env = (secrets_mod.litestream_env_sync()
                      if name in secrets_mod.LITESTREAM_PAIR else None)
    _diag_onbellek_bosalt("secret_cleared")       # POST dalıyla aynı gerekçe, ters yön
    return {"ok": True, "name": name, "status": secrets_mod.status().get(name),
            "skills_disabled": rec["changed"], "local_agent": local_agent,
            "litestream_env": litestream_env}


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
    """EMEKLİ İKİZ — DAVRANIŞI /api/halt'a DELEGE EDER.

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
    """Faz 3 — Debug Export: state kök dosyaları (json/jsonl/yaml) + son olaylar tek zip.
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
    """Öz-değerlendirme: her çağrıda taze üretilir (ucuz okuma-sentezi); haftalık koşum
    ayrıca bildirim atar. Rapor ajanın kanıt paketine de girer."""
    _auth(request)
    from . import selfreview
    return selfreview.build()


@app.get("/api/alerts")
def api_alerts(request: Request):
    """YEREL ALARM GELEN KUTUSU. Uzak kanal (Telegram/webhook) yapılandırılmamışsa
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
    # ACK ZAMANI 'ŞİMDİ' DEĞİL, GÖRÜLEN EN YENİ OLAYIN ZAMANIDIR. `now_iso()` yazmak
    # aynı-saniye yarışını operatörün aleyhine çözüyordu: gelen kutusu okunduktan SONRA, ACK
    # yazılmadan ÖNCE düşen bir alarm (olaylar saniye çözünürlüklü) `ts <= ack_ts` olduğu için bir
    # daha hiç görünmeden "okundu" sayılıyordu — ve tam da o alarm, en taze olan, en kritik olabilir.
    # Sınır yalnız GERÇEKTEN GÖSTERİLMİŞ en yeni olaya kadar ilerler; ötesi görülmemiştir.
    _seen_max = max((str(g.get("last_ts") or "") for g in (_before.get("groups") or [])),
                    default="")
    doc = {"ack_ts": _seen_max or memory.now_iso(), "ack_by": "operator",
           # SOĞURULAN YIĞIN: `notify_undelivered.json` KÜMÜLATİF bir sayaçtır ve
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
        """Ack defterine bilinen anahtarları İDEMPOTENT ekler; ilk görülme anını EZMEZ.

        `store.update_json` geri-çağrısıdır: defteri yerinde değiştirir ve gerçekten yeni satır
        eklenip eklenmediğini bool olarak döner (yazımın gerekip gerekmediğini o belirler)."""
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
# SAĞLAYICI SAĞLIK KARTI
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
    """Yedi sağlayıcının sağlık kartı (sekiz satır — Alpaca'nın iki taşıması ayrı).
    AĞ ÇAĞRISI YOK — hepsi süreç-içi sayaç okuması."""
    from .adapters import finviz as _fv, massive as _ms, insider as _in
    from .adapters import shortinterest as _si, alpaca as _alp, fmp as _fmp
    from .adapters import constituents as _con
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
    try:
        # FMP LİSTEYE 2026-08-25'TE GİRDİ ve YOKLUĞU BİR GÖZETİM BOŞLUĞUYDU, bir tercih değil.
        # Operatör bildirdi ("sağlayıcılarda FMP'yi göremiyorum") ve ölçüm onu doğruladı: FMP'nin
        # bu depoda ADAPTÖRÜ (`adapters/fmp.py`), İKİ ANAHTAR YUVASI (`FMP_API_KEY`,
        # rotasyonlu `FMP_API_KEY_2`), GÜNLÜK KOTA MUHASEBESİ (`fmp_usage.json`) ve araç
        # kapısı var (`skills.py`, `fmp=='req'` olan araçlar anahtar gelene kadar KAPALI) —
        # ama sağlık kartında SATIRI YOKTU. Yani en çok bakılan yerde görünmüyordu.
        #
        # BUNUN BEDELİ ÖLÇÜLDÜ, varsayılmadı: aynı teşhis gövdesinde `integrity.production.starved`
        # `fmp_source` diyor ve gerekçesi "anahtar var ama üretmiyor — 402 Payment Required";
        # `pipeline.fmp_usage` 2026-08-23 için 43 çağrı / 43 hata (`by_status: {"402": 43}`)
        # sayıyor. Yani sağlayıcı ÇALIŞMIYORDU ve sağlayıcı kartı bunu HİÇ göstermiyordu —
        # operatör "FMP gerek" yazan araçlarla, sebebini göstermeyen bir kart arasında kaldı.
        #
        # `ek` ÜÇ ŞEYİ AYRI TAŞIR ve üçü ayrı sorulardır: anahtar VAR MI (`anahtar`), kota
        # KAPATMIŞ MI (`kota_blokli` — 429 sınıfı), ve günün muhasebesi (`kullanim`; 402 gibi
        # ödeme/plan hataları burada `by_status`ta görünür). Üçünü tek bayrağa indirmek
        # "anahtar yok" ile "anahtar var ama plan kapsamıyor"u aynı hâle sokardı.
        satirlar.append(_saglayici_satiri("fmp", _fmp.health(),
                                          ek={"anahtar": _fmp.available(),
                                              "kota_blokli": _fmp.quota_blocked(),
                                              "kullanim": _fmp.usage()}))
    except Exception as e:
        satirlar.append({"ad": "fmp", "ok": None, "olculemedi": f"{type(e).__name__}"})
    try:
        # ÜYELİK KAYNAĞI DA BİR SAĞLAYICIDIR (2026-08-25, aynı gözetim boşluğu). FMP satırını
        # eklerken `health()` sunan adaptörler sayıldı ve kartta olmayan İKİNCİSİ buydu:
        # `adapters/constituents` S&P 500 üyeliğini kurar (FMP birincil, Wikipedia ikincil) ve
        # ürünün gerçek tüketicisi `universe_drift()`tir — yani EVRENİN kendisi bu kaynağa bağlı.
        # Kendi şerhi Wikipedia yolunun bu kurulumda HTTP 403 aldığını yazıyor; kartta satırı
        # olmadığı için o hâl hiçbir yerde görünmüyordu.
        satirlar.append(_saglayici_satiri("uyelik", _con.health()))
    except Exception as e:
        satirlar.append({"ad": "uyelik", "ok": None, "olculemedi": f"{type(e).__name__}"})
    return {"kapsam": "surec-ici",
            "beyan": ("sağlık sayaçları DİSKE YAZILMAZ — bu kart yalnız BU sürecin gördüğünü "
                      "anlatır ve yeniden başlatmada sıfırlanır. Boş bir kart 'sağlayıcı bozuk' "
                      "değil 'bu süreçte henüz çağrı yapılmadı' demektir."),
            "saglayicilar": satirlar}


# =================================================================================================
# SESSİZ HAT — ÜÇ SAĞLIK YÜZEYİNİN LEVEL-1 TOPLAMASI
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
    # ASKIDA: pencereyi aşmış AMA sistemin kendi beyanıyla beklemeye alınmış mekanizma
    # (hermes kota soğuması / kimlik havuzu tükenmesi). SAPMA DEĞİLDİR — sessiz hattın kırmızısını
    # meşru bir beklemeyle boyamak, hattın anlamını yine alarm-yorgunluğuna çevirirdi. Ama GİZLİ de
    # değildir: `ok/total` oranında eksik görünen mekanizmanın nedeni burada yazar.
    askida = list(wd.get("askida") or [])
    # F8/T3.1 (A4 kararı 2026-08-23): penceresinde-sayaç kanonik `n_ok`tan okunur; eski
    # sayı-taşıyan `ok` eşanlamlıdır ve okunursa SAYILIR (durum_sozlugu — okuyucu-ölümü ölçümü).
    # `ok` artık HÜKÜM taşır ve sayaç yerine geçemez (bool `n_ok_oku`da tip emniyetiyle elenir).
    from . import durum_sozlugu as _dsz
    n_ok, _ = _dsz.n_ok_oku(wd)
    segmentler.append({
        "ad": "bekçiler", "saglikli": not b_sapma,
        # KRİTİK = "hiç koşmadı". watchdog.report'un kendi ifadesiyle en yüksek sesli hâl:
        # geciken bir mekanizma yavaşlamıştır, hiç koşmamış bir mekanizma KABLOLANMAMIŞTIR.
        "kritik": bool(never),
        # SAYI YOKSA SAYI YAZILMAZ (v196): `n_ok` okunamadıysa özet "—" der — "None/17" basmak
        # ölçülemezliği bir sayıymış gibi giydirmek olurdu.
        "ozet": (f"{n_ok}/{toplam}" if toplam is not None and n_ok is not None else "—"),
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

    # F8 ÇİFT-ALAN GEÇİŞİ (WP8-C · T1.4): sapma satırlarının `detay`ı kanonik `neden` adıyla DA
    # taşınır; `detay` dönem sonuna dek eşanlamlı kalır (okuyucu-ölümü durum_sozlugu sayaçlarıyla
    # ölçülür, düşürme Rol-1'de). Askıda satırları ZATEN iki adı da taşıyor (:3010 civarı).
    # `saglikli` alanı KALIR-şerhlidir: bilinçli İKİ değerli, fail-closed (docstring sözleşmesi) —
    # sözlük onu yeniden adlandırmaz, şerhiyle kaydeder (meridian/durum_sozlugu.py).
    for _seg in segmentler:
        for _s in _seg.get("sapmalar") or []:
            _s.setdefault("neden", _s.get("detay"))
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
# GÖLGE-FİT GÖRÜNÜRLÜĞÜ (operatör: "pano antrenman hiç koşmamış diyor")
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
# EKSEN-2'NİN "0 ÜRETİLDİ"Sİ — DOĞRU SAYI, GÖRÜNMEYEN NEDEN
# =============================================================================================
# ÖLÇÜM (canlı `last_learn.eksen2.teshis.sayim`): gercek_katman_olculmemis 57 · korumali 5 ·
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
#
# PAYDA DÜZELTİLDİ. Yukarıdaki ölçüm (`gercek_katman_olculmemis 57` / payda 67)
# DOĞRU SAYILMIŞ ama YANLIŞ ETİKETLENMİŞTİ: `skills.catalog()` kayıt defterinin BİLDİĞİ `retired`
# alanını düşürüyordu, yani 36 ARŞİV kaydı da "ölçülmemiş aktif skill" gibi sayılıyordu. Panonun
# okuduğu şey "67 skillin 60'ı hiç koşmamış" idi; ölçülen gerçek ise "31 AKTİF skillin 24'ü hiç
# koşmamış"tır. Aradaki fark bir yuvarlama değil, olmayan bir kusurun sürekli raporlanmasıydı.
# Payda artık `arsiv` kovası DÜŞÜLEREK kurulur ve SABİT YAZILMAZ: kova sayımından türer.
_EKSEN2_OLCULMEMIS_ONEK = "gercek_katman_olculmemis"
_EKSEN2_KORUMALI = "korumali"
_EKSEN2_ARSIV = "arsiv"                   # `skills.ARSIV` ile AYNI ad — kova adı sözleşmedir
_AXIS2_DEFTERI = "axis2_status.json"      # LİTERAL ad (codelaw.artifact_graph okuyabilsin)


def _eksen2_ozeti(ex: dict | None) -> dict:
    """Sıfır üretimin NEDENİ — kova sayımından türetilmiş özet.

    UYDURMA YASAĞI: kovalar yükte yoksa `durum="ÖLÇÜLEMEDİ"` ve bütün sayılar None döner —
    0 DEĞİL. "31 aktif skillin 2'si ölçüldü" ile "kaç skill olduğunu bilmiyoruz" aynı ekranda aynı
    şeye benzeyemez.

    PAYDA = AKTİF KÜME. `arsiv` kovası ne bölene ne paydaya girer; AYRI bir sayı olarak
    taşınır ki "emekli edildi" ile "ölçülmedi" bir daha tek rakamda birleşmesin."""
    kv = (ex or {}).get("kovalar")
    if not isinstance(kv, dict) or not kv:
        return {"durum": "ÖLÇÜLEMEDİ", "toplam_skill": None, "olculen": None,
                "olculmemis": None, "korumali": None, "arsiv": None, "kayit_toplam": None,
                "oran": None, "payda": None, "dokum": [],
                "motor_ici_esik_asan": None,
                "neden": ("Eksen-2 teşhis kovaları yükte YOK — üretecin sessizliği ÖLÇÜLEMEDİ. "
                          "Bu bir 'kanıt yok' hükmü değildir: hükmü verecek sayım okunamadı.")}
    sayim = {str(k): int(v) for k, v in kv.items() if isinstance(v, (int, float))}
    kayit_toplam = sum(sayim.values())                 # kayıt defterinin TAMAMI (aktif + arşiv)
    arsiv = sayim.get(_EKSEN2_ARSIV, 0)
    toplam = kayit_toplam - arsiv                      # PAYDA: yalnız aktif küme
    olculmemis = sum(n for k, n in sayim.items() if k.startswith(_EKSEN2_OLCULMEMIS_ONEK))
    korumali = sayim.get(_EKSEN2_KORUMALI, 0)
    olculen = toplam - olculmemis - korumali
    return {
        "durum": "dolu",
        "toplam_skill": toplam, "olculen": olculen,
        "olculmemis": olculmemis, "korumali": korumali,
        # ARŞİV AYRI SAYIDIR, PAYDANIN DIŞINDA: kütüphanenin büyüklüğü de görünsün ama hükme
        # karışmasın. İkisi tek rakama katlanırsa yaşam döngüsü bir daha okunamaz.
        "arsiv": arsiv, "kayit_toplam": kayit_toplam,
        # ÇUBUK PAYDASI BEYANLI (kart sözleşmesi): paydası yazılmayan bir doluluk,
        # okurun kendi uydurduğu tavana göre okunur. Sayı KOVA SAYIMINDAN türer — panoya da
        # buraya da SABİT yazılmaz (ders: 2026-07-30 arşivi "66 skill" yazısını bir gecede
        # yalana çevirmişti).
        "oran": (round(olculen / toplam, 4) if toplam else None),
        "payda": f"AKTİF skill sayısı ({toplam}) — arşiv ({arsiv}) hariç, kayıt toplamı {kayit_toplam}",
        "dokum": sorted(sayim.items(), key=lambda kv_: (-kv_[1], kv_[0])),
        "motor_ici_esik_asan": None,      # `_eksen2_motor_ici` doldurur (ayrı defterden okunur)
        "neden": (f"{toplam} AKTİF skillin {olculmemis}'i gerçek katmanda HİÇ ölçülmemiş, "
                  f"{korumali}'i motor-içi (aday değil); hüküm verilebilir olan {olculen}. "
                  f"Ayrıca {arsiv} kayıt ARŞİVDE (emekli/birleştirilmiş) — ölçülmemiş değil, "
                  f"ölçülecek olmayan. Üreteç kanıt olmayan yerde öneri ÜRETMEZ — '0 üretildi' "
                  f"bir arıza değil, KANIT YOKLUĞUdur."),
    }


_GORUS_DEFTERI = "skill_gorusleri.jsonl"       # LİTERAL adlar (codelaw.artifact_graph çözebilsin)
_GORUS_DURUM = "skill_gorus_durum.json"


def _gorus_defter_hacmi() -> dict:
    """Görüş defterinin HACMİ — rapordan BAĞIMSIZ, doğrudan defterden okunur.

    NEDEN AYRI BİR OKUMA. `rapor()` bir HÜKÜMDÜR ve hüküm verilemeyebilir: girdi bekçisi bir
    yüzeyi kapatırsa (kill#4) ya da örneklem n_min'in altındaysa rapor o yüzey için boş döner.
    O anda "defter boş" ile "defter dolu ama hüküm yok" ekranda aynı şeye benzerdi. Hacim
    sayacı bu ikisini ayırır: kaç satır YAZILDI sorusunun cevabı hükümden bağımsızdır.

    HAM SATIR TAŞIMAZ: defter süresiz büyür (canlı kaynaklarda bugün ~4400 satır); uç yükü
    onunla birlikte büyüyemez. Yalnız yüzey × skill sayımı ve tarih aralığı çıkar."""
    satirlar = store.read_jsonl(_GORUS_DEFTERI)
    hacim: dict[str, dict[str, int]] = {}
    tarihler = []
    for s in satirlar:
        y, sk = str(s.get("yuzey") or "?"), str(s.get("skill") or "?")
        hacim.setdefault(y, {})[sk] = hacim.setdefault(y, {}).get(sk, 0) + 1
        if s.get("tarih"):
            tarihler.append(str(s["tarih"]))
    return {"n": len(satirlar), "yuzey_skill": {y: dict(sorted(v.items())) for y, v in sorted(hacim.items())},
            "ilk_tarih": (min(tarihler) if tarihler else None),
            "son_tarih": (max(tarihler) if tarihler else None)}


def _eksen2_gorus() -> dict:
    """GÖRÜŞ DEFTERİNİN OKUMA ALANI — defterin DAVRANIŞSAL tüketicisi.

    NEDEN İLK GÜNDEN BAĞLI. `dormant_setup` dersi: önden bağlı arkadan bağsız bir yüzey (31 plan /
    0 işlem) inşa edilmez. Görüş defteri yazılmaya başlar başlamaz okuyucusu da olmalı, yoksa
    kanıt birikir ve hiçbir karara girmez — bu deponun en sık ölçülen arıza sınıfı.

    NE TAŞIR: kova sayımı, yüzey-başına FDR künyesi, terfi/emeklilik ADAY listeleri ve kill#1'in
    p95 ölçümü. NE TAŞIMAZ: ham görüş satırları (defter süresiz büyür) ve HİÇBİR eylem düğmesi —
    terfi otomatik değildir, bu alan da bir onay yüzeyi DEĞİLDİR.

    Defter okunamazsa `durum="ÖLÇÜLEMEDİ"` (boş rapor DEĞİL): "hiç görüş yok" ile "bakamadık"
    aynı ekranda aynı şeye benzeyemez."""
    try:
        from . import skill_gorus as _sg
        r = _sg.rapor()
    except Exception as e:
        # HÜKÜM ÜRETİLEMEDİ AMA DEFTER OKUNABİLİR: hacim sayacı ayrı bir okumadır ve ayakta kalır.
        # "Hiç görüş yok" ile "hüküm kurulamadı" aynı ekranda aynı şeye benzeyemez.
        return {"durum": "ÖLÇÜLEMEDİ", "neden": f"{type(e).__name__}: {e}",
                "defter_n": None, "kova_sayimi": None, "yuzeyler": None,
                "terfi_adaylari": None, "emeklilik_isaretleri": None, "kill_p95": None,
                "hacim": _gorus_defter_hacmi()}
    d = store.read_json(_GORUS_DURUM, None)
    return {
        "durum": "dolu", "kart": r.get("kart"), "neden": None,
        "defter_n": r.get("defter_n"), "hacim": _gorus_defter_hacmi(),
        "kova_sayimi": r.get("kova_sayimi"),
        "evren": (r.get("evren") or {}).get("sayim"),
        "girdi_bekcisi": r.get("girdi_bekcisi"),
        "yuzeyler": {y: {k: v[k] for k in ("durum", "neden", "fdr", "metrik", "skiller")
                         if k in v} for y, v in (r.get("yuzeyler") or {}).items()},
        "terfi_adaylari": r.get("terfi_adaylari"), "emeklilik_isaretleri": r.get("emeklilik_isaretleri"),
        "esikler": r.get("esikler"),
        # KILL#1 ÖLÇÜMÜ AYRI DEFTERDEN: `rapor()` saf okumadır ve süre ölçmez; süre kadansın
        # kendi damgasıdır. İkisini tek çağrıya katlamak, panonun her açılışında ölçüm koşturmak
        # ve o ölçümü "canlı kadans süresi" diye raporlamak olurdu.
        "kill_p95": ((d or {}).get("kill_p95") if isinstance(d, dict) else None),
        "son_kadans": ({"ts": d.get("ts"), "sure_ms": d.get("sure_ms"),
                        "sure_p95_ms": d.get("sure_p95_ms"),
                        "yazilan": (d.get("toplama") or {}).get("yazilan")}
                       if isinstance(d, dict) else None),
        "beyan": r.get("beyan"),
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

    ESKİ NOT DÜZELTİLDİ: burada eskiden "kadansın gerçekten koşmadığı doğrudur" yazıyordu.
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
        # DAMGA MI, ÇIKARIM MI: `kunye` değeri "fit_ts damgası YOK, tarih künyeden
        # çıkarıldı" demektir — daha önce canlının hâli buydu ve ayrımı yazmayan bir tarih,
        # çıkarımı damga gibi gösterirdi.
        "kaynak": an2.get("son_fit_kaynak"),
        # KADANS ≠ FİT: rozetin neyi ölçtüğü kartın kendi üstünde yazsın, dipnotta değil.
        # BEYAN DÜZELTİLDİ: eskiden "damgayı yalnız maybe_refit yazar" deniyordu ve bu artık
        # YANLIŞ — damga fiilin yanına (refit_and_save) taşındı, yani fit'i kim atarsa atsın
        # deneme damgası düşer. Eski metni bırakmak, düzeltilmiş bir kusuru panoda yaşatmaktı.
        "beyan": ("`son_fit` MODELİN son fiilen KURULDUĞU andır (`fit_ts`). Yanındaki `son deneme` "
                  "(`fit_attempt_ts`) fit DENENDİĞİ andır ve fit edilmeyen denemeler de "
                  "(veri seti değişmedi · eşik altı) oraya damga bırakır. İkisi AYRI olgudur: "
                  "deneme ilerlerken fit yerinde kalabilir. Damgayı `shadow_model.refit_and_save` "
                  "atar — kadans (maybe_refit) da, loop.P5_LEARN de o yoldan geçer."),
    }
    # ---- SON DENEME --------------------------------------------------------------------
    # Fit ile DENEME panoda ayrı okunmak zorunda: "kadans koştu, veri değişmemişti" ile "kadans
    # hiç koşmadı" tek satıra sıkışırsa sessiz bir duruş taze görünür (kadans nabzının ölçtüğü
    # damga tam olarak budur).
    out["son_deneme"] = {
        "ts": an2.get("son_deneme_ts"),
        "atlama_nedeni": an2.get("son_atlama_nedeni"),
        "damga_var": bool(an2.get("son_deneme_ts")),
    }
    # ---- EKSEN-2 ÖZETİ -----------------------------------------------------------------
    ex = out.get("eksen2")
    if isinstance(ex, dict):
        ex = dict(ex)
        ozet = _eksen2_ozeti(ex)
        ozet["motor_ici_esik_asan"] = _eksen2_motor_ici()
        ex["ozet"] = ozet
        out["eksen2"] = ex
    return out


def _bekci_durumlari() -> dict:
    """DÖRT OKUYUCUSUZ BEKÇİ RAPORUNUN SERVİS YÜZEYİ (WP8 · YASA 6 kapanışı — ölçüm:
    docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md §T2). `goal_failure` · `kitap_damga` ·
    `mutabakat_tazelik` · `onayli_gonderim` dördü de watchdog'da üretiliyordu, alarm satırı
    akışa düşüyordu ama DURUM YÜZEYİ yoktu — operatör "şu an ne âlemde" sorusunu ancak son
    alarmı bularak cevaplayabiliyordu. Dördü fonksiyon olduğu için `codelaw.artifact_graph`
    onları göremez (parity `artifact_unread` yalnız dosya-artefaktı tarar); okuyucu zinciri
    bu yüzden ELLE kurulur: watchdog üretir → bu uç servis eder → pano `bekciDurumlari` okur.

    EVİ /api/diagnostics, /api/today DEĞİL — maliyet ÖLÇÜLDÜ: dördü de yalnız yerel state
    okur (goal: trades.jsonl + goal.yaml skoru; kitap: damga tabanı + içerik özeti; mutabakat/
    onay: iki json + trade_plans.jsonl), broker/ağ çağrısı YOK; yine de soğuk-yol maliyeti
    /api/today'e taşınmaz (16,7 sn vakasının dersi) ve 45 sn'lik teşhis önbelleği burada doğru
    amortisman.

    RAPORLAR OLDUĞU GİBİ SERVİS EDİLİR (alan çevrilmez): F8 geçiş haritası "ÖNCE yüzey aç,
    sonra adlandır" der — goal_failure hükmü `failed` taşır (`ok` değil) ve pano onu üç değerli
    okur. `kitap_damga_report` PERSIST'SİZ çağrılır: tabanı yalnız `check_kitap_damga_and_alarm`
    ilerletir; okuma yolu tabana yazsaydı '/api/diagnostics'i açık tutmak dedektörü körleştirirdi
    (raporun kendi sözleşmesi).

    RAPOR BAŞINA YALITIM (integrity_report'un dedektör-yalıtım deseni): biri düşerse üçü ayakta
    kalır ve düşen, iskeletiyle GÖRÜNÜR — `ok=None + olculemedi + olculemedi_neden`; 0'a/temiz'e
    çevrilmez (uydurma yasağı)."""
    from . import watchdog as _w
    out = {}
    for ad, fn in (("goal_failure", _w.goal_failure_report),
                   ("kitap_damga", _w.kitap_damga_report),
                   ("mutabakat_tazelik", _w.mutabakat_tazelik_report),
                   ("onayli_gonderim", _w.onayli_gonderim_report)):
        try:
            out[ad] = fn()
        except Exception as e:  # sessiz-yutma: tek bekçinin düşmesi teşhis ucunun tamamını düşürmemeli; düşüş iskeletle (olculemedi + neden) panoda GÖRÜNÜR kalır, temiz'e çevrilmez
            out[ad] = {"ok": None, "olculemedi": True,
                       "olculemedi_neden": f"{type(e).__name__}: {e}"}
    return out


def _durum_sozlugu(bd: dict) -> dict:
    """F8 KANONİK DURUM SÖZLÜĞÜNÜN SERVİS YÜZEYİ (WP8-C — tasarım §5/§6; sözlüğün kendisi
    `meridian/durum_sozlugu.py`). İKİ İŞ, İKİSİ DE ÖLÇÜM:

    1) `satirlar` — dört bekçi raporunun (bd) kanonik-okuyucudan geçmiş normalize hükümleri.
       SENTEZ YOK: her satır hükmün OKUNDUĞU alanın adını (`kaynak_alan`) taşır — üretici
       kanonik alanı taşıdığı sürece "ok" yazar; eski adlı bir yük sızarsa alan adı ve aşağıdaki
       sayaç onu GÖRÜNÜR kılar (geçiş haritası canlıda izlenir olur).
    2) `esanlamli_okumalar` — eski adların okunma sayaçları (ölüm tarihi ölçümü): uzun süre 0
       kalan eski ad, okuyucusu ölmüş demektir ve dönem sonunda DÜŞÜRÜLEBİLİR (karar Rol-1'de).
       Sayaç süreç-içidir (gerekçe modül başlığında); restart sıfırlar — tek artış bile "eski ad
       hâlâ okunuyor" hükmü için yeter, sıfırlanma o hükmü çürütmez ve bu beyan yanıtta taşınır.

    Okuyucu zinciri (YASA 6, elle kurulu — fonksiyon-düzeyi yüzeyleri codelaw göremez):
    durum_sozlugu modülü → bu uç → app.js `f8SozlukSatiri`. Çivi: tests/test_f8_durum_sozlugu_v271.py."""
    from . import durum_sozlugu as _dsz
    return {
        "kanonik": {
            "hukum": {"kanonik": _dsz.HUKUM_KANONIK, "esanlamli": list(_dsz.HUKUM_ESANLAMLI)},
            "neden": {"kanonik": _dsz.NEDEN_KANONIK, "esanlamli": list(_dsz.NEDEN_ESANLAMLI)},
            # T3.1/A4 (2026-08-23): sayaç ailesi de sözlüğe girdi — `report().ok` sayısı `n_ok`
            # oldu; eski ad eşanlamlı okunur ve "sayac:ok" anahtarıyla aşağıdaki sayaçta görünür.
            "sayac": {"kanonik": _dsz.SAYAC_KANONIK, "esanlamli": list(_dsz.SAYAC_ESANLAMLI)},
            "beyan": _dsz.BEYAN_KANONIK,
            "kol": {k: list(v) for k, v in _dsz.KOL_KANONIK.items()},
        },
        "satirlar": [_dsz.normalize_satir(ad, rapor) for ad, rapor in (bd or {}).items()],
        "esanlamli_okumalar": _dsz.esanlamli_okumalar(),
        "sayac_rejimi": ("süreç-içi — restart sıfırlar (bekçi süreç-içi mandallarıyla aynı "
                         "beyanlı karar: diske yazmak artifact_unread yüzeyi doğururdu)"),
        "beyan": ("F8 geçiş rejimi: üretici kanonik adı ÇİFT alan taşır, okuyucu önce kanonik "
                  "okur; eşanlamlı okuma sayaçlıdır. Sayaç 0 = bu süreçte hiçbir eski ad "
                  "okunmadı; eski adı DÜŞÜRME kararı Rol-1'de."),
    }


def _alarm_gunluk() -> dict:
    """Alarm hijyeninin GÜNLÜK sayacı — bekçi defterinin DIŞ okuyucusu burasıdır.

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


# ---- /api/diagnostics KISA ÖMÜRLÜ YANIT ÖNBELLEĞİ -------------------------
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
        → reconcile.*, ledgers, mirror akışı · `/api/alpaca/koruma_kur` → koruma bekçisi
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
# FIRSAT YÜZEYLERİ — OKUYUCUSUZ DEFTERLERİN UÇ TARAFI
# ----------------------------------------------------------------------------------------------
# ÖLÇÜLEN KUSUR SINIFI (docs/PATTERN-ETUDU-2026-08-06.md): "veri üretiliyor ama panoda
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
#   maliyet     → /api/hermes `spend_detay`   (kanonik spend yüzeyi — /api/spend EMEKLİ)
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
    """Reddedilen kararların karnesi — `near_miss.json`ın İLK uç tüketicisi.

    KÜNYE ZORUNLU VE BURADA TAŞINIR: defter `source: "yalnız-simüle"` / `n_real: 0` damgasını
    taşıyor. Künyeyi düşürüp yalnız sayıları servis etmek, simüle bir kanıtı gerçek kanıt gibi
    göstermek olurdu. Pano onu okumak ZORUNDA kalsın diye `_kaynak` aynı yükte gider."""
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
    """Onaylanan planın emir yaşam-döngüsü izi — `mirror_orders.json`ın ilk panosal okuyucusu.

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
    """Eylemsizlik: "Bugün neden hiçbir şey olmadı" — eylemsizliğin ADI, tek yerde toplanmış.

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
    """Gece hattının CANLI zaman çizelgesi — damgalar nihayet uca açılıyor.

    `saglik#cizelge` yüzeyi kurulurken şu BEYAN edilmişti: "'bu adım saat 03:12'de koştu'
    bilgisi bu uçtan GELMİYOR — adım başına damga `state/mechanism_beats.json`da var ama panoya
    açılmamış." Bu fonksiyon o borcu kapatır.

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
    # her olay penceresinden taşırır — daha önce ölçülen kusurun ta kendisi ("kart 'ölçülemedi'
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
            # F8/T3.1 (A4): `bekci_ok` bir SAYIDIR ve kanonik `n_ok`tan okunur; eski sayı-taşıyan
            # `ok` eşanlamlı (sayaçlı). Hüküm-ok buraya sızamaz — n_ok_oku bool'u elemekle yükümlü.
            "bekci_ok": __import__("meridian.durum_sozlugu",
                                   fromlist=["n_ok_oku"]).n_ok_oku(wd)[0],
            "bekci_total": wd.get("total")}


def _spend_detay() -> dict:
    """Gece koşusunun maliyet ve token karnesi.

    NEDEN /api/spend'E YENİ TÜKETİCİ BAĞLANMADI: o uç EMEKLİ edildi ve kaynağın kendi
    kuralı yazıyor — "bu uçlara YENİ tüketici bağlanmaz; kanonik yüzey /api/hermes `spend`".
    Kırılım o yüzden kanonik ucun içine, `spend.summary()`nin YANINA girer. Aynı defter iki uçtan
    iki farklı şekilde servis edilmez; yalnız kanonik olan zenginleşir.

    HESAP YOK, TOPLAM VAR: `cost_usd`/`in_tokens`/`out_tokens` satırlarda ZATEN yazılı; burada
    yalnız gruplanıyor. `cost_usd` alanını hiç taşımayan satır toplama 0 katkısıyla GİRER (ve `n`
    içinde sayılır), ama ayrıca `olculemeyen_satir` ile beyan edilir: toplam tek başına okunursa
    "bedava çağrı" gibi görünür, bu yüzden payda (`satir_n`) ve ölçülemeyen sayısı yanında durur.
    Pay ve payda AYNI kümeden (`rows`) tek geçişte sayılır — bkz. gövdedeki sayaç notu."""
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    rows = store.read_jsonl("spend.jsonl")
    if not rows:
        return _olculemedi("spend.jsonl boş ya da okunamadı — gece maliyeti bu turda ölçülemedi. "
                           "'Maliyet sıfır' DEĞİL: ölçüm defteri hiç yazılmamış olabilir.")
    ay = _dt.datetime.now(_dt.timezone.utc).isoformat()[:7]
    bu_ay = [r for r in rows if str(r.get("ts", ""))[:7] == ay]
    # PAY VE PAYDA AYNI KÜMEDEN SAYILIR. Bu sayaç eskiden `_topla` içinde `nonlocal` olarak
    # artıyordu; oysa `_topla` AYNI satırları defalarca gezer (toplam, bu_ay, modeller, kollar,
    # günler — beşi de `rows`un tamamını ya da bir dilimini kapsar), yani her eksik satır ~5 kez
    # sayılıyordu. Panoda alan `olculemeyen_satir/satir_n` biçiminde çiziliyor (app.js harcama
    # kartı), dolayısıyla kusur ekrana "5/2" gibi İMKÂNSIZ bir kesir olarak düşüyordu — payı
    # şişmiş bir dürüstlük sayacı, dürüstlüğün kendisini çürütür. Sayım artık paydayla AYNI
    # küme üzerinden, TEK geçişte yapılır.
    olculemeyen = sum(1 for r in rows if r.get("cost_usd") is None)

    def _topla(kume):
        """Bir satır kümesinin n/token/maliyet toplamlarını çıkarır (maliyet 4 haneye yuvarlanır).

        SAYIM ÖNCE, AYRIŞTIRMA SONRA: `n` her satır için koşulsuz artar — satır ayrıştırılabilse de
        ayrıştırılamasa da SAYILMIŞTIR. Alan bazında: eksik/None alan `or 0` ile 0 EKLENİR; yalnız
        `float()` ayrıştırması patlayan alan atlanır ve atlanan O ALANDIR, satır değil — satırın
        öteki alanları toplama girmeye devam eder. Eksik-maliyet sayacı burada TUTULMAZ: bu
        fonksiyon çakışan kümeler üzerinde birden çok kez çağrılır (yukarıdaki nota bak)."""
        c = {"n": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0, "thought_tokens": 0}
        for r in kume:
            c["n"] += 1
            for alan in ("in_tokens", "out_tokens", "cost_usd", "thought_tokens"):
                try:
                    c[alan] += float(r.get(alan) or 0)
                except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen (dizgi vb.) alan — `continue` iç döngüdedir, yani yalnız O ALAN atlanır; satır `n` içinde ZATEN sayılmıştır ve `olculemeyen_satir` sayacı ayrıca beyan edilir
                    continue
        c["cost_usd"] = round(c["cost_usd"], 4)
        return c

    def _grup(anahtar):
        """Tüm harcama satırlarını verilen alana göre gruplayıp her grubun toplamını döndürür.

        Alanı boş olan satırlar "—" adı altında toplanır; sonuç maliyete (sonra n'e) göre azalan
        sıralanır."""
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
            # Kota YÜZÜ ayrı bir iştir (ajan telemetrisi); bu kart harcamayı ölçer.


def _rollback_sicili() -> dict:
    """Otomatik geri-almanın sicili — PRODUCT.md'nin açık vaadinin İLK panosal kanıtı.

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
    """Regresyon kırılımı: "Bu sürüm neyi düzeltti, NEYİ BOZDU" — toplam skorun gizlediği tek şey.

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
        """Sayısal olanların ortalamasını 3 haneye yuvarlar; hiç sayı yoksa None döner (0 DEĞİL)."""
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
            """Eksen sözlüğünü {ad, n, avg_r, az_ornek} dilimlerine çevirip n'e göre sıralar.

            `az_ornek`, dilimin örneklemi görünürlük çizgisi `AZ`ın altındaysa işaretlenir —
            hüküm değil uyarıdır."""
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


# ---- DENETİM İZİNİN TAMAMI — SORGULANABİLİR UÇ -----------------------------------------
# ETÜDÜN KENDİ HÜKMÜ: "Tavanların kendisi bir performans kararıydı — çözüm tavanı
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
    # yansıma boyunca donuk kalır — pano "poll yapılmadı" diye okuyordu. Aynı süreçteki
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
    # İç HWM (pozisyonun trail_stop'u) vs Alpaca'ya giden son PATCH — yan yana + desync bayrağı
    last_patch = {t["ticker"]: t for t in (rc.get("trail_synced") or [])}
    hwm = []
    for tkr, p in (pf.get("positions") or {}).items():
        lp = last_patch.get(tkr, {})
        hwm.append({"ticker": tkr, "internal_trail": p.get("trail_stop"),
                    "last_patch_to": lp.get("to"), "patch_ok": lp.get("ok"),
                    "desync": bool(lp) and not lp.get("ok")})
    # Tek-değişken diff — son hipotezler (old→new + arama/onay etkisi)
    diffs = []
    for h in store.read_jsonl("hypotheses.jsonl")[-10:]:
        # DSR DAMGASI SHIP GEÇMİŞİNE TAŞINIR: kâğıt modunda düşük DSR ship'i BLOKLAMIYOR
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
    # Faz 4: parçalı dolum R-ayrıştırma matrisi — WS'in gördüğü filled_qty ile planın
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
    # Faz 4: son olasılıksal kapı koşusunun çan eğrisi (histogram hipotez kaydında taşınır)
    last_hist = None
    for h in reversed(store.read_jsonl("hypotheses.jsonl")):
        g = (h.get("backtest") or {})
        if g.get("search_hist"):
            last_hist = {"id": h.get("id"), "variable": h.get("variable"), **g["search_hist"]}
            break
    # UCB sıralaması (ısınma termometresinin 'öncelikler' yarısı) — defterden deterministik
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
    # TEK OKUMA ANI: `regime.json` ve karartma radarı AŞAĞIDA İKİ tüketici tarafından
    # okunuyor — `risk.regime`/`risk.blackout_radar` ve eylemsizlik özeti. İkisini ayrı ayrı
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
    # BEKÇİ RAPORU TEK KEZ: hem `watchdog` satırı hem sessiz hat okuyor. İki çağrı iki
    # okuma anı demektir ve aynı yanıtta iki farklı "kaç bekçi gecikti" cevabı doğabilirdi.
    _wd = __import__("meridian.watchdog",
                     fromlist=["report", "alarm_budget_cached", "liveness_report"])
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
    # ---- FAZ-6 KİLİT ZİNCİRİNİN ÜÇ GİRDİSİ TEK KEZ HESAPLANIR ----------------------------
    # `edge_verdict`/`result_verdict` blok-bootstrap CI koşuyor ve `validation_trio` DSR hesaplıyor.
    # Üçü hem kendi satırlarında hem kilit zincirinde okunuyor; ikinci kez çağırmak aynı istekte aynı
    # bootstrap'i iki kez koşturmak olurdu. AYNI NESNE paylaşılır — yoksa tek yanıtta "EDGE 3/5" ile
    # "kilit: EDGE 4/5" gibi iki farklı gerçek belirebilirdi (aynı istekte iki ayrı okuma anı).
    _edge_v, _sonuc_v, _trio_v = an.edge_verdict(), an.result_verdict(), an.validation_trio()
    # HAFTALIK KANIT RAPORU: DIŞ okuyucu burasıdır (yazan scheduler._weekly_validation) — dosya adı
    # LİTERAL yazılır, `codelaw.artifact_graph` statik graf olduğu için sabitten türetilen adı
    # çözemez ve artefakt "okuyucusu yok" diye görünürdü.
    _vrep = store.read_json("validation_report.json", None)
    # ELEME DEFTERİ TEK KEZ: hem `sieve` satırı hem `ogrenme.son_fit`in terfi hükmü okuyor.
    # İki çağrı iki okuma anı demektir ve aynı yanıtta "0 çift çıktı" ile "3 çift çıktı" gibi iki
    # farklı gerçek doğabilirdi (`_wd_rep` ile bire bir aynı gerekçe).
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
                # HAM BAYRAK YALAN SÖYLEYEBİLİR: dinleyici görevi ölse dosyadaki
                # `stream_ok: true` diskte DONAR ve pano "WS canlı" gösterir. Canlı kanıt:
                # stream_ok=true iken last_event_ts 3 gün eskiydi. Dürüst değer bayrağı nabız
                # tazeliğiyle çarpar; şerit "ne kadardır kopuk"u da buradan okur.
                **stream, "halted": health.halted(),
                "learn_halted": health.learn_halted(), "data_ok": hb.get("data_ok")},
        "scheduler": {"updated": sched.get("updated"), "last_tick": sched.get("last_tick"),
                      "poll_seconds": sched.get("poll_seconds"), "cycles": sched.get("cycles"),
                      # ÖĞRENME KADANSININ SEANS DAMGASI: zamanlayıcı seans-sonrası
                      # kancasında antrenman/Eksen-2/dolgu koşturuyor. "Hangi seans için koştu"
                      # sorusu buradan cevaplanır; koşunun İÇERİĞİ `ogrenme` bloğunda.
                      "learn_session": sched.get("learn_session"),
                      # TEMİZLİK KADANSLARININ DAMGALARI: "hangi seans için Y4
                      # topladı" ve "hangi hafta doğrulama üçlüsünü koştu". İçerikleri sırasıyla
                      # `saglayicilar` ve `mlops.validation_report`/`shadowlaw_drift` bloklarında.
                      "y4_session": sched.get("y4_session"),
                      "validation_week": sched.get("validation_week")},
        # SAĞLAYICI SAĞLIK KARTI — beş adaptörün sağlık sayaçları TEK yerde,
        # ortak biçimde. app.js'e bu turda DOKUNULMADI: alanlar hazır, pano turu bağlayacak.
        "saglayicilar": _saglayicilar(sched),
        # ÖĞRENME OTOMASYONU — antrenman durumu + Eksen-2 üreteci + dolgu kuyruğu,
        # üçü TEK blokta. app.js'e bu turda DOKUNULMADI: alanlar hazır, pano turu bağlayacak.
        # Neden mlops'un içinde DEĞİL: mlops kalibrasyon ÇIKTILARINI taşır (Brier, IC, kapı çanı);
        # burası o çıktıları ÜRETEN kadansların sağlığıdır. İkisini karıştırmak, "ölçüm kötü" ile
        # "ölçüm hiç koşmadı"yı aynı karta koymak olurdu — bu turun bulduğu kusurun ta kendisi.
        # `son_fit` zenginleştirmesi: kadans nabzı ile MODELİN son fiili fit'i AYRI iki
        # gerçektir; kart ikisini yan yana göstermezse "antrenman hiç koşmamış" okunur (operatör
        # şikâyeti). Zenginleştirme YENİ ÖLÇÜM ÜRETMEZ — `training_status`ın okuyucusuz
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
                      # AÇIK / KAPATILMIŞ AYRIMI: şeridi besleyen sayı yalnız `open`.
                      # Kapatılanlar pakette KALIR (tarihçe silinmez, sesi kısılır) — /api/alpaca
                      # aynı ayrımı uygular, iki uç aynı alanı iki farklı şekilde servis edemez.
                      "failed_submissions": health.split_rejections(rc.get("failed_submissions")),
                      # EMİR YAŞAM-DÖNGÜSÜ: `mirror_orders.json` bugüne kadar yalnız
                      # `_stream_view` için okunuyordu — coid başına status/filled_qty/
                      # filled_avg_price panoya HİÇ ulaşmıyordu. Evi `reconcile`: "emrin gerçekte
                      # ne olduğu" ailesi (partial_fills/failed_submissions ile aynı sözlük).
                      "emir_yasam": _emir_yasam()},
        # ---- İCRA GERÇEKLİĞİ — YASA 6 ZİNCİRİ ------------
        # Üç ölçüm de bugüne kadar HİÇBİR uçtan servis edilmiyordu, çünkü ikisi bugün doğdu ve
        # üçüncüsü (gece/gündüz) hiç sorulmamıştı. Neden `mlops` içinde DEĞİL: mlops öğrenme
        # kalibrasyonunun çıktılarıdır; burası EMRİN GERÇEKTE NE OLDUĞUdur (gönderildi mi, doldu
        # mu, kaça doldu, kâr hangi bacaktan geldi) — `reconcile` ile aynı aile.
        "icra": {
            # Gönderim/ret/veto sayıları, RET NEDENİ dağılımı (ölçüt:
            # `stop_vs_current` sınıfı sıfıra inmeli), iki bps dağılımı, iki-motor mutabakatı.
            "slipaj": an.entry_execution_summary(),
            # Kötümser maliyet bandının yürürlükteki hâli + slipaj ölçümünden AMPİRİK güncelleme.
            # `ampirik_bps` None ise ölçüm henüz yok — 0.0 yazmak "maliyet yok" demek olurdu.
            "kotumser_band": an.pessimistic_band_update(),
            # Her işlemin tutuş yolu gece (close→open) / gündüz (open→close) bacaklarına
            # ayrılmış hâli + kaynak damgası (training ayrı) × tutuş dilimi çapraz tablosu.
            "gece_gunduz": an.night_day_split(),
        },
        "risk": {"regime": _rejim_doc,
                 "blackout_radar": _radar,
                 # KAZANÇ TAKVİMİNİN PIT BİRİKİM DEFTERİ — `earnings.csv` tek anlık
                 # görüntüdür ve her tazeleme geçmişi EZER; defter "bu tarihler bu fetch gününde
                 # biliniyordu"yu biriktirir. DIŞ OKUYUCU BURASIDIR (YASA 6): sayaç panoya çıkar,
                 # asıl tüketici gelecekteki ölçüm turlarıdır.
                 # DOSYA ADI LİTERAL OKUNUR (trend_book.json ile aynı desen ve aynı gerekçe):
                 # `codelaw.artifact_graph` statik bir graftır; okuma `earnings` modülünün içinde
                 # kalsaydı defter "yazılıyor ama kimse okumuyor" görünürdü. Maliyet ölçülü: kadans
                 # HAFTALIK, yani ~52 satır/yıl — anket başına birkaç ms'lik ayrıştırma.
                 "earnings_pit": earnings.snapshot_stats(
                     store.read_jsonl("history/earnings_snapshots.jsonl")),
                 "halted": health.halted(), "learn_halted": health.learn_halted(),
                 # "BUGÜN NEDEN HİÇBİR ŞEY OLMADI". Alanların HEPSİ bu blokta ZATEN
                 # vardı (bütçe, karartma radarı, halt) ama hiçbiri eylemsizliğin ADI olarak
                 # okunmuyordu — pano dürüsttü ("aday yok") ve NEDENSİZDİ. Dört kaynak ÇAĞIRANIN
                 # elinden geçer (hb/regime/gk_plans/radar); ikinci kez okunsalardı aynı yanıtta
                 # iki farklı gerçek doğardı.
                 "eylemsizlik": _eylemsizlik(hb, _rejim_doc, gk_plans, _radar)},
        "mlops": {"recent_hypotheses": diffs, "deflate": an.deflate_stats(),
                  "deflate_why": an.deflate_why(), "gate_hist": last_hist,
                  "llm_calibration": store.read_json("llm_calibration.json", {}),
                  "exit_efficiency": store.read_json("exit_efficiency.json", None),
                  # REDDEDİLEN KARARLARIN KARNESİ: `near_miss.json`ın İLK uç
                  # tüketicisi. Kardeşleri `exit_efficiency` ve `mae_profile` ile AYNI üretici
                  # (P5 kalibrasyonları) — evi de bu yüzden burası. Künye (`yalnız-simüle`,
                  # `n_real: 0`) yükle BİRLİKTE gider; ayrılırsa simüle kanıt gerçek gibi okunur.
                  "near_miss": _near_miss_karne(),
                  "gate_calibration": store.read_json("gate_calibration.json", {}),
                  "score_calibration": store.read_json("score_calibration.json", None),
                  # ---- KENAR SAĞLIĞI: dört ölçüt TEK yükte, çünkü pano Bölüm 3'te tek
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
                  # SPY-VETO ADAYININ SAYACI: `vs_benchmark_at_ship` her ship'e
                  # damgalanıyor ama hiçbir yerde raporlanmıyordu — "20-30 gözlem birikince veriyle
                  # karar verilir" eşiğinin sayacı yoktu, yani karar anı asla tetiklenmeyecekti.
                  "benchmark_veto_tally": _benchmark_veto_tally(),
                  "prediction_hit": an.prediction_hit_rate(),
                  # DÖRT ÖLÇÜTÜN TEK HÜKMÜ: dört sayıyı yan yana koymak, okurdan her
                  # bakışta yazılı olmayan bir birleştirme işlemi ister — ve o işlem her seferinde
                  # farklı çıkar. Eşikler analytics'te tek yerde; buradan servis edilen cümle onlardan
                  # TÜREVDİR. Alt ölçütler yukarıda ayrıca duruyor: hüküm onların yerine geçmez.
                  "edge_verdict": _edge_v,
                  # SONUÇ HÜKMÜ — EDGE'İN İKİZİ, DOLAR MERCEĞİ. EDGE
                  # "kenar var mı?"yı R biriminde sorar; R birimi geniş stopa YAPISAL önyargılı,
                  # yani sermaye kararı tek başına ona bırakılamaz. Bu hüküm aynı
                  # defteri DOLAR biriminde yargılar: friksiyon-sonrası işlem başına beklenti
                  # (blok-bootstrap CI) + profit factor + maks düşüş + net PnL vs ödenen friksiyon.
                  # KARAR KULLANIMI: rafineri kararları EDGE'e, sermaye/silahlanma İKİSİNE bakar.
                  "result_verdict": _sonuc_v,
                  # ATRİBÜSYON KABLOSU: işlem-penceresi alfa/beta + aile ×
                  # rejim × tutuş-dilimi kırılımı. `result_verdict.beta_duzeltilmis` ile AYNI
                  # NESNEDİR (yeniden hesaplanmaz): `trade_alpha_beta` SPY barlarını diskten
                  # okuyor ve aynı istekte iki kez çağrılsaydı hem boşuna iş yapılır hem de tek
                  # yanıtta iki farklı okuma anı doğardı (edge/result/trio üçlüsüyle aynı gerekçe).
                  # ADVISORY: hiçbir kapıya bağlı değil, dört dolar ölçütünü DEĞİŞTİRMEZ.
                  "alpha_beta": _sonuc_v.get("beta_duzeltilmis"),
                  # DEFTERİN KAYNAK SAYAÇLARI: teşhis sayfası "ölçüm zemini" sorusunu
                  # burada cevaplar — kaç satır canlı kanıt, kaç satır replay tohumu (training),
                  # kaç satır ayırt edilemedi. /api/today AYNI saf fonksiyonu çağırır.
                  "ledger_source": __import__("meridian.ledgerstamp",
                                              fromlist=["counts"]).counts(),
                  # PORTFÖY ISISI: masadaki toplam açık risk tek sayı + NAV yüzdesi. YALNIZ
                  # GÖSTERGE — bu turda hiçbir kapıya bağlı değil (ısı tavanı
                  # default-OFF bir knob). `today.current_exposure_pct` GİRİŞTEKİ riski toplar;
                  # buradaki sayı YÜRÜRLÜKTEKİ stopa göredir ve ikisi bir kazananda ayrışır.
                  "portfolio_heat": an.portfolio_heat(),
                  # DOĞRULAMA ÜÇLÜSÜ: DSR (deneme-sayısı düzeltmeli Sharpe) + PBO/CSCV
                  # + sorgu sayacı yan yana. ÜÇÜ DE ADVISORY — kapı passes semantiği DEĞİŞMEDİ.
                  # `validation_ledger.jsonl`ın dış tüketicisi bu zincirdir (YASA 6): validation.py
                  # yazar → analytics.validation_trio okur → bu uç servis eder → pano gösterir.
                  "validation_trio": _trio_v,
                  # HAFTALIK KANIT RAPORUNUN ÖZETİ. `validation_report`
                  # modülü "hangi mekanizma/edge KANITLANIYOR?" tablosunu öteden beri
                  # üretebiliyordu ve TEK çağıranı kendi `__main__` bloğuydu — yani rapor ancak
                  # biri elle koşturursa vardı. Artık haftalık kadans üretiyor (scheduler), bu uç
                  # okuyor: YASA 6 zinciri tam (yazan scheduler → okuyan api → pano).
                  # ÖZET SERVİS EDİLİR, TAM METİN DEĞİL: `metin` alanı ~30 satırlık insan-okur bir
                  # rapordur ve her pano isteğinde taşınması saf yüktür; dosya state'te duruyor.
                  # `validation_trio` ile KARIŞTIRILMAMALI — o DSR/PBO kilitleridir, bu edge tablosu.
                  "validation_report": ({k: _vrep.get(k) for k in
                                         ("uretildi", "hafta", "evidence_base", "base_edge",
                                          "cf_fidelity")} if _vrep else None),
                  # MEASURED_V3 KAYMA BEKÇİSİNİN SON ÖLÇÜMÜ: yasa
                  # sabitlerinin (MONEY_GATE_MARGIN, DD_VETO_MARGIN) türetim tabanı hâlâ yerinde mi.
                  # `kayma` BOŞ LİSTE = sınandı ve geçti; None = bu süreçte/haftada HİÇ ölçülmedi.
                  "shadowlaw_drift": sched.get("shadowlaw_drift"),
                  # ---- FAZ-6 KİLİT ZİNCİRİ: BEŞ KİLİT, TEK YERDE ADLANDIRILMIŞ ----------
                  # "Dört kilit" cümlesi bugüne kadar hiçbir yerde makine okunur
                  # değildi — yani denetçisi yoktu. Beşinci kilit (yürürlükteki pencerede DSR > 0.95
                  # ölçülü ve geçer) bu turda eklendi ve zincir `health.faz6_kilitleri`de yazılı.
                  # SAF OKUMA: hiçbir şey silahlamaz. Eşik ship yoluyla AYNI sabitten gelir.
                  "faz6_kilitleri": health.faz6_kilitleri(edge=_edge_v, sonuc=_sonuc_v,
                                                          trio=_trio_v),
                  # BÜYÜKLÜK YASASI SATIRI — **TERS GÖLGELEME** (PARA-v3). DİKKAT: bu
                  # alanın anlamı önceki düzene göre TERSİNE döndü ve adı (`shadow_law`) tarihsel sebeple
                  # KORUNDU (tüketicisi app.js'te `ml.shadow_law`; anahtar yeniden adlandırılsa
                  # pano sessizce boş çizerdi). Önceden "v2 OLSAYDI" alanıydı: karar eski bileşik
                  # skordaydı, v2 kayda geçiyordu. ARTIK: karar PARA-v3'te, ESKİ bileşik yasa kayda
                  # geçiyor. Satır DÖRT şeyi birlikte söyler: (a) yürürlükteki yasa PARA-v3'tür ve
                  # `passes`i O üretir (`law_transition: True`); (b) PARA'nın varyans payı %0,3 →
                  # %100; (c) skordan çıkan düşüş/Sharpe bacaklarının NEREYE gittiği (sert vetolar —
                  # yoksa "korumayı kaldırdılar" diye okunur); (d) eski yasanın son hükmü + ıraksama
                  # sayacı. Geçiş YAPILDI; operatör kararı ALINDI ("1 numaradan başla").
                  "shadow_law": an.shadow_law_row(),
                  # MAE KARNESİ: `exit_efficiency`in ikizi — MFE çıkış kuralını,
                  # MAE STOP kuralını yargılar. `mae_r` 95 satırın hepsinde vardı ve tüketicisi
                  # YOKTU (YASA 6): stop mesafesinin karnesi hiç ölçülmüyordu.
                  "mae_profile": store.read_json("mae_profile.json", None),
                  # GÖLGE-VARYANT ÖZET KARTI: sadeleştirme turu bu defteri
                  # `codelaw.DECLARED_SINKS`e SÜRELİ beyanla koymuştu ("pano/api tüketicisi
                  # devredildi"). Devir BURADA tamamlandı ve o beyan satırı KALDIRILDI — varyant
                  # başına son karar + kümülatif ayrışma sayısı panoya çıkar.
                  "shadow_variants": an.shadow_variant_summary(),
                  # HERMES KARNESİ: beynin KENDİ tahmin isabeti + ölü aileleri + hiç
                  # denenmemiş düğmeleri + bileşik kuyruk durumu. Aynı sözlük evidence_pack yoluyla
                  # PROMPT'a da giriyor — pano ve beyin AYNI karneyi görür (iki gerçek olmasın).
                  "hermes_scorecard": an.hermes_scorecard(),
                  # NOUS SİSTEM ÖNERİLERİ: beynin MEKANİZMA düzeyindeki
                  # haftalık önerileri + KALİTE KAPISI istatistiği (kaç öneri kanıt-atıfsız düştü).
                  # Düşme sayısı kartta GÖRÜNÜR: kapı sessiz çalışırsa "4 öneri üretti" ile "9
                  # üretti, 5'i düştü" aynı görünür ve ikincisi beynin karnesi hakkında çok daha
                  # fazla şey söyler. TELEMETRİ PAKETİ BURADA SERVİS EDİLMEZ: `system_telemetry`
                  # 12 üreticiyi (bootstrap CI'lar dahil) çağırır ve her pano isteğinde yeniden
                  # hesaplanması saf bir maliyet olurdu — paketin tüketicisi prompt ve `--ozet`.
                  "improvement_proposals": an.improvement_proposals_status(),
                  # NOUS ÖNERİ FİŞLERİ (otomatik yönlendirme borusu). DOSYA ADI LİTERAL
                  # yazılır ve okuma DIŞ modülde (burada) yapılır — `codelaw.artifact_graph`
                  # "kendi yazdığını kendi okuyan tüketici değildir" der; `nous_eval` içinden
                  # okunsaydı defter `artifact_unread` olarak görünürdü (aynı gerekçe:
                  # analytics.improvement_proposals_status).
                  # NİYE AYRI DEFTER: `improvement_proposals.jsonl` KABUL EDİLENLERİN kaydıdır ve
                  # sözleşmesi "akıbet alanı YOKTUR" der (akıbet zamanla değişir, damga yalan
                  # söyler). Fiş ise operatörün İŞ KALEMİdir; durumu zamanla değişir ve kendi
                  # defterinde yaşamak zorundadır.
                  "nous_fisler": _nous_fisler(),
                  # REJİM/RİSK DÖRTLÜSÜ: dördü de DEFAULT-OFF. VIX bacağı ayrıca `veri_yok`
                  # (Massive 403 / FMP boş — doğrulandı) ve knob açılsa bile karar üretmez.
                  "y3_entry_gates": _y3_gate_row(),
                  # OTOMATİK GÖLGE DUYURUSU: otonom bir karar SESSİZ KALMAZ. Dosya adı
                  # literal (statik graf sabitten türetilmiş adı çözemez → artefakt "okuyucusu yok"
                  # görünürdü). PROTECTED beşlisi ASLA bu listede olamaz.
                  "skill_auto_shadow": store.read_json("skill_auto_shadow.json", None),
                  # EMPİRİK BAYES KÜÇÜLTME: küçük hücrenin ekstrem değeri büyük ölçüde
                  # GÜRÜLTÜDÜR ve "en kötü rejim" seçimi tam onu seçer. Panoda "küçültülmüş"
                  # ETİKETİYLE gösterilir; verdict TABANLARINA GİRMEZ (küçültme n'i büyütmez).
                  "shrunk_regime_cells": an.shrunk_regime_cells(),
                  "shrunk_component_ic": an.shrunk_component_ic(),
                  # HOLDOUT ROTASYON ÖNERİSİ: aşınma eşiği aşıldığında ÖNERİ üretir,
                  # UYGULAMAZ — pencere değişimi geçmiş kapı kayıtlarının karşılaştırılabilirliğini
                  # keser ve operatör kararıdır.
                  "holdout_rotation": an.holdout_rotation_advice(),
                  # BİLEŞEN IC TABLOSU: "skorun IC'si sıfır" ile "skorun
                  # hiçbir parçası bilgi taşımıyor" aynı cümle değildir. Dört bileşenin ayrı IC'si
                  # ancak burada dışarı verilirse pano ve operatör onu görebilir (YASA 6 — üreten
                  # modülün kendi dosyasını okuması tüketici saymaz).
                  # Dosya adı LİTERAL yazılır (sabitten türetilmez): `codelaw.artifact_graph` statik
                  # bir graftır ve değişkenden gelen adı ÇÖZEMEZ — artefakt o zaman "okuyucusu yok"
                  # diye görünmez olur, YASA 6 denetimi de onu hiç göremez.
                  "component_ic": store.read_json("component_ic.json", None),
                  # MIN_SCORE EŞİK EĞRİSİ: "kapıyı yükseltsek kâr artar mı?"
                  # sorusunun tek ölçüm yüzeyi. Dilim istatistiği ile tam replay 07-28'de ÇELİŞTİ
                  # (60→80 replay'de Δ-0.095); eğri o çelişkiyi panoda görünür tutar.
                  "threshold_curve": store.read_json("threshold_curve.json", None),
                  # KÂR ŞELALESİ: "edge var mı?" ile "para var mı?" ayrı sorular.
                  # Sinyalin sunduğu (MFE) → çıkışın geri verdiği → friksiyon → net ayrıştırması,
                  # exit_reason kırılımıyla. Saf hesap (dosya yok) — bu yüzden fonksiyon çağrısı.
                  "profit_waterfall": an.profit_waterfall(),
                  # OOS AŞINMASI: kapı hükümlerinin ne kadar yıprandığı,
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
        # `alarm_gunluk` sonradan EKLENDİ: bekçi raporu "şu an ne bayat" der, günlük sayaç "bugün kaç
        # alarm yazıldı, kaçı tavana takıldı, kaçı askıdaydı" der. İkincisi olmadan alarm hijyeni
        # ölçülemez — ve ölçülmeyen bir susturma, susturmanın kendisinden daha tehlikelidir.
        "watchdog": {**_wd_rep, "alarm_gunluk": _alarm_gunluk()},
        # CANLILIK: kadans nabzı ("dişli döndü mü") ≠ canlılık ("dişlinin ürettiği
        # iş yaşıyor mu"). `watchdog` (report) sprint_cadence/shadow_fit'i penceresinde sayabilir
        # AMA sprint çocuğu ölü / hipotez defteri donuk olabilir — o sahte-yeşil bu satırda
        # GERÇEĞE bağlanır (sprint orphan + öğrenme durması, ölçülüp BEYAN edilerek). Alarm geçişi
        # `check_liveness_and_alarm` (300 sn poll); bu satır teşhis paneline okunur.
        "liveness": _wd.liveness_report(),
        # BEKÇİ DURUM YÜZEYLERİ — T2.1-T2.4 YASA-6 kapanışı: dört raporun alarm satırı vardı,
        # durum yüzeyi yoktu. Maliyet/yalıtım/persist şerhleri `_bekci_durumlari`nın kendisinde.
        # WALRUS BİLEREK: aynı dört rapor hem burada olduğu gibi hem `durum_sozlugu.satirlar`da
        # normalize servis edilir — ikinci bir `_bekci_durumlari()` çağrısı dört bekçiyi aynı
        # istekte İKİ kez koşturmak olurdu (45 sn önbelleğin kapattığı maliyeti geri açardı).
        "bekci_durumlari": (_bd := _bekci_durumlari()),
        # F8 KANONİK DURUM SÖZLÜĞÜ (WP8-C) — kanonik ad kümeleri + normalize hükümler +
        # eşanlamlı-okuma sayaçları (eski adların ölüm tarihi ölçümü). Okuyucu: app.js
        # `f8SozlukSatiri` (Gözetim & Alarmlar). Şerhler `_durum_sozlugu`nun kendisinde.
        "durum_sozlugu": _durum_sozlugu(_bd),
        # CANLI ZAMAN ÇİZELGESİ — BEKÇİNİN YANINDA, İÇİNDE DEĞİL. Bekçi raporu
        # "geciken var mı?" der; çizelge "adım adım NE ZAMAN koştu?" der. İkisi aynı dosyadan
        # (mechanism_beats.json) beslenir ama farklı soruların cevabıdır; `watchdog` içine
        # gömmek, gecikme raporunu bir zaman serisiyle şişirmek olurdu.
        # BEYANLI BORÇ BURADA KAPANIYOR: "adım başına damga … panoya açılmamış."
        # (app.js `RENDER.cizelge` başlığı).
        "cizelge": _hat_cizelgesi(_wd_rep, sched),
        # SESSİZ HAT — bekçi + kilit + tazelik TEK Level-1 toplaması. `_wd_rep` AYNI
        # NESNEDİR: bekçi raporunu ikinci kez çağırmak, aynı yanıtta "bekçi 17/17" ile
        # "sessiz hat 16/17" gibi iki farklı gerçek doğurabilirdi (iki ayrı okuma anı).
        "sessiz_hat": _sessiz_hat(_wd_rep, hb),
        # ALARM BÜTÇESİ — EEMUA 191 merceğiyle son 24 sa. `_age` DIŞARI VERİLİR:
        # önbellekli bir sayıyı taze gibi göstermek bu deponun kovaladığı kusur sınıfıdır.
        "alarm_butcesi": {**_alarm_rep, "yas_s": _alarm_age},
        "hotstate": hot,          # Redis sıcak katman (intraday) — down GÖRÜNÜR olmalı, sessiz değil
        "marketstream": __import__("meridian.marketstream", fromlist=["health"]).health(),   # Faz 2 data akışı; ok:None/down görünür
        "barfeed": __import__("meridian.barfeed", fromlist=["health"]).health(),             # Faz 3 dayanıklı bar-tetiği (consumer-group)
        "intraday": _intra,          # Faz 4 gözlem-modu + intraday_decisions.jsonl özeti (dış okuma)
        # TREND KOLU GÖLGE-KİTABI — incumbent kolunun CANLI sanal
        # defteri. DIŞ OKUYUCU BURASIDIR (YASA 6): defteri `trend_shadow` yazar, `intraday_shadow`
        # ile AYNI desen — dosya adı LİTERAL okunur ki `codelaw.artifact_graph` tüketiciyi görsün;
        # okuma modülün kendi içinde kalsaydı artefakt "yazılıyor ama kimse okumuyor" görünürdü.
        # `pit_serh` özetin İÇİNDE taşınır ve panoya rakamla BİRLİKTE çıkar: +13,1p/yıl'ı şerhsiz
        # okutmamak bu kolun hükmünün parçasıdır (yanlılık-düşülmüş ~6-7p/yıl).
        "trend_kitabi": __import__("meridian.trend_shadow", fromlist=["ozet"]).ozet(
            store.read_json("trend_book.json", None)),

        # BÜTÜNLÜK: "koşuyor mu" değil "üretiyor mu / kaybetmiyor mu / deterministik mi"
        # ÖNBELLEKLİ OKUMA: `integrity_report_cached` yalnız BURASI için var; yan
        # etkili `persist=True` yolunu (taban ilerlemesi, mutasyon kararı) hiç kullanmaz.
        # `integrity_age_s` dışarı verilir: pano raporun kaç saniye önce hesaplandığını söyler,
        # taze gibi göstermez. 0.0 = bu istekte hesaplandı.
        "integrity": _integrity_rep,
        "integrity_age_s": _integrity_age,
        # DAĞITIM BEYANI — YASA-6 orphan kapaması (2026-08-23): `dagit.sh` [B] adımı canlıya
        # `state/dagitim.json` yazıyor (deployed_sha + dagitildi_utc + dagitan_host +
        # kirli_gec_kullanildi) ama hiçbir canlı yüzey onu OKUMUYORDU — üretilip tüketilmeyen
        # kanıt. Okuyucu burasıdır; pano (app.js Gözetim) tek satırla basar. Dosya yoksa None
        # DEĞİL, adlı boşluk: "hiç dağıtım olmadı" ile "beyan yazılamadı" ayrımını dagit.sh'ın
        # kendi düşme mesajı taşır; buradan söylenebilecek dürüst cümle yalnız beyanın YOKLUĞUDUR.
        "dagitim": (store.read_json("dagitim.json", None)
                    or {"olculemedi": "state/dagitim.json yok — henüz beyanlı dağıtım yok "
                                      "(dagit.sh [B] adımı ilk koşumda yazar)"}),
        "coverage": __import__("meridian.integrity_registry", fromlist=["coverage_report"]).coverage_report(),
        # evren sapması: elle bakımlı 250'lik listede endeksten düşmüş isim var mı
        "universe_drift": store.read_json("universe_drift.json", None),
        "pipeline": {"cf_fidelity": store.read_json("cf_fidelity.json", None),
                     "refetch_attempts": sched.get("refetch_attempts", 0), "refetch_max": 8,
                     "last_refetch_session": sched.get("last_refetch_session"),
                     "earnings_attempts": sched.get("earnings_attempts", 0),
                     "quarantine": dq.get("tickers_failed") or [],
                     # KAYNAK DİKİŞİ: uyarı susturuldu ama DURUM görünür kalmalı — kaç sembolün
                     # geçmişi artık yayın yapmayan bir kaynağa sabitli?
                     "bar_source_seams": __import__("meridian.adapters.data",
                                                    fromlist=["seam_report"]).seam_report(),
                     # VERİ DÖNMEYEN SEMBOLLER: "kaynak hatası" ile "sembol yok" AYRI şeylerdir —
                     # ilki geçici (429), ikincisi evren bakımı gerektirir. 18 sağlıklı sembol
                     # yalnız throttling yüzünden "ölü" sanılabilirdi.
                     "symbol_no_data": __import__("meridian.adapters.data",
                                                  fromlist=["no_data_report"]).no_data_report(),
                     "crosscheck": store.read_json("index_crosscheck.json", {}),
                     # MASSIVE ÇAPRAZ-KONTROL — BEYAN EDİLEN OKUYUCU NİHAYET
                     # ÇAĞRILIYOR. `codelaw.DECLARED_SINKS` massive_crosscheck.json'u
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
                     # YASA 6: fmp_usage.json her istekte YAZILIYOR ama `fmp.usage()`
                     # erişimcisini kod içinde kimse çağırmıyordu — kota telemetrisi diskte birikip
                     # görünmez kalıyordu. 429 kesintileri tam bu sayıdan okunur.
                     "fmp_usage": __import__("meridian.adapters.fmp", fromlist=["usage"]).usage(),
                     # FINVIZ — /api/hermes'ten TAŞINDI: evren keşif kaynağının
                     # sağlığı hermes yükünde servis ediliyordu ve hiçbir yüzeyi yoktu (app.js'teki
                     # finviz geçişleri /api/market src.finviz_extra ve sırlar ekranıydı). Kaynak
                     # sağlığı pipeline kartına aittir — seam_report/no_data_report'un yanına.
                     # Token son-4 maskeli döner (sır sızdırmaz).
                     "finviz": __import__("meridian.adapters.finviz", fromlist=["status"]).status(),
                     "io": store.io_stats()},
        "ledgers": {"cf_open": len(store.read_json("cf_open.json", [])), "cf_cap": 2500,
                    "cf_resolved": len(store.read_jsonl("counterfactuals.jsonl")),
                    "trades": len(store.read_jsonl("trades.jsonl"))},
        # DEFTER SÖZLEŞMESİ: sayaç "defter dolu mu" der, sözleşme "içindekiler söz
        # verdiği alanları taşıyor mu" der. Bugünün altı hatasının kökü ikincisiydi.
        "ledger_contract": __import__("meridian.ledgers", fromlist=["report"]).report(),
        # ELEME MUHASEBESİ: "veri yok" ile "veri elendi" ayrı şeylerdir. Hangi satırın NEDEN
        # düştüğü sayılmazsa, sessiz eleme ekranda "henüz kanıt birikmedi" gibi okunur.
        "sieve": _sieve_rep})                 # tek okuma anı — yukarıda hesaplandı


# ---------- Hermes (the reflection brain) ----------
@app.get("/api/hermes")
def api_hermes(request: Request):
    """Hermes status + spend + last proposals for the dashboard's Hermes section."""
    _auth(request)
    from . import hermes_runtime, spend, skills, scheduler, sprint
    hyps = memory.all_hypotheses()
    from . import hermes as _hm
    return {"status": hermes_runtime.status(), "spend": spend.summary(),
            # GECE MALİYET/TOKEN KARNESİ. `spend.summary()` aylık TOPLAMI verir;
            # "hangi kol yedi, hangi model yedi, hangi gece?" sorusu çağrı-başına kırılım ister ve
            # o kırılım `spend.jsonl`de ZATEN yazılı, hiçbir uçtan servis edilmiyordu.
            # NEDEN /api/spend'E BAĞLANMADI: o uç EMEKLİ ("bu uçlara YENİ tüketici bağlanmaz
            # — kanonik yüzey /api/hermes `spend`"). Kırılım o yüzden kanonik ucun İÇİNDE doğar.
            "spend_detay": _spend_detay(),
            "autostart": os.environ.get("MERIDIAN_AUTOSTART_HERMES") == "1",
            "recent": list(reversed(hyps))[:8],
            "skill_recommendations": _oneriler_karar_damgali(),          # Axis-2 (operator applies)
            "skill_count": len(skills.catalog()),
            "learning": analytics.learning_scorecard(),                  # honest "is it learning?" scorecard
            "scheduler": __import__("meridian.scheduler", fromlist=["status"]).status(),
            "sprint": sprint.status(),                                   # öğrenme antrenmanı (sandbox loop-closer)
            "integrations": _hm.integrations_status(),                   # MCP/hook/cache/pool + görüş dolgusu
            # ---- BEŞ ÖLÜ SAĞLIK BLOĞU EMEKLİ EDİLDİ ---------------------------------------
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
    """`POST /api/hermes/{action}`: yerel ajan denetimi. YETKİLİ ve YAN ETKİLİ uç.

    Tanınan eylemler: `start`/`stop` (ajan koşucusu), `backfill` (görüş dolgusunu arka planda
    başlatır — tavan `hermes.backfill_budget()`ten gelir, bu uçtan `max_days` VERİLMEZ),
    `sync_integrations` (MCP/hook/cache/pool ayarlarını tazeler). Başkası 400 döner. Gerçekten
    iş gören her dalda teşhis önbelleği boşaltılır."""
    _auth(request)
    from . import hermes_runtime, hermes
    if action in ("start", "stop"):
        out = _ogrenme_kumanda(action)
        _diag_onbellek_bosalt(f"hermes_{action}")
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


OGRENME_BIRIMI = "meridian-learn"


def _ogrenme_kumanda(action: str) -> dict:
    """Pano `start`/`stop` düğmelerini DOĞRU sürece yönlendirir (ROADMAP Ö-50).

    NEDEN VAR — BU BİR EMNİYET KAPISIDIR, kolaylık değil: öğrenme döngüsü artık
    `meridian-learn.service` biriminde koşuyor ve bu süreçte `MERIDIAN_AUTOSTART_HERMES=0`.
    Düğme eskisi gibi `hermes_runtime.start()` çağırsaydı, döngüyü TAM DA BOŞALTTIĞIMIZ YERDE —
    API sürecinin içinde — yeniden başlatırdı: ölçülen arıza (GIL çekişmesi, pano 2,6-14,0 sn)
    bir düğmeye basmakla geri gelirdi.

    İKİ KİP, ve hangisinde olduğumuz VARSAYILMAZ, `MERIDIAN_AUTOSTART_HERMES`ten OKUNUR:
      "1" → döngü BU süreçte (yerel geliştirme, `serve.sh`): eski süreç-içi yol aynen korunur.
      aksi → döngü AYRI birimde: `systemctl start|stop meridian-learn`.

    Tetik komutu `sprint._systemctl_komutu()`den gelir — ikinci bir uygulama YAZILMADI. O fonksiyon
    `NoNewPrivileges` altında `sudo`nun geçmeyebileceğini ve operatörün polkit yolunu seam olarak
    zaten çözmüş durumda; aynı yasanın iki uygulaması bu depoda tekrar eden kusurdur."""
    from . import hermes_runtime, sprint
    if os.environ.get("MERIDIAN_AUTOSTART_HERMES") == "1":
        if action == "start":
            return {**hermes_runtime.start(poll_seconds=int(os.environ.get("HERMES_POLL_SECONDS", "300"))),
                    "kip": "surec_ici"}
        return {**hermes_runtime.stop(), "kip": "surec_ici"}
    onek, sebep = sprint._systemctl_komutu()
    if onek is None:
        # UYDURMA YASAĞI: "durduruldu" demek bir iddiadır. Komut kurulamadıysa hiçbir şey olmadı.
        return {"ok": False, "kip": "birim", "birim": OGRENME_BIRIMI, "action": action,
                "neden": sebep, "detail": f"systemctl tetiği kurulamadı ({sebep}) — HİÇBİR ŞEY YAPILMADI; "
                                          f"operatör: systemctl {action} {OGRENME_BIRIMI}"}
    import subprocess
    komut = [*onek, action, f"{OGRENME_BIRIMI}.service"]
    try:
        p = subprocess.run(komut, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        obs.warn("ogrenme_birimi_kumanda_dustu", action=action, error=f"{type(e).__name__}: {e}")
        return {"ok": False, "kip": "birim", "birim": OGRENME_BIRIMI, "action": action,
                "neden": f"{type(e).__name__}: {e}"}
    ok = p.returncode == 0
    (obs.log if ok else obs.warn)("ogrenme_birimi_kumanda", action=action, rc=p.returncode,
                                  stderr=(p.stderr or "").strip()[:300])
    return {"ok": ok, "kip": "birim", "birim": OGRENME_BIRIMI, "action": action,
            "rc": p.returncode, "stderr": (p.stderr or "").strip()[:300]}


# ---------- paper-advance scheduler (keeps the local agent from freezing) ----------
# K1-EMEKLİ: kanonik yüzey /api/hermes `scheduler`. Yeni tüketici bağlanmaz.
@app.get("/api/scheduler")
def api_scheduler(request: Request):
    """`GET /api/scheduler` (EMEKLİ): zamanlayıcı durumunu döner. Yetkili, salt-okuma.

    Kanonik yüzey `/api/hermes` `scheduler` alanıdır — buraya YENİ tüketici bağlanmaz."""
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
    """`GET /api/sprint` (EMEKLİ): öğrenme sprintinin durumunu döner. Yetkili, salt-okuma.

    Kanonik yüzey `/api/hermes` `sprint` alanıdır — buraya YENİ tüketici bağlanmaz."""
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
    """`POST /api/sprint/stop`: koşan öğrenme sprintini durdurur. YETKİLİ ve YAN ETKİLİ.

    Yalnız kum havuzundaki alt süreci sonlandırır — canlı kitaba dokunmaz. Ardından teşhis
    önbelleği boşaltılır."""
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
            # uçlar arası hâli.
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

    E1 YASASI ARTIK TEK KAPIDAN: bu uç EskİDEN kendi gönderim mantığını
    kuruyordu — `alpaca.submit_plan(p, eq)` çıplak varsayılanlarıyla. Yani de-risk çarpanı YOK
    (%5 düşüşte döngü 0,6 ile doldururken düğme TAM boyut gönderiyordu), atr/ref_price YOK (aynı
    planda iki farklı limit tavanı + gap dalında kırılım teyidinin tümden kalkması), dedup YOK
    (`alpaca_submitted` ne okunuyor ne yazılıyordu → döngü aynı planı ikinci kez gönderip
    duplicate-coid reddi alınca planı SİLAHLI kümeden düşürüyordu), E2 satırı YOK, ve hesap
    okunamazken 100k sabitine düşüp hayali sermaye üzerinden boyutlandırma VARDI. Artık uç,
    döngünün kullandığı `loop.mirror_submit_armed` fonksiyonunu çağırır — ikinci bir emir yolu
    kalmadı.

    KALICILIK ARTIK TEK YERDE (İŞ-2-EOD, 2026-08-11): gönderim + kilit-altı yama gövdesi
    `loop.mirror_submit_ve_kalicilastir`a taşındı — onay anı (operator_onay_ver), intraday 4b ve bu
    uç AYNI kalıcılaştırma yasasını paylaşır (tam-belge yazımı YASAK; gönderilenler dedup kümesine
    EKLENİR, düşen veto/ret planları armed'dan kimlikle ÇIKARILIR, boyut makbuzu basılır — 08-06
    AMGN pano/nabız vakasının kuralları aynen o gövdede). Davranış birebir; buradaki tek fark
    çağrı olması (aynı taşıma deseni)."""
    _auth(request)
    from . import loop as _loop
    if health.halted():
        return {"ok": False, "detail": "HALT aktif — emir gönderilmez"}
    res = _loop.mirror_submit_ve_kalicilastir(source="pano")
    gonderilen, dusen = set(res.get("submitted_ids") or []), set(res.get("dropped_ids") or [])
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
# KORUMAYI YENİDEN KURAN YOL — ÖNERİ ÜRETİCİ + ONAY KAPISI + İCRA
# --------------------------------------------------------------------------------------------------
# EKSİK MEKANİZMA (canlı A1, 2026-08-07): panoda üç uç vardı — `/api/alpaca` (oku),
# `submit_armed` (gir), `close_all` (düzleştir). "Korumayı yeniden kur" YOKTU. `watchdog
# .koruma_report()` çıplak motor pozisyonlarını GÖRÜYOR ama bekçi haber verir, düzeltmez;
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
# sırasında yapılacak şeyin ta kendisidir. `cancel_open_entries` zaten aynı ayrımı
# yapıyor — dolu pozisyonların koruma bacaklarına DOKUNMUYOR.
KORUMA_KART_SEV = "sev-1"
# Emir listesi tavanı — `watchdog.KORUMA_EMIR_TAVANI` ile AYNI gerekçe (sahiplik kanıtı tavanın
# dışında kalabilir) ama İKİNCİ BİR OKUMA: bu modül bekçinin `rows`unu kullanır, bekçi ise emir
# FİYATLARINI döndürmez ve `watchdog.py` bu turda yazma kapsamı dışındadır.
# GEVŞETME denetimi (mevcut stop'un ÜSTÜNE çıkma) fiyatsız yapılamaz, o yüzden emirler burada bir kez
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
    """Sembol → broker'da CANLI duran koruyucu stop'ların EN YÜKSEĞİ (gevşetme denetiminin tabanı).

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
      · çıplak listesi → `watchdog.koruma_report()`. Yeniden yazılmaz: ikinci bir "koruma
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
        # ÜSTÜNDE olabilir; ikisinin BÜYÜĞÜ alınır çünkü kural "koruma gevşetilmez" der — küçüğünü
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
            # SAHİPLİK SINIRI: motor sahibi olmadığı pozisyona emir göndermez. GÖRÜNÜR olur, öneri ÜRETMEZ.
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
            # ARKA KAPI KAPALI: bu yol var olan bir korumayı DÜŞÜREMEZ.
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
         dokunmaz (`close_all` ile aynı desen).
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

    UÇ DÜZEYİ DENETİM İZİ. Kural "her GÖNDERİM olay bırakır"
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
    # CÜMLE DALDAN SEÇİLİR, `or` İLE TAKAS EDİLMEZ. `ozet` ve `detail` iki AYRI olgudur:
    # `ozet` yalnız icra dalında doğar ve "kaç/kaç + hangi sembol neden düştü" der; `detail` ise
    # emir GİTMEDİĞİNDE nedeni yazar (icra dalında çoğu zaman boştur). İkisini `x.get(a) or
    # x.get(b)` diye birleştirmek, bu deponun şema-takası tarayıcısının (test_parity_v56) tam da
    # kovaladığı desendir — ve o desen burada gerçek bir belirsizlik üretirdi: satırı okuyan,
    # cümlenin hangi olgudan geldiğini bilemezdi.
    if sonuc in ("gonderildi", "kismi-ya-da-dusuk"):
        cumle = res.get("ozet")
    else:
        cumle = res.get("detail")
    # TOPLAM ÖLÇÜLEMEDİ DALINDA None — 0 DEĞİL. `koruma_kur` ölçüm kapısında geri döner ve "kaç
    # öneri gönderilmeliydi" hiç hesaplanmaz; oraya 0 yazmak, korumasız pozisyon olmadığını iddia
    # etmek olurdu (`koruma_onerileri` de aynı dalda `gonderilebilir: None` döndürüyor).
    # `gonderilen` ise HER dalda ölçülüdür: emir yüzeyine hiç girilmeyen dallarda gerçekten 0'dır.
    obs.log("koruma_kur_istegi",
            oneri_id=_koruma_iz_maskele(oneri_id, 64) or "—", onay_verildi=onay_verildi,
            onaylayan=onaylayan, sonuc=sonuc,
            gonderilen=res.get("gonderilen"),
            toplam=(None if sonuc == "olculemedi" else res.get("toplam")),
            ozet=_koruma_iz_maskele(cumle, 240))
    if res.get("gonderilen"):
        _diag_onbellek_bosalt("koruma_kur")
    return res


# ---------- Batch N: ops & UX ----------
# ---- /halt SATIR İÇİ BETİĞİ DIŞARI ALINDI -----------------------------------------------------
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

    "Self-contained" ARTIK TAM DOĞRU DEĞİL ve cümle bu yüzden düzeltildi: betik
    `/halt.js`ten gelir. Bağımlılık AYNI ORIGIN'de, aynı süreçte, aynı dosyada üretilen tek bir
    rotadır — SPA'ya, diske ya da bir dış host'a bağlanmaz — ama "hiçbir şey istemez" demek
    yanlış olurdu: o rota düşerse düğme ölür (çivisi tests/test_guvenlik_basliklari_v203.py Ç5)."""
    return HTMLResponse("""<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<title>Meridian — HALT</title><link rel="icon" href="/favicon.svg" type="image/svg+xml"><style>body{margin:0;background:#0b0b0f;color:#eee;font-family:system-ui;
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
            # SQLite GEÇİŞİ SONRASI YEDEK BOŞALMASIN: yukarıdaki listenin
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
    """`GET /api/pipeline_runs` (EMEKLİ): son 60 skill koşusunu yeniden eskiye döner (salt-okuma).

    Yetki gerektirir. Kanonik yüzey `/api/skills` `recent_runs` alanıdır — YENİ tüketici bağlanmaz."""
    _auth(request)
    return {"runs": list(reversed(store.read_jsonl("pipeline_runs.jsonl")[-60:]))}


@app.get("/api/approvals")
def api_approvals(request: Request):
    """v11 #4 — BİRLEŞİK GELEN KUTUSU: onay bekleyen HER karar türü tek listede (otonomi
    seviyesinden bağımsız): kapıyı geçmiş silahlanma ölçümleri, skill revizyon taslakları,
    Eksen-2 önerileri, (L1+) canlı emir onayları. Her öğe: kanıt + yapılabilir eylem.

    KİMLİKLER `onay_kimligi()`DEN ÇIKAR: aynı dizgeyi L1 onay kapısı da arıyor. Burada
    satır içi `f"rev:{...}"` kurmak, kimliği İKİ yerde üretmek ve önek değiştiği gün kapıyı sessizce
    ayrıştırmak olurdu. Dizgeler DEĞİŞMEDİ — üretim yeri tekleşti."""
    _auth(request)
    from . import skill_evolve as _se
    inbox = []
    ar = store.read_json("arming_report.json", {}) or {}
    for setup, m in (ar.get("measurements") or {}).items():
        if m.get("status") == "gate_passed":
            rep = (ar.get("cf_report") or {}).get(setup) or {}
            inbox.append({"type": "arming", "id": onay_kimligi("arming", setup),
                          "title": f"Kurulum silahlanmaya hazır: {setup}",
                          "evidence": f"kapı GEÇTİ · P={m.get('search_p')} · onay P={m.get('confirm_p', '—')} · "
                                      f"cf n={rep.get('n')} ort {rep.get('avg_r')}R",
                          "actions": [],
                          "note": "Silahlanma kod değişikliğidir (ARMED_SETUPS) — onayını Claude'a söyle."})
    for r in _se.pending_drafts():
        ev = r.get("evidence") or {}
        inbox.append({"type": "skill_revision", "id": onay_kimligi("skill_revision", r["skill"]),
                      "title": f"Revizyon taslağı: {r['skill']}",
                      "evidence": f"{esc_ev(r.get('rationale'))} · kanıt n={ev.get('n')} ort {ev.get('avg_r')}R",
                      "actions": ["apply", "reject"], "skill": r["skill"]})
    from . import skills as _sk2
    _tarama = None                      # TEK okuma, TEMBEL: her öneri için defteri yeniden taramak
                                        # aynı yanıtın içinde N farklı okuma anı demek olurdu; hiç
                                        # kayıt-önerisi yoksa da defter boşuna okunmamalı
    for rec in _sk2.pending_recommendations():
        # EYLEM LİSTESİ ARTIK ÖLÇÜLÜR. Eskiden HER Eksen-2 önerisi koşulsuz
        # `actions: ["apply"]` taşıyordu; `lean_in` önerisi için de bir "Uygula" düğmesi çiziliyor,
        # düğme sunucuda reddediliyor ve ret ekranda görünmüyordu. Uygulayıcısı olmayan bir eylemi
        # uygulanabilir gibi sunmak, kusurun İLK adımı — `arming:{setup}` öğesi bu deseni zaten
        # doğru kuruyor: `actions: []` + neden diye DÜRÜST bir `note`. Aynısı burada uygulanır ve
        # ölçüt `skills.eylem_uygulanabilir` (uygulayıcının kendi kümesi), elle liste DEĞİL.
        _uyg = bool(rec.get("uygulanabilir", _sk2.eylem_uygulanabilir(rec.get("action"))))
        _oge = {"type": "skill_rec", "id": onay_kimligi("skill_rec", str(rec.get("skill"))),
                "title": f"Eksen-2: {rec.get('skill')} → {rec.get('action')}",
                # ÖRNEKLEM KANITIN YANINDA: kanıt satırı öneri METNİDİR ve o metni LLM
                # yazıyor olabilir ("Strong live performance of 0.918 avg_r" — canlı vaka, n=1).
                # Ölçülen künye metnin YANINA konur, metnin İÇİNE değil: iddia ile ölçü ayrı
                # okunabilmeli, yoksa "düzeltilmiş metin" ile "doğru metin" karışır.
                "evidence": rec.get("rationale") or "",
                "ornek": rec.get("ornek"), "ornek_yeterli": rec.get("ornek_yeterli"),
                "ornek_notu": rec.get("ornek_notu"),
                "actions": ["apply"] if _uyg else [],
                "skill": rec.get("skill"), "action": rec.get("action"),
                "uygulanabilir": _uyg}
        if not _uyg:
            _oge["note"] = rec.get("uygulanamama_notu") or _sk2.UYGULANAMAZ_NOT
            # KARAR YOLU: uygulanabilir karşılığı olmayan öneri artık "görülüp geçilen" bir
            # satır değil — operatör KABUL/RET diyebilir ve karar deftere düşer. `actions` BOŞ
            # KALIR (orası UYGULAMA eylemlerinin listesi; oraya kayıt düğmesi koymak, v238'de
            # kapattığımız "uygulanabilir gibi sunma" kusurunu geri getirirdi).
            if _tarama is None:
                _tarama = _defter_tarama()
            _oge["karar_kaydi"] = _karar_kaydi(str(rec.get("skill")), str(rec.get("action")),
                                               tarama=_tarama)
        inbox.append(_oge)
    lvl = config.limits()["autonomy_level"]
    return {"level": lvl, "inbox": inbox,
            "pending": store.read_jsonl(APPROVALS_LEDGER) if lvl >= 1 else [],
            "note": "Gelen kutusu her seviyede aktif; canlı emir onayları yalnız L1+."}


def esc_ev(x):
    """Gelen kutusu kanıt metnini güvenli kısa dizgiye çevirir: None → "", en fazla 200 karakter."""
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

    KUSUR: Genel Bakış'ın "Bugün ne var" kartı `inbox_count` okuyordu
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

    DÖRT KAYNAK: silahlanma kapısını geçen ölçüm · skill revizyon
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
        # KARAR VERİLMİŞ ÖNERİ ROZETİ ŞİŞİRMEZ: rozet "senden İŞ isteyen karar" sayar.
        # Operatör bir kayıt-önerisine Kabul/Ret dedikten sonra o satır gelen kutusunda damgasıyla
        # DURUR (üreteç aynı öneriyi yeniden yazabilir, karar geçmişi görünür kalmalı) ama artık iş
        # istemez. Sayım gelen kutusuyla AYNI yardımcıdan (`_karar_kaydi`) geçer; ölçütü burada
        # yeniden yazsaydık kart ile rozet aynı gün ayrışırdı (`_onay_bekleyen_damgala` dersi).
        _tarama = None                             # tembel: kayıt-önerisi yoksa defter okunmaz
        for _rec in _sk3.pending_recommendations():
            if _rec.get("uygulanabilir"):
                n += 1
                continue
            if _tarama is None:
                _tarama = _defter_tarama()
            _kk = _karar_kaydi(str(_rec.get("skill")), str(_rec.get("action")), tarama=_tarama)
            n += 0 if _kk["karar"] in ("approve", "reject") else 1
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
    """`POST /api/halt`: kill-switch'i AÇAR — yeni girişler bir bar içinde durur. YETKİLİ, YAZAR.

    Bayrak dosyasına kendi eliyle dokunmaz, `health.set_halt(True)`e delege eder (tek kapı).
    Yan etkileri: nabız notuyla yeniden yazılır (mevcut alanlar korunur, sıfırdan yazılmaz),
    `ALARM_HALT` alarmı düşer, ikincil bildirim kanalı denenir ve teşhis önbelleği boşaltılır."""
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
    """`POST /api/resume`: kill-switch'i KALDIRIR. YETKİLİ, YAZAR — `api_halt`ın tersi.

    `health.set_halt(False)`e delege eder ve İDEMPOTENTtir (bayrak dosyası yoksa no-op).
    `resume` olayı yazılır, bildirim kanalı denenir, teşhis önbelleği boşaltılır."""
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
    döner (sessiz "olmadı" yok).

    ONAY = İCRA YETKİSİ (İŞ-2-EOD/İŞ-3a, 2026-08-11 — tarihçe-koru: v190 sözleşmesi "bu uç emir
    göndermez" idi ve P-2026-08-07-VLO fiyaskosu o boşluğu kanıtladı): onay artık AYNI TEK KAPIDAN
    (`loop.mirror_submit_ve_kalicilastir` → `mirror_submit_armed`) onay ANINDA aynaya gönderimi de
    dener — ikinci bir emir gövdesi YOK, yasa yine loop'ta. DÜRÜSTLÜK SÖZLEŞMESİ: yanıtın
    `icra_yolu` alanı gönderimin sonucunu — ya da icra yolunun yokluğunu ("onay iç-deftere işler,
    broker'a GİTMEZ: <eksik>") — AÇIKÇA söyler; onay REDDEDİLMEZ (operatör bilerek iç-defter
    denemesi yapabilir), ama sessizlik YASAK."""
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


@app.post("/api/plan/{plan_id}/reddet")
async def api_plan_reddet(plan_id: str, request: Request):
    """REVIEW/NO_GO planına operatörün GEREKÇELİ ret kaydı — icraya DOKUNMAZ.

    ONAYIN AYNASI DEĞİL: `girise_uygun` yasası onaylanmayan REVIEW'ü zaten silahlandırmaz, NO_GO'yu
    zaten geçirmez. Yani bu uç bir şeyi DURDURMAZ — durduracak bir şey yoktur. Kaydın değeri
    ayrımdadır: sessiz zaman aşımı ile "operatör gördü ve şu sebeple istemedi" bugüne kadar AYNI
    görünüyordu. Gerekçe ZORUNLUdur (400) çünkü gerekçesiz ret o ayrımı üretmez.

    YASA BURADA DEĞİL `loop.operator_ret_ver`DE — `api_plan_onayla` ile birebir aynı gerekçe:
    `trade_plans.jsonl`in yazar listesi `ledgers.CONTRACTS`ta yazılıdır."""
    _auth(request)
    from . import loop as _loop
    try:
        govde = await request.json()
    except Exception:  # sessiz-yutma: gövde okunamazsa gerekçe BOŞ sayılır ve alttaki yasa 400 ile reddeder — uydurma bir gerekçe üretmektense dürüst ret
        govde = {}
    if not isinstance(govde, dict):
        govde = {}
    res = _loop.operator_ret_ver(plan_id, gerekce=str(govde.get("gerekce") or ""), kanal="pano")
    if not res.get("ok"):
        raise HTTPException(status_code=int(res.get("kod") or 409),
                            detail=str(res.get("neden") or "reddedilemedi"))
    _diag_onbellek_bosalt("plan_operator_rejected")
    return res


@app.post("/api/approvals/{approval_id}")
async def api_approve(approval_id: str, request: Request):
    """Operatörün onay/ret kararını deftere yazar. YALNIZ YAZAR — hiçbir şey uygulamaz.

    Bu satır artık BAĞLAYICI: `approval_id`, `GET /api/approvals` gelen kutusunun
    `id` alanıyla AYNI dizge olmalıdır (`onay_kimligi()`: `rev:{skill}` · `rec:{skill}` ·
    `arming:{setup}`) — L1+ uygulama kapıları (`_onay_kapisi`) o kimlikle bu deftere bakar.
    Tanınmayan bir kimliğe yazılan karar hiçbir yolu açmaz; kapı fail-closed'dır.

    `decision` yalnız `approve` ya da `reject` olarak OKUNUR. Uç bunu burada DAYATMAZ (defter bir
    olay kaydıdır ve operatörün yazdığı ham karar aynen saklanır); okunamayan bir karar kapıda
    "onay YOK" sayılır ve nedeni olay akışına düşer (`approval_missing_refused`).

    L0 İSTİSNASI — KAPI-BAĞLAMAYAN KİMLİKLER. L1+ kısıtı BURADA DEĞİL, kısıtın
    KORUDUĞU ŞEYDE anlamlıdır: bir `approve` satırı L1'de bir UYGULAMA KAPISINI açar
    (`_onay_kapisi` ← `rev:` / `rec:`), yani L0'da yazılan karar yarın icraya dönüşebilirdi.
    `KAPI_OKUYAN_ONEKLER` DIŞINDAKİ kimlikleri (bugün `kayit:` ve `arming:`) HİÇBİR kapı okumaz —
    orada 403'ün koruduğu bir şey YOKTUR ve 403, sistem L0 olduğu sürece karar kaydını tümüyle
    imkânsız kılıyordu (operatörün itirazının tam adresi: öneri görünür, karar yolu yok).
    TANINMAYAN ÖNEK L0'DA HÂLÂ 403: bağlamadığını KANITLAYAMADIĞIMIZ bir uzaya karar yazdırmak,
    fail-closed'ın tersi olurdu."""
    _auth(request)
    _onek = str(approval_id).split(":", 1)[0]
    _baglayici = _onek in KAPI_OKUYAN_ONEKLER
    _kapi_disi = _onek in (set(ONAY_ONEK.values()) - set(KAPI_OKUYAN_ONEKLER))
    if config.limits()["autonomy_level"] < 1 and not _kapi_disi:
        raise HTTPException(status_code=403, detail="approvals are L1+ only; system is L0 paper")
    body = await request.json()
    decision = body.get("decision")
    reason = body.get("reason", "")
    satir = {"id": approval_id, "decision": decision, "reason": reason, "ts": memory.now_iso()}
    if not _baglayici:
        # KAYIT SATIRI KENDİNİ BEYAN EDER: defteri sonradan okuyan (insan ya da kapı) bu satırın
        # hiçbir icrayı açmadığını satırın KENDİSİNDEN görmeli — "hangi önekti?" diye hatırlamak
        # zorunda kalmamalı. `davranissal: False` bir yorum değil, defterin kendi künyesi.
        satir["davranissal"] = False
        satir["not"] = KAYIT_KARARI_NOT
    if _onek == ONAY_ONEK["skill_rec_kayit"]:
        # KARAR ANINDAKİ KANIT KÜNYESİ — SUNUCU ÖLÇER, İSTEMCİ BEYAN ETMEZ. Künyeyi gövdeden almak,
        # "kararın dayandığı kanıt"ı karar verenin kendi iddiasına bırakmak olurdu; ayrıca panonun
        # o an ekranda tuttuğu bayat bir künye deftere gerçekmiş gibi girerdi.
        satir["kunye"] = _kayit_karar_kunyesi(approval_id)
    store.append_jsonl(APPROVALS_LEDGER, satir)
    # Operatör kararı OLAY defterine de düşer: onay/ret, alarmların ve döngü olaylarının yanında
    # tek bir zaman çizgisinde okunabilmeli (N/A sorgusu, 2026-07-21).
    obs.log("approval_decision", approval_id=approval_id, decision=str(decision)[:40],
            has_reason=bool(reason), davranissal=_baglayici)
    if reason:
        memory.distill_lessons()
    # L0'da 403 YUKARIDA fırladı (zarf düşmez); buraya gelen istek onay defterine satır yazmıştır.
    _diag_onbellek_bosalt("approval_decision")
    # YANIT KENDİ SINIRINI SÖYLER: "ok: true" tek başına "yapıldı" gibi okunur ve bir
    # kayıt-önerisinde bu YANLIŞ GÜVEN üretirdi — operatör davranışın değiştiğini sanırdı. Alan
    # her kararda taşınır (bağlayıcıda da), çünkü "davranışsal mı" sorusunun cevabı istemcinin
    # kimlik önekini kendi ayrıştırmasına bırakılamaz.
    yanit = {"ok": True, "id": approval_id, "decision": decision, "davranissal": _baglayici}
    if not _baglayici:
        yanit["not"] = KAYIT_KARARI_NOT
        yanit["kunye"] = satir.get("kunye")
    return yanit


# =================================================================================================
# v287 · PANO ALTYAPI YÜZEYİ — `/api/infra` (makine + Meridian bileşenleri) ve `/api/roadmap`
# =================================================================================================
#
# NEDEN BU İKİ UÇ BURADA, `/api/diagnostics` İÇİNDE DEĞİL: teşhis ucu **Meridian'ın kendi
# defterini** (state/) okur ve 45 sn önbelleklidir. Bu ikisi defterin DIŞINA bakar — biri işletim
# sistemine (çekirdek, bellek, disk, systemd), diğeri bir markdown dosyasına. Aynı zarfa
# koysaydık: (a) `/proc` okuması ve `systemctl` alt süreçleri teşhis yükünün maliyetine eklenir,
# (b) 562 KB'lık ROADMAP ayrıştırması her teşhis isteğine bulaşırdı, (c) makine metriği 45 sn
# bayatlıkla servis edilirdi — oysa "makine şu an ne durumda" sorusunun cevabı 45 sn'de eskir.
#
# PSUTIL YOK — VE EKLENMEDİ. Depoda `psutil` bağımlılığı ÖLÇÜLDÜ ve YOKTUR (`pyproject.toml`:
# 0 eşleşme · `uv.lock`: 0 eşleşme · `.venv` import denemesi: ModuleNotFoundError, 2026-08-25).
# Tek bir pano ucu için üretim bağımlılık ağacına C uzantılı bir paket sokmak, ucun getirdiği
# değerden pahalıdır (canlı A1 aarch64; tekerlek yoksa derleme). Bu yüzden ölçüm YALNIZ standart
# kütüphaneyle yapılır: `os` · `platform` · `shutil.disk_usage` · `/proc` (Linux) · `os.getloadavg`
# · `os.times`. BEDELİ AÇIKÇA TAŞINIR: psutil'in taşınabilir verdiği birkaç alan (macOS'ta CPU
# yüzdesi, kullanılan bellek, makine uptime'ı) bu makinede ÖLÇÜLEMEZ ve `None` + neden döner.
#
# PLATFORM FARKI GİZLENMEZ. Canlı sistem Linux (Oracle A1), geliştirme makinesi macOS ve `/proc`
# macOS'ta YOKTUR. Bir alanı "ölçülemedi" yerine `0` yazmak sözdizimsel olarak bedavadır ve panoda
# "boşta makine" diye okunur — bu deponun birinci yasasının (UYDURMA YASAĞI) tam ihlali. Bu yüzden
# her ölçüm alanının yanında ya kendi `<alan>_neden` kardeşi ya da kabın `olculemedi_neden`i
# vardır; `tests/test_pano_altyapi_v287.py` bunu GENEL biçimde çivilemiştir (yarın eklenen alan da
# kurala girer, kimse listeyi güncellemeyi unutamaz).
#
# CPU YÜZDESİ BİR FARKTIR, BİR OKUMA DEĞİL. `/proc/stat` ve systemd `CPUUsageNSec` KÜMÜLATİF
# sayaçlardır; yüzde ancak İKİ örnek arasındaki farktan çıkar. Uç içinde `sleep` YOKTUR (madde 7'nin
# ruhu: bekleyen kod yasak; ayrıca 15 sn'de bir yoklanan bir uçta 200 ms uyumak panoyu yavaşlatırdı)
# — bunun yerine önceki örnek süreç-içi tutulur ve İLK istekte yüzde `None` + neden döner. "Bir
# sonraki yoklamada ölçülür" demek, sıfır yazmaktan dürüsttür.
_INFRA_CACHE: dict = {}
_INFRA_CPU_ORNEK: dict = {}
INFRA_TTL_S = 8.0
# 8 sn: pano şeridi 15 sn'de bir yokluyor, yani ardışık iki yoklamanın İKİSİ birden kutudan
# gelemez — "pano donmuş" hissi doğmaz. Aşağı sınırı da var: `systemctl show` alt süreçleri
# birim başına bir fork'tur ve önbelleksiz bir uç, 15 sn'de bir 14 fork demek olurdu.
_INFRA_SUREC_BASI = _time.time()
_INFRA_SUREC_MONO = _time.monotonic()

# systemd `MemoryCurrent` AYARSIZ olduğunda 2^64-1 döndürür. Bunu 18 exabayt RSS diye basmak,
# ölçülmemiş bir değeri sayıya çevirmenin ders kitabı örneğidir — sentinel `None`a çevrilir.
_SYSTEMD_AYARSIZ = 18446744073709551615
_SYSTEMCTL_ALANLARI = ("LoadState", "ActiveState", "SubState", "MainPID", "NRestarts",
                       "MemoryCurrent", "CPUUsageNSec", "ExecMainStartTimestampMonotonic",
                       "UnitFileState", "Description",
                       # TETİKLEYİCİ ÜÇLÜSÜ (v310) — `inactive` TEK BAŞINA bir hüküm değildir.
                       # `Type=oneshot` bir birim koşumlar ARASINDA zaten `inactive`tir; sağlıklı
                       # olup olmadığı TETİKLEYİCİSİNDEN okunur: `TriggeredBy` (timer) ya da
                       # `OnFailureOf` (arıza kancası). Bu üç alan olmadan pano ya susar ya
                       # uydurur; operatör 2026-08-25'te "neden inaktif gözüküyor" diye sordu.
                       "Type", "TriggeredBy", "OnFailureOf")
# TOPLAM zaman bütçesi: birim başına 2 sn'lik timeout × 14 birim = en kötü 28 sn ve o, 15 sn'de
# bir yoklanan bir ucu kilitlerdi. Bütçe dolunca kalan birimler ÖLÇÜLMEDİ + neden ile döner.
_SYSTEMCTL_BUTCE_S = 1.5
# CPU farkının anlamlı olması için gereken asgari aralık (ölçüm gerekçesi `_infra_cpu_yuzde`de).
_CPU_ASGARI_ARALIK_S = 0.5


def _proc_oku(ad: str) -> str | None:
    """`/proc/<ad>` içeriğini döndürür; dosya yoksa/okunamazsa `None`.

    TEK KAPI OLMASI BİLİNÇLİ: `/proc` macOS'ta HİÇ YOKTUR ve ölçümün platforma bağlı yarısı bu tek
    fonksiyondan geçer. Testler bunu kör ederek macOS'u Linux üstünde simüle eder — yoksa çivi
    yerelde ve canlıda FARKLI şeyi ölçer, geçtiğinde hiçbir şey kanıtlamazdı."""
    try:
        return Path("/proc", ad).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):  # sessiz-yutma: /proc yokluğu macOS'ta NORMAL hâldir, hata değil; çağıran None'ı "ölçülemedi" olarak işler ve nedenini gövdeye yazar
        return None


def _infra_cpu_yuzde(anahtar: str, kumulatif_ns: float | None, *,
                     bolen_ns: float | None = None) -> tuple[float | None, str | None]:
    """Kümülatif bir CPU sayacından yüzde çıkarır — İKİ örnek arasındaki farkla.

    `bolen_ns` verilirse (örn. `/proc/stat`'ın toplam jiffy'si) yüzde o farka bölünür; verilmezse
    duvar saati farkı × çekirdek sayısı yerine DUVAR SAATİ kullanılır (tek çekirdek-eşdeğeri
    yüzdesi, `top`un süreç sütunuyla aynı sözleşme: %200 = iki çekirdek dolu).
    İlk örnekte `None` + neden döner — sıfır yazmak "boşta" demek olurdu.

    ÇOK KISA ARALIK DA ÖLÇÜM DEĞİLDİR. `?taze=1` art arda çağrılınca aralık milisaniyelere
    düşer ve pay/payda gürültüsü %200+ gibi anlamsız değerler üretir (ölçüldü: 0,1 sn aralıkta
    %224,8). O sayı "CPU yandı" diye okunur — oysa ölçülen şey aralığın kısalığıdır. Bu durumda
    ÖNCEKİ ÖRNEK KORUNUR (üzerine yazılmaz): taban geride kalsın ki aradan yeterli süre geçtiğinde
    fark GERÇEKTEN ölçülebilsin. Örneği yenileseydik hızlı yoklama yüzdeyi sonsuza dek ölçülemez
    yapardı."""
    simdi = _time.monotonic()
    onceki = _INFRA_CPU_ORNEK.get(anahtar)
    if onceki is not None and (simdi - onceki[2]) < _CPU_ASGARI_ARALIK_S:
        return None, (f"iki örnek arası {simdi - onceki[2]:.2f} sn (< {_CPU_ASGARI_ARALIK_S} sn) — "
                      "bu kadar kısa aralıkta yüzde gürültüdür; taban korundu, sonraki yoklamada ölçülür")
    _INFRA_CPU_ORNEK[anahtar] = (kumulatif_ns, bolen_ns, simdi)
    if kumulatif_ns is None:
        return None, "kümülatif CPU sayacı okunamadı (kaynak alan yok)"
    if onceki is None:
        return None, ("ilk örnek: CPU yüzdesi iki örnek arasındaki FARKtır, tek okumadan "
                      "hesaplanamaz — bir sonraki yoklamada ölçülür")
    ov, ob, ot = onceki
    if ov is None:
        return None, "önceki örnekte sayaç okunamamıştı; fark alınamadı"
    d_sayac = float(kumulatif_ns) - float(ov)
    if d_sayac < 0:
        return None, "sayaç geriye gitti (birim yeniden başladı) — bu aralık için fark anlamsız"
    if bolen_ns is not None and ob is not None:
        d_bolen = float(bolen_ns) - float(ob)
        if d_bolen <= 0:
            return None, "iki örnek arasında geçen çekirdek zamanı sıfır — yüzde tanımsız"
        return round(100.0 * d_sayac / d_bolen, 1), None
    d_duvar = simdi - ot
    if d_duvar <= 0:
        return None, "iki örnek arasında geçen duvar saati sıfır — yüzde tanımsız"
    return round(100.0 * d_sayac / (d_duvar * 1e9), 1), None


def _infra_makine() -> dict:
    """MAKİNE bloğu — çekirdek, yük, CPU, bellek, disk, çalışma süresi.

    Her alan kendi ölçüm yolunu taşır; ölçülemeyen alan `None` + neden döner."""
    import platform as _pf

    cekirdek = os.cpu_count()
    # ---- yük ortalaması: Linux + macOS'ta VAR, Windows'ta yok
    try:
        y1, y5, y15 = os.getloadavg()
        yuk, yuk_neden = {"1dk": round(y1, 2), "5dk": round(y5, 2), "15dk": round(y15, 2)}, None
    except (OSError, AttributeError) as e:
        yuk, yuk_neden = None, f"os.getloadavg() bu platformda yok/başarısız: {type(e).__name__}"

    # ---- CPU yüzdesi: /proc/stat'ın kümülatif jiffy'lerinden FARK
    stat = _proc_oku("stat")
    kumulatif = bolen = None
    cpu_neden_on = None
    if stat is None:
        cpu_neden_on = ("`/proc/stat` okunamadı — bu makinede `/proc` yok (macOS) ya da erişilemez; "
                        "psutil kurulu DEĞİL, taşınabilir bir CPU okuması bu uçta mevcut değil")
    else:
        satir = next((s for s in stat.split("\n") if s.startswith("cpu ")), None)
        if satir is None:
            cpu_neden_on = "`/proc/stat` içinde toplam `cpu ` satırı yok — beklenmedik biçim"
        else:
            try:
                alanlar = [float(x) for x in satir.split()[1:]]
            except ValueError:  # sessiz-yutma: /proc/stat satırı beklenmedik biçimde — alan listesi boş bırakılır ve CPU yüzdesi çağıran tarafında None + neden ile döner; kısmi sayı uydurmaktan dürüst
                alanlar = []
            if len(alanlar) < 5:
                cpu_neden_on = "`/proc/stat` `cpu ` satırı beklenen alan sayısını taşımıyor"
            else:
                toplam = sum(alanlar)
                bosta = alanlar[3] + alanlar[4]          # idle + iowait
                kumulatif, bolen = toplam - bosta, toplam
    if cpu_neden_on:
        cpu_yuzde, cpu_neden = None, cpu_neden_on
        _INFRA_CPU_ORNEK.pop("makine", None)             # kör örnek saklanmaz: sahte fark üretirdi
    else:
        cpu_yuzde, cpu_neden = _infra_cpu_yuzde("makine", kumulatif, bolen_ns=bolen)

    # ---- bellek: /proc/meminfo (Linux). Toplam sysconf'tan da ölçülebilir; KULLANILAN ölçülemez.
    bellek: dict = {"toplam_bayt": None, "kullanilan_bayt": None, "kullanilabilir_bayt": None,
                    "kullanim_yuzde": None, "kaynak": None, "olculemedi_neden": None}
    meminfo = _proc_oku("meminfo")
    if meminfo:
        kb: dict = {}
        for s in meminfo.split("\n"):
            p = s.split(":", 1)
            if len(p) == 2:
                sayi = p[1].strip().split()
                if sayi and sayi[0].isdigit():
                    kb[p[0]] = int(sayi[0]) * 1024
        t, a = kb.get("MemTotal"), kb.get("MemAvailable")
        if t and a is not None:
            bellek.update(toplam_bayt=t, kullanilabilir_bayt=a, kullanilan_bayt=t - a,
                          kullanim_yuzde=round(100.0 * (t - a) / t, 1), kaynak="/proc/meminfo")
        elif t:
            bellek.update(toplam_bayt=t, kaynak="/proc/meminfo",
                          olculemedi_neden="`MemAvailable` satırı yok (çok eski çekirdek) — "
                                           "kullanılan/kullanılabilir bellek çıkarılamadı")
        else:
            bellek["olculemedi_neden"] = "`/proc/meminfo` okundu ama `MemTotal` satırı yok"
    if bellek["toplam_bayt"] is None:
        try:
            t = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            bellek.update(toplam_bayt=t, kaynak="sysconf")
        except (OSError, ValueError, AttributeError):  # sessiz-yutma: sysconf anahtarı bu platformda yoksa toplam bellek de ölçülemez; aşağıdaki gerekçe satırı bunu gövdeye yazar
            pass
        bellek["olculemedi_neden"] = (
            "`/proc/meminfo` yok (macOS) — KULLANILAN bellek yalnız `vm_stat`/psutil ile "
            "çıkarılabilir, ikisi de bu uçta kullanılmıyor" + (
                "; toplam bellek `sysconf` ile ölçüldü" if bellek["toplam_bayt"] is not None
                else "; `sysconf` da toplamı vermedi"))

    # ---- disk: `shutil.disk_usage` HER platformda çalışır (psutil'in gerekmediği tek metrik).
    # AYNI BÖLÜM İKİ SATIR OLMAZ: `/`, depo kökü ve `state/` çoğu kurulumda tek dosya sistemidir ve
    # üç satır aynı sayıyı üç kez basardı — pano "üç disk" sanardı. Bunun yerine bölüm TEK satırdır
    # ve `kapsayan_yollar` hangi Meridian yolunun o bölümde durduğunu SÖYLER; bilgi kaybı yok.
    diskler, aygit_satiri = [], {}
    for yol in ("/", str(config.ROOT), str(config.STATE)):
        try:
            aygit = os.stat(yol).st_dev
        except OSError as e:
            diskler.append({"yol": yol, "kapsayan_yollar": [yol], "toplam_bayt": None,
                            "kullanilan_bayt": None, "bos_bayt": None, "kullanim_yuzde": None,
                            "olculemedi_neden": f"os.stat başarısız — {type(e).__name__}: {e}"})
            continue
        if aygit in aygit_satiri:
            aygit_satiri[aygit]["kapsayan_yollar"].append(yol)
            continue
        satir: dict = {"yol": yol, "kapsayan_yollar": [yol], "toplam_bayt": None,
                       "kullanilan_bayt": None, "bos_bayt": None, "kullanim_yuzde": None,
                       "olculemedi_neden": None}
        try:
            u = shutil.disk_usage(yol)
            satir.update(toplam_bayt=u.total, kullanilan_bayt=u.used, bos_bayt=u.free,
                         kullanim_yuzde=round(100.0 * u.used / u.total, 1) if u.total else None)
            if u.total == 0:
                satir["olculemedi_neden"] = "aygıt toplam boyutu 0 bildirdi — yüzde tanımsız"
        except OSError as e:
            satir["olculemedi_neden"] = f"shutil.disk_usage başarısız — {type(e).__name__}: {e}"
        aygit_satiri[aygit] = satir
        diskler.append(satir)

    # ---- makine çalışma süresi: /proc/uptime. macOS'ta `sysctl kern.boottime` gerekir (alt süreç).
    uptime_s = uptime_neden = None
    up = _proc_oku("uptime")
    if up:
        try:
            uptime_s = round(float(up.split()[0]), 1)
        except (ValueError, IndexError):  # sessiz-yutma: gerekçe hemen altta `uptime_neden`e yazılıyor ve gövdede beyan ediliyor — yutulan şey istisna, ölçüm değil
            uptime_neden = "`/proc/uptime` beklenmedik biçimde — ilk alan sayı değil"
    else:
        uptime_neden = ("`/proc/uptime` yok (macOS) — makine çalışma süresi ancak `sysctl "
                        "kern.boottime` alt süreciyle ölçülebilir, bu uç alt süreç açmıyor")

    return {
        "hostname": _pf.node(),
        "platform": {"sistem": _pf.system(), "surum": _pf.release(), "makine": _pf.machine(),
                     "python": _pf.python_version(), "tam": _pf.platform()},
        "cekirdek_n": cekirdek,
        "cekirdek_n_neden": None if cekirdek else "os.cpu_count() None döndürdü — çekirdek sayısı belirlenemedi",
        "yuk": yuk, "yuk_neden": yuk_neden,
        "cpu_yuzde": cpu_yuzde, "cpu_yuzde_neden": cpu_neden,
        "bellek": bellek, "disk": diskler,
        "uptime_s": uptime_s, "uptime_s_neden": uptime_neden,
    }


def _infra_surec() -> dict:
    """BU API SÜRECİ — makine ile bileşenler arasındaki üçüncü kat.

    Neden ayrı: `/api/infra`yı okuyan operatörün ilk sorusu "pano süreci kendisi ne kadar yiyor?"
    ve bu, systemd'nin `meridian.service` satırıyla AYNI ŞEY DEĞİLDİR (o birim docker compose'u
    sarar). `os.times()` HER platformda çalışır, yani süreç CPU'su macOS'ta da ölçülür — `/proc`
    körlüğünün istisnası."""
    try:
        t = os.times()
        cpu_ns = (t.user + t.system) * 1e9
    except (OSError, AttributeError):  # sessiz-yutma: os.times() yoksa süreç CPU'su ölçülemez; aşağıda None + neden ile beyan edilir
        cpu_ns = None
    cpu_yuzde, cpu_neden = _infra_cpu_yuzde("surec", cpu_ns)

    rss = rss_neden = None
    statm = _proc_oku("self/statm")
    if statm:
        try:
            rss = int(statm.split()[1]) * os.sysconf("SC_PAGE_SIZE")
        except (ValueError, IndexError, OSError):  # sessiz-yutma: gerekçe hemen altta `rss_neden`e yazılıyor ve gövdede beyan ediliyor — yutulan şey istisna, ölçüm değil
            rss_neden = "`/proc/self/statm` okundu ama yerleşik sayfa alanı çıkarılamadı"
    else:
        # `resource.getrusage(...).ru_maxrss` BİLEREK KULLANILMADI: o ZİRVE RSS'tir, ANLIK değil —
        # ve macOS'ta bayt, Linux'ta kilobayt döndürür. İki farklı şeyi tek alana yazmak, tam olarak
        # bu dosyanın kovaladığı sessiz yalan sınıfıdır.
        rss_neden = ("`/proc/self/statm` yok (macOS) — ANLIK RSS yalnız psutil/`ps` ile ölçülür; "
                     "`ru_maxrss` ZİRVE değeri ve birimi platforma göre değişir, kullanılmadı")
    return {"pid": os.getpid(),
            "uptime_s": round(_time.monotonic() - _INFRA_SUREC_MONO, 1),
            "baslangic_ts": __import__("datetime").datetime.fromtimestamp(
                _INFRA_SUREC_BASI, __import__("datetime").timezone.utc).isoformat(timespec="seconds"),
            "cpu_yuzde": cpu_yuzde, "cpu_yuzde_neden": cpu_neden,
            "rss_bayt": rss, "rss_bayt_neden": rss_neden}


def _infra_birim_adlari() -> dict:
    """Meridian systemd birimlerinin GERÇEK adları — `deploy/` altındaki birim DOSYALARINDAN.

    AD UYDURULMAZ: "muhtemelen `meridian-worker.service` vardır" demek, panoya var olmayan bir
    satır bastırır ve o satır sonsuza dek `not-found` gösterir. Kaynak diskteki dosyadır; aynı ad
    iki yerde geçiyorsa (`deploy/meridian.service` ve `deploy/oracle-a1/meridian.service`) birim
    TEK sayılır — systemd için de tek bir addır."""
    kok = Path(config.ROOT) / "deploy"
    birimler: dict = {}
    neden = None
    try:
        dosyalar = sorted(list(kok.rglob("*.service")) + list(kok.rglob("*.timer")))
    except OSError as e:
        dosyalar, neden = [], f"`deploy/` taranamadı: {type(e).__name__}: {e}"
    # KURULUM BEKLENTİSİ, AD BAZINDA (v310). "kurulu değil" İKİ AYRI İŞTİR: biri operatörden sudo
    # bekler (`meridian-aylik-bucket-kopya`), öteki hiçbir şey beklemez (`deploy/litestream.service`
    # — üst dizinde duran eski/genel kopya). Ayrımın OTORİTESİ `dagit.sh`: o yalnız
    # `deploy/oracle-a1/*.service` dosyalarını canlının birimleriyle kıyaslar, yani kurulum
    # beklentisi HOST ALT DİZİNİNDE olmaktır. Beklenti AD bazında toplanıyor, tarama sırasından
    # DEĞİL: `meridian.service` hem `deploy/` kökünde hem `deploy/oracle-a1/` altında var ve
    # sıralamada kök önce gelir — sıraya güvenmek canlının ANA birimini "envanter gürültüsü" diye
    # susturur (bu tam olarak susturmaması gereken satır).
    host_altinda: set[str] = {p.name for p in dosyalar if p.parent != kok}
    for p in dosyalar:
        ad = p.name
        if ad in birimler:
            continue
        _beklenen = ad in host_altinda
        birimler[ad] = {
            "beklenen": _beklenen,
            "beklenen_neden": (
                f"`{kok.name}/<host>/` altında birim dosyası var ve `dagit.sh` bu dizini canlıyla "
                "kıyaslıyor"
                if _beklenen else
                f"yalnız `{kok.name}/` kökünde duruyor, hiçbir host dizininde yok ve `dagit.sh` "
                "kurulum kıyasına almıyor"),
            "ad": ad, "dosya": ad, "tur": p.suffix.lstrip("."),
            # ŞABLON BİRİM (`ad@.service`): düz adla `systemctl show` sorgusu SAHTE bir `inactive`
            # döndürür — birim şablonu değil, örneği koşar (`meridian-sprint@2026-08-13.service`).
            # Bu tuzak bu depoda bir kez yaşandı: "koşmuyor" ile "koştu, aday geçmedi" karıştı.
            "sablon": "@" in ad,
            "yol": str(p.relative_to(config.ROOT)) if str(p).startswith(str(config.ROOT)) else str(p),
        }
    if not birimler and neden is None:
        neden = f"`{kok}` altında hiç `.service`/`.timer` dosyası yok"
    return {"birimler": list(birimler.values()), "dizin": str(kok), "olculemedi_neden": neden}


def _systemctl_show(birim: str) -> dict | None:
    """`systemctl show <birim>` çıktısını `anahtar=değer` sözlüğüne çevirir; ölçülemezse `None`.

    AYRI FONKSİYON OLMASI BİLİNÇLİ: alt süreç çağrısı testlerde tek noktadan saplanabilmeli,
    yoksa bileşen sözleşmesi ancak systemd KURULU bir makinede sınanabilirdi."""
    import subprocess
    yol = shutil.which("systemctl")
    if not yol:
        return None
    try:
        cp = subprocess.run([yol, "show", birim, "--no-pager"]
                            + [f"--property={a}" for a in _SYSTEMCTL_ALANLARI],
                            capture_output=True, text=True, timeout=2.0)
    except (OSError, subprocess.SubprocessError):  # sessiz-yutma: systemctl yoksa/zaman aşarsa bu birim ÖLÇÜLEMEDİ demektir; çağıran None'ı gerekçeye çevirir, uydurma satır basmaz
        return None
    if cp.returncode != 0:
        return None
    out: dict = {}
    for satir in cp.stdout.split("\n"):
        if "=" in satir:
            k, v = satir.split("=", 1)
            out[k] = v
    return out or None


def _systemd_liste(ham: dict, alan: str) -> list[str]:
    """systemd'nin boşlukla ayrılmış birim listesi alanını (`TriggeredBy`, `OnFailureOf`) böler.

    Alan YOKSA ya da boşsa BOŞ LİSTE döner — ve boş liste burada "bağ yok" DEĞİL "bu çıktıda bağ
    görünmedi" demektir; hükmü kuran `_infra_durum_sinifi` bu ikisini `Type` ölçüldü mü diye
    ayırır."""
    return [p for p in (ham.get(alan) or "").split() if p]


def _infra_durum_sinifi(s: dict, olculen_durumlar: dict[str, str | None]) -> tuple[str, str]:
    """Bir birim satırını OPERATÖRÜN İŞİNE karşılık gelen tek bir sınıfa indirger + gerekçesini.

    NEDEN VAR (operatör kusuru, 2026-08-25: "neden kurulu değil, inaktif ve ölçülemedi
    gözüküyor"): tablo ÜÇ AYRI DÜNYAYI tek kılıkta gösteriyordu. `Type=oneshot` bir birim
    koşumlar ARASINDA zaten `inactive`tir — `meridian-backup.service` timer'ı aktifken de
    `inactive` görünür ve bu SAĞLIKLI hâldir. `meridian-fail-notify.service` ise hiç timer
    taşımaz; `OnFailure` ile tetiklenir ve `inactive` olması "hiçbir şey arızalanmadı" demektir,
    mümkün olan EN İYİ hâl. Bunları koşması gerekirken durmuş bir `Type=simple` birimle aynı
    rozete koymak, sinyali gürültünün içinde kaybetmekti.

    SAĞLIK İDDİASI ANCAK ÖLÇÜLDÜYSE KURULUR (UYDURMA YASAĞI). `Type` gelmediyse birimin oneshot
    olup olmadığı BİLİNMİYOR; `TriggeredBy` bu istekte ölçülmemiş bir birimi gösteriyorsa timer'ın
    aktifliği BİLİNMİYOR. İkisinde de sınıf bir "ölçülemedi" sınıfıdır — "muhtemelen sıradadır"
    bir ölçüm değil, bir varsayımdır ve panoya yazıldığı an güvence gibi okunur.

    `olculen_durumlar`: bu istekte ÖLÇÜLEBİLMİŞ birim adı → `ActiveState`. Tetikleyici timer'ın
    kendisi de listedeki bir satırdır; ek `systemctl` çağrısı YOK (birim başına fork, 1.5 sn'lik
    bütçeyi yerdi)."""
    ad = s.get("ad") or "?"
    # ŞABLON BİRİM BURADA ELENMEZ, ÇÜNKÜ HİÇ SORGULANMAZ: `_infra_bilesenler` şablonları
    # `systemctl`e götürmeden `durum=None` + şablon gerekçesiyle geçer, o satırlar aşağıdaki
    # "durum ölçülemedi" dalına düşer ve kendi gerekçelerini taşır. Buraya ikinci bir şablon
    # kontrolü koymak ULAŞILAMAZ bir dal olurdu — mutasyonla sınandı, silindiğinde hiçbir çivi
    # ötmedi; yani okuyucuya "burada bir koruma var" diye yalan söyleyen bir satırdı.
    if s.get("kurulu") is False:
        if s.get("beklenen") is True:
            return "kurulmali", (
                f"`{ad}` bu makineye KURULU DEĞİL ama kurulması bekleniyor: "
                f"{s.get('beklenen_neden') or 'host dizininde birim dosyası var'}. "
                "Kurulum `sudo` ister, operatör işidir")
        if s.get("beklenen") is False:
            return "envanter_gurultusu", (
                f"`{ad}` kurulu değil ve KURULMASI DA BEKLENMİYOR: "
                f"{s.get('beklenen_neden') or 'deploy/ kökünde duran eski/genel kopya'}. "
                "Bu satır bir eksik değil, envanter gürültüsüdür")
        return "olculemedi", (
            f"`{ad}` kurulu değil ama kurulmasının BEKLENİP beklenmediği ölçülemedi "
            f"({s.get('beklenen_neden') or '`beklenen` alanı yok'}) — eylem gerekip gerekmediği "
            "söylenemez")
    durum = s.get("durum")
    if durum is None:
        return "olculemedi", (s.get("durum_neden")
                              or f"`{ad}` için `ActiveState` ölçülemedi ve nedeni de yazılmadı")
    if durum == "failed":
        return "arizali", (
            f"`{ad}` `ActiveState=failed` — birim koşmadı DEĞİL, KOŞTU VE DÜŞTÜ; tetikleyicisi "
            "sağlam olsa bile bu bir arızadır")
    if durum == "active":
        return "kosuyor", f"`{ad}` `ActiveState=active` (alt durum: {s.get('alt_durum') or '—'})"

    # --- Buradan aşağısı: kurulu, ölçüldü, `active` DEĞİL. Hüküm tetikleyiciye bağlı. ---
    tur = s.get("servis_turu")
    if tur != "oneshot":
        _tur_metni = (f"`Type={tur}`" if tur else
                      f"`Type` ÖLÇÜLEMEDİ ({s.get('servis_turu_neden') or 'alan gelmedi'})")
        return "olu", (
            f"`{ad}` `ActiveState={durum}` ve {_tur_metni} — koşumlar arasında dinlenen bir "
            "`oneshot` OLDUĞU ölçülemedi, dolayısıyla bu duruş SAĞLIKLI SAYILAMAZ; koşması "
            "gereken bir servis durmuş olabilir")
    timerlar = s.get("tetikleyen_timerlar") or []
    aktif = [t for t in timerlar if olculen_durumlar.get(t) == "active"]
    if aktif:
        return "sirada_timer", (
            f"`{ad}` `Type=oneshot` ve tetikleyicisi {', '.join(f'`{t}`' for t in aktif)} "
            f"`active` ölçüldü — koşumlar arasında `{durum}` olması BEKLENEN hâldir, arıza değil")
    if timerlar:
        olculemeyen = [t for t in timerlar if t not in olculen_durumlar]
        if olculemeyen:
            return "tetikleyici_olculemedi", (
                f"`{ad}` `Type=oneshot` ve `TriggeredBy={' '.join(timerlar)}`, ama "
                f"{', '.join(f'`{t}`' for t in olculemeyen)} bu istekte ÖLÇÜLMEDİ — timer'ın "
                "aktif olduğu VARSAYILAMAZ, sağlık iddia edilmiyor")
        return "tetikleyici_bozuk", (
            f"`{ad}` `Type=oneshot` ama tetikleyicisi "
            f"{', '.join(f'`{t}` ({olculen_durumlar.get(t)})' for t in timerlar)} — timer aktif "
            "değil, yani bu birim HİÇ koşmuyor olabilir")
    onfailure = s.get("onfailure_kaynaklari") or []
    if onfailure:
        return "ariza_yok_onfailure", (
            f"`{ad}` `Type=oneshot`, timer'ı yok; `OnFailureOf="
            f"{' '.join(onfailure)}` ile tetikleniyor — `{durum}` olması "
            "HİÇBİR ŞEY ARIZALANMADI demektir, mümkün olan en iyi hâl")
    return "tetikleyici_yok", (
        f"`{ad}` `Type=oneshot` ve `{durum}`, ama ne `TriggeredBy` ne `OnFailureOf` bağı "
        "görüldü — elle mi koşuluyor, bağlanmayı mı bekliyor ölçülemedi; sağlık iddia edilmiyor")


def _infra_bilesenler(birimler: list[dict]) -> tuple[list | None, str | None]:
    """MERIDIAN BİLEŞENLERİ — birim başına durum, CPU%, RSS, çalışma süresi, restart sayısı.

    `systemctl` YOKSA BOŞ LİSTE DEĞİL `None` DÖNER. Boş liste panoda "bu makinede Meridian
    bileşeni yok" diye okunur; oysa ölçülen şey "ölçemedim"dir. (YASA: boş gövde 'her şey yolunda'
    DEĞİLDİR.) Süreç taramasına da düşülmedi: `ps` ayrıştırmak, systemd'nin ZATEN otoriter olarak
    tuttuğu bilgiyi tahmine çevirmek olurdu ve macOS'ta koşan bir `python -m meridian...` süreci
    "canlı bileşen" gibi görünürdü — yerel geliştirme makinesini canlı sanmak, bu deponun en
    pahalı hata sınıfı (ölçüm bağlamı tuzağı)."""
    if not shutil.which("systemctl"):
        import platform as _pf
        return None, (f"`systemctl` bu makinede yok ({_pf.system()}) — Meridian bileşenleri systemd "
                      "birimleridir ve durumları yalnız canlı Linux sunucusunda (A1) ölçülebilir; "
                      "süreç taraması bilerek kullanılmadı (tahmini otoriteye çevirirdi)")
    # Makine uptime'ı birim başlangıcını mutlak zamana çevirmek için gerekir; bir kez okunur.
    mak_uptime = None
    up = _proc_oku("uptime")
    if up:
        try:
            mak_uptime = float(up.split()[0])
        except (ValueError, IndexError):  # sessiz-yutma: biçim beklenmedikse birim çalışma süresi ölçülemez; her satır kendi `uptime_s_neden`ini taşır
            pass
    bitis = _time.monotonic() + _SYSTEMCTL_BUTCE_S
    satirlar = []
    for b in birimler:
        s: dict = {"ad": b["ad"], "dosya": b["dosya"], "tur": b["tur"], "sablon": b["sablon"],
                   "birim_dosyasi": b["yol"],
                   # KURULUM BEKLENTİSİ diskten gelir (`_infra_birim_adlari`), systemd'den değil:
                   # systemd kurulmamış bir birim için yalnız `not-found` der, "kurulmalı mıydı"
                   # sorusunun cevabı depodaki YOLDADIR.
                   "beklenen": b.get("beklenen"), "beklenen_neden": b.get("beklenen_neden"),
                   "servis_turu": None, "servis_turu_neden": None,
                   "tetikleyen_timerlar": [], "onfailure_kaynaklari": [],
                   "durum_sinifi": None, "durum_sinifi_neden": None,
                   "kurulu": None, "kurulu_neden": None,
                   "durum": None, "durum_neden": None, "alt_durum": None, "alt_durum_neden": None,
                   "cpu_yuzde": None, "cpu_yuzde_neden": None, "rss_bayt": None, "rss_bayt_neden": None,
                   "uptime_s": None, "uptime_s_neden": None, "restart_n": None, "restart_n_neden": None,
                   "pid": None, "pid_neden": None, "aciklama": None, "aciklama_neden": None}
        if b["sablon"]:
            _sablon = ("ŞABLON birim (`@`): düz adla `systemctl show` SAHTE bir `inactive` döndürür "
                       "— koşan şey şablon değil, örneğidir (`ad@<örnek>.service`). Bu birimin "
                       "gerçek durumu `/api/sprint` üzerinden okunur; buradan UYDURULMAZ")
            for alan in ("kurulu", "durum", "alt_durum", "cpu_yuzde", "rss_bayt", "uptime_s",
                         "restart_n", "pid", "aciklama", "servis_turu"):
                s[f"{alan}_neden"] = _sablon
            satirlar.append(s)
            continue
        if _time.monotonic() >= bitis:
            _butce = (f"zaman bütçesi doldu ({_SYSTEMCTL_BUTCE_S} sn): bu birim bu istekte "
                      "sorgulanmadı — bütçe, 15 sn'de bir yoklanan ucun kilitlenmemesi için var")
            for alan in ("kurulu", "durum", "alt_durum", "cpu_yuzde", "rss_bayt", "uptime_s",
                         "restart_n", "pid", "aciklama", "servis_turu"):
                s[f"{alan}_neden"] = _butce
            satirlar.append(s)
            continue
        ham = _systemctl_show(b["ad"])
        if not ham:
            _yok = "`systemctl show` bu birim için çıktı vermedi (hata/zaman aşımı) — ölçülemedi"
            for alan in ("kurulu", "durum", "alt_durum", "cpu_yuzde", "rss_bayt", "uptime_s",
                         "restart_n", "pid", "aciklama", "servis_turu"):
                s[f"{alan}_neden"] = _yok
            satirlar.append(s)
            continue

        # TETİKLEYİCİ ÜÇLÜSÜ. `Type` timer birimlerinde HİÇ YOKTUR (`.timer` bir servis değildir)
        # ve orada yokluğu normaldir; hükmü kuran `_infra_durum_sinifi` timer'ları zaten
        # `ActiveState` üzerinden okur, `Type`a bakmaz.
        s["servis_turu"] = ham.get("Type") or None
        if s["servis_turu"] is None:
            s["servis_turu_neden"] = (
                "`Type` alanı çıktıda yok/boş — birimin `oneshot` (koşumlar arasında dinlenen) "
                "olup olmadığı ölçülemedi; `.timer` birimlerinde bu NORMALDİR"
                if b["tur"] == "timer" else
                "`Type` alanı çıktıda yok/boş — birimin `oneshot` (koşumlar arasında dinlenen) "
                "olup olmadığı ölçülemedi, bu yüzden duruşu için sağlık İDDİA EDİLEMEZ")
        s["tetikleyen_timerlar"] = _systemd_liste(ham, "TriggeredBy")
        s["onfailure_kaynaklari"] = _systemd_liste(ham, "OnFailureOf")

        yukleme = ham.get("LoadState") or None
        s["kurulu"] = (yukleme == "loaded") if yukleme else None
        if yukleme is None:
            s["kurulu_neden"] = "`LoadState` alanı çıktıda yok — kurulu olup olmadığı ölçülemedi"
        elif yukleme != "loaded":
            # Depoda dosyası olan ama bu makineye KURULMAMIŞ birimler var (örn. taslak
            # `litestream.service`). Onları "inactive" diye basmak, kurulu ama durmuş bir birimle
            # aynı görünürdü — iki farklı gerçek, tek rozet.
            s["kurulu_neden"] = (f"`LoadState={yukleme}` — birim dosyası depoda var ama bu makineye "
                                 "KURULU DEĞİL; durum/kaynak alanları bu yüzden ölçülemez")
        durum = ham.get("ActiveState") or None
        if s["kurulu"] and durum:
            s["durum"], s["alt_durum"] = durum, (ham.get("SubState") or None)
            if s["alt_durum"] is None:
                s["alt_durum_neden"] = "`SubState` alanı çıktıda yok"
        else:
            _d = s["kurulu_neden"] or "`ActiveState` alanı çıktıda yok"
            s["durum_neden"] = s["alt_durum_neden"] = _d

        def _sayi(alan: str):
            v = ham.get(alan)
            try:
                return int(v)
            except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen systemd alanı None döner ve çağıran onu kendi `_neden` metniyle karşılar; 0 yazmak 'ölçüldü, sıfır çıktı' diye okunurdu
                return None

        mem = _sayi("MemoryCurrent")
        if mem is None:
            s["rss_bayt_neden"] = "`MemoryCurrent` çıktıda yok/sayı değil"
        elif mem >= _SYSTEMD_AYARSIZ:
            s["rss_bayt_neden"] = ("`MemoryCurrent` 2^64-1 (systemd'nin AYARSIZ sentineli) — bellek "
                                   "muhasebesi bu birim için açık değil; 18 EB diye BASILMAZ")
        else:
            s["rss_bayt"] = mem

        nr = _sayi("NRestarts")
        if nr is None:
            s["restart_n_neden"] = "`NRestarts` çıktıda yok/sayı değil"
        else:
            s["restart_n"] = nr

        pid = _sayi("MainPID")
        if pid:
            s["pid"] = pid
        else:
            s["pid_neden"] = ("`MainPID` yok ya da 0 — birim koşmuyor ya da ana süreci yok "
                              "(oneshot/timer birimlerinde NORMAL)")

        s["cpu_yuzde"], s["cpu_yuzde_neden"] = _infra_cpu_yuzde(f"birim:{b['ad']}", _sayi("CPUUsageNSec"))

        bas = _sayi("ExecMainStartTimestampMonotonic")
        if bas and mak_uptime is not None:
            s["uptime_s"] = round(mak_uptime - bas / 1e6, 1)
        elif not bas:
            s["uptime_s_neden"] = ("`ExecMainStartTimestampMonotonic` yok/0 — birim hiç başlamamış "
                                   "ya da ana süreci yok; çalışma süresi ölçülemez")
        else:
            s["uptime_s_neden"] = "`/proc/uptime` okunamadı — monotonik başlangıç mutlak süreye çevrilemez"

        s["aciklama"] = ham.get("Description") or None
        if s["aciklama"] is None:
            s["aciklama_neden"] = "`Description` alanı çıktıda yok"
        satirlar.append(s)

    # --- İKİNCİ GEÇİŞ: HÜKÜM. Tek geçişte kurulamaz, çünkü `meridian-backup.service`in sağlığı
    # `meridian-backup.timer`ın ölçülmüş durumuna dayanır ve o satır listede DAHA SONRA gelebilir.
    # Tetikleyiciyi ayrıca `systemctl show` ile sormak birim başına bir fork daha demekti ve 1.5
    # sn'lik bütçeyi yerdi; zaten ölçülmüş satırdan okunuyor. Ölçülemeyen bir tetikleyici hükme
    # GİRMEZ (sözlükte yoktur) ve sınıf "ölçülemedi" olur — sağlık ancak ölçüldüyse iddia edilir.
    olculen_durumlar = {s["ad"]: s["durum"] for s in satirlar if s.get("durum") is not None}
    for s in satirlar:
        s["durum_sinifi"], s["durum_sinifi_neden"] = _infra_durum_sinifi(s, olculen_durumlar)
    return satirlar, None


# ---- İKİNCİ KEŞİF BACAĞI: AYNA KÖRLÜĞÜ (2026-09-01) --------------------------------------------
#
# BİRİNCİ BACAK TEK YÖNLÜDÜR. `_infra_birim_adlari` → `_infra_bilesenler` zinciri DEPODAN
# MAKİNEYE bakar: `deploy/**` altındaki her birim dosyası için "kurulu mu, koşuyor mu" diye sorar.
# Sorduğu soru kümesi repodaki DOSYA LİSTESİYLE sınırlıdır — makinede DURAN ama repoda karşılığı
# OLMAYAN bir birim o bacağa GÖRÜNMEZ, çünkü hakkında hiç soru sorulmaz. Eksiği gösteren bir
# envanter, FAZLAYA kördür.
#
# ÖLÇÜLMÜŞ VAKA (canlı A1, 2026-09-01): `meridian-dash.service` makinede duruyor (`inactive`) ve
# `deploy/` ağacının HİÇBİR yerinde yok. Pano "bileşenler listelendi" diyordu; listelenmeyen bir
# birim vardı ve onu ne kuran ne emekli eden bir kayıt kaldı.
#
# `[]` İLE `None` BURADA İKİ AYRI GERÇEKTİR ve bu ayrım bacağın kendisi kadar önemlidir: boş liste
# "ölçtük, makinede fazlalık yok" der; `None` "ölçemedik" der. Karıştıkları gün pano ÖLÇÜLMEMİŞ
# bir temizlik beyan eder — `bilesenler`de kapatılan kusurun tam kardeşi.
#
# BEDEL (bedel yasası): sorgu `meridian-*` deseniyle DAR tutuluyor. Bu, makinedeki üçüncü taraf
# birimlerini ve desene uymayan `meridian.service`/`litestream.service`i kapsam DIŞINDA bırakır.
# Alternatif — deseni kaldırıp makinenin TÜM birimlerini listelemek — 200+ satırlık bir çıktıyı 8
# sn'lik bir zarfa sokup panoya "beklenmedik" diye basardı; kazanılan sinyal, üretilen gürültünün
# altında kalırdı. Kapsam gövdede `beklenmedik_olcum.kapsam_disi` ile BEYANLIDIR.
_BEKLENMEDIK_DESEN = "meridian-*"
# 5 sn: `_SYSTEMCTL_BUTCE_S` (1,5 sn) ile TOPLANIR — en kötü 6,5 sn ve uç 15 sn'de bir yoklanıyor,
# yani nabız kilitlenmez. Tek fork'tur (birim başına değil), o yüzden birinci bacağın sıkı
# bütçesine ihtiyaç duymaz.
_LIST_UNIT_FILES_TIMEOUT_S = 5.0
# `--no-legend` başlığı susturur ama systemd sürümüne göre `14 unit files listed.` dipnotu
# gelebilir. Dipnotu birim sanmak, panoya var olmayan bir birim adı bastırmak olurdu.
_SYSTEMD_BIRIM_SONEKI = re.compile(
    r"\.(service|timer|socket|path|target|mount|automount|swap|slice|scope|device)$")


def _sablon_koku(ad: str) -> str:
    """`ad@örnek.service` → `ad@.service`; şablon olmayan ad AYNEN döner.

    NEDEN (şablon tuzağının ikinci yüzü): repoda duran dosya `meridian-sprint@.service`dir, ama
    makinede şablonun KALICI BİR ÖRNEĞİ de görünebilir (`meridian-sprint@2026-08-13.service`).
    Örneği ham adıyla kıyaslamak onu "repoda yok" sayardı ve pano her sprint gününde YENİ bir
    sahte "beklenmedik birim" basardı — gürültü, üstelik tarihli ve sonsuz."""
    kok, ayrac, son = ad.rpartition(".")
    if not ayrac or "@" not in kok:
        return ad
    return f"{kok.split('@', 1)[0]}@.{son}"


def _systemctl_birim_dosyalari() -> tuple[list[tuple[str, str | None]] | None, str | None]:
    """Bu MAKİNEDE duran `meridian-*` birim DOSYALARI — `(ad, UnitFileState)` çiftleri + gerekçe.

    ÖLÇÜLEMEZSE BOŞ LİSTE DEĞİL `None`: boş liste çağıranda "fazlalık yok" hükmüne dönüşür ve
    panoya ölçülmemiş bir temizlik olarak gider.

    `list-unit-files` SEÇİLDİ, `list-units` DEĞİL: ikincisi yalnız systemd'nin O AN belleğinde
    tuttuğu birimleri verir ve hiç tetiklenmemiş bir birim orada YOKTUR — aradığımız şey tam
    olarak "duruyor ama kimse dokunmuyor" sınıfıdır. Bedeli: dönen sütun `UnitFileState`tir
    (enabled/disabled/static), `ActiveState` DEĞİL; gövde bunu `durum_alani` ile beyan eder.

    AYRI FONKSİYON OLMASI BİLİNÇLİ (`_systemctl_show` emsali): alt süreç çağrısı testlerde tek
    noktadan saplanabilmeli — ama saplama KOMUTUN KENDİSİNİ de görebilsin diye çağrı burada,
    ayrıştırmayla AYNI yerde duruyor."""
    import subprocess
    yol = shutil.which("systemctl")
    if not yol:
        import platform as _pf
        return None, (f"`systemctl` bu makinede yok ({_pf.system()}) — makinede duran birimler "
                      "ancak systemd'ye sorularak sayılabilir ve bu ölçüm yalnız canlı Linux "
                      "sunucusunda (A1) yapılabilir; süreç taraması bilerek kullanılmadı "
                      "(tahmini otoriteye çevirirdi)")
    komut = [yol, "list-unit-files", _BEKLENMEDIK_DESEN, "--no-legend", "--no-pager"]
    try:
        cp = subprocess.run(komut, capture_output=True, text=True,
                            timeout=_LIST_UNIT_FILES_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as e:
        return None, (f"`systemctl list-unit-files {_BEKLENMEDIK_DESEN}` koşturulamadı — "
                      f"{type(e).__name__}: {e}. Makinedeki birimler bu istekte ÖLÇÜLMEDİ; "
                      "zaman aşımı ya da açılamayan komut 'fazlalık yok' DEMEK DEĞİLDİR")
    if cp.returncode != 0:
        return None, (f"`systemctl list-unit-files {_BEKLENMEDIK_DESEN}` çıkış kodu "
                      f"{cp.returncode} döndürdü (stderr: "
                      f"{' '.join((cp.stderr or '').split())[:200] or '(boş)'}) — makinedeki "
                      "birimler ölçülemedi")
    satirlar: list[tuple[str, str | None]] = []
    for ham in cp.stdout.split("\n"):
        parcalar = ham.split()
        if not parcalar or not _SYSTEMD_BIRIM_SONEKI.search(parcalar[0]):
            continue                 # başlık/dipnot satırı ("14 unit files listed.") birim DEĞİL
        satirlar.append((parcalar[0], parcalar[1] if len(parcalar) > 1 else None))
    return satirlar, None


def _infra_beklenmedik(birimler: list[dict]) -> dict:
    """MAKİNEDE OLUP REPODA OLMAYAN birimler — keşfin ikinci (ters) bacağı.

    `birimler`: `_infra_birim_adlari()["birimler"]`, yani repo BEKLENTİSİNİN tamamı. Kıyas
    `beklenen` bayrağına DEĞİL ADIN VARLIĞINA bakar: `deploy/` kökünde duran (kurulması
    beklenmeyen) bir birim de repo tarafından BİLİNİYOR demektir; onu "beklenmedik" saymak,
    zaten `envanter_gurultusu` diye sınıflanmış bir satırı ikinci kez, bu kez yanlış adla
    bastırırdı."""
    olcum: dict = {
        "komut": f"systemctl list-unit-files '{_BEKLENMEDIK_DESEN}' --no-legend --no-pager",
        "durum_alani": ("`list-unit-files` STATE sütunu = systemd `UnitFileState` "
                        "(enabled/disabled/static/masked) — `ActiveState` DEĞİLDİR: birimin ŞU AN "
                        "koşup koşmadığını bu sütun SÖYLEMEZ"),
        "kapsam_disi": (f"yalnız `{_BEKLENMEDIK_DESEN}` deseni sorgulanır; desene uymayan birimler "
                        "(`meridian.service`, `litestream.service`, üçüncü taraf birimler) bu "
                        "bacağa GÖRÜNMEZ — dar kapsam bilinçli (gürültü bedeli), körlük beyanlı"),
        "makinedeki_birim_n": None,
        "makinedeki_birim_n_neden": None,
        "repo_birim_n": len(birimler),
    }
    makinedeki, neden = _systemctl_birim_dosyalari()
    if makinedeki is None:
        olcum["makinedeki_birim_n_neden"] = neden
        return {"birimler": None, "neden": neden, "olcum": olcum}
    olcum["makinedeki_birim_n"] = len(makinedeki)
    bilinen = {_sablon_koku(b["ad"]) for b in birimler}
    satirlar = [
        {"birim": ad, "durum": durum,
         "durum_neden": None if durum else (
             "`list-unit-files` bu satırda STATE sütunu vermedi — birim dosyasının etkinlik "
             "durumu ölçülemedi")}
        for ad, durum in sorted(makinedeki, key=lambda t: t[0])
        if _sablon_koku(ad) not in bilinen]
    return {"birimler": satirlar, "neden": None, "olcum": olcum}


def _infra_yaslandir(yuk: dict, yas: float) -> dict:
    """Önbellekten servis edilen yükün YAŞ alanlarını zarfın yaşıyla toplar (`_diag_yaslandir`
    emsali, aynı yasa): hiçbir alan içinde bulunduğu zarftan taze olduğunu iddia edemez.
    Ölçülmemiş (None) bir süre YAŞLANDIRILMAZ — 'ölçülemedi' sessizce sayıya dönmesin."""
    out = dict(yuk)
    out["zarf_yasi_s"] = round(yas, 1)
    mak = dict(out.get("makine") or {})
    if isinstance(mak.get("uptime_s"), (int, float)):
        mak["uptime_s"] = round(mak["uptime_s"] + yas, 1)
        out["makine"] = mak
    sur = dict(out.get("surec") or {})
    if isinstance(sur.get("uptime_s"), (int, float)):
        sur["uptime_s"] = round(sur["uptime_s"] + yas, 1)
        out["surec"] = sur
    bl = out.get("bilesenler")
    if isinstance(bl, list):
        out["bilesenler"] = [
            ({**s, "uptime_s": round(s["uptime_s"] + yas, 1)}
             if isinstance(s.get("uptime_s"), (int, float)) else s) for s in bl]
    return out


@app.get("/api/infra")
def api_infra(request: Request, taze: int = 0):
    """MAKİNE + MERİDİAN BİLEŞENLERİ — operatörün AYRI görmek istediği iki kat.

    · `makine`: hostname, platform, çekirdek sayısı, yük ortalaması, CPU yüzdesi, bellek, disk
      doluluğu, çalışma süresi.
    · `surec`: bu API sürecinin kendisi (pid, uptime, CPU%, RSS) — systemd birimiyle AYNI ŞEY DEĞİL.
    · `bilesenler`: `deploy/` altındaki GERÇEK systemd birimleri için durum/CPU%/RSS/uptime/restart.
    · `beklenmedik_birimler`: TERS YÖN — makinede duran ama `deploy/` ağacında karşılığı OLMAYAN
      `meridian-*` birimleri. `bilesenler` eksiği gösterir, bu alan FAZLAYI; ikisi olmadan envanter
      tek yönlüdür (vaka: `meridian-dash.service`, canlı A1, 2026-09-01).

    ÖNBELLEK: 8 sn, `hesaplama_ts` + `onbellekten` + `zarf_yasi_s` ile BEYANLI; `?taze=1` zorlar
    (`/api/diagnostics` deseni). Ölçülemeyen HER alan `None` + neden taşır — 0 yazmak yalandır."""
    _auth(request)
    anahtar = str(getattr(config, "STATE", ""))
    if not taze:
        hit = _INFRA_CACHE.get(anahtar)
        if hit:
            yuk, at = hit
            yas = _time.monotonic() - at
            if yas < INFRA_TTL_S:
                return {**_infra_yaslandir(yuk, yas), "onbellekten": True}
    kaynak = _infra_birim_adlari()
    bilesenler, bilesen_neden = _infra_bilesenler(kaynak["birimler"])
    beklenmedik = _infra_beklenmedik(kaynak["birimler"])
    import datetime as _dt          # dosyanın konvansiyonu: datetime fonksiyon içinde import edilir
    yuk = {
        "hesaplama_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "onbellekten": False, "zarf_yasi_s": 0.0, "ttl_s": INFRA_TTL_S,
        "makine": _infra_makine(),
        "surec": _infra_surec(),
        "bilesenler": bilesenler,
        "bilesenler_olculemedi_neden": bilesen_neden,
        # İKİNCİ KEŞİF BACAĞI — ters yön: makinede olup repoda OLMAYAN birimler.
        # Gerekçe alanı `<alan>_neden` KARDEŞİ olarak adlandırıldı (`beklenmedik_neden` değil):
        # `tests/test_pano_altyapi_v287.py::_gerekcesiz_none` GENEL taraması kardeş adı arıyor ve
        # kısa ad o taramanın DIŞINDA kalırdı — yani gerekçe bir gün düşse hiçbir çivi ötmezdi.
        "beklenmedik_birimler": beklenmedik["birimler"],
        "beklenmedik_birimler_neden": beklenmedik["neden"],
        "beklenmedik_olcum": beklenmedik["olcum"],
        "bilesen_kaynagi": {"dizin": kaynak["dizin"], "birim_n": len(kaynak["birimler"]),
                            "systemctl_yolu": shutil.which("systemctl"),
                            "systemctl_yolu_neden": None if shutil.which("systemctl")
                            else "`systemctl` PATH'te yok — bu makine systemd koşmuyor",
                            "olculemedi_neden": kaynak["olculemedi_neden"]},
        "olcum_yolu": "stdlib (psutil YOK; /proc + os + shutil.disk_usage + systemctl)",
    }
    _INFRA_CACHE.clear()            # tek girdi: kum havuzu anahtarları birikip sızmasın (diag emsali)
    _INFRA_CACHE[anahtar] = (yuk, _time.monotonic())
    return yuk


# ------------------------------------------------------------------ /api/roadmap ---------------
#
# ROADMAP.md 562 KB / 4622 satırdır ve panonun tahtası odur. Ayrıştırıcının TEK işi markdown
# yapısını (başlıklar + madde listeleri) veri hâline getirmektir; YORUM ÜRETMEZ.
#
# İŞARETSİZ KALEM "AÇIK" DEĞİL "BELİRSİZ"dir. Bu ayrım bu ucun en önemli satırıdır: 419 maddenin
# çoğu düzyazıdır ve durum işareti taşımaz. Onları "açık" saymak, tahtanın üstüne ÖLÇÜLMEMİŞ bir
# sayı yazmak olurdu — ve o sayı yönetim kararına dönüşürdü. `belirsiz` dürüst olandır.
#
# ÜSTÜ ÇİZİLİ KAPANIŞ KAPALI DEĞİLDİR. Dosyada `~~✅ KAPANDI~~ — yukarıda ✅ (tarihçe)` ve
# `~~⟳ YENİDEN AÇILDI~~` desenleri GERÇEKTEN var: kapanış iddiası sonradan GERİ ALINMIŞ demektir.
# Naif bir `"✅" in satır` ayrıştırıcısı onu kapalı sayar ve tahta yalan söyler. Bu yüzden önce
# üstü çizili aralıklar SÖKÜLÜR, işaret ancak KALAN metinde aranır.
_ROADMAP_HAM_TAVAN = 400
_ROADMAP_BASLIK_TAVAN = 160
# Durum ROZETİNİN arandığı alan (gerekçe `_roadmap_madde_durumu`da). 160: dosyadaki en uzun rozet
# başlıkları (`**✅ SB-4 — DAMGASIZ YAZIM BEKÇİSİ (KAPANDI v216, dağıtım #2 …)**`) buna sığıyor.
_ROADMAP_ISARET_ALANI = 160
_ROADMAP_CACHE: dict = {}
_ROADMAP_MADDE = re.compile(r"^(\s*)([-*]) (\S.*)$")
_ROADMAP_BASLIK = re.compile(r"^(#{1,6})\s+(.*)$")
_ROADMAP_NO = re.compile(r"^(§[0-9∞]+)\s*(.*)$")
_ROADMAP_CIZIK = re.compile(r"~~(.+?)~~", re.S)
# KAPANIŞ İMLERİ — TEK KAYNAK. Aynı desen iki yerde okunuyordu (rozet araması + üstü-çizili geri
# alma kontrolü) ve iki kopya sessizce ayrışır; artık tek yerde.
#
# SÖZCÜK SINIRI, VE NEDEN ÖLÇÜLDÜ (2026-08-31): sınırsız desen kelime İÇİNDE de eşliyordu.
# İki ölçülmüş vaka: (1) `§2`nin "chop BÜTÇE-KAPALILIĞI — OPERATÖR KARARI BEKLİYOR" satırı,
# içindeki "KAPALI" yüzünden `kapali` sayılıyordu — kalem gerçekten kapalıydı ama ayrıştırma
# YANLIŞ NEDENLE doğruydu; (2) daha ağırı, `§3`ün WP özet tablosunda BEŞ AKTİF CEPHE
# (`WP1`·`WP4`·`WP5`·`WP7`·`WP8`) panoda "kapalı" okunuyordu, çünkü hücre düzyazısında "KAPANDI"
# geçiyor ve rozet alanına düşüyordu. Tahtanın yalan söylediği yer tam olarak burasıydı.
#
# `\b` Türkçe eklerde de doğru çalışır: desen `str` üstünde UNICODE modda koşar, yani "Ğ/İ/Ş"
# sözcük karakteridir. EŞLEŞMEZ: "KAPALILIĞI" · "KAPANDIĞI" · "KAPALIDIR" · "TAMAMLANDIĞINDA".
# EŞLEŞİR: "✅ KAPANDI" · "**KAPALI**" · "BÜTÇE-KAPALI" · "KAPANDI-BAYAT" · "KAPALI KALIR".
# `✅` bir EMOJİdir ve sözcük sınırı almaz (yanındaki `\b` anlamsız olurdu) — bilerek dışarıda.
_ROADMAP_KAPANIS = r"(✅|\bKAPANDI\b|\bKAPALI\b|\bTAMAMLANDI\b)"

# ---- §1 MADDE ŞEMASI (docs/TASARIM-ROADMAP-STANDART-2026-09-01.md) ------------------------------
#
# 2026-09-01 göçünde belgenin YAŞAYAN bölümleri tek bir başlık gramerine çevrildi:
#
#     - **[TSK-041] Yansıma mükerrerlik kapısı** — status: INTERIM · born: 2026-09-01 ·
#       owner: rol1 · size: S-M · trigger: —
#
# ve `§2 TAHTA`nın tabloları AYNI alanları sütun olarak taşıyor
# (`| id | name | status | owner | size | trigger |`). Bu yüzden durum artık DÜZYAZIDA ARANMAZ,
# BEYAN EDİLDİĞİ ALANDAN OKUNUR.
#
# NEDEN BU AYRIM ÖLÇÜLDÜ (2026-08-31 → 09-01, `tests/test_tahta_hijyeni_v337.py` iki kırmızısı):
# eski sözlük (`KAPANDI`/`BLOKE`/`ASKIDA`/`AÇIK`) satırın HER hücresinde aranıyordu ve göçten
# sonra iki §2 satırı düzyazısı yüzünden "kapalı" okundu — `TSK-062`nin tetiği "learn program
# boyunca KAPALI" diyor, `TSK-077`nin adı "…2026-08-24 elemesinde KAPANDI" diyor. İkisi de AÇIK
# kalemdi. Sözlüğü genişletmek TEK BAŞINA bunu çözmezdi (satır o zaman "çok işaretli" olurdu);
# çözen şey şemanın kendisidir: rozet artık KENDİ SÜTUNUNDA yaşıyor ve başka sütun rozet alanı
# DEĞİLDİR. Bedeli de ölçüldü ve küçüktür (bedel yasası): şema tablolarında düzyazı sütunlarının
# eski-sözlük taraması KAYBEDİLİR — kaybedilen sinyalin tamamı yukarıdaki iki yanlış pozitifti,
# çünkü şemada kapanış zaten `status: DONE(...)` ile söylenir.
#
# ESKİ SÖZLÜK EMEKLİ DEĞİL: `§7 KARAR GÜNLÜĞÜ` · `§8 ARŞİV` · `§8.T TAHTA ARŞİVİ` ve göç ÖNCESİ
# tarihçe blokları hâlâ rozet-düzyazısıyla yazılmıştır (operatör onaylı muafiyet, spec §3) —
# şemaya uymayan her satır ESKİ yolla ölçülmeye devam eder ve `sayim.sema.muaf_tarihce`de sayılır.
_ROADMAP_SEMA_BASLIK = re.compile(r"^\*\*\[([^\]]+)\]\s+([^*]*?)\*\*\s+—\s+(.*)$")
# Parantez İSTEĞE BAĞLI ve önündeki boşluk SERBEST bırakıldı: `§2` tabloları (v351'in bullet
# gramerinin DIŞINDA — o çivi bilinçli olarak yalnız `- **[` satırlarını ölçer) gerçekte
# `QUEUED (trigger karşılandı: …)` ve `OPERATOR (operatör 2026-08-16: "beklet")` biçimleri
# taşıyor. Daraltmak bu satırları "sözlük dışı" gösterirdi — ölçülmüş bir yanlış pozitif.
# `.*` AÇGÖZLÜdür ve bu bilinçli: `GATED(EDG-062(b) inişinden sonra)` iç içe parantez taşıyor.
_ROADMAP_SEMA_STATUS = re.compile(
    r"^(ACTIVE|QUEUED|INTERIM|GATED|OPERATOR|DONE|DROPPED)\s*(?:\((.*)\))?$", re.S)
# ATIF SATIRI — `§2`de ölçülen üçüncü biçim (3 satır: TSK-069/051/063). Kalem tahtada İKİ kez
# görünür: gerçek satırı bir alt bölümde, ikinci satır yalnız "bu blok da o kaleme bağlı" kaydı.
# Durumu burada ÖLÇÜLMEZ — ve uydurulmaz: `status` None kalır, nedeni alanında taşınır.
_ROADMAP_SEMA_ATIF = re.compile(r"^\(\s*bkz\.\s*(.+?)\s*\)$", re.S)
_ROADMAP_SEMA_ALANLARI = ("status", "born", "owner", "size", "trigger")
# §6 KART ENDEKSİ `born` TAŞIMAZ (spec §2 tarihli eki): kartın doğum tarihi kart dosyasının
# kendi künyesindedir; ROADMAP'e ikinci bir kopya koymak tek-kaynak yasasını çiğnerdi.
_ROADMAP_KART_ALANLARI = ("status", "owner", "size", "trigger")
_ROADMAP_SEMA_TABLO_BASLIKLARI = ("id", "name", "status", "owner", "size", "trigger")
# Şema sözlüğü → bu ucun KENDİ durum kovaları. İki sözlük AYRI şeylerdir ve öyle kalmalı:
# şema `status`u belgenin dilidir (spec §1, donuk), `durum` panonun beş kovasıdır (bu ucun
# 2026-08-25'ten beri taşıdığı sözleşme). Eşleme burada TEK yerde yazılır.
_ROADMAP_STATUS_DURUM = {"ACTIVE": "acik", "QUEUED": "acik", "INTERIM": "acik",
                         "GATED": "askida", "OPERATOR": "bloke",
                         "DONE": "kapali", "DROPPED": "kapali"}
# Spec §1 ÜST SINIFLANDIRMASI — "AÇIK = ACTIVE·QUEUED·INTERIM·GATED·OPERATOR,
# KAPALI = DONE·DROPPED". Panonun tahtası bu iki grubu çizer; grubu yüzeyde yeniden kurmak
# aynı kuralın ikinci kopyası olurdu (tek-kaynak yasası), o yüzden gövdede taşınır.
_ROADMAP_STATUS_SINIFI = {s: ("KAPALI" if s in ("DONE", "DROPPED") else "AÇIK")
                          for s in _ROADMAP_STATUS_DURUM}
# `atif` ALTINCI KOVA DEĞİL YEDİNCİ: `cok_isaretli` "iki rozet taşıyor" der, `atif` "rozeti
# BAŞKA satırda" der. İkisini aynı kovaya koymak, ölçülen iki ayrı olguyu tek isim altında
# gizlerdi — ve `belirsiz`e koymak daha kötüsü olurdu: satır durumunu SÖYLÜYOR, ölçülmemiş değil.
_ROADMAP_DURUM_KOVALARI = ("kapali", "bloke", "askida", "acik", "belirsiz", "atif")


def _roadmap_alanlari(govde: str) -> tuple[list[str], dict[str, str]]:
    """`status: X · born: Y · …` → (SIRALI anahtar listesi, anahtar→değer).

    PARANTEZ DERİNLİĞİNE DUYARLI, ve bu şart: gerçek veri
    `status: DONE(2026-08-31 · v349, 28 çivi) · born: …` taşıyor. Naif bir `split(" · ")`
    `DONE(...)` İÇİNDEKİ ayracı üst-düzey alan ayracı sanır, alan sayısı bozulur ve tamamen
    sağlam bir satır "şemasız" görünür. Sıra ayrıca DÖNDÜRÜLÜR (sözlük değil liste): şema alan
    SIRASINI de bağlar ve `dict` sırasına güvenmek niyeti okuyucudan gizlerdi."""
    parcalar: list[str] = []
    derinlik, tampon, i, n, ayrac = 0, [], 0, len(govde), " · "
    while i < n:
        ch = govde[i]
        if ch == "(":
            derinlik += 1
        elif ch == ")":
            derinlik -= 1
        elif derinlik == 0 and govde[i:i + len(ayrac)] == ayrac:
            parcalar.append("".join(tampon))
            tampon = []
            i += len(ayrac)
            continue
        tampon.append(ch)
        i += 1
    parcalar.append("".join(tampon))

    anahtarlar: list[str] = []
    sozluk: dict[str, str] = {}
    for parca in parcalar:
        if ":" in parca:
            anahtar, deger = parca.split(":", 1)
            anahtarlar.append(anahtar.strip())
            sozluk[anahtar.strip()] = deger.strip()
    return anahtarlar, sozluk


def _roadmap_status_coz(ham: str) -> tuple[str | None, str | None, str | None]:
    """Bir `status` DEĞERİNİ çözer → (status, status_detay, status_neden).

    Üç çıkış, üçü de ölçülmüş biçimlerden: (1) sözlükteki değer (parantezli detay ayrı alana
    iner — spec §1: parantez GATED/DONE/DROPPED'a aittir ve DETAYdır, durumun kendisi değil);
    (2) `(bkz. …)` atfı → status None + NEDEN (durumu başka satırda yaşıyor); (3) tanınmayan
    değer → status None + NEDEN. Hiçbir yolda değer UYDURULMAZ."""
    deger = (ham or "").strip()
    m = _ROADMAP_SEMA_STATUS.match(deger)
    if m:
        detay = (m.group(2) or "").strip() or None
        return m.group(1), detay, None
    atif = _ROADMAP_SEMA_ATIF.match(deger)
    if atif:
        # Metin EKRANA çıkıyor (pano satırın altında basıyor): ters tırnak/alan adı gibi iç
        # ayrıntı taşımaz — v323'ün arayüz dili kuralının aynı gerekçesi.
        return None, None, (f"durum bu satırda yazmıyor: satır {atif.group(1)} kalemine ATIF "
                            "yapıyor, kalemin durumu kendi satırında okunur")
    if not deger:
        return None, None, "`status` alanı boş — durum yazılmamış"
    return None, None, (f"`status` değeri şema sözlüğünde yok: {deger[:120]!r} "
                        "(ACTIVE · QUEUED · INTERIM · GATED · OPERATOR · DONE · DROPPED)")


def _roadmap_sema_kur(kimlik: str, ad: str, alanlar: dict[str, str], *, bolum_no: str | None,
                      kaynak: str) -> dict:
    """Çözülmüş alanlardan şema sözlüğünü kurar. ÖLÇÜLEMEYEN ALAN None KALIR."""
    status, detay, neden = _roadmap_status_coz(alanlar.get("status", ""))
    return {"id": kimlik or None, "name": ad or None,
            "status": status, "status_detay": detay, "status_neden": neden,
            "sinif": _ROADMAP_STATUS_SINIFI.get(status) if status else None,
            # `born` tablo biçiminde YOKTUR (şemanın tablo sütunları arasında değil) — bu
            # None bir ölçüm kusuru değil, biçimin kendisi; `sema_kapsam` bunu beyan eder.
            "born": alanlar.get("born") or None,
            "owner": alanlar.get("owner") or None,
            "size": alanlar.get("size") or None,
            "trigger": alanlar.get("trigger") or None,
            "section": bolum_no, "kaynak": kaynak}


def _roadmap_sema_durumu(sema: dict) -> tuple[str, str | None]:
    """Şema satırının bu ucun durum kovasındaki karşılığı → (durum, kanıt)."""
    if sema["status"] is None:
        if sema["status_neden"] and "ATIF" in sema["status_neden"]:
            return "atif", sema["status_neden"]
        return "belirsiz", sema["status_neden"]
    return _ROADMAP_STATUS_DURUM[sema["status"]], f"status: {sema['status']}"


def _roadmap_madde_semasi(baslik_satiri: str,
                          bolum_no: str | None) -> tuple[dict | None, str | None]:
    """Bir MADDE başlık satırını §1 şemasına karşı çözer → (şema | None, ihlal nedeni | None).

    ÜÇ SINIF, VE İKİSİ KARIŞTIRILMAZ:
      · şema  → (sözlük, None)
      · muaf  → (None, None)   şema BİÇİMİNDE değil: §7/§8 düzyazısı, tarihçe satırı, serbest
                               metin. Bunlar İHLAL DEĞİLDİR (operatör onaylı muafiyet, spec §3)
                               ve `muaf_tarihce` sayacına gider.
      · ihlal → (None, neden)  şema BİÇİMİNDE (`- **[KİMLİK] Ad** — …`) AMA alanları tutmuyor.
                               Bu bir bozulmadır ve ADIYLA sayılır — muaf sayacına karışsaydı
                               şema çürümesi sessizce tarihçe gibi görünürdü.

    SATIR başlığı alınır, KATLANMIŞ gövde değil: bu dosya madde gövdelerini sarıyor ve `What:`
    / `Why:` satırları maddeye katlanıyor — onları alan gövdesine karıştırmak alan sayımını
    bozardı. `§6` kart endeksinde alan seti farklıdır (`born` yok, spec §2 tarihli eki)."""
    m = _ROADMAP_SEMA_BASLIK.match(baslik_satiri.strip())
    if not m:
        return None, None
    kimlik, ad, govde = m.group(1).strip(), m.group(2).strip(), m.group(3)
    anahtarlar, alanlar = _roadmap_alanlari(govde)
    beklenen = _ROADMAP_KART_ALANLARI if bolum_no == "§6" else _ROADMAP_SEMA_ALANLARI
    if tuple(anahtarlar) != beklenen:
        return None, (f"[{kimlik}] alan sırası {list(beklenen)} bekleniyordu, bulunan: "
                      f"{anahtarlar}")
    sema = _roadmap_sema_kur(kimlik, ad, alanlar, bolum_no=bolum_no, kaynak="madde")
    return sema, None


def _roadmap_sema_sayimi(bolumler: list) -> dict:
    """Şema sayacı — TEK yerde hesaplanır ve iki yerden çağrılır (belge geneli + `?bolum=`
    süzgeci). İki kopya sessizce ayrışırdı; ayrışan sayaç ekranda ayrışma UYARISI değil,
    ayrışmanın KENDİSİ olurdu."""
    sayac = {"madde_n": 0, "tablo_satir_n": 0, "muaf_tarihce": 0, "ihlal_n": 0}
    status: dict[str, int] = {s: 0 for s in _ROADMAP_STATUS_DURUM}
    sinif = {"AÇIK": 0, "KAPALI": 0, "olculemedi": 0}

    def _say(sema: dict | None) -> None:
        if sema is None:
            return
        if sema["status"] is None:
            sinif["olculemedi"] += 1
        else:
            status[sema["status"]] += 1
            sinif[_ROADMAP_STATUS_SINIFI[sema["status"]]] += 1

    def _gez(bs: list) -> None:
        for b in bs:
            for m in b["maddeler"]:
                if m["sema"] is None:
                    sayac["muaf_tarihce"] += 1
                else:
                    sayac["madde_n"] += 1
                _say(m["sema"])
            sayac["ihlal_n"] += len(b.get("sema_ihlal") or [])
            for t in b["tablolar"]:
                for r in t["satirlar"]:
                    if r["sema"] is not None:
                        sayac["tablo_satir_n"] += 1
                    _say(r["sema"])
            _gez(b["alt_bolumler"])

    _gez(bolumler)
    return {**sayac, "status": status, "sinif": sinif}


def _ROADMAP_TABLO_SATIRI(l: str) -> bool:
    """Markdown tablo satırı mı? Boru ile BAŞLAR, boru ile BİTER ve en az iki boru taşır.

    "Boru ile başlar" TEK BAŞINA YETMEZ — ölçüldü (2026-08-25, ROADMAP satır 3639): sarılmış bir
    düzyazı satırı `|Δclose|/c, hacim oranı) …` diye başlıyor ve gevşek kural onu tablo sanıp
    içinde bulunduğu maddenin gövdesinden KOPARIYORDU. Sonu da boru olma şartı bu yanlış pozitifi
    kapatır: gerçek satırlar (`| kalem | WP | durum |`) kapanış borusunu taşır."""
    k = l.strip()
    return k.startswith("|") and k.endswith("|") and k.count("|") >= 2


def _roadmap_yolu() -> Path:
    """Tahtanın kaynağı — depo kökündeki `ROADMAP.md`. Ad TAHMİN EDİLMEDİ, diskte ölçüldü
    (2026-08-25: `ROADMAP.md` 562 515 bayt / 4622 satır; `docs/` altındakiler tarihli türevlerdir
    ve SSoT değildir)."""
    return Path(config.ROOT) / "ROADMAP.md"


def _roadmap_madde_durumu(metin: str) -> tuple[str, str | None, bool]:
    """(durum, kanıt, üstü_çizili). Durum sözlüğü: kapali · bloke · askida · acik · belirsiz.

    İŞARET KALEMİN BAŞINDA ARANIR, DÜZYAZISINDA DEĞİL. Bu satır da bir ölçümün bedelidir: tüm
    gövdede arayan ilk sürüm, 763 karakterlik bir BULGU paragrafının ortasındaki bir ✅'yi görüp
    kalemi "kapandı" saydı. Bu dosyada durum işareti bir ROZETTİR ve rozet başta durur
    (`- **✅ KAPANDI — …`, `- **📋 SB-2 …`, `- **BLOKE:** …`); cümlenin ortasındaki ✅ bir işaret
    değil, bir ANLATIDIR. Aranan alan: üstü-çizili aralıklar söküldükten SONRA kalan metnin ilk
    `_ROADMAP_ISARET_ALANI` karakteri.

    BİLİNEN SINIR (gizlenmiyor): "→ yukarıda ✅ (tarihçe)" gibi tarihçe İŞARETÇİLERİ de rozet
    alanına düşerse `kapali` etiketlenir. Bunlar `ustu_cizili=True` taşır ve `durum_kanit` ham
    işareti verir — tüketici ikisini birden görüp kendi hükmünü kurabilir. Düzyazıyı yorumlayacak
    bir sezgisel eklemedim: sezgisel, ölçülmemiş bir hükmü ölçülmüş gibi gösterirdi."""
    cizili = bool(_ROADMAP_CIZIK.search(metin))
    kalan = _ROADMAP_CIZIK.sub(" ", metin)[:_ROADMAP_ISARET_ALANI]
    for durum, desen in (("kapali", _ROADMAP_KAPANIS),
                         ("bloke", r"\bBLOKE\b"),
                         ("askida", r"\bASKIDA\b"),
                         ("acik", r"\bAÇIK\b")):
        m = re.search(desen, kalan)
        if m:
            return durum, m.group(0), cizili
    if cizili and re.search(_ROADMAP_KAPANIS, metin[:_ROADMAP_ISARET_ALANI]):
        # Kapanış işareti VARDI ama üstü çizilmişti → "kapandı" DEĞİL; ölçülmüş bir geri alma.
        return "belirsiz", "kapanış işareti ÜSTÜ ÇİZİLİ (geri alınmış) — kapalı sayılmaz", cizili
    return "belirsiz", None, cizili


def _roadmap_madde_basligi(metin: str) -> str:
    """Kalın başlangıç (`**...**`) varsa başlıktır; yoksa ilk cümle/tire öncesi kırpılır."""
    m = re.match(r"^\*{2}(.+?)\*{2}", metin, re.S)
    ham = m.group(1) if m else re.split(r"\s+[—–]\s+|(?<=[.:])\s", metin, maxsplit=1)[0]
    ham = _ROADMAP_CIZIK.sub(r"\1", ham).replace("**", "").strip().rstrip(":").strip()
    return ham[:_ROADMAP_BASLIK_TAVAN]


def _roadmap_ayristir(metin: str, *, yol: str, bayt: int, mtime: str | None,
                      tam: bool = False) -> dict:
    """Markdown'ı bölüm ağacına + madde listelerine çevirir. YORUM ÜRETMEZ, yalnız yapı çıkarır."""
    satirlar = metin.split("\n")
    belge_basligi = None
    kok: list = []                 # üst düzey (## ) bölümler
    yigin: list = []               # (seviye, bölüm) — açık başlık zinciri
    onsoz: dict | None = None      # ilk başlıktan ÖNCEki maddeler (varsa) kaybolmasın
    fence = False

    def _yeni(seviye: int, ham_baslik: str, satir_no: int) -> dict:
        no = None
        govde = ham_baslik
        m = _ROADMAP_NO.match(ham_baslik.strip())
        if m:
            no, govde = m.group(1), m.group(2)
        return {"no": no, "baslik": govde.strip() or ham_baslik.strip(),
                "ham_baslik": ham_baslik.strip(), "seviye": seviye, "satir": satir_no,
                "maddeler": [], "alt_bolumler": []}

    def _aktif() -> dict | None:
        return yigin[-1][1] if yigin else None

    acik: dict | None = None       # devam satırı katlanabilecek AÇIK madde (yoksa None)
    for i, l in enumerate(satirlar, 1):
        if l.lstrip().startswith("```"):
            fence = not fence
            acik = None
            continue
        if fence:
            continue
        if not l.strip():
            # BOŞ SATIR MADDEYİ KAPATIR. Bu satır bir ölçümün bedelidir: kapatmayan ilk sürüm
            # §0'ın son maddesine (satır 58) sonraki İKİ paragrafı katladı ve o paragrafların
            # birindeki "✅ kapalı" LEJANTI maddeyi "kapandı" diye etiketledi. Yani tahtanın durum
            # sütunu, madde ile hiç ilgisi olmayan bir açıklama satırından geliyordu. Markdown'da
            # boş satırdan sonraki gövde ZATEN girintili olmak zorundadır; bu dosya satırlarını
            # bitişik sardığı için yalnız BİTİŞİK satırlar katlanır.
            acik = None
            continue
        if not _ROADMAP_TABLO_SATIRI(l):
            # TABLO BLOĞUNU BOŞ SATIR BÖLMEZ, DÜZ METİN BÖLER. Ölçüldü (2026-08-25): ROADMAP'in
            # §2 TAHTA tabloları ortalarında boş satır taşıyor (284-296 arası üç tane) ve
            # bitişiklik varsayan ilk sürüm bloğu ÜÇE bölüp ayraçsız kalan iki parçayı SESSİZCE
            # düşürdü — `BLOKE`/`ASKIDA` sayaçları bu yüzden 0 görünüyordu. Boş satır burada hiç
            # görünmez (yukarıda `continue` edilir); kesinti işareti yalnız GERÇEK metin için.
            _ht = _aktif() or onsoz
            if _ht is not None and _ht.get("_tablo_ham"):
                _ht["_tablo_ham"].append((i, None))
        hb = _ROADMAP_BASLIK.match(l)
        if hb:
            acik = None
            seviye, ham_baslik = len(hb.group(1)), hb.group(2)
            if seviye == 1 and belge_basligi is None:
                belge_basligi = ham_baslik.strip()
                continue
            if seviye == 1:
                continue           # ikinci bir `#` başlık: belge içi ayraç, bölüm değil
            b = _yeni(seviye, ham_baslik, i)
            while yigin and yigin[-1][0] >= seviye:
                yigin.pop()
            if yigin:
                yigin[-1][1]["alt_bolumler"].append(b)
            else:
                kok.append(b)
            yigin.append((seviye, b))
            continue
        mm = _ROADMAP_MADDE.match(l)
        if mm:
            girinti, govde = len(mm.group(1)), mm.group(3)
            hedef = _aktif()
            if hedef is None:
                if onsoz is None:
                    # Başlıksız önsöz maddeleri SESSİZCE DÜŞMEZ: sayım dosyayla tutarlı kalmalı.
                    onsoz = _yeni(2, "(başlıksız önsöz)", 1)
                    onsoz["no"] = None
                hedef = onsoz
            acik = {"satir": i, "girinti": girinti, "_ham": [govde]}
            hedef["maddeler"].append(acik)
            continue
        if l.lstrip().startswith(">"):
            acik = None            # alıntı bloğu maddenin devamı değildir (§2'nin doğrulama bloğu)
            continue
        if _ROADMAP_TABLO_SATIRI(l):
            # TABLOLAR AYRI BİR SINIF — VE BU DEPODA ASIL TAHTA ONLARDIR. Ölçüldü (2026-08-25):
            # dosyada 13 tablo / 194 satır var ve `BLOKE:`/`ASKIDA:` durumlarının TAMAMI tablo
            # hücrelerinde yaşıyor (§2 TAHTA bir tablodur, liste değil). Yalnız madde listelerini
            # ayrıştıran bir uç `bloke: 0` derdi — ölçmediği bir şeyi "yok" diye bildirmek, bu
            # deponun birinci yasasının ihlali. Satır maddeye KATLANMAZ: tablo hücresi bir
            # maddenin devamı değildir.
            acik = None
            hedef = _aktif() or onsoz
            if hedef is not None:
                hedef.setdefault("_tablo_ham", []).append((i, l.strip()))
            continue
        # Bitişik devam satırı: bu dosya madde gövdelerini sarıyor, katlanmazsa metin yarım kalır.
        if acik is not None:
            acik["_ham"].append(l.strip())

    if onsoz is not None:
        kok.insert(0, onsoz)

    sayim_durum = {k: 0 for k in _ROADMAP_DURUM_KOVALARI}
    tablo_durum = {**{k: 0 for k in _ROADMAP_DURUM_KOVALARI}, "cok_isaretli": 0}
    tablo_sayaci = {"tablo": 0, "satir": 0, "atlanan": 0}

    def _hucreler(satir: str) -> list[str]:
        """`| a | b |` → ["a", "b"]. Kenar borularının ürettiği boş uçlar atılır."""
        parcalar = satir.split("|")
        if parcalar and not parcalar[0].strip():
            parcalar = parcalar[1:]
        if parcalar and not parcalar[-1].strip():
            parcalar = parcalar[:-1]
        return [x.strip() for x in parcalar]

    def _sema_satiri_kur(no: int, hucreler: list[str], kok_no: str | None) -> dict:
        """`| id | name | status | owner | size | trigger |` satırını ŞEMA olarak kurar.

        DÜZYAZI SÜTUNLARI TARANMAZ ve `hucre_durum` bunu OLDUĞU GİBİ söyler: yalnız `status`
        sütunu rozet taşır, kalanı `belirsiz`dir — çünkü kalanı VERİdir, rozet değil. Eski
        sürüm hepsini tarıyordu ve `TSK-062`nin tetiğindeki "…boyunca KAPALI" ile `TSK-077`nin
        adındaki "…elemesinde KAPANDI" satırları kapalı gösteriyordu (v337 iki kırmızısı)."""
        kimlik, ad = hucreler[0], hucreler[1]
        alanlar = dict(zip(_ROADMAP_SEMA_TABLO_BASLIKLARI[2:], hucreler[2:]))
        sema = _roadmap_sema_kur(kimlik, ad, alanlar, bolum_no=kok_no, kaynak="tablo")
        durum, kanit = _roadmap_sema_durumu(sema)
        hucre_durum = ["belirsiz"] * len(hucreler)
        sutun = _ROADMAP_SEMA_TABLO_BASLIKLARI.index("status")
        if durum != "belirsiz":
            hucre_durum[sutun] = durum
        tablo_durum[durum] += 1
        tablo_sayaci["satir"] += 1
        kirpildi = (not tam) and any(len(h) > _ROADMAP_HAM_TAVAN for h in hucreler)
        return {"satir": no,
                "hucreler": [h if tam or len(h) <= _ROADMAP_HAM_TAVAN
                             else h[:_ROADMAP_HAM_TAVAN] for h in hucreler],
                "hucre_kirpildi": kirpildi,
                "hucre_uzunluk": [len(h) for h in hucreler],
                "hucre_durum": hucre_durum,
                "durum": durum,
                # ŞEMA SATIRI TEK HÜKÜMLÜDÜR: rozet tek sütunda yaşar, çelişki DOĞAMAZ —
                # `durum` asla None olmaz ve `cok_isaretli` kovası bu satırlarda boş kalır.
                "durum_neden": None if durum != "belirsiz" else sema["status_neden"],
                "durum_kanitlari": ([{"sutun": sutun, "durum": durum, "kanit": kanit}]
                                    if durum != "belirsiz" else []),
                "ustu_cizili": bool(_ROADMAP_CIZIK.search(" ".join(hucreler))),
                "sema": sema}

    def _tablolari_kur(b: dict, kok_no: str | None) -> list:
        """Bitişik `|` satırlarını tablolara böler; başlık + ayraç + satırlar.

        DURUM HÜCRE HÜCRE ARANIR, satırın tamamında DEĞİL: tablo satırı birden çok sütundur ve
        rozet KENDİ hücresindedir (`| kalem | WP | **BLOKE: operatör** |`). Satırın tamamını tek
        metin sayan bir arama, `kalem` sütunundaki düzyazıyı da rozet alanına sokardı — madde
        tarafında ölçülüp düzeltilen kusurun aynısı."""
        ham = b.pop("_tablo_ham", [])
        tablolar, blok, atlanan = [], [], []

        def _ayrac(l: str) -> bool:
            return bool(re.fullmatch(r"[\s|:\-]+", l)) and "-" in l

        def _bitir(blok):
            """Bir `|` bloğunu tablolara böler. AYRAÇ satırı (`|---|`) tabloyu başlatır; bir blokta
            birden çok ayraç varsa üst üste binmiş birden çok tablo demektir."""
            if len(blok) < 2:
                if blok:
                    atlanan.append({"satir": blok[0][0], "satir_n": len(blok),
                                    "neden": "tek satırlık `|` bloğu — tablo değil"})
                return
            ayrac_ix = [k for k, (_no, _l) in enumerate(blok) if _ayrac(_l)]
            if not ayrac_ix:
                # SESSİZ DÜŞÜRME YOK: atlanan her blok sayılır ve NEDENİ gövdede taşınır.
                atlanan.append({"satir": blok[0][0], "satir_n": len(blok),
                                "neden": "ayraç satırı (`|---|`) yok — markdown tablosu değil, "
                                         "boru karakterli düz metin"})
                return
            for j, ix in enumerate(ayrac_ix):
                if ix == 0:
                    atlanan.append({"satir": blok[0][0], "satir_n": 1,
                                    "neden": "ayraç ilk satır — üstünde başlık satırı yok"})
                    continue
                son = ayrac_ix[j + 1] - 1 if j + 1 < len(ayrac_ix) else len(blok)
                _tabloyu_kur(blok[ix - 1], [x for x in blok[ix + 1:son] if not _ayrac(x[1])])

        def _tabloyu_kur(baslik_satiri, govde):
            basliklar = _hucreler(baslik_satiri[1])
            # ŞEMA TABLOSU MU: başlık hücreleri §1 şemasının sütun adlarıysa rozet KENDİ
            # SÜTUNUNDADIR ve düzyazı sütunları rozet alanı DEĞİLDİR. Bu ayrımın gerekçesi
            # `_ROADMAP_SEMA_BASLIK`in üstündeki şerhte ölçümüyle yazılı (v337 iki kırmızısı).
            sema_tablosu = tuple(h.strip().lower() for h in basliklar) == \
                _ROADMAP_SEMA_TABLO_BASLIKLARI
            blok = [baslik_satiri]
            satirlar = []
            for no, l in govde:
                hucreler = _hucreler(l)
                if sema_tablosu and len(hucreler) == len(_ROADMAP_SEMA_TABLO_BASLIKLARI):
                    satirlar.append(_sema_satiri_kur(no, hucreler, kok_no))
                    continue
                hucre_durum, kanitlar, cizili = [], [], False
                for h in hucreler:
                    d, k, c = _roadmap_madde_durumu(h)
                    cizili = cizili or c
                    hucre_durum.append(d)
                    if d != "belirsiz":
                        kanitlar.append({"sutun": len(hucre_durum) - 1, "durum": d, "kanit": k})
                # TEK HÜKME İNDİRGEME YOK. Ölçüldü (2026-08-25, ROADMAP satır 290): bir §2 TAHTA
                # satırı `| ~~B1 …~~ **H6 ✅ KARAR+UYGULAMA** | WP11 | **BLOKE: operatör** |`
                # biçiminde HEM kapanış HEM blok rozeti taşıyor — ilk bulduğunu alan sürüm satırı
                # "kapalı" sayıyor ve `BLOKE` sayacı 0 kalıyordu. İkisi ÇELİŞMİYOR da: karar
                # verilmiş (kapalı) ama kapı operatörde (bloke). Çelişkiyi bir sezgiselle çözmek,
                # ölçülmemiş bir hükmü ölçülmüş gibi göstermek olurdu.
                ayrik = sorted({d for d in hucre_durum if d != "belirsiz"})
                if len(ayrik) == 1:
                    durum, durum_neden = ayrik[0], None
                elif not ayrik:
                    durum, durum_neden = "belirsiz", None
                else:
                    durum = None
                    durum_neden = ("satırda birden çok durum rozeti var (" + " + ".join(ayrik) +
                                   ") — tek hükme indirgenemedi; hücre başına `hucre_durum` ve "
                                   "`durum_kanitlari` okunur")
                tablo_durum["cok_isaretli" if durum is None else durum] += 1
                tablo_sayaci["satir"] += 1
                kirpildi = (not tam) and any(len(h) > _ROADMAP_HAM_TAVAN for h in hucreler)
                satirlar.append({
                    "satir": no,
                    "hucreler": [h if tam or len(h) <= _ROADMAP_HAM_TAVAN
                                 else h[:_ROADMAP_HAM_TAVAN] for h in hucreler],
                    "hucre_kirpildi": kirpildi,
                    "hucre_uzunluk": [len(h) for h in hucreler],
                    "hucre_durum": hucre_durum,
                    "durum": durum, "durum_neden": durum_neden,
                    "durum_kanitlari": kanitlar, "ustu_cizili": cizili,
                    # ŞEMASIZ TABLO: `sema` alanı VAR ve None'dır — alanı hiç yazmamak
                    # "şemasız" ile "bu sürüm şemayı hiç ölçmüyor"u aynı gösterirdi.
                    "sema": None})
            tablo_sayaci["tablo"] += 1
            tablolar.append({"satir": baslik_satiri[0], "basliklar": basliklar,
                             "satirlar": satirlar, "satir_n": len(satirlar)})

        for no, l in ham:
            if l is None:            # kesinti işareti: araya GERÇEK metin girdi
                _bitir(blok); blok = []
                continue
            blok.append((no, l))
        _bitir(blok)
        if atlanan:
            b["tablo_atlanan"] = atlanan
            tablo_sayaci["atlanan"] += len(atlanan)
        return tablolar

    def _kapat(b: dict, kok_no: str | None) -> None:
        yeni, ihlaller = [], []
        for m in b["maddeler"]:
            ham_liste = m.pop("_ham")
            # ŞEMA BAŞLIK SATIRINDAN OKUNUR, KATLANMIŞ GÖVDEDEN DEĞİL: `What:`/`Why:` satırları
            # maddeye katlanıyor ve onları alan gövdesine karıştırmak alan sayımını bozardı.
            sema, ihlal = _roadmap_madde_semasi(ham_liste[0], kok_no)
            ham = " ".join(ham_liste).strip()
            if ihlal:
                ihlaller.append({"satir": m["satir"], "bolum": kok_no, "neden": ihlal})
            if sema is None:
                durum, kanit, cizili = _roadmap_madde_durumu(ham)
            else:
                # ŞEMALI MADDE DÜZYAZIDAN ÖLÇÜLMEZ: durum beyan edildiği alandadır.
                durum, kanit = _roadmap_sema_durumu(sema)
                cizili = bool(_ROADMAP_CIZIK.search(ham))
            sayim_durum[durum] += 1
            kirpildi = (not tam) and len(ham) > _ROADMAP_HAM_TAVAN
            yeni.append({"satir": m["satir"], "girinti": m["girinti"],
                         "baslik": _roadmap_madde_basligi(ham) or None,
                         "ham": ham[:_ROADMAP_HAM_TAVAN] if kirpildi else ham,
                         "ham_kirpildi": kirpildi, "ham_uzunluk": len(ham),
                         "durum": durum, "durum_kanit": kanit, "ustu_cizili": cizili,
                         "sema": sema})
        b["maddeler"] = yeni
        b["madde_n"] = len(yeni)
        if ihlaller:
            # `tablo_atlanan` EMSALİ: şema biçiminde olup alanları tutmayan satır SESSİZCE
            # "tarihçe" sayılmaz — adıyla, satırıyla ve nedeniyle gövdede taşınır.
            b["sema_ihlal"] = ihlaller
        b["tablolar"] = _tablolari_kur(b, kok_no)
        b["tablo_satir_n"] = sum(t["satir_n"] for t in b["tablolar"])
        for alt in b["alt_bolumler"]:
            _kapat(alt, kok_no)
        b["madde_n_toplam"] = b["madde_n"] + sum(a["madde_n_toplam"] for a in b["alt_bolumler"])
        b["tablo_satir_n_toplam"] = b["tablo_satir_n"] + sum(
            a["tablo_satir_n_toplam"] for a in b["alt_bolumler"])

    for b in kok:
        _kapat(b, b.get("no"))

    # ALT BÖLÜM KENDİ ADRESİNİ TAŞIR: `### WP7 …` başlığı `§N` numarası taşımaz ve tüketici
    # "bu kalem hangi bölümde?" sorusunu ancak ağacı kendi gezerek cevaplayabilirdi. `ust_no`
    # o gezintiyi gövdeye taşır — yüzey ajanı satırı tek başına gösterebilsin.
    def _adresle(bs: list, ust_no, ust_baslik) -> None:
        for b in bs:
            b["ust_no"], b["ust_baslik"] = ust_no, ust_baslik
            _adresle(b["alt_bolumler"], ust_no if ust_no else b["no"], ust_baslik or b["baslik"])

    for b in kok:
        b["ust_no"], b["ust_baslik"] = None, None
        _adresle(b["alt_bolumler"], b["no"], b["baslik"])

    def _alt_say(bs: list) -> int:
        return sum(1 + _alt_say(b["alt_bolumler"]) for b in bs)

    # `wc -l` İLE AYNI SAYIYI VERSİN: `split("\n")` sondaki satır sonundan sonra BOŞ bir eleman
    # üretir ve "4623 satır" der — dosyada 4622 var. Bir satırlık fark küçüktür ama gövdedeki her
    # sayı dışarıdan doğrulanabilir olmalı; doğrulanamayan sayı güveni sessizce aşındırır.
    satir_n = len(satirlar) - (1 if satirlar and satirlar[-1] == "" else 0)
    return {"yol": yol, "bayt": bayt, "satir_n": satir_n, "mtime": mtime,
            "baslik": belge_basligi, "bolumler": kok,
            "sayim": {"bolum_n": len(kok), "alt_bolum_n": _alt_say(kok) - len(kok),
                      "madde_n": sum(b["madde_n_toplam"] for b in kok), "durum": sayim_durum,
                      "tablo_n": tablo_sayaci["tablo"], "tablo_satir_n": tablo_sayaci["satir"],
                      "tablo_atlanan_n": tablo_sayaci["atlanan"], "tablo_durum": tablo_durum,
                      # ŞEMA SAYACI AYRI KAPTA: `durum`/`tablo_durum` sözlükleri kendi
                      # birimlerinin TAMAMINI sayar (toplamları `madde_n`/`tablo_satir_n`e eşit
                      # olmak ZORUNDA — v287 çivisi) ve şema sayacı onların İÇİNE karışamaz.
                      "sema": _roadmap_sema_sayimi(kok),
                      "kapsam": "belgenin TAMAMI"},
            "ham_tavan": None if tam else _ROADMAP_HAM_TAVAN,
            # SÖZLEŞME GÖVDEDE TAŞINIR: tüketici `durum` alanının NE KADARINI ölçtüğünü satırın
            # kendisinden okumalı. Özellikle `belirsiz`: "işaretsiz" demektir, "açık" DEĞİL.
            "durum_kapsam": (f"durum işareti kalemin ilk {_ROADMAP_ISARET_ALANI} karakterinde "
                             "(rozet alanı) aranır; düzyazının ortasındaki işaret sayılmaz. "
                             "`belirsiz` = kalem işaret TAŞIMIYOR — 'açık' DEĞİL, ölçülmemiş. "
                             "Üstü çizili kapanış rozeti kapalı SAYILMAZ (`ustu_cizili` alanı). "
                             "Tablo satırlarında durum HÜCRE HÜCRE aranır ve sayımı AYRI tutulur "
                             "(`sayim.tablo_durum`) — §2 TAHTA bir tablodur, madde listesi değil; "
                             "iki sayımı toplamak kalemleri çift saymak olurdu. "
                             "ŞEMALI satırda (2026-09-01 göçü) durum DÜZYAZIDA ARANMAZ: "
                             "`sema.status` alanından okunur ve yalnız o sütun rozet alanıdır. "
                             "`atif` = satır durumunu BAŞKA satıra havale ediyor (`(bkz. …)`) — "
                             "belirsiz DEĞİL, ölçülmüş bir havale"),
            # ŞEMA SÖZLEŞMESİ — `sema` alanının ne olduğunu ve NEYİ ÖLÇMEDİĞİNİ tüketici
            # ezberden bilemez. Özellikle iki nokta: (1) `sema: null` bir kusur değil, operatör
            # onaylı MUAFİYETtir (§7 KARAR GÜNLÜĞÜ · §8 ARŞİV · tarihçe blokları — spec §3);
            # (2) tablo biçimi `born` TAŞIMAZ ve o None bir ölçüm kusuru değil, biçimin kendisi.
            "sema_kapsam": (
                "madde/tablo satırı `docs/TASARIM-ROADMAP-STANDART-2026-09-01.md` §1 şemasına "
                "uyuyorsa `sema` alanları taşır (id · name · status · status_detay · "
                "status_neden · sinif · born · owner · size · trigger · section · kaynak); "
                "uymuyorsa `sema` null'dır ve `sayim.sema.muaf_tarihce`de sayılır — bu bir "
                "İHLAL DEĞİL, operatör onaylı muafiyettir (§7/§8 tarihçe-koru). Şema BİÇİMİNDE "
                "olup alanları tutmayan satır AYRI sayılır (`sayim.sema.ihlal_n`, bölümde "
                "`sema_ihlal` listesi). `born` YALNIZ bullet biçiminde vardır; §6 kart endeksi "
                "ve §2 tablo satırları born taşımaz ve alan null kalır — uydurulmaz. "
                "`status` null ise `status_neden` DOLUdur.")}


def _roadmap_say(bolumler: list) -> dict:
    """Verilen bölüm ağacından sayımı YENİDEN hesaplar (süzgeç uygulandığında kullanılır).

    NİYE GEREKLİ: `?bolum=§2` isteğinde `madde_n`i süzgeçleyip `tablo_durum`u belge-geneli
    bırakmak, aynı `sayim` sözlüğünün yarısını bir kapsama yarısını başkasına bağlardı — okuyan
    hangi sayının neyi saydığını AYIRT EDEMEZDİ. Sayım tek kapsamlıdır ve kapsamını `kapsam`
    alanında söyler."""
    durum = {k: 0 for k in _ROADMAP_DURUM_KOVALARI}
    tdurum = {**{k: 0 for k in _ROADMAP_DURUM_KOVALARI}, "cok_isaretli": 0}
    sayac = {"madde": 0, "tablo": 0, "tsatir": 0, "atlanan": 0, "alt": 0}

    def _gez(bs: list, ust: bool) -> None:
        for b in bs:
            if not ust:
                sayac["alt"] += 1
            for m in b["maddeler"]:
                durum[m["durum"]] += 1
                sayac["madde"] += 1
            for t in b["tablolar"]:
                sayac["tablo"] += 1
                for r in t["satirlar"]:
                    tdurum["cok_isaretli" if r["durum"] is None else r["durum"]] += 1
                    sayac["tsatir"] += 1
            sayac["atlanan"] += len(b.get("tablo_atlanan") or [])
            _gez(b["alt_bolumler"], False)

    _gez(bolumler, True)
    return {"bolum_n": len(bolumler), "alt_bolum_n": sayac["alt"], "madde_n": sayac["madde"],
            "durum": durum, "tablo_n": sayac["tablo"], "tablo_satir_n": sayac["tsatir"],
            "tablo_atlanan_n": sayac["atlanan"], "tablo_durum": tdurum,
            # ŞEMA SAYACI DA SÜZGEÇLE DARALIR — belge-geneli bir şema sayısını süzgeçli gövdeye
            # koymak, `kapsam` alanının söylediğiyle çelişen bir sayı üretirdi. TEK fonksiyon
            # iki yerden çağrılır (`_roadmap_ayristir` + burası); ikinci bir gezinti yazmak
            # sessizce ayrışan iki sayaç demek olurdu.
            "sema": _roadmap_sema_sayimi(bolumler)}


def _roadmap_ozetle(bolumler: list) -> list:
    """Gövdeleri SÖKER, yapıyı ve durumu bırakır. Kopya üretir — önbellekteki ağaca DOKUNMAZ
    (yerinde budasaydık ikinci istek gövdesiz bir tahta görür ve `?ozet=0` sessizce yalan olurdu).

    NİYE VAR: tam gövde ÖLÇÜLDÜ — 383 KB (2026-08-25). Uygulamada gzip ara katmanı YOK, yani o
    383 KB telden ham geçiyor. Tahtayı çizmek için madde gövdesi gerekmez; başlık + durum yeter.
    Ayrıntı `?bolum=§N` ile tek bölüm olarak istenir."""
    def _b(b: dict) -> dict:
        return {**b,
                # `sema` ÖZETTE DE KALIR: sökülen şey madde GÖVDESİdir (383 KB'ın kaynağı),
                # şema ise gövdenin özeti-zaten-alınmış hâlidir — onu sökmek özeti tahtayı
                # çizemez hâle getirirdi (dinamik tahtanın tek girdisi bu alandır).
                "maddeler": [{"satir": m["satir"], "girinti": m["girinti"], "baslik": m["baslik"],
                              "durum": m["durum"], "durum_kanit": m["durum_kanit"],
                              "ustu_cizili": m["ustu_cizili"], "ham_uzunluk": m["ham_uzunluk"],
                              "sema": m["sema"]}
                             for m in b["maddeler"]],
                "tablolar": [{**t, "satirlar": [
                    {"satir": r["satir"], "etiket": (r["hucreler"][0] if r["hucreler"] else "")[:160],
                     "durum": r["durum"], "durum_neden": r["durum_neden"],
                     "hucre_durum": r["hucre_durum"], "ustu_cizili": r["ustu_cizili"],
                     "sema": r["sema"]}
                    for r in t["satirlar"]]} for t in b["tablolar"]],
                "alt_bolumler": [_b(a) for a in b["alt_bolumler"]]}
    return [_b(b) for b in bolumler]


@app.get("/api/roadmap")
def api_roadmap(request: Request, bolum: str | None = None, tam: int = 0, ozet: int = 0):
    """ROADMAP.md → tahta. SALT OKUNUR; yazma ucu YOKTUR (dosya insan tarafından düzenlenir).

    `?bolum=§3` tek bölüme daraltır · `?tam=1` madde gövdelerinin kırpılmasını kapatır
    (kırpılmışsa gövde bunu `ham_kirpildi` + `ham_uzunluk` ile SÖYLER — kırpılmış metni tam
    sanmak yalandır) · `?ozet=1` madde/hücre gövdelerini söker, yapı + başlık + durum bırakır
    (tam gövde ÖLÇÜLDÜ: 383 KB, uygulamada gzip ara katmanı yok).

    MADDE LİSTELERİ VE TABLOLAR AYRI SAYILIR. Bu dosyanın asıl tahtası (§2) bir TABLODUR; yalnız
    `- ` maddelerini ayrıştıran bir uç `bloke: 0` derdi — ölçmediğini "yok" diye bildirmek. İki
    sayaç ayrı tutulur (`sayim.durum` vs `sayim.tablo_durum`); toplamak kalemleri çift sayardı.

    DOSYA YOKSA 200 + `hata` + `yol` döner, 404 DEĞİL: 404'ün gövdesi FastAPI zarfıdır ve panonun
    `useApi` üç-hâl ayrımında yalnız "hata" olarak görünürdü — operatör HANGİ yolun okunamadığını
    göremezdi. Burada `bolumler: null`tır (boş liste DEĞİL: boş liste 'yol haritası boş' diye
    okunur, oysa ölçülen şey 'dosyayı bulamadım')."""
    _auth(request)
    p = _roadmap_yolu()
    try:
        st = p.stat()
        metin = p.read_text(encoding="utf-8")
    except OSError as e:
        return {"ok": False, "bolumler": None,
                "hata": f"ROADMAP dosyası okunamadı ({type(e).__name__}): {e}",
                "yol": str(p)}
    import datetime as _dt
    mtime = _dt.datetime.fromtimestamp(st.st_mtime, _dt.timezone.utc).isoformat(timespec="seconds")
    kok = Path(config.ROOT)
    gorunur = str(p.relative_to(kok)) if str(p).startswith(str(kok)) else str(p)
    ck = (str(p), st.st_mtime_ns, st.st_size, bool(tam))
    yuk = _ROADMAP_CACHE.get(ck)
    if yuk is None:
        # ÖNBELLEK ANAHTARI mtime_ns + boyut TAŞIR: dosya değişince anahtar da değişir, yani bayat
        # bir tahta servis edilemez. 562 KB'lık ayrıştırma her istekte tekrarlanmasın diye var.
        yuk = _roadmap_ayristir(metin, yol=gorunur, bayt=st.st_size, mtime=mtime, tam=bool(tam))
        _ROADMAP_CACHE.clear()
        _ROADMAP_CACHE[ck] = yuk
    bolumler = yuk["bolumler"]
    if bolum:
        ara = bolum.strip()
        secili = [b for b in bolumler
                  if (b.get("no") or "") == ara or b["ham_baslik"].startswith(ara)]
        yuk = {**yuk, "bolumler": secili,
               "sayim": {**_roadmap_say(secili), "kapsam": f"YALNIZ süzgeçlenen bölüm(ler): {ara}"}}
    if ozet:
        yuk = {**yuk, "bolumler": _roadmap_ozetle(yuk["bolumler"]),
               "ozet_beyani": ("madde `ham` gövdeleri ve tablo hücreleri SÖKÜLDÜ; başlık, durum ve "
                               "yapı duruyor. Gövde için `?ozet=0` (varsayılan) ya da `?bolum=§N`")}
    yuk = {**yuk, "ok": True,
           "suzgec": {"bolum": bolum, "tam": bool(tam), "ozet": bool(ozet),
                      "eslesen_bolum_n": len(yuk["bolumler"]), "toplam_bolum_n": len(bolumler)}}
    return yuk


# ---- KARAR / HÜKÜM ARŞİVİ -------------------------------------------
# Zincir "tur → hüküm → belge" son halkasızdı: `docs/` altında 14 karar/hüküm belgesi duruyor
# (ölçüldü 2026-08-25) ve HİÇBİRİNİ listeleyen uç yoktu — pano belge rafı bu satırı "uç yok"
# rozetiyle, dürüstçe boş gösteriyordu. Buradaki uç o rafı DOLDURUR.
#
# NE SUNULUR, NE SUNULMAZ: bugün YALNIZ künye (ad · tarih · başlık · bayt). Belge GÖVDESİ
# sunulmaz ve bu bir eksiklik değil bir SIRA: gövde ucu bir "hangi belge?" parametresi demektir,
# o parametre de kullanıcıdan gelen bir dizeyi dosya sistemine yaklaştıran ilk adımdır. Kapı o
# adımda BİLEREK yeniden açılacak (`test_belge_rafi_v312::test_uc_kullanicidan_YOL_almiyor`
# ötecek), sessizce değil.
#
# YETKİ: `_auth` ZORUNLU. Arşiv tur hükümlerini, kök nedenleri ve açık kalemleri taşır —
# `/runbook` ile aynı sınıf: sistemin iç haritası, genel anlatım yüzeyi değil.
_KARAR_BELGE_ADI = re.compile(r"^(?:KARAR|HUKUM)-[\w.-]+\.md$")
_KARAR_TARIHI = re.compile(r"(\d{4}-\d{2}-\d{2})")
# Başlık için belgenin TAMAMI okunmaz: en büyük arşiv belgesi 60 KB'ı aşıyor ve raf 14 satır
# çiziyor. İlk `# ` başlığı bu depoda HER ZAMAN belgenin ilk satırlarındadır; bulunamazsa
# uydurulmaz, "ölçülemedi + neden" yazılır.
_KARAR_BASLIK_TARAMA = 4096  # karakter (bayt değil: dosya utf-8 metin olarak açılır)


def _karar_belgeleri_dizini() -> Path:
    """Arşivin kaynağı — depo kökündeki `docs/`. Ad TAHMİN EDİLMEDİ, diskte ölçüldü
    (2026-08-25: 14 dosya, `KARAR-*.md` 11 + `HUKUM-*.md` 3)."""
    return Path(config.ROOT) / "docs"


def _karar_belge_kaydi(p: Path, dizin_cozulmus: Path) -> dict:
    """Bir arşiv belgesinin ÖLÇÜLEN künyesi: {ad, tarih, baslik, bayt, neden}.

    ÖLÇÜLEMEYEN ALAN None KALIR ve `neden` onu ADIYLA açıklar (UYDURMA YASAĞI). İki kolay yalan
    burada kapalı: tarihi okunamayan belgeye bugünün tarihini yazmak, ve başlığı okunamayan
    belgeye dosya adını başlık diye koymak. Üçüncüsü daha sinsiydi — okunamayan belgeyi listeden
    DÜŞÜRMEK: raf 13 belge gösterir, 14.'sü hakkında hiçbir şey söylenmez ve kimse aramaz.
    Kayıt her hâlde listede kalır (YASA 4: sessiz atlama yok).

    YOL GEÇİŞİ KAPISI: dosya `resolve()` sonrası hâlâ arşiv dizininin İÇİNDE değilse (arşiv adı
    taşıyan bir sembolik bağ dışarıyı gösteriyorsa) AÇILMAZ — ne boyutu ne başlığı okunur, yani
    dizin dışındaki içerik telden geçemez. Ret de sessiz değildir: kayıt `neden` ile durur."""
    nedenler: list[str] = []
    ad = p.name

    m = _KARAR_TARIHI.search(ad)
    tarih = m.group(1) if m else None
    if tarih is None:
        nedenler.append("tarih ölçülemedi: dosya adında YYYY-AA-GG deseni yok")

    try:
        icerde = p.resolve().parent == dizin_cozulmus
        yol_hatasi = None
    except OSError as e:
        icerde, yol_hatasi = False, f"{type(e).__name__}: {e}"
    if not icerde:
        nedenler.append("başlık ve boyut ölçülemedi: dosya arşiv dizininin DIŞINI gösteriyor "
                        f"(sembolik bağ ya da çözülemeyen yol{'; ' + yol_hatasi if yol_hatasi else ''})"
                        " — açılmadı")
        return {"ad": ad, "tarih": tarih, "baslik": None, "bayt": None,
                "neden": "; ".join(nedenler)}

    try:
        bayt: int | None = p.stat().st_size
    except OSError as e:
        bayt = None
        nedenler.append(f"boyut ölçülemedi: stat başarısız ({type(e).__name__}: {e})")

    baslik: str | None = None
    try:
        with p.open("r", encoding="utf-8") as f:
            bas = f.read(_KARAR_BASLIK_TARAMA)
    except (OSError, UnicodeDecodeError) as e:
        nedenler.append(f"başlık ölçülemedi: belge okunamadı ({type(e).__name__}: {e})")
    else:
        for satir in bas.splitlines():
            if satir.startswith("# "):
                baslik = satir[2:].strip()
                break
        if baslik is None:
            nedenler.append(f"başlık ölçülemedi: ilk {_KARAR_BASLIK_TARAMA} karakterde "
                            "`# ` ile başlayan satır yok")

    return {"ad": ad, "tarih": tarih, "baslik": baslik, "bayt": bayt,
            "neden": "; ".join(nedenler) if nedenler else None}


@app.get("/api/karar-belgeleri")
def api_karar_belgeleri(request: Request):
    """`docs/KARAR-*.md` + `docs/HUKUM-*.md` arşivinin KÜNYE listesi. SALT OKUNUR; yazma ucu
    YOKTUR (belgeler tur kapanışında insan eliyle yazılır).

    Dönen alanlar: `ok` · `dizin` · `hata` · `belgeler[]` = {ad, tarih, baslik, bayt, neden}.
    Sıra EN YENİ ÖNCE (dosya adındaki tarihe göre); tarihi ölçülemeyen belge sona düşer — sona
    düşmek listeden düşmek değildir.

    ARŞİVİN TANIMI DESENDİR, dizin listesi değil: yalnız `KARAR-`/`HUKUM-` ile başlayan `.md`
    DOSYALARI. Komşu dosyalar (notlar, sır dosyaları) ve aynı adı taşıyan dizinler rafa giremez;
    kullanıcıdan gelen HİÇBİR dize bu seçime karışmaz (uç `request` dışında parametre almaz).

    DİZİN OKUNAMIYORSA 200 + `hata` döner, 404 DEĞİL: 404'ün gövdesi FastAPI zarfıdır ve panonun
    üç-hâl ayrımında yalnız "hata" olarak görünürdü — operatör HANGİ dizinin okunamadığını
    göremezdi. `belgeler` o hâlde null'dır (boş liste DEĞİL: boş liste "arşiv boş" diye okunur,
    oysa ölçülen şey "dizini açamadım")."""
    _auth(request)
    d = _karar_belgeleri_dizini()
    kok = Path(config.ROOT)
    gorunur = str(d.relative_to(kok)) if str(d).startswith(str(kok)) else str(d)
    try:
        girdiler = sorted(d.iterdir())
        dizin_cozulmus = d.resolve()
    except OSError as e:
        return {"ok": False, "dizin": gorunur, "belgeler": None,
                "hata": f"arşiv dizini okunamadı ({type(e).__name__}): {e}"}

    kayitlar = [_karar_belge_kaydi(p, dizin_cozulmus) for p in girdiler
                if _KARAR_BELGE_ADI.match(p.name) and p.is_file()]
    tarihli = sorted((k for k in kayitlar if k["tarih"]),
                     key=lambda k: (k["tarih"], k["ad"]), reverse=True)
    tarihsiz = sorted((k for k in kayitlar if not k["tarih"]), key=lambda k: k["ad"])
    # `hata` BAŞARIDA DA VAR ve None: şekil TAM tutulur, yoksa okuyucu `.get("hata")` ile
    # "hata yok" ile "alan yok"u ayırt edemez — bu depodaki baskın hata deseni.
    return {"ok": True, "dizin": gorunur, "belgeler": tarihli + tarihsiz, "hata": None}


# ---- AJAN YÜZEYİ: üç bot + ana beyin, SALT OKUNUR --------------------
# Operatörün bugün üç botun (`sef` · `bekci` · `karne`) ve ana hermes beyninin ne konuştuğunu
# görmesinin TEK yolu A1'e ssh'layıp `state.db`leri elle açmaktı. Bu uç o kaynakları tek yüzeye
# taşır. YAZMA UCU YOKTUR ve olmayacaktır: sohbet ayrı bir dalganın (B) işi.
#
# ÜÇ KAYNAK, ÜÇ AYRI HÜKÜM — ve bu ayrım ucun tüm anlamıdır:
#   1. profil defterleri  `~/.hermes/profiles/<ad>/state.db`  (bot başına)
#   2. ana beyin defteri  `~/.hermes/state.db`                (şema ÖLÇÜLDÜ 2026-08-31: aynı)
#   3. teslim olayları    `state/events.jsonl` → `<ad>_brifingi_teslim`
# Bir kaynağın okunamaması ÖTEKİLERİ düşürmez; her biri kendi `durum`/`neden`ini taşır.
#
# "BOŞ LİSTE" İLE "ÖLÇÜLEMEDİ" AYNI ŞEY DEĞİLDİR ve bu ucun en kolay bozulma yolu ikisini
# birleştirmektir. `oturumlar: []` "bu ajanla hiç konuşulmamış" DER — bir iddiadır. `oturumlar:
# null` + `neden` ise "defteri okuyamadım" der. Defteri okuyamadığımızda ilkini yazmak, operatöre
# sessiz bir yalan söylemektir; `tests/test_ajan_yuzeyi_api_v347.py` bu çevirmeyi çivilemiştir.
#
# SALT-OKUMA BİR KOLAYLIK DEĞİL ŞARTTIR: bu defterlere CANLI hermes yazar. Pano bir okuma
# isteğiyle onların üzerine kilit koyamaz, `-wal`/`-journal` doğuramaz, tek bayt değiştiremez.
# Mekanizma `file:…?mode=ro` URI'sidir; çivi dizgeyi DE davranışı DA ölçer (bağlantıya gerçekten
# yazma denenir), çünkü `mode=ro` bir yorumda da geçebilir ve dize çivisi tek başına kandırılır.

#: Mesaj gövdesi tavanı (karakter). Brifing mesajları on binlerce karakter olabilir; pano zaman
#: çizelgesi onları ham taşıyamaz. Kaba üst sınır: 600 × `AJAN_MESAJ_N` × `AJAN_OTURUM_TAVANI` ×
#: ajan sayısı. Kırpma SESSİZ DEĞİLDİR — her mesaj `kirpildi` + `ham_uzunluk` taşır, yani kırpılmış
#: bir metni tam sanmak imkânsızdır (`/api/roadmap`in `ham_kirpildi` emsali).
AJAN_MESAJ_TAVANI = 600
#: Oturum başına dönen mesaj sayısı — defterin KUYRUĞUNDAN (operatör son konuşulanı arar).
AJAN_MESAJ_N = 20
#: Varsayılan oturum sayısı. "Hafif varsayılan" bir tasarım kararıdır: pano bu ucu her açılışta
#: çağırır ve varsayılanın maliyeti her operatör bakışında ödenir.
AJAN_OTURUM_N = 5
#: `?limit=` TAVANI. Tavansız bir sayaç bir kaynak tüketim yüzeyidir; kırpma UYGULANDIĞINDA
#: `suzgec.limit_istenen` ile SÖYLENİR — sessiz kırpma, isteyene "500 oturum aldım" sandırırdı.
AJAN_OTURUM_TAVANI = 50
#: Teslim olayı kuyruğu (bayt) ve ajan başına tutulan olay sayısı. `events.jsonl` canlıda ~9 MB
#: (ölçüldü 2026-08-07) ve tamamını ayrıştırmak her istekte ödenen bir bedel olurdu; ~120 KB/gün
#: ölçümüyle 512 KB ≈ son 4 gün. Emsal ve gerekçe: `_SON_DONGU_KUYRUK`.
#: TAVAN SESSİZ DEĞİLDİR: kesildiğinde `teslim_kirpildi` + `teslim_toplam` bunu SÖYLER (mesaj
#: gövdesindeki `kirpildi`/`ham_uzunluk` ile aynı disiplin). Sessiz kesme, operatöre "bu ajanın
#: tüm teslim tarihçesi bu" sandırırdı.
_AJAN_TESLIM_KUYRUK = 512_000
_AJAN_TESLIM_N = 25
#: Çevrilemeyen bir damganın KORUNAN ham değerinin tavanı. Ham'ı hiç taşımamak, ölçülemeyen
#: damganın NE olduğunu da yok ederdi; tavansız taşımak bozuk bir defterden telden geçen
#: sınırsız bir gövde açardı.
_AJAN_TS_HAM_TAVANI = 120
#: Defter meşgulse süresiz beklemek uç ipliğini asardı; zaman aşımı `olculemedi`ye düşer.
_AJAN_DB_TIMEOUT_S = 2.0
#: Teslim olayının adı AJAN ADINDAN TÜRER (`sef_brifingi_teslim` → `sef`). Elle yazılmış bir
#: olay→ajan haritası TEK-KAYNAK YASASINI çiğnerdi: dördüncü bot doğduğu gün harita sessizce
#: eksik kalır ve o botun teslimleri hiçbir yerde görünmezdi.
_AJAN_TESLIM_SONEKI = "_brifingi_teslim"
#: Ana beynin ADI. Kimlik (`ad`, `tur`) ÇİFTİDİR: bir profil bu adı taşısaydı iki kayıt aynı adı
#: paylaşır ama `tur` (`bot` vs `ana`) onları ayırırdı.
_AJAN_ANA_ADI = "hermes"
#: OKUNAN ŞEMANIN SÖZLEŞMESİ — canlı `~/.hermes/state.db`den ölçüldü (2026-08-31, `sqlite_master`).
#: Yalnız GERÇEKTEN okunan sütunlar: fazlasını istemek, uca hiç dokunmayan bir şema değişikliğinde
#: sağlam bir kaynağı `olculemedi` ilan ederdi. Eksik olan `neden`de ADIYLA geçer — "şema farklı"
#: demek, bir sonraki teşhisi hiçbir yere götürmez.
_AJAN_ZORUNLU_SEMA: dict[str, tuple[str, ...]] = {
    "sessions": ("id", "model", "started_at"),
    "messages": ("id", "session_id", "role", "content", "timestamp"),
}


def _ajan_profil_koku() -> Path:
    """Bot profillerinin ÇALIŞMA kökü. Fonksiyon (modül sabiti değil) ki testler gerçek
    `~/.hermes`e dokunmadan sentetik bir kök enjekte edebilsin."""
    return Path.home() / ".hermes" / "profiles"


def _ajan_ana_beyin_db() -> Path:
    """Ana hermes beyninin defteri — profil botlarından AYRI bir muhatap."""
    return Path.home() / ".hermes" / "state.db"


def _ajan_bot_koku() -> Path:
    """ROSTER'IN TEK KAYNAĞI: dağıtılan profil dizinleri. Bot listesi elle YAZILMAZ, buradan
    TÜRER — ikinci bir liste (kod içinde bir demet) canlıyla sessizce ayrışırdı."""
    return Path(config.ROOT) / "deploy" / "hermes" / "profiles"


def _ajan_botlari() -> tuple[list[str] | None, str | None]:
    """`(botlar, neden)`. Dizin okunamazsa `None` döner — BOŞ LİSTE DEĞİL: boş liste "hiç bot yok"
    der, oysa ölçülen şey "kaç bot olduğunu bilmiyorum"dur."""
    kok = _ajan_bot_koku()
    try:
        return sorted(p.name for p in kok.iterdir() if p.is_dir()), None
    except OSError as e:
        return None, (f"bot roster'ı ÖLÇÜLEMEDİ ({type(e).__name__}: {e}); yol: {kok}. "
                      "Liste 'bot yok' DEĞİL, 'listeyi okuyamadım' demektir.")


def _ajan_ts(ham) -> str | None:
    """sqlite REAL (unix epoch) → ISO-8601 UTC metin. Çevrilemezse `None` (UYDURMA YASAĞI:
    okunamayan bir damgayı 1970'e sabitlemek, ölçülmemiş bir tarih yazmaktır)."""
    import datetime as _dt
    try:
        return _dt.datetime.fromtimestamp(float(ham), _dt.timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError, OverflowError):
        # sessiz-yutma: damga yok/biçimsiz/menzil dışı — alan None KALIR ve okuyan "ts ölçülemedi"
        # görür; istisnayı yukarı taşımak tek bozuk satır için TÜM ajanı ölçülemez yapardı
        return None


def _ajan_damga(ham) -> dict:
    """`{ts, ts_ham}` — çevrilebildiyse ISO, çevrilemediyse `ts: None` ve HAM DEĞER KORUNUR.

    PLAN SÖZLEŞMESİ (T1'DEN MİRAS, 2026-08-31): "`oturum.ts`/`mesaj.ts` = damga çevrilemedi
    (ham korunur)". Ham'ı düşürmek ölçülemezliği İKİ KAT yapardı: operatör hem damgayı göremez
    hem defterde NE yazdığını asla öğrenemezdi — `_ajan_ts`in işaretli sessiz-yutması ancak bu
    alan sayesinde GÖZLENEBİLİR (çivi: `test_bozuk_damga_HAM_korunur_ve_ajan_ok_kalir`).

    Şekil TAM tutulur: `ts_ham` başarıda da VARDIR ve `None`dır — yoksa okuyan `.get("ts_ham")`
    ile "ham yok" ile "alan yok"u ayırt edemezdi (bu depodaki baskın hata deseni)."""
    iso = _ajan_ts(ham)
    if iso is not None or ham is None:
        return {"ts": iso, "ts_ham": None}
    return {"ts": None, "ts_ham": str(ham)[:_AJAN_TS_HAM_TAVANI]}


def _ajan_mesaj_govdesi(ham) -> dict:
    """`{metin, kirpildi, ham_uzunluk}` — kırpma HER ZAMAN kendini beyan eder."""
    s = "" if ham is None else str(ham)
    return {"metin": s[:AJAN_MESAJ_TAVANI], "kirpildi": len(s) > AJAN_MESAJ_TAVANI,
            "ham_uzunluk": len(s)}


def _ajan_sema_eksigi(conn) -> str | None:
    """Şema sözleşmesi tutuyor mu? Tutmuyorsa EKSİK OLANIN ADI, tutuyorsa `None`.

    Kontrol `SELECT` denemesinden ÖNCE yapılır ve bu bilinçlidir: eksik sütun çalışma anında bir
    `OperationalError` olurdu ve o istisnanın metni ("no such column: content") bir `except`in
    içinde, hükümle karışmış hâlde gelirdi. Burada eksik ALAN ADIYLA, hükümden önce ölçülür."""
    eksik: list[str] = []
    for tablo, sutunlar in _AJAN_ZORUNLU_SEMA.items():
        # Tablo adı MODÜL SABİTİDİR, kullanıcı girdisi değil — `PRAGMA` parametre bağlamayı
        # desteklemediği için bu ayrım şart: uca gelen hiçbir dize buraya ulaşamaz.
        var = {satir[1] for satir in conn.execute(f"PRAGMA table_info({tablo})")}
        if not var:
            eksik.append(f"`{tablo}` tablosu YOK")
            continue
        if yok := [s for s in sutunlar if s not in var]:
            eksik.append(f"`{tablo}` tablosunda eksik sütun: {', '.join(yok)}")
    return "; ".join(eksik) or None


def _ajan_oturumlar(db: Path, oturum_n: int) -> tuple[list | None, str | None]:
    """Bir defterden son `oturum_n` oturum + her birinin son `AJAN_MESAJ_N` mesajı.

    `(oturumlar, neden)` döner ve İKİSİ BİRDEN DOLU OLMAZ: ölçülebildiyse liste (boş olabilir —
    o zaman "hiç oturum yok" DOĞRU cevaptır), ölçülemediyse `None` + neden.

    BAĞLANTI SALT-OKUNUR (`mode=ro`): bu dosyaya canlı hermes yazar."""
    import sqlite3
    if not db.exists():
        return None, (f"oturum defteri ÖLÇÜLEMEDİ: dosya yok — {db}. Bu, 'bu ajanla iletişim yok' "
                      "DEĞİLDİR; defterin kendisi bulunamadı (profil hiç koşmamış ya da yol farklı).")
    conn = None
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=_AJAN_DB_TIMEOUT_S)
        if eksik := _ajan_sema_eksigi(conn):
            return None, (f"oturum defterinin ŞEMASI tanınmadı ({db}): {eksik}. Boş liste "
                          "döndürmek 'hiç konuşulmamış' derdi; ölçülen şey şemanın farklılığıdır.")
        oturumlar = []
        for oid, model, ts in conn.execute(
                "SELECT id, model, started_at FROM sessions "
                "ORDER BY started_at DESC, id DESC LIMIT ?", (oturum_n,)).fetchall():
            # KUYRUKTAN alınır (DESC + LIMIT) ve sunuma KRONOLOJİK çevrilir: operatör son
            # konuşulanı arar ama bir konuşmayı tersten okumaz.
            satirlar = conn.execute(
                "SELECT role, timestamp, content FROM messages WHERE session_id = ? "
                "ORDER BY timestamp DESC, id DESC LIMIT ?", (oid, AJAN_MESAJ_N)).fetchall()
            oturumlar.append({
                "id": oid, **_ajan_damga(ts), "model": model,
                "mesajlar": [{"rol": rol, **_ajan_damga(mts), **_ajan_mesaj_govdesi(icerik)}
                             for rol, mts, icerik in reversed(satirlar)]})
        return oturumlar, None
    except (sqlite3.Error, OSError, ValueError) as e:
        # İSTİSNA YUTULMAZ, HÜKME ÇEVRİLİR: türü ve metni `neden`e taşınır (YASA 4'ün sinyal
        # şartı: `e` gövdede kullanılıyor). Türü yazmak bir sonraki teşhisi "dosya mı bozuk,
        # izin mi yok, kilit mi var" sorusundan kurtarır.
        return None, f"oturum defteri ÖLÇÜLEMEDİ ({type(e).__name__}: {e}); yol: {db}"
    finally:
        if conn is not None:
            conn.close()


def _ajan_teslimleri() -> tuple[dict[str, list] | None, str | None]:
    """`state/events.jsonl` kuyruğundan `<ad>_brifingi_teslim` olayları, ajan adına kovalanmış.

    Defter okunamazsa `None` — boş sözlük "hiç teslim yapılmadı" derdi.

    SIRA EN YENİ ÖNCE (plan sözleşmesi: `teslimler` YENİDEN→ESKİYE). Defter kronolojik yazılır,
    yani ters çevirme ŞARTTIR: `reversed` düşerse uç dolu ama EN ESKİ listeyi döndürür — operatör
    hiçbir boşluk görmeden yanlış uçtan bakar. Çivi: `test_teslimler_YENIDEN_ESKIYE_siralaniyor`.

    TAVAN BURADA UYGULANMAZ, çağıran uygular ve BEYAN EDER: bu fonksiyon kuyrukta GÖRDÜĞÜNÜN
    tamamını döndürür ki `teslim_toplam` gerçek sayıyı söyleyebilsin. Kesmeyi ölçümün içine
    gömmek, kesildiğini söyleyecek sayıyı da yok ederdi.

    BEDEL BEYANI (inceleme K-5, 2026-08-31): projeksiyon dört alanlık BEYAZ LİSTEYDİ ve
    `ops/sef_brifingi.py::main`in bastığı `olculemeyen` alanını — "hangi kaynaklar ölçülemedi"
    listesini — sessizce düşürüyordu. Ölçülemezliği gösteren bir alanın, ölçülemezliği göstermek
    için yazılmış bir uçta düşmesi Bedel yasasının tam konusuydu; alan artık TAŞINIYOR (olayda
    yoksa `None`). HÂLÂ DÜŞENLER, adlarıyla: `siralama`/`sunum` (üretici içi sıralama kaynağı) ·
    `bastirilan` (bekci) · `giren`/`gecis`/`bicimsiz` (karne). Bunlar bilinçli dışarıda: pano
    zaman çizelgesi teslimin KİMLİĞİNİ ve KAPSAMINI çizer, üreticinin iç muhasebesini değil."""
    p = Path(config.STATE) / "events.jsonl"
    try:
        boyut = p.stat().st_size
        with open(p, "rb") as f:
            if boyut > _AJAN_TESLIM_KUYRUK:
                f.seek(boyut - _AJAN_TESLIM_KUYRUK)
                f.readline()          # kuyruğun başındaki YARIM satır atılır
            satirlar = f.read().decode("utf-8", "replace").splitlines()
    except OSError as e:
        return None, (f"teslim olayları ÖLÇÜLEMEDİ ({type(e).__name__}: {e}); yol: {p}. "
                      "Boş liste 'hiç brifing teslim edilmedi' derdi — ölçülen şey bu değil.")
    kova: dict[str, list] = {}
    for satir in satirlar:
        if _AJAN_TESLIM_SONEKI not in satir:
            continue
        try:
            ev = json.loads(satir)
        except ValueError:
            # sessiz-yutma: kırpılmış/bozuk TEK satır — tarama sonraki satırla sürer; bozuk bir
            # satır yüzünden tüm teslim tarihçesini "ölçülemedi" ilan etmek orantısız olurdu
            continue
        ad_olay = ev.get("event") if isinstance(ev, dict) else None
        if not isinstance(ad_olay, str) or not ad_olay.endswith(_AJAN_TESLIM_SONEKI):
            continue
        kova.setdefault(ad_olay[: -len(_AJAN_TESLIM_SONEKI)], []).append(
            {"ts": ev.get("ts"), "event": ad_olay, "damgalanan": ev.get("damgalanan"),
             "detail": ev.get("detail"), "olculemeyen": ev.get("olculemeyen")})
    return {ad: list(reversed(v)) for ad, v in kova.items()}, None


@app.get("/api/ajanlar")
def api_ajanlar(request: Request, limit: int = AJAN_OTURUM_N, ajan: str | None = None):
    """Üç bot + ana hermes beyni: son oturumlar, mesajlar, model rozetleri ve teslim damgaları.
    SALT OKUNUR; yazma/sohbet ucu YOKTUR (dalga-B).

    `?limit=` oturum sayısı (tavan `AJAN_OTURUM_TAVANI`; kırpılırsa `suzgec.limit_istenen` söyler)
    · `?ajan=` TÜRETİLMİŞ roster üzerinde bir ÜYELİK SÜZGECİDİR — dosya sistemine ham geçmez ve
    eşleşmeyen bir dize hiçbir defter AÇTIRMAZ (çivi: `test_ajan_parametresi_SUZGECTIR_yol_degil`).

    ÜÇ HÜKÜM ÜÇ YERDE, ve karıştırılmazlar:
      · `ok`/`hata` — LİSTENİN kendisi hakkında: roster ve olay defteri okunabildi mi. Bir ajanın
        defterinin okunamaması `ok`u DÜŞÜRMEZ; o, o ajanın kendi hükmüdür.
      · ajan başına `durum`/`neden` — YALNIZ oturum kaynağı hakkında. `teslimler` AYRI bir
        kaynaktan gelir ve `durum: olculemedi` olan bir ajanda bile ölçülmüş olabilir.
      · `kaynak.botlar` — `null` ise roster ölçülemedi (boş liste "bot yok" derdi).

    Ölçülemeyen her yerde `null` + `neden` durur, boş liste DEĞİL: boş liste 'iletişim yok' diye
    okunur ve bu AYRI BİR İDDİADIR. `eslesmeyen_teslimler` aynı disiplinin üçüncü ayağıdır: hiçbir
    profile karşılık gelmeyen bir teslim olayı (`oneri_brifingi_teslim` gibi) sessizce DÜŞMEZ —
    ama SONEK DIŞI teslimler (`alarm_backlog_digest_teslim`, `ops/olcum.py`) bu sözleşmenin
    KAPSAMI DIŞINDADIR ve buraya hiç girmez; "hiçbir teslim düşmez" cümlesi o kümede geçersizdir.

    SIRA SÖZLEŞMESİ (plan: T1'DEN MİRAS, T2 bunu DEĞİŞTİRMEZ) — üçü de çivili:
      · `oturumlar` YENİDEN→ESKİYE · `mesajlar` ESKİDEN→YENİYE (okuma akışı) ·
        `teslimler` YENİDEN→ESKİYE.

    SKALER `null` ANLAMLARI (liste `null`larından AYRI, ve birbirinden de ayrı):
      · `model` — en yeni oturumun modeli kayıtlı değil ya da hiç oturum yok; `durum` ayırt eder.
      · `son_oturum_ts` — hiç oturum görülmedi (ya da damgası çevrilemedi: `oturumlar[0].ts_ham`).
      · `oturum.ts` / `mesaj.ts` — damga ÇEVRİLEMEDİ; ham değer `ts_ham`ta KORUNUR.
      · `teslim.damgalanan` / `detail` / `olculemeyen` — üretici o alanı olaya hiç basmadı.

    KIRPMALAR KENDİLERİNİ SÖYLER, üçü de: mesaj gövdesi (`kirpildi`+`ham_uzunluk`) · oturum
    sayısı (`suzgec.limit_istenen`) · teslim listesi (`teslim_kirpildi`+`teslim_toplam`,
    tavan `kaynak.teslim_tavani`; eşleşmeyenlerde `kaynak.eslesmeyen_toplam`)."""
    _auth(request)
    n = max(1, min(limit, AJAN_OTURUM_TAVANI))
    botlar, roster_neden = _ajan_botlari()
    profil_koku = _ajan_profil_koku()
    ana_db = _ajan_ana_beyin_db()

    # PLAN ÖNCE KURULUR, SÜZGEÇ SONRA UYGULANIR, DEFTERLER EN SON AÇILIR. Sıra bir kapıdır:
    # süzgeç defter açılmadan ÖNCE işlediği için `?ajan=` ile gelen bir dize hiçbir dosya yoluna
    # dönüşemez — yalnız zaten türetilmiş adlarla karşılaştırılır.
    plan = [{"ad": b, "tur": "bot", "db": profil_koku / b / "state.db"} for b in (botlar or [])]
    plan.append({"ad": _AJAN_ANA_ADI, "tur": "ana", "db": ana_db})
    secili = [k for k in plan if k["ad"] == ajan] if ajan else plan

    teslimler, events_neden = _ajan_teslimleri()
    ajanlar = []
    for k in secili:
        oturumlar, neden = _ajan_oturumlar(k["db"], n)
        # TAVAN BURADA KESER ve KESTİĞİNİ SÖYLER. `ham_teslim` kuyrukta görülenin tamamı;
        # `teslim_toplam` o gerçek sayıyı taşır, `teslim_kirpildi` kesmenin OLUP OLMADIĞINI.
        # Sessiz `[:25]`, operatöre "bu ajanın tüm teslim tarihçesi bu" sandırırdı.
        ham_teslim = None if teslimler is None else teslimler.get(k["ad"], [])
        ajanlar.append({
            "ad": k["ad"], "tur": k["tur"],
            "model": oturumlar[0]["model"] if oturumlar else None,
            "son_oturum_ts": oturumlar[0]["ts"] if oturumlar else None,
            "oturumlar": oturumlar,
            "teslimler": None if ham_teslim is None else ham_teslim[:_AJAN_TESLIM_N],
            "teslim_toplam": None if ham_teslim is None else len(ham_teslim),
            "teslim_kirpildi": None if ham_teslim is None else len(ham_teslim) > _AJAN_TESLIM_N,
            "durum": "ok" if neden is None else "olculemedi",
            "neden": neden,
        })

    # EŞLEŞMEYEN TESLİMLER TAM ROSTER'A GÖRE ÖLÇÜLÜR, süzgeçlenmiş listeye göre değil: `?ajan=sef`
    # ile bakan operatöre bekci'nin teslimlerini "sahipsiz" diye göstermek uydurma olurdu. Roster
    # ölçülemediyse hüküm de verilemez (`None`) — kimin sahipsiz olduğu ancak tam liste bilinirken
    # söylenebilir.
    if teslimler is None or botlar is None:
        eslesmeyen, eslesmeyen_toplam = None, None
    else:
        bilinen = set(botlar) | {_AJAN_ANA_ADI}
        ham_eslesmeyen = [t for ad, olaylar in sorted(teslimler.items()) if ad not in bilinen
                          for t in olaylar]
        eslesmeyen_toplam = len(ham_eslesmeyen)
        eslesmeyen = ham_eslesmeyen[:_AJAN_TESLIM_N]

    nedenler = [x for x in (roster_neden, events_neden) if x]
    return {
        "ok": not nedenler,
        "hata": "; ".join(nedenler) if nedenler else None,
        "ajanlar": ajanlar,
        "eslesmeyen_teslimler": eslesmeyen,
        "kaynak": {"profil_koku": str(profil_koku), "ana_beyin": str(ana_db),
                   "bot_koku": str(_ajan_bot_koku()), "botlar": botlar,
                   "events": str(Path(config.STATE) / "events.jsonl"),
                   "events_neden": events_neden, "teslim_tavani": _AJAN_TESLIM_N,
                   "eslesmeyen_toplam": eslesmeyen_toplam},
        "suzgec": {"limit": n, "limit_istenen": limit, "ajan": ajan,
                   "eslesen_n": len(ajanlar), "toplam_n": len(plan)},
    }
