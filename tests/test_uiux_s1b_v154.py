"""v154 — UIUX S1 / AJAN-B: runbook yüzeyi (T3) · g-kısayolları + ? haritası (T4) · ekran-başına
soru cümlesi (T5).

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **hedefsiz işaret**. Üç biçimi vardı ve üçü de WP0'da ölçüldü:

  A) RUNBOOK YOK (borç #1, Nielsen İ9/şiddet 3) — pano "alarm → teşhis → runbook → çözüm"
     zincirinin son halkasını gösteremiyordu; palet bile 'runbook' komutunu /workflow'a
     bağlamak zorunda kalmıştı. Bir arayüzün var olmayan bir yere işaret etmesi, hiç işaret
     etmemekten kötüdür: operatör aramaya çıkar.
  B) KISAYOL HARİTASI EKSİK (İ6/şiddet 2) — `g d / g a / g r` iş emrinde vardı, panoda yoktu;
     üstelik en çok kullanılan kısayol (⌘K) haritada HİÇ yazmıyordu. Belgelenmemiş bir kısayol,
     olmayan bir kısayoldur.
  C) EKRANIN SORUSU YALNIZ YORUMDA — "her ekran tek soruya cevap verir" kuralı app.js'in
     tepesindeki bir yorumda yaşıyordu; kuralı uygulaması gereken kişi onu ekranda göremiyordu.

TESTLER KAYNAĞA BAKAR (repo deseni: v139/v151/v152). Bir alanın API'de var olması onun panoda
OKUNDUĞU anlamına gelmez; bu turun yarısı tam olarak o boşluğun kapatılmasıdır. Ayrıca üretici ↔
okuyucu PARİTELERİ zorlanır: runbook'un ürettiği çapa ile panonun kurduğu bağ aynı kuraldan
gelmelidir — iki slug kuralı doğarsa biri sessizce bayatlar ve bağlar ölü bağa döner.

YEREL SUNUCU KOŞULMAZ (CLAUDE.md §5): rota testleri FastAPI TestClient ile, ağsız.
"""
from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
PALETTE = (WEB / "palette.js").read_text()
RUNBOOK_HTML = (WEB / "runbook.html").read_text()
API_SRC = (SRC / "meridian" / "api.py").read_text()
URETICI_YOL = SRC / "ops" / "runbook_uret.py"
RUNBOOK_MD_YOL = SRC / "docs" / "RUNBOOK.md"

# Yorum satırları KURAL SAYILMAZ: bu turun her kararı gerekçesiyle yazıldı ("eski davranış
# şuydu, neden yanlıştı"). O gerekçe kaynakta durmalı ama "hâlâ orada" diye okunmamalı —
# yoksa doğru davranan bir düzeltme kendi belgesi yüzünden düşer (v139/v151'in aynı kuralı).
KOD_JS = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _uretici():
    """`ops/` bir paket DEĞİL (ve olmamalı: ops betikleri içe aktarılmak için değil koşulmak
    için var). Üreticiyi dosya yolundan yükleriz — testin üretim koduna erişimi, üretim kodunun
    paketlenme biçimini değiştirmeden sağlanır."""
    spec = importlib.util.spec_from_file_location("runbook_uret", URETICI_YOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


U = _uretici()
RUNBOOK_MD = RUNBOOK_MD_YOL.read_text() if RUNBOOK_MD_YOL.exists() else ""


# ==================================================================================
# T3-a — ÜRETİCİ: kaynaklardan bölüm üretimi
# ==================================================================================

def test_t3_uretici_deterministik():
    """Aynı kaynaktan aynı metin. Determinizm bir zarafet değil ÖLÇÜM ALETİDİR: belge zaman
    damgası taşısaydı `--kontrol` her koşuda 'bayat' derdi ve 'kodla ayrıştı mı' sorusu bir
    daha cevaplanamazdı."""
    assert U.uret() == U.uret()
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}", U.uret()), (
        "belgeye üretim ZAMAN DAMGASI sızmış — determinizm kırılır, --kontrol kapısı ölür")


def test_t3_diskteki_belge_kaynakla_ayrismamis():
    """`docs/RUNBOOK.md` üretilenle BİREBİR aynı olmalı.

    Bu testin kırılması bir hata DEĞİL bir HABERDİR: kaynak kod değişti (yeni alarm jetonu, yeni
    bekçi mekanizması, değişen betik başlığı) ve belge geride kaldı. Çözüm:
    `python ops/runbook_uret.py`. Elle düzeltme YAPILMAZ — bir sonraki üretimde silinir."""
    assert RUNBOOK_MD_YOL.exists(), "docs/RUNBOOK.md YOK — `python ops/runbook_uret.py` koş"
    assert RUNBOOK_MD == U.uret(), (
        "docs/RUNBOOK.md kaynak koddan geride kalmış — `python ops/runbook_uret.py` ile yeniden üret")


def _capalar() -> set[str]:
    return set(re.findall(r"\{#([^}]+)\}", RUNBOOK_MD))


def test_t3_her_alarm_jetonu_bolum_almis():
    """`obs.py`'deki her ALARM_ sabiti runbook'ta bir bölüm. Jeton listesi ELLE tutulmaz —
    `obs.NOTIFY_TOKENS` de aynı sabitlerden türer; üçüncü bir elle liste doğurmayız."""
    jetonlar = [a["jeton"] for a in U.alarm_envanteri()]
    assert len(jetonlar) >= 12, f"alarm envanteri şüpheli derecede küçük: {jetonlar}"
    capalar = _capalar()
    eksik = [j for j in jetonlar if j.lower() not in capalar]
    assert not eksik, f"runbook'ta bölümü olmayan alarm jetonu: {eksik}"


