#!/usr/bin/env python3
"""Alan sayfası başına KART SAYIMI — statik emisyon atfı (D2-a · kart sözleşmesi).

NEDEN BU BETİK VAR
------------------
`docs/BASELINE-2026-08-06.md` §0.1 Ö4 şunu ölçemedi diye kaydetmişti: "sayfa başına
ÇALIŞMA-ZAMANI kart sayısı". Gerekçe doğruydu — kart HTML'i yardımcı fonksiyonlarda
üretilip şablona enterpole ediliyor, satır-sırasına dayalı atıf yanlış sonuç veriyor
(baseline'ın kendi örneği: `market` kovası 31 kart gösteriyor, gerçekte 8). Sayfa
kırılımı bu yüzden "önceki denetimden devralındı, tekrar ölçülmedi" diye yazıldı.

Bu betik o boşluğu kapatır. Satır aralığına DEĞİL, üç kaynağa bakar:
  1. `RENDER.<bölüm>` gövdesinin KENDİ emisyonları,
  2. o gövdenin `opParcalar()` / `intraParcalar()` sözlüğünden TÜKETTİĞİ anahtarlar
     (paylaşımlı hesap: her parça KURULUR ama her sayfa yalnız kendi anahtarlarını yazar),
  3. gövdenin çağırdığı yardımcı fonksiyonların emisyonları (özyinelemeli).

DOĞRULAMA: yöntem, baseline'ın devraldığı üç sayıyı BAĞIMSIZ olarak yeniden üretiyor —
Öğrenme 39, Gözetim 3, Kilitler 5. (Portföy'de 17 ölçülüyor; baseline'ın devraldığı 13
tekrar ölçülmemiş bir sayıydı ve bu betik onu düzeltir.)

SINIR — BEYAN: sayım STATİK EMİSYON sayısıdır, çalışma zamanı kart sayısı değil. İki
yönde ayrışır ve ikisi de bilerek:
  * `.map()` içindeki tek emisyon çalışma zamanında N kart doğurur (araç kütüphanesi
    kategorileri: bir emisyon, veriden gelen kategori sayısı kadar kart).
  * Bir fonksiyonun iki dalı (ör. "ölçüm yok" / "ölçüldü") iki emisyon sayılır ama
    aynı anda yalnız biri çizilir.
Bütçe bu yüzden bir TAVANdır: statik emisyon, çalışma zamanı yükünün üst sınırı değil
ÜST MERTEBESİdir ve ratchet olarak kullanılır (sessizce kart eklenemesin diye).

Koşum:  python3 research/olcumler/kart_sozlesmesi_2026-08-07/say_kart.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
APPJS = KOK / "meridian" / "web" / "app.js"

# Yüzey → bölümler. KAYNAKTAN TÜRETİLİR (D2-b, 2026-08-07): eskiden bu tablo burada ELLE
# duruyordu ve app.js'in `ALAN_BOLUMLERI`si ile "birebir olmalı" diye BEYAN ediliyordu. IA
# değiştiği gün beyan yalanlandı ve ölçüm betiği var olmayan sayfaları saymaya çalıştı
# (KeyError). İkinci bir liste tutmanın bedeli budur; artık tek kaynak app.js'in kendisi.
# Ölçümün YÖNTEMİ değişmedi — yalnız girdisi artık ölçtüğü şeyden okunuyor.
def _alan_bolumleri(kaynak: str) -> dict[str, list[str]]:
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", kaynak, re.S)
    if not blok:
        raise SystemExit("app.js'te ALAN_BOLUMLERI bulunamadı — ölçüm girdisi yok")
    return {alan: re.findall(r'"(\w+)"', liste)
            for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok.group(1), re.M)}
PAYLASIMLI = {"opParcalar", "intraParcalar"}
_TANIM = re.compile(
    r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"
    r"|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="
    r"|^(RENDER\.[A-Za-z_$][\w$]*)\s*="
    r"|^(window\.[A-Za-z_$][\w$]*)\s*="
)


def _yukle(kaynak: str | None = None):
    satirlar = (kaynak if kaynak is not None else APPJS.read_text()).splitlines()
    baslar = []
    for i, l in enumerate(satirlar):
        m = _TANIM.match(l)
        if m:
            baslar.append((i, m.group(1) or m.group(2) or m.group(3) or m.group(4)))
    bloklar: dict[str, list[tuple[int, int]]] = {}
    for idx, (i, ad) in enumerate(baslar):
        son = baslar[idx + 1][0] if idx + 1 < len(baslar) else len(satirlar)
        bloklar.setdefault(ad, []).append((i, son))
    return satirlar, bloklar


def _kod(satirlar, bloklar, ad):
    # YORUM SATIRLARI SAYILMAZ (repo deseni, test_pano_durum_kartlari_v191): bu depo her silmeyi
    # gerekçesiyle yazıyor ve gerekçe "hâlâ orada" diye okunmamalı.
    parcalar = []
    for a, b in bloklar[ad]:
        parcalar.append("\n".join(l for l in satirlar[a:b] if not l.lstrip().startswith("//")))
    return "\n".join(parcalar)


def _kart(metin: str) -> int:
    return len(re.findall(r'class="card', metin))


def _parca_haritasi(satirlar, bloklar, fn):
    """opParcalar/intraParcalar içindeki `const sX = …` anahtarına düşen kart sayısı."""
    a, b = bloklar[fn][0]
    govde = satirlar[a:b]
    ic = re.compile(r"^  (?:const|let)\s+([A-Za-z_$][\w$]*)\s*=")
    isaret = [(i, m.group(1)) for i, l in enumerate(govde) if (m := ic.match(l))]
    cikti = {}
    for idx, (i, ad) in enumerate(isaret):
        son = isaret[idx + 1][0] if idx + 1 < len(isaret) else len(govde)
        cikti[ad] = _kart("\n".join(l for l in govde[i:son] if not l.lstrip().startswith("//")))
    return cikti


def olc(kaynak: str | None = None):
    metin = kaynak if kaynak is not None else APPJS.read_text()
    ALAN_BOLUMLERI = _alan_bolumleri(metin)
    satirlar, bloklar = _yukle(metin)
    OP = _parca_haritasi(satirlar, bloklar, "opParcalar")
    INTRA = _parca_haritasi(satirlar, bloklar, "intraParcalar")
    adlar = set(bloklar)

    def yardimci(ad, gorulen):
        govde = _kod(satirlar, bloklar, ad)
        toplam, kaynaklar = 0, []
        for m in adlar:
            if m in gorulen or m in PAYLASIMLI or m == ad:
                continue
            kisa = m.split(".")[-1]
            if len(kisa) < 4:
                continue
            if re.search(r"(?<![\w$.])" + re.escape(kisa) + r"\s*\(", govde):
                c = _kart(_kod(satirlar, bloklar, m))
                alt, altk = yardimci(m, gorulen | {m})
                if c or alt:
                    kaynaklar.append(m)
                toplam += c + alt
                kaynaklar += altk
        return toplam, kaynaklar

    sonuc = {}
    for alan, bolumler in ALAN_BOLUMLERI.items():
        alan_toplam, alan_kapakli, bolum_detay = 0, 0, {}
        for b in bolumler:
            k = "RENDER." + b
            if k not in bloklar:
                bolum_detay[b] = {"toplam": None, "neden": "RENDER tanımı bulunamadı"}
                continue
            govde = _kod(satirlar, bloklar, k)
            # opParcalar/intraParcalar'a bağlanan değişken adları — `p.` sabit varsayılamaz
            # (`karne` ve `hermes` `op.` adını kullanıyor ve ilk ölçümde bu yüzden 39 yerine 32 çıktı).
            baglar = {}
            for m in re.finditer(r"(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:await\s+)?(opParcalar|intraParcalar)\b", govde):
                baglar[m.group(1)] = m.group(2)
            for m in re.finditer(r"(?:const|let)\s+\[([^\]]*)\]\s*=\s*await\s+Promise\.all\(\[(.*?)\]\)", govde, re.S):
                degiskenler = [v.strip() for v in m.group(1).split(",")]
                for i, arg in enumerate(re.split(r",\s*\n", m.group(2))):
                    if i >= len(degiskenler):
                        break
                    if "opParcalar" in arg:
                        baglar[degiskenler[i]] = "opParcalar"
                    elif "intraParcalar" in arg:
                        baglar[degiskenler[i]] = "intraParcalar"
            parca, parca_detay = 0, []
            for v, fn in baglar.items():
                H = OP if fn == "opParcalar" else INTRA
                for anahtar in sorted(set(re.findall(r"\b" + re.escape(v) + r"\.([A-Za-z_$][\w$]*)", govde))):
                    if anahtar in H:
                        parca += H[anahtar]
                        parca_detay.append(f"{v}.{anahtar}={H[anahtar]}")
            direkt = _kart(govde)
            yard, kaynaklar = yardimci(k, {k})
            t = direkt + parca + yard
            alan_toplam += t
            bolum_detay[b] = {"toplam": t, "direkt": direkt, "parca": parca,
                              "parcalar": parca_detay, "yardimci": yard, "kaynak": sorted(set(kaynaklar))}
        sonuc[alan] = {"toplam": alan_toplam, "bolumler": bolum_detay}
    # Kapak (katlanır kart) atfı: `katKart("<anahtar>")` çağrılarının kayıt defterindeki alanı.
    kayit = dict(re.findall(r'^\s*"([\w:]+)":\s*\{\s*alan:\s*"(\w+)"', "\n".join(satirlar), re.M))
    kullanim = {}
    for m in re.finditer(r'katKart\("([\w:]+)"', "\n".join(
            l for l in satirlar if not l.lstrip().startswith("//"))):
        kullanim[m.group(1)] = kullanim.get(m.group(1), 0) + 1
    for anahtar, n in kullanim.items():
        alan = kayit.get(anahtar)
        if alan in sonuc:
            sonuc[alan]["kapakli"] = sonuc[alan].get("kapakli", 0) + n
    for alan in sonuc:
        sonuc[alan].setdefault("kapakli", 0)
        sonuc[alan]["kapaksiz"] = sonuc[alan]["toplam"] - sonuc[alan]["kapakli"]
    return sonuc, kayit, kullanim


def main():
    sonuc, kayit, kullanim = olc()
    print("ALAN SAYFASI BAŞINA KART EMİSYONU (statik atıf)\n")
    print(f"{'sayfa':10s} {'toplam':>7s} {'kapaklı':>8s} {'kapaksız':>9s}")
    for alan, v in sonuc.items():
        print(f"{alan:10s} {v['toplam']:7d} {v['kapakli']:8d} {v['kapaksiz']:9d}")
    print(f"\nΣ toplam = {sum(v['toplam'] for v in sonuc.values())} · "
          f"Σ kapaklı = {sum(v['kapakli'] for v in sonuc.values())}")
    print(f"\nkayıt defterinde {len(kayit)} anahtar · kaynakta {len(kullanim)} anahtar kullanılıyor")
    eksik = sorted(set(kayit) - set(kullanim))
    if eksik:
        print("KAYITLI AMA KULLANILMAYAN (ölü anahtar):", ", ".join(eksik))
    fazla = sorted(set(kullanim) - set(kayit))
    if fazla:
        print("KULLANILIYOR AMA KAYITSIZ (kapak almaz):", ", ".join(fazla))
    # ÇIKTI YOLU ARTIK ARGÜMAN (D2-b, 2026-08-07). Sabit yol, betiği ikinci kez koşan her turun
    # ÖNCEKİ TURUN FOTOĞRAFINI EZMESİ demekti — ve tam olarak bu oldu: D2-b koşumu D2-a'nın
    # `kart_sayimi.json`unu üstüne yazdı (D2-a'nın insan-okur kaydı `kart_sayimi.txt`te ve ADR
    # Ek D.2 tablosunda duruyor; JSON `git checkout` ile geri alınabilir). Bir ölçüm artefaktı
    # dönemine ait olmalı: yol verilmezse eski davranış korunur, verilirse tur kendi dosyasına yazar.
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "kart_sayimi.json"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps({"sayfa": sonuc, "kayit": kayit, "kullanim": kullanim},
                                ensure_ascii=False, indent=1))
    print(f"\nyazıldı: {hedef}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
