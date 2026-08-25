"""test_belge_rafi_v312.py — belge rafının ÜÇ ölçülmüş kusuru (2026-08-25, operatör ekranı).

Operatörün gördüğü iki şey vardı: "uç yok" rozeti ve HTTP 405. Denetim üçüncüsünü ekledi: uç
yazıldıktan sonra da pano onu okumadı ve ekranda kendi ucunu YALANLAYAN cümleler kaldı.

KUSUR 1 — HEAD /runbook 405. Pano rafı `/runbook`u HEAD ile yokluyor: ÖLÇÜLDÜ (2026-08-25)
`docs/RUNBOOK.md` 184 776 bayt ve sunulan sayfa 238 785 bayt — bunu indirmeden "kapı açık mı"
diye sormak DOĞRU olandır. Rota `@app.get` ile tanımlıydı ve FastAPI `@app.get`te YALNIZ GET
kaydeder: Starlette'in düz `Route`u HEAD'i kendiliğinden ekler ama FastAPI'nin `APIRoute`u
EKLEMEZ. Canlıda ölçüldü: GET 401, HEAD 405. Yani panel doğru soruyu soruyor, rota cevap
veremiyor. Çiviler: HEAD 405 DEĞİL · HEAD yetkisizken GET ile AYNI kapıdan ve AYNI gövdeyle
401 · yetkili HEAD TELDE gövde yaymıyor · HEAD markdown'ı render ETMİYOR · belge yokken HEAD
de GET gibi 503.

KUSUR 2 — karar/hüküm arşivinin ucu YOK'tu. `docs/` altında 14 belge (KARAR-*.md · HUKUM-*.md)
duruyordu, hiçbirini listeleyen uç yoktu. Çiviler: uç 14 belgeyi listeliyor · yetki istiyor ·
desen dışı dosya listelenmiyor · dizin DIŞINA çıkan sembolik bağ AÇILMIYOR · okunamayan belge
"ölçülemedi + neden" diyor (sessizce düşmüyor) · uç kullanıcıdan YOL almıyor.

KUSUR 3 — uç yazıldı, OKUYUCUSU YAZILMADI (YASA 6) ve daha kötüsü pano kendi ucunu yalanladı:
rafta "uç yok" rozeti, "sunum ucu yok" uyarı kartı ve dosya başında "listeleyen ya da sunan bir
uç api.py'de YOK" beyanı durmaya devam etti. Bir cümle ölçüldüğü an doğruydu diye doğru kalmaz;
uç geldiğinde okuyucu da gelmezse ekran, sistemin kendi hakkındaki en yeni gerçeğini gizler.
Aynı sınıfın ikinci örneği yorumdaki YANLIŞ TEKNİK İDDİAYDI ("Starlette GET rotalarına HEAD'i
kendisi ekler") — 405'in kök nedeni tam olarak o yanlış ölçüttü ve yorumda kalsaydı bir sonraki
teşhisi de yanlış yöne sürerdi. Çiviler bu yüzden yorumları HER ZAMAN sökmez: bayat beyan
yorumda dursa da kusurdur.

YOL GEÇİŞİ NEDEN "İMKÂNSIZ" DEĞİL DE ÇİVİLİ: bugün uç hiçbir kullanıcı girdisi almıyor, yani
saldırı yüzeyi yok. Ama içerik sunumu (ikinci adım) bir `?ad=` parametresi getirdiğinde bu
testler o parametrenin ham hâlde dosya sistemine geçmesini engelleyecek — kapı bugün kurulur,
yarın açılmaz.
"""
from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth


ARSIV_UCU = "/api/karar-belgeleri"
# Arşivin TANIMI — üretim kodundaki desenin testteki BAĞIMSIZ ikizi. Kopya değil karşı-ölçüm:
# üretimdeki desen gevşerse (örn. `.md` şartı düşerse) iki taraf ayrışır ve test öter.
_ARSIV_DESENI = re.compile(r"^(?:KARAR|HUKUM)-.+\.md$")


def _acik_kapi(monkeypatch):
    """Yetki kapısını AÇIK bir istemci: parola kurulu değil, token yok → `_auth` geçer."""
    monkeypatch.setattr(auth, "password_set", lambda: False)
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _kapali_kapi(monkeypatch, token: str = "T0KEN-312"):
    """Yetki kapısı KAPALI bir istemci: token ayarlı, istekte başlık YOK → `_auth` 401 verir."""
    monkeypatch.setattr(auth, "password_set", lambda: False)
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    return TestClient(api.app), token


