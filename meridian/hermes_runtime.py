"""hermes_runtime.py — in-process supervisor for the Hermes reflection brain, for LOCAL running. On app
open (serve.sh sets MERIDIAN_AUTOSTART_HERMES=1) a daemon thread runs a standby loop: it watches the
heartbeat and reflects when `reflection_every` new trades have closed and the system is healthy (not
halted, not stale). The operator can also trigger one cycle on demand via reflect_now(). Every
reflection goes through reflect.submit → the backtest gate decides; the brain only proposes. A single
reflection lock guarantees the standby loop and a manual trigger never run two reflections at once.
Status mirrors to state/hermes_status.json for the dashboard's Hermes section."""
from __future__ import annotations
import datetime as dt
import os
import threading

from . import config, store, health, secrets, obs

STATUS_FILE = "hermes_status.json"
REFLECTION_MIN_DAYS = int(os.environ.get("HERMES_REFLECTION_MIN_DAYS", "30"))   # Phase 3 overfitting horizon
WARMUP_EVERY_POLLS = int(os.environ.get("MERIDIAN_WARMUP_EVERY_POLLS", "12"))   # ısınma sprinti sıklığı (poll)

# ---- ISINMA SPRİNTİ SÜRE TAVANI (WP-H/H11, 2026-07-31) -----------------------------------------
# 300 dk = 5 sa, ısınmanın NOMİNAL üst bandı (ölçülmüş aralık 1-5 sa). Tavan bir kısıtlama değil,
# ANOMALİ SINIRI: nominal bandın içinde kalan hiçbir koşum kesilmez; 5 saati aşan koşum tanım gereği
# artık nominal değildir ve döngüyü daha fazla rehin tutmasının hiçbir gerekçesi yoktur.
WARMUP_MAX_MIN_DEFAULT = 300


def _warmup_tavan_dk() -> float:
    """`HERMES_WARMUP_MAX_MIN` (dk) — HER ÇAĞRIDA okunur, modül yüklenirken DEĞİL.

    Neden çağrı anında: bu değer bir operatör kolu (canlıda bir bakım penceresinde daraltılmak
    istenebilir) ve modül-yükleme anında dondurulmuş bir env, süreç yeniden başlatılana kadar
    değişmez — yani kolun çevrildiği ama hiçbir şeyin değişmediği bir yanılsama üretirdi.

    BOZUK DEĞER SESSİZCE 0 OLMAZ: `float("abc")` istisnası yutulup 0'a düşülseydi tavan HER
    ısınmayı anında keserdi ve ısınma kadansı sessizce ölürdü — bekçi bile göremezdi, çünkü nabız
    atılmaya devam ederdi. Bozuk değer ADIYLA uyarılır ve varsayılana dönülür."""
    ham = os.environ.get("HERMES_WARMUP_MAX_MIN")
    if ham is None or not str(ham).strip():
        return float(WARMUP_MAX_MIN_DEFAULT)
    try:
        v = float(ham)
    except (TypeError, ValueError):
        obs.warn("hermes_warmup_max_min_gecersiz", value=str(ham)[:40],
                 fallback_min=WARMUP_MAX_MIN_DEFAULT,
                 detail="HERMES_WARMUP_MAX_MIN sayıya çevrilemedi — varsayılan tavana dönüldü; "
                        "0'a düşmek ısınma kadansını sessizce öldürürdü")
        return float(WARMUP_MAX_MIN_DEFAULT)
    if v <= 0:
        # 0/negatif = "tavan yok" DEĞİL, "her koşumu anında kes" olurdu. Operatör tavanı kaldırmak
        # isterse doğru kol devre dışı bırakmadır (MERIDIAN_WARMUP_SPRINTS=0), tavanı sıfırlamak değil.
        obs.warn("hermes_warmup_max_min_gecersiz", value=str(ham)[:40],
                 fallback_min=WARMUP_MAX_MIN_DEFAULT,
                 detail="HERMES_WARMUP_MAX_MIN sıfır ya da negatif — bu 'tavan yok' değil 'her "
                        "ısınmayı anında kes' anlamına gelirdi; varsayılan tavana dönüldü")
        return float(WARMUP_MAX_MIN_DEFAULT)
    return v


