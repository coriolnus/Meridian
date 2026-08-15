"""sprint_run.py — öğrenme sprintinin ÇOCUK SÜRECİ: kum havuzunda üç fazlı ileri-yürüyüş ölçümü.

`python -m meridian.sprint_run <sbroot> <cfg-json>` olarak, MERIDIAN_ROOT kum havuzunu gösterirken
çağrılır (`sprint.start()` doğurur): her config/store okuma-yazması kum havuzuna düşer, canlı
deftere dokunulmaz. Üç faz (`_run`):

  A. v1 İLERİ TABAN — `loop.daily_cycle` eval penceresi (sprint.EVAL_START→bugün) boyunca düz
     kitaptan yürütülür (parent=None → evaluate_outcomes no-op); dürüst aynı-pencere v1 örneklemi
     doğar. min_sample'a ulaşılamazsa tur "yetersiz örnek" beyanıyla biter.
  B. ARAMA + GEMİ — `reflect.search_and_submit` DEĞİŞMEMİŞ kapıyla, AYRIK seçim penceresinde
     (sprint.SELECT_WINDOWS) koşar; v2 gemiye biner ya da "hiçbir aday kapıyı geçemedi" yazılır.
  C. v2 İLERİ ADAY — kitap aynı düz duruma sıfırlanır (day_before = EVAL_START'tan kesin önceki
     seans; aynı-pencere değişmezi bozulmasın), AYNI pencere yeniden yürünür; v2 min_sample'a
     ulaşınca döngü sızıntısız bir realized_delta + calibration_hit ile kapanır.

DEĞİŞMEZLER: v1 ve v2 aynı pencereyi AYNI düz kitaptan yürür (rejim ortak-mod); sonuç yalnız
antrenman kalibrasyon noktasıdır, canlı defter v1'de kalır; `STOP` dosyası her seansta yoklanır.

OKUR/YAZAR: kum havuzu state'i (trades/hypotheses/portfolio/strategy) + arama özeti
`sprint_runs.jsonl`a; ilerleme canlı `sprint_status.json`a ($MERIDIAN_SPRINT_STATUS) ATOMİK yazılır
ve ebeveynin kadans damgası (STAMP_KEYS, `_damgayi_koru`) her yazımda korunur."""
from __future__ import annotations
import datetime as dt
import json
import os
import sys


# KADANS DAMGASI — ebeveynin (`sprint.start`) yazdığı, çocuğun ÜRETMEDİĞİ alanlar. Çocuğun her
# yazımında KORUNUR; bkz. `_damgayi_koru`.
# `kosum_yolu`/`birim` EKLENDİ (systemd koşum yolu): ebeveyn hangi yoldan başlattığını
# damgalar, çocuk bunu BİLEMEZ ve ilk ilerleme yazımında silerdi — C15'in birebir aynı sınıfı.
# Damganın okuyucusu operatörün doğrulama adımıdır ("kosum_yolu 'systemd' mi?") ve panodur.
STAMP_KEYS = ("cfg", "n_hyp_at_start", "kosum_yolu", "birim")


def _damgayi_koru(path: str, payload: dict) -> dict:
    """Mevcut durum dosyasındaki KADANS DAMGASINI payload'a geri koy.

    KUSUR. `sprint.start()` `n_hyp_at_start` (+ `cfg`) damgasını CANLI `sprint_status.json`a yazar
    ve kendi yorumunda nedenini beyan eder: "Damga olmadan `taze = len(hyps) − 0` olurdu ve tetik
    HER GECE yanardı". Ama çocuk süreç aynı dosyayı sabit bir payload'la BİRLEŞTİRMEDEN EZİYORDU ve
    o payload'da damga YOKTU. Sonuç ölçüldü: ilk ilerleme yazımında damga siliniyor, `should_run`
    `taze = 41 − 0 = 41 ≥ SPRINT_MIN_NEW_HYP` görüyor ve `gun < 7` olsa bile "taze_aday_birikimi"
    ile tetikliyordu — haftalık disiplin yerine gecelik zincir.

    NEDEN BİRLEŞTİRME, NEDEN PAYLOAD'A TAŞIMA DEĞİL. İki seçenek vardı: (a) damgayı `start()`ta
    çocuğa argüman olarak geçirmek, (b) çocuğun her yazımında dosyadaki damgayı korumak. (a)
    `n_hyp` ölçümünü `Popen`ın ÖNÜNE almayı ve çocuğun `cfg` sözleşmesini genişletmeyi gerektirir,
    üstelik `main()`in hata yolunu (sid'siz payload) ve `sprint.stop()`u KAPSAMAZ — damga oralardan
    yine düşerdi. (b) tek bir yerde, yazımın kendi katmanında kapanır. Yazım ATOMİK kalır: okuma,
    aynı fonksiyonda `os.replace`ten hemen önce yapılır, yani oku-yaz penceresi mikrosaniyeliktir
    ve tek diğer yazar (ebeveyn) o dosyaya sprint ömrü boyunca yalnız BİR kez yazar.

    SID KAPISI. Dosyadaki kayıt BAŞKA bir sprintin ise damga taşınmaz: bir önceki sprintin tabanını
    bu sprintin damgası gibi sunmak, ölçülmemiş bir sayıyı ölçülmüş gibi göstermek olurdu. Payload
    sid taşımıyorsa (`main()`in hata yolu) kapı uygulanmaz — o yazım zaten dosyadaki kaydın
    ÜSTÜNE yazıyor ve damgasını korumak, sprint çökünce kadans tabanının da sıfırlanmasını önler."""
    try:
        with open(path) as f:
            eski = json.load(f)
    except (OSError, ValueError):  # sessiz-yutma: dosya yoksa/bozuksa korunacak damga da yoktur; payload olduğu gibi yazılır ve ebeveynin damga yazımı zaten AYRI bir yoldur
        return payload
    if not isinstance(eski, dict):
        return payload
    if payload.get("sid") is not None and eski.get("sid") != payload.get("sid"):
        return payload
    korunan = {k: eski[k] for k in STAMP_KEYS if k in eski and k not in payload}
    return {**korunan, **payload} if korunan else payload


