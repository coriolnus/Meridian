"""v287 · PANO ALTYAPI YÜZEYİ — `/api/infra` (makine + Meridian bileşenleri) ve `/api/roadmap`.

NEDEN BU İKİ UÇ AYNI DOSYADA: ikisi de panonun **kabuk-dışı** yüzeyleridir — biri makinenin
kendisini, diğeri işin tahtasını okur; ikisi de state/ defterine DEĞİL, işletim sistemine ve bir
markdown dosyasına bakar. Yani ikisi de bu deponun "ölçemediğini yazma" yasasının EN KOLAY
çiğnendiği sınıftır: bir makine metriği ölçülemediğinde `0` yazmak sözdizimsel olarak bedava, ve
`0` ekranda "boşta" diye okunur — ölçülemedi diye DEĞİL. Bu dosya o kısayolu kapatır.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. KAYIT + YETKİ — iki uç da rota tablosunda VAR ve ikisi de `_auth(request)` ÇAĞIRIYOR. Makine
   telemetrisi (hostname, yük, disk doluluk, hangi birim koşuyor) yetkisiz açılmaz; yol haritası
   ise iç mühendislik kararlarının tamamıdır. Çivi casus (`spy`) ile davranışa bakar — kaynak
   metnine değil: `_auth` çağrısını yorum satırına çevirmek testi YEŞİL bırakmamalı.

B. UYDURMA YASAĞI, GENEL BİÇİMDE — `/api/infra` gövdesinde None olan HER ölçüm alanının yanında
   ya kendi `<alan>_neden` kardeşi ya da kabın `olculemedi_neden` alanı DOLU olmalı. Bu, tek tek
   alan saymaktan güçlüdür: yarın eklenen bir metrik de bu kurala girer, kimse listeyi güncellemeyi
   unutamaz. Karşı-yön de çivili: ölçülemeyen alan `0`/`""`/`{}` OLARAK GELEMEZ.

C. PLATFORM FARKI GİZLENEMEZ — bu depo YERELDE macOS, CANLIDA Linux koşuyor ve `/proc` macOS'ta
   YOK. `/proc` okunamadığında uç `cpu_yuzde`/`uptime_s`/bellek alanlarını None + neden ile
   döndürmeli. Test bunu platforma BAĞLI OLMADAN sınar: `/proc` okuyucusu kasten kör edilir
   (macOS simülasyonu) ve gövde yine dürüst olmalı. Aksi hâlde test yerelde ve canlıda FARKLI
   şeyi ölçerdi — ve geçtiğinde hiçbir şey kanıtlamazdı.

D. BİRİM ADLARI UYDURULAMAZ — bileşen listesi `deploy/` altındaki GERÇEK systemd birim
   dosyalarından gelmeli. Çivi ters yönden bakar: ucun bildirdiği her birim adının diskte bir
   karşılığı olmalı. Bir gün biri "meridian-worker.service" diye var olmayan bir ad ekleyerek
   panoyu doldurursa kırmızı.

E. ŞABLON BİRİM TUZAĞI (MEMORY: "meridian-sprint şablon birim") — `meridian-sprint@.service` bir
   ŞABLONDUR; düz adla `systemctl show` sorgusu sahte bir `inactive` döndürür ve pano "koşmuyor"
   der. Ölçülen gerçek şuydu: "koşmuyor" ile "koştu, aday geçmedi" karıştı. Uç şablon birimi
   ŞABLON olarak işaretlemeli ve durumunu UYDURMAMALI.

F. `systemctl` YOKSA — boş liste DEĞİL, None + neden. Boş liste "hiç bileşen yok" diye okunur;
   oysa ölçülen şey "ölçemedim"dir. (YASA: boş gövde 'her şey yolunda' DEĞİLDİR.)

G. ÖNBELLEK BEYANI — uç 15 sn'de bir yoklanabilmeli, bu yüzden kısa önbellekli; ama bayatlığını
   `hesaplama_ts` + `onbellekten` ile BEYAN etmeli ve `?taze=1` zorlamayı açmalı
   (`/api/diagnostics` deseni, aynı gerekçe).

H. ROADMAP GERÇEK DOSYAYI OKUR — bölüm/madde sayısı > 0 ve `§0` gibi bilinen bir bölüm çıkmalı.
   Sabit/örnek bir yükle geçmek imkânsız olmalı: bildirilen `yol` diskte VAR olmalı ve dosyanın
   boyutu gövdedeki `bayt` ile birebir eşleşmeli.

I. ÜSTÜ ÇİZİLİ KAPANIŞ "KAPALI" DEĞİLDİR — ROADMAP'te `~~✅ KAPANDI~~` deseni GERÇEKTEN var
   (örn. §3'te "koruma ölmüyor" kalemi): kapanış iddiası SONRADAN GERİ ALINMIŞ demektir. Naif bir
   `"✅" in satir` ayrıştırıcısı onu kapalı sayar ve tahtayı YALAN gösterir. Çivi bunu sentetik
   metinle sınar (canlı dosyanın o satırı yarın taşınabilir; çivi taşınmaya bağlı olmamalı).

J. DOSYA YOKSA — boş liste DEĞİL, `hata` + `yol` taşıyan dürüst gövde.

K. JSON SÖZLEŞMESİ — iki gövde de `allow_nan=False` ile serileşmeli (numpy/NaN sızmıyor).
   `_NativeRoute` bunu zaten yapıyor ama sözleşme burada çivilenir, yoksa bir gün uç
   `JSONResponse` döndürmeye geçse sarıcı devre dışı kalırdı.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from meridian import api, config

REPO = pathlib.Path(__file__).resolve().parents[1]

# `<alan>_neden` kardeşi ARAMAYAN, kabın `olculemedi_neden`ine düşen alanlar da geçerlidir; ikisi de
# yoksa alan "sessizce None" demektir ve bu dosyanın kovaladığı kusur tam olarak odur.
_GEREKCE_ASGARI = 10          # bir gerekçe en az bu kadar karakter olmalı ("yok" bir gerekçe değil


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci: `with TestClient(app)` `_autostart`'ı koşturur ve
    scheduler/hermes/mirror ipliklerini ayağa kaldırırdı — bu iki uç için tamamen gereksiz ve
    paralel ajan penceresinde canlı state'e dokunma riski. Bağlamsız istemci yaşam döngüsünü
    ATLAR, rotalar yine çalışır."""
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def _onbellekleri_bosalt(monkeypatch):
    """SIRA BAĞIMSIZLIĞI: hem infra zarfı hem CPU delta örneği süreç-içi sözlüklerdir. Temizlemezsek
    ikinci test birincinin kopyasını okur ve `onbellekten` çivisi kendi kendine geçerdi."""
    for ad in ("_INFRA_CACHE", "_INFRA_CPU_ORNEK"):
        kutu = getattr(api, ad, None)
        if isinstance(kutu, dict):
            monkeypatch.setattr(api, ad, {})
    yield


