"""BEKLENMEDİK BİRİM — TERS YÖNÜN PANO OKUYUCUSU · YASA 6 çivisi (v354, 2026-09-01)

NE ÖLÇÜLÜYOR. `/api/infra` 2026-09-01 gecesinden beri `beklenmedik_birimler` +
`beklenmedik_birimler_neden` + `beklenmedik_olcum` yayınlıyor (`api.py::_infra_beklenmedik`,
çivileri `tests/test_pano_altyapi_v287.py` L bölümü). Alan YAYINDAYDI ama pano yüzeyinde
HİÇBİR okuyucusu yoktu: `Bilesenler.tsx` bu üç alana hiç dokunmuyordu. YASA 6'nın tanımı
budur — okunmayan artefakt üretilmemişten farksızdır; bacağı indiren ajan bunu kendi açık
kalemi olarak beyan etti (ROADMAP TSK-086).

ALANIN TAŞIDIĞI GERÇEK — TERS YÖN: `bilesenler` "depoda var, makinede EKSİK" olanı gösterir;
bu alan "makinede DURUYOR, depoda YOK" olanı. Ölçülmüş vaka (canlı A1, 2026-09-01):
`meridian-dash.service` makinede duruyordu ve `deploy/` ağacında karşılığı yoktu — pano
"bileşenler listelendi" derken listelenmeyen bir birim vardı.

ÜÇ TUZAK BURADA AÇIKÇA KARŞILANIYOR

  1) `[]` İLE `null` ASLA KARIŞMAZ. Boş liste "ÖLÇTÜK, fazlalık yok"tur; `null` "ÖLÇEMEDİK".
     İkisini aynı çizmek, panoya ölçülmemiş bir TEMİZLİK beyan ettirirdi — ucun kendi çivisi
     (v287 `test_temiz_makinede_BOS_LISTE_doner_None_DEGIL`) bunu uçta kapatıyor; bu dosya
     EKRANDA kapatıyor. Üçüncü hâl de ayrı: alan HİÇ gelmediyse (eski gövde) `false`/boş
     VARSAYILMAZ, "ölçülemedi"ye düşer.

  2) BOŞ LİSTE ROZET ÇİZDİRMEZ. Temiz makinede "0 beklenmedik birim" rozeti, her gün her
     bakışta okunan ve hiçbir zaman iş çıkarmayan bir gürültüdür; sinyal gürültüde kaybolur.
     Sessizlik burada bir karardır — ve karşı yönü ÇİVİLİ: "ölçülemedi" hâli SESSİZ DEĞİLDİR,
     çünkü o hâlde temizlik iddia edilemez.

  3) `durum` SÜTUNU "KOŞUYOR MU" DEMEK DEĞİLDİR. `list-unit-files` STATE sütunu systemd
     `UnitFileState`tir (enabled/disabled/static/masked), `ActiveState` DEĞİL — ucun kendi
     beyanı `beklenmedik_olcum.durum_alani`dır. Ekranda `disabled` görüp "duruyor" diye
     okumak, ölçülmemiş bir hüküm kurmaktır; beyan ekranda TAŞINMALI.

NEDEN ÖLÇÜM DAVRANIŞ ÜZERİNDE. Alt-dize tuzağı bu depoda tekrar tekrar yakalandı: bir alan
adının kaynakta (hele yorumda) geçmesi OKUNDUĞUNU kanıtlamaz. Bu yüzden karar veren üç saf
işlev TSX'ten SÖKÜLÜP esbuild ile çevriliyor ve node'da GERÇEKTEN koşturuluyor. Sökme/çeviri
yardımcıları `test_infra_okuyucu_v316`ten İTHAL EDİLİYOR, kopyalanmıyor (tek-kaynak yasası:
aynı ayrıştırıcının iki kopyası sessizce ayrışır).

VE BİR KÖPRÜ ÇİVİSİ: ucun GERÇEK gövdesi (TestClient, saplı `systemctl`) doğrudan pano
okuyucusuna veriliyor. İki tarafın alan adları ayrıştığı gün — uçta `beklenmedik_birimler`,
panoda başka bir ad — davranış çivileri kurgu sözlükleriyle YEŞİL kalırdı; köprü öter.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meridian import api

# TEK-KAYNAK: TSX sökme/çeviri ayrıştırıcısı v316'da yazıldı ve orada çivili. İkinci bir kopya
# yazmak, aynı gerçeğin iki sürümünü üretirdi (bu deponun terfi etmiş yasası). İthal kırılırsa
# SESSİZ kalmaz — toplama anında patlar.
from tests.test_infra_okuyucu_v316 import (  # noqa: E402
    BILESENLER,
    ESBUILD,
    UCTIPLERI,
    _govde,
    _islev,
    _soy,
)

KOK = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(not BILESENLER.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")

_ARAC_YOK = shutil.which("node") is None or not ESBUILD.exists()
arac_gerek = pytest.mark.skipif(_ARAC_YOK, reason="node/esbuild yok — TSX davranışı bu ağaçta koşturulamaz")

#: Panoya eklenen SAF okuyucular. Hepsi tek nesne alır, hüküm döndürür, JSX taşımaz.
OKUYUCULAR = ("beklenmedikOku", "beklenmedikDurumOku", "beklenmedikBedelOku")

_GEREKCE_ASGARI = 20          # "yok" bir gerekçe değildir

#: ÖLÇÜM ARACININ KENDİ ALT SÜREÇLERİ SAPLAMANIN DIŞINDA KALMALI. Köprü çivisi `subprocess.run`u
#: SÜREÇ GENELİNDE saplıyor (v287 emsali: komutun kendisi de sözleşmenin parçası) — esbuild ve
#: node çağrıları o saplamaya düşerse ölçüm aracı sessizce `returncode=1` alır ve çivi, ölçtüğü
#: şey yüzünden DEĞİL kendi hattı yüzünden kırmızıya döner. İlk koşumda tam bu oldu.
_GERCEK_RUN = subprocess.run

_CEVRILMIS: str | None = None


def _kaynak() -> str:
    return _soy(BILESENLER.read_text(encoding="utf-8"))


def _cevir() -> str:
    """Üç saf okuyucuyu TSX'ten söküp esbuild ile JS'e çevirir (bir kez)."""
    global _CEVRILMIS
    if _CEVRILMIS is None:
        ham = _kaynak()
        parcalar = []
        for ad in OKUYUCULAR:
            imza = f"export function {ad}("
            assert imza in ham, f"`{ad}` DIŞA AKTARILMIŞ bir işlev değil — davranışı ölçülemez"
            parcalar.append(_islev(ham, imza))
        ts = "\n".join(parcalar).replace("export function", "function")
        cp = _GERCEK_RUN([str(ESBUILD), "--loader=ts"], input=ts, capture_output=True,
                         text=True, timeout=60)
        assert cp.returncode == 0, f"esbuild çeviremedi: {cp.stderr}"
        _CEVRILMIS = cp.stdout
    return _CEVRILMIS


def _cagir(ad: str, *argumanlar) -> object:
    """Sökülen okuyucuyu node'da GERÇEKTEN çağırır ve dönen hükmü verir."""
    js = (_cevir() + "\nconst __a = " + json.dumps(list(argumanlar), ensure_ascii=False)
          + f";\nconsole.log(JSON.stringify({ad}(...__a)));\n")
    with tempfile.TemporaryDirectory() as d:
        yol = Path(d) / "olcum.mjs"
        yol.write_text(js, encoding="utf-8")
        cp = _GERCEK_RUN(["node", str(yol)], capture_output=True, text=True, timeout=60)
    assert cp.returncode == 0, f"node çalıştıramadı: {cp.stderr}"
    return json.loads(cp.stdout.strip().split("\n")[-1])


