"""reflect.py — yansıma boru hattının motoru ve TEK ship kapısı: hipotez nereden gelirse gelsin
aynı dürüst yoldan geçer.

Ne yapar: bir hipotezi guard.validate_change → walk-forward OOS kapısı → teyit yürüyüşü →
DSR/PBO doğrulama kapısı → sürüm artırma + skor tahtası + defter kaydı zincirinden geçirir.
İki hipotez kaynağı aynı boru hattını kullanır: deterministik önerici (`--auto`; LLM daha
ortada yokken tüm halkayı kanıtlar) ve Hermes (`--hermes --hypothesis '<json>'`; beyin önerir,
motor doğrular ve kapılar). `coordinate_descent_search`/`search_and_submit` tüm düğmelerde
sistematik arama koşar ve kazananı yine aynı kapıya verir.

Kilit girişler: `submit`/`_submit_locked` (süreçler-arası fcntl kilidi altında tek ship
yetkisi), `_gate_eval` (TEK yasa — arama ve submit birebir aynısını okur, iki yerde iki yasa
sessizce ayrışırdı), `_wf_cached`/`clear_wf_caches` (incumbent walk-forward önbelleği,
bar-revizyon korumalı), `propose_deterministic` (UCB sıralı sezgisel önerici).

Değişmezler: öneri danışmadır, kararı kapı verir — motor ship eder, LLM etmez; büyüklük hükmü
dilim varken olasılıksaldır (blok-bootstrap P(ΔS>0) ≥ p_required(K); K = o oturumda denenen
aday sayısı, kazananın-laneti cezası), dilim yokken legacy nokta-marj (GATE_MARGIN) koşar ve
hangisinin koştuğu kapı kaydında damgalıdır; fold-çoğunluğu kanıt ister, kuyruk (VaR/CVaR) ve
düşüş vetoları tek yönlüdür; "ölçülemedi" üçüncü hâldir ve fail-closed'dur — asla "geçti"
sayılmaz; OOS aşınma defteri aynı pencereye sorulan her resmî soruyu sayar ve marjı yükseltir.

Okur/yazar: hypotheses.jsonl (memory.record — her hüküm, ret dahil, deftere iner),
inc_cache.json + probe_cache.json + wf_cache_rev.json (walk-forward önbellekleri, bar
revizyonuyla yaşar), strategy.yaml ve skor tahtası (versioning), aşınma/doğrulama defterleri
(oos_erosion, validation); goal.yaml ve bounds.yaml'ı config üzerinden okur."""
from __future__ import annotations
import argparse
import json
import os
import math
from collections import Counter

from . import config, store, guard, memory, versioning, backtest, dataset, oos_erosion, shadowlaw

GATE_MARGIN = 0.02   # candidate must beat incumbent OOS by at least this
TAIL_MARGIN_R = 0.5  # capital preservation: candidate may not raise OOS tail loss (VaR AND CVaR) by >this many R

# ---- PARA-v3: marj para ölçeğine çevrildi, düşüş vetosu eklendi --------------------------------
# `GATE_MARGIN` BİLEŞİK ölçekte tanımlıydı ve yasanın karar değişkeni artık PARA. İki sabit, tek
# kaynaktan (`shadowlaw`) gelir çünkü türetimleri ölçüme dayanır ve ölçüm kaydı orada durur:
#   MONEY_GATE_MARGIN = 0.004  ← 0.02 × σ(ΔS_v3)/σ(S_eski) = 0.02 × 0.1908 (σ-eşdeğerliği)
#   DD_VETO_MARGIN    = 0.08   ← düşüş bütçesinin YARISI (goal.max_drawdown=0,16, operatör
#                                kararı 2026-08-13) ve σ(düşüş)=0,0343'ün DIŞINDA — türetim
#                                `shadowlaw.DD_VETO_MARGIN` başlığında, sayı ORADAN gelir (burada kopya YOK)
# `GATE_MARGIN` SİLİNMEDİ ve 0.02 kaldı: LEGACY yolun (dilimsiz fikstür/sandbox) yasası odur ve o
# yol bileşik skor karşılaştırır — orada para ölçeği hesaplanamaz (dilim yok, span yok). Yani
# 0.02 artık "eski yasanın marjı", 0.004 ise "yürürlükteki yasanın marjı"dır ve hangisinin koştuğu
# kapı kaydındaki `yasa_surumu` damgasında yazılıdır.
DD_VETO_MARGIN = shadowlaw.DD_VETO_MARGIN      # düşüş vetosunun marjı (para-v3 ile eklendi)
MONEY_GATE_MARGIN = shadowlaw.MONEY_GATE_MARGIN  # GATE_MARGIN'ın para-ölçek eşdeğeri
HOLDOUT_DIVERGENCE = 0.10   # OOS→holdout drop beyond this flags overfit_suspect (does NOT block the ship)

# ---- AÇIK-POZİSYON DÜŞÜŞÜ: ÖLÇÜLÜR, HÜKÜM VERMEZ ----------------------------------------------
# EŞİK İCAT EDİLMEDİ, BU YÜZDEN BAĞLANMADI. M2M bacağı kapanmış-işlem bacağının YAPISINI aynen
# alır (aday > incumbent + marj, tek yönlü) ama `DD_VETO_MARGIN`in türetimi KAPANMIŞ-İŞLEM düşüş
# dağılımı üzerinde yapılmıştı: σ(düşüş)=0,0343 (blok-yeniden-örnekleme, 2000 replikasyon) ve "%8
# bütçenin yarısı". M2M eğrisinin düşüş dağılımı BAŞKA bir dağılımdır (açık pozisyonların çukurunu
# içerir, yani sistematik olarak DAHA GENİŞTİR) ve σ'sı ÖLÇÜLMEMİŞTİR. Ölçülmemiş bir dağılıma
# ölçülmüş bir marjı taşımak, tam olarak bu depoda "eşik sonradan seçildi" diye yasaklanan hamledir.
# Bu yüzden bacak ÖLÇÜLÜR ve kapı kaydına YAZILIR ama `passes`e GİRMEZ. Bağlanması için önce
# `research/cards/` altında bir ölçüm kartı gerekir (M2M düşüş σ'sı + marj türetimi).
# Bayrak yalnız O KARTIN ölçüm koşumları içindir; varsayılan KAPALI ve canlıda kapalı kalır.
DD_MTM_VETO_ENV = "MERIDIAN_DD_MTM_VETO"


def _dd_mtm_bagli() -> bool:
    """M2M düşüş bacağı `passes`e bağlı mı? Varsayılan HAYIR (eşik ölçülmedi)."""
    return os.environ.get(DD_MTM_VETO_ENV) == "1"


# incumbent walk-forward is identical across every candidate in a reflection session — compute once.
_INC_CACHE: dict = {}
INC_DISK_FILE = "inc_cache.json"     # incumbent walk'ları da bar-revizyonuyla diskte yaşar
INC_DISK_CAP = 40
_INC_DISK_LOADED = False

# Önbellek G/Ç uyarıları OLAY TÜRÜ BAŞINA bir kez: arama döngüsü bunları yüzlerce kez çağırır,
# tekrar tekrar uyarmak logu sele çevirir ve asıl sinyali gömer (yasa 4'ün amacı sinyal, gürültü değil).
_CACHE_WARNED: set = set()


def _cache_warn(event: str, exc: BaseException) -> None:
    """Önbellek G/Ç hatasını OLAY TÜRÜ BAŞINA BİR KEZ uyarı olarak düşer (YASA 4).

    Arama döngüsü bu yolu yüzlerce kez geçer; her seferinde uyarmak asıl sinyali log seline
    gömerdi. Kayıt kanalının kendisi düşerse sessiz kalır — telemetri aramayı düşüremez."""
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
    """Diskteki incumbent walk-forward önbelleğini süreç-içi `_INC_CACHE`e SÜREÇ BAŞINA bir kez yükler.

    Yalnız dosyadaki bar revizyonu yürürlükteki revizyonla AYNIYSA alınır — bayat barların walk'ı
    yeni barların adayıyla kıyaslanamaz. Okuma düşerse yalnız süre uzar, uyarı bırakılır."""
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
        # YASA 4: önbellek okuması sessizce düşerse hata görünmez, YALNIZ SÜRE uzar —
        # her aday incumbent walk-forward'ı sıfırdan hesaplar. "Refleksiyon neden 40 dakika sürüyor?"
        # sorusunun cevabı diskteki bozuk bir JSON olabilir; artık iz bırakıyor.
        _cache_warn("inc_cache_load_failed", e)


