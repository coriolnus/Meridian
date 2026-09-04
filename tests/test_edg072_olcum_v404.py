"""tests/test_edg072_olcum_v404.py — EDG-2026-072 ÖLÇÜM betiğinin çivisi (2026-09-04, EDG-072).

NE ÖLÇER. `research/olcumler/edg072_rejim_cikis/olcum.py` — rejim-koşullu ÇIKIŞ override'ının
(trend_up geniş trail/uzun time-stop, chop kısa time-stop/erken breakeven) ölçüm betiği. Bu dosya
AŞAĞIDAKİLERİ ölçer (EDG-019 `tests/test_edg019_olcum_v389.py` deseni AYNEN):
  (a) çarpan → mutlak değer türetimi (`harita_olustur`/`_carpan_uygula`) TABANDAN doğru hesaplıyor
      mu, YUVARLAMA BEYANI (round-half-to-even) uygulanıyor mu;
  (b) öz-sınama 1 (`oz_sinama_1`) gerçekten kontrol ediyor mu — MUTASYON (bozuk harita) onu
      GERÇEKTEN ÖTÜRÜYOR mu (CLAUDE.md §6: "çivi yeşili kanıt değildir");
  (c) ADIM-0'ın dayandığı sha256 içerik-adresleme (git DEĞİL — modül başlığı "GİT SAPMASI")
      gerçek bir değişikliği YAKALIYOR mu (negatif kontrol, tmp_path);
  (d) POZİTİF KONTROL: `config.resolve_params` → `strategy.manage_position` zinciri (motor
      fonksiyonları BİREBİR, yamasız), küçük sentetik bar seti üzerinde — sentetik chop
      `exit.time_stop_days=1` override'ı bars_held=1'de time_stop ATEŞLİYOR mu, AYNI sentetik
      bar/pozisyon TABAN (time_stop=15) altında ATEŞLEMİYOR mu (kontrast = MUTASYON).

KAPSAM DIŞI: kartın hükmü (Rol-1 verir) ve TAM/duman pencere replay koşumlarının sayısal sonucu —
bu dosya betiğin DOĞRU ÖLÇTÜĞÜNÜ kanıtlar, bir terfi/emeklilik kararı vermez. Tam replay (~30dk)
BU ÇİVİDE KOŞULMAZ (pytest SERİ tavanı) — yalnız `resolve_params`/`manage_position` motor
fonksiyonları küçük sentetik girdiyle çağrılır (saniyeler mertebesinde).

EK — EDG-2026-073 R2 (2026-09-04, Rol-1 r1 kararı: EDG-072 "kaldı — şasi bayatlığı", §5 kriter
yerinde düzeltilmedi; kod AYNI `olcum.py`de `kiyasla --kart EDG-2026-073` ile devam eder). Bu
dosyaya AŞAĞIDAKİLER EKLENDİ:
  (e) 073 ŞASİ SINAMASI (`sasi_sinamasi_073`, kill-1): `resolve_params(params,{},rejim)` HER
      gözlenen rejim için `params`'la birebir eşit mi — normalde TRIVIAL geçer (by_regime={}
      falsy); MUTASYON (resolve_params'ı yan-etkili bir sürüme çeviren monkeypatch, hem "eff
      params'tan farklı" hem "girdi yerinde bozuldu" biçimleri) öter mi;
  (f) `kiyasla(kart=..., kok=...)` seçim mantığı: EDG-2026-073 istenince edg072+edg073 İKİSİ de
      (kok=tam'da), EDG-2026-072 istenince YALNIZ edg072 hesaplanıyor mu (çağrı izleme,
      monkeypatch'li sahte alt-fonksiyonlarla — gerçek 30dk'lık koşum GEREKMEZ);
  (g) `kill2_motor_bar_073`: DOĞRUDAN yol (üç koşum da kendi `bar_onbellek_ozet`ini taşıyorsa)
      POST-HOC ölçümü atlıyor mu, uyuşmazlığı yakalıyor mu; `adim0c_taze`, `_taban_params`,
      `_bar_cache_ozet`, `_log_baslangic_ts` yardımcılarının doğru ölçtüğü.
"""
from __future__ import annotations

