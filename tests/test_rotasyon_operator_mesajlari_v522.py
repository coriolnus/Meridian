"""test_rotasyon_operator_mesajlari_v522.py — TSK-064 takip (2)(4)(5): rotasyon aracı operatöre DOĞRU
şeyi söyler (2026-09-17). DAVRANIŞ DEĞİŞMEZ — yalnız basılan uyarı/beyan metinleri.

(2) ESKİ YOL + KASAYA BAĞLI SIR. Dalga-1 bağından (v521) sonra altı rotasyon sırrının altısı da
    kasaya BAĞLI, ama `--kapi`/`--tenant`/`--dash`/`--openrouter`/`--apisix-admin` `--vault`
    VERİLMEDEN koşunca eski yol Vault Agent'ın render ettiği credential kaynağına DOĞRUDAN yazıyor ve
    hiçbir şey söylemiyordu. Hipotez (ROADMAP TSK-064 14:2xZ, A1'de ÖLÇÜLMEDİ): Agent render
    aralığında kasadaki ESKİ değeri geri yazar. Uyarı artık yazımdan (kuru koşumda plandan) ÖNCE,
    sır adı + hedef dosya + render aralığı (`ops/vault_politika_uret.py::RENDER_ARALIGI`, UYDURULMAZ)
    + doğru yol (`--<alt> --vault`) ile basılır. Tespit yolu `--db`nin mevcut uyarısıyla TEK
    (`_agent_hedefleri`); `--db` metni AYNEN kalır.
(4) KASA YOLU DEĞERİ ÜRETMEZ. `--dash`/`--apisix-admin`/`--kapi`/`--tenant` eski yolda değeri betik
    İÇİNDE üretir; `--vault` sizden ister. İstem noktası ve kuru plan bunu söyler — değer ya da
    örnek değer basmadan.
(5) NOUS `api` KOPYASI. Kasa akışı motor deposunu restart ve kanıttan ÖNCE yazar; `_api_yaz`ın hata
    metni ("Rotasyon KANITLANDI") orada YANLIŞTI. Metin artık akışa göre; eski yolunki AYNEN.

BÖLÜMLER
  A  (2) eski yol uyarısı — bağlı sırlar · render aralığı tek kaynaktan · `--db` aynen
  B  (4) değer kaynağı beyanı — kuru plan · istem noktası · `_uret` kümesiyle ayrışma çivisi
  C  (5) `_api_yaz` hata metni akışa göre (motor deposu yazımı düşürülür)
  D  davranış değişmezliği — "mesajsız eş" ile iz kıyası · kuru koşum hiçbir şey yazmaz
  M  MUTASYONLAR — her çivinin hedeflediği dalı ısırdığı

SIR DEĞERİ YOK: her değer `SAHTE-` önekli ve sahtedir (v447/v521 tohumları).
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

import pytest
import yaml

from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_sir_rotasyon_v447 import BETIK, ENVANTER, ESKI, _kos, _mutant

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
URETICI = KOK_DEPO / "ops" / "vault_politika_uret.py"

#: KASAYA BAĞLI sırların eski yolda Agent RENDER HEDEFİNE yazan kopyaları — ELLE durur (v521 BAGLAR
#: gerekçesi: envanterden türetilseydi bir hedef envanterden düştüğünde çivi de onunla küçülürdü).
#: A1b bu tablonun envanterle hâlâ uyuştuğunu AYRICA ölçer (bayat tablo sessiz kalmasın).
BAGLI_HEDEFLER = {
    "kapi": {("KAPI_APIKEY", "/etc/meridian/kapi_apikey")},
    "tenant": {("HINDSIGHT_API_TENANT_API_KEY", "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY")},
    "dash": {("MERIDIAN_DASH_TOKEN", "/etc/meridian/dash_token")},
    "apisix-admin": {("APISIX_ADMIN_KEY", "/etc/meridian/apisix_admin_key")},
    "openrouter": {("NOUS_API_KEY", "/etc/meridian/nous_api_key"),
                   ("OPENROUTER_API_KEY", "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY")},
}
#: Eski yolun değeri betik İÇİNDE ürettiği alt komutlar (`_uret`) — ELLE. B3 bu kümeyi betiğin
#: fonksiyon gövdelerinden ve `_deger_kaynagi_beyani`nin ölçülen davranışından AYRICA türetir.
DEGER_URETEN = {"kapi", "tenant", "db", "dash", "apisix-admin"}

BAGLI_SINIF = "sır kasaya BAĞLI (bu ESKİ yol)"
BAGSIZ_SINIF = "kasaya BAĞLI DEĞİL"
BASLIK_RE = re.compile(r"^  !! UYARI — VAULT AGENT RENDER HEDEFİ, (?P<sinif>.+?): "
                       r"(?P<sir>[A-Z_]+) → (?P<yol>\S+)$", re.M)
DEGER_KAYNAGI = "DEĞER KAYNAĞI: bu yol değeri ÜRETMEZ, sizden İSTER"

#: `--db --kuru` uyarısı — bu dilimden ÖNCEKİ çıktının BİREBİR kopyası (brief madde 3: "aynen").
DB_BLOK = (
    "  !! UYARI — VAULT AGENT RENDER HEDEFİ, kasaya BAĞLI DEĞİL: HINDSIGHT_DB_PAROLA → "
    "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL\n"
    "     kasa yolu: secret/meridian/HINDSIGHT_API_DATABASE_URL (vault_kv.HINDSIGHT_API_DATABASE_URL)\n"
    "     Eski yolun yazımı kasadaki ESKİ değerle EZİLEBİLİR (Agent render aralığında; A1'de\n"
    "     ÖLÇÜLMEDİ). Eski yol YİNE DE KOŞAR — uyarı, kapı değil.\n"
    "     Kasadaki değer rotasyonla AYNI pencerede elle güncellenmeli (değer STDIN'den, BASILMADAN:\n"
    "     vault kv put secret/meridian/HINDSIGHT_API_DATABASE_URL value=-) ve render ölçülmeli "
    "(dosya kasadaki yeni değere eşit mi).\n"
    "     Sıra (yazım ↔ kasa ↔ render) bu betikte TASARLANMADI.\n"
)

#: `_api_yaz` eski yol hata metni — bu dilimden ÖNCEKİ metnin BİREBİR kopyası (brief madde 5).
ESKI_API_METNI = (
    "!! motor API yazımı başarısız (HTTP 500): /api/secrets/NOUS_API_KEY (NOUS_API_KEY)\n"
    "     Rotasyon KANITLANDI ve credential kanalı yeni değeri taşıyor; başarısız olan YALNIZ motorun\n"
    "     kendi deposundaki kopya. O depo `secrets._fetch`in ÜÇÜNCÜ basamağıdır (credential ilk), yani\n"
    "     motor bugün doğru çalışır — ama depoda ESKİ değer kalır ve credential bir gün boşalırsa\n"
    "     motor sessizce ona düşer. Elle eşitle: pano → sır girişi, ya da /api/secrets/NOUS_API_KEY.\n"
)
API_HATA_BASI = "!! motor API yazımı başarısız (HTTP 500): /api/secrets/NOUS_API_KEY (NOUS_API_KEY)"

#: Motor deposuna YAZMAYI (POST) düşüren curl sarmalayıcısı — silme (DELETE) ve öteki her uç v447
#: şimine aynen gider. Motorun TAMAMINI öldüren `SAHTE_MOTOR_OLU` burada işe yaramaz: eski yol depo
#: yazımından ÖNCE aynı motorda negatif kontrol ve varlık kanıtı koşar.
SIM_API_BOZUK = '''#!/usr/bin/env python3
import os, re, sys
a = sys.argv[1:]
with open(a[a.index("-K") + 1], encoding="utf-8") as fh:
    cfg = fh.read()
m = re.search(r'^url = "(.*)"$', cfg, re.M)
if m and m.group(1).endswith("/api/secrets/NOUS_API_KEY") and 'request = "DELETE"' not in cfg:
    sys.stdout.write("500")
    sys.exit(0)
os.execv(__ASIL__, [__ASIL__] + a)
'''


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _render_araligi() -> str:
    """Tek kaynak: üreticinin KENDİ sabiti (v491 B5 ile aynı yükleyici) — çivide ikinci kopya yok."""
    from tests.conftest import betikten_modul_yukle
    return betikten_modul_yukle(URETICI, "vault_politika_uret").RENDER_ARALIGI


def _ortam(tmp_path: pathlib.Path, *, uretici: pathlib.Path | None = None,
           api_bozuk: bool = False) -> tuple[pathlib.Path, dict, pathlib.Path]:
    """v521 sahte kök + sahte kasa. `uretici` VERİLMEZSE betik render aralığını KENDİ yolundan
    türetir (operatörün koşacağı biçim); tmp'deki mutantlar için açıkça verilir."""
    kok, ortam, log = v521._kasa_ortami(tmp_path)
    ortam.pop("VAULT_POLITIKA_URETICI", None)
    if uretici is not None:
        ortam["VAULT_POLITIKA_URETICI"] = str(uretici)
    if api_bozuk:
        binn = tmp_path / "bin_v522"
        binn.mkdir()
        asil = tmp_path / "bin" / "curl"
        (binn / "curl").write_text(SIM_API_BOZUK.replace("__ASIL__", repr(str(asil))),
                                   encoding="utf-8")
        (binn / "curl").chmod(0o755)
        ortam["PATH"] = f"{binn}:{ortam['PATH']}"
    return kok, ortam, log