def _inc_disk_save() -> None:
    """Süreç-içi incumbent önbelleğinin SON `INC_DISK_CAP` girdisini yürürlükteki bar revizyonuyla
    damgalayıp diske yazar. Yazım düşerse önbellek hiç kalıcı olmaz (tek belirti yavaşlama) —
    bu yüzden uyarı bırakılır."""
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
    from the OLD bars would be compared against a candidate walked on the NEW bars.
    DİSK önbelleği de bar-revizyonuyla yaşar — revizyon burada artar, eski dosya silinir; bayat
    önbellek diskten de dönemez."""
    _INC_CACHE.clear()
    _PROBE_CACHE.clear()
    global _PROBE_DISK_LOADED, _INC_DISK_LOADED
    _PROBE_DISK_LOADED = False
    _INC_DISK_LOADED = False
    # MONOTON revizyon: eski hali oku-artır-yaz sayacıydı; okuma boş dönerse rev 1'e
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
    """Üretim pencere demeti: (IS_START, OOS_START, OOS_END, HOLDOUT_END, OOS_FOLDS, EMBARGO_DAYS).

    `dataset` sabitlerinden okunur; sprint aramaları kendi kaydırılmış pencerelerini verir."""
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


# ---- 2026-08-05: ANAHTAR YASAYI TAŞIR · TUR-İÇİ TEK HESAP · REVİZYON KORUMASI ----------
# ÖLÇÜLEN VAKA (canlı A1, 2026-08-04/05, py-spy): EOD döngüsü iki gece üst üste BİTMEDİ; yığın
# `scheduler.advance_once → arming.evaluate → _measure → _wf_cached → backtest.walk_forward →
# replay → scan_entry` içinde AKTİF dönüyordu.
#
# ASILMANIN KÖK NEDENİ BU DOSYADA DEĞİL (dürüstlük şartı): ölçüm MEŞRU-uzundu (canlıda 27-100 dk;
# bkz. `arming.py` başlığındaki ölçüm dökümü), yol nabız atmıyordu ve bekçi turu 45 dk'da
# öldürüyordu. Kilit `arming.py`deki SÜRE TAVANIYLA kırıldı. Aşağıdaki üç kusur o yolun ÜZERİNDE
# bulundu ve üçü de bağımsızdır; (a) bir DOĞRULUK açığıdır (hız değil), (b) ve (c) ise tavanın
# getirdiği arka-plan ipliğinin AÇTIĞI yeni yarışları kapatır.
#
#   (a) ANAHTAR YASAYI TAŞIMIYORDU. Anahtar (sürüm, paramlar, rejim-tablosu, pencere, eval_regime)
#       idi — `goal` YOKTU. 2026-08-03'te operatör `execution_v2`yi değiştirdi (limit
#       min(0,5·ATR,%1) → min(100·ATR,%4)) ve ÖLÇÜLDÜ ki bu yasa dolum sayısını da skoru da
#       değiştiriyor (aynı pencerede 157 vs 147 işlem, OOS 0,0572 vs 0,0221). Anahtarda yasa
#       olmayınca ESKİ yasayla yürünmüş bir incumbent'ın YENİ yasadaki bir kıyasa girmesini
#       ENGELLEYEN hiçbir şey yoktu. Açığın ÖMRÜ: süreç-içi `_INC_CACHE` süreç boyu yaşar; diskteki
#       `inc_cache.json` ise bir sonraki `clear_wf_caches`e (taze poll) kadar. Yani pencere dardı
#       ama SIFIR değildi — ve `windows`/`eval_regime`in anahtara eklenmesini gerektiren elma-armut
#       kusurunun BİREBİR aynısı, bu kez değişkeni OPERATÖR değiştiriyor. Yasanın parmak izi artık
#       anahtarın parçası: yasa değişince önbellek İSKA verir (bir kereye mahsus yeniden hesap).
#       TUR-İÇİ PAYLAŞIM BOZULMAZ: yasa bir tur boyunca sabittir (`config.goal()` lru-önbellekli,
#       dosya değişmez), yani aynı turdaki tekrar çağrılar AYNI anahtara düşer — tek hesap.
#
#   (b) AYNI ANAHTAR İKİ KEZ HESAPLANABİLİYORDU. `if key not in _INC_CACHE: hesapla` iki iş
#       parçacığı arasında yarışa açıktı ve süre tavanı bu yarışı GERÇEK kılıyor: `arming` ölçümü süre
#       tavanını aşarsa arka planda SÜRMEYE devam eder; bir sonraki tur aynı anahtarı isteseydi
#       İKİNCİ bir (canlıda ölçülen) 30+ dakikalık walk başlardı. Anahtar başına hesap kilidi:
#       ikinci çağıran BEKLER ve birincinin sonucunu kullanır.
#
#   (c) HESAP SÜRERKEN BARLAR TAZELENEBİLİYORDU. `clear_wf_caches()` HER taze poll'de koşar
#       (scheduler.py, `if fresh:` bloğu). Uzun bir walk sürerken temizlik geçerse, hesap bitince
#       sözlüğe yazmak TEMİZLENMİŞ önbelleğe ESKİ barların sonucunu geri koymak olurdu —
#       `clear_wf_caches`in kendi docstring'inde yasaklanan kusurun ta kendisi.
#       Revizyon hesaptan ÖNCE okunur ve sonra kıyaslanır; değiştiyse sonuç ÇAĞIRANA döner (o tur
#       kendi barlarıyla tutarlıdır) ama ÖNBELLEĞE YAZILMAZ.
import hashlib as _hl
import threading as _th

_WF_KILITLERI: dict = {}          # anahtar -> RLock (hesap kilidi; bkz. (b))
_WF_KILIT_GUARD = _th.Lock()


def _wf_kilidi(key: str):
    """Anahtar başına TEK kilit nesnesi. RLock (Lock değil): aynı iş parçacığının kazara yeniden
    girmesi bugün mümkün değil ama olursa kilitlenme yerine (eski davranış olan) yeniden hesap
    olur — bir teşhis yolu, süreci asla kilitlemez."""
    with _WF_KILIT_GUARD:
        lk = _WF_KILITLERI.get(key)
        if lk is None:
            lk = _WF_KILITLERI[key] = _th.RLock()
        return lk


def _wf_rev() -> int:
    """Yürürlükteki bar revizyonu (`clear_wf_caches` her tazelemede artırır). Okunamazsa 0 döner ve
    bu GÜVENLİDİR: hesap öncesi/sonrası aynı değeri (0) görür, yani okuma düşse davranış eski hâle
    (koşulsuz yazım) döner — kayıt da düşmez (`_cache_warn` bir kez uyarır)."""
    try:
        return int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
    except Exception as e:
        _cache_warn("wf_rev_read_failed", e)
        return 0


def _yasa_parmak(goal: dict) -> str:
    """DEĞİŞMEZ sözleşmenin (goal.yaml) parmak izi. TÜM sözlük hash'lenir, seçilmiş alanlar DEĞİL:
    "replay'i hangi anahtar etkiler" diye bir liste tutmak, bir gün eklenecek yeni bir icra
    düğmesinde sessizce yanılırdı — bugün kapatılan kusur zaten TAM O SINIFTAN.

    KARDEŞ KALEM, BU TURDA AÇILMADI (brief kapsamı `_wf_cached`ti): `_probe_key` (sprint sonda
    önbelleği, `_PROBE_CACHE`) yasa parmak izini HÂLÂ taşımıyor — aynı sınıf açıklık, farklı
    önbellek. Kapatılması `_PROBE_CACHE`in diskteki sürümünü de geçersizleştirir, o yüzden ayrı
    bir hüküm ister (Rol-1)."""
    try:
        ham = json.dumps(goal or {}, sort_keys=True, default=str)
    except Exception as e:
        _cache_warn("yasa_parmak_serialize_failed", e)
        ham = repr(goal)
    return _hl.sha256(ham.encode("utf-8")).hexdigest()[:16]


def _param_parmak(params: dict) -> tuple:
    """Paramların anahtar-sıralı (ad, değer) demeti — SAYISAL değerlerde eski davranışla bit-bit
    aynı (`round(float(x), 6)`). Sayısal OLMAYAN değer artık fırlatmıyor: silahlanma ölçümünün
    `entry.armed_extra` LİSTESİ `float()`e giremediği için aday walk'ları önbelleğe HİÇ
    giremiyordu (her tur sıfırdan hesap); kararlı JSON metniyle temsil edilir."""
    out = []
    for k in sorted(params or {}, key=str):
        x = params[k]
        try:
            out.append((str(k), round(float(x), 6)))
        except (TypeError, ValueError):  # sessiz-yutma: sayısal OLMAYAN param bir hata değil bir TÜRDÜR (liste/metin) — burada yakalanan şey "float'a çevrilemedi" bilgisidir ve cevabı uyarı değil kararlı JSON temsilidir; uyarmak her aday walk'ında log seli üretirdi
            out.append((str(k), json.dumps(x, sort_keys=True, default=str)))
    return tuple(out)


def _wf_key(params: dict, version: int, goal: dict, by_regime: dict | None,
            w: tuple, eval_regime: str | None) -> str:
    """İncumbent önbellek anahtarı — TEK KAYNAK.

    window IS part of the cache key — otherwise a sprint incumbent walked on shifted windows would
    collide with a production incumbent walked on dataset.* (the judge-found apples-to-oranges bug).
    eval_regime is ALSO part of the key: a regime-sliced incumbent score must never collide with the
    global incumbent score (same params, different grading population — same class of bug).
    goal (yasa) parmak izi AYNI GEREKÇEYLE anahtarın parçası — bkz. yukarıdaki (a).

    FONKSİYON OLMASININ SEBEBİ ÖLÇÜLDÜ (2026-08-05): `prefill_incumbents` bu ifadenin ELLE
    yazılmış bir KOPYASINI taşıyordu ve anahtar burada değişince kopya sessizce ıskalamaya başladı
    (test `test_prefill_incumbents_...` kırmızı döndü: "hepsi önbellekte" iddiası 3 hesap saydı).
    Aynı yasanın iki uygulaması deseninin bu depodaki N'inci vakası — kopya SİLİNDİ, iki çağıran
    da buradan okur."""
    return repr((version, _param_parmak(params),
                 json.dumps(by_regime or {}, sort_keys=True), tuple(w[:4]) + (tuple(w[4]), w[5]),
                 eval_regime, _yasa_parmak(goal)))


def _wf_cached(params: dict, version: int, bars, index, goal: dict, by_regime: dict | None = None,
               windows: tuple | None = None, eval_regime: str | None = None) -> dict:
    """Walk-forward'ı önbellekli koşar — aynı anahtar bir turda YALNIZ BİR KEZ hesaplanır.

    Anahtar `_wf_key`den gelir (paramlar + sürüm + yasa parmak izi + pencere + eval_regime).
    Anahtar başına hesap kilidi: ikinci çağıran bekler, birincinin sonucunu kullanır. Hesap
    sürerken barlar tazelenirse (revizyon değişti) sonuç ÇAĞIRANA döner ama ÖNBELLEĞE YAZILMAZ."""
    w = windows or _default_windows()
    key = _wf_key(params, version, goal, by_regime, w, eval_regime)
    _inc_disk_load()
    if key in _INC_CACHE:
        return _INC_CACHE[key]
    with _wf_kilidi(key):
        if key in _INC_CACHE:      # kilidi beklerken BAŞKA iplik hesapladı → tek hesap, bkz. (b)
            return _INC_CACHE[key]
        _rev0 = _wf_rev()
        sonuc = backtest.walk_forward(
            params, bars, index, goal, w[0], w[1], w[2], w[3], strategy_version=version,
            oos_folds=w[4], embargo_days=w[5], params_by_regime=by_regime, eval_regime=eval_regime)
        _rev1 = _wf_rev()
        if _rev1 == _rev0:
            _INC_CACHE[key] = sonuc
            _inc_disk_save()
        else:
            try:
                from . import obs as _obs_rev
                _obs_rev.warn("wf_cache_rev_changed", rev_basta=_rev0, rev_simdi=_rev1,
                              detail="walk-forward sürerken barlar tazelendi (clear_wf_caches) — "
                                     "sonuç ÇAĞIRANA döner ama ÖNBELLEĞE YAZILMAZ (denetim #30: "
                                     "eski barların walk'ı yeni barların adayıyla kıyaslanamaz)")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; ASIL koruma (önbelleğe yazmama) zaten uygulandı, bu satır yalnız onun ilanıdır
                pass
        return sonuc


def _gate_why(inc: dict, cand: dict, majority: bool, fold_wins: int, fold_total: int, tail_ok: bool,
              margin: float = GATE_MARGIN) -> str:
    """Reddin İNSAN OKUNUR gerekçesini üretir: hangi kapı dalı düşürdü (skor/marj, fold-çoğunluğu,
    kuyruk riski). Yalnız METİN üretir — hükmü `_gate_eval` verir.

    MARJ DIŞARIDAN GELİR, ÇIPLAK SABİT DEĞİL. `margin` parametresi olmadan bu fonksiyon çıplak
    `GATE_MARGIN` ile sınıyordu; oysa çağıran legacy dal hükmü `effective_margin = GATE_MARGIN +
    erosion_margin` ile veriyor. Aşınma marjı devredeyken (`extra_margin > 0`) ikisi AYRIŞIYORDU:
    hüküm "büyüklük düştü" derken gerekçe zinciri büyüklük dalını ATLIYOR, `majority`/`tail_ok`
    çağrıda sabit `True` olduğu için akış SON return'e düşüyor ve `cand_tail['var_r']` okunuyordu —
    legacy sözlüklerde `oos_tail_risk` yoktur, yani `TypeError: 'NoneType' object is not
    subscriptable`. Gerekçe üreten yol, hükmü veren yolla AYNI eşiği okumak zorundadır.

    KAPSAM BEYANI — BU ÜÇ DAL, HÜKMÜN BEŞİ DEĞİL: `_gate_eval`in `passes` bağlacı beş terimlidir
    ve sırası `magnitude_ok · majority · tail_ok · dd_ok · dd_mtm_ok` — yani KUYRUK ORADA 3.
    terimdir. `_gate_eval`in KENDİ gerekçe zinciri ise başka bir sıra izler: büyüklük → çoğunluk →
    düşüş → M2M düşüş → kuyruk; orada kuyruk 5. ve SONdur. Buradaki zincirde iki düşüş dalı HİÇ
    yoktur (büyüklük → çoğunluk → kuyruk); yani bu üç dalın göreli sırası `_gate_eval`in gerekçe
    zincirininkiyle aynı, `passes` bağlacınınkiyle DEĞİLDİR.

    EKSİKLİK BUGÜN NEDEN GÖRÜNMÜYOR: ÜRETİMDEKİ tek çağıran `_gate_eval`in LEGACY dalıdır
    (dilim yok → `law="legacy_margin"`) ve orası `majority`/`tail_ok` yerine sabit `True` geçer,
    yani zincir pratikte yalnız büyüklük gerekçesini üretir. Aynı legacy dünyada `_trades_search`/
    `_mtm_search` dilimleri de yoktur; iki düşüş bacağı ölçülemez (`dd_durum`/`dd_mtm_durum` =
    "olculemedi") ve tanım gereği ret sebebi olamaz. Dilimli (olasılıksal) yolda gerekçeyi zaten
    `_gate_eval`in kendi zinciri yazar — düşüş vetoları oradan, adıyla çıkar.

    "ÜRETİMDEKİ" NİTELEMESİ 2026-08-16'DA EKLENDİ: eski cümle "tek çağıranı `_gate_eval`" diyordu
    ve bu YANLIŞTI — `tests/test_audit_fixes.py::test_gate_why_handles_none_incumbent_oos` İKİNCİ
    çağırandır, üstelik `margin` GEÇMEZ (yani çıplak `GATE_MARGIN` yolunu sınayan tek yer odur).
    "Tek çağıran" iddiası, bir parametrenin gerçekte hangi değerlerle geldiğini gizler; kapsamı
    daraltan her beyan gibi ölçülerek yazılmalıdır."""
    inc_oos, cand_oos = inc["oos_score"], cand["oos_score"]
    inc_tail, cand_tail = inc.get("oos_tail_risk"), cand.get("oos_tail_risk")
    if cand_oos is None:
        return "candidate OOS score undefined (below min_sample)"
    if inc_oos is None:                          # L2: _gate_eval's `passes` guards this, but _gate_why did
        return "incumbent OOS score undefined (below min_sample)"   # not — `None + margin` → TypeError
    if not (cand_oos > inc_oos + margin):
        return f"candidate OOS {cand_oos} did not beat incumbent {inc_oos} + {margin}"
    if not majority:
        if fold_total == 1:
            return ("fold-robustness UNPROVABLE: only 1 window had enough trades — a single-window "
                    "edge is not robustness (2026-07-22)")
        return f"candidate lost the fold-robustness majority ({fold_wins}/{fold_total})"
    # `tail_ok` ARTIK OKUNUYOR (2026-08-16). Bu parametre imzada VARDI ama gövdede HİÇ geçmiyordu:
    # son dal, kuyruk geçmiş olsa bile koşulsuz "kuyruk düşürdü" gerekçesi yazıyordu. Beyan edilip
    # okunmayan bir parametre, okuyucuya kapının o bacağa BAKTIĞINI söyleyen sessiz bir yalandır —
    # ve buraya `tail_ok=True` ile düşmek, gerekçenin bu zincirde OLMADIĞI anlamına gelir (hüküm
    # `_gate_eval`in beş terimli bağlacından, örneğin bir düşüş vetosundan gelmiştir). O durumda
    # kuyruğu suçlamak sebep UYDURMAKTIR; zincir kendi kapsamının dışını gösterir.
    if tail_ok:
        return ("gate rejected but NOT by this chain (magnitude/majority/tail all held here) — "
                "the binding reason is in _gate_eval's own chain (drawdown or M2M drawdown veto)")
    # SON DAL SAVUNMALI: buraya düşmek "kuyruk düşürdü" demektir, ama kuyruk ÖLÇÜLMEMİŞ olabilir
    # (legacy/fikstür sözlüklerinde `oos_tail_risk` yoktur). Ölçülmemiş kuyruğu sayı gibi okumak
    # önce TypeError'dı; sayı UYDURMAK ise daha kötüsü olurdu. UYDURMA YASAĞI: ölçülemediğini söyle.
    if not (isinstance(inc_tail, dict) and isinstance(cand_tail, dict)):
        eksik = [ad for ad, v in (("incumbent", inc_tail), ("candidate", cand_tail))
                 if not isinstance(v, dict)]
        return ("gate rejected but the reason is UNMEASURED: no oos_tail_risk record on "
                f"{' and '.join(eksik)} — no cause is invented here")
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

    # ---- N-DENGELİ FOLD KESİMİ -----------------------------------------------------------------
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
    # FOLD ÇOĞUNLUĞU KANIT İSTER. Eskiden `fold_total < 2` iken
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
    # ---- BOŞ BIRAKILAN PENCERE = SAĞLAMLIK İDDİASI YOK (n-dengeli kesimin GEREKTİRDİĞİ
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
        # AND → OR. "İkisi BİRDEN kötüleşsin" demek, sermaye korumasında
        # fazla hoşgörülü: VaR'ı AYNI kalıp CVaR'ı 3.5R → 9.0R'ye çıkan bir aday geçiyordu — marjın
        # 11 KATI ve kalın-kuyruğun ders kitabı tanımı. Kuyruk riski tek metrikte bile anlamlı
        # kötüleşiyorsa bu bir vetodur; iki metrik iki AYRI soru sorar (tipik en kötü / en kötülerin
        # ortalaması), biri diğerini affedemez.
        tail_ok = not (worse_var or worse_cvar)

    # ---- DÜŞÜŞ VETOSU (PARA-v3) ----------------------------------------------------------------
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
    # BEYAN EDİLMİŞ SINIR: VETONUN TETİKLEYİCİSİ Search diliminin
    # KAPANMIŞ-İŞLEM sermaye eğrisidir. `score_detail` düşüşü hesaplarken günlük mark-to-market
    # eğrisini de katlıyor ("açık pozisyon düşüşü saklanamasın") ama o sayı `oos_detail`in içinde
    # birleşmiş hâlde duruyor. Artık `walk_forward` M2M eğrisini DİLİM BAŞINA
    # döndürüyor (`_mtm_search`) ve aşağıdaki ikinci bacak onu AYRI ölçüyor — ama ÖLÇER, HÜKÜM
    # VERMEZ (bkz. `DD_MTM_VETO_ENV` yorumu: marj kapanmış-işlem dağılımından türetildi, M2M
    # dağılımının σ'sı ölçülmedi). Yani bu satırın hükmü DEĞİŞMEDİ; yanına ölçülen bir ikiz kondu.
    inc_dd = cand_dd = None
    dd_ok, dd_durum = True, "olculemedi"
    if _its and _cts:
        from . import score as _sc
        inc_dd = _sc.max_drawdown(_sc.equity_curve(_its))
        cand_dd = _sc.max_drawdown(_sc.equity_curve(_cts))
        dd_ok = not (cand_dd > inc_dd + DD_VETO_MARGIN)
        dd_durum = "gecti" if dd_ok else "veto"

    # ---- AÇIK-POZİSYON (M2M) DÜŞÜŞ BACAĞI — ÖLÇÜLÜR, VARSAYILAN BAĞLANMAZ ----------------------
    # AYNI YAPI, AYNI PENCERE, BAŞKA EĞRİ: `_mtm_search` ile `_trades_search` aynı sınırlardan
    # kesilir (backtest.walk_forward), yani iki bacak aynı sınavı iki farklı mercekle okur. Düşüş
    # formülü de AYNIDIR — yukarıdaki bacağın kullandığı `score.max_drawdown`. Kapı, `walk_forward`ın
    # RAPOR bloğunu okumaz ve okuyamaz (o blok "hüküm vermez" beyanını taşır ve çivisi vardır);
    # buradaki sayı kapının kendi girdisinden, kendi formülüyle türer.
    # UYGULANAMAYAN KONTROL VETO SEBEBİ OLAMAZ: eğri yoksa (fikstür, legacy yol, replaysiz sözlük)
    # `dd_mtm_durum="olculemedi"` yazar ve hiçbir şeyi engellemez — "temiz kâğıt" DEĞİL, "bakılmadı".
    inc_dd_mtm = cand_dd_mtm = None
    dd_mtm_ihlal, dd_mtm_durum = False, "olculemedi"
    _imtm, _cmtm = inc.get("_mtm_search"), cand.get("_mtm_search")
    _mtm_bagli = _dd_mtm_bagli()
    if _imtm and _cmtm:
        from . import score as _sc2
        _ic = [float(e) for _d, e in _imtm]
        _cc = [float(e) for _d, e in _cmtm]
        if _ic and _cc:
            inc_dd_mtm = _sc2.max_drawdown(_ic)
            cand_dd_mtm = _sc2.max_drawdown(_cc)
            dd_mtm_ihlal = bool(cand_dd_mtm > inc_dd_mtm + DD_VETO_MARGIN)
            dd_mtm_durum = ("gecti" if not dd_mtm_ihlal else
                            ("veto" if _mtm_bagli else "ihlal_baglanmadi"))
    # HÜKME GİDEN TEK KAPI: bayrak kapalıyken bu değer HER ZAMAN True'dur, yani `passes` bu turda
    # bit-bit eski davranıştadır (test çivisiyle sabit).
    dd_mtm_ok = not (dd_mtm_ihlal and _mtm_bagli)

    # ---- OOS AŞINMA DEFTERİ --------------------------------------------------------------------
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
    # ---- "ÖLÇÜLEMEDİ" ÜÇÜNCÜ HÂLDİR — "GEÇTİ" DEĞİL --------------------------------------------
    # `evaluate_search` İKİ SEBEPLE `law="legacy"` döner ve ikisi AYNI ŞEY DEĞİLDİR:
    #   (a) DİLİM YOK      → olasılıksal yasa bu ortamda hiç YÜRÜRLÜKTE DEĞİL (fikstür/sandbox);
    #                        eski marj yasası o dünyanın MEŞRU yasasıdır ve aynen koşar.
    #   (b) DİLİM VAR ama ölçüm YAPILAMADI (dilim sınırı çözülemedi · dilim boş · geçerli
    #                        replikasyon < max(200, n_boot/10)) → yasa YÜRÜRLÜKTE ama ÖLÇEMEDİ.
    # (b) bugüne kadar (a) ile aynı dala düşüyordu ve sonuç şuydu: yürürlükteki yasa ölçemeyince
    # kapı sessizce BAŞKA ve DAHA GEVŞEK bir yasaya (bileşik nokta-marj) geçip adayı GEÇİRİYORDU.
    # ÖLÇÜLDÜ: dilimleri olan, arama sınırı çözülemeyen bir çiftte `passes=True, gate_law=legacy_
    # margin, search_p=None, why=''` — yani hiçbir olasılıksal kanıt olmadan "geçti".
    # Bu bir EŞİK DEĞİŞİKLİĞİ DEĞİL, TANIM DÜZELTMESİdir: ölçülemeyen bir aday ölçülmüş sayılamaz.
    # Fail-closed, ve nedeni kayda ADIYLA girer.
    _dilimli = bool(OutOfSamplePipeline.has_slices(inc) and OutOfSamplePipeline.has_slices(cand))
    if prob.law == "probabilistic":
        # dilim tabanı: bootstrap içi min_sample bypass'ı dilimin KENDİSİNİ inceltmesin — iki tarafta
        # da en az min_sample·0.7 işlem yoksa olasılıksal karar dürüst değildir → magnitude geçmez.
        floor = max(10, int(config.goal().get("min_sample", 30) * 0.7))
        thin = min(len(inc.get("_trades_search", [])), len(cand.get("_trades_search", []))) < floor
        # `goal.min_sample` DEĞİŞMEZ bir sözleşmedir: olasılıksal yasa
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
    elif _dilimli:
        # ÖLÇÜLEMEDİ: yasa yürürlükte, ölçüm yok → GEÇEMEZ. Eski marj yasasına DÜŞMEZ, çünkü
        # düşmek "ölçemedim" ile "başka bir yasaya göre geçti"yi aynı şey saymak olurdu.
        inc_para = cand_para = None
        erosion_margin_para = None
        magnitude_ok = False
        mag_why = (f"ÖLÇÜLEMEDİ: dilimler VAR (olasılıksal yasa yürürlükte) ama arama dilimi "
                   f"ölçülemedi — {prob.why or 'sebep beyan edilmedi'}. Ölçülemeyen aday geçmiş "
                   f"sayılamaz (fail-closed); eski bileşik marj yasasına DÜŞÜLMEZ, o başka bir "
                   f"yasadır ve burada yürürlükte değildir")
        law = "olculemedi"
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
        # ETKİN MARJ GEÇİRİLİR: hüküm `effective_margin` ile verildi, gerekçe de onunla yazılmalı.
        # Çıplak `GATE_MARGIN` ile sınayan eski çağrı, aşınma marjı devredeyken büyüklük dalını
        # atlayıp akışı kuyruk dalına düşürüyordu (bkz. `_gate_why` MARJ DIŞARIDAN GELİR notu).
        mag_why = "" if magnitude_ok else _gate_why(inc, cand, True, fold_wins, fold_total, True,
                                                    margin=effective_margin)
        law = "legacy_margin"

    # `dd_mtm_ok` bayrak kapalıyken TANIM GEREĞİ True — bu terim varsayılan yolda NO-OP'tur ve
    # yalnız ölçüm kartının koşumunda (MERIDIAN_DD_MTM_VETO=1) hüküm üretebilir.
    passes = bool(magnitude_ok and majority and tail_ok and dd_ok and dd_mtm_ok)

    # DAMGA TEK YERDE TÜRETİLİR (kapı kaydı + doğrulama defteri AYNI dizgeyi yazsın). ÜÇ DEĞER:
    # ölçülemeyen bir satıra "eski_bilesik_marj" basmak BİRİM YALANI olurdu — o satırda hiçbir
    # ölçek yok, çünkü hiçbir ölçüm yok (`probgate.BILESIK_DAMGALAR` bilinmeyen damgayı zaten
    # SAYMAZ ve sayaçta adıyla gösterir; ship etmediği için çift de üretmez).
    _yasa_damga = (shadowlaw.YASA_SURUMU if law == "probabilistic"
                   else ("olculemedi" if law == "olculemedi" else "eski_bilesik_marj"))

    # ---- Y1 DOĞRULAMA: DSR (ADVISORY) + ADAY GETİRİ DEFTERİ ------------------------------------
    # DSR, kapının SORMADIĞI soruyu sorar: "kaç aday denedik de bu geçti?" Aşınma defteri o yükü
    # SAYIYOR ve marja çeviriyor; DSR onu Sharpe'ın kendi ölçeğinde bir OLASILIĞA çevirir
    # (Bailey & López de Prado 2014, çarpıklık/basıklık düzeltmeli).
    #
    # ADVISORY — `passes` YUKARIDA HESAPLANDI VE BU BLOK ONA DOKUNMAZ. Bu, bilinçli bir sıralamadır:
    # DSR alanı `passes` satırının ALTINDA üretilir, yani hükmü değiştirmesi kod düzeninde de
    # imkânsızdır. Hard-gate'e geçiş (DSR>0.95) AYRI bir operatör kararıdır ve
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
            # ---- PENCERE DAMGASI (HOLDOUT ROTASYONU R1) ----
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
            # ROL METNİ GÜNCELLENDİ ama "ADVISORY" KELİMESİ YERİNDE KALDI ve bu doğrudur:
            # DSR `_gate_eval`in `passes` hükmüne HÂLÂ girmez (blok `passes` satırının ALTINDA).
            # Sertlik SHIP yolunda (`_submit_locked`) ve MOD-FARKINDALIKLIDIR — iki ayrı yerdeki
            # iki ayrı hüküm tek cümlede karışmasın.
            "dsr_rol": ("ADVISORY (KAPI) — passes hükmüne girmez; SHIP yolunda mod-farkındalıklı: "
                        "paper=damga · gerçek-para=SERT fail-closed (v130)"),
            # `margin` ARTIK YÜRÜRLÜKTEKİ marjdır (taban + aşınma). Tabanı ayrı yazmak şart: kapı
            # kaydını sonradan okuyan biri 0.03 görüp "GATE_MARGIN değişmiş" sanmasın.
            "gate_margin_base": GATE_MARGIN, "erosion": erosion,
            # ---- PARA-v3 DAMGASI ----
            # Bir kapı kaydını altı ay sonra okuyan biri, o `search_p`nin HANGİ yasanın p'si
            # olduğunu tahmin etmek zorunda kalmamalı. Damga + geçiş tarihi kayda GİRER; geçiş
            # ÖNCESİ kayıtlarda alan YOKTUR ve yokluğu "eski bileşik yasa" demektir (retro damga
            # yasağı — eski kayıtlar geriye dönük damgalanmaz).
            "yasa_surumu": _yasa_damga,
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
            # AÇIK-POZİSYON (M2M) DÜŞÜŞ BACAĞI — ÖLÇÜM, HÜKÜM DEĞİL. Kayda girmesinin sebebi tam
            # olarak eşiğin ölçülebilmesi: `ihlal_baglanmadi` yazan her satır, marj M2M dağılımına
            # göre türetilseydi bu adayın RET edileceği anlamına gelir. Kartın ham maddesi budur.
            "dd_mtm_ok": bool(dd_mtm_ok), "dd_mtm_durum": dd_mtm_durum,
            "dd_mtm_bagli": bool(_mtm_bagli),
            "incumbent_dd_mtm": None if inc_dd_mtm is None else round(float(inc_dd_mtm), 4),
            "candidate_dd_mtm": None if cand_dd_mtm is None else round(float(cand_dd_mtm), 4),
            "dd_mtm_beyan": ("açık-pozisyon düşüşü ÖLÇÜLDÜ, hükme BAĞLANMADI — marj "
                             "(DD_VETO_MARGIN) kapanmış-işlem düşüş dağılımından türetildi, M2M "
                             "dağılımının σ'sı ölçülmedi; bağlanması ölçüm kartı ister"),
            "gate_law": law, "k_probes": k_probes, **prob.as_gate_fields("search"),
            # ÜÇ DEĞERLİ BÜYÜKLÜK HÜKMÜ: "gecti" · "gecmedi" · "olculemedi". `magnitude_ok`
            # tek başına iki-değerlidir ve ÖLÇÜLEMEYENİ GEÇMEYENDEN ayıramaz; bir okuyucu (ya da
            # bekçi) "kapı neyi eliyor?" sorusunu ancak bu alanla dürüstçe cevaplayabilir.
            "magnitude_durum": ("gecti" if magnitude_ok else
                                "olculemedi" if law == "olculemedi" else "gecmedi"),
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
    elif not dd_mtm_ok:
        # BU DALA VARSAYILAN YOLDA GİRİLMEZ (bayrak kapalı → dd_mtm_ok hep True). Var olma sebebi:
        # bayrak açıkken ret gerekçesi "kuyruk riski" diye okunamamalı — aşağıdaki `else` kuyruk
        # sözlüklerini okur ve M2M reddinde onlar None bile olabilir.
        why = (f"aday AÇIK-POZİSYON (M2M) maks düşüşü incumbent'ı {DD_VETO_MARGIN} marjından fazla "
               f"kötüleştiriyor (M2M düşüş {cand_dd_mtm:.4f} vs {inc_dd_mtm:.4f}) — M2M düşüş "
               f"vetosu ({DD_MTM_VETO_ENV}=1 ile BAĞLI koşuluyor)")
    else:
        why = (f"candidate worsens OOS tail risk beyond {TAIL_MARGIN_R}R "
               f"(VaR {cand_tail['var_r']} vs {inc_tail['var_r']}, "
               f"CVaR {cand_tail['cvar_r']} vs {inc_tail['cvar_r']})")

    # ---- ADAY GETİRİ SERİSİ KALICI DEFTERE (PBO'nun ham maddesi) -------------------------------
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
    # HİÇBİR kayıtta yoktu (geçmiş ölçümler yalnız `oos_score` yazdı, bu yüzden o vakaların
    # terim ayrıştırması artık yeniden koşmadan çıkarılamıyor). Bundan sonra her resmî
    # değerlendirmede duruyor.
    if record_erosion:
        _inc_p, _cand_p = inc.get("params") or {}, cand.get("params") or {}
        _degisen = {k: v for k, v in _cand_p.items() if _inc_p.get(k) != v}
        _od = cand.get("oos_detail") or {}
        # ---- DSR DAMGASI (TSK-077, KYS-2026-002 R2, 2026-09-03) --------------------------------
        # R1 tabanının DSR yarısı kill#2 ile durmuştu: donmuş kopya kapının `_ret` girdisini
        # TAŞIMIYORDU, `seri` (kapanış-günü, r_multiple) ölçek-eşdeğer DEĞİL (motorun kendi
        # _moments'ıyla ÖLÇÜLDÜ ve REDDEDİLDİ — karta bkz.). Tek yol İLERİYE DÖNÜK DAMGA: `_ret`
        # (satır ~681, koşulsuz kurulan, `deflated_sharpe`a verilen AYNI liste) buradan itibaren
        # deftere de yazılır — YENİDEN HESAP YOK, aynı nesne kullanılır.
        # UYDURMA YASAĞI: `_trades_search` anahtarı YOKSA (None) `_ret` `_cts_all = ... or []`
        # (satır 680) yüzünden zaten [] — ama "yok" ile "ölçüldü, boş çıktı" AYNI ŞEY DEĞİLDİR;
        # ayrım burada RAW anahtara bakılarak (satır 680'in `or []` düşmesinden ÖNCEki hâl) yeniden
        # kurulur. Anahtar YOKSA ret_seri/ret_n None + beyana neden eklenir; anahtar VARSA ve boşsa
        # []/0 de bir ölçümdür. RETRO-DAMGA YASAK: eski satırlara dokunulmaz (ledgers.py sözleşme
        # notu; `required` DEĞİŞMEDİ).
        _cts_raw = cand.get("_trades_search")
        _ret_seri = None if _cts_raw is None else _ret
        _ret_n = None if _cts_raw is None else len(_ret)
        _beyan = "ADVISORY defter — kapı passes semantiğine girmez (Hafta 3a)"
        if _cts_raw is None:
            _beyan += " · ret_seri: _trades_search yok (TSK-077)"
        validation.record_candidate({
            "ts": memory.now_iso(), "fingerprint": _fp,
            # PENCERE DAMGASI (R1): PBO/DSR bu defteri TEK POPÜLASYON sanarak okur.
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
            "yasa_surumu": _yasa_damga,
            "oos_para": cand_para, "incumbent_para": inc_para,
            "dd_ok": bool(dd_ok), "candidate_dd": None if cand_dd is None else round(float(cand_dd), 4),
            "incumbent_dd": None if inc_dd is None else round(float(inc_dd), 4),
            # M2M ikizi ADVISORY defterde de durur: PBO/DSR analizleri "eşik M2M'ye taşınsaydı bu
            # popülasyon nasıl değişirdi?" sorusunu ancak satır satır kayıtla cevaplayabilir.
            "dd_mtm_durum": dd_mtm_durum, "dd_mtm_bagli": bool(_mtm_bagli),
            "candidate_dd_mtm": None if cand_dd_mtm is None else round(float(cand_dd_mtm), 4),
            "incumbent_dd_mtm": None if inc_dd_mtm is None else round(float(inc_dd_mtm), 4),
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
            # RET_SERİ/RET_N (TSK-077): `_ret`in KENDİSİ, yuvarlamasız — PBO'nun ham maddesi `seri`
            # gibi bir yeniden-türetme DEĞİL, kapının DSR'a verdiği serinin BİREBİR kopyası.
            "ret_seri": _ret_seri, "ret_n": _ret_n,
            "beyan": _beyan})
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
    # çıkış-verimliliği dürtmesi — MFE muhasebesi "masada R kalıyor" diyorsa (rapor eşiği),
    # exit.* düğmeleri sıralamada KÜÇÜK bir bonus alır. Yalnız arama SIRASI etkilenir; kapı yasası,
    # ödüller ve karar mekanizması değişmez. Dosya yoksa bonus 0 → davranış birebir eski hal.
    try:
        _ee = store.read_json("exit_efficiency.json", {})
        exit_bonus = 0.05 if _ee.get("nudge_active") else 0.0
    except Exception as e:
        # YASA 4: dosya bozuksa dürtü sessizce KAPANIR ve arama sırası "masada R kalıyor"
        # bulgusunu hiç duymadan koşar. Davranış aynı kalır (bonus 0) ama artık nedeni görünür.
        _cache_warn("exit_efficiency_unreadable", e)
        exit_bonus = 0.0

    def ucb(v):
        """Tek değişkenin UCB1 skoru: hiç denenmemişse +inf (iyimserlik → önce keşif), denenmişse
        ortalama ödül + c·sqrt(ln(toplam)/deneme) + (varsa) exit.* dürtü bonusu."""
        s = stats.get(v)
        bonus = exit_bonus if str(v).startswith("exit.") else 0.0
        if not s or s["trials"] == 0:
            return float("inf")
        return s["reward"] / s["trials"] + c * math.sqrt(math.log(total) / s["trials"]) + bonus

    return sorted(candidates, key=lambda v: (-ucb(v), v))


# ==================================== Ö-48 HAYALET SÜZGECİ ======================================
# VAKA (ROADMAP §48, 2026-08-14): keşif bütçesinin %62'si (29/47 öneri) canlı params'ta taşınmayan
# düğmelere gitti. O iki düğme motorda KABLOLUYDU (okuyucuları var) — ama aynı vaka daha sert bir
# sınıfı görünür kıldı: iki düğme bounds.yaml'a kablolanmadan GÜNLER ÖNCE girmişti. bounds'a motor
# okuyucusu OLMAYAN bir anahtar girerse arama bütçesi yapısal-ölü sondalara akar ve hiçbir kapı
# bunu söylemez. Bu süzgeç o sınıfın kalıcı bekçisidir.
#
# TANIM — HAYALET: motor zinciri modüllerinin hiçbirinde string sabiti olarak GEÇMEYEN bounds
# anahtarı. Motor, params anahtarlarını dotted-string literaliyle okur (`_f(params, "entry.w_rs",
# 0.35)` — strategy.py deseni); dolayısıyla "kaynak AST'sinde sabit yok" = "okuyucu yok".
# Yorum ve docstring OKUYUCU SAYILMAZ (AST docstring'leri dışlar; yorumlar AST'ye hiç girmez).
# ÖLÇÜM 2026-08-22: bugünkü 32 bounds anahtarının 32'sinde de okuyucu VAR — bugünkü hayalet
# listesi BOŞ (test_hayalet_dugme_v263 N2 bunu çiviler; süzgeç bugün davranış DEĞİŞTİRMEZ,
# yarının regresyonunu keser).
#
# KAPSAM: arama uzayı = bounds anahtarları (goal.yaml yasadır, öneriye hiç girmez — iki
# enumerasyon noktası da yalnız bounds.keys() üzerinde yürür). Süzgeç DOSYAYA DEĞİL bellekteki
# sözlüğe uygulanır: bounds.yaml İZLİ state'tir ve operatör/dagit kanalıdır, buradan yazılmaz.
MOTOR_ZINCIRI = ("strategy", "backtest", "broker", "guard", "regime", "loop",
                 "faz5_cikis", "sieve", "indicators", "intraday_cycle")

_HAYALET_SAYAC = 0            # süreç-içi kümülatif süzülen-anahtar sayacı (olay alanı `sayac_toplam`)
_MOTOR_SABIT_CACHE: dict = {}  # {(dosya, mtime_ns) demeti: frozenset} — kaynak değişmedikçe tek tarama


def _motor_sabitleri_olc() -> tuple:
    """(sabitler, hata) döner: motor zinciri kaynaklarındaki TÜM string sabitlerinin kümesi
    (docstring hariç) ya da (None, neden). None = ÖLÇÜLEMEDİ — hayalet hükmü VERİLEMEZ; çağıran
    fail-open davranır. Önbellek (dosya, mtime) anahtarlıdır: kaynak değişirse yeniden ölçülür,
    hata ASLA önbelleklenmez (geçici bir G/Ç arızası kalıcı körlüğe dönmesin)."""
    import ast as _ast
    import pathlib as _pl
    kok = _pl.Path(__file__).resolve().parent
    try:
        kimlik = tuple((str(kok / f"{m}.py"), (kok / f"{m}.py").stat().st_mtime_ns)
                       for m in MOTOR_ZINCIRI)
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"
    if kimlik in _MOTOR_SABIT_CACHE:
        return _MOTOR_SABIT_CACHE[kimlik], None
    sabitler: set = set()
    try:
        for yol, _mt in kimlik:
            agac = _ast.parse(_pl.Path(yol).read_text())
            docstringler = set()
            for dugum in _ast.walk(agac):
                if isinstance(dugum, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef,
                                      _ast.ClassDef)):
                    d = _ast.get_docstring(dugum, clean=False)
                    if d:
                        docstringler.add(d)
            for dugum in _ast.walk(agac):
                if isinstance(dugum, _ast.Constant) and isinstance(dugum.value, str) \
                        and dugum.value not in docstringler:
                    sabitler.add(dugum.value)
    except (OSError, SyntaxError, ValueError) as e:
        return None, f"{type(e).__name__}: {e}"
    donuk = frozenset(sabitler)
    _MOTOR_SABIT_CACHE[kimlik] = donuk
    return donuk, None


def motor_okunan_sabitler() -> frozenset | None:
    """Motor zincirinin okuduğu string sabitleri; None = ölçülemedi (neden `hayalet_suzgeci`
    olayında). Rapor/teşhis yüzeyi — süzgecin kendisi `hayalet_suzgeci` üzerinden çalışır."""
    sabitler, _neden = _motor_sabitleri_olc()
    return sabitler


def hayalet_suzgeci(bounds: dict, kaynak: str) -> tuple:
    """Arama uzayı kurulumunun HAYALET kapısı: (temiz_anahtarlar, hayalet) döner.

    * hayalet = [..]  → bu anahtarların motor okuyucusu YOK; arama uzayından çıkarıldılar ve
      süzüm `reflect_hayalet_dugme_suzuldu` olayıyla (adlar + kümülatif sayaç) görünür kılındı.
    * hayalet = []    → ölçüldü, temiz: hiçbir anahtar süzülmedi.
    * hayalet = None  → okuyucu kümesi ÖLÇÜLEMEDİ (null=ölçülemedi≠0): süzgeç FAIL-OPEN —
      hiçbir anahtar süzülmez ve `reflect_hayalet_olculemedi` uyarısı basılır. Kör bir
      tarayıcının aramayı SESSİZCE daraltma yetkisi yoktur; yanlış-pozitif hayalet damgası
      (gerçek düğmeyi aramadan düşürmek) kaçırılmış hayaletten pahalıdır.

    bounds SÖZLÜĞÜNE ve bounds.yaml DOSYASINA DOKUNULMAZ — süzgeç yalnız dönen listeyi daraltır."""
    global _HAYALET_SAYAC
    anahtarlar = list(bounds.keys())
    sabitler, neden = _motor_sabitleri_olc()
    if sabitler is None:
        try:
            from . import obs as _obs_h
            _obs_h.warn("reflect_hayalet_olculemedi", kaynak=kaynak, error=neden,
                        n_bounds=len(anahtarlar),
                        detail="motor okuyucu kümesi ÖLÇÜLEMEDİ (kaynak okunamadı/parse edilemedi)"
                               " — süzgeç FAIL-OPEN: hiçbir anahtar süzülmedi, hayalet=None "
                               "(ölçülemedi, sıfır DEĞİL). Arama tam uzayda sürüyor.")
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; telemetri denemesi aramayı düşüremez ve fail-open dönüş zaten çağırana gidiyor
            pass
        return anahtarlar, None
    hayalet = [k for k in anahtarlar if k not in sabitler]
    if not hayalet:
        return anahtarlar, []
    temiz = [k for k in anahtarlar if k in sabitler]
    _HAYALET_SAYAC += len(hayalet)
    try:
        from . import obs as _obs_h
        _obs_h.warn("reflect_hayalet_dugme_suzuldu", kaynak=kaynak, hayalet=hayalet,
                    n_hayalet=len(hayalet), n_bounds=len(anahtarlar),
                    sayac_toplam=_HAYALET_SAYAC,
                    detail="bounds'ta duran ama MOTOR ZİNCİRİNDE okuyucusu olmayan anahtar(lar) "
                           "arama uzayına ALINMADI — keşif bütçesi yapısal-ölü sondaya akmasın "
                           "(Ö-48; %62 vakasının sert sınıfı). bounds.yaml'a dokunulmadı; kalıcı "
                           "çözüm operatör kanalında (anahtarı kablola ya da bounds'tan düşür).")
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; süzüm izi coordinate_descent_search dönüşündeki `hayalet_suzulen` alanında AYRICA taşınıyor
        pass
    return temiz, hayalet


def propose_deterministic(explore: bool = False) -> dict:
    """Form ONE single-variable hypothesis. No LLM, one_variable_only preserved.

    EMEKLİ EDİLMEDİ — OPERATÖR KALEMİ (av adayıydı, çürütüldü).
    AV İDDİASI: "üretim yolu kalmadı — `skills.axis2_cycle` bugün `recommend_from_attribution`ı
    DOĞRUDAN çağırıyor". Doğrulandı: Eksen-2 kolu artık buradan geçmiyor. AMA çürütme şu:
    bu fonksiyonun kalan tek yolu `reflect --auto` CLI'ıdır (aşağıda `main`) ve o CLI ÖLÜ DEĞİL —
    `README.md` satır 81'de operatörün elle koşturduğu komutlar listesinde yazılı duruyor
    ("force a reflection cycle (deterministic proposer — no LLM)"). Beyinsiz/kotasız bir gecede
    TEK hamle üretmenin elle tetiği budur; hermes'in canlı yolu onu çağırmaz (bkz. hermes.py
    ~2550'deki not). Belgesi: OPERATÖR tablosu. Yeni bir üretim çağıranı EKLENMEZ —
    eklenirse aynı gecede iki yansıma yarışır (`_submit_locked`in engellediği hâl).

    Two selection modes over the SAME single-variable move:
      * exploit (default): a behavior heuristic reads recent exit reasons / win rate and nudges the
        one variable most implicated (stop-outs → wider stop, time-stops → shorter clock, …).
      * explore (--explore): a UCB1 bandit ranks ALL tunable variables by their historical ship-rate
        in the ledger, preferring under-tried ones, so the loop widens its search instead of hammering
        the same few knobs. Either way the result is a single validated-shape proposal for the gate.

    HAFIZA HER İKİ KİPTE DE OKUNUR: defterde `rejected_by_backtest` ya da
    `rolled_back` ile duran bir (değişken, değer) çifti yeniden ÖNERİLMEZ. Exploit kipinde bu,
    sezgiselin yönünde bir sonraki denenmemiş ADIMA geçmek demektir (yön ve değişken değişmez).
    Tüm adımlar elenirse öneri yine döner ama `memory_exhausted=True` taşır ve
    `propose_deterministic_memory_exhausted` uyarısı basılır — kısırlık sessiz kalamaz."""
    strat = config.load_strategy()
    params = strat.get("params", {})
    bounds = config.bounds()
    hyps = memory.all_hypotheses()
    trades = store.read_jsonl("trades.jsonl", limit=40)
    reasons = Counter(t.get("exit_reason", "") for t in trades)
    n = max(1, len(trades))
    win_rate = sum(1 for t in trades if t.get("r_multiple", 0) > 0) / n if trades else 0.0

    def move(var, direction, k: int = 1):
        """Sezgiselin YÖNÜNDE k adım. `k` ADIM SAYISIDIR — ikinci bir değişken ya da ikinci bir yön
        DEĞİL: tek-değişken sözleşmesi ve `hdir` sezgiseli aynen korunur (k=1 eski davranış)."""
        b = bounds[var]
        lo, hi, step, typ = b["min"], b["max"], b["step"], b["type"]
        cur = params.get(var, lo)
        new = max(lo, min(hi, cur + direction * k * step))
        return int(new) if typ == "int" else round(new, 4)

    def explore_dir(var):
        """Keşif yönü: mevcut değer aralığın ortasının altındaysa +1, üstündeyse −1 — adım hep
        aralığın HENÜZ DENENMEMİŞ yarısına doğru atılır."""
        b = bounds[var]
        mid = (b["min"] + b["max"]) / 2.0
        return +1 if params.get(var, mid) <= mid else -1   # step toward the untested half of the range

    # HAFIZA TEK TANIMDAN OKUNUR. Burada eskiden aynı işi yapan İKİNCİ bir
    # `already_failed` kapanışı vardı; modül düzeyindeki `_already_failed` (koordinat-inişi aramasının
    # da kullandığı tanım) ile tek farkı @regime son-ekini çözememesiydi — `bounds[var]["type"]`
    # son-ekli adla aranıyor ve defterde o adla bir satır VARSA KeyError fırlatıyordu (yani hafızanın
    # tam da iş göreceği anda). "Başarısız" tanımı DEĞİŞMEDİ: guard'ın kalıcı kara listesiyle birebir
    # aynı küme — `status in ("rejected_by_backtest", "rolled_back")` (`guard.validate_change`).

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
        # Ö-48: uzay HAYALET SÜZGECİNDEN geçer — motor-okuyucusuz anahtar UCB sırasına hiç girmez
        # (süzüm olayla görünür; ölçülemezse fail-open, tam uzay). Exploit sezgiselinin 4 sabit
        # düğmesi süzgeçten BİLEREK geçmez: dördü de okuyucusu ölçülmüş kod sabitidir ve sezgisel
        # bir enumerasyon değil teşhistir — hayaletleşmeleri ancak motordan okuyucu SİLİNMESİYLE
        # mümkün olur, o da bu süzgecin değil o değişikliğin turunun işidir.
        arama_uzayi, _hayalet_e = hayalet_suzgeci(bounds, kaynak="propose_deterministic.explore")
        for var in _ucb_rank(arama_uzayi, hyps):
            direction = hdir if var == hvar else explore_dir(var)
            new = move(var, direction)
            if guard._equalish(params.get(var), new, bounds[var]["type"]) \
                    or _already_failed(var + suffix, new, hyps, bounds):
                continue
            label = f"bandit(UCB) explore: {var}{suffix}" + (f" ({live_regime} rejimine özel)" if suffix else "")
            return _proposal(var + suffix, new, params, label, explore=True)
        var = hvar
    else:
        var = hvar

    # =============================================================================================
    # EXPLOIT YOLUNA HAFIZA — 21 TEKRARIN KÖKÜ
    # ---------------------------------------------------------------------------------------------
    # ÖLÇÜLEN BEDEL (docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md): `already_failed` kontrolü
    # YALNIZ explore dalının içindeydi; varsayılan exploit yolunda hafıza YOKTU. Sezgisel "stop'lar
    # baskın → stop'a yer aç" dediği sürece `move()` HER TURDA aynı tek adımı üretiyordu:
    # `stop_loss_atr_mult=2.1` defterde 21 kez (1 backtest reti + 20 guard reti), oysa bounds o
    # düğmede 33 adım-üstü değer taşıyor ve 32'sine HİÇ bakılmamıştı. Döngüyü kıran şey üretici
    # değil guard'ın kara listesiydi — yani sistem öğrenerek değil, bir kapıyla kurtuluyordu.
    #
    # KONTROLÜN NEDEN YALNIZ EXPLORE'DA OLDUĞUNA DAİR GEREKÇE: KODDA/YORUMDA BULUNAMADI. Docstring
    # iki modu "aynı tek-değişken hamlesi üzerinde iki SEÇİM kipi" diye tanımlıyor ve hafızadan hiç
    # söz etmiyor; `_ucb_rank`in kendi yorumu da hafızayı değil sıralamayı anlatıyor. En yakın örtük
    # okuma "explore taranan bir LİSTE üzerinde yürür, atlamak doğal; exploit tek hamle üretir" —
    # ama bu bir gerekçe değil bir yapı farkıdır ve ölçüm onu çürütüyor.
    #
    # ÇÖZÜM ADIM SAYISINDADIR, YÖN DEĞİL: sezgiselin TEŞHİSİ (hangi değişken, hangi yön) korunur;
    # hafıza yalnız "kaçıncı adım" sorusunu açar. Ters yön BİLEREK denenmiyor — "stop'a yer aç"
    # diyen bir teşhisin ardından stop'u daraltmak teşhisin kendisini çürütmek olurdu; yön sorusu
    # ayrı bir ölçümün (ve explore/UCB kolunun) işidir.
    # KAPSAM NOTU: explore dalı aday BULAMAYIP buraya düştüğünde de bu merdiven koşar — çünkü bu
    # kuyruk yapısı gereği EXPLOIT hamlesidir (`var = hvar`, `hwhy`, `explore=False`). Explore'un
    # KENDİ dönüş yolu (yukarıdaki `_proposal(..., explore=True)`) bit-bit dokunulmadan durur.
    # =============================================================================================
    b = bounds[var]
    n_adim = int(round((b["max"] - b["min"]) / b["step"])) + 1 if b["step"] else 1
    adaylar, onceki = [], None
    for k in range(1, max(1, n_adim) + 1):
        val = move(var, hdir, k)
        if onceki is not None and guard._equalish(val, onceki, b["type"]):
            break                      # sınıra kenetlendi — sonraki adımlar aynı değeri üretir
        onceki = val
        adaylar.append((k, val))

    elenen = []
    for k, val in adaylar:
        if guard._equalish(params.get(var), val, b["type"]):
            elenen.append({"deger": val, "neden": "no-op"})
            continue
        if _already_failed(var, val, hyps, bounds):
            elenen.append({"deger": val, "neden": "zaten_denendi"})
            continue
        why = hwhy if k == 1 else (f"{hwhy} — hafıza: {k} adım (daha yakın {k - 1} değer zaten "
                                   f"denenip başarısız olmuştu)")
        return _proposal(var, val, params, why, explore=False)

    # TÜM ADAYLAR ELENDİ — SESSİZ KISIRLAŞMA YASAK. Dönüş DEĞERİ eski davranışın aynısıdır (tek
    # adım; guard onu zaten tekrar diye reddedecek) ama artık hem olay hem alan bunu SÖYLER: bu
    # değişkende sezgiselin yönünde denenmemiş değer KALMADI. Sessizce boş dönmek ya da None
    # döndürmek çağıranı (`reflect --auto` CLI'ı, `proposal['variable']` okur) kırardı.
    from . import obs as _obs_m
    _obs_m.warn("propose_deterministic_memory_exhausted", variable=var, direction=hdir,
                n_aday=len(adaylar), n_elenen=len(elenen), elenen=elenen[:12],
                rationale=hwhy,
                detail="exploit sezgiselinin YÖNÜNDEKİ tüm adım değerleri elendi (no-op ya da "
                       "defterde başarısız) — bu değişkende deterministik üretici yeni bir hamle "
                       "ÜRETEMİYOR. Öneri yine de tek-adım değeriyle dönüyor (eski davranış) ve "
                       "guard onu tekrar diye reddedecek; kısırlık artık görünür. Yol: --explore "
                       "(UCB kolu başka değişkene geçer) ya da sezgiselin yön/değişken revizyonu.")
    return _proposal(var, move(var, hdir), params,
                     f"{hwhy} — HAFIZA TÜKENDİ: bu yönde denenmemiş değer kalmadı",
                     explore=False, memory_exhausted=True)


def _proposal(var, new, params, why, explore=False, memory_exhausted: bool = False) -> dict:
    """Deterministik üreticinin tek-değişkenli öneri sözlüğünü kurar (kaynak: "deterministic").

    Güven değeri sabit DEĞİL: ≥5 sonuç varsa ajanın KENDİ gerçekleşmiş isabet oranından türetilir
    (0.30..0.70), yoksa soğuk başlangıç önselidir. `memory_exhausted` her öneride yazılır (False
    olsa bile) — eksik alan sıfır sanılamaz."""
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
        # HER ÖNERİDE YAZILIR (False olsa bile): bu depoda "eksik alan = sıfır/false sanılır" kendi
        # sınıfıdır (agent_tooluse `olculemeyen` dersi). True = üretici bu değişkende denenmemiş
        # değer bulamadı ve dönen hamle bilinen bir tekrardır.
        "memory_exhausted": bool(memory_exhausted),
    }


# ---------------- the pipeline every hypothesis flows through ----------------
class _ProcessLock:
    """CROSS-PROCESS reflection lock (fcntl.flock on state/.reflect.lock). The in-process
    _reflect_lock in hermes_runtime can't stop a SECOND process (tmux `hermes --loop`, a manual
    `reflect --auto`) from shipping concurrently — two multi-minute reflections racing versioning.commit
    would clobber strategy.yaml/version state. Non-blocking: the loser gets an honest
    'locked' result instead of silently corrupting."""
    def __enter__(self):
        """Kilit dosyasını açıp BLOKSUZ flock dener; alınamazsa `self.held=False` ile döner
        (bekleme yok — kaybeden çağıran dürüst 'locked' cevabı alır)."""
        import fcntl
        self.fh = open(config.STATE / ".reflect.lock", "w")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.held = True
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            self.held = False
        return self

    def __exit__(self, *a):
        """Kilidi (tutuluyorsa) bırakır ve dosyayı kapatır; temizlik hatası asıl iş yolunu düşürmez."""
        try:
            if self.held:
                import fcntl
                fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass


def submit(proposal: dict, goal: dict | None = None, windows: tuple | None = None) -> dict:
    """Ship yetkisinin TEK KAPISI: öğrenme-durdurma bayrağını ve süreçler-arası yansıma kilidini
    kontrol edip asıl boru hattını (`_submit_locked`) çağırır.

    LEARN_HALT aktifse hiç ilerlemez ("halt_learning"); kilit başkasındaysa bloklamadan
    "locked" döner — iki eşzamanlı yansıma strategy.yaml/sürüm durumunu ezemez."""
    from . import health as _health, obs as _obs
    if _health.learn_halted():                 # Faz 3: öğrenme durduruldu — işlemler sürer,
        _obs.log("submit_blocked_learn_halt")  # ama YENİ versiyon ship edilemez (operatör bayrağı)
        # F8-A3 (operatör kararı 2026-08-23): üretici KANONİK kol adını yazar — eski
        # "learning_halted" dönem sonuna dek EŞANLAMLI-OKUNUR (durum_sozlugu.KOL_KANONIK
        # listesinde; okuyucu `kol_adi()` sayaçlı çevirir). Değer değişikliği davranış
        # değiştirmez: bu status'u Python tarafında karşılaştıran üretim okuyucusu yok
        # (grep 2026-08-23 — yalnız pano f8KolAd, o da kanoniği aynen geçirir).
        return {"status": "halt_learning", "detail": "state/LEARN_HALT aktif — ship engellendi"}
    with _ProcessLock() as pl:
        if not pl.held:
            return {"status": "locked", "detail": "başka bir süreçte yansıma sürüyor — bu öneri atlandı"}
        return _submit_locked(proposal, goal, windows)


def _submit_locked(proposal: dict, goal: dict | None = None, windows: tuple | None = None) -> dict:
    """Her hipotezin geçtiği boru hattı — kilit ALINMIŞKEN koşar (yalnız `submit` çağırır).

    Sıra: guard (şekil/kara liste; bileşik öneri kuyruğa) → OOS kapısı (incumbent ve aday AYNI
    motor ve AYNI pencerelerde) → teyit yürüyüşü → Y1 sert kapıları (DSR/PBO) → ship (sürüm
    artırımı, anlık görüntü, skor tablosu, defter). Her dal deftere bir statüyle yazılır.

    Fail-closed: teyit ÖLÇÜLEMEDİĞİNDE (dilimler var ama hüküm yok) ship ENGELLENİR —
    "ölçülemedi" ne "geçti" ne "reddedildi"dir. DSR gerçek-parada sert, kâğıtta damga; PBO
    ölçülebiliyorsa iki modda da serttir."""
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
        # BİLEŞİK ÖNERİ KUYRUĞA BURADA YAZILIR (guard'da DEĞİL). guard SAF kalmak zorunda:
        # sert zarf yasası (test_gate_statistics_v74) o modülde hiçbir defter/LLM/ağ kanalı
        # bulunmamasını çiviliyor ve bir kuyruk yazımı tam olarak o kanaldır. guard yalnız ŞEKİL
        # hükmü verir (`composite_pending_queue`), yazımı ÇAĞIRAN yapar. Bileşik öneri CANLIYA
        # GİRMEZ — statüsü `rejected_by_guard` DEĞİL `queued_composite`tir: "reddedildi" demek,
        # ölçüme giden bir fikri mezarlığa yazmak olurdu (ölü-aile sayımını da kirletirdi).
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
    # ---- SHIP KAPISINDAKİ DELİK — "ÖLÇÜLEMEDİ" ARTIK "GEÇTİ" DEĞİL -----------------------------
    # ESKİSİ: `if conf.law == "probabilistic":` — yani teyit yürüyüşü olasılıksal bir hüküm
    # VEREMEDİĞİNDE bütün blok ATLANIYOR ve aday teyit edilmeden SHIP ediliyordu. `confirm()` DÖRT
    # ayrı sebeple `law="legacy"` döner ve ÖLÇÜLDÜ (hepsi p=None, n_valid=0):
    #     [A] dilim yok           → "teyit dilimi yok — legacy yasa"
    #     [B] teyit dilimi ince   → "teyit dilimi ince (6 < 21 işlem) — SHIP YETKİSİ BU KANITLA
    #                                VERİLEMEZ"          ← kod bunu YAZIYOR, ship yolu YOK SAYIYORDU
    #     [C] teyit dilimi boş    → aynı taban dalı (0 < 21)
    #     [D] dilim sınırı bozuk / geçerli replikasyon yetersiz → probgate.evaluate legacy döner
    # GEÇMİŞ VAKA (ADIYLA, retro DÜZELTİLMEDİ): **H00029 → v0003** (`entry.w_prox` None→0,15,
    # 2026-07-20) `confirm_p=null`, `confirm_n_valid=0` ile SHIP edildi; değeri `strategy.evaluate_entry`
    # varsayılanının aynısıydı, yani ölçülemeyen bir NO-OP canlıya çıktı. Defter GERİYE DÖNÜK
    # DÜZELTİLMEZ (tarihçe bozulur); bu düzeltme yalnız bundan sonrasını bağlar.
    #
    # ÜÇ DEĞERLİ HÜKÜM: geçti · geçmedi · ÖLÇÜLEMEDİ. Üçüncüsü ship'i ENGELLER (fail-closed).
    # [A] AYRI TUTULUR ve tek meşru atlama sebebidir: dilim YOKSA teyit mekanizması o ortamda hiç
    # YÜRÜRLÜKTE DEĞİLDİR (fikstür/sandbox, arama ayağı da orada legacy marj yasasında koşuyor) —
    # olmayan bir sınavdan kalmak diye bir şey yok. [B]/[C]/[D] ise dilimler VARKEN ölçümün
    # YAPILAMAMASIDIR ve orada susmak, tam olarak bu deponun en pahalı hatasıdır.
    _teyit_yururlukte = bool(OutOfSamplePipeline.has_slices(inc)
                             and OutOfSamplePipeline.has_slices(cand))
    if conf.law == "probabilistic":
        gate["confirm_durum"] = "gecti" if conf.passes else "gecmedi"
    else:
        gate["confirm_durum"] = "olculemedi" if _teyit_yururlukte else "yasa_yururlukte_degil"
    gate["confirm_beyan"] = {
        "gecti": "teyit dilimi ÖLÇÜLDÜ ve adayı DOĞRULADI",
        "gecmedi": "teyit dilimi ÖLÇÜLDÜ ve adayı REDDETTİ — kazananın-laneti yakalandı",
        "olculemedi": ("teyit dilimi ÖLÇÜLEMEDİ (dilimler var, hüküm yok) — ship fail-closed "
                       "ENGELLENDİ; bu bir kalite reddi DEĞİL, kanıtın YOKLUĞUdur"),
        "yasa_yururlukte_degil": ("bu ortamda OOS dilimi YOK (fikstür/sandbox) — teyit mekanizması "
                                  "hiç yürürlükte değil; arama ayağı da legacy marj yasasında"),
    }[gate["confirm_durum"]]
    if gate["confirm_durum"] == "olculemedi":
        gate["confirm_failed"] = True          # bekçiler/pano için: bu satır ship ETMEDİ
        _neden = (f"teyit ÖLÇÜLEMEDİ: {conf.why or 'sebep beyan edilmedi'} — ölçülemeyen bir aday "
                  f"ship edilemez (fail-closed). ÖLÇÜLEMEDİ ≠ GEÇTİ ve ≠ REDDEDİLDİ.")
        hyp = memory.record({**base, "version_to": None, "status": "rejected_by_confirmation",
                             "backtest": gate, "reject_reasons": [_neden]})
        memory.distill_lessons()
        return {"status": "rejected_by_confirmation", "gate": gate, "hypothesis": hyp,
                "beyan": gate["confirm_beyan"]}
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
    #
    # NEREDE DURDUĞU BİR TASARIM KARARIDIR. Kural `_gate_eval`in İÇİNDE DEĞİL, SHIP yolunda:
    #   * `_gate_eval` arama döngüsünde binlerce kez çağrılıyor ve `passes` semantiği ORADA
    #     değişmedi — DSR o fonksiyonda hâlâ `passes` satırının ALTINDA üretilir, yani hükme
    #     girmesi kod düzeninde imkânsız kalır (kasıtlı sıralama korundu).
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
        # EBEVEYN SATIRI ARTIK HÜKÜMLE BİRLİKTE YAZILIR. Eskiden yalnız bir SAYI
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
        # TANIMLIDIR. Eskiden böyle değildi ve v3 tam o delikten skorsuz ship edildi;
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
    # this version can never mistake it for a global baseline (the plain-key fallbacks in
    # rollback read only unannotated keys, so annotated entries fall through to population-consistent
    # sources by construction).
    oos_field = {f"backtest_oos@{ereg}": cand_oos} if ereg else {"backtest_oos": cand_oos}
    # TAM-PENCERE DEFTERİ (`backtest_full`) ARTIK SHIP YOLUNDAN DA DÜŞER (akıbet kalemi N00017).
    # Bugüne kadar o alanı YALNIZ re-seed (`run.replay_seed`) yazıyordu, dolayısıyla
    # `analytics._backtest_beklenti_r`ın ÖNCELİKLİ bacağı ship edilen HER sürümde boştu ve tavan
    # hükmü "ölçülemedi" doğuyordu (fiş 1/4/9). Kapanan şey bir HESAP değil bir KABLOdur: detay
    # `walk_forward`ın `full_detail`i olarak (= `BacktestResult.detail(goal)` = `score.score_detail`)
    # ZATEN hesaplanmıştı ve atılıyordu — yeni bir replay koşulmaz.
    #
    # İKİ SHIP, İKİ ANAHTAR, İKİ POPÜLASYON (2026-09-02'de tamamlandı — TSK-002).
    # `full_detail` replay'in BÜTÜN işlemlerinden üretilir (rejim dilimlenmemiş), oysa rejim
    # ship'inde sürüm yalnız o rejimin diliminde notlandırılır. TARİHÇE: 2026-09-01'de rejim satırı
    # bilinçli olarak BOŞ bırakılmıştı ve gerekçesi şuydu — düz `backtest_full` yazmak ÖNCELİKLİ
    # bacağa global bir popülasyon koyup rejim dilimli fold bacağını ezerdi (`backtest_oos@<rejim>`
    # ek-adının önlediği hatanın ta kendisi), `backtest_full@<rejim>` yazmak ise YALAN olurdu çünkü
    # içerik rejim dilimi DEĞİLDİ. O gerekçe hâlâ geçerli; ORTADAN KALKAN şey ikinci şıkkın
    # önkoşuluydu: `walk_forward` artık rejimli çağrıda İKİNCİ bir defter döndürüyor
    # (`full_detail_graded` = `score_detail(graded, goal)`, popülasyon = `_regime_slice(...)`),
    # yani ek-adlı anahtarın içeriği ARTIK GERÇEKTEN rejim dilimidir.
    #
    # DÜZ ANAHTAR REJİM SATIRINA YİNE ASLA DÜŞMEZ: `analytics`in düz-anahtar geri-düşüşü damgasız
    # girdiyi GLOBAL sayar; `rollback` ise `backtest_full`ü HİÇ okumaz (ölçüldü, inceleme
    # 2026-09-02) — onun damgasız yasası `backtest_oos` içindir (yukarıdaki `oos_field` notu).
    # Ek-ad, düz anahtarın YANINA değil YERİNE geçer. Üretici defteri vermezse anahtar HİÇ yazılmaz;
    # `None` yazmak "ölçtük, boş çıktı" diye okunurdu. Çivi: `test_rejim_tam_pencere_v371`.
    #
    # `.get` + `isinstance`: üretici sözleşmesini burada SERT indeksleme değil ÇİVİ zorlar
    # (`test_karne_veri_hatti_v293::test_A_a_full_detail_URETICIDE_VAR_ship_yolunun_okudugu_alan`).
    # Sert indeksleme, `walk_forward`ı taklit eden bir düzine test dosyasını konuyla ilgisiz
    # biçimde kırardı ve kırılma yeri kusuru DEĞİL fikstürü gösterirdi.
    versioning.update_scoreboard(candidate["version"], params=candidate["params"],
                                 parent=int(current.get("version", 1)),
                                 backtest_folds=cand["oos_folds"],
                                 backtest_holdout=cand["holdout_score"], overfit_suspect=overfit_suspect,
                                 changed_variable=v.variable, live_since=memory.now_iso(),
                                 **({"backtest_full": cand["full_detail"]}
                                    if ereg is None and isinstance(cand.get("full_detail"), dict)
                                    else {}),
                                 # `if ereg` (doğruluk) — `oos_field`in yasasıyla BİR: boş dizge de
                                 # globaldir (`_regime_slice` filtre uygulamaz) ve `is not None`
                                 # burada okunamayan bir `backtest_full@` doğururdu (inceleme
                                 # 2026-09-02 bulgu-2; üreticinin kendi kapısı da `if eval_regime`).
                                 **({f"backtest_full@{ereg}": cand["full_detail_graded"]}
                                    if ereg
                                    and isinstance(cand.get("full_detail_graded"), dict)
                                    else {}),
                                 **oos_field)
    # SPY-üstü alfa DAMGASI — kapının bileşeni DEĞİL (hedef fonksiyonunu uçuşta değiştirmek
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
    """Strateji sözlüğünün düz `params` haritasını döndürür (yoksa boş sözlük)."""
    return strategy.get("params", {})


# ---------------- coordinate-descent search (the escape from the ±1 trap) ----------------
# A single ±1-step move almost never clears +0.02 OOS, so the deterministic proposer re-hammered the same
# 3-4 dead moves forever and nothing ever shipped. This searches SEVERAL values per knob across ALL knobs,
# magnitude-first (bigger moves first), through the SAME _gate_eval law. It NOMINATES; submit() still SHIPS.
_PROBE_CACHE: dict = {}
# SONDA ÖNBELLEĞİ DİSKE: ısınma sprintleri her yeniden başlatmada aynı walk-forward'ları yeniden
# hesaplıyordu (bellek-içi önbellek uçucu). Sonuçlar bar-revizyon anahtarlı tek JSON'da birikir:
# sprintler üst üste eklenir, 20 dakikalık aramalar önbellek isabetiyle kısalır. Revizyon uyuşmayan
# dosya YOK sayılır (bayat bar dersi). LRU tavanı: dosya şişmesin.
PROBE_DISK_FILE = "probe_cache.json"
PROBE_REV_FILE = "wf_cache_rev.json"
PROBE_DISK_CAP = 300
_PROBE_DISK_LOADED = False


def _probe_disk_load() -> None:
    """Diskteki sonda önbelleğini `_PROBE_CACHE`e SÜREÇ BAŞINA bir kez yükler.

    Yalnız bar revizyonu uyuşuyorsa alınır — revizyonu uymayan dosya YOK sayılır (bayat bar
    dersi). Okuma düşerse tek belirti koordinat inişinin yavaşlamasıdır, uyarı bırakılır."""
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
    """Sonda önbelleğinin son `PROBE_DISK_CAP` girdisini yürürlükteki bar revizyonuyla damgalayıp
    diske yazar (LRU tavanı dosyayı şişmekten korur)."""
    try:
        rev = int(store.read_json(PROBE_REV_FILE, {}).get("rev", 0))
        keys = list(_PROBE_CACHE.keys())[-PROBE_DISK_CAP:]
        store.write_json(PROBE_DISK_FILE, {"rev": rev,
                                           "entries": {k: _PROBE_CACHE[k] for k in keys}})
    except Exception as e:
        _cache_warn("probe_cache_save_failed", e)


def _already_failed(var: str, val, hyps: list, bounds: dict) -> bool:
    """Bu (değişken, değer) çifti defterde daha önce ÇÖKTÜ mü — hafızanın TEK tanımı.

    "Başarısız" kümesi guard'ın kalıcı kara listesiyle birebir aynıdır:
    `rejected_by_backtest` ya da `rolled_back`. `@rejim` son-eki taban ada çözülerek tip
    aranır, böylece rejim-hedefli düğmelerde de KeyError'suz çalışır."""
    base = str(var).split("@", 1)[0]
    typ = bounds[base]["type"] if base in bounds else "float"
    for h in hyps:
        if h.get("variable") == var and guard._equalish(h.get("new"), val, typ) \
                and h.get("status") in ("rejected_by_backtest", "rolled_back"):
            return True
    return False


