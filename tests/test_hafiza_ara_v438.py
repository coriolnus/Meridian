"""test_hafiza_ara_v438.py — TSK-167 dilim-1: EDG-067 taban indeksi üzerinde ARAMA CLI'ı,
A1 sarmalayıcısı ve haftalık tazeleme birimi (pano yüzeyi dilim-2'de).

NE ÖLÇÜLÜR VE NE ÖLÇÜLEMEZ — sınır baştan yazılır, çünkü bu dosyanın yeşili "arama çalışıyor"
DEMEZ. Gerçek arama üç dış bileşene bağlı: `onnxruntime` (bge-m3 ONNX oturumu), `tokenizers`
ve `sqlite_vec` uzantısı. Yerel macOS Python'ında ÜÇÜ DE YOK; dahası bu yorumcunun `sqlite3`
modülü `enable_load_extension` DESTEĞİ OLMADAN derlenmiş (taban_indeks'in `vec_baglan`ı bu iki
arızayı zaten AYRI AYRI adlandırıyor). Yani burada ölçülen şey SÖZLEŞMEdir: hangi argümanlar,
hangi çıktı biçimi, hangi çıkış kodu, hangi süzgeç aritmetiği. Gerçek koşum A1'de Rol-1'e ait
(brief S3) ve bu dosya onun YERİNE GEÇMEZ.

Bu yüzden arama kolu sahte bir `taban_hazirla`/`taban_sorgu` çiftiyle sürülür: CLI'ın kendi
gövdesi (süzgeç, kesit, biçim, çıkış kodu) gerçek, gömme/vektör katmanı sahte. Sahtelenen sınır
tam olarak dış bağımlılığın başladığı yerdir — bir satır daha içeriden sahtelenseydi çivi kendi
kodunu değil kendi kurgusunu ölçerdi.

TERFİ KOLU İSE GERÇEKTİR VE BU BİLİNÇLİDİR: haftalık tazelemenin "%90 satır kapısı" mantığı
düz `sqlite3` ile ölçülebiliyor (`chunk` NORMAL bir tablodur, vec0 uzantısı gerekmez), o yüzden
taban_terfi çivileri gerçek dosyalar üzerinde gerçek terfi/bırakma kararını koşturur.

KAPSAM (brief görev 1-4):
  1. hafiza_ara.py   — arama CLI'ı (çiviler A-F, H)
  2. taban_terfi.py  — %90 kapısı + atomik terfi (çiviler J) [brief'ten SAPMA, raporda gerekçeli]
  3. hafiza_ara.sh   — A1 sarmalayıcısı (çiviler G)
  4. hindsight-taban-tazele.service/.timer — haftalık tazeleme (çiviler K, L)
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sqlite3

import pytest

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
KIYAS_DIZIN = REPO / "research" / "olcumler" / "edg067_hindsight_faz1"
ARA_YOL = KIYAS_DIZIN / "hafiza_ara.py"
TERFI_YOL = KIYAS_DIZIN / "taban_terfi.py"
SARMAL_YOL = REPO / "deploy" / "hindsight" / "hafiza_ara.sh"
SERVICE_YOL = REPO / "deploy" / "hindsight" / "hindsight-taban-tazele.service"
TIMER_YOL = REPO / "deploy" / "hindsight" / "hindsight-taban-tazele.timer"

#: Brief'in donuk değerleri — buradan TÜRETİLİR, tekrar yazılmaz (tek-kaynak refleksi).
KESIT_TAVANI = 240
ADAY_KATI = 4
ESIK_ORAN = 0.9


# ==================================================================================================
# ORTAK — sahte gömme/vektör katmanı
# ==================================================================================================
def _kunye():
    """`kunye_oku`nun döndüreceği şekil (taban_indeks'in künye yazımından TÜRETİLDİ)."""
    return {"head_commit": "abc123def456", "dosya_sayisi": 121, "chunk_sayisi": 3582,
            "kurulum_suresi_s": 611.4, "boyut": 1024, "uretim_ts": "2026-09-07T03:41:02Z"}


def _sonuc(i, dosya, bolum, metin, mesafe):
    """taban_indeks'in `en_yakin` satır şekli — CLI onu HAM geçirmekle yükümlü."""
    return {"id": i, "dosya": dosya, "bolum": bolum, "metin": metin,
            "blob_sha": "%040x" % i, "mesafe": mesafe}


@pytest.fixture
def ara():
    """Betiği KAYNAKTAN yükler (bayat `__pycache__` tuzağı — ops/sasi_yukleyici başlığı)."""
    assert ARA_YOL.exists(), f"arama CLI'ı YOK: {ARA_YOL}"
    return betikten_modul_yukle(ARA_YOL, "hafiza_ara_v438")


@pytest.fixture
def terfi():
    assert TERFI_YOL.exists(), f"terfi betiği YOK: {TERFI_YOL}"
    return betikten_modul_yukle(TERFI_YOL, "taban_terfi_v438")


def _patchle(ara, monkeypatch, sonuclar, *, kunye=None, hata=None, defter=None):
    """Sahte `taban_hazirla`/`taban_sorgu`. Dönen liste: kapatma çağrılarının defteri."""
    kapatildi = []

    def sahte_hazirla(db_yolu, model_dir, **kw):
        if hata is not None:
            raise hata
        return (_kunye() if kunye is None else kunye), ("SAHTE_DB", "SAHTE_GOMUCU"), \
            lambda: kapatildi.append(True)

    def sahte_sorgu(ortam, soru, k):
        if defter is not None:
            defter.append({"ortam": ortam, "soru": soru, "k": k})
        return list(sonuclar)

    monkeypatch.setattr(ara, "taban_hazirla", sahte_hazirla)
    monkeypatch.setattr(ara, "taban_sorgu", sahte_sorgu)
    return kapatildi


def _satirlar(cikti):
    """Künye/şerh satırları (`#` önekli) AYRILIR — sonuç satırı sayımı onlara kör olmalı."""
    ham = [s for s in cikti.splitlines() if s.strip()]
    return [s for s in ham if not s.startswith("#")]


def _kunye_satirlari(cikti):
    return [s for s in cikti.splitlines() if s.startswith("#")]


def _alanlar(satir):
    return satir.split(" · ", 4)


# ==================================================================================================
# A — ÇIKTI BİÇİMİ
# ==================================================================================================
def test_uc_sonuc_uc_satir_basar(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [
        _sonuc(1, "docs/A.md", "§1 Giriş", "alfa", 0.1234),
        _sonuc(2, "docs/B.md", "§2 Orta", "beta", 0.5),
        _sonuc(3, "research/cards/C.yaml", "", "gama", 0.98765),
    ])
    rc = ara.main(["--db", "/yok/taban.sqlite", "--model-dir", "/yok/model", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    assert len(_satirlar(out)) == 3, out


def test_mesafe_uc_ondalik_basilir(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "alfa", 0.1234567)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    alan = _alanlar(_satirlar(capsys.readouterr().out)[0])
    assert alan[1] == "0.123", alan


def test_kesit_240_karakterle_sinirli_ve_bosluk_katlanmis(ara, monkeypatch, capsys):
    uzun = ("satır bir\n\n   satır   iki\t\tsonu " + "x" * 400)
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", uzun, 0.4)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    kesit = _alanlar(_satirlar(capsys.readouterr().out)[0])[4]
    assert len(kesit) <= KESIT_TAVANI, len(kesit)
    assert "\n" not in kesit and "\t" not in kesit and "  " not in kesit, repr(kesit[:80])
    assert kesit.startswith("satır bir satır iki sonu ")


def test_kunye_ilk_satirda_uretim_ts_ve_head_commit_tasir(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "alfa", 0.4)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    ilk = capsys.readouterr().out.splitlines()[0]
    assert ilk.startswith("#"), ilk
    assert "2026-09-07T03:41:02Z" in ilk and "abc123def456" in ilk, ilk


def test_kunye_eksik_alani_uydurmaz(ara, monkeypatch, capsys):
    """Uydurma yasağı: künyede olmayan alan için sıfır/varsayılan basılmaz, `None` basılır."""
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "alfa", 0.4)],
             kunye={"head_commit": "deadbee"})
    ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    ilk = capsys.readouterr().out.splitlines()[0]
    assert "uretim_ts=None" in ilk, ilk


