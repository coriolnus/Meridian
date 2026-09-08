"""tests/test_ops_duzeltme_v446.py — ops düzeltme turu: iki bağımsız çekişmeli incelemenin
bulgularına karşı çiviler. TUR 1 = C1..C6 (17 bulgu; bulgular_C_ops.json + brief_C_ops.md);
TUR 2 = K1..K8 (C tesliminin incelemesi, 21 ayakta bulgu → 8 kök; inceleme_C.json +
brief_C2_ops_tur2.md). İki tur AYNI dosyada, ayrı başlıklar altında durur.

NUMARA: brief'in SABİT atadığı v446 (çakışma yok — `ls tests | grep v446` boştu).

KAPSAM (brief §Konum) — SERİ, TEK KOMUTTA:
    .venv/bin/python -m pytest tests/test_bar_arsivle_v435.py tests/test_bar_sorgu_v436.py \
        tests/test_jeton_eski_sayfalar_v437.py tests/test_hafiza_ara_v438.py \
        tests/test_bar_arsivle_bolum_v442.py tests/test_ops_duzeltme_v446.py

Bu dosya YALNIZ düzeltme turlarının YENİ çivilerini taşır; v435/v436/v437/v438/v442'ye kod
düzeyinde dokunulmadı — v438'in üç OnCalendar/Persistent/sprint değişmezi ile `kesit` tavanı
değişmezi bu dosyada da (C6/K7, C5d/K8) ayrıca ölçülür.

KOŞUM BİÇİMİ — ÖLÇÜLMÜŞ AYRIM, TEK TEK BEYANLI (TUR 2'de düzeltildi: TUR 1'in raporu C5 için
"en az bir çivi GERÇEK subprocess ile koştu" diyordu ve BU YANLIŞTI — ölçüldü, tek subprocess
koşucusu `_kos_jeton`du):
  · `ops/bar_arsivle.py` · `ops/bar_sorgu.py` — `meridian`ı İTHAL EDER (`sanitize_bars` /
    `_sessions()` üzerinden `meridian.obs`a ulaşır). Çiviler `main([...])` + `sandbox_state`
    ile SÜREÇ İÇİNDE koşar, ASLA subprocess değil (v435/v436 başlıklarının ölçülmüş gerekçesi:
    subprocess yamayı görmez ve canlı `state/events.jsonl`e yazardı).
  · `ops/jeton_css_uret.py` — `meridian` ithal ETMEZ; komut satırı çivileri `_kos_jeton`
    (gerçek subprocess). İç mekanizma (monkeypatch gerektiren) çivileri `main([...])`.
  · `research/olcumler/edg067_hindsight_faz1/taban_terfi.py` — `meridian` de ONNX de ithal
    etmez (v438 AST çivisi); GERÇEK dosya, GERÇEK süreç, sahteleme YOK (K3).
  · `research/olcumler/edg067_hindsight_faz1/hafiza_ara.py` — gerçek betik BAYT BAYT kopyalanıp
    ayrı süreçte koşar; YALNIZ kardeşi `kiyas_kos.py` sahtelenir, çünkü gerçek `taban_hazirla`
    ONNX oturumu açar ve `onnxruntime`/`tokenizers`/bge-m3 snapshot'ı YERELDE YOKTUR (K3;
    sınırın tam gerekçesi K3 bölümünün başındadır).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sqlite3
import subprocess
import sys

import duckdb
import pandas as pd
import pytest

from meridian.adapters import data as _data
from ops import bar_arsivle, bar_sorgu
from ops import jeton_css_uret as jcu
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
OCAK = "2024-01"
SUBAT = "2024-02"


def _seanslar(ay: str, adet: int) -> list[str]:
    ses = sorted(g for g in _data._sessions() if g.startswith(ay))
    if len(ses) < adet:
        pytest.skip(f"takvim ölçülemedi ya da {ay} için {adet} seans yok (bulunan: {len(ses)})")
    return ses[:adet]


# ================================================================================================
# C1 — `ops/bar_sorgu.py::sorgu_dikis` ay-sınırı dikişi (bulgu ×2, YÜKSEK)
# ================================================================================================

def _dikis_parquet_yaz(hedef: pathlib.Path, sembol: str, gunler: list[str],
                       olcekler: list[float]) -> None:
    """Sembol için TEK parquet (VARSAYILAN `sembol` yerleşimi) — `ayarlama_olcegi` DOLU.

    Şema `bar_arsivle.SUTUNLAR`/`SUTUN_TIPLERI`den TÜRETİLİR, elle yazılmaz: `1.0` literali
    DuckDB'de DECIMAL doğar (arşivin DOUBLE'ı değil) — v436'nın `test_DIKIS_gercek_olcek...`
    çivisinin aynı dersi."""
    hedef.mkdir(parents=True, exist_ok=True)
    tipli = ", ".join(f"{s} {bar_arsivle.SUTUN_TIPLERI[s]}" for s in bar_arsivle.SUTUNLAR)
    # `None` → SQL `NULL` (Python'ın "None"u DuckDB'de geçersiz bir belirteçtir). Ölçek NULL'u
    # bir uydurma DEĞİL: canlı CSV'de o sütun HİÇ yoktur (TUR 2 / K1 senaryosu bunu kullanır).
    degerler = ", ".join(
        f"(DATE '{gun}', 1.0, 1.0, 1.0, 1.0, 10, NULL, {'NULL' if o is None else o})"
        for gun, o in zip(gunler, olcekler))
    con = duckdb.connect()
    try:
        con.execute(f"CREATE TABLE t ({tipli})")
        con.execute(f"INSERT INTO t VALUES {degerler}")
        con.execute(f"COPY (SELECT * FROM t) TO '{hedef / f'{sembol}.parquet'}' "
                    "(FORMAT PARQUET)")
    finally:
        con.close()


def _kirik_sorgu_dikis(con, sembol, ay, n):
    """ESKİ (kırık) `sorgu_dikis` gövdesi — süzgeç LAG'DEN ÖNCE uygulanır. Mutasyon testinin
    kanıtı: bu gövdeyle çalıştırılan çivi KIRMIZI olmalı."""
    nerede, parametreler = bar_sorgu._suzgec(sembol, ay)
    return con.execute(
        "SELECT sembol, tarih, onceki_olcek, olcek FROM ("
        "  SELECT sembol, date AS tarih, ayarlama_olcegi AS olcek, "
        "         lag(ayarlama_olcegi) OVER (PARTITION BY sembol ORDER BY date) AS onceki_olcek "
        f"  FROM barlar{nerede}) AS _d "
        "WHERE onceki_olcek IS NOT NULL AND olcek IS DISTINCT FROM onceki_olcek "
        f"ORDER BY sembol, tarih LIMIT {int(n)}", parametreler).fetchall()


def test_C1_AY_SINIRI_dikis_ay_filtresiyle_KAYBOLMAZ(tmp_path, sandbox_state, capsys):
    """KIRMIZI-ÖNCESİ senaryo: Ocak'ın SON günü olcek=1.0, Şubat'ın İLK günü olcek=0.5 — gerçek
    bir dikiş, TAM ay sınırında. `--ay 2024-02` filtresiyle sorgulanınca dikiş YİNE görünmeli."""
    hedef = tmp_path / "barlar"
    ocak, subat = _seanslar(OCAK, 3), _seanslar(SUBAT, 3)
    gunler = ocak + subat
    olcekler = [1.0, 1.0, 1.0, 0.5, 0.5, 0.5]
    _dikis_parquet_yaz(hedef, "TEST", gunler, olcekler)

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()] if yakala.out.strip() \
        else []
    assert len(satirlar) == 1, (satirlar, yakala.err)
    assert satirlar[0]["tarih"] == subat[0]
    assert satirlar[0]["onceki_olcek"] == 1.0 and satirlar[0]["olcek"] == 0.5
    assert "ÖLÇÜLEMEDİ" not in yakala.err


def test_C1_MUTASYON_suzgec_pencereye_alinirsa_KIRMIZI(tmp_path, sandbox_state, monkeypatch,
                                                       capsys):
    """Mutasyon turu: eski (kırık) gövdeye dönünce yukarıdaki senaryo GERÇEKTEN kırmızı olmalı —
    çivi yanlış sebepten yeşil olmasın diye."""
    hedef = tmp_path / "barlar"
    ocak, subat = _seanslar(OCAK, 3), _seanslar(SUBAT, 3)
    gunler = ocak + subat
    _dikis_parquet_yaz(hedef, "TEST", gunler, [1.0, 1.0, 1.0, 0.5, 0.5, 0.5])

    monkeypatch.setattr(bar_sorgu, "sorgu_dikis", _kirik_sorgu_dikis)
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()] if yakala.out.strip() \
        else []
    assert satirlar == [], "mutasyon (süzgeç içeri alınmış) dikişi YİNE bulmuş — çivi kör"


def test_C1_SEMBOL_ay_filtreli_dikis_komut_satirindan(tmp_path, sandbox_state, capsys):
    """Ek çivi (bulgu 'test' mercek): `--sembol` + `--ay` birlikte, GERÇEK argv ile."""
    hedef = tmp_path / "barlar"
    ocak, subat = _seanslar(OCAK, 3), _seanslar(SUBAT, 3)
    gunler = ocak + subat
    _dikis_parquet_yaz(hedef, "AAA", gunler, [1.0, 1.0, 1.0, 0.5, 0.5, 0.5])
    _dikis_parquet_yaz(hedef, "BBB", gunler, [2.0, 2.0, 2.0, 2.0, 2.0, 2.0])  # dikişsiz

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--sembol", "aaa",
                        "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()]
    assert len(satirlar) == 1 and satirlar[0]["sembol"] == "AAA"


def test_C1_SEMBOL_ay_filtreli_bosluk_komut_satirindan(tmp_path, sandbox_state, capsys):
    """Ek çivi: `bosluk` `--sembol`/`--ay` birlikte hiç çalıştırılmıyordu (bulgu 'test' mercek) —
    ikili parametre-kopyalama sözleşmesi (`kapsam`+`mevcut` CTE'lerinin ikisi de aynı `nerede`yi
    taşır) burada gerçekten ısırılır."""
    kaynak = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 6)
    _csv_yaz_446(kaynak, "aapl.csv", [g for i, g in enumerate(gunler) if i != 2])  # 1 boşluk
    _csv_yaz_446(kaynak, "msft.csv", gunler)                                       # boşluksuz
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "bosluk", "--sembol", "AAPL",
                        "--ay", OCAK, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()]
    assert len(satirlar) == 1 and satirlar[0]["sembol"] == "AAPL"
    assert satirlar[0]["eksik"] == 1, satirlar


def test_C1_COK_SEMBOLLU_partition_by_SIZMAZ(tmp_path, sandbox_state, capsys):
    """Bulgu (test mercek): `dikis`in `PARTITION BY sembol`ü çok-sembollü sahnede hiç
    sınanmıyordu. A'nın son günü (olcek=1.0) B'nin ilk günüyle (olcek=0.5) YAN YANA gelse bile
    sahte bir dikiş SAYILMAMALI."""
    hedef = tmp_path / "barlar"
    g = _seanslar(OCAK, 4)
    _dikis_parquet_yaz(hedef, "AAA", g, [1.0, 1.0, 1.0, 1.0])
    _dikis_parquet_yaz(hedef, "BBB", g, [0.5, 0.5, 0.5, 0.5])

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()] if yakala.out.strip() \
        else []
    assert satirlar == [], (
        f"AAA'nın son günü ile BBB'nin ilk günü arasında SAHTE dikiş bulundu: {satirlar}")


def test_C1_MUTASYON_partition_by_kaldirilirsa_KIRMIZI(tmp_path, sandbox_state, monkeypatch,
                                                        capsys):
    hedef = tmp_path / "barlar"
    g = _seanslar(OCAK, 4)
    _dikis_parquet_yaz(hedef, "AAA", g, [1.0, 1.0, 1.0, 1.0])
    _dikis_parquet_yaz(hedef, "BBB", g, [0.5, 0.5, 0.5, 0.5])

    def _partitionsiz(con, sembol, ay, n):
        dis_kosullar = ["onceki_olcek IS NOT NULL", "olcek IS DISTINCT FROM onceki_olcek"]
        dis_param: list = []
        if sembol:
            dis_kosullar.append("sembol = ?")
            dis_param.append(sembol.upper())
        if ay:
            dis_kosullar.append("ay = ?")
            dis_param.append(ay)
        return con.execute(
            "SELECT sembol, tarih, onceki_olcek, olcek FROM ("
            "  SELECT sembol, ay, date AS tarih, ayarlama_olcegi AS olcek, "
            "         lag(ayarlama_olcegi) OVER (ORDER BY sembol, date) AS onceki_olcek "
            "  FROM barlar) AS _d "
            f"WHERE {' AND '.join(dis_kosullar)} ORDER BY sembol, tarih LIMIT {int(n)}",
            dis_param).fetchall()

    monkeypatch.setattr(bar_sorgu, "sorgu_dikis", _partitionsiz)
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()] if yakala.out.strip() \
        else []
    assert satirlar != [], "mutasyon (PARTITION BY kaldırılmış) sahte dikişi YAKALAMADI — kör çivi"


# ================================================================================================
# C2 — `ops/bar_arsivle.py::_secim_sql` dinamik sütun kümesi (bulgu ×2, ORTA)
# ================================================================================================

def _csv_yaz_446(dizin: pathlib.Path, ad: str, gunler: list[str],
                 baslangic: float = 100.0, kaynak_sutunu: bool = False) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    baslik = "date,open,high,low,close,volume" + (",kaynak" if kaynak_sutunu else "")
    satirlar = [baslik]
    for i, g in enumerate(gunler):
        c = baslangic + i
        satir = f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000000 + i}"
        if kaynak_sutunu:
            satir += ",IEX"
        satirlar.append(satir)
    (dizin / ad).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def _eski_secim_sql(kaynak_adi, mevcut_sutunlar=None):
    """Bulgu C2'nin ÖNCEKİ (kırık) `_secim_sql` gövdesi — statik `CSV_SUTUNLARI`ya bakar,
    ikinci argümanı (gerçek sütun kümesi) YOKSAYAR."""
    parcalar = []
    for s in bar_arsivle.SUTUNLAR:
        tip = bar_arsivle.SUTUN_TIPLERI[s]
        if s in bar_arsivle.CSV_SUTUNLARI:
            parcalar.append(f"CAST({s} AS {tip}) AS {s}")
        else:
            parcalar.append(f"CAST(NULL AS {tip}) AS {s}")
    return f"SELECT {', '.join(parcalar)} FROM {kaynak_adi} ORDER BY date"


def test_C2_MEVCUT_kaynak_sutunu_GERCEK_deger_yazar(sandbox_state, tmp_path):
    """CSV'ye GERÇEK bir `kaynak` sütunu eklenirse (bugün YOK, ölçüldü) manifest onu 'eksik
    değil' der VE parquet'e GERÇEK değeri yazmalı — statik tabloya bakıp NULL yazmamalı."""
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 3)
    _csv_yaz_446(kaynak_dizin, "aapl.csv", gunler, kaynak_sutunu=True)

    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    assert rc == 0

    m = json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))
    assert "kaynak" not in m["eksik_sutunlar"]["AAPL"], m["eksik_sutunlar"]

    con = duckdb.connect()
    try:
        satirlar = con.execute(
            f"SELECT kaynak FROM read_parquet('{hedef / 'AAPL.parquet'}')").fetchall()
    finally:
        con.close()
    assert satirlar and all(s[0] == "IEX" for s in satirlar), satirlar


def test_C2_MUTASYON_statik_CSV_SUTUNLARIYA_donerse_KIRMIZI(sandbox_state, tmp_path, monkeypatch):
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 3)
    _csv_yaz_446(kaynak_dizin, "aapl.csv", gunler, kaynak_sutunu=True)

    monkeypatch.setattr(bar_arsivle, "_secim_sql", _eski_secim_sql)
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    assert rc == 0

    con = duckdb.connect()
    try:
        satirlar = con.execute(
            f"SELECT kaynak FROM read_parquet('{hedef / 'AAPL.parquet'}')").fetchall()
    finally:
        con.close()
    assert all(s[0] is None for s in satirlar), (
        "mutasyon (statik CSV_SUTUNLARI) uygulanınca kaynak sütunu HÂLÂ dolu geldi — çivi kör")


# ================================================================================================
# C3 — idempotency: içerik hash + sha256 mutasyonları + hepsi-ya-hiç çok kalemli (bulgu ×3)
# ================================================================================================

def _csv_yaz_ohlcv_446(dizin: pathlib.Path, ad: str, gunler: list[str],
                       acilislar: list[float]) -> None:
    """`close` SABİT (`100+i`) kalır — yalnız `open`/`high`/`low` değişir. Böylece satır/ilk/
    son/kapanış TOPLAMI aynı kalıp yalnız bir hücre değişen bir OHLCV revizyonu üretilebilir."""
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = ["date,open,high,low,close,volume"]
    for i, (g, o) in enumerate(zip(gunler, acilislar)):
        c = 100.0 + i
        yuksek, dusuk = max(o, c) + 0.5, min(o, c) - 0.5
        satirlar.append(f"{g},{o:.2f},{yuksek:.2f},{dusuk:.2f},{c:.2f},{1000000 + i}")
    (dizin / ad).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def test_C3_OHLCV_REVIZYONU_ayni_ozet_farkli_hucre_YENIDEN_yazilir(sandbox_state, tmp_path,
                                                                    capsys):
    """Bulgu 'dogruluk': toplamı KORUYAN bir revizyon (satır/ilk/son/kapanış TOPLAMI DEĞİŞMEZ,
    yalnız `open` değişir) eski dört-özet kıyasını YANILTIRDI. İçerik hash'i bunu yakalamalı."""
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 5)
    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [100.0] * 5)
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [101.0, 99.0, 100.0, 100.0, 100.0])
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0, cikti
    assert "yazıldı" in cikti and "atlandı" not in cikti, (
        f"OHLCV revizyonu (özetler AYNI kalan) SESSİZCE atlandı: {cikti}")


