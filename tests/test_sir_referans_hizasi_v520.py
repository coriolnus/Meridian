"""test_sir_referans_hizasi_v520.py — TSK-064 (d-1): rotasyon tablosu CANLI GERÇEKLE hizalanır.

BAĞLAM (Rol-1 A1 ölçümü, 2026-09-17). `sudo sir_rotasyon.sh --envanter` karşılaştırılabilen BÜTÜN
kopyaları EŞİT buldu ama üç yerde tablo gerçeği TAŞIMIYORDU:
  1. `MERIDIAN_DASH_TOKEN · /opt/meridian/.dash.env → OKUNAMADI` — dosya A1'de YOK (operatör kararı
     2026-09-14 17:46Z, yedek `/root/sir-yedek-20260914T174655Z-dash-env`). Tablo satırı yaşadıkça
     bir sonraki `--dash` rotasyonu "hedef dosya YOK" ile yarıda düşerdi (harita Risk B).
  2. `OPENROUTER_API_KEY` ve `APISIX_ADMIN_KEY`in REFERANS kopyası (tablodaki İLK satır)
     `/opt/apisix/.env-apisix`ti — yani (d-2)'nin sır satırlarını SİLECEĞİ dosyanın kendisi. Bugün
     iki sırrın yürürlükteki değeri Vault'tan gelir (kapı `.env-apisix.vault`ı ikinci `--env-file`
     olarak okur, hafıza `.env.vault`ı ikinci `EnvironmentFile=` olarak) ve Agent'ın TEKİL render
     hedefleri (`/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY`, `/etc/meridian/apisix_admin_key`)
     o değerin kanonik kopyasıdır. Referans oraya taşınır; `.env-apisix` satırları KOPYA olarak kalır
     (asıl satırlar (d-2)'ye kadar yaşıyor ve rotasyon onları da yazmak zorunda).
  3. Envanter "dosya yok" ile "okunamadı"yı AYNI kovaya atıyordu: `var` her `OSError`da "YOK",
     `esit` her `OSError`da "OKUNAMADI" basıyordu. Canlı ölçümün "OKUNAMADI"sı aslında "YOK"tu ve
     triyaj yanlış soruyu sordu ("izin mi bozuk?").

BÖLÜMLER
  A  Tablo gerçeği — `_kopyalar()` ↔ envanter: `.dash.env` yok, referanslar tekil hedefte, hermes aynen
  B  Envanter sınıfları (sahte kök): YOK ≠ OKUNAMADI, iki tarafta da; ALAN YOK / ÇİFT SATIR bozulmaz
  C  `--esitle`: yeni referanstan AYRI kopyaya; referans yoksa eskisi gibi DÜŞER
  D  Kasa: `vault_sir_koy.sh` openrouter tohum kaynağı · `--vault` envanter kanıtının referansı
  M  MUTASYON — her çivinin hedeflediği dalı gerçekten ısırdığının gösterimi

ÖLÇÜM MİMARİSİ v447'nin sahte köküdür (şimler davranış MODELİDİR, oyuncak değil) ve v491'in kasa
şimidir; burada yeniden yazılmaz, İTHAL edilir (tek-kaynak yasası). Her sahne kendi tohumunu AÇIKÇA
kurar (`_canli_sahne`): v447 tohumu bir gün yeniden şekillenirse bu dosyanın ölçtüğü dünya sessizce
kaymasın.

SIR DEĞERİ YOK: bütün değerler SAHTEDİR ve adında öyle yazar; hiçbir kanıt onları BASMAZ.
"""
from __future__ import annotations

import copy
import os
import pathlib
import subprocess

import pytest
import yaml

