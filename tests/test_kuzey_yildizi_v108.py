"""v108 — KUZEY YILDIZI TURU, sinyal tarafı (2026-07-28).

Kapsam: Aşama 1.1 (IC katmanlaması + cf üretim sadakati denetimi) ve Aşama 1.2 (bileşen IC'si).

Bu dosyanın çivilediği asıl şey TEK BİR CÜMLE: **ölçülmeyen ölçülmüş gibi sunulamaz.** Üç katman
ayrı ayrı raporlanmazsa 2100 simüle satır 95 gerçeği boğar ve "skorun tahmin gücü" diye okunan sayı
fiilen simülasyonun IC'si olur; simülasyonun canlıdan NEREDE ayrıldığı serbest metinde kalırsa o
sapma kod değişince sessizce yanlışa döner; bileşenler ayrı ölçülmezse "skor işe yaramıyor" cümlesi
"hiçbir parçası işe yaramıyor" diye okunur.
"""
from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from meridian import analytics, component_ic, counterfactual, store, strategy


# =================================================================================================
# A) IC KATMANLAMASI — gerçek / cf / havuz
# =================================================================================================
def _pairs_to_ledger(sandbox, gercek: list, cf_rows: list) -> None:
    """Üç katmanı da doldurabilen en küçük gerçek şema: trades.jsonl (score + r_multiple) ve
    counterfactuals.jsonl (entered + score + r_multiple)."""
    for i, (s, r) in enumerate(gercek):
        store.append_jsonl("trades.jsonl", {"id": f"T{i:05d}", "score": s, "r_multiple": r,
                                            "plan_id": f"P-2025-01-{(i % 28) + 1:02d}-AAA"})
    for i, (s, r) in enumerate(cf_rows):
        store.append_jsonl("counterfactuals.jsonl",
                           {"id": f"CF-{i}", "date": "2025-01-05", "ticker": "AAA",
                            "entered": True, "taken": False, "resolved": True,
                            "score": s, "r_multiple": r})


def test_uc_katman_AYRI_hesaplanir_ve_havuz_ikisinin_yerine_GECMEZ(sandbox_state):
    """Kurgu bilerek ZIT: gerçek dilim pozitif eğimli, cf dilimi negatif. Tek havuzlanmış sayı
    raporlansaydı 40 cf satırı 40 gerçek satırı bastırır ve iki zıt gerçek tek rakama çökerdi."""
    rng = np.random.default_rng(7)
    gercek = [(int(s), float(s) / 50.0 + float(rng.normal(0, 0.1))) for s in rng.integers(40, 95, 40)]
    cf_rows = [(int(s), -float(s) / 50.0 + float(rng.normal(0, 0.1))) for s in rng.integers(40, 95, 40)]
    _pairs_to_ledger(sandbox_state, gercek, cf_rows)

    cal = analytics.score_calibration()

    kat = cal["katmanlar"]
    assert set(kat) == {"gercek", "cf", "havuz"}, "üç katman açık adla durmuyor"
    assert kat["gercek"]["rank_ic"] > 0 > kat["cf"]["rank_ic"], \
        f"katmanlar ayrışmadı: {kat['gercek']} / {kat['cf']}"
    assert kat["gercek"]["n"] == 40 and kat["cf"]["n"] == 40
    assert kat["havuz"]["n"] == 80, "havuz iki dilimin TOPLAMI değil"
    # Geriye dönük uyum: eski tüketiciler `real`/`cf`/`rank_ic` alanlarına bakıyor, kırılmamalı.
    assert cal["real"]["rank_ic"] == kat["gercek"]["rank_ic"]
    assert cal["rank_ic"] == kat["havuz"]["rank_ic"]


def test_ic_ESIK_ALTINDA_None_kalir_sifira_cokmez(sandbox_state):
    """IC_MIN_SAMPLE altındaki bir dilim için 0.0 yazmak, "ölçtük ve ilişki yok" demektir —
    oysa doğru cümle "ölçemedik"tir."""
    rng = np.random.default_rng(3)
    az = [(int(s), float(rng.normal())) for s in rng.integers(40, 95, 10)]     # 10 < 30
    cok = [(int(s), float(rng.normal())) for s in rng.integers(40, 95, 40)]
    _pairs_to_ledger(sandbox_state, az, cok)

    kat = analytics.score_calibration()["katmanlar"]

    assert kat["gercek"] is None, "eşik altı dilim uydurma bir sayıyla dolduruldu"
    assert kat["cf"] is not None and kat["cf"]["n"] == 40


