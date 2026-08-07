"""GÜVENLİK BAŞLIKLARI — UYGULAMA KATMANINDA ZORLANIYOR MU (v203, 2026-08-07).

NİYE VAR. Bu depo iki yıldır "CSP-self yasası"ndan söz ediyor: `test_web_csp_uyum.py` satır içi
işleyicileri yasaklarken, `test_yazitipi_v201.py` dış font host'unu yasaklarken, `api.py`'nin
statik rota notları "dağıtım CSP'si `script-src 'self'`" derken hep aynı yasaya dayandılar.
ÖLÇÜM (Rol-1, canlı A1) o yasanın YOK olduğunu gösterdi:

    curl -D- http://127.0.0.1:8080/    →  ne Content-Security-Policy, ne X-Frame-Options,
                                          ne X-Content-Type-Options.  HİÇBİRİ.

Sebep tek cümlede: başlıklar YALNIZ `deploy/Caddyfile`'da tanımlıydı ve **A1'de Caddy koşmuyor**
(`systemctl is-active caddy` → inactive, `/etc/caddy/Caddyfile` yok). Yani üç test dosyasının
GEREKÇESİ doğruydu, dayandıkları YASA ise üretimde hiç yürürlükte değildi. Bu deponun baskın
kusur sınıfı: kurulu ≠ çalışır.

BU DOSYA O BOŞLUĞU KAPALI TUTAR ve dört ayrı gerilemeyi adlandırır:

  Ç1  BAŞLIK GERÇEKTEN GİDİYOR MU — her yüzeyde, ölçülerek. "Middleware yazıldı" bir vaat;
      ölçülen şey `TestClient` yanıtının başlık sözlüğüdür.
  Ç2  DEĞER CADDYFILE'LA BİREBİR Mİ — iki kaynak (uygulama + atıl vekil referansı) DİZE
      EŞİTLİĞİYLE bağlanır. Bağlanmazsa "aynı politika" iddiası zamanla sessizce yalan olur.
  Ç3  POLİTİKA GEVŞEDİ Mİ — `script-src`'de `unsafe-inline`/`unsafe-eval` yok, `font-src`'de
      dış host yok, `frame-ancestors 'none'` duruyor. (D4 sertleştirmesi geri alınamaz.)
  Ç4  VARLIK YOLU BOZULDU MU — ETag pazarlığı, gövdesiz 304 ve önbellek yasası AYNEN duruyor.
      Bir başlık middleware'i gövdeye dokunursa `FileResponse`/304 sözleşmesi kırılır.

AYRICA Ç5: `/halt`. O sayfa `api.py`'den üretiliyordu ve GÖVDELİ bir `<script>` taşıyordu —
yani politikayı zorlamaya başlamak, acil durdurma düğmesini SESSİZCE öldürürdü (sayfa çizilir,
tıklanır, hiçbir şey olmaz). Betik `/halt.js` rotasına alındı; buradaki testler hem başlığı hem
de düğmenin ulaşabileceği bir betiğin GERÇEKTEN sunulduğunu ölçer.

Ağ istemez, tarayıcı istemez — TestClient ile GERÇEK istek atılır.
"""
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from meridian.api import CSP_POLITIKASI, GUVENLIK_BASLIKLARI, app

KOK = pathlib.Path(__file__).resolve().parents[1]
CADDY_YOL = KOK / "deploy" / "Caddyfile"


@pytest.fixture
def istemci(sandbox_state):
    """`sandbox_state` ZORUNLU: `TestClient(app)` uygulamayı AYAĞA KALDIRIR ve açılış yolu canlı
    `state/events.jsonl`e yazar (conftest'in canlı-state bekçisi bunu haklı olarak kırar —
    operatöre sunulan defter bir test artefaktı taşıyamaz)."""
    with TestClient(app) as c:
        yield c


