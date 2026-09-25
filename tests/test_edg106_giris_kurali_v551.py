"""test_edg106_giris_kurali_v551.py — EDG-2026-106 (TSK-224 tur 3): replay girişlerini koda sadık canlı giriş kuralıyla,
BÖLÜNME YENİDEN ÖLÇEKLEMELİ (bar geriye dönük bölünme-düzeltmeli, tick ham) tick arşivinde yeniden yürüten ölçüm betiğinin
çivileri (`research/olcumler/edg106_giris_kurali/olcum.py`).

KART: research/cards/EDG-2026-106-replay-giris-canli-kural-tick-olcekli.yaml — eşik, kill-list ve pozitif kontrol ORADA
donuktur; bu dosya betiğin karta SADAKATİNİ ölçer, kartı değil. Selef EDG-2026-105'in betiği ve v550'si DOKUNULMAZ (kartı o
betiğin blob'una bağlı tarihsel artefakt); bu dosya f = 1 satırların o betikle BAYT-ÖZDEŞ geçtiğini ayrıca çiviler.

NE ÖLÇÜLÜR (EDG-105'in v550 çivilerinin halefe uyarlanmışı + tur 3'ün yeni maddeleri):
  * ölçek eşleme — F kümesi kartla aynı, `fractions.Fraction` ile TAM; en yakın kesir, |r/f − 1| ≤ %2 (sınır DAHİL, float
    tuzağına düşmeden); kesir dışı → `olcek_eslenemez`; parite (plan kapanışı / tetik ∉ [0,9; 1,1]) → `olcek_parite_disi`.
  * yeniden ölçekleme — ÷ f ondalık-tam (10,0073 ÷ 1/10 = 100,073; float bölme 100,07300000000001 der), L ham birimde canlı
    çift yuvarlamayla; f ∈ {1/10, 1/2, 3} kimliği; f = 1 satırlar EDG-105 ile satır-düzeyi eşit.
  * monotonluk (kill-4) — ticker başına tek yönlü basamak dizisi; ihlalde TÜM f ≠ 1 satırlar eşlenemez.
  * sonuç alanı disiplini — yayımlanmayan durumda satır-düzeyi `fark_bps`/`canli_dolum` YAZILMAZ, DOLAN/DOLMAZ sayıları
    BASILMAZ (sonuc.json, OZET.md, stdout).
  * EDG-105'ten devralınanların hepsi: iki dal, L sınırları, 09:45/DST, karar kuralları, kill-list, PK-1/2/3, stdin/sha, EDG-102
    kopyalarının ve EDG-105 kopyalarının ayrışma çivileri.

PARQUET NEDEN DUCKDB İLE YAZILIR: bu venv'de pyarrow YOK (v546 ile aynı gerekçe). Betik yerelde `--okuyucu duckdb` koşar.
Test adlarında sonuç jetonları (büyük harfli başarısızlık/hata sözcükleri) BİLEREK kullanılmaz (CLAUDE.md §6).
"""
from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import inspect
import json
import pathlib
import random
import re
import sqlite3
import subprocess
import sys
from fractions import Fraction as F

import duckdb
import pytest
import yaml

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "research" / "olcumler" / "edg106_giris_kurali" / "olcum.py"
KART = REPO / "research" / "cards" / "EDG-2026-106-replay-giris-canli-kural-tick-olcekli.yaml"
KART105 = REPO / "research" / "cards" / "EDG-2026-105-replay-giris-canli-kural-tick-koda-sadik.yaml"
GOAL = REPO / "state" / "goal.yaml"
EDG102 = REPO / "research" / "olcumler" / "edg102_stop_kayma" / "olcum.py"
EDG105 = REPO / "research" / "olcumler" / "edg105_giris_kurali" / "olcum.py"

NS = 1_000_000_000
UTC = dt.timezone.utc


@pytest.fixture(scope="module")
def om():
    """Ölçüm betiği — KAYNAKTAN derlenmiş modül (ham exec_module yasağı v334)."""
    return betikten_modul_yukle(BETIK, "edg106_olcum")


@pytest.fixture(scope="module")
def e102():
    return betikten_modul_yukle(EDG102, "edg102_olcum_v551")


@pytest.fixture(scope="module")
def e105():
    """EDG-2026-105 betiği — f = 1 bayt-özdeşlik referansı; dosya yolundan, `meridian` değil."""
    return betikten_modul_yukle(EDG105, "edg105_olcum_v551")


@pytest.fixture
def hizli(om, monkeypatch):
    """CI değerinin konu OLMADIĞI kill/eşik çivilerinde bootstrap tekrar sayısını düşürür."""
    monkeypatch.setattr(om, "BOOT_B", 200)


def _kart() -> dict:
    return yaml.safe_load(KART.read_text(encoding="utf-8"))


def _goal() -> dict:
    return yaml.safe_load(GOAL.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# sentetik sahne kurucuları
# ---------------------------------------------------------------------------
def _ns(gun: str, saat: str, tz=UTC) -> int:
    t = dt.datetime.fromisoformat(f"{gun}T{saat}").replace(tzinfo=tz)
    return int(t.timestamp()) * NS


def _et(gun: str, saat: str) -> int:
    from zoneinfo import ZoneInfo
    return _ns(gun, saat, ZoneInfo("America/New_York"))


def _kayit(ts, fiyat_dolar, kosul=0, alis=None, satis=None, lot=100):
    """Betiğin kayıt biçimi: (ts, fiyat[1e-4 tamsayı], lot, kosul, k_alis, k_satis)."""
    def _i(x):
        return None if x is None else int(round(x * 10_000))
    return (ts, _i(fiyat_dolar), lot, kosul, _i(alis), _i(satis))


def _kural(om, gun: str, kayitlar: list, *, ref, tetik=50.0, dk=None):
    d = dt.date.fromisoformat(gun)
    esik = om.pencere_ns(d) if dk is None else om.pencere_ns(d, dk)
    return om.canli_kural(om.seans_suz(kayitlar, d), tetik, om.limit_fiyati(tetik), esik, ref)


def _is_gunleri(bas: str, adet: int) -> list[str]:
    g = dt.date.fromisoformat(bas)
    out = []
    while len(out) < adet:
        if g.weekday() < 5:
            out.append(g.isoformat())
        g += dt.timedelta(days=1)
    return out


def _onceki_is_gunu(gun: str) -> str:
    g = dt.date.fromisoformat(gun) - dt.timedelta(days=1)
    while g.weekday() >= 5:
        g -= dt.timedelta(days=1)
    return g.isoformat()


def _db_yaz(yol: pathlib.Path, islemler: list[dict], planlar: list[dict]) -> None:
    """SQLite defterini MOTORUN şemasıyla kurar (`storage._ddl` + `storage._row_to_cols`)."""
    from meridian import storage
    yol.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(yol))
    try:
        for ddl in storage._ddl():
            con.execute(ddl)
        for ad, tablo, satirlar in (("trades.jsonl", "trades", islemler),
                                    ("trade_plans.jsonl", "trade_plans", planlar)):
            kolonlar = [c for c, _ in storage._COLS[ad]]
            for s in satirlar:
                vals, extra = storage._row_to_cols(ad, s)
                ad_listesi = ",".join(f'"{c}"' for c in kolonlar) + ",extra_json"
                con.execute(f"INSERT INTO {tablo} ({ad_listesi}) VALUES "
                            f"({','.join('?' for _ in range(len(kolonlar) + 1))})", [*vals, extra])
        con.commit()
    finally:
        con.close()


def _parquet_yaz(yol: pathlib.Path, satirlar: list[tuple]) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE t (ts BIGINT, sembol VARCHAR, fiyat BIGINT, lot INTEGER, "
                    "kosul UTINYINT, k_ts BIGINT, k_alis_fiyat BIGINT, k_alis_lot INTEGER, "
                    "k_satis_fiyat BIGINT, k_satis_lot INTEGER)")
        if satirlar:
            con.executemany("INSERT INTO t VALUES (?,?,?,?,?,?,?,?,?,?)", satirlar)
        con.execute(f"COPY t TO '{yol}' (FORMAT PARQUET)")
    finally:
        con.close()


def _bar_yaz(kok: pathlib.Path, ticker: str, barlar: dict[str, tuple]) -> None:
    kok.mkdir(parents=True, exist_ok=True)
    yol = kok / f"{ticker.lower().replace('.', '-')}.csv"
    satir = ["date,open,high,low,close,volume"]
    for g in sorted(barlar):
        o, h, l, c = barlar[g]
        satir.append(f"{g},{o!r},{h!r},{l!r},{c!r},1000000.0")
    yol.write_text("\n".join(satir) + "\n", encoding="utf-8")


TETIK = 50.0
GIRIS = 50.0
ACILIS = GIRIS / 1.0005

