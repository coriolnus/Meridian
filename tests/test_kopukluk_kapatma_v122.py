"""test_kopukluk_kapatma_v122 — K1 KOPUKLUK KAPATMA TURU (2026-07-30).

Bu dosya, 8 kesit/40 bulguluk kopukluk denetiminin ONARIMLARINI çiviler. Kapsanan sınıflar ve her
birinin NEDEN bir test hak ettiği:

  A) BEYAN vs ÇAĞRI — `codelaw` bir okuyucunun VAR olduğuna bakar, ÇAĞRILDIĞINA bakamaz. Beyan
     alarmı susturur ama zinciri bağlamaz (`massive_crosscheck.json` → crosscheck_report()).
  B) İMZA KAYMASI — bir olay `warn`dan `alarm`a yükseltilince olay ADI değişir ve o adı bekleyen
     her süzgeç SESSİZCE hiçbir şey bulamaz. `failed_broker_rejection` tam bu tuzaktı: watchdog
     hiç yayınlanmayan bir olay adını bekliyordu ve canlıdaki 4 broker reddi "açıklanamayan"
     sayılıyordu. Bu yüzden yükseltilen olaylar makine-okunur adı `kind` alanında taşır.
  C) PENCERE KÖRLÜĞÜ — satır-limitli okuyucular, tek bir olayın seli altında gördüklerini sandıkları
     tarihi görmez. Canlı kanıt: defterin %60'ı `hotstate_down`, pencere 7 günden ~16 saate düştü.
  D) SÖZLEŞMESİZ DEFTER / ÖLÇÜLMEYEN HÜKÜM — goal.yaml'ın `failure_below` hükmü 16 gün boyunca
     hiçbir kod tarafından okunmadı; iki intraday defteri sözleşme yasasının tamamen dışındaydı.
  E) DEDEKTÖRÜN KÖR KESİTİ — orphan taraması yalnız `state/*.json*` geziyordu; kök artefaktlar,
     başka uzantılar ve DİZİNLER görüş alanının dışındaydı (11 MB'lık yedek dizini böyle birikti).

HİÇBİR TEST CANLI `state/`E YAZMAZ: hepsi `sandbox_state` fikstürüyle koşar (canlı worker koşuyor).
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from meridian import store


# =================================================================================================
# A) BEYAN vs ÇAĞRI — beyan edilen okuyucu ÜRETİMDE gerçekten çağrılıyor mu?
# =================================================================================================
def test_massive_crosscheck_beyan_edilen_okuyucu_uretimde_CAGRILIYOR():
    """`codelaw.DECLARED_SINKS` massive_crosscheck.json'u "adapters.data.crosscheck_report() okur"
    diye aklıyordu; ama üretimde o fonksiyonun TEK çağıranı testlerdi (meridian/ içinde sıfır).
    Yasa okuyucunun VAR olduğuna bakar, ÇAĞRILDIĞINA bakamaz — beyan alarmı susturmuş ama zinciri
    bağlamamıştı (`learning_loop_open` emsalinin birebir tekrarı).

    Bu test statik olarak api.py'de gerçek bir çağrı arar: metinde adının GEÇMESİ yetmez, çağrı
    parantezi aranır. Aksi hâlde bu testi bir yorum satırı bile geçirirdi."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py").read_text()
    # Yorumları at: bir dosya adını ANMAK onu okumak değildir (aynı ders orphan taramasında da var).
    kod = "\n".join(ln.split("#", 1)[0] for ln in src.splitlines())
    assert "crosscheck_report()" in kod, \
        "massive_crosscheck.json'un beyan edilen okuyucusu api.py'den ÇAĞRILMIYOR — beyan yine boş"


