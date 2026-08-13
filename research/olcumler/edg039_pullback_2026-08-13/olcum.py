"""EDG-2026-039 — PULLBACK SİLAHSIZLANMA (C+mb − pullback) · ölçüm aracı (2026-08-13)

Kart: research/cards/EDG-2026-039-pullback-silahsizlanma.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ,
repo koduna DOKUNMAZ (strategy.py dahil — kart kill#2).

ŞASİ: research/olcumler/edg032b_tamsatir_2026-08-13/olcum.py AYNEN DEVRALINDI (C+mb @5R dünyası:
rampa kablolu 15/36, slot 20, 0,5R, zarf 5R, mb ARMED'da; seed 20260812; sha-pinli). Devralınan
her şey aynı: izole sandbox (EDG-022 DONMUŞ config kopyaları + salt-okunur bars symlink), kayıt
kancaları, bütünlük kontrolleri, rampa-kablolu kanıtı, mb-ARMED kanıtı, slim+tam defter yazımı.
TABAN yeniden koşulmaz: `edg032b/islemler_tam_kontrol.json` (885 satır, sha256 46ebeb48…674874).

TEK DEĞİŞKEN (bu kartın tüm işi): ARMED_SETUPS'tan `pullback` ÇIKARILIR.

KANAL SEÇİMİ (BEYANLI) — niçin monkeypatch, niçin BU nokta:
  * Mevcut yüzey EKLEME yönünde: `strategy.scan_entry` (strategy.py:1061-1072) her ticker'da
    `scan_all` çağırır, sonra `for setup in ARMED_SETUPS + extra` sırasıyla İLK eşleşeni döner;
    `extra = params["entry.armed_extra"]` (EDG-025/032'nin ölçüm kanalı). ÇIKARMA yüzeyi YOK:
    `armed_eksi` diye bir param anahtarı repo kodunda MEVCUT DEĞİL (grep: sıfır geçiş).
  * Bir `entry.armed_eksi` kanalı AÇMAK strategy.py'yi DEĞİŞTİRMEK demekti → kart kill#2
    ("ARMED kümesi enjeksiyonu strategy.py'yi DEĞİŞTİRİYORSA geçersiz"). Bu yol REDDEDİLDİ.
  * Modül sabitini (`strat.ARMED_SETUPS`) koşum boyunca yeniden bağlamak da REDDEDİLDİ: sabit
    replay dışında da okunuyor (watchdog/arming/skills/cf) ve "koşum sırasında sabit oynatıldı"
    kaydı ölçümün kendi bütünlük kanıtını zayıflatırdı (kart öz-sınama (c) tam bunu yasaklıyor).
  * SEÇİLEN: kartın adıyla önerdiği ikinci yol — ARMED KÜMESİNİN TAMAMINI PARAM OLARAK GEÇEN
    BEYANLI MONKEYPATCH, TEK KANONİK NOKTADA: `strategy.scan_entry`. Bu nokta kanonik çünkü
    replay yolunda ARMED_SETUPS'ın TEK okuyucusu odur (backtest.py:329 → scan_entry; broker/
    backtest başka yerde okumaz — cf_backfill/loop/shadow_variants replay'de İTHAL EDİLMEZ).
  * KANUN ÇAĞRILIR, KOPYALANMAZ: sarmalayıcı taramayı `strat.scan_all`a yaptırır (motorun kendi
    yasası), yalnız "hangi kurulum silahlı" ÖNCELİK DÖNGÜSÜNÜ param kümesinden okur. Kopyalanan
    tek şey 3 satırlık seçim döngüsüdür ve taban kümesiyle çağrıldığında ÖZDEŞ davranır
    (koşum-içi çağrı-başı assert + tam pencerede BAYT-ÖZDEŞLİK kapısı ile kanıtlanır).

ÖZ-SINAMA (kart şartı; üçü de assert'li, kanıtı `kanal_<run>.json` + sonuc["kanal"]):
  (a) pullback sinyali üreten barda kurulum SİLAHLANMIYOR — ön-uçuşta sentetik `scan_all` ile
      (pullback-tek → None; pullback+mb → mb), koşum-içinde GERÇEK barlarda sayaçla
      (`taban_pullback_secti_n` > 0 ve bu çağrıların hepsinde hücre farklı/None döndü).
  (b) diğer üç kurulum etkilenmiyor — ÇAĞRI BAŞINA değişmez: taban seçimi `pullback` DEĞİLSE
      hücre seçimi AYNI NESNE olmak zorunda (assert; ihlal sayacı 0 raporlanır).
  (c) ARMED_SETUPS modül sabiti koşum sonrası DEĞİŞMEMİŞ — tuple kimliği + değeri + strategy.py
      sha256/mtime (kill#3) koşum öncesi/sonrası kıyaslanır.

KANAL-NÖTRLÜĞÜ KAPISI (`notrluk`): `taban` koşumu AYNI sarmalayıcıdan TAM ARMED kümesiyle geçer;
slim islemler + seanslar dosyaları edg032b `kontrol` çıktılarıyla BAYT-ÖZDEŞ olmak ZORUNDA.
Düşerse kanal dünyayı değiştirmiş demektir → ölçüm DURUR (exit 2).

KIYAS (`kiyas`): hücre ↔ taban (edg032b hazır çıktıları, salt-okunur). Eşlenik ay-kümeli
bootstrap (5000, seed 20260812; aynı ay çekilişi İKİ koşuma birden) ile Δn, ΔP&L, Δsharpe,
Δmaxdd CI'ları; işlem-kümesi eşlemesi (ÇIKAN/EKLENEN/ORTAK) ve SENTE KAPANAN P&L ayrıştırması;
EDG-030 desenli YAN-KANAL AYRIŞTIRMASI (serbest kalan slot/ısı → hangi kurulumlar doldurdu);
kurulum kırılımı yan yana; kart başarı ölçütünün MEKANİK işareti (hüküm DEĞİL).

TANIMLAR (032b/030 şasi tanımları AYNEN): seans, ay kümesi = ts_open[:7], eşlenik ay-kümeli
bootstrap (5000, seed 20260812), max-dd = score.score_detail.max_drawdown (kanonik).

KILL KONTROLLERİ:
  kill#1 şasi bütünlüğü: frame_miss/dup/scan!=plan/yasak-modül/base_max bozuk → GEÇERSİZ.
  kill#2 kanal        : repo koduna dokunulduysa (motor sha/mtime değişimi ∨ ARMED_SETUPS
                        sabiti değişmiş ∨ kanal-nötrlüğü düştü) → GEÇERSİZ.
  kill#3 taban defteri: taban defterde `pullback` 6 işlem bulunamazsa (sha uyuşmazlığı) GEÇERSİZ.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli); YASA-6
(okuyucu: sonuc_*.json + kanal_*.json + notrluk.json + kiyas → dönüş raporu + Rol-1).
SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar sembolik bağla SALT-OKUNUR; canlı
state'e ve motor dosyalarına tek bayt yazılmaz. meridian.loop / counterfactual / cf_backfill /
hermes İTHAL EDİLMEZ — sys.modules ile kanıtlanır.

KULLANIM:
  olcum.py taban  [--smoke]      # kanal-nötrlüğü kolu (TAM ARMED kümesi, aynı sarmalayıcı)
  olcum.py eksipb [--smoke]      # HÜCRE: C+mb − pullback
  olcum.py notrluk [--smoke]     # kanal-nötrlüğü kapısı (taban ↔ edg032b kontrol bayt-özdeş)
  olcum.py kiyas  [--smoke]      # hücre ↔ taban kıyası + yan-kanal ayrıştırması → sonuc.json
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
REPO = SANDBOX.parents[2]                      # research/olcumler/<bu>/ -> repo kökü
EDG022 = REPO / "research/olcumler/edg022_evren_kisit_2026-08-09"
EDG032 = REPO / "research/olcumler/edg032_final_paket_2026-08-12"
EDG032B = REPO / "research/olcumler/edg032b_tamsatir_2026-08-13"     # TABAN (hazır; yeniden koşulmaz)
# kart kill#3 çivisi: taban tam-satır defterinin sha256'sı (brief'te verilen künye)
TABAN_TAM_SHA = "46ebeb48a8d35bc421b49f51f1996ea0c2d69563dc39a7b825c7d4dea7674874"

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # 032/026 penceresi AYNEN
BOOT_SEED = 20260812
BOOT_ITER = 5000

# merkez (C+mb) — 032b-kontrol dünyası AYNEN; bu kartta SAPMA YOK (tek hücre)
MERKEZ = {"slot": 20, "size": 0.5, "zarf": None}     # zarf None = DOKUNULMAZ (5.0 assert'lenir)
HUCRELER = {
    # kanal-nötrlüğü kolu: AYNI sarmalayıcı, TAM ARMED kümesi → edg032b kontrol ile BAYT-ÖZDEŞ olmalı
    "taban": {"armed_cikar": ()},
    # TEK HÜCRE: C+mb − pullback
    "eksipb": {"armed_cikar": ("pullback",)},
}

# ÖLÇÜM-YEREL param anahtarı. Repo kodu bu anahtarı OKUMAZ (grep: sıfır geçiş) — okuyan tek yer
# aşağıdaki BEYANLI sarmalayıcıdır. `entry.armed_extra` (repo kanalı, EKLEME yönü) DOKUNULMADAN
# durur ve sarmalayıcı onu da hesaba katar (taban küme = ARMED_SETUPS + armed_extra).
ARMED_KUME_PARAM = "entry.armed_kume"

# canlı `trades` şeması — storage.py:82-95 tipli kolonlar (25) + skill_chain (extra_json) = 26.
# EDG-036 `sema_uyumu.canli_trades_alanlari` ile birebir aynı liste (sıralı kıyas assert'i altında).
CANLI_SEMA = ("bars_held", "costs", "entry", "exit", "exit_reason", "exploration", "id", "kaynak",
              "mae_r", "mfe_r", "plan_id", "pnl_dollars", "pnl_pct", "qty", "r_multiple",
              "r_multiple_expected", "regime", "scaled_out", "score", "setup", "side",
              "skill_chain", "strategy_version", "ticker", "ts_close", "ts_open")
# replay defterinin ÜRETMEDİĞİ, yazarın bastığı prosedürel damgalar (ledgerstamp.py / yazar yolu)
PROSEDUREL_DAMGA = {
    "kaynak": ("ledgerstamp.stamp() ürünü — `loop._persist_trade`→live_paper, `run.replay_seed`→"
               "replay_seed (broker.py:666-667). Üretici satıra damga BASMAZ: satırın nereye "
               "yazıldığını bilen katman basar. Replay çıktısında YAPISAL OLARAK YOK."),
    "id": ("broker._id sayacı (T00001…) — koşum-içi sıra numarası. Replay ÜRETİR ama defter "
           "kimliği değildir: canlı deftere yazılırken yazarın sayacıyla yeniden basılır."),
    "strategy_version": ("plan['strategy_version'] üzerinden taşınır; replay DONMUŞ sandbox "
                         "strategy.yaml sürümünü (v3) yazar. Tohum partisinin sürüm damgası "
                         "prosedürdür (kart aşama-2) — replay'in ürettiği değer o damga DEĞİLDİR."),
}

ZARF_MERKEZ = 5.0                              # frozen goal beklenen zarf (assert)
RAMPA_BEKLENEN = {"full_dd": 0.15, "floor_dd": 0.36}   # kablolu fail-safe = C+mb rampası
ARMED_BEKLENEN = ("breakout_vcp", "pullback", "exhaustion_hammer", "momentum_burst")

KAPI_DD_KATSAYI = 1.3
KAPI_SHARPE_MIN = 0.20

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")
MOTOR_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py",
                  "config.py", "dataset.py", "score.py", "regime.py")

# NO_GO/REVIEW neden eşlemesi (şasi AYNEN)
NEDEN_ESLEME = [
    ("heat_hard", "portföy ısısı sert tavanı"),
    ("max_open_positions", "pozisyon dolu"),
    ("sector_cap", "sektör tavanı"),
    ("rr_floor", "yetersiz ödül/risk"),
    ("exposure_budget", "exposure_budget"),
    ("daily_loss_breaker", "devre kesici"),
    ("position_size", "boyut "),
    ("heat_review", "portföy ısısı yüksek"),
    ("sector_stacking", "korelasyon yığılması"),
    ("correlation", "yüksek korelasyon"),
    ("leading_sector", "lider sektörlerinde değil"),
    ("rr_marginal", "marjinal"),
    ("rr_defined", "R:R belirsiz"),
    ("score_band", "skor alt bantta"),
    ("earnings_coverage_note", "kazanç kapsamı"),
]


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _motor_kunye() -> dict:
    """kill#3 parmak izi: motor dosyaları sha256 + mtime_ns (033 dersi)."""
    out = {}
    for f in MOTOR_DOSYALAR:
        p = REPO / "meridian" / f
        try:
            st = p.stat()
            out[f] = {"sha256_16": _sha(p), "mtime_ns": st.st_mtime_ns}
        except OSError:
            out[f] = {"sha256_16": None, "mtime_ns": None}   # ölçülemedi
    return out


