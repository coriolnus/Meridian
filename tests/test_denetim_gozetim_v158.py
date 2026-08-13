"""test_denetim_gozetim_v158.py — GÖZETİM + ZAMANLAYICI denetim düzeltmeleri (2026-08-02).

`docs/SISTEM-DENETIMI-2026-08-02.md` kümesi: C2, C6, C7, C21, C22. Beşi de aynı aileden —
**bir dedektör ya da kadans, ölçemediği/göremediği şeyi "temiz" sayıyor**:

- C6 korunum penceresi SATIR limitliydi (8000/20000): 27k satırlık canlı defterde K1'in
  BROKER_REJECT düzeltmesi pencerenin DIŞINDA kaldı, yani ÖLÜYDÜ; `live_start` de pencereden
  hesaplandığı için canlı dönem 12 gün geç başlıyor, aradaki her sızıntı `replay_era`ya düşüyordu.
- C7 kanal BAĞLIYKEN düşen teslimat hiçbir sayaca girmiyordu — `alarm_delivery` ve `notify_channel`
  satırları yeşilken operatöre tek bir alarm ulaşmamış olabilirdi.
- C21 `integrity_report` persist'li üçlüyü parity'den ÖNCE değerliyordu: parity fırlarsa alarm
  katmanı hiç koşmuyor, ama YENİ TABAN çoktan yazılmış oluyordu → o turun gerilemesi KALICI kayıp.
- C22 bar dizini okunamayınca `ok=True` dönüyordu (fail-open) ve tek satır bile kayıt düşmüyordu.
- C2 seans takvimi düşerse TÜM seans-sonrası kadans SESSİZCE duruyordu.

Bu dosya yalnız HATA YOLLARINI sürer: mutlu yol akranlarının testlerinde (test_integrity_v15,
test_alarm_delivery_v71, test_kopukluk_kapatma_v122) zaten çivili ve orada kalmalı.
"""
from __future__ import annotations

import datetime as dt
import sys

import pytest

from meridian import config, notify, obs, store, watchdog as wd


# =================================================================================================
# Yardımcılar
# =================================================================================================
def _bugun() -> dt.date:
    return dt.date.today()


def _gurultu(n: int) -> list[dict]:
    """Damgasız gürültü satırı: `events_since` damgasızları pencerede TUTAR (ölçülemeyeni yok
    saymaz), yani bu satırlar pencere GENİŞLİĞİNİ değil yalnız SATIR SAYISINI sınar — C6'nın
    ölçtüğü şey tam olarak budur."""
    return [{"level": "info", "event": "hotstate_down", "error": "ConnectionError"} for _ in range(n)]


def _parity_satiri(ad: str):
    return next((r for r in wd.parity_report()["rows"] if r["check"] == ad), None)


@pytest.fixture
def yakala_uyari(monkeypatch):
    """obs.warn/obs.alarm çağrılarını topla (defterin kendisine değil ÇAĞRIYA bakarız: uyarının
    varlığı sözleşme, biçimi değil)."""
    uyarilar: list[tuple[str, dict]] = []
    alarmlar: list[tuple[str, str, dict]] = []
    _w, _a = obs.warn, obs.alarm

    def _warn(event, **f):
        uyarilar.append((event, f))
        return _w(event, **f)

    def _alarm(token, message, **f):
        alarmlar.append((token, message, f))
        return _a(token, message, **f)

    monkeypatch.setattr(obs, "warn", _warn)
    monkeypatch.setattr(obs, "alarm", _alarm)
    return uyarilar, alarmlar


