"""test_edg100_bar_arsiv_kiyas_v506.py — EDG-2026-100 K1: bar arşivi (parquet) ↔ canlı
CSV(sanitize) okuma yolu EŞDEĞERLİK ölçüm aracının çivileri.

vNNN KİMLİK KAYDI: v506 seçildi çünkü ölçüm anında (2026-09-16) `tests/`+`ops/`+`meridian/`+
`research/` altında v506 HİÇ geçmiyordu — çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik
kuralı). En yakın komşu v505 (koherans kadansı) başka bir iş koluna aittir, dokunulmadı.

NE ÇİVİLER. Tek betik: `ops/bar_arsiv_kiyas.py`. Kart EDG-2026-100'ün K1 ayağının ARACIdır;
K2 (canlı gölge kıyası, `data.load_many` bayrağı) BU DİLİMDE YOKTUR ve bu dosyada da yoktur.

KIYASIN İKİ YAKASI, ÖLÇÜLDÜ (2026-09-16, duckdb 1.5.5 + pandas bu venv'de):
  * arşiv yakası — parquet, DuckDB ile okunur (pyarrow bu venv'de YOK, ölçüldü: `import pyarrow`
    ModuleNotFoundError); DATE sütunu pandas tarafında `datetime64[us]` olur;
  * canlı yaka — `pd.read_csv(..., parse_dates=["date"])` + `data.sanitize_bars`, yani
    `meridian/dataset.py`nin bugün kullandığı desenin ta kendisi; `date` orada da
    `datetime64[us]`tir. Yani EŞİT bir çift KURULABİLİRDİR ve (a) çivisi onu kurar.

SENTETİK TARİH UYDURULMAZ. `sanitize_bars` takvim kapısı seans OLMAYAN tarihin satırını DÜŞÜRÜR;
uydurma bir tarih kullanan çivi, aracın ölçtüğü satır farkını değil FİKSTÜRÜN kusurunu ölçerdi.
Bu yüzden üç tarih de gerçek XNYS seansıdır (2024-06-24/25/26, Pzt–Çrş).

AĞ YOK, CANLI DEFTER YOK. Her çivi `sandbox_state` üstünde koşar (fikstür `config.STATE`i tmp'ye
çevirir) ve araca verilen kaynak/arşiv/rapor dizinleri tmp'dedir: gerçek `state/` OKUNMAZ.
Komut satırı sözleşmesini sınayan TEK alt-süreç çivisi `MERIDIAN_ROOT`u tmp'ye çevirir — o
değişken `config.ROOT`u (dolayısıyla STATE/BARS'ı ve `obs`un yazdığı `events.jsonl`ı) taşır,
yani alt süreç de canlı deftere ulaşamaz.

MUTASYON KANITI bu dosyada KOŞMAZ; Rol-1'e teslim raporunda tablo hâlinde durur (CLAUDE.md §6).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from meridian import config
from ops import bar_arsivle
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
ARAC = REPO / "ops" / "bar_arsiv_kiyas.py"
KART_DOSYASI = (REPO / "research" / "cards"
                / "EDG-2026-100-bar-arsivi-canli-okuma-esdegerlik.yaml")

#: GERÇEK XNYS seansları (gerekçe modül başlığında).
SEANSLAR = ("2024-06-24", "2024-06-25", "2024-06-26")

#: Canlı CSV'nin BUGÜNKÜ sütunları — kaynak `ops/bar_arsivle.py` sabitidir, kopyalanmaz.
CSV_SUTUNLARI = tuple(bar_arsivle.CSV_SUTUNLARI)

#: EŞİT ÇİFTİN KURULMASI İÇİN GEREKEN TEK SAPMA, VE O SAPMA BİR BULGUDUR (ölçüldü 2026-09-16):
#: arşiv yazıcısı `volume`u BIGINT'e döker (kesir "bilgi değil biçim artığı" gerekçesiyle), canlı
#: CSV yakası ise `float64` taşır. Yani GERÇEK arşivde bu sütun HER parçada dtype farkı üretir.
#: Çiviler bunu iki ayrı yerde tutar: (a)–(e) eşit tabanı kurabilmek için burada DOUBLE'a çeker,
#: `test_K_*` ise arşivin GERÇEK şemasını yazıp aracın o farkı ÖTTÜĞÜNÜ ölçer. İkisini tek
#: fikstüre sıkıştırmak, ya pozitif kontrolü ya da bulguyu görünmez yapardı.
ESIT_TABAN_TIPLERI = {"volume": "DOUBLE"}


@pytest.fixture
def arac(sandbox_state):
    """Araç — KAYNAKTAN derlenmiş modül (ham `exec_module` yasağı v334). `sandbox_state`
    bağımlılığı kolaylık değil KAPIDIR: fikstür `config.STATE`i tmp'ye çevirir, yani bu
    dosyadaki hiçbir çivi canlı deftere bakamaz (CLAUDE.md §2)."""
    return betikten_modul_yukle(ARAC, "edg100_bar_arsiv_kiyas")


# ---------------------------------------------------------------------------
# fikstür kurucuları
# ---------------------------------------------------------------------------
def _cerceve(kapanislar=None) -> pd.DataFrame:
    """Üç seanslık sentetik bar çerçevesi. Fiyatlar `sanitize_bars`ın hiçbir onarımını
    tetiklemez (high = max(OHLC), low = min(OHLC), hareketler %35 altında) — onarım tetiklenseydi
    çivi aracın değil onarımın davranışını ölçerdi."""
    return pd.DataFrame({
        "date": pd.to_datetime(SEANSLAR),
        "open": [10.0, 11.0, 11.8],
        "high": [11.0, 11.5, 12.4],
        "low": [9.8, 10.8, 11.6],
        "close": list(kapanislar or [10.5, 11.25, 12.0]),
        "volume": [1000.0, 2000.0, 3000.0],
    })


def _csv_yaz(dizin: pathlib.Path, sembol: str, df: pd.DataFrame) -> pathlib.Path:
    dizin.mkdir(parents=True, exist_ok=True)
    yol = dizin / bar_arsivle.sembol_dosya_adi(sembol)
    df.to_csv(yol, index=False)
    return yol


def _parquet_yaz(yol: pathlib.Path, df: pd.DataFrame, tipler=None, sutunlar=None) -> None:
    """Parquet'i ARŞİV YAZICISININ mekanizmasıyla yazar (DuckDB `COPY`; pyarrow yok).
    `tipler`/`sutunlar` yalnız ÇİVİ için vardır: mutasyonu (dtype düşürme, sütun eksiltme)
    fikstür tarafında kurmak, üretim yazıcısını değiştirmekten güvenlidir."""
    tip = dict(bar_arsivle.SUTUN_TIPLERI)
    tip.update(ESIT_TABAN_TIPLERI)
    tip.update(tipler or {})
    sut = tuple(sutunlar if sutunlar is not None else df.columns)
    secim = ", ".join(f"CAST({s} AS {tip[s]}) AS {s}" if s in df.columns
                      else f"CAST(NULL AS {tip[s]}) AS {s}" for s in sut)
    yol.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.register("_k", df)
        con.execute(f"COPY (SELECT {secim} FROM _k ORDER BY date) TO '{yol}' "
                    "(FORMAT PARQUET)")
    finally:
        con.close()


def _manifest_yaz(arsiv: pathlib.Path, semboller, bolum=None, damga=None) -> pathlib.Path:
    """Arşiv manifesti — şekli `ops/bar_arsivle.py`nin yazdığının aynısı (yerleşim beyanı
    `bolum`, üretim damgası `uretim.utc`)."""
    bolum = bolum if bolum is not None else bar_arsivle.BOLUM_SEMBOL
    damga = damga or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "bolum": bolum,
        "eksik_sutunlar": {},
        "semboller": {s: {"satir": len(SEANSLAR)} for s in semboller},
        "uretim": {"utc": damga, "arac": bar_arsivle.ARAC_ADI,
                   "surum": bar_arsivle.ARAC_SURUMU, "sema": list(bar_arsivle.SUTUNLAR)},
    }
    arsiv.mkdir(parents=True, exist_ok=True)
    yol = arsiv / bar_arsivle.MANIFEST_ADI
    yol.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    return yol


def _sahne(tmp_path, *, parquet_kapanis=None, tipler=None, sutunlar=None, parquet_satir=None,
           manifest=True, bolum=None, damga=None):
    """(kaynak, arşiv, rapor) dizinleri + tek sembollük (AAPL) eşit çift; verilen mutasyon
    yalnız PARQUET yakasına uygulanır (canlı CSV yakası her sahnede aynıdır)."""
    kaynak, arsiv, rapor = tmp_path / "bars", tmp_path / "barlar", tmp_path / "olcum"
    csv_df = _cerceve()
    _csv_yaz(kaynak, "AAPL", csv_df)
    p_df = _cerceve(parquet_kapanis)
    if parquet_satir is not None:
        p_df = p_df.iloc[:parquet_satir]
    _parquet_yaz(arsiv / "AAPL.parquet", p_df, tipler=tipler,
                 sutunlar=sutunlar if sutunlar is not None else CSV_SUTUNLARI)
    if manifest:
        _manifest_yaz(arsiv, ["AAPL"], bolum=bolum, damga=damga)
    else:
        arsiv.mkdir(parents=True, exist_ok=True)
    return kaynak, arsiv, rapor


def _kos(arac, kaynak, arsiv, rapor, ek=()) -> int:
    return arac.main(["--kaynak-dizin", str(kaynak), "--arsiv-dizin", str(arsiv),
                      "--rapor-dizin", str(rapor), *ek])


def _sonuc(rapor: pathlib.Path) -> dict:
    ler = sorted(rapor.glob("sonuc_100_*.json"))
    assert len(ler) == 1, f"tek sonuç dosyası bekleniyordu, bulunan: {ler}"
    return json.loads(ler[0].read_text(encoding="utf-8"))


def _fark_satirlari(rapor: pathlib.Path) -> list[dict]:
    ler = sorted(rapor.glob("fark_*.jsonl"))
    assert len(ler) == 1, f"tek fark dosyası bekleniyordu, bulunan: {ler}"
    return [json.loads(s) for s in ler[0].read_text(encoding="utf-8").splitlines() if s.strip()]


# ---------------------------------------------------------------------------
# (a) EŞİT ÇİFT
# ---------------------------------------------------------------------------
def test_A_esit_cift_esit_1_farkli_0(arac, tmp_path):
    """Aynı çerçevenin iki yakası EŞİTTİR. Bu çivi aynı zamanda NEGATİF KONTROLDÜR: araç her
    şeye 'farklı' diyorsa (b)–(d)'nin kırmızıları bir şey KANITLAMAZ."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"] == {"esit": 1, "farkli": 0, "olculemeyen": 0}
    assert s["oran"]["esitlik_orani"] == 1.0
    assert _fark_satirlari(rapor) == []