# ===================== YÜZEY HARİTASI =====================
# Sınıfları AYIRMAK bilinçli: brief "TÜM HTML yanıtları" ile "JSON/API yanıtlarında güvenli
# olanlar"ı ayrı sözleşmeler olarak yazdı, ve `font/woff2` ayrıca "davranışı BOZULMAYACAK" diye
# işaretlendi. Tek düz liste, hangi sınıfın hangi gerekçeyle kapsandığını okunmaz kılardı.
HTML_YUZEYLER = ["/", "/landing", "/workflow", "/runbook", "/halt"]
BETIK_YUZEYLER = ["/app.js", "/theme.js", "/landing.js", "/workflow.js", "/palette.js", "/halt.js"]
VARLIK_YUZEYLER = ["/fonts/recursive-sans-vf.woff2", "/fonts/recursive-mono-vf.woff2"]
JSON_YUZEYLER = ["/api/public/summary", "/healthz", "/api/session", "/api/summary"]
METIN_YUZEYLER = ["/metrics"]

TUM_YUZEYLER = HTML_YUZEYLER + BETIK_YUZEYLER + VARLIK_YUZEYLER + JSON_YUZEYLER + METIN_YUZEYLER


# ===================== Ç1 · BAŞLIK GERÇEKTEN GİDİYOR MU =====================

@pytest.mark.parametrize("yol", TUM_YUZEYLER)
def test_her_yuzey_TUM_guvenlik_basliklarini_alir(istemci, yol):
    """Her yüzey, `GUVENLIK_BASLIKLARI`nın TAMAMINI ve DEĞERİYLE alır.

    "Var mı" değil "hangi değerle" ölçülür: boş ya da kısaltılmış bir CSP de bir başlıktır ve
    varlık kontrolünde yeşil yanar. Ölçümün ilk hâli (bu tur, değişiklikten ÖNCE) altı yüzeyde
    de `HİÇBİRİ` diyordu — yani bu testin kırık hâli gerçekten yaşandı."""
    r = istemci.get(yol)
    for ad, beklenen in GUVENLIK_BASLIKLARI.items():
        assert ad.lower() in {k.lower() for k in r.headers}, (
            f"{yol} ({r.status_code}): `{ad}` başlığı YOK. Politika yalnız deploy/Caddyfile'da "
            f"tanımlıysa ve vekil koşmuyorsa — A1'deki durum buydu — hiçbir şey zorlanmaz.")
        assert r.headers[ad] == beklenen, (
            f"{yol}: `{ad}` değeri sapmış.\n  gelen   : {r.headers[ad]!r}\n"
            f"  beklenen: {beklenen!r}")


@pytest.mark.parametrize("yol", HTML_YUZEYLER)
def test_HTML_yuzeyleri_gercekten_HTML_dondurur(istemci, yol):
    """Yüzey haritası bir VARSAYIM olmasın: CSP'nin anlamlı olduğu tek bağlam belge bağlamıdır.

    Bir yol sessizce 404'e ya da JSON'a düşerse yukarıdaki başlık testi hâlâ geçer ama artık
    HTML yüzeyini ölçmüyordur — kapsam sessizce daralır. (`/runbook` `docs/RUNBOOK.md` yoksa
    dürüst bir 503 döner; o hâlde bu test ATLANIR, çünkü ölçtüğü şey belge yüzeyidir, belgenin
    varlığı değil — ve 503 de başlığı ALMAK ZORUNDADIR, onu Ç1 zaten sınadı.)"""
    r = istemci.get(yol)
    if r.status_code == 503:
        pytest.skip(f"{yol} → 503 (kaynak belge üretilmemiş); başlık sözleşmesi Ç1'de sınandı")
    assert r.status_code == 200, f"{yol} → {r.status_code}"
    assert r.headers["content-type"].split(";")[0].strip() == "text/html"


@pytest.mark.parametrize("yol", JSON_YUZEYLER + METIN_YUZEYLER)
def test_API_yanitlarinda_nosniff(istemci, yol):
    """`X-Content-Type-Options: nosniff` API yanıtlarında BAĞIMSIZ olarak değerlidir.

    CSP bir belge politikasıdır ve bir JSON gövdesinde tarayıcı onu yok sayar; `nosniff` ise
    tam da orada iş görür: içerik-tipi tahmini kapanır, yani saldırganın kontrol ettiği bir
    alanı taşıyan bir JSON yanıtı `text/html` sanılıp çizilemez."""
    assert istemci.get(yol).headers.get("x-content-type-options") == "nosniff"


