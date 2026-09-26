"""test_sir_kasa_surum_v561.py — TSK-064 takibi: genel kasa döngüsü KV SÜRÜMÜNÜ kaydeder ve geri alma reçetesi
kasayı DOSYADAN ÖNCE geri alır (2026-09-27).

NUMARA: `ls tests | grep _v561` boş (ana checkout + bütün worktree'ler tarandı 2026-09-27; en yüksek v560).

BAĞLAM (TSK-226c incelemesi BULGU 1, ORTA — Rol-1 doğruladı). `sir_rotasyon.sh`in genel kasa döngüsü
(`vault_rotasyon`: kapi · tenant · dash · apisix-admin · openrouter; `--uret`li ya da istemli) kasaya `kv put`
yazıyordu ama yazım ÖNCESİ `current_version`ı KAYDETMİYORDU ve geri alma reçetesi bu yol için yalnız dosya
yedeğini (`sudo cp -p $YEDEK/…`) öneriyordu. Render/kanıt aşamasında arıza olursa operatör dosyaları geri koysa
bile Agent bir sonraki render'da onları kasadaki YENİ değerle tekrar ezer → reçete YANLIŞ güvence verirdi.
`--db --vault` ve `--cp --vault` dalları bunu zaten doğru yapıyordu; bu dilim AYNI deseni genel döngüye getirir
ve sürüm okumasını üç dalın ortak yardımcısına (`_kasa_surumu`) çıkarır (tek-kaynak yasası).

YOL YOKSA (metadata yok → ilk yazım) — KARAR: DURUR, `--db`/`--cp` ile AYNI. Gerçek Vault `kv metadata get`
yazılmamış yolda 2 ile düşer, stdout boş ("No value found at secret/metadata/…" — Vault CLI davranışı, A1'de
ÖLÇÜLMEDİ) → `pipefail` → "okunamadı"; `current_version` 0 (meta var, sürüm yok) → "geçersiz". İkisinde de
kasaya HİÇBİR ŞEY yazılmaz: geri alma hedefi olmayan bir yazım rotasyon değil BAĞLAMADIR (`vault_sir_koy.sh`).
db/cp dalları bu hâle `kv get` adımında (ESKİ değer okunamadı) ve sürüm kapısında AYNI biçimde durur. D bölümü
iki biçimi de ölçer (sarmalayıcının `yok` kipi = gerçek Vault; `yol_yok` = v556 şiminin kendi modeli).

DÜZENEK — ŞİMLER YENİDEN YAZILMADI: v556 `_cp_ortami` (v447 sahte kök + KV v2 sahte kasa + sahte Agent +
CP-duyarlı systemctl/curl) ve v538 `_db_ortami`. Bu dosya üstlerine YALNIZ bir `vault` SARMALAYICISI ekler:
`SAHTE_METADATA=<kip>` iken (`SAHTE_METADATA_YOL` verilirse yalnız o yolda) `kv metadata get` cevabını bozar;
öteki her çağrı alttaki şime AYNEN gider. Kasa tohumları sürüm numarasını AYIRT EDİCİ kılar (kiracı 2 sürüm,
NOUS 2, LLM 3): geri alma "bir önceki" ya da "yazım sonrası" sürüme dönse sayı ayrışır.

BÖLÜMLER
  A  sözleşme — sürüm okuması TEK yerde (`_kasa_surumu`), üç dal da oradan
  B  kuru — her kasa yolu için "ÖNCE current_version kaydedilir — geri alma: vault kv rollback" satırı; kasaya çağrı YOK
  C  gerçek — metadata yazımdan ÖNCE · sürüm doğru · reçetede rollback DOSYADAN ÖNCE · reçeteyi izlemek kasayı
     ESKİ değere döndürür · iki sırlı tur · put düşerse de rollback
  D  ön kapı — okunamaz/geçersiz sürüm (yol yok dahil) → kasaya yazım YOK + açık hata + reçete GEREKMEZ
  E  db/cp BİREBİR — ortak yardımcı ↔ taban satır içi blok İZ KIYASI (aynı dünya, aynı senaryo)
  F  kasasız eski yol reçetesi DEĞİŞMEDİ
  M  MUTASYONLAR — brief'in dördü (sürüm okuma · reçetede kv satırı · sıra · geçersiz sürüm kapısı) + kuru satırı ·
     iki sırlı tur metni · evre sırası

SIR DEĞERİ YOK: tohumlar `SAHTE-` önekli; iddialar bool'a indirilir (v557 `_iddia`/`_maskeli` — pytest içgözlemi
işlenenleri HAM basmasın). Sürüm numarası sır değildir.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest

from tests import test_cp_rotasyon_v556 as v556
from tests import test_sir_uret_v557 as v557
from tests import test_vault_db_kasa_v538 as v538
from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_sir_rotasyon_v447 import BETIK, ENVANTER, ESKI, _dosya_imzalari, _kos, _sahte_ortam

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

TENANT_YOLU = "secret/meridian/HINDSIGHT_API_TENANT_API_KEY"
TENANT_HEDEF = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
TAKMA_TENANT = "secret/meridian/hindsight_cp_dataplane_api_key"     # takma ad — kasada YOLU YOK
NOUS_YOLU = "secret/meridian/nous_api_key"
LLM_YOLU = "secret/meridian/HINDSIGHT_API_LLM_API_KEY"
TAKMA_OR = "secret/meridian/openrouter_api_key"                     # takma ad — kasada YOLU YOK

ONCEKI_TENANT = "SAHTE-ONCEKI-TENANT-0561"
ONCEKI_NOUS = "SAHTE-ONCEKI-NOUS-0561"
LLM_V1, LLM_V2 = "SAHTE-LLM-V1-0561", "SAHTE-LLM-V2-0561"
#: Kasa tohumları — A1'de bağlı yollar DOLUDUR (dalga-1/2 `vault_sir_koy.sh`). Sürüm sayıları AYIRT EDİCİ.
TOHUM = {TENANT_YOLU: [ONCEKI_TENANT, ESKI["tenant"]],          # current_version 2
         NOUS_YOLU: [ONCEKI_NOUS, ESKI["nous"]],                # 2
         LLM_YOLU: [LLM_V1, LLM_V2, ESKI["or"]]}                # 3
YENI_NOUS = "SAHTE-YENI-NOUS-0561"
YENI_OR = "SAHTE-YENI-OR-0561"
TENANT_BIRIMLER = "hindsight-api.service hindsight-cp.service meridian.service"

KURU_SATIRI = "  kasa sürümü      : ÖNCE current_version kaydedilir — geri alma: vault kv rollback -version=<o sürüm> {yol}"
SURUM_OLDU = "  ✓ kasa sürümü (yazım ÖNCESİ): {n} — geri alma: vault kv rollback -version={n}"
ROLLBACK_SATIRI = "        vault kv rollback -version={n} {yol}"
RECETE_BASI = ">> GERİ ALMA"
KASA_ONCE = "sıra: ÖNCE kasa, SONRA dosya"
DOSYA_ADIMI = "sudo cp -p "
GEREKMEZ = "GEREKMEZ"
HICBIR = "HİÇBİR ŞEY yazılmadı"
IKINCI_SIR = "bu sır YAZILMADI; bu turda ÖNCE yazılan kasa yolu VAR — reçete aşağıda"
OKUNAMADI = "!! kasa sürümü okunamadı ({yol}) — geri alma hedefi bilinmeden kasaya YAZILMAZ ({neden})"
GECERSIZ = "!! kasa sürümü geçersiz: '{v}' ({yol}) — kasaya {neden}"

#: `kv metadata get` sarmalayıcısı. `yok` = gerçek Vault'un yazılmamış yol cevabı (2, stdout boş).
SIM_METADATA = '''#!__PY__
"""`kv metadata get` cevabını SAHTE_METADATA kipine göre bozar (SAHTE_METADATA_YOL verilirse YALNIZ o yolda);
öteki her çağrı alttaki şime AYNEN gider. Değer taşımaz: yalnız yol ve kip."""
import json, os, sys
ASIL = __ASIL__
a = sys.argv[1:]
kip = os.environ.get("SAHTE_METADATA", "")
sart = os.environ.get("SAHTE_METADATA_YOL", "")
if a[:3] == ["kv", "metadata", "get"] and kip and (not sart or a[-1] == sart):
    yol = a[-1]
    with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
        fh.write("OLAY kv-metadata-%s %s\\n" % (kip, yol))
    if kip == "yok":
        sys.stderr.write("No value found at %s\\n" % yol.replace("secret/", "secret/metadata/", 1))
        sys.exit(2)
    govde = {"sifir": {"data": {"current_version": 0}},
             "eksi": {"data": {"current_version": -1}},
             "bozuk": {"data": {}},
             "metin": {"data": {"current_version": "7a"}}}.get(kip)
    if govde is not None:
        print(json.dumps(govde))
    sys.exit(0)
os.execv(ASIL, [ASIL] + a)
'''

#: (kip, sınıf, görünen sürüm) — `okunamadi` = pipeline/ayrıştırma düştü; `gecersiz` = sayı ama kapıdan geçmez.
KIPLER = (("yok", "okunamadi", None), ("bos", "okunamadi", None), ("bozuk", "okunamadi", None),
          ("metin", "okunamadi", None), ("sifir", "gecersiz", "0"), ("eksi", "gecersiz", "-1"))


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

_iddia = v557._iddia
_maskeli = v557._maskeli
_ozet = v557._ozet


def _sarmala(tmp_path: pathlib.Path, ortam: dict) -> dict:
    """VAULT_BIN'i metadata sarmalayıcısıyla değiştirir (alttaki şim AYNEN koşar)."""
    binn = tmp_path / "bin_v561"
    binn.mkdir()
    (binn / "vault").write_text(SIM_METADATA.replace("__PY__", sys.executable)
                                .replace("__ASIL__", repr(ortam["VAULT_BIN"])), encoding="utf-8")
    (binn / "vault").chmod(0o755)
    return dict(ortam, VAULT_BIN=str(binn / "vault"))


