"""test_edg094_r_yeniden_v492.py — EDG-2026-094 ADIM-1 ölçümü + ADIM-2 yazım betiği çivileri.

vNNN KİMLİK KAYDI: v492 seçildi çünkü ölçüm anında (2026-09-14)
`grep -rn v492 tests/ ops/ meridian/ research/` HİÇBİR eşleşme vermedi — çakışma yok, taşıma yok
(CLAUDE.md §2 vNNN kimlik kuralı). Komşu v490 EDG-093'e aittir, dokunulmadı.

NE ÇİVİLER. İki betik, iki dünya:
  * ölçüm — `research/olcumler/edg094_r_yeniden/olc.py` (SALT-OKUR): R1 kapsam, R2 giriş adedi,
    R3 stop kaynağı, R4 R yeniden hesabı, R5 eşik alanları, R6 pozitif kontroller;
  * yazım — `ops/r_giris_yeniden_yaz.py`: PK-3, yani kuru koşumun defteri DEĞİŞTİRMEDİĞİ,
    uygula koşumunun YALNIZ `extra_json`ı değiştirdiği ve ikinci koşumun 0 satır yazdığı.

ÖLÇÜLEN SAYI DEĞİL SÖZLEŞME. Gerçek defterdeki sayılar A1 kopyasından doğar (T9, ortam
değişkeniyle açılan tek çivi); buradaki sentetik veriler yalnız HESAP YOLUNU ve KAPSAMI ölçer.
Sentetik DB şeması gerçek defterin `sqlite_master` dökümünden alınmıştır (aşağıdaki DDL
dizgeleri) — motorun şema üreticisi ÇAĞRILMAZ, çünkü çivinin ölçtüğü şey ölçüm betiğinin bu
şemayı okuyabilmesidir, üreticinin kendisi değil.

NEDEN SUBPROCESS (yalnız yazım betiği için). `ops/` sözleşmesi KOMUT SATIRIdır, `main()` değil
(CLAUDE.md §1, vaka 2026-08-30: 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu). Bu yüzden
yazım betiği operatörün koşacağı BİÇİMDE, çıkış koduyla birlikte sınanır. Ölçüm betiği ise
`sasi_yukleyici.kaynaktan_yukle` ile (conftest'in betikten_modul_yukle adıyla dışa verdiği
yardımcı) KAYNAKTAN derlenerek yüklenir — ham `exec_module` yasağı v334'tedir.

AĞ YOK, CANLI DEFTER YOK: hiçbir çivi ağa çıkmaz; ölçüm betiği `meridian.*` ithal etmez, yani
`obs` yolu hiç kurulmaz. T9 gerçek verinin SALT-OKUR KOPYASINI okur ve çıktısını depo DIŞINA
(scratchpad) yazar.

MUTASYON KANITI bu dosyada KOŞMAZ; Rol-1'e teslim raporunda tablo hâlinde durur (CLAUDE.md §6).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

import pytest
import yaml

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
OLC = REPO / "research" / "olcumler" / "edg094_r_yeniden" / "olc.py"
OPS = REPO / "ops" / "r_giris_yeniden_yaz.py"
KART = REPO / "research" / "cards" / "EDG-2026-094-gecmis-r-giris-riski-paydasi-yeniden-hesap.yaml"

#: GERÇEK ŞEMANIN BİREBİR DÖKÜMÜ (A1 defter kopyasının `sqlite_master` satırları, 2026-09-14).
TRADES_DDL = (
    'CREATE TABLE trades (  seq INTEGER PRIMARY KEY,  "id" TEXT,  "plan_id" TEXT,  '
    '"ticker" TEXT,  "side" TEXT,  "ts_open" TEXT,  "ts_close" TEXT,  "entry" REAL,  '
    '"exit" REAL,  "qty" INTEGER,  "r_multiple" REAL,  "r_multiple_expected" REAL,  '
    '"pnl_pct" REAL,  "pnl_dollars" REAL,  "costs" REAL,  "exit_reason" TEXT,  '
    '"strategy_version" INTEGER,  "regime" TEXT,  "setup" TEXT,  "score" INTEGER,  '
    '"exploration" INTEGER,  "scaled_out" INTEGER,  "bars_held" INTEGER,  "mfe_r" REAL,  '
    '"mae_r" REAL,  "kaynak" TEXT,  extra_json TEXT)')
PLANS_DDL = (
    'CREATE TABLE trade_plans (  seq INTEGER PRIMARY KEY,  "id" TEXT,  "date" TEXT,  '
    '"ticker" TEXT,  "side" TEXT,  "entry_trigger" REAL,  "stop" REAL,  '
    '"profit_target" REAL,  "size_r" REAL,  "r_multiple_expected" REAL,  '
    '"regime_at_plan" TEXT,  "strategy_version" INTEGER,  "sector" TEXT,  "score" INTEGER,  '
    '"setup" TEXT,  "gate_verdict" TEXT,  "broker_status" TEXT,  "dormant_setup" INTEGER,  '
    '"exploration" INTEGER,  "p_win_shadow" REAL,  extra_json TEXT)')


@pytest.fixture
def olc_mod(sandbox_state):
    """Ölçüm betiği — KAYNAKTAN derlenmiş modül. `sandbox_state` bağımlılığı kolaylık değil
    kapıdır: fikstür `config.STATE`i tmp'ye çevirir, yani bu dosyadaki hiçbir çivi canlı
    deftere bakamaz (CLAUDE.md §2)."""
    return betikten_modul_yukle(OLC, "edg094_olc")


# ---------------------------------------------------------------------------
# sentetik defter kurucuları
# ---------------------------------------------------------------------------
def _db_kur(yol, trades, plans=()):
    """Sentetik `trades`/`trade_plans` defteri kurar ve yolunu döner."""
    con = sqlite3.connect(str(yol))
    con.execute(TRADES_DDL)
    con.execute(PLANS_DDL)
    for t in trades:
        sut = ", ".join(f'"{k}"' for k in t)
        con.execute(f"INSERT INTO trades ({sut}) VALUES ({', '.join('?' * len(t))})",
                    tuple(t.values()))
    for p in plans:
        sut = ", ".join(f'"{k}"' for k in p)
        con.execute(f"INSERT INTO trade_plans ({sut}) VALUES ({', '.join('?' * len(p))})",
                    tuple(p.values()))
    con.commit()
    con.close()
    return pathlib.Path(yol)


def _islem(seq=1, **ek):
    """Varsayılan canlı işlem: entry 100, stop 90 (planla), qty 20 → hisse-başı risk 10."""
    t = {"seq": seq, "id": f"T{seq:05d}", "plan_id": f"P-{seq}", "ticker": "AAA", "side": "long",
         "ts_open": "2026-09-01", "ts_close": "2026-09-05", "entry": 100.0, "exit": 112.5,
         "qty": 20, "r_multiple": 1.25, "pnl_dollars": 250.0, "scaled_out": 0,
         "kaynak": "live_paper", "extra_json": None}
    t.update(ek)
    return t


def _plan(pid="P-1", stop=90.0, ticker="AAA"):
    """`seq` plan kimliğinden DETERMİNİSTİK türer — `hash()` süreç tohumuyla değişir ve
    birincil anahtar çakışmasını rastgele bir teste taşırdı."""
    seq = int(hashlib.sha256(pid.encode("utf-8")).hexdigest()[:8], 16) % 9000 + 10
    return {"seq": seq, "id": pid, "date": "2026-09-01", "ticker": ticker, "side": "long",
            "entry_trigger": 100.0, "stop": stop, "size_r": 1.0}


def _olaylar_yaz(yol, olaylar):
    pathlib.Path(yol).write_text(json.dumps(olaylar, ensure_ascii=False), encoding="utf-8")
    return pathlib.Path(yol)


def _benimseme(ticker="AAA", ts="2026-09-03T20:00:00+00:00", onceki=17.0, yeni=38):
    return {"ts": ts, "level": "warn", "event": "adet_benimsendi", "ticker": ticker,
            "onceki": onceki, "yeni": yeni, "drift_sinifi": "kitap_kaydi", "detail": ""}


def _kos(olc_mod, tmp_path, trades, plans=(), olaylar=(), kaynak="live_paper"):
    """Sentetik defteri kurup ölçümü koşar; sonuç sözlüğünü döner."""
    db = _db_kur(tmp_path / "defter.db", trades, plans)
    ol = _olaylar_yaz(tmp_path / "olaylar.json", list(olaylar))
    return olc_mod.olc(db, ol, kaynak)


# ---------------------------------------------------------------------------
# T1 — R1 kapsam
# ---------------------------------------------------------------------------
def test_T1a_REPLAY_SATIRI_KAPSAM_DISI(olc_mod, tmp_path):
    """replay tohumu satırı canlı ölçüme GİRMEZ (kart kill-list 4)."""
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1), _islem(2, kaynak="replay_seed", plan_id="P-2")],
                 plans=[_plan("P-1"), _plan("P-2")])
    assert sonuc["ozet"]["n"] == 1
    assert [s["id"] for s in sonuc["satirlar"]] == ["T00001"]
    assert sonuc["kaynak_suzgeci"] == "live_paper"


def test_T1b_BILINMEYEN_KAYNAK_OLCUMU_DURDURUR(olc_mod, tmp_path):
    """Bilinmeyen `kaynak` değeri sessizce 'canlı değil' sayılmaz — ölçüm DURUR."""
    with pytest.raises(ValueError, match="R1 DURDU"):
        _kos(olc_mod, tmp_path, [_islem(1), _islem(2, kaynak="paper_sim", plan_id="P-2")],
             plans=[_plan("P-1")])


# ---------------------------------------------------------------------------
# T2 — R2 giriş adedi
# ---------------------------------------------------------------------------
def test_T2a_BENIMSEMESIZ_QTY_GIRIS_TRADES_QTY(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")])
    s = sonuc["satirlar"][0]
    assert (s["qty_giris"], s["qty_giris_kaynak"], s["benimsenmis_mi"]) == (20.0, "trades.qty", False)


def test_T2b_BENIMSENMIS_SON_YENI_ALINIR(olc_mod, tmp_path):
    """Pencere içindeki benimseme olayı (17 → 38) giriş adedini belirler."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, qty=38, pnl_dollars=-500.0,
                                            r_multiple=-500.0 / 170.0)],
                 plans=[_plan("P-1")], olaylar=[_benimseme()])
    s = sonuc["satirlar"][0]
    assert (s["qty_giris"], s["qty_giris_kaynak"], s["benimsenmis_mi"]) == (38.0, "adet_benimsendi", True)


