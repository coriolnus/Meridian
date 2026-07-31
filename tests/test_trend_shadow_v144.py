"""test_trend_shadow_v144.py — WP-K TREND KOLU GÖLGE-KİTABI (2026-07-31).

EDG-2026-009'un incumbent kolu (chandelier × full_251 × N=10) canlı barlarda SANAL bir defterde
yürüyor. Bu dosya altı yasayı çiviler:

  1. SIFIR YETKİ (AST) — modül broker/alpaca/emir yolunu IMPORT BİLE ETMEZ ve kendi defteri
     dışında hiçbir dosyaya yazmaz. Kaynak-metin değil AST: bir yorum satırındaki "broker"
     kelimesi teli yanlış yere ağlatırdı (test_bottleneck_v12'nin AST'ye taşınma gerekçesi).
  2. SEÇİM DETERMİNİZMİ — sabit bar fikstüründe ay-sonu kararı AYNI N=10 listesini verir.
  3. CHANDELIER TETİĞİ — kapanış tepe − 3.5×ATR22'nin altına düşünce pozisyon `chandelier`
     sebebiyle kapanır; düşmeyince kapanmaz (iki yönlü çivi, tek yönlü değil).
  4. M2M MUHASEBESİ — kapanan işlemin getirisi/doları ELLE hesaplanmış fikstürle birebir; 10bps
     iki bacakta da ödenir.
  5. YASA 6 — defterin DIŞ okuyucusu (api.py) var ve PIT şerhi okuyucuya ULAŞIYOR.
  6. HATA İZOLASYONU — gölge-kitap patlarsa `daily_cycle` SÜRER ve olay adıyla kaydedilir.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from meridian import config, loop, store, trend_shadow as ts
from tests.conftest import make_bars


# ---------------------------------------------------------------- fikstürler
@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


def _evren(n=420, k=14):
    """SPY + k sembol; her biri FARKLI trendde → 12-1 sıralaması yapay bir berabere üretmez."""
    idx = make_bars(n, seed=1, trend=0.0004)
    bars = {}
    for i in range(k):
        bars[f"T{i:02d}"] = make_bars(n, seed=100 + i, trend=0.0002 + i * 0.00025)
    return bars, idx


def _rampa(n, gunluk, baz=100.0):
    """GÜRÜLTÜSÜZ rampa: 12-1 sıralaması `gunluk`ta MONOTONdur — yani 'deterministik ama yanlış'
    bir sıralama, gürültünün arkasına saklanamaz. ATR22 > 0 kalsın diye high/low bandı var."""
    dates = pd.bdate_range("2022-01-03", periods=n)
    close = baz * (1.0 + gunluk) ** np.arange(n)
    openp = close / (1.0 + gunluk)
    return pd.DataFrame({"date": dates, "open": openp, "high": close * 1.005,
                         "low": openp * 0.995, "close": close,
                         "volume": np.full(n, 2_000_000.0)})


def _rampa_evren(n=420, k=14):
    """SPY + k sembol; T00 en yavaş, T{k-1} en hızlı — sıralama beklentisi KESİN."""
    idx = _rampa(n, 0.0004)
    bars = {f"T{i:02d}": _rampa(n, 0.0002 + i * 0.0004) for i in range(k)}
    return bars, idx


def _uni_yamasi(monkeypatch, bars):
    """Fikstür sembolleri REPLAY_UNIVERSE'te yok — evren listesi ÜRETİM globali, setattr ile yamanır."""
    from meridian.adapters import data as _data
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", sorted(bars))


def _ay_sonlari(idx):
    """Fikstürün ana takvimindeki GERÇEK XNYS ay-sonları (takvim kapısı bunları kabul eder)."""
    dates = pd.DatetimeIndex(idx["date"])
    return [d for d in dates if ts.ay_sonu_mu(d)]


# ---------------------------------------------------------------- 1. SIFIR YETKİ (AST)
def _ithal_edilenler() -> set:
    """trend_shadow.py'nin İTHAL ETTİĞİ her modül adı (AST — yorumlar ve dizeler sayılmaz)."""
    src = pathlib.Path("meridian/trend_shadow.py").read_text()
    tree = ast.parse(src)
    out: set = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            kok = ("." * (n.level or 0)) + (n.module or "")
            out.add(kok)
            out.update(f"{kok}.{a.name}" for a in n.names)
    return out


