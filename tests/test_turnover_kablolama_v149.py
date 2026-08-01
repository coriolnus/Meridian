"""test_turnover_kablolama_v149.py — EDG-2026-016 TURNOVER: ÖLÇÜLMÜŞ YOLUN KABLOLANMASI (2026-08-01).

BU TURUN İDDİASI ŞU DEĞİL: "turnover skoru iyileştiriyor." Öyle bir iddia ancak kapıdan geçen bir
ölçümle kurulabilir ve kartın entegrasyon kararı onu bilerek ÖĞRENME DÖNGÜSÜNE bırakıyor (elle
ağırlık YOK). Bu turun iddiası üç cümledir ve üçü de burada çivilenir:

  1. ÖLÇÜLEN SERİ CANLI MOTORDA ÜRETİLİYOR — payda EDGAR'dan as-of okunuyor ve ölçüm turunun
     kurallarıyla (etiket/PIT/split/bayatlık/ölçek + fiziksel devir bekçisi) BİREBİR.
  2. CANLI DAVRANIŞ ZERRE DEĞİŞMEDİ — `entry.w_turnover` varsayılanı 0.0 iken bileşik skor,
     turnover terimi HİÇ YOKKENKİ formülün birebir aynısı.
  3. DÜĞME GERÇEKTEN BAĞLI — açıldığında skoru ölçülen YÖNDE oynatıyor, bounds.yaml'dan okunuyor
     ve kapı (guard) sınırlarını otomatik uyguluyor.

Ayrıca FAIL-OPEN sözleşmesi burada BEYAN EDİLİR VE SINANIR: turnover ölçülemeyen sembolde bileşen
terimi hiç eklenmez (pay da payda da dokunulmaz) — motor durmaz, skor kalan bileşenlerin ölçeğinde
kalır ve sebep sayacı defterlere düşer. Bu, komşu iki bileşenin ("ölçülemeyen ağırlıklı bileşen →
kurulum yok") kuralından BİLİNÇLİ bir sapmadır; gerekçesi `strategy.evaluate_entry` turnover
bloğunda yazılıdır ve bu dosya o sapmanın gerçekten fail-OPEN olduğunu (fail-CLOSED değil) ölçer.
"""
from __future__ import annotations

import inspect
import pathlib

import numpy as np
import pandas as pd
import pytest

from meridian import component_ic as cic, config, guard, indicators as ind, strategy as strat
from meridian.adapters import edgar_shares as es
from tests.test_learning_roundtrip_v76 import staircase_bars

REPO = pathlib.Path(__file__).resolve().parent.parent

# Kapıları gevşetilmiş param seti (test_score_rebuild_v115 ile aynı gerekçe): bu dosyanın sorusu
# "kaç sinyal geçiyor" değil "geçen sinyalin SKORU değişti mi".
LOOSE = {"entry.pivot_proximity_pct": 8.0, "entry.min_volume_ratio": 1.0, "entry.min_score": 40}

# ÖLÇÜMÜN YAYIMLADIĞI MUHASEBE (wp2_olcum/sonuc_016.json → hisse_muhasebesi). Canlı köprü aynı
# dosyayı aynı kurallarla okuyorsa bu sayıları BİREBİR üretmek zorundadır; üretmiyorsa "ölçümle
# aynı payda" cümlesi bir niyet beyanıdır, kanıt değil.
OLCUM_MUHASEBESI = {"ham_satir": 161856, "birim_veya_val_dusen": 76,
                    "anlik_iki_etiket_satir": 32954, "birincil_dei": 244, "birincil_usgaap": 8}
OLCUM_YEDEK_ETIKET = 22


def _ilk_sinyal(df: pd.DataFrame, params: dict, rs: int = 85, ticker: str = "T"):
    for i in range(400, len(df)):
        sub = df.iloc[:i + 1].reset_index(drop=True)
        sig = strat.evaluate_entry(sub, params, rs, ticker)
        if sig is not None:
            return sub, sig
    return None, None


