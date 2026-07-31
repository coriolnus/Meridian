"""regime.py — tags every trade (trend_up | trend_down | chop | high_vol) and builds the P1
regime.json artifact. With no FMP breadth feed, signals are derived from the index (SPY) itself
and labeled index-derived — an honest proxy, not faked breadth. exposure_budget_pct is a HARD cap
on new risk enforced in guard.py; if 0, no new positions that day."""
from __future__ import annotations
import pandas as pd
from . import indicators as ind

TREND_UP, TREND_DOWN, CHOP, HIGH_VOL = "trend_up", "trend_down", "chop", "high_vol"


# ÇIKARILDI 2026-07-30 (temizlik turu): `_slice(bars, upto_idx)` → `bars.iloc[: upto_idx + 1]`.
# ÇAĞIRAN TARAMASI (meridian/ + tests/): bu modülde de repo genelinde de tek eşleşme tanımın
# kendisiydi ("_slice" araması yalnız `has_slices`/`atr_slice` gibi ALAKASIZ adlara düşüyor).
# NEDEN ÖLÜ: tek satırlık bir dilimleme yardımcısı; `classify` çağıranın verdiği barları OLDUĞU
# GİBİ alır (kırpma çağıranın işidir — look-ahead karantinası `dataset.load`/`on_date` katmanında).
# GERİ-AL: `def _slice(bars, upto_idx): return bars.iloc[: upto_idx + 1]` — bu yorumun yerine.

# Rejim sınıflamasının EN UZUN penceresi: 200 günlük ortalama + onun 20 barlık eğimi.
TREND_WARMUP = 220


def classify(index_bars: pd.DataFrame) -> tuple[str, dict]:
    """Classify the market regime from index bars ending at the last CLOSED bar.
    Returns (regime, metrics).

    ISINMA DOLMADAN TREND SINIFLANMAZ (2026-07-22, sinyal-matematiği turu). Eski kod iki ayrı
    uydurma yapıyordu ve ikisi de "ölçülmemiş bir şeyi ölçülmüş gibi" sunuyordu:
      (1) 200 bar yoksa `sma(close, min(len-1, 150))` hesaplayıp metriklere `"sma200"` ADIYLA
          yazıyordu. 60 barlık bir endeksle `classify` çağrısı `sma200: 113.72` döndürüyordu —
          o sayı 59 BARLIK bir ortalamaydı. Üstelik 50 ile 59 barlık ortalamaların karşılaştırılması
          (`sma50 > sma200`) trend değil GÜRÜLTÜ ölçer.
      (2) 220 bar yoksa `sma200_prev = sma200` atanıyordu; yani "200 günlük ortalama YÜKSELİYOR"
          koşulu (`sma200 >= sma200_prev`) KANIT OLMADAN her zaman doğru oluyordu. Gerçek SPY
          serisinde diğer iki TREND_UP koşulunu sağlayan 3.132 barın 108'inde (%3,4) 200 günlük
          ortalama DÜŞÜYOR — o barlar bu otomatik-geçişle TREND_UP (maruziyet 80) etiketi alırdı.
    exposure_budget_pct SERT bir tavan olduğu için yanlış etiket doğrudan gün içi risk bütçesidir.
    Üretimde endeks ısınması yeterlidir (FETCH_START 2021-01-01 vs IS_START 2022-01-01); yol asıl
    sentetik/kısa endeksli replay'lerde işliyordu — yani KAPININ ölçtüğü dünyada."""
    if index_bars is None or len(index_bars) < TREND_WARMUP:
        # Ölçülebilen ne varsa DÜRÜSTÇE raporlanır; trend etiketi verilmez. CHOP burada "yatay
        # piyasa" değil "trend BİLİNMİYOR" demektir ve reason bunu açıkça söyler (<60 bar için
        # eski dize aynen korunur — tüketicileri var).
        n = 0 if index_bars is None else len(index_bars)
        return CHOP, {"reason": "insufficient index history", "bars": n,
                      "warmup_needed": TREND_WARMUP, "sma50": None, "sma200": None}
    close = index_bars["close"]
    sma50 = ind.sma(close, 50).iloc[-1]
    sma200_series = ind.sma(close, 200)
    sma200 = sma200_series.iloc[-1]
    sma200_prev = sma200_series.shift(20).iloc[-1]
    c = close.iloc[-1]

    atr14 = ind.atr(index_bars, 14).iloc[-1]
    atr_pct = atr14 / c if c else 0.0
    atr_pct_series = (ind.atr(index_bars, 14) / close).dropna()
    hi_vol_thresh = atr_pct_series.quantile(0.80) if len(atr_pct_series) > 30 else atr_pct

    ret20 = close.iloc[-1] / close.iloc[-21] - 1.0 if len(close) > 21 else 0.0

    high_vol = atr_pct >= hi_vol_thresh and atr_pct > 0.0
    if pd.isna(sma50) or pd.isna(sma200) or pd.isna(sma200_prev):
        regime = CHOP
    elif c > sma50 and sma50 > sma200 and sma200 >= sma200_prev:
        regime = TREND_UP
    elif c < sma50 and sma50 < sma200:
        regime = TREND_DOWN
    else:
        regime = CHOP
    if high_vol and regime != TREND_UP:
        regime = HIGH_VOL

    metrics = {
        "close": round(float(c), 2), "sma50": round(float(sma50), 2) if not pd.isna(sma50) else None,
        "sma200": round(float(sma200), 2) if not pd.isna(sma200) else None,
        "atr_pct": round(float(atr_pct), 4), "ret20": round(float(ret20), 4),
        "high_vol": bool(high_vol),
    }
    return regime, metrics