def _yazilan_dosyalar() -> set:
    """store.write_*/append_* çağrılarının LİTERAL hedefleri + sabitten çözülenler."""
    src = pathlib.Path("meridian/trend_shadow.py").read_text()
    tree = ast.parse(src)
    sabit = {t.id: n.value.value
             for n in ast.walk(tree) if isinstance(n, ast.Assign)
             for t in n.targets
             if isinstance(t, ast.Name) and isinstance(n.value, ast.Constant)
             and isinstance(n.value.value, str)}
    yazim = {"write_json", "write_jsonl", "append_jsonl", "update_json", "update_jsonl",
             "merge_dated_jsonl"}
    out: set = set()
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in yazim and n.args):
            a = n.args[0]
            if isinstance(a, ast.Constant):
                out.add(a.value)
            elif isinstance(a, ast.Name):
                out.add(sabit.get(a.id, f"<COZULEMEDI:{a.id}>"))
            else:
                out.add("<COZULEMEDI:ifade>")
    return out


def test_golge_kitap_sifir_yetkilidir():
    """YAPISAL SIFIR YETKİ: emir yolu İTHAL BİLE EDİLMEZ, yazım tek deftere kilitli.

    Neden ithal listesi (çağrı listesi değil): bir modül `broker`ı import ettiği anda emir yolu
    onun çağrı grafiğine girer ve 'yetkisiz' iddiası her yeni satırda yeniden ispat gerektirir.
    İthali yasaklamak iddiayı BİR KEZ ve YAPISAL olarak kurar."""
    ith = _ithal_edilenler()
    yasak = ("broker", "alpaca", "arming", "notify", "mirror_stream", "intraday_cycle",
             "hermes", "versioning", "rollback", "sprint", "guard", "strategy", "backtest")
    for y in yasak:
        kirli = sorted(m for m in ith if y in m.lower())
        assert not kirli, f"gölge-kitap emir/karar yoluna bağlandı: {kirli}"

    yazilan = _yazilan_dosyalar()
    assert yazilan == {ts.BOOK}, f"gölge-kitap kendi defteri dışına yazıyor: {yazilan - {ts.BOOK}}"

    # ÇAĞRI DÜZEYİ İKİNCİ KAT: emir fiilleri kaynakta hiç geçmemeli (ithal olmasa da bir gün
    # `__import__("meridian.broker")` ile dolanılabilir — o yol da burada kırmızı yakar).
    src = inspect.getsource(ts)
    for tok in ("submit", "fill_entry", "place_order", "_load_broker", "PaperBroker",
                "__import__"):
        assert tok not in src, f"gölge-kitapta emir/dolanma yüzeyi: {tok}"


# ---------------------------------------------------------------- 2. SEÇİM DETERMİNİZMİ
def test_secim_determinizmi_ve_n10(seeded, monkeypatch):
    """Sabit bar fikstüründe ay-sonu kararı AYNI listeyi verir ve slot sayısı N=10'u AŞMAZ."""
    bars, idx = _evren()
    _uni_yamasi(monkeypatch, bars)
    aylar = _ay_sonlari(idx)
    assert len(aylar) >= 14, "fikstür 12-1 çapası için yeterli ay-sonu taşımıyor"
    rd = aylar[13]                                     # 13. ay-sonu → gk=13 >= 12

    kararlar = []
    for _ in range(2):
        (config.STATE / ts.BOOK).unlink(missing_ok=True)   # kitabı sıfırla → aynı başlangıç
        r = ts.run_cycle(bars, idx, on_date=str(rd.date()))
        assert r["status"] == "born"                   # kitap BOŞ doğar (geri-doldurma yok)
        # doğumdan sonraki İLK ay-sonuna kadar yürüt
        r2 = ts.run_cycle(bars, idx, on_date=str(aylar[-1].date()))
        assert r2["status"] == "ok"
        kitap = store.read_json(ts.BOOK, {})
        kararlar.append(sorted(kitap["positions"]))

    assert kararlar[0] == kararlar[1], f"seçim deterministik değil: {kararlar}"
    assert 0 < len(kararlar[0]) <= ts.N_SLOTS, f"slot yasası bozuldu: {len(kararlar[0])}"
    assert ts.N_SLOTS == 10 and ts.CHANDELIER_K == 3.5 and ts.ATR_LEN == 22 \
        and ts.FRICTION_BPS == 10.0, "şasi sabiti sürüklendi (engine.py:21-23 ile birebirlik)"


