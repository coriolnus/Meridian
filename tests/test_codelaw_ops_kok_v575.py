"""v575 — `codelaw.report()` ÜÇÜNCÜ BESLEMESİ `ops/`+`deploy/`+kök `.py` yorumlarını da okur (TSK-243, 2026-09-27).

BOŞLUK (TSK-241 kaygı K1, inceleme ORTA-1): sembol çapası çekirdeğinin (`codelaw.capa_uyusmasi`) `.py` yorum/docstring
beslemesi `report()`ta yalnız `meridian/`+`tests/` metnini okuyordu. `ops/`+`deploy/`+kök `.py` yorumlarındaki çürük
yalnız `tests/test_ops_py_yorum_capa_v574.py`de (tam suite) görünüyordu — `report()["ok"]` ve onu koşan CI duman
çivisi (`ops/ci_duman.sh` → v214) görmüyordu; ops-yalnız bir commit'in etkilenen kümesinde v574 olmayabilirdi.

DEĞİŞİKLİK (motor, `meridian/codelaw.py`): `codelaw.OPS_YORUM_KOKLERI` (özyineli) + `codelaw.OPS_YORUM_DUZ_KOKLERI`
(depo kökü, TEK SEVİYE) — TEK KAYNAK: `report()` metin köklerini, v574 kapsamını buradan türetir (ayrışma çivisi C).
Önbellek anahtarı (`codelaw._yorum_sembol_capalari`) artık metin + çözücü + tek-seviye köklerin HEPSİNİN damgasını
taşır (çivi B — eski anahtar yalnız metin köklerini damgalıyordu: metin kökü dışındaki bir çözücü kökünde sembol
silinince aynı süreçteki ikinci `report()` bayat "temiz" dönerdi).

BÖLÜŞÜM (korundu, gerekçe): `report()` bu beslemede yalnız `curuyen`i hükme bağlar — `cozulemeyen` İHLAL DEĞİLDİR
(uydurma yasağı; `meridian/`+`tests/` metniyle AYNI kural). v574 daha SIKI kalır: beyansız çözülemeyen kırmızı,
bayat beyan, `deploy` çözücü kökü, körlük alarmı, yol-tutarlı pozitif kontrol. O sıkılık motora TAŞINMADI: beyan
defteri (hermes-agent harici kaynağı) yalnız test tarafında, yerel ağaçta doğrulanabiliyor — motorda doğrulanamayan
beyan borç defteridir, hüküm değil. Çivi E bu bölüşümü davranışla ölçer.

ÖLÇÜM (2026-09-27, taban c92509f7, pytest içi yoklama): ops/deploy/kök metni codelaw'ın KENDİ çözücü kökleriyle
(meridian+ops+tests) — 50 dosya (ops 46 · deploy 4 · kök 0), 254 çözülen, 0 çürük, 2 çözülemeyen (v574'ün iki
beyanlı hermes-agent harici çapası); `deploy` çözücü kökü eklenince ops/deploy metninde fark 0.
"""
from __future__ import annotations

import os
import pathlib

import pytest

from meridian import codelaw
from tests.test_capa_pydisi_hedef_v571 import REPO
from tests.test_ops_py_yorum_capa_v574 import _metinler as v574_metinler, ops_hukmu

_HEDEF = "SABIT = 1\n\n\ndef var_olan():\n    return SABIT\n"
_METIN_ADI = "tsk243_yorum.py"


@pytest.fixture
def sahte_kok(tmp_path, monkeypatch):
    """Sentetik depo kökü. `stale_claims` yalıtılır (v373/v314 gerekçesi: depo beyanları boş ağaçta doğrulanamaz,
    yalıtılmasa `ok` iki durumda da False çıkar ve deney çapa hakkında hiçbir şey ölçmezdi)."""
    codelaw.UNSCANNED.clear()
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a, **k: [])
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "hedef.py").write_text(_HEDEF, encoding="utf-8")
    return tmp_path


