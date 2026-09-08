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

SAYFA KİPİ (TSK-132 dilim-1, 2026-09-07) — eski yüzeylerin (workflow.html) `<style>` içindeki
jeton bloğunu da BU dosya üretir:
    python ops/jeton_css_uret.py --sayfa meridian/web/workflow.html            # KURU koşum: diff basar, YAZMAZ
    python ops/jeton_css_uret.py --sayfa meridian/web/workflow.html --uygula   # yaz
    python ops/jeton_css_uret.py --sayfa … --sayfa … --kontrol                # bayat mı (çıkış 1 = bayat)
`--sayfa` tekrarlanabilir. `--uygula` YALNIZ sayfa kipinde anlamlıdır ve sayfasız verilirse
kullanım hatasıdır (çıkış 2) — sessizce yok saymak, operatöre yazdım hissi verip hiçbir şey
yazmamak olurdu (ops aracı vakası 2026-08-30). `--sayfa` ile `--cikti` birlikte verilemez.
`--kontrol --uygula` de birlikte verilemez (çıkış 2): biri SORAR, diğeri YAZAR ve sessiz bir
öncelik kuralı `--uygula`yı yutardı. `--sayfa` bir LİNK sayfasını da (aşağı bkz.) tanır —
öyle bir sayfada blok YOKTUR, `--uygula` onun için bir NO-OP'tur (yazacak bir şey yok, yalnız
doğrular) ve `--kontrol` onu "GÜNCEL (bağlantılı)" der.

DOSYA KİPİ (TSK-132 dilim-2, 2026-09-08) — SAYFA kipi HTML'e bir blok ENJEKTE eder ve bu N
sayfa için N (özdeş) fiziksel kopya demektir; dilim-1 kopyaların AYRIŞMASINI önledi ama
kopyanın kendisini kaldırmadı. DOSYA kipi bunu bitirir: eski sayfalar `<link rel="stylesheet"
href="/jetonlar.css">` ile TEK bir üretilmiş dosyayı okur, hiçbir kopya kalmaz.
    python ops/jeton_css_uret.py --dosya --kontrol   # meridian/web/jetonlar.css bayat mı
    python ops/jeton_css_uret.py --dosya             # yaz (varsayılan --cikti; --uygula GEREKMEZ)