def test_C3_MUTASYON_icerik_hash_SABIT_donerse_revizyon_KACAR(sandbox_state, tmp_path,
                                                              monkeypatch, capsys):
    """Mutasyon HER İKİ koşumdan ÖNCE uygulanır: `kaynak_icerik_hash` her girdi için AYNI
    (kör) değeri dönerse, birinci koşumun manifeste yazdığı hash de ikinci koşumun hesapladığı
    hash de "sabit" olur — tam da eski (düzeltmeden önceki) körlüğün taklidi. Mutasyonu yalnız
    İKİNCİ koşumdan önce uygulamak TERSİ etkiyi yapardı (birinci koşumun GERÇEK hash'iyle
    ikincinin SABİT değeri UYUŞMAZ ve yanlışlıkla 'yazıldı' çıkardı — ilk taslakta ölçüldü)."""
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 5)
    monkeypatch.setattr(bar_arsivle, "kaynak_icerik_hash", lambda dilim: "sabit")

    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [100.0] * 5)
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [101.0, 99.0, 100.0, 100.0, 100.0])
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert "atlandı" in cikti, (
        "mutasyon (içerik hash SABİT) uygulanınca revizyon YİNE 'atlandı' sayılmadı — kör çivi")


def test_C3_HEDEF_DOSYA_BOZULURSA_yeniden_yazilir(sandbox_state, tmp_path, capsys):
    """Bulgu 'test': disk sha256 kontrolü hiçbir çivide mutasyonla sınanmıyordu."""
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 4)
    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [100.0] * 4)
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    (hedef / "AAPL.parquet").write_bytes(b"bozuk parquet - elle degistirildi")
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0, cikti
    assert "yazıldı" in cikti and "atlandı" not in cikti

    con = duckdb.connect()
    try:
        n = con.execute(
            f"SELECT count(*) FROM read_parquet('{hedef / 'AAPL.parquet'}')").fetchone()[0]
    finally:
        con.close()
    assert n == 4, "yeniden yazılan dosya GEÇERSİZ (bozuk içerik kalmış olabilir)"


def test_C3_MANIFEST_SHA256_BOZULURSA_yeniden_yazilir(sandbox_state, tmp_path, capsys):
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 4)
    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [100.0] * 4)
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    m = json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))
    m["semboller"]["AAPL"]["sha256"] = "0" * 64
    (hedef / bar_arsivle.MANIFEST_ADI).write_text(json.dumps(m), encoding="utf-8")

    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0, cikti
    assert "yazıldı" in cikti and "atlandı" not in cikti


def test_C3_HEPSI_YA_HIC_coklu_kalemde_biri_duserse_manifest_YOK(sandbox_state, tmp_path,
                                                                  monkeypatch, capsys):
    """Bulgu 'test': hepsi-ya-hiç yazımı yalnız TEK kalemlik başarısızlıkla ölçülüyordu. Burada
    İKİ sembol var; yalnız MSFT'in yazımı bozulur — AAPL diskte kalsa bile manifest HİÇ
    oluşmamalı."""
    kaynak_dizin = tmp_path / "bars"
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 4)
    _csv_yaz_ohlcv_446(kaynak_dizin, "aapl.csv", gunler, [100.0] * 4)
    _csv_yaz_ohlcv_446(kaynak_dizin, "msft.csv", gunler, [200.0] * 4)

    gercek = bar_arsivle._parquet_yaz

    def _bozuk_yaz(con, df, hedef_dosya):
        # `yaz_ve_dogrula` bu fonksiyonu HEDEFE değil bir GEÇİCİ dosyaya (`.{stem}-XXXXXX.tmp`)
        # çağırır — `hedef_dosya.stem` burada tam "MSFT" DEĞİL, ".MSFT-<rastgele>"dir; `==`
        # yerine `in` ile eşle (ilk taslakta `==` HİÇBİR satırı bozmadan sessizce geçti).
        if "MSFT" in hedef_dosya.stem:
            return gercek(con, df.iloc[:-1], hedef_dosya)      # bir satır DÜŞÜR
        return gercek(con, df, hedef_dosya)

    monkeypatch.setattr(bar_arsivle, "_parquet_yaz", _bozuk_yaz)
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 5, hata
    assert (hedef / "AAPL.parquet").is_file(), "AAPL diskte kalmalıydı (bedel: yeniden yazılır)"
    assert not (hedef / bar_arsivle.MANIFEST_ADI).exists(), (
        "AAPL başarıyla yazıldı diye manifest KISMİ yazılmış — hepsi-ya-hiç ihlali")


