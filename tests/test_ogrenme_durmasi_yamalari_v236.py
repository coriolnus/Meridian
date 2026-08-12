"""test_ogrenme_durmasi_yamalari_v236.py — öğrenme-durması turunun ÜÇ yaması (2026-08-12).

P1 — watchdog.monotonicity_report `sermaye_taban`ı artık KANONİK türetimden okur
     (`sermaye.sermaye_taban`, sent-tam): ham-float Σ'nin toplama-sırası tozu bir daha
     yarım-sent alarmı ("5542.09 → 5542.08") üretemez; GERÇEK gerileme yine alarmlar.
P2 — broker birikimi SENT-TAM: `realized_pnl`/`cash`/`banked_pnl` artışları `round(pnl, 2)` —
     `Position.entry_commission` yanındaki sözleşmenin ("realized_pnl == Σ row.pnl_dollars")
     İCRASI. Yarım-sent sürüklenmesi kaynağında kesilir.
P3 — asılı aramanın KENDİ onarımı: (a) SEARCH_PROGRESS yazımları `updated_at` damgalı
     (`hermes._progress` tek kapı; damga sprint bayatlık parmak-izine GİRMEZ), (b) `reflect_once`
     finally güvenlik ağı (bayrak hiçbir çıkışta asılı kalamaz), (c) havuz sonuç-beklemesi
     TOPLAM-ATALET tavanlı (`reflect._havuz_sonuclari`): ilerleyen arama kesilmez, ölü havuz
     `arama_havuzu_zaman_asimi` olayıyla öldürülür ve arama sıralı yolda yaşar.

CANLI STATE'E YAZILMAZ: state'e dokunan her test `sandbox_state` içinde koşar; hiçbir test
gerçek işçi SÜRECİ başlatmaz (havuz testleri thread/sahte-future ile koşar — v136 dersi).
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import threading
import time

import pytest

from meridian import hermes, reflect, sermaye, store, watchdog
from meridian.broker import PaperBroker

from tests.test_ogrenme_katmani_durmasi_v235 import PNLS, TABAN, _kitap_yaz

UTC = dt.timezone.utc
GECE = dt.datetime(2026, 8, 12, 23, 0, tzinfo=UTC)


def _plan(tid="P1", ticker="AAA", trigger=100.0, stop=95.0, target=115.0, size_r=1.0):
    return {"id": tid, "ticker": ticker, "entry_trigger": trigger, "stop": stop,
            "profit_target": target, "size_r": size_r}


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# ==================================================================================================
# P2 — broker: sent-tam birikim (kök onarım)
# ==================================================================================================
def test_p2_cok_kapanisli_realized_esittir_defter_BIT_BIT():
    """SÖZLEŞMENİN İCRASI: sent-altı üreten komisyon/kayma ile 8 ardışık kapanışta
    `realized_pnl == Σ satır.pnl_dollars` BİT-BİT (== , approx değil) — birikim de satır da aynı
    yuvarlanmış artışı taşıdığı için toplamlar aynı sırayla aynı double'ları toplar."""
    b = PaperBroker(equity=100_000, slippage_bps=7, commission_per_share=0.0037)
    seq = [("AAA", 100.0, 95.0, 115.0, 107.31, "target"),
           ("BBB", 50.0, 47.0, 60.0, 46.53, "stop"),
           ("CCC", 200.0, 190.0, 230.0, 208.7, "time_stop"),
           ("DDD", 33.33, 31.11, 41.0, 34.017, "time_stop"),
           ("EEE", 77.77, 74.0, 90.0, 76.123, "time_stop"),
           ("FFF", 12.34, 11.11, 15.0, 12.9876, "target"),
           ("GGG", 250.01, 240.0, 280.0, 251.111, "time_stop"),
           ("HHH", 61.803, 58.0, 70.0, 61.007, "stop")]
    for i, (tk, op, st, tg, ex, why) in enumerate(seq):
        pos = b.fill_entry(_plan(f"P{i}", tk, op, st, tg), next_open=op, ts="2026-01-02",
                           equity=b.equity())
        assert pos is not None, tk
        b.close_position(tk, raw_exit=ex, reason=why, ts="2026-01-10")
    toplam = sum(r["pnl_dollars"] for r in b.closed)
    assert b.realized_pnl == toplam, (b.realized_pnl, toplam)          # BİT-BİT, tolerans yok
    # yarım-sent kalıntısı YOK: realized sent ızgarasının üstünde durur (toz < 1e-6 sent)
    assert abs(b.realized_pnl * 100 - round(b.realized_pnl * 100)) < 1e-6