def test_secim_momentum_siralamasini_izler(seeded, monkeypatch):
    """Seçim RASTGELE değil: girenler 12-1 getirisi EN YÜKSEK adaylardan gelir.

    GÜRÜLTÜSÜZ rampa fikstüründe sıralama KESİNDİR (T00 en yavaş, T13 en hızlı): doğru bir
    12-1 sıralaması tam olarak en hızlı 10'u seçmeli. Bu, 'deterministik ama yanlış' bir
    sıralamayı determinizm testinden ayıran çividir."""
    bars, idx = _rampa_evren(n=420, k=14)
    _uni_yamasi(monkeypatch, bars)
    aylar = _ay_sonlari(idx)
    ts.run_cycle(bars, idx, on_date=str(aylar[13].date()))
    ts.run_cycle(bars, idx, on_date=str(aylar[-1].date()))
    secilen = sorted(store.read_json(ts.BOOK, {})["positions"])
    assert secilen == [f"T{i:02d}" for i in range(4, 14)], \
        f"12-1 sıralaması izlenmiyor (en hızlı 10 beklenirdi): {secilen}"


# ---------------------------------------------------------------- 3. CHANDELIER TETİĞİ
def _kitap_kur(state, sym, entry_px, peak, entry_date, shares=100.0, cash=1000.0):
    kitap = ts.yeni_kitap()
    kitap["cash"] = cash
    kitap["positions"] = {sym: {"shares": shares, "entry_date": entry_date,
                                "entry_price": entry_px, "peak_high": peak,
                                "last_close": entry_px}}
    return kitap


def test_chandelier_cikis_tetigi(seeded, monkeypatch):
    """Kapanış tepe − 3.5×ATR22'nin ALTINA düşerse `chandelier`; üstünde kalırsa çıkış YOK."""
    bars, idx = _evren(n=420, k=3)
    _uni_yamasi(monkeypatch, bars)
    master = pd.DatetimeIndex(idx["date"])
    mpos = {d: i for i, d in enumerate(master)}
    rd = _ay_sonlari(idx)[13]
    per = ts._norm(bars)
    uni = sorted(bars)

    tail = master[max(0, mpos[rd] - ts.TAIL_SESSIONS + 1): mpos[rd] + 1]
    dilim = ts._dilim(per, ["T00"], tail)
    atr = float(ts._atr(dilim["T00"]).iloc[-1])
    px = float(per["T00"].at[rd, "close"])
    assert atr > 0, "fikstürde ATR22 ölçülemedi — test bir şey kanıtlamıyor"

    # (a) TETİKLENİR: tepe = px + 3.5×ATR + 1 → kapanış duraktan aşağıda
    kitap = _kitap_kur(seeded, "T00", px, px + ts.CHANDELIER_K * atr + 1.0, str(master[0].date()))
    karar = ts._karar(kitap, rd, per, master, mpos, uni)
    assert ("T00", "chandelier") in karar["exits"], f"chandelier tetiklenmedi (atr={atr})"

    # (b) TETİKLENMEZ: tepe = px + 3.5×ATR − 1 → kapanış durağın ÜSTÜNDE
    kitap2 = _kitap_kur(seeded, "T00", px, px + ts.CHANDELIER_K * atr - 1.0, str(master[0].date()))
    karar2 = ts._karar(kitap2, rd, per, master, mpos, uni)
    assert not [x for x in karar2["exits"] if x[0] == "T00"], "durak üstünde pozisyon kapatıldı"


