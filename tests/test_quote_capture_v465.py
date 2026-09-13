"""test_quote_capture_v465.py — EDG-2026-085 Senaryo-A: icra-anı quote kaydı (halka · pencere ·
abone · yazıcı · marketstream q yolu · mirror kancası). Kart:
research/cards/EDG-2026-085-icra-ani-quote-kaydi.yaml.

BÖLÜMLER: A) `quotecapture` birimi · B) marketstream `q` yolu + `quotes` aboneliği · C) mirror
kancası · D) yapısal sınırlar (marketstream disk yolu yok, codelaw desen beyanı).

ÖLÇÜM NOTU (plan yer tutucusu düzeltildi): `store` modülünde `STATE_DIR` diye bir ad YOKTUR
(ölçüldü 2026-09-13); sandbox kökü `config.STATE`tir ve `sandbox_state` fikstürü o dizini zaten
döndürür — A13 onu kullanır, uydurma bir ad değil.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json

import pytest

from meridian import quotecapture as qc


class Saat:
    """Enjekte edilebilir UTC saati — testler zamanı elle ilerletir (gerçek uyku YOK)."""

    def __init__(self, t0="2026-09-14T13:45:00Z"):
        self.t = dt.datetime.fromisoformat(t0.replace("Z", "+00:00"))

    def __call__(self):
        return self.t

    def ilerle(self, s):
        self.t += dt.timedelta(seconds=s)


def _q(sembol, bid, ask, ts):
    return {"T": "q", "S": sembol, "bp": bid, "bs": 2, "ap": ask, "as": 3, "bx": "V", "ax": "V",
            "c": ["R"], "t": ts, "z": "C"}


def _emir(coid, sembol, side="buy", event="new", **ek):
    return event, {"client_order_id": coid, "symbol": sembol, "side": side,
                   "status": ek.pop("status", event), **ek}


@pytest.fixture
def kayit(tmp_path, sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "1")
    d = tmp_path / "kayit"
    monkeypatch.setenv(qc.DIZIN_ENV, str(d))
    qc._KAYIT = None
    saat = Saat()
    k = qc.QuoteCapture(str(d), simdi=saat)
    yield k, d, saat
    qc._KAYIT = None


def _satirlar(d, ad):
    p = d / ad
    return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []


# =================================================================================================
# A) quotecapture birimi — halka · pencere · abone kümesi · yazıcı
# =================================================================================================

def test_A1_pencere_disi_quote_YAZILMAZ_halkada_tutulur(kayit):
    k, d, saat = kayit
    k.q_geldi(_q("AAPL", 100.0, 100.1, "2026-09-14T13:45:00.100Z"))
    assert _satirlar(d, "edg085_2026-09-14.jsonl") == []
    assert k.snapshot()["satir_bugun"] == 0 and k.snapshot()["son_q_at"] is not None


def test_A2_new_olayi_pencere_acar_halka_geri_30sn_dokulur(kayit):
    k, d, saat = kayit
    for i in range(6):                       # 13:44:10 .. 13:45:00 → yalnız son 30 sn halka_geri'ye girer
        saat.t = Saat("2026-09-14T13:44:10Z").t + dt.timedelta(seconds=10 * i)
        k.q_geldi(_q("AAPL", 100 + i, 100.1 + i, saat.t.isoformat().replace("+00:00", "Z")))
    saat.t = Saat("2026-09-14T13:45:05Z").t
    k.olay(*_emir("P-2026-09-14-AAPL-1", "AAPL"))
    rows = _satirlar(d, "edg085_2026-09-14.jsonl")
    geri = [r for r in rows if r["tur"] == "quote" and r["faz"] == "halka_geri"]
    assert [r["bid"] for r in geri] == [103, 104, 105], "yalnız son 30 sn (≥13:44:35) dökülmeli"
    assert any(r["tur"] == "pencere" and r["olay"] == "ac" and r["neden"] == "new" for r in rows)


def test_A3_pencere_icinde_quote_kayit_ve_HAM_yazilir(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(2)
    m = _q("AAPL", 100.0, 100.2, "2026-09-14T13:45:02.000Z")
    k.q_geldi(m)
    rows = [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "quote"]
    assert rows[-1]["faz"] == "pencere" and rows[-1]["coid"] == "P-1" and rows[-1]["ask"] == 100.2
    ham = _satirlar(d, "edg085_ham_2026-09-14.jsonl")
    assert ham == [m], "ham çerçeve OLDUĞU GİBİ (süzgeçsiz) yazılmalı"


def test_A4_fill_dolum_isareti_ve_30sn_kuyruk_sonra_kapanis(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(5)
    k.q_geldi(_q("AAPL", 100.0, 100.2, "2026-09-14T13:45:05.000Z"))
    saat.ilerle(1)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="100.15",
                  filled_at="2026-09-14T13:45:06.4Z"))
    saat.ilerle(10)
    k.q_geldi(_q("AAPL", 100.1, 100.3, "2026-09-14T13:45:16.000Z"))   # dolum_sonrasi
    saat.ilerle(25)
    k.q_geldi(_q("AAPL", 100.2, 100.4, "2026-09-14T13:45:41.000Z"))   # +35 sn → kapanmış, yazılmaz
    rows = _satirlar(d, "edg085_2026-09-14.jsonl")
    dolum = [r for r in rows if r["tur"] == "dolum"][0]
    assert dolum["coid"] == "P-1" and dolum["dolum_fiyat"] == 100.15 and dolum["quote_n_pencere"] == 1
    assert dolum["kayip_nedeni"] is None and dolum["son_quote"]["ask"] == 100.2
    fazlar = [r["faz"] for r in rows if r["tur"] == "quote"]
    assert fazlar == ["pencere", "dolum_sonrasi"]
    assert [r for r in rows if r["tur"] == "pencere" and r["olay"] == "kapat"][-1]["neden"] == "fill+30s"


def test_A5_quote_suz_dolum_kayip_nedeni_SEMBOL_SESSIZ(kayit):
    k, d, saat = kayit
    k.baglanti(True)          # soket KANITLI ayakta → kayıp nedeni SEMBOLÜN kendisi (bkz. A17)
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(3)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="100.15"))
    dolum = [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "dolum"][0]
    assert dolum["quote_n_pencere"] == 0 and dolum["kayip_nedeni"] == "sembol_sessiz"


def test_A6_abone_degil_dolum_isareti(kayit):
    k, d, saat = kayit
    k.baglanti(True)          # bağlantı sorunu DEĞİL: neden abonelik kümesinin dışında olmak
    # NVDA motor-dışı: pozisyon değil, bekleyen emir değil → abone kümesinde yok
    k.olay(*_emir("6f0c-uuid", "NVDA", event="fill", status="filled", filled_avg_price="10"))
    dolum = [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "dolum"][0]
    assert dolum["kayip_nedeni"] == "abone_degil"


def test_A7_bracket_bacagi_uuid_coid_halka_geri_ve_dolum_sonrasi(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))                       # sembol abone kümesine girer
    saat.ilerle(1)
    k.q_geldi(_q("AAPL", 99.0, 99.1, "2026-09-14T13:45:01.000Z"))
    saat.ilerle(1)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="99.05"))
    saat.ilerle(3600)                                    # bir saat sonra stop bacağı dolar
    k.q_geldi(_q("AAPL", 95.0, 95.1, "2026-09-14T14:45:00.000Z"))   # halkada
    saat.ilerle(1)
    k.olay(*_emir("e1a2-uuid", "AAPL", side="sell", event="fill", status="filled",
                  filled_avg_price="95.02"))
    rows = _satirlar(d, "edg085_2026-09-14.jsonl")
    cikis = [r for r in rows if r["tur"] == "dolum" and r["coid"] == "e1a2-uuid"][0]
    assert cikis["quote_n_pencere"] == 1 and cikis["kayip_nedeni"] is None
    assert [r["faz"] for r in rows if r["tur"] == "quote" and r["coid"] == "e1a2-uuid"] == ["halka_geri"]


def test_A8_pencere_tavani_1800sn_kapatir_ve_isaretler(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(qc.PENCERE_TAVAN_S + 1)
    k.q_geldi(_q("AAPL", 100.0, 100.1, "2026-09-14T14:15:01.000Z"))
    rows = _satirlar(d, "edg085_2026-09-14.jsonl")
    assert [r for r in rows if r["tur"] == "pencere" and r["olay"] == "kapat"][-1]["neden"] == "pencere_tavani"
    assert not [r for r in rows if r["tur"] == "quote" and r["faz"] == "pencere"]


def test_A9_abone_kumesi_oncelik_ve_tavan(kayit):
    from meridian import store
    k, d, saat = kayit
    k.baglanti(True)          # bağlantı sorunu DEĞİL: neden abone TAVANI
    store.write_json("portfolio.json", {"positions": {f"POS{i}": {} for i in range(20)}})
    for i in range(15):
        k.olay(*_emir(f"P-{i}", f"GIR{i}"))
    for i in range(5):
        k.olay(*_emir(f"uuid-{i}", f"DIG{i}", event="accepted"))
    ab = k.istenen_abonelik()
    assert len(ab) == qc.ABONE_TAVAN and ab[:20] == [f"POS{i}" for i in range(20)]
    assert ab[20:] == [f"GIR{i}" for i in range(10)] and k.snapshot()["tavan_asimi_n"] == 10
    k.olay(*_emir("P-14", "GIR14", event="fill", status="filled", filled_avg_price="1"))
    assert [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "dolum"][-1]["kayip_nedeni"] == "tavan_asimi"


def test_A10_terminal_olay_sembolu_kumeden_dusurur_ve_event_set_eder(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    assert "AAPL" in k.istenen_abonelik() and k.abonelik_degisti().is_set()
    k.abonelik_degisti().clear()
    k.olay(*_emir("P-1", "AAPL", event="canceled", status="canceled"))
    assert "AAPL" not in k.istenen_abonelik() and k.abonelik_degisti().is_set()
    assert [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "pencere"][-1]["neden"] == "canceled"


def test_A11_dizin_yoksa_yazim_yok_ve_BIR_kez_warn(sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "1")
    monkeypatch.delenv(qc.DIZIN_ENV, raising=False)
    uyarilar = []
    monkeypatch.setattr(qc.obs, "warn", lambda ev, **f: uyarilar.append(ev))
    k = qc.QuoteCapture(None, simdi=Saat())
    k.olay(*_emir("P-1", "AAPL"))
    k.q_geldi(_q("AAPL", 1, 1.1, "2026-09-14T13:45:01.000Z"))
    assert uyarilar.count("quote_capture_dizin_yok") == 1 and k.snapshot()["dizin"] is None


def test_A12_yazim_dusunce_WARN_ve_sayac(kayit, monkeypatch):
    k, d, saat = kayit
    uyarilar = []
    monkeypatch.setattr(qc.obs, "warn", lambda ev, **f: uyarilar.append((ev, f)))
    d.mkdir(exist_ok=True)
    (d / "edg085_2026-09-14.jsonl").mkdir()          # dosya yerine DİZİN → açılamaz
    k.olay(*_emir("P-1", "AAPL"))
    assert uyarilar and uyarilar[0][0] == "quote_capture_yazim_dustu" and k.snapshot()["yazim_hata_n"] >= 1


def test_A13_STATE_altina_tek_bayt_yazilmaz(kayit, sandbox_state):
    import pathlib
    k, d, saat = kayit
    once = sorted(str(p) for p in pathlib.Path(sandbox_state).rglob("*"))
    k.olay(*_emir("P-1", "AAPL"))
    k.q_geldi(_q("AAPL", 1, 1.1, "2026-09-14T13:45:01.000Z"))
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="1"))
    sonra = sorted(str(p) for p in pathlib.Path(sandbox_state).rglob("*"))
    assert once == sonra, "quotecapture state/ altına yazdı"


def test_A14_acilis_tohumu_mirror_orders_bekleyenleri_abone_kumesine_alir(tmp_path, sandbox_state,
                                                                         monkeypatch):
    """Açılış tohumu: restart sonrası bekleyen emirler dosyadan okunur — PENDING sözlüğü
    `mirror_stream` modülünden İTHAL edilir (kopya yok)."""
    from meridian import store, mirror_stream
    store.write_json(mirror_stream.STATE_FILE, {"orders": {
        "P-9": {"status": "new", "symbol": "TOHUM", "side": "buy"},
        "P-8": {"status": "filled", "symbol": "TERM", "side": "buy"}}})
    monkeypatch.setenv(qc.AKTIF_ENV, "1")
    monkeypatch.setenv(qc.DIZIN_ENV, str(tmp_path / "kayit"))
    k = qc.QuoteCapture(str(tmp_path / "kayit"), simdi=Saat())
    ab = k.istenen_abonelik()
    assert "TOHUM" in ab and "TERM" not in ab


def test_A15_bilinmeyen_olay_SESSIZ_degil_sayilir(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL", event="held", status="held"))
    assert k.snapshot()["bilinmeyen_olay_n"] == 1


def test_A16_GORELI_kayit_dizini_reddedilir_state_altina_baglanmaz(sandbox_state, monkeypatch):
    """kill#4 (göreli yol açığı, dal-sonu incelemesi bulgu 2): `store._path` MUTLAK adı olduğu gibi
    bırakır ama GÖRELİ adı `state/` altına BAĞLAR — yani göreli bir MERIDIAN_EDG085_KAYIT_DIZIN
    değeri quote kaydını sessizce canlı deftere düşürürdü. Göreli değer dizin YOKMUŞ gibi ele
    alınır: tek bayt yazılmaz, `dizin` None kalır, bir kez uyarılır (A11 deseni)."""
    import pathlib
    monkeypatch.setenv(qc.AKTIF_ENV, "1")
    monkeypatch.setenv(qc.DIZIN_ENV, "kayit/edg085")          # GÖRELİ — state/ altına bağlanırdı
    uyarilar = []
    monkeypatch.setattr(qc.obs, "warn", lambda ev, **f: uyarilar.append(ev))
    once = sorted(str(p) for p in pathlib.Path(sandbox_state).rglob("*"))
    k = qc.get()                                  # ÜRETİM YOLU: get() → _dizin_env()
    assert qc.get() is k, "tekil kurulmalı (uyarı da bir kez düşsün)"
    k.olay(*_emir("P-1", "AAPL"))
    k.q_geldi(_q("AAPL", 1, 1.1, "2026-09-14T13:45:01.000Z"))
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="1"))
    assert k.snapshot()["dizin"] is None, "göreli dizin kabul edildi"
    assert uyarilar.count("quote_capture_dizin_goreli") == 1, uyarilar
    assert sorted(str(p) for p in pathlib.Path(sandbox_state).rglob("*")) == once, \
        "göreli dizin state/ altına bağlandı — kill#4 ihlali"


def test_A17_baglanti_HIC_kurulmadan_dolum_BAGLANTI_YOK_der(kayit):
    """K7 (dal-sonu incelemesi): bağlantı bayrağının varsayılanı KAPALIDIR — ilk KANITLI canlılığa
    kadar "soket kuruldu" bilinmez. Worker açılışında auth'a takılan bir oturumda gelen quote'suz
    dolum `sembol_sessiz` diye ETİKETLENMEZ (teşhis yanlış olurdu: sembol değil soket sessizdi);
    kill#3 ihlali değil ama K ölçüsünün kayıp-nedeni dağılımını bozardı."""
    k, d, saat = kayit
    assert k.snapshot()["baglanti_ok"] is False, "varsayılan KAPALI olmalı"
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(3)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="100.15"))
    dolum = [r for r in _satirlar(d, "edg085_2026-09-14.jsonl") if r["tur"] == "dolum"][0]
    assert dolum["quote_n_pencere"] == 0 and dolum["kayip_nedeni"] == "baglanti_yok"


