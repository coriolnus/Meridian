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
    · dagit: `[0b]`nin İLK görevi; `[0b] uv audit` + `[0c]/[0d]/[5c]` `uv run`dan önce (yoksa `[0a]`nın
      temiz bulduğu ağaç `[0b]`de kirlenir, commit'lenmemiş kilit `[2]` ile A1'e gider). TUR 2 (Rol-1 hükmü
      2026-09-27): YALNIZ rc 1 (ayrışma) DURDURUR; rc 2 (uv yok — Ansible'da da rc 2, ölçüldü — / kilit
      yok / yorumlayıcı yok / `--check` yok) ÖLÇÜLEMEDİ'dir: nedeniyle log'a basılır, dağıtım SÜRER. Kapının
      amacı ayrışma, operatör Mac'inin pinsiz uv'si değil; bedel = TSK-230 öncesi durum. Sözleşme dışı kod
      (3, sinyal) görevi düşürür.
    · CI uv'si A1 pinine (`defaults/main.yml::uv_surum`) sabitlendi (belgeli sürüm-pinli installer URL'si);
      literal kopya E6 ile çivili. 0.12.0'da `uv lock --check` ve `uv audit` (preview `AuditCommand`)
      KAYNAKTAN okundu (tag 0.12.0, `uv-cli::LockArgs.check`, `uv-preview`), KOŞULMADI — `[0/4]`/`[3/4]`
      yoklama deseni (alt komut/bayrak yoksa ÖLÇÜLEMEDİ) yerinde kalır.