def _bg_ready_regime(trades: list, every: int, live_reg: str | None) -> str | None:
    """#2 REJİM-HEDEFLİ ARKA PLAN YANSIMASI: canlı rejimin ufku dolmadığında boşta beklemek,
    diğer rejimlerin BİRİKMİŞ kanıtını israf etmekti (chop'ta yaşarken trend_up defterinde 80+
    işlem kullanılmadan duruyordu). Ufku DOLU (katı-VE, rejim-dilimli) canlı-dışı rejimlerden,
    son arka-plan yansımasından beri EN ÇOK yeni işlem birikmişi seçilir. Güvenlik: ship yalnız
    params_by_regime[o rejim]'i değiştirir — canlı davranış rejim dönene dek değişmez ve o güne
    kadar kapı+defterde denetlenmiştir. Rejim başına taban: aynı kanıta ikinci kez yansıma yok."""
    baselines = _state.get("bg_reflect_by_regime") or {}
    best, best_n = None, 0
    for r in config.VALID_REGIMES:
        if r == live_reg:
            continue
        last_r = int(baselines.get(r, 0))
        if not _horizon_ok(trades, last_r, regime=r, min_trades=every):
            continue
        n_new = sum(1 for t in trades[last_r:] if str(t.get("regime")) == r)
        if n_new > best_n:
            best, best_n = r, n_new
    return best