def test_kapat_her_kosumda_cagrilir(ara, monkeypatch, capsys):
    kapatildi = _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "alfa", 0.4)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    capsys.readouterr()
    assert kapatildi == [True], "bağlantı kapatılmadı — sqlite tanıtıcısı sızıyor"


# ==================================================================================================
# B — `--json` ŞEMASI
# ==================================================================================================
def test_json_stdoutu_ham_liste_ve_ayristirilabilir(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [
        _sonuc(7, "docs/A.md", "§1", "alfa", 0.25),
        _sonuc(8, "docs/B.md", "§2", "beta", 0.35),
    ])
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "--json", "soru"])
    yak = capsys.readouterr()
    assert rc == 0
    veri = json.loads(yak.out)
    assert isinstance(veri, list) and len(veri) == 2
    assert set(veri[0]) == {"id", "dosya", "bolum", "metin", "blob_sha", "mesafe"}, veri[0]
    assert veri[0]["id"] == 7 and veri[0]["mesafe"] == 0.25


def test_json_modunda_kunye_stdouta_karismaz_stderre_gider(ara, monkeypatch, capsys):
    """`--json` boru hattına gider; künye stdout'a düşseydi her `jq` çağrısı kırılırdı."""
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "alfa", 0.25)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "--json", "soru"])
    yak = capsys.readouterr()
    assert not yak.out.lstrip().startswith("#"), yak.out[:120]
    assert "abc123def456" in yak.err, yak.err


