"""test_sir_rotasyon_aski_v542 — `deploy/oracle-a1/sir_rotasyon.sh` bekleme SAYAÇLARI süreç ASKISINA
dayanıklı (TSK-213 v447 bacağı, 2026-09-25).

ÖLÇÜLMÜŞ SORUN. v447'nin zamana duyarlı üç çivisi (M2 · M4 · N1) sahte KIRMIZI verdi; kök çivide
değil BETİĞİN SAATİNDEYDİ:
  · SÜREÇ ASKISI (Rol-1 sondası 2026-09-24 09:2xZ, yerel Mac): 12 s'lik sınırlı bir döngüde DUVAR
    saati 62,8 s, MONOTONİK saat 13,1 s ilerledi — iki ~25 s sıçrama (uyku/güç askısı). Betik geçen
    süreyi `date +%s` (duvar) ile ölçüyordu: askı "bekleme" sayılır, birim hazır olsa da tavan
    (çivi ortamında `SAHTE_HAZIR_TAVAN_S` = 20 s) "aşılır" ve betik sahte ÖLÇÜLEMEDİ ile çıkar.
    M2 SERİ koşumda da düştü: "seri tekrar yeşilse flake" kuralı askı altında YETMEZ, çünkü askı
    koşumdan bağımsız bir dış olaydır.
  · YÜK (suite #56, 2026-09-15): N1 2 s tavanla kırmızıydı; 7a7e9caf tavanı 20 s'ye çekti. Yük
    GERÇEK geçen süredir ve monotonik saat onu DOĞRU olarak sayar — bu dosya yük sınıfını değil
    ASKI sınıfını kapatır (ayrım ve bedel rapordadır).

ASKI MODELİ. Mac'i uyutmak çivi değildir; askı DETERMİNİSTİK olarak SİMÜLE edilir. PATH'e önce giren
`date` şimi her okumada duvar saatini `SAHTE_ASKI_S` kadar DAHA ileri atar (n. çağrı = gerçek +
n × ASKI): iki okuma arasında süreç askıdaydı. Monotonik saat SIÇRAMAZ — askının ölçülen imzası
tam budur (duvar ilerler, monotonik ilerlemez). Şim `+%s` DIŞINDAKİ biçimli okumaları da
(`-u +%Y…`, yedek dizini adı) aynı sıçramış saatle basar: askı BÜTÜN duvar okumalarını kaydırır.
Modelin kendisi S0b'de ölçülür — sıçramayan bir şim her çiviyi yanlış sebeple yeşil yapardı.

BÖLÜMLER
  S0  ithal edilen yollar bu ağacın · ASKI şimi duvarı GERÇEKTEN sıçratır, monotoniği sıçratmaz
  S1  (a) askı altında `--dash`: sahte ÖLÇÜLEMEDİ YOK
  S2  (a) askı altında `--openrouter` — v447 M2'nin ikizi (9 "hazır" satırı)
  S3  (c) basılan süreler ("hazır: … N s" · "render ÖLÇÜLDÜ (N s)" · "pencere B: N s") askıyı
      SAYMAZ: hiçbiri koşumun kendi (monotonik) süresini aşamaz
  S4  (b) GERÇEK tavan aşımı (birim hiç açılmıyor) askı altında da ÖLÇÜLEMEDİ — ve tavan kadar SÜRER
  S5  (a) `_render_bekle` askı altında: gecikmeli render sahte "render bekleme aşıldı" VERMEZ
  S6  sınıf taraması: betikte duvar saatiyle süre ölçümü KALMADI; monotonik saat TEK yerden okunur
  S7  yeni bağımlılığın arıza yüzü: saat okunamazsa ÖLÇÜLEMEDİ, duvar saatine DÜŞÜLMEZ
  S8  `--db --vault`: saat kasa yazımından ÖNCE okunur — okunamıyorsa kasaya hiçbir şey yazılmaz
      (inceleme 2026-09-24: sonraki okumada düşen saat kasayı geri almadan çıkıyordu)
  M   MUTASYONLAR — duvar saatine dönüş S1'i, donmuş saat S4'ü, geri gelen `date +%s` S6'yı,
      yutulan saat arızası S7'yi kırar

SIR DEĞERİ YOK: her değer `SAHTE-` önekli ve sahtedir (v447 / v521 / v538 tohumları).
"""
from __future__ import annotations

