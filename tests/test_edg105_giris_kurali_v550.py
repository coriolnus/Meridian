"""test_edg105_giris_kurali_v550.py — EDG-2026-105 (TSK-224 tur 2): replay girişlerini KODA SADIK canlı giriş kuralıyla
(emir tipi plan günü kapanışından · 09:45 ET gönderim · limit tavanı canlı kuruş yuvarlamasıyla) tick arşivinde yeniden
yürüten ölçüm betiğinin çivileri (`research/olcumler/edg105_giris_kurali/olcum.py`).

KART: research/cards/EDG-2026-105-replay-giris-canli-kural-tick-koda-sadik.yaml — eşik, kill-list ve pozitif kontrol ORADA
donuktur; bu dosya betiğin karta SADAKATİNİ ölçer, kartı değil. Selef EDG-2026-104 ölçüm öncesi EMEKLİ (emir tipini 09:45
fiyatından seçiyordu; canlı kod plan anında sinyal kapanışından seçer) — bu dosyanın kill-6 çivisi o hatanın geri dönüşünü ısırır.

NUMARA: v550 bu dosyanın kimliğidir; tur 1'in `test_edg104_giris_kurali_v550.py`si emekli kartın taslağıdır ve Rol-1
tarafından kaldırılır (brief: ajan silmez/taşımaz).

KART YOLU: kart ağaçta `research/cards/` altındadır. Eski tabanlı bir worktree'de kart henüz yoksa `EDG105_KART_YOLU`
ortam değişkeni kartın salt-okur yolunu verir; ikisi de yoksa kartı okuyan çivi KIRMIZI olur (sessiz atlama YOK).

NE ÖLÇÜLÜR:
  * emir tipi YALNIZ plan günü kapanışından (`emir_tipi` ↔ `meridian.broker.entry_order_decision`); 09:45'te tetiğin altında
    açılan GAP satırı yine GAP dalında dolar (kill-6 + PK-1).
  * öykünücünün iki dalı, DOLMAZ, L sınırı CANLI kuruş yuvarlamasıyla (`meridian.adapters.alpaca.submit_bracket` gövdesi
    yakalanır), 09:45 sınırı, DST, akis_yok, "SONRAKİ kayıt" mekaniği, fark işareti.
  * erken kapanış listesi kart ↔ betik ↔ `pandas_market_calendars` XNYS eşitliği; o günlerin girişleri dışlanır, sayılır.
  * kill-3'ün iki bandı (bar açılışı / ilk tik · plan günü kapanışı / tetik), kill-list 1–7, n eşikleri, iki AYRI karar.
  * PK-2 kotası (≥ 4 GAP, varsa STOP-LIMIT, varsa ≥ 1 DOLMAZ), PK-3'ün iki koşulu.
  * EDG-2026-102 kopyalarının ayrışma çivisi, stdin argv + `--betik-sha256`, girdi dökümü sha256 kararlılığı.

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
import os
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
BETIK = REPO / "research" / "olcumler" / "edg105_giris_kurali" / "olcum.py"
KART = pathlib.Path(os.environ.get("EDG105_KART_YOLU") or
                    REPO / "research" / "cards" / "EDG-2026-105-replay-giris-canli-kural-tick-koda-sadik.yaml")
GOAL = REPO / "state" / "goal.yaml"
EDG102 = REPO / "research" / "olcumler" / "edg102_stop_kayma" / "olcum.py"

NS = 1_000_000_000
UTC = dt.timezone.utc


@pytest.fixture(scope="module")
def om():
    """Ölçüm betiği — KAYNAKTAN derlenmiş modül (ham exec_module yasağı v334)."""
    return betikten_modul_yukle(BETIK, "edg105_olcum")


@pytest.fixture(scope="module")
def e102():
    """EDG-2026-102 betiği — kopyaların kaynağı; `meridian` değil, dosya yolundan."""
    return betikten_modul_yukle(EDG102, "edg102_olcum_v550b")


@pytest.fixture
def hizli(om, monkeypatch):
    """CI değerinin konu OLMADIĞI kill/eşik çivilerinde bootstrap tekrar sayısını düşürür."""
    monkeypatch.setattr(om, "BOOT_B", 200)


def _kart() -> dict:
    assert KART.exists(), (f"kart yok: {KART} — eski tabanlı ağaçta EDG105_KART_YOLU ile kartın salt-okur yolunu ver")
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
    """New York duvar saatinden epoch ns — test tarafı zoneinfo'yu KENDİSİ kullanır."""
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
    """Pilotun `islem/` şemasıyla (tipler birebir) parquet yazar."""
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
        satir.append(f"{g},{o!r},{h!r},{l!r},{c!r},1000000.0")
    yol.write_text("\n".join(satir) + "\n", encoding="utf-8")


TETIK = 50.0             # L = 52.0 (canlı yuvarlamada da 52.00)
GIRIS = 50.0             # trades.entry (replay dolumu)
ACILIS = GIRIS / 1.0005  # bar açılışı: açılış × (1 + 5 bps) = giriş → öz-sınama tutarlı

#: sembol → (plan günü kapanışı = ref, ET akışı [(saat, fiyat | "DOLUM")], bar yükseği, çıkış nedeni, r)
AKISLAR = {
    # GAP (ref = tetik): p0 = 50,50 → dolum t0'dan SONRAKİ ilk ≤ L kayıt (09:45:01)
    "AAA": (50.0, [("09:30:00", 49.00), ("09:45:00", 50.50), ("09:45:01", "DOLUM"), ("10:00:00", 51.00)],
            51.00, "target", 1.5),
    # STOP-LIMIT (ref < tetik): 09:30 kırılımı pencere ÖNCESİ; aktivasyon TAM tetikte
    "BBB": (49.0, [("09:30:00", 50.40), ("09:45:00", 49.50), ("10:00:00", 49.80), ("10:30:00", 50.00),
                   ("10:30:01", "DOLUM"), ("11:00:00", 50.10)], 50.40, "target", 1.2),
    # STOP-LIMIT: aktivasyondan sonraki kayıt L ÜSTÜ (atlanır), dolum bir sonraki
    "CCC": (49.0, [("09:31:00", 49.70), ("09:45:30", 49.60), ("12:00:00", 50.20), ("12:00:01", 52.50),
                   ("12:00:02", "DOLUM")], 52.50, "trail", 0.4),
    # STOP-LIMIT DOLMAZ: seans içinde tetiğe hiç çıkmaz; 16:00 sonrası kırılım SAYILMAZ
    "DDD": (49.0, [("09:30:00", 49.00), ("09:50:00", 49.20), ("11:00:00", 49.90), ("15:59:59", 49.95),
                   ("16:00:00", 50.50)], 49.95, "stop", -1.0),
    # GAP (ref = tetik) ama 09:45 fiyatı tetiğin ALTINDA: tip plan anından → yine GAP, 49,45'ten dolar (−110 bps)
    "EEE": (50.0, [("09:30:00", 50.20), ("09:45:00", 49.40), ("09:45:02", 49.45), ("11:00:00", 49.60),
                   ("15:00:00", 49.70)], 50.20, "stop", -0.8),
}


def _akis_satirlari(g: str, sym: str, dolum: float, kosul: int) -> list[tuple]:
    def r(saat, fiyat):
        t = _et(g, saat)
        p = int(round(fiyat * 10_000))
        return (t, sym, p, 100, kosul, t, p - 100, 100, p + 100, 100)
    out = [r("08:00:00", 51.00)]            # seans öncesi, tetik üstü — süzülmeli
    for saat, fiyat in AKISLAR[sym][1]:
        out.append(r(saat, dolum if fiyat == "DOLUM" else fiyat))
    return out


def _sahne(tmp_path, *, gun_sayisi=100, dolum=50.06, dolmaz=True, kosul=0, bas="2024-01-02") -> dict:
    """Uçtan uca sahne: her gün AAA, EEE (GAP) + BBB, CCC (STOP-LIMIT) DOLAN, DDD DOLMAZ. DOLAN'ların canlı dolumu
    `dolum` (50,06 → +12 bps; EEE her zaman 49,45 → −110 bps). Plan tarihi önceki iş günüdür, bar kapanışı = sembolün
    ref'i (tip oradan seçilir). 2024-01-02'den 100 iş günü Mart DST sınırını geçer."""
    kok = tmp_path / "sahne"
    state = kok / "state"
    tick = kok / "veri" / "tick" / "islem"
    bars = state / "bars"
    gunler = _is_gunleri(bas, gun_sayisi)
    semboller = [s for s in AKISLAR if dolmaz or s != "DDD"]
    islemler, planlar = [], []
    gun_tik: dict[str, list] = {g: [] for g in gunler}
    bar_ser: dict[str, dict] = {s: {} for s in semboller}
    n = 0
    ilk_plan = _onceki_is_gunu(bas)
    for i, g in enumerate(gunler):
        onceki = gunler[i - 1] if i else ilk_plan
        for sym in semboller:
            n += 1
            ref, _, yuksek, neden, rm = AKISLAR[sym]
            pid = f"P-{onceki}-{sym}"
            islemler.append({"id": f"T{n:05d}", "plan_id": pid, "ticker": sym, "side": "long",
                             "ts_open": g, "ts_close": g, "entry": GIRIS, "exit": 51.0, "qty": 10,
                             "r_multiple": rm, "exit_reason": neden, "strategy_version": 91,
                             "kaynak": "replay_seed"})
            planlar.append({"id": pid, "date": onceki, "ticker": sym, "side": "long",
                            "entry_trigger": TETIK, "stop": 48.0, "profit_target": 55.0,
                            "strategy_version": 91})
            gun_tik[g] += _akis_satirlari(g, sym, dolum, kosul)
            bar_ser[sym][g] = (ACILIS, yuksek, 48.5, ref)
    for sym in semboller:
        bar_ser[sym][ilk_plan] = (ACILIS, 50.0, 48.5, AKISLAR[sym][0])
    gurultu = dict(islemler[0], id="T99999", kaynak="live_paper")   # girdiye GİRMEZ
    _db_yaz(state / "meridian.db", islemler + [gurultu], planlar)
    for g, s in gun_tik.items():
        _parquet_yaz(tick / f"{g}.parquet", s)
    for sym, ser in bar_ser.items():
        _bar_yaz(bars, sym, ser)
    return {"db": state / "meridian.db", "tick": tick, "bars": bars, "cikti": kok / "cikti",
            "gunler": gunler, "state": state, "n": len(islemler)}


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