def test_listeden_dusen_kapanmaz_incumbent_akisi(seeded, monkeypatch):
    """INCUMBENT AKIŞ: üst-N listesinden düşmek TEK BAŞINA çıkış sebebi DEĞİLDİR (rafine
    'rotate' kolu ölçüldü ve üstünlüğünü kanıtlayamadı — EDG-2026-009 hüküm §2)."""
    bars, idx = _rampa_evren(n=420, k=14)
    _uni_yamasi(monkeypatch, bars)
    master = pd.DatetimeIndex(idx["date"])
    mpos = {d: i for i, d in enumerate(master)}
    rd = _ay_sonlari(idx)[13]
    per = ts._norm(bars)
    # T00 = en yavaş sembol → üst-10'a asla giremez; durak ÇOK uzakta (tepe = giriş fiyatı)
    px = float(per["T00"].at[rd, "close"])
    kitap = _kitap_kur(seeded, "T00", px, px, str(master[0].date()))
    karar = ts._karar(kitap, rd, per, master, mpos, sorted(bars))
    assert not karar["exits"], f"listeden düşen pozisyon kapatıldı (rotasyon sızdı): {karar['exits']}"
    assert "T00" not in karar["en_iyi"], "fikstür varsayımı bozuk: T00 üst-10'a girmiş"


# ---------------------------------------------------------------- 4. M2M MUHASEBESİ
def test_m2m_muhasebesi_elle_dogrulanmis(seeded, monkeypatch):
    """Kapanan işlemin getirisi/doları ELLE hesapla birebir; 10bps İKİ bacakta da ödenir.

    Fikstür: 100 hisse @ 50.00 girildi, çıkış açılışı 60.00.
      brüt gelir      = 100 × 60.00                       = 6000.00
      nakde giren     = 6000 × (1 − 0.0010)               = 5994.00
      ödenen friksiyon= 6000 × 0.0010                     =    6.00
      pnl_dollars     = 6000 − 100×50                     = 1000.00   (giriş friksiyonu girişte ödendi)
      getiri_pct      = (60/50 − 1) × 100                 =   20.0
    """
    bars, idx = _evren(n=420, k=3)
    _uni_yamasi(monkeypatch, bars)
    master = pd.DatetimeIndex(idx["date"])
    mpos = {d: i for i, d in enumerate(master)}
    rd, xd = master[-2], master[-1]

    per = ts._norm(bars)
    # icra fiyatını DETERMİNİSTİK yap: çıkış gününün açılışı tam 60.00
    per["T00"] = per["T00"].copy()
    per["T00"].loc[xd, "open"] = 60.0

    kitap = _kitap_kur(seeded, "T00", 50.0, 999.0, str(master[0].date()), shares=100.0, cash=0.0)
    kitap["pending"] = {"date": str(rd.date()), "exits": [("T00", "chandelier")], "entries": []}
    ts._icra(kitap, xd, per, mpos)

    assert not kitap["positions"], "çıkış sonrası pozisyon defterde kaldı"
    c = kitap["closed"][-1]
    assert c["sym"] == "T00" and c["reason"] == "chandelier"
    assert c["exit_px"] == 60.0 and c["entry_px"] == 50.0
    assert c["getiri_pct"] == 20.0, c
    assert c["pnl_dollars"] == 1000.0, c
    assert round(kitap["cash"], 2) == 5994.00, kitap["cash"]
    assert round(kitap["sayaclar"]["friction_paid"], 2) == 6.00
    assert kitap["sayaclar"]["exits"]["chandelier"] == 1
    assert kitap["sayaclar"]["closed_toplam"] == 1
    assert kitap["pending"] is None


def test_gunluk_m2m_ve_esit_agirlik(seeded, monkeypatch):
    """Günlük M2M noktası HER seansta düşer ve giriş sonrası ağırlıklar 1/N'e yakın olur."""
    bars, idx = _evren(n=420, k=14)
    _uni_yamasi(monkeypatch, bars)
    aylar = _ay_sonlari(idx)
    ts.run_cycle(bars, idx, on_date=str(aylar[13].date()))
    ts.run_cycle(bars, idx, on_date=str(aylar[-1].date()))
    kitap = store.read_json(ts.BOOK, {})

    eq = kitap["equity"]
    assert len(eq) > 20 and eq[0]["equity"] == ts.INIT_EQUITY
    tarihler = [r["date"] for r in eq]
    assert tarihler == sorted(tarihler) and len(tarihler) == len(set(tarihler)), \
        "M2M eğrisi sıralı/tekil değil"

    son = eq[-1]["equity"]
    per = ts._norm(bars)
    sd = pd.Timestamp(kitap["last_session"])
    agirliklar = [p["shares"] * float(per[t].at[sd, "close"]) / son
                  for t, p in kitap["positions"].items() if sd in per[t].index]
    assert agirliklar, "pozisyon yok — ağırlık iddiası kurulamıyor"
    for w in agirliklar:
        assert 0.03 < w < 0.25, f"eşit-ağırlık (1/10) sözleşmesi bozuldu: {agirliklar}"


