"""EDG-2026-020 · POST-EVENT in-play — ORTAK ÖLÇÜM ALTYAPISI.

Kart: research/cards/EDG-2026-020-postevent-inplay.yaml (status: registered).
KARTA DOKUNULMAZ · HÜKÜM VERİLMEZ · EŞİK ÖLÇÜMDEN SONRA DEĞİŞMEZ.

KÖKEN (yeniden kullanılan altyapı — kopya, yeniden tanım DEĞİL):
  research/olcumler/wp1_rvol_form/ortak017.py (EDG-2026-017, 2026-08-02) — motor sha256 kopyası,
  bar yolu, 21g blok-bootstrap, hızlı Spearman, temiz-taban maskesi ORADAN BİREBİR alındı.
  research/olcumler/kys_olcum/ortak_kys.py (KYS-2026-001) — takvim önbelleği okuma deseni.

BU DOSYANIN EKLEDİĞİ TEK YENİ ŞEY: **PIT KAPISI** (`gecikme_gunu`). Kartın guard'ı harfiyen
"yalnız e<=t; gelecek-tarih okuyan tek satır bile ihlaldir (test/assert ile çivilenir)" diyor.
Kapı bir `if` değil, bir DİLİM'dir: olay dizisi t'de KESİLİR (`ev[:j]`) ve fonksiyon o dilimin
dışındaki hiçbir öğeye DOKUNMAZ. Gelecek-tarih erişimi "yapılmıyor" değil, YAPILAMIYOR.

YASALAR
  * repo/state'e HİÇBİR yazım yok: config.STATE kum havuzuna çevrilir, barlar CANLI önbellekten
    SALT-OKUNUR okunur. Kum havuzu `state/earnings.csv`si TARİHSEL Nasdaq takvimiyle doldurulur
    (evaluate_pead'in çapası) — canlı `state/earnings.csv`ye TEK BAYT yazılmaz.
  * UYDURMA YASAĞI: ölçülemeyen her hücre None + neden.
  * Motor ÇALIŞMA AĞACINDAN KUM HAVUZUNA KOPYALANIR ve dosya bazında sha256 damgalanır.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib
import pickle
import shutil
import sys

REPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
KLASOR = pathlib.Path(__file__).resolve().parent            # research/olcumler/inplay_postevent
TAKVIM_KANIT = KLASOR / "takvim_kaniti"                     # arşivlenmiş Nasdaq gün-JSONL'leri
CALISMA = pathlib.Path("/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/"
                       "70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/inplay_postevent_calisma")
LIVE_STATE = REPO / "state"
LIVE_BARS = LIVE_STATE / "bars"
MOTOR = CALISMA / "_motor"
CACHE = CALISMA / "_cache"
for _p in (CALISMA, CACHE):
    _p.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ MOTOR ANLIK GÖRÜNTÜSÜ
def _motor_kopyala() -> dict:
    """meridian paketini kum havuzuna kopyala ve sha256 damgala (repo ↔ kopya)."""
    src = REPO / "meridian"
    if MOTOR.exists():
        shutil.rmtree(MOTOR)
    MOTOR.mkdir(parents=True)
    shutil.copytree(src, MOTOR / "meridian",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    damga = {}
    for p in sorted(src.rglob("*.py")):
        rel = str(p.relative_to(src))
        if "__pycache__" in rel:
            continue
        q = MOTOR / "meridian" / rel
        damga[rel] = {"repo": hashlib.sha256(p.read_bytes()).hexdigest()[:32],
                      "kopya": hashlib.sha256(q.read_bytes()).hexdigest()[:32]}
    return damga


MOTOR_DAMGA = _motor_kopyala()
sys.path.insert(0, str(MOTOR))

from meridian import config  # noqa: E402

config.STATE = CALISMA / "_state"
config.STATE.mkdir(parents=True, exist_ok=True)
config.HISTORY = config.STATE / "history"
config.BARS = LIVE_BARS
assert config.BARS == LIVE_BARS
assert config.STATE.resolve() != (REPO / "state").resolve(), "MÜHÜR TUTMADI"
_LEDGER_SRC = LIVE_STATE / "bars_integrity.json"
if _LEDGER_SRC.exists():          # kanonik defter yolu kum havuzunda da GERÇEKTEN koşsun
    shutil.copy2(_LEDGER_SRC, config.STATE / "bars_integrity.json")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from meridian import indicators as ind  # noqa: E402
from meridian import strategy as strat  # noqa: E402
from meridian.adapters import data as dat  # noqa: E402
from meridian.analytics import spearman_ic  # noqa: E402
from meridian.olcum_araclari import blok_bootstrap_ci, kod_surumu_damgasi, temiz_taban  # noqa: E402,F401

# ------------------------------------------------------------------ ŞABLON SABİTLERİ (017 ile aynı)
BLOCK = 21              # blok-bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ (kart: "21g blok CI")
BOOT = 2000
BOOT_IC = 600
MIN_SLICE = 30          # analytics.IC_MIN_SAMPLE tabanı (şablon)
MALIYET_BPS = 10.0      # kart cost_model: "10bps + 20bps duyarlılık"
MALIYET_BPS_DUYARLILIK = 20.0
BAR_MIN_UZUNLUK = ind.TREND_TEMPLATE_WARMUP + 60 + 5   # wp2/017 dalgasıyla BİREBİR aynı taban
RNG = np.random.default_rng(20260803)

# ---- KART SABİTLERİ (kart metninden; ÖLÇÜMDEN SONRA DEĞİŞMEZ) -----------------------------------
PENCERELER = (3, 5)     # parameter_grid.pencere_gun — K += 2
RVOL_ESIK = 1.5         # kart features_asof: rvol20(t) >= 1.5
UFUKLAR = (5, 10, 20)   # hüküm 10/20; 5 betimleyici olarak taşınır
# ÖLÇÜM ÖNCESİ BEYAN (kart bunu yazmıyor; ölçüm bir taban-eşiği seçmek ZORUNDA ve seçim ÖNCEDEN
# yazılır): birincil okuma min_taban=1 (kartın harfi — "aynı-gün havuz ortalaması"), min_taban=5
# yalnız DUYARLILIK satırıdır ve hükme GİRMEZ.
MIN_TABAN = 1
MIN_TABAN_DUYARLILIK = 5


def _r6(x):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(f) else round(f, 6)


# ==================================================================================================
# PIT KAPISI — kartın guard'ı (YAPISAL, bir `if` değil bir DİLİM)
# ==================================================================================================
def gecikme_gunu(olay_ord: np.ndarray, t_ord: np.ndarray) -> np.ndarray:
    """t − e (TAKVİM GÜNÜ), e = t'de GERÇEKLEŞMİŞ en yakın olay. Olay yoksa −1.

    PIT KAPISI YAPISALDIR. `np.searchsorted(ev, t, side="right")` t'den BÜYÜK ilk olayın
    indeksini verir; `ev[:j]` dilimi tanım gereği YALNIZ e <= t olan olayları içerir. Fonksiyon
    yalnız `ev[j-1]`i (yani o dilimin SON öğesini) okur ve j==0 olan satırlarda diziye HİÇ
    DOKUNMAZ (maskeli indeksleme). Gelecek tarih "okunmuyor" değil — OKUNAMIYOR.

    `olay_ord` ARTAN SIRADA olmak zorundadır (searchsorted sözleşmesi); sıralılık burada
    assert'lenir, çünkü sırasız bir dizide searchsorted sessizce yanlış bir komşu döndürür ve
    hata hiçbir yerde görünmez.
    """
    if olay_ord.size == 0:
        return np.full(t_ord.shape, -1, dtype=np.int64)
    assert np.all(np.diff(olay_ord) >= 0), "olay dizisi ARTAN SIRADA değil (searchsorted sözleşmesi)"
    j = np.searchsorted(olay_ord, t_ord, side="right")
    out = np.full(t_ord.shape, -1, dtype=np.int64)
    var = np.nonzero(j > 0)[0]                       # yalnız GEÇMİŞ olayı olan satırlar
    if var.size:
        e = olay_ord[j[var] - 1]                     # ev[:j] diliminin SON öğesi — e <= t GARANTİ
        # PIT ASSERT (satır başına, ucuz): seçilen olay t'yi AŞAMAZ.
        assert np.all(e <= t_ord[var]), "PIT İHLALİ: e > t olan bir olay seçildi"
        out[var] = t_ord[var] - e
    return out


def gecikme_gunu_saf(olay_listesi: list, t: int):
    """`gecikme_gunu`nun BAĞIMSIZ saf-python ikizi (PK5 özdeşliği). Aynı PIT kapısı, farklı kod:
    dizi TAM TARANIR ama yalnız e <= t olanlar aday havuzuna girer."""
    gecmis = [e for e in olay_listesi if e <= t]     # YAPISAL: koşul havuzun TANIMI
    return (t - max(gecmis)) if gecmis else -1


# ==================================================================================================
# TAKVİM — arşivlenmiş Nasdaq gün-JSONL'lerinden
# ==================================================================================================
def takvim_yukle(klasor: pathlib.Path = TAKVIM_KANIT) -> tuple[dict, dict]:
    """{TICKER: sorted[ISO tarih]} + muhasebe. Kaynak: `kys_olcum/takvim_cek.py`nin yazdığı
    gün-başına JSONL satırları (`{date, n_ham_sembol, syms}`) — o gün RAPORLAYAN semboller."""
    gunler: dict = {}
    acc = {"dosya": [], "satir": 0, "bozuk_satir": 0}
    for p in sorted(klasor.glob("gunler*.jsonl")):
        n = 0
        for satir in p.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if not satir:
                continue
            try:
                r = json.loads(satir)
            except json.JSONDecodeError:
                acc["bozuk_satir"] += 1              # sessiz düşürme YOK: sayılır ve rapora girer
                continue
            gunler[r["date"]] = r.get("syms") or []
            n += 1
        acc["dosya"].append({"ad": p.name, "satir": n,
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        acc["satir"] += n
    takvim: dict = {}
    for d, syms in gunler.items():
        for t in syms:
            takvim.setdefault(str(t).upper(), []).append(d)
    takvim = {t: sorted(set(ds)) for t, ds in takvim.items()}
    gs = sorted(gunler)
    acc.update({"tekil_gun": len(gunler), "gun_araligi": [gs[0], gs[-1]] if gs else None,
                "sembol": len(takvim), "olay_gunu": sum(len(v) for v in takvim.values()),
                "sembol_basina_medyan": (float(np.median([len(v) for v in takvim.values()]))
                                         if takvim else None),
                "kaynak": "Nasdaq anahtarsız takvim (adapters.data.nasdaq_earnings_window) — "
                          "kys_olcum/takvim_cek.py ile çekildi, bu klasöre ARŞİVLENDİ",
                "saat_alani": "YOK — takvim_cek.py:74 bmo/amc'yi süzüyor (keşif turu şerhi)"})
    return takvim, acc


def takvim_csv_yaz(takvim: dict, yol: pathlib.Path) -> int:
    """Kum havuzu `state/earnings.csv` — `evaluate_pead`in çapası buradan okunur.
    CANLI dosyaya DOKUNULMAZ (yol assert'lenir)."""
    assert str(yol).startswith(str(CALISMA)), f"KUM HAVUZU DIŞI YAZIM ENGELLENDİ: {yol}"
    yol.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(yol, "w") as fh:
        fh.write("ticker,date\n")
        for t in sorted(takvim):
            for d in takvim[t]:
                fh.write(f"{t},{d}\n")
                n += 1
    return n


def iso_ord(s) -> int:
    return _dt.date.fromisoformat(str(s)[:10]).toordinal()


# ==================================================================================================
# MOTOR DAMGASI — "bu sayı hangi kod BAYTLARIYLA üretildi?"
# ==================================================================================================
# NEDEN GİT SHA'SI YETMİYOR. `kod_surumu_damgasi` `kirli_agac: True` derse SHA o anki kodun değil
# ATASININ adıdır; üstelik bu depoda Rol-1 AJAN UÇUŞTAYKEN commit atar (CLAUDE.md md.8) — yani tek
# bir ölçüm turunun iki betiği İKİ FARKLI HEAD görebilir. Bu turda tam olarak bu oldu. Bu yüzden
# damga dosya-bazında sha256'dır: SHA değişse de ölçüme GİREN modüllerin baytları aynıysa iki
# çıktı aynı koddan gelmiştir ve bu KANITLANABİLİR.
OLCUME_GIREN_MODULLER = (
    "config.py", "indicators.py", "strategy.py", "earnings.py", "analytics.py",
    "olcum_araclari.py", "adapters/data.py", "obs.py", "store.py",
)


def motor_damgasi() -> dict:
    kritik = {m: (MOTOR_DAMGA.get(m) or {}).get("repo") for m in OLCUME_GIREN_MODULLER}
    eksik = [m for m, v in kritik.items() if v is None]
    tumu = hashlib.sha256(
        json.dumps({k: v["repo"] for k, v in sorted(MOTOR_DAMGA.items())},
                   sort_keys=True).encode()).hexdigest()
    ayrisan = [k for k, v in MOTOR_DAMGA.items() if v["repo"] != v["kopya"]]
    return {"n_dosya": len(MOTOR_DAMGA), "tum_agac_sha256": tumu,
            "olcume_giren_moduller": kritik, "kritik_modul_bulunamadi": eksik,
            "repo_kopya_ayrisan": ayrisan,
            "beyan": "sha256'lar REPO dosyalarının; 'repo_kopya_ayrisan' boş ise kum havuzundaki "
                     "kopya repo ile bit-bit aynıdır. İki çıktının aynı koddan geldiğini "
                     "'olcume_giren_moduller' sözlüklerinin eşitliği KANITLAR — git SHA'sı "
                     "kirli ağaçta bunu kanıtlayamaz."}


# ================================================================== BARLAR (ortak017 birebir)
def load_bars() -> tuple[dict, dict]:
    """Takvim kapısı (sanitize_bars) + bars_integrity GÜVENSİZ-DÖNEM dışlaması. İKİ YOL DA KOŞAR."""
    per, acc = {}, {"istenen": 0, "dosya_yok": 0, "okunamadi": 0, "kisa": 0, "yuklendi": 0,
                    "hayalet_dusen": 0, "karantina_dusen": 0, "takvim_reddedilen": [],
                    "defter_yolu_dusen": 0, "defter_yolu_sembol": 0,
                    "hesaplanan_dislanan_satir": 0, "iki_yol_ayrisan_sembol": [],
                    "kirilma_sinifi": {}, "kisa_semboller": []}
    for t in dat.REPLAY_UNIVERSE:
        acc["istenen"] += 1
        cp = dat._cache_path(t)
        if not cp.exists():
            acc["dosya_yok"] += 1
            continue
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
            df, rep = dat.sanitize_bars(raw, t)
        except Exception as e:                       # noqa: BLE001 — sayılır, yutulmaz
            acc["okunamadi"] += 1
            print(f"  ! bar okunamadi {t}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        acc["hayalet_dusen"] += int(rep.get("ghost_session_dropped") or 0)
        acc["karantina_dusen"] += int(rep.get("unadjusted_quarantined") or 0)
        if rep.get("calendar_mismatch_rows"):
            acc["takvim_reddedilen"].append(t)

        n_once = len(df)
        df = dat.measurement_bars(df, t)                    # (1) KANONİK defter yolu
        d_defter = n_once - len(df)
        acc["defter_yolu_dusen"] += d_defter
        acc["defter_yolu_sembol"] += int(d_defter > 0)

        try:                                                 # (2) HESAPLANAN yol
            ss, brk = dat.integrity_safe_start(df)
        except Exception as e:                               # noqa: BLE001
            ss, brk = None, []
            print(f"  ! integrity {t}: {type(e).__name__}: {e}", file=sys.stderr)
        for b in (brk or []):
            k = b.get("sinif", "?")
            acc["kirilma_sinifi"][k] = acc["kirilma_sinifi"].get(k, 0) + 1
        if ss:
            keep = df["date"].astype(str).str.slice(0, 10) >= ss
            ek = int((~keep).sum())
            acc["hesaplanan_dislanan_satir"] += ek
            if ek > 0 and d_defter > 0:
                acc["iki_yol_ayrisan_sembol"].append(t)
            df = df.loc[keep].reset_index(drop=True)

        if df is None or len(df) < BAR_MIN_UZUNLUK:
            acc["kisa"] += 1
            acc["kisa_semboller"].append(t)
            continue
        per[t] = df.reset_index(drop=True)
        acc["yuklendi"] += 1
    return per, acc


def bar_paneli(per: dict, ufuklar=UFUKLAR) -> dict:
    """Sembol → {dates, close, volume, fwd{h}, chain{h}, rvol20, ret63}."""
    out = {}
    for t, df in per.items():
        close = df["close"].to_numpy(float)
        vol = df["volume"].to_numpy(float)
        n = len(df)
        dates = df["date"].dt.strftime("%Y-%m-%d").to_numpy()
        rec = {"dates": dates, "close": close, "volume": vol}
        for h in ufuklar:
            f = np.full(n, np.nan)
            f[:n - h] = close[h:] / close[:n - h] - 1.0
            rec[f"fwd{h}"] = f
        ret = np.full(n, np.nan)
        ret[1:] = close[1:] / close[:-1] - 1.0
        lr = pd.Series(np.log1p(ret))
        for h in ufuklar:                                    # PK4 için BAĞIMSIZ zincir yolu
            rec[f"chain{h}"] = np.expm1(
                lr.shift(-1).rolling(h).sum().shift(-(h - 1))).to_numpy(float)
        # CANLI TANIM (indicators.rvol20 = hacim / SMA20(hacim)) — kart "canlı tanımla BİREBİR"
        rec["rvol20"] = ind.rvol20(df["volume"]).to_numpy(float)
        # RS çapraz-kesiti için 63 barlık geriye getiri (backtest.py:295 ile AYNI tanım)
        L = strat.RS_LOOKBACK
        r63 = np.full(n, np.nan)
        if n > L:
            r63[L:] = close[L:] / close[:n - L] - 1.0
        rec["ret63"] = r63
        out[t] = rec
    return out


def bars_cached():
    p = CACHE / "bars020.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    per, acc = load_bars()
    pan = bar_paneli(per)
    obj = (pan, acc)
    with open(p, "wb") as fh:
        pickle.dump(obj, fh, protocol=4)
    return obj


# ================================================================== İSTATİSTİK (ortak017 birebir)
def block_boot(stat_fn, dates: np.ndarray, n_boot: int = BOOT) -> dict:
    """21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap (MOVING blok, sarılma yok)."""
    uniq, inv = np.unique(dates, return_inverse=True)
    rows_by_date = [np.where(inv == i)[0] for i in range(len(uniq))]
    nd = len(uniq)
    if nd < BLOCK * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {BLOCK * 3} (blok bootstrap için yetersiz)"}
    n_blok = int(np.ceil(nd / BLOCK))
    son_bas = nd - BLOCK
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = np.concatenate([np.arange(b, b + BLOCK) for b in bas])[:nd]
        idx = np.concatenate([rows_by_date[g] for g in gun])
        v = stat_fn(idx)
        if v is None or not np.isfinite(v):
            atlanan += 1
            continue
        vals.append(v)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": BLOCK, "atlanan": atlanan,
            "neden": None}


def mean_block_boot(y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    """block_boot'un ORTALAMA istatistiği için cebirsel özdeş hızlı yolu (PK5-C bunu sınar)."""
    uniq, inv = np.unique(dates, return_inverse=True)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3} (blok bootstrap için yetersiz)"}
    sums = np.bincount(inv, weights=y, minlength=nd)
    cnts = np.bincount(inv, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnts[gun].sum()
        if c <= 0:
            atlanan += 1
            continue
        vals.append(sums[gun].sum() / c)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "neden": None}


def mean_with_ci(y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    n = int(len(y))
    if n < MIN_SLICE:
        return {"n": n, "ort": None, "ci": None, "anlamli": None, "pozitif_anlamli": None,
                "negatif_anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ci = mean_block_boot(y, dates, n_boot, blok)
    return {"n": n, "ort": _r6(float(np.mean(y))), "medyan": _r6(float(np.median(y))),
            "std": _r6(float(np.std(y, ddof=1))), "pozitif_oran": _r6(float((y > 0).mean())),
            "ci": None if ci["lo"] is None else {"lo": ci["lo"], "hi": ci["hi"], "seviye": 0.95},
            "ci_meta": ci,
            "anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0 or ci["hi"] < 0),
            "pozitif_anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0),
            "negatif_anlamli": None if ci["lo"] is None else bool(ci["hi"] < 0),
            "neden": None}


def fark_with_ci(yA: np.ndarray, dA: np.ndarray, yB: np.ndarray, dB: np.ndarray,
                 n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    """A ve B dilimlerinin ORTALAMA FARKI (A−B) + 21g blok CI; bootstrap AYNI gün dizisini iki
    dilime de uygular (ortak takvim) → fark istatistiği gün-etkisinden arınır."""
    if len(yA) < MIN_SLICE or len(yB) < MIN_SLICE:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": f"dilimlerden biri n<{MIN_SLICE}"}
    uniq = np.unique(np.concatenate([dA, dB]))
    nd = len(uniq)
    if nd < blok * 3:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": f"ortak gözlem günü < {blok * 3}"}
    ia = np.searchsorted(uniq, dA)
    ib = np.searchsorted(uniq, dB)
    sA = np.bincount(ia, weights=yA, minlength=nd)
    cA = np.bincount(ia, minlength=nd).astype(float)
    sB = np.bincount(ib, weights=yB, minlength=nd)
    cB = np.bincount(ib, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        ca, cb = cA[gun].sum(), cB[gun].sum()
        if ca <= 0 or cb <= 0:
            atlanan += 1
            continue
        vals.append(sA[gun].sum() / ca - sB[gun].sum() / cb)
    if len(vals) < n_boot * 0.5:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    lo, hi = _r6(np.percentile(a, 2.5)), _r6(np.percentile(a, 97.5))
    return {"nA": int(len(yA)), "nB": int(len(yB)),
            "fark": _r6(float(np.mean(yA)) - float(np.mean(yB))),
            "ci": {"lo": lo, "hi": hi, "seviye": 0.95},
            "n_gun": nd, "blok": blok, "n_boot_gecerli": len(vals), "atlanan": atlanan,
            "anlamli": bool(lo > 0 or hi < 0), "pozitif_anlamli": bool(lo > 0),
            "negatif_anlamli": bool(hi < 0), "neden": None}


def _rank_avg_np(a: np.ndarray) -> np.ndarray:
    return pd.Series(a).rank().to_numpy()


def spearman_fast(x: np.ndarray, y: np.ndarray):
    rx, ry = _rank_avg_np(x), _rank_avg_np(y)
    sx, sy = rx.std(), ry.std()
    if sx <= 0 or sy <= 0:
        return None
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _gun_indeksi(dates: np.ndarray):
    uniq, inv = np.unique(dates, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cnt = np.bincount(inv, minlength=len(uniq))
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    return uniq, order, start, cnt


def ic_block_boot_fast(x: np.ndarray, y: np.ndarray, dates: np.ndarray,
                       n_boot: int = BOOT_IC, blok: int = BLOCK) -> dict:
    """block_boot ile AYNI şema, IC istatistiği için vektörel yol. Özdeşliği PK5-E'de sınanır."""
    uniq, order, start, cnt = _gun_indeksi(dates)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3} (blok bootstrap için yetersiz)"}
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnt[gun]
        tot = int(c.sum())
        if tot < MIN_SLICE:
            atlanan += 1
            continue
        cikis_bas = np.concatenate([[0], np.cumsum(c)[:-1]])
        poz = np.arange(tot) - np.repeat(cikis_bas, c) + np.repeat(start[gun], c)
        idx = order[poz]
        v = spearman_fast(x[idx], y[idx])
        if v is None or not np.isfinite(v):
            atlanan += 1
            continue
        vals.append(v)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "neden": None}


def ic_with_ci(x: np.ndarray, y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT_IC) -> dict:
    """KANONİK IC yolu (analytics.spearman_ic + block_boot). Pozitif kontrol bunu kullanır."""
    if len(x) < MIN_SLICE:
        return {"ic": None, "n": int(len(x)), "ci": None, "anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ic = spearman_ic(list(zip(x.tolist(), y.tolist())))
    if ic is None:
        return {"ic": None, "n": int(len(x)), "ci": None, "anlamli": None,
                "neden": "rütbe değişimi yok"}

    def _stat(idx):
        v = spearman_ic(list(zip(x[idx].tolist(), y[idx].tolist())))
        return None if v is None else float(v)

    ci = block_boot(_stat, dates, n_boot=n_boot)
    return {"ic": round(float(ic), 4), "n": int(len(x)),
            "ci": None if ci["lo"] is None else {"lo": round(ci["lo"], 4),
                                                 "hi": round(ci["hi"], 4), "seviye": 0.95},
            "ci_meta": ci,
            "anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0 or ci["hi"] < 0),
            "neden": None}


def ic_hizli(x: np.ndarray, y: np.ndarray, dates: np.ndarray, ci: bool = True) -> dict:
    """Nokta tahmini KANONİK analytics.spearman_ic ile; CI hızlı blok-bootstrap ile."""
    n = int(len(x))
    if n < MIN_SLICE:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ic = spearman_ic(list(zip(x.tolist(), y.tolist())))
    if ic is None:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": "rütbe değişimi yok"}
    if not ci:
        return {"ic": round(float(ic), 4), "n": n, "ci": None, "anlamli": None,
                "neden": "CI istenmedi (tanı okuması — kart bacağı değil)"}
    c = ic_block_boot_fast(x, y, dates)
    return {"ic": round(float(ic), 4), "n": n,
            "ci": None if c["lo"] is None else {"lo": round(c["lo"], 4),
                                                "hi": round(c["hi"], 4), "seviye": 0.95},
            "ci_meta": c,
            "anlamli": None if c["lo"] is None else bool(c["lo"] > 0 or c["hi"] < 0),
            "pozitif_anlamli": None if c["lo"] is None else bool(c["lo"] > 0),
            "negatif_anlamli": None if c["lo"] is None else bool(c["hi"] < 0),
            "neden": None}


# ================================================================== ADAY HAVUZU (cf katmanı)
def aday_havuzu() -> tuple[list, dict]:
    """EDG-011 ile BİREBİR popülasyon: counterfactuals.jsonl entered=True (near_miss DAHİL)
    + cf_open.json; TEKİL (ticker, date). Kart `universe` alanı evren KAPSAMASINI beyan eder;
    ölçüm kesiti ADAY kesitidir (011'in `universe` satırı: 'cf-katmanlı aday popülasyonu')."""
    ham, acc = [], {"cf_satir": 0, "cf_girilmemis": 0, "cf_eksik_alan": 0,
                    "open_satir": 0, "open_eksik_alan": 0}
    with open(LIVE_STATE / "counterfactuals.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            acc["cf_satir"] += 1
            if not r.get("entered"):
                acc["cf_girilmemis"] += 1
                continue
            if not r.get("ticker") or not r.get("date"):
                acc["cf_eksik_alan"] += 1
                continue
            ham.append((str(r["ticker"]).upper(), str(r["date"])[:10]))
    with open(LIVE_STATE / "cf_open.json") as fh:
        for r in json.load(fh):
            acc["open_satir"] += 1
            if not r.get("ticker") or not r.get("date"):
                acc["open_eksik_alan"] += 1
                continue
            ham.append((str(r["ticker"]).upper(), str(r["date"])[:10]))
    acc["ham_aday_satiri"] = len(ham)
    tekil = sorted(set(ham))
    acc["tekillestirmede_dusen"] = len(ham) - len(tekil)
    acc["tekil_aday_gun"] = len(tekil)
    return tekil, acc


def json_yaz(p: pathlib.Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
