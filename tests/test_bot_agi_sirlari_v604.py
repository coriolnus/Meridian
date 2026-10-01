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

BÖLÜM B (G3b Task 2, 2026-10-01) — `API_SERVER_KEY` ZİNCİRİ + KİRACI ANAHTARININ SOHBET KOPYALARI + CREDENTIAL
DROP-IN'LERİ. Tablo satırları artık GERÇEK (Task 1'in tmp-kopya dünyaları gerçek betiğe taşındı: A7 · A14 · sürücü);
bot listesi kabukta TEK sabit (`_SOHBET_BOTLARI`), envanter aynası üreteçle (`ops/sir_envanteri_bot_uret.py`).
Task 1 incelemesinin taşınan maddeleri: M1 (reçeteler koşullu birimi `try-restart` ile anar — B11), M2 (ön-denetimin
alt komut süzgeci + tekilleştirme — B10), M3 (A7-r3 / A14 yeni gerçeğe çevrildi).

BÖLÜM C (G3b Task 3, 2026-10-01) — `--kapi-bot <ad>`: bir botun kapı tüketici anahtarı (`BOT_KEY_<AD>`) dört kopyasıyla
(Agent render hedefi REFERANS · `.env-apisix` · rapor profili · sohbet profili) birlikte döner (operatör K-G3b-1); iç alt ad
`kapi-bot-<ad>` (Rol-1 G3b-R2), bot listesi kabukta TEK sabit. Task 2 incelemesinin taşınan maddeleri: M1 (ön-denetim ALAN
varlığını da sorar — A16), M5 (`--api-sunucu --vault` gerçek koşum B15 · envanter/eşitleme ayrışma senaryosu B16), M6
(üretecin bot başı alt komut ailesi — C9).

BÖLÜM D (G3b Task 4, 2026-10-01) — `--tohumla-sohbet`: bot ağ geçidinin sohbet `.env`lerinin İLK yazımı (operatör K-G3b-2).
Hedef ve alan kümesi KOPYA TABLOSUNDAN türer (`_SOHBET_KOKU` altına yazan `env` satırları — ikinci liste YOK, D9), değer her
sırrın REFERANSINDAN (`py cikar`, değer argv'ye/çıktıya düşmez — D7); YOK olan dosya 0600 ubuntu:ubuntu yazılır (D1), VAR
olana dokunulmaz (D2) ve eksik alanı ADIYLA söylenir → çıkış 3 (D3); referans ya da dizin yoksa HİÇBİR şey yazılmaz (D4/D5);
ikinci koşum yazmaz (D6); kuru sıfır yazım (D8); yardımcı var olan hedefi `os.link` ile reddeder — yarışta da (D10).
Task 3 incelemesinin taşınan maddeleri: M1 → Rol-1 0. madde (kasa yolunda yan dosya render'ı restart'tan ÖNCE ölçülür ve
eski yolun tüketici kanıtı kasa yolunda da koşar — C10), M2 (ön-denetim ÖLÇÜLEMEDİ hâli çıkış 2, traceback yok — A16c),
M4 (`_sir_birimleri` `BOT_KEY_MERIDIAN`ı bot globuyla EŞLEMEZ — C11), M5 (C9 kapsam beyanı).

ÇIKTI DİSİPLİNİ: iddialar bool'a indirgenir (`_iddia`); mesajlar bilinen tohumları ve uzun jetonları
maskeler. Bu dosyadaki her değer SAHTEdir.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from tests import test_cp_rotasyon_v556 as v556
from tests import test_vault_dalga1_baglama_v521 as v521
from tests import test_vault_db_kasa_v538 as v538
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    ESKI,
    KAPI_BOT_ALTLARI,
    KOSULLU_BIRIMLER,
    _env_alan,
    _betik_kopyalari,
    _birim_sirasi,
    _kos,
    _mutant,
    _sahte_ortam,
    _yardimci,
    alt_argv,
    alt_bayragi,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

BOTLAR = "meridian-botlar.service"
TELEGRAM = "meridian-telegram.service"
#: Kiracı sırrının KOŞULSUZ tüketicileri — sahnede koşullu birimler `inactive` olduğu için yeniden başlatılan küme
#: TAM budur (v557 `TENANT_BIRIMLER` ile aynı küme ve sıra). Task 2'den beri tüketici kümesi + botlar + telegram.
TENANT_BIRIMLER = ["hindsight-api.service", "hindsight-cp.service", "meridian.service"]
TENANT_KRED_KAYNAK = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
#: Bot ağ geçidinin sahte kökü: `url.log`da botlar yoklaması AYIRT edilebilsin diye ayrı bir host.
BOTLAR_KOK = "http://botlar"

#: Task 2'nin getireceği sohbet `.env` hedefi — sahnede YOKTUR (her çivi yokluğu ayrıca sağlar).
EKSIK_YOL = "/home/ubuntu/.hermes-botlar/profiles/bekci/.env"
EKSIK_ALAN = "HINDSIGHT_API_KEY"
TOHUMLA = "--tohumla-sohbet"
#: 2026-10-01 (G3b Task 2): `api-sunucu` — dört `.env` hedefi taşıyan ilk alt komut; aynı kapıdan geçer.
ROTASYON_ALTLARI = ("kapi", "tenant", "db", "dash", "openrouter", "apisix-admin", "cp", "api-sunucu")

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

def _yeniden_baslat_kos(tmp_path: pathlib.Path, hazirla=None,
                        birimler: str = f"meridian.service {BOTLAR} {TELEGRAM}",
                        ) -> tuple[pathlib.Path, subprocess.CompletedProcess]:
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    if hazirla:
        hazirla(kok)
    # K4 (Task 2): botlar'ın kiracı credential satırı artık GERÇEK tabloda (`_kredensiyeller`) — sürücü eki kalktı.
    surucu = _surucu(tmp_path, f"_yeniden_baslat tenant {birimler}")
    return kok, _kos(surucu, ortam)


def test_A2_etkin_olmayan_kosullu_birim_baslatilmaz(tmp_path):
    """A1 gerçeği (şim varsayılanı): iki koşullu birim `inactive`. Restart YOK, `ATLANDI (etkin değil:
    inactive)` satırı VAR, credential denetimi İSTENMEZ (botlar'ın kiracı credential satırı GERÇEK tabloda —
    istenseydi `/run/credentials` yokluğu `olcum_yok` çıkış 2 verirdi), hazırlık YOKLANMAZ.
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
    """A3'ün ters yüzü — denetim gerçekten İSTENİYOR: etkin botlar'ın credential'ı yoksa çıkış 2.
    Task 2 (2026-10-01): botlar drop-in'i GERÇEK — şim restart'ta kaynağı `/run/credentials`a kopyalar; credential'ın
    YOK olduğu dünya kaynağın kendisi kaldırılarak kurulur ve küme yalnız botlar'dır (meridian aynı kaynağı okur ve
    önce düşerdi — ölçülen dal botlar'ınki olmazdı)."""
    def hazirla(kok: pathlib.Path) -> None:
        (kok / ".sahte/etkin_birimler").write_text(f"{BOTLAR}\n", encoding="utf-8")
        (kok / TENANT_KRED_KAYNAK.lstrip("/")).unlink()

    kok, r = _yeniden_baslat_kos(tmp_path, hazirla, birimler=f"{BOTLAR} {TELEGRAM}")
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
    notu ve her birimin ŞU ANKİ durumu + sonucu (inactive → ATLANACAK) basılır; hiçbir şey yazılmaz.
    M3 (Task 2, 2026-10-01): kiracı sırrının koşullu tüketicileri artık GERÇEK tabloda — Task 1'in tmp kopya dünyası
    (`_sir_birimleri` başına eklenen kol) kalktı, çivi gerçek betiği koşar. "Koşullu birim yoksa not BASILMAZ" yüzü
    (bedel) koşullu tüketicisi OLMAYAN bir alt komutla (`--dash`) ölçülür."""
    kok, ortam, _ = v521._kasa_ortami(tmp_path)
    ek = ("--vault",) if kip == "vault" else ()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--tenant", *ek, "--kuru")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia("YALNIZ ETKİNSE" in r.stdout, f"koşullu birim notu yok\n{_ozet(r)}")
    for b in (BOTLAR, TELEGRAM):
        _iddia(f"    · {b} — şu an: inactive → ATLANACAK" in r.stdout.splitlines(),
               f"{b} şu anki durumuyla bildirilmedi\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok), "kuru koşum YAZDI")
    # Etkin dünyada aynı satır "yeniden başlar" der.
    (kok / ".sahte/etkin_birimler").write_text(f"{BOTLAR}\n", encoding="utf-8")
    r2 = _kos(BETIK, ortam, "--tenant", *ek, "--kuru")
    _iddia(f"    · {BOTLAR} — şu an: active → yeniden başlar" in r2.stdout.splitlines(), _ozet(r2))
    # BEDEL: kümede koşullu birim YOKSA not BASILMAZ — ilgisiz başlık gürültüdür (`--dash`: tek tüketici meridian).
    r3 = _kos(BETIK, ortam, "--dash", *ek, "--kuru")
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


ESITLENEBILIR = ("kapi", "tenant", "dash", "openrouter", "apisix-admin", "cp", "api-sunucu")


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
    """Çağrı noktası: root kapısından ve çalışma dizininden (`_islik_kur`) SONRA, bütün yazım yollarından
    (kasa dalı · eşitleme · eski yol alt komutları) ÖNCE; betikte TEK çağrı (tek-kaynak). Kuru koşum ve
    eşitleme kapıdan geçmez (kuru hiçbir şey yazmaz; eşitlemenin kendi durdurması var — A9).
    2026-10-01 (G3b Task 3, Task 2 incelemesi M1): ön-denetim ALAN VARLIĞINI da sorar ve kural `yaz-env`inkiyle AYNI
    fonksiyondur (gömülü yardımcının `_env_satiri`i) — yardımcı `_islik_kur`un yazdığı dosyadır, o yüzden kapı çalışma
    dizininden SONRA. Çalışma dizini bir YAZIM değildir (0700 geçici, çıkışta silinir; yedek/kasa/kopya değil) — A5/A6/A16
    "hiçbir yazım yok" sözleşmesini aynen ölçer."""
    metin = BETIK.read_text(encoding="utf-8")
    cagrilar = [s for s in metin.splitlines()
                if "_hedef_on_denetim " in s and not s.lstrip().startswith("#")
                and not s.lstrip().startswith("_hedef_on_denetim()")]
    _iddia(len(cagrilar) == 1, f"TEK çağrı beklendi: {cagrilar}")
    blok = _dagitim_blogu()
    sira = [blok.find(x) for x in ("\n_islik_kur\n", '_hedef_on_denetim "$ALT"', 'vault_rotasyon "$ALT"',
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
# A16 — ön-denetim ALAN VARLIĞINI da sorar (G3b Task 3; Task 2 incelemesi M1 → Rol-1 IMPORTANT)
# =================================================================================================
# Ölçüm (Task 2 incelemesi X5): bekçinin sohbet `.env`i VAR ama `HINDSIGHT_API_KEY=` satırı YOK → `--tenant` dosya
# kapısından geçiyordu; yedek alındı, render hedefi ve şefin kopyası YENİ değerle yazıldı, bekçide `yaz-env` "satırı 0 kez
# bulundu" ile öldü, restart yok — Review Focus 2'nin yasakladığı yarım rotasyon, dosya değil ALAN sınıfında. Kapı artık
# her `env` hedefinin alanını, `yaz-env`in AYNI kuralıyla (TAM 1 satır, `_env_satiri`) HİÇBİR yazımdan önce sınar.

def _alan_bozuk_sahne(kok: pathlib.Path, bozukluk: str) -> None:
    y = kok / EKSIK_YOL.lstrip("/")
    satirlar = y.read_text(encoding="utf-8").splitlines(True)
    _iddia(sum(s.startswith(EKSIK_ALAN + "=") for s in satirlar) == 1, "sahne: alan tam bir kez değil (pozitif kontrol)")
    if bozukluk == "alan_yok":
        y.write_text("".join(s for s in satirlar if not s.startswith(EKSIK_ALAN + "=")), encoding="utf-8")
    else:
        y.write_text("".join(satirlar) + f"{EKSIK_ALAN}={ESKI['tenant']}\n", encoding="utf-8")


@pytest.mark.parametrize("kip", ["eski", "vault"])
@pytest.mark.parametrize("bozukluk,hal", [("alan_yok", "ALAN YOK"), ("cift_satir", "ÇİFT SATIR (2)")],
                         ids=["alan_yok", "cift_satir"])
def test_A16_on_denetim_ALAN_eksik_ya_da_CIFTSE_HICBIR_yazim_yok(tmp_path, kip, bozukluk, hal):
    """Dosya VAR, alan yok ya da iki kez: kasaya put · yedek · değer üretimi · ilk satır HİÇBİRİ yok; render hedefi ve öteki
    kopyaların sha256'sı aynı; restart yok; istem açılmaz. stderr yolu VE alanı ADIYLA söyler ve `--tohumla-sohbet`in bu
    hâli düzeltmediğini (yalnız YOKSA yazar) + elle düzeltme yolunu söyler."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    _alan_bozuk_sahne(kok, bozukluk)
    ek = ("--vault",) if kip == "vault" else ()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--tenant", *ek, girdi=GIRDI)
    ih = []
    if r.returncode == 0:
        ih.append("çıkış 0 — alan sorunlu hedefte koşum DURMADI")
    if f"alan {hal}: {EKSIK_YOL} [{EKSIK_ALAN}]" not in r.stderr:
        ih.append("stderr yolu + alanı + hâli ADIYLA söylemiyor")
    if "YALNIZ YOKSA" not in r.stderr or "elle" not in r.stderr:
        ih.append("stderr tohumlamanın bu hâli düzeltmediğini / elle düzeltmeyi söylemiyor")
    if _yedekler(kok):
        ih.append("yedek dizini OLUŞTU")
    if _imzalar(kok) != once:
        ih.append("dosya DEĞİŞTİ (sha256) — yarım rotasyon")
    if kasa_log.exists() and v521._kv_put_yollari(kasa_log):
        ih.append("kasaya `kv put` YAPILDI")
    if _systemctl_log(kok):
        ih.append("birim yeniden BAŞLATILDI")
    if "(boş = bu bacağı atla)" in r.stderr or "yeni değer üretildi" in r.stdout:
        ih.append("değer istemi AÇILDI / değer ÜRETİLDİ")
    _iddia(not ih, f"--tenant {' '.join(ek)} [{bozukluk}]:\n" + "\n".join(ih) + "\n" + _ozet(r))


def test_A16b_alan_DEGERSIZ_tek_satirsa_on_denetim_GECER_ve_rotasyon_yazar(tmp_path):
    """Ters yüz (kural `yaz-env`inkiyle AYNI — "alan VAR" = TAM 1 satır, değer boş olabilir): elle eklenen değersiz
    `HINDSIGHT_API_KEY=` satırı kapıdan geçer ve rotasyon değeri kendisi yazar — iletinin önerdiği elle düzeltme ÇALIŞIR."""
    kok, ortam = _sahte_ortam(tmp_path)
    y = kok / EKSIK_YOL.lstrip("/")
    y.write_text("".join(s if not s.startswith(EKSIK_ALAN + "=") else f"{EKSIK_ALAN}=\n"
                         for s in y.read_text(encoding="utf-8").splitlines(True)), encoding="utf-8")
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    yeni = (kok / TENANT_KRED_KAYNAK.lstrip("/")).read_text(encoding="utf-8").strip()
    _iddia(yeni != ESKI["tenant"] and _env_alan(y, EKSIK_ALAN) == yeni, "değersiz satır yeni değeri almadı")


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
    """Mevcut birimler için davranış BİREBİR: koşulsuz birime `is-active` hiç sorulmaz, restart kümesi ve sırası v557/v561
    `TENANT_BIRIMLER` ile aynı. M3 (Task 2, 2026-10-01): `--tenant`in tüketici kümesine iki koşullu birim GİRDİ — soru
    artık TAM OLARAK `_KOSULLU_BIRIMLER`e sorulur (ikisi de sahnede `inactive` → ATLANDI, restart pini değişmez)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(set(_is_active_sorulari(kok)) == set(KOSULLU_BIRIMLER),
           f"is-active sorulan birimler {sorted(set(_is_active_sorulari(kok)))} ≠ koşullu küme")
    _iddia(_systemctl_log(kok) == TENANT_BIRIMLER, f"restart: {_systemctl_log(kok)}")
    _iddia(not [s for s in r.stdout.splitlines() if "ATLANDI" in s and not any(b in s for b in KOSULLU_BIRIMLER)],
           "koşulsuz birim ATLANDI")


def test_A15_KULLANIM_basligi_kosullu_birimi_TEK_satirla_soyler():
    metin = BETIK.read_text(encoding="utf-8")
    baslik = metin[: metin.index("\nset -euo pipefail\n")]
    kullanim = baslik[baslik.index("# KULLANIM"):]
    satirlar = [s for s in kullanim.splitlines() if "_KOSULLU_BIRIMLER" in s]
    _iddia(len(satirlar) == 1 and "YALNIZ ETKİNSE" in satirlar[0] and "ATLANDI" in satirlar[0],
           f"KULLANIM satırı: {satirlar}")


# =================================================================================================
# BÖLÜM B (G3b Task 2) — API_SERVER_KEY ZİNCİRİ · KİRACI ANAHTARININ SOHBET KOPYALARI · CREDENTIAL DROP-IN'LERİ
# =================================================================================================
# ÖLÇÜLMÜŞ ZEMİN (plan "Ölçülmüş zemin", Rol-1 A1 Hermes v0.19 kaynağı 2026-09-30): `API_SERVER_KEY` PROFİL
# kapsamlıdır — `/p/<profil>/…` isteğinin anahtarı o profilin `.env`inden (`secret_scope.get_secret`) okunur ve yoksa
# ya da <16 karakterse 401. Anahtar TEK sırdır, DÖRT kopyası vardır (kök + sohbet profilleri) ve Telegram dinleyicisi
# AYNI değeri credential'dan (55 drop-in) okur. Bot listesi kabukta TEK sabittir (`_SOHBET_BOTLARI`); satırlar
# döngüyle türer ve envanter aynası üreteçle (`ops/sir_envanteri_bot_uret.py`, `--kontrol` çivili) yazılır.

DEFAULTS = KOK_DEPO / "deploy/ansible/roles/meridian_a1/defaults/main.yml"
ENVANTER_YOLU = KOK_DEPO / "deploy/sir_envanteri.yaml"
URETEC = KOK_DEPO / "ops/sir_envanteri_bot_uret.py"
BIRIM_DIZINI = KOK_DEPO / "deploy/oracle-a1"
API_SIR = "API_SERVER_KEY"
API_REF = "/etc/meridian/api_server_key"
TENANT_SIR = "HINDSIGHT_API_TENANT_API_KEY"
TENANT_REF = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
SOHBET_TENANT_ALANI = "HINDSIGHT_API_KEY"
KANIT_YOK = f"KANIT: ölçülemedi — {BOTLAR} etkin değil (inactive)"


def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _sohbet_profilleri() -> list[str]:
    return list(_defaults()["sohbet_profil_adlari"])


def _sohbet_koku() -> str:
    d = _defaults()
    return d["sohbet_kok_dizini"].replace("{{ meridian_kullanici }}", d["meridian_kullanici"])


def _profil_env(ad: str) -> str:
    return f"{_sohbet_koku()}/profiles/{ad}/.env"


def _kok_env() -> str:
    return f"{_sohbet_koku()}/.env"


def _p(kok: pathlib.Path, yol: str) -> pathlib.Path:
    return kok / yol.lstrip("/")


def _alan(kok: pathlib.Path, yol: str, alan: str) -> str | None:
    for s in _p(kok, yol).read_text(encoding="utf-8").splitlines():
        if s.startswith(alan + "="):
            return s.split("=", 1)[1]
    return None


def _dosya_degeri(kok: pathlib.Path, yol: str) -> str:
    return _p(kok, yol).read_text(encoding="utf-8").strip()


def _deger_ciktida_yok(r: subprocess.CompletedProcess, kok: pathlib.Path, deger: str) -> list[str]:
    ih = []
    for ad, metin in (("stdout", r.stdout), ("stderr", r.stderr),
                      ("şim argv", (kok / ".sahte/argv.log").read_text(encoding="utf-8"))):
        if deger in metin:
            ih.append(f"yeni değer {ad} içinde")
    return ih


def test_B0_SAHNE_bot_agi_dunyasini_tasir(tmp_path):
    """Pozitif kontrol: v447 sahnesi bot ağ geçidinin hedef dünyasını kurar (dört `.env` + render hedefi + botlar'ın
    açılış anahtarı) — yoksa B bölümünün her çivisi var olmayan bir dünyayı ölçerdi. Liste betikten türer."""
    kok, _ = _sahte_ortam(tmp_path)
    _iddia(_p(kok, _kok_env()).is_file() and _p(kok, API_REF).is_file(), "kök .env ya da render hedefi sahnede yok")
    for ad in _sohbet_profilleri():
        _iddia(_p(kok, _profil_env(ad)).is_file(), f"{ad} sohbet .env'i sahnede yok")
    _iddia((kok / ".sahte/botlar_api_anahtari").is_file(), "botlar açılış anahtarı sahnede yok")


# --- B1/B2 — tablo ------------------------------------------------------------------------------------

def test_B1_API_SERVER_KEY_dort_kopya_ayni_sir():
    """`API_SERVER_KEY`in REFERANSI Agent render hedefi (`dosya /etc/meridian/api_server_key`), ardından kök + her sohbet
    profili için TAM BİR `env` satırı (alan `API_SERVER_KEY`, alt komut `api-sunucu`). Beklenen yol listesi A0'ın
    `sohbet_profil_adlari`/`sohbet_kok_dizini`nden TÜRER; kabukta profil adı literal geçmez (ikinci liste yok)."""
    k = _betik_kopyalari()
    api = [x for x in k if x["sir"] == API_SIR]
    _iddia(bool(api) and api[0]["tur"] == "dosya" and api[0]["yol"] == API_REF,
           f"referans render hedefi değil: {api[:1]}")
    profiller = _sohbet_profilleri()
    _iddia(len(profiller) >= 1, "sohbet_profil_adlari boş — çivi kör (pozitif kontrol)")
    beklenen = [_kok_env()] + [_profil_env(ad) for ad in profiller]
    env = api[1:]
    _iddia([x["yol"] for x in env] == beklenen, f"env kopyaları: {[x['yol'] for x in env]} ≠ {beklenen}")
    _iddia(all(x["tur"] == "env" and x["alan"] == API_SIR and x["mod"] == "koru" and x["sahip"] == "koru"
               for x in env), f"env satırı biçimi: {env}")
    _iddia({x["alt"] for x in api} == {"api-sunucu"}, f"alt komut: {sorted({x['alt'] for x in api})}")
    metin = BETIK.read_text(encoding="utf-8")
    # Rapor profilleri (`~/.hermes/profiles/<ad>`) AYRI bir dünyadır ve tabloda literal durur (openrouter satırları);
    # yasak olan SOHBET kökünün profil yolunu elle yazmaktır — o satırlar `_SOHBET_BOTLARI` döngüsünden türer.
    elle = [ad for ad in profiller
            if f"{_sohbet_koku()}/profiles/{ad}" in metin or f"$_SOHBET_KOKU/profiles/{ad}" in metin]
    _iddia(not elle, f"kabukta sohbet profil yolu LİTERAL yazılmış (ikinci liste): {elle}")


def test_B2_tenant_sohbet_kopyalari():
    """Kiracı anahtarının bloğu: referans (render hedefi) İLK, ardından her sohbet profili için `HINDSIGHT_API_KEY`
    satırı — BİTİŞİK. Bitişiklik genel kuraldır (REFERANS KURALI): her sırrın satırları tabloda tek blok."""
    k = _betik_kopyalari()
    t = [x for x in k if x["sir"] == TENANT_SIR]
    _iddia(t[0]["tur"] == "dosya" and t[0]["yol"] == TENANT_REF, f"referans: {t[0]}")
    beklenen = [_profil_env(ad) for ad in _sohbet_profilleri()]
    _iddia([x["yol"] for x in t[1:]] == beklenen, f"tenant kopyaları: {[x['yol'] for x in t[1:]]}")
    _iddia(all(x["tur"] == "env" and x["alan"] == SOHBET_TENANT_ALANI and x["alt"] == "tenant" for x in t[1:]),
           f"tenant sohbet satırı biçimi: {t[1:]}")
    for sir in {x["sir"] for x in k}:
        idx = [i for i, x in enumerate(k) if x["sir"] == sir]
        _iddia(idx == list(range(idx[0], idx[0] + len(idx))), f"{sir} satırları BİTİŞİK değil: {idx}")


# --- B3/B4 — `--api-sunucu` davranışı ---------------------------------------------------------------

def _api_hedefleri() -> list[str]:
    return [API_REF, _kok_env()] + [_profil_env(ad) for ad in _sohbet_profilleri()]


def _api_degerleri(kok: pathlib.Path) -> list[str | None]:
    return [_dosya_degeri(kok, API_REF)] + [_alan(kok, y, API_SIR) for y in _api_hedefleri()[1:]]


def test_B3_api_sunucu_sahte_ortamda_doner(tmp_path):
    """Eski yol: render hedefi + dört `.env` kopyası AYNI yeni değeri taşır (64 hex, eskiden farklı); kök `.env`in
    öteki satırları ve profil `.env`lerinin öteki alanları bayt-eşit; değer hiçbir çıktıda/argv'de yok; botlar etkin
    değil → kanıt ADIYLA "ölçülemedi", çıkış 0, `/health/detailed` hiç yoklanmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    kok_diger = [s for s in _p(kok, _kok_env()).read_text(encoding="utf-8").splitlines()
                 if not s.startswith(API_SIR + "=")]
    profil_diger = {y: [s for s in _p(kok, y).read_text(encoding="utf-8").splitlines() if not s.startswith(API_SIR + "=")]
                    for y in _api_hedefleri()[2:]}
    _iddia(set(_api_degerleri(kok)) == {ESKI["api"]}, "tohum: dört kopya + referans eşit değil")
    r = _kos(BETIK, ortam, "--api-sunucu")
    _iddia(r.returncode == 0, _ozet(r))
    degerler = _api_degerleri(kok)
    _iddia(len(set(degerler)) == 1 and degerler[0] != ESKI["api"], "kopyalar AYNI yeni değeri taşımıyor")
    _iddia(bool(re.fullmatch(r"[0-9a-f]{64}", degerler[0] or "")), "yeni değer 64 küçük hex değil (sınıf hex)")
    _iddia([s for s in _p(kok, _kok_env()).read_text(encoding="utf-8").splitlines()
            if not s.startswith(API_SIR + "=")] == kok_diger, "kök .env'in öteki satırları DEĞİŞTİ")
    for y, diger in profil_diger.items():
        _iddia([s for s in _p(kok, y).read_text(encoding="utf-8").splitlines()
                if not s.startswith(API_SIR + "=")] == diger, f"{y}: öteki alanlar DEĞİŞTİ")
    ih = _deger_ciktida_yok(r, kok, degerler[0])
    _iddia(not ih, "\n".join(ih))
    _iddia(KANIT_YOK in r.stdout, f"kanıt satırı yok\n{_ozet(r)}")
    _iddia(not [u for u in _url_log(kok) if u.endswith("/health/detailed")], "etkin olmayan botlar yoklandı")
    _iddia(_systemctl_log(kok) == [], f"etkin olmayan birim yeniden başlatıldı: {_systemctl_log(kok)}")


def _etkin_botlar(kok: pathlib.Path, *birimler: str) -> None:
    (kok / ".sahte/etkin_birimler").write_text("".join(b + "\n" for b in birimler), encoding="utf-8")


def test_B4_api_sunucu_etkin_botlarda_kanit_ister(tmp_path):
    """Botlar ETKİN: restart + `/health` hazırlığı + kanıt `GET /health/detailed` İKİ kez (yeni → 200, eski → 401)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    _etkin_botlar(kok, BOTLAR)
    r = _kos(BETIK, ortam, "--api-sunucu")
    _iddia(r.returncode == 0, _ozet(r))
    detay = [u for u in _url_log(kok) if u == f"{BOTLAR_KOK}/health/detailed"]
    _iddia(len(detay) == 2, f"/health/detailed çağrı sayısı {len(detay)} (2 bekleniyordu)")
    _iddia("botlar /health/detailed: yeni→200 · eski→401" in r.stdout, f"kanıt satırı yok\n{_ozet(r)}")
    _iddia(_systemctl_log(kok) == [BOTLAR], f"restart: {_systemctl_log(kok)}")
    _iddia("KANIT: ölçülemedi" not in r.stdout, "etkin botlarda kanıt atlandı")


def test_B4b_kanit_ANAHTARA_BAGLI_degilse_cikis_2(tmp_path):
    """İki hüküm birden: yüzey anahtara KÖR olursa (`SAHTE_KOR`) eski değer de 200 alır → `ÖLÇÜLEMEDİ`, çıkış 2."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam.update(SIR_ROT_BOTLAR=BOTLAR_KOK, SAHTE_KOR="1")
    _etkin_botlar(kok, BOTLAR)
    r = _kos(BETIK, ortam, "--api-sunucu")
    _iddia(r.returncode == 2 and "ÖLÇÜLEMEDİ" in r.stderr and "/health/detailed" in r.stderr, _ozet(r))


def test_B4c_api_sunucu_KURU_plani_kaniti_ve_kosullu_birimleri_soyler(tmp_path):
    kok, ortam = _sahte_ortam(tmp_path)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--api-sunucu", "--kuru")
    _iddia(r.returncode == 0 and "KURU KOŞUM: --api-sunucu" in r.stdout, _ozet(r))
    _iddia("/health/detailed" in r.stdout, f"kanıt planı yok\n{_ozet(r)}")
    for b in (BOTLAR, TELEGRAM):
        _iddia(f"    · {b} — şu an: inactive → ATLANACAK" in r.stdout.splitlines(), _ozet(r))
    _iddia(_imzalar(kok) == once and not _yedekler(kok), "kuru koşum YAZDI")


def test_B4d_referans_YOKSA_hicbir_sey_yazilmaz(tmp_path):
    """İlk değer kasaya RUNBOOK borusuyla konur (Rol-1 G3b-R6); referans yokken eski yol ESKİ değeri okuyamaz →
    yedek dahil HİÇBİR yazım olmadan durur."""
    kok, ortam = _sahte_ortam(tmp_path)
    _p(kok, API_REF).unlink()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--api-sunucu")
    _iddia(r.returncode != 0 and API_REF in r.stderr, _ozet(r))
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok), "referanssız koşum YAZDI")