def test_p2_scale_out_dahil_yarim_sent_suruklenmesi_uremiyor():
    """Kısmi satış (banked) + araya giren başka kapanışlarla SIRA KARIŞIK birikimde bile toplamlar
    SENT-TAM kapanır: banked artışı da yuvarlandığı için satır (`round(rem+banked, 2)`) ile birikim
    (`round(rem,2)+banked`) aynı sent ızgarasına oturur — sürüklenecek kalıntı kalmaz."""
    b = PaperBroker(equity=100_000, slippage_bps=7, commission_per_share=0.0037)
    pa = b.fill_entry(_plan("PA", "AAA", 200.0, 190.0, 230.0), next_open=200.0,
                      ts="2026-01-02", equity=b.equity())
    pb = b.fill_entry(_plan("PB", "BBB", 50.0, 47.0, 60.0), next_open=50.0,
                      ts="2026-01-02", equity=b.equity())
    assert pa is not None and pb is not None
    bar = {"open": 210.0, "high": pa.entry + 2.2 * pa.r_per_share, "low": 208.0, "close": 212.0}
    assert b.scale_out(pa, bar, {"exit.scale_out_frac": 0.4, "exit.scale_out_r": 2.0}) is True
    assert pa.banked_pnl == round(pa.banked_pnl, 2), "banked artışı sent-tam değil"
    b.close_position("BBB", raw_exit=46.53, reason="stop", ts="2026-01-09")   # araya giren kapanış
    b.close_position("AAA", raw_exit=225.117, reason="time_stop", ts="2026-01-10")
    toplam = sum(r["pnl_dollars"] for r in b.closed)
    assert len(b.closed) == 2                                   # kısmi satış EKSTRA satır üretmedi
    assert round(b.realized_pnl * 100) == round(toplam * 100), (b.realized_pnl, toplam)
    assert abs(b.realized_pnl - toplam) < 5e-10                 # fark yalnız double-toplama tozu
    # zımni taban: taze broker için realized − Σ defter TAM SIFIR — dedektörün izlediği büyüklük
    # bu dünyada gerçekten SABİT (yarım-sent sınırına oturacak kalıntı üretilmiyor)
    assert sermaye.sermaye_taban({"realized_pnl": b.realized_pnl}, b.closed) == 0.0


# ==================================================================================================
# P1 — watchdog: sermaye_taban kanonik türetimden
# ==================================================================================================
def test_p1_watchdog_kanonik_tabani_kullanir_ve_yazim_yolu_alarm_uretmez(sandbox_state):
    """Aynı ondalık defter üç farklı yazım yolundan (birikim + satır sırası) geçince watchdog'un
    izlediği `sermaye_taban` BİT-BİT aynı kalır ve kanonik fonksiyonla birebirdir — 2026-08-12
    yanlış alarmı (toplama-sırası tozu) yapısal olarak kapanır."""
    _kitap_yaz(PNLS)
    ilk = watchdog.monotonicity_report(persist=True)
    assert ilk["ok"] is True
    taban = store.read_json(watchdog.MONOTONIC_FILE, {}).get("sermaye_taban")
    assert taban == TABAN == sermaye.sermaye_taban(), taban
    for yol in ({"ters": True}, {"karistir": 7}):
        _kitap_yaz(PNLS, **yol)                                 # aynı defter, farklı yazım yolu
        rep = watchdog.monotonicity_report()
        assert not [r for r in rep.get("regressions", []) if r["field"] == "sermaye_taban"], rep
        watchdog.monotonicity_report(persist=True)
        assert store.read_json(watchdog.MONOTONIC_FILE, {})["sermaye_taban"] == TABAN


def test_p1_gercek_gerileme_HALA_alarmlar_ve_af_yolu_hazir(sandbox_state):
    """EŞİK GEVŞETİLMEDİ: gerçek 1-sentlik beyan silinmesi dedektörün `v < p` kuralını aynen
    yakar. GEÇİŞ NOTU yolu da ÇALIŞIR hâlde: tek-seferlik `grant_amnesty('sermaye_taban', …)`
    tam-eşleşmeli affı verir — kod affı ÇAĞIRMAZ (canlı karar), yol burada kanıtlanır."""
    _kitap_yaz(PNLS)
    watchdog.monotonicity_report(persist=True)
    pf = store.read_json("portfolio.json", {})
    store.write_json("portfolio.json", {**pf, "realized_pnl": float(pf["realized_pnl"]) - 0.01})
    rep = watchdog.monotonicity_report()
    kayit = [r for r in rep["regressions"] if r["field"] == "sermaye_taban"]
    assert rep["ok"] is False and kayit, rep
    assert kayit[0]["was"] == TABAN and kayit[0]["now"] == round(TABAN - 0.01, 2), kayit
    # geçiş affı: (alan, was, now) birebir → bayrak yeşile döner, af YAZILI kalır
    watchdog.grant_amnesty("sermaye_taban", TABAN, round(TABAN - 0.01, 2),
                           reason="v236 geçiş testi: kanonik türetime tek-seferlik geçiş sapması",
                           by="test_v236")
    rep2 = watchdog.monotonicity_report()
    assert rep2["ok"] is True
    assert [a for a in rep2["amnestied"] if a["field"] == "sermaye_taban"], rep2