TSK-238 (2026-09-27) — ÜÇ GENİŞLEME:
  (1) PYTHON İLETİ/DOCSTRING YÜZEYİ. `ops/*.py` + `deploy/*/*.py` (TSK-230 ölçümü: 11 dosyada 31 satır,
      operatöre giden bot iletileri dahil — `karne_brifingi.py` kırpma işareti, `aylik_bucket_kopya.py`
      ölçü iletisi) `_py_parcalari` ile taranır: her dizge sabiti (docstring, ileti; f-string'in sabit
      kısımları, örtük bitiştirme ayrıştırıcının birleştirdiği hâliyle) ve her yorum → DÜZYAZI (yalnız
      argümanlı anış çağrıdır). Kod taranmaz: `subprocess.run(["uv", "sync", …])` listesinin ayrı
      sabitleri tek başına çağrı değildir (bilinçli sınır, aşağıda).
  (2) A1 ↔ YEREL ÖLÇÜTÜ. Varsayılan A1'dir: öğüt A0 semantiğini taşır. Gerekçe İKİ yönlü ölçüldü (bu tur,
      uv 0.11.28, yalıtılmış proje, `--offline`): A0 semantiği YEREL geliştirici venv'inde ZARARSIZDIR —
      dev kurulu venv'de `uv run --frozen --no-dev true` çıktısız, rc 0, dev paketi (pluggy) YERİNDE ve
      içe aktarılabilir (`uv run` varsayılan inexact'tir: `--no-dev` kurulmamayı söyler, kaldırmayı değil);
      ters yön A1'de ZARARLIDIR (dev geri kurulur, bayat kilit yeniden yazılır — v558/TSK-230). Yani bir
      öğüdü "yerel" yapan yer iddiası değil, A1'de KOŞAMAMASIDIR: komut dev grubu ister (`lint-imports`,
      `pytest`, `mutmut`, `import_tarama`nın dev ölçümü — A1'de dev grubu kurulu değil) → `YEREL` beyan;
      ya da metin bir öğüt değil BETİMLEMEdir (tarihçe, süreç adı) → `BETIMLEYICI` beyan. İki sınıfın da
      ölçülebilir koşulu var: BETİMLEYİCİ beyan bir KOD çağrısını susturamaz (C3); YEREL beyanın kaynağı
      hiçbir A1 yürütme yüzeyinde (birim/drop-in komutu · A0 rol görevi · dagit A1 play'i · hermes
      profili) geçemez — geçerse A1'de koşuyordur ve beyan yalandır (C4).
  (3) KİLİT EKSENİ (A6). Beyan GRUP eksenini (dev) muaf tutar, KİLİT eksenini DEĞİL: kapsamdaki her KOD
      bağlamı `uv run|sync|audit` çağrısı (yardım hariç) A0 kümesinin kilit alt kümesini (`--frozen`)
      taşır ya da aynı dosyada ondan ÖNCE bir `uv lock --check` KOD çağrısı koşar (ci_duman `[0/4]` —
      yeniden yazım o zaman SESSİZ değildir, KIRMIZI raporlanmıştır). `audit` bu eksende ölçülür çünkü
      TSK-230 onun da bayat kilidi yeniden yazdığını ölçtü. `ops/kapilar.sh` kilit kapısı taşımaz ve ilk
      işi bayraksız `uv run` idi → bayat kilitte yerel uv.lock'u SESSİZCE yeniden yazıyordu; üç uv adımı
      da `--frozen` taşır (`--no-dev` YOK: kapı dev araçlarını koşar). K1 onu operatörün biçiminde (sahte
      `UV`) koşar. Aynı sınıf `haftalik_mutasyon.sh`de de vardı (mutmut, yerel) — düzeltildi.

MODELLENMEYEN (bilinçli; hepsi adıyla):
  · Python KODU (dizge dışı): liste biçimli `subprocess` çağrıları (`["uv", "sync", …]`) ve satırlara
    bölünmüş tek bir çağrı (docstring'de `uv run` bir satırda, bayrakları sonrakinde) görülmez. Bugün
    kapsamda liste biçimli tek çağrı `import_tarama.py::dev_kumesi` (`--frozen --no-default-groups
    --dry-run`, yerel ölçüm) — okundu 2026-09-27.
  · `meridian/` (motor) ileti metinleri kapsam DIŞI (TSK-238 brief'i `ops/` + `deploy/`); ölçüldü: tek
    satır, `meridian/adapters/alpaca.py` "`uv sync --extra live` to enable Alpaca fills" (rapor).
  · `deploy/ansible/*.yml` görev metinleri: A0'ın kendi `uv sync`i v558'de; `[0c]/[0d]` A0 (yerel) komutu.
  · Kök `serve.sh` / `README.md` / `.github/` (`ci.yml`i yalnız E2/E6/E6b/E7 ölçer) — A1'e gitmeyen yerel
    yüzey.
  · `$(…)` içindeki `case` deseni `)`i, `$'…'` ayrıntıları — bugün kapsamda yok; olursa A3 öter.

Numara v566: ana checkout + worktree'lerde boş (ölçüldü 2026-09-27; v567 paralel ajanın). Bu dosya
`state/` okumaz/yazmaz; E1 `ops/ci_duman.sh`i SAHTE bir `UV` ile koşar (hiçbir gerçek araç çağrılmaz),
E4 gerçek `uv lock --check --offline`ı tmp kopyada + depoda koşar (yazmaz — sha ile ölçülür).
"""
from __future__ import annotations

import ast
import dataclasses
import functools
import hashlib
import io
import os
import re
import shutil
import subprocess
import tokenize
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_ansible_dagit_v452 import (
    _dagit_yml,
    _jinja_ortami,
    _komut_metni,
    _play_gorevleri,
    _when_degerlendir,
)
from tests.test_birim_argv_sir_v554 import KOMUT_YONERGELERI, _goreli
from tests.test_birim_argv_sir_v554 import _kapsam as _birim_kapsami
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _yonergeler
from tests.test_birim_uv_run_v558 import (
    DEV_HARIC_BAYRAKLAR,
    ESITLEYEN_ALT_KOMUTLAR,
    _bayrak,
    _beklenen,
    _defaults,
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


class Beyan(NamedTuple):
    """`sinif`: `YEREL` (komut A1'de KOŞAMAZ — dev grubu ister; C4: kaynak hiçbir A1 yürütme yüzeyinde
    geçmez) ya da `BETIMLEYICI` (öğüt değil, ad/tarihçe; C3: yalnız KOD OLMAYAN parçayı susturur)."""
    sinif: str
    gerekce: str


YEREL, BETIMLEYICI = "YEREL", "BETIMLEYICI"

#: (depo-göreli kaynak, çağrının parçasında geçen LİTERAL parmak izi) → Beyan (gerekçe ≥20 karakter).
#: Parmak izi, çağrının bulunduğu parça metninde (tek mantıksal satır) geçmek zorunda; kullanılmayan
#: anahtar çürüktür (C1). Beyan yalnız GRUP eksenini muaf tutar — KOD çağrısının kilit ekseni A6'da.
UV_CAGRI_BEYANI: dict[tuple[str, str], Beyan] = {
    ("ops/ci_duman.sh", "run python -m compileall"): Beyan(YEREL,
        "CI/yerel duman kapısı — A1'e GİTMEZ (CI koşucusu ve geliştirici makinesi). Kilit bu çağrıdan "
        "ÖNCE [0/4]'te denetlenir; CI eşitlemesi `--frozen --extra dev` (ci.yml, E2)."),
    ("ops/ci_duman.sh", "run lint-imports"): Beyan(YEREL,
        "CI/yerel duman kapısı — A1'e GİTMEZ; import-linter DEV grubundadır, `--no-dev` kapıyı "
        "'command not found' ile KOŞMADAN geçirirdi (dagit [0c] şerhindeki aynı gerekçe)."),
    ("ops/ci_duman.sh", "run pytest"): Beyan(YEREL,
        "CI/yerel duman kapısı — A1'e GİTMEZ; duman kapsamı pytest + hypothesis ister (extra `dev` + "
        "dependency-group `dev`; CI ikisini de eşitler) — `--no-dev` kapsamı koşturmazdı."),
    ("ops/kapilar.sh", "run --frozen lint-imports"): Beyan(YEREL,
        "Yerel hızlı kapı (geliştirici makinesi, ci_duman.sh'ın yerel ikizi) — A1'e GİTMEZ; "
        "import-linter DEV grubundadır. `--frozen` VAR (A6: kilit kapısı yok, yeniden yazım sessiz olurdu)."),
    ("ops/kapilar.sh", "run --frozen pytest"): Beyan(YEREL,
        "Yerel hızlı kapı + onun yerel tekrar öğüdü (echo) — A1'e GİTMEZ; kapsam pytest + hypothesis "
        "ister (extra `dev` + dependency-group `dev`)."),
    ("ops/haftalik_mutasyon.sh", "run --frozen python - <<"): Beyan(YEREL,
        "Mutasyon öz-testi (heredoc) `mutmut`u içe aktarır — dev grubu; betik ELLE, geliştirici venv'inde "
        "koşar (deploy/ altında birimi/timer'ı yok, 2026-09-27 ölçüldü). A1'e dev grubu kurulmaz."),
    ("ops/haftalik_mutasyon.sh", "run --frozen mutmut"): Beyan(YEREL,
        "Haftalık mutasyon koşumu ELLE, geliştirici venv'inde — A1'e GİTMEZ; `mutmut` dev grubundadır, "
        "`--no-dev` aracı ortamdan düşürürdü."),
    ("ops/barsarchive-run.sh", "uv sync --extra dev"): Beyan(YEREL,
        "Mac-dönemi yerel arşivci başlatıcısı (launchd'siz nohup; A1'de arşivciyi "
        "meridian-barsarchive.service koşar) — öğüt YEREL geliştirici venv'i içindir; A1 DEĞİL."),
    ("ops/import_tarama.py", "run python ops/import_tarama.py"): Beyan(YEREL,
        "Kullanım öğüdü YEREL (A0) ölçüm aracınındır: araç dev grubunun kaldırılmasını ölçer ve modül → "
        "dağıtım eşlemesini KURULU ortamdan okur — dev grubu kurulu venv ister (A1'de yok); dagit [0d] onu "
        "Play 1'de (localhost) koşar."),
    ("ops/import_tarama.py", "uv sync --dry-run"): Beyan(BETIMLEYICI,
        "Betimleme: aracın KENDİ ölçüm çağrısını (`dev_kumesi`: `--frozen --no-default-groups --dry-run`) "
        "ve rapor etiketini adlandırır — operatöre öğüt değil."),
    ("ops/state_fark_hukmu.py", "run python - <<"): Beyan(BETIMLEYICI,
        "Tarihçe: gövdenin dagit.sh [1b]'deki ESKİ heredoc yerini adlandırır — öğüt değil; bugünkü "
        "çağıran dagit.yml [1b] (Play 1, localhost)."),
    ("deploy/oracle-a1/meridian-sprint@.service", "uv run uvicorn"): Beyan(BETIMLEYICI,
        "Betimleyici şerh: canlı pano sürecinin ADINI anlatır, koşulmaz. Dosya F9 artefaktıdır "
        "(elle kurulur) — yalnız şerh için değiştirmek F9 içerik kapısında AYRIK gürültüsü üretir."),
    ("deploy/oracle-a1/meridian-fail-notify.service.d/10-sertlestirme-faz1.conf", "uv run python"): Beyan(
        BETIMLEYICI,
        "Betimleyici şerh: sertleştirmenin ÖLÇÜLEN yüzeyini (ubuntu olarak koşan süreç) anlatır, "
        "komut öğütlemez; birimin kendi ExecStart'ı v558 ile `--frozen --no-dev` taşır."),
}

#: A6 kilit ekseni: A0 eşitleme-semantiğinin KİLİT alt kümesi bu bayraklardan türer (v558 süzgeci).
KILIT_SEMANTIGI = frozenset({"--frozen", "--locked", "--no-sync"})
#: Bayat kilidi yeniden yazabilen alt komutlar (TSK-230 ölçümü: bayraksız `run` ve `audit` yazdı).
KILIT_YAZAN_ALT_KOMUTLAR = ESITLEYEN_ALT_KOMUTLAR | {"audit"}

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


def _py_parcalari(metin: str) -> list[Parca]:
    """Python kaynağı → İLETİ/DÜZYAZI parçaları (TSK-238): her dizge sabiti ve her yorum, satır satır.

    Dizge: `ast` ile — docstring, ileti, f-string'in SABİT kısımları (`{…}` yer tutucusuyla) ve örtük
    bitiştirme ayrıştırıcının birleştirdiği hâliyle (iki sabite bölünmüş bir öğüt tek metin olur).
    f-string'in iç sabitleri ayrıca SAYILMAZ (çift sayım yok). Yorum: `tokenize` COMMENT jetonu.
    Satır numarası dizgenin başladığı satırdır (+ dizge içi satır ofseti) — yalnız raporlama içindir."""
    agac = ast.parse(metin)
    ic: set[int] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.JoinedStr):
            ic.update(id(v) for v in dugum.values)
    parcalar: list[Parca] = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.JoinedStr) and id(dugum) not in ic:
            govde = "".join(v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else "{…}"
                            for v in dugum.values)
        elif isinstance(dugum, ast.Constant) and isinstance(dugum.value, str) and id(dugum) not in ic:
            govde = dugum.value
        else:
            continue
        parcalar += [Parca("duzyazi", dugum.lineno + k, s) for k, s in enumerate(govde.splitlines()) if s.strip()]
    for jeton in tokenize.generate_tokens(io.StringIO(metin).readline):
        if jeton.type == tokenize.COMMENT:
            parcalar.append(Parca("yorum", jeton.start[0], jeton.string[1:]))
    return sorted(parcalar, key=lambda p: (p.satir, p.tur, p.metin))


def _sh_kapsami(kok: Path = KOK) -> list[Path]:
    return sorted(set((kok / "deploy").rglob("*.sh")) | set((kok / "ops").glob("*.sh")))


def _py_kapsami(kok: Path = KOK) -> list[Path]:
    """TSK-238 brief'inin Python yüzeyi: `ops/*.py` + `deploy/*/*.py`."""
    return sorted(set((kok / "ops").glob("*.py")) | set((kok / "deploy").glob("*/*.py")))


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
    py = _py_kapsami()
    for p in py:
        kaynak = _goreli(p, KOK)
        sonuc += [(kaynak, x) for x in _py_parcalari(p.read_text(encoding="utf-8"))]
    # Üretici başlığı: yalnız sh/py taramasının KAPSAMADIĞI dosyalar için (kapsananın başlığı zaten
    # yorum/docstring olarak yukarıda taranır — iki kez saymak çift ihlal üretirdi).
    dogrudan_taranan = {_goreli(p, KOK) for p in (*sh, *py)}
    for yol, baslik in _runbook_basliklari():
        if yol not in dogrudan_taranan:
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
        # TSK-238 Python ileti/docstring yüzeyi (A1'de koşulan araçların öğütleri + bot iletileri)
        "ops/karne_brifingi.py": 6,                 # kullanım ×2 + kırpma işareti ×2 + ileti ×2
        "ops/sermaye_beyani_iade.py": 6,            # kullanım ×5 + "uygulamak için" iletisi
        "ops/bekci_brifingi.py": 3,                 # kullanım ×2 + "tam liste" iletisi
        "ops/plan_geri_doldur.py": 3,               # kullanım ×3
        "ops/sef_brifingi.py": 2,
        "ops/alarm_backlog_digest.py": 2,
        "ops/bekci_tarama.py": 1,                   # bekçi iletisi
        "ops/karne_hesap.py": 1,                    # "state/events.jsonl'e YAZAR" uyarısı
        "deploy/oracle-a1/aylik_bucket_kopya.py": 1,  # operatöre ölçü iletisi
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
    """Üretici başlıklarının `deploy/`·`ops/` sh/py kümesine girmeyen kısmı (kök `dagit.sh`,
    `meridian/auth_cli.py`, `altyapi/altyapi.sh`) GERÇEKTEN taranıyor — kanal boş kalırsa kapsamın o
    ayağı ölü. `ops/*.py` CLI'larının başlığı TSK-238'den beri Python taramasında (yorum jetonu)."""
    sh = {_goreli(p, KOK) for p in (*_sh_kapsami(), *_py_kapsami())}
    dogrudan = [yol for yol, _ in _runbook_basliklari() if yol not in sh]
    assert "dagit.sh" in dogrudan and len(dogrudan) >= 3, dogrudan
    ciftler, _ = _taranan_parcalar()
    taranan = {k for k, p in ciftler if p.satir == 0}
    bos_baslikli = {yol for yol, baslik in _runbook_basliklari() if not baslik.strip()}
    assert taranan == set(dogrudan) - bos_baslikli, (sorted(taranan), sorted(dogrudan), sorted(bos_baslikli))


def test_A5_python_yuzeyi_TARANIYOR_ve_bot_iletisi_gorulur():
    """TSK-238: Python ileti/docstring kanalı CANLI — yalnız docstring değil, operatöre giden ileti
    dizgeleri de (f-string, örtük bitiştirme) görülür. A2 sayı tabanıdır; bu çivi KANALI adlandırır."""
    ciftler, _ = _taranan_parcalar()
    py = {_goreli(p, KOK) for p in _py_kapsami()}
    assert {"ops/karne_brifingi.py", "deploy/oracle-a1/aylik_bucket_kopya.py"} <= py, "Python kapsamı eksik"
    karne_ileti = [c for c in _cagrilar([(k, p) for k, p in ciftler if k == "ops/karne_brifingi.py"])
                   if "KIRPILDI" in c.parca]
    assert len(karne_ileti) == 2 and all(c.tur == "duzyazi" for c in karne_ileti), (
        f"karne kırpma işareti (Telegram iletisi) iki yerde görülmeli: {karne_ileti}")
    assert all(c.satir > 1 for c in _depo_cagrilari() if c.kaynak in py), "Python parçası satırsız"


def test_A6_KILIT_EKSENI_kod_cagrisi_kilidi_SESSIZCE_yeniden_yazmaz():
    """Beyan GRUP eksenini (dev) muaf tutar, KİLİT eksenini değil. Her KOD bağlamı `uv run|sync|audit`
    (yardım hariç) A0'ın kilit bayrağını taşır ya da aynı dosyada ondan ÖNCE bir `uv lock --check` KOD
    çağrısı koşmuştur (yeniden yazım o zaman KIRMIZI raporlanmış olur, sessiz değil)."""
    ihlaller, gorulen = _kilit_ekseni_ihlalleri()
    assert gorulen >= 10, f"kilit ekseni yalnız {gorulen} KOD çağrısı gördü — tarama kör olabilir"
    assert not ihlaller, (
        f"KOD çağrısı bayat kilidi SESSİZCE yeniden yazabilir (A0 kilit semantiği "
        f"{sorted(_beklenen() & KILIT_SEMANTIGI)} yok ve dosyada önce `uv lock --check` koşmuyor):\n"
        f"{_bicimle(ihlaller)}\nÇARE: bayrağı alt komuttan SONRA ekle (`uv run --frozen <komut>`, "
        "`uv audit --frozen …`) ya da betiğin başına kilit tazeliği kapısı koy.")


def _kilit_ekseni_ihlalleri(ciftler=None) -> tuple[list[Cagri], int]:
    if ciftler is None:
        ciftler, _ = _taranan_parcalar()
    beklenen_kilit = _beklenen() & KILIT_SEMANTIGI
    assert beklenen_kilit, "A0 `uv sync` görev metni kilit bayrağı taşımıyor — A6'nın kaynağı yok"
    ilk_kilit_denetimi: dict[str, int] = {}
    kod: list[Cagri] = []
    for kaynak, p in ciftler:
        if p.tur != "kod":
            continue
        for alt, sec in _uv_cagrilari(p.metin):
            if alt == "lock" and "--check" in sec:
                ilk_kilit_denetimi.setdefault(kaynak, p.satir)
            elif alt in KILIT_YAZAN_ALT_KOMUTLAR and not {"--help", "-h"} & set(sec):
                kod.append(Cagri(kaynak, p.satir, p.tur, alt, sec, p.metin.strip()))
    ihlaller = [c for c in sorted(kod)
                if _semantik(c.secenekler) & KILIT_SEMANTIGI != beklenen_kilit
                and not ilk_kilit_denetimi.get(c.kaynak, c.satir + 1) < c.satir]
    return ihlaller, len(kod)


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
    for anahtar, beyan in UV_CAGRI_BEYANI.items():
        assert isinstance(anahtar, tuple) and len(anahtar) == 2 and all(anahtar), anahtar
        assert (KOK / anahtar[0]).is_file(), f"{anahtar}: kaynak dosya yok"
        assert beyan.sinif in (YEREL, BETIMLEYICI), f"{anahtar}: bilinmeyen sınıf {beyan.sinif!r}"
        assert len(beyan.gerekce.strip()) >= 20, f"{anahtar}: gerekçe kısa"
    _, kullanilan = _tara(list(_depo_cagrilari()), beklenen=_beklenen())
    curuk = sorted(set(UV_CAGRI_BEYANI) - kullanilan)
    assert not curuk, f"çürük beyan (ayrık çağrı artık yok ya da parmak izi eşleşmiyor — SİL): {curuk}"


def test_C3_BETIMLEYICI_beyan_KOD_cagrisini_SUSTURAMAZ():
    """Betimleme bir öğüt değildir — ama koşan bir kabuk satırı da betimleme değildir. BETİMLEYİCİ bir
    beyanın susturduğu her çağrı düzyazı/yorum/tırnak parçasındadır; KOD'a düşerse beyan yanlış sınıftadır."""
    betimleyici = {k for k, b in UV_CAGRI_BEYANI.items() if b.sinif == BETIMLEYICI}
    assert betimleyici, "BETİMLEYİCİ sınıfta beyan yok — çivi boşta"
    yanlis = [c for c in _depo_cagrilari() if c.tur == "kod"
              and any(k[0] == c.kaynak and k[1] in c.parca for k in betimleyici)]
    assert not yanlis, f"BETİMLEYİCİ beyan KOD çağrısını susturuyor:\n{_bicimle(yanlis)}"


def _a1_yurutme_metinleri() -> dict[str, list[str]]:
    """A1'de GERÇEKTEN koşan komut yüzeyleri → metinler (C4). Kabuk betikleri (`deploy/**/*.sh`) BİLEREK
    dışarıda: yerel/uzak karışıktır — `cutover.sh` `./ops/barsarchive-run.sh stop`u Mac'te koşar (ölçüldü)."""
    cikti: dict[str, list[str]] = {}
    for p in _birim_kapsami():                       # birim + drop-in komut yönergeleri (yalnız A1'de koşar)
        cikti[_goreli(p, KOK)] = [d for _b, a, d in _yonergeler(p.read_text(encoding="utf-8"))
                                  if a in KOMUT_YONERGELERI]

    def dizgeler(dugum):
        if isinstance(dugum, dict):
            for anahtar, deger in dugum.items():
                if anahtar != "name":
                    yield from dizgeler(deger)
        elif isinstance(dugum, list):
            for oge in dugum:
                yield from dizgeler(oge)
        elif isinstance(dugum, str):
            yield dugum

    for p in sorted((DEPLOY / "ansible" / "roles").rglob("tasks/*.yml")):   # A0 rolü → A1
        cikti[_goreli(p, KOK)] = list(dizgeler(yaml.safe_load(p.read_text(encoding="utf-8"))))
    a1_play = [pl for pl in _dagit_yml() if pl.get("hosts") != "localhost"]
    assert len(a1_play) == 1, f"dagit.yml'de tek A1 play'i beklenirdi: {[pl.get('hosts') for pl in _dagit_yml()]}"
    cikti["deploy/ansible/dagit.yml (A1 play)"] = [
        s for g in _play_gorevleri(a1_play[0]) if g.get("delegate_to") != "localhost" for s in dizgeler(g)]
    for p in sorted((DEPLOY / "hermes" / "profiles").glob("*/*.yaml")):     # bot profilleri A1'de koşar
        cikti[_goreli(p, KOK)] = [p.read_text(encoding="utf-8")]
    return cikti


def test_C4_YEREL_beyanin_kaynagi_hicbir_A1_yurutme_yuzeyinde_GECMEZ():
    """YEREL beyanın ölçülebilir iddiası: bu komut A1'de koşmaz. Kaynağın adı bir A1 birim komutunda,
    A0 rol görevinde, dagit'in A1 play'inde ya da bir hermes profilinde geçiyorsa A1'de koşuyordur ve
    beyan yalandır — o çağrı A0 semantiğini taşımak zorundadır."""
    yuzeyler = _a1_yurutme_metinleri()
    assert len(yuzeyler) >= 20 and any("hermes" in k for k in yuzeyler), f"A1 yüzeyi kör: {sorted(yuzeyler)[:5]}"
    kaynaklar = sorted({k[0] for k, b in UV_CAGRI_BEYANI.items() if b.sinif == YEREL})
    assert kaynaklar, "YEREL sınıfta beyan yok — çivi boşta"
    gecen = [(kaynak, yuzey) for kaynak in kaynaklar for yuzey, metinler in yuzeyler.items()
             if any(Path(kaynak).name in m for m in metinler)]
    assert not gecen, f"YEREL beyanlı kaynak bir A1 yürütme yüzeyinde koşuyor (beyan yalan): {gecen}"


def test_C4b_A1_yurutme_yuzeyi_POZITIF_KONTROL_bilinen_A1_betigi_gorulur():
    """C4'ün gözü açık mı: A1 birimlerinin koştuğu bilinen betikler yüzeyde GÖRÜLÜR."""
    yuzeyler = _a1_yurutme_metinleri()
    for ad in ("karne_hesap.py", "sef_brifingi.py", "aylik_bucket_kopya.py"):
        assert any(ad in m for metinler in yuzeyler.values() for m in metinler), f"{ad} A1 yüzeyinde görülmedi"


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


_PY_ORNEK = '''"""Modül.

KULLANIM:
    uv run python ops/x.py --uygula     # A1 öğüdü (bayraksız)
    uv run --frozen --no-dev python ops/x.py
"""
import subprocess
# ölçü: `uv run python -m meridian.barsarchive --ozet`
# `uv run` önbelleği (ad)
def f(n):
    subprocess.run(["uv", "sync", "--dry-run"])
    a = f"… (KIRPILDI — tamamı: `uv run python ops/k.py --json`, {n})"
    b = ("önce: uv sync "
         "--extra dev")
    return "düz dizge `uv sync` etiketi"
'''


def test_D5_pozitif_kontrol_PYTHON_dizge_ve_yorum_taramasi():
    """`_py_parcalari`: docstring satırları, yorum, f-string sabit kısmı, ÖRTÜK BİTİŞTİRME (iki sabite
    bölünmüş öğüt tek metin) görülür; liste biçimli `subprocess` çağrısı ve argümansız ad görülmez."""
    bulunan = sorted((p.satir, p.tur, alt, sec) for p in _py_parcalari(_PY_ORNEK) for alt, sec in _parca_cagrilari(p))
    assert bulunan == [
        (4, "duzyazi", "run", ()),
        (5, "duzyazi", "run", ("--frozen", "--no-dev")),
        (8, "yorum", "run", ()),
        (12, "duzyazi", "run", ()),
        (13, "duzyazi", "sync", ("--extra",)),
    ], bulunan


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
  "audit --help") exit "${SAHTE_AUDIT_YARDIM_RC:-2}" ;;
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


KAPILAR = OPS / "kapilar.sh"


@pytest.mark.parametrize("kip", ["tam", "--hizli"])
def test_K1_kapilar_OPERATOR_BICIMINDE_her_uv_adimi_frozen_ILK_adim_dahil(tmp_path, kip):
    """TSK-238 (b): `ops/kapilar.sh` kilit kapısı taşımaz; ilk işi bayraksız `uv run` idi → bayat kilitte
    yerel uv.lock SESSİZCE yeniden yazılıyordu. Betik operatörün koşacağı biçimde (sahte `UV`, audit
    alt komutu VAR) koşulur: kaydedilen her proje çağrısı (`run`/`sync`/`audit`, yardım hariç) `--frozen`
    taşır, İLK uv adımı dahil. `--no-dev` YOK (kapı dev araçlarını koşar — A6 yalnız kilit eksenini ister)."""
    sahte = tmp_path / "uv"
    sahte.write_text(_SAHTE_UV, encoding="utf-8")
    sahte.chmod(0o755)
    kayit = tmp_path / "kayit.txt"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("UV_", "SAHTE_"))}
    env.update({"UV": str(sahte), "SAHTE_UV_KAYIT": str(kayit), "SAHTE_AUDIT_YARDIM_RC": "0"})
    argv = ["bash", str(KAPILAR)] + ([kip] if kip != "tam" else [])
    r = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "KAPI ZİNCİRİ YEŞİL" in r.stdout, f"{kip}: {r.returncode}\n{r.stdout[-1200:]}"
    cagrilar = [(k, _uv_cagrilari(f"uv {k}")) for k in kayit.read_text(encoding="utf-8").splitlines()]
    proje = [(k, c[0]) for k, c in cagrilar if c and c[0][0] in KILIT_YAZAN_ALT_KOMUTLAR
             and not {"--help", "-h"} & set(c[0][1])]
    beklenen_alt = ["run", "audit"] + (["run"] if kip == "tam" else [])
    assert [c[0] for _, c in proje] == beklenen_alt, f"{kip}: beklenmeyen çağrı dizisi: {cagrilar}"
    eksik = [k for k, (_alt, sec) in proje if "--frozen" not in sec]
    assert not eksik, f"{kip}: `--frozen`sız proje çağrısı (bayat kilidi yeniden yazar): {eksik}"
    assert all("--no-dev" not in sec for _, (_a, sec) in proje), "kapı dev araçlarını koşar — `--no-dev` olmamalı"


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


