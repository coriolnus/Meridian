"""rollback.py — otomatik ebeveyn-dönüşü: kötüleşen sürüm insansız geri alınır, sonuç deftere işlenir.

Ne yapar: Canlı sürüm altında min_sample işlem birikince sürümü ebeveyniyle karşılaştırır. Fark
goal.rollback_if_worse_by eşiğinden kötüyse strategy.yaml ebeveyn anlık görüntüsüne döndürülür
(versioning.revert_to) ve ship eden hipotez rolled_back işaretlenir — ajan geri almayla tartışamaz,
yalnız sonradan değişikliğin neden başarısız olduğunu açıklar. Kötü değilse gerçekleşen delta +
calibration_hit hipoteze geri yazılır; eşiği aşan kalıcı bir kazanç promoted'a terfi eder.

Kilit girişler: `evaluate_outcomes(goal)` döngüyü SİMETRİK kapatan ana yol (geri al / tut / terfi;
idempotent, v01'de ve örneklem altında no-op); `check_and_rollback(goal, would_have)` negatif yarı
(revert + writeback + alarm); `sweep_orphan_hypotheses()` yeni ship'le aşılmış 'live' satırları
superseded'a taşır (defter sonsuza dek açık satır taşımasın). Karar girdisi `_karar_girdisi` ile
TEK yerde seçilir ve `karar_yontemi` damgasıyla kayda geçer: like_for_like_replay_v1 (ebeveyn
parametreleri çocuğun canlı döneminde replay edilir — baseline.would_have_replay; maliyet kapısı
gereği yalnız geri-alma adayı tetiklenince koşar) ya da legacy_scoreboard_oos (ölçülemeyen hâllerde
damgalı yedek — kaldırılmadı, çünkü kaldırmak veri kesintisinde geri-almayı sessizce dondururdu).

Değişmezler: gürültüyle asla geri alınmaz (min_sample tabanı); rejim ship'i yalnız o rejimin
işlem dilimiyle ölçülür — global karne skoru dilimli skorla karşılaştırılamaz (sahte delta);
geri alma başarısızlığı geri almanın kendisi kadar yüksek seslidir (alarm + elle müdahale çağrısı);
realized_delta BİLEŞİK skor biriminde kalır, para-ölçekli ikizi ölçülemiyorsa None + neden yazılır;
döngü kapanamıyorsa bu "kanıt bekliyorum"dan AYRI bir olaydır ve sayılır (learning_loop_open.json).
Okur: trades.jsonl, strategy.yaml, karne, hipotez defteri; yazar: karne satırları, hipotez
statüleri/sonuçları, lessons.md, açık-döngü kaydı."""
from __future__ import annotations
from typing import Optional

from . import config, store, memory, versioning, score as score_mod, obs


def _ship_eval_regime(version: int) -> str | None:
    """The regime slice the shipping hypothesis was GATE-graded on (var@regime → that regime), else None.
    The realized outcome must be measured on the SAME population the promise was made on — comparing a
    global live score against a regime-sliced gate score fabricates deltas (false promote/rollback)."""
    for h in reversed(memory.all_hypotheses()):
        if h.get("version_to") == version and h.get("status") in ("live", "promoted"):
            er = (h.get("backtest") or {}).get("eval_regime")
            if er:
                return er
            var = str(h.get("variable") or "")
            return var.split("@", 1)[1] if "@" in var else None
    return None


def _parent_score_fallback(version: int, par_score):
    """Reachability: when the parent has neither min_sample live trades NOR a scoreboard entry
    (e.g. the ledger was re-seeded under the child version), fall back to the incumbent OOS recorded in
    the SHIPPING hypothesis's gate — the exact score the child had to beat to go live. Without this,
    par_score stays None forever and the realized-outcome writeback (realized_delta, calibration_hit,
    market_regime telemetry) never fires for that version."""
    if par_score is not None:
        return par_score
    for h in reversed(memory.all_hypotheses()):
        if h.get("version_to") == version and isinstance(h.get("backtest"), dict):
            return h["backtest"].get("incumbent_oos")
    return None


def _market_regime(trades: list) -> str:
    """The distinct regime(s) the realized delta was MEASURED in (the eval window), '|'-joined —
    so we can audit whether a shipped change only helped in one market (bull/bear bias)."""
    regs = sorted({t.get("regime") for t in trades if t.get("regime")})
    return "|".join(regs) if regs else "unknown"


