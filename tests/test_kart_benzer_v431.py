"""tests/test_kart_benzer_v431.py — `ops/kart_benzer.py` çivileri (TSK-170 bacak b).

Brief: `.superpowers/sdd/2026-09-06-tsk170/brief-kart-benzer.md`.

NUMARA SEÇİMİ: `ls tests | grep -oE "v[0-9]{2,}" | sort -n` ile ölçüldü — en büyük alınmış numara
v430 idi (2026-09-06). v431 boştu; çakışma yok.

NEYİ ÇİVİLER (her biri ayrı bir sınıf):
  1. SÖZLEŞME KOMUT SATIRIDIR — uçtan-uca senaryolar (a-e) `subprocess` ile ARACI ÇAĞIRIR,
     `main()` import ETMEZ (vaka 2026-08-30 emsali — bkz. `test_olay_sorgu_v355.py`).
  2. Hüküm sınıfının TEK KAYNAĞI `ROADMAP.md` §6'dır — kartın kendi `status` alanı DEĞİL
     (`ops/kart_endeksi_uret.py` FARKLI bir sözleşmeyi okur; bu ikisi kasıtlı ayrı kaynaktır).
     Bu, GERÇEK depo üstünde koşan (a)/(b) ile ve tmp_path'teki sentetik depoyla (d) sınanır.
  3. Skor bileşenleri (Jaccard / aile-bonusu / slug-örtüşmesi) hem uçtan-uca hem İZOLE
     fonksiyon çağrısıyla sınanır — aile-bonusu hiçbir uçtan-uca sorgu `--family` PASS ETMEDİĞİ
     için o yoldan görünmez; izolasyon bu yüzden AYRI bir çivi sınıfıdır (mutasyon kanıtı notuna
     bkz: rapor).
  4. YASA 4 (sessiz yutma yok) — bozuk kart YAML'i taramayı çökertmez, UYARI+sayaçla raporlanır.
  5. Uydurma yasağı — §6'da satırı olmayan kart için sınıf TAHMİN EDİLMEZ: `bilinmiyor`.
  6. OBS SIZINTISI KAPALI — araç `meridian` paketini import ETMEZ (statik + `-X importtime`
     davranışsal ölçüm, `test_olay_sorgu_v355.py` ile aynı desen).

GERÇEK DEPOYA DOKUNULMAZ: (a)/(b)/meridian-sızıntı testleri gerçek `research/cards/` ve
`ROADMAP.md`'yi SALT-OKUNUR okur (araç zaten hiçbir dosyaya yazmaz — yalnız `--json` verilirse
KENDİ belirttiğimiz hedefe yazar). Diğer tüm testler `tmp_path` altında kendi sentetik mini-
depolarını kurar.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
ARAC = KOK / "ops" / "kart_benzer.py"

# Gerçek depoda kararlı, önceden ölçülmüş (2026-09-06) sorgu/örnek çiftleri — bkz. §6 satırları:
#   EDG-2026-080 → status: ACTIVE (çıplak)
#   EDG-2026-074 → status: DONE(2026-09-06·KALDI)
#   EDG-2026-001 → status: DONE(2026-07-31·KALDI)
SORGU_HINDSIGHT = "Hindsight reflect kanary zihin modeli minimax"
SORGU_52WH = "52 hafta yüksek kırılım momentum"
SORGU_UYDURUK = "qzxqzx wqywqy zzptzzpt placeholder999"


def _kos(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ARAC), *argv],
        capture_output=True, text=True, cwd=str(KOK),
    )


def _satirlar(stdout: str) -> list[str]:
    return [s for s in stdout.splitlines() if s.strip()]


@pytest.fixture(scope="module")
def mod():
    """Beyaz-kutu erişimi için KAYNAKTAN yüklenmiş modül (bayat-bytecode YOK — TEK uygulama:
    `ops/sasi_yukleyici.kaynaktan_yukle`, `tests/conftest.py` üzerinden). Yalnız İZOLE fonksiyon
    testleri (aşağıda) kullanır; sözleşme testleri (a-e) `subprocess` ile CLI'yi çağırır."""
    return betikten_modul_yukle(ARAC, ad="kart_benzer_v431_mod")


# ---------------------------------------------------------------------------
# (a) — GERÇEK DEPO: hindsight sorgusu, ilk 3'te 080 (ACTIVE) ve 074 (KALDI)
# ---------------------------------------------------------------------------