# ---------------------------------------------------------------------------
# (b) YOL-TUTARLI POZİTİF KONTROL — TEK HÜCRE
# ---------------------------------------------------------------------------
def test_B_PK_parquette_TEK_hucre_degisince_deger_farki_oter(arac, tmp_path):
    """Kartın (1) numaralı pozitif kontrolü: parçanın parquet kopyasında TEK hücre değişir ve
    AYNI kıyas fonksiyonundan geçer — fark ÖTMELİDİR. Ötmezse ölçüm geçersizdir."""
    kaynak, arsiv, rapor = _sahne(tmp_path, parquet_kapanis=[10.5, 11.25, 12.000000000001])
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"]["esit"] == 0 and s["sayim"]["farkli"] == 1
    assert s["oran"]["esitlik_orani"] == 0.0
    deger = [f for f in _fark_satirlari(rapor) if f["tur"] == "deger"]
    assert len(deger) == 1, deger
    assert deger[0]["sembol"] == "AAPL" and deger[0]["sutun"] == "close"
    assert deger[0]["satir"] == 2


def test_B2_bit_esitlik_np_isclose_DEGILDIR(arac):
    """`np.isclose`ın EŞİT sayacağı bir fark (1 ULP) BURADA FARKTIR — kart 'float bit-eşit' der.
    Kıyas fonksiyonu SAF olduğu için doğrudan çağrılır (dosya G/Ç yok)."""
    a = pd.DataFrame({"close": [1.0]})
    b = pd.DataFrame({"close": [np.nextafter(1.0, 2.0)]})
    assert bool(np.isclose(a["close"].iat[0], b["close"].iat[0])) is True
    rapor = arac.kiyasla(a, b)
    assert rapor["esit"] is False
    assert [f["tur"] for f in rapor["farklar"]] == ["deger"]


