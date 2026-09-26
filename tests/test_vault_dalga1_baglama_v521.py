"""test_vault_dalga1_baglama_v521.py — TSK-064: dalga-1'in üç sırrı KASAYA BAĞLANIR (2026-09-17).

NE ÇAKIYOR. `deploy/sir_envanteri.yaml::vault_kv`in dalga-1 girdileri `dash_token`,
`apisix_admin_key`, `nous_api_key` Vault Agent'ın RENDER HEDEFİDİR (`/etc/meridian/<ad>`) ama
`rotasyon_siri` taşımıyordu. Sonuç: `sir_rotasyon.sh --dash --vault` / `--apisix-admin --vault`
"kasaya BAĞLI sırrı YOK" ile düşüyor, `--openrouter --vault` NOUS'u "KAPSAM DIŞI — eski yolla
döner" diye beyan ediyordu; eski yol ise Agent'ın render ettiği dosyaya DOĞRUDAN yazar. Hipotez
(ROADMAP TSK-064 14:2xZ, A1'de ÖLÇÜLMEDİ): Agent render aralığında (1 dk) kasadaki ESKİ değeri
geri yazar ve rotasyon sessizce geri alınır. Doğru yön kasadan rotasyondur.

ROL-1 KARARI (Seçenek A, değişmez): dalga-1 girdisine YALNIZ `rotasyon_siri` eklenir — `kaynak` /
`kopya_kaynaklari` GİREMEZ (v485 E1). `HINDSIGHT_API_DATABASE_URL` / `--db` bu dilimde BAĞLANMADI;
onun yerine eski yol ve `--db --vault` Agent render hedefi UYARISI basıyordu.
2026-09-24 (TSK-064 `--db --vault`, v538): DB de BAĞLANDI — sıra tasarlandı (kasa → render kanıtı →
ALTER ROLE → restart → kanıt). A2/A3/B3/E1/M3 yeni sözleşmeye çekildi: bağlı küme artık tablonun
BÜTÜN sırlarıdır, `--db --vault` kasa yolunun kendi dalıyla koşar (uyarı basmaz); eski `--db`
uyarısı bağlı sınıfa geçti (E2/E3 aynen yeşil — uyarı, hedef ve kasa yolu yine basılır). Bağsız
sırrın kapsam beyanı dalı (M3) artık E5'in bağsız-NOUS sahte envanteriyle ölçülür.

ÖLÇÜLÜP BRIEF'E EKLENENLER (rapor: tsk064-baglama-rapor.md):
  · `--openrouter --vault` NOUS bağlanınca İLK KEZ iki sırlı döngü koşar. Döngü boş değerde
    `die` ediyordu — `_oku_gizli` istemi ise "boş = bu bacağı atla" der ve eski yol tek anahtarı
    döndürebilir. Boş değer artık o sırrı ATLAR (ADIYLA), hiç değer yoksa durur (D4/D5).
  · NOUS'un eski yoldaki VARLIK kanıtı (`_nous_hali`) kasa yolunda da koşar (D3/D7).
  · Kuru rapor yeniden başlatılacak birimleri basmıyordu — `--dash --vault --kuru` planında HİÇBİR
    birim görünmezdi. Gerçek koşum ile kuru rapor artık AYNI yardımcıdan okur (C1).
  · İki sırlı turda ikinci sırrın render'ı gelmezse ilk sır kasada/eski kanalda YENİ, tüketicisi
    yeniden başlamamış kalır — hâl ADIYLA basılır (D8).
  · `ops/apisix_uygula.py` (birim olmayan tüketici) beyanı kasa yolunda da basılır (C1/D2).

BÖLÜMLER
  A  Envanter bağı (değerler, şema, DB bağlanmadı, bağlı küme tam)
  B  `_vault_kv_satirlari` — betikten KESİLEN fonksiyon, gerçek ve sahte envanterle
  C  `--<alt> --vault --kuru` — düşmez, kasa yolu + render hedefi + restart planı
  D  `--<alt> --vault` gerçek koşum (yol-duyarlı sahte kasa) — değer/hash BASILMAZ
  E  `--db` / `--db --vault` Agent render hedefi uyarısı + kapsam beyanının iki dalı
  M  MUTASYONLAR — her çivinin hedeflediği dalı ısırdığı

SIR DEĞERİ YOK: her değer `SAHTE-` önekli ve sahtedir.
"""
from __future__ import annotations

import inspect
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest
import yaml

from tests import test_vault_dalga2_v491 as v491
from tests import test_vault_faz2_v485 as v485
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    ENVANTER,
    ESKI,
    _betik_kopyalari,
    _env_alan,
    _kos,
    _mutant,
    _sahte_ortam,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

