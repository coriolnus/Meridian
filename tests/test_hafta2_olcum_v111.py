"""v111 — HAFTA 2 TURU, ölçüm tarafı (2026-07-29).

Kapsam: (B) bileşen IC'sine güven aralığı + cf katmanının karar girdisi olarak açılması;
(C) min_score eşik eğrisi; (D) kâr şelalesi.

Çivilenen üç cümle:
  1. **Aralıksız bir IC bir bulgu değildir.** n=95'te 0.15, n=2100'de 0.05 ile aynı kesinliğe sahip
     değildir; tabloyu aralıksız okumak, örneklem büyüklüğünü okurun kafasında taşımasını beklemektir.
  2. **cf katmanı bu tabloda sadakat kusurundan bağımsızdır** — çünkü y ekseni cf'in simüle ettiği
     çıkıştan (`r_multiple`) DEĞİL, barlardan gelir. Bu gerekçe yazılı olmazsa dar bir istisna
     sessizce genelleşir ve cf sayıları her yerde kanıt sayılmaya başlar.
  3. **Şelale bir ÖZDEŞLİKTİR, bir tahmin değil**: MFE + geri verilen − friksiyon, net'e EŞİT olmalı.
     Bacaklar farklı paydalardan toplanırsa tablo kendi kendine yalan söyler ve kimse fark etmez.
"""
from __future__ import annotations

import math

import pytest

from meridian import analytics, codelaw, component_ic, store, threshold_curve


# =================================================================================================
# B) BİLEŞEN IC — FISHER GÜVEN ARALIĞI
# =================================================================================================
def test_fisher_ci_ic_etrafinda_ve_n_buyudukce_DARALIR():
    """Aralığın iki temel özelliği: (1) tahmini KAPSAR, (2) örneklem büyüdükçe DARALIR. İkincisi
    olmadan aralık dekoratiftir — asıl işi "bu sayı ne kadar veriye dayanıyor?"u göstermektir."""
    lo_k, hi_k = component_ic._fisher_ci(0.15, 95)
    lo_b, hi_b = component_ic._fisher_ci(0.15, 2100)
    assert lo_k < 0.15 < hi_k, f"aralık tahmini kapsamıyor: [{lo_k},{hi_k}]"
    assert (hi_b - lo_b) < (hi_k - lo_k), "n 22 kat büyüdüğü hâlde aralık daralmadı"
    assert (hi_k - lo_k) > 0.3, "n=95'te aralık gerçekçi olmayacak kadar dar"


def test_fisher_ci_asla_birim_araligin_disina_TASMAZ():
    """Aralık z ölçeğinde kurulup tanh ile geri alınır; naif `ic ± 1.96*se` yaklaşımı yüksek IC'de
    1.0'ı aşar ve "korelasyon 1.08" gibi anlamsız bir sayı üretirdi."""
    for ic in (0.95, -0.95, 0.99):
        lo, hi = component_ic._fisher_ci(ic, 20)
        assert -1.0 <= lo <= 1.0 and -1.0 <= hi <= 1.0, f"ic={ic}: aralık [-1,1] dışında [{lo},{hi}]"


@pytest.mark.parametrize("n", [0, 3, None])
def test_fisher_ci_olculemeyen_n_icin_UYDURMAZ(n):
    """n<=3'te SE tanımsızdır (sqrt(n-3) sıfır ya da sanal). Uydurma yasağı: None döner."""
    assert component_ic._fisher_ci(0.5, n) == (None, None)


def test_hucre_anlamliligi_ARALIK_SIFIRI_DISLIYOR_MU_sorusudur(sandbox_state, monkeypatch):
    """`anlamli` bir eşik karşılaştırması değil, aralığın sıfırı dışarıda bırakıp bırakmadığıdır.
    Kurgu: aynı IC, iki farklı n → biri anlamsız, diğeri anlamlı."""
    lo1, hi1 = component_ic._fisher_ci(0.05, 100)
    lo2, hi2 = component_ic._fisher_ci(0.05, 5000)
    assert lo1 < 0 < hi1, "n=100'de IC 0.05 anlamlı çıkmamalıydı"
    assert lo2 > 0, "n=5000'de IC 0.05 hâlâ sıfırı kapsıyor — aralık daralmıyor"


def _mini_evren(monkeypatch, n_gun: int = 400):
    """Tek sembollü, deterministik bar evreni — bileşen IC'si gerçek yolundan koşsun diye."""
    import pandas as pd
    idx = pd.date_range("2024-01-01", periods=n_gun, freq="D")
    df = pd.DataFrame({"open": [100.0 + i * 0.1 for i in range(n_gun)],
                       "high": [100.5 + i * 0.1 for i in range(n_gun)],
                       "low": [99.5 + i * 0.1 for i in range(n_gun)],
                       "close": [100.0 + i * 0.1 for i in range(n_gun)],
                       "volume": [1_000_000 + (i % 7) * 10_000 for i in range(n_gun)]}, index=idx)
    monkeypatch.setattr(component_ic, "_load_universe", lambda: {"AAA": df})
    return idx


