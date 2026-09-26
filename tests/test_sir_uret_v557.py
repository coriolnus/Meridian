"""test_sir_uret_v557.py — TSK-226c: kasa yolunda değeri betik İÇİNDE üretme seçeneği (`--uret`)
(2026-09-26).

NUMARA: `ls tests | grep _v557` boş (ana checkout + iki worktree tarandı 2026-09-26; en yüksek v556).

BAĞLAM (Rol-1 brief'i). TSK-226 sonrası kiracı anahtarı (`HINDSIGHT_API_TENANT_API_KEY`) döndürülecek.
`sir_rotasyon.sh --tenant --vault` genel kasa döngüsü (`vault_rotasyon`) değeri operatörden İSTER
(`_oku_gizli`, `read -rs`) ve komutları koşan Rol-1 bir isteme sır değeri GİREMEZ. Eski yol (`--tenant`)
değeri betik İÇİNDE üretir ama sır kasaya BAĞLI olduğu için yazımı Agent render'ıyla ezilir — o yol
kullanılamaz. `--uret` kasa yolunun İSTEM NOKTASININ yerine geçer: eski yolun AYNI üretim yöntemi
(`_uret` — alt komutun eski yolda kullandığı sınıf; kiracı `hex` 64), uzunluk denetimli, render hedefindeki
ESKİ değerle AYNI olamaz, hiçbir yere BASILMAZ. Akışın geri kalanı (takma ad · render kanıtı · eski kanal ·
restart · kanıt) AYNEN — yalnız değerin KAYNAĞI değişir (C3 bunu iz kıyasıyla ölçer).

DÜZENEK — ŞİMLER YENİDEN YAZILMADI: v556 `_cp_ortami` (v447 sahte kök + KV v2 sahte kasa + sahte Agent
[kanonik hedef + yan dosya satırları, eşleme envanterden] + CP-duyarlı systemctl/curl). Kiracı yolu
`hindsight-cp`yi de yeniden başlatır (takma ad `hindsight_cp_dataplane_api_key` → `.env-cp.vault`) ve
hazırlığı CP'nin `/api/health` ucuyla beklenir — o yüzden CP şimi gerekir. Kasa tohumu A1'in hâlini
modeller: kiracı yolu ESKİ değeri taşır (tek sürüm).

BÖLÜMLER
  A  sözleşme — üretim sınıfı eski yol gövdeleriyle ayrışmaz · beyan metni · başlık (RUNBOOK kaynağı)
  B  kuru — `--tenant --vault --uret --kuru`: istem yok · yazım yok · "sizden İSTER" YOK · plan aynen
  C  gerçek — `--tenant --vault --uret`: istem yok · 64 hex kasada · ESKİ ≠ YENİ · basılmaz · akış aynen
  D  `--uret` YOKKEN birebir — istem çağrılır, kuru metin değişmedi
  E  hata matrisi — `--vault`sız · `--openrouter` · `--db` → açık hata, istem/yazım/kasa YOK; `--cp` etkisiz
  F  ESKİ ile AYNI üretim → durur, kasaya yazım yok; render hedefi YOKSA kıyas ADIYLA atlanır
  M  MUTASYONLAR — brief'in dört mutasyonu (istem · değeri bas · üretim sınıfı · db kabul) + beyan ·
     kuru değer satırı · eşitlik kapısı · iki hata dalı

SIR DEĞERİ YOK: tohumlar `SAHTE-` önekli; üretilen değer YALNIZ test belleğinde ve sahte kasa JSON'unda
yaşar, hiçbir yüzeye (stdout · stderr · şim günlükleri · kasa argv'si) girmediği ölçülür.
ÇIKTI DİSİPLİNİ — İDDİA BOOL'A İNDİRİLİR (`_iddia`). pytest'in assert İÇGÖZLEMİ karşılaştırılan işlenenleri
HAM basar: liste farkında "At index 3 diff: '<değer>'", `r.returncode` iddiasında `CompletedProcess` repr'i
(stdout dahil). Ölçüldü 2026-09-26: "değeri bas" mutasyonunda üretilen değer tam oradan pytest çıktısına
düştü — maskeli iddia MESAJI yetmiyordu. Çıktı taşıyan her iddia `_iddia(bool, maskeli_mesaj)` ile
`pytest.fail`e gider; mesajlar yalnız ad/etiket ya da maskeli metin taşır (uzun jetonlar + bilinen tohumlar).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import subprocess

import pytest

from tests import test_cp_rotasyon_v556 as v556
from tests import test_rotasyon_operator_mesajlari_v522 as v522
from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_sir_rotasyon_v447 import BETIK, ENVANTER, ESKI, _dosya_imzalari, _env_alan, _kos, _sahte_ortam

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

SIR = "HINDSIGHT_API_TENANT_API_KEY"
KASA_YOLU = "secret/meridian/HINDSIGHT_API_TENANT_API_KEY"
HEDEF = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"   # Agent render hedefi = tablonun REFERANSI
KEY = "/opt/hindsight/.key"
DATAPLANE = "HINDSIGHT_CP_DATAPLANE_API_KEY"
TENANT_BIRIMLER = {"hindsight-api.service", "hindsight-cp.service", "meridian.service"}

#: Eski yolun değeri `_uret` ile ürettiği ve GENEL kasa döngüsünden geçen alt komutlar — ELLE (v522
#: DEGER_URETEN gerekçesi). `db` DIŞARIDA: eski yol üretir ama kasa yolu kendi dalıdır ve `--uret`
#: bu turun kapsamı dışıdır (brief). `cp` DIŞARIDA: kendi dalı değeri ZATEN üretir. A1 bu kümeyi
#: betiğin `_uret_sinifi`nden ve eski yol gövdelerinden AYRICA türetir.
URETILEBILIR = {"kapi", "tenant", "dash", "apisix-admin"}
TUM_ALTLAR = ("kapi", "tenant", "db", "dash", "openrouter", "apisix-admin", "cp")

ISTEM = "(boş = bu bacağı atla)"                 # `_oku_gizli`nin istem metni (stderr)
ISTEM_DEGERI = "SAHTE-ISTEM-0557"                # istem çağrılırsa kasaya giden değer budur
URET_BEYAN = "DEĞER KAYNAĞI: betik İÇİNDE üretilir (--uret)"
URET_PLAN = "  değer: betik İÇİNDE üretilir"     # kuru planın değer satırı (`--uret`)
SORULUR = "her kasa sırrı AYRI sorulur"          # kuru planın değer satırı (`--uret` YOK)
URETILDI = "yeni değer üretildi (hex, 64 karakter; DEĞER BASILMAZ)"
AYRI_SATIRI = "yeni değer render hedefindeki ESKİ değerden AYRI"
CAKISMA_SATIRI = "üretilen değer render hedefindeki ESKİ değerle AYNI"
KIYAS_YOK_SATIRI = "ESKİ değer kıyası YAPILAMADI"
ETKISIZ = "--uret bu yolda ETKİSİZDİR"

HATA_VAULTSUZ = "--uret yalnız --vault ile anlamlıdır"
HATA_OPENROUTER = "--uret --openrouter ile verilemez"
HATA_DB = "--db --vault --uret bu turun kapsamı DIŞI"

#: Sahte `openssl`: `rand -hex 32` SABİT bir değer verir (çakışma sahnesi — F1). Öteki çağrılar gerçek openssl.
SIM_OPENSSL_SABIT = '''#!/bin/sh
if [ "$1" = "rand" ] && [ "$2" = "-hex" ]; then echo "__SABIT__"; exit 0; fi
exec __ASIL__ "$@"
'''
#: Çakışma sahnesinin ortak değeri — 64 küçük hex (üretim biçimi), SAHTE.
CAKISMA_DEGERI = "5a" * 32

#: Maskelenecek bilinen tohumlar — iddia mesajına sahte değer bile düşmesin.
_TOHUMLAR = tuple(ESKI.values()) + (ISTEM_DEGERI, CAKISMA_DEGERI, v556.ESKI_CP, v556.ONCEKI_CP)


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _iddia(kosul: bool, mesaj: str) -> None:
    """Bool iddia — pytest içgözlemi işlenenleri basmaz (modül şerhi: ÇIKTI DİSİPLİNİ)."""
    if not kosul:
        pytest.fail(mesaj, pytrace=False)


def _ortam(tmp_path: pathlib.Path, **bayrak: str):
    """v556 CP dünyası + kiracı yolunun kasa tohumu (A1: kasa ESKİ kiracı değerini taşır)."""
    kok, ortam, log, durum = v556._cp_ortami(tmp_path, **bayrak)
    veri = json.loads(durum.read_text(encoding="utf-8"))
    veri[KASA_YOLU] = [ESKI["tenant"]]
    durum.write_text(json.dumps(veri), encoding="utf-8")
    return kok, ortam, log, durum


def _kasa(durum: pathlib.Path) -> list[str]:
    return json.loads(durum.read_text(encoding="utf-8")).get(KASA_YOLU, [])


def _dosya(kok: pathlib.Path, yol: str) -> str | None:
    p = kok / yol.lstrip("/")
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def _maskeli(metin: str) -> str:
    """İddia mesajı için: bilinen tohumlar ve uzun jetonlar (üretim biçimleri 48/64 karakter) maskelenir."""
    for d in _TOHUMLAR:
        metin = metin.replace(d, "<SAHTE-TOHUM>")
    return re.sub(r"[A-Za-z0-9_+=-]{40,}", "<UZUN-JETON>", metin)


def _ozet(r: subprocess.CompletedProcess) -> str:
    return (f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)}\n"
            f"--- stderr ---\n{_maskeli(r.stderr)}")


def _sizinti(r: subprocess.CompletedProcess, kok: pathlib.Path, log: pathlib.Path,
             *degerler: str) -> list[str]:
    """Değer ve sha256'sının ilk 8 hanesi hiçbir yüzeyde yok (v556 `_deger_yok` sözleşmesi, ihlal
    listesi biçiminde — mutasyon çivisi AYNI listeyi ısırır). Mesaj değeri BASMAZ, sırasını söyler."""
    yuzeyler = {"stdout": r.stdout, "stderr": r.stderr}
    for ad in ("argv.log", "url.log", "cp_istek.log", "systemctl.log"):
        p = kok / ".sahte" / ad
        if p.exists():
            yuzeyler[ad] = p.read_text(encoding="utf-8")
    if log.exists():
        yuzeyler["kasa argv"] = log.read_text(encoding="utf-8")
    ih = []
    for i, d in enumerate(degerler):
        if not d:
            continue
        h8 = hashlib.sha256(d.encode()).hexdigest()[:8]
        for etiket, metin in yuzeyler.items():
            if d in metin:
                ih.append(f"değer #{i} {etiket} içine düştü")
            if h8 in metin:
                ih.append(f"değer #{i} HASH'i {etiket} içine düştü")
    return ih


def _ihlaller_gercek(r: subprocess.CompletedProcess, kok: pathlib.Path, log: pathlib.Path,
                     durum: pathlib.Path) -> list[str]:
    """`--tenant --vault --uret` gerçek koşumunun BÜTÜN iddiaları — C1 ve mutasyon çivileri aynı liste."""
    ih = []
    if r.returncode != 0:
        ih.append(f"çıkış {r.returncode} (0 bekleniyordu)")
    if ISTEM in r.stderr:
        ih.append("istem basıldı — `_oku_gizli` çağrıldı")
    kasa = _kasa(durum)
    if len(kasa) != 2 or kasa[0] != ESKI["tenant"]:
        ih.append(f"kasaya TEK yeni sürüm yazılmadı ({len(kasa)} sürüm)")
    yeni = kasa[-1] if len(kasa) == 2 else ""
    if not re.fullmatch(r"[0-9a-f]{64}", yeni):
        ih.append("kasadaki yeni değer 64 küçük hex DEĞİL (eski yol `tenant()` → `_uret hex`)")
    if yeni in (ESKI["tenant"], ISTEM_DEGERI):
        ih.append("kasadaki yeni değer ESKİ değer ya da İSTEM değeri")
    kopyalar = (("render hedefi", _dosya(kok, HEDEF)),
                (".key", _dosya(kok, KEY)),
                (".env-cp DATAPLANE", _env_alan(kok / v556.ENV_CP.lstrip("/"), DATAPLANE)),
                (".env-cp.vault DATAPLANE (Agent)", _env_alan(kok / v556.ENV_CP_VAULT.lstrip("/"), DATAPLANE)))
    for etiket, deger in kopyalar:
        if not yeni or deger != yeni:
            ih.append(f"{etiket} kasadaki YENİ değerde DEĞİL")
    if set(v556._restartlar(kok)) != TENANT_BIRIMLER:
        ih.append(f"yeniden başlatılan birimler {sorted(set(v556._restartlar(kok)))} ≠ {sorted(TENANT_BIRIMLER)}")
    for metin in (URETILDI, URET_BEYAN, AYRI_SATIRI):
        if metin not in r.stdout:
            ih.append(f"stdout'ta yok: {metin!r}")
    if "sizden İSTER" in r.stdout:
        ih.append("'sizden İSTER' beyanı basıldı (--uret'te yalan beyan)")
    if (URETILDI in r.stdout and "kasaya yazıldı:" in r.stdout
            and r.stdout.index(URETILDI) > r.stdout.index("kasaya yazıldı:")):
        ih.append("üretim kasa yazımından SONRA")
    ih += _sizinti(r, kok, log, yeni, ESKI["tenant"])
    return ih


def _ihlaller_kuru(r: subprocess.CompletedProcess, kok: pathlib.Path, log: pathlib.Path,
                   durum: pathlib.Path, once: dict) -> list[str]:
    """`--tenant --vault --uret --kuru` — B1 ve mutasyon çivileri aynı liste."""
    ih = []
    if r.returncode != 0:
        ih.append(f"çıkış {r.returncode} (0 bekleniyordu)")
    if URET_BEYAN not in r.stdout:
        ih.append(f"stdout'ta yok: {URET_BEYAN!r}")
    if "sizden İSTER" in r.stdout:
        ih.append("'sizden İSTER' beyanı basıldı (--uret'te yalan beyan)")
    if SORULUR in r.stdout:
        ih.append("kuru plan 'her kasa sırrı AYRI sorulur' diyor (--uret'te yalan)")
    plan = [s for s in r.stdout.splitlines() if s.startswith(URET_PLAN)]
    if len(plan) != 1 or "(_uret hex)" not in plan[0]:
        ih.append("kuru planda TEK '  değer: betik İÇİNDE üretilir … (_uret hex)' satırı yok")
    if ISTEM in r.stderr:
        ih.append("istem basıldı — `_oku_gizli` çağrıldı")
    if _dosya_imzalari(kok) != once:
        ih.append("kuru koşum dosya yazdı")
    if v556._restartlar(kok):
        ih.append("kuru koşum birim yeniden başlattı")
    if log.exists():
        ih.append("kuru koşum kasaya çağrı yaptı")
    if _kasa(durum) != [ESKI["tenant"]]:
        ih.append("kuru koşum kasayı değiştirdi")
    ih += _sizinti(r, kok, log, ESKI["tenant"])
    return ih


def _hata_ihlalleri(r: subprocess.CompletedProcess, kok: pathlib.Path, log: pathlib.Path,
                    once: dict, beklenen: str) -> list[str]:
    """Hata matrisi: çıkış 1 · mesaj ADIYLA · HİÇBİR ŞEY koşmadı (stdout boş, istem yok, yazım yok,
    kasaya çağrı yok, restart yok)."""
    ih = []
    if r.returncode != 1:
        ih.append(f"çıkış {r.returncode} (1 bekleniyordu)")
    if beklenen not in r.stderr:
        ih.append(f"stderr'de yok: {beklenen!r}")
    if r.stdout:
        ih.append("stdout BOŞ değil — koşum başladı")
    if ISTEM in r.stderr:
        ih.append("istem basıldı")
    if _dosya_imzalari(kok) != once:
        ih.append("dosya yazıldı")
    if log.exists():
        ih.append("kasaya çağrı yapıldı")
    if v556._restartlar(kok):
        ih.append("birim yeniden başlatıldı")
    return ih


def _norm(metin: str, dizin: pathlib.Path) -> str:
    metin = metin.replace(str(dizin), "<T>")
    metin = re.sub(r"sir-rot\.[A-Za-z0-9]+", "sir-rot.X", metin)
    metin = re.sub(r"sir-yedek-\d{8}T\d{6}Z", "sir-yedek-TS", metin)
    # "credential dolu: … (65 bayt)" DEĞERİN uzunluğudur (istem değeri keyfî uzunlukta) — akışın değil.
    metin = re.sub(r"\(\d+ bayt\)", "(N bayt)", metin)
    return re.sub(r"\b\d+ s\b", "N s", metin)


def _deger_satirlari_ayir(metin: str) -> tuple[list[str], list[str]]:
    """(kalan, çıkan): değerin KAYNAĞINA ait satırlar çıkarılır — DEĞER KAYNAĞI beyanı (+ devam satırı),
    kuru planın `  değer:` satırı, istem, üretim/ayrılık/`--uret` satırları. Geri kalan her satır iki
    kipte BİREBİR olmalı."""
    kalan, cikan, devam = [], [], False
    for s in metin.splitlines():
        if devam and s.startswith("    ") and not s.startswith("    ·"):
            cikan.append(s)
            devam = False
            continue
        devam = False
        if "DEĞER KAYNAĞI" in s:
            cikan.append(s)
            devam = True
        elif (s.startswith("  değer: ") or ISTEM in s or "üretildi" in s or AYRI_SATIRI in s
              or "--uret" in s):
            cikan.append(s)
        else:
            kalan.append(s)
    return kalan, cikan


def _satirlar(etiket: str, satirlar: list[str]) -> str:
    return "\n".join([f"{etiket}:"] + [_maskeli(s) for s in satirlar])


def _agac(kok: pathlib.Path) -> dict[str, str]:
    return {p.relative_to(kok).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(kok.rglob("*")) if p.is_file() and ".sahte" not in p.parts}


def _iz(dizin: pathlib.Path, args: tuple[str, ...], girdi: str) -> dict:
    """Bir koşumun DAVRANIŞ izi — değerden bağımsız: hangi dosya YENİ/DEĞİŞTİ/AYNI, restart sırası,
    kasa/Agent olay sırası, kasa argv'si, sürüm sayısı, değer satırları çıkarılmış metin."""
    dizin.mkdir()
    kok, ortam, log, durum = _ortam(dizin)
    once = _agac(kok)
    r = _kos(BETIK, ortam, *args, girdi=girdi)
    sonra = _agac(kok)
    dosyalar = {}
    for rel in sorted(set(once) | set(sonra)):
        dosyalar[_norm(rel, dizin)] = ("SİLİNDİ" if rel not in sonra else "YENİ" if rel not in once
                                       else "AYNI" if once[rel] == sonra[rel] else "DEĞİŞTİ")
    out_kalan, out_cikan = _deger_satirlari_ayir(_norm(r.stdout, dizin))
    err_kalan, err_cikan = _deger_satirlari_ayir(_norm(r.stderr, dizin))
    return {"rc": r.returncode, "dosyalar": dosyalar, "restartlar": v556._restartlar(kok),
            "olaylar": v556._olaylar(kok),
            "kasa_argv": _norm(log.read_text(encoding="utf-8"), dizin) if log.exists() else None,
            "surum": len(_kasa(durum)), "stdout": out_kalan, "stderr": err_kalan,
            "stdout_cikan": len(out_cikan), "stderr_cikan": len(err_cikan)}