def test_T2c_PENCERE_DISI_OLAY_SAYILMAZ(olc_mod, tmp_path):
    """Kapanıştan SONRA düşen benimseme bu işlemin adedini değiştirmez."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")],
                 olaylar=[_benimseme(ts="2026-09-09T20:00:00+00:00", yeni=38)])
    s = sonuc["satirlar"][0]
    assert s["benimsenmis_mi"] is False
    assert (s["qty_giris"], s["qty_giris_kaynak"]) == (20.0, "trades.qty")


def test_T2c2_KAPANIS_GUNUNDEKI_OLAY_PENCEREDE(olc_mod, tmp_path):
    """Kapanış GÜNÜ içindeki olay pencereye DAHİLDİR — gün dizgesi ile tam ISO damga arasındaki
    ham dizge kıyası bu olayı sessizce dışarıda bırakırdı."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, qty=38, pnl_dollars=-500.0,
                                            r_multiple=-500.0 / 170.0)],
                 plans=[_plan("P-1")],
                 olaylar=[_benimseme(ts="2026-09-05T23:59:00+00:00")])
    assert sonuc["satirlar"][0]["benimsenmis_mi"] is True


def test_T2d_IKI_OLAYDAN_SONUNCUSU(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, qty=38, pnl_dollars=-500.0,
                                            r_multiple=-500.0 / 170.0)],
                 plans=[_plan("P-1")],
                 olaylar=[_benimseme(ts="2026-09-04T20:00:00+00:00", onceki=25.0, yeni=38),
                          _benimseme(ts="2026-09-02T20:00:00+00:00", onceki=17.0, yeni=25)])
    assert sonuc["satirlar"][0]["qty_giris"] == 38.0