# =================================================================================================
# C6 — KORUNUM PENCERESİ SATIR DEĞİL TARİH TABANLI
# =================================================================================================
def test_C6_broker_reddi_8000_SATIRIN_otesinde_de_gorulur(sandbox_state):
    """CANLI VAKA: `plan_id` taşıyan 4 BROKER_REJECT olayı defterin sonundan 15-19 bin satır
    geride duruyordu; `limit=8000` penceresi onları GÖREMİYOR ve K1'in düzeltmesi üretimde ÖLÜ
    kalıyordu (dropped=0 → unexplained=10; tam defterle dropped=4 → unexplained=6).

    Kurulum: reddi defterin BAŞINA koy, üstüne 9000 gürültü satırı yığ. Doğru davranış: plan
    AÇIKLANMIŞ sayılır."""
    pid = "P-2026-07-23-UNP"
    plan_gun = str(_bugun() - dt.timedelta(days=5))
    store.write_json("portfolio.json", {"last_date": str(_bugun())})
    store.write_jsonl("trade_plans.jsonl", [
        {"id": pid, "date": plan_gun, "ticker": "UNP", "gate_verdict": "GO"}])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    defter = ([{"level": "info", "event": "daily_cycle", "date": str(_bugun() - dt.timedelta(days=20))},
               {"level": "alarm", "event": "BROKER_REJECT Alpaca reddi: UNP",
                "alarm": "BROKER_REJECT", "plan_id": pid}]
              + _gurultu(9000))
    store.write_jsonl("events.jsonl", defter)

    # ÖN KOŞUL: kurulum gerçekten eski pencerenin DIŞINDA (aksi hâlde test hiçbir şey kanıtlamaz)
    assert len(defter) > 8000 and defter[8000 - 1].get("alarm") != "BROKER_REJECT", \
        "kurulum 8000 satırlık pencerenin içinde kalmış — regresyon testi kör"

    rep = wd.conservation_report()
    assert rep["unexplained"] == 0, \
        f"broker reddi satır penceresinin dışında kaldığı için AÇIKLANAMAYAN sayıldı (rapor: {rep})"
    assert rep["ok"] is True


def test_C6_live_start_defterin_TAMAMINDAN_okunur_penceresinden_DEGIL(sandbox_state):
    """İKİNCİ YÜZ: `live_start` 20000 satırlık pencerenin İLK daily_cycle'ıydı — canlı defterde
    2026-07-22 çıkıyordu, GERÇEK ilk daily_cycle ise 2026-07-10'du. Aradaki 12 günde açıklanamayan
    her plan `replay_era` ("körlük, sızıntı değil") sayılıp sessizce düşüyordu; docstring'in tek
    gerçek bulgusu olarak andığı GS 07-14 sızıntısı tam bu yoldan yutulurdu.

    Kurulum: GERÇEK sınır defterin BAŞINDA, sahte sınır 20000 satır SONRA. Plan ikisinin ARASINDA."""
    store.write_json("portfolio.json", {"last_date": "2026-07-31"})
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-2026-07-14-GS", "date": "2026-07-14", "ticker": "GS", "gate_verdict": "GO"}])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    defter = ([{"level": "info", "event": "daily_cycle", "date": "2026-07-10"}]   # GERÇEK sınır
              + _gurultu(20000)
              + [{"level": "info", "event": "daily_cycle", "date": "2026-07-22"}])  # pencerenin ilki
    store.write_jsonl("events.jsonl", defter)
    assert len(defter) > 20000, "kurulum 20000 satırlık pencereyi zorlamıyor — test kör"

    rep = wd.conservation_report()
    assert rep["live_start"] == "2026-07-10", \
        f"canlı dönem sınırı hâlâ satır penceresinden okunuyor (live_start={rep['live_start']!r})"
    assert rep["replay_era"] == 0, "canlı dönem sızıntısı replay körlüğü sayıldı"
    assert rep["unexplained"] == 1 and rep["rows"][0]["ticker"] == "GS"


def test_C6_satir_limitli_okuma_korunum_raporuna_GERI_DONMEDI():
    """Sınıfın nüksetmemesi: `conservation_report` gövdesinde `events.jsonl` için satır limitli
    okuma DURMAMALI. (Yorumlar düşürülür — beyan değil KOD ölçülür.)"""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "watchdog.py").read_text()
    govde = src.split("def conservation_report")[1].split("\nFINGERPRINT_FILE")[0]
    kod = "\n".join(ln.split("#", 1)[0] for ln in govde.splitlines())
    assert 'read_jsonl("events.jsonl"' not in kod, \
        "korunum raporu olay defterini yine doğrudan/limitli okuyor — pencere körlüğü geri döndü"
    assert "events_since(" in kod, "tarih tabanlı pencere kullanılmıyor"


