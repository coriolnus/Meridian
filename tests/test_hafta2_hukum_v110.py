"""v110 — HAFTA 2 TURU, hüküm tarafı (2026-07-29).

Kapsam: (A) EDGE hükmüne ANLAMLILIK katı — dördüncü durum `ZAYIF`; (E) maruziyet-düzeltilmiş SPY
farkı ve onun hükme bağlanması.

Bu dosyanın çivilediği cümle: **eşiği geçmek ile gürültüden ayrılmak AYNI ŞEY DEĞİLDİR.**
2026-07-29 sabahı kuzey yıldızının 1. ölçütü "SAGLANDI" yanıyordu (IC 0.0492 > eşik 0.03) ve aynı
payload iki alan ötede `anlamli: False` diyordu — yani kartın en pahalı kararlara dayanak olan
kelimesi, ölçülmemiş bir kesinlik taşıyordu. Aynı gün 2. ölçüt SPY'ı HAM farkla kıyaslıyordu:
sermayesinin %6'sını taşıyan bir stratejiden, tam maruziyetli bir SPY tutucusunun getirisi
çıkarılıyordu.

İkinci çivi: ZAYIF yalnız ANLAMLILIK HESABI OLAN ölçütlere uygulanır. Hesabı olmayana "anlamlı
değil" damgası basmak, yapılmamış bir testin sonucunu uydurmaktır (UYDURMA YASAĞI).
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import analytics, codelaw, store


# =================================================================================================
# A) DURUM MATRİSİ — (eşik, anlamlılık) → durum
# =================================================================================================
@pytest.mark.parametrize("esik_gecti,anlamli,beklenen", [
    (True, True, "gecti"),        # ikisi de sağlandı → tek SAGLANDI hâli
    (True, False, "zayif"),       # eşik geçti, gürültüden ayrılmadı → ZAYIF (yeni durum)
    (True, None, "olculemedi"),   # anlamlılık ÖLÇÜLEMEDİ → hüküm tamamlanamaz (uydurma yok)
    (False, True, "kaldi"),       # eşik geçilmedi: anlamlılık durumu değiştirmez
    (False, False, "kaldi"),
    (False, None, "kaldi"),
])
def test_durum_matrisi_esik_ve_anlamliligi_BIRLIKTE_ister(esik_gecti, anlamli, beklenen):
    """SAGLANDI artık İKİSİNİ birden ister. `True/None` satırı özellikle önemli: eşiği geçmiş bir
    değeri "sağlandı" saymak anlamlılığı VARSAYMAK, "zayıf" saymak ise yapılmamış bir testin
    olumsuz sonucunu UYDURMAK olurdu — ikisi de yasak, cevap `olculemedi`."""
    assert analytics._durum_anlamlilikla(esik_gecti, anlamli) == beklenen


def test_ZAYIF_durum_adi_sozlukte_ve_dordu_de_ayri_isimli():
    """`EDGE_DURUM_ADI` makine değeri ile insan dilini TEK yerde eşler. Dört durumun dördü de ayrı
    bir isim taşımalı: ikisi aynı ada eşlenirse pano iki farklı hükmü aynı renge boyar."""
    d = analytics.EDGE_DURUM_ADI
    assert d["zayif"] == "ZAYIF", "ZAYIF durum adı sözlükte yok"
    assert set(d) == {"gecti", "kaldi", "olculemedi", "zayif"}, f"durum kümesi değişmiş: {set(d)}"
    assert len(set(d.values())) == 4, "iki durum aynı insan-diline eşleniyor"


def _cal_yaz(ic: float, n: int, anlamli: bool | None) -> None:
    """`score_calibration.json`ın GERÇEK şeması (katmanlar.gercek) — hüküm bunu okur."""
    store.write_json("score_calibration.json", {
        "n": n, "n_real": n, "n_cf": 0, "rank_ic": ic,
        "katmanlar": {"gercek": {"rank_ic": ic, "n": n, "anlamli": anlamli},
                      "cf": None, "havuz": {"rank_ic": ic, "n": n, "anlamli": None}},
        "real": {"rank_ic": ic, "n": n, "anlamli": anlamli}, "cf": None})


def test_esik_ustu_ama_anlamsiz_IC_SAGLANDI_YAZMAZ(sandbox_state):
    """CANLI VAKANIN ÇİVİSİ: IC 0.0492, eşik 0.03, n=95, anlamli=False. Eski yasa "SAGLANDI" derdi."""
    _cal_yaz(0.0492, 95, False)
    ev = analytics.edge_verdict()
    skor = ev["criteria"]["skor_sonuc"]
    assert skor["status"] == "zayif" and skor["durum"] == "ZAYIF", \
        f"eşik üstü ama anlamsız IC hâlâ SAGLANDI sayılıyor: {skor}"
    assert ev["passed"] == 0, "ZAYIF bir ölçüt paya girmiş — `passed` yalnız eşik+anlamlılık sayar"
    assert ev["zayif"] >= 1, "zayıf sayacı hükümde yok"
    assert "zayıf" in ev["verdict"], f"hüküm cümlesi zayıfı saymıyor: {ev['verdict']}"


def test_anlamli_IC_SAGLANDI_yazar(sandbox_state):
    """Karşı kutup: aynı eşik, aynı n, ama anlamlılık VAR → durum SAGLANDI. Testin çift yönlü
    olması şart; yalnız negatif kutup çivilenirse "her şeye ZAYIF de" de testi geçerdi."""
    _cal_yaz(0.19, 95, True)
    skor = analytics.edge_verdict()["criteria"]["skor_sonuc"]
    assert skor["status"] == "gecti" and skor["durum"] == "SAGLANDI", skor


def test_hukum_cumlesi_dort_kovayi_da_sayar(sandbox_state):
    """"x/5 sağlandı" tek başına, kalanların başarısız mı, ölçülemez mi, yoksa zayıf mı olduğunu
    gizler — sabır, başarısızlık ve gürültü aynı cümleye sıkıştırılamaz. (Payda Hafta 3a'da
    dörtten BEŞE çıktı: 5. ölçüt KUYRUK.)"""
    _cal_yaz(0.0492, 95, False)
    ev = analytics.edge_verdict()
    assert ev["verdict"].startswith("EDGE KANITI:"), ev["verdict"]
    for parca in ("zayıf", "sağlanmadı", "ölçülemedi"):
        assert parca in ev["verdict"], f"'{parca}' hüküm cümlesinde yok: {ev['verdict']}"
    assert ev["passed"] + ev["failed"] + ev["unmeasured"] + ev["zayif"] == 5, \
        f"dört kova toplamı 5 etmiyor: {ev}"


def test_anlamlilik_HESABI_OLMAYAN_olcutlere_ZAYIF_UYDURULMAZ(sandbox_state):
    """3. (tahmin isabeti) ve 4. (rejim edge) ölçütlerin bugün anlamlılık hesabı YOKTUR. Onlara
    "anlamlı değil" demek, yapılmamış bir testin sonucunu raporlamaktır. Bayrak alanları bunu
    makine-okunur söyler ki bir gün hesap eklendiğinde bu test onu HATIRLATSIN."""
    ev = analytics.edge_verdict()
    for ad in ("tahmin_isabeti", "rejim_edge"):
        c = ev["criteria"][ad]
        assert c.get("anlamlilik_hesabi") is False, f"{ad}: anlamlılık hesabı beyanı yok/yanlış"
        assert c["status"] != "zayif", f"{ad}: hesabı olmadığı hâlde ZAYIF damgası basılmış"
    for ad in ("skor_sonuc", "spy_ustu"):
        assert ev["criteria"][ad].get("anlamlilik_hesabi") is True, f"{ad}: hesap beyanı eksik"


# =================================================================================================
# E) MARUZİYET-DÜZELTİLMİŞ SPY FARKI
# =================================================================================================
def _islem(i: int, pnl: float, o: str, c: str, entry=100.0, qty=10):
    return {"id": f"T{i:05d}", "ts_open": o, "ts_close": c, "ticker": "AAA", "entry": entry,
            "qty": qty, "pnl_dollars": pnl, "r_multiple": pnl / 100.0, "costs": 1.0,
            "exit_reason": "target", "mfe_r": abs(pnl) / 100.0 + 0.1, "strategy_version": 1}


def test_maruziyet_orani_NOTIONAL_agirlikli_ve_gun_sayimindan_FARKLI(sandbox_state):
    """"En az bir pozisyon açıktı" ikili sayımı, tek hisselik bir günü beş hisselik bir günle aynı
    sayar — oysa beta maruziyeti beş kat farklıdır. Kurgu bunu ayırır: aynı günlerde açık, ama
    notional'ı 10 kat farklı iki defter AYNI `yatirimda_gun_orani`nı, FARKLI `oran`ı vermeli."""
    kucuk = [_islem(i, 10.0, "2025-01-02", "2025-01-06", entry=100.0, qty=1) for i in range(5)]
    buyuk = [_islem(i, 10.0, "2025-01-02", "2025-01-06", entry=100.0, qty=10) for i in range(5)]
    o1, d1 = analytics._exposure_ratio(kucuk, "2025-01-01", "2025-01-10")
    o2, d2 = analytics._exposure_ratio(buyuk, "2025-01-01", "2025-01-10")
    assert d1["yatirimda_gun_orani"] == d2["yatirimda_gun_orani"], "gün sayımı kurgu gereği aynı olmalı"
    assert o2 == pytest.approx(o1 * 10, rel=1e-6), \
        f"maruziyet notional'a duyarlı değil: {o1} vs {o2} — ikili gün sayımına düşmüş"