# ---- KARAR GİRDİSİ: LIKE-FOR-LIKE mi, ESKİ ASİMETRİK YOL mu? ---------------------
# Geri-alma kararının İKİ olası girdisi var ve hangisinin kullanıldığı KARAR KAYDINA damgalanır:
#   * `like_for_like_replay_v1` — ebeveyn parametreleri çocuğun canlı döneminde replay edildi;
#     iki taraf da `backtest.segment_score` ile AYNI pencerede puanlandı (bkz. baseline modülü).
#   * `legacy_scoreboard_oos` — would-have ölçülemedi (bar yok, anlık görüntü yok, örneklem altı);
#     eski (dönem+motor+yıllıklandırma ekseninde asimetrik) kıyas kullanıldı.
# İkinci yol KALDIRILMADI çünkü kaldırmak, bir veri kesintisinde geri-almayı SESSİZCE dondururdu —
# kötü bir sürüm canlıda kalır ve hiçbir yerde "karar verilemedi" yazmaz. Ama artık damgasız da
# değil: `karar_yontemi` alanı her kayıtta durur ve `legacy` damgalı bir geri alma, denetimde
# "bu karar zayıf kanıtla verildi" diye okunabilir.
LEGACY_YONTEM = "legacy_scoreboard_oos"


def _karar_girdisi(cur_score: float, par_score: float, wh: Optional[dict]) -> dict:
    """(çocuk, ebeveyn, delta, yöntem) — kararın DAYANDIĞI çift. Tek yerde seçilir ki
    `check_and_rollback` ile `evaluate_outcomes` iki farklı yasa uygulamasın (ikisi bugün de aynı
    hesabı iki kez yapıyor ve `test_rb1_a` tam olarak o ayrışma riski için var)."""
    if wh and wh.get("verdict") == "olculdu" and wh.get("delta") is not None:
        return {"cur": wh["canli_skor"], "par": wh["would_have_skor"], "delta": wh["delta"],
                "yontem": wh.get("yontem") or "like_for_like_replay_v1"}
    return {"cur": cur_score, "par": par_score, "delta": cur_score - par_score,
            "yontem": LEGACY_YONTEM}