def test_t3_her_bekci_mekanizmasi_bolum_almis():
    """`watchdog.EXPECTED`'deki her mekanizma bir bölüm ÇAPASI (brief: bekçi mekanizma adları
    bölüm çapası olur). Sessiz hat sapan mekanizmanın ADINI verir; bağ o adla kurulur."""
    adlar = [m["ad"] for m in U.mekanizma_envanteri()]
    assert len(adlar) >= 17, f"bekçi envanteri şüpheli derecede küçük: {adlar}"
    capalar = _capalar()
    eksik = [a for a in adlar if a not in capalar]
    assert not eksik, f"runbook'ta bölümü olmayan bekçi mekanizması: {eksik}"


def test_t3_her_sessizhat_sapmasi_bolum_almis():
    """Kilit kolları ve veri sapmaları (soft_halt · halt_learning · devre_kesici · nabız ·
    veri_kalitesi) da bağ hedefidir — bekçi segmenti tek sapma türü değildir."""
    sapmalar, _ = U.sessizhat_envanteri()
    adlar = [s["ad"] for s in sapmalar]
    assert {"soft_halt", "halt_learning"} <= set(adlar), f"kilit kolları okunamadı: {adlar}"
    capalar = _capalar()
    eksik = [a for a in adlar if a not in capalar]
    assert not eksik, f"runbook'ta bölümü olmayan sessiz-hat sapması: {eksik}"


def test_t3_mekanizma_pencereleri_hesaplanmis():
    """`30 * 60` ifadesi 1800 olarak okunmalı. Metinden okusaydık belgede '30 sn' yazardı —
    yani operatöre yanlış bir eşik. Bir runbook'un yanlış eşiği, eşiği hiç yazmamaktan kötüdür."""
    m = {x["ad"]: x["pencere_s"] for x in U.mekanizma_envanteri()}
    assert m["scheduler_poll"] == 1800, m["scheduler_poll"]
    assert m["warmup_sprint"] == 8 * 3600, m["warmup_sprint"]
    assert "30 dk" in RUNBOOK_MD and "8 sa" in RUNBOOK_MD


def test_t3_nabiz_yerleri_koddan_turer():
    """Her mekanizmanın `beat()` çağrısı runbook'ta gösterilmeli — 'mekanizma sustu' alarmının
    ilk teşhis sorusu 'nabzı KİM atıyor' olduğu için bu, belgenin en değerli satırıdır."""
    nabizlar = U.nabiz_yerleri()
    adlar = [m["ad"] for m in U.mekanizma_envanteri()]
    yok = [a for a in adlar if a not in nabizlar]
    assert not yok, (f"EXPECTED'de beklenen ama `beat()` çağrısı OLMAYAN mekanizma: {yok} — "
                     "bu bekçinin kör noktasıdır; runbook onu bulgu olarak yazar ama test de görsün")
    assert "meridian/scheduler.py:" in RUNBOOK_MD


# ==================================================================================
# T3-b — UYDURMA YASAĞI ÇİVİSİ
# ==================================================================================

def test_t3_uydurma_yok_civisi_sentinel_ifadesi():
    """Kaynağı olmayan alan SUSMAZ, adını söyler. Sentinel dizge hem üreticide hem okuyucuda
    (api.py) AYNI olmalı: ayrışırsa pano işareti sessizce sönerdi — eksik girdiler çözülmüş
    girdilerle aynı tonda görünürdü."""
    assert U.YAZILMADI == "runbook girdisi henüz yazılmadı"
    assert f'_RUNBOOK_YAZILMADI = "{U.YAZILMADI}"' in API_SRC, (
        "api.py'deki sentinel üreticininkiyle ayrışmış — /runbook'ta 'yazılmadı' işareti sönük kalır")
    assert U.YAZILMADI in RUNBOOK_MD, "hiçbir alan boş çıkmamış — sentinel yolu ölü olabilir"


def test_t3_betik_iddiasi_dogrulanabilir():
    """HER betik-eşleşme iddiası DOĞRU olmalı — iki kanıt biçiminde de.

    Bu, uydurma yasağının bu dosyadaki en sert biçimi: belge bir betiği bir alarma bağladığında
    o bağın kanıtı DOSYANIN KENDİSİNDE durmalı. Bulanık/anlamsal eşleştirme yapılsaydı bu test
    yazılamazdı — ve yazılamayan bir iddia, denetlenemeyen bir iddiadır. İki kanıt biçimi:
      (a) BAŞLIK: “`X.sh` — başlığında `Y` geçiyor” → jeton betiğin başlık yorumunda durmalı.
      (b) GÖVDE (seçenek C): “`X.sh` — gövdesinde `obs.alarm('Y')` ateşliyor” → betik gerçekten
          o jetonu GÖVDESİNDE (yorum-dışı satırda) ateşlemeli; yoksa uydurma bir KURTARMA
          YÖNETİCİSİDİR. Betik ÜRETİCİDEN BAĞIMSIZ yeniden okunur ki test üreticinin değil
          dosyanın kanıtını görsün."""
    basliklar = {b["yol"]: b["baslik"] for b in U.betik_basliklari()}
    iddialar = re.findall(r"`([^`]+\.sh)` — başlığında `([^`]+)` geçiyor\.", RUNBOOK_MD)
    for yol, ad in iddialar:
        assert yol in basliklar, f"belge var olmayan bir betiğe işaret ediyor: {yol}"
        assert ad in basliklar[yol], f"YANLIŞ İDDİA: `{ad}` {yol} başlığında geçmiyor"

    govde_iddialar = re.findall(
        r"`([^`]+\.sh)` — gövdesinde `obs\.alarm\('([A-Z_0-9]+)'\)` ateşliyor", RUNBOOK_MD)
    for yol, jeton in govde_iddialar:
        assert yol in basliklar, f"belge var olmayan bir betiğe işaret ediyor: {yol}"
        satirlar = (SRC / yol).read_text().splitlines()
        gercek = any(re.search(rf"obs\.alarm\(\s*['\"]{re.escape(jeton)}['\"]", s)
                     for s in satirlar if not s.lstrip().startswith("#"))
        assert gercek, f"UYDURMA KURTARMA YÖNETİCİSİ: {yol} gövdesinde `obs.alarm('{jeton}')` YOK"