def _probe_key(cand_strat: dict, var: str, new, w: tuple) -> str:
    """Sonda önbellek anahtarı: pencere + TÜM parametre dünyası (düz + rejim-tablosu) + değişken +
    değer.

    Sürüm NUMARASI anahtara girmez (geri alma sonrası aynı numara farklı paramlarla dönebilir);
    `var` anahtarda kalır çünkü eval_regime'i, yani notlandırma nüfusunu belirler."""
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


def _havuz_tavani(tavan: int = 4) -> int:
    """Havuz işçi sayısı TAVANI: `max(1, cpu-2)`, ayrıca çağıranın kendi tavanıyla sınırlı.

    CANLI OLAY (2026-08-03, A1 4 OCPU): iki işçi iki saat boyunca %99,9 CPU'da koştu ve pano
    API'sini boğdu (`/api/diagnostics` 8,8-10,4 sn) — operatör elle `renice` atmak zorunda kaldı.
    "-2" tam bu yüzden var: bir çekirdek uvicorn'a, bir çekirdek işlem döngüsü/hermes ipliğine
    kalmalı. ESKİ HÂLİ `max(2, ...)` İDİ ve tabanı 2'ye ÇİVİLİYORDU: 2 çekirdekli bir makinede
    "cpu-2 = 0" hesabını EZİP yine iki işçi açıyordu, yani tavan orada hiç yoktu. Taban 1'e indi.
    Arama SONUÇLARI değişmez — işçi sayısı yalnız duvar-saatini belirler (sonuçlar `_havuz_sonuclari`
    üzerinden tamamlanma sırasıyla gelir ama her sonda bağımsız ve `_PROBE_CACHE` ANAHTARLIDIR;
    determinizm sıraya değil anahtara dayanır — atalet bekçisi de bu yüzden sırayı korumak
    zorunda değildir)."""
    return max(1, min(tavan, (os.cpu_count() or 4) - 2))


