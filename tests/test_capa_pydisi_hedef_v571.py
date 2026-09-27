"""v571 — SATIR ÇAPASI YASASI, `.py` DIŞI HEDEFLER (TSK-236, 2026-09-27).

Varlık yasağı ailesinin DÖRDÜNCÜ üyesi. Önceki üçü (hepsi "beyansız satır çapası var mı?" sorar):
  * `tests/test_kovab_dilim_v382.py::test_meridian_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK`
    (çekirdek `_capa_ihlalleri`, desen `codelaw._CAPA_DESENI`) — yalnız `meridian/*.py`, yalnız `.py` HEDEF,
  * `tests/test_tests_ops_satir_capasi_v401.py::test_tests_ops_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK`
    (çekirdek `_iki_muafiyetli_ihlaller`) — `tests/`+`ops/` `.py` kaynağı, yalnız `.py` HEDEF,
  * `tests/test_birim_capa_taramasi_v563.py::test_deploy_birim_dosyalarinda_MUAFIYETSIZ_satir_capasi_YOK`
    (çekirdek `_birim_capa_ihlalleri`, desen `_BIRIM_CAPA_DESENI`) — `deploy/**` birim dosyaları, HER hedef.
Bayatlık tarafında `codelaw.stale_text_anchors` `.py` dışı hedefleri YALNIZ `docs/` altında ve yalnız beş
uzantıda (yaml/yml/md/json/sh) ölçer, `report()["ok"]`i düşürmez. Yani `meridian/`, `tests/`, `ops/` ve
`deploy/`un birim-dışı dosyalarında `.sh`/`.yaml`/`.js`/`.html`/`.md`/`.service`… HEDEFLİ bir satır çapası
HİÇBİR çivinin görüş alanında değildi (TSK-231 kaygı K5/K6).

TUR BAŞI ÖLÇÜM (2026-09-27, taban deca767b, bitişik biçim = dosya adı + iki nokta + satır; bu dosyanın
deseniyle; ölçüm betiği depo dışı, stdlib):
  * `meridian/` `.py` kaynağı → `.py` dışı hedef: 14 (7 dosya) · `meridian/web/` (js/html): 13 `.py` dışı +
    11 `.py` hedefli (app.js; v382 yalnız kök `meridian/*.py`yi okur) = 24.
  * `tests/`: 49 (13 dosya) — 32'si sentetik fikstür/desen örneği (v563 16 · v391 11 · v314 5), 17 gerçek.
  * `ops/`: 3 (`olcum.py` 2, `supervise.sh` 1).
  * `deploy/` birim dışı: `.md` 99 · `.yml` 20 · `.sh` 4 = 123 (7'si `.py` hedefli; 25'i harici litestream
    `.go`; 89'u `deploy/HANDBOOK-PLAN.md`).
  * Kök: `DESIGN.md` 2 · `workflow-diagram.html` 1 · `pyproject.toml` 2 (harici mutmut) · `ROADMAP.md` 45
    (`.py` dışı; tüm hedeflerle 208) · `CLAUDE.md` 1.
  * Bayatlık (hedefte bugünkü satır okundu, çapanın yazıldığı commit'teki hedefle kıyaslandı; desen örneği,
    sentetik ve repo dışı hedef hariç): YANLIŞ satırı gösteren / doğrulanabilir — `meridian/` 29/33,
    `tests/` 8/13, `ops/` 0/3, `deploy/` (birim dışı, tarihçe hariç) 7/8, kök 2/3 → toplam 46/60. Doğru
    kalan 14'ü TESADÜFEN doğrudur (hedef nadir değişiyor), sözleşmeyle değil. Tam liste: TSK-236 raporu.
  * Düzeltme sonrası (bu dosyanın kendi sayımı, 2026-09-27): 940 taranan dosya, 0 ihlal, 10 doğrulanan
    kayıtlı çapa, 4 örnek/harici beyan, 28 harici `.go`, 56 muaf; atlanan (çapa/dosya) tarihçe 4030/161 ·
    rol1 211/3 · ui_kaynagi 15/262 · ssot 6/2 · üretilmiş 2/1 · skill 2/531 · birim 0/67.

SÖZLEŞME — İKİ YÜZEY SINIFI (brief TSK-236):
  * YASAK yüzey (`meridian/**` — canlıda koşan motor + panonun statik kaynağı): muafiyet işaretsiz HER satır
    çapası kırmızıdır; doğru olsa bile (v382 ile aynı hüküm). Burada çapa SEMBOL (`dosya.py::ad`) ya da
    BAŞLIK/ALINTI (hedefte aranabilir bir metin) olur.
  * İZİNLİ yüzey (test şerhi, ops, belge, `deploy/` betik/yapılandırma): satır çapası KALABİLİR ama SESSİZ
    çürüyemez — `IZINLI_CAPALAR` kaydında (kaynak, çapa) → (hedef yol, hedefte ZORUNLU metin) olarak beyan
    edilir ve her koşumda hedef dosyanın o satır(lar)ı o metni taşımak ZORUNDADIR. Beyansız çapa kırmızı;
    beyanlı ama metni tutmayan çapa (hedef kaydı) kırmızı; kaynakta artık bulunmayan kayıt (bayat beyan)
    kırmızı. Hedef `None` = beyanlı ÖRNEK/HARİCİ (doğrulanamaz; gerekçe yazılı — v563 BASLIK_CAPALARI emsali).
  * HARİCİ uzantı (`.go`): depoda hiç `.go` dosyası YOK (çivili); litestream v0.5.15 kaynağını gösterir ve
    sürüm tanığı v563'te çivilidir. Hüküm KURULMAZ (uydurma yasağı), SAYILIR.
  * Muafiyet işaretleri codelaw'ın İKİSİ (tek kaynak): `çapa-mezar-taşı` (bayat çapayı kanıt/desen örneği
    olarak alıntılayan satır) ve `çapa-sentetik` (fikstür dizgesi).

BÖLÜŞÜM (aynı iddia iki dosyada tutulmaz — v314/v401 emsali): `.py` kaynağında `.py` HEDEFİ v382 (kök
`meridian/*.py`) ve v401 (`tests/`+`ops/`) ile, `docs/*.md`de codelaw `stale_docs_line_anchors` ile ölçülür —
bu dosya orada YALNIZ `.py` dışı hedeflere bakar. Birim dosyaları v563'ündür. Geri kalan her kaynakta
(`meridian/web/*`, `meridian/<alt dizin>/*.py`, `ops/*.sh`, `deploy/` birim dışı, kök betik/belge) HER hedef.

KAPSAM DIŞI — BEYAN (`BEYANLI_ATLANAN`, bedel yasası: atlanan her yüzey ADIYLA ve SAYISIYLA görünür; bkz.
`test_ATLANAN_yuzeyler_SAYILIR_ve_GEREKCELI`). `research/` hiç GEZİLMEZ: 1659 metin dosyası / 113 MB, tek
tarama 13 s (ölçüldü 2026-09-27); donmuş ölçüm arşivi, kartlar git blob'una bağlıdır (CLAUDE.md §5).

TARİHÇE (TSK-242, 2026-09-27): E bölümünün çözüm çivisi (`test_cevrilen_SEMBOL_capalari_COZULUR_curuyen_YOK`) KALDIRILDI —
aynı 17 çapayı v572'nin yol-tutarlı pozitif kontrolü korpus yolundan çözer; aynı iddia iki dosyada tutulmaz."""
from __future__ import annotations

