"""test_wpe_dolum_boslugu_v234.py — WP-E ayna-dolum teşhisinin KALAN 6 boşluğu
(docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md; B3+B4 v232'de kapandı, bu dosya kalanları kapatır).

  B1 — karar_cikisi_dolum_korlugu: DELETE /positions kapatmasının GERÇEK dolum fiyatı hiçbir
       deftere akmıyordu (~%38 kapanış; slipaj örneklemi TP/SL-bacağına yanlıydı). Artık DELETE
       cevabındaki emir kimliği (`close_order_id`) kalıcı kuyruğa düşer ve reconcile o emrin
       `filled_avg_price`ını trades satırına yamalar (E2 giriş-yamasının çıkış simetriği).
  B2 — tek_atis_yamasi: eski (1.3) yalnız aynı-tur kapananlara bakıyordu; arıza/geç-dolum kalıcı
       kayıptı. Kuyruk `EXIT_FILL_MAX_TRIES` tura kadar yeniden dener, vazgeçiş OLAYLI + satıra
       dürüst beyan (fiyat UYDURULMAZ: None + neden; `alpaca_fill_price` anahtarı açılmaz ki geç
       gelen gerçek dolum hâlâ yamanabilsin).
  B5 — kismi_dolum: (a) E2 satırı ilk kısmi fotoğrafta DONMAZ (terminal olana dek tazelenir);
       (b) adet sapmasında `kismi_dolum` sınıfı emrin KENDİ kanıtından (filled_qty<qty) türetilir;
       (c) makbuzsuz sapmanın adı `makbuzsuz_boyut` (ROADMAP Ö-7 — sb2 dosyasında da sınanır).
  B6 — fill_eq_now_anakronizmi: yaşlı pozisyonun adet sapması BUGÜNÜN sermayesiyle KIYASLANMAZ —
       makbuzda `dolum_eq` damgası varsa o, pozisyon bu seansta dolduysa bugünün açılış tabanı,
       yoksa dürüst `olculemedi` (+anakronizm nedeni). İç dolum anı makbuza damga basar.
  B7 — pencere_bosluklari: (a) emir penceresi `until`-imleciyle SAYFALI; hedef (dolum bekleyen en
       eski kayıt) kapsanamazsa beyanlı (`kapsandi=False` + olay). (b) reconcile'ın koşmadığı gün
       sınıfı (`noop`/`waiting_for_universe`/`refused_regressive`) OLAYLANIR.
  B8 — motor_yetimi üç ayrı olgu: `tasima_gecikmesi` / `cikis_gecikmesi` / `giris_yetimi` alt
       adlarıyla sınıflanır; `engine_orphans` listesi ve `_mirror_busy` kilidi DEĞİŞMEZ (bu tur
       görünürlük turu — EMİR ÜRETMEZ, kabul/kapatma operatör kararıdır).

YÖNTEM: ağa çıkılmaz — okuma uçları saplanır; her iddianın yanında POZİTİF KONTROL vardır.
"""
from __future__ import annotations

import copy
import inspect

import pytest

from meridian import config, loop, store
from meridian.adapters import alpaca