def test_cf_katman_gerekcesi_CIKTININ_ICINDE_yazili(sandbox_state, monkeypatch):
    """Gerekçe MAKİNE OKUNUR biçimde ÇIKTIYA girmeli: panoyu ya da beyni okuyan biri "cf sayıları
    neden burada kanıt sayılıyor?" sorusunu koda inmeden cevaplayabilmeli. Yalnız yorumda kalsaydı,
    kod değişince cümle olduğu yerde durur ve yanlışlığı hiçbir yerde görünmezdi.

    Bu test alanları GERÇEK bir koşunun çıktısında arar (kaynak metninde değil): bir alanı kodda
    yazıp çıktıya koymamak tam olarak gizlenmesi gereken hatadır."""
    idx = _mini_evren(monkeypatch)
    gunler = [str(d.date()) for d in idx[250:340]]
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i:05d}", "plan_id": f"P-{g}-AAA", "score": 60 + (i % 30),
         "r_multiple": 0.1 * ((i % 5) - 2)} for i, g in enumerate(gunler)])
    doc = component_ic.component_ic()
    assert doc is not None, "bileşen IC'si üretilmedi"
    for alan in ("cf_katman_gerekce", "ci_yontem", "ci_varsayim", "anlamli_sayim"):
        assert doc.get(alan), f"'{alan}' çıktıda yok — gerekçe/yöntem beyanı kaybolmuş"
    assert "BAR" in doc["cf_katman_gerekce"].upper(), doc["cf_katman_gerekce"]
    assert "kümelen" in doc["ci_varsayim"], "cf kümelenme uyarısı aralık varsayımında yok"
    modul = component_ic.__doc__ or ""
    assert "GİRİŞ ANI" in modul.upper() and "sadakat" in modul.lower(), \
        "cf katmanının bar-tabanlı gerekçesi modül başlığında yok"


def test_hucreler_ARALIK_ve_ANLAMLILIK_alanlarini_tasir(sandbox_state, monkeypatch):
    """Her ölçülebilen hücre aralığını yanında taşımalı; ölçülemeyen hücrede ikisi de None kalmalı
    (uydurma yasağı)."""
    idx = _mini_evren(monkeypatch)
    gunler = [str(d.date()) for d in idx[250:340]]
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i:05d}", "plan_id": f"P-{g}-AAA", "score": 70,
         "r_multiple": 0.1} for i, g in enumerate(gunler)])
    doc = component_ic.component_ic()
    for c in doc["components"]:
        for h in doc["horizons"]:
            cell = doc["tablo"]["gercek"][c][str(h)]
            if cell["ic"] is None:
                assert cell["ci"] is None and cell["anlamli"] is None, f"{c}@{h}: ölçülemedi ama aralık var"
            else:
                assert cell["ci"] and {"lo", "hi"} <= set(cell["ci"]), f"{c}@{h}: aralık yok"
                assert isinstance(cell["anlamli"], bool), f"{c}@{h}: anlamlılık bayrağı yok"


def test_pano_cf_satirlarini_SIM_etiketiyle_ayri_cizer():
    """Karar girdisi olması cf'i gerçek katmanla EŞİT yapmaz. Satırlar ayrı ve etiketli olmalı;
    aynı kefeye konsaydı okur 2100 satırlık simülasyonu 95 gerçek işlemle aynı ağırlıkta okurdu."""
    import pathlib
    src = pathlib.Path("meridian/web/app.js").read_text()
    assert 'satir("cf"' in src, "pano cf katmanını hiç çizmiyor"
    assert 'satir("gercek"' in src, "gerçek katman satırı kaybolmuş"
    assert src.index('satir("gercek"') < src.index('satir("cf"'), \
        "cf satırları gerçek katmandan ÖNCE geliyor — hüküm taşıyan katman altta kalıyor"
    assert '_chip("sim"' in src, "cf satırlarında 'sim' etiketi yok"