# ---------------------------------------------------------------------------
# Emir tipi — YALNIZ plan günü kapanışından (kill-6)
# ---------------------------------------------------------------------------
G = "2024-07-10"   # EDT


def test_kill6_tip_YALNIZ_plan_gunu_kapanisindan_0945_fiyatindan_BAGIMSIZ(om):
    """Selefin hatası geri gelmesin: GAP satırı (ref ≥ tetik) 09:45'te tetiğin ALTINDA olsa da GAP dalında dolar;
    STOP-LIMIT satırı (ref < tetik) 09:45'te tetiğin ÜSTÜNDE olsa da STOP-LIMIT'tir (aktivasyon t0'ın kendisi)."""
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
    for _ in range(3000):
        t = round(rng.uniform(1.0, 1500.0), 4)
        ref = rng.choice([t, round(t + 1e-4, 4), round(t - 1e-4, 4), round(t * rng.uniform(0.9, 1.1), 4)])
        dec = B.entry_order_decision(t, ref_price=ref, atr=None, cfg=cfg)
        assert esle[dec["mode"]] == om.emir_tipi(ref, t), (t, ref)
    assert om.emir_tipi(50.0, 50.0) == "GAP" and om.emir_tipi(49.9999, 50.0) == "STOP_LIMIT"


# ---------------------------------------------------------------------------
# Öykünücü — iki dal, sınırlar
# ---------------------------------------------------------------------------
def test_GAP_dali_dolum_t0dan_SONRAKI_ilk_limit_ici_kayit(om):
    kay = [_kayit(_et(G, "09:30:00"), 49.0), _kayit(_et(G, "09:45:00"), 50.5),
           _kayit(_et(G, "09:45:01"), 50.06), _kayit(_et(G, "10:00:00"), 51.0)]
    k = _kural(om, G, kay, ref=50.0)
    assert k["dal"] == "GAP" and k["sinif"] == "DOLAN"
    assert k["t0_i"] == 1 and k["dolum_i"] == 2          # t0'ın KENDİSİ değil, sonraki kayıt
    assert k["canli_dolum"] == 50.06 and k["p0"] == 50.5


def test_STOP_LIMIT_dali_aktivasyon_TAM_tetikte_ve_SONRAKI_kayitta_dolum(om):
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "10:00:00"), 49.8),
           _kayit(_et(G, "10:30:00"), 50.0), _kayit(_et(G, "10:30:01"), 50.07),
           _kayit(_et(G, "11:00:00"), 49.0)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["dal"] == "STOP_LIMIT" and k["sinif"] == "DOLAN"
    assert k["akt_i"] == 2 and k["dolum_i"] == 3          # aktivasyon kaydı dolum DEĞİL
    assert k["canli_dolum"] == 50.07


def test_tetige_hic_cikmayan_STOP_LIMIT_DOLMAZ(om):
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "12:00:00"), 49.99),
           _kayit(_et(G, "15:59:59"), 49.9), _kayit(_et(G, "16:00:00"), 51.0)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["sinif"] == "DOLMAZ" and k["neden"] == "tetik_kirilmadi" and k["akt_i"] is None