def test_diagnostics_massive_crosscheck_alanini_servis_eder(sandbox_state):
    """Zincirin uç noktası: pano yükünde alan GERÇEKTEN var mı (YASA 6'nın dış tüketicisi)."""
    from meridian.adapters import data
    rep = data.crosscheck_report()
    # `index_crosscheck.json` (endeks düzeyi) ile KARIŞTIRILMAMALI: iki ayrı gerçek, iki ayrı anahtar.
    assert {"tickers", "compared", "mismatches", "tol_pct"} <= set(rep)


def test_uyusmazlik_DATA_QUALITY_alarmi_ve_makine_okunur_ad_tasir(sandbox_state, monkeypatch):
    """Uyuşmazlık olayının kendi metni ilk günden "v1'de ALARM" diyordu ama seviye `warn`dı — ve
    notify.py alarm-olmayan her satırı eler, yani bildirim zincirine HİÇ giremiyordu.

    İKİ ŞEY BİRDEN çivilenir: (1) seviye alarm ve jeton DATA_QUALITY, (2) makine-okunur ad `kind`
    alanında YAŞIYOR. İkincisi olmadan onarım yeni bir kopukluk üretirdi: obs.alarm olay adını
    "DATA_QUALITY <mesaj>"a çevirir, dolayısıyla `event == "bar_kaynak_uyusmazligi"` süzgeci artık
    tutmaz — `failed_broker_rejection` tuzağının aynısı."""
    from meridian import obs
    from meridian.adapters import data
    fired = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: fired.append((tok, msg, f)))
    # Ölçüm yolunu doğrudan sürmek yerine sözleşmeyi kontrol ediyoruz: kaynakta alarm çağrısı ve
    # `kind` alanı var mı. (Tam fetch yolu ağ/sağlayıcı stub'ları gerektirir; onu v118 zaten sürüyor.)
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "meridian" / "adapters" / "data.py").read_text()
    kod = "\n".join(ln.split("#", 1)[0] for ln in src.splitlines())
    assert "ALARM_DATA_QUALITY" in kod and 'kind="bar_kaynak_uyusmazligi"' in kod, \
        "uyuşmazlık ya alarm seviyesinde değil ya makine-okunur adı `kind`'da taşımıyor"
    assert "bar_kaynak_uyusmazligi" not in kod.split("def crosscheck_report")[0].replace(
        'kind="bar_kaynak_uyusmazligi"', ""), \
        "eski obs.warn çağrısı hâlâ duruyor olabilir — iki kanaldan iki kez anlatılır"


# =================================================================================================
# B) İMZA KAYMASI — korunum raporu GERÇEK broker-red imzasını okuyor mu?
# =================================================================================================
def test_korunum_raporu_BROKER_REJECT_imzasini_dropped_sayar(sandbox_state):
    """watchdog.conservation_report `event == "failed_broker_rejection"` arıyordu; o ad HİÇBİR ZAMAN
    olay olarak yayınlanmadı — loop.py onu yalnız plan ALANI olarak yazar, yayılan olay ise
    obs.alarm(BROKER_REJECT). Dal ÖLÜYDÜ: canlıdaki 4 red (UNP/NSC/TMO/RTX) `dropped` kümesine hiç
    giremiyor, korunum raporu onları AÇIKLANAMAYAN sayıyordu.

    Kurulum: bir plan yaz, işleme DÖNÜŞTÜRME, ve düşüşünü GERÇEK imzayla kaydet. Doğru davranış:
    plan açıklanmış sayılır (unexplained == 0)."""
    from meridian import obs, watchdog as wd
    store.append_jsonl("trade_plans.jsonl", {
        "id": "P-2026-07-23-UNP", "date": "2026-07-23", "ticker": "UNP", "setup": "breakout_vcp",
        "score": 72, "entry_trigger": 100.0, "stop": 95.0, "gate_verdict": "GO",
        "strategy_version": 3})
    # GERÇEK imza: obs.alarm `alarm` alanını fields'a koyar ve olay adını "<JETON> <mesaj>" yapar.
    obs.alarm(obs.ALARM_BROKER_REJECT, "Alpaca reddi: UNP — stop price must be greater",
              ticker="UNP", plan_id="P-2026-07-23-UNP")
    rep = wd.conservation_report()
    assert rep["plans"] == 1
    assert rep["unexplained"] == 0, \
        ("broker reddi AÇIKLANAMAYAN sayıldı — süzgeç hâlâ yayınlanmayan bir olay adını bekliyor "
         f"(rapor: {rep})")