def test_maruziyet_olculemezse_DUZELTILMIS_FARK_URETILMEZ(sandbox_state):
    """Ham farkı "düzeltilmiş" adıyla ikinci kez yayınlamak, düzeltme yapılmadığı hâlde yapılmış
    gibi okunurdu. Alanı olmayan bir ölçüm None kalır ve ölçüt `olculemedi` olur."""
    oran, detay = analytics._exposure_ratio([], "2025-01-01", "2025-01-10")
    assert oran is None and "neden" in detay, detay


def test_verdict_ikinci_olcut_MARUZIYET_DUZELTILMIS_alani_okur(sandbox_state, monkeypatch):
    """Kararın DAYANDIĞI sayı değişti: ham fark negatifken düzeltilmiş fark pozitif olabilir (boğada
    taşınmamış beta cezası). Ölçüt yeni alanı okumazsa düzeltme yalnız SÜS olurdu.

    Kurgu: ham fark −0.50 (SPY'ın altında), düzeltilmiş +0.05 ve aralık sıfırı DIŞARIDA bırakıyor."""
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: {
        "start": "2025-01-01", "end": "2025-12-31", "benchmark": "SPY",
        "strategy_return": 0.10, "benchmark_return": 0.60,
        "excess_return": -0.50, "beat_benchmark": False,
        "maruziyet": {"oran": 0.0833}, "exposure_adjusted_excess": 0.05,
        "exposure_adjusted_beat": True, "anlamli": True,
        "ci": {"lo": 0.01, "hi": 0.09, "seviye": 0.95}, "ci_kapsam": "x"})
    c = analytics.edge_verdict()["criteria"]["spy_ustu"]
    assert c["status"] == "gecti", f"ölçüt hâlâ ham farkı okuyor: {c}"
    assert c["value"] == 0.05, f"ölçütün değeri düzeltilmiş fark değil: {c['value']}"
    assert c["ham_excess_return"] == -0.50, "ham alan kaldırılmış — geriye dönük uyum kırıldı"