# ==================================================================================================
# P3a — SEARCH_PROGRESS: updated_at damgası (tek yazım kapısı)
# ==================================================================================================
def test_p3a_progress_damgasi_kanonik_ve_tum_yazimlar_kapidan(monkeypatch):
    """Her `_progress` yazımı tz-aware UTC ISO `updated_at` taşır; hermes kaynağında `_progress`
    dışında çıplak `SEARCH_PROGRESS.update(` KALMADI (kapı tekliği — kaynak taraması, codelaw
    deseni). Damga yazımdan yazıma İLERLER (asılı aramada donmuş görünmesinin ön şartı)."""
    import inspect
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    hermes._progress(running=True, phase="probing", i=1)
    d1 = hermes.SEARCH_PROGRESS["updated_at"]
    t1 = dt.datetime.fromisoformat(d1)
    assert t1.tzinfo is not None and t1.utcoffset() == dt.timedelta(0), d1
    time.sleep(1.05)                                            # timespec=seconds → damga ilerlesin
    hermes._progress(running=True, phase="probing", i=2)
    assert hermes.SEARCH_PROGRESS["updated_at"] > d1
    src = inspect.getsource(hermes)
    assert src.count("SEARCH_PROGRESS.update(") == 1, \
        "hermes'te _progress kapısı dışında çıplak SEARCH_PROGRESS.update kaldı"


def test_p3a_damga_sprint_parmak_izini_TAZELEMEZ(sandbox_state, monkeypatch):
    """Damga bayatlık yasasının parmak izine GİRMEZ: içeriksiz bir yeniden-yazım (aynı faz/i,
    yalnız updated_at değişir) sprint'in bayatlık saatini SIFIRLAYAMAZ — girseydi her damga
    'ilerleme' okunur, v235 yasası körleşirdi (bayrak yine günlerce kilit tutardı)."""
    from meridian import sprint
    monkeypatch.setattr(sprint, "_ARAMA_GOZLEM", {"iz": None, "beri": None, "olayli": False})
    monkeypatch.setattr(sprint, "_YETIM_OLAYLI", set())
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    hermes._progress(running=True, phase="probing", i=2, total=10)
    assert sprint.should_run(now=GECE)["sebep"] == "mesgul:canli_arama"      # gözlem başlar
    hermes._progress(running=True, phase="probing", i=2, total=10)           # yalnız damga değişti
    karar = sprint.should_run(now=GECE + dt.timedelta(hours=6, minutes=30))
    assert karar["arama_bayragi"]["bayat"] is True, karar
    assert karar["sebep"] != "mesgul:canli_arama", karar


# ==================================================================================================
# P3b — reflect_once finally güvenlik ağı
# ==================================================================================================
def test_p3b_finally_agi_istisna_yolunda_bayragi_indirir(monkeypatch):
    """Gövde bayrağı kaldırıp İSTİSNAYLA çıkarsa (bugün var olmayan bir yol dahil) sarmalayıcı
    bayrağı İNDİRİR — canlı vakanın 'günlerce running=True' hâli süreç-içi birinci hatta ölür."""
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)

    def _patlayan(target_regime="auto", *, background=False):
        hermes._progress(running=True, phase="probing", i=3)
        raise RuntimeError("asili-arama benzetimi")

    monkeypatch.setattr(hermes, "_reflect_once_govde", _patlayan)
    with pytest.raises(RuntimeError):
        hermes.reflect_once()
    assert hermes.SEARCH_PROGRESS.get("running") is False
    assert hermes.SEARCH_PROGRESS.get("kaynak") == "reflect_once_finally_agi"
    assert hermes.SEARCH_PROGRESS.get("updated_at")


def test_p3b_finally_agi_temiz_cikista_NOOP(monkeypatch):
    """Ağ yalnız güvenlik ağıdır: gövde bayrağı zaten indirmişse (normal 'done' yolu) sarmalayıcı
    HİÇBİR alanı ezmez — mevcut hata/başarı yazımları aynen kalır."""
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)

    def _duzgun(target_regime="auto", *, background=False):
        hermes._progress(running=False, phase="done", status="no_candidate")
        return {"status": "no_candidate"}

    monkeypatch.setattr(hermes, "_reflect_once_govde", _duzgun)
    assert hermes.reflect_once() == {"status": "no_candidate"}
    assert hermes.SEARCH_PROGRESS.get("phase") == "done"
    assert hermes.SEARCH_PROGRESS.get("kaynak") is None