# --- B5/B6 — `--tenant` sohbet kopyaları ve koşullu tüketiciler ---------------------------------------

def test_B5_tenant_sohbet_kopyalarini_birlikte_dondurur(tmp_path):
    kok, ortam = _sahte_ortam(tmp_path)
    once_api = {ad: _alan(kok, _profil_env(ad), API_SIR) for ad in _sohbet_profilleri()}
    once_bot = {ad: _alan(kok, _profil_env(ad), f"BOT_KEY_{ad.upper()}") for ad in _sohbet_profilleri()}
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    yeni = _dosya_degeri(kok, TENANT_REF)
    _iddia(yeni != ESKI["tenant"], "kiracı anahtarı dönmedi")
    for ad in _sohbet_profilleri():
        y = _profil_env(ad)
        _iddia(_alan(kok, y, SOHBET_TENANT_ALANI) == yeni, f"{ad}: sohbet kopyası yeni değeri taşımıyor")
        _iddia(_alan(kok, y, API_SIR) == once_api[ad] and _alan(kok, y, f"BOT_KEY_{ad.upper()}") == once_bot[ad],
               f"{ad}: komşu alan DEĞİŞTİ")
    ih = _deger_ciktida_yok(r, kok, yeni)
    _iddia(not ih, "\n".join(ih))


