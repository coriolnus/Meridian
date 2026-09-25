"""test_edg102_stop_kayma_v546.py — EDG-2026-102 (TSK-221): replay stop çıkışlarının GERÇEK kayması
ölçüm betiğinin çivileri (`research/olcumler/edg102_stop_kayma/olcum.py`).

KART: research/cards/EDG-2026-102-replay-stop-kaymasi-tick.yaml — eşik, kill-list ve pozitif kontrol
ORADA donuktur; bu dosya betiğin karta SADAKATİNİ ölçer, kartı değil.

NE ÖLÇÜLÜR (kartın ve briefin çivi listesi):
  * PK-1 KİMLİK — dokunuştan sonraki fiyat = eff_stop → 0 bps; bilinen 12 bps enjeksiyonu TAM çıkar
    (birim çekirdekte VE CLI uçtan uca).
  * seans süzgeci ET 09:30 ≤ t < 16:00, DST-farkında (Mart/Kasım sınırları).
  * `dokunus_yok` / `sonraki_yok` sınıfları medyana GİRMEZ, sayılır.
  * seans-kümeli bootstrap deterministik ve EDG-2026-042'nin (`betimleyici`) yöntemiyle BİREBİR.
  * karar kuralı üç dalı + sınırlar; kill-list dalları (dokunuş_yok %20, tek seans %10, öz-sınama 20).
  * eff_stop formülü MOTORLA aynı: satırlar gerçek motor yoluyla üretilir (Position → _touch_exit →
    close_position) ve betik o satırdan eff_stop'u geri kurar.
  * betik `meridian` İÇE AKTARMAZ (kaynak metin/AST çivisi); yalnız stdlib + pyarrow (+ açıkça seçilen
    duckdb okuyucusu).
  * yazım YALNIZ `--cikti` altında; girdi ağacı bayt-özdeş kalır.
  * birincil kestirim `kosul` alanından BAĞIMSIZ (kill-list 4); tanı (a) ona bağlı.

PARQUET NEDEN DUCKDB İLE YAZILIR: bu venv'de pyarrow YOK (ölçüldü 2026-09-25: `import pyarrow` →
ModuleNotFoundError; v506 aynı gerekçeyle DuckDB COPY kullanır). Sentetik dosya pilotun şemasını
(`research/olcumler/edg066_tick_arsiv/pilot.py` → `ayristir`) BİREBİR tiplerle taşır; CLI yerelde
`--okuyucu duckdb` ile koşar. A1 sözleşmesinin pyarrow okuyucusu burada KOŞMAZ — bu bir kapsam
sınırıdır ve betiğin `--kuru` adımı A1'de onu ilk iş olarak sınar (devir raporunda).

Test adlarında sonuç jetonları (büyük harfli başarısızlık/hata sözcükleri) BİLEREK kullanılmaz
(CLAUDE.md §6: ad grep'i kirletir).
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import pathlib
import random
import re
import sqlite3
import subprocess
import sys

import duckdb
import pytest
import yaml

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "research" / "olcumler" / "edg102_stop_kayma" / "olcum.py"
KART = REPO / "research" / "cards" / "EDG-2026-102-replay-stop-kaymasi-tick.yaml"
GOAL = REPO / "state" / "goal.yaml"
EDG042 = REPO / "research" / "olcumler" / "edg042_kosum_2026-09-24" / "olcum.py"

NS = 1_000_000_000
UTC = dt.timezone.utc


@pytest.fixture(scope="module")
def om():
    """Ölçüm betiği — KAYNAKTAN derlenmiş modül (ham exec_module yasağı v334)."""
    return betikten_modul_yukle(BETIK, "edg102_olcum")


# ---------------------------------------------------------------------------
# sentetik sahne kurucuları
# ---------------------------------------------------------------------------
def _ns(gun: str, saat: str, tz=UTC) -> int:
    """`gun` + `saat` (HH:MM:SS) → epoch ns; tz varsayılanı UTC."""
    t = dt.datetime.fromisoformat(f"{gun}T{saat}").replace(tzinfo=tz)
    return int(t.timestamp()) * NS


def _et(gun: str, saat: str) -> int:
    """New York duvar saatinden epoch ns — test tarafı zoneinfo'yu KENDİSİ kullanır."""
    from zoneinfo import ZoneInfo
    return _ns(gun, saat, ZoneInfo("America/New_York"))


def _kayit(ts, fiyat_dolar, kosul=0, alis=None, satis=None, lot=100):
    """Betiğin kayıt biçimi: (ts, fiyat[1e-4 tamsayı], lot, kosul, k_alis, k_satis)."""
    def _i(x):
        return None if x is None else int(round(x * 10_000))
    return (ts, _i(fiyat_dolar), lot, kosul, _i(alis), _i(satis))


def _is_gunleri(bas: str, adet: int) -> list[str]:
    g = dt.date.fromisoformat(bas)
    out = []
    while len(out) < adet:
        if g.weekday() < 5:
            out.append(g.isoformat())
        g += dt.timedelta(days=1)
    return out


def _motor_satiri(ticker: str, gun: str, stop: float, trail: float | None = None) -> dict:
    """Stop çıkış satırını GERÇEK motor yoluyla üretir: Position → _touch_exit → close_position.
    Betik bu satırdan eff_stop'u GERİ kurmak zorundadır — formül kopyası değil, motorun kendisi."""
    from meridian import broker as B
    br = B.PaperBroker(100_000.0, 5.0, 0.0)
    giris = round(stop * 1.05, 4)
    pos = B.Position(plan_id=f"P-{gun}-{ticker}", ticker=ticker, side="long", entry=giris,
                     stop=stop, trail_stop=(trail if trail is not None else stop),
                     target=round(max(stop, trail or 0.0) * 1.5, 4), qty=100,
                     r_per_share=giris - stop,
                     risk_dollars=100 * (giris - stop), size_r=1.0, ts_open=gun, qty_taban=100)
    br.positions[ticker] = pos
    eff = max(stop, trail if trail is not None else stop)
    ex = br._touch_exit(pos, {"open": eff * 1.01, "high": eff * 1.02, "low": eff * 0.99})
    assert ex is not None and ex[1] == "stop"
    satir = br.close_position(ticker, ex[0], ex[1], gun)
    satir["kaynak"] = "replay_seed"
    return satir


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
    """Pilotun `islem/` şemasıyla (`pilot.ayristir` ty yazıcısı, tipler birebir) parquet yazar.
    satırlar: (ts, sembol, fiyat, lot, kosul, k_ts, k_alis_fiyat, k_alis_lot, k_satis_fiyat, k_satis_lot)."""
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
    """Bar CSV'si — motorun biçimi (`date,open,high,low,close,volume`, ad küçük harf, '.'→'-')."""
    kok.mkdir(parents=True, exist_ok=True)
    yol = kok / f"{ticker.lower().replace('.', '-')}.csv"
    satir = ["date,open,high,low,close,volume"]
    for g in sorted(barlar):
        o, h, l, c = barlar[g]
        satir.append(f"{g},{o},{h},{l},{c},1000000.0")
    yol.write_text("\n".join(satir) + "\n", encoding="utf-8")