import hashlib
import pathlib

import pandas as pd
import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg072_rejim_cikis" / "olcum.py"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg072_olcum")


# ==================================================================================
# (a) çarpan → mutlak değer türetimi + yuvarlama beyanı
# ==================================================================================

def test_carpan_uygula_int_round_half_to_even():
    o = _olcum()
    # 15 × 1.5 = 22.5 → 22 (22 çift, round-half-to-even) — trend_up time_stop (H1/H2)
    assert o._carpan_uygula(15, 1.5, int) == 22
    # 15 × 0.5 = 7.5 → 8 (8 çift) — chop time_stop (H1/H2)
    assert o._carpan_uygula(15, 0.5, int) == 8


def test_carpan_uygula_float_6_hane():
    o = _olcum()
    assert o._carpan_uygula(2.5, 1.5, float) == pytest.approx(3.75)
    assert o._carpan_uygula(1.0, 0.5, float) == pytest.approx(0.5)


def test_harita_olustur_h1_h2_kart_carpanlariyla_birebir():
    """Kart k_registry (donuk): H1 = trend_up{trail×1.5, time_stop×1.5} + chop{time_stop×0.5};
    H2 = H1 + chop{breakeven×0.5}. Taban EDG-022 donmuş strategy.yaml değerleridir (test kendi
    sentetik tabanını kullanır — türetim KURALINI sınar, gerçek dosyayı DEĞİL)."""
    o = _olcum()
    taban = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0}

    h1 = o.harita_olustur("h1", taban)
    assert h1["trend_up"] == {"exit.trail_atr_mult": 3.75, "exit.time_stop_days": 22}
    assert h1["chop"] == {"exit.time_stop_days": 8}
    assert h1["trend_down"] == {} and h1["high_vol"] == {}

    h2 = o.harita_olustur("h2", taban)
    assert h2["trend_up"] == h1["trend_up"]
    assert h2["chop"] == {"exit.time_stop_days": 8, "exit.breakeven_r": 0.5}

    kontrol = o.harita_olustur("kontrol", taban)
    assert kontrol == {rg: {} for rg in o.REGIMES}

    pk = o.harita_olustur("pk", taban)
    assert pk["chop"] == {"exit.time_stop_days": 1}
    assert pk["trend_up"] == {}


def test_harita_olustur_taban_degisince_mutlak_deger_TAKIP_EDER():
    """MUTASYON: taban değişirse (donmuş strategy.yaml farklı bir sürüm taşısaydı) harita
    hardcode DEĞİL, türetilmiş kalmalı — sabit 3.75/22 döndürmemeli."""
    o = _olcum()
    taban2 = {"exit.trail_atr_mult": 2.0, "exit.time_stop_days": 10, "exit.breakeven_r": 1.0}
    h1 = o.harita_olustur("h1", taban2)
    assert h1["trend_up"]["exit.trail_atr_mult"] == pytest.approx(3.0)      # 2.0×1.5
    assert h1["trend_up"]["exit.time_stop_days"] == 15                     # 10×1.5
    assert h1["chop"]["exit.time_stop_days"] == 5                          # 10×0.5


# ==================================================================================
# (b) öz-sınama 1 — GERÇEKTEN kontrol ediyor mu (mutasyon çivisi)
# ==================================================================================

def _bounds():
    return {"exit.trail_atr_mult": {"min": 1.0, "max": 5.0}, "exit.time_stop_days": {"min": 3, "max": 40},
            "exit.breakeven_r": {"min": 0.0, "max": 3.0}}


def test_oz_sinama_1_normal_hucrede_gecer():
    o = _olcum()
    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0,
             "entry.rs_rating_min": 70}
    harita = o.harita_olustur("h1", params)
    r = o.oz_sinama_1("h1", params, harita, _bounds())
    assert r["gecti"] is True
    assert r["bounds_ihlal"] == []