import pathlib
import re
from collections import Counter
from pathlib import PurePosixPath

import pytest

from meridian import codelaw
from tests.test_birim_capa_taramasi_v563 import BIRIM_UZANTILARI, _uzantilar as _v563_uzantilari

REPO = pathlib.Path(__file__).resolve().parents[1]

# =================================================================================================
# DESEN — v563'ün uzantı kümesinden TÜRETİLİR (o da codelaw._CAPA_UZANTILARI'ndan); kopya YOK
# =================================================================================================

#: v563 kümesinde OLMAYAN, depoda dosyası bulunan iki hedef uzantısı: `mjs` (`tests/*.mjs` Node
#: betikleri) ve `plist` (`ops/*.plist` launchd birimleri). İkisi de bir çapanın hedefi olabilir.
_EK_UZANTILAR = ("mjs", "plist")
_PY_UZANTILARI = frozenset({"py", "pyi"})


def _uzantilar(py_dahil: bool) -> tuple[str, ...]:
    """Hedef uzantıları — v563 kümesi + ek; `py_dahil=False` iken `.py`/`.pyi` çıkar. Uzundan kısaya
    (alternasyonda `json` `js`den, `yaml` `yml`den önce denensin)."""
    kume = {*_v563_uzantilari(), *_EK_UZANTILAR}
    if not py_dahil:
        kume -= _PY_UZANTILARI
    return tuple(sorted(kume, key=lambda u: (-len(u), u)))


def _desen(py_dahil: bool) -> re.Pattern:
    """Bitişik biçim: isteğe bağlı yol öneki + ad + bilinen uzantı + iki nokta + satır (+ aralık). Ad harf
    ya da alt çizgiyle başlar (adres:port ve sürüm dizgeleri eşleşmez) — v563 `_BIRIM_CAPA_DESENI` ile aynı
    gövde, farklı uzantı kümesi."""
    return re.compile(r"((?:[\w.@-]+/)*)([^\W\d][\w.@-]*\.(?:"
                      + "|".join(re.escape(u) for u in _uzantilar(py_dahil))
                      + r")):(\d+)(?:-(\d+))?")


_DESEN_HEPSI = _desen(True)
_DESEN_PYDISI = _desen(False)

#: ÖN SÜZGEÇ (yalnız hız): her bitişik çapa "ad karakteri + iki nokta + rakam" taşır; taşımayan satır
#: desene hiç sokulmaz. Hükmü değiştirmez — desenin eşleşebildiği her satır bu süzgeçten geçer.
_ON_SUZGEC = re.compile(r"\w:\d")


def _muafiyetler() -> tuple[str, str]:
    """TEK KAYNAK codelaw (v382/v401/v563 ile aynı iki işaret)."""
    return codelaw._CAPA_MUAFIYETI, codelaw._CAPA_SENTETIK_ISARETI


# =================================================================================================
# YÜZEY SINIFLARI — beyanlı atlanan · birim (v563) · yasak · izinli
# =================================================================================================

#: HARİCİ hedef uzantıları → gerekçe. Depoda bu uzantılı dosya YOKTUR (`test_HARICI_uzanti_depoda_YOK`).
_HARICI_UZANTILAR = {
    "go": ("litestream v0.5.15 kaynağı (repo DIŞI, sürüm-sabitli: o sürümde satır numarası değişmez); "
           "sürüm tanığı `test_birim_capa_taramasi_v563.py::test_harici_litestream_capalari_SURUM_TANIGI_sabit`"),
}

_ROL1_YUZEYLERI = frozenset({"ROADMAP.md", "CLAUDE.md", "AGENTS.md"})
_SSOT_STATE = ("state/goal.yaml", "state/bounds.yaml")
_TARIHCE_TEK_DOSYA = frozenset({"MERIDIAN_ENGINEERING_LOG.md", "deploy/HANDBOOK-PLAN.md"})
#: Adındaki tarih künyesi bu köklerde tarihçe SAYILMAZ (kod/test/ops dosyası tarihli ad taşısa da yaşar).
_TARIHSIZ_KOKLER = ("meridian/", "tests/", "ops/")

#: BEYANLI ATLANAN yüzey sınıfı → gerekçe. Atlanan her dosyanın çapaları SAYILIR (görünürlük), hüküm almaz.
BEYANLI_ATLANAN: dict[str, str] = {
    "tarihce": (
        "TARİHÇE BELGESİ — yazıldığı gün doğruydu, geriye dönük düzeltme tarihi tahrif eder (brief TSK-236 + "
        "codelaw `_docs_capa_disi` sınıf (a)/(c) emsali): `MERIDIAN_ENGINEERING_LOG.md`, `docs/TASARIM-*`, "
        "`docs/superpowers/**`, `meridian/`·`tests/`·`ops/` dışında adında `-YYYY-AA-GG` künyesi taşıyan "
        "her dosya (ör. `docs/ARASTIRMA-…`, `docs/degerlendirme/*-2026-09-06-*.json`, kök `AUDIT-…`) ve "
        "kendi başında 'tarihsel kayıt' diye beyanlı `deploy/HANDBOOK-PLAN.md` (2026-08-01 belgeleme turu "
        "planı). `research/` da bu sınıftadır ama gezilmez (modül belgesi)."),
    "uretilmis": (
        "ÜRETİLMİŞ — `docs/RUNBOOK.md` `ops/runbook_uret.py` çıktısıdır, elle düzenlenmez; çapası kaynağında "
        "(`ops/*.sh` başlığı ya da günlük) düzeltilir ve kaynak zaten bu dosyanın ya da v401'in kapsamındadır."),
    "rol1": (
        "ROL-1 YAZIM YÜZEYİ — `ROADMAP.md`, `CLAUDE.md` (ve symlink'i `AGENTS.md`) yalnız Rol-1 tarafından "
        "yazılır (CLAUDE.md §3); çapaları ayrı bir Rol-1 kalemidir. ROADMAP'in §8 arşivi ayrıca tarihçedir."),
    "ssot": (
        "İZLİ SSoT — `state/goal.yaml`, `state/bounds.yaml`: yazımı Rol-1 + worker DURMUŞKEN (CLAUDE.md §2); "
        "bu yüzeyi taşıyan kalem canlı-duruş penceresi ister."),
    "ui_kaynagi": (
        "PANO KAYNAĞI — `ui/src/**`: `.py` hedefleri codelaw TSX dünyasında ölçülür; `.py` dışı hedefli "
        "çapaları düzeltmek UI derlemesi + dağıtımın mtime kapısını tetikler — ayrı kalem."),
    "skill_kutuphanesi": (
        "SKILL KÜTÜPHANESİ — `skills/**` ajanın İngilizce skill metinleri ve betikleridir (skill_evolve "
        "taslak yazar); bu deponun motor/test/ops yüzeyi değil — ayrı kalem."),
    "birim": (
        "BİRİM DÜNYASI — `deploy/**` `.service`/`.conf`/`.timer`/`.path` dosyaları v563'ündür (her hedef, "
        "sıfır tolerans); aynı iddia iki dosyada tutulmaz."),
}


