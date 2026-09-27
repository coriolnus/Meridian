"""v572 — SEMBOL ÇAPASI YASASI, `.py` DIŞI KAYNAKLAR (TSK-239, 2026-09-27).

CLAUDE.md §2 satır çapasının güvenli alternatifi olarak `dosya.py::ad` SEMBOL çapasını öğütler: sembol çapası
da çürür ama SESLİ çürür — ad silinince AST'de bulunamaz. O ses yalnız çapayı bir çözücü OKURSA çıkar. Sembol
çözücüsünün tek çekirdeği `codelaw.capa_uyusmasi`dır (ikinci bir çözücü YAZILMADI — tek-kaynak yasası) ve
bugüne dek dört beslemesi vardı:
  (a) `DECLARED_*` beyan metinleri, (b) `ui/src` tsx/ts kaynağı (`codelaw._tsx_metinleri`),
  (c) `meridian/`+`tests/` `.py` YORUM/docstring metni (`codelaw._yorum_metinleri`),
  (d) `deploy/**` birim dosyaları (`tests/test_birim_capa_taramasi_v563.py::test_birim_SEMBOL_capalari_COZULUR_curuyen_YOK`).
`.py` DIŞI kaynaklar — pano js/html (`meridian/web/`), `deploy/`un birim dışı `.sh`/`.yml`/`.yaml`/`.md`/`.rules`,
`ops/*.sh`, kök betik/belge (pyproject, ansible.cfg, DESIGN.md, workflow-diagram.html, README.md,
docker-compose.yml), `altyapi/`, `.github/`, yaşayan `docs/` — HİÇBİR beslemede değildi (TSK-236 kaygı K5). Bu
dosya o beşinci beslemedir: metinleri v571'in depo gezgininden alır (`_depo_metinleri_onbellekli` — ikinci bir
gezgin yok), yüzey sınıfını v571'in sınıflayıcısından türetir ve AYNI çekirdeğe verir.

TUR BAŞI ÖLÇÜM (2026-09-27, taban df0c590b; codelaw çekirdeğiyle, pytest içi yoklama; çözücü kökü aşağıda):
  * Dosya biçimi, taranan yüzeyler: 125 çözülen (51'i pano derleme paketinde — aşağıda atlanır), 2 ÇÜRÜK,
    8 çözülemeyen. İki çürük: `deploy/oracle-a1/sir_rotasyon.sh` v447'nin P6 çivisini adının yalnız ÖNEKİYLE
    anıyordu (sembol yok); `deploy/hermes/profiles/sef/config.yaml` hermes-agent'ın `hermes_cli/` paketindeki bir
    işlevi yol öneksiz yazıyordu ve çözücü onu `meridian/config.py`ye bağlıyordu (orada yok). İkisi de bu turda
    YALNIZ YORUMDA düzeltildi (satır sayısı aynı; anahtar/değer ve komut satırı değişmedi).
  * Çözücü kökü `deploy` eklenmeden 9 çözülemeyen vardı: dokuzuncusu pano app.js'in geridolum.py'deki
    TAVAN_BAYT atfıydı — `deploy/**/*.py` (4 dosya) hiçbir çözücü kökünde değildi. `deploy` eklenince yeni
    `ikircikli` ad: 0 (ölçüldü).
  * Kalan 8 çözülemeyen sınıflandı (`BEYANLI_COZULEMEYEN`): 7 harici (hermes-agent v0.18.2 kaynağı 6, ansible-core
    2.18.19 kaynağı 1 — ikisi de yerel kurulumda elle doğrulandı) + 1 arşiv (`research/` ölçüm betiği — çözücü
    kökü dışında; bu dosya yolu ve sembolü ayrıca doğrular). Üretilmiş dosya ya da silinmiş sembol sınıfı: 0.
    Düzeltilen sef çapası artık yol önekli yazıldığı için dokuzuncu harici beyandır.
  * Modül biçimi (backtick içinde modül + nokta + sembol): operasyon yüzeylerinde (deploy/ops/kök) 54 eşleşmenin
    51'i sembole çözüldü, 3'ü sembol DEĞİLDİ (iki Hermes yapılandırma anahtar yolu + bir modül dunder'ı) →
    `MODUL_BICIMI_ALAN_ADI` beyanı. Pano (`meridian/web/`) ve yaşayan `docs/`ta biçim KAPALI: orada çözülmeyen
    12 eşleşmenin 11'i sembol değildi ya da biçimi yanlış hedefliyordu (JSON alan/blok adı, obs olay adı, yerel
    kapanış, sınıf metodunun modül önekiyle yazımı) — codelaw kapsam sınırı (1)'in ta kendisi; on ikincisi (docs)
    deponun git tarihinde hiç tanımlanmamış bir ad (TSK-239 raporu). BEDEL (ölçüldü): pano 39, docs 36
    modül-biçimli eşleşme bu dosyada ÖLÇÜLMEZ (gerekçe `MODUL_BICIMI_KAPALI`).
  * Atlanan (beyanlı) yüzeylerdeki dosya-biçimli çürük, GÖRÜNÜRLÜK için (bu dosya düzeltmez): ROADMAP 4 · tarihçe 10 ·
    üretilmiş RUNBOOK 3 (iç içe tanım: `codelaw._modul_adlari` yalnız modül ve sınıf düzeyini toplar) · birim 0 ·
    tsx 0. `.py` kör noktası (`ops/`+`deploy/` `.py` yorumları üçüncü beslemede değil — 50 dosya, 3 dosya-biçimli
    çürük) TSK-242'de kapandı: `tests/test_ops_py_yorum_capa_v574.py` bu dosyanın hüküm gövdesini o metinle çağırır.

SÖZLEŞME:
  * Çürük (`curuyen`: modül var, sembol yok) → KIRMIZI. Taban YOK (codelaw beşinci dünya emsali: sembol çürümesi
    adı olan, düzeltmesi mekanik bir kusurdur, kayıtlı borç değildir).
  * Çözülemeyen (`cozulemeyen`: hedef yok · kapsam dışı · ikircikli) → `BEYANLI_COZULEMEYEN`de gerekçeli değilse
    KIRMIZI (uydurma yasağı: yokluk kanıtlanmadı; ama sayılmayan körlük de körlüğü gizlemektir). Kaynakta artık
    bulunmayan ya da artık çözülen beyan BAYATtır → KIRMIZI.
  * Muafiyet işareti codelaw'ınki (`çapa-mezar-taşı`) — çekirdek o satırı atlar; ikinci işaret icat edilmedi.

BÖLÜŞÜM (aynı iddia iki dosyada tutulmaz): `.py` kaynak codelaw üçüncü beslemesinin; `ui/src` tsx/ts ikinci
beslemenin; birim dosyaları v563'ün; pano derleme paketi (`meridian/web/pano-assets/`) `ui/src`in kopyasıdır.
v571'in 17 çevrilmiş sembol çapalık STATİK listesi burada YOL-TUTARLI POZİTİF KONTROLdür: hepsi bu dosyanın
korpus taramasında `cozulen`e düşmelidir (düşmezse gezgin/sınıflayıcı o yüzeyi göremiyor demektir).
"""
from __future__ import annotations