def test_olmayan_olay_adi_artik_suzgecte_DEGIL():
    """Ölü dalın geri gelmemesi: `failed_broker_rejection` bir OLAY adı olarak süzgeçte durmamalı.
    (Plan ALANI olarak loop.py'de yaşamaya devam eder — orası meşru, süzgeç değil.)"""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "watchdog.py").read_text()
    kod = "\n".join(ln.split("#", 1)[0] for ln in src.splitlines())
    assert "failed_broker_rejection" not in kod, \
        "ölü olay adı watchdog süzgecine geri dönmüş — dedektör yine hiç eşleşmeyecek"


# =================================================================================================
# C) PENCERE KÖRLÜĞÜ — tarih tabanlı pencere + seli ölçen meta dedektör
# =================================================================================================
def _ev(event: str, ts: str, **f):
    store.append_jsonl("events.jsonl", {"ts": ts, "level": "warn", "event": event, **f})


def test_events_since_TARIH_tabanli_penceredir_satir_limitli_DEGIL(sandbox_state):
    """Satır limiti, tek bir olayın seli altında pencereyi çökertiyordu (canlı: 7 gün istenirken
    ~16 saat görülüyordu). Kurulum: 3000 gürültü satırı + 8 gün önce TEK anlamlı satır.
    Doğru davranış: 30 günlük pencere o eski satırı GÖRÜR."""
    from meridian import watchdog as wd
    eski = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=8)).isoformat(timespec="seconds")
    _ev("session_bar_never_published", eski, session="2026-07-20", universe_coverage=0.18)
    simdi = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for _ in range(3000):
        _ev("hotstate_down", simdi, error="ConnectionError")
    pencere = wd.events_since(30)
    assert any(e.get("event") == "session_bar_never_published" for e in pencere), \
        "8 gün önceki satır 30 günlük pencerede GÖRÜNMÜYOR — pencere yine satır limitine bağlı"
    # 1 günlük pencere eski satırı DIŞLAR (pencere gerçekten tarihe göre çalışıyor, hep-hepsi değil)
    assert not any(e.get("event") == "session_bar_never_published" for e in wd.events_since(1))


def test_universe_coverage_atlanan_seanslari_GORUR(sandbox_state):
    """Dedektör yalnız `universe_coverage_low`a bakıyordu ve o olay canlıda 0 kez ateşlenmiş; bu
    yüzden "işlenen seanslar tam evreni gördü" diyordu — oysa aynı defterde 164 ATLANMIŞ seans
    yazılıydı. İki imza birden okunmalı: tarihsel `event` adı VE yükseltme sonrası `kind`."""
    from meridian import watchdog as wd
    simdi = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    _ev("session_bar_never_published", simdi, session="2026-07-28", universe_coverage=0.18)
    row = next(r for r in wd.parity_report()["rows"] if r["check"] == "universe_coverage")
    assert row["ok"] is False and "ATLANDI" in row["detail"], row

    # Yükseltilmiş imza (alarm → ad `kind`'da) da SAYILMALI, yoksa dedektör YENİ satırlara kör olur.
    store.write_jsonl("events.jsonl", [])
    store.append_jsonl("events.jsonl", {
        "ts": simdi, "level": "alarm", "event": "DATA_QUALITY SEANS ATLANDI: 2026-07-28",
        "alarm": "DATA_QUALITY", "kind": "session_bar_never_published",
        "session": "2026-07-28", "universe_coverage": 0.18})
    row2 = next(r for r in wd.parity_report()["rows"] if r["check"] == "universe_coverage")
    assert row2["ok"] is False, "yükseltilmiş imza sayılmıyor — dedektör yeni olaylara kör"