def test_T2e_YENI_QTY_TUTMAZSA_OLCULEMEDI(olc_mod, tmp_path):
    """Benimseme `yeni`si defterdeki qty ile tutmuyorsa hangi sayının doğru olduğu BİLİNMEZ."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, qty=20)], plans=[_plan("P-1")],
                 olaylar=[_benimseme(yeni=38)])
    s = sonuc["satirlar"][0]
    assert s["olculebildi"] is False and s["neden"] == "benimseme yeni≠qty"
    assert s["qty_giris"] is None and s["r_yeni"] is None


def test_T2f_EXTRA_QTY_TABAN_BIRINCI_KAYNAK(olc_mod, tmp_path):
    """Kart sırası: `extra_json.qty_taban` varsa o kazanır (bugün defterde yok, ileride olur)."""
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, extra_json=json.dumps({"qty_taban": 12}))], plans=[_plan("P-1")])
    s = sonuc["satirlar"][0]
    assert (s["qty_giris"], s["qty_giris_kaynak"]) == (12.0, "extra_json.qty_taban")


# ---------------------------------------------------------------------------
# T3 — R3 stop kaynağı
# ---------------------------------------------------------------------------
def _trail(ticker="AAA", ts="2026-09-02T20:00:00+00:00", from_stop=80.0, to_stop=95.0):
    return {"ts": ts, "level": "info", "event": "mirror_trail_synced", "ticker": ticker,
            "from_stop": from_stop, "to_stop": to_stop, "ok": True, "detail": ""}


def _koruma(ticker="AAA", ts="2026-09-02T20:00:00+00:00", stop=70.0):
    return {"ts": ts, "level": "info", "event": "koruma_oco_gonderildi", "ticker": ticker,
            "stop": stop, "hedef": 150.0, "adet": 20.0}


def test_T3a_PLAN_STOPU_BIRINCI(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1", stop=90.0)],
                 olaylar=[_trail(), _koruma()])
    s = sonuc["satirlar"][0]
    assert (s["stop"], s["stop_kaynak"], s["guven"]) == (90.0, "plan", "yuksek")
    assert s["r_per_share"] == 10.0


def test_T3b_PLAN_YOKSA_TRAIL_FROM_STOP(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[], olaylar=[_trail(), _koruma()])
    s = sonuc["satirlar"][0]
    assert (s["stop"], s["stop_kaynak"], s["guven"]) == (80.0, "trail_from_stop", "orta")


def test_T3c_TRAIL_YOKSA_KORUMA_OCO_GUVEN_DUSUK(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[], olaylar=[_koruma()])
    s = sonuc["satirlar"][0]
    assert (s["stop"], s["stop_kaynak"], s["guven"]) == (70.0, "koruma_oco", "dusuk")


def test_T3d_HICBIRI_YOKSA_OLCULEMEDI_STOP_YOK(olc_mod, tmp_path):
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[], olaylar=[])
    s = sonuc["satirlar"][0]
    assert s["olculebildi"] is False and s["neden"] == "stop yok"
    assert s["r_yeni"] is None and s["dR"] is None
    assert sonuc["ozet"]["olculemeyen_n"] == 1


# ---------------------------------------------------------------------------
# T4 — PK-2 sentetik iki vaka
# ---------------------------------------------------------------------------
def test_T4a_PK2_BENIMSEMESIZ_DR_SIFIR(olc_mod, tmp_path):
    """Benimsemesiz işlemde qty_giris = qty → yeni payda eski paydayla AYNI → dR tam sıfır."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, pnl_dollars=250.0, r_multiple=250.0 / 200.0)],
                 plans=[_plan("P-1")])
    s = sonuc["satirlar"][0]
    assert s["olculebildi"] is True
    assert s["dR"] == 0.0 and s["dR_oran"] == 0.0
    assert sonuc["ozet"]["benimsemesiz_max_abs_dR"] == 0.0
    assert sonuc["ozet"]["esikler"]["benimsemesiz_ozdeslik_tol"]["gecti"] is True