import pathlib
from collections import Counter
from pathlib import PurePosixPath

import pytest

from meridian import codelaw
from tests.test_capa_pydisi_hedef_v571 import (
    BEYANLI_ATLANAN as _V571_ATLANAN,
    CEVRILEN_SEMBOL as _V571_CEVRILEN_SEMBOL,
    REPO,
    _atlanan_sinif as _v571_atlanan_sinif,
    _depo_metinleri_onbellekli,
)

# =================================================================================================
# ÇÖZÜCÜ KÖKLERİ — codelaw'ın çapa kökleri + `deploy` (kopya liste yok)
# =================================================================================================

#: `codelaw.report` sembol çözümünü `meridian` + `codelaw._EK_CAPA_KOKLERI` (tests, ops) ile kurar. `.py` DIŞI
#: kaynaklar `deploy/**/*.py`yi de çapalar (pano app.js → geridolum.py) — ek kök TEK: `deploy`.
_EK_COZUCU_KOKLERI = ("deploy",)


def _py_kokleri(kok: pathlib.Path = REPO) -> tuple[str, ...]:
    """MUTLAK kökler — codelaw yol önekli çapayı `endswith("/" + önek)` ile eşler; göreli kökte önek eşleşmez."""
    return tuple(str(kok / k) for k in ("meridian", *codelaw._EK_CAPA_KOKLERI, *_EK_COZUCU_KOKLERI))


# =================================================================================================
# YÜZEY SINIFLARI — v571'in sınıflayıcısından TÜRETİLİR, bölüşüm sınıfları eklenir
# =================================================================================================

_PY_UZANTILARI = (".py", ".pyi")
_PANO_DERLEME_ONEKI = "meridian/web/pano-assets/"
#: v571'den AYNEN alınan sınıflar (gerekçe metni v571'de yaşar — tek kaynak).
_V571_AYNEN = ("tarihce", "uretilmis", "rol1", "ssot", "skill_kutuphanesi")

