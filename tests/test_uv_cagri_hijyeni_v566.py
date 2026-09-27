"""v566 — TSK-230: birim DIŞI `uv run|sync` çağrıları A0 semantiğini taşır + kilit tazeliği kapısı.

BAĞLAM. TSK-228 (v558) birim/drop-in KOMUT yönergelerini `uv run --frozen --no-dev`e çekti; A0 rolü ve
dagit `[3]` `uv sync --frozen --no-dev` koşar. v558'in kapsam dışı bıraktığı yüzey: A1'de ELLE ya da
betikle koşulan / koşulması ÖĞÜTLENEN komutlar. Bayraksız `uv run` açılışta VARSAYILAN grupları (dev)
kurar, `--frozen`sız hâli kilidi YENİDEN YAZAR (v558 ölçümü) — bir sonraki dağıtımda "VENV DEĞİŞTİ" öter.

ÖLÇÜM (Rol-1 taramasına göre fark, 2026-09-27):
  · Üretilmiş `docs/RUNBOOK.md`de ÇAĞRI YOK — yalnız iki düzyazı adı (`ops/belge_esitle.sh` başlığı:
    "`uv sync` çağırmaz"). TSK-228 raporunun "RUNBOOK'taki A1 elle komutları" dediği metin ELLE yazılmış
    A1 kılavuzu `deploy/oracle-a1/RUNBOOK.md`dir (`uv run python -m meridian.barsarchive --ozet` vb.).
    Kapsama o yüzden AÇIKÇA eklendi; üreticinin kaynak başlıkları da (sözleşme) taranır.
  · Aynı öğüt birim ŞERHLERİNDE de yaşıyor (`meridian-barsarchive.service` "ölçüsü: uv run …"); v558
    yalnız yönergeleri okur → birim yorum satırları da taranır.
  · `ops/state_yetim_temizle.sh` varsayılanı A1'e SSH'tir (dagit `[5a]` onu öğütler) — A1 çağrısı.
  · `uv sync --extra dev`: `bakim_h9.sh` (A1, düzeltildi) + `ops/barsarchive-run.sh` (Mac başlatıcısı,
    beyanlı) + kök `serve.sh` / `README.md` (yerel geliştirici; kapsam dışı, raporda).

KURAL (A). Kapsamdaki her proje-EŞİTLEYEN uv çağrısının (v558 `ESITLEYEN_ALT_KOMUTLAR`) eşitleme-semantiği
(v558 `_semantik`) A0'ın `uv sync` görev metninden türeyen kümeye (v558 `_beklenen()` — TEK KAYNAK:
`venv.yml` + defaults `uv_sync_bayrak`) EŞİTTİR; değilse `UV_CAGRI_BEYANI`nda gerekçelidir.

KAPSAM (`_taranan_parcalar`): `deploy/**/*.sh` + `ops/*.sh` (kabuk sözcük çözümlemesi) · üreticinin
(`ops/runbook_uret.py::betik_basliklari`) kaynak başlıklarından bu kümeye girmeyenler (`dagit.sh`,
`ops/filo.py` …) · `deploy/oracle-a1/RUNBOOK.md` · depodaki birim/drop-in dosyalarının YORUM satırları
(küme v554 `_kapsam()`, ikinci kez tanımlanmaz).

ÇAĞRI ile AD ayrımı — iki bağlam, ölçülmüş örneklerle:
  · KOD (tırnaksız kabuk): her `uv run|sync` bir çağrıdır. `deploy.sh`in `|| uv sync` yedeği argümansızdı
    ve kilidi yeniden yazıyordu — argümansız diye atlanamaz.
  · İLETİ/DÜZYAZI (tırnak içi, yorum, heredoc gövdesi, markdown düzyazısı; ters tırnak dilimleri ayrı):
    yalnız ARGÜMANLI anış çağrıdır. `uv sync`in konumsal argümanı YOKTUR → en az bir seçenek ister
    (`echo "  ✓ uv sync"` bir ETİKETTİR, `echo "önce: uv sync --extra dev"` bir ÖĞÜTTÜR); `uv run` en az
    bir seçenek ya da komut ister ("`uv run` önbelleği" addır, "`uv run python -m x`" öğüttür).
  · `"$UV"` / `${UV}` (`UV="${UV:-uv}"` deseni) `uv` sayılır — v558'in beyanlı kör noktası bu kapsamda
    gerçek: `ci_duman.sh`, `kapilar.sh`, `haftalik_mutasyon.sh` uv'yi YALNIZ böyle çağırıyor.
  Kabuk sözcük çözümlemesi dengesi ÖLÇÜLÜR (A3): bir metin açık tırnak/heredoc ile biterse ayrıştırma
  güvenilmezdir ve bu SESSİZ geçmez.

KİLİT TAZELİĞİ (E). Ölçüm (bu tur, Mac, uv 0.11.28, yalıtılmış kopyalar; `uv lock --check --offline`):
  taze kilit → rc 0, ~0,01 sn, BOŞ `UV_CACHE_DIR` ile de (ağ/önbellek gerekmez), uv.lock değişmez;
  ayrışma (yeni ana/dev bağımlılığı · extra kısıtı · kilitli sürümün HÂLÂ sağladığı gevşetme · silme ·
  requires-python) → rc 1 ("needs to be updated" ya da önbellekte olmayan paket için "network was
  disabled" ipucu — ikisi de AYNI hüküm), uv.lock değişmez; kilit yok / yorumlayıcı yok → rc 2.
  YAN BULGU (kapının SIRASINI belirleyen): bayraksız `uv run` ve `uv audit` bayat kilidi SESSİZCE
  YENİDEN YAZAR — audit rc 2 ile düştüğü koşumda bile uv.lock değişti. Dolayısıyla:
    · CI: `ci.yml` eşitleme adımı `--frozen` taşır (bayraksızı kilidi kapıdan ÖNCE tazelerdi) ve
      `ops/ci_duman.sh` `[0/4]` her `uv run|audit`tan ÖNCE koşar; sürüm uyumu `[3/4] uv audit` deseni
      (bu uv `--check` bilmiyorsa ÖLÇÜLEMEDİ, KIRMIZI değil).
    · dagit: `[0b]`nin İLK görevi; `[0b] uv audit` + `[0c]/[0d]/[5c]` `uv run`dan önce. Fail-closed
      (dagit `[0b]/[0d]` sözleşmesi): rc 1 ve rc 2 İKİSİ DE dağıtımı durdurur — A0'ın uv'si ölçüldü
      (0.11.28 `--check` taşır); dagit'in kapısı yoksa `[0a]`nın temiz bulduğu ağaç `[0b]`de kirlenir ve
      commit'lenmemiş bir kilit `[2]` ile A1'e gider.

MODELLENMEYEN (bilinçli; hepsi adıyla):
  · `ops/*.py` ve `deploy/*/*.py` docstring'leri ve operatöre giden ileti metinleri (`uv run python
    ops/karne_hesap.py --json` sınıfı; 11 dosyada 31 satır, ad + öğüt karışık, 2026-09-27) — kapsam dışı;
    sınıfın sistemik çaresi (A1 kabuğunda `UV_NO_DEV=1` + `UV_FROZEN=1` — uv 0.11.28 ikisini de ortamdan
    okur) Rol-1 kararı (rapor).
  · `deploy/ansible/*.yml` görev metinleri: A0'ın kendi `uv sync`i v558'de; `[0c]/[0d]` A0 (yerel) komutu.
  · Kök `serve.sh` / `README.md` / `.github/` (yalnız E2 ölçer) — A1'e gitmeyen yerel yüzey.
  · `$(…)` içindeki `case` deseni `)`i, `$'…'` ayrıntıları — bugün kapsamda yok; olursa A3 öter.

Numara v566: ana checkout + worktree'lerde boş (ölçüldü 2026-09-27; v567 paralel ajanın). Bu dosya
`state/` okumaz/yazmaz; E1 `ops/ci_duman.sh`i SAHTE bir `UV` ile koşar (hiçbir gerçek araç çağrılmaz),
E4 gerçek `uv lock --check --offline`ı tmp kopyada + depoda koşar (yazmaz — sha ile ölçülür).
"""
from __future__ import annotations