def test_tek_siralama_uygulamasi_vardir(sandbox_state):
    """`spearman_ic` modül düzeyine ÇIKARILDI ki bileşen IC'si onu yeniden yazmasın. İki ayrı
    rütbeleme, aynı büyüklüğün iki farklı değerini üretir ve hangisinin doğru olduğu yazılı olmaz."""
    assert "spearman_ic" in inspect.getsource(component_ic), \
        "bileşen IC'si merkezî Spearman'ı kullanmıyor — ikinci bir uygulama doğmuş"
    # Beraberlikler ORTALAMA rütbeyle kırılır: girdi sırası sonucu DEĞİŞTİRMEMELİ.
    duz = [(1.0, 5.0), (1.0, 1.0), (2.0, 9.0), (3.0, 2.0)]
    assert analytics.spearman_ic(duz) == analytics.spearman_ic(list(reversed(duz)))
    # Tek tarafta hiç rütbe değişimi yok → korelasyon TANIMSIZ, 0.0 değil.
    assert analytics.spearman_ic([(5.0, 1.0), (5.0, 2.0), (5.0, 3.0)]) is None


def test_gecmis_serisi_UC_katmani_da_tasir(sandbox_state):
    """Trend grafiği havuz ile gerçek arasındaki makası gösteriyordu ama makasın NEREDEN geldiğini
    (cf dilimi) göstermiyordu — o çizgi seride yoksa fark her bakışta yeniden tahmin edilir."""
    cal = {"rank_ic": -0.01, "n": 80, "n_real": 40, "n_cf": 40,
           "real": {"rank_ic": 0.31, "n": 40}, "cf": {"rank_ic": -0.12, "n": 40}}

    assert analytics.record_score_calibration_point("2026-07-28", cal) is True

    satir = store.read_jsonl(analytics.SCORE_CAL_HISTORY)[-1]
    assert satir["real_ic"] == 0.31 and satir["cf_ic"] == -0.12 and satir["rank_ic"] == -0.01
    # IDEMPOTENT: aynı güne ikinci nokta düşmez (yeniden başlatma seriyi sahte yoğunlaştırmasın).
    assert analytics.record_score_calibration_point("2026-07-28", cal) is False


# =================================================================================================
# A2) CF ÜRETİM SADAKATİ — beyan KENDİ KENDİNİ DENETLER
# =================================================================================================
def test_cf_sadakat_beyani_canli_KAYNAKLA_tutarli():
    """DENETİMİN KENDİSİ BURADA ÇİVİLENİR. `analytics.CF_SIM_EXITS`/`CF_MISSING_EXITS` serbest bir
    yorum satırı olsaydı, biri cf'e trailing stop eklediğinde beyan olduğu yerde kalır ve YANLIŞ
    olduğu hiçbir yerde görünmezdi. Test beyanı canlı kaynak koduyla karşılaştırır.

    Beklenen ilişki: beyan edilen SİMÜLE çıkışların hepsi `counterfactual.advance`ın gövdesinde
    GEÇMELİ; beyan edilen EKSİK mekanizmaların hiçbiri orada geçMEMELİ (geçiyorsa artık eksik
    değildir ve beyan güncellenmelidir)."""
    adv = inspect.getsource(counterfactual.advance)

    for ad in analytics.CF_SIM_EXITS:
        assert f'"{ad}"' in adv, f"beyan '{ad}' çıkışını simüle edildi sayıyor ama advance'te YOK"

    # Eksik beyan edilen mekanizmaların cf'te izi olmamalı. `trail`/`scale_out` gibi kökler aranır:
    # tam ad eşleşmesi, `trail_stop` gibi bir değişkenin eklenmesini KAÇIRIRDI.
    for kok in ("trail", "scale_out", "chandelier", "giveback", "breakeven", "regime_flip"):
        assert kok not in adv, \
            f"'{kok}' artık cf'te uygulanıyor — CF_MISSING_EXITS beyanı BAYAT, güncellenmeli"

    # Ve o mekanizmalar CANLI yolda gerçekten var (beyan "eksik" derken var olmayan bir şeyi
    # eksik saymamalı — o da uydurma olurdu).
    canli = inspect.getsource(strategy.manage_position)
    for kok in ("trail", "chandelier", "giveback", "breakeven", "regime_flip"):
        assert kok in canli, f"'{kok}' canlı çıkış yasasında yok — 'eksik' beyanı dayanaksız"