BEYANLI_ATLANAN: dict[str, str] = {
    **{s: _V571_ATLANAN[s] for s in _V571_AYNEN},
    "birim": (
        "BİRİM DÜNYASI — `deploy/**` `.service`/`.conf`/`.timer`/`.path` şerhlerinin sembol çapaları (modül biçimi "
        "dahil) v563'ün `test_birim_SEMBOL_capalari_COZULUR_curuyen_YOK` çivisinde AYNI çekirdekten geçer."),
    "py_kaynagi": (
        "PYTHON KAYNAĞI — `meridian/`+`tests/` yorum/docstring metni codelaw ÜÇÜNCÜ BESLEMESİNDE ölçülür "
        "(`report()` alanı yorum_sembol_curume, ok'u düşürür); `ops/`+`deploy/`+kök `.py` yorum/docstring metni "
        "TSK-242'den beri tests/test_ops_py_yorum_capa_v574.py'de AYNI hüküm gövdesiyle (bu dosyanın sembol_hukmu) "
        "ölçülür. Bu dosyanın kapsamı `.py` DIŞIdır."),
    "tsx_beslemesi": (
        "PANO KAYNAĞI (tsx/ts) — `ui/src` `.ts`/`.tsx` codelaw İKİNCİ BESLEMESİNDE ölçülür (`report()` alanı "
        "sembol_capa_curume, v373); aynı çapayı burada ikinci kez ölçmek aynı iddiayı iki yerde tutardı. "
        "`ui/src`in tsx DIŞI dosyaları (bugün css) burada taranır."),
    "uretilmis_pano": (
        "ÜRETİLMİŞ PANO PAKETİ — `meridian/web/pano-assets/**` Vite derleme çıktısıdır (`ui/vite.config.ts` "
        "assetsDir); dizgeleri `ui/src`ten gelir ve orada ikinci beslemeyle ölçülür. Paketi de ölçmek aynı iddiayı "
        "iki yerde tutardı ve bayat derlemede kaynak düzeltilmişken kırmızı verirdi (ölçüldü: 51 çapa, 0 çürük)."),
}


def _atlanan_sinif(rel: str) -> str | None:
    """Beyanlı atlanan sınıf ya da None (taranır). v571'in `ui_kaynagi` sınıfı burada İKİYE bölünür: tsx/ts
    ikinci beslemenin (atlanır), geri kalanı (css) taranır."""
    p = PurePosixPath(rel)
    if p.suffix in _PY_UZANTILARI:
        return "py_kaynagi"
    if rel.startswith("ui/src/") and p.suffix in codelaw.TSX_UZANTILAR:
        return "tsx_beslemesi"
    if rel.startswith(_PANO_DERLEME_ONEKI):
        return "uretilmis_pano"
    sinif = _v571_atlanan_sinif(rel)
    return None if sinif == "ui_kaynagi" else sinif


# =================================================================================================
# MODÜL BİÇİMİ — yalnız operasyon yüzeylerinde açık (ölçüm)
# =================================================================================================

#: Modül biçiminin KAPALI olduğu yüzey önekleri → gerekçe. Dosya biçimi HER yüzeyde açıktır.
MODUL_BICIMI_KAPALI: dict[str, str] = {
    "meridian/web/": (
        "PANO (js/html) — backtick içindeki modül + nokta + ad burada JSON alan/blok adı, obs olay adı ya da yerel "
        "kapanıştır; ölçüldü 2026-09-27: çözülmeyen 8 eşleşmenin 8'i sembol değildi (codelaw kapsam sınırı 1'in "
        "tsx'te gördüğü sınıf). Bedel: 39 modül-biçimli eşleşme ölçülmez."),
    "ui/src/": (
        "PANO KAYNAĞI — codelaw pano tarafında YALNIZ dosya biçimini okur (kapsam sınırı 1); `ui/src`in tsx dışı "
        "dosyaları (bugün 9 css, 0 eşleşme) aynı karara tabidir."),
    "docs/": (
        "YAŞAYAN BELGE düzyazısı — ölçüldü 2026-09-27: çözülmeyen 4 eşleşmenin ikisi sınıf metodu / iç içe tanımı "
        "modül önekiyle anıyordu (sembol VAR, biçim yanlış hedefliyor), biri pano alan adı, biri deponun hiçbir "
        "sürümünde tanımlanmamış bir ad. Bedel: 36 modül-biçimli eşleşme ölçülmez."),
}


def _modul_bicimi_acik(rel: str) -> bool:
    return not rel.startswith(tuple(MODUL_BICIMI_KAPALI))


#: Modül biçimli, SEMBOL OLMAYAN eşleşmeler: (kaynak, çapa) → gerekçe. Çekirdek bunları `curuyen`e yazar; beyanlı
#: olanlar ihlal sayılmaz ama SAYILIR. Kaynakta artık bulunmayan beyan bayattır (kırmızı).
_HERMES_ANAHTAR_YOLU = (
    "Hermes `config.yaml` ANAHTAR YOLU (skills bloğundaki external_dirs listesi) — Python sembolü değil; "
    "`meridian/skills.py` ile ad çakışması tesadüf (ölçüldü 2026-09-27)")
MODUL_BICIMI_ALAN_ADI: dict[tuple[str, str], str] = {
    ("deploy/hermes/skills/meridian-olcum/SKILL.md", "skills.external_dirs"): _HERMES_ANAHTAR_YOLU,
    ("deploy/oracle-a1/deploy.sh", "skills.external_dirs"): _HERMES_ANAHTAR_YOLU,
    ("pyproject.toml", "config.__file__"): (
        "Python modül DUNDER'ı (mutmut kök-neden şerhi: ROOT'un modül dosya yolundan türetilmesi) — tanım değil; "
        "`codelaw._modul_adlari` yalnız def/class/atama toplar (ölçüldü 2026-09-27)"),
}

