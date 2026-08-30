"""test_pencere_kaydirma_v272.py — EXE-2026-009 (B-PENCERE-KAYDIR, K2) çivileri.

Kart: research/cards/EXE-2026-009-pencere-kaydirma.yaml (DONUK) · karar: docs/KARAR-2026-08-23-
YEDI-KARAR.md K2. Çivilenen sözleşme:
  (1) TETİK SABİTİ tek kaynak: `barclock.ENTRY_WINDOW_ET_MIN = 9*60+45` (EDT'de 13:45 UTC) ve
      damga rejimi (`pencere_rejimi`) AYNI sabitten türetilir — ikiz-değer yok (EQUIVALENT_TRUTHS
      sınıfı tuzağı). Bilinmeyen sabit değeri rejim adı UYDURMAZ (KeyError).
  (2) DAMGA — SÖZLEŞME 2026-08-29'da TERS ÇEVRİLDİ (EXE-009 P-1, operatör hükmü): damga artık
      GÖNDERİM satırında basılır, dolum yaması ona DOKUNMAZ. Gerekçe ve asıl çiviler
      `tests/test_pencere_damgasi_gonderim_ani_v335.py`de; buradaki test o hükme çevrildi
      (tarihçe korunur, satır silinmez). İç motor dolum satırı kaynakta damgayı taşımaya
      DEVAM eder (kaynak-çivisi) — orada gönderim/yazım ayrışması yoktur, aynı turda olur.
  (3) GERİYE DÖNÜK ETİKETLEME YOK (kart kill#3): dolumu ESKİ olan satır damgalanmaz; kısmi
      satırın mevcut damgası tazelemede DEĞİŞMEZ.
  (4) GÖNDERİM PENCERESİ: `mirror_submit_armed` pencere dışında gönderMEZ (erteler — emir
      açılıştan önce dinlenip 13:30 dolumunu geri getirirdi); İŞ-2-EOD kemeri `pencere_muaf`
      ile muaftır (mutabakat > zamanlama).
  (5) SABAH KANCASI: intraday tüketici pencere açılınca bekleyen silahlı planları TEK KAPIDAN
      gönderir; pencere öncesi tarama/karar üretmez (`skipped["pencere"]`).
  (6) ÖNERİ TETİĞİ üç dalı (hakem_kurali BİREBİR): tetiklenmedi / geri_al_onerisi /
      orneklem_birikimde — sentetik verilerle.

`set_clock` module-global → autouse `_saat_sifirla` ZORUNLU (donuk saat sızmasın)."""
import datetime as dt
import re
from pathlib import Path

import pytest

from meridian import barclock as bc, intraday_cycle as ic, loop, store
from tests.conftest import betikten_modul_yukle

UTC = dt.timezone.utc
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _saat_sifirla():
    ic._CONSUMER = None
    yield
    bc.reset_clock()
    ic._CONSUMER = None


def _t(h, m, s=0, gun=23):
    """2026-07-23 Perşembe (EDT — 9:30 ET = 13:30 UTC); mevcut intraday testlerin tarihiyle aynı."""
    return dt.datetime(2026, 7, gun, h, m, s, tzinfo=UTC)


# ---------------------------------------------------------------------------------------------
# (1) TETİK SABİTİ + TEK KAYNAK
# ---------------------------------------------------------------------------------------------
def test_tetik_sabiti_1345_ve_pencere_siniri():
    assert bc.ENTRY_WINDOW_ET_MIN == 9 * 60 + 45          # K2: 13:30 → 13:45 UTC (EDT)
    assert not bc.is_entry_window(_t(13, 30))             # eski çapa artık pencere DIŞI
    assert not bc.is_entry_window(_t(13, 44, 59))
    assert bc.is_entry_window(_t(13, 45))                 # tetik anı
    assert bc.is_entry_window(_t(19, 59))
    assert not bc.is_entry_window(_t(20, 0))              # seans kapanışı (16:00 ET)
    assert not bc.is_entry_window(_t(14, 0, gun=25))      # 2026-07-25 Cumartesi
    # SEANS YASASI AYRI KALIR: RTH tanımı (9:30-16:00) değişmedi — pencere onun ALT kümesi.
    assert bc.is_market_open(_t(13, 35))


def test_rejim_damgasi_tetik_sabitiyle_ayni_kaynaktan(monkeypatch):
    assert bc.pencere_rejimi() == "1345"
    # sabit geri alınırsa damga KENDİLİĞİNDEN "1330" olur — ikinci bir değer/dosya yok
    monkeypatch.setattr(bc, "ENTRY_WINDOW_ET_MIN", 9 * 60 + 30)
    assert bc.pencere_rejimi() == "1330"
    assert bc.is_entry_window(_t(13, 35))                 # pencere de aynı sabitten açıldı
    # bilinmeyen sabit değeri için rejim adı UYDURULMAZ
    monkeypatch.setattr(bc, "ENTRY_WINDOW_ET_MIN", 9 * 60 + 40)
    with pytest.raises(KeyError):
        bc.pencere_rejimi()