FAKE_KEY = "PKWPEDOLUMV234FAKEKEY11223"
FAKE_SECRET = "SKWPEDOLUMV234FAKESECRET4455"
D = "2026-08-12"


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper`; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    yield sandbox_state
    secrets_mod.clear_cache()


def _events(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


def _wire(monkeypatch, orders=(), positions=()):
    monkeypatch.setattr(alpaca, "orders", lambda **k: [copy.deepcopy(o) for o in orders])
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in positions])


def _trade_satiri(pid="P-2026-08-11-NUE", sym="NUE", exit_=100.0, reason="time_stop",
                  ts_close="2026-08-11"):
    row = {"plan_id": pid, "ticker": sym, "exit": exit_, "exit_reason": reason,
           "ts_close": ts_close, "qty": 25}
    store.append_jsonl("trades.jsonl", dict(row))
    return row


def _kapatma_emri(oid="close-ord-1", sym="NUE", price=99.4, status="filled"):
    """DELETE /positions'ın doğurduğu market SELL — coid Alpaca-üretimi (plan_id DEĞİL)."""
    return {"id": oid, "client_order_id": "9af1-alpaca-uuid", "symbol": sym, "side": "sell",
            "type": "market", "status": status, "qty": "25", "filled_qty": "25",
            "filled_avg_price": (str(price) if price is not None else None), "legs": [],
            "submitted_at": "2026-08-11T20:01:00Z"}


def _giris_parent(sym, qty, pid=None, status="filled", fq=None, avg=None,
                  submitted="2026-08-11T13:30:00Z", legs=()):
    return {"id": f"id-giris-{sym}", "client_order_id": pid or f"P-2026-08-11-{sym}",
            "symbol": sym, "side": "buy", "type": "limit", "status": status, "qty": str(qty),
            "filled_qty": str(fq if fq is not None else (qty if status == "filled" else 0)),
            "filled_avg_price": (str(avg) if avg is not None else None),
            "submitted_at": submitted, "legs": list(legs)}


# =================================================================================================
# B1 · KARAR-ÇIKIŞI DOLUM KÖRLÜĞÜ — DELETE cevabı → kuyruk → satır yaması
# =================================================================================================
class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._p = payload

    def json(self):
        if isinstance(self._p, Exception):
            raise self._p
        return self._p if self._p is not None else {}


def test_B1_delete_cevabi_close_order_id_tasir(ayna, monkeypatch):
    """ÇEKİRDEK OKUMA UCU: kapatma DELETE'inin cevabındaki emir kimliği dönüşte taşınır.
    POZİTİF KONTROL: gövde okunamazsa kimlik UYDURULMAZ — None + neden."""
    emirler = [_giris_parent("NUE", 25)]

    class _Cli:
        def __init__(self, payload):
            self._p = payload

        def delete(self, url, **kw):
            return _Resp(200, self._p)

    monkeypatch.setattr(alpaca, "orders", lambda **k: [copy.deepcopy(o) for o in emirler])
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "NUE", "qty": "25"}])
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: {"ok": True})

    monkeypatch.setattr(alpaca, "httpx", _Cli({"id": "close-ord-1", "symbol": "NUE"}))
    res = alpaca.close_engine_position("NUE", plan_id="P-2026-08-11-NUE")
    assert res["ok"] is True and res["close_order_id"] == "close-ord-1"
    assert res["close_order_neden"] is None

    monkeypatch.setattr(alpaca, "httpx", _Cli(ValueError("bozuk gövde")))
    res2 = alpaca.close_engine_position("NUE", plan_id="P-2026-08-11-NUE")
    assert res2["ok"] is True and res2["close_order_id"] is None
    assert res2["close_order_neden"] and len(res2["close_order_neden"]) >= 10, \
        "kimlik okunamadı ama neden yazılmadı (uydurma yasağı yarım)"


def test_B1_kapatma_basarisi_kuyruga_kimlikli_kayit_dusurur(ayna, monkeypatch):
    """`_mirror_exit_sync` başarı dalı: dolum-yaması kuyruğuna `kaynak=karar` + `close_order_id`
    kaydı düşer ve `mirror_exit_closed` olayı kimliği taşır (olay-katmanı yüzü)."""
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": True, "owned": True, "closed_qty": 25.0,
                                                 "cancelled": [], "naked": False,
                                                 "close_order_id": "close-ord-1",
                                                 "close_order_neden": None, "detail": ""})
    meta = {loop.MIRROR_EXIT_KEY: {"NUE": {"plan_id": "P-2026-08-11-NUE",
                                           "reason": "time_stop", "tries": 0}}}
    out = loop._mirror_exit_sync(meta, "2026-08-11")
    assert out["closed"] and meta[loop.MIRROR_EXIT_KEY] == {}
    kayit = meta[loop.EXIT_FILL_KEY]["P-2026-08-11-NUE"]
    assert kayit["kaynak"] == "karar" and kayit["order_id"] == "close-ord-1"
    assert kayit["ticker"] == "NUE" and kayit["tries"] == 0
    ev = [e for e in _events("mirror_exit_closed") if e.get("ticker") == "NUE"]
    assert ev and ev[-1].get("close_order_id") == "close-ord-1", \
        "olay kapatma emrinin kimliğini taşımıyor (B1 olay-katmanı)"


def test_B1_kapatilacak_pozisyon_yoksa_kuyruk_ACILMAZ(ayna, monkeypatch):
    """POZİTİF KONTROL: `closed_qty=0` (pozisyon zaten yoktu) dalında ölçülecek dolum yok —
    kuyruğa kayıt düşmez (sahte 'ölçülemedi' beyanları üretilmez)."""
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": True, "owned": True, "closed_qty": 0.0,
                                                 "cancelled": [], "naked": False,
                                                 "close_order_id": None,
                                                 "close_order_neden": None,
                                                 "detail": "kapatılacak motor pozisyonu yok"})
    meta = {loop.MIRROR_EXIT_KEY: {"NUE": {"plan_id": "P-X", "reason": "time_stop", "tries": 0}}}
    loop._mirror_exit_sync(meta, "2026-08-11")
    assert loop.EXIT_FILL_KEY not in meta or meta[loop.EXIT_FILL_KEY] == {}


def test_B1_reconcile_karar_dolumunu_satira_yamalar_penceden(ayna, monkeypatch):
    """UÇTAN UCA: kuyrukta `karar` kaydı + pencerede kapatma emri (kimlikle) → trades satırına
    `alpaca_fill_price + mirror_divergence` yazılır, kuyruk boşalır, olay düşer. Sapma eşik
    üstündeyse `icra` sınıflı MIRROR_DRIFT (eski 1.3 ile aynı eşik) — burada eşik altı."""
    _trade_satiri(exit_=99.5)                                  # sim çıkış 99.5, gerçek 99.4
    _wire(monkeypatch, orders=[_kapatma_emri(price=99.4)], positions=[])
    meta = {"armed": [],
            loop.EXIT_FILL_KEY: {"P-2026-08-11-NUE": {"ticker": "NUE", "kaynak": "karar",
                                                      "order_id": "close-ord-1",
                                                      "reason": "time_stop",
                                                      "since": "2026-08-11", "tries": 0}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-NUE"][-1]
    assert satir.get("alpaca_fill_price") == 99.4, "karar-çıkışı dolumu satıra akmadı (B1 özü)"
    assert satir.get("mirror_divergence") == round(abs(99.4 - 99.5) / 99.5, 5)   # 5 ondalık (1.3 yasası)
    assert meta[loop.EXIT_FILL_KEY] == {}, "yamalanan kayıt kuyruktan düşmedi"
    assert out["exit_fill"] == {"bekleyen": 0, "yamalanan": 1, "vazgecilen": 0}
    ev = [e for e in _events("mirror_exit_fill_patched")]
    assert ev and ev[-1].get("kaynak") == "karar" and ev[-1].get("alpaca_fill") == 99.4
    assert out["drift"] == [], "eşik altı sapma drift üretti — eşik davranışı değişmiş"


def test_B1_pencere_disi_kapatma_emri_kimlikle_GETlenir(ayna, monkeypatch):
    """Kapatma emri liste PENCERESİNDE YOK (limit taşması) → `order_by_id` tekil GET'i devreye
    girer ve yama yine yazılır — pencere boşluğundan bağımsızlık B1'in ikinci yarısı."""
    _trade_satiri(exit_=100.0)
    _wire(monkeypatch, orders=[], positions=[])                # pencere BOŞ
    monkeypatch.setattr(alpaca, "order_by_id",
                        lambda oid: _kapatma_emri(price=101.0) if oid == "close-ord-1" else None)
    meta = {"armed": [],
            loop.EXIT_FILL_KEY: {"P-2026-08-11-NUE": {"ticker": "NUE", "kaynak": "karar",
                                                      "order_id": "close-ord-1",
                                                      "since": "2026-08-11", "tries": 0}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-NUE"][-1]
    assert satir.get("alpaca_fill_price") == 101.0
    # %1 sapma > MIRROR_DRIFT_TOL (%0.5) → `icra` sınıflı alarm AYNEN öter (eşik değişmedi)
    assert out["drift"] and out["drift"][0]["drift_sinifi"] == "icra"
    assert any(e.get("drift_sinifi") == "icra" for e in _events("MIRROR_DRIFT"))


def test_B1_kimliksiz_kapatma_vazgecis_beyanla_kapanir(ayna, monkeypatch):
    """DELETE cevabı kimlik taşımadıysa fiyat UYDURULMAZ: `EXIT_FILL_MAX_TRIES` tur sonunda
    vazgeçiş OLAYLI ve satıra `alpaca_fill_beyan` düşer — `alpaca_fill_price` anahtarı AÇILMAZ
    (geç gelen gerçek dolum hâlâ yamanabilir)."""
    _trade_satiri()
    _wire(monkeypatch, orders=[], positions=[])
    monkeypatch.setattr(alpaca, "order_by_id", lambda oid: None)
    meta = {"armed": [],
            loop.EXIT_FILL_KEY: {"P-2026-08-11-NUE": {"ticker": "NUE", "kaynak": "karar",
                                                      "order_id": None,
                                                      "order_id_neden": "DELETE cevap gövdesi okunamadı: ValueError",
                                                      "since": "2026-08-11", "tries": 0}}}
    for i in range(loop.EXIT_FILL_MAX_TRIES):
        loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    assert meta[loop.EXIT_FILL_KEY] == {}, "vazgeçilen kayıt kuyruktan düşmedi"
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-NUE"][-1]
    assert "alpaca_fill_price" not in satir, "vazgeçiş fiyat anahtarı açtı — geç dolum kilitlenir"
    assert "ÖLÇÜLEMEDİ" in str(satir.get("alpaca_fill_beyan")), "satıra dürüst beyan yazılmadı"
    ev = _events("mirror_exit_fill_vazgecildi")
    assert ev and ev[-1].get("tries") == loop.EXIT_FILL_MAX_TRIES
    assert len(str(ev[-1].get("neden") or "")) >= 20, "vazgeçiş nedeni yazılmamış (YASA-4)"


# =================================================================================================
# B2 · TEK-ATIŞ YAMASI — kalıcı kuyruk, arıza turu kaybettirmez, geç dolum yakalanır
# =================================================================================================
def test_B2_kapanis_turu_arizasi_yamayi_KAYBETTIRMEZ(ayna, monkeypatch):
    """ESKİ KUSURUN ÇEKİRDEĞİ: kapanış turunda emir listesi arızalı → eski kod `return out` ile
    yamayı SONSUZA DEK kaybederdi. Artık kapanan işlem kuyruğa arıza dallarından ÖNCE yazılır;
    ertesi tur (API sağlıklı) bacak dolumunu satıra yamalar."""
    row = _trade_satiri(pid="P-2026-08-11-AMD", sym="AMD", exit_=150.0, reason="stop")
    # TUR 1: emir listesi ARIZALI (transport down) — reconcile erken döner
    monkeypatch.setattr(alpaca, "orders", lambda **k: [])
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": False, "error": "boom"})
    meta = {"armed": []}
    out1 = loop.reconcile_broker_state(meta, "2026-08-11", [dict(row)],
                                       open_positions={}, fill_eq_now=100000.0)
    assert out1["checked"] is False, "arıza turu 'checked' sayıldı — test kurgusu yanlış"
    assert "P-2026-08-11-AMD" in meta.get(loop.EXIT_FILL_KEY, {}), \
        "arıza turunda kapanan işlem kuyruğa yazılmadı — tek-atış kusuru duruyor"
    # TUR 2: API sağlıklı, parent'ın stop bacağı dolmuş
    parent = _giris_parent("AMD", 25, pid="P-2026-08-11-AMD",
                           legs=[{"id": "leg-sl", "symbol": "AMD", "side": "sell", "type": "stop",
                                  "status": "filled", "qty": "25", "filled_qty": "25",
                                  "filled_avg_price": "149.2"}])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    _wire(monkeypatch, orders=[parent], positions=[])
    out2 = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-AMD"][-1]
    assert satir.get("alpaca_fill_price") == 149.2, "ertesi tur yeniden denemedi (B2 özü)"
    assert out2["exit_fill"]["yamalanan"] == 1 and meta[loop.EXIT_FILL_KEY] == {}


def test_B2_farkli_gunde_dolan_bacak_sonraki_turda_yakalanir(ayna, monkeypatch):
    """İç bar stop'a değdi (iç kapanış bugün), gerçek piyasa bacağı YARIN doluyor — tur 1'de
    dolum yok (tries=1, kuyruk taşır), tur 2'de bacak dolmuş → yama yazılır."""
    row = _trade_satiri(pid="P-2026-08-11-AMD", sym="AMD", exit_=150.0, reason="stop")
    bos_parent = _giris_parent("AMD", 25, pid="P-2026-08-11-AMD",
                               legs=[{"id": "leg-sl", "symbol": "AMD", "side": "sell",
                                      "type": "stop", "status": "held", "qty": "25",
                                      "filled_qty": "0"}])
    _wire(monkeypatch, orders=[bos_parent], positions=[{"symbol": "AMD", "qty": "25"}])
    meta = {"armed": []}
    loop.reconcile_broker_state(meta, "2026-08-11", [dict(row)],
                                open_positions={}, fill_eq_now=100000.0)
    kayit = meta[loop.EXIT_FILL_KEY]["P-2026-08-11-AMD"]
    assert kayit["tries"] == 1 and kayit["kaynak"] == "bacak"
    assert "son_neden" in kayit and len(kayit["son_neden"]) >= 10
    dolu_parent = copy.deepcopy(bos_parent)
    dolu_parent["legs"][0].update({"status": "filled", "filled_qty": "25",
                                   "filled_avg_price": "149.9"})
    _wire(monkeypatch, orders=[dolu_parent], positions=[])
    loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-AMD"][-1]
    assert satir.get("alpaca_fill_price") == 149.9 and meta[loop.EXIT_FILL_KEY] == {}


def test_B2_gec_gelen_gercek_dolum_beyani_SILER(ayna, monkeypatch):
    """Vazgeçiş beyanı bir MEZAR TAŞI değil: sonradan gerçek dolum gelirse (geç `karar` kaydı)
    fiyat yazılır ve beyan satırdan kalkar — ölçüm beyanı her zaman yener."""
    _trade_satiri()
    _wire(monkeypatch, orders=[], positions=[])
    monkeypatch.setattr(alpaca, "order_by_id", lambda oid: None)
    meta = {"armed": [],
            loop.EXIT_FILL_KEY: {"P-2026-08-11-NUE": {"ticker": "NUE", "kaynak": "karar",
                                                      "order_id": None, "since": "2026-08-11",
                                                      "tries": loop.EXIT_FILL_MAX_TRIES - 1}}}
    loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-NUE"][-1]
    assert satir.get("alpaca_fill_beyan"), "kurgu: önce vazgeçiş beyanı düşmeli"
    # geç başarı: kapatma emri kimliği sonradan öğrenildi (ör. elle teşhis / geç kapanış)
    loop._exit_fill_kaydet(meta, "P-2026-08-11-NUE", "NUE", kaynak="karar", dstr=D,
                           order_id="close-ord-1")
    monkeypatch.setattr(alpaca, "order_by_id", lambda oid: _kapatma_emri(price=99.7))
    loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    satir2 = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-2026-08-11-NUE"][-1]
    assert satir2.get("alpaca_fill_price") == 99.7
    assert "alpaca_fill_beyan" not in satir2, "ölçüm geldi ama beyan mezar taşı gibi kaldı"


def test_B2_ayna_kapatmasi_hala_kuyruktaysa_bacak_kaydi_ACILMAZ(ayna, monkeypatch):
    """Karar-çıkışında ayna kapatması HENÜZ başarısızsa (MIRROR_EXIT_KEY'de bekliyor) ölçülecek
    dolum yoktur — `bacak` kaydı açmak 5 turda erken vazgeçiş üretirdi. Kapatma başarınca
    `karar` kaydı kimlikle düşer (üstteki testler); o zamana dek kuyruk temiz kalır."""
    row = _trade_satiri()
    _wire(monkeypatch, orders=[], positions=[])
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: {"NUE": {"plan_id": "P-2026-08-11-NUE",
                                                        "reason": "time_stop", "tries": 2}}}
    loop.reconcile_broker_state(meta, D, [dict(row)], open_positions={}, fill_eq_now=100000.0)
    assert meta.get(loop.EXIT_FILL_KEY, {}) == {}, \
        "ayna kapanmamışken bacak kaydı açıldı — erken vazgeçiş yolu"


def test_B2_koruma_dolumu_satiri_yeniden_KUYRUKLANMAZ(ayna, monkeypatch):
    """POZİTİF KONTROL: B3 yolu satırı kapanış anında GERÇEK dolumla yazar (`alpaca_fill_price`
    dolu) — o kapanış kuyruğa alınmaz (çifte yama/сahte bekleyen yok)."""
    row = {"plan_id": "P-K", "ticker": "NUE", "exit": 141.0, "exit_reason": "koruma_stop",
           "ts_close": "2026-08-11", "alpaca_fill_price": 141.0}
    _wire(monkeypatch, orders=[], positions=[])
    meta = {"armed": []}
    loop.reconcile_broker_state(meta, D, [dict(row)], open_positions={}, fill_eq_now=100000.0)
    assert meta.get(loop.EXIT_FILL_KEY, {}) == {}


def test_B2_kuyruk_restarti_atlatir(ayna):
    """Kuyruk `_save_broker`ın sahiplenilen anahtarıdır — restart kaybı tek-atış kusurunu
    (B2) restart kılığında geri getirirdi."""
    from meridian.broker import PaperBroker
    b = PaperBroker(100_000.0, 5, 0.0)
    meta = {"armed": [], loop.EXIT_FILL_KEY: {"P-X": {"ticker": "NUE", "kaynak": "bacak",
                                                      "since": "2026-08-11", "tries": 1}}}
    loop._save_broker(b, meta)
    _, meta2 = loop._load_broker()
    assert meta2.get(loop.EXIT_FILL_KEY, {}).get("P-X", {}).get("tries") == 1, \
        "kuyruk diske yazılmadı / geri yüklenmedi"


# =================================================================================================
# B5 · KISMİ DOLUM — E2 satırı donmaz + adet sapmasında sınıf
# =================================================================================================
def _e2_ayna_satiri(pid="P-2026-08-11-NUE", sym="NUE", date="2026-08-11"):
    with store.file_lock(loop.ENTRY_LEDGER):
        store.append_jsonl(loop.ENTRY_LEDGER, {
            "ts": "2026-08-11T20:00:00+00:00", "date": date, "plan_id": pid, "ticker": sym,
            "motor": "ayna", "karar": "submitted", "entry_trigger": 100.0, "limit": 100.4,
            "qty": 25, "fill": None, "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None})


def test_B5a_kismi_dolum_satiri_DONMAZ_terminale_dek_tazelenir(ayna, monkeypatch):
    """ÇEKİRDEK: tur 1 kısmi dolum (10/25 @100.1) → satır yazılır ama DONMAZ; tur 2 tam dolum
    (25/25 @100.3) → satır GÜNCELLENİR ve terminal statüyle donar; tur 3 aynı emir → yeniden
    yazım YOK (idempotens geri gelir)."""
    _e2_ayna_satiri()
    kismi = _giris_parent("NUE", 25, status="partially_filled", fq=10, avg=100.1)
    _wire(monkeypatch, orders=[kismi], positions=[])
    meta = {"armed": []}
    out1 = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    r1 = [r for r in store.read_jsonl(loop.ENTRY_LEDGER) if r.get("motor") == "ayna"][-1]
    assert (r1["fill"], r1["fill_qty"], r1["fill_status"]) == (100.1, "10", "partially_filled")
    assert out1["entry_slippage"]["yazilan"] == 1

    tam = _giris_parent("NUE", 25, status="filled", fq=25, avg=100.3)
    _wire(monkeypatch, orders=[tam], positions=[])
    out2 = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    r2 = [r for r in store.read_jsonl(loop.ENTRY_LEDGER) if r.get("motor") == "ayna"][-1]
    assert (r2["fill"], r2["fill_qty"], r2["fill_status"]) == (100.3, "25", "filled"), \
        "kısmi satır ilk fotoğrafta dondu — geç dolum görünmez (B5a özü)"
    assert out2["entry_slippage"]["kismi_tazelenen"] == 1

    out3 = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    assert out3["entry_slippage"]["yazilan"] == 0 and out3["entry_slippage"]["kismi_tazelenen"] == 0, \
        "terminal satır yeniden yazılıyor — idempotens bozuldu"


def test_B5a_kismi_sonra_iptal_SON_durumla_donar(ayna, monkeypatch):
    """Kısmi-dolmuş emir sonradan süpürülmüş/iptal (`canceled` + filled_qty>0): dolum GERÇEK —
    ortalama fiyat son kez yazılır, satır gerçek statüsüyle donar (sonsuz retry yok)."""
    _e2_ayna_satiri()
    kismi = _giris_parent("NUE", 25, status="partially_filled", fq=10, avg=100.1)
    _wire(monkeypatch, orders=[kismi], positions=[])
    meta = {"armed": []}
    loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    olu = _giris_parent("NUE", 25, status="canceled", fq=10, avg=100.1)
    _wire(monkeypatch, orders=[olu], positions=[])
    loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    r = [r for r in store.read_jsonl(loop.ENTRY_LEDGER) if r.get("motor") == "ayna"][-1]
    assert r["fill_status"] == "canceled" and r["fill"] == 100.1, \
        "kısmi-sonra-iptal satırı son durumuyla donmadı"


def test_B5b_adet_sapmasi_kismi_dolum_sinifiyla_adlanir(ayna, monkeypatch):
    """İçeride 25, aynada 10 (>%25 sapma) ve parent emir 10/25 dolmuş → sınıf makbuz kıyası DEĞİL
    emrin kendi kanıtı: `kismi_dolum`. Makbuz VARKEN bile kısmi kanıt ÖNCE gelir (pozitif
    kontrol: makbuz kıyası boyutlama_tabani derdi — 08-05 tuzağının tersi)."""
    kismi = _giris_parent("NUE", 25, status="partially_filled", fq=10, avg=100.1)
    _wire(monkeypatch, orders=[kismi], positions=[{"symbol": "NUE", "qty": "10"}])
    meta = {"armed": [], "peak_equity": 100000.0,
            "size_law": {"P-2026-08-11-NUE": {"eq_kaynak": "eq_now", "eq_now": 94457.91,
                                              "peak": 100000.0, "size_mult": 0.4916,
                                              "kitap_rev": 5}}}
    out = loop.reconcile_broker_state(
        meta, D, [],
        open_positions={"NUE": {"qty": 25.0, "scaled_out": False,
                                "plan_id": "P-2026-08-11-NUE", "ts_open": D}},
        fill_eq_now=100000.0)
    qd = out["positions"]["qty_drift"]
    assert len(qd) == 1 and qd[0]["drift_sinifi"] == "kismi_dolum", f"sınıf: {qd}"
    ev = [e for e in _events("MIRROR_DRIFT") if e.get("ticker") == "NUE"]
    assert ev and ev[-1].get("drift_sinifi") == "kismi_dolum"
    assert "10" in str(ev[-1].get("drift_neden")) and "25" in str(ev[-1].get("drift_neden")), \
        "neden dolan/istenen adetleri adlandırmıyor"


def test_B5b_tam_dolmus_emir_kismi_sinifina_DUSMEZ(ayna, monkeypatch):
    """POZİTİF KONTROL (08-06 dört-pozisyon dersi): emir TAM dolmuşsa kısmi tespiti None döner ve
    hüküm SB-2 tablosuna kalır — kismi_dolum her adet sapmasını yutan bir joker değildir."""
    assert loop._kismi_dolum_tespiti(_giris_parent("NUE", 25, status="filled", fq=25)) is None
    assert loop._kismi_dolum_tespiti(None) is None
    k = loop._kismi_dolum_tespiti(_giris_parent("NUE", 25, status="partially_filled", fq=10))
    assert k is not None and k[0] == "kismi_dolum"


# =================================================================================================
# B6 · FILL_EQ_NOW ANAKRONİZMİ — yaşlı pozisyonda bugünün tabanıyla kıyas YOK
# =================================================================================================
def test_B6_yasli_pozisyon_bugunun_eq_siyle_kiyas_YAPILMAZ(sandbox_state):
    """Makbuzda `dolum_eq` yok VE pozisyon bu seansta dolmadı → sınıf dürüst `olculemedi` +
    anakronizm nedeni (eski davranış: bugünün eq'siyle `boyutlama_tabani` UYDURURDU)."""
    makbuz = {"eq_kaynak": "eq_now", "eq_now": 94457.91, "peak": 100000.0,
              "size_mult": 0.4916, "kitap_rev": 5}
    sinif, neden = loop._drift_sinifi_adet(makbuz, fill_eq_now=100000.0, fill_peak=100000.0,
                                           dolum_taze=False)
    assert sinif == "olculemedi", f"yaşlı pozisyonda kıyas yapıldı: {sinif} — {neden}"
    assert "anakronizm" in neden and "dolum_eq" in neden
    # ts_open okunamadıysa da kıyas yok — bilinmeyen yaş, taze varsayılamaz
    sinif2, neden2 = loop._drift_sinifi_adet(makbuz, fill_eq_now=100000.0, fill_peak=100000.0,
                                             dolum_taze=None)
    assert sinif2 == "olculemedi" and "ts_open" in neden2


def test_B6_dolum_eq_damgasi_yasli_pozisyonda_kiyasi_MESRULASTIRIR(sandbox_state):
    """Makbuz `dolum_eq` damgası taşıyorsa kıyas dolum GÜNÜNÜN tabanıyla yapılır — bugünün eq'si
    (55555, kasıtlı saçma) HİÇ kullanılmaz; neden damgadaki tabanı (100000) adlandırır."""
    makbuz = {"eq_kaynak": "eq_now", "eq_now": 94457.91, "peak": 100000.0, "size_mult": 0.4916,
              "kitap_rev": 5, "dolum_eq": 100000.0, "dolum_peak": 100000.0}
    sinif, neden = loop._drift_sinifi_adet(makbuz, fill_eq_now=55555.0, fill_peak=100000.0,
                                           dolum_taze=False)
    assert sinif == "boyutlama_tabani", f"{sinif} — {neden}"
    assert "100000" in neden and "55555" not in neden, \
        "kıyas bugünün eq'sine kaçtı — anakronizm damgaya rağmen sürüyor"


def test_B6_e2e_yasli_pozisyonda_alarm_yine_oter_sinif_dürüst(ayna, monkeypatch):
    """EŞİK DEĞİŞMEDİ: yaşlı pozisyonda (>%25 sapma) alarm YİNE öter; yalnız sınıf artık uydurma
    `boyutlama_tabani` değil `olculemedi`+anakronizm nedenidir."""
    _wire(monkeypatch, orders=[], positions=[{"symbol": "NUE", "qty": "25"}])
    meta = {"armed": [], "peak_equity": 100000.0,
            "size_law": {"P-2026-08-05-NUE": {"eq_kaynak": "eq_now", "eq_now": 94457.91,
                                              "peak": 100000.0, "size_mult": 0.4916,
                                              "kitap_rev": 5}}}
    out = loop.reconcile_broker_state(
        meta, D, [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-2026-08-05-NUE",
                                "ts_open": "2026-08-05"}},          # 7 gün önce doldu
        fill_eq_now=100000.0)
    qd = out["positions"]["qty_drift"]
    assert len(qd) == 1, "alarm ötmedi — eşik davranışı değişti"
    assert qd[0]["drift_sinifi"] == "olculemedi"
    ev = [e for e in _events("MIRROR_DRIFT") if e.get("ticker") == "NUE"]
    assert ev and "anakronizm" in str(ev[-1].get("drift_neden")), \
        "neden anakronizmi adlandırmıyor — sebep yine uyduruluyor olabilir"


def test_B6_ic_dolum_makbuza_dolum_eq_DAMGALAR(sandbox_state):
    """KABLO KANITI (test_Y2 deseni): `daily_cycle` iç dolum anında makbuza `dolum_eq`/`dolum_peak`
    basıyor — sınıflandırıcının okuduğu damga canlı yolda gerçekten üretiliyor (ölü doğmadı)."""
    src = inspect.getsource(loop.daily_cycle)
    assert '"dolum_eq"' in src and '"dolum_peak"' in src, "iç dolum makbuza damga basmıyor"
    assert src.index("fill_entry") < src.index('"dolum_eq"'), \
        "damga dolumdan önce basılıyor — dolum-anı tabanı değil"


# =================================================================================================
# B7 · PENCERE BOŞLUKLARI — sayfalama + atlanan gün olayları
# =================================================================================================
def _sayfa_ureten(pages):
    """orders stub'ı: her çağrıda çağrı parametrelerini kaydeder, sirayla sayfa döndürür."""
    calls = []

    def _orders(**k):
        calls.append(dict(k))
        i = min(len(calls) - 1, len(pages) - 1)
        return [copy.deepcopy(o) for o in pages[i]]
    return _orders, calls


def test_B7a_pencere_hedefe_dek_GERIYE_sayfalanir(ayna, monkeypatch):
    """Tur hedefi eski bir bekleyen (2026-08-01) → ilk 200'lük sayfa yetmez, `until` imleciyle
    ikinci sayfa çekilir; eski parent pencereye girer ve pencere `kapsandi=True` beyan eder."""
    yeni_sayfa = [_giris_parent(f"S{i:03d}", 10, pid=f"P-YENI-{i}",
                                submitted="2026-08-11T13:30:00Z") for i in range(200)]
    eski_sayfa = [_giris_parent("OLD", 10, pid="P-2026-07-30-OLD",
                                submitted="2026-07-30T13:30:00Z")]
    stub, calls = _sayfa_ureten([yeni_sayfa, eski_sayfa])
    monkeypatch.setattr(alpaca, "orders", stub)
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    meta = {"armed": [], loop.EXIT_FILL_KEY: {"P-ESKI": {"ticker": "OLD", "kaynak": "bacak",
                                                         "since": "2026-08-01", "tries": 1}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    p = out["emir_penceresi"]
    assert p["sayfa"] == 2 and p["kapsandi"] is True and p["hedef"] == "2026-08-01"
    assert calls[1].get("until") == "2026-08-11T13:30:00Z", \
        f"ikinci sayfa until imleci taşımıyor: {calls[1]}"
    assert p["n_emir"] == 201
    rc = store.read_json("broker_reconcile.json", {})
    assert rc.get("emir_penceresi", {}).get("kapsandi") is True, "pencere beyanı panoya inmedi"


def test_B7a_hedef_yokken_tek_sayfa_eski_davranis(ayna, monkeypatch):
    """POZİTİF KONTROL: dolum bekleyen yokken tek sayfa çekilir (bugünkü maliyet korunur)."""
    stub, calls = _sayfa_ureten([[_giris_parent("NUE", 25)] * 1])
    monkeypatch.setattr(alpaca, "orders", stub)
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    loop.reconcile_broker_state({"armed": []}, D, [], open_positions={}, fill_eq_now=100000.0)
    assert len(calls) == 1 and "until" not in {k for c in calls for k in c if c.get(k)}, \
        f"bekleyen yokken sayfalandı: {calls}"


def test_B7a_sayfa_tavani_asilirsa_BEYANLI(ayna, monkeypatch):
    """Hedef pencereye sığmıyor (her sayfa 200 dolu, tarih hedefe inmiyor) → tavanda durulur,
    `kapsandi=False` + neden + `reconcile_emir_penceresi_asilamadi` olayı (pencere-dışı satır
    'dolmadı' diye OKUNMAZ — hüküm yok beyanı)."""
    sayfa = [_giris_parent(f"S{i:03d}", 10, pid=f"P-S-{i}",
                           submitted="2026-08-10T13:30:00Z") for i in range(200)]
    stub, calls = _sayfa_ureten([sayfa])          # her çağrı aynı 200'lük sayfa (tarih inmiyor)
    monkeypatch.setattr(alpaca, "orders", stub)
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    meta = {"armed": [], loop.EXIT_FILL_KEY: {"P-ESKI": {"ticker": "OLD", "kaynak": "bacak",
                                                         "since": "2026-08-01", "tries": 1}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    p = out["emir_penceresi"]
    assert p["kapsandi"] is False and "tavan" in str(p["neden"])
    assert len(calls) == loop._EMIR_PENCERESI_SAYFA_TAVANI
    ev = _events("reconcile_emir_penceresi_asilamadi")
    assert ev and ev[-1].get("hedef") == "2026-08-01", "pencere aşımı olaysız — sessiz boşluk"


def test_B7a_e2_ufku_kacan_girisi_hedefe_ALMAZ(ayna, monkeypatch):
    """ALARM HİJYENİ: E2'de 30 gün önce dolMAMIŞ kalmış satır (meşru 'kaçan giriş') pencere
    hedefini sonsuza dek geriye çekmez — ufuk (14 gün) dışı satır 'dolmadı' sınıfının kendisidir.
    Aksi her tur sahte 'kapsanamadı' olayı basardı."""
    _e2_ayna_satiri(pid="P-2026-07-10-ESKI", sym="ESKI", date="2026-07-10")
    hedef = loop._emir_penceresi_hedefi({"armed": []}, D)
    assert hedef is None, f"ufuk dışı E2 satırı hedefe girdi: {hedef}"
    _e2_ayna_satiri(pid="P-2026-08-11-YENI", sym="YENI", date="2026-08-11")
    assert loop._emir_penceresi_hedefi({"armed": []}, D) == "2026-08-11"


def test_B7b_atlanan_gun_siniflari_OLAYLANIR_gunde_bir(ayna):
    """`noop` dalı olaylanır (gün+sınıf başına BİR kez — poll başına değil); farklı sınıf ayrı
    olay. POZİTİF KONTROL: iç-broker modunda ayna yok → olay yok."""
    loop._RECONCILE_ATLANDI_LOGGED.clear()
    loop._reconcile_gunu_atlandi("noop", D)
    loop._reconcile_gunu_atlandi("noop", D)                       # dedup
    loop._reconcile_gunu_atlandi("waiting_for_universe", D)
    evs = _events("reconcile_atlandi")
    assert len(evs) == 2, f"gün+sınıf tekilleştirmesi bozuk: {len(evs)} olay"
    assert {e.get("sinif") for e in evs} == {"noop", "waiting_for_universe"}
    n0 = len(_events("reconcile_atlandi"))
    eski = config.BROKER
    try:
        config.BROKER = "internal"
        loop._RECONCILE_ATLANDI_LOGGED.clear()
        loop._reconcile_gunu_atlandi("noop", D)
    finally:
        config.BROKER = eski
    assert len(_events("reconcile_atlandi")) == n0, "ayna yokken de olay basıldı (sahte borç)"


def test_B7b_uc_dal_da_kablolu():
    """KABLO KANITI: üç erken-dönüş dalı da (`noop` / `waiting_for_universe` /
    `refused_regressive`) yardımcıyı çağırıyor — olay mekanizması ölü doğmadı."""
    src = inspect.getsource(loop.daily_cycle)
    for sinif in ("noop", "waiting_for_universe", "refused_regressive"):
        assert f'_reconcile_gunu_atlandi("{sinif}"' in src, f"dal kablosuz: {sinif}"


# =================================================================================================
# B8 · MOTOR YETİMİ ÜÇ SINIF — görünürlük, davranış/kilit aynı
# =================================================================================================
def _yetim_kurulum(monkeypatch, syms=("AAA", "BBB", "CCC")):
    """Üç sembol de aynada dolmuş motor emriyle açık, iç kitapta yok — eski kod üçünü de tek adla
    (`motor_yetimi`) alarmlıyordu."""
    orders = [_giris_parent(s, 10, pid=f"P-2026-08-11-{s}") for s in syms]
    poss = [{"symbol": s, "qty": "10"} for s in syms]
    _wire(monkeypatch, orders=orders, positions=poss)


def test_B8_uc_yetim_sinifi_ayri_adlarla_alarmlanir(ayna, monkeypatch):
    """AAA silahlı kümede (taşınan plan) → `tasima_gecikmesi`; BBB çıkış dolum-yaması kuyruğunda
    (iç kapalı, bacak bekleniyor) → `cikis_gecikmesi`; CCC hiçbiri → `giris_yetimi`.
    `engine_orphans` LİSTESİ DEĞİŞMEZ (pano sayacı + `_mirror_busy` kilidi eski davranış)."""
    _yetim_kurulum(monkeypatch)
    meta = {"armed": [{"id": "P-2026-08-11-AAA", "ticker": "AAA"}],
            loop.EXIT_FILL_KEY: {"P-2026-08-11-BBB": {"ticker": "BBB", "kaynak": "bacak",
                                                      "since": "2026-08-11", "tries": 1}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    assert out["positions"]["engine_orphans"] == ["AAA", "BBB", "CCC"], \
        "liste üyeliği değişti — _mirror_busy/pano okuyucusu kırılır"
    sinifli = {r["ticker"]: r["sinif"] for r in out["positions"]["engine_orphans_sinifli"]}
    assert sinifli == {"AAA": "tasima_gecikmesi", "BBB": "cikis_gecikmesi",
                      "CCC": "giris_yetimi"}, f"sınıflar yanlış: {sinifli}"
    ev = _events("MIRROR_DRIFT")
    for sym, sinif in sinifli.items():
        assert any(e.get("ticker") == sym and e.get("drift_sinifi") == sinif for e in ev), \
            f"{sym} alarmı {sinif} sınıfını taşımıyor"
    assert not any(e.get("drift_sinifi") == "motor_yetimi" for e in ev), \
        "eski jenerik ad hâlâ basılıyor — üç olgu yine tek isimde"
    for r in out["positions"]["engine_orphans_sinifli"]:
        assert len(r["neden"]) >= 20, f"sınıf nedeni yazılmamış: {r}"


def test_B8_yakin_kapanis_trades_izinden_cikis_gecikmesi(ayna, monkeypatch):
    """Kuyrukta olmasa da trades.jsonl'da YAKIN (≤7 gün) kapanış izi olan yetim `cikis_gecikmesi`
    sayılır; ESKİ (>7 gün) kapanış izi sayılmaz → `giris_yetimi` (pozitif kontrol)."""
    _trade_satiri(pid="P-1-AAA", sym="AAA", reason="stop", ts_close="2026-08-08")   # 4 gün önce
    _trade_satiri(pid="P-1-CCC", sym="CCC", reason="stop", ts_close="2026-07-20")   # 23 gün önce
    _yetim_kurulum(monkeypatch, syms=("AAA", "CCC"))
    out = loop.reconcile_broker_state({"armed": []}, D, [], open_positions={},
                                      fill_eq_now=100000.0)
    sinifli = {r["ticker"]: r["sinif"] for r in out["positions"]["engine_orphans_sinifli"]}
    assert sinifli == {"AAA": "cikis_gecikmesi", "CCC": "giris_yetimi"}, f"{sinifli}"


def test_B8_cikis_yetimi_ayri_kalir(ayna, monkeypatch):
    """C9 ayrımı KORUNUR: `MIRROR_EXIT_KEY` kuyruğundaki sembol `exit_orphans`/`cikis_yetimi`
    olarak kalır — B8 sınıflaması onu yutmaz (iki mekanizma ayrı teşhis)."""
    _yetim_kurulum(monkeypatch, syms=("DDD",))
    meta = {"armed": [], loop.MIRROR_EXIT_KEY: {"DDD": {"plan_id": "P-2026-08-11-DDD",
                                                        "reason": "time_stop", "tries": 2}}}
    out = loop.reconcile_broker_state(meta, D, [], open_positions={}, fill_eq_now=100000.0)
    assert out["positions"]["exit_orphans"] == ["DDD"]
    assert out["positions"]["engine_orphans"] == [] and \
        out["positions"]["engine_orphans_sinifli"] == []
    assert any(e.get("drift_sinifi") == "cikis_yetimi" for e in _events("MIRROR_DRIFT"))


# =================================================================================================
# Y · YASA-6 / GÖRÜNÜRLÜK KABLOLARI
# =================================================================================================
def test_Y_reconcile_artefakti_uc_yeni_yuzeyi_tasir(ayna, monkeypatch):
    """`broker_reconcile.json` artık `entry_slippage` (teşhis §3'ün TEK okuyucusuz-yazım bulgusu),
    `exit_fill` ve `emir_penceresi` anahtarlarını taşır — okuyucu /api/alpaca `reconcile`
    passthrough'u (rc'nin tamamını yayar) + pano mutabakat masası."""
    _wire(monkeypatch, orders=[], positions=[])
    loop.reconcile_broker_state({"armed": []}, D, [], open_positions={}, fill_eq_now=100000.0)
    rc = store.read_json("broker_reconcile.json", {})
    assert rc.get("entry_slippage") == {"eslesen": 0, "yazilan": 0, "acilis_yok": 0,
                                        "kismi_tazelenen": 0}
    assert rc.get("exit_fill") == {"bekleyen": 0, "yamalanan": 0, "vazgecilen": 0}
    assert rc.get("emir_penceresi", {}).get("kapsandi") is True
    assert "engine_orphans_sinifli" in rc.get("positions", {})


def test_Y_emir_gonderim_yolu_ACILMADI():
    """SINIR ÇİZGİSİ KANITI: bu turun yeni kod yolları (kuyruk + pencere + sınıflar) hiçbir emir
    ucu ÇAĞIRMAZ — ölçüm/görünürlük turu, icra yok. (submit/cancel/DELETE yalnız eski yollarda.)"""
    for fn in (loop._exit_fill_yamasi, loop._alpaca_emir_penceresi, loop._emir_penceresi_hedefi,
               loop._exit_fill_kaydet, loop._kismi_dolum_tespiti, loop._reconcile_gunu_atlandi):
        src = inspect.getsource(fn)
        for yasak in ("submit_bracket", "submit_plan", "submit_protective_oco", "cancel_order",
                      ".delete(", ".post("):
            assert yasak not in src, f"{fn.__name__} emir ucuna dokunuyor: {yasak}"
    # order_by_id SALT-OKUMA: GET dışında fiil yok
    src = inspect.getsource(alpaca.order_by_id)
    assert "httpx.get" in src and ".post(" not in src and ".delete(" not in src
