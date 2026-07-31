"""reflect.py — the reflection entrypoint. Routes a hypothesis through the honest pipeline:
    guard.validate_change  ->  backtest OOS gate  ->  version bump + snapshot  ->  memory write-back

Two sources of hypotheses, same pipeline:
  * deterministic fallback proposer (--auto): proves the whole loop before an LLM is anywhere near it
  * Hermes (--hermes --hypothesis '<json>'): the brain proposes; the engine validates and gates

The engine — not the LLM — decides what ships. An instruction is a suggestion; the gate is the law."""
from __future__ import annotations
import argparse
import json
import os
import math
from collections import Counter

from . import config, store, guard, memory, versioning, backtest, dataset, oos_erosion, shadowlaw

GATE_MARGIN = 0.02   # candidate must beat incumbent OOS by at least this
TAIL_MARGIN_R = 0.5  # capital preservation: candidate may not raise OOS tail loss (VaR AND CVaR) by >this many R

# ---- PARA-v3 (2026-07-30): marj para ölçeğine çevrildi, düşüş vetosu eklendi -------------------
# `GATE_MARGIN` BİLEŞİK ölçekte tanımlıydı ve yasanın karar değişkeni artık PARA. İki sabit, tek
# kaynaktan (`shadowlaw`) gelir çünkü türetimleri ölçüme dayanır ve ölçüm kaydı orada durur:
#   MONEY_GATE_MARGIN = 0.004  ← 0.02 × σ(ΔS_v3)/σ(S_eski) = 0.02 × 0.1908 (σ-eşdeğerliği)
#   DD_VETO_MARGIN    = 0.04   ← σ(düşüş)=0.0343'ün DIŞINDA ve %8 düşüş bütçesinin YARISI
# `GATE_MARGIN` SİLİNMEDİ ve 0.02 kaldı: LEGACY yolun (dilimsiz fikstür/sandbox) yasası odur ve o
# yol bileşik skor karşılaştırır — orada para ölçeği hesaplanamaz (dilim yok, span yok). Yani
# 0.02 artık "eski yasanın marjı", 0.004 ise "yürürlükteki yasanın marjı"dır ve hangisinin koştuğu
# kapı kaydındaki `yasa_surumu` damgasında yazılıdır.
DD_VETO_MARGIN = shadowlaw.DD_VETO_MARGIN      # düşüş vetosunun marjı (para-v3 ile eklendi)
MONEY_GATE_MARGIN = shadowlaw.MONEY_GATE_MARGIN  # GATE_MARGIN'ın para-ölçek eşdeğeri
HOLDOUT_DIVERGENCE = 0.10   # OOS→holdout drop beyond this flags overfit_suspect (does NOT block the ship)

# incumbent walk-forward is identical across every candidate in a reflection session — compute once.
_INC_CACHE: dict = {}
INC_DISK_FILE = "inc_cache.json"     # #2: incumbent walk'ları da bar-revizyonuyla diskte yaşar
INC_DISK_CAP = 40
_INC_DISK_LOADED = False

# Önbellek G/Ç uyarıları OLAY TÜRÜ BAŞINA bir kez: arama döngüsü bunları yüzlerce kez çağırır,
# tekrar tekrar uyarmak logu sele çevirir ve asıl sinyali gömer (yasa 4'ün amacı sinyal, gürültü değil).
_CACHE_WARNED: set = set()


def _cache_warn(event: str, exc: BaseException) -> None:
    if event in _CACHE_WARNED:
        return
    _CACHE_WARNED.add(event)
    try:
        from . import obs
        obs.warn(event, error=f"{type(exc).__name__}: {exc}")
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi
        # arama döngüsünü ASLA düşüremez (bu fonksiyon yalnız telemetri içindir).
        pass


def _inc_disk_load() -> None:
    global _INC_DISK_LOADED
    if _INC_DISK_LOADED:
        return
    _INC_DISK_LOADED = True
    try:
        blob = store.read_json(INC_DISK_FILE, None)
        rev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
        if blob and int(blob.get("rev", -1)) == rev:
            for k, v in (blob.get("entries") or {}).items():
                _INC_CACHE.setdefault(k, v)
    except Exception as e:
        # YASA 4 (2026-07-21): önbellek okuması sessizce düşerse hata görünmez, YALNIZ SÜRE uzar —
        # her aday incumbent walk-forward'ı sıfırdan hesaplar. "Refleksiyon neden 40 dakika sürüyor?"
        # sorusunun cevabı diskteki bozuk bir JSON olabilir; artık iz bırakıyor.
        _cache_warn("inc_cache_load_failed", e)


def _inc_disk_save() -> None:
    try:
        rev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
        keys = list(_INC_CACHE.keys())[-INC_DISK_CAP:]
        store.write_json(INC_DISK_FILE, {"rev": rev, "entries": {k: _INC_CACHE[k] for k in keys}})
    except Exception as e:
        # Yazım düşerse önbellek HİÇ kalıcı olmaz: her oturum baştan hesaplar ve bu, yavaşlama
        # dışında hiçbir belirti vermezdi.
        _cache_warn("inc_cache_save_failed", e)


def clear_wf_caches() -> None:
    """Drop every cached walk-forward. MUST be called when the bar data changes (the scheduler's
    once-per-session refetch): cache keys carry params/windows/regime but nothing identifying the bars
    revision, so after a refetch (dividend/split re-adjustment, backfilled sessions) a cached incumbent
    from the OLD bars would be compared against a candidate walked on the NEW bars (audit #30).
    #3: DİSK önbelleği de bar-revizyonuyla yaşar — revizyon burada artar, eski dosya silinir; bayat
    önbellek (audit #30 sınıfı) diskten de dönemez."""
    _INC_CACHE.clear()
    _PROBE_CACHE.clear()
    global _PROBE_DISK_LOADED, _INC_DISK_LOADED
    _PROBE_DISK_LOADED = False
    _INC_DISK_LOADED = False
    # MONOTON revizyon (2026-07-21): eski hali oku-artır-yaz sayacıydı; okuma boş dönerse rev 1'e
    # SIFIRLANIYOR ve bayat önbellekler yeniden "geçerli" oluyordu (monotonluk dedektörü canlıda
    # 4→1 gerilemesini yakaladı). Zaman damgası hem sıfırlanamaz hem eşzamanlı yazımda kayıp-güncelleme
    # üretmez; yine de prev+1 tabanıyla korunur (saat geri alınsa bile ileri gider).
    import time as _t
    _prev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
    store.write_json(PROBE_REV_FILE, {"rev": max(int(_t.time()), _prev + 1)})
    try:
        (config.STATE / PROBE_DISK_FILE).unlink(missing_ok=True)
        (config.STATE / INC_DISK_FILE).unlink(missing_ok=True)
    except Exception:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
        pass


def _default_windows() -> tuple:
    return (dataset.IS_START, dataset.OOS_START, dataset.OOS_END,
            dataset.HOLDOUT_END, dataset.OOS_FOLDS, dataset.EMBARGO_DAYS)


def _eval_regime_of(variable: str) -> str | None:
    """Phase 3 regime-isolated learning: a 'base@regime' knob is a REGIME-TARGETED hypothesis — the gate
    must grade it only on trades from that regime (both incumbent and candidate on the same slice, so the
    comparison stays apples-to-apples). A plain global knob returns None (global grading — correct, since
    a global change affects every regime and slicing would hide cross-regime damage)."""
    if "@" not in str(variable):
        return None
    regime = str(variable).split("@", 1)[1]
    return regime if regime in config.VALID_REGIMES else None


def _wf_cached(params: dict, version: int, bars, index, goal: dict, by_regime: dict | None = None,
               windows: tuple | None = None, eval_regime: str | None = None) -> dict:
    w = windows or _default_windows()
    # window IS part of the cache key — otherwise a sprint incumbent walked on shifted windows would
    # collide with a production incumbent walked on dataset.* (the judge-found apples-to-oranges bug).
    # eval_regime is ALSO part of the key: a regime-sliced incumbent score must never collide with the
    # global incumbent score (same params, different grading population — same class of bug).
    key = repr((version, tuple(sorted((k, round(float(x), 6)) for k, x in params.items())),
                json.dumps(by_regime or {}, sort_keys=True), tuple(w[:4]) + (tuple(w[4]), w[5]), eval_regime))
    _inc_disk_load()
    if key not in _INC_CACHE:
        _INC_CACHE[key] = backtest.walk_forward(
            params, bars, index, goal, w[0], w[1], w[2], w[3], strategy_version=version,
            oos_folds=w[4], embargo_days=w[5], params_by_regime=by_regime, eval_regime=eval_regime)
        _inc_disk_save()
    return _INC_CACHE[key]


def _gate_why(inc: dict, cand: dict, majority: bool, fold_wins: int, fold_total: int, tail_ok: bool) -> str:
    inc_oos, cand_oos = inc["oos_score"], cand["oos_score"]
    inc_tail, cand_tail = inc.get("oos_tail_risk"), cand.get("oos_tail_risk")
    if cand_oos is None:
        return "candidate OOS score undefined (below min_sample)"
    if inc_oos is None:                          # L2: _gate_eval's `passes` guards this, but _gate_why did
        return "incumbent OOS score undefined (below min_sample)"   # not — `None + GATE_MARGIN` → TypeError
    if not (cand_oos > inc_oos + GATE_MARGIN):
        return f"candidate OOS {cand_oos} did not beat incumbent {inc_oos} + {GATE_MARGIN}"
    if not majority:
        if fold_total == 1:
            return ("fold-robustness UNPROVABLE: only 1 window had enough trades — a single-window "
                    "edge is not robustness (2026-07-22)")
        return f"candidate lost the fold-robustness majority ({fold_wins}/{fold_total})"
    return (f"candidate worsens OOS tail risk beyond {TAIL_MARGIN_R}R "
            f"(VaR {cand_tail['var_r']} vs {inc_tail['var_r']}, "
            f"CVaR {cand_tail['cvar_r']} vs {inc_tail['cvar_r']})")