@pytest.mark.parametrize("etkin", [False, True], ids=["etkin_degil", "etkin"])
def test_B6_telegram_ve_botlar_tenant_restart_yalniz_etkinse(tmp_path, etkin):
    """A2/A3'ün tenant yolu üzerinden tekrarı (gerçek tablo): etkin değilse ATLANDI + credential/hazırlık yok;
    etkinse koşulsuz birimlerden SONRA restart, iki birimin kiracı credential'ı ölçülür, botlar `/health` beklenir."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    if etkin:
        _etkin_botlar(kok, BOTLAR, TELEGRAM)
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    if not etkin:
        _iddia(_systemctl_log(kok) == TENANT_BIRIMLER, f"restart: {_systemctl_log(kok)}")
        for b in (BOTLAR, TELEGRAM):
            _iddia(f"ATLANDI (etkin değil: inactive): {b}" in r.stdout, f"{b} ATLANDI yok\n{_ozet(r)}")
            _iddia(f"/run/credentials/{b}/" not in r.stdout + r.stderr, f"{b} credential denetimi İSTENDİ")
        _iddia(not [u for u in _url_log(kok) if u.startswith(BOTLAR_KOK)], "etkin olmayan botlar yoklandı")
    else:
        _iddia(_systemctl_log(kok) == TENANT_BIRIMLER + [BOTLAR, TELEGRAM], f"restart: {_systemctl_log(kok)}")
        for b in (BOTLAR, TELEGRAM):
            _iddia(f"credential dolu: /run/credentials/{b}/{TENANT_SIR}" in r.stdout, f"{b} credential\n{_ozet(r)}")
        _iddia("hazır: meridian-botlar" in r.stdout and "ATLANDI" not in r.stdout, _ozet(r))
    _iddia(set(_is_active_sorulari(kok)) == {BOTLAR, TELEGRAM}, f"is-active: {_is_active_sorulari(kok)}")


# --- B7/B8 — drop-in'ler ----------------------------------------------------------------------------

def _credential_satirlari(conf: pathlib.Path) -> list[str]:
    return [s.strip() for s in conf.read_text(encoding="utf-8").splitlines() if s.strip().startswith("LoadCredential")]


def _bot_kanal_kimligi() -> str:
    m = re.findall(r'credential_oku\("([A-Z_]+)"\)', (KOK_DEPO / "meridian/bot_kanal.py").read_text(encoding="utf-8"))
    _iddia(len(set(m)) == 1, f"bot_kanal credential kimliği tek değil: {m}")
    return m[0]


def test_B7_drop_in_icerigi_emsalle_ayni():
    """Botlar ve Telegram'ın `54-hafiza-credential.conf` LoadCredential satırı `meridian.service.d/54`ün AYNISI;
    Telegram'ın `55-api-sunucu-credential.conf`u kimliği `bot_kanal`ın okuduğu addan, kaynağı envanterin
    `api_server_key.hedef`inden alır. Boş `LoadCredential=` YOK (listeyi sıfırlardı); başlık şerh deseni aynı."""
    emsal = _credential_satirlari(BIRIM_DIZINI / "meridian.service.d/54-hafiza-credential.conf")
    _iddia(len(emsal) == 1, f"emsal: {emsal}")
    for b in (BOTLAR, TELEGRAM):
        conf = BIRIM_DIZINI / f"{b}.d/54-hafiza-credential.conf"
        _iddia(conf.is_file(), f"{conf.relative_to(KOK_DEPO)} yok")
        _iddia(_credential_satirlari(conf) == emsal, f"{b}: {_credential_satirlari(conf)} ≠ {emsal}")
    kv = {g["ad"]: g for g in yaml.safe_load(ENVANTER_YOLU.read_text(encoding="utf-8"))["vault_kv"]}
    _iddia("api_server_key" in kv, "envanterde vault_kv.api_server_key yok")
    api_conf = BIRIM_DIZINI / f"{TELEGRAM}.d/55-api-sunucu-credential.conf"
    _iddia(api_conf.is_file(), "telegram 55 drop-in'i yok")
    _iddia(_credential_satirlari(api_conf) == [f"LoadCredential={_bot_kanal_kimligi()}:{kv['api_server_key']['hedef']}"],
           f"55: {_credential_satirlari(api_conf)}")
    for conf in (*sorted((BIRIM_DIZINI / f"{BOTLAR}.d").glob("*.conf")),
                 *sorted((BIRIM_DIZINI / f"{TELEGRAM}.d").glob("*.conf"))):
        metin = conf.read_text(encoding="utf-8")
        _iddia(not re.search(r"^\s*LoadCredential=\s*$", metin, re.M), f"{conf.name}: boş LoadCredential= ataması")
        _iddia(metin.startswith("# ====") and "BU DOSYA KENDİLİĞİNDEN ETKİN DEĞİLDİR" in metin,
               f"{conf.name}: emsal başlık deseni yok")


def test_B8_botlar_birimi_API_SERVER_KEY_credential_TASIMAZ():
    """Hermes `API_SERVER_KEY`i PROFİL `.env`inden okur (`secret_scope.get_secret`, çoklu kipte kapsam yetkili,
    `os.environ`a/credential'a düşmez) — botlar birimindeki bir credential okunmayan bir kopya olurdu (Yasa 6) ve
    rotasyon onu "döndü" sayardı. Pozitif kontrol: denetçi aynı birimde hafıza credential'ını GÖRÜYOR."""
    from tests.test_bot_agi_gecidi_v601 import _credential_yonergeleri
    yon = _credential_yonergeleri(BIRIM_DIZINI / BOTLAR)
    _iddia(any(d.split(":", 1)[0] == TENANT_SIR for _, _, d in yon), f"pozitif kontrol: {yon}")
    _iddia(not [d for _, _, d in yon if d.split(":", 1)[0] == API_SIR], f"botlar API_SERVER_KEY credential taşıyor: {yon}")
    _iddia(not [x for x in _betik_kopyalari() if x["sir"] == API_SIR and x["tur"] == "dosya" and BOTLAR in x["yol"]],
           "tabloda botlar credential satırı")


# --- B9 — bot listesi TEK kaynak --------------------------------------------------------------------

def test_B9_bot_listesi_TEK_kaynak_kabuk_A0_kadro():
    """Kabuktaki TEK liste (`_SOHBET_BOTLARI`) = A0 `sohbet_profil_adlari` (sıra dahil) = kadronun aktif botları; kök =
    `sohbet_kok_dizini`. Envanter `dosyalar` satırının `<…>` kümesi ve `_taranan_dosyalar` aynı listeden."""
    from meridian import kadro
    kabuk = _betik_sabiti("_SOHBET_BOTLARI")
    _iddia(kabuk == _sohbet_profilleri(), f"_SOHBET_BOTLARI {kabuk} ≠ sohbet_profil_adlari {_sohbet_profilleri()}")
    _iddia(set(kabuk) == {b.ad for b in kadro.aktif_botlar()}, f"kadro aktif: {[b.ad for b in kadro.aktif_botlar()]}")
    _iddia(_betik_sabiti("_SOHBET_KOKU") == [_sohbet_koku()], f"kök: {_betik_sabiti('_SOHBET_KOKU')}")
    satir = [d["yol"] for d in yaml.safe_load(ENVANTER_YOLU.read_text(encoding="utf-8"))["dosyalar"]
             if d["yol"].startswith("~/.hermes-botlar/profiles/")]
    _iddia(len(satir) == 1, f"dosyalar sohbet profil satırı: {satir}")
    m = re.search(r"<([^>]*)>", satir[0])
    _iddia(bool(m) and set(m.group(1).split(",")) == set(kabuk), f"dosyalar satırı bot kümesi: {satir[0]}")
    kod = (f'_SOHBET_KOKU="{_sohbet_koku()}"\n_SOHBET_BOTLARI="{" ".join(kabuk)}"\n'
           + v521._fonksiyon("_taranan_dosyalar") + "_taranan_dosyalar\n")
    r = subprocess.run(["bash", "-c", kod], capture_output=True, text=True)
    _iddia(r.returncode == 0, r.stderr)
    taranan = set(r.stdout.split())
    sohbet_yollari = {x["yol"] for x in _betik_kopyalari() if x["yol"].startswith(_sohbet_koku() + "/")}
    _iddia(sohbet_yollari and sohbet_yollari <= taranan, f"taranmayan sohbet .env: {sorted(sohbet_yollari - taranan)}")


# --- B10 — ön-denetim süzgeçleri (Task 1 incelemesi M2) ---------------------------------------------

def test_B10_on_denetim_ALT_suzgeci_baska_alt_komutu_DURDURMAZ(tmp_path):
    """Bir alt komutun eksik hedefi BAŞKA bir alt komutu durdurmaz: sohbet `.env`i yokken `--dash` (hiç sohbet hedefi
    yok) koşar; `--tenant` ise o yolu ADIYLA söyleyip durur."""
    kok, ortam = _sahte_ortam(tmp_path)
    _eksik_hedefi_sil(kok)
    r = _kos(BETIK, ortam, "--dash")
    _iddia(r.returncode == 0 and "hedef dosya YOK" not in r.stderr, f"--dash başka alt komutun hedefine takıldı\n{_ozet(r)}")
    r2 = _kos(BETIK, ortam, "--tenant")
    _iddia(r2.returncode != 0 and f"hedef dosya YOK: {EKSIK_YOL}" in r2.stderr, _ozet(r2))


def test_B10b_on_denetim_TEKILLESTIRIR_yol_bir_kez_sayilir(tmp_path):
    """`/opt/hindsight/.env` altı `--openrouter` satırının hedefidir: yokken yol stderr'de TAM BİR kez ve sayaç 1."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/hindsight/.env").unlink()
    r = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI)
    _iddia(r.returncode != 0, _ozet(r))
    _iddia(r.stderr.count("hedef dosya YOK: /opt/hindsight/.env") == 1, f"yol tekrarlandı\n{_ozet(r)}")
    _iddia("--openrouter: 1 hedef dosya YOK" in r.stderr, f"sayaç\n{_ozet(r)}")


# --- B11 — reçeteler koşullu birimi BAŞLATTIRMAZ (Task 1 incelemesi M1) -----------------------------

def _ciplak_kosullu(metin: str) -> list[str]:
    """Reçete satırlarında (`geri alma` · `yeniden başlat`) koşullu birimi `try-restart`ın DIŞINDA anan satırlar —
    operatör o satırı yapıştırırsa etkin olmayan birimi BAŞLATIR."""
    out = []
    for s in metin.splitlines():
        if "geri alma" not in s.lower() and "yeniden başlat" not in s:
            continue
        for b in KOSULLU_BIRIMLER:
            if b in s and ("try-restart" not in s or s.index(b) < s.index("try-restart")):
                out.append(s)
                break
    return out


@pytest.mark.parametrize("alt", ["tenant", "api-sunucu"])
def test_B11_ESKI_YOL_receteleri_kosullu_birimi_YALNIZ_try_restart_ile_anar(tmp_path, alt):
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, f"--{alt}")
    _iddia(r.returncode == 0, _ozet(r))
    metin = r.stdout + "\n" + r.stderr
    _iddia(not _ciplak_kosullu(metin), "çıplak koşullu birim:\n" + "\n".join(_ciplak_kosullu(metin)))
    _iddia(f"sudo systemctl try-restart {BOTLAR} {TELEGRAM}" in r.stderr, f"GERİ ALMA reçetesi koşullu birimi anmıyor\n{_ozet(r)}")
    _iddia(f"try-restart {BOTLAR} {TELEGRAM}" in r.stdout, f">> geri alma satırı koşullu birimi anmıyor\n{_ozet(r)}")


def test_B11b_KASA_receteleri_kosullu_birimi_YALNIZ_try_restart_ile_anar(tmp_path):
    from tests import test_sir_uret_v557 as v557
    kok, ortam, log, durum = v557._ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    metin = r.stdout + "\n" + r.stderr
    _iddia(not _ciplak_kosullu(metin), "çıplak koşullu birim:\n" + "\n".join(_ciplak_kosullu(metin)))
    _iddia(f"4) sonra yeniden başlat: " in r.stderr and f"try-restart {BOTLAR} {TELEGRAM}" in r.stderr, _ozet(r))


def test_B11c_STATIK_her_recete_birim_listesi_tek_yardimcidan():
    """Reçete basan HER satır (`>> geri alma` · `sonra yeniden başlat`) birim listesini `_recete_birimleri`nden alır —
    yeni bir alt komutun reçetesi `_birimler`i çıplak basarsa öter (dinamik çiviler yalnız koşturulan alt komutları görür)."""
    satirlar = [s for s in BETIK.read_text(encoding="utf-8").splitlines()
                if not s.lstrip().startswith("#") and (">> geri alma" in s or "sonra yeniden başlat" in s)
                and ("$(_birimler" in s or "$birimler" in s)]
    _iddia(len(satirlar) >= 7, f"reçete satırı çok az ({len(satirlar)}) — tarama kör")
    ciplak = [s.strip() for s in satirlar if "_recete_birimleri" not in s]
    _iddia(not ciplak, "çıplak reçete satırı:\n" + "\n".join(ciplak))


# --- B12 — envanter aynası üreteçle (bot sayısından bağımsız) ----------------------------------------

def _uretec(*args: str, betik: pathlib.Path | None = None,
            envanter: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(URETEC), *args]
    if betik is not None:
        cmd += ["--betik", str(betik)]
    if envanter is not None:
        cmd += ["--envanter", str(envanter)]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(KOK_DEPO))


def test_B12_envanter_bot_satirlari_URETECLE_guncel():
    r = _uretec("--kontrol")
    _iddia(r.returncode == 0, f"çıkış {r.returncode}\n{r.stdout}\n{r.stderr}")


def _yeni_botlu_betik(tmp_path: pathlib.Path) -> pathlib.Path:
    eski = f'_SOHBET_BOTLARI="{" ".join(_betik_sabiti("_SOHBET_BOTLARI"))}"'
    return _mutant(tmp_path, (eski, eski[:-1] + ' yenibot"'), ad="yeni_botlu.sh")


def test_B12b_YENI_BOT_envanteri_BAYAT_yapar_uygula_tamamlar(tmp_path):
    """Listeye bir ad eklemek envanter aynasını BAYAT yapar (`--kontrol` 1); `--uygula` (kopya envanterde) yeni botun
    satırlarını tenant ve api-sunucu bloklarına + kiracı takma adının `kopya_kaynaklari`na yazar — elle satır yok."""
    betik = _yeni_botlu_betik(tmp_path)
    r = _uretec("--kontrol", betik=betik)
    _iddia(r.returncode == 1, f"yeni bot envanteri bayat yapmadı: {r.returncode}\n{r.stdout}\n{r.stderr}")
    env = tmp_path / "envanter.yaml"
    env.write_text(ENVANTER_YOLU.read_text(encoding="utf-8"), encoding="utf-8")
    r = _uretec("--uygula", betik=betik, envanter=env)
    _iddia(r.returncode == 0, f"{r.stdout}\n{r.stderr}")
    r = _uretec("--kontrol", betik=betik, envanter=env)
    _iddia(r.returncode == 0, f"uygula sonrası bayat\n{r.stdout}\n{r.stderr}")
    veri = yaml.safe_load(env.read_text(encoding="utf-8"))
    yol = f"{_sohbet_koku()}/profiles/yenibot/.env"
    satirlar = {(k["alt_komut"], k["sir"], k["alan"]) for k in veri["rotasyon_kopyalari"]["kopyalar"] if k["yol"] == yol}
    # 2026-10-01 (G3b Task 3): yeni botun sohbet `.env`ine `kapi-bot-<ad>` ailesinin satırı da yazar (C9 bloğun tamamını ölçer).
    _iddia(satirlar == {("tenant", TENANT_SIR, SOHBET_TENANT_ALANI), ("api-sunucu", API_SIR, API_SIR),
                        ("kapi-bot-yenibot", "BOT_KEY_YENIBOT", "BOT_KEY_YENIBOT")}, f"{satirlar}")
    kk = [k for g in veri["vault_kv"] for k in (g.get("kopya_kaynaklari") or []) if k["dosya"] == yol]
    _iddia(kk == [{"tur": "env_satiri", "dosya": yol, "alan": SOHBET_TENANT_ALANI, "onek": None}], f"{kk}")


def test_B12c_ELLE_silinen_bot_satiri_kontrolde_oter(tmp_path):
    ham = ENVANTER_YOLU.read_text(encoding="utf-8")
    capa = f'      yol: "{_profil_env(_sohbet_profilleri()[-1])}"\n      alan: {SOHBET_TENANT_ALANI}\n'
    _iddia(ham.count(capa) == 1, "mutasyon çapası envanterde tek değil")
    env = tmp_path / "envanter.yaml"
    env.write_text(ham.replace(capa, f'      yol: "{_profil_env(_sohbet_profilleri()[-1])}"\n      alan: YANLIS_ALAN\n'),
                   encoding="utf-8")
    r = _uretec("--kontrol", envanter=env)
    _iddia(r.returncode == 1, f"elle bozulan bölge yakalanmadı: {r.returncode}\n{r.stdout}\n{r.stderr}")


def test_B12d_kontrol_ile_uygula_birlikte_KULLANIM_hatasi():
    """Biri SORAR öteki YAZAR — sessiz öncelik yok (`ops/vault_politika_uret.py` emsali). Çıkış 2 tek başına yetmez:
    dosya yokken python da 2 döner; hüküm üretecin KENDİ kullanım metnidir."""
    _iddia(URETEC.is_file(), f"{URETEC.relative_to(KOK_DEPO)} yok")
    r = _uretec("--kontrol", "--uygula")
    _iddia(r.returncode == 2 and "KULLANIM" in r.stdout + r.stderr, f"çıkış {r.returncode}\n{r.stdout}\n{r.stderr}")


# --- B13 — kanal beyanı: hermes `.env` kopyaları kapatılacak eski kanal DEĞİL -------------------------

@pytest.mark.parametrize("alt,hedef", [("tenant", TENANT_REF), ("api-sunucu", API_REF)])
def test_B13_KANAL_BEYANI_sohbet_env_kopyalari_TEK_KANALi_bozmaz(alt, hedef):
    """Kasa döngüsünün son satırı: render hedefi dışında YALNIZ C sınıfı hermes `.env` kopyası olan alt komut "TEK
    KANAL" der ve hermes kopyalarını KALICI rotasyon kanalı olarak sayıyla söyler (kapatılacak eski kanal değildir —
    hermes `.env.vault` OKUMAZ). `--openrouter` (asıl dosya satırları VAR) "İKİ KANAL AÇIK" der."""
    harness = f'_kopyalar() {{ bash "{BETIK}" --kopyalar; }}\n_SOHBET_KOKU="{_sohbet_koku()}"\n'
    kod = harness + v521._fonksiyon("_kanal_beyani") + '_kanal_beyani "$1" "$2"\n'
    r = subprocess.run(["bash", "-c", kod, "_", alt, hedef], capture_output=True, text=True)
    _iddia(r.returncode == 0, r.stderr)
    n = len([x for x in _betik_kopyalari() if x["alt"] == alt and x["yol"].startswith(_sohbet_koku() + "/")])
    _iddia(r.stdout.startswith(f">> TEK KANAL: --{alt}") and f"hermes .env kopyası ({n})" in r.stdout, r.stdout)
    r2 = subprocess.run(["bash", "-c", kod, "_", "openrouter",
                         "/etc/meridian/nous_api_key /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"],
                        capture_output=True, text=True)
    _iddia(r2.stdout.startswith(">> İKİ KANAL AÇIK"), r2.stdout)


# --- B14 — tablo borusu: okuyan TAMAMINI okur ---------------------------------------------------------

def test_B14_STATIK_kopya_tablosu_borusunda_ERKEN_cikan_okuyucu_YOK():
    """`_kopyalar` iki heredoc + döngü `echo`larıdır. Boruda ERKEN çıkan bir okuyucu (`awk '…; exit}'` · `head` ·
    `grep -q/-m`) boruyu kapatır, sonraki `echo` SIGPIPE alır ve `pipefail` + `set -e` koşumu 141 ile SESSİZCE öldürür —
    ölçüldü (G3b Task 2: `--api-sunucu` ilk satırı bulduğu an "echo: write error: Broken pipe"). `exit` yalnız `END{…}`
    içinde serbesttir. Pozitif kontrol: tarama gerçekten boru satırlarını görüyor."""
    satirlar = [s for s in BETIK.read_text(encoding="utf-8").splitlines()
                if "_kopyalar |" in s and not s.lstrip().startswith("#")]
    _iddia(len(satirlar) >= 5, f"tablo borusu satırı çok az ({len(satirlar)}) — tarama kör")
    erken = [s.strip() for s in satirlar
             if re.search(r"exit\s*\}", s.replace("END{exit", "")) or re.search(r"\|\s*(head|grep\s+-[a-z]*[qm])", s)]
    _iddia(not erken, "erken çıkan tablo okuyucusu:\n" + "\n".join(erken))


# --- B15/B16 — Task 2 incelemesinin çivi boşlukları (M5, G3b Task 3 turunda) -------------------------

def _kasa_dunyasi(tmp_path: pathlib.Path, tohumlar: dict[str, str]):
    """v556 kasa dünyası (Agent render hedefini VE yan dosyaları yazar; `kv get`/`metadata` kasadaki ESKİ değeri sunar)
    + verilen kasa yollarının ESKİ değerleri — A1 gerçeği: bağlı yollar DOLUDUR (dalga-1/2 `vault_sir_koy.sh`)."""
    kok, ortam, log, durum = v556._cp_ortami(tmp_path)
    veri = json.loads(durum.read_text(encoding="utf-8"))
    veri.update({y: [d] for y, d in tohumlar.items()})
    durum.write_text(json.dumps(veri), encoding="utf-8")
    return kok, ortam, log, durum


def _kasa_sizintisi(r: subprocess.CompletedProcess, kok: pathlib.Path, log: pathlib.Path, deger: str) -> list[str]:
    ih = _deger_ciktida_yok(r, kok, deger)
    if log.exists() and deger in log.read_text(encoding="utf-8"):
        ih.append("yeni değer kasa argv günlüğünde")
    return ih


def test_B15_api_sunucu_KASA_URET_gercek_kosum_bes_kopya_ayni_sizinti_yok(tmp_path):
    """M5(a): aracın DOĞRU yolu (`--api-sunucu --vault --uret`) gerçek koşar — `kv put` TEK yol (api_server_key), render
    hedefi + kök + üç profil `.env`i AYNI yeni 64-hex değeri taşır (eskiden farklı), koşullu birimler etkin değil → restart
    YOK (ATLANDI), değer stdout/stderr/şim argv/kasa argv'de YOK.
    2026-10-01 (G3b Task 4 — Task 3 incelemesi M1): kasa yolu artık eski yolun KANITINI koşar (`_kasa_kaniti`); botlar etkin
    DEĞİLKEN o kanıt Task 2 davranışıyla "KANIT: ölçülemedi — … etkin değil" der ve çıkış 0'dır (eskiden "değer-doğruluğu
    ÖLÇÜLMEDİ (None)" satırıydı). Etkin botlarda kanıt C10b'de."""
    kasa_yolu = "secret/meridian/api_server_key"
    kok, ortam, log, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI["api"]})
    r = _kos(BETIK, ortam, "--api-sunucu", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    degerler = _api_degerleri(kok)
    _iddia(len(set(degerler)) == 1 and degerler[0] != ESKI["api"], "beş kopya AYNI yeni değeri taşımıyor")
    _iddia(bool(re.fullmatch(r"[0-9a-f]{64}", degerler[0] or "")), "yeni değer 64 küçük hex değil")
    _iddia(v521._kv_put_yollari(log) == [kasa_yolu], f"kasa put yolları: {v521._kv_put_yollari(log)}")
    _iddia(_systemctl_log(kok) == [], f"etkin olmayan birim yeniden başlatıldı: {_systemctl_log(kok)}")
    for b in (BOTLAR, TELEGRAM):
        _iddia(f"ATLANDI (etkin değil: inactive): {b}" in r.stdout, f"{b} ATLANDI yok\n{_ozet(r)}")
    _iddia(KANIT_YOK in r.stdout and "ÖLÇÜLMEDİ (None)" not in r.stdout, _ozet(r))
    ih = _kasa_sizintisi(r, kok, log, degerler[0])
    _iddia(not ih, "\n".join(ih))


def _alan_yaz(kok: pathlib.Path, yol: str, alan: str, deger: str) -> None:
    p = _p(kok, yol)
    satirlar = p.read_text(encoding="utf-8").splitlines(True)
    _iddia(sum(s.startswith(alan + "=") for s in satirlar) == 1, f"{yol}: {alan} tam bir kez değil")
    p.write_text("".join(f"{alan}={deger}\n" if s.startswith(alan + "=") else s for s in satirlar), encoding="utf-8")


BOZUK_KOPYA = "SAHTE-BOZUK-KOPYA-0001"


@pytest.mark.parametrize("alt,sir,alan,profil", [
    ("api-sunucu", API_SIR, API_SIR, "karne"),
    ("tenant", TENANT_SIR, SOHBET_TENANT_ALANI, "sef"),
    ("kapi-bot-karne", "BOT_KEY_KARNE", "BOT_KEY_KARNE", "karne"),
], ids=["api-sunucu", "tenant", "kapi-bot"])
def test_B16_envanter_AYRIYI_gorur_esitle_YALNIZ_ayrigi_yazar(tmp_path, alt, sir, alan, profil):
    """M5(c) — Review Focus 5'in son cümlesi KOŞAN bir çiviyle: bir sohbet kopyası bozulunca `--envanter` onu `→ AYRI` gösterir
    (öteki kopyalar EŞİT); `--<alt> --esitle` YALNIZ o dosyayı yazar (öteki her dosyanın sha256'sı aynı), restart YOK, değer
    referansa eşitlenir ve yeniden ölçümde EŞİT'tir. Tablo güdümlüdür: yeni satırlar (sohbet kopyaları, `kapi-bot-<ad>`)
    ayrıca kodlanmadan kapsanır."""
    kok, ortam = _sahte_ortam(tmp_path)
    hedef = _profil_env(profil)
    _alan_yaz(kok, hedef, alan, BOZUK_KOPYA)
    r = _kos(BETIK, ortam, "--envanter")
    _iddia(r.returncode == 0, _ozet(r))
    satirlar = [s for s in r.stdout.splitlines() if s.startswith(f"  {sir} · ")]
    _iddia(f"  {sir} · {hedef} [{alan}] → AYRI" in satirlar, f"bozulan kopya AYRI görünmüyor\n{_ozet(r)}")
    _iddia(sum(s.endswith("→ AYRI") for s in satirlar) == 1, f"AYRI satırı tam bir değil: {satirlar}")
    # İmza içerik + KİMLİK: yazım `_atomik_yaz` (mkstemp + `os.replace`) ile olur ve EŞİT bir kopyayı aynı değerle yeniden
    # yazmak içeriği değiştirmez ama dosyayı DEĞİŞTİRİR (yeni inode, yeni mtime) — "yalnız ayrığı yazar" sözleşmesi ancak
    # böyle ölçülür (ölçüldü: yalnız sha256 kıyası AYRI süzgecini kaldıran mutasyona KÖRDÜ — rapor M7).
    def imza() -> dict[str, tuple]:
        return {str(q.relative_to(kok)): (hashlib.sha256(q.read_bytes()).hexdigest(), q.stat().st_ino, q.stat().st_mtime_ns)
                for q in kok.rglob("*") if q.is_file() and ".sahte" not in q.parts}
    once = imza()
    r2 = _kos(BETIK, ortam, *alt_argv(alt), "--esitle")
    _iddia(r2.returncode == 0, _ozet(r2))
    sonra = imza()
    degisen = sorted(k for k in set(once) | set(sonra) if once.get(k) != sonra.get(k) and not k.startswith("root/"))
    _iddia(degisen == [hedef.lstrip("/")], f"eşitleme YALNIZ ayrığı yazmadı: {degisen}")
    _iddia(_systemctl_log(kok) == [], f"eşitleme yeniden başlattı: {_systemctl_log(kok)}")
    ref = next(x for x in _betik_kopyalari() if x["sir"] == sir)
    ref_deger = (_dosya_degeri(kok, ref["yol"]) if ref["tur"] == "dosya" else _alan(kok, ref["yol"], ref["alan"]))
    _iddia(_alan(kok, hedef, alan) == ref_deger and ref_deger != BOZUK_KOPYA, "kopya referansa eşitlenmedi")
    _iddia(BOZUK_KOPYA not in r.stdout + r.stderr + r2.stdout + r2.stderr and ref_deger not in r2.stdout + r2.stderr,
           "bir değer çıktıya düştü")
    r3 = _kos(BETIK, ortam, "--envanter")
    _iddia(f"  {sir} · {hedef} [{alan}] → EŞİT" in r3.stdout.splitlines(), _ozet(r3))


# =================================================================================================
# BÖLÜM C (G3b Task 3, 2026-10-01) — `--kapi-bot <ad>`: BİR BOTUN KAPI ANAHTARI TÜM KOPYALARIYLA BİRLİKTE DÖNER
# =================================================================================================
# Operatör kararı K-G3b-1 (2026-09-30): kapı tüketicisi (`.env-apisix` `BOT_KEY_<AD>` — `$env://` açılışta çözülür,
# RESTART), rapor profili (`~/.hermes/profiles/<ad>/.env`) ve sohbet profili (`~/.hermes-botlar/profiles/<ad>/.env`) AYNI
# turda yazılır; REFERANS Agent'ın render hedefidir (`/etc/meridian/bot_key_<ad>`, Rol-1 G3b-R3). İç alt ad
# `kapi-bot-<ad>` (G3b-R2): tablo güdümlü makine (`_birimler` · `_alt_sirlari` · `_yedek_al` · `_kuru_rapor` ·
# `_envanter_esitlik`) süzgeçsiz doğru çalışır. Bot listesi kabukta TEK sabittir (`_SOHBET_BOTLARI`).

APISIX_ENV = "/opt/apisix/.env-apisix"
RAPOR_PROFIL_KOKU = "/home/ubuntu/.hermes/profiles"


def _bot_sir(ad: str) -> str:
    return f"BOT_KEY_{ad.upper()}"


def _bot_ref(ad: str) -> str:
    return f"/etc/meridian/bot_key_{ad}"


def _bot_kopyalari(ad: str) -> list[tuple[str, str]]:
    """`(tür, yol)` — tablodaki SIRA: referans render hedefi, kapı, rapor profili, sohbet profili (brief Task 3)."""
    return [("dosya", _bot_ref(ad)), ("env", APISIX_ENV), ("env", f"{RAPOR_PROFIL_KOKU}/{ad}/.env"),
            ("env", _profil_env(ad))]


def _bot_degerleri(kok: pathlib.Path, ad: str) -> list[str | None]:
    return [_dosya_degeri(kok, _bot_ref(ad))] + [_alan(kok, y, _bot_sir(ad)) for _, y in _bot_kopyalari(ad)[1:]]


def _diger_satirlar(kok: pathlib.Path, yol: str, alan: str) -> list[str]:
    return [s for s in _p(kok, yol).read_text(encoding="utf-8").splitlines() if not s.startswith(alan + "=")]


# --- C1 — yalnız kendi botunu döndürür ----------------------------------------------------------------

@pytest.mark.parametrize("kip", ["eski", "kasa"])
def test_C1_kapi_bot_yalniz_kendi_botunu_dondurur(tmp_path, kip):
    """`--kapi-bot bekci` (eski yol ve `--vault --uret`): `BOT_KEY_BEKCI`in DÖRT kopyası (render hedefi · `.env-apisix` ·
    rapor `.env` · sohbet `.env`) AYNI yeni değeri taşır (48 kr b64url, eskiden farklı). Öteki botların bütün kopyaları,
    `.env-apisix`in ve bekçi `.env`lerinin öteki satırları bayt-eşit; tablonun bekçi bloğu DIŞINDA hiçbir dosya değişmez.
    Değer hiçbir çıktıda/argv'de yok. Kapı yeniden başlar (`$env://` açılışta); botlar etkin değil → ATLANDI. Eski yolun
    kanıtı kapı `/models` (yeni → 200 · eski → 401); kasa yolunda `kv put` TEK yol."""
    ad, digerler = "bekci", [b for b in _sohbet_profilleri() if b != "bekci"]
    kasa_yolu = f"secret/meridian/bot_key_{ad}"
    if kip == "eski":
        kok, ortam = _sahte_ortam(tmp_path)
        log, args = None, ("--kapi-bot", ad)
    else:
        kok, ortam, log, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI["bot_bekci"]})
        args = ("--kapi-bot", ad, "--vault", "--uret")
    _iddia(set(_bot_degerleri(kok, ad)) == {ESKI["bot_bekci"]}, "tohum: dört kopya eşit değil (pozitif kontrol)")
    once = _imzalar(kok)
    komsu = {y: _diger_satirlar(kok, y, _bot_sir(ad)) for _, y in _bot_kopyalari(ad)[1:]}
    r = _kos(BETIK, ortam, *args)
    _iddia(r.returncode == 0, _ozet(r))
    degerler = _bot_degerleri(kok, ad)
    _iddia(len(set(degerler)) == 1 and degerler[0] != ESKI["bot_bekci"], "dört kopya AYNI yeni değeri taşımıyor")
    _iddia(bool(re.fullmatch(r"[A-Za-z0-9_-]{48}", degerler[0] or "")), "yeni değer 48 kr b64url değil (sınıf b64)")
    for b in digerler:
        _iddia(set(_bot_degerleri(kok, b)) == {ESKI[f"bot_{b}"]}, f"{b}: başka botun anahtarı DEĞİŞTİ")
    for y, satirlar in komsu.items():
        _iddia(_diger_satirlar(kok, y, _bot_sir(ad)) == satirlar, f"{y}: öteki satırlar DEĞİŞTİ")
    sonra = _imzalar(kok)
    izinli = {y.lstrip("/") for _, y in _bot_kopyalari(ad)} | ({"opt/apisix/.env-apisix.vault"} if kip == "kasa" else set())
    degisen = {k for k in set(once) | set(sonra) if once.get(k) != sonra.get(k) and not k.startswith("root/")}
    _iddia(degisen <= izinli, f"bekçi bloğu DIŞINDA dosya değişti: {sorted(degisen - izinli)}")
    ih = _deger_ciktida_yok(r, kok, degerler[0]) if log is None else _kasa_sizintisi(r, kok, log, degerler[0])
    _iddia(not ih, "\n".join(ih))
    _iddia(_systemctl_log(kok) == ["apisix.service"], f"restart: {_systemctl_log(kok)}")
    _iddia(f"ATLANDI (etkin değil: inactive): {BOTLAR}" in r.stdout, f"botlar ATLANDI yok\n{_ozet(r)}")
    if kip == "eski":
        _iddia(f"kapı /models (bot_{ad}): yeni→200 · eski→401" in r.stdout, f"kapı kanıtı yok\n{_ozet(r)}")
    else:
        _iddia(v521._kv_put_yollari(log) == [kasa_yolu], f"kasa put yolları: {v521._kv_put_yollari(log)}")