def _uret_sinifi_olcum(betik: pathlib.Path = BETIK) -> dict[str, str | None]:
    """`_uret_sinifi`nin ÖLÇÜLEN davranışı (betikten KESİLİR): alt komut → sınıf, tanımsızsa None."""
    kod = (v521._fonksiyon("_uret_sinifi", betik)
           + 'for a in "$@"; do if s="$(_uret_sinifi "$a")"; then echo "$a $s"; else echo "$a -"; fi; done\n')
    r = subprocess.run(["bash", "-c", kod, "_", *TUM_ALTLAR], capture_output=True, text=True)
    _iddia(r.returncode == 0, r.stderr)
    out = {}
    for satir in r.stdout.splitlines():
        alt, sinif = satir.split()
        out[alt] = None if sinif == "-" else sinif
    return out


def _eski_yol_sinifi(alt: str, betik: pathlib.Path = BETIK) -> list[str]:
    """Eski yol fonksiyon GÖVDESİNDEKİ `_uret <sınıf>` çağrıları (v522 `_uret_cagiran_altlar` deseni)."""
    return re.findall(r"^\s*_uret\s+(\w+)\s*$", v521._fonksiyon(alt.replace("-", "_"), betik), re.M)


# =================================================================================================
# A) SÖZLEŞME
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v520/v521/v556 A0): ithal edilen modül başka ağaçtan yüklenirse bütün çiviler
    BAŞKA bir betiği ölçer — sessizce."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v556.__file__), pathlib.Path(v522.__file__),
                pathlib.Path(v521.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


def _sinif_ihlalleri(betik: pathlib.Path = BETIK) -> list[str]:
    ih = []
    olcum = _uret_sinifi_olcum(betik)
    tanimli = {a for a, s in olcum.items() if s}
    if tanimli != URETILEBILIR:
        ih.append(f"`_uret_sinifi` tanım kümesi {sorted(tanimli)} ≠ {sorted(URETILEBILIR)}")
    for alt in sorted(URETILEBILIR):
        eski = _eski_yol_sinifi(alt, betik)
        if len(eski) != 1:
            ih.append(f"{alt}: eski yol gövdesinde TEK `_uret <sınıf>` yok ({eski})")
        elif olcum.get(alt) != eski[0]:
            ih.append(f"{alt}: `--uret` sınıfı {olcum.get(alt)!r} ≠ eski yolun {eski[0]!r}")
    return ih


def test_A1_URETIM_SINIFI_eski_yol_govdeleriyle_AYRISMAZ():
    """Tek-kaynak (kopya kaçınılmaz → türetme + ayrışma çivisi): `--uret`in sınıf tablosu
    (`_uret_sinifi`) her alt komutta eski yol GÖVDESİNİN `_uret <sınıf>` çağrısıyla aynı; tanım kümesi
    genel kasa döngüsünden geçen üreticiler (`db` ve `cp` kendi dallarında). Eski yola bir `_uret`
    eklenir/değişir de tablo güncellenmezse öter."""
    assert URETILEBILIR == v522._uret_cagiran_altlar() - {"db"}, v522._uret_cagiran_altlar()
    ih = _sinif_ihlalleri()
    assert not ih, "\n".join(ih)


def test_A2_DEGER_KAYNAGI_beyani_URET_varken_URETILIR_der_ISTER_demez():
    """`_deger_kaynagi_beyani` (betikten kesilir) `URET=1` iken üretilebilir her alt komutta TEK satır
    "betik İÇİNDE üretilir (--uret)" basar, "sizden İSTER" DEMEZ; üretmeyenlerde (openrouter · cp) susar.
    `URET=0`/tanımsız davranış v522 B1/B3'te aynen ölçülür."""
    kod = v521._fonksiyon("_deger_kaynagi_beyani") + '_deger_kaynagi_beyani "$1"\n'
    for alt in TUM_ALTLAR:
        if alt == "db":
            continue            # `--db --vault --uret` ayrıştırmada reddedilir (E) — beyan oraya ulaşmaz
        r = subprocess.run(["bash", "-c", kod, "sir_rotasyon.sh", alt], capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "URET": "1"})
        _iddia(r.returncode == 0, f"{alt}: {r.stderr}")
        satirlar = [s for s in r.stdout.splitlines() if "DEĞER KAYNAĞI" in s]
        if alt in URETILEBILIR:
            _iddia(len(satirlar) == 1 and URET_BEYAN in satirlar[0], f"{alt}: {r.stdout}")
            _iddia("sizden İSTER" not in r.stdout and "ÜRETMEZ" not in r.stdout, f"{alt}: {r.stdout}")
        else:
            _iddia(r.stdout == "", f"{alt}: {r.stdout}")