# =================================================================================================
# ÇÖZÜLEMEYEN ÇAPALAR — gerekçeli beyan
# =================================================================================================

_HERMES_AGENT = (
    "HARİCİ — hermes-agent kaynağı (repo DIŞI; yerel ağaç ~/.hermes/hermes-agent, sürüm v0.18.2). "
    "Sembol 2026-09-27'de yerel ağaçta elle doğrulandı: ")
_ANSIBLE_CORE = (
    "HARİCİ — ansible-core kaynağı (kurulu paket, repo DIŞI). 2026-09-27'de ansible-core 2.18.19 kurulumunda "
    "elle doğrulandı: native_helpers.py içinde def ansible_eval_concat")

#: (kaynak, çapa) → (sınıf, gerekçe, doğrulama yolu | None). Sınıflar: `harici` (repo dışı paket kaynağı) ·
#: `arsiv` (hedef depoda ama çözücü kökü dışında; doğrulama yolu verilir ve sembol AST ile ayrıca doğrulanır).
BEYANLI_COZULEMEYEN: dict[tuple[str, str], tuple[str, str, str | None]] = {
    ("deploy/ansible/dagit.yml", "ansible/template/native_helpers.py::ansible_eval_concat"):
        ("harici", _ANSIBLE_CORE, None),
    ("deploy/apisix/routes.yaml", "hermes_cli/config.py::normalize_extra_headers"):
        ("harici", _HERMES_AGENT + "hermes_cli/config.py içinde def normalize_extra_headers", None),
    ("deploy/hermes/profiles/sef/config.yaml", "hermes_cli/config.py::normalize_extra_headers"):
        ("harici", _HERMES_AGENT + "hermes_cli/config.py içinde def normalize_extra_headers (TSK-239: eskiden yol "
                                   "öneksizdi ve meridian/config.py'ye çözülüp çürük görünüyordu)", None),
    ("deploy/hermes/profiles/bekci/config.yaml", "hermes_cli/runtime_provider.py::_get_named_custom_provider"):
        ("harici", _HERMES_AGENT + "hermes_cli/runtime_provider.py içinde def _get_named_custom_provider", None),
    ("deploy/hermes/profiles/sef/config.yaml", "runtime_provider.py::_get_named_custom_provider"):
        ("harici", _HERMES_AGENT + "hermes_cli/runtime_provider.py içinde def _get_named_custom_provider (yol "
                                   "öneksiz; depoda aynı adlı dosya doğarsa hüküm değişir ve bu beyan öter)", None),
    ("deploy/hermes/profiles/sef/config.yaml", "hermes_cli/oneshot.py::run_oneshot"):
        ("harici", _HERMES_AGENT + "hermes_cli/oneshot.py içinde def run_oneshot", None),
    ("deploy/hermes/profiles/sef/config.yaml", "hermes_cli/timeouts.py::get_provider_request_timeout"):
        ("harici", _HERMES_AGENT + "hermes_cli/timeouts.py içinde def get_provider_request_timeout", None),
    ("deploy/hermes/profiles/sef/config.yaml",
     "tests/agent/test_shell_hooks_consent.py::test_no_tty_no_flag_skips_registration"):
        ("harici", _HERMES_AGENT + "tests/agent/test_shell_hooks_consent.py içinde bir test sınıfının metodu "
                                   "(pytest düğümü sınıf adını da taşır; atıf harici, burada çözülmez)", None),
    ("docs/kontrast-denetimi.md", "olc.py::_okuyucu_sayisi"):
        ("arsiv", "ARŞİV — Dub dönüşümü kontrast ölçüm betiği (research/ donmuş ölçüm arşivi, çözücü kökü DIŞINDA; "
                  "research/ altında aynı adlı birden çok olc.py var). Belge betiğin yolunu kendi 12. bölümünde "
                  "adıyla anar; sembol aşağıdaki doğrulama yolunda AST ile ölçülür",
         "research/olcumler/dub_donusumu_2026-08-24/olc.py"),
}
_COZULEMEYEN_SINIFLARI = frozenset({"harici", "arsiv"})


# =================================================================================================
# ÇEKİRDEK — saf fonksiyon (sentetik girdiyle sınanır)
# =================================================================================================