def _pool_worker_init():
    """Süreç havuzu işçisinin açılış kancası: önce `nice(15)` (pano/işlem döngüsü CPU isteyince
    öncelik onlarındır), sonra barları AĞA ÇIKMADAN önbellekten yükler.

    Ebeveyn önbelleği doldurduğu için işçiler donmuş AYNI barları okur — aksi hâlde işçiler
    birbirinin bar dosyalarını yeniden yazardı. Kibarlık kurulamazsa iş sürer (yalnız pano yavaşlar)."""
    # KİBARLIK ÖNCE: işçi AĞIR işe başlamadan önce nice'lanır — dataset yüklemesinin
    # kendisi de (I/O + pandas) rekabet eden bir yüktür. `nice(15)` bir CPU TAVANI değildir: işçiler
    # boş makinede yine tam hızda koşar, YALNIZ pano/uvicorn ya da işlem döngüsü CPU isteyince
    # zamanlayıcı onlara öncelik verir. Canlıda elle atılan `renice`in kalıcı hâli budur.
    # SESSİZ YUTMA GEREKÇESİ: nice ayarlanamazsa (platform desteklemiyor, izin yok) yapılacak tek
    # şey daha yavaş bir panodur — arama sonucu ve bu turun hükmü DEĞİŞMEZ; kibarlık kurulamadı
    # diye antrenmanı iptal etmek, ölçülen sorunu (yavaş pano) çözmeyip kanıt üretimini durdururdu.
    try:
        os.nice(15)
    except (OSError, AttributeError):  # sessiz-yutma: kibarlık kurulamadıysa (platform/izin) tek sonuç daha yavaş bir panodur — arama sonucu ve bu turun hükmü DEĞİŞMEZ, işçiyi düşürmek kanıt üretimini durdururdu
        pass
    # AĞA ÇIKMAYAN yükleme ŞART: load() bayat önbellekte fetch eder, fetch corporate-action tespitiyle
    # bar CSV'lerini yeniden yazar — her işçi kendi load()'unu çağırdığında işçiler BİRBİRİNİN barlarını
    # değiştiriyor, aynı aramanın sondaları farklı bar durumlarında ölçülüyordu (canlıda
    # bulundu). Ebeveyn load() ile önbelleği yerleştirir; işçiler o donmuş hali okur → birebir aynı barlar.
    from meridian import dataset as _ds
    _POOL_WORKER_DATA["bars"], _POOL_WORKER_DATA["index"] = _ds.load_cached()