def test_L_ustunde_kalan_akis_DOLMAZ(om):
    kay = [_kayit(_et(G, "09:45:00"), 49.5), _kayit(_et(G, "10:00:00"), 50.2),
           _kayit(_et(G, "10:00:01"), 52.01), _kayit(_et(G, "10:00:02"), 53.0)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["sinif"] == "DOLMAZ" and k["neden"] == "limit_ici_kayit_yok" and k["akt_i"] == 1
    gap = [_kayit(_et(G, "09:45:00"), 52.5), _kayit(_et(G, "09:45:01"), 52.3), _kayit(_et(G, "15:00:00"), 53.1)]
    assert _kural(om, G, gap, ref=50.0)["sinif"] == "DOLMAZ"     # GAP dalında da L üstü dolmaz


def test_L_siniri_tam_L_DAHIL_bir_kurus_ustu_HARIC(om):
    assert om.limit_fiyati(TETIK) == 52.0
    tam = [_kayit(_et(G, "09:45:00"), 52.5), _kayit(_et(G, "09:45:01"), 52.0)]
    k = _kural(om, G, tam, ref=50.0)
    assert k["sinif"] == "DOLAN" and k["canli_dolum"] == 52.0
    ust = [_kayit(_et(G, "09:45:00"), 52.5), _kayit(_et(G, "09:45:01"), 52.01)]
    assert _kural(om, G, ust, ref=50.0)["sinif"] == "DOLMAZ"


def test_L_KURUS_yuvarlamali_canli_L_asagi_ve_yukari(om):
    """Ham L = 10,413 → canlı 10,41: 10,412 (ham L'nin ALTINDA, canlı L'nin ÜSTÜNDE) DOLMAZ, 10,41 dolar.
    Ham L = 12,8076 → canlı 12,81: 12,81 (ham L'nin ÜSTÜNDE) dolar."""
    assert om.limit_ham(10.0125) > 10.412 > om.limit_fiyati(10.0125) == 10.41
    kay = [_kayit(_et(G, "09:45:00"), 10.60), _kayit(_et(G, "09:45:01"), 10.412), _kayit(_et(G, "09:45:02"), 10.41)]
    k = _kural(om, G, kay, tetik=10.0125, ref=10.0125)
    assert k["sinif"] == "DOLAN" and k["dolum_i"] == 2 and k["canli_dolum"] == 10.41
    assert om.limit_ham(12.315) < 12.81 == om.limit_fiyati(12.315)
    kay = [_kayit(_et(G, "09:45:00"), 13.00), _kayit(_et(G, "09:45:01"), 12.81)]
    k = _kural(om, G, kay, tetik=12.315, ref=12.315)
    assert k["sinif"] == "DOLAN" and k["canli_dolum"] == 12.81


@pytest.mark.parametrize("tetik,canli_L,tek_yuvarlama_L", [(1.0337, 1.07, 1.08), (1.0913, 1.14, 1.13)])
def test_L_CIFT_yuvarlama_tek_yuvarlamadan_AYRISIR(om, tetik, canli_L, tek_yuvarlama_L):
    """Canlı zincir: karar L = round(ham, 4) → gövde L = round(karar, 2). 4 haneli tetiklerin ~%0,5'inde bu, tek
    round(ham, 2)'den FARKLI kuruş verir (ölçüldü 2026-09-25: 1,0000–199,9999 ızgarasında 9.554 tetik)."""
    assert om.limit_fiyati(tetik) == canli_L and round(om.limit_ham(tetik), 2) == tek_yuvarlama_L
    kay = [_kayit(_et(G, "09:45:00"), 1.20), _kayit(_et(G, "09:45:01"), max(canli_L, tek_yuvarlama_L)),
           _kayit(_et(G, "09:45:02"), min(canli_L, tek_yuvarlama_L))]
    k = _kural(om, G, kay, tetik=tetik, ref=tetik)
    beklenen_i = 1 if canli_L >= tek_yuvarlama_L else 2        # yalnız canlı L içindeki ilk kayıt dolar
    assert k["sinif"] == "DOLAN" and k["dolum_i"] == beklenen_i


def test_0944_59_kirilimi_SAYILMAZ_t0_tam_0945(om):
    kay = [_kayit(_et(G, "09:30:00"), 49.0), _kayit(_et(G, "09:44:59"), 50.5),
           _kayit(_et(G, "09:45:00"), 49.8), _kayit(_et(G, "10:00:00"), 49.7)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["t0_i"] == 2 and k["p0"] == 49.8 and k["dal"] == "STOP_LIMIT"
    assert k["sinif"] == "DOLMAZ"                        # 09:44:59 kırılımı pencere ÖNCESİ


def test_t0_SINIRI_nanosaniye_duzeyinde(om):
    p = _et(G, "09:45:00")
    kay = [_kayit(p - 1, 50.5), _kayit(p, 49.0), _kayit(p + 1, 49.1)]
    k = _kural(om, G, kay, ref=49.0)
    assert k["t0_i"] == 1 and k["p0"] == 49.0


@pytest.mark.parametrize("gun,pencere_utc", [
    ("2024-01-10", "14:45:00"), ("2024-03-08", "14:45:00"), ("2024-03-11", "13:45:00"), ("2024-11-04", "14:45:00"),
])
def test_pencere_DST_farkinda(om, gun, pencere_utc):
    assert om.pencere_ns(dt.date.fromisoformat(gun)) == _ns(gun, pencere_utc)


def test_kis_gunu_1345Z_kaydi_pencere_ONCESI(om):
    g = "2024-01-10"
    kay = [(_ns(g, "13:45:00"), 505_000, 100, 0, None, None), (_ns(g, "14:45:00"), 495_000, 100, 0, None, None),
           (_ns(g, "15:00:00"), 499_000, 100, 0, None, None)]
    k = _kural(om, g, kay, ref=49.0)
    assert k["t0_i"] == 0 and k["p0"] == 49.5 and k["sinif"] == "DOLMAZ"


def test_akis_yok_pencere_sonrasi_kayit_yoksa(om):
    kay = [_kayit(_et(G, "09:30:00"), 49.0), _kayit(_et(G, "09:44:00"), 50.5), _kayit(_et(G, "16:00:00"), 50.5)]
    assert _kural(om, G, kay, ref=50.0)["sinif"] == "akis_yok"
    assert _kural(om, G, [], ref=50.0)["sinif"] == "akis_yok"


def test_GAP_t0_son_kayitsa_DOLMAZ_sonraki_yok(om):
    k = _kural(om, G, [_kayit(_et(G, "15:59:00"), 50.5)], ref=50.0)
    assert k["sinif"] == "DOLMAZ" and k["neden"] == "sonraki_kayit_yok"


def test_fark_bps_isareti_canli_PAHALIYSA_pozitif(om):
    assert abs(om.fark_bps(50.06, 50.0) - 12.0) < 1e-9
    assert abs(om.fark_bps(49.94, 50.0) + 12.0) < 1e-9


def test_PK1_calisma_ani_kimlik_gecer(om):
    r = om.pk1_kimlik()
    assert r["gecti"] is True, r


# ---------------------------------------------------------------------------
# Motor ↔ betik ↔ kart sabitleri (tek-kaynak)
# ---------------------------------------------------------------------------
def test_sabitler_MOTOR_ve_goal_ile_ayni(om):
    from meridian import barclock
    goal = _goal()
    assert om.GIRIS_PENCERE_ET_DK == barclock.ENTRY_WINDOW_ET_MIN == 9 * 60 + 45
    assert float(goal["execution_v2"]["limit_pct_cap"]) == om.LIMIT_PCT_CAP == 0.04
    assert float(goal["slippage_bps"]) == om.SLIP_BPS == 5.0


def test_limit_ham_MOTORUN_entry_limit_price_ile_BIREBIR(om):
    from meridian import broker as B
    ex = _goal()["execution_v2"]
    cfg = {"limit_pct_cap": float(ex["limit_pct_cap"]), "limit_atr_mult": float(ex["limit_atr_mult"])}
    rng = random.Random(104)
    for _ in range(3000):
        t = round(rng.uniform(1.0, 2000.0), 4)
        assert om.limit_ham(t) == B.entry_limit_price(t, None, cfg), t


def test_limit_KURUS_yuvarlamasi_CANLI_emir_govdesiyle_AYNI(om, sandbox_state, monkeypatch):
    """Canlı L = `meridian.adapters.alpaca.submit_bracket` gövdesindeki `limit_price` — gerçek fonksiyon koşar, yalnız
    HTTP gönderimi yakalanır. Sınır örnekleri: aşağı (10,413 → 10,41), yukarı (12,8076 → 12,81), yarım kuruş (12,805)."""
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
    rng = random.Random(1050)
    ornekler = ([50.0, 10.0125, 12.315, 12.3125, 48.37, 123.4567, 1.0337, 1.0913, 1.1298]
                + [round(rng.uniform(1, 900), 4) for _ in range(400)])
    for t in ornekler:
        dec = B.entry_order_decision(t, ref_price=t, atr=None, cfg=cfg)
        assert dec["mode"] == "marketable_limit" and dec["limit"] == om.limit_karar(t)   # karar L: 4 hane
        r = A.submit_bracket("ZZZ", 10, t, t * 1.2, t * 0.9, client_order_id="P-v550", entry_limit=dec["limit"],
                             entry_type="limit")
        assert r["ok"] is True and govdeler[-1]["type"] == "limit"
        assert govdeler[-1]["limit_price"] == om.limit_fiyati(t), t
    assert om.limit_fiyati(12.3125) == 12.8 and om.limit_ham(12.3125) == 12.805


def test_replay_giris_MOTORUN_fill_entry_satiriyla_BIREBIR(om, sandbox_state):
    from meridian import broker as B
    rng = random.Random(20260925)
    for i in range(300):
        tetik = round(rng.uniform(5.0, 800.0), 4)
        acilis = round(tetik * rng.uniform(0.95, 1.009), 2)
        br = B.PaperBroker(100_000.0, om.SLIP_BPS, 0.0)
        plan = {"id": f"P{i}", "ticker": "ZZZ", "stop": round(min(tetik, acilis) * 0.9, 4),
                "entry_trigger": tetik, "size_r": 1.0, "profit_target": round(tetik * 1.3, 4)}
        assert br.fill_entry(plan, acilis, "2024-02-01", 100_000.0) is not None
        satir = br.close_position("ZZZ", acilis, "target", "2024-02-02")
        assert satir["entry"] == om.replay_giris(acilis), (tetik, acilis)
        assert om.oz_fark_bps(satir["entry"], acilis) <= om.OZ_SINAMA_TOL_BPS


def test_betik_sabitleri_KARTLA_ayni(om):
    kart = _kart()
    ham = KART.read_text(encoding="utf-8")
    assert kart["card_id"] == om.KART_ID == "EDG-2026-105" and kart["selef"] == "EDG-2026-104"
    e = kart["esikler"]
    assert e["n_uygun_alt"] == om.N_UYGUN_ALT == 300 and e["seans_alt"] == om.SEANS_ALT == 100
    assert e["dolmaz_esik_pct"] == om.DOLMAZ_ESIK_PCT == 5 and e["fiyat_bandi_bps"] == om.FIYAT_BANDI_BPS == 5
    for s in (om.KARAR_H1_IYIMSER, om.KARAR_H1_ESDEGER, om.KARAR_H2_IYIMSER, om.KARAR_H2_KOTUMSER,
              om.KARAR_H2_ESDEGER, om.KARAR_BELIRSIZ):
        assert f'"{s}"' in e["karar_kurali"], s
    assert len(kart["kill_list"]) == 7
    kill = " ".join(kart["kill_list"])
    assert re.search(r"en az 20 satırda\s+≤\s+1 bps", kill) and om.OZ_SINAMA_ALT == 20 and om.OZ_SINAMA_TOL_BPS == 1.0
    assert "%10'unu aşarsa" in kill and om.AKIS_YOK_TAVAN == 0.10
    assert kill.count("[0,9, 1,1]") == 2 and "plan-günü kapanışı ↔ tetik" in kill and om.OLCEK_BANDI == (0.9, 1.1)
    assert "%5'i aşarsa" in kill and om.OLCEK_DISLANAN_TAVAN == 0.05
    assert "%10'undan fazlasını" in kill and om.TEK_SEANS_TAVAN == 0.10
    assert "tip yalnız plan günü kapanışından" in kill
    pk = kart["pozitif_kontrol"]
    assert "> %20" in pk and om.PK3_TUTARSIZ_TAVAN == 0.20
    assert "≥4 GAP" in pk and om.PK2_GAP_ALT == 4
    plan = " ".join(kart["olcum_plani"])
    assert f"B={om.BOOT_B}" in plan and f"seed={om.BOOT_TOHUM}" in plan
    assert "0x20" in plan and om.KOSUL_TEK_LOT_BITI == 0x20
    assert "09:45" in plan and "limit_pct_cap" in plan and "kuruş yuvarlaması" in plan
    assert "tetik × 1,04" in ham
    assert len(kart["k_registry"]["trial_ids"]) == 2


def test_erken_kapanis_listesi_KART_betik_ve_mcal_ile_AYNI(om):
    metin = _kart()["adim_0_kaydi_2026_09_25"]
    blok = metin.split("XNYS erken kapanış")[1].split("bu günlerde")[0]
    kart_gunleri = tuple(re.findall(r"\d{4}-\d{2}-\d{2}", blok))
    import pandas_market_calendars as mcal
    takvim = mcal.get_calendar("XNYS")
    erken = takvim.early_closes(takvim.schedule("2022-01-01", "2026-07-31"))
    mcal_gunleri = tuple(d.date().isoformat() for d in erken.index)
    assert len(kart_gunleri) == 9
    assert kart_gunleri == tuple(om.ERKEN_KAPANIS_GUNLERI) == mcal_gunleri


# ---------------------------------------------------------------------------
# Öz-sınama (kill-1) ve açılış↔tetik (tanı h)
# ---------------------------------------------------------------------------
def test_kill1_oz_sinama_1bps_TOLERANSI(om):
    s = om.SLIP_BPS / 10_000.0
    ic = (GIRIS - GIRIS * 0.99e-4) / (1.0 + s)
    dis = (GIRIS - GIRIS * 1.01e-4) / (1.0 + s)
    assert abs(om.oz_fark_bps(GIRIS, ic) - 0.99) < 1e-6 and om.oz_fark_bps(GIRIS, ic) <= om.OZ_SINAMA_TOL_BPS
    assert om.oz_fark_bps(GIRIS, dis) > om.OZ_SINAMA_TOL_BPS


def test_kill1_oz_sinama_20_SATIR_siniri(om):
    def rows(n_ic, n_dis):
        return ([{"oz_fark_bps": 0.3} for _ in range(n_ic)] + [{"oz_fark_bps": 2.0} for _ in range(n_dis)]
                + [{"oz_fark_bps": None}])
    assert om.oz_sinama_ozeti(rows(19, 50))["gecti"] is False
    o = om.oz_sinama_ozeti(rows(20, 0))
    assert o["gecti"] is True and o["tutarli_n"] == 20 and o["olculemedi_n"] == 1


@pytest.mark.parametrize("oran,dal", [(0.4e-4, "acilis_yakin"), (-0.4e-4, "acilis_yakin"),
                                      (0.6e-4, "acilis_ustu"), (-0.6e-4, "acilis_alti")])
def test_acilis_tetik_isareti_tani_h(om, oran, dal):
    tetik = 80.0
    giris = tetik * (1.0 + oran) * (1.0 + om.SLIP_BPS / 10_000.0)
    bps, d = om.acilis_dali(giris, tetik)
    assert d == dal and abs(bps - oran * 1e4) < 1e-6


# ---------------------------------------------------------------------------
# Karar kuralları — iki hüküm, sınırlar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("alt,ust,beklenen", [
    (5.01, 9.0, "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"),
    (5.0, 9.0, "BELİRSİZ"),                  # CI-alt TAM 5 → '> 5' değil → İYİMSER DEĞİL
    (1.0, 5.0, "DOLUM EŞDEĞER"),             # CI-üst TAM 5 → '≤ 5'
    (1.0, 5.01, "BELİRSİZ"),
    (0.0, 0.0, "DOLUM EŞDEĞER"),
])
def test_karar_H1_dallari(om, alt, ust, beklenen):
    assert om.karar_h1(alt, ust) == beklenen