def _warmup_sprint() -> None:
    """Boş-döngü ısınması (öneri #4): coordinate_descent_search'i SHIP ETMEDEN koştur — yalnız UCB
    önceliklerini + probe cache'ini ısıtmak için. Nothing ships (submit çağrılmaz). En iyi probe'un
    özeti hermes_status'a yazılır (görünürlük). Ağ/veri hatası sessizce yutulur — ısınma asla döngüyü
    kırmaz.

    WP-H/H11 (2026-07-31) — İKİ KUSUR BİRDEN KAPANIR, İKİSİ DE AYNI KÖKTEN:

      (1) POLL AÇLIĞI. Bu fonksiyon hermes bekleme döngüsünün KENDİ iş parçacığında koşar ve nominal
          süresi 1-5 saattir. O süre boyunca `_run` döngüsü bir sonraki tura dönemez, yani
          `watchdog.beat("hermes_poll")` ATILMAZ. Bekçinin `hermes_poll` penceresi 30 DAKİKAdır →
          ısınma her koştuğunda MECHANISM_STALE üretilir. Bu SAHTE bir alarmdır: mekanizma ölü değil,
          MEŞGULdür. Ve sahte alarmın maliyeti gerçek alarmdan yüksektir — operatörü alarm okumamaya
          eğitir. Çözüm: nabız artık sondadan sondaya, ısınmanın İÇİNDEN atılıyor. `hermes_poll`
          nabzının ısınma tarafından atıldığı bu yoruma yazılıdır: nabız "poll döngüsü turladı"
          demez, "hermes ipliği CANLI ve İLERLİYOR" der — bekçinin gerçekte sorduğu soru budur.

      (2) İPTAL EDİLEMEZLİK. 8 saati aşan bir ısınmada bekçinin elinde ALARM'dan başka araç yoktu.
          Artık aramanın kendisi bir süre tavanı taşıyor (`max_minutes`) ve tavana takılırsa KİBARCA
          kesiliyor — biten sondalarla dönüyor, kesinti damgalanıyor. Bekçi eşiği 8 saatte KALIR ve
          bu bilinçlidir: tavan 5 saat olduğuna göre 8 saatlik bir sessizlik artık "uzun sürdü"
          değil "tavan çalışmadı" demektir — yani eşik nihayet GERÇEK bir anomali ölçer.
    """
    try:
        from . import hermes, reflect, dataset
        from . import watchdog as _wd8
        bars, index = dataset.load()
        # #2: önce sıradaki muhtemel yansımaların incumbent'ları (global + canlı + ufku dolu arka plan
        # rejimi) — yansıma anında kapı beklemesin; sonra sonda ısınması.
        try:
            trades = store.read_jsonl("trades.jsonl")
            every = int((config.goal().get("reflection_every") or 5))
            live = store.read_json("regime.json", {}).get("regime")
            live = live if live in config.VALID_REGIMES else None
            bg = _bg_ready_regime(trades, every, live)
            reflect.prefill_incumbents(bars, index, [None, live, bg])
        except Exception as e:
            obs.warn("incumbent_prefill_failed", error=f"{type(e).__name__}: {e}")
        def _nabiz(i, total, *_a):
            """Her sonda bitiminde İKİ nabız. Mevcut `on_probe` dikişi yeniden kullanılır: aramaya
            ikinci bir geri-çağırma parametresi eklemek, aynı olayı iki kanaldan taşıyan bir
            ikizlik yaratırdı. Nabız yazımı `store.write_json`dur (birkaç ms) ve sonda başına bir
            kez olur — 40 sondalık bir turda toplam maliyet ölçülemeyecek kadar küçüktür."""
            _wd8.beat("warmup_sprint")     # ısınmanın KENDİ kadansı ilerliyor
            _wd8.beat("hermes_poll")       # poll ipliği MEŞGUL ama CANLI — sahte alarm burada biter

        _tavan = _warmup_tavan_dk()
        res = reflect.coordinate_descent_search(bars, index, budget=int(os.environ.get("HERMES_WARMUP_BUDGET", "10")),
                                                k_max=2, max_minutes=_tavan, on_probe=_nabiz)
        _wd8.beat("warmup_sprint")         # sonda HİÇ koşmadıysa da ısınma turladı: kadans nabzı düşmez
        _wd8.beat("hermes_poll")
        _state["last_warmup"] = {"at": _now(), "evaluated": res.get("evaluated"),
                                 "cleared": res.get("cleared"),
                                 "best": (res.get("best") or {}).get("variable"),
                                 # KESİNTİ PANODA GÖRÜNÜR: "3 sonda değerlendi" ile "10 sondanın
                                 # 3'ü değerlendi, kalanı kesildi" aynı karta yazılamaz.
                                 "kesildi": bool(res.get("kesildi")),
                                 "sebep": res.get("sebep"), "tavan_dk": _tavan,
                                 "kalan_sonda": res.get("kalan_sonda")}
        from . import obs
        obs.log("warmup_sprint", evaluated=res.get("evaluated"), cleared=res.get("cleared"),
                best=(res.get("best") or {}).get("variable"),
                kesildi=bool(res.get("kesildi")), tavan_dk=_tavan,
                kalan_sonda=res.get("kalan_sonda"))
    except Exception as e:
        _state["last_warmup"] = {"at": _now(), "error": type(e).__name__}

_lock = threading.Lock()            # guards thread start/stop
_reflect_lock = threading.Lock()    # guarantees only ONE reflection runs at a time
_thread: threading.Thread | None = None
_stop = threading.Event()
_state: dict = {"reflections": 0, "last_reflection": None, "last_poll": None,
                "last_result": None, "last_variable": None, "started_at": None, "poll_seconds": None,
                # trade-count baseline at the LAST reflection — the standby loop's trigger AND the honest
                # "next auto-reflection" countdown both derive from it. It used to be a local in _run(), so
                # the dashboard invented its own (wrong) formula from total closed trades.
                "last_reflect_at": None}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _brain() -> str:
    """Aktif beyin: HERMES_BRAIN_ORDER zincirinde anahtarı hazır VE soğumada olmayan ilk sağlayıcı
    (claude/nous/gemini), hiçbiri yoksa deterministik. Görüntü katmanı da bu tek kaynaktan okur.
    Soğuma farkı v66'da eklendi: gemini üç gün 429 yerken pano hâlâ bir LLM beyni gösteriyordu, yani
    deterministik yola düşüş LLM görüşü gibi okunuyordu — bozunmanın gizlenmesi tam olarak budur."""
    try:
        from . import hermes
        return hermes.active_brain()
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        return "deterministic"