# ================================================================================================
# C4 — `ops/jeton_css_uret.py` sayfa kipi (bulgu ×3, ORTA)
# ================================================================================================

WEB = REPO / "meridian" / "web"
URETICI = REPO / "ops" / "jeton_css_uret.py"


def _kos_jeton(*argv):
    return subprocess.run([sys.executable, str(URETICI), *argv],
                          capture_output=True, text=True, cwd=str(REPO))


def test_C4a_kontrol_ve_uygula_birlikte_KULLANIM_hatasi(tmp_path):
    """Komut satırından (subprocess): eskiden `--kontrol --uygula` birlikte verilince yazma
    SESSİZCE yutuluyordu (yalnız `--kontrol` dalına girilirdi)."""
    p = tmp_path / "runbook.html"
    p.write_text((WEB / "runbook.html").read_text(encoding="utf-8"), encoding="utf-8")
    r = _kos_jeton("--sayfa", str(p), "--kontrol", "--uygula")
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "birlikte verilemez" in r.stderr, r.stderr


def test_C4a_MUTASYON_eski_davranista_yazma_yutulurdu(tmp_path):
    """Pozitif kontrol — DÜZELTMEDEN ÖNCEKİ argparse/main() davranışını taklit eder: `--kontrol`
    ile `--uygula` birlikte verilince eski kod yalnız `--kontrol` dalına girerdi (rc'ye BAKMAKSIZIN
    hiçbir zaman yazardı). Burada doğrudan `_sayfa_kipi`yi (kontrol=True, uygula=True) ile
    çağırıp dosyanın YAZILMADIĞINI (eski sessiz-yutma) gösteriyoruz — bu YENİ `main()` kapısının
    NEDEN gerekli olduğunun kanıtı."""
    p = tmp_path / "runbook.html"
    metin = (WEB / "runbook.html").read_text(encoding="utf-8")
    bozuk = metin.replace("--bg: #fafafa;", "--bg: #fafaf0;", 1)
    p.write_text(bozuk, encoding="utf-8")
    once = p.read_text(encoding="utf-8")
    rc = jcu._sayfa_kipi([p], kontrol=True, uygula=True)
    assert rc == 1, "kontrol dalı bayat sayfayı doğru buluyor (bu davranış BEKLENEN)"
    assert p.read_text(encoding="utf-8") == once, (
        "`_sayfa_kipi` kendi başına hâlâ YAZMIYOR — asıl kapı main()'deki YENİ kontrol; "
        "bu test onun OLMADIĞI (main() bypass edildiği) senaryoyu belgeler")


def test_C4b_sayfa_kipinde_ATLANAN_uyarisi_basar(tmp_path, monkeypatch, capsys):
    """Bulgu: `_kovalar()`ın `atlanan` listesi sayfa kipinde sessizce düşüyordu. Bugünkü
    tokens.json 129/129 · 96/96 tam örtüştüğü için (v437 ölçümü) `atlanan` GERÇEKTE boş —
    mekanizma `sayfa_blogu` sahtelenerek ısırtılır (v437'nin `ESLENEMEYEN` pozitif kontrolüyle
    AYNI desen)."""
    gercek_sayfa_blogu = jcu.sayfa_blogu

    def _sahte():
        blok, _ = gercek_sayfa_blogu()
        return blok, ["kok/sahte/deger (dict: {'garip': 1})"]

    monkeypatch.setattr(jcu, "sayfa_blogu", _sahte)
    p = tmp_path / "runbook.html"
    p.write_text((WEB / "runbook.html").read_text(encoding="utf-8"), encoding="utf-8")
    rc = jcu.main([f"--sayfa={p}", "--kontrol"])
    err = capsys.readouterr().err
    assert rc in (0, 1)
    assert "ATLANAN 1 jeton" in err, err
    assert "kok/sahte/deger" in err, err


def test_C4c_ON_DOGRULAMA_yok_sayfada_hicbir_sey_YAZMADAN_durur(tmp_path):
    """Bulgu: çok-sayfalı `--uygula`da N. sayfa arızalıysa 1..N-1 ZATEN yazılmış olurdu. Ön
    doğrulama TÜM sayfalar için biter, sonra yazma başlar — birinci sayfa bayat olsa bile
    ikinci sayfa YOK diye komut YAZMADAN durmalı."""
    p1 = tmp_path / "runbook.html"
    p1.write_text(
        (WEB / "runbook.html").read_text(encoding="utf-8").replace(
            "--bg: #fafafa;", "--bg: #fafaf0;", 1), encoding="utf-8")
    once = p1.read_text(encoding="utf-8")
    p2 = tmp_path / "yok.html"

    r = _kos_jeton("--sayfa", str(p1), "--sayfa", str(p2), "--uygula")
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "YOK" in r.stderr, r.stderr
    assert p1.read_text(encoding="utf-8") == once, (
        "1. sayfa doğrulama TAMAMLANMADAN yazıldı — ön doğrulama pasosu çalışmıyor")


@pytest.mark.skipif(
    os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="izin-tabanlı yazma arızası yalnız POSIX + root-olmayan kullanıcıda ölçülebilir")
def test_C4c_KISMI_yazim_devam_eder_ve_N_M_yazildi_ozeti(tmp_path):
    """Ön doğrulamayı geçen ama GERÇEK bir G/Ç arızasıyla (izin reddi) düşen bir sayfa DİĞER
    sayfaların yazımını ENGELLEMEMELİ; sonuç exit 1 + 'N/M yazıldı' özetiyle GÖRÜNÜR olmalı.

    ARIZA DOSYA İZNİYLE DEĞİL DİZİN İZNİYLE ÜRETİLİR (K2, 2026-09-08 — atomik yazımın ÖLÇÜLMÜŞ
    BEDELİ): `os.replace` hedef dosyanın kipine değil DİZİN yazma iznine bakar, yani salt-okunur
    bir hedef DOSYA artık yazımı ENGELLEMEZ. Kazanç (yarım/kesik dosya imkânsız) bu bedelle
    alındı; bedel burada AÇIKÇA ölçülür ve `--uygula`nın izin-reddi dalı salt-okunur bir DİZİNLE
    ısırılır."""
    p1 = tmp_path / "runbook.html"
    p1.write_text(
        (WEB / "runbook.html").read_text(encoding="utf-8").replace(
            "--bg: #fafafa;", "--bg: #fafaf0;", 1), encoding="utf-8")
    once1 = p1.read_text(encoding="utf-8")
    kilitli = tmp_path / "kilitli"
    kilitli.mkdir()
    p2 = kilitli / "landing.html"
    p2.write_text(
        (WEB / "landing.html").read_text(encoding="utf-8").replace(
            "--bg: #fafafa;", "--bg: #fafaf0;", 1), encoding="utf-8")
    once2 = p2.read_text(encoding="utf-8")

    kilitli.chmod(0o555)
    try:
        r = _kos_jeton("--sayfa", str(p1), "--sayfa", str(p2), "--uygula")
    finally:
        kilitli.chmod(0o755)

    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert f"yazıldı: {p1}" in r.stdout, r.stdout
    assert "HATA" in r.stderr and str(p2) in r.stderr, r.stderr
    assert "1/2 yazıldı" in r.stderr, r.stderr
    assert p1.read_text(encoding="utf-8") != once1, "geçerli sayfa YAZILMADI"
    assert p2.read_text(encoding="utf-8") == once2, "izinsiz sayfa YİNE DE değişmiş"


# ================================================================================================
# C5 — `research/olcumler/edg067_hindsight_faz1/{hafiza_ara,taban_terfi}.py` (bulgu ×4)
# ================================================================================================

KIYAS_DIZIN = REPO / "research" / "olcumler" / "edg067_hindsight_faz1"
ARA_YOL = KIYAS_DIZIN / "hafiza_ara.py"
TERFI_YOL = KIYAS_DIZIN / "taban_terfi.py"


@pytest.fixture
def ara446():
    return betikten_modul_yukle(ARA_YOL, "hafiza_ara_v446")


@pytest.fixture
def terfi446():
    return betikten_modul_yukle(TERFI_YOL, "taban_terfi_v446")


def _sonuc446(i, dosya, bolum, metin, mesafe):
    return {"id": i, "dosya": dosya, "bolum": bolum, "metin": metin,
            "blob_sha": "%040x" % i, "mesafe": mesafe}


def _patchle446(ara, monkeypatch, sonuclar, *, kunye=None, hata=None):
    def sahte_hazirla(db_yolu, model_dir, **kw):
        if hata is not None:
            raise hata
        return (kunye or {"head_commit": "x", "dosya_sayisi": 1, "chunk_sayisi": 1,
                          "uretim_ts": "2026-09-08T00:00:00Z"}), ("DB", "GOMUCU"), lambda: None

    def sahte_sorgu(ortam, soru, k):
        return list(sonuclar)

    monkeypatch.setattr(ara, "taban_hazirla", sahte_hazirla)
    monkeypatch.setattr(ara, "taban_sorgu", sahte_sorgu)


# ---- C5a — AYIRAC (" · ") sütun kayması ----

def test_C5a_bolumde_AYIRAC_gecerse_sutun_sayisi_SABIT(ara446, monkeypatch, capsys):
    """Depo kendi belgelerinde AYNI diziyi taşıyor (ölçüldü, `docs/ARASTIRMA-SLIPAJ-AZALTMA-
    2026-08-13.md`: `### C.1 · Limit tavanını gerçekten BAĞLAYICI yap`)."""
    baslik = "### C.1 · Limit tavanını gerçekten BAĞLAYICI yap"
    _patchle446(ara446, monkeypatch, [
        _sonuc446(1, "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md", baslik, "kesit metni", 0.1),
    ])
    rc = ara446.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    satir = [s for s in out.splitlines() if not s.startswith("#")][0]
    alanlar = satir.split(ara446.AYIRAC, 4)
    assert len(alanlar) == 5, (alanlar, satir)
    assert alanlar[2] == "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md"
    assert "C.1" in alanlar[3] and "BAĞLAYICI" in alanlar[3], alanlar[3]
    assert ara446.AYIRAC not in alanlar[3], "C5a: bolum alanı AYIRAC taşıyor — sütun kayar"
    assert alanlar[4].strip() == "kesit metni", alanlar[4]


def test_C5a_MUTASYON_kacis_kaldirilirsa_sutun_KAYAR(ara446, monkeypatch, capsys):
    monkeypatch.setattr(ara446, "_kacir", lambda d: str(d))
    baslik = "### C.1 · Limit tavanını gerçekten BAĞLAYICI yap"
    _patchle446(ara446, monkeypatch, [_sonuc446(1, "docs/X.md", baslik, "kesit metni", 0.1)])
    ara446.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    out = capsys.readouterr().out
    satir = [s for s in out.splitlines() if not s.startswith("#")][0]
    alanlar = satir.split(ara446.AYIRAC, 4)
    assert alanlar[3] == "### C.1", alanlar
    assert "kesit metni" in alanlar[4] and "BAĞLAYICI" in alanlar[4], (
        f"mutasyon (kaçış kaldırılmış) sütunu KAYDIRMADI — çivi kör: {alanlar}")


