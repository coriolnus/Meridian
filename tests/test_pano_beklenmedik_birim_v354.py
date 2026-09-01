"""BEKLENMEDİK BİRİM — TERS YÖNÜN PANO OKUYUCUSU · YASA 6 çivisi (v354, 2026-09-01)

NE ÖLÇÜLÜYOR. `/api/infra` 2026-09-01 gecesinden beri `beklenmedik_birimler` +
`beklenmedik_birimler_neden` + `beklenmedik_olcum` yayınlıyor (`api.py::_infra_beklenmedik`,
çivileri `tests/test_pano_altyapi_v287.py` L bölümü). Alan YAYINDAYDI ama pano yüzeyinde
HİÇBİR okuyucusu yoktu: `Bilesenler.tsx` bu üç alana hiç dokunmuyordu. YASA 6'nın tanımı
budur — okunmayan artefakt üretilmemişten farksızdır (ROADMAP TSK-086).

ALANIN TAŞIDIĞI GERÇEK — TERS YÖN: `bilesenler` "depoda var, makinede EKSİK" olanı gösterir;
bu alan "makinede DURUYOR, depoda YOK" olanı. Ölçülmüş vaka (canlı A1, 2026-09-01):
`meridian-dash.service` makinede duruyordu ve `deploy/` ağacında karşılığı yoktu.

ÜÇ TUZAK BURADA AÇIKÇA KARŞILANIYOR

  1) `[]` İLE `null` ASLA KARIŞMAZ. Boş liste "ÖLÇTÜK, fazlalık yok"tur; `null` "ÖLÇEMEDİK".
     İkisini aynı çizmek, panoya ölçülmemiş bir TEMİZLİK beyan ettirirdi. Üçüncü hâl de ayrı:
     alan HİÇ gelmediyse (eski gövde) `[]` VARSAYILMAZ.

  2) BOŞ LİSTE ROZET ÇİZDİRMEZ. Temiz makinede "0 beklenmedik birim" rozeti, her gün okunan ve
     hiçbir zaman iş çıkarmayan bir gürültüdür. Sessizlik burada bir karardır — ve karşı yönü
     ÇİVİLİ: "ölçülemedi" hâli SESSİZ DEĞİLDİR.

  3) `durum` SÜTUNU "KOŞUYOR MU" DEMEK DEĞİLDİR. `list-unit-files` STATE sütunu systemd
     `UnitFileState`tir, `ActiveState` DEĞİL — ucun beyanı `beklenmedik_olcum.durum_alani`dır
     ve ekranda TAŞINMALI.

HÜKÜM DOĞRU KURULUP EKRANA HİÇ ÇIKMAYABİLİR — BU ÖLÇÜLDÜ (görev incelemesi, 2026-09-01).
İlk sürümde saf okuyucular doğruydu, kaynak-biçimi çivileri yeşildi, blok da JSX'te duruyordu;
ama blok kartın GÖVDESİNİN İÇİNDEYDİ ve gövde `bilesenler` ölçülemediğinde ERKEN ÇIKIYORDU.
Sonuç: `systemctl` olmayan her makinede — yani yerel geliştirmenin BASKIN hâlinde — ikinci
bacağın "ölçemedik" beyanı ekrana HİÇ düşmüyordu, üstelik 18 çivi yeşilken. Ders: saf-işlev
çağrısı bir MONTAJ kanıtı DEĞİLDİR. Bu yüzden aşağıda ikinci bir ölçüm katmanı var — bileşen
`react-dom/server` ile GERÇEKTEN çizilir ve HTML çıktısı okunur.

NEDEN ÖLÇÜM DAVRANIŞ ÜZERİNDE. Alt-dize tuzağı bu depoda tekrar tekrar yakalandı: bir alan
adının kaynakta (hele yorumda) geçmesi OKUNDUĞUNU kanıtlamaz. Sök/çevir/koştur ve çizim hattı
`tests/conftest.py`te TEK yerde durur; v316 de aynı hattı kullanır (tek-kaynak yasası — bu
dosyanın ilk sürümü hattı KOPYALAYIP "ithal ediliyor" diye beyan etmişti).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meridian import api
from tests.conftest import (
    ESBUILD_YOLU,
    tsx_bileseni_cizdir,
    tsx_islev_cagir,
    tsx_islev_govdesi,
    tsx_saf_islevleri_cevir,
    tsx_yorumlari_soy,
)

KOK = Path(__file__).resolve().parent.parent
SISTEM = KOK / "ui" / "src" / "pano" / "yuzeyler" / "sistem"
BILESENLER = SISTEM / "Bilesenler.tsx"
UCTIPLERI = SISTEM / "uctipleri.ts"

pytestmark = pytest.mark.skipif(not BILESENLER.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")

_ARAC_YOK = shutil.which("node") is None or not ESBUILD_YOLU.exists()
arac_gerek = pytest.mark.skipif(_ARAC_YOK, reason="node/esbuild yok — TSX davranışı bu ağaçta koşturulamaz")

#: UCUN YAYINLADIĞI ALANLAR — TEK KAYNAK. Ad dört ayrı çivide geçiyor (okuyucu haritası, tip
#: sözleşmesi, köprü hata metni, gövde kurgusu); dördünü elle yazmak, birini değiştirip ötekileri
#: unutmanın açık davetiydi.
ALAN_LISTE = "beklenmedik_birimler"
ALAN_NEDEN = "beklenmedik_birimler_neden"
ALAN_OLCUM = "beklenmedik_olcum"
UC_ALANLARI = (ALAN_LISTE, ALAN_NEDEN, ALAN_OLCUM)

#: Panoya eklenen SAF okuyucular. Hepsi tek nesne alır, hüküm döndürür, JSX taşımaz.
OKUYUCULAR = ("beklenmedikOku", "beklenmedikDurumOku", "beklenmedikBedelOku")

#: EKRANDA ARANAN ÇAPALAR — çizim çivileri bu metinleri HTML'de arar.
METIN_OLCULEMEDI = "Makinede fazladan duran birimler bu ölçümde sayılamadı"
METIN_VAR = "Makinede duruyor, depoda karşılığı yok"
METIN_KART = "Meridian bileşenleri"

_GEREKCE_ASGARI = 20          # "yok" bir gerekçe değildir

#: ÖLÇÜM ARACININ KENDİ ALT SÜREÇLERİ SAPLAMANIN DIŞINDA KALMALI. Köprü çivisi `subprocess.run`u
#: SÜREÇ GENELİNDE saplıyor (v287 emsali: komutun kendisi de sözleşmenin parçası) — esbuild ve
#: node çağrıları o saplamaya düşerse ölçüm aracı sessizce `returncode=1` alır ve çivi, ölçtüğü
#: şey yüzünden DEĞİL kendi hattı yüzünden kırmızıya döner. İlk koşumda tam bu oldu.
_GERCEK_RUN = subprocess.run

_CEVRILMIS: str | None = None


def _kaynak() -> str:
    return tsx_yorumlari_soy(BILESENLER.read_text(encoding="utf-8"))


def _cevir() -> str:
    global _CEVRILMIS
    if _CEVRILMIS is None:
        _CEVRILMIS = tsx_saf_islevleri_cevir(_kaynak(), OKUYUCULAR, kosucu=_GERCEK_RUN)
    return _CEVRILMIS


def _cagir(ad: str, *argumanlar) -> object:
    return tsx_islev_cagir(_cevir(), ad, *argumanlar, kosucu=_GERCEK_RUN)


# --- ÇİZİM HATTI: KARTI GERÇEKTEN ÇİZ -------------------------------------
# `Bilesenler` KARTIN TAMAMIDIR — blok tek başına değil KART İÇİNDEN çizilir, çünkü ölçülen şey
# tam olarak MONTAJdır: bloğu izole çizmek, kartın erken çıkışlarının onu yutmasını göremezdi
# (kusurun kendisi buydu).
_GIRIS = """
import { renderToStaticMarkup } from "react-dom/server";
import { Bilesenler } from "./Bilesenler";
const govde = JSON.parse(process.env.GOVDE ?? "{}");
console.log(renderToStaticMarkup(
  <Bilesenler durum={{ veri: govde, hata: null, oturumDustu: false }} />));