def test_ikinci_kosum_ayni_seansi_tekrar_islemez(seeded, monkeypatch):
    """İDEMPOTANLIK: aynı seans iki kez çağrılırsa eğri ÇOĞALMAZ (defterin monotonluk yasası)."""
    bars, idx = _evren(n=420, k=5)
    _uni_yamasi(monkeypatch, bars)
    son = str(pd.DatetimeIndex(idx["date"])[-1].date())
    ts.run_cycle(bars, idx, on_date=son)
    r2 = ts.run_cycle(bars, idx, on_date=son)
    assert r2["status"] == "noop"
    n = len(store.read_json(ts.BOOK, {})["equity"])
    ts.run_cycle(bars, idx, on_date=son)
    assert len(store.read_json(ts.BOOK, {})["equity"]) == n, "eğri aynı seansta çoğaldı"


def test_takvim_yoksa_karar_alinmaz(seeded, monkeypatch):
    """FAIL-CLOSED: XNYS takvimi yoksa 'ay-sonu mu' CEVAPSIZDIR — uydurma ay-sonu üretilmez."""
    from meridian.adapters import data as _data
    bars, idx = _evren(n=420, k=5)
    _uni_yamasi(monkeypatch, bars)
    aylar = _ay_sonlari(idx)
    ts.run_cycle(bars, idx, on_date=str(aylar[13].date()))
    monkeypatch.setattr(_data, "_sessions", lambda: frozenset())
    monkeypatch.setattr(ts, "_AY_SONU", {})
    r = ts.run_cycle(bars, idx, on_date=str(aylar[-1].date()))
    kitap = store.read_json(ts.BOOK, {})
    assert r["status"] == "ok" and not kitap["positions"], "takvimsiz karar alındı"
    assert kitap["sayaclar"]["kararsiz_gun"] > 0, "kararsız gün SAYILMADI (sessiz boşluk)"


# ---------------------------------------------------------------- 5. YASA 6 (okuyucu)
def test_yasa6_defterin_dis_okuyucusu_var():
    """Defteri YAZAN modül dışında bir tüketici olmalı ve PIT şerhi ona ULAŞMALI."""
    from meridian import codelaw
    graf = codelaw.artifact_graph()["artifacts"].get(ts.BOOK)
    assert graf, f"{ts.BOOK} artefakt grafında görünmüyor (literal ad kullanılmalı)"
    assert "trend_shadow.py" in graf["writers"]
    assert graf["external_readers"], f"{ts.BOOK} okuyucusuz yazılıyor (YASA 6)"
    assert not graf["unread"]

    api_src = pathlib.Path("meridian/api.py").read_text()
    assert 'store.read_json("trend_book.json"' in api_src, "api uç defteri LİTERAL adla okumuyor"

    # ŞERH RAKAMLA BİRLİKTE ÇIKAR: özet hem equity hem şerh taşır
    o = ts.ozet({"positions": {"A": {}}, "equity": [{"date": "2026-01-02", "equity": 100.0},
                                                    {"date": "2026-01-05", "equity": 110.0}],
                 "cash": 5.0, "sayaclar": {"closed_toplam": 2}, "pit_serh": ts.PIT_SERH})
    assert o["equity"] == 110.0 and o["getiri_pct"] == 10.0 and o["pozisyon"] == 1
    assert "PIT" in o["pit_serh"] and "yanlılık-düşülmüş" in o["pit_serh"]
    # BOŞ KART DÜRÜSTTÜR: kitap yoksa "yok" der, sıfır UYDURMAZ
    assert ts.ozet(None) == {"var": False, "pozisyon": 0, "equity": None}