def test_T4b_PK2_BENIMSENMIS_17_38_ORANI(olc_mod, tmp_path):
    """Benimsenmiş işlemde (17 → 38) yeni R ile eski R'nin oranı tam 17/38'dir."""
    rps, pnl = 10.0, -500.0
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, qty=38, pnl_dollars=pnl, r_multiple=pnl / (17 * rps))],
                 plans=[_plan("P-1")], olaylar=[_benimseme()])
    s = sonuc["satirlar"][0]
    assert s["olculebildi"] is True
    assert abs(s["r_yeni"] / s["r_eski"] - 17.0 / 38.0) < 1e-9
    assert s["dR_oran"] == pytest.approx(1.0 - 17.0 / 38.0, abs=1e-9)
    assert sonuc["ozet"]["benimsenmis_medyan_dR_oran"] == pytest.approx(1.0 - 17.0 / 38.0, abs=1e-9)


# ---------------------------------------------------------------------------
# T5 — PK-1 damgalı satır eşitliği
# ---------------------------------------------------------------------------
def test_T5a_PK1_DAMGALI_SATIR_ESITLIGI(olc_mod, tmp_path):
    """Damgalı satırda hesaplanan R, defterdeki `r_multiple` ile (tol 0,001) AYNI olmalı."""
    rps, qty, pnl = 10.0, 38, 456.0
    extra = {"r_payda": "giris_riski", "qty_taban": qty, "r_payda_usd": qty * rps}
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, qty=qty, pnl_dollars=pnl, r_multiple=pnl / (qty * rps),
                         extra_json=json.dumps(extra))],
                 plans=[_plan("P-1")])
    s = sonuc["satirlar"][0]
    pk1 = sonuc["ozet"]["pk1"]
    assert s["damgali_mi"] is True
    assert abs(s["r_yeni"] - s["r_eski"]) <= 0.001
    assert (pk1["n"], pk1["gecti"]) == (1, True)
    assert sonuc["ozet"]["esikler"]["kontrol_esitlik_tol"]["gecti"] is True
    assert sonuc["ozet"]["kill_list_tetik"] == []