# =================================================================================================
# B) marketstream — `quotes` aboneliği (eşlik görevi) + `q` yönlendirme + sağlık
# =================================================================================================
from meridian import marketstream as mk                                    # noqa: E402
from tests.test_marketstream_v84 import FakeWS                             # noqa: E402  (TEK kaynak)


class KuyrukluWS(FakeWS):
    """Eşlik görevi test edilebilsin diye çerçeveler asyncio kuyruğundan gelir; test aralara olay
    sokar. `FakeWS` İTHAL edilir, kopyalanmaz (tek-kaynak yasası)."""

    def __init__(self):
        super().__init__([])
        self.kuyruk = asyncio.Queue()

    def __aiter__(self):
        async def _gen():
            while True:
                f = await self.kuyruk.get()
                if f is None:
                    return
                yield f
        return _gen()


@pytest.fixture(autouse=True)
def _sifirla():
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    qc._KAYIT = None
    yield
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    qc._KAYIT = None


def test_B1_bayrak_KAPALI_bit_ozdes_abonelik_yalniz_bars(sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "0")
    lis = mk.MarketStreamListener()
    ws = FakeWS([json.dumps({"T": "q", "S": "AAPL", "bp": 1, "ap": 1.1})])
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    asyncio.run(lis.session(ws, lambda: None))
    assert all("quotes" not in json.loads(s) for s in ws.sent)
    assert lis.snapshot()["quote_capture"] == {"aktif": False}