# ---------------------------------------------------------------------------
# (c) DTYPE
# ---------------------------------------------------------------------------
def test_C_dtype_float32e_dusunce_dtype_farki(arac, tmp_path):
    """Kartın (2) numaralı kontrolü: dtype'ı düşürülmüş parquet FARKLIdır — değerler
    yuvarlanarak aynı görünse bile TİP bir farktır."""
    kaynak, arsiv, rapor = _sahne(tmp_path, tipler={"close": "FLOAT"})
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"]["farkli"] == 1
    turler = [f["tur"] for f in _fark_satirlari(rapor)]
    assert "dtype" in turler, turler
    dtip = [f for f in _fark_satirlari(rapor) if f["tur"] == "dtype"]
    assert dtip[0]["sutun"] == "close"
    assert dtip[0]["arsiv"] == "float32" and dtip[0]["csv"] == "float64"


# ---------------------------------------------------------------------------
# (d) SATIR SAYISI
# ---------------------------------------------------------------------------
def test_D_satir_eksikse_satir_sayisi_farki(arac, tmp_path):
    kaynak, arsiv, rapor = _sahne(tmp_path, parquet_satir=2)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"]["farkli"] == 1
    satir = [f for f in _fark_satirlari(rapor) if f["tur"] == "satir_sayisi"]
    assert len(satir) == 1 and satir[0]["arsiv"] == 2 and satir[0]["csv"] == 3