def test_tek_olayin_defteri_ELE_GECIRMESI_olculur(sandbox_state):
    """META DEDEKTÖR: gürültü, dedektörleri kapatan bir yüzeye dönüşebilir ve bunu ölçen hiçbir şey
    yoktu. Bir olay defteri domine ediyorsa PENCERELİ tüm tüketiciler (parite/inbox/selfreview/
    otonomi) ölçtüklerini sandıkları tarihi görmüyor demektir."""
    from meridian import watchdog as wd
    simdi = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for _ in range(900):
        _ev("hotstate_down", simdi, error="ConnectionError: Connection closed by server.")
    for _ in range(100):
        _ev("daily_cycle", simdi, candidates=3)
    row = next(r for r in wd.parity_report()["rows"] if r["check"] == "event_ledger_domination")
    assert row["ok"] is False and "hotstate_down" in row["detail"], row


def test_selfreview_HAFTAYI_gorur_ve_kesilmeyi_OLCER(sandbox_state):
    """"Hiçbir satır uydurulmaz" iddialı haftalık rapor, `limit=4000` yüzünden haftanın çoğuna
    kördü ve bunu ÖLÇMÜYORDU (notify.inbox aynı sorunu `window_truncated` ile ölçüyor).
    İki şey çivilenir: hafta içindeki alarm SAYILIR, ve pencerenin kesilip kesilmediği raporlanır."""
    from meridian import selfreview
    simdi = dt.datetime.now(dt.timezone.utc)
    # 6 gün önce bir MECHANISM_STALE (pencere içinde) + bugün 3000 gürültü satırı
    store.append_jsonl("events.jsonl", {
        "ts": (simdi - dt.timedelta(days=6)).isoformat(timespec="seconds"), "level": "alarm",
        "event": "MECHANISM_STALE eski", "alarm": "MECHANISM_STALE", "mechanism": "cf_advance"})
    for _ in range(3000):
        _ev("hotstate_down", simdi.isoformat(timespec="seconds"), error="x")
    rep = selfreview.build()
    wk = rep["week"]
    assert wk["watchdog_incidents_n"] >= 1, \
        "6 gün önceki alarm haftalık raporda sayılmadı — pencere yine satır limitine bağlı"
    assert "window_truncated" in wk and "window_oldest_ts" in wk, \
        "kesilme ÖLÇÜLMÜYOR — eksiklik 'olay yok' diye okunur"


# =================================================================================================
# D) ÖLÇÜLMEYEN HÜKÜM + SÖZLEŞMESİZ DEFTER
# =================================================================================================
def test_goal_failure_hukmu_OLCULUR(sandbox_state):
    """goal.yaml `failure_below: -0.04` hükmü 2026-07-14'ten 07-30'a kadar hiçbir kod tarafından
    okunmadı: `guard.GOAL_KEYS` yalnız üyelik seti, `score.score_detail` hedef üçlüsünü composite'e
    katıyor ama failure tarafını ASLA. Deney başarısız olsa bunu söyleyecek tek satır yoktu."""
    from meridian import watchdog as wd, config
    goal = config.goal()
    # Eşiğin ALTINA düşen bir defter kur: min_sample kadar kaybeden işlem.
    n = int(goal.get("min_sample", 30))
    rows = [{"id": f"T{i}", "ts_open": "2026-07-01", "ts_close": "2026-07-02", "ticker": "AAA",
             "r_multiple": -1.0, "pnl_dollars": -900.0, "plan_id": f"P-2026-07-01-A{i}",
             "regime": "chop", "score": 70, "setup": "breakout_vcp", "strategy_version": 3}
            for i in range(n)]
    store.write_jsonl("trades.jsonl", rows)
    rep = wd.goal_failure_report()
    assert rep["threshold"] == float(goal["failure_below"])
    assert rep["failed"] is True, f"başarısızlık hükmü ölçülmedi: {rep}"
    assert rep["realized_30d"] is not None and rep["realized_30d"] < rep["threshold"]