@pytest.fixture()
def temiz_kopru():
    """Köprünün süreç-içi önbelleğini/sayaçlarını testler arasında yalıtır."""
    es._sifirla()
    yield es
    es._sifirla()


# =================================================================================================
# A) VERİ KÖPRÜSÜ — as-of kuralları ÖLÇÜMLE BİREBİR
# =================================================================================================
@pytest.mark.skipif(not es.SHARES_FILE.exists(), reason="research/edgar_facts yok (veri dosyası)")
def test_a1_kurallar_olcumle_BIREBIR_muhasebe(temiz_kopru):
    """ÇİVİ: canlı köprünün yükleme muhasebesi, ölçüm turunun yayımladığı sayıların AYNISI.

    Beş sayı beş ayrı kuralı temsil eder: kaç ham satır okundu (dosyanın kendisi), birim/val
    filtresi kaç satır düşürdü, anlık İKİ etikette kaç satır kaldı, kaç sembolde birincil dei ve
    kaç sembolde us-gaap seçildi. Biri bile kayarsa canlı payda ile ölçülen payda AYNI SERİ
    DEĞİLDİR ve EDG-016'nın kanıtı canlıda geçerli olmaktan çıkar."""
    es._tablolar()
    for k, beklenen in OLCUM_MUHASEBESI.items():
        assert es._YUKLEME.get(k) == beklenen, f"{k}: canlı köprü {es._YUKLEME.get(k)}, ölçüm {beklenen}"
    for sym in sorted(es._tablolar()["birincil"]):
        es._seri(sym)
    assert es._YUKLEME.get("yedek_etiket_eklenen_kayit") == OLCUM_YEDEK_ETIKET


@pytest.mark.skipif(not es.SHARES_FILE.exists(), reason="research/edgar_facts yok (veri dosyası)")
def test_a2_split_GUNCEL_BAZA_cevrilir_ve_PIT_korunur(temiz_kopru):
    """Bölünme dönüşümü olmadan oran 4×/20× yanlış olurdu; PIT olmadan gelecek sızardı.

    GOOGL 20:1 (2022-07) ve AAPL 4:1 (2020-08) bölünmeleri: bölünmeden ÖNCEKİ bir tarihte okunan
    değer, o günün ham beyanı DEĞİL güncel bazdaki karşılığıdır (bar hacmi de güncel bazda
    split-düzeltilmiş olduğu için oran ancak böyle bölünmeden bağımsız olur). Serinin ilk
    dosyalamasından ÖNCE hiçbir değer yoktur — uydurulmaz, `dosyalama_yok` döner."""
    googl, neden = es.as_of_shares_detay("GOOGL", "2022-04-28")
    assert neden == "" and googl is not None
    assert 12e9 < googl < 14e9, f"GOOGL güncel baza çevrilmemiş görünüyor: {googl}"
    aapl = es.as_of_shares("AAPL", "2019-01-02")
    assert aapl is not None and 17e9 < aapl < 20e9, f"AAPL güncel baza çevrilmemiş: {aapl}"
    # 2000 yılında bu dosyada hiçbir dosyalama yok (EDGAR XBRL 2009'da başlar) → ölçülemedi.
    v, neden = es.as_of_shares_detay("AAPL", "2000-01-03")
    assert v is None and neden == es.NEDEN_DOSYALAMA_YOK


@pytest.mark.skipif(not es.SHARES_FILE.exists(), reason="research/edgar_facts yok (veri dosyası)")
def test_a3_bayatlik_bekcisi_200g_gercekten_isliyor(temiz_kopru):
    """200 günden eski bir dosyalamadan as-of değer ÜRETİLMEZ (None + `bayat_seri`).

    Ölçüm bu bekçinin 27 sembolde işlediğini raporluyor (SCHW 1006, V 4007, NKE 2934 hücre...).
    Bekçi canlı köprüde de duruyorsa aynı sembollerde bayat hücreler görünmelidir."""
    gunler = pd.date_range("2010-01-04", "2026-07-28", freq="21D").strftime("%Y-%m-%d").tolist()
    _v, neden = es.as_of_shares_series("V", gunler)
    assert (neden == es.NEDEN_BAYAT).any(), "bayatlık bekçisi hiç işlemedi — 200g kuralı kayıp"