def test_json_metni_kesilmez_ham_kalir(ara, monkeypatch, capsys):
    """Kesit YALNIZ tablo görünümünün işidir — `--json` ham metni taşır (bedel yasası: pano
    dilim-2 tam metni isteyecek, kesit orada bir kayıp olurdu)."""
    uzun = "y" * 900
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", uzun, 0.25)])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "--json", "soru"])
    veri = json.loads(capsys.readouterr().out)
    assert veri[0]["metin"] == uzun


# ==================================================================================================
# C — `--dosya` SÜZGECİ
# ==================================================================================================
def test_dosya_onekiyle_suzer_ve_k_kati_aday_ceker(ara, monkeypatch, capsys):
    defter = []
    _patchle(ara, monkeypatch, [
        _sonuc(1, "docs/A.md", "§1", "a", 0.1),
        _sonuc(2, "research/cards/X.yaml", "", "b", 0.2),
        _sonuc(3, "docs/B.md", "§2", "c", 0.3),
        _sonuc(4, "MERIDIAN_ENGINEERING_LOG.md", "", "d", 0.4),
    ], defter=defter)
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "-k", "2", "--dosya", "docs/", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    assert defter[0]["k"] == 2 * ADAY_KATI, defter
    satir = _satirlar(out)
    assert len(satir) == 2
    assert all(_alanlar(s)[2].startswith("docs/") for s in satir), satir


def test_suzulen_sayisi_raporlanir(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [
        _sonuc(1, "docs/A.md", "§1", "a", 0.1),
        _sonuc(2, "research/cards/X.yaml", "", "b", 0.2),
        _sonuc(3, "state/goal.yaml", "", "c", 0.3),
    ])
    ara.main(["--db", "/yok", "--model-dir", "/yok", "-k", "5", "--dosya", "docs/", "soru"])
    out = capsys.readouterr().out
    serh = [s for s in _kunye_satirlari(out) if "süzül" in s.casefold()]
    assert len(serh) == 1, out
    assert "2 süzüldü" in serh[0], serh[0]


def test_suzgec_ONEKTIR_yol_ortasindaki_eslesme_saymaz(ara, monkeypatch, capsys):
    """MUTASYON TURU BULGUSU (M6): `startswith(onek)` → `onek in dosya` mutasyonu ilk turda
    HİÇBİR çiviyi ısırmadı — fikstürlerin hepsinde önek zaten yolun BAŞINDAYDI, yani "önek" ile
    "içerir" ayırt edilemiyordu.

    Ayrım gerçektir ve sessizdir: `--dosya cards/` içerik araması olsaydı
    `research/cards/X.yaml`i getirirdi ve operatör bunu bir arıza olarak GÖRMEZDİ — yalnız
    süzgecin ne yaptığını yanlış bilirdi. Sözleşme ÖNEKtir; çivi artık farkı ölçüyor."""
    _patchle(ara, monkeypatch, [
        _sonuc(1, "research/cards/X.yaml", "", "a", 0.1),
        _sonuc(2, "docs/cards/Y.md", "", "b", 0.2),
    ])
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "--dosya", "cards/", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    assert _satirlar(out) == ["sonuç yok"], (
        "yol ORTASINDAKİ `cards/` eşleşti — süzgeç önek değil içerik araması yapıyor")


def test_dosya_verilmezse_aday_kati_uygulanmaz(ara, monkeypatch, capsys):
    """Bedel: `k×4` yalnız süzgeç varken ödenir — süzgeçsiz koşumda dört kat vektör taraması
    boşuna gecikmedir (taban p50 0,62 s ölçümü, EDG-067)."""
    defter = []
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "a", 0.1)], defter=defter)
    ara.main(["--db", "/yok", "--model-dir", "/yok", "-k", "3", "soru"])
    capsys.readouterr()
    assert defter[0]["k"] == 3, defter


def test_suzgec_hicbir_sonucu_birakmazsa_sonuc_yok_ve_rc0(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [_sonuc(1, "docs/A.md", "§1", "a", 0.1)])
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "--dosya", "ops/", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "sonuç yok" in out
    assert _satirlar(out) == ["sonuç yok"], out


# ==================================================================================================
# D — BOŞ SONUÇ
# ==================================================================================================
def test_bos_sonuc_sonuc_yok_basar_rc0(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [])
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    out = capsys.readouterr().out
    assert rc == 0, "boş sonuç bir ARIZA değildir — rc 0"
    assert "sonuç yok" in out


def test_bos_sonuc_json_modunda_bos_liste(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [])
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "--json", "soru"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == []


# ==================================================================================================
# E — ARIZA YOLU: RuntimeError METNİ AYNEN, rc 1 · KULLANIM rc 2
# ==================================================================================================
UZANTI_METNI = ("bu Python'ın `sqlite3` modülü `enable_load_extension` desteği OLMADAN "
                "derlenmiş — sqlite-vec yüklenemez")