def test_T5b_PK1_DAMGASIZ_DEFTERDE_GECTI_NONE(olc_mod, tmp_path):
    """Damgalı satır yokken PK-1 'geçti' DEĞİL 'ölçülmedi'dir — 0 ile bilmiyorum ayrı şeyler."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")])
    pk1 = sonuc["ozet"]["pk1"]
    assert (pk1["n"], pk1["gecti"]) == (0, None)
    assert pk1["neden"] == "damgalı kapanmış işlem yok"


def test_T5c_PK1_BOZUK_HESAP_KILL_LIST_TETIKLER(olc_mod, tmp_path):
    """Damgalı satır tutmazsa kill-list kalemi ADIYLA listeye düşer (hüküm yine Rol-1'in)."""
    rps, qty, pnl = 10.0, 38, 456.0
    extra = {"r_payda": "giris_riski", "qty_taban": qty, "r_payda_usd": qty * rps}
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, qty=qty, pnl_dollars=pnl, r_multiple=pnl / (qty * rps) + 0.5,
                         extra_json=json.dumps(extra))],
                 plans=[_plan("P-1")])
    assert sonuc["ozet"]["pk1"]["gecti"] is False
    assert any("PK-1" in t for t in sonuc["ozet"]["kill_list_tetik"])
    assert sonuc["hukum"] == "YOK — Rol-1"


# ---------------------------------------------------------------------------
# T6/T7 — tek kaynak: kart ve motor
# ---------------------------------------------------------------------------
def test_T6_ESIKLER_KARTLA_AYNI(olc_mod):
    """Kart TEK KAYNAKTIR; ölçüm betiğindeki kopya ondan ayrışırsa bu çivi kırılır."""
    kart = yaml.safe_load(KART.read_text(encoding="utf-8"))
    assert kart["esikler"] == olc_mod.ESIKLER
    assert olc_mod.ESIKLER == {"benimsenmis_ayrisma_medyan_alt": 0.10,
                               "benimsemesiz_ozdeslik_tol": 0.01,
                               "kontrol_esitlik_tol": 0.001,
                               "olculemeyen_ust_oran": 0.10}


def test_T7_R_PAYDA_GIRIS_BROKER_ILE_AYNI(olc_mod):
    """Ölçüm betiği motoru ithal EDEMEZ (obs yolu); damga dizgesi bu yüzden kopyadır ve
    kopyanın `broker.R_PAYDA_GIRIS` ile eşitliği burada ölçülür."""
    from meridian import broker
    assert olc_mod.R_PAYDA_GIRIS == broker.R_PAYDA_GIRIS