#: ÖLÇÜLEMEDİ iletisinin neden sınıflandırması — (register içeriği, iletide olması gereken neden parçası).
#: Girdiler ÖLÇÜLDÜ (2026-09-27): uv yokken Ansible `command` rc 2 + msg `[Errno 2] No such file…`;
#: kilitsiz proje stderr "Unable to find lockfile…"; bilinmeyen bayrak (clap) "unexpected argument '…' found".
OLCULEMEDI_NEDENLERI = [
    ({"rc": 2, "msg": "[Errno 2] No such file or directory: b'uv'", "stderr": "", "stderr_lines": []},
     "uv bulunamadı"),
    ({"rc": 2, "msg": "non-zero return code",
      "stderr": "error: Unable to find lockfile at `uv.lock`, but `--check` was provided.",
      "stderr_lines": ["error: Unable to find lockfile at `uv.lock`, but `--check` was provided."]},
     "uv.lock yok"),
    ({"rc": 2, "msg": "non-zero return code", "stderr": "error: unexpected argument '--check' found",
      "stderr_lines": ["error: unexpected argument '--check' found"]},
     "`lock --check` bayrağını tanımıyor"),
    ({"rc": 2, "msg": "non-zero return code", "stderr": "error: No interpreter found",
      "stderr_lines": ["error: No interpreter found"]},
     "uv çıkış 2"),
]