# ---------------------------------------------------------------- A. KAYIT + YETKİ

def test_iki_uc_da_rota_tablosunda_kayitli():
    yollar = {getattr(r, "path", None) for r in api.app.routes}
    assert "/api/infra" in yollar
    assert "/api/roadmap" in yollar


@pytest.mark.parametrize("yol", ["/api/infra", "/api/roadmap"])
def test_uc_auth_cagiriyor(yol, monkeypatch, sandbox_state):
    """Kaynak metni değil DAVRANIŞ: `_auth` casusu çağrılmazsa kırmızı."""
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(yol))
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert cagrildi == [yol], f"{yol} `_auth` çağırmadı — makine/tahta yüzeyi yetkisiz açık"


@pytest.mark.parametrize("yol", ["/api/infra", "/api/roadmap"])
def test_uc_auth_reddini_yutmaz(yol, monkeypatch, sandbox_state):
    """`_auth` 401 fırlatınca uç onu SESSİZCE yutup 200 dönmemeli (fail-closed)."""
    from fastapi import HTTPException

    def _red(request):
        raise HTTPException(status_code=401, detail="yetkisiz")

    monkeypatch.setattr(api, "_auth", _red)
    r = _client().get(yol)
    assert r.status_code == 401, f"{yol}: yetki reddi yutuldu (durum={r.status_code})"


# ---------------------------------------------------------------- B/C. UYDURMA YASAĞI