def _gate_eval(inc: dict, cand: dict, k_probes: int = 1,
               record_erosion: bool = False) -> tuple[bool, dict, str]:
    """The ONE law. Shared verbatim by submit() (ship authority) and the sprint search so a candidate can
    never pass the search but be rejected by submit(), or vice-versa.

    v3 İSTATİSTİKSEL KATMAN: büyüklük (magnitude) kararı artık OLASILIKSAL — walk_forward dilim
    taşıyorsa Search-OOS üzerinde blok-bootstrap P(ΔS>0) ≥ p_required(K) aranır (K = o oturumda
    denenen aday sayısı; kazananın-laneti cezası). Dilim yoksa (eski fixture/sandbox) eski nokta-marj
    yasasına güvenli fallback. Fold-çoğunluğu ve kuyruk vetosu her iki yasada da aynen yürürlükte."""
    inc_oos, cand_oos = inc["oos_score"], cand["oos_score"]

    # ---- N-DENGELİ FOLD KESİMİ (Aşama 2.1, 2026-07-28) -----------------------------------------
    # Sınırlar INCUMBENT'ın Search-OOS işlemlerinden TEK KEZ türetilir, sonra İKİ TARAFA DA aynen
    # uygulanır. `walk_forward`ın takvim fold'ları bozulmadan yerinde kalır (önbellek anahtarı
    # değişmez, rapor alanları korunur); kapının OKUDUĞU fold'lar burada yeniden kesilir.
    # DİLİMSİZ SÖZLÜK = ESKİ DAVRANIŞ: fikstürler ve eski kayıtlar `_trades_search` taşımaz; onlarda
    # takvim fold'ları aynen kullanılır. Yeni yasayı veri olmayan yere zorlamak, olmayan bir kesimi
    # varmış gibi raporlamak olurdu.
    inc_folds, cand_folds = inc["oos_folds"], cand["oos_folds"]
    fold_bounds, fold_law = None, "takvim"
    _its, _cts = inc.get("_trades_search"), cand.get("_trades_search")
    _hi = (inc.get("oos_split") or {}).get("search_end")
    if _its and _cts is not None and _hi:
        fold_bounds = backtest.balanced_fold_bounds(_its, _hi, dataset.EMBARGO_DAYS)
        if fold_bounds:
            inc_folds = backtest._fold_metrics(_its, fold_bounds, dataset.EMBARGO_DAYS)
            cand_folds = backtest._fold_metrics(_cts, fold_bounds, dataset.EMBARGO_DAYS)
            fold_law = "n_dengeli"
        else:
            # SESSİZ DÜŞMEZ: taban tutmadıysa neden takvime dönüldüğü kapı kaydında görünür.
            fold_law = "n_dengeli_taban_tutmadi"

    fold_wins = fold_total = 0
    itiraz_edilmemis = 0        # incumbent'ın kanıt taşıdığı ama adayın HİÇ görünmediği pencereler
    for cf, incf in zip(cand_folds, inc_folds):
        inc_var = incf["n"] >= 3 and incf["avg_r"] is not None
        cand_var = cf["n"] >= 3 and cf["avg_r"] is not None
        if cand_var and inc_var:
            fold_total += 1
            fold_wins += 1 if cf["avg_r"] > incf["avg_r"] else 0
        elif inc_var:
            itiraz_edilmemis += 1
    # FOLD ÇOĞUNLUĞU KANIT İSTER (2026-07-22, kapı denetimi). Eskiden `fold_total < 2` iken
    # çoğunluk VARSAYILAN True'ydu — yani var olma sebebi olan hatayı serbest bırakıyordu: yalnız
    # TEK pencerede işlem yapan bir aday (fold 1'de 60 işlem, fold 2-3'te sıfır) diğer fold'ları
    # `n>=3` eşiğinin altına düşürüyor, `fold_total=1` oluyor ve çoğunluk otomatik geçiyordu.
    # Ölçüldü: böyle bir aday `passes=True, fold_wins=1/1, search_p=0.9995` ile "birkaç pencerede
    # sağlam" etiketiyle ship ediliyordu. Tek pencerelik bir edge, sağlamlığın KANITI değil ZITTIDIR.
    # Artık: en az 2 fold'da kanıt yoksa ÇOĞUNLUK İDDİA EDİLEMEZ (muhafazakâr taraf: False).
    # AYRIM ÖNEMLİ: `fold_total == 0` kontrolün HİÇ ÇALIŞMADIĞI hâldir (fold verisi yok — legacy
    # yol, fikstür, ya da walk-forward dilim üretmemiş): uygulanamayan bir kontrol veto sebebi
    # olamaz. `fold_total == 1` ise kontrol ÇALIŞTI ama kanıt TEK pencereye toplandı — B'nin bulduğu
    # hata tam buydu: fold 1'de 60 işlem, fold 2-3'te sıfır → diğerleri `n>=3` eşiğinin altına
    # düşüyor, `fold_total=1` oluyor ve çoğunluk VARSAYILAN True'ya kaçıyordu. Tek pencerelik bir
    # edge, sağlamlığın kanıtı değil ZITTIDIR; "birkaç pencerede sağlam" etiketiyle ship ediliyordu.
    majority = True if fold_total == 0 else (fold_wins >= (fold_total + 1) // 2 if fold_total >= 2
                                             else False)
    # ---- BOŞ BIRAKILAN PENCERE = SAĞLAMLIK İDDİASI YOK (2026-07-28, n-dengeli kesimin GEREKTİRDİĞİ
    # koruma; SAPMA BEYANI: brief "fold çoğunluğu aynen kalır" diyordu, bu ek kural onu GEVŞETMEZ,
    # SIKILAŞTIRIR — ve eklenmeseydi mevcut bir koruma sessizce kaybolurdu).
    # ÖLÇÜLDÜ: takvim fold'ları, işlemleri tek bir patlamaya sıkışmış bir adayı "fold 1'de 60 işlem,
    # fold 2-3'te sıfır" diye gösteriyordu → `fold_total=1` → çoğunluk reddediliyordu. n-dengeli
    # kesim sınırları incumbent'ın DAĞILIMINDAN türettiği için aynı adayın 9 aylık patlaması İKİ
    # dengeli fold'a bölünebiliyor → `fold_wins=2/2` → aynı aday "birkaç pencerede sağlam" etiketiyle
    # geçiyordu. Sınavın yarısına hiç girmemiş bir aday, sınavı geçmiş sayılamaz.
    # Kural: incumbent'ın kanıt taşıdığı BİR pencerede bile aday görünmüyorsa (n<3), sağlamlık
    # çoğunluğu İDDİA EDİLEMEZ. İki taraf da her pencerede işlem yapıyorsa bu dal hiç çalışmaz —
    # yani normal adaylar için davranış birebir aynıdır.
    if itiraz_edilmemis:
        majority = False
    inc_tail, cand_tail = inc.get("oos_tail_risk"), cand.get("oos_tail_risk")
    tail_ok = True
    if inc_tail and cand_tail:
        worse_var = cand_tail["var_r"] > inc_tail["var_r"] + TAIL_MARGIN_R
        worse_cvar = cand_tail["cvar_r"] > inc_tail["cvar_r"] + TAIL_MARGIN_R
        # AND → OR (2026-07-22, kapı denetimi). "İkisi BİRDEN kötüleşsin" demek, sermaye korumasında
        # fazla hoşgörülü: VaR'ı AYNI kalıp CVaR'ı 3.5R → 9.0R'ye çıkan bir aday geçiyordu — marjın
        # 11 KATI ve kalın-kuyruğun ders kitabı tanımı. Kuyruk riski tek metrikte bile anlamlı
        # kötüleşiyorsa bu bir vetodur; iki metrik iki AYRI soru sorar (tipik en kötü / en kötülerin
        # ortalaması), biri diğerini affedemez.
        tail_ok = not (worse_var or worse_cvar)

    # ---- DÜŞÜŞ VETOSU (PARA-v3, 2026-07-30) ----------------------------------------------------
    # ÇİFT-SAYIM BİTTİ AMA KORUMA BİTMEDİ. `dd_c` skordan çıktı (varyansının %82'sini oradan
    # alıyordu ve AYNI ANDA kuyruk vetosunda da sayılıyordu). Çıkardığımız şey bir ÖLÇÜT değil bir
    # ÇİFT SAYIMdı; ölçütün kendisi buraya, SERT kapıya taşınır ve burada DAHA GÜÇLÜdür: skorda
    # düşüş yalnız bir ağırlıkla pazarlık konusuydu (kâr artışıyla telafi edilebilirdi), burada
    # PAZARLIK YOK — marj aşılırsa aday RET.
    #
    # TEK YÖNLÜ, VE BU BİLİNÇLİ: yalnız KÖTÜLEŞMEYİ cezalandırır, İYİLEŞMEYİ ödüllendirmez. Çünkü
    # ödüllendirmek onu karar değişkenine geri sokmak olurdu — düşüşü sığlaştıran bir aday puan
    # kazanırsa, çift-sayım arka kapıdan geri gelir ve skorun varyansı yine düşüşe kayar.
    # (İyileşme YİNE DE görünür: `oos_detail.max_drawdown` ve 3A kuyruk ölçütü onu raporlar.)
    #
    # UYGULANAMAYAN KONTROL VETO SEBEBİ OLAMAZ (fold_total==0 ile aynı ilke): dilim yoksa
    # (fikstür/legacy) düşüş ölçülemez → `dd_ok=True` ve kayıtta `dd_durum="olculemedi"` yazar.
    # Sessizce "geçti" demez; ÖLÇÜLEMEDİĞİNİ söyler.
    #
    # BEYAN EDİLMİŞ SINIR (audit #6'nın kapsamı): veto, Search diliminin KAPANMIŞ-İŞLEM sermaye
    # eğrisini okur. `score_detail` düşüşü hesaplarken günlük mark-to-market eğrisini de katlıyor
    # ("açık pozisyon düşüşü saklanamasın"), ama `walk_forward` o eğriyi DİLİM BAŞINA döndürmüyor —
    # yalnız `oos_detail.max_drawdown` içinde, tam-OOS ölçeğinde var. Yani AÇIK POZİSYON düşüşü bu
    # vetonun tetikleyicisine GİRMEZ; bilgi kaybolmuyor (rapor alanında duruyor) ama veto onu
    # görmüyor. Mevcut fold ve kuyruk vetoları da aynı biçimde kapanmış işlemler üzerinden çalışır,
    # yani bu yeni bir tutarsızlık DEĞİL — mevcut sınırın aynısı. Kapatmak için `walk_forward`ın
    # dilim-başına M2M eğrisi döndürmesi gerekir; ROADMAP'e ölçüm borcu olarak yazıldı.
    inc_dd = cand_dd = None
    dd_ok, dd_durum = True, "olculemedi"
    if _its and _cts:
        from . import score as _sc
        inc_dd = _sc.max_drawdown(_sc.equity_curve(_its))
        cand_dd = _sc.max_drawdown(_sc.equity_curve(_cts))
        dd_ok = not (cand_dd > inc_dd + DD_VETO_MARGIN)
        dd_durum = "gecti" if dd_ok else "veto"

    # ---- OOS AŞINMA DEFTERİ (Aşama 2.2, 2026-07-28) --------------------------------------------
    # Bu değerlendirme, bu pencere geometrisine sorulan KAÇINCI sorudur? Parmak izi fold sınırlarını
    # DA kapsar (n-dengeli kesim onları incumbent'tan türettiği için geometrinin parçası oldular).
    # Ceza kapıyı kapatmaz, çıtayı yükseltir — ve HER İKİ YASAYA da biner: aşınma, oturum içi
    # çoklu-testten (k_probes) AYRI bir yüktür ve olasılıksal yasa onu görmüyordu.
    # SAYIM YALNIZ RESMÎ DEĞERLENDİRMEDE (`record_erosion=True`): `_gate_eval` arama döngüsünde,
    # silahlanma yolunda ve testlerde de çağrılır; her çağrıda sayan bir defter "kaç resmî soru
    # soruldu"yu değil "kaç kez fonksiyon çağrıldı"yı ölçerdi. Ön-elemenin çoklu-test yükü zaten
    # AYRI bir kanaldan, `k_probes` beyanıyla taşınıyor — ikisini tek sayaca toplamak aynı cezayı
    # iki kez kesmek olurdu. MARJ ise her çağrıda uygulanır: aşınmış bir pencerede ölçüm yapan
    # herkes aynı çıtayı görmeli, yoksa ön-eleme kapının göremediği bir gevşeklikten yararlanırdı.
    _fp = oos_erosion.fingerprint(dataset.IS_START, dataset.OOS_START, dataset.OOS_END,
                                  dataset.HOLDOUT_END, fold_bounds or dataset.OOS_FOLDS,
                                  dataset.EMBARGO_DAYS)
    erosion = (oos_erosion.note(_fp, {"is_start": dataset.IS_START, "oos_start": dataset.OOS_START,
                                      "oos_end": dataset.OOS_END, "holdout_end": dataset.HOLDOUT_END,
                                      "fold_law": fold_law, "folds": fold_bounds or dataset.OOS_FOLDS})
               if record_erosion else oos_erosion.status(_fp))
    erosion_margin = float(erosion.get("extra_margin") or 0.0)
    effective_margin = GATE_MARGIN + erosion_margin

    from .oos_pipeline import OutOfSamplePipeline
    pipe = OutOfSamplePipeline(config.goal())
    prob = pipe.evaluate_search(inc, cand, k_probes=k_probes)
    if prob.law == "probabilistic":
        # dilim tabanı: bootstrap içi min_sample bypass'ı dilimin KENDİSİNİ inceltmesin — iki tarafta
        # da en az min_sample·0.7 işlem yoksa olasılıksal karar dürüst değildir → magnitude geçmez.
        floor = max(10, int(config.goal().get("min_sample", 30) * 0.7))
        thin = min(len(inc.get("_trades_search", [])), len(cand.get("_trades_search", []))) < floor
        # `goal.min_sample` DEĞİŞMEZ bir sözleşmedir (2026-07-22, kapı denetimi): olasılıksal yasa
        # kendi tabanını icat ediyordu (0.7·30 = 21) ve `cand_oos is not None` kontrolü YOKTU. Sonuç:
        # 26 kapanmış OOS işlemiyle bir aday `passes=True, candidate_oos=None` alıp ship ediliyor,
        # karneye `backtest_oos: None` yazılıyordu — yani skoru DÜRÜSTÇE tanımsız olan bir sürüm
        # canlıya çıkıyordu. Ölçülemeyen bir aday, ölçülmüş bir aday gibi ship edilemez.
        # AŞINMA CEZASI OLASILIKSAL YASADA DA BİNER: olasılıksal yasa `GATE_MARGIN`ı p-eşiğiyle
        # değiştirdiği için ek marj kendiliğinden uygulanmıyordu. Aşınma, K-cezasının ölçtüğü
        # OTURUM İÇİ çoklu testten farklı bir şeydir (aylar boyunca aynı sınava dönmek); ikisinden
        # birini görmeyen bir yasa aşınmayı bedava yapardı. Ceza yalnız eşik aşıldığında (>0) devreye
        # girer, yani normal hâlde bu satır bir NO-OP'tur ve v3 yasasının davranışı değişmez.
        # AŞINMA MARJI ARTIK PARA ÖLÇEĞİNDE (PARA-v3). Eski satır bileşik `oos_score`ları
        # kıyaslıyordu; yeni yasada bu, skordan ÇIKARDIĞIMIZ düşüş/Sharpe bacaklarını arka kapıdan
        # karara geri sokmak olurdu — aşınmış bir pencerede aday, kârı DEĞİL düşüşünü iyileştirerek
        # ek marjı geçebilirdi. `oos_erosion`ın bileşik-ölçek marjı, aynı ölçülmüş çarpanla
        # (`shadowlaw.MARGIN_MONEY_SCALE`) para ölçeğine çevrilir; ceza yine yalnız eşik aşıldığında
        # (>0) devreye girer, yani normal hâlde bu satırlar NO-OP'tur.
        import datetime as _dt
        _sp = cand.get("oos_split") or {}
        try:
            _span_s = max(1, (_dt.date.fromisoformat(str(_sp.get("search_end"))[:10])
                              - _dt.date.fromisoformat(str(_sp.get("search_start"))[:10])).days)
        except (ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik dilim sınırı; para skoru None kalır ve aşağıdaki muhafazakâr dal (ölçülemedi → marj karşılanmadı) devreye girer
            _span_s = None
        _g = config.goal()
        inc_para = shadowlaw.money_score(_its or [], _g, span_days=_span_s) if _span_s else None
        cand_para = shadowlaw.money_score(_cts or [], _g, span_days=_span_s) if _span_s else None
        erosion_margin_para = round(erosion_margin * shadowlaw.MARGIN_MONEY_SCALE, 6)
        erosion_ok = (erosion_margin <= 0.0 or (cand_para is not None and inc_para is not None
                                                and cand_para > inc_para + erosion_margin_para))
        magnitude_ok = bool(prob.passes and not thin and cand_oos is not None
                            and inc_oos is not None and erosion_ok)
        mag_why = ("aday/incumbent OOS skoru TANIMSIZ (min_sample altı) — ölçülmemiş aday ship edilemez"
                   if (cand_oos is None or inc_oos is None) else
                   f"arama dilimi ince (<{floor} işlem) — olasılıksal karar güvenilmez" if thin
                   else (f"OOS aşınması: bu pencereye {erosion.get('queries')} sorgu soruldu "
                         f"(>{oos_erosion.EROSION_QUERY_LIMIT}) — PARA ölçeğinde ek marj "
                         f"{erosion_margin_para} karşılanmadı (aday {cand_para} vs incumbent "
                         f"{inc_para})" if not erosion_ok else prob.why))
        law = "probabilistic"
    else:
        # LEGACY fallback (dilim yok): davranış-özdeş ESKİ marj yasası — bool() coercion yük taşır
        # (numpy.bool_ /api 500 dersi). Marj artık aşınma cezasını İÇERİR.
        # PARA-v3 BU YOLA İNMEZ ve inemez: para skoru dilimin takvim uzunluğuna ihtiyaç duyar, dilim
        # yoksa payda yoktur. Bu yol yalnız fikstür/sandbox içindir; hangi yasanın koştuğu kapı
        # kaydındaki `yasa_surumu` damgasında AÇIKÇA yazılıdır ("eski_bilesik_marj").
        inc_para = cand_para = None
        erosion_margin_para = None
        magnitude_ok = bool(cand_oos is not None and inc_oos is not None
                            and cand_oos > inc_oos + effective_margin)
        mag_why = "" if magnitude_ok else _gate_why(inc, cand, True, fold_wins, fold_total, True)
        law = "legacy_margin"

    passes = bool(magnitude_ok and majority and tail_ok and dd_ok)

    # ---- Y1 DOĞRULAMA: DSR (ADVISORY) + ADAY GETİRİ DEFTERİ (Hafta 3a, 2026-07-30) -------------
    # DSR, kapının SORMADIĞI soruyu sorar: "kaç aday denedik de bu geçti?" Aşınma defteri o yükü
    # SAYIYOR ve marja çeviriyor; DSR onu Sharpe'ın kendi ölçeğinde bir OLASILIĞA çevirir
    # (Bailey & López de Prado 2014, çarpıklık/basıklık düzeltmeli).
    #
    # ADVISORY — `passes` YUKARIDA HESAPLANDI VE BU BLOK ONA DOKUNMAZ. Bu, bilinçli bir sıralamadır:
    # DSR alanı `passes` satırının ALTINDA üretilir, yani hükmü değiştirmesi kod düzeninde de
    # imkânsızdır. Hard-gate'e geçiş (ROADMAP §3.1 önerisi: DSR>0.95) AYRI bir operatör kararıdır ve
    # kapı yasasının passes-semantiği bu turda DEĞİŞMEZ.
    #
    # DENEME SAYISI İKİ KANALDAN: aşınma defterinin bu pencereye ömür-boyu sorgu sayısı (oturumlar
    # arası seçilim) + `k_probes` (oturum içi çoklu test). Toplamak kasıtlı — aynı sınava sorulan her
    # soru, ister aylar arayla ister aynı gece, seçilim baskısına eşit katkı yapar.
    #
    # DEFTER YAZIMI YALNIZ RESMÎ DEĞERLENDİRMEDE (`record_erosion`): `_gate_eval` arama döngüsünde
    # binlerce kez çağrılıyor; her çağrıda yazan bir defter "kaç aday değerlendirildi" değil "kaç kez
    # fonksiyon çağrıldı" ölçerdi (oos_erosion'ın birebir aynı dersi). Deneme-Sharpe varyansı da
    # yalnız o yolda ÖLÇÜLÜR (defter okuması hot-path'e girmesin); arama yolunda null yaklaşımı
    # kullanılır ve `varyans_kaynagi` hangisinin geçerli olduğunu çıktının içinde söyler.
    from . import score as _score_mod, validation
    _cts_all = cand.get("_trades_search") or []
    _ret = [float(t.get("pnl_dollars") or 0.0) / float(_score_mod.START_EQUITY) for t in _cts_all]
    _n_trials = int(erosion.get("queries") or 0) + int(k_probes or 1)
    _trial_sh = None
    if record_erosion:
        # Literal dosya adı DEĞİL `validation.ledger()`: buradaki okumanın amacı YASA 6 tüketiciliği
        # değil (o iş `analytics.validation_trio`da yapılıyor), yalnız geçmiş adayların Sharpe'larını
        # almak. Aynı dosya adını üçüncü bir yerde tekrarlamak sürüklenme riski olurdu.
        _trial_sh = [r.get("sharpe_gozlem") for r in validation.ledger()
                     if r.get("sharpe_gozlem") is not None]
    dsr = validation.deflated_sharpe(_ret, _n_trials, _trial_sh)

    gate = {"incumbent_oos": inc_oos, "candidate_oos": cand_oos, "margin": effective_margin,
            # ---- PENCERE DAMGASI (HOLDOUT ROTASYONU R1, 2026-07-30) ----
            # `fingerprint` geometrinin HASH'idir — makine için yeter, insan için yetmez. Bir kapı
            # kaydını altı ay sonra okuyan biri, o `p`/`ΔS`in HANGİ SINAV KÂĞIDINA ait olduğunu 16
            # haneli bir hash'ten çıkarmak zorunda kalmamalı. `pencere_id` o soruyu tek kelimeyle
            # cevaplar ve HABERSİZ KIYASI imkânsız yapar: R0 kaydıyla R1 kaydını yan yana koyan
            # okuyucu, iki farklı kimliği GÖRÜR. Geçiş öncesi kayıtlarda alan YOKTUR ve yokluğu
            # "R1 öncesi" demektir (retro damga yasağı — eski kayıtlar geriye dönük damgalanmaz).
            "pencere_id": dataset.ROTATION_ID, "pencere_rotasyon_tarihi": dataset.ROTATION_DATE,
            "pencere_kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI,
            # DSR: ADVISORY alan — `passes` hükmüne GİRMEZ (bkz. yukarıdaki blok). None =
            # ölçülemedi (seri DSR_MIN_N altında ya da varyansı sıfır), 0.0 DEĞİL.
            "dsr": dsr, "dsr_n_trials": _n_trials,
            # ROL METNİ v130'da GÜNCELLENDİ ama "ADVISORY" KELİMESİ YERİNDE KALDI ve bu doğrudur:
            # DSR `_gate_eval`in `passes` hükmüne HÂLÂ girmez (blok `passes` satırının ALTINDA).
            # Sertlik SHIP yolunda (`_submit_locked`) ve MOD-FARKINDALIKLIDIR — iki ayrı yerdeki
            # iki ayrı hüküm tek cümlede karışmasın.
            "dsr_rol": ("ADVISORY (KAPI) — passes hükmüne girmez; SHIP yolunda mod-farkındalıklı: "
                        "paper=damga · gerçek-para=SERT fail-closed (v130)"),
            # `margin` ARTIK YÜRÜRLÜKTEKİ marjdır (taban + aşınma). Tabanı ayrı yazmak şart: kapı
            # kaydını sonradan okuyan biri 0.03 görüp "GATE_MARGIN değişmiş" sanmasın.
            "gate_margin_base": GATE_MARGIN, "erosion": erosion,
            # ---- PARA-v3 DAMGASI (2026-07-30) ----
            # Bir kapı kaydını altı ay sonra okuyan biri, o `search_p`nin HANGİ yasanın p'si
            # olduğunu tahmin etmek zorunda kalmamalı. Damga + geçiş tarihi kayda GİRER; geçiş
            # ÖNCESİ kayıtlarda alan YOKTUR ve yokluğu "eski bileşik yasa" demektir (retro damga
            # yasağı — eski kayıtlar geriye dönük damgalanmaz).
            "yasa_surumu": (shadowlaw.YASA_SURUMU if law == "probabilistic" else "eski_bilesik_marj"),
            "yasa_gecis_tarihi": shadowlaw.YASA_GECIS_TARIHI, "yasa_metni": shadowlaw.YASA_METNI,
            # KARAR skorları PARA ölçeğinde (yasanın gerçekten okuduğu sayılar). `incumbent_oos`/
            # `candidate_oos` bileşik RAPOR metriği olarak yerinde kalır — ikisi AYRI satırdır.
            "incumbent_para": inc_para, "candidate_para": cand_para,
            "money_gate_margin": MONEY_GATE_MARGIN,
            "erosion_margin_para": erosion_margin_para,
            # DÜŞÜŞ VETOSU: skordan çıkan bacağın sert kapıdaki hâli (tek yönlü)
            "incumbent_dd": None if inc_dd is None else round(float(inc_dd), 4),
            "candidate_dd": None if cand_dd is None else round(float(cand_dd), 4),
            "dd_ok": bool(dd_ok), "dd_durum": dd_durum, "dd_veto_margin": DD_VETO_MARGIN,
            "gate_law": law, "k_probes": k_probes, **prob.as_gate_fields("search"),
            "incumbent_folds": inc_folds, "candidate_folds": cand_folds,
            "fold_law": fold_law, "fold_bounds": fold_bounds,
            # Hedef (FOLD_TARGET_N) sınavı KOLAYLAŞTIRMAK için kullanılmaz; tutup tutmadığı burada
            # ölçülür ki "fold'lar dengelendi" cümlesi kalitesiyle birlikte okunsun.
            "fold_target_met": (None if not fold_bounds else
                                bool(min(f["n"] for f in cand_folds) >= backtest.FOLD_TARGET_N
                                     and min(f["n"] for f in inc_folds) >= backtest.FOLD_TARGET_N)),
            "fold_wins": f"{fold_wins}/{fold_total}", "fold_uncontested": itiraz_edilmemis,
            "embargo_days": dataset.EMBARGO_DAYS,
            "incumbent_tail": inc_tail, "candidate_tail": cand_tail, "tail_ok": tail_ok,
            "candidate_holdout": cand["holdout_score"], "incumbent_holdout": inc["holdout_score"]}
    if passes:
        why = ""
    elif not magnitude_ok:
        why = mag_why or "büyüklük kapısı geçilemedi"
    elif not majority:
        why = (f"aday {itiraz_edilmemis} pencerede HİÇ işlem yapmadı (incumbent orada kanıt taşıyor) "
               f"— sınavın bir kısmına girmeyen aday sağlamlık iddia edemez"
               if itiraz_edilmemis else
               f"candidate lost the fold-robustness majority ({fold_wins}/{fold_total})")
    elif not dd_ok:
        # DÜŞÜŞ VETOSU (PARA-v3): skorda pazarlık konusuydu, artık pazarlık YOK.
        why = (f"aday OOS maks düşüşü incumbent'ı {DD_VETO_MARGIN} marjından fazla kötüleştiriyor "
               f"(düşüş {cand_dd:.4f} vs {inc_dd:.4f}) — düşüş vetosu")
    else:
        why = (f"candidate worsens OOS tail risk beyond {TAIL_MARGIN_R}R "
               f"(VaR {cand_tail['var_r']} vs {inc_tail['var_r']}, "
               f"CVaR {cand_tail['cvar_r']} vs {inc_tail['cvar_r']})")

    # ---- D1: ADAY GETİRİ SERİSİ KALICI DEFTERE (PBO'nun ham maddesi) ---------------------------
    # HÜKÜM YAZILDIKTAN SONRA, HÜKMÜ DEĞİŞTİRMEYEN BİR YAN ETKİ. `passes` ve `why` yukarıda
    # kesinleşti; buradaki yazım yalnız KAYIT tutar ve başarısız olursa (disk dolu, izin) kapı
    # kararı düşmez — `validation.record_candidate` uyarır ve None döner (YASA 4: sessiz değil,
    # ama bir doğrulama defterinin ship kararını durdurma yetkisi de yok).
    #
    # NEDEN SERİ, NEDEN SKOR DEĞİL: PBO, N adayın AYNI zaman ızgarasındaki getirilerini ister. Kapı
    # kaydı bugüne kadar yalnız `oos_score` taşıyordu — 19 geçmiş değerlendirmenin hiçbiri PBO'ya
    # girebilecek veri bırakmadı ve retro damga yasağı gereği geriye dönük üretilmeyecek.
    #
    # `oos_detail.components` DE SAKLANIR VE BU KENDİ BAŞINA BİR ÖLÇÜM BORCUNU KAPATIR: bileşik
    # skorun (0,5·ret + 0,3·dd + 0,2·sharpe) hangi teriminin bir adayı reddettiği bugüne kadar
    # HİÇBİR kayıtta yoktu (S1/S2 ve G3a ölçümleri yalnız `oos_score` yazdı, bu yüzden o vakaların
    # terim ayrıştırması artık yeniden koşmadan çıkarılamıyor). Bundan sonra her resmî
    # değerlendirmede duruyor.
    if record_erosion:
        _inc_p, _cand_p = inc.get("params") or {}, cand.get("params") or {}
        _degisen = {k: v for k, v in _cand_p.items() if _inc_p.get(k) != v}
        _od = cand.get("oos_detail") or {}
        validation.record_candidate({
            "ts": memory.now_iso(), "fingerprint": _fp,
            # PENCERE DAMGASI (R1, 2026-07-30): PBO/DSR bu defteri TEK POPÜLASYON sanarak okur.
            # `fingerprint` zaten geometriyi ayırt eder ama `pencere_id` onu OKUNABİLİR yapar —
            # ve tüketici uyarısı (ledgers sözleşmesi) bu alana dayanır: iki farklı `pencere_id`
            # iki farklı SINAV KÂĞIDIdır ve tek PBO ızgarasında karıştırılamaz.
            "pencere_id": dataset.ROTATION_ID,
            # ETİKET = değişen düğmeler. `_gate_eval` hipotezin adını GÖRMEZ (yalnız iki walk-forward
            # sözlüğü alır); param farkı aynı bilgiyi kendi kendine yeterek taşır.
            "etiket": ("·".join(f"{k}={v}" for k, v in sorted(_degisen.items())) or "degisiklik_yok"),
            "degisen_params": _degisen, "eval_regime": inc.get("eval_regime"),
            "oos_score": cand_oos, "incumbent_oos": inc_oos, "passes": passes,
            # PARA-v3: defter satırı da HANGİ YASA altında hüküm aldığını taşır. Yoksa geçiş
            # öncesi/sonrası satırlar aynı kolonda karışır ve PBO/DSR analizleri iki farklı
            # karar değişkenini tek popülasyon sanır.
            "yasa_surumu": (shadowlaw.YASA_SURUMU if law == "probabilistic" else "eski_bilesik_marj"),
            "oos_para": cand_para, "incumbent_para": inc_para,
            "dd_ok": bool(dd_ok), "candidate_dd": None if cand_dd is None else round(float(cand_dd), 4),
            "incumbent_dd": None if inc_dd is None else round(float(inc_dd), 4),
            "gate_law": law, "fold_wins": f"{fold_wins}/{fold_total}", "tail_ok": bool(tail_ok),
            "k_probes": int(k_probes or 1), "erosion_queries": erosion.get("queries"),
            "n_trials": _n_trials,
            "oos_components": _od.get("components"),
            "oos_ozet": {k: _od.get(k) for k in
                         ("n", "total_return", "realized_30d", "max_drawdown", "sharpe",
                          "sharpe_measurable", "avg_r", "win_rate")},
            "sharpe_gozlem": (dsr or {}).get("sharpe_gozlem"),
            "dsr": (dsr or {}).get("dsr"), "varyans_kaynagi": (dsr or {}).get("varyans_kaynagi"),
            # SERİ: (kapanış tarihi, gerçekleşen R). Tarih PBO'nun ortak ızgara anahtarıdır; R ise
            # `_fold_metrics` ve kuyruk vetosunun okuduğu AYNI alan (iki farklı getiri tanımı iki
            # farklı gerçek olurdu).
            "seri": [[str(t.get("ts_close") or "")[:10], round(float(t.get("r_multiple") or 0.0), 4)]
                     for t in _cts_all if t.get("ts_close")],
            "beyan": "ADVISORY defter — kapı passes semantiğine girmez (Hafta 3a)"})
    return passes, gate, why


# ---------------- deterministic fallback proposer ----------------
def _ledger_stats(hyps: list) -> dict:
    """Per-variable {trials, reward} from the hypothesis ledger. A 'trial' is a hypothesis the BACKTEST
    actually judged (shipped/live/promoted, rejected_by_backtest, or rolled_back); rejected_by_guard is
    structural (off-step/quota/immutable) — not evidence about the variable, so it is not counted.
    Reward is MAGNITUDE-aware: once the outcome loop has written a realized_delta the reward is that
    delta mapped to [0,1] (a change that shipped AND held up beats one that shipped and got rolled back),
    else it falls back to a binary ship reward. Regime knobs (var@regime) credit the base variable so
    regime-specific exploration still informs the global bandit."""
    stats: dict = {}
    for h in hyps:
        v, st = h.get("variable"), h.get("status")
        if not v or st not in ("live", "shipped", "accepted", "promoted", "rejected_by_backtest", "rolled_back"):
            continue
        base = str(v).split("@", 1)[0]
        s = stats.setdefault(base, {"trials": 0, "reward": 0.0})
        s["trials"] += 1
        rd = h.get("realized_delta")
        if rd is not None:
            s["reward"] += max(0.0, min(1.0, 0.5 + float(rd) * 5.0))   # delta∈[-0.1,0.1] → [0,1]
        else:
            s["reward"] += 1.0 if st in ("live", "shipped", "accepted", "promoted") else 0.0
    return stats


def _ucb_rank(candidates: list, hyps: list, c: float = 1.2) -> list:
    """Deterministic UCB1 ranking of tunable variables. Untried variables get +inf (optimism → explore
    first); tried ones score mean_reward + c·sqrt(ln(total)/trials). Ties break by name so the same
    ledger always yields the same order (reproducible, testable — no wall-clock/random)."""
    stats = _ledger_stats(hyps)
    total = max(1, sum(s["trials"] for s in stats.values()))
    # #4: çıkış-verimliliği dürtmesi — MFE muhasebesi "masada R kalıyor" diyorsa (rapor eşiği),
    # exit.* düğmeleri sıralamada KÜÇÜK bir bonus alır. Yalnız arama SIRASI etkilenir; kapı yasası,
    # ödüller ve karar mekanizması değişmez. Dosya yoksa bonus 0 → davranış birebir eski hal.
    try:
        _ee = store.read_json("exit_efficiency.json", {})
        exit_bonus = 0.05 if _ee.get("nudge_active") else 0.0
    except Exception as e:
        # YASA 4 (2026-07-21): dosya bozuksa dürtü sessizce KAPANIR ve arama sırası "masada R kalıyor"
        # bulgusunu hiç duymadan koşar. Davranış aynı kalır (bonus 0) ama artık nedeni görünür.
        _cache_warn("exit_efficiency_unreadable", e)
        exit_bonus = 0.0

    def ucb(v):
        s = stats.get(v)
        bonus = exit_bonus if str(v).startswith("exit.") else 0.0
        if not s or s["trials"] == 0:
            return float("inf")
        return s["reward"] / s["trials"] + c * math.sqrt(math.log(total) / s["trials"]) + bonus

    return sorted(candidates, key=lambda v: (-ucb(v), v))


def propose_deterministic(explore: bool = False) -> dict:
    """Form ONE single-variable hypothesis. No LLM, one_variable_only preserved.

    EMEKLİ EDİLMEDİ — OPERATÖR KALEMİ (temizlik turu 2026-07-30, av adayı #çürütüldü).
    AV İDDİASI: "üretim yolu kalmadı — `skills.axis2_cycle` bugün `recommend_from_attribution`ı
    DOĞRUDAN çağırıyor". Doğrulandı: Eksen-2 kolu artık buradan geçmiyor. AMA çürütme şu:
    bu fonksiyonun kalan tek yolu `reflect --auto` CLI'ıdır (aşağıda `main`) ve o CLI ÖLÜ DEĞİL —
    `README.md` satır 81'de operatörün elle koşturduğu komutlar listesinde yazılı duruyor
    ("force a reflection cycle (deterministic proposer — no LLM)"). Beyinsiz/kotasız bir gecede
    TEK hamle üretmenin elle tetiği budur; hermes'in canlı yolu onu çağırmaz (bkz. hermes.py
    ~2550'deki not). Belgesi: ROADMAP §6 OPERATÖR tablosu. Yeni bir üretim çağıranı EKLENMEZ —
    eklenirse aynı gecede iki yansıma yarışır (`_submit_locked`in engellediği hâl).

    Two selection modes over the SAME single-variable move:
      * exploit (default): a behavior heuristic reads recent exit reasons / win rate and nudges the
        one variable most implicated (stop-outs → wider stop, time-stops → shorter clock, …).
      * explore (--explore): a UCB1 bandit ranks ALL tunable variables by their historical ship-rate
        in the ledger, preferring under-tried ones, so the loop widens its search instead of hammering
        the same few knobs. Either way the result is a single validated-shape proposal for the gate."""
    strat = config.load_strategy()
    params = strat.get("params", {})
    bounds = config.bounds()
    hyps = memory.all_hypotheses()
    trades = store.read_jsonl("trades.jsonl", limit=40)
    reasons = Counter(t.get("exit_reason", "") for t in trades)
    n = max(1, len(trades))
    win_rate = sum(1 for t in trades if t.get("r_multiple", 0) > 0) / n if trades else 0.0

    def move(var, direction):
        b = bounds[var]
        lo, hi, step, typ = b["min"], b["max"], b["step"], b["type"]
        cur = params.get(var, lo)
        new = max(lo, min(hi, cur + direction * step))
        return int(new) if typ == "int" else round(new, 4)

    def explore_dir(var):
        b = bounds[var]
        mid = (b["min"] + b["max"]) / 2.0
        return +1 if params.get(var, mid) <= mid else -1   # step toward the untested half of the range

    def already_failed(var, val):
        for h in hyps:
            if h.get("variable") == var and guard._equalish(h.get("new"), val, bounds[var]["type"]) \
                    and h.get("status") in ("rejected_by_backtest", "rolled_back"):
                return True
        return False

    # exploit heuristic — the one variable most implicated by recent behavior
    if reasons.get("stop", 0) + reasons.get("stop_gap", 0) > 0.4 * n:
        hvar, hdir, hwhy = "stop_loss_atr_mult", +1, "stop-outs dominate — give trades more room"
    elif reasons.get("time_stop", 0) > 0.4 * n:
        hvar, hdir, hwhy = "exit.time_stop_days", -1, "many time-stops — cut dead trades sooner"
    elif win_rate < 0.45:
        hvar, hdir, hwhy = "entry.min_score", +1, "low win rate — tighten setup quality"
    else:
        hvar, hdir, hwhy = "entry.rs_rating_min", +1, "demand stronger relative strength"

    if explore:
        # in a NON-default regime, retarget the knob to that regime (var@regime) so the dormant
        # regime-conditional machinery actually gets exercised instead of only ever tuning globally.
        live_regime = store.read_json("regime.json", {}).get("regime")
        suffix = f"@{live_regime}" if live_regime in config.VALID_REGIMES and live_regime != "trend_up" else ""
        # walk the UCB ranking, skipping no-ops and known-failed values; fall back to the heuristic
        for var in _ucb_rank(list(bounds.keys()), hyps):
            direction = hdir if var == hvar else explore_dir(var)
            new = move(var, direction)
            if guard._equalish(params.get(var), new, bounds[var]["type"]) or already_failed(var + suffix, new):
                continue
            label = f"bandit(UCB) explore: {var}{suffix}" + (f" ({live_regime} rejimine özel)" if suffix else "")
            return _proposal(var + suffix, new, params, label, explore=True)
        var = hvar
    else:
        var = hvar

    new = move(var, hdir)
    return _proposal(var, new, params, hwhy, explore=False)


def _proposal(var, new, params, why, explore=False) -> dict:
    from . import skills, analytics
    recs = skills.recommend_from_attribution()      # Axis-2 from measured skill contribution (no LLM)
    # confidence anchored to the agent's OWN realized calibration (how often its past predictions held),
    # not a hardcoded constant — so confidence is itself honest once the outcome loop has data.
    cal = analytics.calibration()
    if cal.get("n", 0) >= 5 and cal.get("hit_rate") is not None:
        conf = round(0.30 + 0.40 * float(cal["hit_rate"]), 2)   # 0.30..0.70 from realized hit-rate
    else:
        conf = 0.4 if explore else 0.5                          # cold-start prior until 5 outcomes exist
    return {
        "source": "deterministic",
        "variable": var, "new": new, "old": params.get(var),
        "rationale": why,
        "predicted_direction": "improve_oos_score",
        "predicted_delta": 0.03,
        "confidence": conf,
        "regime": store.read_json("regime.json", {}).get("regime", "any"),
        "skill_recommendation": recs[0] if recs else None,
    }


# ---------------- the pipeline every hypothesis flows through ----------------
class _ProcessLock:
    """CROSS-PROCESS reflection lock (fcntl.flock on state/.reflect.lock). The in-process
    _reflect_lock in hermes_runtime can't stop a SECOND process (tmux `hermes --loop`, a manual
    `reflect --auto`) from shipping concurrently — two multi-minute reflections racing versioning.commit
    would clobber strategy.yaml/version state (audit #24). Non-blocking: the loser gets an honest
    'locked' result instead of silently corrupting."""
    def __enter__(self):
        import fcntl
        self.fh = open(config.STATE / ".reflect.lock", "w")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.held = True
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            self.held = False
        return self

    def __exit__(self, *a):
        try:
            if self.held:
                import fcntl
                fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass


def submit(proposal: dict, goal: dict | None = None, windows: tuple | None = None) -> dict:
    from . import health as _health, obs as _obs
    if _health.learn_halted():                 # Faz 3 (5a-4): öğrenme durduruldu — işlemler sürer,
        _obs.log("submit_blocked_learn_halt")  # ama YENİ versiyon ship edilemez (operatör bayrağı)
        return {"status": "learning_halted", "detail": "state/LEARN_HALT aktif — ship engellendi"}
    with _ProcessLock() as pl:
        if not pl.held:
            return {"status": "locked", "detail": "başka bir süreçte yansıma sürüyor — bu öneri atlandı"}
        return _submit_locked(proposal, goal, windows)


def _submit_locked(proposal: dict, goal: dict | None = None, windows: tuple | None = None) -> dict:
    goal = goal or config.goal()
    rec = proposal.get("skill_recommendation")       # Axis-2: record the skill note (operator applies it)
    if isinstance(rec, dict) and rec.get("skill"):
        from . import skills
        skills.record_recommendation(rec, source=proposal.get("source", "hermes"))
    bounds = config.bounds()
    current = config.load_strategy()
    params = current.get("params", {})
    hyps = memory.all_hypotheses()
    accepted = memory.accepted_this_month()

    # 1. GUARD (static)
    v = guard.validate_change(proposal, params, bounds, goal, hyps, accepted,
                              params_by_regime=current.get("params_by_regime"))
    base = {
        "variable": v.variable, "old": v.old, "new": v.new,
        "rationale": proposal.get("rationale", ""), "predicted_direction": proposal.get("predicted_direction"),
        "predicted_delta": proposal.get("predicted_delta"), "confidence": proposal.get("confidence"),
        "regime": proposal.get("regime", "any"), "source": proposal.get("source", "hermes"),
        "version_from": int(current.get("version", 1)),
        # Phase 3.3 telemetry: the market regime present when this hypothesis was FORMED (the eval-window
        # regime is written later by rollback.evaluate_outcomes). Lets us audit bull/bear proposal bias.
        "market_regime": store.read_json("regime.json", {}).get("regime", "any"),
    }
    if not v.ok:
        # H3 — BİLEŞİK ÖNERİ KUYRUĞA BURADA YAZILIR (guard'da DEĞİL). guard SAF kalmak zorunda:
        # sert zarf yasası (test_gate_statistics_v74) o modülde hiçbir defter/LLM/ağ kanalı
        # bulunmamasını çiviliyor ve bir kuyruk yazımı tam olarak o kanaldır. guard yalnız ŞEKİL
        # hükmü verir (`composite_pending_queue`), yazımı ÇAĞIRAN yapar. Bileşik öneri CANLIYA
        # GİRMEZ — statüsü `rejected_by_guard` DEĞİL `queued_composite`tir: "reddedildi" demek,
        # ölçüme giden bir fikri mezarlığa yazmak olurdu (H2'nin ölü-aile sayımını da kirletirdi).
        comp = proposal.get("composite")
        if isinstance(comp, dict) and comp and any("composite_pending_queue" in str(r)
                                                   for r in v.reasons):
            from . import hermes_composite
            res = hermes_composite.enqueue(comp, rationale=proposal.get("rationale", ""),
                                           source=proposal.get("source", "hermes"), bounds=bounds)
            rid = (res.get("row") or {}).get("id")
            hyp = memory.record({**base, "version_to": None, "status": "queued_composite",
                                 "reject_reasons": list(v.reasons) + [f"composite_id:{rid}"]})
            memory.distill_lessons()
            return {"status": "queued_composite", "composite_id": rid, "reasons": v.reasons,
                    "hypothesis": hyp, "beyan": "ölçüm sırasına girdi — ship yolu kapı + operatör"}
        hyp = memory.record({**base, "version_to": None, "status": "rejected_by_guard",
                             "reject_reasons": v.reasons})
        memory.distill_lessons()
        return {"status": "rejected_by_guard", "reasons": v.reasons, "hypothesis": hyp}

    # 2. BACKTEST OOS GATE — purged+embargoed multi-fold, incumbent + candidate through the SAME engine
    # and the SAME windows (w). windows=None → dataset.* → identical to production; the sprint passes a
    # calendar-shifted w so selection stays disjoint from its forward eval window.
    bars, index = dataset.load()
    w = windows or _default_windows()
    candidate = versioning.bump(current, v.variable, v.new, note=proposal.get("rationale", ""))
    # Phase 3 regime isolation: a var@regime hypothesis is graded ONLY on that regime's trades —
    # incumbent AND candidate on the identical slice. The min_sample floor applies to the slice, so a
    # thin regime yields score=None and the gate honestly refuses to ship (no small-sample overfits).
    ereg = _eval_regime_of(v.variable)
    inc = _wf_cached(params_of(current), int(current.get("version", 1)), bars, index, goal,
                     current.get("params_by_regime"), windows=w, eval_regime=ereg)
    cand = backtest.walk_forward(params_of(candidate), bars, index, goal,
                                 w[0], w[1], w[2], w[3], strategy_version=candidate["version"],
                                 oos_folds=w[4], embargo_days=w[5],
                                 params_by_regime=candidate.get("params_by_regime"), eval_regime=ereg)

    k_probes = int(proposal.get("probes_tested", 1) or 1)   # aramadan gelen K → kazanan-laneti cezası
    # RESMÎ KAPI DEĞERLENDİRMESİ — aşınma sayacına DÜŞER (ship yetkisi olan tek yol).
    passes, gate, why = _gate_eval(inc, cand, k_probes=k_probes, record_erosion=True)
    gate["eval_regime"] = ereg                  # audit: which population graded this hypothesis
    cand_oos = cand["oos_score"]

    if not passes:
        hyp = memory.record({**base, "version_to": None, "status": "rejected_by_backtest",
                             "backtest": gate, "reject_reasons": [why]})
        memory.distill_lessons()
        return {"status": "rejected_by_backtest", "gate": gate, "hypothesis": hyp}

    # v3 TEYİT YÜRÜYÜŞÜ: aramanın hiç dokunmadığı Confirm-OOS (%30) diliminde P(ΔS>0) ≥ p_confirm.
    # Arama dilimi ne kadar parlak olursa olsun teyit veremeyen aday REDDEDİLİR — deftere yazılan
    # predicted_delta da teyit dilimindeki SAPMASIZ ortalama farktır (dürüst kalibrasyon; v2'nin
    # +0.059→−0.036 dersinin kurumsallaşması). Dilim yoksa (legacy ortam) adım atlanır.
    from .oos_pipeline import OutOfSamplePipeline
    conf = OutOfSamplePipeline(goal).confirm(inc, cand)
    gate.update(conf.as_gate_fields("confirm"))
    if conf.law == "probabilistic":
        if not conf.passes:
            gate["confirm_failed"] = True
            hyp = memory.record({**base, "version_to": None, "status": "rejected_by_confirmation",
                                 "backtest": gate,
                                 "reject_reasons": [f"teyit dilimi: {conf.why}"]})
            memory.distill_lessons()
            return {"status": "rejected_by_confirmation", "gate": gate, "hypothesis": hyp}
        base["predicted_delta_search"] = base.get("predicted_delta")   # şişkin arama tahmini (audit)
        base["predicted_delta"] = conf.mean_delta                      # sapmasız teyit deltası

    # ---- 2c. Y1 SERT KAPI: DSR (MOD-FARKINDALIKLI) + PBO (İKİ MODDA SERT) ----------------------
    # (DSR hard-gate turu, 2026-07-30 — operatör onaylı; ROADMAP §3.1 Y1 hard-gate kalemi)
    #
    # NEREDE DURDUĞU BİR TASARIM KARARIDIR. Kural `_gate_eval`in İÇİNDE DEĞİL, SHIP yolunda:
    #   * `_gate_eval` arama döngüsünde binlerce kez çağrılıyor ve `passes` semantiği ORADA
    #     değişmedi — DSR o fonksiyonda hâlâ `passes` satırının ALTINDA üretilir, yani hükme
    #     girmesi kod düzeninde imkânsız kalır (Hafta 3a'nın kasıtlı sıralaması korundu).
    #   * SHIP yolu ise "bu sürüm CANLI DEFTERE giriyor" noktasıdır ve bu turda sertleşen tam
    #     olarak o noktadır. Aramayı sertleştirmek, ölçüm aracını ölçüm yapmadan kısmak olurdu.
    #
    # EŞİKLER BURADA YAZILI DEĞİL: `validation.DSR_HARD_MIN`/`PBO_HARD_MAX` ve hüküm fonksiyonları
    # (`dsr_kapi`/`pbo_kapi`) TEK yerdedir; Faz-6 kilit zinciri (`health.faz6_kilitleri`) AYNI
    # fonksiyonları okur. Bir eşiğin iki kopyası, sessizce ayrışan iki kapı demektir.
    #
    # MOD FARKI VE GEREKÇESİ (mühürlü tasarım):
    #   * DSR — kâğıtta BLOKLAMAZ, yalnız damga (`dsr_dusuk`/`dsr_durum`). Kâğıt evrimi ÖLÇÜM
    #     ARACIDIR; ana defterin öğrenme hızını istatistiksel bir uyarıyla kısmak, kanıt üretimini
    #     kanıt olmadan yavaşlatmak olurdu. Gerçek-para bağlamında SERT ve FAIL-CLOSED.
    #   * PBO — İKİ MODDA DA SERT (ölçülebilirse). Bu bir aday testi değil SÜREÇ testidir: aşırı-
    #     uydurulmuş bir SEÇİM SÜRECİNDEN çıkan aday kâğıda bile inmemeli, çünkü kâğıt defter o
    #     adayın kanıtı olarak birikir ve süreç bozuksa biriken şey kanıt değil gürültüdür.
    #
    # PBO TABANI TEK PENCEREDEN (R1 düzeltmesindeki havuzlama yasağı — ledgers sözleşmesi): iki
    # `pencere_id` iki AYRI sınav kâğıdıdır ve `_matris` ızgaraları BİRLEŞTİRDİĞİ için havuzlanan
    # bir PBO, kesişmeyen dönemleri sıfırlarla doldurup gürültüyü "aşırı-uydurma yok" diye okurdu.
    # Damgasız satır = R1 ÖNCESİ ve paydaya GİRMEZ. Bugünkü sonuç: yürürlükteki pencerede taban
    # dolmadığı için PBO dürüstçe ÖLÇÜLEMEDİ döner ve kâğıtta veto ETMEZ (uygulanamayan kontrol
    # veto olamaz) — canlı davranış bu turda değişmez, kapı gelecekteki tabanı bekler.
    from . import validation as _val
    _live = config.live_enabled()
    _dsr_kapi = _val.dsr_kapi((gate.get("dsr") or {}).get("dsr"), live=_live)
    _pbo_olcum = _val.pbo_cscv([r for r in _val.ledger()
                                if r.get("pencere_id") == dataset.ROTATION_ID])
    _pbo_kapi = _val.pbo_kapi(_pbo_olcum, live=_live)
    # DAMGA HER YOLDA: ship edilen kayıt da, DSR/PBO yüzünden reddedilen kayıt da aynı alanları
    # taşır. Yalnız ret yolunda damgalamak, "düşük DSR ile ship edilmiş sürümler" sorusunu
    # cevaplanamaz yapardı — ve o soru bu turun VAR OLMA sebebidir.
    gate.update({"ship_modu": _dsr_kapi["mod"],
                 "dsr_dusuk": _dsr_kapi["dsr_dusuk"], "dsr_durum": _dsr_kapi["dsr_durum"],
                 "dsr_hard_kapi": _dsr_kapi, "pbo_hard_kapi": _pbo_kapi})
    if _dsr_kapi["ret"] or _pbo_kapi["ret"]:
        # STATÜ AYRI ADLANDIRILIR (`rejected_by_backtest` DEĞİL): backtest bu adayı GEÇİRDİ, onu
        # durduran şey doğrulama kapısıdır. Aynı kovaya atmak, kapı istatistiklerini ("backtest
        # neyi eliyor?") sessizce kirletirdi. Ayrıca `_ledger_stats` bu statüleri DENEME saymaz ve
        # bu doğrudur: bir PBO reddi o DEĞİŞKEN hakkında kanıt değildir (guard reddiyle aynı
        # yapısal sebep) — bandite ödül/ceza yazmak, süreç hükmünü değişken hükmü sanmak olurdu.
        _st = "rejected_by_dsr" if _dsr_kapi["ret"] else "rejected_by_pbo"
        hyp = memory.record({**base, "version_to": None, "status": _st, "backtest": gate,
                             "reject_reasons": [n for n in (_dsr_kapi["neden"],
                                                            _pbo_kapi["neden"]) if n]})
        memory.distill_lessons()
        return {"status": _st, "gate": gate, "hypothesis": hyp,
                "beyan": ("Y1 doğrulama sert kapısı — kapı ölçümü GEÇTİ, doğrulama kapısı "
                          "reddetti (mod: " + _dsr_kapi["mod"] + ")")}

    # 3. SHIP — version bump, snapshot, scoreboard, hypothesis -> live
    # Holdout is NEVER allowed to drive acceptance, but a big negative OOS→holdout gap is an overfit
    # tell — flag it (does not block the ship) so the overfit rate becomes observable over time.
    hold = cand.get("holdout_score")
    overfit_suspect = bool(hold is not None and cand_oos is not None and hold < cand_oos - HOLDOUT_DIVERGENCE)
    gate["overfit_suspect"] = overfit_suspect
    versioning.commit(candidate)
    # P3.d reachability: record the PARENT's incumbent OOS on the scoreboard BEFORE the candidate entry
    # (update_scoreboard sets current_version on every call — candidate must be written last so it wins).
    # Without this, a parent with no live trades AND no scoreboard row makes evaluate_outcomes par_score
    # None forever → the realized-outcome writeback (and its market_regime telemetry) never fires.
    # ONLY for global grading: a REGIME-SLICED incumbent score must never become the parent's global
    # baseline (rollback would then compare a global live score against a single-regime score — fabricated
    # deltas, false promote/rollback). Regime ships rely on the hypothesis gate record instead, and
    # rollback slices its live population to the same regime (population-consistent by construction).
    if ereg is None:
        # EBEVEYN SATIRI ARTIK HÜKÜMLE BİRLİKTE YAZILIR (2026-07-27). Eskiden yalnız bir SAYI
        # düşüyordu ve "bu sayı taban olarak KULLANILABİLİR mi" sorusu okuyanın çıkarımına kalıyordu;
        # `baseline.measure_parent_baseline` ise aynı satıra hükmüyle yazıyor. İki yol AYNI alan
        # ailesini konuşmazsa `rollback._no_parent_diagnostics` birinden okuduğunu diğerinde göremez
        # (dizgeler `baseline.py` ile birebir aynıdır — orada da "olculebilir").
        #
        # KAPSAM DÜRÜSTLÜĞÜ: buradaki hüküm YALNIZ ÖRNEKLEM boyutudur — ebeveyn, adayla birebir aynı
        # walk-forward'dan, aynı global nüfusta, ÖLÇÜLMÜŞ bir skorla geçti. FREKANS karşılaştırması
        # (backfill'in `baseline_freq_ratio`'su) burada YAPILAMAZ: aday tam bu saniye canlıya çıkıyor,
        # canlı defterinde sıfır işlem var ve olmayan bir sıklığı oranlamak uydurmaktır. O alan bu
        # yüzden YAZILMAZ (yokluk = ölçülmedi) ve `baseline_source` iki yolu ayırır; sonradan koşan
        # backfill kendi hükmünü ve oranını üstüne yazar.
        #
        # ÖLÇÜLMEMİŞ TABAN DALI YOK, ÇÜNKÜ ULAŞILAMAZ: `_gate_eval` (magnitude_ok, her iki yasada da)
        # `inc_oos is not None` şartını taşır — kapıdan geçen her global ship'in ebeveyn tabanı
        # TANIMLIDIR. 2026-07-22 öncesi böyle değildi ve v3 tam o delikten skorsuz ship edildi;
        # `test_ship_baseline_v100` bu şartı çiviliyor, gevşerse orası kırmızı yanar.
        #
        # `set_row_fields` DEĞİL `update_scoreboard`: ship yolu zaten `current_version`'ı yönetir ve
        # aday yazımı SONDA gelip kazanır (yukarıdaki sıra notu).
        versioning.update_scoreboard(
            int(current.get("version", 1)), backtest_oos=inc["oos_score"],
            baseline_verdict="olculebilir", baseline_source="ship_gate",
            baseline_measured_at=memory.now_iso(),
            baseline_n_trades=sum(int(f.get("n") or 0) for f in inc["oos_folds"]))
    # a regime ship's cand_oos is a SLICED score: store it regime-annotated so a future GLOBAL child of
    # this version can never mistake it for a global baseline (audit #18 — the plain-key fallbacks in
    # rollback read only unannotated keys, so annotated entries fall through to population-consistent
    # sources by construction).
    oos_field = {f"backtest_oos@{ereg}": cand_oos} if ereg else {"backtest_oos": cand_oos}
    versioning.update_scoreboard(candidate["version"], params=candidate["params"],
                                 parent=int(current.get("version", 1)),
                                 backtest_folds=cand["oos_folds"],
                                 backtest_holdout=cand["holdout_score"], overfit_suspect=overfit_suspect,
                                 changed_variable=v.variable, live_since=memory.now_iso(), **oos_field)
    # öneri #5: SPY-üstü alfa DAMGASI — kapının bileşeni DEĞİL (hedef fonksiyonunu uçuşta değiştirmek
    # karşılaştırılabilirliği bozar), yalnız her ship'e yazılan raporlanan-veto-adayı. 20-30 gözlem
    # birikince kapıya kuyruk-vetosu gibi eklenip eklenmeyeceğine veriyle karar verilir.
    try:
        from . import analytics
        base["vs_benchmark_at_ship"] = analytics.benchmark_relative()
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        pass
    hyp = memory.record({**base, "version_to": candidate["version"], "status": "live",
                         "backtest": gate, "overfit_suspect": overfit_suspect})
    memory.distill_lessons()
    return {"status": "shipped", "version": candidate["version"], "gate": gate, "hypothesis": hyp}


def params_of(strategy: dict) -> dict:
    return strategy.get("params", {})


# ---------------- coordinate-descent search (the escape from the ±1 trap) ----------------
# A single ±1-step move almost never clears +0.02 OOS, so the deterministic proposer re-hammered the same
# 3-4 dead moves forever and nothing ever shipped. This searches SEVERAL values per knob across ALL knobs,
# magnitude-first (bigger moves first), through the SAME _gate_eval law. It NOMINATES; submit() still SHIPS.
_PROBE_CACHE: dict = {}
# #3 SONDA ÖNBELLEĞİ DİSKE: ısınma sprintleri her yeniden başlatmada aynı walk-forward'ları yeniden
# hesaplıyordu (bellek-içi önbellek uçucu). Sonuçlar bar-revizyon anahtarlı tek JSON'da birikir:
# sprintler üst üste eklenir, 20 dakikalık aramalar önbellek isabetiyle kısalır. Revizyon uyuşmayan
# dosya YOK sayılır (bayat bar dersi). LRU tavanı: dosya şişmesin.
PROBE_DISK_FILE = "probe_cache.json"
PROBE_REV_FILE = "wf_cache_rev.json"
PROBE_DISK_CAP = 300
_PROBE_DISK_LOADED = False


def _probe_disk_load() -> None:
    global _PROBE_DISK_LOADED
    if _PROBE_DISK_LOADED:
        return
    _PROBE_DISK_LOADED = True
    try:
        blob = store.read_json(PROBE_DISK_FILE, None)
        rev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
        if blob and int(blob.get("rev", -1)) == rev:
            for k, v in (blob.get("entries") or {}).items():
                _PROBE_CACHE.setdefault(k, v)
    except Exception as e:
        # Aynı gerekçe (yasa 4): sonda önbelleği düşerse tek belirti, koordinat inişinin sessizce
        # kat kat yavaşlamasıdır — hata değil, miktar değişimi.
        _cache_warn("probe_cache_load_failed", e)


def _probe_disk_save() -> None:
    try:
        rev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
        keys = list(_PROBE_CACHE.keys())[-PROBE_DISK_CAP:]
        store.write_json(PROBE_DISK_FILE, {"rev": rev,
                                           "entries": {k: _PROBE_CACHE[k] for k in keys}})
    except Exception as e:
        _cache_warn("probe_cache_save_failed", e)


def _already_failed(var: str, val, hyps: list, bounds: dict) -> bool:
    base = str(var).split("@", 1)[0]
    typ = bounds[base]["type"] if base in bounds else "float"
    for h in hyps:
        if h.get("variable") == var and guard._equalish(h.get("new"), val, typ) \
                and h.get("status") in ("rejected_by_backtest", "rolled_back"):
            return True
    return False


def _probe_key(cand_strat: dict, var: str, new, w: tuple) -> str:
    wkey = tuple(w[:4]) + (tuple(w[4]), w[5])
    return repr((wkey,
                 tuple(sorted((k, round(float(x), 6)) for k, x in params_of(cand_strat).items())),
                 json.dumps(cand_strat.get("params_by_regime") or {}, sort_keys=True),
                 var, round(float(new), 6)))


def _probe_wf(cand_strat: dict, var: str, new, from_version: int, bars, index, goal: dict, w: tuple) -> dict:
    """Full walk_forward for a probe, cached by (window, from_version, var, val). A cached hit returns the
    FULL result so the caller re-runs the COMPLETE _gate_eval (magnitude AND folds AND tail) — never a
    magnitude-only shortcut (the judge-found cache bug). A var@regime probe is graded on its regime slice
    (Phase 3); the regime rides in `var`, so the cache key already separates sliced from global results."""
    wkey = tuple(w[:4]) + (tuple(w[4]), w[5])
    # Key on the FULL parameter world (flat + by_regime digests), not the version number: after a
    # rollback, versioning.bump REUSES the rolled-back version number with different params, so a
    # version-keyed cache would serve stale probe walk-forwards against a fresh incumbent. `var` stays
    # in the key because it determines eval_regime (the grading population).
    key = _probe_key(cand_strat, var, new, w)
    _probe_disk_load()
    if key not in _PROBE_CACHE:
        _PROBE_CACHE[key] = backtest.walk_forward(
            params_of(cand_strat), bars, index, goal, w[0], w[1], w[2], w[3],
            strategy_version=cand_strat["version"], oos_folds=w[4], embargo_days=w[5],
            params_by_regime=cand_strat.get("params_by_regime"), eval_regime=_eval_regime_of(var))
        _probe_disk_save()
    return _PROBE_CACHE[key]


# 250 evrende tek walk-forward dakikalara çıktı; sondalar bağımsız olduğundan süreç havuzuyla
# duvar-saati ~işçi-sayısı kadar kısalır. spawn + işçi-başı dataset yüklemesi (ilk görevde ~sn'ler,
# havuz arama boyunca yeniden kullanılır). HERHANGİ bir hata → sessizce sıralı yol (davranış birebir).
# Testler/sandbox bilerek kapsam dışı: bayrak yalnız serve.sh'ta açılır (spawn işçisi monkeypatch/
# sandbox STATE görmez — üretimde doğru, testte yanlış olurdu).
_POOL_WORKER_DATA: dict = {}


def _pool_worker_init():
    # AĞA ÇIKMAYAN yükleme ŞART: load() bayat önbellekte fetch eder, fetch corporate-action tespitiyle
    # bar CSV'lerini yeniden yazar — her işçi kendi load()'unu çağırdığında işçiler BİRBİRİNİN barlarını
    # değiştiriyor, aynı aramanın sondaları farklı bar durumlarında ölçülüyordu (2026-07-21, canlıda
    # bulundu). Ebeveyn load() ile önbelleği yerleştirir; işçiler o donmuş hali okur → birebir aynı barlar.
    from meridian import dataset as _ds
    _POOL_WORKER_DATA["bars"], _POOL_WORKER_DATA["index"] = _ds.load_cached()


def _pool_probe_job(args: dict) -> tuple:
    from meridian import backtest as _bt
    w = args["w"]
    wf = _bt.walk_forward(args["params"], _POOL_WORKER_DATA["bars"], _POOL_WORKER_DATA["index"],
                          args["goal"], w[0], w[1], w[2], w[3], strategy_version=args["version"],
                          oos_folds=list(w[4]), embargo_days=w[5],
                          params_by_regime=args["by_regime"], eval_regime=args["eval_regime"])
    return args["key"], wf


def _parallel_prefill_probes(probes, current, version, goal, w, regime) -> None:
    """Sonda walk-forward'larını havuzda ÖNCEDEN hesaplayıp _PROBE_CACHE'e doldurur; ana döngü
    değişmeden (deterministik sıra + K-ceza + erken-en-iyi seçimi) önbellekten tüketir."""
    if os.environ.get("MERIDIAN_PARALLEL_PROBES") != "1" or len(probes) < 2:
        return
    try:
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing as mp
        jobs = []
        for var, new in probes:
            cand = versioning.bump(current, var, new, note="search probe")
            key = _probe_key(cand, var, new, w)
            _probe_disk_load()
            if key in _PROBE_CACHE:
                continue
            jobs.append({"key": key, "params": params_of(cand), "by_regime": cand.get("params_by_regime"),
                         "version": cand["version"], "goal": goal, "w": (w[0], w[1], w[2], w[3], list(w[4]), w[5]),
                         "eval_regime": _eval_regime_of(var)})
        if not jobs:
            return
        workers = max(2, min(4, (os.cpu_count() or 4) - 2))
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=ctx,
                                 initializer=_pool_worker_init) as ex:
            for key, wf in ex.map(_pool_probe_job, jobs):
                _PROBE_CACHE[key] = wf
        _probe_disk_save()
        from . import obs as _obs
        _obs.log("parallel_probes_prefilled", n=len(jobs), workers=workers)
    except Exception as e:
        from . import obs as _obs
        _obs.warn("parallel_probes_failed", error=f"{type(e).__name__}: {e}",
                  detail="sıralı yola düşüldü — davranış birebir")


