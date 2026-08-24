"""FONT SUNUM ROTASI — `/fonts/*.woff2` (D5, 2026-08-07).

NİYE VAR. D4 turu yazı tipini kendi-barındırmaya aldı: iki `.woff2` `meridian/web/fonts/` altına
kondu, üç yüzeye yerel yollu `@font-face` yazıldı, ve `deploy/Caddyfile` CSP'sinden
`fonts.googleapis.com` + `fonts.gstatic.com` DÜŞTÜ. Yapılmayan tek şey rotaydı ve o eksik
ölçülmüştü: `/fonts/recursive-sans-vf.woff2` → 404, `/fonts/recursive-mono-vf.woff2` → 404
(tests/test_yazitipi_v201.py'nin KATI xfail'i). Bu depoda `StaticFiles` montajı BİLEREK yok
(`meridian/api.py`, "STATİK BETİKLER TEK TEK YÖNLENDİRİLİR" notu), yani bir dosyayı diske koymak
onu YAYINA ALMAZ.

BU DOSYANIN ÖLÇTÜĞÜ ÜÇ ŞEY, ve üçü de ayrı bir gerilemenin adı:

  1. **SUNULUYOR MU** — iki kesit 200, `font/woff2`, ve gövde diskteki baytların TA KENDİSİ.
     Kırılırsa: üç yüzey de sistem yüzüne düşer ve CSP `font-src 'self'` olduğu için
     "CDN'den gelsin" kaçışı da yoktur (ki olmaması bir sertleştirmedir, bir maliyet değil).
  2. **YALNIZ O İKİSİ Mİ** — izin listesi kaynakta LİTERALDİR. `fonts/` dizinine düşen başka
     hiçbir bayt (lisans metni, ölçüm turunun ara kesitleri, bir `.orig`) sunulmaz. Bu, montaj
     reddinin tek gerçek karşılığıdır: montaj olsaydı dizindeki her şey yayında olurdu.
  3. **ÖNBELLEK YASASI AYNI MI** — fontlar `immutable` DEĞİL, öteki varlıklarla aynı
     içerik-ETag + `no-cache` + 304 sözleşmesini okur. Gerekçe rotanın yanında yazılı: dosya
     adları sürümsüzdür, `immutable` bir sonraki yazı tipi turunu tarayıcıda bir yıl hapseder.

Ağ istemez, tarayıcı istemez — TestClient ile GERÇEK istek atılır.
"""
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from meridian.api import app

KOK = pathlib.Path(__file__).resolve().parents[1]
FONTLAR = KOK / "meridian" / "web" / "fonts"
API_PY = KOK / "meridian" / "api.py"

# 2026-08-24 · YAZI TİPİ DEVRALMA (docs/HUKUM-2026-08-24-YAZITIPI.md).
# `--sans` Inter oldu; `recursive-sans-vf.woff2` EMEKLİ ama LİSTEDE KALIR ve SUNULMAYA
# devam eder — silmek, eski önbelleklerden gelen istekleri 404'e düşürür ve tarihçe-koru
# ilkesini çiğner. Hiçbir yüzeyin onu ARTIK istemediği ayrı bir çividir
# (tests/test_yazitipi_v201.py::test_EMEKLI_sans_kesidi_HICBIR_YUZEYDE_istenmiyor); yani
# "sunuluyor" ile "yükleniyor" iki ayrı iddia ve ikisi de ayrı ölçülüyor.
# ~~Emekli liste: ["recursive-sans-vf.woff2", "recursive-mono-vf.woff2"]~~
SUNULAN = ["inter-vf.woff2", "recursive-sans-vf.woff2", "recursive-mono-vf.woff2"]


@pytest.fixture
def istemci(sandbox_state):
    """`sandbox_state` ZORUNLU: `TestClient(app)` uygulamayı AYAĞA KALDIRIR ve açılış yolu canlı
    `state/events.jsonl`e yazar. Fikstürsüz koşulduğunda conftest'in canlı-state bekçisi haklı
    olarak kırıyor — operatöre sunulan defter bir test artefaktı taşıyamaz."""
    with TestClient(app) as c:
        yield c