def test_oz_sinama_1_dokunulmayan_anahtar_SIZARSA_YAKALANIR():
    """MUTASYON: harita, DEKLARE ETMEDİĞİ bir anahtarı da eff'te değiştirseydi (yüzey sızıntısı —
    resolve_params'ın DIŞINDA bir yan etki), öz-sınama 1 bunu PATLAMALI. Burada resolve_params'ın
    KENDİSİ değil, öz-sınamanın "dokunulmayan anahtar" kontrolünün gerçekten sıkı olduğu, bozuk bir
    harita ile ölçülür (harita, chop'ta VAR OLMAYAN entry.rs_rating_min'i de listelemiş gibi
    davranarak eff'i manuel bozar)."""
    o = _olcum()
    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0}
    harita_bozuk = {rg: {} for rg in o.REGIMES}
    harita_bozuk["chop"] = {"exit.time_stop_days": 8}

    import meridian.config as _cfg
    orij = _cfg.resolve_params

    def _bozuk_resolve(params_, by_regime_, regime_):
        eff = orij(params_, by_regime_, regime_)
        if regime_ == "chop":
            eff["exit.trail_atr_mult"] = 999.0     # DEKLARE EDİLMEMİŞ sızıntı
        return eff

    _cfg.resolve_params = _bozuk_resolve
    try:
        with pytest.raises(AssertionError):
            o.oz_sinama_1("h1", params, harita_bozuk, _bounds())
    finally:
        _cfg.resolve_params = orij     # motoru geri bırak — başka teste sızmasın


def test_oz_sinama_1_pk_hucresi_bounds_disi_BEYANLI_yakalanir():
    """PK (kart pozitif_kontrol) KASITLI uç değer taşır (chop time_stop_days=1 < bounds min 3) —
    öz-sınama bunu PATLATMAZ (PK, K registry DIŞI, hüküm yüzeyi DEĞİL) ama `bounds_ihlal` alanında
    KAYDEDER — sessizce yutulmaz (YASA 4/6)."""
    o = _olcum()
    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0}
    harita = o.harita_olustur("pk", params)
    r = o.oz_sinama_1("pk", params, harita, _bounds())
    assert r["gecti"] is True
    assert len(r["bounds_ihlal"]) == 1
    assert r["bounds_ihlal"][0]["anahtar"] == "exit.time_stop_days"
    assert r["bounds_ihlal"][0]["rejim"] == "chop"


# ==================================================================================
# (c) ADIM-0 sha256 içerik-adresleme — negatif kontrol (git DEĞİL — modül başlığı GİT SAPMASI)
# ==================================================================================

def test_sha_full_icerik_degisince_hash_DEGISIR(tmp_path):
    o = _olcum()
    f = tmp_path / "girdi.json"
    f.write_text('{"a": 1}')
    h1 = o._sha_full(f)
    assert h1 == hashlib.sha256(f.read_bytes()).hexdigest()

    f.write_text('{"a": 2}')      # TEK bayt fark — ADIM-0'ın dayandığı sensörün gerçekten
    h2 = o._sha_full(f)           # ölçtüğünü kanıtlayan mutasyon (sha değişmezse sensör kördür)
    assert h2 != h1


def test_sha_full_dosya_yoksa_None_UYDURMAZ(tmp_path):
    o = _olcum()
    assert o._sha_full(tmp_path / "yok.json") is None


def test_edg026_sha256_sabitleri_GERCEK_dosyalarla_esit():
    """EDG026_SHA256 bu turda `shasum -a 256` ile DONDURULDU (git DEĞİL). Bu test dondurulmuş
    sabitlerin repodaki GERÇEK EDG-026 dosyalarıyla bugün örtüştüğünü doğrular — ayrışırsa
    (EDG-026 dosyaları elle değiştirildiyse) KIRMIZI olup haber verir (ADIM-0'ın kendisi de aynı
    kontrolü koşum-anında yapar; bu test onu donmuş halde tekrar sınar)."""
    o = _olcum()
    for ad, beklenen in o.EDG026_SHA256.items():
        simdi = o._sha_full(o.EDG026 / ad)
        assert simdi == beklenen, f"{ad}: EDG026_SHA256 sabiti dosyayla ayrıştı (dosya değişmiş olabilir)"


