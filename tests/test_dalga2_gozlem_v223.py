"""test_dalga2_gozlem_v223.py — DALGA-2 GÖZLEM: üç sahte-yeşil/sessiz-bozulma kalemi (2026-08-09).

Üç kusur, üçü de "sistem bir şey söylüyor ama gerçeği söylemiyor" sınıfından:

  KALEM 3 — SİSTEM ÖLÜ AMA PANODA ÇALIŞIYOR (sahte-yeşil). `mechanism_beats.json` nabzı KADANS
  KONTROLÜNÜN damgasıdır ("dişli döndü mü"), canlılığın DEĞİL ("dişlinin ürettiği iş yaşıyor mu").
  sprint pid'i ölü + faz 'baseline'da takılıyken kadans nabzı taze kalır; hipotez defteri günlerce
  donukken öğrenme kadansı her seans nabız atar. `watchdog.liveness_report` GERÇEK canlılığı ölçüp
  BEYAN eder: "koşuyor" yalnız gerçekten koşuyorken, aksi halde "N gündür KOŞMADI".

  KALEM 6 — TOHUM/CANLI KARNE AYRIMI. `/api/public/summary` 96 "kapanmış işlem" diyordu; gövdesi
  replay TOHUMU (training, survivorship'li), GERÇEK canlı 1. Özet artık ayrımı KAYNAK DAMGASINDAN
  (ledgerstamp) okuyup ayrı raporlar — sabit sayı yazmadan (C10), $ P&L sızdırmadan.

  KALEM 7 — UNIVERSE-UNKNOWN SESSİZ. `universe_drift.json` üyelik kaynağı ölünce (lxml/FMP/finviz)
  `status:"unknown"` yazar ve loop YALNIZ status=='ok' iken alarm eder — "ÖLÇEMEDİM" sessiz kalır.
  `watchdog.check_universe_and_alarm` bunu sev-2 `DATA_QUALITY` (ÖLÇÜLEMEDİ) alarmına çevirir.
  "unknown" ≠ "sapma yok" (determinism `olculemedi` dalının evren-tarafı ikizi).

SAAT ÇİVİLİDİR (2026-08-03 tarih-bağımlı fikstür dersi): `watchdog._now` monkeypatch'lenir.
Mandal (_LIVENESS_ALARMED/_UNIVERSE_ALARMED) modül-globaldir → her test öncesi/sonrası temizlenir.
"""
from __future__ import annotations

import calendar
import datetime as dt

import pytest

from meridian import api, ledgerstamp, obs, store, watchdog

# 2026-08-06T12:00:00Z — gün ortası (komşu testlerin saat oynatması gün sınırını kazara geçmesin).
T0 = float(calendar.timegm((2026, 8, 6, 12, 0, 0, 0, 0, 0)))


@pytest.fixture
def saat(monkeypatch):
    """`watchdog._now` çivili; testler `saat.t`yi taban alır."""
    class _Saat:
        t = T0
    s = _Saat()
    monkeypatch.setattr(watchdog, "_now", lambda: s.t)
    return s


@pytest.fixture
def alarmlar(monkeypatch):
    """`obs.alarm` çağrılarını dict olarak yakalar (token + mesaj + alanlar)."""
    kayit: list[dict] = []
    monkeypatch.setattr(obs, "alarm",
                        lambda tok, msg, **kw: kayit.append({"tok": tok, "msg": msg, **kw}))
    return kayit


@pytest.fixture(autouse=True)
def _mandal_temiz():
    """Modül-global alarm mandalları testler arası TAŞINMASIN (v192 çırpınma dersinin ikizi)."""
    watchdog._LIVENESS_ALARMED.clear()
    watchdog._UNIVERSE_ALARMED.clear()
    yield
    watchdog._LIVENESS_ALARMED.clear()
    watchdog._UNIVERSE_ALARMED.clear()


def _sprint(monkeypatch, saat, *, active: bool, phase: str, age_h):
    """sprint.status() ve sprint_status.json yaşını çivile — sprint.py'ye DOKUNMADAN (yalnız
    status() okunur; canlılık bekçisi onu import edip çağırır)."""
    import meridian.sprint as sprint_mod
    monkeypatch.setattr(sprint_mod, "status", lambda: {"active": active, "phase": phase})
    mt = None if age_h is None else (saat.t - age_h * 3600)
    monkeypatch.setattr(store, "mtime", lambda name: mt)


def _hyps(saat, ages_h: list[float]) -> None:
    """Hipotezleri verilen YARATILMA yaşlarıyla (saat) yaz — `ts` kayıt damgası (memory.record)."""
    rows = []
    for i, a in enumerate(ages_h):
        ts = dt.datetime.fromtimestamp(saat.t - a * 3600, dt.timezone.utc).isoformat(timespec="seconds")
        rows.append({"variable": f"v{i}", "status": "proposed", "ts": ts})
    store.write_jsonl("hypotheses.jsonl", rows)


