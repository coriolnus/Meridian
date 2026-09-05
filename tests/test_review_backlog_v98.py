"""test_review_backlog_v98.py — 2026-07-26 review turunun BİLİNÇLİ ERTELENMİŞ beş kalemi.

Hepsinin ortak sınıfı aynı: bir ölçüm YAPILIYOR ama sonucu ya yanlış gruplanıyor, ya hiç
okunmuyor, ya da arızalandığında sessizlikten ayırt edilemiyor.

  1. `notify._signature` — ticker imzada İKİ YÖNE birden yanlış duruyordu: anahtar alanı varken
     farklı semboller tek gruba ÇÖKÜYOR, anahtar alanı yokken aynı kusur sembole göre BÖLÜNÜYORDU.
  2. `obs.NOTIFY_TOKENS` — el listesiydi ve çürümüştü (turu 20'de üç kritik jeton dışarıda kaldı);
     artık ALARM_ sabitlerinden TÜRETİLİYOR, bu dosya sözleşmeyi donduruyor.
  3. `alarm_delivery` — "teslim edilemedi" bulgusunu alarma çevirmek, ölçtüğü sayacı kendi besler.
  4. `ack_by` — yazılıyor, hiçbir yerde okunmuyordu (alan düzeyinde yasa 6).
  5. beyin zinciri — ölçüm ARIZASI ile "hermes hiç koşmamış" ayırt edilemiyordu; ilki artık konuşur,
     ikincisi hâlâ SESSİZ kalır (taze sandbox'ta yeni kırmızı üretmek mutasyon tabanını kirletirdi).
  6. `_fmp._HEALTH` — testler arası sızıyor, sonraki testi kendi kurmadığı bir bulguyla karşılaştırıyordu.
  7. "news.stock_news" [çapa-mezar-taşı] — `[]` dönmek doğru davranış; yutmanın SESSİZ olması değil.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from meridian import notify, obs, store, watchdog as wd
from meridian.api import app


def _row(name: str):
    return next((r for r in wd.parity_report()["rows"] if r["check"] == name), None)


# ---------------------------------------------------------------------------------------------
# 1) notify._signature — ticker iki yöne birden çalışır
# ---------------------------------------------------------------------------------------------
def test_a_broad_key_is_narrowed_by_the_ticker():
    """KABA BİRLEŞME: `kind=determinism` iki AYRI sembolün bozulmasını tek satıra çökertiyordu —
    operatör "1 mutasyon" okuyup 2 hisseyi kaçırıyordu."""
    aapl = {"alarm": "DATA_QUALITY", "kind": "determinism", "ticker": "AAPL",
            "message": "SESSİZ BAR MUTASYONU: AAPL 07-20"}
    tsla = {**aapl, "ticker": "TSLA", "message": "SESSİZ BAR MUTASYONU: TSLA 07-24"}
    assert notify._signature(aapl) != notify._signature(tsla), \
        "iki sembolün bozulması tek gruba çöktü — sayaç 1 diyor, kusur 2"
    assert notify._signature(aapl).endswith("determinism·AAPL")


def test_a_keyless_alarm_collapses_across_tickers():
    """YANLIŞ BÖLME: anahtar alanı OLMAYAN alarm mesaj yedeğine düşer ve oradaki ticker varyansı
    AYNI kusuru sembole göre bölüyordu — tek bir 'bakiye yetersiz' hatası N satır oluyordu."""
    aapl = {"alarm": "BROKER_REJECT", "ticker": "AAPL",
            "message": "Alpaca reddi: AAPL — insufficient buying power"}
    tsla = {"alarm": "BROKER_REJECT", "ticker": "TSLA",
            "message": "Alpaca reddi: TSLA — insufficient buying power"}
    assert notify._signature(aapl) == notify._signature(tsla), \
        "aynı kusur ticker başına bölündü — gelen kutusu tek arızayı N kez sayar"


def test_only_the_known_ticker_is_normalised_never_turkish_emphasis():
    """GENEL BÜYÜK-HARF NORMALİZASYONU YASAK: mesajlardaki 'SESSİZ', 'MAKULLÜK', 'CANLI' gibi
    vurgu sözcükleri sembol sanılsaydı imza boşalır ve HER kusur tek gruba düşerdi."""
    ev = {"alarm": "BROKER_REJECT", "ticker": "AAPL",
          "message": "SESSİZ RED: AAPL kapıda durdu"}
    sig = notify._signature(ev)
    assert "SESSİZ" in sig, f"Türkçe vurgu sözcüğü sembol sanıldı: {sig}"
    assert "AAPL" not in sig and "§" in sig, f"bilinen ticker normalize edilmedi: {sig}"


def test_an_event_without_a_ticker_keeps_the_old_signature():
    """Ticker YOKSA davranış değişmez — yeni alan eski gruplamayı bozamaz."""
    assert notify._signature({"alarm": "MECHANISM_STALE", "mechanism": "fmp_source"}) \
        == "MECHANISM_STALE·fmp_source"


def test_the_ticker_never_becomes_a_key_on_its_own():
    """Ticker anahtar LİSTESİNE girseydi ikinci senaryodaki tek kusur yine sembole bölünürdü:
    ticker bir kusur KİMLİĞİ değil, var olan bir kimliğin nitelemesidir."""
    assert notify._signature({"alarm": "BROKER_REJECT", "ticker": "AAPL"}) \
        == notify._signature({"alarm": "BROKER_REJECT", "ticker": "TSLA"})


# ---------------------------------------------------------------------------------------------
# 2) NOTIFY_TOKENS — türetme + donmuş sözleşme
# ---------------------------------------------------------------------------------------------
def test_notify_tokens_are_derived_from_the_alarm_constants():
    """DONMUŞ SÖZLEŞME: bir ALARM_ sabiti eklemek/silmek bildirim kapsamını SESSİZCE değiştirir.
    Turu 20'de tam bu yolla HALT, ROLLBACK ve HEARTBEAT_STALE listede yoktu. Türetme unutkanlığı
    yapısal olarak imkânsız kılar; bu liste ise kapsamın KAZAYLA değişmesini yakalar.

    AUTHORITY_CHANGE 2026-07-27 kasıtlı kapsam kararı (10 → 11): bu test kazara kaymayı yakalar,
    kasıtlı değişiklik literali günceller. Literalin güncellenmesi kararın kaydıdır — güncellenmeden
    geçen bir suite, kapsamın kimsenin fark etmediği bir yoldan büyüdüğü anlamına gelirdi.

    GOAL_FAILURE 2026-07-30 kasıtlı kapsam kararı (11 → 12, K1 kopukluk turu): goal.yaml'ın
    `failure_below` hükmü tanımlandığı 2026-07-14'ten beri hiçbir kod tarafından ölçülmüyordu —
    deney başarısız olsa bunu söyleyecek tek satır yoktu (watchdog.goal_failure_report). Hüküm
    kendi sınıfıdır: DATA_QUALITY "veri bozuk", MECHANISM_STALE "mekanizma üretmiyor" der; ikisi de
    "mekanizma çalıştı, sonuç sözleşmenin başarısızlık eşiğinin altında" demez.

    NAKED_POSITION 2026-08-09 kasıtlı kapsam kararı (12 → 13, DALGA W1 / N1 jeton ayrımı, 5df1657):
    `watchdog.check_koruma_and_alarm` (v209) korumasız-pozisyon alarmını `MIRROR_DRIFT` jetonuyla
    basıyordu ve bunun BEDELİ o gün ölçülüp kendi docstring'ine yazılmıştı — `obs._maybe_notify`in
    6 saatlik susturma penceresi JETON BAŞINADIR, yani gürültülü bir mutabakat gecesinde ADET
    SAPMASI alarmları bu sev-1 alarmın TESLİMATINI bastırabiliyordu. İki olgu ayrı sınıftır: "ayna
    kitabın söylediği adette değil" bir MUHASEBE sapması, "pozisyonun broker'da canlı stop'u yok"
    bir SERMAYE riskidir; birincisi ikincisini susturamaz. Kapsam BÜYÜDÜ (yeni bir alarm sınıfı
    operatöre ulaşıyor), daralmadı; teslim zinciri değişmedi — `NOTIFY_TOKENS` türetmesi jetonu
    `obs.py`ye eklendiği an kendiliğinden kapsıyor. Bu literalin güncellenmesi o kararın kaydıdır.

    DISK_ESIK 2026-09-05 kasıtlı kapsam kararı (15 → 16, TSK-131 alt-iş): A1 /opt/veri (EDG-066
    tick geri dolumu) hiçbir sensörle izlenmiyordu. Operatörün 120 G tavanı (ROADMAP TSK-131,
    `deploy/oracle-a1/geridolum.py::TAVAN_BAYT` — tek kaynak) dolmadan 10 G ÖNCE haber veren
    `watchdog.check_veri_disk_and_alarm` bu jetonu basar. Kendi sınıfıdır: DATA_QUALITY "veri
    bozuk", MECHANISM_STALE "mekanizma üretmiyor" der; ikisi de "disk operatör tavanına
    yaklaşıyor" demez — bu bir KAPASİTE uyarısıdır. Kapsam BÜYÜDÜ, daralmadı; bu literal
    güncellemesi o kararın kaydıdır."""
    assert obs.NOTIFY_TOKENS == {
        "ARMING_READY", "TRAIL_DESYNC", "DATA_QUALITY", "CIRCUIT_BREAKER", "MIRROR_DRIFT",
        "BROKER_REJECT", "MECHANISM_STALE", "HALT_ACTIVE", "ROLLBACK", "HEARTBEAT_STALE",
        "AUTHORITY_CHANGE", "GOAL_FAILURE",
        # N1 (2026-08-09): korumasız pozisyon artık MIRROR_DRIFT'in susturma penceresini
        # PAYLAŞMIYOR — gerekçe yukarıda, davranışsal çivi
        # tests/test_dalga_w1_v216.py::test_N1_iki_alarm_ARTIK_AYNI_susturma_penceresini_paylasmaz
        "NAKED_POSITION",
        # İCRA-SÖZLEŞMESİ (2026-08-12, v233 — VLO vakası): onaylı plan broker'a gitmediyse bu
        # sermaye-sınıfı alarm split_brain gürültüsüne gömülmesin diye AYRI jeton; NOTIFY türetmesi
        # bildirime otomatik bağlar. Bu literal güncellemesi o kararın kaydıdır (`obs._maybe_notify` jeton-başına susturma gerekçesi).
        "ONAYLI_PLAN_GONDERILMEDI",
        # TESLİMAT SINIFI (2026-08-25, v313): `ARAMA_HAVUZU_OLU` kasıtlı kapsam kararıdır (14 → 15).
        # ÖLÇÜLEN BEDEL: arama havuzu 2026-08-12'den beri her atalet olayında `biten=0` döndü (61
        # olayın 61'i) ve öğrenme hattı 2026-08-21'den sonra SIFIR öneri üretti — ama olgu yalnız
        # `obs.warn` ile yazılıyordu ve `warn`ın kendi şerhi "alarm DEĞİLDİR: bildirim zincirini
        # tetiklemez" diyor. 61 kayıt, günde 8-9, operatörün gelen kutusuna HİÇ düşmedi.
        # NEDEN MECHANISM_STALE YETMEZ: o jeton CANLILIK ölçer ("iplik nabız atıyor mu"). v302
        # nabzı havuz bekleyişinin İÇİNDEN attırdı ve bunu DOĞRU yaptı — iplik gerçekten canlı.
        # Ama o düzeltme, kazara bu arızanın tek sesi olan yanıltıcı alarmı susturur. Doğru çözüm
        # sesi kısmak değil, YANLIŞ sinyali DOĞRUSUYLA değiştirmektir: "iplik canlı" (MECHANISM_STALE,
        # doğru) + "havuz iş bitirmiyor" (bu jeton, doğru). İkisi AYRI olgudur; biri ötekinin
        # yerine geçemez. Kapsam BÜYÜDÜ, daralmadı. Bu literal güncellemesi o kararın kaydıdır.
        "ARAMA_HAVUZU_OLU",
        # KAPASİTE SINIFI (2026-09-05, TSK-131 alt-iş): `DISK_ESIK` kasıtlı kapsam kararıdır
        # (15 → 16) — gerekçe yukarıda, üretici `watchdog.check_veri_disk_and_alarm`.
        "DISK_ESIK"}


def test_every_alarm_constant_reaches_the_operator_by_construction():
    consts = {v for k, v in vars(obs).items() if k.startswith("ALARM_") and isinstance(v, str)}
    assert consts == obs.NOTIFY_TOKENS, \
        "türetme kopmuş — bir ALARM_ sabiti bildirim kapsamının dışında kaldı"


def test_the_two_tokens_that_were_only_string_literals_now_have_constants():
    """Çağrı yerleri `obs.alarm("MECHANISM_STALE", ...)` düz metniyle çağırıyor; sabit yoksa
    türetme onları GÖREMEZ ve en sık üretilen iki alarm kapsam dışında kalırdı."""
    assert obs.ALARM_MECHANISM_STALE == "MECHANISM_STALE"
    assert obs.ALARM_ARMING_READY == "ARMING_READY"


# ---------------------------------------------------------------------------------------------
# 3) alarm_delivery muafiyeti
# ---------------------------------------------------------------------------------------------
def test_the_undelivered_backlog_never_alarms_through_the_same_channel(sandbox_state, monkeypatch):
    """KABUL EDİLEN DÖNGÜSELLİĞİN KALINTISI: `parity:alarm_delivery` alarmı, kanal yokken
    `notify_undelivered` sayacını +1 besliyordu — yani "teslim edilemedi" bulgusunun KENDİSİ
    ölçtüğü yığını büyütüyordu. Mandal defterine yapışsaydı, yığın ACK ile soğurulup satır yeşile
    döndükten sonra GERÇEKTEN yeniden biriktiğinde bir daha hiç alarm üretemezdi."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")          # satırın ÇIKMASI için yığın gerekli
    assert _row("alarm_delivery")["ok"] is False, "ön koşul: satır kırmızı olmalı"

    wd.check_integrity_and_alarm()

    latched = store.read_json("integrity_alarmed.json", [])
    assert "parity:alarm_delivery" not in latched, \
        "teslim boşluğu mandala yapıştı — yığın yeniden biriktiğinde bir daha hiç alarm veremez"
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "MAKULLÜK: alarm_delivery" not in blob, \
        "bulgu kendi saydığı sayacı besledi — döngüsellik geri geldi"