def sembol_hukmu(metinler, py_kokler: tuple[str, ...] | None = None, cozulemeyen_beyan=None,
                 alan_adi_beyan=None, atlanan_sinif=None) -> dict:
    """`(rel yol, metin)` çiftleri → hüküm. Sınıflama bu dosyada, çözüm codelaw çekirdeğinde (iki çağrı: modül
    biçimi açık ve kapalı yüzeyler).

    `atlanan_sinif`: yüzey sınıflayıcısı (varsayılan bu dosyanınki). `tests/test_ops_py_yorum_capa_v574.py` AYNI
    hüküm gövdesini `ops/`+`deploy/`+kök `.py` yorum metniyle çağırır — bu dosyanın sınıflayıcısı `.py`yi atladığı
    için kendi sınıflayıcısını geçer (ikinci bir hüküm gövdesi yazılmadı — tek kaynak).

    Dönüş: `ihlal` (tür: curuk · beyansiz_cozulemeyen) · `cozulen` (kaynak, çapa) listesi · `alan_adi` ·
    `beyanli_cozulemeyen` sayıları · `kullanilan_alan`/`kullanilan_cozulemeyen` (bayat beyan ölçümü) ·
    `atlanan` {sınıf: çapa} · `atlanan_dosya` {sınıf: dosya} · `taranan` (rel listesi)."""
    py_kokler = _py_kokleri() if py_kokler is None else py_kokler
    atlanan_sinif = _atlanan_sinif if atlanan_sinif is None else atlanan_sinif
    cozulemeyen_beyan = BEYANLI_COZULEMEYEN if cozulemeyen_beyan is None else cozulemeyen_beyan
    alan_adi_beyan = MODUL_BICIMI_ALAN_ADI if alan_adi_beyan is None else alan_adi_beyan
    out = {"ihlal": [], "cozulen": [], "alan_adi": 0, "beyanli_cozulemeyen": 0, "kullanilan_alan": set(),
           "kullanilan_cozulemeyen": set(), "atlanan": Counter(), "atlanan_dosya": Counter(), "taranan": []}
    acik, kapali = [], []
    for rel, metin in metinler:
        sinif = atlanan_sinif(rel)
        if sinif is not None:
            out["atlanan_dosya"][sinif] += 1
            out["atlanan"][sinif] += len(codelaw._SEMBOL_CAPA_DESENI.findall(metin))
            continue
        out["taranan"].append(rel)
        (acik if _modul_bicimi_acik(rel) else kapali).append((rel, metin))
    for grup, modul in ((acik, True), (kapali, False)):
        if not grup:
            continue
        h = codelaw.capa_uyusmasi(grup, py_kokler=py_kokler, modul_bicimi=modul)
        out["cozulen"].extend((c["kaynak"], c["capa"]) for c in h["cozulen"])
        for c in h["curuyen"]:
            anahtar = (c["kaynak"], c["capa"])
            if "::" not in c["capa"] and anahtar in alan_adi_beyan:
                out["alan_adi"] += 1
                out["kullanilan_alan"].add(anahtar)
                continue
            out["ihlal"].append({"kaynak": c["kaynak"], "capa": c["capa"], "tur": "curuk", "neden": c["neden"]})
        for c in h["cozulemeyen"]:
            anahtar = (c["kaynak"], c["capa"])
            if anahtar in cozulemeyen_beyan:
                out["beyanli_cozulemeyen"] += 1
                out["kullanilan_cozulemeyen"].add(anahtar)
                continue
            out["ihlal"].append({"kaynak": c["kaynak"], "capa": c["capa"], "tur": "beyansiz_cozulemeyen",
                                 "neden": c["neden"]})
    return out


_ONBELLEK: dict = {}


def _depo_hukmu() -> dict:
    if "h" not in _ONBELLEK:
        metinler, _ = _depo_metinleri_onbellekli()
        _ONBELLEK["h"] = sembol_hukmu(metinler)
    return _ONBELLEK["h"]


# =================================================================================================
# A) SENTETİK — çürük kırmızı · doğru yeşil · beyanlı yüzey atlanır ama sayılır
# =================================================================================================

@pytest.fixture
def sahte_kok(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "hedef.py").write_text(
        "SABIT = 1\n\n\ndef var_olan():\n    return SABIT\n\n\nclass Sinif:\n    def metot(self):\n"
        "        return 2\n", encoding="utf-8")
    return tmp_path


def _sentetik(sahte_kok, metinler, **kw):
    return sembol_hukmu(metinler, py_kokler=(str(sahte_kok / "pkg"),), cozulemeyen_beyan=kw.get("coz", {}),
                        alan_adi_beyan=kw.get("alan", {}))


#: (kaynak rel yolu, satır şablonu) — `.sh`/`.yml`/`.js` + deploy .md + kök toml; {c} yerine çapa gelir.
_YENI_YUZEYLER = [
    ("ops/uydurma.sh", "# bkz. `{c}` — kilit orada kurulur"),
    ("deploy/oracle-a1/uydurma.yml", "  # saklama kuralı: {c}"),
    ("meridian/web/uydurma.js", "// sayaç {c} tarafından yazılır"),
    ("deploy/oracle-a1/UYDURMA.md", "Ayrıntı `{c}` içinde."),
    ("uydurma.toml", "# kök yapılandırma: {c}"),
]