def _uyarilar(metin: str) -> list[dict]:
    """Agent hedefi uyarı BLOKLARI: başlık + ardındaki 5 boşluklu devam satırları."""
    satirlar = metin.splitlines()
    out = []
    for i, s in enumerate(satirlar):
        m = BASLIK_RE.match(s)
        if not m:
            continue
        blok = [s]
        for d in satirlar[i + 1:]:
            if not d.startswith("     "):
                break
            blok.append(d)
        out.append(dict(m.groupdict(), blok="\n".join(blok)))
    return out


def _temiz_satirlar(satirlar: list[str], *betikler: pathlib.Path) -> None:
    """Değer/hash basılmaz sözleşmesi YENİ satırlarda: bilinen sahte değerler yok, hash'e benzeyen
    uzun hex yok, örnek değere benzeyen uzun jeton yok (betik yolu çıkarılarak — yol bir değer değil)."""
    for s in satirlar:
        for b in betikler:
            s = s.replace(str(b), "<BETIK>")
        for d in v521.YENILER + tuple(ESKI.values()):
            assert d not in s, f"SIR DEĞERİ basıldı: {s!r}"
        assert not re.search(r"[0-9a-f]{16,}", s), f"hash'e benzeyen dizge basıldı: {s!r}"
        # Değere benzeyen jeton: uzun, harf VE rakam taşır, sabit adı (BÜYÜK HARF) değil. Rakamsız
        # snake_case (`static_secret_render_interval`) bir ad'dır, değer değil.
        jetonlar = [j for j in re.findall(r"[A-Za-z0-9+=_-]{20,}", s)
                    if not j.isupper() and re.search(r"\d", j) and re.search(r"[A-Za-z]", j)]
        assert not jetonlar, f"değere/örnek değere benzeyen jeton basıldı: {jetonlar} · {s!r}"