def test_a4_FAIL_OPEN_dosya_yoksa_None_ve_SEBEP_ADIYLA(temiz_kopru, sandbox_state, monkeypatch):
    """Dosya yoksa köprü SESSİZCE boş dönmez: None + neden + sayaç + olay.

    Bu, fail-open sözleşmesinin ilk yarısıdır. İkinci yarısı (skorun bozulmaması) D bölümünde."""
    monkeypatch.setattr(es, "SHARES_FILE", sandbox_state / "olmayan_dosya.csv.gz")
    es._sifirla()
    v, neden = es.as_of_shares_detay("AAPL", "2024-06-03")
    assert v is None and neden == es.NEDEN_DOSYA_YOK
    r = es.okuma_raporu()
    assert r["cagri"] == 1 and r["olculemedi"] == 1 and r["oran_olculdu"] == 0.0
    assert r["neden"].get(es.NEDEN_DOSYA_YOK) == 1
    assert r["yukleme"].get("durum") == es.NEDEN_DOSYA_YOK


def test_a5_kapsam_disi_sembol_SAYILIR_ADIYLA_ama_DEFTERE_YAZILMAZ(temiz_kopru, capsys):
    """EDGAR kapsamında olmayan sembol → None + `anlik_hisse_serisi_yok` + ADIYLA sayaç; olay YOK.

    İKİ ŞEYİ BİRDEN ÇİVİLER. (1) Ölçülemezlik sessiz değildir: sebep kodu, sayaç ve SEMBOL ADI
    raporda durur. (2) Skor yolu DEFTERE YAZMAZ: `obs.warn` bir `store.append_jsonl` çağrısıdır ve
    bu fonksiyon sembol döngüsünün içinden çağrılır — sembol başına uyarı, saf skor hesabını canlı
    `events.jsonl`a yazan bir G/Ç yoluna çevirirdi. Bu test BİLEREK `sandbox_state` ALMAZ: kod
    uyarmaya dönerse conftest'in canlı-state sızıntı bekçisi de kırmızıya döner (çift bekçi)."""
    if not es.SHARES_FILE.exists():
        pytest.skip("research/edgar_facts yok (veri dosyası)")
    v, neden = es.as_of_shares_detay("YOKBOYLEBIRSEY", "2024-06-03")
    assert v is None and neden == es.NEDEN_SERI_YOK
    r = es.okuma_raporu()
    assert r["neden"].get(es.NEDEN_SERI_YOK) == 1
    assert "YOKBOYLEBIRSEY" in r["kapsam_disi_sembol"], "kapsam dışı sembol ADIYLA raporlanmıyor"
    assert "edgar_shares" not in capsys.readouterr().out, \
        "skor yolu olay yazdı — sembol başına defter yazımı (bkz. as_of_shares_series gerekçesi)"