def test_the_exemption_does_not_silence_other_parity_rows(sandbox_state, monkeypatch):
    """MUAFİYET DAR OLMALI: kalkan tüm makullük satırlarını kapsasaydı dedektörün tamamı susardı."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    store.write_json("regime_edge.json", {"chop": {"n": 40, "avg_r": -0.5}})
    wd.check_integrity_and_alarm()
    assert "parity:measured_edge" in store.read_json("integrity_alarmed.json", [])


# ---------------------------------------------------------------------------------------------
# 4) ack_by tüketicisi
# ---------------------------------------------------------------------------------------------
def test_the_ack_owner_is_recorded_in_the_event_trail(sandbox_state, monkeypatch):
    """"Bu alarmları kim kapattı" sorusu cevapsız kalamaz: `ack_by` yazılıyor ama HİÇBİR yerde
    okunmuyordu — üretilip tüketilmeyen bir alan (yasa 6, alan düzeyinde)."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")
    with TestClient(app) as client:
        r = client.post("/api/alerts/ack")
    assert r.status_code == 200 and r.json()["ack_by"] == "operator"

    acked = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "alerts_acked"]
    assert acked and acked[-1].get("ack_by") == "operator", \
        f"ACK'in faili ize düşmedi: {acked[-1] if acked else None}"