def test_D2_satir_sayisi_farkinda_deger_ekseni_OLCULMEDI_denir(arac):
    """Satır sayıları tutmuyorsa hücre HİZALAMASI yoktur; araç 'değer farkı yok' DEMEZ,
    'değer ekseni ölçülmedi' der (uydurma yasağı: ölçülemeyen ile 'fark yok' ayrı şeylerdir)."""
    a = pd.DataFrame({"close": [1.0, 2.0]})
    b = pd.DataFrame({"close": [1.0, 2.0, 3.0]})
    rapor = arac.kiyasla(a, b)
    assert rapor["esit"] is False
    assert rapor["deger_olculdu"] is False
    assert [f["tur"] for f in rapor["farklar"]] == ["satir_sayisi"]


# ---------------------------------------------------------------------------
# (e) NaN
# ---------------------------------------------------------------------------
def test_E_NaN_NaN_ESIT_NaN_0_FARKLI(arac):
    """Kart: 'NaN ↔ NaN EŞİT sayılır'. Sıfır ile 'bilmiyorum' aynı şey DEĞİLDİR."""
    nan_nan = arac.kiyasla(pd.DataFrame({"x": [float("nan")]}),
                           pd.DataFrame({"x": [float("nan")]}))
    assert nan_nan["esit"] is True, nan_nan["farklar"]

    nan_sifir = arac.kiyasla(pd.DataFrame({"x": [float("nan")]}),
                             pd.DataFrame({"x": [0.0]}))
    assert nan_sifir["esit"] is False
    assert [f["tur"] for f in nan_sifir["farklar"]] == ["deger"]


def test_E2_eksi_sifir_arti_sifirdan_BIT_olarak_farklidir(arac):
    """`-0.0 == 0.0` Python'da TRUE'dur; BİT eşitliği değildir. Kart bit-eşitlik der."""
    r = arac.kiyasla(pd.DataFrame({"x": [-0.0]}), pd.DataFrame({"x": [0.0]}))
    assert r["esit"] is False and [f["tur"] for f in r["farklar"]] == ["deger"]


# ---------------------------------------------------------------------------
# (f) MANİFEST YOK → ÖLÇÜM DURUR
# ---------------------------------------------------------------------------
def test_F_manifest_yoksa_cikis_2_ve_SONUC_DOSYASI_YAZILMAZ(arac, tmp_path):
    """Manifest ölçümün KAPSAM BEYANIdır. Yoksa 'kaç parça vardı' sorusu cevapsızdır ve
    dosyaları tarayıp kapsamı UYDURMAK yasaktır — ölçüm DURUR, artefakt YAZILMAZ."""
    kaynak, arsiv, rapor = _sahne(tmp_path, manifest=False)
    assert _kos(arac, kaynak, arsiv, rapor) == 2
    assert not rapor.exists() or list(rapor.iterdir()) == []


