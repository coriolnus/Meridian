"""scheduler.py — the local paper-advance loop. On a laptop there is no systemd worker, so nothing
calls loop.daily_cycle: within ~15 min the heartbeat goes stale, /healthz 503s, and hermes_runtime
stops reflecting — the "self-improving local agent" silently freezes. This daemon thread (started by
the dashboard when MERIDIAN_AUTOSTART_CYCLE=1) polls the XNYS calendar and runs ONE daily cycle each
time a new session has closed — the same job run.worker does on the VM, but in-process and stoppable.
Dedupes on portfolio last_date; respects HALT; never advances on a non-session day."""
from __future__ import annotations
import datetime as dt
import threading

from . import config, store, health

STATUS_FILE = "scheduler_status.json"
LEARN_FILE = "learning_cadence.json"    # öğrenme kadansının son koşusu (okuyan: analytics + api)
# HAFTALIK KANIT RAPORU (temizlik turu 2026-07-30). Ad LİTERAL sabittir çünkü `codelaw.artifact_graph`
# statik bir graftır; yazan bu modül, DIŞ okuyucu `api.api_diagnostics` (mlops.validation_report) —
# yani artefakt YASA 6 anlamında tüketicilidir ve DECLARED_SINKS muafiyeti GEREKMEZ.
VALIDATION_FILE = "validation_report.json"

_lock = threading.Lock()
_run_lock = threading.Lock()     # one cycle at a time (manual tick vs scheduled)
_thread: threading.Thread | None = None
_stop = threading.Event()
_state: dict = {"last_processed": None, "last_tick": None, "last_summary": None,
                "cycles": 0, "started_at": None, "poll_seconds": None, "last_refetch_session": None}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _persist() -> None:
    store.write_json(STATUS_FILE, {**_state, "updated": _now()})


# Yeniden başlatmada KORUNMASI gereken alanlar. Diğerleri (last_tick, cycles, started_at) o sürecin
# canlılık bilgisidir ve taşınmamalı.
# YENİ ALANLAR (2026-07-30, son-tarihli merdiven): eskiler AYNEN korundu — `refetch_attempts` hâlâ
# 0..DENSE_ATTEMPTS aralığında "sık deneme" sayacıdır ve panonun 8'lik halkası doğru okumaya devam
# eder; `last_refetch_session` hâlâ "sık faz kapandı" bayrağıdır. Merdivenin seyrek fazı ve son
# tarihi AYRI alanlarda tutulur, çünkü dış tüketiciler (api /api/diagnostics pipeline, app.js
# 2450) bu iki adın ANLAMINA bağlı ve anlamı kaydırmak sessizce yanlış bir pano üretirdi.
_DURABLE = ("last_refetch_session", "refetch_attempts", "last_processed", "last_refetch_coverage",
            "refetch_chase", "refetch_sparse_attempts", "refetch_next_at", "refetch_latest_bar",
            "last_repair_session",
            # ÖĞRENME KADANSI (2026-07-30) DA KALICIDIR ve nedeni `refetch_attempts`inkiyle AYNI
            # sınıf: süreç başına sıfırlanan bir seans damgası, her yeniden başlatmada kadansı
            # BAŞTAN koşturur. Antrenman ucuzdur ama dolgu her plan-günü için bir LLM çağrısı
            # yakar — bir gecede üç kez yeniden başlatılan bir pano, gecelik bütçeyi üç kez harcardı.
            "learn_session", "last_learn",
            # TEMİZLİK TURU KADANSLARI (2026-07-30) — AYNI SINIF, AYNI GEREKÇE. Y4 toplaması FMP
            # kotası yakar (insider `/latest` akışı); haftalık üçlü (doğrulama raporu, massive
            # verify, yasa kayması) ise 2000 replikasyonluk bootstrap ve sembol-başına Massive
            # isteği demektir. Süreç başına sıfırlanan bir damga, her yeniden başlatmada bunları
            # BAŞTAN koştururdu — `refetch_attempts`in öğrettiği hatanın birebir aynısı.
            # `validation_week` ÜÇÜNÜN ORTAK damgasıdır (üçü aynı gün, tek blokta koşar) — üç ayrı
            # damga tutmak, üçünün ayrı ayrı kaydığı bir dünya varmış gibi yapmak olurdu.
            # `shadowlaw_drift` son ÖLÇÜMÜ taşır: yeniden başlatmada kaybolursa pano "hiç ölçülmedi"
            # der ve bir sonraki haftaya kadar öyle kalırdı (2000 replikasyon boşuna yanardı).
            "y4_session", "last_y4", "validation_week", "shadowlaw_drift")

# ---- SON TARİHLİ YENİDEN-DENEME MERDİVENİ (2026-07-30) -------------------------------------------
# ESKİ YASA: 8 deneme × 300 sn = 40 dakika, sonra seans KALICI atlanır ve "SEANS ATLANDI" alarmı
# atılır. İki ölçülmüş kusuru vardı:
#   (1) BÜTÇE YANLIŞ YERDEYDİ. Zincirin en taze kolu T+1 yayınlıyor (massive_grouped_last.json:
#       date 07-28 / fetched_at 07-29 21:15Z), yani barın 40 dakikada gelmesi çoğu gece YAPISAL
#       olarak imkânsızdı. 40 dakika sonra pes etmek, veriyi 23 saat sonra gelecekken beklememek
#       demekti — ve onarım geçidi olmadığı için o seans bir daha HİÇ işlenmiyordu.
#   (2) ALARM SAHTEYDİ. "Kaynak yayınlamıyor" diyordu; oysa kaynak yayınlıyordu, biz beklemiyorduk.
#       164 tarihsel satırın hepsi aynı imza. Sahte alarm, gerçek alarmı okunmaz yapar.
# YENİ YASA: sık faz AYNEN korunur (ilk ~40 dk, mevcut sıklık) — çünkü aynı-akşam bacağı sayesinde
# normal gecede bar ZATEN o pencerede gelir. Gelmezse merdiven SEYREKLEŞİR (30→45→60 dk) ve kovalama
# BİR SONRAKİ SEANSIN KAPANIŞINA kadar sürer. Terminal atlama — ve alarm — yalnız o anda ilan edilir:
# "bir sonraki seans kapandı, öncekinin barı hâlâ yok" gerçekten arızadır ve uyandırmayı hak eder.
DENSE_ATTEMPTS = 8               # sık faz tavanı (mevcut davranış, mevcut alan adı, mevcut pano halkası)
SPARSE_BASE_S = 1800.0           # seyrek fazın İLK aralığı: 30 dk
SPARSE_MAX_S = 3600.0            # üst sınır: 60 dk (aralık 1,5 kat büyür, burada durur)


def _rehydrate() -> dict:
    """Kalıcı sayaçları diskten geri yükle.

    NEDEN (2026-07-22, veri hattı denetimi bunu kanıtla buldu): `_state` YALNIZ süreç belleğindeydi.
    `_persist()` yazıyordu ama kimse geri okumuyordu. Sonuç: 8 denemelik tazeleme tavanı SÜREÇ
    BAŞINAydı — her yeniden başlatma tavanı sıfırdan yakıyor ve her deneme 250 sembol × 3 kaynaklık,
    önbelleği baypas eden bir ağ süpürmesi demek. Canlı kanıt: TEK bir seans (2026-07-15) için 159
    kez "yayınlanmadı" uyarısı, ve aynı pencerede 18 sembolde 429 kaynaklı "hiçbir kaynak veri
    dönmedi". İki hata aynı olayın iki ucuydu: tavanın unutulması, sağlayıcıyı boğuyordu."""
    saved = store.read_json(STATUS_FILE, {}) or {}
    if not isinstance(saved, dict):
        return {}
    got = {k: saved[k] for k in _DURABLE if saved.get(k) is not None}
    if got:
        _state.update(got)
        from . import obs
        obs.log("scheduler_state_rehydrated", **got,
                detail="tazeleme tavanı süreçler arasında korundu — yeniden başlatma ağ süpürmesini "
                       "sıfırdan yakmıyor")
    return got


_CALENDAR_WARNED = False


def _last_closed_session() -> str | None:
    """Most recent GENUINELY CLOSED XNYS session (market_close <= now, UTC). The old version included
    today's session from midnight, so the once-per-session refetch fired PRE-OPEN (when the feed can't
    have today's bar yet), consumed the dedup flag, and every post-close poll that evening ran
    cache-only — new bars arrived a full session late (audit #12)."""
    global _CALENDAR_WARNED
    try:
        import pandas_market_calendars as mcal
        today = dt.date.today()
        sched = mcal.get_calendar("XNYS").schedule(start_date=str(today - dt.timedelta(days=10)), end_date=str(today))
        now = dt.datetime.now(dt.timezone.utc)
        closed = [str(d.date()) for d, row in sched.iterrows() if row["market_close"] <= now]
        return closed[-1] if closed else None
    except Exception as e:
        # SESSİZ DEĞİL ama SÜREÇ BAŞINA BİR KEZ (C2, 2026-08-02). Eski işaretin gerekçesi
        # ("asıl karar bu değere bağlı DEĞİL ve çağıran yokluğu yedek değerle karşılıyor")
        # GERÇEĞE AYKIRIYDI — repoda 13 yerde harfi harfine tekrarlanan bir şablon damgaydı ve
        # burada tutmuyordu: `last_closed` None dönerse `advance_once` içinde `_dense` ve
        # `_chasing` False kalır, `fresh` KALICI False olur ve terminal atlama, merdiven adım-1,
        # onarım/sip düzeltici, aynı-akşam bacağı, earnings, arming, selfreview, yetim süpürme,
        # nous_eval, öğrenme kadansı, Y4, haftalık üçlü, skill revizyonu ve crosscheck — yani TÜM
        # seans-sonrası kadans — tek bir uyarı bile düşmeden durur. Yedek değer YOKTUR.
        # Kardeş `_leg_ready` bu boşluğu kapatmaz: `if not session: return None` ile try'a hiç
        # girmez, dolayısıyla onun tek-seferlik uyarısı da ATEŞLENMEZ.
        #
        # TEKRAR-UYARI YOK: bu yol her poll'de (300 sn) çalışır; koşulsuz uyarı 288 satır/gün
        # üretir ve olay defterini — gelen kutusunun ve tüm makullük dedektörlerinin okuduğu
        # kaynağı — boğardı (K1 seli dersi). Anlatılacak olgu "takvim YOK", "her poll" değil.
        if not _CALENDAR_WARNED:
            _CALENDAR_WARNED = True
            from . import obs
            obs.warn("session_calendar_unavailable", error=f"{type(e).__name__}: {e}",
                     detail="seans takvimi okunamadı — son KAPANMIŞ seans bilinmiyor, seans-sonrası "
                            "kadansın TAMAMI duruyor (süreç başına bir kez kaydedilir)")
        return None