#: BAĞ TABLOSU — ELLE durur (v491 DALGA2_ADLARI gerekçesi): envanterden türetilseydi bir bağ
#: envanterden düştüğünde çivi de onunla küçülür ve "her şey uyuşuyor" derdi.
#: vault_kv adı → (rotasyon_siri, alt komut, kasa yolu, render hedefi, restart birimi)
BAGLAR = {
    "dash_token": ("MERIDIAN_DASH_TOKEN", "dash", "secret/meridian/dash_token",
                   "/etc/meridian/dash_token", "meridian.service"),
    "apisix_admin_key": ("APISIX_ADMIN_KEY", "apisix-admin", "secret/meridian/apisix_admin_key",
                         "/etc/meridian/apisix_admin_key", "apisix.service"),
    "nous_api_key": ("NOUS_API_KEY", "openrouter", "secret/meridian/nous_api_key",
                     "/etc/meridian/nous_api_key", "meridian.service"),
}
#: Kasaya BAĞLI rotasyon sırlarının TAM kümesi. Bu dilimde tek bağsız sır DB parolasıydı; 2026-09-24
#: (TSK-064 `--db --vault`, v538) o da bağlandı — küme artık tablonun BÜTÜN sırlarıdır.
#: 2026-09-26 (TSK-226b, v556): `HINDSIGHT_CP_ACCESS_KEY` tabloya `--cp` ile girdi ve kasaya BAĞLI
#: (dalga-2 girdisi `hindsight_cp_access_key`in `rotasyon_siri`si) — küme yine tablonun BÜTÜN sırları.
BAGLI_TAM_KUME = {"KAPI_APIKEY", "HINDSIGHT_API_TENANT_API_KEY", "OPENROUTER_API_KEY",
                  "MERIDIAN_DASH_TOKEN", "APISIX_ADMIN_KEY", "NOUS_API_KEY", "HINDSIGHT_DB_PAROLA",
                  "HINDSIGHT_CP_ACCESS_KEY"}
DB_SIR = "HINDSIGHT_DB_PAROLA"
DB_KV = "HINDSIGHT_API_DATABASE_URL"
DB_HEDEF = "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"
DB_KASA = "secret/meridian/HINDSIGHT_API_DATABASE_URL"
LLM_KASA = "secret/meridian/HINDSIGHT_API_LLM_API_KEY"

UYARI = "VAULT AGENT RENDER HEDEFİ"
ESKI_YOL_METNI = "eski yolla döner"
#: `APISIX_ADMIN_KEY`in birim OLMAYAN tüketicisi — restart kümesine girmez, ADIYLA beyan edilir.
BIRIMSIZ_APISIX = "ops/apisix_uygula.py yeniden başlatılmaz"

YENI_DASH = "SAHTE-YENI-DASH-0521"
YENI_ADMIN = "SAHTE-YENI-ADMIN-0521"
YENI_NOUS = "SAHTE-YENI-NOUS-0521"
YENI_OR = "SAHTE-YENI-OR-0521"
YENILER = (YENI_DASH, YENI_ADMIN, YENI_NOUS, YENI_OR)


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _kv() -> dict[str, dict]:
    return {g["ad"]: g for g in yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]}


