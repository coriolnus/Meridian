"""tests/test_edg093_veri_v489.py — EDG-2026-093 ANA ÖLÇÜM Parti-1 (VERİ KURULUMU) çivileri.

vNNN KİMLİK KAYDI: v489 seçildi çünkü ölçüm anında (2026-09-14) `grep -rl v489 tests/ docs/
research/ ops/ meridian/` yalnız ilgisiz bir HTML artefaktında rastlantısal alt dizge buldu;
`tests/` altında v489 BOŞTU — çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı).

NE ÇİVİLER — ÜÇ DOSYA:
  ortak.py    saf sözleşme gövdesi (kohort okuma, sembol anahtarı, bar dosya adı, EDGAR şeması,
              SEC politikası, karar çiftleri, manifest yazımı). Bu dosya İTHAL EDİLEBİLİR
              (argparse kurmaz, modül düzeyinde G/Ç yapmaz) — çiviler onu doğrudan yükler.
  veri_bar    Alpaca IEX bar çekimi → canlı arşiv şemasıyla csv + manifest.
  veri_edgar  CIK eşlemesi + companyfacts çekimi + PIT hisse-adedi çıkarımı.

NEDEN SUBPROCESS (veri_bar/veri_edgar). İkisinin de sözleşmesi KOMUT SATIRIdır (CLAUDE.md §1),
`main()` değil; argparse MODÜL SEVİYESİNDE kurulur (stdin kipi şartı, v480 dersi) — ithal etmek
pytest'in argv'siyle bir koşum tetiklerdi. Her çivi betiği GERÇEKTEN stdin'den, kök dizinden
koşturur. Ham `exec_module` YOKTUR (v334): ortak.py ve emsal betikler
`tests.conftest.betikten_modul_yukle` ile KAYNAKTAN derlenir.

AĞ YOK — VE BU VARSAYILMAZ, ÖLÇÜLÜR:
  * bar tarafı: v488'in SENTETİK Alpaca ikamesi İTHAL EDİLİR (kopya değil — tek-kaynak) ve her
    çağrı bir JSONL defterine düşer; "hiç çağrılmadı" iddiası sayaçla ölçülür.
  * EDGAR tarafı: betik atılacak HER isteği ATILMADAN ÖNCE `edgar/istek_defteri.jsonl` dosyasına
    yazar. `--sec 0` çivisi o dosyanın YOKLUĞUNU ölçer; `--sec 1` çivisi de hepsi diskte hazırken
    defterin BOŞ kaldığını ölçer. İddia ile ölçüm arasındaki fark tam olarak budur.

TEK KAYNAK ÇİVİLERİ (bu dosyanın omurgası). Parti-1 dört sözleşmeyi başka dosyalardan TÜRETİR:
bar kolonları (canlı bar arşivi), hisse-adedi etiket kümesi ve 16 kolonluk EDGAR şeması (EDGAR
çıkarım/nihai betikleri), SEC nezaket politikası (EDGAR indirici) ve karar grameri (kohort
üreticisi). Her biri için çivi ÜRETİCİYİ OKUR ve eşitliği ölçer — kopya kaçınılmazsa türetme +
ayrışma çivisi (CLAUDE.md §4).

MUTASYON KANITI (bu dosyada KOŞMAZ, Rol-1'e raporla teslim edilir — CLAUDE.md §6):
  (a) hisse-adedi etiket kümesi daraltılınca (ortak.py beyanı + extract.py türetmesi birlikte)
      `test_edgar_CIKARIM_etiket_kumesi_ve_ON_ALTI_kolon` kırmızı,
  (b) `filed` kontrolü kaldırılınca `test_edgar_FILED_BOS_satir_REDDEDILIR` kırmızı,
  (c) alpaca anahtar dönüşümü kaldırılınca `test_bar_SINIF_HISSE_anahtari_NOKTAYA_cevrilir` ve
      `test_alpaca_anahtari_DAR_desen` kırmızı,
  (d) üzerine-yazma koruması kaldırılınca `test_bar_YENIDEN_CEK_ayrisan_icerik_YAN_DOSYAYA` kırmızı,
  (g) `cift` filtresi (`main`, Rol-1 hükmü 2026-09-14) kaldırılınca
      `test_edgar_CIFT_CIK_CEKIME_ve_PIT_SERISINE_sizmaz` kırmızı — TUR-2 regresyon çivisi.
"""
from __future__ import annotations

import ast
import gzip
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle
# SENTETİK Alpaca ikamesi ve ortak.py kurucusu TEK KOPYADIR: v488'den İTHAL edilir. İkinci bir
# gövde yazmak, iki çivinin AYNI sözleşmeyi farklı sanmasına giden yoldur (bu deponun tekrar eden
# "iki kopya sessizce ayrışır" sınıfı).
from tests.test_edg093_adim0b_v488 import SAHTE_ALPACA, _ortak_kur

REPO = pathlib.Path(__file__).resolve().parents[1]
OLCUM = REPO / "research" / "olcumler" / "edg093_midcap_pit"
ORTAK_YOLU = OLCUM / "ortak.py"
BAR_BETIK = OLCUM / "veri_bar.py"
EDGAR_BETIK = OLCUM / "veri_edgar.py"
ADIM0B = OLCUM / "adim0b_kapsama.py"
KART_ADI = "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml"

EDGAR_BETIKLERI = REPO / "research" / "edgar_facts" / "betikler"
ELLE_ESLEME = REPO / "research" / "pit_universe" / "sp400_elle_esleme.yaml"

_BUGUN = "2026-09-14"
_PENCERE = "2020-07-27"

#: SENTETİK kart — gerçek kartın iki alanını taşır: `esikler` (v488 uyumu) ve `veri_penceresi`
#: (kohort penceresinin başı BURADAN okunur; koda gömülü olmadığını ayrı çivi ölçer).
SENTETIK_KART = (
    "# SENTETİK kart (v489 fikstürü) — gerçek kart bu ağaçta DEĞİL.\n"
    "card_id: EDG-2026-093\n"
    "esikler:\n"
    "  kapsanan_isim_alt: 40\n"
    "  ortalama_bar_gecmisi_yil_alt: 3\n"
    f"veri_penceresi: \"{_PENCERE} (Alpaca IEX ilk-bar tabanı) → ölçüm günü\"\n"
)

#: Bar tarafının sentetik kohortu — v488'in kohortuyla AYNI semboller (aynı sentetik uç servis
#: eder): AAA 504 bar · BBB 756 · CCC RuntimeError · DDD boş cevap · EEE 252.
KOHORT_CSV = (
    "date,tickers\n"
    f'{_PENCERE},"AAA,BBB,CCC,DDD,EEE"\n'
    '2020-08-03,"AAA,BBB,CCC,DDD"\n'
    '2020-08-10,"AAA,BBB,CCC"\n'
)

#: Sınıf-hisse kohortu (v488 ile aynı fikstür sembolleri): tire biçimi sentetik uçta 400 alır.
KOHORT_SINIF_CSV = "date,tickers\n" + f'{_PENCERE},"AA,BRK-B,MOG-A,MP,TST-AB"\n'