def test_cf_fidelity_ciktisi_sadakat_beyanini_TASIR(sandbox_state):
    """`fidelity_ok: true` tek başına "simülasyon canlıyı temsil ediyor" diye okunuyordu. O bayrak
    yalnız korelasyon+sapma eşiğini söyler; hangi mekanizmaların HİÇ simüle edilmediğini değil."""
    for i in range(12):
        store.append_jsonl("trades.jsonl",
                           {"id": f"T{i}", "plan_id": f"P-2025-03-{i + 1:02d}-AAA",
                            "r_multiple": 0.5 + i * 0.1})
        store.append_jsonl("counterfactuals.jsonl",
                           {"id": f"CF-{i}", "date": f"2025-03-{i + 1:02d}", "ticker": "AAA",
                            "entered": True, "taken": True, "resolved": True,
                            "r_multiple": 0.55 + i * 0.1})

    out = analytics.cf_fidelity()

    assert out["eksik_mekanizmalar"] == list(analytics.CF_MISSING_EXITS)
    assert out["eksik_friksiyon"] == list(analytics.CF_MISSING_FRICTION)
    assert out["sim_cikislar"] == list(analytics.CF_SIM_EXITS)
    assert "UYGULANMAZ" in out["sadakat_beyani"]


def test_cf_dilim_IC_si_sadakat_uyarisini_YANINDA_tasir(sandbox_state):
    """cf dilimin IC'si, canlı çıkış yasasının yalnız bir kısmıyla simüle edilmiş sonuçlardan gelir.
    Etiket sayının yanında durmazsa okur onu gerçek işlem IC'siyle aynı kefeye koyar."""
    rng = np.random.default_rng(11)
    _pairs_to_ledger(sandbox_state, [], [(int(s), float(rng.normal())) for s in rng.integers(40, 95, 40)])

    kat = analytics.score_calibration()["katmanlar"]

    assert kat["cf"]["sadakat"] == analytics.CF_EXIT_FIDELITY_NOTE
    assert kat["gercek"] is None


# =================================================================================================
# B) BİLEŞEN IC — rs / tight / vol / prox × 5/10/20 bar × katman
# =================================================================================================
def _bars(n=420, seed=5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.001, 0.02, n)))
    dates = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"date": dates, "open": close * 0.995, "high": close * 1.02,
                         "low": close * 0.98, "close": close,
                         "volume": rng.integers(1_000_000, 5_000_000, n).astype(float)})


@pytest.fixture
def bar_evreni(sandbox_state, monkeypatch):
    """İki sembollük sahte evren — kesitsel RS'in çalışabilmesi için en az iki isim şart."""
    per = {t: _bars(seed=s).set_index("date") for t, s in (("AAA", 5), ("BBB", 6))}
    monkeypatch.setattr(component_ic, "_load_universe", lambda: per)
    return per