# ==================================================================================
# (d) POZİTİF KONTROL — resolve_params → manage_position (motor fonksiyonları, sentetik bar seti)
# ==================================================================================

def _sentetik_bars(n: int = 20, seviye: float = 100.0) -> pd.DataFrame:
    """ATR hesaplanabilir (n > ATR_PERIOD=14), sabit dar aralık — trail/breakeven/giveback
    TETİKLENMEZ (yalnız time_stop dalı sınanır)."""
    idx = pd.date_range("2024-01-02", periods=n, freq="B")
    rows = [{"open": seviye - 0.05, "high": seviye + 0.3, "low": seviye - 0.3,
             "close": seviye, "volume": 1_000_000} for _ in range(n)]
    return pd.DataFrame(rows, index=idx)


def _sentetik_pozisyon() -> dict:
    return {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0, "pivot": 0.0}


def test_pk_sentetik_chop_time_stop_1_manage_position_ATESLER():
    """POZİTİF KONTROL (kart pozitif_kontrol, kısım 2): resolve_params(params, {"chop":
    {"exit.time_stop_days": 1}}, "chop") → manage_position — bars_held=1'de zaman-stopu ATEŞLEMELİ.
    Motor fonksiyonları (config.resolve_params, strategy.manage_position) BİREBİR — yamasız."""
    from meridian import config, strategy as strat

    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0,
             "exit.giveback_pct": 0.0, "exit.chandelier_lookback": 0}
    by_regime = {"chop": {"exit.time_stop_days": 1}}
    eff = config.resolve_params(params, by_regime, "chop")
    assert eff["exit.time_stop_days"] == 1

    bars = _sentetik_bars()
    pos = _sentetik_pozisyon()
    dec = strat.manage_position(bars, pos, eff, bars_held=1, regime_ok=True)
    assert dec.exit_now is True
    assert dec.exit_reason == "time_stop"


def test_mutasyon_override_YOKSA_AYNI_bars_held_ATESLEMEZ():
    """MUTASYON KANITI (yukarıdaki testin kontrastı — CLAUDE.md §6): AYNI sentetik bar/pozisyon/
    bars_held, override OLMADAN (taban time_stop=15) time_stop ATEŞLEMEMELİ — ateşliyorsa
    yukarıdaki PK hiçbir şey ölçmüyor, manage_position her zaman 'çık' diyordur."""
    from meridian import config, strategy as strat

    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0,
             "exit.giveback_pct": 0.0, "exit.chandelier_lookback": 0}
    eff_taban = config.resolve_params(params, {}, "chop")     # override YOK — eff == params
    assert eff_taban["exit.time_stop_days"] == 15

    bars = _sentetik_bars()
    pos = _sentetik_pozisyon()
    dec = strat.manage_position(bars, pos, eff_taban, bars_held=1, regime_ok=True)
    assert dec.exit_now is False, "taban time_stop=15 iken bars_held=1 zaman-stopu ATEŞLEMEMELİ"


def test_pk_diger_rejimde_UYGULANMAZ_tek_anahtar_yuzeyi():
    """PK haritası yalnız `chop`a dokunur — `trend_up` günü aynı bars_held=1 ile çağrılırsa taban
    time_stop=15 yürümeli (yüzey sızıntısı yok — tek-rejim izolasyonu)."""
    from meridian import config, strategy as strat

    params = {"exit.trail_atr_mult": 2.5, "exit.time_stop_days": 15, "exit.breakeven_r": 1.0,
             "exit.giveback_pct": 0.0, "exit.chandelier_lookback": 0}
    by_regime = {"chop": {"exit.time_stop_days": 1}}
    eff_trend_up = config.resolve_params(params, by_regime, "trend_up")
    assert eff_trend_up == params      # trend_up haritada YOK → dokunulmamış

    bars = _sentetik_bars()
    pos = _sentetik_pozisyon()
    dec = strat.manage_position(bars, pos, eff_trend_up, bars_held=1, regime_ok=True)
    assert dec.exit_now is False