import dataclasses
import functools
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_ansible_dagit_v452 import _dagit_yml, _komut_metni, _play_gorevleri, _when_degerlendir
from tests.test_birim_argv_sir_v554 import _goreli
from tests.test_birim_argv_sir_v554 import _kapsam as _birim_kapsami
from tests.test_birim_uv_run_v558 import (
    DEV_HARIC_BAYRAKLAR,
    ESITLEYEN_ALT_KOMUTLAR,
    _bayrak,
    _beklenen,
    _semantik,
    _uv_cagrilari,
)

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ORACLE = DEPLOY / "oracle-a1"
OPS = KOK / "ops"
ELLE_RUNBOOK = ORACLE / "RUNBOOK.md"
CI_DUMAN = OPS / "ci_duman.sh"
CI_YML = KOK / ".github" / "workflows" / "ci.yml"
ANSIBLE_README = DEPLOY / "ansible" / "README.md"
RUNBOOK_URETICI = OPS / "runbook_uret.py"

#: Kilit tazeliği komutu — CI dumanı ve dagit `[0b]` AYNI komutu koşar (E1/E3 ikisini de bu değerle ölçer).
KILIT_KOMUTU = "lock --check --offline"

#: (depo-göreli kaynak, çağrının parçasında geçen LİTERAL parmak izi) → gerekçe (≥20 karakter).
#: Parmak izi, çağrının bulunduğu parça metninde (tek mantıksal satır) geçmek zorunda; kullanılmayan
#: anahtar çürüktür (C1).
UV_CAGRI_BEYANI: dict[tuple[str, str], str] = {
    ("ops/ci_duman.sh", "run python -m compileall"):
        "CI/yerel duman kapısı — A1'e GİTMEZ (CI koşucusu ve geliştirici makinesi). Kilit bu çağrıdan "
        "ÖNCE [0/4]'te denetlenir; CI eşitlemesi `--frozen --extra dev` (ci.yml, E2).",
    ("ops/ci_duman.sh", "run lint-imports"):
        "CI/yerel duman kapısı — A1'e GİTMEZ; import-linter DEV grubundadır, `--no-dev` kapıyı "
        "'command not found' ile KOŞMADAN geçirirdi (dagit [0c] şerhindeki aynı gerekçe).",
    ("ops/ci_duman.sh", "run pytest"):
        "CI/yerel duman kapısı — A1'e GİTMEZ; duman kapsamı pytest + hypothesis ister (extra `dev` + "
        "dependency-group `dev`; CI ikisini de eşitler) — `--no-dev` kapsamı koşturmazdı.",
    ("ops/kapilar.sh", "run lint-imports"):
        "Yerel hızlı kapı (geliştirici makinesi, ci_duman.sh'ın yerel ikizi) — A1'e GİTMEZ; "
        "import-linter DEV grubundadır.",
    ("ops/kapilar.sh", "run pytest"):
        "Yerel hızlı kapı + onun yerel tekrar öğüdü (echo) — A1'e GİTMEZ; kapsam pytest + hypothesis "
        "ister (extra `dev` + dependency-group `dev`).",
    ("ops/haftalik_mutasyon.sh", "run python - <<"):
        "Mutasyon öz-testi (heredoc) `mutmut`u içe aktarır — dev grubu; betik ELLE, geliştirici venv'inde "
        "koşar (deploy/ altında birimi/timer'ı yok, 2026-09-27 ölçüldü). A1'e dev grubu kurulmaz.",
    ("ops/haftalik_mutasyon.sh", "run mutmut"):
        "Haftalık mutasyon koşumu ELLE, geliştirici venv'inde — A1'e GİTMEZ; `mutmut` dev grubundadır, "
        "`--no-dev` aracı ortamdan düşürürdü.",
    ("ops/barsarchive-run.sh", "uv sync --extra dev"):
        "Mac-dönemi yerel arşivci başlatıcısı (launchd'siz nohup; A1'de arşivciyi "
        "meridian-barsarchive.service koşar) — öğüt YEREL geliştirici venv'i içindir; A1 DEĞİL.",
    ("deploy/oracle-a1/meridian-sprint@.service", "uv run uvicorn"):
        "Betimleyici şerh: canlı pano sürecinin ADINI anlatır, koşulmaz. Dosya F9 artefaktıdır "
        "(elle kurulur) — yalnız şerh için değiştirmek F9 içerik kapısında AYRIK gürültüsü üretir.",
    ("deploy/oracle-a1/meridian-fail-notify.service.d/10-sertlestirme-faz1.conf", "uv run python"):
        "Betimleyici şerh: sertleştirmenin ÖLÇÜLEN yüzeyini (ubuntu olarak koşan süreç) anlatır, "
        "komut öğütlemez; birimin kendi ExecStart'ı v558 ile `--frozen --no-dev` taşır.",
}

