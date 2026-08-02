"""ortak_kys.py — KYS-2026-001 ölçüm turunun ORTAK ZEMİNİ (mühür + tanım + panel).

BU DOSYA HÜKÜM VERMEZ, KARTA DOKUNMAZ. Yalnız üç şeyi tek yerde tutar:

  1. SALT-ÖLÇÜM MÜHRÜ (`muhurle`) — `MERIDIAN_ROOT` bir kum-havuzuna çevrilir ve `meridian.config`
     ithal EDİLMEDEN ÖNCE bu yapılır. Gerekçe: `config.ROOT` ortam değişkenini İTHALAT ANINDA okur
     (config.py:10); ithalattan sonra çevirmek geç kalır. Böylece `obs.warn` (bar hayaleti,
     karantina), `store.append_jsonl` ve bar onarımı canlı `state/`e DEĞİL kopyaya yazar.
     EAP turunun (2026-07-31) kayıtlı kazası tam olarak buydu: ölçüm başında canlı
     `state/events.jsonl`e 5 satır düşmüştü.

  2. OLAY PENCERESİ TANIMI (`PENCERE`) — `earnings.in_blackout` ile BİREBİR. Kart `features_asof`
     alanında bunu şart koşuyor; eşdeğerlik VARSAYILMAZ, PK'de sembol sembol DOĞRULANIR
     (`pk_kys.py`, PK-0).

         in_blackout: 0 <= (olay_günü − gün) <= BLACKOUT_DAYS(=5)
         olay_disi_kiyas: -once <= (gün − olay_günü) <= sonra
         ⇒ once = BLACKOUT_DAYS = 5,  sonra = 0

     Yani pencere kazanç gününün KENDİSİ ve ONDAN ÖNCEKİ 5 TAKVİM GÜNÜDÜR; rapor sonrası günler
     karartmada DEĞİLDİR (PEAD çapası ayrı bir tanımdır — `days_since_report`, bu ölçümde
     kullanılmaz).

  3. PANEL — barlar kum-havuzu kopyasından, deponun KENDİ `sanitize_bars`/`measurement_bars`
     kapısından geçirilerek okunur. Kapı yeniden yazılmaz, ÇAĞRILIR (hayalet seans / ölçek
     kırılması dersleri: 2025-05-26 sınıfı).
"""
from __future__ import annotations

import os
import pathlib
import sys

KUM_HAVUZU = pathlib.Path(
    "/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/"
    "70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/kys_root")
DEPO = pathlib.Path(__file__).resolve().parents[3]
CIKTI = pathlib.Path(__file__).resolve().parent
TAKVIM_ONBELLEK = KUM_HAVUZU / "cal_cache"          # Nasdaq gün-JSON önbelleği (kum havuzunda)

# PENCERE — `earnings.in_blackout` ile birebir (bkz. modül başlığı, madde 2).
BLACKOUT_DAYS = 5
PENCERE = (BLACKOUT_DAYS, 0)


def muhurle() -> pathlib.Path:
    """SALT-ÖLÇÜM MÜHRÜ: meridian ithalatından ÖNCE çağrılmalıdır. Kum havuzu kökünü döner.

    TEKRAR ÇAĞRILABİLİR (bir betik mühürlü bir başkasını ithal edebilsin diye) AMA SESSİZ DEĞİL:
    `meridian.config` zaten yüklüyse mühür ancak kök ZATEN kum havuzuysa geçerlidir; başka bir kökle
    yüklenmişse süreç canlı state'e yazabilir ve ölçüm DURUR. "İkinci çağrıyı yok say" demek, geç
    kalmış bir mührü sessizce onaylamak olurdu."""
    zaten = os.environ.get("MERIDIAN_ROOT")
    if "meridian.config" in sys.modules and zaten != str(KUM_HAVUZU):
        raise RuntimeError(f"meridian.config ZATEN ithal edilmiş ve kök kum havuzu DEĞİL "
                           f"({zaten!r}) — mühür GEÇ kaldı; bu süreç canlı state'e yazabilir "
                           f"(ölçüm durdu)")
    (KUM_HAVUZU / "state").mkdir(parents=True, exist_ok=True)
    os.environ["MERIDIAN_ROOT"] = str(KUM_HAVUZU)
    if str(DEPO) not in sys.path:
        sys.path.insert(0, str(DEPO))
    return KUM_HAVUZU


def muhur_dogrula() -> dict:
    """Mühür TUTTU MU — canlı state'e yazma ihtimali kalmadığının kanıtı (rapora basılır)."""
    from meridian import config
    canli = DEPO / "state"
    if config.STATE.resolve() == canli.resolve():
        raise RuntimeError(f"MÜHÜR TUTMADI — config.STATE canlı state'i gösteriyor: {config.STATE}")
    return {"config_ROOT": str(config.ROOT), "config_STATE": str(config.STATE),
            "canli_state": str(canli), "muhur": "TUTTU"}


# ==================================================================================================
# TAKVİM
# ==================================================================================================
def takvim_oku(yol: pathlib.Path) -> dict:
    """`ticker,date[,time]` CSV → {TICKER: sorted[date]}. `earnings._load` ile aynı ayıklama."""
    import csv
    import datetime as dt
    out: dict = {}
    with open(yol, newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 2:
                continue
            t, d = row[0].strip().upper(), row[1].strip()
            if not t or t in ("TICKER", "SYMBOL"):
                continue
            try:
                dt.date.fromisoformat(d)
            except ValueError:
                continue
            out.setdefault(t, []).append(d)
    return {t: sorted(set(ds)) for t, ds in out.items()}


def takvim_yaz(takvim: dict, yol: pathlib.Path) -> int:
    n = 0
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w") as fh:
        fh.write("ticker,date\n")
        for t in sorted(takvim):
            for d in takvim[t]:
                fh.write(f"{t},{d}\n")
                n += 1
    return n


# ==================================================================================================
# PANEL (barlar) — deponun KENDİ kapısıyla
# ==================================================================================================
def panel_yukle(semboller=None):
    """{TICKER: DataFrame(index=date)} — kum-havuzu bar kopyasından, `measurement_bars` kapısıyla.

    `component_ic._load_universe` ile AYNI yol (ağ yok, sanitize onarımı var, bütünlük defteri
    uygulanır). Kopyalanmadı, ÇAĞRILDI: iki yerde iki panel, iki farklı taban demek olurdu."""
    import pandas as pd
    from meridian.adapters import data as da
    per = {}
    for t in (semboller or da.REPLAY_UNIVERSE):
        cp = da._cache_path(t)
        if not cp.exists():
            continue
        try:
            df, _ = da.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
            df = da.measurement_bars(df, t)
            if df is not None and len(df):
                per[t] = df.set_index("date").sort_index()
        except Exception as e:                       # noqa: BLE001 — sayılır, yutulmaz
            per.setdefault("_hata", {})
            print(f"[panel] {t} okunamadı: {type(e).__name__}: {e}", file=sys.stderr)
    per.pop("_hata", None)
    return per


def ileri_getiri_paneli(per: dict, ufuklar=(10, 20)):
    """{ufuk: DataFrame(gün × sembol)} — `close[t+h]/close[t]-1`.

    Tanım `component_ic.forward_returns` ile BİREBİR aynıdır (o modülün `getiri_tanimi` alanı).
    Ufuk dolmayan son h bar NaN kalır — uydurulmaz."""
    import pandas as pd
    kapanis = pd.DataFrame({t: df["close"] for t, df in per.items()}).sort_index()
    return {h: (kapanis.shift(-h) / kapanis - 1.0) for h in ufuklar}, kapanis
