"""v476 — APISIX admin anahtarının CREDENTIAL kanalı (TSK-064 Faz-1C, repo tarafı).

BAĞLAM. `docs/TASARIM-SIR-YOL1-2026-09-03.md` §3 madde 4: "Faz-1C (apisix/cp): sarmalayıcı
ExecStart; `$env://` çözümü aynen; `ops/apisix_uygula.py` admin anahtarını credential dosyasından
okur." Bu tur o maddenin REPO yarısını çiviler; A1 yarısı (dosyanın yaratılması, sarmalayıcı
ExecStart) BU TURUN DIŞINDADIR ve reçetesi devir raporundadır.

ÜÇ YÜZEY, TEK GERÇEK:
  1. `ops/apisix_uygula.py` — admin anahtarını ÖNCE credential dosyasından (`/etc/meridian/
     apisix_admin_key`), bulamazsa `.env-apisix` YEDEĞİNDEN okur ve okuduğu KANALI bildirir.
  2. `deploy/oracle-a1/sir_rotasyon.sh --apisix-admin` — o sırrın DEĞERİNİ döndürür (iki kopya).
     Çivileri v447'dedir (bölüm R); burada yalnız iki betiğin AYNI yolları konuştuğu ölçülür.
  3. `deploy/oracle-a1/sir_credential_gecis.sh --faz1-apisix` — credential dosyasını `.env-apisix`
     içindeki MEVCUT değerden yaratır (kanal EKLER, `.env` satırını KAPATMAZ); `--geri-al-apisix`
     onu kaldırır.

SIR DEĞERİ YOK: bu dosyadaki her değer SAHTEDİR ve adında öyle yazar. Hiçbir çivi bir sır
değerini beklemez; beklediği şey DEĞERİN BASILMAMASIDIR.

OKUMA SIRASI NİYE ÖNEMLİ (ve niye "yedek" bir geçiş penceresidir). `.env-apisix` apisix
konteynerinin `--env-file`ıdır: dosya Faz-1C'den SONRA da yaşar (B sınıfı yarım kazanım, spec §2)
ve `APISIX_ADMIN_KEY` satırı kapının kendi `config.yaml` çözümü için orada KALIR. Yani burada
"yedek" TSK-049 faz-2'deki gibi silinecek bir satır değil, farklı bir TÜKETİCİNİN kanalıdır —
ve bu yüzden `apisix_uygula.py` iki kanalı da tanımak ZORUNDADIR. Kazanım: aracın okuduğu dosya
0400 root olabilir ve kapının `.env` dosyası gevşerse araç ondan etkilenmez.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

KOK = pathlib.Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from tests.conftest import betikten_modul_yukle  # noqa: E402

ARAC = KOK / "ops" / "apisix_uygula.py"
GECIS = KOK / "deploy" / "oracle-a1" / "sir_credential_gecis.sh"
ROTASYON = KOK / "deploy" / "oracle-a1" / "sir_rotasyon.sh"
ENVANTER = KOK / "deploy" / "sir_envanteri.yaml"

#: Tohum değerler. İkisi de SAHTE ve BİRBİRİNDEN FARKLI: "hangi kanal okundu" sorusu ancak iki
#: kanal AYRI değer taşırken ölçülebilir — eşit değerlerde her iki sıra da yeşil görünürdü.
KRED_DEGER = "SAHTE-KRED-ADMIN-0001"
ENV_DEGER = "SAHTE-ENV-ADMIN-0002"


# =================================================================================================
# A) ops/apisix_uygula.py — OKUMA SIRASI
# =================================================================================================

@pytest.fixture()
def arac(monkeypatch, tmp_path):
    """Aracı yükler ve İKİ kanalı da tmp'ye yönlendirir. Üretim yolları MUTLAKTIR; bu makinede
    yokturlar ve olmamaları bir ihlal değil, ÖLÇÜM SONUCUDUR (v361 `KAPI_ENV_DOSYASI` emsali)."""
    mod = betikten_modul_yukle(ARAC, "apisix_uygula_v476")
    kred = tmp_path / "apisix_admin_key"
    env = tmp_path / ".env-apisix"
    monkeypatch.setattr(mod, "KRED_DOSYASI", kred)
    monkeypatch.setattr(mod, "ENV_DOSYASI", env)
    return type("Arac", (), {"mod": mod, "kred": kred, "env": env})


def _env_yaz(yol: pathlib.Path, deger: str = ENV_DEGER) -> None:
    yol.write_text(f"# yorum satiri\nOPENROUTER_API_KEY=SAHTE-OR\n"
                   f"APISIX_ADMIN_KEY={deger}\nBOT_KEY_MERIDIAN=SAHTE-BOT\n", encoding="utf-8")


def test_A1_CREDENTIAL_dosyasi_VARSA_o_okunur(arac):
    """Sıranın TEK ölçüsü: iki kanal AYRI değer taşırken hangisi dönüyor. Eşit değerlerde bu
    çivi hiçbir şey ölçmezdi — yanlış sebeple yeşil bir çivi (§6)."""
    arac.kred.write_text(KRED_DEGER + "\n", encoding="utf-8")
    _env_yaz(arac.env)
    assert arac.mod.anahtar() == KRED_DEGER
    _, kanal = arac.mod.anahtar_kanali()
    assert "credential" in kanal and str(arac.kred) in kanal


def test_A2_CREDENTIAL_YOKSA_env_YEDEGINE_dusulur(arac):
    """GEÇİŞ PENCERESİ. Dosya A1'de henüz yaratılmadan bu sürüm dağıtılabilmeli — yoksa dağıtım
    ile elle kurulum birbirinin rehinesi olurdu (TSK-049 faz-2 deseni)."""
    _env_yaz(arac.env)
    assert not arac.kred.exists()
    assert arac.mod.anahtar() == ENV_DEGER
    _, kanal = arac.mod.anahtar_kanali()
    assert "YEDEK" in kanal and str(arac.env) in kanal


def test_A3_BOS_credential_DEGER_DEGILDIR_yedege_dusulur(arac):
    """2026-09-07 vakasının bu yüzeydeki karşılığı: 1 baytlık satır sonu taşıyan bir kaynak
    `test -s`i GEÇER. Boş değer "ayarlı ama değersiz" demektir ve alt kanala DÜŞMEK gerekir —
    sıfır ile "bilmiyorum" aynı şey değildir (uydurma yasağı)."""
    arac.kred.write_text("\n   \n", encoding="utf-8")
    _env_yaz(arac.env)
    assert arac.mod.anahtar() == ENV_DEGER


def test_A4_credential_kaynaginda_AD_ONEKI_taninir(arac):
    """Operatörün `.env` satırını kaynağa kopyalaması ÖNGÖRÜLEBİLİR bir kazadır
    (`meridian.secrets.credential_oku` aynı toleransı taşır). YALNIZ İSTENEN adın öneki soyulur."""
    arac.kred.write_text(f"APISIX_ADMIN_KEY={KRED_DEGER}\n", encoding="utf-8")
    _env_yaz(arac.env)
    assert arac.mod.anahtar() == KRED_DEGER


def test_A5_IKI_KANAL_da_yoksa_DURUR_ve_IZIN_ipucunu_verir(arac):
    """Ölçülemeyen değer `None` + NEDEN. Hata metni `sudo` ipucunu TAŞIMALI: 0400 root bir
    dosyayı ubuntu okuyamaz ve `PermissionError` operatöre "anahtar yok" gibi görünür — teşhis
    yanlış yerde aranır (betiğin bütün tezi bu ayrımdır)."""
    with pytest.raises(SystemExit) as ex:
        arac.mod.anahtar()
    metin = str(ex.value)
    assert "APISIX_ADMIN_KEY" in metin
    assert "sudo" in metin, "izin sınıfı hata metninde anılmıyor"
    assert str(arac.kred) in metin and str(arac.env) in metin


def test_A6_BICIM_TOLERANSI_meridian_secrets_ile_AYRISMAZ(arac, tmp_path, monkeypatch):
    """AYRIŞMA ÇİVİSİ (tek-kaynak yasası). Aracın credential ayrıştırıcısı
    `meridian.secrets.credential_oku`un BİR KOPYASIDIR — araç meridian'ı ithal ETMEZ (A1'de
    sistem python3'üyle koşar ve `meridian.obs`a ulaşan bir ithal canlı deftere yazardı,
    CLAUDE.md §2). Kopya kaçınılmaz olduğu için DAVRANIŞ eşitliği çiviyle bağlanır: aynı ham
    içerik iki ayrıştırıcıda aynı sonucu vermeli."""
    import meridian.secrets as secrets_mod

    kdir = tmp_path / "creds"
    kdir.mkdir()
    monkeypatch.setenv(secrets_mod.CREDENTIAL_DIZIN_ENV, str(kdir))
    ad = "APISIX_ADMIN_KEY"
    hamlar = [
        f"{KRED_DEGER}\n",
        f"  {KRED_DEGER}  \n",
        f"{ad}={KRED_DEGER}\n",
        f"{ad}= {KRED_DEGER}\n",
        f"{KRED_DEGER}\nikinci-satir-yok-sayilir\n",
        "\n",
        "   \n",
        "",
    ]
    for ham in hamlar:
        (kdir / ad).write_text(ham, encoding="utf-8")
        arac.kred.write_text(ham, encoding="utf-8")
        assert arac.mod._kredensiyelden() == secrets_mod.credential_oku(ad), repr(ham)


def test_A7_env_YEDEGI_TIRNAK_SOYMAZ_kapiyla_AYNI_degeri_gorur(arac):
    """ÖLÇÜLMÜŞ BİR KARAR, bir ihmal değil. `.env-apisix` docker'ın `--env-file`ıdır ve docker
    tırnak SOYMAZ: `APISIX_ADMIN_KEY="x"` yazılırsa konteynerin gördüğü değer `"x"`tir (tırnaklar
    dahil). Araç tırnağı soysaydı kapıyla AYRI bir değer kullanır ve `X-API-KEY` 401 alırdı —
    üstelik teşhis "anahtar yanlış" derken hata soyma kodunda olurdu. Mevcut davranış KORUNUR."""
    arac.env.write_text('APISIX_ADMIN_KEY="SAHTE-TIRNAKLI"\n', encoding="utf-8")
    assert arac.mod.anahtar() == '"SAHTE-TIRNAKLI"'


# =================================================================================================
# B) KANAL RAPORU — okunan kanalın ADI bildirilir, DEĞERİ asla
# =================================================================================================

def _routes_yaml(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "routes.yaml"
    p.write_text("rotalar:\n  - id: r-bir\n    uri: /bir\n    plugins:\n      prometheus: {}\n",
                 encoding="utf-8")
    return p


class _SahteCevap:
    def __init__(self, govde: dict, status: int = 200):
        self._g = json.dumps(govde).encode()
        self.status = status

    def read(self):
        return self._g

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture()
def kuru(arac, monkeypatch, tmp_path):
    """Ağı keser, routes.yaml'ı tmp'ye alır. `--denetle` GET'leri boş liste döner."""
    monkeypatch.setattr(arac.mod, "ROTA_DOSYASI", _routes_yaml(tmp_path))
    monkeypatch.setattr(arac.mod.urllib.request, "urlopen",
                        lambda req, timeout=None: _SahteCevap({"list": []}))
    return arac