# ==================================================================================
# EDG-2026-073 R2 (2026-09-04) — (e) şasi sınaması + mutasyon, (f) kart seçim mantığı,
# (g) kill-2 motor/bar + yardımcı fonksiyonlar
# ==================================================================================

# ---- (e) şasi sınaması (kill-1) ---------------------------------------------------

def test_sasi_sinamasi_073_normalde_TUM_gozlenen_rejimlerde_gecer():
    o = _olcum()
    r = o.sasi_sinamasi_073({"trend_up", "chop", "trend_down", "high_vol", "sentetik_rejim_XYZ"})
    assert r["gecti"] is True
    assert r["tetiklendi"] is False
    assert len(r["kayit"]) == 5   # bilinmeyen rejim etiketi dahil — resolve_params({}) HER ZAMAN no-op


def test_sasi_sinamasi_073_MUTASYON_eff_farkli_donen_resolve_params_YAKALANIR():
    """MUTASYON KANITI (CLAUDE.md §6, coordinator talebi): resolve_params'ı YAN ETKİLİ hale
    getiren bir hataya karşı şasi sınamasının GERÇEKTEN öttüğü."""
    o = _olcum()
    import meridian.config as _cfg
    orij = _cfg.resolve_params

    def _yan_etkili(params_, by_regime_, regime_):
        eff = dict(params_)
        eff["exit.time_stop_days"] = 999      # DEKLARE EDİLMEMİŞ — by_regime BOŞ olsa bile bozar
        return eff

    _cfg.resolve_params = _yan_etkili
    try:
        r = o.sasi_sinamasi_073({"trend_up", "chop"})
        assert r["tetiklendi"] is True
        assert r["gecti"] is False
        assert all(not k["eff_params_esit"] for k in r["kayit"])
    finally:
        _cfg.resolve_params = orij     # motoru geri bırak — başka teste sızmasın


def test_sasi_sinamasi_073_MUTASYON_girdiyi_yerinde_bozan_resolve_params_YAKALANIR():
    """İkinci mutasyon biçimi: resolve_params GİRDİ sözlüğünü YERİNDE mutasyona uğratırsa
    (gerçek resolve_params `dict(params)` ile kopyalar, asla yerinde değiştirmez)
    `girdi_mutasyona_ugramadi` False olmalı."""
    o = _olcum()
    import meridian.config as _cfg
    orij = _cfg.resolve_params

    def _girdi_bozan(params_, by_regime_, regime_):
        params_["position_size_r"] = -1.0     # GİRDİYİ YERİNDE BOZAR
        return dict(params_)

    _cfg.resolve_params = _girdi_bozan
    try:
        r = o.sasi_sinamasi_073({"trend_up"})
        assert r["tetiklendi"] is True
        assert r["kayit"][0]["girdi_mutasyona_ugramadi"] is False
    finally:
        _cfg.resolve_params = orij


def test_taban_params_position_size_r_enjekte_EDG022_donmus():
    o = _olcum()
    p = o._taban_params()
    assert p["position_size_r"] == pytest.approx(o.BOYUT_R)
    assert p["exit.time_stop_days"] == 15      # EDG-022 donmuş taban (bilinen sabit, öz-sınama tabanıyla AYNI)
    assert p["exit.trail_atr_mult"] == pytest.approx(2.5)


# ---- (f) `kiyasla(kart, kok)` seçim mantığı — gerçek 30dk koşum GEREKMEZ (monkeypatch'li stub) ----