#: Canlı arşiv kolonlarının PERMÜTASYONU — "kolonlar koda gömülü mü" sorusunun ölçümü. Adlar
#: AYNI (yazım bozulmaz), SIRA farklı: betik gerçekten türetiyorsa csv başlığı bu sırayı taşır.
PERMUTE_COLS = ["date", "close", "open", "high", "low", "volume"]


# =================================================================================================
# FİKSTÜRLER
# =================================================================================================
def _kos(betik: pathlib.Path, *args: str, defter: pathlib.Path | None = None, cwd: str = "/"):
    """Betiği stdin'den koşar. PYTHONPATH SİLİNİR (sentetik paket gerçeğe yenilmesin)."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    if defter is not None:
        env["SAHTE_ALPACA_DEFTER"] = str(defter)
    return subprocess.run([sys.executable, "-", *args], input=betik.read_bytes(), cwd=cwd,
                          capture_output=True, timeout=180, env=env)


def _bar_repo(tmp_path: pathlib.Path, kolonlar=None) -> pathlib.Path:
    """Sahte repo: sentetik `meridian.adapters` (alpaca ikamesi + COLS taşıyan data), kart,
    ortak.py. `kolonlar` verilirse data.py O listeyi taşır (türetme çivisi)."""
    repo = tmp_path / "sahte_repo"
    (repo / "meridian" / "adapters").mkdir(parents=True)
    (repo / "meridian" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "meridian" / "adapters" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "meridian" / "adapters" / "alpaca.py").write_text(SAHTE_ALPACA, encoding="utf-8")
    (repo / "meridian" / "adapters" / "data.py").write_text(
        "# SENTETİK data.py (v489) — yalnız kolon şeması sabiti.\n"
        "COLS = %r\n" % (list(kolonlar or ["date", "open", "high", "low", "close", "volume"]),),
        encoding="utf-8")
    (repo / "research" / "cards").mkdir(parents=True)
    (repo / "research" / "cards" / KART_ADI).write_text(SENTETIK_KART, encoding="utf-8")
    _ortak_kur(repo)
    return repo


def _bar_duzen(tmp_path: pathlib.Path, kohort_metni: str = KOHORT_CSV, kolonlar=None):
    kohort = tmp_path / "sp400_uyelik_tarihi.csv"
    kohort.write_text(kohort_metni, encoding="utf-8")
    return (_bar_repo(tmp_path, kolonlar), kohort, tmp_path / "cikti",
            tmp_path / "alpaca_cagrilari.jsonl")


def _bar_kos(duzen, *ek: str, defter_ver: bool = True):
    repo, kohort, cikti, defter = duzen
    r = _kos(BAR_BETIK, "--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
             "--bugun", _BUGUN, "--bekleme-sn", "0", "--baslangic", "2019-06-01", *ek,
             defter=(defter if defter_ver else None))
    assert r.returncode == 0, (r.returncode, r.stderr.decode()[-1500:])
    uretilen = sorted(cikti.glob("bars_manifest_*.json"))
    assert len(uretilen) == 1, [p.name for p in uretilen]
    return r, json.loads(uretilen[-1].read_text(encoding="utf-8")), defter


def _kayitlar(rapor) -> dict:
    return {k["sembol"]: k for k in rapor["kayitlar"]}


def _cagrilar(defter: pathlib.Path) -> list[dict]:
    if not defter.exists():
        return []
    return [json.loads(x) for x in defter.read_text(encoding="utf-8").splitlines() if x.strip()]


# ---- EDGAR fikstürleri: `--repo` GERÇEK depodur (edgar_facts sözleşmeleri gerçeğinden ölçülsün);
# ---- ağ YOKTUR çünkü company_tickers ve ham companyfacts önceden DİSKE konur.
#: Sentetik kohort: DECK gerçek haritada VAR (kaynak 1) · AAA/BBB sentetik tickers'ta (kaynak 2) ·
#: HTA gerçek yaml'de `esle:HTA->HR` (kaynak 3, kimlik) · AMCX gerçek yaml'de `cift:AMCX->CNXC`
#: (kaynak 3, ANOTASYON) · ZZZZ hiçbir yerde (eşleşmeyen).
EDGAR_KOHORT_CSV = "date,tickers\n" + f'{_PENCERE},"AAA,AMCX,BBB,DECK,HTA,ZZZZ"\n'

_SENTETIK_TICKERS = {
    "0": {"cik_str": 111, "ticker": "AAA", "title": "Sentetik AAA Inc"},
    "1": {"cik_str": 222, "ticker": "BBB", "title": "Sentetik BBB Corp"},
    "2": {"cik_str": 333, "ticker": "HR", "title": "Healthcare Realty (HTA halefi)"},
    "3": {"cik_str": 444, "ticker": "CNXC", "title": "Concentrix (AMCX ÇİFTİ — ayrı ihraççı)"},
    "4": {"cik_str": 910521, "ticker": "DECK", "title": "SENTETİK DECK — kaynak 1 kazanmalı"},
}

#: Sentetik companyfacts. ÜÇ ŞEYİ birden sınar: (1) etiket kümesi (Assets ÇIKARIMA GİRMEZ),
#: (2) `filed` boş satırın REDDİ, (3) `end`in pencerenin DIŞINDA olmasının satırı DÜŞÜRMEMESİ.
_FACTS_AAA = {
    "cik": 111,
    "facts": {
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": "2020-06-30", "val": 1000.0, "filed": "2020-07-15", "form": "10-Q",
             "fy": 2020, "fp": "Q2", "accn": "acc-1", "frame": "CY2020Q2I"},
            {"end": "2019-01-31", "val": 900.0, "filed": "2019-02-10", "form": "10-K",
             "fy": 2019, "fp": "FY", "accn": "acc-0"},
            {"end": "2021-03-31", "val": 1100.0, "filed": None, "form": "10-Q",
             "fy": 2021, "fp": "Q1", "accn": "acc-2"},
        ]}}},
        "us-gaap": {
            "CommonStockSharesIssued": {"units": {"shares": [
                {"end": "2020-06-30", "val": 1200.0, "filed": "2020-07-15", "form": "10-Q",
                 "fy": 2020, "fp": "Q2", "accn": "acc-1"}]}},
            "WeightedAverageNumberOfSharesOutstandingBasic": {"units": {"shares": [
                {"start": "2020-04-01", "end": "2020-06-30", "val": 995.0,
                 "filed": "2020-07-15", "form": "10-Q", "fy": 2020, "fp": "Q2",
                 "accn": "acc-1"}]}},
            "Assets": {"units": {"USD": [
                {"end": "2020-06-30", "val": 5.0, "filed": "2020-07-15", "form": "10-Q"}]}},
        },
    },
}
# ELLE HESAPLANMIŞ BEKLENEN (AAA): dei 3 girişin biri `filed` boş → REDDEDİLİR → dei 2 satır;
# CommonStockSharesIssued 1; WeightedAverageNumberOfSharesOutstandingBasic 1 → TOPLAM 4 satır.
# `Assets` etiket kümesinin DIŞINDADIR → 0 satır. `filed` boş red sayısı 1.
_BEKLENEN_AAA_SATIR = 4
_BEKLENEN_AAA_DEI = 2
_BEKLENEN_FILED_BOS = 1


def _edgar_duzen(tmp_path: pathlib.Path, ciklar=(111,)):
    """(kohort, cikti) — sentetik tickers + verilen CIK'ler için sentetik ham companyfacts."""
    kohort = tmp_path / "edgar_kohort.csv"
    kohort.write_text(EDGAR_KOHORT_CSV, encoding="utf-8")
    cikti = tmp_path / "cikti"
    (cikti / "edgar" / "raw").mkdir(parents=True)
    (cikti / "edgar" / "company_tickers.json").write_text(
        json.dumps(_SENTETIK_TICKERS), encoding="utf-8")
    for cik in ciklar:
        govde = dict(_FACTS_AAA)
        govde["cik"] = cik
        (cikti / "edgar" / "raw" / f"CIK{cik:010d}.json.gz").write_bytes(
            gzip.compress(json.dumps(govde).encode("utf-8"), mtime=0))
    return kohort, cikti