def test_B1_main_KANALI_stderr_e_bildirir_DEGERI_BASMAZ(kuru, capsys):
    """Yasa 6'nın okuyucusu OPERATÖRDÜR: "araç hangi kanaldan okudu" sorusu bakım penceresinin
    ta kendisidir ve cevabı çıktıda GÖRÜNMELİDİR. Bildirilen şey KANAL ADIDIR — değer değil."""
    kuru.kred.write_text(KRED_DEGER + "\n", encoding="utf-8")
    _env_yaz(kuru.env)
    assert kuru.mod.main([]) == 0
    yak = capsys.readouterr()
    assert "admin anahtarı kanalı" in yak.err
    assert str(kuru.kred) in yak.err
    assert KRED_DEGER not in (yak.out + yak.err), "KANAL RAPORU SIR DEĞERİ BASTI"
    assert ENV_DEGER not in (yak.out + yak.err)


def test_B2_denetle_STDOUT_u_SAF_JSON_kalir(kuru, capsys):
    """`--denetle` çıktısı bir SÖZLEŞMEDİR (v364 onu `json.loads` ile bütün olarak ayrıştırır).
    Kanal raporu stdout'a basılsaydı o sözleşme sessizce kırılırdı — rapor stderr'e gider.

    DRİFT BİLEREK DOLU (beyanda bir rota var, sahte etcd boş): bu dalda çıkış kodu 1'dir ve
    ÖLÇÜLEN ŞEY ÇIKIŞ KODU DEĞİL STDOUT'UN SAFLIĞIDIR — arıza yolunda bile gövde ayrıştırılabilir
    kalmalı, çünkü okuyucu tam o anda çıktıyı makineyle okur."""
    _env_yaz(kuru.env)
    assert kuru.mod.main(["--denetle"]) == 1
    yak = capsys.readouterr()
    json.loads(yak.out)                       # tam gövde ayrıştırılabilmeli
    assert "admin anahtarı kanalı" in yak.err