def _pool_probe_job(args: dict) -> tuple:
    """İşçi sürecinde TEK sondanın walk-forward'ını koşar ve `(önbellek_anahtarı, sonuç)` döndürür.

    Barlar `_pool_worker_init`in donmuş kopyasından okunur; ebeveyn sonucu anahtarla eşler, yani
    determinizm tamamlanma sırasına DEĞİL anahtara dayanır."""
    from meridian import backtest as _bt
    w = args["w"]
    wf = _bt.walk_forward(args["params"], _POOL_WORKER_DATA["bars"], _POOL_WORKER_DATA["index"],
                          args["goal"], w[0], w[1], w[2], w[3], strategy_version=args["version"],
                          oos_folds=list(w[4]), embargo_days=w[5],
                          params_by_regime=args["by_regime"], eval_regime=args["eval_regime"])
    return args["key"], wf


# ---- HAVUZ TOPLAM-ATALET TAVANI (2026-08-12 asılı-arama vakası) ---------------------------------
# ÖLÇÜLEN ARIZA (`sprint._arama_durumu` bayatlık yasasının kök tarafı): canlı arama ProcessPoolExecutor açar ve
# `ex.map` sonuç-beklemesi SINIRSIZDIR — ölen/kilitlenen bir işçi süreci ebeveyn iş parçacığını
# sonsuza dek bekletir; SEARCH_PROGRESS.running=True donar ve öğrenme zinciri kilitlenir (canlıda
# 4+ gün ölçüldü; sprint'in bayatlık yasası semptomu 6 saatte söker, bu tavan KAYNAĞI onarır:
# asılı bekleyiş kendini kurtarır, iş parçacığı geri gelir).
#
# YASA: tavan FUTURE-BAŞINA DEĞİL, TOPLAM-ATALETTİR — "son biten işten beri HAVUZ_ATALET_SN boyunca
# HİÇBİR iş bitmediyse havuz ölü sayılır". İlerleyen uzun bir arama (ör. 40 sondalı gece koşusu,
# saatler sürer) ASLA kesilmez: her biten iş sayacı sıfırlar.
#
# EŞİK TÜRETİMDİR — VE TÜRETİM 2026-08-25'TE YANLIŞLANIP YENİDEN ÖLÇÜLDÜ (v318).
# ESKİ GEREKÇE: "bir havuz işi TEK walk-forward'dır ve incumbent-walk ~90 sn ÖLÇÜLÜDÜR;
# 1800 sn = o işin 20 katı". İKİ YERİNDEN BOZUKTU: (1) o ~90 sn `hermes.py`de PANONUN bekleme
# süresi için düşülmüş bir nottur ve BAŞKA bir hesabı anlatır — havuz işi 251 sembollük SONDA
# walk-forward'ıdır; (2) doğru sayı ölçülmemiş değildi, `events.jsonl`da 94 satır hâlinde duruyordu.
#
# ÖLÇÜM (canlı A1, üç bağımsız kaynak — hepsi TEK bir walk-forward'ın süresi):
#     45 başarılı `parallel_probes_prefilled` turu (duvar × işçi / n) ...  2279-3042 sn
#     ardışık `hermes_search_probe` farkı (sıralı yol, 08-17 + 08-21) ...  2487-3185 sn
#     bu dosyanın kendi notu (`prefill_incumbents`, 5065 sn / 2 walk) ...  2532 sn
#
# BEDELİ ÖLÇÜLDÜ: 1800 tek işin ALTINDA kaldığı için ilk bitiş tavana HİÇ yetişemedi — 2026-08-12
# ile 08-25 arasında 61 atalet olayının 61'inde `biten=0`, sıfır havuz sonucu. Havuz 08-12'ye kadar
# ÇALIŞIYORDU (son başarı 08-12T07:40, n=10); tavan o gün indi ve SAĞLIKLI bir mekanizmayı öldürdü.
# Aramanın verimi de aynı gün çöktü: `evaluated` 26/34'ten tam 2'ye indi — tavanın yediği 1800 sn'den
# sonra `MERIDIAN_SEARCH_MAX_MIN` penceresine yalnız iki taze sonda sığıyor.
#
# YENİ TÜRETİM: tavan = ÖLÇÜLEN EN UZUN TEK İŞ × MARJ. Marj 20 değil 3'tür, çünkü artık çarpanın
# ALTINDAKİ SAYI GERÇEK: 3× soğuk önbellek + nice(15) + dolu makineyi karşılar. Sonuç ~9555 sn
# (2 sa 39 dk) ve bayatlık eşiğinin (6 sa) ALTINDA KALIR — kurtarma hâlâ bayrak bayatlamadan, aynı
# gece penceresinde olur; eski yasanın korumak istediği şey buydu ve korunuyor. YASA DEĞİŞMEDİ:
# tavan hâlâ TOPLAM-ATALETTİR (biten her iş sayacı sıfırlar), yalnız sayı ölçülen işten türüyor.
# BAĞLAYICI KISIT İLK İŞTİR: ilk bitişten sonra iki işçide tamamlanmalar ~iş/2'de bir gelir ve
# sayaç sürekli sıfırlanır — yani tavan yalnız "havuz hiç açılamadı" hâlini ölçer.
HAVUZ_IS_SURESI_OLCULEN_SN = 3185.0   # canlıda gözlenen EN UZUN tek walk-forward (yukarıdaki tablo)
HAVUZ_ATALET_MARJI = 3.0
HAVUZ_ATALET_SN = float(os.environ.get("MERIDIAN_HAVUZ_ATALET_SN",
                                       str(HAVUZ_IS_SURESI_OLCULEN_SN * HAVUZ_ATALET_MARJI)))

