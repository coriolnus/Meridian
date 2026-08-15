"""regime.py — endeks (SPY) barlarından piyasa rejimi sınıflaması ve günlük rejim artefaktı.

Ne yapar: kapalı endeks barlarından rejimi (trend_up | trend_down | chop | high_vol) sınıflar,
dağıtım-günü ve follow-through vekillerini sayar, sektör momentumunu evrenin kendisinden
sıralar ve build_regime_json ile günün rejim çıktısını kurar. exposure_budget_pct SERT bir
yeni-risk tavanıdır ve guard.py'de uygulanır; 0 ise o gün yeni pozisyon açılmaz. Genişlik
(breadth) beslemesi olmadığından tüm sinyaller endeks-türevi vekildir ve öyle etiketlenir —
uydurma genişlik yok.

Kilit girişler: classify, distribution_days, follow_through, exposure_score, sector_momentum,
build_regime_json; pano göstergeleri spy_sma_gate, vix_backwardation_gate, vix_term_structure
ve birleşik entry_gates.

Değişmezler: saf hesap — I/O yok, saat yok, ağ yok; yalnız verilen kapalı barları okur,
dilimleme/look-ahead karantinası çağıranın katmanındadır. Isınma (TREND_WARMUP) dolmadan trend
SINIFLANMAZ: eksik pencereyle "sma200" raporlamak uydurmadır; buradaki CHOP "yatay piyasa" değil
"trend BİLİNMİYOR" demektir ve reason bunu söyler. İki piyasa göstergesi (SPY 200-SMA hükmü ve
VIX/VIX3M vade yapısı) ölçülür ve YALNIZ panoda görünür: biri ölçülüp elendi, öteki veri-kilitli;
blocks_new_entries SABİT False'tur, hiçbir karar yoluna girmez ve knob açılsa bile değişmez.
VIX kaynağı doğrulandı ve yok — oran uydurulmaz, yakın bir vekil VIX adıyla sunulmaz.

Okur/yazar: dosya ve ağ erişimi yoktur; rejim sözlüğünü ÜRETİR, kalıcılaştırma çağıranındır."""
from __future__ import annotations
import pandas as pd
from . import indicators as ind

TREND_UP, TREND_DOWN, CHOP, HIGH_VOL = "trend_up", "trend_down", "chop", "high_vol"


# ÇIKARILDI 2026-07-30: `_slice(bars, upto_idx)` → `bars.iloc[: upto_idx + 1]`.
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

    ISINMA DOLMADAN TREND SINIFLANMAZ. Eski kod iki ayrı
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
    """Rejime karşılık gelen 0-100 maruziyet skorunu verir; rejim HIGH_VOL değilken yüksek oynaklık
    ölçülmüşse taban 25 puan düşürülür. Sonuç [0, 100] aralığına kırpılır."""
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
    # --- `entry_gates` ANAHTARI BURADA YAZILMAZ — HÜKÜM: GÖSTERGE, KAPI DEĞİL
    # Bu satır önce üretici-tüketici paritesini kurmak için eklenmişti: `guard` hükmü
    # `regime["entry_gates"]`ten okuyor ama anahtarı yalnız pano yolu üretiyordu (kapı panoda vardı,
    # kararda yoktu). Parite kuruldu ve AYNI GÜN kapının kendisi ÖLÇÜLDÜ: kart EDG-2026-005 arşive
    # düştü — "KAPI AÇILMAZ, pano göstergesi yeter". Dolayısıyla doğru düzeltme paritenin diğer
    # ucundan gelir: tüketici kaldırıldı (guard `_y3_portfolio_caps` docstring'i), üretici de
    # kaldırılır. YASA 6 (okuyucusuz yazım yok) bunu ZORUNLU kılar: guard okumayı bıraktıktan sonra
    # `regime.json`daki bu anahtarın üretim tüketicisi kalmaz — yazmaya devam etmek, her gün her
    # motorda hesaplanan ve kimsenin okumadığı bir alan bırakmak olurdu.
    # HÜKÜM ÖLMEDİ, YERİ DEĞİŞTİ: `entry_gates()` hâlâ ölçer; TEK tüketicisi pano satırıdır
    # (`api._y3_gate_row` → `y3_entry_gates`). Yani SPY 200-SMA hükmü GÖRÜNÜR, hiçbir karara GİRMEZ.
    # GERİ ALMA: kapı yeni bir kartla açılacaksa üç yer BİRLİKTE değişir — (a) `entry_gates`in sabit
    # `blocks_new_entries=False`i, (b) bu satır, (c) guard'daki tüketici. İkisi eksik hâli tam olarak
    # bu turda temizlenen ölü-uçtu.
    return out