def test_C1b_kapi_bot_kaniti_ANAHTARA_BAGLI_degilse_cikis_2(tmp_path):
    """İki hüküm birden: kapı anahtara KÖR olursa (`SAHTE_KOR`) eski anahtar da 200 alır → `ÖLÇÜLEMEDİ`, çıkış 2."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_KOR"] = "1"
    r = _kos(BETIK, ortam, "--kapi-bot", "bekci")
    _iddia(r.returncode == 2 and "ÖLÇÜLEMEDİ" in r.stderr and "kapı /models (bot_bekci)" in r.stderr, _ozet(r))


def test_C1c_referans_YOKSA_hicbir_sey_yazilmaz(tmp_path):
    """Referans Agent render hedefidir (G3b-R3); yoksa ESKİ değer UYDURULMAZ — eski yol yedekten ÖNCE durur: yedek, değer
    üretimi, kopya yazımı ve restart YOK; ileti yolu ADIYLA söyler (`api_sunucu` B4d emsali)."""
    kok, ortam = _sahte_ortam(tmp_path)
    _p(kok, _bot_ref("bekci")).unlink()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--kapi-bot", "bekci")
    _iddia(r.returncode != 0 and _bot_ref("bekci") in r.stderr, _ozet(r))
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok), f"referanssız koşum YAZDI\n{_ozet(r)}")


# --- C2 — geçersiz ad: kasaya ve dosyaya dokunmadan ret -------------------------------------------------

GECERSIZ = [
    ("bos", ["--kapi-bot", "", "--vault"], "geçersiz bot adı"),
    ("meridian", ["--kapi-bot", "meridian", "--vault"], "geçersiz bot adı"),
    ("buyuk_harf", ["--kapi-bot", "BEKCI", "--vault"], "geçersiz bot adı"),
    ("yol", ["--kapi-bot", "bekci/../sef", "--vault"], "geçersiz bot adı"),
    ("bosluklu", ["--kapi-bot", "sef bekci", "--vault"], "geçersiz bot adı"),
    ("bilinmeyen", ["--kapi-bot", "yok", "--vault"], "geçersiz bot adı"),
    ("bayrak_ad", ["--kapi-bot", "--kuru", "--vault"], "geçersiz bot adı"),
    ("argumansiz", ["--kapi-bot"], "bot ADI ister"),
    ("ic_ad_bayrak", ["--kapi-bot-bekci"], "bilinmeyen argüman"),
    ("iki_bot", ["--kapi-bot", "bekci", "--kapi-bot", "sef"], "iki alt komut"),
]


@pytest.mark.parametrize("args,ileti", [(a, i) for _, a, i in GECERSIZ], ids=[k for k, _, _ in GECERSIZ])
def test_C2_gecersiz_bot_adi_hicbir_sey_yazmadan_reddedilir(tmp_path, args, ileti):
    """Ad TEK listeye (`_SOHBET_BOTLARI`) TAM eşitlikle sorulur — büyük harf, yol karakteri, boşluk, boş, bayrak gibi
    görünen ad ve bilinmeyen bot AYRIŞTIRMADA reddedilir: kasa şimi hiç çağrılmaz, `is-active`/restart yok, yedek yok,
    sahnedeki her dosyanın sha256'sı aynı. Ret ayrıştırma katmanındadır (ileti ADIYLA) — derindeki tablo kapıları
    (satırı olmayan alt komut) ikinci savunmadır, birinci değil."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, *args, girdi=GIRDI)
    ih = []
    if r.returncode == 0:
        ih.append("çıkış 0 — geçersiz ad KABUL edildi")
    if ileti not in r.stderr:
        ih.append(f"stderr ayrıştırma iletisini ({ileti!r}) taşımıyor")
    if kasa_log.exists():
        ih.append("kasa şimi ÇAĞRILDI")
    if _is_active_sorulari(kok) or _systemctl_log(kok):
        ih.append("systemctl'e soruldu / restart yapıldı")
    if _yedekler(kok) or _imzalar(kok) != once:
        ih.append("yedek alındı ya da dosya değişti")
    _iddia(not ih, f"{args}:\n" + "\n".join(ih) + "\n" + _ozet(r))


# --- C3 — bot listesi tek kaynak; tablo blokları ---------------------------------------------------------

