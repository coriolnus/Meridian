"""v275 — ÜÇ KÜÇÜK KALEMİN ÇİVİLERİ (2026-08-23 Rol-1 brief'i).

(a) F8 A4 KARARI — `watchdog.report().ok` SAYI-TAŞIMA VAKASI (T3.1) ÜRETİCİDE KAPANDI:
    sayaç kanonik `n_ok`a taşındı, `ok` YALNIZ hüküm taşır (True/False/None — askıda: ne OK
    ne ihlal → None, sebep `askida` listesinde). Eski sayı-taşıyan `ok` bir dönem EŞANLAMLI
    okunur (`durum_sozlugu.n_ok_oku`, F8 sayaç desenine bağlı: her eşanlamlı okuma "sayac:ok"
    anahtarıyla sayılır — okuyucu-ölümü ölçülür, düşürme Rol-1'de). `hukum_oku`nun "sayı-ok
    hüküm sayılmaz" emniyeti KALIR (eski-şekilli yükler için hâlâ gerekli) ve ayna kuralı
    doğar: "hüküm-ok sayaç sayılmaz" (bool→int mirasında True==1 sessizce '1 mekanizma'
    uydururdu).

(b) 25b SON DAMGA — SKILL "GÖLGE" ROZETİ (WP7-24h; DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13
    §D-2 "En acil damga"): bayrak trading davranışını DEĞİŞTİRMEZ — rozet bunu artık kendisi
    söyler (tooltip) ve beyan kayıt yüzeyinde taşınır (`skills.GOLGE_BEYANI` →
    /api/skills `golge_beyani` → app.js okuyucusu; YASA 6 zinciri elle kurulu).
    DAVRANIŞSIZLIK ÇİVİSİ: deterministik karar çekirdeği (strategy/guard/broker/regime/
    prescreen/arming/faz5_cikis/intraday_cycle) `skills` modülünü HİÇ import etmez; import
    eden karar-yolu modülleri (loop/backtest/counterfactual) yalnız GÖZLEMSEL üyeleri kullanır
    (pipeline_run/reconcile_enablement/screener_for — hiçbiri `shadow` bayrağını karara
    bağlamaz). Yarın biri bayrağı motora bağlarsa bu çivi kırmızı doğar ve BEYAN yeniden
    ölçülmek zorunda kalır — damga bayatlayamaz.

(c) POZİTİF KONTROLLER + DÜZENEK ÇİVİLERİ (v251 dersi): kanonik okuma sayaç OYNATMAZ;
    AST tarayıcısı loop.py'de SIFIR kullanım bulursa hiçbir şey ölçmeden yeşil geçerdi —
    o sessiz-yeşil kapalı; tarayıcının kendisi sentetik ihlalle sınanır.

Kaynak çivileri repo deseniyle (v196 · v251 · v271): dizgi kaynağı, sandbox gerçek üreticiyi
ölçer. Not: bu dosya worktree kapsam testidir — otoriter tam suite Rol-1'de.
"""
from __future__ import annotations

import ast
import pathlib
import time

import pytest

from meridian import durum_sozlugu as dsz, skills, store, watchdog

SRC = pathlib.Path(__file__).resolve().parents[1]
APIPY = (SRC / "meridian" / "api.py").read_text(encoding="utf-8")
APPJS = (SRC / "meridian" / "web" / "app.js").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _temiz_sayac():
    """Sayaç süreç-içi ve modül-küresel: testler arası sızıntıyı keser (v271 hijyeni)."""
    dsz._sifirla_test_icin()
    yield
    dsz._sifirla_test_icin()


def _beats(**adlar: float) -> None:
    store.write_json(watchdog.BEATS_FILE, dict(adlar))


# =============================================================================================
# (a1) ÜRETİCİ — report(): sayaç `n_ok`ta, `ok` yalnız hüküm
# =============================================================================================