# ---- PARA İKİZİ: GERÇEKLEŞMENİN İKİNCİ CETVELİ -------------------------------------------------
# NEDEN. `realized_delta` BİLEŞİK skordan (`score.score`) türer ve TÜREMEYE DEVAM EDER: geri-alma
# hükmü ve `goal.rollback_if_worse_by` eşiği o birimde kalibre edildi, birimi değiştirmek eşiği
# ölçümsüz değiştirmek olurdu. Ama `predicted_delta` PARA-v3 geçişinden beri `ret_c_v3` ölçeğinde
# yazılıyor (`reflect._gate_eval` → `conf.mean_delta`) ve `probgate.refresh_meta_calibration` bu iki
# sayıyı BÖLÜYORDU: para ÷ bileşik = birim karışımı (σ oranı ≈0,19 olduğundan oran ~5× şişerdi).
# Karışım ATLAMAYLA kapatıldı — ama atlama mekanizmayı MUHAFAZAKÂR yapmadı, ÖLDÜRDÜ:
# para_v3 altında hiçbir YENİ çift sayılamaz, `n_measured` META_MIN_N'e asla ulaşamaz, `extra_p`
# sonsuza dek 0 kalır; yani sistematik iyimserliği cezalandıran emniyet sessizce kapalıdır.
#
# BU BLOK O EMNİYETİ DİRİLTİR VE HÜKME DOKUNMAZ. Gerçekleşmenin PARA ölçeğindeki ikizi ÖLÇÜLÜR ve
# `realized_detail` içine yazılır (`memory.writeback_outcome` sözlüğü olduğu gibi saklar → hipotez
# şeması değişmez). Değişmeyenler: kapı kararı, geri-alma kararı, eşik, `realized_delta`ın kendisi.
#
# ÜÇ YOLDA ÖLÇÜLEMEZ VE ÜÇÜ DE ADIYLA YAZILIR (UYDURMA YASAĞI — None + neden):
#   (1) Karar LIKE-FOR-LIKE replay çiftinden geldiyse: o çiftin iki tarafı replay'in ÜRETTİĞİ işlem
#       listeleridir ve bu katmanda yokturlar. Elimizdeki canlı dilimlerden bir para farkı
#       hesaplamak KARARIN ikizini vermez — başka bir şeyin ikizini verir ve fark sessizce
#       başka bir soruyu cevaplardı.
#   (2) Ebeveyn skoru YEDEKten geldiyse (`par_trades` < min_sample → karne `live_score`/
#       `backtest_oos`, ya da kapı `incumbent_oos`): ebeveynin işlem listesi yok, para tarafı yok.
#   (3) `money_score` None döndüyse: bilinmeyen skor, sıfır skor gibi okunamaz.
#
# TEK PAYDA, İKİ TARAF: `hedef_pencere` span'e bağlıdır; her tarafı KENDİ span'iyle normalize etmek
# iki FARKLI paydayla bölmek olurdu — `probgate.py::PairedProbabilisticGate._score_pair`in "payda dilimin uzunluğuyla
# sabitlenir" kuralının aynısı. Span iki listenin BİRLEŞİMİNDEN türer ve kayda yazılır.
def _para_ikizi(cur_trades: list, par_trades: list, goal: dict, karar: dict,
                par_yedekten: bool) -> dict:
    """Gerçekleşen farkın PARA-v3 ölçeğindeki ikizi. ÖLÇER, HÜKÜM VERMEZ; hiçbir kapıya girmez."""
    ortak = {"birim": "PARA-v3 (shadowlaw.money_score / ret_c_v3)", "hukum_verir": False,
             "karar_yontemi": karar.get("yontem"),
             "kapsam": ("gerçekleşme tarafının İKİNCİ cetveli — `realized_delta` BİLEŞİK kalır ve "
                        "geri-alma hükmünü o vermeye devam eder")}
    bos = {**ortak, "olculdu": False, "delta_para": None, "cur_para": None, "par_para": None,
           "span_days": None}
    if karar.get("yontem") != LEGACY_YONTEM:
        return {**bos, "neden": ("karar LIKE-FOR-LIKE replay çiftinden geldi; o çiftin işlem "
                                 "listeleri bu katmanda YOK — canlı dilimlerden hesaplanacak bir "
                                 "para farkı KARARIN ikizi olmazdı")}
    if par_yedekten:
        return {**bos, "neden": ("ebeveyn skoru YEDEKten geldi (par_trades < min_sample) — "
                                 "ebeveynin işlem listesi yok, para tarafı ölçülemez")}
    from . import shadowlaw
    span = score_mod._span_days(list(cur_trades) + list(par_trades))
    cur_para = shadowlaw.money_score(cur_trades, goal, span_days=span)
    par_para = shadowlaw.money_score(par_trades, goal, span_days=span)
    if cur_para is None or par_para is None:
        return {**bos, "span_days": round(float(span), 1),
                "neden": (f"money_score ölçülemedi (cur={cur_para}, par={par_para}) — bilinmeyen "
                          f"skor sıfır sayılmaz")}
    return {**ortak, "olculdu": True, "delta_para": round(float(cur_para) - float(par_para), 6),
            "cur_para": cur_para, "par_para": par_para, "span_days": round(float(span), 1),
            "neden": None}


def _ikizi_yaz(detay: dict, cur_trades: list, par_trades: list, goal: dict, karar: dict,
               par_yedekten: bool) -> dict:
    """İkizi kayda koyar. `delta_para` ÜST DÜZEYdedir (tüketicisi `probgate` orada arar); ölçüm
    kaydının geri kalanı `para_ikizi` bloğunda durur — değer İKİ yerde tutulmaz ki ayrışamasın."""
    ikiz = _para_ikizi(cur_trades, par_trades, goal, karar, par_yedekten)
    detay["delta_para"] = ikiz["delta_para"]
    detay["para_ikizi"] = {k: v for k, v in ikiz.items() if k != "delta_para"}
    return detay