#: v558 algılayıcısına eklenen seçenek-dışı sonek (argümanlılık ölçüsü; bkz. `_duzyazi_cagrilari`).
_SON = "--v566-son"
#: `"$UV"`, `"${UV}"`, `${UV}`, `$UV` → `uv` (ops betiklerinin `UV="${UV:-uv}"` deseni).
_UV_DEGISKEN = re.compile(r'"\$UV"|"\$\{UV\}"|\$\{UV\}|\$UV(?![A-Za-z0-9_])')
_HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_KABUK_DILLERI = frozenset({"bash", "sh", "shell", "zsh", "console"})


# ================================================================================================
# Çekirdek — gerçek depo ve sentetik metinler AYNI fonksiyonlardan geçer
# ================================================================================================

@dataclasses.dataclass(frozen=True)
class Parca:
    tur: str      # "kod" | "tirnak" | "yorum" | "duzyazi"
    satir: int    # 0 = üretici başlığı (satır bilgisi yok)
    metin: str


def _kabuk_parcalari(metin: str, ilk_satir: int = 1) -> tuple[list[Parca], bool]:
    """Kabuk metni → (parçalar, dengeli). Parça = tek mantıksal satırın tek bağlamlı dilimi.

    Bağlam: `kod` (tırnaksız) · `tirnak` (tek/çift tırnak içi, `"…$(…)…"` dahil; heredoc gövdesi) ·
    `yorum` (kelime başındaki `#`ten satır sonuna). `\\`+satır sonu devamı boşluk olur (satır sayılır).
    `dengeli` False = metin açık tırnak/alt kabuk/heredoc ile bitti → ayrıştırma güvenilmez."""
    parcalar: list[Parca] = []
    yigin: list[list] = [["kod", 0]]          # ["kod"|"alt", parantez derinliği] | ["sq"] | ["dq"]
    durum = {"yorum": False, "tur": None, "bas": ilk_satir, "heredoc_acik": False}
    tampon: list[str] = []
    satir = ilk_satir
    bekleyen: list[tuple[str, bool]] = []

    def simdiki_tur() -> str:
        if durum["yorum"]:
            return "yorum"
        return "tirnak" if any(c[0] in ("sq", "dq") for c in yigin) else "kod"

    def bosalt() -> None:
        if durum["tur"] is not None and "".join(tampon).strip():
            parcalar.append(Parca(durum["tur"], durum["bas"], "".join(tampon)))
        tampon.clear()
        durum["tur"] = None

    def ekle(s: str) -> None:
        t = simdiki_tur()
        if durum["tur"] is not None and durum["tur"] != t:
            bosalt()
        if durum["tur"] is None:
            durum["tur"], durum["bas"] = t, satir
        tampon.append(s)

    i, n = 0, len(metin)
    while i < n:
        c = metin[i]
        ust = yigin[-1][0]
        if c == "\n":
            durum["yorum"] = False
            bosalt()
            satir += 1
            i += 1
            if yigin[-1][0] in ("kod", "alt") and bekleyen:   # `$(… <<'PY'` dahil
                for ayrac, sekme in bekleyen:
                    kapandi = False
                    while i < n:
                        j = metin.find("\n", i)
                        j = n if j < 0 else j
                        govde = metin[i:j]
                        i = min(j + 1, n)
                        if (govde.lstrip("\t") if sekme else govde) == ayrac:
                            satir += 1
                            kapandi = True
                            break
                        if govde.strip():
                            parcalar.append(Parca("tirnak", satir, govde))
                        satir += 1
                    if not kapandi:
                        durum["heredoc_acik"] = True
                bekleyen = []
            continue
        if durum["yorum"]:
            ekle(c)
            i += 1
            continue
        if ust == "sq":
            if c == "'":
                yigin.pop()
            else:
                ekle(c)
            i += 1
            continue
        if c == "\\" and i + 1 < n:                 # kod, alt kabuk ve çift tırnakta kaçış
            if metin[i + 1] == "\n":
                ekle(" ")
                satir += 1
            else:
                ekle(metin[i:i + 2])
            i += 2
            continue
        if ust == "dq":
            if c == '"':
                yigin.pop()
                i += 1
            elif metin.startswith("$(", i) and not metin.startswith("$((", i):
                yigin.append(["alt", 0])
                ekle("$(")
                i += 2
            else:
                ekle(c)
                i += 1
            continue
        # kod ya da alt kabuk çerçevesi
        if c == "'":
            yigin.append(["sq"])
            i += 1
            continue
        if c == '"':
            yigin.append(["dq"])
            i += 1
            continue
        if c == "#" and len(yigin) == 1 and (i == 0 or metin[i - 1] in " \t\n;&|()"):
            bosalt()
            durum["yorum"] = True
            i += 1
            continue
        if metin.startswith("<<<", i):
            ekle("<<<")
            i += 3
            continue
        if metin.startswith("<<", i):
            m = _HEREDOC.match(metin, i)
            if m:
                bekleyen.append((m.group(3), m.group(1) == "-"))
                ekle(m.group(0))
                i = m.end()
                continue
        if c == "(":
            yigin[-1][1] += 1
        elif c == ")":
            if ust == "alt" and yigin[-1][1] == 0:
                yigin.pop()
            else:
                yigin[-1][1] = max(0, yigin[-1][1] - 1)
        ekle(c)
        i += 1
    bosalt()
    dengeli = len(yigin) == 1 and not bekleyen and not durum["heredoc_acik"]
    return parcalar, dengeli