def test_a7_SCHW_bayat_hucre_sayisi_OLCUMLE_BIREBIR(temiz_kopru, sandbox_state):
    """EN SERT ÇİVİ: gerçek bar takviminde SCHW'nin bayat hücre sayısı ölçümün yayımladığı sayının
    TA KENDİSİ (1006). Bu tek sayı zincirin TAMAMINI sınar — etiket seçimi, yedek etiket doldurma,
    bölünme takvimi, 200g bayatlık bekçisi ve as-of arama; biri kayarsa sayı da kayar.

    Kaynak: wp2_olcum/sonuc_016.json → panel_muhasebesi.bayat_seri_sembol.SCHW = 1006.
    Bar önbelleği yoksa atlanır (ölçüm bar tabanına çapalıdır; test yalnız SALT-OKUNUR okur).

    BAR YOLU CANLI DİZİNDEN, DOĞRUDAN: `sandbox_state` `config.BARS`ı tmp'ye çevirir (yazımlar —
    ör. `sanitize_bars`ın hayalet-seans uyarısı — canlı deftere düşmesin diye ve bu doğrudur), ama
    ölçümün çapalandığı BAR TABANI canlı önbellektedir. `_cache_path` kullanılsaydı test sessizce
    ATLANIR ve "en sert çivi" hiç çakılmamış olurdu — geçen ama hiçbir şey ölçmeyen bir test."""
    cp = REPO / "state" / "bars" / "schw.csv"
    if not es.SHARES_FILE.exists() or not cp.exists():
        pytest.skip("EDGAR dosyası ya da SCHW bar önbelleği yok")
    from meridian.adapters import data as dat
    df, _ = dat.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), "SCHW")
    df = df.set_index("date").sort_index()
    _v, neden = es.as_of_shares_series("SCHW", [d.strftime("%Y-%m-%d") for d in df.index])
    assert int((neden == es.NEDEN_BAYAT).sum()) == 1006


def test_a6_kopru_SALT_OKUNUR(temiz_kopru):
    """Köprüde yazım yolu YOKTUR: ne EDGAR dosyasına ne state'e. Kaynak sınanır çünkü bir yazım
    çağrısı buraya eklendiği gün canlı worker'la yarışır (state'e iki süreçten yazım yasağı)."""
    kaynak = inspect.getsource(es)
    for yasak in ("write_json", "append_jsonl", "write_text", "to_csv", "open(", "os.replace"):
        assert yasak not in kaynak, f"köprüde yazım izi: {yasak}"


# =================================================================================================
# B) GÖSTERGE + FİZİKSEL DEVİR BEKÇİSİ
# =================================================================================================
def test_b1_turnover21_tanimi_ve_isinmasi():
    """turnover21 = medyan21(hacim)/hisse; pencere dolmadan NaN (yarım pencereyle "medyan" yok)."""
    vol = pd.Series(np.arange(1, 41, dtype=float) * 1_000_000)
    to = ind.turnover21(vol, 2_000_000_000.0)
    assert to.iloc[:20].isna().all(), "21 bar dolmadan devir hesaplanmış — uydurma"
    med = float(np.median(vol.iloc[0:21]))
    assert to.iloc[20] == pytest.approx(med / 2_000_000_000.0)
    assert ind.med_volume21(vol).first_valid_index() == ind.TURNOVER_WINDOW - 1


def test_b2_FIZIKSEL_BEKCI_devir_birden_buyukse_None():
    """Devir > 1 FİZİKSEL OLARAK İMKÂNSIZDIR (medyan günlük hacim tüm dolaşımı geçemez) → NaN.

    Kaynağı ölçülmüş kabuk-sayısı vakalarıdır (CSX 3 hisse, ETN 100, SPG 8.000...); bekçi olmadan
    o kayıtlar deviri 10⁴ katına çıkarıyordu. Bu bir sinyal eşiği DEĞİL veri kalitesi kuralıdır."""
    vol = pd.Series([1_000_000.0] * 30)
    assert ind.turnover21(vol, 5_000_000.0).iloc[-1] == pytest.approx(0.2)      # normal
    assert pd.isna(ind.turnover21(vol, 500_000.0).iloc[-1])                     # devir 2.0 → None
    assert pd.isna(ind.turnover21(vol, 0.0).iloc[-1])                           # sıfır hisse → None
    assert bool(ind.turnover21(vol, None).isna().all())                         # payda yok → None
    assert ind.TURNOVER_FIZIKSEL_TAVAN == 1.0


