"""EDG-2026-048 — chop tabanı · ölçüm koşumu (2026-08-23).

KART: research/cards/EDG-2026-048-chop-tabani.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Ölçüm ajanı karta DOKUNMAZ; bu betik HÜKÜM VERMEZ, sayı getirir. Karar kuralının
(CI-alt > 0 → GO / değilse NO-GO) okunması Rol-1'in işidir.

NE YAPAR: edg032c tabanının dünyasını (B1-sonrası; edg032b şasisi + ARMED_BEKLENEN=B1
uyarlaması AYNEN) 2 hücrede koşar (K += 1):
  kontrol = bugünkü dünya, chop taban 45 → ŞASİ KAPISI hücresi (K harcamaz)
  taban60 = chop taban 60 — TEK yeni hücre

════════ ŞASİ: YENİDEN KURULMAZ, ÇAĞRILIR (edg032c/edg046/edg040 deseni AYNEN) ════════
edg032b/olcum.py importlib ile modül olarak yüklenir, `SANDBOX`ı BU dizine çevrilir (artefakt
koruması YAPISAL), `ARMED_BEKLENEN`i B1 yasasına çevrilir (edg032c'nin BEYANLI TEK UYARLAMASI
AYNEN; motor ARMED_SETUPS B1'den saparsa koşum BAŞLAMADAN durur) ve `kosum(run, smoke)` yolu
OLDUĞU GİBİ çağrılır. HİÇBİR şasi-parametre enjeksiyonu YOK (2 hücre de merkez: slot 20 ·
size 0,5R · zarf 5R).

════════ ENJEKSİYON NOKTASI (koddan okundu, varsayılmadı; ayrıntı KOMUT.txt) ════════
meridian/regime.py:127 `base = {TREND_UP: 80, CHOP: 45, TREND_DOWN: 15, HIGH_VOL: 25}[regime]`
— exposure_score gövdesi :124-130; TEK tüketicisi build_regime_json (:150); dd-cezası
:151-152; min_exp eşiği + bütçe :153-154; replay'de günde bir çağrı backtest.py:373.
Enjeksiyon SÜREÇ-İÇİ: YALNIZ taban60 hücresinde `regime_mod.exposure_score` yerine
:124-130'un BİREBİR replikası (tek fark: CHOP tabanı 45→60) konur; kontrol hücresinde
exposure_score'a HİÇ dokunulmaz. dd-cezası/min_exp/tetik motorun kendi build_regime_json'unda
kalır — replika onlara DOKUNMAZ (tek-kaldıraç sözleşmesi, kill#3). Motor DOSYASI DEĞİŞMEZ.
Replika koşumdan ÖNCE sentetik doğruluk-tablosuyla sınanır (4 rejim × high_vol {yok,False,
True}: replika(45) ≡ motor; replika(60) yalnız chop'ta sapar).
YAKALAMA (iki hücrede AYNI, salt-geçirgen): `regime_mod.build_regime_json` sarmalanır, günün
{date, regime, distribution_days, high_vol, exposure_score, exposure_budget_pct,
min_exposure_score} kaydı alınır; dönüş değeri DEĞİŞMEZ (nötrlük kanıtı = kontrol hücresinin
kill#1 bayt-özdeşliği — edg046 sabit_mevcut emsali).

════════ ÖZ-SINAMA (kill#2) — seans defterine çivili, satır satır ════════
Her SEANS satırı için uygulanan exposure_budget_pct beklenen formülle (KARAR-BRIEF-CHOP-BUTCE
§0 zinciri: taban[hücre] − high_vol-düzeltmesi 25 − dd≥5 cezası 20, [0,100] kırp,
min_exposure_score eşiği) kıyaslanır — hem yakalanan rejim-günü kaydı hem seans defterinin
kendisi (seanslar_*.json exposure_budget_pct + regime) birebir olmalı. min_exp≠40 görülürse
tek-kaldıraç ihlali (kill#3) → hücre geçersiz. Birebir değilse hücre geçersiz → DUR.

ZORUNLU YER-DEĞİŞTİRME RAPORU (kill#5): taban60'ta chop-DIŞI işlem kümesinin (ticker, ts_open)
kontrole göre farkı — çıkan/giren/ortak TAM listeleri + sayıları + chop-dilim işlem
sayısı/toplam-R/PF her iki hücrede. Rapor üretilmeden hüküm yazılamaz (hüküm zaten Rol-1'in).

Δ+CI (kart, donuk): Δ(taban60−taban45) EŞLENİK ay-kümeli bootstrap · birim=AY · B=5000 ·
seed=20260812 (edg040/045/046 `delta_pnl_ci` AYNEN; aylar kontrol seanslarından).

KİLL'LER (karttan, donuk):
  kill#1 kontrol ≢ edg032c/kosum1 (üç defter sha256 + künye sha çivisi) → DUR (exit 2).
  kill#2 bütçe öz-sınaması satır-başına birebir değilse hücre geçersiz → DUR + rapor.
  kill#3 taban DIŞINDA knob'a dokunulursa geçersiz (replika+doğruluk-tablosu+min_exp assert).
  kill#4 motor sha (broker/backtest/strategy/guard) TABAN_KUNYESI ile tutarsızsa geçersiz
         (hücre başı önce/sonra + künye kosum1_once kıyası).
  kill#5 yer-değiştirme raporu üretilmeden hüküm yazılamaz (bu betik raporu ÜRETİR).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) · git
KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir) · test suite KOŞULMAZ · motor
dosyalarına DOKUNULMAZ (yama süreç-içi; restorasyon ExitStack-finally) · karta/ROADMAP'e
YAZILMAZ · HÜKÜM YOK.

KULLANIM:
  olcum.py --smoke   # [1] DUMAN: dar pencere (2022-01→06) — iki hücre + tüm kapılar
  olcum.py           # [2] TAM: kontrol→kapı → taban60 → Δ+CI + yer-değiştirme + grid raporu
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
sys.path.insert(0, str(REPO))

BOOT_SEED = 20260812
BOOT_ITER = 5000
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")   # edg032c uyarlaması AYNEN
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")
TABAN_SATIR_BEKLENEN = "base = {TREND_UP: 80, CHOP: 45, TREND_DOWN: 15, HIGH_VOL: 25}[regime]"
REPLAY_CAGRI_BEKLENEN = "rj = regime_mod.build_regime_json(idx_slice.reset_index(), params, str(d.date()))"
MIN_EXP_BEKLENEN = 40          # donmuş EDG-022 strategy.yaml:13 — sapma = kill#3 sinyali
DD_CEZA = 20                   # regime.py:152 — motorda kalır, replika DOKUNMAZ (formül kopyası öz-sınamada)
HV_DUZELTME = 25               # regime.py:128-129 — motorda ve replikada AYNI (dokunulmadı)

# hücre → chop tabanı (45 = kontrol/şasi kapısı; 60 tek yeni hücre — kart grid'i DONUK)
HUCRELER = {"kontrol": 45, "taban60": 60}

# ── KÜNYE TAZELEME PROTOKOLÜ (Rol-1 devri, 2026-08-23; EDG-045 kill-tarihçesi emsali) ──
# kill#4 duman teşhisi: guard.py künyeden SONRA v268 mezar-taşıyla değişti (commit 375abd5;
# okuyucusuz SECTOR_CAP_DEFAULT_PCT/HEAT_CAP_DEFAULT_PCT kaldırıldı). Rol-1 hükmü: nötrlük
# İMA yetmez, ÖLÇÜLÜR — TAM pencerede kontrol (taban=45) İKİ KEZ koşulur (edg032c determinizm
# çift-kapısı deseni; her koşum taze süreç + bakir sandbox); iki koşum birbirleriyle VE
# edg032c/kosum1 ile üç defterde bayt-özdeş ise TABAN_KUNYESI.json güncellenir (eski guard
# sha'sı silinmez, kunye_tarihcesi bloğuna taşınır). Özdeş DEĞİLSE künye tazelenmez → DUR.
# Ölçüm dizini dışına TEK yazım bu künye güncellemesidir (Rol-1 yetki devri; kart yine DOKUNULMAZ).
GUARD_V268_SHA = "185b467f33f08150f63261841b834db5886b4361e3f89afe88e9938715ccd1a6"
KONTROL_TASINACAK = ("sonuc_kontrol.json", "seanslar_kontrol.json", "islemler_kontrol.json",
                     "islemler_tam_kontrol.json", "alan_envanteri_kontrol.json",
                     "oz_sinama_kontrol.json", "rejim_gunluk_kontrol.json", "hucre_kontrol.json")
KAPI_DEFTERLER = ("islemler_tam_kontrol.json", "islemler_kontrol.json", "seanslar_kontrol.json")
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim", "tasnif_tum_seans",
                        "birincil", "ci95_ay_kumeli", "islem", "replay", "hucre")


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}


def referans_modul():
    """edg032b şasisini modül olarak yükler; SANDBOX'ı BU dizine çevirir; ARMED_BEKLENEN'i
    B1 yasasına çevirir (edg032c'nin beyanlı TEK uyarlaması AYNEN); motoru B1'e assert'ler."""
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    m = referans_sasi_yukle(REFERANS)
    m.SANDBOX = BURASI                # artefakt koruması: edg032b dizinine ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen),
               "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS)}


# ---------------------------------------------------------------------------------------------
# ENJEKSİYON NOKTASI DOĞRULAMASI + REPLİKA + SENTETİK ÖN-SINAMA
# ---------------------------------------------------------------------------------------------
def enjeksiyon_noktasi_dogrula() -> dict:
    """regime.py:127 taban satırı ve backtest.py:373 çağrı satırı KAYNAKTAN doğrulanır
    (satır kayarsa assert düşer — varsayım yok)."""
    from meridian import regime as R, backtest as BT
    r_kaynak = pathlib.Path(R.__file__).read_text(encoding="utf-8").splitlines()
    r_hit = [i for i, ln in enumerate(r_kaynak, 1) if TABAN_SATIR_BEKLENEN in ln]
    assert len(r_hit) == 1, \
        f"chop-taban satırı tekil bulunamadı ({len(r_hit)} eşleşme) — enjeksiyon noktası kayıp, DUR"
    b_kaynak = pathlib.Path(BT.__file__).read_text(encoding="utf-8").splitlines()
    b_hit = [i for i, ln in enumerate(b_kaynak, 1) if REPLAY_CAGRI_BEKLENEN in ln]
    assert len(b_hit) == 1, \
        f"replay build_regime_json çağrısı tekil bulunamadı ({len(b_hit)}) — desen beklenmedik, DUR"
    return {"regime_taban_satiri": r_hit[0], "backtest_cagri_satiri": b_hit[0],
            "taban_satir_icerigi": TABAN_SATIR_BEKLENEN}


def exposure_score_kur(chop_taban: int):
    """regime.py:124-130'un BİREBİR replikası — TEK fark CHOP tabanı parametrik.
    dd-cezası/min_exp bu fonksiyonda DEĞİL (motorun build_regime_json'unda kalır)."""
    from meridian import regime as R

    def exposure_score_replika(regime: str, metrics: dict) -> int:
        base = {R.TREND_UP: 80, R.CHOP: chop_taban, R.TREND_DOWN: 15, R.HIGH_VOL: 25}[regime]
        if metrics.get("high_vol") and regime != R.HIGH_VOL:
            base -= HV_DUZELTME
        return max(0, min(100, base))

    return exposure_score_replika


def replika_on_sinama() -> dict:
    """Sentetik doğruluk-tablosu (koşumdan önce; motor koşmaz): 4 rejim × metrics
    {boş, high_vol=False, high_vol=True} için replika(45) ≡ motor exposure_score;
    replika(60) YALNIZ chop'ta sapar ve sapma tam +15'tir."""
    from meridian import regime as R
    r45 = exposure_score_kur(45)
    r60 = exposure_score_kur(60)
    rejimler = (R.TREND_UP, R.CHOP, R.TREND_DOWN, R.HIGH_VOL)
    metrikler = ({}, {"high_vol": False}, {"high_vol": True})
    tablo = []
    for rj in rejimler:
        for mt in metrikler:
            asil = R.exposure_score(rj, dict(mt))
            v45 = r45(rj, dict(mt))
            v60 = r60(rj, dict(mt))
            assert v45 == asil, \
                f"replika(45) motordan sapıyor: {rj}/{mt}: {v45} ≠ {asil} — replika sadakatsiz, DUR"
            if rj == R.CHOP:
                assert v60 == asil + 15, \
                    f"replika(60) chop sapması +15 değil: {mt}: {v60} vs {asil} — DUR"
            else:
                assert v60 == asil, \
                    f"replika(60) chop-DIŞI rejimi değiştirdi: {rj}/{mt}: {v60} ≠ {asil} — tek-kaldıraç İHLALİ, DUR"
            tablo.append({"regime": rj, "metrics": dict(mt), "motor": asil,
                          "replika45": v45, "replika60": v60})
    return {"gecti": True, "n_kombinasyon": len(tablo), "tablo": tablo}


# ---------------------------------------------------------------------------------------------
# REJİM KANCASI — yakalama (iki hücrede aynı, salt-geçirgen) + taban60'ta replika enjeksiyonu
# ---------------------------------------------------------------------------------------------
@contextlib.contextmanager
def rejim_kancasi(kayit: dict, chop_taban: int):
    """`regime_mod.build_regime_json` sarmalanır (salt-geçirgen yakalama; dönüş DEĞİŞMEZ).
    chop_taban==60 ise `regime_mod.exposure_score` replika ile değiştirilir (SÜREÇ-İÇİ;
    orijinal build_regime_json global-ad çözümüyle replikayı görür — regime.py:150).
    Kontrol hücresinde (45) exposure_score'a HİÇ dokunulmaz."""
    from meridian import regime as R
    asil_brj = R.build_regime_json
    asil_es = R.exposure_score

    def brj_sarmal(index_bars, params_, date):
        out = asil_brj(index_bars, params_, date)
        kayit["gunler"].append({
            "date": out["date"], "regime": out["regime"],
            "distribution_days": out["distribution_days"],
            "high_vol": bool((out.get("metrics") or {}).get("high_vol")),
            "exposure_score": out["exposure_score"],
            "exposure_budget_pct": out["exposure_budget_pct"],
            "min_exposure_score": out["min_exposure_score"]})
        return out

    R.build_regime_json = brj_sarmal
    enjekte = False
    if chop_taban != 45:
        R.exposure_score = exposure_score_kur(chop_taban)
        enjekte = True
    try:
        yield
    finally:
        R.build_regime_json = asil_brj
        if enjekte:
            R.exposure_score = asil_es


# ---------------------------------------------------------------------------------------------
# ÖZ-SINAMA (kill#2) — brief §0 zinciri, seans defterine çivili, satır satır
# ---------------------------------------------------------------------------------------------
def beklenen_butce(regime: str, dd: int, high_vol: bool, min_exp: int, chop_taban: int) -> tuple:
    """(beklenen_score, beklenen_budget) — regime.py:127-130 + :150-154 aritmetiğinin bağımsız
    kopyası (brief §0 zinciri): taban − high_vol-düzeltmesi, [0,100] kırp, dd≥5 → −20 (0 taban),
    min_exp eşiği."""
    taban_tbl = {"trend_up": 80, "chop": chop_taban, "trend_down": 15, "high_vol": 25}
    pre = taban_tbl[regime]
    if high_vol and regime != "high_vol":
        pre -= HV_DUZELTME
    pre = max(0, min(100, pre))
    score = max(0, pre - DD_CEZA) if dd >= 5 else pre
    budget = score if score >= min_exp else 0
    return score, budget


def oz_sinama(kayit: dict, chop_taban: int, seanslar: list) -> dict:
    """kill#2: (a) yakalanan her rejim-günü formülle birebir; (b) SEANS DEFTERİNİN her satırı
    (exposure_budget_pct + regime) o günün yakalanan kaydıyla ve formülle birebir;
    (c) min_exp≠40 → kill#3 sinyali. Bozuk satırlar TAM sayılır (ilk 50 örneklenir)."""
    gunler = kayit["gunler"]
    # aynı güne çok çağrı olduysa tutarlılık aranır (beklenti: replay'de günde 1 — backtest.py:373)
    gun_map: dict[str, dict] = {}
    cok_cagri_gun_n = 0
    cok_cagri_tutarsiz = []
    for g in gunler:
        d0 = str(g["date"])[:10]
        if d0 in gun_map:
            cok_cagri_gun_n += 1
            if {k: gun_map[d0][k] for k in ("regime", "exposure_score", "exposure_budget_pct",
                                            "distribution_days")} != \
               {k: g[k] for k in ("regime", "exposure_score", "exposure_budget_pct",
                                  "distribution_days")}:
                cok_cagri_tutarsiz.append(d0)
        gun_map[d0] = g

    # (a) formül ↔ yakalanan gün
    gun_bozuk = []
    min_exp_sapan = []
    for d0, g in gun_map.items():
        me = g["min_exposure_score"]
        if me != MIN_EXP_BEKLENEN:
            min_exp_sapan.append({"date": d0, "min_exp": me})
        bek_s, bek_b = beklenen_butce(g["regime"], g["distribution_days"], g["high_vol"],
                                      me, chop_taban)
        if bek_s != g["exposure_score"] or bek_b != g["exposure_budget_pct"]:
            gun_bozuk.append({"date": d0, "regime": g["regime"], "dd": g["distribution_days"],
                              "high_vol": g["high_vol"],
                              "beklenen": [bek_s, bek_b],
                              "uygulanan": [g["exposure_score"], g["exposure_budget_pct"]]})

    # (b) seans defteri ↔ yakalanan gün (defterin kendisine çivili)
    seans_bozuk = []
    seans_gunsuz = []
    for s in seanslar:
        d0 = str(s["date"])[:10]
        g = gun_map.get(d0)
        if g is None:
            seans_gunsuz.append(d0)
            continue
        bek_s, bek_b = beklenen_butce(g["regime"], g["distribution_days"], g["high_vol"],
                                      g["min_exposure_score"], chop_taban)
        if s["exposure_budget_pct"] != bek_b or s["regime"] != g["regime"] \
                or s["exposure_budget_pct"] != g["exposure_budget_pct"]:
            seans_bozuk.append({"date": d0, "seans_budget": s["exposure_budget_pct"],
                                "seans_regime": s["regime"], "beklenen_budget": bek_b,
                                "yakalanan_budget": g["exposure_budget_pct"],
                                "yakalanan_regime": g["regime"]})

    # chop kesiti (gün düzeyi — rapor girdisi, hüküm değil)
    chop_gun = [g for g in gun_map.values() if g["regime"] == "chop"]
    chop_acik = [g for g in chop_gun if g["exposure_budget_pct"] > 0]
    butce_dagilim: dict[str, dict] = {}
    for g in gun_map.values():
        r = g["regime"]
        b = str(g["exposure_budget_pct"])
        butce_dagilim.setdefault(r, {})
        butce_dagilim[r][b] = butce_dagilim[r].get(b, 0) + 1

    gecti = (len(gun_map) > 0 and len(seanslar) > 0 and not gun_bozuk and not seans_bozuk
             and not seans_gunsuz and not min_exp_sapan and not cok_cagri_tutarsiz)
    return {
        "chop_taban": chop_taban,
        "n_yakalanan_cagri": len(gunler), "n_yakalanan_gun": len(gun_map),
        "n_seans": len(seanslar),
        "cok_cagri_gun_n": cok_cagri_gun_n,
        "cok_cagri_tutarsiz": cok_cagri_tutarsiz[:20],
        "gun_formul_bozuk_n": len(gun_bozuk), "gun_formul_bozuk": gun_bozuk[:50],
        "seans_defter_bozuk_n": len(seans_bozuk), "seans_defter_bozuk": seans_bozuk[:50],
        "seans_gunsuz_n": len(seans_gunsuz), "seans_gunsuz": seans_gunsuz[:20],
        "min_exp_beklenen": MIN_EXP_BEKLENEN,
        "min_exp_sapan_n": len(min_exp_sapan), "min_exp_sapan": min_exp_sapan[:20],
        "butce_dagilimi_rejim_bazinda": butce_dagilim,
        "chop_gun_n": len(chop_gun), "chop_acik_gun_n": len(chop_acik),
        "chop_kapali_gun_n": len(chop_gun) - len(chop_acik),
        "chop_dd5_gun_n": sum(1 for g in chop_gun if g["distribution_days"] >= 5),
        "kill2_gecti": gecti,
        "beyan": ("Beklenen formül brief §0 zincirinin bağımsız kopyası: taban[hücre] − "
                  "high_vol-düzeltmesi 25, [0,100] kırp, dd≥5 → −20 (0 taban), min_exp eşiği. "
                  "Kıyas HEM yakalanan rejim-gününe HEM seans defterinin kendisine çivili; "
                  "TÜM satırlara uygulanır (kart: satır satır)."),
    }


# ---------------------------------------------------------------------------------------------
# ŞASİ KAPISI (kill#1) + MOTOR KÜNYE KIYASI (kill#4)
# ---------------------------------------------------------------------------------------------
def sasi_kapisi(smoke: bool) -> dict:
    ek = "_smoke" if smoke else ""
    yerel_dir = (BURASI / "smoke") if smoke else BURASI
    ref_dir = EDG032C / ("kosum1_smoke" if smoke else "kosum1")
    ciftler = {
        "islemler_tam": (yerel_dir / f"islemler_tam_kontrol{ek}.json",
                         ref_dir / f"islemler_tam_kontrol{ek}.json"),
        "islemler_slim": (yerel_dir / f"islemler_kontrol{ek}.json",
                          ref_dir / f"islemler_kontrol{ek}.json"),
        "seanslar": (yerel_dir / f"seanslar_kontrol{ek}.json",
                     ref_dir / f"seanslar_kontrol{ek}.json"),
    }
    sonuc = {}
    for ad, (y, r) in ciftler.items():
        sy, sr = _sha_full(y), _sha_full(r)
        sonuc[ad] = {"yerel_sha256": sy, "edg032c_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    # tam koşumda künye çivisi: kıyaslanan referans dosyalar TABAN_KUNYESI kaydının kendisi mi
    kunye_tutarli = None
    if not smoke:
        kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
        ks = kunye["determinizm_kaniti"]["kapi_sha256"]
        kunye_tutarli = (sonuc["islemler_tam"]["edg032c_sha256"] == ks["islemler_tam_kontrol.json"]
                         and sonuc["islemler_slim"]["edg032c_sha256"] == ks["islemler_kontrol.json"]
                         and sonuc["seanslar"]["edg032c_sha256"] == ks["seanslar_kontrol.json"])
    gecti = all(v["bayt_ozdes"] for v in sonuc.values()) and (kunye_tutarli is not False)
    out = {"bayt_kiyas_edg032c": sonuc, "kunye_sha_tutarli": kunye_tutarli,
           "kill1_gecti": gecti}
    (yerel_dir / f"sasi_kapisi{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI{ek}: bayt={all(v['bayt_ozdes'] for v in sonuc.values())} "
          f"künye_tutarlı={kunye_tutarli} → {'GEÇTİ' if gecti else 'DÜŞTÜ — ölçüm DURUR'}")
    return out


def motor_kunye_kiyas(m: dict) -> dict:
    """kill#4: bugünkü motor sha (4 dosya) TABAN_KUNYESI kosum1_once kaydıyla birebir mi."""
    kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    kiyas = {f: {"simdi": m[f], "kunye": ref[f]["sha256"],
                 "esit": m[f] == ref[f]["sha256"]} for f in MOTOR_SHA_DOSYALAR}
    return {"dosyalar": kiyas, "kill4_tutarli": all(v["esit"] for v in kiyas.values())}


# ---------------------------------------------------------------------------------------------
# Δ+CI (edg040/045/046 reçetesi AYNEN) + YER-DEĞİŞTİRME (kill#5) + chop kesiti
# ---------------------------------------------------------------------------------------------
def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg040/edg035 AYNEN): birim = AY, iki kol AYNI ayı görür,
    B=5000, seed=20260812, yüzdelik CI."""
    import numpy as np
    M = len(aylar)

    def seri(defter):
        pnl = {a: 0.0 for a in aylar}
        disi = 0
        for t in defter:
            a = str(t["ts_open"])[:7]
            if a not in pnl:
                disi += 1                  # takvim dışı ay — sayılır, sessiz düşmez (YASA-4)
                continue
            pnl[a] += float(t.get("pnl_dollars") or 0.0)
        return np.array([pnl[a] for a in aylar], dtype=float), disi

    A_t, disi_t = seri(taban_defter)
    A_h, disi_h = seri(hucre_defter)
    rng = np.random.default_rng(BOOT_SEED)
    idx = np.arange(M)
    f = np.empty(BOOT_ITER)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki kola
        f[i] = float(A_h[pick].sum()) - float(A_t[pick].sum())
    lo = round(float(np.percentile(f, 2.5)), 2)
    hi = round(float(np.percentile(f, 97.5)), 2)
    nokta = round(float(A_h.sum() - A_t.sum()), 2)
    return {"delta_pnl": nokta, "ci95": [lo, hi], "n_ay": M,
            "takvim_disi_islem": {"taban": disi_t, "hucre": disi_h},
            "sifir_disinda": ("evet (CI-alt > 0)" if lo > 0 else
                              "evet (CI-üst < 0)" if hi < 0 else "hayır (0 içinde)"),
            "yontem": ("EŞLENİK ay-kümeli bootstrap · birim = AY (iki kol AYNI ayı görür) · "
                       "B=5000 · seed=20260812 · yüzdelik")}


def _pf(defter: list) -> tuple[float | None, str | None]:
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    if neg < 0:
        return round(poz / abs(neg), 4), None
    return None, "kayıp bacağı boş (Σpnl<0 yok) — PF paydası sıfır, TANIMSIZ"


def chop_dilim_kesiti(defter: list) -> dict:
    """Defterden chop-dilim işlemleri (t['regime']=='chop'): n · toplam-R · PF (+bağlam)."""
    dilim = [t for t in defter if t.get("regime") == "chop"]
    pf, pf_neden = _pf(dilim) if dilim else (None, "chop-dilim işlemi yok")
    n_kazanan = sum(1 for t in dilim if float(t["pnl_dollars"]) > 0)
    return {"n": len(dilim),
            "toplam_r": round(sum(float(t.get("r_multiple") or 0.0) for t in dilim), 4),
            "pf": pf, "pf_olculemedi_nedeni": pf_neden,
            "net_pnl": round(sum(float(t["pnl_dollars"]) for t in dilim), 2),
            "win_rate": (round(n_kazanan / len(dilim), 4) if dilim else None),
            "exit_reason": {r: sum(1 for t in dilim if t.get("exit_reason") == r)
                            for r in sorted({t.get("exit_reason") for t in dilim})},
            "setup": {s: sum(1 for t in dilim if t.get("setup") == s)
                      for s in sorted({t.get("setup") for t in dilim})}}


def yer_degistirme(kontrol_defter: list, t60_defter: list) -> dict:
    """kill#5 ZORUNLU RAPOR: taban60'ta chop-DIŞI işlem kümesinin kontrole göre farkı —
    çıkan/giren/ortak TAM listeleri + sayıları (anahtar: ticker, ts_open). Bu fark KILL
    DEĞİLDİR (kart: mekanizmanın kendisi) ama raporlanmadan hüküm yazılamaz. HÜKÜM YOK."""
    def anahtar(defter, chop_disi: bool):
        return {(t["ticker"], str(t["ts_open"])) for t in defter
                if (t.get("regime") != "chop") == chop_disi}

    def liste(kume):
        return [list(k) for k in sorted(kume)]

    def ozet(defter, kume):
        satirlar = [t for t in defter if (t["ticker"], str(t["ts_open"])) in kume]
        setup_n: dict[str, int] = {}
        for t in satirlar:
            setup_n[t.get("setup") or "?"] = setup_n.get(t.get("setup") or "?", 0) + 1
        return {"setup": dict(sorted(setup_n.items())),
                "net_pnl": round(sum(float(t["pnl_dollars"]) for t in satirlar), 2),
                "toplam_r": round(sum(float(t.get("r_multiple") or 0.0) for t in satirlar), 4)}

    k_nc, t_nc = anahtar(kontrol_defter, True), anahtar(t60_defter, True)
    k_c, t_c = anahtar(kontrol_defter, False), anahtar(t60_defter, False)
    cikan, giren, ortak = k_nc - t_nc, t_nc - k_nc, k_nc & t_nc
    return {
        "tanim": ("chop-DIŞI işlem kümesi (regime != 'chop'; anahtar ticker+ts_open) "
                  "taban60 ↔ kontrol. Bu fark KILL DEĞİLDİR (chop işlemleri slot/ısı tüketir; "
                  "chop-dışı kümenin değişmesi mekanizmanın kendisidir) ama RAPORLANMADAN "
                  "hüküm yazılamaz — kart features_asof/kill#5."),
        "chop_disi": {
            "kontrol_n": len(k_nc), "taban60_n": len(t_nc),
            "ortak_n": len(ortak), "cikan_n": len(cikan), "giren_n": len(giren),
            "cikan_listesi": liste(cikan), "giren_listesi": liste(giren),
            "cikan_ozet": ozet(kontrol_defter, cikan),
            "giren_ozet": ozet(t60_defter, giren),
        },
        "chop_dilimi": {
            "kontrol_n": len(k_c), "taban60_n": len(t_c),
            "ortak_n": len(k_c & t_c), "yalniz_kontrol_n": len(k_c - t_c),
            "yalniz_taban60_n": len(t_c - k_c),
            "yalniz_taban60_listesi": liste(t_c - k_c),
            "yalniz_kontrol_listesi": liste(k_c - t_c),
        },
    }


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU
# ---------------------------------------------------------------------------------------------
def hucre_kos(ref, run: str, smoke: bool) -> dict:
    chop_taban = HUCRELER[run]
    ref.HUCRELER.setdefault(run, {})             # merkez hücre (şasi parametre enjeksiyonu YOK)
    kayit = {"gunler": []}
    m_once = motor_sha()
    kunye_once = motor_kunye_kiyas(m_once)

    with rejim_kancasi(kayit, chop_taban):
        ref.kosum(run, smoke=smoke)              # ŞASİ: referansın kendi yolu, dokunulmadan

    m_sonra = motor_sha()
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())
    seanslar = json.loads((outdir / f"seanslar_{run}{ek}.json").read_text())

    oz = oz_sinama(kayit, chop_taban, seanslar)
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    (outdir / f"rejim_gunluk_{run}{ek}.json").write_text(
        json.dumps(kayit["gunler"], ensure_ascii=False), encoding="utf-8")

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    pf, pf_neden = _pf(defter)
    chop_kesit = chop_dilim_kesiti(defter)

    ozet = {
        "kosum": run, "smoke": smoke,
        "kol_kimligi": {                          # kol kimliği damgası (exe006 Kritik-1 emsali)
            "chop_taban": chop_taban,
            "enjeksiyon": ("YOK — motor exposure_score olduğu gibi (kontrol/şasi kapısı)"
                           if chop_taban == 45 else
                           "regime_mod.exposure_score → replika(60); SÜREÇ-İÇİ, dosya yamasız"),
            "min_exp_sapan_n": oz["min_exp_sapan_n"],     # 0 olmalı (kill#3 kanıtı)
        },
        "hucre_sasi": d.get("hucre"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),   # KANONİK (islem.net_pnl YOK — bilinen tuzak)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "avg_r": perf.get("avg_r"),
        "win_rate": perf.get("win_rate"), "total_return": perf.get("total_return"),
        "setup_bazinda": islem.get("setup_bazinda"),
        "exit_reason_dagilim": islem.get("exit_reason_dagilim"),
        "toplam_plan": islem.get("toplam_plan"), "silahlanan_plan": islem.get("silahlanan_plan"),
        "entry_rejects": islem.get("entry_rejects"),
        "chop_dilim": chop_kesit,
        "rejim_gun_sayaclari": {k: oz[k] for k in
                                ("chop_gun_n", "chop_acik_gun_n", "chop_kapali_gun_n",
                                 "chop_dd5_gun_n", "n_yakalanan_gun", "n_seans")},
        "butce_dagilimi_rejim_bazinda": oz["butce_dagilimi_rejim_bazinda"],
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "sasi_kill3_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": oz["kill2_gecti"],
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_sha_ayni": m_once == m_sonra,
        "motor_kunye_kill4_once": kunye_once,
        "motor_kunye_kill4_sonra": motor_kunye_kiyas(m_sonra),
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] taban={chop_taban} n={ozet['islem_n']} net={ozet['net_pnl_trades']} "
          f"pf={pf} dd={ozet['maxdd_kanonik']} sharpe={ozet['sharpe']} "
          f"chop_dilim_n={chop_kesit['n']} chop_R={chop_kesit['toplam_r']} "
          f"chop_gun_acik/kapali={oz['chop_acik_gun_n']}/{oz['chop_kapali_gun_n']} "
          f"kill2={oz['kill2_gecti']} kill4={ozet['motor_kunye_kill4_sonra']['kill4_tutarli']} "
          f"bütünlük={ozet['butunluk_gecerli']} motor_sha_ayni={ozet['motor_sha_ayni']}")
    return ozet


# ---------------------------------------------------------------------------------------------
def main() -> int:
    smoke = "--smoke" in sys.argv
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI

    # ön-uçuş: eski koşum artığı varsa DUR (şasi hazirla() var-olan state'i yeniden kullanır)
    artiklar = []
    for run in HUCRELER:
        if (BURASI / f"state_{run}{ek}").exists():
            artiklar.append(f"state_{run}{ek}")
        if (outdir / f"sonuc_{run}{ek}.json").exists():
            artiklar.append(f"sonuc_{run}{ek}.json")
    if artiklar:
        sys.exit(f"önceki koşum artığı duruyor: {artiklar} — elle kaldır, yeniden başlat (DUR)")

    motor_once = motor_sha()
    kunye_kiyas = motor_kunye_kiyas(motor_once)
    kill4_baslangic = kunye_kiyas["kill4_tutarli"]
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} · "
          f"taban satırı=regime.py:{noktalar['regime_taban_satiri']} · "
          f"replay çağrısı=backtest.py:{noktalar['backtest_cagri_satiri']} · "
          f"replika ön-sınaması geçti={on['gecti']} (n={on['n_kombinasyon']}) · "
          f"kill4(başlangıç)={kunye_kiyas['kill4_tutarli']}")

    rapor: dict = {
        "kart": "EDG-2026-048", "smoke": smoke,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
        "motor_kunye_kill4_baslangic": kunye_kiyas,
        "kill4_teshis": (None if kill4_baslangic else {
            "tutarsiz_dosyalar": [f for f, v in kunye_kiyas["dosyalar"].items()
                                  if not v["esit"]],
            "guard_mtime": dt.datetime.fromtimestamp(
                (REPO / "meridian" / "guard.py").stat().st_mtime,
                dt.timezone.utc).isoformat(timespec="seconds"),
            "olcum_ajani_teshisi": (
                "guard.py künye-sonrası TEK hunk değişti (git 987b552→HEAD): v268 mezar taşı "
                "(commit 375abd5, 'WP6 küçük kalemler … #11 mezar taşı') — OKUYUCUSUZ "
                "SECTOR_CAP_DEFAULT_PCT/HEAT_CAP_DEFAULT_PCT sabitlerinin kaldırılması + "
                "yorum bloğu. broker/backtest/strategy/regime/config/dataset/score: fark YOK. "
                "Sabitlerin kod okuyucusu grep'le DOĞRULANDI: yalnız mezar-taşı testi "
                "(tests/test_wp6_kucuk_kalemler_v268.py, YOKLUĞU assert'ler). Statik teşhis "
                "davranış-nötr İMLER; bayt-özdeşlik kanıtı duman kill#1 kapısındadır. "
                "Künyeyi yenilemek/kabul Rol-1 kararıdır — bu betik HÜKÜM VERMEZ."),
        }),
        "uyarlama_beyani": {**uyarlama,
                            "beyan": ("edg032c TEK uyarlaması AYNEN: yüklenen şasi modülünün "
                                      "ARMED_BEKLENEN sabiti B1 yasasına çevrildi (dünya-"
                                      "beklentisi; motor DEĞİL). Şasi parametre enjeksiyonu YOK.")},
        "enjeksiyon_noktalari": {
            "chop_taban": (f"meridian/regime.py:{noktalar['regime_taban_satiri']} "
                           f"`{TABAN_SATIR_BEKLENEN}` — taban60 hücresinde regime_mod."
                           "exposure_score süreç-içi replika(60) ile; kontrol hücresinde "
                           "DOKUNULMADI"),
            "replay_cagri": (f"meridian/backtest.py:{noktalar['backtest_cagri_satiri']} "
                             "`build_regime_json` (günde bir); yakalama sarmalayıcısı "
                             "salt-geçirgen, iki hücrede AYNI"),
            "dd_ceza_min_exp": ("regime.py:151-154 — motorda KALDI, replika dokunmadı "
                                "(tek-kaldıraç sözleşmesi; doğruluk-tablosu + min_exp=40 kanıtı)"),
        },
        "replika_on_sinamasi": {"gecti": on["gecti"], "n_kombinasyon": on["n_kombinasyon"],
                                "tablo": on["tablo"]},
    }

    def yaz_ve_cik(kod: int) -> int:
        rapor["motor_sha256_sonra"] = motor_sha()
        rapor["motor_sha_ayni_toplam"] = (motor_once == rapor["motor_sha256_sonra"])
        (BURASI / f"sonuc_grid{ek}.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"yazıldı: {BURASI / f'sonuc_grid{ek}.json'}")
        return kod

    # ── KILL#4 ÖN-UÇUŞ KAPISI: motor sha künyeyle tutarsızsa ÖLÇÜM YAPILMAZ ──
    # (kart kill#4 mekaniktir; koşum öncesi belirlenebilir olduğundan hücre koşmadan durulur.
    #  Duman modunda hücreler YALNIZ TEŞHİS için koşar — Rol-1'e "donmuş taban bugünkü motorla
    #  hâlâ bayt-özdeş yeniden üretilebiliyor mu?" (kill#1 duman kapısı) kanıtı üretmek için —
    #  ve koşum sonunda yine DURDU + exit 2 ile damgalanır; edg045 DURDU emsali.)
    if not kill4_baslangic:
        if not smoke:
            rapor["DURDU"] = ("kill#4 (ÖN-UÇUŞ): motor sha TABAN_KUNYESI.kosum1_once ile "
                              "tutarsız — TAM koşum YAPILMADI (hücre koşulmadı, K harcanmadı)")
            print("KILL#4 ÖN-UÇUŞTA DÜŞTÜ — TAM koşum yapılmadı; teşhis Rol-1'e")
            return yaz_ve_cik(2)
        print("KILL#4 ÖN-UÇUŞTA DÜŞTÜ — duman yalnız TEŞHİS olarak koşuyor "
              "(ölçüm GEÇERSİZ; sonunda DURDU + exit 2)")

    hucreler: dict = {}

    # [A] kontrol → ŞASİ KAPISI (kill#1)
    hucreler["kontrol"] = hucre_kos(ref, "kontrol", smoke)
    rapor["hucreler"] = hucreler
    sk = sasi_kapisi(smoke)
    rapor["sasi_kapisi"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: kontrol edg032c/kosum1 ile bayt-özdeş DEĞİL — taban60 koşulmadı"
        print("KILL#1 DÜŞTÜ — ölçüm DURDU; şasi teşhisi Rol-1'e")
        return yaz_ve_cik(2)
    if not hucreler["kontrol"]["oz_sinama_kill2_gecti"]:
        rapor["DURDU"] = "kill#2: kontrol öz-sınaması düştü — kablo tutmuyor"
        print("KILL#2 DÜŞTÜ (kontrol) — ölçüm DURDU")
        return yaz_ve_cik(2)
    if not hucreler["kontrol"]["motor_sha_ayni"] or (
            kill4_baslangic
            and not hucreler["kontrol"]["motor_kunye_kill4_sonra"]["kill4_tutarli"]):
        rapor["DURDU"] = "kill#4: motor sha kontrol koşumunda değişti/künyeyle tutarsız — geçersiz"
        print("KILL#4 DÜŞTÜ (kontrol) — ölçüm DURDU")
        return yaz_ve_cik(2)

    # [B] taban60
    hucreler["taban60"] = hucre_kos(ref, "taban60", smoke)
    if not hucreler["taban60"]["oz_sinama_kill2_gecti"]:
        rapor["DURDU"] = "kill#2: taban60 öz-sınaması düştü — hücre geçersiz"
        print("KILL#2 DÜŞTÜ (taban60) — ölçüm DURDU")
        return yaz_ve_cik(2)
    if not hucreler["taban60"]["motor_sha_ayni"] or (
            kill4_baslangic
            and not hucreler["taban60"]["motor_kunye_kill4_sonra"]["kill4_tutarli"]):
        rapor["DURDU"] = "kill#4: motor sha taban60 koşumunda değişti/künyeyle tutarsız — geçersiz"
        print("KILL#4 DÜŞTÜ (taban60) — ölçüm DURDU")
        return yaz_ve_cik(2)

    # [C] YER-DEĞİŞTİRME (kill#5 zorunlu raporu — dumanda da üretilir: kablo kanıtı)
    defter_k = json.loads((outdir / f"islemler_tam_kontrol{ek}.json").read_text())
    defter_60 = json.loads((outdir / f"islemler_tam_taban60{ek}.json").read_text())
    yd = yer_degistirme(defter_k, defter_60)
    (outdir / f"yer_degistirme{ek}.json").write_text(
        json.dumps(yd, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor["yer_degistirme"] = {
        "dosya": str(outdir / f"yer_degistirme{ek}.json"),
        "chop_disi_ozet": {k: yd["chop_disi"][k] for k in
                           ("kontrol_n", "taban60_n", "ortak_n", "cikan_n", "giren_n",
                            "cikan_ozet", "giren_ozet")},
        "chop_dilimi_ozet": {k: yd["chop_dilimi"][k] for k in
                             ("kontrol_n", "taban60_n", "ortak_n",
                              "yalniz_kontrol_n", "yalniz_taban60_n")},
    }
    print(f"  YER-DEĞİŞTİRME{ek}: chop-dışı kontrol={yd['chop_disi']['kontrol_n']} "
          f"taban60={yd['chop_disi']['taban60_n']} ortak={yd['chop_disi']['ortak_n']} "
          f"çıkan={yd['chop_disi']['cikan_n']} giren={yd['chop_disi']['giren_n']} · "
          f"chop-dilim {yd['chop_dilimi']['kontrol_n']}→{yd['chop_dilimi']['taban60_n']}")

    # [D] Δ+CI (kart kuralı: Δ(taban60−taban45); yalnız TAM koşumda)
    if not smoke:
        seanslar = json.loads((outdir / "seanslar_kontrol.json").read_text())
        aylar = sorted({str(r["date"])[:7] for r in seanslar})
        rapor["delta_ci"] = {"taban60_vs_kontrol": delta_pnl_ci(defter_k, defter_60, aylar)}
        dd_ = rapor["delta_ci"]["taban60_vs_kontrol"]
        print(f"  Δ[taban60−taban45]: {dd_['delta_pnl']} CI95={dd_['ci95']} ({dd_['sifir_disinda']})")
    else:
        rapor["delta_ci"] = {"degerlendirilmedi": "duman — kablo sınaması; Δ/CI yalnız TAM koşumda"}

    rapor["hukum_yok"] = ("Bu rapor HÜKÜM İÇERMEZ. Karar kuralının (CI-alt) okunması ve "
                          "kill#5 raporu eşliğinde hüküm Rol-1'in işidir.")
    if not kill4_baslangic:
        rapor["DURDU"] = ("kill#4: motor sha (guard.py) TABAN_KUNYESI ile tutarsız — bu duman "
                          "YALNIZ TEŞHİS koşumudur (kill#1 duman kapısı sonucu dahil); ölçüm "
                          "GEÇERSİZ, TAM koşum YAPILMADI")
        print("DUMAN TEŞHİS TAMAM — KILL#4 nedeniyle DURDU (exit 2); TAM koşum yapılmadı")
        return yaz_ve_cik(2)
    return yaz_ve_cik(0)


# ---------------------------------------------------------------------------------------------
# KÜNYE TAZELEME FAZLARI (Rol-1 devri, 2026-08-23) — her faz AYRI süreç (sıra zorunlu):
#   kontrol1 → kontrol2 → determinizm_kunye → taban60
# ---------------------------------------------------------------------------------------------
def tazeleme_on_kontrol() -> dict:
    """Motor pin denetimi: broker/backtest/strategy künyeyle BİREBİR olmalı; guard ya künye
    sha'sı ya da v268 pin'i olmalı. Başka her sürüklenme → bilinmeyen dünya, DUR."""
    m = motor_sha()
    kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    for f in ("broker.py", "backtest.py", "strategy.py"):
        assert m[f] == ref[f]["sha256"], \
            f"{f} künyeden sapmış ({m[f][:16]} ≠ {ref[f]['sha256'][:16]}) — v268-DIŞI sürüklenme, DUR"
    if m["guard.py"] != ref["guard.py"]["sha256"]:
        assert m["guard.py"] == GUARD_V268_SHA, \
            (f"guard.py ne künye ne v268 pin ({m['guard.py'][:16]}) — bilinmeyen sürüklenme, DUR")
    return m


def kontrol_kosumu(n: int) -> int:
    """Künye-tazeleme kontrol koşumu #n (TAM pencere, taban=45): bakir sandbox → hücre koşumu
    (kill#2 öz-sınama dahil) → çıktılar kontrol_kosum{n}/ altına taşınır."""
    hedef = BURASI / f"kontrol_kosum{n}"
    if hedef.exists():
        sys.exit(f"{hedef} zaten var — üzerine koşulmaz (elle kaldır, yeniden başlat)")
    for fs in KONTROL_TASINACAK:
        if (BURASI / fs).exists():
            sys.exit(f"kök dizinde eski çıktı duruyor: {fs} — arşivlenmemiş koşum var, DUR")
    st = BURASI / "state_kontrol"
    if st.exists():
        shutil.rmtree(st)                 # BAKİR sandbox (edg032c determinizm standardı)

    t0 = dt.datetime.now(dt.timezone.utc)
    m_pin = tazeleme_on_kontrol()
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"[kontrol_kosum{n}] pin OK (guard={'v268' if m_pin['guard.py'] == GUARD_V268_SHA else 'künye'}) · "
          f"taban satırı=regime.py:{noktalar['regime_taban_satiri']} · replika ön-sınama={on['gecti']}")

    ozet = hucre_kos(ref, "kontrol", smoke=False)
    t1 = dt.datetime.now(dt.timezone.utc)
    if not ozet["oz_sinama_kill2_gecti"]:
        sys.exit(f"KILL#2 DÜŞTÜ (kontrol_kosum{n}) — koşum künye tazelemeye kullanılamaz, DUR")
    if not ozet["motor_sha_ayni"]:
        sys.exit(f"motor sha kontrol_kosum{n} İÇİNDE değişti — koşum geçersiz, DUR")

    hedef.mkdir()
    tasinan = {}
    for fs in KONTROL_TASINACAK:
        kk = BURASI / fs
        if not kk.exists():
            tasinan[fs] = None            # ölçülemedi: şasi bu dosyayı üretmedi (raporda görünür)
            continue
        shutil.move(str(kk), str(hedef / fs))
        tasinan[fs] = _sha_full(hedef / fs)
    (hedef / "run_kunye.json").write_text(json.dumps({
        "ad": f"kontrol_kosum{n}", "amac": "künye tazeleme çift-koşumu (Rol-1 devri 2026-08-23)",
        "baslangic_utc": t0.isoformat(timespec="seconds"),
        "bitis_utc": t1.isoformat(timespec="seconds"),
        "sure_sn": round((t1 - t0).total_seconds(), 1),
        "motor_sha_pin": m_pin, "guard_v268_pin": GUARD_V268_SHA,
        "uyarlama_beyani": uyarlama, "enjeksiyon_noktalari": noktalar,
        "replika_on_sinamasi_gecti": on["gecti"],
        "sandbox": "state_kontrol koşum öncesi silindi (bakir); şasi hazirla() EDG-022 donmuş kopyalarından kurdu",
        "tasinan_dosyalar_sha256": tasinan,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[kontrol_kosum{n}] bitti · süre={round((t1 - t0).total_seconds(), 1)}s → {hedef}")
    return 0


def determinizm_kunye() -> int:
    """Çift kapı + künye tazeleme: kosum1 ↔ kosum2 ↔ edg032c/kosum1 üç defterde bayt-özdeş
    ise TABAN_KUNYESI.json'daki guard kaydı v268'e güncellenir (eski sha kunye_tarihcesi'ne).
    Özdeş DEĞİLSE künye TAZELENMEZ → exit 2."""
    k1, k2 = BURASI / "kontrol_kosum1", BURASI / "kontrol_kosum2"
    refdir = EDG032C / "kosum1"
    for d in (k1, k2):
        if not d.exists():
            sys.exit(f"determinizm_kunye: koşum dizini yok: {d} — sıra bozuk, DUR")

    kunye_yolu = EDG032C / "TABAN_KUNYESI.json"
    kunye_once_bayt = kunye_yolu.read_bytes()
    kunye = json.loads(kunye_once_bayt)

    kapi = {}
    for f in KAPI_DEFTERLER:
        s1, s2, sr = _sha_full(k1 / f), _sha_full(k2 / f), _sha_full(refdir / f)
        kapi[f] = {"kosum1_sha256": s1, "kosum2_sha256": s2, "edg032c_sha256": sr,
                   "uc_yonlu_ozdes": (s1 is not None and s1 == s2 == sr)}
    kapi_gecti = all(v["uc_yonlu_ozdes"] for v in kapi.values())

    # künye çivisi: kıyaslanan referans dosyalar künyenin kapi_sha256 kaydının kendisi mi
    ks = kunye["determinizm_kaniti"]["kapi_sha256"]
    kunye_civisi = all(kapi[f]["edg032c_sha256"] == ks[f] for f in KAPI_DEFTERLER)

    # ek kanıt 1: alan envanteri üç yönlü bayt
    ae = {d.name: _sha_full(d / "alan_envanteri_kontrol.json") for d in (k1, k2)}
    ae["edg032c"] = _sha_full(refdir / "alan_envanteri_kontrol.json")
    ae_ozdes = (ae["kontrol_kosum1"] is not None
                and ae["kontrol_kosum1"] == ae["kontrol_kosum2"] == ae["edg032c"])
    # ek kanıt 2: sonuc ölçüm blokları k1↔k2 derin-eşit (sonuc'un kendisi bayt-özdeş OLAMAZ:
    # olcum_zamani/sure_sn koşum kimliğidir); k1↔edg032c BİLGİ AMAÇLI (replay.n_endeks_satir
    # koşum-günü önbellek uzunluğudur — edg040 dersi; bayt kapısı zaten defterlerde)
    s1 = json.loads((k1 / "sonuc_kontrol.json").read_text())
    s2 = json.loads((k2 / "sonuc_kontrol.json").read_text())
    sr_ = json.loads((refdir / "sonuc_kontrol.json").read_text())
    blok_k1k2 = {b: (s1.get(b) == s2.get(b)) for b in SONUC_OLCUM_BLOKLARI}
    blok_k1ref = {b: (s1.get(b) == sr_.get(b)) for b in SONUC_OLCUM_BLOKLARI}
    bloklar_esit = all(blok_k1k2.values())

    # koşumlar arası motor sabitliği (koşum-içi zaten hucre_kos'ta)
    h1 = json.loads((k1 / "hucre_kontrol.json").read_text())
    h2 = json.loads((k2 / "hucre_kontrol.json").read_text())
    motor_arasi_ayni = (h1["motor_sha_sonra"] == h2["motor_sha_once"]
                        == h1["motor_sha_once"] == h2["motor_sha_sonra"])
    guard_simdi = motor_sha()["guard.py"]
    guard_v268 = (guard_simdi == GUARD_V268_SHA
                  and h1["motor_sha_once"]["guard.py"] == GUARD_V268_SHA)

    gecti = bool(kapi_gecti and kunye_civisi and ae_ozdes and bloklar_esit
                 and motor_arasi_ayni and guard_v268
                 and h1["oz_sinama_kill2_gecti"] and h2["oz_sinama_kill2_gecti"])

    out = {
        "adim": "EDG-048 KÜNYE TAZELEME ÇİFT KAPISI (Rol-1 devri 2026-08-23)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("TAM kontrol (taban=45) iki kez, taze süreç + bakir sandbox, v268 guard ile; "
                  "üç defter kosum1 ↔ kosum2 ↔ edg032c/kosum1 BAYT-ÖZDEŞ olmalı. Ek kanıt: "
                  "alan_envanteri üç yönlü bayt + sonuc ölçüm blokları k1↔k2 derin-eşit + "
                  "motor sha dört noktada sabit + iki koşumda kill#2 öz-sınama."),
        "kapi_defterleri": kapi, "kapi_uc_yonlu_ozdes": kapi_gecti,
        "kunye_civisi_tutarli": kunye_civisi,
        "ek_kanit_alan_envanteri": {**ae, "uc_yonlu_ozdes": ae_ozdes},
        "ek_kanit_sonuc_bloklari_k1k2": blok_k1k2,
        "bilgi_sonuc_bloklari_k1_edg032c": blok_k1ref,
        "motor_dort_noktada_sabit": motor_arasi_ayni,
        "guard_v268_dogrulandi": guard_v268,
        "kill2_iki_kosum": [h1["oz_sinama_kill2_gecti"], h2["oz_sinama_kill2_gecti"]],
        "TAZELEME_GECTI": gecti,
        "hukum": None,   # hüküm Rol-1'in; bu bayrak mekanik sha kıyasıdır
    }

    if gecti:
        # ── KÜNYE GÜNCELLEMESİ (ölçüm dizini dışına TEK yazım; Rol-1 yetki devri) ──
        (BURASI / "kunye_yedek_pre048.json").write_bytes(kunye_once_bayt)   # eski hâl korunur
        mt = (REPO / "meridian" / "guard.py").stat().st_mtime_ns
        eski = dict(kunye["motor_sha256"]["kosum1_once"]["guard.py"])
        yeni_kayit = {"sha256": GUARD_V268_SHA, "sha256_16": GUARD_V268_SHA[:16], "mtime_ns": mt}
        kunye["motor_sha256"]["kosum1_once"]["guard.py"] = dict(yeni_kayit)
        kunye["motor_sha256"]["kosum2_sonra"]["guard.py"] = dict(yeni_kayit)
        kunye.setdefault("kunye_tarihcesi", []).append({
            "tarih_utc": out["olcum_zamani"], "dosya": "guard.py",
            "eski_sha256": eski["sha256"], "eski_mtime_ns": eski["mtime_ns"],
            "yeni_sha256": GUARD_V268_SHA,
            "neden": ("v268 mezar-taşı (commit 375abd5): OKUYUCUSUZ SECTOR_CAP_DEFAULT_PCT/"
                      "HEAT_CAP_DEFAULT_PCT sabitleri kaldırıldı (+yorum bloğu); davranış "
                      "bayt-nötr KANITLI — TAM-pencere çift-koşum (edg048 kontrol_kosum1/2) "
                      "birbirleriyle VE edg032c/kosum1 ile üç defterde bayt-özdeş. "
                      "kosum1_once + kosum2_sonra guard kayıtları birlikte güncellendi "
                      "(dort_noktada_sabit iç tutarlılığı için)."),
            "kanit": str(BURASI / "determinizm_kunye.json"),
            "yedek": str(BURASI / "kunye_yedek_pre048.json"),
            "yetki": "Rol-1 devri (EDG-048 ölçüm turu koordinatör mesajı, 2026-08-23)",
        })
        kunye_yolu.write_text(json.dumps(kunye, ensure_ascii=False, indent=1), encoding="utf-8")
        out["kunye_guncellendi"] = {
            "dosya": str(kunye_yolu),
            "once_sha256": hashlib.sha256(kunye_once_bayt).hexdigest(),
            "sonra_sha256": _sha_full(kunye_yolu),
            "guard_eski": eski["sha256"], "guard_yeni": GUARD_V268_SHA,
        }
    else:
        out["kunye_guncellendi"] = None
        out["DURDU"] = ("çift kapı DÜŞTÜ — dünya değişmiş demektir; künye TAZELENMEZ, "
                        "taban60 koşulmaz; teşhis Rol-1'e")

    (BURASI / "determinizm_kunye.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"TAZELEME ÇİFT KAPISI: defter={kapi_gecti} çivi={kunye_civisi} ae={ae_ozdes} "
          f"blok={bloklar_esit} motor={motor_arasi_ayni} guard_v268={guard_v268} → "
          f"{'GEÇTİ — künye güncellendi' if gecti else 'DÜŞTÜ — künye TAZELENMEDİ'}")
    print(f"yazıldı: {BURASI / 'determinizm_kunye.json'}")
    return 0 if gecti else 2


def taban60_tam() -> int:
    """Kartın kalan akışı: taban60 TAM hücresi + kill kapıları + Δ/CI + yer-değiştirme +
    sonuc_grid.json. Ön-şart: determinizm_kunye GEÇTİ ve künye bugünkü motorla 4/4 tutarlı."""
    det_yolu = BURASI / "determinizm_kunye.json"
    if not det_yolu.exists():
        sys.exit("taban60: determinizm_kunye.json yok — sıra bozuk (önce çift kapı), DUR")
    det = json.loads(det_yolu.read_text())
    if not det["TAZELEME_GECTI"]:
        sys.exit("taban60: künye tazeleme kapısı GEÇMEDİ — hücre koşulmaz, DUR")
    for fs in ("sonuc_taban60.json", "islemler_tam_taban60.json"):
        if (BURASI / fs).exists():
            sys.exit(f"kök dizinde eski çıktı duruyor: {fs} — arşivlenmemiş koşum var, DUR")
    st = BURASI / "state_taban60"
    if st.exists():
        shutil.rmtree(st)                 # bakir sandbox

    motor_once = motor_sha()
    kunye_kiyas = motor_kunye_kiyas(motor_once)
    if not kunye_kiyas["kill4_tutarli"]:
        sys.exit("taban60: kill#4 — motor sha GÜNCEL künyeyle bile tutarsız, DUR")
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"[taban60] kill4(güncel künye)=True · taban satırı=regime.py:"
          f"{noktalar['regime_taban_satiri']} · replika ön-sınama={on['gecti']}")

    rapor: dict = {
        "kart": "EDG-2026-048", "smoke": False, "faz": "taban60 (künye-tazeleme sonrası TAM)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
        "motor_kunye_kill4_baslangic": kunye_kiyas,
        "kunye_tazeleme_kaniti": {
            "dosya": str(det_yolu),
            "kapi_uc_yonlu_ozdes": det["kapi_uc_yonlu_ozdes"],
            "kunye_guncellendi": det.get("kunye_guncellendi"),
        },
        "uyarlama_beyani": {**uyarlama,
                            "beyan": ("edg032c TEK uyarlaması AYNEN: ARMED_BEKLENEN → B1. "
                                      "Şasi parametre enjeksiyonu YOK.")},
        "enjeksiyon_noktalari": {
            "chop_taban": (f"meridian/regime.py:{noktalar['regime_taban_satiri']} "
                           f"`{TABAN_SATIR_BEKLENEN}` — taban60'ta regime_mod.exposure_score "
                           "süreç-içi replika(60); kontrolde DOKUNULMADI"),
            "replay_cagri": (f"meridian/backtest.py:{noktalar['backtest_cagri_satiri']} "
                             "`build_regime_json` (günde bir); yakalama salt-geçirgen"),
            "dd_ceza_min_exp": "regime.py:151-154 — motorda KALDI (tek-kaldıraç sözleşmesi)",
        },
        "replika_on_sinamasi": {"gecti": on["gecti"], "n_kombinasyon": on["n_kombinasyon"]},
    }

    def yaz_ve_cik(kod: int) -> int:
        rapor["motor_sha256_sonra"] = motor_sha()
        rapor["motor_sha_ayni_toplam"] = (motor_once == rapor["motor_sha256_sonra"])
        (BURASI / "sonuc_grid.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"yazıldı: {BURASI / 'sonuc_grid.json'}")
        return kod

    k1 = BURASI / "kontrol_kosum1"
    hucreler = {"kontrol": json.loads((k1 / "hucre_kontrol.json").read_text())}
    hucreler["taban60"] = hucre_kos(ref, "taban60", smoke=False)
    rapor["hucreler"] = hucreler
    rapor["kontrol_kaynagi"] = (f"{k1} (künye-tazeleme kosum1 — edg032c/kosum1 ile bayt-özdeş "
                                "kanıtlı; kill#1 bu özdeşliğin kendisi)")
    if not hucreler["taban60"]["oz_sinama_kill2_gecti"]:
        rapor["DURDU"] = "kill#2: taban60 öz-sınaması düştü — hücre geçersiz"
        print("KILL#2 DÜŞTÜ (taban60) — ölçüm DURDU")
        return yaz_ve_cik(2)
    if not (hucreler["taban60"]["motor_sha_ayni"]
            and hucreler["taban60"]["motor_kunye_kill4_sonra"]["kill4_tutarli"]):
        rapor["DURDU"] = "kill#4: motor sha taban60 koşumunda değişti/künyeyle tutarsız — geçersiz"
        print("KILL#4 DÜŞTÜ (taban60) — ölçüm DURDU")
        return yaz_ve_cik(2)

    defter_k = json.loads((k1 / "islemler_tam_kontrol.json").read_text())
    defter_60 = json.loads((BURASI / "islemler_tam_taban60.json").read_text())
    yd = yer_degistirme(defter_k, defter_60)
    (BURASI / "yer_degistirme.json").write_text(
        json.dumps(yd, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor["yer_degistirme"] = {
        "dosya": str(BURASI / "yer_degistirme.json"),
        "chop_disi_ozet": {k: yd["chop_disi"][k] for k in
                           ("kontrol_n", "taban60_n", "ortak_n", "cikan_n", "giren_n",
                            "cikan_ozet", "giren_ozet")},
        "chop_dilimi_ozet": {k: yd["chop_dilimi"][k] for k in
                             ("kontrol_n", "taban60_n", "ortak_n",
                              "yalniz_kontrol_n", "yalniz_taban60_n")},
    }
    print(f"  YER-DEĞİŞTİRME: chop-dışı kontrol={yd['chop_disi']['kontrol_n']} "
          f"taban60={yd['chop_disi']['taban60_n']} ortak={yd['chop_disi']['ortak_n']} "
          f"çıkan={yd['chop_disi']['cikan_n']} giren={yd['chop_disi']['giren_n']} · "
          f"chop-dilim {yd['chop_dilimi']['kontrol_n']}→{yd['chop_dilimi']['taban60_n']}")

    seanslar = json.loads((k1 / "seanslar_kontrol.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})
    rapor["delta_ci"] = {"taban60_vs_kontrol": delta_pnl_ci(defter_k, defter_60, aylar)}
    dd_ = rapor["delta_ci"]["taban60_vs_kontrol"]
    print(f"  Δ[taban60−taban45]: {dd_['delta_pnl']} CI95={dd_['ci95']} ({dd_['sifir_disinda']})")

    rapor["hukum_yok"] = ("Bu rapor HÜKÜM İÇERMEZ. Karar kuralının (CI-alt) okunması ve "
                          "kill#5 raporu eşliğinde hüküm Rol-1'in işidir.")
    return yaz_ve_cik(0)


if __name__ == "__main__":
    _faz = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    if _faz == "kontrol1":
        raise SystemExit(kontrol_kosumu(1))
    if _faz == "kontrol2":
        raise SystemExit(kontrol_kosumu(2))
    if _faz == "determinizm_kunye":
        raise SystemExit(determinizm_kunye())
    if _faz == "taban60":
        raise SystemExit(taban60_tam())
    if "--smoke" in sys.argv:
        raise SystemExit(main())
    sys.exit("kullanım: olcum.py --smoke | kontrol1 | kontrol2 | determinizm_kunye | taban60 "
             "(tam akış Rol-1 künye-tazeleme protokolü: sıra zorunlu, her faz ayrı süreç)")