def _fonksiyon(ad: str, betik: pathlib.Path = BETIK) -> str:
    return v521._fonksiyon(ad, betik)


# =================================================================================================
# A) (2) ESKİ YOL UYARISI — KASAYA BAĞLI SIRLAR
# =================================================================================================

@pytest.mark.parametrize("alt", sorted(BAGLI_HEDEFLER))
def test_A1_ESKI_YOL_KURU_bagli_sirrin_AGENT_HEDEFI_uyarisi_adiyla_ve_VAULT_onerisiyle(tmp_path, alt):
    """Brief 1-2: sır adı + hedef dosya + kasa yolu + render aralığı (tek kaynaktan) + `--vault`
    önerisi; YALNIZ render hedefi olan kopyalar (hermes `.env`, `.env-apisix`, `/opt/hindsight/.key`
    İÇİN UYARI YOK — küme eşitliği); plandan ÖNCE."""
    _, ortam, _ = _ortam(tmp_path)
    r = _kos(BETIK, ortam, f"--{alt}", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    uy = _uyarilar(r.stdout)
    assert {(u["sir"], u["yol"]) for u in uy} == BAGLI_HEDEFLER[alt], r.stdout
    assert all(u["sinif"] == BAGLI_SINIF for u in uy), r.stdout
    aralik = _render_araligi()
    for u in uy:
        assert f"sudo {BETIK} --{alt} --vault" in u["blok"], u["blok"]
        assert f"render eder — aralık: {aralik} (" in u["blok"], u["blok"]
        assert "ÖLÇÜLMEDİ" in u["blok"] and "EZİLEBİLİR" in u["blok"], u["blok"]
        assert re.search(r"kasa yolu: secret/meridian/\S+ \(vault_kv\.\S+\)", u["blok"]), u["blok"]
    assert r.stdout.index("  !! UYARI") < r.stdout.index("=== KURU KOŞUM"), "uyarı plandan SONRA"
    _temiz_satirlar([s for u in uy for s in u["blok"].splitlines()], BETIK)


def test_A1b_BAGLI_HEDEFLER_tablosu_envanterle_BAYAT_DEGIL():
    """Pozitif kontrol: elle tablo hâlâ envanterin gerçeği — her yol bir `vault_kv.hedef`, her sır
    bir `rotasyon_siri` ile bağlı ve kopya tablosunda o alt komutun `dosya` satırı."""
    kv = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]
    hedefler = {g["hedef"] for g in kv if g.get("hedef")}
    bagli = {g["rotasyon_siri"] for g in kv if g.get("rotasyon_siri")}
    tablo = {(k["alt"], k["sir"], k["yol"]) for k in v521._betik_kopyalari()
             if k["tur"] in ("dosya", "url")}
    for alt, ciftler in BAGLI_HEDEFLER.items():
        beklenen = {(s, y) for a, s, y in tablo if a == alt and y in hedefler}
        assert ciftler == beklenen, (alt, sorted(ciftler ^ beklenen))
        assert {s for s, _ in ciftler} <= bagli, (alt, ciftler)


@pytest.mark.parametrize("alt", sorted(BAGLI_HEDEFLER))
def test_A2_KASA_YOLU_KURU_bagli_sir_uyarisi_TASIMAZ(tmp_path, alt):
    """Brief 1: `--<alt> --vault --kuru` doğru yoldur; orada eski yol uyarısı gereksiz."""
    _, ortam, _ = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--vault", f"--{alt}", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert not _uyarilar(r.stdout), r.stdout
    assert "kasa yolunu kullanın" not in r.stdout, r.stdout