def _brain_availability() -> dict:
    """Sağlayıcı başına {credentials, ready, cooling_s, reason} — bozunma NEDENİ panoda okunur olsun.
    İSTİSNA `{}` DEĞİL `{"error": ...}` DÖNER — gerekçesi için bkz. `_brain_chain`."""
    try:
        from . import hermes
        return hermes.brain_availability()
    except Exception as e:
        return {"error": type(e).__name__}


def _brain_chain() -> dict:
    """Zincirin YEDEKLİLİĞİ hakkında yalnız ölçülen olgular (bkz. hermes.brain_chain_facts):
    ad saymak kota saymak değildir. Bağımsız uç sayısı burada da ÜRETİLMEZ.

    İSTİSNA ARTIK YUTULMUYOR (2026-07-26): boş sözlük dönmek "hermes hiç koşmadı" (taze kurulum)
    ile "ÖLÇÜM ARIZALANDI" (hermes import'u/çağrısı düştü) arasındaki farkı siliyordu — ve bekçi
    tarafındaki `if _ch:` kapısı ikisini birden düşürüyordu. Yani yedeklilik denetiminin KENDİSİ
    bozulduğunda pano hiçbir şey söylemiyor, kör noktayı sessizlik gibi gösteriyordu. Hata SINIFI
    ölçülen bir olgudur; `{}` yerine onu döndürmek uydurma değil kayıttır."""
    try:
        from . import hermes
        return hermes.brain_chain_facts()
    except Exception as e:
        return {"error": type(e).__name__}


def _horizon_ok(trades: list, last_at: int, min_days: int = REFLECTION_MIN_DAYS,
                regime: str | None = None, min_trades: int = 1) -> bool:
    """Phase 3 time-clustering guardrail — STRICT AND: the trades accrued SINCE the last reflection must
    number >= min_trades AND span >= min_days of MARKET time (measured from trade timestamps, so it holds
    under fast paper-advance too). With `regime`, both conditions are measured WITHIN that regime's trades
    only — a reflection that would tune the live regime must be backed by enough time IN that regime.
    (The old '>=2 distinct regimes' OR-branch is deliberately GONE: it let N trades clustered in a few
    days bypass the calendar floor entirely — the exact overfit this guardrail exists to prevent.)"""
    new = trades[last_at:]
    if regime:
        new = [t for t in new if str(t.get("regime")) == str(regime)]
    if len(new) < max(1, int(min_trades)):
        return False
    ds = [str(t.get("ts_close") or t.get("ts_open") or "")[:10] for t in new]
    ds = [d for d in ds if d]
    if len(ds) < 2:
        return False
    try:
        return (dt.date.fromisoformat(max(ds)) - dt.date.fromisoformat(min(ds))).days >= min_days
    except Exception:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False


