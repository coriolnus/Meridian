"""guard.py — the real constraint layer. An instruction to an LLM is a suggestion; a validator is
a constraint (Hard Rule 6). Every rule stated to Hermes is enforced here.

Two surfaces:
  validate_change(proposal, ...) — static validation of a parameter hypothesis (no backtest)
  check_trade(plan, portfolio, regime, goal) — runtime risk-envelope check for a would-be entry
Every rejection carries a machine-readable reason and is written back by memory.py."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from . import config

# Names that are immutable to Hermes. Touching any of these is an automatic reject.
GOAL_KEYS = {"schema_version", "universe", "style", "session_tz", "target_return_30d", "min_sharpe",
             "max_drawdown", "failure_below", "reflection_every", "min_sample", "one_variable_only",
             "backtest_gate", "rollback_if_worse_by", "explore_rate", "max_accepted_changes_per_month",
             "commission_per_share", "slippage_bps", "fill",
             # WP-E (2026-07-31): giriş İCRA yasası ve kötümser maliyet bandı goal.yaml'a girdi ve
             # ikisi de DEĞİŞMEZ olmak ZORUNDA — icra yasası bir arama değişkeni olsaydı ajan kendi
             # dolum fiyatını, maliyet bandı düğme olsaydı kendi karnesinin paydasını seçerdi.
             # GU1 sürüklenme testi (test_guard_audit_v27) bu iki adı burada görmezse kırmızı yanar.
             "execution_v2", "pessimistic_band_v2"}
LIMIT_KEYS = {"autonomy_level", "max_position_r", "max_open_positions", "max_daily_loss_pct",
              "max_sector_exposure_pct", "no_trade_before_bars", "kill_switch_file",
              # C24 (denetim 2026-08-02): portföy-ısısı ve korelasyon eşikleri KOD SABİTİYDİ — ne
              # operatörün değişmez zarfında (goal.yaml) ne arama uzayında (bounds.yaml). Yani
              # canlı defterde plan kesen bir risk eşiği HİÇBİR yönetişim yüzeyinde görünmüyordu
              # (adı konmuş sınıfın ikinci örneği: `broker.max_positions_at` rampası). Üçü de
              # goal.yaml `limits`e OPERATÖR KALEMİ olarak indi: Hermes öneremez (bu liste), arama
              # göremez (bounds'ta yok), operatör tek satırla değiştirir. DEĞERLER KORUNDU.
              "heat_hard_r", "heat_review_r", "corr_review"}

# --- CANLI MOTORUN OKUYAMADIĞI KNOB SINIFI (C13b, 2026-08-02) ------------------------------------
# Bir knob replay/gölgede ÖLÇÜLÜR ama canlı motorda yapısal olarak hiçbir şey yapmazsa, terfi yolu
# ölçülmemiş bir ΔS'i kazanç sayar: aday kapıdan geçer, strategy.yaml'a iner, canlıda SESSİZ NO-OP
# olur ve `rollback.evaluate_outcomes` gerçekleşmeyen tahmini o değişkenin suçu gibi deftere yazar.
# `validate_change` bu sınıfı `regime.*@regime` için ADIYLA reddediyordu ama SINIF korumasızdı —
# `exit.early_kill_pivot` (denetim C13) tam bu deliğe oturmuştu.
#
# LİSTE BUGÜN BOŞ VE BOŞ OLMASI DOĞRUDUR: pivot kablosu 2026-08-02'de canlıya bağlandı
# (`loop.fill_entry(pivot=…)` + `manage_position` sözlüğünde `pivot`). Bu dal İKİNCİ savunma
# hattıdır; BİRİNCİ hat motor-eşitliği çivisidir (tests/test_kovab_ikimotor_v164: üç motorun
# yönetim-sözlüğü alan kümesi EŞİT, yani yeni bir ayrışma adsız yakalanır). Birinci hat kırmızı
# yandığında knob buraya ADIYLA + GEREKÇEYLE yazılır ve terfi yolu aynı turda kapanır.
LIVE_DEAD_KNOBS: dict[str, str] = {
    # "exit.early_kill_pivot": "canlı fill_entry pivot geçirmiyor, manage_position sözlüğünde pivot yok",
}


@dataclass
class Verdict:
    ok: bool
    reasons: list
    variable: Optional[str] = None
    old: Optional[float] = None
    new: Optional[float] = None


def _on_step(new, lo, step, typ, tol=1e-6) -> bool:
    k = round((new - lo) / step)
    nearest = lo + k * step
    if typ == "int":
        return abs(nearest - new) < tol and float(new).is_integer()
    return abs(nearest - new) <= tol * max(1.0, abs(step))


COMPOSITE_MAX_KNOBS = 3    # bkz. hermes_composite: 5 düğmelik demet hipotez değil yeniden yazımdır


def composite_shape_reasons(composite: dict, bounds: dict) -> list:
    """Bileşik demetin ŞEKİL hükmü — SAF fonksiyon (defter yok, ağ yok, yan etki yok).

    Bileşik olmak bir düğmeyi bounds dışına çıkarma ruhsatı DEĞİLDİR: her düğme ayrı ayrı aralık +
    adım + tip denetiminden geçer ve biri düşerse ADAYIN TAMAMI düşer (prescreen'in bileşik kuralı
    (1) ile birebir aynı yasa — iki yerde iki farklı şekil denetimi olsaydı kuyruğa giren ile
    ölçülen aday ayrışırdı)."""
    nedenler = []
    if not isinstance(composite, dict) or not composite:
        return ["composite boş ya da sözlük değil"]
    if len(composite) < 2:
        nedenler.append("composite tek düğme taşıyor — bileşik değil, normal hipotez yolunu kullan")
    if len(composite) > COMPOSITE_MAX_KNOBS:
        nedenler.append(f"composite {len(composite)} düğme taşıyor; tavan {COMPOSITE_MAX_KNOBS}")
    for k, v in composite.items():
        b = bounds.get(str(k).split("@", 1)[0])
        if b is None:
            nedenler.append(f"{k}: bounds'ta tanımlı değil")
            continue
        try:
            val = float(v)
        except (TypeError, ValueError):  # sessiz-yutma: sessiz DEĞİL — neden listeye YAZILIR ve aday reddedilir (istisna yalnız akış kontrolü)
            nedenler.append(f"{k}: sayı değil ({v!r})")
            continue
        if val < float(b["min"]) or val > float(b["max"]):
            nedenler.append(f"{k}={val}: sınır dışı [{b['min']}, {b['max']}]")
        elif not _on_step(val, float(b["min"]), float(b["step"]), b.get("type")):
            nedenler.append(f"{k}={val}: adım üstünde değil (step={b['step']})")
    return nedenler


def validate_change(proposal: dict, current_params: dict, bounds: dict, goal: dict,
                    hypotheses: list, accepted_this_month: int,
                    params_by_regime: dict | None = None) -> Verdict:
    """Validate a single-variable parameter proposal. Does NOT run the backtest — that is the
    separate gate. `proposal` = {variable, new, ...}. params_by_regime: the live strategy's regime
    overrides, so a base@regime no-op check compares against the regime-EFFECTIVE value (an override
    reverting to the flat value IS a real behavior change in that regime, not a no-op)."""
    reasons = []

    # --- H3: BİLEŞİK ÖNERİ — TEK-DEĞİŞKEN YASASI ONU REDDETMEZ, KUYRUĞA YÖNLENDİRİR -------------
    # Tek-değişken yasası bir ÖLÇÜM kuralıdır, bir yasak değil (bkz. prescreen --composite). Eskiden
    # hermes bileşik bir fikir ürettiğinde guard onu "more than one variable" diye çöpe atıyordu ve
    # fikir kayboluyordu — ölçülmemiş bir kayıp. Artık yol açık ama YETKİ AÇILMADI: dönüş yine
    # ok=False'tur (bu öneri CANLIYA GİRMEZ), yalnız nedeni `composite_pending_queue`dur.
    #
    # GUARD KUYRUĞA YAZMAZ — YAZDIRMAZ DA. İlk yazımda buradan `hermes_composite.enqueue` çağrılmıştı
    # ve `test_gate_statistics_v74` haklı olarak kırmızıya döndü: guard'ın SERT ZARF yasası, bu
    # modülün SAF olmasını (verdict yalnız argümanlarının fonksiyonu, hiçbir defter/LLM/ağ kanalı
    # yok) çiviliyor. Bir defter yazımı tam olarak o kanaldır. Bu yüzden guard yalnız ŞEKİL hükmü
    # verir; kuyruğa yazma işini ÇAĞIRAN yapar (`memory.record_hypothesis` yolu). Ship yolu
    # değişmedi: prescreen ölçer → kapı karar verir → operatör onaylar.
    comp = proposal.get("composite")
    if isinstance(comp, dict) and comp:
        nedenler = composite_shape_reasons(comp, bounds)
        if nedenler:
            return Verdict(False, ["composite_rejected_shape: " + "; ".join(nedenler)])
        return Verdict(False, [f"composite_pending_queue: {len(comp)} düğme prescreen ölçüm "
                               f"kuyruğuna YÖNLENDİRİLDİ; tek-değişken yasası KALDIRILMADI, canlı "
                               f"değişiklik YAPILMADI"])

    # --- shape: exactly one variable ---
    if "changes" in proposal and isinstance(proposal["changes"], dict):
        if len(proposal["changes"]) != 1:
            return Verdict(False, [f"more than one variable changed ({len(proposal['changes'])}); one_variable_only"])
        variable, new = next(iter(proposal["changes"].items()))
    else:
        variable = proposal.get("variable")
        new = proposal.get("new")
    if variable is None or new is None:
        return Verdict(False, ["proposal missing variable/new"])

    # --- regime-conditional knob 'base@regime': tune one variable, in one regime, still one variable ---
    base, regime = variable, None
    if "@" in variable:
        base, regime = variable.split("@", 1)
        if regime not in config.VALID_REGIMES:
            return Verdict(False, [f"unknown regime '{regime}' (must be one of {config.VALID_REGIMES})"],
                           variable=variable)
        # resolve_params overlays ONLY keys present in flat params — an override for a base knob missing
        # from strategy.yaml's params would be silently DROPPED by both the backtest replay and the live
        # loop: candidate == incumbent, the gate rejects, and the ledger records a false dead end for a
        # value that was never actually simulated. Reject honestly instead.
        if base not in current_params:
            return Verdict(False, [f"'{base}' is not in the live strategy params — a @{regime} override "
                                   f"would be silently ignored (add the base knob first)"], variable=variable)
        if base.startswith("regime."):
            # regime detection runs BEFORE the regime is known — build_regime_json consumes FLAT params
            # in both engines, so a regime.* override can never take effect: the candidate replays
            # byte-identical to the incumbent, the gate rejects, and a false permanent dead end lands in
            # the ledger (audit #33). Reject honestly instead.
            return Verdict(False, [f"'{base}' rejim tespitinin kendisini besler — rejim bilinmeden çalışır, "
                                   f"@{regime} override'ı yapısal olarak etkisizdir"], variable=variable)

    # --- immutability: goal.yaml / bounds.yaml / limits block ---
    if base in GOAL_KEYS or base in LIMIT_KEYS or base.startswith("limits.") \
            or base in ("goal", "bounds"):
        return Verdict(False, [f"'{base}' is immutable (goal/limits block); Hermes may not propose it"],
                       variable=variable)

    # --- canlı motorun OKUYAMADIĞI knob: yapısal etkisizlik (C13b) — regime.* dalının İKİZİ -------
    # Buradaki ret, yukarıdaki `regime.*@regime` reddiyle AYNI gerekçeye dayanır ve aynı zararı
    # önler: replay ΔS ölçer, kapı kabul eder, canlı uygulayamaz → defterde SAHTE kazanç ya da
    # SAHTE kalıcı çıkmaz sokak. Fark, o reddin YALNIZ @regime son ekiyle gelen öneriyi kapatması,
    # bunun DÜZ öneriyi de kapatmasıdır (C13'ün kaçtığı tek yol düz öneriydi).
    if base in LIVE_DEAD_KNOBS:
        return Verdict(False, [f"'{base}' canlı motorda YAPISAL olarak ölü ({LIVE_DEAD_KNOBS[base]}) — "
                               f"replay/gölge ΔS ölçer, canlı uygulayamaz; kablo bağlanmadan terfi "
                               f"edilirse defterde ölçülmemiş bir kazanç kalır"], variable=variable)

    # --- must be a tunable in bounds.yaml ---
    if base not in bounds:
        return Verdict(False, [f"'{base}' is not a tunable variable in bounds.yaml"], variable=variable)

    spec = bounds[base]
    lo, hi, step, typ = spec["min"], spec["max"], spec["step"], spec["type"]

    # --- SAYIYA ÇEVRİLEBİLİR Mİ (2026-07-22, öğrenme-döngüsü denetimi) ---
    # `float("abc")` ValueError atıyordu ve `submit` bunu genel bir `except`'e düşürüyordu: HİÇBİR
    # defter satırı yazılmıyordu. Oysa bu deponun yasası "değerlendirilen her öneri KAYITLI bir
    # terminale ulaşır". Çöp değer artık istisna değil, GEREKÇELİ RET olur.
    try:
        _num = float(new)
    except (TypeError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR — dönen Verdict gerekçesiyle birlikte defterde terminal bir satır olur; istisna atmak tam tersine hiçbir kayıt bırakmıyordu
        return Verdict(False, [f"{variable}={new!r} sayı değil (reddedildi, çökme değil)"],
                       variable=variable)
    # NaN aralık kontrolünü SESSİZCE geçiyordu: `nan < lo` ve `nan > hi` ikisi de False. Yalnız adım
    # kontrolü tesadüfen çöküyordu — yani NaN'ı yakalayan şey bir hataydı, bir kural değil.
    if _num != _num or _num in (float("inf"), float("-inf")):
        return Verdict(False, [f"{variable}={new!r} sonlu bir sayı değil (NaN/sonsuz)"],
                       variable=variable)

    # --- type ---
    if typ == "int" and not _num.is_integer():
        reasons.append(f"{variable}={new} must be int")
    new = int(_num) if typ == "int" else _num

    # --- range ---
    if new < lo or new > hi:
        reasons.append(f"{variable}={new} out of range [{lo}, {hi}]")
    # --- step ---
    elif not _on_step(new, lo, step, typ):
        reasons.append(f"{variable}={new} off-step (step={step} from {lo})")

    if regime is not None:
        # regime-EFFECTIVE old: the override when one exists, else the flat value (that IS what the
        # regime trades under). Comparing against flat-only made reverting a bad override a guard-level
        # "no-op" — an unrevertable override and a search/ship-authority disagreement.
        old = ((params_by_regime or {}).get(regime) or {}).get(base, current_params.get(base))
    else:
        old = current_params.get(base)

    # --- no-op ---
    if old is not None and not reasons and _equalish(old, new, typ):
        reasons.append(f"{variable} no-op: already {old}")

    # --- already-failed identical change ---
    for h in hypotheses:
        if h.get("variable") == variable and _equalish(h.get("new"), new, typ) \
                and h.get("status") in ("rejected_by_backtest", "rolled_back"):
            reasons.append(f"{variable}={new} already tried and failed (hyp {h.get('id')}, {h.get('status')})")
            break

    # --- monthly accepted-change quota ---
    quota = int(goal.get("max_accepted_changes_per_month", 8))
    if accepted_this_month >= quota:
        reasons.append(f"monthly accepted-change quota spent ({accepted_this_month}/{quota})")

    if reasons:
        return Verdict(False, reasons, variable=variable, old=old, new=new)
    return Verdict(True, [], variable=variable, old=old, new=new)


def _equalish(a, b, typ) -> bool:
    if a is None or b is None:
        return False
    if typ == "int":
        return int(a) == int(b)
    return abs(float(a) - float(b)) < 1e-9


# --------- runtime trade-envelope guard ---------
@dataclass
class TradeVerdict:
    ok: bool
    reasons: list


def check_trade(plan: dict, portfolio: dict, regime: dict, goal: dict) -> TradeVerdict:
    """Sert risk zarfı — TEK YASA, tek uygulama.

    DENETİM 2026-07-21 (tur 12): bu fonksiyon zarfın İKİNCİ bir kopyasını taşıyordu ve docstring'i
    "canlı döngü bunu kullanır" diyordu — ikisi de artık doğru DEĞİLDİ. Canlı döngü, backtest ve
    cf_backfill'in üçü de classify_gate çağırıyor; classify_gate ise zamanla R:R tabanını ve
    portföy-ısısı tavanını SERT kurala çevirmişti. Yani iki yüzey sessizce ayrışmıştı: buradaki
    kopya, canlıda NO_GO olan planlara "geçti" diyordu. Kimse fark etmedi çünkü kimse kıyaslamadı.

    Kopyayı silmek yerine TÜRETİYORUZ: sert kural listesi tek yerde (classify_gate) yaşıyor, bu
    yüzey onun sonucunu döndürüyor. Böylece ayrışma yapısal olarak imkânsız — ileride bir kural
    eklenirse iki yüzey de aynı anda öğrenir."""
    verdict, reasons = classify_gate(plan, portfolio, regime, goal)
    extra = []
    if goal["limits"]["autonomy_level"] < 1 and config.live_enabled():
        extra.append("live mode requested but autonomy_level<1 — refused")
    if verdict == "NO_GO":
        return TradeVerdict(False, list(reasons) + extra)
    return TradeVerdict(not extra, extra)


# --------- three-state discipline gate: GO / REVIEW / NO_GO (matches the product design) ---------
DISCIPLINE_MIN_RR = 2.0        # pre-trade-discipline-gate R:R floor — a HARD veto (R:R now varies per plan)
REVIEW_RR_BAND = 0.3           # R:R below floor+band -> REVIEW (marginal)
REVIEW_SCORE_BAND = 10         # score within this of entry.min_score -> REVIEW
# ÜÇ EŞİK ARTIK OPERATÖR KALEMİDİR (C24, 2026-08-02) — buradakiler YALNIZ FAIL-SAFE VARSAYILANDIR.
# Kanonik kaynak `goal.yaml`ın `limits` bloğudur ve `classify_gate` onu ORADAN okur; anahtar yoksa
# bu değerlere düşer, yani eski goal.yaml'lı bir kopya (ya da elle kurulmuş bir goal sözlüğü taşıyan
# test) davranış DEĞİŞTİRMEDEN koşar. TAŞIMA turu bir yönetişim turuydu, eşik turu değil: değerler
# 4,5 / 3,5 / 0,85 olarak KORUNMUŞTU. `heat_hard_r` o günden BERİ değişti — OPERATÖR KARARI
# 2026-08-03 (d01ccb5) onu 4,5→5,0R'ye taşıdı (ilan edilen zarfa eşitleme); aşağıdaki fail-safe de
# aynı karara göre güncellendi (7e99eff). Diğer ikisi taşındıkları gibi durur.
HEAT_REVIEW_R = 3.5            # total open risk (R) above this -> REVIEW (book getting concentrated)
HEAT_HARD_R = 5.0             # OPERATÖR KARARI 2026-08-03 (d01ccb5): zarf aritmetiğine eşitlendi; fail-safe = operatör değerinin yedeği (eşitlik çivisi v166-c24)
CORR_REVIEW = 0.85           # candidate return-correlation with a held name above this -> REVIEW


def classify_gate(plan: dict, portfolio: dict, regime: dict, goal: dict, params: dict | None = None,
                  detail_out: list | None = None):
    """Return (verdict, reasons) where verdict ∈ {GO, REVIEW, NO_GO}.
    NO_GO = a hard risk breach — the plan never reaches the broker (== the old check_trade 'reject').
    REVIEW = passes every hard rule but carries a soft flag a human should eyeball (== a flagged GO).
    GO = clean. At L0 both GO and REVIEW trade autonomously; at L1 both wait for approval; NO_GO never trades.

    BU FONKSİYON SERT ZARFIN TEK KAYNAĞIDIR (denetim turu 12, 2026-07-21). Eskiden bu docstring
    "sert kurallar eski check_trade zarfının aynısı" diyordu; artık DEĞİL — R:R tabanı ve portföy-ısısı
    sert tavanı sonradan HARD'a çevrildi ve check_trade'deki kopya geride kaldı. check_trade şimdi bunu
    çağırıyor, dolayısıyla iki yüzeyin ayrışması yapısal olarak imkânsız.

    R:R neden artık SERT: r_multiple_expected plan başına DEĞİŞİYOR (ölçülü-hareket hedefi) ve
    exit.profit_target_r'nin alt sınırı (2.0) tavanı tabanın üstünde tutuyor — yani sığ-bazlı düşük
    ödüllü kurulumları eliyor, tüm işlemi sıfırlayamıyor. (Eski gerekçe: her plan aynı R:R'yi
    taşırken sert taban, Hermes profit_target_r'yi düşürdüğünde TÜM işlemi durdururdu.)"""
    limits = goal["limits"]
    # C24: ısı/korelasyon eşikleri OPERATÖR ZARFINDAN gelir; anahtar yoksa modül varsayılanı
    # (fail-safe — eski bir goal.yaml ya da elle kurulmuş goal sözlüğü davranışı değiştirmez).
    # `float(... or default)` DEĞİL `.get(..., default)`: 0.0 meşru bir eşiktir (her planı keser)
    # ve `or` onu sessizce modül varsayılanına (bugün 5,0R) çevirirdi — operatörün yazdığı sayı
    # operatörün sayısıdır.
    heat_hard_r = float(limits.get("heat_hard_r", HEAT_HARD_R))
    heat_review_r = float(limits.get("heat_review_r", HEAT_REVIEW_R))
    corr_review = float(limits.get("corr_review", CORR_REVIEW))
    hard, soft = [], []
    sec = plan.get("sector", "?")
    sc = portfolio.get("sector_counts", {})
    rr = float(plan.get("r_multiple_expected", 0.0))

    # Faz 3 (5b): yapılandırılmış karar ağacı — detail_out verilirse HER kontrol pass/fail olarak
    # kaydedilir ("neden GO verdi?" sorusu geçen kontrolleri de gerektirir; yalnız vetolar yetmez).
    # Karar mantığı DEĞİŞMEZ: hard/soft listeleri birebir aynı dizgilerle dolar.
    def _chk(name: str, failed: bool, why: str, sev: str, value=None, threshold=None,
             gecse_de_yaz: bool = False):
        # `note` KURAL OLARAK yalnız DÜŞEN kontrolde yazılır: geçen bir satıra ret gerekçesi yazmak
        # kararı okuyan herkesi yanıltırdı. TEK İSTİSNA `gecse_de_yaz` (C12 ek bulgusu, 2026-08-02,
        # Rol-1 hükmü): "ÖLÇÜLEMEDİ" dalları `failed=False` ile çağrılır (fail-open BİLİNÇLİ — Y3
        # alanlarını hâlâ göndermeyen üreticiler var, `failed=True` onların TÜM planlarını keserdi)
        # ve satır `passed=True, note=None` olarak, yani tam olarak "tavan tuttu" görünümünde
        # düşüyordu. ÖLÇÜLEMEDİ ≠ HÜKÜM: hüküm DEĞİŞMEZ, ama satır sebebini TAŞIR.
        if detail_out is not None:
            detail_out.append({"check": name, "passed": not failed, "severity": sev,
                               "value": value, "threshold": threshold,
                               "note": why if (failed or gecse_de_yaz) else None})
        if failed:
            (hard if sev == "hard" else soft).append(why)

    # --- HARD (NO_GO) — exactly the old check_trade risk envelope; nothing more ---
    _chk("exposure_budget", regime.get("exposure_budget_pct", 0) <= 0,
         "exposure_budget %0 — bugün yeni risk yok", "hard",
         value=regime.get("exposure_budget_pct", 0), threshold=">0")
    _chk("max_open_positions", portfolio.get("open_positions", 0) >= limits["max_open_positions"],
         f"max {limits['max_open_positions']} pozisyon dolu", "hard",
         value=portfolio.get("open_positions", 0), threshold=f"<{limits['max_open_positions']}")
    _chk("sector_cap",
         (sc.get(sec, 0) + 1) / max(1, limits["max_open_positions"]) > limits["max_sector_exposure_pct"] / 100.0,
         f"'{sec}' sektör tavanı %{limits['max_sector_exposure_pct']:.0f} aşılıyor", "hard",
         value=sc.get(sec, 0) + 1, threshold=f"%{limits['max_sector_exposure_pct']:.0f}")
    _chk("daily_loss_breaker", portfolio.get("day_pnl_pct", 0.0) <= -limits["max_daily_loss_pct"] / 100.0,
         f"günlük kayıp devre kesici %{limits['max_daily_loss_pct']:.0f}", "hard",
         value=round(portfolio.get("day_pnl_pct", 0.0) * 100, 2), threshold=f">-%{limits['max_daily_loss_pct']:.0f}")
    _chk("position_size", plan.get("size_r", 0) > limits["max_position_r"],
         f"boyut {plan.get('size_r')}R > max {limits['max_position_r']}R", "hard",
         value=plan.get("size_r", 0), threshold=f"<={limits['max_position_r']}R")
    # R:R floor is a HARD veto now that r_multiple_expected VARIES per plan (measured-move target) and
    # exit.profit_target_r's lower bound (2.0) keeps the cap at/above the floor — so this discriminates
    # shallow-base low-reward setups per plan and can never zero out all trading.
    _chk("rr_floor", 0.0 < rr < DISCIPLINE_MIN_RR,
         f"R:R {rr:.1f} < {DISCIPLINE_MIN_RR:.1f} (yetersiz ödül/risk)", "hard",
         value=round(rr, 2), threshold=f">={DISCIPLINE_MIN_RR:.1f}")
    open_heat = portfolio.get("open_risk_r", 0.0) + float(plan.get("size_r", 0.0))
    _chk("heat_hard", open_heat > heat_hard_r,
         f"portföy ısısı sert tavanı %{heat_hard_r:.1f}R aşıyor (~{open_heat:.1f}R açık risk)", "hard",
         value=round(open_heat, 2), threshold=f"<={heat_hard_r:.1f}R")

    # --- SOFT (REVIEW) ---
    _chk("sector_stacking", sc.get(sec, 0) >= 1,
         f"'{sec}' sektöründe korelasyon yığılması", "soft", value=sc.get(sec, 0), threshold="0")
    heat = portfolio.get("open_risk_r", 0.0) + float(plan.get("size_r", 0.0))
    _chk("heat_review", heat > heat_review_r,
         f"portföy ısısı yüksek (~{heat:.1f}R açık risk)", "soft",
         value=round(heat, 2), threshold=f"<={heat_review_r:.1f}R")
    _chk("correlation", float(portfolio.get("max_corr", 0.0)) > corr_review,
         f"açık pozisyonlarla yüksek korelasyon (ρ≈{float(portfolio.get('max_corr', 0.0)):.2f}) — gerçek konsantrasyon",
         "soft", value=round(float(portfolio.get("max_corr", 0.0)), 2), threshold=f"<={corr_review}")
    # #11: prefer names in the day's leading sectors. leading_sectors may be plain names (older/backtest
    # path, often []) OR dicts {sector,momentum,n} (live loop's sector_momentum) — normalize to names so
    # the membership test and the join never see a dict (that TypeError only surfaced on a live cycle with
    # a candidate in a non-leading sector, which the backtest never exercised).
    leaders = [(d.get("sector") if isinstance(d, dict) else d) for d in regime.get("leading_sectors", [])]
    _chk("leading_sector", bool(leaders) and sec not in leaders,
         f"'{sec}' bugünün lider sektörlerinde değil ({', '.join(str(x) for x in leaders[:3])})", "soft",
         value=sec, threshold=",".join(str(x) for x in leaders[:3]) if leaders else None)
    if rr <= 0.0:
        _chk("rr_defined", True, "R:R belirsiz/sıfır", "soft", value=rr)   # explicit: 0 is a flag, not 'missing'
    else:
        _chk("rr_marginal", DISCIPLINE_MIN_RR <= rr < DISCIPLINE_MIN_RR + REVIEW_RR_BAND,
             f"R:R {rr:.1f} marjinal", "soft", value=round(rr, 2),
             threshold=f">={DISCIPLINE_MIN_RR + REVIEW_RR_BAND:.1f}")      # just above the floor -> eyeball
    if params is not None:
        min_score = float(params.get("entry.min_score", 60))
        _chk("score_band", plan.get("score", 100) < min_score + REVIEW_SCORE_BAND,
             "skor alt bantta", "soft", value=plan.get("score"), threshold=f">={min_score + REVIEW_SCORE_BAND:.0f}")

    # --- Y3'ÜN KARAR YOLUNDA KALAN KISMI: İKİ PORTFÖY TAVANI, İKİSİ DE BAYRAK-ARKASI -----------
    # DEFAULT KAPALI: knob yoksa/0 ise bu blok HİÇBİR ŞEY yapmaz ve kapı birebir eski davranışı
    # gösterir (çivi testi: params={} ile hüküm değişmez). Açılışları ÖLÇÜMDEN geçecek
    # (gölge-varyant/prescreen) — bugün yalnız yolu ve beyanı iniyor.
    #
    # Y3'ün İKİ PİYASA KAPISI (SPY 200-SMA, VIX backwardation) BU ZİNCİRDEN ÇIKARILDI — EDG-005
    # hükmü: GÖSTERGE, KAPI DEĞİL (gerekçe `_y3_portfolio_caps` gövdesinde).
    _y3_portfolio_caps(plan, portfolio, params, _chk)

    if hard:
        return "NO_GO", hard
    if soft:
        return "REVIEW", soft
    return "GO", []


# Y3 PORTFÖY TAVANLARININ BANTLARI (ROADMAP §3.1: sektör ≤ %25-30, ısı ≤ NAV %6-8). Knob DEĞERİ
# bandın içinden seçilir ve bounds.yaml onu zorlar; buradaki sabitler yalnız "knob verilmemişse
# hangi değer varsayılır" sorusunun cevabıdır ve kapı KAPALIYKEN hiç okunmaz.
SECTOR_CAP_DEFAULT_PCT = 25.0     # bandın ALT ucu (muhafazakâr): açılırsa en sıkı hâliyle açılır
HEAT_CAP_DEFAULT_PCT = 6.0        # NAV yüzdesi — bandın alt ucu, aynı gerekçe


# --- Y3 ÜRETİCİ↔TÜKETİCİ SÖZLEŞMESİ (C12, 2026-08-02) --------------------------------------------
# `_y3_portfolio_caps` ÜÇ portföy + İKİ plan alanı okur. Denetim C12: ÜRETİM ÇAĞIRANLARININ HİÇBİRİ
# bu alanları göndermiyordu — ampirik kanıt, en sıkı tavanla (sector_cap=0,1 / heat_cap=0,1) bile
# hükmün BİREBİR aynı kalmasıydı. Yani knob "açık" görünüyor (pano `enabled: true`), arama uzayında
# duruyor (bounds.yaml), Hermes önerebiliyor — ama yapısal olarak HİÇBİR yapılandırmada bağlayamıyor:
# aday replay incumbent'la bit-bit özdeş çıkar, kapı reddeder ve meşru bir risk kontrolü deftere
# KALICI kara liste ("already tried and failed") olarak yazılır.
#
# Alan adları burada SÖZLEŞME olarak durur (üretici testi bu iki demeti okur) ve ölçüm yardımcıları
# da burada: aynı büyüklüğün dört üreticide ayrı ayrı yazılması bu deponun ilk günden beri kovaladığı
# sınıftır (iki yüzey, sessiz ayrışma — `check_trade` kopyası GU2'de tam bundan patlamıştı).
Y3_PORTFOLIO_FIELDS = ("equity", "sector_notional", "heat_pct")
Y3_PLAN_FIELDS = ("notional", "risk_dollars")


def y3_plan_inputs(plan: dict, *, equity: float, size_fn) -> dict:
    """Aday planın DOLAR büyüklükleri (`notional`, `risk_dollars`) — kapı bunları PLANDAN okur.

    BOYUTLANDIRMA YASASI KOPYALANMAZ, ÇAĞRILIR: `size_fn` broker'ın `size_position`'ıdır ve
    ÇAĞIRANDAN gelir, çünkü guard broker'ı import EDEMEZ (içe aktarım kilidi,
    test_gate_statistics_v74 — "hüküm yalnız argümanlarının fonksiyonudur" yasasının uygulaması).
    Böylece qty/risk aritmetiği tek yerde kalır: boyutlandırıcı yarın değişirse tavan onunla
    birlikte değişir, ayrı bir kopya sessizce geride kalmaz.

    TAHMİN OLDUĞU BEYANLIDIR. Kapı SİLAHLANMA anında (D kapanışı) koşar, dolum ERTESİ AÇILIŞTA
    olur — o günün açılış fiyatı da, o andaki sermaye de HENÜZ YOKTUR. Ölçüm tetik fiyatı + bugünkü
    sermaye ile yapılır; gerçek dolum slippage/ADV tavanı/kısma çarpanıyla farklı çıkar. Bu bir
    muhasebe satırı değil, ÖNCEDEN bakan bir kısıttır; sapma yönü tek taraflı değildir ve tavanın
    kendisi zaten bir bandın alt ucundan seçilir.
    """
    trig = float(plan.get("entry_trigger") or 0.0)
    qty, risk_dollars = size_fn(trig, float(plan.get("stop") or 0.0),
                                float(plan.get("size_r") or 0.0), float(equity or 0.0))
    return {"notional": float(qty) * trig, "risk_dollars": float(risk_dollars)}


def y3_portfolio_inputs(positions, armed_plans=(), *, equity: float, size_fn) -> dict:
    """`_y3_portfolio_caps`ın okuduğu ÜÇ portföy alanını KİTAPTAN ölçer — üreticilerin tek kaynağı.

    positions   : açık pozisyon satırları — {"sector","qty","entry","stop","trail_stop","mark"}.
                  `mark` yoksa girişe düşülür: uydurma fiyat yerine BİLİNEN fiyat. Bu, kâr etmiş bir
                  pozisyonun notional'ını olduğundan KÜÇÜK gösterir, yani tavan geç bağlar — sapma
                  muhafazakâr yönde DEĞİLDİR ve bu yüzden çağıran markı geçirmek zorundadır (üç
                  üretici de geçiriyor; alan burada yalnız fail-safe olarak duruyor).
    armed_plans : dolmamış ama SLOT TUTAN planlar. R bacağı (`open_risk_r`) onları ZATEN sayıyor;
                  NAV bacağı saymasaydı aynı kitabı iki tavan farklı büyüklükte görürdü ve akşam
                  aynı anda silahlanan iki plan birbirini hiç görmezdi.
    ISI YASASI ölçüm katmanınınkiyle AYNIDIR: Σ max(0, giriş − max(stop, trail)) × adet ⁄ NAV.
                  `trail` savunmacı `max` ile alınır (broker yasası: trail asla gevşemez), yani
                  ölçülen şey "bugün stop'a düşse kaybedilecek" olandır — ilk risk değil.
    NAV ölçülemezse (eq ≤ 0) `heat_pct` **None** döner. 0.0 dönmek "ısı yok" demek olurdu ve açık
                  bir tavan ölçemediği turu "tavan tuttu" diye okuturdu; guard None dalında tavanı
                  UYGULAMAZ ve bunu karar satırında SÖYLER.
    """
    eq = float(equity or 0.0)
    sector_notional: dict = {}
    risk = 0.0
    for p in positions:
        qty = float(p.get("qty") or 0.0)
        entry = float(p.get("entry") or 0.0)
        mark = p.get("mark")
        px = float(mark) if mark is not None else entry
        sec = p.get("sector") or "?"
        sector_notional[sec] = sector_notional.get(sec, 0.0) + qty * px
        stop = float(p.get("stop") or 0.0)
        trail = p.get("trail_stop")
        etkin = max(stop, float(trail)) if trail is not None else stop
        risk += max(0.0, (entry - etkin) * qty)
    for a in (armed_plans or ()):
        d = y3_plan_inputs(a, equity=eq, size_fn=size_fn)
        sec = a.get("sector") or "?"
        sector_notional[sec] = sector_notional.get(sec, 0.0) + d["notional"]
        risk += d["risk_dollars"]
    return {"equity": eq, "sector_notional": sector_notional,
            "heat_pct": (100.0 * risk / eq) if eq > 0 else None}


def _olculemedi_notu(eksik: list, tavan: str) -> str:
    """ÖLÇÜLEMEDİ ≠ HÜKÜM (Rol-1 hükmü, 2026-08-02). Açık bir tavanın ölçüm yapamadığı tur karar
    ağacında `passed=True` düşer — fail-open BİLİNÇLİDİR, çünkü Y3 alanlarını hâlâ göndermeyen
    üreticiler var (gölge-v1/v2, mutation) ve `passed=False` onların TÜM planlarını keserdi. Ama
    satır sebebini taşımak ZORUNDA: eksik alan adıyla yazılmazsa denetimde "tavan tuttu"dan
    ayırt edilemez ve operatör panoda `enabled: true` görürken hiçbir koruma almaz (C12'nin
    kendisi tam olarak bu sessizlikten doğdu)."""
    return (f"ölçülemedi: {', '.join(eksik)} — {tavan} tavanının HÜKMÜ YOK (fail-open); "
            f"bu satır 'tavan tuttu' diye okunamaz")


def _y3_portfolio_caps(plan: dict, portfolio: dict, params: dict | None, _chk) -> None:
    """Y3'ün karar yolunda KALAN iki tavanı. İkisi de `params` içindeki knob 0/yok iken TAMAMEN ATIL.

    (1) portfolio.sector_cap  — sektör AĞIRLIĞI tavanı (%25-30 bandı). Mevcut `sector_cap` sert
        kuralı POZİSYON SAYISI tavanıdır (`max_sector_exposure_pct` ile sayıya çevrilir); bu knob
        farklı bir şey ölçer: sektörün NOTIONAL payı. İkisi birbirinin yerine geçmez ve bu yüzden
        ayrı isimle gelir.
    (2) portfolio.heat_cap    — açık risk / NAV tavanı. Isı 3a'dan beri analytics katmanında
        ÖLÇÜLÜYOR ama hiçbir kapıya bağlı DEĞİLDİ (3a beyanı: "YALNIZ GÖSTERGE"). Bağlanışı BU
        knob'la olur ve varsayılan KAPALIDIR — knob 0 iken ısı hiçbir karara girmez, yani 3a'nın
        beyanı knob açılana kadar birebir geçerli kalır. Ölçüm katmanının ADI burada bilerek
        yazılmaz: guard SAF kalmak zorunda ve o modülü ne çağırır ne içe aktarır; ısı `portfolio`
        sözlüğünden `heat_pct` alanı olarak GELİR (çağıranın sorumluluğu).
    (3)(4) İKİ PİYASA KAPISI BU ZİNCİRDEN ÇIKTI — EDG-005 HÜKMÜ: GÖSTERGE, KAPI DEĞİL (2026-08-01).
        `regime.spy_sma_gate` ÖLÇÜLDÜ (kart EDG-2026-005, arşiv): tek atfedilebilir pencerede kill#1
        tetiklendi (Sharpe −0,25→−0,90, PARA-v3 −0,029→−0,088); vol düşüyor ama bedeli getiri. OOS'ta
        55 bloke günde 0 girişi engelledi → kill#2'nin "pano göstergesi yeter" hükmü yürürlükte.
        `regime.vix_backwardation_gate` ise doğrulanmış VERİ-YOK (Massive 403 + FMP boş) — hüküm
        üretemez. Yani bu satırdan sonra `regime["entry_gates"]` okunsa bile HİÇBİR koşulda True
        gelemezdi: okuyan bir satır bırakmak, ölü bir kapıyı canlı gibi gösteren süs olurdu.
        Kapının hükmü ÖLMEDİ, YERİ DEĞİŞTİ: `regime.entry_gates()` hâlâ ölçer ve pano satırı
        (`api._y3_gate_row`) gösterir — karar yoluna GİRMEZ.
        GERİ ALMA (kablo yeniden kurulacaksa): VIX kaynağı gelirse ya da SMA kapısı yeni bir kartla
        yeniden açılırsa (a) `regime.entry_gates` sabit `blocks_new_entries=False`ini kaldırır,
        (b) `regime.build_regime_json` anahtarı yeniden yazar, (c) burada tüketici satır geri gelir.
        Üçü BİRLİKTE olmadan kapı çalışmaz — parça parça geri alınamaz (bugünkü ölü-ucun kendisi
        bu üçlünün ikisi eksik hâliydi).
    """
    p = params or {}
    # (1) sektör notional tavanı
    cap_pct = float(p.get("portfolio.sector_cap", 0) or 0)
    if cap_pct > 0:
        sec = plan.get("sector", "?")
        nav = float(portfolio.get("equity") or 0.0)   # KANONİK ALAN: `nav` takma adı YOK (parity yasası)
        sec_notional = float((portfolio.get("sector_notional") or {}).get(sec, 0.0))
        plan_notional = float(plan.get("notional") or 0.0)
        if nav > 0:
            pay = 100.0 * (sec_notional + plan_notional) / nav
            _chk("y3_sector_cap", pay > cap_pct,
                 f"Y3 sektör tavanı: '{sec}' payı %{pay:.1f} > %{cap_pct:.0f}", "hard",
                 value=round(pay, 2), threshold=f"<={cap_pct:.0f}%")
        else:
            # NAV ölçülemedi → tavan UYGULANMAZ ve bu SESSİZ KALMAZ: açık bir knob'un ölçüm
            # yapamadığı tur, "tavan tuttu" diye okunamaz. ÖLÇÜLEMEDİ ≠ HÜKÜM (2026-08-02): satır
            # GEÇER (fail-open bilinçli) ama EKSİK ALANI adıyla taşır — okuyucu "tavan çalıştı" ile
            # "tavan ölçemedi"yi ayırt edemezse açık bir knob sessizce atıl kalır.
            _chk("y3_sector_cap", False, _olculemedi_notu(["equity"], "Y3 sektör"),
                 "soft", value=None, threshold=f"<={cap_pct:.0f}%", gecse_de_yaz=True)
    # (2) portföy ısısı tavanı (NAV %)
    heat_pct_cap = float(p.get("portfolio.heat_cap", 0) or 0)
    if heat_pct_cap > 0:
        isi = portfolio.get("heat_pct")
        if isi is None:
            # Aynı yasa (ÖLÇÜLEMEDİ ≠ HÜKÜM): NAV da ölçülemiyorsa iki eksik alan da adıyla yazılır
            # — "hangisini kablolayınca tavan ayağa kalkar?" sorusu karar satırından cevaplanmalı.
            _eksik = ["heat_pct"] + ([] if float(portfolio.get("equity") or 0.0) > 0 else ["equity"])
            _chk("y3_heat_cap", False, _olculemedi_notu(_eksik, "Y3 ısı"), "soft",
                 value=None, threshold=f"<={heat_pct_cap:.1f}%", gecse_de_yaz=True)
        else:
            # Aday planın riski de eklenir: tavan ÖNCEDEN bakar, sonradan değil.
            plan_risk = float(plan.get("risk_dollars") or 0.0)
            nav = float(portfolio.get("equity") or 0.0)
            toplam = float(isi) + (100.0 * plan_risk / nav if nav > 0 else 0.0)
            _chk("y3_heat_cap", toplam > heat_pct_cap,
                 f"Y3 ısı tavanı: açık risk %{toplam:.2f} NAV > %{heat_pct_cap:.1f}", "hard",
                 value=round(toplam, 3), threshold=f"<={heat_pct_cap:.1f}%")
    # (3)(4) YOK — bilerek. Rejim katmanının piyasa kapıları artık GÖSTERGEdir (docstring, EDG-005).