def _gercek_arsiv() -> list[str]:
    """`docs/` altındaki gerçek arşiv adları — testin KENDİ taraması (uçtan bağımsız)."""
    d = Path(api.config.ROOT) / "docs"
    return sorted(p.name for p in d.iterdir() if p.is_file() and _ARSIV_DESENI.match(p.name))


# ===================== KUSUR 1 · HEAD /runbook =====================

def test_head_runbook_405_donmuyor(monkeypatch):
    """Panonun sorduğu soru cevap almalı: HEAD /runbook 405 DEĞİL, GET ile aynı durumu döner.

    405 "yöntem yok" demektir ve panonun rafında `/runbook` satırını kırmızı yakar — belge
    yerinde dururken. Ölçülen kusur tam olarak buydu."""
    c = _acik_kapi(monkeypatch)
    y = c.head("/runbook")
    assert y.status_code != 405, "HEAD hâlâ 405 — rota HEAD'i kaydetmiyor"
    assert y.status_code == 200, f"HEAD beklenen 200'ü vermedi: {y.status_code}"


def _asgi_yanit(yol: str, yontem: str, basliklar: tuple = ()) -> tuple[int, bytes]:
    """Uygulamanın ASGI üzerinden GERÇEKTEN yaydığı (durum, gövde) — istemci katmanı ARADAN ÇIKAR.

    NEDEN GEREKLİ (2026-08-25 denetimi): `TestClient` bir HEAD yanıtının gövdesini httpx
    katmanında ATAR. Bu yüzden `y.content == b""` çivisi, sunucu gövde yollasa bile YEŞİL
    yanıyordu — ölçüldü: yetkisiz HEAD yanıtında `Content-Length: 25` ve 25 baytlık yetki zarfı
    telden geçiyordu. Yani o çivi sunucu hakkında hiçbir şey söylemiyor, istemciyi ölçüyordu.
    Burada `http.response.body` olayları olduğu gibi biriktirilir; ölçülen şey TELDEKİ bayttır."""
    kapsam = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1", "method": yontem, "scheme": "http",
        "path": yol, "raw_path": yol.encode(), "query_string": b"",
        "root_path": "", "headers": [(b"host", b"testserver"), *basliklar],
        "client": ("testclient", 50000), "server": ("testserver", 80),
    }
    olaylar: list[dict] = []

    async def _al():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def _yolla(mesaj):
        olaylar.append(mesaj)

    asyncio.run(api.app(kapsam, _al, _yolla))
    durum = next(o["status"] for o in olaylar if o["type"] == "http.response.start")
    govde = b"".join(o.get("body", b"") for o in olaylar if o["type"] == "http.response.body")
    return durum, govde


def test_head_runbook_yetkisizken_401(monkeypatch):
    """HEAD, GET ile AYNI yetki kapısından geçer. Yetkisiz bir HEAD'in 200 dönmesi, belgenin
    varlığını (ve dolaylı olarak sistemin iç haritasının orada durduğunu) yetkisiz bir çağırana
    doğrulamak olurdu — bir bilgi sızıntısı.

    ESKİ ÇİVİ ÖTMÜYORDU ve yerine bu geldi. `assert y.content == b""` bir GARANTİ gibi
    duruyordu ama istemciyi ölçüyordu: `TestClient` HEAD gövdesini atar, sunucu ise aynı istekte
    25 baytlık yetki zarfını yayıyordu (`Content-Length: 25`). Yani o satırın söylediği şey
    ("gövde de gitmez") ölçüldüğünde YANLIŞ çıktı; olmayan bir garantiyi okuyucuya söylemek
    yasaktır. Ölçüm artık ASGI olay akışından.

    ÇİVİLENEN ÜÇ ŞEY: (a) durum 401, (b) telde yayılan gövde GET'in 401 zarfının AYNISI — yani
    HEAD ayrı bir kod yolu değil, kapı tek, (c) o zarf belgeden hiçbir şey taşımıyor. 25 baytlık
    zarf bir sızıntı DEĞİL: belgenin var olup olmadığı hakkında tek kelime etmiyor."""
    c, token = _kapali_kapi(monkeypatch)
    y = c.head("/runbook")
    assert y.status_code == 401, f"yetkisiz HEAD 401 vermedi: {y.status_code}"

    h_durum, h_govde = _asgi_yanit("/runbook", "HEAD")
    g_durum, g_govde = _asgi_yanit("/runbook", "GET")
    assert h_durum == 401 and g_durum == 401, (h_durum, g_durum)
    assert h_govde == g_govde, f"HEAD 401 ayrı bir gövde yolu tuttu: {h_govde!r} != {g_govde!r}"
    assert len(h_govde) < 1024, f"yetkisiz HEAD gövde sızdırdı: {len(h_govde)} bayt"

    # POZİTİF KONTROL — İKİ KATLI: (1) 401 "her şey kırık"tan değil, gerçekten kapıdan geliyor;
    # (2) ölçüm aracı KÖR DEĞİL: yetkili GET'te sayfanın tamamını görüyor. Kör bir okuyucuyla
    # "gövde sızmadı" demek, gözü kapalı "yol boş" demekle aynı şey olurdu.
    yetkili = ((b"x-meridian-token", token.encode()),)
    assert c.head("/runbook", headers={"x-meridian-token": token}).status_code == 200
    _, tam = _asgi_yanit("/runbook", "GET", yetkili)
    assert len(tam) > 100_000, f"ASGI okuyucusu gövde görmüyor, çivi kör: {len(tam)} bayt"
    # ASIL "gövde gitmez" ÇİVİSİ BURADA ve yalnız burada doğru: YETKİLİ HEAD telde SIFIR bayt.
    _, yoklama = _asgi_yanit("/runbook", "HEAD", yetkili)
    assert yoklama == b"", f"yetkili HEAD telde gövde yaydı: {len(yoklama)} bayt"