def test_404_ve_bilinmeyen_yol_da_baslik_alir(istemci):
    """Hata yanıtları kapsamın DIŞINDA kalmaz — iki AYRI yoldan geçtikleri için ikisi de ölçülür.

    `/fonts/yok.woff2` rotanın KENDİ 404'üdür (izin listesi reddi); `/boyle-bir-yol-yok` ise
    çerçevenin `ExceptionMiddleware` 404'üdür. Bir başlık katmanı ilkini kapsayıp ikincisini
    kaçırabilir; ayrı ölçülmezse fark görünmez."""
    for yol in ("/fonts/yok.woff2", "/boyle-bir-yol-yok"):
        r = istemci.get(yol)
        assert r.status_code == 404, f"{yol} → {r.status_code} (bu test 404 yolunu ölçüyor)"
        assert r.headers.get("content-security-policy") == CSP_POLITIKASI, (
            f"{yol}: hata yanıtı CSP'siz döndü")
        assert r.headers.get("x-content-type-options") == "nosniff"


def test_HSTS_uygulama_katmanindan_GONDERILMEZ(istemci):
    """`Strict-Transport-Security` vekilde KALIR ve bu bir eksiklik değil, bir doğruluk kararıdır.

    Uygulama loopback'te düz HTTP konuşur. HSTS'i düz HTTP üzerinden göndermek RFC 6797 §8.1'e
    göre tarayıcının YOK SAYDIĞI bir gürültüdür; TLS'i kimin sonlandırdığını bilen tek katman
    vekildir. Yanlış katmandan gönderilen bir başlık, "gönderiliyor" diye işaretlenip hiçbir şey
    yapmadığında ölçümü kirletir."""
    assert "strict-transport-security" not in {k.lower() for k in istemci.get("/").headers}
    assert "Strict-Transport-Security" not in GUVENLIK_BASLIKLARI


# ===================== Ç2 · CADDYFILE İLE BİREBİR (tek kaynak çivisi) =====================

def _caddy_satir(ad: str) -> tuple[str, bool] | None:
    """Caddyfile'daki `<Ad> "<değer>"` satırını bul → (değer, yorumda_mı). Yoksa None."""
    m = re.search(rf'^([\t ]*)(#?)[\t ]*{re.escape(ad)}[\t ]+"([^"]*)"',
                  CADDY_YOL.read_text(encoding="utf-8"), re.M)
    return (m.group(3), m.group(2) == "#") if m else None


@pytest.mark.parametrize("ad", sorted(GUVENLIK_BASLIKLARI))
def test_caddyfile_referans_degeri_api_pydekiyle_BIREBIR(ad):
    """İki kaynak DİZE EŞİTLİĞİYLE bağlıdır — "aynı politika" bir iddia değil, bir ölçüm olsun.

    Vekil kopyası bugün ATIL (yorumda). Atıl olması sürüklenmeyi zararsız YAPMAZ: Caddy bir gün
    devreye alınırsa açılacak olan o satırdır, ve o an ayrışmış bir değer uygulamanınkini SET
    semantiğiyle sessizce EZER. Kapı bu yüzden burada, sürüklenmenin ucunda değil."""
    bulunan = _caddy_satir(ad)
    assert bulunan is not None, (
        f"deploy/Caddyfile'da `{ad}` referans satırı YOK. Silinmişse tek-kaynak çivisi de "
        f"silinmiş demektir; satır atıl (yorumlu) hâlde DURMALI.")
    deger, _ = bulunan
    assert deger == GUVENLIK_BASLIKLARI[ad], (
        f"`{ad}` iki kaynakta AYRIŞTI:\n  api.py  : {GUVENLIK_BASLIKLARI[ad]!r}\n"
        f"  Caddyfile: {deger!r}\nDeğiştirilecek şey varsa api.py'deki sözlüktedir; "
        f"Caddyfile satırı onun atıl kopyasıdır.")


@pytest.mark.parametrize("ad", sorted(GUVENLIK_BASLIKLARI))
def test_caddyfile_kopyasi_ATIL_yani_yorumda(ad):
    """Vekil kopyası ETKİN OLMAMALI — yoksa iki CANLI tanım olur.

    Caddy'de `header <ad> <değer>` bir SET'tir: vekil etkinleştirildiğinde üstteki kopya
    uygulamanınkini değiştirir. İki canlı tanım = zamanla ayrışan iki yasa, ve ayrışmanın yönü
    tahmin edilemez (biri sertleşir, öteki gevşer, tarayıcı gevşeyeni görür)."""
    deger, yorumda = _caddy_satir(ad)
    assert yorumda, (
        f"deploy/Caddyfile'da `{ad}` satırı AÇILMIŞ. Vekil devreye alınırsa bu satır uygulamanın "
        f"yazdığı başlığı EZER ve sürüklenme sessizce üretime çıkar. Yoruma geri al; "
        f"canlı tanım `meridian/api.py::GUVENLIK_BASLIKLARI`.")