def test_t3_govde_atesleme_kurtarma_yoneticisini_eslestirir():
    """Seçenek C: bir betik GÖVDESİNDE `obs.alarm('JETON')` ateşliyorsa o betik jetonun
    KURTARMA YÖNETİCİSİ olarak Çözüm/betik alanına girer — başlıkta ad geçmese BİLE.

    ÇİVİLİ GERÇEK BAĞ: `ops/keepalive.sh` gövdesinde `obs.alarm('MECHANISM_STALE')` ateşler
    (ölü sunucuyu diriltir) ama BAŞLIĞINDA 'MECHANISM_STALE' GEÇMEZ. Yani yalnız başlık
    taransaydı bu bağ görünmez, MECHANISM_STALE'in Çözüm alanı boş kalırdı (WP0 borcu). Gövde
    boyutu tam olarak bu boşluğu GERÇEK bir kaynaktan kapatır; test hem bağı hem 'başlıkta
    geçmiyor' farkını çivi haline getirir — fark olmasaydı gövde boyutu gereksiz olurdu."""
    govde = U.betik_govde_atesleme()
    assert "MECHANISM_STALE" in govde, "gövde ateşleme taraması MECHANISM_STALE'i bulmadı"
    yollar = {a["yol"] for a in govde["MECHANISM_STALE"]}
    assert "ops/keepalive.sh" in yollar, f"keepalive.sh gövde bağı yok: {yollar}"

    basliklar = {b["yol"]: b["baslik"] for b in U.betik_basliklari()}
    assert "MECHANISM_STALE" not in basliklar["ops/keepalive.sh"], (
        "keepalive.sh başlığında MECHANISM_STALE geçiyor — bu vakada gövde boyutu gereksiz olurdu; "
        "testin var oluş sebebi tam olarak başlık↔gövde farkıdır")

    # MECHANISM_STALE'in Çözüm/betik alanı ARTIK boş değil.
    sec = RUNBOOK_MD[RUNBOOK_MD.index("## MECHANISM_STALE {#mechanism_stale}"):]
    sec = sec[:sec.index("\n## ", 1)]
    cozum = sec[sec.index("### Çözüm / betik"):]
    assert "`ops/keepalive.sh` — gövdesinde `obs.alarm('MECHANISM_STALE')` ateşliyor" in cozum, (
        "keepalive.sh MECHANISM_STALE Çözüm alanına girmemiş")
    assert U.YAZILMADI not in cozum, "MECHANISM_STALE Çözüm alanı hâlâ 'yazılmadı' diyor"


def test_t3_kapsam_disi_kaynak_sizmamis():
    """Onaylı küme `ops/*.sh` + `deploy/oracle-a1/*.sh`. Üst düzey `deploy/*.sh` (monitoring.sh
    dahil) BİLEREK dışarıda ve sınır belgede yazılı. Sessiz bir kapsam genişlemesi, 'runbook'un
    kaynağı ne' sorusunu bir daha cevaplanamaz kılardı."""
    yollar = [b["yol"] for b in U.betik_basliklari()]
    assert yollar, "hiç betik okunamadı — kaynak kümesi kırılmış"
    for y in yollar:
        assert y.startswith("ops/") or y.startswith("deploy/oracle-a1/"), f"kapsam dışı betik: {y}"
    # SINIR "BÖLÜM AÇMA"DIR, "ADI HİÇ GEÇMESİN" DEĞİL: `deploy/monitoring.sh` adı belgede
    # geçiyor çünkü `obs.py`'nin KENDİ yorumu ondan söz ediyor ("Tokens matched by
    # deploy/monitoring.sh log filters") ve o yorum onaylı bir kaynaktan ALINTIDIR. Alıntıyı
    # sansürlemek, kaynağı sadakatsizce aktarmak olurdu. Ölçülen şey: o betikten İÇERİK
    # çekilmemiş, yani ne bölümü ne de "başlığında geçiyor" iddiası var.
    bolum_yollari = set(re.findall(r"^## `([^`]+)` \{#", RUNBOOK_MD, re.M))
    assert bolum_yollari == set(yollar), f"betik bölümleri kaynak kümesiyle ayrışmış: {bolum_yollari ^ set(yollar)}"
    assert not re.search(r"`deploy/(?!oracle-a1/)[^`]+\.sh` — başlığında", RUNBOOK_MD), (
        "kapsam dışı bir betikten içerik iddiası üretilmiş")
    # Gövde boyutu (seçenek C) da aynı kapsamla sınırlı: kapsam dışı bir betikten gövde-ateşleme
    # iddiası da üretilmemeli — betik_govde_atesleme yalnız BETIK_KUMESI'ni tarar.
    assert not re.search(r"`deploy/(?!oracle-a1/)[^`]+\.sh` — gövdesinde", RUNBOOK_MD), (
        "kapsam dışı bir betikten gövde-ateşleme iddiası üretilmiş")
    assert "Kapsam dışı, bilerek" in RUNBOOK_MD, "kapsam sınırı belgede beyan edilmemiş"