#: sembol → (plan günü kapanışı = ref, ET akışı [(saat, fiyat | "DOLUM")], bar yükseği, çıkış nedeni, r) — PLAN birimi
AKISLAR = {
    "AAA": (50.0, [("09:30:00", 49.90), ("09:45:00", 50.50), ("09:45:01", "DOLUM"), ("10:00:00", 51.00)],
            51.00, "target", 1.5),
    "BBB": (49.0, [("09:30:00", 50.40), ("09:45:00", 49.50), ("10:00:00", 49.80), ("10:30:00", 50.00),
                   ("10:30:01", "DOLUM"), ("11:00:00", 50.10)], 50.40, "target", 1.2),
    "CCC": (49.0, [("09:31:00", 49.70), ("09:45:30", 49.60), ("12:00:00", 50.20), ("12:00:01", 52.50),
                   ("12:00:02", "DOLUM")], 52.50, "trail", 0.4),
    "DDD": (49.0, [("09:30:00", 49.90), ("09:50:00", 49.20), ("11:00:00", 49.90), ("15:59:59", 49.95),
                   ("16:00:00", 50.50)], 49.95, "stop", -1.0),
    "EEE": (50.0, [("09:30:00", 50.20), ("09:45:00", 49.40), ("09:45:02", 49.45), ("11:00:00", 49.60),
                   ("15:00:00", 49.70)], 50.20, "stop", -0.8),
}


def _ham(adj: float, f: F) -> int:
    """Plan birimindeki fiyatı ölçek f ile HAM (tick) birime çevirip 1e-4 tamsayı yapar: ham = adj ÷ f."""
    return int(round(float(F(repr(adj)) / f) * 10_000))


def _akis_satirlari(g: str, sym: str, taban: str, dolum: float, kosul: int, f: F) -> list[tuple]:
    def r(saat, fiyat):
        t = _et(g, saat)
        p = _ham(fiyat, f)
        return (t, sym, p, 100, kosul, t, p - 100, 100, p + 100, 100)
    out = [r("08:00:00", 51.00)]
    for saat, fiyat in AKISLAR[taban][1]:
        out.append(r(saat, dolum if fiyat == "DOLUM" else fiyat))
    return out


def _sahne(tmp_path, *, gun_sayisi=100, dolum=50.06, dolmaz=True, kosul=0, bas="2024-01-02", ekler=None,
           yalniz=None) -> dict:
    """Uçtan uca sahne (plan birimi = bar birimi). `ekler`: {sembol: (taban sembol, f(i) → Fraction, plan kapanışı)} —
    taban akışının HAM tick'i f ile ölçeklenmiş kopyası (bar CSV'si bölünme-düzeltmeli kalır). `yalniz`: taban sembol süzgeci."""
    kok = tmp_path / "sahne"
    state = kok / "state"
    tick = kok / "veri" / "tick" / "islem"
    bars = state / "bars"
    gunler = _is_gunleri(bas, gun_sayisi)
    tanim = {s: (s, (lambda i: F(1)), AKISLAR[s][0]) for s in AKISLAR
             if (dolmaz or s != "DDD") and (yalniz is None or s in yalniz)}
    tanim.update(ekler or {})
    islemler, planlar = [], []
    gun_tik: dict[str, list] = {g: [] for g in gunler}
    bar_ser: dict[str, dict] = {s: {} for s in tanim}
    ilk_plan = _onceki_is_gunu(bas)
    n = 0
    for i, g in enumerate(gunler):
        onceki = gunler[i - 1] if i else ilk_plan
        for sym, (taban, f_fn, ref) in tanim.items():
            n += 1
            _, _, yuksek, neden, rm = AKISLAR[taban]
            pid = f"P-{onceki}-{sym}"
            islemler.append({"id": f"T{n:05d}", "plan_id": pid, "ticker": sym, "side": "long",
                             "ts_open": g, "ts_close": g, "entry": GIRIS, "exit": 51.0, "qty": 10,
                             "r_multiple": rm, "exit_reason": neden, "strategy_version": 91, "kaynak": "replay_seed"})
            planlar.append({"id": pid, "date": onceki, "ticker": sym, "side": "long", "entry_trigger": TETIK,
                            "stop": 48.0, "profit_target": 55.0, "strategy_version": 91})
            gun_tik[g] += _akis_satirlari(g, sym, taban, dolum, kosul, f_fn(i))
            bar_ser[sym][g] = (ACILIS, yuksek, 48.5, ref)
    for sym, (_, _, ref) in tanim.items():
        bar_ser[sym][ilk_plan] = (ACILIS, 50.0, 48.5, ref)
    gurultu = dict(islemler[0], id="T99999", kaynak="live_paper")
    _db_yaz(state / "meridian.db", islemler + [gurultu], planlar)
    for g, s in gun_tik.items():
        _parquet_yaz(tick / f"{g}.parquet", s)
    for sym, ser in bar_ser.items():
        _bar_yaz(bars, sym, ser)
    return {"db": state / "meridian.db", "tick": tick, "bars": bars, "cikti": kok / "cikti",
            "gunler": gunler, "state": state, "n": len(islemler)}


SPL = {"SPL": ("AAA", lambda i: F(1, 10) if i < 50 else F(1), 50.0)}       # ileri bölünme 10:1, gün 50'de
ZIG_DESEN = [F(1, 2), F(1, 2), F(1), F(1), F(1, 2), F(1), F(1), F(1)]   # 8 gün: 24 satır ≥ öz-sınama 20
ZIG_PAR = {"ZIG": ("AAA", lambda i: ZIG_DESEN[i], 50.0),                     # monoton DEĞİL: 1/2 → 1 → 1/2
           "PAR": ("AAA", lambda i: F(1), 62.5)}                            # plan kapanışı / tetik = 1,25


def _kos(om, sahne, *ek) -> int:
    return om.main(["--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]),
                    "--bar-kok", str(sahne["bars"]), "--cikti", str(sahne["cikti"]),
                    "--okuyucu", "duckdb", *ek])


def _sonuc(sahne, ad="sonuc.json") -> dict:
    return json.loads((sahne["cikti"] / ad).read_text(encoding="utf-8"))