def _dunya(tmp_path: pathlib.Path, **bayrak: str):
    """v556 CP dünyası + bu dosyanın kasa tohumları + metadata sarmalayıcısı. `bayrak`: SAHTE_* ortamı."""
    kok, ortam, log, durum = v556._cp_ortami(tmp_path)
    veri = json.loads(durum.read_text(encoding="utf-8"))
    veri.update({y: list(d) for y, d in TOHUM.items()})
    durum.write_text(json.dumps(veri), encoding="utf-8")
    ortam = _sarmala(tmp_path, ortam)
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _kasa(durum: pathlib.Path, yol: str) -> list[str]:
    return json.loads(durum.read_text(encoding="utf-8")).get(yol, [])


def _putlar(log: pathlib.Path) -> list[str]:
    if not log.exists():
        return []
    return [s.split()[2] for s in log.read_text(encoding="utf-8").splitlines() if s.startswith("kv put ")]


def _recete(stderr: str) -> list[str]:
    """Geri alma reçetesi — `>> GERİ ALMA` satırından sonuna."""
    satirlar = stderr.splitlines()
    for i, s in enumerate(satirlar):
        if s.startswith(RECETE_BASI):
            return satirlar[i:]
    return []


def _satir_indeksi(satirlar: list[str], parca: str) -> int | None:
    for i, s in enumerate(satirlar):
        if parca in s:
            return i
    return None