def distribution_days(index_bars: pd.DataFrame, window: int = 25) -> int:
    """IBD-style distribution days proxy: down days (>0.2%) on higher volume than prior day."""
    if len(index_bars) < window + 1:
        return 0
    tail = index_bars.iloc[-window:]
    prev_close = index_bars["close"].shift(1).iloc[-window:]
    prev_vol = index_bars["volume"].shift(1).iloc[-window:]
    down = (tail["close"] / prev_close - 1.0) < -0.002
    heavier = tail["volume"] > prev_vol
    return int((down & heavier).sum())


def follow_through(index_bars: pd.DataFrame) -> bool:
    """FTD proxy: a >1.2% up day on rising volume within the last 5 sessions."""
    if len(index_bars) < 6:
        return False
    tail = index_bars.iloc[-5:]
    prev_close = index_bars["close"].shift(1).iloc[-5:]
    prev_vol = index_bars["volume"].shift(1).iloc[-5:]
    up_strong = (tail["close"] / prev_close - 1.0) > 0.012
    heavier = tail["volume"] > prev_vol
    return bool((up_strong & heavier).any())


def exposure_score(regime: str, metrics: dict) -> int:
    base = {TREND_UP: 80, CHOP: 45, TREND_DOWN: 15, HIGH_VOL: 25}[regime]
    if metrics.get("high_vol") and regime != HIGH_VOL:
        base -= 25
    return max(0, min(100, base))


def sector_momentum(returns_by_ticker: dict, sectors: dict, top: int = 3) -> list:
    """Rank sectors by the mean recent return of their members — leadership from the universe itself
    (no FMP needed). Fills the previously-empty leading_sectors so the operator sees where strength is."""
    from collections import defaultdict
    agg = defaultdict(list)
    for t, r in returns_by_ticker.items():
        if r is not None:
            agg[sectors.get(t, "?")].append(r)
    ranked = sorted(((s, sum(v) / len(v)) for s, v in agg.items() if v), key=lambda x: -x[1])
    return [{"sector": s, "momentum": round(m, 4), "n": len(agg[s])} for s, m in ranked[:top]]