def _agac_fotografi(kok: pathlib.Path, haric: pathlib.Path) -> dict:
    out = {}
    for p in sorted(kok.rglob("*")):
        if p.is_file() and haric not in p.parents:
            out[str(p.relative_to(kok))] = (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
    return out


G = "2024-07-10"   # EDT


def _satir(om, *, tetik, ref, acilis, entry=None, yuksek=None, dusuk=None):
    """`satir_olc` girdisi — PLAN birimi (bar CSV birimi); `limit` satirlari_hazirla'daki gibi plan biriminde."""
    return {"seans": G, "tetik": tetik, "limit": om.limit_fiyati(tetik), "entry": entry or tetik,
            "bar_acilis": acilis, "ref_kapanis": ref,
            "bar": {"open": acilis, "high": yuksek or tetik * 1.02, "low": dusuk or tetik * 0.97, "close": ref}}


# ---------------------------------------------------------------------------
# ÖLÇEK EŞLEME — F kümesi, en yakın kesir, %2 sınırı, Fraction
# ---------------------------------------------------------------------------
def test_olcek_kumesi_KART_tanimiyla_AYNI_ve_TAM_kesir(om):
    beklenen = ({F(1)} | {F(1, k) for k in range(2, 31)} | {F(k) for k in range(2, 11)}
                | {F(2, 3), F(3, 4), F(4, 5), F(3, 2), F(4, 3), F(5, 4)})
    assert set(om.OLCEK_KUMESI) == beklenen and len(om.OLCEK_KUMESI) == len(beklenen) == 45
    assert all(isinstance(f, F) for f in om.OLCEK_KUMESI)
    assert om.OLCEK_TOL == F(2, 100) and om.OLCEK_TOL_PCT == 2


@pytest.mark.parametrize("acilis,tik,beklenen", [
    (50.0, 500_000, F(1)), (5.0, 500_000, F(1, 10)), (25.0, 500_000, F(1, 2)), (150.0, 500_000, F(3)),
    (2.0, 500_000, F(1, 25)), (33.3333, 500_000, F(2, 3)), (8.3333, 500_000, F(1, 6)), (500.0, 500_000, F(10)),
])
def test_olcek_esle_EN_YAKIN_basit_kesir(om, acilis, tik, beklenen):
    assert om.olcek_esle(acilis, tik)["f"] == beklenen


@pytest.mark.parametrize("acilis,tik,beklenen", [
    (0.765625, 78_125, F(1, 10)),    # r/f = 0,98 TAM → |.−1| = %2 → DAHİL (float'ta 0,020000000000000018 > 0,02)
    (2.65625, 78_125, F(1, 3)),      # r/f = 1,02 TAM → DAHİL
    (0.7656, 78_125, None),          # %2,003 → eşlenemez
    (5.25, 500_000, None),           # r = 0,105: 1/10'a %5 uzak — %2 dışı (tolerans %5 olsaydı eşlenirdi)
    (51.5, 500_000, None),           # r = 1,03: 1'e %3, 5/4'e %17,6
])
def test_olcek_toleransi_YUZDE2_sinir_DAHIL_TAM_kesirle(om, acilis, tik, beklenen):
    assert om.olcek_esle(acilis, tik)["f"] == beklenen


def test_olcek_esle_ikinci_aday_RAPORLANIR(om):
    """1/29 ile 1/30 arası r iki adaya da %2 içinde yakın olabilir — en yakın seçilir, ikincisi raporlanır."""
    e = om.olcek_esle(50.0 / 29.45, 500_000)
    assert e["f"] == F(1, 29) and e["ikinci_aday"] == F(1, 30)
    assert om.olcek_esle(5.0, 500_000)["ikinci_aday"] is None


def test_olcekle_ONDALIK_tam_bolme_float_tuzagi_YOK(om):
    assert 10.0073 / float(F(1, 10)) != 100.073                  # float bölme tuzağı (ölçüldü)
    assert om.olcekle(10.0073, F(1, 10)) == 100.073
    assert om.olcekle(1.07, F(1, 10)) == 10.7                    # Fraction(1.07) olsaydı 10.700000000000001
    assert om.olcekle(150.0, F(3)) == 50.0 and om.olcekle(25.0, F(1, 2)) == 50.0
    x = 48.37
    assert om.olcekle(x, F(1)) is x


def test_olcekli_STOP_aktivasyonu_TAM_ham_tetikte(om):
    """tetik 10,0073 (plan) × 10 = 100,073 (ham): 100,073'lük tik aktivasyondur (float ÷ f 100,07300000000001 derdi)."""
    kay = [_kayit(_et(G, "09:30:00"), 100.0), _kayit(_et(G, "09:45:00"), 99.5), _kayit(_et(G, "10:00:00"), 100.073),
           _kayit(_et(G, "10:00:01"), 100.07)]
    r = _satir(om, tetik=10.0073, ref=9.9, acilis=10.0)
    om.satir_olc(r, kay)
    assert r["olcek_f"] == "1/10" and r["tetik_tik"] == 100.073 and r["dal"] == "STOP_LIMIT"
    assert r["sinif"] == "DOLAN" and r["canli_dolum"] == 100.07


def test_L_HAM_birimde_canli_zincirle_hesaplanir(om):
    """tetik 10,0125 (plan), f = 1/10: ham L = zincir(100,125) = 104,13; plan biriminde L = 10,41 × 10 = 104,1 olurdu."""
    kay = [_kayit(_et(G, "09:30:00"), 100.0), _kayit(_et(G, "09:45:00"), 104.5), _kayit(_et(G, "09:45:01"), 104.12),
           _kayit(_et(G, "09:45:02"), 104.05)]
    r = _satir(om, tetik=10.0125, ref=10.0125, acilis=10.0)
    om.satir_olc(r, kay)
    assert r["limit_tik"] == 104.13 and om.limit_fiyati(10.0125) * 10 != 104.13
    assert r["sinif"] == "DOLAN" and r["canli_dolum"] == 104.12


@pytest.mark.parametrize("f", [F(1, 10), F(1, 2), F(3)])
def test_olcek_KIMLIGI_bilinen_f_ile_f1_akisiyla_AYNI_sonuc(om, f):
    """Kart PK-1 ek ayağı: ham akış + plan fiyatları × f → ölçeklenmiş satır, f = 1 (ham plan) satırıyla aynı dal/dolum/fark."""
    kay = [_kayit(_et(G, "09:30:00"), 59.80), _kayit(_et(G, "09:45:00"), 59.40), _kayit(_et(G, "10:00:00"), 60.00),
           _kayit(_et(G, "10:00:01"), 60.06), _kayit(_et(G, "11:00:00"), 60.50)]

    def olc(k):
        return float(F(repr(k)) * f)
    r1 = _satir(om, tetik=60.0, ref=59.0, acilis=59.80, yuksek=60.5, dusuk=59.4)
    rf = _satir(om, tetik=olc(60.0), ref=olc(59.0), acilis=olc(59.80), entry=olc(60.0), yuksek=olc(60.5),
                dusuk=olc(59.4))
    om.satir_olc(r1, kay)
    om.satir_olc(rf, kay)
    assert r1["olcek_f"] == "1" and rf["olcek_f"] == str(f)
    for k in ("sinif", "dal", "canli_dolum", "tetik_tik", "limit_tik", "entry_tik", "pk3_bar_yuksek", "pk3_bar_dusuk",
              "pk3_tik_yuksek", "pk3_tik_dusuk"):
        assert rf[k] == r1[k], k
    assert abs(rf["fark_bps"] - r1["fark_bps"]) < 1e-9 and r1["sinif"] == "DOLAN"


def test_olcek_ESLENEMEZ_ve_PARITE_disi_siniflari(om):
    kay = [_kayit(_et(G, "09:30:00"), 50.0), _kayit(_et(G, "09:45:00"), 50.5), _kayit(_et(G, "09:45:01"), 50.1)]
    r = _satir(om, tetik=50.0, ref=50.0, acilis=52.5)                  # r = 1,05 → kesir dışı
    om.satir_olc(r, kay)
    assert r["sinif"] == "olcek_eslenemez" and r["olcek_alt_neden"] == "kesir_disi" and "canli_dolum" not in r
    for ref, beklenen in ((62.5, "olcek_parite_disi"), (55.0, "DOLAN"), (45.0, "DOLAN"), (44.99, "olcek_parite_disi")):
        r = _satir(om, tetik=50.0, ref=ref, acilis=50.0)
        om.satir_olc(r, kay)
        assert r["sinif"] == beklenen, ref
    r = _satir(om, tetik=50.0, ref=None, acilis=50.0)
    om.satir_olc(r, kay)
    assert r["sinif"] == "olcek_olculemedi" and r["olcek_alt_neden"] == "ref_yok"


# ---------------------------------------------------------------------------
# MONOTONLUK (kill-4)
# ---------------------------------------------------------------------------
def _mono(tkr, seans, f, sinif="DOLAN"):
    return {"ticker": tkr, "seans": seans, "seq": 0, "_f": f, "olcek_f": str(f), "sinif": sinif, "fark_bps": 3.0,
            "canli_dolum": 10.0, "pk3_bar_yuksek": True, "pk3_tik_yuksek": True}


def test_kill4_monotonluk_TEK_YON_ihlalde_TUM_f1_disi_satirlar_ESLENEMEZ(om):
    s = [_mono("NVDA", "2024-06-03", F(1, 10)), _mono("NVDA", "2024-06-05", F(1, 10)), _mono("NVDA", "2024-06-12", F(1)),
         _mono("DD", "2023-01-05", F(3)), _mono("DD", "2023-06-05", F(1)),
         _mono("IKI", "2022-01-05", F(1, 4)), _mono("IKI", "2023-01-05", F(1, 2)), _mono("IKI", "2024-01-05", F(1)),
         _mono("ZIG", "2024-01-05", F(1, 2)), _mono("ZIG", "2024-03-05", F(1)),
         _mono("ZIG", "2024-02-05", F(1, 2), sinif="olcek_parite_disi")]         # tarih sırası: 1/2, 1/2, 1 ✓ — ama:
    s.append(_mono("ZIG", "2024-04-05", F(1, 2)))                                # … 1 → 1/2 ✗
    m = om.monotonluk_uygula(s)
    assert set(m["ihlal_tickerlar"]) == {"ZIG"} and m["yeniden_siniflanan_n"] == 3
    for r in s:
        if r["ticker"] == "ZIG" and r["_f"] != 1:
            assert r["sinif"] == "olcek_eslenemez" and r["olcek_alt_neden"] == "monotonluk_ihlali"
            assert "fark_bps" not in r and "canli_dolum" not in r and r["pk3_bar_yuksek"] is None
        else:
            assert r["sinif"] in ("DOLAN", "olcek_parite_disi") and "fark_bps" in r


# ---------------------------------------------------------------------------
# Emir tipi (kill-7) ve öykünücü — EDG-105'ten devralınan çiviler
# ---------------------------------------------------------------------------
def test_kill7_tip_YALNIZ_plan_gunu_kapanisindan_0945_fiyatindan_BAGIMSIZ(om):
    alt = [_kayit(_et(G, "09:45:00"), 49.40), _kayit(_et(G, "09:45:02"), 49.45), _kayit(_et(G, "11:00:00"), 49.6)]
    k = _kural(om, G, alt, ref=50.0)
    assert k["dal"] == "GAP" and k["sinif"] == "DOLAN" and k["dolum_i"] == 1 and k["canli_dolum"] == 49.45
    ust = [_kayit(_et(G, "09:45:00"), 50.50), _kayit(_et(G, "09:45:01"), 50.30)]
    k = _kural(om, G, ust, ref=49.0)
    assert k["dal"] == "STOP_LIMIT" and k["akt_i"] == 0 and k["dolum_i"] == 1 and k["canli_dolum"] == 50.3
    assert inspect.signature(om.canli_kural).parameters["ref"].default is inspect.Parameter.empty
    assert om.TIP_KAYNAGI == "plan_gunu_kapanisi"


def test_emir_tipi_MOTORUN_entry_order_decision_ile_AYNI(om):
    from meridian import broker as B
    cfg = B.entry_law(override=_goal()["execution_v2"])
    rng = random.Random(105)
    esle = {"marketable_limit": "GAP", "stop_limit": "STOP_LIMIT"}
    for _ in range(2000):
        t = round(rng.uniform(1.0, 1500.0), 4)
        ref = rng.choice([t, round(t + 1e-4, 4), round(t - 1e-4, 4), round(t * rng.uniform(0.9, 1.1), 4)])
        assert esle[B.entry_order_decision(t, ref_price=ref, atr=None, cfg=cfg)["mode"]] == om.emir_tipi(ref, t)


def test_GAP_dali_dolum_t0dan_SONRAKI_ilk_limit_ici_kayit(om):
    kay = [_kayit(_et(G, "09:30:00"), 49.0), _kayit(_et(G, "09:45:00"), 50.5),
           _kayit(_et(G, "09:45:01"), 50.06), _kayit(_et(G, "10:00:00"), 51.0)]
    k = _kural(om, G, kay, ref=50.0)
    assert k["dal"] == "GAP" and k["sinif"] == "DOLAN" and k["t0_i"] == 1 and k["dolum_i"] == 2


def test_STOP_LIMIT_dali_aktivasyon_TAM_tetikte_ve_SONRAKI_kayitta_dolum(om):
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "10:00:00"), 49.8),
           _kayit(_et(G, "10:30:00"), 50.0), _kayit(_et(G, "10:30:01"), 50.07)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["dal"] == "STOP_LIMIT" and k["sinif"] == "DOLAN" and k["akt_i"] == 2 and k["dolum_i"] == 3