# ---- C5b — ValueError yakalanmadan sızıyor ----

def test_C5b_ValueError_taban_hazirlada_OLCULEMEDI_rc3(ara446, monkeypatch, capsys):
    """K4 (2026-09-08): brief 'ölçülemedi: <neden>' öneki + AYRI bir çıkış kodu istemişti; ilk
    tur yalnız `ValueError`ı mevcut demete ekledi (önek yok, rc 1) ve sapmayı BEYAN ETMEDİ.
    ÖLÇÜLDÜ: modülün kendi sözleşmesi 2'yi argparse kullanım hatasına ayırıyor (v438
    `test_gercek_surecte_soru_eksikse_rc2`), yani brief'in verdiği 2 ÇAKIŞIR → 3 kullanılır ve
    beyan edilir. rc 1 (girdi/uzantı arızası) AYNEN kalır: 'model dizini YOK' ile 'model/şema
    ayrışmış' farklı reçetelerdir."""
    _patchle446(ara446, monkeypatch, [], hata=ValueError(
        "gömme boyutu 768, beklenen 1024 — model/şema ayrışmış"))
    rc = ara446.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    yak = capsys.readouterr()
    assert rc == 3, (rc, yak.err)
    assert yak.err.startswith("ölçülemedi:"), yak.err
    assert "ayrışmış" in yak.err, yak.err
    assert yak.out.strip() == ""


def test_C5b_GIRDI_arizasi_rc1_KALIR(ara446, monkeypatch, capsys):
    """Bedel yasası: yeni kod (3) ÖLÇÜLEMEZLİK sınıfını ayırdı — kazanç. KAYIP ölçülür: rc 1'in
    kendi sınıfı (girdi/uzantı arızası, `taban_hazirla`nın mesajı AYNEN) DEĞİŞMEDİ."""
    _patchle446(ara446, monkeypatch, [],
                hata=FileNotFoundError("model dizini YOK: /yok — taban kolu koşamaz"))
    rc = ara446.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    yak = capsys.readouterr()
    assert rc == 1, (rc, yak.err)
    assert yak.err.startswith("model dizini YOK:"), yak.err


def test_C5b_ValueError_taban_sorguda_OLCULEMEDI_rc3(ara446, monkeypatch, capsys):
    def sahte_hazirla(db_yolu, model_dir, **kw):
        return {"head_commit": "x"}, ("DB", "GOMUCU"), lambda: None

    def sahte_sorgu(ortam, soru, k):
        raise ValueError("gömme boyutu 768, beklenen 1024 — model/şema ayrışmış")

    monkeypatch.setattr(ara446, "taban_hazirla", sahte_hazirla)
    monkeypatch.setattr(ara446, "taban_sorgu", sahte_sorgu)
    rc = ara446.main(["--db", "/yok", "--model-dir", "/yok", "soru"])
    yak = capsys.readouterr()
    assert rc == 3, (rc, yak.err)
    assert yak.err.startswith("ölçülemedi:"), yak.err
    assert "ayrışmış" in yak.err, yak.err


# ---- C5c — sqlite URI kaçışsız yol enjeksiyonu ----

def _db_yaz_446(yol, satir_sayisi):
    db = sqlite3.connect(str(yol))
    db.execute("CREATE TABLE chunk(id INTEGER PRIMARY KEY, metin TEXT NOT NULL)")
    db.executemany("INSERT INTO chunk(id, metin) VALUES(?, ?)",
                   [(i + 1, f"m{i}") for i in range(satir_sayisi)])
    db.commit()
    db.close()
    return yol


def test_C5c_OZEL_karakterli_dizinde_terfi_calisir(terfi446, tmp_path, capsys):
    garip = tmp_path / "weird?dir#name"
    garip.mkdir()
    hedef, yeni = garip / "taban.sqlite", garip / "taban.sqlite.yeni"
    _db_yaz_446(hedef, 100)
    _db_yaz_446(yeni, 95)
    rc = terfi446.main(["--yeni", str(yeni), "--hedef", str(hedef)])
    capsys.readouterr()
    assert rc == 0
    db = sqlite3.connect(str(hedef))
    assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 95
    db.close()


def test_C5c_MUTASYON_eski_kacissiz_URI_ile_KIRILIR(tmp_path):
    """Pozitif kontrol: DÜZELTMEDEN ÖNCEKİ `"file:%s?mode=ro" % yol` deseni özel karakterli
    yolda GERÇEKTEN kırılıyor (ölçüldü: connect BAŞARILI ama sorgu `no such table: chunk` ile
    düşüyor — URI'nin `?`/`#`si tarafından bozulmuş oluyor)."""
    def eski_satir_say(yol):
        yol = pathlib.Path(yol)
        db = sqlite3.connect("file:%s?mode=ro" % yol, uri=True)
        try:
            return int(db.execute("SELECT count(*) FROM chunk").fetchone()[0])
        finally:
            db.close()

    garip = tmp_path / "weird?dir#name"
    garip.mkdir()
    hedef = garip / "taban.sqlite"
    _db_yaz_446(hedef, 100)
    with pytest.raises(sqlite3.OperationalError):
        eski_satir_say(hedef)


# ---- C5d / K8 — kesit tavanı: kırpma İŞARETİ tavanın İÇİNDE ----
#
# TUR 1 SAPMASININ GEREKÇESİ ÖLÇÜLMEDEN YAZILMIŞTI (bulgu K8, 2026-09-08): rapor "sonek v438'in
# `len(kesit) <= KESIT_TAVANI` değişmezini KIRAR" demişti; ÖLÇÜLDÜ ki değişmez `<=`dır, yani
# TAVANA SIĞAN bir işaret onu KIRMAZ. Kalan gerçek arıza duruyordu: `kesit()` 240 karakterde
# SESSİZCE kesiyor ve okuyucu (operatör ve `meridian/sohbet.py::_arac_hafiza_ara` üzerinden
# model) 241 karakterlik bir chunk ile 20.000 karakterlik bir chunk'ı AYIRT EDEMİYORDU — Yasa 4
# (sessiz yutma) + bedel yasası. HÜKÜM (Rol-1): işaret TAVANIN İÇİNDE uygulanır; BİRİM karakter
# (`kr`), çünkü `kesit` zaten tek satıra katlanmış metin döndürür ve "satır" kavramı orada YOK.
# `--json` ham metni KESMEDEN vermeye devam eder — bedel yalnız tablo görünümünde ödenir.
def test_C5d_kesit_TAVAN_DOLUNCA_tam_tavan_kadar(ara446):
    """"Tam kısılma": tavan dolduğunda çıktı TAM tavan kadardır (ne bir eksik, ne bir fazla) —
    işaret de o tavanın İÇİNDEDİR."""
    uzun = "x" * (ara446.KESIT_TAVANI + 50)
    sonuc = ara446.kesit(uzun)
    assert len(sonuc) == ara446.KESIT_TAVANI, (len(sonuc), ara446.KESIT_TAVANI)


def test_C5d_MUTASYON_kesme_kaldirilirsa_KIRMIZI(ara446, monkeypatch):
    monkeypatch.setattr(
        ara446, "kesit",
        lambda metin, tavan=ara446.KESIT_TAVANI: " ".join(str(metin).split()))
    uzun = "x" * (ara446.KESIT_TAVANI + 50)
    sonuc = ara446.kesit(uzun)
    assert len(sonuc) != ara446.KESIT_TAVANI, (
        "mutasyon (kesme kaldırılmış) YİNE tavana eşit uzunluk verdi — çivi kör")


def test_K8_KIRPMA_isareti_tavan_ICINDE_ve_SAYI_dogru(ara446):
    """Kırpma artık SESSİZ değil: kaç karakterin düştüğü işaretin İÇİNDE durur ve toplam uzunluk
    tavanı AŞMAZ (v438'in `<=` değişmezi korunur)."""
    uzun = "x" * (ara446.KESIT_TAVANI + 500)
    sonuc = ara446.kesit(uzun)
    assert len(sonuc) <= ara446.KESIT_TAVANI, len(sonuc)
    m = re.search(r"…\(\+(\d+) kr\)$", sonuc)
    assert m, repr(sonuc[-30:])
    dusen = int(m.group(1))
    govde = len(sonuc) - len(m.group(0))
    assert govde + dusen == len(uzun), (govde, dusen, len(uzun))


def test_K8_TAVANA_SIGAN_metne_isaret_KONMAZ(ara446):
    """Bedel: işaret yalnız GERÇEKTEN kırpılan metne konur — sığan her kesite sonek eklemek
    tabloyu gürültüyle doldururdu ve 'kırpıldı' sinyalini anlamsızlaştırırdı."""
    kisa = "alfa beta gama"
    assert ara446.kesit(kisa) == kisa
    tam = "y" * ara446.KESIT_TAVANI
    assert ara446.kesit(tam) == tam


def test_K8_MUTASYON_isaret_dusurulurse_KIRMIZI(ara446, monkeypatch):
    monkeypatch.setattr(
        ara446, "kesit",
        lambda metin, tavan=ara446.KESIT_TAVANI: " ".join(str(metin).split())[:tavan])
    sonuc = ara446.kesit("x" * (ara446.KESIT_TAVANI + 500))
    assert re.search(r"…\(\+(\d+) kr\)$", sonuc) is None, (
        "mutasyon (işaret düşürülmüş) YİNE işaret üretti — çivi kör")


def test_K8_JSON_kipi_HAM_metni_KESMEDEN_verir(ara446, monkeypatch, capsys):
    """Kırpma bedelinin ÖDENMEDİĞİ yüzey: `--json` makine yüzeyidir ve ham metni taşır."""
    uzun = "z" * (ara446.KESIT_TAVANI + 500)
    _patchle446(ara446, monkeypatch, [_sonuc446(1, "docs/A.md", "§1", uzun, 0.1)])
    rc = ara446.main(["--db", "/yok", "--model-dir", "/yok", "--json", "soru"])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)[0]["metin"] == uzun


# ================================================================================================
# C6 — `deploy/hindsight/hindsight-taban-tazele.{timer,service}` TARİHÇE ayrışması (ORTA)
# ================================================================================================

TIMER_YOL = REPO / "deploy" / "hindsight" / "hindsight-taban-tazele.timer"
SERVICE_YOL = REPO / "deploy" / "hindsight" / "hindsight-taban-tazele.service"
TARIHCE_BAS = "TARİHÇE (terk edildi, neden)"
TARIHCE_SON = "TARİHÇE SONU"


def _tarihce_araligi(metin: str):
    if TARIHCE_BAS not in metin:
        return None
    i = metin.index(TARIHCE_BAS)
    j = metin.index(TARIHCE_SON, i)
    return i, j + len(TARIHCE_SON)


# NOT (TUR 2): TUR 1'in `test_C6_0330_YALNIZ_tarihce_blogunda_gecer` çivisi KALDIRILDI ve yerini
# K7'nin `test_K7_0330_yalniz_TARIHCE_ve_ENVANTER_bloklarinda` + `test_K7_yorum_saatleri_
# OnCalendar_dan_TURER` ikilisi aldı. Gerekçe ölçüldü: eski çivi ÇIPLAK bir `03:30` dizesine
# bağlıydı — (a) yeni slotu `OnCalendar`a HİÇ bağlamıyordu (slot 09:40'a çekilse yeşil kalırdı),
# (b) ölçülmüş bir komşu saatini (hindsight-yedek'in günlük tetiği) çakışma envanterinden
# düşürtmüştü. Yeni ikili tek anlatıyı KORUR (03:30 yalnız TARİHÇE + FİLO ENVANTERİ) ve üstüne
# türetmeyi ekler. Kapsama: eski çivinin yakaladığı her şey yeni ikilinin de kırmızısıdır.


