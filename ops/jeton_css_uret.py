#!/usr/bin/env python3
"""jeton_css_uret.py — `tokens.json`'dan CSS jeton bildirimlerini ÜRET (2026-08-24).

NEDEN VAR. Bugün dört yüzey (index/landing/workflow/runbook) aynı jeton bloğunu ELLE
kopyalıyor. Kopya, ilk düzenlemede ayrışır ve bunu bugün ölçtük: `--yon-*` tabanı değişti,
türevleri (saç teli .35, tint .10/.08) dört yüzeyde eski RGB'de kaldı; `tokens.json`'ın
`hex` / `literal` / `cozulen-deger` alanları birbirinden ayrıştı; kör bir `replace`
`--huni-3`'ü de vurdu ve bunu ancak bir çivi yakaladı.

Bu betik shadcn pilotunun G1 kapısının cevabıdır: pilot jetonları ELLE KOPYALAMAZ,
SSoT'tan üretir. Üretim DETERMİNİSTİKtir ve damga taşımaz — her koşu aynı baytı verir,
yoksa `--kontrol` diff gürültüsü üretirdi.

KULLANIM
    python ops/jeton_css_uret.py                    # ui/src/jetonlar.css üret/yaz
    python ops/jeton_css_uret.py --kontrol          # yazMA; diskteki dosya güncel mi (çıkış 1 = bayat)
    python ops/jeton_css_uret.py --cikti /yol.css   # başka hedefe yaz

KAPSAM SINIRI. Bu betik yalnız `tokens.json`ı okur ve YALNIZ jeton bildirimi üretir.
Bileşen kuralı üretmez — o katman rol jetonlarını okur ve bu ayrım sözleşmedir
(index.html:296-299 "bileşen kuralları YALNIZ rol jetonu okur").
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

KOK = pathlib.Path(__file__).resolve().parents[1]
JETONLAR = KOK / "meridian" / "web" / "tokens.json"
VARSAYILAN_CIKTI = KOK / "ui" / "src" / "jetonlar.css"

BASLIK = """/* ÜRETİLDİ — ELLE DÜZENLEME. Kaynak: meridian/web/tokens.json
   Üreten: ops/jeton_css_uret.py · deterministik, damgasız (her koşu aynı bayt).
   Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler; jetonu tokens.json'da değiştir.
   Tazelik kapısı: `python ops/jeton_css_uret.py --kontrol` (çıkış 1 = bayat).

   AD ÇAKIŞMASI, BEYANLI (TSK-134, 2026-09-04): bu dosyanın `:root`u ile `ui/src/tema.css`in
   shadcn `:root`u İKİ adı PAYLAŞIYOR — `--card`, `--accent`. `ui/src/tema.css` KAZANIR: bu
   dosya `@import "./jetonlar.css"` ile tema.css'in EN BAŞINDA yüklenir, tema.css'in KENDİ
   shadcn `:root` gövdesi metinde importtan SONRA gelir ve aynı özgüllükte SON bildirim kazanır
   (ölçüldü, `tests/test_jeton_shadcn_cakisma_v407.py`). Bu iki ad eski sayfalar (index/landing/
   runbook/workflow.html) İÇİNDİR — pano (`ui/src`) `bg-card`/`bg-accent` utility'sini
   `tema.css`in KENDİ `--color-card`/`--color-accent` eşlemesinden okur, bu dosyanın
   `--card`/`--accent`ından DEĞİL (pano kaynağında bracket okuması yok, ölçüldü). Düşürme
   (bu iki adı jetonlar.css sözlüğünden çıkarmak) AYRI bir kalem, kapsam DIŞINDA. */
