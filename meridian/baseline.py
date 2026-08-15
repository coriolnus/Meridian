"""baseline.py — ebeveyn sürümün tabanını UYDURMADAN ölçmek: backfill + like-for-like would-have kıyası.

Ne yapar: Öğrenme döngüsü ebeveyn skoru olmadan kapanamaz — taban yoksa delta yoktur; delta yoksa
hiçbir hipotez terminale ulaşmaz ve kalibrasyon n=0 kalır (re-seed sonrası ebeveynin karnede ne
satırı ne skoru olabilir). Bu modül tabanı UYDURMAZ, ÖLÇER: ebeveynin state/history/vNNNN.yaml
anlık görüntüsündeki parametreleri, adayın geçtiği kapının GÖRDÜĞÜ walk-forward'ın birebir
aynısından geçirir (aynı bar seti, aynı pencereler, aynı fold/ambargo). Ayrıca geri-alma kararının
simetrik kıyasını kurar; eski kıyas YANLIŞLANDI: çocuğun canlı skoru ile ebeveynin backtest OOS
skoru üç ayrı eksende (dönem, motor, yıllıklandırma) ayrışıyordu ve ölçülen sapma geri-alma
eşiğinin iki katıydı — karar beceriyi değil takvimi ölçüyordu.

Kilit girişler: `would_have_replay(version, parent, goal, eval_regime)` — ebeveyn parametrelerini
çocuğun CANLI DÖNEMİNDE replay eder ve iki tarafı da AYNI backtest.segment_score penceresiyle
puanlar (dönem + yıllıklandırma eksenleri kapanır); kapanmayan motor ekseni gizlenmez, üçüncü
bacakla ölçülür: motor_sapmasi = çocuk_replay − çocuk_canlı. `measure_parent_baseline(publish)` —
ebeveyni walk-forward'dan geçirir, hükmünü verir, yalnız istenirse karneye yazar.

Değişmezler: ölçmek / hüküm / yayınlamak ÜÇ AYRI karardır — bir sayının var olması taban olarak
kullanılabileceği anlamına gelmez (verdict: olculebilir | olculemez_orneklem | olculemez_frekans;
would-have'de olculdu | olculemez_pencere | olculemez_replay). Ölçülemeyen hâlde delta UYDURULMAZ:
None + neden döner ve çağıran eski yola damgayla düşer. Frekans oranı FREQ_RATIO_MAX'ı aşarsa delta
beceri değil işlem sıklığı ölçer — skor karneye YAZILMAZ. Karar yolunda ağa çıkılmaz
(dataset.load_cached: determinizm + kararın kendi verisini değiştirmemesi); canlı worker koşarken
yayın reddedilir (kilitsiz karne yazımı worker satırını ezebilir). Okur: history anlık görüntüleri,
trades.jsonl, bar önbelleği; yazar: yalnız publish=True ile karne satır alanları
(versioning.set_row_fields — current_version'a dokunmaz)."""
from __future__ import annotations
import datetime as dt
import os

from . import config, health, memory, obs, store, versioning

# FREKANS ORANI TAVANI. `score.py` Sharpe'ı `sqrt(trades_per_year)` ile ölçekler (105-112. satırlar),
# yani aynı beceriye sahip iki tarafın skoru YALNIZ işlem sıklıkları farklı olduğu için ayrışır.
# Backtest tabanı ~2.5 yıllık OOS penceresinden, canlı taraf ise birkaç aylık kâğıt defterinden
# gelir; sıklıkları bu tavanı aşacak kadar ayrışıyorsa aradaki delta BECERİ değil FREKANS ölçer ve
# öyle bir sayıyı taban diye yayınlamak geri-alma kararını zehirler.
FREQ_RATIO_MAX = float(os.environ.get("MERIDIAN_BASELINE_FREQ_RATIO_MAX", "2.0"))

# İşlem defterindeki zaman damgası alanları — CANLI `state/trades.jsonl` satırlarından doğrulandı
# (`ts`/`exit_ts` DEĞİL). `score._span_days` de aynı ikiliyi okur; süre tanımı iki yerde ayrışmasın.
TS_FIELDS = ("ts_open", "ts_close")