def _gun_tikleri(gun: str, sembol: str, stop: float, dolum: float, kosul: int = 0,
                 dokunus: bool = True, sonraki: bool = True) -> list[tuple]:
    """Bir sembolün bir günlük tik akışı. Seans ÖNCESİ bir kayıt stop'un ALTINDADIR — seans süzgeci
    çalışmıyorsa o kayıt sahte dokunuş üretir (DST çivisinin uçtan uca ikizi)."""
    def p(x):
        return int(round(x * 10_000))
    on = _et(gun, "08:00:00")
    s = [(on, sembol, p(stop * 0.97), 100, kosul, on, p(stop * 0.969), 100, p(stop * 0.971), 100)]
    t0 = _et(gun, "10:00:00")
    s.append((t0, sembol, p(stop + 0.10), 100, kosul, t0, p(stop + 0.09), 100, p(stop + 0.11), 100))
    if dokunus:
        t1 = _et(gun, "10:00:01")
        s.append((t1, sembol, p(stop), 100, kosul, t1, p(stop - 0.01), 100, p(stop + 0.01), 100))
        if sonraki:
            t2 = _et(gun, "10:00:02")
            s.append((t2, sembol, p(dolum), 100, kosul, t2, p(dolum - 0.01), 100,
                      p(dolum + 0.01), 100))
            t3 = _et(gun, "11:00:00")
            s.append((t3, sembol, p(stop + 0.05), 100, kosul, t3, p(stop + 0.04), 100,
                      p(stop + 0.06), 100))
    else:
        t3 = _et(gun, "11:00:00")
        s.append((t3, sembol, p(stop + 0.05), 100, kosul, t3, p(stop + 0.04), 100,
                  p(stop + 0.06), 100))
    return s


def _sahne(tmp_path, *, gun_sayisi=60, enjeksiyon_bps=12.0, kosul=0, ek_siniflar=False,
           plan_yaz=True) -> dict:
    """Uçtan uca sahne: `gun_sayisi` seans × 2 sembol stop çıkışı (hepsi sert stop, plan kayıtlı),
    tik dolumu eff_stop × (1 − enjeksiyon) — yani her satırın gerçek kayması TAM `enjeksiyon_bps`.
    Stoplar 0,25$ ızgarasındadır: eff_stop × 12e-4 1e-4 ızgarasına düşer, 12 bps TAM temsil edilir.
    ek_siniflar=True: bir `dokunus_yok` + bir `sonraki_yok` satırı + gürültü satırları (canlı kaynak,
    başka çıkış nedeni) eklenir."""
    kok = tmp_path / "sahne"          # sandbox_state'in tmp_path/state'i ile karışmasın
    state = kok / "state"
    tick = kok / "veri" / "tick" / "islem"
    bars = state / "bars"
    gunler = _is_gunleri("2024-02-01", gun_sayisi)
    islemler, planlar = [], []
    gun_tik: dict[str, list] = {g: [] for g in gunler}
    bar_ser: dict[str, dict] = {"AAA": {}, "BBB": {}, "CCC": {}, "DDD": {}}
    for i, g in enumerate(gunler):
        for j, sym in enumerate(("AAA", "BBB")):
            stop = 40.0 + 0.25 * ((i * 2 + j) % 80)
            satir = _motor_satiri(sym, g, stop)
            islemler.append(satir)
            planlar.append({"id": satir["plan_id"], "date": g, "ticker": sym, "side": "long",
                            "stop": stop, "entry_trigger": round(stop * 1.05, 4)})
            dolum = round(stop * (1.0 - enjeksiyon_bps / 10_000.0), 4)
            gun_tik[g] += _gun_tikleri(g, sym, stop, dolum, kosul=kosul)
            bar_ser[sym][g] = (round(stop * 1.01, 2), round(stop * 1.02, 2),
                               round(stop * 0.99, 2), round(stop + 0.05, 4))
    if ek_siniflar:
        g0, g1 = gunler[0], gunler[1]
        for sym, g, dok, son in (("CCC", g0, False, True), ("DDD", g1, True, False)):
            stop = 30.0
            satir = _motor_satiri(sym, g, stop)
            islemler.append(satir)
            planlar.append({"id": satir["plan_id"], "date": g, "ticker": sym, "side": "long",
                            "stop": stop})
            gun_tik[g] += _gun_tikleri(g, sym, stop, stop, kosul=kosul, dokunus=dok, sonraki=son)
            bar_ser[sym][g] = (30.3, 30.6, 29.7, 30.05)
        # gürültü: canlı kaynaklı stop + tohumun hedef çıkışı — ikisi de girdiye GİRMEZ
        canli = _motor_satiri("AAA", gunler[2], 41.0)
        canli["kaynak"] = "live_paper"
        hedef = dict(_motor_satiri("BBB", gunler[3], 42.0), exit_reason="target")
        islemler += [canli, hedef]
    _db_yaz(state / "meridian.db", islemler, planlar if plan_yaz else [])
    for g, s in gun_tik.items():
        _parquet_yaz(tick / f"{g}.parquet", s)
    for sym, ser in bar_ser.items():
        if ser:
            _bar_yaz(bars, sym, ser)
    return {"db": state / "meridian.db", "tick": tick, "bars": bars, "cikti": kok / "cikti",
            "gunler": gunler, "state": state}