def test_goal_failure_ORNEKLEM_YETMEZSE_None_dondurur_sifir_DEGIL(sandbox_state):
    """UYDURMA YASAĞI: `failed=False` demek "ölçtük, başarısız değil" gibi okunur. Örneklem
    min_sample'ın altındaysa doğru cevap None'dır — "henüz ölçülemiyor"."""
    from meridian import watchdog as wd
    store.write_jsonl("trades.jsonl", [])
    rep = wd.goal_failure_report()
    assert rep["failed"] is None, f"ölçülemeyen hüküm False döndü — yanlış güven: {rep}"
    assert rep["realized_30d"] is None


def test_GOAL_FAILURE_jetonu_bildirim_kapsamina_TURETMEYLE_girer():
    """Yeni bir ALARM_ sabiti eklemek kapsamı KENDİLİĞİNDEN büyütmeli (el listesi çürür)."""
    from meridian import obs
    assert obs.ALARM_GOAL_FAILURE == "GOAL_FAILURE"
    assert obs.ALARM_GOAL_FAILURE in obs.NOTIFY_TOKENS


def test_intraday_defterleri_SOZLESMEYE_girdi():
    """Faz 4a/4b defterleri sözleşme yasasının TAMAMEN dışındaydı: `watchdog.parity_report` yalnız
    `ledgers.CONTRACTS`ı gezer ve CONTRACTS 8 eski defterle sınırlıydı. Yani 2026-07-21'de yedi
    hatayı doğuran "sözleşmesiz defter" deseni en YENİ iki defterde aynen yeniden açıktı."""
    from meridian import ledgers as lg
    for ad in ("intraday_decisions.jsonl", "intraday_shadow_orders.jsonl"):
        assert ad in lg.CONTRACTS, f"{ad} sözleşmesiz — alan katmanı denetimsiz"
        c = lg.CONTRACTS[ad]
        # ÜÇ DAMGA zorunlu: look-ahead denetiminin girdisi. Eksikse iddia DOĞRULANAMAZ.
        assert {"decision_as_of", "bar_t", "close_ts"} <= set(c.required), \
            f"{ad}: üç damga zorunlu alan değil — 'sonradan denetlenebilir' iddiası boş kalır"


def test_uc_damga_look_ahead_ihlalini_YAKALAR(sandbox_state):
    """`intraday_shadow.py` "as_of >= close_ts sonradan denetlenebilir" diyor; bugüne kadar o
    denetimi yapan tek şey fixture'lı birim testlerdi — DİSKTEKİ satırlara bakan canlı dedektör
    yoktu. Karar, barın kapanışından ÖNCE alınmış olamaz."""
    from meridian import watchdog as wd
    store.append_jsonl("intraday_decisions.jsonl", {
        "ts": "2026-07-28T14:31:00+00:00", "ticker": "AAPL", "source": "intraday_minute",
        "decision_as_of": "2026-07-28T14:30:00+00:00",       # KAPANIŞTAN ÖNCE → ihlal
        "bar_t": "2026-07-28T14:30:00+00:00",
        "close_ts": "2026-07-28T14:31:00+00:00", "admissible_bars": 5, "fired": False})
    row = next(r for r in wd.intraday_stamp_report()["rows"]
               if r["ledger"] == "intraday_decisions.jsonl")
    assert row["ok"] is False and "LOOK-AHEAD" in row["detail"], row


def test_bos_intraday_defteri_IHLAL_DEGIL(sandbox_state):
    """"Damga tutmuyor" ile "denetlenecek satır yok" AYRI hükümler. İki defter de bugün 0 satır
    (bilinen 4a saha açlığı); boş defteri kırmızı yakmak her gün SAHTE alarm üretirdi."""
    from meridian import watchdog as wd
    rep = wd.intraday_stamp_report()
    assert rep["ok"] is True
    assert all(r["rows"] == 0 and "boş" in r["detail"] for r in rep["rows"])


