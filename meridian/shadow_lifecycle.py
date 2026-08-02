"""shadow_lifecycle.py — GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU (2026-07-30). SIFIR YETKİ, KENDİ KÂĞIT DEFTERİ.

NE DEĞİŞTİ. `shadow_variants` (v1) bir GİRİŞ-KARARI anlık görüntüsüdür: "bugün hangi varyant neyi
silahlandırırdı". Pozisyon taşımaz, fill görmez, çıkış görmez. Bu sınır iki bedel doğurmuştu ve
ikisi de yazılıydı: (a) ÇIKIŞ düğmeli kollar (V3/V6/V7) kontrol koluyla KARAR-ÖZDEŞ çıkıyor,
ölçüm kazancı sıfır olduğu için defterden ÇIKARILDILAR; (b) "bu varyant PARA kazandırır mıydı"
sorusu gölge katmanında hiç sorulamıyordu — yalnız `backtest.walk_forward` (geçmişe bakan, pencere
tüketen) yanıtlıyordu. Bu modül o eksik katmandır: **varyant başına kalıcı kâğıt defteri** —
fill → yönetim → çıkış → mark, her gün, canlı akışın taze barlarıyla.

YASALAR ÇAĞRILIR, KOPYALANMAZ — VE BURADA BU DAHA DA KRİTİKTİR. v1'de kopyalanacak şey kapı
hükmüydü; v2'de kopyalanacak şey İCRA yasasının TAMAMI olurdu (gap koruması, likidite tavanı,
notional tavanı, kısmi satış sırası, bar-içi muhafazakârlık, komisyon/kayma muhasebesi). Onlarca
satırlık bir kopya, ilk düzeltmede sessizce çatallanır ve defter zamanla stratejiyi değil KENDİNİ
ölçmeye başlardı. Bu yüzden:
  * FILL / KISMİ SATIŞ / DOKUNUŞ ÇIKIŞI / KAPANIŞ SATIRI  → `broker.PaperBroker`ın TA KENDİSİ.
    Her varyantın kitabı bir `PaperBroker` örneğidir; diskteki JSON yalnız o nesnenin serileşmiş
    hâlidir (`dataclasses.fields(Position)` ile — Position'a yarın eklenen alan kendiliğinden taşınır).
  * TRAIL / BREAKEVEN / CHANDELIER / GIVEBACK / TIME-STOP / ERKEN İTLAF → `strategy.manage_position`.
  * LİKİDİTE (ADV) → `backtest._adv`.  KISMA/TAVAN → `broker.derisk_mult` / `broker.max_positions_at`.
  * TARAMA + KAPI → `shadow_variants._signals` / `._judge` (onlar da `strategy.scan_all` /
    `guard.classify_gate` çağırır). İkinci bir tarama ya da ikinci bir kapı YOKTUR.
KOPYALANAN TEK ŞEY SÜRÜCÜDÜR (`step()`in faz sırası) ve kaynağı ADIYLA yazılıdır: `backtest.replay`
satır 182-351 — OPEN(D) bekleyen çıkışlar+fill, INTRADAY(D) scale_out+dokunuş, CLOSE(D) yönetim+arm.
Sıra bir "yasa" değil bir OLAY DÜZENİDİR ve ileri-dönüklüğü olmayan tek düzendir; onu çağırmanın yolu
yok (replay kendi takvimini ve kendi brokerını kurar), o yüzden burada tek yardımcıya çıkarıldı.

KİMLİK AYRIKLIĞI. Kapanan her işlem `SV-` önekli bir kimlik taşır (`SV-<varyant>-<tarih>-<ticker>`)
ve satırdaki `plan_id` de `SV-` öneklidir (`shadow_variants._plan_of`). `ledgers.PLAN_ID_RE`
(`^P-\\d{4}-\\d{2}-\\d{2}-`) ile ASLA eşleşmez: canlı defterin eşleştirmeleri (trades.plan_id,
cf_fidelity) hayali bir planla eşleşmeye çalışmaz. v1'in gerekçesi aynen geçerlidir, burada bir de
İŞLEM satırı ürettiğimiz için daha yüksek bedellidir.

ÇOKLU KARŞILAŞTIRMA — İKİ SORU, İKİ PAYDA (bu turun BİLİNÇLİ tasarım sapması, ROADMAP §7'de yazılı).
v1 defteri KARAR ayrışmasını ölçer; orada V3/V6 kontrol koluyla karar-özdeştir (bu YAPISAL bir olgu
ve `tests/test_sadelestirme_v123.py` ile çakılıdır — çıkış düğmeleri `scan_all`/`classify_gate`
yolunda HİÇ okunmaz). Bu yüzden `shadow_variants.VARIANTS` DEĞİŞMEDİ ve `k_variants` 4 kaldı:
karar sorusunun paydasını karar-özdeş kollarla şişirmek, gerçekten ayrışan kolların (V1/V2/V4)
cezasını sıfır ölçüm kazancı karşılığında artırmak olurdu — 2026-07-30'da tam bu gerekçeyle
temizlenmişti. PARA sorusunun paydası ise BAŞKADIR: kitapta V3/V6 gerçekten ayrışır. O yüzden
`k_lifecycle` (= `len(arms())`) ayrı bir alandır, kitap ve işlem satırlarında taşınır ve karnede
yazılır. Tek bir sayıya indirgemek, iki farklı çoklu-karşılaştırma ailesini birbirine karıştırmak
olurdu; iki sayı tutmak onları AYIRT EDİLEBİLİR kılar.

NO-OP KOL YASAĞI (E4 tuzağı). `exit.scale_out_r` üretim varsayılanı ZATEN 2.0'dır — onu 2.0'a
"ayarlayan" bir kol hiçbir şeyi değiştirmez ama paydayı büyütür ve defterine yazacağı sıfır ayrışma
bir ÖLÇÜM değil bir KURGU olur. `noop_arms()` her kolun ETKİN parametre sözlüğünü kontrol kolununkiyle
OKUNAN anahtar düzeyinde karşılaştırır; farkı boş olan kol turdan DÜŞÜRÜLÜR (sessizce değil: obs.warn
+ kitap satırında `dropped_arms`). Kural testle çakılıdır.

SIFIR YETKİ. Yazdığı iki dosya vardır: `shadow_books.json` ve `shadow_trades.jsonl`. Canlı
`portfolio.json`a, `trades.jsonl`a, `trade_plans.jsonl`a, aynaya (Alpaca) ve strategy.yaml'a HİÇBİR
yol çıkmaz. Bu defterden ship yolu YOKTUR — canlıya geçiş yalnız OOS kapısından (prescreen/reflect)
geçer; buradaki para sayıları bir KANIT HIZLANDIRICISIDIR, bir onay değil.
"""
from __future__ import annotations

