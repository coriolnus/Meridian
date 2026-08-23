#!/usr/bin/env python3
"""ops/kart_endeksi_uret.py — `research/cards/README.md` ENDEKSİNİN ÜRETİCİSİ (U3, 2026-08-23).

NEDEN VAR. Ön-kayıt defterinin endeksi ELLE bakılıyordu ve bayatladı: 2026-08-23 WP5 eleme
turu EDG-001/002'yi hâlâ "Aktif kartlar (registered)" başlığı altında buldu, oysa ikisi de
2026-07-31'de `archived`di (docs/ELEME-WP5-2026-08-23.md kalem 3, iz ②). Bayat bir endeks
YANLIŞ endekstir: okuyucuyu ölü bir kartı canlı sanmaya götürür ve "hangi kart açık" sorusu
bir daha güvenle cevaplanamaz. Bu yüzden endeks YAZILMAZ, ÜRETİLİR — kaynağı kartların
KENDİ `status` alanlarıdır ve kart değişince yeniden üretilir (runbook_uret.py emsali).

KAYNAK SÖZLEŞMESİ (bu dört alan; başka hiçbir yerden okunmaz):
  1. `card_id`   — satırın kimliği
  2. `status`    — gruplama ekseni (kartın kendi alanı; yorum satırı DEĞİL)
  3. `thesis`    — tek-cümle konu (kartın KENDİ cümlesi, ilk cümlesi kesilerek)
  4. hüküm özeti — şu öncelikle: `verdict` (str ya da dict'in `hukum`/`sonuc`/… anahtarı),
     yoksa `status:` satırının kendi yorumu. İkisi de yoksa satırda hüküm sütunu YAZILMAZ.

UYDURMA YASAĞI (anayasa 1'in bu dosyadaki karşılığı). Hiçbir konu/hüküm cümlesi ÖZETLENMEZ;
yalnız kartın kendi metni KESİLİR (kesik `…` ile görünür olur). Bir kartın hükmü yoksa satır
sessizce güzelleştirilmez — sütun hiç basılmaz. Statü kovası tanınmıyorsa kart "diğer"
kovasına ADIYLA düşer (YASA 4: sessiz yutma yok); listeden düşürülmez.

DAMGA YOK, DETERMİNİSTİK ÇIKTI. Endekse üretim ZAMANI yazılmaz: yazılsaydı her koşu diff
üretir ve `--kontrol` kapısı ("endeks kartlarla ayrıştı mı") ölçülemez olurdu.

ELLE YAZILAN BÖLÜMLER KORUNUR. README'nin endeks DIŞI bölümleri (retroaktif kayıt kuyruğu,
kart-adayı bulgular, numara notu) karttan türetilemez — bu yüzden üretici yalnız iki sentinel
arasını sahiplenir; dışını OKUMAZ, YAZMAZ, karşılaştırmaz.

KULLANIM:
    python ops/kart_endeksi_uret.py             # README.md endeks bölümünü üret/yaz
    python ops/kart_endeksi_uret.py --kontrol   # yazMA; endeks güncel mi (çıkış 1 = bayat)
    python ops/kart_endeksi_uret.py --cikti /yol.md
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import yaml

KOK = pathlib.Path(__file__).resolve().parents[1]
KART_DIZINI = KOK / "research" / "cards"
HEDEF = KART_DIZINI / "README.md"

BASLA = "<!-- ENDEKS: ÜRETİLEN BÖLÜM — ELLE DÜZENLEME YOK (ops/kart_endeksi_uret.py) -->"
BITIR = "<!-- ENDEKS: SON -->"

# Kova sırası ANLAMLIDIR: açık işten kapanmışa. `measured_partial` bilerek `measured`
# kovasında — yarısı ölçülmüş bir kart "henüz ölçülmedi" değildir; satırda statü AYNEN
# basıldığı için birleştirme görünür kalır (gizli normalizasyon yok).
KOVALAR: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("registered", "Kayıtlı — ölçüm bekliyor", ("registered",)),
    ("measuring", "Ölçümde", ("measuring",)),
    ("measured", "Ölçüldü", ("measured", "measured_partial")),
    ("arsiv", "Arşiv", ("archived",)),
)
DIGER = ("diger", "Diğer — kova tanımı yok (YASA 4: adıyla listelenir)")

# `verdict` bir sözlükse hüküm cümlesinin aranacağı anahtarlar, SIRAYLA. Hiçbiri yoksa
# sözlüğün İLK anahtarı kullanılır (YAML sırası korunur → deterministik).
HUKUM_ANAHTARLARI = ("hukum", "ana_hukum", "sonuc", "olcum")

KONU_SINIRI = 150
HUKUM_SINIRI = 170


def _duzlestir(metin: object) -> str:
    return " ".join(str(metin).split())


def ilk_cumle(metin: object, sinir: int) -> str:
    """Kartın KENDİ ilk cümlesi, `sinir` karakterde kelime sınırından kesilerek.

    Özetleme YOK — yalnız kesme. Kesildiyse `…` ile görünür olur.
    """
    duz = _duzlestir(metin)
    if not duz:
        return ""
    parcalar = re.split(r"(?<=[.!?])\s+", duz)
    cumle = parcalar[0]
    # İki hâlde sonraki cümle EKLENİR (ikisi de sabit kural → deterministik, özet değil):
    #  (a) açılış çok kısa ("Mevcut kırılma ailesi GÜÇTE giriyor.") — tek başına konu olmaz;
    #  (b) açılış `:` ile biten bir BAŞLIK ("2026-08-01 — KARNE HÜKMÜ (Rol-1):") — hükmün
    #      kendisi bir sonraki cümlededir; başlığı tek başına basmak boş satır üretirdi.
    i = 1
    while i < len(parcalar) and (len(cumle) < 40 or cumle.rstrip().endswith(":")):
        cumle = f"{cumle} {parcalar[i]}"
        i += 1
    if len(cumle) <= sinir:
        return cumle
    return cumle[:sinir].rsplit(" ", 1)[0] + "…"


def hukum_metni(kart: dict, ham: str) -> str:
    """Hüküm özeti kaynağı: `verdict` alanı, yoksa `status:` satırının kendi yorumu."""
    v = kart.get("verdict")
    if isinstance(v, str) and v.strip():
        return ilk_cumle(v, HUKUM_SINIRI)
    if isinstance(v, dict) and v:
        for anahtar in HUKUM_ANAHTARLARI:
            if v.get(anahtar):
                return ilk_cumle(v[anahtar], HUKUM_SINIRI)
        return ilk_cumle(next(iter(v.values())), HUKUM_SINIRI)
    satirlar = ham.split("\n")
    for i, satir in enumerate(satirlar):
        if not satir.startswith("status:") or "#" not in satir:
            continue
        # `status:` satırının yorumu ÇOK SATIRLI olabilir (hüküm gövdesi hemen altındaki
        # `#` satırlarında sürer — EDG-001, BASE-001 …). Blok bitene kadar okunur; yoksa
        # ilk cümle yalnız "KARNE HÜKMÜ (Rol-1):" gibi bir BAŞLIK olur ve satır boş kalırdı.
        blok = [satir.split("#", 1)[1].strip()]
        for devam in satirlar[i + 1:]:
            if not devam.startswith("#"):
                break
            blok.append(devam.lstrip("#").strip())
        yorum = " ".join(p for p in blok if p)
        return ilk_cumle(yorum, HUKUM_SINIRI) if yorum else ""
    return ""


def kartlari_oku(dizin: pathlib.Path | None = None) -> list[dict]:
    """Her kart için endeks satırının ham malzemesi. Sıra: dosya adı (deterministik)."""
    dizin = dizin or KART_DIZINI
    kayitlar = []
    for yol in sorted(dizin.glob("*.yaml")):
        ham = yol.read_text(encoding="utf-8")
        kart = yaml.safe_load(ham)
        if not isinstance(kart, dict):
            raise SystemExit(f"kart sözlük değil: {yol}")
        kayitlar.append({
            "dosya": yol.name,
            "card_id": str(kart.get("card_id", yol.stem)),
            "status": str(kart.get("status", "")),
            "konu": ilk_cumle(kart.get("thesis", ""), KONU_SINIRI),
            "hukum": hukum_metni(kart, ham),
        })
    return kayitlar


def _satir(k: dict) -> str:
    parcalar = [f"- **{k['card_id']}** (`{k['status']}`) — {k['konu']}"]
    if k["hukum"]:
        parcalar.append(f"  · HÜKÜM: {k['hukum']}")
    parcalar.append(f"  · kart: `{k['dosya']}`")
    return "\n".join(parcalar)


def endeks(kayitlar: list[dict] | None = None) -> str:
    kayitlar = kartlari_oku() if kayitlar is None else kayitlar
    yerlesen: set[str] = set()
    satirlar = [
        BASLA,
        "",
        "## Kart endeksi (ÜRETİLİR — elle düzenlenmez)",
        "",
        "Kaynak: `research/cards/*.yaml` → `status` alanı. Üretici: `ops/kart_endeksi_uret.py`.",
        "Bayat mı diye sor: `python ops/kart_endeksi_uret.py --kontrol` (çıkış 1 = bayat).",
        "Konu ve hüküm cümleleri kartın KENDİ metninden KESİLİR (`…`), özetlenmez.",
        "",
        f"Toplam **{len(kayitlar)}** kart.",
        "",
    ]
    for _ad, baslik, statuler in KOVALAR:
        kova = [k for k in kayitlar if k["status"] in statuler]
        yerlesen.update(k["card_id"] for k in kova)
        satirlar.append(f"### {baslik} ({len(kova)})")
        satirlar.append("")
        if kova:
            satirlar.extend(_satir(k) for k in kova)
        else:
            satirlar.append("_(kart yok)_")
        satirlar.append("")
    artan = [k for k in kayitlar if k["card_id"] not in yerlesen]
    satirlar.append(f"### {DIGER[1]} ({len(artan)})")
    satirlar.append("")
    if artan:
        satirlar.extend(_satir(k) for k in artan)
    else:
        satirlar.append("_(kart yok)_")
    satirlar.append("")
    satirlar.append(BITIR)
    return "\n".join(satirlar) + "\n"


def birlestir(mevcut: str, uretilen: str) -> str:
    """Üretilen bölümü sentinel'ler arasına yerleştirir; dışındaki elle yazımı KORUR."""
    if BASLA in mevcut and BITIR in mevcut:
        bas = mevcut.index(BASLA)
        son = mevcut.index(BITIR) + len(BITIR)
        kuyruk = mevcut[son:]
        return mevcut[:bas] + uretilen.rstrip("\n") + kuyruk
    ayrac = "" if mevcut.endswith("\n\n") or not mevcut else "\n"
    return mevcut + ayrac + "\n" + uretilen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="research/cards/README.md kart endeksi üreticisi (kaynak: kartların status alanı)")
    ap.add_argument("--kontrol", action="store_true",
                    help="yazma; diskteki endeks kartlarla aynı mı (çıkış 1 = bayat)")
    ap.add_argument("--cikti", default=str(HEDEF), help="hedef dosya (varsayılan research/cards/README.md)")
    a = ap.parse_args(argv)
    hedef = pathlib.Path(a.cikti)
    mevcut = hedef.read_text(encoding="utf-8") if hedef.exists() else ""
    yeni = birlestir(mevcut, endeks())
    if a.kontrol:
        if mevcut == yeni:
            print(f"GÜNCEL · {hedef} (endeks kartlarla aynı)")
            return 0
        print(f"BAYAT · {hedef} kart durumlarıyla ayrışmış — "
              f"`python ops/kart_endeksi_uret.py` ile yeniden üret", file=sys.stderr)
        return 1
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(yeni, encoding="utf-8")
    kayitlar = kartlari_oku()
    dagilim = ", ".join(
        f"{baslik.split(' —')[0]}={sum(1 for k in kayitlar if k['status'] in st)}"
        for _ad, baslik, st in KOVALAR)
    print(f"yazıldı: {hedef} · {len(kayitlar)} kart · {dagilim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