@pytest.mark.parametrize("kaynak,sablon", _YENI_YUZEYLER)
def test_SENTETIK_yeni_yuzeyde_OLMAYAN_sembol_KIRMIZI(sahte_kok, kaynak, sablon):
    """Pozitif kontrol: `.py` dışı kaynakta var olmayan sembole çapa çürük olarak yakalanır. Çapa parametreden
    gelir; yüzey tarayıcıdan düşerse ihlal listesi boş kalır ve çivi KIRMIZI olur (mutasyon M1)."""
    h = _sentetik(sahte_kok, [(kaynak, sablon.format(c="hedef.py::yok_olan") + "\n")])
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("curuk", "hedef.py::yok_olan")], h["ihlal"]
    assert h["taranan"] == [kaynak]


@pytest.mark.parametrize("kaynak,sablon", _YENI_YUZEYLER)
@pytest.mark.parametrize("capa", ["hedef.py::var_olan", "hedef.py::SABIT", "hedef.py::Sinif.metot",
                                  "pkg/hedef.py::var_olan"])
def test_SENTETIK_yeni_yuzeyde_VAR_OLAN_sembol_YESIL(sahte_kok, kaynak, sablon, capa):
    h = _sentetik(sahte_kok, [(kaynak, sablon.format(c=capa) + "\n")])
    assert h["ihlal"] == [] and h["cozulen"] == [(kaynak, capa)], h


@pytest.mark.parametrize("rel,sinif", [
    ("MERIDIAN_ENGINEERING_LOG.md", "tarihce"),
    ("docs/TASARIM-UYDURMA-2026-09-01.md", "tarihce"),
    ("docs/superpowers/plans/uydurma.md", "tarihce"),
    ("docs/RUNBOOK.md", "uretilmis"),
    ("ROADMAP.md", "rol1"),
    ("state/goal.yaml", "ssot"),
    ("skills/uydurma/SKILL.md", "skill_kutuphanesi"),
    ("deploy/oracle-a1/uydurma.service", "birim"),
    ("ops/uydurma.py", "py_kaynagi"),
    ("ui/src/pano/Uydurma.tsx", "tsx_beslemesi"),
    ("meridian/web/pano-assets/pano-UYDURMA.js", "uretilmis_pano"),
])
def test_SENTETIK_BEYANLI_yuzey_ATLANIR_ama_SAYILIR(sahte_kok, rel, sinif):
    """Çürük çapa taşıyan beyanlı yüzey hüküm almaz, ama çapası sınıf adıyla SAYILIR (sessiz atlama yok)."""
    h = _sentetik(sahte_kok, [(rel, "bkz. `hedef.py::yok_olan` ve `hedef.py::yok_iki`\n")])
    assert h["ihlal"] == [] and h["taranan"] == []
    assert h["atlanan"][sinif] == 2 and h["atlanan_dosya"][sinif] == 1, h["atlanan"]


def test_SENTETIK_ui_src_TSX_DISI_dosya_TARANIR(sahte_kok):
    """v571'in `ui_kaynagi` sınıfı bölünür: css ikinci beslemede DEĞİL, burada taranır."""
    h = _sentetik(sahte_kok, [("ui/src/uydurma.css", "/* bkz. hedef.py::yok_olan */\n")])
    assert [i["capa"] for i in h["ihlal"]] == ["hedef.py::yok_olan"], h


@pytest.mark.parametrize("kaynak", ["ops/uydurma.sh", "deploy/uydurma.yml", "uydurma.toml"])
def test_SENTETIK_MODUL_BICIMI_operasyon_yuzeyinde_ACIK(sahte_kok, kaynak):
    h = _sentetik(sahte_kok, [(kaynak, "# `hedef.var_olan` ve `hedef.yok_olan` birlikte\n")])
    assert h["cozulen"] == [(kaynak, "hedef.var_olan")], h
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("curuk", "hedef.yok_olan")], h["ihlal"]


@pytest.mark.parametrize("kaynak", ["meridian/web/uydurma.js", "docs/uydurma.md", "ui/src/uydurma.css"])
def test_SENTETIK_MODUL_BICIMI_pano_ve_docsta_KAPALI_dosya_bicimi_ACIK(sahte_kok, kaynak):
    metin = "`hedef.yok_olan` alanı; asıl yazar `hedef.py::yok_iki`\n"
    h = _sentetik(sahte_kok, [(kaynak, metin)])
    assert [i["capa"] for i in h["ihlal"]] == ["hedef.py::yok_iki"], h["ihlal"]


def test_SENTETIK_ALAN_ADI_beyani_modul_bicimini_AFFEDER_dosya_bicimini_AFFETMEZ(sahte_kok):
    kaynak = "ops/uydurma.sh"
    alan = {(kaynak, "hedef.alan_yolu"): "sentetik: yapılandırma anahtar yolu",
            (kaynak, "hedef.py::alan_yolu"): "sentetik: dosya biçimi beyanla AFFEDİLMEZ"}
    h = _sentetik(sahte_kok, [(kaynak, "# `hedef.alan_yolu` ve hedef.py::alan_yolu\n")], alan=alan)
    assert h["alan_adi"] == 1 and h["kullanilan_alan"] == {(kaynak, "hedef.alan_yolu")}
    assert [i["capa"] for i in h["ihlal"]] == ["hedef.py::alan_yolu"], h["ihlal"]