def _overturn_log(version: int, parent, ham_delta: float, karar: dict, wh: Optional[dict],
                  threshold: float) -> None:
    """SİMETRİK KIYAS GERİ ALMAYI ÇÜRÜTTÜ MÜ? Eski (asimetrik) kıyas "geri al" derken yenisi
    demiyorsa bu SESSİZ bir no-op olamaz: kararın yönünü değiştiren şey tam olarak bu turda yapılan
    ölçümdür ve defterde görünmelidir. İki karar yolundan da (evaluate_outcomes ve doğrudan
    check_and_rollback) aynı cümleyle yazılsın diye tek yerde durur."""
    if karar["yontem"] == LEGACY_YONTEM:
        return
    if ham_delta < -threshold <= karar["delta"]:
        obs.log("rollback_like_for_like_overturn", version=version, parent=parent,
                eski_delta=round(ham_delta, 4), karar_delta=round(karar["delta"], 4),
                karar_yontemi=karar["yontem"], would_have_skor=karar["par"],
                motor_sapmasi=(wh or {}).get("motor_sapmasi"),
                detail="eski asimetrik kıyas GERİ AL diyordu; ebeveynin aynı canlı döneme replay'i "
                       "farkı doğrulamadı — sürüm canlıda kalıyor")


def _would_have(version: int, parent, goal: dict, ereg: Optional[str]) -> Optional[dict]:
    """Would-have replay'i YALNIZ geri-alma adayı tetiklendiğinde koş (maliyet kapısı).

    İki tam replay (ebeveyn + çocuk kontrol bacağı) canlı dönem boyunca koşar; bunu her P5 turunda
    yapmak, kararın hiç değişmeyeceği yüzlerce turda boşuna CPU yakardı. Aday tetiklendiğinde ise
    maliyet kararın kendisinin yanında ihmal edilebilir."""
    if parent is None:
        return None
    try:
        from . import baseline
        return baseline.would_have_replay(int(version), int(parent), goal, eval_regime=ereg)
    except Exception as e:
        # YASA 4: sessizce eski yola düşmek, kıyasın simetrisini kaybettiğimizi gizlerdi.
        obs.warn("would_have_unavailable", error=f"{type(e).__name__}: {e}",
                 version=version, parent=parent,
                 detail="like-for-like kıyas kurulamadı — karar ESKİ asimetrik yola düşüyor")
        return None