def test_head_govde_URETMIYOR_get_uretiyor(monkeypatch):
    """HEAD'in TÜM ANLAMI: 184 776 baytlık markdown'ı (ölçüldü 2026-08-25) 238 785 baytlık bir
    HTML sayfasına çevirmeden "kapı açık mı" diye sormak.

    Ölçüm doğrudan: `_md_render` HEAD'de HİÇ çağrılmamalı, GET'te çağrılmalı. "Gövde boş mu"
    diye bakmak yetmezdi — sunucu render'ı yapıp gövdeyi atsaydı test yine yeşil yanardı ve
    ölçülen tasarruf hiç gerçekleşmezdi."""
    sayac = {"n": 0}
    gercek = api._md_render

    def _sayan(md: str):
        sayac["n"] += 1
        return gercek(md)

    monkeypatch.setattr(api, "_md_render", _sayan)
    c = _acik_kapi(monkeypatch)

    assert c.head("/runbook").status_code == 200
    assert sayac["n"] == 0, "HEAD gövdeyi render etti — yoklamanın maliyeti GET ile aynı kaldı"

    assert c.get("/runbook").status_code == 200
    assert sayac["n"] == 1, "GET render etmedi — sayaç ölçmüyor, test anlamsız"


def test_get_runbook_hala_gercek_sayfa_donduruyor(monkeypatch):
    """REGRESYON: HEAD eklemek GET'i bozmamalı. Gövde YER TUTUCUSUZ ve DOLU gelir."""
    c = _acik_kapi(monkeypatch)
    y = c.get("/runbook")
    assert y.status_code == 200
    for yt in api._RUNBOOK_YER_TUTUCU:
        assert yt not in y.text, f"{yt} yer tutucusu doldurulmamış — sayfa boş çıkıyor"
    assert len(y.text) > 10_000, f"runbook gövdesi şüpheli kısa: {len(y.text)} bayt"


def test_head_belge_yoksa_GET_gibi_503(monkeypatch):
    """DURUM PARİTESİ: HEAD, GET'in söyleyeceğinden BAŞKA bir şey söylemez. Belge üretilmemişse
    GET 503 der; HEAD 200 deseydi pano "raf dolu" diye yeşil yanar, tıklayan operatör hataya
    düşerdi — yoklama tam da bu yalanı önlemek için var."""
    monkeypatch.setattr(api, "RUNBOOK_MD", Path(api.config.ROOT) / "docs" / "YOK-OLAN-RUNBOOK.md")
    c = _acik_kapi(monkeypatch)
    assert c.get("/runbook").status_code == 503
    assert c.head("/runbook").status_code == 503, "HEAD, GET'ten farklı bir gerçek söyledi"


# ===================== KUSUR 2 · karar/hüküm arşivi ucu =====================

def test_arsiv_ucu_yetki_istiyor(monkeypatch):
    """Arşiv tur hükümlerini, kök nedenleri ve açık kalemleri taşır — sistemin iç haritası.
    `/runbook` ile aynı sınıf, yani aynı kapı."""
    c, token = _kapali_kapi(monkeypatch)
    assert c.get(ARSIV_UCU).status_code == 401
    assert c.get(ARSIV_UCU, headers={"x-meridian-token": token}).status_code == 200