def test_taban_hazirla_runtimeerror_metni_aynen_rc1(ara, monkeypatch, capsys):
    _patchle(ara, monkeypatch, [], hata=RuntimeError(UZANTI_METNI))
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    yak = capsys.readouterr()
    assert rc == 1
    assert yak.err.strip() == UZANTI_METNI, repr(yak.err)
    assert yak.out.strip() == "", "arıza turunda stdout'a künye/sonuç basılmaz"


def test_indeks_yoksa_filenotfound_da_rc1(ara, monkeypatch, capsys):
    """`taban_hazirla` eksik indeks/model için `FileNotFoundError` atar; operatör açısından bu da
    aynı sınıftır (girdi arızası) ve aynı kapıdan çıkmalıdır."""
    metin = "taban indeksi YOK: /opt/hindsight/edg067/taban.sqlite"
    _patchle(ara, monkeypatch, [], hata=FileNotFoundError(metin))
    rc = ara.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    assert rc == 1
    assert capsys.readouterr().err.strip() == metin


def test_soru_verilmezse_kullanim_rc2(ara):
    with pytest.raises(SystemExit) as e:
        ara.main(["--db", "/yok", "--model-dir", "/yok"])
    assert e.value.code == 2


def test_k_sifir_ya_da_negatif_kullanim_rc2(ara):
    with pytest.raises(SystemExit) as e:
        ara.main(["--db", "/yok", "--model-dir", "/yok", "-k", "0", "soru"])
    assert e.value.code == 2


# ==================================================================================================
# F — `meridian` İTHAL EDİLMEZ (obs'a ulaşan pytest-dışı koşum sınıfı kapatılır)
# ==================================================================================================
@pytest.mark.parametrize("yol", [ARA_YOL, TERFI_YOL], ids=["hafiza_ara", "taban_terfi"])
def test_meridian_ithal_edilmez_ast(yol):
    agac = ast.parse(yol.read_text(encoding="utf-8"), str(yol))
    ithal = []
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            ithal += [a.name for a in d.names]
        elif isinstance(d, ast.ImportFrom) and d.module:
            ithal.append(d.module)
    kirli = [m for m in ithal if m == "meridian" or m.startswith("meridian.")]
    assert not kirli, (
        f"{yol.name} `meridian` ithal ediyor: {kirli} — bu betik pytest DIŞINDA koşar ve "
        "`meridian.obs` üzerinden canlı yerel deftere yazardı (3 vaka, 2026-08-30)")


@pytest.mark.parametrize("yol", [ARA_YOL, TERFI_YOL], ids=["hafiza_ara", "taban_terfi"])
def test_meridian_ithal_edilmez_metin(yol):
    """AST'in göremeyeceği bir yol (`__import__`, `importlib`) metin tarafından da kapatılır."""
    ihlal = [s for s in yol.read_text(encoding="utf-8").splitlines()
             if re.match(r"^\s*(import|from)\s+meridian\b", s)
             or re.search(r"""__import__\(\s*["']meridian""", s)
             or re.search(r"""import_module\(\s*["']meridian""", s)]
    assert not ihlal, ihlal


@pytest.mark.parametrize("yol", [ARA_YOL, TERFI_YOL], ids=["hafiza_ara", "taban_terfi"])
def test_sir_yuzeyi_yok(yol):
    """Bu iki betik hiçbir kimlik okumaz: anahtar dosyası da, `Authorization` başlığı da yok."""
    metin = yol.read_text(encoding="utf-8")
    for yasak in ("--key-file", "Authorization", "api_key", "SECRET"):
        assert yasak not in metin, f"{yol.name}: sır yüzeyi `{yasak}`"


def test_kiyas_kostan_ithal_eder_kopyalamaz(ara):
    """Sözleşme: arama CLI'ı `taban_hazirla`/`taban_sorgu`yu İTHAL eder. Kopyalansaydı iki gövde
    sessizce ayrışırdı (tek-kaynak yasası).

    KİMLİK KIYASI NEDEN MODÜL İÇİNDEN: kaynaktan yükleyici her çağrıda YENİDEN derler (bayat
    pyc'ye bakmamak için), yani ayrı ayrı yüklenmiş iki kiyas_kos'un `__code__`ları eşit AMA aynı
    nesne DEĞİLDİR. Ölçülebilir olan şey, CLI'ın kendi yüklediği modülden aldığıdır."""
    assert pathlib.Path(ara.KIYAS.__file__).name == "kiyas_kos.py", ara.KIYAS.__file__
    assert ara.taban_hazirla is ara.KIYAS.taban_hazirla
    assert ara.taban_sorgu is ara.KIYAS.taban_sorgu
    kaynak = ARA_YOL.read_text(encoding="utf-8")
    for ad in ("def taban_hazirla", "def taban_sorgu", "def en_yakin", "def paketle"):
        assert ad not in kaynak, f"gövde KOPYALANMIŞ: {ad}"