def test_SENTETIK_COZULEMEYEN_beyansiz_KIRMIZI_beyanli_SAYILIR(sahte_kok):
    kaynak, capa = "deploy/uydurma.yaml", "dis_paket/modul.py::islev"
    metin = [(kaynak, f"# ölçüldü: `{capa}`\n")]
    beyansiz = _sentetik(sahte_kok, metin)
    assert [(i["tur"], i["neden"]) for i in beyansiz["ihlal"]] == [("beyansiz_cozulemeyen", "kapsam_disi")]
    beyanli = _sentetik(sahte_kok, metin, coz={(kaynak, capa): ("harici", "sentetik", None)})
    assert beyanli["ihlal"] == [] and beyanli["beyanli_cozulemeyen"] == 1
    assert beyanli["kullanilan_cozulemeyen"] == {(kaynak, capa)}


def test_SENTETIK_MEZAR_TASI_codelaw_isaretiyle_MUAF(sahte_kok):
    mezar = codelaw._CAPA_MUAFIYETI
    h = _sentetik(sahte_kok, [("ops/uydurma.sh", f"# eski ad hedef.py::yok_olan ({mezar})\n")])
    assert h["ihlal"] == [] and h["cozulen"] == []


def test_SENTETIK_DEPLOY_koku_COZUCUDE(sahte_kok):
    """`_py_kokleri` deploy'u içerir: deploy altındaki bir `.py`nin sembolü çözülür (kök düşerse `kapsam_disi`)."""
    (sahte_kok / "deploy" / "oracle-a1").mkdir(parents=True)
    (sahte_kok / "deploy" / "oracle-a1" / "yardimci.py").write_text("TAVAN = 1\n", encoding="utf-8")
    h = sembol_hukmu([("meridian/web/uydurma.js", "// deploy/oracle-a1/yardimci.py::TAVAN\n")],
                     py_kokler=_py_kokleri(sahte_kok), cozulemeyen_beyan={}, alan_adi_beyan={})
    assert h["ihlal"] == [] and len(h["cozulen"]) == 1, h


# =================================================================================================
# B) GERÇEK DEPO — çürük 0 · beyansız çözülemeyen 0 · bayat beyan 0 · körlük alarmı · pozitif kontrol
# =================================================================================================

def test_GERCEK_depoda_CURUK_sembol_capasi_YOK():
    ihlal = [f"{i['kaynak']}: {i['capa']} ({i['neden']})" for i in _depo_hukmu()["ihlal"] if i["tur"] == "curuk"]
    assert not ihlal, ("`.py` dışı kaynakta çürük sembol çapası — hedefte ad yok. Adı düzelt; harici bir kaynağı "
                       f"gösteriyorsa yol önekiyle yaz ve `BEYANLI_COZULEMEYEN`e ekle: {ihlal}")


def test_GERCEK_depoda_BEYANSIZ_COZULEMEYEN_YOK():
    ihlal = [f"{i['kaynak']}: {i['capa']} ({i['neden']})" for i in _depo_hukmu()["ihlal"]
             if i["tur"] == "beyansiz_cozulemeyen"]
    assert not ihlal, f"hükmü kurulamayan çapa gerekçesiz — `BEYANLI_COZULEMEYEN`e sınıfıyla beyan et: {ihlal}"


def test_BAYAT_BEYAN_YOK():
    """Beyan kaynakta artık bulunmayan (ya da artık çözülen / sınıf değiştiren) bir çapayı taşıyamaz."""
    h = _depo_hukmu()
    assert not sorted(set(BEYANLI_COZULEMEYEN) - h["kullanilan_cozulemeyen"])
    assert not sorted(set(MODUL_BICIMI_ALAN_ADI) - h["kullanilan_alan"])


def test_BEYAN_kayitlari_GEREKCELI_ve_TARANAN_yuzeyde():
    for (kaynak, capa), (sinif, gerekce, dogrulama) in BEYANLI_COZULEMEYEN.items():
        assert sinif in _COZULEMEYEN_SINIFLARI and len(gerekce) >= 60, (kaynak, capa)
        assert (dogrulama is not None) == (sinif == "arsiv"), (kaynak, capa)
        assert "::" in capa and _atlanan_sinif(kaynak) is None, (kaynak, capa)
    for (kaynak, capa), gerekce in MODUL_BICIMI_ALAN_ADI.items():
        assert len(gerekce) >= 60 and "::" not in capa and _modul_bicimi_acik(kaynak), (kaynak, capa)


