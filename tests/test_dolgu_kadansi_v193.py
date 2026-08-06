"""test_dolgu_kadansi_v193.py — KANIT DOLGUSUNUN OTOMATİK KADANSI (canlı olgu, 2026-08-06).

OPERATÖR GÖZLEMİ: "kanıt dolgusu otomatik HİÇ koşmuyor; elle tetik çalışıyor."

TEŞHİS — ZİNCİR EKSİK DEĞİLDİ, DAMGA YANLIŞTI. `scheduler._learning_cadence` üçüncü adımı olarak
dolguyu ZATEN çağırıyordu. Kusur şuydu:
  1. `hermes.backfill_budget()` ajan havuzu SOĞUMADAYKEN tavan 0 döndürür (doğru davranış);
  2. kadans dolguyu başlatmaz — ama `learn_session` damgasını YİNE DE basar;
  3. damga basıldığı için o seans bir daha DENENMEZ → havuz açıldıktan sonra bile dolgu o seans
     için hiç koşmaz.
Yani "askıda" sessizce "bitti"ye dönüşüyordu. Ve soğuma nadir değildi: boş-yanıt zinciri
(`review_fallback_empty` → `brain_pause`) her turda yeni bir pencere kuruyordu — bu dosyanın
kardeşi `test_ajan_bos_yanit_v193.py` o kolun kendisini kapatıyor.

DOSYA DÖRT SÖZLEŞMEYİ KİLİTLER:
  1. Kadans dolguyu tetikler ve damgayı YALNIZ gerçekten başlayınca basar.
  2. Havuz askıdaysa ERTELENİR (damga basılmaz) + `dolgu_ertelendi` olayı — seans+sebep başına BİR
     KEZ (300 sn'lik poll'de koşulsuz uyarı günde 288 satır ederdi).
  3. Ertelenen dolgu "current" dalında yeniden yoklanır: havuz açıldığı ilk poll'de koşar.
  4. Damga KALICIDIR (`_DURABLE`) — yeniden başlatma gecelik LLM bütçesini baştan yakmaz.
Ve bir DAVRANIŞ AYRIMI: `MERIDIAN_BACKFILL_MAX_DAYS=0` operatörün KAPATMASIDIR, erteleme değil.
"""
import pytest

from meridian import hermes, scheduler, store


def _events(event: str) -> list:
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


@pytest.fixture(autouse=True)
def _temiz(monkeypatch):
    """Her test bilinen bir dünyada başlar: `_state` sızmaz, env kolu kabuktan miras alınmaz."""
    monkeypatch.delenv("MERIDIAN_BACKFILL_MAX_DAYS", raising=False)
    for k in ("learn_session", "dolgu_session", "_dolgu_ertelendi", "last_learn"):
        scheduler._state.pop(k, None)
    yield
    for k in ("learn_session", "dolgu_session", "_dolgu_ertelendi", "last_learn"):
        scheduler._state.pop(k, None)


def _butce(monkeypatch, tavan, kaynak="turetim", soguma=False):
    """`backfill_budget`ı çivile — kota/soğuma türetimi burada ölçülmüyor (kendi testleri var);
    ölçülen şey KADANSIN o türetime nasıl davrandığı."""
    monkeypatch.setattr(hermes, "backfill_budget",
                        lambda: {"tavan": tavan, "kaynak": kaynak, "formul": "test",
                                 "soguma_aktif": soguma, "agent_cooldown_s": 900.0 if soguma else 0.0,
                                 "kalan": 0 if (tavan == 0 and not soguma) else 40})


# ----------------------------------------------------------------- 1) MUTLU YOL: KADANS TETİKLER
def test_kadans_dolguyu_baslatir_ve_damgayi_basar(sandbox_state, monkeypatch,
                                                  hermes_async_cagrilari):
    _butce(monkeypatch, tavan=3)
    out = scheduler._dolgu_kadansi("2026-08-05")
    assert out["baslatildi"] is True
    assert [c[0] for c in hermes_async_cagrilari] == ["backfill_opinions_async"]
    assert scheduler._state["dolgu_session"] == "2026-08-05"


def test_damga_DURABLE_listesinde(sandbox_state):
    """RESTART YENİDEN TETİKLEMESİN: süreç başına sıfırlanan bir damga, bir gecede üç kez yeniden
    başlatılan bir panoda gecelik LLM bütçesini üç kez yakardı (`refetch_attempts` dersinin ikizi)."""
    assert "dolgu_session" in scheduler._DURABLE
    scheduler._state["dolgu_session"] = "2026-08-05"
    scheduler._persist()
    scheduler._state.pop("dolgu_session")
    assert scheduler._rehydrate().get("dolgu_session") == "2026-08-05"


# ------------------------------------------------------------- 2) ASKIDA ≠ BİTTİ (KUSURUN KENDİSİ)
def test_havuz_askidayken_damga_BASILMAZ_ve_ertelendi_yazilir(sandbox_state, monkeypatch,
                                                              hermes_async_cagrilari):
    """KUSURUN ÇİVİSİ: eski kod burada damgayı basıyordu ve o seansın dolgusu sonsuza dek kayıptı."""
    _butce(monkeypatch, tavan=0, soguma=True)
    out = scheduler._dolgu_kadansi("2026-08-05")
    assert out == {"baslatildi": False, "ertelendi": True, "sebep": "havuz_askida",
                   "tavan": 0, "formul": "test", "butce": hermes.backfill_budget()}
    assert "dolgu_session" not in scheduler._state, "ERTELENEN dolgu damgalanamaz"
    assert hermes_async_cagrilari == [], "askıdayken hiçbir süreç doğmamalı"
    ev = _events("dolgu_ertelendi")
    assert len(ev) == 1 and ev[0]["sebep"] == "havuz_askida" and len(ev[0]["detail"]) >= 20