import calendar
import pathlib
import re
import shutil
import subprocess
import sys
import time

import pytest

from tests import test_vault_dalga1_baglama_v521 as v521
from tests import test_vault_db_kasa_v538 as v538
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    SAHTE_HAZIR_TAVAN_S,
    YENI_NOUS,
    YENI_OR,
    _mutant,
    _sahte_ortam,
    _url_gunlugu,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

#: ASKI BÜYÜKLÜĞÜ — ölçülen sıçrama ~25 s (2026-09-24). (a) çivileri ancak sıçrama TAVANI AŞARSA
#: bir şey ölçer: tavan sıçramadan büyük olsaydı duvar saatiyle ölçen betik de yeşil kalırdı.
#: Bu yüzden sayı tavandan TÜRETİLİR — biri `SAHTE_HAZIR_TAVAN_S`i yükseltirse çivi kör kalmaz.
ASKI_S = max(25, int(SAHTE_HAZIR_TAVAN_S) + 5)
#: (c) çivileri için: sıçrama koşumun kendi süresinden bir mertebe büyük olmalı ki duvar saatinden
#: sızan tek bir sıçrama "N s" satırında AYIRT EDİLEBİLSİN.
BUYUK_ASKI_S = 1000
#: (b) çivisinin tavanı — gerçek saatle beklenir (hüküm N'e bağlıdır, tavan yalnız bitişi söyler).
KISA_TAVAN_S = 2
#: Koşum başına üst sınır YALNIZ asılı kalmaya karşıdır (donmuş saat mutantı sonsuz döngüdür);
#: hüküm hiçbir çivide bu sayıya bağlı DEĞİLDİR.
ZAMAN_ASIMI_S = 300

SIM_DATE = '''#!/usr/bin/env python3
"""ASKI MODELİ: duvar saati her okumada `SAHTE_ASKI_S` kadar DAHA ileri sıçrar (n. çağrı = gerçek +
n x ASKI). Tanınan biçimler `+%s` ve `[-u] +<strftime>`; öteki her çağrı gerçek `date`e gider.
Monotonik saat bu şimden GEÇMEZ — askının ölçülen imzası: duvar ilerler, monotonik ilerlemez."""
import os, sys, time
KOK = os.environ["SIR_ROT_KOK"]
a = sys.argv[1:]
sayac = os.path.join(KOK, ".sahte", "date_sayac")
with open(sayac, encoding="utf-8") as fh:
    n = int(fh.read())
with open(sayac, "w", encoding="utf-8") as fh:
    fh.write(str(n + 1))
with open(os.path.join(KOK, ".sahte", "date.log"), "a", encoding="utf-8") as fh:
    fh.write(" ".join(a) + "\\n")
t = time.time() + n * int(os.environ["SAHTE_ASKI_S"])
utc = a[:1] == ["-u"]
bicim = a[1:] if utc else a
if bicim == ["+%s"]:
    print(int(t))
    sys.exit(0)
if len(bicim) == 1 and bicim[0].startswith("+"):
    print(time.strftime(bicim[0][1:], time.gmtime(t) if utc else time.localtime(t)))
    sys.exit(0)
for gercek in ("/bin/date", "/usr/bin/date"):
    if os.path.exists(gercek):
        os.execv(gercek, [gercek] + a)
sys.stderr.write("date: gerçek date bulunamadı\\n")
sys.exit(127)
'''