def test_C3_bot_listesi_tek_kaynaktan_ve_tablo_bloklari():
    """Kabuktaki bot kümesi (`_SOHBET_BOTLARI`) = A0 `sohbet_profil_adlari` = `deploy/hermes/sohbet/profiles/*` dizinleri;
    `--kopyalar`ın `kapi-bot-*` alt komutları TAM bu kümedir ve her botun bloğu dört satırdır (referans render hedefi İLK,
    `.env-apisix`, rapor, sohbet — BİTİŞİK, alan `BOT_KEY_<AD>`). Kabukta `kapi-bot-<ad>` LİTERALİ yok (ikinci liste yok);
    başlığın KULLANIM satırındaki ad listesi (belge — kopya kaçınılmaz) bot listesiyle AYNI."""
    kabuk = _betik_sabiti("_SOHBET_BOTLARI")
    dizinler = sorted(p.name for p in (KOK_DEPO / "deploy/hermes/sohbet/profiles").iterdir() if p.is_dir())
    _iddia(set(kabuk) == set(_sohbet_profilleri()) == set(dizinler), f"{kabuk} · {_sohbet_profilleri()} · {dizinler}")
    _iddia(set(KAPI_BOT_ALTLARI) == {f"kapi-bot-{b}" for b in kabuk}, f"v447 KAPI_BOT_ALTLARI: {KAPI_BOT_ALTLARI}")
    k = _betik_kopyalari()
    _iddia({x["alt"] for x in k if x["alt"].startswith("kapi-bot-")} == {f"kapi-bot-{b}" for b in kabuk},
           f"tablonun kapi-bot alt komutları: {sorted({x['alt'] for x in k if x['alt'].startswith('kapi-bot-')})}")
    for b in kabuk:
        blok = [x for x in k if x["alt"] == f"kapi-bot-{b}"]
        _iddia([(x["tur"], x["yol"]) for x in blok] == _bot_kopyalari(b), f"{b} bloğu: {[(x['tur'], x['yol']) for x in blok]}")
        _iddia({x["sir"] for x in blok} == {_bot_sir(b)}, f"{b}: sır kimliği {sorted({x['sir'] for x in blok})}")
        _iddia(blok[0]["mod"] == "0400" and blok[0]["sahip"] == "root:root" and blok[0]["alan"] is None, f"{b}: {blok[0]}")
        _iddia(all(x["alan"] == _bot_sir(b) and x["mod"] == x["sahip"] == "koru" for x in blok[1:]), f"{b}: {blok[1:]}")
    metin = BETIK.read_text(encoding="utf-8")
    govde = "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))
    _iddia(not [b for b in kabuk if f"kapi-bot-{b}" in govde], "kabukta kapi-bot-<ad> LİTERALİ (ikinci liste)")
    m = re.findall(r"^#\s+sudo \./sir_rotasyon\.sh --kapi-bot <([^>]*)>", metin, re.M)
    _iddia(len(m) == 1 and m[0].split("|") == kabuk, f"KULLANIM satırının ad listesi: {m} ≠ {kabuk}")


# --- C4 — restart: kapı her zaman, botlar yalnız etkinse, motor ASLA ---------------------------------------

@pytest.mark.parametrize("etkin", [False, True], ids=["botlar_etkin_degil", "botlar_etkin"])
def test_C4_kapi_bot_apisix_restart_botlar_yalniz_etkinse(tmp_path, etkin):
    """`BOT_KEY_<AD>`in tüketicileri kapı (`$env://` AÇILIŞTA — reload yetmez, restart) ve bot ağ geçidi (profil `.env`i,
    açılışta). Motor bu anahtarı KULLANMAZ → `meridian.service` YENİDEN BAŞLAMAZ; Telegram dinleyicisine SORULMAZ bile.
    Botlar etkin değilse ATLANDI; etkinse kapıdan SONRA restart + `/health` hazırlığı (credential satırı YOK — denetim
    istenmez). Rapor botları timer'lı oneshot'tur, `.env`i her koşuda okur (restart yok)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    if etkin:
        _etkin_botlar(kok, BOTLAR)
    r = _kos(BETIK, ortam, "--kapi-bot", "karne")
    _iddia(r.returncode == 0, _ozet(r))
    log = _systemctl_log(kok)
    _iddia("apisix.service" in log and "meridian.service" not in log, f"restart: {log}")
    _iddia(set(_is_active_sorulari(kok)) == {BOTLAR}, f"is-active: {_is_active_sorulari(kok)}")
    if etkin:
        _iddia(log == ["apisix.service", BOTLAR], f"restart sırası: {log}")
        _iddia("hazır: meridian-botlar" in r.stdout and "ATLANDI" not in r.stdout, _ozet(r))
        _iddia(f"/run/credentials/{BOTLAR}/" not in r.stdout + r.stderr, "botlar için credential denetimi İSTENDİ")
    else:
        _iddia(log == ["apisix.service"], f"restart: {log}")
        _iddia(f"ATLANDI (etkin değil: inactive): {BOTLAR}" in r.stdout, _ozet(r))
        _iddia(not [u for u in _url_log(kok) if u.startswith(BOTLAR_KOK)], "etkin olmayan botlar YOKLANDI")


# --- C5 — envanter bağı tabloyla birebir ------------------------------------------------------------------

def test_C5_BOT_KEY_baglari_tabloyla_birebir():
    """Envanter `bot_key_<ad>`: `rotasyon_siri: BOT_KEY_<AD>` (kasaya BAĞLI — `--kapi-bot <ad> --vault`), `kaynak` = REFERANS
    render hedefi (G3b-R3, emsal `hindsight_cp_access_key`), `{kaynak} ∪ kopya_kaynaklari` = tablonun o sırra ait satırları
    (v491 A5'in genel kuralı — bu çivi ona işaret eden POZİTİF KONTROLdür: bot girdileri A5'in atladığı dalga-1/bağsız
    kollara DÜŞMÜYOR). Tüketici beyanı rotasyon komutunu adıyla taşır ve LoadCredential DEMEZ (v485 F2)."""
    veri = yaml.safe_load(ENVANTER_YOLU.read_text(encoding="utf-8"))
    kv = {g["ad"]: g for g in veri["vault_kv"]}
    tablo = _betik_kopyalari()
    tur_esleme = {"env": "env_satiri", "dosya": "dosya"}
    for b in _sohbet_profilleri():
        g = kv.get(f"bot_key_{b}")
        _iddia(g is not None, f"vault_kv.bot_key_{b} yok")
        _iddia(g.get("rotasyon_siri") == _bot_sir(b) and "ayni_deger" not in g and "kaynak" in g,
               f"bot_key_{b}: A5'in BİREBİR kolunda değil: rotasyon_siri={g.get('rotasyon_siri')!r}")
        _iddia(g["kaynak"] == {"tur": "dosya", "dosya": _bot_ref(b), "alan": None, "onek": None}, f"kaynak: {g['kaynak']}")
        _iddia(g["hedef"] == _bot_ref(b), f"hedef: {g['hedef']}")
        beklenen = {(tur_esleme[x["tur"]], x["yol"], x["alan"], x["onek"]) for x in tablo if x["sir"] == _bot_sir(b)}
        gercek = {(k["tur"], k["dosya"], k["alan"], k["onek"]) for k in [g["kaynak"], *(g.get("kopya_kaynaklari") or [])]}
        _iddia(gercek == beklenen and len(beklenen) == 4, f"bot_key_{b}: {sorted(gercek ^ beklenen)}")
        _iddia(f"--kapi-bot {b}" in g["tuketici"] and "LoadCredential" not in g["tuketici"]
               and "vault_dosyalar" in g["tuketici"], f"bot_key_{b} tüketici: {g['tuketici']!r}")


# --- C6 — kuru plan: operatöre giden her komut GERÇEK bayrakla --------------------------------------------

@pytest.mark.parametrize("kip", ["eski", "kasa"])
def test_C6_kuru_plan_dort_kopya_ve_komutlar_GERCEK_bayrakla(tmp_path, kip):
    """`--kapi-bot <ad> --kuru` (ve `--vault --kuru`): dört kopya planda, kapı restart + botlar "YALNIZ ETKİNSE" notu, hiçbir
    şey yazılmaz. İç alt ad komut satırına SIZMAZ: `--kapi-bot-<ad>` diye bir bayrak yoktur (C2) ve operatöre basılan her
    komut `--kapi-bot <ad>` biçimindedir (eski yol uyarısının `--vault` önerisi dahil)."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    ek = ("--vault",) if kip == "kasa" else ()
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--kapi-bot", "sef", *ek, "--kuru")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(f"KURU KOŞUM: --kapi-bot sef" in r.stdout, f"kuru başlığı\n{_ozet(r)}")
    for _, y in _bot_kopyalari("sef"):
        _iddia(y in r.stdout, f"planda yok: {y}\n{_ozet(r)}")
    _iddia(f"    · {BOTLAR} — şu an: inactive → ATLANACAK" in r.stdout.splitlines(), _ozet(r))
    _iddia(not re.search(r"--kapi-bot-", r.stdout + r.stderr), "iç alt ad komut satırı biçiminde basıldı")
    if kip == "eski":
        _iddia(f"sudo {BETIK} --kapi-bot sef --vault" in r.stdout, f"eski yol uyarısı kasa yolunu göstermiyor\n{_ozet(r)}")
        _iddia("/llm/v1/models (apikey, tüketici bot_sef)" in r.stdout, f"kanıt planı yok\n{_ozet(r)}")
    else:
        _iddia("kasaya yazılacak : secret/meridian/bot_key_sef" in r.stdout, _ozet(r))
        _iddia(f"eski yol (sudo {BETIK} --kapi-bot sef)" in r.stdout, f"değer kaynağı beyanı bayrağı\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok) and not kasa_log.exists(),
           "kuru koşum YAZDI / kasaya dokundu")


# --- C7 — ön-denetim bot başı alt komutu da kapsar ---------------------------------------------------------

@pytest.mark.parametrize("kip", ["eski", "kasa"])
def test_C7_sohbet_env_YOKKEN_kapi_bot_HIC_yazmaz_ama_ozge_bot_KOSAR(tmp_path, kip):
    """A1 bugün: sohbet `.env`leri YOK (tohumlama Task 4). `--kapi-bot bekci` HİÇBİR yazım yapmadan durur (yolu ADIYLA);
    ön-denetimin alt komut süzgeci başka botu durdurmaz — karnenin `.env`i yerindeyse `--kapi-bot karne` KOŞAR."""
    if kip == "eski":
        kok, ortam = _sahte_ortam(tmp_path)
        kasa_log, ek = None, ()
    else:
        kok, ortam, kasa_log, _ = _kasa_dunyasi(tmp_path, {"secret/meridian/bot_key_bekci": ESKI["bot_bekci"],
                                                           "secret/meridian/bot_key_karne": ESKI["bot_karne"]})
        ek = ("--vault", "--uret")
    _eksik_hedefi_sil(kok)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--kapi-bot", "bekci", *ek)
    _iddia(r.returncode != 0 and f"hedef dosya YOK: {EKSIK_YOL}" in r.stderr and TOHUMLA in r.stderr, _ozet(r))
    _iddia(not _yedekler(kok) and _imzalar(kok) == once and not _systemctl_log(kok), f"YAZDI\n{_ozet(r)}")
    if kasa_log is not None:
        _iddia(not v521._kv_put_yollari(kasa_log), "kasaya put YAPILDI")
    r2 = _kos(BETIK, ortam, "--kapi-bot", "karne", *ek)
    _iddia(r2.returncode == 0, f"başka botun eksik hedefi karneyi durdurdu\n{_ozet(r2)}")


# --- C8 — envanter sahnede bot anahtarlarını EŞİT görür, beyan dışı bağırmaz ---------------------------------

def test_C8_envanter_bot_anahtarlari_ESIT_beyan_disi_YOK(tmp_path):
    """`BOT_KEY_<AD>` artık bir sır KİMLİĞİDİR (`_aranan_adlar` birinci kaynağı) → `.env-apisix` · rapor · sohbet `.env`lerinde
    duran her `BOT_KEY_*` satırı ya tabloda ya BEYAN DIŞI'dır. Sahne (canlının varacağı dünya): her botun dört kopyası EŞİT,
    beyan dışı kopya YOK (yalnız spec Bulgu-2'nin pano jetonu kopyaları — v447 I3)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    _iddia(r.returncode == 0, _ozet(r))
    for b in _sohbet_profilleri():
        satirlar = [s for s in r.stdout.splitlines() if s.startswith(f"  {_bot_sir(b)} · ")]
        _iddia(len(satirlar) == 4 and satirlar[0].endswith("→ VAR (referans kopya)")
               and all(s.endswith("→ EŞİT") for s in satirlar[1:]), f"{b}: {satirlar}")
    beyan_disi = [s for s in r.stdout.splitlines() if "BEYAN DIŞI" in s and "BOT_KEY_" in s]
    _iddia(not beyan_disi, "bot anahtarı BEYAN DIŞI:\n" + "\n".join(beyan_disi))


# --- C9 — üretecin bot başı alt komut ailesi (M6) -----------------------------------------------------------

def test_C9_URETEC_kapi_bot_ailesi_YENI_BOTTA_dort_satir_uretir(tmp_path):
    """Task 2 incelemesi M6: üreteç "aile = bütün botlar" varsayımını `kapi-bot-<ad>` (aile başına TEK bot, alt komut başına
    dört satır) için genişletir. Yeni bot → `--kontrol` BAYAT; `--uygula` (kopya envanter) yeni botun `kapi-bot-<ad>`
    bloğunu SIRAYLA (tür · yol · alan) yazar; ikinci `--kontrol` 0. Kasa girdisi (`vault_kv.bot_key_<ad>`) sır başına elle
    yazılır (plan Global Constraints) — üreteç onu UYDURMAZ.
    KAPSAM BEYANI (Task 3 incelemesi M5, 2026-10-01): tüketici metni için bu çivi YALNIZ `{ad}` yer tutucusunun dolduğunu
    ölçer (`yenibot` metinde, `{ad}` hiçbir metinde yok). HANGİ şablonun hangi satıra gittiğini ÖLÇMEZ — dört şablonun
    hepsi `{ad}` taşır, yani tüketicileri satırlar arasında KARIŞTIRAN bir üreteç burada yeşil kalır (ölçüldü: inceleme
    N11). O karışımı B12 yakalar (`--kontrol` güncel envanteri bayt bayt kıyaslar)."""
    betik = _yeni_botlu_betik(tmp_path)
    env = tmp_path / "envanter.yaml"
    env.write_text(ENVANTER_YOLU.read_text(encoding="utf-8"), encoding="utf-8")
    r = _uretec("--uygula", betik=betik, envanter=env)
    _iddia(r.returncode == 0, f"{r.stdout}\n{r.stderr}")
    _iddia(_uretec("--kontrol", betik=betik, envanter=env).returncode == 0, "uygula sonrası bayat")
    veri = yaml.safe_load(env.read_text(encoding="utf-8"))
    blok = [k for k in veri["rotasyon_kopyalari"]["kopyalar"] if k["alt_komut"] == "kapi-bot-yenibot"]
    beklenen = [("dosya", "/etc/meridian/bot_key_yenibot", None), ("env", APISIX_ENV, "BOT_KEY_YENIBOT"),
                ("env", f"{RAPOR_PROFIL_KOKU}/yenibot/.env", "BOT_KEY_YENIBOT"),
                ("env", f"{_sohbet_koku()}/profiles/yenibot/.env", "BOT_KEY_YENIBOT")]
    _iddia([(k["tur"], k["yol"], k["alan"]) for k in blok] == beklenen, f"yenibot bloğu: {blok}")
    _iddia(all(k["sir"] == "BOT_KEY_YENIBOT" for k in blok) and "yenibot" in blok[2]["tuketici"]
           and "{ad}" not in "".join(k["tuketici"] for k in blok), f"tüketici şablonu: {[k['tuketici'] for k in blok]}")
    _iddia("bot_key_yenibot" not in {g["ad"] for g in veri["vault_kv"]}, "üreteç kasa girdisi UYDURDU")


@pytest.mark.parametrize("bozma", ["satir", "bolge", "sablon"])
def test_C9b_URETEC_kapi_bot_bolgesi_bozulursa_kontrol_OTER(tmp_path, bozma):
    """`--kontrol` ısırır: (satır) üretilmiş bir `kapi-bot-*` satırı elle değişirse BAYAT (1); (bölge) aile işaretçisi
    kaldırılırsa ayna dışında kalan aile SÖZLEŞME hatası (1); (şablon) bir yolun tüketici şablonu silinirse o satır
    üretilemez — SÖZLEŞME hatası (1). Üçünde de envanter YAZILMAZ."""
    ham = ENVANTER_YOLU.read_text(encoding="utf-8")
    if bozma == "satir":
        capa = '      yol: "/opt/apisix/.env-apisix"\n      alan: BOT_KEY_SEF\n'
        _iddia(ham.count(capa) == 1, "çapa tek değil")
        bozuk = ham.replace(capa, '      yol: "/opt/apisix/.env-apisix"\n      alan: BOT_KEY_YANLIS\n')
    elif bozma == "bolge":
        bas = ham.index("# >>> ÜRETİLDİ alt_ailesi kapi-bot-{ad}")
        son = ham.index("# <<< ÜRETİLDİ", bas) + len("# <<< ÜRETİLDİ")
        bozuk = ham[:bas] + "# (bölge kaldırıldı)" + ham[son:]
    else:
        satirlar = [s for s in ham.splitlines(True) if s.lstrip().startswith("# şablon /home/ubuntu/.hermes/profiles/")]
        _iddia(len(satirlar) == 1, f"şablon satırı tek değil: {satirlar}")
        bozuk = ham.replace(satirlar[0], "", 1)
    env = tmp_path / "envanter.yaml"
    env.write_text(bozuk, encoding="utf-8")
    r = _uretec("--kontrol", envanter=env)
    _iddia(r.returncode == 1, f"bozulan bölge yakalanmadı ({bozma}): {r.returncode}\n{r.stdout}\n{r.stderr}")
    _iddia(env.read_text(encoding="utf-8") == bozuk, "--kontrol envanteri YAZDI")


# =================================================================================================
# C10/C11 — Task 3 incelemesinden taşınanlar (G3b Task 4 turu, 2026-10-01)
# =================================================================================================
# C10 (Rol-1 0. madde ← Task 3 incelemesi M1): kasa yolunda (`--kapi-bot <ad> --vault`, aynı sınıf `--kapi --vault` ·
# `--api-sunucu --vault`) tüketici kanıtı YOKTU — `vault_rotasyon` "değer-doğruluğu ÖLÇÜLMEDİ (None)" basıp geçiyordu. Kapı
# değeri docker'ın İKİNCİ `--env-file`ından (`.env-apisix.vault`, Agent yazar) alır ve aynı anahtarda o KAZANIR: yan dosya
# render'ı gecikirse kapı ESKİ anahtarla açılır, bot 401 alır ve hiçbir satır bunu söylemezdi. Artık (1) restart'tan ÖNCE
# kasa yolunu taşıyan her yan dosya alanı kasadaki yeni değere BİREBİR ölçülür (sınırlı bekleme; gelmezse ÖLÇÜLEMEDİ, eski
# kanal YAZILMAZ, restart YOK) ve (2) restart'tan sonra eski yolun kanıtı (`_farksal`: yeni 200 · eski 401) koşar — ESKİ
# değer yazım ÖNCESİ KASADAN okunan yedektir.

#: `alt → (argv, kasa yolu, ESKI tohum anahtarı, yan dosya alanı, kanıt satırı)`.
KASA_KANITLI = {
    "kapi-bot": (("--kapi-bot", "bekci"), "secret/meridian/bot_key_bekci", "bot_bekci", "BOT_KEY_BEKCI",
                 "kapı /models (bot_bekci): yeni→200 · eski→401"),
    "kapi": (("--kapi",), "secret/meridian/kapi_apikey", "kapi", "BOT_KEY_MERIDIAN",
             "kapı /models: yeni→200 · eski→401"),
}
APISIX_YAN = "/opt/apisix/.env-apisix.vault"


def _dosya_ref(alt: str) -> str:
    """Alt komutun kanonik render hedefi (tablonun İLK satırı) — `KASA_KANITLI` argv'sinden."""
    ic = "kapi-bot-" + KASA_KANITLI[alt][0][1] if alt == "kapi-bot" else alt
    return next(x["yol"] for x in _betik_kopyalari() if x["alt"] == ic)