import dataclasses
import os

import pandas as pd

from . import barclock, broker as brk, indicators as ind, obs, regime as regime_mod, \
    score as score_mod, store, strategy
from . import shadow_variants as sv
from .backtest import SECTORS, _adv          # likidite (ADV) yasası + sektör haritası: ÜRETİMİN kendisi

# Varsayılan AÇIK — tek yan etkisi kendi iki defterine yazmaktır (v1 ile aynı gerekçe). Kapatma
# anahtarı yine de var: ölçüm bile olsa operatör bir katmanı susturabilmelidir.
ENABLED = os.environ.get("MERIDIAN_SHADOW_LIFECYCLE", "1") != "0"

BOOKS_FILE = "shadow_books.json"          # varyant → kitap (pozisyonlar, sermaye, zirve, eğri)
TRADES_FILE = "shadow_trades.jsonl"       # kapanan işlemler, satır başına `variant` + `SV-` kimlik

SEED_SESSIONS = 5        # N00005 tohumlama penceresi (seans). Yalnız defter BOŞKEN, bir kez.
MAX_CURVE = 260          # kitapta tutulan sermaye eğrisi tavanı (~1 yıl seans) — dosya şişmesin
BOOK_SCHEMA = 1

# --- v2'DE GERİ GELEN ÇIKIŞ KOLLARI ---------------------------------------------------------------
# Bunlar `shadow_variants.VARIANTS`e EKLENMEZ (yukarıdaki iki-payda gerekçesi): v1 defteri KARAR
# ölçer ve orada karar-özdeşler. Kitapta ise gerçekten ayrışırlar, çünkü bu katman fill ömrünü ve
# yönetim barlarını izler — `exit.early_kill_pivot` `strategy.manage_position` içinde, `scale_out`
# `broker.scale_out` içinde OKUNUR ve ikisi de burada koşar.
#   V3 — G3b erken itlaf. `exit.early_kill_bars` VARSAYILANDA (1) bırakıldı: ikinci düğmeyi de
#        oynatmak iki değişkenli bir kol yapardı ve "hangisi etkiledi" sorusu ölçülemez hâle gelirdi.
#        Pivot GEREKLİDİR ve bu motor onu taşır (armed yan haritası → fill_entry(pivot=...) →
#        Position.pivot). C13 (2026-08-02): canlı yol da artık taşıyor — bu satır eskiden "canlıda
#        pivot 0.0, orada atıldır" diyordu, yani bu kolun ölçtüğü kazanç terfi etse canlıda sessiz
#        no-op olurdu. Kol artık CANLIDA UYGULANABİLİR bir düğmeyi ölçüyor.
#   V6 — Batch L #8 kısmi kâr alma. YALNIZ `scale_out_frac`: `scale_out_r` zaten 2.0 (üretim
#        varsayılanı VE canlı strategy.yaml değeri) — onu sete koymak E4 no-op tuzağının ta kendisi
#        olurdu. `noop_arms()` bunu koda değil ÖLÇÜME dayanarak yakalar.
LIFECYCLE_ONLY: dict[str, dict] = {
    "V3": {"label": "erken itlaf: pivot-altı kapanış (G3b, PARA-v3 E1)",
           "knobs": {"exit.early_kill_pivot": 1}},
    "V6": {"label": "kısmi kâr alma %50 @ 2.0R (Batch L #8)",
           "knobs": {"exit.scale_out_frac": 0.5}},
}