def test_T6b_HUKUM_METNI_DAMGALI(olc_mod, tmp_path):
    """R1–R6 metni çıktıya ve sha256'sı damgaya girer — ölçüm hangi tanımla koştuysa o kalır."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")])
    assert set(sonuc["hukumler"]) == {"R1", "R2", "R3", "R4", "R5", "R6"}
    assert sonuc["hukumler_sha256"] == hashlib.sha256(
        json.dumps(olc_mod.HUKUMLER, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    assert sonuc["girdi_kunyesi"]["db"]["sha256"] and sonuc["girdi_kunyesi"]["olaylar"]["sha256"]


# ---------------------------------------------------------------------------
# T8 — PK-3: ADIM-2 yazım betiğinin kuru/uygula sözleşmesi (KOMUT SATIRI)
# ---------------------------------------------------------------------------
def _r_multiple_sha(db) -> str:
    """`r_multiple` sütununun (seq sırasıyla) damgası — yazımın o sütuna dokunmadığının ölçüsü."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    veri = [(r[0], r[1]) for r in con.execute("SELECT seq, r_multiple FROM trades ORDER BY seq")]
    con.close()
    return hashlib.sha256(json.dumps(veri).encode("utf-8")).hexdigest()


def _extra(db, seq) -> dict:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    ham = con.execute("SELECT extra_json FROM trades WHERE seq = ?", (seq,)).fetchone()[0]
    con.close()
    return json.loads(ham) if ham else {}


@pytest.fixture
def yazim_ortami(olc_mod, tmp_path):
    """İki ölçülebilir + bir ölçülemez satırlı defter ve onun ölçüm JSON'u."""
    db = _db_kur(tmp_path / "defter.db",
                 [_islem(1), _islem(2, plan_id="P-2", ticker="BBB"),
                  _islem(3, plan_id="YOK", ticker="CCC")],
                 [_plan("P-1"), _plan("P-2", ticker="BBB")])
    ol = _olaylar_yaz(tmp_path / "olaylar.json", [])
    cikti = tmp_path / "cikti"
    olc_mod.main(["--db", str(db), "--olaylar", str(ol), "--cikti", str(cikti)])
    sonuc_yolu = sorted(cikti.glob("sonuc_094_*.json"))[-1]
    sonuc = json.loads(sonuc_yolu.read_text(encoding="utf-8"))
    assert sonuc["ozet"]["olculen_n"] == 2 and sonuc["ozet"]["olculemeyen_n"] == 1
    return {"db": db, "olcum": sonuc_yolu, "yedek": tmp_path / "yedek", "sonuc": sonuc}


def _ops(args):
    return subprocess.run([sys.executable, str(OPS), *args], capture_output=True, text=True)


def test_T8a_KURU_KOSUM_DB_SHA_DEGISMEZ(yazim_ortami):
    db = yazim_ortami["db"]
    once = hashlib.sha256(db.read_bytes()).hexdigest()
    p = _ops(["--db", str(db), "--olcum", str(yazim_ortami["olcum"]),
              "--yedek-dizin", str(yazim_ortami["yedek"]), "--kuru"])
    assert p.returncode == 0, p.stderr
    assert "KURU KOŞUM" in p.stdout and "Hedef satır: 2" in p.stdout
    assert hashlib.sha256(db.read_bytes()).hexdigest() == once
    assert not yazim_ortami["yedek"].exists()


def test_T8b_UYGULA_YALNIZ_EXTRA_JSON_DEGISIR(yazim_ortami):
    db = yazim_ortami["db"]
    r_sha = _r_multiple_sha(db)
    p = _ops(["--db", str(db), "--olcum", str(yazim_ortami["olcum"]),
              "--yedek-dizin", str(yazim_ortami["yedek"]), "--uygula", "--bugun", "2026-09-14"])
    assert p.returncode == 0, p.stderr
    assert "yazilan=2 atlanan=0 hedef=2" in p.stdout
    assert _r_multiple_sha(db) == r_sha                      # eski R alanına DOKUNULMADI
    for seq in (1, 2):
        e = _extra(db, seq)
        assert e["r_giris_damga"] == "EDG-2026-094 2026-09-14"
        assert e["r_giris_kaynak"] == "trades.qty+plan"
        assert e["r_multiple_giris"] == pytest.approx(1.25)
    assert _extra(db, 3) == {}                               # ölçülemeyen satıra yazılmadı
    yedekler = sorted(yazim_ortami["yedek"].glob("*.edg094.bak"))
    assert len(yedekler) == 1
    yan = pathlib.Path(str(yedekler[0]) + ".sha256")
    assert yan.exists() and yan.read_text(encoding="utf-8").split()[0] == \
        hashlib.sha256(yedekler[0].read_bytes()).hexdigest()