# =================================================================================================
# KALEM 3a — SPRINT CANLILIĞI (orphan)
# =================================================================================================
def test_sprint_olu_pid_nonterminal_faz_ORPHAN(sandbox_state, saat, monkeypatch):
    """pid ölü + faz 'baseline' (in-progress) → orphan; beyan 'KOŞMADI' der, 'koşuyor' DEMEZ."""
    _sprint(monkeypatch, saat, active=False, phase="baseline", age_h=42.6)
    sp = watchdog._sprint_liveness()
    assert sp["orphaned"] is True and sp["ok"] is False
    # DÜRÜST BEYAN: "N gündür KOŞMADI" + panoyu açıkça uyarır ("koşuyor sanmasın").
    assert "KOŞMADI" in sp["beyan"] and "sanmasın" in sp["beyan"]


def test_sprint_canli_pid_taze_KOSUYOR(sandbox_state, saat, monkeypatch):
    """pid canlı + durum taze → gerçekten koşuyor (orphan DEĞİL)."""
    _sprint(monkeypatch, saat, active=True, phase="search", age_h=0.2)
    sp = watchdog._sprint_liveness()
    assert sp["ok"] is True and sp["orphaned"] is False and "KOŞUYOR" in sp["beyan"]


def test_sprint_terminal_faz_ORPHAN_DEGIL(sandbox_state, saat, monkeypatch):
    """pid ölü ama faz 'done' (terminal) → sprint DÜRÜSTÇE bitmiş, orphan değil (boşta)."""
    _sprint(monkeypatch, saat, active=False, phase="done", age_h=100)
    sp = watchdog._sprint_liveness()
    assert sp["orphaned"] is False and sp["ok"] is True and "boşta" in sp["beyan"]


def test_sprint_pid_canli_ama_bayat_PID_YENIDEN_KULLANIM(sandbox_state, saat, monkeypatch):
    """os.kill(pid,0) yeniden kullanılan pid'de de başarılı olabilir: pid 'canlı' ama durum çok
    bayatsa canlılık tazelikle çapraz doğrulanır → orphan (şüphe beyanlı)."""
    _sprint(monkeypatch, saat, active=True, phase="baseline", age_h=100)  # 100 > 72 sa eşiği
    sp = watchdog._sprint_liveness()
    assert sp["orphaned"] is True and "yeniden-kullanım" in sp["beyan"]


def test_sprint_probe_dustu_OLCULEMEDI(sandbox_state, saat, monkeypatch):
    """sprint.status() fırlarsa: 'koşuyor' DEMEZ — ÖLÇÜLEMEDİ (ok None), YASA 4."""
    import meridian.sprint as sprint_mod

    def _patla():
        raise RuntimeError("kum havuzu okunamadı")
    monkeypatch.setattr(sprint_mod, "status", _patla)
    sp = watchdog._sprint_liveness()
    assert sp["ok"] is None and sp["olculemedi"] is True and "ÖLÇÜLEMEDİ" in sp["beyan"]


# =================================================================================================
# KALEM 3b — ÖĞRENME CANLILIĞI (stall)
# =================================================================================================
def test_ogrenme_donuk_STALLED(sandbox_state, saat):
    """En taze hipotez 7 günden eski → öğrenme durdu; beyan 'DURDU' der."""
    _hyps(saat, [200, 300, 400])           # en taze 200 sa > 168 sa eşiği
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is True and lr["ok"] is False and "DURDU" in lr["beyan"]


def test_ogrenme_taze_STALLED_DEGIL(sandbox_state, saat):
    """En taze hipotez eşik içinde → öğrenme ilerliyor."""
    _hyps(saat, [10, 300])                  # en taze 10 sa
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is False and lr["ok"] is True


def test_ogrenme_hic_hipotez_DURDU_DEGIL(sandbox_state, saat):
    """Hiç hipotez yok = 'durdu' DEĞİL (ayrı hâl: hiç başlamadı) — kurt masalı anlatılmaz."""
    store.write_jsonl("hypotheses.jsonl", [])
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is False and lr["n"] == 0 and "hiç başlamadı" in lr["beyan"]


def test_ogrenme_ts_ayristirilamadi_OLCULEMEDI(sandbox_state, saat):
    """Kayıt damgası ayrıştırılamazsa: 'taze' DEMEZ — ÖLÇÜLEMEDİ (ok None)."""
    store.write_jsonl("hypotheses.jsonl", [{"variable": "x", "ts": "bozuk-damga"}])
    lr = watchdog._learning_liveness()
    assert lr["ok"] is None and lr["olculemedi"] is True