def _atlanan_sinif(rel: str) -> str | None:
    """Beyanlı atlanan yüzey sınıfı ya da None (taranır)."""
    p = PurePosixPath(rel)
    if rel in _ROL1_YUZEYLERI:
        return "rol1"
    if rel in _SSOT_STATE:
        return "ssot"
    if (rel in _TARIHCE_TEK_DOSYA or rel.startswith(("docs/superpowers/", "research/"))
            or (rel.startswith("docs/") and p.name.startswith("TASARIM-"))
            or (not rel.startswith(_TARIHSIZ_KOKLER) and codelaw._DOCS_TARIHLI_TESHIS_RE.search(p.name))):
        return "tarihce"
    if rel == "docs/RUNBOOK.md":
        return "uretilmis"
    if rel.startswith("ui/src/"):
        return "ui_kaynagi"
    if rel.startswith("skills/"):
        return "skill_kutuphanesi"
    if rel.startswith("deploy/") and p.suffix.lstrip(".") in BIRIM_UZANTILARI:
        return "birim"
    return None


def _hedef_desen(rel: str) -> re.Pattern:
    """Bölüşüm: `.py` HEDEFİNİ başka bir çivinin ölçtüğü kaynakta yalnız `.py` dışı hedefler taranır."""
    p = PurePosixPath(rel)
    py_baska_civide = (
        (p.suffix == ".py" and (p.parent.as_posix() == "meridian" or rel.startswith(("tests/", "ops/"))))
        or (rel.startswith("docs/") and p.suffix == ".md"))
    return _DESEN_PYDISI if py_baska_civide else _DESEN_HEPSI


def _yuzey(rel: str) -> str:
    return "yasak" if rel.startswith("meridian/") else "izinli"


# =================================================================================================
# İZİNLİ YÜZEYDE KALAN SATIR ÇAPALARI — beyan + doğrulama (hedef satır beyan edilen metni taşımalı)
# =================================================================================================
#: (kaynak yol, çapanın yol/ad kısmı, satır, aralık sonu | None) → (hedef yol | None, hedefte ZORUNLU metin |
#: hedef None iken gerekçe). Çapa metni anahtardan KURULUR (`_capa_metni`) — bu dosyanın kendi kaynağında iki
#: nokta + satır biçimi hiç geçmesin, kayıt satırları kendi yasasını ihlal etmesin (v401 (e) emsali).
#: Her kayıt 2026-09-27'de elle doğrulandı: çapanın yazıldığı commit'teki hedef satır ile bugünkü aynı şeyi
#: gösteriyor. Hedef değişip metin kayarsa kayıt KIRMIZI olur — o gün çapa sembol/başlık çapasına çevrilir.
IZINLI_CAPALAR: dict[tuple[str, str, int, int | None], tuple[str | None, str]] = {
    ("ops/olcum.py", "ops/keepalive.sh", 46, None): ("ops/keepalive.sh", "obs.alarm('MECHANISM_STALE'"),
    ("ops/supervise.sh", "ops/keepalive.sh", 2, 3): ("ops/keepalive.sh", "~/Documents'a TCC engeli"),
    ("tests/test_olcum_araci_v328.py", "ops/keepalive.sh", 46, None):
        ("ops/keepalive.sh", "obs.alarm('MECHANISM_STALE'"),
    ("tests/test_h3_tur2_v174.py", "bakim_h9.sh", 59, None):
        ("deploy/oracle-a1/bakim_h9.sh", 'sed -i "/^Environment=MERIDIAN_DASH_TOKEN=/d"'),
    ("tests/test_capa_kimligi_slug_v324.py", "ui/src/pano/yuzeyler/antrenman/Sprint.tsx", 120, None):
        ("ui/src/pano/yuzeyler/antrenman/Sprint.tsx", 'kimlik="sprint"'),
    ("tests/test_capa_kimligi_slug_v324.py", "ui/src/pano/yuzeyler/antrenman/Hermes.tsx", 67, None):
        ("ui/src/pano/yuzeyler/antrenman/Hermes.tsx", 'kimlik="hermes"'),
    ("tests/test_skill_cleanup_v121.py", "workflow.js", 28, None): ("meridian/web/workflow.js", '{id:"scan",'),
    ("deploy/oracle-a1/cutover.sh", "keepalive.sh", 26, None): ("ops/keepalive.sh", "grep -q 'keepalive\\.sh'"),
    ("DESIGN.md", "docs/BASELINE-2026-08-06.md", 92, None):
        ("docs/BASELINE-2026-08-06.md", "`flat-type-hierarchy`"),
    # --- hedef None: beyanlı ÖRNEK / HARİCİ (doğrulanamaz; gerekçe yazılı) ---
    ("deploy/hermes/skills/meridian-olcum/SKILL.md", "dosya.py", 123, None):
        (None, "bot skill metninde KURALIN KENDİSİNİ örnekleyen uydurma çapa (gerçek bir dosyayı göstermez); "
               "metin canlı hermes skill kütüphanesine gider, işaret gürültüsü eklenmedi"),
    ("pyproject.toml", "configuration.py", 100, 113):
        (None, "mutmut 3.7.0 kaynağı (kurulu paket, repo DIŞI, sürüm-sabitli) — şerh anahtar adlarının "
               "ezberden değil kurulu sürümden ölçüldüğünü kanıt olarak gösterir"),
    ("pyproject.toml", "__main__.py", 264, None):
        (None, "mutmut 3.7.0 kaynağı (kurulu paket, repo DIŞI, sürüm-sabitli) — `setup_source_paths` "
               "davranışının kanıtı; pyproject şerhi sürümü adıyla taşır"),
    ("tests/test_hafiza_genel_bakis_v388.py", "home-view.tsx", 160, 173):
        (None, "Hindsight control plane @ ebad4782 kaynağı — repo DIŞI; cümlenin kendisi bu çapanın buradan "
               "doğrulanamadığını söyler (takimyildizi.tsx'teki dış çapanın alıntısı)"),
}


def _capa_metni(ad: str, n1: int, n2: int | None) -> str:
    return f"{ad}:{n1}" + (f"-{n2}" if n2 is not None else "")


def _kayit_sozlugu(kayit) -> dict[tuple[str, str], tuple[str | None, str]]:
    """Tuple anahtarlı kayıt → (kaynak, çapa metni) anahtarlı sözlük (tarayıcının eşleşme anahtarı)."""
    return {(k, _capa_metni(ad, n1, n2)): v for (k, ad, n1, n2), v in kayit.items()}


def _capa_parcala(capa: str):
    m = _DESEN_HEPSI.fullmatch(capa)
    assert m, f"kayıttaki çapa metni desene uymuyor: {capa}"
    return m.group(1), m.group(2), int(m.group(3)), (int(m.group(4)) if m.group(4) else None)


def _kayit_hukmu(capa: str, hedef_yol: str, hedef_metin: str, kok: pathlib.Path) -> str | None:
    """Beyanlı çapanın doğrulaması: None = tutuyor, aksi hâlde çürüme nedeni."""
    onek, ad, n1, n2 = _capa_parcala(capa)
    tam = (onek + ad).lstrip("./")
    if not (hedef_yol == tam or hedef_yol.endswith("/" + tam)):
        return "hedef_uyusmaz"
    yol = kok / hedef_yol
    if not yol.is_file():
        return "hedef_yok"
    satirlar = yol.read_text(encoding="utf-8").splitlines()
    ust = n2 if n2 is not None else n1
    if n1 < 1 or ust > len(satirlar) or n1 > ust:
        return "menzil_disi"
    if hedef_metin not in "\n".join(satirlar[n1 - 1:ust]):
        return "metin_tutmuyor"
    return None