def test_E3_dagit_0b_kilit_kapisi_ILK_uv_gorevi_rc1_DURUR_rc2_SURER_ve_BASAR():
    """Rol-1 hükmü (TSK-230 tur 2): kapının amacı AYRIŞMA. rc 1 → dağıtım DURUR; rc 2 (uv ölçemedi) →
    DURMAZ ama SESSİZ de geçmez — ÖLÇÜLEMEDİ nedeniyle log'a basılır; sözleşme dışı kod görevi düşürür."""
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
    # failed_when: sözleşmedeki üç kod hükme taşınır, sözleşme dışı kod görevi düşürür.
    for rc, dusmeli in ((0, False), (1, False), (2, False), (3, True), (-9, True)):
        assert _when_degerlendir(olcum["failed_when"], {kayit: {"rc": rc}}) is dusmeli, (rc, olcum["failed_when"])
    # KAPI: ölçümün hemen ardındaki assert — rc 1 DURDURUR, rc 0 ve rc 2 GEÇER.
    sonraki = gorevler[ki + 1:ki + 3]
    assertler = [g for g in sonraki
                 if "ansible.builtin.assert" in g and kayit in str(g["ansible.builtin.assert"].get("that"))]
    assert len(assertler) == 1, "kilit ölçümünün hemen ardında tek bir KAPI (assert) görevi yok"
    that = assertler[0]["ansible.builtin.assert"]["that"]
    for rc, gecmeli in ((0, True), (1, False), (2, True)):
        assert _when_degerlendir(that, {kayit: {"rc": rc}}) is gecmeli, (
            f"rc {rc}: {'geçmeli' if gecmeli else 'DURDURMALI'} — {that}")
    assert "uv lock" in str(assertler[0]["ansible.builtin.assert"].get("fail_msg")), "fail_msg çareyi söylemiyor"
    # ÖLÇÜLEMEDİ: SESSİZ DEĞİL — yalnız rc 2'de basan bir `debug` (durdurmaz), iletisi nedeni taşır.
    debuglar = [g for g in sonraki if "ansible.builtin.debug" in g]
    assert len(debuglar) == 1, "rc 2 için ÖLÇÜLEMEDİ iletisini basan `debug` görevi kilit kapısının ardında yok"
    debug = debuglar[0]
    for rc, basmali in ((0, False), (1, False), (2, True)):
        assert _when_degerlendir(debug.get("when", "false"), {kayit: {"rc": rc}}) is basmali, (
            f"ÖLÇÜLEMEDİ iletisi rc {rc}'de {'basılmalı' if basmali else 'basılMAMALI'}: {debug.get('when')!r}")
    sablon = _jinja_ortami().from_string(str(debug["ansible.builtin.debug"]["msg"]))
    for sonuc, neden in OLCULEMEDI_NEDENLERI:
        ileti = sablon.render(**{kayit: sonuc})
        assert "ÖLÇÜLEMEDİ" in ileti and "dağıtım sürüyor" in ileti and neden in ileti, (
            f"neden {neden!r} iletide yok ya da ileti 'sürüyor' demiyor:\n{ileti}")