def _gerekcesiz_none(kap: dict, iz: str = "") -> list[str]:
    """None olan ama gerekçesi OLMAYAN alanların yolunu döndürür.

    Kabul edilen gerekçe biçimleri: kardeş `<alan>_neden` · kardeş `<alan>_olculemedi_neden` ·
    kabın kendi `olculemedi_neden`i. Üçü de AYNI şartı taşır (dolu, anlamlı bir dizge); kabul edilen
    ADIN genişlemesi zorunluluğu gevşetmez — bu depoda kap düzeyi gerekçeler zaten
    `olculemedi_neden` adıyla yazılıyor (`/api/today.pozisyon_mutabakati`, `/api/market.source`).
    `_neden`/`_nedeni` ile biten alanların KENDİSİ None olabilir — o "ölçüldü, açıklanacak bir şey
    yok" demektir ve bir gerekçenin gerekçesini istemek sonsuz döngüdür."""
    kusurlu: list[str] = []
    kap_gerekcesi = kap.get("olculemedi_neden")
    kap_ok = isinstance(kap_gerekcesi, str) and len(kap_gerekcesi.strip()) >= _GEREKCE_ASGARI
    for k, v in kap.items():
        yol = f"{iz}.{k}" if iz else k
        if isinstance(v, dict):
            kusurlu += _gerekcesiz_none(v, yol)
            continue
        if isinstance(v, list):
            for i, e in enumerate(v):
                if isinstance(e, dict):
                    kusurlu += _gerekcesiz_none(e, f"{yol}[{i}]")
            continue
        if v is not None:
            continue
        if k.endswith("_neden") or k.endswith("_nedeni"):
            continue
        if any(isinstance(kap.get(f"{k}{ek}"), str)
               and len(kap[f"{k}{ek}"].strip()) >= _GEREKCE_ASGARI
               for ek in ("_neden", "_olculemedi_neden")):
            continue
        if kap_ok:
            continue
        kusurlu.append(yol)
    return kusurlu


def test_infra_olculemeyen_her_alan_gerekce_tasir(sandbox_state):
    yuk = _client().get("/api/infra?taze=1").json()
    kusurlu = _gerekcesiz_none(yuk)
    assert not kusurlu, ("gerekçesiz None alan(lar) — UYDURMA YASAĞI: ölçülemeyen alan NEDENİNİ "
                         f"taşımalı: {kusurlu}")


def test_infra_proc_korken_sifir_degil_none_doner(monkeypatch, sandbox_state):
    """macOS SİMÜLASYONU — `/proc` okuyucusu kör edilir. Uç `0` yazarsa (pano "boşta makine" der)
    kırmızı; `None` + neden yazarsa yeşil. Bu çivi platformdan BAĞIMSIZ koşar, yoksa yerelde ve
    canlıda farklı şeyi ölçerdi."""
    monkeypatch.setattr(api, "_proc_oku", lambda ad: None)
    yuk = _client().get("/api/infra?taze=1").json()
    makine = yuk["makine"]
    for alan in ("cpu_yuzde", "uptime_s"):
        assert alan in makine, f"`makine.{alan}` alanı HİÇ YOK — yokluk da bir yalandır"
        assert makine[alan] is None, (f"`/proc` kör ama `makine.{alan}` = {makine[alan]!r} — "
                                      "ölçülemeyen alan sayı UYDURAMAZ")
        gerekce = makine.get(f"{alan}_neden")
        assert isinstance(gerekce, str) and len(gerekce.strip()) >= _GEREKCE_ASGARI, (
            f"`makine.{alan}` None ama `{alan}_neden` yok/kısa: {gerekce!r}")
    bellek = makine["bellek"]
    assert bellek.get("kullanilan_bayt") is None
    assert isinstance(bellek.get("olculemedi_neden"), str) and bellek["olculemedi_neden"].strip()


def test_infra_disk_gercekten_olculur(sandbox_state):
    """`shutil.disk_usage` HER platformda çalışır — yani disk ölçülemedi diyen bir gövde
    tembelliktir. Karşı-yön çivisi: en az bir disk satırı GERÇEK sayı taşımalı ve toplam,
    kullanılan + boş toplamıyla tutarlı olmalı."""
    yuk = _client().get("/api/infra?taze=1").json()
    diskler = yuk["makine"]["disk"]
    assert isinstance(diskler, list) and diskler, "disk listesi boş — `shutil.disk_usage` her yerde var"
    olculen = [d for d in diskler if isinstance(d.get("toplam_bayt"), int)]
    assert olculen, f"hiçbir disk satırı ölçülmemiş: {diskler}"
    for d in olculen:
        assert d["toplam_bayt"] > 0
        assert d["kullanilan_bayt"] + d["bos_bayt"] <= d["toplam_bayt"] + 1