def capa_hukmu(metinler, kayit=None, kok: pathlib.Path = REPO) -> dict:
    """ÇEKİRDEK: `(rel yol, metin)` çiftleri → hüküm. Saf fonksiyon (sentetik girdiyle sınanır).

    Dönüş: `ihlal` (tür: yasak · beyansiz · curuk) · `dogrulanan` · `ornek` · `harici` · `muaf` sayıları ·
    `atlanan` {sınıf: çapa sayısı} · `atlanan_dosya` {sınıf: dosya sayısı} · `taranan_dosya` · `kullanilan`
    (eşleşen kayıt anahtarları — bayat kayıt ölçümü için)."""
    kayit = _kayit_sozlugu(IZINLI_CAPALAR if kayit is None else kayit)
    muaflar = _muafiyetler()
    out = {"ihlal": [], "dogrulanan": 0, "ornek": 0, "harici": 0, "muaf": 0,
           "atlanan": Counter(), "atlanan_dosya": Counter(), "taranan_dosya": 0, "kullanilan": set()}
    for rel, metin in metinler:
        sinif = _atlanan_sinif(rel)
        if sinif is not None:
            out["atlanan_dosya"][sinif] += 1
            out["atlanan"][sinif] += sum(1 for satir in metin.splitlines() if _ON_SUZGEC.search(satir)
                                         for _ in _DESEN_HEPSI.finditer(satir))
            continue
        out["taranan_dosya"] += 1
        desen, yuzey = _hedef_desen(rel), _yuzey(rel)
        for i, satir in enumerate(metin.splitlines(), 1):
            if not _ON_SUZGEC.search(satir):
                continue
            eslesme = list(desen.finditer(satir))
            if not eslesme:
                continue
            if any(m in satir for m in muaflar):
                out["muaf"] += len(eslesme)
                continue
            for m in eslesme:
                capa = m.group(0)
                yer = {"kaynak": rel, "satir": i, "capa": capa}
                if yuzey == "yasak":
                    out["ihlal"].append({**yer, "tur": "yasak"})
                    continue
                anahtar = (rel, capa)
                if anahtar in kayit:
                    out["kullanilan"].add(anahtar)
                    hedef_yol, metin_ya_da_gerekce = kayit[anahtar]
                    if hedef_yol is None:
                        out["ornek"] += 1
                        continue
                    neden = _kayit_hukmu(capa, hedef_yol, metin_ya_da_gerekce, kok)
                    if neden is None:
                        out["dogrulanan"] += 1
                    else:
                        out["ihlal"].append({**yer, "tur": "curuk", "neden": neden})
                    continue
                if m.group(2).rsplit(".", 1)[1] in _HARICI_UZANTILAR:
                    out["harici"] += 1
                    continue
                out["ihlal"].append({**yer, "tur": "beyansiz"})
    return out


# =================================================================================================
# GERÇEK DEPO METİNLERİ
# =================================================================================================

TARANAN_KOKLER = ("meridian", "tests", "ops", "deploy", "docs", "ui/src", "altyapi", ".github", "skills")
_METIN_UZANTILARI = frozenset({
    "py", "sh", "md", "yml", "yaml", "js", "mjs", "ts", "tsx", "html", "css", "json", "jsonl", "txt", "hcl",
    "rules", "ini", "plist", "toml", "cfg", "service", "conf", "timer", "path", "iskelet", "tf"})
_ATLA_DIZIN = frozenset({"__pycache__", "node_modules", ".venv", ".git", "mutants", ".pytest_cache"})