def test_vekile_AIT_kalemler_Caddyfile_da_ETKIN_kalir():
    """`Strict-Transport-Security` ve `-Server` vekilde AÇIK kalmalı — taşınmadılar, düşmediler.

    Yoruma alma turunun en olası kazası hepsini birden kapatmaktı; o hâlde TLS'i sonlandıran
    katmanın tek yapabildiği iki şey de sessizce kaybolurdu."""
    caddy = CADDY_YOL.read_text(encoding="utf-8")
    hsts = _caddy_satir("Strict-Transport-Security")
    assert hsts is not None and not hsts[1], (
        "Strict-Transport-Security yorumda ya da yok — uygulama onu GÖNDEREMEZ (düz HTTP), "
        "yani bu satır kapanırsa HSTS hiçbir katmanda kalmaz")
    assert re.search(r"^[\t ]*-Server[\t ]*$", caddy, re.M), (
        "`-Server` düşmüş: sunucu parmak izini silen tek yer vekildi (uygulama katmanındaki "
        "karşılığı ASGI sunucusunun anahtarıdır ve api.py'de AÇIK BORÇ olarak yazılı)")


# ===================== Ç3 · POLİTİKA GEVŞEDİ Mİ =====================

def _direktif(ad: str) -> str:
    m = re.search(rf"(?:^|;\s*){re.escape(ad)}\s+([^;]+)", CSP_POLITIKASI)
    assert m, f"CSP'de `{ad}` direktifi YOK: {CSP_POLITIKASI!r}"
    return m.group(1).strip()


def test_script_src_de_unsafe_YOK():
    """`script-src`'ye `'unsafe-inline'` EKLENMEZ — ve artık bu ölçülen bir yasa.

    Eklemek zorunda kalındıysa sebep neredeyse kesinlikle bir yere satır içi `onclick`in ya da
    gövdeli bir `<script>`in geri gelmesidir; doğru çözüm başlığı gevşetmek değil, eylemi
    `app.js`'teki EYLEMLER kümesine kaydetmek ya da betiği aynı-origin bir rotaya almaktır
    (`/halt.js`'in var oluş sebebi tam olarak budur)."""
    d = _direktif("script-src")
    assert "unsafe-inline" not in d, f"script-src gevşetilmiş: {d!r}"
    assert "unsafe-eval" not in d, f"script-src'de unsafe-eval: {d!r} — panoda eval kullanımı yok"
    assert d == "'self'", f"script-src {d!r} — 'self' dışında bir kaynak eklenmiş"


def test_font_src_D4_sertlestirmesi_GERI_ALINMADI():
    """`font-src 'self'` — `fonts.gstatic.com` ve `fonts.googleapis.com` GERİ GELMEZ.

    D4 (2026-08-07) iki dış host'u düşürdü çünkü Recursive kendi-barındırılıyor. Geri eklemek
    zorunda kalındıysa bir yere CDN'li bir `<link>`/`@font-face` geri gelmiş demektir; çözüm
    dosyayı `meridian/web/fonts/` altına koymaktır."""
    assert _direktif("font-src") == "'self'", f"font-src gevşemiş: {_direktif('font-src')!r}"
    for direktif in ("style-src", "img-src", "connect-src", "default-src", "font-src"):
        assert "//" not in _direktif(direktif), (
            f"`{direktif}` bir DIŞ ORIGIN taşıyor: {_direktif(direktif)!r} — "
            f"panonun hiçbir yüzeyi üçüncü taraf yüklemiyor")


def test_cerceveleme_ve_taban_kapali():
    """Tıklama hırsızlığı ve taban-URL enjeksiyonu: iki ayrı kapı, ikisi de kapalı kalmalı."""
    assert _direktif("frame-ancestors") == "'none'"
    assert _direktif("base-uri") == "'self'"
    assert _direktif("form-action") == "'self'"
    assert GUVENLIK_BASLIKLARI["X-Frame-Options"] == "DENY"