def prefill_incumbents(bars, index, regimes: list, goal: dict | None = None,
                       windows: tuple | None = None) -> dict:
    """#2 — boşta incumbent ön-hesabı: sıradaki muhtemel yansımaların (global + canlı rejim + ufku dolu
    arka plan rejimi) incumbent walk'ları ÖNCEDEN hesaplanıp diske yazılır. Yansıma tetiklendiğinde
    kapı sıfır beklemeyle açılır; boş CPU bileşik çalışır. Havuz açıksa varyantlar paralel; değilse
    sıralı (_wf_cached zaten diske yazar). Dönüş: {hesaplanan, önbellekte} — çağıran görmezden gelir."""
    goal = goal or config.goal()
    w = windows or _default_windows()
    current = config.load_strategy()
    params, version = params_of(current), int(current.get("version", 1))
    by_regime = current.get("params_by_regime")
    variants = [r if r in config.VALID_REGIMES else None for r in dict.fromkeys(regimes)]
    variants = list(dict.fromkeys(variants))
    computed = cached = 0
    _inc_disk_load()
    missing = []
    for er in variants:
        key = repr((version, tuple(sorted((k, round(float(x), 6)) for k, x in params.items())),
                    json.dumps(by_regime or {}, sort_keys=True),
                    tuple(w[:4]) + (tuple(w[4]), w[5]), er))
        (missing.append((key, er)) if key not in _INC_CACHE else None)
        cached += 1 if key in _INC_CACHE else 0
    if missing and os.environ.get("MERIDIAN_PARALLEL_PROBES") == "1" and len(missing) > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor
            import multiprocessing as mp
            jobs = [{"key": k, "params": params, "by_regime": by_regime, "version": version,
                     "goal": goal, "w": (w[0], w[1], w[2], w[3], list(w[4]), w[5]), "eval_regime": er}
                    for k, er in missing]
            ctx = mp.get_context("spawn")
            with ProcessPoolExecutor(max_workers=min(len(jobs), 3), mp_context=ctx,
                                     initializer=_pool_worker_init) as ex:
                for key, wf in ex.map(_pool_probe_job, jobs):
                    _INC_CACHE[key] = wf
                    computed += 1
            _inc_disk_save()
        except Exception as e:
            from . import obs as _obs
            _obs.warn("incumbent_prefill_pool_failed", error=f"{type(e).__name__}: {e}")
            missing = [(k, er) for k, er in missing if k not in _INC_CACHE]
    for _k, er in missing:
        if _k not in _INC_CACHE:
            _wf_cached(params, version, bars, index, goal, by_regime, windows=w, eval_regime=er)
            computed += 1
    if computed:
        from . import obs as _obs
        _obs.log("incumbents_prefilled", computed=computed, cached=cached,
                 regimes=[r or "global" for r in variants])
    return {"computed": computed, "cached": cached}