def test_infra_cekirdek_ve_hostname_uydurulmaz(sandbox_state):
    yuk = _client().get("/api/infra?taze=1").json()
    makine = yuk["makine"]
    import os as _os
    import platform as _pf
    assert makine["hostname"] == _pf.node()
    assert makine["cekirdek_n"] == _os.cpu_count()
    assert makine["platform"]["sistem"] == _pf.system()


# ---------------------------------------------------------------- D/E/F. BİLEŞENLER

def test_birim_adlari_diskteki_gercek_dosyalardan_gelir():
    """Ters yönden bakış: ucun bildirdiği HER birim adının `deploy/` altında bir dosyası olmalı."""
    kaynak = api._infra_birim_adlari()
    adlar = kaynak["birimler"]
    assert adlar, "birim listesi boş — deploy/ altında .service dosyaları VAR"
    diskteki = {p.name for p in REPO.glob("deploy/**/*.service")} | {
        p.name for p in REPO.glob("deploy/**/*.timer")}
    for b in adlar:
        dosya = b["dosya"]
        assert dosya in diskteki, f"UYDURMA BİRİM: {b['ad']} ({dosya}) diskte YOK"


def test_sablon_birim_durumu_uydurmaz():
    """MEMORY dersi: `meridian-sprint@.service` düz adla sorgulanınca sahte `inactive` verir."""
    adlar = api._infra_birim_adlari()["birimler"]
    sablonlar = [b for b in adlar if b.get("sablon")]
    assert sablonlar, "şablon birim (`@.service`) tanınmıyor — deploy/ altında VAR"
    for b in sablonlar:
        assert "@" in b["ad"]


def test_systemctl_yoksa_bos_liste_degil_none(monkeypatch, sandbox_state):
    monkeypatch.setattr(api.shutil, "which", lambda ad: None)
    yuk = _client().get("/api/infra?taze=1").json()
    assert yuk["bilesenler"] is None, ("`systemctl` yokken boş liste döndü — boş liste 'bileşen yok' "
                                       "diye okunur, oysa ölçülen şey 'ölçemedim'")
    neden = yuk.get("bilesenler_olculemedi_neden")
    assert isinstance(neden, str) and len(neden.strip()) >= _GEREKCE_ASGARI


def test_systemctl_varsa_bilesen_satirlari_beyanli(monkeypatch, sandbox_state):
    """`systemctl` sahte bir çıktı verir; satırların ŞEKLİ ve dürüstlüğü çivilenir."""
    monkeypatch.setattr(api.shutil, "which", lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)

    def _sahte(birim: str) -> dict:
        return {"LoadState": "loaded", "ActiveState": "active", "SubState": "running",
                "MainPID": "4242", "NRestarts": "3", "MemoryCurrent": "104857600",
                "CPUUsageNSec": "1000000000", "Description": f"{birim} tanımı",
                "ExecMainStartTimestamp": ""}

    monkeypatch.setattr(api, "_systemctl_show", lambda birim: _sahte(birim))
    yuk = _client().get("/api/infra?taze=1").json()
    satirlar = yuk["bilesenler"]
    assert isinstance(satirlar, list) and satirlar
    for s in satirlar:
        assert set(("ad", "durum", "rss_bayt", "cpu_yuzde", "uptime_s")) <= set(s)
        if s.get("sablon"):
            # şablon birim: durum UYDURULMAZ
            assert s["durum"] is None and isinstance(s.get("durum_neden"), str)
        else:
            assert s["durum"] == "active"
            assert s["rss_bayt"] == 104857600
            assert s["restart_n"] == 3
        # İLK ÖRNEK: CPU bir DELTA'dır, tek örnekle ölçülemez → None + neden (0.0 DEĞİL)
        assert s["cpu_yuzde"] is None
        assert isinstance(s.get("cpu_yuzde_neden"), str) and s["cpu_yuzde_neden"].strip()
    assert not _gerekcesiz_none(yuk)


def test_memorycurrent_ayarsiz_sentineli_sayi_olarak_sizmaz(monkeypatch, sandbox_state):
    """systemd `MemoryCurrent`ı ayarsızken 2^64-1 döndürür. Onu 18 exabayt RSS diye basmak,
    ölçülmemiş bir değeri sayıya çevirmenin ders kitabı örneğidir."""
    monkeypatch.setattr(api.shutil, "which", lambda ad: "/usr/bin/systemctl")
    monkeypatch.setattr(api, "_systemctl_show", lambda birim: {
        "LoadState": "loaded", "ActiveState": "inactive", "SubState": "dead",
        "MemoryCurrent": "18446744073709551615", "NRestarts": "0"})
    yuk = _client().get("/api/infra?taze=1").json()
    for s in yuk["bilesenler"]:
        assert s["rss_bayt"] is None, f"sentinel sayı olarak sızdı: {s['rss_bayt']}"
        assert isinstance(s.get("rss_bayt_neden"), str) and s["rss_bayt_neden"].strip()