# ---------------------------------------------------------------------------
# POZİTİF KONTROL — ölçüm hattının kendisi koşuyor mu
# ---------------------------------------------------------------------------

@arac_gerek
def test_olcum_hatti_GERCEKTEN_KOSUYOR():
    """Sıfır bulgunun anlamı olması için hattın çalıştığı kanıtlanmalı (test_codelaw_v59
    disiplini): sökme + esbuild + node zincirinin bir yerinde sessizce boş dönseydi aşağıdaki
    davranış çivilerinin hepsi ANLAMSIZ YEŞİL olurdu."""
    js = _cevir()
    for ad in OKUYUCULAR:
        assert f"function {ad}" in js, f"`{ad}` çeviriye girmemiş"
    assert _cagir("beklenmedikOku", {"beklenmedik_birimler": []})["hal"] == "temiz"


# ---------------------------------------------------------------------------
# 1) `[]` İLE `null` AYRI — ÜÇÜNCÜ HÂL DE AYRI
# ---------------------------------------------------------------------------

@arac_gerek
def test_BOS_LISTE_OLCULDU_DEMEKTIR_temiz():
    """`[]` ucun "ÖLÇTÜM ve fazlalık YOK" hükmüdür — belirsizlik değil, sonuçtur."""
    o = _cagir("beklenmedikOku", {"beklenmedik_birimler": [], "beklenmedik_birimler_neden": None})
    assert o["hal"] == "temiz", f"boş liste `{o['hal']}` diye okundu"
    assert o["birimler"] == [] and o["neden"] is None, (
        "temiz hâl gerekçe/birim taşıyor — ekranda açıklanacak bir şey yok")


