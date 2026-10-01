#!/usr/bin/env python3
"""research/olcumler/edg103_okuma_ilgi_atif/dondur.py — EDG-2026-103 sayımının GİRDİSİNİ dondurur.

NE YAPAR. `sayim.py` yalnız dondurulmuş bir dizini okur; bu betik o dizini Rol-1'in checkout'unda kurar ve
her dosyayı `SHA256.txt` ile içerik-adresler. A1'e BAĞLANMAZ: okuma kaydını ve sayfa anlık görüntülerini
Rol-1 ssh ile çeker ve dosya (ya da `--okuma-kaydi -` ile stdin) olarak verir. Git'e YALNIZ salt-okur
alt komutlarla gider (`rev-parse`, `status`, `log`, `show`); `meridian`ı İTHAL ETMEZ (obs'a ulaşmaz).

OKUYUCU (Yasa 6): `sayim.py` — ürettiği her dosyayı `say()` okur (dosya listesi `sayim.GIRDI_DOSYALARI`).

ÜRETTİĞİ DİZİN (`--girdi`, var olmamalı ya da boş olmalı — dondurulmuş girdi sessizce EZİLMEZ):
  kart.yaml, kart_acilis.yaml   kart HEAD'deki hâli + `pencere_acilis_*` alanının GİRİŞ commit'indeki hâli
  okuma.jsonl                   Rol-1'in A1'den çektiği kayıt, baytı baytına
  sayfalar/<kimlik>.md          Rol-1'in çektiği `sayfa_oku.sh <kimlik>` çıktıları, baytı baytına
  karar_envanteri.json          `karar_envanteri.envanter()` çıktısı (İTHAL; araç CLI'ıyla aynı biçim)
  karar_zamanlari.json          her kararın commit damgası + sentetik işareti (aşağıda)
  kunye.json                    dondurma anı, HEAD, kart/enstrümantasyon ilk commit'i, §0-5 kural izi, PK/NK zamanı
  SHA256.txt                    yukarıdakilerin sha256'sı

KARAR DAMGASI (netleştirme (2): pencere ve D commit damgasıyla). Envanter kararı GÜN olarak verir; damga
burada kararın KAYNAKLARINDAN türetilir: git kaynağı → commit'in kendi zamanı (envanterle aynı `%cI`,
UTC'ye çevrilir); ROADMAP/günlük/kart kaynağı → o metnin GİRİŞ commit'i: kaynağın HEAD'deki satırından
HEAD içeriğinde TEKİL olan en kısa önek (≥80 karakter; ROADMAP DONE/DROPPED başlığında durum tarihini
de kapsar; kartta anahtar satırının tamamı; günlük biriminde önce karar İŞARETİ taşıyan ilk satır, sonra
birimin ilk satırı — `kaynak_adaylari`) `git log --reverse -S<önek>` ile aranır, İLK commit alınır.
Önek sayımı değiştirmeyen sonraki düzenlemeler (aynı satıra yeni not eklenmesi, arşive taşıma) damgayı
DEĞİŞTİRMEZ — satır-temelli `blame` bunları sonraki commit'e yazardı. Kararın damgası destek OLMAYAN
kaynaklarının en erkenidir (karar ilk yazıldığı an). Tekil önek bulunamazsa damga None + neden; sayım
o durumda hesap YAPMAZ (uydurma yasağı).
BEDELİ: önekin ilk 80 karakteri sonradan düzeltilirse damga düzeltme commit'ine kayar; aynı öneki daha
önce taşımış, sonra silinmiş bir metin varsa damga ona kayar (ikisi de nadir; künyede önek uzunluğu
ve commit kaynak başına yazılır, denetlenebilir).

SENTETİK İŞARET (kill #7): destek olmayan herhangi bir kaynağının metni kartın `[PK-…]`/`[NK-…]`
işaretini taşıyan karar `sentetik_isaretler` alır; sayım onu D'den çıkarıp AYRI listeler.

SIR DENETİMİ (kill #5, netleştirme b (10)): dondurulacak HER dosya yazılmadan önce `sayim.notify_taramasi` ile
(notify sır desenleri — yanlış-pozitifsiz katman) taranır; eşleşmede hiçbir şey yazılmaz, stderr'e yalnız dosya adı +
satır no + desen adı basılır (değer asla).

ÇIKIŞ: 0 donduruldu · 1 girdi eksik (gerekli sayfa anlık görüntüsü — kimlikleri ve çekme komutu stderr'e),
sır deseni eşleşti ya da git/kaynak okunamadı · 2 kullanım (kirli ağaç, dolu hedef dizin, biçimsiz `--sayfa`, kart yok).

CLI (sözleşme KOMUT SATIRIdır; Rol-1, ana checkout'ta, pencere KAPANDIKTAN sonra):
    .venv/bin/python research/olcumler/edg103_okuma_ilgi_atif/dondur.py --repo . \\
        --okuma-kaydi <okuma.jsonl | -> --sayfa <kimlik>=<dosya> [--sayfa …] --girdi <dizin> [--kenar-gun 7]
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

import sayim as SAYIM  # aynı dizin: betik olarak koşulunca sys.path[0]

KE = SAYIM.KE
UTC = SAYIM.UTC
ARAC = "research/olcumler/edg103_okuma_ilgi_atif/dondur.py"
KART_DESENI = "EDG-2026-103-*.yaml"
ANAHTAR_ASGARI = 80
#: Kaynak dosyalar: damgalar git'ten okunur, içerik çalışma ağacından — ikisi aynı olmalı (temiz ağaç).
IZLENEN = ("ROADMAP.md", "MERIDIAN_ENGINEERING_LOG.md", "research/cards", "CLAUDE.md")
_KIMLIK_BICIMI = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_DURUM_TARIHI = re.compile(r"status:\s*(?:DONE|DROPPED)\(\d{4}-\d{2}-\d{2}")


class DondurmaHatasi(Exception):
    """git ya da kaynak okunamadı (çıkış 1)."""


class KullanimHatasi(Exception):
    """Kullanım/ön koşul ihlali (çıkış 2)."""


def git(repo: pathlib.Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        raise DondurmaHatasi(f"git {args[0]} koşamadı ({type(e).__name__})") from e
    if r.returncode != 0:
        raise DondurmaHatasi(f"git {args[0]} çıkış {r.returncode}: {r.stderr.strip()[:200]}")
    return r.stdout


def _commit(satir: str) -> dict:
    sha, zaman = satir.split("\x1f", 1)
    return {"commit": sha, "zaman": SAYIM.an(zaman.strip()).isoformat()}


def ilk_commit(repo, yol: str) -> dict:
    satirlar = [s for s in git(repo, "log", "--reverse", "--format=%H%x1f%cI", "--", yol).splitlines() if s.strip()]
    if not satirlar:
        raise DondurmaHatasi(f"{yol} için commit yok")
    return _commit(satirlar[0])


def giris_commiti(repo, dosya: str, anahtar: str) -> dict | None:
    """`anahtar`ın `dosya`daki adedini DEĞİŞTİREN en eski commit — metnin giriş anı."""
    for satir in git(repo, "log", "--reverse", "--format=%H%x1f%cI", f"-S{anahtar}", "--", dosya).splitlines():
        if satir.strip():
            return _commit(satir)
    return None


def anahtar_sec(icerik: str, satir: str, asgari: int) -> tuple[str | None, str | None]:
    """HEAD içeriğinde tekil en kısa önek (asgari, 2×, 4×, tam satır)."""
    satir = satir.rstrip()
    for n in sorted({min(len(satir), asgari * k) for k in (1, 2, 4)} | {len(satir)}):
        onek = satir[:n]
        if not onek.strip():
            continue
        adet = icerik.count(onek)
        if adet == 1:
            return onek, None
        if adet == 0:
            return None, "önek HEAD içeriğinde yok"
    return None, "önek tekil değil (tam satır da birden çok kez geçiyor)"


def kaynak_adaylari(kayit: dict, icerik) -> list[tuple[str, str, int, str]]:
    """[(dosya, aday satır, asgari önek uzunluğu, adayın adı)] — sırayla denenir, ilk tekil önek kazanır.
    `icerik(dosya)` HEAD metnini verir. Günlük biriminde ÖNCE karar işareti taşıyan ilk satır denenir:
    eski bir başlığın altına sonradan eklenen KARAR paragrafının damgası başlığın değil kendi girişidir
    (başlık damgası onu pencere dışına iterdi — alt sayım); işaret satırlara bölünmüşse ya da o satır
    tekil değilse birimin ilk satırına düşülür ve hangisinin kullanıldığı künyeye yazılır."""
    ref = kayit["ref"]
    if ref["tur"] == "roadmap" and "not" in ref:
        return [(KE.ROADMAP, kayit["metin"], ANAHTAR_ASGARI, "not")]
    if ref["tur"] == "roadmap":
        satir = icerik(KE.ROADMAP).splitlines()[ref["satir"] - 1]
        m = _DURUM_TARIHI.search(satir)
        return [(KE.ROADMAP, satir, max(ANAHTAR_ASGARI, m.end() if m else 0), "durum_basligi")]
    if ref["tur"] == "gunluk":
        isaretli = next((s for s in kayit["metin"].splitlines() if s.strip() and KE.karar_isaretleri(s)), None)
        ilk = icerik(KE.GUNLUK).splitlines()[ref["satir"] - 1]
        return ([(KE.GUNLUK, isaretli, ANAHTAR_ASGARI, "isaretli_satir")] if isaretli else []) + \
            [(KE.GUNLUK, ilk, ANAHTAR_ASGARI, "ilk_satir")]
    if ref["tur"] == "kart":
        satir = icerik(ref["dosya"]).splitlines()[ref["satir"] - 1]
        return [(ref["dosya"], satir, len(satir), "anahtar_satiri")]
    raise DondurmaHatasi(f"bilinmeyen kaynak türü: {ref['tur']}")


def karar_zamanlari(repo, envanter: dict, kart: dict, harita: dict) -> list[dict]:
    tarihsiz: dict = {}
    kart_dizini = repo / KE.KART_DIZINI
    kayitlar = (KE.git_kayitlari(repo, harita)
                + KE.roadmap_kayitlari(git(repo, "show", f"HEAD:{KE.ROADMAP}"), harita)
                + KE.kart_kayitlari(kart_dizini, harita, tarihsiz)[0]
                + KE.gunluk_kayitlari(git(repo, "show", f"HEAD:{KE.GUNLUK}"), harita, tarihsiz))
    dizin = {json.dumps(k["ref"], sort_keys=True): k for k in kayitlar}
    commitler: dict[str, list[str]] = {}
    zamanlar: dict[str, str] = {}
    for satir in git(repo, "log", "--format=%H%x1f%cI").splitlines():
        if satir.strip():
            c = _commit(satir)
            commitler.setdefault(c["commit"][:8], []).append(c["commit"])
            zamanlar[c["commit"]] = c["zaman"]
    icerikler: dict[str, str] = {}

    def icerik(dosya: str) -> str:
        if dosya not in icerikler:
            icerikler[dosya] = git(repo, "show", f"HEAD:{dosya}")
        return icerikler[dosya]

    sonuc = []
    for i, k in enumerate(envanter["kararlar"]):
        kaynaklar, isaretler = [], set()
        for ref in k["kaynaklar"]:
            if ref.get("destek"):
                continue
            kayit = dizin.get(json.dumps(ref, sort_keys=True))
            if kayit is None:
                kaynaklar.append({"ref": ref, "zaman": None, "neden": "kaynak kaydı yeniden kurulamadı"})
                continue
            isaretler |= set(kart["isaret_deseni"].findall(kayit["metin"]))
            if ref["tur"] == "git":
                tam = commitler.get(ref["commit"], [])
                kaynaklar.append({"ref": ref, "commit": tam[0] if len(tam) == 1 else None,
                                  "zaman": zamanlar[tam[0]] if len(tam) == 1 else None,
                                  "neden": None if len(tam) == 1 else f"kısa sha {len(tam)} commit'e uyuyor"})
                continue
            onek = giris = None
            nedenler = []
            for dosya, satir, asgari, aday in kaynak_adaylari(kayit, icerik):
                onek, neden = anahtar_sec(icerik(dosya), satir, asgari)
                if onek:
                    break
                nedenler.append(f"{aday}: {neden}")
            if onek:
                giris = giris_commiti(repo, dosya, onek)
                if giris is None:
                    nedenler.append(f"{aday}: önek için giriş commit'i bulunamadı")
            neden = "; ".join(nedenler) or None
            kaynaklar.append({"ref": ref, "anahtar_kaynagi": aday if onek else None,
                              "onek_uzunlugu": None if onek is None else len(onek),
                              "onek_basi": None if onek is None else onek[:60],
                              "commit": None if giris is None else giris["commit"],
                              "zaman": None if giris is None else giris["zaman"], "neden": neden})
        damgalar = [SAYIM.an(x["zaman"]) for x in kaynaklar if x.get("zaman")]
        sonuc.append({"sira": i, "tarih": k["tarih"], "kimlik": k["kimlik"], "baslik": k["baslik"],
                      "zaman": min(damgalar).isoformat() if damgalar else None,
                      "zaman_neden": None if damgalar else "hiçbir kaynağın giriş commit'i bulunamadı",
                      "kaynaklar": kaynaklar, "sentetik_isaretler": sorted(isaretler)})
    return sonuc


def kural_izi(repo, anahtar: str, bas, son) -> list[dict]:
    """CLAUDE.md'ye dokunan commit'lerden pencere içindekiler + pencereden önceki SONUNCU: kural metni adedi."""
    commitler = [_commit(s) for s in git(repo, "log", "--format=%H%x1f%cI", "--", "CLAUDE.md").splitlines() if s.strip()]
    secilen = [c for c in commitler if SAYIM.pencerede(SAYIM.an(c["zaman"]), bas, son)]
    once = [c for c in commitler if SAYIM.an(c["zaman"]) < bas]
    if once:
        secilen.append(max(once, key=lambda c: SAYIM.an(c["zaman"])))
    return [dict(c, adet=git(repo, "show", f"{c['commit']}:CLAUDE.md").count(anahtar))
            for c in sorted(secilen, key=lambda c: SAYIM.an(c["zaman"]))]


def sayfa_argumanlari(degerler: list[str]) -> dict[str, pathlib.Path]:
    sayfalar = {}
    for d in degerler:
        kimlik, ayrac, yol = d.partition("=")
        if not ayrac or not _KIMLIK_BICIMI.fullmatch(kimlik) or ".." in kimlik:
            raise KullanimHatasi(f"--sayfa biçimi <kimlik>=<dosya> olmalı (kimlik [a-z0-9._-]): {d!r}")
        if kimlik in sayfalar:
            raise KullanimHatasi(f"--sayfa {kimlik} iki kez verildi")
        sayfalar[kimlik] = pathlib.Path(yol)
    return sayfalar


def dondur(repo: pathlib.Path, okuma_baytlari: bytes, sayfalar: dict, girdi: pathlib.Path, kenar_gun: int) -> dict:
    if girdi.exists() and any(girdi.iterdir()):
        raise KullanimHatasi(f"hedef dizin dolu: {girdi} — dondurulmuş girdi ezilmez, yeni dizin ver")
    kirli = git(repo, "status", "--porcelain", "--", *IZLENEN)
    if kirli.strip():
        raise KullanimHatasi("kaynak dosyalarda commit'lenmemiş değişiklik var — damga git'ten, içerik ağaçtan "
                             f"okunur, ayrışırlar: {' '.join(s[3:] for s in kirli.splitlines()[:5])}")
    kartlar = sorted((repo / KE.KART_DIZINI).glob(KART_DESENI))
    if len(kartlar) != 1:
        raise KullanimHatasi(f"{KE.KART_DIZINI}/{KART_DESENI} tek dosya değil: {[p.name for p in kartlar]}")
    kart_yolu = f"{KE.KART_DIZINI}/{kartlar[0].name}"
    kart_metni = git(repo, "show", f"HEAD:{kart_yolu}")
    kart = SAYIM.kart_coz(kart_metni)
    satirlar, _denetim = SAYIM.okuma_kaydi_oku(okuma_baytlari.decode("utf-8"))
    gercek = SAYIM.gercek_okumalar(satirlar, kart["bas"], kart["son"])
    gerekli = {r["kimlik"] for r in gercek} | {kart["pk"]["sayfa"], kart["ek_nk"]["sayfa"]}
    eksik = sorted(str(k) for k in gerekli if k not in sayfalar)
    if eksik:
        recete = "\n".join(f"  ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'HAFIZA_OKUMA_ETIKET=olcum-anlik "
                           f"~/bin/sayfa_oku.sh {k}' </dev/null > <scratch>/sayfa-{k}.md" for k in eksik)
        raise DondurmaHatasi(f"EKSİK SAYFA ANLIK GÖRÜNTÜSÜ: {', '.join(eksik)} — Rol-1 A1'den çeker (ardından "
                             f"okuma kaydını YENİDEN çeker; anlık görüntü satırları kayda düşer):\n{recete}")
    acilis_satiri = next((s for s in kart_metni.splitlines() if s.startswith(f"{kart['acilis_alani']}:")), None)
    acilis = giris_commiti(repo, kart_yolu, acilis_satiri) if acilis_satiri else None
    if acilis is None:
        raise DondurmaHatasi(f"{kart['acilis_alani']} alanının giriş commit'i bulunamadı")
    enstr_yolu = pathlib.Path(SAYIM.OKUMA.__file__).resolve().relative_to(SAYIM.KOK).as_posix()
    harita = KE.kisa_kimlik_haritasi(repo / KE.KART_DIZINI)
    envanter = KE.envanter(repo, kart["bas"].date() - _dt.timedelta(days=kenar_gun), kart["son"].date())
    zamanlar = karar_zamanlari(repo, envanter, kart, harita)
    kunye = {
        "sema": SAYIM.SEMA, "arac": ARAC, "dondurma_ani": _dt.datetime.now(UTC).replace(microsecond=0).isoformat(),
        "repo_head": git(repo, "rev-parse", "HEAD").strip(),
        "kart": {"yol": kart_yolu, "ilk_commit": ilk_commit(repo, kart_yolu), "acilis_alani": kart["acilis_alani"],
                 "acilis_commit": acilis},
        "enstrumantasyon": {"yol": enstr_yolu, "ilk_commit": ilk_commit(repo, enstr_yolu)},
        "kural_0_5": {"anahtar": kart["kural_anahtari"],
                      "iz": kural_izi(repo, kart["kural_anahtari"], kart["bas"], kart["son"])},
        "pk_nk_zamani": acilis["zaman"],
        "envanter": {"baslangic": (kart["bas"].date() - _dt.timedelta(days=kenar_gun)).isoformat(),
                     "bitis": kart["son"].date().isoformat(), "kenar_gun": kenar_gun},
    }
    yazilacak = {
        "kart.yaml": kart_metni.encode("utf-8"),
        "kart_acilis.yaml": git(repo, "show", f"{acilis['commit']}:{kart_yolu}").encode("utf-8"),
        "okuma.jsonl": okuma_baytlari,
        "karar_envanteri.json": (json.dumps(envanter, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        "karar_zamanlari.json": (json.dumps({"sema": SAYIM.SEMA, "kararlar": zamanlar}, ensure_ascii=False,
                                            indent=2) + "\n").encode("utf-8"),
        "kunye.json": (json.dumps(kunye, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    for kimlik, yol in sorted(sayfalar.items()):
        try:
            yazilacak[f"{SAYIM.SAYFA_DIZINI}/{kimlik}.md"] = yol.read_bytes()
        except OSError as e:
            raise DondurmaHatasi(f"sayfa dosyası okunamadı: {yol} ({type(e).__name__})") from e
    # kill #5 / netleştirme b (10): girdi DEPOYA girer → yazmadan ÖNCE her dosya notify sır desenleriyle taranır;
    # eşleşmede HİÇBİR ŞEY yazılmaz. Yalnız dosya adı, satır no ve desen adı basılır, değer ASLA (inceleme I4).
    bulgular = SAYIM.notify_taramasi({ad: bayt.decode("utf-8", errors="replace") for ad, bayt in yazilacak.items()})
    if bulgular:
        raise DondurmaHatasi(f"SIR DENETİMİ (kill #5): {len(bulgular)} notify desen eşleşmesi — girdi YAZILMADI: "
                             + "; ".join(f"{b['kaynak']} {b['yer']} {b['denetci']}" for b in bulgular[:20]))
    (girdi / SAYIM.SAYFA_DIZINI).mkdir(parents=True, exist_ok=True)
    for ad, bayt in yazilacak.items():
        (girdi / ad).write_bytes(bayt)
    ozetler = [f"{hashlib.sha256(b).hexdigest()}  {ad}" for ad, b in sorted(yazilacak.items())]
    (girdi / SAYIM.SHA_DOSYASI).write_text("\n".join(ozetler) + "\n", encoding="utf-8")
    return {"kararlar": len(zamanlar), "zamansiz": sum(1 for z in zamanlar if z["zaman"] is None),
            "sentetik": sum(1 for z in zamanlar if z["sentetik_isaretler"]), "head": kunye["repo_head"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-103 sayım girdisini dondurur (git salt-okur; A1'e bağlanmaz).")
    ap.add_argument("--repo", default=".", help="depo kökü (Rol-1 ana checkout'u)")
    ap.add_argument("--okuma-kaydi", required=True, help="A1'den çekilmiş okuma.jsonl yolu ya da '-' (stdin)")
    ap.add_argument("--sayfa", action="append", default=[], help="<kimlik>=<sayfa_oku.sh çıktısı dosyası>")
    ap.add_argument("--girdi", required=True, help="dondurulmuş dizin (var olmamalı ya da boş olmalı)")
    ap.add_argument("--kenar-gun", type=int, default=7,
                    help="envanter tarih aralığının pencere başından önceki kenarı (metin tarihi ≠ commit günü)")
    a = ap.parse_args(argv)
    try:
        sayfalar = sayfa_argumanlari(a.sayfa)
        okuma = sys.stdin.buffer.read() if a.okuma_kaydi == "-" else pathlib.Path(a.okuma_kaydi).read_bytes()
        ozet = dondur(pathlib.Path(a.repo).resolve(), okuma, sayfalar, pathlib.Path(a.girdi), a.kenar_gun)
    except KullanimHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 2
    except SAYIM.KartHatasi as e:
        print(f"HATA: kart çözümlenemedi: {e}", file=sys.stderr)
        return 2
    except (DondurmaHatasi, SAYIM.GirdiHatasi, KE.KaynakHatasi, OSError, UnicodeDecodeError) as e:
        print(f"HATA: girdi DONDURULMADI: {e}", file=sys.stderr)
        return 1
    print(f"donduruldu: {ozet['kararlar']} karar (zamansız {ozet['zamansiz']}, sentetik {ozet['sentetik']}) · "
          f"HEAD {ozet['head'][:8]} → {a.girdi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