def test_L_ustunde_kalan_akis_ve_tetiksiz_akis_DOLMAZ(om):
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "10:00:00"), 50.2), _kayit(_et(G, "10:00:01"), 52.01)]
    assert _kural(om, G, kay, ref=49.0)["neden"] == "limit_ici_kayit_yok"
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "15:59:59"), 49.9), _kayit(_et(G, "16:00:00"), 51.0)]
    assert _kural(om, G, kay, ref=49.0)["neden"] == "tetik_kirilmadi"


def test_L_siniri_ve_CIFT_yuvarlama(om):
    assert om.limit_fiyati(TETIK) == 52.0
    assert _kural(om, G, [_kayit(_et(G, "09:45:00"), 52.5), _kayit(_et(G, "09:45:01"), 52.0)], ref=50.0)["sinif"] == "DOLAN"
    assert _kural(om, G, [_kayit(_et(G, "09:45:00"), 52.5), _kayit(_et(G, "09:45:01"), 52.01)],
                  ref=50.0)["sinif"] == "DOLMAZ"
    assert om.limit_fiyati(1.0337) == 1.07 and om.limit_fiyati(1.0913) == 1.14 and om.limit_fiyati(12.315) == 12.81


def test_0944_59_kirilimi_SAYILMAZ_ve_t0_nanosaniye_siniri(om):
    kay = [_kayit(_et(G, "09:30:00"), 49.0), _kayit(_et(G, "09:44:59"), 50.5), _kayit(_et(G, "09:45:00"), 49.8)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["t0_i"] == 2 and k["sinif"] == "DOLMAZ"
    p = _et(G, "09:45:00")
    assert _kural(om, G, [_kayit(p - 1, 50.5), _kayit(p, 49.0)], ref=49.0)["t0_i"] == 1


@pytest.mark.parametrize("gun,pencere_utc", [("2024-01-10", "14:45:00"), ("2024-03-11", "13:45:00"),
                                              ("2024-11-04", "14:45:00")])
def test_pencere_DST_farkinda(om, gun, pencere_utc):
    assert om.pencere_ns(dt.date.fromisoformat(gun)) == _ns(gun, pencere_utc)


def test_akis_yok_ve_fark_isareti(om):
    assert _kural(om, G, [_kayit(_et(G, "09:44:00"), 50.5)], ref=50.0)["sinif"] == "akis_yok"
    assert abs(om.fark_bps(50.06, 50.0) - 12.0) < 1e-9 and om.fark_bps(49.94, 50.0) < 0


def test_PK1_calisma_ani_kimlik_OLCEK_ayagi_dahil_gecer(om):
    r = om.pk1_kimlik()
    assert r["gecti"] is True, r
    assert r["olcek_kimligi"] == {"1/10": True, "1/2": True, "3": True} and r["olcek_eslenemez"] is True


# ---------------------------------------------------------------------------
# Motor ↔ betik ↔ kart ↔ selef betik (tek-kaynak)
# ---------------------------------------------------------------------------
def test_sabitler_MOTOR_ve_goal_ile_ayni(om):
    from meridian import barclock
    goal = _goal()
    assert om.GIRIS_PENCERE_ET_DK == barclock.ENTRY_WINDOW_ET_MIN
    assert float(goal["execution_v2"]["limit_pct_cap"]) == om.LIMIT_PCT_CAP
    assert float(goal["slippage_bps"]) == om.SLIP_BPS


def test_limit_KURUS_yuvarlamasi_CANLI_emir_govdesiyle_AYNI(om, sandbox_state, monkeypatch):
    from meridian import broker as B
    from meridian.adapters import alpaca as A
    govdeler = []

    class _Yanit:
        status_code = 200

        def json(self):
            return {"id": "sahte"}

    def _post(url, headers=None, json=None, timeout=None):
        govdeler.append(json)
        return _Yanit()
    monkeypatch.setattr(A, "_paper_base", lambda: "https://paper-api.alpaca.markets")
    monkeypatch.setattr(A, "_headers", lambda: {})
    monkeypatch.setattr(A.httpx, "post", _post)
    cfg = B.entry_law(override=_goal()["execution_v2"])
    rng = random.Random(1060)
    for t in [100.125, 100.073, 1.0337, 1.0913, 500.0] + [round(rng.uniform(1, 2000), 4) for _ in range(300)]:
        dec = B.entry_order_decision(t, ref_price=t, atr=None, cfg=cfg)
        assert dec["limit"] == om.limit_karar(t) and dec["limit"] == om.limit_karar(t)
        A.submit_bracket("ZZZ", 10, t, t * 1.2, t * 0.9, client_order_id="P-v551", entry_limit=dec["limit"],
                         entry_type="limit")
        assert govdeler[-1]["limit_price"] == om.limit_fiyati(t), t


def test_replay_giris_MOTORUN_fill_entry_satiriyla_BIREBIR(om, sandbox_state):
    from meridian import broker as B
    rng = random.Random(20260925)
    for i in range(200):
        tetik = round(rng.uniform(5.0, 800.0), 4)
        acilis = round(tetik * rng.uniform(0.95, 1.009), 2)
        br = B.PaperBroker(100_000.0, om.SLIP_BPS, 0.0)
        plan = {"id": f"P{i}", "ticker": "ZZZ", "stop": round(min(tetik, acilis) * 0.9, 4),
                "entry_trigger": tetik, "size_r": 1.0, "profit_target": round(tetik * 1.3, 4)}
        assert br.fill_entry(plan, acilis, "2024-02-01", 100_000.0) is not None
        assert br.close_position("ZZZ", acilis, "target", "2024-02-02")["entry"] == om.replay_giris(acilis)


def test_betik_sabitleri_KARTLA_ayni(om):
    kart = _kart()
    assert kart["card_id"] == om.KART_ID == "EDG-2026-106" and kart["selef"] == "EDG-2026-105"
    e = kart["esikler"]
    assert e["n_uygun_alt"] == om.N_UYGUN_ALT == 300 and e["seans_alt"] == om.SEANS_ALT == 100
    assert e["dolmaz_esik_pct"] == om.DOLMAZ_ESIK_PCT == 5 and e["fiyat_bandi_bps"] == om.FIYAT_BANDI_BPS == 5
    assert e["olcek_eslem_tolerans_pct"] == om.OLCEK_TOL_PCT == 2
    for s in (om.KARAR_H1_IYIMSER, om.KARAR_H1_ESDEGER, om.KARAR_H2_IYIMSER, om.KARAR_H2_KOTUMSER,
              om.KARAR_H2_ESDEGER, om.KARAR_BELIRSIZ):
        assert f'"{s}"' in e["karar_kurali"], s
    kl = kart["kill_list"]
    assert len(kl) == 8
    assert "%10'u → YAYIMLANMAZ" in kl[1] and om.AKIS_YOK_TAVAN == 0.10
    assert "(olcek_eslenemez + olcek_parite_disi + ölçülemeyen) / (aday − akis_yok) > %5" in kl[2]
    assert om.OLCEK_DISLANAN_TAVAN == 0.05
    assert "MONOTON" in kl[3] and "TÜM f ≠ 1 satırları `olcek_eslenemez`" in kl[3]
    assert "%10'u → CI şerhli" in kl[4] and om.TEK_SEANS_TAVAN == 0.10
    plan = " ".join(kart["olcum_plani"])
    assert "F = {1} ∪ {1/k : k=2..30} ∪ {k : k=2..10} ∪ {2/3, 3/4, 4/5, 3/2, 4/3, 5/4}" in plan
    assert "|r/f − 1| ≤ %2" in plan and "[0,9, 1,1]" in plan and om.OLCEK_BANDI == (0.9, 1.1)
    assert "÷ f" in plan and "B=5000" in plan and "seed=20260812" in plan
    assert "4 / 836 = %0,48" in kart["adim_0_kaydi_2026_09_25"] and om.ADIM0_BEKLENEN_KILL3 == (4, 836)
    pk = kart["pozitif_kontrol"]
    assert "(1/10, 1/2, 3)" in pk and "en az 1 f ≠ 1" in pk
    assert len(kart["k_registry"]["trial_ids"]) == 2


def test_erken_kapanis_listesi_EDG105_KARTI_ve_mcal_ile_AYNI(om):
    metin = yaml.safe_load(KART105.read_text(encoding="utf-8"))["adim_0_kaydi_2026_09_25"]
    blok = metin.split("XNYS erken kapanış")[1].split("bu günlerde")[0]
    import pandas_market_calendars as mcal
    takvim = mcal.get_calendar("XNYS")
    erken = takvim.early_closes(takvim.schedule("2022-01-01", "2026-07-31"))
    assert tuple(re.findall(r"\d{4}-\d{2}-\d{2}", blok)) == tuple(om.ERKEN_KAPANIS_GUNLERI) == \
        tuple(d.date().isoformat() for d in erken.index)


# ---------------------------------------------------------------------------
# Öz-sınama, karar kuralları
# ---------------------------------------------------------------------------
def test_kill1_oz_sinama_siniri_ve_toleransi(om):
    s = om.SLIP_BPS / 10_000.0
    assert om.oz_fark_bps(GIRIS, (GIRIS - GIRIS * 0.99e-4) / (1.0 + s)) <= 1.0
    assert om.oz_fark_bps(GIRIS, (GIRIS - GIRIS * 1.01e-4) / (1.0 + s)) > 1.0
    rows = [{"oz_fark_bps": 0.3}] * 19 + [{"oz_fark_bps": 2.0}] * 5
    assert om.oz_sinama_ozeti(rows)["gecti"] is False and om.oz_sinama_ozeti(rows + [{"oz_fark_bps": 0.1}])["gecti"]


@pytest.mark.parametrize("alt,ust,beklenen", [(5.01, 9.0, "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"),
                                              (5.0, 9.0, "BELİRSİZ"), (1.0, 5.0, "DOLUM EŞDEĞER")])
def test_karar_H1_dallari(om, alt, ust, beklenen):
    assert om.karar_h1(alt, ust) == beklenen


@pytest.mark.parametrize("alt,ust,beklenen", [(5.01, 9.0, "REPLAY GİRİŞ FİYATI İYİMSER"), (5.0, 9.0, "BELİRSİZ"),
                                              (-9.0, -5.01, "REPLAY GİRİŞ FİYATI KÖTÜMSER"), (-9.0, -5.0, "BELİRSİZ"),
                                              (-5.0, 5.0, "GİRİŞ FİYATI EŞDEĞER (model yeterli)")])
def test_karar_H2_dallari(om, alt, ust, beklenen):
    assert om.karar_h2(alt, ust) == beklenen


# ---------------------------------------------------------------------------
# ozetle — paydalar, kill-list
# ---------------------------------------------------------------------------
def _ozet_satirlari(n_dolan, n_dolmaz, n_seans, *, fark=12.0, n_akis_yok=0, n_eslenemez=0, n_parite=0,
                    n_olculemedi=0, buyuk_seans=0, pk3_tutarsiz=0):
    gunler = _is_gunleri("2023-01-02", n_seans)

    def satir(sinif, seans, i, f=None):
        olc = sinif != "akis_yok" or None
        return {"sinif": sinif, "seans": seans, "fark_bps": f, "dal": "GAP", "plan_dal": "GAP", "tetik": 50.0,
                "ticker": f"T{i}", "seq": i, "acilis_dal": "acilis_alti", "_f": F(1), "olcek_f": "1",
                "pk3_bar_yuksek": olc, "pk3_tik_yuksek": olc, "pk3_bar_dusuk": olc, "pk3_tik_dusuk": olc}
    s = [satir("DOLAN", gunler[i % n_seans], i, fark) for i in range(n_dolan)]
    s += [satir("DOLMAZ", gunler[i % n_seans], 10_000 + i) for i in range(n_dolmaz)]
    s += [satir("DOLAN", gunler[0], 20_000 + i, fark) for i in range(buyuk_seans)]
    s += [satir("akis_yok", gunler[i % n_seans], 30_000 + i) for i in range(n_akis_yok)]
    for sinif, n in (("olcek_eslenemez", n_eslenemez), ("olcek_parite_disi", n_parite),
                     ("olcek_olculemedi", n_olculemedi)):
        s += [satir(sinif, gunler[i % n_seans], 40_000 + i) for i in range(n)]
    for r in [r for r in s if r["pk3_tik_yuksek"] is not None][:pk3_tutarsiz]:
        r["pk3_tik_yuksek"] = False
    return s


_OZ = {"gecti": True}
_PK1 = {"gecti": True}


def test_H1_orani_DOLMAZ_PAYDADA_ve_iki_hukum_AYRI(om):
    o = om.ozetle(_ozet_satirlari(300, 100, 100, fark=0.0), _OZ, _PK1)
    assert o["h1"]["oran_pct"] == 25.0 and o["h1"]["karar"] == "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"
    assert o["h2"]["karar"] == "GİRİŞ FİYATI EŞDEĞER (model yeterli)" and o["durum"] == "KOSULLU_HUKUM"


def test_n_ve_seans_esigi(om, hizli):
    assert om.ozetle(_ozet_satirlari(299, 0, 100), _OZ, _PK1)["durum"] == "OLCULEMEDI"
    assert om.ozetle(_ozet_satirlari(300, 0, 100), _OZ, _PK1)["durum"] == "KOSULLU_HUKUM"
    assert om.ozetle(_ozet_satirlari(400, 0, 99), _OZ, _PK1)["durum"] == "OLCULEMEDI"


def test_kill2_akis_yok_TAM_yuzde10_gecer_USTU_yayimlanmaz(om, hizli):
    assert om.ozetle(_ozet_satirlari(360, 0, 100, n_akis_yok=40), _OZ, _PK1)["kill_list"]["akis_yok_asimi"] is False
    o = om.ozetle(_ozet_satirlari(360, 0, 100, n_akis_yok=41), _OZ, _PK1)
    assert o["kill_list"]["akis_yok_asimi"] is True and o["durum"] == "YAYIMLANMAZ"


def test_kill3_ESLENEMEZ_PARITE_OLCULEMEZ_toplami_TAM_yuzde5(om, hizli):
    o = om.ozetle(_ozet_satirlari(380, 0, 100, n_eslenemez=7, n_parite=7, n_olculemedi=6, n_akis_yok=5), _OZ, _PK1)
    assert o["kill_list"]["olcek_dislanan_pct"] == 5.0 and o["kill_list"]["olcek_asimi"] is False
    assert o["kill_list"]["olcek_eslenemez_n"] == 7 and o["kill_list"]["olcek_parite_disi_n"] == 7
    o = om.ozetle(_ozet_satirlari(380, 0, 100, n_eslenemez=7, n_parite=7, n_olculemedi=7, n_akis_yok=5), _OZ, _PK1)
    assert o["kill_list"]["olcek_asimi"] is True and o["durum"] == "YAYIMLANMAZ"
    # PAYDA AYIRICI: 21 / (aday − akis_yok = 400) = %5,25 → aşım; yanlış payda 21 / 440 = %4,77 geçerdi
    o = om.ozetle(_ozet_satirlari(379, 0, 100, n_eslenemez=21, n_akis_yok=40), _OZ, _PK1)
    assert o["kill_list"]["olcek_dislanan_pct"] == 5.25 and o["kill_list"]["olcek_asimi"] is True


def test_kill5_tek_seans_TAM_yuzde10_serhsiz_USTU_serhli(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 0, 100, buyuk_seans=30), _OZ, _PK1)
    assert o["h2"]["tek_seans_payi"] == 0.10 and o["h2"]["ci_serh"] is None
    o = om.ozetle(_ozet_satirlari(300, 0, 100, buyuk_seans=31), _OZ, _PK1)
    assert o["h2"]["ci_serh"].startswith("kill-5:") and o["h2"]["ci95_bps"] is not None