@arac_gerek
def test_NULL_TEMIZ_DEGILDIR_olculemedi():
    """`null` "ÖLÇEMEDİK"tir. Temiz sayılırsa pano ölçülmemiş bir temizlik beyan eder —
    uçta kapatılan kusurun (v287) EKRAN tarafı."""
    neden = "`systemctl` bu makinede yok (Darwin) — makinede duran birimler sayılamadı"
    o = _cagir("beklenmedikOku",
               {"beklenmedik_birimler": None, "beklenmedik_birimler_neden": neden})
    assert o["hal"] == "olculemedi", f"ölçülemeyen bacak `{o['hal']}` diye okundu"
    assert o["neden"] == neden, "ucun gerekçesi taşınmıyor — okuyucu iddiayı doğrulayamaz"
    assert o["birimler"] == [], "ölçülemeyen bacak birim listesi uyduruyor"


@arac_gerek
def test_ALAN_HIC_GELMEDIYSE_de_olculemedi():
    """ÜÇÜNCÜ HÂL: eski/kırpılmış gövde alanı HİÇ göndermez. `[]` varsaymak, hiç sorulmamış
    bir soruya olumlu cevap uydurmaktır."""
    o = _cagir("beklenmedikOku", {})
    assert o["hal"] == "olculemedi", f"alan gelmediğinde `{o['hal']}` hükmü kuruldu"
    assert isinstance(o["neden"], str) and len(o["neden"].strip()) >= _GEREKCE_ASGARI, (
        f"gerekçe uydurulmadı ama BOŞ da bırakıldı: {o['neden']!r}")


@arac_gerek
def test_DOLU_LISTE_var_hali_ve_birimleri_TASIR():
    o = _cagir("beklenmedikOku", {"beklenmedik_birimler": [
        {"birim": "meridian-dash.service", "durum": "disabled", "durum_neden": None},
        {"birim": "meridian-eski.timer", "durum": None, "durum_neden": "STATE sütunu gelmedi"}]})
    assert o["hal"] == "var"
    assert [b["birim"] for b in o["birimler"]] == ["meridian-dash.service", "meridian-eski.timer"]
    assert o["neden"] is None, "ölçülmüş bir liste 'ölçülemedi' gerekçesi taşıyor"


# ---------------------------------------------------------------------------
# 2) SATIR DURUMU UYDURULMAZ
# ---------------------------------------------------------------------------

@arac_gerek
def test_SATIR_DURUMU_OLCULDUYSE_AYNEN_gecer():
    d = _cagir("beklenmedikDurumOku", {"birim": "meridian-dash.service", "durum": "disabled"})
    assert d["olculdu"] is True and d["metin"] == "disabled" and d["neden"] is None