def _horizon_progress(trades: list, last_at: int, regime: str | None,
                      min_trades: int, min_days: int = REFLECTION_MIN_DAYS) -> dict:
    """Observable horizon state for the dashboard: how far along BOTH strict-AND conditions are
    (trades accrued + calendar span, within `regime` when given). Keeps the countdown honest — a
    count-only 'hazır' while the horizon still blocks was exactly the dishonest-status bug class."""
    new = trades[last_at:]
    if regime:
        new = [t for t in new if str(t.get("regime")) == str(regime)]
    ds = sorted(d for d in (str(t.get("ts_close") or t.get("ts_open") or "")[:10] for t in new) if d)
    span = 0
    if len(ds) >= 2:
        try:
            span = (dt.date.fromisoformat(ds[-1]) - dt.date.fromisoformat(ds[0])).days
        except Exception:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            span = 0
    return {"regime": regime, "trades": len(new), "trades_needed": max(1, int(min_trades)),
            "span_days": span, "min_days": min_days,
            "ready": len(new) >= max(1, int(min_trades)) and span >= min_days}


def _persist() -> None:
    try:
        from . import hermes
        model = hermes.active_model()
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        model = None
    brain = _brain()
    store.write_json(STATUS_FILE, {**_state, "brain": brain, "model": model, "updated": _now(),
                                   "brain_availability": _brain_availability(),
                                   "brain_chain": _brain_chain(),
                                   # DÜRÜST BOZUNMA: deterministik yola düştüysek bu dosyada AÇIKÇA yazar.
                                   "brain_degraded": brain == "deterministic"})


def _record(res: dict) -> None:
    _state["reflections"] += 1
    _state["last_reflection"] = _now()
    _state["last_result"] = res.get("status")
    _state["last_variable"] = (res.get("hypothesis") or {}).get("variable")
    # reset the countdown baseline. A MANUAL reflection must push the standby trigger out too — otherwise
    # the loop would immediately re-reflect on the very same trades.
    _state["last_reflect_at"] = len(store.read_jsonl("trades.jsonl"))


def _restored_baseline() -> int:
    """The reflection baseline for a fresh process: RESTORE the persisted last_reflect_at from
    hermes_status.json. Re-baselining to the current ledger length on every start silently discarded all
    span accrued since the last real reflection — under the strict-AND >=30-day horizon, routine daily
    restarts would reset the calendar clock forever and auto-reflection could NEVER fire (livelock).
    min() guards against a re-seeded (shorter) ledger; a first-ever run keeps the original design
    (baseline = current length: never reflect on the pre-existing backlog)."""
    n_now = len(store.read_jsonl("trades.jsonl"))
    persisted = store.read_json(STATUS_FILE, {}).get("last_reflect_at")
    return min(int(persisted), n_now) if isinstance(persisted, (int, float)) else n_now