def test_t3_eslestirme_kurali_belgede_yazili():
    """Kural okunabilir olmalı: okuyucu 'bu satır neden burada' sorusunu belgeden cevaplayabilsin."""
    assert "LİTERAL AD GEÇİŞİ" in RUNBOOK_MD
    assert "ÜRETİLMİŞ DOSYA" in RUNBOOK_MD and "ops/runbook_uret.py" in RUNBOOK_MD


def test_t3_gunluk_maddeleri_okunmus():
    """Mühendislik günlüğünün üç bölümü gerçekten taşınmış olmalı — kaynak sözleşmesinin
    ikinci maddesi 'okunuyor' diye yazılıp okunmadan kalabilirdi."""
    maddeler = U.log_maddeleri()
    assert len(maddeler) >= 10, f"günlükten yalnız {len(maddeler)} madde okundu"
    bolumler = {m["bolum"].split(" ")[0] for m in maddeler}
    assert len(bolumler) >= 3, f"üç bölümün hepsi okunamamış: {bolumler}"


# ==================================================================================
# T3-c — ROTA / SAYFA
# ==================================================================================

def test_t3_rota_yetki_istiyor():
    """`/runbook` `_auth` ÇAĞIRMAK ZORUNDA. Runbook mekanizma adlarını, betik başlıklarını ve
    açık-kalanları taşır — sistemin iç haritasıdır; `/landing`/`/workflow` gibi genel bir
    anlatım yüzeyi DEĞİLDİR. (Aynı kural `test_api_audit_v21::test_p1c` tarafından da
    dolaylı olarak zorlanır: yetkisiz GET izin listesinde `/runbook` yok.)"""
    m = re.search(r'@app\.get\("/runbook".*?\ndef runbook\(request: Request\):(.*?)\n@app\.',
                  API_SRC, re.S)
    assert m, "/runbook rotası bulunamadı"
    assert "_auth(request)" in m.group(1), "/runbook YETKİSİZ — iç harita açık yüzeye çıkmış"


def test_t3_yer_tutucular_duruyor():
    """Kabuk sayfanın yer tutucuları sözleşmedir; kaybolurlarsa sayfa BOŞ çizilirdi."""
    for yt in ("<!--RUNBOOK-GOVDE-->", "<!--RUNBOOK-TOC-->"):
        assert yt in RUNBOOK_HTML, f"runbook.html yer tutucusunu kaybetmiş: {yt}"
    assert 'runbook.html").read_text' in API_SRC


@pytest.mark.parametrize("desen,aciklama", [
    (r'\son[a-z]+\s*=\s*["\']', "satır içi olay özniteliği"),
    (r"<script(?![^>]*\ssrc=)[^>]*>", "gövdeli <script>"),
    (r"\beval\s*\(", "eval()"),
])
def test_t3_runbook_html_csp_uyumlu(desen, aciklama):
    """Dağıtım CSP'si `script-src 'self'`. Bu sayfa zaten SIFIR JS ile tasarlandı; test o
    kararı çivi haline getirir — yarın bir 'küçük' satır içi işleyici eklenirse burada durur.
    (`test_web_csp_uyum.py` yüzey listesini ayrı tutar; yeni sayfa oraya girene kadar
    korumasız kalmasın diye kural burada da duruyor.)"""
    assert not re.search(desen, RUNBOOK_HTML), f"runbook.html içinde {aciklama} var — CSP bloklar"


def test_t3_sayfa_disa_bagimli_degil():
    """Dış font/CDN yok: olay anında, SSH tüneli arkasında, ağ yokken de açılmalı."""
    assert "https://" not in RUNBOOK_HTML, "runbook.html dışarı bağlanıyor — olay anında açılmayabilir"


@pytest.fixture
def istemci(monkeypatch):
    """Yetki kapısı BİLEREK açılır (token yok + parola kurulu değil → `_auth` no-op).
    Burada ölçülen şey yetki değil RENDER — yetki kuralı yukarıda kaynaktan çivilendi."""
    from fastapi.testclient import TestClient
    from meridian import api, auth
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    monkeypatch.setattr(auth, "password_set", lambda: False)
    return TestClient(api.app), api


def test_t3_rota_cizer_ve_capalari_html_id_yapar(istemci):
    c, api = istemci
    r = c.get("/runbook")
    assert r.status_code == 200, r.text[:300]
    g = r.text
    assert "<!--RUNBOOK-GOVDE-->" not in g and "<!--RUNBOOK-TOC-->" not in g, "yer tutucu tüketilmemiş"
    # Çapa → HTML id pariteси: belgedeki her `{#x}` sayfada `id="x"` olmalı, yoksa pano bağı
    # sayfaya varır ama BÖLÜME varmaz — operatör 900 satırın tepesine düşer.
    for capa in sorted(_capalar()):
        assert f'id="{capa}"' in g, f"çapa HTML id'ye dönüşmemiş: {capa}"
    # "yazılmadı" İŞARETİ (WP-P 2026-08-12 güncellemesi): eski assert canlı belgede HER ZAMAN en az
    # bir boş girdi varsayıyordu — içerik borcu kapanınca (Çözüm boşları 16→0) o varsayım yanlış
    # oldu ve test, runbook'u TAMAMLAMAYI cezalandırır hale geldi. Ölçülen şey RENDER YETENEĞİDİR,
    # belgenin sonsuza dek eksik kalması değil: yetenek üreticinin sentineliyle doğrudan sınanır,
    # canlı belgede sentinel MADDESİ varsa sayfada da renkli görünmek zorundadır (iki yön de korunur).
    yetenek, _ = api._md_render(f"- x **{U.YAZILMADI}** y")
    assert 'class="yok"' in yetenek, "'yazılmadı' işareti render yolunda sönük — api._md_render kuralı kaybolmuş"
    if any(l.startswith(("- ", "  - ")) and U.YAZILMADI in l for l in RUNBOOK_MD.splitlines()):
        assert 'class="yok"' in g, "belgede 'yazılmadı' maddesi var ama sayfada sönük kalmış"
    assert "<nav class=\"toc\"" in g and g.count("<li") > 20, "içindekiler üretilmemiş"


