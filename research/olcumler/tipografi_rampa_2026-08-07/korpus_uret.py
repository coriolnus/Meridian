#!/usr/bin/env python3
"""D6 tip-rampası turunun ÜÇ girdi artefaktını `docs/RUNBOOK.md`den yeniden üretir.

NEDEN VAR (EDG-016 dersi, MERIDIAN_ENGINEERING_LOG): "measured" statüsü kanıt + damga +
KOD üçlüsü depoya girince tamamdır — damga kodsuz yaşayamaz. Bu turun ölçüm harness'ları
(`olcum.html`, `baslik_olcum.html`) depodaydı ama onları BESLEYEN korpus çıkarımı ilk
koşumda satır-içi heredoc'tu, yani scratchpad'le birlikte ölürdü. O gün
`ornek_metin.json`in 151 bloğu "nereden geldiği gösterilemeyen bir kanıt"a dönerdi.

ÜRETTİĞİ ÜÇ DOSYA (üçü de bu dizinde, üçü de commit'li):
  ornek_metin.json        · CPL/x-yüksekliği koşumunun korpusu — 151 gövde-ölçüsü blok
  baslik_ornegi.json      · başlık merdiveni koşumunun gerçek h1/h2/gövde kesiti
  en_dar_h1_araligi.html  · belgedeki EN DAR h1→h1 aralığı (28px Display meşruiyet ölçümü)

KULLANIM
  python research/olcumler/tipografi_rampa_2026-08-07/korpus_uret.py            # üret
  python research/olcumler/tipografi_rampa_2026-08-07/korpus_uret.py --kontrol  # SHA-256 karşılaştır

`--kontrol` HİÇBİR ŞEY YAZMAZ: yeniden üretir, diskteki commit'li hâlle SHA-256 karşılaştırır,
ayrışma varsa exit 1. Bu, `ops/runbook_uret.py --kontrol` ile aynı idiomdur.

UYARI — BU BETİK KAYNAĞA BAĞLIDIR. `docs/RUNBOOK.md` üretilmiş bir dosyadır ve değişir;
o değiştiğinde bu betik FARKLI bir korpus üretir ve `--kontrol` düşer. Bu bir arıza DEĞİL,
tam olarak istenen davranıştır: DESIGN.md'deki sayılar 2026-08-07'deki belgeye aittir ve
belge değiştiyse sayılar yeniden ölçülmelidir. Düşen kontrol "ölçümü tazele" demektir,
"betiği düzelt" demek değildir.
"""
from __future__ import annotations

import argparse
import hashlib
import html as H
import json
import re
import sys
from pathlib import Path

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[2]
KAYNAK = KOK / "docs" / "RUNBOOK.md"

# Ölçüm koşumundaki eşikler — DEĞİŞTİRİLEMEZ. Bunlar ON_KAYIT.md'nin donmuş kararının
# parçasıdır: korpusun neyi içerdiğini sonradan oynatmak, ölçümü sonradan seçmektir.
ASGARI_BLOK_UZUNLUGU = 120        # karakter — altındakiler satır-uzunluğu ölçmez, gürültü katar
BASLIK_ORNEGI_GOVDE_SAYISI = 3
EN_DAR_ARALIK_DILIMI = (0, 46)    # ölçüldü: h1'ler 0·44·285·620·702·980·1087 → en dar ikili 0→44


def _kaynak() -> list[str]:
    if not KAYNAK.exists():
        sys.exit(f"KAYNAK YOK: {KAYNAK} — üret: python ops/runbook_uret.py")
    return KAYNAK.read_text(encoding="utf-8").split("\n")


def _capa_sil(s: str) -> str:
    """`{#capa}` son ekini at — okuyucuya görünmeyen bir şey ölçüme girmemeli."""
    return re.sub(r"\s*\{#[^}]*\}", "", s).strip()