SIM_CMP_GECIKME = '''#!/usr/bin/env python3
"""RENDER GECİKMESİ: ilk `cmp_butce` karşılaştırma "farklı" (çıkış 1) döner — Agent henüz render
etmedi; bütçe bitince gerçek `cmp`e gider. `_render_bekle`nin bekleme dalı ancak böyle koşar:
v521'in kasa şimi render'ı `kv put` anında yazar ve ilk yoklama hemen geçer."""
import os, sys
yol = os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "cmp_butce")
with open(yol, encoding="utf-8") as fh:
    kalan = int(fh.read())
if kalan > 0:
    with open(yol, "w", encoding="utf-8") as fh:
        fh.write(str(kalan - 1))
    sys.exit(1)
os.execv(__GERCEK__, [__GERCEK__] + sys.argv[1:])
'''


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _aski_ekle(tmp_path: pathlib.Path, kok: pathlib.Path, ortam: dict, aski_s: int) -> dict:
    """Var olan bir sahte ortamın ÖNÜNE askı şimini koyar (v447 · v521 · v538 ortamlarının hepsi)."""
    binn = tmp_path / "aski_bin"
    binn.mkdir(exist_ok=True)
    (binn / "date").write_text(SIM_DATE, encoding="utf-8")
    (binn / "date").chmod(0o755)
    (kok / ".sahte/date_sayac").write_text("0", encoding="utf-8")
    (kok / ".sahte/date.log").write_text("", encoding="utf-8")
    return dict(ortam, PATH=f"{binn}:{ortam['PATH']}", SAHTE_ASKI_S=str(aski_s))


def _aski_ortami(tmp_path: pathlib.Path, aski_s: int) -> tuple[pathlib.Path, dict]:
    kok, ortam = _sahte_ortam(tmp_path)
    return kok, _aski_ekle(tmp_path, kok, ortam, aski_s)


def _cmp_gecikmesi(tmp_path: pathlib.Path, kok: pathlib.Path, n: int) -> None:
    gercek = shutil.which("cmp", path="/usr/bin:/bin")
    assert gercek, "gerçek cmp bulunamadı"
    binn = tmp_path / "aski_bin"
    (binn / "cmp").write_text(SIM_CMP_GECIKME.replace("__GERCEK__", repr(gercek)), encoding="utf-8")
    (binn / "cmp").chmod(0o755)
    (kok / ".sahte/cmp_butce").write_text(str(n), encoding="utf-8")


def _kos_sureli(betik: pathlib.Path, ortam: dict, *args: str, girdi: str = "",
                zaman_asimi: float = ZAMAN_ASIMI_S) -> tuple[subprocess.CompletedProcess, float]:
    """v447 `_kos` + koşumun MONOTONİK süresi. Basılan her bekleme süresi bu sayıyı aşamaz: askıyı
    sayan bir betik, koşumun kendisinden uzun bir bekleme basar (S3'ün değişmezi)."""
    bas = time.monotonic()
    r = subprocess.run(["bash", str(betik), *args], capture_output=True, text=True, env=ortam,
                       input=girdi, timeout=zaman_asimi)
    return r, time.monotonic() - bas


def _hazir_sureleri(cikti: str) -> list[tuple[str, int]]:
    return [(ad, int(s)) for ad, s in re.findall(r"✓ hazır: (\S+) (\d+) s", cikti)]


# =================================================================================================
# S0 — DÜZENEK
# =================================================================================================