# ---------------------------------------------------------------- G. ÖNBELLEK BEYANI

def test_infra_onbellegi_beyanli_ve_taze_zorlanabilir(sandbox_state):
    c = _client()
    ilk = c.get("/api/infra").json()
    assert ilk["onbellekten"] is False
    assert isinstance(ilk["hesaplama_ts"], str) and ilk["hesaplama_ts"]
    ikinci = c.get("/api/infra").json()
    assert ikinci["onbellekten"] is True, "ikinci istek yeniden hesapladı — önbellek yok"
    assert ikinci["hesaplama_ts"] == ilk["hesaplama_ts"], "kopya kendini TAZE gibi damgaladı"
    zorlanan = c.get("/api/infra?taze=1").json()
    assert zorlanan["onbellekten"] is False


# ---------------------------------------------------------------- H/I/J. ROADMAP

def test_roadmap_gercek_dosyayi_okur(sandbox_state):
    yuk = _client().get("/api/roadmap").json()
    assert "hata" not in yuk, yuk
    dosya = REPO / yuk["yol"]
    assert dosya.is_file(), f"bildirilen yol diskte yok: {yuk['yol']}"
    assert yuk["bayt"] == dosya.stat().st_size, "bayt sayısı dosyayla eşleşmiyor — gövde sabit mi?"
    bolumler = yuk["bolumler"]
    assert len(bolumler) > 0
    assert yuk["sayim"]["madde_n"] > 0
    numaralar = {b.get("no") for b in bolumler}
    assert "§0" in numaralar, f"§0 bölümü ayrıştırılamadı: {sorted(x for x in numaralar if x)}"


def test_roadmap_madde_sayisi_dosyadaki_madde_sayisiyla_tutarli(sandbox_state):
    """Ayrıştırıcı sessizce yarısını düşürmemeli: gövdedeki madde sayısı dosyadaki üst-düzey
    madde işareti sayısına EŞİT olmalı (kaynak sayımı burada bağımsız yapılır)."""
    metin = (REPO / "ROADMAP.md").read_text(encoding="utf-8")
    # kod bloklarını çıkar: içlerindeki `- ` madde DEĞİLDİR
    disi = re.sub(r"```.*?```", "", metin, flags=re.S)
    beklenen = len([l for l in disi.split("\n") if re.match(r"^\s*[-*] \S", l)])
    yuk = _client().get("/api/roadmap").json()
    assert yuk["sayim"]["madde_n"] == beklenen, (
        f"ayrıştırıcı {yuk['sayim']['madde_n']} madde saydı, dosyada {beklenen} var")


def test_roadmap_ustu_cizili_kapanis_kapali_sayilmaz():
    """`~~✅ KAPANDI~~ — geri alındı` KAPALI DEĞİLDİR; naif `'✅' in satir` ayrıştırıcısı düşer."""
    metin = "\n".join([
        "# T",
        "## §9 SINAMA",
        "- **~~✅ KAPANDI~~ — geri alındı, kalem yeniden açık:** gövde",
        "- **✅ KAPANDI (v1):** gerçekten kapandı",
        "- **BLOKE:** dış bağımlılık",
        "- işaretsiz kalem",
    ])
    yuk = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()), mtime=None)
    maddeler = yuk["bolumler"][0]["maddeler"]
    assert maddeler[0]["ustu_cizili"] is True
    assert maddeler[0]["durum"] != "kapali", ("üstü çizili kapanış KAPALI sayıldı — tahta yalan "
                                              "söylüyor")
    assert maddeler[1]["durum"] == "kapali"
    assert maddeler[2]["durum"] == "bloke"
    assert maddeler[3]["durum"] == "belirsiz", ("işaretsiz kalem 'açık' diye ETİKETLENEMEZ — "
                                                "ölçülmemiş bir durum bir durum değildir")