def coordinate_descent_search(bars, index, goal: dict | None = None, *, windows: tuple | None = None,
                              k_max: int = 3, budget: int = 10, tried: set | None = None,
                              on_probe=None, regime: str | None = None,
                              max_minutes: float | None = None,
                              deadline_ts: float | None = None) -> dict:
    """Walk the incumbent ONCE, then probe up to `budget` single-variable candidates (magnitude-first,
    breadth across UCB-ranked knobs) through the SAME OOS gate. Returns the best gate-CLEARING probe (or
    None). Probes are NOT recorded as hypotheses — a probe that lost vs this incumbent is not a permanent
    dead end (unlike a real submit rejection).
    regime (Phase 3): a REGIME-TARGETED search — every probe becomes var@regime (routed into
    params_by_regime by versioning.bump) and BOTH incumbent and candidates are graded only on that
    regime's trades. The current value each probe steps from is the regime override when one exists,
    else the global value (that IS the effective value the regime trades under today).

    SÜRE TAVANI (WP-H/H11, 2026-07-31) — `max_minutes` / `deadline_ts`, VARSAYILAN YOK.
    Vaka: `hermes_runtime._warmup_sprint` bu aramayı hermes döngüsünün KENDİ iş parçacığında koşturur
    ve nominal süresi 1-5 SAATtir. O süre boyunca döngü bir sonraki `hermes_poll` nabzına gelemez;
    bekçi 8 saatte MECHANISM_STALE üretir ve operatör hiçbir arıza yokken alarma koşar. Daha kötüsü:
    bekçinin elinde ALARM'dan başka bir araç yoktu — İPTAL edemiyordu.

    NEDEN MEVCUT `MERIDIAN_SEARCH_MAX_MIN` YETMİYOR (ölçüldü, aşağıdaki `_max_min`): o tavan yalnız
    TAZE hesapları ATLAR, aramayı DURDURMAZ — döngü kalan sondaları (önbellekten) dolaşmaya devam
    eder ve her biri yine tam `_gate_eval` koşar. Yani o tavan K sayımını dürüst tutmak için vardır,
    duvar-saatini bağlamak için değil. Bu tavan aramanın KENDİSİNİ bitirir.

    KİBAR-İPTAL, YARIM SONUÇ DEĞİL: tavan aşıldığında o ana dek BİTMİŞ sondalarla normal bir sonuç
    döner (`best` dahil — kapıyı geçmiş bir aday, arama kesildi diye çöpe atılmaz). Kesintinin
    KENDİSİ sonuçta damgalıdır (`kesildi`/`sebep`/`kalan_sonda`), çünkü "10 sondadan 3'ü değerlendi"
    ile "yalnız 3 sonda vardı" AYNI sözlükle temsil edilirse sonraki okuyucu aramayı eksik değil
    KÜÇÜK sanır. `kesildi` kesilmeyen koşumlarda da (False olarak) yazılır: alanın YOKLUĞU ile
    "kesilmedi" birbirine karışmasın.

    K SAYIMI DOKUNULMAZ: kapıya giden K = PLANLANAN toplam sonda sayısıdır (`total`), değerlendirilen
    değil. Kesinti K'yı küçültseydi kazananın-laneti cezası hafifler ve tavan, kapıyı GEVŞETEN bir
    kolaylık hâline gelirdi — süre tavanının kalite üzerinde yetkisi yoktur."""
    # `_time` BURADA içe aktarılır (eskiden sonda döngüsünün hemen üstündeydi): süre tavanı ondan
    # ÖNCE, fonksiyonun ilk satırında saat okumak zorunda. Tek alias kalır — aynı modülün iki adı,
    # ikisinden birinin sessizce farklı bir saat okuduğu izlenimi verirdi.
    import time as _time
    # TAVAN SAATİ EN BAŞTA BAŞLAR — incumbent yürüyüşü DAHİL. Sayacı sonda döngüsünde başlatmak,
    # tavanın aramanın en pahalı tek adımını (incumbent walk-forward) hiç ölçmemesi demekti: 5 saatlik
    # bir tavan, incumbent 5 saat sürdüğünde de "aşılmamış" görünürdü.
    _t_basla = _time.time()
    _tavan_ts = None
    if deadline_ts is not None:
        _tavan_ts = float(deadline_ts)
    elif max_minutes is not None and float(max_minutes) > 0:
        _tavan_ts = _t_basla + float(max_minutes) * 60.0

    def _tavan_asildi() -> bool:
        return _tavan_ts is not None and _time.time() > _tavan_ts

    def _kesinti(evaluated: int, kalan: int) -> dict:
        """Kesinti damgası + YASA 4 kaydı (gerekçe ≥20 karakter): sessiz bir kesinti, kısa bir
        aramadan ayırt edilemez ve okuyucu aramanın eksik olduğunu ASLA öğrenemez.

        `kalan_sonda` = DÖNGÜNÜN HİÇ ULAŞMADIĞI sonda sayısı. `planlanan_sonda - evaluated` ile
        AYNI ŞEY DEĞİLDİR ve olmamalıdır: aradaki fark `skipped_wallclock`tur — o sondalara ULAŞILDI
        (ve K sayımında dururlar), yalnız taze hesapları `MERIDIAN_SEARCH_MAX_MIN` yüzünden
        atlandı. İkisini tek sayıya indirmek, iki farklı eksikliği (hiç bakılmadı / bakıldı ama
        hesaplanmadı) ayırt edilemez kılardı."""
        gecen = round((_time.time() - _t_basla) / 60.0, 2)
        damga = {"kesildi": True, "sebep": "sure_tavani",
                 "tavan_dk": (round((_tavan_ts - _t_basla) / 60.0, 2) if _tavan_ts else None),
                 "gecen_dk": gecen, "kalan_sonda": int(kalan)}
        try:
            from . import obs as _obs_k
            _obs_k.log("search_sure_tavani_kesildi", evaluated=evaluated, kalan_sonda=int(kalan),
                       gecen_dk=gecen, tavan_dk=damga["tavan_dk"], regime=regime,
                       detail="koordinat araması süre tavanına takıldı ve KİBARCA kesildi — biten "
                              "sondalarla dönüldü, kalanlar hiç değerlendirilmedi; K sayımı "
                              "planlanan toplam sonda üzerinden DEĞİŞMEDEN kaldı")
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kesinti damgası ZATEN dönüş sözlüğünde taşınıyor ve kayıt denemesi çağıranı düşüremez
            pass
        return damga

    goal = goal or config.goal()
    w = windows or _default_windows()
    bounds = config.bounds()
    current = config.load_strategy()
    params = params_of(current)
    version = int(current.get("version", 1))
    hyps = memory.all_hypotheses()
    tried = set() if tried is None else tried
    regime = regime if regime in config.VALID_REGIMES else None
    overrides = (current.get("params_by_regime") or {}).get(regime, {}) if regime else {}
    inc = _wf_cached(params, version, bars, index, goal, current.get("params_by_regime"), windows=w,
                     eval_regime=regime)
    inc_oos = inc.get("oos_score")
    ranked = _ucb_rank(list(bounds.keys()), hyps)   # untried knobs first (+inf), then by historical reward

    probes, seen = [], set()
    for k in range(k_max, 0, -1):                   # magnitude-first: biggest moves of every knob first
        for var in ranked:
            if regime and var.startswith("regime."):
                continue    # regime.* feeds regime DETECTION (pre-regime) — a @regime override is
                            # structurally dead; probing it burns budget on guaranteed rejections (#33)
            b = bounds[var]
            lo, hi, step, typ = b["min"], b["max"], b["step"], b["type"]
            cur = overrides.get(var, params.get(var, lo)) if regime else params.get(var, lo)
            pvar = f"{var}@{regime}" if regime else var
            for direction in (+1, -1):
                raw = cur + direction * k * step
                new = max(lo, min(hi, raw))
                new = int(round(new)) if typ == "int" else round(new, 4)
                if guard._equalish(new, cur, typ):
                    continue                        # clamped onto current → no-op
                sig = (pvar, new)
                if sig in seen or sig in tried or _already_failed(pvar, new, hyps, bounds):
                    continue
                seen.add(sig)
                probes.append(sig)
    # v10 #3 — UYARLANABİLİR BÜTÇE: `budget` artık TAZE (önbellek-ıskası) hesap sayısıdır. Önbellekte
    # hazır duran sonda BEDAVA değerlendirilir (bütçe yemez) — önbellek-sıcak gecelerde aynı sürede
    # 2-3 kat hipotez taranır; soğukta davranış birebir eski hal. K-cezası DÜRÜST kalır: kapıya giden
    # K = planlanan TOPLAM değerlendirme sayısı (bedavalar dahil — kazananın-laneti aday sayısını
    # fiyatlar, maliyetini değil). Duvar-saati tavanı yalnız taze hesapları keser; atlanan taze sonda
    # değerlendirilmez ama K'da sayılmaya devam eder (yalnız SIKILAŞTIRIR).
    _probe_disk_load()
    planned, fresh_planned = [], 0
    for sig in probes[:max(budget * 4, 40)]:
        var2, new2 = sig
        cand2 = versioning.bump(current, var2, new2, note="budget peek")
        cached = _probe_key(cand2, var2, new2, w) in _PROBE_CACHE
        if cached:
            planned.append(sig)
        elif fresh_planned < budget:
            planned.append(sig)
            fresh_planned += 1
    probes = planned
    _parallel_prefill_probes(probes, current, version, goal, w, regime)
    _t0 = _time.time()
    _max_min = float(os.environ.get("MERIDIAN_SEARCH_MAX_MIN", "35"))
    _fresh_done = _skipped_fresh = 0

    evaluated = cleared = 0
    best, trace = None, []
    total = len(probes)
    kesinti: dict = {"kesildi": False}
    if on_probe:
        # Publish the plan (total + incumbent) the MOMENT it is known. The incumbent walk above takes ~a
        # minute, during which the caller has no idea how big the run is — "başlıyor…" with no scale.
        try:
            on_probe(0, total, None, None, None, inc_oos, None, None)
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
    for i, (var, new) in enumerate(probes, 1):
        # TAVAN KONTROLÜ SONDALAR ARASINDA (sondanın İÇİNDE değil): tek bir walk-forward bölünemez;
        # ortasından kesmek yarım bir ölçüm bırakırdı ve yarım ölçüm, ölçüm değildir. Kesinti noktası
        # her zaman iki tam sondanın arasıdır — dönen `trace` bu yüzden hep tutarlı satırlar taşır.
        if _tavan_asildi():
            kesinti = _kesinti(evaluated, kalan=total - (i - 1))
            break
        tried.add((var, new))
        base_var = str(var).split("@", 1)[0]
        old = overrides.get(base_var, params.get(base_var)) if regime else params.get(base_var)
        cand_strat = versioning.bump(current, var, new, note="search probe")
        _is_cached = _probe_key(cand_strat, var, new, w) in _PROBE_CACHE
        if not _is_cached and (_time.time() - _t0) / 60.0 > _max_min:
            _skipped_fresh += 1                # duvar-saati doldu: taze hesap atla (K sayımda kalır → sıkı)
            continue
        if not _is_cached:
            _fresh_done += 1
        cand = _probe_wf(cand_strat, var, new, version, bars, index, goal, w)
        # RESMÎ: arama oturumu pencereye BİR soru sorar (K aday tek beyanla taşınır — bkz. oos_erosion
        # beyan (2)). Oturum içindeki her prob ayrı ayrı sayılsaydı aynı yük iki kez cezalandırılırdı.
        passes, gate, _why = _gate_eval(inc, cand, k_probes=total, record_erosion=True)   # FULL gate + K-aday cezası (winner's curse)
        evaluated += 1
        c_oos = cand.get("oos_score")
        trace.append({"variable": var, "new": new, "old": old,
                      "candidate_oos": c_oos, "incumbent_oos": inc_oos,
                      "fold_wins": gate["fold_wins"], "tail_ok": gate["tail_ok"], "passes": passes})
        if passes:
            cleared += 1
            # explicit None checks — `or -1e9` treated a legitimate 0.0 score as missing (audit #34)
            _c = c_oos if c_oos is not None else -1e9
            _b = best["candidate_oos"] if (best and best["candidate_oos"] is not None) else -1e9
            if best is None or _c > _b:
                best = {"variable": var, "new": new, "old": old,
                        "candidate_oos": c_oos, "incumbent_oos": inc_oos}
        if on_probe:                      # a walk_forward takes ~a minute — without this the caller is blind
            try:
                on_probe(i, total, var, new, c_oos, inc_oos, passes, best)
            except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
                pass                      # progress reporting must NEVER break the search
    return {"incumbent_oos": inc_oos, "evaluated": evaluated, "cleared": cleared,
            "fresh": _fresh_done, "cached_hits": evaluated - _fresh_done, "skipped_wallclock": _skipped_fresh,
            "best": best, "trace": trace[-40:], "regime": regime, "planlanan_sonda": total,
            **kesinti}


