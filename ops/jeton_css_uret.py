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

SAYFA KİPİ (TSK-132 dilim-1, 2026-09-07) — eski yüzeylerin (runbook/landing/workflow.html)
`<style>` içindeki jeton bloğunu da BU dosya üretir:
    python ops/jeton_css_uret.py --sayfa meridian/web/runbook.html            # KURU koşum: diff basar, YAZMAZ
    python ops/jeton_css_uret.py --sayfa meridian/web/runbook.html --uygula   # yaz
    python ops/jeton_css_uret.py --sayfa … --sayfa … --kontrol                # bayat mı (çıkış 1 = bayat)
`--sayfa` tekrarlanabilir. `--uygula` YALNIZ sayfa kipinde anlamlıdır ve sayfasız verilirse
kullanım hatasıdır (çıkış 2) — sessizce yok saymak, operatöre yazdım hissi verip hiçbir şey
yazmamak olurdu (ops aracı vakası 2026-08-30). `--sayfa` ile `--cikti` birlikte verilemez.
İKİ KİP, İKİ BİÇİM — bilerek: `jetonlar.css` seçiciyi boşlukla yazar (`:root {`), sayfa bloğu
boşluksuz (`:root{`), çünkü `tests/test_tasarim_token_v153.py`nin ham-renk linti jeton bloğunu
`":root{"` LİTERALİYLE keser ve boşluklu biçim o kesiciyi düşürür. Fark çivilidir
(`tests/test_jeton_eski_sayfalar_v437.py`).