def _depo_metinleri() -> tuple[list[tuple[str, str]], list[str]]:
    """(rel, metin) listesi + okunamayanlar. Kök düzeyi tek seviye; `state/`ten yalnız iki izli SSoT."""
    yollar: list[pathlib.Path] = []
    for k in TARANAN_KOKLER:
        kok = REPO / k
        if kok.is_dir():
            yollar.extend(f for f in sorted(kok.rglob("*"))
                          if f.is_file() and not any(p in _ATLA_DIZIN for p in f.relative_to(REPO).parts))
    yollar.extend(f for f in sorted(REPO.iterdir()) if f.is_file())
    yollar.extend(REPO / s for s in _SSOT_STATE if (REPO / s).is_file())
    metinler, okunamayan = [], []
    for f in yollar:
        if f.suffix.lstrip(".") not in _METIN_UZANTILARI:
            continue
        rel = f.relative_to(REPO).as_posix()
        try:
            metinler.append((rel, f.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError) as e:
            okunamayan.append(f"{rel}: {type(e).__name__}")
    return metinler, okunamayan


_ONBELLEK: dict = {}


def _depo_metinleri_onbellekli() -> tuple[list[tuple[str, str]], list[str]]:
    if "m" not in _ONBELLEK:
        _ONBELLEK["m"] = _depo_metinleri()
    return _ONBELLEK["m"]


def _depo_hukmu() -> dict:
    if "h" not in _ONBELLEK:
        metinler, okunamayan = _depo_metinleri_onbellekli()
        h = capa_hukmu(metinler)
        h["okunamayan"] = okunamayan
        h["rel_kumesi"] = {r for r, _ in metinler}
        _ONBELLEK["h"] = h
    return _ONBELLEK["h"]


# =================================================================================================
# A) TEK KAYNAK — uzantılar v563'ten, işaretler codelaw'dan; desen codelaw/v563 desenlerinin ÜST KÜMESİ
# =================================================================================================

def test_muafiyet_isaretleri_CODELAW_TEK_KAYNAGINDAN_gelir():
    assert _muafiyetler() == ("çapa-mezar-taşı", "çapa-sentetik")


def test_uzanti_kumesi_V563ten_TURETILIR_ek_ikisi_ayri():
    kume = set(_uzantilar(True))
    assert set(_v563_uzantilari()) <= kume
    assert kume - set(_v563_uzantilari()) == set(_EK_UZANTILAR)
    assert not (set(_uzantilar(False)) & _PY_UZANTILARI)
    assert {"sh", "yaml", "yml", "js", "html", "md", "service", "conf", "go"} <= set(_uzantilar(False))


@pytest.mark.parametrize("ornek", [
    "uydurma.yaml:27", "uydurma.sh:12-30", "ops/uydurma-run.sh:45", "uydurma.service:176",  # çapa-sentetik: desen örneği (TSK-236)
    "cmd/uydurma/main_notwindows.go:20", "uydurma.js:4944", "uydurma_modul.py:7",  # çapa-sentetik: desen örneği (TSK-236)
])
def test_desen_CODELAW_ve_V563_desenlerinin_UST_KUMESI(ornek):
    """Ayrışma çivisi: codelaw'ın iki deseni ve v563'ün deseni neyi görüyorsa bu dosyanın `hepsi` deseni de
    AYNI metinle görür (kopya daralırsa "temiz" der)."""
    from tests.test_birim_capa_taramasi_v563 import _BIRIM_CAPA_DESENI
    onlarin = [m.group(0) for d in (codelaw._CAPA_DESENI, codelaw._TEXT_CAPA_DESENI, _BIRIM_CAPA_DESENI)
               for m in d.finditer(ornek)]
    assert onlarin, f"örnek en az bir kardeş desende eşleşmeli (yoksa çivi boşta): {ornek}"
    bizim = [m.group(0) for m in _DESEN_HEPSI.finditer(ornek)]
    for c in onlarin:
        assert any(c in b for b in bizim), f"kardeş desen `{c}` görüyor, v571 görmüyor: {bizim}"


def test_desen_UST_KUMESI_canli_korpus():
    """Ayrışma çivisi (canlı korpus): taranan her dosyada codelaw'ın iki deseninin ve v563 deseninin gördüğü
    her eşleşme bu dosyanın `hepsi` deseninin bir eşleşmesinin içinde kalır."""
    from tests.test_birim_capa_taramasi_v563 import _BIRIM_CAPA_DESENI
    metinler, _ = _depo_metinleri_onbellekli()
    kacan = []
    for rel, metin in metinler:
        if _atlanan_sinif(rel) is not None:
            continue
        for i, satir in enumerate(metin.splitlines(), 1):
            if not _ON_SUZGEC.search(satir):
                continue
            bizim = [m.group(0) for m in _DESEN_HEPSI.finditer(satir)]
            for d in (codelaw._CAPA_DESENI, codelaw._TEXT_CAPA_DESENI, _BIRIM_CAPA_DESENI):
                kacan.extend(f"{rel} satır {i}: {m.group(0)}" for m in d.finditer(satir)
                             if not any(m.group(0) in b for b in bizim))
    assert not kacan, kacan[:20]


# =================================================================================================
# B) SENTETİK — çürük kırmızı · doğru yeşil · beyanlı tarihçe atlanır ama sayılır
# =================================================================================================

@pytest.fixture
def sahte_kok(tmp_path):
    (tmp_path / "ops").mkdir()
    (tmp_path / "deploy").mkdir()
    (tmp_path / "ops" / "hedef.sh").write_text("#!/bin/bash\n# başlık\nset -e\nrm -f /tmp/kilit\n", encoding="utf-8")
    (tmp_path / "deploy" / "hedef.yml").write_text("a: 1\nretention: 24h\nb: 2\n", encoding="utf-8")
    return tmp_path


#: Tuple anahtar (kaynak, çapa yolu, satır, aralık sonu) — gerçek kayıtla aynı biçim.
_SENTETIK_KAYIT = {
    ("ops/kaynak.py", "ops/hedef.sh", 4, None): ("ops/hedef.sh", "rm -f /tmp/kilit"),
    ("tests/test_x.py", "deploy/hedef.yml", 2, None): ("deploy/hedef.yml", "retention: 24h"),
}


@pytest.mark.parametrize("kaynak,satir,capa_yolu,n", [
    ("ops/kaynak.py", "# kilit ops/hedef.sh:3 satırında siliniyor", "ops/hedef.sh", 3),  # çapa-sentetik: çürük fikstür (TSK-236)
    ("tests/test_x.py", "# saklama deploy/hedef.yml:1 anahtarında", "deploy/hedef.yml", 1),  # çapa-sentetik: çürük fikstür (TSK-236)
])
def test_SENTETIK_sh_ve_yml_hedefli_CURUK_capa_KIRMIZI(sahte_kok, kaynak, satir, capa_yolu, n):
    """Pozitif kontrol: `.sh`/`.yml` hedefli, beyanlı ama YANLIŞ satırı gösteren çapa yakalanır (beyan edilen
    metin o satırda yok → `metin_tutmuyor`); aynı çapa beyansızken `beyansiz` olarak yakalanır. Çapa metni
    desenden DEĞİL parametreden gelir: uzantı desenden düşerse ihlal listesi boş kalır ve çivi KIRMIZI olur."""
    metin = "rm -f /tmp/kilit" if capa_yolu.endswith(".sh") else "retention: 24h"
    kayit = {(kaynak, capa_yolu, n, None): (capa_yolu, metin)}
    h = capa_hukmu([(kaynak, satir + "\n")], kayit=kayit, kok=sahte_kok)
    assert [(i["tur"], i.get("neden"), i["capa"]) for i in h["ihlal"]] == [
        ("curuk", "metin_tutmuyor", _capa_metni(capa_yolu, n, None))], h["ihlal"]
    beyansiz = capa_hukmu([(kaynak, satir + "\n")], kayit={}, kok=sahte_kok)
    assert [i["tur"] for i in beyansiz["ihlal"]] == ["beyansiz"], beyansiz["ihlal"]


@pytest.mark.parametrize("kaynak,satir", [
    ("ops/kaynak.py", "# kilit ops/hedef.sh:4 satırında siliniyor"),  # çapa-sentetik: doğru fikstür (TSK-236)
    ("tests/test_x.py", "# saklama deploy/hedef.yml:2 anahtarında"),  # çapa-sentetik: doğru fikstür (TSK-236)
])
def test_SENTETIK_sh_ve_yml_hedefli_DOGRU_capa_YESIL(sahte_kok, kaynak, satir):
    h = capa_hukmu([(kaynak, satir + "\n")], kayit=_SENTETIK_KAYIT, kok=sahte_kok)
    assert h["ihlal"] == [] and h["dogrulanan"] == 1, h


def test_SENTETIK_hedef_KAYARSA_kayit_KIRMIZIya_doner(sahte_kok):
    """Hedefin başına tek satır eklenir: beyanlı doğru çapa artık metni tutmaz — SESLİ çürüme."""
    satir = "# kilit ops/hedef.sh:4 satırında siliniyor\n"  # çapa-sentetik: fikstür (TSK-236)
    assert capa_hukmu([("ops/kaynak.py", satir)], kayit=_SENTETIK_KAYIT, kok=sahte_kok)["ihlal"] == []
    h = sahte_kok / "ops" / "hedef.sh"
    h.write_text("# yeni ilk satır\n" + h.read_text(encoding="utf-8"), encoding="utf-8")
    ihlal = capa_hukmu([("ops/kaynak.py", satir)], kayit=_SENTETIK_KAYIT, kok=sahte_kok)["ihlal"]
    assert [(i["tur"], i["neden"]) for i in ihlal] == [("curuk", "metin_tutmuyor")], ihlal


def test_SENTETIK_BAYAT_KAYIT_kullanilanlar_disinda_kalir(sahte_kok):
    """Kaynakta hiç geçmeyen kayıt `kullanilan` kümesine girmez — gerçek depo çivisi farkı bayat beyan sayar."""
    h = capa_hukmu([("ops/kaynak.py", "# çapasız satır\n")], kayit=_SENTETIK_KAYIT, kok=sahte_kok)
    assert h["kullanilan"] == set() and h["ihlal"] == []


@pytest.mark.parametrize("satir,capa", [
    ("// bkz. uydurma.js:4944 üçlü dalı", ("uydurma.js", 4944)),  # çapa-sentetik: yasak yüzey fikstürü (TSK-236)
    ("# model tarafı: goal.yaml:62 sabit", ("goal.yaml", 62)),  # çapa-sentetik: yasak yüzey fikstürü (TSK-236)
])
def test_SENTETIK_YASAK_yuzeyde_DOGRU_capa_bile_KIRMIZI(sahte_kok, satir, capa):
    """Motor yüzeyinde kayıt HİÇ okunmaz: beyanlı olsa da kırmızı (v382 ile aynı hüküm)."""
    kayit = {("meridian/web/x.js", capa[0], capa[1], None): ("ops/hedef.sh", "set -e")}
    h = capa_hukmu([("meridian/web/x.js", satir + "\n")], kayit=kayit, kok=sahte_kok)
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("yasak", _capa_metni(*capa, None))], h["ihlal"]