YIL_GUN = 365.25


def _gun_farki(a, b):
    """İki ISO tarih arasındaki gün sayısı; ölçülemiyorsa None.

    None UYDURMA YASAĞI'nın gereği: 0 gün "aynı gün" demektir, "bilmiyorum" demez — ve 0'a bölünen
    bir frekans ya patlar ya da sonsuz bir sıklık uydurur."""
    try:
        return (dt.date.fromisoformat(str(b)[:10]) - dt.date.fromisoformat(str(a)[:10])).days
    except (TypeError, ValueError):  # sessiz-yutma: kayıp DEĞİL — None doğrudan hükme (`olculemez_orneklem`) girer, raporda ve obs kaydında görünür; ayrıca uyarmak aynı olguyu iki kez söylerdi
        return None


def _frekans(n: int, span_days) -> float | None:
    """Yılda işlem. n ya da süre yoksa None (ölçülmemiş olan yazılmaz)."""
    if not n or not span_days or span_days <= 0:
        return None
    return round(n / (span_days / YIL_GUN), 4)


# ---- LIKE-FOR-LIKE ROLLBACK KIYASI (2026-07-29) -----------------------------------------------
# TEŞHİS. Bugünkü geri-alma kararı ELMA-ARMUTtu: çocuğun CANLI skoru (95 işlem, ~4 ay, canlı motor,
# `score_mod.score` ile o kümenin KENDİ süresine göre yıllıklandırılmış) ile ebeveynin BACKTEST OOS
# skoru (2,5 yıllık pencere, replay motoru, `span_days=903` ile yıllıklandırılmış) karşılaştırılıyordu.
# İki sayı üç ayrı eksende ayrışıyor: DÖNEM (farklı piyasa), MOTOR (canlı vs replay) ve
# YILLIKLANDIRMA (farklı span). `tests/test_gate_statistics_v74.py::test_def8` bu sapmayı canlı
# defterde 0.21 olarak ÖLÇTÜ — geri-alma eşiği ise 0.10. Yani karar, ölçüm hatasının yarısı kadar
# bir eşikle veriliyordu; hangi yöne düşeceği becerinin değil takvimin işiydi.
#
# ÇÖZÜM. Ebeveynin PARAMETRELERİ, çocuğun canlı döneminin TAM OLARAK aynısında replay edilir
# ("would-have" skoru: ebeveyn canlıda kalsaydı ne olurdu?) ve iki taraf da AYNI fonksiyonla
# (`backtest.segment_score`, aynı `seg_start/seg_end`) puanlanır — yani dönem ve yıllıklandırma
# eksenleri KAPANIR.
#
# KAPANMAYAN EKSEN AÇIKÇA BEYAN EDİLİR: motor. Çocuğun tarafı GERÇEK canlı defterdir (gerçek
# dolumlar, gerçek kayma, o günün gerçek evreni — Finviz keşfi dahil), ebeveynin tarafı ise replay
# motorudur (`dataset.load()` → yalnız REPLAY_UNIVERSE). Bu farkı GİZLEMEK yerine ÖLÇÜYORUZ:
# üçüncü bir bacak olarak ÇOCUĞUN PARAMETRELERİ de aynı pencerede replay edilir ve
# `motor_sapmasi = cocuk_replay − cocuk_canli` olarak raporlanır. Sapma büyükse kıyasın kalan
# kusuru sayının yanında görünür; küçükse "would-have" kıyası güvenle okunur. Karar (brief gereği)
# canlı-çocuk vs would-have-ebeveyn üzerinden verilir, ama damga hangi yöntemin kullanıldığını
# ve sapmanın ne olduğunu KARAR KAYDINA yazar.
WOULD_HAVE_YONTEM = "like_for_like_replay_v1"