def test_C6_MUTASYON_tarihce_isareti_kaldirilirsa_KIRMIZI():
    """Pozitif kontrol: TARİHÇE işaretini metinden kaldırınca (ama 03:30 mevcut metinde
    dururken) yukarıdaki çivinin YAKALADIĞINI göster."""
    metin = TIMER_YOL.read_text(encoding="utf-8")
    assert "03:30" in metin, "fikstür varsayımı bozuk: timer dosyasında 03:30 hiç yok"
    sahte = metin.replace(TARIHCE_BAS, "BAŞLIK KALDIRILDI (mutasyon testi)")
    assert _tarihce_araligi(sahte) is None
    konumlar = [m.start() for m in re.finditer(r"03:30", sahte)]
    assert konumlar, "mutasyon fikstürü kendi içinde tutarsız: 03:30 hiç kalmamış"


def test_C6_v438_UC_DEGISMEZ_HALA_YESIL():
    """v438'in dokunulmaması istenen üç değişmezi burada da (bağımsız) ölçülür — C6 düzenlemesi
    bunları kırmamalı."""
    y_satirlari = [s.strip() for s in TIMER_YOL.read_text(encoding="utf-8").splitlines()
                  if s.strip().startswith("OnCalendar=")]
    assert len(y_satirlari) == 1
    m = re.match(r"OnCalendar=Sun \*-\*-\* (\d{2}):(\d{2}):00 UTC$", y_satirlari[0])
    assert m, y_satirlari[0]
    saat, dakika = int(m.group(1)), int(m.group(2))
    assert not (saat >= 22 or saat < 6), "sprint penceresi [22:00,06:00) içinde olamaz"
    assert (saat, dakika) != (3, 30), "hindsight-yedek.timer ile aynı dakika olamaz"
    assert 6 <= saat < 9, "sessiz bant 06:00–09:00"


# ==================================================================================================
# ==================================================================================================
# TUR 2 — C tesliminin bağımsız çekişmeli incelemesi (21 ayakta bulgu → 8 kök: K1..K8).
# Kaynak: inceleme_C.json + brief_C2_ops_tur2.md. Her kök ÖNCE kırmızı çiviyle açıldı.
# ==================================================================================================
# ==================================================================================================

# ==================================================================================================
# K1 — `ops/bar_sorgu.py::olcek_olculdu_mu` dikiş KAPISI süzülmüş kümede ölçüyordu (YÜKSEK)
# ==================================================================================================

def _barlar_baglantisi(hedef: pathlib.Path):
    """`barlar` görünümü kurulmuş bir DuckDB bağlantısı — `main()`i atlayıp alt komut
    fonksiyonlarını DOĞRUDAN ölçmek için (K6'nın kapı-bağımsız ölçümü bunu ister)."""
    con = bar_sorgu.olay_sorgu.baglanti_kur()
    con.execute("CREATE OR REPLACE TEMP VIEW barlar AS "
                + bar_sorgu.gorunum_sql(bar_sorgu.parquet_dosyalari(hedef)))
    return con


def test_K1_KAPI_TUM_arsivde_olcer_ay_suzgeci_kapiyi_KAPATMAZ(tmp_path, sandbox_state, capsys):
    """Bulgu (YÜKSEK): C1 `sorgu_dikis`in penceresini tüm seriye taşıdı ama `main`'in dikis
    dalındaki ÖN KAPI (`olcek_olculdu_mu`) hâlâ SÜZÜLMÜŞ kümede sayıyordu — C1'in kapattığı sınıf
    kapıdan geri giriyordu.

    Senaryo (kısmi geri-dolum): `ayarlama_olcegi` Ocak boyunca DOLU (1.0), Şubat'tan itibaren
    hiç yazılmamış (NULL). `--ay <Şubat>` ile sorulunca kapı Şubat'ta 0 DOLU satır sayıp
    'bu arşivde cevaplanamaz' derdi; oysa Şubat'ın ilk seansı GERÇEK bir dikiştir
    (onceki_olcek=1.0 → olcek=NULL)."""
    hedef = tmp_path / "barlar"
    ocak, subat = _seanslar(OCAK, 3), _seanslar(SUBAT, 3)
    _dikis_parquet_yaz(hedef, "TEST", ocak + subat, [1.0, 1.0, 1.0, None, None, None])

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    assert "ÖLÇÜLEMEDİ" not in yakala.err, (
        "kapı SÜZÜLMÜŞ kümede ölçtü: cevap düzeltilmiş sorguda dururken 'cevaplanamaz' denildi")
    satirlar = [json.loads(s) for s in yakala.out.strip().splitlines()] if yakala.out.strip() \
        else []
    assert len(satirlar) == 1, (satirlar, yakala.err)
    assert satirlar[0]["tarih"] == subat[0]
    assert satirlar[0]["onceki_olcek"] == 1.0 and satirlar[0]["olcek"] is None


def test_K1_BEYAN_yalniz_arsivin_TAMAMI_bosken_basilir(tmp_path, sandbox_state, capsys):
    """Beyanın kapsamı DARALDI ama KAYBOLMADI: arşivin TAMAMINDA hiç dolu ölçek yoksa
    'ÖLÇÜLEMEDİ' hâlâ basılır ve 0 satır döner (sessiz boş sonuç 'dikiş yok' yalanıdır)."""
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 3) + _seanslar(SUBAT, 3)
    _dikis_parquet_yaz(hedef, "TEST", gunler, [None] * 6)

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    assert "ÖLÇÜLEMEDİ" in yakala.err, yakala.err
    assert yakala.out.strip() == "", yakala.out


def _kapi_suzgecli(con):
    """MUTASYON: kapının ESKİ (süzülmüş kümede sayan) gövdesi. Yeni imza süzgeç ALMADIĞI için
    süzgeç bu senaryonun argv'sinden (`--ay 2024-02`) elle sabitlenmiştir — mutasyonun taklit
    ettiği şey KAPININ FİLTRELİ OLMASIdır, argümanın nereden geldiği değil."""
    nerede, parametreler = bar_sorgu._suzgec(None, SUBAT)
    ek = " AND ayarlama_olcegi IS NOT NULL" if nerede else " WHERE ayarlama_olcegi IS NOT NULL"
    return int(con.execute(f"SELECT count(*) FROM barlar{nerede}{ek}",
                           parametreler).fetchone()[0])


def test_K1_MUTASYON_kapi_suzgecli_kalirsa_OLCULEMEDI_der(tmp_path, sandbox_state, monkeypatch,
                                                          capsys):
    hedef = tmp_path / "barlar"
    ocak, subat = _seanslar(OCAK, 3), _seanslar(SUBAT, 3)
    _dikis_parquet_yaz(hedef, "TEST", ocak + subat, [1.0, 1.0, 1.0, None, None, None])

    monkeypatch.setattr(bar_sorgu, "olcek_olculdu_mu", _kapi_suzgecli)
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "dikis", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0
    assert "ÖLÇÜLEMEDİ" in yakala.err, (
        "mutasyon (kapı süzgeçli) YİNE de dikişi buldu — çivi kör")
    assert yakala.out.strip() == ""


# ==================================================================================================
# K6 — `sorgu_dikis` süzgeç gramerini `_suzgec`ten KOPYALAMIŞTI (tek-kaynak yasası)
# ==================================================================================================

def test_K6_suzgec_metni_kosul_listesinden_TURER():
    """`_suzgec` artık `_suzgec_kosullari`nın SARMALAYICISIDIR: metin biçimi koşul listesinden
    türer, ikinci bir gramer yoktur."""
    for sembol, ay in ((None, None), ("aapl", None), (None, SUBAT), ("brk.b", SUBAT)):
        kosullar, param = bar_sorgu._suzgec_kosullari(sembol, ay)
        metin, metin_param = bar_sorgu._suzgec(sembol, ay)
        beklenen = (" WHERE " + " AND ".join(kosullar)) if kosullar else ""
        assert metin == beklenen, (sembol, ay, metin, kosullar)
        assert param == metin_param, (sembol, ay, param, metin_param)


def test_K6_dikis_dis_WHERE_i_ORTAK_gramerden_kurar(tmp_path, sandbox_state, monkeypatch):
    """AYRIŞMA ÇİVİSİ: `_suzgec_kosullari`ya üçüncü bir kural eklenirse `dikis` de ONU uygular.
    (Kapıyı atlamak için `sorgu_dikis` DOĞRUDAN çağrılır — `main` üzerinden gitseydi mutasyon
    K1 kapısını da kapatır ve çivi yanlış sebeple yeşil olurdu.)"""
    hedef = tmp_path / "barlar"
    gunler = _seanslar(OCAK, 4)
    _dikis_parquet_yaz(hedef, "TEST", gunler, [1.0, 1.0, 0.5, 0.5])

    con = _barlar_baglantisi(hedef)
    try:
        assert len(bar_sorgu.sorgu_dikis(con, None, None, 10)) == 1, "fikstür: dikiş olmalı"
        monkeypatch.setattr(bar_sorgu, "_suzgec_kosullari", lambda sembol, ay: (["1 = 0"], []))
        assert bar_sorgu.sorgu_dikis(con, None, None, 10) == [], (
            "`dikis` ortak süzgeç gramerini KULLANMIYOR — kendi kopyasını taşıyor (tek-kaynak "
            "yasası: `_suzgec`e eklenen üçüncü bir süzgeç `dikis`te SESSİZCE uygulanmazdı)")
    finally:
        con.close()


# ==================================================================================================
# K5 — `ops/bar_arsivle.py`: hash alan-ayrımı · sürüm/göç beyanı · okuyucusuz alan · tek kaynak
# ==================================================================================================

def _cerceve_446(gunler: list[str], **sutunlar) -> pd.DataFrame:
    return pd.DataFrame({"date": pd.to_datetime(gunler), **sutunlar})


def test_K5a_hash_SUTUN_ADINI_akisa_katar(sandbox_state):
    """Bulgu (ORTA): `kaynak_icerik_hash` yalnız DEĞERLERİ hash'liyordu. Üst akış CSV yazıcısı
    `volume`u `hacim`e yeniden adlandırsa (DEĞERLER AYNI) hash DEĞİŞMEZ → idempotency kapısı
    'atlandı' der, ama `main()` koşulsuz `eksik_sutunlar[sembol]`ı günceller: manifest
    'volume eksik' derken parquet gerçek volume taşır. Okuyucusu VAR
    (`ops/bar_sorgu.py::_olculemedi_beyani` bu alanı okur)."""
    gunler = _seanslar(OCAK, 3)
    d1 = _cerceve_446(gunler, volume=[10, 20, 30])
    d2 = d1.rename(columns={"volume": "hacim"})
    assert bar_arsivle.kaynak_icerik_hash(d1) != bar_arsivle.kaynak_icerik_hash(d2), (
        "yalnız sütun ADI değişen iki dilim AYNI hash'i verdi — ad akışa girmiyor")