def _kos(om, sahne, *ek) -> int:
    return om.main(["--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]),
                    "--bar-kok", str(sahne["bars"]), "--cikti", str(sahne["cikti"]),
                    "--okuyucu", "duckdb", *ek])


def _sonuc(sahne) -> dict:
    return json.loads((sahne["cikti"] / "sonuc.json").read_text(encoding="utf-8"))


def _agac_fotografi(kok: pathlib.Path, haric: pathlib.Path) -> dict:
    """`kok` altındaki her dosya → (boyut, sha256); `haric` altı dışarıda."""
    out = {}
    for p in sorted(kok.rglob("*")):
        if p.is_file() and haric not in p.parents:
            out[str(p.relative_to(kok))] = (p.stat().st_size,
                                            hashlib.sha256(p.read_bytes()).hexdigest())
    return out


# ---------------------------------------------------------------------------
# PK-1 KİMLİK — çekirdek
# ---------------------------------------------------------------------------
def test_PK1_kimlik_dolum_eff_stopa_esitse_kayma_SIFIR(om):
    g = "2024-05-15"
    kay = [_kayit(_et(g, "10:00:00"), 50.30), _kayit(_et(g, "10:00:01"), 50.00),
           _kayit(_et(g, "10:00:02"), 50.00)]
    r = om.dokunus_ve_dolum(om.seans_suz(kay, dt.date.fromisoformat(g)), 50.0)
    assert r["sinif"] == "olculdu"
    assert r["kayma_bps"] == 0.0


def test_PK1_bilinen_12_bps_enjeksiyonu_TAM_cikar(om):
    g = "2024-05-15"
    kay = [_kayit(_et(g, "10:00:00"), 50.30), _kayit(_et(g, "10:00:01"), 50.00),
           _kayit(_et(g, "10:00:02"), 49.94), _kayit(_et(g, "10:00:03"), 49.00)]
    r = om.dokunus_ve_dolum(om.seans_suz(kay, dt.date.fromisoformat(g)), 50.0)
    assert r["sinif"] == "olculdu"
    assert r["dokunus_i"] == 1 and r["dolum_i"] == 2
    assert r["tick_fill"] == 49.94
    assert abs(r["kayma_bps"] - 12.0) < 1e-9


def test_PK1_dokunus_ILK_esik_alti_kayittir_sonraki_degil(om):
    """İlk `fiyat ≤ eff_stop` dokunuştur; daha derin sonraki kayıtlar dokunuşu KAYDIRMAZ."""
    g = "2024-05-15"
    kay = [_kayit(_et(g, "10:00:00"), 49.99), _kayit(_et(g, "10:00:01"), 49.80),
           _kayit(_et(g, "10:00:02"), 49.50)]
    r = om.dokunus_ve_dolum(om.seans_suz(kay, dt.date.fromisoformat(g)), 50.0)
    assert r["dokunus_i"] == 0 and r["tick_fill"] == 49.80


def test_PK1_calisma_ani_oz_kontrolu_gecer(om):
    """Betik gerçek veriye dokunmadan ÖNCE aynı kodla kimlik PK'sını koşar (A1'de de)."""
    r = om.pk1_kimlik()
    assert r["gecti"] is True
    assert r["kimlik_bps"] == 0.0 and abs(r["enjeksiyon_bps"] - 12.0) < 1e-9


# ---------------------------------------------------------------------------
# Seans süzgeci — DST
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("gun,acilis_utc", [
    ("2024-03-08", "14:30:00"),   # EST (DST öncesi cuma)
    ("2024-03-11", "13:30:00"),   # EDT (DST sonrası pazartesi)
    ("2024-11-01", "13:30:00"),   # EDT (DST bitişi öncesi cuma)
    ("2024-11-04", "14:30:00"),   # EST (DST bitişi sonrası pazartesi)
])
def test_seans_siniri_DST_farkinda(om, gun, acilis_utc):
    acilis, kapanis = om.seans_siniri_ns(dt.date.fromisoformat(gun))
    assert acilis == _ns(gun, acilis_utc)
    assert kapanis - acilis == int(6.5 * 3600) * NS


def test_seans_suzgeci_Mart_DST_ayni_UTC_saat_iki_farkli_hukum(om):
    """13:45Z: DST öncesi cuma 08:45 EST (seans DIŞI), DST sonrası pazartesi 09:45 EDT (seans İÇİ)."""
    for gun, beklenen in (("2024-03-08", 0), ("2024-03-11", 1)):
        kay = [_kayit(_ns(gun, "13:45:00"), 49.0)]
        assert len(om.seans_suz(kay, dt.date.fromisoformat(gun))) == beklenen, gun


def test_seans_suzgeci_Kasim_DST_ayni_UTC_saat_iki_farkli_hukum(om):
    """13:45Z: 2024-11-01 09:45 EDT (İÇİ), 2024-11-04 08:45 EST (DIŞI)."""
    for gun, beklenen in (("2024-11-01", 1), ("2024-11-04", 0)):
        kay = [_kayit(_ns(gun, "13:45:00"), 49.0)]
        assert len(om.seans_suz(kay, dt.date.fromisoformat(gun))) == beklenen, gun


def test_seans_acilis_DAHIL_kapanis_HARIC(om):
    g = "2024-07-10"
    kay = [_kayit(_et(g, "09:29:59"), 1.0), _kayit(_et(g, "09:30:00"), 2.0),
           _kayit(_et(g, "15:59:59"), 3.0), _kayit(_et(g, "16:00:00"), 4.0)]
    fiyatlar = [r[1] for r in om.seans_suz(kay, dt.date.fromisoformat(g))]
    assert fiyatlar == [20_000, 30_000]


def test_seans_suzgeci_esit_zamanda_DOSYA_SIRASINI_korur(om):
    g = "2024-07-10"
    t = _et(g, "10:00:00")
    kay = [_kayit(t + 5, 10.0), _kayit(t, 11.0), _kayit(t, 12.0), _kayit(t, 13.0)]
    assert [r[1] for r in om.seans_suz(kay, dt.date.fromisoformat(g))] == [
        110_000, 120_000, 130_000, 100_000]