def test_roadmap_bos_satir_maddeyi_kapatir():
    """GERİLEME ÇİVİSİ — GERÇEK DOSYADA ÖLÇÜLEN KUSUR (2026-08-25).

    İlk sürüm devam satırlarını boş satırda KAPATMIYORDU: ROADMAP §0'ın son maddesine (satır 58)
    sonraki iki paragraf katlandı ve o paragraflardaki **"✅ kapalı" LEJANTI** maddeyi "kapandı"
    diye etiketledi. Yani tahtanın durum sütunu, maddeyle hiç ilgisi olmayan bir açıklama
    satırından geliyordu — ölçülmemiş bir hüküm, ölçülmüş gibi. Çivi hem katlama sınırını hem
    onun durum sütununa yansımasını bağlar."""
    metin = "\n".join([
        "# T", "## §9 SINAMA",
        "- kalem gövdesi burada",
        "  ve bitişik satırda sürüyor",
        "",
        "**LEJANT:** ✅ kapalı · 🔴 aktif",
        "",
        "- ikinci kalem",
    ])
    yuk = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()), mtime=None)
    maddeler = yuk["bolumler"][0]["maddeler"]
    assert len(maddeler) == 2
    assert "bitişik satırda sürüyor" in maddeler[0]["ham"], "bitişik sarma satırı katlanmadı"
    assert "LEJANT" not in maddeler[0]["ham"], ("boş satırdan SONRAKİ paragraf maddeye katlandı — "
                                                "madde gövdesi artık ona ait olmayan metin taşıyor")
    assert maddeler[0]["durum"] == "belirsiz", "yabancı paragraftaki ✅ maddeyi kapalı yaptı"


def test_roadmap_duzyazidaki_isaret_rozet_sayilmaz():
    """GERİLEME ÇİVİSİ — uzun bir bulgu paragrafının ORTASINDAKİ ✅ bir rozet değildir.
    Gerçek dosyada ölçüldü: 763 karakterlik bir `**BULGU (...)**` kalemi bu yüzden `kapali`
    etiketlenmişti."""
    uzun = "gövde " * 60                        # rozet alanını (ilk 160 karakter) aşan düzyazı
    metin = f"# T\n## §9 SINAMA\n- **BULGU:** {uzun} sonra ✅ diye anlatan bir cümle\n"
    m = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                              mtime=None)["bolumler"][0]["maddeler"][0]
    assert m["durum"] == "belirsiz", (f"düzyazıdaki işaret rozet sayıldı (durum={m['durum']}, "
                                      f"kanıt={m['durum_kanit']!r})")


def test_roadmap_govdesi_durum_sozlesmesini_beyan_eder(sandbox_state):
    """`belirsiz`in ne demek olduğu tüketicinin EZBERİNE bırakılamaz: 274 kalem işaretsiz ve
    onları "açık" sayan bir yüzey, ölçülmemiş bir sayıyı yönetim kararına çevirirdi."""
    yuk = _client().get("/api/roadmap").json()
    kapsam = yuk["durum_kapsam"]
    assert isinstance(kapsam, str) and "belirsiz" in kapsam and "açık" in kapsam.lower()


def test_roadmap_alt_bolum_ust_adresini_tasir(sandbox_state):
    """Alt bölüm başlıkları `§N` taşımaz; kalem tek başına gösterilebilmeli."""
    yuk = _client().get("/api/roadmap").json()
    s3 = next(b for b in yuk["bolumler"] if b.get("no") == "§3")
    assert s3["alt_bolumler"], "§3'ün alt bölümü yok — ayrıştırıcı ağacı düzleştirmiş"
    for alt in s3["alt_bolumler"]:
        assert alt["ust_no"] == "§3"


def test_roadmap_kirpma_beyanli():
    """Uzun madde gövdesi kırpılıyorsa gövde bunu SÖYLEMELİ (kırpılmış metni tam sanmak yalandır)."""
    uzun = "x" * 5000
    metin = f"# T\n## §9 SINAMA\n- **UZUN:** {uzun}\n"
    yuk = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()), mtime=None)
    m = yuk["bolumler"][0]["maddeler"][0]
    assert m["ham_kirpildi"] is True
    assert m["ham_uzunluk"] > len(m["ham"])