from tests.test_sir_rotasyon_v447 import (
    BETIK,
    ENVANTER,
    ESKI,
    _betik_kopyalari,
    _env_alan,
    _envanter_kopyalari,
    _kos,
    _mutant,
    _sahte_ortam,
)
from tests.test_vault_dalga2_v491 import (
    GIRDI_YALNIZ_OR,
    KANONIK_HEDEF,
    KOY_SH,
    YENI_VAULT_DEGERI,
    _koy_ortam,
    _sahte_vault,
    _vault_ortam,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
DROPIN_51 = KOK_DEPO / "deploy" / "oracle-a1" / "meridian.service.d" / "51-dash-env-kaldir.conf"

LLM_KRED = "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"
ADMIN_KRED = "/etc/meridian/apisix_admin_key"
DASH_KRED = "/etc/meridian/dash_token"
DASH_ENV = "/opt/meridian/.dash.env"
APISIX_ENV = "/opt/apisix/.env-apisix"

#: HERMES `.env` KOPYALARI — iki-kanal istisnası (Rol-1 (c) kararı 2026-09-15): hermes-agent
#: `.env.vault` OKUMAZ, kanalı rotasyonun kendisidir. Bu dilim onlara DOKUNMAZ; satırlar ELLE durur
#: (tablodan türetilseydi bir satır düştüğünde çivi de onunla küçülürdü).
HERMES_SATIRLARI = (
    "openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/bekci/.env OPENROUTER_API_KEY koru koru -",
    "openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/karne/.env OPENROUTER_API_KEY koru koru -",
    "openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/sef/.env OPENROUTER_API_KEY koru koru -",
    "openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/.env OPENROUTER_API_KEY koru koru -",
)

#: MUTASYON ÇAPALARI — "eski gerçek" (3d0bae5'teki tablo sırası). Çapa bulunamazsa `_mutant` DURUR:
#: bulunamayan bir mutasyon sessizce "mutasyonsuz betik" üretir ve hiçbir şey ölçmezdi.
YENI_OR_SIRASI = (
    "openrouter OPENROUTER_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY - 0400 root:root -\n"
    "openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_API_KEY koru koru -\n"
    "openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_AUTH koru koru Bearer\n")
ESKI_OR_SIRASI = (
    "openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_API_KEY koru koru -\n"
    "openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_AUTH koru koru Bearer\n"
    "openrouter OPENROUTER_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY - 0400 root:root -\n")
YENI_ADMIN_SIRASI = (
    "apisix-admin APISIX_ADMIN_KEY dosya /etc/meridian/apisix_admin_key - 0400 root:root -\n"
    "apisix-admin APISIX_ADMIN_KEY env /opt/apisix/.env-apisix APISIX_ADMIN_KEY koru koru -\n")
ESKI_ADMIN_SIRASI = (
    "apisix-admin APISIX_ADMIN_KEY env /opt/apisix/.env-apisix APISIX_ADMIN_KEY koru koru -\n"
    "apisix-admin APISIX_ADMIN_KEY dosya /etc/meridian/apisix_admin_key - 0400 root:root -\n")
DASH_SATIRI = "dash MERIDIAN_DASH_TOKEN dosya /etc/meridian/dash_token - 0400 root:root -\n"
ESKI_DASH_ENV_SATIRI = "dash MERIDIAN_DASH_TOKEN env /opt/meridian/.dash.env MERIDIAN_DASH_TOKEN koru koru -\n"

BAYAT = "SAHTE-BAYAT-KOPYA-0520"

#: İzin ölçümü ROOT altında anlamsızdır: root 000 bir dosyayı da okur ve "okunamadı" dalı hiç doğmaz.
#: Atlama bir KAPSAM BEYANIDIR (sessiz yeşil değil): koşum root ise sebep çıktıda görünür.
ROOT_DEGIL = pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                                reason="root 000 izinli dosyayı da okur — OKUNAMADI dalı doğmaz")


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _referanslar(satirlar: list[dict]) -> dict[str, dict]:
    """Her sır kimliğinin İLK satırı — `esitle()` ve `_envanter_esitlik`in referans kuralı
    (`[ "$sir" != "$onceki" ]` → ilk görülen satır referanstır)."""
    ref: dict[str, dict] = {}
    for s in satirlar:
        ref.setdefault(s["sir"], s)
    return ref