@pytest.mark.parametrize("alt,girdi,ilk_yazim", [
    ("dash", "", "yazıldı: /etc/meridian/dash_token"),
    ("openrouter", f"{v521.YENI_NOUS}\n{v521.YENI_OR}\n", "negatif kontrol (NOUS_API_KEY)"),
])
def test_A3_ESKI_YOL_GERCEK_kosum_uyari_YAZIMDAN_ONCE_ve_eski_yol_KESILMEZ(tmp_path, alt, girdi, ilk_yazim):
    kok, ortam, _ = _ortam(tmp_path)
    r = _kos(BETIK, ortam, f"--{alt}", girdi=girdi)
    assert r.returncode == 0, f"eski yol KESİLDİ:\n{r.stdout}\n{r.stderr}"
    assert {(u["sir"], u["yol"]) for u in _uyarilar(r.stdout)} == BAGLI_HEDEFLER[alt], r.stdout
    assert r.stdout.index("  !! UYARI") < r.stdout.index(ilk_yazim), "uyarı yazımdan SONRA basıldı"
    assert v521._birimler(kok), "eski yol yeniden başlatma yapmadı — akış değişti"
    v521._deger_basilmaz(r, kok)


def test_A4_DB_KURU_mevcut_uyari_AYNEN(tmp_path):
    """Brief 3 (regresyon): `--db`nin bağsız uyarısı bayt bayt önceki metin, başlığın hemen ardında,
    planın hemen önünde; bağlı sınıfın hiçbir satırı sızmaz."""
    _, ortam, _ = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert ("=== ROTASYON: Postgres 'hindsight' rol parolası ===\n" + DB_BLOK
            + "=== KURU KOŞUM: --db ") in r.stdout, r.stdout
    assert len(_uyarilar(r.stdout)) == 1, r.stdout
    assert "aralık:" not in r.stdout and "kasa yolunu kullanın" not in r.stdout, r.stdout