def check_and_rollback(goal: Optional[dict] = None,
                       would_have: Optional[dict] = None) -> Optional[dict]:
    """Canlı sürümü ebeveyniyle kıyaslar ve eşiği aşan bir kötüleşme varsa GERİ ALIR.
    Ebeveyn yoksa, `min_sample` dolmamışsa ya da iki skordan biri ölçülemiyorsa None döner —
    gürültüyle geri alma YOKTUR. Geri alındığında karne/hipotez/dersler güncellenir, alarm ve
    bildirim yazılır; ebeveyn anlık görüntüsü yoksa sessizce geçilmez, alarm basılır.
    `would_have` verilmişse yeniden hesaplanmaz (iki replay = iki farklı karar riski)."""
    goal = goal or config.goal()
    strat = config.load_strategy()
    version = int(strat.get("version", 1))
    parent = strat.get("parent")
    if parent is None:
        return None  # v01 has nothing to roll back to

    trades = store.read_jsonl("trades.jsonl")
    ereg = _ship_eval_regime(version)            # regime ship → measure on that regime's trades only
    if ereg:
        trades = [t for t in trades if str(t.get("regime")) == ereg]
    cur_trades = [t for t in trades if t.get("strategy_version") == version]
    if len(cur_trades) < int(goal["min_sample"]):
        return None  # not enough evidence yet — never roll back on noise

    par_trades = [t for t in trades if t.get("strategy_version") == parent]
    # PARA İKİZİNİN ÖN KOŞULU: ebeveyn skoru işlemlerden mi, YEDEKten mi geldi?
    # Aşağıdaki yedek dallarından biri işlerse ebeveynin işlem listesi YOKTUR ve para tarafı
    # ölçülemez — bayrak burada, karar dallarından ÖNCE donar.
    _par_yedekten = len(par_trades) < int(goal["min_sample"])
    cur_score = score_mod.score(cur_trades, goal)
    par_score = score_mod.score(par_trades, goal) if len(par_trades) >= int(goal["min_sample"]) else None

    # Fall back to the scoreboard's recorded parent score (its own live period, else its backtest OOS).
    # NOT for regime ships: scoreboard values are GLOBAL-population scores — comparing them against a
    # regime-sliced cur_score is the exact population mismatch this patch removes. A regime ship's only
    # valid fallback is the shipping gate's own (identically-sliced) incumbent OOS.
    if par_score is None and not ereg:
        v = versioning.scoreboard().get("versions", {}).get(str(parent), {})
        par_score = v.get("live_score", v.get("backtest_oos"))
    par_score = _parent_score_fallback(version, par_score)   # last resort: the shipping gate's incumbent OOS
    if cur_score is None or par_score is None:
        return None

    threshold = float(goal["rollback_if_worse_by"])
    # KARAR ARTIK SİMETRİK ÇİFTTEN GELİR. `would_have` çağıran tarafından verildiyse YENİDEN
    # HESAPLANMAZ: `evaluate_outcomes` → `check_and_rollback` yolunda iki ayrı replay koşmak hem
    # pahalı hem de iki farklı sonuç (dolayısıyla iki farklı karar) üretme riski taşır.
    wh = would_have if would_have is not None else _would_have(version, parent, goal, ereg)
    karar = _karar_girdisi(cur_score, par_score, wh)
    if karar["delta"] < -threshold:
        try:
            versioning.revert_to(parent)
        except FileNotFoundError as e:
            # EBEVEYN ANLIK GÖRÜNTÜSÜ YOK: eskiden bu istisna döngüde
            # jenerik bir uyarıya dönüşüyordu ("evaluate_outcomes_failed") — yani kötü sürüm CANLI
            # kalıyor, geri alma sessizce başarısız oluyordu. Geri alma başarısızlığı, geri almanın
            # kendisi kadar yüksek sesli olmalı: operatör elle müdahale etmeli.
            obs.alarm(obs.ALARM_ROLLBACK,
                      f"GERİ ALMA BAŞARISIZ: v{version} kötü ama v{parent} anlık görüntüsü yok — "
                      f"kötü sürüm CANLI kalıyor, elle müdahale gerekli",
                      from_version=version, to_version=parent, error=str(e)[:160])
            return {"rolled_back_from": None, "attempted": version, "to": parent,
                    "error": "parent snapshot missing", "cur_score": cur_score, "par_score": par_score}
        # regime ships get a regime-annotated live score so the GLOBAL live_score baseline is never
        # polluted by a single-regime population (future children compare against clean baselines).
        versioning.update_scoreboard(version, rolled_back=True,
                                     **({f"live_score@{ereg}": cur_score} if ereg else {"live_score": cur_score}))
        versioning.update_scoreboard(parent, reinstated=True)
        mreg = _market_regime(cur_trades)
        # KAYITTA İKİ SKOR + YÖNTEM DAMGASI. `cur_score`/`par_score` alanları ANLAMLARINI KORUR
        # (ham canlı skor ve eski taban) — mevcut tüketiciler ve testler onları okuyor. Kararın
        # DAYANDIĞI çift ayrı adlarla (`karar_*`) yanlarına yazılır; ikisi ayrışıyorsa bu, denetimde
        # görülmesi gereken en önemli olgudur ve tek bir alana ezdirilemez.
        detay = {"cur_score": cur_score, "par_score": par_score,
                 "n": len(cur_trades), "market_regime": mreg,
                 "karar_yontemi": karar["yontem"], "karar_cur": karar["cur"],
                 "karar_par": karar["par"], "karar_delta": round(karar["delta"], 4)}
        if wh:
            detay["would_have"] = {k: wh.get(k) for k in
                                   ("verdict", "pencere", "would_have_skor", "canli_skor",
                                    "n_would_have", "n_canli", "cocuk_replay_skor",
                                    "motor_sapmasi", "neden")}
        _ikizi_yaz(detay, cur_trades, par_trades, goal, karar, _par_yedekten)
        hyp = memory.writeback_outcome(version, realized_delta=karar["delta"],
                                       realized_detail=detay)
        if hyp:
            memory.update_status(hyp["id"], "rolled_back",
                                 realized_delta=round(karar["delta"], 4), market_regime=mreg)
        memory.distill_lessons()
        obs.alarm(obs.ALARM_ROLLBACK,
                  f"v{version} → v{parent} underperformed by {round(karar['par'] - karar['cur'], 4)} "
                  f"({karar['yontem']})",
                  from_version=version, to_version=parent, cur_score=cur_score, par_score=par_score,
                  karar_yontemi=karar["yontem"], karar_cur=karar["cur"], karar_par=karar["par"],
                  would_have_skor=(wh or {}).get("would_have_skor"),
                  motor_sapmasi=(wh or {}).get("motor_sapmasi"))
        try:
            from . import notify
            notify.rollback(version, parent, karar["delta"])
        except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
            pass
        return {"rolled_back_from": version, "to": parent, "cur_score": cur_score,
                "par_score": par_score, "delta": round(karar["delta"], 4),
                "karar_yontemi": karar["yontem"], "karar_cur": karar["cur"],
                "karar_par": karar["par"], "would_have": wh}
    _overturn_log(version, parent, cur_score - par_score, karar, wh, threshold)
    return None