def _canli_sahne(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """A1'in 2026-09-17 ÖLÇÜLEN hâli: `.dash.env` YOK, OpenRouter'ın bütün kopyaları EŞİT, kapı
    yönetim anahtarının iki kopyası EŞİT. Tohum AÇIKÇA kurulur (bkz. dosya başlığı)."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / LLM_KRED.lstrip("/")).write_text(ESKI["or"] + "\n", encoding="utf-8")
    (kok / ADMIN_KRED.lstrip("/")).write_text(ESKI["admin"] + "\n", encoding="utf-8")
    dash_env = kok / DASH_ENV.lstrip("/")
    if dash_env.exists():
        dash_env.unlink()
    return kok, ortam


def _envanter_satirlari(cikti: str, sir: str) -> list[str]:
    return [s for s in cikti.splitlines() if s.startswith(f"  {sir} · ")]


def _satir(cikti: str, parca: str) -> str:
    bulunan = [s for s in cikti.splitlines() if parca in s and "BEYAN DIŞI" not in s]
    assert len(bulunan) == 1, (parca, bulunan, cikti)
    return bulunan[0].rstrip()


def _deger_yok(cikti: str) -> None:
    for d in list(ESKI.values()) + [BAYAT]:
        assert d not in cikti, f"SIR DEĞERİ çıktıya düştü: {d}"


def _alan_degistir(yol: pathlib.Path, alan: str, yeni_sag: str) -> None:
    satirlar = yol.read_text(encoding="utf-8").splitlines(keepends=True)
    say = 0
    for i, s in enumerate(satirlar):
        if s.startswith(alan + "="):
            satirlar[i] = f"{alan}={yeni_sag}\n"
            say += 1
    assert say == 1, f"sahne kurulamadı: {yol} [{alan}] {say} kez"
    yol.write_text("".join(satirlar), encoding="utf-8")


# =================================================================================================
# A) TABLO GERÇEĞİ
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (kalıcı kayıt `worktree-pythonpath-tuzagi`): sanal ortam ANA checkout'u
    `sys.path`e koyar. İthal edilen v447/v491 modülleri başka bir ağaçtan yüklenirse `BETIK` o
    ağacın betiğini gösterir ve bu dosyanın bütün çivileri BAŞKA bir kodu ölçer — sessizce."""
    for yol in (BETIK, ENVANTER, KOY_SH):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


def test_A1_DASH_ENV_kopyasi_TABLODA_ve_ENVANTERDE_YOK_referans_CREDENTIAL():
    """`.dash.env` 2026-09-14 17:46Z'de SİLİNDİ. Tablo satırı kalırsa `--dash` rotasyonu o satırda
    "hedef dosya YOK" ile yarıda düşer ve envanter her koşumda yanlış sınıfta bir satır basar.
    İKİ tablo birlikte ölçülür (betik + envanterin iki bloğu): biri kalırsa v447 A1/A2 zaten öter,
    ama `dosyalar:` bloğu o çivinin DIŞINDADIR."""
    betik = _betik_kopyalari()
    envanter = _envanter_kopyalari()
    assert not [s for s in betik if s["yol"] == DASH_ENV], "betik tablosunda .dash.env satırı duruyor"
    assert not [s for s in envanter if s["yol"] == DASH_ENV], "envanter rotasyon bloğunda .dash.env duruyor"
    dosyalar = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["dosyalar"]
    assert DASH_ENV not in {d["yol"] for d in dosyalar}, "envanter `dosyalar:` bloğunda .dash.env duruyor"
    dash = [s for s in betik if s["sir"] == "MERIDIAN_DASH_TOKEN"]
    assert [(s["tur"], s["yol"]) for s in dash] == [("dosya", DASH_KRED)], dash
    assert _referanslar(betik)["MERIDIAN_DASH_TOKEN"]["yol"] == DASH_KRED


def test_A2_REFERANSLAR_vault_TEKIL_hedefinde_env_apisix_satirlari_KOPYA_olarak_duruyor():
    """Referans = sırrın tablodaki İLK satırı. OpenRouter ve kapı yönetim anahtarı için o satır
    artık Vault'un tekil render hedefidir; `.env-apisix` satırları tabloda KALIR (rotasyon onları
    da yazar) ama İLK sırada değildir."""
    betik = _betik_kopyalari()
    ref = _referanslar(betik)
    assert (ref["OPENROUTER_API_KEY"]["tur"], ref["OPENROUTER_API_KEY"]["yol"]) == ("dosya", LLM_KRED)
    assert (ref["APISIX_ADMIN_KEY"]["tur"], ref["APISIX_ADMIN_KEY"]["yol"]) == ("dosya", ADMIN_KRED)
    kopya = {(s["sir"], s["yol"], s["alan"], s["onek"]) for s in betik if s is not ref[s["sir"]]}
    for beklenen in (("OPENROUTER_API_KEY", APISIX_ENV, "OPENROUTER_API_KEY", None),
                     ("OPENROUTER_API_KEY", APISIX_ENV, "OPENROUTER_AUTH", "Bearer"),
                     ("APISIX_ADMIN_KEY", APISIX_ENV, "APISIX_ADMIN_KEY", None)):
        assert beklenen in kopya, f"`.env-apisix` satırı KOPYA olarak yok: {beklenen}"


def test_A3_ENVANTER_SIRASI_betikle_AYNI_referans_iki_yerde_TEK():
    """v447 A1/A2 KÜME eşitliği ölçer — sıraya kördür. Envanterin şerhleri "referans şudur" diye
    yazıyor; sıra ayrışırsa belge bir satırı, betik başkasını referans sayar ve operatör yanlış
    dosyayı "doğru" sanar. Her sırrın satır SIRASI iki tabloda aynı olmalı."""
    def dizi(satirlar, alt_anahtar):
        out: dict[str, list] = {}
        for s in satirlar:
            out.setdefault(s["sir"], []).append((s[alt_anahtar], s["tur"], s["yol"], s.get("alan")))
        return out
    assert dizi(_envanter_kopyalari(), "alt_komut") == dizi(_betik_kopyalari(), "alt")


def test_A4_HERMES_env_satirlari_AYNEN_ve_SONDA():
    """Hermes iki-kanal istisnası: bu dilim hermes kopyalarının ne içeriğine ne tablodaki yerine
    dokunur. Dört satır BİREBİR durur ve OpenRouter bloğunun son dört satırıdır."""
    r = subprocess.run(["bash", str(BETIK), "--kopyalar"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    or_satirlari = [s for s in r.stdout.splitlines() if s.startswith("openrouter OPENROUTER_API_KEY ")]
    assert tuple(or_satirlari[-4:]) == HERMES_SATIRLARI, or_satirlari


def test_A5_VAULT_KV_openrouter_KAYNAGI_tablonun_REFERANSI():
    """`vault_sir_koy.sh` takma adın eşitlik kapısını `kaynak`tan kurar. `kaynak` rotasyon
    tablosunun REFERANSIYLA aynı kopya olmalı — v491 A5 KÜMEYİ ölçer, "hangisi kaynak"ı değil.
    Emsal `bot_key_meridian`: takma adın kaynağı birincilin RENDER EDİLMİŞ dosyasıdır."""
    kv = {g["ad"]: g for g in yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]}
    ref = _referanslar(_envanter_kopyalari())["OPENROUTER_API_KEY"]
    kaynak = kv["openrouter_api_key"]["kaynak"]
    assert kaynak == {"tur": "dosya", "dosya": LLM_KRED, "alan": None, "onek": None}, kaynak
    assert (ref["tur"], ref["yol"]) == ("dosya", kaynak["dosya"])
    assert kaynak["dosya"] == kv[kv["openrouter_api_key"]["ayni_deger"]]["hedef"], \
        "takma adın kaynağı birincilin render hedefi DEĞİL"
    kopyalar = kv["openrouter_api_key"]["kopya_kaynaklari"]
    assert {"tur": "env_satiri", "dosya": APISIX_ENV, "alan": "OPENROUTER_API_KEY", "onek": None} in kopyalar
    assert not [k for k in kopyalar if k["dosya"] == LLM_KRED], "referans kopya listesinde de duruyor"


def test_A6_DROPIN_51_serhi_SILINDI_notunu_tarihiyle_tasir_eski_cumle_KALIR():
    """Tarihçe silinmez: faz-2'nin "yerinde bırakılır" cümlesi o günün doğrusuydu. Altına tarihli
    SİLİNDİ notu ve birimin neden etkilenmediği (`EnvironmentFile=-` tireli) yazılır."""
    metin = " ".join(DROPIN_51.read_text(encoding="utf-8").replace("#", " ").split())
    assert "`.dash.env` yerinde bırakılır" in metin, "tarihçe cümlesi silinmiş"
    assert "2026-09-14" in metin and "SİLİNDİ" in metin, "silinme notu tarihiyle yok"
    assert "EnvironmentFile=-" in metin, "birimin etkilenmeme gerekçesi (tireli satır) yok"
    assert "/root/sir-yedek-20260914T174655Z-dash-env" in metin, "yedek yolu yok"


# =================================================================================================
# B) ENVANTER SINIFLARI — YOK ≠ OKUNAMADI
# =================================================================================================

def test_B1_KOPYA_dosyasi_YOKKEN_envanter_YOK_der(tmp_path):
    kok, ortam = _canli_sahne(tmp_path)
    (kok / "home/ubuntu/.hermes/profiles/sef/.env").unlink()
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    satir = _satir(r.stdout, "OPENROUTER_API_KEY · /home/ubuntu/.hermes/profiles/sef/.env [OPENROUTER_API_KEY]")
    assert satir.endswith("→ YOK"), satir
    _deger_yok(r.stdout + r.stderr)


@ROOT_DEGIL
def test_B2_KOPYA_var_ama_OKUNAMIYORKEN_envanter_OKUNAMADI_der(tmp_path):
    kok, ortam = _canli_sahne(tmp_path)
    p = kok / "home/ubuntu/.hermes/profiles/sef/.env"
    p.chmod(0o000)
    try:
        r = _kos(BETIK, ortam, "--envanter")
    finally:
        p.chmod(0o600)
    assert r.returncode == 0, r.stdout + r.stderr
    satir = _satir(r.stdout, "OPENROUTER_API_KEY · /home/ubuntu/.hermes/profiles/sef/.env [OPENROUTER_API_KEY]")
    assert satir.endswith("→ OKUNAMADI"), satir
    _deger_yok(r.stdout + r.stderr)


def test_B3_REFERANS_dosyasi_YOKKEN_referans_YOK_kopyalar_REFERANS_YOK_der(tmp_path):
    """Referans yokken kopya satırına "YOK" basmak, VAR olan kopyayı yok diye raporlamaktır. Kıyas
    yapılamadığının sebebi referanstadır ve satır bunu ADIYLA söyler."""
    kok, ortam = _canli_sahne(tmp_path)
    (kok / LLM_KRED.lstrip("/")).unlink()
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    ref = _satir(r.stdout, f"OPENROUTER_API_KEY · {LLM_KRED}")
    assert ref.endswith("→ YOK (referans kopya)"), ref
    kopya = _satir(r.stdout, f"OPENROUTER_API_KEY · {APISIX_ENV} [OPENROUTER_API_KEY]")
    assert kopya.endswith("→ REFERANS YOK"), kopya
    _deger_yok(r.stdout + r.stderr)


@ROOT_DEGIL
def test_B4_REFERANS_OKUNAMIYORKEN_referans_OKUNAMADI_der(tmp_path):
    kok, ortam = _canli_sahne(tmp_path)
    p = kok / LLM_KRED.lstrip("/")
    p.chmod(0o000)
    try:
        r = _kos(BETIK, ortam, "--envanter")
    finally:
        p.chmod(0o600)
    assert r.returncode == 0, r.stdout + r.stderr
    ref = _satir(r.stdout, f"OPENROUTER_API_KEY · {LLM_KRED}")
    assert ref.endswith("→ OKUNAMADI (referans kopya)"), ref
    _deger_yok(r.stdout + r.stderr)


def test_B5_MEVCUT_SINIFLAR_BOZULMAZ_alan_yok_ve_cift_satir(tmp_path):
    """Dosya VAR ama alan yok → "ALAN YOK" (dosya yokluğu DEĞİL); alan iki kez → "ÇİFT SATIR (2)".
    Yeni `FileNotFoundError` kovası bu iki sınıfı yutmamalı."""
    kok, ortam = _canli_sahne(tmp_path)
    apisix = kok / APISIX_ENV.lstrip("/")
    apisix.write_text("".join(s for s in apisix.read_text(encoding="utf-8").splitlines(keepends=True)
                              if not s.startswith("OPENROUTER_AUTH=")), encoding="utf-8")
    hermes = kok / "home/ubuntu/.hermes/.env"
    hermes.write_text(hermes.read_text(encoding="utf-8") + f"OPENROUTER_API_KEY={ESKI['or']}\n",
                      encoding="utf-8")
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _satir(r.stdout, f"{APISIX_ENV} [OPENROUTER_AUTH]").endswith("→ ALAN YOK")
    assert _satir(r.stdout, "/home/ubuntu/.hermes/.env [OPENROUTER_API_KEY]").endswith("→ ÇİFT SATIR (2)")
    _deger_yok(r.stdout + r.stderr)


def test_B6_CANLI_SAHNEDE_referanslar_tekil_hedef_ve_hepsi_ESIT(tmp_path):
    """Pozitif kontrol: A1'in ölçülen hâlinde (hepsi eşit) referans satırları tekil hedefi
    gösterir ve karşılaştırılabilen her kopya EŞİT'tir — B1-B5'in kırmızıları sahne kazası değil."""
    _, ortam = _canli_sahne(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    for sir, ref_yol in (("OPENROUTER_API_KEY", LLM_KRED), ("APISIX_ADMIN_KEY", ADMIN_KRED),
                         ("MERIDIAN_DASH_TOKEN", DASH_KRED)):
        satirlar = _envanter_satirlari(r.stdout, sir)
        assert satirlar and ref_yol in satirlar[0] and satirlar[0].endswith("→ VAR (referans kopya)"), satirlar
        assert all(s.rstrip().endswith("→ EŞİT") for s in satirlar[1:]), satirlar
    assert DASH_ENV not in r.stdout, "silinmiş .dash.env envanterde hâlâ görünüyor"
    _deger_yok(r.stdout + r.stderr)


def test_B7_DASH_ENV_GERI_DOGARSA_BEYAN_DISI_KOPYA_diye_bagirilir(tmp_path):
    """Satır tablodan çıktı ama dosya TARAMADA kaldı (bilinçli): biri `.dash.env`i geri yaratıp
    pano jetonunu içine koyarsa o artık rotasyonun YAZMADIĞI bir kopyadır — ve envanter bunu
    söylemek zorundadır. Taramadan da çıkarsaydık geri dönüş SESSİZ olurdu (bedel yasası)."""
    kok, ortam = _canli_sahne(tmp_path)
    (kok / DASH_ENV.lstrip("/")).write_text(f'MERIDIAN_DASH_TOKEN="{ESKI["dash"]}"\n', encoding="utf-8")
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"BEYAN DIŞI KOPYA: {DASH_ENV} [MERIDIAN_DASH_TOKEN]" in r.stdout, r.stdout
    _deger_yok(r.stdout + r.stderr)


def test_B8_DASH_rotasyonu_DASH_ENV_YOKKEN_KOSAR_ve_onu_YARATMAZ(tmp_path):
    """Harita Risk B'nin kapanışı: canlı dünyada (`.dash.env` YOK) `--dash` hem kuru hem gerçek
    koşumda yarıda düşmez, silinmiş dosyayı geri doğurmaz ve adını basmaz."""
    kok, ortam = _canli_sahne(tmp_path)
    kuru = _kos(BETIK, ortam, "--dash", "--kuru")
    assert kuru.returncode == 0, kuru.stdout + kuru.stderr
    assert DASH_KRED in kuru.stdout and ".dash.env" not in kuru.stdout, kuru.stdout
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = (kok / DASH_KRED.lstrip("/")).read_text(encoding="utf-8").strip()
    assert yeni != ESKI["dash"] and len(yeni) == 48
    assert not (kok / DASH_ENV.lstrip("/")).exists(), "rotasyon silinmiş .dash.env'i geri yarattı"
    assert ".dash.env" not in r.stdout + r.stderr, "geri alma/rapor metni silinmiş dosyayı anıyor"
    assert yeni not in r.stdout + r.stderr


# =================================================================================================
# C) --esitle — YENİ REFERANSTAN
# =================================================================================================

def _or_apisix_bayat(kok: pathlib.Path) -> pathlib.Path:
    apisix = kok / APISIX_ENV.lstrip("/")
    _alan_degistir(apisix, "OPENROUTER_API_KEY", f'"{BAYAT}"')
    _alan_degistir(apisix, "OPENROUTER_AUTH", f'"Bearer {BAYAT}"')
    return apisix


def test_C1_esitle_OPENROUTER_tekil_hedeften_env_apisix_e_yazar(tmp_path):
    kok, ortam = _canli_sahne(tmp_path)
    apisix = _or_apisix_bayat(kok)
    r = _kos(BETIK, ortam, "--openrouter", "--esitle")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"OPENROUTER_API_KEY · {LLM_KRED} → REFERANS" in r.stdout, r.stdout
    assert _env_alan(apisix, "OPENROUTER_API_KEY") == f'"{ESKI["or"]}"', "AYRI kopya referansa çekilmedi"
    assert _env_alan(apisix, "OPENROUTER_AUTH") == f'"Bearer {ESKI["or"]}"', "önekli kopya çekilmedi"
    assert (kok / LLM_KRED.lstrip("/")).read_text(encoding="utf-8") == ESKI["or"] + "\n", \
        "REFERANSA dokunuldu"
    assert r.stdout.count("yazıldı:") == 2, r.stdout
    assert "choices" in r.stdout, "kapı kanıtı basılmadı"
    _deger_yok(r.stdout.replace(str(tmp_path), "<TMP>") + r.stderr)


def test_C2_esitle_APISIX_ADMIN_credentialdan_env_apisix_e_yazar(tmp_path):
    """Faz-1C'de yön TERSİYDİ (kapının kanalı → credential). Bugün kapının yürürlükteki değeri
    `.env-apisix.vault`tan gelir ve credential dosyası o değerin Agent render'ıdır: bayat olan
    `.env-apisix` satırıdır."""
    kok, ortam = _canli_sahne(tmp_path)
    apisix = kok / APISIX_ENV.lstrip("/")
    _alan_degistir(apisix, "APISIX_ADMIN_KEY", BAYAT)
    r = _kos(BETIK, ortam, "--apisix-admin", "--esitle")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"APISIX_ADMIN_KEY · {ADMIN_KRED} → REFERANS" in r.stdout, r.stdout
    assert _env_alan(apisix, "APISIX_ADMIN_KEY") == ESKI["admin"]
    assert (kok / ADMIN_KRED.lstrip("/")).read_text(encoding="utf-8") == ESKI["admin"] + "\n", \
        "REFERANSA dokunuldu"
    assert "yeniden başlatma YAPILMADI" in r.stdout
    _deger_yok(r.stdout.replace(str(tmp_path), "<TMP>") + r.stderr)


@pytest.mark.parametrize("alt,ref_yol,bayat_hedef,bayat_alan", [
    ("--openrouter", LLM_KRED, "home/ubuntu/.hermes/.env", "OPENROUTER_API_KEY"),
    ("--apisix-admin", ADMIN_KRED, APISIX_ENV.lstrip("/"), "APISIX_ADMIN_KEY"),
])
def test_C3_esitle_REFERANS_YOKSA_eskisi_gibi_DUSER_hicbir_sey_yazilmaz(tmp_path, alt, ref_yol,
                                                                        bayat_hedef, bayat_alan):
    kok, ortam = _canli_sahne(tmp_path)
    hedef = kok / bayat_hedef
    _alan_degistir(hedef, bayat_alan, BAYAT)
    once = hedef.read_text(encoding="utf-8")
    (kok / ref_yol.lstrip("/")).unlink()
    r = _kos(BETIK, ortam, alt, "--esitle")
    assert r.returncode != 0, r.stdout + r.stderr
    assert f"referans kopya YOK: {ref_yol}" in r.stderr, r.stderr
    assert hedef.read_text(encoding="utf-8") == once, "referans yokken yazıldı"
    assert not (kok / ref_yol.lstrip("/")).exists(), "referans yokken referans YARATILDI"
    assert not list((kok / "root").glob("sir-yedek-*")), "yazım yokken yedek alındı"


# =================================================================================================
# D) KASA — tohum kaynağı ve `--vault` kanıtı
# =================================================================================================

def _koy_sahnesi(tmp_path: pathlib.Path, apisix_or: str | None = None,
                 eski_kaynak: bool = False) -> tuple[pathlib.Path, pathlib.Path]:
    """GERÇEK envanterin iki girdisi (birincil `HINDSIGHT_API_LLM_API_KEY` + takma ad
    `openrouter_api_key`) yolları tmp köke kaydırılarak küçük bir envantere kopyalanır —
    ölçülen şey envanterin BUGÜNKÜ `kaynak`/`kopya_kaynaklari` sözleşmesidir, elle yazılmış bir
    benzeri değil. `eski_kaynak=True` 3d0bae5'teki biçimi (kaynak = `.env-apisix` satırı) kurar:
    mutasyon/pozitif kontrol."""
    kok = tmp_path / "koy_kok"
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    ind = {g["ad"]: g for g in veri["vault_kv"]}
    birincil = copy.deepcopy(ind["HINDSIGHT_API_LLM_API_KEY"])
    takma = copy.deepcopy(ind["openrouter_api_key"])
    if eski_kaynak:
        kred = takma["kaynak"]
        apisix = next(k for k in takma["kopya_kaynaklari"]
                      if k["dosya"] == APISIX_ENV and k["alan"] == "OPENROUTER_API_KEY")
        takma["kopya_kaynaklari"] = [kred if k is apisix else k for k in takma["kopya_kaynaklari"]]
        takma["kaynak"] = apisix
    deger = "SAHTE-KOY-OR-0520"
    satirlar: dict[str, list[str]] = {}
    for k in [takma["kaynak"], *takma["kopya_kaynaklari"]]:
        if k["tur"] == "dosya":
            continue
        onek = "Bearer " if k["onek"] == "Bearer" else ""
        d = apisix_or if (apisix_or and k["dosya"] == APISIX_ENV
                          and k["alan"] == "OPENROUTER_API_KEY") else deger
        satirlar.setdefault(k["dosya"], []).append(f"{k['alan']}={onek}{d}\n")
    for yol, govde in satirlar.items():
        p = kok / yol.lstrip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(govde), encoding="utf-8")
    kred = kok / birincil["hedef"].lstrip("/")
    kred.parent.mkdir(parents=True, exist_ok=True)
    kred.write_text(deger + "\n", encoding="utf-8")
    birincil["hedef"] = str(kok) + birincil["hedef"]
    for k in [takma["kaynak"], *takma["kopya_kaynaklari"]]:
        k["dosya"] = str(kok) + k["dosya"]
    env = tmp_path / "koy_envanter.yaml"
    env.write_text(yaml.safe_dump({"vault_kv": [birincil, takma]}, allow_unicode=True), encoding="utf-8")
    return kok, env


def test_D1_koy_OPENROUTER_tohum_kaynagi_TEKIL_hedef_env_apisix_KOPYA(tmp_path):
    """Takma adın eşitlik kapısı bugün Vault'un tekil hedefini REFERANS okur: `.env-apisix` ayrışırsa
    AYRI diye adı basılan `.env-apisix`tir, referans değil. (d-2) satırı sildiğinde tohum kaynağı
    kaybolmaz — kaynak o dosyada yaşamıyor."""
    kok, env = _koy_sahnesi(tmp_path, apisix_or="SAHTE-AYRISMIS-APISIX-0520")
    binler, argv_log, _ = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--kuru"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, env))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (f"TAKMA AD openrouter_api_key → HINDSIGHT_API_LLM_API_KEY  "
            f"(secret/meridian/HINDSIGHT_API_LLM_API_KEY)  ← {kok}{LLM_KRED}") in r.stdout, r.stdout
    assert f"✗ kopya AYRI: {kok}{APISIX_ENV} [OPENROUTER_API_KEY]" in r.stdout, r.stdout
    assert f"kopya AYRI: {kok}{LLM_KRED}" not in r.stdout, r.stdout
    assert not argv_log.exists(), "kuru koşum kasaya çağrı yaptı"
    assert "SAHTE-KOY-OR-0520" not in r.stdout and "SAHTE-AYRISMIS" not in r.stdout


def test_D2_koy_UYGULA_takma_ad_TEKIL_hedefle_EŞİT_kv_put_YOK(tmp_path):
    kok, env = _koy_sahnesi(tmp_path)
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, env))
    assert r.returncode == 0, r.stdout + r.stderr
    argv = argv_log.read_text(encoding="utf-8")
    assert "kv put secret/meridian/HINDSIGHT_API_LLM_API_KEY" in argv
    assert "kv put secret/meridian/openrouter_api_key" not in argv
    assert "✓ TAKMA AD openrouter_api_key → HINDSIGHT_API_LLM_API_KEY" in r.stdout, r.stdout
    assert "SAHTE-KOY-OR-0520" not in r.stdout + argv