def _apisix_yan_tohumu(kok: pathlib.Path) -> None:
    """A1 gerçeği: kapının yan dosyası (`.env-apisix.vault`, dalga-2'den beri) VARDIR ve Agent'ın ÖNCEKİ render'ının — yani
    ESKİ — değerlerini taşır. (v556 dünyası onu kurmaz; yoksa şimin kapısı yalnız `.env-apisix`i okur ve gecikmiş yan
    dosya hiçbir şeyi değiştirmezdi — ilk mutasyon turunda ÖLÇÜLDÜ: bekleme kaldırılınca C10b[kapi-bot] çıkış 0 verdi.)"""
    p = _p(kok, APISIX_YAN)
    p.write_text("".join(f"BOT_KEY_{b.upper()}={ESKI[f'bot_{b}']}\n" for b in ("bekci", "karne", "sef"))
                 + f"BOT_KEY_MERIDIAN={ESKI['kapi']}\n", encoding="utf-8")
    p.chmod(0o400)


def _yan_render_kapat(tmp_path: pathlib.Path) -> None:
    """Sahte Agent kanonik hedefi render eder ama YAN DOSYALARI ETMEZ — A1'de aynı render turunda yan dosyanın geride
    kalmasının modeli (yan dosya ESKİ değerde kalır — `_apisix_yan_tohumu`). v556 kasa şiminin yan dosya döngüsü BU
    koşumun kopyasında boşaltılır (v556 değişmez)."""
    sim = tmp_path / "bin_v556" / "vault"
    metin = sim.read_text(encoding="utf-8")
    capa = "for dosya, alan, onek in YAN.get(yol, []):"
    _iddia(metin.count(capa) == 1, "kasa şiminin yan dosya döngüsü TEK değil — sahne kurulamaz")
    sim.write_text(metin.replace(capa, "for dosya, alan, onek in []:"), encoding="utf-8")


@pytest.mark.parametrize("alt", sorted(KASA_KANITLI))
def test_C10_kasa_yolu_YAN_DOSYA_renderini_restarttan_ONCE_olcer_ve_KANIT_kosar(tmp_path, alt):
    """Doğru yol (`--vault --uret`): yan dosya alanı (`.env-apisix.vault [<alan>]`) kasadaki yeni değere BİREBİR ölçülür,
    SONRA kapı yeniden başlar, SONRA eski yolun kanıtı koşar (kapı `/models` yeni → 200 · eski → 401; `--kapi`de ayrıca motor
    `/api/secrets/test/nous` ok:true). "ÖLÇÜLMEDİ (None)" satırı YOK."""
    args, kasa_yolu, tohum, alan, kanit = KASA_KANITLI[alt]
    kok, ortam, log, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI[tohum]})
    _apisix_yan_tohumu(kok)
    r = _kos(BETIK, ortam, *args, "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(_alan(kok, APISIX_YAN, alan) == _dosya_degeri(kok, _dosya_ref(alt)), "yan dosya alanı yeni değere render edilmedi")
    olcum = f"yan dosya render ÖLÇÜLDÜ: {APISIX_YAN} [{alan}]"
    _iddia(olcum in r.stdout and kanit in r.stdout and "ÖLÇÜLMEDİ (None)" not in r.stdout, _ozet(r))
    i_olcum, i_restart, i_kanit = (r.stdout.index(olcum), r.stdout.index("yeniden başlat: apisix.service"),
                                   r.stdout.index(kanit))
    _iddia(i_olcum < i_restart < i_kanit, f"sıra: yan dosya {i_olcum} · restart {i_restart} · kanıt {i_kanit}")
    if alt == "kapi":
        _iddia("motor içi kanıt: /api/secrets/test/nous ok:true" in r.stdout, f"motor kanıtı yok\n{_ozet(r)}")
    _iddia(v521._kv_put_yollari(log) == [kasa_yolu], f"kasa put yolları: {v521._kv_put_yollari(log)}")


@pytest.mark.parametrize("alt", sorted(KASA_KANITLI))
def test_C10b_YAN_DOSYA_render_GELMEZSE_restart_YOK_eski_kanal_YOK_cikis_2(tmp_path, alt):
    """Agent kanonik hedefi render etti, yan dosyayı ETMEDİ (aynı turda gecikme): ÖLÇÜLEMEDİ (çıkış 2), yan dosya alanı
    ADIYLA; HİÇBİR birim yeniden BAŞLATILMAZ (kapı eski anahtarla açılmaz), eski kanal (`.env-apisix` …) YAZILMAZ; kasa
    YENİ değerde olduğu için geri alma reçetesi kasa geri alımını basar. Bekleme kaldırılırsa kapı restart edilir — kırmızı."""
    args, kasa_yolu, tohum, alan, kanit = KASA_KANITLI[alt]
    kok, ortam, _, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI[tohum]})
    _apisix_yan_tohumu(kok)
    _yan_render_kapat(tmp_path)
    eski_satir = _alan(kok, APISIX_ENV, alan)
    r = _kos(BETIK, ortam, *args, "--vault", "--uret")
    _iddia(r.returncode == 2 and "ÖLÇÜLEMEDİ" in r.stderr and "yan dosya render bekleme aşıldı" in r.stderr
           and f"{APISIX_YAN} [{alan}]" in r.stderr, _ozet(r))
    _iddia(_systemctl_log(kok) == [], f"yan dosya ESKİYKEN birim yeniden başlatıldı: {_systemctl_log(kok)}")
    _iddia(_alan(kok, APISIX_ENV, alan) == eski_satir, "eski kanal (.env-apisix) yan dosya ölçülmeden YAZILDI")
    _iddia(kanit not in r.stdout and "vault kv rollback" in r.stderr, f"kanıt koştu / kasa geri alımı yok\n{_ozet(r)}")


def test_C10c_KASA_kaniti_ANAHTARA_BAGLI_degilse_cikis_2(tmp_path):
    """İki hüküm birden kasa yolunda da: kapı anahtara KÖR (`SAHTE_KOR`) → eski değer de 200 → ÖLÇÜLEMEDİ, çıkış 2."""
    args, kasa_yolu, tohum, _, _ = KASA_KANITLI["kapi-bot"]
    kok, ortam, _, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI[tohum]})
    _apisix_yan_tohumu(kok)
    ortam["SAHTE_KOR"] = "1"
    r = _kos(BETIK, ortam, *args, "--vault", "--uret")
    _iddia(r.returncode == 2 and "ÖLÇÜLEMEDİ" in r.stderr and "kapı /models (bot_bekci)" in r.stderr, _ozet(r))


def test_C10d_api_sunucu_KASA_yolu_botlar_ETKINSE_health_detailed_kaniti(tmp_path):
    """`--api-sunucu --vault --uret`, botlar ETKİN: kasa yolunun yan dosyası YOK (Hermes `.env.vault` okumaz — satır bunu
    söyler), restart botlar, kanıt `/health/detailed` yeni → 200 · eski → 401 (eski = yazım ÖNCESİ kasa değeri). Etkin
    DEĞİLKEN "ölçülemedi — birim etkin değil" (çıkış 0) B15'te."""
    kasa_yolu = "secret/meridian/api_server_key"
    kok, ortam, _, _ = _kasa_dunyasi(tmp_path, {kasa_yolu: ESKI["api"]})
    ortam["SIR_ROT_BOTLAR"] = BOTLAR_KOK
    _etkin_botlar(kok, BOTLAR)
    r = _kos(BETIK, ortam, "--api-sunucu", "--vault", "--uret")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(f"yan dosya YOK ({kasa_yolu})" in r.stdout, f"yan dosya beyanı yok\n{_ozet(r)}")
    _iddia("botlar /health/detailed: yeni→200 · eski→401" in r.stdout and "KANIT: ölçülemedi" not in r.stdout, _ozet(r))
    _iddia(BOTLAR in _systemctl_log(kok), f"restart: {_systemctl_log(kok)}")