def test_kill8_PK1_PK3_ve_oz_sinama(om, hizli):
    assert om.ozetle(_ozet_satirlari(300, 0, 100), _OZ, {"gecti": False})["durum"] == "GECERSIZ"
    assert om.ozetle(_ozet_satirlari(300, 0, 100), {"gecti": False}, _PK1)["durum"] == "GECERSIZ"
    assert om.ozetle(_ozet_satirlari(400, 0, 100, pk3_tutarsiz=80), _OZ, _PK1)["pk3"]["dustu"] is False
    assert om.ozetle(_ozet_satirlari(400, 0, 100, pk3_tutarsiz=81), _OZ, _PK1)["durum"] == "GECERSIZ"


def test_PK3_iki_kosul_DUSUK_yalniz_GAPta(om):
    def satir(dal, by, ty, bd, td):
        return {"sinif": "DOLAN", "seans": G, "plan_dal": dal, "pk3_bar_yuksek": by, "pk3_tik_yuksek": ty,
                "pk3_bar_dusuk": bd, "pk3_tik_dusuk": td}
    p = om.pk3_ozeti([satir("GAP", True, True, True, False), satir("STOP_LIMIT", True, True, True, False),
                      satir("STOP_LIMIT", True, False, None, None), satir("GAP", True, True, None, True),
                      satir("GAP", True, True, True, True)])
    assert p["payda_n"] == 4 and p["tutarsiz_n"] == 2 and p["dusuk_tutarsiz_n"] == 1 and p["olculemedi_n"] == 1