# CANLILIK KUANTUMU (v302, 2026-08-25). Bekleyiş ARTIK TEK BLOK DEĞİL: `_cf.wait` bu kuantumla
# turlanır ve her turda `canlilik()` ateşlenir. TOPLAM-ATALET YASASI DEĞİŞMEDİ — kurtarma hâlâ
# HAVUZ_ATALET_SN'de tetiklenir, yalnız bekleyiş artık GÖZLENEBİLİR.
#
# NEDEN VAR: `beat("hermes_poll")` yalnız İŞ BİTİNCE atılıyordu; havuz bekleyişi ise tanım gereği
# "hiçbir iş bitmeyen" penceredir. HAVUZ_ATALET_SN (O GÜN 1800; v318'te ~9555) ile bekçi penceresi
# `watchdog.EXPECTED["hermes_poll"]` (1800) BİREBİR EŞİT olduğundan, havuz ataleti her çarptığında
# bayat-geçiş GARANTİYDİ. Alarm bekçi kusuru değildi: kör bir fazı doğru bildiriyordu.
# (2026-08-24 kanıtı: alarm 01:59:48, `arama_havuzu_zaman_asimi biten=0` olayı 02:00:08.)
#
# EŞİTLİK v318'TE KALKTI (tavan 1800 → ~9555) ama bu bir ÇARE DEĞİL, YAN ETKİDİR: tavan ölçülen
# iş süresinden türetilince sayı kendiliğinden ayrıştı. Çare hâlâ ARADA NABIZ ATMAKTIR ve v318 bunu
# GEVŞETMEZ, SIKILAŞTIRIR: bekleyiş artık bekçi penceresinin kat kat üstünde sürebildiğinden,
# nabız kuantumlanmamış olsaydı v318 bayat-geçişi ortadan kaldırmaz BÜYÜTÜRDÜ. İki yama bu sırayla
# bağlıdır — v302 olmadan v318 dağıtılamaz.
# 60 sn seçimi: bekçinin tespit kadansı 300 sn (scheduler poll), yani 60 sn'lik nabız tespit
# çözünürlüğünün beş katı sık — tespit penceresinde her zaman en az bir nabız bulunur.
HAVUZ_NABIZ_SN = float(os.environ.get("MERIDIAN_HAVUZ_NABIZ_SN", "60"))