def test_the_watchdog_row_shows_who_absorbed_the_backlog(sandbox_state, monkeypatch):
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")
    store.write_json(notify.ACK_FILE, {"ack_ts": "2099-01-01T00:00:00+00:00",
                                       "ack_by": "operator", "absorbed": 1})
    r = _row("alarm_delivery")
    assert r and "ack: operator@2099-01-01T00:00:00+00:00" in r["detail"], \
        f"kalıntıyı kimin düştüğü satırda görünmüyor: {r}"


def test_an_old_ack_file_without_an_owner_invents_none(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: alan yoksa 'operator' yazmak ölçülmemiş bir faili var etmek olurdu."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")
    store.write_json(notify.ACK_FILE, {"ack_ts": "2099-01-01T00:00:00+00:00", "absorbed": 1})
    assert "ack:" not in (_row("alarm_delivery") or {}).get("detail", "")


# ---------------------------------------------------------------------------------------------
# 5) beyin zinciri — ölçüm ARIZASI ile "hiç koşmadı" ayrı şeylerdir
# ---------------------------------------------------------------------------------------------
def _status(monkeypatch, chain: dict, availability: dict | None = None):
    from meridian import hermes_runtime as hr
    monkeypatch.setattr(hr, "status", lambda: {"brain_chain": chain,
                                               "brain_availability": availability or {}})