# ---------------------------------------------------------------- 1 · CPL korpusu
def korpus() -> list[str]:
    """Gövde ÖLÇÜSÜNDE çizilen her blok: paragraflar + liste maddeleri.

    Liste maddeleri KORPUSA DAHİLDİR ve bu bilinçlidir — kaynakta 314 liste satırı var,
    yani bu belgenin baskın gövde biçimi listedir. Yalnız paragraf ölçmek, sayfanın
    çoğunluğunu ölçmemek olurdu. Başlık/tablo/kod bloğu HARİÇ: onlar gövde ölçüsünde
    çizilmiyor ve satır uzunluğu sorusuna cevap vermiyorlar.
    """
    ham = "\n".join(_kaynak())
    ham = re.sub(r"```.*?```", "\x00FENCE\x00", ham, flags=re.S)   # kod bloklarını tek işarete indir

    bloklar: list[str] = []
    tampon: list[str] = []

    def bosalt() -> None:
        if tampon:
            bloklar.append(" ".join(tampon))
            tampon.clear()

    for satir in ham.split("\n"):
        s = satir.strip()
        if not s or s.startswith(("#", ">", "|", "<")) or "\x00FENCE\x00" in s:
            bosalt()
            continue
        if re.match(r"^\s*[-*]\s|^\s*\d+\.\s", satir):
            bosalt()
            bloklar.append(_capa_sil(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", satir)))
            continue
        tampon.append(_capa_sil(s))
    bosalt()
    return [b for b in bloklar if len(b) >= ASGARI_BLOK_UZUNLUGU]


# ------------------------------------------------------- 2 · başlık merdiveni kesiti
def baslik_ornegi() -> dict:
    """Merdiven koşumu SENTETİK metinle çalışmaz: gerçek bir h1, gerçek bir h2, ve
    gerçek bir "tamamı kod" h2 (`h2 code` kuralının sınandığı vaka) alınır."""
    satirlar = _kaynak()
    i = next(k for k, l in enumerate(satirlar) if l.startswith("## HEARTBEAT_STALE"))
    j = next(k for k, l in enumerate(satirlar) if l.startswith("# Alarmlar"))

    govde: list[str] = []
    for l in satirlar[i + 1:i + 14]:
        s = l.strip()
        if s and not s.startswith(("#", "|", "```")):
            govde.append(re.sub(r"^\s*[-*]\s+", "", s))
        if len(govde) >= BASLIK_ORNEGI_GOVDE_SAYISI:
            break

    return {
        "h1": _capa_sil(satirlar[j][2:]),
        "h2a": _capa_sil(satirlar[i][3:]),
        "h2b": "`ops/kapilar.sh`",     # kaynaktaki 15 "tamamı kod" başlığından biri
        "govde": govde,
    }


# ------------------------------------------------- 3 · en dar h1→h1 aralığı (HTML)
def _satir_ici(s: str) -> str:
    s = H.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def en_dar_h1_araligi() -> str:
    """28px Display meşruiyet ölçümünün girdisi.

    DESIGN.md 28px'i "görünüm başına bir tane" diye ayırır. Kural yalnız EN DAR h1 ikilisi
    üzerinden çürütülebilir — geri kalan beş aralık daha genişse zaten sorun değildir.
    Bu yüzden dilim sabit ve dar seçilmiştir; ölçüm 1189px verdi (ekran 1112px).
    """
    bas, son = EN_DAR_ARALIK_DILIMI
    dilim = _kaynak()[bas:son]

    out: list[str] = []
    tampon: list[str] = []
    liste = alinti = False

    def bosalt() -> None:
        if tampon:
            out.append("<p>" + _satir_ici(" ".join(tampon)) + "</p>")
            tampon.clear()

    for l in dilim:
        s = l.strip()
        if not s:
            bosalt()
            if liste:
                out.append("</ul>")
                liste = False
            if alinti:
                out.append("</blockquote>")
                alinti = False
            continue
        if s.startswith("# "):
            bosalt()
            out.append("<h1>" + _satir_ici(_capa_sil(s[2:])) + "</h1>")
            continue
        if s.startswith("## "):
            bosalt()
            out.append("<h2>" + _satir_ici(_capa_sil(s[3:])) + "</h2>")
            continue
        if s.startswith(">"):
            bosalt()
            if not alinti:
                out.append("<blockquote>")
                alinti = True
            out.append("<p>" + _satir_ici(s.lstrip("> ")) + "</p>")
            continue
        if re.match(r"^[-*]\s", s):
            bosalt()
            if not liste:
                out.append("<ul>")
                liste = True
            out.append("<li>" + _satir_ici(s[2:]) + "</li>")
            continue
        tampon.append(s)
    bosalt()
    if liste:
        out.append("</ul>")
    if alinti:
        out.append("</blockquote>")
    return "\n".join(out)


# ------------------------------------------------------------------------ koşum
def uretilenler() -> dict[str, str]:
    return {
        "ornek_metin.json": json.dumps(korpus(), ensure_ascii=False, indent=1),
        "baslik_ornegi.json": json.dumps(baslik_ornegi(), ensure_ascii=False, indent=1),
        "en_dar_h1_araligi.html": en_dar_h1_araligi(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kontrol", action="store_true",
                    help="yazma; diskteki commit'li hâlle SHA-256 karşılaştır")
    a = ap.parse_args()

    kotu = 0
    for ad, icerik in uretilenler().items():
        hedef = BURASI / ad
        yeni = hashlib.sha256(icerik.encode("utf-8")).hexdigest()
        if a.kontrol:
            if not hedef.exists():
                print(f"YOK      {ad}")
                kotu += 1
                continue
            eski = hashlib.sha256(hedef.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            durum = "BİREBİR" if eski == yeni else "AYRIŞTI"
            print(f"{durum:8} {ad}  {yeni[:16]}")
            kotu += eski != yeni
        else:
            hedef.write_text(icerik, encoding="utf-8")
            print(f"yazıldı  {ad}  {yeni[:16]}")

    if a.kontrol and kotu:
        print(f"\n{kotu} dosya ayrıştı — `docs/RUNBOOK.md` değişmiş olabilir. Bu durumda "
              "DESIGN.md'nin D6 sayıları O BELGEYE aittir ve ölçüm YENİDEN koşulmalıdır.")
        return 1
    if a.kontrol:
        print("\nüç artefakt da commit'li hâlleriyle birebir — D6 kanıt zinciri sağlam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