@pytest.mark.parametrize("anahtar", [k for k, v in BEYANLI_COZULEMEYEN.items() if v[2]])
def test_ARSIV_beyani_HEDEFTE_sembolu_TASIR(anahtar):
    """`arsiv` beyanı körlük değil yönlendirmedir: verilen yolda sembol AYNI çekirdekle çözülmelidir."""
    kaynak, capa = anahtar
    yol = BEYANLI_COZULEMEYEN[anahtar][2]
    sembol = capa.split("::", 1)[1]
    h = codelaw.capa_uyusmasi([(kaynak, f"{yol}::{sembol}")], py_kokler=(str((REPO / yol).parent),))
    assert len(h["cozulen"]) == 1 and not h["curuyen"] and not h["cozulemeyen"], h


def test_KORLUK_ALARMI_taranan_yuzeyler_ve_cozulen_sayilari():
    """Yanlış kök / sınıflama az dosya ya da az çapa döndürür ve "temiz" ebediyen yeşil kalırdı. Ölçüldü
    2026-09-27 (düzeltme sonrası): taranan dosya 148 · dosya-biçimli çözülen 75 · modül-biçimli çözülen 51."""
    h = _depo_hukmu()
    taranan = set(h["taranan"])
    assert len(taranan) >= 120, len(taranan)
    for zorunlu in ("meridian/web/app.js", "meridian/web/index.html", "deploy/oracle-a1/sir_rotasyon.sh",
                    "deploy/hermes/profiles/sef/config.yaml", "deploy/apisix/routes.yaml", "deploy/ansible/dagit.yml",
                    "deploy/oracle-a1/RUNBOOK.md", "ops/supervise.sh", "pyproject.toml", "workflow-diagram.html",
                    "docs/kontrast-denetimi.md", "altyapi/altyapi.sh"):
        assert zorunlu in taranan, zorunlu
    dosya_bicimi = [c for c in h["cozulen"] if "::" in c[1]]
    modul_bicimi = [c for c in h["cozulen"] if "::" not in c[1]]
    assert len(dosya_bicimi) >= 60, len(dosya_bicimi)
    assert len(modul_bicimi) >= 40, len(modul_bicimi)


#: Yol-tutarlı pozitif kontrol — modül biçimi, üç operasyon yüzeyinden (kaynak, çapa).
_PK_MODUL_BICIMI = [
    ("deploy/oracle-a1/litestream.yml", "storage.backup_to"),
    ("ops/ci_duman.sh", "codelaw.report"),
    ("pyproject.toml", "guard.classify_gate"),
]
#: Dosya biçimi — v571'in çevirdiklerine ek: deploy kökünü ve bu turun iki düzeltmesini kanıtlayanlar.
_PK_DOSYA_BICIMI = [
    ("meridian/web/app.js", "deploy/oracle-a1/geridolum.py::TAVAN_BAYT"),
    ("deploy/oracle-a1/sir_rotasyon.sh",
     "tests/test_sir_rotasyon_v447.py::test_P6_KREDENSIYEL_tablosu_DROPINLERLE_AYRISMAZ"),
]


@pytest.mark.parametrize("kaynak,capa", [*_V571_CEVRILEN_SEMBOL, *_PK_DOSYA_BICIMI, *_PK_MODUL_BICIMI])
def test_POZITIF_KONTROL_bilinen_capa_KORPUSTA_cozulur(kaynak, capa):
    """v571'in 17 çevrilmiş sembol çapası + deploy kökü + iki düzeltme + modül biçimi: hepsi bu dosyanın korpus
    yolundan (gezgin → sınıflayıcı → çekirdek) `cozulen`e düşmeli. Düşmezse yüzey sessizce taramadan çıkmıştır."""
    assert (kaynak, capa) in set(_depo_hukmu()["cozulen"]), (kaynak, capa)


def test_ATLANAN_yuzeyler_SAYILIR_ve_GEREKCELI():
    """Bedel yasası: atlanan her sınıf gerekçeli ve BUGÜN gerçekten bir dosya atlıyor (ölü beyan yok). Ölçüldü
    2026-09-27 (atlanan dosya-biçimli çapa / dosya): tarihçe 141/161 · üretilmiş RUNBOOK 152/1 · rol1 88/3 ·
    birim 38/67 · ssot 5/2 · skill 3/264 · tsx 349/253 · pano paketi 51/3 · py_kaynagi 494/1066 (`.py`
    dosyalarının TÜM metni sayılır — yorum ve kod birlikte; çözüm üçüncü beslemede yalnız yorumdan yapılır)."""
    h = _depo_hukmu()
    for sinif, gerekce in BEYANLI_ATLANAN.items():
        assert len(gerekce) >= 80, sinif
        assert h["atlanan_dosya"][sinif] >= 1, f"beyanlı sınıf `{sinif}` bugün hiçbir dosyayı atlamıyor"
    for sinif in ("tarihce", "uretilmis", "rol1", "birim", "tsx_beslemesi", "uretilmis_pano", "py_kaynagi"):
        assert h["atlanan"][sinif] >= 1, (sinif, dict(h["atlanan"]))
    for onek, gerekce in MODUL_BICIMI_KAPALI.items():
        assert len(gerekce) >= 80 and any(r.startswith(onek) for r in h["taranan"]), onek