def test_a_failed_chain_measurement_is_reported_as_a_fact(sandbox_state, monkeypatch):
    """`hermes` import'u düşerse hesap `{}` dönüyordu ve bekçinin `if _ch:` kapısı onu tamamen
    düşürüyordu: yedeklilik denetimi SESSİZCE kayboluyordu. Dedektörün öldüğü an, tam da hiçbir
    şeyin duyulmadığı andır."""
    from meridian import hermes, hermes_runtime as hr

    def _bom(*a, **k):
        raise ImportError("hermes yok")

    monkeypatch.setattr(hermes, "brain_chain_facts", _bom)
    monkeypatch.setattr(hermes, "brain_availability", _bom)
    assert hr._brain_chain() == {"error": "ImportError"}, "arıza yine boş sözlüğe çevrildi"
    assert hr._brain_availability() == {"error": "ImportError"}

    _status(monkeypatch, hr._brain_chain(), hr._brain_availability())
    rc, ra = _row("brain_chain_distinct"), _row("brain_availability")
    assert rc and rc["ok"] is False and "ölçümü ÇALIŞMADI" in rc["detail"] and "ImportError" in rc["detail"]
    assert ra and ra["ok"] is False and "ölçümü ÇALIŞMADI" in ra["detail"]


def test_a_fresh_sandbox_where_hermes_never_ran_stays_silent(sandbox_state, monkeypatch):
    """TABAN TEMİZLİĞİ — TASARIMIN ÖZÜ: ölçülecek bir şeyin HİÇ olmaması bir arıza değildir.
    Taze bir kurulumda kırmızı basmak kurt masalıdır ve kirli bir temelde her mutasyon 'yakalandı'
    görünür — kapsama sayısı yalan söyler (mutation.py bunu haklı olarak reddediyor)."""
    _status(monkeypatch, {}, {})
    assert _row("brain_chain_distinct") is None and _row("brain_availability") is None