# ===================== Ç1 · SUNULUYOR MU =====================

@pytest.mark.parametrize("ad", SUNULAN)
def test_font_200_doner_ve_govde_DISKTEKI_BAYTLARIN_TA_KENDISI(istemci, ad):
    """200, ve gövde diskteki dosyanın birebir kopyası.

    `len(body) > 0` YETMEZ ve bu bilinçli: bir 404 gövdesi de sıfırdan uzundur, bir hata
    sayfası da. Ölçülen şey "bir şey döndü mü" değil, "DOĞRU BAYTLAR mı döndü" — çünkü
    yanlış baytlarla dönen bir yazı tipi rotası, tarayıcıda tam olarak rotanın hiç
    olmamasıyla aynı sonucu verir (yüz yüklenmez), ama testte yeşil yanar."""
    diskte = (FONTLAR / ad).read_bytes()
    r = istemci.get(f"/fonts/{ad}")
    assert r.status_code == 200, f"/fonts/{ad} → {r.status_code} (rota yok ya da dosya dağıtılmamış)"
    assert r.content == diskte, (
        f"/fonts/{ad}: gövde diskteki dosyayla aynı DEĞİL "
        f"({len(r.content)} bayt döndü, diskte {len(diskte)})")


@pytest.mark.parametrize("ad", SUNULAN)
def test_content_type_font_woff2(istemci, ad):
    """`Content-Type: font/woff2` — tahmine bırakılmaz.

    Bu başlık olmadan da çoğu tarayıcı yüzü çizer (`@font-face` `format('woff2')` diyor ve
    tarayıcı baytlara bakar), ama `application/octet-stream` ile dönen bir font ara katmanlarda
    ve sıkı yapılandırmalarda reddedilebilir. RFC 8081 bu tipi tanımlar; tahmin bir sözleşme
    değildir."""
    ct = istemci.get(f"/fonts/{ad}").headers.get("content-type", "")
    assert ct.split(";")[0].strip() == "font/woff2", f"/fonts/{ad}: content-type {ct!r}"


def test_iki_kesit_AYRI_dosyadir(istemci):
    """Sans ve mono AYNI baytları döndürmemeli.

    Recursive'de mono ayrı bir aile değil, AYNI değişken dosyanın `MONO 1` kesitidir — yani
    "iki rota da çalışıyor" derken ikisinin de aynı dosyaya bağlanmış olması sessiz ve çok
    kolay bir hatadır. Sonuç: pano tek yüzle çizilir, sayı sütunu ile metin ayırt edilemez
    hâle gelir, ve hiçbir test kırılmaz. Bu test onu kırar."""
    a = istemci.get(f"/fonts/{SUNULAN[0]}").content
    b = istemci.get(f"/fonts/{SUNULAN[1]}").content
    assert a != b, "iki font rotası AYNI baytları döndürüyor — biri yanlış dosyaya bağlı"


# ===================== Ç2 · YALNIZ O İKİSİ (dizin-dışı erişim) =====================

# Dizindeki GERÇEK ama sunulmaması gereken dosya. `OFL.txt` lisans metnidir ve `fonts/` altında
# durmak ZORUNDADIR (SIL OFL 1.1 §çoğaltma şartı) — yani "diskte var" ile "yayında" arasındaki
# farkın canlı örneği burada, aynı dizinde duruyor.
DIZINDE_AMA_SUNULMAZ = "OFL.txt"

DUSMANCA = [
    "../api.py",                    # klasik; httpx yolu normalize eder → /api.py, o da 404
    "..%2f..%2fapi.py",             # kodlanmış ayraç: normalizasyondan SAĞ çıkar
    "%2e%2e/api.py",                # kodlanmış nokta
    "....//api.py",                 # tek geçişli `..` temizleyicilerini atlatan biçim
    "/etc/passwd",                  # mutlak yol
    "..\\..\\api.py",               # ters bölü (Windows biçimi)
    "recursive-sans-vf.woff2.orig", # yedek/taslak — montaj olsaydı YAYINDA olurdu
    "recursive-sans-vf.woff2/",     # sondaki ayraç (starlette 307 ile kanonik ada yollar)
    "RECURSIVE-SANS-VF.WOFF2",      # büyük/küçük harf (macOS dosya sistemi harf-duyarsızdır)
    "recursive-sans-vf.woff2%00.txt",   # boş bayt
    DIZINDE_AMA_SUNULMAZ,
]