def test_PK3_olculemezse_ayak_DUSMUS_sayilir(om, hizli):
    s = _ozet_satirlari(300, 0, 100)
    for r in s:
        r["pk3_bar_yuksek"] = None
    o = om.ozetle(s, _OZ, _PK1)
    assert o["pk3"]["payda_n"] == 0 and o["pk3"]["dustu"] is True and o["durum"] == "GECERSIZ"


def test_paydalar_BEYANI_her_kalemi_tasir(om):
    for k in ("aday", "erken_kapanis", "olcek_eslem", "kill1_oz_sinama", "kill2_akis_yok", "kill3_olcek",
              "kill4_monoton", "kill5_tek_seans", "kill6_kosul", "kill7_tip", "kill8_pk", "h1", "h2", "n_esigi",
              "gizlilik"):
        assert k in om.PAYDALAR and len(om.PAYDALAR[k]) > 20, k


def test_on_siniflar_ve_erken_kapanis(om):
    girdi = {"planlar": {"P1": [{"entry_trigger": 50.0, "date": "2024-01-31"}],
                         "P4": [{"entry_trigger": 50.0, "date": "2024-07-02"}]},
             "secili": [({"seq": 1}, {"ticker": "aaa", "side": "long", "ts_open": "2024-02-01", "entry": 50.0,
                                      "plan_id": "P1"}),
                        ({"seq": 2}, {"ticker": "HHH", "side": "long", "ts_open": "2024-07-03", "entry": 50.0,
                                      "plan_id": "P4"}),
                        ({"seq": 3}, {"ticker": "BBB", "side": "short", "ts_open": "2024-02-01", "entry": 50.0,
                                      "plan_id": "P1"})]}
    assert [r["sinif"] for r in om.satirlari_hazirla(girdi)] == [None, "erken_kapanis", "yon_disi"]


# ---------------------------------------------------------------------------
# Kopyaların AYRIŞMA ÇİVİLERİ — EDG-102 (yardımcılar) ve EDG-105 (öykünücü, zincir, özet)
# ---------------------------------------------------------------------------
def _tanim_dokumu(kaynak: str, ad: str) -> str | None:
    for d in ast.parse(kaynak).body:
        if isinstance(d, (ast.FunctionDef, ast.ClassDef)) and d.name == ad:
            k = copy.deepcopy(d)
            govde = list(k.body)
            if (govde and isinstance(govde[0], ast.Expr) and isinstance(govde[0].value, ast.Constant)
                    and isinstance(govde[0].value.value, str)):
                govde = govde[1:]
            k.body = govde or [ast.Pass()]
            return ast.dump(k, include_attributes=False)
    return None


ZORUNLU_102 = {"_sayi", "seans_siniri_ns", "seans_suz", "yuzdelik", "seans_kumeli_ci", "_r3", "_dagilim",
               "_fiyat_kovasi", "_db_ac", "_birlestir", "_kanonik", "SemaHatasi", "_sema_kapisi", "_sema_pyarrow",
               "_sema_duckdb", "_oku_pyarrow", "_oku_duckdb", "gun_oku", "bar_dosyasi", "bar_oku", "okuma_sinamasi",
               "_icinde", "_yaz", "_json"}
ZORUNLU_105 = {"limit_ham", "limit_karar", "limit_fiyati", "emir_tipi", "replay_giris", "oz_fark_bps", "acilis_dali",
               "fark_bps", "pencere_ns", "t0_bul", "canli_kural", "seans_kumeli_oran_ci", "karar_h1", "karar_h2",
               "_ikili", "_pk3_satir", "_h1_blok", "_h2_blok", "girdi_oku", "satirlari_hazirla", "bar_alanlari"}


@pytest.mark.parametrize("kaynak,ad_listesi,sabit_listesi,zorunlu", [
    (EDG102, "EDG102_KOPYA_TANIMLAR", "EDG102_KOPYA_SABITLER", ZORUNLU_102),
    (EDG105, "EDG105_KOPYA_TANIMLAR", "EDG105_KOPYA_SABITLER", ZORUNLU_105),
])
def test_kopya_tanimlari_AST_OZDES(om, kaynak, ad_listesi, sabit_listesi, zorunlu):
    assert zorunlu <= set(getattr(om, ad_listesi))
    a, b = BETIK.read_text(encoding="utf-8"), kaynak.read_text(encoding="utf-8")
    for ad in getattr(om, ad_listesi):
        da, db_ = _tanim_dokumu(a, ad), _tanim_dokumu(b, ad)
        assert da is not None and db_ is not None, ad
        assert da == db_, f"{ad} {kaynak.parent.name} betiğinden AYRIŞTI"


def test_kopya_sabitleri_ESIT(om, e102, e105):
    for m, liste in ((e102, om.EDG102_KOPYA_SABITLER), (e105, om.EDG105_KOPYA_SABITLER)):
        for ad in liste:
            assert getattr(om, ad) == getattr(m, ad), ad
    assert {"ERKEN_KAPANIS_GUNLERI", "KARAR_HANE", "KURUS_HANE", "OZ_SINAMA_ALT", "PK2_GAP_ALT"} <= \
        set(om.EDG105_KOPYA_SABITLER)


def test_ayrisma_taramasi_SENTETIK_sapmayi_gorur():
    k = EDG105.read_text(encoding="utf-8")
    sapma = k.replace("bas = t0 + 1", "bas = t0")
    assert sapma != k and _tanim_dokumu(sapma, "canli_kural") != _tanim_dokumu(k, "canli_kural")


def test_EDG102_kopyalari_AYNI_girdide_AYNI_cikti(om, e102, tmp_path):
    g, d = "2024-03-11", dt.date(2024, 3, 11)
    rng = random.Random(551)
    kay = [_kayit(_et(g, "16:00:00"), 50.0), _kayit(_et(g, "09:30:00"), 49.0)]
    for _ in range(200):
        kay.append(_kayit(_et(g, f"{rng.randrange(7, 18):02d}:{rng.randrange(60):02d}:00"), round(rng.uniform(40, 60), 4)))
    assert om.seans_suz(kay, d) == e102.seans_suz(kay, d)
    kumeler = [[rng.gauss(5, 9) for _ in range(rng.randrange(1, 5))] for _ in range(12)]
    assert om.seans_kumeli_ci(kumeler) == e102.seans_kumeli_ci(kumeler)
    yol = tmp_path / "tik" / f"{g}.parquet"
    _parquet_yaz(yol, [(ts, "AAA", p, lot, k, ts, ka, 100, ks, 100) for ts, p, lot, k, ka, ks in kay[:40]])
    assert om.gun_oku(yol, {"AAA", "YOK"}, "duckdb") == e102.gun_oku(yol, {"AAA", "YOK"}, "duckdb")


# ---------------------------------------------------------------------------
# Kaynak metin: meridian İÇE AKTARILMAZ
# ---------------------------------------------------------------------------
def _ithal_kokleri(yol=None) -> set[str]:
    agac = ast.parse((yol or BETIK).read_text(encoding="utf-8"))
    kokler = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            kokler |= {a.name.split(".")[0] for a in d.names}
        elif isinstance(d, ast.ImportFrom):
            assert d.level == 0
            kokler.add(d.module.split(".")[0])
        elif isinstance(d, ast.Call) and getattr(d.func, "id", None) == "__import__":
            kokler.add("__import__")
    return kokler


def test_betik_meridian_ICE_AKTARMAZ_ve_yalniz_stdlib_pyarrow(om):
    kokler = _ithal_kokleri()
    assert "meridian" not in kokler and "__import__" not in kokler and "importlib" not in kokler
    assert kokler <= set(sys.stdlib_module_names) | {"pyarrow", "duckdb"}, kokler
    assert {"pyarrow", "sqlite3", "fractions"} <= kokler and "pandas_market_calendars" not in kokler


def test_ithal_tarayicisi_SENTETIK_ihlali_gorur(tmp_path):
    sahte = tmp_path / "olcum.py"
    sahte.write_text("from meridian import broker\n", encoding="utf-8")
    assert "meridian" in _ithal_kokleri(sahte)