# ==================================================================================================
# P3c — havuz toplam-atalet tavanı
# ==================================================================================================
def test_p3c_ilerleyen_havuz_KESILMEZ(monkeypatch):
    """TOPLAM-ATALET yasasının yarısı: toplam süre tavanın 2 katı olsa bile her iş tavan penceresi
    İÇİNDE bittiği sürece akış kesilmez — uzun ama CANLI bir gece araması asla kurban edilmez."""
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 0.5)
    monkeypatch.setattr(reflect, "_pool_probe_job",
                        lambda j: (time.sleep(0.12), (j["key"], {"oos": 1.0}))[1])
    jobs = [{"key": f"j{i}"} for i in range(6)]                 # 6 × 0.12s ≈ 0.72s > 0.5s tavan
    with cf.ThreadPoolExecutor(max_workers=1) as ex:
        cikti = dict(reflect._havuz_sonuclari(ex, jobs))
    assert set(cikti) == {f"j{i}" for i in range(6)}


def test_p3c_olu_havuz_toplam_atalette_yakalanir(monkeypatch):
    """Yasanın öbür yarısı: son bitenden beri tavan boyunca SIFIR ilerleme → `_HavuzAtaleti`
    (biten/bekleyen sayımlarıyla). Kilitlenmiş işçi ebeveyni artık sonsuza dek bekletemez."""
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 0.3)
    kilit = threading.Event()

    def _is(j):
        if j["key"] == "asili":
            kilit.wait(5.0)                                     # kilitlenmiş işçi benzetimi
        return j["key"], {"oos": 1.0}

    monkeypatch.setattr(reflect, "_pool_probe_job", _is)
    ex = cf.ThreadPoolExecutor(max_workers=2)
    try:
        with pytest.raises(reflect._HavuzAtaleti) as z:
            list(reflect._havuz_sonuclari(ex, [{"key": "hizli"}, {"key": "asili"}]))
        assert z.value.biten == 1 and z.value.bekleyen == 1, (z.value.biten, z.value.bekleyen)
    finally:
        kilit.set()                                             # thread'i serbest bırak (temizlik)
        ex.shutdown(wait=True)


def test_p3c_prefill_zaman_asimi_OLAYLI_ve_arama_olmez(sandbox_state, monkeypatch):
    """UÇTAN UCA kurtarma: hiçbir işi bitmeyen (kilitlenmiş) bir havuzda `_parallel_prefill_probes`
    (1) İSTİSNASIZ döner — arama ölmez, kalan sondalar sıralı yolda hesaplanır; (2) havuz bloke
    etmeden kapatılır (`shutdown(wait=False, cancel_futures=True)` — with-çıkışının sonsuz join'i
    yok); (3) tespit OLAYLIDIR: `arama_havuzu_zaman_asimi` sayımlarıyla düşer (YASA 4)."""
    olusanlar = []

    class _AsiliHavuz:
        def __init__(self, *a, **k):
            self._processes = {}
            self.kapanislar = []
            olusanlar.append(self)

        def submit(self, fn, j):
            return cf.Future()                                  # hiç bitmeyecek iş

        def shutdown(self, wait=True, cancel_futures=False):
            self.kapanislar.append((wait, cancel_futures))

    monkeypatch.setattr("concurrent.futures.ProcessPoolExecutor", _AsiliHavuz)
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 0.2)
    monkeypatch.setattr(reflect.versioning, "bump", lambda cur, var, new, note="": {"version": 2})
    monkeypatch.setattr(reflect, "params_of", lambda c: {})
    monkeypatch.setattr(reflect, "_probe_key", lambda cand, var, new, w: f"k:{var}:{new}")
    monkeypatch.setenv("MERIDIAN_PARALLEL_PROBES", "1")
    baslangic = time.monotonic()
    reflect._parallel_prefill_probes([("a.x", 1.0), ("a.y", 2.0)], current={"version": 1},
                                     version=1, goal={}, w=(0.6, 0.2, 0.2, 0.1, [3], 5),
                                     regime=None)
    assert time.monotonic() - baslangic < 5.0, "zaman aşımı tavana bağlı değil — bekleyiş sınırsız"
    olay = _olaylar("arama_havuzu_zaman_asimi")
    assert olay and olay[-1]["yer"] == "probe_prefill", olay
    assert olay[-1]["biten"] == 0 and olay[-1]["bekleyen"] == 2, olay
    assert olusanlar and (False, True) in olusanlar[0].kapanislar, \
        "havuz bloke etmeden (wait=False, cancel_futures=True) kapatılmadı"