def build_regime_json(index_bars: pd.DataFrame, params: dict, date: str) -> dict:
    """The P1 REGIME artifact. exposure_budget_pct is a hard cap: 0 => no new positions today."""
    regime, metrics = classify(index_bars)
    dd = distribution_days(index_bars)
    ftd = follow_through(index_bars)
    score = exposure_score(regime, metrics)
    if dd >= 5:
        score = max(0, score - 20)  # heavy distribution throttles exposure
    min_exp = int(params.get("regime.min_exposure_score", 40))
    budget = score if score >= min_exp else 0
    breadth = max(0, min(100, int(50 + metrics.get("ret20", 0.0) * 500)))  # index-derived proxy
    out = {
        "date": date, "regime": regime, "breadth_score": breadth, "distribution_days": dd,
        "ftd": ftd, "exposure_budget_pct": budget, "exposure_score": score,
        "min_exposure_score": min_exp, "leading_sectors": [],  # requires FMP sector data
        "source": "index-derived (SPY); FMP breadth/sector feeds inactive until key present",
        "metrics": metrics,
        "rationale": f"{regime}: exposure_score={score} vs min={min_exp} -> budget={budget}%; "
                     f"distribution_days={dd}, ftd={ftd}",
    }
    # --- ÜRETİCİ-TÜKETİCİ PARİTESİ: `entry_gates` (2026-07-31) -------------------------------
    # KUSUR: `guard._y3_entry_gates` Y3'ün iki PİYASA kapısının hükmünü `regime["entry_gates"]`ten
    # OKUYOR (guard.py:418) ama o anahtarı YALNIZ api.py'nin pano yolu (`_y3_gate_row`) üretiyordu.
    # guard'a `regime` olarak verilen sözlük ise HER motorda bu fonksiyonun çıktısıdır
    # (loop.py:529+655, backtest.py:230+323, cf_backfill.py:39+94, shadow_lifecycle.py:444).
    # Yani anahtar yoktu, `eg` None'a düşüyordu ve iki kapı knob AÇILSA BİLE canlı döngüde de
    # replay'de de YAPISAL OLARAK ateşleyemiyordu — kapı yalnız PANODA vardı, KARARDA yoktu.
    # KAPI BURADA YENİDEN HESAPLANMAZ: ortak `entry_gates()` çağrılır, api.py'nin çağrısıyla
    # (`_rg.entry_gates(bars, params)`) BİREBİR aynı imza ve aynı girdilerle — tek yasa, tek yer
    # (denetim turu 12'nin dersi; `leading_sectors` ayrışmasının aynısı, tur 23).
    # PARAMS DÜZLEMİ: kapı, bu fonksiyona ZATEN verilen `params`ı okur — kendine ayrı bir düzlem
    # SEÇMEZ. Canlı döngü ve backtest buraya FLAT params verir (loop.py:529, backtest.py:230),
    # gölge yaşam döngüsü kendi kolunun `eff`ini (shadow_lifecycle.py:444); bu fark ÖNCEDEN VARDI
    # ve `regime.*` anahtarlarında zararsızdır, çünkü guard.py:134-140 `regime.*` knob'larının
    # `@regime` override'ını YAPISAL OLARAK ETKİSİZ ilan edip proposal kapısında REDDEDER (rejim
    # tespiti rejim bilinmeden ÖNCE koşar) — yani iki düzlem bu anahtarlarda ayrışmaz.
    #
    # AYRI BİR "index_bars yok" DALI YOKTUR ve bu bir eksiklik DEĞİL, ölçülmüş bir olgudur:
    #   * `index_bars=None` BU SATIRA ULAŞAMAZ — fonksiyonun BAŞINDAKİ `distribution_days` çağrısı
    #     `len(None)` ile ZATEN TypeError atar (regime.py:84). Buraya savunma kodu yazmak hiç
    #     koşmayacak bir dal ve YANLIŞ bir yorum eklemek olurdu; None'ın çökmesi bu düzeltmenin
    #     kapsamı dışında, ÖNCEDEN VAR OLAN davranıştır.
    #   * ULAŞILABİLİR yetersizlik (boş / 200 bardan kısa endeks) `entry_gates` içinde ZATEN
    #     BEYANLI-None döner: `spy_sma_gate.hukum = None` + `why="ısınma yetersiz (n/200 bar)"`,
    #     `blocks_new_entries=False`. Yani anahtar HER ZAMAN VARDIR ve ölçülemediğinde bunu SÖYLER
    #     — sessiz eksik anahtar (bugünkü kusur) hiçbir yolda geri gelmez. Ölçülemeyen koşul yeni
    #     riski DURDURMAZ; ortak fonksiyonun şekli pano yoluyla birebir aynı kalır.
    out["entry_gates"] = entry_gates(index_bars, params)
    return out