KAPSAM SINIRI. Bu betik yalnız `tokens.json`ı okur ve YALNIZ jeton bildirimi üretir.
Bileşen kuralı üretmez — o katman rol jetonlarını okur ve bu ayrım sözleşmedir
(index.html'in jeton bloğu: "bileşen kuralları YALNIZ rol jetonu okur").
"""
from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
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


def _kovalar() -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    """tokens.json → ({kok/gunduz/gece: [(ad, css_degeri)…]}, atlananlar).

    İKİ KİP TEK KAYNAKTAN OKUSUN diye ayrı bir fonksiyon: `jetonlar.css` ile eski sayfaların
    bloğu aynı kovaları kullanır. Ayrı iki okuma yazsaydık, tam da bu betiğin ortadan
    kaldırdığı sınıftan (aynı gerçeğin iki kopyası) ikinci bir kopya doğardı."""
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
    return kova, atlanan


def _blok(secici: str, ciftler: list[tuple[str, str]], son: tuple[str, ...] = (),
          bosluk: str = " ") -> str:
    """Bir CSS kuralı. `son` seçiciye ait ama JETON OLMAYAN bildirimler içindir (`color-scheme`);
    `bosluk` seçici ile `{` arasına girer — sayfa kipi onu boşaltır (bkz. modül başlığı)."""
    if not ciftler:
        return ""
    satirlar = "".join(f"  {ad}: {d};\n" for ad, d in sorted(set(ciftler)))
    satirlar += "".join(f"  {s}\n" for s in son)
    return f"{secici}{bosluk}{{\n{satirlar}}}\n"


def uret() -> tuple[str, list[str]]:
    """(css, atlananlar) döndür. Atlananlar SESSİZ DEĞİL — çağıran onları basar."""
    kova, atlanan = _kovalar()
    blok = _blok

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


# ============================ SAYFA KİPİ (TSK-132 dilim-1) ============================
# Eski yüzeyler jeton takımını ELLE KOPYALIYORDU. `tests/test_jeton_birligi_v208.py` kopyaların
# AYRIŞMADIĞINI ölçüyordu ama kopyayı kaldırmıyordu: bir jeton değişikliği DÖRT yerde elle
# yapılmak zorundaydı ve v208 ancak biri unutulduktan SONRA ötüyordu. Artık blok üretiliyor.

SAYFA_ISARET_BAS = "/* JETON-BLOK BAŞI — ÜRETİLMİŞ, ELLE DÜZENLENMEZ (ops/jeton_css_uret.py) */"
SAYFA_ISARET_SON = "/* JETON-BLOK SONU */"
SAYFA_GUNDUZ_SEC = ":root"
SAYFA_GECE_SEC = ':root[data-theme="gece"]'

#: `color-scheme` bir JETON DEĞİL, bir CSS özelliğidir (tokens.json yalnız özel özellik taşır) —
#: ama aynı kuralın içindedir ve üretim onu düşürseydi tarayıcı form kontrollerini/kaydırma
#: çubuklarını yanlış temada çizerdi. Bu yüzden burada, kaynağı BEYANLI bir sabit olarak durur.
SAYFA_SON_BILDIRIMLER = {SAYFA_GUNDUZ_SEC: ("color-scheme: light;",),
                         SAYFA_GECE_SEC: ("color-scheme: dark;",)}

#: ESKİ AD → JETON ROLÜ. Bir sayfa kuralı tokens.json'da KARŞILIĞI OLMAYAN bir ada bağlıysa,
#: üretim o adı düşüremez (kural `var(--yok)` ile tanımsıza düşer). Böyle bir ad buraya
#: gerekçesiyle yazılır ve blok hem takma adı (`--eski: var(--rol);`) hem rol jetonunu taşır.
#:
#: BUGÜN BOŞ — VE BU BİR ÖLÇÜMDÜR, ihmal değil (2026-09-07): üç sayfanın bildirdiği ad kümesi
#: tokens.json ile TAM örtüşüyor (gündüz 129/129 · gece 96/96, fazla ad YOK). Uydurma yasağı:
#: karşılığı olmayan ad OLMADIĞI için tabloya satır yazılmadı. Tablo ölü değildir — aşağıdaki
#: `sayfa_denetimi` onu okur ve eşlenemeyen ad görürse üretimi REDDEDER; mekanizmanın kendisi
#: `tests/test_jeton_eski_sayfalar_v437.py`de sentetik bir sayfayla ısırtılır.
ESKI_AD_ESLEME: dict[str, str] = {}

SAYFA_BASLIK = """/* Kaynak: meridian/web/tokens.json (SSoT) — bu blok ELLE DÜZENLENMEZ.
   Jetonu tokens.json'da değiştir, sonra:
     python ops/jeton_css_uret.py --sayfa <bu dosya> --uygula
   Tazelik kapısı: aynı komut `--kontrol` ile (çıkış 1 = bayat).
   Gerekçe ve ölçüm TEKRARLANMAZ; TEK yerde durur: tokens.json'ın `$description` alanları +
   index.html'in kendi jeton blokları + docs/kontrast-denetimi.md.
   Çiviler: tests/test_jeton_birligi_v208.py (dört yüzey aynı takım) ·
            tests/test_jeton_eski_sayfalar_v437.py (blok == üretici çıktısı).
   GECE bloğu `theme.js`in kurduğu `data-theme` niteliğine bağlıdır; `@media
   (prefers-color-scheme: dark)` BİLEREK YOK — v208 her yüzeyde TAM İKİ `:root` bloğu ölçer ve
   OS tercihi zaten `theme.js` tarafından tohumlanır. */"""

_SAYFA_JETON = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:")
_CSS_YORUM = re.compile(r"/\*.*?\*/", re.S)


def sayfa_blogu() -> tuple[str, list[str]]:
    """(işaretli blok metni, atlananlar). Deterministik ve damgasız — `--kontrol`ün diff
    gürültüsü üretmemesinin şartı budur."""
    kova, atlanan = _kovalar()
    takma_gunduz = [(eski, f"var({rol})") for eski, rol in ESKI_AD_ESLEME.items()]
    metin = (
        SAYFA_ISARET_BAS + "\n" + SAYFA_BASLIK + "\n"
        + _blok(SAYFA_GUNDUZ_SEC, kova["kok"] + kova["gunduz"] + takma_gunduz,
                SAYFA_SON_BILDIRIMLER[SAYFA_GUNDUZ_SEC], bosluk="")
        # TAKMA AD İKİ TEMADA DA BİLDİRİLİR: gece bloğunda eksik kalan bir ad gündüz değerini
        # miras alır ve koyu zeminde açık zeminin rengiyle çizer (`--nav-bg` vakasının sınıfı).
        + _blok(SAYFA_GECE_SEC, kova["gece"] + takma_gunduz,
                SAYFA_SON_BILDIRIMLER[SAYFA_GECE_SEC], bosluk="")
        + SAYFA_ISARET_SON)
    return metin, atlanan


def _sayfa_bolgesi(metin: str) -> tuple[int, int]:
    """Sayfadaki jeton bölgesinin (başlangıç, bitiş) indisleri.

    İKİ HÂL: işaret varsa işaretler arası; YOKSA (ilk taşıma) eski elle-kopya bölge — gündüz
    `:root{`ten gece bloğunun kapanışına kadar. İkinci hâl BİR KEZ geçerlidir ve `--uygula`
    ile işaretleri koyar; sonraki her koşu birinci haldedir."""
    if SAYFA_ISARET_BAS in metin:
        i = metin.index(SAYFA_ISARET_BAS)
        son = metin.find(SAYFA_ISARET_SON, i)
        if son < 0:
            raise ValueError("JETON-BLOK BAŞI var, SONU yok — blok elle kesilmiş olabilir")
        return i, son + len(SAYFA_ISARET_SON)
    try:
        i = metin.index(SAYFA_GUNDUZ_SEC + "{")
        g = metin.index(SAYFA_GECE_SEC + "{", i)
    except ValueError as e:
        raise ValueError(
            "sayfada ne JETON-BLOK işareti ne de `:root{` + `:root[data-theme=\"gece\"]{` "
            "ikilisi var — bu dosya sayfa kipinin tanıdığı bir yüzey değil") from e
    kapanis = metin.find("\n}", g)
    if kapanis < 0:
        raise ValueError("gece bloğu kapanmıyor — CSS bozuk")
    return i, kapanis + 2


def sayfa_denetimi(metin: str) -> list[str]:
    """Mevcut bölgede bildirilen ama tokens.json'da da `ESKI_AD_ESLEME`de de KARŞILIĞI OLMAYAN
    adlar. Boş değilse üretim REDDEDİLİR: o adı okuyan her kural `var(--yok)` ile tanımsıza
    düşerdi ve bu sessiz bir arızadır (uydurma yasağı — eşlenemeyen ad uydurulmaz, sorulur)."""
    kova, _ = _kovalar()
    bilinen = {ad for kutu in kova.values() for ad, _ in kutu} | set(ESKI_AD_ESLEME)
    i, j = _sayfa_bolgesi(metin)
    govde = _CSS_YORUM.sub(" ", metin[i:j])
    return sorted({ad for ad in _SAYFA_JETON.findall(govde) if ad not in bilinen})


def sayfa_uygula(yol: pathlib.Path, blok: str) -> tuple[bool, str]:
    """(zaten_guncel_mi, yeni_metin). Dosyaya YAZMAZ — yazma kararı çağıranındır."""
    metin = yol.read_text(encoding="utf-8")
    i, j = _sayfa_bolgesi(metin)
    yeni = metin[:i] + blok + metin[j:]
    return yeni == metin, yeni


def _sayfa_kipi(sayfalar: list[pathlib.Path], kontrol: bool, uygula: bool) -> int:
    blok, _ = sayfa_blogu()
    bayat = 0
    for p in sayfalar:
        if not p.is_file():
            print(f"YOK: {p}", file=sys.stderr)
            return 2
        eslenemeyen = sayfa_denetimi(p.read_text(encoding="utf-8"))
        if eslenemeyen:
            print(f"REDDEDİLDİ {p}: bölgede tokens.json'da karşılığı OLMAYAN ad(lar) "
                  f"{eslenemeyen} — sessizce düşürülmez. Karşılığını ölç ve "
                  f"ops/jeton_css_uret.py içindeki ESKI_AD_ESLEME'ye gerekçesiyle yaz.",
                  file=sys.stderr)
            return 2
        guncel, yeni = sayfa_uygula(p, blok)
        if guncel:
            print(f"GÜNCEL: {p}")
            continue
        bayat += 1
        if kontrol:
            print(f"BAYAT: {p} tokens.json ile ayrışmış", file=sys.stderr)
        elif uygula:
            p.write_text(yeni, encoding="utf-8")
            print(f"yazıldı: {p}")
        else:
            eski = p.read_text(encoding="utf-8")
            sys.stdout.writelines(difflib.unified_diff(
                eski.splitlines(True), yeni.splitlines(True),
                fromfile=str(p), tofile=f"{p} (üretilmiş)"))
    return 1 if (kontrol and bayat) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kontrol", action="store_true", help="yazma; diskteki dosya güncel mi")
    ap.add_argument("--cikti", type=pathlib.Path, default=None)
    ap.add_argument("--sayfa", type=pathlib.Path, action="append", default=[],
                    help="jeton bloğu üretilecek HTML yüzeyi (tekrarlanabilir)")
    ap.add_argument("--uygula", action="store_true",
                    help="sayfa kipinde YAZ (varsayılan kuru koşum: diff basar)")
    a = ap.parse_args(argv)

    if a.sayfa and a.cikti is not None:
        print("KULLANIM: --sayfa ile --cikti birlikte verilemez (iki hedef, tek üretim)",
              file=sys.stderr)
        return 2
    if a.uygula and not a.sayfa:
        print("KULLANIM: --uygula yalnız --sayfa kipinde anlamlıdır", file=sys.stderr)
        return 2
    if a.sayfa:
        return _sayfa_kipi(a.sayfa, a.kontrol, a.uygula)

    a.cikti = VARSAYILAN_CIKTI if a.cikti is None else a.cikti
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