def test_duzeltilmis_fark_pozitif_ama_ANLAMSIZSA_ZAYIF(sandbox_state, monkeypatch):
    """S3C'nin kendi gürültü kapısı: düzeltilmiş fark sıfırın üstünde ama aralık sıfırı KAPSIYORSA
    bu bir edge iddiası değildir."""
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: {
        "start": "a", "end": "b", "benchmark": "SPY", "strategy_return": 0.1,
        "benchmark_return": 0.1, "excess_return": 0.0, "beat_benchmark": False,
        "maruziyet": {"oran": 0.5}, "exposure_adjusted_excess": 0.02,
        "exposure_adjusted_beat": True, "anlamli": False,
        "ci": {"lo": -0.04, "hi": 0.08, "seviye": 0.95}, "ci_kapsam": "x"})
    c = analytics.edge_verdict()["criteria"]["spy_ustu"]
    assert c["status"] == "zayif" and c["durum"] == "ZAYIF", c


def test_benchmark_bootstrap_AYNI_DEFTERDE_AYNI_ARALIGI_verir(sandbox_state, monkeypatch):
    """SABİT TOHUM ÇİVİSİ: hiçbir işlem değişmediği hâlde panoda her turda kıpırdayan bir güven
    aralığı, okur tarafından "yeni bilgi" sanılır. İki ardışık çağrı birebir aynı aralığı vermeli."""
    import pandas as pd
    from meridian.adapters import data as data_adapter
    store.write_jsonl("trades.jsonl", [_islem(i, (-1) ** i * 50.0, "2025-01-02", "2025-01-06")
                                       for i in range(20)])
    monkeypatch.setattr(data_adapter, "load_bars", lambda *a, **k: pd.DataFrame(
        {"date": pd.to_datetime(["2025-01-01", "2025-12-31"]), "close": [100.0, 120.0]}))
    a, b = analytics.benchmark_relative(), analytics.benchmark_relative()
    assert a["ci"] == b["ci"], f"bootstrap aralığı koşudan koşuya oynuyor: {a['ci']} vs {b['ci']}"
    assert a["exposure_adjusted_excess"] is not None


