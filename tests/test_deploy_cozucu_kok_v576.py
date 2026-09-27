"""v576 — codelaw çapa çözücüsünün Python ağacında `deploy/` (TSK-244(b), 2026-09-27).

BOŞLUK (TSK-243 kaygı K1 → TSK-244): çapa dünyalarının (satır çapası py/tsx/docs + sembol çapası beyan/tsx/yorum)
adres defteri `meridian` + `codelaw._EK_CAPA_KOKLERI` ile kuruluyordu ve o sabit `tests`+`ops` idi. `deploy/**/*.py`
(4 dosya) hiçbir dünyanın adres defterinde değildi: onları gösteren çapa `hedef_yok`/`kapsam_disi` → `cozulemeyen`
kovasına düşüyor, çürük olsa da `report()["ok"]` görmüyordu (çözülemeyen ihlal sayılmaz — uydurma yasağı). Vaka:
`meridian/watchdog.py` ve `tests/test_veri_disk_esigi_v414.py` şerhleri geridolum modülünde git tarihinde hiç var
olmamış bir adı çapalıyordu; hiçbir çivi ötmedi, TSK-244(a) elle düzeltti. Elle düzeltme sınıfı kapatmaz.

DEĞİŞİKLİK (motor): `codelaw._EK_CAPA_KOKLERI` artık `deploy`u da taşır — altı çapa dünyası AYNI Python ağacını görür
(tek kaynak; `report()` onu tek yerde `capa_kokleri`ne katar). Yan etki (ölçüldü, bedelsiz): `stale_line_anchors`
`deploy/**/*.py`yi satır çapası için de tarar — 4 dosya, 0 satır çapası.

ADIM-0 ÖLÇÜMÜ (2026-09-27, taban 9a758bab; pytest içi karşı-olgusal yoklama — kök monkeypatch ile eklendi, kod
değişmeden; depo dışı `scratchpad/tsk244b/adim0.json`):
  * Karar kuralı (Rol-1): çürük ≤ 5 VE ad çakışması belirsizlik üretmiyor → EKLE. Ölçülen: çürük 0; yeni ad çakışması
    0 (deploy'un 4 taban adı meridian/tests/ops'ta YOK, deploy içinde de tekil; önceden var olan tek çakışma
    `__init__.py` — değişmedi). Modül biçimi: deploy modül adlarıyla 7 backtick eşleşmesinin 7'si DOSYA ADI
    (kuyruk `py` — `codelaw._dosya_adi_kuyrugu_mu` affeder) → yeni modül-biçimi hükmü 0.
  * Üçüncü besleme (yorum/docstring, 801 dosya): 3518 → 3525 çözülen (+7, hepsi dosya biçimi, hepsi geridolum
    hedefli: watchdog 3 · v414 3 · v98 1), çürük 0 → 0, çözülemeyen 58 → 51 (kalan 51'in hiçbiri deploy hedefli
    değil: `dosya.py` yer tutucusu 22, hermes-agent/research/mutants harici kaynaklar). Beyan+tsx beslemesi ve
    satır/metin dünyaları: fark 0. `report()["ok"]` önce True, sonra True.
  * Bedel (taze süreç, n=3, dönüşümlü): soğuk `report()` medyanı 9,42 s → 9,38 s (gürültü içinde), sıcak 2,38 →
    2,40 s.

ÇİVİLER: A) sentetik çürük — gerçek deploy modülünde OLMAYAN bir ad üç beslemenin her birine enjekte edilir,
`report()` onu `curuyen`e yazar ve `ok` düşer; kök `deploy`suz olsa çapa `cozulemeyen`e düşer ve çivi KIRMIZI.
B) yol-tutarlı pozitif kontrol — ADIM-0'da deploy köküyle çözülen yedi GERÇEK çapa, `report()`un geçtiği çözücü
kökleriyle `cozulen`e düşer. C) altı çapa dünyasının adres defterinin HEPSİ deploy'u taşır.
Olmayan ad KODDA birleştirilir: yorum ya da docstring'e yazılsaydı üçüncü besleme onu GERÇEK bir çürük sayardı.
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import codelaw
from tests.test_capa_pydisi_hedef_v571 import REPO

_DEPLOY_HEDEF = "deploy/oracle-a1/geridolum.py"
_OLMAYAN = "tsk244b_" + "sentetik_olmayan_ad"
_DOSYA_CAPASI = "geridolum.py" + "::" + _OLMAYAN
_YOLLU_CAPA = _DEPLOY_HEDEF + "::" + _OLMAYAN
_MODUL_CAPASI = "geridolum." + _OLMAYAN

#: ADIM-0'da (2026-09-27) yalnız deploy köküyle `cozulemeyen`den `cozulen`e geçen yedi gerçek çapa.
_DEPLOYLA_COZULEN = (
    ("meridian/watchdog.py", "geridolum.py::bos_bayt"),
    ("meridian/watchdog.py", "geridolum.py::TAVAN_BAYT"),
    ("meridian/watchdog.py", "deploy/oracle-a1/geridolum.py::TAVAN_BAYT"),
    ("tests/test_veri_disk_esigi_v414.py", "geridolum.py::bos_bayt"),
    ("tests/test_veri_disk_esigi_v414.py", "geridolum.py::TAVAN_BAYT"),
    ("tests/test_veri_disk_esigi_v414.py", "deploy/oracle-a1/geridolum.py::TAVAN_BAYT"),
    ("tests/test_review_backlog_v98.py", "deploy/oracle-a1/geridolum.py::TAVAN_BAYT"),
)


def _gercek_kok_mu() -> None:
    assert pathlib.Path.cwd().resolve() == REPO and (REPO / _DEPLOY_HEDEF).is_file(), (
        "report() göreli köklerle çalışır — çivi depo kökünden koşmalı ve deploy hedefi var olmalı")


@pytest.fixture
def yalitilmis(monkeypatch):
    """Körlük defteri yalıtılır: önceki testlerin `UNSCANNED` kaydı `ok`u bu deneyden bağımsız düşürmesin."""
    _gercek_kok_mu()
    monkeypatch.setattr(codelaw, "UNSCANNED", [])
    return monkeypatch


def _enjekte(mp, besleme: str, metin: str) -> None:
    if besleme == "yorum":
        asil_yorum = codelaw._yorum_metinleri
        mp.setattr(codelaw, "_yorum_metinleri",
                   lambda kokler=("meridian", "tests"), duz_kokler=(): [*asil_yorum(kokler, duz_kokler),
                                                                        ("tsk244b_sentetik.py", metin)])
        # Sonuç önbelleğinin anahtarı METNİ değil kök damgalarını taşır — enjekte metin önbellek isabetinde görünmezdi.
        mp.setattr(codelaw, "_YORUM_SEMBOL_CACHE", {})
    elif besleme == "beyan":
        asil_beyan = codelaw._beyan_metinleri
        mp.setattr(codelaw, "_beyan_metinleri", lambda: [*asil_beyan(), ("DECLARED_SINKS[tsk244b]", metin)])
    else:
        asil_tsx = codelaw._tsx_metinleri
        mp.setattr(codelaw, "_tsx_metinleri", lambda root: [*asil_tsx(root), ("tsk244b.tsx", metin)])


# =================================================================================================
# A) SENTETİK ÇÜRÜK — deploy modülünde olmayan ad, üç beslemenin her birinde `report()["ok"]`i düşürür
# =================================================================================================

@pytest.mark.parametrize("besleme,metin,capa", [
    ("yorum", "# kilit burada: `" + _DOSYA_CAPASI + "`", _DOSYA_CAPASI),
    ("yorum", "# yol önekli: `" + _YOLLU_CAPA + "`", _YOLLU_CAPA),
    ("yorum", "# modül biçimi: `" + _MODUL_CAPASI + "()`", _MODUL_CAPASI),
    ("beyan", "okuyan: `" + _DOSYA_CAPASI + "`", _DOSYA_CAPASI),
    ("tsx", "// kaynak: " + _DOSYA_CAPASI, _DOSYA_CAPASI),
], ids=["yorum-dosya", "yorum-yollu", "yorum-modul", "beyan-dosya", "tsx-dosya"])
def test_SENTETIK_deploy_modulunde_OLMAYAN_ad_report_OKUNU_DUSURUR(yalitilmis, besleme, metin, capa):
    """Çözücü `deploy`u görmezse bu çapa `hedef_yok`/`kapsam_disi` → `cozulemeyen` (modül biçiminde hiç hükme
    girmez: tek adaylı modül şartı) ve `curuyen`de görünmez → KIRMIZI. Kayıt yalnız bu enjeksiyona süzülür: gerçek
    ağacın temizliği v402/v214'ün iddiasıdır, burada tekrarlanmaz."""
    _enjekte(yalitilmis, besleme, metin)
    r = codelaw.report()
    kova, bayrak = (("yorum_sembol_capalari", "yorum_sembol_curume") if besleme == "yorum"
                    else ("sembol_capalari", "sembol_capa_curume"))
    ilgili = [(c["capa"], c["hedef"], c["sembol"], c["neden"]) for c in r[kova]["curuyen"]
              if c.get("sembol") == _OLMAYAN]
    assert ilgili == [(capa, _DEPLOY_HEDEF, _OLMAYAN, "sembol_yok")], (ilgili, r[kova].get("cozulemeyen"))
    assert r[bayrak] is True and r["ok"] is False, (r[bayrak], r["ok"])