def would_have_replay(version: int, parent: int, goal: dict | None = None,
                      eval_regime: str | None = None) -> dict:
    """Ebeveyn parametrelerini ÇOCUĞUN CANLI DÖNEMİNDE replay et; simetrik skor çiftini döndür.

    HİÇBİR ŞEY YAZMAZ (ne karneye, ne state'e) — saf ölçüm. Çağıran (`rollback`) sonucu kendi
    kayıtlarına gömer; bu modülün `measure_parent_baseline`deki ölç/hüküm/yayınla ayrımı burada da
    geçerlidir, farkı bu fonksiyonun YAYINLAMA bacağı hiç yoktur.

    PENCERE canlı defterden gelir: çocuğun işlemlerinin ilk `ts_open`u ile son `ts_close`u.
    Takvimden ya da `live_since` damgasından değil — kıyasın paydası, ölçülen işlemlerin GERÇEKTEN
    kapsadığı dönem olmalıdır; bir gün bile kaydırmak iki tarafa farklı piyasa verirdi.

    Dönüş `verdict` alanı üç değerden biridir:
      * `olculdu`            — simetrik kıyas kuruldu, `delta` karar için kullanılabilir.
      * `olculemez_pencere`  — canlı dönem okunamadı (damga yok / tek işlem).
      * `olculemez_replay`   — bar/anlık görüntü yok ya da bir taraf skorlanamadı (min_sample altı).
    ÖLÇÜLEMEYEN HÂLDE DELTA UYDURULMAZ: None döner ve çağıran eski yola damgayla düşer."""
    goal = goal or config.goal()
    trades = store.read_jsonl("trades.jsonl")
    # REJİM SHIP'İNDE İKİ TARAF DA AYNI DİLİMDEN: `rollback`ın kendi yasası (ve `_ship_eval_regime`in
    # varlık sebebi) rejim dilimli bir canlı skoru global bir tabanla karşılaştırmayı yasaklar.
    # Would-have replay'i global bırakıp canlı tarafı dilimli tutmak, kapattığımız asimetriyi başka
    # bir eksende geri açardı — replay işlemleri de aynı rejime süzülür.
    if eval_regime:
        trades = [t for t in trades if str(t.get("regime")) == eval_regime]
    cur_rows = [t for t in trades if t.get("strategy_version") == version]
    stamps = sorted(str(t[k])[:10] for t in cur_rows for k in TS_FIELDS if t.get(k))
    if len(stamps) < 2:
        return {"verdict": "olculemez_pencere", "yontem": WOULD_HAVE_YONTEM,
                "neden": "canlı dönem damgası yok (en az iki zaman damgası gerek)",
                "version": version, "parent": parent, "delta": None}
    lo, hi = stamps[0], stamps[-1]

    snap_path = config.HISTORY / f"v{parent:04d}.yaml"
    if not snap_path.exists():
        return {"verdict": "olculemez_replay", "yontem": WOULD_HAVE_YONTEM,
                "neden": f"ebeveyn anlık görüntüsü yok: {snap_path.name}",
                "version": version, "parent": parent, "pencere": [lo, hi], "delta": None}
    import yaml
    with open(snap_path) as f:
        parent_strat = yaml.safe_load(f) or {}

    # AĞIR İTHALAT FONKSİYON İÇİNDE: `baseline` modülünü içe alan her yol (watchdog dahil) pandas/
    # numpy yüklemek zorunda kalmasın (mevcut `measure_parent_baseline` ile aynı desen).
    from . import backtest, dataset, reflect
    # `load_cached()` — `load()` DEĞİL. İki gerekçe, ikisi de kararın geçerliliğiyle ilgili:
    #   (1) AĞA ÇIKMAZ. Bu fonksiyon bir KARAR yolunun içindedir (geri alma). Bayat önbellekte
    #       `load()` fetch eder, fetch corporate-action tespitini tetikleyip bar CSV'lerini yeniden
    #       yazabilir — yani geri-alma kararı, kendi altındaki veriyi değiştirebilirdi.
    #   (2) DETERMİNİZM. `evaluate_outcomes` idempotan olmalı (test_na_revision_v53): arka arkaya iki
    #       çağrı AYNI deltayı vermeli. Ağdan gelen bir bar, iki çağrı arasında bunu bozardı.
    # Bedeli: önbellek boşsa (taze kurulum, sandbox) ölçüm yapılamaz — o hâlde uydurmak yerine
    # `olculemez_replay` denir ve karar damgalı biçimde eski yola düşer.
    try:
        bars, index = dataset.load_cached()
    except Exception as e:
        obs.warn("would_have_bars_unavailable", error=f"{type(e).__name__}: {e}",
                 version=version, parent=parent,
                 detail="ebeveyn would-have replay'i koşulamadı — kıyas eski (asimetrik) yola düşer")
        return {"verdict": "olculemez_replay", "yontem": WOULD_HAVE_YONTEM,
                "neden": f"bar yüklenemedi: {type(e).__name__}", "version": version,
                "parent": parent, "pencere": [lo, hi], "delta": None}
    if not bars or index is None or len(index) == 0:
        return {"verdict": "olculemez_replay", "yontem": WOULD_HAVE_YONTEM,
                "neden": "yerel bar önbelleği boş (ağa çıkılmaz) — simetrik kıyas kurulamadı",
                "version": version, "parent": parent, "pencere": [lo, hi], "delta": None}

    # ÇOCUĞUN PARAMETRELERİ: yürürlükteki `strategy.yaml` YALNIZ `version` canlı sürümse çocuğundur.
    # Üretim yolunda hep öyledir (rollback canlı sürümü değerlendirir), ama fonksiyon geçmiş bir
    # kararı yeniden ölçmek için de çağrılabilir (denetim, otopsi) — o hâlde `load_strategy()`
    # BAŞKA bir sürümün parametrelerini "çocuk" diye replay ederdi ve motor sapması bacağı
    # sessizce yanlış bir şeyi ölçerdi. Uyuşmazlıkta çocuğun kendi anlık görüntüsüne düşülür.
    cur_strat = config.load_strategy()
    if int(cur_strat.get("version", -1)) != int(version):
        cocuk_snap = config.HISTORY / f"v{int(version):04d}.yaml"
        if cocuk_snap.exists():
            with open(cocuk_snap) as f:
                cur_strat = yaml.safe_load(f) or {}
        else:
            # Kontrol bacağı ölçülemez → ölçüm SÜRER (asıl kıyas ebeveyn tarafındadır) ama motor
            # sapması None kalır; uydurulmuş bir kontrol, olmayan bir güvence verirdi.
            cur_strat = None

    def _replay_skor(params, pbr, ver):
        res = backtest.replay(params, bars, index, goal, lo, hi, strategy_version=ver,
                              params_by_regime=pbr)
        rows = ([t for t in res.trades if str(t.get("regime")) == eval_regime] if eval_regime
                else res.trades)
        det = backtest.segment_score(rows, goal, lo, hi)
        return det, rows

    try:
        par_det, par_trades = _replay_skor(reflect.params_of(parent_strat),
                                           parent_strat.get("params_by_regime"), parent)
        if cur_strat is None:
            cocuk_det, cocuk_trades = {}, []
        else:
            cocuk_det, cocuk_trades = _replay_skor(reflect.params_of(cur_strat),
                                                   cur_strat.get("params_by_regime"), version)
    except Exception as e:
        obs.warn("would_have_replay_failed", error=f"{type(e).__name__}: {e}",
                 version=version, parent=parent)
        return {"verdict": "olculemez_replay", "yontem": WOULD_HAVE_YONTEM,
                "neden": f"replay düştü: {type(e).__name__}", "version": version,
                "parent": parent, "pencere": [lo, hi], "delta": None}

    # ÇOCUĞUN CANLI TARAFI DA AYNI FONKSİYONLA PUANLANIR — asimetrinin asıl kaynağı buydu:
    # `score_mod.score` süreyi kendi kümesinden türetiyor, `segment_score` ise PENCEREDEN.
    canli_det = backtest.segment_score(cur_rows, goal, lo, hi)
    canli_skor = canli_det.get("score")
    wh_skor = par_det.get("score")
    cocuk_replay_skor = cocuk_det.get("score")
    if canli_skor is None or wh_skor is None:
        return {"verdict": "olculemez_replay", "yontem": WOULD_HAVE_YONTEM,
                "neden": ("canlı taraf skorlanamadı (min_sample altı)" if canli_skor is None
                          else "ebeveyn would-have skorlanamadı (min_sample altı)"),
                "version": version, "parent": parent, "pencere": [lo, hi],
                "canli_skor": canli_skor, "would_have_skor": wh_skor, "delta": None}

    motor_sapmasi = (None if cocuk_replay_skor is None
                     else round(cocuk_replay_skor - canli_skor, 4))
    return {
        "verdict": "olculdu", "yontem": WOULD_HAVE_YONTEM,
        "version": version, "parent": parent, "pencere": [lo, hi], "eval_regime": eval_regime,
        "canli_skor": canli_skor, "would_have_skor": wh_skor,
        "delta": round(canli_skor - wh_skor, 4),
        "n_canli": len(cur_rows), "n_would_have": len(par_trades),
        # MOTOR SAPMASI KONTROL BACAĞI: çocuğun KENDİ parametreleri aynı pencerede replay edilirse
        # canlı skoruna ne kadar yaklaşıyor? Sıfıra yakınsa replay canlıyı iyi temsil ediyor demektir.
        "cocuk_replay_skor": cocuk_replay_skor, "n_cocuk_replay": len(cocuk_trades),
        "motor_sapmasi": motor_sapmasi,
        "puanlama": "backtest.segment_score (iki taraf da AYNI pencere, AYNI yıllıklandırma)",
        "kalan_asimetri": ("motor: canlı defter gerçek dolum/kayma ve o günün gerçek evreniyle "
                           "(Finviz keşfi dahil) üretildi; would-have replay yalnız "
                           "REPLAY_UNIVERSE üzerinde koşar — `motor_sapmasi` bunun ölçüsüdür"),
    }