def test_B2_bayrak_ACIK_new_olayi_subscribe_quotes_gonderir_sonra_unsubscribe(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    ws = KuyrukluWS()

    async def senaryo():
        gorev = asyncio.ensure_future(lis.session(ws, lambda: None))
        await ws.kuyruk.put(json.dumps({"T": "success", "msg": "authenticated"}))
        await asyncio.sleep(0.05)
        k.olay("new", {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new"})
        await asyncio.sleep(0.05)
        await ws.kuyruk.put(json.dumps([{"T": "q", "S": "AAPL", "bp": 1.0, "ap": 1.1, "bs": 1,
                                         "as": 1, "t": "2026-09-14T13:45:01.000Z"}]))
        await asyncio.sleep(0.05)
        k.olay("canceled", {"client_order_id": "P-1", "symbol": "AAPL", "status": "canceled"})
        await asyncio.sleep(0.05)
        await ws.kuyruk.put(None)
        await gorev

    asyncio.run(senaryo())
    gond = [json.loads(s) for s in ws.sent]
    assert {"action": "subscribe", "quotes": ["AAPL"]} in gond
    assert {"action": "unsubscribe", "quotes": ["AAPL"]} in gond
    assert gond.index({"action": "subscribe", "quotes": ["AAPL"]}) > 1, "auth + bars aboneliğinden SONRA"
    assert _satirlar(d, "edg085_2026-09-14.jsonl") and k.snapshot()["son_q_at"]


def test_B3_q_cercevesi_hotstate_e_GITMEZ(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    got = []
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: (got.append(b), 0)[1])
    lis = mk.MarketStreamListener()
    bar = {"T": "b", "S": "AAPL", "o": 1, "h": 1, "l": 1, "c": 1, "t": "2026-09-14T13:45:00Z"}
    quote = {"T": "q", "S": "AAPL", "bp": 1, "ap": 1.1, "t": "2026-09-14T13:45:01Z"}
    # İKİ SIRA DA ÖLÇÜLÜR (mutasyon dersi 2026-09-13): yalnız "q önce, b sonra" sınandığında,
    # `q`yu batch'e sokan bir sızıntı b'nin ÜSTÜNE yazılıp GÖRÜNMEZ kalıyordu — çivi yanlış
    # sebeple yeşildi. Ters sırada aynı sızıntı barı EZER ve çivi ısırır.
    ws = FakeWS([json.dumps([quote, bar]), json.dumps([bar, quote])])
    asyncio.run(lis.session(ws, lambda: None))
    beklenen = {"AAPL": {"o": 1, "h": 1, "l": 1, "c": 1, "v": 0, "vw": None, "n": None,
                         "t": "2026-09-14T13:45:00Z"}}
    assert got == [beklenen, beklenen]


def test_B4_subscription_mesaji_quotes_sayisini_sagliga_yazar(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    ws = FakeWS([json.dumps([{"T": "subscription", "bars": ["AAPL"], "quotes": ["AAPL", "MSFT"]}])])
    asyncio.run(lis.session(ws, lambda: None))
    assert lis.snapshot()["quote_capture"]["soket_abone_n"] == 2


def test_B5_health_hic_kosmamis_quote_capture_aktif_false():
    assert mk.health()["quote_capture"] == {"aktif": False}


def test_B6_kopus_baglanti_bayragini_dusurur(kayit, monkeypatch):
    """Dolum işaretindeki `baglanti_yok` nedeninin kaynağı: oturum bitince bağlantı bayrağı düşer,
    KANITLI canlılıkta geri kalkar (uydurma yasağı: 'sessiz sembol' ile 'soket yok' ayrı şeydir)."""
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    k.baglanti(True)          # ÖNCE kaldır: aksi hâlde çivi varsayılanı ölçer, DÜŞÜŞÜ değil
    ws = FakeWS([json.dumps([{"T": "success", "msg": "authenticated"}])])
    asyncio.run(lis.session(ws, lambda: None))
    assert k.snapshot()["baglanti_ok"] is False, "oturum bittiğinde bağlantı bayrağı DÜŞMELİ"


def test_B7_KANITLI_canlilik_baglanti_bayragini_kaldirir(kayit, monkeypatch):
    """Bayrağın DİĞER yönü: varsayılan False'tan True'ya YALNIZ kanıtlı bir olay (auth'lı /
    abonelik / bar) çıkarır. `session` yerine `_mesaj_dongusu` ölçülür — `session`ın `finally`si
    bayrağı çıkışta zaten düşürür ve yükselişi görünmez kılardı."""
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    assert k.snapshot()["baglanti_ok"] is False, "varsayılan KAPALI olmalı (K7)"
    ws = FakeWS([json.dumps([{"T": "success", "msg": "authenticated"}])])
    asyncio.run(lis._mesaj_dongusu(ws, lambda: None))
    assert k.snapshot()["baglanti_ok"] is True, "KANITLI canlılık bağlantı bayrağını kaldırmalı"


def test_B8_oturum_biterken_ESLIK_gorevinin_bitmesi_BEKLENIR(kayit, monkeypatch):
    """Mercek 1 (dal-sonu incelemesi): `finally` içindeki `eslik.cancel()` yalnız bir İSTEKTİR.
    Beklenmezse `session()` görev HÂLÂ UÇUŞTAYKEN döner — döngü kapanırsa "Task was destroyed but
    it is pending" ya da yakalanmamış istisna riski doğar.

    YARIŞ GÖRÜNÜR KILINIR: eşlik görevinin iptali BİR TUR geciktirilir. Gecikmesiz hâlde olay
    döngüsünün geri-çağırma sırası yarışı TESADÜFEN örtüyor ve çivi yanlış sebeple yeşil kalıyordu
    (ölçüldü 2026-09-13); gecikmeyle `gather` gerçekten beklenmedikçe görev `done()` olmaz."""
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    ws = KuyrukluWS()
    gorevler = []
    orj = lis._q_abonelik

    async def yavas_iptal(w):
        gorevler.append(asyncio.current_task())
        try:
            await orj(w)
        except asyncio.CancelledError:
            await asyncio.sleep(0)        # iptal SONRASI bir tur daha — bekleyen var mı, görünsün
            raise

    monkeypatch.setattr(lis, "_q_abonelik", yavas_iptal)

    async def senaryo():
        gorev = asyncio.ensure_future(lis.session(ws, lambda: None))
        await ws.kuyruk.put(json.dumps({"T": "success", "msg": "authenticated"}))
        await asyncio.sleep(0.05)
        await ws.kuyruk.put(None)
        await gorev
        # ÖLÇÜM NOKTASI DÖNGÜNÜN İÇİDİR: `asyncio.run` döndükten sonra görev nasılsa toplanmış
        # olur ve `done()` her hâlde True okunur — çivi yanlış sebeple yeşile döner.
        return (gorevler[0].done() if gorevler else None,
                [t for t in asyncio.all_tasks() if t is not asyncio.current_task()])

    bitti, kalan = asyncio.run(senaryo())
    assert gorevler, "eşlik görevi hiç kurulmadı — senaryo bayrağı ölçmüyor"
    assert bitti is True, "session() eşlik görevi BİTMEDEN döndü (iptal await EDİLMİYOR)"
    assert kalan == [], f"oturum bitti ama uçuşta görev kaldı: {kalan}"


# =================================================================================================
# D) yapısal sınırlar — marketstream disk yolu yok · codelaw desen beyanı
# =================================================================================================

def test_D1_marketstream_yapisal_sinir_korunur():
    import inspect
    src = inspect.getsource(mk)
    for f in ("write_json", "write_jsonl", "append_jsonl", "write_text", "open("):
        assert f not in src, f"marketstream '{f}' içeremez (dosya yazımı quotecapture'da yaşar)"


def test_D2_codelaw_desen_beyani_var():
    from meridian import codelaw
    k = [a for a, s in codelaw.DECLARED_SINK_PATTERNS.items() if "EDG-2026-085" in s.get("gerekce", "")]
    assert len(k) == 1, f"EDG-085 desen beyanı tekil değil: {k}"
    assert {"sinif", "gerekce", "sinanamaz"} <= set(codelaw.DECLARED_SINK_PATTERNS[k[0]])
    # ANAHTAR KODDAN TÜRETİLİR (elle yazılmaz): `_joined_glob` sabit parçaları AYNEN korur, dizin
    # (attribute) ve gün defteri adı (yerel parametre) çözülemez → `*/edg085_*.jsonl`. Öneki
    # kaldıran ya da bir değişkene taşıyan bir değişiklik anahtarı ayrıştırır ve beyan ÖKSÜZ kalır.
    assert k[0] == "*/edg085_*.jsonl", "anahtar `_joined_glob` türetimiyle ayrıştı — orphan_patterns ihlali olur"


def test_D3_desenin_BEDELI_olculur_yalniz_quotecapture_karsilar():
    """BEDEL YASASI: `edg085_` öneki anahtarı daralttı ama SIFIRLAMADI — dizin ve gün hâlâ `*`tır,
    yani aynı f-string şekline (`<dizin>/edg085_<ad>.jsonl`) düşen BAŞKA bir yazar hâlâ sessizce
    bu beyanın altına girebilir. Çivi o sessizliği kapatır: desenin çağrı yerleri YALNIZ
    quotecapture olmalı; başka bir dosya düşerse beyan yeniden tartışılır."""
    from meridian import codelaw
    yerler = codelaw.artifact_graph()["declared_patterns"].get("*/edg085_*.jsonl", [])
    dosyalar = sorted({y.rsplit(":", 1)[0] for y in yerler})
    assert dosyalar == ["quotecapture.py"], f"beyanın altına yeni yazar girdi: {dosyalar}"



# =================================================================================================
# C) mirror_stream kancası — trade_updates olayı → quotecapture
# =================================================================================================
from meridian import mirror_stream as ms                                   # noqa: E402

#: ÖLÇÜLDÜ 2026-09-13: durum makinesinin adı `MirrorOrderStateMachine`tir (plan taslağı
#: "OrderStateMachine" diyordu — yer tutucu düzeltildi; ad kaynaktan okundu).
MAKINE = ms.MirrorOrderStateMachine


def test_C1_apply_olayi_quotecapture_a_iletir(kayit, monkeypatch, sandbox_state):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    sm = MAKINE()
    sm.apply("new", {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new",
                     "filled_qty": "0"})
    assert "AAPL" in k.istenen_abonelik()


def test_C2_mukerrer_olay_ILETILMEZ(kayit, monkeypatch, sandbox_state):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    sayac = []
    monkeypatch.setattr(k, "olay", lambda e, o: sayac.append(e))
    sm = MAKINE()
    o = {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new",
         "filled_qty": "0"}
    sm.apply("new", o)
    sm.apply("new", dict(o))
    assert sayac == ["new"], "mirror'ın v68 tekrar yasası kancadan ÖNCE dönmeli"


def test_C3_bayrak_KAPALI_kanca_erken_doner(monkeypatch, sandbox_state):
    monkeypatch.setenv(qc.AKTIF_ENV, "0")
    qc._KAYIT = None
    cagri = []
    monkeypatch.setattr(qc, "get", lambda: (cagri.append(1), None)[1])
    MAKINE().apply("new", {"client_order_id": "P-1", "symbol": "AAPL", "status": "new"})
    assert cagri == [], "bayrak kapalıyken quotecapture.get() bile çağrılmamalı"


def test_C4_bayat_terminal_olay_da_ILETILMEZ(kayit, monkeypatch, sandbox_state):
    """Terminal EMİCİDİR (v68): geri saran bayat olay kancaya da geçmemeli — aksi hâlde kapanmış
    bir emir EDG-085 penceresini yeniden açardı."""
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    sayac = []
    monkeypatch.setattr(k, "olay", lambda e, o: sayac.append(e))
    monkeypatch.setattr(ms.obs, "warn", lambda *a, **kw: None)
    sm = MAKINE()
    sm.apply("fill", {"client_order_id": "P-1", "symbol": "AAPL", "status": "filled",
                      "filled_qty": "10"})
    sm.apply("new", {"client_order_id": "P-1", "symbol": "AAPL", "status": "new",
                     "filled_qty": "0"})
    assert sayac == ["fill"]


def test_D4_dagitim_dropini_bayragi_VARSAYILAN_KAPALI(sandbox_state):
    """Pilot bayrağı canlıya KAPALI iner (kart adim_0_kaydi_2026_09_13: pilot en erken 09-21).
    Kayıt dizini repo ve state/ DIŞIDIR (kill#4) — drop-in bunu da taşır."""
    import pathlib
    p = (pathlib.Path(__file__).resolve().parents[1] / "deploy" / "oracle-a1" /
         "meridian.service.d" / "55-edg085-quote.conf")
    metin = p.read_text(encoding="utf-8")
    assert f"Environment={qc.AKTIF_ENV}=0" in metin, "pilot bayrağı KAPALI inmeli"
    dizin = [s.split("=", 2)[2].strip() for s in metin.splitlines()
             if s.startswith(f"Environment={qc.DIZIN_ENV}=")]
    assert len(dizin) == 1 and dizin[0].startswith("/opt/veri/"), dizin
    assert "/state" not in dizin[0] and "AI-Trading" not in dizin[0]