@pytest.mark.parametrize("rel,sinif", [
    ("MERIDIAN_ENGINEERING_LOG.md", "tarihce"),
    ("docs/TASARIM-UYDURMA-2026-09-01.md", "tarihce"),
    ("docs/superpowers/plans/uydurma.md", "tarihce"),
    ("docs/ARASTIRMA-UYDURMA-2026-08-13.md", "tarihce"),
    ("deploy/HANDBOOK-PLAN.md", "tarihce"),
    ("docs/RUNBOOK.md", "uretilmis"),
    ("ROADMAP.md", "rol1"),
    ("ui/src/pano/Uydurma.tsx", "ui_kaynagi"),
])
def test_SENTETIK_BEYANLI_yuzey_ATLANIR_ama_SAYILIR(sahte_kok, rel, sinif):
    """Çürük çapa taşıyan beyanlı yüzey hüküm almaz, ama çapası sınıf adıyla SAYILIR (sessiz atlama yok)."""
    metin = "bkz. ops/hedef.sh:1 ve deploy/hedef.yml:3\n"  # çapa-sentetik: atlanan yüzey fikstürü (TSK-236)
    h = capa_hukmu([(rel, metin)], kayit={}, kok=sahte_kok)
    assert h["ihlal"] == [] and h["taranan_dosya"] == 0
    assert h["atlanan"][sinif] == 2 and h["atlanan_dosya"][sinif] == 1, h["atlanan"]


def test_SENTETIK_MUAFIYET_isaretleri_GECER_isaretsiz_YAKALANIR(sahte_kok):
    mezar, sentetik = _muafiyetler()
    ham = "# eski: ops/hedef.sh:3"  # çapa-sentetik: fikstür (TSK-236)
    assert [i["tur"] for i in capa_hukmu([("ops/k.sh", ham)], kayit={}, kok=sahte_kok)["ihlal"]] == ["beyansiz"]
    for isaret in (mezar, sentetik):
        h = capa_hukmu([("ops/k.sh", f"{ham} ({isaret})")], kayit={}, kok=sahte_kok)
        assert h["ihlal"] == [] and h["muaf"] == 1


def test_SENTETIK_HARICI_go_hedefi_SAYILIR_hukum_ALMAZ(sahte_kok):
    h = capa_hukmu([("deploy/x.yml", "# db.go:1030 dosya yoksa yaratmaz\n")], kayit={}, kok=sahte_kok)  # çapa-sentetik: fikstür (TSK-236)
    assert h["ihlal"] == [] and h["harici"] == 1


@pytest.mark.parametrize("rel,satir,beklenen", [
    # `.py` kaynağında `.py` hedefi v382/v401'indir → burada görünmez; `.py` dışı hedef görünür
    ("tests/test_x.py", "# uydurma_modul.py:7 ve uydurma.sh:9", ["uydurma.sh:9"]),  # çapa-sentetik: bölüşüm fikstürü (TSK-236)
    # `.py` olmayan kaynakta (ops betiği, deploy belgesi, pano js) `.py` hedefi de BURADA görünür
    ("ops/x.sh", "# uydurma_modul.py:7 ve uydurma.sh:9", ["uydurma_modul.py:7", "uydurma.sh:9"]),  # çapa-sentetik: bölüşüm fikstürü (TSK-236)
    ("deploy/x.md", "`uydurma_modul.py:7`", ["uydurma_modul.py:7"]),  # çapa-sentetik: bölüşüm fikstürü (TSK-236)
])
def test_SENTETIK_BOLUSUM_py_hedefi_KARDES_civide_kalir(sahte_kok, rel, satir, beklenen):
    h = capa_hukmu([(rel, satir + "\n")], kayit={}, kok=sahte_kok)
    assert [i["capa"] for i in h["ihlal"]] == beklenen, h["ihlal"]


@pytest.mark.parametrize("satir", [
    "Environment=REDIS=127.0.0.1:6379", "# her gece 23:32 UTC", "curl -s localhost:8080/healthz",
    "# bkz. api.anthropic.com:443", "# `hermes.py::sync_agent_skills` sembol çapası",
    "x = {\"a.json\": 1}", "image: redis:7-alpine",
])
def test_SENTETIK_YANLIS_POZITIF_uretmez(sahte_kok, satir):
    assert capa_hukmu([("ops/x.sh", satir + "\n")], kayit={}, kok=sahte_kok)["ihlal"] == []


# =================================================================================================
# C) KÖRLÜK ALARMI + GÖRÜNÜRLÜK — gerçek depo
# =================================================================================================

def test_KORLUK_ALARMI_taranan_dosya_ve_yuzeyler():
    """Bugün (2026-09-27) 940 taranan dosya. Taban 800: yanlış kök/uzantı listesi az dosya döner ve "temiz"
    ebediyen yeşil kalırdı. Her yüzeyden en az bir dosya taranmış olmalı (yüzey sessizce düşmesin)."""
    h = _depo_hukmu()
    assert h["taranan_dosya"] >= 800, h["taranan_dosya"]
    rel = h["rel_kumesi"]
    for zorunlu in ("meridian/web/app.js", "meridian/web/index.html", "ops/supervise.sh",
                    "deploy/oracle-a1/RUNBOOK.md", "deploy/oracle-a1/litestream.yml", "dagit.sh", "serve.sh",
                    "DESIGN.md", "tests/test_capa_pydisi_hedef_v571.py"):
        assert zorunlu in rel and _atlanan_sinif(zorunlu) is None, zorunlu


def test_OKUNAMAYAN_metin_dosyasi_YOK():
    assert _depo_hukmu()["okunamayan"] == []


def test_ATLANAN_yuzeyler_SAYILIR_ve_GEREKCELI():
    """Bedel yasası: atlanan her sınıf gerekçeli ve BUGÜN gerçekten bir şey atlıyor (ölü beyan yok).
    Ölçüldü 2026-09-27 (atlanan çapa, tüm hedefler): tarihçe 4030 · rol1 211 · ui_kaynagi 15 · ssot 6 ·
    skill 2 · üretilmiş 2 · birim 0 (v563 sonrası; dosya sayısı 67)."""
    h = _depo_hukmu()
    for sinif, gerekce in BEYANLI_ATLANAN.items():
        assert len(gerekce) >= 80, sinif
        assert h["atlanan_dosya"][sinif] >= 1, f"beyanlı sınıf `{sinif}` bugün hiçbir dosyayı atlamıyor"
    for sinif in ("tarihce", "rol1", "ssot", "ui_kaynagi", "uretilmis", "skill_kutuphanesi"):
        assert h["atlanan"][sinif] >= 1, (sinif, dict(h["atlanan"]))
    assert h["atlanan"]["tarihce"] >= 500