# ==================================================================================================
# G0 — OPERATÖRÜN KOŞACAĞI BİÇİM: GERÇEK SÜREÇ, SAHTELEME YOK
# ==================================================================================================
# Yukarıdaki her şey `main()`i İÇERİDEN çağırır. O katman `__main__` muhafızını, argparse
# bağlantısını ve gerçek `taban_hazirla`nın arıza yolunu HİÇ görmez — ve tam bu boşlukta 18 çivi
# yeşilken bir ops aracının `--uygula` bayrağı sessizce yok sayılmıştı (vaka 2026-08-30). Bu üç
# çivi aracı operatörün yazacağı gibi, ayrı bir süreç olarak koşturur.
#
# ONNX/sqlite-vec GEREKMEZ ve bu ÖLÇÜLDÜ, umut edilmedi: `taban_hazirla` ÖNCE model dizinini
# sınar ve yoksa `FileNotFoundError` atar — ağır ithal o satıra hiç ulaşmaz.
def _kos(*argv):
    import subprocess
    import sys
    return subprocess.run([sys.executable, str(ARA_YOL), *argv],
                          capture_output=True, text=True, cwd=str(REPO))


def test_gercek_surecte_eksik_model_dizini_rc1_ve_metin_aynen(tmp_path):
    r = _kos("--db", str(tmp_path / "yok.sqlite"), "--model-dir", str(tmp_path / "yokdizin"),
             "bir soru")
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert r.stderr.strip().startswith("model dizini YOK:"), repr(r.stderr)
    assert r.stdout.strip() == "", r.stdout


def test_gercek_surecte_soru_eksikse_rc2(tmp_path):
    r = _kos("--db", str(tmp_path / "yok.sqlite"), "--model-dir", str(tmp_path))
    assert r.returncode == 2, (r.returncode, r.stderr)


def test_gercek_surecte_help_rc0_ve_tum_bayraklari_gosterir():
    r = _kos("--help")
    assert r.returncode == 0, r.stderr
    for bayrak in ("--db", "--model-dir", "-k", "--dosya", "--json"):
        assert bayrak in r.stdout, (bayrak, r.stdout)


# ==================================================================================================
# G — A1 SARMALAYICISI
# ==================================================================================================
SNAPSHOT = ("/opt/hindsight/hf-cache/hub/models--BAAI--bge-m3/snapshots/"
            "5617a9f61b028005a4858fdac845db406aefb181")


def test_sarmalayici_venv_python_ve_dogru_betigi_cagirir():
    metin = SARMAL_YOL.read_text(encoding="utf-8")
    assert "/opt/hindsight/venv/bin/python" in metin
    assert "/opt/meridian/research/olcumler/edg067_hindsight_faz1/hafiza_ara.py" in metin


def test_sarmalayici_db_model_ve_omp_tasir():
    metin = SARMAL_YOL.read_text(encoding="utf-8")
    assert "--db /opt/hindsight/edg067/taban.sqlite" in metin
    assert SNAPSHOT in metin
    assert "OMP_NUM_THREADS=2" in metin, "kos_taban.sh emsali: 4 OCPU'da 2 iş parçacığı"


def test_sarmalayici_argumanlari_gecirir_ve_cikis_kodunu_korur():
    """`"$@"` olmadan `-k`/`--json`/`--dosya` sarmalayıcıda ölür; `exec` olmadan çıkış kodu
    sözleşmesi (0/1/2) kabuğun kendi kodunun arkasında kaybolabilir."""
    metin = SARMAL_YOL.read_text(encoding="utf-8")
    assert '"$@"' in metin
    assert re.search(r"^exec\s", metin, re.M), "exec YOK — çıkış kodu sarmalayıcıdan geçmeli"