def test_kiyasla_kart_073_HEM_072_HEM_073_hesaplar_ve_TEK_dosyaya_yazar(tmp_path, monkeypatch):
    o = _olcum()
    monkeypatch.setattr(o, "SANDBOX", tmp_path)
    cagrilar = []

    def sahte_072(kok):
        cagrilar.append(("072", kok))
        return {"kart": "EDG-2026-072", "olculemedi": "test-stub"}

    def sahte_073(kok):
        cagrilar.append(("073", kok))
        return {"kart": "EDG-2026-073", "olculemedi": "test-stub"}

    monkeypatch.setattr(o, "kiyasla_072", sahte_072)
    monkeypatch.setattr(o, "kiyasla_073", sahte_073)

    out = o.kiyasla(kart="EDG-2026-073", kok="tam")
    assert "edg072" in out and "edg073" in out
    assert ("072", "tam") in cagrilar and ("073", "tam") in cagrilar
    import datetime as _dt
    bugun = _dt.date.today().isoformat()
    assert (tmp_path / f"sonuc_{bugun}.json").exists()


def test_kiyasla_kart_072_YALNIZ_072_hesaplar_073_HIC_CAGRILMAZ(tmp_path, monkeypatch):
    o = _olcum()
    monkeypatch.setattr(o, "SANDBOX", tmp_path)
    cagrilar = []
    monkeypatch.setattr(o, "kiyasla_072", lambda kok: (cagrilar.append(("072", kok)),
                                                       {"kart": "EDG-2026-072"})[1])
    monkeypatch.setattr(o, "kiyasla_073", lambda kok: (cagrilar.append(("073", kok)),
                                                       {"kart": "EDG-2026-073"})[1])

    out = o.kiyasla(kart="EDG-2026-072", kok="tam")
    assert "edg072" in out and "edg073" not in out
    assert cagrilar == [("072", "tam")]        # 073 HİÇ ÇAĞRILMADI
    import datetime as _dt
    bugun = _dt.date.today().isoformat()
    assert (tmp_path / f"sonuc_edg072_{bugun}.json").exists()
    assert not (tmp_path / f"sonuc_{bugun}.json").exists()   # 073 dosyasına YAZILMADI


def test_kiyasla_kok_duman_073de_072_ATLANIR_cagrilmaz(tmp_path, monkeypatch):
    """kok≠tam iken eski-C kıyası (edg072) anlamsız (C yalnız tam pencere taşır) — `kiyasla_072`
    hiç çağrılmadan bir 'olculemedi' yer tutucusu üretilmeli."""
    o = _olcum()
    monkeypatch.setattr(o, "SANDBOX", tmp_path)
    cagrilar = []
    monkeypatch.setattr(o, "kiyasla_072", lambda kok: cagrilar.append(("072", kok)))
    monkeypatch.setattr(o, "kiyasla_073", lambda kok: {"kart": "EDG-2026-073", "genel_gecerli": False})

    out = o.kiyasla(kart="EDG-2026-073", kok="duman")
    assert cagrilar == []                      # kiyasla_072 HİÇ ÇAĞRILMADI
    assert "olculemedi" in out["edg072"]
    import datetime as _dt
    bugun = _dt.date.today().isoformat()
    assert (tmp_path / f"sonuc_{bugun}_kuru_duman.json").exists()
    assert not (tmp_path / f"sonuc_{bugun}.json").exists()   # gerçek dosya adıyla ÇAKIŞMADI


# ---- (g) kill-2 (motor/bar özdeşliği) + yardımcı fonksiyonlar ---------------------

def test_adim0c_taze_esik_30_dogru_sayar():
    o = _olcum()
    islemler = [{"regime": "trend_up"}] * 35 + [{"regime": "chop"}] * 10
    r = o.adim0c_taze(islemler)
    assert r["trend_up"]["n"] == 35 and r["trend_up"]["olculebilir"] is True
    assert r["chop"]["n"] == 10 and r["chop"]["olculebilir"] is False
    assert r["trend_down"]["n"] == 0 and r["trend_down"]["olculebilir"] is False