@pytest.mark.parametrize("alt,ust,beklenen", [
    (5.01, 9.0, "REPLAY GİRİŞ FİYATI İYİMSER"),
    (5.0, 9.0, "BELİRSİZ"),
    (-9.0, -5.01, "REPLAY GİRİŞ FİYATI KÖTÜMSER"),
    (-9.0, -5.0, "BELİRSİZ"),
    (-5.0, 5.0, "GİRİŞ FİYATI EŞDEĞER (model yeterli)"),
    (-5.01, 3.0, "BELİRSİZ"),
    (5.0, 5.0, "GİRİŞ FİYATI EŞDEĞER (model yeterli)"),
])
def test_karar_H2_dallari(om, alt, ust, beklenen):
    assert om.karar_h2(alt, ust) == beklenen


# ---------------------------------------------------------------------------
# ozetle — paydalar, n eşikleri, kill-list
# ---------------------------------------------------------------------------
def _ozet_satirlari(n_dolan, n_dolmaz, n_seans, *, fark=12.0, fark_fn=None, n_akis_yok=0,
                    n_olcek_disi=0, buyuk_seans=0, pk3_tutarsiz=0):
    gunler = _is_gunleri("2023-01-02", n_seans)

    def satir(sinif, seans, i, f=None):
        olc = sinif != "akis_yok" or None
        return {"sinif": sinif, "seans": seans, "fark_bps": f, "dal": "GAP", "plan_dal": "GAP", "tetik": 50.0,
                "ticker": f"T{i}", "seq": i, "acilis_dal": "acilis_alti",
                "pk3_bar_yuksek": olc, "pk3_tik_yuksek": olc, "pk3_bar_dusuk": olc, "pk3_tik_dusuk": olc}
    s = []
    for i in range(n_dolan):
        s.append(satir("DOLAN", gunler[i % n_seans], i, fark_fn(i) if fark_fn else fark))
    for i in range(n_dolmaz):
        s.append(satir("DOLMAZ", gunler[i % n_seans], 10_000 + i))
    for i in range(buyuk_seans):
        s.append(satir("DOLAN", gunler[0], 20_000 + i, fark))
    for i in range(n_akis_yok):
        s.append(satir("akis_yok", gunler[i % n_seans], 30_000 + i))
    for i in range(n_olcek_disi):
        s.append(satir("olcek_disi", gunler[i % n_seans], 40_000 + i))
    olc = [r for r in s if r["pk3_tik_yuksek"] is not None]
    for r in olc[:pk3_tutarsiz]:
        r["pk3_tik_yuksek"] = False
    return s


_OZ = {"gecti": True}
_PK1 = {"gecti": True}


def test_H1_orani_DOLMAZ_PAYDADA(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 100, 100), _OZ, _PK1)
    h1 = o["h1"]
    assert h1["n"] == 400 and h1["dolmaz_n"] == 100 and h1["oran_pct"] == 25.0
    assert h1["ci95_pct"] == [25.0, 25.0] and h1["karar"] == "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"


def test_iki_hukum_AYRI_biri_digerini_EZMEZ(om):
    o = om.ozetle(_ozet_satirlari(300, 100, 100, fark=0.0), _OZ, _PK1)
    assert o["durum"] == "KOSULLU_HUKUM"
    assert o["h1"]["karar"] == "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"
    assert o["h2"]["karar"] == "GİRİŞ FİYATI EŞDEĞER (model yeterli)"
    assert o["h2"]["medyan_bps"] == 0.0 and o["h2"]["ci95_bps"] == [0.0, 0.0]
    o = om.ozetle(_ozet_satirlari(300, 0, 100, fark=-12.0), _OZ, _PK1)
    assert o["h1"]["karar"] == "DOLUM EŞDEĞER" and o["h2"]["karar"] == "REPLAY GİRİŞ FİYATI KÖTÜMSER"
    assert o["kill_list"]["tip_kaynagi"] == "plan_gunu_kapanisi"


def test_H2_medyani_yalniz_DOLAN(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 50, 100, fark_fn=lambda i: [4.0, 8.0, 12.0][i % 3]), _OZ, _PK1)
    assert o["h2"]["n"] == 300 and o["h2"]["medyan_bps"] == 8.0


def test_oran_ci_deterministik_tohuma_duyarli_ve_kumeli(om):
    rng = random.Random(9)
    kumeler = [[float(rng.random() < 0.3) for _ in range(rng.randrange(1, 6))] for _ in range(40)]
    a = om.seans_kumeli_oran_ci(kumeler, 2000, om.BOOT_TOHUM)
    assert a == om.seans_kumeli_oran_ci(kumeler, 2000, om.BOOT_TOHUM)
    assert a != om.seans_kumeli_oran_ci(kumeler, 2000, om.BOOT_TOHUM + 1)
    r2 = random.Random(om.BOOT_TOHUM)
    ref = []
    for _ in range(2000):
        sec = [x for _ in kumeler for x in kumeler[r2.randrange(len(kumeler))]]
        ref.append(sum(sec) / len(sec) * 100.0)
    ref.sort()
    assert a == (om.yuzdelik(ref, 0.025), om.yuzdelik(ref, 0.975))
    assert om.seans_kumeli_oran_ci([[0.0], [0.0, 0.0]], 50, 1) == (0.0, 0.0)


def test_n_esigi_299_OLCULEMEDI_300_gecer(om, hizli):
    o = om.ozetle(_ozet_satirlari(299, 0, 100), _OZ, _PK1)
    assert o["h1"]["durum"] == o["h2"]["durum"] == "OLCULEMEDI" and o["durum"] == "OLCULEMEDI"
    assert o["h1"]["oran_pct"] is None and o["h2"]["medyan_bps"] is None
    o = om.ozetle(_ozet_satirlari(300, 0, 100), _OZ, _PK1)
    assert o["h1"]["durum"] == o["h2"]["durum"] == "KOSULLU_HUKUM"


def test_seans_esigi_99_OLCULEMEDI(om, hizli):
    o = om.ozetle(_ozet_satirlari(400, 0, 99), _OZ, _PK1)
    assert o["h1"]["durum"] == o["h2"]["durum"] == "OLCULEMEDI"


def test_H2_paydasi_YALNIZ_DOLAN(om, hizli):
    o = om.ozetle(_ozet_satirlari(250, 50, 100), _OZ, _PK1)
    assert o["h1"]["n"] == 300 and o["h1"]["durum"] == "KOSULLU_HUKUM"
    assert o["h2"]["n"] == 250 and o["h2"]["durum"] == "OLCULEMEDI" and o["h2"]["karar"] is None
    assert o["durum"] == "KOSULLU_HUKUM"


def test_kill2_akis_yok_TAM_yuzde10_gecer_USTU_yayimlanmaz(om, hizli):
    o = om.ozetle(_ozet_satirlari(360, 0, 100, n_akis_yok=40), _OZ, _PK1)
    assert o["kill_list"]["akis_yok_asimi"] is False and o["durum"] == "KOSULLU_HUKUM"
    o = om.ozetle(_ozet_satirlari(360, 0, 100, n_akis_yok=41), _OZ, _PK1)
    assert o["kill_list"]["akis_yok_asimi"] is True and o["durum"] == "YAYIMLANMAZ"
    assert o["h1"]["oran_pct"] is None and o["h2"]["medyan_bps"] is None and o["tanilar"] is None


def test_kill3_olcek_dislanan_TAM_yuzde5_gecer_USTU_yayimlanmaz(om, hizli):
    o = om.ozetle(_ozet_satirlari(380, 0, 100, n_olcek_disi=20, n_akis_yok=5), _OZ, _PK1)
    assert o["kill_list"]["olcek_asimi"] is False and o["durum"] == "KOSULLU_HUKUM"
    o = om.ozetle(_ozet_satirlari(380, 0, 100, n_olcek_disi=21, n_akis_yok=5), _OZ, _PK1)
    assert o["kill_list"]["olcek_asimi"] is True and o["durum"] == "YAYIMLANMAZ"
    # PAYDA AYIRICI: 21 / (aday − akis_yok = 400) = %5,25 → aşım; yanlış payda 21 / aday(440) = %4,77 geçerdi
    o = om.ozetle(_ozet_satirlari(379, 0, 100, n_olcek_disi=21, n_akis_yok=40), _OZ, _PK1)
    assert o["kill_list"]["akis_yok_asimi"] is False and o["kill_list"]["olcek_dislanan_pct"] == 5.25
    assert o["kill_list"]["olcek_asimi"] is True and o["durum"] == "YAYIMLANMAZ"


def _olcek_satiri(bar_acilis, ref):
    return {"seans": G, "tetik": 50.0, "limit": 52.0, "entry": 50.0, "bar_acilis": bar_acilis, "ref_kapanis": ref}