def test_a_measured_chain_still_reports_normally(sandbox_state, monkeypatch):
    """Hata dalı, ÖLÇÜLEN dalı gölgelemez: `error` yoksa satır eskisi gibi konuşur."""
    _status(monkeypatch, {"order": ["nous", "gemini"], "ready": ["nous", "gemini"],
                          "models": {"nous": "gemini-3.5-flash", "gemini": "gemini-3.5-flash"},
                          "same_model_ids": [["gemini", "nous"]],
                          "nous_mode": "portal", "agent_config_provider": None},
            {"nous": {"ready": True}, "gemini": {"ready": False, "credentials": True}})
    rc = _row("brain_chain_distinct")
    assert rc and rc["ok"] is False and "AYNI model kimliğiyle" in rc["detail"]
    assert _row("brain_availability")["detail"].startswith("hazır sağlayıcı: nous")


# ---------------------------------------------------------------------------------------------
# 6) _HEALTH testler arası sızmaz
# ---------------------------------------------------------------------------------------------
_HEALTH_FRESH = {"ok": None, "calls": 0, "fails": 0, "last_status": None, "last_error": "",
                 "at": None, "last_key": None, "last_body": ""}


def test_fmp_health_is_reset_between_tests_without_breaking_identity():
    """SIZINTI: mock 429 kullanan bir test `ok=False, calls>0` bırakınca SONRAKİ watchdog testi
    kendi kurmadığı bir 'fmp_source starved' bulgusu görüyordu — o an dedektör değil, sıra
    ölçülüyordu. Sıfırlama YERİNDE olmalı: yeni bir dict atamak modül referanslarını koparır ve
    reset hiçbir şeye dokunmamış olurdu."""
    from meridian.adapters import fmp as _fmp
    from tests.conftest import _clear_module_caches

    same_object = _fmp._HEALTH
    _fmp._HEALTH.update({"ok": False, "calls": 7, "fails": 7, "last_status": 429,
                         "last_error": "quota", "last_key": "FMP_API_KEY_2"})
    _clear_module_caches()
    assert _fmp._HEALTH == _HEALTH_FRESH, f"sağlık kaydı sızdı: {_fmp._HEALTH}"
    assert _fmp._HEALTH is same_object, \
        "sıfırlama yeni bir dict atadı — modül referansları koptu, reset hiçbir şey yapmıyor"