def test_F2_bolum_taninmiyorsa_cikis_2(arac, tmp_path):
    kaynak, arsiv, rapor = _sahne(tmp_path, bolum="ceyrek")
    assert _kos(arac, kaynak, arsiv, rapor) == 2
    assert not rapor.exists() or list(rapor.iterdir()) == []


def test_F3_bozuk_manifest_cikis_2(arac, tmp_path):
    kaynak, arsiv, rapor = _sahne(tmp_path)
    (arsiv / bar_arsivle.MANIFEST_ADI).write_text("{bozuk", encoding="utf-8")
    assert _kos(arac, kaynak, arsiv, rapor) == 2
    assert not rapor.exists() or list(rapor.iterdir()) == []


# ---------------------------------------------------------------------------
# (g) EŞİKLER KARTTAN
# ---------------------------------------------------------------------------
def test_G_esikler_KARTTAN_okunur_kod_sabiti_DEGIL(arac, tmp_path, monkeypatch):
    """Eşik kodda DONMUŞ olsaydı kart ile sessizce ayrışırdı (tek-kaynak yasası). Çivi kartın
    KOPYASINI değiştirir ve raporun eşik alanının DEĞİŞTİĞİNİ ölçer."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    canli = _sonuc(rapor)["esikler"]["esitlik_orani_alt"]
    assert canli["esik"] == 1.0

    sahte_dizin = tmp_path / "kartlar"
    sahte_dizin.mkdir()
    govde = yaml.safe_load(KART_DOSYASI.read_text(encoding="utf-8"))
    govde["esikler"]["esitlik_orani_alt"] = 0.42
    govde["esikler"]["olculemeyen_ust_oran"] = 0.5
    (sahte_dizin / KART_DOSYASI.name).write_text(yaml.safe_dump(govde, allow_unicode=True),
                                                 encoding="utf-8")
    monkeypatch.setattr(arac, "KART_DIZINI", sahte_dizin)

    rapor2 = tmp_path / "olcum2"
    assert _kos(arac, kaynak, arsiv, rapor2) == 0
    s2 = _sonuc(rapor2)["esikler"]
    assert s2["esitlik_orani_alt"]["esik"] == 0.42
    assert s2["olculemeyen_ust_oran"]["esik"] == 0.5


def test_G2_kart_okunamazsa_olcum_DURUR(arac, tmp_path, monkeypatch):
    """Eşiksiz bir ölçüm hüküm taşıyamaz; kart yoksa araç sayı basmak yerine DURUR."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    bos = tmp_path / "kartsiz"
    bos.mkdir()
    monkeypatch.setattr(arac, "KART_DIZINI", bos)
    assert _kos(arac, kaynak, arsiv, rapor) == 2
    assert not rapor.exists() or list(rapor.iterdir()) == []


