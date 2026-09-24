#!/usr/bin/env python3
"""ops/roadmap_cephe_ozeti.py — ROADMAP §3 CEPHE ÖZETİ ÜRETİCİSİ (TSK-216, 2026-09-24).

NE: `ROADMAP.md`deki AÇIK TSK kalemlerini (DONE/DROPPED dışı) cephelerine (`PRG-NN`) göre sayar
ve §3'teki işaretli bloğa bir tablo yazar. Tablo ELLE DÜZENLENMEZ — tek kaynak kalemlerin kendisidir.

NEDEN: 2026-09-24 ölçümü — açık 55 TSK'nın 43'ünde cephe bağı yoktu; §3 özet tablosu 2026-08-13'ten
beri elle tutuluyordu ve bayattı (PRG-02 "kapalı" görünürken açık bir koruma boşluğu, TSK-205,
taşıyordu). Cephe katmanı ancak kalemlerden TÜRETİLİRSE bayatlamaz (tek-kaynak yasası); elle tutulan
bir sayım, kalemler değiştikçe sessizce ayrışır.

KALEM BİÇİMLERİ — iki yüzey, ikisi de sayılır:
  1. Başlık biçimi (§0 · §2 · §3 · §4 · §5): `- **[TSK-NNN] Ad** — status: X · …`. Cephesi, kalemin
     alan satırları (iki boşlukla girintili) içindeki İLK `  Ref:` satırının BAŞINDAKİ `PRG-NN`
     jetonudur: `  Ref: PRG-06 · …`. Ref'in ortasında geçen bir PRG anıştırması cephe SAYILMAZ —
     bağ açık beyandır, metinden tahmin edilmez.
  2. §2 TAHTA tablo satırı: `| TSK-NNN | … (WP: WPn) | … | DURUM(…) |`. Cephesi `WPn` → `PRG-0n`
     (2026-08-13 yeniden numaralamasında WP1..WP12 cephe numaralarıyla birebir). `(bkz. …)` satırları
     başka bir kalemin kaydıdır, sayılmaz.
§1 (hat) · §6 (kart endeksi — TSK taşımaz) · §7 (günlük) · §8 (arşiv) · §∞ (eşleme) TARANMAZ.

KULLANIM (depo kökünden):
    python ops/roadmap_cephe_ozeti.py               # tabloyu stdout'a bas
    python ops/roadmap_cephe_ozeti.py --yaz         # ROADMAP.md'deki bloğu yeniden üret
    python ops/roadmap_cephe_ozeti.py --denetle     # yazma; blok bayatsa ya da cephesiz kalem varsa çıkış 1
    python ops/roadmap_cephe_ozeti.py --dosya <yol> # başka bir ROADMAP (çiviler bunu kullanır)

OKUYAN: `tests/test_roadmap_cephe_ozeti_v535.py` (ayrışma + cephe bağı çivileri) ve ROADMAP §3'ü
okuyan operatör. Yalnız stdlib — `meridian` import ETMEZ, yani pytest dışında koşmak canlı ya da
yerel deftere dokunmaz.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

KOK = pathlib.Path(__file__).resolve().parents[1]
VARSAYILAN_YOL = KOK / "ROADMAP.md"

BOLUM_DESENI = re.compile(r"^## §(\S+)")
TARANAN_BOLUMLER = frozenset({"0", "2", "3", "4", "5"})
BASLIK_DESENI = re.compile(r"^- \*\*\[(TSK-\d+)\] (.*?)\*\* — status: ([A-Z_]+)")
REF_PRG_DESENI = re.compile(r"^  Ref: (PRG-\d{2})\b")
TAHTA_DESENI = re.compile(r"^\| *\*{0,2}(TSK-\d+)\*{0,2} *\|")
WP_DESENI = re.compile(r"\(WP: ?WP(\d+)\)")
DURUM_DESENI = re.compile(r"^\**(ACTIVE|QUEUED|GATED|OPERATOR|INTERIM|DONE|DROPPED)\b")
PRG_BASLIK_DESENI = re.compile(r"^### (PRG-\d+) — (.+)$")

KAPALI_DURUMLAR = frozenset({"DONE", "DROPPED"})
#: Tablo sütunları — v351'in açık durum sözlüğü (çıplak ACTIVE/QUEUED/INTERIM/OPERATOR + GATED).
ACIK_DURUMLAR = ("ACTIVE", "QUEUED", "GATED", "OPERATOR", "INTERIM")
#: Cephe adı, başlıktaki ilk rozetten ya da not parantezinden önce biter.
AD_KESICILER = (" 🔴", " 🔶", " 🟡", " 🟢", " 📋", " 🆕", " _(", " **[")

BLOK_BASLA = "<!-- CEPHE-OZETI:BASLA -->"
BLOK_BITIR = "<!-- CEPHE-OZETI:BITIR -->"


def _bolum_etiketleri(satirlar: list[str]) -> list[str | None]:
    """Her satırın içinde bulunduğu `## §X` bölüm anahtarı (başlıktan önceki satırlar için None)."""
    etiket: str | None = None
    sonuc: list[str | None] = []
    for s in satirlar:
        m = BOLUM_DESENI.match(s)
        if m:
            etiket = m.group(1)
        sonuc.append(etiket)
    return sonuc


def cephe_adlari(metin: str) -> dict[str, str]:
    """`### PRG-NN — Ad …` başlıklarından {kimlik: kısa ad}. Ad ilk rozette/nottan önce kesilir."""
    adlar: dict[str, str] = {}
    for s in metin.splitlines():
        m = PRG_BASLIK_DESENI.match(s)
        if not m:
            continue
        ad = m.group(2)
        kesim = min((ad.find(k) for k in AD_KESICILER if k in ad), default=len(ad))
        adlar[m.group(1)] = ad[:kesim].strip()
    return adlar


def acik_kalemler(metin: str) -> list[dict]:
    """Taranan bölümlerdeki AÇIK TSK kalemleri, dosya sırasıyla.

    Her kayıt: `tsk` · `durum` · `cephe` (PRG-NN ya da None) · `yuzey` ("baslik" | "tahta") · `satir`
    (1-tabanlı). Aynı kimlik iki kez geçerse İLKİ sayılır — başlık biçimli kalem yaşayan tektir,
    tahtadaki ikinci satır ancak `(bkz. …)` kaydı olabilir ve zaten elenir."""
    satirlar = metin.splitlines()
    bolumler = _bolum_etiketleri(satirlar)
    kalemler: list[dict] = []
    gorulen: set[str] = set()
    for i, s in enumerate(satirlar):
        bolum = bolumler[i]
        if bolum not in TARANAN_BOLUMLER:
            continue
        m = BASLIK_DESENI.match(s)
        if m:
            tsk, durum = m.group(1), m.group(3)
            if tsk in gorulen or durum in KAPALI_DURUMLAR:
                gorulen.add(tsk)
                continue
            cephe = None
            j = i + 1
            while j < len(satirlar) and satirlar[j].startswith("  "):
                r = REF_PRG_DESENI.match(satirlar[j])
                if satirlar[j].startswith("  Ref:"):
                    cephe = r.group(1) if r else None
                    break
                j += 1
            kalemler.append({"tsk": tsk, "durum": durum, "cephe": cephe, "yuzey": "baslik", "satir": i + 1})
            gorulen.add(tsk)
            continue
        if bolum != "2":
            continue
        m = TAHTA_DESENI.match(s)
        if not m or "(bkz." in s:
            continue
        tsk = m.group(1)
        if tsk in gorulen:
            continue
        hucreler = [h.strip() for h in s.strip().strip("|").split("|")]
        durum = next((DURUM_DESENI.match(h).group(1) for h in hucreler[1:] if DURUM_DESENI.match(h)), None)
        if durum is None or durum in KAPALI_DURUMLAR:
            gorulen.add(tsk)
            continue
        w = WP_DESENI.search(s)
        cephe = f"PRG-{int(w.group(1)):02d}" if w else None
        kalemler.append({"tsk": tsk, "durum": durum, "cephe": cephe, "yuzey": "tahta", "satir": i + 1})
        gorulen.add(tsk)
    return kalemler


def ihlaller(metin: str) -> list[str]:
    """Cephesiz ya da tanımsız cepheye bağlı açık kalemler — boş liste = her açık kalem bağlı."""
    adlar = cephe_adlari(metin)
    sonuc: list[str] = []
    for k in acik_kalemler(metin):
        if k["cephe"] is None:
            ipucu = ("`  Ref:` satırı `PRG-NN ·` ile başlamalı" if k["yuzey"] == "baslik"
                     else "tahta satırı `(WP: WPn)` etiketi taşımalı")
            sonuc.append(f"{k['tsk']} (satır {k['satir']}): cephe bağı yok — {ipucu}")
        elif k["cephe"] not in adlar:
            sonuc.append(f"{k['tsk']} (satır {k['satir']}): {k['cephe']} tanımlı bir `### PRG-NN — Ad` başlığı değil")
    return sonuc


def ozet_tablosu(metin: str) -> str:
    """Cephe başına açık kalem sayımı (markdown). Kalemsiz cepheler de satır alır (0 bir bilgidir)."""
    adlar = cephe_adlari(metin)
    kalemler = acik_kalemler(metin)
    satirlar = [
        "_Üretildi: `python ops/roadmap_cephe_ozeti.py --yaz` · kaynak: açık TSK kalemleri "
        "(başlık `Ref: PRG-NN ·` + tahta `(WP: WPn)`) · ELLE DÜZENLENMEZ (çivi: v535)._",
        "",
        "| Cephe | Açık | " + " | ".join(ACIK_DURUMLAR) + " | Kalemler |",
        "|---|---:|" + "---:|" * len(ACIK_DURUMLAR) + "---|",
    ]

    def _satir(etiket: str, grup: list[dict]) -> str:
        sayim = [sum(1 for k in grup if k["durum"] == d) for d in ACIK_DURUMLAR]
        liste = " · ".join(k["tsk"] for k in sorted(grup, key=lambda k: int(k["tsk"][4:]))) or "—"
        return f"| {etiket} | {len(grup)} | " + " | ".join(str(n) for n in sayim) + f" | {liste} |"

    for kimlik in sorted(adlar, key=lambda k: int(k[4:])):
        satirlar.append(_satir(f"{kimlik} {adlar[kimlik]}", [k for k in kalemler if k["cephe"] == kimlik]))
    bagsiz = [k for k in kalemler if k["cephe"] not in adlar]
    if bagsiz:
        satirlar.append(_satir("_cephesiz / tanımsız cephe_", bagsiz))
    satirlar.append(_satir("**Toplam**", kalemler).rsplit(" | ", 1)[0] + " | — |")
    return "\n".join(satirlar)


def blok_icerigi(metin: str) -> str | None:
    """ROADMAP'teki işaretli bloğun içeriği (işaretler hariç, baş/son boş satırlar kırpılmış)."""
    if BLOK_BASLA not in metin or BLOK_BITIR not in metin:
        return None
    a = metin.index(BLOK_BASLA) + len(BLOK_BASLA)
    b = metin.index(BLOK_BITIR)
    return metin[a:b].strip("\n")


