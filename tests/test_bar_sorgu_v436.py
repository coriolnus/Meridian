"""v436 — `ops/bar_sorgu.py` çivileri: bar arşivinin DuckDB okuma yüzeyi
(TSK-020 [UYGULA-3] Task 2, 2026-09-07).

NUMARA SEÇİMİ: v435 ile aynı ölçümden (2026-09-07) — en büyük alınmış numara v434, v435/v436
boştu; v435 bu turda `test_bar_arsivle_v435.py`ye verildi, v436 bu dosyanındır.

FİKSTÜR TASARIM-1'İN ARACIYLA ÜRETİLİR (elle yazılmış parquet DEĞİL): arşivi `ops/bar_arsivle.py`
yazar, sorguyu `ops/bar_sorgu.py` okur. İkisini elle yazılmış bir dosya üzerinde buluşturmak,
şema ayrışmasını (yazıcı bir sütunu değiştirir, okuyucu eskisini okumaya devam eder) çivinin
GÖREMEYECEĞİ yere taşırdı. TEK istisna `dikis` çivisidir: `ayarlama_olcegi` CSV'de YOK, yani
arşivde her zaman NULL — dolu bir sütunun davranışı ancak sentetik bir parquet ile ölçülebilir
ve o çivi bunu AÇIKÇA yapar.

NEDEN `main([...])`, `subprocess` DEĞİL: v435 başlığındaki ölçülmüş gerekçenin aynısı — bu araç
takvimi `meridian.adapters.data`dan ithal eder ve o modül `meridian.obs`a ulaşır.

NEYİ ÇİVİLER:
  1. KAPSAM — sembol × ilk/son gün × satır, arşivin İÇERİĞİNDEN (dosya adından sembol).
  2. DİKİŞ — `ayarlama_olcegi` bir önceki güne göre değişen günler; sütun NULL ise "ÖLÇÜLEMEDİ"
     BEYANI (0 satır + gerekçe), sessiz boş sonuç DEĞİL.
  3. BOŞLUK — takvim `meridian.adapters.data`dan İTHAL edilir, KOPYALANMAZ: takvim değişince
     sonuç değişir (çivi bunu yamayla ölçer).
  4. SELECT MUHAFIZI İTHALDİR — `ops/olay_sorgu.py`nin `select_kapisi` fonksiyonunun TA KENDİSİ
     (kimlik kıyası), kopya değil; SELECT dışı ve çok-ifadeli sorgu rc 3.
  5. ÇIKIŞ KODLARI — 0 ok · 1 arşiv yok/boş · 2 kullanım hatası · 3 sorgu reddedildi ·
     4 takvim ölçülemedi.

GERÇEK ARŞİVE DOKUNULMAZ: her çivi `sandbox_state` altında koşar, arşivini `tmp_path`e kurar.
"""

from __future__ import annotations

import json

import duckdb
import pytest

from meridian.adapters import data as _data
from ops import bar_arsivle, bar_sorgu, olay_sorgu


OCAK = "2024-01"


def _seanslar(ay: str, adet: int) -> list[str]:
    ses = sorted(g for g in _data._sessions() if g.startswith(ay))
    if len(ses) < adet:
        pytest.skip(f"takvim ölçülemedi ya da {ay} için {adet} seans yok (bulunan: {len(ses)})")
    return ses[:adet]


def _csv_yaz(dizin, ad: str, gunler: list[str], baslangic: float = 100.0) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = ["date,open,high,low,close,volume"]
    for i, g in enumerate(gunler):
        c = baslangic + i
        satirlar.append(f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000000 + i}")
    (dizin / ad).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


@pytest.fixture
def arsiv(tmp_path, sandbox_state):
    """AAPL: Ocak'ın ilk 6 seansından 3.'sü ATLANMIŞ (boşluk çivisi için) · MSFT: ilk 4 seans."""
    kaynak = tmp_path / "bars"
    gunler = _seanslar(OCAK, 6)
    _csv_yaz(kaynak, "aapl.csv", [g for i, g in enumerate(gunler) if i != 2])
    _csv_yaz(kaynak, "msft.csv", _seanslar(OCAK, 4), baslangic=300.0)
    hedef = tmp_path / "barlar"
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    assert rc == 0, "fikstür arşivi kurulamadı"
    return hedef, gunler


# ---------------------------------------------------------------------------------------------
# 1. KAPSAM
# ---------------------------------------------------------------------------------------------

def test_KAPSAM_sembol_ilk_son_satir(arsiv, capsys):
    hedef, gunler = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--json"])
    cikti = capsys.readouterr().out.strip().splitlines()
    assert rc == 0
    kayitlar = {json.loads(s)["sembol"]: json.loads(s) for s in cikti}
    assert set(kayitlar) == {"AAPL", "MSFT"}
    assert kayitlar["AAPL"]["satir"] == 5 and kayitlar["MSFT"]["satir"] == 4
    assert kayitlar["AAPL"]["ilk"] == gunler[0] and kayitlar["AAPL"]["son"] == gunler[5]