def _run(poll_seconds: int) -> None:
    from . import hermes
    every = int(config.goal().get("reflection_every", 5))
    if _state.get("last_reflect_at") is None:
        _state["last_reflect_at"] = _restored_baseline()
    _state.update(started_at=_now(), poll_seconds=poll_seconds)
    _persist()
    while not _stop.is_set():
        try:
            _state["last_poll"] = _now()
            _persist()      # poll BAŞLARKEN yaz: aşağıdaki yansıma dakikalar sürebilir ve tek yazma
                            # poll sonundaysa dosya o süre boyunca donar, panoda "hiç poll yapılmadı"
                            # görünür (gözlem boşluğu, 2026-07-22).
            from . import watchdog as _wd7
            _wd7.beat("hermes_poll")
            try:
                from . import hermes as _hm3
                _hm3.sync_agent_skills()   # canlıda görüldü: hermes-agent küratörü linkleri silebiliyor —
                _hm3.config_ensure_integrations()  # aynı öz-onarım: MCP/hook/cache/pool config'i tazele
            except Exception:              # her poll'da ucuz eşitleme = sürekli öz-onarım
                # sessiz-yutma: kalıcı bozukluk bir SONRAKİ poll'da yine denenir ve start() yolundaki
                # AYNI çağrı uyarıyı zaten yazar; burada uyarmak aynı olayı günde yüzlerce kez tekrarlardı.
                pass
            if not health.halted() and not health.stale(900):
                trades = store.read_jsonl("trades.jsonl")
                n, last_at = len(trades), int(_state["last_reflect_at"])
                # Phase 3 STRICT-AND guardrail, scoped to the LIVE regime (the one a new reflection would
                # tune): >= reflection_every trades AND >= min_days span, both within that regime.
                live_reg = store.read_json("regime.json", {}).get("regime")
                live_reg = live_reg if live_reg in config.VALID_REGIMES else None
                horizon = _horizon_ok(trades, last_at, regime=live_reg, min_trades=every)
                _state["horizon_ready"] = bool(horizon)
                _state["horizon_regime"] = live_reg
                # ISINMA SPRİNTİ NEDEN KOŞMADI: sprint bu elif zincirinin SON dalı, yani her poll'da
                # önceki dallara yeniliyor olabilir. 0/12'yi "birazdan koşar" diye göstermek yanlış
                # vaat: arka plan yansıması sırayı sürekli tutuyorsa sayaç ASLA ilerlemez. Nedeni
                # burada tokenle yaz ki pano "koşmadı" ile "koşamaz"ı ayırt edebilsin.
                _state["_warm_skip"] = None
                if health.learn_halted():
                    _state["last_result"] = "learning_halted"      # ısınma da duraklar: operatör tam sessizlik istedi
                    _state["_warm_skip"] = "learn_halted"
                elif n - last_at >= every and horizon and _reflect_lock.acquire(blocking=False):
                    try:
                        # pass the CERTIFIED regime: the search takes minutes, and a regime flip in the
                        # meantime must not retarget the ship into a regime the horizon never certified.
                        _state["_warm_skip"] = "reflect"
                        _record(hermes.reflect_once(target_regime=live_reg))
                    finally:
                        _reflect_lock.release()
                elif (bg := _bg_ready_regime(trades, every, live_reg)) and \
                        os.environ.get("MERIDIAN_BG_REFLECT", "1") == "1" and \
                        _reflect_lock.acquire(blocking=False):
                    try:
                        _state["_warm_skip"] = "bg_reflect"
                        obs.log("bg_reflection_start", regime=bg,
                                detail="canlı ufuk dolu değil — birikmiş kanıtlı rejim arka planda işleniyor")
                        _record(hermes.reflect_once(target_regime=bg))
                        _state.setdefault("bg_reflect_by_regime", {})[bg] = len(trades)
                    finally:
                        _reflect_lock.release()
                elif os.environ.get("MERIDIAN_WARMUP_SPRINTS", "1") == "1" and \
                        _reflect_lock.acquire(blocking=False):
                    # ISINMA SPRINTİ (öneri #4): yansıma ateşlemeye HAK KAZANMADI (ufuk dolmadı) ama işlemci
                    # boşta. Sandbox koordinat araması koştur — HİÇBİR ŞEY SHIP ETMEDEN, yalnız UCB
                    # önceliklerini ısıtmak için (probe'lar defter-kalıcı çıkmaz yaratmaz — bilinçli tasarım).
                    # Gerçek yansıma ateşlediğinde arama bilgili sıralamadan başlar. Sık koşmasın diye
                    # WARMUP_EVERY_POLLS pollda bir.
                    try:
                        _state["_warm_ticks"] = _state.get("_warm_ticks", 0) + 1
                        if _state["_warm_ticks"] % WARMUP_EVERY_POLLS == 0:
                            _warmup_sprint()
                    finally:
                        _reflect_lock.release()
                elif os.environ.get("MERIDIAN_WARMUP_SPRINTS", "1") != "1":
                    _state["_warm_skip"] = "disabled"
                else:
                    _state["_warm_skip"] = "lock_busy"   # başka bir yansıma kilidi tutuyor
            else:
                _state["_warm_skip"] = "halted_or_stale"
            _persist()
        except Exception as e:
            _state["last_result"] = f"error: {type(e).__name__}"
            _persist()
        _stop.wait(poll_seconds)
    _persist()