def test_A5_RENDER_ARALIGI_UYDURULMAZ_ureticiden_okunur_okunamazsa_OLCULEMEDI(tmp_path):
    """Sayı üreticinin sabitinden gelir: sahte üretici "7m" derse uyarı "7m" der; üretici yoksa
    "ÖLÇÜLEMEDİ" der ve eski yol KESİLMEZ (plan basılır, çıkış 0)."""
    aralik = _render_araligi()
    capa = f'RENDER_ARALIGI = "{aralik}"'
    kaynak = URETICI.read_text(encoding="utf-8")
    assert kaynak.count(capa) == 1, f"üretici çapası yok/tekrarlı (çivi bayat): {capa!r}"
    sahte = tmp_path / "sahte_uretici.py"
    sahte.write_text(kaynak.replace(capa, 'RENDER_ARALIGI = "7m"'), encoding="utf-8")
    (tmp_path / "a").mkdir()
    _, ortam, _ = _ortam(tmp_path / "a", uretici=sahte)
    r = _kos(BETIK, ortam, "--dash", "--kuru")
    assert r.returncode == 0 and "render eder — aralık: 7m (" in r.stdout, r.stdout
    (tmp_path / "b").mkdir()
    _, ortam, _ = _ortam(tmp_path / "b", uretici=tmp_path / "yok.py")
    r = _kos(BETIK, ortam, "--dash", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "render eder — aralık: ÖLÇÜLEMEDİ" in r.stdout and "=== KURU KOŞUM" in r.stdout, r.stdout


def test_A6_TARAMA_YAPILAMAZSA_bagli_alt_komutta_da_OLCULEMEDI_eski_yol_KESILMEZ(tmp_path):
    """Brief: PyYAML/envanter yoksa mevcut "ÖLÇÜLEMEDİ" beyan dalı AYNEN (v521 E4'ün `--db` dalı)."""
    _, ortam, _ = _ortam(tmp_path)
    ortam["VAULT_ENVANTER"] = str(tmp_path / "yok.yaml")
    r = _kos(BETIK, ortam, "--dash", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert ("  !! UYARI ÖLÇÜLEMEDİ — Vault Agent render hedefi taraması yapılamadı" in r.stdout
            and "     --dash kopyalarından biri Agent'ın render hedefi OLABİLİR" in r.stdout), r.stdout
    assert "yeniden başlatılacak: meridian.service" in r.stdout, r.stdout


def _bagsiz_kes(betik: pathlib.Path, alt: str) -> subprocess.CompletedProcess:
    kod = (_fonksiyon("_kopyalar", betik) + _fonksiyon("_agent_hedefleri", betik)
           + _fonksiyon("_bagsiz_agent_hedefleri", betik)
           + 'set -euo pipefail\n_bagsiz_agent_hedefleri "$1"\n')
    return subprocess.run(["bash", "-c", kod, "_", alt], capture_output=True, text=True,
                          env={"PATH": "/usr/bin:/bin", "PYTHON_BIN": sys.executable,
                               "VAULT_ENVANTER": str(ENVANTER)})


def test_A7_KAPSAM_BEYANI_suzgeci_YALNIZ_BAGSIZ_satiri_verir():
    """Tek tespit yolu: kasa kipinin kapsam beyanı `_agent_hedefleri`nin BAGSIZ süzgecidir — bağlı
    `--dash` boş, bağsız `--db` tek satır."""
    r = _bagsiz_kes(BETIK, "dash")
    assert r.returncode == 0 and r.stdout == "", (r.stdout, r.stderr)
    r = _bagsiz_kes(BETIK, "db")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "HINDSIGHT_DB_PAROLA\t/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL\t"
        "secret/meridian/HINDSIGHT_API_DATABASE_URL\tHINDSIGHT_API_DATABASE_URL\tBAGSIZ\tdb"], r.stdout


# =================================================================================================
# B) (4) DEĞER KAYNAĞI BEYANI
# =================================================================================================

@pytest.mark.parametrize("alt", sorted(BAGLI_HEDEFLER))
def test_B1_KASA_KURU_plani_deger_kaynagini_SOYLER_uretmeyen_eski_yolda_SOYLEMEZ(tmp_path, alt):
    _, ortam, _ = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--vault", f"--{alt}", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    satirlar = [s for s in r.stdout.splitlines() if "DEĞER KAYNAĞI" in s]
    assert len(satirlar) == (1 if alt in DEGER_URETEN else 0), r.stdout
    if satirlar:
        assert DEGER_KAYNAGI in r.stdout and f"eski yol (sudo {BETIK} --{alt})" in r.stdout, r.stdout
        i = r.stdout.splitlines().index(satirlar[0])
        _temiz_satirlar(r.stdout.splitlines()[i:i + 2], BETIK)


@pytest.mark.parametrize("alt,girdi,beyan", [
    ("dash", f"{v521.YENI_DASH}\n", True),
    ("apisix-admin", f"{v521.YENI_ADMIN}\n", True),
    ("openrouter", f"{v521.YENI_NOUS}\n{v521.YENI_OR}\n", False),
])
def test_B2_KASA_GERCEK_istem_noktasinda_beyan_ve_DEGER_BASILMAZ(tmp_path, alt, girdi, beyan):
    kok, ortam, log = _ortam(tmp_path)
    r = _kos(BETIK, ortam, "--vault", f"--{alt}", girdi=girdi)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert (DEGER_KAYNAGI in r.stdout) is beyan, r.stdout
    if beyan:
        assert r.stdout.index(DEGER_KAYNAGI) < r.stdout.index("kasaya yazıldı:"), (
            "beyan kasaya yazımdan SONRA basıldı — istem noktasında değil")
    v521._deger_basilmaz(r, kok, log)


def _uret_cagiran_altlar(betik: pathlib.Path = BETIK) -> set[str]:
    """Eski yol fonksiyon GÖVDELERİNDEN türetilir: `_uret` çağıran alt komutlar."""
    out = set()
    for alt in ("kapi", "tenant", "db", "dash", "openrouter", "apisix-admin"):
        if re.search(r"^\s*_uret\s+\w+", _fonksiyon(alt.replace("-", "_"), betik), re.M):
            out.add(alt)
    return out


def _beyan_basan_altlar(betik: pathlib.Path = BETIK) -> set[str]:
    """`_deger_kaynagi_beyani`nin ÖLÇÜLEN davranışı: hangi alt komutta satır basıyor."""
    kod = _fonksiyon("_deger_kaynagi_beyani", betik) + 'for a in "$@"; do [ -z "$(_deger_kaynagi_beyani "$a")" ] || echo "$a"; done\n'
    r = subprocess.run(["bash", "-c", kod, "sir_rotasyon.sh", "kapi", "tenant", "db", "dash",
                        "openrouter", "apisix-admin"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return set(r.stdout.split())


def test_B3_AYRISMA_beyan_kumesi_ESKI_YOLUN_URETTIGI_kumeyle_BIREBIR():
    """Tek-kaynak: beyanın "eski yol üretir" iddiası betiğin kendi `_uret` çağrılarıyla ayrışamaz.
    Eski yola `_uret` eklenir/çıkarılır da beyan listesi güncellenmezse öter."""
    assert _uret_cagiran_altlar() == DEGER_URETEN, _uret_cagiran_altlar()
    assert _beyan_basan_altlar() == DEGER_URETEN, _beyan_basan_altlar()


# =================================================================================================
# C) (5) `_api_yaz` HATA METNİ AKIŞA GÖRE
# =================================================================================================

def test_C1_KASA_AKISI_depo_yazimi_duserse_KANITLANDI_DEMEZ_HENUZ_der_restart_YOK(tmp_path):
    kok, ortam, log = _ortam(tmp_path, api_bozuk=True)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{v521.YENI_NOUS}\n\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert API_HATA_BASI in r.stderr, r.stderr
    assert "KANITLANDI" not in r.stderr, r.stderr
    assert "HENÜZ KOŞMADI" in r.stderr and "rotasyon DOĞRULANMADI" in r.stderr, r.stderr
    assert "sonra meridian.service yeniden başlat" in r.stderr, r.stderr
    assert not v521._birimler(kok), "kasa akışı depo yazımı düşünce restart yaptı — akış değişti"
    v521._deger_basilmaz(r, kok, log)
    i = r.stderr.splitlines().index(API_HATA_BASI)
    _temiz_satirlar(r.stderr.splitlines()[i:i + 6], BETIK)


def test_C2_ESKI_YOL_depo_yazimi_duserse_metin_AYNEN(tmp_path):
    kok, ortam, _ = _ortam(tmp_path, api_bozuk=True)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{v521.YENI_NOUS}\n\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert ESKI_API_METNI in r.stderr, r.stderr
    assert "HENÜZ KOŞMADI" not in r.stderr, r.stderr
    assert "meridian.service" in v521._birimler(kok), "eski yol kanıttan ÖNCE düştü — akış değişti"
    assert "motor kanıtı: /api/secrets/test/nous ok:true" in r.stdout, r.stdout


# =================================================================================================
# D) DAVRANIŞ DEĞİŞMEZLİĞİ
# =================================================================================================
# "MESAJSIZ EŞ": bu dilimin eklediği mesaj çağrıları `:` ile nötrlenmiş betik. İki betik AYNI sahte
# dünyada koşar; çıkış kodu, dosya ağacı (hangi dosya yazıldı/yaratıldı + deterministik içerik),
# systemctl/sudo/curl/kasa çağrı günlükleri BİREBİR aynı olmalı. Çapalar `_mutant`ta doğrulanır:
# bulunamayan çapa sessizce "mesajlı eş" üretmez.

MESAJ_CAGRILARI = (
    ("  _agent_hedefi_uyarisi kapi\n", "  :\n"),
    ("  _agent_hedefi_uyarisi apisix-admin      #", "  :      #"),
    ("  _agent_hedefi_uyarisi tenant            #", "  :            #"),
    ("  _agent_hedefi_uyarisi dash              #", "  :              #"),
    ("  _agent_hedefi_uyarisi openrouter\n", "  :\n"),
    ('  _deger_kaynagi_beyani "$alt"\n  echo "  render bekleme', '  :\n  echo "  render bekleme'),
    ('    _deger_kaynagi_beyani "$alt"          #', "    :          #"),
    ("    YAZIM_AKISI=kasa\n", "    :\n"),
)
LOGLAR = ("kok/.sahte/argv.log", "kok/.sahte/url.log", "kok/.sahte/systemctl.log", "kasa_argv.log")


def _norm(metin: str, dizin: pathlib.Path, betik: pathlib.Path) -> str:
    metin = metin.replace(str(dizin), "<T>").replace(str(betik), "<BETIK>")
    metin = re.sub(r"sir-rot\.[A-Za-z0-9]+", "sir-rot.X", metin)
    return re.sub(r"sir-yedek-\d{8}T\d{6}Z", "sir-yedek-TS", metin)


def _agac(dizin: pathlib.Path) -> dict[str, str]:
    out = {}
    for p in sorted(dizin.rglob("*")):
        rel = p.relative_to(dizin).as_posix()
        if not p.is_file() or rel.split("/")[0] in ("bin", "kasa_bin", "bin_v522") or rel in LOGLAR:
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _iz(betik: pathlib.Path, dizin: pathlib.Path, args: tuple[str, ...], girdi: str = "",
        api_bozuk: bool = False, uretir: bool = False) -> dict:
    """Bir koşumun DAVRANIŞ izi. `uretir`: eski yol değeri rastgele üretir → içerik hash'i yerine
    dosyanın DURUMU (YENİ/DEĞİŞTİ/AYNI/SİLİNDİ) kıyaslanır; hangi dosyaların yazıldığı yine birebir."""
    dizin.mkdir()
    _, ortam, _ = _ortam(dizin, uretici=URETICI, api_bozuk=api_bozuk)
    once = _agac(dizin)
    r = _kos(betik, ortam, *args, girdi=girdi)
    sonra = _agac(dizin)
    dosyalar = {}
    for rel in sorted(set(once) | set(sonra)):
        durum = ("SİLİNDİ" if rel not in sonra else "YENİ" if rel not in once
                 else "AYNI" if once[rel] == sonra[rel] else "DEĞİŞTİ")
        dosyalar[_norm(rel, dizin, betik)] = (durum, None if uretir else sonra.get(rel))
    loglar = {ad: _norm((dizin / ad).read_text(encoding="utf-8"), dizin, betik)
              if (dizin / ad).exists() else None for ad in LOGLAR}
    # Metin kıyası SÜREYE kör olmalı: "render ÖLÇÜLDÜ … (0 s)" / "(1 s)" saniye sınırına düşer.
    def metin(m: str) -> str:
        return re.sub(r"\b\d+ s\b", "N s", _norm(m, dizin, betik))
    return {"rc": r.returncode, "dosyalar": dosyalar, "loglar": loglar,
            "stdout": metin(r.stdout), "stderr": metin(r.stderr)}


def _davranis(iz: dict) -> dict:
    return {k: iz[k] for k in ("rc", "dosyalar", "loglar")}


#: (etiket, argümanlar, girdi, api_bozuk, uretir, metin_farki) — kuru + gerçek, iki akış, iki arıza
#: dalı. `metin_farki`: bu senaryoda yeni mesaj BASILIR mı (False = başarılı `--openrouter --vault`:
#: bağlam ataması koşar ama hiçbir metin değişmez — o da ölçülür).
SENARYOLAR = (
    ("dash_kuru", ("--dash", "--kuru"), "", False, False, True),
    ("openrouter_kuru", ("--openrouter", "--kuru"), "", False, False, True),
    ("dash_gercek", ("--dash",), "", False, True, True),
    ("openrouter_gercek", ("--openrouter",), f"{v521.YENI_NOUS}\n{v521.YENI_OR}\n", False, False, True),
    ("openrouter_api_bozuk", ("--openrouter",), f"{v521.YENI_NOUS}\n\n", True, False, True),
    ("vault_dash", ("--vault", "--dash"), f"{v521.YENI_DASH}\n", False, False, True),
    ("vault_apisix_kuru", ("--vault", "--apisix-admin", "--kuru"), "", False, False, True),
    ("vault_openrouter", ("--vault", "--openrouter"), f"{v521.YENI_NOUS}\n{v521.YENI_OR}\n",
     False, False, False),
    ("vault_openrouter_api_bozuk", ("--vault", "--openrouter"), f"{v521.YENI_NOUS}\n\n", True, False, True),
)


@pytest.mark.parametrize("etiket,args,girdi,api_bozuk,uretir,metin_farki", SENARYOLAR,
                         ids=[s[0] for s in SENARYOLAR])
def test_D1_MESAJSIZ_ES_ile_DAVRANIS_IZI_BIREBIR(tmp_path, etiket, args, girdi, api_bozuk, uretir,
                                                metin_farki):
    es = _mutant(tmp_path, *MESAJ_CAGRILARI, ad="mesajsiz_es.sh")
    yeni = _iz(BETIK, tmp_path / "yeni", args, girdi, api_bozuk, uretir)
    eski = _iz(es, tmp_path / "es", args, girdi, api_bozuk, uretir)
    assert _davranis(yeni) == _davranis(eski), (
        f"{etiket}: mesaj çağrıları DAVRANIŞI değiştirdi\nyeni={_davranis(yeni)}\nes={_davranis(eski)}")
    # Kıyas boş bir kıyas değil: yeni mesaj basılan senaryoda metin GERÇEKTEN ayrışır (eş mesajsızdır),
    # basılmayanda ayrışmaz (mesaj başka bir akışa sızmaz).
    assert ((yeni["stdout"], yeni["stderr"]) != (eski["stdout"], eski["stderr"])) is metin_farki, (
        f"{etiket}\n--- yeni ---\n{yeni['stdout']}\n{yeni['stderr']}\n--- eş ---\n{eski['stdout']}\n{eski['stderr']}")


@pytest.mark.parametrize("args", [("--kapi", "--kuru"), ("--tenant", "--kuru"), ("--dash", "--kuru"),
                                  ("--openrouter", "--kuru"), ("--apisix-admin", "--kuru"),
                                  ("--vault", "--dash", "--kuru"), ("--vault", "--openrouter", "--kuru")])
def test_D2_KURU_kosum_cikis_0_HICBIR_SEY_YAZMAZ_restart_YOK_kasaya_DOKUNMAZ(tmp_path, args):
    kok, ortam, log = _ortam(tmp_path)
    once = _agac(tmp_path)
    r = _kos(BETIK, ortam, *args)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _agac(tmp_path) == once, "kuru koşum dosya yazdı"
    assert not v521._birimler(kok) and not v521._kv_put_yollari(log), "kuru koşum restart/kasa yazımı"


# =================================================================================================
# M) MUTASYONLAR
# =================================================================================================

def test_M1_MUT_dash_uyari_CAGRISI_kalkarsa_A1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("  _agent_hedefi_uyarisi dash              #", "  :              #"), ad="m1.sh")
    _, ortam, _ = _ortam(tmp_path, uretici=URETICI)
    r = _kos(m, ortam, "--dash", "--kuru")
    assert r.returncode == 0 and not _uyarilar(r.stdout), f"MUTASYON ISIRMADI:\n{r.stdout}"


def test_M2_MUT_BAGLI_baslik_dali_kalkarsa_A1_KIRMIZI(tmp_path):
    capa = '    if [ "$bag" = "BAGLI" ]; then\n      echo "  !! UYARI'
    m = _mutant(tmp_path, (capa, capa.replace('[ "$bag" = "BAGLI" ]', "false", 1)), ad="m2.sh")
    _, ortam, _ = _ortam(tmp_path, uretici=URETICI)
    r = _kos(m, ortam, "--dash", "--kuru")
    assert [u["sinif"] for u in _uyarilar(r.stdout)] == [BAGSIZ_SINIF], f"MUTASYON ISIRMADI:\n{r.stdout}"


def test_M3_MUT_bag_siniflamasi_TERS_donerse_A4_ve_A1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ('"BAGLI" if sir in bagli else "BAGSIZ"',
                           '"BAGLI" if sir not in bagli else "BAGSIZ"'), ad="m3.sh")
    _, ortam, _ = _ortam(tmp_path, uretici=URETICI)
    r = _kos(m, ortam, "--db", "--kuru")
    assert DB_BLOK not in r.stdout, f"MUTASYON ISIRMADI (db):\n{r.stdout}"
    r = _kos(m, ortam, "--dash", "--kuru")
    assert [u["sinif"] for u in _uyarilar(r.stdout)] == [BAGSIZ_SINIF], f"MUTASYON ISIRMADI (dash):\n{r.stdout}"


def test_M4_MUT_BAGSIZ_suzgeci_kalkarsa_A7_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("""  printf '%s\\n' "$tablo" | awk -F'\\t' '$5=="BAGSIZ"'""",
                           """  printf '%s\\n' "$tablo" | awk 'NF'"""), ad="m4.sh")
    r = _bagsiz_kes(m, "dash")
    assert r.returncode == 0 and r.stdout.strip(), f"MUTASYON ISIRMADI:\n{r.stdout}\n{r.stderr}"