# =================================================================================================
# C) SKOR ŞEKLİ — ölçülmüş yüzdeliklere çapalı, MONOTON, ekstrapolasyonsuz
# =================================================================================================
def test_c1_capalar_OLCUMUN_dagilimi_ve_monotonluk():
    """Çapa noktaları ölçümün havuzlanmış dağılımıdır (sonuc_016 turnover21_dagilimi) ve dönüşüm
    MONOTONdur — kanıtın taşıdığı tek şey (sıralama/tekdüze monotonluk) korunur."""
    for ham, puan in strat.TURNOVER_PCTL_CAPA:
        assert strat.turnover_score(ham) == pytest.approx(puan)
    x = np.geomspace(1e-4, 1.0, 200)
    p = [strat.turnover_score(v) for v in x]
    assert all(b >= a for a, b in zip(p, p[1:])), "dönüşüm monoton değil — kanıtın yönü kayboldu"


def test_c2_EKSTRAPOLASYON_YOK_ve_olculemeyen_girdi_None():
    """Ölçülmemiş bölgede eğri uydurulmaz: p01 altı 1, p99 üstü 99'da sabitlenir."""
    assert strat.turnover_score(1e-9) == pytest.approx(1.0)
    assert strat.turnover_score(0.99) == pytest.approx(99.0)
    for kotu in (None, float("nan"), 0.0, -0.01):
        assert strat.turnover_score(kotu) is None


# =================================================================================================
# D) SIFIR-ETKİ ÇİVİSİ + FAIL-OPEN — TURUN ASIL İDDİASI
# =================================================================================================
def _turnoversuz_skor(df: pd.DataFrame, params: dict, rs: int) -> int:
    """TURNOVER ÖNCESİ bileşik skor, satır satır (strategy.py 2026-08-01 öncesi hâli).

    Referansı testin içinde YENİDEN YAZMAK bilinçli (test_score_rebuild_v115'in B bölümüyle aynı
    gerekçe): üretim koduna bakıp "sıfır ekledik, değişmez" demek muhakemedir, ölçüm değil."""
    piv = float(ind.pivot_high(df["high"], strat.PIVOT_LOOKBACK, exclude_recent=1).iloc[-1])
    c = float(df["close"].iloc[-1])
    vr = float(ind.volume_ratio(df["volume"], 50).iloc[-1])
    tt = float(ind.trend_template(df).iloc[-1])
    prox_max = float(params.get("entry.pivot_proximity_pct", 2.0))
    prox_pct = (c - piv) / piv * 100.0
    prox_score = 100.0 * (1.0 - min(prox_pct / prox_max, 1.0)) if prox_max > 0 else 0.0
    vol_score = 100.0 * min(vr / 3.0, 1.0)
    w_rs = float(params.get("entry.w_rs", 0.35)); w_tt = float(params.get("entry.w_tight", 0.30))
    w_vol = float(params.get("entry.w_vol", 0.20)); w_px = float(params.get("entry.w_prox", 0.15))
    return int(round((w_rs * rs + w_tt * (tt * 100.0) + w_vol * vol_score + w_px * prox_score)
                     / max(w_rs + w_tt + w_vol + w_px, 1e-9)))


def test_d1_YIRMI_sembolde_skor_TURNOVER_ONCESIYLE_BIREBIR(temiz_kopru, sandbox_state):
    """ÇİVİ: `entry.w_turnover` varsayılan 0.0 iken her sinyalin skoru turnover öncesinin aynısı."""
    olculen = 0
    for seed in range(20):
        df = staircase_bars(n=600, seed=seed)
        sub, sig = _ilk_sinyal(df, LOOSE, rs=85, ticker=f"S{seed}")
        if sig is None:
            continue
        olculen += 1
        assert sig.score == _turnoversuz_skor(sub, LOOSE, 85), \
            f"seed={seed}: skor turnover öncesinden SAPTI ({sig.score})"
    assert olculen >= 15, f"20 sembolün yalnız {olculen}'inde sinyal doğdu — çivi örneklemsiz kaldı"