def search_and_submit(bars, index, goal: dict | None = None, *, windows: tuple | None = None,
                      k_max: int = 3, budget: int = 10, on_probe=None, regime: str | None = None) -> dict:
    """Search for a gate-clearing candidate, then hand the winner to submit() — which re-runs the identical
    gate and remains the SOLE ship authority. Nothing ships if no probe clears. predicted_delta is the
    MEASURED OOS lift (not a hardcoded 0.03), so a later realized_delta gives an honest calibration hit/miss.
    regime: run a REGIME-TARGETED search (all probes var@regime, graded on that regime's slice — Phase 3);
    submit() re-derives the same eval_regime from the winning variable's @suffix, so search and ship grade
    on the identical population."""
    goal = goal or config.goal()
    res = coordinate_descent_search(bars, index, goal, windows=windows, k_max=k_max, budget=budget,
                                    on_probe=on_probe, regime=regime)
    best = res.get("best")
    if not best:
        return {"status": "no_clearing_candidate", "search": res}
    from . import analytics
    cal = analytics.calibration()
    conf = round(0.30 + 0.40 * float(cal["hit_rate"]), 2) if (cal.get("n", 0) >= 5 and cal.get("hit_rate") is not None) else 0.5
    prop = {
        # neutral provenance: BOTH the live reflection and the sandbox sprint call this. Labelling it
        # "sprint_search" made a live ship look like it came from a sandbox — a lie in the ledger.
        "source": "coordinate_search",
        "variable": best["variable"], "new": best["new"], "old": best["old"],
        "rationale": (f"coordinate-descent: {best['variable']} {best['old']}→{best['new']} "
                      f"(OOS {best['incumbent_oos']}→{best['candidate_oos']})"),
        "predicted_direction": "improve_oos_score",
        "predicted_delta": round((best["candidate_oos"] or 0.0) - (best["incumbent_oos"] or 0.0), 4),
        "confidence": conf,
        "probes_tested": res.get("evaluated", 1),   # submit() kazanan-laneti cezasını buradan okur
        "regime": store.read_json("regime.json", {}).get("regime", "any"),
    }
    result = submit(prop, goal, windows=windows)
    result["search"] = res
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Meridian reflection — propose a strategy change.")
    ap.add_argument("--auto", action="store_true", help="use the deterministic fallback proposer")
    ap.add_argument("--hermes", action="store_true", help="hypothesis supplied by Hermes")
    ap.add_argument("--hypothesis", type=str, help="JSON hypothesis {variable,new,...}")
    ap.add_argument("--explore", action="store_true")
    args = ap.parse_args(argv)

    if args.hermes:
        if not args.hypothesis:
            raise SystemExit("--hermes requires --hypothesis '<json>'")
        proposal = json.loads(args.hypothesis)
        proposal.setdefault("source", "hermes")
    else:
        proposal = propose_deterministic(explore=args.explore)

    print(f"[reflect] proposal: {proposal['variable']} {proposal.get('old')} -> {proposal['new']}"
          f"  ({proposal.get('rationale','')})")
    result = submit(proposal)
    print(f"[reflect] result: {result['status']}")
    if result.get("gate"):
        print(f"[reflect] gate: {json.dumps(result['gate'])}")
    if result.get("reasons"):
        print(f"[reflect] reasons: {result['reasons']}")
    return result


if __name__ == "__main__":
    main()