def test_t3_belge_yoksa_sessiz_bos_sayfa_yok(istemci, monkeypatch):
    """Boş bir runbook, olay anında en kötü yalandır: 'bakacak bir şey yok' der."""
    c, api = istemci
    monkeypatch.setattr(api, "RUNBOOK_MD", SRC / "docs" / "OLMAYAN-RUNBOOK.md")
    r = c.get("/runbook")
    assert r.status_code == 503
    assert "ops/runbook_uret.py" in r.text, "hata mesajı ÇÖZÜMÜ söylemiyor"


def test_t3_md_render_kacis_yapar():
    """Ayrıştırıcı HTML kaçışı yapmalı: belge üretilmiş olsa da kaçışsız bir render, yarın
    başka bir kaynağa bağlandığında sessiz bir enjeksiyon yüzeyi olurdu."""
    from meridian import api
    govde, _ = api._md_render("## <script>x</script> {#t}\n\n- `<b>` ve **kalın**\n")
    assert "<script>" not in govde and "&lt;script&gt;" in govde
    assert "<code>&lt;b&gt;</code>" in govde and "<strong>kalın</strong>" in govde


# ==================================================================================
# T3-d — ALARM → TEŞHİS BAĞI (pano tarafı)
# ----------------------------------------------------------------------------------
# ÇİVİ TAŞINDI (D2-b, 2026-08-07): bağın HEDEFİ değişti, VARLIĞI değil. `runbookHref`/
# `runbookLink` `/runbook#<ad>` üretiyordu ve o sayfa panoya EMİLDİ (olay yüzeyleri).
# Kural aynı kuraldır ve bir kademe SERTLEŞTİ: eskiden bağ panoyu terk edebiliyordu,
# artık edemez. Ölçülen üç şey de yerinde: (1) iki tüketici de bağlı, (2) bağ <button>'ın
# İÇİNE girmiyor, (3) ad → sınıf çözümlemesi TEK yerde ve dönüşümsüz.
# ==================================================================================

def test_t3_pano_bag_yardimcilari_var():
    assert "function olayBagi(" in KOD_JS and "function olaySinifi(" in KOD_JS
    assert "const OLAY_YUZEYLERI = {" in KOD_JS, "olay yüzeyi kayıt defteri yok"
    assert "function runbookHref(" not in KOD_JS and "function runbookLink(" not in KOD_JS, \
        "emekli edilen runbook bağı hâlâ kodda — okuyucusu kalmamış yazım (YASA 6)"
    assert '"/runbook#"' not in KOD_JS, "pano hâlâ terk edilen yüzeye bağ kuruyor"


def test_t3_alarm_satiri_ve_sessizhat_bagli():
    """İKİ TÜKETİCİ DE BAĞLI OLMALI (brief: alarm satırları + sessiz-hat sapma satırları)."""
    alarm = KOD_JS[KOD_JS.index("function alertsInbox("):]
    alarm = alarm[:alarm.index("window.ackAlerts")]
    assert "olayBagi(g.token)" in alarm, "alarm satırında teşhis bağı yok"

    sh = KOD_JS[KOD_JS.index("function sessizHat("):]
    sh = sh[:sh.index("function alarmButce(")]
    assert "olayBagi(x.ad" in sh, "sessiz-hat sapma satırında teşhis bağı yok"
    assert "s.ad" in sh, "sessiz-hat bağı SEGMENTİ geçirmiyor — sınıf çözümlemesi yarım kalır"


def test_t3_alarm_bagi_butonun_icine_girmemis():
    """Bağ bir `<button>`dır ve iç içe düğme de geçersizdir: satırın kendisi zaten bir
    `<button>` (kaydı açar). Bağ satırın YANINA konur, İÇİNE değil."""
    alarm = KOD_JS[KOD_JS.index("function alertsInbox("):]
    alarm = alarm[:alarm.index("window.ackAlerts")]
    m = re.search(r"const rows = groups\.map\(\(?g[^)]*\)? => \{(.*?)\}\)\.join", alarm, re.S)
    assert m, "alarm satırı üretici bloğu bulunamadı — testin çıpası kaynakla ayrışmış"
    satir = m.group(1)
    govde = satir[satir.index("return"):]
    assert govde.index("</button>") < govde.index("olayBagi("), (
        "teşhis bağı <button> KAPANMADAN önce yerleştirilmiş — iç içe etkileşimli öğe")


