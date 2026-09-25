"""test_cikis_acilisa_ertele_v545.py — TSK-205: karar çıkışı seans kapalıyken AÇILIŞA ERTELENİR.

VAKA (Rol-1 ölçümü, A1, 2026-09-25): akşam döngüsündeki karar çıkışı (`loop._mirror_exit_sync` →
`alpaca.close_engine_position`) seans KAPALIYKEN koruma bacaklarını iptal edip bir kapatma emri
gönderiyordu; kapatma kapalı seansta KUYRUKLANDI ve ertesi gerçek açılışa dek pozisyon korumasız
kaldı: NAKED_POSITION DE/MPC/MRNA/MU ~64 sa (Cuma 20:38Z → Pazartesi 12:21Z), PANW ~15,5 sa,
CRM 09-21 20:44Z. Kâğıt hesap — gerçek hesaba geçmeden kapanmalıydı.

KARAR (operatör 2026-09-25, seçenek (b)): seans KAPALIYKEN `close_engine_position` HİÇ çağrılmaz
(koruma bacaklarına dokunulmaz); karar kuyrukta "bekleyen çıkış" olarak kalır ve seans AÇIKKEN
çalışan ilk yolda (zamanlayıcının her poll'ü — `scheduler.advance_once` → `loop.mirror_exit_acilis_turu`)
iptal+kapatma art arda yapılır. İptal→kapat sırası ve B4 (yarım-durum üretilmez) DEĞİŞMEZ.

ÇİVİLER:
  A  seans kapalı → çağrı yok, koruma yerinde, kuyruk kalır, erteleme OLAYLI, deneme sayılmaz
  B  seans açılınca aynı girdi işlenir (iptal→kapat sırası), kitap DAR yamayla güncellenir
  C  seans açıkken bugünkü davranış AYNEN (regresyon)
  D  `naked` raporlaması: başarı dalı + `_mirror_exit_sync` ok dalı
  E  aynı-gün kısa yolu ("current" dalı) bekleyen çıkışı ENGELLEMEZ; bar yüklemesi düşse bile
  F  akşam mutabakatı bu turda ertelenen çıkış için arıza alarmı BASMAZ (planlı erteleme; mandal
     açılıştaki gerçek başarısızlığı yutmasın); işlenmeyen erteleme ertesi akşam AYRI cümleyle öter

YÖNTEM: hiçbir test ağa çıkmaz — adaptörün okuma uçları (`orders`/`positions`) saplanır, iptal ucu
kayıt tutar ve emir durumunu gerçekçi günceller, `httpx` kayıt edicidir. Saat `barclock.set_clock`
ile ÇİVİLENİR (duvar saatine bağlı suite geçtiğinde hiçbir şey kanıtlamaz); fikstür sıfırlar.
Tatil kör noktası (`is_market_open` resmi tatilleri bilmez) BU DİLİMDE çözülmedi — ayrı kalem.
"""
from __future__ import annotations

import copy
import datetime as dt

import pandas as pd
import pytest

from meridian import barclock, config, loop, store
from meridian.adapters import alpaca

UTC = dt.timezone.utc
FAKE_KEY = "PKCIKISV545FAKEKEY11223344"
FAKE_SECRET = "SKCIKISV545FAKESECRET5566778899"

# Ölçülen vakanın saatleri (EDT: ET = UTC-4)
KAPALI_CUMA_AKSAM = dt.datetime(2026, 9, 11, 20, 38, tzinfo=UTC)     # Cuma 16:38 ET — akşam döngüsü
CUMARTESI = dt.datetime(2026, 9, 12, 15, 0, tzinfo=UTC)              # hafta sonu
ACILIS_ONCESI = dt.datetime(2026, 9, 14, 13, 29, tzinfo=UTC)         # Pazartesi 09:29 ET
KAPANIS_ANI = dt.datetime(2026, 9, 14, 20, 0, tzinfo=UTC)            # Pazartesi 16:00 ET (kapalı sınır)
ACIK = dt.datetime(2026, 9, 14, 13, 35, tzinfo=UTC)                  # Pazartesi 09:35 ET
AKSAM_DSTR = "2026-09-11"