# =================================================================================================
# C7 — KANAL BAĞLIYKEN DÜŞEN TESLİMAT SAYILIR
# =================================================================================================
def test_C7_kanal_BAGLIYKEN_dusen_teslimat_sayaca_girer(sandbox_state, monkeypatch):
    """`notify.send` False dönerse hiçbir sayaç artmıyor, hiçbir artefakt yazılmıyordu. "Kanal yok"
    ölçülüyor, "kanal var ama cevap vermiyor" ölçülmüyordu."""
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: False)          # uzak uç cevap vermiyor
    obs.alarm("MECHANISM_STALE", "mekanizma gecikti")
    obs.alarm("DATA_QUALITY", "veri kapısı")

    d = store.read_json("notify_undelivered.json", {})
    assert d.get("_toplam") == 2, f"teslim edilemeyen alarm sayılmadı (dosya: {d})"
    assert d.get("_teslim_hatasi") == 2, "teslim HATASI 'kanal yok' yığınından ayrılmıyor"
    assert d.get("MECHANISM_STALE") == 1 and d.get("DATA_QUALITY") == 1, "jeton kırılımı yok"


def test_C7_basarisiz_teslimat_susturma_penceresi_KURMAZ(sandbox_state, monkeypatch):
    """Başarısız bir deneme `notify_sent.json` yazsaydı kanalı 6 saat susturur ve alarm gerçekten
    kaybolurdu — mevcut davranış korunmalı."""
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: False)
    obs.alarm("MECHANISM_STALE", "x")
    assert store.read_json("notify_sent.json", None) in (None, {}), \
        "başarısız teslimat susturma penceresi kurdu — sonraki 6 saat sessizlik"


def test_C7_alarm_delivery_satiri_teslim_hatasini_ADIYLA_anlatir(sandbox_state, monkeypatch):
    """YANLIŞ-YEŞİL DEĞİL, DOĞRU-KIRMIZI: satır artık "kanal bağlı ama uzak uç cevap vermiyor"
    hâlini görüyor. Eski metin bu yığın için "bu yığın kanal YOKKEN toplandı" diyordu — kanal
    bağlıyken düşen teslimatlar için bu bir UYDURMAdır ve yanlış teşhis yanlış müdahaleyi doğurur."""
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: False)
    obs.alarm("MECHANISM_STALE", "x")

    r = _parity_satiri("alarm_delivery")
    assert r is not None and r["ok"] is False, "teslim edilemeyen alarm varken satır yeşil/kayıp"
    assert "BAĞLIYKEN teslim EDİLEMEDİ" in r["detail"], f"metin yığını yanlış anlatıyor: {r['detail']}"
    assert "kanal YOKKEN toplandı" not in r["detail"]


def test_C7_basarili_teslimat_sayac_URETMEZ(sandbox_state, monkeypatch):
    """KURT MASALI YASAĞI: teslimat başarılıysa hiçbir sayaç artmamalı."""
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: True)
    obs.alarm("MECHANISM_STALE", "x")
    assert store.read_json("notify_undelivered.json", {}) == {}
    assert _parity_satiri("alarm_delivery") is None


# =================================================================================================
# C21 — DEĞERLEME SIRASI + DEDEKTÖR-BAŞINA YALITIM
# =================================================================================================
def test_C21_parity_persistli_UCLUDEN_once_degerlenir(sandbox_state, monkeypatch):
    """SIRA SÖZLEŞMESİ: parity fırlarsa persist'li üçlü TABANI YAZMAMIŞ olmalı. Eski sırada
    determinism/monotonicity/ownership tabanı diske yazdıktan SONRA parity çağrılıyordu; parity
    fırlayınca alarm katmanı hiç koşmuyor ama yeni taban duruyordu → o turun gerilemesi bir sonraki
    turda prev==cur olduğu için SONSUZA DEK kayboluyordu.

    `_tut` yalnız `Exception` yakalar; sıra sözleşmesini yakalanMAYAN bir düşüşle sürüyoruz —
    böylece ölçülen şey yalıtım değil, saf DEĞERLEME SIRASI olur."""
    (config.BARS / "aaa.csv").write_text("date,close\n2024-01-02,1\n")

    def _patla():
        raise KeyboardInterrupt("parity düştü")

    monkeypatch.setattr(wd, "parity_report", _patla)
    with pytest.raises(KeyboardInterrupt):
        wd.integrity_report(persist=True)

    assert store.read_json(wd.FINGERPRINT_FILE, None) is None, \
        "parity düşmesine rağmen determinizm TABANI yazıldı — gerileme yeni tabana emilirdi"
    assert store.read_json(wd.MONOTONIC_FILE, None) is None, "monotonluk tabanı yazıldı"
    assert store.read_json(wd.OWNERSHIP_FILE, None) is None, "sahiplik tabanı yazıldı"


