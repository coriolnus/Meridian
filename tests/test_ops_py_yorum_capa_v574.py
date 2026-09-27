"""v574 — SEMBOL ÇAPASI YASASI, `ops/`+`deploy/`+kök `.py` YORUMLARI (TSK-242, 2026-09-27).

Sembol çapasının (`dosya.py::ad`, backtick içinde modül + nokta + ad) tek çekirdeği `codelaw.capa_uyusmasi`dır ve
`.py` yorum/docstring metnini okuyan besleme codelaw'ın ÜÇÜNCÜ beslemesidir (`codelaw._yorum_metinleri`) — ama
`codelaw.report` onu yalnız `meridian/`+`tests/` kökleriyle çağırır. `ops/`+`deploy/`+kök `.py` yorumları hiçbir
beslemede değildi (TSK-239 kaygı K2; `codelaw._yorum_metinleri` docstring'i asimetriyi bilerek yazar ve
"genişletmek isteyen çağıran kökleri geçebilir" der). Bu dosya o çağırandır: metni codelaw'ın KENDİ çıkarımıyla
(`codelaw._yorum_metinleri` — tokenize yorum + ast docstring, kod dizgesi HARİÇ) alır, hükmü v572'nin hüküm
gövdesiyle (`tests/test_sembol_capa_pydisi_v572.py::sembol_hukmu`) kurar. İkinci bir çıkarım ya da çözücü YAZILMADI.

TUR BAŞI ÖLÇÜM (2026-09-27, taban 839f3e2e; pytest içi yoklama, depo dışı): 50 dosya (`ops/` 46 · `deploy/` 4 ·
kök 0), 250 çözülen (30 dosya biçimi · 220 modül biçimi), 4 ÇÜRÜK, 2 çözülemeyen.
  * Dört çürüğün HEDEFİ doğruydu, YAZIMI çürüktü: `ops/dolum_geri_dolum.py` v475 çivisinin adını satır sonunda
    BÖLMÜŞTÜ; `ops/olcum.py` v328 çivisinin adını üç noktayla KISALTMIŞTI; `ops/sasi_yukleyici.py` conftest'teki bir
    İTHAL takma adını tanım gibi çapalıyordu (codelaw ithal adı tanım saymaz — `codelaw._modul_adlari`);
    `ops/sermaye_beyani_iade.py` PaperBroker'ın METODUNU modül önekiyle yazıyordu. Dördü bu turda yalnız yorum
    metninde düzeltildi (satır sayısı aynı).
  * İki çözülemeyen `ops/sef_brifingi.py`de hermes-agent kaynağını gösterir (harici). Beyan için yerel ağaçta
    doğrulanırken biri ÇÜRÜK çıktı: yerel v0.18.2'de o adla bir işlev YOK (git tarihinde de yok); şerhin anlattığı
    öncelik listesini taşıyan işlev `build_context_files_prompt` — şerh o ada düzeltildi. İkincisi (bir satıcı
    test metodu, yol öneksiz) doğrulandı.
  * Bedel (ölçüldü): çıkarım ~0,24 s + çözüm ~0,34 s (soğuk). `codelaw.report`un kendi beslemesine katılsaydı bu
    maliyet her `report()` çağrısına binerdi; burada yalnız suite öder.

KAPSAM KARARI — TEST TARAFI, MOTOR DEĞİL (TSK-242 brief'i "codelaw kapsam kararı, gerekçele"): (1) bu tur motor
dosyalarında yalnız yorum değişir (Rol-1 kuralı); (2) v563/v571/v572 emsali — codelaw canlı kod ailesindedir,
test tarafı çivi `report()["ok"]`e yeni hüküm eklemez; (3) codelaw'ın üçüncü beslemesi yalnız `curuyen`i hükme
bağlar, `cozulemeyen`i SAYMAZ — bu dosya beyansız çözülemeyeni de kırmızı yapar (daha sıkı). BEDEL: codelaw
`report()` (ve onu okuyan CI duman çivileri) ops çürümesini görmez; yalnız bu dosyanın koşulduğu suite görür.

BÖLÜŞÜM: `meridian/`+`tests/` `.py` codelaw üçüncü beslemesinin; `.py` DIŞI kaynaklar v572'nin. Bu dosya yalnız
`ops/`+`deploy/`+kök `.py`yi okur ve öyle olduğu çivilidir.
"""
from __future__ import annotations

import os
import pathlib

import pytest

from meridian import codelaw
from tests.test_capa_pydisi_hedef_v571 import REPO, _atlanan_sinif as _v571_atlanan_sinif
from tests.test_sembol_capa_pydisi_v572 import _HERMES_AGENT, _py_kokleri, sembol_hukmu