# ---------------------------------------------------------------------------
# Sınıflar: dokunus_yok / sonraki_yok medyana GİRMEZ
# ---------------------------------------------------------------------------
def test_dokunus_yok_ve_sonraki_yok_siniflari(om):
    g = dt.date(2024, 5, 15)
    ust = [_kayit(_et(g.isoformat(), "10:00:00"), 50.2), _kayit(_et(g.isoformat(), "10:00:01"), 50.1)]
    assert om.dokunus_ve_dolum(om.seans_suz(ust, g), 50.0)["sinif"] == "dokunus_yok"
    son = [_kayit(_et(g.isoformat(), "10:00:00"), 50.2), _kayit(_et(g.isoformat(), "10:00:01"), 49.9)]
    r = om.dokunus_ve_dolum(om.seans_suz(son, g), 50.0)
    assert r["sinif"] == "sonraki_yok" and r["kayma_bps"] is None
    assert om.dokunus_ve_dolum([], 50.0)["sinif"] == "dokunus_yok"


def _ozet_satirlari(n_olc, n_seans, kayma=12.0, n_dokunus_yok=0, n_sonraki_yok=0,
                    buyuk_seans=0, kayma_fn=None):
    """`ozetle` girdisi: n_olc ölçülmüş satır n_seans seansa dağıtılır; `buyuk_seans` > 0 ise ilk
    seans o kadar EK satır taşır."""
    satirlar = []
    gunler = _is_gunleri("2023-01-02", n_seans)
    for i in range(n_olc):
        k = kayma_fn(i) if kayma_fn else kayma
        satirlar.append({"sinif": "olculdu", "seans": gunler[i % n_seans], "kayma_bps": k,
                         "eff_stop": 50.0, "ticker": f"T{i}"})
    for i in range(buyuk_seans):
        satirlar.append({"sinif": "olculdu", "seans": gunler[0], "kayma_bps": kayma,
                         "eff_stop": 50.0, "ticker": f"B{i}"})
    for i in range(n_dokunus_yok):
        satirlar.append({"sinif": "dokunus_yok", "seans": gunler[i % n_seans], "kayma_bps": None,
                         "alt_neden": "fiyat_esige_inmedi", "eff_stop": 50.0, "ticker": f"D{i}"})
    for i in range(n_sonraki_yok):
        satirlar.append({"sinif": "sonraki_yok", "seans": gunler[i % n_seans], "kayma_bps": None,
                         "eff_stop": 50.0, "ticker": f"S{i}"})
    return satirlar


_OZ_GECTI = {"gecti": True}
_PK1_GECTI = {"gecti": True}


def test_dokunus_yok_ve_sonraki_yok_MEDYANA_girmez(om):
    s = _ozet_satirlari(110, 55, kayma=7.0, n_dokunus_yok=10, n_sonraki_yok=3)
    for x in s:
        if x["sinif"] != "olculdu":
            x["kayma_bps"] = 999.0     # medyana sızarsa değeri sürükler
    o = om.ozetle(s, _OZ_GECTI, _PK1_GECTI)
    assert o["n_olculen"] == 110
    assert o["siniflar"]["dokunus_yok"] == 10 and o["siniflar"]["sonraki_yok"] == 3
    assert o["medyan_bps"] == 7.0


# ---------------------------------------------------------------------------
# Bootstrap — deterministik ve EDG-042 ile BİREBİR
# ---------------------------------------------------------------------------
def _rastgele_kumeler(tohum=7, n_seans=14, n=45):
    rng = random.Random(tohum)
    gunler = _is_gunleri("2024-01-02", n_seans)
    satirlar = [{"ticker": f"X{i}", "tarih": gunler[rng.randrange(n_seans)],
                 "bps": round(rng.gauss(6.0, 9.0), 3)} for i in range(n)]
    kumeler: dict[str, list] = {}
    for r in satirlar:
        kumeler.setdefault(r["tarih"], []).append(r["bps"])
    return satirlar, list(kumeler.values())


def test_bootstrap_ayni_tohum_AYNI_CI(om):
    _, kumeler = _rastgele_kumeler()
    a = om.seans_kumeli_ci(kumeler, om.BOOT_B, om.BOOT_TOHUM)
    b = om.seans_kumeli_ci(kumeler, om.BOOT_B, om.BOOT_TOHUM)
    assert a == b
    c = om.seans_kumeli_ci(kumeler, om.BOOT_B, om.BOOT_TOHUM + 1)
    assert c != a     # tohum gerçekten kullanılıyor (sabit çıktı değil)


def test_bootstrap_EDG042_betimleyici_ile_BIREBIR(om):
    """Kart: 'seans-kümeli bootstrap B=5000, seed=20260812 (EDG-040/042/045 künyesi)'. Canlı ikizi
    EDG-042 K3'ün uygulaması (`betimleyici`) — aynı girdi, aynı kümeleme sırası → aynı CI."""
    e42 = betikten_modul_yukle(EDG042, "edg042_kosum_0924")
    satirlar, kumeler = _rastgele_kumeler()
    ref = e42.betimleyici(satirlar, "cikis_stop", 5.0)["ci"]
    alt, ust = om.seans_kumeli_ci(kumeler, om.BOOT_B, om.BOOT_TOHUM)
    assert (round(alt, 3), round(ust, 3)) == (ref["alt"], ref["ust"])
    assert (e42.B, e42.SEED) == (om.BOOT_B, om.BOOT_TOHUM)


def test_yuzdelik_lineer_interpolasyon(om):
    assert om.yuzdelik([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    assert om.yuzdelik([0.0, 10.0], 0.025) == 0.25
    assert om.yuzdelik([5.0], 0.975) == 5.0


# ---------------------------------------------------------------------------
# Karar kuralı — üç dal + sınırlar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("alt,ust,beklenen", [
    (5.01, 9.0, "STOP BACAĞINDA MODEL İYİMSER"),
    (1.0, 4.99, "MODEL YETERLİ (stop bacağı)"),
    (3.0, 7.0, "BELİRSİZ"),
    (5.0, 8.0, "BELİRSİZ"),      # CI-alt = 5 → '> 5' değil
    (2.0, 5.0, "BELİRSİZ"),      # CI-üst = 5 → '< 5' değil
])
def test_karar_kurali_uc_dal(om, alt, ust, beklenen):
    assert om.karar_kurali(alt, ust) == beklenen


