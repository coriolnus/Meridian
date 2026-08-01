"""Central config + path resolution. Loads the immutable goal.yaml/bounds.yaml and the
mutable strategy.yaml. Nothing here talks to a broker or the network."""
from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache
import yaml

# Project root = the directory that contains state/ and skills/
ROOT = Path(os.environ.get("MERIDIAN_ROOT", Path(__file__).resolve().parent.parent))
STATE = ROOT / "state"
SKILLS = ROOT / "skills"
BARS = STATE / "bars"
HISTORY = STATE / "history"

# Operating mode. L0 default. The live path is only importable when BOTH are set by a human.
MODE = os.environ.get("MERIDIAN_MODE", "paper").lower()
I_ACCEPT_RISK = os.environ.get("MERIDIAN_I_ACCEPT_RISK", "false").lower() == "true"

# Live-execution BACKEND — which venue the live loop mirrors fills to. BOTH options are PAPER (no real
# money): "internal" = the in-process simulator (default); "alpaca_paper" = mirror the agent's decisions
# to your Alpaca PAPER account. This is INDEPENDENT of MODE/I_ACCEPT_RISK (those gate REAL money only).
BROKER = os.environ.get("MERIDIAN_BROKER", "internal").lower()

def live_enabled() -> bool:
    """Live trading is gated behind two hand-set env flags AND autonomy_level>=1 in goal.yaml.
    Guard.py enforces autonomy_level; this only governs whether the live adapter may be imported."""
    return MODE == "live" and I_ACCEPT_RISK


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"required config missing: {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def _goal_cached() -> dict:
    return _read_yaml(STATE / "goal.yaml")


def goal() -> dict:
    """Immutable success/failure/risk contract. Hermes may never edit the file behind this.

    DERİN KOPYA (2026-07-22, öğrenme-döngüsü denetimi): `lru_cache` AYNI sözlüğü geri veriyordu, yani
    herhangi bir modül `goal()["min_sample"] = 1` yazınca sonraki HER okuyucu — kapı, rollback eşiği,
    aylık kota — o değeri görüyordu. Dosyada değişiklik yok, alarm yok, iz yok. "Değişmez sözleşme"
    yalnız DOSYA için geçerliydi; bellekteki kopya serbestti."""
    import copy
    return copy.deepcopy(_goal_cached())


@lru_cache(maxsize=1)
def _bounds_cached() -> dict:
    return _read_yaml(STATE / "bounds.yaml")


def bounds() -> dict:
    """The sandbox Hermes may move parameters inside. Derin kopya — bkz. goal() gerekçesi."""
    import copy
    return copy.deepcopy(_bounds_cached())


# `goal.cache_clear()` / `bounds.cache_clear()` çağrıları KORUNUR (config.reload_config, conftest):
# sarmalayıcı derin kopya yapar, önbellek yine altta durur.
goal.cache_clear = _goal_cached.cache_clear       # type: ignore[attr-defined]
bounds.cache_clear = _bounds_cached.cache_clear   # type: ignore[attr-defined]


def limits() -> dict:
    return goal()["limits"]