# ---------------------------------------------------------------------------
# Uçtan uca — f = 1 BAYT-ÖZDEŞLİK, ölçekli sahne, monotonluk/parite, gizlilik
# ---------------------------------------------------------------------------
def test_f1_satirlari_EDG105_betigiyle_SATIR_DUZEYINDE_ESIT(om, e105, sandbox_state, tmp_path):
    """Kart: 'f = 1 satırlar EDG-105 ile bayt-özdeş yoldan geçer'. Aynı sentetik girdide (tüm f = 1) iki betik: EDG-105'in
    her satır alanı EDG-106'da AYNI değerle; iki birincil ve (a)–(h) tanıları aynı."""
    sahne = _sahne(tmp_path)
    c105, c106 = tmp_path / "c105", tmp_path / "c106"
    arg = ["--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
           "--okuyucu", "duckdb"]
    assert e105.main(arg + ["--cikti", str(c105)]) == 0 and om.main(arg + ["--cikti", str(c106)]) == 0
    a = json.loads((c105 / "sonuc.json").read_text(encoding="utf-8"))
    b = json.loads((c106 / "sonuc.json").read_text(encoding="utf-8"))
    assert len(a["satirlar"]) == len(b["satirlar"]) == 500 and a["girdi"] == b["girdi"]
    for ra, rb in zip(a["satirlar"], b["satirlar"]):
        assert rb["olcek_f"] == "1"
        for k, v in ra.items():
            assert rb.get(k, "<YOK>") == v, (ra["ticker"], ra["seans"], k)
    for h in ("h1", "h2"):
        for k, v in a["ozet"][h].items():
            assert b["ozet"][h][k] == v, (h, k)
    def _beyansiz(x):
        if isinstance(x, dict):
            return {k: _beyansiz(v) for k, v in x.items() if k != "beyan"}
        return x
    for k, v in a["ozet"]["tanilar"].items():                     # beyan METİNLERİ belgedir, sayılar aynı olmalı
        assert _beyansiz(b["ozet"]["tanilar"][k]) == _beyansiz(v), k
    assert b["ozet"]["kill_list"]["olcek_dislanan_pct"] == 0.0 and b["gizlilik"] == {"h1": False, "h2": False}


def test_uctan_uca_OLCEKLI_sahne_bolunmeli_satirlar_birincilde(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, ekler=SPL)
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    o = s["ozet"]
    assert o["durum"] == "KOSULLU_HUKUM" and o["siniflar"]["DOLAN"] == 500 and o["siniflar"]["DOLMAZ"] == 100
    assert o["siniflar"]["olcek_eslenemez"] == 0 and o["kill_list"]["olcek_dislanan_pct"] == 0.0
    assert abs(o["h1"]["oran_pct"] - 100 / 6) < 1e-9 and o["h1"]["karar"].startswith("REPLAY DOLUMU İYİMSER")
    assert abs(o["h2"]["medyan_bps"] - 12.0) < 1e-9 and o["h2"]["karar"] == "REPLAY GİRİŞ FİYATI İYİMSER"
    spl = [r for r in s["satirlar"] if r["ticker"] == "SPL"]
    onc = [r for r in spl if r["olcek_f"] == "1/10"]
    assert len(onc) == 50 and all(r["sinif"] == "DOLAN" and r["tetik_tik"] == 500.0 and r["limit_tik"] == 520.0
                                  and r["canli_dolum"] == 500.6 and abs(r["fark_bps"] - 12.0) < 1e-9 for r in onc)
    assert s["pk"]["pk3"]["tutarsiz_n"] == 0 and s["pk"]["pk3"]["payda_n"] == 600
    t = o["tanilar"]
    assert t["i_f1_disi_haric"]["n"] == 550 and t["i_f1_disi_haric"]["dolmaz_n"] == 100
    assert t["i_f1_disi_haric"]["dislanan_f1_disi_n"] == 50 and t["i_f1_disi_haric"]["fark_medyan_bps"] == 12.0
    assert t["j_olcek_tablosu"]["ticker_f"] == {"SPL": {"1": 50, "1/10": 50}}
    assert t["j_olcek_tablosu"]["f_dagilimi"] == {"1": 550, "1/10": 50}
    assert o["kill_list"]["monotonluk_ihlali_tickerlar"] == []


def _gizlilik_denetimi(s: dict, md: str, stdout: str) -> None:
    metin = json.dumps(s, ensure_ascii=False)
    assert '"fark_bps"' not in metin and '"canli_dolum"' not in metin and '"t930_fark_bps"' not in metin
    assert all(r["sinif"] not in ("DOLAN", "DOLMAZ") for r in s["satirlar"])
    assert {"DOLAN", "DOLMAZ"}.isdisjoint(s["ozet"]["siniflar"]) and s["ozet"]["dolmaz_nedenleri"] is None
    assert "dolmaz_n" not in s["ozet"]["h1"] and s["ozet"]["h1"]["gizli"] is True and "n" not in s["ozet"]["h2"]
    assert s["ozet"]["tanilar"] is None and s["pk"]["pk2"]["ornekler"] == []
    assert not re.search(r"DOLAN\s*=\s*\d|DOLMAZ\s*=\s*\d|dolmaz_n|dolan_n", md)
    assert not re.search(r"DOLAN\s*=\s*\d|DOLMAZ\s*=\s*\d|dolmaz_n|dolan_n|fark=", stdout)
    assert "GİZLİ" in md and "GİZLİ" in stdout


def test_YAYIMLANMAZ_iken_satir_sonuclari_ve_DOLAN_DOLMAZ_sayilari_YAZILMAZ_BASILMAZ(om, sandbox_state, tmp_path,
                                                                                   capsys):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    (sahne["tick"] / f"{sahne['gunler'][2]}.parquet").unlink()
    capsys.readouterr()
    assert _kos(om, sahne, "--elle-ornek", "6") == 0
    out = capsys.readouterr().out
    s = _sonuc(sahne)
    assert s["ozet"]["durum"] == "YAYIMLANMAZ" and s["gizlilik"]["h1"] is True and s["gizlilik"]["h2"] is True
    assert s["ozet"]["birincil_aday_n"] == 25 and s["ozet"]["siniflar"]["akis_yok"] == 5
    assert "kill-2" in out
    _gizlilik_denetimi(s, (sahne["cikti"] / "OZET.md").read_text(encoding="utf-8"), out)


def test_OLCULEMEDI_iken_de_GIZLI_yayimlanirken_ACIK(om, sandbox_state, tmp_path, capsys):
    sahne = _sahne(tmp_path / "k", gun_sayisi=6)
    capsys.readouterr()
    assert _kos(om, sahne) == 0
    out = capsys.readouterr().out
    s = _sonuc(sahne)
    assert s["ozet"]["durum"] == "OLCULEMEDI" and s["ozet"]["birincil_aday_n"] == 30
    _gizlilik_denetimi(s, (sahne["cikti"] / "OZET.md").read_text(encoding="utf-8"), out)
    acik = _sahne(tmp_path / "b")
    assert _kos(om, acik) == 0
    s = _sonuc(acik)
    assert s["gizlilik"] == {"h1": False, "h2": False} and s["ozet"]["siniflar"]["DOLAN"] == 400
    assert '"fark_bps"' in json.dumps(s) and s["ozet"]["h1"]["dolmaz_n"] == 100


def test_yayim_gorunumu_H1_gizliyken_H2_sayisi_da_GIZLI(om):
    """Sözleşme: H1 yayımlanmıyorsa H2'nin n'i (DOLAN sayısı) birincil_aday_n ile DOLMAZ'ı ele verir → H2 de gizlenir.
    (`ozetle` bugün bu durumu üretemez — H1 paydası H2'yi kapsar — ama görünüm katmanı kendi başına güvenli olmalı.)"""
    ozet = om.ozetle(_ozet_satirlari(300, 50, 100), _OZ, _PK1)
    ozet = dict(ozet, h1=dict(ozet["h1"], durum="OLCULEMEDI"))
    oz, satirlar, pk2, g = om.yayim_gorunumu(ozet, [], {"istenen": 0, "ornekler": []})
    assert g == {"h1": True, "h2": True} and oz["h2"]["gizli"] is True and "n" not in oz["h2"]
    assert oz["birincil_aday_n"] == 350 and "DOLAN" not in oz["siniflar"]


def test_uctan_uca_MONOTONLUK_ve_PARITE_siniflari(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=8, yalniz={"AAA"}, ekler=ZIG_PAR)
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    zig = {r["seans"]: r for r in s["satirlar"] if r["ticker"] == "ZIG"}
    for i, g in enumerate(sahne["gunler"]):
        if ZIG_DESEN[i] != 1:
            assert zig[g]["sinif"] == "olcek_eslenemez" and zig[g]["olcek_alt_neden"] == "monotonluk_ihlali"
            assert zig[g]["olcek_f"] == "1/2"
        else:
            assert zig[g]["sinif"] == "BIRINCIL_GIZLI"          # yayımlanmayan durumda DOLAN/DOLMAZ maskeli
    par = [r for r in s["satirlar"] if r["ticker"] == "PAR"]
    assert all(r["sinif"] == "olcek_parite_disi" and r["olcek_alt_neden"] == "kapanis_tetik" for r in par)
    kl = s["ozet"]["kill_list"]
    assert kl["monotonluk_ihlali_tickerlar"] == ["ZIG"] and kl["olcek_eslenemez_n"] == 3
    assert kl["olcek_parite_disi_n"] == 8 and kl["olcek_asimi"] is True and s["ozet"]["durum"] == "YAYIMLANMAZ"