def test_A3_BASLIK_KULLANIM_satiri_URET_i_belgeler():
    """RUNBOOK betik başlığından ÜRETİLİR (`ops/runbook_uret.py`): operatörün okuyacağı komut satırı
    başlıkta yazılı olmalı — sudo'lu (v447 K1b sözleşmesi) ve hedef kullanım adıyla."""
    baslik = BETIK.read_text(encoding="utf-8").split("set -euo pipefail", 1)[0]
    assert "sudo ./sir_rotasyon.sh --<alt> --vault --uret" in baslik
    assert "--tenant --vault --uret" in baslik
    blok = baslik.split("--<alt> --vault --uret", 1)[1].split("\n#   sudo", 1)[0]
    for parca in ("--openrouter", "--db", "_uret_sinifi", "--cp --vault"):
        assert parca in blok, parca


# =================================================================================================
# B) KURU KOŞUM
# =================================================================================================

def test_B1_KURU_URET_istem_YOK_yazim_YOK_URETILIR_der_ISTER_demez(tmp_path):
    kok, ortam, log, durum = _ortam(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret", "--kuru")
    ih = _ihlaller_kuru(r, kok, log, durum, once)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_B2_KURU_plani_URET_ile_ISTEM_arasinda_YALNIZ_deger_satirlarinda_ayrisir(tmp_path):
    """Plan (kasa yolu · TAKMA AD · render kanıtı · yan dosyalar · eski kanal · restart · tavan · ön
    koşullar) iki kipte BİREBİR; ayrışan yalnız değerin KAYNAĞI satırlarıdır."""
    out = {}
    for kip, args in (("uret", ("--tenant", "--vault", "--uret", "--kuru")),
                      ("istem", ("--tenant", "--vault", "--kuru"))):
        (tmp_path / kip).mkdir()
        kok, ortam, _, _ = _ortam(tmp_path / kip)
        r = _kos(BETIK, ortam, *args)
        _iddia(r.returncode == 0, _ozet(r))
        out[kip] = _deger_satirlari_ayir(_norm(r.stdout, tmp_path / kip))
    _iddia(out["uret"][0] == out["istem"][0],
           _satirlar("uret", out["uret"][0]) + "\n" + _satirlar("istem", out["istem"][0]))
    _iddia(len(out["uret"][1]) == 2 and len(out["istem"][1]) == 3,
           _satirlar("uret çıkan", out["uret"][1]) + "\n" + _satirlar("istem çıkan", out["istem"][1]))
    plan = "\n".join(out["uret"][0])
    _iddia(f"kasaya yazılacak : {KASA_YOLU}" in plan and "TAKMA AD" in plan, _maskeli(plan))


# =================================================================================================
# C) GERÇEK KOŞUM
# =================================================================================================

@pytest.mark.parametrize("girdi", ["", f"{ISTEM_DEGERI}\n"], ids=["stdin_bos", "stdin_dolu"])
def test_C1_GERCEK_URET_istem_YOK_64_hex_kasada_ESKIden_AYRI_BASILMAZ_kopyalar_YENI(tmp_path, girdi):
    """stdin BOŞ: istem çağrılsaydı "değer boş — yapacak iş yok" ile düşerdi. stdin DOLU: istem
    çağrılsaydı kasaya İSTEM değeri giderdi. İkisinde de kasadaki değer 64 küçük hex (eski yolun
    `_uret hex` biçimi), ESKİ değerden ayrı, render hedefi + eski kanal + Agent yan dosyası YENİ,
    tüketiciler yeniden başladı ve değer (ve hash'i) hiçbir yüzeyde yok."""
    kok, ortam, log, durum = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret", girdi=girdi)
    ih = _ihlaller_gercek(r, kok, log, durum)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C2_GERCEK_URET_kanit_ve_envanter_esitligi_AYNEN_kosar(tmp_path):
    """Akışın kuyruğu (değer-doğruluğu beyanı · envanter eşitliği · iki-kanal notu) `--uret`te de koşar."""
    kok, ortam, log, durum = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    esit = [s for s in r.stdout.splitlines() if s.startswith(f"  {SIR} · ")]
    _iddia(len(esit) == 3 and all(s.endswith(("→ VAR (referans kopya)", "→ EŞİT")) for s in esit), _ozet(r))
    _iddia(f"render ÖLÇÜLDÜ: {HEDEF}" in r.stdout and "İKİ KANAL AÇIK" in r.stdout, _ozet(r))


def test_C3_AKIS_AYNEN_uret_ile_istem_AYNI_izi_birakir_yalniz_DEGER_KAYNAGI_ayrisir(tmp_path):
    """"Yalnız değerin KAYNAĞI değişir" (brief) ÖLÇÜLÜR: aynı dünyada `--uret` ile istem kipinin izleri —
    çıkış, hangi dosyanın YENİ/DEĞİŞTİ olduğu, restart sırası, kasa/Agent olay sırası, kasa argv'si,
    sürüm sayısı ve değer satırları dışındaki BÜTÜN metin — BİREBİR."""
    a = _iz(tmp_path / "uret", ("--tenant", "--vault", "--uret"), "")
    b = _iz(tmp_path / "istem", ("--tenant", "--vault"), f"{ISTEM_DEGERI}\n")
    # İzin bu anahtarları DEĞER taşımaz (durum · birim · olay adı · argv · sayı); yine de bool'a indirilir.
    for k in ("rc", "dosyalar", "restartlar", "olaylar", "kasa_argv", "surum"):
        _iddia(a[k] == b[k], _maskeli(f"{k} ayrıştı\nuret={a[k]}\nistem={b[k]}"))
    _iddia(a["rc"] == 0 and a["surum"] == 2, f"çıkış {a['rc']} · sürüm {a['surum']}")
    _iddia(a["stdout"] == b["stdout"], _satirlar("uret", a["stdout"]) + "\n" + _satirlar("istem", b["stdout"]))
    _iddia(a["stderr"] == b["stderr"], _satirlar("uret", a["stderr"]) + "\n" + _satirlar("istem", b["stderr"]))
    # Kıyas boş bir kıyas değil: çıkarılan satırlar tam beklenen sayıda (uret: beyan · üretildi · AYRI ·
    # --uret notu = 4; istem: iki satırlık beyan = 2, stderr'de istem = 1).
    sayilar = (a["stdout_cikan"], a["stderr_cikan"], b["stdout_cikan"], b["stderr_cikan"])
    _iddia(sayilar == (4, 0, 2, 1), f"çıkarılan satır sayıları {sayilar}")
    _iddia(any("kasaya yazıldı:" in s for s in a["stdout"]), "kıyas kalan metinde çekirdek satırı taşımıyor")


def test_C4_BICIM_eski_yolla_AYNI_iki_yolda_da_64_kucuk_hex(tmp_path):
    """Eski yol (`--tenant`, kasasız) aynı biçimi üretir — `.key` kopyası 64 küçük hex (A1'in
    gövde çivisinin koşan karşılığı)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(bool(re.fullmatch(r"[0-9a-f]{64}", _dosya(kok, KEY) or "")), "eski yol değeri 64 küçük hex değil")
    _iddia(URETILDI in r.stdout, _ozet(r))


# =================================================================================================
# D) `--uret` YOKKEN DAVRANIŞ BİREBİR
# =================================================================================================

def test_D1_URETSIZ_GERCEK_istem_CAGRILIR_ve_kasaya_ISTEM_degeri_gider(tmp_path):
    kok, ortam, log, durum = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant", "--vault", girdi=f"{ISTEM_DEGERI}\n")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(ISTEM in r.stderr, "istem çağrılmadı — --uret YOKKEN davranış değişti")
    _iddia(_kasa(durum) == [ESKI["tenant"], ISTEM_DEGERI], "kasaya istem değeri gitmedi")
    _iddia(v522.DEGER_KAYNAGI in r.stdout and URET_BEYAN not in r.stdout, _ozet(r))
    _iddia(URETILDI not in r.stdout and AYRI_SATIRI not in r.stdout, _ozet(r))
    ih = _sizinti(r, kok, log, ISTEM_DEGERI, ESKI["tenant"])
    _iddia(not ih, "\n".join(ih))


def test_D2_URETSIZ_KURU_plan_metni_AYNEN(tmp_path):
    kok, ortam, log, durum = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--kuru")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(f"  değer: {SORULUR} (ekrana yansımaz); boş bırakılan sır bu tur DÖNMEZ ve ADIYLA söylenir"
           in r.stdout.splitlines(), _ozet(r))
    _iddia(v522.DEGER_KAYNAGI in r.stdout, _ozet(r))
    _iddia(URET_BEYAN not in r.stdout and URET_PLAN not in r.stdout, _ozet(r))
    _iddia(not log.exists() and not v556._restartlar(kok), "kuru koşum kasaya/birime dokundu")


# =================================================================================================
# E) HATA MATRİSİ
# =================================================================================================

HATALAR = (
    ("vaultsuz", ("--tenant", "--uret"), HATA_VAULTSUZ),
    ("vaultsuz_kuru", ("--tenant", "--uret", "--kuru"), HATA_VAULTSUZ),
    ("vaultsuz_esitle", ("--tenant", "--esitle", "--uret"), HATA_VAULTSUZ),
    ("vaultsuz_envanter", ("--envanter", "--uret"), HATA_VAULTSUZ),
    ("openrouter", ("--openrouter", "--vault", "--uret"), HATA_OPENROUTER),
    ("openrouter_kuru", ("--openrouter", "--vault", "--uret", "--kuru"), HATA_OPENROUTER),
    ("db", ("--db", "--vault", "--uret"), HATA_DB),
    ("db_kuru", ("--db", "--vault", "--uret", "--kuru"), HATA_DB),
)


@pytest.mark.parametrize("etiket,args,beklenen", HATALAR, ids=[h[0] for h in HATALAR])
def test_E1_URET_HATALARI_acik_mesaj_cikis_1_HICBIR_SEY_kosmaz(tmp_path, etiket, args, beklenen):
    """`--uret` yalnız `--vault` ile ve yalnız genel döngünün üreticileriyle: öteki her birleşim AÇIK
    hatayla, istem/yazım/kasa/restart OLMADAN durur (stdin dolu verilir: istem çağrılsa değer alırdı)."""
    kok, ortam, log, _ = _ortam(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, *args, girdi=f"{ISTEM_DEGERI}\n")
    ih = _hata_ihlalleri(r, kok, log, once, beklenen)
    _iddia(not ih, f"{etiket}: " + "\n".join(ih) + "\n" + _ozet(r))


def test_E1b_VAULTSUZ_hata_YALNIZ_gecerli_bicimi_ONERIR(tmp_path):
    """Öneri satırı olmayan bir biçimi göstermez (v447 L4c emsali): `--tenant --uret` doğru biçimi
    (`--tenant --vault --uret`) önerir, `--envanter --uret` hiçbir biçim önermez."""
    for alt, oneri in (("--tenant", True), ("--envanter", False)):
        (tmp_path / alt.strip("-")).mkdir()
        _, ortam, _, _ = _ortam(tmp_path / alt.strip("-"))
        r = _kos(BETIK, ortam, alt, "--uret")
        _iddia((f"Doğrusu: sudo {BETIK} {alt} --vault --uret." in r.stderr) is oneri, _ozet(r))
        _iddia(("Doğrusu:" in r.stderr) is oneri, _ozet(r))


def test_E2_CP_VAULT_URET_ETKISIZ_der_ve_plan_URETSIZ_ile_BIREBIR(tmp_path):
    """`--cp --vault` kendi dalında değeri ZATEN üretir (TSK-226b): `--uret` orada etkisizdir ve bunu
    SÖYLER (`--kuru`nun etkisiz alt komut emsali); plan bayraksız koşumla birebir."""
    out = {}
    for kip, args in (("uret", ("--cp", "--vault", "--uret", "--kuru")), ("yalin", ("--cp", "--vault", "--kuru"))):
        (tmp_path / kip).mkdir()
        kok, ortam, log, _ = v556._cp_ortami(tmp_path / kip)
        r = _kos(BETIK, ortam, *args)
        _iddia(r.returncode == 0, _ozet(r))
        _iddia(not log.exists() and not v556._restartlar(kok), "kuru koşum kasaya/birime dokundu")
        out[kip] = (_norm(r.stdout, tmp_path / kip), r.stderr)
    _iddia(out["uret"][0] == out["yalin"][0], "plan --uret ile değişti")
    _iddia(ETKISIZ in out["uret"][1] and ETKISIZ not in out["yalin"][1], _maskeli(out["uret"][1]))


def test_E3_CP_VAULT_URET_GERCEK_kosum_TSK226b_akisiyla_KOSAR(tmp_path):
    kok, ortam, log, durum = v556._cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(ETKISIZ in r.stderr and ISTEM not in r.stderr, _ozet(r))
    kasa = v556._kasa(durum)
    _iddia(len(kasa) == 3 and bool(re.fullmatch(r"[0-9a-f]{64}", kasa[-1])), "CP kasa yolu yeni 64 hex yazmadı")
    ih = _sizinti(r, kok, log, kasa[-1])
    _iddia(not ih, "\n".join(ih))


# =================================================================================================
# F) ESKİ İLE AYNI ÜRETİM · RENDER HEDEFİ YOK
# =================================================================================================

def _sabit_openssl(tmp_path: pathlib.Path, ortam: dict) -> dict:
    binn = tmp_path / "bin_v557"
    binn.mkdir()
    asil = shutil.which("openssl")
    assert asil, "openssl PATH'te yok"
    (binn / "openssl").write_text(SIM_OPENSSL_SABIT.replace("__SABIT__", CAKISMA_DEGERI)
                                  .replace("__ASIL__", asil), encoding="utf-8")
    (binn / "openssl").chmod(0o755)
    return dict(ortam, PATH=f"{binn}:{ortam['PATH']}")


def _cakisma_ihlalleri(r, kok, log, durum, once) -> list[str]:
    ih = []
    if r.returncode != 1:
        ih.append(f"çıkış {r.returncode} (1 bekleniyordu)")
    if CAKISMA_SATIRI not in r.stderr:
        ih.append(f"stderr'de yok: {CAKISMA_SATIRI!r}")
    if any(s.startswith("kv put ") for s in (log.read_text(encoding="utf-8").splitlines()
                                             if log.exists() else [])):
        ih.append("kasaya yazıldı (kv put)")
    if _kasa(durum) != [CAKISMA_DEGERI]:
        ih.append("kasa değişti")
    if _dosya_imzalari(kok) != once:
        ih.append("dosya yazıldı (yedek dahil)")
    if v556._restartlar(kok):
        ih.append("birim yeniden başlatıldı")
    ih += _sizinti(r, kok, log, CAKISMA_DEGERI)
    return ih


def _cakisma_sahnesi(tmp_path: pathlib.Path):
    kok, ortam, log, durum = _ortam(tmp_path)
    (kok / HEDEF.lstrip("/")).write_text(CAKISMA_DEGERI, encoding="utf-8")
    veri = json.loads(durum.read_text(encoding="utf-8"))
    veri[KASA_YOLU] = [CAKISMA_DEGERI]
    durum.write_text(json.dumps(veri), encoding="utf-8")
    return kok, _sabit_openssl(tmp_path, ortam), log, durum


def test_F1_URETILEN_deger_ESKI_ile_AYNIYSA_DURUR_kasaya_HICBIR_SEY_yazilmaz(tmp_path):
    """Render kanıtı ESKİ değerle ayrışmalı: üretilen değer hedefte ZATEN duruyorsa render ölçümü
    Agent hiç çalışmasa da "geçer" — tiyatro. Sahte openssl sabit değer verir, hedef aynı değeri taşır:
    betik kasaya dokunmadan, yedek almadan, istem açmadan durur."""
    kok, ortam, log, durum = _cakisma_sahnesi(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    ih = _cakisma_ihlalleri(r, kok, log, durum, once)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_F2_RENDER_HEDEFI_YOKSA_kiyas_ADIYLA_atlanir_render_kaniti_YINE_olculur(tmp_path):
    """Hedef yoksa ESKİ değer okunamaz: kıyas UYDURULMAZ ("AYRI" denmez), ADIYLA atlanır; boş hedef
    render kanıtını sahte geçiremez (kanıt hedefin YENİ değere BİREBİR eşitliğidir) ve koşum tamamlanır."""
    kok, ortam, log, durum = _ortam(tmp_path)
    (kok / HEDEF.lstrip("/")).unlink()
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(KIYAS_YOK_SATIRI in r.stdout and AYRI_SATIRI not in r.stdout, _ozet(r))
    kasa = _kasa(durum)
    _iddia(len(kasa) == 2 and _dosya(kok, HEDEF) == kasa[-1], "render hedefi YENİ değerle doğmadı")
    ih = _sizinti(r, kok, log, kasa[-1])
    _iddia(not ih, "\n".join(ih))


# =================================================================================================
# M) MUTASYONLAR — her çivinin hedeflediği dalı ısırdığı (mutant tmp'ye yazılır, özgün betik DEĞİŞMEZ)
# =================================================================================================

URET_DALI = '    if [ "$URET" = 1 ]; then\n      _vault_uret '
URET_CAGRISI = '  _uret "$sinif" "$ISLIK/vault_yeni"\n'
SINIF_TENANT = "    tenant) echo hex ;;\n"
DB_RED = '    db) die "--db --vault --uret'
BEYAN_DALI = '      if [ "${URET:-0}" = 1 ]; then\n        echo "  · DEĞER KAYNAĞI: betik'
KURU_DEGER_DALI = '  if [ "$URET" = 1 ]; then\n    echo "betik İÇİNDE üretilir — eski yolun'
ESIT_DALI = '    EŞİT) die "üretilen değer'
VAULTSUZ_RED = '    die "--uret yalnız --vault ile'
OPENROUTER_RED = '    openrouter) die "--uret --openrouter'


def _kos_mutant(tmp_path, ad, ciftler, args, girdi="", sahne=None):
    m = v556._mutant(tmp_path, *ciftler, ad=ad)
    (tmp_path / "dunya").mkdir()
    kok, ortam, log, durum = (sahne or _ortam)(tmp_path / "dunya")
    once = _dosya_imzalari(kok)
    return _kos(m, ortam, *args, girdi=girdi), kok, log, durum, once, m


@pytest.mark.parametrize("girdi", ["", f"{ISTEM_DEGERI}\n"], ids=["stdin_bos", "stdin_dolu"])
def test_M1_MUT_URET_te_ISTEM_yine_cagrilirsa_C1_KIRMIZI(tmp_path, girdi):
    r, kok, log, durum, _, _ = _kos_mutant(tmp_path, "m1.sh", [(URET_DALI, URET_DALI.replace(
        '[ "$URET" = 1 ]', "false", 1))], ("--tenant", "--vault", "--uret"), girdi)
    ih = _ihlaller_gercek(r, kok, log, durum)
    _iddia(any(i.startswith("istem basıldı") for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M2_MUT_uretilen_deger_BASILIRSA_C1_KIRMIZI(tmp_path):
    r, kok, log, durum, _, _ = _kos_mutant(tmp_path, "m2.sh", [(URET_CAGRISI, URET_CAGRISI
                                           + '  cat "$ISLIK/vault_yeni"\n')], ("--tenant", "--vault", "--uret"))
    ih = _ihlaller_gercek(r, kok, log, durum)
    _iddia("değer #0 stdout içine düştü" in ih, "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M3_MUT_uretim_SINIFI_eski_yoldan_ayrisirsa_C1_ve_A1_KIRMIZI(tmp_path):
    r, kok, log, durum, _, m = _kos_mutant(tmp_path, "m3.sh", [(SINIF_TENANT, "    tenant) echo b64 ;;\n")],
                                           ("--tenant", "--vault", "--uret"))
    ih = _ihlaller_gercek(r, kok, log, durum)
    _iddia(any("64 küçük hex DEĞİL" in i for i in ih), "MUTASYON ISIRMADI (C1): " + "\n".join(ih))
    _iddia(any(i.startswith("tenant: `--uret` sınıfı") for i in _sinif_ihlalleri(m)), "MUTASYON ISIRMADI (A1)")


@pytest.mark.parametrize("kuru", [False, True], ids=["gercek", "kuru"])
def test_M4_MUT_URET_db_de_KABUL_edilirse_E1_KIRMIZI(tmp_path, kuru):
    args = ("--db", "--vault", "--uret") + (("--kuru",) if kuru else ())
    r, kok, log, _, once, _ = _kos_mutant(tmp_path, "m4.sh", [(DB_RED, DB_RED.replace("die", ":", 1))], args,
                                          f"{ISTEM_DEGERI}\n")
    _iddia(bool(_hata_ihlalleri(r, kok, log, once, HATA_DB)), "MUTASYON ISIRMADI")


def test_M5_MUT_beyan_URET_te_ISTER_derse_B1_KIRMIZI(tmp_path):
    r, kok, log, durum, once, _ = _kos_mutant(tmp_path, "m5.sh", [(BEYAN_DALI, BEYAN_DALI.replace(
        '[ "${URET:-0}" = 1 ]', "false", 1))], ("--tenant", "--vault", "--uret", "--kuru"))
    ih = _ihlaller_kuru(r, kok, log, durum, once)
    _iddia(any("sizden İSTER" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M6_MUT_kuru_DEGER_satiri_URET_i_gormezse_B1_KIRMIZI(tmp_path):
    r, kok, log, durum, once, _ = _kos_mutant(tmp_path, "m6.sh", [(KURU_DEGER_DALI, KURU_DEGER_DALI.replace(
        '[ "$URET" = 1 ]', "false", 1))], ("--tenant", "--vault", "--uret", "--kuru"))
    ih = _ihlaller_kuru(r, kok, log, durum, once)
    _iddia(any("AYRI sorulur" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M7_MUT_ESITLIK_kapisi_kalkarsa_F1_KIRMIZI(tmp_path):
    r, kok, log, durum, once, _ = _kos_mutant(tmp_path, "m7.sh", [(ESIT_DALI, ESIT_DALI.replace("die", "oldu", 1))],
                                              ("--tenant", "--vault", "--uret"), sahne=_cakisma_sahnesi)
    ih = _cakisma_ihlalleri(r, kok, log, durum, once)
    _iddia("kasaya yazıldı (kv put)" in ih, "MUTASYON ISIRMADI: " + "\n".join(ih))


@pytest.mark.parametrize("capa,args,beklenen", [
    (VAULTSUZ_RED, ("--tenant", "--uret", "--kuru"), HATA_VAULTSUZ),
    (OPENROUTER_RED, ("--openrouter", "--vault", "--uret", "--kuru"), HATA_OPENROUTER),
], ids=["vaultsuz", "openrouter"])
def test_M8_MUT_hata_dali_kalkarsa_E1_KIRMIZI(tmp_path, capa, args, beklenen):
    r, kok, log, _, once, _ = _kos_mutant(tmp_path, "m8.sh", [(capa, capa.replace("die", ":", 1))], args,
                                          f"{ISTEM_DEGERI}\n")
    _iddia(bool(_hata_ihlalleri(r, kok, log, once, beklenen)), "MUTASYON ISIRMADI")