OPEN_LOOP_FILE = "learning_loop_open.json"


def _open_loop(reason: str, **fields) -> None:
    """Öğrenme döngüsü kapanamadı — SÖYLE ve SAY. Log satırı her turda tekrarlanmasın diye durum
    dosyada birikir; makullük dedektörü toplamı okur (üretilip tüketilmeyen kanıt olmasın)."""
    from . import obs
    prev = store.read_json(OPEN_LOOP_FILE, {}) or {}
    if prev.get("reason") != reason:
        obs.warn("learning_loop_open", reason=reason, **fields,
                 detail="öğrenme döngüsü KAPANMIYOR — hiçbir hipotez terminale ulaşmaz, "
                        "kalibrasyon beslenmez. 'kanıt bekleniyor' ile karıştırılmamalı.")

    def _bump(d):
        """Açık-döngü durum dosyasının yamacı: nedeni yazar, sayacı bir artırır, alanları ve son damgayı tazeler."""
        d["reason"] = reason
        d["n"] = int(d.get("n", 0)) + 1
        d.update({k: v for k, v in fields.items()})
        d["last"] = memory.now_iso()
        return True

    store.update_json(OPEN_LOOP_FILE, _bump, {})


def _no_parent_diagnostics(version: int, parent) -> dict:
    """DÖNGÜ NEDEN ÖLÇEMİYOR — ÖLÇÜLEN OLGULAR, ATIF DEĞİL.

    Kayıt eskiden yalnız n_cur/n_par taşıyordu; "kanıt bekliyorum" ile "ölçemiyorum" ayrıldı ama
    ÖLÇEMEYİŞİN SEBEBİ hâlâ görünmüyordu. Suçu tek bir sebebe sabitlemek de yanlış olurdu: canlı
    kanıt bunu çürütür — v3 kapıdan GEÇTİ (H00029, gate_law=probabilistic) ve yine de taban
    üretmedi, çünkü OOS dilimlerinin ikisinde SIFIR işlem vardı, üçüncüsü de min_sample'ın altında
    kaldı → `score()` None döndü. Yani kuraklık bir örneklem büyüklüğü sorunu, salt bir soyağacı
    kopukluğu değil. Burada yalnız DOĞRUDAN SAYILABİLİR olgular yazılır; teşhisi okuyan kurar."""
    vers = (versioning.scoreboard().get("versions") or {})
    prow = vers.get(str(parent))
    ship = [h for h in memory.all_hypotheses() if h.get("version_to") == version]
    out = {"parent_row_exists": prow is not None,
           "parent_row_has_score": bool(prow and (prow.get("live_score") is not None
                                                  or prow.get("backtest_oos") is not None)),
           "ship_hypothesis_exists": bool(ship)}
    if ship:
        # Kapıdan geçmiş olmak taban ÜRETTİĞİ anlamına gelmez: incumbent_oos None ise kapı da
        # karşılaştırılabilir bir sayı yazmamıştır. Bugün v3'te durum tam olarak budur.
        out["ship_gate_incumbent_oos"] = (ship[-1].get("backtest") or {}).get("incumbent_oos")
    if prow and prow.get("baseline_verdict"):
        # `baseline.measure_parent_baseline` ebeveyni ÖLÇTÜYSE hükmü buraya taşınır: "hiç ölçülmedi"
        # ile "ölçüldü ama karşılaştırılamaz çıktı" bambaşka iki teşhistir ve ikincisinde yapılacak
        # şey bellidir (örneklem biriktir ya da frekansı hizala), belirsizlik değil.
        out["baseline_verdict"] = prow["baseline_verdict"]
        if prow.get("baseline_freq_ratio") is not None:
            out["baseline_freq_ratio"] = prow["baseline_freq_ratio"]
    return out