# =================================================================================================
# DIŞ TÜKETİCİ (YASA 6) — üretilen alanın panoda okuyucusu var mı?
# =================================================================================================
@pytest.mark.parametrize("alan", ["ev.zayif", "DURUM_TON", "ZAYIF",
                                  "exposure_adjusted_excess", "maruziyet", "ci_kapsam"])
def test_pano_yeni_alanlari_okuyor(alan):
    """YASA 6: üretilen alanın DIŞ tüketicisi olmalı. `dashboard_mentions` app.js kaynağında
    literal arar — alan adı panoda geçmiyorsa üretilen sayı kimsenin görmediği bir yerde ölür."""
    assert codelaw.dashboard_mentions(alan), f"pano '{alan}' alanını hiç okumuyor (YASA 6)"


def test_pano_ZAYIF_tonu_ayri_ve_yesil_DEGIL():
    """Görsel ayrışma çivisi: ZAYIF ara tonda (warn) olmalı. Yeşile boyamak ölçülmemiş bir kesinlik
    iddia ederdi; kırmızıya boyamak ölçülmüş bir başarısızlık. Ton zinciri sırasıyla okunur."""
    src = pathlib.Path("meridian/web/app.js").read_text()
    assert 'ev.passed === 5 ? "pos"' in src, "5/5 yeşil kuralı kaybolmuş"
    assert 'ev.zayif ? "warn"' in src, "ZAYIF için ara ton yok"
    assert 'ev.unmeasured ? "warn"' in src, "ölçülemedi tonu kaybolmuş"
    assert src.index('ev.zayif ? "warn"') < src.index('ev.unmeasured ? "warn"'), \
        "ZAYIF kontrolü ölçülemedi'den SONRA geliyor — zayıf bir ölçüt ölçülemedi gibi okunur"
    assert 'SAGLANDI: "pos"' in src and 'ZAYIF: "warn"' in src, "durum→ton haritası panoda yok"