def test_B3_YEDEK_kanal_okunurken_rapor_bunu_SOYLER(kuru, capsys):
    """"credential'dan okudum" ile "yedekten okudum" AYNI CÜMLE DEĞİLDİR: Faz-1C'nin kabul
    ölçütü tam olarak birincisidir ve sessizce ikincisine düşen bir araç geçişi "yapılmış"
    gösterirdi."""
    _env_yaz(kuru.env)
    assert kuru.mod.main([]) == 0
    yak = capsys.readouterr()
    assert "YEDEK" in yak.err and str(kuru.env) in yak.err


# =================================================================================================
# C) MUTASYON — çivi yeşili KANIT DEĞİLDİR (§6)
# =================================================================================================

def _mutant(tmp_path: pathlib.Path, kaynak: pathlib.Path, eski: str, yeni: str) -> pathlib.Path:
    ham = kaynak.read_text(encoding="utf-8")
    assert ham.count(eski) == 1, f"mutasyon deseni {ham.count(eski)} kez eşleşti: {eski!r}"
    hedef = tmp_path / kaynak.name
    hedef.write_text(ham.replace(eski, yeni), encoding="utf-8")
    return hedef


def test_C1_MUT_SIRA_ters_cevrilirse_A1_kirmizi(tmp_path, monkeypatch):
    """A1'in ısırdığı dal: yedek ÖNCE okunursa credential kanalı hiç kullanılmaz ve Faz-1C
    sessizce hiçbir şey yapmamış olur."""
    m = _mutant(tmp_path, ARAC,
                "    deger = _kredensiyelden()\n    if deger is not None:",
                "    deger = _env_dosyasindan()\n    if deger is not None:")
    mod = betikten_modul_yukle(m, "apisix_uygula_v476_mut1")
    kred = tmp_path / "k"
    env = tmp_path / "e"
    kred.write_text(KRED_DEGER + "\n", encoding="utf-8")
    _env_yaz(env)
    monkeypatch.setattr(mod, "KRED_DOSYASI", kred)
    monkeypatch.setattr(mod, "ENV_DOSYASI", env)
    assert mod.anahtar() == ENV_DEGER, "mutant hâlâ credential okuyor — A1 kendini ölçüyor"