def test_D3_VAULT_rotasyonu_ENVANTER_KANITININ_referansi_RENDER_hedefi(tmp_path):
    """`--vault` kipinin referansa bağlı TEK davranışı son kanıttır (`_envanter_esitlik`): yazım,
    render ölçümü ve restart listesi tablo sırasından bağımsızdır (kod okundu). Kanıt artık
    "kopyalar KASADAN render edilen değere eşit mi" sorusunu sorar — doğru yön."""
    kok, ortam = _canli_sahne(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=GIRDI_YALNIZ_OR)
    assert r.returncode == 0, r.stdout + r.stderr
    kanit = r.stdout.split("kanıt: envanter eşitlik ölçümü")[1]
    satirlar = _envanter_satirlari(kanit, "OPENROUTER_API_KEY")
    assert satirlar and KANONIK_HEDEF in satirlar[0] and "(referans kopya)" in satirlar[0], satirlar
    assert len(satirlar) == 13 and all(s.rstrip().endswith("→ EŞİT") for s in satirlar[1:]), satirlar
    assert YENI_VAULT_DEGERI not in r.stdout + r.stderr


# =================================================================================================
# M) MUTASYON
# =================================================================================================

def test_M1_MUT_OPENROUTER_ESKI_SIRA_esitle_YANLIS_YONE_yazar_C1_KIRMIZI(tmp_path):
    """C1'in ısırdığı dal: tablo sırası. Eski sırada referans bayat `.env-apisix` olur ve eşitleme
    Vault'un render ettiği değeri BAYAT değerle EZER — (d-1)'in kapattığı tam yön hatası."""
    m = _mutant(tmp_path, (YENI_OR_SIRASI, ESKI_OR_SIRASI))
    kok, ortam = _canli_sahne(tmp_path)
    _or_apisix_bayat(kok)
    r = _kos(m, ortam, "--openrouter", "--esitle")
    assert (kok / LLM_KRED.lstrip("/")).read_text(encoding="utf-8").strip() == BAYAT, \
        f"MUTASYON ISIRMADI: eski sırada da tekil hedef korundu:\n{r.stdout}\n{r.stderr}"