# --- WP-M: CANLI-BEKLENTİ TAVANI (ROADMAP §WP-M borç kalemi, 2026-08-01) -------------------------
# KURAL (ROADMAP'te yazılı, bugüne kadar HİÇBİR KOD OKUMUYORDU): canlı beklenti tavanı =
# backtest × 0,5; canlı/backtest oranı × 0,4'ün altına düşerse SÜSPANSİYON DEĞERLENDİRMESİ.
# Yazılı ama bağlanmamış bir kural, `explore_rate`/`kill_switch_file` sınıfındadır: operatör onu
# yürürlükte sanır, gerçekte hiçbir yüzey onu ölçmez. Bu tur kuralı KONFİGÜRE EDİLEBİLİR yapar ve
# ölçülür kılar — HÜKÜM VERDİRMEZ (bkz. analytics.live_expectancy_ceiling'in `hukme_girmez`i).
#
# VARSAYILAN NEDEN KODDA, goal.yaml'da DEĞİL: goal.yaml DEĞİŞMEZ sözleşmedir ve bu turda
# DOKUNULMADI (dosyaya yeni alan yazmak, canlı state'e yazmaktır — bu depoda ayrı bir yetki).
# Kod varsayılanı sayesinde alanlar goal.yaml'da OLMASA DA kural yürürlüktedir; operatör bir gün
# `live_expectancy_cap_mult` / `live_suspend_ratio` anahtarlarını dosyaya yazarsa DOSYA KAZANIR.
# Kaynak her okumada ADIYLA raporlanır (`kaynak` alanı) ki "0,5 nereden geldi?" sorusu tahminle
# cevaplanmasın.
#
# GUARD ŞERHİ: bu iki ad `guard.GOAL_KEYS` içinde DEĞİLDİR, yani bugün Hermes'in önerebileceği bir
# değişken adı da değildir (`bounds.yaml`da yoklar → `classify_proposal` zaten reddeder). Operatör
# alanları goal.yaml'a yazmaya karar verirse GOAL_KEYS'e de eklenmelidir — aksi hâlde GU1
# sürüklenme testi "goal.yaml'da tanınmayan anahtar" diye kırmızı yanar. Bu, unutulmasın diye
# burada yazılıdır ve `docs/olcum_standartlari.md`de tekrarlanır.
LIVE_EXPECTANCY_CAP_MULT = 0.5    # canlıdan BEKLENEN tavan = backtest beklentisi × bu katsayı
LIVE_SUSPEND_RATIO = 0.4          # canlı/backtest bu oranın ALTINA düşerse süspansiyon değerlendirmesi
_LIVE_EXPECTANCY_ALANLARI = (("live_expectancy_cap_mult", LIVE_EXPECTANCY_CAP_MULT),
                             ("live_suspend_ratio", LIVE_SUSPEND_RATIO))