def test_HARICI_uzanti_depoda_YOK():
    """`.go` hedefinin harici sayılması ancak depoda `.go` dosyası YOKSA doğrudur."""
    for u in _HARICI_UZANTILAR:
        bulunan = [str(f) for k in (*TARANAN_KOKLER, "research") for f in (REPO / k).rglob(f"*.{u}")]
        assert not bulunan, bulunan


# =================================================================================================
# D) CANLI HÜKÜM — yasak yüzeyde 0 · izinli yüzeyde beyansız/çürük 0 · bayat kayıt 0
# =================================================================================================

def test_YASAK_yuzeyde_meridian_SATIR_capasi_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']}" for i in _depo_hukmu()["ihlal"]
             if i["tur"] == "yasak"]
    assert not ihlal, ("motor yüzeyinde satır çapası — `dosya.py::ad` sembol çapasına ya da hedefte aranabilir "
                       f"bir başlık/alıntıya çevir: {ihlal}")


def test_IZINLI_yuzeyde_BEYANSIZ_satir_capasi_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']}" for i in _depo_hukmu()["ihlal"]
             if i["tur"] == "beyansiz"]
    assert not ihlal, ("beyansız satır çapası — sembol/başlık çapasına çevir ya da `IZINLI_CAPALAR`a hedefte "
                       f"ZORUNLU metniyle beyan et: {ihlal}")


def test_IZINLI_yuzeyde_CURUK_capa_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']} ({i['neden']})" for i in _depo_hukmu()["ihlal"]
             if i["tur"] == "curuk"]
    assert not ihlal, f"beyanlı çapa artık hedefte beyan edilen metni göstermiyor (satır kaydı): {ihlal}"


def test_BAYAT_KAYIT_YOK_her_beyan_kaynakta_duruyor():
    """Kayıt kaynaktan silinmiş bir çapayı beyan etmeye devam edemez (sessiz ölü beyan)."""
    bayat = sorted(set(_kayit_sozlugu(IZINLI_CAPALAR)) - _depo_hukmu()["kullanilan"])
    assert not bayat, bayat


def test_IZINLI_kayit_ornekleri_GEREKCELI():
    for anahtar, (hedef, metin) in IZINLI_CAPALAR.items():
        assert metin and (hedef is not None or len(metin) >= 60), anahtar
        assert _atlanan_sinif(anahtar[0]) is None and _yuzey(anahtar[0]) == "izinli", anahtar


def test_SAYIM_bugunku_dagilim():
    """Kayıt DEFTERİ (2026-09-27, düzeltme sonrası): 9 kayıtla 10 doğrulanan (bir kayıt iki kez geçer),
    4 örnek/harici beyan, 28 harici `.go`. Sayı düşerse sorun değil (çapa sembole çevrildi); YÜKSELİRSE yeni
    bir satır çapası beyan edilmiş demektir — bu çivi onu görünür kılar ve kaydı yeniden düşündürür."""
    h = _depo_hukmu()
    assert h["dogrulanan"] <= 10 and h["ornek"] <= 4 and h["harici"] <= 28, (
        h["dogrulanan"], h["ornek"], h["harici"])


# =================================================================================================
# E) ÇEVRİLEN ÇAPALAR ÇÜRÜMEZ — sembol çapaları codelaw çekirdeğinden, başlık/alıntı çapaları metinden
# =================================================================================================
#: (kaynak, kaynakta DURMASI ZORUNLU sembol çapası). Çözümü (`codelaw.capa_uyusmasi`) v572 ölçer:
#: `tests/test_sembol_capa_pydisi_v572.py::test_POZITIF_KONTROL_bilinen_capa_KORPUSTA_cozulur`.
CEVRILEN_SEMBOL = [
    ("meridian/web/app.js", "loop.py::MIRROR_DRIFT_TOL"),
    ("meridian/web/app.js", "loop.py::mirror_submit_armed"),
    ("meridian/web/app.js", "loop.py::_armed_drop_row"),
    ("meridian/web/app.js", "obs.py::ALARM_ONAYLI_PLAN_GONDERILMEDI"),
    ("meridian/web/app.js", "api.py::api_diagnostics"),
    ("meridian/web/app.js", "watchdog.py::integrity_report_cached"),
    ("meridian/web/app.js", "loop.py::_persist_equity_point"),
    ("meridian/web/app.js", "sprint.py::status"),
    ("deploy/oracle-a1/RUNBOOK.md", "barsarchive.py::BarsArchiver.poll"),
    ("deploy/oracle-a1/RUNBOOK.md", "barsarchive.py::BarsArchiver.run"),
    ("deploy/oracle-a1/RUNBOOK.md", "hermes_composite.py::spawn_pending"),
    ("deploy/oracle-a1/RUNBOOK.md",
     "tests/test_denetim_defter_v159.py::test_c4_sema_migrasyon_transaction_ININ_ICINDE_kurulur"),
    ("deploy/oracle-a1/RUNBOOK.md", "api.py::healthz"),
    ("deploy/oracle-a1/litestream.yml",
     "tests/test_denetim_defter_v159.py::test_c4_sema_migrasyon_transaction_ININ_ICINDE_kurulur"),
    ("deploy/oracle-a1/litestream.yml", "storage.py::DB_NAME"),
    ("deploy/oracle-a1/litestream.yml", "storage.py::db_path"),
    ("workflow-diagram.html", "hermes.py::_bg_on_eleme_kaydi"),
]