_OLCEK_AKISI = [_kayit(_et(G, "09:40:00"), 50.0), _kayit(_et(G, "09:45:00"), 50.5),
                _kayit(_et(G, "09:45:01"), 50.1), _kayit(_et(G, "11:00:00"), 50.2)]


@pytest.mark.parametrize("bar_acilis,beklenen", [(45.0, "DOLAN"), (55.0, "DOLAN"), (44.99, "olcek_disi"),
                                                 (55.01, "olcek_disi")])
def test_kill3_acilis_tik_bandi_SINIRLARI_dahil(om, bar_acilis, beklenen):
    """oran = bar açılışı / ilk seans tiki (50,00): 45/50 = 0,9 ve 55/50 = 1,1 TAM temsil — sınır DAHİL."""
    assert 45.0 / 50.0 == 0.9 and 55.0 / 50.0 == 1.1
    r = _olcek_satiri(bar_acilis, 50.0)
    om.satir_olc(r, _OLCEK_AKISI)
    assert r["sinif"] == beklenen and r["oykunucu_sinif"] == "DOLAN"
    if beklenen == "olcek_disi":
        assert r["olcek_alt_neden"] == "acilis_tik"


@pytest.mark.parametrize("ref,beklenen", [(45.0, "DOLAN"), (55.0, "DOLAN"), (44.99, "olcek_disi"),
                                          (55.01, "olcek_disi"), (25.0, "olcek_disi")])
def test_kill3_KAPANIS_tetik_bandi_SINIRLARI_dahil(om, ref, beklenen):
    """Kartın yeni kill-3 kolu: plan günü kapanışı / tetik ∉ [0,9; 1,1] → dışlanır ve sayılır (tetik/kapanış = 2,0
    bölünme artefaktı bu sınıftır: 25 / 50 = 0,5)."""
    r = _olcek_satiri(50.0, ref)
    om.satir_olc(r, _OLCEK_AKISI)
    assert r["sinif"] == beklenen and r["oykunucu_sinif"] == "DOLAN"
    if beklenen == "olcek_disi":
        assert r["olcek_alt_neden"] == "kapanis_tetik"


def test_kill3_olculemeyen_olcek_ve_ref_DISLANIR(om):
    r = _olcek_satiri(None, 50.0)
    om.satir_olc(r, _OLCEK_AKISI)
    assert r["sinif"] == "olcek_olculemedi" and r["olcek_alt_neden"] == "bar_acilis_yok"
    r = _olcek_satiri(50.0, None)
    om.satir_olc(r, _OLCEK_AKISI)
    assert r["sinif"] == "olcek_olculemedi" and r["olcek_alt_neden"] == "ref_yok"


def test_kill4_tek_seans_TAM_yuzde10_serhsiz_USTU_serhli(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 0, 100, buyuk_seans=30), _OZ, _PK1)     # 33/330 = %10
    assert o["h2"]["tek_seans_payi"] == 0.10 and o["h2"]["ci_serh"] is None
    o = om.ozetle(_ozet_satirlari(300, 0, 100, buyuk_seans=31), _OZ, _PK1)     # 34/331
    assert o["h2"]["tek_seans_asimi"] is True and o["h2"]["ci_serh"]
    assert o["h1"]["ci_serh"] and o["h2"]["ci95_bps"] is not None
    assert any("tek seans" in k for k in o["kosullar"])


def test_kill1_oz_sinama_duserse_GECERSIZ(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 100, 100), {"gecti": False}, _PK1)
    assert o["durum"] == "GECERSIZ" and o["h1"]["oran_pct"] is None and o["h2"]["karar"] is None


def test_kill7_PK1_duserse_hicbir_sayi_yok(om, hizli):
    o = om.ozetle(_ozet_satirlari(300, 100, 100), _OZ, {"gecti": False})
    assert o["durum"] == "GECERSIZ" and o["tanilar"] is None
    assert o["h1"]["oran_pct"] is None and o["h2"]["medyan_bps"] is None


def test_kill7_PK3_TAM_yuzde20_gecer_USTU_GECERSIZ(om, hizli):
    o = om.ozetle(_ozet_satirlari(400, 0, 100, pk3_tutarsiz=80), _OZ, _PK1)
    assert o["pk3"]["dustu"] is False and o["durum"] == "KOSULLU_HUKUM"
    o = om.ozetle(_ozet_satirlari(400, 0, 100, pk3_tutarsiz=81), _OZ, _PK1)
    assert o["pk3"]["dustu"] is True and o["durum"] == "GECERSIZ"
    assert o["h1"]["oran_pct"] is None and o["h2"]["medyan_bps"] is None


def test_PK3_iki_kosul_DUSUK_yalniz_GAPta(om):
    """Kart: GAP'te bar düşüğü ≤ L ⇔ tik min ≤ L; her satırda bar yükseği ≥ tetik ⇔ tik maks ≥ tetik."""
    def satir(dal, by, ty, bd, td):
        return {"sinif": "DOLAN", "seans": G, "plan_dal": dal, "pk3_bar_yuksek": by, "pk3_tik_yuksek": ty,
                "pk3_bar_dusuk": bd, "pk3_tik_dusuk": td}
    rows = [satir("GAP", True, True, True, False),          # GAP düşük koşulu tutarsız → sayılır
            satir("STOP_LIMIT", True, True, True, False),   # STOP-LIMIT'te düşük koşulu UYGULANMAZ
            satir("STOP_LIMIT", True, False, None, None),   # yüksek tutarsız
            satir("GAP", True, True, None, True),           # GAP düşük ayağı ölçülemedi → paydada yok
            satir("GAP", True, True, True, True)]
    p = om.pk3_ozeti(rows)
    assert p["payda_n"] == 4 and p["tutarsiz_n"] == 2
    assert p["dusuk_tutarsiz_n"] == 1 and p["yuksek_tutarsiz_n"] == 1 and p["olculemedi_n"] == 1
    assert p["dustu"] is True                                # 2/4 = %50 > %20


def test_PK3_olculemezse_ayak_DUSMUS_sayilir(om, hizli):
    s = _ozet_satirlari(300, 0, 100)
    for r in s:
        r["pk3_bar_yuksek"] = None
    o = om.ozetle(s, _OZ, _PK1)
    assert o["pk3"]["payda_n"] == 0 and o["pk3"]["dustu"] is True and o["durum"] == "GECERSIZ"


def test_paydalar_BEYANI_her_kalemi_tasir(om):
    for k in ("aday", "kill1_oz_sinama", "kill2_akis_yok", "kill3_olcek", "kill4_tek_seans",
              "kill5_kosul", "kill6_tip", "kill7_pk", "h1", "h2", "n_esigi", "erken_kapanis"):
        assert k in om.PAYDALAR and len(om.PAYDALAR[k]) > 20, k


# ---------------------------------------------------------------------------
# Tik-öncesi sınıflar + girdi
# ---------------------------------------------------------------------------
def test_on_siniflar_SAYILIR_olcume_girmez(om):
    girdi = {"planlar": {"P1": [{"entry_trigger": 50.0, "stop": 48.0, "date": "2024-01-31"}],
                         "P2": [{"entry_trigger": 50.0}, {"entry_trigger": 51.0}],
                         "P3": [{"entry_trigger": None}],
                         "P4": [{"entry_trigger": 50.0, "date": "2024-07-02"}]},
             "secili": [
                 ({"seq": 1}, {"ticker": "aaa", "side": "long", "ts_open": "2024-02-01", "entry": 50.0,
                               "plan_id": "P1"}),
                 ({"seq": 2}, {"ticker": "BBB", "side": "short", "ts_open": "2024-02-01", "entry": 50.0,
                               "plan_id": "P1"}),
                 ({"seq": 3}, {"ticker": "CCC", "side": "long", "ts_open": "bozuk", "entry": 50.0}),
                 ({"seq": 4}, {"ticker": "DDD", "side": "long", "ts_open": "2024-02-01", "entry": None,
                               "plan_id": "P1"}),
                 ({"seq": 5}, {"ticker": "EEE", "side": "long", "ts_open": "2024-02-01", "entry": 50.0,
                               "plan_id": "YOK"}),
                 ({"seq": 6}, {"ticker": "FFF", "side": "long", "ts_open": "2024-02-01", "entry": 50.0,
                               "plan_id": "P2"}),
                 ({"seq": 7}, {"ticker": "GGG", "side": "long", "ts_open": "2024-02-01", "entry": 50.0,
                               "plan_id": "P3"}),
                 ({"seq": 8}, {"ticker": "HHH", "side": "long", "ts_open": "2024-07-03", "entry": 50.0,
                               "plan_id": "P4"})]}
    s = om.satirlari_hazirla(girdi)
    assert [r["sinif"] for r in s] == [None, "yon_disi", "tarih_okunamadi", "giris_okunamadi", "plan_yok",
                                       "plan_belirsiz", "tetik_okunamadi", "erken_kapanis"]
    assert s[0]["ticker"] == "AAA" and s[0]["tetik"] == 50.0 and s[0]["limit"] == 52.0
    assert s[0]["plan_tarihi"] == "2024-01-31" and s[0]["seans"] == "2024-02-01"


def test_birlestir_extra_json_KAZANIR(om):
    sayac = {"extra_json_bozuk": 0}
    b = om._birlestir({"seq": 1, "kaynak": "live_paper", "extra_json": '{"kaynak": "replay_seed"}'}, sayac)
    assert b["kaynak"] == "replay_seed" and "seq" not in b and "extra_json" not in b