def live_expectancy_rule(goal_doc: dict | None = None) -> dict:
    """Canlı-beklenti tavanı kuralının YÜRÜRLÜKTEKİ değerleri + her değerin KAYNAĞI.

    Dönüş: {"cap_mult", "suspend_ratio", "kaynak": {alan: "goal.yaml"|"kod varsayilani"},
            "kural_metni", "uyari"}.

    ÜÇ DÜRÜSTLÜK KURALI:
      (1) goal.yaml'da alan YOKSA kod varsayılanı kullanılır ve `kaynak` bunu söyler — sessiz bir
          varsayılan, okuyucuya "operatör böyle yazmış" izlenimi verirdi.
      (2) GEÇERSİZ değer (sayı değil / (0,1] dışında) SESSİZCE kabul EDİLMEZ: uyarılır (YASA 4) ve
          kod varsayılanına düşülür. Bir tavan katsayısının 0 ya da negatif olması "tavan yok"
          demek değil, ölçümü anlamsız kılmak demektir.
      (3) suspend_ratio > cap_mult TUTARSIZDIR — süspansiyon eşiği beklenti tavanının ÜSTÜNDEyse
          tavanın altındaki her NORMAL sonuç aynı anda süspansiyon adayı olurdu. Bu durumda İKİ
          alan birden kod varsayılanına döner ve gerekçe `uyari` alanında taşınır.

    Saf okuma: hiçbir dosyaya yazmaz, hiçbir davranışı değiştirmez."""
    if goal_doc is None:
        try:
            goal_doc = goal()
        except (OSError, ValueError) as e:
            # YASA 4: goal.yaml okunamıyorsa kural yine yürür (varsayılanlar kodda) ama bu SESSİZ
            # kalamaz — okunamayan bir sözleşme, "alan yazılmamış" ile aynı şey değildir.
            try:
                from . import obs
                obs.warn("live_expectancy_goal_unreadable", error=f"{type(e).__name__}: {e}")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok ve kural okuması bundan ötürü durduramaz
                pass
            goal_doc = {}
    if not isinstance(goal_doc, dict):
        goal_doc = {}

    degerler, kaynak, uyarilar = {}, {}, []
    for ad, varsayilan in _LIVE_EXPECTANCY_ALANLARI:
        ham = goal_doc.get(ad)
        if ham is None:
            degerler[ad], kaynak[ad] = varsayilan, "kod varsayilani"
            continue
        try:
            v = float(ham)
        except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen değer AŞAĞIDA geçersiz sayılır, uyarı listesine adıyla girer ve obs.warn ile bir kez duyurulur — burada susmak kaydı ERTELER, yutmaz
            v = None
        if v is None or not (0.0 < v <= 1.0):
            uyarilar.append(f"{ad}={ham!r} geçersiz (sayı ve (0,1] aralığında olmalı) — "
                            f"kod varsayılanı {varsayilan} kullanıldı")
            degerler[ad], kaynak[ad] = varsayilan, "kod varsayilani (goal.yaml degeri gecersiz)"
        else:
            degerler[ad], kaynak[ad] = v, "goal.yaml"

    if degerler["live_suspend_ratio"] > degerler["live_expectancy_cap_mult"]:
        uyarilar.append(
            f"tutarsız kural: live_suspend_ratio ({degerler['live_suspend_ratio']}) > "
            f"live_expectancy_cap_mult ({degerler['live_expectancy_cap_mult']}) — süspansiyon eşiği "
            f"beklenti tavanının üstünde olamaz; İKİ alan da kod varsayılanına döndürüldü")
        for ad, varsayilan in _LIVE_EXPECTANCY_ALANLARI:
            degerler[ad], kaynak[ad] = varsayilan, "kod varsayilani (goal.yaml kurali tutarsiz)"

    if uyarilar:
        try:
            from . import obs
            obs.warn("live_expectancy_rule_invalid", detail=" · ".join(uyarilar))
        except Exception:  # sessiz-yutma: kayıt kanalı düştü — uyarı metni yine dönüş sözlüğünde taşınır, yani kayıp değil
            pass

    return {"cap_mult": degerler["live_expectancy_cap_mult"],
            "suspend_ratio": degerler["live_suspend_ratio"],
            "kaynak": kaynak,
            "varsayilanlar": {"live_expectancy_cap_mult": LIVE_EXPECTANCY_CAP_MULT,
                              "live_suspend_ratio": LIVE_SUSPEND_RATIO},
            "kural_metni": ("canlı beklenti TAVANI = backtest beklentisi × cap_mult; "
                            "canlı/backtest oranı suspend_ratio'nun ALTINDAysa SÜSPANSİYON "
                            "DEĞERLENDİRMESİ (ROADMAP §WP-M)"),
            "uyari": (" · ".join(uyarilar) if uyarilar else None)}


def strategy_path() -> Path:
    return STATE / "strategy.yaml"


def load_strategy() -> dict:
    """The mutable, versioned parameter set. Falls back to defaults if not yet written.

    BOŞ/BOZUK DOSYA KORUMASI (denetim turu 10, 2026-07-21): `yaml.safe_load(f) or {}` boş bir
    strategy.yaml için **{}** döndürüyordu — default_strategy() DEĞİL. O durumda motor params={}
    ile koşar: her eşik kaybolur, kapı parametresiz bir aday ölçer ve hiçbir yerde hata görünmez.
    #32 atomik yazımı yarım dosyayı çözdü ama SIFIR baytlık/şemasız dosya yolu açıktı."""
    p = strategy_path()
    if not p.exists():
        return default_strategy()
    _err = None
    try:
        with open(p) as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        # YASA 4 (2026-07-21): aşağıdaki uyarı "kullanılamaz" diyordu ama NEDEN'i yutuluyordu —
        # bozuk YAML mı, izin hatası mı, disk mi? Motor varsayılan parametrelerle koşmaya devam
        # ettiği için operatörün elinde tek ipucu "got=NoneType" kalıyordu. Tür artık taşınıyor.
        doc, _err = None, f"{type(e).__name__}: {e}"
    if not isinstance(doc, dict) or not doc.get("params"):
        try:
            from . import obs
            obs.warn("strategy_file_unusable", path=str(p), got=type(doc).__name__, error=_err)
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        return default_strategy()
    return doc