def test_report_sayac_n_ok_hukum_ok(sandbox_state, monkeypatch):
    """Temiz hâl: her mekanizma penceresinde → n_ok sayar, ok=True (hüküm, SAYI DEĞİL)."""
    monkeypatch.setattr(watchdog, "EXPECTED", {"scheduler_poll": 3600.0})
    _beats(scheduler_poll=time.time())
    rep = watchdog.report()
    assert type(rep["n_ok"]) is int and rep["n_ok"] == 1          # bool int'e sızamaz
    assert rep["ok"] is True and rep["total"] == 1
    # üretici temizlendi: kanonik okuyucu artık report'tan HÜKÜM okuyabiliyor (A4'ün amacı)
    assert dsz.hukum_oku(rep) == (True, "ok")
    assert dsz.n_ok_oku(rep) == (1, "n_ok")
    assert dsz.esanlamli_okumalar() == {}                          # kanonik yol sayaç oynatmaz


def test_report_geciken_ve_hic_kosmamis_hukmu_dusurur(sandbox_state, monkeypatch):
    monkeypatch.setattr(watchdog, "EXPECTED",
                        {"scheduler_poll": 1800.0, "warmup_sprint": 3600.0})
    _beats(scheduler_poll=time.time() - 7200.0)                    # geciken (never'lı ikinci ad)
    rep = watchdog.report()
    assert rep["ok"] is False and rep["n_ok"] == 0
    assert {x["name"] for x in rep["stale"]} == {"scheduler_poll"}
    assert rep["never"] == ["warmup_sprint"]


def test_report_askida_hukum_askiya_alinir(sandbox_state, monkeypatch):
    """Askıda ne OK ne ihlaldir (tasarım §4a): ihlal yokken askıda varsa hüküm None —
    'temiz' UYDURULMAZ, sebep `askida` listesinde adıyla durur; sayaç askıdayı SAYMAZ."""
    monkeypatch.setattr(watchdog, "EXPECTED",
                        {"scheduler_poll": 3600.0, "hermes_poll": 1800.0})
    monkeypatch.setattr(watchdog, "_hermes_askida",
                        lambda: {"neden": "kota_sogumasi", "kalan_s": 900.0, "detay": "soğumada"})
    simdi = time.time()
    _beats(scheduler_poll=simdi, hermes_poll=simdi - 3600.0)
    rep = watchdog.report()
    assert rep["stale"] == [] and rep["never"] == []
    assert rep["askida"][0]["name"] == "hermes_poll"
    assert rep["ok"] is None and rep["n_ok"] == 1


# =============================================================================================
# (a2) EŞANLAMLI OKUMA — n_ok_oku F8 sayaç deseninde
# =============================================================================================

def test_n_ok_oku_kanonik_ve_esanlamli():
    assert dsz.SAYAC_KANONIK == "n_ok" and tuple(dsz.SAYAC_ESANLAMLI) == ("ok",)
    assert dsz.n_ok_oku({"n_ok": 5, "ok": True}) == (5, "n_ok")
    assert dsz.esanlamli_okumalar() == {}                          # pozitif kontrol: kanonik yol
    assert dsz.n_ok_oku({"ok": 7, "total": 17}) == (7, "ok")       # eski-şekilli yük
    assert dsz.esanlamli_okumalar() == {"sayac:ok": 1}             # okuyucu-ölümü ölçülür


def test_n_ok_oku_hukum_ok_sayac_sayilmaz():
    """Ayna emniyeti: bool bir sayaç DEĞİLDİR (True==1 mirası '1 mekanizma' uydururdu) —
    `hukum_oku`nun 'sayı-ok hüküm sayılmaz' kuralının tersi yönü."""
    assert dsz.n_ok_oku({"ok": True}) == (None, None)
    assert dsz.n_ok_oku({"ok": None}) == (None, None)
    assert dsz.n_ok_oku({"n_ok": True, "ok": False}) == (None, None)
    assert dsz.n_ok_oku("rapor-degil") == (None, None)
    assert dsz.esanlamli_okumalar() == {}                          # uydurmayan yol saymaz da