def test_arsiv_ucu_ondort_belgeyi_listeliyor(monkeypatch):
    """ÖLÇÜLDÜ (2026-08-25): `docs/` altında 14 arşiv belgesi var. Uç TAM O KÜMEYİ döner.

    Sayı LİTERAL olarak çivilenmez (yarın 15 olur ve test bayatlardı) — testin KENDİ taraması
    ile uç KARŞILAŞTIRILIR; 14 yalnız "tarama boş değil" tabanıdır."""
    c = _acik_kapi(monkeypatch)
    y = c.get(ARSIV_UCU)
    assert y.status_code == 200
    g = y.json()
    assert g["ok"] is True, g
    adlar = [b["ad"] for b in g["belgeler"]]
    beklenen = _gercek_arsiv()
    assert len(beklenen) >= 14, f"tarama bozuldu, arşiv {len(beklenen)} belge gördü"
    assert sorted(adlar) == beklenen, f"uç ile disk ayrıştı: {set(adlar) ^ set(beklenen)}"
    # SIRA: en yeni önce. Tarihi olmayan belge sona düşer (bugün yok, ama sıra kuralı çivili).
    tarihli = [b["tarih"] for b in g["belgeler"] if b["tarih"]]
    assert tarihli == sorted(tarihli, reverse=True), f"sıra en-yeni-önce değil: {tarihli}"


def test_kayit_alanlari_gercekten_olculuyor(monkeypatch):
    """Dört alan da DİSKTEN gelir: ad · tarih (dosya adından) · başlık (ilk `# ` satırı) · bayt."""
    hedef = "KARAR-2026-08-25-D4-STUDIO-ADMIN-GOCU.md"
    p = Path(api.config.ROOT) / "docs" / hedef
    if not p.exists():
        pytest.skip(f"referans belge yok: {hedef}")
    c = _acik_kapi(monkeypatch)
    kayit = next(b for b in c.get(ARSIV_UCU).json()["belgeler"] if b["ad"] == hedef)
    assert kayit["tarih"] == "2026-08-25", kayit
    assert kayit["bayt"] == p.stat().st_size, kayit
    ilk_baslik = next(s[2:].strip() for s in p.read_text(encoding="utf-8").splitlines()
                      if s.startswith("# "))
    assert kayit["baslik"] == ilk_baslik, kayit
    assert kayit["neden"] is None, f"ölçülen belge için neden yazılmış: {kayit}"


def test_desen_disi_dosyalar_LISTELENMIYOR(monkeypatch, tmp_path):
    """Arşivin tanımı desendir: `docs/` altındaki KARAR-*.md ve HUKUM-*.md. Komşu dosyalar
    (sır dosyaları, notlar) ve aynı adı taşıyan DİZİNLER rafa giremez."""
    (tmp_path / "KARAR-2026-01-01-GERCEK.md").write_text("# Gerçek karar\n", encoding="utf-8")
    (tmp_path / "HUKUM-2026-01-02-GERCEK.md").write_text("# Gerçek hüküm\n", encoding="utf-8")
    (tmp_path / ".env").write_text("MERIDIAN_DASH_TOKEN=sir\n", encoding="utf-8")
    (tmp_path / "NOTLAR.md").write_text("# Not\n", encoding="utf-8")
    (tmp_path / "KARAR-2026-01-03-YEDEK.md.bak").write_text("# Yedek\n", encoding="utf-8")
    (tmp_path / "KARAR-2026-01-04-DIZIN.md").mkdir()

    monkeypatch.setattr(api, "_karar_belgeleri_dizini", lambda: tmp_path)
    c = _acik_kapi(monkeypatch)
    adlar = {b["ad"] for b in c.get(ARSIV_UCU).json()["belgeler"]}
    assert adlar == {"KARAR-2026-01-01-GERCEK.md", "HUKUM-2026-01-02-GERCEK.md"}, adlar


