#!/usr/bin/env python3
"""ops/karar_envanteri.py — bir penceredeki KARARLARIN envanteri ve hafıza atıfları (EDG-2026-103 SAYAÇ-0).

NEDEN VAR. EDG-2026-103 "zihin modeli sayfaları neden karara girmiyor" sorusunu dört kola ayırır ve
her kolun paydası bir KARAR kümesidir (D). Önceki üç kart (083/084/089) "atıf yazıldı mı" diye baktı
ama "o pencerede kaç karar fırsatı vardı" sorusunu hiç sormadı: "0 atıf" ile "0 karar" ayrışmadı.
Bu araç pencereyi tarar ve her karar için kaynağını, tarihini, atıf türünü ve konu token kümesini
çıkarır. HÜKÜM VERMEZ — K1–K4 ölçüm kodu bu çıktıyı okur.

OKUYUCU (Yasa 6): EDG-2026-103 ölçümü (`research/olcumler/edg103_okuma_ilgi_atif/`, kart
`olcum_plani` SAYAÇ-0 + K2–K4) ve kartın ADIM-0 (d) kuru koşumu. Araç dosyaya yalnız `--cikti`
verilince, verilen yola yazar; başka hiçbir şey yazmaz.

KARAR TANIMI: CLAUDE.md §2'nin "Bir karar / ruling / ayar değişikliği yazmak" satırı. O satır bir
DAVRANIŞ tarif eder, metin biçimi değil; aşağıdaki kurallar onu metinde yakalamanın SEZGİSEL
karşılığıdır ve kusursuz değildir. Kartın PK/NK'sı aracı doğrular (kill-list: PK/NK tutmazsa hiçbir
sayı yayılmaz). Pencere UTC günleridir, iki uç dâhil.

KAYNAKLAR VE KURALLAR
  1. git — `git log` (TÜM erişilebilir commit'ler, committer tarihi UTC'ye çevrilerek süzülür; git'in
     `--since` kesimi tarih sırası bozuk geçmişte erken durabildiği için KULLANILMAZ). Commit KONU
     SATIRI aşağıdaki karar işaretlerinden birini taşıyorsa karardır; ek olarak konu satırında
     `CLAUDE.md §N` anılması kural değişikliği sayılır (yalnız git'te — günlükte kural ATFI çoktur).
     Konusu `Günlük` ile başlayan commit'ler SAYILMAZ: içlerindeki kararlar günlük kaynağından sayılır.
     Atıf ve token için tüm mesaj (konu + gövde) okunur.
  2. roadmap — (a) başlık satırı `**[ID] …** — status: DONE(YYYY-AA-GG…` ya da `DROPPED(YYYY-AA-GG…`
     olan kalemler (TSK kalemleri ve §6 kart satırları; tarih parantezin İÇİNDEN okunur) karardır;
     (b) her kalemin `What:` alanının başındaki TARİHLİ üst düzey parantezli notları AYRI kayıttır
     (Rol-1 kararı ve hafıza atfını oraya yazar — "(2026-09-24 22:5xZ ÖLÇÜM + KARAR [Rol-1] … Kaynak:
     hafıza: …)"); notun tarihi ilk 60 karakterindeki tarihtir. Karar işareti taşıyan not karardır.
  3. kart — `research/cards/*.yaml` üst düzey anahtarları: `on_kayit` (kart açılışı; metin = dosya
     başı yorum bloğu + alan — HAFIZA KONTROLÜ orada yazılır) ve `hukum*` / `karar*` /
     `operator_karar*` (metin = o anahtarın bloğu). Tarih: anahtar son ekindeki `_YYYY_AA_GG`, yoksa
     bloktaki İLK tarih; hiç tarih yoksa karar UYDURULMAZ, `tarihsiz_atlanan`a sayılır (tarihsiz
     kayıt pencereye yerleştirilemez — bu sayı pencerenin değil TÜM külliyatındır).
  4. günlük — `MERIDIAN_ENGINEERING_LOG.md` birimleri: her `#` başlığı (sonraki paragraflarıyla) ve
     her sütun-0 `- ` maddesi ayrı birimdir. Birimin tarihi, başlıktaki EN BÜYÜK tarih (yazım günü;
     "olaylar 09-21 · yazım 09-23" gibi çift tarihli başlıklar), başlıkta tarih yoksa bir önceki
     tarihli başlıktan devralınır. Karar işareti taşıyan birim karardır.

KARAR İŞARETLERİ (`KARAR_ISARETLERI`): büyük harf `KARAR…` · "operatör/Rol-1 kararı" · "karar
(operatör…" · `HÜKÜM`/`HÜKMÜ` ya da "hüküm:"/"hükmü:" ve "Rol-1/operatör hükmü" · "ruling" ·
`ÖN-KAYIT` · durum geçişi (`→ ACTIVE|GATED|DONE|DROPPED|QUEUED|OPERATOR`, `DROPPED`, `KAPANDI`,
`REDDEDİLDİ`, `YÜKSELTİLDİ`, kart `→ measuring|measured|archived`) · "ayar değişikliği"/"ayar:".
"üçlü hüküm" (§6 test hükmü, rutin doğrulama) aramadan ÖNCE metinden çıkarılır.

DESTEK: karar işareti TAŞIMAYAN ama kimliği ve tarihi olan kayıt (işaretsiz ROADMAP notu, işaretsiz
commit, işaretsiz günlük birimi) karar DOĞURMAZ; aynı (UTC günü, kimlik) anahtarlı bir karar VARSA
ona DESTEK olarak eklenir — yalnız ATIF türlerine katkı verir, konu tokenlarına ve D'ye girmez.
Gerekçe (kuru koşumda ölçüldü, 2026-09-25): 09-24'ten beri Rol-1 hafıza atfını kalemin ROADMAP
notuna yazıyor, kararın kendisi ise commit konusunda duruyor (`TSK-219 → ACTIVE` ↔ notta
"Kaynak: hafıza: benzer kayıt yok (recall …)"); destek olmadan bu kararlar sahte "atıfsız" sayılırdı.

BİRLEŞTİRME: aynı UTC gününde aynı BİRİNCİL KİMLİĞİ (başlıktaki ilk TSK/EDG/EXE/BASE kimliği;
PRG cephe etiketi sayılmaz; `EDG-085` gibi kısa biçim kart dosyalarından TEK eşleşmeyle tam kimliğe
çevrilir) taşıyan kayıtlar TEK karardır — atıf türleri ve tokenlar birleşir, kaynaklar listelenir.
Kimliksiz kayıt hiçbir şeyle birleşmez.

ATIF TÜRLERİ (`atif_turleri`, çoklu):
  * `kaynak: zihin modeli|sayfa|recall|memory|kart_benzer` (CLAUDE.md §0-5 / §2 biçimi) → o tür;
    tırnak ya da backtick içinde başlayan biçim bir ALINTIDIR (kuralın kendisinden söz eden karar) ve
    sayılmaz
  * "hafıza:" ya da "HAFIZA KONTROLÜ (…):" / "HAFIZA ATFI […]:" SEGMENTİ (etiketten sonraki ≤240 karakter, ilk `)` / `]` /
    boş satırda kesilir) içinde: "zihin modeli"/`sayfa_oku` → sayfa · "recall"/`hafiza_sor` → recall ·
    `kart_benzer` → kart_benzer · "memory" ya da kebap-biçimli not adı (`ornek-hafiza-notu`) → memory ·
    araç yok ama "kayıt yok"/"benzer yok" → `bos_beyan` (CLAUDE.md §2'nin "hafıza: benzer kayıt yok"
    biçimi) · segment var ama hiçbiri yok → `diger`
  * "memory `ad`" alıntısı → memory; `kart_benzer` metinde herhangi bir yerde → kart_benzer
  Segment dışındaki çıplak "recall" SAYILMAZ: konusu recall olan kararlar (TSK-162 gibi) sahte atıf
  üretirdi.

BİLİNÇLİ OLARAK YAKALANMAYANLAR (sezgilerin bedeli — bedel yasası):
  * işaretsiz yazılmış kararlar (ör. "izin kipi kalıyor" deyip hiçbir işaret kelimesi taşımayan
    düzyazı; küçük harf "kapandı"; "AÇILDI" ile açılan yeni kalemler — ROADMAP'e madde yazmak §2'de
    AYRI bir satırdır);
  * ROADMAP'te tarihsiz durum değişiklikleri (ACTIVE/GATED/QUEUED başlıkta tarih taşımaz — yalnız
    git konu satırı ya da tarihli not yakalar); `What:` dışındaki alanlardaki (İŞ/Why/Ref) ve
    `What:`in düz metin kısmından SONRA gelen notlar; tarihi ilk 60 karakterde olmayan notlar;
  * destek, aynı gün aynı kalemde ALAKASIZ bir atfı da karara taşıyabilir (üst sayım yönünde);
    kimliksiz destek hiçbir şeye eklenmez (alt sayım yönünde);
  * kart `status` geçişleri (kart dosyasında tarih yok — git konusu yakalarsa sayılır) ve
    `*_kaydi_*` kayıt anahtarları (ölçüm kaydıdır, karar değil);
  * aynı gün aynı kimlikte İKİ ayrı karar TEK sayılır (alt sayım yönünde); başlıkta kimlik taşımayan
    aynı kararın farklı kaynaklardaki kopyaları birleşmez (üst sayım yönünde);
  * aynı karar FARKLI bir kalem kimliği altında da yazılmışsa ikinci kez sayılır (kuru koşumda
    EDG-089 hükmü TSK-060 notunda, EDG-085 pilot açılışı TSK-013 notunda — üst sayım yönünde);
    birincil kimlik başlıktaki İLK kimliktir, çok kimlikli başlıkta karar yanlış kaleme yazılabilir;
  * `operator_kararlari` gibi çok kararlı tek blok TEK karar sayılır;
  * bir kararın konusunu recall ile ilgili bir kaynaktan alan "kaynak: `…` 'recall/…'" biçimi recall
    atfı sayılmaz, ama "hafıza:" segmentinde konusu recall olan bir cümle SAYILIR (nadir).

SIR: araç yalnız DEPOYA girmiş metni okur (depo sırsızdır: `.env`/`backups/` versiyonlanmaz). Yine
de kartın kill-list'i sırrı sıfır toleransla kapattığı için çıktıda serbest metin yalnız ≤160
karakterlik başlıktır; ≥24 karakterlik harf+rakam karışık jetonlar (anahtar/özet biçimi) hem token
kümesinden hem başlıktan ATILIR ve sayısı `sir_benzeri_atilan`da raporlanır.

TOKEN: `kart_benzer.normalize_tokens` İTHAL edilir — kopya değil (tek-kaynak yasası; kartın K2'si
aynı fonksiyonla sayfa tokenlarını çıkaracak, iki uçta iki normalizasyon Jaccard'ı sessizce bozardı).

Bu araç `meridian` paketini içe aktarmaz ve ağa çıkmaz. A1'de depo `.git` taşımaz — araç Rol-1'in
checkout'unda koşar.

CLI (sözleşme KOMUT SATIRIdır):
    .venv/bin/python ops/karar_envanteri.py --baslangic 2026-09-18 --bitis 2026-09-24 [--repo .] [--cikti y.json]
ÇIKIŞ: 0 envanter üretildi · 1 bir kaynak okunamadı (eksik D BASILMAZ — uydurma yasağı) ·
2 kullanım/pencere hatası. `--cikti` yoksa JSON stdout'a, varsa dosyaya ve stdout'a tek satır özet.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys

# Betik olarak koşulduğunda `sys.path[0]` bu dosyanın dizinidir (ops/) — düz ithal yeter; depo kökü
# ELLE yola eklenmez (o, `meridian`ı ithal yoluna açardı).
from kart_benzer import normalize_tokens

SEMA = 1
ROADMAP = "ROADMAP.md"
GUNLUK = "MERIDIAN_ENGINEERING_LOG.md"
KART_DIZINI = "research/cards"
ATIF_TURLERI = ("sayfa", "recall", "memory", "kart_benzer", "bos_beyan", "diger")
BASLIK_SINIRI = 160
SEGMENT_SINIRI = 240
SIR_BENZERI_ASGARI = 24
GIZLI_YER = "‹gizlendi›"

KARAR_ISARETLERI = (
    ("karar", re.compile(r"\bKARAR")),
    ("karar", re.compile(r"(?i)\b(?:operatör|rol-1)\S*\s+karar")),
    ("karar", re.compile(r"(?i)\bkarar(?:ı|lar|ları)?\s*[(\[]?\s*(?:operatör|rol-1)")),
    ("hukum", re.compile(r"HÜKÜM|HÜKMÜ|(?i:\bhükm?ü\w*\s*:)|(?i:\b(?:rol-1|operatör)\S*\s+hükmü)")),
    ("ruling", re.compile(r"(?i)\bruling\b")),
    ("on_kayit", re.compile(r"ÖN-KAYIT")),
    ("durum", re.compile(r"→\s*(?:ACTIVE|GATED|DONE|DROPPED|QUEUED|OPERATOR)\b"
                         r"|\b(?:DROPPED|KAPANDI|REDDEDİLDİ|YÜKSELTİLDİ)\b"
                         r"|(?i:→\s*(?:measuring|measured|archived)\b)")),
    ("ayar", re.compile(r"(?i)\bayar(?:ı|lar|ları)?\s*(?:değişikliği|:)")),
)
GIT_KURAL_ISARETI = ("kural", re.compile(r"CLAUDE\.md\s*§\s*\d"))
_UCLU_HUKUM = re.compile(r"(?i)üçlü\s+hükm?\w*")

_KIMLIK = re.compile(r"(?<![A-Za-z0-9])(TSK-\d{3,4}|PRG-\d{2}|(?:EDG|EXE|BASE)-\d{4}-\d{3}"
                     r"|(?:EDG|EXE|BASE)-\d{3})(?![0-9])")
_TARIH = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

_RM_KALEM = re.compile(r"^(?:- )?\*\*\[([A-Z]+-[0-9-]+)\].*?\*\* — status: ")
_RM_KAPANIS = re.compile(r"\*\* — status: (?:DONE|DROPPED)\((\d{4}-\d{2}-\d{2})")
NOT_TARIH_PENCERESI = 60
_RM_KALEM_BASI = re.compile(r"^(?:- )?\*\*\[|^#")
_RM_WHAT = re.compile(r"^\s+What:\s*(.*)$")

_KART_ANAHTAR = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:")
_KART_KARAR_ANAHTARI = re.compile(r"^(?:on_kayit|hukum\w*|karar\w*|operator_karar\w*)$")
_ANAHTAR_TARIHI = re.compile(r"_(\d{4})_(\d{2})_(\d{2})$")
_KART_DOSYA_KIMLIGI = re.compile(r"^([A-Z]+-\d{4}-\d{3})")

#: "hafıza:" · "HAFIZA KONTROLÜ (…):" · "HAFIZA ATFI [… 18:2xZ …]:" — etiketten sonra tek büyük harfli
#: sözcük ve bir parantez/köşeli grup (içinde saat gibi ':' olabilir) izinlidir.
_SEGMENT_BASI = re.compile(r"(?:\b[Hh]afıza|\bHAFIZA(?:\s+[A-ZÇĞİÖŞÜ]+)?)\s*(?:[(\[][^)\]\n]*[)\]])?\s*:")
#: Tırnak/backtick'ten HEMEN sonra gelen "kaynak: …" kuralın BİÇİMİNİN alıntısıdır, atıf değil — kuru
#: koşumda (2026-09-25) EDG-089 hükmü "hiçbir karara `kaynak: zihin modeli <ad> v<n>` atfı yazılmadı"
#: cümlesiyle sahte 'sayfa' sayılmıştı; atfın KONUSU olan kararlar tam da bu biçimi alıntılar.
_KAYNAK_ATIF = re.compile(r"(?i)(?<![`'\"‘’“”])\bkayna(?:k|ğı)\s*:\s*(zihin\s+modeli|sayfa|recall|memory|kart_benzer)")
_MEMORY_ALINTI = re.compile(r"\bmemory\s+`[a-z0-9çğıöşü-]+`")
_NOT_ADI = re.compile(r"(?<![\w/.-])[a-zçğıöşü][a-z0-9çğıöşü]*(?:-[a-z0-9çğıöşü]+){2,}(?![\w/.-])")
_BOS_BEYAN = re.compile(r"(?i)kayıt\s+yok|benzer\s+yok")


class KaynakHatasi(Exception):
    """Bir kaynak okunamadı — eksik D basılmaz (uydurma yasağı)."""


# ------------------------------------------------------------------------------------------------
# ORTAK
# ------------------------------------------------------------------------------------------------

def karar_isaretleri(metin: str, *, git: bool = False) -> list[str]:
    temiz = _UCLU_HUKUM.sub(" ", metin)
    isaretler = [ad for ad, desen in KARAR_ISARETLERI if desen.search(temiz)]
    if git and GIT_KURAL_ISARETI[1].search(temiz):
        isaretler.append(GIT_KURAL_ISARETI[0])
    return sorted(set(isaretler))


def _segmentler(metin: str):
    for m in _SEGMENT_BASI.finditer(metin):
        parca = metin[m.end(): m.end() + SEGMENT_SINIRI]
        kesimler = [i for i in (parca.find(")"), parca.find("]"), parca.find("\n\n")) if i != -1]
        yield parca[: min(kesimler)] if kesimler else parca


def _segment_turleri(segment: str) -> set[str]:
    turler: set[str] = set()
    if re.search(r"(?i)zihin\s+modeli|sayfa_oku", segment):
        turler.add("sayfa")
    if re.search(r"(?i)recall|hafiza_sor", segment):
        turler.add("recall")
    if "kart_benzer" in segment:
        turler.add("kart_benzer")
    if re.search(r"(?i)\bmemory\b", segment) or ("sayfa" not in turler and _NOT_ADI.search(segment)):
        turler.add("memory")
    if not turler:
        turler.add("bos_beyan" if _BOS_BEYAN.search(segment) else "diger")
    return turler


def atif_turleri(metin: str) -> set[str]:
    """Metindeki hafıza atıflarının türleri (kural modül başlığında)."""
    turler: set[str] = set()
    for m in _KAYNAK_ATIF.finditer(metin):
        sozcuk = " ".join(m.group(1).lower().split())
        turler.add("sayfa" if sozcuk in ("zihin modeli", "sayfa") else sozcuk)
    if _MEMORY_ALINTI.search(metin):
        turler.add("memory")
    if "kart_benzer" in metin:
        turler.add("kart_benzer")
    for segment in _segmentler(metin):
        turler |= _segment_turleri(segment)
    return turler


def _sir_benzeri(jeton: str) -> bool:
    return (len(jeton) >= SIR_BENZERI_ASGARI and any(c.isdigit() for c in jeton)
            and any(c.isalpha() for c in jeton))


def _baslik(metin: str) -> str:
    ilk = " ".join((metin or "").split())
    ilk = re.sub(r"[A-Za-z0-9_+/=-]{%d,}" % SIR_BENZERI_ASGARI,
                 lambda m: GIZLI_YER if _sir_benzeri(m.group(0)) else m.group(0), ilk)
    return ilk if len(ilk) <= BASLIK_SINIRI else ilk[:BASLIK_SINIRI].rstrip() + "…"


def _tarih_ayikla(metin: str):
    for m in _TARIH.finditer(metin):
        try:
            yield _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:  # sessiz-yutma: takvimde olmayan '2026-13-45' biçimli metin tarih DEĞİLDİR, atlanır
            continue


def _birincil_kimlik(baslik: str, harita: dict[str, str]) -> str | None:
    for m in _KIMLIK.finditer(baslik):
        kimlik = harita.get(m.group(1), m.group(1))
        if not kimlik.startswith("PRG-"):
            return kimlik
    return None


def _blob_sha(veri: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(veri) + veri).hexdigest()


def _oku(yol: pathlib.Path) -> str:
    try:
        return yol.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise KaynakHatasi(f"{yol.name} okunamadı ({type(e).__name__}: {e})") from e


# ------------------------------------------------------------------------------------------------
# KAYNAKLAR — her biri (tarih, kayıt) üretir; kayıt: tur, ref, tarih, kimlik, baslik, metin, isaretler
# ------------------------------------------------------------------------------------------------

def git_kayitlari(repo: pathlib.Path, harita: dict[str, str]) -> list[dict]:
    try:
        r = subprocess.run(["git", "-C", str(repo), "log", "--format=%H%x1f%cI%x1f%B%x1e"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        raise KaynakHatasi(f"git log koşamadı ({type(e).__name__}: {e})") from e
    if r.returncode != 0:
        raise KaynakHatasi(f"git log çıkış {r.returncode}: {r.stderr.strip()[:200]}")
    kayitlar = []
    for ham in r.stdout.split("\x1e"):
        ham = ham.lstrip("\n")
        if not ham.strip():
            continue
        sha, tarih_s, mesaj = ham.split("\x1f", 2)
        konu = mesaj.split("\n", 1)[0].strip()
        if konu.startswith("Günlük"):
            continue
        isaretler = karar_isaretleri(konu, git=True)
        tarih = _dt.datetime.fromisoformat(tarih_s).astimezone(_dt.timezone.utc).date()
        kayitlar.append({"tur": "git", "ref": {"tur": "git", "commit": sha[:8]}, "tarih": tarih,
                         "kimlik": _birincil_kimlik(konu, harita), "baslik": konu,
                         "metin": mesaj, "isaretler": isaretler})
    return kayitlar


def _ust_parantezler(metin: str) -> list[str]:
    """Metnin BAŞINDAKİ üst düzey parantezli notlar (dengeli); ilk düz metinde durur."""
    notlar, i = [], 0
    while True:
        while i < len(metin) and metin[i].isspace():
            i += 1
        if i >= len(metin) or metin[i] != "(":
            return notlar
        derinlik, j = 0, i
        for j in range(i, len(metin)):
            if metin[j] == "(":
                derinlik += 1
            elif metin[j] == ")":
                derinlik -= 1
                if derinlik == 0:
                    break
        notlar.append(metin[i: j + 1])
        i = j + 1


def roadmap_kayitlari(metin: str, harita: dict[str, str]) -> list[dict]:
    satirlar = metin.splitlines()
    kayitlar = []
    for i, satir in enumerate(satirlar):
        m = _RM_KALEM.match(satir)
        if not m:
            continue
        kimlik = harita.get(m.group(1), m.group(1))
        k = _RM_KAPANIS.search(satir)
        if k:
            kayitlar.append({"tur": "roadmap", "ref": {"tur": "roadmap", "satir": i + 1},
                             "tarih": _dt.date.fromisoformat(k.group(1)), "kimlik": kimlik,
                             "baslik": satir.strip(), "metin": satir, "isaretler": ["durum"]})
        for j, sonraki in enumerate(satirlar[i + 1:], i + 2):
            if _RM_KALEM_BASI.match(sonraki):
                break
            w = _RM_WHAT.match(sonraki)
            if not w:
                continue
            for n, not_metni in enumerate(_ust_parantezler(w.group(1)), 1):
                tarih = next(_tarih_ayikla(not_metni[:NOT_TARIH_PENCERESI]), None)
                if tarih is None:
                    continue
                kayitlar.append({"tur": "roadmap", "ref": {"tur": "roadmap", "satir": j, "not": n},
                                 "tarih": tarih, "kimlik": kimlik,
                                 "baslik": f"[{kimlik}] {not_metni}", "metin": not_metni,
                                 "isaretler": karar_isaretleri(not_metni)})
            break
    return kayitlar


def _kart_bloklari(metin: str) -> tuple[str, list[tuple[str, int, str]]]:
    """(baş yorum bloğu, [(anahtar, satır no, blok metni)])."""
    bas: list[str] = []
    bloklar: list[list] = []
    for i, satir in enumerate(metin.splitlines(), 1):
        m = _KART_ANAHTAR.match(satir)
        if m:
            bloklar.append([m.group(1), i, [satir]])
        elif bloklar:
            bloklar[-1][2].append(satir)
        else:
            bas.append(satir)
    bas_metni = " ".join(s.lstrip("#").strip() for s in bas if s.strip())
    return bas_metni, [(a, n, "\n".join(s)) for a, n, s in bloklar]


def _ilk_deger(blok: str) -> str:
    """Anahtarın değerinin ilk satırı (blok skaler `>`/`|` ise bir sonraki dolu satır)."""
    satirlar = blok.split("\n")
    deger = satirlar[0].split(":", 1)[1].split("#", 1)[0].strip()
    if deger in ("", ">", "|", ">-", "|-"):
        deger = next((s.strip() for s in satirlar[1:]
                      if s.strip() and not s.strip().startswith("#")), "")
    return deger


def kart_kayitlari(kart_dizini: pathlib.Path, harita: dict[str, str], tarihsiz: dict) -> tuple[list[dict], int]:
    kayitlar = []
    dosyalar = sorted(kart_dizini.glob("*.yaml"))
    for yol in dosyalar:
        metin = _oku(yol)
        bas, bloklar = _kart_bloklari(metin)
        card_id = next((b.split(":", 1)[1].split("#", 1)[0].strip().strip("'\"")
                        for a, _n, b in bloklar if a == "card_id"), "")
        if not card_id:
            m = _KART_DOSYA_KIMLIGI.match(yol.stem)
            card_id = m.group(1) if m else yol.stem
        for anahtar, satir_no, blok in bloklar:
            if not _KART_KARAR_ANAHTARI.match(anahtar):
                continue
            son_ek = _ANAHTAR_TARIHI.search(anahtar)
            if son_ek:
                tarih = _dt.date(*map(int, son_ek.groups()))
            else:
                tarih = next(_tarih_ayikla(blok), None)
            if tarih is None:
                tarihsiz["kart"] = tarihsiz.get("kart", 0) + 1
                continue
            govde = (bas + "\n" + blok) if anahtar == "on_kayit" else blok
            kayitlar.append({
                "tur": "kart",
                "ref": {"tur": "kart", "dosya": f"{KART_DIZINI}/{yol.name}", "alan": anahtar,
                        "satir": satir_no},
                "tarih": tarih, "kimlik": harita.get(card_id, card_id),
                "baslik": f"{card_id} {anahtar}: {_ilk_deger(blok)}",
                "metin": govde,
                "isaretler": ["on_kayit" if anahtar == "on_kayit" else "hukum"]})
    return kayitlar, len(dosyalar)


def gunluk_kayitlari(metin: str, harita: dict[str, str], tarihsiz: dict) -> list[dict]:
    birimler: list[dict] = []
    tarih = None
    for i, satir in enumerate(metin.splitlines(), 1):
        if re.match(r"^#{1,6} ", satir):
            tarihler = list(_tarih_ayikla(satir))
            if tarihler:
                tarih = max(tarihler)
            birimler.append({"satir": i, "tarih": tarih, "satirlar": [satir]})
        elif satir.startswith("- "):
            birimler.append({"satir": i, "tarih": tarih, "satirlar": [satir]})
        elif birimler:
            birimler[-1]["satirlar"].append(satir)
    kayitlar = []
    for b in birimler:
        govde = "\n".join(b["satirlar"])
        isaretler = karar_isaretleri(govde)
        if b["tarih"] is None:
            if isaretler:
                tarihsiz["gunluk"] = tarihsiz.get("gunluk", 0) + 1
            continue
        baslik = b["satirlar"][0]
        kayitlar.append({"tur": "gunluk", "ref": {"tur": "gunluk", "satir": b["satir"]},
                         "tarih": b["tarih"], "kimlik": _birincil_kimlik(baslik, harita),
                         "baslik": baslik.strip(), "metin": govde, "isaretler": isaretler})
    return kayitlar


def kisa_kimlik_haritasi(kart_dizini: pathlib.Path) -> dict[str, str]:
    """`EDG-085` → `EDG-2026-085` — yalnız kart dosyalarında TEK eşleşme varsa (yıl UYDURULMAZ)."""
    adaylar: dict[str, set[str]] = {}
    for yol in kart_dizini.glob("*.yaml"):
        m = _KART_DOSYA_KIMLIGI.match(yol.stem)
        if not m:
            continue
        tam = m.group(1)
        onek, _yil, no = tam.split("-")
        adaylar.setdefault(f"{onek}-{no}", set()).add(tam)
    return {kisa: next(iter(t)) for kisa, t in adaylar.items() if len(t) == 1}


# ------------------------------------------------------------------------------------------------
# BİRLEŞTİRME VE ÇIKTI
# ------------------------------------------------------------------------------------------------

def birlestir(kayitlar: list[dict]) -> tuple[list[dict], int, int]:
    """Karar kayıtlarını anahtarla gruplar, sonra işaretsiz kayıtları VAR OLAN gruplara destek
    olarak ekler. Dönüş: (kararlar, atılan sır-benzeri jeton, eklenen destek)."""
    gruplar: dict[tuple, dict] = {}
    atilan = 0
    for k in (k for k in kayitlar if k["isaretler"]):
        anahtar = ((k["tarih"], k["kimlik"]) if k["kimlik"]
                   else (k["tarih"], None, k["tur"], json.dumps(k["ref"], sort_keys=True)))
        g = gruplar.setdefault(anahtar, {"tarih": k["tarih"], "kimlik": k["kimlik"],
                                         "baslik": _baslik(k["baslik"]), "kaynaklar": [],
                                         "isaretler": set(), "turler": set(), "tokenler": set()})
        g["kaynaklar"].append(k["ref"])
        g["isaretler"].update(k["isaretler"])
        g["turler"] |= atif_turleri(k["metin"])
        for jeton in normalize_tokens(k["metin"]):
            if _sir_benzeri(jeton):
                atilan += 1
            else:
                g["tokenler"].add(jeton)
    destek = 0
    for k in (k for k in kayitlar if not k["isaretler"] and k["kimlik"]):
        g = gruplar.get((k["tarih"], k["kimlik"]))
        if g is None:
            continue
        g["kaynaklar"].append(dict(k["ref"], destek=True))
        g["turler"] |= atif_turleri(k["metin"])
        destek += 1
    kararlar = []
    for g in gruplar.values():
        turler = sorted(g["turler"])
        kararlar.append({
            "tarih": g["tarih"].isoformat(), "kimlik": g["kimlik"], "baslik": g["baslik"],
            "kaynaklar": g["kaynaklar"], "isaretler": sorted(g["isaretler"]),
            "atif_var": bool(turler), "atif_turleri": turler,
            "konu_tokenleri": sorted(g["tokenler"]),
        })
    kararlar.sort(key=lambda k: (k["tarih"], k["kimlik"] or "~", k["baslik"]))
    return kararlar, atilan, destek


def envanter(repo: pathlib.Path, baslangic: _dt.date, bitis: _dt.date) -> dict:
    kart_dizini = repo / KART_DIZINI
    if not kart_dizini.is_dir():
        raise KaynakHatasi(f"{KART_DIZINI} dizini yok")
    roadmap_metni = _oku(repo / ROADMAP)
    gunluk_metni = _oku(repo / GUNLUK)
    harita = kisa_kimlik_haritasi(kart_dizini)
    tarihsiz: dict[str, int] = {}
    kart, kart_sayisi = kart_kayitlari(kart_dizini, harita, tarihsiz)
    tum = (git_kayitlari(repo, harita) + roadmap_kayitlari(roadmap_metni, harita) + kart
           + gunluk_kayitlari(gunluk_metni, harita, tarihsiz))
    pencere = [k for k in tum if baslangic <= k["tarih"] <= bitis]
    sayilar = {t: sum(1 for k in pencere if k["tur"] == t and k["isaretler"])
               for t in ("git", "roadmap", "kart", "gunluk")}
    kararlar, atilan, destek = birlestir(pencere)
    dagilim = {"atifli": sum(1 for k in kararlar if k["atif_var"]),
               "yok": sum(1 for k in kararlar if not k["atif_var"])}
    dagilim.update({t: sum(1 for k in kararlar if t in k["atif_turleri"]) for t in ATIF_TURLERI})
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                          text=True, timeout=60)
    return {
        "sema": SEMA, "arac": "ops/karar_envanteri.py",
        "tanim": "CLAUDE.md §2 'Bir karar / ruling / ayar değişikliği yazmak' — sezgisel kurallar araç başlığında",
        "pencere": {"baslangic": baslangic.isoformat(), "bitis": bitis.isoformat(), "saat_dilimi": "UTC"},
        "girdi": {
            "head": head.stdout.strip() if head.returncode == 0 else None,
            "dosyalar": {ROADMAP: _blob_sha(roadmap_metni.encode("utf-8")),
                         GUNLUK: _blob_sha(gunluk_metni.encode("utf-8"))},
            "kart_sayisi": kart_sayisi,
        },
        "D": len(kararlar),
        "atif_dagilimi": dagilim,
        "kaynak_kayit_sayilari": sayilar,
        "tarihsiz_atlanan": tarihsiz,
        "sir_benzeri_atilan": atilan,
        "destek_eklenen": destek,
        "kararlar": kararlar,
    }


def ozet_satiri(veri: dict) -> str:
    d = veri["atif_dagilimi"]
    turler = " · ".join(f"{t} {d[t]}" for t in ATIF_TURLERI)
    return f"D={veri['D']} · atıflı {d['atifli']} · yok {d['yok']} · {turler}"


def _tarih(s: str) -> _dt.date:
    try:
        return _dt.date.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"'{s}' YYYY-AA-GG değil") from e


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-103 SAYAÇ-0: penceredeki kararlar ve hafıza atıfları "
                                             "(LLM'siz, deterministik; hüküm VERMEZ).")
    ap.add_argument("--baslangic", required=True, help="pencere başı (UTC, dâhil) YYYY-AA-GG")
    ap.add_argument("--bitis", required=True, help="pencere sonu (UTC, dâhil) YYYY-AA-GG")
    ap.add_argument("--repo", default=".", help="depo kökü (varsayılan .)")
    ap.add_argument("--cikti", help="JSON'u bu dosyaya yaz; stdout'a tek satır özet basılır")
    a = ap.parse_args(argv)
    try:
        bas, bit = _tarih(a.baslangic), _tarih(a.bitis)
    except ValueError as e:
        print(f"HATA: pencere tarihi geçersiz: {e}", file=sys.stderr)
        return 2
    if bit < bas:
        print(f"HATA: pencere ters: --bitis {bit} < --baslangic {bas}", file=sys.stderr)
        return 2
    try:
        veri = envanter(pathlib.Path(a.repo), bas, bit)
    except KaynakHatasi as e:
        print(f"HATA: kaynak okunamadı — envanter BASILMADI: {e}", file=sys.stderr)
        return 1
    metin = json.dumps(veri, ensure_ascii=False, indent=2) + "\n"
    if a.cikti:
        pathlib.Path(a.cikti).write_text(metin, encoding="utf-8")
        print(f"{ozet_satiri(veri)} → {a.cikti}")
    else:
        sys.stdout.write(metin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