def test_C21_dusen_dedektor_digerlerini_GOTURMEZ(sandbox_state, monkeypatch):
    """YALITIM: bir dedektör fırlarsa rapor ölmez; o dedektör `ok=False` + `error` döner, diğerleri
    hükmünü verir. Şekil sözleşmesi (7 desen) korunur."""
    def _patla():
        raise ValueError("defter okunamadı")

    monkeypatch.setattr(wd, "conservation_report", _patla)
    rep = wd.integrity_report(persist=True)

    # 8. DESEN BEYANLI EKLENDİ (2026-08-13): `divergence` — DEĞER eşitliği dedektörü.
    assert {"production", "conservation", "determinism", "coherence",
            "monotonicity", "ownership", "parity", "divergence"} == set(rep), \
        "şekil sözleşmesi bozuldu"
    kons = rep["conservation"]
    assert kons["ok"] is False and kons["dedektor_dustu"] is True
    assert "ValueError" in kons["error"] and "defter okunamadı" in kons["error"]
    # İSKELET: tüketiciler alt alanları indeksliyor — yalıtım çağıranda KeyError'a dönüşmemeli
    assert kons["unexplained"] == 0 and kons["rows"] == []
    # AKRANLAR KOŞTU
    assert "starved" in rep["production"] and "rows" in rep["parity"]
    assert not rep["production"].get("dedektor_dustu")


def test_C21_dusen_dedektor_ADIYLA_alarmlanir(sandbox_state, monkeypatch, yakala_uyari):
    """Yalıtım tek başına SESSİZLİK üretmemeli: "ölçemedim" de bir hükümdür. Eskiden parity
    fırladığında `check_integrity_and_alarm` hiçbir alarm üretmeden düşüyor ve
    `integrity_alarmed.json` hiç yazılmıyordu."""
    uyarilar, alarmlar = yakala_uyari

    def _patla():
        raise RuntimeError("parity yüzeyi düştü")

    monkeypatch.setattr(wd, "parity_report", _patla)
    wd.check_integrity_and_alarm()

    assert any(e == "integrity_detector_failed" and f.get("detector") == "parity"
               for e, f in uyarilar), "düşen dedektör uyarı bile üretmedi"
    assert any(f.get("kind") == "detector_failed" and f.get("detector") == "parity"
               for _, _, f in alarmlar), "düşen dedektör ALARM üretmedi"
    assert "detector_failed:parity" in set(store.read_json("integrity_alarmed.json", [])), \
        "mandal defteri yazılmadı — sonraki turda tekrar alarmlanır (gürültü) ya da hiç yazılmaz"


def test_C21_parity_dususu_o_turun_GERILEMESINI_kaybettirmez(sandbox_state, monkeypatch):
    """KUSURUN ÖZÜ: parity fırladığında alarm katmanı ölüyordu, ama taban çoktan ilerlemişti — o
    turda gerçekleşen bar küçülmesi bir sonraki turda prev==cur olduğu için görülemez oluyordu.
    Yalıtımdan sonra: parity düşse de gerileme AYNI TURDA alarmlanır."""
    fired: list[tuple[str, dict]] = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: fired.append((msg, kw)))
    (config.BARS / "aaa.csv").write_text("date,open,high,low,close,volume\n2024-01-02,1,1,1,1,1\n")
    store.write_json("wf_cache_rev.json", {"rev": 3})
    wd.determinism_report(persist=True)                      # TABAN: küçülme ÖNCESİ
    (config.BARS / "aaa.csv").write_text("date,o\n1,2\n")     # GEÇMİŞ yeniden yazıldı, rev SABİT

    def _patla():
        raise RuntimeError("parity yüzeyi düştü")

    monkeypatch.setattr(wd, "parity_report", _patla)
    wd.check_integrity_and_alarm()

    assert any(kw.get("kind") == "determinism" for _, kw in fired), \
        "parity düşmesi sessiz bar mutasyonu alarmını da götürdü — gerileme kalıcı olarak kayboldu"