#: Metni okunan kökler (özyineli) — kök düzeyi `.py` ayrıca TEK SEVİYE okunur (bugün 0 dosya; doğduğu gün görünür).
METIN_KOKLERI = ("ops", "deploy")


def _metinler(kok: pathlib.Path = REPO) -> list[tuple[str, str]]:
    """`(rel yol, yorum+docstring metni)` — codelaw'ın üçüncü besleme çıkarımı. Kökler MUTLAK geçilir (çalışma
    dizininden bağımsız); kök düzeyi `.py` aynı çıkarımla (`codelaw._dosya_yorum_metni`)."""
    ler = codelaw._yorum_metinleri(tuple(str(kok / k) for k in METIN_KOKLERI if (kok / k).is_dir()))
    ler += [(str(p), m) for p in sorted(kok.glob("*.py")) if (m := codelaw._dosya_yorum_metni(p))]
    return [(pathlib.Path(y).relative_to(kok).as_posix(), m) for y, m in ler]


def _atlanan_sinif(rel: str) -> str | None:
    """v571'in sınıflayıcısı (tek kaynak): bugünkü 50 dosyanın hiçbiri atlanmaz; ölçüm dosyası adı tarih künyesi
    taşıyan bir kök `.py` doğarsa tarihçe sınıfına düşer ve sayılır."""
    return _v571_atlanan_sinif(rel)


# =================================================================================================
# BEYANLAR — çözülemeyen (harici) çapalar
# =================================================================================================

#: (kaynak, çapa) → (sınıf, gerekçe, doğrulama yolu | None). Sınıflar v572'ninkiyle aynı (`harici` · `arsiv`).
BEYANLI_COZULEMEYEN: dict[tuple[str, str], tuple[str, str, str | None]] = {
    ("ops/sef_brifingi.py", "agent/prompt_builder.py::build_context_files_prompt"):
        ("harici", _HERMES_AGENT + "agent/prompt_builder.py içinde def build_context_files_prompt (TSK-242: şerh "
                                   "eskiden yerel ağaçta hiç var olmamış bir adı yazıyordu)", None),
    ("ops/sef_brifingi.py", "test_shell_hooks_consent.py::test_no_tty_no_flag_skips_registration"):
        ("harici", _HERMES_AGENT + "tests/agent/test_shell_hooks_consent.py içinde bir test sınıfının metodu (yol "
                                   "öneksiz; depoda aynı adlı dosya doğarsa hüküm değişir ve bu beyan öter)", None),
}

#: Modül biçimli, SEMBOL OLMAYAN eşleşmeler (v572 `MODUL_BICIMI_ALAN_ADI` biçimi). Bugün BOŞ.
MODUL_BICIMI_ALAN_ADI: dict[tuple[str, str], str] = {}


def ops_hukmu(metinler, py_kokler=None, cozulemeyen_beyan=None, alan_adi_beyan=None) -> dict:
    """v572'nin hüküm gövdesi, bu dosyanın sınıflayıcısı ve beyanlarıyla."""
    return sembol_hukmu(metinler, py_kokler=_py_kokleri() if py_kokler is None else py_kokler,
                        cozulemeyen_beyan=BEYANLI_COZULEMEYEN if cozulemeyen_beyan is None else cozulemeyen_beyan,
                        alan_adi_beyan=MODUL_BICIMI_ALAN_ADI if alan_adi_beyan is None else alan_adi_beyan,
                        atlanan_sinif=_atlanan_sinif)


_ONBELLEK: dict = {}


def _depo() -> tuple[list[tuple[str, str]], dict]:
    if "h" not in _ONBELLEK:
        metinler = _metinler()
        _ONBELLEK["m"] = metinler
        _ONBELLEK["h"] = ops_hukmu(metinler)
    return _ONBELLEK["m"], _ONBELLEK["h"]


# =================================================================================================
# A) SENTETİK — besleme uçtan uca: dosya → çıkarım → hüküm
# =================================================================================================

_HEDEF = "SABIT = 1\n\n\ndef var_olan():\n    return SABIT\n\n\nclass Sinif:\n    def metot(self):\n        return 2\n"


@pytest.fixture
def sahte_kok(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "hedef.py").write_text(_HEDEF, encoding="utf-8")
    return tmp_path


def _yaz(kok: pathlib.Path, rel: str, metin: str) -> None:
    yol = kok / rel
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")


def _sentetik(kok: pathlib.Path, **kw) -> dict:
    return ops_hukmu(_metinler(kok), py_kokler=(str(kok / "pkg"),), cozulemeyen_beyan=kw.get("coz", {}),
                     alan_adi_beyan={})


