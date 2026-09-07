"""v435 — `ops/bar_arsivle.py` çivileri: günlük bar CSV önbelleğinin ay/sembol bölümlü
tipli PARQUET arşivi (TSK-020 [UYGULA-3] Task 1, 2026-09-07).

NUMARA SEÇİMİ: `ls tests | grep -o 'v[0-9]*' | sort -V | tail -1` ile ölçüldü (2026-09-07) —
en büyük alınmış numara v434 idi; `ls tests | grep -E 'v43[0-9]'` v430-v434'ü döndürdü,
v435/v436 BOŞ. Çakışma yok.

NEDEN `main([...])` ÇAĞRILIYOR, `subprocess` DEĞİL — ÖLÇÜLMÜŞ GEREKÇE (v379'un devraldığı
"sözleşme komut satırıdır" disiplininden BİLİNÇLİ sapma): bu araç `sanitize_bars`ı ithal eder,
o da `meridian.obs`a ulaşır (hayalet-seans / karantina olayları). `subprocess` ile çağrılan bir
koşum `sandbox_state`in `config.STATE` yamasını GÖRMEZ (yama süreç-içidir) ve CANLI
`state/events.jsonl`e yazardı — CLAUDE.md §2'nin "pytest DIŞI koşum" kapısının tam olarak
kapattığı sınıf. Sözleşme yine de KOMUT SATIRIdır: her çivi gerçek `argv` listesi geçer,
hiçbir iç fonksiyon taklit edilmez (iki çivi hariç: yazıcıyı bozan mutasyon çivisi ve takvim
çivisi, ki ikisi de bunu AÇIKÇA yapar).

NEYİ ÇİVİLER (sınıf sınıf):
  1. VARSAYILAN KURU — `--uygula` verilmedikçe hedef dizine 1 BAYT yazılmaz (manifest dahil).
  2. ŞEMA DONUK VE TİPLİ — date DATE · o/h/l/c DOUBLE · volume BIGINT · kaynak VARCHAR ·
     ayarlama_olcegi DOUBLE. CSV'de olmayan sütun UYDURULMAZ: NULL + manifest beyanı.
  3. AY/SEMBOL BÖLÜMLEMESİ — `<hedef>/AAAA-AA/<sembol>.parquet`.
  4. DOĞRULAMA TAŞIYICIDIR — parquet geri okunur; satır sayısı / date min-max / kapanış
     toplamı sanitize sonrası CSV ile EŞİT değilse rc 5 ve dosya YERİNE KONMAZ.
  5. IDEMPOTENT — ikinci koşum "atlandı"; `--zorla` yeniden yazar.
  6. CSV SİLİNMEZ, DEĞİŞMEZ — canlı önbellek salt okunur (sha256 + mtime).
  7. SANITIZE BOĞAZI — arşive giren satır `sanitize_bars` çıktısıdır, ham CSV değil.
  8. MANİFEST ŞEMASI — üretim damgası (utc + araç + sürüm) + {sembol: {ay: {sha256, satir}}}
     + `eksik_sutunlar` beyanı.
  9. ÇIKIŞ KODLARI — 0 ok · 1 girdi yok · 2 kullanım hatası · 5 doğrulama farkı.

GERÇEK DEFTERE DOKUNULMAZ: her çivi `sandbox_state` altında koşar ve kendi sentetik CSV'sini
`tmp_path`e yazar; canlı `state/bars/` bu dosyada hiç açılmaz.
"""

from __future__ import annotations

import hashlib
import json

import duckdb
import pandas as pd
import pytest

from meridian.adapters import data as _data
from ops import bar_arsivle


# ---------------------------------------------------------------------------------------------
# Sentetik defter — tarihler GERÇEK XNYS seanslarından seçilir. Uydurma bir tarih kullanılsaydı
# `sanitize_bars`ın takvim kapısı satırları HAYALET sayıp düşürürdü (ya da kitlesel uyuşmazlık
# görüp seriyi hiç adjudike etmezdi) ve çivi ölçtüğünü sandığı şeyi ölçmezdi.
# ---------------------------------------------------------------------------------------------

def _seanslar(ay: str, adet: int) -> list[str]:
    """`ay` (AAAA-AA) içindeki İLK `adet` gerçek XNYS seansı. Kaynak `_sessions` — takvimin
    TEK kaynağı; testin kendi tatil listesi YOKTUR (kopya sessizce ayrışırdı)."""
    ses = sorted(g for g in _data._sessions() if g.startswith(ay))
    if len(ses) < adet:
        pytest.skip(f"takvim ölçülemedi ya da {ay} için {adet} seans yok (bulunan: {len(ses)})")
    return ses[:adet]