def test_E3b_dagit_README_0b_satiri_kilit_kontrolunu_ve_rc_hukmunu_anar():
    satir = [s for s in ANSIBLE_README.read_text(encoding="utf-8").splitlines() if s.startswith("| `[0b]`")]
    assert len(satir) == 1 and "uv lock --check" in satir[0], satir
    assert "rc 1" in satir[0] and "ÖLÇÜLEMEDİ" in satir[0] and "sürer" in satir[0], (
        f"README `[0b]` satırı rc 1 = durur / rc 2 = ÖLÇÜLEMEDİ, sürer hükmünü söylemiyor: {satir[0]}")


#: `https://astral.sh/uv[/<sürüm>]/install.sh` — sürümsüz biçimde grup boş kalır.
_UV_KURULUM_URL = re.compile(r"https://astral\.sh/uv/(?:([^/\s]+)/)?install\.sh")


def test_E6_ci_uv_surumu_A1_pinine_ESIT_surumsuz_kurulum_YOK():
    """CI uv'si A1 pinine (`defaults/main.yml::uv_surum`, TEK KAYNAK) eşit: sürümsüz installer her koşumda
    en son uv'yi kurar ve `[0/4]` kod değişmeden kırmızıya dönebilirdi (inceleme bulgusu, tur 2)."""
    beklenen = str(_defaults()["uv_surum"])
    assert beklenen and beklenen != "OLCULECEK", f"A0 uv_surum ölçülmemiş: {beklenen!r}"
    veri = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    kosumlar = [adim.get("run", "") for is_ in veri["jobs"].values() for adim in is_.get("steps", [])]
    surumler = [m.group(1) or "" for k in kosumlar for m in _UV_KURULUM_URL.finditer(k)]
    assert surumler, "ci.yml uv'yi resmi installer'dan kurmuyor — çivi bayat"
    assert "" not in surumler, "ci.yml sürümsüz uv installer'ı kullanıyor (`astral.sh/uv/install.sh`)"
    assert set(surumler) == {beklenen}, (
        f"ci.yml uv sürümü {sorted(set(surumler))} ≠ A1 pini {beklenen!r} (defaults/main.yml::uv_surum) — "
        "ikisi aynı değişiklikte güncellenir")