def reload_config() -> None:
    """goal/bounds ÖNBELLEĞİNİ boşalt. lru_cache(maxsize=1) uzun ömürlü sunucu sürecinde dosyayı
    SONSUZA kadar dondurur: operatör goal.yaml'daki limiti elle değiştirdiğinde çalışan süreç eski
    değeri kullanmaya devam eder ve bunu hiçbir yerde söylemez (denetim turu 10)."""
    goal.cache_clear()
    bounds.cache_clear()


# Must match exactly the labels regime.py emits — else a `var@regime` knob for a real regime is rejected
# as "unknown regime" (trend_down/high_vol), and a knob for a phantom regime (risk_off) is silently dead.
VALID_REGIMES = ("trend_up", "trend_down", "chop", "high_vol")


# --- G3b ④ REJİM-KOŞULLU ÇIKIŞ ALTYAPISI (ROADMAP §3.2, 2026-07-30) ------------------------------
# Rejim başına çözülmesine İZİN VERİLEN çıkış anahtarları — flat params'ta OLMASALAR BİLE.
#
# ÖNCE DÜRÜST TESPİT: "params_by_regime yalnız girişte çalışıyor" TAM DOĞRU DEĞİLDİ. Replay ve canlı
# döngü ikisi de CLOSE(D)'de `resolve_params` çağırıp sonucu `manage_position`a veriyor, yani flat
# params'ta BULUNAN çıkış knob'ları (exit.time_stop_days, exit.trail_atr_mult, exit.breakeven_r,
# exit.profit_target_r) rejim başına ZATEN çözülüyordu. Gerçek boşluk daha dar ve daha sinsiydi:
# overlay YALNIZ `k in params` olduğunda uygulandığı için, strategy.yaml'ın TAŞIMADIĞI bir knob için
# yazılmış bir rejim override'ı SESSİZCE DÜŞÜYORDU. Batch L deseniyle eklenen her yeni knob (giveback,
# chandelier, scale_out ve şimdi G3b'nin dördü) tam bu sınıftadır: bounds'ta var, flat params'ta yok.
# Yani "rejim başına erken itlaf" denemesi, denenmiş sanılırken hiç denenmemiş olurdu.
#
# NEDEN LİSTE, NEDEN GENEL BİR GEVŞETME DEĞİL: `k in params` kuralının VAR OLMA SEBEBİ bir knob
# İCADINI engellemek — yazım hatalı bir anahtar ("exit.time_stop_dayz") sessizce yeni bir parametre
# doğurmasın. O korumayı topluca kaldırmak, kuralı doğuran hatayı geri getirirdi. Bu yüzden izin
# ADIYLA verilir: aşağıdaki anahtarlar bounds.yaml'da tanımlı, motorun GERÇEKTEN okuduğu çıkış
# knob'larıdır. Liste dışı bir anahtar eskisi gibi düşer.
#
# SIFIR-ETKİ: bugünün canlı durumu `params_by_regime = {rejim: {} for …}` (boş) olduğu için aşağıdaki
# döngü gövdesi HİÇ çalışmaz → dönen sözlük flat params'ın kopyasıdır, davranış BİREBİR eskisidir.
# Flat params'ta BULUNAN bir anahtarın override'ı da eskisi gibi uygulanır. Değişen TEK hâl: flat
# params'ta olmayan bir ÇIKIŞ anahtarı için yazılmış override artık sessizce düşmez.
#
# KALAN DİKİŞ (3b'ye devir): `guard.classify_proposal` hâlâ `base not in current_params` diye
# reddediyor — yani Hermes bu türden bir hipotezi ÖNEREMEZ (ve reddi DÜRÜSTTÜR: bugüne kadar override
# gerçekten düşüyordu). Sevk yetkisini açmak ayrı bir karardır; bu tur yalnız ALTYAPIyı kurar, öyle ki
# ölçüm yolu (walk_forward'a doğrudan params_by_regime geçen kum havuzu scripti) rejim-koşullu bir
# çıkışı GERÇEKTEN simüle edebilsin.
REGIME_EXIT_KEYS = (
    "exit.time_stop_days", "exit.trail_atr_mult", "exit.breakeven_r", "exit.profit_target_r",
    "exit.giveback_pct", "exit.chandelier_lookback", "exit.scale_out_r", "exit.scale_out_frac",
    "exit.early_kill_pivot", "exit.early_kill_bars",          # G3b ①
    "stop_loss_atr_mult", "stop_mode", "stop_buffer_atr",     # G3b ② (stop da bir çıkış parametresidir)
)