def test_t3_capa_kurali_tek_ve_donusumsuz():
    """Ad → sınıf çözümlemesi TEK yerde ve DÖNÜŞÜMSÜZ: jeton adı yalnız büyük harfe çevrilir,
    slug'lanmaz. İkinci bir kural doğsaydı üreticinin adlarıyla ayrışır ve bağlar sessizce
    yanlış yüzey açardı — yanlış bir olay yüzeyi ölü bağdan pahalıdır."""
    fn = KOD_JS[KOD_JS.index("function olaySinifi("):]
    fn = fn[:fn.index("function olayYuzeyiHTML(")]
    assert ".toUpperCase()" in fn
    assert "replace(" not in fn, "çözümlemeye bir dönüşüm sızmış — üreticiyle ayrışır"
    assert "return null;" in fn, "eşleşmeyen ad sessizce bir yüzeye atanıyor olabilir"

    # PARİTE: `obs.py`nin ürettiği HER alarm jetonunun bir olay yüzeyi sınıfı OLMALI.
    # Eskiden bu parite "runbook belgesinde bir çapa var mı?" diye ölçülüyordu; artık
    # "panoda bir yüzeyi var mı?" diye ölçülür — aynı kusur sınıfı, daha yakın hedef.
    blok = re.search(r"const OLAY_YUZEYLERI = \{(.*?)\n\};", KOD_JS, re.S)
    assert blok, "OLAY_YUZEYLERI tanımlı değil"
    kapsanan = set()
    for dizi in re.findall(r"jetonlar:\s*\[([^\]]*)\]", blok.group(1)):
        kapsanan |= set(re.findall(r'"([A-Z_]+)"', dizi))
    jetonlar = {a["jeton"] for a in U.alarm_envanteri()}
    assert not (jetonlar - kapsanan), \
        f"olay yüzeyi OLMAYAN alarm jeton(lar)ı: {sorted(jetonlar - kapsanan)}"
    assert not (kapsanan - jetonlar), \
        f"var olmayan jetona yüzey açılmış: {sorted(kapsanan - jetonlar)}"


def test_t3_palet_runbook_komutu_gercek_hedefe_gidiyor():
    """Palet 'runbook' komutu artık /workflow'a değil /runbook'a gider ve iki komut ayrıştı."""
    assert 'id: "yrd:runbook"' in PALETTE
    rb = PALETTE[PALETTE.index('id: "yrd:runbook"'):]
    rb = rb[:rb.index('id: "yrd:workflow"')]
    assert 'location.href = "/runbook"' in rb
    assert '"runbook"' in rb, "arama anahtarı 'runbook' kaybolmuş"
    wf = PALETTE[PALETTE.index('id: "yrd:workflow"'):]
    wf = wf[:wf.index("K.push({", 10)] if "K.push({" in wf[10:] else wf[:400]
    assert "runbook" not in wf.lower(), (
        "workflow komutu hâlâ 'runbook' diyor — iki komut aynı kelimeyi kapışırsa palet yanlış "
        "yüzeye götürür (bu satırın var oluş sebebi tam olarak buydu)")


# ==================================================================================
# T4 — g-KISAYOLLARI + ? HARİTASI
# ==================================================================================

def test_t4_g_esleme_tum_gorunumleri_kapsar():
    """Dördünü bağlayıp üçünü dışarıda bırakmak, 'hangileri var' sorusunu her seferinde
    deneyerek cevaplatırdı — kısayolun amacı tam da bunu bitirmek."""
    blok = re.search(r"const GIT_KISAYOL = \{(.*?)\};", KOD_JS, re.S)
    assert blok, "GIT_KISAYOL tanımlı değil"
    esleme = dict(re.findall(r"(\w+):\s*\"(\w+)\"", blok.group(1)))
    views = dict(re.findall(r'\["(\w+)", "([^"]+)"\]', re.search(
        r"const VIEWS = \[(.*?)\];", KOD_JS, re.S).group(1)))
    assert set(esleme.values()) == set(views), (
        f"g-eşlemesi VIEWS ile ayrışmış: {sorted(set(esleme.values()) ^ set(views))}")
    # İş emrinin adlandırdığı üçlü + açılış sayfası — bunlar sözleşmedir.
    #
    # ÇİVİ TAŞINDI (S2R-1, 2026-08-02): eski hedefler (market/operasyon/ajan/brifing) artık
    # SAYFA DEĞİL, alan sayfalarının altındaki bölümler. Sözleşmenin KENDİSİ değişmedi — iş
    # emrinin `g d`/`g a`/`g r` üçlüsü hâlâ veri/alarm/araştırma yüzeylerine bağlı; yeni IA'da
    # o yüzeylerin adları kelimenin tam anlamıyla "Veri Sağlığı", "Gözetim & Alarmlar" ve
    # "Öğrenme" oldu, yani harf ile hedef arasındaki bağ artık bir yorum satırı okumadan kuruluyor.
    # 'b' (Bugün) yerini 'g' (Genel Bakış) aldı: açılış sayfası odur.
    # ÇİVİ TAŞINDI (D2-b, 2026-08-07): iş emrinin veri/alarm/araştırma üçlüsünün YÜZEYLERİ
    # birleşti — veri ve alarm artık tek yüzeydir (③ Sağlık) ve araştırma ④ Öğrenme'dir.
    # Sözleşmenin kendisi değişmedi: her yüzeyin harfi KENDİ ADINDAN gelir, bir yorum satırı
    # okumadan kurulabilir. 'b' açılış yüzeyi (① Bugün), 's' sağlık, 'o' öğrenme, 'k' karar.
    for tus, hedef in (("b", "bugun"), ("k", "karar"), ("s", "saglik"),
                       ("o", "ogrenme"), ("y", "kilitler")):
        assert esleme.get(tus) == hedef, f"g {tus} → {esleme.get(tus)} (beklenen {hedef})"


def test_t4_meta_erken_donus_bozulmamis():
    """ÇİVİLİ SATIR (test_pano_palet_v152::test_c4 ile aynı yasa): ⌘K/Ctrl+K panonun tek-tuş
    kısayollarını ateşlememeli. g-öneki bu satırın ALTINA girer — üstüne girseydi ⌘G gibi bir
    tarayıcı kısayolu paneli kaçırırdı."""
    h = KOD_JS[KOD_JS.rindex('addEventListener("keydown"'):]
    assert re.search(r'addEventListener\("keydown", e => \{\s*\n\s*if \(e\.metaKey \|\| e\.ctrlKey \|\| e\.altKey\) return;', h), (
        "meta/ctrl/alt erken dönüşü keydown dinleyicisinin İLK satırı değil")
    assert h.index("e.metaKey") < h.index("_gOnekTs"), "g-öneki meta erken-dönüşünün ÜSTÜNE girmiş"