def test_events_sozlesmesi_GERCEK_tuketicileri_sayar():
    """Sözleşmenin tek işi TAM olmaktır: `notify.inbox` ve `analytics.autonomy` da bu defteri
    okuyor ve ikisi de PENCERELİ okur — budama/şema kararı bu listeye bakılarak verilir."""
    from meridian import ledgers as lg
    tuketiciler = set(lg.CONTRACTS["events.jsonl"].consumers)
    assert {"notify", "analytics"} <= tuketiciler, \
        f"events.jsonl sözleşmesi iki gerçek okuyucuyu saymıyor: {tuketiciler}"


def test_candidates_G2_takma_adi_BEYAN_EDILDI():
    """Defter `mom_12_1` yazıyor (strategy.py), component_ic raporu `mom12_1` kullanıyor — ad dikişi
    alanların eklendiği GÜN ayrıştı. ledgers.py TAM BU "takma ad" hastalığı için kurulmuştu."""
    from meridian import ledgers as lg
    c = lg.CONTRACTS["candidates.jsonl"]
    assert ("mom_12_1", "mom12_1") in c.aliases, \
        "G2 ad dikişi sözleşmede beyan edilmemiş — sessizce birikir"
    # G2 alanları ZORUNLU OLMAMALI: 323 satırın yalnız 10'unda var; zorunlu yapmak 313 tarihsel
    # satırı ihlalli gösterip makullük satırını SAHTE kırmızıya boyardı.
    assert not ({"rvol20", "mom_12_1", "rmom"} & set(c.required)), \
        "G2 alanları zorunlu yapılmış — tarihsel satırlar sahte ihlal üretir"


def test_takma_ad_kanonik_adin_YERINI_ALAMAZ(sandbox_state):
    """Satır yalnız rapor-tarafı yazımını (`mom12_1`) taşıyorsa bu bir İHLALDİR: yaması olmayan
    her tüketici o satırı sessizce eler."""
    from meridian import ledgers as lg
    ihlal = lg.validate_row("candidates.jsonl", {
        "date": "2026-07-29", "ticker": "AAA", "score": 70, "setup": "breakout_vcp",
        "mom12_1": 0.4})
    assert any("kanonik ad eksik" in v for v in ihlal), ihlal


# =================================================================================================
# E) DEDEKTÖRÜN KÖR KESİTİ — kök + dizin + .json OLMAYAN artefaktlar
# =================================================================================================
def test_orphan_taramasi_KOK_ve_DIZIN_artefaktlarini_gorur(sandbox_state):
    """Tarama `config.STATE.glob("*.json*")` idi; üç şeyi HİÇ göremiyordu: kök artefaktlar, başka
    uzantılar ve DİZİNLER. Canlı kanıt: `state/bars_cboe_backup/` 11 MB / 56 dosya, sıfır referans,
    hiçbir dedektör görmüyordu; `state/server.log` 14 Temmuz'dan donuktu."""
    from meridian import recompute, config
    (config.STATE / "server.log").write_text("x" * 200)
    d = config.STATE / "bars_cboe_backup"
    d.mkdir()
    (d / "aapl.csv").write_text("date,close\n2026-07-01,100\n")
    recompute._CORPUS_CACHE.clear()
    row = next(r for r in recompute.report()["rows"] if r["check"] == "orphan_state_files")
    assert row["ok"] is False
    assert "server.log" in row["detail"] and "bars_cboe_backup" in row["detail"], row["detail"]