def test_kill6_birincil_KOSULDAN_bagimsiz(om, sandbox_state, tmp_path):
    a = _sahne(tmp_path / "a", kosul=0)
    b = _sahne(tmp_path / "b", kosul=0x20)
    assert _kos(om, a) == 0 and _kos(om, b) == 0
    sa, sb = _sonuc(a), _sonuc(b)
    for k in ("h1", "h2", "siniflar"):
        assert sa["ozet"][k] == sb["ozet"][k], k
    assert sb["ozet"]["tanilar"]["e_kosul_0x20_disi"]["n"] == 0 and sa["ozet"]["kill_list"]["kosul_birincilde"] is False


def test_erken_kapanis_gunu_girisleri_DISLANIR(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6, bas="2024-07-01")
    assert _kos(om, sahne) == 0
    o = _sonuc(sahne)["ozet"]
    assert o["siniflar"]["erken_kapanis"] == 5 and o["n_aday"] == 25 and o["birincil_aday_n"] == 25


def test_yazim_YALNIZ_cikti_altinda_ve_KORUMALAR(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    once = _agac_fotografi(tmp_path, sahne["cikti"])
    assert _kos(om, sahne) == 0
    assert _agac_fotografi(tmp_path, sahne["cikti"]) == once
    assert sorted(p.name for p in sahne["cikti"].rglob("*") if p.is_file()) == sorted(om.CIKTI_DOSYALARI)
    assert _kos(om, sahne) == 2                                   # var olan sonucun üstüne yazılmaz
    for icerisi in (sahne["state"] / "olcum", sahne["tick"].parent / "x", sahne["bars"] / "y"):
        sahne["cikti"] = icerisi
        assert _kos(om, sahne) == 2 and not icerisi.exists()


def test_girdi_dokumu_sha256_ve_parmak_izi_KARARLI(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    sahne["cikti"] = tmp_path / "c1"
    assert _kos(om, sahne) == 0
    s1 = _sonuc(sahne)
    sahne["cikti"] = tmp_path / "c2"
    assert _kos(om, sahne) == 0
    s2 = _sonuc(sahne)
    assert s1["girdi"] == s2["girdi"] and s1["parmak_izi"] == s2["parmak_izi"]
    assert hashlib.sha256((tmp_path / "c1" / "girdi_trades.json").read_bytes()).hexdigest() == s1["girdi"]["trades_sha256"]


def test_elle_ornek_KOTALI_f1_disi_satir_dahil_ve_parmak_izi_AYNI(om, sandbox_state, tmp_path):
    a = _sahne(tmp_path / "a", ekler=SPL)
    b = _sahne(tmp_path / "b", ekler=SPL)
    assert _kos(om, a, "--elle-ornek", "7") == 0 and _kos(om, b, "--elle-ornek", "7") == 0
    pa, pb = _sonuc(a)["pk"]["pk2"], _sonuc(b)["pk"]["pk2"]
    oa = pa["ornekler"]
    assert len(oa) == 7 and pa["kota_karsilandi"] is True
    assert [(x["ticker"], x["seans"]) for x in oa] == [(x["ticker"], x["seans"]) for x in pb["ornekler"]]
    assert sum(1 for x in oa if x["dal"] == "GAP") >= 4 and any(x["dal"] == "STOP_LIMIT" for x in oa)
    assert any(x["sinif"] == "DOLMAZ" for x in oa) and any(x["olcek_f"] != "1" for x in oa)
    for x in oa:
        rol = {k["rol"]: k for k in x["dilim"] if k["rol"]}
        if x["sinif"] == "DOLAN":
            assert rol["dolum"]["fiyat"] == x["canli_dolum"] <= x["limit_tik"]
    iz = _sonuc(b)["parmak_izi"]
    a["cikti"] = tmp_path / "a" / "tam"
    assert _kos(om, a) == 0 and _sonuc(a)["parmak_izi"] == iz


def test_PK2_kotasi_SANSA_birakilmaz_f1_disi_dahil(om, tmp_path, monkeypatch):
    gunler = _is_gunleri("2024-02-01", 30)
    s = []
    for i in range(28):
        s.append({"sinif": "DOLAN", "dal": "GAP", "seans": gunler[i], "ticker": "G", "seq": i, "_f": F(1)})
        s.append({"sinif": "DOLAN", "dal": "STOP_LIMIT", "seans": gunler[i], "ticker": "S", "seq": 100 + i, "_f": F(1)})
    s.append({"sinif": "DOLMAZ", "dal": "GAP", "seans": gunler[5], "ticker": "D", "seq": 999, "_f": F(1)})
    s.append({"sinif": "DOLAN", "dal": "STOP_LIMIT", "seans": gunler[7], "ticker": "X", "seq": 998, "_f": F(1, 10)})
    for tohum in range(25):
        monkeypatch.setattr(om, "BOOT_TOHUM", tohum)
        p = om.pk2_ornekler(s, 7, tmp_path)
        secim = [x["ticker"] for x in p["ornekler"]]
        assert len(secim) == 7 and p["kota_karsilandi"] is True, tohum
        assert secim.count("D") == 1 and secim.count("X") == 1 and secim.count("G") >= 4, tohum
    assert om.pk2_ornekler(s, 3, tmp_path)["kota_karsilandi"] is False


def test_kuru_kip_OLCEK_dagilimi_monotonluk_ve_beklenen_kill3(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=8, yalniz={"AAA"}, ekler=ZIG_PAR)
    assert _kos(om, sahne, "--kuru") == 0
    k = json.loads((sahne["cikti"] / "kuru.json").read_text(encoding="utf-8"))
    assert k["kip"] == "kuru" and k["aday_n"] == 24 and k["seans_n"] == 8
    assert k["olcek"]["f_dagilimi"] == {"1": 21, "1/2": 3}
    assert k["olcek"]["olcek_eslenemez_n"] == 3 and k["olcek"]["olcek_parite_disi_n"] == 8
    assert k["olcek"]["monotonluk_ihlali_tickerlar"] == ["ZIG"] and k["olcek"]["akis_yok_n"] == 0
    assert k["olcek"]["kill3_payi_pct"] == 45.833 and k["olcek"]["kill3_pay_payda"] == [11, 24]
    assert k["olcek"]["olcek_uygun_n"] == 13                     # kuru adımda öykünücü KOŞMAZ: DOLAN/DOLMAZ doğmaz
    assert k["olcek"]["adim0_beklenen"] == {"pay": 4, "payda": 836, "pct": 0.478}
    assert k["okuma_sinamasi"]["gun"] == sahne["gunler"][0] and k["plan_tipi_dagilimi"]["GAP"] == 24
    metin = (sahne["cikti"] / "kuru.json").read_text(encoding="utf-8")
    assert '"DOLAN"' not in metin and '"fark_bps"' not in metin and not (sahne["cikti"] / "sonuc.json").exists()
    assert sorted(p.name for p in sahne["cikti"].rglob("*") if p.is_file()) == sorted(om.KURU_DOSYALARI)


def test_CLI_dosya_kipi_operatorun_kosacagi_bicimde(sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    p = subprocess.run([sys.executable, str(BETIK), "--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]),
                        "--bar-kok", str(sahne["bars"]), "--cikti", str(sahne["cikti"]), "--okuyucu", "duckdb"],
                       capture_output=True, text=True, timeout=300, cwd=str(tmp_path))
    assert p.returncode == 0, p.stderr[-2000:]
    s = _sonuc(sahne)
    assert s["kart"] == "EDG-2026-106" and s["arac"]["kip"] == "dosya"
    assert s["arac"]["betik_sha256"] == hashlib.sha256(BETIK.read_bytes()).hexdigest() and "H1" in p.stdout


def _stdin_kos(*args, cwd="/"):
    return subprocess.run([sys.executable, "-", *args], input=BETIK.read_bytes(), cwd=cwd, capture_output=True,
                          timeout=300)


def test_stdin_kipi_ARGV_ayrisir_ve_sha_BEYANI(sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    sha = hashlib.sha256(BETIK.read_bytes()).hexdigest()
    r = _stdin_kos("--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                   "--cikti", str(sahne["cikti"]), "--okuyucu", "duckdb", "--elle-ornek", "6", "--betik-sha256", sha)
    assert r.returncode == 0, r.stderr.decode()[-2000:]
    s = _sonuc(sahne)
    assert s["arac"]["kip"] == "stdin" and s["arac"]["betik_sha256"] is None and s["arac"]["betik_sha256_beyan"] == sha
    assert s["pk"]["pk2"]["istenen"] == 6
    r = _stdin_kos("--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                   "--cikti", str(tmp_path / "yeni"), "--okuyucu", "duckdb")
    assert r.returncode == 2 and b"--betik-sha256" in r.stdout and not (tmp_path / "yeni").exists()
    assert _stdin_kos("--help").returncode == 0


def test_dosya_kipi_YANLIS_sha_beyani_reddedilir(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=6)
    assert _kos(om, sahne, "--betik-sha256", "0" * 64) == 2 and _kos(om, sahne, "--betik-sha256", "kisa") == 2
    assert _kos(om, sahne, "--betik-sha256", hashlib.sha256(BETIK.read_bytes()).hexdigest()) == 0