def test_ozet_karari_CI_ile_basar(om):
    o = om.ozetle(_ozet_satirlari(120, 60, kayma=12.0), _OZ_GECTI, _PK1_GECTI)
    assert o["durum"] == "KOSULLU_HUKUM"
    assert o["ci95_bps"] == [12.0, 12.0]
    assert o["karar"] == "STOP BACAĞINDA MODEL İYİMSER"
    o2 = om.ozetle(_ozet_satirlari(120, 60, kayma=1.0), _OZ_GECTI, _PK1_GECTI)
    assert o2["karar"] == "MODEL YETERLİ (stop bacağı)"
    o3 = om.ozetle(_ozet_satirlari(120, 60, kayma_fn=lambda i: [0.0, 10.0][i % 2]),
                   _OZ_GECTI, _PK1_GECTI)
    assert o3["karar"] == "BELİRSİZ"


def test_esik_n_ve_seans_altinda_OLCULEMEDI(om):
    o = om.ozetle(_ozet_satirlari(99, 60), _OZ_GECTI, _PK1_GECTI)
    assert o["durum"] == "OLCULEMEDI" and o["medyan_bps"] is None and o["karar"] is None
    o = om.ozetle(_ozet_satirlari(120, 49), _OZ_GECTI, _PK1_GECTI)
    assert o["durum"] == "OLCULEMEDI"
    o = om.ozetle(_ozet_satirlari(100, 50), _OZ_GECTI, _PK1_GECTI)
    assert o["durum"] == "KOSULLU_HUKUM"


# ---------------------------------------------------------------------------
# Kill-list dalları
# ---------------------------------------------------------------------------
def test_kill2_dokunus_yok_yuzde20_ASARSA_medyan_yayimlanmaz(om):
    # uygun = 120 olculdu + 31 dokunus_yok = 151 → %20,5 > %20
    o = om.ozetle(_ozet_satirlari(120, 60, n_dokunus_yok=31), _OZ_GECTI, _PK1_GECTI)
    assert o["kill_list"]["dokunus_yok_asimi"] is True
    assert o["durum"] == "YAYIMLANMAZ"
    assert o["medyan_bps"] is None and o["ci95_bps"] is None and o["karar"] is None


def test_kill2_tam_yuzde20_ASIM_sayilmaz(om):
    # uygun = 120 + 30 = 150 → tam %20 — kart 'aşarsa' der
    o = om.ozetle(_ozet_satirlari(120, 60, n_dokunus_yok=30), _OZ_GECTI, _PK1_GECTI)
    assert o["kill_list"]["dokunus_yok_asimi"] is False
    assert o["durum"] == "KOSULLU_HUKUM"


def test_kill3_tek_seans_yuzde10_ASARSA_CI_serhli(om):
    # 120 satır / 60 seans + ilk seansa 12 ek → ilk seans 14/132 = %10,6
    o = om.ozetle(_ozet_satirlari(120, 60, buyuk_seans=12), _OZ_GECTI, _PK1_GECTI)
    assert o["kill_list"]["tek_seans_asimi"] is True
    assert o["ci_serh"] and "tek seans" in o["ci_serh"]
    assert o["ci95_bps"] is not None      # şerhli yayımlanır, düşürülmez


def test_kill3_tam_yuzde10_serh_gerektirmez(om):
    # 110 satır / 55 seans + ilk seansa 10 ek → ilk seans 12/120 = TAM %10 — kart 'fazlasını' der
    o = om.ozetle(_ozet_satirlari(110, 55, buyuk_seans=10), _OZ_GECTI, _PK1_GECTI)
    assert o["tek_seans_payi"] == 0.10
    assert o["kill_list"]["tek_seans_asimi"] is False and o["ci_serh"] is None


def test_kill1_oz_sinama_duserse_GECERSIZ(om):
    o = om.ozetle(_ozet_satirlari(120, 60), {"gecti": False}, _PK1_GECTI)
    assert o["durum"] == "GECERSIZ" and o["medyan_bps"] is None


def test_PK1_duserse_hicbir_sayi_yok(om):
    o = om.ozetle(_ozet_satirlari(120, 60), _OZ_GECTI, {"gecti": False})
    assert o["durum"] == "GECERSIZ" and o["medyan_bps"] is None and o["tanilar"] is None


# ---------------------------------------------------------------------------
# eff_stop — motorla aynılık + tersine-çevirme + öz-sınama
# ---------------------------------------------------------------------------
def test_ileri_formul_MOTORUN_defter_exitine_birebir_esit(om, sandbox_state):
    rng = random.Random(20260925)
    for _ in range(400):
        stop = round(rng.uniform(3.0, 900.0), 4)
        trail = None if rng.random() < 0.5 else stop + rng.uniform(0.0, 20.0)
        satir = _motor_satiri("ZZZ", "2024-01-05", stop, trail)
        eff = max(stop, trail if trail is not None else stop)
        assert om.ileri_dolum(eff, om.SLIP_BPS) == satir["exit"]
        ters = om.ters_eff_stop(satir["exit"], om.SLIP_BPS)
        assert abs(ters - eff) <= om.ters_hata_siniri(om.SLIP_BPS) + 1e-9


def test_betik_kayma_sabiti_goal_ve_kartla_ayni(om):
    goal = yaml.safe_load(GOAL.read_text(encoding="utf-8"))
    kart = yaml.safe_load(KART.read_text(encoding="utf-8"))
    assert float(goal["slippage_bps"]) == om.SLIP_BPS
    assert float(kart["esikler"]["model_varsayimi_bps"]) == om.MODEL_VARSAYIMI_BPS == om.SLIP_BPS


def test_eff_stop_coz_sert_stop_PLANLA_izgara_kilidi(om, sandbox_state):
    satir = _motor_satiri("AAA", "2024-02-01", 48.37)
    r = om.eff_stop_coz(satir, [48.37], om.SLIP_BPS)
    assert r["oz"] == "plan_ileri_esit" and r["eff_stop"] == 48.37 and r["kaynak"] == "plan_stop"
    assert r["ters"] < 48.37          # saf ters formül bu satırda ızgaranın ALTINA düşer