def _sahte_envanter(tmp_path: pathlib.Path, ad: str, degistir) -> pathlib.Path:
    """Envanterin YAML düzeyinde değiştirilmiş kopyası. `degistir(veri)` yerinde değiştirir."""
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    degistir(veri)
    yol = tmp_path / f"{ad}.yaml"
    yol.write_text(yaml.safe_dump(veri, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return yol


def _girdi(veri: dict, ad: str) -> dict:
    return next(g for g in veri["vault_kv"] if g["ad"] == ad)


#: YOL-DUYARLI SAHTE KASA. v491'in şimi her `kv put`u TEK kanonik hedefe (LLM anahtarı) render
#: ediyordu — dalga-1 bağında NOUS/dash/admin kendi hedeflerine render edilmeli, yoksa render
#: ölçümü hiç gelmez. Eşleme envanterin `vault_yolu → hedef`inden gelir: gerçek Agent'ın şablonları
#: da oradan ÜRETİLİR (`ops/vault_politika_uret.py`), yani şim üretilmiş yapılandırmanın modelidir.
#: `render`: True = her eşlenen yol · False = hiçbiri · yol demeti = YALNIZ o kasa yolları (iki sırlı
#: turda ikinci sırrın render'ı gelmeyince ilk sırrın hâli ölçülebilsin diye — D8).
SIM_KASA = '''#!/usr/bin/env python3
import os, sys
ESLEME = __ESLEME__
KOK = __KOK__
KASA = __KASA__
RENDER = __RENDER__
with open(__LOG__, "a", encoding="utf-8") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
a = sys.argv[1:]
if a[:1] == ["login"]:
    sys.stdin.read()
    sys.exit(0)
if a[:2] == ["kv", "put"]:
    yol = a[2]
    deger = sys.stdin.read()
    os.makedirs(KASA, exist_ok=True)
    with open(os.path.join(KASA, yol.replace("/", "_")), "w", encoding="utf-8") as fh:
        fh.write(deger)
    if yol in ESLEME and (RENDER is True or (RENDER and yol in RENDER)):
        hedef = KOK + ESLEME[yol]
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        with open(hedef, "w", encoding="utf-8") as fh:
            fh.write(deger)
    sys.exit(0)
sys.exit(0)
'''


def _kasa_ortami(tmp_path: pathlib.Path, render: bool | tuple[str, ...] = True,
                 envanter: pathlib.Path = ENVANTER) -> tuple[pathlib.Path, dict, pathlib.Path]:
    kok, ortam = _sahte_ortam(tmp_path)
    esleme = {g["vault_yolu"]: g["hedef"]
              for g in yaml.safe_load(envanter.read_text(encoding="utf-8"))["vault_kv"]
              if "hedef" in g}
    binn = tmp_path / "kasa_bin"
    binn.mkdir()
    log = tmp_path / "kasa_argv.log"
    govde = (SIM_KASA.replace("__ESLEME__", repr(esleme)).replace("__KOK__", repr(str(kok)))
             .replace("__KASA__", repr(str(tmp_path / "kasa"))).replace("__RENDER__", repr(render))
             .replace("__LOG__", repr(str(log))))
    (binn / "vault").write_text(govde, encoding="utf-8")
    (binn / "vault").chmod(0o755)
    jeton = kok / "etc/vault/admin.token"
    jeton.parent.mkdir(parents=True, exist_ok=True)
    jeton.write_text("SAHTE-hvs-yonetici\n", encoding="utf-8")
    ortam = dict(ortam, VAULT_BIN=str(binn / "vault"), VAULT_TOKEN_FILE=str(jeton),
                 VAULT_ENVANTER=str(envanter), PYTHON_BIN=sys.executable,
                 VAULT_RENDER_TAVAN_S="1", VAULT_RENDER_ARALIK_S="0.05")
    return kok, ortam, log


def _kv_put_yollari(log: pathlib.Path) -> list[str]:
    if not log.exists():
        return []
    return [s.split()[2] for s in log.read_text(encoding="utf-8").splitlines()
            if s.startswith("kv put ")]


def _birimler(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").split()


def _deger_basilmaz(r: subprocess.CompletedProcess, kok: pathlib.Path, *loglar: pathlib.Path) -> None:
    """Değer/hash basılmaz sözleşmesi (v447 D5 düzeneği): stdout, stderr ve iki argv günlüğü."""
    metinler = {"stdout": r.stdout, "stderr": r.stderr,
                "şim argv": (kok / ".sahte/argv.log").read_text(encoding="utf-8")}
    for log in loglar:
        if log.exists():
            metinler[log.name] = log.read_text(encoding="utf-8")
    for etiket, metin in metinler.items():
        for d in YENILER + tuple(ESKI.values()):
            assert d not in metin, f"SIR DEĞERİ {etiket} içine düştü: {d}"


def _yeniden_baslatilacak(cikti: str) -> set[str]:
    m = re.findall(r"^  yeniden başlatılacak: (.*)$", cikti, re.M)
    assert len(m) == 1, f"kuru raporda TEK 'yeniden başlatılacak:' satırı beklendi: {m}\n{cikti}"
    return set(re.findall(r"[a-z0-9-]+\.service", m[0]))


def _fonksiyon(ad: str, betik: pathlib.Path = BETIK) -> str:
    """Betikten bir kabuk fonksiyonunu KESER (v447 `_yardimci` gerekçesi: kopya değil kaynak)."""
    ham = betik.read_text(encoding="utf-8")
    bas = ham.index(f"\n{ad}() {{\n") + 1
    son = ham.index("\n}\n", bas) + 3
    return ham[bas:son]


def _kv_satirlari(envanter: pathlib.Path, *sirlar: str) -> subprocess.CompletedProcess:
    kod = _fonksiyon("_vault_kv_satirlari") + '\n_vault_kv_satirlari "$@"\n'
    return subprocess.run(["bash", "-c", kod, "_", *sirlar], capture_output=True, text=True,
                          env=dict(os.environ, PYTHON_BIN=sys.executable,
                                   VAULT_ENVANTER=str(envanter)))


# =================================================================================================
# A) ENVANTER BAĞI
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v520 A0 ile aynı): ithal edilen modül başka ağaçtan yüklenirse bütün
    çiviler BAŞKA bir betiği ölçer — sessizce."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v485.__file__), pathlib.Path(v491.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


@pytest.mark.parametrize("ad", sorted(BAGLAR))
def test_A1_dalga1_girdisi_ROTASYON_SIRI_tasir_ve_tablonun_REFERANSI_render_hedefi(ad):
    """Bağın dört yüzü birlikte: (1) değer rotasyon tablosundaki sır KİMLİĞİYLE birebir; (2) girdi
    YALNIZ `rotasyon_siri` eklemiştir (Seçenek A — `kaynak`/`kopya_kaynaklari` YOK); (3) kasa yolu
    ve render hedefi değişmedi; (4) betiğin kopya tablosunda o sırrın İLK satırı (REFERANS) render
    hedefidir — `--vault`ın son kanıtı (`_envanter_esitlik`) referansı ona kıyaslar."""
    sir, alt, kasa, hedef, _ = BAGLAR[ad]
    g = _kv()[ad]
    assert g.get("rotasyon_siri") == sir, f"{ad}: rotasyon_siri {g.get('rotasyon_siri')!r} ≠ {sir!r}"
    zorunlu = {"ad", "vault_yolu", "hedef", "mod", "sahip", "tuketici"}
    assert set(g) == zorunlu | {"rotasyon_siri"}, f"{ad}: şema {sorted(set(g) - zorunlu)}"
    assert (g["vault_yolu"], g["hedef"]) == (kasa, hedef), g
    satirlar = [k for k in _betik_kopyalari() if k["sir"] == sir]
    assert satirlar, f"{sir} betiğin kopya tablosunda YOK (dangling bağ)"
    assert {k["alt"] for k in satirlar} == {alt}, satirlar
    assert (satirlar[0]["tur"], satirlar[0]["yol"]) == ("dosya", hedef), (
        f"{sir}: REFERANS satırı render hedefi değil: {satirlar[0]}")


def test_A2_DB_URL_BAGLANDI_ve_YALNIZ_o_girdi_DB_parolasini_gosterir():
    """2026-09-17'de bağ BİLEREK yoktu (ALTER ROLE ↔ kasa ↔ render sırası tasarlanmamıştı). 2026-09-24
    (TSK-064, v538): sıra tasarlandı ve uygulandı → bağ VAR, TEK girdiden ve YALNIZ `rotasyon_siri`
    alanıyla (Seçenek A: dalga-1'e kaynak/kopya GİREMEZ). Bağ düşerse `--db --vault` "kasaya BAĞLI
    sırrı YOK" ile durur; ikinci bir girdi aynı sırrı gösterirse rotasyon hangi DSN'i döndürdüğünü
    bilemez."""
    kv = _kv()
    assert kv[DB_KV].get("rotasyon_siri") == DB_SIR, kv[DB_KV]
    assert [g["ad"] for g in kv.values() if g.get("rotasyon_siri") == DB_SIR] == [DB_KV]
    assert not ({"kaynak", "kopya_kaynaklari"} & set(kv[DB_KV])), kv[DB_KV]


def test_A3_BAGLI_KUME_tablonun_BUTUN_sirlari():
    """Pozitif kontrol: bağlı küme ELLE yazılı tam küme ve rotasyon tablosunun BÜTÜN sırlarıyla AYNI
    (2026-09-24'e kadar DB parolası dışarıda kalıyordu). Bir bağ düşerse ya da tabloya bağsız bir
    sır girerse öter."""
    bagli = {g["rotasyon_siri"] for g in _kv().values() if g.get("rotasyon_siri")}
    assert bagli == BAGLI_TAM_KUME, sorted(bagli ^ BAGLI_TAM_KUME)
    tablo = {k["sir"] for k in _betik_kopyalari()}
    assert tablo == bagli, sorted(tablo ^ bagli)


# =================================================================================================
# B) `_vault_kv_satirlari` — betikten KESİLEN fonksiyon
# =================================================================================================

@pytest.mark.parametrize("ad", sorted(BAGLAR))
def test_B1_kv_satirlari_BAGLI_sir_icin_TEK_satir_kasa_yolu_ve_render_hedefi(ad):
    sir, _, kasa, hedef, _ = BAGLAR[ad]
    r = _kv_satirlari(ENVANTER, sir)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"{ad}\t{kasa}\t{hedef}\t{sir}\t-"], r.stdout


def test_B2_SAHTE_envanterde_BAG_YOKSA_satir_BASILMAZ(tmp_path):
    """B1'in negatif kontrolü: aynı fonksiyon, üç `rotasyon_siri` kaldırılmış envanter → boş.
    Satır bağdan gelmeseydi (ör. ad eşleşmesi) burası da satır basardı."""
    def bagi_sok(veri):
        for ad in BAGLAR:
            _girdi(veri, ad).pop("rotasyon_siri", None)
    sahte = _sahte_envanter(tmp_path, "bagsiz", bagi_sok)
    for sir, *_ in BAGLAR.values():
        r = _kv_satirlari(sahte, sir)
        assert r.returncode == 0 and r.stdout == "", (sir, r.stdout, r.stderr)


def test_B3_DB_parolasi_icin_TEK_satir_kasa_yolu_ve_render_hedefi():
    """2026-09-24 (TSK-064, v538): bağ var → `--db --vault`ın okuduğu TEK satır (takma ad yok)."""
    r = _kv_satirlari(ENVANTER, DB_SIR)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"{DB_KV}\t{DB_KASA}\t{DB_HEDEF}\t{DB_SIR}\t-"], r.stdout