def test_YORUM_okuyucu_SAYILMAZ(sandbox_state):
    """BU DEDEKTÖR YAZILIRKEN CANLI OLARAK YAKALANDI: korpus ham metin olarak kurulunca tarama
    sessizce kör kaldı, çünkü aradığı dosya adlarını recompute.py'nin KENDİ açıklama yorumları ve
    docstring'i içeriyordu. Yani bulgunun gerekçesini yazmak bulgunun kendisini yok ediyordu.
    `test_c7`nin hükmü: "Yorum ve düzyazı yetki değildir" — bir dosyayı OKUMAK kod gerektirir."""
    from meridian import recompute
    kod = recompute._code_only.__doc__ or ""
    assert kod, "gerekçe docstring'i silinmiş"
    # Fonksiyonel kanıt: yorum ve docstring içinde geçen bir ad korpusta OLMAMALI.
    import pathlib
    p = pathlib.Path(recompute.__file__)
    metin = recompute._code_only(p)
    assert "# " not in metin, "yorumlar korpustan atılmamış"
    # recompute.py'nin docstring'i `server.log`u anıyor; korpus onu referans SAYMAMALI.
    assert "server.log" not in metin, \
        "docstring'de anılan dosya adı kod sayılıyor — dedektör kendi gerekçesiyle kör kalır"


# =================================================================================================
# F) EMEKLİ AMA CANLI — halt ikizi TEK yola delege eder
# =================================================================================================
def test_control_halt_ikizi_kanonik_yola_DELEGE_eder(sandbox_state, monkeypatch):
    """`/api/control/halt` `/api/halt`ın ölü ikiziydi ve tehlikeli biçimde SESSİZDİ: kanonik yol
    obs.alarm + notify.halted + heartbeat notu üretirken ikiz yalnız obs.log basıyordu. İkizden
    HALT basılsa Telegram bildirimi ve alarm HİÇ çıkmazdı.

    Tuzak: aynı ailenin `control/learn_halt` ve `control/cancel_open` üyeleri KULLANILIYOR —
    simetriye bakan biri halt'ı da `control/*`a taşırsa bildirim sessizce kaybolurdu.
    SİLİNMEDİ, DELEGE EDİLDİ: rota silinse ona inanan bir istemci 404 alır ve HALT SESSİZCE düşer."""
    from fastapi.testclient import TestClient
    from meridian import api, obs, health
    alarms = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: alarms.append(tok))
    c = TestClient(api.app)
    r = c.post("/api/control/halt", json={"on": True})
    assert r.status_code == 200 and r.json()["halted"] is True, r.text
    assert health.halt_path().exists(), "ikiz HALT bayrağını kurmadı"
    assert obs.ALARM_HALT in alarms, \
        "ikizden HALT basıldı ama ALARM ÇIKMADI — sessiz yol hâlâ ayrışık"
    # Kapatma da aynı kanonik yola gider (bayrak gerçekten kalkar).
    r2 = c.post("/api/control/halt", json={"on": False})
    assert r2.status_code == 200 and r2.json()["halted"] is False
    assert not health.halt_path().exists()