@pytest.mark.parametrize("yol", DUSMANCA)
def test_dizin_disi_erisim_REDDEDILIR(istemci, yol):
    """İzin listesi dışındaki hiçbir istek gövde alamaz.

    HÜKÜM 404'ÜN KENDİSİNDE DEĞİL, GÖVDENİN YOKLUĞUNDA: bazı biçimler rotaya hiç ulaşmaz
    (`{ad}` yol parametresi `/` ile eşleşmez, yani FastAPI'nin kendi 404'ü döner), bazıları
    rotaya ulaşıp izin listesinden döner. İkisi de doğru sonuçtur ve testin ayırt etmesi
    GEREKMEZ — ayırt etmeye kalksa, çerçevenin yönlendirme ayrıntısını sözleşmeye çevirirdi.

    YÖNLENDİRME TAKİP EDİLMEZ (`follow_redirects=False`) ve bu ÖLÇÜLMÜŞ bir ayrımdır: starlette
    `redirect_slashes` ile `…woff2/` isteğini 307'yle KANONİK ada yollar, httpx onu takip eder
    ve sonuç 200 görünür. O 200 bir sızıntı DEĞİL, izin verilen adın kendisidir — ama takip
    açıkken test bunu "izin listesi delindi"den ayırt EDEMEZ. Takip kapatılır ve yönlendirmenin
    hedefi ayrıca sınanır: bir 3xx de kaçak yolu olamaz."""
    r = istemci.get(f"/fonts/{yol}", follow_redirects=False)
    assert r.status_code != 200, (
        f"/fonts/{yol} → 200 ({len(r.content)} bayt). İzin listesi delinmiş: bu rota YALNIZ "
        f"kaynakta literal olarak sayılan iki adı sunmalı.")
    if 300 <= r.status_code < 400:
        hedef = r.headers.get("location", "")
        assert hedef.rsplit("/", 1)[-1] in SUNULAN, (
            f"/fonts/{yol} → {r.status_code} {hedef!r}: yönlendirme izin listesi DIŞINA "
            f"gidiyor — kaçak yolu bir yönlendirme olarak da açılamaz")


def test_dizindeki_GERCEK_dosya_bile_sunulmaz(istemci):
    """`OFL.txt` diskte VARDIR, okunabilirdir, ve yine de sunulmaz.

    Bu, montaj reddinin tek ölçülebilir karşılığıdır. Bir `StaticFiles` montajı bu dosyayı —
    ve dizine sonradan düşecek her baytı — sessizce yayına açardı. Test "dosya yok" diye
    değil, "bu ad sunulmuyor" diye geçmeli: dosyanın VARLIĞI önce doğrulanır, yoksa test
    kendi kendini boşa çıkarır."""
    assert (FONTLAR / DIZINDE_AMA_SUNULMAZ).is_file(), (
        f"{DIZINDE_AMA_SUNULMAZ} dizinde YOK — bu test bir şey ölçmüyor demektir "
        f"(ve SIL OFL 1.1 lisans metninin kopyalarla birlikte taşınması ayrıca zorunlu)")
    assert istemci.get(f"/fonts/{DIZINDE_AMA_SUNULMAZ}").status_code == 404


