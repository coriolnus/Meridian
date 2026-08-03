#!/usr/bin/env python3
"""import_tarama.py — ÇALIŞMA YOLU IMPORT TARAMASI (WP-H, 2026-08-03).

NEDEN VAR — bir İDDİA vardı, ÖLÇÜMÜ yoktu. `dagit.sh` [3] adımı 2026-08-01'de `--no-dev`e
çekildi ve gerekçesi şuydu: "çalışma yolunda sıfır dev-import ölçüldü". O ölçüm bir kereye
mahsus, elle ve KAYITSIZ yapılmıştı — yani bugün hâlâ doğru olup olmadığını kimse söyleyemezdi.
Yarın biri `meridian/` içine `import hypothesis` yazarsa daraltma canlıyı SESSİZCE düşürürdü
(A1'de o paket artık YOK) ve arıza dağıtımdan sonra, süreç açılırken patlardı. Bu betik iddiayı
YENİDEN ÜRETİLEBİLİR bir ölçüme çevirir: her koşuda baştan ölçer, kaynağını gösterir.

NE ÖLÇER: `meridian/` + `ops/` altındaki her `.py` dosyasının AST'sini ayrıştırır ve GERÇEKTEN
import edilen üçüncü-parti tepe-düzey modülleri çıkarır. AST tabanlıdır, metin araması DEĞİL:
`grep import` yorum satırını, dizgeyi ve docstring'i de yakalardı — üçü de import değildir.
Fonksiyon gövdesindeki import'lar DA sayılır (bu depoda yaygın: `hermes.py` içinde `import yaml`,
`earnings.py` içinde `import tempfile`) — tembel import da çalışma zamanında GERÇEKTEN yüklenir.

SERVE YOLU: `serve.sh` uvicorn'u `python -m uvicorn` ile SÜREÇ olarak başlatır; hiçbir `.py`
onu import etmez ama paket yoksa pano açılmaz. Bu yüzden `-m <modül>` çağrıları ayrıca taranır
ve "süreç düzeyi" olarak raporlanır — import grafiğinde görünmeyen ama çalışma yolunda ZORUNLU
olan bağımlılık sınıfı budur.

MODÜL → DAĞITIM EŞLEMESİ UYDURULMAZ, KURULU ORTAMDAN OKUNUR: `pyyaml` dağıtımı `yaml` modülünü,
`import-linter` `importlinter`ı verir; isimden türetmek tahmindir. `importlib.metadata.
packages_distributions()` kurulu metadata'dan GERÇEK eşlemeyi verir. Eşlenemeyen modül
"ÇÖZÜLEMEDİ" diye raporlanır — sessizce "üçüncü parti değil" sayılmaz (UYDURMA YASAĞI).

DEV KÜMESİ DE ÖLÇÜLÜR: `uv sync --dry-run` ile daraltmanın GERÇEKTEN kaldıracağı paketler
alınır — bu GEÇİŞLİ kümedir (`import-linter` → `grimp`, `mutmut` → `textual`, ...). pyproject'teki
3 satırlık doğrudan liste CVE yüzeyini ANLATMAZ; kaldırılan 17 paket anlatır. uv yoksa ölçüm
YAPILAMADI denir ve doğrudan-liste'ye düşülür (etiketiyle birlikte).

KULLANIM:
    uv run python ops/import_tarama.py            # tam rapor
    uv run python ops/import_tarama.py --sessiz   # yalnız HÜKÜM satırı (kapı kullanımı)
ÇIKIŞ KODU: 0 = daraltma güvenli (kesişim boş) · 1 = dev paketi çalışma yolunda · 2 = ölçülemedi
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
TARANAN_KOKLER = ["meridian", "ops"]
SERVE_BETIKLERI = ["serve.sh"]

# Bu depoda tepe-düzey ilk-parti adlar. `meridian` paketin kendisi; `ops` betik dizini.
ILK_PARTI = {"meridian", "ops", "tests", "conftest"}


def _dagitim_normal(ad: str) -> str:
    """PEP 503 normalizasyonu — `import-linter` / `import_linter` / `Import-Linter` aynı şeydir."""
    return re.sub(r"[-_.]+", "-", ad).lower()


def tepe_modulleri(dosya: Path) -> list[tuple[str, int]]:
    """Dosyadaki her import'un TEPE-DÜZEY modül adı + satır numarası.

    Göreli import (`from . import config`) ATLANIR: `node.level > 0` ilk-parti demektir ve
    `node.module` orada ya None'dır ya da paket-içi bir addır — üçüncü parti sayılamaz.
    """
    try:
        agac = ast.parse(dosya.read_text(encoding="utf-8"), filename=str(dosya))
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        # AYRIŞTIRILAMAYAN DOSYA "import yok" DEĞİLDİR: ölçüm yapılamadı demektir ve bu görünür olmalı.
        print(f"  !! AYRIŞTIRILAMADI {dosya.relative_to(KOK)}: {type(e).__name__}: {e}", file=sys.stderr)
        return []
    bulunan: list[tuple[str, int]] = []
    for node in ast.walk(agac):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bulunan.append((alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue                      # göreli → ilk parti
            if node.module:
                bulunan.append((node.module.split(".")[0], node.lineno))
    return bulunan


def surec_duzeyi_moduller() -> dict[str, str]:
    """serve.sh gibi betiklerdeki `python -m <modül>` çağrıları — import grafiğinde GÖRÜNMEZ.

    DESEN İKİ KEZ DARALTILDI (ilk koşumun yanlış-pozitifleri): `-m` bir SÖZCÜK İÇİNDEN
    yakalanmamalı. `x-meridian-token` "eridian", `real-money` ise "oney" üretiyordu — ikisi de
    yorum satırındaki tireli sözcüklerdi. Tire'nin önünde sözcük karakteri (ya da başka bir tire)
    OLMAMALI, ve `-m` ile modül adı arasında en az bir ayraç (boşluk/tırnak/virgül) BULUNMALI:
    gerçek çağrı `python -m uvicorn` ya da `'-m','uvicorn'` biçimindedir, `-money` değil.
    Yorum satırları ayrıca atlanır — bir yorumdaki örnek komut çalışma yolu KANITI değildir.
    """
    desen = re.compile(r"(?<![\w-])-m['\"]?[\s,]+['\"]?([A-Za-z_][A-Za-z0-9_]*)")
    out: dict[str, str] = {}
    for ad in SERVE_BETIKLERI:
        p = KOK / ad
        if not p.exists():
            continue
        for no, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if satir.lstrip().startswith("#"):
                continue
            for m in desen.finditer(satir):
                modul = m.group(1)
                if modul not in ILK_PARTI:
                    out.setdefault(modul, f"{ad}:{no}")
    return out


def dev_kumesi() -> tuple[set[str], str]:
    """Daraltmanın GERÇEKTEN kaldıracağı dağıtımlar (geçişli). (küme, kaynak_etiketi)."""
    try:
        r = subprocess.run(["uv", "sync", "--frozen", "--no-default-groups", "--dry-run"],
                           cwd=str(KOK), capture_output=True, text=True, timeout=180)
        kaldirilan = set()
        for satir in (r.stdout + r.stderr).splitlines():
            m = re.match(r"\s*-\s+([A-Za-z0-9][A-Za-z0-9._-]*)==", satir)
            if m:
                kaldirilan.add(_dagitim_normal(m.group(1)))
        if kaldirilan:
            return kaldirilan, "ÖLÇÜLDÜ (uv sync --dry-run · geçişli)"
    except (OSError, subprocess.SubprocessError):
        pass
    # ÖLÇÜM DÜŞTÜ → doğrudan listeye düşülür AMA etiketi bunu söyler; geçişli kapanış EKSİKTİR.
    veri = tomllib.loads((KOK / "pyproject.toml").read_text(encoding="utf-8"))
    dogrudan = set()
    for grup in (veri.get("dependency-groups") or {}).values():
        for spec in grup:
            if isinstance(spec, str):
                dogrudan.add(_dagitim_normal(re.split(r"[<>=!~\[; ]", spec, 1)[0]))
    return dogrudan, "ÖLÇÜLEMEDİ — pyproject doğrudan listesi (GEÇİŞLİ KAPANIŞ YOK)"


def ana_bagimliliklar() -> tuple[set[str], dict[str, set[str]]]:
    veri = tomllib.loads((KOK / "pyproject.toml").read_text(encoding="utf-8"))
    ana = {_dagitim_normal(re.split(r"[<>=!~\[; ]", s, 1)[0])
           for s in (veri.get("project", {}).get("dependencies") or [])}
    ekstralar = {ad: {_dagitim_normal(re.split(r"[<>=!~\[; ]", s, 1)[0]) for s in liste}
                 for ad, liste in (veri.get("project", {}).get("optional-dependencies") or {}).items()}
    return ana, ekstralar


def main() -> int:
    sessiz = "--sessiz" in sys.argv
    stdlib = set(sys.stdlib_module_names)
    mod2dist = {m: [_dagitim_normal(d) for d in ds] for m, ds in packages_distributions().items()}
    ana, ekstralar = ana_bagimliliklar()
    dev, dev_kaynak = dev_kumesi()

    # ---- tarama -------------------------------------------------------------------------------
    kullanim: dict[str, list[str]] = {}     # tepe modül -> ["dosya:satır", ...]
    dosya_sayisi = 0
    for kok_ad in TARANAN_KOKLER:
        for dosya in sorted((KOK / kok_ad).rglob("*.py")):
            if "__pycache__" in dosya.parts:
                continue
            dosya_sayisi += 1
            for modul, satir in tepe_modulleri(dosya):
                if modul in stdlib or modul in ILK_PARTI:
                    continue
                kullanim.setdefault(modul, []).append(f"{dosya.relative_to(KOK)}:{satir}")
    for modul, yer in surec_duzeyi_moduller().items():
        if modul not in stdlib:
            kullanim.setdefault(modul, []).append(f"{yer} (süreç-düzeyi -m)")

    # ---- sınıflandırma ------------------------------------------------------------------------
    cozulemeyen: list[str] = []
    dev_supheli: list[str] = []            # çözülemeyen ama DEV dağıtımına benzeyen → fail-closed
    calisma_yolu_dist: set[str] = set()
    satirlar: list[str] = []
    for modul in sorted(kullanim):
        dists = mod2dist.get(modul)
        if not dists:
            # Kurulu değil (koşullu/ekstra) ya da metadata yok. Tahmin YOK: modül adının kendisi
            # aday dağıtım olarak DENENİR ama "ÇÖZÜLEMEDİ" etiketi düşmez — hüküm buna güvenmez.
            aday = _dagitim_normal(modul)
            if aday in ana or any(aday in e for e in ekstralar.values()) or aday in dev:
                dists = [aday]
            else:
                # ADAY EŞLEME — ÖLÇÜM DEĞİL, ETİKETİ BUNU SÖYLER. `alpaca` modülünü `alpaca-py`
                # dağıtımı, `google`ı `google-cloud-secret-manager` verir; ikisi de KURULU
                # OLMADIĞI için metadata'da yok. Beyan edilmiş dağıtımlar arasında modül adıyla
                # BAŞLAYAN varsa aday olarak GÖSTERİLİR — ama hüküm buna dayanmaz.
                beyan = ana | dev | {d for e in ekstralar.values() for d in e}
                adaylar = sorted(d for d in beyan if d == aday or d.startswith(aday + "-"))
                cozulemeyen.append(modul)
                # FAIL-CLOSED: aday bir DEV dağıtımıysa, "çözülemedi" sessizce "temiz" sayılamaz —
                # daraltma o paketi kaldırır ve çalışma yolu onu import ediyor OLABİLİR.
                if any(a in dev for a in adaylar):
                    dev_supheli.append(f"{modul}~{'/'.join(a for a in adaylar if a in dev)}")
                ek = f" · ADAY: {', '.join(adaylar)}" if adaylar else ""
                satirlar.append(f"  {modul:<28} → ÇÖZÜLEMEDİ (kurulu değil){ek}"
                                f"  [{kullanim[modul][0]}]")
                continue
        calisma_yolu_dist.update(dists)
        etiketler = []
        for d in dists:
            if d in ana:
                etiketler.append("ana")
            elif d in dev:
                etiketler.append("GRUP:DEV")
            else:
                yer = [ad for ad, e in ekstralar.items() if d in e]
                etiketler.append(f"ekstra:{yer[0]}" if yer else "BEYAN-DIŞI")
        satirlar.append(f"  {modul:<28} → {', '.join(dists):<32} [{'/'.join(etiketler)}]"
                        f"  ({len(kullanim[modul])} yer)")

    kesisim = sorted(calisma_yolu_dist & dev)
    beyan_disi = sorted(d for d in calisma_yolu_dist if d not in ana and d not in dev
                        and not any(d in e for e in ekstralar.values()))

    if not sessiz:
        print("=== ÇALIŞMA YOLU IMPORT TARAMASI ===")
        print(f"kök: {', '.join(TARANAN_KOKLER)}/ — {dosya_sayisi} dosya · serve yolu: "
              f"{', '.join(SERVE_BETIKLERI)}")
        print(f"dev kümesi kaynağı: {dev_kaynak} — {len(dev)} dağıtım")
        print(f"\n--- üçüncü-parti tepe modüller ({len(kullanim)}) ---")
        print("\n".join(satirlar))
        if beyan_disi:
            print(f"\n!! BEYAN-DIŞI (çalışma yolunda import ediliyor ama pyproject'te YOK): "
                  f"{', '.join(beyan_disi)}")
        if cozulemeyen:
            print(f"\n?? ÇÖZÜLEMEDİ ({len(cozulemeyen)}): {', '.join(cozulemeyen)}")
            print("   (kurulu olmayan koşullu/ekstra import — hüküm ADAY eşlemeye GÜVENMEZ)")
        print(f"\n--- KESİŞİM (dev kümesi ∩ çalışma yolu) ---")
        print(f"  {', '.join(kesisim) if kesisim else '(BOŞ)'}")

    if "ÖLÇÜLEMEDİ" in dev_kaynak:
        print("HÜKÜM=ÖLÇÜLEMEDİ (uv koşulamadı — geçişli dev kümesi bilinmiyor, fail-closed)")
        return 2
    if dev_supheli:
        print(f"HÜKÜM=ÖLÇÜLEMEDİ — çözülemeyen modül bir DEV dağıtımına eşleşebilir: "
              f"{', '.join(dev_supheli)} (fail-closed: kurup yeniden ölç)")
        return 2
    if kesisim:
        print(f"HÜKÜM=DARALTMA-YOK — dev paketi çalışma yolunda: {', '.join(kesisim)}")
        return 1
    print(f"HÜKÜM=DARALT-GÜVENLİ — {len(dev)} dev dağıtımının HİÇBİRİ çalışma yolunda import "
          f"edilmiyor ({dosya_sayisi} dosya tarandı)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