OCAK = "2024-01"
SUBAT = "2024-02"


def _csv_yaz(dizin, sembol_dosya: str, gunler: list[str], baslangic: float = 100.0) -> None:
    """`date,open,high,low,close,volume` — canlı önbelleğin ÖLÇÜLMÜŞ şeması (2026-09-07).
    Fiyatlar yumuşak: sıçrama yazılsaydı `sanitize_bars` satırı düzeltilmemiş sayıp
    KARANTİNAYA alırdı ve çivi sayıyı yanlış ölçerdi."""
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = ["date,open,high,low,close,volume"]
    for i, g in enumerate(gunler):
        c = baslangic + i
        satirlar.append(f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000000 + i}")
    (dizin / sembol_dosya).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


@pytest.fixture
def kaynak(tmp_path):
    """İki aylık tek sembol (AAPL) + tek aylık ikinci sembol (MSFT)."""
    d = tmp_path / "bars_kaynak"
    _csv_yaz(d, "aapl.csv", _seanslar(OCAK, 5) + _seanslar(SUBAT, 4))
    _csv_yaz(d, "msft.csv", _seanslar(OCAK, 3), baslangic=300.0)
    return d


@pytest.fixture
def hedef(tmp_path):
    return tmp_path / "barlar_hedef"


def _dosyalar(kok):
    return sorted(p.relative_to(kok).as_posix() for p in kok.rglob("*") if p.is_file())


def _oku(parquet):
    con = duckdb.connect()
    try:
        return con.execute(f"SELECT * FROM read_parquet('{parquet}')").fetchall()
    finally:
        con.close()


def _manifest(hedef):
    return json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# 1. VARSAYILAN KURU
# ---------------------------------------------------------------------------------------------

def test_KURU_kosum_HICBIR_BAYT_yazmaz(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef)])
    cikti = capsys.readouterr().out
    assert rc == 0, cikti
    assert not hedef.exists(), f"kuru koşum hedef dizini YARATTI: {_dosyalar(hedef)}"
    assert "yazılacak" in cikti
    assert "AAPL" in cikti and "MSFT" in cikti


def test_KURU_kosum_manifest_YAZMAZ(sandbox_state, kaynak, hedef):
    hedef.mkdir(parents=True)
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef)])
    assert _dosyalar(hedef) == [], "kuru koşum dosya bıraktı"


# ---------------------------------------------------------------------------------------------
# 2-3. ŞEMA + AY/SEMBOL BÖLÜMLEMESİ
# ---------------------------------------------------------------------------------------------

def test_UYGULA_ay_sembol_bolumlemesi_yazar(sandbox_state, kaynak, hedef):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    assert rc == 0
    assert _dosyalar(hedef) == [
        "2024-01/AAPL.parquet", "2024-01/MSFT.parquet", "2024-02/AAPL.parquet",
        bar_arsivle.MANIFEST_ADI,
    ]