def test_roadmap_tablolari_ayristirilir_ve_ayri_sayilir(sandbox_state):
    """§2 TAHTA bir TABLODUR, madde listesi değil. Yalnız `- ` maddelerini okuyan bir uç
    `bloke: 0` derdi — ölçmediğini 'yok' diye bildirmek. Gerçek dosyada BLOKE/ASKIDA rozetlerinin
    TAMAMI tablo hücrelerinde yaşıyor (ölçüldü 2026-08-25: satır 292/293/295/296)."""
    yuk = _client().get("/api/roadmap").json()
    s = yuk["sayim"]
    assert s["tablo_n"] > 0 and s["tablo_satir_n"] > 0
    td = s["tablo_durum"]
    assert td["bloke"] + td["askida"] > 0, ("tablo durum sayacı boş — bloklama satırları yutuyor "
                                            f"olabilir: {td}")
    assert "tablo_durum" in s and "durum" in s, "iki sayaç AYRI tutulmalı (çift sayım yasağı)"


def test_roadmap_tabloyu_bos_satir_bolmez():
    """GERİLEME ÇİVİSİ — GERÇEK DOSYADA ÖLÇÜLEN KUSUR (2026-08-25).

    ROADMAP'in §2 tabloları ortalarında boş satır taşıyor (284-296 arasında üç tane). Bitişiklik
    varsayan ilk sürüm bloğu üçe bölüp ayraçsız kalan parçaları SESSİZCE düşürdü: 19 tablo satırı
    kayboldu ve `BLOKE`/`ASKIDA` sayaçları 0 göründü. Sessiz düşürme bu deponun YASA 4 ihlalidir."""
    metin = "\n".join([
        "# T", "## §9 SINAMA",
        "| kalem | durum |",
        "|---|---|",
        "| bir | **BLOKE: operatör** |",
        "",
        "| iki | **ASKIDA: kanıt** |",
        "",
        "| üç | ✅ KAPANDI |",
    ])
    yuk = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()), mtime=None)
    b = yuk["bolumler"][0]
    assert len(b["tablolar"]) == 1, f"boş satır tabloyu böldü: {len(b['tablolar'])} tablo"
    assert b["tablolar"][0]["satir_n"] == 3, "boş satırdan sonraki satırlar sessizce düştü"
    assert yuk["sayim"]["tablo_durum"]["bloke"] == 1
    assert yuk["sayim"]["tablo_durum"]["askida"] == 1
    assert yuk["sayim"]["tablo_durum"]["kapali"] == 1


def test_roadmap_tablo_disi_boru_blogu_sessizce_dusmez():
    """Ayraçsız bir `|` bloğu tablo DEĞİLDİR — ama atlandığı BEYAN edilmeli (gerçek dosyada
    satır 2454'te başlıksız dört satırlık böyle bir blok var)."""
    metin = "# T\n## §9 SINAMA\n| a | b |\n| c | d |\n"
    yuk = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()), mtime=None)
    b = yuk["bolumler"][0]
    assert b["tablolar"] == []
    assert yuk["sayim"]["tablo_atlanan_n"] == 1
    assert b["tablo_atlanan"][0]["neden"].strip()


def test_roadmap_cok_rozetli_tablo_satiri_tek_hukme_indirgenmez():
    """Gerçek satır (290): `| ~~B1 …~~ **H6 ✅ KARAR** | WP11 | **BLOKE: operatör** |` HEM kapanış
    HEM blok rozeti taşıyor. İlk bulduğunu alan sürüm satırı 'kapalı' sayıyordu ve blok görünmez
    oluyordu. Çelişki bir sezgiselle çözülemez — beyan edilir."""
    metin = ("# T\n## §9 SINAMA\n| kalem | wp | kapı |\n|---|---|---|\n"
             "| ~~`B1` iş~~ **H6 ✅ KAPANDI** | WP11 | **BLOKE: operatör** |\n")
    r = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                              mtime=None)["bolumler"][0]["tablolar"][0]["satirlar"][0]
    assert r["durum"] is None, f"çelişkili satır tek hükme indirgendi: {r['durum']!r}"
    assert isinstance(r["durum_neden"], str) and r["durum_neden"].strip()
    assert set(r["hucre_durum"]) >= {"kapali", "bloke"}
    assert {k["durum"] for k in r["durum_kanitlari"]} == {"kapali", "bloke"}