class _HavuzAtaleti(RuntimeError):
    """Havuz toplam-atalet tavanına çarptı: son bitenden beri HAVUZ_ATALET_SN geçti, hiçbir iş bitmedi."""
    def __init__(self, bekleyen: int, biten: int):
        """İstisnayı sayılabilir olguyla kurar: kaç iş bitti, kaçı hâlâ bekliyor (mesaj metnine de
        girer, alanlar `bekleyen`/`biten` olarak saklanır)."""
        super().__init__(f"havuz {HAVUZ_ATALET_SN:.0f} sn'dir tek iş bitirmedi "
                         f"(biten {biten}, bekleyen {bekleyen})")
        self.bekleyen, self.biten = bekleyen, biten


def _havuz_sonuclari(ex, jobs: list[dict], canlilik=None):
    """`ex.map` YERİNE toplam-atalet bekçili sonuç akışı. Tamamlanma SIRASI korunmaz ve bu
    ÖNEMSİZDİR: iki tüketici de sonucu ANAHTARLI önbelleğe yazar (_PROBE_CACHE/_INC_CACHE —
    `_havuz_tavani` docstring'indeki determinizm beyanı anahtara dayanır, sıraya değil). Bir işçi
    istisnası `f.result()` ile aynen yükselir (ex.map ile aynı sözleşme).

    `canlilik`: bekleyişin İÇİNDEN, HAVUZ_NABIZ_SN'de bir ateşlenen geri-çağırma (v302).
    "Bir iş bitti" DEMEZ — "bu iplik canlı ve bekliyor" der; bekçinin gerçekte sorduğu soru budur.
    Verilmezse davranış eskisiyle birebir aynıdır (geriye uyum: testler, diğer tüketiciler)."""
    import concurrent.futures as _cf
    kalan = {ex.submit(_pool_probe_job, j) for j in jobs}
    biten = 0
    while kalan:
        # Bekleyiş kuantumlara BÖLÜNÜR ama tavan TOPLAM-ATALETTİR: `atalet` yalnız hiçbir iş
        # bitmediğinde birikir, biten ilk iş onu sıfırlar (yasa dosya başında, değişmedi).
        atalet, done = 0.0, set()
        while True:
            kuantum = min(HAVUZ_NABIZ_SN, HAVUZ_ATALET_SN - atalet)
            if kuantum <= 0:
                break
            done, kalan = _cf.wait(kalan, timeout=kuantum, return_when=_cf.FIRST_COMPLETED)
            if done:
                break
            atalet += kuantum
            if canlilik is not None:
                try:
                    canlilik()
                except Exception:  # sessiz-yutma: nabız yazımı bir TELEMETRİ işidir; disk/kilit hatası aramanın kendisini öldürmemeli, ölçülmüş sonucu telemetri arızasına kurban etmek YASA 4'ün tersidir
                    pass
        if not done:                       # tavan penceresi boyunca SIFIR ilerleme → havuz ölü
            raise _HavuzAtaleti(bekleyen=len(kalan), biten=biten)
        for f in done:
            biten += 1
            yield f.result()


def _havuzu_oldur(ex) -> None:
    """Atalete çarpan (ya da terk edilen) havuzu BLOKE ETMEDEN kapat: bekleyenler iptal, işçi
    süreçleri öldürülür. Normal `shutdown(wait=True)` / `with`-çıkışı burada KULLANILAMAZ —
    kilitlenmiş işçinin join'i sonsuza dek bekler, yani kaçılan arızanın kendisi. `_processes`
    özel API'dir; erişilemezse (sürüm değişimi) kalan tek bedel nice(15)'li yetim bir süreçtir
    ve zaman-aşımı olayı zaten beyan edilmiştir. İşçiler yalnız HESAPLAR (donmuş bar önbelleği,
    yazım ebeveynde) — öldürmek hiçbir state yazımını yarıda kesmez."""
    # SIRA YASADIR — TUTAMAKLAR shutdown'dan ÖNCE YAKALANIR (v317, canlı ölçüm).
    # `ProcessPoolExecutor.shutdown()` gövdesinin sonunda koşulsuz bir `self._processes = None`
    # vardır ve `wait` bayrağına BAKMAZ (CPython 3.12 process.py). Yakalama shutdown'dan SONRA
    # yapılırsa `getattr(ex, "_processes", {})` varsayılan `{}`e DÜŞMEZ — öznitelik VARDIR, değeri
    # `None`dır — ve `None.values()` AttributeError fırlatıp aşağıdaki yutucuya düşer: `terminate()`
    # HİÇ ÇAĞRILMAZDI. ÖLÇÜLDÜ (A1, 2026-08-25): 18:56:29'daki atalet olayından sonra iki işçi 19:43'te
    # hâlâ ayaktaydı — biri %99,8 CPU'da (sonucu artık kimsenin okumayacağı bir walk-forward),
    # öbürü `anon_pipe_read`de donmuş, ikisi de ~225 MB tutuyor. Kaçağın ÖMRÜ DE ÖLÇÜLDÜ ve
    # SINIRLIDIR: 20:05'te ikisi de gitmişti — yani süreçler terk edildikten sonra ~47-69 dk daha
    # yaşıyor (kabaca elde kalan bir walk-forward kadar) ve `terminate()` koştuğu için değil, işleri
    # bitip terk edilmiş kuyruk yıkıldığı için ölüyorlar. Bedel kalıcı bir sızıntı DEĞİL, atalet
    # başına ~1 saatlik tam çekirdek + ~450 MB — üstelik tam da sıralı yedek yolun CPU istediği
    # pencerede, yani `_havuz_tavani`nin uvicorn'a ayırdığı çekirdeği geri alarak.
    procs = list((getattr(ex, "_processes", None) or {}).values())
    ex.shutdown(wait=False, cancel_futures=True)
    try:
        for p in procs:
            p.terminate()
    except Exception:  # sessiz-yutma: terminate'in KENDİSİ düştü (izin/yarış) — havuz yine kapalı (wait=False) ve arama sıralı yolda devam ediyor; bedel nice'lenmiş yetim süreç, zaman-aşımı olayı bunu zaten beyan etti. NOT: bu yutucunun eski gerekçesi "sürüm değişiminde _processes'e erişilemezse" diyordu ve YANLIŞLANDI — o dal bir uç durum değil TEK durumdu (yukarıdaki sıra yasası)
        pass


def _parallel_prefill_probes(probes, current, version, goal, w, regime, canlilik=None) -> None:
    """Sonda walk-forward'larını havuzda ÖNCEDEN hesaplayıp _PROBE_CACHE'e doldurur; ana döngü
    değişmeden (deterministik sıra + K-ceza + erken-en-iyi seçimi) önbellekten tüketir."""
    if os.environ.get("MERIDIAN_PARALLEL_PROBES") != "1" or len(probes) < 2:
        return
    ex = None
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
        workers = _havuz_tavani(4)          # kibarlık + tavan gerekçesi: `_havuz_tavani` docstring'i
        ctx = mp.get_context("spawn")
        # `with` BİLEREK YOK: with-çıkışı `shutdown(wait=True)`dır ve kilitlenmiş bir işçide
        # sonsuza dek bekler — asılı-arama vakasının mekanizmasının ta kendisi. Kapatma üç yolda da
        # AÇIK: normal (bekle — işler bitti, join anlık), atalet (öldür), istisna (öldür + yeniden fırlat).
        ex = ProcessPoolExecutor(max_workers=workers, mp_context=ctx, initializer=_pool_worker_init)
        for key, wf in _havuz_sonuclari(ex, jobs, canlilik=canlilik):
            _PROBE_CACHE[key] = wf
        ex.shutdown()
        _probe_disk_save()
        from . import obs as _obs
        _obs.log("parallel_probes_prefilled", n=len(jobs), workers=workers)
    except _HavuzAtaleti as z:
        _havuzu_oldur(ex)
        _probe_disk_save()                  # BİTEN sondalar kaybolmaz — kısmi ilerleme diske iner
        from . import obs as _obs
        _obs.alarm(_obs.ALARM_ARAMA_HAVUZU_OLU,
                   f"arama havuzu (probe_prefill) {HAVUZ_ATALET_SN:.0f} sn'de TEK İŞ bitirmedi "
                   f"(biten {z.biten}, bekleyen {z.bekleyen}) — öğrenme hattı ÜRETMİYOR; "
                   "bu bir CANLILIK değil TESLİMAT arızasıdır (iplik nabız atıyor olabilir)",
                   yer="probe_prefill", atalet_sn=HAVUZ_ATALET_SN, biten=z.biten, bekleyen=z.bekleyen)
        # TARİHÇE KORUNUR: `warn` satırı SİLİNMEZ — olay defterindeki 61 kayıtlık seri aynı adla
        # sürsün ki geçmişle kıyas kopmasın. Alarm EKLENİR, yerine geçmez.
        _obs.warn("arama_havuzu_zaman_asimi", yer="probe_prefill", atalet_sn=HAVUZ_ATALET_SN,
                  biten=z.biten, bekleyen=z.bekleyen,
                  detail="havuz toplam-atalet tavanına çarptı (son bitenden beri hiçbir iş "
                         "bitmedi) — işçiler öldürüldü, kalan sondalar ana döngüde SIRALI "
                         "hesaplanır; arama ölmez, bayrağı da arama sonu / reflect_once finally "
                         "ağı temizler (asılı bekleyiş artık kendini kurtarıyor)")
    except Exception as e:
        if ex is not None:
            _havuzu_oldur(ex)               # sağlıklı işçiler cancel+terminate ile bloke etmeden iner
        from . import obs as _obs
        _obs.warn("parallel_probes_failed", error=f"{type(e).__name__}: {e}",
                  detail="sıralı yola düşüldü — davranış birebir")