def _neden_dagit(nedenler_listesi) -> dict:
    c: dict[str, int] = {}
    for neden in nedenler_listesi:
        ad = None
        for kontrol, parca in NEDEN_ESLEME:
            if parca in neden:
                ad = kontrol
                break
        c[ad or f"HAM:{neden[:80]}"] = c.get(ad or f"HAM:{neden[:80]}", 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — izole state (EDG-022 DONMUŞ kopyaları; 026/032 şasisi AYNEN)
# ---------------------------------------------------------------------------------------------
def hazirla(run: str) -> pathlib.Path:
    st = SANDBOX / f"state_{run}"
    st.mkdir(exist_ok=True)
    (st / "history").mkdir(exist_ok=True)
    bars = st / "bars"
    if not bars.exists():
        bars.symlink_to(REPO / "state" / "bars")          # SALT-OKUNUR canlı önbellek
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        dst = st / f
        if not dst.exists():
            # kaynak = EDG-022 DONMUŞ kopyaları (026/032/C ile aynı kaynak — tutarlılık çivisi).
            # DOSYALAR DEĞİŞTİRİLMEZ: enjeksiyonlar YÜKLENMİŞ sözlüklere yapılır ki config
            # sha'ları 032 kaydıyla bayt-aynı kalsın (şasi kimliği sha ile kanıtlanır).
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# SINIFLAMA + BOOTSTRAP + ISI — şasi fonksiyonları AYNEN (032)
# ---------------------------------------------------------------------------------------------
def classify(rec: dict, no_trade_before: int) -> str:
    acik_slot = rec["acik_slot"]
    if acik_slot <= 0:
        return "tavan_sifir"
    if rec["bar_i"] is not None and rec["bar_i"] < no_trade_before:
        return "isinma"
    if (rec["exposure_budget_pct"] or 0) <= 0:
        return "rejim_kapali"
    return "evren_bagladi" if rec["aday_n"] <= acik_slot else "derisk_bagladi"


def bootstrap_ci(sess: list[dict], siniflar: list[str], n_iter: int = BOOT_ITER,
                 seed: int = BOOT_SEED) -> dict:
    import numpy as np
    rng = np.random.default_rng(seed)
    aylar: dict[str, list[str]] = {}
    for s in sess:
        aylar.setdefault(s["date"][:7], []).append(s["sinif"])
    ay_adlari = list(aylar.keys())
    ay_siniflar = {a: np.array(v) for a, v in aylar.items()}
    m = len(ay_adlari)
    props = {c: np.empty(n_iter) for c in siniflar}
    props["derisk+tavan"] = np.empty(n_iter)
    idx_all = np.arange(m)
    for i in range(n_iter):
        pick = rng.choice(idx_all, size=m, replace=True)
        pooled = np.concatenate([ay_siniflar[ay_adlari[j]] for j in pick])
        tot = len(pooled)
        for c in siniflar:
            props[c][i] = np.count_nonzero(pooled == c) / tot
        props["derisk+tavan"][i] = (np.count_nonzero(pooled == "derisk_bagladi") +
                                    np.count_nonzero(pooled == "tavan_sifir")) / tot
    out = {}
    for c, arr in props.items():
        out[c] = {"lo": round(float(np.percentile(arr, 2.5)), 4),
                  "hi": round(float(np.percentile(arr, 97.5)), 4),
                  "orta": round(float(np.median(arr)), 4)}
    out["_n_ay_kume"] = m
    return out


def _isi_ozet(degerler: list[float]) -> dict | None:
    import numpy as np
    if not degerler:
        return None
    a = np.asarray(degerler, dtype=float)
    hist: dict[str, int] = {}
    for v in a:
        k = f"{round(v * 2) / 2:.1f}"
        hist[k] = hist.get(k, 0) + 1
    return {"max": round(float(a.max()), 3),
            "p50": round(float(np.percentile(a, 50)), 3),
            "p90": round(float(np.percentile(a, 90)), 3),
            "p99": round(float(np.percentile(a, 99)), 3),
            "ort": round(float(a.mean()), 3),
            "sifir_ustu_seans_n": int((a > 0).sum()),
            "n_seans": int(len(a)),
            "histogram_0p5R": dict(sorted(hist.items(), key=lambda kv: float(kv[0])))}


def _islem_araligi_sayimi(islemler: list[dict], takvim: list[str]) -> list[int]:
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


def _setup_ozet(ts: list[dict]) -> dict:
    by: dict[str, dict] = {}
    for t in ts:
        b = by.setdefault(t.get("setup") or "?", {"n": 0, "pnl": 0.0, "sum_r": 0.0, "n_r": 0})
        b["n"] += 1
        b["pnl"] += float(t.get("pnl_dollars") or 0.0)
        if t.get("r_multiple") is not None:
            b["sum_r"] += float(t["r_multiple"])
            b["n_r"] += 1
    return {s: {"n": v["n"], "pnl": round(v["pnl"], 2),
                "avg_r": round(v["sum_r"] / v["n_r"], 4) if v["n_r"] else None}
            for s, v in sorted(by.items())}


# ---------------------------------------------------------------------------------------------
# ARMED KANALI — BEYANLI MONKEYPATCH (tek kanonik nokta: strategy.scan_entry)
# ---------------------------------------------------------------------------------------------
def kur_armed_kanali(strat) -> tuple:
    """`strategy.scan_entry`i, silahlı kurulum kümesini PARAMDAN okuyan bir sarmalayıcıyla
    değiştirir. Döner: (orijinal_fonksiyon, sayaç_sözlüğü).

    NİÇİN BU NOKTA (tek kanonik): replay yolunda ARMED_SETUPS'ın TEK okuyucusu `scan_entry`tir
    (backtest.py:329 onu çağırır; broker/backtest/guard/score ARMED_SETUPS'a hiç bakmaz;
    cf_backfill/loop/shadow_variants ARMED_SETUPS okur AMA replay'de İTHAL EDİLMEZ — YASAK
    listesi + sys.modules assert'i bunu koşumda kanıtlar).

    NE KOPYALANDI, NE ÇAĞRILDI: tarama motorun kendi yasasıyla yapılır (`strat.scan_all` —
    kopyalanmaz, ÇAĞRILIR). Kopyalanan tek şey strategy.py:1069-1072'deki 3 satırlık ÖNCELİK
    döngüsüdür; taban kümesiyle çağrıldığında orijinalle ÖZDEŞ davranır. Bu iddia iki ayrı
    kanıtla çakılıdır: (1) çağrı-başı assert — taban seçimi `pullback` değilse hücre seçimi
    AYNI NESNE; (2) `taban` kolunun TAM pencerede edg032b `kontrol` ile BAYT-ÖZDEŞ çıkması.

    MODÜL SABİTİNE DOKUNULMAZ: `strat.ARMED_SETUPS` okunur, asla yeniden bağlanmaz."""
    orij = strat.scan_entry
    sayac = {
        "cagri_n": 0,
        "taban_sinyal_n": 0,             # taban kümesiyle silahlanacak çağrı sayısı
        "hucre_sinyal_n": 0,             # hücre kümesiyle silahlanan çağrı sayısı
        "taban_pullback_secti_n": 0,     # taban seçimi pullback olan çağrı (öz-sınama (a) tabanı)
        "kesildi_bosa_dustu_n": 0,       # pullback kesildi ve yerine BAŞKA kurulum gelmedi (None)
        "kesildi_yerine_gecen": {},      # pullback kesildi, yerine geçen kurulum sayımı
        "ozsinama_b_ihlal_n": 0,         # taban≠pullback iken hücre farklı döndü (0 OLMALI)
        "ozsinama_b_ihlal_ornek": [],
        "kesilen_ornekler": [],          # (ticker, taban_setup→hücre_setup) ilk 40 kayıt
    }

    def scan_entry_kume(bars, params, rs_rating_value, ticker="?"):
        by_setup = strat.scan_all(bars, params, rs_rating_value, ticker=ticker)   # KANUN ÇAĞRILIR
        taban_kume = tuple(strat.ARMED_SETUPS) + tuple(params.get("entry.armed_extra") or ())
        hucre_kume = params.get(ARMED_KUME_PARAM)
        hucre_kume = taban_kume if hucre_kume is None else tuple(hucre_kume)
        taban_pick = next((by_setup[s] for s in taban_kume if s in by_setup), None)
        pick = next((by_setup[s] for s in hucre_kume if s in by_setup), None)

        sayac["cagri_n"] += 1
        if taban_pick is not None:
            sayac["taban_sinyal_n"] += 1
        if pick is not None:
            sayac["hucre_sinyal_n"] += 1
        if taban_pick is not None and taban_pick.setup == "pullback":
            sayac["taban_pullback_secti_n"] += 1
            yerine = None if pick is None else pick.setup
            if pick is None:
                sayac["kesildi_bosa_dustu_n"] += 1
            else:
                sayac["kesildi_yerine_gecen"][yerine] = \
                    sayac["kesildi_yerine_gecen"].get(yerine, 0) + 1
            if len(sayac["kesilen_ornekler"]) < 40:
                sayac["kesilen_ornekler"].append({"ticker": ticker, "taban": "pullback",
                                                  "hucre": yerine})
        else:
            # ÖZ-SINAMA (b): pullback seçilmediyse hücre AYNI NESNEYİ döndürmek ZORUNDA
            if pick is not taban_pick:
                sayac["ozsinama_b_ihlal_n"] += 1
                if len(sayac["ozsinama_b_ihlal_ornek"]) < 10:
                    sayac["ozsinama_b_ihlal_ornek"].append(
                        {"ticker": ticker,
                         "taban": None if taban_pick is None else taban_pick.setup,
                         "hucre": None if pick is None else pick.setup})
                raise AssertionError(
                    "ÖZ-SINAMA (b) İHLALİ: taban seçimi pullback değilken hücre farklı döndü "
                    f"(ticker={ticker} taban={getattr(taban_pick, 'setup', None)} "
                    f"hucre={getattr(pick, 'setup', None)}) — kanal yan etki üretiyor")
        return pick

    strat.scan_entry = scan_entry_kume
    return orij, sayac


def onucus_ozsinama(strat, cikar: tuple) -> dict:
    """ÖN-UÇUŞ ÖZ-SINAMASI — replay'den ÖNCE, SENTETİK `scan_all` ile (gerçek bar gerekmez).
    Kanal takılıyken `strat.scan_all` geçici olarak sahte bir tabloyla değiştirilir; her senaryoda
    dönen kurulum kontrol edilir. Sahte tarama koşum boyunca DEĞİL, yalnız bu fonksiyon içinde
    takılıdır ve `finally` ile geri alınır (geri alım assert'li)."""
    class _S:                                    # scan_entry yalnız `.setup` okur
        def __init__(self, s):
            self.setup = s

        def __repr__(self):
            return f"<sig {self.setup}>"

    tablo = {}                                   # senaryo adı -> {setup: _S}
    for ad, setler in {
        "yalniz_pullback": ("pullback",),
        "pullback_ve_mb": ("pullback", "momentum_burst"),
        "pullback_ve_eh": ("pullback", "exhaustion_hammer"),
        "breakout_ve_pullback": ("breakout_vcp", "pullback"),
        "yalniz_eh": ("exhaustion_hammer",),
        "yalniz_mb": ("momentum_burst",),
        "yalniz_breakout": ("breakout_vcp",),
        "uyuyan_kurulum": ("episodic_pivot",),   # silahlı değil → her iki kümede de None
        "hicbiri": (),
    }.items():
        tablo[ad] = {s: _S(s) for s in setler}

    orij_scan_all = strat.scan_all
    kume_hucre = tuple(s for s in strat.ARMED_SETUPS if s not in cikar)
    sonuc = {}
    try:
        for ad, by in tablo.items():
            strat.scan_all = (lambda by_=by: (lambda *a, **kw: dict(by_)))()
            taban = strat.scan_entry(None, {}, 50, ticker="SENTETİK")
            hucre = strat.scan_entry(None, {ARMED_KUME_PARAM: kume_hucre}, 50, ticker="SENTETİK")
            sonuc[ad] = {"taban": None if taban is None else taban.setup,
                         "hucre": None if hucre is None else hucre.setup}
    finally:
        strat.scan_all = orij_scan_all
    assert strat.scan_all is orij_scan_all, "ön-uçuş: scan_all geri alınamadı"

    # BEKLENEN TABLO (kart öz-sınama (a) + (b)) — donuk, koşum sonucuna bakmaz
    beklenen = {
        "yalniz_pullback":     {"taban": "pullback", "hucre": None},              # (a)
        "pullback_ve_mb":      {"taban": "pullback", "hucre": "momentum_burst"},  # (a)
        "pullback_ve_eh":      {"taban": "pullback", "hucre": "exhaustion_hammer"},
        "breakout_ve_pullback": {"taban": "breakout_vcp", "hucre": "breakout_vcp"},  # (b)
        "yalniz_eh":           {"taban": "exhaustion_hammer", "hucre": "exhaustion_hammer"},
        "yalniz_mb":           {"taban": "momentum_burst", "hucre": "momentum_burst"},
        "yalniz_breakout":     {"taban": "breakout_vcp", "hucre": "breakout_vcp"},
        "uyuyan_kurulum":      {"taban": None, "hucre": None},
        "hicbiri":             {"taban": None, "hucre": None},
    } if cikar == ("pullback",) else None
    gecti = (sonuc == beklenen) if beklenen is not None else None
    if beklenen is not None:
        assert gecti, f"ÖN-UÇUŞ ÖZ-SINAMASI DÜŞTÜ: {sonuc} ≠ {beklenen}"
    return {"cikarilan": list(cikar), "hucre_kumesi": list(kume_hucre),
            "senaryolar": sonuc, "beklenen": beklenen, "gecti": gecti,
            "beyan": ("sentetik `scan_all` ile ön-uçuş: (a) pullback sinyali TEK adayken hücre "
                      "hiç silahlanmıyor; pullback+mb'de mb'ye düşüyor. (b) pullback dışındaki "
                      "üç kurulumun seçimi HER senaryoda taban ile aynı. Sahte tarama yalnız bu "
                      "fonksiyon içinde takılı, finally ile geri alındı (assert'li).")}


# ---------------------------------------------------------------------------------------------
# TEK HÜCRE KOŞUMU (taban + eksipb — tek şasi, hücre-parametreli)
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    hucre = dict(MERKEZ)
    hucre.update(HUCRELER[run])
    SLOT, BOYUT_R, ZARF = int(hucre["slot"]), float(hucre["size"]), hucre["zarf"]
    CIKAR = tuple(hucre["armed_cikar"])                  # ARMED kümesinden ÇIKARILACAKLAR

    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    # kill#3 parmak izi — replay ÖNCESİ (koşum sonunda yeniden alınıp karşılaştırılır)
    motor_once = _motor_kunye()

    # ŞASİ KİMLİK ÇİVİSİ: sandbox config sha'ları 032-cmb kaydıyla bayt-aynı olmalı
    cmb_kayit = json.loads((EDG032 / "sonuc_cmb.json").read_text())
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        beklenen = cmb_kayit["config_sha256_16"][f]["sandbox"]
        gercek = _sha(st_dir / f)
        assert gercek == beklenen, \
            f"ŞASİ KİMLİĞİ BOZUK: sandbox {f} sha {gercek} ≠ 032 kaydı {beklenen}"

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"
    config.reload_config()      # lru_cache boşalt: goal() bundan sonra SANDBOX dosyasını okur
    #                             (derisk_ramp/entry_law config.goal() okuyucusudur — izolasyon şartı)

    import numpy as np                     # noqa: F401
    import yaml
    from meridian import backtest, dataset, guard, score as score_mod

    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk
    strat = backtest.strat
    ORIJ_DERISK = brk.derisk_mult          # kablolu-rampa kanıtı: koşum boyunca YAMASIZ kalmalı

    # ---- RAMPA KABLOLU KANITI (kart universe: monkeypatch YOK — motor goal-okuyucu) ----------
    rampa_cfg = brk.derisk_ramp()
    assert rampa_cfg["full_dd"] == RAMPA_BEKLENEN["full_dd"] \
        and rampa_cfg["floor_dd"] == RAMPA_BEKLENEN["floor_dd"], \
        f"rampa bandı beklenen 15/36 değil: {rampa_cfg}"
    # sandbox goal'ünde derisk anahtarı YOK → kaynak 'kod varsayilani' (fail-safe = C+mb bandı)
    _sand_goal = yaml.safe_load((st_dir / "goal.yaml").read_text())
    assert "derisk_full_dd" not in (_sand_goal.get("limits") or {}) \
        and "derisk_floor_dd" not in (_sand_goal.get("limits") or {}), \
        "sandbox goal derisk anahtarı içeriyor — şasi beklentisi bozuk"
    # 023/026 değer çivileri — bu kez YAMASIZ motor fonksiyonunun kendisi üstünde
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4       # 023 çivisi
    assert brk.max_positions_at(80.0, 100.0, 20) == 15     # slot-20 tabanı (026 çivisi)
    assert brk.max_positions_at(80.0, 100.0, SLOT) == max(1, int(round(SLOT * 0.7619)))
    rampa_kanit = {
        "monkeypatch": False,
        "kaynak": rampa_cfg["kaynak"],     # beklenen: iki alan da 'kod varsayilani' (fail-safe)
        "band": {"full_dd": rampa_cfg["full_dd"], "floor_dd": rampa_cfg["floor_dd"]},
        "beyan": ("broker.derisk_ramp() goal-okuyucu (broker.py:227); sandbox goal'ünde "
                  "derisk anahtarı yok → fail-safe 0.15/0.36 = C+mb bandı. derisk_mult "
                  "YAMASIZ; 023/026 değer çivileri koşum başında assert'lendi"),
    }

    # ---- girdiler + HÜCRE ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir) -----------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              "heat_hard_r": float(goal["limits"]["heat_hard_r"]),
              "entry.armed_extra": params.get("entry.armed_extra"),   # beklenen: None (v3 dosya)
              ARMED_KUME_PARAM: params.get(ARMED_KUME_PARAM)}         # beklenen: None (ölçüm-yerel)
    assert onceki["heat_hard_r"] == ZARF_MERKEZ, \
        f"beklenen zarf merkezi 5.0 değil: {onceki['heat_hard_r']}"
    assert onceki["entry.armed_extra"] is None, \
        "frozen strategy.yaml entry.armed_extra içeriyor — şasi beklentisi bozuk"
    assert onceki[ARMED_KUME_PARAM] is None, \
        f"frozen strategy.yaml {ARMED_KUME_PARAM} içeriyor — ölçüm-yerel anahtar dosyaya sızmış"

    # ARMED kümeleri: taban = motor sabiti + repo EKLEME kanalı (armed_extra=None) — DOKUNULMADI
    ARMED_TABAN = tuple(strat.ARMED_SETUPS) + tuple(params.get("entry.armed_extra") or ())
    ARMED_HUCRE = tuple(s for s in ARMED_TABAN if s not in CIKAR)
    assert set(CIKAR) <= set(ARMED_TABAN), f"çıkarılacak kurulum ARMED kümesinde yok: {CIKAR}"
    assert len(ARMED_HUCRE) == len(ARMED_TABAN) - len(CIKAR), "çıkarma sayısı tutmuyor"
    assert [s for s in ARMED_HUCRE] == [s for s in ARMED_TABAN if s not in CIKAR], \
        "hücre kümesi taban SIRASINI korumuyor — öncelik değişirse yan etki ölçüme karışır"

    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (goal/limits)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (strateji params)
    params[ARMED_KUME_PARAM] = ARMED_HUCRE                 # ENJEKSİYON 4 (ARMED kümesi — bu kart)
    if ZARF is not None:
        goal["limits"]["heat_hard_r"] = float(ZARF)        # ENJEKSİYON 3 (zarf hücreleri; 028 emsali)

    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        _ovr = (by_regime or {}).get(_rg) or {}
        assert "position_size_r" not in _ovr, f"params_by_regime[{_rg}] position_size_r içeriyor"
        assert "entry.armed_extra" not in _ovr, f"params_by_regime[{_rg}] entry.armed_extra içeriyor"
        assert ARMED_KUME_PARAM not in _ovr, f"params_by_regime[{_rg}] {ARMED_KUME_PARAM} içeriyor"
        # ENJEKSİYON 4'ün YÜZEYE ULAŞMA kanıtı: scan_entry `eff`i görür (backtest.py:329)
        assert tuple(_eff[ARMED_KUME_PARAM]) == ARMED_HUCRE, \
            f"ARMED kümesi {_rg} rejiminde eff'e taşınmadı: {_eff.get(ARMED_KUME_PARAM)}"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R          # yukarı-kırpma etkilemez
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- MB MOTORDA SİLAHLI KANITI (kanal enjeksiyonu YOK — kart universe) -------------------
    assert tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN, \
        f"repo ARMED_SETUPS beklenenden farklı: {strat.ARMED_SETUPS}"
    assert strat.ARMED_SETUPS[-1] == "momentum_burst", \
        "mb SONDA değil — 032'nin ölçtüğü öncelik sırası (armed üçlü önce) bozulmuş olur"
    mb_kanit = {
        "armed_setups": list(strat.ARMED_SETUPS),
        "armed_extra_enjeksiyonu": None,
        "beyan": ("mb motorun kendi ARMED_SETUPS'unda ve SONDA (strategy.py:1029) — 032'nin "
                  "`ARMED_SETUPS + extra` (extra sonda) önceliğiyle birebir; kanal gereksiz"),
    }

    # ---- ARMED KANALI: BEYANLI MONKEYPATCH + ÖN-UÇUŞ ÖZ-SINAMASI ----------------------------
    # SIRA ÖNEMLİ: kanal, aşağıdaki sayım kancalarından (`_orig_scan`) ÖNCE takılır; böylece
    # `n_sinyal` sayacı HÜCRENİN gerçek silahlanmasını sayar ve `scan==plan` çivisi anlamlı kalır.
    ARMED_SABIT_ONCE = tuple(strat.ARMED_SETUPS)
    ARMED_SABIT_ID_ONCE = id(strat.ARMED_SETUPS)
    STRATEGY_SHA_ONCE = _sha_full(REPO / "meridian/strategy.py")
    _GERCEK_SCAN_ENTRY, kanal_sayac = kur_armed_kanali(strat)
    assert strat.scan_entry is not _GERCEK_SCAN_ENTRY, "kanal takılmadı"
    on_ucus = onucus_ozsinama(strat, CIKAR) if CIKAR else {
        "cikarilan": [], "hucre_kumesi": list(ARMED_TABAN), "senaryolar": None,
        "beklenen": None, "gecti": None,
        "beyan": ("taban kolu — çıkarma YOK; ön-uçuş senaryo tablosu ÇALIŞTIRILMADI (olculemedi: "
                  "senaryolar bu kolda taban≡hücre olduğu için ayırt edici değil). Bu kolun "
                  "kanıtı BAYT-ÖZDEŞLİK kapısıdır (`notrluk`)."),
    }
    assert tuple(strat.ARMED_SETUPS) == ARMED_SABIT_ONCE, "ön-uçuş ARMED_SETUPS'ı oynattı"
    # ön-uçuş sentetik çağrıları sayaçları kirletir → SIFIRLA (koşum-içi sayaçlar YALNIZ gerçek
    # barları saymalı; yoksa öz-sınama (a) kendi sentetik kanıtıyla beslenirdi — döngüsel olurdu)
    on_ucus["sentetik_cagri_n"] = kanal_sayac["cagri_n"]
    for _k, _v in list(kanal_sayac.items()):
        kanal_sayac[_k] = 0 if isinstance(_v, int) else ({} if isinstance(_v, dict) else [])
    assert kanal_sayac["cagri_n"] == 0 and not kanal_sayac["kesilen_ornekler"], \
        "sayaç sıfırlaması tutmadı"

    # ---- ZARF YÜZEYİ ÖZ-SINAMASI (yalnız zarf hücreleri; 028 T10 emsali AYNEN) ---------------
    zarf_oz_sinama = None
    if ZARF is not None:
        Z = float(ZARF)
        # sentetik plan/portföy: open_heat = open_risk_r + size_r (guard.py:375)
        _tp = {"sector": "tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 95}
        _rj = {"exposure_budget_pct": 60, "leading_sectors": []}
        _pf_ara = {"open_positions": 3, "sector_counts": {}, "day_pnl_pct": 0.0,
                   "open_risk_r": Z - 0.8, "max_corr": 0.0}    # heat = Z-0.3: eski zarfın ÜSTÜ, yeninin ALTI
        _pf_ust = {**_pf_ara, "open_risk_r": Z + 0.2}          # heat = Z+0.7: yeni zarfın da ÜSTÜ
        assert (Z - 0.8 + 0.5) > ZARF_MERKEZ, "öz-sınama aralığı eski zarfın üstünde değil — sınama anlamsız"
        _g5 = {"limits": {**limits, "heat_hard_r": ZARF_MERKEZ}}
        _v5, _n5 = guard.classify_gate(_tp, _pf_ara, _rj, _g5)
        assert _v5 == "NO_GO" and any("ısısı sert tavanı" in x for x in _n5), \
            "5R zarf yüzeyi kanıtlanamadı (ara-ısı eski zarfta kesilmedi)"
        _vZ, _nZ = guard.classify_gate(_tp, _pf_ara, _rj, goal)
        assert _vZ != "NO_GO", f"zarf enjeksiyonu ısı kapısına işlemedi (ara-ısı hâlâ kesiliyor): {_nZ}"
        _vZu, _nZu = guard.classify_gate(_tp, _pf_ust, _rj, goal)
        assert _vZu == "NO_GO" and any("ısısı sert tavanı" in x for x in _nZu), \
            f"{Z}R tavanın ÜSTÜ kesilmiyor — enjeksiyon yanlış yüzeyde"
        zarf_oz_sinama = {
            "ara_isi_R": round(Z - 0.3, 2), "ust_isi_R": round(Z + 0.7, 2),
            "eski_zarfta_NO_GO": True, "yeni_zarfta_gecer": True, "yeni_zarf_ustu_NO_GO": True,
            "yuzey": "guard.classify_gate → goal['limits']['heat_hard_r'] (guard.py:326; 028 emsali)",
        }

    # ---- kancalar (032 şasi deseni AYNEN) ----------------------------------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)              # GERÇEK eff_max_open (kablolu rampa)
        fr = sys._getframe(1)
        loc = fr.f_locals
        d = loc.get("d")
        bar_i = loc.get("bar_i")
        broker = loc.get("broker")
        if d is None or broker is None:
            _frame_miss[0] += 1                               # sessiz-yutma DEĞİL: sayılır, geçerliliği bozar
            return n
        date = str(d.date())
        n_acik = len(broker.positions)                        # açılışta, fill'den ÖNCE
        dd = ((peak - equity) / peak) if peak and peak > 0 else 0.0
        pozlar = list(broker.positions.values())
        rec = {
            "date": date, "bar_i": int(bar_i) if bar_i is not None else None,
            "eq_open": round(float(equity), 2), "peak_equity": round(float(peak), 2),
            "dd": round(float(dd), 6), "base_max_open": int(base_max),
            "eff_max_open": int(n), "n_acik": int(n_acik),
            "acik_slot": int(n) - int(n_acik),
            "size_mult": float(brk.derisk_mult(equity, peak)),
            "acik_size_r_toplam": round(sum(float(p.size_r) for p in pozlar), 3),
            "acik_risk_dollars_giris": round(sum(float(p.risk_dollars) for p in pozlar), 2),
            "acik_kalan_risk_dollars": round(sum(
                max(0.0, (float(p.entry) - max(float(p.stop), float(p.trail_stop))) * int(p.qty))
                for p in pozlar), 2),
            "regime": None, "exposure_budget_pct": None,
            "n_scan_cagri": 0, "n_sinyal": 0,
        }
        if date in seans_by_date:
            _dup.append(date)
        seans_by_date[date] = rec
        return n

    def _regime(idx_df, params_, asof):
        rj = _orig_regime(idx_df, params_, asof)
        date = str(asof)[:10]
        _cur_close_date[0] = date
        rec = seans_by_date.get(date)
        if rec is not None:
            rec["regime"] = rj.get("regime")
            rec["exposure_budget_pct"] = rj.get("exposure_budget_pct")
        return rj

    def _scan(*a, **kw):
        rec = seans_by_date.get(_cur_close_date[0])
        if rec is not None:
            rec["n_scan_cagri"] += 1
        sig = _orig_scan(*a, **kw)
        if sig and rec is not None:
            rec["n_sinyal"] += 1
        return sig

    brk.max_positions_at = _maxpos
    backtest.regime_mod.build_regime_json = _regime
    backtest.strat.scan_entry = _scan

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    # kanca restorasyonu (kanıtlı) — süreç tek koşumluk ama düzen gereği geri takılır
    brk.max_positions_at = _orig_maxpos
    backtest.regime_mod.build_regime_json = _orig_regime
    backtest.strat.scan_entry = _orig_scan                 # (= ARMED sarmalayıcısı)
    strat.scan_entry = _GERCEK_SCAN_ENTRY                  # ARMED kanalı da SÖKÜLDÜ
    assert strat.scan_entry is _GERCEK_SCAN_ENTRY, "ARMED kanalı geri alınamadı"

    # koşum sonrası kanıtlar
    yasak_yuklu = [m for m in sys.modules if m in YASAK]
    armed_sonrasi_ayni = tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN
    assert armed_sonrasi_ayni, f"ARMED_SETUPS koşum sonrasında değişmiş: {strat.ARMED_SETUPS}"
    assert brk.derisk_mult is ORIJ_DERISK, "derisk_mult koşum sırasında yamalanmış — rampa kanıtı bozuk"

    # ---- ÖZ-SINAMA (a)(b)(c) KOŞUM-SONRASI HÜKMÜ (assert'li; kanıt dosyaya yazılır) ----------
    strategy_sha_sonra = _sha_full(REPO / "meridian/strategy.py")
    ozsinama_c = {
        "armed_setups_once": list(ARMED_SABIT_ONCE),
        "armed_setups_sonra": list(strat.ARMED_SETUPS),
        "deger_ayni": tuple(strat.ARMED_SETUPS) == ARMED_SABIT_ONCE,
        "tuple_kimligi_ayni": id(strat.ARMED_SETUPS) == ARMED_SABIT_ID_ONCE,
        "strategy_py_sha256_once": STRATEGY_SHA_ONCE,
        "strategy_py_sha256_sonra": strategy_sha_sonra,
        "strategy_py_dokunulmadi": STRATEGY_SHA_ONCE == strategy_sha_sonra,
        "scan_entry_geri_takildi": strat.scan_entry is _GERCEK_SCAN_ENTRY,
    }
    assert ozsinama_c["deger_ayni"] and ozsinama_c["tuple_kimligi_ayni"], \
        "ÖZ-SINAMA (c) DÜŞTÜ: ARMED_SETUPS modül sabiti değişmiş"
    assert ozsinama_c["strategy_py_dokunulmadi"], \
        "ÖZ-SINAMA (c) DÜŞTÜ: strategy.py sha256 koşum sırasında değişmiş (kart kill#2)"
    assert kanal_sayac["ozsinama_b_ihlal_n"] == 0, \
        f"ÖZ-SINAMA (b) DÜŞTÜ: {kanal_sayac['ozsinama_b_ihlal_n']} çağrıda yan etki"
    # (a)'nın KOŞUM-İÇİ ayağı yalnız TAM pencerede zorunludur: smoke penceresinde (2022-H1)
    # taban dünyasında hiç pullback planı yok (taban plan_setup_dagilim: pullback=13, hepsi
    # 2023+) — orada sayaç 0 çıkması ölçüm hatası değil, PENCERE OLGUSUDUR. UYDURMA YASAĞI
    # gereği smoke'ta "olculemedi" diye adıyla kaydedilir; ön-uçuş ayağı her iki pencerede koşar.
    if CIKAR and not smoke:
        assert kanal_sayac["taban_pullback_secti_n"] > 0, \
            ("ÖZ-SINAMA (a) DÜŞTÜ: hiçbir çağrıda taban seçimi pullback olmadı — kanal ölçülemez "
             "(pullback sinyali üretmeyen bir dünyada silahsızlanma boş işlem olurdu)")
    kanal_kanit = {
        "secim": ("BEYANLI MONKEYPATCH — ARMED kümesinin TAMAMI param olarak geçirildi "
                  f"(`{ARMED_KUME_PARAM}`); tek kanonik nokta: strategy.scan_entry"),
        "gerekce": ("repo yüzeyi yalnız EKLEME yönünde (`entry.armed_extra`, strategy.py:1068); "
                    "ÇIKARMA anahtarı repo kodunda YOK. Bir `armed_eksi` kanalı açmak strategy.py'yi "
                    "DEĞİŞTİRMEK olurdu → kart kill#2. Modül sabitini koşum boyunca yeniden bağlamak "
                    "da reddedildi (sabit replay dışında da okunuyor; öz-sınama (c) tam bunu yasaklar). "
                    "Kalan tek yol kartın adıyla önerdiği ikinci yoldur."),
        "kanonik_nokta_kaniti": ("replay yolunda ARMED_SETUPS'ın TEK okuyucusu scan_entry "
                                 "(backtest.py:329). cf_backfill/loop/shadow_variants da okur ama "
                                 "replay'de İTHAL EDİLMEZ — yasak-modül assert'i bunu kanıtlar: "
                                 f"yuklenen={yasak_yuklu}"),
        "armed_taban": list(ARMED_TABAN),
        "armed_hucre": list(ARMED_HUCRE),
        "cikarilan": list(CIKAR),
        "param_yuzeyi": (f"params['{ARMED_KUME_PARAM}'] → config.resolve_params → eff → "
                         "backtest.py:329 scan_entry(eff) (4 rejimde assert'lendi)"),
        "kanun_kopyalanmadi": ("tarama `strat.scan_all` ÇAĞRISIYLA yapılır; kopyalanan tek şey "
                               "strategy.py:1069-1072 öncelik döngüsüdür ve taban kümesiyle "
                               "özdeş davranışı BAYT-ÖZDEŞLİK kapısıyla (`notrluk`) çakılıdır"),
        "on_ucus_ozsinama_a_b": on_ucus,
        "kosum_ici_sayaclar": {k: v for k, v in kanal_sayac.items()},
        "ozsinama_a_kosum_ici": {
            "taban_pullback_secti_n": kanal_sayac["taban_pullback_secti_n"],
            "kesildi_bosa_dustu_n": kanal_sayac["kesildi_bosa_dustu_n"],
            "kesildi_yerine_gecen": kanal_sayac["kesildi_yerine_gecen"],
            "gecti": ((kanal_sayac["taban_pullback_secti_n"] > 0) if not smoke else None)
            if CIKAR else None,
            "olculemedi_neden": (("smoke penceresinde (2022-H1) taban dünyasında hiç pullback "
                                  "planı yok — sayaç 0 çıkması pencere olgusudur, kanal hatası "
                                  "DEĞİL; (a)'nın koşum-içi ayağı TAM pencerede ölçülür")
                                 if (CIKAR and smoke) else None),
            "beyan": ("GERÇEK barlarda: taban kümesiyle `pullback` seçilecek her çağrıda hücre "
                      "ya hiç silahlanmadı ya da bir SONRAKİ öncelikli kuruluma düştü"),
        },
        "ozsinama_b_kosum_ici": {
            "ihlal_n": kanal_sayac["ozsinama_b_ihlal_n"],
            "ihlal_ornek": kanal_sayac["ozsinama_b_ihlal_ornek"],
            "gecti": kanal_sayac["ozsinama_b_ihlal_n"] == 0,
            "beyan": ("ÇAĞRI BAŞINA değişmez: taban seçimi pullback DEĞİLSE hücre seçimi AYNI "
                      "NESNE olmak zorunda — ihlalde koşum AssertionError ile durur"),
        },
        "ozsinama_c": ozsinama_c,
    }

    # kill#3: motor parmak izi replay SONRASI aynı mı? (033 dersi — mtime değişimi hücreyi geçersiz kılar)
    motor_sonra = _motor_kunye()
    kill3_bozuk = [f for f in MOTOR_DOSYALAR if motor_once[f] != motor_sonra[f]]

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı (032 AYNEN) ------------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    nogo_nedenler: list[str] = []
    review_nedenler: list[str] = []
    verdict_n = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    silahli_size_r: list[float] = []
    plan_setup_n: dict[str, int] = {}
    mb_plan_verdict = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    for p in (res.plan_log or []):
        dts = str(p.get("date"))[:10]
        plan_aday[dts] = plan_aday.get(dts, 0) + 1
        v = p.get("gate_verdict")
        verdict_n[v] = verdict_n.get(v, 0) + 1
        su = p.get("setup") or "?"
        plan_setup_n[su] = plan_setup_n.get(su, 0) + 1
        if su == "momentum_burst":
            mb_plan_verdict[v] = mb_plan_verdict.get(v, 0) + 1
        if v != "NO_GO":
            plan_silahli[dts] = plan_silahli.get(dts, 0) + 1
            silahli_size_r.append(float(p.get("size_r") or 0.0))
            if v == "REVIEW":
                review_nedenler.extend(p.get("gate_reasons") or [])
        else:
            nogo_nedenler.extend(p.get("gate_reasons") or [])

    sess = sorted(seans_by_date.values(),
                  key=lambda r: (r["bar_i"] if r["bar_i"] is not None else 0))
    scan_vs_plan = []
    for r in sess:
        r["aday_n"] = r["n_sinyal"]                           # TAM aday (CAPSIZ — şasi birincil kaynağı)
        r["silahli_n"] = plan_silahli.get(r["date"], 0)
        r["plan_aday"] = plan_aday.get(r["date"], 0)
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan.append({"date": r["date"], "n_sinyal": r["n_sinyal"],
                                 "plan_aday": r["plan_aday"]})
        r["sinif"] = classify(r, no_trade_before)

    n_all = len(sess)
    base_max_bozuk = [r["date"] for r in sess if r["base_max_open"] != SLOT]   # enjeksiyon çivisi
    birincil = [r for r in sess if r["sinif"] in KART3]
    n_bir = len(birincil)

    def dagit(records):
        c: dict[str, int] = {}
        for r in records:
            c[r["sinif"]] = c.get(r["sinif"], 0) + 1
        return c

    def yuzde(cnt, tot):
        return {k: {"n": v, "pct": round(100.0 * v / tot, 2)} for k, v in sorted(cnt.items())}

    ci = bootstrap_ci(birincil, KART3) if birincil else None

    # ---- işlem/doluluk/ısı/performans metrikleri (032 AYNEN) ---------------------------------
    trades = res.trades or []
    n_islem = len(trades)
    mb_islem_n = sum(1 for t in trades if t.get("setup") == "momentum_burst")
    aylik: dict[str, int] = {}
    for t in trades:
        aylik[str(t["ts_open"])[:7]] = aylik.get(str(t["ts_open"])[:7], 0) + 1
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days
    yil = pencere_gun / 365.25

    eq_vals = [float(e) for _, e in (res.equity or [])]
    net_pnl_equity = round(eq_vals[-1] - score_mod.START_EQUITY, 2) if eq_vals else None
    net_pnl_trades = round(sum(float(t.get("pnl_dollars", 0.0)) for t in trades), 2)
    maxdd_m2m = round(score_mod.max_drawdown(eq_vals), 4) if eq_vals else None
    detail = score_mod.score_detail(trades, goal, span_days=pencere_gun, mtm_equity=res.equity)

    doluluk_pozgun = sum(r["n_acik"] for r in sess)
    doluluk_barsheld = sum(int(t.get("bars_held") or 0) for t in trades)
    exit_dist: dict[str, int] = {}
    for t in trades:
        exit_dist[str(t.get("exit_reason"))] = exit_dist.get(str(t.get("exit_reason")), 0) + 1

    takvim = [r["date"] for r in sess]
    aralik_sayim = _islem_araligi_sayimi(
        [{"ts_open": t.get("ts_open"), "ts_close": t.get("ts_close")} for t in trades], takvim)
    isi = {
        "formul": f"nominal = n_eszamanli × {BOYUT_R}R (kart formülü; conviction 0.6-1.0× nedeniyle ÜST SINIR)",
        "nominal_open_fazi_R": _isi_ozet([r["n_acik"] * BOYUT_R for r in sess]),
        "nominal_islem_araligi_R": _isi_ozet([n * BOYUT_R for n in aralik_sayim]),
        "gerceklesen_open_fazi": {
            "size_r_toplam": _isi_ozet([r["acik_size_r_toplam"] for r in sess]),
            "risk_dollars_giris_max": round(max((r["acik_risk_dollars_giris"] for r in sess),
                                                default=0.0), 2),
            "kalan_risk_dollars_max": round(max((r["acik_kalan_risk_dollars"] for r in sess),
                                                default=0.0), 2),
            "kalan_risk_nav_pct_max": round(max(
                (100.0 * r["acik_kalan_risk_dollars"] / r["eq_open"]
                 for r in sess if r["eq_open"] > 0), default=0.0), 3),
        },
        "eszamanli_poz_max": {"open_fazi": max((r["n_acik"] for r in sess), default=0),
                              "islem_araligi": max(aralik_sayim, default=0)},
    }

    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA_BEKLENEN["full_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk and not kill3_bozuk)

    out = {
        "kart": "EDG-2026-039", "adim": "pullback silahsızlanma koşumu", "kosum": run,
        "smoke": smoke,
        "hucre": {"eksen": ("kanal_notrlugu" if not CIKAR else "armed_cikarma"),
                  "slot": SLOT, "position_size_r": BOYUT_R,
                  "heat_hard_r": (float(ZARF) if ZARF is not None else ZARF_MERKEZ),
                  "zarf_enjekte": ZARF is not None,
                  "armed_cikar": list(CIKAR), "armed_kume": list(ARMED_HUCRE)},
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa_kablolu": rampa_kanit,
        "mb_motor": mb_kanit,
        "kanal": kanal_kanit,
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (config.goal() derin kopyası — dosya değişmedi)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": ("strateji params sözlüğü (strategy.py _f yüzeyi; "
                                          "params_by_regime 4 rejimde boş — resolve_params assert'i; "
                                          "026 beyanı AYNEN)")},
            "armed_kume": {"once": list(ARMED_TABAN), "sonra": list(ARMED_HUCRE),
                           "yuzey": (f"strateji params['{ARMED_KUME_PARAM}'] → resolve_params → "
                                     "eff → scan_entry BEYANLI sarmalayıcısı (bkz. `kanal`)")},
            "heat_hard_r": {"once": onceki["heat_hard_r"],
                            "sonra": (float(ZARF) if ZARF is not None else onceki["heat_hard_r"]),
                            "yuzey": ("goal['limits'] — guard.classify_gate kanonik okuma yüzeyi "
                                      "(guard.py:326; 028 T10 emsali)" if ZARF is not None
                                      else "DOKUNULMADI (merkez 5.0R)")},
            "zarf_oz_sinama": zarf_oz_sinama,
        },
        "kill3_mtime": {"motor_once": motor_once, "motor_sonra": motor_sonra,
                        "bozuk_dosyalar": kill3_bozuk,
                        "temiz": not kill3_bozuk},
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "guard.py")},
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f),
                                 "repo_state": _sha(REPO / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0)),
                                  "not": "motorun kendi maliyet modeli — dokunulmadı (kart: pessimistic_band_v2 rapor bandı ayrı)"}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan),
            "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu,
            "base_max_open_bozuk": base_max_bozuk[:10],
            "kill3_bozuk_dosyalar": kill3_bozuk,
            "gecerli": butunluk_gecerli,
        },
        "islem": {
            "n": n_islem, "islem_yil": round(n_islem / yil, 2),
            "aylik_ts_open": dict(sorted(aylik.items())),
            "silahlanan_plan": sum(plan_silahli.values()),
            "toplam_plan": sum(plan_aday.values()),
            "verdict_dagilim": verdict_n,
            "nogo_neden_dagilim": _neden_dagit(nogo_nedenler),
            "review_neden_dagilim": _neden_dagit(review_nedenler),
            "silahli_plan_size_r": {"min": round(min(silahli_size_r), 3) if silahli_size_r else None,
                                    "max": round(max(silahli_size_r), 3) if silahli_size_r else None,
                                    "ort": round(sum(silahli_size_r) / len(silahli_size_r), 3)
                                    if silahli_size_r else None},
            "entry_rejects": res.entry_rejects,
            "exit_reason_dagilim": dict(sorted(exit_dist.items(), key=lambda kv: -kv[1])),
            "setup_bazinda": _setup_ozet([{k: t.get(k) for k in
                                           ("setup", "pnl_dollars", "r_multiple")} for t in trades]),
            "mb_islem_n": mb_islem_n,
            "plan_setup_dagilim": dict(sorted(plan_setup_n.items(), key=lambda kv: -kv[1])),
            "mb_plan_verdict": mb_plan_verdict,
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kapı (b) BUNUN üstünden
            "maxdd_m2m": maxdd_m2m,
            "avg_r": detail.get("avg_r"), "win_rate": detail.get("win_rate"),
            "sharpe": detail.get("sharpe"), "sharpe_measurable": detail.get("sharpe_measurable"),
            "score": detail.get("score"), "score_n": detail.get("n"),
            "total_return": detail.get("total_return"),
        },
        "doluluk": {"pozisyon_gun_open_fazi": doluluk_pozgun,
                    "ort_acik_pozisyon": round(doluluk_pozgun / n_all, 3) if n_all else None,
                    "doluluk_orani_slot": round(doluluk_pozgun / n_all / SLOT, 4) if n_all else None,
                    "toplam_bars_held": doluluk_barsheld},
        "tepe_isi": isi,
        "betim": {
            "n_seans": n_all, "dd_gt_tam_esik_n": dd_gt_tam,
            "eff_max_open_eq0_n": eff_eq0, "eff_max_open_eq1_n": eff_eq1,
            "eff_max_open_lt_base_n": eff_lt, "acik_slot_le0_n": slot_le0,
            "size_mult_0_n": size0,
        },
        "tasnif_tum_seans": {"n": n_all, "dagilim": yuzde(dagit(sess), n_all)},
        "birincil": {"n": n_bir, "dagilim": yuzde(dagit(birincil), n_bir) if n_bir else {},
                     "tavan_sifir_pct": tavan_pct_bir},
        "ci95_ay_kumeli": ci,
    }

    ek = "_smoke" if smoke else ""
    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    # (1) SLIM PROJEKSİYON — 032/035 kodu HARFİ HARFİNE (özdeşlik kapısının kıyas nesnesi)
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))
    # (2) TAM SATIR — broker.close_position'ın ürettiği sözlük OLDUĞU GİBİ (broker.py:685-702).
    # KIRPMA YOK, EKLEME YOK, YENİDEN ADLANDIRMA YOK: `res.trades` = `broker.closed`
    # (backtest.py:464) ve satırlar yalnız close_position tarafından append edilir (broker.py:703).
    # Anahtar sırası da bozulmaz (sort_keys YOK) — satırın kendi şeması kanıt niteliğindedir.
    (outdir / f"islemler_tam_{run}{ek}.json").write_text(
        json.dumps(trades, ensure_ascii=False, indent=1, default=str))
    # tam-satır defterinin alan envanteri (kapsama raporunun ham girdisi; hüküm YOK)
    tam_alanlar: dict[str, dict] = {}
    for t in trades:
        for k, v in t.items():
            b = tam_alanlar.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}})
            b["var"] += 1
            if v is not None:
                b["dolu"] += 1
            tn = type(v).__name__
            b["tipler"][tn] = b["tipler"].get(tn, 0) + 1
    (outdir / f"alan_envanteri_{run}{ek}.json").write_text(json.dumps(
        {"n_satir": n_islem, "alanlar": dict(sorted(tam_alanlar.items())),
         "satir_anahtar_sirasi": list(trades[0].keys()) if trades else None,
         "tum_satirlar_ayni_anahtar_kumesi": (
             len({tuple(t.keys()) for t in trades}) == 1 if trades else None)},
        ensure_ascii=False, indent=1, default=str))

    (outdir / f"kanal_{run}{ek}.json").write_text(
        json.dumps(kanal_kanit, ensure_ascii=False, indent=1, default=str))

    print(f"\n=========== EDG-039 KOŞUM [{run}{ek}] ===========")
    print(f"hücre: slot={SLOT} size_r={BOYUT_R} zarf={out['hucre']['heat_hard_r']} "
          f"(enjekte={out['hucre']['zarf_enjekte']})")
    print(f"ARMED: taban={list(ARMED_TABAN)} → hücre={list(ARMED_HUCRE)} (çıkarılan={list(CIKAR)})")
    print(f"kanal öz-sınama: ön-uçuş={on_ucus['gecti']}  (a) taban-pullback-seçti="
          f"{kanal_sayac['taban_pullback_secti_n']} boşa={kanal_sayac['kesildi_bosa_dustu_n']} "
          f"yerine={kanal_sayac['kesildi_yerine_gecen']}  (b) ihlal={kanal_sayac['ozsinama_b_ihlal_n']}  "
          f"(c) ARMED sabiti aynı={ozsinama_c['deger_ayni']} strategy.py sha aynı="
          f"{ozsinama_c['strategy_py_dokunulmadi']}")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"rampa kablolu: band={rampa_cfg['full_dd']}/{rampa_cfg['floor_dd']} "
          f"kaynak={rampa_cfg['kaynak']}  mb ARMED_SETUPS'ta (sonda)={armed_sonrasi_ayni}")
    print(f"bütünlük geçerli={butunluk_gecerli}  frame_miss={_frame_miss[0]} dup={len(_dup)} "
          f"scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} base_max_bozuk={len(base_max_bozuk)} "
          f"kill3_bozuk={kill3_bozuk}")
    print(f"işlem n={n_islem} (mb={mb_islem_n})  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  sharpe={detail.get('sharpe')}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"TAM defter: {outdir}/islemler_tam_{run}{ek}.json  satır={n_islem} "
          f"alan={len(tam_alanlar)} anahtar_kümesi_tek={len({tuple(t.keys()) for t in trades}) == 1 if trades else None}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")