def test_C2_MUT_BOS_DEGER_kapisi_kalkarsa_A3_kirmizi(tmp_path, monkeypatch):
    """A3'ün ısırdığı dal: `or None` düşerse boş bir kaynak "ayarlı" sayılır, yedeğe HİÇ
    düşülmez ve araç boş bir `X-API-KEY` ile 401 alır (2026-09-07 sınıfı)."""
    m = _mutant(tmp_path, ARAC, "    return deger or None\n", "    return deger\n")
    mod = betikten_modul_yukle(m, "apisix_uygula_v476_mut2")
    kred = tmp_path / "k2"
    env = tmp_path / "e2"
    kred.write_text("\n   \n", encoding="utf-8")
    _env_yaz(env)
    monkeypatch.setattr(mod, "KRED_DOSYASI", kred)
    monkeypatch.setattr(mod, "ENV_DOSYASI", env)
    assert mod.anahtar() != ENV_DEGER, "mutant yine yedeğe düştü — A3 kendini ölçüyor"


def test_C3_MUT_kanal_raporu_kalkarsa_B1_kirmizi(tmp_path, monkeypatch, capsys):
    """B1'in ısırdığı dal: rapor satırı düşerse operatör hangi kanalın okunduğunu ÖLÇEMEZ ve
    "geçiş yapıldı" bir varsayıma dönüşür."""
    m = _mutant(tmp_path, ARAC, "    kanal_bildir()\n", "")
    mod = betikten_modul_yukle(m, "apisix_uygula_v476_mut3")
    env = tmp_path / "e3"
    _env_yaz(env)
    monkeypatch.setattr(mod, "KRED_DOSYASI", tmp_path / "yok")
    monkeypatch.setattr(mod, "ENV_DOSYASI", env)
    monkeypatch.setattr(mod, "ROTA_DOSYASI", _routes_yaml(tmp_path))
    monkeypatch.setattr(mod.urllib.request, "urlopen",
                        lambda req, timeout=None: _SahteCevap({"list": []}))
    assert mod.main([]) == 0
    assert "admin anahtarı kanalı" not in capsys.readouterr().err