def test_C21_tek_sahip_yorumu_mutation_gercegiyle_DUZELTILDI():
    """Yorum-davranış sürüklenmesi: ":1053 'taban YALNIZ burada ilerler (tek sahip)'" diyordu, oysa
    `mutation.py` de `integrity_report(persist=True)` çağırıyor (farkı yönlendirme: geçici kopyaya
    yazar). Yorum, okuyanı yanlış bir tekile inandırmamalı."""
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent
    src = (kok / "meridian" / "watchdog.py").read_text()
    assert "(tek sahip)" not in src, "düzeltilmemiş 'tek sahip' iddiası hâlâ duruyor"
    assert "canlı tabanın tek yazarı" in src and "mutation.py" in src, \
        "düzeltilmiş yorum mutation.py gerçeğini adlandırmıyor"
    assert "integrity_report(persist=True)" in (kok / "meridian" / "mutation.py").read_text(), \
        "yorumun dayandığı olgu değişmiş — yorum yeniden ölçülmeli"


# =================================================================================================
# C22 — DETERMİNİZM RAPORU FAIL-CLOSED
# =================================================================================================
class _OkunamazDizin:
    """`stat()`/`glob()` gerçek bir G/Ç-izin arızasında fırlatır (A1'de blok-birim hıçkırığı, bozuk
    sembolik bağ). `Path.glob` olmayan dizinde fırlatMAdığı için senaryo ancak böyle kurulur."""

    def glob(self, desen):
        raise PermissionError(f"izin reddedildi: {desen}")


def test_C22_okunamaz_bar_dizini_ok_FALSE_doner_ve_uyari_basar(sandbox_state, monkeypatch,
                                                               yakala_uyari):
    """FAIL-OPEN → FAIL-CLOSED. Eski dönüş `{"ok": True, "detail": "kontrol atlandı"}` idi ve
    `detail`i okuyan TEK bir tüketici yoktu: üç tüketicinin (alarm katmanı, mutation.py, pano)
    üçü de yalnız `ok`a bakar — yani ÖLÇÜLEMEYEN bir hüküm "temiz" kılığında yeşile boyanıyordu."""
    uyarilar, _ = yakala_uyari
    monkeypatch.setattr(config, "BARS", _OkunamazDizin())

    rep = wd.determinism_report(persist=True)
    assert rep["ok"] is False, "okunamayan bar dizini hâlâ 'temiz' sayılıyor (fail-open)"
    assert rep["olculemedi"] is True, "makine-okunur 'ölçülemedi' bayrağı yok"
    assert "PermissionError" in rep["error"]
    assert any(e == "determinism_bars_unreadable" for e, _ in uyarilar), \
        "olay defterine tek satır bile geçmedi — işaretin gerekçesi yine gerçeğe aykırı olurdu"


def test_C22_olculemedi_dalinda_TABAN_ILERLEMEZ(sandbox_state, monkeypatch):
    """Kanıt yok olmasın: erken dönüş taban yazımından ÖNCEDİR — küçülmüş bar dosyası küçük kalır
    ve bir sonraki BAŞARILI çağrı aynı bozulmamış tabana karşı kıyaslayıp alarmı üretir."""
    monkeypatch.setattr(config, "BARS", _OkunamazDizin())
    wd.determinism_report(persist=True)
    assert store.read_json(wd.FINGERPRINT_FILE, None) is None, \
        "ölçülemeyen turda taban yazıldı — kanıt kayboldu"


def test_C22_alarm_metni_olcumu_IHLAL_diye_adlandirmaz(sandbox_state, monkeypatch, yakala_uyari):
    """UYDURMA YASAĞI: "ölçemedim" ile "sessiz bar mutasyonu buldum" ayrı hükümlerdir. Jeton da
    AYRIDIR — ölçüm geri geldiğinde gerçek bir mutasyon kendi jetonuyla yeniden alarmlanabilsin."""
    _, alarmlar = yakala_uyari
    monkeypatch.setattr(config, "BARS", _OkunamazDizin())

    wd.check_integrity_and_alarm()

    det = [(m, f) for _, m, f in alarmlar if f.get("kind") == "determinism"]
    assert det, "ölçülemeyen determinizm hükmü hiç alarmlanmadı (fail-open geri döndü)"
    mesaj, alanlar = det[0]
    assert "ÖLÇÜLEMEDİ" in mesaj and "SESSİZ BAR MUTASYONU" not in mesaj, \
        f"ölçülemeyen hüküm ihlal diye adlandırıldı: {mesaj}"
    assert alanlar.get("olculemedi") is True
    mandal = set(store.read_json("integrity_alarmed.json", []))
    assert "determinism_unmeasured" in mandal and "determinism" not in mandal