def test_T8c_IKINCI_UYGULA_IDEMPOTENT(yazim_ortami):
    ortak = ["--db", str(yazim_ortami["db"]), "--olcum", str(yazim_ortami["olcum"]),
             "--yedek-dizin", str(yazim_ortami["yedek"]), "--uygula"]
    assert _ops(ortak).returncode == 0
    sonra = hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest()
    p = _ops(ortak)
    assert p.returncode == 0, p.stderr
    assert "yazilan=0 atlanan=2 hedef=2" in p.stdout
    assert hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest() == sonra


def test_T8d_BAYRAK_CELISKISI_CIKIS_2(yazim_ortami):
    """Kip bayrağı TEK olmalı: ikisi birden de, hiçbiri de defteri AÇMAZ."""
    temel = ["--db", str(yazim_ortami["db"]), "--olcum", str(yazim_ortami["olcum"]),
             "--yedek-dizin", str(yazim_ortami["yedek"])]
    once = hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest()
    for ek in ([], ["--kuru", "--uygula"]):
        p = _ops(temel + ek)
        assert p.returncode == 2, (ek, p.stdout, p.stderr)
        assert "KİP BELİRSİZ" in p.stderr
    assert hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest() == once


def test_T8e_YEDEK_ALINAMAZSA_DB_DOKUNULMAZ(yazim_ortami, tmp_path):
    """Yedek yazılamıyorsa defter AÇILMAZ — yedeksiz yazım yoktur."""
    engel = tmp_path / "engel"          # dizin DEĞİL dosya → mkdir başarısız olur
    engel.write_text("dosya", encoding="utf-8")
    once = hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest()
    p = _ops(["--db", str(yazim_ortami["db"]), "--olcum", str(yazim_ortami["olcum"]),
              "--yedek-dizin", str(engel), "--uygula"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "YEDEK ALINAMADI" in p.stderr
    assert hashlib.sha256(yazim_ortami["db"].read_bytes()).hexdigest() == once
    assert _extra(yazim_ortami["db"], 1) == {}


# ---------------------------------------------------------------------------
# T9 — GERÇEK KOPYA (yalnız ortam değişkeni verildiğinde)
# ---------------------------------------------------------------------------
GERCEK_DB = os.environ.get("EDG094_DB")
GERCEK_OLAYLAR = os.environ.get("EDG094_OLAYLAR")
GERCEK_CIKTI = os.environ.get("EDG094_CIKTI")
GERCEK_ON_DOKUM = os.environ.get("EDG094_ON_DOKUM")


@pytest.mark.skipif(not (GERCEK_DB and GERCEK_OLAYLAR and GERCEK_CIKTI),
                    reason="EDG094_DB / EDG094_OLAYLAR / EDG094_CIKTI verilmedi — gerçek "
                           "defter kopyası bu koşumda yok")
def test_T9_GERCEK_KOPYA_OLCUMU(olc_mod):
    """A1 defter kopyasının SALT-OKUR ölçümü. Çıktı DEPO DIŞINA yazılır (Rol-1 taşır)."""
    argv = ["--db", GERCEK_DB, "--olaylar", GERCEK_OLAYLAR, "--cikti", GERCEK_CIKTI]
    if GERCEK_ON_DOKUM:
        argv += ["--on-dokum", GERCEK_ON_DOKUM]
    assert olc_mod.main(argv) == 0
    cikti = pathlib.Path(GERCEK_CIKTI)
    sonuc = json.loads(sorted(cikti.glob("sonuc_094_*.json"))[-1].read_text(encoding="utf-8"))
    oz = sonuc["ozet"]
    assert oz["n"] == 24, f"canlı kapanmış işlem sayısı 24 bekleniyordu: {oz['n']}"
    assert oz["benimsenmis_n"] + oz["benimsemesiz_n"] + oz["olculemeyen_n"] == oz["n"]
    assert sonuc["hukum"] == "YOK — Rol-1"
    assert sorted(cikti.glob("RAPOR_094_*.md"))