def _yaz(kok: pathlib.Path, rel: str, metin: str) -> pathlib.Path:
    yol = kok / rel
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")
    return yol


def _ileri_it(yol: pathlib.Path) -> None:
    """Yeniden yazılan dosyanın mtime'ını 1 s ileri iter: çivi anahtarın KÖK KAPSAMINI ölçer, damga çözünürlüğünü
    değil (aynı ns'de iki yazım `_src_stamp`i eşit bırakabilirdi — yanlış sebeple kırmızı)."""
    st = yol.stat()
    os.utime(yol, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


def _rapor(kok: pathlib.Path) -> dict:
    return codelaw.report(str(kok), tsx_kok=str(kok))


def _curuyen(y: dict, kok: pathlib.Path) -> list[tuple[str, str]]:
    return [(pathlib.Path(c["kaynak"]).relative_to(kok).as_posix(), c["capa"]) for c in y["curuyen"]]


# =================================================================================================
# A) SENTETİK — dört yüzeyin her birinde yorumdaki çürük sembol `report()["ok"]`i düşürür
# =================================================================================================

@pytest.mark.parametrize("rel", [f"ops/{_METIN_ADI}", f"ops/alt/{_METIN_ADI}", f"deploy/oracle-a1/{_METIN_ADI}",
                                 _METIN_ADI])
def test_SENTETIK_ops_deploy_kok_yorumunda_curuk_report_OKUNU_DUSURUR(sahte_kok, rel):
    """TEK DEĞİŞKENLİ DENEY: aynı ağaç, yalnız çapanın sembolü değişir. Önce çözülen çapa (`ok` yeşil, dosya taranmış
    ve çapa SAYILMIŞ — körlük kontrolü), sonra çürük çapa (`ok` kırmızı). `report()` bu kökleri beslemeye katmazsa
    ikinci çağrı `curuyen` boş döner ve çivi KIRMIZI olur (mutasyon M1/M2)."""
    _yaz(sahte_kok, rel, "# kilit burada kurulur: `hedef.py::var_olan`\nX = 1\n")
    r = _rapor(sahte_kok)
    y = r["yorum_sembol_capalari"]
    assert (y["taranan_dosya"], y["capa_n"], y["curuyen"]) == (1, 1, []), y
    assert r["yorum_sembol_curume"] is False and r["ok"] is True, r
    _ileri_it(_yaz(sahte_kok, rel, "# kilit burada kurulur: `hedef.py::yok_olan_sembol`\nX = 1\n"))
    r = _rapor(sahte_kok)
    y = r["yorum_sembol_capalari"]
    assert _curuyen(y, sahte_kok) == [(rel, "hedef.py::yok_olan_sembol")], y
    assert r["yorum_sembol_curume"] is True and r["ok"] is False, r


def test_SENTETIK_MODUL_BICIMI_curuk_de_report_OKUNU_DUSURUR(sahte_kok):
    """Besleme `modul_bicimi=True` ile çekirdeğe girer (meridian/tests metniyle AYNI): TSK-242'nin dördüncü çürüğünün
    sınıfı (backtick içinde modül + nokta + olmayan ad) ops yorumunda da hükme girer."""
    _yaz(sahte_kok, f"ops/{_METIN_ADI}", "# boyutlandırma tabanı (`hedef.olmayan_metot()`)\n")
    r = _rapor(sahte_kok)
    assert [c["capa"] for c in r["yorum_sembol_capalari"]["curuyen"]] == ["hedef.olmayan_metot"], r
    assert r["ok"] is False, r


# =================================================================================================
# B) ÖNBELLEK ANAHTARI — metin + çözücü + tek-seviye köklerin HEPSİ damgalı (bayat "temiz" yok)
# =================================================================================================

def _dogrudan(kok: pathlib.Path) -> dict:
    """`report()`un üretim ağacındaki kök BİÇİMİ, sentetik ağaçta: tek-seviye kök (depo kökü) ve çözücü kökü metin
    köklerinin ALTINDA DEĞİL — iki damganın da anahtara katkısı ayrı ölçülür."""
    return codelaw._yorum_sembol_capalari(metin_kokler=(str(kok / "ops"),), py_kokler=(str(kok / "pkg"),),
                                          duz_kokler=(str(kok),))


def test_ONBELLEK_kokte_YENI_py_DOGUNCA_duser(sahte_kok):
    """Tek-seviye damga: ops/ ve pkg/ dokunulmadan depo kökünde yeni bir `.py` doğar → ikinci çağrı onu görür.
    Anahtar tek-seviye kökü damgalamazsa önbellek isabet eder ve çürük görünmez (mutasyon M3)."""
    _yaz(sahte_kok, f"ops/{_METIN_ADI}", "# `hedef.py::var_olan`\n")
    ilk = _dogrudan(sahte_kok)
    assert (ilk["taranan_dosya"], ilk["curuyen"]) == (1, []), ilk
    _ileri_it(_yaz(sahte_kok, "tsk243_kok.py", "# `hedef.py::yok_olan_sembol`\n"))
    ikinci = _dogrudan(sahte_kok)
    assert ikinci["taranan_dosya"] == 2, ikinci
    assert _curuyen(ikinci, sahte_kok) == [("tsk243_kok.py", "hedef.py::yok_olan_sembol")], ikinci


def test_ONBELLEK_COZUCU_kokunde_SEMBOL_SILININCE_duser(sahte_kok):
    """ÇÖZÜCÜ KÖKÜ damgası — ölçülen bayat önbellek riski: metin dosyası aynı kalır, HEDEF modülde sembol silinir.
    Eski anahtar yalnız metin köklerini damgalıyordu → aynı süreçteki ikinci çağrı bayat "0 çürük" dönerdi
    (üretimde: `ops/` çözücü kökündeydi ama metin kökünde değildi). Mutasyon M4 eski anahtarı geri getirir."""
    _yaz(sahte_kok, f"ops/{_METIN_ADI}", "# `hedef.py::var_olan`\n")
    ilk = _dogrudan(sahte_kok)
    assert (ilk["capa_n"], ilk["curuyen"]) == (1, []), ilk
    _ileri_it(_yaz(sahte_kok, "pkg/hedef.py", "SABIT = 1\n\n\ndef baska_ad():\n    return SABIT\n"))
    ikinci = _dogrudan(sahte_kok)
    assert _curuyen(ikinci, sahte_kok) == [(f"ops/{_METIN_ADI}", "hedef.py::var_olan")], ikinci


# =================================================================================================
# C) AYRIŞMA — `report()`un ops dünyası ile v574'ün kapsamı AYNI kaynaktan, AYNI dosyalar
# =================================================================================================

def _gercek_kok_mu() -> None:
    assert (pathlib.Path.cwd() / "meridian" / "codelaw.py").is_file() and pathlib.Path.cwd().resolve() == REPO, (
        "report() göreli köklerle çalışır — çivi depo kökünden koşmalı")


def _cozulmus(kokler) -> list[pathlib.Path]:
    return [pathlib.Path(k).resolve() for k in kokler]


def test_AYRISMA_report_ops_dunyasi_ile_v574_kapsami_AYNI(monkeypatch):
    """Tek-kaynak yasası: `report()`un metin kökleri (meridian/tests DIŞINDA kalanlar) + tek-seviye kökleri ile v574'ün
    okuduğu kökler AYNI olmalı; iki tarafın okuduğu DOSYA kümesi de aynı olmalı. Biri kendi listesini yazarsa
    (ör. `deploy` düşer) çivi KIRMIZI (mutasyon M5/M6)."""
    _gercek_kok_mu()
    rapor: dict = {}

    def rapor_casusu(**kw):
        rapor.update(kw)
        return {"taranan_dosya": 0, "capa_n": 0, "curuyen": []}

    v574: dict = {}
    asil = codelaw._yorum_metinleri

    def v574_casusu(kokler=("meridian", "tests"), duz_kokler=()):
        v574.update(kokler=kokler, duz_kokler=duz_kokler)
        return asil(kokler, duz_kokler)

    with monkeypatch.context() as m:
        m.setattr(codelaw, "_yorum_sembol_capalari", rapor_casusu)
        codelaw.report()
    with monkeypatch.context() as m:
        m.setattr(codelaw, "_yorum_metinleri", v574_casusu)
        v574_dosyalari = {rel for rel, _ in v574_metinler()}
    cekirdek = set(_cozulmus(("meridian", "tests")))
    rapor_ops = [k for k in _cozulmus(rapor["metin_kokler"]) if k not in cekirdek]
    assert rapor_ops == _cozulmus(v574["kokler"]), (rapor["metin_kokler"], v574["kokler"])
    assert _cozulmus(rapor.get("duz_kokler", ())) == _cozulmus(v574["duz_kokler"]), (rapor, v574)
    ops_kokleri = tuple(k for k in rapor["metin_kokler"] if pathlib.Path(k).resolve() not in cekirdek)
    rapor_dosyalari = {pathlib.Path(y).as_posix()
                       for y, _ in codelaw._yorum_metinleri(ops_kokleri, rapor.get("duz_kokler", ()))}
    assert rapor_dosyalari == v574_dosyalari, sorted(rapor_dosyalari ^ v574_dosyalari)
    assert len(v574_dosyalari) >= 40, len(v574_dosyalari)


# =================================================================================================
# D) GERÇEK DEPO — `report()` ops dünyasını SAYAR ve orada çürük yok
# =================================================================================================

def test_GERCEK_report_OPS_DUNYASINI_SAYAR_curuk_YOK():
    """`taranan_dosya` = meridian+tests metinli dosyaları + v574'ün ops/deploy/kök dosyaları (ölçüldü 2026-09-27:
    750 + 50). Beslemeden ops dünyası düşerse eşitlik bozulur — `ok`un kendisi v402'de ölçülür (aynı iddia iki
    dosyada tutulmaz)."""
    _gercek_kok_mu()
    r = codelaw.report()
    y = r["yorum_sembol_capalari"]
    cekirdek_n = len(codelaw._yorum_metinleri(("meridian", "tests")))
    ops_n = len(v574_metinler())
    assert ops_n >= 40 and y["taranan_dosya"] == cekirdek_n + ops_n, (y["taranan_dosya"], cekirdek_n, ops_n)
    ops_curuk = [c for c in y["curuyen"] if not str(c["kaynak"]).startswith(("meridian/", "tests/"))]
    assert ops_curuk == [] and r["yorum_sembol_curume"] is False, ops_curuk


# =================================================================================================
# E) BÖLÜŞÜM — çözülemeyen çapa `report()`ta ihlal DEĞİL, v574'te beyansızsa KIRMIZI (sıkılık testte kaldı)
# =================================================================================================

def test_BOLUSUM_cozulemeyen_report_OKUNU_DUSURMEZ_v574_KIRMIZI(sahte_kok):
    capa = "dis_paket/modul.py::islev"
    _yaz(sahte_kok, f"ops/{_METIN_ADI}", f"# ölçüldü: `{capa}`\n")
    r = _rapor(sahte_kok)
    y = r["yorum_sembol_capalari"]
    assert (y["taranan_dosya"], y["curuyen"]) == (1, []) and r["ok"] is True, r
    h = ops_hukmu(v574_metinler(sahte_kok), py_kokler=(str(sahte_kok / "pkg"),), cozulemeyen_beyan={},
                  alan_adi_beyan={})
    assert [(i["tur"], i["neden"]) for i in h["ihlal"]] == [("beyansiz_cozulemeyen", "kapsam_disi")], h["ihlal"]
