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
import sys

import pytest
import yaml

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
    _iddia(satirlar == {("tenant", TENANT_SIR, SOHBET_TENANT_ALANI), ("api-sunucu", API_SIR, API_SIR)}, f"{satirlar}")
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
