"""GÜVENLİK BAŞLIKLARI — UYGULAMA KATMANINDA ZORLANIYOR MU (v203, 2026-08-07).

NİYE VAR. Bu depo iki yıldır "CSP-self yasası"ndan söz ediyor: `test_web_csp_uyum.py` satır içi
işleyicileri yasaklarken, `test_yazitipi_v201.py` dış font host'unu yasaklarken, `api.py`'nin
statik rota notları "dağıtım CSP'si `script-src 'self'`" derken hep aynı yasaya dayandılar.
ÖLÇÜM (Rol-1, canlı A1) o yasanın YOK olduğunu gösterdi:

    curl -D- http://127.0.0.1:8080/    →  ne Content-Security-Policy, ne X-Frame-Options,
                                          ne X-Content-Type-Options.  HİÇBİRİ.

Sebep tek cümlede: başlıklar YALNIZ ters vekilin (Caddy) yapılandırmasında tanımlıydı ve
**A1'de Caddy koşmuyor** (`systemctl is-active caddy` → inactive). Yani üç test dosyasının
GEREKÇESİ doğruydu, dayandıkları YASA ise üretimde hiç yürürlükte değildi. Bu deponun baskın
kusur sınıfı: kurulu ≠ çalışır.

BU DOSYA O BOŞLUĞU KAPALI TUTAR ve dört ayrı gerilemeyi adlandırır:

  Ç1  BAŞLIK GERÇEKTEN GİDİYOR MU — her yüzeyde, ölçülerek. "Middleware yazıldı" bir vaat;
      ölçülen şey `TestClient` yanıtının başlık sözlüğüdür.
  Ç2  TANIM TEK Mİ — politikayı tanımlayan İKİNCİ bir yüzey (vekil yapılandırması, birim
      dosyası, dağıtım betiği) OLMAMALI. Bu iddia 2026-09-07'de HEDEF DEĞİŞTİRDİ; gerekçesi
      Ç2 bölümünün başında yazılı.
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

#: Ç2 taramasının AĞAÇLARI: politikayı UYGULAMA DIŞINDA tanımlayabilecek yüzeyler.
#: KAPSAM DIŞI SINIFLAR ADIYLA YAZILIDIR (tur-2 — docstring kapsamı olduğundan geniş gösteriyordu):
#:   · `tests/` — bir test başlık adını BEKLENEN DEĞER olarak taşır ve bu bir tanım değildir.
#:   · `docs/`, `research/`, `MERIDIAN_ENGINEERING_LOG.md` — tarih kaydı.
#:   · `meridian/` — tanımın KENDİ yeri; "ikinci tanım" ölçümünün konusu değil, öznesi.
#:   · `.md`/`.html`/`.txt` uzantıları — düzyazı. `deploy/README-oracle.md` bugün `Referrer-Policy`
#:     ve `Permissions-Policy` adlarını GEÇİRİYOR ve bu doğrudur: orada anlatılan şey "burada
#:     tanımlı DEĞİL"dir. Düzyazıyı kapsama almak, doğru cümleyi kırmızıya çevirirdi.
VEKIL_AGACLARI = ("deploy", "ops", ".github")

#: Depo KÖKÜNDEKİ dağıtım yüzeyleri. Tur-2'de eklendi ve gerekçesi ÖLÇÜLMÜŞTÜR: aynı IaC-K5 turu
#: `docker-compose.yml`i ve `Dockerfile`ı DÜZENLEDİ, yani ikisinin de canlı dağıtım yüzeyi olduğu
#: kabul edilmişti — ama Ç2 taraması onları görmüyordu. Biri `docker-compose.yml`e bir vekil/etiket
#: üzerinden başlık eklerse ya da `Dockerfile`a bir `ENV` yazarsa ikinci CANLI tanım doğar ve çivi
#: yeşil kalırdı. (Kök `deploy.sh` bu listede YOK çünkü tur-2'de SİLİNDİ — v448 `SILINEN_YOLLAR`.)
VEKIL_KOK_DOSYALARI = ("docker-compose.yml", "Dockerfile")

#: Taramanın gireceği uzantılar. Uzantısız dosyalar da dahildir (`Caddyfile` gibi adlar uzantısız
#: olur) — dışlamak, taramanın kaçırmak için en olası olduğu sınıfı kaçırmak olurdu. `.py` tur-2'de
#: eklendi: `ops/` altında 33 Python aracı var ve biri (`ops/apisix_uygula.py`) APISIX
#: yapılandırmasını GERÇEKTEN etcd'ye PUT ediyor — oraya yazılacak bir `response-rewrite` bloğu
#: uygulamanın başlığını SET semantiğiyle ezerdi ve eski kapsam onu hiç görmezdi.
VEKIL_UZANTILARI = ("", ".conf", ".yaml", ".yml", ".json", ".sh", ".service", ".toml", ".py")

#: POZİTİF KONTROL TABANI. ÖLÇÜLDÜ 2026-09-08: 109 dosya (deploy 61 + ops 45 + .github 1 + kök 2 —
#: `.py` ve kök yüzeyleri eklendikten sonra; eski kapsam 71'di). Eşik ÖLÇÜMÜN KENDİSİ DEĞİL: bu bir
#: çırçır değil KÖRLÜK ALARMIdır (emsal `test_capa_uyusmasi_v373.py::test_CANLI_TARAMA_SESSIZCE_BOS_DEGIL`)
#: — sayıya yapıştırmak, dosya silen her meşru temizliği kırmızıya çevirirdi. 60, "tarayıcı onlarca
#: dosyayı gerçekten görüyor" demeye yeter ve yanlış-kök/yanlış-uzantı arızasının ürettiği sıfırı
#: kaçırmaz.
VEKIL_TARAMA_ASGARI = 60


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
            f"{yol} ({r.status_code}): `{ad}` başlığı YOK. Politika yalnız vekilde tanımlıysa "
            f"ve vekil koşmuyorsa — A1'deki durum buydu — hiçbir şey zorlanmaz.")
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
    """HSTS'i YALNIZ TLS'i sonlandıran katman gönderebilir — ve bugün o katman onu GÖNDERMİYOR.

    Uygulama loopback'te düz HTTP konuşur. HSTS'i düz HTTP üzerinden göndermek RFC 6797 §8.1'e
    göre tarayıcının YOK SAYDIĞI bir gürültüdür; TLS'i kimin sonlandırdığını bilen tek katman
    vekildir. Yanlış katmandan gönderilen bir başlık, "gönderiliyor" diye işaretlenip hiçbir şey
    yapmadığında ölçümü kirletir. Bu test o yüzden başlığın BURADAN çıkmadığını ölçer.

    NE OLMADIĞI DA YAZILI (tur-2 düzeltmesi — tek-kaynak yasası). Bu docstring "HSTS vekilde
    KALIR" diyordu; aynı dosyanın ~70 satır aşağısı ise doğru olanı söylüyor: vekil yapılandırması
    IaC-K5 ile silindi ve iki kalem de bugün HİÇBİR yapılandırmada tanımlı DEĞİL. Bir dosyada iki
    zıt hüküm, borcu sulandırır: sonraki tur ilkini okur ve HSTS'in bir yerde durduğunu sanar.
    Borcun tek kaydı `test_vekile_AIT_iki_kalem_ACIK_BORC_olarak_YAZILI`dır."""
    assert "strict-transport-security" not in {k.lower() for k in istemci.get("/").headers}
    assert "Strict-Transport-Security" not in GUVENLIK_BASLIKLARI


# ===================== Ç2 · TANIM TEK Mİ (tek kaynak çivisi) =====================
#
# HEDEF DEĞİŞTİ, ÇİVİ SİLİNMEDİ (IaC-K5, operatör kararı 2026-09-07 — bedel yasası).
#
# ESKİ HÂL: politikanın vekil tarafında ATIL (yorumlu) bir referans kopyası duruyordu ve buradaki
# üç test onu okuyordu — değerin sözlükle DİZE EŞİTLİĞİ, kopyanın ETKİN OLMAMASI, ve vekile ait
# iki kalemin (`Strict-Transport-Security`, `-Server`) orada AÇIK kalması. Ölü GCP yolu silinirken
# o dosya da düştü, yani üç iddianın da OKUYACAĞI kaynak yok.
#
# NE KAYBEDİLDİ, açıkça (bedel yasası — kazanç ölçülüp bedel ölçülmezse körlük sessizdir):
#   (a) "iki kopya ayrıştı mı" ölçümü. Yerine gelen iddia daha güçlüdür — ayrışacak İKİNCİ bir
#       kopyanın hiç VAR OLMAMASI — ama aynı şey değildir ve öyle yazılıyor.
#   (b) `Strict-Transport-Security` ile `-Server`ın bir dosyada YAZILI durduğunun ölçümü. Bu
#       GERÇEK bir kayıptır: bugün ikisi de hiçbir yapılandırmada tanımlı değil. Kaybı ölçülebilir
#       tutmanın tek dürüst yolu, borcun KENDİSİNİ ölçmektir (`test_vekile_AIT_iki_kalem…`).
#
# NEDEN "İKİNCİ TANIM YOK" DOĞRU SÜREKÇİ: bir vekilde `header <ad> <değer>` (Caddy) ya da
# `response-rewrite` (APISIX) SET semantiğindedir — ikinci bir canlı tanım uygulamanınkini
# SESSİZCE ezer. Eskiden kapı "kopya ayrışmasın" diyordu; şimdi "kopya doğmasın" diyor.


def _vekil_dosyalari():
    """Dağıtımda GERÇEKTEN okunan yapılandırma/betik yüzeylerini gezer.

    Kapsam `VEKIL_AGACLARI` × `VEKIL_UZANTILARI` + `VEKIL_KOK_DOSYALARI` ile YAZILIDIR: sessiz bir
    kapsam daralması (ör. yeni bir uzantının unutulması, ya da `deploy/`nin bir gün yeniden
    adlandırılması — tasarım belgesi Ansible/Terraform geçişini zaten planlıyor) bu testi bir gün
    hiçbir şey ölçmeden yeşil bırakırdı ve o hâl, testin hiç olmamasından kötüdür. O yüzden
    `if not kok.is_dir(): continue` bir SESSİZ ATLAMA olmaktan çıkarıldı: aşağıdaki
    `test_vekil_taramasi_SESSIZCE_BOS_DEGIL` üreticinin gerçekten dosya bulduğunu ÖLÇER."""
    for agac in VEKIL_AGACLARI:
        kok = KOK / agac
        if not kok.is_dir():
            continue
        for p in sorted(kok.rglob("*")):
            if p.is_file() and p.suffix in VEKIL_UZANTILARI:
                yield p
    for ad in VEKIL_KOK_DOSYALARI:
        p = KOK / ad
        if p.is_file():
            yield p


def test_vekil_taramasi_SESSIZCE_BOS_DEGIL():
    """POZİTİF KONTROL: Ç2'nin tarayıcısı canlı ağaçta gerçekten dosya BULUYOR.

    NEDEN AYRI BİR ÇİVİ: `_vekil_dosyalari` var olmayan bir kökü sessizce atlar. `deploy/` ya da
    `ops/` bir gün taşınır/yeniden adlandırılırsa üretici SIFIR dosya döner ve Ç2'nin İKİ iddiası
    da (`ikinci_kez_TANIMLANMAMIS`, `politikasi_metni_yalniz_uygulamada`) hiçbir şey taramadan
    GEÇER — koruma sessizce ölür. Üreticinin kendi docstring'i bu hâli "testin hiç olmamasından
    kötüdür" diye ADLANDIRIYORDU ama ÖLÇMÜYORDU; adlandırılmış ve ölçülmemiş bir risk, ölçülmemiş
    bir risktir."""
    n = len(list(_vekil_dosyalari()))
    assert n >= VEKIL_TARAMA_ASGARI, (
        f"vekil taraması yalnız {n} dosya gördü (asgari {VEKIL_TARAMA_ASGARI}, ölçülen taban "
        f"2026-09-08: 109). Kök taşınmış ya da uzantı süzgeci daralmış olabilir — Ç2'nin iki "
        f"iddiası bu hâlde HİÇBİR ŞEY ölçmeden yeşil yanar.")


@pytest.mark.parametrize("ad", sorted(GUVENLIK_BASLIKLARI))
def test_baslik_UYGULAMA_DISINDA_ikinci_kez_TANIMLANMAMIS(ad):
    """Her başlığın tanımı TEK yerdedir: `meridian/api.py::GUVENLIK_BASLIKLARI`.

    Vekil/birim/betik ağacında bir başlık ADI geçiyorsa iki hâlden biridir ve ikisi de kapıyı
    hak eder: ya ikinci bir CANLI tanım doğmuştur (uygulamanınkini SET semantiğiyle ezer), ya da
    yeni bir ATIL kopya (v203'ün ilk turunda tam olarak bu vardı ve sürüklenme riski oradaydı).
    Bugün yüzey TEMİZ ve testin işi onu temiz tutmaktır."""
    kirli = [p.relative_to(KOK) for p in _vekil_dosyalari()
             if ad in p.read_text(encoding="utf-8", errors="replace")]
    assert not kirli, (
        f"`{ad}` uygulama DIŞINDA da geçiyor: {kirli}. Vekil başlık yönergeleri SET'tir — "
        f"ikinci tanım uygulamanın yazdığını sessizce ezer. Tek kaynak: "
        f"`meridian/api.py::GUVENLIK_BASLIKLARI`.")


def test_CSP_politikasi_metni_yalniz_uygulamada_gecer():
    """Politika METNİNİN kendisi de ikinci bir yerde durmamalı — ad taraması bunu kaçırırdı.

    Bir yapılandırma başlığı adsız yazabilir (Lua `ngx.header`, bir `curl` örneği, bir birim
    dosyasının `Environment=` satırı). Ayrışmanın gerçekten sinsi hâli budur: adı aramakla
    bulunmaz, çünkü orada duran şey DEĞERDİR."""
    parca = "default-src 'self'"
    kirli = [p.relative_to(KOK) for p in _vekil_dosyalari()
             if parca in p.read_text(encoding="utf-8", errors="replace")]
    assert not kirli, f"CSP metni uygulama dışında da geçiyor: {kirli}"


def test_vekile_AIT_iki_kalem_ACIK_BORC_olarak_YAZILI():
    """`Strict-Transport-Security` ve `-Server` artık HİÇBİR dosyada tanımlı değil — ve bu
    olgunun kendisi yazılı durmak zorundadır (YASA 4: sessiz yutma yok).

    Eski çivi ikisinin vekilde AÇIK kaldığını ölçüyordu; vekil yapılandırması silinince o ölçüm
    de düştü. Beyanı ölçmeyi bırakırsak kayıp SESSİZ olur: bir gün TLS yeniden sonlandırılır,
    kimse HSTS'i hatırlamaz ve "eskiden vardı" cümlesi hiçbir yerde durmaz. Bu yüzden ölçülen
    şey artık DAVRANIŞ değil BORCUN KAYDI: api.py'nin güvenlik başlığı notu iki kalemi de ADIYLA
    anmak ve bugün nerede olduklarını söylemek zorunda."""
    kaynak = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")
    bas = kaynak.index("# ---- GÜVENLİK BAŞLIKLARI")
    not_metni = kaynak[bas:kaynak.index("CSP_POLITIKASI = (", bas)]
    for kalem in ("Strict-Transport-Security", "-Server"):
        assert kalem in not_metni, (
            f"`{kalem}` güvenlik başlığı notunda ARTIK anılmıyor. İkisi de hiçbir yapılandırmada "
            f"tanımlı değil; adları buradan da düşerse kayıt tamamen kaybolur.")
    assert "bedel yasası" in not_metni, (
        "kaybedilen ölçüm (vekil kopyasıyla dize eşitliği) notta beyan edilmemiş")
    assert "Strict-Transport-Security" not in GUVENLIK_BASLIKLARI, (
        "HSTS uygulama sözlüğüne SIZMIŞ — düz HTTP'de tarayıcı onu yok sayar (RFC 6797 §8.1)")


def test_CSP_DISI_iki_baslik_DEGERI_de_civili():
    """`Referrer-Policy` ve `Permissions-Policy` DEĞERLERİ bağımsız olarak çivilenir.

    ÜÇÜNCÜ KAYIP (tur-2'de ölçüldü; tur-1'in bedel beyanı iki kalem sayıyordu, üç olmalıydı).
    Silinen vekil kopyasıyla DİZE EŞİTLİĞİ çivisi BEŞ başlığın değerini sözlükten BAĞIMSIZ bir
    literale bağlıyordu. Yerine gelen Ç2 yalnız "ikinci tanım doğmasın" der (değer ölçmez) ve Ç1
    yanıtı `GUVENLIK_BASLIKLARI`nın KENDİSİYLE kıyaslar — değer sapması için totoloji. `X-Frame-Options`
    ("DENY") ve `X-Content-Type-Options` ("nosniff") başka testlerde bağımsız olarak hâlâ çivili;
    bu iki başlık ise ÖLÇÜLDÜ: `api.py` dışında hiçbir yerde geçmiyorlardı.

    NE OLURDU: biri `Referrer-Policy`yi `unsafe-url` yapsın — tam URL, sorgu dizesiyle birlikte
    üçüncü tarafa gider; ya da `Permissions-Policy` değerini boşaltsın — kamera/mikrofon/konum
    yetenekleri açılır. İkisinde de v203, v448, v201 ve test_web_csp_uyum dahil TÜM küme yeşil
    kalırdı. Değerler burada literal yazılıdır ve bu KOPYA DEĞİL ÇİVİDİR: sözlükten türetilseydi
    yine totoloji olurdu (bkz. yukarıdaki Ç1 notu)."""
    assert GUVENLIK_BASLIKLARI["Referrer-Policy"] == "no-referrer", (
        "Referrer-Policy gevşemiş — `no-referrer` dışındaki her değer yol adlarını (ve `unsafe-url` "
        "hâlinde tam URL'i) üçüncü tarafa sızdırır")
    izinler = dict(
        parca.strip().split("=", 1)
        for parca in GUVENLIK_BASLIKLARI["Permissions-Policy"].split(",")
    )
    assert set(izinler) == {"geolocation", "microphone", "camera", "payment", "usb"}, (
        f"Permissions-Policy direktif kümesi değişmiş: {sorted(izinler)} — panonun hiçbirine "
        f"ihtiyacı yok; bir direktifin DÜŞMESİ o yeteneği sessizce açar")
    acik = [ad for ad, deger in izinler.items() if deger != "()"]
    assert not acik, f"Permissions-Policy'de AÇIK bırakılmış yetenek(ler): {acik}"


def _rota_bloklari(routes: str) -> dict[str, str]:
    """`routes.yaml` → {rota kimliği: o rotanın gövdesi}. Kimlik TÜRETİLİR, elle yazılmaz."""
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"\n\s*- id: ", routes)[1:]}


def test_ingress_XFORWARDED_sozlesmesi_VEKIL_YAPILANDIRMASINDA_yazili():
    """DÖRDÜNCÜ KAYIP ve onun onarımı (tur-2): `X-Forwarded-Proto`/`-For` sözleşmesinin TEK kaydı
    silinen vekil yapılandırmasıydı; şimdi kayıt `deploy/apisix/routes.yaml` pano-ingress bloğunda.

    NEDEN GERÇEK BİR RİSK, düzyazı değil: `api._secure_cookie` oturum çerezinin `Secure` işaretini
    `x-forwarded-proto`dan okur — ingress o başlığı İLETMEZSE uygulama şemayı düz `http` görür ve
    çerez HTTPS altında `Secure`suz çıkar. `api._client_ip` ise hız sınırı anahtarını
    `x-forwarded-for`dan okur — iletilmezse tüm istekler tek vekil IP'sinde toplanır ve IP başına
    kilit anlamını yitirir. Eski kayıt vekil dosyasının `header_up` satırlarındaydı ve gerekçesi
    oracıkta yazılıydı; dosya gidince ölçüm de gitti (tur-1'in bedel beyanı bu kalemi saymadı).

    ÖLÇÜLEN ŞEY BEYANIN KENDİSİDİR, DAVRANIŞ DEĞİL — ve bu ayrım dürüstçe yazılmalı: APISIX'in bu
    başlıkları varsayılan olarak ekleyip eklemediği CANLIDA ÖLÇÜLMEDİ. O ölçüm yapılana kadar
    doğru duruş, yükümlülüğü vekil yapılandırmasının kendi dosyasında yazılı tutmaktır."""
    routes = (KOK / "deploy" / "apisix" / "routes.yaml").read_text(encoding="utf-8")
    bas = routes.index("- id: pano-ingress")
    blok = routes[bas:routes.index("- id: ", bas + 10)]
    for kalem in ("X-Forwarded-Proto", "X-Forwarded-For", "_secure_cookie", "_client_ip"):
        assert kalem in blok, (
            f"pano-ingress bloğu `{kalem}`i anmıyor — silinen vekil yapılandırmasının taşıdığı "
            f"yükümlülük yeni kaynağa TAŞINMAMIŞ demektir (bedel yasası)")
    assert "ölçülmedi" in blok or "ÖLÇÜLMEDİ" in blok, (
        "APISIX'in bu başlıkları varsayılan eklediği ÖLÇÜLMEDİ — beyan bu belirsizliği taşımak "
        "zorunda (uydurma yasağı)")
    # KARŞI-KANIT AYRIŞMASIN (tur-3): aynı dosyada XFF'i `proxy-rewrite` ile SİLEN rotalar var ve
    # "ölçülmedi" beyanı onları anmadan eksikti — ölçümü yapacak kişinin ilk kanıtı orası. Kural
    # tek yönlüdür ve TÜRETİLİR: silen HER rota şerhte ADIYLA anılmalı; yenisi doğarsa burası
    # kırmızı yanar ve beyan tazelenir (elle liste tutmak, listenin eskimesi demektir).
    kaldiran = sorted(rid for rid, govde in _rota_bloklari(routes).items()
                      if re.search(r"remove:\s*\[[^\]]*X-Forwarded-For", govde))
    assert kaldiran, (
        "hiçbir rota `X-Forwarded-For`u silmiyor — ya yapılandırma değişti ya da bu tarama "
        "kırıldı; iki hâlde de aşağıdaki iddia hiçbir şey ölçmeden geçerdi")
    eksik = [rid for rid in kaldiran if rid not in blok]
    assert not eksik, (
        f"XFF'i silen rota(lar) pano-ingress şerhinde ANILMIYOR: {eksik}. Şerh, ölçümü yapacak "
        f"kişiye aynı dosyadaki karşı-kanıtı göstermek zorunda (bedel yasası: kayıt tek yerde "
        f"tutuluyorsa eksik kayıt körlüktür).")
    cfg = (KOK / "deploy" / "apisix" / "config.yaml").read_text(encoding="utf-8")
    for ayar in ("real_ip", "trusted_addresses"):
        assert ayar not in cfg, (
            f"`config.yaml` artık `{ayar}` taşıyor — pano-ingress şerhinin 'böyle bir ayar YOK "
            f"(ölçüldü 2026-09-08)' cümlesi ARTIK YANLIŞ; şerh ölçümle birlikte güncellenmeli")

    api_src = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")
    for fn in ("def _secure_cookie", "def _client_ip"):
        govde = api_src[api_src.index(fn):]
        docstring = govde[:govde.index('"""', govde.index('"""') + 3)]
        assert "routes.yaml" in docstring, (
            f"`{fn}` docstring'i sözleşmenin KAYNAĞINI göstermiyor — okuyucu 'bu başlık nereden "
            f"geliyor, kim iletmek zorunda' sorusunu cevaplayamaz")


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