def test_sarmalayici_bash_n_temiz():
    import subprocess
    r = subprocess.run(["bash", "-n", str(SARMAL_YOL)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ==================================================================================================
# H — TERFİ BETİĞİ: %90 KAPISI, ATOMİKLİK, `.onceki`
# ==================================================================================================
def _db_yaz(yol, satir_sayisi):
    db = sqlite3.connect(str(yol))
    db.execute("CREATE TABLE chunk(id INTEGER PRIMARY KEY, metin TEXT NOT NULL)")
    db.executemany("INSERT INTO chunk(id, metin) VALUES(?, ?)",
                   [(i + 1, f"m{i}") for i in range(satir_sayisi)])
    db.commit()
    db.close()
    return yol


def test_esik_ustunde_terfi_eder_ve_onceki_saklanir(terfi, tmp_path, capsys):
    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz(hedef, 100)
    _db_yaz(yeni, 95)
    rc = terfi.main(["--yeni", str(yeni), "--hedef", str(hedef)])
    capsys.readouterr()
    assert rc == 0
    assert not yeni.exists(), "terfi sonrası `.yeni` kalmamalı (yarım indeks karışır)"
    assert hedef.exists() and (tmp_path / "taban.sqlite.onceki").exists()
    db = sqlite3.connect(str(hedef))
    assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 95
    db.close()
    onceki = sqlite3.connect(str(tmp_path / "taban.sqlite.onceki"))
    assert onceki.execute("SELECT count(*) FROM chunk").fetchone()[0] == 100
    onceki.close()


def test_esik_altinda_birakir_neden_basar_rc1(terfi, tmp_path, capsys):
    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz(hedef, 100)
    _db_yaz(yeni, 89)
    rc = terfi.main(["--yeni", str(yeni), "--hedef", str(hedef)])
    out = capsys.readouterr().out
    assert rc == 1, "bırakma SESSİZ olamaz — birim `failed` olmalı ki /api/infra görsün"
    assert yeni.exists(), "bırakılan `.yeni` teşhis için YERİNDE kalır"
    db = sqlite3.connect(str(hedef))
    assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 100, "hedef DOKUNULMAMALI"
    db.close()
    assert "89" in out and "100" in out, out


def test_esik_tam_sinirda_terfi_eder(terfi, tmp_path, capsys):
    """`>=` sözleşmesi: tam %90 KABUL. Sınırın hangi tarafta olduğu ölçülmeden bırakılamaz."""
    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz(hedef, 100)
    _db_yaz(yeni, 90)
    assert terfi.main(["--yeni", str(yeni), "--hedef", str(hedef)]) == 0
    capsys.readouterr()


def test_hedef_yokken_kosulsuz_terfi(terfi, tmp_path, capsys):
    """İlk kurulum: kıyaslanacak eski satır sayısı YOK — oran hesaplanamaz, uydurulmaz."""
    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz(yeni, 7)
    rc = terfi.main(["--yeni", str(yeni), "--hedef", str(hedef)])
    capsys.readouterr()
    assert rc == 0 and hedef.exists() and not yeni.exists()
    assert not (tmp_path / "taban.sqlite.onceki").exists(), "yokken `.onceki` UYDURULMAZ"


def test_yeni_yoksa_rc1(terfi, tmp_path, capsys):
    hedef = _db_yaz(tmp_path / "taban.sqlite", 10)
    rc = terfi.main(["--yeni", str(tmp_path / "taban.sqlite.yeni"), "--hedef", str(hedef)])
    assert rc == 1
    assert "yok" in capsys.readouterr().out.casefold()


def test_yeni_bozuksa_sifir_saymaz_rc1(terfi, tmp_path, capsys):
    """Uydurma yasağı: `chunk` tablosu olmayan bir dosya "0 satır" DEĞİLDİR, ÖLÇÜLEMEZDİR."""
    hedef = _db_yaz(tmp_path / "taban.sqlite", 10)
    (tmp_path / "taban.sqlite.yeni").write_bytes(b"bu bir sqlite dosyasi degil")
    rc = terfi.main(["--yeni", str(tmp_path / "taban.sqlite.yeni"), "--hedef", str(hedef)])
    out = capsys.readouterr().out
    assert rc == 1
    db = sqlite3.connect(str(hedef))
    assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 10
    db.close()
    assert "chunk" in out.casefold(), out


def test_ikinci_terfi_onceki_uzerine_yazar_tek_surum(terfi, tmp_path, capsys):
    """"eski dosya `.onceki` olarak BİR SÜRÜM saklanır" — ikinci tur üçüncü bir kopya bırakmaz."""
    hedef = _db_yaz(tmp_path / "taban.sqlite", 100)
    _db_yaz(tmp_path / "taban.sqlite.yeni", 100)
    assert terfi.main(["--yeni", str(tmp_path / "taban.sqlite.yeni"),
                       "--hedef", str(hedef)]) == 0
    _db_yaz(tmp_path / "taban.sqlite.yeni", 102)
    assert terfi.main(["--yeni", str(tmp_path / "taban.sqlite.yeni"),
                       "--hedef", str(hedef)]) == 0
    capsys.readouterr()
    kalanlar = sorted(p.name for p in tmp_path.iterdir())
    assert kalanlar == ["taban.sqlite", "taban.sqlite.onceki"], kalanlar
    onceki = sqlite3.connect(str(tmp_path / "taban.sqlite.onceki"))
    assert onceki.execute("SELECT count(*) FROM chunk").fetchone()[0] == 100
    onceki.close()


def test_yerine_koyma_duserse_hedef_adi_KAYBOLMAZ(terfi, tmp_path, monkeypatch):
    """MUTASYON TURU BULGUSU (M11): `os.link` → `os.rename` mutasyonu ilk turda hiçbir çiviyi
    ısırmadı, çünkü İKİ SIRA DA AYNI SON DURUMU üretiyor. Ayrım yalnız ARADA görünür ve tam da
    kodun iddia ettiği değişmez odur: hedef ADI hiçbir an kaybolmaz.

    Ölçüm yolu: `os.replace` DÜŞÜRÜLÜR. Sert bağ sırasında hedef hâlâ YERİNDEDİR (bağ yalnız
    ikinci bir ad ekledi); `rename` sırasında hedef GİTMİŞTİR — yani yarım kalan bir terfi,
    canlı indeksi yok eder. Pencere haftada bir, 03:30'da, kimsenin bakmadığı anda açılır."""
    import os as _os

    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz(hedef, 100)
    _db_yaz(yeni, 100)

    class _DusenOs:
        link = staticmethod(_os.link)

        @staticmethod
        def replace(a, b):
            raise OSError("mutasyon: yerine koyma yarıda düştü")

    monkeypatch.setattr(terfi, "os", _DusenOs)
    with pytest.raises(OSError):
        terfi.terfi_et(yeni, hedef)
    assert hedef.exists(), (
        "yerine koyma düştü ve HEDEF KAYBOLDU — canlı indeks yarım bir terfide yok oluyor")
    db = sqlite3.connect(str(hedef))
    assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 100
    db.close()


def test_esik_orani_parametredir_ve_varsayilani_09(terfi, tmp_path, capsys):
    hedef = _db_yaz(tmp_path / "taban.sqlite", 100)
    _db_yaz(tmp_path / "taban.sqlite.yeni", 50)
    assert terfi.main(["--yeni", str(tmp_path / "taban.sqlite.yeni"),
                       "--hedef", str(hedef), "--esik-oran", "0.4"]) == 0
    capsys.readouterr()
    assert terfi.ESIK_ORAN == ESIK_ORAN


# ==================================================================================================
# K — TAZELEME BİRİMİ (.service)
# ==================================================================================================
def _bolumler(metin):
    """GERÇEK bölüm başlıkları (`[Unit]` gibi SATIRIN KENDİSİ olanlar).

    YORUM-KÖR OLAMAZ: iki birim dosyası da anlatım metninde `[Install] BÖLÜMÜ BİLEREK YOK` ve
    `timer birimlerinin [Service] bölümü olmaz` cümlelerini geçiriyor — ham `in` araması onları
    bölüm sanıyordu (ilk koşumda ölçüldü, v418'in `_yonergeler`inin öğrendiği dersin aynısı bir
    kat yukarıda). Ayraç bölümü SATIR olarak tanır, metin olarak değil."""
    return {s.strip()[1:-1] for s in metin.splitlines()
            if s.strip().startswith("[") and s.strip().endswith("]")}


def _yonergeler(metin):
    """Yorum-kör yönerge ayrıştırıcı: `#` ile başlayan satır YÖNERGE DEĞİLDİR (v418 emsali).
    Aynı anahtar birden çok kez geçebilir (ExecStart) — değerler LİSTE olarak toplanır."""
    out = {}
    for satir in metin.splitlines():
        s = satir.strip()
        if not s or s.startswith("#") or s.startswith("[") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out.setdefault(k.strip(), []).append(v.strip())
    return out


def test_service_kullanici_ve_tip():
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    assert y["Type"] == ["oneshot"]
    assert y["User"] == ["ubuntu"]


def test_service_readwritepaths_iki_dizinle_sinirli():
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    assert y["ReadWritePaths"] == ["/opt/hindsight/edg067 /opt/hindsight/ingest067"], y.get(
        "ReadWritePaths")


def test_service_sertlestirme_karne_emsalini_tasir():
    """Sertleştirme birim DOĞARKEN yazılır — `meridian-brifing.service` bir tur geciktiği için
    "filoda sertleştirmesi olmayan tek birim" hâli doğmuştu."""
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    beklenen = {
        "NoNewPrivileges": "true", "ProtectSystem": "strict", "ProtectHome": "read-only",
        "PrivateTmp": "true", "ProtectKernelTunables": "true", "ProtectKernelModules": "true",
        "ProtectKernelLogs": "true", "ProtectClock": "true", "ProtectControlGroups": "true",
        "ProtectHostname": "true", "RestrictNamespaces": "true", "RestrictSUIDSGID": "true",
        "RestrictRealtime": "true", "LockPersonality": "true",
        "SystemCallArchitectures": "native", "SystemCallFilter": "@system-service",
    }
    eksik = {k: v for k, v in beklenen.items() if y.get(k) != [v]}
    assert not eksik, eksik
    assert y.get("CapabilityBoundingSet") == [""], y.get("CapabilityBoundingSet")


def test_service_uc_adimi_dogru_sirada_kosar():
    """Sıra SÖZLEŞMEDİR: korpus paketi → indeks → terfi. `-` öneksiz ExecStart'lar ilk düşüşte
    durur, yani yarım bir paketten indeks kurulmaz."""
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    adimlar = y["ExecStart"]
    assert len(adimlar) == 3, adimlar
    assert "manifest_uret.py" in adimlar[0]
    assert "taban_indeks.py" in adimlar[1]
    assert "taban_terfi.py" in adimlar[2]
    assert not any(a.startswith("-") for a in adimlar), "`-` öneki çıkış kodunu YUTAR"


def test_service_yeni_dosyaya_kurar_hedefe_degil():
    """`taban_indeks.py` var olan hedefin üstüne YAZMAZ (`HEDEF VAR` ile düşer) — bu yüzden
    indeks `.yeni`ye kurulur ve terfi kapısından geçer."""
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    indeks = y["ExecStart"][1]
    assert "--db /opt/hindsight/edg067/taban.sqlite.yeni" in indeks, indeks
    on = " ".join(y.get("ExecStartPre", []))
    assert "taban.sqlite.yeni" in on, "bayat `.yeni` silinmezse ikinci tur `HEDEF VAR` ile düşer"


def test_service_paket_dizini_ingest067_altinda():
    """manifest_uret.py tar'ı ÇIKTI DİZİNİNİN ÜST DİZİNİNE yazar (ölçüldü) — çıktı doğrudan
    /opt/hindsight/ingest067 olsaydı tar /opt/hindsight'a düşer ve ProtectSystem=strict altında
    EROFS alırdı. Bir alt dizin seçmek bunu ReadWritePaths'in İÇİNDE tutar."""
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    paket = y["ExecStart"][0].split()
    cikti = paket[2]
    assert cikti.startswith("/opt/hindsight/ingest067/"), cikti
    assert cikti != "/opt/hindsight/ingest067", "kartın donuk korpusunun üstüne yazılmaz"
    assert paket[3] == "/opt/meridian", paket


def test_service_omp_iki_is_parcacigi():
    y = _yonergeler(SERVICE_YOL.read_text(encoding="utf-8"))
    assert "OMP_NUM_THREADS=2" in y.get("Environment", []), y.get("Environment")


def test_service_environment_satirinda_satir_sonu_yorumu_yok():
    """systemd `Environment=` satırında `#`i yorum SAYMAZ — değişken SESSİZCE boş kalır
    (2026-08-01 vakası; v174'ün aynı kapısı yalnız deploy/oracle-a1'i tarıyor)."""
    for anahtar in ("Environment", "EnvironmentFile"):
        for v in _yonergeler(SERVICE_YOL.read_text(encoding="utf-8")).get(anahtar, []):
            assert "#" not in v, f"{anahtar}={v!r}"


def test_service_install_bolumu_yok():
    """Tetik YALNIZ timer'dır; `[Install]` olsaydı `systemctl enable <service>` sessizce ikinci
    bir açılış tetiği eklerdi (karne emsali)."""
    assert "Install" not in _bolumler(SERVICE_YOL.read_text(encoding="utf-8"))


# ==================================================================================================
# L — TAZELEME TİMER'I
# ==================================================================================================
ONCALENDAR_RE = re.compile(
    r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \*-\*-\* (\d{2}):(\d{2}):(\d{2}) UTC$")


def test_timer_oncalendar_sozdizimi_ve_slotu():
    """`systemd-analyze calendar` yerelde YOK — sözdizimi düzenli ifadeyle ölçülür (yapısal
    çivi: yanlış yazılmış bir `OnCalendar` systemd'de birimi REDDETTİRİR ve tetik SESSİZCE
    hiç kurulmaz)."""
    y = _yonergeler(TIMER_YOL.read_text(encoding="utf-8"))
    assert len(y.get("OnCalendar", [])) == 1, y.get("OnCalendar")
    m = ONCALENDAR_RE.match(y["OnCalendar"][0])
    assert m, y["OnCalendar"][0]
    assert m.group(1) == "Sun", "haftalık slot Pazar (brief)"
    assert (m.group(2), m.group(3), m.group(4)) == ("03", "30", "00")


def test_timer_persistent_ve_fixedrandomdelay():
    """`FixedRandomDelay=true` YOKSA dagit'in sistem-geneli `daemon-reload`u rastgele payı
    yeniden çeker ve tetiği erkene alır (TSK-152). v418 kapısı da bunu tarar."""
    y = _yonergeler(TIMER_YOL.read_text(encoding="utf-8"))
    assert y.get("Persistent") == ["true"], y.get("Persistent")
    assert y.get("FixedRandomDelay") == ["true"], y.get("FixedRandomDelay")
    assert y.get("RandomizedDelaySec"), "FixedRandomDelay ölçecek bir pay olmadan anlamsızdır"


def test_timer_install_bolumu_var():
    metin = TIMER_YOL.read_text(encoding="utf-8")
    assert "Install" in _bolumler(metin)
    assert _yonergeler(metin).get("WantedBy") == ["timers.target"]


def test_timer_service_bolumu_tasimaz():
    """Sertleştirme süreç yürütmeye aittir; timer'da `[Service]` görülmesi yanlış dosyaya
    yazıldığının işaretidir (v174 emsali)."""
    assert "Service" not in _bolumler(TIMER_YOL.read_text(encoding="utf-8"))


def test_timer_sprint_penceresi_bedeli_beyanli():
    """Bedel yasası: 03:30Z öğrenme sprintinin [22:00, 06:00) penceresinin İÇİNDEDİR. Kazanç
    (brifing/bekçi/karne slotlarından uzaklık) ölçülüp bedel yazılmasaydı, CPU çekişmesi
    sessiz kalırdı."""
    metin = TIMER_YOL.read_text(encoding="utf-8").casefold()
    assert "sprint" in metin and "22:00" in metin, "sprint penceresi çakışması beyan edilmemiş"