def test_a_hindsight_sorgusu_ilk_ucte_080_ve_074_dogru_sec6_sinifiyla():
    r = _kos("--hipotez", SORGU_HINDSIGHT, "--n", "8")
    assert r.returncode == 0, r.stderr
    satirlar = _satirlar(r.stdout)
    ilk_uc_id = [s.split(" · ", 1)[0] for s in satirlar[:3]]
    assert "EDG-2026-080" in ilk_uc_id, r.stdout
    assert "EDG-2026-074" in ilk_uc_id, r.stdout
    satir_080 = next(s for s in satirlar if s.startswith("EDG-2026-080 "))
    satir_074 = next(s for s in satirlar if s.startswith("EDG-2026-074 "))
    assert " · ACTIVE · " in satir_080, satir_080
    assert " · KALDI · " in satir_074, satir_074


# ---------------------------------------------------------------------------
# (b) — GERÇEK DEPO: 52wh sorgusu, EDG-2026-001 listede ve KALDI
# ---------------------------------------------------------------------------

def test_b_52wh_sorgusu_edg001_listede_kaldi_sinifiyla():
    r = _kos("--hipotez", SORGU_52WH, "--n", "20")
    assert r.returncode == 0, r.stderr
    satirlar = _satirlar(r.stdout)
    satir = next((s for s in satirlar if s.startswith("EDG-2026-001 ")), None)
    assert satir is not None, r.stdout
    assert " · KALDI · " in satir, satir


# ---------------------------------------------------------------------------
# (c) — skor 0 olan kart HİÇ basılmaz (eşik yok; sıfır zaten dışlanır)
# ---------------------------------------------------------------------------

def test_c_hicbir_karta_ortusmeyen_sorguda_liste_bostur():
    r = _kos("--hipotez", SORGU_UYDURUK, "--n", "8")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "(benzer kart bulunamadı)", r.stdout


# ---------------------------------------------------------------------------
# (d) — §6'da olmayan sahte kart → bilinmiyor; §6'ya satır eklenince gerçek sınıf
#       (uydurma yasağı: sınıf TAHMİN EDİLMEZ, yalnız §6'dan OKUNUR)
# ---------------------------------------------------------------------------

def _mini_depo_kur(tmp_path: pathlib.Path, roadmap_govde: str = "") -> pathlib.Path:
    depo = tmp_path / "sahte_depo"
    (depo / "research" / "cards").mkdir(parents=True)
    (depo / "ROADMAP.md").write_text(
        "# ROADMAP\n\n## §6 KANIT/KARTLAR\n\n" + roadmap_govde + "\n\n## §7 KARAR GÜNLÜĞÜ\n",
        encoding="utf-8")
    return depo


def _sahte_kart_yaz(depo: pathlib.Path) -> None:
    (depo / "research" / "cards" / "FAKE-2026-999-sahte-deneme.yaml").write_text(
        "card_id: FAKE-2026-999\n"
        "family: sahte_aile_xyz\n"
        "hipotez: >\n"
        "  Tamamen uydurma bir sahte hipotez metni qwqwqw zxzxzx.\n"
        "status: measuring\n",
        encoding="utf-8")


SORGU_SAHTE = "Tamamen uydurma sahte hipotez qwqwqw zxzxzx"


def test_d1_sec6da_olmayan_kart_bilinmiyor(tmp_path):
    depo = _mini_depo_kur(tmp_path)
    _sahte_kart_yaz(depo)
    r = _kos("--hipotez", SORGU_SAHTE, "--repo", str(depo), "--n", "5")
    assert r.returncode == 0, r.stderr
    satir = next((s for s in _satirlar(r.stdout) if s.startswith("FAKE-2026-999 ")), None)
    assert satir is not None, r.stdout
    assert " · bilinmiyor · " in satir, satir


def test_d2_sec6ya_satir_eklenince_bilinmiyor_degil_gercek_sinif(tmp_path):
    depo = _mini_depo_kur(
        tmp_path,
        "- **[FAKE-2026-999] sahte-deneme** — status: DONE(2026-09-06·KALDI) · owner: rol1 · "
        "size: — · trigger: —\n")
    _sahte_kart_yaz(depo)
    r = _kos("--hipotez", SORGU_SAHTE, "--repo", str(depo), "--n", "5")
    assert r.returncode == 0, r.stderr
    satir = next(s for s in _satirlar(r.stdout) if s.startswith("FAKE-2026-999 "))
    assert " · KALDI · " in satir, satir
    assert " · bilinmiyor · " not in satir, satir


# ---------------------------------------------------------------------------
# (e) — JSON çıktısı şeması
# ---------------------------------------------------------------------------