# =================================================================================================
# C) `--<alt> --vault --kuru`
# =================================================================================================

@pytest.mark.parametrize("alt,ad", [("dash", "dash_token"), ("apisix-admin", "apisix_admin_key")])
def test_C1_KURU_kosum_DUSMEZ_kasa_yolu_render_hedefi_ve_RESTART_plani(tmp_path, alt, ad):
    sir, _, kasa, hedef, birim = BAGLAR[ad]
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", f"--{alt}", "--kuru")
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    assert "kasaya BAĞLI sırrı YOK" not in r.stderr, r.stderr
    assert re.search(rf"kasaya yazılacak\s*:\s*{re.escape(kasa)}\s", r.stdout), r.stdout
    assert re.search(rf"render kanıtı\s*:\s*{re.escape(hedef)}\s", r.stdout), r.stdout
    assert _yeniden_baslatilacak(r.stdout) == {birim}, r.stdout
    assert "KAPSAM DIŞI" not in r.stdout and UYARI not in r.stdout, r.stdout
    # Birim OLMAYAN tüketici (brief madde 3): restart kümesi dışında, ADIYLA.
    assert (BIRIMSIZ_APISIX in r.stdout) == (alt == "apisix-admin"), r.stdout
    assert not log.exists(), f"kuru koşum kasaya çağrı yaptı:\n{log.read_text()}"
    assert not _birimler(kok), "kuru koşum birim yeniden başlattı"