@pytest.mark.parametrize("alt,args,beklenen", [
    ("kapi-bot", ("--kapi-bot", "sef"), (f"    · {APISIX_YAN} [BOT_KEY_SEF]", "/llm/v1/models (apikey, tüketici bot_sef)")),
    ("kapi", ("--kapi",), (f"    · {APISIX_YAN} [BOT_KEY_MERIDIAN]", "kanıt: GET http://kapi/llm/v1/models (apikey)")),
    ("api-sunucu", ("--api-sunucu",), ("    · yan dosya YOK", "/health/detailed (Bearer)")),
])
def test_C10e_KASA_KURU_plani_yan_dosya_olcumunu_ve_KANITI_soyler(tmp_path, alt, args, beklenen):
    """Bedel yasası: gerçek koşumun restart'tan ÖNCE ölçeceği yan dosya alanları ve restart SONRASI kanıtı kuru planda
    görünür; kuru koşum hiçbir şey yazmaz, kasaya dokunmaz."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, *args, "--vault", "--kuru")
    _iddia(r.returncode == 0 and "yan dosya render kanıtı" in r.stdout, _ozet(r))
    for b in beklenen:
        _iddia(b in r.stdout, f"planda yok: {b!r}\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once and not _yedekler(kok) and not _systemctl_log(kok) and not kasa_log.exists(),
           "kuru koşum YAZDI / kasaya dokundu")


def test_C11_sir_birimleri_BOT_KEY_MERIDIAN_bot_globuyla_ESLESMEZ(tmp_path):
    """Task 3 incelemesi M4: `BOT_KEY_*` kolu bot sayısından bağımsızlık için globdur, ama `BOT_KEY_MERIDIAN` bir bot anahtarı
    DEĞİL motorun kapı anahtarıdır (`KAPI_APIKEY`ın takma adı; tüketici kapı + MOTOR) ve `--kapi` onu `KAPI_APIKEY` adıyla
    döndürür. Glob onu eşleseydi bir gün `rotasyon_siri: BOT_KEY_MERIDIAN` yazıldığında motor SESSİZCE yeniden başlamazdı.
    Açık dışlama: harita YOK (çağıran "tüketici birim haritası YOK" ile durur — fail-closed); her bot anahtarı kapı + bot ağ
    geçidi; motorun gerçek adı (`KAPI_APIKEY`) motoru taşır."""
    kok, ortam = _sahte_ortam(tmp_path)
    sirlar = ["BOT_KEY_MERIDIAN", "KAPI_APIKEY"] + [_bot_sir(b) for b in _sohbet_profilleri()]
    cagri = ('for s in ' + " ".join(sirlar) + '; do printf "%s=" "$s"; _sir_birimleri "$s" || echo "HARITA-YOK"; done')
    r = _kos(_surucu(tmp_path, cagri), ortam)
    _iddia(r.returncode == 0 and "SURUCU-SONU" in r.stdout, _ozet(r))
    satirlar = dict(s.split("=", 1) for s in r.stdout.splitlines() if "=" in s)
    _iddia(satirlar.get("BOT_KEY_MERIDIAN") == "HARITA-YOK", f"BOT_KEY_MERIDIAN: {satirlar.get('BOT_KEY_MERIDIAN')!r}")
    _iddia("meridian.service" in satirlar.get("KAPI_APIKEY", "").split(), f"KAPI_APIKEY: {satirlar.get('KAPI_APIKEY')!r}")
    for b in _sohbet_profilleri():
        _iddia(satirlar.get(_bot_sir(b)) == "apisix.service meridian-botlar.service", f"{b}: {satirlar.get(_bot_sir(b))!r}")


# =================================================================================================
# A16c — ön-denetimin ÖLÇÜLEMEDİ hâli (Task 3 incelemesi M2)
# =================================================================================================

@pytest.mark.parametrize("kip", ["eski", "vault"])
@pytest.mark.parametrize("bozma", ["utf8", "izin"])
def test_A16c_on_denetim_OLCULEMEDI_hali_cikis_2_traceback_YOK(tmp_path, kip, bozma):
    """Hedef VAR ama alanı ÖLÇÜLEMİYOR (UTF-8 dışı bayt · okuma izni yok): eskiden UTF-8 dışı dosya python traceback'i + çıkış
    1 veriyordu ve izin hâli "alan TAM BİR satır değil … elle düzelt" diyordu (dosya okunamazken yanıltıcı). Artık: yol ve
    alan ADIYLA "ÖLÇÜLEMEDİ", çıkış 2 (ölçemedim ≠ arıza), traceback yok, sayım iletisi yok; HİÇBİR yazım yok."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    y = kok / EKSIK_YOL.lstrip("/")
    if bozma == "utf8":
        y.write_bytes(b"\xff\xfeBOZUK\n" + y.read_bytes())
    once = _imzalar(kok)
    if bozma == "izin":
        y.chmod(0o000)
    ek = ("--vault",) if kip == "vault" else ()
    try:
        r = _kos(BETIK, ortam, "--tenant", *ek, girdi=GIRDI)
    finally:
        y.chmod(0o600)
    ih = []
    if r.returncode != 2:
        ih.append(f"çıkış {r.returncode} (2 bekleniyordu — ölçemedim ≠ arıza)")
    if "ÖLÇÜLEMEDİ" not in r.stderr or EKSIK_YOL not in r.stderr or EKSIK_ALAN not in r.stderr:
        ih.append("stderr ÖLÇÜLEMEDİ + yol + alan ADIYLA söylemiyor")
    if "Traceback" in r.stderr:
        ih.append("python traceback'i basıldı")
    if "TAM BİR satır" in r.stderr:
        ih.append("ölçülemeyen hâl sayım hatası diye raporlandı")
    if _yedekler(kok) or _imzalar(kok) != once or _systemctl_log(kok):
        ih.append("yedek / dosya değişimi / restart")
    if kasa_log.exists() and v521._kv_put_yollari(kasa_log):
        ih.append("kasaya `kv put` YAPILDI")
    _iddia(not ih, f"--tenant {' '.join(ek)} [{bozma}]:\n" + "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# BÖLÜM D (G3b Task 4, 2026-10-01) — `--tohumla-sohbet`: TABLODAN TÜREYEN, DEĞERSİZ, İDEMPOTENT İLK YAZIM
# =================================================================================================
# Operatör kararı K-G3b-2 ("araç oluştursun"): sohbet `.env` YOKSA oluşturur, VARSA dokunmaz; değer ekrana, argv'ye, log'a
# düşmez. Beklenen küme bu dosyada da TABLODAN (`--kopyalar`) ve A0 kök dizininden türer — kabuğun kümesine bakılmaz.

def _tohum_plani() -> tuple[dict[str, dict[str, str]], dict[str, dict]]:
    """`({hedef yol: {alan: sır}}, {sır: referans satırı})` — `_SOHBET_KOKU` (A0 `sohbet_kok_dizini`) altına yazan `env`
    satırları; referans = sırrın tablodaki İLK satırı (REFERANS KURALI)."""
    k = _betik_kopyalari()
    ref: dict[str, dict] = {}
    for x in k:
        ref.setdefault(x["sir"], x)
    plan: dict[str, dict[str, str]] = {}
    for x in k:
        if x["tur"] == "env" and x["yol"].startswith(_sohbet_koku() + "/"):
            plan.setdefault(x["yol"], {})[x["alan"]] = x["sir"]
    _iddia(len(plan) == 1 + len(_sohbet_profilleri()), f"tohum planı kök + profiller değil: {sorted(plan)}")
    return plan, ref


def _ref_degeri(kok: pathlib.Path, satir: dict) -> str:
    if satir["tur"] == "dosya":
        return _dosya_degeri(kok, satir["yol"])
    return _alan(kok, satir["yol"], satir["alan"]) or ""


def _env_sozlugu(p: pathlib.Path) -> dict[str, str]:
    satirlar = p.read_text(encoding="utf-8").splitlines()
    _iddia(all("=" in s for s in satirlar), f"{p.name}: KEY=değer olmayan satır")
    return dict(s.split("=", 1) for s in satirlar)


def _tohum_sil(kok: pathlib.Path, *yollar: str) -> None:
    for y in yollar:
        _p(kok, y).unlink()
        _iddia(not _p(kok, y).exists(), f"silinemedi: {y}")


def _dosya_imzasi(p: pathlib.Path) -> tuple:
    st = p.stat()
    return hashlib.sha256(p.read_bytes()).hexdigest(), st.st_mtime_ns, st.st_ino, st.st_mode & 0o7777


def _sahiplik_kaydi(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Sahiplik ÖLÇÜMÜ (çivi makinesinde `ubuntu` YOK — yardımcının işaretli emsali chown'u atlar): yardımcı sürecine
    `sitecustomize` ile `pwd/grp` `ubuntu` → 1000/1001 ve kayıt tutan `os.chown`/`os.fchown` verilir. Kayıttaki (uid, gid)
    YALNIZ yardımcı `ubuntu:ubuntu` istediyse 1000/1001 olur — istenen sahip böyle ölçülür, çivi makinesinde hiçbir şey chown
    edilmez. G3b dal sonu M1: yazım artık DOSYA TANITICISINA `fchown` yapar (yol tabanlı chown bir bağı izlerdi) — tanıtıcının
    yolu `F_GETPATH` (macOS) ya da `/proc/self/fd` (Linux) ile okunur."""
    site = tmp_path / "site_v604"
    site.mkdir()
    log = tmp_path / "chown.log"
    (site / "sitecustomize.py").write_text(
        "import grp, os, pwd\n"
        "_LOG = os.environ.get('SAHTE_CHOWN_LOG')\n"
        "if _LOG:\n"
        "    _p, _g = pwd.getpwnam, grp.getgrnam\n"
        "    class _K:\n        pw_uid = 1000\n"
        "    class _G:\n        gr_gid = 1001\n"
        "    pwd.getpwnam = lambda ad: _K() if ad == 'ubuntu' else _p(ad)\n"
        "    grp.getgrnam = lambda ad: _G() if ad == 'ubuntu' else _g(ad)\n"
        "    def _chown(yol, uid, gid, *a, **k):\n"
        "        with open(_LOG, 'a', encoding='utf-8') as fh:\n"
        "            fh.write('%s\\t%s\\t%s\\n' % (os.path.dirname(os.fspath(yol)), uid, gid))\n"
        "    os.chown = _chown\n"
        "    def _fd_yolu(fd):\n"
        "        try:\n"
        "            import fcntl\n"
        "            return fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024)).split(bytes(1), 1)[0].decode()\n"
        "        except (ImportError, AttributeError, OSError):\n"
        "            return os.readlink('/proc/self/fd/%d' % fd)\n"
        "    def _fchown(fd, uid, gid):\n"
        "        with open(_LOG, 'a', encoding='utf-8') as fh:\n"
        "            fh.write('%s\\t%s\\t%s\\n' % (os.path.dirname(_fd_yolu(fd)), uid, gid))\n"
        "    os.fchown = _fchown\n", encoding="utf-8")
    return site, log


def _tohum_degerleri(kok: pathlib.Path) -> set[str]:
    plan, ref = _tohum_plani()
    return {_ref_degeri(kok, ref[s]) for alanlar in plan.values() for s in alanlar.values()}


def test_D1_yok_olan_dosyalar_0600_ubuntu_ile_yazilir(tmp_path):
    """Dört sohbet `.env`i YOK, referanslar VAR: dördü de oluşur — mod 0600, istenen sahip `ubuntu:ubuntu` (chown kaydı),
    alan kümesi tablodan türeyen küme ile BİREBİR (fazla satır yok), her değer sırrının referansına EŞİT. Restart YOK,
    yedek YOK; özet `yazıldı 4 · dokunulmadı 0 · eksik alanlı 0`."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, ref = _tohum_plani()
    _tohum_sil(kok, *plan)
    site, chown_log = _sahiplik_kaydi(tmp_path)
    ortam.update(PYTHONPATH=os.pathsep.join(x for x in (str(site), ortam.get("PYTHONPATH", "")) if x),
                 SAHTE_CHOWN_LOG=str(chown_log))
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode == 0, _ozet(r))
    for yol, alanlar in plan.items():
        p = _p(kok, yol)
        _iddia(p.is_file() and (p.stat().st_mode & 0o777) == 0o600, f"{yol}: yok ya da mod 0600 değil")
        icerik = _env_sozlugu(p)
        _iddia(set(icerik) == set(alanlar), f"{yol}: alanlar {sorted(icerik)} ≠ tablo {sorted(alanlar)}")
        for alan, sir in alanlar.items():
            _iddia(icerik[alan] == _ref_degeri(kok, ref[sir]) and icerik[alan], f"{yol} [{alan}]: referansa eşit değil")
    kayit = sorted(chown_log.read_text(encoding="utf-8").splitlines()) if chown_log.exists() else []
    beklenen = sorted(f"{_p(kok, y).parent}\t1000\t1001" for y in plan)
    _iddia(kayit == beklenen, f"chown kaydı (ubuntu:ubuntu = 1000/1001):\n{kayit}\n≠\n{beklenen}")
    _iddia("yazıldı 4 · dokunulmadı 0 · eksik alanlı 0" in r.stdout, _ozet(r))
    _iddia(not _systemctl_log(kok) and not _is_active_sorulari(kok) and not _yedekler(kok), "restart / is-active / yedek")


def test_D2_var_olan_dosyaya_dokunulmaz(tmp_path):
    """Bir dosya önceden VAR, alanları tam ama içeriği FARKLI (fazla satır + referanstan ayrı değer) ve modu 0640: sha256,
    mtime_ns, inode ve mod AYNI kalır; satır `dokunulmadı` der; öteki üç YOK dosya yazılır, çıkış 0."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    var_olan = _profil_env("karne")
    _tohum_sil(kok, *[y for y in plan if y != var_olan])
    _alan_yaz(kok, var_olan, API_SIR, "SAHTE-FARKLI-D2-0001")
    p = _p(kok, var_olan)
    p.write_text(p.read_text(encoding="utf-8") + "SAHTE_EK=farkli\n", encoding="utf-8")
    p.chmod(0o640)
    once = _dosya_imzasi(p)
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(_dosya_imzasi(p) == once, "VAR olan dosya DEĞİŞTİ (sha256 · mtime · inode · mod)")
    _iddia(f"{var_olan} → VAR (alanlar tam) — dokunulmadı" in r.stdout, _ozet(r))
    _iddia("yazıldı 3 · dokunulmadı 1 · eksik alanlı 0" in r.stdout, _ozet(r))
    _iddia(all(_p(kok, y).is_file() for y in plan), "YOK olan dosyalar yazılmadı")


def test_D3_var_olan_dosyada_eksik_alan_raporlanir_yazilmaz(tmp_path):
    """VAR olan dosyada bir alan EKSİK: dosya BAYT-EŞİT kalır, alan ADIYLA (yol ile) söylenir, çıkış 3 (operatör reçetesi
    elle inceleme ister). YOK olan öteki dosyalar yine yazılır — eksik alanlı dosya onları rehin almaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    var_olan = _profil_env("bekci")
    _tohum_sil(kok, *[y for y in plan if y != var_olan])
    p = _p(kok, var_olan)
    p.write_text("".join(s for s in p.read_text(encoding="utf-8").splitlines(True)
                         if not s.startswith(SOHBET_TENANT_ALANI + "=")), encoding="utf-8")
    once = _dosya_imzasi(p)
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode == 3, f"çıkış {r.returncode} (3 bekleniyordu)\n{_ozet(r)}")
    _iddia(f"{var_olan} → VAR (eksik: {SOHBET_TENANT_ALANI})" in r.stdout, _ozet(r))
    _iddia(_dosya_imzasi(p) == once, "eksik alanlı dosya DEĞİŞTİ")
    _iddia("yazıldı 3 · dokunulmadı 1 · eksik alanlı 1" in r.stdout, _ozet(r))
    _iddia(all(_p(kok, y).is_file() for y in plan), "YOK olan dosyalar yazılmadı")


KARNE_REF = "/etc/meridian/bot_key_karne"


@pytest.mark.parametrize("ref,icerik,ileti", [
    (API_REF, None, "referans YOK: {ref}"),
    (KARNE_REF, None, "referans YOK: {ref}"),
    (KARNE_REF, "", "referans BOŞ: {ref}"),
    (KARNE_REF, "   \n", "referans TEK satırlık dolu bir değer değil: {ref}"),
    (KARNE_REF, "SAHTE-SATIR-1\nSAHTE-SATIR-2\n", "referans TEK satırlık dolu bir değer değil: {ref}"),
], ids=["api_server_key_yok", "tek_hedefin_referansi_yok", "bos", "yalniz_bosluk", "cok_satirli"])
def test_D4_referans_yoksa_hicbir_dosya_yazilmaz(tmp_path, ref, icerik, ileti):
    """Bir referans (Agent render hedefi) YOK, BOŞ, yalnız boşluk ya da ÇOK SATIRLI (Agent boş/bozuk render edebilir — RUNBOOK
    adım 2'nin uyarısı; dal sonu M5): hiçbir sohbet `.env`i oluşmaz — o referansa İHTİYACI OLMAYAN hedefler de; çıkış ≠ 0,
    ileti yolu ve hâli ADIYLA söyler, değer basılmaz. `api_server_key` dünyası brief'inkidir (dört hedefin HEPSİ ister);
    `bot_key_karne` YALNIZ karne profilinin referansıdır: denetim yazımdan SONRAYA (hedef başına, tembel) kayarsa sef/bekçi
    dosyaları karneden ÖNCE yazılırdı (brief M2 mutasyonunun ısırdığı yer). İki kapı katmanı ayrı ölçülür: `py var` (YOK/BOŞ)
    ve tek-satır+dolu kapısı (boşluk/çok satır) — biri gevşerse kendi parametresi kırmızı."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    if icerik is None:
        _p(kok, ref).unlink()
    else:
        _p(kok, ref).write_text(icerik, encoding="utf-8")
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode != 0 and ileti.format(ref=ref) in r.stderr, _ozet(r))
    _iddia("SAHTE-SATIR" not in r.stdout + r.stderr, "referans değeri çıktıya düştü")
    _iddia(not [y for y in plan if _p(kok, y).exists()], "referans yokken sohbet .env YAZILDI")
    _iddia(_imzalar(kok) == once and not _yedekler(kok), "dosya değişti / yedek alındı")


def test_D5_dizin_yoksa_durur(tmp_path):
    """Bir profil dizini YOK (A0 site.yml koşmamış): HİÇBİR dosya yazılmaz, araç dizin AÇMAZ (root sahipli dizin hermes
    evinde yanlış olurdu — A0'ın işi); ileti dizini ve A0'ı ADIYLA söyler."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    dizin = str(pathlib.PurePosixPath(_profil_env("karne")).parent)
    shutil.rmtree(_p(kok, dizin))
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode != 0 and f"dizin YOK: {dizin}" in r.stderr and "site.yml" in r.stderr, _ozet(r))
    _iddia(not _p(kok, dizin).exists(), "araç dizin AÇTI")
    _iddia(not [y for y in plan if _p(kok, y).exists()], "dizin yokken sohbet .env YAZILDI")


def test_D6_ikinci_kosum_hicbir_sey_yazmaz(tmp_path):
    """İdempotent: ilk koşum dördünü yazar; ikinci koşum hiçbirine dokunmaz (sha256 · mtime_ns · inode · mod aynı),
    özet `yazıldı 0 · dokunulmadı 4 · eksik alanlı 0`, çıkış 0."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    r1 = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r1.returncode == 0, _ozet(r1))
    once = {y: _dosya_imzasi(_p(kok, y)) for y in plan}
    r2 = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r2.returncode == 0 and "yazıldı 0 · dokunulmadı 4 · eksik alanlı 0" in r2.stdout, _ozet(r2))
    _iddia({y: _dosya_imzasi(_p(kok, y)) for y in plan} == once, "ikinci koşum YAZDI")


def test_D7_deger_hicbir_ciktida_yok(tmp_path):
    """Referans değerleri (dolayısıyla yazılan değerler) stdout, stderr, şim argv günlüğü (`sudo …` çağrıları — yardımcının
    argümanları dahil), url ve systemctl günlüklerinde YOK: değer yalnız 0600 işlik dosyasından akar."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    degerler = _tohum_degerleri(kok)
    _iddia(len(degerler) == 2 + len(_sohbet_profilleri()) and all(degerler), f"tohum değerleri: {len(degerler)}")
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode == 0, _ozet(r))
    metinler = {"stdout": r.stdout, "stderr": r.stderr}
    for ad in ("argv.log", "url.log", "systemctl.log"):
        metinler[ad] = (kok / ".sahte" / ad).read_text(encoding="utf-8")
    _iddia("tohumla-env" in metinler["argv.log"], "yardımcı çağrısı argv günlüğünde yok (pozitif kontrol)")
    sizan = sorted(ad for ad, m in metinler.items() for d in degerler if d in m)
    _iddia(not sizan, f"değer düştü: {sizan}")


