"""api.py — FastAPI read-model over state/ + a tiny write surface (HALT / resume / approvals).
The dashboard NEVER talks to the broker directly; it reads state and posts operator intents.
Single-operator: reach it over an IAP tunnel (no inbound firewall on the VM). Optional shared-token
gate for local use. Research system. Paper mode. Not financial advice."""
from __future__ import annotations
import functools
import hmac
import inspect
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
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
DASH_TOKEN = os.environ.get("MERIDIAN_DASH_TOKEN")  # required to reach the API over a network origin

# Cross-origin access — OFF unless MERIDIAN_CORS_ORIGINS is set (comma-separated origins, or "*"). Lets a
# frontend on ANOTHER origin (e.g. a local dashboard) call this agent's API. Only meaningful with a token.
_CORS = [o.strip() for o in os.environ.get("MERIDIAN_CORS_ORIGINS", "").split(",") if o.strip()]
if _CORS:
    app.add_middleware(CORSMiddleware, allow_origins=_CORS, allow_credentials=False,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["x-meridian-token", "content-type"])
    if not DASH_TOKEN:
        obs.warn("cors_without_token",
                 detail="CORS enabled but MERIDIAN_DASH_TOKEN unset — API is cross-origin AND unauthenticated")


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


_NOCACHE = {"Cache-Control": "no-cache, must-revalidate"}


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(WEB / "index.html", headers=_NOCACHE)


@app.get("/app.js")
def appjs():
    return FileResponse(WEB / "app.js", media_type="application/javascript", headers=_NOCACHE)


# STATİK BETİKLER TEK TEK YÖNLENDİRİLİR (StaticFiles montajı YOK): montaj, WEB dizinine sonradan
# düşen her dosyayı — yedek, taslak, .orig — sessizce yayına açar. Ad ad yazmak sıkıcı ama
# yayına ne çıktığı okunabilir kalır.
#
# NEDEN SATIR İÇİ DEĞİL DE DOSYA: dağıtım CSP'si `script-src 'self'` (deploy/Caddyfile).
# Satır içi bloklar üretimde bloklanır — landing ve workflow bu yüzden dışarı taşındı; o iki
# sayfa aksi hâlde canlıda ölü açılırdı (workflow'un tüm diyagramı script'te üretiliyor).
@app.get("/theme.js")
def themejs():
    return FileResponse(WEB / "theme.js", media_type="application/javascript", headers=_NOCACHE)


@app.get("/landing.js")
def landingjs():
    return FileResponse(WEB / "landing.js", media_type="application/javascript", headers=_NOCACHE)


@app.get("/workflow.js")
def workflowjs():
    return FileResponse(WEB / "workflow.js", media_type="application/javascript", headers=_NOCACHE)


@app.get("/landing", response_class=HTMLResponse)
def landing():
    """The original marketing landing page — the design reference the dashboard is cut from."""
    return FileResponse(WEB / "landing.html")


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
def workflow():
    """İnteraktif günlük karar hattı diyagramı — kapanış sonrası tek döngünün tam akışı; bugünkü
    darboğaz turunda eklenen mekanizmalar YENİ rozetiyle işaretli. Bağımsız, dış bağımlılık yok."""
    return FileResponse(WEB / "workflow.html")


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