def test_K5a_MUTASYON_ad_akistan_cikarilirsa_hash_AYNI(sandbox_state, monkeypatch):
    """Pozitif kontrol: adı akıştan çıkaran (eski) gövde ile aynı iki dilim AYNI hash'i verir —
    yani yukarıdaki çivi gerçekten AD dalını ısırıyor."""
    import hashlib as _h

    def _adsiz_hash(dilim):
        sirali = dilim.sort_values("date").reset_index(drop=True)
        h = _h.sha256()
        for kolon in sirali.columns:
            h.update(pd.util.hash_pandas_object(sirali[kolon], index=False).values.tobytes())
        return h.hexdigest()

    gunler = _seanslar(OCAK, 3)
    d1 = _cerceve_446(gunler, volume=[10, 20, 30])
    d2 = d1.rename(columns={"volume": "hacim"})
    assert _adsiz_hash(d1) == _adsiz_hash(d2), (
        "mutasyon (ad akıştan çıkarılmış) hash'i YİNE ayırdı — çivi kör")


def _csv_yaz_adli_446(dizin: pathlib.Path, ad: str, gunler: list[str], hacim_adi: str) -> None:
    """CSV'yi `volume` sütunu VERİLEN ADLA yazar (üst akış yeniden adlandırmasının taklidi)."""
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = [f"date,open,high,low,close,{hacim_adi}"]
    for i, g in enumerate(gunler):
        c = 100.0 + i
        satirlar.append(f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000000 + i}")
    (dizin / ad).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def test_K5a_YENIDEN_ADLANDIRMA_manifest_parquet_AYRISMASINI_durdurur(sandbox_state, tmp_path,
                                                                      capsys):
    """Uçtan uca (bulgunun ÖLÇÜLMÜŞ senaryosu): iki satırlık bir sembol önce `volume` ile
    arşivlenir, sonra CSV'de sütun `hacim`e döner (DEĞERLER AYNI). İkinci koşum 'atlandı'
    DEMEMELİ — yoksa parquet gerçek volume taşırken manifest onu 'eksik' beyan eder.

    İki satır BİLEREK: `sanitize_bars`ın `_unadjusted_mask`i n>=3'te `df["volume"]`a ADIYLA
    dokunup rc 2 ile gürültülü düşer; sessiz ayrışma yolu n<3'te (ve `sanitize_bars`ın hiç
    dokunmadığı `kaynak`/`ayarlama_olcegi` sütunlarında) açıktır."""
    kaynak_dizin, hedef = tmp_path / "bars", tmp_path / "barlar"
    gunler = _seanslar(OCAK, 2)
    _csv_yaz_adli_446(kaynak_dizin, "aapl.csv", gunler, "volume")
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    _csv_yaz_adli_446(kaynak_dizin, "aapl.csv", gunler, "hacim")
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    assert "yazıldı" in yakala.out and "atlandı" not in yakala.out, (
        f"yeniden adlandırma SESSİZCE atlandı — manifest/parquet ayrıştı: {yakala.out}")

    m = json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))
    assert "volume" in m["eksik_sutunlar"]["AAPL"], m["eksik_sutunlar"]
    con = duckdb.connect()
    try:
        degerler = con.execute(
            f"SELECT volume FROM read_parquet('{hedef / 'AAPL.parquet'}')").fetchall()
    finally:
        con.close()
    assert all(d[0] is None for d in degerler), (
        f"manifest 'volume eksik' derken parquet GERÇEK değer taşıyor: {degerler}")


def test_K5b_ARAC_SURUMU_sema_gociyle_ARTTI():
    """`kaynak_hash` manifest ŞEMASINI değiştirdi; sürüm sabitinin yorumu bunun için var
    ('şema değişirse bu artar ve eski arşiv AYIRT EDİLEBİLİR'). Bir önceki bump (`bolum` alanı)
    aynı sınıftandı."""
    assert bar_arsivle.ARAC_SURUMU == "2026-09-08.1", bar_arsivle.ARAC_SURUMU


def test_K5b_ESKI_SOZLESME_kaydi_GEREKCESIYLE_yeniden_yazilir(sandbox_state, tmp_path, capsys):
    """Göç bedeli GÖRÜNÜR olmalı: A1'deki manifest (ölçüldü 2026-09-07, 260 sembol) `kaynak_hash`
    taşımıyor, yani dağıtımdan sonraki ilk `--uygula` arşivin TAMAMINI yeniden yazacak. Çıktı
    bunun NEDENİNİ söylemezse 260 satırlık 'yazıldı' listesi arıza gibi okunur."""
    kaynak_dizin, hedef = tmp_path / "bars", tmp_path / "barlar"
    gunler = _seanslar(OCAK, 4)
    _csv_yaz_446(kaynak_dizin, "aapl.csv", gunler)
    _csv_yaz_446(kaynak_dizin, "msft.csv", gunler, baslangic=200.0)
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    yol = hedef / bar_arsivle.MANIFEST_ADI
    m = json.loads(yol.read_text(encoding="utf-8"))
    for kayit in m["semboller"].values():          # ESKİ SÖZLEŞME taklidi: alanı SİL
        kayit.pop("kaynak_hash", None)
    yol.write_text(json.dumps(m), encoding="utf-8")

    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    assert "yazıldı" in yakala.out and "atlandı" not in yakala.out
    assert "eski sözleşme" in yakala.err, yakala.err
    assert "yeniden yazılıyor" in yakala.err, yakala.err
    assert "2 (sembol, parça)" in yakala.err, (
        f"göç satırı KAÇ kaydın etkilendiğini SAYIYLA söylemiyor: {yakala.err}")


def test_K5b_BASLIK_goc_bedelini_ve_pandas_bagimliligini_BEYAN_eder():
    """Bedel yasası: kazanç (revizyon yakalama) ölçüldü; bedel (tek seferlik tam yeniden yazım +
    hash'in pandas bayt biçimine bağlılığı) BAŞLIKTA yazılı olmalı."""
    doc = bar_arsivle.__doc__
    for parca in ("kaynak_hash", "tam yeniden yazım", "260 sembol", "hepsi-ya-hiç", "pandas"):
        assert parca in doc, parca


def test_K5c_manifest_kaydi_OKUYUCUSUZ_kapanis_toplami_TASIMAZ(sandbox_state, tmp_path, capsys):
    """Yasa 6 (okuyucusuz yazım yok): `atlanir_mi` artık `kaynak_hash` + `sha256` okuyor;
    `kapanis_toplami` manifestteki TEK okuyucusunu kaybetti. ÖLÇÜLDÜ (depo geneli grep,
    2026-09-08): alan yalnız `_olc` üretir ve `_dogrula` BELLEK İÇİNDE okur — manifestten okuyan
    hiçbir kod ya da çivi yok. Her koşum her sembol için okunmayan bir alan yazıyordu."""
    kaynak_dizin, hedef = tmp_path / "bars", tmp_path / "barlar"
    _csv_yaz_446(kaynak_dizin, "aapl.csv", _seanslar(OCAK, 4))
    assert bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"]) == 0
    capsys.readouterr()

    kayit = json.loads(
        (hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))["semboller"]["AAPL"]
    assert "kapanis_toplami" not in kayit, kayit
    # v442'nin alt-küme çivisi BOZULMADI (aynı değişmez burada da ölçülür):
    assert {"sha256", "satir", "ilk", "son"} <= set(kayit), kayit
    assert "kaynak_hash" in kayit and "bayt" in kayit, kayit


def test_K5c_BEDEL_kapanis_toplami_DOGRULAMADA_hala_olculur():
    """Bedel yasası: alanı manifestten DÜŞÜRMENİN kaybı ölçülür — yazım-anı doğrulaması
    (`_dogrula`) kapanış toplamını HÂLÂ kıyaslar; kaybolan yalnız DEFTERDEKİ kopyadır."""
    beklenen = {"satir": 3, "ilk": "2024-01-02", "son": "2024-01-04", "kapanis_toplami": 300.0}
    olculen = dict(beklenen, kapanis_toplami=301.0)
    assert bar_arsivle._dogrula(beklenen, olculen) is not None
    assert bar_arsivle._dogrula(beklenen, dict(beklenen)) is None


def test_K5d_manifest_EKSIK_ile_CAST_karari_AYNI_cerceveden_turer(sandbox_state, tmp_path,
                                                                  monkeypatch, capsys):
    """C2'nin tek-kaynak hedefi YARIM kalmıştı: `eksik` HAM (read_csv) çerçeveden, CAST kararı
    SANITIZE edilmiş çerçeveden ölçülüyordu. Bugün ayrışmıyorlar çünkü `sanitize_bars` sütun
    kümesini KORUYOR — ama bu YAZILI OLMAYAN, ÇİVİSİZ bir değişmezdi. Burada `sanitize_bars` bir
    sütun DÜŞÜRECEK şekilde sahtelenir: manifest beyanı ile parquet NULL'ları AYNI kümeden
    türemeli."""
    gercek = bar_arsivle.sanitize_bars

    def _volume_dusuren(ham, sembol):
        temiz, rapor = gercek(ham, sembol)
        return temiz.drop(columns=["volume"]), rapor

    monkeypatch.setattr(bar_arsivle, "sanitize_bars", _volume_dusuren)
    kaynak_dizin, hedef = tmp_path / "bars", tmp_path / "barlar"
    _csv_yaz_446(kaynak_dizin, "aapl.csv", _seanslar(OCAK, 4))
    rc = bar_arsivle.main(
        ["--kaynak-dizin", str(kaynak_dizin), "--hedef", str(hedef), "--uygula"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err

    m = json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))
    beyan = set(m["eksik_sutunlar"]["AAPL"])
    con = duckdb.connect()
    try:
        bos = {s for s in bar_arsivle.SUTUNLAR
               if con.execute(f"SELECT count({s}) FROM "
                              f"read_parquet('{hedef / 'AAPL.parquet'}')").fetchone()[0] == 0}
    finally:
        con.close()
    assert beyan == bos, (
        f"manifest beyanı {sorted(beyan)} ile parquet'teki NULL sütunlar {sorted(bos)} "
        "AYRIŞTI — iki karar hâlâ iki ayrı çerçeveden türüyor")
    assert "volume" in beyan, beyan


# ==================================================================================================
# K2 — `ops/jeton_css_uret.py::_sayfa_kipi` sayfa yazımı ATOMİK değildi (YÜKSEK)
# ==================================================================================================

def _bayat_sayfa_446(hedef: pathlib.Path, ad: str = "runbook.html") -> pathlib.Path:
    """Gerçek bir yüzeyin BAYAT kopyası (jeton bloğu tokens.json ile ayrışmış)."""
    p = hedef / ad
    p.write_text((WEB / ad).read_text(encoding="utf-8").replace(
        "--bg: #fafafa;", "--bg: #fafaf0;", 1), encoding="utf-8")
    return p