`--dosya`, VARSAYILAN olarak `meridian/web/jetonlar.css`e yazar; `--cikti` ile başka bir hedef
verilebilir. `--dosya` ile `--sayfa` birlikte verilemez (çıkış 2) — iki AYRI üretim kipidir.
`--dosya`nın ürettiği dosya `ui/src/jetonlar.css` (panonun, `uret()`in çıktısı) İLE AYNI DOSYA
DEĞİLDİR: ikisi AYNI ADI taşır ama FARKLI seçici grameri kullanır (aşağıdaki İKİ KİP, İKİ
BİÇİM notunun devamı — `dosya_blogu()`nun kendi docstring'i ayrımı tam anlatır).

SAYFA KİPİNDE ÇIKIŞ 1 İKİ ANLAM TAŞIR ve ayrımı stderr satırı yapar (bulgu 2026-09-08):
`--kontrol` ile 1 = BAYAT (hiçbir şey yazılmadı); `--uygula` ile 1 = KISMİ YAZIM — en az bir
sayfa G/Ç arızasıyla düştü ve stderr'de `UYGULANDI: N/M yazıldı` özeti durur. rc 1'i koşulsuz
"hiçbir şey yazılmadı" diye okuyan bir sarmalayıcı kirli bir ağacı temiz sanırdı.

SAYFA YAZIMI ATOMİKTİR (geçici ad + `os.replace`, `ops/bar_arsivle.py::yaz_ve_dogrula` deseni):
`Path.write_text` dosyayı yazmadan ÖNCE truncate eder, yani gerçek bir G/Ç arızası (disk dolu,
kota) hedefi KESİK bırakır ve "yazılamadı" mesajı 'dosyaya dokunulmadı' diye okunurdu (ölçüldü:
28.688 baytlık runbook.html 20.000 baytta koparıldı). Artık okuyucu ya eski ya yeni dosyayı
görür, yarısını asla.
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
import os
import pathlib
import re
import sys
import tempfile

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


# ============================ DOSYA KİPİ (TSK-132 dilim-2, 2026-09-08) ============================
# SAYFA KİPİ (üstteki) bloğu HTML'İN İÇİNE enjekte eder — dilim-1'in çözümü, ama HÂLÂ N fiziksel
# kopya üretir (N sayfa = N kez AYNI bayt; dilim-1 yalnız kopyaların AYRIŞMASINI önledi, kopyanın
# kendisini kaldırmadı). Dilim-2 kopyayı TAMAMEN kaldırır: sayfalar `<link rel="stylesheet"
# href="/jetonlar.css">` ile TEK bir üretilmiş dosyayı okur.
#
# BU DOSYA `ui/src/jetonlar.css` (`uret()`in çıktısı, panonun/Vite'ın okuduğu) DEĞİLDİR — AYNI ADI
# taşır ama FARKLI SEÇİCİ GRAMERİ üretir, ve bu KASITLI: ÖLÇÜLDÜ (`meridian/web/theme.js`), eski
# sayfalar (index/landing/runbook/workflow) `data-theme="gece"`/`"gunduz"` DAMGALAR; pano
# (`ui/src`, TSK-117) `data-theme="dark"`/`.dark` okur. `uret()`in gece bloğu `[data-theme="dark"],
# .dark` seçicisiyle üretilir — bu seçici `data-theme="gece"` ile HİÇ eşleşmez. Yani eski bir
# sayfayı `ui/src/jetonlar.css`e bağlamak GÜNDÜZ paletini doğru yükler ama GECE bloğunu SESSİZCE
# hiç açmaz (hata yok, yalnız `data-theme="gece"` iken hâlâ gündüz renkleri çizilir) — tam olarak
# `--nav-bg` vakasının (v208) sınıfı, yeni bir kılıkta. `dosya_blogu()` bu yüzden `uret()`i DEĞİL,
# `sayfa_blogu()`nun ZATEN doğru seçici gramerini (`:root` + `:root[data-theme="gece"]`) taşır —
# TEK farkı HTML'e SPLICE edilecek işaretlerin (`SAYFA_ISARET_BAS/SON`) OLMAMASI: bu metin bir
# .html'e enjekte edilmez, kendi başına bağımsız bir .css dosyasıdır. Servis rotası:
# `meridian/api.py::jetonlar_css()` (`/jetonlar.css`, `WEB / "jetonlar.css"`).
DOSYA_BASLIK = """/* ÜRETİLDİ — ELLE DÜZENLEME. Kaynak: meridian/web/tokens.json (SSoT).
   Üreten: `python ops/jeton_css_uret.py --dosya` (yaz) · `--dosya --kontrol` (bayat mı, çıkış
   1 = bayat) · deterministik, damgasız (her koşu aynı bayt).
   Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler; jetonu tokens.json'da değiştir.

   TSK-132 dilim-2 (2026-09-08): eski sayfaların (landing/runbook/…) `<link rel="stylesheet"
   href="/jetonlar.css">` ile yüklediği PAYLAŞILAN dosya — dilim-1'in HTML'e enjekte edilen
   kopyasının (N sayfa = N kopya) yerine geçer: N sayfa artık TEK bu dosyayı, TEK link ile okur.
   `ui/src/jetonlar.css` (pano/Vite, `uret()`) İLE KARIŞTIRILMASIN: AYNI ADI taşır, AYNI
   `_kovalar()`tan (tokens.json) türer, ama FARKLI seçici grameri kullanır — pano
   `data-theme="dark"`/`.dark` okur, bu dosya eski sayfaların `theme.js`inin kurduğu
   `data-theme="gece"`yi (ölçüldü, ops/jeton_css_uret.py modül başlığındaki DOSYA KİPİ notu).
   Yanlış dosyaya link vermek gece temasını SESSİZCE öldürür — hata yok, yalnız hiç açılmaz.
   Çiviler: tests/test_jeton_eski_sayfalar_v437.py (blok == üretici çıktısı, link kipi dahil) ·
            tests/test_jeton_birligi_v208.py (dört yüzey aynı takım). */
"""

VARSAYILAN_DOSYA_CIKTI = KOK / "meridian" / "web" / "jetonlar.css"


def dosya_blogu() -> tuple[str, list[str]]:
    """(css, atlananlar) — `SAYFA_LINK_ETIKETI` ile yüklenen BAĞIMSIZ dosyanın metni.
    `sayfa_blogu()` ile AYNI kovaları (`_kovalar()` ← tokens.json) ve AYNI seçici gramerini
    (`SAYFA_GUNDUZ_SEC`/`SAYFA_GECE_SEC`) kullanır; TEK fark satır-içi enjeksiyon işaretlerinin
    (`SAYFA_ISARET_BAS/SON`) ve `SAYFA_BASLIK`in OLMAMASI — bu metin bir .html'e SPLICE edilmez,
    kendi başına bir .css dosyasıdır ve kendi başlığını (`DOSYA_BASLIK`) taşır."""
    kova, atlanan = _kovalar()
    takma_gunduz = [(eski, f"var({rol})") for eski, rol in ESKI_AD_ESLEME.items()]
    css = (DOSYA_BASLIK
        + _blok(SAYFA_GUNDUZ_SEC, kova["kok"] + kova["gunduz"] + takma_gunduz,
                SAYFA_SON_BILDIRIMLER[SAYFA_GUNDUZ_SEC], bosluk="")
        + _blok(SAYFA_GECE_SEC, kova["gece"] + takma_gunduz,
                SAYFA_SON_BILDIRIMLER[SAYFA_GECE_SEC], bosluk=""))
    return css, atlanan


#: Eski sayfaların DOSYA KİPİNE geçtiğini gösteren kanonik etiket. `_sayfa_kipi` bunu ARAR: bir
#: sayfada `SAYFA_ISARET_BAS` yoksa ama bu etiket VARSA, o sayfa LİNK kipindedir (blok kipi
#: DEĞİL) — `--kontrol`/`--uygula` ona göre davranır (aşağı bkz. `sayfa_baglantili_mi`).
SAYFA_LINK_ETIKETI = '<link rel="stylesheet" href="/jetonlar.css">'

#: `var(--ad)` KULLANIMLARINI bulur — `_SAYFA_JETON` (yukarıda) yalnız BİLDİRİMLERİ (`--ad:`)
#: bulur, bu ise OKUMALARI. Link kipindeki bir sayfanın kendi bloğu YOK; denetlenecek şey artık
#: "bildirilen adlar" değil "kullanılan adlar ⊆ dosyanın bildirdiği adlar" sorusudur.
#:
#: YALNIZ TEK-ARGÜMANLI ÇAĞRI (`var(--ad)`), İKİ-ARGÜMANLI DEĞİL (`var(--ad, yedek)`) — ÖLÇÜLDÜ
#: (2026-09-08): dört yüzeydeki (index/landing/runbook/workflow) HER iki-argümanlı `var()`
#: çağrısı (`--cols`, `--conf`, `--navh`, `--kmc`, `--fill`, `--isaret`) bir JETON değil, satır
#: içi `style="--cols:2"` ile kurulan YERLEŞİM parametresidir — kendi yedeği zaten kendi
#: tanımıdır, `jetonlar.css`e hiç ihtiyaç duymaz (v437'nin de aynı ayrımı yaptığı yer:
#: "gövdedeki `style=\"--cols:2\"` … palet değil yerleşim parametresi"). Tek-argümanlı bir
#: çağrının YEDEĞİ YOKTUR — tanımsızsa tarayıcı sessizce `initial` değere düşer, yani bu ayrım
#: gevşetme değil TAM DA uydurma yasağının aradığı çizgidir.
_VAR_KULLANIM = re.compile(r"var\(\s*(--[a-zA-Z0-9_-]+)\s*\)")


def sayfa_baglantili_mi(metin: str) -> bool:
    """Sayfa İŞARETLİ BLOK yerine kanonik `<link>`i mi taşıyor? İki kip birbirini dışlar — hem
    blok hem link aynı adı iki kaynaktan besler (tek-kaynak yasası ihlali), bu yüzden
    `_sayfa_kipi` önce blok (`SAYFA_ISARET_BAS`) arar, YOKSA link arar."""
    return SAYFA_ISARET_BAS not in metin and SAYFA_LINK_ETIKETI in metin


def sayfa_cakismasi_mi(metin: str) -> bool:
    """Hem İŞARETLİ BLOK hem kanonik `<link>` AYNI ANDA var mı? Bu, tek-kaynak yasasının en
    sessiz ihlal biçimidir: blok TAZE olsa (sayfa_blogu() ile bayt-eşit) bile, linkin VARLIĞI
    ikinci bir kaynağın orada durduğunu gösterir — biri güncellenir, öteki fark edilmeden kalır.
    `_sayfa_kipi` bunu blok/link ayrımından ÖNCE arar ve REDDEDER (`sayfa_baglantili_mi` blok
    varsa link'i hiç GÖRMEZ, yani bu çakışmayı KENDİ BAŞINA yakalayamaz — ayrı bir kapı gerekir)."""
    return SAYFA_ISARET_BAS in metin and SAYFA_LINK_ETIKETI in metin


def baglanti_denetimi(metin: str) -> list[str]:
    """Link kipindeki bir sayfa için hata listesi (boş = temiz) — `sayfa_denetimi`nin link kipi
    karşılığı. Sayfanın KULLANDIĞI (`var(--x)`) her ad, `dosya_blogu()`nun (yani `_kovalar()`ın,
    yani tokens.json'ın) bildirdiği kümenin ALT KÜMESİ olmalı — aksi hâlde tanımsız değere düşer
    (uydurma yasağı, `sayfa_denetimi` ile AYNI ilke, blok yerine link için)."""
    kova, _ = _kovalar()
    bilinen = {ad for kutu in kova.values() for ad, _ in kutu} | set(ESKI_AD_ESLEME)
    govde = _CSS_YORUM.sub(" ", metin)
    kullanilan = {ad for ad in _VAR_KULLANIM.findall(govde)}
    eslenemeyen = sorted(kullanilan - bilinen)
    if not eslenemeyen:
        return []
    return [f"jetonlar.css'te tanımı OLMAYAN değişken kullanımı: {eslenemeyen}"]


def _atlanan_bas(atlanan: list[str]) -> None:
    """Atlanan jetonları stderr'e basar — HER İKİ kip (klasik `uret()` yolu ve sayfa kipi) AYNI
    uyarıyı basar (bulgu C4b, 2026-09-08): eskiden yalnız klasik yol basıyordu, sayfa kipi
    `_kovalar()`'ın döndürdüğü `atlanan` listesini sessizce atıyordu — `--sayfa … --uygula`
    tanınmayan şekle sahip bir jetonu üç sayfanın bloğundan da EKSİK yazardı ve operatöre hiçbir
    uyarı gitmezdi (Yasa 6 / uydurma yasağı ihlali: tek belirti sonradan CSS'te tanımsız kalan
    `var(--jeton)` olurdu)."""
    if not atlanan:
        return
    print(f"ATLANAN {len(atlanan)} jeton (şekli tanınmadı — UYDURULMADI):", file=sys.stderr)
    for x in atlanan:
        print(f"  {x}", file=sys.stderr)


def _atomik_yaz(yol: pathlib.Path, metin: str) -> None:
    """Aynı dizinde geçici ada yaz → `os.replace` ile yerine koy. Arızada hedefe DOKUNULMAZ ve
    geçici dosya SİLİNİR.

    KOPYA MI? `meridian.store._atomic_write` bu deseni ZATEN taşıyor ve `ops/bar_arsivle.py` onu
    İTHAL ediyor. Burada ithal edilmedi ve gerekçe ÖLÇÜLDÜ: bu araç pytest DIŞINDA, elle ve
    `ui/package.json` üzerinden koşar; `meridian.store` `meridian.config`/`meridian.storage`
    zincirini (ve `meridian.obs`ı) sürece sokar, yani her jeton üretimi canlı yerel deftere satır
    düşürebilirdi (CLAUDE.md §2, 3 vaka 2026-08-30). Sözleşme tek satırdır ve davranışsal olarak
    çivilidir (v446 K2); ayrışma riski, motor paketini bir CSS üreticisine bağlama bedelinden
    KÜÇÜKTÜR."""
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=str(yol.parent), prefix=f".{yol.name}-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(metin)
            f.flush()
            os.fsync(f.fileno())
        os.replace(gecici, yol)
    except BaseException:
        if os.path.exists(gecici):
            try:
                os.unlink(gecici)
            except OSError:  # sessiz-yutma: temizlik EN İYİ ÇABAdır, asıl istisna yukarı fırlatılmaya devam ediyor ve hüküm onundur
                pass
        raise


def _sayfa_kipi(sayfalar: list[pathlib.Path], kontrol: bool, uygula: bool) -> int:
    blok, atlanan = sayfa_blogu()
    _atlanan_bas(atlanan)

    # ÖN DOĞRULAMA — TÜMÜ ÖNCE, YAZMA SONRA (bulgu C4c, 2026-09-08). Doğrulama (dosya var mı,
    # `sayfa_denetimi`de eşlenemeyen ad var mı) sayfaların TAMAMI için burada biter; yazma pasosu
    # ancak HİÇBİRİ reddedilmeden başlar. Aksi hâlde N. sayfadaki bir doğrulama arızası (yazım
    # hatalı yol, eşlenemeyen ad) 1..N-1 sayfaları ZATEN diske yazılmış bir anda komutu durdurur
    # ve hiçbir stderr satırı bunu söylemezdi — operatör exit kodunu "hiçbir şey yazılmadı" diye
    # okuyup CLAUDE.md §9'daki "temiz ağaç" varsayımıyla devam edebilirdi.
    #
    # SINIFLANDIRMA (TSK-132 dilim-2): burada AYRICA her sayfanın BLOK mu LİNK mi olduğuna karar
    # verilir. `kip[p] == "link"` sayfalar yazma pasosunda ATLANIR (aşağıda) — onların "kaynağı"
    # bu sayfa DEĞİL, paylaşılan `jetonlar.css`dir (`--dosya` ile üretilir/denetlenir).
    kip: dict[pathlib.Path, str] = {}
    for p in sayfalar:
        if not p.is_file():
            print(f"YOK: {p}", file=sys.stderr)
            return 2
        metin = p.read_text(encoding="utf-8")
        if sayfa_cakismasi_mi(metin):
            print(f"REDDEDİLDİ {p}: HEM işaretli blok HEM kanonik <link> var — iki kaynak "
                  "aynı jetonu besliyor (tek-kaynak yasası ihlali), blok TAZE olsa bile. "
                  "Bloğu kaldır (link kipine geçmiş demektir) ya da linki kaldır (hâlâ blok "
                  "kipindeyse).", file=sys.stderr)
            return 2
        if sayfa_baglantili_mi(metin):
            hatalar = baglanti_denetimi(metin)
            if hatalar:
                print(f"REDDEDİLDİ {p}: " + "; ".join(hatalar), file=sys.stderr)
                return 2
            kip[p] = "link"
            continue
        try:
            eslenemeyen = sayfa_denetimi(metin)
        except ValueError as e:
            # NE BLOK NE LİNK: `sayfa_denetimi` → `_sayfa_bolgesi` burada ValueError fırlatır
            # (ör. bir sayfadan kanonik `<link>` SİLİNDİYSE, artık ne işaretli blok ne eski
            # elle-kopya `:root{`/`:root[data-theme="gece"]{` ikilisi kalır). Yakalanmazsa bu
            # istisna `main()`i UÇURUR — operatöre çıplak bir traceback, "REDDEDİLDİ" DEĞİL.
            # Diğer red dallarıyla AYNI dilde konuşsun diye burada da rc 2 + stderr satırı.
            print(f"REDDEDİLDİ {p}: {e}", file=sys.stderr)
            return 2
        if eslenemeyen:
            print(f"REDDEDİLDİ {p}: bölgede tokens.json'da karşılığı OLMAYAN ad(lar) "
                  f"{eslenemeyen} — sessizce düşürülmez. Karşılığını ölç ve "
                  f"ops/jeton_css_uret.py içindeki ESKI_AD_ESLEME'ye gerekçesiyle yaz.",
                  file=sys.stderr)
            return 2
        kip[p] = "blok"

    bayat = 0
    yazilan = 0
    yazilamayan = 0
    for p in sayfalar:
        if kip[p] == "link":
            # LİNK KİPİ: bu sayfanın kendi bloğu yok, yazacak bir şey yok — `baglanti_denetimi`
            # yukarıda zaten temiz bulduğu için burada yalnız raporlanır. `--uygula` onun için
            # bir NO-OP'tur (CLAUDE.md'nin "sessizce yok sayma" yasağı burada İHLAL EDİLMEZ:
            # rapor satırı "bağlantılı" der, "yazıldı" demez — hangi dalda olduğu açık).
            print(f"GÜNCEL (bağlantılı): {p}")
            continue
        guncel, yeni = sayfa_uygula(p, blok)
        if guncel:
            print(f"GÜNCEL: {p}")
            continue
        bayat += 1
        if kontrol:
            print(f"BAYAT: {p} tokens.json ile ayrışmış", file=sys.stderr)
        elif uygula:
            try:
                _atomik_yaz(p, yeni)
            except OSError as e:
                # KISMİ YAZIM GÖRÜNÜR OLSUN (bulgu C4c): ön doğrulama TÜMÜNÜ geçse bile gerçek
                # bir G/Ç arızası (disk dolu, izin reddi) tek bir sayfada olabilir — o zaman
                # DİĞER sayfalar atlanmaz, her sayfa BAĞIMSIZ denenir ve durumu AYRI basılır.
                # "yazılamadı" ARTIK 'dosyaya DOKUNULMADI' demektir (K2, atomik yazım): eski
                # `write_text` gövdesinde aynı mesaj kesilmiş bir dosyanın üstünü örtüyordu.
                print(f"HATA {p}: yazılamadı (dosyaya DOKUNULMADI) — {type(e).__name__}: {e}",
                      file=sys.stderr)
                yazilamayan += 1
                continue
            print(f"yazıldı: {p}")
            yazilan += 1
        else:
            eski = p.read_text(encoding="utf-8")
            sys.stdout.writelines(difflib.unified_diff(
                eski.splitlines(True), yeni.splitlines(True),
                fromfile=str(p), tofile=f"{p} (üretilmiş)"))

    if uygula and yazilamayan:
        print(f"UYGULANDI: {yazilan}/{bayat} yazıldı — {yazilamayan} sayfa HATA verdi "
              "(yukarıda); kısmi yazım SESSİZ değildir.", file=sys.stderr)
        return 1
    return 1 if (kontrol and bayat) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kontrol", action="store_true", help="yazma; diskteki dosya güncel mi")
    ap.add_argument("--cikti", type=pathlib.Path, default=None)
    ap.add_argument("--sayfa", type=pathlib.Path, action="append", default=[],
                    help="jeton bloğu üretilecek HTML yüzeyi (tekrarlanabilir)")
    ap.add_argument("--uygula", action="store_true",
                    help="sayfa kipinde YAZ (varsayılan kuru koşum: diff basar)")
    ap.add_argument("--dosya", action="store_true",
                    help="pano'nun (`ui/src/jetonlar.css`, `uret()`) DEĞİL, eski sayfaların "
                         "`<link>` ile yüklediği bağımsız dosyayı (`dosya_blogu()`) üret/denetle "
                         f"— varsayılan çıktı: {VARSAYILAN_DOSYA_CIKTI}")
    a = ap.parse_args(argv)

    if a.sayfa and a.dosya:
        print("KULLANIM: --sayfa ile --dosya birlikte verilemez (iki AYRI üretim kipi: biri "
              "HTML'e enjekte eder, öteki bağımsız bir dosya üretir)", file=sys.stderr)
        return 2
    if a.sayfa and a.cikti is not None:
        print("KULLANIM: --sayfa ile --cikti birlikte verilemez (iki hedef, tek üretim)",
              file=sys.stderr)
        return 2
    if a.kontrol and a.uygula:
        # ÇAKIŞAN BAYRAK KOMBİNASYONU AÇIKÇA REDDEDİLİR (bulgu C4a, 2026-09-08): eskiden ikisi
        # birlikte verilince argparse'ta çakışma tanımı OLMADIĞI için `_sayfa_kipi` sessizce
        # yalnız `--kontrol` dalına girip YAZMIYORDU — operatöre `--uygula`nın yok sayıldığına
        # dair hiçbir uyarı gitmezdi (2026-08-30 vakasıyla AYNI sınıf: "sessizce yok sayılan
        # bayrak"). Diğer çakışan kombinasyonlarla (--sayfa+--cikti, --uygula sayfasız) TUTARLI
        # olsun diye bu da KULLANIM hatasıdır (çıkış 2), sessiz bir öncelik kuralı DEĞİL.
        print("KULLANIM: --kontrol ile --uygula birlikte verilemez (biri SORAR, diğeri YAZAR — "
              "sessizce biri diğerini geçersiz kılmaz)", file=sys.stderr)
        return 2
    if a.uygula and not a.sayfa:
        print("KULLANIM: --uygula yalnız --sayfa kipinde anlamlıdır", file=sys.stderr)
        return 2
    if a.sayfa:
        return _sayfa_kipi(a.sayfa, a.kontrol, a.uygula)

    if a.dosya:
        a.cikti = VARSAYILAN_DOSYA_CIKTI if a.cikti is None else a.cikti
        css, atlanan = dosya_blogu()
    else:
        a.cikti = VARSAYILAN_CIKTI if a.cikti is None else a.cikti
        css, atlanan = uret()
    _atlanan_bas(atlanan)

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