# =================================================================================================
# C) MIN_SCORE EŞİK EĞRİSİ
# =================================================================================================
def test_ort_ci_min_n_altinda_ORTALAMA_YAZMAZ():
    """Eğrinin sağ ucu doğası gereği en az veriye dayanır ve tam orada en ikna edici görünür.
    3 gözlemden ortalama R çıkarmak, eğriyi gürültüyle yukarı büken tam olarak o hatadır."""
    az = threshold_curve._ort_ci([0.5] * (threshold_curve.MIN_N - 1))
    assert az["ort"] is None and az["ci"] is None and "n<" in az["neden"], az
    yeter = threshold_curve._ort_ci([0.5, -0.2] * threshold_curve.MIN_N)
    assert yeter["ort"] is not None and yeter["ci"] is not None, yeter


def test_ort_ci_araligi_ortalamayi_KAPSAR_ve_n_ile_DARALIR():
    vals = [0.5, -0.3, 0.2, -0.1, 0.4, 0.0, -0.2, 0.3, 0.1, -0.4]
    dar = threshold_curve._ort_ci(vals * 10)
    genis = threshold_curve._ort_ci(vals)
    assert genis["ci"]["lo"] < genis["ort"] < genis["ci"]["hi"], genis
    assert (dar["ci"]["hi"] - dar["ci"]["lo"]) < (genis["ci"]["hi"] - genis["ci"]["lo"]), \
        "örneklem 10 kat büyüdüğü hâlde aralık daralmadı"


def test_esik_izgarasi_canli_esigin_ALTINDAN_baslar():
    """Yalnız yukarı bakan bir tarama, cevabı soruya gömer: eşiği DÜŞÜRMEK de bir seçenektir ve
    ızgara onu görebilmelidir."""
    assert min(threshold_curve.THRESHOLDS) < 60 <= max(threshold_curve.THRESHOLDS), \
        f"ızgara canlı eşiği (60) iki yandan çevrelemiyor: {threshold_curve.THRESHOLDS}"


def test_capraz_not_H2_REPLAY_CURUTMESINI_tasir(sandbox_state, monkeypatch):
    """SEÇİM ETKİSİ ≠ SİSTEM ETKİSİ. Bu eğri "eşiği yükselt" için bir davetiye gibi okunabilir;
    07-28'de tam replay bunu ÇÜRÜTTÜ (H2: 60→80, Δ-0.095). Uyarı sayının YANINDA durmalı."""
    monkeypatch.setattr(threshold_curve, "_gozlemler", lambda: ([], {"gercek": 0, "cf": 0}))
    assert threshold_curve.build() is None, "gözlem yokken boş tablo yazılmış"
    # Not metni koddaki sabittir; testin onu istemesi, bir gün sessizce silinmesini engeller.
    import inspect
    src = inspect.getsource(threshold_curve)
    assert "capraz_not" in src and "H2" in src and "replay" in src.lower(), \
        "çapraz not (H2 replay çürütmesi) kaybolmuş"


def test_esik_yukseldikce_aday_sayisi_ARTMAZ(sandbox_state, monkeypatch):
    """Monotonluk çivisi: eşik yükseldikçe geçen aday sayısı yalnız azalabilir. Artıyorsa süzgeç
    ters çevrilmiş demektir ve eğrinin tamamı anlamsızdır."""
    import pandas as pd
    gozlem = [("gercek", float(40 + (i % 55)), {5: 0.01, 10: 0.02, 20: 0.03}, 0.1)
              for i in range(200)]
    monkeypatch.setattr(threshold_curve, "_gozlemler",
                        lambda: ([("gercek", "AAA", "2025-01-02", g[1], g[3]) for g in gozlem],
                                 {"gercek": 200, "cf": 0}))
    df = pd.DataFrame({"close": [100.0 + i for i in range(400)]},
                      index=pd.date_range("2024-01-01", periods=400, freq="D"))
    monkeypatch.setattr(component_ic, "_load_universe", lambda: {"AAA": df})
    doc = threshold_curve.build()
    ns = [p["n_aday"] for p in doc["egri"]["gercek"]]
    assert ns == sorted(ns, reverse=True), f"eşik yükseldikçe aday sayısı artıyor: {ns}"


# =================================================================================================
# D) KÂR ŞELALESİ
# =================================================================================================
def _tr(i, r, mfe, costs=2.5, pnl=None, reason="stop"):
    """Canlı `trades.jsonl` şemasının şelale için gereken alanları (broker.close_position'dan
    doğrulandı): r_multiple NET, pnl_dollars NET, costs = kayma + çıkış komisyonu."""
    pnl = pnl if pnl is not None else r * 1000.0        # risk_dolar = 1000 → r = pnl/1000
    return {"id": f"T{i:05d}", "r_multiple": r, "mfe_r": mfe, "costs": costs,
            "pnl_dollars": pnl, "exit_reason": reason, "ts_open": "2025-01-02",
            "ts_close": "2025-01-06", "ticker": "AAA", "entry": 100.0, "qty": 10}