def test_M5_MUT_render_araligi_SABIT_yazilirsa_A5_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ('aralik="$(_render_araligi_metni)"', 'aralik="1m (sabit)"'), ad="m5.sh")
    sahte = tmp_path / "sahte_uretici.py"
    aralik = _render_araligi()
    sahte.write_text(URETICI.read_text(encoding="utf-8").replace(
        f'RENDER_ARALIGI = "{aralik}"', 'RENDER_ARALIGI = "7m"'), encoding="utf-8")
    _, ortam, _ = _ortam(tmp_path, uretici=sahte)
    r = _kos(m, ortam, "--dash", "--kuru")
    assert r.returncode == 0 and "aralık: 7m" not in r.stdout, f"MUTASYON ISIRMADI:\n{r.stdout}"


@pytest.mark.parametrize("kip,capa,args,girdi", [
    ("kuru", '  _deger_kaynagi_beyani "$alt"\n  echo "  render bekleme', ("--vault", "--dash", "--kuru"), ""),
    ("gercek", '    _deger_kaynagi_beyani "$alt"          #', ("--vault", "--dash"), f"{v521.YENI_DASH}\n"),
])
def test_M6_MUT_deger_kaynagi_CAGRISI_kalkarsa_B1_B2_KIRMIZI(tmp_path, kip, capa, args, girdi):
    yeni = dict(MESAJ_CAGRILARI)[capa]
    m = _mutant(tmp_path, (capa, yeni), ad=f"m6_{kip}.sh")
    _, ortam, _ = _ortam(tmp_path, uretici=URETICI)
    r = _kos(m, ortam, *args, girdi=girdi)
    assert r.returncode == 0 and "DEĞER KAYNAĞI" not in r.stdout, f"MUTASYON ISIRMADI ({kip}):\n{r.stdout}"