def test_KAPSAM_metin_tablosu(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert "sembol" in cikti and "AAPL" in cikti and "MSFT" in cikti


def test_SEMBOL_suzgeci(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--sembol", "msft"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert "MSFT" in cikti and "AAPL" not in cikti


def test_AY_suzgeci_bos_ayda_0_satir(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--ay", "2023-05"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert "(0 satır)" in cikti


# ---------------------------------------------------------------------------------------------
# 2. DİKİŞ
# ---------------------------------------------------------------------------------------------

def test_DIKIS_sutun_NULL_ise_OLCULEMEDI_beyani(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis"])
    yakala = capsys.readouterr()
    assert rc == 0
    assert "(0 satır)" in yakala.out
    assert "ÖLÇÜLEMEDİ" in yakala.err
    assert "ayarlama_olcegi" in yakala.err
    assert "eksik_sutunlar" in yakala.err


def test_DIKIS_gercek_olcek_degisimini_bulur(tmp_path, sandbox_state, capsys):
    """`ayarlama_olcegi` DOLU bir arşivde dikiş günü bulunur.

    Bu parquet ELLE yazılır ve gerekçesi dosya başlığındadır: CSV'de o sütun YOKTUR, dolayısıyla
    Task-1 aracı onu hiçbir zaman doldurmaz — dolu sütunun davranışı başka türlü ölçülemez.

    ŞEMA TASARIM-1'DEN TÜRETİLİR, ELLE YAZILMAZ: sütun adları ve tipleri `bar_arsivle`nin
    `SUTUNLAR`/`SUTUN_TIPLERI` sözlüklerinden okunur. Elle yazıldığında ÖLÇÜLDÜ (2026-09-07):
    `1.0` literali DuckDB'de DECIMAL doğar, arşivin DOUBLE'ı değil — fikstür sessizce BAŞKA bir
    şemayı test ederdi (ve `--json` çıktısında sayı yerine dize görünürdü)."""
    hedef = tmp_path / "barlar"
    (hedef / OCAK).mkdir(parents=True)
    g = _seanslar(OCAK, 4)
    olcekler = [1.0, 1.0, 0.5, 0.5]
    tipli = ", ".join(f"{s} {bar_arsivle.SUTUN_TIPLERI[s]}" for s in bar_arsivle.SUTUNLAR)
    degerler = ", ".join(
        f"(DATE '{gun}', 1.0, 1.0, 1.0, 1.0, 10, NULL, {o})" for gun, o in zip(g, olcekler))
    con = duckdb.connect()
    try:
        con.execute(f"CREATE TABLE t ({tipli})")
        con.execute(f"INSERT INTO t VALUES {degerler}")
        con.execute(f"COPY (SELECT * FROM t) TO '{hedef / OCAK / 'TEST.parquet'}' "
                    "(FORMAT PARQUET)")
    finally:
        con.close()

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()]
    assert len(satirlar) == 1, satirlar
    assert satirlar[0]["sembol"] == "TEST"
    assert satirlar[0]["tarih"] == g[2]
    assert satirlar[0]["onceki_olcek"] == 1.0 and satirlar[0]["olcek"] == 0.5
    assert "ÖLÇÜLEMEDİ" not in yakala.err


# ---------------------------------------------------------------------------------------------
# 3. BOŞLUK — takvim İTHAL EDİLİR
# ---------------------------------------------------------------------------------------------

def test_BOSLUK_eksik_seansi_bulur(arsiv, capsys):
    hedef, gunler = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "bosluk", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    kayitlar = {json.loads(s)["sembol"]: json.loads(s) for s in yakala.out.strip().splitlines()}
    assert kayitlar["AAPL"]["eksik"] == 1
    assert kayitlar["AAPL"]["ilk_eksik"] == gunler[2]
    assert kayitlar["MSFT"]["eksik"] == 0, "kapsamı içinde boşluğu olmayan sembol EKSİK sayıldı"


def test_BOSLUK_TAKVIM_ITHAL_kopya_DEGIL(arsiv, capsys, monkeypatch):
    """Takvim yamalanınca sonuç DEĞİŞİR — yani araç `meridian.adapters.data`nın `_sessions`
    fonksiyonunu ÇAĞIRIYOR, kendi tatil listesini taşımıyor. Kopya taşısaydı bu çivi yeşil
    kalırdı ve takvim güncellemesi arşiv tarafında sessizce eskirdi."""
    hedef, gunler = arsiv
    gercek = set(_data._sessions())
    monkeypatch.setattr(_data, "_sessions", lambda: frozenset(gercek - {gunler[2]}))
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "bosluk", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    kayitlar = {json.loads(s)["sembol"]: json.loads(s) for s in yakala.out.strip().splitlines()}
    assert kayitlar["AAPL"]["eksik"] == 0, "takvim yaması sonucu DEĞİŞTİRMEDİ — kopya kullanılıyor"


def test_TAKVIM_olculemezse_rc4(arsiv, capsys, monkeypatch):
    hedef, _ = arsiv
    monkeypatch.setattr(_data, "_sessions", frozenset)
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "bosluk"])
    hata = capsys.readouterr().err
    assert rc == 4
    assert "takvim" in hata.lower() and "ölçülemedi" in hata.lower()


# ---------------------------------------------------------------------------------------------
# 4. SELECT MUHAFIZI — İTHAL
# ---------------------------------------------------------------------------------------------

def test_SELECT_kapisi_ITHAL_kopya_degil():
    assert bar_sorgu.select_kapisi is olay_sorgu.select_kapisi


def test_SQL_SELECT_kabul_edilir(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sql",
                         "SELECT sembol, count(*) AS n FROM barlar GROUP BY sembol ORDER BY 1",
                         "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()]
    assert satirlar == [{"sembol": "AAPL", "n": 5}, {"sembol": "MSFT", "n": 4}]


@pytest.mark.parametrize("sql", [
    "DROP TABLE barlar",
    "CREATE TABLE x AS SELECT * FROM barlar",
    "SELECT 1; DROP TABLE barlar",
    "PRAGMA database_list",
])
def test_SQL_SELECT_disi_reddedilir_rc3(arsiv, capsys, sql):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sql", sql])
    hata = capsys.readouterr().err
    assert rc == 3, hata
    assert "reddedildi" in hata


# ---------------------------------------------------------------------------------------------
# 5. ÇIKIŞ KODLARI
# ---------------------------------------------------------------------------------------------

def test_DIZIN_YOK_rc1(tmp_path, sandbox_state, capsys):
    rc = bar_sorgu.main(["--dizin", str(tmp_path / "yok"), "--sorgu", "kapsam"])
    assert rc == 1
    assert "bulunamadı" in capsys.readouterr().err


def test_BOS_DIZIN_rc1_ve_ACIKLAMA(tmp_path, sandbox_state, capsys):
    bos = tmp_path / "barlar"
    bos.mkdir()
    rc = bar_sorgu.main(["--dizin", str(bos), "--sorgu", "kapsam"])
    hata = capsys.readouterr().err
    assert rc == 1
    assert "parquet" in hata and "bar_arsivle" in hata


def test_SORGU_ve_SQL_birlikte_rc2(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--sql", "SELECT 1"])
    assert rc == 2
    assert "birlikte kullanılamaz" in capsys.readouterr().err


def test_HICBIRI_verilmezse_rc2(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef)])
    assert rc == 2
    assert "--sorgu" in capsys.readouterr().err


def test_OPERATOR_KOSUMU_uctan_uca(tmp_path, sandbox_state, capsys):
    """İKİ ARACIN OPERATÖRÜN YAZACAĞI SIRAYLA, GERÇEK argv İLE koşumu — teslim kapısı.

    NEDEN AYRI BİR ÇİVİ (vaka 2026-08-30): 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu,
    çünkü hiçbir çivi aracı operatörün koşacağı BİÇİMDE baştan sona koşmamıştı. Buradaki zincir
    kuru koşumdan başlar, arşivi yazar ve dört okuma yüzeyinin dördünü de sırayla sorar; her
    adımın çıkış kodu ayrı ayrı ölçülür."""
    kaynak = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    _csv_yaz(kaynak, "aapl.csv", _seanslar(OCAK, 5))

    assert bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef)]) == 0
    assert not hedef.exists(), "kuru koşum yazdı"
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"]) == 0
    assert (hedef / OCAK / "AAPL.parquet").is_file()
    capsys.readouterr()

    for argv in (["--sorgu", "kapsam"], ["--sorgu", "dikis"], ["--sorgu", "bosluk"],
                 ["--sql", "SELECT count(*) AS n FROM barlar"]):
        rc = bar_sorgu.main(["--dizin", str(hedef)] + argv)
        yakala = capsys.readouterr()
        assert rc == 0, f"{argv} → rc {rc}; stderr: {yakala.err}"
        assert yakala.out.strip(), f"{argv} hiçbir şey basmadı"


def test_N_TAVANI_gorunur(arsiv, capsys):
    hedef, _ = arsiv
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--n", "1"])
    yakala = capsys.readouterr()
    assert rc == 0
    assert yakala.out.count("AAPL") + yakala.out.count("MSFT") == 1
    assert "tavan" in yakala.err.lower()