@pytest.mark.parametrize("dunya", ["karma", "eksik"])
def test_D8_kuru_sifir_yazim(tmp_path, dunya):
    """`--kuru`: hedef başına `YOK — yazılacak alanlar: …` / `VAR (alanlar tam)` / `VAR (eksik: …)`, referans ve dizin başına
    VAR/YOK; sıfır yazım (dosya, dizin, yedek), çıkış 0. Eksik dünyada (referans + dizin yok) plan gerçek koşumun
    DURACAĞINI söyler — kuru koşum bir durum uydurmaz ve durmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    kok_env, bekci, karne, sef = _kok_env(), _profil_env("bekci"), _profil_env("karne"), _profil_env("sef")
    if dunya == "karma":
        _tohum_sil(kok, kok_env, sef)
        p = _p(kok, bekci)
        p.write_text("".join(s for s in p.read_text(encoding="utf-8").splitlines(True)
                             if not s.startswith(SOHBET_TENANT_ALANI + "=")), encoding="utf-8")
    else:
        _tohum_sil(kok, *plan)
        _p(kok, API_REF).unlink()
        shutil.rmtree(_p(kok, str(pathlib.PurePosixPath(karne).parent)))
    once = _imzalar(kok)
    dizinler = sorted(str(q.relative_to(kok)) for q in kok.rglob("*") if q.is_dir())
    r = _kos(BETIK, ortam, TOHUMLA, "--kuru")
    _iddia(r.returncode == 0 and "KURU KOŞUM" in r.stdout, _ozet(r))
    s = r.stdout
    if dunya == "karma":
        _iddia(f"{kok_env} → YOK — yazılacak alanlar: {API_SIR}" in s, _ozet(r))
        _iddia(f"{bekci} → VAR (eksik: {SOHBET_TENANT_ALANI})" in s and f"{karne} → VAR (alanlar tam)" in s, _ozet(r))
        _iddia(f"referans: {API_SIR} · {API_REF} → VAR" in s, _ozet(r))
        _iddia("plan: yazılacak 2 · dokunulmayacak 2 · eksik alanlı 1" in s and "GERÇEK KOŞUM DURUR" not in s, _ozet(r))
    else:
        _iddia(f"referans: {API_SIR} · {API_REF} → YOK" in s, _ozet(r))
        _iddia(f"dizin: {pathlib.PurePosixPath(karne).parent} → YOK" in s and "GERÇEK KOŞUM DURUR" in s, _ozet(r))
    _iddia(_imzalar(kok) == once and not _yedekler(kok), "kuru koşum dosya YAZDI")
    _iddia(sorted(str(q.relative_to(kok)) for q in kok.rglob("*") if q.is_dir()) == dizinler, "kuru koşum dizin AÇTI")


def test_D9_alan_kumesi_tablodan_turetilir(tmp_path):
    """İkinci liste YOK: tabloya (worktree DIŞI betik kopyası) sahte bir sohbet satırı eklenince tohumlama o alanı da,
    sırrın REFERANSINDAN okunan değerle yazar. Sabit bir alan listesi bu satırı görmezdi."""
    capa = "cp HINDSIGHT_CP_ACCESS_KEY dosya /etc/meridian/hindsight_cp_access_key - 0400 root:root -\n"
    ek = f"cp HINDSIGHT_CP_ACCESS_KEY env {_profil_env('sef')} D9_SAHTE_ALAN koru koru -\n"
    m = _mutant(tmp_path, (capa, capa + ek), ad="d9_ek_satir.sh")
    _iddia(any(x["alan"] == "D9_SAHTE_ALAN" for x in _betik_kopyalari(m)), "kopya tablosu ek satırı taşımıyor")
    kok, ortam = _sahte_ortam(tmp_path)
    _p(kok, "/etc/meridian/hindsight_cp_access_key").write_text("SAHTE-CP-D9-0001\n", encoding="utf-8")
    _tohum_sil(kok, _profil_env("sef"))
    r = _kos(m, ortam, TOHUMLA)
    _iddia(r.returncode == 0 and "yazıldı 1 · dokunulmadı 3 · eksik alanlı 0" in r.stdout, _ozet(r))
    icerik = _env_sozlugu(_p(kok, _profil_env("sef")))
    _iddia(icerik.get("D9_SAHTE_ALAN") == "SAHTE-CP-D9-0001", f"ek alan yazılmadı: {sorted(icerik)}")
    _iddia({API_SIR, SOHBET_TENANT_ALANI, _bot_sir("sef")} <= set(icerik), f"tablonun öteki alanları: {sorted(icerik)}")


def _yardimci_kos(yardimci: pathlib.Path, op: str, *args: str, on: str = "") -> subprocess.CompletedProcess:
    """Gömülü yardımcıyı DOĞRUDAN koşar; `on` yardımcıdan ÖNCE çalışan yama kodudur (yarış / root / bağ hâli modeli)."""
    kod = (on + "import runpy, sys\n"
           f"sys.argv = {[str(yardimci), op, *args]!r}\n"
           f"runpy.run_path({str(yardimci)!r}, run_name='__main__')\n")
    return subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True)


def test_D10_tohumla_env_yardimcisi_var_olan_hedefi_reddeder(tmp_path):
    """İkinci savunma — yardımcı DOĞRUDAN (imza `<kök> <hedef> <mod> <sahip> <grup> (<alan> <değer>)+`, dal sonu M1): (a) hedef
    yoksa `ALAN=değer` 0600 yazar ve doğrulama hükmünü basar; (b) hedef VARSA reddeder, dosya bayt, inode ve mtime olarak aynı;
    (c) YARIŞ: ön denetim (`lexists`) "yok" dese de dosya arada doğmuşsa `os.link` reddeder — `os.replace` olsaydı EZERDİ;
    (d) tek sayıda alan/değer argümanı reddedilir, dosya oluşmaz. Geçici dosya kalmaz."""
    yardimci = _yardimci(tmp_path)
    dizin = tmp_path / "hedef"
    dizin.mkdir()
    hedef = dizin / ".env"
    dgr = tmp_path / "deger"
    dgr.write_text("SAHTE-D10-0001\n", encoding="utf-8")
    dgr2 = tmp_path / "deger2"
    dgr2.write_text("SAHTE-D10-0002\n", encoding="utf-8")
    ortak = (str(dizin),)

    r = _yardimci_kos(yardimci, "tohumla-env", *ortak, str(hedef), "0600", "ubuntu", "ubuntu", "ALAN", str(dgr))
    _iddia(r.returncode == 0 and hedef.read_text(encoding="utf-8") == "ALAN=SAHTE-D10-0001\n"
           and (hedef.stat().st_mode & 0o777) == 0o600 and "DOĞRULANDI" in r.stdout, f"(a) {r.returncode} {r.stderr}")
    once = _dosya_imzasi(hedef)
    r = _yardimci_kos(yardimci, "tohumla-env", *ortak, str(hedef), "0600", "ubuntu", "ubuntu", "ALAN", str(dgr2))
    _iddia(r.returncode != 0 and "VAR" in r.stderr and _dosya_imzasi(hedef) == once, f"(b) {r.returncode} {r.stderr}")
    r = _yardimci_kos(yardimci, "tohumla-env", *ortak, str(hedef), "0600", "ubuntu", "ubuntu", "ALAN", str(dgr2),
                      on="import os\nos.path.lexists = lambda p: False\n")
    _iddia(r.returncode != 0 and _dosya_imzasi(hedef) == once, f"(c) yarışta EZİLDİ ya da kabul edildi: {r.returncode}")
    yeni = dizin / ".env-d"
    r = _yardimci_kos(yardimci, "tohumla-env", *ortak, str(yeni), "0600", "ubuntu", "ubuntu", "ALAN", str(dgr), "TEK")
    _iddia(r.returncode != 0 and not yeni.exists(), f"(d) {r.returncode} {r.stderr}")
    _iddia(sorted(q.name for q in dizin.iterdir()) == [".env"], f"geçici dosya kaldı: {sorted(q.name for q in dizin.iterdir())}")
    _iddia("SAHTE-D10" not in r.stderr, "değer stderr'e düştü")


#: root dalının modeli — `os.geteuid` 0 ve `ubuntu` adı verilen uid/gid'e çözülür (yardımcı `pwd`/`grp`ı içeride ithal eder).
def _root_yamasi(uid: int, gid: int) -> str:
    return ("import os, pwd, grp\nos.geteuid = lambda: 0\n"
            f"class _K:\n    pw_uid = {uid}\nclass _G:\n    gr_gid = {gid}\n"
            "_p, _g = pwd.getpwnam, grp.getgrnam\n"
            "pwd.getpwnam = lambda a: _K() if a == 'ubuntu' else _p(a)\n"
            "grp.getgrnam = lambda a: _G() if a == 'ubuntu' else _g(a)\n")


#: Yazım SONRASI ölçümün modeli — `os.link` hedefe YAZILAN dosyayı değil başka bir inode'u bağlar (yarışta değişen ad).
_LINK_YEMI = ("import os\n_l = os.link\n"
              "def _sahte(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):\n"
              "    os.close(os.open('yem', os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=dst_dir_fd))\n"
              "    return _l('yem', dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd, follow_symlinks=follow_symlinks)\n"
              "os.link = _sahte\n")


@pytest.mark.parametrize("hal", ["bag_ebeveyn", "bag_kok", "kok_disi", "grup_yazar", "root_sahip_yanlis",
                                 "root_sahip_dogru", "yazim_dogrulamasi"])
def test_D10b_tohumla_env_DIZIN_BAGINI_izlemez_ve_YAZIMI_olcer(tmp_path, hal):
    """Dal sonu M1 (CWE-59) — yardımcı katmanı (kabuğun dizin kapısı geçilmiş/yarışılmış olsa bile): zincir kökten aşağı bağ
    İZLENMEDEN açılır. Ret: ebeveyn ya da kök SEMBOLİK BAĞ (bağın hedef dizininde `.env` DOĞMAZ) · hedef kökün DIŞINDA · bileşen
    grup/diğer YAZILABİLİR · root iken bileşen sahibi `ubuntu` değil · yazılan inode ölçümde tutmuyor (DOĞRULANAMADI). Kabul:
    root iken doğru sahip → hüküm sahibi ölçülmüş basar. Hiçbir hâlde değer çıktıya düşmez, geçici dosya kalmaz."""
    yardimci = _yardimci(tmp_path)
    kok = tmp_path / "kok_d"
    (kok / "profil").mkdir(parents=True)
    disari = tmp_path / "disari"
    disari.mkdir()
    dgr = tmp_path / "deger"
    dgr.write_text("SAHTE-D10B-0001\n", encoding="utf-8")
    hedef_kok, hedef, on, beklenen = kok, kok / "profil" / ".env", "", "RED"
    if hal == "bag_ebeveyn":
        shutil.rmtree(kok / "profil")
        (kok / "profil").symlink_to(disari, target_is_directory=True)
        beklenen = "SEMBOLİK BAĞ"
    elif hal == "bag_kok":
        bag = tmp_path / "kok_bag"
        bag.symlink_to(kok, target_is_directory=True)
        hedef_kok, hedef, beklenen = bag, bag / "profil" / ".env", "SEMBOLİK BAĞ"
    elif hal == "kok_disi":
        hedef, beklenen = disari / ".env", "DIŞINDA"
    elif hal == "grup_yazar":
        (kok / "profil").chmod(0o777)
        beklenen = "YAZABİLİR"
    elif hal == "root_sahip_yanlis":
        on, beklenen = _root_yamasi(os.getuid() + 4242, os.getgid()), "sahibi uid"
    elif hal == "root_sahip_dogru":
        on, beklenen = _root_yamasi(os.getuid(), os.getgid()), ""
    else:
        on, beklenen = _LINK_YEMI, "DOĞRULANAMADI"
    r = _yardimci_kos(yardimci, "tohumla-env", str(hedef_kok), str(hedef), "0600", "ubuntu", "ubuntu", "ALAN", str(dgr), on=on)
    if hal == "root_sahip_dogru":
        _iddia(r.returncode == 0 and f"DOĞRULANDI: normal dosya, 0600, sahip {os.getuid()}:{os.getgid()}" in r.stdout
               and hedef.read_text(encoding="utf-8") == "ALAN=SAHTE-D10B-0001\n", f"{r.returncode}\n{r.stdout}\n{r.stderr}")
    else:
        _iddia(r.returncode != 0 and beklenen in r.stderr, f"{hal}: {r.returncode}\n{r.stderr}")
        if hal != "yazim_dogrulamasi":
            _iddia(not hedef.exists() and not (disari / ".env").exists(), f"{hal}: dosya YAZILDI")
    kalan = [q for d in (kok, kok / "profil", disari) if d.is_dir() for q in d.iterdir() if q.name.startswith(".sir-rot-")]
    _iddia(not kalan and "SAHTE-D10B" not in r.stdout + r.stderr, f"geçici dosya kaldı / değer düştü: {kalan}")


@pytest.mark.parametrize("deger", ["", "   ", '""'], ids=["degersiz", "yalniz_bosluk", "bos_tirnak"])
def test_D3b_var_olan_dosyada_BOS_alan_eksik_sayilir(tmp_path, deger):
    """Dal sonu M2: VAR olan dosyada alan TAM 1 satır ama DEĞERSİZ (`ALAN=`, yalnız boşluk, `""`) — eskiden "VAR (alanlar tam)",
    `eksik alanlı 0`, çıkış 0 diyordu ve ilk işaret G3c'de 401 olurdu. Artık "boş: ALAN" (eksik sayılır), çıkış 3, dosya
    BAYT-EŞİT, elle reçete (`--esitle` değeri referanstan yazar) stderr'de. Ön-denetim (rotasyon) değersiz satırı yer tutucu sayar
    — A16b DEĞİŞMEDİ."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    var_olan = _profil_env("bekci")
    _tohum_sil(kok, *[y for y in plan if y != var_olan])
    _alan_yaz(kok, var_olan, API_SIR, deger)
    p = _p(kok, var_olan)
    once = _dosya_imzasi(p)
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode == 3, f"çıkış {r.returncode} (3 bekleniyordu)\n{_ozet(r)}")
    _iddia(f"{var_olan} → VAR (boş: {API_SIR})" in r.stdout and "alanlar tam" not in r.stdout.split(var_olan, 1)[1].splitlines()[0],
           _ozet(r))
    _iddia(f"'{API_SIR}=' satırı DEĞERSİZ" in r.stderr and "--api-sunucu --esitle" in r.stderr, _ozet(r))
    _iddia(_dosya_imzasi(p) == once and "yazıldı 3 · dokunulmadı 1 · eksik alanlı 1" in r.stdout, _ozet(r))


def _profili_baga_cevir(kok: pathlib.Path, ad: str) -> pathlib.Path:
    """`profiles/<ad>` → kök DIŞINDA gerçek bir dizine SEMBOLİK BAĞ (dal sonu sondası P1'in sahnesi). Döner: bağın hedefi."""
    dizin = _p(kok, str(pathlib.PurePosixPath(_profil_env(ad)).parent))
    disari = kok / "opt" / f"disari_{ad}"
    disari.mkdir(parents=True)
    shutil.rmtree(dizin)
    dizin.symlink_to(disari, target_is_directory=True)
    return disari


@pytest.mark.parametrize("hal", ["profil_bag", "kok_bag", "ara_dizin_grup_yazar"])
def test_D12_DIZIN_sembolik_bag_ya_da_gevsek_izin_HICBIR_sey_yazilmaz(tmp_path, hal):
    """Dal sonu M1 (CWE-59), uçtan uca: (profil_bag) `profiles/karne` başka bir dizine bağ — sonda P1 eskiden çıkış 0 verip
    `.env`i bağın hedefine yazıyordu; (kok_bag) `.hermes-botlar`ın kendisi bağ; (ara_dizin_grup_yazar) `profiles/` 0777 (zincirin
    ARA bileşeni). Hepsinde: çıkış ≠ 0, dizin ADIYLA "REDDEDİLDİ", HİÇBİR sohbet `.env`i yazılmaz (bağdan bağımsız hedefler de —
    kapı bütün dizinler için yazımdan ÖNCE), bağın hedef dizininde `.env` DOĞMAZ. Kuru koşum aynı hükmü basar, durmaz, yazmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    koku = _sohbet_koku()
    if hal == "profil_bag":
        disari, reddedilen = _profili_baga_cevir(kok, "karne"), str(pathlib.PurePosixPath(_profil_env("karne")).parent)
        neden = "SEMBOLİK BAĞ"
    elif hal == "kok_bag":
        disari = kok / "opt" / "hb_gercek"
        _p(kok, koku).rename(disari)
        _p(kok, koku).symlink_to(disari, target_is_directory=True)
        reddedilen, neden = koku, "SEMBOLİK BAĞ"
    else:
        disari = None
        _p(kok, f"{koku}/profiles").chmod(0o777)
        reddedilen, neden = _profil_env("sef").rsplit("/", 1)[0], "YAZABİLİR"
    once = _imzalar(kok)
    rk = _kos(BETIK, ortam, TOHUMLA, "--kuru")
    _iddia(rk.returncode == 0 and f"dizin: {reddedilen} → REDDEDİLDİ" in rk.stdout and "GERÇEK KOŞUM DURUR" in rk.stdout,
           _ozet(rk))
    r = _kos(BETIK, ortam, TOHUMLA)
    _iddia(r.returncode != 0 and f"dizin REDDEDİLDİ: {reddedilen}" in r.stderr and neden in r.stderr, _ozet(r))
    _iddia(not [y for y in plan if os.path.lexists(_p(kok, y))], "sohbet .env YAZILDI")
    if disari is not None:
        _iddia(not list(disari.rglob(".env")), "bağın hedef dizininde .env DOĞDU")
    _iddia(_imzalar(kok) == once and not _yedekler(kok), "dosya değişti / yedek alındı")


@pytest.mark.parametrize("hal", ["sarkik", "hedefli"])
def test_D13_HEDEF_sembolik_bag_okunmaz_SEBEP_adiyla_cikis_2(tmp_path, hal):
    """Dal sonu M4: hedef `.env` bir SEMBOLİK BAĞ (sarkık ya da bir dosyaya) — içerik okunmaz (bağ izlenmez), bağa dokunulmaz;
    son çıkış-2 iletisi gerçek sebebi hedef başına söyler ("SEMBOLİK BAĞ (sarkık …" / "(izlenmez …"), eski genel cümle ("izin
    ya da UTF-8") YOK. Öteki YOK hedefler yazılır (rehin alınmaz)."""
    kok, ortam = _sahte_ortam(tmp_path)
    plan, _ = _tohum_plani()
    bagli = _profil_env("sef")
    _tohum_sil(kok, *plan)
    hedef = kok / "opt" / "bag_hedefi.env"
    if hal == "hedefli":
        hedef.write_text("SAHTE_ICERIK=dokunulmaz\n", encoding="utf-8")
        once = _dosya_imzasi(hedef)
    _p(kok, bagli).symlink_to(hedef)
    r = _kos(BETIK, ortam, TOHUMLA)
    beklenen = "SEMBOLİK BAĞ (sarkık" if hal == "sarkik" else "SEMBOLİK BAĞ (izlenmez"
    _iddia(r.returncode == 2 and f"{bagli}: {beklenen}" in r.stderr and "izin ya da UTF-8" not in r.stderr, _ozet(r))
    _iddia(_p(kok, bagli).is_symlink() and os.readlink(_p(kok, bagli)) == str(hedef), "bağa DOKUNULDU")
    if hal == "hedefli":
        _iddia(_dosya_imzasi(hedef) == once, "bağın hedefi DEĞİŞTİ")
    else:
        _iddia(not hedef.exists(), "sarkık bağın hedefi YARATILDI")
    _iddia("yazıldı 3 · dokunulmadı 1 · eksik alanlı 0" in r.stdout, _ozet(r))


SOHBET_MANIFEST_KOKU = KOK_DEPO / "deploy/hermes/sohbet"


def _manifest_sir_adlari(yol: pathlib.Path) -> tuple[set[str], set[str]]:
    """`(default'suz adlar, default'lu adlar)` — `env_requires`ın SIR sınıfı varsayılansız girdilerdir (değer profil `.env`inden
    gelmek ZORUNDA); varsayılanlı girdiler (`HERMES_WRITE_SAFE_ROOT` gibi) sır değil ayardır ve tohumlanmaz."""
    m = yaml.safe_load(yol.read_text(encoding="utf-8"))
    girdiler = m.get("env_requires") or []
    adlar = [g["name"] for g in girdiler]
    _iddia(len(adlar) == len(set(adlar)), f"{yol}: env_requires'ta çift ad: {adlar}")
    return {g["name"] for g in girdiler if "default" not in g}, {g["name"] for g in girdiler if "default" in g}


def test_D14_TOHUM_alan_kumesi_ile_PROFIL_MANIFESTI_env_requires_IKI_YONLU_ESIT():
    """Dal sonu M6 — iki liste, tek gerçek: tohumlamanın bir sohbet `.env`ine yazdığı alan kümesi KOPYA TABLOSUNDAN türer
    (`--kopyalar` → `_tohum_plani`), Hermes'in o profilde zorunlu tuttuğu sırlar ise üretilmiş `distribution.yaml`ın
    `env_requires`ındadır (`ops/sohbet_profili_uret.py`). İkisi ayrışırsa ya tohumlama Hermes'in istediği bir sırrı YAZMAZ (bot
    açılışta düşer / 401) ya da Hermes'in bilmediği bir sırrı profile koyar (okuyucusuz kopya). İki yön: (1) manifestli profil
    kümesi == tablonun sohbet profili hedefleri; (2) her profilde tablo alanları == `env_requires`ın VARSAYILANSIZ adları;
    (3) varsayılanlı adlar (ayar) tabloda YOK. Kök `.env` (`_SOHBET_KOKU/.env`) için manifest varsa aynı kural; bugün YOK
    (yalnız profillerin manifesti üretilir) ve bu satır o durumu da ölçer."""
    plan, _ = _tohum_plani()
    koku = _sohbet_koku()
    profil_hedefleri = {pathlib.PurePosixPath(y).parent.name: set(a) for y, a in plan.items() if y != _kok_env()}
    manifestler = {p.parent.name: p for p in sorted((SOHBET_MANIFEST_KOKU / "profiles").glob("*/distribution.yaml"))}
    _iddia(len(manifestler) >= 1 and set(manifestler) == set(profil_hedefleri),
           f"manifestli profiller {sorted(manifestler)} ≠ tablonun sohbet profilleri {sorted(profil_hedefleri)}")
    for ad, yol in manifestler.items():
        sirlar, ayarlar = _manifest_sir_adlari(yol)
        tablo = profil_hedefleri[ad]
        _iddia(tablo == sirlar, f"{ad}: tablo {sorted(tablo)} ≠ env_requires varsayılansız {sorted(sirlar)} "
                                f"(yalnız tabloda: {sorted(tablo - sirlar)} · yalnız manifestte: {sorted(sirlar - tablo)})")
        _iddia(not (tablo & ayarlar), f"{ad}: varsayılanlı (ayar) ad tabloda: {sorted(tablo & ayarlar)}")
    kok_manifest = SOHBET_MANIFEST_KOKU / "distribution.yaml"
    kok_tablo = set(plan.get(_kok_env(), {}))
    _iddia(kok_tablo == {API_SIR}, f"kök .env alanları {sorted(kok_tablo)} ({koku})")
    if kok_manifest.exists():
        sirlar, _ = _manifest_sir_adlari(kok_manifest)
        _iddia(kok_tablo == sirlar, f"kök: tablo {sorted(kok_tablo)} ≠ manifest {sorted(sirlar)}")


@pytest.mark.parametrize("ek", [("--vault",), ("--esitle",), ("--uret",), ("--vault", "--uret")],
                         ids=["vault", "esitle", "uret", "vault_uret"])
def test_D11_tohumlama_ROTASYON_bayraklariyla_reddedilir(tmp_path, ek):
    """Tohumlama bir rotasyon değildir (değer üretmez/sormaz, kasaya yazmaz, eşitlemez): `--vault`/`--esitle`/`--uret` ile
    AÇIK hatayla reddedilir — kasa şimi çağrılmaz, hiçbir dosya yazılmaz."""
    kok, ortam, kasa_log = v521._kasa_ortami(tmp_path)
    plan, _ = _tohum_plani()
    _tohum_sil(kok, *plan)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, TOHUMLA, *ek)
    _iddia(r.returncode != 0 and TOHUMLA in r.stderr, _ozet(r))
    _iddia(_imzalar(kok) == once and not kasa_log.exists() and not _yedekler(kok), "reddedilen birleşim YAZDI")