# ---------------------------------------------------------------------------------------------
# (2) DAMGA DOLUM YOLUNDA
# ---------------------------------------------------------------------------------------------
def _ayna_satir(**ek):
    return {"date": "2026-07-22", "plan_id": "P1", "ticker": "AAPL", "motor": "ayna",
            "karar": "submitted", "entry_trigger": 100.0, "limit": 101.0,
            "fill": None, "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None, **ek}


def test_ayna_dolum_yamasi_pencere_damgasina_DOKUNMAZ(sandbox_state):
    """2026-08-29 ÖNCESİ bu test tersini çiviliyordu (`assert r["pencere"] == "1345"`, yani yama
    damgayı BASAR). Operatör hükmü sözleşmeyi çevirdi: yazım-anı rejimi gönderim rejimi değildir
    ve araya dağıtım girdiğinde yalan söyler (DE/PANW vakası). Yama artık yalnız dolum alanlarını
    yazar."""
    store.write_jsonl(loop.ENTRY_LEDGER, [_ayna_satir()])
    by_coid = {"P1": {"status": "filled", "filled_avg_price": "101.5", "filled_qty": "10"}}
    loop._patch_entry_slippage(by_coid, {"AAPL": 100.0}, "2026-07-23")
    r = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert r["fill"] == 101.5                              # dolum alanları yazıldı
    assert r.get("pencere") is None                        # damga UYDURULMADI (gönderimde basılır)


def test_geriye_donuk_etiketleme_yok(sandbox_state):
    # (a) dolumu ESKİ (terminal) satır: damgasız girdi, damgasız kalır (kart kill#3)
    eski = _ayna_satir(fill=100.5, fill_status="filled")
    # (b) kısmi satır: 1330 rejiminde damgalanmış; tazeleme damgayı DEĞİŞTİRMEZ
    kismi = _ayna_satir(plan_id="P2", ticker="MSFT", fill=200.0, fill_qty="5",
                        fill_status="partially_filled", pencere="1330")
    store.write_jsonl(loop.ENTRY_LEDGER, [eski, kismi])
    by_coid = {"P1": {"status": "filled", "filled_avg_price": "999.0", "filled_qty": "10"},
               "P2": {"status": "filled", "filled_avg_price": "201.0", "filled_qty": "10"}}
    loop._patch_entry_slippage(by_coid, {"AAPL": 100.0, "MSFT": 199.0}, "2026-07-23")
    rows = store.read_jsonl(loop.ENTRY_LEDGER)
    assert "pencere" not in rows[0]                        # terminal satıra dokunulmadı
    assert rows[0]["fill"] == 100.5
    assert rows[1]["fill"] == 201.0                        # kısmi tazelendi (B5a)
    assert rows[1]["pencere"] == "1330"                    # ama damga yeniden yazılmadı


def test_ic_motor_dolum_satiri_damgayi_kaynaktan_tasir():
    """Kaynak-çivisi: iç motor dolum yolu `daily_cycle` içinde gömülü (birim-kurulumu ağır) —
    E2 `karar: "fill"` yazımının `pencere` alanını barclock TEK kaynağından aldığı kaynak
    metninden doğrulanır (AST-yokluk testleriyle aynı desen, test_streamhealth_parity emsali)."""
    src = (REPO / "meridian" / "loop.py").read_text()
    m = re.search(r'_entry_exec_write\(\{\*\*_base, "karar": "fill".*?\}\)', src, re.S)
    assert m, "iç motor E2 dolum yazımı bulunamadı — çivi güncellenmeli"
    assert '"pencere": barclock.pencere_rejimi()' in m.group(0), \
        "iç motor dolum satırı pencere damgasını barclock tek kaynağından taşımıyor"


# ---------------------------------------------------------------------------------------------
# (4) GÖNDERİM PENCERESİ YASASI
# ---------------------------------------------------------------------------------------------
def _meta():
    return {"armed": [{"id": "P1", "ticker": "AAPL", "entry_trigger": 100.0}],
            "alpaca_submitted": [], "entry_law": {}, "peak_equity": 100_000.0}


def test_pencere_disi_gonderim_ertelenir(sandbox_state, monkeypatch):
    monkeypatch.setattr(loop.config, "BROKER", "alpaca_paper")
    bc.set_clock(lambda: _t(3, 0))                        # gece — emir açılışa dek DİNLENİRDİ
    meta = _meta()
    out = loop.mirror_submit_armed(meta, "2026-07-23", eq_now=100_000.0, halted=False)
    assert out.get("deferred") is True and out["submitted"] == 0
    assert len(meta["armed"]) == 1                        # plan düşürülmedi, silahlı bekliyor
    assert meta["alpaca_submitted"] == []


def test_pencere_ici_gonderim_kapidan_gecer(sandbox_state, monkeypatch):
    from meridian.adapters import alpaca
    monkeypatch.setattr(loop.config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)   # ağsız kanıt: kapıyı GEÇTİ
    bc.set_clock(lambda: _t(14, 0))                       # 10:00 ET — pencere içi
    out = loop.mirror_submit_armed(_meta(), "2026-07-23", eq_now=100_000.0, halted=False)
    assert out.get("deferred") is None                    # pencere yasası bağlamadı
    assert "anahtar" in out["detail"]                     # anahtar-yok dalına ULAŞTI


def test_gec_kemer_pencere_muaf(sandbox_state, monkeypatch):
    from meridian.adapters import alpaca
    monkeypatch.setattr(loop.config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    bc.set_clock(lambda: _t(3, 0))                        # gece — ama kemer mutabakat işi görür
    out = loop.mirror_submit_armed(_meta(), "2026-07-23", eq_now=100_000.0, halted=False,
                                   pencere_muaf=True)
    assert out.get("deferred") is None
    assert "anahtar" in out["detail"]


# ---------------------------------------------------------------------------------------------
# (5) SABAH KANCASI — intraday tüketici
# ---------------------------------------------------------------------------------------------
def _kitap(armed=True, submitted=()):
    return {"positions": {}, "last_date": "2026-07-22",
            "armed": ([{"id": "P1", "ticker": "AAPL", "entry_trigger": 100.0}] if armed else []),
            "alpaca_submitted": list(submitted)}


def test_pencere_oncesi_tarama_yok_ve_gonderim_yok(sandbox_state, monkeypatch):
    monkeypatch.setattr(ic.config, "BROKER", "alpaca_paper")
    calls = []
    monkeypatch.setattr(loop, "mirror_submit_ve_kalicilastir",
                        lambda *a, **k: calls.append(k) or {"ok": True, "submitted": 0})
    bc.set_clock(lambda: _t(13, 40))                      # RTH açık ama pencere ÖNCESİ
    store.write_json("portfolio.json", _kitap())
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [{"t": "2026-07-23T13:38:00Z", "o": 99, "h": 101,
                                        "l": 99, "c": 100.5, "v": 100}])
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert calls == []                                    # gönderim denenmedi
    assert store.read_jsonl(ic.DECISIONS_FILE) == []      # karar/tarama satırı da yok
    assert ic.consumer().skipped["pencere"] == 1


def test_pencere_acilinca_bekleyen_silahli_tek_kapidan_gider(sandbox_state, monkeypatch):
    monkeypatch.setattr(ic.config, "BROKER", "alpaca_paper")
    calls = []

    def _sahte(*a, **k):
        calls.append(k)
        # gerçek tek kapının yaptığı yamayı taklit et: dedup kümesine yaz
        store.update_json("portfolio.json",
                          lambda d: d.__setitem__("alpaca_submitted", ["P1"]) or True, {})
        return {"ok": True, "submitted": 1, "submitted_ids": ["P1"], "dropped_ids": []}

    monkeypatch.setattr(loop, "mirror_submit_ve_kalicilastir", _sahte)
    bc.set_clock(lambda: _t(13, 46))                      # pencere AÇIK
    store.write_json("portfolio.json", _kitap())
    ic.consumer().on_barfeed_event({"syms": ""})          # sembolsüz olay bile kancayı işletir
    assert len(calls) == 1 and calls[0].get("source") == "pencere_gonderim"
    ic.consumer().on_barfeed_event({"syms": ""})          # dedup: ikinci olayda İKİNCİ çağrı yok
    assert len(calls) == 1


def test_kanca_ayna_kapaliyken_dokunmaz(sandbox_state, monkeypatch):
    # BROKER=internal (test varsayılanı): kanca hiçbir şey çağırmaz — gözlem sıfır yetkili kalır
    calls = []
    monkeypatch.setattr(loop, "mirror_submit_ve_kalicilastir",
                        lambda *a, **k: calls.append(k) or {"ok": True, "submitted": 0})
    bc.set_clock(lambda: _t(13, 46))
    store.write_json("portfolio.json", _kitap())
    ic.consumer().on_barfeed_event({"syms": ""})
    assert calls == []


def test_ertelenen_gonderim_sabah_kancasiyla_tamamlanir(sandbox_state, monkeypatch):
    """ENTEGRASYON ÇİVİSİ: akşam ertelenen EOD gönderimi, sabah kancasında GERÇEK tek kapıdan
    (mirror_submit_ve_kalicilastir) tamamlanır — E2 `kaynak=pencere_gonderim` satırı + dedup
    kümesi + kitap yaması. Zincirin iki ucu tek testte: erteleme kanıtı + tamamlanma kanıtı."""
    from meridian.adapters import alpaca
    from meridian import health as _h
    monkeypatch.setattr(ic.config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda pl, eq, size_mult=1.0, atr=None, ref_price=None:
                        {"ok": True, "qty": 5,
                         "law": {"limit": 101.0, "mode": "marketable_limit", "tif": "gtc"}})
    store.write_json("portfolio.json",
                     {"positions": {}, "last_date": "2026-07-22",
                      "armed": [{"id": "P1", "ticker": "AAPL", "entry_trigger": 100.0}],
                      "alpaca_submitted": [], "peak_equity": 100_000.0, "entry_law": {}})
    _h.write_heartbeat(equity=100_000.0, last_bar="2026-07-22")   # kancanın eq kaynağı (nabız)
    bc.set_clock(lambda: _t(2, 0))                    # gece: EOD gönderimi ERTELENİR
    out = loop.mirror_submit_ve_kalicilastir(source="loop")
    assert out.get("deferred") is True
    assert store.read_json("portfolio.json", {})["alpaca_submitted"] == []
    bc.set_clock(lambda: _t(13, 46))                  # pencere açıldı — sembolsüz olay yeter
    ic.consumer().on_barfeed_event({"syms": ""})
    pf = store.read_json("portfolio.json", {})
    assert pf["alpaca_submitted"] == ["P1"]           # tek kapının kalıcı yaması
    ayna = [r for r in store.read_jsonl(loop.ENTRY_LEDGER)
            if r.get("motor") == "ayna" and r.get("karar") == "submitted"]
    assert len(ayna) == 1 and ayna[0]["kaynak"] == "pencere_gonderim"


# ---------------------------------------------------------------------------------------------
# (6) ÖNERİ TETİĞİ — üç dal (hakem_kurali birebir)
# ---------------------------------------------------------------------------------------------
def _altbant():
    yol = REPO / "research" / "olcumler" / "edg042_kosum_2026-08-22" / "pencere_altbant.py"
    return betikten_modul_yukle(yol, "pencere_altbant_test")


def _bant(bps_liste, pencere, gun0=1):
    """Her satır ayrı seansta (kümeli bootstrap'a gerçekçi girdi)."""
    return [{"ticker": f"T{i}", "date": f"2026-07-{gun0 + i:02d}", "motor": "ayna",
             "karar": "submitted", "fill": 100.0, "fill_vs_resmi_acilis_bps": b,
             "pencere": pencere}
            for i, b in enumerate(bps_liste)]


def test_oneri_tetigi_tetiklenmedi():
    m = _altbant()
    rapor = m.altbant_raporu(_bant([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], "1330")
                             + _bant([5, 6, 4, 5, 6, 4, 5, 5, 6, 4, 5, 5], "1345"))
    assert rapor["oneri_tetigi"]["sonuc"] == "tetiklenmedi"
    assert rapor["bantlar"]["1330"]["ci"] is not None      # iki CI da hesaplandı, kesişiyor
    assert rapor["bantlar"]["1345"]["ci"] is not None


def test_oneri_tetigi_geri_al_onerisi():
    m = _altbant()
    rapor = m.altbant_raporu(_bant([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], "1330")
                             + _bant([104, 105, 106, 105, 104, 106, 105, 105, 104, 106, 105, 105],
                                     "1345"))
    assert rapor["oneri_tetigi"]["sonuc"] == "geri_al_onerisi"
    assert "GERİ-AL" in rapor["oneri_tetigi"]["beyan"]      # operatöre düşen öneri metni
    assert "otomatik" in rapor["oneri_tetigi"]["beyan"].lower()   # geri alma OTOMATİK DEĞİL


def test_oneri_tetigi_orneklem_birikimde():
    m = _altbant()
    rapor = m.altbant_raporu(_bant([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], "1330")
                             + _bant([104, 105, 106, 105, 104], "1345"))   # n=5 < 10
    assert rapor["oneri_tetigi"]["sonuc"] == "orneklem_birikimde"
    assert rapor["bantlar"]["1345"]["ci"] is None           # n<10: CI/kıyas YAPILMAZ


def test_damgasiz_eski_satirlar_ayri_sayilir_kiyasa_girmez():
    m = _altbant()
    eski = _bant([50, 60], None)                            # damgasız (kaydırma-öncesi kayıt)
    for r in eski:
        r.pop("pencere")
    rapor = m.altbant_raporu(_bant([4] * 12, "1330") + _bant([5] * 12, "1345") + eski)
    assert rapor["damgasiz"]["n"] == 2                      # geriye dönük etiketlenMEZ, sayılır
    assert rapor["bantlar"]["1330"]["n"] == 12 and rapor["bantlar"]["1345"]["n"] == 12