def test_hukum_alani_saf_kaldi():
    """Eski-şekilli sayı-ok'tan hüküm hâlâ TÜRETİLMEZ (emniyet üretici temizlense de kalır);
    yeni-şekilli çift alanda hüküm `ok`tan, sayaç `n_ok`tan okunur — karışmazlar."""
    assert dsz.hukum_oku({"ok": 17, "total": 17}) == (None, None)
    assert dsz.hukum_oku({"ok": False, "n_ok": 3}) == (False, "ok")
    assert dsz.hukum_oku({"ok": None, "n_ok": 0}) == (None, "ok")
    assert dsz.esanlamli_okumalar() == {}


# =============================================================================================
# (a3) OKUYUCULAR BİRLİKTE ÇEVRİLDİ — api + pano
# =============================================================================================

def test_api_okuyuculari_n_ok_okur(sandbox_state):
    """`_sessiz_hat` özeti ve `_hat_cizelgesi.bekci_ok` sayacı kanonik yoldan okur; eski
    sayı-taşıyan yük gelirse eşanlamlı okur ve SAYAR (dağıtım-arası pencere boş kalmaz)."""
    from meridian import api
    yeni = {"stale": [], "never": [], "askida": [], "ok": True, "n_ok": 17, "total": 17}
    seg = {s["ad"]: s for s in api._sessiz_hat(yeni, {})["segmentler"]}["bekçiler"]
    assert seg["ozet"] == "17/17"
    assert dsz.esanlamli_okumalar() == {}
    eski = {"stale": [], "never": [], "askida": [], "ok": 9, "total": 17}
    seg = {s["ad"]: s for s in api._sessiz_hat(eski, {})["segmentler"]}["bekçiler"]
    assert seg["ozet"] == "9/17"
    assert dsz.esanlamli_okumalar().get("sayac:ok") == 1
    # hüküm-ok sayaç sayılmaz + sayaç yokluğu 0'a/None-metnine bulaşmaz (v196)
    bos = {"stale": [], "never": [], "askida": [], "ok": True, "total": 17}
    seg = {s["ad"]: s for s in api._sessiz_hat(bos, {})["segmentler"]}["bekçiler"]
    assert seg["ozet"] == "—"


def test_kaynak_civileri_okuyucular_ve_sozluk_yuzeyi():
    assert APIPY.count("n_ok_oku(") >= 2, "api okuyucuları (sessiz_hat + cizelge) kanonik okumuyor"
    assert '"sayac": {"kanonik": _dsz.SAYAC_KANONIK' in APIPY, "sözlük ucu sayaç ailesini taşımıyor"
    assert "kan.sayac" in APPJS, "F8 sözlük kartı sayaç ailesini basmıyor (YASA 6)"
    # pano iki okuyucusu: kanonik önce, eski ad yalnız GERÇEK sayıysa (hüküm-ok sayılmaz)
    assert APPJS.count('wd.n_ok ?? (typeof wd.ok === "number"') >= 2
    assert "${wd.ok}/" not in APPJS, "pano hâlâ ham `ok`u sayaç diye basıyor"


# =============================================================================================
# (b) 25b SON DAMGA — gölge rozeti beyanı + davranışsızlık çivisi
# =============================================================================================

def test_golge_beyani_kayit_yuzeyinde():
    assert isinstance(skills.GOLGE_BEYANI, str)
    assert "DEĞİŞTİRMEZ" in skills.GOLGE_BEYANI and "gözlem katman" in skills.GOLGE_BEYANI
    assert '"golge_beyani"' in APIPY and "GOLGE_BEYANI" in APIPY, "/api/skills beyanı taşımıyor"


def test_golge_rozeti_beyani_basar():
    """Rozet üretim noktası (RENDER.skiller `satir`) gölge rozetine tooltip beyanı iliştirir;
    metin uçtan gelir (`golge_beyani`), uç eski sürümse yerel eş metin basılır — rozet
    beyansız kalamaz."""
    assert "d.golge_beyani" in APPJS
    assert 'title="${esc(GOLGE_BEYAN)}"' in APPJS
    assert APPJS.count("trading'i DEĞİŞTİRMEZ") >= 1                # yerel eş metin (fallback)