def test_style_src_borcu_BEYANLI_kalir():
    """`style-src`'deki `'unsafe-inline'` AÇIK bir borçtur ve gizlenmez (YASA 4).

    Bu test onu SAVUNMUYOR — kapandığı gün bilinçli olarak güncellenir. Ölçtüğü şey, borcun
    sessizce ötekilere (script/font) BULAŞMAMASI: bugün tek gevşek direktif budur."""
    gevsek = [d for d in re.split(r";\s*", CSP_POLITIKASI) if "unsafe-" in d]
    assert gevsek == ["style-src 'self' 'unsafe-inline'"], (
        f"CSP'de beklenmedik gevşeme: {gevsek} — bilinen tek borç style-src'dir")


# ===================== Ç4 · VARLIK YOLU BOZULMADI =====================

@pytest.mark.parametrize("yol", ["/theme.js", "/app.js", "/fonts/recursive-sans-vf.woff2"])
def test_ETag_ve_304_pazarligi_AYNEN_calisir(istemci, yol):
    """Başlık katmanı gövdeye DOKUNMAZ: güçlü ETag, gövdesiz 304 ve tam-gövde dönüşü aynen.

    NEDEN GERÇEK BİR RİSK: `@app.middleware("http")` (BaseHTTPMiddleware) yanıtı bir
    `StreamingResponse`a sarar; bu dosyanın statik yolu ise tam olarak gövde-akışı
    (`FileResponse`, app.js 518 KB) ve GÖVDESİZLİK (`Response(status_code=304)`) üzerine kurulu.
    Bu yüzden saf ASGI sarıcısı seçildi — ve o seçimin doğrulaması burada ölçülüyor."""
    r1 = istemci.get(yol)
    assert r1.status_code == 200
    etag = r1.headers.get("etag")
    assert etag and not etag.startswith("W/"), f"{yol}: güçlü ETag kayboldu ({etag!r})"

    r2 = istemci.get(yol, headers={"If-None-Match": etag})
    assert r2.status_code == 304, f"{yol}: eşleşen ETag'e {r2.status_code} döndü"
    assert r2.content == b"", "304 GÖVDESİZDİR (RFC 9110 §15.4.5) — middleware gövde eklemiş"
    assert "content-length" not in {k.lower() for k in r2.headers}, (
        f"{yol}: 304'e `Content-Length` yazılmış (RFC 9110 §15.4.5)")

    r3 = istemci.get(yol, headers={"If-None-Match": '"boyle-bir-etiket-yok"'})
    assert r3.status_code == 200 and r3.content == r1.content


def test_304_de_guvenlik_basligini_TASIR(istemci):
    """Gövdesiz 304 de politikayı taşır.

    Bir tarayıcı 304'ten sonra ÖNBELLEKTEKİ gövdeyi çizer; RFC 9110 §15.4.5 bu yüzden 304'ün
    saklanan yanıtın başlıklarını GÜNCELLEMESİNİ ister. Politikayı 304'te atlamak, uzun ömürlü
    bir sekmede eski politikayı yaşatmanın en sessiz yoludur."""
    r1 = istemci.get("/theme.js")
    r2 = istemci.get("/theme.js", headers={"If-None-Match": r1.headers["etag"]})
    assert r2.status_code == 304
    assert r2.headers.get("content-security-policy") == CSP_POLITIKASI


@pytest.mark.parametrize("yol", VARLIK_YUZEYLER)
def test_font_onbellek_ve_tipi_DEGISMEDI(istemci, yol):
    """`font/woff2` + `no-cache` + `immutable` DEĞİL — D5 sözleşmesi aynen (bkz. test_font_rotasi_v202)."""
    r = istemci.get(yol)
    assert r.headers["content-type"].split(";")[0].strip() == "font/woff2"
    cc = r.headers.get("cache-control", "")
    assert "no-cache" in cc and "immutable" not in cc, f"{yol}: önbellek yasası kaymış ({cc!r})"
    assert cc == istemci.get("/theme.js").headers.get("cache-control")