#: TSK-238 (d) — CI kurulumu DOĞRULAMALIDIR. ÖLÇÜM (2026-09-27, GitHub API, yalnız üst veri):
#:   · `repos/astral-sh/uv/releases/tags/0.12.0` → `immutable: true` (yayımdan sonra varlık değiştirilemez);
#:   · `uv-installer.sh` varlığının GitHub-hesaplı özeti `sha256:b67e3850…8764` = A0 defaults
#:     `uv_installer_sha256` (Rol-1'in 2026-09-08'de `astral.sh/uv/0.12.0/install.sh`ten ölçtüğü değer) —
#:     iki bağımsız kaynak AYNI baytı gösteriyor; akış olarak okunan betiğin sha256'sı da aynı (diske yazılmadı);
#:   · betik (cargo-dist 0.31.0 şablonu) her arşivin sha256'sını GÖMÜLÜ taşır ve `verify_checksum` ile
#:     doğrular — `x86_64-unknown-linux-gnu` için gömülü değer = o arşivin GitHub özeti (`eaf84226…31a9`).
#: Zincir: sabit özetli installer → gömülü arşiv özeti. Sürüm ve özet A0 defaults'ta TEK kaynak; ci.yml
#: iki literal kopya taşır (YAML defaults'u okuyamaz) → E6 ikisini de eşitler, E7 davranışı koşar.
_SHA256 = re.compile(r"\b[0-9a-f]{64}\b")