def _duzyazi_cagrilari(metin: str) -> list[tuple[str, tuple[str, ...]]]:
    """İleti/düzyazı bağlamı: ters tırnak dilimleri ayrı; YALNIZ argümanlı anış çağrıdır.

    Argümanlılık v558 algılayıcısına bir seçenek-dışı sonek (`_SON`) eklenerek ölçülür (algılayıcının
    ikinci kopyası YAZILMAZ): sonek seçeneklere karışıyorsa çağrıdan sonra hiçbir şey yoktu."""
    cikti: list[tuple[str, tuple[str, ...]]] = []
    for dilim in metin.split("`"):
        dilim = dilim[:-1] if dilim.endswith("\\") else dilim     # kabuk çift tırnağında `\``
        duz = _uv_cagrilari(dilim)
        isaretli = _uv_cagrilari(f"{dilim} {_SON}")
        assert len(duz) == len(isaretli), f"sonek çağrı sayısını değiştirdi: {dilim!r}"
        for (alt, sec), (_, sec_s) in zip(duz, isaretli):
            if alt not in ESITLEYEN_ALT_KOMUTLAR:
                continue
            argumanli = bool(sec) if alt == "sync" else (bool(sec) or _SON not in sec_s)
            if argumanli:
                cikti.append((alt, sec))
    return cikti


def _parca_cagrilari(p: Parca) -> list[tuple[str, tuple[str, ...]]]:
    if p.tur == "kod":
        return [(a, s) for a, s in _uv_cagrilari(p.metin) if a in ESITLEYEN_ALT_KOMUTLAR]
    return _duzyazi_cagrilari(p.metin)


def _md_parcalari(metin: str) -> tuple[list[Parca], bool]:
    """Markdown: kabuk dilli çit bloğu → kabuk çözümlemesi; kalan her satır (öteki çitler dahil) düzyazı."""
    parcalar: list[Parca] = []
    dengeli = True
    satirlar = metin.splitlines()
    i = 0
    while i < len(satirlar):
        m = re.match(r"^\s*```\s*([\w+-]*)", satirlar[i])
        if not m:
            parcalar.append(Parca("duzyazi", i + 1, satirlar[i]))
            i += 1
            continue
        j = i + 1
        while j < len(satirlar) and not satirlar[j].lstrip().startswith("```"):
            j += 1
        govde = satirlar[i + 1:j]
        if m.group(1).lower() in _KABUK_DILLERI:
            p, d = _kabuk_parcalari(_UV_DEGISKEN.sub("uv", "\n".join(govde)), i + 2)
            parcalar += p
            dengeli = dengeli and d
        else:
            parcalar += [Parca("duzyazi", i + 2 + k, g) for k, g in enumerate(govde)]
        i = j + 1
    return parcalar, dengeli


def _birim_yorumlari(metin: str) -> list[Parca]:
    return [Parca("duzyazi", no, s.lstrip()[1:]) for no, s in enumerate(metin.splitlines(), 1)
            if s.lstrip().startswith(("#", ";"))]


def _sh_kapsami(kok: Path = KOK) -> list[Path]:
    return sorted(set((kok / "deploy").rglob("*.sh")) | set((kok / "ops").glob("*.sh")))


@functools.lru_cache(maxsize=1)
def _runbook_basliklari() -> tuple[tuple[str, str], ...]:
    """Üreticinin KENDİ başlık okuyucusu (tek kaynak — RUNBOOK'a giren metin tam olarak bu)."""
    mod = betikten_modul_yukle(RUNBOOK_URETICI, "runbook_uret_v566")
    return tuple((b["yol"], b["baslik"]) for b in mod.betik_basliklari())


def _taranan_parcalar() -> tuple[list[tuple[str, Parca]], list[str]]:
    """Gerçek depo kapsamı → ([(kaynak, parça)], dengesiz kabuk metinleri)."""
    sonuc: list[tuple[str, Parca]] = []
    dengesiz: list[str] = []
    sh = _sh_kapsami()
    for p in sh:
        parcalar, dengeli = _kabuk_parcalari(_UV_DEGISKEN.sub("uv", p.read_text(encoding="utf-8")))
        kaynak = _goreli(p, KOK)
        if not dengeli:
            dengesiz.append(kaynak)
        sonuc += [(kaynak, x) for x in parcalar]
    sh_goreli = {_goreli(p, KOK) for p in sh}
    for yol, baslik in _runbook_basliklari():
        if yol not in sh_goreli:
            sonuc += [(yol, Parca("duzyazi", 0, s)) for s in baslik.splitlines()]
    parcalar, dengeli = _md_parcalari(ELLE_RUNBOOK.read_text(encoding="utf-8"))
    if not dengeli:
        dengesiz.append(_goreli(ELLE_RUNBOOK, KOK))
    sonuc += [(_goreli(ELLE_RUNBOOK, KOK), x) for x in parcalar]
    for p in _birim_kapsami():
        sonuc += [(_goreli(p, KOK), x) for x in _birim_yorumlari(p.read_text(encoding="utf-8"))]
    return sonuc, dengesiz


@dataclasses.dataclass(frozen=True, order=True)
class Cagri:
    kaynak: str
    satir: int
    tur: str
    alt: str
    secenekler: tuple[str, ...]
    parca: str

    def __str__(self) -> str:
        yer = f"{self.kaynak}:{self.satir}" if self.satir else f"{self.kaynak} (başlık)"
        return f"{yer} [{self.tur}] uv {self.alt} {' '.join(self.secenekler) or '(seçeneksiz)'} ← {self.parca[:90]!r}"


def _cagrilar(ciftler: list[tuple[str, Parca]]) -> list[Cagri]:
    return sorted(Cagri(k, p.satir, p.tur, alt, sec, p.metin.strip())
                  for k, p in ciftler for alt, sec in _parca_cagrilari(p))


def _tara(cagrilar: list[Cagri], *, beklenen: frozenset[str], beyan: dict | None = None
          ) -> tuple[list[Cagri], set[tuple[str, str]]]:
    """A kuralı. Dönüş: (ihlaller, kullanılan beyan anahtarları)."""
    beyan = UV_CAGRI_BEYANI if beyan is None else beyan
    ihlaller: list[Cagri] = []
    kullanilan: set[tuple[str, str]] = set()
    for c in cagrilar:
        if _semantik(c.secenekler) == beklenen:
            continue
        eslesen = [k for k in beyan if k[0] == c.kaynak and k[1] in c.parca]
        if eslesen:
            kullanilan.update(eslesen)
            continue
        ihlaller.append(c)
    return ihlaller, kullanilan


@functools.lru_cache(maxsize=1)
def _depo_cagrilari() -> tuple[Cagri, ...]:
    ciftler, _ = _taranan_parcalar()
    return tuple(_cagrilar(ciftler))


def _bicimle(cagrilar) -> str:
    return "\n".join(f"  · {c}" for c in cagrilar)


# ================================================================================================
# A — kural (gerçek depo)
# ================================================================================================