# ==================================================================================================
# Y3 REJİM/RİSK DÖRTLÜSÜ — İKİ PİYASA GÖSTERGESİ
# ==================================================================================================
# HÜKÜM (kart arşiv): bu bölümün İKİ PİYASA KAPISI ARTIK KAPI DEĞİL, GÖSTERGEdir.
# SPY 200-SMA kapısı ölçüldü ve kill#1 tetiklendi (tek atfedilebilir pencerede Sharpe −0,25→−0,90,
# PARA-v3 −0,029→−0,088; vol anlamlı düşüyor ama bedeli getiri) — OOS'ta 55 bloke günde 0 giriş
# engelledi, yani kill#2'nin "pano göstergesi yeter" hükmü fiilen geçerli. VIX bacağı ise doğrulanmış
# VERİ-YOK. İkisinin de hükmü ÖLÇÜLÜR ve PANODA görünür; hiçbiri karar yoluna girmez (tüketici
# guard'dan, üretici `build_regime_json`dan kaldırıldı — bkz. o iki gövdedeki geri-alma notu).
# BEKLENTİ: getiri DEĞİL risk — vol ~-1/3, MaxDD ~yarı. Bu yüzden dördü de
# "kâr getirir" iddiasıyla değil "düşüşü kısar" iddiasıyla gelir ve ikisi de ÖLÇÜMDEN geçecek
# (gölge-varyant / prescreen). Bugün hiçbiri açık değil: knob satırı bounds.yaml'da var,
# strategy.yaml onları TAŞIMIYOR, dolayısıyla canlı etkileri SIFIRDIR (Batch L deseni).
#
# ZORLA TASFİYE YOKTUR VE ARTIK YENİ GİRİŞ DE KAPANMAZ. Tasfiye yasağının gerekçesi ölçülebilirlikti
# (zorla tasfiye açık pozisyonların ömrünü kesip defterin çıkış istatistiğini bozar ve "kapı mı işe
# yaradı, çıkış mı" sorusu bir daha ayrıştırılamaz); yeni-giriş kapatma ise ÖLÇÜLDÜ ve ELENDİ.
# Geriye ölçülen ve gösterilen bir hüküm kalır.

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


# KARARIN MAKİNE-OKUNUR HÂLİ. Metin çıktının içinde durur (pano ve beyin koda inmeden
# "bu satır neden karar vermiyor?" sorusunu cevaplayabilmeli) ve hükmün adresi kartın kendisidir.
SPY_SMA_EMEKLI = {
    "karar": "EDG-2026-005", "tarih": "2026-07-31", "durum": "arşiv",
    "hukum": "KAPI AÇILMAZ — pano göstergesi yeter",
    "kanit": ("tek atfedilebilir pencerede (IS 2022-24) kill#1: Sharpe −0,254→−0,898, "
              "PARA-v3 −0,029→−0,0878; vol anlamlı düşüyor (oran 0,792) ama bedeli getiri. "
              "OOS'ta 55 bloke günde 0 giriş engellendi (doğrudan etki TAM SIFIR)"),
}