def _ci_uv_kurulum_adimi() -> str:
    veri = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    adimlar = [adim.get("run", "") for is_ in veri["jobs"].values() for adim in is_.get("steps", [])
               if _UV_KURULUM_URL.search(adim.get("run", ""))]
    assert len(adimlar) == 1, f"ci.yml'de tek uv kurulum adımı beklenirdi: {len(adimlar)}"
    return adimlar[0]


def test_E6b_ci_uv_installer_OZETI_A0_ile_ESIT_ve_borulanmaz():
    """Sürüm-pinli URL sürümü sabitler ama içeriği DOĞRULAMAZ: `curl … | sh` indirdiğini körlemesine koşar.
    CI adımı installer'ı dosyaya indirir, A0 `uv_installer_sha256` ile doğrular, sonra koşar."""
    beklenen = str(_defaults()["uv_installer_sha256"])
    assert _SHA256.fullmatch(beklenen), f"A0 uv_installer_sha256 ölçülmemiş/biçimsiz: {beklenen!r}"
    adim = _ci_uv_kurulum_adimi()
    assert not re.search(r"curl[^\n]*\|\s*(sh|bash)\b", adim), "ci.yml installer'ı doğrulamadan kabuğa boruluyor"
    assert set(_SHA256.findall(adim)) == {beklenen}, (
        f"ci.yml installer özeti {sorted(set(_SHA256.findall(adim)))} ≠ A0 {beklenen!r} "
        "(defaults/main.yml::uv_installer_sha256) — sürüm ile AYNI değişiklikte güncellenir")
    assert "sha256sum -c" in adim, "özet doğrulaması (`sha256sum -c`) yok"