"""


def _gez(o, yol=()):
    for k, v in (o.items() if isinstance(o, dict) else ()):
        if isinstance(v, dict) and "$value" in v:
            yield yol + (k,), v
        elif isinstance(v, dict):
            yield from _gez(v, yol + (k,))


def _css_degeri(deger, yol: str) -> str | None:
    """Bir `$value`yu CSS metnine çevir. ÇEVRİLEMEYEN None döner — UYDURMA YASAĞI:
    tanımadığı bir şekli tahmin etmez, atlar ve sayımda görünür."""
    if isinstance(deger, str):
        if deger.startswith("{") and deger.endswith("}"):
            # takma ad: {temel.tipografi.sans} → var(--sans)
            return "var(--" + deger.strip("{}").split(".")[-1] + ")"
        return deger
    if isinstance(deger, list):
        return ", ".join(f"'{x}'" if " " in x else x for x in deger)
    if isinstance(deger, dict):
        if "hex" in deger:
            return deger["hex"]
        if "value" in deger and "unit" in deger:
            v = deger["value"]
            return f"{int(v) if float(v) == int(v) else v}{deger['unit']}"
        if "components" in deger and deger.get("alpha") is not None:
            r, g, b = (round(c * 255) for c in deger["components"])
            return f"rgba({r},{g},{b},{deger['alpha']})"
        if "components" in deger:
            r, g, b = (round(c * 255) for c in deger["components"])
            return f"#{r:02x}{g:02x}{b:02x}"
    return None


def uret() -> tuple[str, list[str]]:
    """(css, atlananlar) döndür. Atlananlar SESSİZ DEĞİL — çağıran onları basar."""
    d = json.loads(JETONLAR.read_text())
    kova: dict[str, list[tuple[str, str]]] = {"kok": [], "gunduz": [], "gece": []}
    atlanan: list[str] = []
    for yol, v in _gez(d):
        ext = (v.get("$extensions") or {}).get("org.meridian.css") or {}
        ad = ext.get("var")
        if not ad:
            continue  # CSS karşılığı olmayan girdi (belge/kayıt) — kusur değil
        # `literal` varsa O yazılır: jetonun CSS'teki GERÇEK yüzü odur (bir başka jetona
        # `var()` ile bağlı olabilir ve o bağ bilgi taşır — çözülmüş hex onu siler).
        ham = ext.get("literal", v["$value"])
        deger = _css_degeri(ham, "/".join(yol))
        if deger is None:
            atlanan.append(f"{'/'.join(yol)} ({type(ham).__name__}: {str(ham)[:40]})")
            continue
        # TEMA İKİ KAYNAKTAN GELİR ve İKİSİ DE OKUNMALI: bazı girdiler `$extensions.tema`
        # taşır, bazıları taşımaz ve tema YOLDAN belli olur (`tema/gunduz/...`). Yalnız
        # birine bakmak ölçüldü ve `--accent`i `:root`ta İKİ KEZ (gündüz + gece değeriyle)
        # üretti — ikincisi birincisini eziyordu, yani gündüz teması gece renklerine düşüyordu.
        # Sessiz bir hataydı: CSS çift bildirimi yutar, son yazan kazanır.
        yol_temasi = "gece" if "gece" in yol else ("gunduz" if "gunduz" in yol else None)
        t = ext.get("tema") or yol_temasi
        kova[t if t in ("gunduz", "gece") else "kok"].append((ad, deger))

    def blok(secici: str, ciftler: list[tuple[str, str]]) -> str:
        if not ciftler:
            return ""
        satirlar = "".join(f"  {ad}: {d};\n" for ad, d in sorted(set(ciftler)))
        return f"{secici} {{\n{satirlar}}}\n"

    css = BASLIK
    css += blok(":root", kova["kok"] + kova["gunduz"])
    # GECE: nitelikle DE, medya sorgusuyla DA — operatörün açık seçimi sistem tercihini yener,
    # seçim yoksa sistem tercihi tohum olur (theme.js sözleşmesi, D5 2026-08-07).
    # TSK-117 (2026-09-03): pano (ui/src) temayı `.dark` sınıfıyla anahtarlar (shadcn); eski yüzeyler
    # `[data-theme="dark"]` ile. İki seçici, TEK blok — değer takımı ayrışamaz (v208 ruhu).
    css += blok('[data-theme="dark"], .dark', kova["gece"])
    # MEDYA BLOĞU PANOYU EZMESİN (v412, 2026-09-04 — operatör vakası: Mac koyu modda gündüz panosunda kartlar
    # siyah). Pano temayı `data-theme="gunduz|gece"` + `.dark` ile damgalar (theme-utils); yalnız `light`i
    # dışlayan seçici `gunduz` kökünde OS koyuyken uygulanıyor ve (0,2,0) özgüllüğüyle tema.css'in `:root`
    # bloğunu eziyordu. İlk düzeltme `:not([data-theme='gunduz'])` de ekledi — ama değer-bazlı dışlama listesi
    # sözlük büyüdükçe yeniden delinir: 2026-09-04 21:0xZ ikinci ölçüm `gece` kökünün AÇIKTA kaldığını
    # gösterdi (gece + OS-koyu'da pano kartı jetonlar #262626 çıkıyor, tema.css `.dark` oklch(0.205) DEĞİL).
    # ARTIK (D1, Rol-1 2026-09-04): seçici NİTELİK-varlığı dışlar. OS tercihi YALNIZ damgasız köke uygulanır;
    # damgalı her kök (gunduz|gece|light|dark|…) temayı KENDİ yönetir — pano geceyi `.dark` sınıfıyla (jetonlar
    # `[data-theme='dark'], .dark` bloğu ÖNCE, tema.css'in KENDİ `.dark` bloğu SONRA yüklenir → tema.css kazanır,
    # v407 hükmüyle tutarlı); eski sayfalar (damgasız) eskisi gibi OS'e uyar.
    gece = blok(":root:not([data-theme])", kova["gece"])
    if gece:
        css += "@media (prefers-color-scheme: dark) {\n" + "\n".join(
            "  " + s for s in gece.splitlines()) + "\n}\n"
    return css, atlanan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kontrol", action="store_true", help="yazma; diskteki dosya güncel mi")
    ap.add_argument("--cikti", type=pathlib.Path, default=VARSAYILAN_CIKTI)
    a = ap.parse_args()

    css, atlanan = uret()
    if atlanan:
        print(f"ATLANAN {len(atlanan)} jeton (şekli tanınmadı — UYDURULMADI):", file=sys.stderr)
        for x in atlanan:
            print(f"  {x}", file=sys.stderr)

    if a.kontrol:
        if not a.cikti.exists():
            print(f"BAYAT: {a.cikti} yok", file=sys.stderr)
            return 1
        if a.cikti.read_text() != css:
            print(f"BAYAT: {a.cikti} tokens.json ile ayrışmış", file=sys.stderr)
            return 1
        print(f"GÜNCEL: {a.cikti}")
        return 0

    a.cikti.parent.mkdir(parents=True, exist_ok=True)
    a.cikti.write_text(css)
    print(f"yazıldı: {a.cikti} ({css.count(chr(10))} satır, "
          f"{css.count('--')} jeton bildirimi)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