def test_C2_OPENROUTER_kuru_IKI_sir_da_BAGLI_ve_NOUS_tuketicisi_planda(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    for kasa in (BAGLAR["nous_api_key"][2], LLM_KASA):
        assert re.search(rf"kasaya yazılacak\s*:\s*{re.escape(kasa)}\s", r.stdout), (kasa, r.stdout)
    assert "KAPSAM DIŞI" not in r.stdout and ESKI_YOL_METNI not in r.stdout, r.stdout
    assert "/api/secrets/NOUS_API_KEY" in r.stdout, "NOUS'un motor deposu kopyası planda yok"
    assert _yeniden_baslatilacak(r.stdout) == {
        "apisix.service", "hindsight-api.service", "meridian.service"}, r.stdout
    assert "boş bırakılan sır bu tur DÖNMEZ" in r.stdout, (
        "boş değer = o sır bu tur DÖNMEZ beyanı planda yok")
    assert not log.exists() and not _birimler(kok)


# =================================================================================================
# D) `--<alt> --vault` GERÇEK KOŞUM (sahte kasa)
# =================================================================================================

def test_D1_DASH_kasadan_doner_render_olculur_MERIDIAN_yeniden_baslar(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--dash", girdi=f"{YENI_DASH}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _kv_put_yollari(log) == ["secret/meridian/dash_token"], log.read_text()
    assert "render ÖLÇÜLDÜ: /etc/meridian/dash_token" in r.stdout, r.stdout
    assert (kok / "etc/meridian/dash_token").read_text().strip() == YENI_DASH
    assert (kok / "run/credentials/meridian.service/dash_token").read_text().strip() == YENI_DASH
    assert _birimler(kok) == ["meridian.service"], _birimler(kok)
    _deger_basilmaz(r, kok, log)


def test_D2_APISIX_ADMIN_kasadan_doner_ESKI_KANAL_esitlenir_KAPI_yeniden_baslar(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--apisix-admin", girdi=f"{YENI_ADMIN}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _kv_put_yollari(log) == ["secret/meridian/apisix_admin_key"], log.read_text()
    assert (kok / "etc/meridian/apisix_admin_key").read_text().strip() == YENI_ADMIN
    assert _env_alan(kok / "opt/apisix/.env-apisix", "APISIX_ADMIN_KEY") == YENI_ADMIN, (
        "iki-kanal dönemi: .env-apisix kopyası KASADAN gelen değerle yazılmadı")
    assert _birimler(kok) == ["apisix.service"], _birimler(kok)
    assert (kok / ".sahte/apisix_etkin_admin").read_text().strip() == YENI_ADMIN
    assert BIRIMSIZ_APISIX in r.stdout, "birim olmayan tüketici (ops aracı) beyan edilmedi"
    _deger_basilmaz(r, kok, log)


def test_D3_OPENROUTER_IKI_sir_kasadan_NOUS_depo_kopyasi_ve_VARLIK_kaniti(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _kv_put_yollari(log) == ["secret/meridian/nous_api_key", LLM_KASA], log.read_text()
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    depo = json.loads((kok / "opt/meridian/state/secrets.json").read_text(encoding="utf-8"))
    assert depo["NOUS_API_KEY"] == YENI_NOUS, "motor deposu (api kopyası) kasadan eşitlenmedi"
    assert "meridian.service" in _birimler(kok), _birimler(kok)
    assert "motor kanıtı: /api/secrets/test/nous ok:true" in r.stdout, r.stdout
    _deger_basilmaz(r, kok, log)


def test_D4_OPENROUTER_YALNIZ_NOUS_bos_birakilan_sir_ATLANIR_ve_ADIYLA_soylenir(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _kv_put_yollari(log) == ["secret/meridian/nous_api_key"], log.read_text()
    assert "ATLANDI: OPENROUTER_API_KEY" in r.stdout, r.stdout
    assert _birimler(kok) == ["meridian.service"], (
        f"atlanan sırrın tüketicisi yeniden başlatıldı: {_birimler(kok)}")
    assert (kok / "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY").read_text().strip() == ESKI["or"]
    assert "kapı kanıtı" not in r.stdout, "dönmeyen OPENROUTER için kapı kanıtı 'kanıt' diye basıldı"
    _deger_basilmaz(r, kok, log)


def test_D5_HICBIR_deger_verilmezse_DURUR_kasaya_HICBIR_SEY_yazilmaz(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi="\n\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "yapacak iş yok" in r.stderr, r.stderr
    assert _kv_put_yollari(log) == [] and not _birimler(kok)
    assert not list((kok / "root").glob("sir-yedek-*")), "değer yokken yedek alındı"


def test_D6_NOUS_RENDER_GELMEZSE_depo_kopyasi_ve_dosya_YAZILMAZ(tmp_path):
    kok, ortam, log = _kasa_ortami(tmp_path, render=False)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    depo = json.loads((kok / "opt/meridian/state/secrets.json").read_text(encoding="utf-8"))
    assert depo["NOUS_API_KEY"] == ESKI["nous"], "render ölçülmeden motor deposu yazıldı"
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    assert not _birimler(kok)
    _deger_basilmaz(r, kok, log)


def test_D7_NOUS_VARLIK_kaniti_OLCULEMEZSE_cikis_2(tmp_path):
    """Motor 200 döner ama gövde yok (`SAHTE_PING_GOVDESIZ`): varlık kanıtı ÖLÇÜLEMEDİ → çıkış 2,
    "geçti" değil."""
    kok, ortam, log = _kasa_ortami(tmp_path)
    ortam["SAHTE_PING_GOVDESIZ"] = "1"
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "test/nous" in r.stderr, r.stderr


def test_D8_IKI_SIRLI_turda_IKINCI_render_GELMEZSE_ONCE_DONEN_sir_ADIYLA_soylenir(tmp_path):
    """NOUS kasaya ve eski kanala YENİ değerle yazıldı, OPENROUTER'ın render'ı gelmedi: çıkış 2 ve
    tüketiciler yeniden başlamaz (restart döngüden sonra). Bu hâl bu dilimin açtığı iki sırlı
    döngüye özgüdür — sessiz kalsaydı operatör "hiçbir şey olmadı" sanardı."""
    kok, ortam, log = _kasa_ortami(tmp_path, render=("secret/meridian/nous_api_key",))
    r = _kos(BETIK, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    assert not _birimler(kok), _birimler(kok)
    assert "BU TURDA ÖNCE DÖNEN SIR: NOUS_API_KEY" in r.stderr, r.stderr
    assert "YENİDEN BAŞLATILMADI" in r.stderr, r.stderr
    _deger_basilmaz(r, kok, log)


# =================================================================================================
# E) `--db` — AGENT RENDER HEDEFİ UYARISI (eski yolda; davranış değişmez)
# =================================================================================================
# 2026-09-24 (TSK-064, v538): DB bağlandı → eski yol uyarısı BAĞLI sınıfta (`--db --vault`u gösterir);
# `_uyari_db`nin ölçtüğü dört iz (başlık, hedef, kasa yolu, sır) iki sınıfta da basılır.

def _uyari_db(metin: str) -> None:
    assert UYARI in metin, f"Agent render hedefi uyarısı YOK:\n{metin}"
    assert DB_HEDEF in metin and DB_KASA in metin, metin
    assert DB_SIR in metin, metin


@pytest.mark.parametrize("kuru", [True, False])
def test_E1_DB_VAULT_kasa_yolunun_KENDI_dali_UYARISIZ_kuru_plan_ya_da_bos_degerde_DURUR(tmp_path, kuru):
    """Bağ öncesi (2026-09-17) `--vault --db` uyarı basıp düşüyordu. Bağ sonrası kasa yolunun kendi
    dalı koşar: kuru plan çıkış 0; gerçek koşum bu dosyanın kasa şiminde (yalnız `kv put` tanır,
    `kv get` BOŞ döner) ön kontrolde durur — "kasaya HİÇBİR ŞEY yazılmadı" (çıkış 1). İkisinde de
    eski yolun uyarısı YOK (tasarım §3.9 — kasa yolu Agent'ı zaten besler), kasaya yazım ve restart
    YOK. Akışın kendisi (KV v2 sürüm modeliyle) v538'de ölçülür."""
    kok, ortam, log = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--vault", "--db", *(["--kuru"] if kuru else []), girdi="\n")
    assert r.returncode == (0 if kuru else 1), f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    tum = r.stdout + r.stderr
    assert UYARI not in tum and ESKI_YOL_METNI not in tum, tum
    assert "kasaya BAĞLI sırrı YOK" not in tum, tum
    if not kuru:
        assert "kasaya HİÇBİR ŞEY yazılmadı" in r.stderr, r.stderr
    assert _kv_put_yollari(log) == [] and not _birimler(kok)


def test_E2_DB_KURU_eski_yol_UYARI_basar_ve_plan_AYNEN(tmp_path):
    kok, ortam, _ = _kasa_ortami(tmp_path)
    once = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    r = _kos(BETIK, ortam, "--db", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    _uyari_db(r.stdout)
    assert "yeniden başlatılacak: hindsight-api.service" in r.stdout, r.stdout
    sonra = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    degisen = {str(p) for p in set(once) | set(sonra) if once.get(p) != sonra.get(p)}
    assert not (degisen - {str(kok / ".sahte/argv.log")}), degisen


def test_E3_DB_GERCEK_eski_yol_UYARIYLA_KOSAR_davranis_DEGISMEZ(tmp_path):
    kok, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    _uyari_db(r.stdout)
    assert (kok / ".sahte/pg_parola").read_text().strip() != ESKI["pg"], "eski yol KESİLDİ"
    assert r.stdout.index(UYARI) < r.stdout.index("ALTER ROLE"), "uyarı yazımdan SONRA basıldı"


def test_E4_TARAMA_YAPILAMAZSA_OLCULEMEDI_der_eski_yol_KESILMEZ(tmp_path):
    kok, ortam, _ = _kasa_ortami(tmp_path)
    ortam["VAULT_ENVANTER"] = str(tmp_path / "yok.yaml")
    r = _kos(BETIK, ortam, "--db", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "UYARI ÖLÇÜLEMEDİ" in r.stdout, r.stdout
    assert "yeniden başlatılacak: hindsight-api.service" in r.stdout


def test_E5_KAPSAM_BEYANI_iki_dal_AGENT_HEDEFI_uyari_DEGILSE_eski_metin(tmp_path):
    """Madde 5: bağsız sır Agent render hedefindeyse beyan UYARIDIR; değilse eski "KAPSAM DIŞI —
    eski yolla döner" metni KALIR. İki sahte envanter iki dalı ayrı ayrı ölçer."""
    def bagi_sok(veri):
        _girdi(veri, "nous_api_key").pop("rotasyon_siri")
    uyarili = _sahte_envanter(tmp_path, "nous_bagsiz", bagi_sok)
    _, ortam, _ = _kasa_ortami(tmp_path, envanter=uyarili)
    r = _kos(BETIK, ortam, "--vault", "--openrouter", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert f"{UYARI}, kasaya BAĞLI DEĞİL: NOUS_API_KEY → /etc/meridian/nous_api_key" in r.stdout, r.stdout
    assert ESKI_YOL_METNI not in r.stdout, r.stdout

    def hedefi_de_tası(veri):
        bagi_sok(veri)
        _girdi(veri, "nous_api_key")["hedef"] = "/etc/meridian/baska_hedef"
    duz = _sahte_envanter(tmp_path, "nous_hedefsiz", hedefi_de_tası)
    ortam2 = dict(ortam, VAULT_ENVANTER=str(duz))
    r2 = _kos(BETIK, ortam2, "--vault", "--openrouter", "--kuru")
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    assert "KAPSAM DIŞI (kasaya bağlı DEĞİL): NOUS_API_KEY — eski yolla döner" in r2.stdout, r2.stdout
    assert UYARI not in r2.stdout, r2.stdout


# =================================================================================================
# M) MUTASYONLAR
# =================================================================================================

@pytest.mark.parametrize("alan,deger", [
    ("kaynak", {"tur": "dosya", "dosya": "/etc/meridian/dash_token", "alan": None, "onek": None}),
    ("kopya_kaynaklari", [{"tur": "dosya", "dosya": "/etc/meridian/dash_token", "alan": None,
                           "onek": None}]),
])
def test_M1_v485_E1_dalga1e_KAYNAK_ya_da_KOPYA_girerse_KIRMIZI(tmp_path, monkeypatch, alan, deger):
    """Seçenek A'nın sınırı: dalga-1'e YALNIZ `rotasyon_siri` girer. Aynı envantere `kaynak` ya da
    `kopya_kaynaklari` eklenince E1 öter; gerçek envanterde (üç `rotasyon_siri` taşırken) yeşildir."""
    v485.test_E1_vault_kv_DALGA1_kumesini_tam_tasir()   # pozitif: rotasyon_siri İZİNLİ
    sahte = _sahte_envanter(tmp_path, f"dalga1_{alan}",
                            lambda veri: _girdi(veri, "dash_token").__setitem__(alan, deger))
    monkeypatch.setattr(v485, "ENVANTER", sahte)
    with pytest.raises(AssertionError, match="dalga-1 girdisi"):
        v485.test_E1_vault_kv_DALGA1_kumesini_tam_tasir()


def test_M1b_ESKI_E1_kurali_bugunku_envanterde_KIRMIZI():
    """E1'in gevşetmesi GEREKLİYDİ ve DAR: eski kural (`set(g) == zorunlu`) bugünkü envantere
    uygulanınca öter — yani üç `rotasyon_siri` gerçekten E1'in ölçtüğü alandadır."""
    kaynak = inspect.getsource(v485.test_E1_vault_kv_DALGA1_kumesini_tam_tasir)
    capa = "set(g) - zorunlu - DALGA1_IZINLI_BAG"
    assert capa in kaynak, f"mutasyon çapası E1'de yok (çivi bayatlamış): {capa!r}"
    ns = dict(vars(v485))
    # `dont_inherit=True` (v334 §B3): bu dosyanın `__future__` bayrağı exec edilen koda sızmasın.
    exec(compile(kaynak.replace(capa, "set(g) - zorunlu", 1), v485.__file__, "exec",
                 dont_inherit=True), ns)
    with pytest.raises(AssertionError, match="dalga-1 girdisi"):
        ns["test_E1_vault_kv_DALGA1_kumesini_tam_tasir"]()


@pytest.mark.parametrize("etiket", ["referans_ters", "dangling"])
def test_M2_v491_A5_dalga1_BAGI_tabloyla_AYRISIRSA_KIRMIZI(tmp_path, monkeypatch, etiket):
    """v491 A5'in dalga-1 dalı: bağın referansı render hedefi değilse (tablo sırası ters) ya da
    `rotasyon_siri` tabloda yoksa öter."""
    v491.test_A5_ROTASYON_SIRI_bagi_kopya_kumesiyle_BIREBIR()   # pozitif
    if etiket == "referans_ters":
        def boz(veri):
            k = veri["rotasyon_kopyalari"]["kopyalar"]
            ix = [i for i, x in enumerate(k) if x["sir"] == "APISIX_ADMIN_KEY"]
            assert len(ix) == 2
            k[ix[0]], k[ix[1]] = k[ix[1]], k[ix[0]]
    else:
        def boz(veri):
            _girdi(veri, "dash_token")["rotasyon_siri"] = "OLMAYAN_SIR"
    monkeypatch.setattr(v491, "ENVANTER", _sahte_envanter(tmp_path, f"a5_{etiket}", boz))
    with pytest.raises(AssertionError):
        v491.test_A5_ROTASYON_SIRI_bagi_kopya_kumesiyle_BIREBIR()


def test_M3_MUT_kapsam_beyaninin_AGENT_dali_kalkarsa_E5_KIRMIZI(tmp_path):
    """2026-09-24: DB bağlandı → bağsız + Agent hedefi olan sırrın TEK dünyası E5'in bağsız-NOUS sahte
    envanteridir (eskiden `--vault --db`/E1 ölçüyordu). Dal kalkınca uyarı yerine "eski yolla döner"."""
    m = _mutant(tmp_path, (
        """    if printf '%s\\n' "$tablo" | awk -F'\\t' -v k="$sir" '$1==k{b=1} END{exit !b}'; then""",
        "    if false; then"), ad="m3.sh")
    uyarili = _sahte_envanter(tmp_path, "nous_bagsiz_m3",
                              lambda veri: _girdi(veri, "nous_api_key").pop("rotasyon_siri"))
    kok, ortam, _ = _kasa_ortami(tmp_path, envanter=uyarili)
    r = _kos(m, ortam, "--vault", "--openrouter", "--kuru")
    tum = r.stdout + r.stderr
    assert UYARI not in tum and ESKI_YOL_METNI in tum, f"MUTASYON ISIRMADI:\n{tum}"


def test_M4_MUT_db_UYARI_cagrisi_kalkarsa_E2_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("  _agent_hedefi_uyarisi db\n", ""), ad="m4.sh")
    _, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(m, ortam, "--db", "--kuru")
    assert r.returncode == 0 and UYARI not in r.stdout, f"MUTASYON ISIRMADI:\n{r.stdout}"


def test_M5_MUT_bos_deger_yine_DIE_ederse_D4_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ("      continue\n    fi\n    donen=",
                           '      die "değer boş (MUTANT)"\n    fi\n    donen='), ad="m5.sh")
    kok, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(m, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode != 0 and not _birimler(kok), f"MUTASYON ISIRMADI:\n{r.stdout}\n{r.stderr}"


def test_M6_MUT_NOUS_varlik_kaniti_kalkarsa_D7_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (
        '[ "$nhal" = "OK" ] || olcum_yok "motor /api/secrets/test/nous → $nhal (OK bekleniyordu; --vault NOUS varlık kanıtı)"',
        ":"), ad="m6.sh")
    _, ortam, _ = _kasa_ortami(tmp_path)
    ortam["SAHTE_PING_GOVDESIZ"] = "1"
    r = _kos(m, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode == 0, f"MUTASYON ISIRMADI:\n{r.returncode}\n{r.stdout}\n{r.stderr}"


def test_M7_MUT_kuru_RESTART_plani_kalkarsa_C1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, ('  echo "  yeniden başlatılacak: $(_sirala $hepsi)',
                           '  : "  yeniden başlatılacak: $(_sirala $hepsi)'), ad="m7.sh")
    _, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(m, ortam, "--vault", "--dash", "--kuru")
    assert r.returncode == 0 and not re.search(r"^  yeniden başlatılacak: ", r.stdout, re.M), (
        f"MUTASYON ISIRMADI:\n{r.stdout}")


@pytest.mark.parametrize("kip,capa,args,girdi", [
    ("gercek", '  _birimsiz_tuketici_beyani "$alt"\n\n  case "$alt" in',
     ("--vault", "--apisix-admin"), f"{YENI_ADMIN}\n"),
    ("kuru", '  _birimsiz_tuketici_beyani "$alt"\n  echo "  değer:',
     ("--vault", "--apisix-admin", "--kuru"), ""),
])
def test_M9_MUT_BIRIMSIZ_tuketici_beyani_kalkarsa_C1_D2_KIRMIZI(tmp_path, kip, capa, args, girdi):
    yeni = capa.replace('  _birimsiz_tuketici_beyani "$alt"\n', "", 1)
    m = _mutant(tmp_path, (capa, yeni), ad=f"m9_{kip}.sh")
    _, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(m, ortam, *args, girdi=girdi)
    assert r.returncode == 0 and BIRIMSIZ_APISIX not in r.stdout, (
        f"MUTASYON ISIRMADI ({kip}):\n{r.stdout}\n{r.stderr}")


def test_M10_MUT_ONCE_DONEN_sir_beyani_kalkarsa_D8_KIRMIZI(tmp_path):
    # Girinti 2026-09-24'te 8→6 (TSK-064: render beklemesi `_render_bekle`e çıktı, dal `if !` içinde).
    m = _mutant(tmp_path, ('      [ "$donen" = " $sir" ] || echo "!! BU TURDA ÖNCE DÖNEN SIR:',
                           '      [ "$donen" = " $sir" ] || : "!! BU TURDA ÖNCE DÖNEN SIR:'), ad="m10.sh")
    kok, ortam, _ = _kasa_ortami(tmp_path, render=("secret/meridian/nous_api_key",))
    r = _kos(m, ortam, "--vault", "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2 and "ÖNCE DÖNEN SIR" not in r.stderr, (
        f"MUTASYON ISIRMADI:\n{r.returncode}\n{r.stderr}")


def test_M8_MUT_sirrin_KENDI_tuketicisi_dusurse_D1_KIRMIZI(tmp_path):
    """Yan dosyası OLMAYAN dalga-1 sırrının tek restart kaynağı `_sir_birimleri`dir: düşerse
    `--dash --vault` meridian'ı YENİDEN BAŞLATMAZ (credential eski değerde kalır)."""
    m = _mutant(tmp_path, ('  echo "$birimler $tuk"', '  echo "$birimler"'), ad="m8.sh")
    kok, ortam, _ = _kasa_ortami(tmp_path)
    r = _kos(m, ortam, "--vault", "--dash", girdi=f"{YENI_DASH}\n")
    assert r.returncode != 0 and "meridian.service" not in _birimler(kok), (
        f"MUTASYON ISIRMADI:\n{r.returncode}\n{r.stdout}\n{r.stderr}")