def spy_sma_gate(index_bars, params: dict | None = None) -> dict:
    """SPY 200-SMA HÜKMÜ — **PANO GÖSTERGESİ, KAPI DEĞİL**.

    Endeksin kapanışı 200 günlük ortalamanın altında mı üstünde mi — ÖLÇÜLÜR ve gösterilir.
    Hiçbir karar yoluna GİRMEZ: `blocks_new_entries` SABİT False'tur ve `regime.spy_sma_gate`
    knob'u 1 verilse bile bu değişmez. Sebep ölçümdür, tercih değil: kart EDG-2026-005 ölçüldü,
    kill#1 tetiklendi ve "pano göstergesi yeter" hükmüyle arşive düştü (ayrıntı `SPY_SMA_EMEKLI`).
    Knob'un adı çıktıda KALIR — hükmü hangi düğmenin taşıdığı, düğme emekli olduktan sonra da
    okunabilir olmalı.

    ARAMA UZAYI HALKASI DA KAPANDI (8b6bbbc): `state/bounds.yaml`daki
    `regime.spy_sma_gate` satırı DÜŞTÜ — makine bu adı artık hiç örneklemez (satır dururken altı
    değerlendirme, sonucu yapısal olarak sabit bir eksene harcanmıştı). Bu docstring daha önce
    "satır düşürülene dek makine o adı hâlâ örnekleyebilir" diyordu; doğru görünen ama
    GERÇEĞE UYMAYAN bir cümleydi. Bugünkü durum: satırın yerinde bounds.yaml'da bir MEZAR TAŞI
    yorumu var (nereye emekli olduğu + hüküm kaynağı + çivilerin adresi); sessiz-diriliş çivileri
    `tests/test_altyapi_kucukler_v172.py` (satır GERİ GELEMEZ) ve `tests/test_hafta3b_v125.py`
    (satır geri gelse DAHİ karar yolu değişmez — ikinci savunma hattı) dosyalarında.

    Isınma dolmadan hüküm ÜRETİLMEZ: 200 barlık bir ortalama 150 bardan hesaplanıp "sma200" adıyla
    sunulamaz (classify'ın düzelttiği uydurmanın aynısı). Isınma yoksa `hukum` BEYANLI
    None döner — sessiz bir "ustunde" değil."""
    istendi = bool(int((params or {}).get("regime.spy_sma_gate", 0) or 0))
    out = {"knob": "regime.spy_sma_gate", "enabled": False, "window": SPY_SMA_GATE_WINDOW,
           # SABİT False — hesaplanmıyor. Bu alanı yeniden HESAPLANIR yapmak kapıyı geri açmaktır ve
           # tek başına yetmez de: üretici + tüketici de geri gelmeli (bkz. build_regime_json).
           "blocks_new_entries": False, "close": None, "sma": None,
           "forced_liquidation": False, "knob_emekli": SPY_SMA_EMEKLI,
           "rol": "PANO GÖSTERGESİ — kapı DEĞİL; hiçbir karar yoluna girmez (EDG-005)"}
    # Knob AÇIK istenmişse bu SESSİZ KALMAZ: "1 yazdım ama hiçbir şey olmadı" sessizliği, bu turda
    # temizlenen ölü-ucun tam olarak yaşattığı deneyimdi.
    emekli_notu = (" — knob 1 verildi ama EMEKLİ (EDG-005): hüküm karara GİRMEZ" if istendi
                   else " — hüküm yalnız panoda görünür")
    if index_bars is None or len(index_bars) < SPY_SMA_GATE_WINDOW:
        out["hukum"] = None
        out["why"] = (f"ısınma yetersiz ({0 if index_bars is None else len(index_bars)}/"
                      f"{SPY_SMA_GATE_WINDOW} bar) — hüküm ÜRETİLMEDİ")
        return out
    close = index_bars["close"]
    sma = ind.sma(close, SPY_SMA_GATE_WINDOW).iloc[-1]
    c = close.iloc[-1]
    if pd.isna(sma):
        out["hukum"] = None
        out["why"] = "200-SMA NaN — hüküm ÜRETİLMEDİ"
        return out
    out.update({"close": round(float(c), 2), "sma": round(float(sma), 2),
                "hukum": "altinda" if bool(c < sma) else "ustunde",
                "why": (f"kapanış {c:.2f} vs {SPY_SMA_GATE_WINDOW}-SMA {sma:.2f}" + emekli_notu)})
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
            # `enabled` knob'u OLDUĞU GİBİ yansıtır (SMA bacağından farklı olarak): bu knob EMEKLİ
            # DEĞİL, VERİ-KİLİTLİ. Ayrım önemli — biri ölçüldü ve elendi, öteki hiç ölçülemedi.
            # Kaynak geldiği gün kapı YİNE DE kendiliğinden açılmaz: kablo (üretici+tüketici) da
            # kaldırıldığı için önce yeni bir kart, sonra üç noktalı geri-alma gerekir.
            "rol": "PANO GÖSTERGESİ — kapı DEĞİL; veri gelse bile kablo yeniden kurulmadan karar vermez"}


def entry_gates(index_bars, params: dict | None = None) -> dict:
    """Y3'ün iki piyasa GÖSTERGESİNİN birleşik hükmü — TEK tüketicisi pano satırı (`api._y3_gate_row`).

    ADI TARİHSEL, ANLAMI DEĞİL: bu sözlük önceden guard'ın giriş zincirinde okunuyordu;
    arşiv kartının hükmüyle (kapı açılmaz, pano göstergesi yeter) tüketici de üretici de kaldırıldı. Ad
    korundu çünkü panonun sözleşmesi (`y3_entry_gates`) ve kartların/raporların atıfları bu ad
    üzerinden yazılı — iki ad iki gerçek riskini yeniden doğurmamak için burada TEK ad, tek yer.

    `blocks_new_entries` ARTIK HESAPLANMAZ, SABİT False'tur ve `blocking` sabit boştur. Bunları
    alt göstergelerden yeniden türetmek, hükmü tek bir alan değişikliğiyle sessizce diriltilebilir
    bırakırdı; bu depoda "açılabilir duran kapı" ile "açık kapı" arasındaki fark bir gözden kaçırma
    kadar incedir. Alanlar SİLİNMEZ çünkü panonun okuduğu şekil budur (YASA 6: tüketicisi var)."""
    sma = spy_sma_gate(index_bars, params)
    vix = vix_backwardation_gate(params)
    return {"blocks_new_entries": False, "blocking": [],
            "spy_sma_gate": sma, "vix_backwardation_gate": vix,
            "forced_liquidation": False,
            "karar_yolu": False,
            "beyan": ("EDG-005 hükmü: GÖSTERGE, KAPI DEĞİL. İki piyasa hükmü ölçülür ve panoda "
                      "görünür; hiçbiri yeni girişi kapatmaz ve zorla tasfiye YOK (hiç olmadı). "
                      "SMA bacağı ÖLÇÜLDÜ ve elendi (kart arşiv), VIX bacağı veri-kilitli."),
            "emekli": SPY_SMA_EMEKLI}