# =================================================================================================
# D) sir_credential_gecis.sh --faz1-apisix / --geri-al-apisix
# =================================================================================================

def _gecis_ortami(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """v439 `_sahte_ortam`ın emsali; ek olarak `/opt/apisix` kökü ve `.env-apisix` tohumu."""
    kok = tmp_path / "kok"
    for d in ("etc/systemd/system/meridian.service.d", "etc/meridian", "opt/meridian",
              "opt/apisix"):
        (kok / d).mkdir(parents=True, exist_ok=True)
    (kok / "opt/meridian/.env").write_text(
        "NOUS_MODEL=sahte/model\nNOUS_ENDPOINT=http://kapi/llm/v1\n", encoding="utf-8")
    _env_yaz(kok / "opt/apisix/.env-apisix")
    binn = tmp_path / "bin"
    binn.mkdir(exist_ok=True)
    (binn / "sudo").write_text('#!/bin/sh\ncase "$1" in chown) exit 0 ;; *) exec "$@" ;; esac\n')
    (binn / "systemctl").write_text(
        '#!/bin/sh\ncase "$*" in\n'
        '  "--version") echo "systemd 255 (255.4-1ubuntu8.4)"; exit 0 ;;\n'
        '  *) exit 0 ;;\nesac\n')
    (binn / "curl").write_text('#!/bin/sh\necho 200\n')
    for f in ("sudo", "systemctl", "curl"):
        (binn / f).chmod(0o755)
    return kok, dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}", SIR_GECIS_KOK=str(kok))


def _kos_gecis(ortam: dict, *args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(GECIS), *args], capture_output=True, text=True,
                          env=ortam, cwd=str(cwd))


def test_D0_betik_sozdizimi_gecerli():
    r = subprocess.run(["bash", "-n", str(GECIS)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_D1_faz1_apisix_KAYNAGI_env_degerinden_yaratir_ve_ENV_SATIRINA_DOKUNMAZ(tmp_path):
    """Faz-1 kanal EKLER, kapatmaz. Burada "kapatmamak" TSK-049'dakinden daha da zorunludur:
    `.env-apisix` satırını kapının KENDİSİ (`config.yaml` `${{APISIX_ADMIN_KEY}}`) okur ve
    silmek kapıyı açılmaz hâle getirirdi."""
    kok, ortam = _gecis_ortami(tmp_path)
    once = (kok / "opt/apisix/.env-apisix").read_bytes()
    r = _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    kred = kok / "etc/meridian/apisix_admin_key"
    assert kred.read_text(encoding="utf-8").strip() == ENV_DEGER
    assert oct(kred.stat().st_mode & 0o777) == "0o400", oct(kred.stat().st_mode & 0o777)
    assert (kok / "opt/apisix/.env-apisix").read_bytes() == once, ".env-apisix DEĞİŞTİ"


def test_D2_faz1_apisix_DEGERI_ARGV_ye_ve_CIKTIYA_koymaz(tmp_path):
    """2026-09-02 vakası (`ps` argv'yi makinedeki herkese gösterir) bu yüzeyde de geçerli."""
    kok, ortam = _gecis_ortami(tmp_path)
    r = _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ENV_DEGER not in (r.stdout + r.stderr), "SIR DEĞERİ BASILDI"


def test_D3_CIFT_SATIR_da_DURUR_ve_HICBIR_SEY_yazmaz(tmp_path):
    """`_deger_dosyala`nın `env` kipindeki kapısı bu yüzeyde de geçerli: iki `^AD=` satırında
    yürürlükteki değer SONuncudur, okuyan İLKİNİ alır. Hangisinin yürürlükte olduğu ÖLÇÜLEMEZ ve
    tahmin etmek uydurmadır."""
    kok, ortam = _gecis_ortami(tmp_path)
    p = kok / "opt/apisix/.env-apisix"
    p.write_text(p.read_text(encoding="utf-8") + f"APISIX_ADMIN_KEY={ENV_DEGER}\n",
                 encoding="utf-8")
    r = _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path)
    assert r.returncode != 0
    assert "ÇİFT SATIR" in r.stderr, r.stderr
    assert not (kok / "etc/meridian/apisix_admin_key").exists()


def test_D4_ALAN_YOKSA_DURUR_ve_HICBIR_SEY_yazmaz(tmp_path):
    """Satır yoksa değer YOKTUR — "1. satırı al" bir TAHMİNDİR ve 2026-09-07'de tam o tahmin
    boş bir değeri 0400 kaynağa yazdı."""
    kok, ortam = _gecis_ortami(tmp_path)
    (kok / "opt/apisix/.env-apisix").write_text("OPENROUTER_API_KEY=SAHTE-OR\n", encoding="utf-8")
    r = _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path)
    assert r.returncode != 0
    assert "DEĞER YOK" in r.stderr, r.stderr
    assert not (kok / "etc/meridian/apisix_admin_key").exists()