def test_izin_listesi_diskle_IKI_YONDE_de_ortusur(istemci):
    """Sunulan her ad diskte var; diskteki her `.woff2` sunuluyor.

    İKİ YÖN AYRI HATA: listede olup diskte olmayan bir ad = 404 (dağıtım eksiği, üç yüzey
    sistem yüzüne düşer). Diskte olup listede olmayan bir `.woff2` = ölü ağırlık — ya
    unutulmuş bir kesit ya da yayına alınması unutulmuş yeni bir yüz. İkincisi sessizdir,
    o yüzden ölçülür."""
    diskte = {p.name for p in FONTLAR.glob("*.woff2")}
    assert set(SUNULAN) <= diskte, f"listede olup diskte olmayan: {set(SUNULAN) - diskte}"
    assert diskte <= set(SUNULAN), (
        f"diskte olup sunulmayan .woff2: {diskte - set(SUNULAN)} — ya rotaya eklenmeli "
        f"ya dizinden silinmeli; sunulmayan bir font dosyası dağıtımda ölü ağırlıktır")


def test_api_pyde_StaticFiles_MONTAJI_YOK():
    """Montaj reddi bir yorum değil, bir ölçüm olmalı.

    Bu turun en olası "düzeltme"si `app.mount("/fonts", StaticFiles(...))` yazmaktı ve o,
    testleri de yeşil yakardı — ama depo sözleşmesini (yayına ne çıktığı kaynakta okunur)
    sessizce iptal ederdi. Kapı burada."""
    api = API_PY.read_text(encoding="utf-8")
    kod = re.sub(r"#.*", "", api)          # yorumlarda adı GEÇEBİLİR (gerekçe metni)
    kod = re.sub(r'"""(?:.|\n)*?"""', "", kod)
    assert "StaticFiles" not in kod, "api.py'ye StaticFiles montajı girmiş — ad-ad rotalama sözleşmesi bozuldu"
    assert ".mount(" not in kod, "api.py'de bir montaj var — WEB dizinine düşen her dosya yayına açılır"


# ===================== Ç3 · ÖNBELLEK YASASI ÖTEKİ VARLIKLARLA AYNI =====================

@pytest.mark.parametrize("ad", SUNULAN)
def test_icerik_ETagi_var_ve_If_None_Match_304_doner(istemci, ad):
    """Güçlü ETag + gövdesiz 304 — `/theme.js` ile AYNI yasa.

    Yazı tipleri bu deponun en ağır iki statik varlığıdır (toplam 79,3 KB, `preload`lı, üç
    yüzeyde de istenir). 304 yolu olmadan her doğrulama tam gövdeyi indirir; VE bu tam olarak
    `_statik`in var olma sebebi olan vakadır (app.js, 518 KB, her doğrulamada baştan)."""
    r1 = istemci.get(f"/fonts/{ad}")
    etag = r1.headers.get("etag")
    assert etag, f"/fonts/{ad}: ETag başlığı YOK — 304 pazarlığı yapılamaz"
    assert not etag.startswith("W/"), f"/fonts/{ad}: zayıf ETag ({etag}) — içerik özeti bekleniyordu"

    r2 = istemci.get(f"/fonts/{ad}", headers={"If-None-Match": etag})
    assert r2.status_code == 304, f"/fonts/{ad}: eşleşen ETag'e {r2.status_code} döndü, 304 bekleniyordu"
    assert r2.content == b"", "304 GÖVDESİZDİR (RFC 9110 §15.4.5)"

    # Eşleşmeyen etiket TAM gövde almalı — yoksa 304 yolu "her zaman 304" demek olurdu.
    r3 = istemci.get(f"/fonts/{ad}", headers={"If-None-Match": '"boyle-bir-etiket-yok"'})
    assert r3.status_code == 200 and r3.content == r1.content