def test_e_json_ciktisi_sema_ve_icerik(tmp_path):
    json_yolu = tmp_path / "cikti.json"
    r = _kos("--hipotez", SORGU_HINDSIGHT, "--n", "3", "--json", str(json_yolu))
    assert r.returncode == 0, r.stderr
    veri = json.loads(json_yolu.read_text(encoding="utf-8"))
    assert isinstance(veri, list)
    assert len(veri) == 3
    for kayit in veri:
        assert isinstance(kayit, dict)
        assert set(kayit) == {"id", "family", "sinif", "skor", "hipotez", "hukum"}
        assert isinstance(kayit["skor"], float) and kayit["skor"] > 0
        assert isinstance(kayit["id"], str) and kayit["id"]
    assert veri[0]["id"] == "EDG-2026-080"
    # stdout ile JSON AYNI sıralamayı taşır (tek kaynak: aynı `benzerleri_bul` çağrısı)
    stdout_ilk_id = _satirlar(r.stdout)[0].split(" · ", 1)[0]
    assert stdout_ilk_id == veri[0]["id"]


# ---------------------------------------------------------------------------
# YASA 4 — bozuk YAML sessizce yutulmaz: kart atlanır, sayılır, UYARI basılır
# ---------------------------------------------------------------------------

def test_yasa4_bozuk_yaml_atlanir_sayilir_ve_diger_kart_okunur(tmp_path):
    depo = _mini_depo_kur(tmp_path)
    (depo / "research" / "cards" / "BROKEN-2026-001-x.yaml").write_text(
        "card_id: BROKEN-2026-001\nfamily: [acilmayan\n", encoding="utf-8")  # kasıtlı bozuk YAML
    (depo / "research" / "cards" / "OK-2026-001-y.yaml").write_text(
        "card_id: OK-2026-001\n"
        "family: saglam_aile\n"
        "hipotez: >\n"
        "  Saglam bir hipotez metni test amacli.\n"
        "status: measuring\n",
        encoding="utf-8")
    sorgu = "Saglam bir hipotez metni test amacli"
    r = _kos("--hipotez", sorgu, "--repo", str(depo), "--n", "5")
    assert r.returncode == 0, r.stderr  # tek bozuk kart aracı ÇÖKERTMEZ
    assert "UYARI" in r.stderr, r.stderr  # ama SESSİZ de değil
    assert "1 kart YAML hatasıyla atlandı" in r.stderr, r.stderr
    assert any(s.startswith("OK-2026-001 ") for s in _satirlar(r.stdout)), r.stdout
    assert not any(s.startswith("BROKEN-2026-001 ") for s in _satirlar(r.stdout)), r.stdout


# ---------------------------------------------------------------------------
# --kart: hipotez/family dosyadan okunur, kartın KENDİ id'si sonuçlardan HARİÇ
# ---------------------------------------------------------------------------

def test_kart_bayragi_kendi_idsini_haric_tutar_ve_ayni_aileyi_one_cikarir():
    kart = (KOK / "research" / "cards" /
            "EDG-2026-080-hindsight-reflect-minimax-kanary-zihin-modeli.yaml")
    r = _kos("--kart", str(kart), "--n", "10")
    assert r.returncode == 0, r.stderr
    satirlar = _satirlar(r.stdout)
    assert not any(s.startswith("EDG-2026-080 ") for s in satirlar), r.stdout
    # aynı family (hindsight_hafiza) kartları aile-bonusu sayesinde listede ÜST SIRALARDA
    ilk_id = satirlar[0].split(" · ", 1)[0]
    assert ilk_id in {"EDG-2026-074", "EDG-2026-077", "EDG-2026-081", "EDG-2026-083"}, r.stdout


# ---------------------------------------------------------------------------
# --hipotez / --kart hiçbiri verilmezse net hata (sözleşme kapısı)
# ---------------------------------------------------------------------------

def test_ne_hipotez_ne_kart_verilirse_hata():
    r = _kos("--n", "5")
    assert r.returncode != 0
    assert "--hipotez" in r.stderr or "--kart" in r.stderr, r.stderr


# ---------------------------------------------------------------------------
# OBS SIZINTISI KAPALI — `meridian` import edilmez (statik + davranışsal)
# ---------------------------------------------------------------------------

def test_kaynakta_meridian_importu_yok():
    """Kaynak metni `meridian`ı import ETMEZ — obs sızıntısı yolu kapalı (statik ölçüm)."""
    kaynak = ARAC.read_text(encoding="utf-8")
    kod = [s for s in kaynak.splitlines() if not s.lstrip().startswith("#")]
    suclu = [s for s in kod if "import meridian" in s or "from meridian" in s]
    assert not suclu, suclu