# =================================================================================================
# FİKSTÜRLER
# =================================================================================================
@pytest.fixture(autouse=True)
def _saat_sifirla():
    """`set_clock` modül-globaldir — donuk saat sonraki testlere SIZMASIN."""
    yield
    barclock.reset_clock()


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper`; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    yield sandbox_state
    secrets_mod.clear_cache()


def _saat(an: dt.datetime) -> None:
    barclock.set_clock(lambda: an)


def _bracket(sym: str, qty: int) -> dict:
    """Motorun DOLMUŞ giriş bracket'ı + CANLI GTC koruma bacakları (TP limit `new`, SL stop `held`)."""
    return {"id": f"id-giris-{sym}", "client_order_id": f"P-2026-09-10-{sym}", "symbol": sym,
            "side": "buy", "type": "limit", "time_in_force": "gtc", "order_class": "bracket",
            "status": "filled", "qty": str(qty), "filled_qty": str(qty),
            "legs": [{"id": f"leg-tp-{sym}", "client_order_id": f"alpaca-tp-{sym}", "symbol": sym,
                      "side": "sell", "type": "limit", "status": "new", "qty": str(qty),
                      "filled_qty": "0"},
                     {"id": f"leg-sl-{sym}", "client_order_id": f"alpaca-sl-{sym}", "symbol": sym,
                      "side": "sell", "type": "stop", "status": "held", "qty": str(qty),
                      "filled_qty": "0"}]}


_CANLI = ("new", "accepted", "pending_new", "held", "partially_filled", "accepted_for_bidding")


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._p = payload if payload is not None else {}

    def json(self):
        return self._p


def _tel(monkeypatch, emirler, pozisyonlar, delete_status=200):
    """Adaptör telleri. Dönen `sira` çağrıların SIRASINI taşır (iptal→kapat iddiasının kanıtı);
    `kce` ise `close_engine_position`ın GERÇEK gövdesini saran casustur (çağrı sayısı + argüman)."""
    sira: list = []
    kce: list = []

    def _orders(status="open", limit=50, nested=False, **_k):
        rows = [copy.deepcopy(o) for o in emirler]
        if str(status) == "open":
            rows = [o for o in rows if str(o.get("status")) in _CANLI
                    or any(str(l.get("status")) in _CANLI for l in o.get("legs") or [])]
        return rows

    def _cancel(oid):
        sira.append(("cancel", str(oid)))
        for o in emirler:
            for kayit in [o] + list(o.get("legs") or []):
                if str(kayit.get("id")) == str(oid):
                    kayit["status"] = "canceled"
        return {"ok": True}

    class _Cli:
        def delete(self, url, **kw):
            sira.append(("DELETE", url, (kw.get("params") or {}).get("qty")))
            if delete_status >= 400:
                return _Resp(delete_status, {"message": "close refused"})
            return _Resp(200, {"id": "kapatma-emri-1"})

    gercek = alpaca.close_engine_position

    def _casus(symbol, plan_id=None):
        kce.append((symbol, plan_id))
        return gercek(symbol, plan_id=plan_id)

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in pozisyonlar])
    monkeypatch.setattr(alpaca, "cancel_order", _cancel)
    monkeypatch.setattr(alpaca, "httpx", _Cli())
    monkeypatch.setattr(alpaca, "close_engine_position", _casus)
    return sira, kce


def _kuyruk(sym="DE", tries=0):
    return {sym: {"plan_id": f"P-2026-09-10-{sym}", "reason": "time_stop", "since": AKSAM_DSTR,
                  "tries": tries, "naked": False}}


def _olaylar(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _alarmlar(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


# =================================================================================================
# A · SEANS KAPALI → ÇAĞRI YOK, KORUMA YERİNDE, KUYRUK KALIR, ERTELEME OLAYLI
# =================================================================================================
@pytest.mark.parametrize("an", [KAPALI_CUMA_AKSAM, CUMARTESI, ACILIS_ONCESI, KAPANIS_ANI],
                         ids=["cuma_aksam_vaka", "cumartesi", "acilis_oncesi_0929", "kapanis_1600"])
def test_A1_seans_kapaliyken_kapatma_cagrilmaz_koruma_yerinde_kuyruk_kalir(ayna, monkeypatch, an):
    """ÇEKİRDEK: ölçülen vakanın akşam anında (ve diğer kapalı anlarda) `close_engine_position`
    HİÇ çağrılmaz — ne bacak iptali ne DELETE; kuyruk girdisi yerinde; erteleme OLAYLI."""
    _saat(an)
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    meta = {loop.MIRROR_EXIT_KEY: _kuyruk("DE")}

    out = loop._mirror_exit_sync(meta, AKSAM_DSTR)

    assert kce == [], f"seans kapalıyken kapatma çağrıldı: {kce}"
    assert sira == [], f"seans kapalıyken koruma/kapatma yüzeyine dokunuldu: {sira}"
    assert "DE" in meta[loop.MIRROR_EXIT_KEY], "ertelenen çıkış kuyruktan DÜŞTÜ"
    assert out["closed"] == [] and out["failed"] == []
    assert out["ertelendi"] == ["DE"]
    ev = _olaylar(loop.EV_CIKIS_ACILISA_ERTELENDI)
    assert ev and ev[-1].get("tickers") == ["DE"], "erteleme SESSİZ — olay defterinde iz yok"
    assert not _alarmlar("MIRROR_DRIFT"), "planlı erteleme arıza alarmı üretti"


def test_A2_erteleme_deneme_sayilmaz_ilk_erteleme_damgasi_korunur(ayna, monkeypatch):
    """Erteleme bir DENEME değildir (`tries` ilerlemez — deneme sayacı gerçek başarısızlıkları
    sayar); ilk erteleme damgası ikinci ertelemede EZİLMEZ (mutabakatın 'işlenmedi' dedektörü
    ona bakar)."""
    _saat(KAPALI_CUMA_AKSAM)
    _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    meta = {loop.MIRROR_EXIT_KEY: _kuyruk("DE", tries=2)}
    loop._mirror_exit_sync(meta, AKSAM_DSTR)
    _saat(CUMARTESI)
    loop._mirror_exit_sync(meta, "2026-09-12")
    girdi = meta[loop.MIRROR_EXIT_KEY]["DE"]
    assert girdi["tries"] == 2, f"erteleme deneme sayıldı: tries={girdi['tries']}"
    assert girdi[loop.ERTELEME_ILK_ALANI] == AKSAM_DSTR, "ilk erteleme damgası ezildi"


def test_A4_dongu_kapanisa_tasarsa_kalan_girdiler_ertelenir(ayna, monkeypatch):
    """Kapı girdi BAŞINA sorulur: ilk girdi 15:59'da denendi, döngü 16:00'ı geçtiyse ikinci girdi
    kapalı seansa kapatma GÖNDERMEZ (tek seferlik kapı döngü başında 'açık' der ve kalanları kör
    geçirirdi — vakanın küçük ölçekli tekrarı)."""
    saatler = iter([dt.datetime(2026, 9, 14, 19, 59, tzinfo=UTC)])          # 15:59 ET, sonra 16:00
    barclock.set_clock(lambda: next(saatler, KAPANIS_ANI))
    cagrilan: list = []

    def _kapat(t, plan_id=None):
        cagrilan.append(t)
        return {"ok": True, "owned": True, "closed_qty": 5.0, "naked": True, "cancelled": [],
                "close_order_id": f"k-{t}", "detail": ""}
    monkeypatch.setattr(alpaca, "close_engine_position", _kapat)
    meta = {loop.MIRROR_EXIT_KEY: {**_kuyruk("DE"), **_kuyruk("MU")}}
    out = loop._mirror_exit_sync(meta, "2026-09-14")
    assert cagrilan == ["DE"], f"kapanıştan sonra kapatma gönderildi: {cagrilan}"
    assert out["ertelendi"] == ["MU"] and list(meta[loop.MIRROR_EXIT_KEY]) == ["MU"]


def test_A3_kimlik_yoksa_eski_uyari_dali_aynen(ayna, monkeypatch):
    """POZİTİF KONTROL (kapı yalnız seans kapısı): kimlik yoksa eski `mirror_exit_deferred` uyarısı
    AYNEN basılır — seans kapısı o arıza sinyalini yutmaz."""
    _saat(KAPALI_CUMA_AKSAM)
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    meta = {loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    out = loop._mirror_exit_sync(meta, AKSAM_DSTR)
    assert out["skipped"] == "paper_available()=False"
    assert _olaylar("mirror_exit_deferred"), "kimlik arızası uyarısı kayboldu"


# =================================================================================================
# B · SEANS AÇILINCA AYNI GİRDİ İŞLENİR — İPTAL→KAPAT, DAR YAMA
# =================================================================================================
def _aksam_ertele_ve_kitaba_yaz(monkeypatch, syms=("DE",)):
    """Akşam döngüsünün yaptığı: kapalı seansta erteler, kitap diske iner (`_save_broker` yerine
    tam belge — yabancı anahtar + silahlı küme ile, dar yamanın dokunmadığını ölçmek için)."""
    _saat(KAPALI_CUMA_AKSAM)
    meta = {loop.MIRROR_EXIT_KEY: {}}
    for s in syms:
        meta[loop.MIRROR_EXIT_KEY].update(_kuyruk(s))
    loop._mirror_exit_sync(meta, AKSAM_DSTR)
    assert set(syms) <= set(meta[loop.MIRROR_EXIT_KEY]), "ön koşul: akşam ertelemesi kuyruğu boşalttı"
    kitap = {"cash": 1000.0, "realized_pnl": 0.0, "last_id": 7, "positions": {},
             "armed": [{"id": "P-2026-09-11-XOM", "ticker": "XOM"}],
             "alpaca_submitted": ["P-2026-09-11-XOM"], "last_date": AKSAM_DSTR,
             "sermaye_resetleri": [{"tarih": "2026-08-01", "tutar": 5000}],
             loop.MIRROR_EXIT_KEY: meta[loop.MIRROR_EXIT_KEY], loop.EXIT_FILL_KEY: {}}
    store.write_json(loop.PORTFOLIO, kitap)
    return kitap


def _bekleyen_kitaba_yaz(sym="DE"):
    """Akşam turunun bıraktığı kitap, DOĞRUDAN yazılır (E çivileri kapıdan bağımsız yalnız
    zamanlayıcı kablolamasını ölçsün — kapı kaldırılsa bile kurulum aynı kalır)."""
    q = _kuyruk(sym)
    q[sym][loop.ERTELEME_ILK_ALANI] = AKSAM_DSTR
    store.write_json(loop.PORTFOLIO, {"cash": 1000.0, "realized_pnl": 0.0, "last_id": 7,
                                      "positions": {}, "armed": [], "last_date": AKSAM_DSTR,
                                      loop.MIRROR_EXIT_KEY: q, loop.EXIT_FILL_KEY: {}})


def test_B1_seans_acilinca_ayni_girdi_islenir_iptal_sonra_kapat(ayna, monkeypatch):
    """Akşam ertelenen girdi, seans açıkken açılış turunda işlenir: önce koruma bacakları iptal,
    SONRA kapatma (B4 sırası aynen); kuyruk boşalır; karar-kolu dolum-yaması kaydı kimlikle düşer."""
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _aksam_ertele_ve_kitaba_yaz(monkeypatch)
    assert kce == [], "ön koşul: akşam hiçbir şey çağrılmamalıydı"

    _saat(ACIK)
    sonuc = loop.mirror_exit_acilis_turu()

    assert kce == [("DE", "P-2026-09-10-DE")], f"açılışta kapatma çağrılmadı: {kce}"
    iptal_i = [i for i, s in enumerate(sira) if s[0] == "cancel"]
    del_i = [i for i, s in enumerate(sira) if s[0] == "DELETE"]
    assert {sira[i][1] for i in iptal_i} == {"leg-tp-DE", "leg-sl-DE"}
    assert len(del_i) == 1 and sira[del_i[0]][2] == "10"
    assert max(iptal_i) < del_i[0], "kapatma iptallerden ÖNCE gitti — iptal→kapat sırası bozuk"
    assert sonuc["calisti"] is True and [c["ticker"] for c in sonuc["closed"]] == ["DE"]
    kitap = store.read_json(loop.PORTFOLIO, {})
    assert kitap[loop.MIRROR_EXIT_KEY] == {}, "başarılı kapatma kitaptaki kuyruktan düşmedi"
    efk = kitap[loop.EXIT_FILL_KEY]["P-2026-09-10-DE"]
    assert efk["kaynak"] == "karar" and efk["order_id"] == "kapatma-emri-1"
    assert _olaylar("mirror_exit_closed"), "açılış kapatması olaysız"


def test_B2_dar_yama_kitabin_kalanina_dokunmaz(ayna, monkeypatch):
    """Açılış turu kitabı TAM yazmaz: silahlı küme, gönderim dedup kümesi ve sermaye beyanı
    (yabancı anahtar) yerinde kalır — `mirror_submit_ve_kalicilastir`in dar yama deseni."""
    _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    once = _aksam_ertele_ve_kitaba_yaz(monkeypatch)
    _saat(ACIK)
    loop.mirror_exit_acilis_turu()
    sonra = store.read_json(loop.PORTFOLIO, {})
    for k in ("armed", "alpaca_submitted", "sermaye_resetleri", "cash", "last_id", "last_date"):
        assert sonra.get(k) == once.get(k), f"açılış turu `{k}` alanını değiştirdi"


def test_B3_acilis_turu_seans_kapaliyken_sifir_dokunus_sifir_olay(ayna, monkeypatch):
    """Zamanlayıcı her poll'de çağırır (hafta içi gece 17,5 sa / 300 sn ≈ 210 kez): seans
    kapalıyken ne adaptöre ne kitaba dokunur ve olay BASMAZ (erteleme akşam döngüsünde bir kez
    anlatıldı; her poll'de yeniden anlatmak olay defterini bilgi taşımayan satırlarla doldururdu)."""
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _aksam_ertele_ve_kitaba_yaz(monkeypatch)
    n_olay = len(store.read_jsonl("events.jsonl"))
    once = store.read_json(loop.PORTFOLIO, {})
    for an in (CUMARTESI, ACILIS_ONCESI):
        _saat(an)
        sonuc = loop.mirror_exit_acilis_turu()
        assert sonuc["calisti"] is False and sonuc["neden"] == "seans_kapali"
    assert kce == [] and sira == []
    assert len(store.read_jsonl("events.jsonl")) == n_olay, "kapalı seans poll'ü olay bastı"
    assert store.read_json(loop.PORTFOLIO, {}) == once, "kapalı seans poll'ü kitaba yazdı"


def test_B4_bos_kuyruk_ve_ic_broker_hic_dokunmaz(ayna, monkeypatch):
    """Kuyruk boşsa (normal gün) ya da iç-broker modunda tur hiçbir yüzeye dokunmaz."""
    sira, kce = _tel(monkeypatch, [], [])
    _saat(ACIK)
    store.write_json(loop.PORTFOLIO, {"armed": [], loop.MIRROR_EXIT_KEY: {}})
    assert loop.mirror_exit_acilis_turu()["neden"] == "kuyruk_bos"
    monkeypatch.setattr(config, "BROKER", "internal")
    store.write_json(loop.PORTFOLIO, {"armed": [], loop.MIRROR_EXIT_KEY: _kuyruk("DE")})
    assert loop.mirror_exit_acilis_turu()["calisti"] is False
    assert kce == [] and sira == []


def test_B5_acilista_kapatma_duserse_kuyrukta_kalir_alarm_ve_isaret_temizlenir(ayna, monkeypatch):
    """Açılış denemesi DÜŞERSE: kuyrukta kalır (tries 1), alarm basılır, `naked` beyanı kitaba
    iner ve erteleme damgası TEMİZLENİR (artık 'denenmemiş erteleme' değil, 'başarısız deneme')."""
    _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}], delete_status=422)
    _aksam_ertele_ve_kitaba_yaz(monkeypatch)
    _saat(ACIK)
    sonuc = loop.mirror_exit_acilis_turu()
    assert sonuc["failed"] and not sonuc["closed"]
    girdi = store.read_json(loop.PORTFOLIO, {})[loop.MIRROR_EXIT_KEY]["DE"]
    assert girdi["tries"] == 1 and girdi["naked"] is True
    assert loop.ERTELEME_ILK_ALANI not in girdi, "denenmiş girdi hâlâ 'ertelendi' işaretli"
    assert any(e.get("drift_sinifi") == "cikis_yetimi" for e in _alarmlar("MIRROR_DRIFT"))


# =================================================================================================
# C · SEANS AÇIKKEN BUGÜNKÜ DAVRANIŞ AYNEN (REGRESYON)
# =================================================================================================
def test_C1_seans_acikken_mirror_exit_sync_bugunku_gibi_kapatir(ayna, monkeypatch):
    """Gün içi yetişme turu (bar ertesi seansta geldi) ya da elle döngü seans AÇIKKEN koşarsa
    davranış bugünkünün birebir aynısı: çağrı, iptal→kapat, kuyruk boşalır, karar kaydı düşer."""
    _saat(ACIK)
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    meta = {loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    out = loop._mirror_exit_sync(meta, "2026-09-14")
    assert kce == [("DE", "P-2026-09-10-DE")]
    assert [c["ticker"] for c in out["closed"]] == ["DE"] and out["closed"][0]["tries"] == 1
    assert meta[loop.MIRROR_EXIT_KEY] == {} and out["ertelendi"] == []
    assert meta[loop.EXIT_FILL_KEY]["P-2026-09-10-DE"]["kaynak"] == "karar"
    assert not _olaylar(loop.EV_CIKIS_ACILISA_ERTELENDI), "açık seansta erteleme olayı basıldı"
    assert [s[0] for s in sira][-1] == "DELETE"


def test_C2_daily_cycle_kablolamasi_degismedi():
    """Karar çıkışı hâlâ kuyruğa yazılır ve AYNI turda `_mirror_exit_sync`e verilir — kapı
    senkronun İÇİNDEDİR, çağrı yerinde değil (akşam turunun da kapıdan geçmesi için)."""
    import inspect
    src = inspect.getsource(loop.daily_cycle)
    i = src.index('meta.get("pending_exits", {}).items()')
    assert "_mirror_exit_enqueue(" in src[i:i + 700] and "_mirror_exit_sync(" in src[i:i + 900]
    kaynak = inspect.getsource(loop._mirror_exit_sync)
    assert "barclock.is_market_open(" in kaynak, "seans kapısı senkronun içinde değil"


# =================================================================================================
# D · `naked` RAPORLAMASI
# =================================================================================================
def test_D1_basari_dalinda_koruma_iptal_edildiyse_naked_True(ayna, monkeypatch):
    """`close_engine_position` başarı dalı: koruma bacakları GERÇEKTEN iptal edildi ve kapatma
    emri henüz dolmadı → `naked: True` (eski gövde başlangıç değerini — False — aynen dönüyordu)."""
    _saat(ACIK)
    _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    res = alpaca.close_engine_position("DE", plan_id="P-2026-09-10-DE")
    assert res["ok"] is True and res["closed_qty"] == 10.0
    assert res["naked"] is True, "koruma söküldü ama başarı dalı çıplak pencereyi beyan etmedi"


def test_D1b_koruma_bacagi_yoksa_basari_dalinda_naked_False(ayna, monkeypatch):
    """POZİTİF KONTROL: sökülecek canlı koruma yoksa başarı dalı `naked: False` kalır — alan
    'her başarıda True' diye sabitlenmedi, iptal kaydından TÜRETİLİYOR."""
    _saat(ACIK)
    b = _bracket("DE", 10)
    for leg in b["legs"]:
        leg["status"] = "expired"
    _tel(monkeypatch, [b], [{"symbol": "DE", "qty": "10"}])
    res = alpaca.close_engine_position("DE", plan_id="P-2026-09-10-DE")
    assert res["ok"] is True and res["naked"] is False


def test_D2_sync_ok_dali_naked_beyanini_olaya_ve_sonuca_tasir(ayna, monkeypatch):
    """`_mirror_exit_sync` ok dalı `naked`i OKUR: `mirror_exit_closed` olayı ve dönüşteki `closed`
    satırı taşır. POZİTİF KONTROL: `naked: False` dönen kapatmada olay False taşır."""
    _saat(ACIK)
    cevaplar = {"DE": True, "MU": False}
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": True, "owned": True, "closed_qty": 5.0,
                                                 "naked": cevaplar[t], "cancelled": [],
                                                 "close_order_id": f"k-{t}", "detail": ""})
    meta = {loop.MIRROR_EXIT_KEY: {**_kuyruk("DE"), **_kuyruk("MU")}}
    out = loop._mirror_exit_sync(meta, "2026-09-14")
    by_t = {c["ticker"]: c for c in out["closed"]}
    assert by_t["DE"]["naked"] is True and by_t["MU"]["naked"] is False
    ev = {e["ticker"]: e for e in _olaylar("mirror_exit_closed")}
    assert ev["DE"].get("naked") is True, "ok dalı naked beyanını olaya taşımıyor"
    assert ev["MU"].get("naked") is False


# =================================================================================================
# E · AYNI-GÜN KISA YOLU BEKLEYEN ÇIKIŞI ENGELLEMEZ (scheduler.advance_once)
# =================================================================================================
class _Dur(RuntimeError):
    """Testin akışı KONTROLLÜ kestiği nokta."""


def _zamanlayici_kur(monkeypatch, *, load_live):
    from meridian import dataset, scheduler, watchdog
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: AKSAM_DSTR)
    monkeypatch.setattr(scheduler.health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    monkeypatch.setattr(scheduler, "_intraday_gap_check", lambda: None)
    monkeypatch.setattr(watchdog, "check_and_alarm", lambda *a, **k: None)
    monkeypatch.setattr(dataset, "load_live", load_live)
    # seans barı ZATEN geldi ve işlendi: sık/seyrek faz kapalı, poll "current" dalına gider
    scheduler._state.update(refetch_chase=None, last_refetch_session=AKSAM_DSTR,
                            refetch_attempts=0, refetch_sparse_attempts=0,
                            learn_session=AKSAM_DSTR, dolgu_session=AKSAM_DSTR)
    return scheduler


def test_E1_current_dali_bekleyen_cikisi_engellemez(ayna, monkeypatch):
    """VAKANIN ASIL KİLİDİ: seanslar arası ~24 saatlik kararlı durumda her poll "current" dalına
    düşer ve `daily_cycle` HİÇ çağrılmaz (akşam turu da aynı gün `bar already processed` der).
    Açılış turu bu kısa yoldan ÖNCE koştuğu için bekleyen çıkış seans açılınca işlenir."""
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _bekleyen_kitaba_yaz()
    idx = pd.DataFrame({"date": pd.to_datetime([AKSAM_DSTR]), "close": [1.0]})
    sch = _zamanlayici_kur(monkeypatch, load_live=lambda *a, **k: ({}, idx))
    from meridian import hermes, sprint
    monkeypatch.setattr(hermes, "review_backlog", lambda **k: None)
    monkeypatch.setattr(sprint, "maybe_start", lambda **k: {"status": "skip"})

    _saat(ACIK)
    assert kce == [], "ön koşul"
    sonuc = sch.advance_once()

    assert sonuc["status"] == "current", f"ön koşul: kısa yol dalı değil: {sonuc}"
    assert kce == [("DE", "P-2026-09-10-DE")], "aynı-gün kısa yolu bekleyen çıkışı engelledi"
    assert store.read_json(loop.PORTFOLIO, {})[loop.MIRROR_EXIT_KEY] == {}


def test_E2_bar_yuklemesi_duserse_bile_acilis_turu_once_kosar(ayna, monkeypatch):
    """Veri sağlayıcı kesintisi (bar yükleme istisnası) çıkışı bloklamaz: açılış turu bar
    yüklemesinden ÖNCE koşar — çıkış icrası günlük veri hattına bağlı DEĞİLDİR."""
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _bekleyen_kitaba_yaz()
    sch = _zamanlayici_kur(monkeypatch, load_live=lambda *a, **k: (_ for _ in ()).throw(_Dur()))
    _saat(ACIK)
    with pytest.raises(_Dur):
        sch.advance_once()
    assert kce == [("DE", "P-2026-09-10-DE")]


def test_E3_halt_acilis_turunu_da_durdurur(ayna, monkeypatch):
    """KARAR BEYANI: HALT (kill-switch) açıkken zamanlayıcı HİÇBİR şey yapmaz — akşam turu da
    koşmaz; açılış turu bu yasayı delmez. Korumalar yerinde kaldığı için bekleme güvenli yöndür."""
    sira, kce = _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _bekleyen_kitaba_yaz()
    sch = _zamanlayici_kur(monkeypatch, load_live=lambda *a, **k: (_ for _ in ()).throw(_Dur()))
    monkeypatch.setattr(sch.health, "halted", lambda: True)
    _saat(ACIK)
    assert sch.advance_once()["status"] == "halted"
    assert kce == [] and sira == []


def test_E4_acilis_turu_istisnasi_poll_u_dusurmez_ve_sessiz_degil(ayna, monkeypatch):
    """Tur patlarsa poll düşmez (kuyruk diskte, sonraki poll yeniden dener) ve bu SESSİZ değildir."""
    _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])
    _bekleyen_kitaba_yaz()
    sch = _zamanlayici_kur(monkeypatch, load_live=lambda *a, **k: (_ for _ in ()).throw(_Dur()))

    def _patla():
        raise RuntimeError("tur çöktü")
    monkeypatch.setattr(loop, "mirror_exit_acilis_turu", _patla)
    _saat(ACIK)
    with pytest.raises(_Dur):                 # poll açılış turunu geçip bar yüklemesine VARDI
        sch.advance_once()
    assert _olaylar("mirror_exit_acilis_dustu"), "açılış turu arızası sessiz"


# =================================================================================================
# F · AKŞAM MUTABAKATI ERTELENMİŞ ÇIKIŞI DOĞRU ANLATIR
# =================================================================================================
def _mutabakat_tel(monkeypatch):
    """Mutabakat da aynı tellerden okur (dolmuş motor parent'ı + aynada açık pozisyon) — iptal/
    DELETE uçları da saplı, mutasyon altında bile hiçbir çağrı ağa çıkamaz."""
    return _tel(monkeypatch, [_bracket("DE", 10)], [{"symbol": "DE", "qty": "10"}])


def test_F1_bu_turda_ertelenen_cikis_alarm_uretmez_liste_uyeligi_aynen(ayna, monkeypatch):
    """Akşam: senkron erteledi, aynı turun mutabakatı sembolü `exit_orphans`ta görür. PLANLI
    ERTELEME ALARM DEĞİLDİR (karar notu (b)): 'kapatılamadı' alarmı BASILMAZ — erteleme aynı
    turda `mirror_exit_acilisa_ertelendi` olayıyla anlatıldı. Alarm basılsaydı MIRROR_DRIFT mandalı
    (imza ticker+drift_sinifi, 96 sa) açılıştaki GERÇEK başarısızlık alarmını YUTARDI.
    Liste üyeliği AYNEN (`exit_orphans` — `_mirror_busy`/pano okuyucuları bozulmaz)."""
    _saat(KAPALI_CUMA_AKSAM)
    _mutabakat_tel(monkeypatch)
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    loop._mirror_exit_sync(meta, AKSAM_DSTR)
    out = loop.reconcile_broker_state(meta, AKSAM_DSTR, [], open_positions={})
    assert out["positions"]["exit_orphans"] == ["DE"]
    assert not [e for e in _alarmlar("MIRROR_DRIFT") if e.get("ticker") == "DE"], \
        "planlı erteleme akşam mutabakatında arıza alarmı üretti"
    assert _olaylar(loop.EV_CIKIS_ACILISA_ERTELENDI), "erteleme aynı turda anlatılmadı"


def test_F1b_ertelemeden_sonra_acilis_basarisizligi_mandala_yutulmaz(ayna, monkeypatch):
    """MANDAL ETKİLEŞİMİ (uçtan uca): Cuma akşamı erteleme + mutabakat → Pazartesi açılışında
    kapatma DÜŞER → `cikis_yetimi` alarmı SATIR olarak basılır (bastırılmış mandal kaydı değil)."""
    _mutabakat_tel(monkeypatch)
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    _saat(KAPALI_CUMA_AKSAM)
    loop._mirror_exit_sync(meta, AKSAM_DSTR)
    loop.reconcile_broker_state(meta, AKSAM_DSTR, [], open_positions={})
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": False, "owned": True, "naked": True,
                                                 "detail": "422 insufficient qty"})
    _saat(ACIK)
    loop._mirror_exit_sync(meta, "2026-09-14")
    # Açılış başarısızlığının KENDİ satırı aranır (senkronun cümlesi) — Cuma'dan kalma başka bir
    # `cikis_yetimi` satırı bu iddiayı karşılayamaz.
    ev = [e for e in _alarmlar("MIRROR_DRIFT") if e.get("ticker") == "DE"
          and "ayna çıkışı kapatılamadı" in str(e.get("message"))]
    assert ev, "açılış başarısızlığı alarm SATIRI yok — mandalda yutuldu"
    assert ev[-1].get("drift_sinifi") == "cikis_yetimi" and ev[-1].get("tries") == 1


def test_F2_islenmeyen_erteleme_ertesi_aksam_ayri_cumleyle_oter(ayna, monkeypatch):
    """Açılış turu hiç koşmadıysa (zamanlayıcı ölü/HALT) ertesi akşam girdi HÂLÂ ilk erteleme
    damgasıyla kuyruktadır — alarm bunu 'seans içinde DENENMEDİ' diye adlandırır."""
    _mutabakat_tel(monkeypatch)
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    _saat(KAPALI_CUMA_AKSAM)
    loop._mirror_exit_sync(meta, AKSAM_DSTR)
    _saat(dt.datetime(2026, 9, 14, 20, 40, tzinfo=UTC))          # Pazartesi akşamı
    loop._mirror_exit_sync(meta, "2026-09-14")
    loop.reconcile_broker_state(meta, "2026-09-14", [], open_positions={})
    ev = [e for e in _alarmlar("MIRROR_DRIFT") if e.get("ticker") == "DE"]
    assert ev and "DENENMEDİ" in str(ev[-1]), str(ev[-1] if ev else None)
    assert ev[-1].get("drift_sinifi") == "cikis_yetimi"
    assert ev[-1].get(loop.ERTELEME_ILK_ALANI) == AKSAM_DSTR


def test_F3_isaretsiz_cikis_yetimi_eski_cumleyle_oter(ayna, monkeypatch):
    """POZİTİF KONTROL: erteleme işareti taşımayan (başarısız denemeden kalan) çıkış yetimi eski
    'kapatılamadı' cümlesiyle öter — yeni dal eski teşhisi YUTMAZ."""
    _saat(KAPALI_CUMA_AKSAM)
    _mutabakat_tel(monkeypatch)
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: _kuyruk("DE", tries=3)}
    loop.reconcile_broker_state(meta, AKSAM_DSTR, [], open_positions={})
    ev = [e for e in _alarmlar("MIRROR_DRIFT") if e.get("ticker") == "DE"]
    assert ev and "kapatılamadı" in str(ev[-1]) and loop.ERTELEME_ILK_ALANI not in ev[-1]