def test_bilesenler_barlardan_YENIDEN_hesaplanir_ve_tablo_uc_katmanli(bar_evreni):
    """Bileşenler hiçbir deftere alan olarak yazılmıyor (yalnız `notes` metninde ve orada da 313
    satırın 13'ünde). Ölçüm o yüzden bardan, canlı skorun kullandığı AYNI gösterge fonksiyonlarıyla
    yeniden üretilir."""
    tarihler = [str(d.date()) for d in list(bar_evreni["AAA"].index)[300:360]]
    for i, d in enumerate(tarihler):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}", "plan_id": f"P-{d}-AAA"})
        store.append_jsonl("counterfactuals.jsonl",
                           {"id": f"CF-{i}", "date": d, "ticker": "BBB", "entered": True,
                            "resolved": True, "r_multiple": 0.1})

    out = component_ic.component_ic()

    # TABLO 2026-07-29'da YEDİ BİLEŞENE ÇIKTI (G2 skor yeniden inşası): eski dördü kıyas tabanı
    # olarak DURUYOR, üç yeni aday (rvol20 / mom12_1 / rmom) yanlarına eklendi. Sıra da çivilenir:
    # pano ve evidence_pack satırları bu listeden üretiyor.
    assert out["components"] == ["rs", "tight", "vol", "prox", "rvol20", "mom12_1", "rmom"]
    assert out["horizons"] == [5, 10, 20]
    assert set(out["tablo"]) == {"gercek", "cf", "havuz"}
    for c in ("rs", "tight", "vol", "prox", "rvol20", "mom12_1"):
        for h in ("5", "10", "20"):
            hucre = out["tablo"]["gercek"][c][h]
            assert hucre["n"] >= 30 and hucre["ic"] is not None, f"{c}@{h} ölçülemedi: {hucre}"
            assert -1.0 <= hucre["ic"] <= 1.0
    # rmom BU FİKSTÜRDE ÖLÇÜLEMEZ ve bu doğru davranıştır: ısınması ~483 bar (252 beta + 231 artık
    # + 21 atlama), fikstür 420 bar ve evrende endeks serisi yok. Ölçülemeyen hücre None kalır —
    # sıfır ya da uydurma bir sayı değil (UYDURMA YASAĞI). Yani bu satır tablonun boş olmasını
    # değil, boşluğun DÜRÜSTÇE raporlandığını çiviler.
    for h in ("5", "10", "20"):
        assert out["tablo"]["gercek"]["rmom"][h]["ic"] is None, "ısınmamış rmom sayı uydurdu"
    # Ağırlıklar tabloyla birlikte gider: hangi bileşenin ne kadar ağırlık taşıdığı, IC'nin
    # yanında olmazsa "hangi ağırlığı hangi yöne?" sorusu kanıta bağlanamaz.
    assert set(out["agirliklar"]) == set(out["components"])


def test_ayni_gozlem_havuzda_IKI_KEZ_sayilmaz(bar_evreni):
    """Alınmış bir cf satırı ile ona karşılık gelen gerçek işlem AYNI (ticker, tarih) gözlemidir;
    bileşen değeri de ileri getirisi de bardan geldiği için ikisi BİREBİR aynı çifti üretir.
    İki kez saymak paydayı şişiren düpedüz bir yalan olurdu."""
    tarihler = [str(d.date()) for d in list(bar_evreni["AAA"].index)[300:340]]
    for i, d in enumerate(tarihler):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}", "plan_id": f"P-{d}-AAA"})
        store.append_jsonl("counterfactuals.jsonl",           # AYNI ticker + AYNI tarih
                           {"id": f"CF-{i}", "date": d, "ticker": "AAA", "entered": True,
                            "resolved": True, "r_multiple": 0.1})

    out = component_ic.component_ic()

    assert out["n_gozlem"]["gercek"] == 40 and out["n_gozlem"]["cf"] == 40
    assert out["n_gozlem"]["havuz_tekil"] == 40, "havuz tekilleştirilmedi — payda ikiye katlanmış"
    n_havuz = out["tablo"]["havuz"]["vol"]["5"]["n"]
    n_gercek = out["tablo"]["gercek"]["vol"]["5"]["n"]
    assert n_havuz == n_gercek, f"havuz {n_havuz}, gerçek {n_gercek} — çift sayım var"


def test_gozlem_yokken_None_doner_bos_tablo_YAZILMAZ(sandbox_state, monkeypatch):
    monkeypatch.setattr(component_ic, "_load_universe", lambda: {})
    assert component_ic.component_ic() is None
    assert store.read_json(component_ic.COMPONENT_IC_FILE, None) is None, \
        "ölçüm yapılmadan artefakt yazıldı — 'ölçtük' izlenimi uydurmadır"


def test_ufuk_dolmamis_barlar_ILERI_GETIRIYE_uydurulmaz(bar_evreni):
    """Serinin son barlarında `close[t+20]` YOKTUR. O satırlar 20-bar hücresinden düşer ama 5-bar
    hücresinde kalabilir — n'ler ufka göre AZALARAK farklılaşmalı, hepsi eşitse bir yerde
    uydurma dolgu var demektir."""
    son = [str(d.date()) for d in list(bar_evreni["AAA"].index)[-45:]]
    for i, d in enumerate(son):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}", "plan_id": f"P-{d}-AAA"})

    out = component_ic.component_ic()

    n5 = out["tablo"]["gercek"]["vol"]["5"]["n"]
    n20 = out["tablo"]["gercek"]["vol"]["20"]["n"]
    assert n5 > n20, f"ufuk dolmamış barlar düşmemiş (n5={n5}, n20={n20})"