# ==================================================================================================
# Y3 REJİM/RİSK DÖRTLÜSÜ — İKİ PİYASA KAPISI (Hafta 3b, 2026-07-30). HEPSİ VARSAYILAN KAPALI.
# ==================================================================================================
# BEKLENTİ (ROADMAP §3.1 Y3): getiri DEĞİL risk — vol ~-1/3, MaxDD ~yarı. Bu yüzden dördü de
# "kâr getirir" iddiasıyla değil "düşüşü kısar" iddiasıyla gelir ve ikisi de ÖLÇÜMDEN geçecek
# (gölge-varyant / prescreen). Bugün hiçbiri açık değil: knob satırı bounds.yaml'da var,
# strategy.yaml onları TAŞIMIYOR, dolayısıyla canlı etkileri SIFIRDIR (Batch L deseni).
#
# İKİSİ DE YALNIZ YENİ GİRİŞİ KAPATIR — ZORLA TASFİYE YOKTUR. Sebebi ölçülebilirlik: zorla tasfiye
# açık pozisyonların ömrünü kesip defterin çıkış istatistiğini bozar ve "kapı mı işe yaradı, çıkış
# mı" sorusu bir daha ayrıştırılamaz. Kapı yeni riski durdurur; mevcut pozisyon kendi kuralıyla ölür.

SPY_SMA_GATE_WINDOW = 200      # 200 günlük ortalama — literatürün en belgeli trend filtresi
VIX_BACKWARDATION_MIN = 1.0    # VIX/VIX3M bu oranın ÜSTÜ = backwardation (akut stres)

# VIX/VIX3M VERİ KAYNAĞI: DOĞRULANDI ve YOK (2026-07-30). UYDURMA YASAĞI gereği knob AÇILAMAZ.
#   * Massive endeks uçları (`/v2/aggs/ticker/I:VIX/...`, `I:VIX3M`): HTTP 403 NOT_AUTHORIZED
#     ("You are not entitled to this data") — plan endeks verisini kapsamıyor.
#   * FMP `quote`: `^VIX`, `VIX`, `^VIX3M`, `VIX3M` dört varyantın DÖRDÜ de BOŞ liste döndürdü.
# Sonuç: knob satırı bounds.yaml'a İNER (arama uzayında yerini alsın, ölçüm yolu hazır olsun) ama
# kapı `veri_yok` beyanıyla DEVRE DIŞI kalır ve hiçbir koşulda karar üretmez. Bir gün kaynak
# geldiğinde tek değişiklik `vix_term_structure()`ın gerçek bir sağlayıcıya bağlanmasıdır.
VIX_DATA_STATUS = {
    "available": False, "reason": "veri_yok",
    "dogrulama_ts": "2026-07-30",
    "massive": "HTTP 403 NOT_AUTHORIZED (I:VIX, I:VIX3M) — plan endeks verisini kapsamıyor",
    "fmp": "quote ^VIX / VIX / ^VIX3M / VIX3M → dördü de BOŞ liste",
    "sonuc": ("knob bounds'a indi ama kapı DEVRE DIŞI; oran UYDURULMAZ, türev bir vekil "
              "(ör. SPY ATR yüzdeliği) VIX vade yapısı ADIYLA sunulmaz"),
}


def vix_term_structure() -> dict:
    """VIX/VIX3M oranı — BUGÜN ÖLÇÜLEMEZ (kaynak yok, bkz. VIX_DATA_STATUS).

    Fonksiyon VAR çünkü kapının yolu tam olsun ve bir gün kaynak geldiğinde tek nokta değişsin.
    `oran: None` döner ve `veri_yok` der. YAKIN BİR VEKİL DÖNDÜRMEZ: SPY ATR yüzdeliği ile VIX vade
    yapısı FARKLI şeylerdir ve birini diğerinin adıyla sunmak tam olarak uydurmadır."""
    return {"oran": None, "vix": None, "vix3m": None, **VIX_DATA_STATUS}