def test_K2_POZITIF_KONTROL_eski_desen_dosyayi_KESIK_birakir(tmp_path):
    """DÜZELTMENİN NEDENİ, ÖLÇÜLEREK: `pathlib.Path.write_text` dosyayı `open(mode='w')` ile
    YAZMADAN ÖNCE truncate eder; write() ortasında düşen gerçek bir G/Ç arızası (ENOSPC/EDQUOT/
    EFBIG) hedefi KESİK bırakır. Eski gövde tam olarak bu deseni kullanıyordu, yani
    "HATA …: yazılamadı" + "0/1 yazıldı" mesajı 'dosyaya dokunulmadı' DEĞİL, 'dosya bozuldu'
    anlamına gelebiliyordu."""
    p = tmp_path / "hedef.txt"
    p.write_text("A" * 600, encoding="utf-8")
    with pytest.raises(OSError):
        with open(p, "w", encoding="utf-8") as f:      # write_text'in TAM olarak yaptığı
            f.write("B" * 100)
            raise OSError(28, "No space left on device")
    assert p.stat().st_size < 600, "pozitif kontrol tutarsız: eski desen dosyayı KESMEDİ"


def test_K2_YAZIM_ATOMIK_replace_duserse_dosya_BAYTI_BAYTINA_ayni(tmp_path, monkeypatch, capsys):
    """Bulgu (YÜKSEK): sayfa yazımı atomik olmalı — geçici ad + `os.replace`
    (`ops/bar_arsivle.py::yaz_ve_dogrula` deseni). O zaman 'yazılamadı' GERÇEKTEN 'dosyaya
    dokunulmadı' demektir. Arıza `os.replace`te, yani içerik geçici dosyaya TAM yazıldıktan
    SONRA üretilir — eski gövdede bu an dosyanın zaten truncate edilmiş olduğu andı."""
    p = _bayat_sayfa_446(tmp_path)
    once = p.read_bytes()
    gercek_replace = os.replace

    def _patlat(src, dst, *a, **kw):
        if pathlib.Path(dst) == p:
            raise OSError(28, "No space left on device")
        return gercek_replace(src, dst, *a, **kw)

    monkeypatch.setattr(os, "replace", _patlat)
    rc = jcu.main([f"--sayfa={p}", "--uygula"])
    yakala = capsys.readouterr()
    assert rc == 1, (rc, yakala.out, yakala.err)
    assert "yazılamadı" in yakala.err, yakala.err
    assert "0/1 yazıldı" in yakala.err, yakala.err
    assert p.read_bytes() == once, (
        "hedef dosya DEĞİŞTİ — 'yazılamadı' derken sayfa kısmen/tamamen üzerine yazılmış")


def test_K2_ARIZADA_gecici_dosya_ARDINDA_KALMAZ(tmp_path, monkeypatch, capsys):
    """Bedel: atomik yazım bir geçici dosya üretir. Arızada o dosya SİLİNİR — yoksa araç her
    başarısız koşumda kaynak ağacına isimsiz artık bırakır ve `dagit.sh`in 'temiz ağaç' kapısı
    sessizce kirlenirdi."""
    p = _bayat_sayfa_446(tmp_path)
    gercek_replace = os.replace

    def _patlat(src, dst, *a, **kw):
        if pathlib.Path(dst) == p:
            raise OSError(28, "No space left on device")
        return gercek_replace(src, dst, *a, **kw)

    monkeypatch.setattr(os, "replace", _patlat)
    jcu.main([f"--sayfa={p}", "--uygula"])
    capsys.readouterr()
    kalanlar = [q.name for q in tmp_path.iterdir() if q.name != p.name]
    assert kalanlar == [], f"geçici artık kaldı: {kalanlar}"


def test_K2_BASLIK_sayfa_kipi_CIKIS_KODLARINI_beyan_eder():
    """Modül BAŞLIĞI `--uygula`nın rc 1 dönebildiğini SÖYLEMİYORDU (yalnız 'çıkış 1 = bayat').
    `ui/package.json` sarmalayıcısı ya da elle koşan operatör rc 1'i 'hiçbir şey yazılmadı' diye
    okur; oysa çok sayfalı koşumda a YAZILMIŞ, b yazılamamış olabilir."""
    doc = jcu.__doc__
    assert "--kontrol --uygula" in doc and "çıkış 2" in doc, doc
    assert "N/M yazıldı" in doc, doc
    assert "ATOMİK" in doc, doc            # casefold Türkçe İ'yi 'i̇'ye açar — literal ölçülür


# ==================================================================================================
# K3/K4 — "ops sözleşmesi KOMUT SATIRIdır": hafiza_ara / taban_terfi için GERÇEK SÜREÇ çivileri
# ==================================================================================================
# TUR 1'İN ÖLÇÜLMÜŞ BOŞLUĞU (bulgu, YÜKSEK): bu dosyadaki TEK subprocess koşucusu `_kos_jeton`du;
# C5a/C5b/C5c'nin hepsi `betikten_modul_yukle` + `main([...])` ile SÜREÇ İÇİNDE koşuyordu, yani
# shebang, argv ayrıştırma, `raise SystemExit(main())` ve `deploy/hindsight/hafiza_ara.sh`in
# belgelediği çıkış-kodu sözleşmesi hiçbir çivide ısırılmıyordu — üstelik dosya başlığı aksini
# İDDİA EDİYORDU (o iddia bu turda düzeltildi). 2026-08-30 vakasının tam sınıfı: 18 çivi yeşilken
# `--uygula` süreç düzeyinde sessizce yok sayılıyordu.
#
# `hafiza_ara.py` NEDEN SAHTE BİR KARDEŞLE KOŞUYOR (beyanlı sınır): gerçek `taban_hazirla` ONNX
# oturumu açar (`onnxruntime` + `tokenizers` + bge-m3 snapshot'ı) ve bu üçü YERELDE YOK — sorgu
# yoluna ulaşan HİÇBİR gerçek koşum yerelde mümkün değildir. Bu yüzden GERÇEK `hafiza_ara.py`
# BAYT BAYT kopyalanır ve YALNIZ kardeşi `kiyas_kos.py` sahte bir sözleşme kabuğuyla değiştirilir:
# betiğin kendi argv/çıkış-kodu/tablo-biçimi yolu GERÇEKTEN, ayrı bir süreçte koşar; sahte olan
# tek şey gömme arka ucudur. `taban_terfi.py`de böyle bir sınır YOK — o gerçek dosyayla koşar.
SAHTE_KIYAS = '''\
"""SAHTE `kiyas_kos.py` — v446 K3. YALNIZ `taban_hazirla`/`taban_sorgu` sözleşmesini taşır.
Senaryo `V446_SAHTE` ortam değişkeninin gösterdiği JSON dosyasından okunur."""
import json
import os
import pathlib


def _veri():
    return json.loads(pathlib.Path(os.environ["V446_SAHTE"]).read_text(encoding="utf-8"))


def taban_hazirla(db_yolu, model_dir, **kw):
    veri = _veri()
    if veri.get("hazirla_hatasi"):
        raise ValueError(veri["hazirla_hatasi"])
    return veri.get("kunye") or {}, ("DB", "GOMUCU"), lambda: None


def taban_sorgu(ortam, soru, k):
    return _veri().get("sonuclar", [])
'''