def _write_live_status(payload: dict) -> None:
    """ATOMIC — the API process polls this file every few seconds while the child rewrites it; a plain
    truncate-then-write let /api/sprint (and /api/hermes, which embeds it) read half-written JSON and
    500 intermittently.

    KADANS DAMGASI KORUNUR: payload yalnız ÇOCUĞUN ürettiği alanları taşır; dosyadaki
    `n_hyp_at_start`/`cfg` bu yazımda silinirse sprint kadansı haftalık tabanını kaybeder."""
    path = os.environ.get("MERIDIAN_SPRINT_STATUS")
    if not path:
        return
    from pathlib import Path
    from . import config, store
    payload = _damgayi_koru(path, payload)
    # KAPI-DIŞI TAŞIMA: elle mkstemp+os.replace (fsync YOK, flock YOK, sanitize YOK)
    # → store.write_json. ATOMİKLİK korunur; fsync EKLENİR (güç kesintisinde sıfır-baytlık status →
    # /api/sprint {} okurdu); sanitize EKLENİR (search sonucu np.float sızarsa çıplak json.dump
    # patlardı). Kilit ADI: çocuk sandbox STATE'inde koşar, canlı status yolu STATE DIŞI → relative_to
    # ValueError → mutlak ad → kendi kilidi. Ebeveynle (sprint.start, CANLI süreç) süreçler-arası
    # serileştirme flock'la SAĞLANAMAZ (ayrı STATE → ayrı kilit); damga güvenliği yapısaldır:
    # _damgayi_koru birleşimi + ebeveynin ömürde TEK yazımı (yukarıdaki docstring).
    # YASA-6 OKUYUCU: /api/sprint + /api/hermes (gömülü) birkaç saniyede bir poll eder.
    try:
        name = str(Path(path).relative_to(config.STATE))
    except ValueError:  # sessiz-yutma: canlı status yolu çocuğun sandbox STATE'i dışında — mutlak ad bilinçli fallback, veri kaybı yok
        name = str(path)
    try:
        store.write_json(name, payload)
    except OSError:  # sessiz-yutma: sprint ilerleme dosyası salt gösterim içindir; yazılamaması sprint'in KENDİSİNİ durduramaz ve sonuç yine sprint_runs.jsonl'a yazılır
        pass


def _sessions(index, lo: str, hi: str) -> list[str]:
    return [str(d.date()) for d in index["date"] if lo <= str(d.date()) <= hi]


def _slim(res: dict) -> dict:
    s = res.get("search") or res
    best = s.get("best")
    return {"status": res.get("status"), "evaluated": s.get("evaluated"), "cleared": s.get("cleared"),
            "incumbent_oos": s.get("incumbent_oos"), "best": best,
            "trace": [t for t in (s.get("trace") or []) if t.get("passes")][:6]}