def test_M7_MUT_kasa_BAGLAMI_atanmazsa_C1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("    YAZIM_AKISI=kasa\n", "    :\n"), ad="m7.sh")
    _, ortam, _ = _ortam(tmp_path, uretici=URETICI, api_bozuk=True)
    r = _kos(m, ortam, "--vault", "--openrouter", girdi=f"{v521.YENI_NOUS}\n\n")
    assert r.returncode == 1 and "KANITLANDI" in r.stderr and "HENÜZ" not in r.stderr, (
        f"MUTASYON ISIRMADI:\n{r.stderr}")


def test_M8_MUT_beyan_kumesinden_bir_alt_DUSERSE_B3_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("    kapi|tenant|db|dash|apisix-admin)\n", "    kapi|tenant|db|apisix-admin)\n"),
                ad="m8.sh")
    assert _beyan_basan_altlar(m) != _uret_cagiran_altlar(m), "MUTASYON ISIRMADI"


def test_M9_MUT_iz_kiyasi_GERCEK_davranis_farkini_YAKALAR(tmp_path):
    """D1'in kıyası bir tiyatro değil: mesaj çağrısının yanına bir restart eklenince iz AYRIŞIR."""
    capa = "  _agent_hedefi_uyarisi dash              #"
    bozuk = _mutant(tmp_path, (capa, "  sudo systemctl restart meridian.service; " + capa.lstrip()),
                    ad="m9.sh")
    a = _iz(bozuk, tmp_path / "bozuk", ("--dash", "--kuru"))
    b = _iz(BETIK, tmp_path / "yeni", ("--dash", "--kuru"))
    assert _davranis(a) != _davranis(b), "MUTASYON ISIRMADI: iz kıyası restart farkını görmedi"