def arms() -> dict[str, dict]:
    """Kitap kolları = v1 karar kolları ∪ yaşam-döngüsü kolları. Payda (`k_lifecycle`) BURADAN
    türer, elle sayılmaz: bir kol eklendiğinde/çıkarıldığında çoklu-karşılaştırma cezası
    kendiliğinden düzelir (v1'in `k_variants = len(VARIANTS)` dersinin aynısı)."""
    return {**sv.VARIANTS, **LIFECYCLE_ONLY}


# --- OKUNAN ANAHTARLAR + ÜRETİM VARSAYILANLARI ----------------------------------------------------
# NEDEN BU TABLO VAR: "bu kol kontrol kolundan farklı mı?" sorusu ancak ETKİN değerler üzerinden
# yanıtlanabilir. Bir düğme canlı `eff` içinde YOKSA motor onu üretim varsayılanıyla okur; kol o
# varsayılanı "ayarlarsa" hiçbir şey değişmez (E4 tuzağı). Tablo bir görüş değil KOPYADIR ve kopya
# olduğu için çürüyebilir — bu yüzden `tests/test_golge_v2_yasam_dongusu_v132.py` her satırı
# kaynaktaki LİTERAL varsayılanla (AST) karşılaştırır; strategy/broker varsayılanı değişirse test patlar.
# Kapsam BİLEREK dardır: yalnız YAŞAM-DÖNGÜSÜ yolunda (manage_position + broker.scale_out) okunan
# anahtarlar. Giriş anahtarlarının varsayılanları burada YOKTUR ve olmamalıdır — bir giriş kolunun
# no-op'u zaten KARAR katmanında görünür (signal_n/would_arm ayrışması sıfır kalır), burada ikinci
# kez ve eksik bir tabloyla tahmin edilmesi gerekmez.
LIFECYCLE_READ_DEFAULTS: dict[str, tuple] = {
    "exit.trail_atr_mult":      (2.5, "strategy.manage_position"),
    "exit.breakeven_r":         (1.0, "strategy.manage_position"),
    "exit.chandelier_lookback": (0,   "strategy.manage_position"),
    "exit.giveback_pct":        (0.0, "strategy.manage_position"),
    "exit.time_stop_days":      (15,  "strategy.manage_position"),
    "exit.early_kill_pivot":    (0,   "strategy.early_kill_pivot_exit"),
    "exit.early_kill_bars":     (1,   "strategy.early_kill_pivot_exit"),
    "exit.scale_out_frac":      (0.0, "broker.scale_out"),
    "exit.scale_out_r":         (2.0, "broker.scale_out"),
}


def _read_value(params: dict, key: str):
    """Motorun o anahtarı OKUYACAĞI değer: sözlükte varsa o, yoksa üretim varsayılanı.
    Tabloda olmayan (giriş) anahtarı için 'yok' anlamında None — bkz. tablo gerekçesi."""
    if key in params:
        return params[key]
    d = LIFECYCLE_READ_DEFAULTS.get(key)
    return d[0] if d else None


def divergent_keys(eff: dict, knobs: dict) -> list[str]:
    """Kolun kontrol kolundan AYRIŞTIĞI okunan-anahtarlar. Boşsa kol no-op'tur."""
    ctrl, arm = dict(eff), {**eff, **knobs}
    keys = set(knobs) | set(LIFECYCLE_READ_DEFAULTS)
    out = []
    for k in sorted(keys):
        a, c = _read_value(arm, k), _read_value(ctrl, k)
        try:
            same = float(a) == float(c)
        except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen değer (None ya da metin) için doğru karşılaştırma ZATEN eşitliktir — dal bir arızayı değil ikinci bir kıyas biçimini işletir
            same = a == c
        if not same:
            out.append(k)
    return out


def noop_arms(eff: dict) -> list[dict]:
    """Kontrol kolundan HİÇBİR okunan-anahtarda ayrışmayan kollar. Kontrol kolunun kendisi (düğmesiz)
    doğal olarak bu listededir ve DIŞARIDA bırakılır — o kolun işi zaten aynı olmaktır."""
    bad = []
    for vid, spec in arms().items():
        if not spec["knobs"]:
            continue
        if not divergent_keys(eff, spec["knobs"]):
            bad.append({"variant": vid, "knobs": dict(spec["knobs"]),
                        "hata": "kontrol kolundan ayrışmıyor (no-op) — payda bedeli var, ölçüm kazancı yok"})
    return bad


# --- KİTAP: PaperBroker ↔ JSON --------------------------------------------------------------------
_POS_FIELDS = tuple(f.name for f in dataclasses.fields(brk.Position))