@app.get("/api/today")
def api_today(request: Request):
    _auth(request)
    d = analytics.today()
    d["inbox_count"] = _inbox_count()
    d["latest_session"] = (store.read_json("portfolio.json", {}) or {}).get("last_date")
    # GERÇEK-CANLI SAYAÇ (BT-1, 2026-07-31). Panonun bugüne kadar gösterdiği "95 kapanmış işlem"
    # sayısı bir KARIŞIMDI: gövdesi replay tohumu (tek toplu yazım, bugünkü evrenle, survivorship'li)
    # ve satırlarda kaynak damgası yoktu — yani operatör "sistem 95 işlem yaptı" cümlesini okuyor,
    # gerçekte canlı kanıt sayısını hiçbir yerden öğrenemiyordu. Bu alan o üç sayıyı yan yana
    # koyar; hangi satırın kanıt, hangisinin training olduğu tek bakışta okunur.
    # ALAN ŞİMDİ HAZIR, PANO SONRAKİ TURDA BAĞLAR (web/* bu turda başka bir kolda).
    from . import ledgerstamp as _ls
    d["defter"] = _ls.counts()
    _enrich_stale_plans(d.get("todays_plans") or [], d["latest_session"])
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
    _auth(request)
    return analytics.agent_view()


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
        return skill_evolve.apply_revision(skill)
    if action == "reject":
        return skill_evolve.reject_revision(skill)
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
            local_agent = {"ok": False, "detail": f"senkron hatası ({type(e).__name__})"}
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
            local_agent = {"ok": False, "detail": f"senkron hatası ({type(e).__name__})"}
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


@app.get("/api/diagnostics")
def api_diagnostics(request: Request):
    """Faz 1 — Teşhis API'si: diskte zaten duran tüm operasyon telemetrisini TEK uçta toplar.
    Mutabakat (hayaletler, HWM çiftleri, force-sync), risk/bütçe, MLOps (diff, deflasyon, ısınma,
    UCB), veri hattı (sabır, karantina, IO gecikme, çapraz-doğrulama), defter sayaçları."""
    _auth(request)
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
    return {
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
        "ogrenme": an.learning_automation(),
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
                      "failed_submissions": health.split_rejections(rc.get("failed_submissions"))},
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
        "risk": {"regime": store.read_json("regime.json", {}),
                 "blackout_radar": earnings.blackout_radar(list(REPLAY_UNIVERSE), today),
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
                 "halted": health.halted(), "learn_halted": health.learn_halted()},
        "mlops": {"recent_hypotheses": diffs, "deflate": an.deflate_stats(),
                  "deflate_why": an.deflate_why(), "gate_hist": last_hist,
                  "llm_calibration": store.read_json("llm_calibration.json", {}),
                  "exit_efficiency": store.read_json("exit_efficiency.json", None),
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
        "watchdog": __import__("meridian.watchdog", fromlist=["report"]).report(),
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
        "sieve": __import__("meridian.sieve", fromlist=["report"]).report()}