def test_selale_OZDESLIGI_tam_tutar(sandbox_state):
    """net_R = MFE_R + (brüt_R − MFE_R) − friksiyon_R. Bacaklar farklı paydalardan gelirse toplam
    net'i tutmaz ve tablo kendi kendine yalan söyler; artık alanı bunu görünür kılar."""
    store.write_jsonl("trades.jsonl", [_tr(i, r, mfe) for i, (r, mfe) in enumerate(
        [(-1.0, 0.5), (2.0, 2.5), (-0.5, 0.2), (1.2, 1.8), (-1.0, 0.9), (0.3, 1.1)])])
    w = analytics.profit_waterfall()
    assert w["ozdeslik_farki"] == pytest.approx(0.0, abs=1e-3), \
        f"şelale özdeşliği tutmuyor, artık={w['ozdeslik_farki']}"
    g = w["genel"]
    assert g["sinyal_mfe_r"] + g["geri_verilen_r"] - g["friksiyon_r"] == pytest.approx(g["net_r"], abs=1e-3)


def test_cikis_verimi_MFE_SIFIRIN_ALTINDA_ise_TANIMSIZ(sandbox_state):
    """Sinyal hiç lehte hareket sunmadıysa "tepenin ne kadarını aldık?" sorusunun PAYDASI yoktur.
    0 yazmak ya da 0'a bölmek, çıkış kuralını hiç suçu olmayan bir kayıptan sorumlu tutardı —
    kayıp GİRİŞ tarafındandır."""
    rows, _ = analytics._waterfall_rows([_tr(0, -1.0, 0.0), _tr(1, -1.0, -0.3), _tr(2, 0.5, 1.0)])
    assert rows[0]["cikis_verimi"] is None and rows[1]["cikis_verimi"] is None, \
        "MFE<=0 işlemde çıkış verimi uydurulmuş"
    assert rows[2]["cikis_verimi"] == pytest.approx(0.5, abs=1e-6)


def test_exit_reason_kirilimi_stop_ve_time_stop_AYRI_sayar(sandbox_state):
    """07-28 otopsisinin kalıcılaşması: kâr time_stop'tan geliyordu, stoplar kanatıyordu. Tek bir
    ortalama bu iki zıt gerçeği tek sayıya çökertir."""
    store.write_jsonl("trades.jsonl",
                      [_tr(i, -0.9, 0.7, reason="stop") for i in range(6)]
                      + [_tr(10 + i, 0.6, 1.2, reason="time_stop") for i in range(6)])
    w = analytics.profit_waterfall()
    assert set(w["exit_reason"]) == {"stop", "time_stop"}, w["exit_reason"].keys()
    assert w["exit_reason"]["stop"]["net_r"] < 0 < w["exit_reason"]["time_stop"]["net_r"], \
        "iki zıt çıkış rejimi aynı işarete çökmüş"


def test_selale_kucuk_defterde_URETMEZ(sandbox_state):
    """Dört işlemden "çıkış verimi %31" diye bir oran üretmek ölçüm değil süslemedir."""
    store.write_jsonl("trades.jsonl", [_tr(i, 0.5, 1.0) for i in range(analytics.WATERFALL_MIN_N - 1)])
    assert analytics.profit_waterfall() is None


def test_friksiyon_risk_dolara_bolunur_ve_r_SIFIRDA_uydurulmaz(sandbox_state):
    """risk_dolar defterde ALAN DEĞİLDİR; r_multiple = pnl_dollars / risk_dolar özdeşliğinden
    türetilir. r_multiple = 0 olan satırda bölme tanımsızdır → friksiyon None, ama satır ATILMAZ
    (MFE bacağı hâlâ ölçülebilir)."""
    rows, _ = analytics._waterfall_rows([_tr(0, 0.0, 0.4, pnl=0.0), _tr(1, 1.0, 1.5)])
    assert rows[0]["friksiyon_r"] is None and rows[0]["mfe_r"] == 0.4, rows[0]
    assert rows[1]["friksiyon_r"] == pytest.approx(2.5 / 1000.0, rel=1e-6), rows[1]


# =================================================================================================
# DIŞ TÜKETİCİ (YASA 6)
# =================================================================================================
@pytest.mark.parametrize("alan", ["threshold_curve", "profit_waterfall", "gerceklesen_r",
                                  "ileri_getiri", "geri_verilen_r", "toplam_verim",
                                  "cf_katman_gerekce", "ci_varsayim", "capraz_not"])
def test_pano_yeni_olcum_alanlarini_okuyor(alan):
    assert codelaw.dashboard_mentions(alan), f"pano '{alan}' alanını hiç okumuyor (YASA 6)"