def test_d2_dugme_YOKKEN_ve_ACIKCA_SIFIRKEN_ayni(temiz_kopru, sandbox_state):
    """"Varsayılan kapalı" ile "sıfıra ayarlı" İKİ FARKLI davranış olamaz — defter satırı dahil."""
    sub, taban = _ilk_sinyal(staircase_bars(n=600, seed=1), LOOSE, 85)
    assert taban is not None
    acik = strat.evaluate_entry(sub, {**LOOSE, "entry.w_turnover": 0.0}, 85, "T")
    assert acik is not None and acik.as_row() == taban.as_row()


def test_d3_dugme_ACILINCA_skor_OLCULEN_YONDE_oynar(temiz_kopru, sandbox_state, monkeypatch):
    """Sıfır-etki çivisi ancak düğme AÇIKKEN etkiliyse anlamlıdır. Yön ölçümden gelir: q5 tekdüze
    MONOTON (yüksek devir → yüksek fazla getiri), yani yüksek devir skoru YUKARI çekmeli."""
    sub, taban = _ilk_sinyal(staircase_bars(n=600, seed=1), LOOSE, 85)
    assert taban is not None
    # Payda monkeypatch'lenir: sentetik seride EDGAR karşılığı yoktur ve olmamalıdır (uydurma yok).
    monkeypatch.setattr(es, "as_of_shares_detay", lambda t, d: (5e7, ""))       # yüksek devir
    yuksek = strat.evaluate_entry(sub, {**LOOSE, "entry.w_turnover": 0.40}, 85, "T")
    monkeypatch.setattr(es, "as_of_shares_detay", lambda t, d: (5e10, ""))      # düşük devir
    dusuk = strat.evaluate_entry(sub, {**LOOSE, "entry.w_turnover": 0.40}, 85, "T")
    assert yuksek is not None and dusuk is not None
    assert yuksek.turnover21 is not None and yuksek.turnover21 > dusuk.turnover21
    assert yuksek.score > dusuk.score, "düğme açıkken devir skoru oynatmıyor — kablo bağlı değil"
    assert {yuksek.score, dusuk.score} != {taban.score}, "açık düğme tabanla aynı skoru veriyor"


def test_d4_FAIL_OPEN_olculemeyen_devir_KURULUMU_OLDURMEZ(temiz_kopru, sandbox_state, monkeypatch):
    """SÖZLEŞME: ağırlık AÇIKKEN bile ölçülemeyen turnover terimi HİÇ EKLENMEZ — skor taban skorun
    BİREBİR aynısı kalır ve sinyal ölmez.

    Bu, komşu iki bileşenin kuralından (ölçülemeyen ağırlıklı bileşen → kurulum yok) bilinçli
    sapmadır: turnover'ın paydası DIŞ ve statik bir dosyadır; yokluğu bir piyasa olgusu değil altyapı
    olgusudur ve "veri kesintisi → işlem durdu" bağlantısını kimse seçmedi. Test hem ölmediğini hem
    de paydaya sızıp skoru SULANDIRMADIĞINI (w'nin bölene eklenmediğini) ölçer."""
    sub, taban = _ilk_sinyal(staircase_bars(n=600, seed=1), LOOSE, 85)
    assert taban is not None
    monkeypatch.setattr(es, "as_of_shares_detay", lambda t, d: (None, es.NEDEN_BAYAT))
    s = strat.evaluate_entry(sub, {**LOOSE, "entry.w_turnover": 0.40}, 85, "T")
    assert s is not None, "ölçülemeyen turnover kurulumu ÖLDÜRDÜ — fail-open değil fail-closed"
    assert s.score == taban.score and s.turnover21 is None
    # Fiziksel bekçi de aynı yolu kullanır: devir>1 → ölçülemedi → terim eklenmez, sinyal yaşar.
    monkeypatch.setattr(es, "as_of_shares_detay", lambda t, d: (1000.0, ""))
    fz = strat.evaluate_entry(sub, {**LOOSE, "entry.w_turnover": 0.40}, 85, "T")
    assert fz is not None and fz.score == taban.score and fz.turnover21 is None
    assert strat._turnover_now(sub, "T")[1] == "fiziksel_bekci_veya_isinma"


