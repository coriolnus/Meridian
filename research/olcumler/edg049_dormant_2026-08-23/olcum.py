"""EDG-2026-049 — uyuyan-kurulum karşı-olgusu · ölçüm koşumu (2026-08-23).

KART: research/cards/EDG-2026-049-uyuyan-kurulum-karsi-olgu.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Ölçüm ajanı karta DOKUNMAZ; bu betik HÜKÜM VERMEZ, sayı getirir. Karar kuralının (ARSENAL
çıtası: Δ CI-alt > 0 ∧ dilim n ≥ 30) okunması Rol-1'in işidir.

NE YAPAR (tam gerekçe + ön-beyanlar KOMUT.txt'te):
  [0] KÜNYE-TAZELEME PROTOKOLÜ (EDG-048 emsali AYNEN): K2/K5 dalgası broker/strategy/guard
      sha'larını değiştirdi (backtest AYNI). TAM pencerede kontrol İKİ KEZ koşulur; üç defter
      kosum1 ↔ kosum2 ↔ edg032c/kosum1 bayt-özdeşse TABAN_KUNYESI.json v273'e tarihçe-koruyarak
      tazelenir; DEĞİLSE künye tazelenmez → DUR (dünya değişmiş — K2 sızıntısı burada yakalanır).
  [1] dormant_acik hücresi: strategy.scan_entry'nin (:1095-1107) süreç-içi BİREBİR replikası —
      tek fark süzgeç `ARMED_SETUPS + extra + DORMANT_EKSTRA`. Plan DOĞUMU (scan_all) yamasız;
      silahlılar mutlak öncelikli (v92). Kontrol hücresine kanca dahi konmaz.
  [2] Öz-sınamalar: replika seçim-tablosu ön-sınaması · kill#3 iki-katmanlı ortak-işlem kıyası
      (GİRİŞ-YASASI katmanı kapı; SERMAYE-EŞLENİK katmanı TAM raporlu — KOMUT.txt beyanı) ·
      kontrol dormant-yokluk kanıtı · doğum-sayım mutabakatı.
  [3] Dormant-dilim kesiti + yer-değiştirme (kill#5, edg048 deseni) + Δ(dormant_acik−kontrol)
      eşlenik ay-kümeli bootstrap (B=5000, seed=20260812, birim=AY).
  [4] n=0 kuralı: dormant PLAN doğumu 0 ise "replay'de ölçülemez + neden" damgası.

DİSİPLİN: UYDURMA YASAĞI · YASA-4 · git KOŞULMAZ · canlı state/ YAZILMAZ · test suite KOŞULMAZ ·
motor dosyalarına DOKUNULMAZ (yama süreç-içi; restorasyon finally) · karta YAZILMAZ · HÜKÜM YOK.

KULLANIM (sıra zorunlu; her faz AYRI süreç):
  olcum.py smoke | kontrol1 | kontrol2 | kunye_tazele | dormant_acik
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import inspect
import json
import pathlib
import re
import shutil
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
sys.path.insert(0, str(REPO))

BOOT_SEED = 20260812
BOOT_ITER = 5000
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")

# ── DORMANT KÜMESİ (koşum günü kaynaktan yeniden türetilip assert'lenir — KOMUT.txt) ──
# scan_all evren pini: strategy.py `setup="…"` üreticileri (7 ad) − B1 silahlı üçlüsü;
# sıra = scan_all değerlendirme sırası (strategy.py:1086-1088).
SCAN_ALL_EVREN = ("breakout_vcp", "momentum_burst", "pullback", "episodic_pivot",
                  "exhaustion_hammer", "pead", "canslim")
DORMANT_EKSTRA = ("pullback", "episodic_pivot", "pead", "canslim")

# scan_entry kaynak pini (inspect.getsource sha256) — kaynak kayarsa replika sadakati
# KANITLANAMAZ → DUR (koddan okundu, varsayılmadı).
SCAN_ENTRY_KAYNAK_SHA = "e945d7d66f43f8de4e198ef6b5d97291c0235894def2ecba0c2e033fd52fa7e7"
SCAN_ENTRY_DEF_SATIR = 1095            # bilgi amaçlı (assert kaynak sha üstünden)
SUZGEC_SATIR_BEKLENEN = "for setup in ARMED_SETUPS + extra:"
REPLAY_CAGRI_BEKLENEN = "sig = strat.scan_entry(sub.tail(340), eff, rs_map.get(t, 50), ticker=t)"

# ── KÜNYE-TAZELEME PİNLERİ (K5 8324177 v273; koşum günü ölçüldü — KOMUT.txt teşhis bloğu) ──
V273_PIN = {
    "broker.py": "09f5d0850122376a560c852307d6e3b49724718e601b74788ae9de8e4b85548b",
    "strategy.py": "449039624127c66d550b8e9f6b43ae8302d6858e706604ba6be7cc048f599877",
    "guard.py": "bb984356798278a513846f27959e26caedc5538f3d76646c72c4819d9e967392",
}
TAZELEME_NEDEN = {
    "broker.py": ("K5 (8324177, v273): +7 satır = 2 YORUM bloğu (EZER damgaları — "
                  "entry_limit_price ATR bacağı :182-184 + ADV katılım :619-622); kod yolu "
                  "DEĞİŞMEDİ. Davranış bayt-nötr KANITLI — TAM-pencere çift-koşum (edg049 "
                  "kontrol_kosum1/2) birbirleriyle VE edg032c/kosum1 ile üç defterde bayt-özdeş."),
    "strategy.py": ("K5 (8324177, v273): +4 satır = ARMED_SETUPS üstü EZER YORUM bloğu "
                    "(registry bayrakları); tuple DEĞERİ değişmedi (B1 aynen — koşum başı "
                    "assert). Davranış bayt-nötr KANITLI — aynı üç-defter özdeşliği."),
    "guard.py": ("K5 (8324177, v273): GOAL_KEYS/LIMIT_KEYS 25a mezar taşları + "
                 "REPLAY_WARMUP_KEYS (25c sınıf damgası) + validate_change reddi — HEPSİ "
                 "Hermes/yönetişim yolu, replay ÇAĞIRMAZ; classify_gate içi fark YORUM. "
                 "Davranış bayt-nötr KANITLI — aynı üç-defter özdeşliği. NOT: K2 (d8030c0, "
                 "v272 giriş penceresi) künye 4'lüsüne HİÇ dokunmadı (barclock/intraday_cycle); "
                 "replay'e sızmadığı da bu özdeşlikle SINANDI."),
}

KONTROL_TASINACAK = ("sonuc_kontrol.json", "seanslar_kontrol.json", "islemler_kontrol.json",
                     "islemler_tam_kontrol.json", "alan_envanteri_kontrol.json",
                     "hucre_kontrol.json")
KAPI_DEFTERLER = ("islemler_tam_kontrol.json", "islemler_kontrol.json", "seanslar_kontrol.json")
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim", "tasnif_tum_seans",
                        "birincil", "ci95_ay_kumeli", "islem", "replay", "hucre")

# ── kill#3 alan katmanları (ölçümden ÖNCE beyan — KOMUT.txt; broker.py:504-515 gerekçesi) ──
GIRIS_YASASI_ALANLARI = ("ticker", "ts_open", "side", "setup", "score", "r_multiple_expected",
                         "regime", "strategy_version", "plan_id", "skill_chain", "exploration")
SERMAYE_ESLENIK_ALANLARI = ("id", "ts_close", "entry", "exit", "qty", "r_multiple", "pnl_pct",
                            "pnl_dollars", "costs", "exit_reason", "bars_held", "scaled_out",
                            "mfe_r", "mae_r")

HUCRELER = ("kontrol", "dormant_acik")


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}


def referans_modul():
    """edg032b şasisini modül olarak yükler; SANDBOX'ı BU dizine çevirir; ARMED_BEKLENEN'i
    B1 yasasına çevirir (edg032c/edg048 beyanlı TEK uyarlaması AYNEN); motoru B1'e assert'ler."""
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    m = referans_sasi_yukle(REFERANS)
    m.SANDBOX = BURASI                # artefakt koruması: edg032b dizinine ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    for h in HUCRELER:
        m.HUCRELER.setdefault(h, {})  # merkez hücreler (şasi parametre enjeksiyonu YOK)
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen),
               "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS)}


# ---------------------------------------------------------------------------------------------
# ENJEKSİYON NOKTASI DOĞRULAMASI + DORMANT EVREN PİNİ + REPLİKA + SENTETİK ÖN-SINAMA
# ---------------------------------------------------------------------------------------------
def enjeksiyon_noktasi_dogrula() -> dict:
    """scan_entry kaynağı (sha pini + süzgeç satırı) ve backtest çağrı satırı KAYNAKTAN
    doğrulanır; DORMANT_EKSTRA scan_all evreninden yeniden türetilir (varsayım yok)."""
    from meridian import strategy as S, backtest as BT
    src = inspect.getsource(S.scan_entry)
    sha = hashlib.sha256(src.encode()).hexdigest()
    assert sha == SCAN_ENTRY_KAYNAK_SHA, \
        f"scan_entry kaynağı pinden sapmış ({sha[:16]}) — replika sadakati kanıtlanamaz, DUR"
    assert SUZGEC_SATIR_BEKLENEN in src, "süzgeç satırı scan_entry gövdesinde yok — desen kayıp, DUR"
    def_satir = inspect.getsourcelines(S.scan_entry)[1]
    b_kaynak = pathlib.Path(BT.__file__).read_text(encoding="utf-8").splitlines()
    b_hit = [i for i, ln in enumerate(b_kaynak, 1) if REPLAY_CAGRI_BEKLENEN in ln]
    assert len(b_hit) == 1, \
        f"replay scan_entry çağrısı tekil bulunamadı ({len(b_hit)}) — desen beklenmedik, DUR"
    # dormant evren pini: setup="..." üreticileri kaynaktan
    s_kaynak = pathlib.Path(S.__file__).read_text(encoding="utf-8")
    uretilen = set(re.findall(r'setup="(\w+)"', s_kaynak))
    assert uretilen == set(SCAN_ALL_EVREN), \
        f"scan_all evreni pinden sapmış: {sorted(uretilen)} ≠ {sorted(SCAN_ALL_EVREN)} — DUR"
    turetilen_dormant = tuple(s for s in SCAN_ALL_EVREN if s not in B1_YASA)
    assert turetilen_dormant == DORMANT_EKSTRA, \
        f"DORMANT_EKSTRA türetimi pinle uyuşmuyor: {turetilen_dormant} ≠ {DORMANT_EKSTRA} — DUR"
    return {"scan_entry_def_satiri": def_satir, "scan_entry_kaynak_sha256": sha,
            "backtest_cagri_satiri": b_hit[0], "dormant_ekstra": list(DORMANT_EKSTRA)}


def _secim(by_setup: dict, params: dict, ac: bool):
    """scan_entry SEÇİM YASASININ tek kaynağı — :1102-1107'nin birebir kopyası; `ac` yalnız
    süzgeç kuyruğuna DORMANT_EKSTRA ekler (arka bağ). Doğum mantığına (scan_all) dokunmaz."""
    extra = tuple(params.get("entry.armed_extra") or ())
    sira = B1_YASA + extra + (DORMANT_EKSTRA if ac else ())
    for setup in sira:
        if setup in by_setup:
            return by_setup[setup]
    return None


def replika_on_sinama() -> dict:
    """Sentetik seçim-tablosu (koşumdan önce; motor koşmaz): kapalı-kip ≡ motor yasası;
    açık-kip yalnız 'hiçbir silahlı ateşlemedi' durumunda dormant döndürür; sıra çivileri."""
    class _S:                                   # sahte sinyal — yalnız kimlik taşır
        def __init__(self, setup):
            self.setup = setup

    def _d(*setuplar):
        return {s: _S(s) for s in setuplar}

    p0: dict = {}                               # frozen strategy.yaml: entry.armed_extra YOK
    tablo = []
    durumlar = [
        # (by_setup kurulumları, kapalı-beklenen, açık-beklenen)
        (("breakout_vcp", "pullback"), "breakout_vcp", "breakout_vcp"),   # silahlı MUTLAK öncelik
        (("momentum_burst", "episodic_pivot"), "momentum_burst", "momentum_burst"),
        (("exhaustion_hammer",), "exhaustion_hammer", "exhaustion_hammer"),
        (("pullback",), None, "pullback"),                                # arka bağ YALNIZ açıkta
        (("episodic_pivot",), None, "episodic_pivot"),
        (("pead",), None, "pead"),
        (("canslim",), None, "canslim"),
        (("pullback", "episodic_pivot"), None, "pullback"),               # dormant içi scan_all sırası
        (("episodic_pivot", "canslim"), None, "episodic_pivot"),
        (("pead", "canslim"), None, "pead"),
        ((), None, None),
    ]
    for setuplar, bek_kapali, bek_acik in durumlar:
        bs = _d(*setuplar)
        g_k = _secim(bs, p0, ac=False)
        g_a = _secim(bs, p0, ac=True)
        v_k = g_k.setup if g_k else None
        v_a = g_a.setup if g_a else None
        assert v_k == bek_kapali, f"kapalı-kip yasası sapıyor: {setuplar}: {v_k} ≠ {bek_kapali} — DUR"
        assert v_a == bek_acik, f"açık-kip yasası sapıyor: {setuplar}: {v_a} ≠ {bek_acik} — DUR"
        if v_k is not None:
            assert v_a == v_k, f"silahlı önceliği bozuldu: {setuplar} — tek-kaldıraç İHLALİ, DUR"
        tablo.append({"setuplar": list(setuplar), "kapali": v_k, "acik": v_a})
    # kapalı-kip ↔ motor scan_entry çapraz kanıtı: motorun kendi süzgeci de aynı seçimi yapmalı.
    # scan_all'ı sahte sözlükle beslemek için scan_entry'yi DEĞİL yasasını kıyaslıyoruz —
    # yasanın kaynağı zaten sha-pinli (enjeksiyon_noktasi_dogrula); burada B1 sırası çivilenir.
    from meridian import strategy as S
    assert tuple(S.ARMED_SETUPS) == B1_YASA
    return {"gecti": True, "n_durum": len(durumlar), "tablo": tablo}


@contextlib.contextmanager
def dormant_kapisi(kayit: dict, ac: bool):
    """dormant_acik hücresinde `strategy.scan_entry` yerine BİREBİR replika konur (süreç-içi;
    motor dosyası değişmez). Kontrol hücresinde (ac=False) HİÇBİR kanca konmaz — kill#1
    özdeşliği bunun kanıtı. Replika: orijinal scan_all (doğum YAMASIZ) + _secim yasası."""
    from meridian import strategy as S
    if not ac:
        yield
        return
    asil_scan_entry = S.scan_entry
    asil_scan_all = S.scan_all

    def scan_entry_replika(bars, params, rs_rating_value, ticker="?"):
        by_setup = asil_scan_all(bars, params, rs_rating_value, ticker)   # doğum: motorun kendisi
        sig = _secim(by_setup, params, ac=True)
        if sig is not None and sig.setup in DORMANT_EKSTRA:
            assert sig.setup not in S.ARMED_SETUPS       # arka bağ tanımı — silahlıyla çakışamaz
            kayit["dogum"].append({"ticker": ticker, "setup": sig.setup})
            # aynı ticker-günde silahlı da ateşlemiş miydi? (beyanlı sınır-1'in ölçümü)
            if any(s in by_setup for s in S.ARMED_SETUPS):
                kayit["silahli_golge_n"] += 1            # olamaz (silahlı öncelikli) — 0 kalmalı
        return sig

    S.scan_entry = scan_entry_replika
    try:
        yield
    finally:
        S.scan_entry = asil_scan_entry
        assert S.scan_all is asil_scan_all, "scan_all koşumda yamalanmış — doğum mantığı İHLALİ"


# ---------------------------------------------------------------------------------------------
# ŞASİ/KÜNYE KAPILARI
# ---------------------------------------------------------------------------------------------
def motor_kunye_kiyas(m: dict) -> dict:
    """kill#4 bacağı: bugünkü motor sha (4 dosya) TABAN_KUNYESI kosum1_once kaydıyla birebir mi
    (künye tazelendiyse GÜNCEL kayıtla)."""
    kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    kiyas = {f: {"simdi": m[f], "kunye": ref[f]["sha256"],
                 "esit": m[f] == ref[f]["sha256"]} for f in MOTOR_SHA_DOSYALAR}
    return {"dosyalar": kiyas, "kill4_tutarli": all(v["esit"] for v in kiyas.values())}


def tazeleme_on_kontrol() -> dict:
    """Motor pin denetimi (her faz): backtest.py künyeyle BİREBİR; broker/strategy/guard ya
    künye sha'sı ya v273 pin'i. Başka her sürüklenme → bilinmeyen dünya, DUR."""
    m = motor_sha()
    kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    assert m["backtest.py"] == ref["backtest.py"]["sha256"], \
        f"backtest.py künyeden sapmış ({m['backtest.py'][:16]}) — bilinmeyen sürüklenme, DUR"
    for f in ("broker.py", "strategy.py", "guard.py"):
        if m[f] != ref[f]["sha256"]:
            assert m[f] == V273_PIN[f], \
                f"{f} ne künye ne v273 pin ({m[f][:16]}) — bilinmeyen sürüklenme, DUR"
    return m


def sasi_kapisi_smoke() -> dict:
    """kill#1 duman kapısı: kontrol duman defterleri edg032c/kosum1_smoke ile bayt-özdeş mi
    (erken nötrlük sinyali; otoriter kapı TAM çift-koşum)."""
    yerel = BURASI / "smoke"
    ref_dir = EDG032C / "kosum1_smoke"
    sonuc = {}
    for f in KAPI_DEFTERLER:
        fs = f.replace(".json", "_smoke.json")
        sy, sr = _sha_full(yerel / fs), _sha_full(ref_dir / fs)
        sonuc[fs] = {"yerel_sha256": sy, "edg032c_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    gecti = all(v["bayt_ozdes"] for v in sonuc.values())
    out = {"bayt_kiyas_edg032c_smoke": sonuc, "kill1_smoke_gecti": gecti}
    (yerel / "sasi_kapisi_smoke.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI (duman): bayt={gecti} → "
          f"{'GEÇTİ (erken nötrlük sinyali)' if gecti else 'DÜŞTÜ — dünya değişmiş, DUR'}")
    return out


# ---------------------------------------------------------------------------------------------
# Δ+CI (edg040/045/046/048 reçetesi AYNEN) + DİLİM + YER-DEĞİŞTİRME + kill#3
# ---------------------------------------------------------------------------------------------
def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg048 AYNEN): birim = AY, iki kol AYNI ayı görür,
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
            "takvim_disi_islem": {"kontrol": disi_t, "dormant_acik": disi_h},
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


def dormant_dilim_kesiti(defter: list) -> dict:
    """Defterden dormant-dilim işlemleri (setup ∈ DORMANT_EKSTRA): kart features_asof kesiti."""
    dilim = [t for t in defter if t.get("setup") in DORMANT_EKSTRA]
    pf, pf_neden = _pf(dilim) if dilim else (None, "dormant-dilim işlemi yok")
    n_kazanan = sum(1 for t in dilim if float(t["pnl_dollars"]) > 0)
    return {"n": len(dilim),
            "toplam_r": round(sum(float(t.get("r_multiple") or 0.0) for t in dilim), 4),
            "pf": pf, "pf_olculemedi_nedeni": pf_neden,
            "net_pnl": round(sum(float(t["pnl_dollars"]) for t in dilim), 2),
            "win_rate": (round(n_kazanan / len(dilim), 4) if dilim else None),
            "exit_reason": {r: sum(1 for t in dilim if t.get("exit_reason") == r)
                            for r in sorted({t.get("exit_reason") for t in dilim})},
            "setup": {s: sum(1 for t in dilim if t.get("setup") == s)
                      for s in sorted({t.get("setup") for t in dilim})},
            "aylik_ts_open": {a: sum(1 for t in dilim if str(t["ts_open"])[:7] == a)
                              for a in sorted({str(t["ts_open"])[:7] for t in dilim})},
            "regime_dagilim": {r: sum(1 for t in dilim if t.get("regime") == r)
                               for r in sorted({t.get("regime") for t in dilim})}}


def kill3_oz_sinama(kontrol_defter: list, dormant_defter: list) -> dict:
    """kill#3 (iki katman, KOMUT.txt ön-beyanı): ortak (ticker, ts_open) işlemler —
    GİRİŞ-YASASI alanları birebir olmalı (kapı); SERMAYE-EŞLENİK alanları TAM sayımla
    raporlanır (kill değil — equity-yolu mekaniği); strict tüm-alan sonucu ayrıca yazılır."""
    def haritala(defter, ad):
        m = {}
        for t in defter:
            k = (t["ticker"], str(t["ts_open"]))
            assert k not in m, f"{ad}: (ticker, ts_open) anahtarı tekil değil: {k} — kıyas geçersiz, DUR"
            m[k] = t
        return m

    mk = haritala(kontrol_defter, "kontrol")
    md = haritala(dormant_defter, "dormant_acik")
    ortak = sorted(set(mk) & set(md))
    tum_alanlar = sorted({k for t in (kontrol_defter + dormant_defter) for k in t})
    bilinmeyen = [a for a in tum_alanlar
                  if a not in GIRIS_YASASI_ALANLARI and a not in SERMAYE_ESLENIK_ALANLARI]
    assert not bilinmeyen, \
        f"katmanlanmamış alan(lar) var: {bilinmeyen} — beyan eksik, kıyas geçersiz, DUR"

    fark_n = {a: 0 for a in tum_alanlar}
    ornekler: dict[str, list] = {}
    giris_ihlal = []
    strict_farkli = 0
    for k in ortak:
        a_k, a_d = mk[k], md[k]
        satir_farkli = False
        for alan in tum_alanlar:
            if a_k.get(alan) != a_d.get(alan):
                fark_n[alan] += 1
                satir_farkli = True
                if len(ornekler.setdefault(alan, [])) < 5:
                    ornekler[alan].append({"anahtar": list(k), "kontrol": a_k.get(alan),
                                           "dormant_acik": a_d.get(alan)})
                if alan in GIRIS_YASASI_ALANLARI:
                    giris_ihlal.append({"anahtar": list(k), "alan": alan,
                                        "kontrol": a_k.get(alan), "dormant_acik": a_d.get(alan)})
        if satir_farkli:
            strict_farkli += 1

    gecti = not giris_ihlal
    return {
        "beyan": ("KOMUT.txt ön-beyanı: kapı GİRİŞ-YASASI katmanında (plan/sinyal-belirlenimli "
                  "11 alan); SERMAYE-EŞLENİK katman farkları kill DEĞİL (broker.py:504-515 "
                  "qty=f(equity); fill katılım-etkisi=f(qty) — dormant işlemler equity yolunu "
                  "değiştirir, ortak işlemlerin boyut/pnl'i mekanik sürüklenir; yer-değiştirme "
                  "mekanizmasının muhasebe izi). Strict tüm-alan sonucu saklanmadan raporda."),
        "ortak_n": len(ortak),
        "yalniz_kontrol_n": len(set(mk) - set(md)), "yalniz_dormant_n": len(set(md) - set(mk)),
        "giris_yasasi_alanlari": list(GIRIS_YASASI_ALANLARI),
        "sermaye_eslenik_alanlari": list(SERMAYE_ESLENIK_ALANLARI),
        "alan_fark_sayimi": {a: n for a, n in sorted(fark_n.items()) if n},
        "alan_fark_ornekleri": ornekler,
        "strict_tum_alan_ozdes": strict_farkli == 0,
        "strict_farkli_satir_n": strict_farkli,
        "giris_yasasi_ihlal_n": len(giris_ihlal),
        "giris_yasasi_ihlal": giris_ihlal[:50],
        "kill3_gecti": gecti,
    }


def yer_degistirme(kontrol_defter: list, dormant_defter: list) -> dict:
    """kill#5 ZORUNLU RAPOR (edg048 deseni): dormant-DIŞI işlem kümesinin (setup ∈ B1;
    anahtar ticker+ts_open) dormant_acik ↔ kontrol farkı — çıkan/giren/ortak TAM listeleri +
    sayıları + özetleri; dormant-dilim sayıları iki hücrede. Fark KILL DEĞİLDİR (dormant
    işlemler slot/ısı/sermaye tüketir; dormant-dışı kümenin değişmesi mekanizmanın kendisi)
    ama raporlanmadan hüküm yazılamaz. HÜKÜM YOK."""
    def anahtar(defter, dormant_disi: bool):
        return {(t["ticker"], str(t["ts_open"])) for t in defter
                if (t.get("setup") not in DORMANT_EKSTRA) == dormant_disi}

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

    k_nd, d_nd = anahtar(kontrol_defter, True), anahtar(dormant_defter, True)
    k_d, d_d = anahtar(kontrol_defter, False), anahtar(dormant_defter, False)
    cikan, giren, ortak = k_nd - d_nd, d_nd - k_nd, k_nd & d_nd
    return {
        "tanim": ("dormant-DIŞI işlem kümesi (setup ∈ B1 silahlı üçlüsü; anahtar ticker+ts_open) "
                  "dormant_acik ↔ kontrol. Kart: kill değil ZORUNLU rapor (kill#5)."),
        "dormant_disi": {
            "kontrol_n": len(k_nd), "dormant_acik_n": len(d_nd),
            "ortak_n": len(ortak), "cikan_n": len(cikan), "giren_n": len(giren),
            "cikan_listesi": liste(cikan), "giren_listesi": liste(giren),
            "cikan_ozet": ozet(kontrol_defter, cikan),
            "giren_ozet": ozet(dormant_defter, giren),
        },
        "dormant_dilimi": {
            "kontrol_n": len(k_d),          # yapısal 0 beklenir (süzgeç kapalı) — assert ayrıca
            "dormant_acik_n": len(d_d),
            "dormant_acik_listesi": liste(d_d),
        },
    }


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU
# ---------------------------------------------------------------------------------------------
def hucre_kos(ref, run: str, smoke: bool) -> dict:
    ac = (run == "dormant_acik")
    kayit = {"dogum": [], "silahli_golge_n": 0}
    m_once = motor_sha()
    kunye_once = motor_kunye_kiyas(m_once)

    # PIT temizliği: sandbox'ta earnings.csv OLMAMALI (pead PIT'siz snapshot'tan beslenemesin
    # — KOMUT.txt; PIT'siz fundamentals proxy YASAK). hazirla() koşumda kuracağı için burada
    # mevcutsa DUR; yoksa koşum sonrası da yokluğu doğrulanır.
    st_ad = f"state_{run}" + ("_smoke" if smoke else "")
    e_csv = BURASI / st_ad / "earnings.csv"
    assert not e_csv.exists(), f"sandbox'ta earnings.csv var ({e_csv}) — pead PIT ihlali riski, DUR"

    with dormant_kapisi(kayit, ac):
        ref.kosum(run, smoke=smoke)              # ŞASİ: referansın kendi yolu, dokunulmadan

    assert not e_csv.exists(), "koşum sandbox'a earnings.csv düşürmüş — pead PIT ihlali, DUR"
    m_sonra = motor_sha()
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    plan_dagilim = islem.get("plan_setup_dagilim") or {}
    dormant_plan_n = sum(int(plan_dagilim.get(s, 0)) for s in DORMANT_EKSTRA)
    dormant_islem = [t for t in defter if t.get("setup") in DORMANT_EKSTRA]

    if ac:
        # doğum-sayım mutabakatı: replika-yakalanan dormant seçim sayısı == plan doğumu
        assert len(kayit["dogum"]) == dormant_plan_n, \
            (f"doğum sayaçları uyuşmuyor: replika {len(kayit['dogum'])} ≠ plan_log "
             f"{dormant_plan_n} — kablo şüpheli, DUR")
        assert kayit["silahli_golge_n"] == 0, \
            "silahlı-öncelik ihlali sayacı sıfır değil — replika yasası bozuk, DUR"
        (outdir / f"dormant_dogumlar_{run}{ek}.json").write_text(json.dumps({
            "n": len(kayit["dogum"]),
            "setup_dagilim": {s: sum(1 for g in kayit["dogum"] if g["setup"] == s)
                              for s in DORMANT_EKSTRA},
            "ticker_n": len({g["ticker"] for g in kayit["dogum"]}),
            "dogumlar": kayit["dogum"],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        # dormant-yokluk kanıtı (süzgeç kapalı → sızıntı = enjeksiyon kaçağı)
        assert dormant_plan_n == 0 and not dormant_islem, \
            (f"KONTROL hücresinde dormant sızıntısı: plan={dormant_plan_n} "
             f"islem={len(dormant_islem)} — enjeksiyon kaçağı, DUR")

    dilim = dormant_dilim_kesiti(defter)
    pf, pf_neden = _pf(defter)
    ozet = {
        "kosum": run, "smoke": smoke,
        "kol_kimligi": {                          # kol kimliği damgası (exe006 Kritik-1 emsali)
            "dormant_icra_kapisi": ("ACIK — strategy.scan_entry süreç-içi replika "
                                    f"(B1 + {list(DORMANT_EKSTRA)}); doğum yamasız" if ac else
                                    "KAPALI — motor scan_entry olduğu gibi (kanca dahi yok)"),
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
        "plan_setup_dagilim": plan_dagilim,
        "verdict_dagilim": islem.get("verdict_dagilim"),
        "entry_rejects": islem.get("entry_rejects"),
        "dormant_plan_n": dormant_plan_n,
        "dormant_dilim": dilim,
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "sasi_kill_mtime_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_sha_ayni": m_once == m_sonra,
        "motor_kunye_kill4_once": kunye_once,
        "motor_kunye_kill4_sonra": motor_kunye_kiyas(m_sonra),
        "sandbox_earnings_csv_yok": True,
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] n={ozet['islem_n']} net={ozet['net_pnl_trades']} pf={pf} "
          f"dd={ozet['maxdd_kanonik']} sharpe={ozet['sharpe']} "
          f"dormant_plan_n={dormant_plan_n} dormant_islem_n={dilim['n']} "
          f"bütünlük={ozet['butunluk_gecerli']} motor_sha_ayni={ozet['motor_sha_ayni']} "
          f"kill4={ozet['motor_kunye_kill4_sonra']['kill4_tutarli']}")
    return ozet


def _on_ucus_artik(adlar: list[str]) -> None:
    artiklar = [a for a in adlar if (BURASI / a).exists()]
    if artiklar:
        sys.exit(f"önceki koşum artığı duruyor: {artiklar} — elle kaldır, yeniden başlat (DUR)")


# ---------------------------------------------------------------------------------------------
# FAZLAR
# ---------------------------------------------------------------------------------------------
def smoke_faz() -> int:
    """[1] DUMAN: dar pencere (2022-01→06), iki hücre + kapılar. Künye kill#4 tutarsızlığı
    BİLİNEN durum (K2/K5) — duman kill#1 duman kapısıyla ERKEN nötrlük sinyali üretir; otoriter
    kapı TAM çift-koşumdur. kill#1 duman düşerse exit 2 (dünya değişmiş)."""
    _on_ucus_artik([f"state_{r}_smoke" for r in HUCRELER])
    if (BURASI / "smoke").exists():
        sys.exit("smoke/ dizini duruyor — arşivlenmemiş duman var, elle kaldır (DUR)")
    m_pin = tazeleme_on_kontrol()
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"[smoke] pin OK · scan_entry=strategy.py:{noktalar['scan_entry_def_satiri']} "
          f"(sha {noktalar['scan_entry_kaynak_sha256'][:16]}) · replay çağrısı=backtest.py:"
          f"{noktalar['backtest_cagri_satiri']} · replika ön-sınama={on['gecti']} "
          f"(n={on['n_durum']}) · dormant_ekstra={noktalar['dormant_ekstra']}")

    rapor: dict = {
        "kart": "EDG-2026-049", "faz": "smoke",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256": m_pin, "uyarlama_beyani": uyarlama,
        "enjeksiyon_noktalari": noktalar,
        "replika_on_sinamasi": on,
        "hucreler": {},
    }
    rapor["hucreler"]["kontrol"] = hucre_kos(ref, "kontrol", smoke=True)
    sk = sasi_kapisi_smoke()
    rapor["sasi_kapisi_smoke"] = sk
    rapor["hucreler"]["dormant_acik"] = hucre_kos(ref, "dormant_acik", smoke=True)

    outdir = BURASI / "smoke"
    defter_k = json.loads((outdir / "islemler_tam_kontrol_smoke.json").read_text())
    defter_d = json.loads((outdir / "islemler_tam_dormant_acik_smoke.json").read_text())
    k3 = kill3_oz_sinama(defter_k, defter_d)
    (outdir / "oz_sinama_kill3_smoke.json").write_text(
        json.dumps(k3, ensure_ascii=False, indent=1), encoding="utf-8")
    yd = yer_degistirme(defter_k, defter_d)
    (outdir / "yer_degistirme_smoke.json").write_text(
        json.dumps(yd, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor["kill3_ozet"] = {k: k3[k] for k in ("ortak_n", "giris_yasasi_ihlal_n",
                                              "strict_tum_alan_ozdes", "kill3_gecti")}
    rapor["yer_degistirme_ozet"] = {"dormant_disi": {k: yd["dormant_disi"][k] for k in
                                                     ("kontrol_n", "dormant_acik_n", "ortak_n",
                                                      "cikan_n", "giren_n")},
                                    "dormant_dilimi_n": yd["dormant_dilimi"]["dormant_acik_n"]}
    rapor["delta_ci"] = {"degerlendirilmedi": "duman — kablo sınaması; Δ/CI yalnız TAM koşumda"}
    rapor["hukum_yok"] = "Bu rapor HÜKÜM İÇERMEZ."
    kod = 0
    if not sk["kill1_smoke_gecti"]:
        rapor["DURDU"] = ("kill#1 (duman): kontrol duman defterleri edg032c/kosum1_smoke ile "
                          "bayt-özdeş DEĞİL — dünya değişmiş; künye-tazeleme çift koşumuna "
                          "GEÇİLMEZ, teşhis Rol-1'e")
        kod = 2
    elif not k3["kill3_gecti"]:
        rapor["DURDU"] = "kill#3 (duman): giriş-yasası katmanı ihlali — kablo bozuk"
        kod = 2
    (BURASI / "sonuc_grid_smoke.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {BURASI / 'sonuc_grid_smoke.json'} (exit {kod})")
    return kod


def kontrol_kosumu(n: int) -> int:
    """[2]/[3] Künye-tazeleme kontrol koşumu #n (TAM pencere): bakir sandbox → hücre koşumu →
    çıktılar kontrol_kosum{n}/ altına taşınır (edg048 deseni AYNEN)."""
    hedef = BURASI / f"kontrol_kosum{n}"
    if hedef.exists():
        sys.exit(f"{hedef} zaten var — üzerine koşulmaz (elle kaldır, yeniden başlat)")
    _on_ucus_artik(list(KONTROL_TASINACAK))
    st = BURASI / "state_kontrol"
    if st.exists():
        shutil.rmtree(st)                 # BAKİR sandbox (edg032c determinizm standardı)

    t0 = dt.datetime.now(dt.timezone.utc)
    m_pin = tazeleme_on_kontrol()
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"[kontrol_kosum{n}] pin OK · scan_entry sha={noktalar['scan_entry_kaynak_sha256'][:16]} "
          f"· replika ön-sınama={on['gecti']}")

    ozet = hucre_kos(ref, "kontrol", smoke=False)
    t1 = dt.datetime.now(dt.timezone.utc)
    if not ozet["motor_sha_ayni"]:
        sys.exit(f"motor sha kontrol_kosum{n} İÇİNDE değişti — koşum geçersiz, DUR")
    if not ozet["butunluk_gecerli"]:
        sys.exit(f"şasi bütünlük bayrağı düştü (kontrol_kosum{n}) — koşum geçersiz, DUR")

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
        "ad": f"kontrol_kosum{n}",
        "amac": "künye tazeleme çift-koşumu (EDG-049; Rol-1 devri 2026-08-23, EDG-048 emsali)",
        "baslangic_utc": t0.isoformat(timespec="seconds"),
        "bitis_utc": t1.isoformat(timespec="seconds"),
        "sure_sn": round((t1 - t0).total_seconds(), 1),
        "motor_sha_pin": m_pin, "v273_pin": V273_PIN,
        "uyarlama_beyani": uyarlama, "enjeksiyon_noktalari": noktalar,
        "replika_on_sinamasi_gecti": on["gecti"],
        "sandbox": ("state_kontrol koşum öncesi silindi (bakir); şasi hazirla() EDG-022 donmuş "
                    "kopyalarından kurdu"),
        "tasinan_dosyalar_sha256": tasinan,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[kontrol_kosum{n}] bitti · süre={round((t1 - t0).total_seconds(), 1)}s → {hedef}")
    return 0


def kunye_tazele() -> int:
    """[4] Çift kapı + künye tazeleme: kosum1 ↔ kosum2 ↔ edg032c/kosum1 üç defterde bayt-özdeş
    ise TABAN_KUNYESI.json'un broker/strategy/guard kayıtları v273'e güncellenir (eski sha'lar
    kunye_tarihcesi'ne; yedek kunye_yedek_pre049.json). Özdeş DEĞİLSE künye TAZELENMEZ → exit 2."""
    k1, k2 = BURASI / "kontrol_kosum1", BURASI / "kontrol_kosum2"
    refdir = EDG032C / "kosum1"
    for d in (k1, k2):
        if not d.exists():
            sys.exit(f"kunye_tazele: koşum dizini yok: {d} — sıra bozuk, DUR")

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
    # koşum-günü önbellek uzunluğu — edg040 dersi; bayt kapısı zaten defterlerde)
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
    m_simdi = motor_sha()
    v273_dogru = all(m_simdi[f] == V273_PIN[f] for f in V273_PIN) and all(
        h1["motor_sha_once"][f] == V273_PIN[f] for f in V273_PIN)

    gecti = bool(kapi_gecti and kunye_civisi and ae_ozdes and bloklar_esit
                 and motor_arasi_ayni and v273_dogru)

    out = {
        "adim": "EDG-049 KÜNYE TAZELEME ÇİFT KAPISI (Rol-1 devri 2026-08-23; EDG-048 emsali)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("TAM kontrol iki kez, taze süreç + bakir sandbox, v273 motorla (K2/K5 dalgası "
                  "sonrası); üç defter kosum1 ↔ kosum2 ↔ edg032c/kosum1 BAYT-ÖZDEŞ olmalı. "
                  "Ek kanıt: alan_envanteri üç yönlü bayt + sonuc ölçüm blokları k1↔k2 "
                  "derin-eşit + motor dört noktada sabit + v273 pin doğrulaması. K2'nin "
                  "(giriş penceresi 13:45) replay'e sızmadığı iddiasını bu özdeşlik SINAR."),
        "kapi_defterleri": kapi, "kapi_uc_yonlu_ozdes": kapi_gecti,
        "kunye_civisi_tutarli": kunye_civisi,
        "ek_kanit_alan_envanteri": {**ae, "uc_yonlu_ozdes": ae_ozdes},
        "ek_kanit_sonuc_bloklari_k1k2": blok_k1k2,
        "bilgi_sonuc_bloklari_k1_edg032c": blok_k1ref,
        "motor_dort_noktada_sabit": motor_arasi_ayni,
        "v273_pin_dogrulandi": v273_dogru,
        "TAZELEME_GECTI": gecti,
        "hukum": None,   # hüküm Rol-1'in; bu bayrak mekanik sha kıyasıdır
    }

    if gecti:
        # ── KÜNYE GÜNCELLEMESİ (ölçüm dizini dışına TEK yazım; Rol-1 yetki devri) ──
        (BURASI / "kunye_yedek_pre049.json").write_bytes(kunye_once_bayt)   # eski hâl korunur
        guncellenen = {}
        for f in ("broker.py", "strategy.py", "guard.py"):
            eski = dict(kunye["motor_sha256"]["kosum1_once"][f])
            if eski["sha256"] == V273_PIN[f]:
                continue                          # zaten güncel (yeniden koşum güvenliği)
            mt = (REPO / "meridian" / f).stat().st_mtime_ns
            yeni_kayit = {"sha256": V273_PIN[f], "sha256_16": V273_PIN[f][:16], "mtime_ns": mt}
            kunye["motor_sha256"]["kosum1_once"][f] = dict(yeni_kayit)
            kunye["motor_sha256"]["kosum2_sonra"][f] = dict(yeni_kayit)
            kunye.setdefault("kunye_tarihcesi", []).append({
                "tarih_utc": out["olcum_zamani"], "dosya": f,
                "eski_sha256": eski["sha256"], "eski_mtime_ns": eski["mtime_ns"],
                "yeni_sha256": V273_PIN[f],
                "neden": TAZELEME_NEDEN[f] + (" kosum1_once + kosum2_sonra kayıtları birlikte "
                                              "güncellendi (dort_noktada_sabit iç tutarlılığı)."),
                "kanit": str(BURASI / "determinizm_kunye.json"),
                "yedek": str(BURASI / "kunye_yedek_pre049.json"),
                "yetki": "Rol-1 devri (EDG-2026-049 ölçüm turu koordinatör mesajı, 2026-08-23)",
            })
            guncellenen[f] = {"eski": eski["sha256"], "yeni": V273_PIN[f]}
        kunye_yolu.write_text(json.dumps(kunye, ensure_ascii=False, indent=1), encoding="utf-8")
        out["kunye_guncellendi"] = {
            "dosya": str(kunye_yolu),
            "once_sha256": hashlib.sha256(kunye_once_bayt).hexdigest(),
            "sonra_sha256": _sha_full(kunye_yolu),
            "dosyalar": guncellenen,
        }
    else:
        out["kunye_guncellendi"] = None
        out["DURDU"] = ("çift kapı DÜŞTÜ — dünya değişmiş demektir (K2 pencere sızıntısı dahil "
                        "olası sınıf); künye TAZELENMEZ, dormant_acik koşulmaz; teşhis Rol-1'e")

    (BURASI / "determinizm_kunye.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"TAZELEME ÇİFT KAPISI: defter={kapi_gecti} çivi={kunye_civisi} ae={ae_ozdes} "
          f"blok={bloklar_esit} motor={motor_arasi_ayni} v273={v273_dogru} → "
          f"{'GEÇTİ — künye güncellendi' if gecti else 'DÜŞTÜ — künye TAZELENMEDİ'}")
    print(f"yazıldı: {BURASI / 'determinizm_kunye.json'}")
    return 0 if gecti else 2


def dormant_acik_tam() -> int:
    """[5] Kartın kalan akışı: dormant_acik TAM hücresi + kill kapıları + dilim + Δ/CI +
    yer-değiştirme + sonuc_grid.json. Ön-şart: kunye_tazele GEÇTİ ve künye motorla 4/4 tutarlı."""
    det_yolu = BURASI / "determinizm_kunye.json"
    if not det_yolu.exists():
        sys.exit("dormant_acik: determinizm_kunye.json yok — sıra bozuk (önce çift kapı), DUR")
    det = json.loads(det_yolu.read_text())
    if not det["TAZELEME_GECTI"]:
        sys.exit("dormant_acik: künye tazeleme kapısı GEÇMEDİ — hücre koşulmaz, DUR")
    _on_ucus_artik(["sonuc_dormant_acik.json", "islemler_tam_dormant_acik.json",
                    "hucre_dormant_acik.json"])
    st = BURASI / "state_dormant_acik"
    if st.exists():
        shutil.rmtree(st)                 # bakir sandbox

    motor_once = motor_sha()
    kunye_kiyas = motor_kunye_kiyas(motor_once)
    if not kunye_kiyas["kill4_tutarli"]:
        sys.exit("dormant_acik: kill#4 — motor sha GÜNCEL künyeyle bile tutarsız, DUR")
    ref, uyarlama = referans_modul()
    noktalar = enjeksiyon_noktasi_dogrula()
    on = replika_on_sinama()
    print(f"[dormant_acik] kill4(güncel künye)=True · scan_entry sha="
          f"{noktalar['scan_entry_kaynak_sha256'][:16]} · replika ön-sınama={on['gecti']}")

    rapor: dict = {
        "kart": "EDG-2026-049", "smoke": False,
        "faz": "dormant_acik (künye-tazeleme sonrası TAM)",
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
                                      "Şasi parametre enjeksiyonu YOK (iki hücre de merkez).")},
        "enjeksiyon_noktalari": {
            "plan_icra_suzgeci": (f"meridian/strategy.py:{noktalar['scan_entry_def_satiri']} "
                                  "scan_entry (kaynak sha "
                                  f"{noktalar['scan_entry_kaynak_sha256'][:16]}…) — "
                                  "dormant_acik'ta süreç-içi replika: süzgeç "
                                  f"B1 + extra + {noktalar['dormant_ekstra']}; scan_all/doğum "
                                  "YAMASIZ; kontrolde kanca dahi YOK"),
            "replay_cagri": (f"meridian/backtest.py:{noktalar['backtest_cagri_satiri']} "
                             "(ticker-günü başına tek sinyal; bütçe-açık seanslarda)"),
        },
        "replika_on_sinamasi": {"gecti": on["gecti"], "n_durum": on["n_durum"],
                                "tablo": on["tablo"]},
        "beyanli_sinirlar": ("(1) replay ticker-günü başına TEK sinyal (silahlı ateşlediyse "
                             "dormant o ticker-günde doğamaz); (2) tarama yalnız bütçe-açık "
                             "günlerde — canlı keşif-modu doğumları burada yok. Kart beyanlı "
                             "sınır-1'in somut mekanizmaları; dilim n bu beyanla okunur."),
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
    hucreler["dormant_acik"] = hucre_kos(ref, "dormant_acik", smoke=False)
    rapor["hucreler"] = hucreler
    rapor["kontrol_kaynagi"] = (f"{k1} (künye-tazeleme kosum1 — edg032c/kosum1 ile bayt-özdeş "
                                "kanıtlı; kill#1 bu özdeşliğin kendisi)")
    if not hucreler["dormant_acik"]["motor_sha_ayni"] or \
            not hucreler["dormant_acik"]["motor_kunye_kill4_sonra"]["kill4_tutarli"]:
        rapor["DURDU"] = "kill#4: motor sha dormant_acik koşumunda değişti/künyeyle tutarsız — geçersiz"
        print("KILL#4 DÜŞTÜ (dormant_acik) — ölçüm DURDU")
        return yaz_ve_cik(2)
    if not hucreler["dormant_acik"]["butunluk_gecerli"]:
        rapor["DURDU"] = "şasi bütünlük bayrağı düştü (dormant_acik) — hücre geçersiz"
        print("BÜTÜNLÜK DÜŞTÜ (dormant_acik) — ölçüm DURDU")
        return yaz_ve_cik(2)

    defter_k = json.loads((k1 / "islemler_tam_kontrol.json").read_text())
    defter_d = json.loads((BURASI / "islemler_tam_dormant_acik.json").read_text())

    # kill#3 — iki katmanlı ortak-işlem öz-sınaması (KOMUT.txt ön-beyanı)
    k3 = kill3_oz_sinama(defter_k, defter_d)
    (BURASI / "oz_sinama_kill3.json").write_text(
        json.dumps(k3, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor["kill3"] = {k: k3[k] for k in ("ortak_n", "alan_fark_sayimi", "strict_tum_alan_ozdes",
                                         "strict_farkli_satir_n", "giris_yasasi_ihlal_n",
                                         "kill3_gecti")}
    print(f"  KILL#3: ortak={k3['ortak_n']} giriş-yasası-ihlal={k3['giris_yasasi_ihlal_n']} "
          f"strict_özdeş={k3['strict_tum_alan_ozdes']} → "
          f"{'GEÇTİ' if k3['kill3_gecti'] else 'DÜŞTÜ'}")
    if not k3["kill3_gecti"]:
        rapor["DURDU"] = "kill#3: dormant-dışı giriş yasası değişmiş (ortak işlem giriş-yasası alanı farklı) — hücre geçersiz"
        print("KILL#3 DÜŞTÜ — ölçüm DURDU")
        return yaz_ve_cik(2)

    # kill#5 — yer-değiştirme (zorunlu rapor; dumanda da üretildi)
    yd = yer_degistirme(defter_k, defter_d)
    (BURASI / "yer_degistirme.json").write_text(
        json.dumps(yd, ensure_ascii=False, indent=1), encoding="utf-8")
    rapor["yer_degistirme"] = {
        "dosya": str(BURASI / "yer_degistirme.json"),
        "dormant_disi_ozet": {k: yd["dormant_disi"][k] for k in
                              ("kontrol_n", "dormant_acik_n", "ortak_n", "cikan_n", "giren_n",
                               "cikan_ozet", "giren_ozet")},
        "dormant_dilimi_n": {"kontrol": yd["dormant_dilimi"]["kontrol_n"],
                             "dormant_acik": yd["dormant_dilimi"]["dormant_acik_n"]},
    }
    print(f"  YER-DEĞİŞTİRME: dormant-dışı kontrol={yd['dormant_disi']['kontrol_n']} "
          f"dormant_acik={yd['dormant_disi']['dormant_acik_n']} "
          f"ortak={yd['dormant_disi']['ortak_n']} çıkan={yd['dormant_disi']['cikan_n']} "
          f"giren={yd['dormant_disi']['giren_n']} · dormant-dilim "
          f"{yd['dormant_dilimi']['kontrol_n']}→{yd['dormant_dilimi']['dormant_acik_n']}")

    # dormant-dilim kesiti (kart features_asof)
    dilim = hucreler["dormant_acik"]["dormant_dilim"]
    (BURASI / "dormant_dilim.json").write_text(
        json.dumps(dilim, ensure_ascii=False, indent=1), encoding="utf-8")

    # n=0 kuralı (kart, donuk): dormant PLAN doğumu 0 → "replay'de ölçülemez + neden"
    dormant_plan_n = hucreler["dormant_acik"]["dormant_plan_n"]
    if dormant_plan_n == 0:
        rapor["OLCULEMEZ"] = {
            "damga": "replay'de ölçülemez",
            "neden": ("dormant_acik hücresinde icra-yolu kapısı AÇIK olmasına rağmen replay "
                      "penceresi boyunca hiçbir dormant plan doğmadı (plan_setup_dagilim "
                      "dormant toplamı 0): scan_all dormant evaluator'ları bütçe-açık "
                      "seanslarda ya hiç sinyal üretmedi ya da her seferinde aynı ticker-günde "
                      "silahlı kurulum öncelik aldı (beyanlı sınır-1/2). Kart kuralı: karar "
                      "canlı-birikim yoluna devredilir."),
            "kanit": {"plan_setup_dagilim": hucreler["dormant_acik"]["plan_setup_dagilim"],
                      "yer_degistirme_sifir_fark": (yd["dormant_disi"]["cikan_n"] == 0
                                                    and yd["dormant_disi"]["giren_n"] == 0)},
        }
        rapor["delta_ci"] = {"degerlendirilmedi": "n=0 kuralı — dormant plan doğmadı; Δ/CI anlamsız"}
        rapor["hukum_yok"] = "Bu rapor HÜKÜM İÇERMEZ; damganın işlenmesi Rol-1'in işidir."
        print("  n=0 KURALI: dormant plan doğmadı → 'replay'de ölçülemez' damgası (hüküm Rol-1'e)")
        return yaz_ve_cik(0)

    # Δ+CI (kart kuralı: Δ(dormant_acik−kontrol); aylar kontrol seanslarından)
    seanslar = json.loads((k1 / "seanslar_kontrol.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})
    rapor["delta_ci"] = {"dormant_acik_vs_kontrol": delta_pnl_ci(defter_k, defter_d, aylar)}
    dd_ = rapor["delta_ci"]["dormant_acik_vs_kontrol"]
    print(f"  Δ[dormant_acik−kontrol]: {dd_['delta_pnl']} CI95={dd_['ci95']} "
          f"({dd_['sifir_disinda']}) · dilim n={dilim['n']}")

    rapor["karar_girdileri_okuma_rol1"] = {
        "delta_ci_alt": dd_["ci95"][0], "dormant_dilim_n": dilim["n"],
        "not": ("ARSENAL çıtalı karar kuralının (Δ CI-alt > 0 ∧ n ≥ 30) OKUNMASI Rol-1'in; "
                "bu satır yalnız girdileri yan yana koyar, hüküm İÇERMEZ.")}
    rapor["hukum_yok"] = ("Bu rapor HÜKÜM İÇERMEZ. Karar kuralının okunması ve kill#5 raporu "
                          "eşliğinde hüküm Rol-1'in işidir.")
    return yaz_ve_cik(0)


if __name__ == "__main__":
    _faz = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    if _faz == "smoke":
        raise SystemExit(smoke_faz())
    if _faz == "kontrol1":
        raise SystemExit(kontrol_kosumu(1))
    if _faz == "kontrol2":
        raise SystemExit(kontrol_kosumu(2))
    if _faz == "kunye_tazele":
        raise SystemExit(kunye_tazele())
    if _faz == "dormant_acik":
        raise SystemExit(dormant_acik_tam())
    sys.exit("kullanım: olcum.py smoke | kontrol1 | kontrol2 | kunye_tazele | dormant_acik "
             "(sıra zorunlu; her faz ayrı süreç — KOMUT.txt)")