@pytest.mark.parametrize("rel", ["ops/uydurma.py", "ops/alt/uydurma.py", "deploy/oracle-a1/uydurma.py", "uydurma.py"])
def test_SENTETIK_ops_deploy_kok_py_YORUMUNDA_curuk_sembol_KIRMIZI(sahte_kok, rel):
    """Pozitif kontrol: dört yüzeyin her birinde yorumdaki olmayan sembol çürük yakalanır. Besleme kökü düşerse
    dosya hiç okunmaz, ihlal listesi boş kalır ve çivi KIRMIZI olur (mutasyon M5)."""
    _yaz(sahte_kok, rel, "# kilit burada kurulur: `hedef.py::yok_olan`\nX = 1\n")
    h = _sentetik(sahte_kok)
    assert [(i["kaynak"], i["tur"], i["capa"]) for i in h["ihlal"]] == [(rel, "curuk", "hedef.py::yok_olan")], h
    assert h["taranan"] == [rel]


def test_SENTETIK_DOCSTRING_okunur_KOD_DIZGESI_okunmaz(sahte_kok):
    """Çıkarım codelaw'ınkidir: docstring'deki çürük yakalanır, kod dizgesindeki (VERİ) hükme girmez."""
    _yaz(sahte_kok, "ops/uydurma.py",
         '"""Belge: `hedef.py::docstringde_yok`."""\n_SABIT = "hedef.py::kod_dizgesinde_yok"\n')
    h = _sentetik(sahte_kok)
    assert [i["capa"] for i in h["ihlal"]] == ["hedef.py::docstringde_yok"], h["ihlal"]


def test_SENTETIK_VAR_OLAN_sembol_ve_modul_bicimi_COZULUR(sahte_kok):
    _yaz(sahte_kok, "ops/uydurma.py", "# `hedef.py::Sinif.metot` · `hedef.var_olan` · `hedef.SABIT`\n")
    h = _sentetik(sahte_kok)
    assert h["ihlal"] == [] and sorted(c for _k, c in h["cozulen"]) == [
        "hedef.SABIT", "hedef.py::Sinif.metot", "hedef.var_olan"], h


def test_SENTETIK_MODUL_BICIMI_curuk_de_KIRMIZI(sahte_kok):
    """TSK-242'nin dördüncü çürüğünün sınıfı: sınıf METODU modül önekiyle yazılırsa modülde öyle bir ad yoktur."""
    _yaz(sahte_kok, "ops/uydurma.py", "# boyutlandırma tabanı (`hedef.metot()` = ...)\n")
    h = _sentetik(sahte_kok)
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("curuk", "hedef.metot")], h["ihlal"]


def test_SENTETIK_COZULEMEYEN_beyansiz_KIRMIZI_beyanli_SAYILIR(sahte_kok):
    capa = "dis_paket/modul.py::islev"
    _yaz(sahte_kok, "ops/uydurma.py", f"# ölçüldü: `{capa}`\n")
    beyansiz = _sentetik(sahte_kok)
    assert [(i["tur"], i["neden"]) for i in beyansiz["ihlal"]] == [("beyansiz_cozulemeyen", "kapsam_disi")]
    beyanli = _sentetik(sahte_kok, coz={("ops/uydurma.py", capa): ("harici", "sentetik", None)})
    assert beyanli["ihlal"] == [] and beyanli["beyanli_cozulemeyen"] == 1


def test_SENTETIK_MEZAR_TASI_isaretli_satir_MUAF(sahte_kok):
    _yaz(sahte_kok, "ops/uydurma.py", f"# eski ad `hedef.py::yok_olan` ({codelaw._CAPA_MUAFIYETI})\n")
    h = _sentetik(sahte_kok)
    assert h["ihlal"] == [] and h["cozulen"] == []


def test_SENTETIK_meridian_ve_tests_OKUNMAZ_bolusum(sahte_kok):
    """Bölüşüm: `meridian/`+`tests/` codelaw üçüncü beslemesinindir — bu dosya onları hiç okumaz."""
    _yaz(sahte_kok, "meridian/uydurma.py", "# `hedef.py::yok_olan`\n")
    _yaz(sahte_kok, "tests/test_uydurma.py", "# `hedef.py::yok_olan`\n")
    h = _sentetik(sahte_kok)
    assert h["ihlal"] == [] and h["taranan"] == []


# =================================================================================================
# B) GERÇEK DEPO — çürük 0 · beyansız çözülemeyen 0 · bayat beyan 0 · körlük alarmı · pozitif kontrol
# =================================================================================================