def test_d5_tarihsiz_cerceve_UYDURMAZ(temiz_kopru, sandbox_state):
    """As-of okuma tarihsiz yapılamaz; "bugünü" varsaymak (duvar saati) §4 ihlali olurdu."""
    df = staircase_bars(n=600, seed=1).drop(columns=["date"])
    assert strat._turnover_now(df, "AAPL") == (None, "tarih_yok")


def test_d6_defterde_ALAN_var_metinde_YOK(temiz_kopru, sandbox_state, monkeypatch):
    """Bileşen değeri `notes` METNİNE değil ALAN olarak yazılır (component_ic'in 1. tasarım
    kararında teşhis edilen hatanın tekrarlanmadığının kanıtı) ve ölçülemediğinde None kalır."""
    sub, _ = _ilk_sinyal(staircase_bars(n=600, seed=1), LOOSE, 85)
    monkeypatch.setattr(es, "as_of_shares_detay", lambda t, d: (5e7, ""))
    sig = strat.evaluate_entry(sub, LOOSE, 85, "T")
    satir = sig.as_row()
    assert "turnover21" in satir and satir["turnover21"] is not None
    assert "turnover" not in sig.notes


# =================================================================================================
# E) BOUNDS + GUARD — düğme arama uzayında ve kapı sınırları OTOMATİK okuyor
# =================================================================================================
def test_e1_bounds_satiri_okunuyor_ve_eskiler_DEGISMEDI():
    b = config.bounds()
    assert b["entry.w_turnover"] == {"min": 0.00, "max": 0.40, "step": 0.05, "type": "float"}
    # Mevcut satırlar korunmalı: EKLEME yapıldı, düzenleme değil.
    for eski in ("entry.w_rs", "entry.w_tight", "entry.w_vol", "entry.w_prox",
                 "entry.w_rvolband", "entry.w_mom", "entry.min_rvol"):
        assert eski in b
    assert b["entry.w_rvolband"] == {"min": 0.00, "max": 0.40, "step": 0.05, "type": "float"}


def test_e2_guard_sinirlari_OTOMATIK_uyguluyor(sandbox_state):
    """Kapı bounds'u GENEL olarak okur — yeni satır için guard'a EK KOD yazılmadı; bu test o
    iddianın kendisidir. Aralık dışı / adım dışı / no-op öneriler reddedilmeli."""
    b, goal = config.bounds(), config.goal()
    cur = {"entry.w_turnover": 0.0}

    def _hukum(deger):
        return guard.validate_change({"variable": "entry.w_turnover", "new": deger},
                                     cur, b, goal, [], 0)

    assert _hukum(0.05).ok, _hukum(0.05).reasons
    assert _hukum(0.40).ok, "aralığın üst ucu reddedildi"
    for kotu in (0.45, 0.07, -0.05):
        assert not _hukum(kotu).ok, f"{kotu} kabul edildi — bounds sınırı uygulanmıyor"
    assert not _hukum(0.0).ok, "no-op (mevcut değerin aynısı) kabul edildi"


# =================================================================================================
# F) ÜRETİM YOLU — gecelik tablo yeni bileşeni KENDİLİĞİNDEN kapsıyor (yazım YOK, yol kanıtı)
# =================================================================================================
def test_f1_component_ic_bileseni_ve_agirlik_esleme():
    assert "turnover21" in cic.COMPONENTS
    assert cic.COMPONENT_WEIGHT_KEY["turnover21"] == "entry.w_turnover"
    assert cic.COMPONENT_WEIGHT_DEFAULT["turnover21"] == 0.0
    assert cic.COMPONENT_WEIGHT_KEY["turnover21"] in config.bounds()