# ---------------------------------------------------------------------------------------------
# YÜKLEYİCİLER
# ---------------------------------------------------------------------------------------------
def _yukle(d: pathlib.Path, ad: str, ek: str) -> dict:
    return {
        "sonuc": json.loads((d / f"sonuc_{ad}{ek}.json").read_text()),
        "seans": json.loads((d / f"seanslar_{ad}{ek}.json").read_text()),
        "islem_slim": json.loads((d / f"islemler_{ad}{ek}.json").read_text()),
        "islem_tam": json.loads((d / f"islemler_tam_{ad}{ek}.json").read_text()),
    }


# ---------------------------------------------------------------------------------------------
# KANAL-NÖTRLÜĞÜ KAPISI (kart kill#2 ayağı) — taban kolu ↔ edg032b kontrol BAYT-ÖZDEŞLİK
# ---------------------------------------------------------------------------------------------
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim",
                        "tasnif_tum_seans", "birincil", "ci95_ay_kumeli", "islem")


def notrluk(smoke: bool = False):
    """Kanal, TAM ARMED kümesiyle çağrıldığında dünyayı DEĞİŞTİRMİYOR mu? Sarmalayıcının
    orijinal `scan_entry` ile davranış-özdeşliği BURADA kanıtlanır: `taban` kolunun slim işlem
    defteri + seans defteri, edg032b `kontrol` çıktılarıyla BAYT-ÖZDEŞ olmak ZORUNDA.
    (sonuc dosyasının KENDİSİ bayt-özdeş OLAMAZ: olcum_zamani/sure_sn/kanal blokları koşum
    kimliğidir — ölçüm blokları DERİN-EŞİT kıyaslanır.)"""
    ek = "_smoke" if smoke else ""
    yerel = (SANDBOX / "smoke") if smoke else SANDBOX
    ref = (EDG032B / "smoke") if smoke else EDG032B

    y = {"islemler": yerel / f"islemler_taban{ek}.json",
         "seanslar": yerel / f"seanslar_taban{ek}.json",
         "islemler_tam": yerel / f"islemler_tam_taban{ek}.json",
         "sonuc": yerel / f"sonuc_taban{ek}.json"}
    r = {"islemler": ref / f"islemler_kontrol{ek}.json",
         "seanslar": ref / f"seanslar_kontrol{ek}.json",
         "islemler_tam": ref / f"islemler_tam_kontrol{ek}.json",
         "sonuc": ref / f"sonuc_kontrol{ek}.json"}
    for ad, p in {**y, **r}.items():
        if not p.exists():
            sys.exit(f"notrluk: dosya yok: {p}")

    sha_y = {k: _sha_full(p) for k, p in y.items()}
    sha_r = {k: _sha_full(p) for k, p in r.items()}
    bayt = {k: (sha_y[k] == sha_r[k]) for k in ("islemler", "seanslar", "islemler_tam")}

    sy, sr = json.loads(y["sonuc"].read_text()), json.loads(r["sonuc"].read_text())
    blok = {b: (sy.get(b) == sr.get(b)) for b in SONUC_OLCUM_BLOKLARI}
    fark = {b: {"taban_039": sy.get(b), "kontrol_032b": sr.get(b)}
            for b, v in blok.items() if not v}

    gecti = all(bayt.values()) and all(blok.values())
    out = {
        "kart": "EDG-2026-039", "adim": f"KANAL-NÖTRLÜĞÜ KAPISI{ek} (taban ↔ edg032b kontrol)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("BEYANLI ARMED sarmalayıcısı TAM kümeyle (çıkarma YOK) koşturuldu. İddia: "
                  "sarmalayıcı orijinal `strategy.scan_entry` ile DAVRANIŞ-ÖZDEŞ. Kanıt: slim "
                  "islemler + seanslar + TAM defter dosya baytları edg032b `kontrol` ile "
                  "sha256-özdeş ve sonuc ölçüm blokları derin-eşit."),
        "dosya_sha256": {"taban_039": sha_y, "kontrol_032b": sha_r},
        "bayt_ozdeslik": bayt,
        "sonuc_blok_esitligi": blok,
        "blok_fark_ozet": fark or None,
        "kanal_sayaclari_taban": (sy.get("kanal") or {}).get("kosum_ici_sayaclar"),
        "notrluk_gecti": gecti,
    }
    (yerel / f"notrluk{ek}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                        default=str))
    print(f"\n===== EDG-039 KANAL-NÖTRLÜĞÜ KAPISI{ek} =====")
    print(f"bayt-özdeşlik: {bayt}")
    print(f"sonuc blokları eşit: {blok}")
    print(f"NÖTRLÜK: {'GEÇTİ — sarmalayıcı dünyayı değiştirmiyor' if gecti else 'DÜŞTÜ — ölçüm DURUR'}")
    print(f"yazıldı: {yerel / f'notrluk{ek}.json'}")
    if not gecti:
        sys.exit(2)


# ---------------------------------------------------------------------------------------------
# KIYAS — hücre (C+mb − pullback) ↔ TABAN (edg032b kontrol, HAZIR; yeniden koşulmadı)
# ---------------------------------------------------------------------------------------------
def _kirilim(ts: list[dict]) -> dict:
    """Kurulum kırılımı: n, ort-R, net P&L, kazanma oranı (kazanma = pnl_dollars > 0)."""
    by: dict[str, dict] = {}
    for t in ts:
        b = by.setdefault(str(t.get("setup")), {"n": 0, "pnl": 0.0, "r_top": 0.0, "n_r": 0, "kaz": 0})
        b["n"] += 1
        b["pnl"] += float(t.get("pnl_dollars") or 0.0)
        if float(t.get("pnl_dollars") or 0.0) > 0:
            b["kaz"] += 1
        if t.get("r_multiple") is not None:
            b["r_top"] += float(t["r_multiple"])
            b["n_r"] += 1
    return {s: {"n": v["n"],
                "ort_r": round(v["r_top"] / v["n_r"], 4) if v["n_r"] else None,
                "net_pnl": round(v["pnl"], 2),
                "kazanma_orani": round(v["kaz"] / v["n"], 4),
                "kazanan_n": v["kaz"]}
            for s, v in sorted(by.items())}


def _kume_ozet(ts: list[dict]):
    """EDG-030 `_kume_ozet` deseni AYNEN (eklenen/çıkan kümelerin karnesi)."""
    import numpy as np
    if not ts:
        return None
    rs = [float(t.get("r_multiple") or 0.0) for t in ts]
    reg: dict[str, dict] = {}
    for t in ts:
        g = reg.setdefault(str(t.get("regime")), {"n": 0, "r_toplam": 0.0, "pnl": 0.0})
        g["n"] += 1
        g["r_toplam"] += float(t.get("r_multiple") or 0.0)
        g["pnl"] += float(t.get("pnl_dollars") or 0.0)
    for g in reg.values():
        g["ort_r"] = round(g["r_toplam"] / g["n"], 3)
        g["pnl"] = round(g["pnl"], 2)
        del g["r_toplam"]
    ex: dict[str, int] = {}
    st: dict[str, int] = {}
    for t in ts:
        ex[str(t.get("exit_reason"))] = ex.get(str(t.get("exit_reason")), 0) + 1
        st[str(t.get("setup"))] = st.get(str(t.get("setup")), 0) + 1
    return {"n": len(ts), "ort_r": round(sum(rs) / len(rs), 3),
            "medyan_r": round(float(np.median(rs)), 3),
            "pnl_toplam": round(sum(float(t.get("pnl_dollars") or 0.0) for t in ts), 2),
            "kazanma_orani": round(sum(1 for t in ts
                                       if float(t.get("pnl_dollars") or 0.0) > 0) / len(ts), 3),
            "rejim_kirilimi": dict(sorted(reg.items(), key=lambda kv: -kv[1]["n"])),
            "exit_reason_dagilim": dict(sorted(ex.items(), key=lambda kv: -kv[1])),
            "setup_dagilim": dict(sorted(st.items(), key=lambda kv: -kv[1])),
            "aylik_n": {a: sum(1 for t in ts if str(t["ts_open"])[:7] == a)
                        for a in sorted({str(t["ts_open"])[:7] for t in ts})}}


def kiyas(smoke: bool = False):
    import numpy as np
    sys.path.insert(0, str(REPO))
    from meridian import score as score_mod          # kanonik equity_curve/max_drawdown

    ek = "_smoke" if smoke else ""
    yerel = (SANDBOX / "smoke") if smoke else SANDBOX
    tdir = (EDG032B / "smoke") if smoke else EDG032B

    T = _yukle(tdir, "kontrol", ek)                  # TABAN: edg032b HAZIR çıktıları (salt-okundu)
    H = _yukle(yerel, "eksipb", ek)                  # HÜCRE: C+mb − pullback
    st_, sh_ = T["sonuc"], H["sonuc"]
    taban_islem, hucre_islem = T["islem_tam"], H["islem_tam"]

    taban_sha = {f"{ad}_kontrol{ek}.json": _sha_full(tdir / f"{ad}_kontrol{ek}.json")
                 for ad in ("sonuc", "seanslar", "islemler", "islemler_tam")}
    tam_sha = taban_sha[f"islemler_tam_kontrol{ek}.json"]

    # ---- KILL#3 (kart): taban defterde pullback 6 işlem + sha künyesi ------------------------
    taban_pb = [t for t in taban_islem if t.get("setup") == "pullback"]
    kill3 = {
        "esik": "taban defterde `pullback` 6 işlem bulunamazsa (sha uyuşmazlığı) GEÇERSİZ",
        "taban_tam_defter_sha256": tam_sha,
        "brief_sha256": TABAN_TAM_SHA,
        "sha_uyuyor": (tam_sha == TABAN_TAM_SHA) if not smoke else None,
        "sha_serh": ("smoke penceresinde brief künyesi TAM koşuma aittir — kıyaslanmadı (None)"
                     if smoke else None),
        "pullback_islem_n": len(taban_pb),
        "beklenen_n": 6,
        "pullback_kirilimi": _kirilim(taban_pb).get("pullback"),
        "tetiklendi": (len(taban_pb) != 6) or (not smoke and tam_sha != TABAN_TAM_SHA),
    }

    # ---- KILL#1/#2: şasi bütünlüğü + kanal repo koduna dokunmadı mı --------------------------
    motor_ayni = {f: (sh_["motor_sha256_16"].get(f) == st_["motor_sha256_16"].get(f)
                      and sh_["motor_sha256_16"].get(f) is not None)
                  for f in ("broker.py", "backtest.py", "strategy.py", "guard.py")}
    config_ayni = {f: (sh_["config_sha256_16"][f]["sandbox"] == st_["config_sha256_16"][f]["sandbox"]
                       and sh_["config_sha256_16"][f]["sandbox"] is not None)
                   for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")}
    tarih_t = [s["date"] for s in T["seans"]]
    tarih_h = [s["date"] for s in H["seans"]]
    takvim_ayni = (tarih_t == tarih_h)
    kanal_h = sh_.get("kanal") or {}
    ozc = kanal_h.get("ozsinama_c") or {}
    notrluk_p = yerel / f"notrluk{ek}.json"
    notrluk_j = json.loads(notrluk_p.read_text()) if notrluk_p.exists() else None

    kill1 = {
        "esik": "şasi bütünlüğü (frame/dup/scan==plan + yasak-modül + base_max + kill3-mtime + sha)",
        "hucre_butunluk": sh_["butunluk"], "taban_butunluk": st_["butunluk"],
        "motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
        "takvim_ayni": takvim_ayni, "n_seans": {"taban": len(tarih_t), "hucre": len(tarih_h)},
        "rampa_ayni_15_36": (sh_["rampa_kablolu"]["band"] == st_["rampa_kablolu"]["band"]
                             == RAMPA_BEKLENEN),
        "tetiklendi": not (sh_["butunluk"]["gecerli"] and st_["butunluk"]["gecerli"]
                           and all(motor_ayni.values()) and all(config_ayni.values())
                           and takvim_ayni
                           and sh_["rampa_kablolu"]["band"] == RAMPA_BEKLENEN),
    }
    kill2 = {
        "esik": ("ARMED kümesi enjeksiyonu strategy.py'yi DEĞİŞTİRİYORSA geçersiz — "
                 "ölçüm kanalı repo koduna dokunmaz"),
        "strategy_py_sha256_once": ozc.get("strategy_py_sha256_once"),
        "strategy_py_sha256_sonra": ozc.get("strategy_py_sha256_sonra"),
        "strategy_py_dokunulmadi": ozc.get("strategy_py_dokunulmadi"),
        "armed_setups_sabiti_degismedi": ozc.get("deger_ayni"),
        "armed_setups_tuple_kimligi_ayni": ozc.get("tuple_kimligi_ayni"),
        "kill3_mtime_temiz": {"hucre": sh_["kill3_mtime"]["temiz"],
                              "taban": st_["kill3_mtime"]["temiz"]},
        "repo_calisma_agacinda_strategy_py_sha256": _sha_full(REPO / "meridian/strategy.py"),
        "kanal_notrlugu_gecti": (notrluk_j or {}).get("notrluk_gecti"),
        "kanal_notrlugu_kaynak": str(notrluk_p) if notrluk_j else "olculemedi (notrluk.json yok)",
        "on_ucus_ozsinama_gecti": (kanal_h.get("on_ucus_ozsinama_a_b") or {}).get("gecti"),
        "ozsinama_b_ihlal_n": (kanal_h.get("ozsinama_b_kosum_ici") or {}).get("ihlal_n"),
        "ozsinama_a_kosum_ici": kanal_h.get("ozsinama_a_kosum_ici"),
        "tetiklendi": not (ozc.get("strategy_py_dokunulmadi") and ozc.get("deger_ayni")
                           and ozc.get("tuple_kimligi_ayni")
                           and (notrluk_j or {}).get("notrluk_gecti") is True
                           and (kanal_h.get("ozsinama_b_kosum_ici") or {}).get("ihlal_n") == 0),
    }

    # ---- EŞLENİK AY-KÜMELİ BOOTSTRAP (EDG-030 iter_metrikler deseni AYNEN) -------------------
    aylar = sorted({d[:7] for d in tarih_t})
    M = len(aylar)
    r_start, r_end = st_["replay"]["start"], st_["replay"]["end"]
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days

    def ay_grup(islemler):
        g: dict[str, list[dict]] = {a: [] for a in aylar}
        for t in islemler:
            a = str(t["ts_open"])[:7]
            if a in g:
                g[a].append(t)
        return g

    def ci95(arr):
        a = np.asarray([x for x in arr if x == x], dtype=float)
        if not len(a):
            return None
        return {"lo": round(float(np.percentile(a, 2.5)), 4),
                "hi": round(float(np.percentile(a, 97.5)), 4),
                "orta": round(float(np.median(a)), 4)}

    def iter_metrikler(gr, pick):
        ts: list[dict] = []
        for j in sorted(pick):
            ts.extend(gr[aylar[j]])
        n = len(ts)
        pnl = float(sum(float(t.get("pnl_dollars", 0.0)) for t in ts))
        if n > 2:
            ret = np.array([float(t.get("pnl_dollars", 0.0)) for t in ts]) / score_mod.START_EQUITY
            sd = float(ret.std(ddof=1))
            if sd > 0:
                tpy = n / (pencere_gun / 365.0)
                sh = float(ret.mean()) / sd * float(np.sqrt(max(tpy, 1.0)))
            else:
                sh = float("nan")
        else:
            sh = float("nan")
        dd = float(score_mod.max_drawdown(score_mod.equity_curve(ts))) if n else float("nan")
        return n, pnl, sh, dd

    grT, grH = ay_grup(taban_islem), ay_grup(hucre_islem)
    rng = np.random.default_rng(BOOT_SEED)
    d_n = np.empty(BOOT_ITER)
    d_pnl = np.empty(BOOT_ITER)
    d_sh: list[float] = []
    d_dd: list[float] = []
    sh_atlanan = dd_atlanan = 0
    idx_all = np.arange(M)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx_all, size=M, replace=True)      # EŞLENİK: aynı çekiliş iki kola
        nT, pT, shT, ddT = iter_metrikler(grT, pick)
        nH, pH, shH, ddH = iter_metrikler(grH, pick)
        d_n[i] = nH - nT
        d_pnl[i] = pH - pT
        if shT == shT and shH == shH:
            d_sh.append(shH - shT)
        else:
            sh_atlanan += 1
        if ddT == ddT and ddH == ddH:
            d_dd.append(ddH - ddT)
        else:
            dd_atlanan += 1
    ci_n, ci_pnl, ci_sh, ci_dd = ci95(d_n), ci95(d_pnl), ci95(d_sh), ci95(d_dd)

    # ---- İŞLEM KÜMESİ EŞLEMESİ: ÇIKAN / EKLENEN / ORTAK -------------------------------------
    def kimlik(t):
        return (str(t["ts_open"])[:10], t["ticker"])
    tekil_t = len({kimlik(t) for t in taban_islem}) == len(taban_islem)
    tekil_h = len({kimlik(t) for t in hucre_islem}) == len(hucre_islem)
    T_by = {kimlik(t): t for t in taban_islem}
    H_by = {kimlik(t): t for t in hucre_islem}
    cikan_k = sorted(set(T_by) - set(H_by))
    eklenen_k = sorted(set(H_by) - set(T_by))
    ortak_k = sorted(set(T_by) & set(H_by))
    cikan = [T_by[k] for k in cikan_k]
    eklenen = [H_by[k] for k in eklenen_k]
    ortak_dpnl = 0.0
    kayan = []
    for k in ortak_k:
        a, b = T_by[k], H_by[k]
        ortak_dpnl += float(b.get("pnl_dollars") or 0.0) - float(a.get("pnl_dollars") or 0.0)
        if (str(a.get("ts_close"))[:10] != str(b.get("ts_close"))[:10]
                or a.get("exit_reason") != b.get("exit_reason")
                or abs(float(a.get("r_multiple") or 0) - float(b.get("r_multiple") or 0)) > 1e-9
                or int(a.get("qty") or 0) != int(b.get("qty") or 0)):
            kayan.append({"kimlik": list(k), "setup": a.get("setup"),
                          "taban": {"ts_close": a.get("ts_close"), "qty": a.get("qty"),
                                    "r": a.get("r_multiple"), "pnl": a.get("pnl_dollars"),
                                    "exit": a.get("exit_reason")},
                          "hucre": {"ts_close": b.get("ts_close"), "qty": b.get("qty"),
                                    "r": b.get("r_multiple"), "pnl": b.get("pnl_dollars"),
                                    "exit": b.get("exit_reason")}})

    cikan_pb = [t for t in cikan if t.get("setup") == "pullback"]
    cikan_diger = [t for t in cikan if t.get("setup") != "pullback"]
    pb_kaybolan_n = len([t for t in taban_pb if kimlik(t) not in H_by])

    # ---- P&L AYRIŞTIRMASI — SENTE KAPANMA + "NAİF BEKLENTİ" FARKININ ADI --------------------
    pnl_t = float(st_["performans"]["net_pnl_trades"])
    pnl_h = float(sh_["performans"]["net_pnl_trades"])
    d_pnl_nokta = round(pnl_h - pnl_t, 2)
    ekl_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in eklenen), 2)
    cik_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan), 2)
    cik_pb_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan_pb), 2)
    cik_diger_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan_diger), 2)
    ortak_dpnl_r = round(ortak_dpnl, 2)
    kalinti = round(d_pnl_nokta - (ekl_pnl + ortak_dpnl_r - cik_pnl), 2)

    naif = round(-cik_pb_pnl, 2)        # "pullback'i çıkarınca kaybı kurtarırız" beklentisi
    naif_fark = round(d_pnl_nokta - naif, 2)
    ayristirma = {
        "kimlik": "Δ(Σpnl) = Σeklenen + Σortak_Δ − Σçıkan   (kalıntı 0.00 olmalı — sente kapanma)",
        "taban_net_pnl_trades": round(pnl_t, 2),
        "hucre_net_pnl_trades": round(pnl_h, 2),
        "delta_net_pnl_trades": d_pnl_nokta,
        "eklenen_pnl": ekl_pnl, "cikan_pnl": cik_pnl, "ortak_delta_pnl": ortak_dpnl_r,
        "kalinti": kalinti,
        "sente_kapaniyor": abs(kalinti) < 0.01,
        "naif_beklenti": {
            "tanim": ("kartın adıyla andığı naif beklenti: pullback'in 6 işlemi kaybolur, "
                      "kaybı kurtarılır → ΔP&L ≈ −(pullback net P&L)"),
            "deger": naif,
            "gerceklesen": d_pnl_nokta,
            "fark": naif_fark,
            "farkin_bilesenleri_ADIYLA": {
                "1_yan_kanal_EKLENEN_islemler":
                    {"pnl": ekl_pnl, "n": len(eklenen),
                     "ad": ("SERBEST KALAN KAPASİTE DOLDU — pullback'in tuttuğu slot/ısı boşalınca "
                            "tabanda kapıdan dönen adaylar işleme girdi")},
                "2_yan_kanal_CIKAN_pullback_disi":
                    {"pnl": cik_diger_pnl, "n": len(cikan_diger), "katki": round(-cik_diger_pnl, 2),
                     "ad": ("KNOCK-ON KAYIP — erken/farklı dolan işlemler slot-ısı-equity yolunu "
                            "kaydırdı; tabanda var olan bu işlemler hücrede HİÇ oluşmadı")},
                "3_ORTAK_islemlerde_kayma":
                    {"pnl": ortak_dpnl_r, "n_kayan": len(kayan), "n_ortak": len(ortak_k),
                     "ad": ("EQUITY-YOLU KAYMASI — aynı gün/aynı sembolde açılan işlemler farklı "
                            "equity ve farklı ısı altında boyutlandı (qty/çıkış/R kaydı)")},
            },
            "toplam_kontrol": round(ekl_pnl + (-cik_diger_pnl) + ortak_dpnl_r, 2),
            "toplam_kontrol_esit_mi": abs(round(ekl_pnl + (-cik_diger_pnl) + ortak_dpnl_r, 2)
                                          - naif_fark) < 0.01,
        },
        "pullback_kalemleri": {
            "taban_n": len(taban_pb), "hucre_n": len([t for t in hucre_islem
                                                      if t.get("setup") == "pullback"]),
            "tabandan_kaybolan_n": pb_kaybolan_n,
            "pnl": cik_pb_pnl,
            "hepsi_kayboldu": pb_kaybolan_n == len(taban_pb),
        },
    }

    # ---- YAN-KANAL AYRIŞTIRMASI (kartın zorunlu kalemi; EDG-030 deseni) ----------------------
    # TANIM: pullback pozisyonunun MEŞGUL ETTİĞİ seans penceresi = [ts_open, ts_close].
    # KAYIT SEMANTİĞİ ŞERHİ (backtest.py:215-225 okundu, varsayılmadı): seans kaydı günün AÇILIŞ
    # fazında, bekleyen çıkışlar İŞLENDİKTEN SONRA ve silahlı planlar DOLMADAN ÖNCE alınır. Yani
    #   * giriş gününün kaydı pozisyonu HENÜZ İÇERMEZ (dolum kayıttan sonra),
    #   * çıkış gününün kaydı, çıkış bir BEKLEYEN çıkışsa (regime_flip/time_stop — önceki kapanışta
    #     karar verilip bu açılışta uygulanır) pozisyonu ARTIK İÇERMEZ; dokunma-çıkışı ise
    #     (stop/target/stop_gap — faz 2, kayıttan sonra) İÇERİR.
    # Pencere yine de [ts_open, ts_close] raporlanır (yan-kanalın soruşturulacak zaman aralığı
    # budur); ısı/slot okumaları bu semantikle okunmalıdır — n_acik farkı pozisyonun kendisini
    # DEĞİL, o pencerede portföyün gerçekten nasıl seyrettiğini gösterir.
    T_seans = {s["date"]: s for s in T["seans"]}
    H_seans = {s["date"]: s for s in H["seans"]}
    tarih_sirali = tarih_t
    ekl_by_gun: dict[str, list[dict]] = {}
    for t in eklenen:
        ekl_by_gun.setdefault(str(t["ts_open"])[:10], []).append(t)

    pencereler = []
    mesgul_gunler: set[str] = set()
    for t in sorted(taban_pb, key=lambda x: str(x["ts_open"])):
        d0, d1 = str(t["ts_open"])[:10], str(t["ts_close"])[:10]
        gunler = [d for d in tarih_sirali if d0 <= d <= d1]
        mesgul_gunler.update(gunler)
        tb = [T_seans[d] for d in gunler if d in T_seans]
        hb = [H_seans[d] for d in gunler if d in H_seans]
        ic_ekl = [x for d in gunler for x in ekl_by_gun.get(d, [])]
        pencereler.append({
            "pullback_islem": {"ticker": t["ticker"], "ts_open": t["ts_open"],
                               "ts_close": t["ts_close"], "r_multiple": t.get("r_multiple"),
                               "pnl_dollars": t.get("pnl_dollars"),
                               "exit_reason": t.get("exit_reason"), "regime": t.get("regime"),
                               "bars_held": t.get("bars_held")},
            "pencere": {"ilk": d0, "son": d1, "seans_n": len(gunler)},
            "taban_seans": {
                "ort_n_acik": round(sum(s["n_acik"] for s in tb) / len(tb), 3) if tb else None,
                "ort_acik_slot": round(sum(s["acik_slot"] for s in tb) / len(tb), 3) if tb else None,
                "ort_acik_size_r": round(sum(s["acik_size_r_toplam"] for s in tb) / len(tb), 3)
                if tb else None,
                "slot_dolu_seans_n": sum(1 for s in tb if s["acik_slot"] <= 0),
                "toplam_silahli_plan": sum(s.get("silahli_n", 0) for s in tb)},
            "hucre_seans": {
                "ort_n_acik": round(sum(s["n_acik"] for s in hb) / len(hb), 3) if hb else None,
                "ort_acik_slot": round(sum(s["acik_slot"] for s in hb) / len(hb), 3) if hb else None,
                "ort_acik_size_r": round(sum(s["acik_size_r_toplam"] for s in hb) / len(hb), 3)
                if hb else None,
                "slot_dolu_seans_n": sum(1 for s in hb if s["acik_slot"] <= 0),
                "toplam_silahli_plan": sum(s.get("silahli_n", 0) for s in hb)},
            "pencere_ici_EKLENEN_islemler": [
                {"ts_open": x["ts_open"], "ticker": x["ticker"], "setup": x.get("setup"),
                 "r_multiple": x.get("r_multiple"), "pnl_dollars": x.get("pnl_dollars"),
                 "exit_reason": x.get("exit_reason")} for x in
                sorted(ic_ekl, key=lambda z: str(z["ts_open"]))],
            "pencere_ici_eklenen_n": len(ic_ekl),
            "pencere_ici_eklenen_pnl": round(sum(float(x.get("pnl_dollars") or 0.0)
                                                 for x in ic_ekl), 2),
            # "kapasite serbest kaldı ama kullanılamadı" ile "kullanılmadı" ayrımı: rejim kapalıysa
            # (exposure_budget_pct 0/None) o seansta HİÇBİR plan silahlanamaz — boşluk yan-kanal
            # bulgusu değil, rejim kapısının kendisidir.
            "pencere_rejim_durumu": {
                "sinif_dagilim": {s: sum(1 for x in tb if x.get("sinif") == s)
                                  for s in sorted({x.get("sinif") for x in tb})} if tb else None,
                "butce_kapali_seans_n": sum(1 for x in tb
                                            if not (x.get("exposure_budget_pct") or 0) > 0),
                "rejimler": sorted({str(x.get("regime")) for x in tb}) if tb else None},
        })

    mg = sorted(mesgul_gunler)
    tb_all = [T_seans[d] for d in mg if d in T_seans]
    hb_all = [H_seans[d] for d in mg if d in H_seans]
    ekl_ic = [x for x in eklenen if str(x["ts_open"])[:10] in mesgul_gunler]
    ekl_dis = [x for x in eklenen if str(x["ts_open"])[:10] not in mesgul_gunler]

    # ---- EKLENEN ort-R tek-örneklem ay-kümeli bootstrap CI (EDG-030 deseni) ------------------
    ekl_r_ci = None
    ekl_r_ci_neden = None
    ekl_aylar = sorted({str(t["ts_open"])[:7] for t in eklenen})
    if len(ekl_aylar) >= 2:
        gr2 = {a: [float(t.get("r_multiple") or 0.0)
                   for t in eklenen if str(t["ts_open"])[:7] == a] for a in ekl_aylar}
        rng2 = np.random.default_rng(BOOT_SEED)
        m2 = len(ekl_aylar)
        ortv = np.empty(BOOT_ITER)
        for i in range(BOOT_ITER):
            pk = rng2.choice(np.arange(m2), size=m2, replace=True)
            hav: list[float] = []
            for j in pk:
                hav.extend(gr2[ekl_aylar[j]])
            ortv[i] = float(np.mean(hav)) if hav else float("nan")
        ekl_r_ci = ci95(ortv)
    else:
        ekl_r_ci_neden = (f"eklenen işlemler {len(ekl_aylar)} ay kümesinde — ay-kümeli CI için "
                          "<2 küme; olculemedi (None)")

    yan_kanal = {
        "tanim": ("pullback'in 6 işlemi kaybolunca ne oldu: MEŞGUL PENCERE = [ts_open, ts_close] "
                  "(seans kaydı bar açılışında alınır, pozisyon o an hâlâ açık). Tabanda bu "
                  "seanslarda 1 slot + pozisyonun size_r'ı bağlıydı."),
        "mesgul_seans_n": len(mg),
        "mesgul_seans_toplam_pencere": {"ilk": mg[0] if mg else None, "son": mg[-1] if mg else None},
        "serbest_kalan_kapasite_ozeti": {
            "taban_ort_n_acik": round(sum(s["n_acik"] for s in tb_all) / len(tb_all), 3)
            if tb_all else None,
            "hucre_ort_n_acik": round(sum(s["n_acik"] for s in hb_all) / len(hb_all), 3)
            if hb_all else None,
            "taban_ort_acik_size_r": round(sum(s["acik_size_r_toplam"] for s in tb_all)
                                           / len(tb_all), 3) if tb_all else None,
            "hucre_ort_acik_size_r": round(sum(s["acik_size_r_toplam"] for s in hb_all)
                                           / len(hb_all), 3) if hb_all else None,
            "taban_slot_dolu_seans_n": sum(1 for s in tb_all if s["acik_slot"] <= 0),
            "hucre_slot_dolu_seans_n": sum(1 for s in hb_all if s["acik_slot"] <= 0),
            "okuma": ("hücre ort_n_acik ≈ taban ise serbest kalan slot ANINDA yeniden doldu; "
                      "belirgin düşükse kapasite BOŞ kaldı"),
        },
        "pencere_pencere": pencereler,
        "EKLENEN_islemler": {
            "toplam": _kume_ozet(eklenen),
            "ort_r_ci95_ay_kumeli": ekl_r_ci,
            "ort_r_ci_olculemedi_neden": ekl_r_ci_neden,
            "mesgul_pencere_ICINDE_acilan": {"n": len(ekl_ic), "ozet": _kume_ozet(ekl_ic)},
            "mesgul_pencere_DISINDA_acilan": {
                "n": len(ekl_dis), "ozet": _kume_ozet(ekl_dis),
                "ad": ("DOWNSTREAM KNOCK-ON — pullback penceresiyle doğrudan ilgisi yok; "
                       "equity/ısı yolunun kayması sonraki seanslarda yeni dolumlar doğurdu")},
        },
        "CIKAN_islemler": {
            "pullback": {"n": len(cikan_pb), "ozet": _kume_ozet(cikan_pb)},
            "pullback_disi_knock_on": {"n": len(cikan_diger), "ozet": _kume_ozet(cikan_diger)},
        },
        "ORTAK_islemlerde_kayma": {
            "ortak_n": len(ortak_k), "kayan_n": len(kayan),
            "kayan_toplam_delta_pnl": ortak_dpnl_r,
            "ornekler": kayan[:20],
        },
        "tarama_evreni": {
            "tanim": ("backtest.py:326 — ZATEN TUTULAN (ya da o gün silahlanmış) ticker taramadan "
                      "ATLANIR. Yani tarama evreni portföye BAĞLIDIR: pullback'in tuttuğu 6 sembol "
                      "hücrede tutulmadığı için sonraki seanslarda taranmaya DEVAM etti."),
            "toplam_scan_cagrisi": {"taban": sum(s["n_scan_cagri"] for s in T["seans"]),
                                    "hucre": sum(s["n_scan_cagri"] for s in H["seans"]),
                                    "delta": (sum(s["n_scan_cagri"] for s in H["seans"])
                                              - sum(s["n_scan_cagri"] for s in T["seans"]))},
            "toplam_sinyal_aday": {"taban": sum(s["n_sinyal"] for s in T["seans"]),
                                   "hucre": sum(s["n_sinyal"] for s in H["seans"]),
                                   "delta": (sum(s["n_sinyal"] for s in H["seans"])
                                             - sum(s["n_sinyal"] for s in T["seans"]))},
            "pullback_ust_secim_sayaci": {
                "taban_kolu": ((json.loads((yerel / f"sonuc_taban{ek}.json").read_text())
                                .get("kanal") or {}).get("kosum_ici_sayaclar") or {})
                .get("taban_pullback_secti_n") if (yerel / f"sonuc_taban{ek}.json").exists()
                else None,
                "hucre_kolu": (kanal_h.get("kosum_ici_sayaclar") or {}).get("taban_pullback_secti_n"),
                "serh": ("İKİ SAYI DOĞRUDAN KIYASLANAMAZ: hücrede pullback sembolleri portföyde "
                         "tutulmadığı için tarama evreninde KALDI ve aynı kurulum tekrar tekrar "
                         "ateşledi (hepsi silahsız düştü). Fark ölçüm hatası değil, atlama "
                         "kuralının portföyle etkileşimidir."),
            },
        },
        "kapi_basinci": {
            "tanim": "silahlı plan kapıdan neden dönüyor — ısı/slot baskısının doğrudan ölçüsü",
            "nogo_neden_dagilim": {"taban": st_["islem"]["nogo_neden_dagilim"],
                                   "hucre": sh_["islem"]["nogo_neden_dagilim"]},
            "review_neden_dagilim": {"taban": st_["islem"]["review_neden_dagilim"],
                                     "hucre": sh_["islem"]["review_neden_dagilim"]},
            "verdict_dagilim": {"taban": st_["islem"]["verdict_dagilim"],
                                "hucre": sh_["islem"]["verdict_dagilim"]},
            "plan_setup_dagilim": {"taban": st_["islem"]["plan_setup_dagilim"],
                                   "hucre": sh_["islem"]["plan_setup_dagilim"]},
        },
    }

    # ---- KURULUM KIRILIMI YAN YANA ----------------------------------------------------------
    kir_t, kir_h = _kirilim(taban_islem), _kirilim(hucre_islem)
    kirilim_yanyana = {}
    for s in sorted(set(kir_t) | set(kir_h)):
        a, b = kir_t.get(s), kir_h.get(s)
        kirilim_yanyana[s] = {
            "taban": a, "hucre": b,
            "delta": None if (a is None or b is None) else {
                "n": b["n"] - a["n"],
                "ort_r": (None if (a["ort_r"] is None or b["ort_r"] is None)
                          else round(b["ort_r"] - a["ort_r"], 4)),
                "net_pnl": round(b["net_pnl"] - a["net_pnl"], 2),
                "kazanma_orani": round(b["kazanma_orani"] - a["kazanma_orani"], 4)},
        }

    # ---- KIYAS TABLOSU ----------------------------------------------------------------------
    def satir(*yol):
        def cek(s):
            v = s
            for kk in yol:
                v = v.get(kk) if isinstance(v, dict) else None
                if v is None:
                    return None
            return v
        t_, h_ = cek(st_), cek(sh_)
        d = None
        if isinstance(t_, (int, float)) and isinstance(h_, (int, float)):
            d = round(h_ - t_, 4)
        return {"taban_Cmb": t_, "hucre_Cmb_eksi_pullback": h_, "delta": d}

    nT, nH = len(taban_islem), len(hucre_islem)
    tablo = {
        "islem_n": {"taban_Cmb": nT, "hucre_Cmb_eksi_pullback": nH, "delta": nH - nT,
                    "delta_pct": round(100.0 * (nH - nT) / nT, 2) if nT else None},
        "islem_n_delta_ci95_eslenik": ci_n,
        "islem_yil": satir("islem", "islem_yil"),
        "net_pnl_equity": satir("performans", "net_pnl_equity"),
        "net_pnl_trades": satir("performans", "net_pnl_trades"),
        "net_pnl_delta_ci95_eslenik": ci_pnl,
        "maxdd_kanonik": satir("performans", "maxdd_kanonik"),
        "maxdd_m2m": satir("performans", "maxdd_m2m"),
        "maxdd_delta_ci95_eslenik_kapali_islem_egrisi": ci_dd,
        "maxdd_ci_atlanan_iter": dd_atlanan,
        "sharpe": satir("performans", "sharpe"),
        "sharpe_delta_ci95_eslenik": ci_sh,
        "sharpe_ci_atlanan_iter": sh_atlanan,
        "avg_r_islem_R": satir("performans", "avg_r"),
        "win_rate": satir("performans", "win_rate"),
        "score": satir("performans", "score"),
        "total_return": satir("performans", "total_return"),
        "silahlanan_plan": satir("islem", "silahlanan_plan"),
        "toplam_plan": satir("islem", "toplam_plan"),
        "doluluk_pozisyon_gun": satir("doluluk", "pozisyon_gun_open_fazi"),
        "ort_acik_pozisyon": satir("doluluk", "ort_acik_pozisyon"),
        "toplam_bars_held": satir("doluluk", "toplam_bars_held"),
        "exit_reason_dagilim": {"taban_Cmb": st_["islem"]["exit_reason_dagilim"],
                                "hucre_Cmb_eksi_pullback": sh_["islem"]["exit_reason_dagilim"]},
        "tepe_isi_gerceklesen_sizeR_max": {
            "taban_Cmb": ((st_["tepe_isi"].get("gerceklesen_open_fazi") or {})
                          .get("size_r_toplam") or {}).get("max"),
            "hucre_Cmb_eksi_pullback": ((sh_["tepe_isi"].get("gerceklesen_open_fazi") or {})
                                        .get("size_r_toplam") or {}).get("max")},
        "eszamanli_poz_max": {"taban_Cmb": st_["tepe_isi"]["eszamanli_poz_max"],
                              "hucre_Cmb_eksi_pullback": sh_["tepe_isi"]["eszamanli_poz_max"]},
    }

    # ---- KAPI İŞARETİ — kart success_metric MEKANİK okuması (HÜKÜM DEĞİL) -------------------
    dd_t, dd_h = st_["performans"]["maxdd_kanonik"], sh_["performans"]["maxdd_kanonik"]
    sh_t, sh_h = st_["performans"]["sharpe"], sh_["performans"]["sharpe"]
    if ci_pnl is None:
        dal = "OLCULEMEDI (ΔP&L CI üretilemedi)"
    elif ci_pnl["lo"] > 0:
        dal = "CI_ALT_SIFIRDAN_BUYUK → ÖNERİLİR (çıkarmak CI ile İYİLEŞTİRİYOR)"
    elif ci_pnl["hi"] < 0:
        dal = "CI_UST_SIFIRDAN_KUCUK → pullback SİLAHLI KALIR (çıkarmak zarar veriyor)"
    else:
        dal = ("CI_0_ICI → kartın İKİNCİ AYAĞI geçerli: 'dd/sharpe belirgin iyileşiyorsa "
               "önerilir'. 'belirgin' kartta SAYISAL TANIMLANMAMIŞ — eşik sonradan konulamaz "
               "(ölçüm disiplini); yön ve CI aşağıda, hüküm Rol-1'in.")
    kapi_isareti = {
        "kart_olcutu": ("ΔP&L CI-alt > 0 → önerilir · ΔP&L CI 0-içi iken dd/sharpe belirgin "
                        "iyileşiyorsa önerilir · ΔP&L CI-üst < 0 → pullback silahlı kalır"),
        "delta_pnl_nokta": d_pnl_nokta,
        "delta_pnl_ci95_eslenik": ci_pnl,
        "dal": dal,
        "ikinci_ayak_dd_sharpe": {
            "maxdd_kanonik": {"taban": dd_t, "hucre": dd_h,
                              "delta": None if None in (dd_t, dd_h) else round(dd_h - dd_t, 4),
                              "yon": (None if None in (dd_t, dd_h) else
                                      ("iyilesme (dd düştü)" if dd_h < dd_t else
                                       "kotulesme (dd yükseldi)" if dd_h > dd_t else "degismedi")),
                              "delta_ci95_eslenik": ci_dd},
            "sharpe": {"taban": sh_t, "hucre": sh_h,
                       "delta": None if None in (sh_t, sh_h) else round(sh_h - sh_t, 4),
                       "yon": (None if None in (sh_t, sh_h) else
                               ("iyilesme (sharpe yükseldi)" if sh_h > sh_t else
                                "kotulesme (sharpe düştü)" if sh_h < sh_t else "degismedi")),
                       "delta_ci95_eslenik": ci_sh},
            "belirgin_mi": None,
            "belirgin_olculemedi_neden": ("kart 'belirgin iyileşme'yi sayısal tanımlamadı; "
                                          "ölçüm ajanı eşik UYDURAMAZ (eşikler donuk) — yön, "
                                          "nokta farkı ve eşlenik CI raporlandı"),
        },
        "beyan": "MEKANİK işaret — HÜKÜM DEĞİL. Hükmü Rol-1 işler (kart status: registered).",
    }

    out = {
        "kart": "EDG-2026-039", "adim": f"kıyas + yan-kanal ayrıştırması{ek}",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "smoke": smoke,
        "hucre": "C+mb − pullback (ARMED_SETUPS'tan `pullback` çıkarılmış dünya) — TEK HÜCRE",
        "kiyas_taban": {
            "kaynak": ("EDG-032b `kontrol` HAZIR çıktıları — YENİDEN KOŞULMADI, salt-okundu "
                       "(C+mb @5R: rampa 15/36, slot 20, 0,5R, zarf 5R, mb ARMED'da)"),
            "dizin": str(tdir), "dosya_sha256": taban_sha,
        },
        "yontem": {
            "eslenik_bootstrap": (f"ay-kümeli EŞLENİK bootstrap (iter={BOOT_ITER}, "
                                  f"seed={BOOT_SEED}): AYNI ay çekilişi İKİ kola birden "
                                  "uygulanır; Δ her iterasyonda eşli hesaplanır (ortak ay "
                                  "gürültüsü sadeleşir). Ay kümesi = ts_open[:7]; "
                                  f"küme sayısı M={M}."),
            "maxdd": ("kapı metriği `maxdd_kanonik` = score.score_detail.max_drawdown (koşum "
                      "çıktısı). Bootstrap içindeki Δmaxdd ise KAPALI-İŞLEM eğrisi üzerinden "
                      "(score.equity_curve) — ay çekilişi m2m eğrisini yeniden kuramaz; iki "
                      "ölçü AYRI adlarla raporlanır, karıştırılmaz."),
            "islem_kimligi": "(ts_open[:10], ticker) — EDG-030 deseni AYNEN",
            "islem_kimligi_tekil": {"taban": tekil_t, "hucre": tekil_h,
                                    "serh": (None if (tekil_t and tekil_h) else
                                             "KİMLİK TEKİL DEĞİL — eşleme çakışması var, "
                                             "ayrıştırma ŞERHLİ okunmalı")},
            "cost_model": ("motorun kendi maliyet modeli (iki kol AYNI) — kart notu: "
                           "pessimistic_band_v2 GÖRECELİ kıyasta etkisiz"),
        },
        "tablo": tablo,
        "kurulum_kirilimi_yanyana": kirilim_yanyana,
        "pnl_ayristirma": ayristirma,
        "yan_kanal_ayristirmasi": yan_kanal,
        "kapi_isareti": kapi_isareti,
        "kill_bayraklari": {"kill1_sasi_butunlugu": kill1, "kill2_kanal": kill2,
                            "kill3_taban_defteri": kill3,
                            "herhangi_tetiklendi": bool(kill1["tetiklendi"] or kill2["tetiklendi"]
                                                        or kill3["tetiklendi"])},
        "kanal_kaniti_hucre": kanal_h,
        "beyan": ("Bu dosya HÜKÜM İÇERMEZ. Kart eşikleri DONUK; kapı işareti MEKANİKTİR. "
                  "Ölçüm ajanı karta dokunmadı, repo koduna dokunmadı, git/canlı/state'e yazmadı."),
    }
    (yerel / f"sonuc{ek}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                      default=str))

    print(f"\n========== EDG-039 KIYAS{ek}: C+mb − pullback  ↔  C+mb (taban) ==========")
    print(f"işlem n: {nT} → {nH}  (Δ={nH - nT})   Δn CI95={ci_n}")
    print(f"net P&L: {pnl_t} → {pnl_h}   Δ={d_pnl_nokta}   ΔP&L CI95(eşlenik)={ci_pnl}")
    print(f"maxdd_kanonik: {dd_t} → {dd_h}   sharpe: {sh_t} → {sh_h}")
    print(f"işlem-R (avg_r): {st_['performans']['avg_r']} → {sh_['performans']['avg_r']}")
    print(f"\n-- P&L ayrıştırması: Δ={d_pnl_nokta} = eklenen {ekl_pnl} + ortak_Δ {ortak_dpnl_r} "
          f"− çıkan {cik_pnl}   kalıntı={kalinti} (sente kapanıyor="
          f"{ayristirma['sente_kapaniyor']})")
    print(f"-- naif beklenti {naif} vs gerçekleşen {d_pnl_nokta} → FARK {naif_fark}")
    print(f"   [1] eklenen: {ekl_pnl} (n={len(eklenen)})  [2] pullback-dışı çıkan: "
          f"{cik_diger_pnl} (n={len(cikan_diger)}, katkı {round(-cik_diger_pnl, 2)})  "
          f"[3] ortak kayma: {ortak_dpnl_r} (kayan {len(kayan)}/{len(ortak_k)})")
    print(f"\n-- yan-kanal: meşgul seans={len(mg)}  eklenen(pencere içi)={len(ekl_ic)} "
          f"eklenen(pencere dışı)={len(ekl_dis)}  çıkan(pullback)={len(cikan_pb)} "
          f"çıkan(knock-on)={len(cikan_diger)}")
    print("\n-- kurulum kırılımı (n / ort-R / net P&L / kazanma):")
    for s, v in kirilim_yanyana.items():
        a, b = v["taban"], v["hucre"]
        fa = (f"{a['n']:4d} / {a['ort_r']} / {a['net_pnl']:+10.2f} / {a['kazanma_orani']}"
              if a else "        —")
        fb = (f"{b['n']:4d} / {b['ort_r']} / {b['net_pnl']:+10.2f} / {b['kazanma_orani']}"
              if b else "        —")
        print(f"   {s:20s} taban[{fa}]   hücre[{fb}]")
    print(f"\n-- KAPI İŞARETİ: {kapi_isareti['dal']}")
    print(f"-- kill: 1={kill1['tetiklendi']} 2={kill2['tetiklendi']} 3={kill3['tetiklendi']}")
    print(f"yazıldı: {yerel / f'sonuc{ek}.json'}")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "notrluk":
        notrluk(smoke=smoke)
    elif mod == "kiyas":
        kiyas(smoke=smoke)
    else:
        sys.exit("kullanım: olcum.py {taban|eksipb|notrluk|kiyas} [--smoke]")