def test_G3_K2_esikleri_OLCULMEDI_diye_ADIYLA_raporlanir(arac, tmp_path):
    """Kartın gölge-kıyası eşikleri (K2) bu koşumun kapsamı DIŞINDADIR. 'Kapsamda yok' ile
    'geçti' aynı piksele düşmemeli: adıyla, nedeniyle raporlanır."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    k2 = _sonuc(rapor)["k2_olculmedi"]
    assert set(k2) == {"golge_kiyas_seans", "golge_fark_ust"}
    assert all(v.get("neden") for v in k2.values())


# ---------------------------------------------------------------------------
# (h) OBS / STATE YAZIMI YOK
# ---------------------------------------------------------------------------
def test_H1_kaynak_taramasi_obs_ithali_YOK(arac):
    """KAYNAK TARAMASI: araç gözlem defterine ulaşan bir ithal TAŞIMAZ. `sanitize_bars`
    üzerinden `meridian.adapters.data`ya ulaşılır — o modül `obs`u yalnız TEMBEL ithal eder ve
    aracın kendi metninde `obs` adı geçmez."""
    metin = ARAC.read_text(encoding="utf-8")
    kod = [s for s in metin.splitlines()
           if s.strip().startswith(("import ", "from ")) and "obs" in s]
    assert kod == [], kod
    assert "meridian.obs" not in metin
    assert "obs.log(" not in metin and "obs.warn(" not in metin and "obs.alarm(" not in metin


def test_H2_kosum_state_dizinine_TEK_BAYT_yazmaz(arac, tmp_path):
    """SANDBOX'TA DOSYA SAYIMI: koşumdan sonra `config.STATE` altında yeni dosya YOK ve rapor
    YALNIZ `--rapor-dizin`e düşmüştür."""
    once = sorted(p.relative_to(config.STATE) for p in config.STATE.rglob("*"))
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    sonra = sorted(p.relative_to(config.STATE) for p in config.STATE.rglob("*"))
    assert sonra == once, [p for p in sonra if p not in once]
    assert not (config.STATE / "events.jsonl").exists()
    assert sorted(p.name for p in rapor.iterdir()) == sorted(
        [_sonuc(rapor)["fark_dosyasi"]] + [p.name for p in rapor.glob("sonuc_100_*.json")])


def test_H3_kuru_kosum_HICBIR_dosya_yazmaz(arac, tmp_path):
    """`--kuru`: ölçer, BASAR, yazmaz. Kazanılan ile kaybedilen ayrı ayrı görünür kalsın diye
    çıkış kodu yine 0'dır (ölçüm koştu) ama rapor dizini DOĞMAZ."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor, ek=["--kuru"]) == 0
    assert not rapor.exists()


# ---------------------------------------------------------------------------
# KAPSAM / ÖLÇÜLEMEYEN
# ---------------------------------------------------------------------------
def test_I_CSV_yoksa_parca_OLCULEMEYEN_sayilir_farkli_DEGIL(arac, tmp_path):
    """CSV yakası yoksa parça hakkında hüküm YOKTUR: 'farklı' demek uydurma olurdu."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    (kaynak / bar_arsivle.sembol_dosya_adi("AAPL")).unlink()
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"] == {"esit": 0, "farkli": 0, "olculemeyen": 1}
    assert s["oran"]["esitlik_orani"] is None
    assert s["oran"]["olculemeyen_oran"] == 1.0
    assert s["esikler"]["esitlik_orani_alt"]["gecti"] is None


def test_I2_parquet_yoksa_parca_OLCULEMEYEN_sayilir(arac, tmp_path):
    kaynak, arsiv, rapor = _sahne(tmp_path)
    (arsiv / "AAPL.parquet").unlink()
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"]["olculemeyen"] == 1
    assert s["olculemeyen_nedenleri"]


def test_I3_sembol_suzgeci_kapsami_daraltir(arac, tmp_path):
    kaynak, arsiv, rapor = _sahne(tmp_path)
    _csv_yaz(kaynak, "MSFT", _cerceve())
    _parquet_yaz(arsiv / "MSFT.parquet", _cerceve(), sutunlar=CSV_SUTUNLARI)
    _manifest_yaz(arsiv, ["AAPL", "MSFT"])
    assert _kos(arac, kaynak, arsiv, rapor, ek=["--sembol", "MSFT"]) == 0
    s = _sonuc(rapor)
    assert s["kapsam"]["parca"] == 1 and s["kapsam"]["sembol_suzgeci"] == ["MSFT"]


def test_I4_manifest_bayatsa_tazelik_esigi_DUSER_ama_olcum_kosar(arac, tmp_path):
    """Bayat manifest ölçümü DURDURMAZ (sayı yine üretilir) ama tazelik eşiği DÜŞER — hükmü
    Rol-1 verir, araç yalnız sayıyı basar."""
    eski = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat(timespec="seconds")
    kaynak, arsiv, rapor = _sahne(tmp_path, damga=eski)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    tazelik = _sonuc(rapor)["esikler"]["manifest_tazelik_gun_ust"]
    assert tazelik["gecti"] is False and tazelik["deger"] > 8


def test_I5_HUKUM_basilmaz(arac, tmp_path):
    """Hüküm Rol-1'indir: sonuç dosyası 'GEÇTİ/KALDI' TAŞIMAZ, yalnız sayıları ve eşik
    karşılaştırmalarını taşır."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["hukum"] == arac.HUKUM_YOK
    assert "ROL-1" in s["hukum"].upper()