@arac_gerek
def test_SATIR_DURUMU_OLCULEMEDIYSE_UYDURULMAZ():
    """`durum` yoksa/boşsa "kapalı" DEĞİL "ölçülemedi"dir — üç giriş de aynı hükmü vermeli."""
    gerekce = "`list-unit-files` bu satırda STATE sütunu vermedi"
    for govde in ({"durum": None, "durum_neden": gerekce},
                  {"durum": "", "durum_neden": gerekce},
                  {"durum": "   ", "durum_neden": gerekce}):
        d = _cagir("beklenmedikDurumOku", govde)
        assert d["olculdu"] is False, f"{govde} → durum ölçülmüş sayıldı"
        assert d["metin"] is None, f"{govde} → ölçülmemiş durum metne çevrildi: {d['metin']!r}"
        assert d["neden"] == gerekce, f"{govde} → ucun gerekçesi taşınmadı"
    # Gerekçe HİÇ gelmediyse uydurulmaz ama boş da bırakılmaz.
    bos = _cagir("beklenmedikDurumOku", {"birim": "x.service"})
    assert bos["olculdu"] is False
    assert isinstance(bos["neden"], str) and len(bos["neden"].strip()) >= _GEREKCE_ASGARI


# ---------------------------------------------------------------------------
# 3) BEDEL VE KAPSAM EKRANDA TAŞINIR
# ---------------------------------------------------------------------------

@arac_gerek
def test_BEDEL_OKUYUCUSU_kapsami_ve_sayimi_TASIR():
    """BEDEL YASASI: bacak yalnız dar bir deseni sorar ve desene uymayan birimlere KÖRDÜR.
    Kazanç ekranda, bedel ekranda değilse körlüğün belirtisi hiçbir şeydir (vaka @bekci)."""
    b = _cagir("beklenmedikBedelOku", {"beklenmedik_olcum": {
        "durum_alani": "STATE sütunu `UnitFileState`tir, `ActiveState` DEĞİLDİR",
        "kapsam_disi": "yalnız `meridian-*` deseni sorgulanır; desene uymayanlar görünmez",
        "makinedeki_birim_n": 4, "makinedeki_birim_n_neden": None, "repo_birim_n": 12}})
    assert "UnitFileState" in (b["durumAlani"] or ""), "durum sütununun NE OLDUĞU taşınmıyor"
    assert "meridian-*" in (b["kapsam"] or ""), "taramanın DAR kapsamı ekrana taşınmıyor"
    assert b["makinedeN"] == 4 and b["repoN"] == 12


@arac_gerek
def test_BEDEL_OLCULEMEDIGINDE_SIFIR_UYDURULMAZ():
    """Sayım ölçülemediğinde `0` yazmak, "hiç birim yok" diye okunur — uydurma yasağı."""
    b = _cagir("beklenmedikBedelOku", {"beklenmedik_olcum": {
        "makinedeki_birim_n": None,
        "makinedeki_birim_n_neden": "`systemctl` koşturulamadı — makinedeki birimler sayılmadı"}})
    assert b["makinedeN"] is None, "ölçülmeyen sayım 0'a çevrildi"
    assert isinstance(b["makinedeNeden"], str) and b["makinedeNeden"].strip()
    # Künye bloğu HİÇ gelmediyse de sessizce sıfırlanmaz.
    yok = _cagir("beklenmedikBedelOku", {})
    assert yok["makinedeN"] is None and yok["repoN"] is None
    assert yok["kapsam"] is None and yok["durumAlani"] is None


# ---------------------------------------------------------------------------
# 4) KÖPRÜ — UCUN GERÇEK GÖVDESİ PANO OKUYUCUSUNA VERİLİR
# ---------------------------------------------------------------------------

_LIST_CIKTISI = (
    "meridian-backup.service              enabled   enabled\n"
    "meridian-backup.timer                enabled   enabled\n"
    "meridian-sprint@.service             static    -\n"
    "meridian-dash.service                disabled  disabled\n"
    "14 unit files listed.\n"          # dipnot: birim DEĞİLDİR
)


@pytest.fixture(autouse=True)
def _onbellekleri_bosalt(monkeypatch):
    """SIRA BAĞIMSIZLIĞI: infra zarfı ve CPU delta örneği süreç-içi sözlüklerdir."""
    for ad in ("_INFRA_CACHE", "_INFRA_CPU_ORNEK"):
        kutu = getattr(api, ad, None)
        if isinstance(kutu, dict):
            monkeypatch.setattr(api, ad, {})
    yield


def _sahte_systemctl(monkeypatch, cikti: str):
    """`subprocess.run` saplaması (v287 emsali): `show` çağrıları bu çivinin konusu değil."""
    import subprocess as _sp

    def _run(argv, *a, **kw):
        if "list-unit-files" in argv:
            return _sp.CompletedProcess(argv, 0, cikti, "")
        return _sp.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(_sp, "run", _run)
    monkeypatch.setattr(api.shutil, "which",
                        lambda ad: "/usr/bin/systemctl" if ad == "systemctl" else None)