"""


def _ciz(govde: dict) -> str:
    import json as _json
    html = tsx_bileseni_cizdir(_GIRIS, SISTEM, {"GOVDE": _json.dumps(govde, ensure_ascii=False)},
                               kosucu=_GERCEK_RUN)
    assert METIN_KART in html, (
        "kart hiç çizilmedi — çizim hattı boş döndü ve aşağıdaki 'şu metin var/yok' hükümleri "
        f"anlamsız olurdu. Çıktı: {html[:200]!r}")
    return html


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
    assert _cagir("beklenmedikOku", {ALAN_LISTE: []})["hal"] == "temiz"


# ---------------------------------------------------------------------------
# 1) `[]` İLE `null` AYRI — ÜÇÜNCÜ HÂL DE AYRI
# ---------------------------------------------------------------------------

@arac_gerek
def test_BOS_LISTE_OLCULDU_DEMEKTIR_temiz():
    """`[]` ucun "ÖLÇTÜM ve fazlalık YOK" hükmüdür — belirsizlik değil, sonuçtur."""
    o = _cagir("beklenmedikOku", {ALAN_LISTE: [], ALAN_NEDEN: None})
    assert o["hal"] == "temiz", f"boş liste `{o['hal']}` diye okundu"
    assert o["birimler"] == [] and o["neden"] is None, (
        "temiz hâl gerekçe/birim taşıyor — ekranda açıklanacak bir şey yok")


@arac_gerek
def test_NULL_TEMIZ_DEGILDIR_olculemedi():
    """`null` "ÖLÇEMEDİK"tir. Temiz sayılırsa pano ölçülmemiş bir temizlik beyan eder."""
    neden = "`systemctl` bu makinede yok (Darwin) — makinede duran birimler sayılamadı"
    o = _cagir("beklenmedikOku", {ALAN_LISTE: None, ALAN_NEDEN: neden})
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
    o = _cagir("beklenmedikOku", {ALAN_LISTE: [
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
    bos = _cagir("beklenmedikDurumOku", {"birim": "x.service"})
    assert bos["olculdu"] is False
    assert isinstance(bos["neden"], str) and len(bos["neden"].strip()) >= _GEREKCE_ASGARI


# ---------------------------------------------------------------------------
# 3) BEDEL, KAPSAM VE KOMUT EKRANDA TAŞINIR
# ---------------------------------------------------------------------------

@arac_gerek
def test_BEDEL_OKUYUCUSU_kapsami_sayimi_ve_KOMUTU_TASIR():
    """BEDEL YASASI: bacak yalnız dar bir deseni sorar ve desene uymayan birimlere KÖRDÜR.
    KOMUT da okunur: ucun yayınladığı ama kimsenin okumadığı alan YASA 6 borcudur ve ekranda
    durması operatörün ölçümü KENDİ ELİYLE tekrarlamasını sağlar."""
    b = _cagir("beklenmedikBedelOku", {ALAN_OLCUM: {
        "komut": "systemctl list-unit-files 'meridian-*' --no-legend --no-pager",
        "durum_alani": "STATE sütunu `UnitFileState`tir, `ActiveState` DEĞİLDİR",
        "kapsam_disi": "yalnız `meridian-*` deseni sorgulanır; desene uymayanlar görünmez",
        "makinedeki_birim_n": 4, "makinedeki_birim_n_neden": None, "repo_birim_n": 12}})
    assert "list-unit-files" in (b["komut"] or ""), "ölçümün komutu taşınmıyor"
    assert "UnitFileState" in (b["durumAlani"] or ""), "durum sütununun NE OLDUĞU taşınmıyor"
    assert "meridian-*" in (b["kapsam"] or ""), "taramanın DAR kapsamı ekrana taşınmıyor"
    assert b["makinedeN"] == 4 and b["repoN"] == 12


@arac_gerek
def test_BEDEL_OLCULEMEDIGINDE_SIFIR_UYDURULMAZ():
    """Sayım ölçülemediğinde `0` yazmak, "hiç birim yok" diye okunur — uydurma yasağı."""
    b = _cagir("beklenmedikBedelOku", {ALAN_OLCUM: {
        "makinedeki_birim_n": None,
        "makinedeki_birim_n_neden": "`systemctl` koşturulamadı — makinedeki birimler sayılmadı"}})
    assert b["makinedeN"] is None, "ölçülmeyen sayım 0'a çevrildi"
    assert isinstance(b["makinedeNeden"], str) and b["makinedeNeden"].strip()
    yok = _cagir("beklenmedikBedelOku", {})
    assert yok["makinedeN"] is None and yok["repoN"] is None
    assert yok["kapsam"] is None and yok["durumAlani"] is None and yok["komut"] is None


# ---------------------------------------------------------------------------
# 4) MONTAJ — HÜKÜM EKRANA GERÇEKTEN ÇIKIYOR MU
# ---------------------------------------------------------------------------
# Bu bölüm bir ARIZANIN bedelidir (2026-09-01): saf okuyucular doğruyken ve `<BeklenmedikBirimler>`
# etiketi kaynakta dururken, blok kartın erken çıkışlarının ardında kaldığı için `systemctl`siz
# makinede EKRANA HİÇ ÇIKMIYORDU. Aşağısı kartı GERÇEKTEN çizer.

@arac_gerek
def test_BILESEN_BACAGI_OLCULEMEZKEN_BLOK_YINE_CIZILIR():
    """B1'İN ÇİVİSİ — BASKIN SENARYO. `systemctl` olmayan makinede uç HER İKİ bacağı da
    ölçemez: `bilesenler` null gelir ve kart gövdesi erken çıkar. İkinci bacağın "ölçemedik"
    beyanı bu çıkıştan BAĞIMSIZ olarak ekranda olmalı — yoksa pano, ölçülmemiş bir bacağı
    ölçülmüş gibi (yani hiç) gösterir."""
    gerekce = "SENTINEL42 systemctl bu makinede yok, makinedeki birimler sayilamadi"
    html = _ciz({"bilesenler": None,
                 "bilesenler_olculemedi_neden": "birinci bacak da olculemedi",
                 ALAN_LISTE: None, ALAN_NEDEN: gerekce})
    assert METIN_OLCULEMEDI in html, (
        "bileşen listesi ölçülemezken ters yön bloğu EKRANA HİÇ ÇIKMADI — kart erken çıkıyor ve "
        "blok o çıkışın ardında kalıyor olabilir (ölçülmüş kusur, 2026-09-01)")
    assert gerekce in html, (
        "blok çizildi ama UCUN GEREKÇESİ ekranda yok — 'ölçemedik' demek, NEDEN ölçemediğini "
        "söylemeden yarım bir beyandır")


@arac_gerek
def test_OLCULMUS_TEMIZLIKTE_HIC_CIZILMEZ():
    """(2) SESSİZLİK KARARI, DAVRANIŞLA. Boş liste = ölçüldü ve fazlalık yok; ekranda hiçbir
    satır doğmaz. Kart yine çizilir (pozitif kontrol `_ciz` içinde), yalnız bu blok susar."""
    html = _ciz({"bilesenler": None, "bilesenler_olculemedi_neden": "birinci bacak olculemedi",
                 ALAN_LISTE: [], ALAN_NEDEN: None})
    assert METIN_OLCULEMEDI not in html, "ÖLÇÜLMÜŞ temizlikte 'ölçülemedi' satırı çizildi"
    assert METIN_VAR not in html, "boş listede rozet/liste çizildi — her gün okunan bir gürültü"


@arac_gerek
def test_DOLU_LISTEDE_ROZET_BIRIM_ADLARI_ve_KUNYE_CIZILIR():
    """Asıl teslimat: rozet + birim adları + satır durumu + ölçüm künyesi ekranda."""
    html = _ciz({
        "bilesenler": None, "bilesenler_olculemedi_neden": "birinci bacak olculemedi",
        ALAN_LISTE: [
            {"birim": "meridian-dash.service", "durum": "disabled", "durum_neden": None},
            {"birim": "meridian-eski.timer", "durum": None,
             "durum_neden": "SENTINEL7 STATE sutunu gelmedi"}],
        ALAN_NEDEN: None,
        ALAN_OLCUM: {"komut": "systemctl list-unit-files 'meridian-*' --no-legend --no-pager",
                     "durum_alani": "UnitFileState, ActiveState degil",
                     "kapsam_disi": "yalniz meridian-* deseni sorgulanir",
                     "makinedeki_birim_n": 4, "makinedeki_birim_n_neden": None,
                     "repo_birim_n": 12}})
    assert METIN_VAR in html, "dolu listede blok çizilmedi"
    assert "2 beklenmedik birim" in html, "rozet sayıyı taşımıyor"
    for ad in ("meridian-dash.service", "meridian-eski.timer"):
        assert ad in html, f"`{ad}` ekranda yok — liste birim adlarını basmıyor"
    assert "disabled" in html, "ölçülmüş satır durumu ekranda yok"
    assert "SENTINEL7" in html, "ölçülemeyen satırın gerekçesi ekranda yok"
    assert "list-unit-files" in html, "ölçümün komutu ekranda yok (YASA 6 borcu sürüyor)"
    assert "4 birim" in html, "kaç birim tarandığı ekranda yok — bedel beyansız kaldı"


# ---------------------------------------------------------------------------
# 5) KÖPRÜ — UCUN GERÇEK GÖVDESİ PANO OKUYUCUSUNA VERİLİR
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


def _repo_birimi(ad: str, *, sablon: bool = False) -> dict:
    return {"ad": ad, "dosya": ad, "tur": ad.rsplit(".", 1)[-1], "sablon": sablon,
            "yol": f"deploy/oracle-a1/{ad}", "beklenen": True,
            "beklenen_neden": "test kurgusu: host dizininde duruyor"}


def _sahte_kaynak(monkeypatch):
    """REPO BEKLENTİSİ SAPLANIR — çivi GERÇEK `deploy/oracle-a1/` ağacına bağlanmamalı.

    Bağlı kalsaydı, depoya bir birim dosyası eklendiği ya da silindiği gün `repo_birim_n`
    değişir ve bu çivi ölçtüğü şeyle (pano okuyucusunun sözleşmesi) İLGİSİZ bir sebeple
    kırmızıya dönerdi."""
    monkeypatch.setattr(api, "_infra_birim_adlari", lambda: {
        "birimler": [_repo_birimi("meridian-backup.service"),
                     _repo_birimi("meridian-backup.timer"),
                     _repo_birimi("meridian-sprint@.service", sablon=True)],
        "dizin": "deploy/oracle-a1", "olculemedi_neden": None})


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
    _sahte_kaynak(monkeypatch)
    _sahte_systemctl(monkeypatch, _LIST_CIKTISI)
    yuk = TestClient(api.app).get("/api/infra?taze=1").json()

    o = _cagir("beklenmedikOku", yuk)
    assert o["hal"] == "var", (
        f"ucun gövdesi panoda `{o['hal']}` diye okundu — alan adları ayrışmış olabilir. "
        f"Beklenen: {UC_ALANLARI}; gövdede: {sorted(k for k in yuk if 'beklenmedik' in k)}")
    assert [b["birim"] for b in o["birimler"]] == ["meridian-dash.service"]

    d = _cagir("beklenmedikDurumOku", o["birimler"][0])
    assert d["olculdu"] is True and d["metin"] == "disabled"

    b = _cagir("beklenmedikBedelOku", yuk)
    assert b["makinedeN"] == 4, f"makinede sayılan birim adedi taşınmadı: {b}"
    assert b["repoN"] == 3, f"repo beklentisinin adedi taşınmadı: {b}"
    assert b["kapsam"] and b["durumAlani"] and b["komut"], "bedel/kapsam/komut panoya ulaşmıyor"


@arac_gerek
def test_SYSTEMCTL_YOKKEN_PANO_TEMIZ_DEMEZ(monkeypatch, sandbox_state):
    """Yerel macOS'un GERÇEK hâli: `systemctl` yok → uç `None` + gerekçe döner.

    BU ÇİVİ TEK BAŞINA MONTAJ KANITI DEĞİLDİR (2026-09-01 dersi): yalnız SAF OKUYUCUyu ölçer
    ve tam bu senaryoda blok ekrana hiç çıkmazken de YEŞİLDİ. Montajın çivisi
    `test_BILESEN_BACAGI_OLCULEMEZKEN_BLOK_YINE_CIZILIR`; bu çivi onun tamamlayıcısı."""
    monkeypatch.setattr(api.shutil, "which", lambda ad: None)
    yuk = TestClient(api.app).get("/api/infra?taze=1").json()
    o = _cagir("beklenmedikOku", yuk)
    assert o["hal"] == "olculemedi", f"ölçülemeyen bacak panoda `{o['hal']}` diye okundu"
    assert isinstance(o["neden"], str) and len(o["neden"].strip()) >= _GEREKCE_ASGARI


# ---------------------------------------------------------------------------
# 6) OKUYUCULAR ÖKSÜZ DEĞİL — KAYNAK BİÇİMİ
# ---------------------------------------------------------------------------

def test_BLOK_KARTA_BAGLI():
    """Blok kartın gövdesine bağlı mı.

    BU ÇİVİ TEK BAŞINA MONTAJ KANITI DEĞİLDİR (2026-09-01 dersi): yalnız JSX ETİKETİNİN
    varlığını görür, etiketin ERİŞİLEBİLİR bir dalda durduğunu görmez — blok erken çıkışların
    ardındayken de YEŞİLDİ. Montajın hükmü §4'teki çizim çivilerindedir; bu çivi ucuz bir ön
    kontroldür (etiket hiç yoksa çizim çivilerinin hata metni okunmaz olurdu)."""
    ham = _kaynak()
    assert re.search(r"function BeklenmedikBirimler\(", ham), (
        "`BeklenmedikBirimler` diye bir blok YOK — alan hâlâ ekransız")
    assert re.search(r"<BeklenmedikBirimler\b[^>]*\bg=\{g\}", ham), (
        "blok kartın gövdesine bağlanmamış — hesaplanan hüküm ekrana çıkmıyor")


def test_BLOK_UC_OKUYUCUYU_DA_CAGIRIR():
    g = tsx_islev_govdesi(_kaynak(), "function BeklenmedikBirimler(")
    for ad in OKUYUCULAR:
        assert re.search(rf"\b{ad}\s*\(", g), f"`{ad}` blokta çağrılmıyor — öksüz okuyucu"


def test_DIKKAT_TONU_KOMSUDAN_GELIR_YENI_RENK_ICAT_EDILMEZ():
    """TASARIM DİLİ: rozet tonu bu kartın kendi ton sözlüğünden okunur. Yeni bir hue bandı
    icat etmek, rezerve renk kaydını (mod/nav/şiddet) sessizce delerdi."""
    g = tsx_islev_govdesi(_kaynak(), "function BeklenmedikBirimler(")
    assert re.search(r"TON_METNI\.dikkat|TON_METNI\[\s*[\"']dikkat[\"']\s*\]", g), (
        "rozet rengi kartın ton sözlüğünden gelmiyor — elle yazılmış bir renk tasarım dilinden kopar")
    assert re.search(r"TON_NOKTASI\.dikkat|TON_NOKTASI\[\s*[\"']dikkat[\"']\s*\]", g), (
        "rozet noktası ton sözlüğünden gelmiyor")


# Hangi alan HANGİ İŞLEVDE okunmalı. "Dosyada bir yerde geçiyor" YETMEZ (v316 dersi): alan bir
# yorumda ya da tip beyanında geçebilir ve hiçbir şey kanıtlamaz.
OKUYUCU_HARITASI = (
    ("beklenmedikOku", (ALAN_LISTE, ALAN_NEDEN)),
    ("beklenmedikDurumOku", ("durum", "durum_neden")),
    ("beklenmedikBedelOku", (ALAN_OLCUM, "komut")),
)


def test_UC_ALANIN_UI_OKUYUCUSU_VAR():
    """YASA 6'nın kendisi: uç bu alanları yayınlıyorsa panoda OKUNUYOR olmalı. Ölçüm ÖZELLİK
    ERİŞİMİNİ, üstelik BELİRLİ BİR İŞLEVİN GÖVDESİNDE arar (yorumlar soyuldu; `uctipleri.ts`
    ölçüme hiç girmiyor — tip beyanı okuyucu DEĞİLDİR)."""
    ham = _kaynak()
    for islev, alanlar in OKUYUCU_HARITASI:
        g = tsx_islev_govdesi(ham, f"function {islev}(")
        for alan in alanlar:
            assert re.search(rf"\.{alan}\b", g), (
                f"`{alan}` `{islev}` içinde okunmuyor — YASA 6 borcu kapanmadı")


def test_TIP_BEYANI_UCUN_SOZLESMESINI_TASIR():
    """Tip beyanı okuyucu değildir ama SÖZLEŞMEdir: `[]` ile `null` ayrımı tipte de durmalı,
    yoksa bir gün `?: Birim[]` yazılır ve derleyici üçüncü hâli görmez."""
    s = UCTIPLERI.read_text(encoding="utf-8")
    for alan in UC_ALANLARI:
        assert re.search(rf"^\s*readonly {alan}\?:", s, re.M), f"`{alan}` tipte beyan edilmemiş"
    m = re.search(rf"readonly {ALAN_LISTE}\?:\s*([^;]+);", s)
    assert m and "null" in m.group(1), (
        f"`{ALAN_LISTE}` tipi `null`ı taşımıyor ({m.group(1) if m else '—'}) — 'ölçemedik' "
        "hâli tipten silinirse ekranda da silinir")
