"""v271 — F8 KANONİK DURUM SÖZLÜĞÜ ÇİVİSİ (WP8-C · TASARIM-F8 §5/§6, 2026-08-22).

CODELAW YAPISAL KÖRLÜĞÜ İÇİN TEK ÇİVİ: sözlük FONKSİYON-düzeyi bir sözleşmedir —
`codelaw.artifact_graph` yalnız dosya-artefaktı tarar, kanonik ad kümesini ve eşanlamlı-okuma
zincirini GÖREMEZ (tasarım §T2 sınır beyanı). Bu dosya o zincirin dört halkasını çiviler:

  1. KANONİK KÜME DONUK — dört tutarsızlık sınıfının (hüküm 5 ad · açıklama 7 ad/2 dil ·
     öğrenme mandalı 4 yazım · acil durdurma 5+ ad) kanonik adları ve eşanlamlı listeleri
     BİREBİR eşitlikle çivilenir: sessiz genişleme/daralma testte patlar.
  2. EŞANLAMLI OKUMA ÇALIŞIR + SAYAÇLIDIR — eski ad okununca kanonik değere çevrilir VE
     sayaç artar (ölüm tarihi ölçümü); kanonik okuma sayaç OYNATMAZ (pozitif kontrol).
  3. DÖRT RAPORUN SERVİS YOLU — üretim ÖLÇÜLDÜ, dördü de CANLI (ölü-beyan GEREKMEDİ):
     kitap_damga/mutabakat/onayli_gonderim scheduler.py:907 → watchdog.check_and_alarm
     zincirinde (300 sn poll, watchdog.py :320/:326/:334), goal_failure
     check_integrity_and_alarm içinde (loop.py, `check_integrity_and_alarm`). Yüzey: /api/diagnostics
     `bekci_durumlari` (v261 çivileri) + bu turun `durum_sozlugu` bloğu.
  4. POZİTİF KONTROL — sayı-`ok`tan hüküm TÜRETİLMEZ (T3.1 · A4 Rol-1'de), tanınmayan kol adı
     DEĞİŞTİRİLMEZ ve sayılmaz, kanonik yol sayaçları 0'da bırakır.

TESTLER HEM KAYNAĞA HEM DAVRANIŞA BAKAR (repo deseni: v196 · v259 · v261): kaynak çivisi
dizgiyi, sandbox koşusu gerçek üreticiyi, Node koşusu pano şablonunun ÇALIŞMA ZAMANI çıktısını
ölçer.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

from meridian import durum_sozlugu as dsz

SRC = pathlib.Path(__file__).resolve().parents[1]
APIPY = (SRC / "meridian" / "api.py").read_text(encoding="utf-8")
WDPY = (SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8")
APPJS = (SRC / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
NODE = shutil.which("node")

DORT_ANAHTAR = ("goal_failure", "kitap_damga", "mutabakat_tazelik", "onayli_gonderim")
NULLSIFIR = re.compile(r"(\?\?|\|\|)\s*0(?![\d.])")


@pytest.fixture(autouse=True)
def _temiz_sayac():
    """Sayaç süreç-içi ve modül-küresel: test sırası birbirine sızmasın diye her testte
    sıfırlanır (yalnız test hijyeni — üretim yolu sayaç sıfırlamaz, sıfırlasaydı ölçmeye
    çalıştığımız ölüm tarihini silerdi)."""
    dsz._sifirla_test_icin()
    yield
    dsz._sifirla_test_icin()


def _js_satir(baslangic: str) -> str:
    for ln in APPJS.splitlines():
        if ln.startswith(baslangic):
            return ln
    raise AssertionError(f"satır yok: {baslangic}")


def _js_blok(bas: str, kapanis: str = "}") -> str:
    """`bas` satırından, tek başına `kapanis` olan satıra kadarki app.js dilimi (v261 deseni)."""
    i = APPJS.index(bas)
    parcalar = []
    for ln in APPJS[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if ln.rstrip("\n") == kapanis and len(parcalar) > 1:
            return "".join(parcalar)
    raise AssertionError(f"kapanış bulunamadı: {bas}")


# =============================================================================================
# §1 — KANONİK KÜME DONUK (birebir eşitlik: genişleme de daralma da bilinçli commit ister)
# =============================================================================================

def test_hukum_kumesi_donuk():
    """T1.3 — hüküm alanının 5 adı: kanonik `ok` + dört eşanlamlı, envanter SIRASIYLA."""
    assert dsz.HUKUM_KANONIK == "ok"
    assert tuple(dsz.HUKUM_ESANLAMLI) == ("failed", "saglikli", "status", "durum")


def test_neden_kumesi_donuk():
    """T1.4 — açıklama alanının 7 adı / 2 dili: kanonik `neden`+`beyan` + beş eşanlamlı.
    Sıra OKUMA ÖNCELİĞİDİR (detail → detay → note → reason → error); `error` bilerek sonda —
    tasarım §4a onu yalnız dedektör-düşüş iskeletinde meşru sayar."""
    assert dsz.NEDEN_KANONIK == "neden"
    assert dsz.BEYAN_KANONIK == "beyan"
    assert tuple(dsz.NEDEN_ESANLAMLI) == ("detail", "detay", "note", "reason", "error")


def test_kol_kumesi_donuk():
    """T1.1 + T1.2 — iki durdurma kolunun kanonik adı ve eski yazımları. `soft_halt` ve
    `halt_learning` sessiz_hat'ın bugünkü adlarıdır (tasarım §6 kararı); API alanları
    (`halted`/`learn_halted`) burada EŞANLAMLI kayıttır, yeniden adlandırılmaz."""
    assert set(dsz.KOL_KANONIK) == {"soft_halt", "halt_learning"}
    assert tuple(dsz.KOL_KANONIK["soft_halt"]) == (
        "HALT", "halted", "HALT_ACTIVE", "meridian_halted", "halt")
    assert tuple(dsz.KOL_KANONIK["halt_learning"]) == (
        "LEARN_HALT", "learn_halted", "learning_halted")


# =============================================================================================
# §2 — EŞANLAMLI OKUMA ÇALIŞIR + SAYAÇLIDIR (+ pozitif kontroller)
# =============================================================================================

def test_failed_ters_isaretle_okunur_ve_sayilir():
    assert dsz.hukum_oku({"failed": True}) == (False, "failed")
    assert dsz.hukum_oku({"failed": False}) == (True, "failed")
    assert dsz.hukum_oku({"failed": None}) == (None, "failed")
    assert dsz.esanlamli_okumalar() == {"hukum:failed": 3}


def test_saglikli_status_durum_okumalari():
    """`saglikli` beyanlı iki-değerli taşınır; `status` yalnız "ok" değerinde hüküm verir
    (enum'un geri kalanından hüküm UYDURULMAZ); `durum` doluluk enum'udur — hiçbir değeri
    hükme çevrilmez, ama okunduğu SAYILIR (ölçülen şey adın okunması)."""
    assert dsz.hukum_oku({"saglikli": True}) == (True, "saglikli")
    assert dsz.hukum_oku({"saglikli": False}) == (False, "saglikli")
    assert dsz.hukum_oku({"status": "ok"}) == (True, "status")
    assert dsz.hukum_oku({"status": "unknown"}) == (None, "status")
    assert dsz.hukum_oku({"durum": "dolu"}) == (None, "durum")
    assert dsz.esanlamli_okumalar() == {
        "hukum:saglikli": 2, "hukum:status": 2, "hukum:durum": 1}


def test_kanonik_okuma_sayac_oynatmaz():
    """POZİTİF KONTROL: kanonik `ok` varken eşanlamlıya DÜŞÜLMEZ ve sayaç oynamaz —
    sayaç sırf çağrıyla artıyor olsaydı 'eski ad okunuyor' ölçümü anlamsızlaşırdı."""
    assert dsz.hukum_oku({"ok": False, "failed": True}) == (False, "ok")
    assert dsz.hukum_oku({"ok": None, "failed": None}) == (None, "ok")
    assert dsz.neden_oku({"neden": "a", "detail": "b"}) == ("a", "neden")
    assert dsz.esanlamli_okumalar() == {}


def test_sayi_ok_hukum_sayilmaz():
    """T3.1 emniyeti: ESKİ-şekilli `report().ok` bir SAYIYDI (penceresindeki mekanizma adedi) —
    sayıdan hüküm TÜRETİLMEZ, alan mevcutken eşanlamlıya da düşülmez. A4 kararıyla (Rol-1,
    2026-08-23) üretici ayrıştı (sayaç `n_ok`, hüküm `ok` — v275); bu emniyet ESKİ-şekilli
    yükler için kalır."""
    assert dsz.hukum_oku({"ok": 17, "total": 17}) == (None, None)
    assert dsz.esanlamli_okumalar() == {}


def test_neden_esanlamli_sirasi_ve_sayac():
    assert dsz.neden_oku({"detail": "b", "detay": "c"}) == ("b", "detail")   # öncelik sırası
    assert dsz.neden_oku({"detay": "c"}) == ("c", "detay")
    assert dsz.neden_oku({"note": "d"}) == ("d", "note")
    assert dsz.neden_oku({"reason": "e"}) == ("e", "reason")
    assert dsz.neden_oku({"error": "f"}) == ("f", "error")
    assert dsz.neden_oku({}) == (None, None)
    assert dsz.esanlamli_okumalar() == {
        "neden:detail": 1, "neden:detay": 1, "neden:note": 1,
        "neden:reason": 1, "neden:error": 1}


def test_kol_adi_esanlamli_ve_pozitif_kontrol():
    assert dsz.kol_adi("learning_halted") == "halt_learning"
    assert dsz.kol_adi("LEARN_HALT") == "halt_learning"
    assert dsz.kol_adi("halted") == "soft_halt"
    assert dsz.kol_adi("HALT_ACTIVE") == "soft_halt"
    # kanonik ad değişmez ve SAYILMAZ; tanınmayan ad (kol değil) da değişmez ve sayılmaz —
    # hermes `last_result="rejected_by_backtest"` bir kol adı değildir, "düzeltilemez".
    assert dsz.kol_adi("soft_halt") == "soft_halt"
    assert dsz.kol_adi("rejected_by_backtest") == "rejected_by_backtest"
    assert dsz.esanlamli_okumalar() == {
        "kol:learning_halted": 1, "kol:LEARN_HALT": 1,
        "kol:halted": 1, "kol:HALT_ACTIVE": 1}


# =============================================================================================
# §3 — ÜRETİCİ ÇİFT-ALAN GEÇİŞİ (eski ad KALIR + kanonik ad EKLENİR; tutarlılık ölçülür)
# =============================================================================================

def test_goal_failure_kanonik_cift_alan(sandbox_state):
    """goal_failure artık kanonik hüküm çekirdeğini DE taşır; `failed`/`detail` kalır ve
    ikisi TUTARLIDIR (işaret ters). Boş sandbox'ta hüküm UYDURULMAZ (ok=None)."""
    from meridian import watchdog
    g = watchdog.goal_failure_report()
    for alan in ("ok", "failed", "neden", "detail", "olculemedi", "kapsam_disi"):
        assert alan in g, f"goal_failure kanonik çift-alan eksik: {alan}"
    assert g["neden"] == g["detail"], "neden ile detail AYRIŞTI — çift-alan tek metin taşımalı"
    assert (g["ok"] is None) == (g["failed"] is None)
    if g["failed"] is not None:
        assert g["ok"] == (not g["failed"]), "ok/failed işaret sözleşmesi bozuk (ters olmalı)"
    assert g["ok"] is None, "boş sandbox'ta goal hükmü uydurulamaz"


def test_kitap_damga_satirlari_neden_tasir(sandbox_state):
    from meridian import watchdog
    rep = watchdog.kitap_damga_report()
    assert rep["rows"], "izlenen belge yok — kapsam testi ölçemedi"
    for r in rep["rows"]:
        assert r.get("neden") == r.get("detay"), f"satır çift-alan taşımıyor: {r.get('ad')}"


def test_universe_unknown_neden_tasir(sandbox_state):
    from meridian import store, watchdog
    store.write_json("universe_drift.json", {"status": "unknown", "reason": "çivi-nedeni"})
    rep = watchdog.universe_audit_report()
    assert rep["reason"] == "çivi-nedeni", "eski ad `reason` KIRILDI — geçiş çift-alan olmalı"
    assert rep["neden"] == "çivi-nedeni", "kanonik `neden` taşınmıyor"


def test_sessiz_hat_sapmalari_neden_tasir(sandbox_state):
    from meridian import api
    wd = {"stale": [{"name": "x", "gap_h": 2.0, "expected_h": 1.0}],
          "never": ["y"], "askida": [], "ok": 15, "total": 17}
    sh = api._sessiz_hat(wd, {})
    sapmalar = [s for seg in sh["segmentler"] for s in seg["sapmalar"]]
    assert sapmalar, "sapma üretilmedi — kapsam testi ölçemedi"
    for s in sapmalar:
        assert s.get("neden") == s.get("detay"), f"sapma çift-alan taşımıyor: {s.get('ad')}"


def test_parity_integrity_production_kaynak_civisi():
    """Ağır koşumlu üreticilerde (parity/integrity/production) çift-alan KAYNAK çivisiyle
    ölçülür — tam koşum otoriter suite'in işi (madde 6), buradaki çivi geri alınmayı patlatır."""
    assert '_r["neden"] = _r["detail"]' in WDPY, "parity satır çift-alanı söküldü"
    assert 'out["neden"] = out["detail"]' in WDPY, "integrity._tut çift-alanı söküldü"
    assert '_r.setdefault("neden", _r.get("detay"))' in WDPY, "kitap satır çift-alanı söküldü"
    assert '_r.setdefault("neden", _r.get("note"))' in WDPY, "production çift-alanı söküldü"
    assert '_s.setdefault("neden", _s.get("detay"))' in APIPY, "sessiz_hat çift-alanı söküldü"


# =============================================================================================
# §4 — SERVİS YOLU: dört rapor + sözlük bloğu /api/diagnostics'te
# =============================================================================================

def test_diagnostics_durum_sozlugu_blogu_tasir():
    govde = APIPY[APIPY.index("def api_diagnostics"):]
    govde = govde[:govde.index("@app.get")]
    assert '"durum_sozlugu"' in govde and "_durum_sozlugu(" in govde, \
        "/api/diagnostics `durum_sozlugu` bloğunu servis etmiyor — sayaçlar okuyucusuz (YASA 6)"
    assert '"bekci_durumlari"' in govde, "dört raporun yüzeyi (v261) kayboldu"


def test_dort_raporun_servis_yolu_canli(sandbox_state):
    """Üretim ölçümünün koşum yarısı: dört rapor gerçek sandbox'ta ÜRETİLİYOR ve uç dördünü
    taşıyor (ölü-beyan gerekmedi — kablolama kanıtı modül docstring'inde satır adresleriyle)."""
    from meridian import api
    out = api._bekci_durumlari()
    assert set(out) == set(DORT_ANAHTAR)
    for ad in DORT_ANAHTAR:
        assert isinstance(out[ad], dict), f"{ad} rapor değil: {type(out[ad])}"


def test_durum_sozlugu_eski_yuku_gorunur_kilar():
    """ESKİ adlı yük sözlükten geçince: hüküm çevrilir, kaynak alanın ADI satırda durur,
    sayaç artar — geçiş haritası canlıda böyle izlenir (tasarım §6 kanonik okuyucu)."""
    from meridian import api
    bd = {"goal_failure": {"failed": True, "detail": "eski-yük"},
          "kitap_damga": {"ok": True, "olculemedi": False},
          "mutabakat_tazelik": {"ok": None, "olculemedi": True, "neden": "kayıt yok"},
          "onayli_gonderim": {"ok": True, "olculemedi": False, "neden": ""}}
    dz = api._durum_sozlugu(bd)
    satir = {s["kimlik"]: s for s in dz["satirlar"]}
    assert set(satir) == set(DORT_ANAHTAR)
    g = satir["goal_failure"]
    assert g["ok"] is False and g["kaynak_alan"] == "failed"
    assert g["neden"] == "eski-yük" and g["neden_kaynak"] == "detail"
    assert dz["esanlamli_okumalar"]["hukum:failed"] == 1
    assert dz["esanlamli_okumalar"]["neden:detail"] == 1
    # kanonik yüklerin satırları kaynak alanı "ok" gösterir
    assert satir["kitap_damga"]["kaynak_alan"] == "ok"
    assert satir["mutabakat_tazelik"]["neden_kaynak"] == "neden"


def test_kanonik_uretici_zinciri_sayac_oynatmaz(sandbox_state):
    """ÖLÇÜMÜN KENDİSİ: üretici kanonik alanları taşıdığı sürece gerçek zincir
    (_bekci_durumlari → _durum_sozlugu) TEK eşanlamlı okuma yapmaz — sayaçlar 0'da kalır.
    Bu test kırmızıya dönerse bir üretici kanonik alanı DÜŞÜRMÜŞ demektir."""
    from meridian import api
    bd = api._bekci_durumlari()
    dsz._sifirla_test_icin()          # üretim sırasındaki başka okumaları ayıkla
    dz = api._durum_sozlugu(bd)
    assert dz["esanlamli_okumalar"] == {}, \
        f"kanonik zincir eşanlamlı okudu: {dz['esanlamli_okumalar']}"
    for s in dz["satirlar"]:
        assert s["kaynak_alan"] == "ok", f"{s['kimlik']} hükmü kanonik alandan okunmuyor"


# =============================================================================================
# §5 — PANO OKUYUCUSU (YASA 6: sözlük bloğu + sayaçlar panoda OKUNUR)
# =============================================================================================

def test_pano_f8_sozluk_ve_okuyucu_var():
    assert "const F8_SOZLUK = {" in APPJS, "pano F8 sözlük sabiti yok"
    assert "function f8KolAd(" in APPJS, "kol eşanlamlı çevirici yok"
    assert "function f8SozlukSatiri(" in APPJS, "sözlük kartı okuyucusu YOK — sayaçlar okuyucusuz"


def test_operasyon_sayfasi_sozluk_kartini_cizer():
    i = APPJS.index("RENDER.operasyon = async")
    govde = APPJS[i:APPJS.index("RENDER.cizelge", i)]
    assert "f8SozlukSatiri(" in govde, "kart hiçbir sayfada çizilmiyor — ölü kod"
    assert "durum_sozlugu" in govde, "çağrıya teşhis yükünün bloğu verilmiyor"


def test_last_result_esanlamlisi_kanonige_baglanir():
    """hermes `last_result` HAM basılıyordu (tasarım Envanter C notu): `learning_halted`
    eşanlamlısı panoda kanonik `halt_learning` adına çevrilir (üretici A3 kararına dek)."""
    assert "f8KolAd(s.last_result" in APPJS, "last_result hâlâ ham basılıyor — sözlük bağı yok"


def test_f8_okuyucuda_nullsifir_yok():
    govde = _js_blok("function f8SozlukSatiri(")
    n = sum(len(NULLSIFIR.findall(l)) for l in govde.splitlines()
            if not l.lstrip().startswith("//"))
    assert n == 0, f"f8SozlukSatiri'de {n} adet `?? 0`/`|| 0` — null 0'a bulaştırılıyor"


# ---- Node davranış koşusu (v196/v261 deseni: şablon dilimi FİİLEN koşar) ---------------------
_HARNESS = """
%(esc)s
%(trn)s
%(sozluk)s
%(kolad)s
%(fn)s
const FIX = %(fikstur)s;
const out = {};
for (const [ad, yuk] of Object.entries(FIX)) out[ad] = f8SozlukSatiri(yuk);
out.__kol = [f8KolAd("learning_halted"), f8KolAd("halted"), f8KolAd("rejected_by_backtest")];
console.log(JSON.stringify(out));
"""

_KANONIK = {
    "hukum": {"kanonik": "ok", "esanlamli": ["failed", "saglikli", "status", "durum"]},
    "neden": {"kanonik": "neden", "esanlamli": ["detail", "detay", "note", "reason", "error"]},
    "beyan": "beyan",
    "kol": {"soft_halt": ["HALT", "halted", "HALT_ACTIVE", "meridian_halted", "halt"],
            "halt_learning": ["LEARN_HALT", "learn_halted", "learning_halted"]},
}

FIKSTUR = {
    # uç bloğu vermedi → sayaçlar ÖLÇÜLEMEDİ (0 DEĞİL)
    "yok": None,
    # kanonik yol: her satır "ok"tan okunmuş, tüm sayaçlar 0
    "temiz": {"kanonik": _KANONIK,
              "satirlar": [{"kimlik": k, "kaynak_alan": "ok"} for k in DORT_ANAHTAR],
              "esanlamli_okumalar": {}, "sayac_rejimi": "süreç-içi"},
    # eski ad hâlâ akıyor: sayaç adıyla basılır, satır kaynak alanıyla görünür
    "eski_ad": {"kanonik": _KANONIK,
                "satirlar": [{"kimlik": "goal_failure", "kaynak_alan": "failed"}],
                "esanlamli_okumalar": {"hukum:failed": 3, "neden:detail": 1},
                "sayac_rejimi": "süreç-içi"},
}


@pytest.fixture(scope="module")
def node_cikti():
    if NODE is None:
        pytest.skip("node yok")
    kaynak = _HARNESS % {
        "esc": _js_satir("const esc = "),
        "trn": _js_satir("const trn = "),
        "sozluk": _js_blok("const F8_SOZLUK = {", "};"),
        "kolad": _js_satir("function f8KolAd("),
        "fn": _js_blok("function f8SozlukSatiri("),
        "fikstur": json.dumps(FIKSTUR, ensure_ascii=False),
    }
    p = subprocess.run([NODE, "-e", kaynak], capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, f"node koşusu düştü:\n{p.stderr}"
    return json.loads(p.stdout)


def test_node_blok_yoksa_olculemedi_der(node_cikti):
    out = node_cikti["yok"]
    assert "ÖLÇÜLEMEDİ" in out, "uç bloğu vermedi ama kart bunu SÖYLEMİYOR"
    assert "hepsi 0" not in out, "ölçülemeyen sayaç '0' kılığında (v196 ihlali)"


def test_node_kanonik_yol_sessiz(node_cikti):
    out = node_cikti["temiz"]
    assert "hepsi 0" in out, "kanonik yolda sayaçların 0 olduğu yazılmıyor"
    assert "×" not in out, "sayaç 0'ken sayaç satırı basılıyor — sağlıklı durum bağırmamalı"
    assert "Kademe 1 · Soft Halt" in out and "Kademe 4 · Öğrenme durdurma" in out, \
        "kanonik kol adları Türkçe pano etiketine bağlanmıyor"


def test_node_eski_ad_adiyla_gorunur(node_cikti):
    out = node_cikti["eski_ad"]
    assert "hukum:failed" in out and "×3" in out, "eşanlamlı okuma sayacı ADIYLA basılmıyor"
    assert "Rol-1" in out, "düşürme kararının sahibi (Rol-1) kartta yazmıyor"


def test_node_kol_cevirisi(node_cikti):
    assert node_cikti["__kol"] == ["halt_learning", "soft_halt", "rejected_by_backtest"], \
        "f8KolAd eşanlamlıyı kanoniğe çevirmiyor ya da tanımadığını 'düzeltiyor'"