def test_gercek_kosumda_meridian_modulu_yuklenmez():
    """DAVRANIŞSAL ölçüm: `-X importtime` ile GERÇEK koşumda yüklenen modüller arasında
    `meridian` YOKTUR — dolaylı import de yakalanır (statik grep'ten farklı bir sınıf)."""
    r = subprocess.run(
        [sys.executable, "-X", "importtime", str(ARAC), "--hipotez", "ozet test", "--n", "1"],
        capture_output=True, text=True, cwd=str(KOK),
    )
    assert r.returncode == 0, r.stderr
    yuklenen = [s.rsplit("|", 1)[-1].strip()
                for s in r.stderr.splitlines() if s.startswith("import time:")]
    sizan = [m for m in yuklenen if m == "meridian" or m.startswith("meridian.")]
    assert not sizan, f"meridian modülü yüklendi: {sizan}"


# ---------------------------------------------------------------------------
# İZOLE FONKSİYON TESTLERİ — mutasyon-duyarlı, uçtan-uca sorgu gürültüsünden bağımsız
#
# NEDEN AYRI SINIF: uçtan-uca (a)-(e) testlerinin hiçbiri `--family` GEÇMEZ (brief'in kendi
# senaryoları böyle), yani "aile bonusunu kapat" mutasyonu o yoldan hiç GÖRÜNMEZ olurdu — çivi
# sessizce kör kalırdı. `skorla`yı doğrudan çağırmak bu körlüğü kapatır.
# ---------------------------------------------------------------------------

def test_normalize_tokens_turkce_karakter_korunur_ve_uzunluk_esigi(mod):
    assert mod.normalize_tokens("Kırılım-momentum, 52 hafta!") == {"kırılım", "momentum", "hafta"}
    assert mod.normalize_tokens("") == set()
    assert mod.normalize_tokens(None) == set()


def test_skorla_jaccard_izole(mod):
    sorgu = {"a", "b", "c"}
    kart = {"a", "b", "x"}
    assert mod.skorla(sorgu, None, None, kart, None) == pytest.approx(2 / 4)


def test_skorla_aile_bonusu_izole(mod):
    sorgu_tokens = {"a", "b", "c", "d"}
    kart_tokens = {"a", "b", "x", "y"}
    skor_ailesiz = mod.skorla(sorgu_tokens, None, None, kart_tokens, None)
    skor_aileli = mod.skorla(sorgu_tokens, "ayni_aile", "ayni_aile", kart_tokens, None)
    skor_farkli_aile = mod.skorla(sorgu_tokens, "aile_a", "aile_b", kart_tokens, None)
    assert skor_aileli - skor_ailesiz == pytest.approx(0.25)
    assert skor_farkli_aile == pytest.approx(skor_ailesiz)  # farklı family → bonus YOK


def test_skorla_slug_ortusmesi_izole(mod):
    sorgu_tokens = {"kirilim", "momentum"}
    skor_slugsuz = mod.skorla(sorgu_tokens, None, None, set(), None)
    skor_sluglu = mod.skorla(sorgu_tokens, None, None, set(), "kirilim-baska-slug")
    assert skor_slugsuz == 0.0
    assert skor_sluglu == pytest.approx(0.1)  # 1 örtüşen slug token × 0.1


def test_hukum_siniflarini_cikar_izole(mod):
    metin = (
        "## §6 KANIT/KARTLAR\n\n"
        "- **[EDG-2026-900] ornek** — status: DONE(2026-09-06·GEÇTİ) · owner: rol1 · size: — · "
        "trigger: —\n"
        "- **[EDG-2026-901] ornek2** — status: ACTIVE · owner: rol1 · size: — · trigger: —\n\n"
        "## §7 KARAR GÜNLÜĞÜ\n"
        "- **[EDG-2026-902] disarda** — status: DONE(2026-09-06·KALDI) · owner: rol1\n"
    )
    sinif = mod.hukum_siniflarini_cikar(metin)
    assert sinif == {"EDG-2026-900": "GEÇTİ", "EDG-2026-901": "ACTIVE"}
    assert "EDG-2026-902" not in sinif  # §7'nin dışına taşan satır §6 SAYILMAZ


def test_hukum_siniflarini_cikar_bolge_yoksa_bos_sozluk(mod):
    assert mod.hukum_siniflarini_cikar("§6 hiç yok burada") == {}