#: (kaynak, kaynakta DURMASI ZORUNLU başlık/alıntı çapası, hedef yol | None, hedefte ZORUNLU metinler).
#: Hedef None = repo DIŞI (onaylı maket `scratch-panov2/`) — seçici adı çapadır, doğrulanamaz.
CEVRILEN_BASLIK = [
    ("meridian/analytics.py", "app.js'in `k.dd_bacagi` üçlü dalı", "meridian/web/app.js",
     ('k.dd_bacagi === true ? "pos" : k.dd_bacagi === false ? "neg" : "mut"',)),
    ("meridian/api.py", "app.js «İKİNCİ ONAY YOLU AÇILMADI» şerhinin", "meridian/web/app.js",
     ("İKİNCİ ONAY YOLU AÇILMADI",)),
    ("meridian/api.py", "goal.yaml `slippage_bps: 5` anahtarı", "state/goal.yaml", ("\nslippage_bps: 5\n",)),
    ("meridian/broker.py", "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md §B.3 «Kötümser çapraz kontrol»",
     "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md",
     ("### B.3 (iii) EMİR BOYUTU / LİKİDİTE", "**Kötümser çapraz kontrol:**", "2%×70.973 = 1.419")),
    ("meridian/codelaw.py", "`ARTEFAKT-TARAMASI-2026-08-07.md`deki", "docs/ARTEFAKT-TARAMASI-2026-08-07.md",
     ("`bararchive.py`'nin KENDİ dosya başlığı (satır 13-18)",)),
    ("meridian/config.py", "`state/goal.yaml` `limits` şerhi", "state/goal.yaml",
     ("BERABERİNDE GİDEN AYAR: `position_size_r` 1,0 → 0,5", "İkisi AYRILMAZ")),
    ("meridian/config.py", "`bounds.yaml` `position_size_r` satırı", "state/bounds.yaml",
     ("position_size_r:          {min: 0.1, max: 1.0, step: 0.1",)),
    ("meridian/config.py", "`goal.yaml` `limits` şerhindeki", "state/goal.yaml",
     ("BERABERİNDE GİDEN AYAR",)),
    ("meridian/hermes.py", "landing.js'in `d.hypotheses_total` okuması", "meridian/web/landing.js",
     ("d.hypotheses_total",)),
    ("meridian/hermes.py", "app.js'in `startsWith(\"rejected\")`", "meridian/web/app.js",
     ('startsWith("rejected")',)),
    ("meridian/skill_evolve.py", "app.js'in «SKILL.md.v2-draft» ipucu", "meridian/web/app.js",
     ("skills/&lt;ad&gt;/SKILL.md.v2-draft",)),
    ("meridian/web/app.js", "index.html `.acct .r b` kuralı", "meridian/web/index.html",
     (".acct .r b{", "white-space:nowrap;flex:none")),
    ("meridian/web/app.js", "bu dosyadaki «P6 TEKİLLEŞTİRMESİ» şerhi", "meridian/web/app.js",
     ("P6 TEKİLLEŞTİRMESİ (D2-b",)),
    ("meridian/web/app.js", "RAPOR.md §4, `production`/`coherence` satırları", "meridian/web/app.js",
     ('k === "monotonicity"',)),
    ("meridian/web/app.js", "`opParcalar` EOD sabır göstergesi", "meridian/web/app.js",
     ('etiket: "EOD sabır"', 'n >= mx ? "sev-1"')),
    ("meridian/web/app.js", "skills.py modül belgesinin", "meridian/skills.py",
     ("ajanın yaptığı hiçbir şey görünmez değildir",)),
    ("meridian/web/app.js", "`apiFetch`in GET-dışı dalı", "meridian/web/app.js",
     ('if (m !== "GET") _JC.clear();',)),
    ("meridian/web/index.html", "onaylı maket `scratch-panov2/index.html`: `.para/.sekme`", None, ()),
    ("meridian/web/index.html", "onaylanan maket `scratch-panov2/index.html`", None, ()),
    ("meridian/web/index.html", "app.js «MAKİNE-OKUNUR AD SATIRDA DURUR» şerhi", "meridian/web/app.js",
     ("MAKİNE-OKUNUR AD SATIRDA DURUR", "greplediği ad AYNI olmalı")),
    ("meridian/web/landing.html", "landing.js'in `c.mean_r` sınıf ataması", "meridian/web/landing.js",
     ('(c.mean_r > 0 ? " pos" : " neg")',)),
    ("meridian/web/landing.html", "index.html'in `.sev-*` rol sınıfına", "meridian/web/index.html",
     (".sev-1,.sev-2,.sev-3,.warn{",)),
    ("meridian/web/landing.html", "index.html'in `.pm-cell.pos/.neg` kuralıyla", "meridian/web/index.html",
     (".pm-cell.pos{background:var(--yon-arti-zemin)} .pm-cell.neg{background:var(--yon-eksi-zemin)}",)),
    ("meridian/web/landing.html", "index.html'in `.sev-3` kuralıyla", "meridian/web/index.html",
     (".sev-3{text-decoration-color:var(--sev-3)}",)),
    ("meridian/web/pano-onyuk.js", "theme.js `GUNDUZ`/`GECE` sabitleri", "meridian/web/theme.js",
     ('var GUNDUZ = "gunduz";', 'var GECE = "gece";')),
    ("tests/test_acil_dogruluk_v196.py", "app.js `EV_TR` süpürücü girdileri", "meridian/web/app.js",
     ("const EV_TR = {", "mirror_cancel_sinif_dokumu: e =>")),
    ("tests/test_acil_dogruluk_v196.py", "app.js `window.opCancelOpen`", "meridian/web/app.js",
     ("window.opCancelOpen = async", "Sınıf dökümü — giriş")),
    ("tests/test_skill_cleanup_v121.py", "Günlüğün 2026-08-02 «DESTEKLEYİCİ KOŞU» kaydı",
     "MERIDIAN_ENGINEERING_LOG.md",
     ("**DESTEKLEYİCİ KOŞU (2026-08-02 gece", "BOŞ ve git-izsiz dizin, yalnız Mac diskinde")),
    ("tests/test_spend_defter_duzeltmesi_v331.py", "`deploy/ansible/vars/dagit_vars.yml` `rsync_disla` listesi",
     "deploy/ansible/vars/dagit_vars.yml", ("rsync_disla:\n", '\n  - "state"\n')),
    ("tests/test_wp2d_pano_beyani_v246.py", "`state/goal.yaml` `limits` şerhi", "state/goal.yaml",
     ("BERABERİNDE GİDEN AYAR: `position_size_r`", "İkisi AYRILMAZ")),
    ("tests/test_wp2d_pano_beyani_v246.py", "`goal.yaml` «BERABERİNDE GİDEN AYAR» şerhi", "state/goal.yaml",
     ("BERABERİNDE GİDEN AYAR",)),
    ("tests/test_wp2d_pano_beyani_v246.py", "`goal.yaml` «BERABERİNDE GİDEN AYAR» invaryantı", "state/goal.yaml",
     ("BERABERİNDE GİDEN AYAR",)),
    ("tests/test_yerlesim_tasma_v205.py", "app.js «MAKİNE-OKUNUR AD SATIRDA DURUR» şerhi", "meridian/web/app.js",
     ("MAKİNE-OKUNUR AD SATIRDA DURUR",)),
    ("deploy/oracle-a1/deploy.sh", "serve.sh'ın `[ ! -s state/trades.jsonl ] && [ ! -s state/meridian.db ]`",
     "serve.sh", ("if [ ! -s state/trades.jsonl ] && [ ! -s state/meridian.db ]; then",)),
    ("DESIGN.md", "`index.html`'s `.md` rule", "meridian/web/index.html",
     (".md{line-height:1.8;", "max-width:72ch}")),
]


@pytest.mark.parametrize("kaynak,capa", CEVRILEN_SEMBOL)
def test_cevrilen_SEMBOL_capasi_KAYNAKTA_duruyor(kaynak, capa):
    """Sınır kontrollü: kaynakta `ad` yerine `adX` yazılırsa alt-dizge araması yine bulurdu ve tablo çözücüden
    geçtiği için çürüme SESSİZ kalırdı — sembolün ardında ad karakteri olmamalı."""
    govde = (REPO / kaynak).read_text(encoding="utf-8")
    assert re.search(re.escape(capa) + r"(?![A-Za-z0-9_])", govde), f"{kaynak} içinde `{capa}` yok"


@pytest.mark.parametrize("kaynak,capa,_hedef,_metinler", CEVRILEN_BASLIK)
def test_cevrilen_BASLIK_capasi_KAYNAKTA_duruyor(kaynak, capa, _hedef, _metinler):
    assert capa in (REPO / kaynak).read_text(encoding="utf-8"), f"{kaynak} içinde `{capa}` yok"


@pytest.mark.parametrize("kaynak,capa,hedef,metinler", [b for b in CEVRILEN_BASLIK if b[2]])
def test_cevrilen_BASLIK_capasi_HEDEFTE_gercekten_var(kaynak, capa, hedef, metinler):
    govde = (REPO / hedef).read_text(encoding="utf-8")
    eksik = [m for m in metinler if m not in govde]
    assert not eksik, f"{kaynak} çapası `{capa}` → {hedef} içinde bulunamadı: {eksik}"