# =================================================================================================
# B) YOL-TUTARLI POZİTİF KONTROL — gerçek deploy hedefli çapalar `report()`un çözücü kökleriyle çözülür
# =================================================================================================

def test_GERCEK_deploy_hedefli_capalar_REPORT_KOKLERIYLE_cozulur(monkeypatch):
    """Kökler `report()`un üçüncü beslemeye GEÇTİĞİ değerlerden okunur (casus), elle yazılmaz: çözücü köküne giden
    yol değişirse kontrol de onu izler. Yedi çapanın her biri `cozulen`e ve deploy hedefine düşmeli."""
    _gercek_kok_mu()
    rapor: dict = {}

    def rapor_casusu(**kw):
        rapor.update(kw)
        return {"taranan_dosya": 0, "capa_n": 0, "curuyen": []}

    with monkeypatch.context() as m:
        m.setattr(codelaw, "_yorum_sembol_capalari", rapor_casusu)
        codelaw.report()
    kaynaklar = sorted({k for k, _c in _DEPLOYLA_COZULEN})
    h = codelaw.capa_uyusmasi([(k, codelaw._dosya_yorum_metni(REPO / k)) for k in kaynaklar],
                              py_kokler=rapor["py_kokler"], modul_bicimi=True)
    cozulen = {(c["kaynak"], c["capa"]): c["hedef"] for c in h["cozulen"]}
    eksik = [kc for kc in _DEPLOYLA_COZULEN if cozulen.get(kc) != _DEPLOY_HEDEF]
    assert not eksik, (eksik, rapor["py_kokler"], h["cozulemeyen"])