def _recete_ihlalleri(r: subprocess.CompletedProcess, beklenen: list[tuple[str, int]],
                      yok: tuple[str, ...] = ()) -> list[str]:
    """Kasa evresi reçetesi: her (yol, sürüm) için TAM rollback satırı · hepsi DOSYA adımından ÖNCE · başlık
    'ÖNCE kasa' der · `yok` yolları için rollback YOK · GEREKMEZ YOK."""
    ih = []
    rec = _recete(r.stderr)
    if not rec:
        return ["geri alma reçetesi basılmadı"]
    if KASA_ONCE not in rec[0]:
        ih.append("reçete başlığı 'ÖNCE kasa, SONRA dosya' demiyor")
    dosya = _satir_indeksi(rec, DOSYA_ADIMI)
    if dosya is None:
        ih.append("reçetede dosya adımı (sudo cp -p) yok")
    for yol, n in beklenen:
        satir = ROLLBACK_SATIRI.format(n=n, yol=yol)
        if satir not in rec:
            ih.append(f"reçetede yok: kv rollback -version={n} {yol}")
        elif dosya is not None and rec.index(satir) > dosya:
            ih.append(f"kv rollback ({yol}) DOSYA adımından SONRA")
    for yol in yok:
        if any("kv rollback" in s and s.rstrip().endswith(" " + yol) for s in rec):
            ih.append(f"reçete YAZILMAMIŞ yolu geri alıyor: {yol}")
    if sum("vault kv rollback" in s for s in rec) != len(beklenen):
        ih.append(f"rollback satırı sayısı {sum('vault kv rollback' in s for s in rec)} ≠ {len(beklenen)}")
    if any(GEREKMEZ in s for s in rec):
        ih.append("kasa evresinde 'GEREKMEZ' dendi")
    return ih