def spy_sma_gate(index_bars, params: dict | None = None) -> dict:
    """SPY 200-SMA YENİ-GİRİŞ KAPISI — varsayılan KAPALI (`regime.spy_sma_gate` = 0).

    Açıkken: endeksin kapanışı 200 günlük ortalamanın ALTINDAysa YENİ giriş kapanır
    (`blocks_new_entries: True`). Açık pozisyonlara DOKUNULMAZ.

    Isınma dolmadan kapı KARAR VERMEZ: 200 barlık bir ortalama 150 bardan hesaplanıp "sma200" adıyla
    sunulamaz (classify'ın 2026-07-22'de düzelttiği uydurmanın aynısı). Isınma yoksa kapı `None`
    hükmüyle döner ve `blocks_new_entries` FALSE kalır — ölçülemeyen bir koşul yeni riski durdurmaz
    (muhafazakâr taraf BURADA kapıyı kapatmak DEĞİL: kapatmak, ölçüm olmadan davranışı değiştirmek
    olurdu ve knob'un ölçülmesini imkânsızlaştırırdı)."""
    on = bool(int((params or {}).get("regime.spy_sma_gate", 0) or 0))
    out = {"knob": "regime.spy_sma_gate", "enabled": on, "window": SPY_SMA_GATE_WINDOW,
           "blocks_new_entries": False, "close": None, "sma": None,
           "forced_liquidation": False,
           "rol": "YENİ GİRİŞ kapısı — zorla tasfiye YOK; açık pozisyon kendi kuralıyla kapanır"}
    if index_bars is None or len(index_bars) < SPY_SMA_GATE_WINDOW:
        out["hukum"] = None
        out["why"] = (f"ısınma yetersiz ({0 if index_bars is None else len(index_bars)}/"
                      f"{SPY_SMA_GATE_WINDOW} bar) — kapı KARAR VERMEZ")
        return out
    close = index_bars["close"]
    sma = ind.sma(close, SPY_SMA_GATE_WINDOW).iloc[-1]
    c = close.iloc[-1]
    if pd.isna(sma):
        out["hukum"] = None
        out["why"] = "200-SMA NaN — kapı KARAR VERMEZ"
        return out
    alti = bool(c < sma)
    out.update({"close": round(float(c), 2), "sma": round(float(sma), 2),
                "hukum": "altinda" if alti else "ustunde",
                "blocks_new_entries": bool(on and alti),
                "why": (f"kapanış {c:.2f} vs {SPY_SMA_GATE_WINDOW}-SMA {sma:.2f}"
                        + ("" if on else " — knob KAPALI, hüküm yalnız kayda geçer"))})
    return out


def vix_backwardation_gate(params: dict | None = None) -> dict:
    """VIX>VIX3M AKUT ANAHTARI — varsayılan KAPALI ve bugün AYRICA veri-yok.

    İki ayrı kilit vardır ve ikisi de bağımsız: (1) knob kapalı, (2) veri kaynağı doğrulandı ve YOK.
    Knob açılsa bile kaynak gelmedikçe kapı karar VERMEZ — sessizce "stres yok" demez, `veri_yok`
    der. Sessiz bir False, tam olarak "ölçülmemiş bir şeyi ölçülmüş gibi sunmak"tır."""
    on = bool(int((params or {}).get("regime.vix_backwardation_gate", 0) or 0))
    ts = vix_term_structure()
    return {"knob": "regime.vix_backwardation_gate", "enabled": on,
            "esik": VIX_BACKWARDATION_MIN, "oran": ts["oran"],
            "veri": {k: ts[k] for k in ("available", "reason", "massive", "fmp", "dogrulama_ts")},
            "blocks_new_entries": False,      # kaynak yokken HİÇBİR koşulda True olamaz
            "forced_liquidation": False,
            "hukum": None,
            "why": ("VIX/VIX3M kaynağı DOĞRULANDI ve YOK (Massive 403, FMP boş) — kapı devre dışı; "
                    "oran uydurulmaz" if not ts["available"] else
                    ("backwardation" if (ts["oran"] or 0) > VIX_BACKWARDATION_MIN else "normal")),
            "rol": "YENİ GİRİŞ kapısı — zorla tasfiye YOK"}


def entry_gates(index_bars, params: dict | None = None) -> dict:
    """Y3'ün iki piyasa kapısının BİRLEŞİK hükmü — guard/loop giriş zincirinin okuduğu tek yer.

    `blocks_new_entries` yalnız AÇIK bir knob ve ÖLÇÜLMÜŞ bir koşulla True olur. Hangi kapının
    bloke ettiği `blocking` listesinde ADIYLA görünür — "yeni giriş yok" cümlesinin sebebi
    kaybolmasın (bugüne kadar exposure_budget %0 dışında bir sebep yoktu ve o da kaydediliyordu)."""
    sma = spy_sma_gate(index_bars, params)
    vix = vix_backwardation_gate(params)
    blocking = [g["knob"] for g in (sma, vix) if g.get("blocks_new_entries")]
    return {"blocks_new_entries": bool(blocking), "blocking": blocking,
            "spy_sma_gate": sma, "vix_backwardation_gate": vix,
            "forced_liquidation": False,
            "beyan": ("Y3 dörtlüsünün iki PİYASA kapısı; ikisi de default-off ve ölçümden geçmeden "
                      "açılmaz. Zorla tasfiye YOKTUR.")}