def _new_book(vid: str) -> dict:
    return {"variant": vid, "start_equity": score_mod.START_EQUITY, "realized_pnl": 0.0,
            "peak_equity": score_mod.START_EQUITY, "day_start_equity": score_mod.START_EQUITY,
            "positions": {}, "armed": [], "pending_exits": {}, "equity_curve": [],
            "n_trades": 0, "n_seeded": 0, "last_date": None, "trade_seq": 0, "prev_scale": None}


def _new_doc() -> dict:
    return {"schema": BOOK_SCHEMA, "created": barclock.now().isoformat(),
            "k_lifecycle": len(arms()), "authority": "paper_only",
            "seed": {"done": False, "dates": [], "at": None, "sessions": SEED_SESSIONS},
            "variants": {}}


def _to_broker(bk: dict, goal: dict) -> brk.PaperBroker:
    """Diskteki kitabı ÜRETİMİN broker nesnesine geri kurar. Sürtünme parametreleri `goal`dan gelir —
    `backtest.replay` satır 141-142 ile aynı kaynak; ikinci bir varsayılan yazmak iki motorun
    sürtünmesini sessizce ayrıştırırdı."""
    b = brk.PaperBroker(float(bk["start_equity"]), float(goal.get("slippage_bps", 5)),
                        float(goal.get("commission_per_share", 0.0)))
    b.realized_pnl = float(bk.get("realized_pnl") or 0.0)
    b.cash = b.start_equity + b.realized_pnl
    b._id = int(bk.get("trade_seq") or 0)
    for t, p in (bk.get("positions") or {}).items():
        b.positions[t] = brk.Position(**{k: p[k] for k in _POS_FIELDS if k in p})
    return b


def _from_broker(b: brk.PaperBroker, bk: dict) -> None:
    bk["realized_pnl"] = round(b.realized_pnl, 4)
    bk["trade_seq"] = b._id
    bk["positions"] = {t: {k: getattr(p, k) for k in _POS_FIELDS} for t, p in b.positions.items()}


def _bar_on(df, d):
    if df is None or d not in df.index:
        return None
    r = df.loc[d]
    return {"open": float(r["open"]), "high": float(r["high"]),
            "low": float(r["low"]), "close": float(r["close"])}