# ---------------------------------------------------------------------------
# EDG-2026-102 kopyaları — AYRIŞMA ÇİVİSİ (tek-kaynak yasası, kopya kaçınılmaz: stdin tek dosya)
# ---------------------------------------------------------------------------
ZORUNLU_KOPYALAR = {"_sayi", "seans_siniri_ns", "seans_suz", "yuzdelik", "seans_kumeli_ci", "_r3", "_dagilim",
                    "_fiyat_kovasi", "_db_ac", "_birlestir", "_kanonik", "SemaHatasi", "_sema_kapisi",
                    "_sema_pyarrow", "_sema_duckdb", "_oku_pyarrow", "_oku_duckdb", "gun_oku", "bar_dosyasi",
                    "bar_oku", "okuma_sinamasi", "_icinde", "_yaz", "_json"}
ZORUNLU_SABITLER = {"FIYAT_OLCEK", "NS", "ET", "SEANS_ACILIS", "SEANS_KAPANIS", "OLCEK_BANDI", "BOOT_B",
                    "BOOT_TOHUM", "OKUNAN_SUTUNLAR", "BEKLENEN_SEMA", "_TIP_ESLEME", "KOSUL_TEK_LOT_BITI",
                    "ELLE_PENCERE", "FIYAT_KOVALARI"}


def _tanim_dokumu(kaynak: str, ad: str) -> str | None:
    """Modül düzeyindeki def/class'ın docstring'siz AST dökümü (yorum ve docstring ayrışabilir)."""
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


def test_EDG102_kopya_listesi_ZORUNLU_kumeyi_kapsar(om):
    assert ZORUNLU_KOPYALAR <= set(om.EDG102_KOPYA_TANIMLAR)
    assert ZORUNLU_SABITLER <= set(om.EDG102_KOPYA_SABITLER)


def test_EDG102_kopya_yardimcilar_AST_OZDES(om):
    a, b = BETIK.read_text(encoding="utf-8"), EDG102.read_text(encoding="utf-8")
    for ad in om.EDG102_KOPYA_TANIMLAR:
        da, db_ = _tanim_dokumu(a, ad), _tanim_dokumu(b, ad)
        assert da is not None and db_ is not None, ad
        assert da == db_, f"{ad} EDG-2026-102'den AYRIŞTI"


def test_EDG102_kopya_sabitler_ESIT(om, e102):
    for ad in om.EDG102_KOPYA_SABITLER:
        assert getattr(om, ad) == getattr(e102, ad), ad
    assert set(om.OKUYUCULAR) == set(e102.OKUYUCULAR)


def test_ayrisma_taramasi_SENTETIK_sapmayi_gorur():
    k = EDG102.read_text(encoding="utf-8")
    ad = "seans_suz"
    sapma = k.replace("if a <= r[0] < k)", "if a <= r[0] <= k)")
    assert sapma != k and _tanim_dokumu(sapma, ad) != _tanim_dokumu(k, ad)
    doc = k.replace("normal seansı süzer.", "normal seansı süzer (başka söz).")
    assert doc != k and _tanim_dokumu(doc, ad) == _tanim_dokumu(k, ad)


def test_EDG102_kopyalari_AYNI_girdide_AYNI_cikti(om, e102, tmp_path):
    for g in ("2024-01-10", "2024-03-08", "2024-03-11", "2024-11-01", "2024-11-04"):
        d = dt.date.fromisoformat(g)
        assert om.seans_siniri_ns(d) == e102.seans_siniri_ns(d)
    rng = random.Random(550)
    g, d = "2024-03-11", dt.date(2024, 3, 11)
    kay = [_kayit(_et(g, "16:00:00"), 50.0), _kayit(_et(g, "09:30:00"), 49.0)]
    for _ in range(300):
        saat = f"{rng.randrange(7, 18):02d}:{rng.randrange(60):02d}:{rng.randrange(60):02d}"
        kay.append(_kayit(_et(g, saat), round(rng.uniform(40, 60), 4), kosul=rng.choice([0, 0x20])))
    assert om.seans_suz(kay, d) == e102.seans_suz(kay, d)
    v = sorted(rng.gauss(0, 10) for _ in range(51))
    for q in (0.0, 0.025, 0.5, 0.975, 1.0):
        assert om.yuzdelik(v, q) == e102.yuzdelik(v, q)
    assert om.yuzdelik([], 0.5) == e102.yuzdelik([], 0.5)
    kumeler = [[rng.gauss(5, 9) for _ in range(rng.randrange(1, 5))] for _ in range(12)]
    assert om.seans_kumeli_ci(kumeler) == e102.seans_kumeli_ci(kumeler)
    assert om._dagilim(v) == e102._dagilim(v) and om._dagilim([]) == e102._dagilim([])
    for p in (0.5, 25.0, 99.99, 100.0, 1e6):
        assert om._fiyat_kovasi(p) == e102._fiyat_kovasi(p)
    for x in (None, True, "3.5", "abc", float("nan"), 7, "inf", 2.25):
        assert om._sayi(x) == e102._sayi(x)
    ham = {"seq": 3, "kaynak": "live_paper", "entry": 10.0, "x": None,
           "extra_json": '{"kaynak": "replay_seed", "y": 1}'}
    sa, sb = {"extra_json_bozuk": 0}, {"extra_json_bozuk": 0}
    assert om._birlestir(ham, sa) == e102._birlestir(ham, sb)
    om._birlestir({"seq": 4, "extra_json": "{bozuk"}, sa)
    e102._birlestir({"seq": 4, "extra_json": "{bozuk"}, sb)
    assert sa == sb == {"extra_json_bozuk": 1}
    obj = {"b": [1, 2.5, "ş"], "a": None}
    assert om._kanonik(obj) == e102._kanonik(obj) and om._json(obj) == e102._json(obj)
    db = tmp_path / "x.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (a, b)")
    con.execute("INSERT INTO t VALUES (1, 'x')")
    con.commit()
    con.close()
    for m in (om, e102):
        c = m._db_ac(db)
        try:
            assert c.execute("SELECT * FROM t").fetchall() == [{"a": 1, "b": "x"}]
            with pytest.raises(sqlite3.OperationalError):
                c.execute("INSERT INTO t VALUES (2, 'y')")
        finally:
            c.close()
    yol = tmp_path / "tik" / f"{g}.parquet"
    satirlar = []
    for i, (ts, fiyat, lot, kosul, ka, ks) in enumerate(kay[:60]):
        satirlar.append((ts, ("AAA", "BBB", "CCC")[i % 3], fiyat, lot, kosul, ts, ka, 100, ks, 100))
    _parquet_yaz(yol, satirlar)
    sema = om._sema_duckdb(yol)
    assert sema == e102._sema_duckdb(yol)
    om._sema_kapisi(sema, yol)
    e102._sema_kapisi(sema, yol)
    bozuk = {**sema, "fiyat": "DOUBLE"}
    with pytest.raises(om.SemaHatasi) as ea:
        om._sema_kapisi(bozuk, yol)
    with pytest.raises(e102.SemaHatasi) as eb:
        e102._sema_kapisi(bozuk, yol)
    assert str(ea.value) == str(eb.value)
    assert om.gun_oku(yol, {"AAA", "BBB", "YOK"}, "duckdb") == e102.gun_oku(yol, {"AAA", "BBB", "YOK"}, "duckdb")
    uygun = [{"seans": g, "ticker": "AAA"}, {"seans": g, "ticker": "CCC"}]
    oa = om.okuma_sinamasi(yol.parent, uygun, [g], {"gun_dosyasi_yok": []}, "duckdb")
    ob = e102.okuma_sinamasi(yol.parent, uygun, [g], {"gun_dosyasi_yok": []}, "duckdb")
    oa.pop("sure_sn")
    ob.pop("sure_sn")
    assert oa == ob
    kok = tmp_path / "bars"
    _bar_yaz(kok, "BRK.B", {"2024-03-08": (1.0, 2.0, 0.5, 1.5), "2024-03-11": (1.5, 2.5, 1.0, 2.0)})
    assert om.bar_dosyasi(kok, "BRK.B") == e102.bar_dosyasi(kok, "BRK.B")
    assert om.bar_oku(kok, "BRK.B", {}) == e102.bar_oku(kok, "BRK.B", {})
    assert om.bar_oku(kok, "YOK", {}) is None and e102.bar_oku(kok, "YOK", {}) is None
    for a_, b_ in ((tmp_path / "a" / "b", tmp_path / "a"), (tmp_path / "a", tmp_path / "a"),
                   (tmp_path / "x", tmp_path / "a")):
        assert om._icinde(a_, b_) == e102._icinde(a_, b_)


# ---------------------------------------------------------------------------
# Kaynak metin: meridian İÇE AKTARILMAZ, yalnız stdlib + pyarrow (+ duckdb okuyucusu)
# ---------------------------------------------------------------------------
def _ithal_kokleri(yol=None) -> set[str]:
    agac = ast.parse((yol or BETIK).read_text(encoding="utf-8"))
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
    assert "meridian" not in kokler and "__import__" not in kokler and "importlib" not in kokler
    izinli = set(sys.stdlib_module_names) | {"pyarrow", "duckdb"}
    assert kokler <= izinli, kokler - izinli
    assert {"pyarrow", "sqlite3"} <= kokler
    assert "numpy" not in kokler and "pandas" not in kokler and "pandas_market_calendars" not in kokler


def test_ithal_tarayicisi_SENTETIK_ihlali_gorur(tmp_path):
    sahte = tmp_path / "olcum.py"
    sahte.write_text("import json\nfrom meridian import broker\n", encoding="utf-8")
    assert "meridian" in _ithal_kokleri(sahte)