def test_evidence_pack_ozeti_YALNIZ_olculebilen_gercek_hucreleri_tasir(bar_evreni):
    """Beyne 36 hücrelik tam tablo giderse prompt şişer ve içindeki tek anlamlı satır kaybolur.
    Ölçülemeyen hücre HİÇ gitmez; ama kaçının ölçülemediği bir satırda söylenir — "gördüğün her şey
    bu" ile "ölçebildiğimiz her şey bu" farkı beyne de açıkça gitmeli."""
    tarihler = [str(d.date()) for d in list(bar_evreni["AAA"].index)[300:360]]
    for i, d in enumerate(tarihler):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}", "plan_id": f"P-{d}-AAA"})

    satirlar = component_ic.compact_lines(component_ic.component_ic())

    assert satirlar and any("IC" in s for s in satirlar)
    assert any("hücre ölçülebildi" in s for s in satirlar), "ölçülemeyenlerin sayısı beyne gitmiyor"
    assert len(satirlar) <= 7, "kompakt özet şişmiş — prompt tavanı deliniyor"


def test_bos_belgede_ozet_COKMEZ_ve_kanit_yok_der(sandbox_state):
    assert component_ic.compact_lines(None) == []
    bos = {"tablo": {"gercek": {"rs": {"5": {"ic": None, "n": 3}}}},
           "components": ["rs"], "horizons": [5]}
    assert "kanıt yok" in component_ic.compact_lines(bos)[0]


def test_getiri_TANIMI_ciktinin_icinde_yazili(bar_evreni):
    """Tanım yalnız kodda dursaydı, panoyu ya da kanıt paketini okuyan "hangi getiri?" sorusunu
    koda inmeden cevaplayamazdı — ve R sanıp yanlış ölçekte yorumlardı."""
    tarihler = [str(d.date()) for d in list(bar_evreni["AAA"].index)[300:340]]
    for i, d in enumerate(tarihler):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}", "plan_id": f"P-{d}-AAA"})

    out = component_ic.component_ic()

    assert "close[t+h]/close[t]-1" in out["getiri_tanimi"]
    assert "R'ye bölünmez" in out["getiri_tanimi"]


def test_bilesen_IC_hicbir_KARARA_girmez():
    """SIFIR YETKİ: bu modül rapor üretir. Kapıya, silahlanmaya ya da skora dokunan tek bir çağrı
    bile, ölçüm aracını sessizce karar aracına çevirirdi."""
    src = inspect.getsource(component_ic)
    for yasak in ("classify_gate", "_gate_eval", "submit(", "write_strategy", "arm_", "promote"):
        assert yasak not in src, f"bileşen IC'si karar yoluna dokunuyor: {yasak}"


# =================================================================================================
# C) EDGE HÜKMÜ — üç durumun yazılı dili
# =================================================================================================
def test_uc_durumun_yazili_dili_TEK_yerde_eslesir(sandbox_state, monkeypatch):
    """Makine değerleri (`gecti`/`kaldi`/`olculemedi`/`zayif`) sözleşmedir ve kırılmaz; insan dili
    onların YANINDA taşınır. Her tüketici kendi çevirisini yapsaydı iki farklı hüküm doğardı.

    DÖRDÜNCÜ DURUM (2026-07-29): `zayif` = eşik geçildi AMA istatistiksel anlamlılık yok. Üç durum
    yeterli sanılmıştı; canlıda IC 0.0492 (eşik 0.03, anlamli=False) "SAGLANDI" yanınca yetmediği
    görüldü — gürültü ile kanıt aynı kelimeye sıkışıyordu."""
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: None)
    monkeypatch.setattr(analytics, "prediction_hit_rate", lambda: {"n": 0, "sign_hits": None})

    v = analytics.edge_verdict()

    assert analytics.EDGE_DURUM_ADI == {"gecti": "SAGLANDI", "kaldi": "SAGLANMADI",
                                        "olculemedi": "OLCULEMEDI", "zayif": "ZAYIF"}
    for c in v["criteria"].values():
        assert c["durum"] == analytics.EDGE_DURUM_ADI[c["status"]]
    assert v["verdict"].startswith("EDGE KANITI:")
    assert "ölçülemedi" in v["verdict"]