# --- GÜNLÜK ADIM — faz sırası `backtest.replay` 182-351'den -----------------------------------------
def step(bk: dict, params: dict, date: str, bars_of, *, regime_ok: bool, limits: dict, goal: dict,
         armed_next: list, seeded: bool = False) -> list[dict]:
    """Bir varyantın BİR seansı. Dönüş: o gün KAPANAN işlem satırları (broker'ın ürettiği satırlar).

    `armed_next`: bu seansın KAPANIŞINDA silahlanacak planlar —
    `[{"plan": {...}, "pivot": float, "atr": float|None}]`. Pivot ve ATR plan SÖZLÜĞÜNE konmaz, YAN
    haritada taşınır: `backtest.replay`in `armed_pivots`/`armed_atr` deseni ve aynı gerekçe (ikisi de
    bir defter alanı değil bir İCRA girdisidir; G3b notu, broker.py:132). `atr` yoksa/None ise E1
    limiti yalnız yüzde tavanıyla kurulur — uydurma ATR yok, ama o durumda bu motor canlıdan GEVŞEK
    kalır, o yüzden `_day` onu silahlanma anındaki sinyalden DOLDURUR (C11/C18).

    İLERİ-DÖNÜKLÜK YOK: D'nin kararları D'nin KAPANIŞINDA verilir, icrası D+1'in AÇILIŞINDA olur."""
    d = pd.Timestamp(date)
    b = _to_broker(bk, goal)
    max_open = int(limits["max_open_positions"])
    max_daily_loss = float(limits["max_daily_loss_pct"]) / 100.0
    closed: list[dict] = []

    def _marks_open():
        # AÇILIŞ MARKI (replay `marks_open_on`): açılış fazının sermayesi D'nin KAPANIŞIYLA
        # işaretlenirse devre kesici/kısma/boyutlandırma sabahtan öğleden sonrayı bilir (denetim #1).
        out = {}
        for t in b.positions:
            bar = _bar_on(bars_of(t), d)
            if bar is not None:
                out[t] = bar["open"]
        return out

    # ---- 1. OPEN(D): bekleyen çıkışlar, sonra silahlı girişler ----
    for t, reason in list((bk.get("pending_exits") or {}).items()):
        bar = _bar_on(bars_of(t), d)
        if t in b.positions and bar is not None:
            closed.append(b.close_position(t, bar["open"], reason, date))
    bk["pending_exits"] = {}

    eq_now = b.equity(_marks_open())
    bk["peak_equity"] = peak = max(float(bk.get("peak_equity") or eq_now), eq_now)
    size_mult = brk.derisk_mult(eq_now, peak)
    eff_max_open = brk.max_positions_at(eq_now, peak, max_open)
    dse = float(bk.get("day_start_equity") or 0.0) or eq_now
    breaker_tripped = (eq_now - dse) / dse <= -max_daily_loss if dse else False
    for entry in (bk.get("armed") or []):
        plan = entry["plan"]
        t = plan["ticker"]
        df = bars_of(t)
        bar = _bar_on(df, d)
        if bar is not None and not breaker_tripped and size_mult > 0 \
                and len(b.positions) < eff_max_open and t not in b.positions:
            # C11+C18 (denetim 2026-08-02): `atr` de pivot ile AYNI yan haritadan geçer. Geçmediği
            # sürece `broker.entry_limit_price` ATR bacağını hiç göremiyor ve bu motor limiti DAİMA
            # %1 tavanıyla kuruyordu — canlı motor min(0,5·ATR14, %1) ile koşarken. Gölge-v2 terfi
            # kanıtı üretir; canlının reddedeceği dolumları yazması, terfi kararını iyimser bir icra
            # modeli üzerinden verdirirdi. Ölçülemeyen ATR None kalır (uydurma yok).
            b.fill_entry(plan, bar["open"], date, eq_now, size_mult=size_mult,
                         adv=_adv(df, d), pivot=float(entry.get("pivot") or 0.0),
                         atr=entry.get("atr"))
    # replay burada `armed`ı SIFIRLAR (bar-yok = tatil/delisting, plan gerçekten dolmaz). Gölge de
    # geçmiş/taze bar üzerinde koşar, canlı `_carry_armed_without_bar` TAŞIMA kuralı buraya girmez:
    # o kural bir EOD YAYIN GECİKMESİ çaresidir ve gölge katmanı zaten canlı akışın barlarını görür.
    bk["armed"] = []
    bk["day_start_equity"] = b.equity(_marks_open())

    # ---- 2. INTRADAY(D): kısmi satış + dokunuş çıkışları ----
    # `prev_scale`: replay CLOSE(D)'de `prev_eff = eff` der ve ERTESİ günün scale_out'unu onunla
    # koşar (D'nin gün-içi anında bilinen rejim D-1'inkidir). `broker.scale_out` params'tan YALNIZ
    # iki anahtar okur, o yüzden defterde tam olarak o iki anahtar taşınır — bugünün rejimiyle
    # çözülmüş `params`ı kullanmak sessiz bir ileri-dönüklük olurdu.
    intraday_params = bk.get("prev_scale") or params
    for t in list(b.positions.keys()):
        bar = _bar_on(bars_of(t), d)
        if bar is None:
            continue
        pos = b.positions[t]
        b.scale_out(pos, {"high": bar["high"], "low": bar["low"], "open": bar["open"]}, intraday_params)
        ex = b._touch_exit(pos, {"open": bar["open"], "high": bar["high"], "low": bar["low"]})
        if ex:
            closed.append(b.close_position(t, ex[0], ex[1], date))
        else:
            pos.bars_held += 1

    # ---- 3. CLOSE(D): yönetim (trail/breakeven/erken itlaf/time-stop), sonra arm ----
    for t in list(b.positions.keys()):
        df = bars_of(t)
        if df is None or d not in df.index:
            continue
        pos = b.positions[t]
        dec = strategy.manage_position(
            df.loc[:d].reset_index(),
            {"entry": pos.entry, "stop": pos.stop, "trail_stop": pos.trail_stop,
             "r_per_share": pos.r_per_share, "pivot": pos.pivot},
            params, pos.bars_held, regime_ok)
        pos.trail_stop = dec.trail_stop
        if dec.exit_now:
            bk["pending_exits"][t] = dec.exit_reason

    slots = max_open - len(b.positions)
    keep = []
    for entry in armed_next:
        if slots <= 0:
            break
        if entry["plan"]["ticker"] in b.positions:
            continue
        keep.append(entry)
        slots -= 1
    bk["armed"] = keep
    bk["prev_scale"] = {k: params[k] for k in ("exit.scale_out_frac", "exit.scale_out_r")
                        if k in params}

    # ---- kapanış markı + defter ----
    marks_close = {}
    for t in b.positions:
        bar = _bar_on(bars_of(t), d)
        if bar is not None:
            marks_close[t] = bar["close"]
    _from_broker(b, bk)
    bk["equity_curve"] = (bk.get("equity_curve") or [])[-(MAX_CURVE - 1):] + \
                         [[date, round(b.equity(marks_close), 2)]]
    bk["last_date"] = date
    bk["n_trades"] = int(bk.get("n_trades") or 0) + len(closed)
    if seeded:
        bk["n_seeded"] = int(bk.get("n_seeded") or 0) + len(closed)
    return closed


def _trade_rows(vid: str, spec: dict, closed: list[dict], date: str, seeded: bool, k: int) -> list[dict]:
    """Broker satırı → defter satırı. RETRO-DAMGA YASAĞI: `ts` satırın GERÇEK yazım anıdır,
    seans tarihi ayrı alandır (`session_date` / `ts_close`). Tohum satırları `seeded: true` taşır —
    "bu kanıt canlı akıştan mı geriye dönük simülasyondan mı geldi" sorusu satırdan yanıtlanabilmeli."""
    now = barclock.now().isoformat()
    out = []
    for r in closed:
        out.append({**r,
                    "id": f"SV-{vid}-{r.get('ts_close') or date}-{r.get('ticker')}",
                    "variant": vid, "label": spec["label"], "knobs": dict(spec["knobs"]),
                    "k_lifecycle": k, "session_date": date, "seeded": bool(seeded),
                    "ts": now, "authority": "paper_only"})
    return out