def measure_parent_baseline(publish: bool = False) -> dict:
    """Canlı sürümün EBEVEYNİNİ walk-forward'dan geçir, hükmünü ver, istenirse karneye yaz."""
    strat = config.load_strategy()
    cur_v = int(strat.get("version", 1))
    parent = strat.get("parent")
    if parent is None:
        return {"error": "no_parent"}
    parent = int(parent)

    # Ebeveynin PARAMETRELERİ yalnız anlık görüntüde durur (strategy.yaml çoktan çocuğun).
    # `versioning.revert_to` ile aynı yol ve aynı okuma.
    snap_path = config.HISTORY / f"v{parent:04d}.yaml"
    if not snap_path.exists():
        return {"error": "no_snapshot", "path": str(snap_path)}
    import yaml
    with open(snap_path) as f:
        parent_strat = yaml.safe_load(f) or {}

    # --- ÖLÇÜM: kapının ADAYA uyguladığı düzenin BİREBİR aynısı (reflect._submit_locked 457-469) ---
    # `eval_regime` GEÇİLMEZ: ebeveyn tabanı GLOBAL bir sayıdır. Rejim dilimli bir taban, global bir
    # canlı skorla karşılaştırıldığında sahte delta üretir (rollback'in kendi notu bunu söylüyor).
    from . import backtest, dataset, reflect
    bars, index = dataset.load()
    w = reflect._default_windows()
    goal = config.goal()
    wf = backtest.walk_forward(reflect.params_of(parent_strat), bars, index, goal,
                               w[0], w[1], w[2], w[3], strategy_version=parent,
                               oos_folds=w[4], embargo_days=w[5],
                               params_by_regime=parent_strat.get("params_by_regime"))

    # --- EBEVEYN TARAFI OLGULARI ---
    oos_score = wf["oos_score"]
    folds = wf["oos_folds"]
    n_par = sum(int(f.get("n") or 0) for f in folds)
    span_par = _gun_farki(w[1], w[2])
    freq_par = _frekans(n_par, span_par)

    # --- CANLI TARAF OLGULARI ---
    trades = store.read_jsonl("trades.jsonl")
    cur_rows = [t for t in trades if t.get("strategy_version") == cur_v]
    n_cur = len(cur_rows)
    stamps = sorted(str(t[k])[:10] for t in cur_rows for k in TS_FIELDS if t.get(k))
    span_cur = _gun_farki(stamps[0], stamps[-1]) if len(stamps) >= 2 else None
    freq_cur = _frekans(n_cur, span_cur)

    # --- HÜKÜM ---
    ratio = None
    if freq_par and freq_cur:
        ratio = round(max(freq_par, freq_cur) / min(freq_par, freq_cur), 3)
    if oos_score is None or freq_par is None or freq_cur is None or ratio is None:
        # Ya OOS dilimi min_sample'ın altında kaldı (score() None döndü) ya da bir tarafın sıklığı
        # hiç ölçülemedi. İkisi de aynı sınıf: ORTADA KARŞILAŞTIRILACAK BİR ÖRNEKLEM YOK.
        # `ratio is None` da buraya düşer: bir taraf sıfır sıklıkta ise oran TANIMSIZDIR ve
        # tanımsız bir oranı "tavanın altında" sayıp ölçülebilir demek, kontrolü sessizce atlatırdı.
        verdict = "olculemez_orneklem"
    elif ratio > FREQ_RATIO_MAX:
        verdict = "olculemez_frekans"
    else:
        verdict = "olculebilir"

    rapor = {
        "parent": parent, "cur_v": cur_v,
        "oos_score": oos_score, "folds": folds,
        "n_par": n_par, "n_cur": n_cur,
        "oos_span_days": span_par, "live_span_days": span_cur,
        "freq_par": freq_par, "freq_cur": freq_cur, "freq_ratio": ratio,
        "verdict": verdict, "published": False, "publish_refused": None,
    }
    if not publish:
        return rapor

    # --- CANLI WORKER BEKÇİSİ (run.replay_seed ile AYNI tanım ve AYNI eşik) ---
    # `set_row_fields` oku-değiştir-yaz yapar ve KİLİTSİZDİR (`store.file_lock` süreç-içidir). Canlı
    # worker aynı anda `update_scoreboard` çağırırsa iki yazardan biri diğerinin satırını sessizce
    # siler. "Worker koşuyor mu" UYDURULMAZ, ÖLÇÜLÜR: nabız tazeliği zaten bu soruyu cevaplıyor.
    from .run import RESEED_HEARTBEAT_FRESH_S as _FRESH_S   # "canlı" tanımı TEK yerde dursun
    hb_age = health.heartbeat_age_seconds()
    if not health.stale(_FRESH_S) and os.environ.get("MERIDIAN_FORCE_BASELINE") != "1":
        obs.warn("baseline_refused_live_worker", heartbeat_age_s=round(hb_age or 0, 1),
                 threshold_s=_FRESH_S, version=cur_v, parent=parent, verdict=verdict,
                 detail="nabız taze — canlı worker koşuyor; taban backfill'i karneye kilitsiz yazar "
                        "ve worker'ın aynı anda yazdığı satırı sessizce ezebilir")
        rapor["error"] = "live_worker_running"
        rapor["publish_refused"] = "live_worker_running"
        rapor["heartbeat_age_s"] = round(hb_age or 0, 1)
        return rapor

    # Meta HER hükümde yazılır — "ölçtük ve ölçülemez çıktı" da bir OLGUDUR ve görünmelidir;
    # yokluğu, hiç ölçülmemiş olmakla karıştırılırdı.
    meta = {"baseline_verdict": verdict, "baseline_source": "parent_backfill",
            "baseline_measured_at": memory.now_iso(), "baseline_n_trades": n_par,
            "baseline_span_days": span_par, "baseline_freq_ratio": ratio}
    if verdict == "olculebilir":
        versioning.set_row_fields(parent, backtest_oos=oos_score, **meta)
    else:
        # SKOR YAZILMAZ. `rollback` karnedeki `backtest_oos`'u ebeveyn tabanı diye okur ve canlı
        # sürümü ona göre geri alır; karşılaştırılamaz bir sayıyı oraya koymak delta UYDURMAKTIR.
        versioning.set_row_fields(parent, **meta)
    rapor["published"] = True
    obs.log("parent_baseline_measured", verdict=verdict, published=True, parent=parent,
            version=cur_v, oos_score=oos_score, score_published=(verdict == "olculebilir"),
            n_par=n_par, n_cur=n_cur, freq_par=freq_par, freq_cur=freq_cur, freq_ratio=ratio)
    return rapor