def blogu_yaz(metin: str) -> str:
    """Bloğu yeniden üretilmiş tabloyla değiştirilmiş metin döndürür (işaretler yoksa ValueError)."""
    if blok_icerigi(metin) is None:
        raise ValueError(f"ROADMAP'te blok işaretleri yok: {BLOK_BASLA} … {BLOK_BITIR}")
    a = metin.index(BLOK_BASLA) + len(BLOK_BASLA)
    b = metin.index(BLOK_BITIR)
    return metin[:a] + "\n" + ozet_tablosu(metin) + "\n" + metin[b:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ROADMAP §3 cephe özeti üreticisi (TSK-216)")
    kip = ap.add_mutually_exclusive_group()
    kip.add_argument("--yaz", action="store_true", help="ROADMAP'teki bloğu yeniden üret")
    kip.add_argument("--denetle", action="store_true", help="yazma; bayat blok ya da cephesiz kalem → çıkış 1")
    ap.add_argument("--dosya", type=pathlib.Path, default=VARSAYILAN_YOL)
    ns = ap.parse_args(argv)
    metin = ns.dosya.read_text(encoding="utf-8")
    if ns.yaz:
        ns.dosya.write_text(blogu_yaz(metin), encoding="utf-8")
        print(f"yazıldı: {ns.dosya} · açık kalem {len(acik_kalemler(metin))} · cephe {len(cephe_adlari(metin))}")
        for s in ihlaller(metin):
            print(f"!! {s}")
        return 0
    if ns.denetle:
        sorunlar = ihlaller(metin)
        blok = blok_icerigi(metin)
        if blok is None:
            sorunlar.append(f"blok işaretleri yok ({BLOK_BASLA} … {BLOK_BITIR})")
        elif blok != ozet_tablosu(metin):
            sorunlar.append("§3 cephe özeti BAYAT — `python ops/roadmap_cephe_ozeti.py --yaz` ile yeniden üret")
        for s in sorunlar:
            print(f"!! {s}")
        if not sorunlar:
            print("cephe özeti güncel; her açık kalem tanımlı bir cepheye bağlı")
        return 1 if sorunlar else 0
    print(ozet_tablosu(metin))
    return 0


if __name__ == "__main__":
    sys.exit(main())