# --- BİR SEANSIN TÜM KOLLARI ----------------------------------------------------------------------
def _day(doc: dict, date: str, live: dict, *, tickers, tail_of, rs_of, sector_of, max_corr_of,
         eff: dict, regime: dict, regime_ok: bool, goal: dict, limits: dict, version: int,
         bars_of, sigs_by_variant: dict | None = None, seeded: bool = False) -> list[dict]:
    """Tek seans × tüm kollar. `live` yalnız kayıt içindir (bu turda canlı kaç sembol silahlandırdı).

    KAPI KOLUN KENDİ KİTABINA KARŞI KOŞAR — v1'den KASITLI ve GEREKLİ fark: v1 kapıyı CANLI kitabın
    projeksiyonuna karşı koşturur ("aynı gün, aynı akış, aynı portföy"), çünkü ölçtüğü şey KARARIN
    ayrışmasıdır. v2'de kolun kendi pozisyonları vardır; slot sayısını, sektör dolumunu ve açık riski
    canlı kitaptan okumak, kolun kendi portföyünü GÖRMEZDEN gelmek olurdu ve kitap ilk haftadan sonra
    canlının portföy kısıtlarını taşıyan hayalî bir defter hâline gelirdi."""
    rows: list[dict] = []
    k = len(arms())
    d = pd.Timestamp(date)
    for vid, spec in arms().items():
        bk = doc["variants"].setdefault(vid, _new_book(vid))
        params = {**eff, **spec["knobs"]}
        try:
            sigs = (sigs_by_variant or {}).get(vid)
            if sigs is None:
                sigs, _failed = sv._signals(tickers, params, tail_of, rs_of)
            book_state = sv._book_state(
                {"positions": {t: {"sector": sector_of(t), "size_r": p.get("size_r")}
                               for t, p in (bk.get("positions") or {}).items()},
                 "equity": _book_equity(bk), "peak_equity": bk.get("peak_equity")},
                limits, sector_of)
            # KORELASYON TAVANI KOLUN KENDİ PORTFÖYÜNDEN ÖLÇÜLÜR. Çağıranın `max_corr_of`u CANLI
            # pozisyonlara demirlidir; kolun kendi kitabı farklı isimler taşıdığında o sayı kapıya
            # YANLIŞ bir yoğunlaşma girdisi verirdi (ve tohumlamada canlı portföy hiç yoktur).
            # Bar bulunamayan sembolde çağıranın girdisine düşülür — uydurma sıfır yerine bilinen kaynak.
            _corr = _corr_fn(bars_of, d, list((bk.get("positions") or {})), max_corr_of)
            armed_next = []
            if regime.get("exposure_budget_pct", 0) > 0:
                _judged, _armed, armed_next = sv._judge(
                    sigs, date, sector_of=sector_of, max_corr_of=_corr, params=params,
                    regime=regime, goal=goal, limits=limits, version=version, bk=book_state)
                # C11/C18: E1 limitinin ATR bacağı. `sv._judge` yan haritayı yalnız `pivot` ile
                # üretiyor; ATR aynı sinyal nesnesinde ZATEN ölçülmüştür (`EntrySignal.atr`) ve
                # burada eklenir — silahlanma anında sabitlenir, dolum anında yeniden hesaplanmaz
                # (canlı `entry_law` tablosu ve replay `armed_atr` ile aynı yasa). Yazım
                # `shadow_variants`e DEĞİL buraya kondu: v1 karar defteri fill koşturmaz, ATR'yi
                # okuyan tek motor budur (YASA 6 — okuyucusuz alan yazılmaz).
                _atr_of = {getattr(s, "ticker", None): (float(getattr(s, "atr", 0.0) or 0.0) or None)
                           for s in (sigs or [])}
                for _e in armed_next:
                    _e.setdefault("atr", _atr_of.get(_e["plan"]["ticker"]))
            closed = step(bk, params, date, bars_of, regime_ok=regime_ok, limits=limits,
                          goal=goal, armed_next=armed_next, seeded=seeded)
        except Exception as e:
            # Bir kolun arızası turu DÜŞÜRMEZ ve SESSİZ KALMAZ (YASA 4, v1 deseni). KİTAP SİLİNMEZ:
            # kolun açık pozisyonları vardır ve onları düşürmek gerçekleşmemiş bir K/Z'yi defterden
            # yok etmek olurdu. Kitap İLERLEMEZ (last_date aynı kalır) ve arıza damgalanır — "bu kol
            # o gün ölçülmedi" ile "o gün hiçbir şey olmadı" birbirinden ayırt edilebilsin.
            obs.warn("shadow_lifecycle_arm_failed", variant=vid, date=date,
                     error=f"{type(e).__name__}: {e}")
            bk["last_error"] = {"date": date, "error": f"{type(e).__name__}: {e}"[:160]}
            bk["failed_days"] = int(bk.get("failed_days") or 0) + 1
            continue
        rows.extend(_trade_rows(vid, spec, closed, date, seeded, k))
    if live:
        doc["last_live"] = live
    return rows