def test_A1_A1_yuzeyinde_uv_esitlemesi_A0_semantigini_tasir():
    beklenen = _beklenen()
    ihlaller, _ = _tara(list(_depo_cagrilari()), beklenen=beklenen)
    assert not ihlaller, (
        f"birim DIŞI proje-eşitleyen uv çağrısı A0 semantiğinden ({sorted(beklenen)}) AYRIK — bayraksız "
        "`uv run|sync` A1 venv'ine dev grubunu geri kurar (sonraki dağıtımda 'VENV DEĞİŞTİ'), `--frozen`sız "
        f"hâli uv.lock'u yeniden yazar:\n{_bicimle(ihlaller)}\n"
        f"ÇARE: `uv run {' '.join(sorted(beklenen))} <komut>` / `uv sync {' '.join(sorted(beklenen))}` "
        "(bayraklar alt komuttan SONRA). A1'e gitmeyen yerel/CI komutuysa UV_CAGRI_BEYANI'na gerekçesiyle.")


def test_A2_tarama_KOR_DEGIL_bilinen_A1_cagrilari_gorulur():
    """Canlı taban: düzeltilen A1 yüzeyleri taramada GÖRÜNÜR ve A0 semantiğini taşır (A1'in "ihlal yok"u
    boşta hak edilmesin). Sayılar tabandır (≥), tavan değil."""
    beklenen = _beklenen()
    taban = {
        "deploy/oracle-a1/bakim_h9.sh": 8,          # 7 run + 1 sync (A1'e ssh)
        "deploy/oracle-a1/deploy.sh": 5,            # sync + import doğrulaması + öğüt + tohum + durum
        "ops/state_yetim_temizle.sh": 1,            # dedektör (varsayılan A1'e ssh)
        "deploy/oracle-a1/RUNBOOK.md": 8,           # elle A1 kılavuzu
        "deploy/oracle-a1/meridian-barsarchive.service": 2,   # "ölçüsü" şerhleri
    }
    for kaynak, en_az in taban.items():
        uyumlu = [c for c in _depo_cagrilari() if c.kaynak == kaynak and _semantik(c.secenekler) == beklenen]
        assert len(uyumlu) >= en_az, (
            f"{kaynak}: A0 semantiğini taşıyan {len(uyumlu)} çağrı görüldü, taban {en_az} — tarama kör ya da "
            f"düzeltme geri alındı. Görülenler:\n{_bicimle(c for c in _depo_cagrilari() if c.kaynak == kaynak)}")


def test_A3_kabuk_cozumlemesi_DENGELI_sessiz_bozulma_yok():
    """Bir kabuk metni açık tırnak/heredoc/alt kabukla biterse sözcük çözümlemesi o noktadan sonra
    YANLIŞ bağlam üretir (çağrı düzyazı sanılır ya da tersi) — bu sessiz geçmez."""
    _, dengesiz = _taranan_parcalar()
    assert not dengesiz, (
        f"kabuk çözümlemesi dengesiz biten metinler: {dengesiz} — `_kabuk_parcalari` bu yapıyı "
        "modellemiyor; model genişletilmeden tarama o dosyalarda güvenilmez")


def test_A4_uretici_baslik_kanali_CANLI():
    """Üretici başlıklarının `deploy/`·`ops/` kabuk kümesine girmeyen kısmı (kök `dagit.sh`, `ops/*.py`
    CLI'ları, `altyapi/altyapi.sh`) GERÇEKTEN taranıyor — kanal boş kalırsa kapsamın o ayağı ölü."""
    sh = {_goreli(p, KOK) for p in _sh_kapsami()}
    dogrudan = [yol for yol, _ in _runbook_basliklari() if yol not in sh]
    assert "dagit.sh" in dogrudan and len(dogrudan) >= 3, dogrudan
    ciftler, _ = _taranan_parcalar()
    taranan = {k for k, p in ciftler if p.satir == 0}
    bos_baslikli = {yol for yol, baslik in _runbook_basliklari() if not baslik.strip()}
    assert taranan == set(dogrudan) - bos_baslikli, (sorted(taranan), sorted(dogrudan), sorted(bos_baslikli))


# ================================================================================================
# B — tek kaynak ve ayrışma
# ================================================================================================

def test_B1_AYRISMA_A0_bayragi_degisirse_her_uyumlu_cagri_OTER():
    """Beklenen küme A0'dan TÜRER, çivide literal yaşamaz: defaults başka bir dev-hariç bayrağa geçerse
    (ör. `--no-default-groups`a yükseltme) bugün uyumlu HER çağrı öter (aynı değişiklikte güncellenmedikçe)."""
    beklenen = _beklenen()
    baska = sorted(DEV_HARIC_BAYRAKLAR - {_bayrak()})[0]
    yeni = (beklenen - {_bayrak()}) | {baska}
    uyumlu = [c for c in _depo_cagrilari() if _semantik(c.secenekler) == beklenen]
    ihlaller, _ = _tara(list(_depo_cagrilari()), beklenen=yeni)
    assert uyumlu and set(uyumlu) <= set(ihlaller), (
        f"A0 {baska!r} olsaydı {len(uyumlu)} uyumlu çağrının yalnız {len(set(uyumlu) & set(ihlaller))}'i "
        "ötecekti — kapsamda A0'dan bağımsız bir kabul yolu var")


# ================================================================================================
# C — beyan hijyeni
# ================================================================================================

def test_C1_UV_CAGRI_BEYANI_gerekceli_ve_curumez():
    for anahtar, gerekce in UV_CAGRI_BEYANI.items():
        assert isinstance(anahtar, tuple) and len(anahtar) == 2 and all(anahtar), anahtar
        assert (KOK / anahtar[0]).is_file(), f"{anahtar}: kaynak dosya yok"
        assert len(gerekce.strip()) >= 20, f"{anahtar}: gerekçe kısa"
    _, kullanilan = _tara(list(_depo_cagrilari()), beklenen=_beklenen())
    curuk = sorted(set(UV_CAGRI_BEYANI) - kullanilan)
    assert not curuk, f"çürük beyan (ayrık çağrı artık yok ya da parmak izi eşleşmiyor — SİL): {curuk}"