def _close_loop() -> None:
    """Döngü kapandı — açık-döngü kaydı silinir (bayat kırmızı bırakma)."""
    if store.read_json(OPEN_LOOP_FILE, None):
        store.write_json(OPEN_LOOP_FILE, {})


def sweep_orphan_hypotheses() -> list:
    """YETİM HİPOTEZ SÜPÜRMESİ. `evaluate_outcomes` yalnız GÜNCEL sürüme
    bakar. v2 min_sample'a ulaşmadan v3 ship edilirse, v2'nin hipotezi `live` durumunda SONSUZA
    KADAR kalır — sonradan 46 işlem biriktirse bile. Canlı kanıt: H00029 (v2→v3, live,
    realized_delta yok) ve H00026 (ölçülmüş -0.0364 ama terminale hiç ulaşmamış).

    Süpürme yalnız SÜPERSEDED olanları kapatır: `version_to` güncel sürümden küçükse o hipotezin
    hükmü bitmiştir. Ölçülmüş bir delta varsa korunur; yoksa 'ölçülemeden aşıldı' diye kapanır."""
    cur = int(config.load_strategy().get("version", 1))
    kapanan = []
    for h in memory.all_hypotheses():
        if h.get("status") != "live":
            continue
        vt = h.get("version_to")
        if vt is None or int(vt) >= cur:
            continue
        memory.update_status(h["id"], "superseded",
                             note=f"v{vt} v{cur} tarafından aşıldı — hüküm bitti"
                                  + ("" if h.get("realized_delta") is not None
                                     else " (gerçekleşen delta ölçülemeden)"))
        kapanan.append(h["id"])
    if kapanan:
        from . import obs
        obs.log("orphan_hypotheses_swept", ids=kapanan, current_version=cur,
                detail="süperseded `live` hipotezler terminale taşındı — defter artık sonsuza kadar "
                       "açık satır taşımıyor")
    return kapanan