def _corr_fn(bars_of, d, held: list, fallback):
    """`guard`ın okuduğu `max_corr` girdisi — `indicators.corr_max`/`returns_tail` ÇAĞRILIR."""
    others = []
    for x in held:
        dfx = bars_of(x)
        if dfx is not None:
            others.append(ind.returns_tail(dfx.loc[:d, "close"]))

    def _of(t):
        df = bars_of(t)
        if df is None:
            return fallback(t)
        return ind.corr_max(df.loc[:d, "close"], others)
    return _of


def _book_equity(bk: dict) -> float:
    """Kitabın SON bilinen sermayesi (eğrinin son noktası; yoksa gerçekleşmiş)."""
    curve = bk.get("equity_curve") or []
    if curve:
        return float(curve[-1][1])
    return float(bk.get("start_equity") or score_mod.START_EQUITY) + float(bk.get("realized_pnl") or 0.0)


# --- N00005 TOHUMLAMA -----------------------------------------------------------------------------
def _seed(doc: dict, date: str, *, bars: dict, index_bars, eff: dict, goal: dict, limits: dict,
          version: int, sessions: int) -> tuple[list[dict], list[str]]:
    """Son `sessions` seansı DETERMİNİSTİK olarak geriye doldur. YALNIZ defter boşken, BİR kez.

    NEDEN (Nous N00005): defter boşken karne aylarca "ölçülemedi" der; günlük kanıt üretimi tek
    seanstır. Geriye dönük simülasyon aynı BARLARLA, aynı kanunlarla ve aynı `step()` sürücüsüyle
    koşar — yani tohum satırları canlı satırlardan YÖNTEM olarak farklı DEĞİLDİR; farkı `seeded: true`
    damgasıdır ve karne onları ayrı sayar (kanıtın nereden geldiği görünmeden birikmesi, kanıt değil
    gürültü olurdu).

    TOHUM PENCERESİ `date`in KENDİSİNİ İÇERMEZ: o seansın adımını canlı kanca atar (aksi hâlde aynı
    gün iki kez işlenir ve fill/çıkış çift sayılırdı)."""
    d0 = pd.Timestamp(date)
    cal = [t for t in index_bars.index if t < d0][-sessions:]
    if not cal:
        return [], []
    from .loop import _scan_tail            # TEK tarama-dilimi reçetesi (nedensel kesim + pencere)
    rows: list[dict] = []
    done: list[str] = []
    for d in cal:
        dstr = str(d.date())
        rj = regime_mod.build_regime_json(index_bars.loc[:d].reset_index(), eff, dstr)
        srets = {t: float(df.loc[:d]["close"].iloc[-1] / df.loc[:d]["close"].iloc[-22] - 1.0)
                 for t, df in bars.items() if len(df.loc[:d]) > 22}
        rj["leading_sectors"] = regime_mod.sector_momentum(srets, SECTORS)
        regime_ok = rj["regime"] in ("trend_up", "chop") and rj["exposure_budget_pct"] > 0
        rets = {t: float(df.loc[:d]["close"].iloc[-1] / df.loc[:d]["close"].iloc[-1 - strategy.RS_LOOKBACK] - 1.0)
                for t, df in bars.items()
                if d in df.index and len(df.loc[:d]) > strategy.RS_LOOKBACK + 1}
        rs_map = ind.rs_rating(rets)
        tickers = sorted(t for t, df in bars.items() if d in df.index)
        rows.extend(_day(
            doc, dstr, {}, tickers=tickers,
            tail_of=lambda t, _d=d: _scan_tail(bars[t], _d),
            rs_of=lambda t: rs_map.get(t, 50), sector_of=lambda t: SECTORS.get(t, "?"),
            max_corr_of=lambda t: 0.0,          # yalnız BAR YOKSA kullanılan yedek (bkz. `_corr_fn`)
            eff=eff, regime=rj, regime_ok=regime_ok, goal=goal, limits=limits, version=version,
            bars_of=lambda t: bars.get(t), seeded=True))
        done.append(dstr)
    return rows, done