@pytest.mark.parametrize("yol", BETIK_YUZEYLER + VARLIK_YUZEYLER)
def test_govde_bozulmadi(istemci, yol):
    """Varlıklar hâlâ boş olmayan bir gövde döndürüyor — başlık turu içeriği kesmiş olmasın."""
    r = istemci.get(yol)
    assert r.status_code == 200 and len(r.content) > 0, f"{yol} → {r.status_code}, {len(r.content)} bayt"


# ===================== Ç5 · /halt: BAŞLIK SAYFAYI ÖLDÜRMÜYOR =====================

def test_halt_sayfasinda_GOVDELI_script_YOK(istemci):
    """`/halt` gövdeli bir `<script>` taşımamalı — yoksa CSP altında düğme SESSİZCE ölür.

    ÖLÇÜM KAYNAKTAN DEĞİL TELDEN: bu sayfa bir dosyadan okunmuyor, `api.py` içinde üretiliyor,
    yani `test_web_csp_uyum.py`nin dosya-tarayan kapsamının DIŞINDA kalıyordu. Politikayı
    uygulama katmanına almak, o kör noktayı canlı bir arızaya çevirirdi: sayfa çizilir, dev
    kırmızı düğme durur, tıklanır ve HİÇBİR ŞEY OLMAZ. Acil durdurma yüzeyinde bu, panonun geri
    kalanının ölmesinden kötüdür — operatör "durdurdum" sanır."""
    govde = istemci.get("/halt").text
    govdeli = re.findall(r"<script(?![^>]*\ssrc=)[^>]*>", govde)
    assert not govdeli, (
        f"/halt içinde gövdeli <script> var: {govdeli}. `script-src 'self'` bunu BLOKLAR — "
        f"HALT düğmesi ölür. Betiği /halt.js gibi aynı-origin bir rotaya al.")
    assert not re.search(r'\son[a-z]+\s*=\s*["\']', govde), (
        "/halt içinde satır içi olay özniteliği var — CSP bunları da bloklar")


def test_halt_in_istedigi_betik_GERCEKTEN_sunuluyor(istemci):
    """`<script src>` bir VAAT'tir; ölçülen şey o yolun 200 ve JS döndürmesidir.

    `StaticFiles` montajı bu depoda BİLEREK yok, yani bir yol yazmak onu yayına ALMAZ — D5'te
    `/fonts/*` tam olarak böyle 404 dönüyordu. Aynı hata burada HALT düğmesini öldürürdü."""
    sayfa = istemci.get("/halt").text
    yollar = re.findall(r'<script[^>]*\ssrc=["\']([^"\']+)["\']', sayfa)
    assert yollar, "/halt hiç betik yüklemiyor — düğme delegasyonsuz ve ölü olurdu"
    for y in yollar:
        assert not y.startswith(("http://", "https://", "//")), (
            f"/halt dış origin'den betik çekiyor ({y}) — `script-src 'self'` bloklar")
        r = istemci.get(y)
        assert r.status_code == 200, f"/halt `{y}` istiyor ama rota {r.status_code} döndürüyor"
        assert "javascript" in r.headers.get("content-type", "")


def test_halt_js_govdesi_HALT_ucuna_baglaniyor(istemci):
    """Sunulan betik GERÇEKTEN durdurma betiği olmalı — 200 tek başına bir kanıt değil.

    Yanlış içerikle dönen bir betik rotası, tarayıcıda rotanın hiç olmamasıyla aynı sonucu verir
    (düğme ölü) ama "200 döndü" testinde yeşil yanar."""
    js = istemci.get("/halt.js").text
    for beklenen in ("/api/halt", "/api/resume", "x-meridian-token"):
        assert beklenen in js, f"/halt.js içinde `{beklenen}` yok — yanlış gövde sunuluyor"


def test_halt_YETKISIZ_erisilebilir_kalir(istemci):
    """`/halt` ve `/halt.js` kapısızdır ve öyle kalmalı.

    Acil durdurma sayfasının arkasına bir oturum kapısı konsaydı, tam da ihtiyaç duyulan anda
    (operatör telefonda, oturum düşmüş) sayfa ölü açılırdı. Yazma yetkisi zaten `/api/halt`
    ucundadır — sayfanın kendisi hiçbir sır taşımaz."""
    assert istemci.get("/halt").status_code == 200
    assert istemci.get("/halt.js").status_code == 200