def test_pit_serhi_kitabin_icinde_tasinir(seeded, monkeypatch):
    """Şerh diskteki defterin İÇİNDE durur — dosyayı elle açan da yanlılık beyanını görür."""
    bars, idx = _evren(n=420, k=5)
    _uni_yamasi(monkeypatch, bars)
    son = str(pd.DatetimeIndex(idx["date"])[-1].date())
    ts.run_cycle(bars, idx, on_date=son)
    kitap = store.read_json(ts.BOOK, {})
    assert kitap["schema"] == ts.SCHEMA and "6-7p/yıl" in kitap["pit_serh"]
    assert "SANAL" in kitap["pit_serh"], "defter sanal olduğunu söylemiyor"
    # ŞERH SİLİNSE BİLE geri çakılır: rakam şerhsiz yaşayamaz (elle düzenlenmiş bir defter,
    # bir sonraki turda yanlılık beyanını kendiliğinden geri kazanır).
    kitap["pit_serh"] = ""
    kitap["last_session"] = "1900-01-01"      # kitabı geriye al ki tur GERÇEKTEN yazsın
    store.write_json(ts.BOOK, kitap)
    ts.run_cycle(bars, idx, on_date=son)
    assert "PIT" in store.read_json(ts.BOOK, {})["pit_serh"], "şerh defterden düştü"


# ---------------------------------------------------------------- 6. HATA İZOLASYONU
def test_golge_kitap_patlarsa_daily_cycle_surer(seeded, monkeypatch):
    """Sıfır yetkili katmanın hatası CANLI DÖNGÜYÜ düşüremez — ama SESSİZ de kalamaz."""
    from meridian import trend_shadow as _ts
    bars, idx = _evren(n=320, k=3)

    def _patla(*a, **k):
        raise RuntimeError("gölge-kitap kasıtlı arıza")

    monkeypatch.setattr(_ts, "run_cycle", _patla)
    d = str(idx["date"].iloc[-1].date())
    s = loop.daily_cycle(bars, idx, on_date=d)
    assert s.get("status") == "ok" and s.get("date") == d, f"canlı döngü gölge yüzünden düştü: {s}"
    assert s.get("trend_book") is None, "ölçülemeyen özet SIFIR diye uydurulmuş"
    assert store.read_json(loop.PORTFOLIO, {}).get("last_date") == d, "kitap ilerlemedi"
    olaylar = [r for r in store.read_jsonl("events.jsonl") if r.get("event") == "trend_shadow_failed"]
    assert olaylar and "RuntimeError" in olaylar[-1]["error"], "arıza sessizce yutuldu"


def test_daily_cycle_gercekten_golge_kitabi_kabliyor(seeded, monkeypatch):
    """Kablo GERÇEK: normal bir döngü defteri doğurur ve özeti olaya/dönüşe taşır."""
    from meridian.adapters import data as _data
    bars, idx = _evren(n=320, k=3)
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", sorted(bars))
    d = str(idx["date"].iloc[-1].date())
    s = loop.daily_cycle(bars, idx, on_date=d)
    assert s["status"] == "ok"
    assert isinstance(s.get("trend_book"), dict) and s["trend_book"]["status"] == "born"
    assert store.read_json(ts.BOOK, {}).get("schema") == ts.SCHEMA
    dc = [r for r in store.read_jsonl("events.jsonl") if r.get("event") == "daily_cycle"]
    assert dc and dc[-1].get("trend_book") is not None, "daily_cycle olayı trend_book alanı taşımıyor"


def test_api_teshis_ucu_defteri_servis_eder(seeded, monkeypatch):
    """Pano yüzeyi: /api/diagnostics `trend_kitabi` bloğunu ŞERHİYLE birlikte verir."""
    bars, idx = _evren(n=320, k=3)
    _uni_yamasi(monkeypatch, bars)
    ts.run_cycle(bars, idx, on_date=str(idx["date"].iloc[-1].date()))
    src = inspect.getsource(__import__("meridian.api", fromlist=["api_diagnostics"]).api_diagnostics)
    assert '"trend_kitabi"' in src and 'store.read_json("trend_book.json"' in src
    o = ts.ozet(store.read_json(ts.BOOK, None))
    assert o["var"] and o["pit_serh"] and o["equity"] == ts.INIT_EQUITY