def _run(sbroot: str, cfg: dict) -> None:
    from . import config, store, dataset, loop, reflect, memory, sprint as S

    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    sid = os.path.basename(sbroot)
    pid = os.getpid()

    def _count(v) -> int:
        return sum(1 for t in store.read_jsonl("trades.jsonl") if t.get("strategy_version") == v)

    def _v2_realized(v2):
        for h in memory.all_hypotheses():
            if h.get("version_to") == v2 and h.get("realized_delta") is not None:
                return {"realized_delta": h.get("realized_delta"), "status": h.get("status"),
                        "calibration_hit": h.get("calibration_hit"), "predicted_delta": h.get("predicted_delta")}
        return None

    def _reset_flat(day_before: str) -> None:
        from .score import START_EQUITY
        store.write_json("portfolio.json", {
            "cash": START_EQUITY, "realized_pnl": 0.0, "last_id": 0, "positions": {},
            "armed": [], "pending_exits": {}, "last_date": day_before, "day_start_equity": START_EQUITY})

    def _stopped() -> bool:
        return (config.STATE / "STOP").exists()

    def status(**kw) -> None:
        _write_live_status({"pid": pid, "sid": sid, "started_at": started, "sbroot": sbroot,
                            "eval_start": S.EVAL_START, "cutoff": S.CUTOFF,
                            "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **kw})

    bars, index = dataset.load()
    today = dt.date.today().isoformat()
    goal = config.goal()
    min_s = int(goal["min_sample"])
    fwd = _sessions(index, S.EVAL_START, today)
    total = len(fwd)
    if total == 0:
        return status(phase="done", loop_closed=False, note="eval penceresinde seans yok")
    # STRICTLY before EVAL_START. _sessions uses an INCLUSIVE upper bound, so when EVAL_START is itself
    # a session, day_before == fwd[0] — Phase C's _reset_flat(day_before) sets last_date=fwd[0], the first
    # daily_cycle(on_date=fwd[0]) hits loop.py's same-day dedup and no-ops, so v2 skips the first eval
    # session that v1 (reset with last_date=None) processes. That breaks the "same window, same flat book"
    # invariant the realized_delta comparison rests on. Take the session strictly before EVAL_START.
    _pre = [s for s in _sessions(index, "2000-01-01", S.EVAL_START) if s < S.EVAL_START]
    day_before = _pre[-1] if _pre else None

    # ---- PHASE A: v1 forward baseline ----
    status(phase="baseline", progress=0, total=total, n_v1=0)
    for i, d in enumerate(fwd):
        if _stopped():
            return status(phase="stopped", note="operatör durdurdu")
        loop.daily_cycle(bars, index, on_date=d)
        if i % 8 == 0 or i == total - 1:
            status(phase="baseline", progress=i + 1, total=total, n_v1=_count(1))
    n_v1 = _count(1)
    if n_v1 < min_s:
        return status(phase="done", loop_closed=False, n_v1=n_v1, shipped=False,
                      note=f"v1 ileri baz {n_v1}/{min_s} işlem — döngü kapanışı için yetersiz örnek")

    # ---- PHASE B: coordinate-descent search + ship on the DISJOINT select window ----
    status(phase="search", n_v1=n_v1, total=total)
    res = reflect.search_and_submit(bars, index, goal, windows=S.SELECT_WINDOWS,
                                    k_max=int(cfg["k_max"]), budget=int(cfg["budget"]))
    try:
        store.append_jsonl("sprint_runs.jsonl", {"ts": today, "sid": sid, **_slim(res)})
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        pass
    if res.get("status") != "shipped":
        return status(phase="done", loop_closed=False, shipped=False, n_v1=n_v1,
                      note="hiçbir aday OOS kapısını geçemedi — bu veri diliminde v1 yerel-optimal",
                      search=_slim(res))
    v2 = res["version"]

    # ---- PHASE C: v2 forward over the SAME window, from a reset flat book ----
    _reset_flat(day_before)
    status(phase="candidate", progress=0, total=total, v2=v2, n_v1=n_v1, n_v2=0, shipped=True, search=_slim(res))
    closed = None
    for i, d in enumerate(fwd):
        if _stopped():
            return status(phase="stopped", v2=v2, n_v1=n_v1, n_v2=_count(v2), note="operatör durdurdu")
        loop.daily_cycle(bars, index, on_date=d)   # tags v2; evaluate_outcomes runs at cycle end
        closed = _v2_realized(v2)
        if i % 8 == 0 or i == total - 1 or closed:
            status(phase="candidate", progress=i + 1, total=total, v2=v2, n_v1=n_v1, n_v2=_count(v2),
                   shipped=True, loop_closed=bool(closed), realized=closed, search=_slim(res))
        if closed:
            break

    status(phase="done", loop_closed=bool(closed), v2=v2, n_v1=n_v1, n_v2=_count(v2),
           shipped=True, realized=closed, search=_slim(res),
           note=("döngü kum havuzunda kapandı — antrenman kalibrasyon noktası (canlı defter hâlâ v1)"
                 if closed else f"v2 ileri işlem {_count(v2)}/{min_s} — min örneğe ulaşamadı"))


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) < 2:
        raise SystemExit("usage: python -m meridian.sprint_run <sbroot> <cfg-json>")
    sbroot, cfg = argv[0], json.loads(argv[1])
    try:
        _run(sbroot, cfg)
    except Exception as e:
        _write_live_status({"phase": "error", "error": f"{type(e).__name__}: {e}",
                            "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        raise


if __name__ == "__main__":
    main()