def resolve_params(params: dict, by_regime: dict | None, regime: str) -> dict:
    """Effective flat params for a regime = base params overlaid with that regime's overrides.
    Only keys that already exist in base params — OR are named in REGIME_EXIT_KEYS (G3b ④, see the
    block above) — are overlaid, so an override can retune a real knob but never invent one. With no
    overrides (the default) this returns an unchanged copy and behavior is byte-identical to the
    flat-param engine. Overrides live at strategy['params_by_regime'][regime], keeping params itself a
    flat float map (so the reflect cache key and scoreboard stay simple)."""
    eff = dict(params)
    if by_regime:
        for k, v in (by_regime.get(regime) or {}).items():
            if k in params or k in REGIME_EXIT_KEYS:
                eff[k] = v
    return eff


def default_strategy() -> dict:
    """v01 seed params. Every value sits inside bounds.yaml. Midpoint-ish, sensible for swing momentum."""
    return {
        "version": 1,
        "params": {
            "entry.rs_rating_min": 70,
            "entry.pivot_proximity_pct": 2.0,
            "entry.min_volume_ratio": 1.5,
            "entry.min_score": 60,
            "exit.profit_target_r": 2.5,
            "exit.time_stop_days": 15,
            "exit.trail_atr_mult": 2.5,
            "exit.breakeven_r": 1.0,
            "stop_loss_atr_mult": 2.0,
            "position_size_r": 1.0,
            "regime.min_exposure_score": 40,
            "exit.giveback_pct": 0.0,          # Batch L — default OFF (Hermes can turn on)
            "exit.chandelier_lookback": 0,
            "entry.max_ext_atr": 0.0,
            "entry.rs_dual_horizon": 0,
            "exit.scale_out_r": 2.0,
            "exit.scale_out_frac": 0.0,        # OFF by default
        },
        "parent": None,
        "note": "v01 seed",
        # Phase 3 dynamic regime profiles: per-regime parameter overrides, keyed by the exact P1_REGIME
        # labels. AUTHORITATIVE schema slot (always present), consumed live by resolve_params at P2/P3.
        # Maps start EMPTY on purpose — identity-seeding them with copies of the global values would make
        # every later gate-approved GLOBAL change silently shadowed per-regime (regimes frozen at old
        # values). A regime map gains an entry ONLY when a var@regime hypothesis clears the OOS gate.
        "params_by_regime": {r: {} for r in VALID_REGIMES},
    }


def dump_yaml(obj: dict, path: Path) -> None:
    """ATOMIC yaml write (mkstemp + os.replace) — strategy.yaml is HOT-RELOADED and read concurrently by
    the scheduler cycle, the Hermes reflection thread, and API handlers. A plain truncate-then-write let
    a reader land mid-write and get {} → params={}, version=1 fallback for that cycle (audit #32)."""
    import os as _os
    import tempfile as _tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = _tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with _os.fdopen(fd, "w") as f:
            yaml.safe_dump(obj, f, sort_keys=False)
        _os.replace(tmp, path)
    except BaseException:
        try:
            _os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass
        raise