def test_SEMA_donuk_ve_tipli(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    con = duckdb.connect()
    try:
        sema = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{hedef / OCAK / 'AAPL.parquet'}')").fetchall()
    finally:
        con.close()
    assert [(a, t) for a, t, *_ in sema] == [
        ("date", "DATE"), ("open", "DOUBLE"), ("high", "DOUBLE"), ("low", "DOUBLE"),
        ("close", "DOUBLE"), ("volume", "BIGINT"), ("kaynak", "VARCHAR"),
        ("ayarlama_olcegi", "DOUBLE"),
    ]
    assert [a for a, *_ in sema] == list(bar_arsivle.SUTUNLAR)


def test_CSVde_OLMAYAN_sutun_UYDURULMAZ_NULL_kalir(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    satirlar = _oku(hedef / OCAK / "AAPL.parquet")
    assert len(satirlar) == 5
    assert all(s[6] is None and s[7] is None for s in satirlar), satirlar


def test_EKSIK_SUTUN_beyani_manifestte(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    m = _manifest(hedef)
    assert m["eksik_sutunlar"]["AAPL"] == ["ayarlama_olcegi", "kaynak"]
    assert m["eksik_sutunlar"]["MSFT"] == ["ayarlama_olcegi", "kaynak"]


# ---------------------------------------------------------------------------------------------
# 4. DOĞRULAMA TAŞIYICIDIR (rc 5)
# ---------------------------------------------------------------------------------------------

def test_SATIR_FARKINDA_rc5_ve_dosya_YERINE_KONMAZ(sandbox_state, kaynak, hedef, monkeypatch,
                                                   capsys):
    """Yazıcı satır KAYBEDERSE doğrulama ısırır: rc 5, hedef dosya YOK, manifest YOK.

    Yazıcının bozulması AÇIKÇA taklit edilir — bu, doğrulama dalının TEK gerçek tetikleyicisidir
    (sağlıklı bir yazımda satır kaybı olmaz ve dal hiç koşmazdı; koşmayan bir kapı yok demektir)."""
    gercek = bar_arsivle._parquet_yaz

    def _eksik_yaz(con, df, hedef_dosya):
        return gercek(con, df.iloc[:-1], hedef_dosya)      # bir satır DÜŞÜR

    monkeypatch.setattr(bar_arsivle, "_parquet_yaz", _eksik_yaz)
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--sembol", "AAPL", "--ay", OCAK, "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 5, hata
    assert not (hedef / OCAK / "AAPL.parquet").exists()
    assert not (hedef / bar_arsivle.MANIFEST_ADI).exists()
    assert "satır" in hata and "AAPL" in hata
    assert not list(hedef.rglob("*.tmp")), "geçici dosya temizlenmedi"


def test_SATIR_SAYISI_kontrolu_TEK_BASINA_tasiyicidir(sandbox_state, kaynak, hedef, monkeypatch,
                                                      capsys):
    """Yalnızca SATIR SAYISININ değiştiği vaka: aynı ilk/son gün, aynı kapanış toplamı.

    NEDEN AYRI BİR ÇİVİ (mutasyon turu bulgusu, 2026-09-07): yukarıdaki çivi SON satırı düşürür
    ve o vakada `max(date)` de değişir — yani satır sayısı kontrolü kaldırılsa bile hüküm "son
    gün" kontrolünden gelirdi ve çivi YANLIŞ SEBEPLE yeşil/kırmızı olurdu. Burada yazıcı,
    ARŞİVDE ZATEN VAR OLAN bir günü `close=0` ile TEKRARLAR: ilk/son gün aynı kalır, kapanış
    toplamı DEĞİŞMEZ, yalnız satır sayısı artar. Bu vakayı YALNIZ satır sayımı yakalayabilir."""
    gercek = bar_arsivle._parquet_yaz

    def _tekrarli_yaz(con, df, hedef_dosya):
        ek = df.iloc[[0]].copy()
        ek.loc[:, "close"] = 0.0                          # toplamı DEĞİŞTİRMEZ
        return gercek(con, pd.concat([df, ek], ignore_index=True), hedef_dosya)

    monkeypatch.setattr(bar_arsivle, "_parquet_yaz", _tekrarli_yaz)
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--sembol", "AAPL", "--ay", OCAK, "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 5, hata
    assert "satır sayısı tutmadı" in hata, hata
    assert not (hedef / OCAK / "AAPL.parquet").exists()


# ---------------------------------------------------------------------------------------------
# 5. IDEMPOTENT + --zorla
# ---------------------------------------------------------------------------------------------

def test_IKINCI_kosum_atlandi(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    capsys.readouterr()
    once = {p: p.stat().st_mtime_ns for p in hedef.rglob("*.parquet")}
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert cikti.count("atlandı") == 3, cikti
    assert {p: p.stat().st_mtime_ns for p in hedef.rglob("*.parquet")} == once


def test_ZORLA_yeniden_yazar(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    capsys.readouterr()
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--uygula", "--zorla"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert cikti.count("yazıldı") == 3 and "atlandı" not in cikti, cikti


def test_KAYNAK_CSV_degisince_ATLANMAZ(sandbox_state, kaynak, hedef, capsys):
    """Manifest damgası yalnız dosyanın kendisini değil ÖLÇÜMÜ de taşır: CSV'ye satır eklenince
    ikinci koşum "atlandı" DEMEZ (yoksa arşiv sessizce bayatlardı)."""
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    capsys.readouterr()
    _csv_yaz(kaynak, "msft.csv", _seanslar(OCAK, 5), baslangic=300.0)
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--sembol", "MSFT", "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert "yazıldı" in cikti and "atlandı" not in cikti, cikti
    assert len(_oku(hedef / OCAK / "MSFT.parquet")) == 5


# ---------------------------------------------------------------------------------------------
# 6. CSV DOKUNULMAZLIĞI
# ---------------------------------------------------------------------------------------------

def test_CSV_dokunulmaz(sandbox_state, kaynak, hedef):
    once = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(kaynak.glob("*.csv"))}
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    sonra = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
             for p in sorted(kaynak.glob("*.csv"))}
    assert sonra == once


# ---------------------------------------------------------------------------------------------
# 7. SANITIZE BOĞAZI
# ---------------------------------------------------------------------------------------------

def test_ARSIVE_giren_satir_SANITIZE_ciktisidir(sandbox_state, tmp_path, hedef):
    """Yinelenmiş tarih + NaN fiyat satırı: ham CSV 7 satır, sanitize sonrası 5 — arşiv 5 yazar."""
    d = tmp_path / "kirli"
    d.mkdir()
    g = _seanslar(OCAK, 5)
    satirlar = ["date,open,high,low,close,volume"]
    for i, gun in enumerate(g):
        c = 100.0 + i
        satirlar.append(f"{gun},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000 + i}")
    satirlar.append(f"{g[2]},101.0,101.5,100.5,101.2,1002")            # yinelenmiş tarih
    satirlar.append(f"{g[4]},,,,,999")                                  # NaN fiyat
    (d / "aapl.csv").write_text("\n".join(satirlar) + "\n", encoding="utf-8")

    rc = bar_arsivle.main(["--kaynak-dizin", str(d), "--hedef", str(hedef), "--uygula"])
    assert rc == 0
    ham = pd.read_csv(d / "aapl.csv")
    assert len(ham) == 7
    assert len(_oku(hedef / OCAK / "AAPL.parquet")) == 5


# ---------------------------------------------------------------------------------------------
# 8. MANİFEST ŞEMASI
# ---------------------------------------------------------------------------------------------

def test_MANIFEST_semasi_ve_sha256_diskle_esit(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    m = _manifest(hedef)
    assert set(m) >= {"uretim", "eksik_sutunlar", "semboller"}
    assert m["uretim"]["arac"] == "ops/bar_arsivle.py"
    assert m["uretim"]["surum"] == bar_arsivle.ARAC_SURUMU
    assert m["uretim"]["utc"].endswith("+00:00") or "T" in m["uretim"]["utc"]
    kayit = m["semboller"]["AAPL"][OCAK]
    assert kayit["satir"] == 5
    disk = hashlib.sha256((hedef / OCAK / "AAPL.parquet").read_bytes()).hexdigest()
    assert kayit["sha256"] == disk


def test_MANIFEST_var_olan_sembolu_KORUR(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--sembol", "MSFT", "--uygula", "--zorla"])
    m = _manifest(hedef)
    assert set(m["semboller"]) == {"AAPL", "MSFT"}, "tek sembollü koşum manifesti EZDİ"


# ---------------------------------------------------------------------------------------------
# 9. ÇIKIŞ KODLARI + SÜZGEÇLER
# ---------------------------------------------------------------------------------------------

def test_GIRDI_YOK_rc1(sandbox_state, tmp_path, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(tmp_path / "yok"), "--hedef", str(hedef)])
    assert rc == 1
    assert "bulunamadı" in capsys.readouterr().err


def test_BOS_DIZIN_rc1(sandbox_state, tmp_path, hedef, capsys):
    bos = tmp_path / "bos"
    bos.mkdir()
    rc = bar_arsivle.main(["--kaynak-dizin", str(bos), "--hedef", str(hedef)])
    assert rc == 1
    assert "csv" in capsys.readouterr().err.lower()


def test_BOZUK_AY_bicimi_rc2(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--ay", "2024/1"])
    assert rc == 2
    assert "AAAA-AA" in capsys.readouterr().err


def test_BILINMEYEN_SEMBOL_rc1(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--sembol", "ZZZZ"])
    assert rc == 1
    assert "ZZZZ" in capsys.readouterr().err


def test_SEMBOL_ve_AY_suzgeci(sandbox_state, kaynak, hedef):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--sembol", "AAPL", "--ay", SUBAT, "--uygula"])
    assert rc == 0
    assert _dosyalar(hedef) == ["2024-02/AAPL.parquet", bar_arsivle.MANIFEST_ADI]


def test_JSON_kipi_satir_JSON_basar(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--json"])
    cikti = capsys.readouterr().out.strip().splitlines()
    assert rc == 0 and len(cikti) == 3
    kayitlar = [json.loads(s) for s in cikti]
    assert all(set(k) == set(bar_arsivle.BASLIKLAR) for k in kayitlar)
    assert all(k["bayt"] is None for k in kayitlar), "kuru koşumda bayt UYDURULMUŞ"


def test_VARSAYILAN_dizinler_configten_turer(sandbox_state, capsys):
    """`--kaynak-dizin`/`--hedef` verilmezse yollar `config.BARS`/`config.STATE`ten TÜRER
    (kopya sabit yazılsaydı sandbox yaması onları ıskalardı — ve canlıda iki kaynak ayrışırdı)."""
    _csv_yaz(sandbox_state / "bars", "aapl.csv", _seanslar(OCAK, 3))
    rc = bar_arsivle.main(["--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert (sandbox_state / "barlar" / OCAK / "AAPL.parquet").exists()