def start(poll_seconds: int = 300) -> dict:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return {"already_running": True}
        _stop.clear()
        try:
            from . import hermes as _hm2
            _hm2.sync_agent_skills()               # ajan skill seti = enabled seti (başlangıçta eşitle)
            _hm2.config_ensure_integrations()      # MCP/hook/cache/pool config'i başlangıçta kur
        except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
            pass
        _thread = threading.Thread(target=_run, args=(poll_seconds,), name="hermes-standby", daemon=True)
        _thread.start()
    return {"started": True, "poll_seconds": poll_seconds}


def stop() -> dict:
    _stop.set()
    return {"stopping": True}


def reflect_now() -> dict:
    """Kick off ONE reflection in a BACKGROUND thread (operator-triggered) and return immediately. The
    coordinate-descent search runs several walk-forwards and can take minutes — far too long to block an
    HTTP request (browser/proxy timeouts, a stuck worker). Poll status()['reflecting'] for completion.
    Refuses if a reflection is already running."""
    from . import hermes
    if _reflect_lock.locked():
        return {"status": "busy", "detail": "zaten bir düşünme sürüyor"}
    # Operator override: the manual button deliberately bypasses the standby horizon (the operator is
    # sovereign), but the bypass must be VISIBLE — report the gate state honestly instead of hiding it.
    st = status()
    hz = st.get("horizon") or {}
    note = "" if hz.get("ready") else (" · not: otomatik ufuk kapısı henüz dolmadı "
                                       f"({hz.get('trades', 0)}/{hz.get('trades_needed', '?')} işlem, "
                                       f"{hz.get('span_days', 0)}/{hz.get('min_days', '?')} gün) — elle tetikleme bunu bilerek atlar")

    def _bg():
        if not _reflect_lock.acquire(blocking=False):
            return
        try:
            _record(hermes.reflect_once())
        except Exception as e:
            _state["last_result"] = f"error: {type(e).__name__}"
        finally:
            _persist()
            _reflect_lock.release()
    threading.Thread(target=_bg, name="hermes-reflect-now", daemon=True).start()
    _persist()
    return {"status": "started", "horizon_ready": bool(hz.get("ready")),
            "detail": "arama başladı — birkaç dakika sürebilir (arka planda)" + note}


def status() -> dict:
    alive = bool(_thread and _thread.is_alive())
    try:
        from . import hermes
        model, search = hermes.active_model(), dict(hermes.SEARCH_PROGRESS)
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        model, search = None, {}
    every = int(config.goal().get("reflection_every", 5))
    trades = store.read_jsonl("trades.jsonl")
    closed = len(trades)
    base = _state.get("last_reflect_at")
    # Honest countdown: how many NEW trades must close before the standby loop reflects again. The old UI
    # formula was `every - closed_trades`, which is 0 for any book with more trades than `every` — i.e. it
    # always read "hazır" (ready), which was simply false. Computed here so there is ONE source of truth.
    since = max(0, closed - int(base)) if base is not None else 0
    # Horizon computed FRESH on every status read (not only in the standby loop's healthy branch), so the
    # dashboard shows the real gate even during HALT/stale and before the first poll.
    live_reg = store.read_json("regime.json", {}).get("regime")
    live_reg = live_reg if live_reg in config.VALID_REGIMES else None
    horizon = _horizon_progress(trades, int(base) if base is not None else closed, live_reg, every)
    brain = _brain()
    return {**_state, "active": alive, "brain": brain, "model": model,
            "brain_availability": _brain_availability(), "brain_chain": _brain_chain(),
            "brain_degraded": brain == "deterministic",
            "reflection_every": every, "closed_trades": closed,
            "trades_since_last_reflection": since,
            "trades_until_next": max(0, every - since),
            "horizon": horizon, "horizon_ready": horizon["ready"], "horizon_regime": live_reg,
            "search": search,                      # live coordinate-descent progress (probe i/total, best)
            "reflecting": _reflect_lock.locked()}