@pytest.mark.skipif(not es.SHARES_FILE.exists(), reason="research/edgar_facts yok (veri dosyası)")
def test_f2_component_frame_GERCEK_sembolde_turnover_uretiyor(temiz_kopru, sandbox_state):
    """Üretim çerçevesi (gecelik P5'in kurduğu çerçevenin ta kendisi) turnover sütununu DOLDURUYOR.

    Ticker verilmezse sütun tamamen NaN'dır — sıfır DEĞİL: as-of okuma sembole çapalıdır ve
    sembolsüz bir devir uydurmak yasaktır."""
    df = staircase_bars(n=600, seed=3)
    df = df.set_index("date").sort_index()
    frame = cic._component_frame(df, 2.0, None, ticker="AAPL")
    assert "turnover21" in frame.columns
    to = frame["turnover21"].dropna()
    assert len(to) > 100, "gerçek sembolde turnover hücreleri dolmadı — üretim yolu kapsamıyor"
    assert bool(((to > 0) & (to <= ind.TURNOVER_FIZIKSEL_TAVAN)).all())
    bos = cic._component_frame(df, 2.0, None, ticker=None)
    assert bool(bos["turnover21"].isna().all())


def test_f3_uretim_cagrisi_TICKER_geciriyor_ve_gecelik_dongude():
    """YOL KANITI: `component_ic()` çerçeveyi sembol adıyla kuruyor ve gecelik döngü onu çağırıyor.
    Bu iki satır kırılırsa turnover satırı sessizce "n=0" olarak yaşar ve kimse fark etmez."""
    from meridian import loop
    assert "_component_frame(per[t], prox_max, index_close, ticker=t)" in \
        inspect.getsource(cic.component_ic)
    assert "_cic.component_ic()" in inspect.getsource(loop.daily_cycle)


def test_f4_payda_sayaci_GECELIK_OLAYA_ve_deftere_dusuyor(temiz_kopru):
    """YASA 6 — üretilen sayaç TÜKETİLİR: `component_ic.json` → `turnover_kaynak` alanı ve gecelik
    `component_ic` olayının üç alanı. Fail-open beyanının görünür yüzü budur."""
    r = cic._turnover_kaynak()
    for alan in ("cagri", "olculdu", "olculemedi", "neden", "oran_olculdu", "en_sik_neden",
                 "kapsam_disi_sembol", "beyan"):
        assert alan in r, f"payda sayacında eksik alan: {alan}"
    kaynak = inspect.getsource(cic.component_ic)
    assert '"turnover_kaynak": _turnover_kaynak()' in kaynak
    for alan in ("turnover_payda_olculdu", "turnover_payda_olculemedi", "turnover_payda_en_sik_neden"):
        assert alan in kaynak, f"gecelik olayda eksik sayaç alanı: {alan}"


def test_f5_olcek_beyani_CIKTININ_ICINDE():
    """Panoyu/beyni okuyan biri "bu satır ham oran mı, skora giren puan mı?" sorusunu koda inmeden
    cevaplayabilmeli — yeni bileşenin beyanı `yeni_bilesen_notu` metnine girdi."""
    kaynak = inspect.getsource(cic.component_ic)
    assert "turnover21 (EDG-016) HAM oran olarak ölçülür" in kaynak
    assert "MONOTON" in kaynak


def test_f6_kart_hukmu_ve_kanit_referansi_KODDA():
    """Kanıtsız knob olmaz: bounds satırı ve skor şekli kart numarasını ve ölçüm çıktısını ADIYLA
    taşımalı (ileride "bu 0.05 nereden geldi?" sorusu tahminle cevaplanmasın)."""
    bounds_metni = (REPO / "state" / "bounds.yaml").read_text(encoding="utf-8")
    assert "EDG-2026-016" in bounds_metni and "entry.w_turnover" in bounds_metni
    assert "sonuc_016.json" in bounds_metni
    kaynak = inspect.getsource(strat)
    assert "sonuc_016.json" in kaynak and "kesit_muhasebesi.turnover21_dagilimi" in kaynak