def _edgar_kos(kohort, cikti, *ek: str, beklenen_kod: int = 0):
    r = _kos(EDGAR_BETIK, "--repo", str(REPO), "--cikti", str(cikti), "--kohort", str(kohort),
             "--bugun", _BUGUN, *ek)
    assert r.returncode == beklenen_kod, (r.returncode, r.stderr.decode()[-1500:])
    if beklenen_kod != 0:
        return r, None
    return r, json.loads((cikti / "edgar" / "kaynak_sp400.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ortak():
    """ortak.py KAYNAKTAN derlenir (v334: ham exec_module yok, `__pycache__` okunmaz)."""
    return betikten_modul_yukle(ORTAK_YOLU, "edg093_ortak_v489")


# =================================================================================================
# §A — ORTAK SAF FONKSİYONLAR
# =================================================================================================
def test_kohort_okuma_SOZLESMESI_baslik_ve_ARTAN_tarih(ortak, tmp_path):
    iyi = tmp_path / "iyi.csv"
    iyi.write_text(KOHORT_CSV, encoding="utf-8")
    satirlar = ortak.kohort_oku(iyi)
    assert [str(d) for d, _ in satirlar] == [_PENCERE, "2020-08-03", "2020-08-10"]
    assert satirlar[0][1] == frozenset({"AAA", "BBB", "CCC", "DDD", "EEE"})

    kotu = tmp_path / "kotu.csv"
    kotu.write_text("gun,semboller\n2020-07-27,AAA\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ex:
        ortak.kohort_oku(kotu)
    assert ex.value.code == 2

    ters = tmp_path / "ters.csv"
    ters.write_text("date,tickers\n2020-08-10,AAA\n2020-07-27,BBB\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ex2:
        ortak.kohort_oku(ters)
    assert ex2.value.code == 2


def test_isim_kumesi_ve_CIKIS_GUNLERI_elle_hesaplanmis(ortak, tmp_path):
    """ELLE: EEE son kez ilk satırda → çıkış 2020-08-03 · DDD son kez ikinci satırda → 2020-08-10 ·
    AAA/BBB/CCC son satırda hâlâ üye → çıkış YOK (dosya sonrası TAŞINMAZ)."""
    import datetime as dt
    yol = tmp_path / "k.csv"
    yol.write_text(KOHORT_CSV, encoding="utf-8")
    etkin, capa = ortak.pencere_satirlari(ortak.kohort_oku(yol), dt.date(2020, 7, 27),
                                          dt.date(2026, 9, 14))
    assert capa is True and len(etkin) == 3
    assert ortak.isim_kumesi_ve_cikislar(etkin) == {
        "AAA": None, "BBB": None, "CCC": None, "DDD": "2020-08-10", "EEE": "2020-08-03"}


def test_alpaca_anahtari_DAR_desen(ortak):
    """MUTASYON HEDEFİ (c): dönüşüm kaldırılırsa BRK-B/MOG-A tire ile kalır ve bu çivi kırmızı."""
    assert ortak.alpaca_anahtari("BRK-B") == "BRK.B"
    assert ortak.alpaca_anahtari("MOG-A") == "MOG.A"
    for dokunulmaz in ("AA", "MP", "TST-AB", "AAPL"):
        assert ortak.alpaca_anahtari(dokunulmaz) == dokunulmaz


def test_bar_dosya_adi_CANLI_ARSIVIN_kendi_kuraliyla_ayni(ortak):
    """Dosya adı ikinci bir şema DEĞİL, canlı arşivin `_cache_path` kuralının ta kendisidir:
    Alpaca anahtarı küçültülür ve nokta TİREYE çevrilir. Kıyas GERÇEK fonksiyonla yapılır."""
    from meridian.adapters import data as dat
    for sembol in ("MOG-A", "BRK-B", "AAA", "MP"):
        anahtar = ortak.alpaca_anahtari(sembol)
        assert ortak.bar_dosya_adi(sembol) + ".csv" == dat._cache_path(anahtar).name
    assert ortak.bar_dosya_adi("MOG-A") == "mog-a"


def test_bar_kolonlari_GERCEK_data_py_den_TURETILIR(ortak):
    from meridian.adapters import data as dat
    kolonlar, kaynak, neden = ortak.bar_kolonlari(REPO)
    assert kolonlar == list(dat.COLS), (kolonlar, dat.COLS)
    assert "türetildi" in kaynak and neden is None


def test_hisse_etiketleri_GERCEK_extract_betiginden_TURETILIR(ortak):
    """TEK KAYNAK ÇİVİSİ. Etiket kümesinin sahibi EDGAR çıkarım betiğidir; ortak.py'deki beyanlı
    taban onunla BİREBİR aynı olmalıdır — ayrışırsa bu çivi ADIYLA düşer (mutasyon hedefi (a))."""
    ext = betikten_modul_yukle(EDGAR_BETIKLERI / "extract.py", "edg093_extract_v489")
    etiketler, kaynak, neden = ortak.hisse_etiketleri(REPO)
    assert etiketler == [tuple(x) for x in ext.SHARE_TAGS]
    assert "türetildi" in kaynak and neden is None
    assert tuple(ortak.HISSE_ETIKETLERI_BEYAN) == tuple(tuple(x) for x in ext.SHARE_TAGS), (
        "ortak.py'deki BEYANLI TABAN çıkarım betiğinin etiket kümesinden AYRIŞTI — türetme "
        "düştüğü gün ölçüm sessizce başka bir kümeyle koşardı")


def test_edgar_kolonlari_ON_ALTI_ve_finalize_betiginden_TURETILIR(ortak):
    fin = betikten_modul_yukle(EDGAR_BETIKLERI / "finalize.py", "edg093_finalize_v489")
    kolonlar, kaynak, neden = ortak.edgar_kolonlari(REPO)
    assert len(kolonlar) == 16 and kolonlar == list(fin.COLS)
    assert "türetildi" in kaynak and neden is None
    assert list(ortak.EDGAR_KOLONLARI_BEYAN) == list(fin.COLS)


def test_donem_turu_MERDIVENI_finalize_betigiyle_AYNI(ortak):
    """Merdiven bir FONKSİYON gövdesidir, literal değil — bu yüzden türetme ÇİVİDE yapılır:
    finalize betiğinin `donem_turu` gövdesi ayrıştırılır ve (eşik, etiket) sırası kıyaslanır."""
    kaynak = (EDGAR_BETIKLERI / "finalize.py").read_text(encoding="utf-8")
    merdiven = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.FunctionDef) and dugum.name == "donem_turu":
            for govde in dugum.body:
                if (isinstance(govde, ast.If) and isinstance(govde.test, ast.Compare)
                        and isinstance(govde.test.comparators[0], ast.Constant)
                        and isinstance(govde.body[0], ast.Return)):
                    merdiven.append((govde.test.comparators[0].value,
                                     govde.body[0].value.value))
            break
    assert merdiven, "finalize betiğinde `donem_turu` merdiveni bulunamadı — çivi hedefini kaybetti"
    assert tuple(merdiven) == ortak.DONEM_TURU_MERDIVENI, (merdiven, ortak.DONEM_TURU_MERDIVENI)
    # davranış: start yok → anlik · 90 gün → ceyrek · 365 → yillik · 500 → diger
    assert ortak.donem_turu(None) == "anlik"
    assert ortak.donem_turu(90) == "ceyrek" and ortak.donem_turu(365) == "yillik"
    assert ortak.donem_turu(500) == "diger"
    assert ortak.donem_gun("2020-04-01", "2020-06-30") == 90
    assert ortak.donem_gun("", "2020-06-30") is None


def test_sec_politikasi_GERCEK_indirici_betiginden_TURETILIR(ortak):
    dl = betikten_modul_yukle(EDGAR_BETIKLERI / "download.py", "edg093_dl_v489") \
        if False else None    # indirici ÇALIŞTIRILMAZ (modül düzeyinde ağa çıkar) — AST ile ölçülür
    assert dl is None
    ham = (EDGAR_BETIKLERI / "download.py").read_text(encoding="utf-8")
    beklenen = {}
    for dugum in ast.parse(ham).body:
        if isinstance(dugum, ast.Assign) and isinstance(dugum.targets[0], ast.Name) \
                and dugum.targets[0].id in ("UA", "DELAY", "TPL"):
            beklenen[dugum.targets[0].id] = ast.literal_eval(dugum.value)
    p = ortak.sec_politikasi(REPO)
    assert p["user_agent"] == beklenen["UA"] and "türetildi" in p["user_agent_kaynak"]
    assert p["bekleme_sn"] == beklenen["DELAY"] and "türetildi" in p["bekleme_sn_kaynak"]
    assert p["companyfacts_tpl"] == beklenen["TPL"]
    assert p["tickers_url"].startswith("https://www.sec.gov/") and "türetildi" in p["tickers_url_kaynak"]
    assert "@" in p["user_agent"], "SEC fair-access kimlik bildiren UA ister"


def test_karar_ciftleri_GERCEK_yaml_den_ve_JETONLAR_ayrilir(ortak):
    desen, neden = ortak.kaynaktan_desen(OLCUM / "kohort.py", "KARAR_CIFT_RE")
    assert neden is None and "esle" in desen and "cift" in desen
    ciftler, cneden = ortak.karar_ciftleri(ELLE_ESLEME, desen)
    assert cneden is None and ciftler, ciftler
    assert ("esle", "HTA", "HR") in ciftler
    jetonlar = {j for j, _, _ in ciftler}
    assert jetonlar <= {"esle", "cift"}
    komsu = ortak.esleme_komsulari(ciftler)
    assert ("HR", "esle") in komsu["HTA"] and ("HTA", "esle") in komsu["HR"]
    assert ortak.KARAR_KIMLIK_KANITI["esle"] == "yeniden_adlandirma"
    assert ortak.KARAR_KIMLIK_KANITI["cift"] == "anotasyon_cift"


def test_manifest_yaz_OKUYAN_alani_ZORUNLU(ortak, tmp_path):
    """YASA 6: okuyucusu adıyla yazılmamış artefakt üretilmemişten farksızdır — manifest yazımı
    o alanı ister ve yoksa çıkış 2 verir ("sonra ekleriz" okunmayan artefaktın doğuş biçimi)."""
    with pytest.raises(SystemExit) as ex:
        ortak.manifest_yaz(tmp_path, "x.json", {"a": 1})
    assert ex.value.code == 2
    yol = ortak.manifest_yaz(tmp_path, "y.json", {"okuyan": "Rol-1", "a": 1})
    assert json.loads(yol.read_text(encoding="utf-8"))["a"] == 1


def test_kaynaktan_sabit_TURETEMEYINCE_NEDEN_dondurur_sayi_UYDURMAZ(ortak, tmp_path):
    hedef = tmp_path / "h.py"
    hedef.write_text("X = [1, 2]\nY = bir_cagri()\n", encoding="utf-8")
    assert ortak.kaynaktan_sabit(hedef, "X") == ([1, 2], None)
    deger, neden = ortak.kaynaktan_sabit(hedef, "Y")
    assert deger is None and "literal değil" in neden
    deger2, neden2 = ortak.kaynaktan_sabit(tmp_path / "yok.py", "X")
    assert deger2 is None and "okunamadı" in neden2


# =================================================================================================
# §B — ADIM-0 EKSEN B: KOPYALAR SİLİNDİ, GÖVDE ORTAKTAN İTHAL
# =================================================================================================
def test_adim0b_ORTAKTAN_ithal_ediyor_ve_KOPYA_GOVDE_yok():
    """Taşınan fonksiyonların GÖVDESİ adim0b'de kalmamalı — kalsaydı iki uygulama zamanla
    ayrışırdı ve tek-kaynak yasası kâğıt üstünde kalırdı (bu turun tam sebebi)."""
    kaynak = ADIM0B.read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    tanimlar = {d.name for d in agac.body if isinstance(d, ast.FunctionDef)}
    tasinan = {"kohort_oku", "pencere_satirlari", "isim_kumesi_ve_cikislar", "alpaca_anahtari",
               "sha256", "_soguma_yuzeyi", "_soguma_sifirla", "_bar_tarihi", "_kullanim_hatasi"}
    assert not (tanimlar & tasinan), f"adim0b'de KOPYA gövde kaldı: {sorted(tanimlar & tasinan)}"
    assert "ortak = _ortak_yukle()" in kaynak
    for ad in ("kohort_oku", "alpaca_anahtari", "sha256"):
        assert f"{ad} = ortak." in kaynak, ad


# =================================================================================================
# §C — VERİ_BAR
# =================================================================================================
def test_DOSYA_KIPI_SIG_DIZINDE_IndexError_vermez():
    """v480 ARIZA SINIFININ DOSYA-KİPİ EŞİ (ölçüldü 2026-09-14). `--repo` varsayılanı betiğin
    "üç üstü"dür ve bu ifade MODÜL SEVİYESİNDE, argparse KURULURKEN çalışır — sığ bir dizinde
    (`/tmp/edg093`, A1 reçetesinin kopyaladığı yer) `parents[2]` IndexError verir ve `--help`
    bile düşer. Çivi ifadenin KENDİSİNİ sığ bir SANDBOX ile değerlendirir: patlamamalı ve
    varsayılan None olmalı (o zaman `--repo` zorunludur, sessiz yanlış kök YOK)."""
    for betik in (BAR_BETIK, EDGAR_BETIK, ADIM0B):
        satirlar = betik.read_text(encoding="utf-8").splitlines()
        basla = next(i for i, s in enumerate(satirlar) if s.startswith("_REPO_VARSAYILAN"))
        ifade = satirlar[basla]
        while ifade.count("(") != ifade.count(")"):
            basla += 1
            ifade += "\n" + satirlar[basla]
        ad = {"STDIN_KIPI": False, "SANDBOX": pathlib.Path("/tmp/edg093"), "pathlib": pathlib}
        # `dont_inherit=True` ZORUNLU (v334 §B3): bu dosyanın `from __future__ import annotations`
        # satırı derlenen ifadeye MİRAS KALMAMALI — tarayıcı bayraksız çağrıyı ADIYLA düşürür.
        exec(compile(ifade, str(betik), "exec", dont_inherit=True), ad)
        assert ad["_REPO_VARSAYILAN"] is None, (betik.name, ad["_REPO_VARSAYILAN"])
        derin = {"STDIN_KIPI": False, "SANDBOX": OLCUM, "pathlib": pathlib}
        exec(compile(ifade, str(betik), "exec", dont_inherit=True), derin)
        assert derin["_REPO_VARSAYILAN"] == REPO, (betik.name, derin["_REPO_VARSAYILAN"])


def test_bar_stdin_repo_verilmezse_KULLANIM_HATASI_cikis_2():
    r = _kos(BAR_BETIK)
    assert r.returncode == 2 and b"--repo zorunlu" in r.stderr, r.stderr.decode()[-400:]


def test_bar_stdin_cikti_verilmezse_KULLANIM_HATASI_cikis_2(tmp_path):
    r = _kos(BAR_BETIK, "--repo", str(tmp_path))
    assert r.returncode == 2 and b"--cikti zorunlu" in r.stderr, r.stderr.decode()[-400:]


def test_bar_ORTAK_bulunamazsa_KULLANIM_HATASI_cikis_2(tmp_path):
    """Sessiz yerel kopyaya düşmek yasak: ortak.py yoksa koşum DURUR ve nedeni yolları sayar."""
    bos = tmp_path / "bos_repo"
    bos.mkdir()
    r = _kos(BAR_BETIK, "--repo", str(bos), "--cikti", str(tmp_path / "c"))
    assert r.returncode == 2 and b"ortak.py bulunamad" in r.stderr, r.stderr.decode()[-400:]


def test_bar_ALPACA_SIFIR_cagri_YOK_dosya_YOK_manifest_CAGRILMADI(tmp_path):
    duzen = _bar_duzen(tmp_path)
    _, rapor, defter = _bar_kos(duzen)                 # --alpaca varsayılanı 0
    assert not defter.exists(), defter.read_text(encoding="utf-8")[:400]
    assert rapor["ozet"]["cagrildi_mi"] is False
    assert not (duzen[2] / "bars").exists()
    for k in rapor["kayitlar"]:
        assert k["durum"] == "cagrilmadi" and k["satir_n"] is None and k["neden"]


def test_bar_CSV_SEMASI_ve_DOSYA_ADI_canli_arsivle_ayni(tmp_path):
    """ELLE HESAPLANMIŞ: AAA 504 · BBB 756 · EEE 252 satır; CCC hata (dosya YOK); DDD boş cevap
    (ölçülmüş sıfır, DOSYA YAZILMAZ — barsız bir bar dosyası 'veri var' gibi okunurdu)."""
    duzen = _bar_duzen(tmp_path)
    _, rapor, defter = _bar_kos(duzen, "--alpaca", "-1")
    bars = duzen[2] / "bars"
    kayit = _kayitlar(rapor)
    assert {k: v["satir_n"] for k, v in kayit.items()} == {
        "AAA": 504, "BBB": 756, "CCC": None, "DDD": 0, "EEE": 252}
    assert kayit["CCC"]["durum"] == "olculemedi" and kayit["CCC"]["hata"].startswith("RuntimeError")
    assert kayit["DDD"]["durum"] == "bos" and not (bars / "ddd.csv").exists()
    basliklar = (bars / "aaa.csv").read_text(encoding="utf-8").splitlines()
    assert basliklar[0] == "date,open,high,low,close,volume"
    assert len(basliklar) == 1 + 504
    assert sorted(p.name for p in bars.glob("*.csv")) == ["aaa.csv", "bbb.csv", "eee.csv"]
    assert len(_cagrilar(defter)) == 5           # isim BAŞINA tek çağrı


def test_bar_PENCERE_karttan_okunur_ve_ISINMA_onde_baslar(tmp_path):
    duzen = _bar_duzen(tmp_path)
    _, rapor, defter = _bar_kos(duzen, "--alpaca", "-1")
    p = rapor["pencere"]
    assert p["kohort_baslangic"] == _PENCERE and "karttan türetildi" in p["kohort_baslangic_kaynak"]
    assert p["bar_baslangic"] == "2019-06-01"
    for c in _cagrilar(defter):
        assert c["start"] == "2019-06-01" and c["end"] == _BUGUN


def test_bar_ISINMA_penceresi_kohorttan_SONRA_olamaz_cikis_2(tmp_path):
    repo, kohort, cikti, _ = _bar_duzen(tmp_path)
    r = _kos(BAR_BETIK, "--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
             "--bugun", _BUGUN, "--baslangic", "2021-01-01")
    assert r.returncode == 2 and b"yar" in r.stderr, r.stderr.decode()[-500:]


def test_bar_KOLONLAR_data_betiginden_TURETILIR_koda_GOMULU_degil(tmp_path):
    """Sentetik data.py kolonları PERMÜTE eder; betik gerçekten türetiyorsa csv başlığı o sırayı
    taşır. Kanonik sırayı yazıyorsa şema koda gömülü demektir."""
    duzen = _bar_duzen(tmp_path, kolonlar=PERMUTE_COLS)
    _, rapor, _ = _bar_kos(duzen, "--alpaca", "1")
    assert rapor["sozlesmeler"]["bar_csv_kolonlari"] == PERMUTE_COLS
    basliklar = (duzen[2] / "bars" / "aaa.csv").read_text(encoding="utf-8").splitlines()
    assert basliklar[0] == ",".join(PERMUTE_COLS)


def test_bar_MANIFEST_sha_DISKTEKI_dosyayla_ayni(tmp_path):
    import hashlib
    duzen = _bar_duzen(tmp_path)
    _, rapor, _ = _bar_kos(duzen, "--alpaca", "1")
    k = _kayitlar(rapor)["AAA"]
    disk = (duzen[2] / "bars" / k["dosya"]).read_bytes()
    assert k["sha256"] == hashlib.sha256(disk).hexdigest()
    assert rapor["girdi"]["ortak_py_sha256"] and rapor["hukum"] == "YOK — Rol-1"
    assert rapor["okuyan"] and rapor["yazim_beyani"]


def test_bar_VAR_OLAN_dosya_YENIDEN_CEKILMEZ(tmp_path):
    """PIT girdisi donuktur: dosyası olan isim için ÇAĞRI BİLE atılmaz (bedel ve donukluk)."""
    duzen = _bar_duzen(tmp_path)
    _bar_kos(duzen, "--alpaca", "1")                    # AAA yazıldı
    (duzen[2]).rename(duzen[2])                         # yol aynı; manifest birikecek
    for eski in sorted(duzen[2].glob("bars_manifest_*.json")):
        eski.unlink()
    duzen[3].unlink()                                    # defteri sıfırla
    _, rapor, defter = _bar_kos(duzen, "--alpaca", "-1")
    k = _kayitlar(rapor)
    assert k["AAA"]["durum"] == "atlandi_mevcut" and "yeniden ÇEKİLMEDİ" in k["AAA"]["neden"]
    assert "AAA" not in [c["symbols"][0] for c in _cagrilar(defter)]
    assert k["BBB"]["durum"] == "yazildi"


def test_bar_YENIDEN_CEK_ayrisan_icerik_YAN_DOSYAYA_uzerine_YAZMAZ(tmp_path):
    """MUTASYON HEDEFİ (d): üzerine-yazma koruması kaldırılırsa özgün dosya EZİLİR ve bu çivi
    kırmızıya döner. Ayrışma SESSİZ değil, DOSYA olarak görünür."""
    import hashlib
    duzen = _bar_duzen(tmp_path)
    _bar_kos(duzen, "--alpaca", "1")
    hedef = duzen[2] / "bars" / "aaa.csv"
    sahte = "date,open,high,low,close,volume\n2020-01-02,1,1,1,1,1\n"
    hedef.write_text(sahte, encoding="utf-8")            # diskte FARKLI bir seri var
    for eski in sorted(duzen[2].glob("bars_manifest_*.json")):
        eski.unlink()
    _, rapor, _ = _bar_kos(duzen, "--alpaca", "1", "--yeniden-cek")
    k = _kayitlar(rapor)["AAA"]
    assert k["durum"] == "yan_dosya" and k["yan_dosya"] and "AYRIŞMA" in k["neden"]
    assert hedef.read_text(encoding="utf-8") == sahte, "ÖZGÜN DOSYA EZİLDİ — koruma düştü"
    assert k["sha256"] == hashlib.sha256(sahte.encode()).hexdigest()
    yan = duzen[2] / "bars" / k["yan_dosya"]
    assert yan.exists() and len(yan.read_text(encoding="utf-8").splitlines()) == 1 + 504


def test_bar_YENIDEN_CEK_ayni_icerik_DEGISMEDI_yazim_YOK(tmp_path):
    duzen = _bar_duzen(tmp_path)
    _bar_kos(duzen, "--alpaca", "1")
    for eski in sorted(duzen[2].glob("bars_manifest_*.json")):
        eski.unlink()
    _, rapor, _ = _bar_kos(duzen, "--alpaca", "1", "--yeniden-cek")
    assert _kayitlar(rapor)["AAA"]["durum"] == "degismedi"
    assert not list((duzen[2] / "bars").glob("aaa__*.csv"))


def test_bar_YALNIZ_EKSIK_yalnizca_eksikleri_ceker(tmp_path):
    """ELLE: ilk koşumda AAA/BBB/EEE yazıldı, DDD 'bos' (ÖLÇÜLMÜŞ SIFIR), CCC 'olculemedi'.
    `--yalniz-eksik` yalnız CCC'yi hedefler: yazılmışlar da, ölçülmüş sıfır da yeniden SORULMAZ."""
    duzen = _bar_duzen(tmp_path)
    _, ilk, defter = _bar_kos(duzen, "--alpaca", "-1")
    onceki = sorted(duzen[2].glob("bars_manifest_*.json"))[-1]
    onceki_yedek = tmp_path / "onceki.json"
    onceki_yedek.write_bytes(onceki.read_bytes())
    onceki.unlink()
    defter.unlink()
    _, rapor, defter2 = _bar_kos(duzen, "--alpaca", "-1", "--yalniz-eksik", str(onceki_yedek))
    assert [c["symbols"][0] for c in _cagrilar(defter2)] == ["CCC"]
    assert rapor["ozet"]["hedef_n"] == 1
    assert rapor["ozet"]["oncekinden_devralinan_n"] == 4
    assert _kayitlar(rapor)["AAA"]["satir_n"] == 504     # önceki kayıt AYNEN devralındı


def test_bar_YALNIZ_EKSIK_KOHORT_SHA_uyusmazsa_cikis_2(tmp_path):
    duzen = _bar_duzen(tmp_path)
    _, ilk, _ = _bar_kos(duzen, "--alpaca", "1")
    onceki = sorted(duzen[2].glob("bars_manifest_*.json"))[-1]
    ham = json.loads(onceki.read_text(encoding="utf-8"))
    ham["girdi"]["kohort_csv_sha256"] = "0" * 64
    bozuk = tmp_path / "bozuk.json"
    bozuk.write_text(json.dumps(ham, ensure_ascii=False), encoding="utf-8")
    repo, kohort, cikti, defter = duzen
    r = _kos(BAR_BETIK, "--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
             "--bugun", _BUGUN, "--bekleme-sn", "0", "--alpaca", "-1",
             "--yalniz-eksik", str(bozuk), defter=defter)
    assert r.returncode == 2 and b"sha256" in r.stderr, r.stderr.decode()[-500:]


def test_bar_SINIF_HISSE_anahtari_NOKTAYA_cevrilir_ve_dosya_adi_TIRE(tmp_path):
    """MUTASYON HEDEFİ (c): dönüşüm kaldırılırsa BRK-B/MOG-A sentetik uca TİRE ile gider, 400 alır
    ve satir_n None olur. ELLE: AA 1000 · BRK.B 400 · MOG.A 252 · MP 300 · TST-AB desen DIŞI → 400."""
    duzen = _bar_duzen(tmp_path, kohort_metni=KOHORT_SINIF_CSV)
    _, rapor, defter = _bar_kos(duzen, "--alpaca", "-1")
    k = _kayitlar(rapor)
    assert {s: v["alpaca_anahtar"] for s, v in k.items()} == {
        "AA": "AA", "BRK-B": "BRK.B", "MOG-A": "MOG.A", "MP": "MP", "TST-AB": "TST-AB"}
    assert {s: v["satir_n"] for s, v in k.items()} == {
        "AA": 1000, "BRK-B": 400, "MOG-A": 252, "MP": 300, "TST-AB": None}
    assert [c["symbols"][0] for c in _cagrilar(defter)] == ["AA", "BRK.B", "MOG.A", "MP", "TST-AB"]
    # DOSYA ADI canlı arşivin kuralıyla: MOG-A → MOG.A → mog-a.csv (tire, nokta değil)
    assert (duzen[2] / "bars" / "mog-a.csv").exists()
    assert (duzen[2] / "bars" / "brk-b.csv").exists()


# =================================================================================================
# §D — VERİ_EDGAR
# =================================================================================================
def test_edgar_stdin_repo_verilmezse_KULLANIM_HATASI_cikis_2():
    r = _kos(EDGAR_BETIK)
    assert r.returncode == 2 and b"--repo zorunlu" in r.stderr, r.stderr.decode()[-400:]


def test_edgar_SEC_SIFIR_ISTEK_DEFTERI_hic_olusmaz(tmp_path):
    """"Ağa çıkılmadı" iddiası VARSAYIM DEĞİL ÖLÇÜMDÜR: betik her isteği ATMADAN ÖNCE deftere
    yazar, `--sec 0` koşumunda defter hiç doğmamalıdır."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    assert not (cikti / "edgar" / "istek_defteri.jsonl").exists()
    assert kaynak["cekim"]["sec"] == 0 and kaynak["cekim"]["atilan_istek_n"] == 0


def test_edgar_SEC_BIR_ama_hepsi_DISKTE_ise_ISTEK_ATILMAZ(tmp_path):
    """download.py disiplini: var olan dosya YENİDEN İNDİRİLMEZ. Hepsi diskteyken `--sec 1` bile
    tek istek atmaz — çivi bunu defterin YOKLUĞUYLA ölçer (ağa çıkmadan sınanabilen tek biçim)."""
    kohort, cikti = _edgar_duzen(tmp_path, ciklar=(111, 222, 333, 444, 910521))
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "1")
    assert not (cikti / "edgar" / "istek_defteri.jsonl").exists()
    assert kaynak["cekim"]["atilan_istek_n"] == 0
    # BEŞ ham dosya diskte ama çekim listesi DÖRT CIK'tir: 444 (CNXC) `cift` hükmüyle eşlemeden
    # ÇIKARILDI (Rol-1 2026-09-14) — "diskte hazır" sayısı by_cik'i izler, ham dizini değil.
    assert kaynak["cekim"]["diskte_hazir_n"] == 4


def test_edgar_ESLEME_SIRASI_harita_sonra_tickers_sonra_cift_sonra_eslesmedi(tmp_path):
    """ELLE: DECK gerçek edgar_facts haritasında (kaynak 1) · AAA/BBB sentetik tickers'ta
    (kaynak 2) · HTA `esle:HTA->HR` ile HR üzerinden · ZZZZ hiçbir yerde → EŞLEŞMEYEN (CIK
    UYDURULMAZ). AMCX `cift:AMCX->CNXC` ile CNXC'ye ÇÖZÜLÜR ama Rol-1 hükmü (2026-09-14) gereği
    EŞLEŞMEYENE düşer — sıra çivisi bu yüzden dört eşleşen, iki eşleşmeyen ölçer."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    harita = json.loads((cikti / "edgar" / "cik_haritasi_sp400.json").read_text(encoding="utf-8"))
    kayit = {r["symbol"]: r for r in harita["eslesen"]}
    assert kayit["DECK"]["cik_kaynak"] == "edgar_facts_cik_haritasi"
    assert kayit["DECK"]["cik"] == 910521
    assert kayit["AAA"]["cik_kaynak"] == "sec_company_tickers" and kayit["AAA"]["cik"] == 111
    assert kayit["HTA"]["cik"] == 333 and kayit["HTA"]["cik_kaynak"].startswith(
        "elle_esleme_cifti:esle:HTA->HR")
    assert "AMCX" not in kayit, "cift ANOTASYONU eşleşene SIZDI (Rol-1 hükmü 2026-09-14)"
    assert sorted(r["symbol"] for r in harita["eslesmeyen"]) == ["AMCX", "ZZZZ"]
    assert harita["esleme_sirasi"] == ["edgar_facts_cik_haritasi", "sec_company_tickers",
                                       "elle_esleme_cifti"]
    assert kaynak["esleme"]["eslesen_n"] == 4 and kaynak["esleme"]["eslesmeyen_n"] == 2


def test_edgar_CIFT_turetilen_REDDEDILIR_esle_ise_KULLANILIR(tmp_path):
    """İKİ JETON, İKİ HÜKÜM (Rol-1 2026-09-14). `esle:` bir KİMLİKTİR (aynı ihraççı) → eşleme
    KULLANILIR. `cift:` bir ANOTASYONDUR (iki yarım satır, aynı endeks olayı) → aynı ihraççı
    KANITLANMADIĞI için eşleme REDDEDİLİR, sembol eşleşmeyene NEDENİYLE düşer.

    Ayrım kaydın kendisinde de görünür kalmalı: `cift_turetilen` listesi (TANI) ve kayıttaki
    jeton sözlüğü hükmü ADIYLA söyler — "reddedildi" sessiz bir eksilme olamaz."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    harita = json.loads((cikti / "edgar" / "cik_haritasi_sp400.json").read_text(encoding="utf-8"))
    kayit = {r["symbol"]: r for r in harita["eslesen"]}
    assert "AMCX" not in kayit
    assert kayit["HTA"]["kimlik_kaniti"] == "yeniden_adlandirma" and kayit["HTA"]["uyari"] is None
    red = {r["symbol"]: r for r in harita["eslesmeyen"]}["AMCX"]
    assert red["neden"].startswith("cift_anotasyon") and red["reddedilen_cik"] == 444
    assert red["reddedilen_kaynak"].startswith("elle_esleme_cifti:cift:AMCX->CNXC")
    cift = kaynak["esleme"]["cift_turetilen"]
    assert [r["symbol"] for r in cift] == ["AMCX"]
    assert cift[0]["kimlik_kaniti"] == "anotasyon_cift" and cift[0]["uyari"]
    assert kaynak["esleme"]["cift_turetilen_hukmu"] == red["neden"]
    assert kaynak["sozlesmeler"]["karar_jetonlari"]["cift"].startswith("ANOTASYON")
    assert "KULLANILMAZ" in kaynak["sozlesmeler"]["karar_jetonlari"]["cift"]


def test_edgar_CIFT_CIK_CEKIME_ve_PIT_SERISINE_sizmaz(tmp_path):
    """ROL-1 HÜKMÜ 2026-09-14 — REGRESYON ÇİVİSİ. `cift:AMCX->CNXC` iki yarım satırın
    ANOTASYONUdur: AMCX ile CNXC AYRI İHRAÇÇILARDIR. CNXC'nin CIK'i (444) diskte HAZIR bir
    companyfacts taşısa BİLE AMCX ne çekim listesine (`by_cik` → indirme manifesti) ne de PIT
    serisine girmelidir — girseydi CNXC'nin hisse adedi AMCX ADINA kitaplanırdı (kimlik hatası).

    Fikstür bunu ölçülebilir kılar: ham dosya 444 için VARDIR. Yani sızıntının yokluğu "dosya
    yoktu" diye değil, FİLTRE yüzündendir — iki durum birbirine karışmasın diye ayrıca
    `eksik_dosya`da da görünmediği ölçülür.

    MUTASYON HEDEFİ (g): `main`deki `kimlik_kaniti != anotasyon_cift` filtresi kaldırılırsa 444
    manifeste girer VE AAA'nın sentetik satırları `symbol=AMCX` adına seriye yazılır — bu çivi
    üç ayrı assert'ten kırmızıya döner."""
    kohort, cikti = _edgar_duzen(tmp_path, ciklar=(111, 444))
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    assert not (cikti / "edgar" / "istek_defteri.jsonl").exists()

    # (1) ÇEKİM: 444 by_cik'e hiç girmediği için indirme manifestinde YOK
    manifest_cikler = {m["cik"] for m in kaynak["cekim"]["manifest"]}
    assert manifest_cikler == {111, 222, 333, 910521}, manifest_cikler
    assert "AMCX" not in {s for m in kaynak["cekim"]["manifest"] for s in m["symbols"]}

    # (2) ÇIKARIM: seride AMCX adına TEK satır yok (ham dosya diskte OLMASINA rağmen)
    assert (cikti / "edgar" / "raw" / "CIK0000000444.json.gz").exists(), "fikstür kurulmadı"
    satirlar = _seri_oku(cikti)
    assert {r["symbol"] for r in satirlar["satirlar"]} == {"AAA"}
    assert 444 not in {e["cik"] for e in kaynak["kapsam"]["eksik_dosya"]}

    # (3) TANI İZİ KAYBOLMAZ: eşleşmeyene NEDENİYLE düşer, `cift_turetilen` onu ADIYLA taşır
    eslesmeyen = {r["symbol"]: r for r in kaynak["esleme"]["eslesmeyen"]}
    assert "AMCX" in eslesmeyen and eslesmeyen["AMCX"]["neden"].startswith("cift_anotasyon")
    assert eslesmeyen["AMCX"]["reddedilen_cik"] == 444
    assert [r["symbol"] for r in kaynak["esleme"]["cift_turetilen"]] == ["AMCX"]


def test_edgar_CIKARIM_etiket_kumesi_ve_ON_ALTI_kolon(tmp_path):
    """MUTASYON HEDEFİ (a): etiket kümesi daraltılırsa (örn. WeightedAverage… düşerse) AAA'nın
    satırı 4'ten 3'e iner ve bu çivi kırmızıya döner. `Assets` küme DIŞIDIR ve hiç görünmemeli."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    satirlar = _seri_oku(cikti)
    assert satirlar["basliklar"] == kaynak["sozlesmeler"]["kolonlar"]
    assert len(satirlar["basliklar"]) == 16
    aaa = [r for r in satirlar["satirlar"] if r["symbol"] == "AAA"]
    assert len(aaa) == _BEKLENEN_AAA_SATIR, aaa
    assert {r["tag"] for r in aaa} == {"EntityCommonStockSharesOutstanding",
                                       "CommonStockSharesIssued",
                                       "WeightedAverageNumberOfSharesOutstandingBasic"}
    assert "Assets" not in {r["tag"] for r in satirlar["satirlar"]}
    wavg = [r for r in aaa if r["tag"].startswith("WeightedAverage")][0]
    assert wavg["donem_gun"] == "90" and wavg["donem_turu"] == "ceyrek"
    dei = [r for r in aaa if r["taxonomy"] == "dei"]
    assert len(dei) == _BEKLENEN_AAA_DEI and all(r["donem_turu"] == "anlik" for r in dei)


def test_edgar_FILED_BOS_satir_REDDEDILIR_ve_SAYILIR(tmp_path):
    """MUTASYON HEDEFİ (b): `filed` kapısı kaldırılırsa `filed` boş satır seriye girer (AAA 5
    satır olur) ve red sayacı 0'a düşer — bu çivi iki yerden birden kırmızıya döner.
    PIT: `filed` değerin BİLİNİR olduğu gündür; o gün yoksa satır hiçbir as-of soruya cevap veremez."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    satirlar = _seri_oku(cikti)
    assert all(r["filed"] for r in satirlar["satirlar"]), "filed BOŞ satır seriye SIZDI"
    assert not any(r["val"] == "1100.0" for r in satirlar["satirlar"])
    assert kaynak["pit_beyani"]["filed_bos_reddedilen_satir_n"] == _BEKLENEN_FILED_BOS
    assert kaynak["pit_beyani"]["end_ile_filtre"] is False


def test_edgar_END_ile_FILTRE_YOK_pencere_disi_end_kalir(tmp_path):
    """PIT kuralı `filed`e bakar; `end` yalnız dönem etiketidir. Pencere başından (2020-07-27)
    ÇOK önceki bir `end` taşıyan satır DÜŞMEMELİ — düşseydi ölçüm kendi geçmişini kırpardı."""
    kohort, cikti = _edgar_duzen(tmp_path)
    _edgar_kos(kohort, cikti, "--sec", "0")
    satirlar = _seri_oku(cikti)
    endler = {r["end"] for r in satirlar["satirlar"] if r["symbol"] == "AAA"}
    assert "2019-01-31" in endler, endler


def test_edgar_KAPSAM_ve_HAM_DOSYASI_OLMAYAN_cik_ADIYLA_dusulur(tmp_path):
    """"Çekilmedi" ile "veri yok" AYRI: ham dosyası olmayan CIK `eksik_dosya` listesine NEDENİYLE
    yazılır ve kapsam dosyasında görünmez (uydurma yasağı)."""
    kohort, cikti = _edgar_duzen(tmp_path, ciklar=(111,))
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    eksik = {e["cik"] for e in kaynak["kapsam"]["eksik_dosya"]}
    # 444 (CNXC) BURADA DA YOK: "ham dosyası eksik" değil, eşlemeden ÇIKARILMIŞ bir CIK'tir —
    # iki durum karışmasın diye ayrıca `..._CIFT_CIK_CEKIME_ve_PIT_SERISINE_sizmaz` ölçer.
    assert eksik == {222, 333, 910521}, eksik
    assert all(e["neden"] for e in kaynak["kapsam"]["eksik_dosya"])
    kapsam = (cikti / "edgar" / "sembol_kapsam_sp400.csv").read_text(encoding="utf-8").splitlines()
    assert kapsam[0].split(",")[:4] == ["symbol", "cik", "satir_n", "shares_dei_n"]
    assert len(kapsam) == 2 and kapsam[1].startswith("AAA,111,4,2")


def test_edgar_KAYIT_hukum_YOK_ve_OKUYAN_yazili(tmp_path):
    kohort, cikti = _edgar_duzen(tmp_path)
    _, kaynak = _edgar_kos(kohort, cikti, "--sec", "0")
    assert kaynak["hukum"] == "YOK — Rol-1"
    assert kaynak["okuyan"] and kaynak["yazim_beyani"]
    assert kaynak["girdi"]["ortak_py_sha256"] and kaynak["girdi"]["kohort_csv_sha256"]
    assert kaynak["seri"]["gz_sha256"] and kaynak["seri"]["duz_sha256"]


def _seri_oku(cikti: pathlib.Path) -> dict:
    """shares_outstanding_sp400.csv.gz → {basliklar, satirlar}. pandas'a bağlanılmaz: çivi
    dosyanın METNİNİ ölçer (şema iddiası bir kolon LİSTESİ iddiasıdır)."""
    import csv as _csv
    ham = gzip.decompress((cikti / "edgar" / "shares_outstanding_sp400.csv.gz").read_bytes())
    satirlar = list(_csv.reader(ham.decode("utf-8").splitlines()))
    basliklar = satirlar[0]
    return {"basliklar": basliklar,
            "satirlar": [dict(zip(basliklar, s)) for s in satirlar[1:]]}