def test_kill2_dogrudan_yol_kayitli_alan_varsa_post_hoc_ATLANIR():
    o = _olcum()
    K = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": {"birlesik_sha256": "AAA"}}}
    H1 = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": {"birlesik_sha256": "AAA"}}}
    r = o.kill2_motor_bar_073(K, H1, None, None)
    assert r["bar_onbellek"]["olcum_yontemi"].startswith("DOGRUDAN")
    assert r["gecti"] is True


def test_kill2_dogrudan_yol_bar_uyusmazligi_YAKALANIR():
    o = _olcum()
    K = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": {"birlesik_sha256": "AAA"}}}
    H1 = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": {"birlesik_sha256": "BBB"}}}
    r = o.kill2_motor_bar_073(K, H1, None, None)
    assert r["gecti"] is False and r["tetiklendi"] is True


def test_kill2_motor_farkliligi_YAKALANIR():
    o = _olcum()
    K = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": None}}
    H1 = {"sonuc": {"motor_sha256_16": {"a.py": "y"}, "bar_onbellek_ozet": None}}
    r = o.kill2_motor_bar_073(K, H1, None, None)
    assert r["motor"]["ayni"] is False
    assert r["tetiklendi"] is True


def test_kill2_post_hoc_yol_log_yoksa_olculemedi_BLOKLAMAZ():
    """log dosyası yok (kok=duman demo düzeni) → bar-zamanlaması ÖLÇÜLEMEZ, kayıt edilir ama
    tek başına kill'i tetiklemez (yalnız AÇIKÇA ölçülmüş bir uyuşmazlık bloklar — UYDURMA YASAĞI:
    ölçülemeyen None + neden, sessizce yeşile YUVARLANMAZ AMA sessizce KIRMIZIYA da yuvarlanmaz)."""
    o = _olcum()
    K = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": None}}
    H1 = {"sonuc": {"motor_sha256_16": {"a.py": "x"}, "bar_onbellek_ozet": None}}
    r = o.kill2_motor_bar_073(K, H1, None, pathlib.Path("/kesinlikle/yok/kosum_kontrol.log"))
    assert r["bar_onbellek"]["olcum_yontemi"].startswith("POST-HOC")
    assert r["bar_onbellek"]["kosum_baslangic_ts_utc"] is None
    assert r["bar_onbellek"]["en_yeni_bar_dosyasi_kosumdan_once_mi"] is None
    assert r["gecti"] is True      # None bloklamaz — yalnız motor uyuşmazlığı ya da AÇIK bar uyuşmazlığı bloklar


def test_log_baslangic_ts_ilk_gecerli_json_satirini_okur(tmp_path):
    o = _olcum()
    log = tmp_path / "x.log"
    log.write_text('\n{"ts": "2026-01-01T00:00:00+00:00", "x": 1}\n{"ts": "2026-01-02T00:00:00+00:00"}\n')
    assert o._log_baslangic_ts(log) == "2026-01-01T00:00:00+00:00"


def test_log_baslangic_ts_dosya_yoksa_None():
    o = _olcum()
    assert o._log_baslangic_ts(pathlib.Path("/kesinlikle/yok/olmayan.log")) is None


def test_bar_cache_ozet_icerik_degisince_birlesik_sha_DEGISIR(tmp_path):
    o = _olcum()
    d = tmp_path / "bars"
    d.mkdir()
    (d / "aaa.csv").write_text("a,b\n1,2\n")
    (d / "bbb.csv").write_text("a,b\n3,4\n")
    r1 = o._bar_cache_ozet(d)
    assert r1["n_dosya"] == 2

    (d / "aaa.csv").write_text("a,b\n1,3\n")     # tek bayt fark
    r2 = o._bar_cache_ozet(d)
    assert r2["birlesik_sha256"] != r1["birlesik_sha256"]