# ---------------------------------------------------------------------------
# Uçtan uca (CLI) — sentetik DB + parquet + bar
# ---------------------------------------------------------------------------
def test_uctan_uca_iki_birincil_karar_ve_tanilar(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path)
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    o = s["ozet"]
    assert s["girdi"]["n_trades_filtreli"] == 500 and s["girdi"]["sql_capraz_n"] == 500
    assert s["girdi"]["n_trades_tum"] == 501 and s["girdi"]["n_plan_satiri"] == 500
    assert o["siniflar"]["DOLAN"] == 400 and o["siniflar"]["DOLMAZ"] == 100
    assert o["siniflar"]["akis_yok"] == 0 and o["siniflar"]["olcek_disi"] == 0
    assert o["siniflar"]["olcek_olculemedi"] == 0 and o["siniflar"]["erken_kapanis"] == 0
    assert o["durum"] == "KOSULLU_HUKUM"
    h1, h2 = o["h1"], o["h2"]
    assert h1["oran_pct"] == 20.0 and h1["ci95_pct"] == [20.0, 20.0] and h1["n_seans"] == 100
    assert h1["karar"] == "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"
    assert abs(h2["medyan_bps"] - 12.0) < 1e-9 and h2["ci95_bps"] == [12.0, 12.0]
    assert h2["karar"] == "REPLAY GİRİŞ FİYATI İYİMSER" and h2["n"] == 400
    assert s["oz_sinama"]["gecti"] is True and s["oz_sinama"]["tutarli_n"] == 500
    assert s["pk"]["pk1"]["gecti"] is True
    assert s["pk"]["pk3"]["tutarsiz_n"] == 0 and s["pk"]["pk3"]["payda_n"] == 500
    assert o["kill_list"]["tip_kaynagi"] == "plan_gunu_kapanisi"
    dallar = {r["ticker"]: r["dal"] for r in s["satirlar"]}
    assert dallar == {"AAA": "GAP", "BBB": "STOP_LIMIT", "CCC": "STOP_LIMIT", "DDD": "STOP_LIMIT", "EEE": "GAP"}
    eee = [r for r in s["satirlar"] if r["ticker"] == "EEE"]
    assert all(r["sinif"] == "DOLAN" and r["p0"] < TETIK and r["canli_dolum"] == 49.45 for r in eee)
    t = o["tanilar"]
    assert t["a_dal_kirilimi"]["GAP"]["n"] == 200 and t["a_dal_kirilimi"]["GAP"]["dolmaz_n"] == 0
    assert t["a_dal_kirilimi"]["STOP_LIMIT"]["dolmaz_n"] == 100
    b = t["b_0930_varyanti"]          # 09:30'da AAA +100 · BBB −100 · CCC +12 · EEE −120 bps; DDD DOLMAZ
    assert b["dolmaz_n"] == 100 and b["fark_medyan_bps"] == -44.0
    assert b["dal_sayimi"] == {"GAP": 200, "STOP_LIMIT": 300}
    assert t["c_gecikme_dk"]["dolum"]["n"] == 400
    assert t["d_yil"]["2024"]["n"] == 500
    assert t["e_kosul_0x20_disi"]["n"] == 500
    assert t["f_dolum_ani_spread_bps"]["n"] == 400
    assert t["g_dolmaz_replay_sonucu"]["exit_reason"] == {"stop": 100}
    h = t["h_acilis_tetik_isareti"]
    assert set(h) == {"acilis_alti"} and h["acilis_alti"]["n"] == 500 and h["acilis_alti"]["fark_medyan_bps"] == 12.0
    dokum = (sahne["cikti"] / "girdi_trades.json").read_bytes()
    assert hashlib.sha256(dokum).hexdigest() == s["girdi"]["trades_sha256"]
    plan = (sahne["cikti"] / "girdi_planlar.json").read_bytes()
    assert hashlib.sha256(plan).hexdigest() == s["girdi"]["planlar_sha256"]
    md = (sahne["cikti"] / "OZET.md").read_text(encoding="utf-8")
    assert "EDG-2026-105" in md and "REPLAY DOLUMU İYİMSER" in md and "REPLAY GİRİŞ FİYATI İYİMSER" in md
    assert s["paydalar"] == om.PAYDALAR and re.fullmatch(r"[0-9a-f]{64}", s["parmak_izi"])


def test_uctan_uca_KIMLIK_sifir_fark_ve_dolmazsiz_ESDEGER(om, sandbox_state, tmp_path):
    sahne = _sahne(tmp_path, dolum=50.0, dolmaz=False)
    assert _kos(om, sahne) == 0
    o = _sonuc(sahne)["ozet"]
    assert o["h1"]["oran_pct"] == 0.0 and o["h1"]["karar"] == "DOLUM EŞDEĞER"
    assert o["h2"]["medyan_bps"] == 0.0 and o["h2"]["ci95_bps"] == [0.0, 0.0]
    assert o["h2"]["karar"] == "GİRİŞ FİYATI EŞDEĞER (model yeterli)"


def test_kill5_birincil_KOSULDAN_bagimsiz_tani_e_bagimli(om, sandbox_state, tmp_path):
    a = _sahne(tmp_path / "a", kosul=0)
    b = _sahne(tmp_path / "b", kosul=0x20)
    assert _kos(om, a) == 0 and _kos(om, b) == 0
    sa, sb = _sonuc(a), _sonuc(b)
    for k in ("h1", "h2", "siniflar"):
        assert sa["ozet"][k] == sb["ozet"][k], k
    assert [(r["sinif"], r.get("fark_bps")) for r in sa["satirlar"]] == \
           [(r["sinif"], r.get("fark_bps")) for r in sb["satirlar"]]
    ta, tb = sa["ozet"]["tanilar"]["e_kosul_0x20_disi"], sb["ozet"]["tanilar"]["e_kosul_0x20_disi"]
    assert ta["n"] == 500 and tb["n"] == 0 and tb["digeri_n"] == 500
    assert sa["ozet"]["kill_list"]["kosul_birincilde"] is False


def _kucuk(tmp_path, **kw):
    return _sahne(tmp_path, gun_sayisi=6, **kw)