def test_izgara_kilidi_stop_seviyesindeki_tiki_DOKUNUS_sayar(om, sandbox_state):
    """Saf ters formül (48,36998…) 48,37'lik tik'i kaçırır ve dokunuşu daha derin bir tike kaydırır —
    kayma YUKARI yanlanır. Plan stop'u ileri formülle exit'i birebir veriyorsa eff_stop = plan stop."""
    g = "2024-02-01"
    satir = _motor_satiri("AAA", g, 48.37)
    kay = [_kayit(_et(g, "10:00:00"), 48.40), _kayit(_et(g, "10:00:01"), 48.37),
           _kayit(_et(g, "10:00:02"), 48.37), _kayit(_et(g, "10:00:03"), 48.20),
           _kayit(_et(g, "10:00:04"), 48.10)]
    seans = om.seans_suz(kay, dt.date.fromisoformat(g))
    r = om.eff_stop_coz(satir, [48.37], om.SLIP_BPS)
    assert om.dokunus_ve_dolum(seans, r["eff_stop"])["kayma_bps"] == 0.0
    saf = om.dokunus_ve_dolum(seans, r["ters"])
    assert saf["kayma_bps"] > 5.0     # yanlılığın büyüklüğü: çivinin neden var olduğu


def test_eff_stop_coz_trailing_ustte_ters_formul(om, sandbox_state):
    satir = _motor_satiri("AAA", "2024-02-01", 40.0, trail=43.123456789)
    r = om.eff_stop_coz(satir, [40.0], om.SLIP_BPS)
    assert r["oz"] == "plan_trailing_ustte" and r["kaynak"] == "ters_formul"
    assert abs(r["eff_stop"] - 43.123456789) <= om.ters_hata_siniri(om.SLIP_BPS)


def test_eff_stop_coz_plan_stopunun_ALTINDA_ters_red(om, sandbox_state):
    satir = _motor_satiri("AAA", "2024-02-01", 40.0)
    r = om.eff_stop_coz(satir, [41.0], om.SLIP_BPS)     # plan stop'u ters değerin ÜSTÜNDE → imkânsız
    assert r["oz"] == "plan_alti_ihlal" and r["red"] is True


def test_eff_stop_coz_plan_yoksa_islem_ici_turetim(om, sandbox_state):
    satir = _motor_satiri("AAA", "2024-02-01", 40.0)
    r = om.eff_stop_coz(satir, [], om.SLIP_BPS)
    assert r["oz"] == "islem_ici_tutarli" and r["kaynak"] == "ters_formul"
    satir.pop("r_payda_usd")
    assert om.eff_stop_coz(satir, [], om.SLIP_BPS)["oz"] == "kaynak_yok"


def test_kill1_oz_sinama_en_az_20_satir(om, sandbox_state):
    def _cozumler(n_esit, n_trailing):
        out = []
        for i in range(n_esit):
            out.append(om.eff_stop_coz(_motor_satiri("AAA", "2024-02-01", 40.0 + i), [40.0 + i],
                                       om.SLIP_BPS))
        for i in range(n_trailing):
            out.append(om.eff_stop_coz(_motor_satiri("AAA", "2024-02-01", 40.0, trail=45.0 + i),
                                       [40.0], om.SLIP_BPS))
        return out
    assert om.oz_sinama_ozeti(_cozumler(19, 30))["gecti"] is False
    assert om.oz_sinama_ozeti(_cozumler(20, 0))["gecti"] is True


# ---------------------------------------------------------------------------
# Kaynak metin: meridian İÇE AKTARILMAZ, yalnız stdlib + pyarrow (+ duckdb okuyucusu)
# ---------------------------------------------------------------------------
def _ithal_kokleri() -> set[str]:
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    kokler = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            kokler |= {a.name.split(".")[0] for a in d.names}
        elif isinstance(d, ast.ImportFrom):
            assert d.level == 0, "göreli içe aktarma"
            kokler.add(d.module.split(".")[0])
        elif isinstance(d, ast.Call) and getattr(d.func, "id", None) == "__import__":
            kokler.add("__import__")
    return kokler


def test_betik_meridian_ICE_AKTARMAZ_ve_yalniz_stdlib_pyarrow(om):
    kokler = _ithal_kokleri()
    assert "meridian" not in kokler and "__import__" not in kokler
    assert "importlib" not in kokler
    izinli = set(sys.stdlib_module_names) | {"pyarrow", "duckdb"}
    assert kokler <= izinli, kokler - izinli
    assert {"pyarrow", "sqlite3"} <= kokler
    assert "numpy" not in kokler and "pandas" not in kokler