def test_GERCEK_depoda_CURUK_sembol_capasi_YOK():
    ihlal = [f"{i['kaynak']}: {i['capa']} ({i['neden']})" for i in _depo()[1]["ihlal"] if i["tur"] == "curuk"]
    assert not ihlal, ("ops/deploy/kök `.py` yorumunda çürük sembol çapası — adı tam ve TANIMLAYAN modülle yaz "
                       f"(bölünmüş/kısaltılmış ad, ithal takma ad, modül önekli metot çürük sayılır): {ihlal}")


def test_GERCEK_depoda_BEYANSIZ_COZULEMEYEN_YOK():
    ihlal = [f"{i['kaynak']}: {i['capa']} ({i['neden']})" for i in _depo()[1]["ihlal"]
             if i["tur"] == "beyansiz_cozulemeyen"]
    assert not ihlal, f"hükmü kurulamayan çapa gerekçesiz — `BEYANLI_COZULEMEYEN`e sınıfıyla beyan et: {ihlal}"


def test_BAYAT_BEYAN_YOK():
    h = _depo()[1]
    assert not sorted(set(BEYANLI_COZULEMEYEN) - h["kullanilan_cozulemeyen"])
    assert not sorted(set(MODUL_BICIMI_ALAN_ADI) - h["kullanilan_alan"])


def test_BEYAN_kayitlari_GEREKCELI():
    for (kaynak, capa), (sinif, gerekce, dogrulama) in BEYANLI_COZULEMEYEN.items():
        assert sinif == "harici" and dogrulama is None and len(gerekce) >= 60, (kaynak, capa)
        assert "::" in capa and kaynak.startswith(METIN_KOKLERI), (kaynak, capa)


def test_KORLUK_ALARMI_taranan_ve_cozulen_sayilari():
    """Ölçüldü 2026-09-27 (düzeltme sonrası): 50 dosya · 33 dosya biçimi · 221 modül biçimi çözülen. Alt sınırlar
    40 / 25 / 150: yanlış kök ya da körleşen çıkarım az dosya/çapa döndürür ve "temiz" ebediyen yeşil kalırdı."""
    metinler, h = _depo()
    taranan = set(h["taranan"])
    assert len(taranan) >= 40, len(taranan)
    for zorunlu in ("ops/sef_brifingi.py", "ops/olcum.py", "deploy/oracle-a1/geridolum.py",
                    "deploy/hindsight/hafiza_okuma_kaydi.py"):
        assert zorunlu in taranan, zorunlu
    assert not any(r.startswith(("meridian/", "tests/")) for r, _ in metinler), "bölüşüm bozuldu"
    assert sum(1 for _k, c in h["cozulen"] if "::" in c) >= 25
    assert sum(1 for _k, c in h["cozulen"] if "::" not in c) >= 150


#: Yol-tutarlı pozitif kontrol: bu turda düzeltilen dört çapa korpus yolundan (gezgin → çıkarım → çekirdek) çözülür.
DUZELTILEN = [
    ("ops/dolum_geri_dolum.py", "tests/test_dolum_geri_dolum_v475.py::test_okuma_kurallari_ITHAL_EDILIR_kopyalanmaz"),
    ("ops/olcum.py", "tests/test_olcum_araci_v328.py::test_COZULEMEYEN_YAPISAL_TAMDIR_BILINMEYEN_BICIME_TEPKI_VERIR"),
    ("ops/sasi_yukleyici.py", "ops/sasi_yukleyici.py::kaynaktan_yukle"),
    ("ops/sermaye_beyani_iade.py", "broker.PaperBroker.equity"),
]


@pytest.mark.parametrize("kaynak,capa", DUZELTILEN)
def test_POZITIF_KONTROL_duzeltilen_capa_KORPUSTA_cozulur(kaynak, capa):
    assert (kaynak, capa) in set(_depo()[1]["cozulen"]), (kaynak, capa)


def test_HARICI_beyan_yerel_hermes_agent_KAYNAGINDA_dogrulanir():
    """Harici beyanın iddiası (yerel ağaçta işlev VAR) ölçülebildiği makinede ölçülür: yerel hermes-agent ağacı yoksa
    (CI, temiz klon) atlanır ve nedeni söylenir — ölçülemeyen doğrulama yeşil sayılmaz."""
    kok = pathlib.Path(os.path.expanduser("~/.hermes/hermes-agent"))
    if not kok.is_dir():
        pytest.skip("yerel hermes-agent ağacı yok — harici beyan bu makinede doğrulanamaz")
    for dosya, ad in (("agent/prompt_builder.py", "def build_context_files_prompt("),
                      ("tests/agent/test_shell_hooks_consent.py", "def test_no_tty_no_flag_skips_registration(")):
        assert ad in (kok / dosya).read_text(encoding="utf-8"), (dosya, ad)