# =================================================================================================
# KALEM 3c — CANLILIK ALARM GEÇİŞİ (mandal + ÖLÇÜLEMEDİ≠0)
# =================================================================================================
def test_check_liveness_orphan_ve_stall_alarm_BIR_kez(sandbox_state, saat, alarmlar, monkeypatch):
    """Orphan + stall birlikte → iki MECHANISM_STALE; ikinci poll'da mandal susturur (çırpınma yok)."""
    _sprint(monkeypatch, saat, active=False, phase="baseline", age_h=48)
    _hyps(saat, [200])
    watchdog.check_liveness_and_alarm()
    ilk = [a for a in alarmlar if a["tok"] == "MECHANISM_STALE"]
    kinds = {a.get("kind") for a in ilk}
    assert "sprint_liveness" in kinds and "learning_stalled" in kinds
    watchdog.check_liveness_and_alarm()                 # aynı hâl sürüyor
    assert len([a for a in alarmlar if a["tok"] == "MECHANISM_STALE"]) == len(ilk)  # yeni alarm YOK


def test_check_liveness_toparlaninca_YENIDEN(sandbox_state, saat, alarmlar, monkeypatch):
    """Orphan alarmı → sprint canlanır (jeton düşer) → yeniden ölür → YENİDEN alarm (histerezis)."""
    _hyps(saat, [10])                                   # öğrenme taze — yalnız sprint bacağı test edilir
    _sprint(monkeypatch, saat, active=False, phase="baseline", age_h=48)
    watchdog.check_liveness_and_alarm()
    _sprint(monkeypatch, saat, active=True, phase="search", age_h=0.1)   # canlandı
    watchdog.check_liveness_and_alarm()
    _sprint(monkeypatch, saat, active=False, phase="baseline", age_h=48)  # yeniden öldü
    watchdog.check_liveness_and_alarm()
    orphan = [a for a in alarmlar if a.get("kind") == "sprint_liveness"]
    assert len(orphan) == 2                             # ölüm → canlanma → ölüm = iki ayrı meşru olay