def test_C2_beyan_yalniz_ADI_gecen_kaynagi_ve_parmak_izini_susturur():
    cagrilar = [Cagri("a.sh", 1, "kod", "run", (), "uv run lint-imports"),
                Cagri("a.sh", 2, "kod", "run", (), "uv run python -m x"),
                Cagri("b.sh", 1, "kod", "run", (), "uv run lint-imports")]
    beyan = {("a.sh", "run lint-imports"): "sentetik: yerel geliştirici komutu gerekçesi"}
    ihlaller, kullanilan = _tara(cagrilar, beklenen=frozenset({"--frozen", "--no-dev"}), beyan=beyan)
    assert [(c.kaynak, c.satir) for c in ihlaller] == [("a.sh", 2), ("b.sh", 1)]
    assert kullanilan == {("a.sh", "run lint-imports")}


# ================================================================================================
# D — pozitif kontrol: sözcük çözümlemesi ve çağrı/ad ayrımı
# ================================================================================================

# (kimlik, kabuk metni, beklenen [(satır, alt komut, seçenekler)])
KABUK_DURUMLARI = [
    ("ciplak_kod", "uv run python -m x\n", [(1, "run", ())]),
    ("argumansiz_kod_sync_CAGRIDIR", "uv sync --frozen 2>/dev/null || uv sync\n",
     [(1, "sync", ("--frozen",)), (1, "sync", ())]),
    ("bayrakli_kod", "uv run --frozen --no-dev python -c 'import x'\n", [(1, "run", ("--frozen", "--no-dev"))]),
    ("ssh_tek_tirnak_icinde_cagri",
     "ssh h 'export PATH=x; cd /opt/meridian && uv run python -m m --durum 2>&1 | tail -3' || die \"x\"\n",
     [(1, "run", ())]),
    ("echo_ETIKETI_cagri_DEGIL", "ssh h 'uv sync --frozen --extra dev -q && echo \"  ✓ uv sync\"' || die \"uv sync\"\n",
     [(1, "sync", ("--frozen", "--extra"))]),
    ("echo_OGUDU_cagridir", 'echo "önce: uv sync --extra dev"\n', [(1, "sync", ("--extra",))]),
    ("echo_parantezli_ad_cagri_DEGIL", 'echo "-- uv sync (bağımlılıklar)"\n', []),
    ("uv_degiskeni_uv_sayilir", '"$UV" run lint-imports\n${UV} sync\n', [(1, "run", ()), (2, "sync", ())]),
    ("yorum_adi_cagri_DEGIL", "# `uv run` boş bir dizinde ortam kurmaya kalkar\n", []),
    ("yorum_OGUDU_cagridir", "# ölçü: `uv run python -m meridian.barsarchive --ozet`\n", [(1, "run", ())]),
    ("satir_ici_yorum", "true  # uv run python -m x\n", [(1, "run", ())]),
    ("hash_kelime_ortasi_yorum_DEGIL", "echo ${#dizi[@]}; uv run x\n", [(1, "run", ())]),
    ("ters_bolu_devami_birlestirir", "uv run \\\n  --frozen --no-dev x\n", [(1, "run", ("--frozen", "--no-dev"))]),
    ("cok_satirli_tek_tirnak_dogru_satir",
     "ssh h 'cd /opt/meridian\ncurl -s x\nuv run python -m m --durum'\n", [(3, "run", ())]),
    ("heredoc_govdesi_duzyazi_ve_sonrasi_kod",
     "cat <<'PY'\nprint(\"it's\")\nuv sync\nPY\nuv run x\n", [(5, "run", ())]),
    ("uc_kucuktur_heredoc_DEGIL", 'read -r a <<< "$b"\nuv run x\n', [(2, "run", ())]),
    ("cift_tirnak_alt_kabuk_ic_tirnagi",
     'x="$(awk \'$1=="cp" {print $3}\')"\nuv run y\n', [(2, "run", ())]),
    ("tirnak_icinde_kacisli_ters_tirnak_ogut", 'echo "(gezinti: \\`uv run mutmut browse\\`)"\n', [(1, "run", ())]),
    ("kacisli_ters_tirnak_bayragi_KIRPILMAZ", 'echo "A1: \\`uv run --frozen --no-dev x\\`"\n',
     [(1, "run", ("--frozen", "--no-dev"))]),
]


@pytest.mark.parametrize("kimlik, metin, beklenen", KABUK_DURUMLARI, ids=[d[0] for d in KABUK_DURUMLARI])
def test_D1_pozitif_kontrol_KABUK_cozumlemesi(kimlik, metin, beklenen):
    parcalar, dengeli = _kabuk_parcalari(_UV_DEGISKEN.sub("uv", metin))
    assert dengeli, f"{kimlik}: dengesiz"
    bulunan = [(p.satir, alt, sec) for p in parcalar for alt, sec in _parca_cagrilari(p)]
    assert bulunan == beklenen, f"{kimlik}: {bulunan}\n{parcalar}"


@pytest.mark.parametrize("metin", ["echo 'açık", 'echo "açık', "cat <<EOF\ngövde\n", 'x="$(a\n'])
def test_D2_dengesiz_metin_DENGESIZ_raporlanir(metin):
    _, dengeli = _kabuk_parcalari(metin)
    assert not dengeli, metin


# (kimlik, düzyazı, beklenen [(alt, seçenekler)])
DUZYAZI_DURUMLARI = [
    ("ters_tirnakli_ad", "aarch64 wheel'i var (`uv sync` derleme yapmaz)", []),
    ("ekli_ad", "ana süreç `uv run`dır ve çocuğu", []),
    ("tirnaksiz_betimleme", "uzakta deploy.sh (uv sync + redis + systemd birimleri)", []),
    ("tirnaksiz_ogut", "ölçüsü:  uv run python -m meridian.barsarchive --ozet", [("run", ())]),
    ("ters_tirnakli_ogut", "`uv run python -m meridian.barsarchive --ozet --gun 5`", [("run", ())]),
    ("bayrakli_betimleme_uyumlu", "`uv run --frozen --no-dev` (TSK-228)", [("run", ("--frozen", "--no-dev"))]),
    ("sync_secenekli_ogut", "kur: `uv sync --extra dev`", [("sync", ("--extra",))]),
    ("iki_dilim", "`uv run` ve `uv sync --frozen`", [("sync", ("--frozen",))]),
    ("uv_lock_esitlemez", "`uv lock --check --offline`", []),
]