@arac_gerek
def test_UCUN_GERCEK_GOVDESI_PANO_OKUYUCUSUNDAN_GECER(monkeypatch, sandbox_state):
    """İKİ TARAF TEK SÖZLEŞME: kurgu sözlüklerle koşan davranış çivileri, uç alan adını
    değiştirdiği gün YEŞİL kalırdı. Bu çivi ucun GERÇEK gövdesini pano okuyucusuna verir."""
    _sahte_systemctl(monkeypatch, _LIST_CIKTISI)
    yuk = TestClient(api.app).get("/api/infra?taze=1").json()

    o = _cagir("beklenmedikOku", yuk)
    assert o["hal"] == "var", (
        f"ucun gövdesi panoda `{o['hal']}` diye okundu — alan adları ayrışmış olabilir: "
        f"{sorted(k for k in yuk if 'beklenmedik' in k)}")
    assert [b["birim"] for b in o["birimler"]] == ["meridian-dash.service"]

    d = _cagir("beklenmedikDurumOku", o["birimler"][0])
    assert d["olculdu"] is True and d["metin"] == "disabled"

    b = _cagir("beklenmedikBedelOku", yuk)
    assert b["makinedeN"] == 4, f"makinede sayılan birim adedi taşınmadı: {b}"
    assert b["kapsam"] and b["durumAlani"], "bedel/kapsam beyanı panoya ulaşmıyor"


@arac_gerek
def test_SYSTEMCTL_YOKKEN_PANO_TEMIZ_DEMEZ(monkeypatch, sandbox_state):
    """Yerel macOS'un GERÇEK hâli: `systemctl` yok → uç `None` + gerekçe döner. Pano bunu
    "temiz" diye okursa, ölçülmemiş bir temizlik ekrana yazılmış olur."""
    monkeypatch.setattr(api.shutil, "which", lambda ad: None)
    yuk = TestClient(api.app).get("/api/infra?taze=1").json()
    o = _cagir("beklenmedikOku", yuk)
    assert o["hal"] == "olculemedi", f"ölçülemeyen bacak panoda `{o['hal']}` diye okundu"
    assert isinstance(o["neden"], str) and len(o["neden"].strip()) >= _GEREKCE_ASGARI


# ---------------------------------------------------------------------------
# 5) OKUYUCULAR ÖKSÜZ DEĞİL — EKRANA BAĞLILAR
# ---------------------------------------------------------------------------

def test_BLOK_KARTA_BAGLI():
    """Okuyucular hesaplanıp çizilmezse YASA 6 boşluğu kapanmaz: alan hâlâ okunmuyordur."""
    ham = _kaynak()
    assert re.search(r"function BeklenmedikBirimler\(", ham), (
        "`BeklenmedikBirimler` diye bir blok YOK — alan hâlâ ekransız")
    assert re.search(r"<BeklenmedikBirimler\b[^>]*\bg=\{g\}", ham), (
        "blok Altyapı kartının gövdesine bağlanmamış — hesaplanan hüküm ekrana çıkmıyor")


def test_BLOK_UC_OKUYUCUYU_DA_CAGIRIR():
    g = _govde(_kaynak(), "function BeklenmedikBirimler(")
    for ad in OKUYUCULAR:
        assert re.search(rf"\b{ad}\s*\(", g), f"`{ad}` blokta çağrılmıyor — öksüz okuyucu"


def test_BOS_LISTEDE_ROZET_CIZILMEZ():
    """SESSİZLİK BİR KARARDIR: temiz makinede rozet çizmek, hiçbir zaman iş çıkarmayan bir
    gürültü üretirdi. Erken çıkış BLOĞUN KENDİSİNDE olmalı — çağıran tarafta değil, yoksa
    ikinci bir çağıran eklendiği gün gürültü sessizce geri gelir."""
    g = _govde(_kaynak(), "function BeklenmedikBirimler(")
    assert re.search(r'hal\s*===\s*"temiz"[\s\S]{0,60}?return null', g), (
        "temiz hâlde blok `null` döndürmüyor — boş listede rozet/liste çizilir ve pano her gün "
        "okunan ama hiçbir zaman iş çıkarmayan bir satır kazanır")