def test_dizin_disina_cikan_bag_ACILMIYOR_ama_gizlenmiyor(monkeypatch, tmp_path):
    """YOL GEÇİŞİ ÇİVİSİ: arşiv adı taşıyan bir sembolik bağ dizin DIŞINI gösteriyorsa
    AÇILMAZ — ne boyutu ne başlığı okunur, yani dışarıdaki içerik telden geçemez.

    Ama SESSİZCE DE DÜŞMEZ (YASA 4): kayıt listede kalır, `neden` reddi ADIYLA söyler.
    Sessiz düşme, arşivde bir belge varmış gibi görünüp olmadığı hâlin ta kendisidir."""
    arsiv = tmp_path / "docs"
    arsiv.mkdir()
    disari = tmp_path / "sir.md"
    disari.write_text("# SIZAN BASLIK\n", encoding="utf-8")
    (arsiv / "KARAR-2026-01-01-DUZGUN.md").write_text("# Düzgün\n", encoding="utf-8")
    (arsiv / "KARAR-2026-01-02-BAG.md").symlink_to(disari)

    monkeypatch.setattr(api, "_karar_belgeleri_dizini", lambda: arsiv)
    c = _acik_kapi(monkeypatch)
    y = c.get(ARSIV_UCU)
    assert "SIZAN BASLIK" not in y.text, "dizin dışındaki içerik telden geçti"
    bag = next(b for b in y.json()["belgeler"] if b["ad"] == "KARAR-2026-01-02-BAG.md")
    assert bag["baslik"] is None and bag["bayt"] is None, bag
    assert bag["neden"] and len(bag["neden"]) >= 20, f"red gerekçesiz: {bag}"


def test_okunamayan_belge_OLCULEMEDI_diyor(monkeypatch, tmp_path):
    """Okunamayan belge listeden DÜŞMEZ: adı ve boyutu ölçülür, başlığı None kalır ve `neden`
    okunamama sebebini taşır. Sessiz atlama, rafta 13 belge gösterip 14. hakkında hiçbir şey
    söylememek olurdu."""
    bozuk = tmp_path / "KARAR-2026-01-05-BOZUK.md"
    bozuk.write_bytes(b"\xff\xfe# bu ge\xc3(erli utf-8 degil\n")
    monkeypatch.setattr(api, "_karar_belgeleri_dizini", lambda: tmp_path)
    c = _acik_kapi(monkeypatch)
    kayit = next(b for b in c.get(ARSIV_UCU).json()["belgeler"]
                 if b["ad"] == "KARAR-2026-01-05-BOZUK.md")
    assert kayit["baslik"] is None, kayit
    assert kayit["bayt"] == bozuk.stat().st_size, "boyut ölçülebiliyordu, ölçülmemiş"
    assert kayit["neden"] and "UnicodeDecodeError" in kayit["neden"], kayit


def test_baslik_ve_tarih_yoksa_NEDEN_yaziliyor(monkeypatch, tmp_path):
    """UYDURMA YASAĞI: başlıksız belgeye dosya adı BAŞLIK diye yazılmaz, tarihsiz belgeye
    bugünün tarihi konmaz. İkisi de None kalır ve `neden` hangisinin neden ölçülemediğini söyler."""
    (tmp_path / "KARAR-BASLIKSIZ.md").write_text("gövde var, başlık yok\n", encoding="utf-8")
    monkeypatch.setattr(api, "_karar_belgeleri_dizini", lambda: tmp_path)
    c = _acik_kapi(monkeypatch)
    kayit = next(b for b in c.get(ARSIV_UCU).json()["belgeler"] if b["ad"] == "KARAR-BASLIKSIZ.md")
    assert kayit["tarih"] is None and kayit["baslik"] is None, kayit
    assert "tarih" in kayit["neden"] and "başlık" in kayit["neden"], kayit


def test_arsiv_dizini_yoksa_200_ve_HATA(monkeypatch, tmp_path):
    """Dizin okunamıyorsa 200 + `hata` döner, 404 değil: 404'ün gövdesi FastAPI zarfıdır ve
    pano HANGİ dizinin okunamadığını göremezdi. `belgeler` null'dır — boş liste "arşiv boş"
    diye okunur, oysa ölçülen şey "dizini bulamadım"."""
    monkeypatch.setattr(api, "_karar_belgeleri_dizini", lambda: tmp_path / "yok-olan-dizin")
    c = _acik_kapi(monkeypatch)
    g = c.get(ARSIV_UCU).json()
    assert g["ok"] is False and g["belgeler"] is None, g
    assert g["hata"] and len(g["hata"]) >= 20, g


def test_uc_kullanicidan_YOL_almiyor():
    """YAPISAL KAPI: uç `request` DIŞINDA parametre almaz, yani kullanıcıdan gelen hiçbir dize
    dosya sistemine geçemez. İçerik sunumu (ikinci adım) bir `?ad=` getirdiğinde bu test öter
    ve yol geçişi tartışması BİLEREK yeniden açılır — sessizce açılmaz."""
    imza = inspect.signature(api.api_karar_belgeleri)
    assert list(imza.parameters) == ["request"], f"uç yeni bir girdi aldı: {list(imza.parameters)}"