@pytest.mark.parametrize("kimlik, metin, beklenen", DUZYAZI_DURUMLARI, ids=[d[0] for d in DUZYAZI_DURUMLARI])
def test_D3_pozitif_kontrol_DUZYAZI_cagri_ad_ayrimi(kimlik, metin, beklenen):
    assert _duzyazi_cagrilari(metin) == beklenen, kimlik


def test_D4_markdown_cit_kabuk_digeri_duzyazi():
    md = ("Giriş `uv sync` derleme yapmaz.\n"
          "```bash\nssh h 'uv run python -m x'\nuv sync\n```\n"
          "```\nuv sync\n```\n"
          "| e | `uv run python -m y` | x |\n")
    parcalar, dengeli = _md_parcalari(md)
    assert dengeli
    bulunan = sorted((p.satir, p.tur, alt) for p in parcalar for alt, _ in _parca_cagrilari(p))
    assert bulunan == [(3, "tirnak", "run"), (4, "kod", "sync"), (9, "duzyazi", "run")], bulunan


# ================================================================================================
# E — kilit tazeliği kapısı
# ================================================================================================

_SAHTE_UV = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >> "$SAHTE_UV_KAYIT"
if [ "$1" = "--version" ]; then echo "uv 0.0.0-sahte"; exit 0; fi
case "$1 $2" in
  "lock --help")
    printf '%s\n' "Update the project's lockfile" "" "Options:"
    if [ "${SAHTE_CHECK_VAR:-1}" = 1 ]; then
      printf '%s\n' "      --check            Check if the lockfile is up-to-date"
    fi
    printf '%s\n' "      --check-exists     Assert that a uv.lock exists" "      --dry-run          Perform a dry run"
    exit 0 ;;
  "lock --check") exit "${SAHTE_KILIT_RC:-0}" ;;
  "audit --help") exit 2 ;;