def test_ertelendi_olayi_seans_sebep_basina_bir_kez(sandbox_state, monkeypatch):
    """ALARM HİJYENİ (v192 dersi): 300 sn'lik poll'de koşulsuz uyarı günde 288 satır ederdi ve
    operatörü defteri okumamaya eğitirdi. Sebep DEĞİŞİRSE yeniden yazılır — o yeni bir olgudur."""
    _butce(monkeypatch, tavan=0, soguma=True)
    for _ in range(5):
        scheduler._dolgu_kadansi("2026-08-05")
    assert len(_events("dolgu_ertelendi")) == 1
    _butce(monkeypatch, tavan=0, soguma=False)          # aynı seans, BAŞKA sebep (gün kotası bitti)
    scheduler._dolgu_kadansi("2026-08-05")
    assert [e["sebep"] for e in _events("dolgu_ertelendi")] == ["havuz_askida", "kota_tukendi"]
    scheduler._dolgu_kadansi("2026-08-06")              # yeni seans → yeniden ilan edilir
    assert len(_events("dolgu_ertelendi")) == 3


def test_operator_kapatmasi_erteleme_DEGILDIR(sandbox_state, monkeypatch, hermes_async_cagrilari):
    """`MERIDIAN_BACKFILL_MAX_DAYS=0` bilinçli bir kapatmadır. Onu ertelenmiş saymak, kapalı bir
    mekanizmayı her poll'de sonsuza dek yeniden yoklamak (ve deftere yazmak) olurdu."""
    _butce(monkeypatch, tavan=0, kaynak="env:MERIDIAN_BACKFILL_MAX_DAYS")
    out = scheduler._dolgu_kadansi("2026-08-05")
    assert out["ertelendi"] is False and out["sebep"] == "operator_kapatti"
    assert scheduler._state["dolgu_session"] == "2026-08-05", "kapalı düğme damgalanır"
    assert _events("dolgu_ertelendi") == []


def test_butce_okunamazsa_ertelenir_ve_sessiz_kalinmaz(sandbox_state, monkeypatch):
    """YASA 4: bütçe okuması düşerse dolgu koşmadı — ama "koşmadı" ile "koşamadı" ayrı hâllerdir ve
    ikincisi damgalanmamalı (arıza geçince yeniden denenmeli)."""
    monkeypatch.setattr(hermes, "backfill_budget",
                        lambda: (_ for _ in ()).throw(RuntimeError("defter bozuk")))
    out = scheduler._dolgu_kadansi("2026-08-05")
    assert out["ertelendi"] is True and "dolgu_session" not in scheduler._state
    assert _events("opinion_backfill_cadence_failed")


# --------------------------------------------------------- 3) KADANS ↔ TELAFİ DİKİŞİ (ZİNCİR)
def test_ogrenme_kadansi_dolgu_adimini_bu_fonksiyona_devreder(sandbox_state, monkeypatch):
    """YASA 6: dolgunun TEK tetik yeri olsun diye adım çıkarıldı — iki yerde iki tavan/damga,
    formül değiştiği gün sessizce ayrışırdı."""
    cagri: list = []
    monkeypatch.setattr(scheduler, "_dolgu_kadansi",
                        lambda s: cagri.append(s) or {"baslatildi": True, "butce": {"tavan": 1}})
    monkeypatch.setattr(scheduler, "_now", lambda: "2026-08-05T22:00:00+00:00")
    out = scheduler._learning_cadence("2026-08-05")
    assert cagri == ["2026-08-05"] and out["dolgu"]["baslatildi"] is True
    assert scheduler._state["learn_session"] == "2026-08-05"


def test_ertelenen_dolgu_havuz_acilinca_ayni_seans_icin_kosar(sandbox_state, monkeypatch,
                                                              hermes_async_cagrilari):
    """TELAFİNİN KENDİSİ: kadans `fresh` dalında koşar ve bar geldiği an o dal sessizleşir. Erteleme
    orada kalsaydı dolgu bir sonraki seansa kadar (ya da hiç) koşmazdı."""
    _butce(monkeypatch, tavan=0, soguma=True)
    scheduler._dolgu_kadansi("2026-08-05")
    scheduler._state["learn_session"] = "2026-08-05"
    assert "dolgu_session" not in scheduler._state
    _butce(monkeypatch, tavan=5)                        # havuz açıldı
    scheduler._dolgu_kadansi("2026-08-05")
    assert scheduler._state["dolgu_session"] == "2026-08-05"
    assert [c[0] for c in hermes_async_cagrilari] == ["backfill_opinions_async"]


def test_telafi_kapisi_kadans_kosmadan_dolguyu_one_almaz(sandbox_state):
    """SIRA GEREKÇELİ (`_learning_cadence`): antrenman ve Eksen-2 kotasızdır ve dolgudan ÖNCE gelir —
    dolgu, ötekilerin artığıyla değil, ötekiler onun artığıyla koşmasın diye sonuncudur."""
    import inspect
    import re
    kaynak = inspect.getsource(scheduler.advance_once)
    dal = re.search(r"if\s+last_closed\s+and(.{0,300}?)_dolgu_kadansi\(last_closed\)",
                    kaynak, re.S)
    assert dal, "'current' dalında ertelenmiş dolgu telafisi YOK — erteleme kalıcı sessizliğe döner"
    assert 'learn_session") == last_closed' in dal.group(1), \
        "telafi, kadans o seans için koşmadan dolguyu ÖNE ALMAMALI (sıra gerekçesi)"
    assert 'dolgu_session") != last_closed' in dal.group(1), \
        "telafi kendi damgasını okumalı, yoksa başlamış dolguyu her poll'de yeniden tetiklerdi"