@pytest.mark.parametrize("ad", SUNULAN)
def test_ETag_ICERIKTEN_turer_her_kesit_AYRI_etiket_tasir(istemci, ad):
    """Her dosya kendi etiketini taşır — etiket İÇERİĞİN özetidir, adın değil.

    ESKİ ADI: ..._iki_kesit_... (2026-08-07 → 2026-08-24). Sunulan kesit sayısı üçe çıktı
    (Inter geldi, emekli Recursive Sans sunulmaya devam ediyor) ve sabit `== 2` beklentisi
    sayıya çivilenmişti. Sayı bir ölçüt DEĞİL: iddia "ETag adı değil içeriği özetliyor"dur,
    yani kaç dosya olursa olsun HEPSİ ayrı etiket taşımalı. Sayıya çivili hâli, üçüncü
    dosya geldiğinde iddiayı değil sayımı kırdı."""
    etiketler = {a: istemci.get(f"/fonts/{a}").headers.get("etag") for a in SUNULAN}
    assert None not in etiketler.values(), f"ETag'siz kesit var: {etiketler}"
    assert len(set(etiketler.values())) == len(SUNULAN), (
        f"iki kesit AYNI ETag'i taşıyor — etiket içerikten türemiyor demektir: {etiketler}")


@pytest.mark.parametrize("ad", SUNULAN)
def test_Cache_Control_IMMUTABLE_DEGIL_yeniden_dogrulamali(istemci, ad):
    """`immutable` / uzun `max-age` YASAK — dosya adları SÜRÜMSÜZ.

    `immutable` ancak ad içeriği adresliyorsa (hash'li ad) doğrudur. Buradaki adlar sabittir
    (`recursive-sans-vf.woff2`), yani bir sonraki yazı tipi turu AYNI ADLA farklı bayt
    dağıtır. `max-age=31536000, immutable` o baytları tarayıcıda bir yıl ulaşılmaz kılardı:
    "dagit'ten sonra değişikliği göremedim" vakasının yazı tipi hâli, ve sert-yenileme bile
    `immutable`ı bazı tarayıcılarda delmez. Doğru olan ~0 baytlık doğrulama: no-cache + 304.

    HASH'Lİ AD GELİRSE bu test bilinçli olarak GÜNCELLENİR — o zaman `immutable` doğru cevap
    olur. Ölçülen şey "hangi başlık" değil, "ad ile içerik arasındaki sözleşme"dir."""
    cc = istemci.get(f"/fonts/{ad}").headers.get("cache-control", "")
    assert "immutable" not in cc, (
        f"/fonts/{ad}: Cache-Control `immutable` ({cc!r}) ama dosya adı sürümsüz — "
        f"bir sonraki yazı tipi turu tarayıcıda görünmez kalır")
    assert "no-cache" in cc, f"/fonts/{ad}: Cache-Control {cc!r} — yeniden-doğrulama sözleşmesi yok"
    # Öteki statik varlıklarla BİREBİR aynı olmalı: iki kaynak, zamanla ayrışan iki yasa.
    assert cc == istemci.get("/theme.js").headers.get("cache-control"), (
        f"/fonts/{ad} önbellek başlığı /theme.js'ten AYRI ({cc!r}) — statik varlıklar tek yasa okur")


# ===================== Ç4 · BİLDİRİM İLE SUNUM ÖRTÜŞÜR =====================

YUZEYLER = ["index.html", "landing.html", "workflow.html"]


@pytest.mark.parametrize("ad", YUZEYLER)
def test_yuzeyin_ISTEDIGI_her_font_GERCEKTEN_sunuluyor(istemci, ad):
    """`@font-face` ve `preload` yolları, rotanın fiilen sunduğu adlarla örtüşmeli.

    Bu, D4'ün açık kalan kaleminin tam ifadesidir: bildirim ile sunum AYRI iki yerde yazılır
    ve biri değişince öteki sessizce yalan söyler. Burada tarayıcının istediği HER yol
    gerçekten istenir ve 200 alması ölçülür — tahmin edilmez."""
    kaynak = (KOK / "meridian" / "web" / ad).read_text(encoding="utf-8")
    yollar = set(re.findall(r"['\"](/fonts/[^'\"]+)['\"]", kaynak))
    assert yollar, f"{ad}: hiç /fonts/ yolu yok — yüzey yazı tipini kendi-barındırmıyor"
    for y in sorted(yollar):
        assert istemci.get(y).status_code == 200, (
            f"{ad} `{y}` istiyor ama rota 200 döndürmüyor — sayfa sistem yüzüne düşer "
            f"(CSP `font-src 'self'` olduğu için CDN kaçışı da yok)")