def test_t4_g_oneki_satir_gezinmesinden_once_cozulur():
    """`g k` beklerken `k`nin satır gezinmesine düşmesi, iki tuşluk bir niyetin ortasında
    başka bir eylem yapmak olurdu. Önek kipi HER ŞEYDEN ÖNCE çözülür."""
    h = KOD_JS[KOD_JS.rindex('addEventListener("keydown"'):]
    assert h.index("_gOnekTs") < h.index('e.key === "j"'), "g-öneki j/k gezinmesinden SONRA çözülüyor"
    assert h.index("_gOnekTs") < h.index('e.key === "?"'), "g-öneki '?' panelinden SONRA çözülüyor"


def test_t4_g_oneki_zaman_asimli_ve_iptal_edilebilir():
    """Yarım bırakılmış bir `g`, dakikalar sonra basılan `r`yi sayfa atlamasına çevirmemeli."""
    assert re.search(r"const G_PENCERE_MS = \d+;", KOD_JS), "önek penceresi tanımsız — süresiz kip"
    h = KOD_JS[KOD_JS.rindex('addEventListener("keydown"'):]
    assert re.search(r'if \(e\.key === "Escape"\) \{ _gOnekTs = 0;', h), "Esc yarım öneki iptal etmiyor"
    assert "Date.now() - _gOnekTs < G_PENCERE_MS" in h, "pencere kontrolü yok"


def test_t4_harita_g_tuslarini_yaziyor():
    """Belgelenmemiş bir kısayol, olmayan bir kısayoldur (İ6). Harita VIEWS'ten TÜRER —
    iki liste elle tutulsaydı yine kayarlardı (2026-07-27'de tam olarak bu olmuştu)."""
    assert "const PAGE_MAP = VIEWS.map(" in KOD_JS
    assert "_gTusu(id)" in KOD_JS, "g tuşu haritaya VIEWS'ten türetilmiyor"
    ov = KOD_JS[KOD_JS.index("function kbdOverlay("):]
    ov = ov[:ov.index("window.kbdOverlay")]
    assert "PAGE_MAP.map(([k, n, d, g])" in ov, "harita 4. sütunu (g tuşu) çizmiyor"
    for beklenen in ("⌘K", "Sayfa atlama öneki", "Esc"):
        assert beklenen in ov, f"kısayol haritasında eksik: {beklenen}"
    assert "olay yüzeyi" in ov, "harita olay yüzeylerini duyurmuyor"
    assert "/runbook" not in ov, "harita hâlâ panoyu terk eden bir yüzeyi duyuruyor"


def test_t4_global_soru_isareti_haritayi_aciyor():
    """'?' zaten globaldi; bu test onu çivi haline getirir (palet-içi komut da aynı yere gider)."""
    h = KOD_JS[KOD_JS.rindex('addEventListener("keydown"'):]
    assert 'if (e.key === "?") { e.preventDefault(); return kbdOverlay(' in h
    assert 'id: "yrd:kbd"' in PALETTE and "window.kbdOverlay(true)" in PALETTE


# ==================================================================================
# T5 — EKRAN-BAŞINA SORU CÜMLESİ
# ==================================================================================

def _render_adlari() -> set[str]:
    """RENDER'ın TAMAMI. S2R-1'den beri iki kaynağı var ve ikisi de sayılmalı:

    * açık atamalar (`RENDER.brifing = …`) — on iki eski görünüm + Genel Bakış,
    * kabuk üreteci (`RENDER[alan] = alanSayfasi(alan, …)`) — altı alan sayfası.

    Yalnız açık atamaları saymak, altı sayfayı denetimin DIŞINDA bırakırdı: soru cümlesi
    olmayan bir sayfa test yeşilken doğabilirdi ve bu, testin var olma sebebinin tersi olurdu.
    """
    acik = set(re.findall(r"^RENDER\.(\w+) = ", APPJS, re.M))
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil — kabuk üreteci kaybolmuş"
    assert "RENDER[alan] = alanSayfasi(alan, bolumler)" in APPJS, \
        "alan sayfaları ALAN_BOLUMLERI'nden TÜRETİLMİYOR — iki liste elle tutulur ve kayar"
    return acik | set(re.findall(r"^\s*(\w+):\s*\[", blok.group(1), re.M))


def test_t5_her_cizilebilir_yuzeyin_sorusu_var():
    """HER ÇİZİLEBİLİR YÜZEY, BİR CÜMLE. Sayı bilerek SABİT DEĞİL — kural sayının kendisi
    değil, eşleşmenin TAM olması.

    ÇİVİ İKİ KEZ TAŞINDI (silme yok, gerekçe kayıtlı):
      * S2R-1 (2026-08-02): 12 → 19. IA yedi alan sayfasına geçti, eski on iki görünüm
        silinmeden bölüm oldu.
      * S2R-2 (2026-08-02): 19 → değişken. İçerik göçü üç görünümü BÖLDÜ (onaylar/intraday/
        operasyon) ve sekiz yeni bölüm doğdu; sayıyı sabitlemek, her göçte testin "kaç oldu"
        diye güncellenmesini gerektirirdi ve o güncelleme kuralı DEĞİL sayıyı korurdu.
        Sabit sayı yerine ALT SINIR + TAM EŞLEŞME: yüzey sayısı yediden az olamaz (yedi alan
        sayfası) ve cümlesiz/karşılıksız tek bir ad bile kalamaz.
    """
    blok = re.search(r"const EKRAN_SORUSU = \{(.*?)\n\};", KOD_JS, re.S)
    assert blok, "EKRAN_SORUSU tanımlı değil"
    sorular = dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", blok.group(1)))
    renderlar = _render_adlari()
    assert len(renderlar) >= 19, f"çizilebilir yüzey sayısı düşmüş ({len(renderlar)}) — içerik kaybı?"
    assert set(sorular) == renderlar, (
        f"soru cümlesi olmayan / karşılığı olmayan görünüm: {sorted(set(sorular) ^ renderlar)}")
    for ad, cumle in sorular.items():
        assert cumle.rstrip().endswith("?"), f"{ad}: soru cümlesi soru işaretiyle bitmiyor"
        assert len(cumle) < 160, f"{ad}: 'tek sönük satır' değil, paragraf olmuş"