def test_roadmap_sarilmis_duzyazi_satiri_tablo_sanilmaz():
    """GERİLEME ÇİVİSİ (gerçek dosya satır 3639): sarılmış bir düzyazı satırı `|Δclose|/c …` diye
    başlıyor. "Boru ile başlar" kuralı onu tablo sanıp maddenin gövdesinden KOPARIYORDU."""
    metin = "# T\n## §9 SINAMA\n- kalem gövdesi\n  |Δclose|/c oranı devam ediyor\n"
    b = api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                              mtime=None)["bolumler"][0]
    assert b["tablolar"] == [] and b.get("tablo_atlanan") is None
    assert "Δclose" in b["maddeler"][0]["ham"], "düzyazı satırı tablo sanılıp maddeden koparıldı"


def test_roadmap_ozet_govdeleri_soker_ama_onbellegi_kirletmez(sandbox_state):
    """Tam gövde ÖLÇÜLDÜ: 383 KB ve uygulamada gzip ara katmanı yok. `?ozet=1` yapıyı bırakır.
    KRİTİK: özetleme önbellekteki ağacı YERİNDE budamamalı — budasaydı sonraki tam istek sessizce
    gövdesiz dönerdi (bayat-yalan sınıfı)."""
    c = _client()
    tam_once = c.get("/api/roadmap").json()
    o = c.get("/api/roadmap?ozet=1")
    ozet = o.json()
    assert ozet["suzgec"]["ozet"] is True and ozet["ozet_beyani"].strip()
    assert len(o.content) < len(c.get("/api/roadmap").content) // 2, "özet gövdeyi küçültmedi"
    m = ozet["bolumler"][1]["maddeler"][0]
    assert "ham" not in m and m["durum"] and m["ham_uzunluk"] > 0
    tam_sonra = c.get("/api/roadmap").json()
    assert tam_sonra["sayim"] == tam_once["sayim"]
    assert "ham" in tam_sonra["bolumler"][1]["maddeler"][0], "özet önbellekteki ağacı budadı"


def test_roadmap_dosya_yoksa_durust_hata(monkeypatch, sandbox_state, tmp_path):
    monkeypatch.setattr(api, "_roadmap_yolu", lambda: tmp_path / "YOK.md")
    r = _client().get("/api/roadmap")
    yuk = r.json()
    assert isinstance(yuk.get("hata"), str) and yuk["hata"].strip()
    assert isinstance(yuk.get("yol"), str) and "YOK.md" in yuk["yol"]
    assert "bolumler" not in yuk or yuk["bolumler"] is None, (
        "dosya yokken boş bölüm listesi döndü — 'yol haritası boş' diye okunur")


def test_roadmap_bolum_suzgeci_calisir(sandbox_state):
    yuk = _client().get("/api/roadmap?bolum=§0").json()
    assert len(yuk["bolumler"]) == 1
    assert yuk["bolumler"][0]["no"] == "§0"
    assert yuk["suzgec"]["bolum"] == "§0"


def test_roadmap_suzgecli_sayim_tek_kapsamli(sandbox_state):
    """Sayımın yarısı süzgeçli yarısı belge-geneli OLAMAZ: okuyan hangi sayının neyi saydığını
    ayırt edemez. §2 iyi bir sınav — kalemleri MADDE değil TABLO satırı olduğu için `madde_n`
    süzgeçlendiğinde 0'a düşer, `tablo_satir_n` düşmezse tutarsızlık ölçülebilir hâle gelir."""
    c = _client()
    tam = c.get("/api/roadmap").json()["sayim"]
    suz = c.get("/api/roadmap?bolum=§2").json()["sayim"]
    assert tam["kapsam"] and suz["kapsam"] and tam["kapsam"] != suz["kapsam"]
    for alan in ("madde_n", "tablo_satir_n", "tablo_n", "alt_bolum_n"):
        assert suz[alan] <= tam[alan], f"{alan} süzgeçte belge-genelinden büyük — kapsam karışmış"
    assert suz["tablo_satir_n"] < tam["tablo_satir_n"], (
        "tablo sayacı süzgeçle daralmadı — belge-geneli değer süzgeçli sayımın içinde kalmış")
    assert sum(suz["tablo_durum"].values()) == suz["tablo_satir_n"]
    assert sum(suz["durum"].values()) == suz["madde_n"]


# ---------------------------------------------------------------- K. JSON SÖZLEŞMESİ

@pytest.mark.parametrize("yol", ["/api/infra?taze=1", "/api/roadmap"])
def test_govde_allow_nan_false_ile_serilesir(yol, sandbox_state):
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    json.dumps(r.json(), allow_nan=False)       # NaN/Inf/numpy sızarsa burada patlar
    assert "NaN" not in r.text and "Infinity" not in r.text