# ---------- Hermes (the reflection brain) ----------
@app.get("/api/hermes")
def api_hermes(request: Request):
    """Hermes status + spend + last proposals for the dashboard's Hermes section."""
    _auth(request)
    from . import hermes_runtime, spend, skills, scheduler, sprint
    hyps = memory.all_hypotheses()
    from . import hermes as _hm
    return {"status": hermes_runtime.status(), "spend": spend.summary(),
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
    return hermes_runtime.reflect_now()


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
        return hermes_runtime.start(poll_seconds=int(os.environ.get("HERMES_POLL_SECONDS", "300")))
    if action == "stop":
        return hermes_runtime.stop()
    if action == "backfill":                       # çevrimdışı görüş dolgusu (kalibrasyon hızlandırma)
        # DÜĞME KALIR ama artık ELLE HIZLANDIRMADIR, tek tetik DEĞİL: varsayılan akış zamanlayıcının
        # seans-sonrası öğrenme kadansıdır (scheduler._learning_cadence). Tavan da sabit 40 değil —
        # `backfill_budget()` kalan ajan kotasından türetir ve env override edilmişse ona dokunmaz.
        # Bu uçtan `max_days` VERİLMEZ: iki yerde iki tavan, formül değiştiği gün sessizce ayrışırdı.
        bt = hermes.backfill_budget()
        hermes.backfill_opinions_async()
        return {"started": bt["tavan"] > 0, "butce": bt,
                "kuyruk": hermes.backfill_queue(),
                "detail": ("görüş dolgusu arka planda başladı" if bt["tavan"] > 0
                           else f"bütçe kıstı — dolgu koşmadı ({bt['formul']})")}
    if action == "sync_integrations":              # MCP/hook/cache/pool config'i elle tazele
        return hermes.config_ensure_integrations()
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
    return sprint.start(body if isinstance(body, dict) else {})


@app.post("/api/sprint/stop")
def api_sprint_stop(request: Request):
    _auth(request)
    from . import sprint
    return sprint.stop()


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
    each cycle when MERIDIAN_BROKER=alpaca_paper). Refuses when halted."""
    _auth(request)
    from .adapters import alpaca
    if health.halted():
        return {"ok": False, "detail": "HALT aktif — emir gönderilmez"}
    if not alpaca.paper_available():
        return {"ok": False, "detail": "Alpaca paper anahtarları yok"}
    meta = store.read_json("portfolio.json", {})
    armed = meta.get("armed", [])
    acct = alpaca.account()
    eq = float(acct["equity"]) if acct and "equity" in acct else 100_000.0
    results = [{"ticker": p["ticker"], **alpaca.submit_plan(p, eq)} for p in armed]
    return {"ok": True, "submitted": sum(1 for r in results if r.get("ok")), "results": results, "equity": eq}


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
    return res


# ---------- Batch N: ops & UX ----------
@app.get("/halt", response_class=HTMLResponse)
def mobile_halt():
    """#44 — a standalone, phone-friendly panic page. One giant button → POST /api/halt. Self-contained;
    reads the token from ?token= so it works over the tunnel. No dependency on the SPA."""
    return HTMLResponse("""<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<title>Meridian — HALT</title><style>body{margin:0;background:#0b0b0f;color:#eee;font-family:system-ui;
display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;gap:24px}
button{width:78vw;max-width:420px;height:34vh;border:none;border-radius:24px;font-size:8vw;font-weight:800;
color:#fff;background:#c0362c;box-shadow:0 8px 40px rgba(192,54,44,.4)}button:active{transform:scale(.97)}
#s{font-size:16px;color:#9aa}.g{background:#1c7a3f!important}</style>
<h2>Meridian · acil durdur</h2><button id=b>■ HALT</button><div id=s>hazır</div><script>
const t=new URLSearchParams(location.search).get('token');const H=t?{'x-meridian-token':t}:{};
async function hit(p){document.getElementById('s').textContent='...';const r=await fetch(p,{method:'POST',headers:H});
document.getElementById('s').textContent=r.ok?(p.includes('resume')?'DEVAM edildi':'DURDURULDU'):'hata '+r.status;
const b=document.getElementById('b');if(p.includes('halt')){b.textContent='▶ DEVAM';b.className='g';b.onclick=()=>hit('/api/resume')}
else{b.textContent='■ HALT';b.className='';b.onclick=()=>hit('/api/halt')}}
document.getElementById('b').onclick=()=>hit('/api/halt');</script>""", headers=_NOCACHE)


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


def _inbox_count() -> int:
    """Kenar çubuğu rozeti: gelen kutusundaki bekleyen karar sayısı (ucuz sayım)."""
    try:
        from . import skill_evolve as _se, skills as _sk3
        ar = store.read_json("arming_report.json", {}) or {}
        n = sum(1 for m2 in (ar.get("measurements") or {}).values() if m2.get("status") == "gate_passed")
        n += len(_se.pending_drafts())
        n += len(_sk3.pending_recommendations())
        return n
    except Exception as e:
        # YASA 4 (2026-07-21): burada sessizce 0 dönmek, operatörün gelen kutusunda BEKLEYEN kararlar
        # varken rozetin "0" göstermesi demek — okunmamış onay = alınmamış karar. Rozet yine 0 döner
        # (uç nokta 500 vermemeli) ama sebebi artık olay akışında.
        obs.warn("inbox_count_failed", error=f"{type(e).__name__}: {e}")
        return 0


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
    return {"halted": False, "message": "HALT cleared."}


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
    return {"ok": True, "id": approval_id, "decision": decision}