def test_D5_geri_al_apisix_KAYNAGI_kaldirir(tmp_path):
    """Geri alma credential kanalını kapatır; araç `.env-apisix` yedeğine düşer. Kaynak dosya
    bir `LoadCredential` kaynağı DEĞİLDİR (henüz), yani kaldırmak hiçbir birimi düşürmez."""
    kok, ortam = _gecis_ortami(tmp_path)
    assert _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path).returncode == 0
    kred = kok / "etc/meridian/apisix_admin_key"
    assert kred.exists()
    r = _kos_gecis(ortam, "--geri-al-apisix", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not kred.exists()
    assert (kok / "opt/apisix/.env-apisix").exists(), "yedek kanal da silindi"


def test_D6_geri_al_apisix_YEDEK_KANAL_yokken_DURUR(tmp_path):
    """Kaldırmak, sırrın okunabildiği TEK kanalı kapatmak olabilir. `.env-apisix` satırı
    yok/değersizse geri alma DURUR — yoksa araç hiçbir kanaldan okuyamaz ve arıza ancak bir
    sonraki `--uygula` denemesinde görünürdü (uydurma yasağı: ölçmeden kapatma)."""
    kok, ortam = _gecis_ortami(tmp_path)
    assert _kos_gecis(ortam, "--faz1-apisix", cwd=tmp_path).returncode == 0
    (kok / "opt/apisix/.env-apisix").write_text("OPENROUTER_API_KEY=SAHTE-OR\n", encoding="utf-8")
    r = _kos_gecis(ortam, "--geri-al-apisix", cwd=tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert (kok / "etc/meridian/apisix_admin_key").exists(), "tek kanal kapatıldı"


def test_D7_durum_FAZ_1C_bacagini_da_raporlar(tmp_path):
    """Operatörün koşacağı İLK komut üç bacağı da göstermeli (v439 I11b'nin kardeşi).
    Raporlamayan bir bacak "kurulu mu?" sorusunu VARSAYIMA bırakır."""
    kok, ortam = _gecis_ortami(tmp_path)
    r = _kos_gecis(ortam, cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Faz-1C" in r.stdout
    assert "/etc/meridian/apisix_admin_key" in r.stdout
    assert "APISIX_ADMIN_KEY" in r.stdout
    assert ENV_DEGER not in (r.stdout + r.stderr), "durum SIR DEĞERİ bastı"


def test_D8_MUT_faz1_apisix_SATIR_ADRESI_okursa_D1_kirmizi(tmp_path):
    """D1'in ısırdığı dal — 2026-09-07 olayının TA KENDİSİ. `sed -n '1{...}'` bir SATIR
    ADRESİDİR, `^AD=` DESENİ değil: `.env-apisix`in 1. satırı bir YORUMDUR ve o yorum
    credential kaynağına yazılırdı."""
    ham = GECIS.read_text(encoding="utf-8")
    eski = '_deger_dosyala "$APISIX_ENVF" "$APISIX_ALAN" "$tmp" env'
    assert ham.count(eski) == 1, ham.count(eski)
    mutant = tmp_path / "mutant.sh"
    mutant.write_text(ham.replace(
        eski, 'sudo sed -n "1{p;q;}" "$APISIX_ENVF" > "$tmp"'), encoding="utf-8")
    kok, ortam = _gecis_ortami(tmp_path)
    r = subprocess.run(["bash", str(mutant), "--faz1-apisix"], capture_output=True, text=True,
                       env=ortam, cwd=str(tmp_path))
    kred = kok / "etc/meridian/apisix_admin_key"
    yazilan = kred.read_text(encoding="utf-8").strip() if kred.exists() else None
    assert yazilan != ENV_DEGER, "mutant yine doğru değeri yazdı — D1 kendini ölçüyor"
    assert r.returncode == 0 or not kred.exists()


# =================================================================================================
# E) ÜÇ YÜZEY AYNI YOLLARI KONUŞUR (tek-kaynak ayrışma çivisi)
# =================================================================================================

def _envanter_kopyalari() -> list[dict]:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["rotasyon_kopyalari"]["kopyalar"]


def test_E1_ARACIN_yollari_ENVANTERDEKI_apisix_admin_kopyalariyla_AYNI():
    """Üç yüzey (araç · rotasyon · envanter) AYNI iki dosyayı konuşmalı. Ayrışırsa: rotasyon bir
    dosyayı döndürür, araç BAŞKA birini okur ve kapı ilk gerçek çağrıda 401 alır — hem de
    rotasyon "başarılı" dedikten saatler sonra (bu betiklerin var olma sebebi olan sınıf)."""
    mod = betikten_modul_yukle(ARAC, "apisix_uygula_v476_yol")
    kopyalar = [k for k in _envanter_kopyalari() if k["alt_komut"] == "apisix-admin"]
    assert len(kopyalar) == 2, kopyalar
    dosya = next(k for k in kopyalar if k["tur"] == "dosya")
    env = next(k for k in kopyalar if k["tur"] == "env")
    assert str(mod.KRED_DOSYASI) == dosya["yol"]
    assert str(mod.ENV_DOSYASI) == env["yol"]
    assert mod.ADMIN_ALAN == env["alan"]
    assert {k["sir"] for k in kopyalar} == {"APISIX_ADMIN_KEY"}


def test_E2_GECIS_BETIGI_ayni_iki_yolu_tasir():
    """Geçiş betiği kaynağı YARATAN taraftır; aracın OKUDUĞU yolla ayrışırsa geçiş "yapıldı"
    raporlanır ve araç yedekten okumaya devam eder — sessiz bir yarım geçiş."""
    mod = betikten_modul_yukle(ARAC, "apisix_uygula_v476_yol2")
    metin = GECIS.read_text(encoding="utf-8")
    assert str(mod.KRED_DOSYASI) in metin
    assert str(mod.ENV_DOSYASI) in metin
    assert mod.ADMIN_ALAN in metin


def test_E3_ROTASYON_BETIGI_ayni_iki_kopyayi_yazar():
    """`--kopyalar` GERÇEKTEN koşturulur (metin grep'lemek beyanı ölçer, davranışı değil)."""
    mod = betikten_modul_yukle(ARAC, "apisix_uygula_v476_yol3")
    r = subprocess.run(["bash", str(ROTASYON), "--kopyalar"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    satirlar = [s.split() for s in r.stdout.strip().splitlines()]
    apisix = [s for s in satirlar if s[0] == "apisix-admin"]
    assert len(apisix) == 2, apisix
    assert {s[1] for s in apisix} == {"APISIX_ADMIN_KEY"}
    dosya = next(s for s in apisix if s[2] == "dosya")
    env = next(s for s in apisix if s[2] == "env")
    assert dosya[3] == str(mod.KRED_DOSYASI)
    assert env[3] == str(mod.ENV_DOSYASI) and env[4] == mod.ADMIN_ALAN
