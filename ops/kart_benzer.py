#!/usr/bin/env python3
"""ops/kart_benzer.py — yeni kart açmadan önce "benzer deneme var mı?" (TSK-170 bacak b).

NEDEN VAR (operatör sorusu 2026-09-06: "başarısız olanların tekrar denenmesini engellemek").
Bir hipotez metni (ya da bir ön-kayıt kartı taslağı) için `research/cards/` külliyatındaki
BENZER denemeleri ve HÜKÜMLERİNİ listeler. Betik HÜKÜM VERMEZ, hiçbir şeyi ENGELLEMEZ — Rol-1
kartı açmadan önce bu listeye bakar, benzerleri yeni kartın `selef`/`ref` alanına kendi eliyle
yazar. LLM'siz, tamamen deterministik: skor yalnız token kümesi aritmetiğidir.

HÜKÜM SINIFININ TEK KAYNAĞI ROADMAP.md §6'DIR. Bir kartın kendi `status` alanı (registered/
measuring/measured/archived) ÖLÇÜM AŞAMASINI anlatır, GEÇTİ/KALDI/NO-GO/ACTIVE'i DEĞİL — o
sınıflandırma yalnız `## §6 KANIT/KARTLAR` bölgesindeki özet satırında yazılıdır
(`ops/kart_endeksi_uret.py` farklı bir sözleşmeyi — kartın KENDİ `status`/`thesis` alanlarını —
okur; bu ikisi KASITLI ayrı kaynaktır, birleştirilmez). §6'da satırı olmayan bir kart için sınıf
UYDURULMAZ: `bilinmiyor` (Uydurma yasağı).

KAYNAKLAR (hepsi depo içi, salt-okunur, ağ YOK):
  1. `research/cards/*.yaml` — `card_id`, `family`, `hipotez` (yoksa eski şema: `thesis`),
     `hukum*` önekli alanlar (isim değişken — hepsi toplanır).
  2. `ROADMAP.md` §6 satırları: `- **[ID] slug** — status: DONE(tarih·SINIF) | ACTIVE | ...`.
  3. `ROADMAP.md` genelinde `status: DROPPED(neden)` kalemleri — "denendi/bırakıldı" listesine
     kart gibi katılır (family/slug'ı yok; sınıfı sabit `DROPPED`).

BENZERLİK: Jaccard(token) + (aynı family ise +0.25) + (sorgu∩slug token sayısı × 0.1). Eşik yok;
skoru 0 olan aday hiç basılmaz (gürültü değil — "benzer değil" demenin biçimi).

YASA 4 (sessiz yutma yok): bozuk bir kart YAML'i taramayı çökertmez — o kart ATLANIR, sayılır,
UYARI stderr'e basılır (sessiz değil).

Bu araç `meridian` paketini import ETMEZ (obs sızıntısı yolu kapalı) ve ağa çıkmaz.

CLI (sözleşme KOMUT SATIRIdır, `main()` içe aktarımı değil):
    .venv/bin/python ops/kart_benzer.py --hipotez "…" [--family x] [--n 8] [--repo .] [--json y.json]
    .venv/bin/python ops/kart_benzer.py --kart research/cards/EDG-2026-083-….yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import yaml

MIN_TOKEN_UZUNLUK = 3
AILE_BONUS = 0.25
SLUG_AGIRLIK = 0.1
VARSAYILAN_N = 8
HUKUM_ONEKI = "hukum"

SEC6_BASLA = "## §6 KANIT/KARTLAR"
SEC6_BITIR = "## §7"

# Kimlik ön eki (`EDG-2026-NNN-`, `EXE-2026-NNN-`, `BASE-2026-NNN-` …) düşürülünce kalan anlamlı
# dosya-adı parçası — "slug". Eşleşmezse dosya adının TAMAMI slug sayılır (fallback, veri kaybı yok).
_SLUG_DESENI = re.compile(r"^[A-Za-z]+-\d{4}-\d+-(.*)$")

# §6'nın kendi biçimi (44/44 satırda doğrulandı, 2026-09-06): `- **[ID] serbest-metin** —
# status: <TOKEN> · owner: … · size: … · trigger: …`. `<TOKEN>` ya `DONE(tarih·SINIF)` ya da
# çıplak bir sözcüktür (`ACTIVE`, `OPERATOR`, `QUEUED` …).
_SEC6_SATIR_DESENI = re.compile(r"^- \*\*\[([A-Za-z0-9\-]+)\][^*]*\*\* — status: (\S+)", re.M)

# ROADMAP genelinde (§6 dışı da dâhil) `status: DROPPED(neden)` kalemleri — kaynak 3.
_DROPPED_DESENI = re.compile(
    r"^- \*\*\[([A-Za-z0-9\-]+)\] ([^*]+)\*\* — status: DROPPED\(([^)]*)\)", re.M)


def normalize_tokens(metin: object) -> set[str]:
    """Casefold + noktalama/alt-çizgi → boşluk + 3+ karakterli token kümesi.

    Türkçe karakter KORUNUR: ASCII'ye indirgeme yok, Python'ın unicode-farkında `str.isalnum()`/
    `str.casefold()` kullanılır. Rakam-yalnız token'lar (`"52"`) 3 karakter eşiğinin altındaysa
    zaten düşer; eşiğin üstündeki karma token'lar (`"52wh"`) tutulur — ayrım harf/rakam değil
    UZUNLUKTUR (brief: "3+ harfli" — ölçüm burada uzunluk kuralına indirgendi, ayrı bir harf-
    zorunluluğu YOK: rakam-yalnız 3+ haneli bir token da (`"429"`) anlam taşıyabilir).
    """
    if not metin:
        return set()
    tampon = "".join(ch if ch.isalnum() else " " for ch in str(metin))
    return {t for t in tampon.casefold().split() if len(t) >= MIN_TOKEN_UZUNLUK}


def slug_from_stem(stem: str) -> str:
    """Dosya adının (uzantısız) `ID-YYYY-NNN-` ön ekini düşürür; kalan slug."""
    m = _SLUG_DESENI.match(stem)
    return m.group(1) if m else stem


def kart_token_kumesi(family: object, hipotez: object, slug: object) -> set[str]:
    """Kart tarafının token kümesi: family + hipotez + slug (tirevirgülü boşluğa çevrilmiş)."""
    return (normalize_tokens(family) | normalize_tokens(hipotez)
            | normalize_tokens(str(slug or "").replace("-", " ")))


def skorla(sorgu_tokens: set[str], sorgu_family: object,
           kart_family: object, kart_tokens: set[str], kart_slug: object) -> float:
    """Skor = Jaccard(sorgu_tokens, kart_tokens) + aile-bonusu + slug-örtüşme bonusu.

    Aile bonusu yalnız İKİ TARAF da family BEYAN ETMİŞSE ve casefold-eşitse uygulanır (sorgu
    family'siz geldiyse — düz `--hipotez`, `--family` verilmemiş — bonus asla tetiklenmez).
    Slug örtüşmesi kart'ın KENDİ slug'ıyla sorgu token'larının kesişim SAYISIdır (oran değil).
    """
    birlesim = sorgu_tokens | kart_tokens
    jaccard = len(sorgu_tokens & kart_tokens) / len(birlesim) if birlesim else 0.0
    aile_bonus = 0.0
    if sorgu_family and kart_family:
        if str(sorgu_family).strip().casefold() == str(kart_family).strip().casefold():
            aile_bonus = AILE_BONUS
    slug_tokens = normalize_tokens(str(kart_slug or "").replace("-", " "))
    slug_ortusme = len(sorgu_tokens & slug_tokens) * SLUG_AGIRLIK
    return jaccard + aile_bonus + slug_ortusme


def hukum_siniflarini_cikar(roadmap_metni: str) -> dict[str, str]:
    """ROADMAP.md §6 bölgesinden `card_id → hüküm sınıfı` sözlüğü.

    `DONE(tarih·SINIF)` → SINIF (GEÇTİ/KALDI/NO-GO); çıplak token (`ACTIVE`, `OPERATOR`, …) →
    kendisi. §6 bölgesi bulunamazsa BOŞ sözlük döner (çağıran bunu `bilinmiyor`a çevirir —
    uydurma yasağı: bölge okunamıyorsa sınıf TAHMİN EDİLMEZ).
    """
    basla = roadmap_metni.find(SEC6_BASLA)
    if basla == -1:
        return {}
    bitir = roadmap_metni.find(SEC6_BITIR, basla)
    bolge = roadmap_metni[basla:bitir] if bitir != -1 else roadmap_metni[basla:]
    sonuc: dict[str, str] = {}
    for kart_id, durum in _SEC6_SATIR_DESENI.findall(bolge):
        if durum.startswith("DONE(") and durum.endswith(")") and "·" in durum:
            ic = durum[len("DONE("):-1]
            sonuc[kart_id] = ic.split("·", 1)[1]
        else:
            sonuc[kart_id] = durum
    return sonuc


def roadmap_dropped_ogeleri(roadmap_metni: str) -> list[dict]:
    """ROADMAP genelinde `status: DROPPED(neden)` kalemleri (kaynak 3) — "denendi/bırakıldı"
    listesine kart-benzeri katılır. family/slug taşımaz; sınıf sabit `DROPPED`."""
    ogeler = []
    for id_, baslik, neden in _DROPPED_DESENI.findall(roadmap_metni):
        ogeler.append({
            "id": id_,
            "family": None,
            "hipotez": baslik.strip(),
            "hukum": neden.strip(),
            "slug": None,
            "sinif": "DROPPED",
        })
    return ogeler


def kartlari_oku(kart_dizini: pathlib.Path) -> tuple[list[dict], int]:
    """`research/cards/*.yaml` içindeki her kartın alanları (dosya adı sırasıyla, deterministik).

    Dönüş: (kart listesi, YAML-hatası-yüzünden-atlanan kart sayısı). Bozuk kart taramayı
    ÇÖKERTMEZ ama SESSİZ de değildir — uyarı stderr'e yazılır (YASA 4).
    """
    kartlar: list[dict] = []
    hata_sayisi = 0
    for yol in sorted(kart_dizini.glob("*.yaml")):
        try:
            ham = yol.read_text(encoding="utf-8")
            veri = yaml.safe_load(ham)
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
            # sessiz-yutma: bozuk TEK kart taramayı çökertmez; kart ATLANIR ve SAYILIR — sessiz
            # değil, uyarı stderr'e basılır (YASA 4, uydurma yasağı: sayı raporda görünür).
            print(f"UYARI: {yol.name} okunamadı/ayrıştırılamadı ({type(e).__name__}: {e}) — atlandı",
                  file=sys.stderr)
            hata_sayisi += 1
            continue
        if not isinstance(veri, dict):
            print(f"UYARI: {yol.name} sözlük değil — atlandı", file=sys.stderr)
            hata_sayisi += 1
            continue
        card_id = veri.get("card_id") or yol.stem
        family = veri.get("family")
        hipotez = veri.get("hipotez") or veri.get("thesis") or ""
        slug = slug_from_stem(yol.stem)
        hukum_parcalari = [str(v) for k, v in veri.items()
                            if isinstance(k, str) and k.startswith(HUKUM_ONEKI) and v]
        kartlar.append({
            "id": str(card_id),
            "family": family,
            "hipotez": hipotez,
            "hukum": " ".join(hukum_parcalari) if hukum_parcalari else "",
            "slug": slug,
        })
    return kartlar, hata_sayisi


def _kirp(metin: object, sinir: int) -> str:
    duz = " ".join(str(metin).split())
    if len(duz) <= sinir:
        return duz
    return duz[:sinir].rstrip() + "…"


def benzerleri_bul(*, hipotez_sorgu: str, family_sorgu: object, repo: str, n: int,
                    haric_id: str | None = None) -> tuple[list[dict], int]:
    """Ana motor: sorguya göre sıralı benzer-liste + kaç kart YAML hatasıyla atlandı.

    Dönen her öğe: id, family, sinif, skor, hipotez, hukum. Skoru 0 olan aday listeye HİÇ
    girmez (eşik yok — sıfır zaten "örtüşme yok" demektir).
    """
    kok = pathlib.Path(repo)
    kart_dizini = kok / "research" / "cards"
    roadmap_yolu = kok / "ROADMAP.md"
    roadmap_metni = roadmap_yolu.read_text(encoding="utf-8") if roadmap_yolu.exists() else ""
    hukum_siniflari = hukum_siniflarini_cikar(roadmap_metni)

    kartlar, hata_sayisi = kartlari_oku(kart_dizini) if kart_dizini.is_dir() else ([], 0)
    dropped = roadmap_dropped_ogeleri(roadmap_metni)

    sorgu_tokens = normalize_tokens(hipotez_sorgu)

    adaylar: list[dict] = []
    for k in kartlar:
        if haric_id and k["id"] == haric_id:
            continue
        tokens = kart_token_kumesi(k["family"], k["hipotez"], k["slug"])
        skor = skorla(sorgu_tokens, family_sorgu, k["family"], tokens, k["slug"])
        if skor <= 0:
            continue
        adaylar.append({
            "id": k["id"], "family": k["family"],
            "sinif": hukum_siniflari.get(k["id"], "bilinmiyor"),
            "skor": skor, "hipotez": k["hipotez"], "hukum": k["hukum"],
        })
    for d in dropped:
        if haric_id and d["id"] == haric_id:
            continue
        tokens = normalize_tokens(d["hipotez"])
        skor = skorla(sorgu_tokens, family_sorgu, d["family"], tokens, d["slug"])
        if skor <= 0:
            continue
        adaylar.append({
            "id": d["id"], "family": d["family"], "sinif": d["sinif"],
            "skor": skor, "hipotez": d["hipotez"], "hukum": d["hukum"],
        })

    adaylar.sort(key=lambda a: (-a["skor"], a["id"]))
    return adaylar[:n], hata_sayisi


def _satir(a: dict) -> str:
    family = a["family"] or "—"
    hukum = _kirp(a["hukum"], 120) if a["hukum"] else "—"
    return (f"{a['id']} · {family} · {a['sinif']} · skor {a['skor']:.2f} · "
            f"{_kirp(a['hipotez'], 90)} · hüküm: {hukum}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Yeni bir hipotez/kart için research/cards/ külliyatındaki BENZER "
                    "denemeleri ve hükümlerini listeler (LLM'siz, deterministik). "
                    "Hüküm VERMEZ, hiçbir şeyi ENGELLEMEZ.")
    ap.add_argument("--hipotez", help="sorgu hipotez metni (--kart verilmezse zorunlu)")
    ap.add_argument("--family", help="sorgu family'si (opsiyonel; --kart verilmişse yok sayılır)")
    ap.add_argument("--n", type=int, default=VARSAYILAN_N,
                    help=f"basılacak azami satır (varsayılan {VARSAYILAN_N})")
    ap.add_argument("--repo", default=".", help="depo kökü (varsayılan .)")
    ap.add_argument("--json", dest="json_yolu", help="aynı listeyi JSON olarak da yaz")
    ap.add_argument("--kart", help="hipotez/family bu YAML dosyasından okunur; kartın kendi "
                    "card_id'si sonuçlardan HARİÇ tutulur")
    a = ap.parse_args(argv)

    if not a.kart and not a.hipotez:
        ap.error("--hipotez ya da --kart gerekli")

    haric_id = None
    if a.kart:
        kart_yolu = pathlib.Path(a.kart)
        try:
            veri = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
            # sessiz-yutma: --kart okunamazsa sorgu KURULAMAZ; hata AÇIKÇA basılır, çıkış != 0
            print(f"HATA: --kart okunamadı/ayrıştırılamadı ({type(e).__name__}: {e})",
                  file=sys.stderr)
            return 2
        if not isinstance(veri, dict):
            print(f"HATA: --kart sözlük değil: {kart_yolu}", file=sys.stderr)
            return 2
        hipotez_sorgu = veri.get("hipotez") or veri.get("thesis") or ""
        family_sorgu = veri.get("family")
        haric_id = str(veri.get("card_id") or kart_yolu.stem)
    else:
        hipotez_sorgu = a.hipotez
        family_sorgu = a.family

    sonuc, hata_sayisi = benzerleri_bul(
        hipotez_sorgu=hipotez_sorgu, family_sorgu=family_sorgu,
        repo=a.repo, n=a.n, haric_id=haric_id)

    for satir in sonuc:
        print(_satir(satir))
    if not sonuc:
        print("(benzer kart bulunamadı)")
    if hata_sayisi:
        print(f"UYARI: {hata_sayisi} kart YAML hatasıyla atlandı", file=sys.stderr)

    if a.json_yolu:
        pathlib.Path(a.json_yolu).write_text(
            json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