# ===================== KUSUR 3 · rafın OKUYUCUSU (YASA 6) =====================
#
# Uç yazıldı, okuyucusu yazılmadı — ve pano ekranda kendi ucunu YALANLAMAYA devam etti. Bu
# bölümün çivileri panonun KAYNAK METNİNİ ölçer, çünkü bu depoda tarayıcı koşturan bir sınama
# hattı yok; kaynak ölçümünün iki tuzağı var ve ikisi de burada kapalı:
#   · ALT-DİZE TUZAĞI — bir dizenin kaynakta "geçiyor olması" kanıt değildir; aynı dize bir
#     yorumda da geçebilir ve varlık çivisi hiç ötmez. VARLIK çivileri bu yüzden yorumları
#     SÖKÜLMÜŞ metinde ve ÇAĞRI BİÇİMİ regex'iyle ölçer.
#   · YOKLUK çivileri bunun TERSİDİR ve bilerek HAM metni tarar: bayat bir beyan yorumda dursa
#     da kusurdur — bir sonraki okuyucu onu ölçüm sanar (bu tur tam olarak bu oldu).

_PANO_BELGELER = Path(api.config.ROOT) / "ui" / "src" / "pano" / "yuzeyler" / "belgeler"

#: Bayat boyut iddiası. PARÇALI yazılıyor: bu dosyanın kendi gövdesi de çivinin taradığı
#: hedeflerden biri ve bir dizeyi hem yasaklayıp hem metninde taşımak, çivinin ilk kurbanı
#: olmak olurdu. Gerçek ölçüm 2026-08-25: `docs/RUNBOOK.md` 184 776 bayt → sayfa 238 785 bayt.
_BAYAT_BOYUT = "163" + " KB"


def _yorumsuz(kaynak: str) -> str:
    """TS/TSX kaynağından yorumları söker; DİZE gövdelerine dokunmaz.

    Sökücü `"` `'` `` ` `` dizelerini ayırt eder, `/* … */` ve `// …` yorumlarını birer boşlukla
    değiştirir. JSX yorumu (`{/* … */}`) blok yorumun özel hâlidir, aynı yoldan düşer.

    KANDIRILDIĞINDA SESSİZ KALMAZ: JSX METNİNDEKİ düz kesme işareti (`api.py'de`) sahte bir dize
    açar ve ardındaki yorum sökülmeden kalır — o hâlde çivi yorumdaki cümleyi "kod" sanardı.
    Sökücü dize içinde biterse ölçüm GEÇERSİZ sayılır ve bağırır; pano metinlerinde tipografik
    kesme (`’`) kullanmanın nedeni budur."""
    cikti: list[str] = []
    i, n = 0, len(kaynak)
    tirnak: str | None = None
    while i < n:
        c = kaynak[i]
        if tirnak is not None:
            cikti.append(c)
            if c == "\\" and i + 1 < n:
                cikti.append(kaynak[i + 1])
                i += 2
                continue
            if c == tirnak:
                tirnak = None
            i += 1
            continue
        if c in "\"'`":
            tirnak = c
            cikti.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and kaynak[i + 1] == "*":
            j = kaynak.find("*/", i + 2)
            i = n if j == -1 else j + 2
            cikti.append(" ")
            continue
        if c == "/" and i + 1 < n and kaynak[i + 1] == "/":
            j = kaynak.find("\n", i)
            i = n if j == -1 else j
            cikti.append(" ")
            continue
        cikti.append(c)
        i += 1
    if tirnak is not None:
        raise AssertionError(
            f"yorum sökücü dize içinde bitti (kapanmayan {tirnak!r}) — büyük olasılıkla JSX "
            "metninde düz kesme işareti var; bu ölçüm GEÇERSİZ, sessizce yeşil yanmasın")
    return "".join(cikti)


def _pano_kaynak(ad: str) -> str:
    return (_PANO_BELGELER / ad).read_text(encoding="utf-8")


def _pano_dosyalari() -> list[Path]:
    return sorted(p for p in _PANO_BELGELER.iterdir() if p.suffix in (".ts", ".tsx"))