def test_S0_ITHAL_edilen_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v521 A0 / v538 Ç0 ile aynı): ithal edilen modül başka ağaçtan yüklenirse
    bütün çiviler BAŞKA bir betiği ölçer — sessizce."""
    for yol in (BETIK, pathlib.Path(v521.__file__), pathlib.Path(v538.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO), f"yabancı ağaçtan ithal: {yol}"
    # (a) çivileri ancak sıçrama tavanı AŞARSA ısırır (bkz. `ASKI_S` şerhi).
    assert ASKI_S > int(SAHTE_HAZIR_TAVAN_S), (ASKI_S, SAHTE_HAZIR_TAVAN_S)


def test_S0b_ASKI_SIMI_duvari_SICRATIR_monotonigi_SICRATMAZ(tmp_path):
    """Modelin pozitif kontrolü. Şim sıçramasaydı (ya da PATH'te öne geçmeseydi) S1–S5 askısız bir
    dünyayı ölçer ve yanlış sebeple yeşil kalırdı."""
    kok, ortam = _aski_ortami(tmp_path, ASKI_S)
    assert shutil.which("date", path=ortam["PATH"]) == str(tmp_path / "aski_bin" / "date")
    m0 = time.monotonic()
    d = [int(subprocess.run(["date", "+%s"], env=ortam, capture_output=True, text=True,
                            check=True).stdout) for _ in range(2)]
    utc = subprocess.run(["date", "-u", "+%Y%m%dT%H%M%SZ"], env=ortam, capture_output=True,
                         text=True, check=True).stdout.strip()
    m1 = time.monotonic()
    assert d[1] - d[0] >= ASKI_S, d
    assert m1 - m0 < ASKI_S, "monotonik saat de sıçradı — model askıyı değil saati bozuyor"
    # Biçimli okuma da AYNI sıçramış saatten (3. çağrı = gerçek + 2 × ASKI).
    damga = calendar.timegm(time.strptime(utc, "%Y%m%dT%H%M%SZ"))
    assert damga >= d[0] + 2 * ASKI_S - 1, (utc, d)


# =================================================================================================
# S1–S2 — (a) ASKI ALTINDA SAHTE ÖLÇÜLEMEDİ YOK
# =================================================================================================

def test_S1_ASKI_altinda_dash_SAHTE_OLCULEMEDI_VERMEZ(tmp_path):
    """Birim üç yoklama boyunca ulaşılamaz, dördüncüde hazır (v447 M1 dünyası) — ve HER duvar
    okuması arasında süreç `ASKI_S` kadar askıdaydı. Gerçek bekleme saniyenin altındadır; duvar
    saatiyle ölçen betik ilk yoklamada "hazırlık bekleme aşıldı" der ve ÖLÇÜLEMEDİ ile çıkar."""
    kok, ortam = _aski_ortami(tmp_path, ASKI_S)
    ortam["SAHTE_HAZIR_N"] = "3"
    r, toplam = _kos_sureli(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "hazırlık bekleme aşıldı" not in r.stderr, r.stderr
    sureler = _hazir_sureleri(r.stdout)
    assert [ad for ad, _ in sureler] == ["meridian"], r.stdout
    assert all(s <= toplam for _, s in sureler), (sureler, toplam)
    # Yoklama GERÇEKTEN döndü (3 × 000 + 1): bir kez bakıp geçen betik de yeşil olurdu.
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/healthz")]) == 4, _url_gunlugu(kok)
    assert "pano /api/secrets: yeni→200 · eski→401" in r.stdout, r.stdout
    # Pozitif kontrol: betik şimi GÖRÜYOR (yedek dizini adı duvar saatinden okunur).
    assert (kok / ".sahte/date.log").read_text(encoding="utf-8").strip(), "betik date şimini hiç çağırmadı"


def test_S2_ASKI_altinda_openrouter_M2_IKIZI_gecer(tmp_path):
    """v447 M2'nin (seri koşumda da düşen çivi) askı altındaki ikizi: beş tur yeniden başlatma,
    negatif kontrolün iki ölçümü ve 9 "hazır" satırı — hiçbiri askıyı saymaz."""
    kok, ortam = _aski_ortami(tmp_path, ASKI_S)
    ortam["SAHTE_HAZIR_N"] = "3"
    r, toplam = _kos_sureli(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "negatif kontrol (NOUS_API_KEY, yöntem=bos): → RET" in r.stdout
    assert "negatif kontrol (OPENROUTER_API_KEY, yöntem=bozuk): → RET" in r.stdout
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    sureler = _hazir_sureleri(r.stdout)
    assert len(sureler) == 9, r.stdout
    assert all(s <= toplam for _, s in sureler), (sureler, toplam)


# =================================================================================================
# S3 — (c) BASILAN SÜRE MONOTONİK
# =================================================================================================
# Değişmez: basılan bir bekleme süresi, onu içeren koşumun MONOTONİK süresini aşamaz. Askıyı sayan
# bir ölçüm bu değişmezi `BUYUK_ASKI_S` mertebesinde çiğner. Dal: birim ANINDA hazır (N=0) ya da
# render ANINDA gelir — yani tavan kıyası hiç koşmaz ve koşum her iki saatle de GEÇER; ayırt eden
# tek şey satırdaki sayıdır. "Geçti ama yanlış süre bastı" (a)'dan AYRI bir arızadır.

def test_S3_ASKI_altinda_HAZIR_suresi_askiyi_SAYMAZ(tmp_path):
    kok, ortam = _aski_ortami(tmp_path, BUYUK_ASKI_S)
    r, toplam = _kos_sureli(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    sureler = _hazir_sureleri(r.stdout)
    assert [ad for ad, _ in sureler] == ["meridian"], r.stdout
    assert all(s <= toplam for _, s in sureler), (sureler, toplam)


def test_S3b_ASKI_altinda_RENDER_ve_PENCERE_B_ve_HAZIR_sureleri_askiyi_SAYMAZ(tmp_path):
    """`--db --vault` (v538 düzeneği) üç süre ölçüm yerinin ÜÇÜNÜ de tek koşumda geçer:
    `_render_bekle` · pencere B (render kanıtı → ALTER ROLE) · `_hazir_bekle`."""
    kok, ortam, _, _ = v538._db_ortami(tmp_path)
    ortam = _aski_ekle(tmp_path, kok, ortam, BUYUK_ASKI_S)
    r, toplam = _kos_sureli(BETIK, ortam, "--db", "--vault", girdi=f"{v538.YENI_PG}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    render = re.findall(r"render ÖLÇÜLDÜ: \S+ \((\d+) s\)", r.stdout)
    pencere = re.findall(r"pencere B \(render kanıtı → ALTER ROLE\): (\d+) s", r.stdout)
    hazir = [s for _, s in _hazir_sureleri(r.stdout)]
    assert len(render) == 1 and len(pencere) == 1 and len(hazir) == 1, r.stdout
    for etiket, s in (("render", render[0]), ("pencere B", pencere[0]), ("hazır", hazir[0])):
        assert int(s) <= toplam, f"{etiket} süresi askıyı saydı: {s} s > koşum {toplam:.1f} s"


# =================================================================================================
# S4 — (b) GERÇEK TAVAN AŞIMI HÂLÂ ÖLÇÜLEMEDİ
# =================================================================================================

def test_S4_GERCEK_TAVAN_ASIMI_aski_altinda_da_OLCULEMEDI_ve_TAVAN_KADAR_surer(tmp_path):
    """Birim HİÇ açılmaz. Monotonik saat tavanı KALDIRMAZ: betik yine "hazır" demez, ölçemediğini
    söyler, çıkış 2 verir. İkinci yarı askının TERS yüzüdür: duvar saatiyle ölçen betik, askı
    altında tavanı GERÇEK sürede beklemeden (ilk yoklamada) "aşıldı" der — kısa bir kesinti ile
    açılmayan birim ayırt edilemez. Tavan gerçek (monotonik) sürede beklenmiş olmalıdır."""
    kok, ortam = _aski_ortami(tmp_path, ASKI_S)
    ortam["SAHTE_HAZIR_N"] = "999999"
    ortam["HAZIR_BEKLE_TAVAN_S"] = str(KISA_TAVAN_S)
    r, toplam = _kos_sureli(BETIK, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hazırlık bekleme aşıldı: meridian.service" in r.stderr, r.stderr
    assert "HTTP 000" in r.stderr and f"({KISA_TAVAN_S} s içinde" in r.stderr, r.stderr
    assert "✓ hazır: " not in r.stdout, r.stdout
    assert toplam >= KISA_TAVAN_S, f"tavan gerçek sürede beklenmeden aşıldı dendi: {toplam:.2f} s"
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/healthz")]) > 1, _url_gunlugu(kok)


# =================================================================================================
# S5 — (a) RENDER BEKLEMESİ ASKI ALTINDA
# =================================================================================================

def test_S5_ASKI_altinda_GECIKMELI_RENDER_sahte_asim_VERMEZ(tmp_path):
    """`--dash --vault` (v521 düzeneği): render iki yoklama gecikir, her duvar okuması arasında
    askı vardır. Tavan çivi ortamının hazırlık tavanına eşitlenir (v521'in 1 s'si yük altında
    saniye sınırına düşebilir; bu çivinin sorusu yük değil askıdır)."""
    kok, ortam, _ = v521._kasa_ortami(tmp_path)
    ortam = _aski_ekle(tmp_path, kok, ortam, ASKI_S)
    ortam["VAULT_RENDER_TAVAN_S"] = SAHTE_HAZIR_TAVAN_S
    _cmp_gecikmesi(tmp_path, kok, 2)
    r, toplam = _kos_sureli(BETIK, ortam, "--vault", "--dash", girdi=f"{v521.YENI_DASH}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "render bekleme aşıldı" not in r.stderr, r.stderr
    m = re.search(r"render ÖLÇÜLDÜ: /etc/meridian/dash_token \((\d+) s\)", r.stdout)
    assert m and int(m.group(1)) <= toplam, (r.stdout, toplam)
    # Gecikme GERÇEKTEN tüketildi: render yoklaması döndü (yoksa bekleme dalı hiç koşmadı).
    assert (kok / ".sahte/cmp_butce").read_text(encoding="utf-8") == "0"
    assert (kok / "etc/meridian/dash_token").read_text().strip() == v521.YENI_DASH


# =================================================================================================
# S6 — SINIF TARAMASI
# =================================================================================================
#: Duvar saatinin bash/python biçimleri. Betikte GEÇEN SÜRE bunlardan ölçülürse askı (ve NTP adımı)
#: bekleme sayılır; yedek dizini damgası gibi TARİH okumaları (`date -u +%Y…`) bu kümede DEĞİLDİR.
DUVAR_SAATI = ("date +%s", "EPOCHSECONDS", "EPOCHREALTIME", "$SECONDS", "time.time(")
SAAT_OKUMASI = "time.monotonic()"


def _kod_satirlari(metin: str) -> list[tuple[int, str]]:
    return [(no, s) for no, s in enumerate(metin.splitlines(), 1) if not s.lstrip().startswith("#")]


def _duvar_saati_ihlalleri(metin: str) -> list[tuple[int, str]]:
    return [(no, s) for no, s in _kod_satirlari(metin) if any(y in s for y in DUVAR_SAATI)]


def test_S6_SINIF_TARAMASI_duvar_saatiyle_sure_olcumu_YOK_monotonik_saat_TEK_yerde():
    """Sınıf bir örnekle kapanmaz: üç ölçüm yeri (`_hazir_bekle` · `_render_bekle` · pencere B)
    aynı saati kullanır ve yeni bir bekleme duvar saatiyle doğarsa bu çivi öter. Saat okuması TEK
    satırdadır (tek-kaynak yasası): iki okuma yeri iki ayrı saat seçebilirdi."""
    metin = BETIK.read_text(encoding="utf-8")
    assert not _duvar_saati_ihlalleri(metin), _duvar_saati_ihlalleri(metin)
    okuma = [(no, s) for no, s in _kod_satirlari(metin) if SAAT_OKUMASI in s]
    assert len(okuma) == 1, okuma


# =================================================================================================
# S7 — YENİ BAĞIMLILIĞIN ARIZA YÜZÜ (bedel yasası)
# =================================================================================================
#: Saat okuması YALNIZ bu yorumlayıcıda düşer; öteki `PYTHON_BIN` çağrıları (envanter/YAML) gerçek
#: python'a gider — "saat okunamadı" ile "python yok" ayrı dünyalardır ve yalnız birincisi ölçülür.
SIM_SAATSIZ_PYTHON = '''#!/usr/bin/env python3
import os, sys
if any("time.monotonic" in x for x in sys.argv[1:]):
    sys.stderr.write("sahte: saat okunamadı\\n")
    sys.exit(1)
os.execv(__GERCEK__, [__GERCEK__] + sys.argv[1:])
'''


def _saatsiz_python(tmp_path: pathlib.Path) -> str:
    py = tmp_path / "saatsiz_python"
    py.write_text(SIM_SAATSIZ_PYTHON.replace("__GERCEK__", repr(sys.executable)), encoding="utf-8")
    py.chmod(0o755)
    return str(py)


def test_S7_SAAT_OKUNAMAZSA_OLCULEMEDI_duvar_saatine_DUSULMEZ(tmp_path):
    """Monotonik saat `PYTHON_BIN` üzerinden okunur. Okuma düşerse betik "hazır" DEMEZ ve duvar
    saatine sessizce DÜŞMEZ (düşmek askı arızasını geri getirirdi): ÖLÇÜLEMEDİ, çıkış 2."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["PYTHON_BIN"] = _saatsiz_python(tmp_path)
    r, _ = _kos_sureli(BETIK, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ: monotonik saat okunamadı" in r.stderr, r.stderr
    assert "✓ hazır: " not in r.stdout, r.stdout


def test_S8_SAAT_OKUNAMAZSA_db_kasa_yolu_KASAYA_DOKUNMADAN_durur(tmp_path):
    """İnceleme 2026-09-24 (ÖNEMLİ-2): `--db --vault`de kasa yazımından SONRAKİ ilk saat okuması render
    beklemesidir. Orada düşen saat `olcum_yok` ile ÇIKAR ve kasa kendiliğinden geri ALINMAZ (render
    tavanı aşımından farkı bu — o yol kasayı geri alır); yalnız el reçetesi basılırdı. Saat bu yüzden
    kasa yazımından ÖNCE, ön kapılarla birlikte bir kez okunur: okunamıyorsa hiçbir şey yazılmaz."""
    kok, ortam, log, durum = v538._db_ortami(tmp_path)
    ortam["PYTHON_BIN"] = _saatsiz_python(tmp_path)
    r = v538._kos(BETIK, ortam, "--db", "--vault", girdi=f"{v538.YENI_PG}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ: monotonik saat okunamadı" in r.stderr, r.stderr
    assert "kasaya HİÇBİR ŞEY yazılmadı" in r.stderr, r.stderr
    o = v538._olaylar(kok)
    assert not [x for x in o if x.startswith(("kv-put", "alter", "restart", "kv-rollback"))], o
    assert v538._kasa(durum) == v538.KASA_TOHUM and v538._pg(kok) == v538.ESKI["pg"]
    assert not list((kok / "root").glob("sir-yedek-*")), "saat kapısında durulan koşum yedek aldı"
    v538._sir_yok(r, kok, log)


# =================================================================================================
# M — MUTASYONLAR
# =================================================================================================
#: Çapa: `_saat_oku`nun saat okuması (betiğin KENDİ metni; `_mutant` varlığını doğrular).
SAAT_CAPA = "\"$PYTHON_BIN\" -c 'import time; print(int(time.monotonic() * 1000))'"


def test_M0_SAAT_CAPASI_betikte_TEKER_kez():
    assert BETIK.read_text(encoding="utf-8").count(SAAT_CAPA) == 1


def test_M1_MUT_DUVAR_SAATINE_donulurse_S1_KIRMIZI(tmp_path):
    """S1'in ısırdığı dal: saat kaynağı. Okuma duvar saatine çevrilince aynı dünyada betik ilk
    yoklamada "hazırlık bekleme aşıldı" der — 2026-09-24'te ölçülen sahte kırmızının METNİ."""
    m = _mutant(tmp_path, (SAAT_CAPA, "echo $(( $(date +%s) * 1000 ))"))
    kok, ortam = _aski_ortami(tmp_path, ASKI_S)
    ortam["SAHTE_HAZIR_N"] = "3"
    r, _ = _kos_sureli(m, ortam, "--dash")
    assert r.returncode == 2, f"MUTASYON ISIRMADI — S1 yanlış sebeple yeşil:\n{r.stdout}\n{r.stderr}"
    assert "hazırlık bekleme aşıldı: meridian.service" in r.stderr, r.stderr


def test_M2_MUT_DONMUS_SAAT_tavani_KALDIRIR_S4_KIRMIZI(tmp_path):
    """S4'ün ısırdığı dal: tavan GERÇEKTEN ilerleyen bir saate bağlı. Saat donarsa (okuma sabit)
    açılmayan birim sonsuza dek beklenir — S4 ÖLÇÜLEMEDİ'yi hiç göremez. Zaman aşımı burada
    HÜKÜMDÜR: tavanın kat kat üstünde koşum hâlâ sürüyor."""
    m = _mutant(tmp_path, (SAAT_CAPA, "echo 0"))
    _, ortam = _aski_ortami(tmp_path, ASKI_S)
    ortam["SAHTE_HAZIR_N"] = "999999"
    ortam["HAZIR_BEKLE_TAVAN_S"] = str(KISA_TAVAN_S)
    with pytest.raises(subprocess.TimeoutExpired):
        _kos_sureli(m, ortam, "--dash", zaman_asimi=KISA_TAVAN_S * 4)


def test_M4_MUT_SAAT_ARIZASI_yutulursa_S7_KIRMIZI(tmp_path):
    """S7'nin ısırdığı dal: `_saat_oku`nun `|| olcum_yok` kapısı. Kapı kalkınca `set -e` koşumu
    gerekçesiz çıkış 1 ile keser — "ölçemedim" (2) ile "çöktüm" (1) aynı şey değildir."""
    capa = ('\')" \\\n    || olcum_yok "monotonik saat okunamadı ($PYTHON_BIN) — bekleme tavanı ve süre '
            'ölçülemez${1:+ — $1}"\n')
    m = _mutant(tmp_path, (capa, "')\"\n"))
    _, ortam = _sahte_ortam(tmp_path)
    ortam["PYTHON_BIN"] = _saatsiz_python(tmp_path)
    r, _ = _kos_sureli(m, ortam, "--dash")
    assert r.returncode != 2 and "monotonik saat okunamadı" not in r.stderr, (
        f"MUTASYON ISIRMADI — S7 yanlış sebeple yeşil:\n{r.returncode}\n{r.stderr}")


def test_M3_MUT_date_s_GERI_GELIRSE_S6_KIRMIZI():
    """S6'nın ısırdığı dal: yeni bir süre ölçümü duvar saatiyle yazılırsa tarama onu bulur."""
    metin = BETIK.read_text(encoding="utf-8")
    capa = '  _saat_oku; t_kanit="$SAAT_MS"\n'
    assert metin.count(capa) == 1, "mutasyon çapası kaynakta yok (çivi bayatlamış)"
    bozuk = metin.replace(capa, '  t_kanit="$(date +%s)"\n', 1)
    assert _duvar_saati_ihlalleri(bozuk), "MUTASYON ISIRMADI — S6 taraması duvar saatini görmüyor"