def test_OLCULEMEDI_HALI_SESSIZ_DEGILDIR():
    """(2)'nin TERS YÖNÜ — gürültüyü susturayım derken SİNYALİ susturmak kusuru ikiye katlar.
    `temiz` dışındaki tek erken çıkış olmamalı: ölçülemeyen bacak ekranda görünür."""
    g = _govde(_kaynak(), "function BeklenmedikBirimler(")
    assert len(re.findall(r"return null", g)) == 1, (
        "blokta birden fazla sessiz çıkış var — 'ölçülemedi' de susturulmuş olabilir")
    assert re.search(r'hal\s*===\s*"olculemedi"', g), (
        "ölçülemeyen hâlin ayrı bir ekran karşılığı yok — 'ölçemedik' ile 'temiz' aynı görünür")


def test_DIKKAT_TONU_KOMSUDAN_GELIR_YENI_RENK_ICAT_EDILMEZ():
    """TASARIM DİLİ: rozet tonu bu kartın kendi ton sözlüğünden okunur. Yeni bir hue bandı
    icat etmek, rezerve renk kaydını (mod/nav/şiddet) sessizce delerdi."""
    g = _govde(_kaynak(), "function BeklenmedikBirimler(")
    assert re.search(r"TON_METNI\.dikkat|TON_METNI\[\s*[\"']dikkat[\"']\s*\]", g), (
        "rozet rengi kartın ton sözlüğünden gelmiyor — elle yazılmış bir renk tasarım dilinden kopar")
    assert re.search(r"TON_NOKTASI\.dikkat|TON_NOKTASI\[\s*[\"']dikkat[\"']\s*\]", g), (
        "rozet noktası ton sözlüğünden gelmiyor")


# Hangi alan HANGİ İŞLEVDE okunmalı. "Dosyada bir yerde geçiyor" YETMEZ (v316 dersi): alan bir
# yorumda ya da tip beyanında geçebilir ve hiçbir şey kanıtlamaz.
OKUYUCU_HARITASI = (
    ("beklenmedikOku", ("beklenmedik_birimler", "beklenmedik_birimler_neden")),
    ("beklenmedikDurumOku", ("durum", "durum_neden")),
    ("beklenmedikBedelOku", ("beklenmedik_olcum",)),
)


def test_UC_ALANIN_UI_OKUYUCUSU_VAR():
    """YASA 6'nın kendisi: uç bu alanları yayınlıyorsa panoda OKUNUYOR olmalı. Ölçüm ÖZELLİK
    ERİŞİMİNİ, üstelik BELİRLİ BİR İŞLEVİN GÖVDESİNDE arar (yorumlar soyuldu; `uctipleri.ts`
    ölçüme hiç girmiyor — tip beyanı okuyucu DEĞİLDİR)."""
    ham = _kaynak()
    for islev, alanlar in OKUYUCU_HARITASI:
        g = _govde(ham, f"function {islev}(")
        for alan in alanlar:
            assert re.search(rf"\.{alan}\b", g), (
                f"`{alan}` `{islev}` içinde okunmuyor — YASA 6 borcu kapanmadı")


def test_TIP_BEYANI_UCUN_SOZLESMESINI_TASIR():
    """Tip beyanı okuyucu değildir ama SÖZLEŞMEdir: `[]` ile `null` ayrımı tipte de durmalı,
    yoksa bir gün `?: Birim[]` yazılır ve derleyici üçüncü hâli görmez."""
    s = UCTIPLERI.read_text(encoding="utf-8")
    for alan in ("beklenmedik_birimler", "beklenmedik_birimler_neden", "beklenmedik_olcum"):
        assert re.search(rf"^\s*readonly {alan}\?:", s, re.M), f"`{alan}` tipte beyan edilmemiş"
    m = re.search(r"readonly beklenmedik_birimler\?:\s*([^;]+);", s)
    assert m and "null" in m.group(1), (
        f"`beklenmedik_birimler` tipi `null`ı taşımıyor ({m.group(1) if m else '—'}) — 'ölçemedik' "
        "hâli tipten silinirse ekranda da silinir")