def test_yorum_sokucusu_KENDISI_olculuyor():
    """POZİTİF KONTROL: sökücü çalışmıyorsa aşağıdaki VARLIK çivilerinin hepsi sessizce yalan
    söyler (yorumdaki dize "kod" sayılır). Sentetik örnekte aynı iz üç yorumda ve iki dizede
    geçiyor; sökümden sonra tam iki tanesi kalmalı."""
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    soyulmus = _yorumsuz(ornek)
    assert soyulmus.count("IZ") == 2, soyulmus
    assert "/*" not in soyulmus and "*/" not in soyulmus, soyulmus


#: Yorumları SÖKÜLMÜŞ metin üzerinden ölçülen dosyalar. Kapsam dar tutuluyor: sökümün
#: artık bırakmadığını iddia etmek, ancak o dosyada gerçekten iddia edilebilir (bkz. aşağıdaki
#: çivinin şerhi).
_SOKUMLE_OLCULENLER = ("KararBelgeleri.tsx", "ortak.tsx")


def test_sokucu_gercek_dosyalarda_TEMIZ_bitiyor():
    r"""Sökücü, ÖLÇTÜĞÜ dosyalarda gerçekten çalışıyor mu? İki kanıt, iki ayrı kapsam.

    (a) DİZE İÇİNDE BİTMİYOR — dizinin TAMAMI için: `_yorumsuz` kandırılırsa bağırır, yani
        Hafiza.tsx ve damitim.ts de bu turnikeden geçer.
    (b) ARTIK YORUM İŞARETİ KALMIYOR — yalnız sökümle ölçülen iki dosya için. Kapsam bilerek
        dar: bir REGEX LİTERALİ meşru olarak `*/` taşıyabilir (ölçüldü — damitim.ts::vurguSok
        içindeki `/\*\*(.+?)\*\*/g`), ve o dosyayı da kapsama katmak çiviyi yanlış bir
        gerekçeyle kırmızıya çevirirdi. Yanlış gerekçeyle kırmızı, yeşile alıştırır."""
    for p in _pano_dosyalari():
        soyulmus = _yorumsuz(p.read_text(encoding="utf-8"))
        if p.name in _SOKUMLE_OLCULENLER:
            assert "/*" not in soyulmus and "*/" not in soyulmus, f"{p.name}: sökücü kandırılmış"
    assert set(_SOKUMLE_OLCULENLER) <= {p.name for p in _pano_dosyalari()}, (
        "sökümle ölçülen dosya adı bayatladı — çivi olmayan bir dosyayı sınıyor")


def test_raf_ARSIV_UCUNU_gercekten_cagiriyor():
    """YASA 6 — uç yazıyor, PANO OKUYOR. Varlık kontrolü değil ÇAĞRI BİÇİMİ çivileniyor: yolun
    kaynakta geçmesi kanıt değil (bir yorumda da geçebilir, bu turda üç kez bu tuzağa düşüldü),
    `useApi<…>("…")` çağrısının kendisi kanıttır."""
    s = _yorumsuz(_pano_kaynak("KararBelgeleri.tsx"))
    # İKİ HALKALI ZİNCİR, ikisi de BİÇİM çivisi: (1) sabit gerçekten bu yola bağlı,
    # (2) `useApi` gerçekten o sabitle çağrılıyor. Tek halka yetmezdi — sabit başka bir yola
    # kaydırılsa çağrı biçimi aynı kalır ve çivi ötmezdi.
    baglama = r'const\s+ARSIV_UCU\s*=\s*"' + re.escape(ARSIV_UCU) + r'"\s*;'
    assert re.search(baglama, s), f"`ARSIV_UCU` sabiti {ARSIV_UCU} yoluna bağlı değil"
    assert re.search(r"useApi<[^;()]*>\(\s*ARSIV_UCU\b", s), (
        "raf ucu okumuyor: `useApi<…>(ARSIV_UCU)` çağrısı yok — uç yazıldı, okuyucusu yok")


def test_ucun_HER_ALANININ_bir_okuyucusu_var(monkeypatch):
    """YASA 6'nın tamamı: uç dokuz alan yazıyor, dokuzunun da okuyucusu olmalı. Alan listesi
    UÇTAN ÖLÇÜLÜR, testte elle sayılmaz — yarın uca bir alan eklenirse bu çivi onu da ister ve
    "yazıldı ama kimse okumuyor" sınıfı bir daha sessizce açılamaz."""
    c = _acik_kapi(monkeypatch)
    g = c.get(ARSIV_UCU).json()
    assert g["belgeler"], "arşiv boş döndü — alan taraması tabansız kalırdı"
    alanlar = sorted(set(g) | set(g["belgeler"][0]))
    assert len(alanlar) >= 9, f"uç sözleşmesi daraldı, tarama tabansız: {alanlar}"
    s = _yorumsuz(_pano_kaynak("KararBelgeleri.tsx"))
    okunmayan = [a for a in alanlar if not re.search(r'\[\s*"' + re.escape(a) + r'"\s*\]', s)]
    assert okunmayan == [], f"uç yazıyor, pano okumuyor: {okunmayan}"


