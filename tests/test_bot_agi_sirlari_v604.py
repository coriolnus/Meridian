"""test_bot_agi_sirlari_v604.py — Konuşan bot filosu Parça 1b G3b: bot ağ geçidinin sırları (2026-09-30).

NUMARA: `ls tests | grep v604` boş (bu worktree, 2026-09-30; en yüksek v603).

BÖLÜM A (G3b Task 1) — ROTASYON ARACININ SIRSIZ GÜVENLİK ALTYAPISI. Yeni sır satırı EKLENMEDEN önce
`deploy/oracle-a1/sir_rotasyon.sh` iki tehlikeye karşı kapanır:
  1. ETKİN OLMAYAN BİRİM. `meridian-botlar.service` ve `meridian-telegram.service` A1'de bugün birim
     dosyası bile taşımıyor (`inactive`, ölçüldü 2026-09-30). `_yeniden_baslat` koşulsuz `systemctl restart`
     yapıyordu (etkin olmayan birimi BAŞLATIRDI) ve `_sirala` `_BIRIM_SIRASI`nda olmayan birimi SESSİZCE
     düşürüyordu. Artık `_KOSULLU_BIRIMLER` YALNIZ ETKİNSE yeniden başlar; değilse `ATLANDI (etkin değil:
     <durum>)` satırı basılır ve o birim için credential ve hazırlık denetimi İSTENMEZ (yoksa `olcum_yok`).
  2. YARIM ROTASYON. `_yaz_satir` `env`/`url` hedefini YARATAMAZ ve yokluğu yalnız YAZIM ANINDA sorardı:
     yedek alınmış, değer üretilmiş, (kasa yolunda) kasaya konmuş ve ÖNCEKİ satırlar yazılmış olurdu.
     `_hedef_on_denetim` artık bunu dağıtım kapısında, HİÇBİR yazımdan önce sorar.

SAHNE. v447'nin sahte kökü ve şimleri (`_sahte_ortam`) — kopya DEĞİL, ithal. `SIM_SYSTEMCTL` `is-active`
modelini v447'de taşır (varsayılan: koşulsuz birim `active`, koşullu birim `inactive` — A1 gerçeği).
Task 1 tablo satırı EKLEMEZ; bu yüzden "sohbet `.env`i yokken `--tenant`" ve "kiracı sırrının tüketicisi
botlar/telegram" dünyaları (Task 2'nin getireceği satırlar) çivinin İÇİNDE, betiğin tmp KOPYASINDA kurulur
(v447 `_mutant` deseni: özgün betik DEĞİŞMEZ). `_yeniden_baslat` DOĞRUDAN sınanır: sürücü betiğin kendi
fonksiyon gövdelerini (dağıtım bloğundan önceki her şey) alır ve yalnız çağrıyı ekler.

ÇIKTI DİSİPLİNİ: iddialar bool'a indirgenir (`_iddia`); mesajlar bilinen tohumları ve uzun jetonları
maskeler. Bu dosyadaki her değer SAHTEdir.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess

import pytest

from tests import test_cp_rotasyon_v556 as v556
from tests import test_vault_dalga1_baglama_v521 as v521
from tests import test_vault_db_kasa_v538 as v538
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    ESKI,
    KOSULLU_BIRIMLER,
    _betik_kopyalari,
    _birim_sirasi,
    _kos,
    _mutant,
    _sahte_ortam,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

BOTLAR = "meridian-botlar.service"
TELEGRAM = "meridian-telegram.service"
#: Kiracı sırrının bugünkü (Task 1) tüketicileri — v557/v561 `TENANT_BIRIMLER` ile aynı küme ve sıra.
TENANT_BIRIMLER = ["hindsight-api.service", "hindsight-cp.service", "meridian.service"]
#: Bot ağ geçidinin sahte kökü: `url.log`da botlar yoklaması AYIRT edilebilsin diye ayrı bir host.
BOTLAR_KOK = "http://botlar"

#: Task 2'nin getireceği sohbet `.env` hedefi — sahnede YOKTUR (her çivi yokluğu ayrıca sağlar).
EKSIK_YOL = "/home/ubuntu/.hermes-botlar/profiles/bekci/.env"
EKSIK_ALAN = "HINDSIGHT_API_KEY"
TOHUMLA = "--tohumla-sohbet"
ROTASYON_ALTLARI = ("kapi", "tenant", "db", "dash", "openrouter", "apisix-admin", "cp")

#: İstem açılırsa okunacak değerler — ön-denetim doğruysa HİÇ okunmazlar. SAHTE.
YENI_A = "SAHTE-YENI-V604-A-0001"
YENI_B = "SAHTE-YENI-V604-B-0002"
GIRDI = f"{YENI_A}\n{YENI_B}\n"
CP_TOHUM = "SAHTE-ESKI-CP-V604-0001"
#: Sahnelerin bütün tohumları (v447 · v538 DB · v556 CP) — maskelenir ve hiçbir çıktıda görünmemelidir.
_TOHUMLAR = (tuple(ESKI.values()) + (YENI_A, YENI_B, CP_TOHUM, v538.YENI_PG, v556.ESKI_CP)
             + tuple(v556.KASA_TOHUM))

#: Sürücünün kestiği yer: dağıtım bloğunun ilk satırları (betikte TEK).
DAGITIM_BASI = "\nKURU=0\nESITLE=0\nVAULT_KIP=0\n"
#: Task 2'nin kiracı credential satırının modeli (bugün tabloda YOK).
KRED_BOTLAR = "tenant meridian-botlar.service HINDSIGHT_API_TENANT_API_KEY"


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _iddia(kosul: bool, mesaj: str) -> None:
    """Bool iddia — pytest içgözlemi işlenenleri basmaz (ÇIKTI DİSİPLİNİ)."""
    if not kosul:
        pytest.fail(mesaj, pytrace=False)


def _maskeli(metin: str) -> str:
    for d in _TOHUMLAR:
        metin = metin.replace(d, "<SAHTE-TOHUM>")
    return re.sub(r"[A-Za-z0-9_+=-]{40,}", "<UZUN-JETON>", metin)


def _ozet(r: subprocess.CompletedProcess) -> str:
    return (f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)[-3000:]}\n"
            f"--- stderr ---\n{_maskeli(r.stderr)[-3000:]}")


def _betik_sabiti(ad: str, metin: str | None = None) -> list[str]:
    metin = BETIK.read_text(encoding="utf-8") if metin is None else metin
    m = re.findall(rf'^{ad}="([^"]*)"$', metin, re.M)
    _iddia(len(m) == 1, f"betikte TEK `{ad}=\"…\"` ataması beklendi, bulunan: {len(m)}")
    return m[0].split()


def _imzalar(kok: pathlib.Path) -> dict[str, str]:
    """Sahte kökteki her dosyanın sha256'sı (şimlerin kendi günlükleri `.sahte/` hariç)."""
    return {str(p.relative_to(kok)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in kok.rglob("*") if p.is_file() and ".sahte" not in p.parts}


def _yedekler(kok: pathlib.Path) -> list[pathlib.Path]:
    return sorted((kok / "root").glob("sir-yedek-*"))


def _systemctl_log(kok: pathlib.Path) -> list[str]:
    return _birim_sirasi(kok)


def _is_active_sorulari(kok: pathlib.Path) -> list[str]:
    p = kok / ".sahte/is_active.log"
    return p.read_text(encoding="utf-8").split() if p.exists() else []


def _url_log(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/url.log").read_text(encoding="utf-8").split()


def _surucu(tmp_path: pathlib.Path, cagri: str, *ciftler: tuple[str, str],
            ad: str = "surucu.sh") -> pathlib.Path:
    """Betiğin fonksiyon gövdeleri + TEK çağrı. Dağıtım bloğundan (`KURU=0 …`) önceki her şey AYNEN alınır
    (`set -euo pipefail` dahil); `ciftler` o metinde TEK geçen dizgeleri değiştirir (Task 2 dünyası)."""
    metin = BETIK.read_text(encoding="utf-8")
    _iddia(metin.count(DAGITIM_BASI) == 1, "dağıtım bloğunun başı betikte TEK değil — sürücü kesemez")
    for eski, yeni in ciftler:
        _iddia(metin.count(eski) == 1, f"sürücü değişikliğinin hedefi TEK değil: {eski!r}")
        metin = metin.replace(eski, yeni, 1)
    on = metin[: metin.index(DAGITIM_BASI) + 1]
    yol = tmp_path / ad
    yol.write_text(on + 'KURU=0\nESITLE=0\nVAULT_KIP=0\nURET=0\nALT="tenant"\n_islik_kur\n'
                   + cagri + '\necho "SURUCU-SONU"\n', encoding="utf-8")
    return yol


def _kred_botlar_cifti() -> tuple[str, str]:
    """`_kredensiyeller` tablosuna Task 2'nin botlar satırı (heredoc sonlandırıcısının önüne)."""
    return ("\nKRED_SON\n", f"\n{KRED_BOTLAR}\nKRED_SON\n")


#: `_sir_birimleri` başına EKLENEN ilk kol — kiracı sırrının tüketicilerine iki koşullu birim (Task 2 dünyası).
#: İlk eşleşen kol kazanır; betikteki kiracı satırı değişse de bu kol aynı dünyayı kurar.
_SIR_BIRIMLERI_BASI = '_sir_birimleri() {\n  case "$1" in\n'
_TENANT_KOSULLU_KOL = ('    HINDSIGHT_API_TENANT_API_KEY) echo "'
                       + " ".join(TENANT_BIRIMLER + [BOTLAR, TELEGRAM]) + '" ;;\n')


def _kosullu_tuketicili_betik(tmp_path: pathlib.Path) -> pathlib.Path:
    return _mutant(tmp_path, (_SIR_BIRIMLERI_BASI, _SIR_BIRIMLERI_BASI + _TENANT_KOSULLU_KOL),
                   ad="kosullu_tuketicili.sh")


def _satir_metni(k: dict) -> str:
    return " ".join([k["alt"], k["sir"], k["tur"], k["yol"], k["alan"] or "-", k["mod"], k["sahip"],
                     k["onek"] or "-"]) + "\n"


def _eksik_hedefli_betik(tmp_path: pathlib.Path, alt: str) -> pathlib.Path:
    """Alt komutun İLK (referans) satırından hemen sonra, hedefi sahnede OLMAYAN bir `env` satırı —
    Task 2'nin sohbet `.env` satırının modeli. Referans satırı bozulmaz (eşitleme onu okur)."""
    ilk = next(k for k in _betik_kopyalari() if k["alt"] == alt)
    metin = _satir_metni(ilk)
    _iddia(BETIK.read_text(encoding="utf-8").count(metin) == 1, f"ilk satır metni TEK değil: {metin!r}")
    yeni = f"{alt} {ilk['sir']} env {EKSIK_YOL} {EKSIK_ALAN} koru koru -\n"
    return _mutant(tmp_path, (metin, metin + yeni), ad=f"eksik_hedef_{alt}.sh")


def _eksik_hedefi_sil(kok: pathlib.Path) -> None:
    p = kok / EKSIK_YOL.lstrip("/")
    p.unlink(missing_ok=True)
    _iddia(not p.exists(), "eksik hedef sahnede duruyor")


def _yazim_yok_ihlalleri(r: subprocess.CompletedProcess, kok: pathlib.Path, once: dict[str, str],
                         kasa_log: pathlib.Path | None) -> list[str]:
    """Ön-denetim sözleşmesi: çıkış ≠ 0 · eksik yol ADIYLA + tohumlama önerisi · yedek YOK · hiçbir dosya
    değişmedi (sha256) · kasaya put YOK · restart YOK · istem AÇILMADI · değer basılmadı."""
    ih = []
    if r.returncode == 0:
        ih.append("çıkış 0 — eksik hedefte koşum DURMADI")
    if f"hedef dosya YOK: {EKSIK_YOL}" not in r.stderr:
        ih.append("stderr eksik yolu ADIYLA söylemiyor")
    if TOHUMLA not in r.stderr:
        ih.append(f"stderr `{TOHUMLA}` önermiyor")
    if _yedekler(kok):
        ih.append("yedek dizini OLUŞTU")
    if _imzalar(kok) != once:
        degisen = sorted(k for k in set(once) | set(_imzalar(kok)) if once.get(k) != _imzalar(kok).get(k))
        ih.append(f"dosya DEĞİŞTİ (sha256): {degisen}")
    if kasa_log is not None and kasa_log.exists():
        if v521._kv_put_yollari(kasa_log):
            ih.append("kasaya `kv put` YAPILDI")
    if _systemctl_log(kok):
        ih.append("birim yeniden BAŞLATILDI")
    if "(boş = bu bacağı atla)" in r.stderr:
        ih.append("değer istemi AÇILDI")
    for d in _TOHUMLAR:
        if d in r.stdout or d in r.stderr:
            ih.append("bir tohum değeri çıktıya düştü")
            break
    return ih


# =================================================================================================
# A0 — ŞİM MODELİ: `systemctl is-active` (v447 `SIM_SYSTEMCTL`)
# =================================================================================================

def test_A0_SIM_is_active_modeli_KOSULSUZ_etkin_KOSULLU_inactive_ve_ACIK_durum(tmp_path):
    """Şimin varsayılanı A1 gerçeğidir: koşulsuz birim `active`, koşullu birim `inactive` (çıkış 3). İki
    açık kanca: `.sahte/etkin_birimler` (listedekiler etkin) ve `.sahte/durum_<birim>` (durum adı, ör.
    `failed`). Şimin koşullu kümesi betiğin `_KOSULLU_BIRIMLER`ından TÜRER (tek-kaynak)."""
    kok, ortam = _sahte_ortam(tmp_path)
    sc = str(tmp_path / "bin" / "systemctl")

    def sor(*a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sc, "is-active", *a], capture_output=True, text=True, env=ortam)

    _iddia(list(KOSULLU_BIRIMLER) == _betik_sabiti("_KOSULLU_BIRIMLER"),
           f"şimin koşullu kümesi betikle AYRIŞTI: {KOSULLU_BIRIMLER}")
    r = sor("--quiet", "meridian.service")
    _iddia(r.returncode == 0 and r.stdout == "", f"koşulsuz birim etkin değil: {r.returncode} {r.stdout!r}")
    for b in (BOTLAR, TELEGRAM):
        r = sor(b)
        _iddia(r.returncode == 3 and r.stdout.strip() == "inactive", f"{b}: {r.returncode} {r.stdout!r}")
        _iddia(sor("--quiet", b).returncode == 3, f"{b}: --quiet çıkışı 3 değil")
    (kok / ".sahte/etkin_birimler").write_text(BOTLAR + "\n", encoding="utf-8")
    r = sor(BOTLAR)
    _iddia(r.returncode == 0 and r.stdout.strip() == "active", f"etkin_birimler kancası: {r.stdout!r}")
    r = sor("meridian.service")
    _iddia(r.returncode == 3 and r.stdout.strip() == "inactive",
           "etkin_birimler VARKEN listede olmayan birim etkin sayıldı")
    (kok / f".sahte/durum_{TELEGRAM}").write_text("failed\n", encoding="utf-8")
    r = sor(TELEGRAM)
    _iddia(r.returncode == 3 and r.stdout.strip() == "failed", f"durum kancası: {r.stdout!r}")


# =================================================================================================
# A1 — `_BIRIM_SIRASI` koşullu birimleri taşır (sessiz düşüş yok) ve birim dosyalarının sırasıyla çelişmez
# =================================================================================================

def test_A1_birim_sirasi_kosullu_birimleri_tasir():
    sira = _betik_sabiti("_BIRIM_SIRASI")
    kosullu = _betik_sabiti("_KOSULLU_BIRIMLER")
    _iddia(kosullu == [BOTLAR, TELEGRAM], f"_KOSULLU_BIRIMLER: {kosullu}")
    _iddia(set(kosullu) <= set(sira), f"koşullu birim _BIRIM_SIRASI'nda YOK (_sirala sessizce düşürür): {sira}")
    _iddia(sira.index(BOTLAR) < sira.index(TELEGRAM), f"botlar telegram'dan ÖNCE değil: {sira}")
    # DAVRANIŞ: `_sirala` iki birimi DÜŞÜRMEZ ve bağımlılık sırasına dizer (fonksiyon betikten KESİLİR).
    kod = f'_BIRIM_SIRASI="{" ".join(sira)}"\n' + v521._fonksiyon("_sirala") + '\n_sirala "$@"\n'
    r = subprocess.run(["bash", "-c", kod, "_", TELEGRAM, BOTLAR, "meridian.service"],
                       capture_output=True, text=True)
    _iddia(r.returncode == 0 and r.stdout.split() == ["meridian.service", BOTLAR, TELEGRAM],
           f"_sirala: {r.returncode} {r.stdout!r} {r.stderr!r}")


def _after_bagimliliklari(birim: str) -> set[str]:
    out: set[str] = set()
    for p in KOK_DEPO.glob(f"deploy/**/{birim}"):
        if p.is_file():
            for s in p.read_text(encoding="utf-8").splitlines():
                if s.startswith("After="):
                    out |= set(s[len("After="):].split())
    return out


def test_A1b_BIRIM_SIRASI_birim_dosyalarinin_After_sirasiyla_CELISMEZ():
    """Sıra bir BAĞIMLILIK sırasıdır: `_BIRIM_SIRASI`ndaki bir birim `After=` ile başka bir listeli birimi
    istiyorsa o birim listede ÖNCE durur (telegram `After=meridian-botlar.service`). Kaynak birim dosyası."""
    sira = _betik_sabiti("_BIRIM_SIRASI")
    bulunan = 0
    for u in sira:
        for d in _after_bagimliliklari(u) & set(sira):
            bulunan += 1
            _iddia(sira.index(d) < sira.index(u), f"{u} After={d} ama sırada {d} SONRA: {sira}")
    _iddia(TELEGRAM in sira and BOTLAR in _after_bagimliliklari(TELEGRAM),
           "telegram birim dosyası botlar'a After= taşımıyor (pozitif kontrol)")
    _iddia(bulunan >= 2, f"After= kıyası çok az çift buldu ({bulunan}) — ayrıştırıcı kör")


# =================================================================================================
# A2-A4 — `_yeniden_baslat` DOĞRUDAN: koşullu birim yalnız etkinse
# =================================================================================================

def _yeniden_baslat_kos(tmp_path: pathlib.Path, hazirla=None) -> tuple[pathlib.Path, subprocess.CompletedProcess]:
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    if hazirla:
        hazirla(kok)
    surucu = _surucu(tmp_path, f"_yeniden_baslat tenant meridian.service {BOTLAR} {TELEGRAM}",
                     _kred_botlar_cifti())
    return kok, _kos(surucu, ortam)


def test_A2_etkin_olmayan_kosullu_birim_baslatilmaz(tmp_path):
    """A1 gerçeği (şim varsayılanı): iki koşullu birim `inactive`. Restart YOK, `ATLANDI (etkin değil:
    inactive)` satırı VAR, credential denetimi İSTENMEZ (Task 2'nin botlar credential satırı sürücüde
    tabloda — istenseydi `/run/credentials` yokluğu `olcum_yok` çıkış 2 verirdi), hazırlık YOKLANMAZ.
    Koşulsuz birim (meridian) aynen yeniden başlar ve ölçülür."""
    kok, r = _yeniden_baslat_kos(tmp_path)
    _iddia(r.returncode == 0 and "SURUCU-SONU" in r.stdout, _ozet(r))
    _iddia(_systemctl_log(kok) == ["meridian.service"], f"restart edilenler: {_systemctl_log(kok)}")
    for b in (BOTLAR, TELEGRAM):
        _iddia(f"ATLANDI (etkin değil: inactive): {b}" in r.stdout, f"{b} ATLANDI satırı yok\n{_ozet(r)}")
    _iddia(f"/run/credentials/{BOTLAR}/" not in r.stdout + r.stderr, "botlar için credential denetimi İSTENDİ")
    _iddia(not [u for u in _url_log(kok) if u.startswith(BOTLAR_KOK)], "etkin olmayan botlar YOKLANDI")
    _iddia("credential dolu: /run/credentials/meridian.service/" in r.stdout, "koşulsuz birim ÖLÇÜLMEDİ")
    _iddia("hazır: meridian" in r.stdout, "koşulsuz birimin hazırlığı beklenmedi")
    _iddia(sorted(set(_is_active_sorulari(kok))) == sorted([BOTLAR, TELEGRAM]),
           f"is-active sorulan birimler: {_is_active_sorulari(kok)}")


def test_A3_etkin_kosullu_birim_restart_ve_credential_denetimi(tmp_path):
    """`.sahte/etkin_birimler` ile ikisi de etkin: restart bağımlılık sırasıyla, botlar'ın credential'ı
    ÖLÇÜLÜR (sahnede dolu) ve `/health` ucu 200 ile beklenir; telegram'ın ucu YOK → mevcut güvenlik ağı."""
    def hazirla(kok: pathlib.Path) -> None:
        (kok / ".sahte/etkin_birimler").write_text(f"{BOTLAR}\n{TELEGRAM}\n", encoding="utf-8")
        kred = kok / "run/credentials" / BOTLAR / "HINDSIGHT_API_TENANT_API_KEY"
        kred.parent.mkdir(parents=True, exist_ok=True)
        kred.write_text("SAHTE-KRED-BOTLAR-0001\n", encoding="utf-8")

    kok, r = _yeniden_baslat_kos(tmp_path, hazirla)
    _iddia(r.returncode == 0 and "SURUCU-SONU" in r.stdout, _ozet(r))
    _iddia(_systemctl_log(kok) == ["meridian.service", BOTLAR, TELEGRAM], f"restart: {_systemctl_log(kok)}")
    _iddia("ATLANDI" not in r.stdout, "etkin birim ATLANDI")
    _iddia(f"credential dolu: /run/credentials/{BOTLAR}/HINDSIGHT_API_TENANT_API_KEY" in r.stdout,
           f"etkin botlar için credential denetimi İSTENMEDİ\n{_ozet(r)}")
    _iddia(f"{BOTLAR_KOK}/health" in _url_log(kok) and "hazır: meridian-botlar" in r.stdout,
           f"botlar hazırlığı /health ile beklenmedi\n{_ozet(r)}")
    _iddia(f"hazırlık yoklaması YOK: {TELEGRAM}" in r.stdout, "telegram güvenlik ağı satırı yok")


def test_A3b_etkin_kosullu_birimin_credential_i_YOKSA_olcum_yok(tmp_path):
    """A3'ün ters yüzü — denetim gerçekten İSTENİYOR: etkin botlar'ın credential'ı yoksa çıkış 2."""
    def hazirla(kok: pathlib.Path) -> None:
        (kok / ".sahte/etkin_birimler").write_text(f"{BOTLAR}\n", encoding="utf-8")

    kok, r = _yeniden_baslat_kos(tmp_path, hazirla)
    _iddia(r.returncode == 2 and f"credential dosyası YOK: /run/credentials/{BOTLAR}/" in r.stderr, _ozet(r))
    _iddia(BOTLAR in _systemctl_log(kok) and TELEGRAM not in _systemctl_log(kok), f"{_systemctl_log(kok)}")


def test_A4_failed_durumu_adiyla_basilir(tmp_path):
    """`failed` (StartLimit) de "etkin değil"dir ve DURUM ADI satıra yazılır — sessiz atlama yok."""
    def hazirla(kok: pathlib.Path) -> None:
        (kok / f".sahte/durum_{BOTLAR}").write_text("failed\n", encoding="utf-8")

    kok, r = _yeniden_baslat_kos(tmp_path, hazirla)
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(f"ATLANDI (etkin değil: failed): {BOTLAR}" in r.stdout, f"failed adıyla basılmadı\n{_ozet(r)}")
    _iddia(f"ATLANDI (etkin değil: inactive): {TELEGRAM}" in r.stdout, _ozet(r))
    _iddia(BOTLAR not in _systemctl_log(kok), "failed birim yeniden BAŞLATILDI")


# =================================================================================================
# A5-A6 — YAZIM ÖNCESİ HEDEF ÖN-DENETİMİ (`--tenant`, Task 2'nin sohbet `.env` satırı modeliyle)
# =================================================================================================

def test_A5_on_denetim_eksik_hedefte_HICBIR_yazim_yok(tmp_path):
    """Eski yol: hedef `.env` yokken yedek · değer üretimi · ilk satır (kiracı credential kaynağı) HİÇBİRİ
    yapılmaz; eksik yol ADIYLA, `--tohumla-sohbet` önerisiyle söylenir. Bugünkü hâl: yedek alınır, kaynak
    YENİ değerle yazılır, sonra `_yaz_satir env` "hedef dosya YOK" ile düşer — yarım rotasyon."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    _eksik_hedefi_sil(kok)
    betik = _eksik_hedefli_betik(tmp_path, "tenant")
    once = _imzalar(kok)
    r = _kos(betik, ortam, "--tenant", girdi=GIRDI)
    ih = _yazim_yok_ihlalleri(r, kok, once, kasa_log)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_A6_on_denetim_vault_kipinde_de_puttan_once(tmp_path):
    """Kasa yolu: `kv put` (geri alınması ayrı bir reçete isteyen yazım) eksik hedefte HİÇ yapılmaz."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    _eksik_hedefi_sil(kok)
    betik = _eksik_hedefli_betik(tmp_path, "tenant")
    once = _imzalar(kok)
    r = _kos(betik, ortam, "--tenant", "--vault", girdi=GIRDI)
    ih = _yazim_yok_ihlalleri(r, kok, once, kasa_log)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# A7 — kuru rapor koşullu birimi ÖNCEDEN bildirir (bedel yasası)
# =================================================================================================

@pytest.mark.parametrize("kip", ["eski", "vault"])
def test_A7_kuru_rapor_kosullu_birimi_bildirir(tmp_path, kip):
    """`--tenant --kuru` (ve `--vault --kuru`): tüketici kümesinde koşullu birim varsa "YALNIZ ETKİNSE"
    notu ve her birimin ŞU ANKİ durumu + sonucu (inactive → ATLANACAK) basılır; hiçbir şey yazılmaz."""
    kok, ortam, _ = v521._kasa_ortami(tmp_path)
    betik = _kosullu_tuketicili_betik(tmp_path)
    ek = ("--vault",) if kip == "vault" else ()
    once = _imzalar(kok)
    r = _kos(betik, ortam, "--tenant", *ek, "--kuru")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia("YALNIZ ETKİNSE" in r.stdout, f"koşullu birim notu yok\n{_ozet(r)}")
    for b in (BOTLAR, TELEGRAM):
        _iddia(f"    · {b} — şu an: inactive → ATLANACAK" in r.stdout.splitlines(),
               f"{b} şu anki durumuyla bildirilmedi\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok), "kuru koşum YAZDI")
    # Etkin dünyada aynı satır "yeniden başlar" der.
    (kok / ".sahte/etkin_birimler").write_text(f"{BOTLAR}\n", encoding="utf-8")
    r2 = _kos(betik, ortam, "--tenant", *ek, "--kuru")
    _iddia(f"    · {BOTLAR} — şu an: active → yeniden başlar" in r2.stdout.splitlines(), _ozet(r2))
    # BEDEL: kümede koşullu birim YOKSA (gerçek betik, Task 1) not BASILMAZ — ilgisiz başlık gürültüdür.
    r3 = _kos(BETIK, ortam, "--tenant", *ek, "--kuru")
    _iddia(r3.returncode == 0 and "YALNIZ ETKİNSE" not in r3.stdout, _ozet(r3))


# =================================================================================================
# A8-A11 — ön-denetimin KAPSAMI: bütün alt komutlar, iki kip, eşitleme, tek nokta, tür sınıfı
# =================================================================================================

@pytest.mark.parametrize("kip", ["eski", "vault"])
@pytest.mark.parametrize("alt", ROTASYON_ALTLARI)
def test_A8_on_denetim_BUTUN_alt_komutlarda_ve_iki_kipte_yazimdan_once(tmp_path, alt, kip):
    """Yedi rotasyon alt komutunun HER BİRİ, eski yolda ve kasa yolunda (genel döngü · `--db` · `--cp`
    dalları dahil): eksik `env` hedefi → hiçbir yazım, hiçbir istem, hiçbir restart, kasaya put yok.
    Sahne v521'in genel kasasıdır: `--db --vault` ve `--cp --vault` hücreleri kapıyı ölçer ama kapı olmasa
    da kendi ön kontrollerinde (kasadan ESKİ değer) dururlardı — o iki dalın yazım karşı-olgusu A8b'dedir."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    _eksik_hedefi_sil(kok)
    betik = _eksik_hedefli_betik(tmp_path, alt)
    ek = ("--vault",) if kip == "vault" else ()
    once = _imzalar(kok)
    r = _kos(betik, ortam, f"--{alt}", *ek, girdi=GIRDI)
    ih = _yazim_yok_ihlalleri(r, kok, once, kasa_log)
    _iddia(not ih, f"--{alt} {' '.join(ek)}:\n" + "\n".join(ih) + "\n" + _ozet(r))


def _db_dunyasi(tmp_path: pathlib.Path):
    kok, ortam, log, _ = v538._db_ortami(tmp_path)
    return kok, ortam, log, f"{v538.YENI_PG}\n"


def _cp_dunyasi(tmp_path: pathlib.Path):
    kok, ortam, log, _ = v556._cp_ortami(tmp_path)
    return kok, ortam, log, ""          # `--cp --vault` değeri SORMAZ, üretir


@pytest.mark.parametrize("alt,dunya", [("db", _db_dunyasi), ("cp", _cp_dunyasi)], ids=["db", "cp"])
def test_A8b_on_denetim_DB_ve_CP_kasa_dallari_KENDI_dunyalarinda_puttan_once(tmp_path, alt, dunya):
    """A8'in `--db --vault` ve `--cp --vault` hücreleri v521'in genel kasa sahnesinde kendi ön kontrollerinde
    (kasadan ESKİ DSN/değer okuma) durur — kapı olmasa da yazıma varmazlardı (ölçüldü: M5 mutasyonu). Bu çivi
    iki dalı KENDİ dünyalarında (v538 DB · v556 CP: kasa ESKİ değeri sunar) koşar: kapı olmasa `kv put` ve
    dosya yazımı GERÇEKTEN olurdu; kapı varken hiçbiri yok."""
    kok, ortam, kasa_log, girdi = dunya(tmp_path)
    _eksik_hedefi_sil(kok)
    betik = _eksik_hedefli_betik(tmp_path, alt)
    once = _imzalar(kok)
    r = _kos(betik, ortam, f"--{alt}", "--vault", girdi=girdi)
    ih = _yazim_yok_ihlalleri(r, kok, once, kasa_log)
    _iddia(not ih, f"--{alt} --vault:\n" + "\n".join(ih) + "\n" + _ozet(r))


ESITLENEBILIR = ("kapi", "tenant", "dash", "openrouter", "apisix-admin", "cp")


@pytest.mark.parametrize("alt", ESITLENEBILIR)
def test_A9_esitle_KOPYA_YOK_durdurmasi_korunur_yazim_yok(tmp_path, alt):
    """`--esitle` ön-denetimden GEÇMEZ: ölçüm geçişinin mevcut "kopya YOK — eşitleme yarım kalırdı"
    durdurması eksik kopyayı ZATEN yazımdan (yedek dahil) önce yakalar — o durdurma KORUNUR (metni aynen).
    (`--db --esitle` tablo sırası gereği referansta durur: ilk satırı `sql`dir — kapsam dışı.)"""
    kok, ortam = _sahte_ortam(tmp_path)
    _eksik_hedefi_sil(kok)
    # v447 sahnesi CP'nin kanonik kopyasını taşımaz (CP dünyası v556'dadır): eşitlemenin REFERANSI kurulur ki
    # durdurma referansta değil, EKSİK kopyada ölçülsün.
    cp_ref = kok / "etc/meridian/hindsight_cp_access_key"
    if alt == "cp" and not cp_ref.exists():
        cp_ref.write_text(CP_TOHUM + "\n", encoding="utf-8")
    betik = _eksik_hedefli_betik(tmp_path, alt)
    once = _imzalar(kok)
    r = _kos(betik, ortam, f"--{alt}", "--esitle")
    _iddia(r.returncode != 0, _ozet(r))
    _iddia(f"kopya YOK: {EKSIK_YOL} [{EKSIK_ALAN}]" in r.stderr and "eşitleme yarım kalırdı" in r.stderr,
           f"eşitlemenin kendi durdurması DEĞİŞTİ\n{_ozet(r)}")
    _iddia(not _yedekler(kok) and _imzalar(kok) == once and not _systemctl_log(kok), "eşitleme YAZDI")


def _dagitim_blogu() -> str:
    metin = BETIK.read_text(encoding="utf-8")
    return metin[metin.index('_UID="$(id -u)"'):]


def test_A10_on_denetim_DAGITIM_kapisinda_TEK_noktada_butun_yollarin_ONUNDE():
    """Çağrı noktası: root kapısından SONRA, çalışma dizini (`_islik_kur`) ve bütün yazım yollarından
    (kasa dalı · eşitleme · eski yol alt komutları) ÖNCE; betikte TEK çağrı (tek-kaynak). Kuru koşum ve
    eşitleme kapıdan geçmez (kuru hiçbir şey yazmaz; eşitlemenin kendi durdurması var — A9)."""
    metin = BETIK.read_text(encoding="utf-8")
    cagrilar = [s for s in metin.splitlines()
                if "_hedef_on_denetim " in s and not s.lstrip().startswith("#")
                and not s.lstrip().startswith("_hedef_on_denetim()")]
    _iddia(len(cagrilar) == 1, f"TEK çağrı beklendi: {cagrilar}")
    blok = _dagitim_blogu()
    sira = [blok.find(x) for x in ('_hedef_on_denetim "$ALT"', "\n_islik_kur\n", 'vault_rotasyon "$ALT"',
                                    'esitle "$ALT"', '\n  kapi)       kapi ;;')]
    _iddia(all(i >= 0 for i in sira) and sira == sorted(sira), f"dağıtım bloğunda sıra: {sira}")
    satir = cagrilar[0]
    _iddia('"$KURU" = 0' in satir and '"$ESITLE" = 0' in satir and '"$KURU_ONERILIR" = 1' in satir,
           f"kapının koşulu: {satir.strip()}")


def test_A10b_kuru_kosum_eksik_hedefte_DURMAZ_ve_YAZMAZ(tmp_path):
    """Kuru koşum operatörün İLK komutudur ve hiçbir şey yazmaz: ön-denetim onu kesmez (plan yine basılır)."""
    kok, ortam = _sahte_ortam(tmp_path)
    _eksik_hedefi_sil(kok)
    once = _imzalar(kok)
    r = _kos(_eksik_hedefli_betik(tmp_path, "tenant"), ortam, "--tenant", "--kuru")
    _iddia(r.returncode == 0 and "KURU KOŞUM: --tenant" in r.stdout, _ozet(r))
    _iddia(_imzalar(kok) == once and not _yedekler(kok), "kuru koşum YAZDI")


@pytest.mark.parametrize("alt,silinen", [
    ("kapi", "/opt/apisix/.env-apisix"),                               # env — gerçek tablo satırı
    ("db", "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"),         # url — gerçek tablo satırı
    ("openrouter", "/home/ubuntu/.hermes/.env"),                       # env — gerçek tablo satırı
])
def test_A11_gercek_tablonun_env_ve_url_hedefi_YOKKEN_yazim_yok(tmp_path, alt, silinen):
    """Kapsam = `_yaz_satir`ın hedefi YARATAMADIĞI türler (`env` · `url`) — gerçek tablo satırlarıyla, betik
    kopyası OLMADAN. (`dosya` satırını betik kurar: v447 R7 / v557 F2 — ön-denetim onu istemez.)"""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    (kok / silinen.lstrip("/")).unlink()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, f"--{alt}", girdi=GIRDI)
    _iddia(r.returncode != 0 and f"hedef dosya YOK: {silinen}" in r.stderr and TOHUMLA in r.stderr, _ozet(r))
    _iddia(not _yedekler(kok) and _imzalar(kok) == once and not _systemctl_log(kok), f"YAZDI\n{_ozet(r)}")
    _iddia("(boş = bu bacağı atla)" not in r.stderr, "istem AÇILDI")


def test_A11b_dosya_hedefi_YOKKEN_on_denetim_KESMEZ(tmp_path):
    """`dosya` (mod/sahip açık) satırının hedefini betik KENDİSİ kurar — ön-denetim bu sözleşmeyi bozmaz.
    Dünya v447 R7'ninki: Faz-1C öncesi `--apisix-admin` credential kaynağı YOK, ESKİ değer `.env-apisix`
    yedeğinden okunur ve eksik kaynak rotasyonla YARATILIR. (`--dash` bu dünyaya uymaz: ESKİ değerini
    kanonik kopyanın kendi yedeğinden okur.)"""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/meridian/apisix_admin_key").unlink()
    r = _kos(BETIK, ortam, "--apisix-admin")
    _iddia(r.returncode == 0 and "hedef dosya YOK" not in r.stderr,
           f"dosya hedefi ön-denetime takıldı\n{_ozet(r)}")
    _iddia((kok / "etc/meridian/apisix_admin_key").exists(), "dosya hedefi KURULMADI")


# =================================================================================================
# A12-A15 — negatif kontrol yolları · hazırlık ucu · koşulsuz birimde davranış aynı · başlık
# =================================================================================================

def test_A12_negatif_kontrol_yollari_kosullu_birime_DOKUNMAZ():
    """`_negatif_restart_kurtarma` ve `_yeniden_baslat_sessiz` koşulsuz restart yapar ve koşullu kurala
    TABİ DEĞİLDİR. Güvenli olmalarının tek sebebi, birim kümelerinin YALNIZ negatif kontrol sırlarının
    tüketicilerinden (`_sir_birimleri`) gelmesidir — ve o tüketiciler koşullu birim İÇERMEZ. Biri o yollara
    koşullu birim sokarsa bu çivi öter (koşullu kural oraya da taşınmalı)."""
    metin = BETIK.read_text(encoding="utf-8")
    govde_nk = v521._fonksiyon("_negatif_kontrol")
    kod_satirlari = [s for s in metin.splitlines() if not s.lstrip().startswith("#")]
    # (1) `_yeniden_baslat_sessiz` ve `NK_BIRIMLER=<dolu>` YALNIZ `_negatif_kontrol` içinde.
    sessiz = [s for s in kod_satirlari if re.search(r"(^|\s)_yeniden_baslat_sessiz\s", s)]
    _iddia(len(sessiz) >= 1 and all(s in govde_nk for s in sessiz),
           f"_yeniden_baslat_sessiz negatif kontrol DIŞINDA çağrılıyor: {sessiz}")
    atama = [s for s in kod_satirlari if re.search(r'NK_BIRIMLER="\$', s)]
    _iddia(atama and all(s in govde_nk for s in atama), f"NK_BIRIMLER dolu ataması: {atama}")
    _iddia('birimler="$(_sir_birimleri "$sir")"' in govde_nk, "negatif kontrolün kümesi _sir_birimleri'nden değil")
    # (2) Negatif kontrol sırlarının tüketicileri koşullu birim içermez.
    sirlar = set()
    for s in kod_satirlari:
        m = re.search(r"(?:^|\s)_negatif_kontrol\s+(\S+)\s+(\S+)\s", s)
        if m and "()" not in s:
            sirlar.add(m.group(2))
    _iddia(sirlar == {"NOUS_API_KEY", "OPENROUTER_API_KEY"}, f"negatif kontrol sırları: {sirlar}")
    kod = v521._fonksiyon("_sir_birimleri") + '\n_sir_birimleri "$1"\n'
    for sir in sirlar:
        r = subprocess.run(["bash", "-c", kod, "_", sir], capture_output=True, text=True)
        _iddia(r.returncode == 0 and r.stdout.split(), f"{sir}: {r.stdout!r}")
        _iddia(not set(r.stdout.split()) & set(KOSULLU_BIRIMLER), f"{sir} tüketicisi koşullu birim: {r.stdout}")


def test_A13_hazir_uc_botlar_health_telegram_UCSUZ():
    """Botlar: Hermes `GET /health` kimliksiz, `{"status":"ok"}` (Rol-1 A1 kaynak ölçümü, 2026-09-30) →
    kabul `200`. Varsayılan dinleyici 127.0.0.1:8642. Telegram'ın ucu YOK → "hazırlık yoklaması YOK"."""
    metin = BETIK.read_text(encoding="utf-8")
    _iddia('BOTLAR_KOK="${SIR_ROT_BOTLAR:-http://127.0.0.1:8642}"' in metin, "botlar kökü/portu betikte yok")
    kod = v521._fonksiyon("_hazir_uc") + '\n_hazir_uc "$1"\n'
    r = subprocess.run(["bash", "-c", kod, "_", BOTLAR], capture_output=True, text=True,
                       env=dict(os.environ, BOTLAR_KOK="http://botlar-kok"))
    _iddia(r.returncode == 0 and r.stdout.split(" ", 2)[:2] == ["http://botlar-kok/health", "200"],
           f"botlar ucu: {r.stdout!r}")
    r = subprocess.run(["bash", "-c", kod, "_", TELEGRAM], capture_output=True, text=True)
    _iddia(r.returncode == 1 and r.stdout == "", f"telegram'a uç tanımlandı: {r.stdout!r}")


def test_A14_kosulsuz_birimde_is_active_SORULMAZ_restart_pini_AYNI(tmp_path):
    """Mevcut birimler için davranış BİREBİR: `is-active` hiç sorulmaz, restart kümesi ve sırası v557/v561
    `TENANT_BIRIMLER` ile aynı, ATLANDI satırı yok."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(_is_active_sorulari(kok) == [], f"koşulsuz birimde is-active soruldu: {_is_active_sorulari(kok)}")
    _iddia(_systemctl_log(kok) == TENANT_BIRIMLER, f"restart: {_systemctl_log(kok)}")
    _iddia("ATLANDI" not in r.stdout, "koşulsuz birim ATLANDI")


def test_A15_KULLANIM_basligi_kosullu_birimi_TEK_satirla_soyler():
    metin = BETIK.read_text(encoding="utf-8")
    baslik = metin[: metin.index("\nset -euo pipefail\n")]
    kullanim = baslik[baslik.index("# KULLANIM"):]
    satirlar = [s for s in kullanim.splitlines() if "_KOSULLU_BIRIMLER" in s]
    _iddia(len(satirlar) == 1 and "YALNIZ ETKİNSE" in satirlar[0] and "ATLANDI" in satirlar[0],
           f"KULLANIM satırı: {satirlar}")