def test_the_reset_literal_matches_production():
    """Literal ÜRETİMDEN doğrulanır, elle kopyalanmaz: alan eklenip burada unutulursa sızıntı
    o alan üzerinden geri gelirdi."""
    import inspect
    import meridian.adapters.fmp as _fmp
    src = inspect.getsource(_fmp)
    # ÇAPA GÜNCELLENDİ (2026-08-25, v291): `QUOTA_COOLDOWN_S` sabiti EMEKLİ edildi (kota bloğu artık
    # saatlik bir sabit değil, sağlayıcının günlük sıfırlaması — `fmp._blok_bitisi`). Eski çapa
    # kaybolunca `split` tüm kaynağı döndürüyor ve bu çivi hiçbir şey ölçmeden yeşil geçerdi;
    # yeni çapa AYNI bölgeyi (`_HEALTH` literalinin hemen ardı) işaret eder.
    _capa = "_blok_bitisi"
    assert _capa in src, "çapa üretimden kayboldu — bu çivi sessiz-yeşile düşer"
    for k in _HEALTH_FRESH:
        assert f'"{k}"' in src.split(_capa)[0], f"_HEALTH alanı {k} üretimde yok"
    assert set(_HEALTH_FRESH) == set(_fmp.health()), \
        "reset literali üretimdeki _HEALTH şemasıyla ayrıştı"


# ---------------------------------------------------------------------------------------------
# 7) news — yutma artık kayıtlı
# ---------------------------------------------------------------------------------------------
def test_news_sessiz_yutma_dersi_emeklilikte_de_korunuyor():
    """DEVİR (2026-07-30 temizlik turu): #7'nin öznesi "news.stock_news" [çapa-mezar-taşı] EMEKLİ edildi — modülün
    ÜRETİM tüketicisi 2026-07-21'den beri yoktu ve dokuz gün sonra da yoktu (hedef sözleşmesi md.1).

    #7'nin BULGUSU emekli EDİLMEDİ. Bulgu şuydu: `[]` dönmek DOĞRU davranıştır (çağıran boş akışla
    yaşayabilir) ama SESSİZ olması değil — 'haber yok' ile 'haber ALINAMADI' aynı görünüyordu.
    Haber katmanı bir gün geri kurulursa aynı tuzağa düşmemek için ders mezar taşında yazılı; bu
    test onun silinmediğini çiviler. Davranış çivisi `tests/test_macro_news_audit_v20.py`de."""
    import inspect
    from meridian.adapters import news

    assert not hasattr(news, "stock_news"), "emeklilik yarım — ad hâlâ var"
    d = inspect.getdoc(news) or ""
    assert "HABER ALINAMADI" in d and "news_fetch_failed" in d, \
        "#7'nin dersi (sessiz yutma yasağı) emeklilikle birlikte kaybolmuş"