def test_pano_KENDI_UCUNU_yalanlamiyor():
    """Bayat beyanlar ekrandan VE yorumdan kalkmalı. Çivi HAM metni tarar (yorum sökmez) çünkü
    kusur tam da yorumdaki cümlenin ölçüm sanılmasıydı: rafta "uç yok" rozeti, "sunum ucu yok"
    uyarı kartı ve dosya başında "listeleyen ya da sunan bir uç YOK" beyanı, uç canlıyken
    duruyordu."""
    ham = _pano_kaynak("KararBelgeleri.tsx")
    duz = " ".join(ham.split())
    bayat = [c for c in ("listeleyen ya da sunan bir uç",
                         "LİSTELEYEN ya da SUNAN bir uç",
                         "arşivinin sunum ucu yok") if c in duz]
    assert bayat == [], f"pano kendi ucunu yalanlıyor: {bayat}"
    assert not re.search(r">\s*uç yok\s*<", ham), '"uç yok" rozeti hâlâ çiziliyor'
    assert not re.search(r"\buc:\s*null", _yorumsuz(ham)), "rafta hâlâ uçsuz satır tanımı var"


def test_ortak_YANLIS_TEKNIK_IDDIAYI_tasimiyor():
    """"Starlette GET rotalarına HEAD'i kendisi ekler" cümlesi FastAPI `APIRoute` için YANLIŞTI
    ve 405'in kök nedeni tam olarak bu yanlış ölçüttü. Yorumda kalan yanlış bir teknik iddia bir
    sonraki teşhisi de yanlış yöne sürer; bu yüzden hem yanlış genellemenin YOKLUĞU hem doğru
    ölçütün VARLIĞI çivileniyor — birincisi olmadan ikincisi "iki iddia yan yana" demek olurdu."""
    duz = " ".join(_pano_kaynak("ortak.tsx").split())
    assert "GET rotalarına HEAD" not in duz, "yanlış genelleme hâlâ yorumda"
    assert re.search(r"APIRoute.{0,80}EKLEMEZ", duz), "doğru ölçüt yazılmamış (`APIRoute` … EKLEMEZ)"
    assert "YALNIZ GET kaydeder" in duz, "`@app.get`in yalnız GET kaydettiği yazılmamış"


def test_belge_yuzeyinde_SATIR_CAPASI_kalmadi():
    """`dosya.py:NNN` biçimli çapa bu dizinde SIFIR. Satır numarası kaydıkça sessizce
    yalanlaşır, sembol adı kaymaz. Ölçülen borç (2026-08-25): ortak.tsx bir, KararBelgeleri.tsx
    iki çapa taşıyordu; üçü de sembol adına çevrildi (`api.py::runbook` ·
    `api.py::api_karar_belgeleri`) ya da tümüyle gereksizleşti.
    Sayılar buraya KANIT diye bile yazılmıyor — mezar taşı da bir çapadır ve o da bayatlar."""
    capa = re.compile(r"\b[\w./-]+\.py:\d+")
    kalan = {p.name: sorted(set(capa.findall(p.read_text(encoding="utf-8"))))
             for p in _pano_dosyalari()}
    kalan = {a: c for a, c in kalan.items() if c}
    assert kalan == {}, f"satır çapası duruyor: {kalan}"


def test_OLCULMEMIS_BOYUT_iddiasi_kalmadi():
    """Panoda duran boyut rakamı hiçbir ölçümün sonucu değildi. Yerine ölçülen değer yazıldı
    (2026-08-25: `docs/RUNBOOK.md` 184 776 bayt, sunulan sayfa 238 785 bayt) ve ölçüm TARİHİYLE
    birlikte duruyor — tarihsiz bir rakam, bayatladığında bayat olduğunu söyleyemez."""
    kirli = [p.name for p in _pano_dosyalari() if _BAYAT_BOYUT in p.read_text(encoding="utf-8")]
    assert kirli == [], f"ölçülmemiş boyut iddiası duruyor: {kirli}"