def test_hermes_yuku_OLU_saglik_bloklarini_servis_ETMEZ():
    """/api/hermes beş bloğu (finviz/hotstate/marketstream/barfeed/intraday) ölü servis ediyordu:
    RENDER.hermes hiçbirini okumuyor, dördünün kaynağı /api/diagnostics. api.py'nin KENDİ kuralı:
    "iki uç aynı alanı farklı şekilde servis edemez"."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py").read_text()
    # `api_hermes` gövdesini izole et (dosyanın geri kalanında bu adlar MEŞRU olarak geçiyor).
    i = src.index("def api_hermes(")
    govde = src[i:src.index("@app.post", i)]
    kod = "\n".join(ln.split("#", 1)[0] for ln in govde.splitlines())
    for olu in ('"hotstate":', '"marketstream":', '"barfeed":', '"intraday":'):
        assert olu not in kod, f"/api/hermes hâlâ {olu} servis ediyor — diagnostics tek kaynak olmalı"


def test_gemini_varsayilan_modeli_KODDAN_servis_edilir(sandbox_state):
    """Pano "Boşsa gemini-2.5-pro." yazıyordu, kod `gemini-3.1-pro` koşuyor (operatör tercihi
    2026-07-19): operatör alanı boş bıraktığında panonun söylediği model ile GERÇEKTE koşan model
    farklıydı. Metin artık sabitin KENDİSİNDEN türetilir."""
    from meridian import api, hermes
    import inspect
    src = inspect.getsource(api.api_secrets)
    assert "GEMINI_DEFAULT_MODEL" in src, "varsayılan model yükte servis edilmiyor"
    assert hermes.GEMINI_DEFAULT_MODEL, "sabit boş"


def test_pano_metni_SABIT_model_adi_TASIMAZ():
    """Pano tarafında KULLANICIYA GÖSTERİLEN sabit model adı kalmamalı — yer tutucu (`{default}`)
    kullanılır, yoksa sabit değiştiğinde metin sessizce yalan söyler.

    YORUMLAR ATILIR: ilk yazımda bu test kendi onarımının GEREKÇE YORUMU yüzünden kırmızı yandı —
    açıklama satırı bayat adı anıyordu. Aynı ders orphan taramasında ve `recompute._code_only`'de
    de var: yorum bir davranış değildir, ekrana çıkan metin davranıştır."""
    import pathlib
    js = (pathlib.Path(__file__).resolve().parent.parent
          / "meridian" / "web" / "app.js").read_text()
    kod = "\n".join(ln.split("//", 1)[0] for ln in js.splitlines())
    assert "gemini-2.5-pro" not in kod, "bayat model adı panoda hâlâ sabit yazılı"
    assert '"Boşsa {default}."' in kod, "GEMINI_MODEL açıklaması yer tutucu kullanmıyor"


# =================================================================================================
# G) PANOYA ÇİZİLDİ — üretilip çizilmeyen alanların DOM tüketicisi var mı?
# =================================================================================================
@pytest.mark.parametrize("alan,gerekce", [
    ("kelly", "her istekte hesaplanıp çöpe atılıyordu (blok-bootstrap simülasyonu dâhil)"),
    ("tail_risk", "VaR/CVaR üretiliyor, hiçbir yerde çizilmiyordu"),
    ("integrity_age_s", "'taze gibi göstermez' tasarım sözü kod yorumunda yaşıyordu, ekranda değil"),
    ("stream_checked_age_s", "akış sağlığının YAŞI servis ediliyor, okunmuyordu"),
    ("regime_budget_triggers", "sinyalin VAR OLUŞ NEDENİ görünürlüktü; panoda sıfır geçiş vardı"),
    ("recent_runs", "pipeline_runs.jsonl'ın HTTP→DOM zinciri kopuktu"),
    ("massive_crosscheck", "Massive-vs-zincir hakemliği hiçbir yüzeyde yoktu"),
    ("slippage_measured", "ölçülen slipaj goal.slippage_bps'e karşı hiç sınanmıyordu"),
    ("benchmark_veto_tally", "'20-30 gözlemde karar' eşiğinin sayacı hiç yazılmamıştı"),
])
def test_uretilen_alanin_panoda_DOM_tuketicisi_var(alan, gerekce):
    """YASA 6'nın `codelaw`un GÖREMEDİĞİ katmanı: HTTP yükü → DOM. Statik Python grafı JS'i görmez,
    bu yüzden "kağıt tüketici" (alan ağa çıkıp DOM'a hiç girmemesi) yasa yeşilken oluşabiliyordu —
    `sp.runs` tam olarak böyleydi. Bu test o kesiti kod düzeyinde sürekli sorar."""
    import pathlib
    js = (pathlib.Path(__file__).resolve().parent.parent
          / "meridian" / "web" / "app.js").read_text()
    assert alan in js, f"`{alan}` panoda okunmuyor — {gerekce}"