# =================================================================================================
# A) SÖZLEŞME — sürüm okuması TEK yerde
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v556/v557 A0): ithal edilen modül başka ağaçtan yüklenirse çiviler BAŞKA betiği ölçer."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v556.__file__), pathlib.Path(v557.__file__),
                pathlib.Path(v538.__file__), pathlib.Path(v521.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


def test_A1_TEK_KAYNAK_surum_okumasi_YALNIZ_kasa_surumu_nde_uc_dal_ORADAN():
    """`kv metadata get` ve `current_version` ayrıştırması betikte TEK kez, `_kasa_surumu` gövdesinde; üç dal
    (`vault_rotasyon` · `vault_db_rotasyon` · `vault_cp_rotasyon`) onu TAM BİR kez çağırır. Üç kopya sessizce
    ayrışırdı (tek-kaynak yasası) — biri kapıyı gevşetir, öteki gevşetmez."""
    # Yorum satırları sayılmaz: şerh komutu ADIYLA anabilir (okuyucuya), kopya olan KODDUR.
    kod = lambda m: "\n".join(s for s in m.splitlines() if not s.lstrip().startswith("#"))  # noqa: E731
    metin = kod(BETIK.read_text(encoding="utf-8"))
    govde = kod(v521._fonksiyon("_kasa_surumu"))
    for parca in ("kv metadata get", '["current_version"]'):
        _iddia(metin.count(parca) == 1 and parca in govde, f"{parca!r} betikte {metin.count(parca)} kez / gövdede değil")
    for dal in ("vault_rotasyon", "vault_db_rotasyon", "vault_cp_rotasyon"):
        n = len(re.findall(r"^\s*_kasa_surumu\s", v521._fonksiyon(dal), re.M))
        _iddia(n == 1, f"{dal}: `_kasa_surumu` {n} kez çağrılıyor (1 bekleniyordu)")


# =================================================================================================
# B) KURU — plan satırı
# =================================================================================================

KURU_ALTLAR = {"kapi": ["secret/meridian/kapi_apikey"], "tenant": [TENANT_YOLU], "dash": ["secret/meridian/dash_token"],
               "apisix-admin": ["secret/meridian/apisix_admin_key"], "openrouter": [NOUS_YOLU, LLM_YOLU]}


def _kuru_ihlalleri(r: subprocess.CompletedProcess, log: pathlib.Path, yollar: list[str]) -> list[str]:
    ih = []
    if r.returncode != 0:
        ih.append(f"çıkış {r.returncode}")
    satirlar = r.stdout.splitlines()
    yazilacak = [i for i, s in enumerate(satirlar) if s.startswith("  kasaya yazılacak : ")]
    if [satirlar[i].split()[3] for i in yazilacak] != yollar:
        ih.append(f"kasaya yazılacak yollar {[satirlar[i].split()[3] for i in yazilacak]} ≠ {yollar}")
    for i in yazilacak:
        yol = satirlar[i].split()[3]
        if i + 1 >= len(satirlar) or not satirlar[i + 1].startswith(KURU_SATIRI.format(yol=yol)):
            ih.append(f"'kasaya yazılacak : {yol}' satırını 'ÖNCE current_version kaydedilir' satırı İZLEMİYOR")
    if sum("ÖNCE current_version kaydedilir" in s for s in satirlar) != len(yollar):
        ih.append("current_version satırı sayısı kasa yolu sayısına eşit değil")
    if log.exists():
        ih.append("kuru koşum kasaya çağrı yaptı")
    return ih


@pytest.mark.parametrize("alt", sorted(KURU_ALTLAR))
def test_B1_KURU_her_kasa_yolu_icin_ONCE_current_version_satiri_KASAYA_cagri_YOK(tmp_path, alt):
    kok, ortam, log, durum = _dunya(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, f"--{alt}", "--vault", "--kuru")
    ih = _kuru_ihlalleri(r, log, KURU_ALTLAR[alt])
    if _dosya_imzalari(kok) != once:
        ih.append("kuru koşum dosya yazdı")
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# C) GERÇEK KOŞUM
# =================================================================================================

def _kos_tenant(tmp_path: pathlib.Path, kip: str = "uret", betik: pathlib.Path = BETIK, **bayrak: str):
    kok, ortam, log, durum = _dunya(tmp_path, **bayrak)
    if kip == "uret":
        r = _kos(betik, ortam, "--tenant", "--vault", "--uret")
    else:
        r = _kos(betik, ortam, "--tenant", "--vault", girdi="SAHTE-ISTEM-0561\n")
    return r, kok, ortam, log, durum


def _tenant_basari_ihlalleri(r, kok, log, durum) -> list[str]:
    ih = []
    if r.returncode != 0:
        ih.append(f"çıkış {r.returncode} (0 bekleniyordu)")
    ol = v556._olaylar(kok)
    meta = [i for i, o in enumerate(ol) if o == f"kv-metadata {TENANT_YOLU}"]
    put = [i for i, o in enumerate(ol) if o.startswith(f"kv-put {TENANT_YOLU} ")]
    if len(meta) != 1:
        ih.append(f"kiracı yolunda metadata okuması {len(meta)} kez (1 bekleniyordu)")
    if len(put) != 1:
        ih.append(f"kiracı yoluna put {len(put)} kez")
    if meta and put and meta[0] > put[0]:
        ih.append("metadata put'tan SONRA okundu")
    if any(TAKMA_TENANT in o for o in ol):
        ih.append("takma adın (hindsight_cp_dataplane_api_key) yoluna kasa çağrısı — sürüm BİRİNCİL yoldan okunur")
    if SURUM_OLDU.format(n=2) not in r.stdout.splitlines():
        ih.append("stdout'ta 'kasa sürümü (yazım ÖNCESİ): 2' satırı yok")
    if len(_kasa(durum, TENANT_YOLU)) != 3:
        ih.append(f"kasada {len(_kasa(durum, TENANT_YOLU))} sürüm (3 bekleniyordu)")
    ih += _recete_ihlalleri(r, [(TENANT_YOLU, 2)])
    return ih


@pytest.mark.parametrize("kip", ["uret", "istem"])
def test_C1_BASARI_metadata_yazimdan_ONCE_surum_DOGRU_recete_KASA_ONCE(tmp_path, kip):
    """Başarıda da reçete basılır (başarıda da arızada da geçerli). Sürüm yazım ÖNCESİ `current_version`dır
    (tohum 2 → 2; "bir önceki" 1 ya da "yazım sonrası" 3 değil) ve TAKMA ADIN değil birincilin yolundan okunur."""
    r, kok, _, log, durum = _kos_tenant(tmp_path, kip)
    ih = _tenant_basari_ihlalleri(r, kok, log, durum)
    # Değer hiçbir yüzeyde yok (v557 `_sizinti`: stdout · stderr · şim günlükleri · kasa argv; değer + sha8).
    ih += v557._sizinti(r, kok, log, _kasa(durum, TENANT_YOLU)[-1], ESKI["tenant"], ONCEKI_TENANT, "SAHTE-ISTEM-0561")
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def _render_yok_ihlalleri(r, kok, ortam, durum) -> list[str]:
    ih = []
    if r.returncode != 2:
        ih.append(f"çıkış {r.returncode} (render aşımı → 2 bekleniyordu)")
    if len(_kasa(durum, TENANT_YOLU)) != 3:
        ih.append("put kasaya ulaşmadı — sahne kurulamadı")
    ih += _recete_ihlalleri(r, [(TENANT_YOLU, 2)])
    return ih


def test_C2_RENDER_ASIMI_recete_rollback_DOSYADAN_ONCE_ve_IZLENINCE_kasa_ESKI_degerde(tmp_path):
    """Bulgunun kendisi: kasa YENİ değerde, render gelmedi → çıkış 2. Reçetenin kasa satırı YÜRÜTÜLÜR (sahte
    kasada, yazıldığı gibi) ve kasadaki güncel değer yazım ÖNCESİ değer olur — "doğru sürüm" iddiası ölçülür."""
    r, kok, ortam, log, durum = _kos_tenant(tmp_path, SAHTE_RENDER="yok")
    ih = _render_yok_ihlalleri(r, kok, ortam, durum)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))
    satir = next(s for s in _recete(r.stderr) if "vault kv rollback" in s)
    arg = satir.split()[1:]            # kv rollback -version=N <yol>
    y = subprocess.run([ortam["VAULT_BIN"], *arg], capture_output=True, text=True, env=ortam)
    _iddia(y.returncode == 0, "reçetenin kasa satırı sahte kasada koşmadı")
    _iddia(_kasa(durum, TENANT_YOLU)[-1] == ESKI["tenant"], "reçete izlenince kasa yazım ÖNCESİ değere DÖNMEDİ")