# ---------------------------------------------------------------------------
# ARŞİVİN GERÇEK ŞEMASI — ölçülmüş yapısal asimetri
# ---------------------------------------------------------------------------
def test_K_gercek_arsiv_semasi_SUTUN_ve_DTYPE_ekseninde_oter(arac, tmp_path):
    """ÖLÇÜLMÜŞ ASİMETRİ (2026-09-16, `ops/bar_arsivle.py` şema sabitleri): arşiv şeması canlı
    CSV'nin ÜST KÜMESİDİR — `kaynak` ve `ayarlama_olcegi` arşivde NULL sütun olarak vardır,
    CSV'de hiç yoktur; `volume` arşivde BIGINT, CSV'de float64'tür.

    Çivi bunu bir 'kusur' olarak değil, ARACIN GÖRDÜĞÜ olarak sabitler: gerçek arşive karşı
    koşulduğunda K1 her parçada sütun + dtype farkı basacaktır ve hükmü (fark kaynağı tasarımda
    kapatılacak mı, yoksa kıyas şema normalizasyonuyla mı sorulacak) Rol-1 verir. Araç sessizce
    normalize etseydi, ölçülmesi istenen fark ölçümün kendisi tarafından silinirdi."""
    kaynak, arsiv, rapor = _sahne(tmp_path, tipler={"volume": "BIGINT"},
                                  sutunlar=bar_arsivle.SUTUNLAR)
    assert _kos(arac, kaynak, arsiv, rapor) == 0
    s = _sonuc(rapor)
    assert s["sayim"] == {"esit": 0, "farkli": 1, "olculemeyen": 0}
    assert s["tur_sayilari"]["sutun"] == 1 and s["tur_sayilari"]["dtype"] == 1
    farklar = _fark_satirlari(rapor)
    sutun = [f for f in farklar if f["tur"] == "sutun"][0]
    assert sutun["yalniz_arsiv"] == ["kaynak", "ayarlama_olcegi"]
    assert sutun["yalniz_csv"] == []
    dtip = [f for f in farklar if f["tur"] == "dtype"]
    assert [f["sutun"] for f in dtip] == ["volume"]
    # ORTAK sütunların DEĞERLERİ tutuyor: fark YALNIZ şema eksenindedir ve bu ayrım raporda durur.
    assert s["deger_hucre_farki"] == 0


# ---------------------------------------------------------------------------
# KOMUT SATIRI SÖZLEŞMESİ — operatörün koşacağı BİÇİMDE (CLAUDE.md §6)
# ---------------------------------------------------------------------------
def test_J_komut_satiri_sozlesmesi_alt_surecte(arac, tmp_path):
    """`ops/` sözleşmesi KOMUT SATIRIdır, `main()` değil (vaka 2026-08-30: 18 çivi yeşilken
    `--uygula` sessizce yok sayılıyordu). `MERIDIAN_ROOT` tmp'ye çevrilir — alt sürecin
    `config.ROOT`u (dolayısıyla STATE ve `obs`un yazdığı defter) canlıya ULAŞAMAZ."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path / "sahte_kok"),
                 PYTHONPATH=str(REPO))
    p = subprocess.run([sys.executable, str(ARAC),
                        "--kaynak-dizin", str(kaynak), "--arsiv-dizin", str(arsiv),
                        "--rapor-dizin", str(rapor)],
                       capture_output=True, text=True, env=ortam, cwd=str(REPO), timeout=300)
    assert p.returncode == 0, p.stderr
    s = _sonuc(rapor)
    assert s["sayim"] == {"esit": 1, "farkli": 0, "olculemeyen": 0}
    assert not (tmp_path / "sahte_kok" / "state" / "events.jsonl").exists()


def test_J2_cakisan_kip_bayragi_cikis_2(arac, tmp_path):
    """`--kuru` ve `--rapor` birlikte verilemez: çelişen kip bayrağı SESSİZCE bir tarafa
    düşmez (dagit kapısıyla aynı disiplin)."""
    kaynak, arsiv, rapor = _sahne(tmp_path)
    assert _kos(arac, kaynak, arsiv, rapor, ek=["--kuru", "--rapor"]) == 2