def test_check_liveness_OLCULEMEDI_kendi_jetonu(sandbox_state, saat, alarmlar, monkeypatch):
    """ÖLÇÜLEMEDİ ≠ 0: ölçülemeyen canlılık 'koşuyor' sayılmaz, kendi jetonuyla duyurulur."""
    import meridian.sprint as sprint_mod
    monkeypatch.setattr(sprint_mod, "status", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    _hyps(saat, [10])
    watchdog.check_liveness_and_alarm()
    olc = [a for a in alarmlar if a.get("olculemedi") and a.get("kind") == "sprint_liveness"]
    assert len(olc) == 1 and "ÖLÇÜLEMEDİ" in olc[0]["msg"]


# =================================================================================================
# KALEM 6 — PUBLIC SUMMARY TOHUM/CANLI AYRIMI
# =================================================================================================
def _trades_kur():
    """1 canlı (R=-1.5), 3 tohum, 1 belirsiz — kaynak damgasından okunur (ledgerstamp)."""
    store.write_jsonl("trades.jsonl", [
        {"kaynak": ledgerstamp.LIVE_PAPER, "r_multiple": -1.5, "setup": "vcp", "regime": "chop"},
        {"kaynak": ledgerstamp.REPLAY_SEED, "r_multiple": 0.8},
        {"kaynak": ledgerstamp.REPLAY_SEED, "r_multiple": 1.2},
        {"kaynak": ledgerstamp.REPLAY_SEED, "r_multiple": -0.3},
        {"r_multiple": 0.5},                              # damgasız → belirsiz
    ])


def test_public_summary_tohum_canli_AYRI(sandbox_state):
    """Özet canlı/tohum/belirsiz'i AYRI raporlar; parçalar ham toplamı KORUR (kaynaktan, C10)."""
    _trades_kur()
    d = api.api_public_summary()
    assert d["closed_trades"] == 5                        # ham toplam GERİYE UYUM
    assert d["closed_trades_live"] == 1                   # GERÇEK canlı — manşetteki '96'nın gerçeği
    assert d["closed_trades_seed"] == 3
    assert d["closed_trades_belirsiz"] == 1
    assert d["closed_trades_live"] + d["closed_trades_seed"] + d["closed_trades_belirsiz"] \
        == d["closed_trades"]                             # korunum: hiçbir satır kaybolmaz


def test_public_summary_canli_n_ve_R_dollar_sizmaz(sandbox_state):
    """Canlı bloğu n + R-multiple taşır (araştırma metriği); $ P&L uç sözleşmesi gereği YOK."""
    _trades_kur()
    d = api.api_public_summary()
    assert d["live"]["n"] == 1 and d["live"]["mean_r"] == -1.5 and d["live"]["sum_r"] == -1.5
    assert d["seed"]["n"] == 3
    # $ P&L sızmasın: canlı/tohum bloklarında dolar/realized_pnl alanı OLMAMALI (yalnız R + not).
    for blok in (d["live"], d["seed"]):
        assert not any(k in blok for k in ("pnl", "realized_pnl", "usd", "dollar", "capital"))


def test_public_summary_score_ve_closed_trades_KAPSAM_beyanli(sandbox_state):
    """C10/beyan: score ne üstünden, closed_trades ne kapsıyor — payda açıkça yazılır."""
    _trades_kur()
    d = api.api_public_summary()
    assert "TOHUM DAHİL" in d["score_kapsam"] and "closed_trades_live" in d["score_kapsam"]
    assert "replay_seed" in d["closed_trades_kapsam"]     # kaynak-damga sözleşmesi dışarı beyanlı


# =================================================================================================
# KALEM 7 — UNIVERSE-UNKNOWN → ALARM (sessiz bozulma değil)
# =================================================================================================
def test_universe_unknown_OLCULEMEDI_sapma_yok_DEMEZ(sandbox_state):
    """status 'unknown' → ÖLÇÜLEMEDİ; beyan 'sapma yok' DEMEZ (ölü isim sorusu cevapsız)."""
    store.write_json("universe_drift.json",
                     {"status": "unknown", "reason": "ImportError lxml", "date": "2026-08-09"})
    rep = watchdog.universe_audit_report()
    # Makine-okunur disklaimer: tüketici `olculemedi`ye bakar, "yok drift" SAYMAZ.
    assert rep["olculemedi"] is True and rep["status"] == "unknown"
    # Metin de açıkça reddeder: "sapma yok DEMEZ" — sessizce 'temiz' boyanmaz.
    assert "ÖLÇÜLEMEDİ" in rep["beyan"] and "DEMEZ" in rep["beyan"]


def test_universe_ok_OLCULEMEDI_DEGIL(sandbox_state):
    """status 'ok' → ölçüldü (alarm sebebi değil)."""
    store.write_json("universe_drift.json", {"status": "ok", "n_stale": 0, "date": "2026-08-09"})
    rep = watchdog.universe_audit_report()
    assert rep["olculemedi"] is False and rep["status"] == "ok"


def test_universe_dosya_yok_BILGI_alarm_degil(sandbox_state):
    """Dosya hiç yoksa: 'hiç koşmamış' bilgisi — ÖLÇÜLEMEDİ alarmı DEĞİL (denetim koşmadı)."""
    rep = watchdog.universe_audit_report()
    assert rep["olculemedi"] is False and rep["status"] == "yok"


def test_check_universe_unknown_DATA_QUALITY_alarm_BIR_kez(sandbox_state, alarmlar):
    """unknown → sev-2 DATA_QUALITY (olculemedi); ikinci poll'da mandal susturur."""
    store.write_json("universe_drift.json", {"status": "unknown", "reason": "FMP 402"})
    watchdog.check_universe_and_alarm()
    dq = [a for a in alarmlar if a["tok"] == "DATA_QUALITY" and a.get("kind") == "universe_drift"]
    assert len(dq) == 1 and dq[0].get("olculemedi") is True
    watchdog.check_universe_and_alarm()
    assert len([a for a in alarmlar if a["tok"] == "DATA_QUALITY"]) == 1   # çırpınma yok


def test_check_universe_ok_ALARM_YOK(sandbox_state, alarmlar):
    """status 'ok' → hiç alarm yok."""
    store.write_json("universe_drift.json", {"status": "ok", "n_stale": 0})
    watchdog.check_universe_and_alarm()
    assert not alarmlar


# =================================================================================================
# WIRING — check_and_alarm iki yeni dedektörü GERÇEKTEN çağırıyor mu (300 sn poll)
# =================================================================================================
def test_check_and_alarm_universe_dedektorunu_cagirir(sandbox_state, saat, alarmlar):
    """Ana poll (`check_and_alarm`) evren dedektörünü çağırıyor: unknown → DATA_QUALITY alarmı."""
    store.write_json("universe_drift.json", {"status": "unknown", "reason": "ImportError lxml"})
    watchdog.check_and_alarm()
    assert any(a["tok"] == "DATA_QUALITY" and a.get("kind") == "universe_drift" for a in alarmlar)


def test_check_and_alarm_canlilik_dedektorunu_cagirir(sandbox_state, saat, alarmlar, monkeypatch):
    """Ana poll canlılık dedektörünü çağırıyor: sprint orphan → MECHANISM_STALE alarmı."""
    _sprint(monkeypatch, saat, active=False, phase="baseline", age_h=48)
    _hyps(saat, [10])
    watchdog.check_and_alarm()
    assert any(a["tok"] == "MECHANISM_STALE" and a.get("kind") == "sprint_liveness" for a in alarmlar)