def prefill_incumbents(bars, index, regimes: list, goal: dict | None = None,
                       windows: tuple | None = None, canlilik=None) -> dict:
    """Boşta incumbent ön-hesabı: sıradaki muhtemel yansımaların (global + canlı rejim + ufku dolu
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
        key = _wf_key(params, version, goal, by_regime, w, er)   # TEK KAYNAK (bkz. `_wf_key`)
        (missing.append((key, er)) if key not in _INC_CACHE else None)
        cached += 1 if key in _INC_CACHE else 0
    if missing and os.environ.get("MERIDIAN_PARALLEL_PROBES") == "1" and len(missing) > 1:
        ex = None
        try:
            from concurrent.futures import ProcessPoolExecutor
            import multiprocessing as mp
            jobs = [{"key": k, "params": params, "by_regime": by_regime, "version": version,
                     "goal": goal, "w": (w[0], w[1], w[2], w[3], list(w[4]), w[5]), "eval_regime": er}
                    for k, er in missing]
            ctx = mp.get_context("spawn")
            # AYNI TAVAN BURADA DA: incumbent ön-hesabı da aynı süreçte, aynı
            # çekirdekleri paylaşarak koşuyor. Kendi 3'lük sınırı KORUNUR (tavan onu yükseltmez,
            # yalnız düşürebilir) — kibarlaştırma hiçbir yolda yükü ARTIRMAmalı.
            # `with` bilerek yok + atalet bekçisi — gerekçe `_parallel_prefill_probes`teki
            # blokla AYNI: bu havuz da hermes iş parçacığını sonsuza dek bekletebiliyordu.
            ex = ProcessPoolExecutor(max_workers=min(len(jobs), _havuz_tavani(3)), mp_context=ctx,
                                     initializer=_pool_worker_init)
            for key, wf in _havuz_sonuclari(ex, jobs, canlilik=canlilik):
                _INC_CACHE[key] = wf
                computed += 1
            ex.shutdown()
            _inc_disk_save()
        except _HavuzAtaleti as z:
            _havuzu_oldur(ex)
            _inc_disk_save()                # biten incumbent'lar kaybolmaz — kısmi ilerleme diske iner
            from . import obs as _obs
            _obs.alarm(_obs.ALARM_ARAMA_HAVUZU_OLU,
                       f"arama havuzu (incumbent_prefill) {HAVUZ_ATALET_SN:.0f} sn'de TEK İŞ "
                       f"bitirmedi (biten {z.biten}, bekleyen {z.bekleyen}) — öğrenme hattı "
                       "ÜRETMİYOR; bu bir CANLILIK değil TESLİMAT arızasıdır (iplik nabız "
                       "atıyor olabilir)",
                       yer="incumbent_prefill", atalet_sn=HAVUZ_ATALET_SN,
                       biten=z.biten, bekleyen=z.bekleyen)
            # TARİHÇE KORUNUR: `warn` satırı SİLİNMEZ — olay defterindeki 61 kayıtlık seri aynı
            # adla sürsün ki geçmişle kıyas kopmasın. Alarm EKLENİR, yerine geçmez.
            _obs.warn("arama_havuzu_zaman_asimi", yer="incumbent_prefill", atalet_sn=HAVUZ_ATALET_SN,
                      biten=z.biten, bekleyen=z.bekleyen,
                      detail="incumbent ön-hesap havuzu toplam-atalet tavanına çarptı — işçiler "
                             "öldürüldü, eksikler aşağıdaki SIRALI yolda hesaplanır (boşta ön-hesap "
                             "asılı kalıp hermes iş parçacığını kilitleyemez)")
            missing = [(k, er) for k, er in missing if k not in _INC_CACHE]
        except Exception as e:
            if ex is not None:
                _havuzu_oldur(ex)
            from . import obs as _obs
            _obs.warn("incumbent_prefill_pool_failed", error=f"{type(e).__name__}: {e}")
            missing = [(k, er) for k, er in missing if k not in _INC_CACHE]
    for _k, er in missing:
        if _k not in _INC_CACHE:
            # (2) NUMARALI KÖR FAZ (v302): havuz atalete çarpınca akış BURAYA düşer ve her
            # `_wf_cached` bir TAM walk-forward'dır. Canlıda ölçüldü: 02:00:08 → 03:24:33
            # arası 5065 sn / 2 walk-forward, sıfır nabız. Havuz bekleyişini kuantumlamak bu
            # bacağı KAPSAMAZ — burası havuz değil, sıralı hesap. Her iş bitiminde nabız.
            _wf_cached(params, version, bars, index, goal, by_regime, windows=w, eval_regime=er)
            computed += 1
            if canlilik is not None:
                try:
                    canlilik()
                except Exception:  # sessiz-yutma: telemetri hatası ön-hesabı öldürmemeli; sonuç zaten _INC_CACHE'e yazıldı, kaybolan yalnız bir nabızdır
                    pass
    if computed:
        from . import obs as _obs
        _obs.log("incumbents_prefilled", computed=computed, cached=cached,
                 regimes=[r or "global" for r in variants])
    return {"computed": computed, "cached": cached}


def coordinate_descent_search(bars, index, goal: dict | None = None, *, windows: tuple | None = None,
                              k_max: int = 3, budget: int = 10, tried: set | None = None,
                              on_probe=None, regime: str | None = None,
                              max_minutes: float | None = None,
                              deadline_ts: float | None = None,
                              canlilik=None,
                              record_session: bool = True) -> dict:
    """Walk the incumbent ONCE, then probe up to `budget` single-variable candidates (magnitude-first,
    breadth across UCB-ranked knobs) through the SAME OOS gate. Returns the best gate-CLEARING probe (or
    None). Probes are NOT recorded as hypotheses — a probe that lost vs this incumbent is not a permanent
    dead end (unlike a real submit rejection).
    regime (Phase 3): a REGIME-TARGETED search — every probe becomes var@regime (routed into
    params_by_regime by versioning.bump) and BOTH incumbent and candidates are graded only on that
    regime's trades. The current value each probe steps from is the regime override when one exists,
    else the global value (that IS the effective value the regime trades under today).

    SÜRE TAVANI — `max_minutes` / `deadline_ts`, VARSAYILAN YOK.
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
    kolaylık hâline gelirdi — süre tavanının kalite üzerinde yetkisi yoktur.

    ---- RESMÎ KAYIT: OTURUM BAŞINA BİR --------------------------------------------------------
    `record_session` — oturum sonunda TEK resmî değerlendirme kaydı düşürülür mü?

    VAKA (ölçülmüş): sonda döngüsü `_gate_eval(..., record_erosion=True)` çağırıyordu, yani HER
    sonda hem aşınma sayacını +1 artırıyor hem doğrulama defterine bir satır yazıyordu. Tek bir gün
    (2026-07-30 07:11→14:04) 204 satır yazdı, `erosion.queries` 351→554'e tırmandı, aynı oturumun
    `k_probes`ı sabit kalarak (17/27/40) her satırda yeniden sayıldı ve 204 satırda yalnız 60 ayrık
    etiket kaldı (aynı aday altı kez, PBO popülasyonu kopyalarla kirli). Kodun KENDİ yorumu bunun
    tersini söylüyordu: "arama oturumu pencereye BİR soru sorar".

    ÇİFTE CEZA BEYANI — İKİ AYRI YÜK, HER BİRİ BİR KEZ SAYILIR:
      * `erosion.queries` = OTURUMLAR ARASI seçilim baskısı ("bu pencere geometrisine ömür boyu kaç
        RESMÎ soru soruldu"). Bir arama oturumu BİR soru sorar → oturum sonunda +1.
      * `k_probes`        = OTURUM İÇİ çoklu test ("o tek soruyu sorarken kaç aday taradık") → K.
    `_gate_eval` ikisini `_n_trials = erosion.queries + k_probes` ile TOPLAR. Sonda başına kayıt,
    K'lık yükü aşınma sayacına K KEZ yazıp üstüne `k_probes` ile bir kez daha yazıyordu — aynı yükün
    iki kanaldan, biri K kat şişmiş hâlde fiyatlanması. Artık her yük kendi kanalında tam bir kez.

    MARJ HER ÇAĞRIDA UYGULANIR, SAYIM UYGULANMAZ (`oos_erosion.status` vs `note`): sondalar aşınmış
    bir pencerede AYNI çıtayı görür — yalnız sayacı ilerletmezler. Yan etki olarak sondalar artık
    OTURUM BOYUNCA SABİT bir marj görür; eskiden ilk sonda sayacı artırdığı için sonraki sondalar
    kendi oturumlarının açtığı çıtayla yarışıyordu (ölçüm aracının kendi ölçtüğü şeyi değiştirmesi).

    KİM YAZAR: kapıyı geçen aday VARSA resmî kaydı `submit()` düşürür — ship otoritesi AYNI kapıyı
    aynı K ile yeniden koşar ve deftere o adayı yazar. Burada ikinci bir satır yazmak aynı oturumu
    iki kez saymak ve PBO ızgarasına aynı adayı iki kopya sokmak olurdu. Geçen aday YOKSA kaydı bu
    fonksiyon düşürür (oturum temsilcisi = en yüksek OOS'lu değerlendirilmiş aday), çünkü pencereye
    soru SORULDU ve sorulmuş bir soruyu saymamak aşınmayı bedavaya getirirdi.
    BEYAN EDİLMİŞ BOŞLUK: kazanan aday `submit`in GUARD dalında (kapıdan önce) reddedilirse o oturum
    kayıtsız kalır. Arama yalnız bounds içinden sonda ürettiği için nadirdir; her ship oturumunu iki
    kez saymaya yeğlenmiştir ve kapatmak `submit`in guard dalına dokunmayı gerektirir (bu turun
    kapsamı dışında).
    `record_session=False`: çağıran YAPISAL OLARAK ship edemiyorsa (ısınma sprinti — "Nothing ships")
    resmî kayıt YAZILMAZ; ship edemeyen bir tur için resmî soru saymak, hiç sorulmamış bir soruyu
    deftere yazmak olurdu. Kalan kanal (ısınmanın UCB önceliklerini ısıtması) dolaylı bir seçilim
    yoludur ve bu tur onu ÖLÇMEDİ — açık ölçüm borcu, sayıya çevrilmiş bir varsayım değil."""
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
        """Süre tavanı aşıldı mı? Tavan kurulmamışsa (None) daima False — yani tavansız arama
        kesilmez. Saat incumbent yürüyüşü DAHİL en başta başlatılmıştır."""
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
    # Ö-48 HAYALET SÜZGECİ: motor-okuyucusuz anahtar sonda listesine hiç girmez; süzülenler hem
    # olayla hem bu fonksiyonun dönüşündeki `hayalet_suzulen` alanıyla görünür (None = ölçülemedi).
    arama_uzayi, hayalet_suzulen = hayalet_suzgeci(bounds, kaynak="coordinate_descent_search")
    ranked = _ucb_rank(arama_uzayi, hyps)           # untried knobs first (+inf), then by historical reward

    probes, seen = [], set()
    for k in range(k_max, 0, -1):                   # magnitude-first: biggest moves of every knob first
        for var in ranked:
            if regime and var.startswith("regime."):
                continue    # regime.* feeds regime DETECTION (pre-regime) — a @regime override is
                            # structurally dead; probing it burns budget on guaranteed rejections
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
    # UYARLANABİLİR BÜTÇE: `budget` artık TAZE (önbellek-ıskası) hesap sayısıdır. Önbellekte
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
    _parallel_prefill_probes(probes, current, version, goal, w, regime, canlilik=canlilik)
    _t0 = _time.time()
    _max_min = float(os.environ.get("MERIDIAN_SEARCH_MAX_MIN", "35"))
    _fresh_done = _skipped_fresh = 0

    evaluated = cleared = 0
    best, trace = None, []
    # OTURUM TEMSİLCİSİ: resmî kayıt oturum SONUNDA bir kez düşer ve bir adayın walk-forward
    # sözlüğünü ister. `rep_cand` = en yüksek OOS'lu DEĞERLENDİRİLMİŞ aday — yani oturumun en güçlü
    # ölçümü. Kapıyı geçen bir aday varsa resmî satırı zaten `submit` yazar (o adayla), bu yüzden
    # temsilci yalnız "hiçbiri geçmedi" dalında kullanılır ve `passes` ölçütüne göre seçilmesi
    # gereksiz olurdu: geçen aday yoksa geçme ölçütü ayırt edici değildir.
    rep_cand = None
    rep_oos = None
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
        # SONDA DEĞERLENDİRMESİ KAYITSIZDIR. Yasa AYNEN koşar (tam kapı + K-aday
        # kazanan-laneti cezası + yürürlükteki aşınma MARJI); yazılmayan tek şey SAYIM'dır. Buradaki
        # `record_erosion=True` kodun kendi beyanının tam tersini yapıyordu: yorum "oturum pencereye
        # BİR soru sorar" derken defter sonda başına bir soru sayıyordu. Oturumun tek resmî kaydı
        # döngüden SONRA (ya da `submit` tarafından) düşer — bkz. fonksiyon başlığı.
        passes, gate, _why = _gate_eval(inc, cand, k_probes=total, record_erosion=False)   # FULL gate + K-aday cezası (winner's curse)
        evaluated += 1
        c_oos = cand.get("oos_score")
        if rep_cand is None or (c_oos is not None and (rep_oos is None or c_oos > rep_oos)):
            rep_cand, rep_oos = cand, c_oos
        # RED GEREKÇESİ İZE GİRER (2026-08-21, canlı kuraklık teşhisi). `_gate_eval` gerekçeyi
        # ZATEN üretiyordu ve `_why` burada ATILIYORDU — üretilip çöpe atılan bir alan YASA 6'nın
        # tam tersidir. Canlı belirti: `warmup_sprint evaluated=40 cleared=0` günlerce basıldı ve
        # operatör NEDEN'i hiçbir yerden okuyamadı; kuraklık teşhis EDİLEMEZ bir sayıydı.
        # Yalnız GEÇMEYEN sonda için yazılır: geçen sondanın "gerekçesi" yoktur.
        trace.append({"variable": var, "new": new, "old": old,
                      "candidate_oos": c_oos, "incumbent_oos": inc_oos,
                      "fold_wins": gate["fold_wins"], "tail_ok": gate["tail_ok"], "passes": passes,
                      "why": (None if passes else _why)})
        if passes:
            cleared += 1
            # explicit None checks — `or -1e9` treated a legitimate 0.0 score as missing
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
    # ---- OTURUMUN TEK RESMÎ KAYDI --------------------------------------------------------------
    # Üç koşul da ZORUNLU ve her biri ayrı bir sahtelik sınıfını kapatır:
    #   `record_session` — ship edemeyen çağıran (ısınma) resmî soru saymaz.
    #   `evaluated > 0`  — hiç sonda koşmadıysa pencereye soru SORULMADI; sıfır ölçümü bir soru gibi
    #                      saymak, aşınma sayacını "kaç kez fonksiyon çağrıldı"ya çevirirdi.
    #   `best is None`   — kapıyı geçen aday varsa resmî kaydı `submit` düşürür (ship otoritesi aynı
    #                      kapıyı aynı K ile yeniden koşar); ikinci satır oturumu iki kez sayardı.
    oturum_kaydi = None
    if record_session and evaluated > 0 and best is None and rep_cand is not None:
        try:
            _gate_eval(inc, rep_cand, k_probes=total, record_erosion=True)
            oturum_kaydi = {"kaydedildi": True, "temsilci_oos": rep_oos, "k_probes": total}
        except Exception as e:
            # YASA 4: bir TELEMETRİ kaydının aramanın sonucunu düşürme yetkisi yoktur, ama sessiz de
            # kalamaz — kayıt düşerse aşınma sayacı O OTURUMU HİÇ görmez ve çıta olması gerekenden
            # gevşek kalır (yön: kapıyı gevşetir, yani sessizlik en pahalı seçenektir).
            oturum_kaydi = {"kaydedildi": False, "hata": type(e).__name__}
            try:
                from . import obs as _obs_s
                _obs_s.warn("search_session_record_failed", error=f"{type(e).__name__}: {e}",
                            evaluated=evaluated, k_probes=total,
                            detail="arama oturumunun TEK resmî kaydı yazılamadı — aşınma sayacı bu "
                                   "oturumu görmedi ve çıta olması gerekenden gevşek kaldı")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok ve kayıt denemesi arama sonucunu düşüremez
                pass
    return {"incumbent_oos": inc_oos, "evaluated": evaluated, "cleared": cleared,
            "fresh": _fresh_done, "cached_hits": evaluated - _fresh_done, "skipped_wallclock": _skipped_fresh,
            "best": best, "trace": trace[-40:], "regime": regime, "planlanan_sonda": total,
            # Ö-48 İZ ALANI (YASA 6 okuyucuları: `search_and_submit` sonucu `search` altında taşır,
            # ısınma log'u/pano aynı sözlüğü basar): [] = ölçüldü-temiz · [..] = süzülen anahtar
            # adları · None = okuyucu kümesi ölçülemedi (fail-open koşuldu, hiçbir anahtar süzülmedi).
            "hayalet_suzulen": hayalet_suzulen,
            # KAYDIN AKIBETİ SONUÇTA GÖRÜNÜR: `None` = bu oturum resmî kayıt düşürmedi (ya kapıyı
            # geçen aday `submit`e gitti, ya çağıran ship edemez, ya hiç sonda koşmadı). Alanın
            # yokluğu ile "yazılamadı" birbirine karışmasın diye her hâlde yazılır.
            "oturum_kaydi": oturum_kaydi,
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
    # RESMÎ KAYIT ZİNCİRİ: arama `record_session=True` (varsayılan) ile koşar. Kapıyı geçen aday
    # ÇIKARSA kaydı aşağıdaki `submit` düşürür (ship otoritesi, aynı kapı, aynı K); çıkmazsa aramanın
    # kendisi düşürür. İki dalın toplamı DEĞİŞMEZDİR: oturum başına TAM BİR resmî soru.
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
    """`reflect` CLI'ı: öneriyi ya `--hypothesis` JSON'undan (--hermes) ya da deterministik
    üreticiden alır, `submit()`e verir ve sonucu (statü, kapı, ret nedenleri) basar.

    Ship yolu yine `submit`tir — bu fonksiyon kapı yasasını atlatmaz, yalnız operatörün elle
    tetiklediği giriştir."""
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