def test_C3_PUT_DUSERSE_de_recete_o_yolu_GERI_ALIR(tmp_path):
    """Put düşse bile kasaya ulaşmış OLABİLİR (`--db`/`--cp` emsali: evre yazımdan ÖNCE `kasa`). Ulaşmadıysa
    `rollback -version=<o sürüm>` aynı değeri yeni sürüm yazar — zararsız; atlamak ise ulaştıysa YANLIŞ güvence."""
    r, kok, ortam, log, durum = _kos_tenant(tmp_path, SAHTE_PUT_IZIN="0")
    ih = []
    if r.returncode != 1 or f"kasaya yazılamadı: {TENANT_YOLU}" not in r.stderr:
        ih.append(f"çıkış {r.returncode} / 'kasaya yazılamadı' yok")
    ih += _recete_ihlalleri(r, [(TENANT_YOLU, 2)])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def _iki_sir_ihlalleri(r, log, durum) -> list[str]:
    """`--openrouter --vault`: NOUS döner, OPENROUTER'ın (LLM birincil yolu) sürümü geçersiz → durur."""
    ih = []
    beklenen = GECERSIZ.format(v="0", yol=LLM_YOLU, neden=IKINCI_SIR)
    if r.returncode != 1:
        ih.append(f"çıkış {r.returncode} (1 bekleniyordu)")
    if beklenen not in r.stderr.splitlines():
        ih.append("ikinci sırrın hata satırı 'bu sır YAZILMADI; … ÖNCE yazılan kasa yolu VAR' demiyor")
    if HICBIR in r.stderr:
        ih.append("'HİÇBİR ŞEY yazılmadı' dendi — ilk sır (NOUS) kasada, beyan YALAN")
    if _putlar(log) != [NOUS_YOLU]:
        ih.append(f"put yolları {_putlar(log)} ≠ [{NOUS_YOLU}]")
    if len(_kasa(durum, LLM_YOLU)) != 3:
        ih.append("LLM yolu değişti")
    ih += _recete_ihlalleri(r, [(NOUS_YOLU, 2)], yok=(LLM_YOLU, TAKMA_OR))
    return ih