def evaluate_outcomes(goal: Optional[dict] = None) -> Optional[dict]:
    """Close the learning loop SYMMETRICALLY — this is the piece that was missing (nobody called
    check_and_rollback, so no version ever got a realized_delta → calibration stayed n=0 forever and the
    autonomy ladder's 'predictions held up' gate was unreachable). Once the live version has min_sample
    trades: if it underperforms its parent, roll it back; if it holds up or beats it, write the realized
    delta + calibration_hit back onto the shipping hypothesis, and PROMOTE (live→promoted) a clear win.
    Idempotent and no-ops on v01 or below min_sample."""
    goal = goal or config.goal()
    strat = config.load_strategy()
    version = int(strat.get("version", 1))
    parent = strat.get("parent")
    if parent is None:
        return None
    trades = store.read_jsonl("trades.jsonl")
    ereg = _ship_eval_regime(version)            # regime ship → measure on that regime's trades only
    if ereg:
        trades = [t for t in trades if str(t.get("regime")) == ereg]
    cur_trades = [t for t in trades if t.get("strategy_version") == version]
    if len(cur_trades) < int(goal["min_sample"]):
        return None
    par_trades = [t for t in trades if t.get("strategy_version") == parent]
    _par_yedekten = len(par_trades) < int(goal["min_sample"])   # para ikizinin ön koşulu (bkz. _para_ikizi)
    cur_score = score_mod.score(cur_trades, goal)
    par_score = score_mod.score(par_trades, goal) if len(par_trades) >= int(goal["min_sample"]) else None
    if par_score is None and not ereg:           # scoreboard scores are GLOBAL — invalid vs a sliced cur
        v = versioning.scoreboard().get("versions", {}).get(str(parent), {})
        par_score = v.get("live_score", v.get("backtest_oos"))
    par_score = _parent_score_fallback(version, par_score)   # last resort: the shipping gate's incumbent OOS
    if cur_score is None or par_score is None:
        # DÖNGÜ AÇIK KALDI. Eskiden burada sessizce
        # `return None` vardı ve "kanıt bekliyorum" ile "ÖLÇEMİYORUM" aynı görünüyordu. CANLI KANIT:
        # v4'ün ebeveyni yok, ebeveyn satırı da karnede yok → `par_score=None` → döngü HER TURDA
        # sessizce kapanıyordu. Ajan meşgul görünüyor ve hiç öğrenmiyor; hiçbir hipotez terminale
        # ulaşmıyor; kalibrasyon n=0 kalıyor. Artık bu bir OLAYDIR ve makullük dedektörü görür.
        _open_loop("no_parent_score" if par_score is None else "no_current_score",
                   version=version, parent=parent, n_cur=len(cur_trades), n_par=len(par_trades),
                   **(_no_parent_diagnostics(version, parent) if par_score is None else {}))
        return None
    _close_loop()                      # ölçüm yapılabildi: bayat 'açık döngü' kaydı kalkar
    ham_delta = cur_score - par_score
    threshold = float(goal["rollback_if_worse_by"])
    # MALİYET KAPISI: like-for-like replay YALNIZ aday tetiklendiğinde koşar. Ham (asimetrik) delta
    # burada bir TETİKLEYİCİdir, karar değil — kararı simetrik kıyas verir. Tetikleyicinin kendisi
    # asimetrik kalabilir çünkü işlevi "bakmaya değer mi?" sorusunu cevaplamak; yanlış pozitifi
    # pahalıdır ama zararsızdır (bir replay koşar ve karar çürütülür), yanlış negatifi ise eski
    # davranışla birebir aynıdır.
    wh = _would_have(version, parent, goal, ereg) if ham_delta < -threshold else None
    karar = _karar_girdisi(cur_score, par_score, wh)
    delta = karar["delta"]
    # Çürütme BU yolda da görünür olmalı: aşağıdaki dal `check_and_rollback`i hiç çağırmadan
    # "sürüm iyi" koluna geçer, yani oradaki kayıt bu turda asla yazılmazdı.
    _overturn_log(version, parent, ham_delta, karar, wh, threshold)
    if delta < -threshold:
        # Ölçülmüş would-have AŞAĞI taşınır: aynı turda ikinci bir replay koşmak hem pahalı hem de
        # iki farklı sonuç üretebilirdi (idempotans testinin koruduğu tam olarak bu).
        return check_and_rollback(goal, would_have=wh)            # negative half (revert + writeback)
    # non-worse: record the realized outcome (the positive/neutral half that never existed)
    versioning.update_scoreboard(version, **({f"live_score@{ereg}": cur_score} if ereg
                                             else {"live_score": cur_score}))
    mreg = _market_regime(cur_trades)
    detay = {"cur_score": cur_score, "par_score": par_score,
             "n": len(cur_trades), "market_regime": mreg, "eval_regime": ereg,
             "karar_yontemi": karar["yontem"], "karar_cur": karar["cur"],
             "karar_par": karar["par"], "karar_delta": round(delta, 4)}
    if wh:
        detay["would_have"] = {k: wh.get(k) for k in
                               ("verdict", "pencere", "would_have_skor", "canli_skor",
                                "n_would_have", "n_canli", "cocuk_replay_skor",
                                "motor_sapmasi", "neden")}
    _ikizi_yaz(detay, cur_trades, par_trades, goal, karar, _par_yedekten)
    hyp = memory.writeback_outcome(version, realized_delta=delta, realized_detail=detay)
    if hyp and hyp.get("status") == "live":
        memory.update_status(hyp["id"], "live", market_regime=mreg)   # tag eval-window regime even on a neutral hold
    promoted = False
    if delta > threshold and hyp and hyp.get("status") == "live":   # a durable win earns promotion
        memory.update_status(hyp["id"], "promoted", realized_delta=round(delta, 4), market_regime=mreg)
        versioning.update_scoreboard(version, promoted=True)
        promoted = True
    memory.distill_lessons()
    return {"version": version, "parent": parent, "cur_score": cur_score, "par_score": par_score,
            "delta": round(delta, 4), "promoted": promoted, "rolled_back": False,
            "karar_yontemi": karar["yontem"], "karar_cur": karar["cur"], "karar_par": karar["par"]}