# AYNI-AKŞAM BACAĞININ ZAMAN KAPISI (Rol 1 eki 2): Basic planın tarihsel-veri kısıtı "son 15
# dakika"dır — konsolide (sip) günlük bar ancak kapanıştan SONRA, o pencerenin dışında sorgulanabilir.
# 16. dakikadan önce çağırmak iki şekilde yanlış olurdu: sip penceresi boş döner (boşuna çağrı) ve
# iex snapshot KISMİ günlük bar verir (kapanış sanılırsa kararlar yanlış fiyata dayanır).
# YASA TEK YERDE: takvim bilgisi zaten burada (bkz. _last_closed_session) — data.py'ye ikinci bir
# takvim uygulaması koymak, bu depoda tekrar tekrar yaşanan "aynı yasanın iki uygulaması" hatasıdır.
SAME_EVENING_DELAY_MIN = 16
_LEG_GATE_WARNED = False


def _leg_ready(session: str | None) -> str | None:
    """Bacağın kapısı: kapanış + SAME_EVENING_DELAY_MIN geçtiyse seansı döndür, yoksa None
    (None = bacak bu poll'de HİÇ denenmez; zincir normal çalışır)."""
    global _LEG_GATE_WARNED
    if not session:
        return None
    try:
        import pandas_market_calendars as mcal
        sched = mcal.get_calendar("XNYS").schedule(start_date=str(session), end_date=str(session))
        if not len(sched):
            return None
        close = sched.iloc[0]["market_close"].to_pydatetime()
        if dt.datetime.now(dt.timezone.utc) < close + dt.timedelta(minutes=SAME_EVENING_DELAY_MIN):
            return None
    except Exception as e:
        # SESSİZ DEĞİL ama SÜREÇ BAŞINA BİR KEZ: bu yol her poll'de çalışır ve takvim modülü
        # yoksa 288 satır/gün üretirdi. Kapalı taraf GÜVENLİ tarafdır: 16 dakikayı kanıtlayamıyorsak
        # kısmî bar riskini almayız.
        if not _LEG_GATE_WARNED:
            _LEG_GATE_WARNED = True
            from . import obs
            obs.warn("same_evening_gate_unavailable", session=str(session),
                     error=f"{type(e).__name__}: {e}",
                     detail="seans kapanışı doğrulanamadı — aynı-akşam bacağı KAPALI kalır "
                            "(kısmî bar yazmaktansa boşluk dürüsttür)")
        return None
    return str(session)


def _session_coverage(bars: dict, session: str | None) -> float:
    """Evrenin kaçta kaçı bu seansın barını taşıyor? Motorun kapsama kapısıyla AYNI soru — tazeleme
    bayrağı da aynı cevaba göre tükenmeli, yoksa veri hattı ile motor birbirini bekler."""
    if not session or not bars:
        return 0.0
    have = 0
    for df in bars.values():
        try:
            if not len(df):
                continue
            last = str(df["date"].iloc[-1])[:10]
            # BİÇİM DOĞRULAMASI: dizgi karşılaştırması bozuk bir değeri ("bozuk" > "2026-…") TAZE
            # sayardı ve kapsamayı yukarı şişirirdi — yani eksik veriyle karar verilmesine yol açardı.
            # Kapsama ölçümü daima muhafazakâr tarafta durur: emin değilsen "yok" say.
            dt.date.fromisoformat(last)
            if last >= session:
                have += 1
        except (ValueError, TypeError, KeyError, IndexError):  # sessiz-yutma: sonuç ÖLÇÜME giriyor — bozuk seri 'bu seansın barı yok' sayılır, kapsama oranını DÜŞÜRÜR (muhafazakâr taraf)
            continue
    return have / max(1, len(bars))


def _sparse_due() -> bool:
    """Seyrek fazda ağ denemesi ZAMANI geldi mi? (damga yoksa: evet — ilk seyrek deneme)"""
    at = _state.get("refetch_next_at")
    if not at:
        return True
    try:
        return dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(str(at))
    except (TypeError, ValueError):  # sessiz-yutma: damga bozuk — "zamanı geldi" sayılır (muhafazakâr: veri BEKLETİLMEZ)
        return True


def _schedule_sparse() -> None:
    """Bir sonraki seyrek denemeyi planla: 30 → 45 → 60 dk (60'ta durur)."""
    k = int(_state.get("refetch_sparse_attempts") or 0)
    gap = min(SPARSE_MAX_S, SPARSE_BASE_S * (1.5 ** max(0, k - 1)))
    _state["refetch_next_at"] = (dt.datetime.now(dt.timezone.utc)
                                 + dt.timedelta(seconds=gap)).isoformat(timespec="seconds")


def _declare_terminal_skip(session: str) -> None:
    """SON TARİH DOLDU: bir sonraki seans kapandı ve `session`ın barı hâlâ gelmedi. Alarm YALNIZ
    burada atılır — merdivenin tamamı boyunca değil. Alan adları ve `kind` KORUNUR: watchdog
    parite dedektörü (`session_bar_never_published`, `session`, `universe_coverage`) bu imzayı
    okuyor; adı kaydırmak dedektörü sessizce kör bırakırdı (failed_broker_rejection dersi)."""
    from . import loop, obs
    need = getattr(loop, "UNIVERSE_MIN_COVERAGE", 0.90)
    cov = _state.get("last_refetch_coverage")
    _state["last_refetch_session"] = session          # kovalama kapandı: bayrak tüketildi
    _state["refetch_chase"] = None
    _state["refetch_next_at"] = None
    try:
        obs.alarm(obs.ALARM_DATA_QUALITY,
                  f"SEANS ATLANDI: {session} — bir sonraki seans kapandı, bu seansın barı hâlâ "
                  f"gelmedi (kapsama %{100 * float(cov or 0):.0f} < %{100 * need:.0f})",
                  kind="session_bar_never_published",
                  session=session, latest_bar=_state.get("refetch_latest_bar"),
                  universe_coverage=cov, required=need,
                  dense_attempts=_state.get("refetch_attempts"),
                  sparse_attempts=_state.get("refetch_sparse_attempts"),
                  detail="son tarih (bir sonraki seansın kapanışı) doldu — motor bu seansı "
                         "ATLAYACAK; onarım geçidi hâlâ deneyecek ama kovalama kapandı")
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
        pass