def test_C4_IKI_SIRLI_TUR_ikinci_sir_duserse_ILK_sir_GERI_ALINIR_metin_DOGRU(tmp_path):
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA="sifir", SAHTE_METADATA_YOL=LLM_YOLU)
    r = _kos(BETIK, ortam, "--openrouter", "--vault", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    ih = _iki_sir_ihlalleri(r, log, durum) + v557._sizinti(r, kok, log, YENI_NOUS, YENI_OR, ESKI["nous"])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C5_IKI_SIRLI_TUR_basari_IKI_yol_KENDI_surumuyle_TAKMA_AD_yolu_YOK(tmp_path):
    """Takma ad (`openrouter_api_key`) birincilin yoluna çözülür: sürüm ve geri alma O yoldadır (3), NOUS 2."""
    kok, ortam, log, durum = _dunya(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", "--vault", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    ih = [] if r.returncode == 0 else [f"çıkış {r.returncode}"]
    ol = v556._olaylar(kok)
    for yol in (NOUS_YOLU, LLM_YOLU):
        if (f"kv-metadata {yol}" not in ol
                or ol.index(f"kv-metadata {yol}") > min(i for i, o in enumerate(ol) if o.startswith(f"kv-put {yol} "))):
            ih.append(f"{yol}: metadata put'tan ÖNCE okunmadı")
    if any(TAKMA_OR in o for o in ol):
        ih.append("takma adın yoluna kasa çağrısı")
    ih += _recete_ihlalleri(r, [(NOUS_YOLU, 2), (LLM_YOLU, 3)], yok=(TAKMA_OR,))
    ih += v557._sizinti(r, kok, log, YENI_NOUS, YENI_OR, ESKI["nous"], ESKI["or"])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# D) ÖN KAPI — okunamaz / geçersiz sürüm → kasaya yazım YOK
# =================================================================================================

def _yedeksiz(imza: dict) -> dict:
    return {k: v for k, v in imza.items() if "/root/sir-yedek-" not in k}


def _on_kapi_ihlalleri(r, kok, log, durum, once, sinif, surum, yol=TENANT_YOLU,
                       kasa_beklenen: list[str] | None = None) -> list[str]:
    ih = []
    kasa_beklenen = TOHUM.get(yol, []) if kasa_beklenen is None else kasa_beklenen
    if r.returncode != 1:
        ih.append(f"çıkış {r.returncode} (1 bekleniyordu)")
    beklenen = (OKUNAMADI.format(yol=yol, neden=HICBIR) if sinif == "okunamadi"
                else GECERSIZ.format(v=surum, yol=yol, neden=HICBIR))
    if beklenen not in r.stderr.splitlines():
        ih.append(f"açık hata satırı yok ({sinif})")
    if _putlar(log):
        ih.append(f"kasaya YAZILDI: {_putlar(log)}")
    if _kasa(durum, yol) != kasa_beklenen:
        ih.append("kasa değişti")
    if _yedeksiz(_dosya_imzalari(kok)) != _yedeksiz(once):
        ih.append("yedek dışında dosya yazıldı")
    if v556._restartlar(kok):
        ih.append("birim yeniden başlatıldı")
    rec = _recete(r.stderr)
    if not rec or GEREKMEZ not in rec[0]:
        ih.append("reçete 'GEREKMEZ' demiyor (kasaya da dosyaya da yazılmadı)")
    if any("kv rollback" in s or DOSYA_ADIMI in s for s in rec):
        ih.append("yazılmamış koşumda geri alma adımı önerildi")
    return ih


@pytest.mark.parametrize("kip,sinif,surum", KIPLER, ids=[k[0] for k in KIPLER])
def test_D1_SURUM_okunamaz_ya_da_GECERSIZ_ise_kasaya_YAZIM_YOK_acik_hata(tmp_path, kip, sinif, surum):
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA=kip)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    ih = _on_kapi_ihlalleri(r, kok, log, durum, once, sinif, surum)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_D2_YOL_YOK_ilk_yazim_DURUR_db_cp_ile_AYNI(tmp_path):
    """Kasa yolu hiç yazılmamış (v556 şiminin modeli: meta yok → current_version 0). Genel döngü bunu BAĞLAMA
    sayar ve durur — `--db`/`--cp` dalları bu hâlde de kasaya hiçbir şey yazmadan durur."""
    kok, ortam, log, durum = _dunya(tmp_path)
    veri = json.loads(durum.read_text(encoding="utf-8"))
    del veri[TENANT_YOLU]
    durum.write_text(json.dumps(veri), encoding="utf-8")
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    ih = _on_kapi_ihlalleri(r, kok, log, durum, once, "gecersiz", "0", kasa_beklenen=[])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# E) db/cp BİREBİR — ortak yardımcı ↔ taban satır içi blok
# =================================================================================================
# TABAN (e0e54f1c, 2026-09-26): iki dal sürümü KENDİ satır içi bloğuyla okuyordu. Bu dilim onu `_kasa_surumu`ya
# çıkardı. İz kıyası: bugünkü betik ile yardımcı çağrısının yerine TABAN bloğu geri konmuş kopyası AYNI dünyada
# AYNI senaryoyla koşar; çıkış, stdout, stderr, olay sırası, kasa argv'si ve dosya durumları BİREBİR olmalı.

TABAN_BLOK = '''  {V}="$(_vault kv metadata get -format=json "$yol" \\
    | "$PYTHON_BIN" -c 'import json, sys; print(int(json.load(sys.stdin)["data"]["current_version"]))')" \\
    || die "kasa sürümü okunamadı ($yol) — geri alma hedefi bilinmeden kasaya YAZILMAZ (HİÇBİR ŞEY yazılmadı)"
  case "${V}" in
    ''|*[!0-9]*|0) die "kasa sürümü geçersiz: '${V}' ($yol) — kasaya HİÇBİR ŞEY yazılmadı" ;;
  esac
  oldu "kasa sürümü (yazım ÖNCESİ): ${V} — geri alma: vault kv rollback -version=${V}"
'''
YARDIMCI_CAGRISI = '  _kasa_surumu "$yol" "HİÇBİR ŞEY yazılmadı"\n  {V}="$KASA_SURUM"\n'


def _taban_betik(tmp_path: pathlib.Path) -> pathlib.Path:
    ciftler = [(YARDIMCI_CAGRISI.replace("{V}", v), TABAN_BLOK.replace("{V}", v)) for v in ("DB_KASA_SURUM", "CP_KASA_SURUM")]
    return v556._mutant(tmp_path, *ciftler, ad="taban_v561.sh")


def _dunya_db(dizin: pathlib.Path, **bayrak: str):
    kok, ortam, log, durum = v538._db_ortami(dizin)
    ortam = dict(_sarmala(dizin, ortam), VAULT_POLITIKA_URETICI=str(v556.URETICI))
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _dunya_cp(dizin: pathlib.Path, **bayrak: str):
    kok, ortam, log, durum = v556._cp_ortami(dizin)
    ortam = _sarmala(dizin, ortam)
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _iz(betik: pathlib.Path, dizin: pathlib.Path, dal: str, bayrak: dict) -> dict:
    dizin.mkdir()
    kok, ortam, log, durum = (_dunya_db if dal == "db" else _dunya_cp)(dizin, **bayrak)
    once = v557._agac(kok)
    if dal == "db":
        r = _kos(betik, ortam, "--db", "--vault", girdi=f"{v538.YENI_PG}\n")
    else:
        r = _kos(betik, ortam, "--cp", "--vault")
    sonra = v557._agac(kok)

    def norm(m: str) -> str:
        return v557._norm(m.replace(str(betik), "<BETIK>"), dizin)

    dosyalar = {v557._norm(rel, dizin): ("YENİ" if rel not in once else "SİLİNDİ" if rel not in sonra
                                         else "AYNI" if once[rel] == sonra[rel] else "DEĞİŞTİ")
                for rel in sorted(set(once) | set(sonra))}
    return {"rc": r.returncode, "stdout": norm(r.stdout), "stderr": norm(r.stderr), "olaylar": v556._olaylar(kok),
            "kasa_argv": norm(log.read_text(encoding="utf-8")) if log.exists() else None, "dosyalar": dosyalar}


E_SENARYO = (("db_basari", "db", {}, 0, "  ✓ kasa sürümü (yazım ÖNCESİ): 3 — geri alma: vault kv rollback -version=3"),
             ("db_yok", "db", {"SAHTE_METADATA": "yok"}, 1,
              OKUNAMADI.format(yol=v538.DB_KASA, neden=HICBIR)),
             ("cp_basari", "cp", {}, 0, "  ✓ kasa sürümü (yazım ÖNCESİ): 2 — geri alma: vault kv rollback -version=2"),
             ("cp_sifir", "cp", {"SAHTE_METADATA": "sifir"}, 1,
              GECERSIZ.format(v="0", yol=v556.KASA_YOLU, neden=HICBIR)))


@pytest.mark.parametrize("etiket,dal,bayrak,rc,capa", E_SENARYO, ids=[e[0] for e in E_SENARYO])
def test_E1_DB_CP_ortak_yardimci_TABAN_satir_ici_blokla_BIREBIR_iz(tmp_path, etiket, dal, bayrak, rc, capa):
    """Çıkarımın kanıtı. Kıyas boş değil: iki izde de beklenen çıkış kodu ve sürüm satırı (başarı: `oldu`; arıza:
    açık hata) VAR — yani iki betik de sürüm kapısına ULAŞTI."""
    taban = _taban_betik(tmp_path)
    a = _iz(BETIK, tmp_path / "yeni", dal, bayrak)
    b = _iz(taban, tmp_path / "taban", dal, bayrak)
    for k in ("rc", "stdout", "stderr", "olaylar", "kasa_argv", "dosyalar"):
        _iddia(a[k] == b[k], _maskeli(f"{etiket}: {k} ayrıştı\nyeni={a[k]}\ntaban={b[k]}"))
    _iddia(a["rc"] == rc, f"{etiket}: çıkış {a['rc']} ({rc} bekleniyordu)")
    _iddia(capa in (a["stdout"] + a["stderr"]).splitlines(), _maskeli(f"{etiket}: sürüm satırı yok\n{a['stdout']}\n{a['stderr']}"))


# =================================================================================================
# F) KASASIZ ESKİ YOL — reçete DEĞİŞMEDİ
# =================================================================================================

def test_F1_VAULTSUZ_eski_yol_recetesi_AYNEN_kasa_satiri_YOK(tmp_path):
    """`--tenant` (kasasız eski yol) reçetesi bu dilimden ÖNCEKİ üç satırın AYNISI (v538 Ç7'nin eski `--db`
    altın izindeki biçim); kasa/rollback/evre metni yok."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(r.returncode == 0, _ozet(r))
    rec = _recete(r.stderr)
    yedek = sorted((kok / "root").glob("sir-yedek-*-tenant"))
    _iddia(len(yedek) == 1, f"yedek dizini sayısı {len(yedek)}")
    beklenen = [">> GERİ ALMA (bu koşum YEDEK aldı — başarıda da arızada da geçerli):",
                f"     sudo cp -p {yedek[0]}/<yol> /<yol>   (yedek ağacı üretim yollarını AYNEN taşır)",
                f"     sonra yeniden başlat: {TENANT_BIRIMLER}"]
    _iddia(rec == beklenen, _maskeli("reçete değişti:\n" + "\n".join(rec)))
    _iddia("kv rollback" not in r.stderr and "kasa sürümü" not in r.stdout, _ozet(r))


# =================================================================================================
# M) MUTASYONLAR — mutant tmp'ye yazılır, özgün betik DEĞİŞMEZ
# =================================================================================================

SURUM_CAGRISI = '    _kasa_surumu "$yol" "$yazilmadi"\n'
RECETE_KV = '          echo "        vault kv rollback -version=$surum $yol"\n'
RECETE_KASA_BASI = '        echo "     1) kasa (yönetici jetonuyla)'
RECETE_DOSYA = '        echo "     3) eski kanal: sudo cp -p $YEDEK/<yol> /<yol>   (yedek ağacı üretim yollarını AYNEN taşır; render hedefi 1–2 ile kasadan döner)"\n'
GECERSIZ_KAPI = "    ''|*[!0-9]*|0) die \"kasa sürümü geçersiz:"
KURU_ECHO = '    echo "  kasa sürümü      : ÖNCE current_version'
IKINCI_METIN = '    [ -z "$GENEL_KASA_SATIRLARI" ] || yazilmadi='
EVRE_SATIRLARI = ('    GENEL_KASA_SATIRLARI="$GENEL_KASA_SATIRLARI$yol"$\'\\t\'"$KASA_SURUM"$\'\\t\'"$hedef"$\'\\n\'\n'
                  "    GENEL_KASA_EVRE=kasa\n")
GENEL_PUT_DIE = '      || die "kasaya yazılamadı: $yol"\n'


def _mutant(tmp_path: pathlib.Path, ad: str, *ciftler) -> pathlib.Path:
    return v556._mutant(tmp_path, *ciftler, ad=ad)


def test_M1_MUT_surum_OKUMASI_kalkarsa_C1_ve_D1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m1.sh", (SURUM_CAGRISI, "    :\n"))
    (tmp_path / "c1").mkdir()
    r, kok, _, log, durum = _kos_tenant(tmp_path / "c1", betik=m)
    ih = _tenant_basari_ihlalleri(r, kok, log, durum)
    _iddia(any("metadata okuması 0 kez" in i for i in ih) and any("kv rollback -version=2" in i for i in ih),
           "MUTASYON ISIRMADI (C1): " + "\n".join(ih))
    (tmp_path / "d1").mkdir()
    kok, ortam, log, durum = _dunya(tmp_path / "d1", SAHTE_METADATA="sifir")
    once = _dosya_imzalari(kok)
    r = _kos(m, ortam, "--tenant", "--vault", "--uret")
    ih = _on_kapi_ihlalleri(r, kok, log, durum, once, "gecersiz", "0")
    _iddia(any(i.startswith("kasaya YAZILDI") for i in ih), "MUTASYON ISIRMADI (D1): " + "\n".join(ih))


def test_M2_MUT_recetede_KV_satiri_kalkarsa_C1_ve_C2_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m2.sh", (RECETE_KV, "          :\n"))
    (tmp_path / "c1").mkdir()
    r, kok, _, log, durum = _kos_tenant(tmp_path / "c1", betik=m)
    _iddia(any("kv rollback -version=2" in i for i in _tenant_basari_ihlalleri(r, kok, log, durum)), "MUTASYON ISIRMADI (C1)")
    (tmp_path / "c2").mkdir()
    r, kok, ortam, log, durum = _kos_tenant(tmp_path / "c2", betik=m, SAHTE_RENDER="yok")
    _iddia(any("kv rollback -version=2" in i for i in _render_yok_ihlalleri(r, kok, ortam, durum)), "MUTASYON ISIRMADI (C2)")


def test_M3_MUT_recete_SIRASI_ters_donerse_C2_KIRMIZI(tmp_path):
    """Dosya adımı kasa adımının ÖNÜNE alınır (bulgunun tam hâli: önce dosya, sonra kasa → render dosyayı ezer)."""
    m = _mutant(tmp_path, "m3.sh", (RECETE_DOSYA, ""), (RECETE_KASA_BASI, RECETE_DOSYA + RECETE_KASA_BASI))
    (tmp_path / "c2").mkdir()
    r, kok, ortam, log, durum = _kos_tenant(tmp_path / "c2", betik=m, SAHTE_RENDER="yok")
    ih = _render_yok_ihlalleri(r, kok, ortam, durum)
    _iddia(any("DOSYA adımından SONRA" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


@pytest.mark.parametrize("kip,surum", [("sifir", "0"), ("eksi", "-1")])
def test_M4_MUT_GECERSIZ_surum_kapisi_kalkarsa_D1_KIRMIZI(tmp_path, kip, surum):
    m = _mutant(tmp_path, "m4.sh", (GECERSIZ_KAPI, GECERSIZ_KAPI.replace(" die ", " : ", 1)))
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA=kip)
    once = _dosya_imzalari(kok)
    r = _kos(m, ortam, "--tenant", "--vault", "--uret")
    ih = _on_kapi_ihlalleri(r, kok, log, durum, once, "gecersiz", surum)
    _iddia(any(i.startswith("kasaya YAZILDI") for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M5_MUT_KURU_satiri_kalkarsa_B1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m5.sh", (KURU_ECHO, KURU_ECHO.replace("    echo ", "    : ", 1)))
    kok, ortam, log, _ = _dunya(tmp_path)
    r = _kos(m, ortam, "--tenant", "--vault", "--kuru")
    ih = _kuru_ihlalleri(r, log, [TENANT_YOLU])
    _iddia(any("İZLEMİYOR" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M6_MUT_ikinci_sirda_HICBIR_SEY_derse_C4_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m6.sh", (IKINCI_METIN, IKINCI_METIN.replace('[ -z "$GENEL_KASA_SATIRLARI" ]', "true", 1)))
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA="sifir", SAHTE_METADATA_YOL=LLM_YOLU)
    r = _kos(m, ortam, "--openrouter", "--vault", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    ih = _iki_sir_ihlalleri(r, log, durum)
    _iddia(any("YALAN" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M7_MUT_evre_yazimdan_SONRA_kurulursa_C3_KIRMIZI(tmp_path):
    """Satır + evre put'tan SONRAya alınır: put düşünce reçete 'GEREKMEZ' der — kasaya ulaşmış olabilecek bir
    yazımı geri almadan bırakır."""
    m = _mutant(tmp_path, "m7.sh", (EVRE_SATIRLARI, ""), (GENEL_PUT_DIE, GENEL_PUT_DIE + EVRE_SATIRLARI))
    r, kok, ortam, log, durum = _kos_tenant(tmp_path, betik=m, SAHTE_PUT_IZIN="0")
    ih = _recete_ihlalleri(r, [(TENANT_YOLU, 2)])
    _iddia(any("GEREKMEZ" in i or "kv rollback -version=2" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))