def test_ithal_tarayicisi_SENTETIK_ihlali_gorur(tmp_path, monkeypatch):
    """Boşta-temiz tuzağı: tarayıcı `from meridian import …`u gerçekten yakalar."""
    sahte = tmp_path / "olcum.py"
    sahte.write_text("import json\nfrom meridian import broker\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "BETIK", sahte)
    assert "meridian" in _ithal_kokleri()


# ---------------------------------------------------------------------------
# Uçtan uca (CLI) — sentetik DB + parquet + bar
# ---------------------------------------------------------------------------
def test_uctan_uca_12_bps_enjeksiyonu_ve_karar(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, ek_siniflar=True)
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    o = s["ozet"]
    assert s["girdi"]["n_trades_filtreli"] == 122           # 120 + dokunus_yok + sonraki_yok
    assert s["girdi"]["sql_capraz_n"] == 122
    assert o["siniflar"]["olculdu"] == 120
    assert o["siniflar"]["dokunus_yok"] == 1 and o["siniflar"]["sonraki_yok"] == 1
    assert abs(o["medyan_bps"] - 12.0) < 1e-9
    assert o["ci95_bps"] == [12.0, 12.0]
    assert o["karar"] == "STOP BACAĞINDA MODEL İYİMSER"
    assert o["durum"] == "KOSULLU_HUKUM"
    assert s["oz_sinama"]["gecti"] is True and s["oz_sinama"]["plan_ileri_esit"] == 122
    assert s["pk"]["pk1"]["gecti"] is True
    assert s["pk"]["pk3"]["bar_ayagi_tutarsiz"] == 0
    assert s["pk"]["pk3"]["tick_ayagi_tutarsiz"] == 1         # dokunus_yok satırı
    # kartın 'tick günlük min'inin harfî okuması: seans ÖNCESİ kayıt eşik altında → günlük ayak tutarlı
    assert s["pk"]["pk3"]["tick_ayagi_gunluk_tutarsiz"] == 0
    t = o["tanilar"]
    assert t["en_yakin_edg045_hucresi"]["hucre"] == 5   # ek = 12 − 5 = 7 → 5
    assert t["dokunus_ani_spread_bps"]["n"] == 120      # dokunuş kaydı iki yanlı kotasyon taşır
    assert t["olcek_uyumlu_altkume"]["n_olculen"] == 120
    assert t["olcek_uyumlu_altkume"]["olcek_uyumsuz_n"] == 0
    assert set(t["yil_kirilimi"]) == {"2024"}
    assert sum(v["n"] for v in t["fiyat_kovasi_kirilimi"].values()) == 120
    # girdi içerik-adresli: dosyanın sha256'sı sonuca yazılan değerle aynı
    dokum = (sahne["cikti"] / "girdi_trades.json").read_bytes()
    assert hashlib.sha256(dokum).hexdigest() == s["girdi"]["trades_sha256"]
    assert (sahne["cikti"] / "OZET.md").read_text(encoding="utf-8").count("EDG-2026-102") >= 1


def test_uctan_uca_KIMLIK_sifir_bps_MODEL_YETERLI(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, enjeksiyon_bps=0.0)
    assert _kos(om, sahne) == 0
    o = _sonuc(sahne)["ozet"]
    assert o["medyan_bps"] == 0.0 and o["ci95_bps"] == [0.0, 0.0]
    assert o["karar"] == "MODEL YETERLİ (stop bacağı)"


def test_uctan_uca_birincil_KOSULDAN_bagimsiz_tani_a_bagimli(om, sandbox_state, tmp_path):
    a = _sahne(tmp_path / "a", kosul=0)
    b = _sahne(tmp_path / "b", kosul=0x20)
    assert _kos(om, a) == 0 and _kos(om, b) == 0
    sa, sb = _sonuc(a), _sonuc(b)
    assert sa["ozet"]["medyan_bps"] == sb["ozet"]["medyan_bps"]
    assert sa["ozet"]["ci95_bps"] == sb["ozet"]["ci95_bps"]
    assert [r["kayma_bps"] for r in sa["satirlar"]] == [r["kayma_bps"] for r in sb["satirlar"]]
    ta, tb = sa["ozet"]["tanilar"]["kosul_0x20_disi"], sb["ozet"]["tanilar"]["kosul_0x20_disi"]
    assert ta["n_olculen"] == 120 and tb["n_olculen"] == 0


def test_uctan_uca_yazim_YALNIZ_cikti_altinda(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path)
    once = _agac_fotografi(tmp_path, sahne["cikti"])
    assert _kos(om, sahne) == 0
    assert _agac_fotografi(tmp_path, sahne["cikti"]) == once
    yazilan = sorted(p.name for p in sahne["cikti"].rglob("*") if p.is_file())
    assert yazilan == sorted(om.CIKTI_DOSYALARI)


def test_cikti_girdi_agacinin_icindeyse_REDDEDER(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=2)
    for icerisi in (sahne["state"] / "olcum", sahne["tick"].parent / "x", sahne["bars"] / "y"):
        sahne["cikti"] = icerisi
        assert _kos(om, sahne) == 2
        assert not icerisi.exists()


def test_mevcut_sonuc_UZERINE_YAZILMAZ(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=2)
    sahne["cikti"].mkdir(parents=True)
    (sahne["cikti"] / "sonuc.json").write_text("{}", encoding="utf-8")
    assert _kos(om, sahne) == 2
    assert (sahne["cikti"] / "sonuc.json").read_text(encoding="utf-8") == "{}"


def test_elle_ornek_deterministik_ve_kanitli(om, sandbox_state, tmp_path):
    a = _sahne(tmp_path / "a")
    b = _sahne(tmp_path / "b")
    assert _kos(om, a, "--elle-ornek", "3") == 0 and _kos(om, b, "--elle-ornek", "3") == 0
    oa, ob = _sonuc(a)["pk"]["pk2"]["ornekler"], _sonuc(b)["pk"]["pk2"]["ornekler"]
    assert len(oa) == 3
    assert [(x["ticker"], x["seans"]) for x in oa] == [(x["ticker"], x["seans"]) for x in ob]
    for x in oa:
        dok = [k for k in x["dilim"] if k["rol"] == "dokunus"]
        dol = [k for k in x["dilim"] if k["rol"] == "dolum"]
        assert len(dok) == 1 and len(dol) == 1
        assert dok[0]["fiyat"] <= x["eff_stop"] and dol[0]["i"] == dok[0]["i"] + 1
        assert dol[0]["fiyat"] == x["tick_fill"]
        assert x["dokunus_oncesi_seans_min"] is None or x["dokunus_oncesi_seans_min"] > x["eff_stop"]
    assert _sonuc(a)["pk"]["pk2"]["durum"] == "ROL1_ELLE_DOGRULAMA_BEKLIYOR"


def test_kuru_kip_tik_OKUMADAN_kapsam_ve_oz_sinama(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, gun_sayisi=3)
    (sahne["tick"] / f"{sahne['gunler'][1]}.parquet").unlink()
    assert _kos(om, sahne, "--kuru") == 0
    k = json.loads((sahne["cikti"] / "kuru.json").read_text(encoding="utf-8"))
    assert k["oz_sinama"]["gecti"] is False            # 6 satır < 20 (kuru adımda da görünür)
    assert k["kapsam"]["gun_dosyasi_yok"] == [sahne["gunler"][1]]
    assert k["kapsam"]["sema_uygun_gun"] == 2
    o = k["okuma_sinamasi"]                           # üretim okuyucusu GERÇEKTEN okudu (şema değil)
    assert o["gun"] == sahne["gunler"][0] and o["sure_sn"] >= 0 and o["bayt"] > 0
    assert o["sembol"] == {"AAA": {"kayit": 5, "seans_kaydi": 4}, "BBB": {"kayit": 5, "seans_kaydi": 4}}
    assert not (sahne["cikti"] / "sonuc.json").exists()


def test_uctan_uca_CLI_operatorun_kosacagi_bicimde(sandbox_state, tmp_path):
    """CLAUDE.md §6: ops aracı operatörün koşacağı BİÇİMDE bir kez koşulur (alt süreç, argv)."""
    sahne = _sahne(tmp_path)
    p = subprocess.run([sys.executable, str(BETIK), "--db", str(sahne["db"]),
                        "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                        "--cikti", str(sahne["cikti"]), "--elle-ornek", "5", "--okuyucu", "duckdb"],
                       capture_output=True, text=True, timeout=300, cwd=str(tmp_path))
    assert p.returncode == 0, p.stderr[-2000:]
    s = _sonuc(sahne)
    assert s["arac"]["okuyucu"] == "duckdb"
    assert abs(s["ozet"]["medyan_bps"] - 12.0) < 1e-9
    assert "KARAR" in p.stdout and "12" in p.stdout


# ---------------------------------------------------------------------------
# Tek-kaynak: betik sabitleri ↔ kart
# ---------------------------------------------------------------------------
def test_betik_sabitleri_KARTLA_ayni(om):
    kart_metin = KART.read_text(encoding="utf-8")
    kart = yaml.safe_load(kart_metin)
    assert kart["card_id"] == om.KART_ID
    assert kart["esikler"]["n_uygun_alt"] == om.N_UYGUN_ALT
    assert kart["esikler"]["seans_alt"] == om.SEANS_ALT
    kill = " ".join(kart["kill_list"])
    assert "%20" in kill and om.DOKUNUS_YOK_TAVAN == 0.20
    assert "%10" in kill and om.TEK_SEANS_TAVAN == 0.10
    assert re.search(r"en az\s+20\s+satır", kill) and om.OZ_SINAMA_ALT == 20
    plan = " ".join(kart["olcum_plani"])
    assert f"B={om.BOOT_B}" in plan and f"seed={om.BOOT_TOHUM}" in plan
    assert "{5,10,20}" in plan and tuple(om.EDG045_HUCRELERI) == (5, 10, 20)
    assert "0x20" in plan and om.KOSUL_TEK_LOT_BITI == 0x20


# ---------------------------------------------------------------------------
# Girdi birleştirme + ölçek tanısı (bölünme riski)
# ---------------------------------------------------------------------------
def test_birlestir_extra_json_KAZANIR_ve_bozuk_extra_sayilir(om):
    """`meridian.storage._cols_to_row` semantiği: tipli kolon + extra_json, extra KAZANIR."""
    sayac = {"extra_json_bozuk": 0}
    b = om._birlestir({"seq": 1, "kaynak": "live_paper", "exit": 10.0,
                       "extra_json": '{"kaynak": "replay_seed"}'}, sayac)
    assert b["kaynak"] == "replay_seed" and "seq" not in b and "extra_json" not in b
    b = om._birlestir({"seq": 2, "kaynak": "replay_seed", "extra_json": "{bozuk"}, sayac)
    assert b["kaynak"] == "replay_seed" and sayac["extra_json_bozuk"] == 1


def test_olcek_tanisi_bolunme_olcegini_ISARETLER(om):
    """Bar split-düzeltmeli, tik ham: 10:1 bölünme öncesi gün bar kapanışı tikin ~1/10'u."""
    g = "2024-05-15"
    kay = [_kayit(_et(g, "10:00:00"), 500.0), _kayit(_et(g, "10:00:01"), 480.0),
           _kayit(_et(g, "10:00:02"), 479.0), _kayit(_et(g, "15:00:00"), 490.0)]
    for bar_kapanis, beklenen in ((49.0, True), (489.0, False)):
        r = {"seans": g, "eff_stop": 480.0, "ters": 480.0, "ticker": "NNN"}
        om.satir_olc(r, kay, {g: {"open": 49.5, "high": 50.0, "low": 47.0, "close": bar_kapanis}})
        assert r["olcek_uyumsuz"] is beklenen
    r = {"seans": g, "eff_stop": 480.0, "ters": 480.0, "ticker": "NNN"}
    om.satir_olc(r, kay, None)
    assert r["olcek_uyumsuz"] is None and r["pk3_bar_ayagi"] is None


def test_on_siniflar_yon_disi_ve_tarih_okunamadi(om):
    """Ters formül yalnız long için okundu; ts_close çözülemeyen satır ölçüme girmez — ikisi de SAYILIR."""
    girdi = {"planlar": {"P1": [40.0]}, "secili": [
        ({"seq": 1}, {"ticker": "aaa", "side": "long", "ts_close": "2024-02-01", "exit": 39.98,
                      "plan_id": "P1"}),
        ({"seq": 2}, {"ticker": "BBB", "side": "short", "ts_close": "2024-02-01", "exit": 39.98}),
        ({"seq": 3}, {"ticker": "CCC", "side": "long", "ts_close": "bozuk", "exit": 39.98})]}
    satirlar, cozumler = om.satirlari_hazirla(girdi)
    assert [r["sinif"] for r in satirlar] == [None, "yon_disi", "tarih_okunamadi"]
    assert satirlar[0]["ticker"] == "AAA" and satirlar[0]["eff_stop"] == 40.0
    assert len(cozumler) == 1


def test_uctan_uca_gun_dosyasi_yoksa_DOKUNUS_YOK_sayilir(om, sandbox_state, tmp_path):
    """Kapsam boşluğu dokunuşsuzluktur (kart kill-2: 'bar ↔ tick tutarsızlığı ya da kapsam boşluğu')."""
    sahne = _sahne(tmp_path)
    (sahne["tick"] / f"{sahne['gunler'][7]}.parquet").unlink()
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    assert s["ozet"]["siniflar"]["dokunus_yok"] == 2 and s["ozet"]["siniflar"]["olculdu"] == 118
    assert {r["alt_neden"] for r in s["satirlar"] if r["sinif"] == "dokunus_yok"} == {"gun_dosyasi_yok"}
    assert s["pk"]["pk3"]["tick_ayagi_olculemedi"] == 2