def test_t5_mertebe_on_eki_dogru():
    """Cümlenin İLK İKİ KELİMESİ mertebeyi söyler ve bu bir sözleşmedir: alan sayfası "Bu ekran
    şunu cevaplar:", bölüm "Bu bölüm şunu cevaplar:". S2R-2'de altı bölüm ev değiştirdi; bir
    bölümün cümlesi "ekran" kalsaydı okuyucu onu hâlâ bir sayfa sanardı."""
    blok = re.search(r"const EKRAN_SORUSU = \{(.*?)\n\};", KOD_JS, re.S).group(1)
    sorular = dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", blok))
    sayfalar = set(re.findall(r"^\s*(\w+):\s*\[", re.search(
        r"const ALAN_BAS = \{(.*?)\n\};", APPJS, re.S).group(1), re.M))
    for ad, c in sorular.items():
        beklenen = "Bu ekran şunu cevaplar:" if ad in sayfalar else "Bu bölüm şunu cevaplar:"
        assert c.startswith(beklenen), f"{ad}: mertebe öneki yanlış — {c[:26]!r}"


def test_t5_her_gorunum_cumleyi_gercekten_ciziyor():
    """Sözlükte durmak yetmez — RENDER onu BASMALI. Bir tanım, çağrılmadıkça bir yorumdur
    (YASA 6'nın bu turdaki küçük kardeşi: okuyucusuz yazım yok).

    ÜÇ ÇİZİM YOLU (S2R-2): alan sayfaları ortak kabuktan (`alanBasHTML` → `soruCumlesi(id)`),
    bölümlerin çoğu ortak bölüm başlığından (`bolumBasHTML` → `soruCumlesi(id)`), kalanı
    doğrudan (`soruCumlesi("market")`). Üçü de sayılır; biri sayılmazsa "çiziliyor" iddiası
    yarım kalır.

    ÇİVİ TAŞINDI (S2R-2): S2R-1'de iki yol vardı ve bölümler cümleyi kendi gövdelerinde
    basıyordu. Göç sırasında o gövdelerin başlık katmanları ERİTİLDİ (kart-içinde-kart yasağı)
    ve tek bir kalıba indi — dolayısıyla ölçüm de o kalıbı tanımak zorunda."""
    dogrudan = set(re.findall(r'soruCumlesi\("(\w+)"\)', APPJS))
    kabuk = re.search(r"function alanBasHTML\(id\) \{(.*?)\n\}", APPJS, re.S)
    assert kabuk and "soruCumlesi(id)" in kabuk.group(1), \
        "alan sayfası kabuğu soru cümlesini BASMIYOR"
    bolum = re.search(r"function bolumBasHTML\(id, baslik, altyazi\) \{(.*?)\n\}", APPJS, re.S)
    assert bolum and "soruCumlesi(id)" in bolum.group(1), \
        "bölüm başlığı kalıbı soru cümlesini BASMIYOR"
    # Kabuğun kapsadığı sayfalar: ALAN_BAS sözlüğünün anahtarları (kabuk onları çizer).
    bas = re.search(r"const ALAN_BAS = \{(.*?)\n\};", APPJS, re.S)
    assert bas, "ALAN_BAS tanımlı değil"
    kabuklu = set(re.findall(r"^\s*(\w+):\s*\[", bas.group(1), re.M))
    # `bolumBasHTML("<ad>", …)` çağrıları — bölümün cümlesini basan ikinci yol.
    bolumlu = set(re.findall(r'bolumBasHTML\("(\w+)"', APPJS))
    cizilen = dogrudan | kabuklu | bolumlu
    assert cizilen >= _render_adlari(), (
        f"çizilmeyen soru cümlesi: {sorted(_render_adlari() - cizilen)}")


def test_t5_satir_sonuk_ve_kancasi_var():
    """Sönük (`--tx3`, 12px) ve testlenebilir (`data-soru`). Kendi CSS sınıfını index.html'e
    EKLEMEZ: jeton/tema katmanı paralel hattın alanı — bu tur oraya dokunmaz."""
    fn = KOD_JS[KOD_JS.index("function soruCumlesi("):]
    fn = fn[:fn.index("\n}") + 2]
    assert 'data-soru="${id}"' in fn, "test kancası yok"
    assert "var(--tx3)" in fn and "font-size:12px" in fn, "satır sönük değil"
    assert 'class="hint soru-c"' in fn


def test_t5_bilinmeyen_gorunum_cumle_uydurmaz():
    fn = KOD_JS[KOD_JS.index("function soruCumlesi("):]
    fn = fn[:fn.index("\n}") + 2]
    assert 'if (!s) return "";' in fn, "kayıtsız görünüm için uydurma cümle riski"