def test_M2_MUT_APISIX_ADMIN_ESKI_SIRA_credential_EZILIR_C2_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (YENI_ADMIN_SIRASI, ESKI_ADMIN_SIRASI))
    kok, ortam = _canli_sahne(tmp_path)
    _alan_degistir(kok / APISIX_ENV.lstrip("/"), "APISIX_ADMIN_KEY", BAYAT)
    r = _kos(m, ortam, "--apisix-admin", "--esitle")
    assert (kok / ADMIN_KRED.lstrip("/")).read_text(encoding="utf-8").strip() == BAYAT, \
        f"MUTASYON ISIRMADI:\n{r.stdout}\n{r.stderr}"


def test_M3_MUT_var_YOK_kovasi_kalkarsa_referans_OKUNAMADI_gorunur_B3_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ('        except FileNotFoundError:\n            print("YOK")\n', ""))
    kok, ortam = _canli_sahne(tmp_path)
    (kok / LLM_KRED.lstrip("/")).unlink()
    r = _kos(m, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    ref = _satir(r.stdout, f"OPENROUTER_API_KEY · {LLM_KRED}")
    assert not ref.endswith("→ YOK (referans kopya)") and ref.endswith("→ OKUNAMADI (referans kopya)"), \
        f"MUTASYON ISIRMADI: {ref}"


def test_M4_MUT_esit_YOK_kovasi_kalkarsa_kopya_OKUNAMADI_gorunur_B1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (
        '        except FileNotFoundError as yok:\n'
        '            print("REFERANS YOK" if yok.filename == argv[3] else "YOK")\n'
        '            return\n', ""))
    kok, ortam = _canli_sahne(tmp_path)
    (kok / "home/ubuntu/.hermes/profiles/sef/.env").unlink()
    r = _kos(m, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    satir = _satir(r.stdout, "OPENROUTER_API_KEY · /home/ubuntu/.hermes/profiles/sef/.env [OPENROUTER_API_KEY]")
    assert satir.endswith("→ OKUNAMADI"), f"MUTASYON ISIRMADI: {satir}"


def test_M5_MUT_DASH_ENV_satiri_GERI_GELIRSE_dash_rotasyonu_DUSER_B8_KIRMIZI(tmp_path):
    """Harita Risk B'nin çoğaltımı: satır tabloda, dosya diskte yok → `--dash` yazım sırasında
    "hedef dosya YOK" ile düşer. B8'in yeşili satırın kaldırılmasına BAĞLIDIR."""
    m = _mutant(tmp_path, (DASH_SATIRI, DASH_SATIRI + ESKI_DASH_ENV_SATIRI))
    kok, ortam = _canli_sahne(tmp_path)
    r = _kos(m, ortam, "--dash")
    assert r.returncode != 0 and f"hedef dosya YOK: {DASH_ENV}" in r.stderr, \
        f"MUTASYON ISIRMADI:\n{r.stdout}\n{r.stderr}"


def test_M6_MUT_DASH_ENV_TARAMADAN_cikarsa_geri_donus_SESSIZ_B7_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("/opt/meridian/.env\n/opt/meridian/.dash.env\n", "/opt/meridian/.env\n"))
    kok, ortam = _canli_sahne(tmp_path)
    (kok / DASH_ENV.lstrip("/")).write_text(f'MERIDIAN_DASH_TOKEN="{ESKI["dash"]}"\n', encoding="utf-8")
    r = _kos(m, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"BEYAN DIŞI KOPYA: {DASH_ENV}" not in r.stdout, "MUTASYON ISIRMADI"


def test_M7_MUT_ESKI_TOHUM_KAYNAGI_ile_D1_etiketi_TERSINE_doner(tmp_path):
    """D1'in ısırdığı şey envanterin `kaynak` alanıdır: 3d0bae5 biçiminde (kaynak `.env-apisix`)
    AYRI diye adı basılan tekil hedef olur — yani D1 gerçekten kaynağın NEREDE olduğunu ölçüyor."""
    kok, env = _koy_sahnesi(tmp_path, apisix_or="SAHTE-AYRISMIS-APISIX-0520", eski_kaynak=True)
    binler, _, _ = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--kuru"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, env))
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"✗ kopya AYRI: {kok}{LLM_KRED}" in r.stdout, f"POZİTİF KONTROL DÜŞTÜ:\n{r.stdout}"
    assert f"✗ kopya AYRI: {kok}{APISIX_ENV} [OPENROUTER_API_KEY]" not in r.stdout


def test_M8_MUT_OPENROUTER_ESKI_SIRA_vault_kaniti_env_apisix_i_referans_sayar_D3_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (YENI_OR_SIRASI, ESKI_OR_SIRASI))
    kok, ortam = _canli_sahne(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(m, ortam, "--vault", "--openrouter", girdi=GIRDI_YALNIZ_OR)
    assert r.returncode == 0, r.stdout + r.stderr
    satirlar = _envanter_satirlari(r.stdout.split("kanıt: envanter eşitlik ölçümü")[1], "OPENROUTER_API_KEY")
    assert KANONIK_HEDEF not in satirlar[0] and APISIX_ENV in satirlar[0], f"MUTASYON ISIRMADI: {satirlar}"