def _ara_kolu_kur(tmp_path: pathlib.Path, senaryo: dict) -> tuple[pathlib.Path, dict]:
    """(kopyalanmış hafiza_ara.py yolu, env). Gerçek betik BAYT BAYT kopyalanır."""
    dizin = tmp_path / "edg067"
    dizin.mkdir()
    (dizin / "hafiza_ara.py").write_bytes(ARA_YOL.read_bytes())
    (dizin / "kiyas_kos.py").write_text(SAHTE_KIYAS, encoding="utf-8")
    senaryo_yolu = tmp_path / "senaryo.json"
    senaryo_yolu.write_text(json.dumps(senaryo, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ, V446_SAHTE=str(senaryo_yolu))
    return dizin / "hafiza_ara.py", env


def _kos_ara446(betik: pathlib.Path, env: dict, tmp_path: pathlib.Path, *argv):
    return subprocess.run([sys.executable, str(betik), "--db", str(tmp_path / "taban.sqlite"),
                           "--model-dir", str(tmp_path), *argv],
                          capture_output=True, text=True, cwd=str(tmp_path), env=env)


def test_K3_C5a_GERCEK_SURECTE_bolumdeki_AYIRAC_sutunu_KAYDIRMAZ(tmp_path, ara446):
    """C5a operatörün koşacağı biçimde: başlığında ` · ` geçen bir kayıt TABLO kipinde sütun
    sayısını DEĞİŞTİRMEMELİ."""
    baslik = "### C.1 · Limit tavanını gerçekten BAĞLAYICI yap"
    betik, env = _ara_kolu_kur(tmp_path, {"sonuclar": [
        _sonuc446(1, "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md", baslik, "kesit metni", 0.1)]})
    r = _kos_ara446(betik, env, tmp_path, "soru")
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    satirlar = [s for s in r.stdout.splitlines() if not s.startswith("#")]
    assert satirlar, (r.stdout, r.stderr)
    alanlar = satirlar[0].split(ara446.AYIRAC, 4)
    assert len(alanlar) == 5, (alanlar, satirlar[0])
    assert alanlar[2] == "docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md", alanlar
    assert "BAĞLAYICI" in alanlar[3] and ara446.AYIRAC not in alanlar[3], alanlar[3]
    assert alanlar[4].strip() == "kesit metni", alanlar[4]


def test_K3_C5b_GERCEK_SURECTE_olculemedi_rc3(tmp_path):
    """C5b operatörün koşacağı biçimde: model/şema ayrışması → `ölçülemedi:` öneki + rc 3.
    Süreç ÇIKIŞ KODU ölçülür, fonksiyon dönüş değeri değil (`raise SystemExit(main())` yolu)."""
    betik, env = _ara_kolu_kur(
        tmp_path, {"hazirla_hatasi": "gömme boyutu 768, beklenen 1024 — model/şema ayrışmış"})
    r = _kos_ara446(betik, env, tmp_path, "soru")
    assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
    assert r.stderr.startswith("ölçülemedi:"), repr(r.stderr)
    assert "ayrışmış" in r.stderr, r.stderr
    assert r.stdout.strip() == "", r.stdout


def test_K3_C5b_GERCEK_SURECTE_kullanim_hatasi_HALA_rc2(tmp_path):
    """Ayrımın kendisi ölçülür: 2 (argparse) ile 3 (ölçülemedi) AYNI süreçte farklı kodlardır —
    K4'ün '3 kullan' hükmünün gerekçesi budur."""
    betik, env = _ara_kolu_kur(tmp_path, {"sonuclar": []})
    r = _kos_ara446(betik, env, tmp_path)          # `soru` YOK
    assert r.returncode == 2, (r.returncode, r.stderr)


def test_K3_C5c_GERCEK_SURECTE_ozel_karakterli_dizinde_terfi(tmp_path):
    """C5c operatörün koşacağı biçimde — burada SAHTELEME YOK: `taban_terfi.py` `meridian`ı da
    ONNX'i de ithal etmez (v438 AST çivisiyle ölçülü), gerçek dosya gerçek sqlite'larla koşar."""
    garip = tmp_path / "weird?dir#name"
    garip.mkdir()
    hedef, yeni = garip / "taban.sqlite", garip / "taban.sqlite.yeni"
    _db_yaz_446(hedef, 100)
    _db_yaz_446(yeni, 95)
    r = subprocess.run([sys.executable, str(TERFI_YOL), "--yeni", str(yeni),
                        "--hedef", str(hedef)],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    karar = json.loads(r.stdout.strip().splitlines()[-1])
    assert karar["karar"] == "TERFI" and karar["yeni_satir"] == 95, karar
    db = sqlite3.connect(str(hedef))
    try:
        assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 95
    finally:
        db.close()


def test_K3_C5c_GERCEK_SURECTE_esik_altinda_BIRAKILIR_rc1(tmp_path):
    """Kapının DİĞER yönü de operatör biçiminde: eşik altındaki bir indeks terfi ETMEZ ve hedefe
    DOKUNULMAZ (birimin `failed` olması `/api/infra`nın okuduğu sinyaldir)."""
    hedef, yeni = tmp_path / "taban.sqlite", tmp_path / "taban.sqlite.yeni"
    _db_yaz_446(hedef, 100)
    _db_yaz_446(yeni, 10)
    r = subprocess.run([sys.executable, str(TERFI_YOL), "--yeni", str(yeni),
                        "--hedef", str(hedef)],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    karar = json.loads(r.stdout.strip().splitlines()[-1])
    assert karar["karar"] == "BIRAKILDI", karar
    db = sqlite3.connect(str(hedef))
    try:
        assert db.execute("SELECT count(*) FROM chunk").fetchone()[0] == 100, "hedefe dokunuldu"
    finally:
        db.close()


SARMAL_YOL_446 = REPO / "deploy" / "hindsight" / "hafiza_ara.sh"


def test_K4_CIKIS_KODU_sozlesmesi_BETIKTE_ve_SARMALAYICIDA_ayni():
    """Tek-kaynak yasası: çıkış kodu sözleşmesinin İKİ kopyası var (betik başlığı + A1
    sarmalayıcısının `ÇIKIŞ KODU:` satırı). 3 eklenip biri güncellenmezse operatör sarmalayıcıya
    bakıp 3'ü tanımaz."""
    betik = ARA_YOL.read_text(encoding="utf-8")
    assert "3 — ÖLÇÜLEMEDİ" in betik, "betik başlığı 3'ü beyan etmiyor"
    sarmal = SARMAL_YOL_446.read_text(encoding="utf-8")
    cikis_satiri = [s for s in sarmal.splitlines() if "ÇIKIŞ KODU" in s]
    assert cikis_satiri, sarmal
    assert "3" in cikis_satiri[0] and "ölçülemedi" in cikis_satiri[0].casefold(), cikis_satiri


# ==================================================================================================
# K7 — C6 çivisi ÇIPLAK '03:30' dizesine bağlıydı; YENİ slot `OnCalendar`a bağlı DEĞİLDİ
# ==================================================================================================
# ÖLÇÜLDÜ (2026-09-08): `08:15` timer'da 5 yorum satırında + service BEDEL BEYANI'nda ELLE
# yazılıydı ve tek gerçek yönerge `OnCalendar=`di. Slot 09:40'a çekilse v446'nın C6 çivisi de
# v438'in üç değişmezi de YEŞİL kalırdı — kapatılan ayrışma sınıfı (yorum bir slot, direktif
# başka slot) aynen açıktı. Ayrıca "03:30 yalnız TARİHÇE'de" kuralı, ÖLÇÜLMÜŞ bir komşu saatini
# (hindsight-yedek.timer'ın günlük tetiği) çakışma envanterinden DÜŞÜRTMÜŞTÜ: kazanç (tek anlatı)
# ölçüldü, KAYIP ölçülmedi (bedel yasası). Çivi artık saati TÜRETİR, envanteri MUAF tutar.

ONCALENDAR_446 = re.compile(r"^OnCalendar=Sun \*-\*-\* (\d{2}):(\d{2}):00 UTC$")
SAAT_446 = re.compile(r"\d{2}:\d{2}")
ENVANTER_BAS = "FİLO ENVANTERİ BAŞI"
ENVANTER_SON = "FİLO ENVANTERİ SONU"

#: BAŞKA birimlerin ÖLÇÜLMÜŞ saatleri (birim dosyaları okundu 2026-09-07) + yapısal pencere
#: sınırları. Muaf blokların DIŞINDA geçmesine izin verilen TEK küme budur; hepsi bu birimin
#: slotu DEĞİL, komşularıdır. `03:30` BİLEREK YOK: o hem hindsight-yedek'in saati hem de BU
#: birimin TERK EDİLEN slotudur, yani serbest bırakılırsa terk edilmiş bir gerekçe metne geri
#: sızabilir — envanterde ve TARİHÇE'de, yalnız oralarda durur.
DIS_SAATLER = {"23:30",   # meridian-backup
               "04:00",   # meridian-aylik-bucket-kopya (ayın 3'ü)
               "22:00",   # @sef  (ve sprint penceresinin başı)
               "10:00",   # @bekci
               "16:00",   # @karne (Cumartesi)
               "07:30"}   # skill-gorus (kısa)
YAPISAL_SAATLER = {"22:00", "06:00", "09:00"}   # sprint penceresi [22:00,06:00) · sessiz bant


def _muaf_araliklar_446(metin: str) -> list[tuple[int, int]]:
    """Saat DENETİMİNDEN muaf bölgeler: TARİHÇE (terk edilen slotun anlatısı) ve FİLO ENVANTERİ
    (başka birimlerin ölçülmüş saatleri)."""
    araliklar = []
    for bas, son in ((TARIHCE_BAS, TARIHCE_SON), (ENVANTER_BAS, ENVANTER_SON)):
        i = metin.find(bas)
        if i < 0:
            continue
        j = metin.find(son, i)
        assert j >= 0, f"{bas} var, {son} yok — muaf bölge kapanmıyor"
        araliklar.append((i, j + len(son)))
    return araliklar


def _slot_ihlalleri_446(timer_metni: str, service_metni: str) -> list[tuple[str, str, str]]:
    """(dosya, bulunan saat, bağlam) ihlalleri. Slot `OnCalendar=` satırından TÜRETİLİR."""
    eslesmeler = [ONCALENDAR_446.match(s.strip()) for s in timer_metni.splitlines()]
    eslesmeler = [m for m in eslesmeler if m]
    assert len(eslesmeler) == 1, eslesmeler
    slot = f"{eslesmeler[0].group(1)}:{eslesmeler[0].group(2)}"
    izinli = {slot} | DIS_SAATLER | YAPISAL_SAATLER
    ihlaller = []
    for ad, metin in (("timer", timer_metni), ("service", service_metni)):
        muaf = _muaf_araliklar_446(metin)
        for g in SAAT_446.finditer(metin):
            if any(i <= g.start() < j for i, j in muaf):
                continue
            if g.group(0) not in izinli:
                satir = metin[:g.start()].count("\n") + 1
                ihlaller.append((ad, g.group(0), f"satır {satir}"))
    return ihlaller


def test_K7_yorum_saatleri_OnCalendar_dan_TURER():
    """HÜKÜM: TARİHÇE ve FİLO ENVANTERİ bloklarının DIŞINDA geçen her `HH:MM` ya `OnCalendar`dan
    türeyen slottur ya da ölçülmüş bir komşu/yapısal sınırdır. Yorum ile direktifin ayrışması
    artık ÇİVİLİDİR — literal bir sayıya değil, TÜRETMEYE bağlı."""
    ihlaller = _slot_ihlalleri_446(TIMER_YOL.read_text(encoding="utf-8"),
                                   SERVICE_YOL.read_text(encoding="utf-8"))
    assert not ihlaller, ihlaller


def test_K7_MUTASYON_OnCalendar_kayarsa_YORUMLAR_KIRMIZI():
    """Bulgunun senaryosu: slot sessiz bant içinde 09:40'a çekilir ve YALNIZ `OnCalendar=`
    güncellenir. Eski çivi (yalnız `03:30` regex'i) ve v438'in üç değişmezi bunu YAKALAMIYORDU."""
    timer = TIMER_YOL.read_text(encoding="utf-8").replace(
        "OnCalendar=Sun *-*-* 08:15:00 UTC", "OnCalendar=Sun *-*-* 09:40:00 UTC", 1)
    ihlaller = _slot_ihlalleri_446(timer, SERVICE_YOL.read_text(encoding="utf-8"))
    assert ihlaller, "mutasyon (OnCalendar kaydı, yorumlar kalmış) YAKALANMADI — çivi kör"
    assert {i[1] for i in ihlaller} == {"08:15"}, ihlaller
    assert {i[0] for i in ihlaller} == {"timer", "service"}, (
        "service'teki bağımsız kopya yakalanmadı", ihlaller)


def test_K7_0330_yalniz_TARIHCE_ve_ENVANTER_bloklarinda():
    """Tek anlatı KORUNUR: terk edilen slot bir GEREKÇE olarak yalnız TARİHÇE'de anlatılır; sayı
    olarak ayrıca yalnız FİLO ENVANTERİ'nde (komşu birimin ölçülmüş saati olarak) durur."""
    for yol in (TIMER_YOL, SERVICE_YOL):
        metin = yol.read_text(encoding="utf-8")
        muaf = _muaf_araliklar_446(metin)
        disi = [m.start() for m in re.finditer(r"03:30", metin)
                if not any(i <= m.start() < j for i, j in muaf)]
        assert not disi, (yol.name, "03:30 muaf blokların DIŞINDA", disi)


def test_K7_ENVANTER_cakismayi_KAYNAGA_baglar_ve_OncULSUZ_ifade_YOK():
    """Bedel yasası (bulgu, ORTA): `03:30` yasağı ölçülmüş bir sayıyı envanterden düşürmüş ve
    yerine öncülsüz bir 'HER GÜN aynı saat' ifadesi bırakmıştı — envanteri çakışma listesi diye
    okuyan bir sonraki Rol-1, hindsight-yedek'i 08:15 sanıp 03:30'a CPU işi koyabilirdi
    (2026-09-06 reflect kanaryası vakasının sınıfı). Sayı KAYNAĞIYLA geri geldi."""
    metin = TIMER_YOL.read_text(encoding="utf-8")
    envanter = metin[metin.index(ENVANTER_BAS):metin.index(ENVANTER_SON)]
    yedek_satiri = [s for s in envanter.splitlines() if "hindsight-yedek" in s]
    assert yedek_satiri, envanter
    assert any("03:30" in s for s in yedek_satiri), yedek_satiri
    assert "HER GÜN aynı saat" not in metin, (
        "öncülsüz 'HER GÜN aynı saat' ifadesi hâlâ duruyor (öncülü YOK: en yakın okuma bu "
        "birimin KENDİ saatidir ve bir sonraki cümle onu çürütür)")
    for kaynak in ("meridian-backup", "@sef", "@bekci", "@karne", "skill-gorus"):
        assert kaynak in envanter, kaynak


def test_K7_taban_terfi_SLOT_saatini_KOPYALAMAZ():
    """Terk edilen slotun ÜÇÜNCÜ kopyası `taban_terfi.py`nin `terfi_et` gerekçesindeydi
    ('gecenin 03:30'unda'). Slot saati o dosyada YAZILI OLMAMALI — kaynağı timer dosyasıdır."""
    metin = TERFI_YOL.read_text(encoding="utf-8")
    bulunan = SAAT_446.findall(metin)
    assert not bulunan, f"taban_terfi.py slot saati KOPYALIYOR: {bulunan}"