# --- KANCA ----------------------------------------------------------------------------------------
def run_cycle(date: str, *, tickers, tail_of, rs_of, sector_of, max_corr_of, eff: dict,
              regime: dict, regime_ok: bool, goal: dict, limits: dict, version: int,
              bars: dict, index_bars=None, sigs_by_variant: dict | None = None,
              live_armed: list | None = None, seed_sessions: int = SEED_SESSIONS,
              write: bool = True) -> dict | None:
    """Bir EOD turu × tüm kollar → kitap güncellenir, kapanan işlemler deftere yazılır.

    `write=False` testler için: kitap/işlemler ÜRETİLİR, diske YAZILMAZ (canlı state'e yazan test yok).
    Dönüş: {"trades": [...], "books": {...}, "dropped_arms": [...], "seeded": [...]} ya da None (kapalı).

    KİLİT (B3, 2026-07-31): gövde bir OKU-DEĞİŞTİR-YAZdır (kitap okunur, tur işlenir, kitap geri
    yazılır) ve kilitsizdi. Tek yazar OLMASI kilidi gereksiz kılmaz: aynı kodu iki SÜREÇ koşarsa
    (zamanlayıcı + elle tetiklenen tur) geç biten, öbürünün tüm kollarını eski kopyasıyla geri
    alır. Kilit YALNIZ `write=True` iken alınır — `write=False` hiçbir bayta dokunmaz ve testlerin
    saf yolunu kilit sırasına sokmak, ölçümü ölçülen şeyin dışındaki bir şeye bağlardı."""
    if not ENABLED:
        return None
    if write:
        with store.file_lock(BOOKS_FILE):
            return _run_cycle_govde(
                date, tickers=tickers, tail_of=tail_of, rs_of=rs_of, sector_of=sector_of,
                max_corr_of=max_corr_of, eff=eff, regime=regime, regime_ok=regime_ok, goal=goal,
                limits=limits, version=version, bars=bars, index_bars=index_bars,
                sigs_by_variant=sigs_by_variant, live_armed=live_armed,
                seed_sessions=seed_sessions, write=True)
    return _run_cycle_govde(
        date, tickers=tickers, tail_of=tail_of, rs_of=rs_of, sector_of=sector_of,
        max_corr_of=max_corr_of, eff=eff, regime=regime, regime_ok=regime_ok, goal=goal,
        limits=limits, version=version, bars=bars, index_bars=index_bars,
        sigs_by_variant=sigs_by_variant, live_armed=live_armed, seed_sessions=seed_sessions,
        write=False)


def _run_cycle_govde(date: str, *, tickers, tail_of, rs_of, sector_of, max_corr_of, eff: dict,
                     regime: dict, regime_ok: bool, goal: dict, limits: dict, version: int,
                     bars: dict, index_bars=None, sigs_by_variant: dict | None = None,
                     live_armed: list | None = None, seed_sessions: int = SEED_SESSIONS,
                     write: bool = True) -> dict | None:
    """`run_cycle`ın gövdesi — kilit ONUN üzerindedir (bkz. oradaki gerekçe)."""
    doc = store.read_json(BOOKS_FILE, None) if write else None
    if not isinstance(doc, dict) or "variants" not in doc:
        doc = _new_doc()
    doc["k_lifecycle"] = len(arms())

    # NO-OP KOL REDDİ — kolun kendisi düşer, tur düşmez (YASA 4: sebep sayılır ve satıra girer).
    dropped = noop_arms(eff)
    if dropped:
        obs.warn("shadow_lifecycle_noop_arm", n=len(dropped), detail=str(dropped)[:200])
    doc["dropped_arms"] = dropped
    drop_ids = {d["variant"] for d in dropped}

    seeded_dates: list[str] = []
    rows: list[dict] = []
    if not doc["seed"]["done"] and bars and index_bars is not None and seed_sessions > 0:
        try:
            rows, seeded_dates = _seed(doc, date, bars=bars, index_bars=index_bars, eff=eff,
                                       goal=goal, limits=limits, version=version,
                                       sessions=seed_sessions)
        except Exception as e:
            obs.warn("shadow_lifecycle_seed_failed", error=f"{type(e).__name__}: {e}")
        doc["seed"] = {"done": True, "dates": seeded_dates, "sessions": seed_sessions,
                       "at": barclock.now().isoformat()}

    rows.extend(_day(doc, date, {"armed": sorted({str(t).upper() for t in (live_armed or []) if t})},
                     tickers=tickers, tail_of=tail_of, rs_of=rs_of, sector_of=sector_of,
                     max_corr_of=max_corr_of, eff=eff, regime=regime, regime_ok=regime_ok,
                     goal=goal, limits=limits, version=version,
                     bars_of=lambda t: (bars or {}).get(t), sigs_by_variant=sigs_by_variant))

    rows = [r for r in rows if r["variant"] not in drop_ids]
    for vid in drop_ids:
        doc["variants"].pop(vid, None)
    if write:
        store.write_json(BOOKS_FILE, doc)
        for r in rows:
            store.append_jsonl(TRADES_FILE, r)
    obs.log("shadow_lifecycle_cycle", date=date, arms=len(doc["variants"]), closed=len(rows),
            seeded_days=len(seeded_dates), k_lifecycle=doc["k_lifecycle"],
            detail="GÖLGE-v2 KÂĞIT DEFTER — emir/ship yolu YOK")
    return {"trades": rows, "books": doc["variants"], "doc": doc,
            "dropped_arms": dropped, "seeded": seeded_dates}