def _skills_kullanimlari(kaynak: str) -> tuple[set[str], set[str]]:
    """(takma_adlar, kullanılan_üyeler): `skills` modülünün import takma adlarını ve o adlar
    üzerinden erişilen öznitelik adlarını AST ile toplar (metin değil DAVRANIŞ sınırı ölçülür —
    Ö-41'in 'metin-çivisi skoru şişirir' dersi)."""
    agac = ast.parse(kaynak)
    takma: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ImportFrom):
            for a in dugum.names:
                if a.name == "skills":
                    takma.add(a.asname or a.name)
        elif isinstance(dugum, ast.Import):
            for a in dugum.names:
                if a.name.endswith(".skills"):
                    takma.add(a.asname or a.name.split(".")[0])
    uyeler = {d.attr for d in ast.walk(agac)
              if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name)
              and d.value.id in takma}
    return takma, uyeler


# Karar-yolu modüllerinin GÖZLEMSEL izin listesi: hiçbiri `shadow`/`enabled` bayrağını karara
# bağlamaz (pipeline_run=telemetri, screener_for=ad eşlemesi, reconcile_enablement=anahtar
# defter bakımı — ve gölge kararı onu da ATLAR, skills.GOLGE_BEYANI (satır-çapası 2026-08-24'te sembole çevrildi) beyanı).
# `auto_shadow_from_evidence` ÖLÇÜLDÜ ve bilerek listede: YAZAR yönüdür (kanıt→bayrak;
# loop'un auto_shadow_from_evidence yazar-yolu (satır-çapası 2026-08-24'te sembole çevrildi) kendi beyanı "bayrak yazımı davranışı değiştirmez") — bayrak→karar okuması değil.
_KARAR_YOLU_IZIN = {
    "loop": {"pipeline_run", "reconcile_enablement", "screener_for", "auto_shadow_from_evidence"},
    "backtest": {"screener_for"},
    "counterfactual": {"screener_for"},
}
_CEKIRDEK_IMPORTSUZ = ("strategy", "guard", "broker", "regime",
                       "prescreen", "arming", "faz5_cikis", "intraday_cycle")


def test_golge_bayragi_davranissizlik_civisi():
    """BEYANIN ÖLÇÜMÜ: deterministik karar çekirdeği skill kayıt defterine hiç uzanmaz;
    uzanan karar-yolu modülleri yalnız gözlemsel üyeleri kullanır. Bayrak yarın motora
    bağlanırsa (denetim D-3'ün öbür şıkkı) burası kırmızı doğar ve beyan güncellenmek
    zorunda kalır — damga sessizce bayatlayamaz."""
    for ad in _CEKIRDEK_IMPORTSUZ:
        takma, _ = _skills_kullanimlari((SRC / "meridian" / f"{ad}.py").read_text(encoding="utf-8"))
        assert not takma, f"{ad}.py skills import ediyor — davranışsızlık beyanı yeniden ölçülmeli"
    for ad, izin in _KARAR_YOLU_IZIN.items():
        takma, uyeler = _skills_kullanimlari((SRC / "meridian" / f"{ad}.py").read_text(encoding="utf-8"))
        assert takma, f"{ad}.py düzeneği kaydı: skills import'u kayboldu — izin listesi bayat"
        assert uyeler <= izin, f"{ad}.py gözlemsel olmayan skills üyesi kullanıyor: {uyeler - izin}"


def test_davranissizlik_civisinin_duzenegi_calisiyor():
    """DÜZENEK ÇİVİSİ (v251 dersi): tarayıcı sentetik ihlali GÖRÜR — görmeseydi yukarıdaki
    çivi hiçbir şey ölçmeden yeşil geçerdi; loop.py'de sıfır kullanım da aynı sessiz-yeşile
    girer ve yukarıda ayrıca kapalı."""
    takma, uyeler = _skills_kullanimlari(
        "from meridian import skills\n"
        "x = skills.registry()['skills']['a']['shadow']\n")
    assert takma == {"skills"} and "registry" in uyeler
    takma, uyeler = _skills_kullanimlari(
        "from . import skills as sm\ny = sm.apply_skill_action('a', 'shadow')\n")
    assert takma == {"sm"} and uyeler == {"apply_skill_action"}