def _repair_once_per_session(session: str) -> None:
    """SIP DÜZELTİCİ + ONARIM GEÇİDİ + HACİM KALİBRASYONU — seans başına BİR kez, ağ maliyeti sınırlı.
    Onarım son K seansın kapsamasını tarar ve eksik seansı grouped ile kapatır (eksik seans başına
    EN ÇOK bir çağrı). Kalibrasyon yalnız BAYATSA koşar (IEX hacmi konsolide değildir; ölçülmemiş
    bir oranla yazılan hacim rvol kapılarını sessizce kapatırdı).

    SIP DÜZELTİCİSİ NEDEN TAM BURADA (2026-07-30 tasarım düzeltmesi — ve neden "sabah" DEĞİL):
    zamanlayıcıda GÜN İÇİ bir kadans yoktur; `_last_closed_session()` sabahleyin hâlâ dünü döndürür
    ve bu blok o seans için zaten yanmıştır. Yani "sabah koşusu" diye bir kanca YOKTU ve UYDURULMADI:
    gerekli koşul "hedef seansın TAKVİM GÜNÜ kapanmış olsun ve massive'den ÖNCE koşsun"dur — bu blok
    ikisini de sağlar. D seansının kapanışında koştuğunda D-1'in (ve daha eskisinin) IEX satırları
    geçmiştedir → sip 200 verir; ve bu satır `dataset.load_live` çağrısından ÖNCEDİR → massive aynı
    turda üstüne yazarsa sıra iex → sip → massive olur, defter ikisini de ayrı ölçer.
    SIRA İÇERİDE DE KASITLI: önce sip (var olan satırı konsolideye taşır), sonra onarım (OLMAYAN
    satırı açar). İkisi ayrık kümelerde çalışır; ters sırada koşsalardı da doğru olurdu, ama bu sıra
    "önce elimizdekini düzelt, sonra deliği kapat" okumasını kodda görünür kılıyor."""
    from . import obs
    from .adapters import data as _da
    _state["last_repair_session"] = session
    try:
        _state["last_sip_correction"] = _da.sip_correct_provisional()
    except Exception as e:
        # YASA 4: düzeltici düşerse dünün satırları TEMSİLÎ (iex) kalır ve konsolideye dönmeleri
        # yeniden TEK kaynağa (massive grouped) bağlanır — bu turun kök nedeninin ta kendisi.
        obs.warn("sip_correction_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="geçmiş seansın temsilî barları konsolide sip barıyla düzeltilemedi — "
                        "massive grouped tek düzeltici olarak kaldı")
    try:
        _state["last_repair"] = _da.repair_coverage()
    except Exception as e:
        # YASA 4: onarım düşerse delik AÇIK kalır ve motor o seansı atlamaya devam eder — sessiz kalamaz.
        obs.warn("coverage_repair_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="eksik seans kapatılamadı; kapsama kapısı bu seansı reddetmeye devam edebilir")
    try:
        if _da.volume_calibration_stale():
            _state["last_volume_calibration"] = _da.calibrate_volume()
    except Exception as e:
        obs.warn("volume_calibration_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="aynı-akşam barlarının hacmi ÖLÇEKLENEMEZ (0 yazılır) — fiyat geçerli, "
                        "hacim türevleri o barlarda kapanır")


# ==================================================================================================
# ÖĞRENME KADANSI — SEANS BAŞINA BİR KEZ, BAR VARIŞINDAN BAĞIMSIZ (2026-07-30)
# ==================================================================================================
# ÖLÇÜLMÜŞ KUSUR. Üç öğrenme mekanizması da KOD OLARAK vardı ve üçü de AYNI yere asılıydı:
# `loop.daily_cycle`ın P5_LEARN bloğu (shadow_model.refit_and_save → loop.py:796,
# skills.auto_shadow_from_evidence → loop.py:848). O blok yalnız YENİ BİR SEANSIN BARI GELDİĞİNDE
# koşar. Canlı kanıt (2026-07-30): scheduler last_summary="noop", kapsama 0,172,
# portfolio.last_date=2026-07-28 — yani veri hattı takılı ve öğrenme onunla birlikte durmuş.
# Kusur eksik bir çağrı değil, bir REHİNELİKTİ: kanıt üreten katman, kanıt TÜKETEN katmanın
# bekleme odasında oturuyordu.
#
# NEDEN BURASI. Bu blok (`fresh`) zamanlayıcının seans-sonrası kancasıdır ve akranları zaten
# burada: arming_eval, selfreview, orphan_sweep, nous_eval, revision_week. Onlar gibi kendi
# damgasıyla tekilleşir (`learn_session`), o damga KALICIDIR (bkz. `_DURABLE`) ve `fresh` bar
# gelmese de yanar (sık/seyrek fazın her denemesinde) — yani kadans bar varışına bağlı DEĞİLDİR.
#
# NE YAPMAZ. Yeni bir yetki İCAT ETMEZ. Antrenmanın sonucu `shadow_model.evaluate_promotion`ın
# yazılı kuralı ve tek etkisi `shadow_veto`dur; dolgu geçmişe görüş damgalar (look-ahead yok);
# Eksen-2 kadansı `skills`in KENDİ eşiklerini kullanır. Üçü de bugünkü karar sınırlarının içinde.
LEARN_STEPS = ("antrenman", "eksen2", "dolgu")


def _learning_cadence(session: str) -> dict:
    """Üç otomasyonu SIRAYLA koştur; her adım kendi korumasında (biri düşerse diğerleri yaşar).

    SIRA GEREKÇELİ: önce antrenman (ucuz, saf-numpy, LLM kotası harcamaz ve Eksen-2'nin okuduğu
    atıf tablosuyla aynı defterleri tazeler), sonra Eksen-2 (deterministik, kotasız), en sonda
    dolgu (TEK kota tüketicisi — ötekiler onun artığıyla değil, o ötekilerin artığıyla koşsun).

    DOLGU ASENKRONDUR: gün başına bir LLM çağrısı × tavan kadar gün, poll'ü dakikalarca bloklardı
    (`review_candidates_async` ile aynı gerekçe ve aynı sözleşme — Thread döner)."""
    from . import obs, watchdog
    out: dict = {"session": session, "ts": _now()}
    try:                                   # 1) ANTRENMAN — veri seti değiştiyse fit + terfi hükmü
        from . import shadow_model as _sm
        out["antrenman"] = _sm.maybe_refit()
        watchdog.beat("shadow_fit")
    except Exception as e:
        # YASA 4: antrenman düşerse model BAYAT kalır ve panodaki gölge P(kazanç) eski katsayılarla
        # üretilmeye devam eder — yani yanlış bir sayı, doğru bir sayı gibi görünür. Sessiz kalamaz.
        obs.warn("shadow_fit_cadence_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="gölge model yeniden eğitilemedi — bayat katsayılarla tahmin üretmeye devam eder")
        out["antrenman"] = {"error": f"{type(e).__name__}: {e}"}
    try:                                   # 2) EKSEN-2 — skill öneri üreteci (deterministik, kotasız)
        from . import skills as _sk
        out["eksen2"] = _sk.axis2_cycle()
        watchdog.beat("axis2_cycle")
    except Exception as e:
        obs.warn("axis2_cycle_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="Eksen-2 üreteci koşmadı — atıf kanıtı bir KARARA bağlanmıyor")
        out["eksen2"] = {"error": f"{type(e).__name__}: {e}"}
    try:                                   # 3) DOLGU — bütçeli, asenkron, en eskiden yeniye
        from . import hermes as _h
        bt = _h.backfill_budget()
        out["dolgu_butce"] = bt
        if bt["tavan"] > 0:
            _h.backfill_opinions_async()   # tavan İÇERİDE türetilir (tek yer, tek formül)
            out["dolgu"] = {"baslatildi": True, "tavan": bt["tavan"], "formul": bt["formul"]}
        else:
            # Kısılma kayda geçer; "başlatılmadı" ile "başlatıldı ve iş çıkmadı" ayrı hâllerdir.
            obs.log("backfill_progress", islenen=0, tavan=0, kaynak=bt["kaynak"],
                    formul=bt["formul"], detail="kadans bütçe nedeniyle dolgu başlatmadı")
            out["dolgu"] = {"baslatildi": False, "tavan": 0, "formul": bt["formul"]}
    except Exception as e:
        obs.warn("opinion_backfill_cadence_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="görüş dolgusu tetiklenemedi — LLM kalibrasyonu beslenmiyor")
        out["dolgu"] = {"error": f"{type(e).__name__}: {e}"}
    _state["learn_session"] = session
    _state["last_learn"] = out
    # DEFTER: analytics/api bu dosyadan okur (YASA 6 — yazan scheduler, okuyan analytics).
    store.write_json(LEARN_FILE, out)
    obs.log("learning_cadence", session=session,
            antrenman=(out.get("antrenman") or {}).get("fitted"),
            eksen2_kaydedilen=len((out.get("eksen2") or {}).get("kaydedilen") or []),
            dolgu=(out.get("dolgu") or {}).get("baslatildi"),
            detail="seans-sonrası öğrenme kadansı — bar varışından BAĞIMSIZ koştu")
    return out


# ==================================================================================================
# Y4 VERİ TOPLAMA KADANSI (temizlik turu, 2026-07-30) — ROADMAP §3.4
# ==================================================================================================
# TEŞHİS. `insider.fetch_delta` ve `shortinterest.fetch` yazıldı, test edildi (v117) ve YALNIZ kendi
# CLI'larından çağrılabilir kaldı: yani defterler ancak operatör elle koştururken doluyordu. Y4'ün
# tüketici bağlantısı BİLİNÇLİ olarak ertelenmiş durumda (bkz. codelaw.DECLARED_SINKS'teki gerekçe:
# insider sınıflaması 3 yıllık pencere ister ve FMP `search` ucu ücretsiz planda 402 dönüyor) — ama
# ERTELENEN ŞEY TÜKETİCİDİR, TOPLAMA DEĞİL. Toplama da durursa pencere HİÇ dolmaz ve "ne zaman
# bağlanabiliriz?" sorusunun cevabı sonsuza kadar "henüz değil" kalır. Bu kadans tam da o pencereyi
# doldurur; hiçbir karara bağlanmaz.
#
# KOTA DİSİPLİNİ — TAVAN FONKSİYONUN KENDİ SINIRINDAN TÜRETİLİR, BURADA SAYI İCAT EDİLMEZ:
#   * insider: `PLAN_SAYFA_TAVANI` — modülün KENDİ ölçülmüş plan sınırı (Rol 1 canlı sondası
#     2026-07-30: ücretsiz planda `page>=1` → 402, `limit>100` → 402, `search` ucu → 402). Günde
#     TEK istek (page=0). `VARSAYILAN_SAYFA_TAVANI` (40) BİLEREK kullanılmıyor: o ücretli plan
#     varsayımıdır ve burada her gece 39 boşa 402 yakardı. Ayrıca `fmp.available()` ve
#     `fmp.quota_blocked()` ÖNDEN sorulur: kota bloğundayken çağrı denemek, bar zincirinin
#     ihtiyacı olan kotayı yakmaktır.
#   * shortinterest: FINRA ucu ANAHTARSIZ ve KOTASIZ (evren `parca` dilimlerine bölünür → 250
#     sembol = 2 istek). FMP bütçesine etkisi SIFIRDIR; `--float-cek` yolu (tek FMP dokunuşu)
#     kadansa BİLEREK bağlanmadı — sembol başına 1 istek yakar ve varsayılanı zaten kapalıdır.
# SEANS BAŞINA 1×: damga `y4_session` ve KALICIDIR (bkz. `_DURABLE`).
def _y4_collect(session: str) -> dict:
    """Y4 veri katmanını (içeriden işlem + kısa pozisyon) bir kez besle. Her ayak kendi
    korumasında — biri düşerse öteki yaşar (öğrenme kadansının deseni)."""
    from . import obs, watchdog
    out: dict = {"session": session, "ts": _now()}
    try:                                   # 1) İÇERİDEN İŞLEM — artımlı delta + özet
        from .adapters import insider as _in, fmp as _fmp
        if not _fmp.available():
            out["insider"] = {"atlandi": "fmp_anahtari_yok"}
        elif _fmp.quota_blocked():
            # KISILMA KAYDA GEÇER: "koşmadı" ile "koştu ve satır bulmadı" ayrı hâllerdir.
            out["insider"] = {"atlandi": "fmp_kota_blogu"}
            obs.log("y4_insider_skipped", session=session, sebep="fmp_kota_blogu",
                    detail="kota bloğundayken Y4 toplaması bar zincirinin kotasını yakmaz")
        else:
            # TAVAN MODÜLÜN KENDİ ÖLÇÜLMÜŞ SINIRINDAN GELİR (Rol 1 canlı sondası, 2026-07-30):
            # ücretsiz planda `page>=1` GARANTİLİ 402'dir. `VARSAYILAN_SAYFA_TAVANI` (40) ücretli
            # plan varsayımıdır ve otonom kadansta kullanılırsa HER GECE 39 boşa 402 yakardı —
            # kotayı bar zincirinden çalan, satır getirmeyen bir tur. Günde 1× page=0: en yeni
            # ~100 dosyalama, evren isabeti ~6/100 (ölçüldü).
            f = _in.fetch_delta(sayfa_tavani=_in.PLAN_SAYFA_TAVANI, limit=_in.SAYFA_LIMIT)
            if "402" in str(f.get("hata") or ""):
                # ABONELİK SINIRI ALARM DEĞİL, BİLİNEN DURUMDUR. `obs.warn` basmak, her gece
                # tekrarlayan ve kimsenin yapabileceği bir şey olmayan bir uyarı üretirdi —
                # gerçek uyarıları okunmaz yapan tam olarak budur. Tek satır, bilgi düzeyinde.
                obs.log("y4_insider_plan_limit", session=session, detail=str(f.get("hata"))[:120],
                        cozum="FMP planı yükseltilirse sayfalama + `search` ucu açılır")
            o = _in.ozet()                 # defterden türetilir, AĞ YOK
            # `durum()` BURADA ÇAĞRILIR, api ucunda DEĞİL — ölçülmüş gerekçe: `defter_oku()` ham
            # Form 4 defterini TAMAMEN okur ve o defter 60.000 satıra kadar büyüyebilir
            # (`DEFTER_TAVANI`). Her pano isteğinde okumak saf maliyet olurdu; seans başına bir kez
            # okunup özeti `scheduler_status.json`a düşer, sağlayıcı kartı ORADAN besleniyor.
            _d = _in.durum()
            out["insider"] = {"cagri": f.get("cagri"), "yeni": f.get("yeni"),
                              "tavana_carpti": f.get("tavana_carpti"),
                              "durma_sebebi": f.get("durma_sebebi"),
                              "kapsam": o.get("kapsam"), "sembol_n": len(o.get("semboller") or {}),
                              "defter": _d.get("defter"), "fmp": _d.get("fmp"),
                              # SAĞLIK KARTINA GEÇEN KÜNYE: kartı okuyan biri "neden günde yalnız
                              # ~6 satır?" sorusunu tahminle değil bu alanla cevaplasın.
                              "plan_siniri": "page0-only"}
    except Exception as e:
        obs.warn("y4_insider_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="Form 4 akışı çekilemedi — 3 yıllık sınıflama penceresi bu seans dolmadı")
        out["insider"] = {"error": f"{type(e).__name__}: {e}"}
    try:                                   # 2) KISA POZİSYON — FINRA (anahtarsız, kotasız)
        from .adapters import shortinterest as _si
        f = _si.fetch()
        satirlar = f.pop("satirlar", [])
        d = _si.ozet(satirlar, cagri=f.get("cagri", 0), hata=f.get("hata"))
        out["shortinterest"] = {"cagri": f.get("cagri"), "satir": f.get("satir"),
                                "hata": f.get("hata"), "yayin": d.get("yayin"),
                                "kapsam": d.get("kapsam"),
                                # kardeşiyle AYNI desen: dosya/bayatlık durumu seans başına bir kez
                                # okunur ve sağlayıcı kartına buradan gider.
                                "durum": _si.durum()}
    except Exception as e:
        obs.warn("y4_shortinterest_failed", session=session, error=f"{type(e).__name__}: {e}",
                 detail="FINRA kısa pozisyon yayını çekilemedi — bayatlık damgası ilerlemedi")
        out["shortinterest"] = {"error": f"{type(e).__name__}: {e}"}
    _state["y4_session"] = session
    _state["last_y4"] = out
    watchdog.beat("y4_collect")
    obs.log("y4_collect", session=session,
            insider_cagri=(out.get("insider") or {}).get("cagri"),
            si_satir=(out.get("shortinterest") or {}).get("satir"),
            detail="Y4 veri toplama kadansı — TÜKETİCİ YOK (bilinçli); pencere doluyor")
    return out


# ==================================================================================================
# HAFTALIK DOĞRULAMA/KAYMA ÜÇLÜSÜ (temizlik turu, 2026-07-30)
# ==================================================================================================
# ÜÇÜ AYNI GÜNDE, AYNI DESENDE (Nous haftalığıyla aynı `isocalendar` damgası): üçü de "yürürlükteki
# ölçüm hâlâ geçerli mi?" sorusunun ayrı birer yüzüdür ve üçü de PAHALIDIR (bootstrap, sembol başına
# ağ isteği) — günlük koşmaları savunulamaz, hiç koşmamaları ise ölçümü dondurur.
#   * validation_report : "hangi mekanizma/edge KANITLANIYOR?" tablosu. `build/render_text` 2026-07-21'de
#     yazıldı ve tek çağıranı `__main__` bloğuydu — yani rapor ancak biri elle çalıştırırsa vardı.
#   * massive.verify    : grouped-vs-zincir ayarlama tutarlılığı. Yazım kapısının (`write_enabled`)
#     DAYANAĞI bu ölçümdür ve ölçüm bayatlarsa kapı bayat kanıtla açık kalır.
#   * shadowlaw kayması : MEASURED_V3'ten türetilmiş marjların hâlâ yerinde olup olmadığı.
# HİÇBİRİ KARAR DEĞİŞTİRMEZ: rapor yazılır, ölçüm yazılır, kayma UYARI olur. Sabit güncellemesi ve
# kapı kararı operatörde kalır.
def _weekly_validation(wk: list) -> dict:
    from . import obs, watchdog
    out: dict = {"hafta": wk, "ts": _now()}
    try:                                   # 1) KANIT RAPORU → state dosyası + api özeti
        from . import validation_report as _vr
        rapor = _vr.build()
        metin = _vr.render_text()
        eb = rapor.get("evidence_base") or {}
        belge = {"uretildi": _now(), "hafta": wk, "evidence_base": eb,
                 "base_edge": rapor.get("base_edge"), "cf_fidelity": rapor.get("cf_fidelity"),
                 "score_calibration": rapor.get("score_calibration"),
                 "setup_edge": rapor.get("setup_edge"), "regime_edge": rapor.get("regime_edge"),
                 "near_miss": rapor.get("near_miss"),
                 "skill_attribution": rapor.get("skill_attribution"), "metin": metin}
        store.write_json(VALIDATION_FILE, belge)
        watchdog.beat("validation_report")
        out["validation_report"] = {"yazildi": True, **eb}
        obs.log("validation_report_written", **eb,
                detail="haftalık kanıt raporu üretildi — SALT-OKUMA analiz, hiçbir kapı etkilenmez")
    except Exception as e:
        # YASA 4: rapor düşerse "hangi edge kanıtlanıyor?" sorusunun TEK derli toplu cevabı kaybolur
        # ve kimse fark etmez (rapor zaten kimsenin beklemediği bir dosyaydı — bu turun kapattığı delik).
        obs.warn("validation_report_failed", error=f"{type(e).__name__}: {e}",
                 detail="haftalık kanıt raporu üretilemedi")
        out["validation_report"] = {"error": f"{type(e).__name__}: {e}"}
    try:                                   # 2) MASSIVE DOĞRULAMA → massive_verify.json (kapının dayanağı)
        from .adapters import massive as _ms
        if not _ms.available():
            out["massive_verify"] = {"atlandi": "massive_anahtari_yok"}
        else:
            v = _ms.verify()               # write=True: hüküm kapının okuduğu dosyaya yazılır
            watchdog.beat("massive_verify")
            out["massive_verify"] = {k: v.get(k) for k in
                                     ("verdict", "samples", "mismatches", "max_dev", "reason")}
            obs.log("massive_verify_week", **out["massive_verify"],
                    write_enabled=_ms.write_enabled())
    except Exception as e:
        obs.warn("massive_verify_failed", error=f"{type(e).__name__}: {e}",
                 detail="yazım kapısının dayanağı tazelenmedi — kapı BAYAT kanıtla karar veriyor")
        out["massive_verify"] = {"error": f"{type(e).__name__}: {e}"}
    try:                                   # 3) MEASURED_V3 KAYMA BEKÇİSİ → yalnız uyarı
        from . import shadowlaw as _sl, config as _cfg
        d = _sl.variance_drift(store.read_jsonl("trades.jsonl"), _cfg.goal())
        watchdog.beat("shadowlaw_drift")
        out["shadowlaw_drift"] = {"olculdu": d.get("olculdu"), "kayma": d.get("kayma"),
                                  "olcum": d.get("olcum")}
        _state["shadowlaw_drift"] = out["shadowlaw_drift"]     # api teşhis bloğunun okuduğu yer
        if d.get("kayma"):
            # SABİT DEĞİŞTİRİLMEZ — yalnız haber verilir. Güncelleme operatör + Rol 1 kararıdır.
            obs.warn("shadowlaw_variance_drift", n=len(d["kayma"]),
                     adlar=[k["ad"] for k in d["kayma"]],
                     gerekceler=[k["gerekce"] for k in d["kayma"]][:3],
                     detail="MEASURED_V3'ten TÜRETİLMİŞ marjlar canlı defterle uyuşmuyor — "
                            "sabitler DEĞİŞTİRİLMEDİ, karar operatör + Rol 1'de")
        elif d.get("olculdu"):
            obs.log("shadowlaw_drift_ok", **(d.get("olcum") or {}),
                    detail="yasa sabitlerinin türetim tabanı hâlâ yerinde")
    except Exception as e:
        obs.warn("shadowlaw_drift_failed", error=f"{type(e).__name__}: {e}",
                 detail="yasa kayması ölçülemedi — marjlar sınanmadan yürürlükte kaldı")
        out["shadowlaw_drift"] = {"error": f"{type(e).__name__}: {e}"}
    _state["validation_week"] = wk
    return out


GAP_SEEN_MAX = 200          # tekrar-bastırma defterinin tavanı (imza başına tek uyarı, sınırsız değil)

# TAKVİM ARIZASI SÜREÇ BAŞINA BİR KEZ ANLATILIR (WP-D kuyruğu, 2026-08-02). `_intraday_gap_check`
# her poll'de (300 sn) koşar; koşulsuz bir uyarı 288 satır/gün üretir ve olay defterini — gelen
# kutusunun ve tüm makullük dedektörlerinin okuduğu kaynağı — boğardı (K1 seli dersi). Kardeş
# `_CALENDAR_WARNED` ile AYNI desen ve AYNI gerekçe; anlatılacak olgu "takvim YOK", "her poll" değil.
# GERİ SIFIRLANMAZ (emsalle aynı): takvim döndüğünde bayrağı temizlemek, modül gidip geldikçe tam da
# bastırmak istediğimiz seli geri açardı.
# AD KARDEŞTEN AYRI (`session_calendar_unavailable` DEĞİL): farklı okuyucu, farklı sonuç. Orada son
# KAPANMIŞ seans bilinmez ve seans-sonrası kadansın TAMAMI durur; burada yalnız boşluk taraması
# ölçülemez, günlük döngü koşmaya devam eder. Tek adla saymak iki arızanın kapsamını karıştırırdı.
_GAP_CALENDAR_WARNED = False


def _intraday_gap_check() -> dict | None:
    """5.3 — SEANS-İÇİ KESİNTİ TESPİTİ. Her poll'de HAFİF bir kontrol: seans-içi bar akışında eksik
    dakika penceresi var mı? Ölçüm SAF fonksiyonda (`barsarchive.gap_scan` — dosyanın yalnız kuyruğu
    okunur); burada yalnız KAYIT ve TEKRAR-BASTIRMA var.

    NEDEN TAM BURADA (halt kapısından ÖNCE): HALT motoru durdurur, veri akışını DEĞİL. Halt
    sırasında akış sessizce koparsa bunu söyleyecek başka bir yer yok ve halt kalktığında motor
    delikli bir seansın üstüne karar verir. Kontrol salt-okunurdur; halt'ın koruduğu şeye dokunmaz.

    TEKRAR-BASTIRMA: pencere (60 dk) iki poll'ü (2 × 5 dk) fazlasıyla kapsar, yani AYNI boşluk her
    poll'de yeniden görünür. İmza (gün|tür|sembol|başlangıç) başına TEK uyarı basılır; imza defteri
    `GAP_SEEN_MAX` ile sınırlıdır (sınırsız bir set, günlerce koşan worker'da sızıntıdır)."""
    global _GAP_CALENDAR_WARNED
    from . import barsarchive, obs
    rapor = barsarchive.gap_scan()
    if rapor.get("durum") in ("seans_disi", "arsiv_yok", "takvim_yok"):
        kopya = {k: rapor[k] for k in ("durum", "gun", "olculdu")}
        if rapor["durum"] == "takvim_yok":
            # ARIZA NEDENİ YALNIZ BU HÂLDE TAŞINIR: takvim konuşmadığında `seans` bloğu (takvim adı
            # + `hata`) tek teşhis kaynağıdır ve durum kopyası onu almadığı için panoya HİÇ
            # ulaşmıyordu — `app.js` `_gapRows` bu yüzden bloğu korumalı okuyup yokluğunu normal
            # sayıyor (4532'deki not). Kapanan boşluk burasıdır. Diğer iki hâlde blok teşhis
            # TAŞIMAZ (`hata` None'dır, hüküm zaten `durum`dan okunur); onların kopyası minimal
            # fark uğruna bit-bit AYNI kalır.
            kopya["seans"] = rapor["seans"]
            if not _GAP_CALENDAR_WARNED:
                _GAP_CALENDAR_WARNED = True
                obs.warn("gap_scan_calendar_unavailable", gun=rapor["gun"],
                         error=rapor["seans"]["hata"],
                         detail="XNYS takvimi okunamadı — seans-içi boşluk taraması bu turda "
                                "ÖLÇÜLEMEDİ: beklenti üretilemediği için eksiklik de ölçülemez ve "
                                "boş boşluk listesi 'boşluk yok' DEĞİLDİR (hüküm verilmedi). "
                                "Günlük döngü etkilenmez; süreç başına bir kez kaydedilir")
        _state["intraday_gap"] = kopya
        return rapor
    gorulen = list(_state.get("intraday_gap_seen") or [])
    yeni = 0
    for b in rapor.get("bosluklar") or []:
        imza = f"{rapor['gun']}|{b['tur']}|{b['sembol'] or '*'}|{b['baslangic']}"
        if imza in gorulen:
            continue
        gorulen.append(imza)
        yeni += 1
        obs.warn("intraday_gap_detected", tur=b["tur"], sembol=b["sembol"], gun=rapor["gun"],
                 aralik=f"{b['baslangic'][11:16]}-{b['bitis'][11:16]}Z", eksik_dk=b["eksik_dk"],
                 beklenen=b["beklenen"], gelen=b["gelen"], pencere_dk=rapor["esik"]["pencere_dk"],
                 detail=("seans içinde HİÇ bar gelmeyen dakika penceresi — akış kesintisi; "
                         "mrd:bars bir RING'tir, o dakikalar geri gelmez"
                         if b["tur"] == "akis" else
                         "sembol deliğin iki yanında dakika dakika akıyordu ama arada sustu"))
    _state["intraday_gap"] = {**{k: rapor[k] for k in
                                 ("durum", "gun", "olculdu", "pencere", "sembol", "gelen_bar",
                                  "bozuk_satir", "bosluk_sayisi", "esik")},
                              "bosluklar": (rapor.get("bosluklar") or [])[:8], "yeni_uyari": yeni}
    _state["intraday_gap_seen"] = gorulen[-GAP_SEEN_MAX:]
    return rapor


def advance_once() -> dict:
    """Run ONE daily cycle to the latest available bar if a new session has closed. Safe to call
    manually (a dashboard button) or from the loop. No-ops when already current or halted."""
    if not _run_lock.acquire(blocking=False):
        return {"status": "busy"}
    try:
        _state["last_tick"] = _now()
        from . import watchdog
        watchdog.beat("scheduler_poll")
        watchdog.check_and_alarm()
        try:
            _intraday_gap_check()
        except Exception as e:
            # YASA 4: bu düşerse akış kesintisi YENİDEN sessizleşir — kontrolün kendisi kaybolur ve
            # pano "boşluk yok" ile "bakılmadı"yı ayıramaz. Kontrol çağıranı DÜŞÜREMEZ (günlük döngü
            # akış sağlığına bağlı değildir), ama sessiz de kalamaz.
            from . import obs as _obs_gap
            _obs_gap.warn("intraday_gap_check_failed", error=f"{type(e).__name__}: {e}",
                          detail="seans-içi boşluk taraması koşmadı — akış kesintisi bu turda ÖLÇÜLMEDİ")
            _state["intraday_gap"] = {"durum": "olculemedi", "hata": f"{type(e).__name__}: {e}"}
        if health.halted():
            _persist()
            return {"status": "halted"}
        last_closed = _last_closed_session()
        pf = store.read_json("portfolio.json", {})
        already = pf.get("last_date")
        from . import dataset, loop
        # Refetch from the network AT MOST ONCE per newly-closed calendar session — not every poll (M2). The
        # old dedup compared the calendar session (always ahead) against the last DATA bar (lagging free
        # feed), so they never converged and every 300s poll did a full ~50-ticker use_cache=False refetch
        # that then no-op'd daily_cycle (measured 61 cache-bypassing refetches — rate-limit/ban risk).
        # ---- MERDİVEN, ADIM 0: SON TARİH KONTROLÜ ----
        # Kovaladığımız seansın barı gelmeden BİR SONRAKİ seans kapandıysa son tarih dolmuştur.
        # Terminal ilan ve alarm YALNIZ burada; merdivenin hiçbir ara adımı "pes etti" demez.
        # ÇÖZÜLMÜŞLÜK ÖLÇÜTÜ `refetch_chase`TİR, `last_refetch_session` DEĞİL: sık faz dolduğunda
        # bayrak yanar (poll'ler cache-only'ye döner) ama kovalama SÜRER — iki alan o noktada eşit
        # olur. Bayrağa bakan bir kapı, terminal atlamayı hiç ilan edemezdi (sessiz sonsuz kovalama).
        # Kovalama YALNIZ iki yerde kapanır: bar geldiğinde (chase=None) ve burada (son tarih).
        _chase = _state.get("refetch_chase")
        _tried = int(_state.get("refetch_attempts") or 0) + int(_state.get("refetch_sparse_attempts") or 0)
        if last_closed and _chase and _chase != last_closed and _tried > 0:
            # HİÇ SORMADIĞIMIZ SEANS HAKKINDA HÜKÜM VERİLMEZ: `_tried == 0` ise o seansı bu durumda
            # bir kez bile çekmeye çalışmadık (taze süreç + kalıntı kovalama). "Kaynak yayınlamadı"
            # demek, sormadan suçlamak olurdu — `source_error` ≠ `symbol_unknown` ayrımının ikizi.
            _declare_terminal_skip(_chase)
        # ---- MERDİVEN, ADIM 1: YENİ SEANS → SAYAÇLAR O SEANSA AİTTİR ----
        if last_closed and _state.get("refetch_chase") != last_closed and \
                _state.get("last_refetch_session") != last_closed:
            _state.update(refetch_chase=last_closed, refetch_attempts=0,
                          refetch_sparse_attempts=0, refetch_next_at=None)
            # BAKIM YOLU (temizlik turu 2026-07-30): `massive.reset_cache()` — süreç-içi anlık
            # görüntü memosu + başarısızlık soğuması. AV BULGUSU: üretim çağıranı YOKTU, yalnız
            # testler çağırıyordu; docstring'i "testler, gün dönümü" diyordu ama GÜN DÖNÜMÜ diye
            # bir çağıran hiç yazılmamıştı. EMEKLİ EDİLMEDİ, BAĞLANDI — ölçülmüş gerekçe:
            #   * BAYATLIK riski YOK: `_MEM_SNAPSHOT` ve `_FAIL_AT` ikisi de TARİHE anahtarlı, yani
            #     gün dönmesi zaten yanlış veri servis edemez. Yani docstring'in gerekçesi geçersiz.
            #   * AMA SIZINTI GERÇEK: memo {tarih: {~12.400 sembol: bar}} biçiminde ve 7/24 koşan
            #     worker'da sorgulanan HER tarih için birikiyor. Aylarca koşan bir süreçte bu, hiç
            #     boşalmayan bir bellek defteridir (A1: 12GB, worker uvicorn'la aynı süreçte).
            # NEDEN TAM BURASI: yeni seansın kovalaması BAŞLARKEN, o seans için henüz hiçbir çekim
            # yapılmadan. Maliyet SIFIRA yakın — temizlenen memo bir sonraki `snapshot()` çağrısında
            # ÖNCE DİSKTEN (`massive_grouped_last.json`) geri doldurulur, ağa çıkmaz.
            try:
                from .adapters import massive as _ms0
                _ms0.reset_cache()
            except Exception as e:
                from . import obs as _obs0
                _obs0.warn("massive_cache_reset_failed", session=last_closed,
                           error=f"{type(e).__name__}: {e}",
                           detail="süreç-içi anlık görüntü memosu boşaltılamadı — bellek birikebilir")
        # ---- MERDİVEN, ADIM 2: BU POLL AĞA ÇIKACAK MI? ----
        # SIK FAZ: bayrak yanmamışsa her poll (eski davranış, eski alan, eski pano halkası).
        # SEYREK FAZ: bayrak yandı ama kovalama sürüyor → 30-60 dakikada bir tek deneme.
        _chasing = bool(_state.get("refetch_chase")) and \
            _state.get("refetch_chase") == last_closed
        _dense = last_closed is not None and last_closed != _state.get("last_refetch_session")
        _sparse = bool(_chasing and not _dense and _sparse_due())
        fresh = _dense or _sparse
        if fresh and last_closed and _state.get("last_repair_session") != last_closed:
            _repair_once_per_session(last_closed)     # onarım/kalibrasyon: seans başına bir kez
        # load_LIVE: REPLAY_UNIVERSE + Finviz'in bugünkü keşfi (yalnız canlı ileri-yürüyen yol;
        # replay/yansıma load() kullanır, look-ahead karantinası için — bkz. dataset.load_live).
        # `session`: aynı-akşam bacağının kapısı — YALNIZ gerçekten KAPANMIŞ ve üstünden 16 dakika
        # geçmiş seans adı verilir (sip tarihsel penceresi + kısmî bar koruması, bkz. _leg_ready).
        bars, index = dataset.load_live(use_cache=not fresh, session=_leg_ready(last_closed))
        if fresh:
            # Consume the once-per-session flag ONLY when the just-closed session's bar actually ARRIVED.
            # Sources publish EOD with lag; burning the flag on a fetch that returned yesterday's data
            # meant the new bar could only enter at the NEXT session's refetch — candidates would be
            # evaluated a full day late. Bounded retry: keep the flag hot (max 8 attempts) until the
            # feed publishes, then settle into cache-only polls.
            # "BAR GELDİ Mİ" SORUSU EVRENE SORULUR, SPY'A DEĞİL (2026-07-22 — uygulamayı kilitleyen hata).
            # Eskiden yalnız endeksin (SPY) son barına bakılıyordu. SPY EOD'yi erken yayınlayan
            # azınlıktandır: canlıda 2026-07-21 barı 250 sembolün 46'sında vardı ama SPY onlardan
            # biriydi → bayrak İLK denemede tükeniyor, kalan 204 sembol bir daha hiç çekilmiyordu.
            # Sonra motorun kapsama kapısı "%18" deyip bir önceki seansa düşüyor, o seans da zaten
            # işlenmiş olduğu için döngü `noop` dönüyordu. Uygulama bu yüzden HİÇ ilerlemiyordu ve
            # hiçbir istisna fırlamıyordu. Bu, motorda düzelttiğimiz evren-kapsaması hatasının veri
            # hattındaki ikizi: aynı yasa iki yerde, biri güncellenmiş diğeri değil.
            # Ölçüt motorunkiyle AYNI eşiktir (loop.UNIVERSE_MIN_COVERAGE) — tek yasa, tek ölçüm.
            got = str(index["date"].iloc[-1].date()) if len(index) else None
            _cov = _session_coverage(bars, last_closed)
            _need = getattr(loop, "UNIVERSE_MIN_COVERAGE", 0.90)
            _arrived = _cov >= _need
            _state["last_refetch_coverage"] = round(_cov, 3)
            _state["refetch_latest_bar"] = got
            if _arrived:
                # BAR GELDİ: sık faz bayrağı yanar (poll'ler cache-only'ye döner) ve kovalama biter.
                _gec = bool(_sparse or int(_state.get("refetch_sparse_attempts") or 0))
                _state.update(last_refetch_session=last_closed, refetch_attempts=0,
                              refetch_chase=None, refetch_sparse_attempts=0, refetch_next_at=None)
                if _gec:
                    try:
                        from . import obs
                        # GEÇ GELEN BAR SESSİZ KALMAZ: merdivenin işe yaradığının kanıtı budur.
                        # Eski yasada bu satırın karşılığı SAHTE bir "SEANS ATLANDI" alarmıydı.
                        obs.log("session_bar_arrived_late", session=last_closed, latest_bar=got,
                                universe_coverage=round(_cov, 3), required=_need,
                                sparse_attempts=int(_state.get("refetch_sparse_attempts") or 0),
                                detail="seans barı sık fazdan SONRA geldi — merdiven yakaladı, "
                                       "seans atlanmadı")
                    except Exception:  # sessiz-yutma: kayıt kanalı düştü; bayrak zaten yandı
                        pass
            elif _dense:
                attempts = int(_state.get("refetch_attempts") or 0) + 1
                _state["refetch_attempts"] = attempts
                if attempts >= DENSE_ATTEMPTS:
                    # SIK FAZ KAPANDI — AMA PES EDİLMEDİ. Bayrak yanar (her 300 sn'de bir 250
                    # sembollük önbellek-baypas süpürmesi sağlayıcıyı döverdi; o disiplin AYNEN
                    # korunuyor), kovalama SEYREK fazda son tarihe kadar sürer. Eski yasada bu
                    # nokta "kalıcı atlama + alarm" idi ve tam da burada 164 sahte alarm doğdu.
                    _state["last_refetch_session"] = last_closed
                    _state["refetch_sparse_attempts"] = 0
                    _schedule_sparse()
                    try:
                        from . import obs
                        obs.log("session_bar_retry_sparse", session=last_closed, latest_bar=got,
                                universe_coverage=round(_cov, 3), required=_need,
                                dense_attempts=attempts, next_try=_state.get("refetch_next_at"),
                                detail="sık faz doldu; kovalama 30-60 dk aralıklarla SÜRÜYOR — "
                                       "terminal atlama yalnız bir sonraki seansın kapanışında ilan edilir")
                    except Exception:  # sessiz-yutma: kayıt kanalı düştü; merdivenin kendisi planlandı
                        pass
            else:
                _state["refetch_sparse_attempts"] = int(_state.get("refetch_sparse_attempts") or 0) + 1
                _schedule_sparse()
            try:
                from . import reflect
                reflect.clear_wf_caches()   # new bars revision → stale walk-forwards must not survive (#30)
            except Exception as e:
                # YASA 4 (2026-07-21): bu sessizlik #30'u GERİ GETİRİR — barlar yeniden çekildikten
                # sonra önbellek temizlenmezse motor ARTIK VAR OLMAYAN barlara ait walk-forward'la
                # karar verir ve sonuç tutarlı ama YANLIŞ görünür. Temizlik yine denenmez, ama sessiz kalmaz.
                from . import obs as _obs_wf
                _obs_wf.warn("wf_cache_clear_failed", error=f"{type(e).__name__}: {e}",
                             detail="bayat walk-forward önbelleği hayatta kalmış olabilir")
            try:                             # kazanç takvimi: haftada bir tazele (PEAD çapası + karartma)
                import datetime as _dt
                wk = _dt.date.today().isocalendar()[:2]
                # PES-FRENİ ARTIK HAFTA DEĞİL GÜN (2026-08-03, Rol-1 A1b — aşağıdaki "İKİNCİSİ HÂLÂ
                # AÇIK" maddesinin kapanışı): sabır sınırı korunur (günde en çok 5 deneme) ama fren
                # ERTESİ GÜN açılır, 7 gün sonra değil.
                _bugun = _dt.date.today().isoformat()
                if _state.get("earnings_week") != list(wk) and _state.get("earnings_gaveup_day") != _bugun:
                    # öneri #5a: hafta bayrağı yalnız VERİ GELİNCE tüketilir — 429/kesintide eski kod
                    # haftayı boşa yakıyordu ve takvim 7 gün daha boş kalıyordu. Sınırlı sabır:
                    # haftada en çok 5 deneme, sonra pes edildiği LOGLANIR (sessiz açlık yok).
                    from . import earnings, obs, watchdog
                    from .adapters.data import REPLAY_UNIVERSE
                    att = _state.get("earnings_attempts", 0) + 1
                    n = earnings.refresh(list(REPLAY_UNIVERSE))
                    if n > 0:
                        watchdog.beat("earnings_refresh")
                        _state["earnings_week"] = list(wk)
                        _state["earnings_attempts"] = 0
                        _state.pop("earnings_gaveup_day", None)   # veri geldi → gün freni kalkar
                        obs.log("earnings_calendar_refreshed", rows=n)
                    elif att >= 5:
                        # ---- ÖRTÜK ZAMAN VARSAYIMI, ARTIK YAZILI (sınıf avı, 2026-07-30) --------
                        # T+1 kusurunun sınıfı buydu: "kodda örtük yayın-zamanı varsayımı". Buradaki
                        # varsayım ÖLÇÜLDÜ ve marjı DAR çıktı — davranış DEĞİŞTİRİLMEDİ, yalnız
                        # sayı yazıldı ki bir dahaki karar tahminle değil ölçümle verilsin.
                        # KALICI HÂLE GETİRİLDİ (2026-08-01): üç girdi (ileri pencere / kadans /
                        # karartma) artık `earnings.py`de ADLANDIRILMIŞ sabitler ve marj onlardan
                        # TÜRETİLİYOR (`earnings.margin_days()` → bugün 21-7-5 = 9 gün). Sayı
                        # buradan da, `coverage()`ten de AYNI türetmeden okunur; üç sayıdan biri
                        # değişirse uyarı kendiliğinden doğruyu söyler.
                        # KADANSIN SAHİBİ BU DAL: `REFRESH_CADENCE_DAYS = 7`in gerçek karşılığı
                        # yukarıdaki isocalendar kapısıdır — sabit oraya bakarak yazıldı.
                        #   * BU DAL MARJI TÜKETİR: hafta damgası pes ederken de İLERLER, yani
                        #     bir sonraki deneme 7 gün daha ileridedir → ileri kapsama 0'a iner.
                        #     `in_blackout` veri yokken FAIL-OPEN'dır (bilerek: bilgi yokken
                        #     bloklamaz), dolayısıyla o hafta karartma guard'ı HERKES için kapanır
                        #     ve motor bilanço gününe pozisyonla girebilir.
                        # İKİ UCUZ ÇÖZÜM VARDI (davranış kararı, Rol-1). BİRİNCİSİ UYGULANDI
                        # (2026-08-01): ileri pencere `REFRESH_FWD_DAYS` 14 → 21 (Nasdaq ucu
                        # ANAHTARSIZ ve gün-başına sorgulanıyor — kota maliyeti ≈ 0), marj 2 → 9
                        # gün. Yani bu dal pes etse bile ileri kapsama bir hafta daha dayanır.
                        # İKİNCİSİ DE UYGULANDI (2026-08-03, Rol-1 A1b): pes ederken HAFTA DAMGASI
                        # ARTIK YAKILMIYOR. Eski satır (`earnings_week = wk`) haftayı tüketiyordu ve
                        # ardışık iki pes ileri kapsamayı 0'a indiriyordu — yani sabır sınırı, tam da
                        # korumaya çalıştığı kapıyı kapatıyordu. Yerine GÜN damgası: sabır sınırı
                        # aynen korunur (günde en çok 5 deneme, sessiz açlık yok) ama fren ERTESİ GÜN
                        # açılır. Kota etkisi yok — pes eden dal zaten satır getirmiyor; kazanılan şey
                        # bir sonraki denemenin 7 gün değil 1 gün ötede olmasıdır.
                        # NOT: bu dal artık takvimin KENDİSİNİ de bağlıyor — ileri kapsama karartma
                        # ufkunun altına inerse `earnings.calendar_untrustworthy()` devreye girer ve
                        # karar turu GO yerine REVIEW üretir (fail-open sessizce açık kalmaz).
                        _state["earnings_gaveup_day"] = _bugun
                        _state["earnings_attempts"] = 0
                        _cov = earnings.coverage(list(REPLAY_UNIVERSE)) or {}
                        obs.warn("earnings_calendar_gave_up", attempts=att,
                                 blackout_days=getattr(earnings, "BLACKOUT_DAYS", None),
                                 marj_gun=_cov.get("marj_gun"), ileri_gun=_cov.get("ileri_gun"),
                                 ileri_kapsama_gun=_cov.get("future_dates"),
                                 yeniden_deneme="yarın (hafta damgası YAKILMADI)",
                                 detail="FMP 5 denemede satır vermedi — takvim bugün boş kalacak, "
                                        "deneme YARIN sürer; ileri kapsama karartma ufkunun altına "
                                        "inerse karar turu GO yerine REVIEW üretir "
                                        "(earnings.calendar_untrustworthy)")
                    else:
                        _state["earnings_attempts"] = att
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
            try:                             # #3: haftalık silahlanma değerlendirmesi (uyuyan→ölç→silahla)
                import datetime as _dt3
                wk3 = list(_dt3.date.today().isocalendar()[:2])
                if _state.get("arming_week") != wk3:
                    from . import arming, watchdog as _wd3
                    arming.evaluate(bars, index)          # bars zaten elimizde — walk maliyeti yalnız eşik geçilirse
                    _wd3.beat("arming_eval")
                    _state["arming_week"] = wk3
            except Exception as e:
                from . import obs as _obs3
                _obs3.warn("arming_eval_failed", error=f"{type(e).__name__}: {e}")
            try:                             # v11 #2: haftalık öz-değerlendirme (sentez + bildirim)
                import datetime as _dt6
                wk6 = list(_dt6.date.today().isocalendar()[:2])
                if _state.get("selfreview_week") != wk6:
                    from . import selfreview
                    selfreview.weekly()
                    _state["selfreview_week"] = wk6
            except Exception as e:
                from . import obs as _obs6
                _obs6.warn("selfreview_failed", error=f"{type(e).__name__}: {e}")
            try:    # K1 (2026-07-30): haftalık YETİM HİPOTEZ SÜPÜRMESİ — kusur #1 onarımı raftaydı
                # `rollback.sweep_orphan_hypotheses` 2026-07-22'de yazıldı, test edildi ve HİÇBİR
                # KADANSA ASILMADI: repo genelinde tek çağıranı testlerdi (loop/scheduler/reflect/api
                # hiçbirinde yok). Onarım kod olarak vardı, süreç olarak yoktu.
                # NEDEN ÖNEMLİ: `evaluate_outcomes` yalnız GÜNCEL sürüme bakar. v2 min_sample'a
                # ulaşmadan v3 ship edilirse v2'nin hipotezi SONSUZA KADAR `live` kalır ve öğrenme
                # muhasebesi sessizce şişer (canlı kanıt: H00029, H00026). Her ship'te yeniden birikir.
                # NEDEN BURADA: ship yolu reflect.py'de, bu turda başka bir ajanın yüzeyi. Haftalık
                # kadans akranlarıyla (arming_eval / selfreview / revision) aynı desende ve
                # süpürmenin doğru sıklığı bu — süpürme İDEMPOTENT, yalnız superseded olanı kapatır.
                import datetime as _dt7
                wk7 = list(_dt7.date.today().isocalendar()[:2])
                if _state.get("orphan_sweep_week") != wk7:
                    from . import rollback as _rb7
                    _kapanan = _rb7.sweep_orphan_hypotheses()
                    _state["orphan_sweep_week"] = wk7
                    if _kapanan:
                        from . import obs as _obs7
                        _obs7.log("orphan_hypotheses_swept", n=len(_kapanan),
                                  ids=[str(x) for x in _kapanan][:10],
                                  detail="superseded hipotezler terminal duruma kapatıldı "
                                         "(min_sample'a ulaşmadan aşılmış sürümler)")
            except Exception as e:
                # YASA 4: süpürme düşerse yetimler birikmeye DEVAM eder ve muhasebe şişer — sessiz kalamaz.
                from . import obs as _obs7b
                _obs7b.warn("orphan_sweep_failed", error=f"{type(e).__name__}: {e}")
            try:    # NOUS SİSTEM-DEĞERLENDİRME KATMANI B (ROADMAP §3.2, 2026-07-30) — haftalık
                # MEKANİZMA değerlendirmesi. Operatör yönü: "bütün mekanizmaları değerlendirip
                # güncellenmesi gerekenleri nous bulmalı; sistem kısıtlı alanda kalmadan sürekli
                # kendini geliştirmeli."
                # NEDEN BURADA: akranlarıyla (arming_eval / selfreview / orphan_sweep / revision)
                # AYNI desende ve doğru sıklık haftalıktır — telemetrinin girdileri (kapanmış işlem,
                # kapı kaydı, aşınma sayacı) günlük ölçekte anlamlı değişmiyor, ve her koşu bir LLM
                # çağrısı + potansiyel bir ölçüm sırasıdır.
                # NE YAPMAZ: hiçbir şeyi UYGULAMAZ. En fazla bir parametre demetini H4'ün 3/hafta
                # bütçesi içinde ölçüm sırasına sokar (ayrı bütçe AÇILMAZ); çekirdek hakkındaki
                # öneriler YALNIZ rapora gider (Katman D).
                import datetime as _dt8
                wk8 = list(_dt8.date.today().isocalendar()[:2])
                if _state.get("nous_eval_week") != wk8:
                    from . import nous_eval as _ne8
                    # HAFTA DAMGASI HER DURUMDA İLERLER: LLM erişimi yoksa koşu "kosulamadi" olarak
                    # kaydedilir (şablon öneri UYDURULMAZ) ve her poll'de yeniden denemek kotayı
                    # boşa yakardı — hermes'in soğuma defteri deseninin aynısı.
                    _state["nous_eval_week"] = wk8
                    _res8 = _ne8.haftalik_degerlendirme()
                    from . import obs as _obs8
                    _k8 = _res8.get("kosu") or {}
                    _obs8.log("nous_eval_week", durum=_k8.get("durum"), beyin=_k8.get("beyin"),
                              kabul=_k8.get("n_kabul"), dusen=_k8.get("n_dusen"),
                              kuyruk=_k8.get("n_kuyruk"), devreden=len(_k8.get("devreden") or []))
            except Exception as e:
                # YASA 4: değerlendirme düşerse sistem kendi kör noktasına kör kalmaya DEVAM eder —
                # sessiz kalamaz. Hafta damgası yukarıda ilerledi, yani arıza bir sonraki haftaya
                # kadar tekrarlanmaz ve uyarı defterde tek satır olur.
                from . import obs as _obs8b
                _obs8b.warn("nous_eval_failed", error=f"{type(e).__name__}: {e}")
            try:    # ÖĞRENME KADANSI (2026-07-30) — SEANS başına bir kez, bar varışından BAĞIMSIZ.
                # NEDEN HAFTALIK DEĞİL (akranlarının aksine): girdileri GÜNLÜK ölçekte değişiyor —
                # her seans yeni kapanış, yeni karşı-olgusal satır, yeni plan. Haftalık bir antrenman
                # altı gün bayat bir modelle tahmin üretmek demekti. Ve maliyeti akranlarınınkinden
                # düşük: antrenman saf-numpy (kotasız), Eksen-2 deterministik (kotasız), yalnız dolgu
                # kota yakar ve o zaten KENDİ bütçesinden türetilmiş bir tavanla koşar.
                if _state.get("learn_session") != last_closed and last_closed:
                    _learning_cadence(last_closed)
            except Exception as e:
                # YASA 4: kadansın KENDİSİ düşerse üç mekanizma birden sessizce durur — en pahalı
                # sessizlik sınıfı. Damga İLERLEMEZ (iç adımlar kendi korumalarında), yani bir
                # sonraki poll yeniden dener.
                from . import obs as _obsL
                _obsL.warn("learning_cadence_failed", session=last_closed,
                           error=f"{type(e).__name__}: {e}",
                           detail="antrenman/Eksen-2/dolgu üçü birden koşmadı")
            try:    # Y4 VERİ TOPLAMA (2026-07-30 temizlik turu) — SEANS başına bir kez.
                # NEDEN ÖĞRENME KADANSININ ARDINDAN: ikisi de seans-sonrası ve ikisi de kotalı,
                # ama öğrenme kadansı KARAR üretir (terfi hükmü, öneri), Y4 yalnız DEFTER doldurur.
                # Kıt kaynak (FMP kotası) önce karar üretene gider — `_learning_cadence`in kendi
                # içindeki sıralamasıyla aynı ilke.
                if _state.get("y4_session") != last_closed and last_closed:
                    _y4_collect(last_closed)
            except Exception as e:
                # YASA 4: toplama düşerse Y4 penceresi sessizce donar ve "tüketici ne zaman
                # bağlanabilir?" sorusu cevapsız kalır. Damga İLERLEMEZ → sonraki poll yeniden dener.
                from . import obs as _obsY
                _obsY.warn("y4_collect_failed", session=last_closed,
                           error=f"{type(e).__name__}: {e}",
                           detail="içeriden işlem + kısa pozisyon toplaması koşmadı")
            try:    # HAFTALIK DOĞRULAMA/KAYMA ÜÇLÜSÜ (2026-07-30 temizlik turu).
                # Akranlarıyla (arming_eval / selfreview / orphan_sweep / nous_eval / revision)
                # AYNI `isocalendar` deseni. HAFTA DAMGASI BLOĞUN İÇİNDE ilerler: üç ayak da kendi
                # korumasında olduğu için buraya düşen bir istisna KADANSIN kendisinin arızasıdır
                # ve o durumda hafta yakılmamalıdır.
                import datetime as _dt9
                wk9 = list(_dt9.date.today().isocalendar()[:2])
                if _state.get("validation_week") != wk9:
                    _weekly_validation(wk9)
            except Exception as e:
                from . import obs as _obs9
                _obs9.warn("weekly_validation_failed", error=f"{type(e).__name__}: {e}",
                           detail="kanıt raporu + massive doğrulama + yasa kayması üçü birden koşmadı")
            try:                             # v10 #5: haftalık skill revizyon taslağı (en fazla 1; operatör onaylı)
                import datetime as _dt5
                wk5 = list(_dt5.date.today().isocalendar()[:2])
                if _state.get("revision_week") != wk5:
                    from . import skill_evolve
                    skill_evolve.weekly_draft()
                    _state["revision_week"] = wk5
            except Exception as e:
                from . import obs as _obs5
                _obs5.warn("skill_revision_week_failed", error=f"{type(e).__name__}: {e}")
            try:                             # öneri #5b: SPY çapraz-doğrulama (bağımsız kaynak, seansta 1 kez)
                from .adapters import data as _da
                from . import watchdog as _wd4
                store.write_json("index_crosscheck.json", _da.crosscheck_index())
                _wd4.beat("crosscheck")
            except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
                pass
        # process only when the latest AVAILABLE bar is genuinely newer than what we've already booked
        latest_bar = str(index["date"].iloc[-1].date()) if len(index) else None
        if latest_bar is not None and already is not None and latest_bar <= already:
            # The 'current' path is the steady state for ~24h between sessions — it must still refresh
            # the heartbeat, else health.stale(900) reads true nearly all day: /healthz 503s and the
            # Hermes standby loop is gated off exactly when it has time to think (audit #13). Re-write
            # the previous heartbeat's fields with a fresh ts (write_heartbeat re-stamps ts/mode/halted).
            hb = store.read_json("heartbeat.json", {})
            if hb.get("regime") is None:
                # canlıda görüldü (2026-07-20): panelden HALT, nabzı yalnız note ile yazınca rejim/bütçe
                # alanları siliniyor ve bu yol None'ları bir sonraki döngüye dek sadakatle taşıyordu —
                # HUD "rejim: yok" gösteriyordu. Kaynağı hâlâ diskte duran regime.json'dan geri doldur.
                rj = store.read_json("regime.json", {})
                if rj.get("regime"):
                    hb["regime"] = rj["regime"]
                    if hb.get("exposure_budget_pct") is None:
                        hb["exposure_budget_pct"] = rj.get("exposure_budget_pct")
            health.write_heartbeat(**{k: v for k, v in hb.items()
                                      if k not in ("ts", "mode", "autonomy_level", "halted")})
            _persist()
            # GÖRÜŞ TELAFİSİ (2026-07-22): danışma katmanı bir seansı kaçırırsa döngü o seansı ikinci
            # kez işlemez ve o gün SONSUZA KADAR görüşsüz kalır — LLM görüş↔sonuç kalibrasyonu da
            # hiç birikmez. "Güncel" turda ucuz bir telafi: planı olup görüşü olmayan son seansı incele.
            try:
                from . import hermes as _h
                _h.review_backlog(max_sessions=1)
            except Exception as e:
                from . import obs as _o
                _o.warn("candidate_review_backlog_failed", error=f"{type(e).__name__}: {e}",
                        detail="bu seans görüşsüz kalabilir — LLM kalibrasyonu beslenmiyor")
            # ÖĞRENME ANTRENMANI (sprint) KADANSI — 2026-07-30.
            # NEDEN TAM BURASI, `fresh` bloğunda DEĞİL: bu dal "işlenecek yeni seans YOK" dalıdır,
            # yani bu poll'de `loop.daily_cycle` KOŞMAYACAK. Sprint 4 işçiyle walk-forward açar;
            # `fresh` bloğuna koysaydım aynı `advance_once` çağrısı birkaç satır sonra EOD döngüsünü
            # başlatırdı ve ikisi 8 çekirdeği paylaşırdı — addendum'un yasakladığı hâlin ta kendisi.
            # Kalan kapılar (gece dilimi, haftalık/taze-aday tetiği, aktif sprint, canlı arama)
            # `sprint.should_run` içinde ve HEPSİ adıyla raporlanır.
            # MEŞGULİYET SİNYALİ: bar kovalaması sürüyorsa (`refetch_chase`) veri hattı ağa çıkıyor
            # demektir; sprint'i o pencereye sokmak, kovalamayı yavaşlatmaktır.
            # DÖRDÜNCÜ KAPI — YALNIZ DAEMON DÖNGÜSÜ SPRINT BAŞLATIR (2026-07-30, ölçülmüş kaza).
            # `advance_once`ın İKİ çağıranı var: bu modülün `_run` daemon döngüsü ve panonun ELLE
            # TİK düğmesi (`api.py:1823`). Kadans bu ayrımı gözetmeyince şu oldu: testler
            # `advance_once()`ı doğrudan çağırıyor ve saat 22:00'yi geçtiği anda gece kapısı
            # AÇILDIĞI için `maybe_start` gerçekten bir alt süreç başlattı — canlı state'i kum
            # havuzuna kopyalayan, 4 işçilik `meridian.sprint_run`. Test paketi 18:00-21:00 arası
            # yeşil, 22:00'den sonra kırmızıydı: SAAT BAĞIMLI bir suite, geçtiğinde hiçbir şey
            # kanıtlamaz (sıra bağımlılığının daha sinsi kuzeni — gece yarısına kadar görünmez).
            # KAPI TESTLER İÇİN DEĞİL, DOĞRU OLDUĞU İÇİN BURADA: operatör "bir tur ilerlet"
            # düğmesine bastığında dakikalarca sürecek, 4 çekirdek yiyen bir antrenman başlatmayı
            # İSTEMEMİŞTİR. Elle tik bir tur ilerletir; sprint'in elle tetiği ayrı bir düğmedir
            # (`/api/sprint/start`) ve o hiçbir kapıya uğramaz. VM worker (`run.py`) zaten
            # `loop.daily_cycle`ı doğrudan çağırır, zamanlayıcıya hiç uğramaz — etkilenmez.
            try:
                from . import sprint as _sp
                _mesgul = ("bar_kovalamasi" if _state.get("refetch_chase")
                           else None if (_thread and _thread.is_alive()) else "elle_tik")
                _state["last_sprint_cadence"] = _sp.maybe_start(mesgul=_mesgul)
            except Exception as e:
                # YASA 4: kadans düşerse öğrenme antrenmanı SESSİZCE elle-tetiğe geri döner —
                # yani bu turun kapattığı deliğin yeniden açılması. Sessiz kalamaz.
                from . import obs as _os2
                _os2.warn("sprint_cadence_failed", error=f"{type(e).__name__}: {e}",
                          detail="öğrenme antrenmanı otomatik başlatılamadı — kalibrasyon noktası "
                                 "üreten tek hızlı yol yine elle tetiğe bağlı")
            return {"status": "current", "last_date": already, "latest_bar": latest_bar}
        # canlıda görüldü (2026-07-16 seansı HİÇ işlenmedi): iki poll arasına birden çok seans sığarsa
        # yalnız SONUNCUSU işleniyordu — aradaki seansın adayları, karşı-olgusal satırları ve silahlı
        # planların dolum günü kayıtsız kayboluyordu (huni koşumu 07-16'da gerçek bir VCP adayı buldu).
        # Sırayla yetiş: işlenmemiş HER seans kendi tarihine kırpılmış veriyle (on_date) işlenir; bir
        # seans patlarsa portfolio.last_date orada kalır ve bir sonraki poll kaldığı yerden devam eder.
        if already is not None:
            todo = [s for s in (str(x.date()) for x in index["date"]) if s > already]
        else:
            todo = [latest_bar] if latest_bar else []
        summary = {}
        for s in todo:
            summary = loop.daily_cycle(bars, index, on_date=s)
            if len(todo) > 1:
                from . import obs as _obs7
                _obs7.log("catchup_session_processed", date=s, remaining=len(todo) - todo.index(s) - 1)
        _state["last_processed"] = summary.get("date", last_closed)
        _state["last_summary"] = summary.get("status")
        _state["cycles"] += 1
        _persist()
        return {"status": "advanced", "summary": summary, "sessions": todo}
    finally:
        _run_lock.release()


def _run(poll_seconds: int) -> None:
    _state.update(started_at=_now(), poll_seconds=poll_seconds)
    _persist()
    while not _stop.is_set():
        try:
            advance_once()
        except Exception as e:
            store.write_json(STATUS_FILE, {**_state, "error": f"{type(e).__name__}: {e}", "updated": _now()})
        _stop.wait(poll_seconds)
    _persist()


def start(poll_seconds: int = 300) -> dict:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return {"already_running": True}
        _rehydrate()          # tavan süreç ömrüne bağlı olamaz (bkz. _rehydrate gerekçesi)
        _stop.clear()
        _thread = threading.Thread(target=_run, args=(poll_seconds,), name="paper-scheduler", daemon=True)
        _thread.start()
    return {"started": True, "poll_seconds": poll_seconds}


def stop() -> dict:
    _stop.set()
    return {"stopping": True}


def status() -> dict:
    # AYNI-AKŞAM BACAĞININ DIŞ TÜKETİCİSİ (YASA 6, 2026-07-30). Defteri `adapters/data.py` yazar;
    # burası onu DIŞARIDAN okuyan tek yerdir → /api/hermes `scheduler` ve /api/scheduler üzerinden
    # panoya çıkar. Neden `data_quality.json` değil: `loop.daily_cycle` o dosyayı her seansta
    # sıfırdan yazıyor (tek sözlük literali) — oraya konan bir anahtar aynı turda silinirdi, yani
    # "birikim" orada yapısal olarak imkânsız (beyan edilmiş sapma; gerekçesi data.py'de yazılı).
    # ÖZET DÖNER, DEFTERİN TAMAMI DEĞİL: `provisional` bölümü 250 sembol taşıyabilir ve durum
    # ucunu şişirmek, okunmayan bir yüzey üretmenin en hızlı yoludur.
    from .adapters import data as _da
    from .adapters.data import SAME_EVENING_FILE
    _doc = store.read_json(SAME_EVENING_FILE, {}) or {}
    return {**_state, "active": bool(_thread and _thread.is_alive()),
            "latest_session": _last_closed_session(),
            "portfolio_last_date": store.read_json("portfolio.json", {}).get("last_date"),
            # ÖZET (ölçüm yoksa None — 0 DEĞİL); şekillendirme data.upgrade_divergence'ta TEK yerde
            "bar_upgrade": _da.upgrade_divergence(_doc)}