# =================================================================================================
# C2 — SEANS TAKVİMİ DÜŞÜŞÜ: SÜREÇ BAŞINA BİR UYARI
# =================================================================================================
@pytest.fixture
def takvimsiz(monkeypatch):
    """`import pandas_market_calendars` başarısız olsun (sys.modules'a None koymak ImportError
    ürettirir) ve süreç-başına bayrak SIFIRLANSIN — bayrak modül düzeyindedir, testler arası
    sızarsa ikinci test hiçbir şey kanıtlamaz."""
    from meridian import scheduler
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", None)
    monkeypatch.setattr(scheduler, "_CALENDAR_WARNED", False)
    return scheduler


def test_C2_takvim_dususu_artik_SESSIZ_degil(sandbox_state, takvimsiz, yakala_uyari):
    """KUSUR: takvim düşerse `last_closed=None` → `_dense`/`_chasing` False → `fresh` KALICI False
    → terminal atlama, merdiven adım-1, onarım/sip düzeltici, aynı-akşam bacağı, earnings, arming,
    selfreview, yetim süpürme, nous_eval, öğrenme kadansı, Y4, haftalık üçlü, skill revizyonu ve
    crosscheck — TÜM seans-sonrası kadans — tek uyarı bile düşmeden durur. Kardeş `_leg_ready` bu
    boşluğu kapatmaz: `if not session: return None` ile try'a hiç girmez."""
    uyarilar, _ = yakala_uyari
    assert takvimsiz._last_closed_session() is None, "ön koşul: takvim gerçekten düşmüyor"
    kayit = [f for e, f in uyarilar if e == "session_calendar_unavailable"]
    assert len(kayit) == 1, f"takvim düşüşü sessiz yutuldu (uyarılar: {[e for e, _ in uyarilar]})"
    assert "ModuleNotFoundError" in str(kayit[0].get("error")), "hata sınıfı kaydedilmemiş"


def test_C2_uyari_SUREC_BASINA_BIR_kez_basilir(sandbox_state, takvimsiz, yakala_uyari):
    """Bu yol her poll'de (300 sn) çalışır: koşulsuz uyarı 288 satır/gün üretir ve olay defterini —
    gelen kutusunun ve tüm makullük dedektörlerinin okuduğu kaynağı — boğardı. Gürültüye karşı
    kurulan mekanizma gürültü üretemez."""
    uyarilar, _ = yakala_uyari
    for _ in range(5):
        assert takvimsiz._last_closed_session() is None
    kayit = [f for e, f in uyarilar if e == "session_calendar_unavailable"]
    assert len(kayit) == 1, f"5 çağrıda {len(kayit)} uyarı — tekrar-uyarı spam'i geri döndü"


def test_C2_eski_sablon_gerekcesi_KALDIRILDI():
    """Eski işaretin gerekçesi ("asıl karar bu değere bağlı DEĞİL ... yedek değerle karşılıyor")
    repoda 13 yerde harfi harfine tekrarlanan bir ŞABLON damgaydı ve burada GERÇEĞE AYKIRIYDI:
    yedek değer yok, karar tamamen bu değere bağlı. `codelaw.MARKER_RE` yalnız gerekçenin
    VARLIĞINI ölçer, doğruluğunu değil — o yüzden bu satır elle çivilenir."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "scheduler.py").read_text()
    govde = src.split("def _last_closed_session")[1].split("\ndef ")[0]
    assert "sessiz-yutma" not in govde, \
        "takvim düşüşü yine sessiz-yutma olarak işaretli — uyarı basan bir dal sessiz DEĞİLDİR"
    assert "session_calendar_unavailable" in govde