def test_n_esigi_uctan_uca_KUCUK_sahne_OLCULEMEDI(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    assert _kos(om, sahne) == 0
    o = _sonuc(sahne)["ozet"]
    assert o["durum"] == "OLCULEMEDI" and o["h1"]["karar"] is None and o["h2"]["karar"] is None
    assert o["siniflar"]["DOLAN"] == 24 and o["siniflar"]["DOLMAZ"] == 6


def test_erken_kapanis_gunu_girisleri_uctan_uca_DISLANIR_sayilir(om, sandbox_state, tmp_path):
    """2024-07-03 XNYS 13:00 kapanışı: o günün 5 girişi birincile GİRMEZ, `erken_kapanis` sınıfında sayılır."""
    sahne = _sahne(tmp_path, gun_sayisi=6, bas="2024-07-01")
    assert "2024-07-03" in sahne["gunler"]
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    o = s["ozet"]
    assert o["siniflar"]["erken_kapanis"] == 5 and o["kill_list"]["erken_kapanis_n"] == 5
    assert o["n_aday"] == 25 and o["siniflar"]["DOLAN"] + o["siniflar"]["DOLMAZ"] == 25
    assert {r["seans"] for r in s["satirlar"] if r["sinif"] == "erken_kapanis"} == {"2024-07-03"}
    assert o["pk3"]["payda_n"] == 25


def test_gun_dosyasi_yoksa_AKIS_YOK_sayilir(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    (sahne["tick"] / f"{sahne['gunler'][2]}.parquet").unlink()
    assert _kos(om, sahne) == 0
    s = _sonuc(sahne)
    assert s["ozet"]["siniflar"]["akis_yok"] == 5
    assert {r["alt_neden"] for r in s["satirlar"] if r["sinif"] == "akis_yok"} == {"gun_dosyasi_yok"}
    assert s["ozet"]["kill_list"]["akis_yok_asimi"] is True and s["ozet"]["durum"] == "YAYIMLANMAZ"


def test_uctan_uca_yazim_YALNIZ_cikti_altinda(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    once = _agac_fotografi(tmp_path, sahne["cikti"])
    assert _kos(om, sahne) == 0
    assert _agac_fotografi(tmp_path, sahne["cikti"]) == once
    yazilan = sorted(p.name for p in sahne["cikti"].rglob("*") if p.is_file())
    assert yazilan == sorted(om.CIKTI_DOSYALARI)


def test_cikti_girdi_agacinin_icindeyse_REDDEDER(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    for icerisi in (sahne["state"] / "olcum", sahne["tick"].parent / "x", sahne["bars"] / "y"):
        sahne["cikti"] = icerisi
        assert _kos(om, sahne) == 2
        assert not icerisi.exists()


def test_mevcut_sonuc_UZERINE_YAZILMAZ(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    sahne["cikti"].mkdir(parents=True)
    (sahne["cikti"] / "sonuc.json").write_text("{}", encoding="utf-8")
    assert _kos(om, sahne) == 2
    assert (sahne["cikti"] / "sonuc.json").read_text(encoding="utf-8") == "{}"


def test_girdi_dokumu_sha256_KARARLI_ve_ICERIGE_duyarli(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    sahne["cikti"] = tmp_path / "c1"
    assert _kos(om, sahne) == 0
    s1 = _sonuc(sahne)
    sahne["cikti"] = tmp_path / "c2"
    assert _kos(om, sahne) == 0
    s2 = _sonuc(sahne)
    assert s1["girdi"]["trades_sha256"] == s2["girdi"]["trades_sha256"]
    assert s1["girdi"]["planlar_sha256"] == s2["girdi"]["planlar_sha256"]
    assert s1["parmak_izi"] == s2["parmak_izi"]
    con = sqlite3.connect(str(sahne["db"]))
    con.execute("UPDATE trade_plans SET entry_trigger = 50.01 WHERE seq = 1")
    con.commit()
    con.close()
    sahne["cikti"] = tmp_path / "c3"
    assert _kos(om, sahne) == 0
    s3 = _sonuc(sahne)
    assert s3["girdi"]["trades_sha256"] == s1["girdi"]["trades_sha256"]
    assert s3["girdi"]["planlar_sha256"] != s1["girdi"]["planlar_sha256"]


def test_elle_ornek_KOTALI_deterministik_ve_kanitli(om, sandbox_state, tmp_path):
    a = _kucuk(tmp_path / "a")
    b = _kucuk(tmp_path / "b")
    assert _kos(om, a, "--elle-ornek", "6") == 0 and _kos(om, b, "--elle-ornek", "6") == 0
    pa, pb = _sonuc(a)["pk"]["pk2"], _sonuc(b)["pk"]["pk2"]
    oa = pa["ornekler"]
    assert len(oa) == 6 and pa["kota_karsilandi"] is True
    assert [(x["ticker"], x["seans"]) for x in oa] == [(x["ticker"], x["seans"]) for x in pb["ornekler"]]
    assert sum(1 for x in oa if x["dal"] == "GAP") >= 4
    assert sum(1 for x in oa if x["dal"] == "STOP_LIMIT") >= 1
    assert sum(1 for x in oa if x["sinif"] == "DOLMAZ") >= 1
    for x in oa:
        rol = {k["rol"]: k for k in x["dilim"] if k["rol"]}
        assert rol["t0"]["ts_ns"] >= x["pencere_ns"][0] and x["ref_kapanis"] is not None
        if x["sinif"] == "DOLAN":
            assert rol["dolum"]["fiyat"] == x["canli_dolum"] <= x["limit"]
            assert rol["dolum"]["i"] > (rol["aktivasyon"]["i"] if x["dal"] == "STOP_LIMIT" else rol["t0"]["i"])
        if x["dal"] == "STOP_LIMIT" and "aktivasyon" in rol:
            assert rol["aktivasyon"]["fiyat"] >= x["tetik"]
    assert pa["durum"] == "ROL1_ELLE_DOGRULAMA_BEKLIYOR"
    assert _sonuc(a)["parmak_izi"] == _sonuc(b)["parmak_izi"]
    iz_elle = _sonuc(b)["parmak_izi"]
    a["cikti"] = tmp_path / "a" / "tam"
    assert _kos(om, a) == 0
    tam = _sonuc(a)
    assert tam["parmak_izi"] == iz_elle
    assert tam["pk"]["pk2"]["ornekler"] == [] and tam["pk"]["pk2"]["kota_karsilandi"] is None


def test_PK2_kotasi_SANSA_birakilmaz(om, tmp_path, monkeypatch):
    """Kart: '≥4 GAP, varsa STOP-LIMIT, varsa ≥1 DOLMAZ'. n = 6 = 4 + 1 + 1: tek DOLMAZ satırı 52'lik havuzda —
    kota olmadan 25 tohumun HEPSİNDE ona denk gelmek ≈ (1/52)^25; kota tohumdan BAĞIMSIZ getirir. DOLAN öncelikli."""
    gunler = _is_gunleri("2024-02-01", 30)
    s = []
    for i in range(28):
        s.append({"sinif": "DOLAN", "dal": "GAP", "seans": gunler[i], "ticker": "G", "seq": i})
        s.append({"sinif": "DOLAN", "dal": "STOP_LIMIT", "seans": gunler[i], "ticker": "S", "seq": 100 + i})
    s.append({"sinif": "DOLMAZ", "dal": "GAP", "seans": gunler[5], "ticker": "D", "seq": 999})
    s += [{"sinif": "akis_yok", "seans": gunler[0], "ticker": "Y", "seq": 1000}]
    for tohum in range(25):
        monkeypatch.setattr(om, "BOOT_TOHUM", tohum)
        p = om.pk2_ornekler(s, 6, tmp_path)
        secim = [(x["ticker"], x["sinif"]) for x in p["ornekler"]]
        assert len(secim) == 6 and p["kota_karsilandi"] is True, tohum
        assert secim.count(("G", "DOLAN")) == 4 and secim.count(("S", "DOLAN")) == 1, tohum
        assert secim.count(("D", "DOLMAZ")) == 1 and p["kota"]["DOLMAZ"] == 1, tohum
    yalniz_gap = [r for r in s if r["ticker"] in ("G", "Y")]           # STOP-LIMIT ve DOLMAZ yok → 'varsa'
    p = om.pk2_ornekler(yalniz_gap, 6, tmp_path)
    assert len(p["ornekler"]) == 6 and p["kota_karsilandi"] is True and p["kota"]["GAP"] == 6
    k = om.pk2_ornekler(s, 3, tmp_path)
    assert len(k["ornekler"]) == 3 and k["kota_karsilandi"] is False
    assert om.pk2_ornekler(s, 0, tmp_path)["ornekler"] == []


def test_kuru_kip_birincilsiz_kapsam_tip_ve_dal_dagilimi(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    (sahne["tick"] / f"{sahne['gunler'][1]}.parquet").unlink()
    assert _kos(om, sahne, "--kuru") == 0
    k = json.loads((sahne["cikti"] / "kuru.json").read_text(encoding="utf-8"))
    assert k["kip"] == "kuru" and k["aday_n"] == 30 and k["seans_n"] == 6
    assert k["oz_sinama"]["gecti"] is True and k["oz_sinama"]["tutarli_n"] == 30
    assert k["kapsam"]["gun_dosyasi_yok"] == [sahne["gunler"][1]]
    assert k["kapsam"]["sema_uygun_gun"] == 5 and k["kapsam"]["bar_dosyasi_yok"] == []
    o = k["okuma_sinamasi"]
    assert o["gun"] == sahne["gunler"][0] and o["sure_sn"] >= 0 and o["bayt"] > 0
    assert o["sembol"]["AAA"] == {"kayit": 5, "seans_kaydi": 4}
    assert k["plan_tipi_dagilimi"] == {"GAP": 12, "STOP_LIMIT": 18, "ref_yok": 0}
    assert k["tetik_ref_esit_n"] == 12 and k["kapanis_tetik_bandi_disi_n"] == 0
    assert k["acilis_tetik_dal_dagilimi"] == {"acilis_alti": 30}
    assert k["siniflar_tik_oncesi"]["erken_kapanis"] == 0
    assert not (sahne["cikti"] / "sonuc.json").exists()
    yazilan = sorted(p.name for p in sahne["cikti"].rglob("*") if p.is_file())
    assert yazilan == sorted(om.KURU_DOSYALARI)


def test_CLI_dosya_kipi_operatorun_kosacagi_bicimde(sandbox_state, tmp_path):
    """CLAUDE.md §6: araç operatörün koşacağı BİÇİMDE koşulur (alt süreç, argv)."""
    sahne = _kucuk(tmp_path)
    p = subprocess.run([sys.executable, str(BETIK), "--db", str(sahne["db"]),
                        "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                        "--cikti", str(sahne["cikti"]), "--okuyucu", "duckdb"],
                       capture_output=True, text=True, timeout=300, cwd=str(tmp_path))
    assert p.returncode == 0, p.stderr[-2000:]
    s = _sonuc(sahne)
    assert s["arac"]["kip"] == "dosya" and s["kart"] == "EDG-2026-105"
    assert s["arac"]["betik_sha256"] == hashlib.sha256(BETIK.read_bytes()).hexdigest()
    assert "H1" in p.stdout and "H2" in p.stdout


def _stdin_kos(*args, cwd="/"):
    return subprocess.run([sys.executable, "-", *args], input=BETIK.read_bytes(), cwd=cwd,
                          capture_output=True, timeout=300)


def test_stdin_kipi_ARGV_ayrisir_ve_sha_BEYANI_sonuca_yazilir(sandbox_state, tmp_path):
    """A1 sözleşmesi `python - args < olcum.py`: sys.argv[0] = '-' ve `__file__` = '<stdin>'."""
    sahne = _kucuk(tmp_path)
    sha = hashlib.sha256(BETIK.read_bytes()).hexdigest()
    r = _stdin_kos("--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                   "--cikti", str(sahne["cikti"]), "--okuyucu", "duckdb", "--elle-ornek", "6",
                   "--betik-sha256", sha)
    assert r.returncode == 0, r.stderr.decode()[-2000:]
    s = _sonuc(sahne)
    assert s["arac"]["kip"] == "stdin" and s["arac"]["betik_sha256"] is None
    assert s["arac"]["betik_sha256_beyan"] == sha and s["arac"]["betik_sha256_neden"]
    assert len(s["pk"]["pk2"]["ornekler"]) == 6
    assert s["arac"]["okuyucu"] == "duckdb"


def test_stdin_kipi_sha_BEYANSIZ_reddedilir(sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    r = _stdin_kos("--db", str(sahne["db"]), "--tick-kok", str(sahne["tick"]), "--bar-kok", str(sahne["bars"]),
                   "--cikti", str(sahne["cikti"]), "--okuyucu", "duckdb")
    assert r.returncode == 2 and b"--betik-sha256" in r.stdout, (r.returncode, r.stdout[-500:])
    assert not sahne["cikti"].exists()


def test_stdin_kipi_kok_dizinden_help_KURULUR():
    r = _stdin_kos("--help")
    assert r.returncode == 0, r.stderr.decode()[-400:]
    assert b"--betik-sha256" in r.stdout and b"--tick-kok" in r.stdout


def test_dosya_kipi_YANLIS_sha_beyani_reddedilir(om, sandbox_state, tmp_path):
    sahne = _kucuk(tmp_path)
    assert _kos(om, sahne, "--betik-sha256", "0" * 64) == 2
    assert _kos(om, sahne, "--betik-sha256", "kisa") == 2
    assert not sahne["cikti"].exists()
    sha = hashlib.sha256(BETIK.read_bytes()).hexdigest()
    assert _kos(om, sahne, "--betik-sha256", sha) == 0