# =================================================================================================
# C) TEK ÇÖZÜCÜ AĞACI — altı çapa dünyasının adres defteri de deploy'u taşır
# =================================================================================================

def test_ALTI_CAPA_DUNYASININ_adres_defteri_DEPLOYU_tasir(monkeypatch):
    """Satır çapası (py · tsx · docs) ve sembol çapası (beyan · tsx · yorum) adres defterini aynı gövdeden kurar
    (`codelaw._capa_adres_defteri`). Sonuç önbelleği boşaltılır ki yorum beslemesi de defterini kursun. Bir dünya
    kendi kök listesini yazarsa ya da `deploy` sabitten düşerse çivi KIRMIZI."""
    _gercek_kok_mu()
    cagri: list[set[pathlib.Path]] = []
    asil = codelaw._capa_adres_defteri

    def casus(kokler):
        cagri.append({pathlib.Path(k).resolve() for k in codelaw._kokler(kokler)})
        return asil(kokler)

    monkeypatch.setattr(codelaw, "_capa_adres_defteri", casus)
    monkeypatch.setattr(codelaw, "_YORUM_SEMBOL_CACHE", {})
    codelaw.report()
    assert len(cagri) >= 6, len(cagri)
    deploysuz = [sorted(map(str, k)) for k in cagri if (REPO / "deploy").resolve() not in k]
    assert not deploysuz, deploysuz
    assert all(k == cagri[0] for k in cagri), [sorted(map(str, k)) for k in cagri]