_SAHTE_CURL = r"""#!/usr/bin/env bash
# sahte curl: `-o <yol>` hedefine $SAHTE_ICERIK dosyasını yazar; URL'yi kaydeder.
hedef=""; onceki=""
for a in "$@"; do [ "$onceki" = "-o" ] && hedef="$a"; onceki="$a"; case "$a" in https://*) echo "$a" >> "$SAHTE_CURL_KAYIT";; esac; done
[ -n "$hedef" ] || { echo "sahte curl: -o yok (borulu kullanım?)" >&2; exit 97; }
cp "$SAHTE_ICERIK" "$hedef"
"""

_SAHTE_INSTALLER = """#!/bin/sh
mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\\necho "uv 0.0.0-sahte"\\n' > "$HOME/.local/bin/uv"
chmod +x "$HOME/.local/bin/uv"
touch "$HOME/KURULDU"
"""


@pytest.mark.parametrize("ozet_uyar", [False, True], ids=["ozet_UYUSMAZ_kurmaz", "ozet_uyar_kurar"])
def test_E7_ci_uv_kurulum_adimi_DAVRANISI_ozet_uyusmazsa_installer_KOSMAZ(tmp_path, ozet_uyar):
    """Adımın `run` gövdesi GitHub'ın varsayılan kabuğuyla (`bash -e`) sahte `curl` ile koşulur. Özet
    uyuşmazsa adım düşer ve installer HİÇ çalışmaz; uyarsa (özet sahte içeriğinkiyle değiştirilerek) kurar."""
    if shutil.which("sha256sum") is None:
        pytest.fail("sha256sum bulunamadı — 'koşamıyorum' bu çivide 'kırmızı' sayılır")
    kutu = tmp_path / "bin"
    kutu.mkdir()
    (kutu / "curl").write_text(_SAHTE_CURL, encoding="utf-8")
    (kutu / "curl").chmod(0o755)
    icerik = tmp_path / "installer.sh"
    icerik.write_text(_SAHTE_INSTALLER, encoding="utf-8")
    ev = tmp_path / "ev"
    ev.mkdir()
    gecici = tmp_path / "runner_temp"
    gecici.mkdir()
    adim = _ci_uv_kurulum_adimi()
    if ozet_uyar:
        adim = adim.replace(str(_defaults()["uv_installer_sha256"]), _sha(icerik))
    env = {"PATH": f"{kutu}:/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(ev), "RUNNER_TEMP": str(gecici),
           "SAHTE_ICERIK": str(icerik), "SAHTE_CURL_KAYIT": str(tmp_path / "curl.txt")}
    r = subprocess.run(["bash", "-e", "-c", adim], env=env, capture_output=True, text=True, timeout=60)
    kuruldu = (ev / "KURULDU").exists()
    url = (tmp_path / "curl.txt").read_text(encoding="utf-8").split()
    assert url and all(f"/uv/{_defaults()['uv_surum']}/install.sh" in u for u in url), url
    if ozet_uyar:
        assert r.returncode == 0 and kuruldu and "uv 0.0.0-sahte" in r.stdout, (r.returncode, r.stdout, r.stderr)
    else:
        assert r.returncode != 0 and not kuruldu, (
            f"özet uyuşmadığı hâlde installer ÇALIŞTI ya da adım geçti: rc {r.returncode}\n{r.stdout}\n{r.stderr}")


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