esac
exit 0
"""


def _ci_duman_kos(tmp_path: Path, **ortam: str) -> tuple[subprocess.CompletedProcess, list[str]]:
    sahte = tmp_path / "uv"
    sahte.write_text(_SAHTE_UV, encoding="utf-8")
    sahte.chmod(0o755)
    kayit = tmp_path / "kayit.txt"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("UV_", "SAHTE_"))}
    env.update({"UV": str(sahte), "SAHTE_UV_KAYIT": str(kayit), **ortam})
    r = subprocess.run(["bash", str(CI_DUMAN)], env=env, capture_output=True, text=True, timeout=120)
    return r, (kayit.read_text(encoding="utf-8").splitlines() if kayit.exists() else [])


# (kimlik, ortam, beklenen çıkış, çıktıda olması gereken, `lock --check` çağrıldı mı)
CI_DUMAN_DURUMLARI = [
    ("taze", {"SAHTE_KILIT_RC": "0"}, 0, "uv.lock pyproject.toml ile TAZE", True),
    ("ayrisik_KIRMIZI", {"SAHTE_KILIT_RC": "1"}, 1, "KİLİT BAYAT", True),
    ("uv_hatasi_KIRMIZI", {"SAHTE_KILIT_RC": "2"}, 1, "KİLİT BAYAT", True),
    ("check_yok_OLCULEMEDI_kirmizi_degil", {"SAHTE_CHECK_VAR": "0"}, 0,
     "lock --check' bayrağını tanımıyor", False),
]


@pytest.mark.parametrize("kimlik, ortam, cikis, metin, check_cagrildi", CI_DUMAN_DURUMLARI,
                         ids=[d[0] for d in CI_DUMAN_DURUMLARI])
def test_E1_ci_duman_kilit_kapisi_DAVRANISI_ve_SIRASI(tmp_path, kimlik, ortam, cikis, metin, check_cagrildi):
    r, kayit = _ci_duman_kos(tmp_path, **ortam)
    assert r.returncode == cikis, f"{kimlik}: çıkış {r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-800:]}"
    assert metin in r.stdout, f"{kimlik}: {metin!r} basılmadı\n{r.stdout[-1500:]}"
    kilit = f"{KILIT_KOMUTU}"
    assert (kilit in kayit) is check_cagrildi, f"{kimlik}: `uv {kilit}` çağrısı {check_cagrildi} beklenirdi: {kayit}"
    # İLK KIRMIZI DURDURMAZ: kilit kırmızıyken de sonraki kapılar koşar.
    assert any(k.startswith("run pytest") for k in kayit), f"{kimlik}: duman pytest'i koşmadı: {kayit}"
    # SIRA: kilit kontrolünden ÖNCE hiçbir eşitleyen/denetleyen uv çağrısı yok (bayat kilidi yeniden yazarlar).
    once = kayit[:kayit.index(kilit)] if kilit in kayit else kayit[:1]
    yasak = [k for k in once if not (k in ("lock --help", "--version") or k.endswith("--help"))]
    if check_cagrildi:
        assert not yasak, f"{kimlik}: `uv {kilit}`dan ÖNCE koşan uv çağrıları (kilidi yeniden yazabilir): {yasak}"


def test_E2_ci_esitleme_adimi_kilidi_YENIDEN_YAZMAZ():
    """CI iş akışının `uv sync` adımı `--frozen` ya da `--locked` taşır: bayraksız sync bayat kilidi
    duman kapısından ÖNCE tazeler ve `[0/4]` her koşumda "taze" derdi (kapı CI'da KÖR)."""
    veri = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    kosumlar = [adim.get("run", "") for is_ in veri["jobs"].values() for adim in is_.get("steps", [])]
    sync = [sec for k in kosumlar for alt, sec in _uv_cagrilari(k) if alt == "sync"]
    assert sync, "ci.yml'de `uv sync` adımı bulunamadı — çivi bayat"
    for sec in sync:
        assert {"--frozen", "--locked"} & set(sec), (
            f"ci.yml `uv sync {' '.join(sec)}` kilidi yeniden yazabilir — kilit kapısı CI'da kör kalır")
    assert any("ops/ci_duman.sh" in k for k in kosumlar), "ci.yml duman kapısını koşmuyor"


def _play1_gorevleri() -> list[dict]:
    return _play_gorevleri(_dagit_yml()[0])


def test_E3_dagit_0b_kilit_kapisi_ILK_uv_gorevi_ve_FAIL_CLOSED():
    gorevler = _play1_gorevleri()
    komutlar = [(i, str(g.get("name", "")), _komut_metni(g).strip()) for i, g in enumerate(gorevler)]
    kilit = [(i, ad) for i, ad, k in komutlar if k == f"uv {KILIT_KOMUTU}"]
    assert len(kilit) == 1, f"Play 1'de tek `uv {KILIT_KOMUTU}` görevi beklenirdi: {kilit}"
    ki, kad = kilit[0]
    assert kad.startswith("[0b]"), f"kilit görevi [0b] kapısının parçası değil: {kad!r}"
    olcum = gorevler[ki]
    assert olcum.get("check_mode") is False and olcum.get("changed_when") is False, (
        "kilit ölçümü kuru koşumda da ölçmeli ve 'changed' dememeli (v452 B2 sözleşmesi)")
    diger_uv = [(i, ad) for i, ad, k in komutlar if re.match(r"uv\s", k) and i != ki]
    assert diger_uv and all(i > ki for i, _ in diger_uv), (
        f"kilit kapısı her `uv` görevinden ÖNCE koşmalı (audit ve bayraksız `uv run` bayat kilidi "
        f"yeniden yazar): kilit #{ki}, öncekiler {[x for x in diger_uv if x[0] < ki]}")
    kayit = olcum.get("register")
    assert kayit, "kilit ölçümü register etmiyor"
    # failed_when: bilinen üç kod hükme taşınır (reçeteyle), bilinmeyen kod görevi düşürür.
    for rc, dusmeli in ((0, False), (1, False), (2, False), (3, True), (-9, True)):
        assert _when_degerlendir(olcum["failed_when"], {kayit: {"rc": rc}}) is dusmeli, (rc, olcum["failed_when"])
    # Hüküm: yalnız rc 0 geçer — 1 (ayrışık) ve 2 (uv koşamadı) DAĞITIMI DURDURUR.
    assertler = [g for g in gorevler[ki + 1:ki + 3]
                 if "ansible.builtin.assert" in g and kayit in str(g["ansible.builtin.assert"].get("that"))]
    assert len(assertler) == 1, "kilit ölçümünün hemen ardında tek bir KAPI (assert) görevi yok"
    that = assertler[0]["ansible.builtin.assert"]["that"]
    for rc, gecmeli in ((0, True), (1, False), (2, False)):
        assert _when_degerlendir(that, {kayit: {"rc": rc}}) is gecmeli, (rc, that)
    assert "uv lock" in str(assertler[0]["ansible.builtin.assert"].get("fail_msg")), "fail_msg çareyi söylemiyor"


def test_E3b_dagit_README_0b_satiri_kilit_kontrolunu_anar():
    satir = [s for s in ANSIBLE_README.read_text(encoding="utf-8").splitlines() if s.startswith("| `[0b]`")]
    assert len(satir) == 1 and "uv lock --check" in satir[0], satir


def _uv_ikili() -> str:
    yol = shutil.which("uv") or next((str(p) for p in (Path.home() / ".local" / "bin" / "uv",) if p.is_file()), None)
    if yol is None:
        pytest.fail("uv bulunamadı (PATH ya da ~/.local/bin) — 'koşamıyorum' bu çivide 'kırmızı' sayılır")
    return yol


def _kilit_denetle(dizin: Path, onbellek: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("UV_")}
    env.update({"UV_CACHE_DIR": str(onbellek), "UV_PYTHON_DOWNLOADS": "never", "UV_NO_PROGRESS": "1"})
    return subprocess.run([_uv_ikili(), *KILIT_KOMUTU.split()], cwd=dizin, env=env,
                          capture_output=True, text=True, timeout=120)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# (kimlik, pyproject dönüşümü (eski, yeni) ya da None, taze mi)
KILIT_DURUMLARI = [
    ("taze_kopya", None, True),
    ("kilitli_surumun_hala_sagladigi_GEVSETME", ('"pandas>=2.1"', '"pandas>=2.0"'), False),
    ("yeni_ana_bagimlilik", ('    "lxml>=6.1.1",\n', '    "lxml>=6.1.1",\n    "iniconfig>=1",\n'), False),
    ("dev_grubu_degisikligi", ('    "mutmut>=3.7.0",\n', '    "mutmut>=3.7.1",\n'), False),
]


@pytest.mark.parametrize("kimlik, donusum, taze", KILIT_DURUMLARI, ids=[d[0] for d in KILIT_DURUMLARI])
def test_E4_uv_lock_check_offline_AYRISMAYI_yakalar_AGSIZ_ve_YAZMAZ(tmp_path, kimlik, donusum, taze):
    """Seçilen komutun pozitif kontrolü GERÇEK uv ile: boş önbellek + `--offline` (ağ yok) altında taze
    kilit geçer, her ayrışma düşer, uv.lock HİÇBİR durumda yazılmaz."""
    kopya = tmp_path / "proje"
    kopya.mkdir()
    for ad in ("pyproject.toml", "uv.lock"):
        shutil.copy2(KOK / ad, kopya / ad)
    if donusum:
        metin = (kopya / "pyproject.toml").read_text(encoding="utf-8")
        assert metin.count(donusum[0]) == 1, f"{kimlik}: ön koşul — dönüşüm hedefi pyproject'te tek değil"
        (kopya / "pyproject.toml").write_text(metin.replace(donusum[0], donusum[1]), encoding="utf-8")
    once = _sha(kopya / "uv.lock")
    r = _kilit_denetle(kopya, tmp_path / "onbellek")
    assert (r.returncode == 0) is taze, f"{kimlik}: rc {r.returncode}\n{r.stderr[-800:]}"
    if not taze:
        assert r.returncode == 1, f"{kimlik}: ayrışma rc 1 beklenirdi (2 = uv koşamadı): {r.stderr[-800:]}"
    assert _sha(kopya / "uv.lock") == once, f"{kimlik}: `uv {KILIT_KOMUTU}` uv.lock'u YAZDI"


def test_E5_depo_kilidi_bugun_TAZE_kapilar_kirmizi_dogmaz(tmp_path):
    """Canlı taban: CI `[0/4]` ve dagit `[0b]` bugünkü depoda geçer (kapı kırmızı doğmaz); ölçüm depoyu yazmaz."""
    once = _sha(KOK / "uv.lock")
    r = _kilit_denetle(KOK, tmp_path / "onbellek")
    assert r.returncode == 0, f"depo kilidi pyproject ile AYRIŞIK — `uv lock` koş ve commit'le:\n{r.stderr[-800:]}"
    assert _sha(KOK / "uv.lock") == once
