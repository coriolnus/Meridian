"""test_orgu2_v103.py — ÖRGÜ-2 (2026-07-27): hüküm, yetki alarmı ve dakikalık kanıt birikimi.

Bu turun dört kaleminin ortak sınıfı, üç ayrı sessizlik biçimidir:

  A3. DÖRT ÖLÇÜT, SIFIR HÜKÜM. Pano dört sayıyı yan yana gösteriyor ama "peki KENAR VAR MI?"
      sorusunu okurun kafasında birleştirmesini bekliyordu. Yazılı olmayan bir birleştirme her
      bakışta yeniden yapılır ve HER SEFERİNDE FARKLI çıkar. Hüküm artık kodda, tek yerde.
      Üçüncü durum (`olculemedi`) zorunludur: ikili bir hüküm, ölçülmemiş olanı sessizce "kaldı"
      sayar ve sabır ile başarısızlık aynı renge boyanır.

  B2. YETKİ DEVRİ SIRADAN BİR LOG SATIRIYDI. `llm_advisor_promotion` bir danışmanın canlı karar
      yüzeyine dokunma hakkını EŞİK DOLDUĞU İÇİN kazanmasıdır — operatör onaylamaz, haberdar
      edilir. `obs.log` ile yazıldığında bu haber panel açılmadan hiçbir yere ulaşmıyordu.
      İki yön de yüksek sesli: yetkinin sessizce GERİ ALINMASI "danışman hâlâ konuşuyor" sanısını
      bırakır.

  C2. UÇUCU KANIT. mrd:bars ring'i ~2 seans tutar; TTL sonrası o çerçeve YOKTUR. "Dakika-hassas
      icra EOD'den iyi mi?" sorusu ancak geçmiş çerçeveler birikmişse cevaplanabilir ve birikim
      bugün başlamazsa üç ay sonra üç aylık olmaz. Arşiv ölçümden ÖNCE açılır — ama arşiv arızası
      canlı veri hattını ASLA düşüremez, yoksa kanıt uğruna gerçeği kaybederiz.
"""
from __future__ import annotations

import datetime as dt
import inspect
import subprocess

import pytest

from meridian import analytics, bararchive, codelaw, obs, store


# =================================================================================================
# A3) EDGE HÜKMÜ — BEŞ ölçütün tek yazılı kararı (5. ölçüt KUYRUK: Hafta 3a, 2026-07-30)
# =================================================================================================
def _cal(rank_ic=0.20, n=500, n_real=95, n_cf=405, real_ic=0.11, anlamli=True) -> dict:
    """`analytics.score_calibration()` çıktısının GERÇEK şeması.

    GÖVDE DEĞİŞTİ (2026-07-28, Aşama 1.1): hüküm artık GERÇEK katmandan çıkar, havuzdan değil.
    Bu yüzden `real_ic` varsayılan olarak DOLUDUR ve `rank_ic` (havuz) yalnız bağlam alanı olarak
    taşınır. `katmanlar` bloğu üreticinin yeni şeması — tüketicinin eski `real`/`cf` alanlarına
    düşebildiğini de sınayabilmek için ikisi birlikte yazılır."""
    out = {"n": n, "n_real": n_real, "n_cf": n_cf, "rank_ic": rank_ic,
           "quintiles": [], "real": None, "cf": None, "katmanlar": {}}
    if real_ic is not None:
        # ANLAMLILIK ARTIK DURUMU BELİRLER (2026-07-29, dördüncü durum ZAYIF): eşiği geçen ama
        # gürültüden ayrılmayan bir IC "SAGLANDI" sayılamaz. Bu yüzden parametrik — senaryolar
        # eşik ile anlamlılığı AYRI AYRI kurabilmeli.
        out["real"] = {"rank_ic": real_ic, "n": n_real, "anlamli": anlamli}
    out["katmanlar"] = {"gercek": out["real"], "cf": None,
                        "havuz": None if rank_ic is None else {"rank_ic": rank_ic, "n": n}}
    return out


def _kuyruk_islemleri(n=45) -> list:
    """5. ölçütü (KUYRUK) GEÇEN bir defter: n >= EDGE_TAIL_N_MIN, düşüş eşiğin altında, en kötü
    R'ler −1,0R civarında (stop disiplini). Deterministik — rastgelelik yok ki senaryo her koşuda
    aynı hükmü versin.

    ÖRÜNTÜ: üçte biri kazanan (+2R), üçte ikisi kaybeden (−1R) ama kazananlar daha büyük →
    sermaye eğrisi yukarı gider ve düşüş sığ kalır. CVaR%5 ≈ −1,0R (boyutlandırma yasasının
    söz verdiği şey), yani EDGE_CVAR5_MIN_R (−1,5R) tabanının rahatça üstünde."""
    out = []
    for i in range(n):
        kazanan = i % 3 == 0
        r = 2.0 if kazanan else -1.0
        out.append({"id": f"T{i:05d}", "ts_open": f"2026-01-{(i % 28) + 1:02d}",
                    "ts_close": f"2026-02-{(i % 28) + 1:02d}", "ticker": "AAA",
                    "r_multiple": r, "pnl_dollars": r * 500.0, "costs": 5.0,
                    "plan_id": f"P-2026-01-{(i % 28) + 1:02d}-AAA", "regime": "trend_up",
                    "score": 80, "setup": "breakout_vcp", "strategy_version": 3})
    return out


def _re(n=60, avg_r=0.20, regime="trend_up") -> dict:
    """`analytics.regime_edge()` çıktısının GERÇEK şeması — künye (`_kaynak`) DAHİL, çünkü onun
    rejim sanılması bu ölçütün en kolay kırılma yoludur."""
    return {regime: {"n": n, "avg_r": avg_r, "win_rate": 0.55},
            "_kaynak": {"source": "sim", "n_total": n}}


@pytest.fixture
def bes_olcut(sandbox_state, monkeypatch):
    """BEŞİ de GEÇEN taban senaryo; her test yalnız kırmak istediği ölçüte dokunur.
    (Hafta 3a'da dörtten beşe çıktı — 5. ölçüt KUYRUK gerçek bir defter ister, o yüzden
    fikstür artık trades.jsonl da tohumlar.)"""
    store.write_json("score_calibration.json", _cal(real_ic=0.11))
    store.write_json("regime_edge.json", _re())
    store.write_jsonl("trades.jsonl", _kuyruk_islemleri())
    monkeypatch.setattr(analytics, "benchmark_relative",
                        lambda: {"start": "2026-01-01", "end": "2026-07-01", "benchmark": "SPY",
                                 "strategy_return": 0.20, "benchmark_return": 0.05,
                                 "excess_return": 0.15, "beat_benchmark": True,
                                 # SAGLANDI artık eşik VE anlamlılık ister (2026-07-29)
                                 "maruziyet": {"oran": 0.5},
                                 "exposure_adjusted_excess": 0.12,
                                 "exposure_adjusted_beat": True, "anlamli": True,
                                 "ci": {"lo": 0.04, "hi": 0.20, "seviye": 0.95}})
    monkeypatch.setattr(analytics, "prediction_hit_rate",
                        lambda: {"n": 10, "sign_hits": 7, "mean_abs_err": 0.02})
    return sandbox_state


def test_esikler_modul_sabiti_olarak_TEK_yerde_durur():
    """Eşikler koda gömülü olsaydı hüküm denetlenemezdi: okur "0.05 nereden geldi" diye
    soramaz, testler de eşiği değiştirmeden senaryo kuramazdı."""
    assert analytics.EDGE_IC_MIN == 0.03          # v2 (2026-07-28): gerçek katman tabanına göre
    assert analytics.EDGE_IC_N_MIN == 60          # ARTIK GERÇEK katman n'i (v1'de havuz n'iydi)
    assert analytics.PRED_HIT_N_MIN == 10
    assert analytics.PRED_HIT_RATE_MIN == 0.6
    assert analytics.REGIME_N_MIN == 30
    assert analytics.REGIME_AVG_R_MIN == 0.0      # karşılaştırma KESİN büyüktür (`> 0`)
    # 5. ölçüt KUYRUK (Hafta 3a, 2026-07-30) — üç eşiği de aynı yerde, adıyla durur
    assert analytics.EDGE_TAIL_N_MIN == 40
    assert analytics.EDGE_MAXDD_MAX == 0.16   # 0.08→0.16: operatör kararı 2026-08-13 (EDG-032 dd %12.7 × 1.3)
    assert analytics.EDGE_CVAR5_MIN_R == -1.5
    # DÜŞÜŞ TAVANI ÜÇ YERDE AYNI SAYI OLMALI: operatörün yazılı başarısızlık sınırı (goal.yaml),
    # EDGE'in kuyruk ölçütü ve SONUÇ hükmünün maks-düşüş ölçütü. Sürüklenirse burası kırmızı yanar.
    from meridian import config
    assert analytics.EDGE_MAXDD_MAX == analytics.RESULT_MAXDD_MAX == float(
        config.goal()["max_drawdown"]), "düşüş tavanı üç kaynakta ayrışmış"


def test_besi_de_gecerse_hukum_TAM_der(bes_olcut):
    v = analytics.edge_verdict()

    assert v["passed"] == 5 and v["failed"] == 0 and v["unmeasured"] == 0 and v["zayif"] == 0
    assert "5/5 sağlandı" in v["verdict"] and "TAM" in v["verdict"]
    assert all(c["status"] == "gecti" for c in v["criteria"].values())


def test_bos_defterde_besi_de_OLCULEMEDI_ve_TAM_denmez(sandbox_state, monkeypatch):
    """Boş bir depoda doğru cevap "kenar yok" değil "henüz bilmiyoruz"dur. Beş ölçütün beşi de
    ölçülemezken kırmızı yanıp "edge kanıtlanmadı — 0 geçti" demek doğrudur; "TAM" demek ya da
    ölçülemeyeni gizlemek UYDURMA olurdu."""
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: None)
    monkeypatch.setattr(analytics, "prediction_hit_rate",
                        lambda: {"n": 0, "sign_hits": None, "mean_abs_err": None})

    v = analytics.edge_verdict()

    assert [c["status"] for c in v["criteria"].values()] == ["olculemedi"] * 5
    assert v["passed"] == 0 and v["unmeasured"] == 5
    assert "TAM" not in v["verdict"]
    assert "5 ölçülemedi" in v["verdict"]


def test_hukum_cumlesi_passed_ve_unmeasured_sayilariyla_TUTARLI(bes_olcut, monkeypatch):
    """Cümle ile sayılar ayrı hesaplansaydı biri diğerini yalanlayabilirdi — ve okur cümleye
    inanırdı, sayıya değil."""
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: None)            # → olculemedi
    monkeypatch.setattr(analytics, "prediction_hit_rate",
                        lambda: {"n": 10, "sign_hits": 2, "mean_abs_err": 0.4})   # → kaldi

    v = analytics.edge_verdict()

    # 3 geçti (skor + rejim + kuyruk), 1 kaldı (tahmin), 1 ölçülemedi (SPY)
    assert v["passed"] == 3 and v["failed"] == 1 and v["unmeasured"] == 1 and v["zayif"] == 0
    assert (v["passed"] + v["failed"] + v["unmeasured"] + v["zayif"]
            == len(v["criteria"]) == 5), "dört kova toplamı ölçüt sayısını tutmuyor"
    assert f"{v['passed']}/5 sağlandı" in v["verdict"]
    assert f"{v['unmeasured']} ölçülemedi" in v["verdict"]
    assert "TAM" not in v["verdict"], "ölçülemeyen varken kutlama dili kullanıldı"


# ---- 1) skor → sonuç ---------------------------------------------------------------------------
def test_skor_olcutu_YALNIZ_gercek_katmani_kullanir_ve_kaynagi_YAZAR(bes_olcut):
    """Aşama 1.1 kararı (2026-07-28): kanıt gövdesi YALNIZ gerçek katmandır — v1'in havuz kararı
    geri alındı. Ölçüldü: 2102 cf satırı 95 gerçeği 22:1 boğuyordu, yani "skorun tahmin gücü" diye
    raporlanan sayı fiilen cf'in IC'siydi. Kaynak etiketi bunu HER okumada söylemeli."""
    c = analytics.edge_verdict()["criteria"]["skor_sonuc"]

    assert c["value"] == 0.11 and c["n"] == 95, "hüküm hâlâ havuz gövdesinden okuyor"
    assert c["kaynak"] == "gerçek kapanmış işlem (cf HARİÇ)"


def test_havuz_artik_BAGLAM_alanidir_hukum_tasimaz(bes_olcut):
    """Havuzlanmış sayı atılmaz (bilgi kaybı da bir kusurdur) ama hükmün DAYANDIĞI yer değildir."""
    c = analytics.edge_verdict()["criteria"]["skor_sonuc"]
    assert c["havuz_ic"] == 0.20 and c["dogrulama_bandi"] == 0.20


def test_gercek_dilim_yokken_olcut_OLCULEMEDI_olur(sandbox_state, monkeypatch):
    """Gerçek katman yoksa hüküm havuza KAÇMAZ — ölçülemedi der. Kaçsaydı, tam da geri alınan v1
    davranışına sessizce geri dönerdik."""
    store.write_json("score_calibration.json", _cal(real_ic=None))
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: None)
    monkeypatch.setattr(analytics, "prediction_hit_rate", lambda: {"n": 0, "sign_hits": None})

    c = analytics.edge_verdict()["criteria"]["skor_sonuc"]

    assert c["status"] == "olculemedi" and c["value"] is None


@pytest.mark.parametrize("real_ic,n_real,anlamli,beklenen", [
    (0.20, 95, True, "gecti"),
    # DÖRDÜNCÜ DURUM (2026-07-29): eşik geçildi AMA aralık sıfırı kapsıyor. Canlı vaka tam buydu
    # (IC 0.0492 > 0.03, anlamli=False) ve eski yasa buna "SAGLANDI" diyordu.
    (0.20, 95, False, "zayif"),
    (0.02, 95, True, "kaldi"),    # eşiğin altı: ölçtük ve YETMEDİ — bu bir başarısızlıktır
    (0.02, 95, False, "kaldi"),   # eşik geçilmediyse anlamlılık durumu DEĞİŞTİRMEZ
    # Anlamlılık ÖLÇÜLEMEDİYSE hüküm tamamlanamaz: "sağlandı" demek anlamlılığı varsaymak,
    # "zayıf" demek yapılmamış bir testin sonucunu uydurmak olurdu.
    (0.20, 95, None, "olculemedi"),
    (0.90, 59, True, "olculemedi"),   # gerçek katman eşiği dolmadı: yüksek IC bile hüküm taşımaz
    (None, 95, True, "olculemedi"),   # rütbe değişimi yok → korelasyon TANIMSIZ
])
def test_skor_olcutunun_dort_durumu(bes_olcut, real_ic, n_real, anlamli, beklenen):
    store.write_json("score_calibration.json",
                     _cal(real_ic=real_ic, n_real=n_real, anlamli=anlamli))
    assert analytics.edge_verdict()["criteria"]["skor_sonuc"]["status"] == beklenen


def test_kalibrasyon_dosyasi_hic_yokken_uc_COKMEZ(sandbox_state, monkeypatch):
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: None)
    monkeypatch.setattr(analytics, "prediction_hit_rate", lambda: {"n": 0, "sign_hits": None})

    c = analytics.edge_verdict()["criteria"]["skor_sonuc"]

    assert c["status"] == "olculemedi" and c["value"] is None


# ---- 2) SPY üstü -------------------------------------------------------------------------------
def test_spy_olcutu_benchmark_relative_in_KENDI_alanina_baglidir():
    """Pozitiflik ölçütü uydurulmuş bir alan adına değil, fonksiyonun GERÇEKTEN döndürdüğü
    `beat_benchmark`/`excess_return` alanlarına bağlanmalı. İkinci bir eşik hesabı yazmak aynı
    olgunun iki farklı yerde iki farklı cevabı olurdu."""
    donen = inspect.getsource(analytics.benchmark_relative)
    assert '"beat_benchmark"' in donen and '"excess_return"' in donen

    hukum = inspect.getsource(analytics.edge_verdict)
    assert "beat_benchmark" in hukum and "excess_return" in hukum


@pytest.mark.parametrize("br,beklenen", [
    # ÖLÇÜT ARTIK `exposure_adjusted_excess` OKUR (S3C, 2026-07-29): ham fark, parası SÜREKLİ
    # piyasada duran bir SPY tutucusuyla kıyas yapıyordu. Ham alanlar `ek` içinde durmaya devam
    # eder (geriye dönük uyum) ama DURUMU düzeltilmiş alan belirler.
    ({"excess_return": 0.15, "beat_benchmark": True, "maruziyet": {"oran": 0.5},
      "exposure_adjusted_excess": 0.12, "exposure_adjusted_beat": True, "anlamli": True},
     "gecti"),
    ({"excess_return": -0.30, "beat_benchmark": False, "maruziyet": {"oran": 0.5},
      "exposure_adjusted_excess": -0.11, "exposure_adjusted_beat": False, "anlamli": True},
     "kaldi"),
    # Düzeltilmiş fark sıfırın üstünde ama aralık sıfırı KAPSIYOR → edge iddiası değil.
    ({"excess_return": 0.15, "beat_benchmark": True, "maruziyet": {"oran": 0.5},
      "exposure_adjusted_excess": 0.02, "exposure_adjusted_beat": True, "anlamli": False},
     "zayif"),
    # Maruziyet ölçülemedi → düzeltilmiş fark üretilmez; ham farka geri düşüp "geçti" demek,
    # ölçütün adını değiştirip yasasını değiştirmemek olurdu.
    ({"excess_return": 0.15, "beat_benchmark": True, "maruziyet": {"oran": None},
      "exposure_adjusted_excess": None, "exposure_adjusted_beat": None, "anlamli": None},
     "olculemedi"),
    (None, "olculemedi"),
])
def test_spy_olcutunun_dort_durumu(bes_olcut, monkeypatch, br, beklenen):
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: br)
    c = analytics.edge_verdict()["criteria"]["spy_ustu"]

    assert c["status"] == beklenen
    assert c["value"] == (br["exposure_adjusted_excess"] if br else None)
    if br:
        assert c["ham_excess_return"] == br["excess_return"], "ham alan kaldırılmış"


# ---- 3) tahmin isabeti -------------------------------------------------------------------------
def test_tahmin_olcutu_ince_orneklemde_OLCULEMEDI_ama_deger_YİNE_raporlanir(bes_olcut, monkeypatch):
    """"2/3 tuttu ama n yetersiz" ile "hiç ölçüm yok" AYNI ŞEY DEĞİLDİR. Değeri gizlemek,
    hükmü denetlenemez yapardı."""
    monkeypatch.setattr(analytics, "prediction_hit_rate",
                        lambda: {"n": 3, "sign_hits": 2, "mean_abs_err": 0.1})

    c = analytics.edge_verdict()["criteria"]["tahmin_isabeti"]

    assert c["status"] == "olculemedi"
    assert c["value"] == round(2 / 3, 3) and c["n"] == 3 and c["sign_hits"] == 2


@pytest.mark.parametrize("n,hits,beklenen", [
    (10, 7, "gecti"),        # 0.70 >= 0.6
    (10, 6, "gecti"),        # tam eşik — sınır DAHİLDİR
    (10, 5, "kaldi"),        # 0.50: yazı-turadan ayırt edilemiyor
    (4, 4, "olculemedi"),    # 4/4 bile n eşiğinin altında hüküm taşımaz
    (0, None, "olculemedi"),
])
def test_tahmin_olcutunun_uc_durumu(bes_olcut, monkeypatch, n, hits, beklenen):
    monkeypatch.setattr(analytics, "prediction_hit_rate",
                        lambda: {"n": n, "sign_hits": hits, "mean_abs_err": None})
    assert analytics.edge_verdict()["criteria"]["tahmin_isabeti"]["status"] == beklenen


# ---- 4) rejim başına edge ----------------------------------------------------------------------
def test_rejim_olcutu_gecen_rejimi_ADIYLA_soyler(bes_olcut):
    c = analytics.edge_verdict()["criteria"]["rejim_edge"]

    assert c["status"] == "gecti"
    assert c["value"] == {"regime": "trend_up", "n": 60, "avg_r": 0.20}


def test_hicbir_rejim_n_esigini_gecmiyorsa_OLCULEMEDI(bes_olcut):
    """İnce örneklemde negatif bir avg_r "o rejimde kenar yok" DEMEZ, "henüz okunmuyor" der.
    Bunu "kaldı" saymak, sabrı başarısızlık diye raporlamak olurdu."""
    store.write_json("regime_edge.json", _re(n=29, avg_r=-0.9))   # REGIME_N_MIN=30 altı

    c = analytics.edge_verdict()["criteria"]["rejim_edge"]

    assert c["status"] == "olculemedi" and c["en_buyuk_n"] == 29


def test_orneklem_yeterli_ama_edge_yoksa_KALDI(bes_olcut):
    """Eşik artık KESİN büyüktür (`avg_r > 0.0`): tam sıfır beklenti bir kenar iddiası değil,
    kenarın YOKLUĞUdur — "ölçtük ve yetmedi" demek doğru cevaptır."""
    store.write_json("regime_edge.json", _re(n=300, avg_r=0.0))
    assert analytics.edge_verdict()["criteria"]["rejim_edge"]["status"] == "kaldi"
    store.write_json("regime_edge.json", _re(n=300, avg_r=-0.20))
    assert analytics.edge_verdict()["criteria"]["rejim_edge"]["status"] == "kaldi"


def test_kunye_REJIM_sanilmaz(bes_olcut):
    """`_kaynak` künyesinin içinde `n_total` var; onu rejim sayan bir tüketici paydayı şişirir ve
    ölçütü sahte bir rejimle GEÇİRİRDİ (regime_edge'in kendi yorumundaki tuzağın aynısı)."""
    store.write_json("regime_edge.json", {"_kaynak": {"source": "sim", "n": 9999, "avg_r": 5.0}})

    c = analytics.edge_verdict()["criteria"]["rejim_edge"]

    assert c["status"] == "olculemedi" and c["rejim_sayisi"] == 0


def test_regime_edge_dosyasi_yokken_uc_COKMEZ(bes_olcut):
    (sandbox := store._state()) and (sandbox / "regime_edge.json").unlink()
    assert analytics.edge_verdict()["criteria"]["rejim_edge"]["status"] == "olculemedi"


# ---- uç + pano ---------------------------------------------------------------------------------
@pytest.fixture
def client(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    return TestClient(api.app)


def test_diagnostics_hukmu_servis_eder_ve_bos_state_500_URETMEZ(client):
    d = client.get("/api/diagnostics")
    assert d.status_code == 200

    ev = d.json()["mlops"]["edge_verdict"]
    assert ev["unmeasured"] == 5 and "TAM" not in ev["verdict"]
    assert set(ev["criteria"]) == {"skor_sonuc", "spy_ustu", "tahmin_isabeti", "rejim_edge",
                                   "kuyruk"}


def test_hukum_panoda_TUKETILIYOR():
    """YASA 6: üretilen alan tüketilir. 'Panoda gösteriliyor' gerekçesi, app.js taranarak
    KANITLANABİLİR olmadıkça gerekçe değildir."""
    for alan in ("edge_verdict", "ev.verdict", "ev.unmeasured", "ev.passed"):
        assert codelaw.dashboard_mentions(alan), f"{alan} panoda okunmuyor"


def test_hukum_satiri_kartin_EN_USTUNDE_ve_yesil_dili_5_5_e_bagli():
    src = open("meridian/web/app.js").read()
    # Başlık ETİKETİNE değil METNİNE tutunulur: h2/h3 seviyesi başka bir iş kolunun tipografi
    # kararıdır ve bu testin ölçtüğü olguyla (hükmün SIRASI) hiç ilgisi yoktur.
    kart = src[src.index("Edge sağlığı · beş ölçüt"):]

    assert kart.index("${evSatir}") < kart.index("1 · Skor → sonuç"), "hüküm satırı kartın üstünde değil"
    assert 'ev.passed === 5 ? "pos"' in src, "yeşil ton 5/5'ten başka bir şeye bağlanmış"
    assert 'ev.unmeasured ? "warn"' in src, "ölçülemeyen varken uyarı tonuna düşülmüyor"


# =================================================================================================
# B2) YETKİ-DEĞİŞİM ALARMI
# =================================================================================================
def test_alarm_authority_NOTIFY_TOKENS_a_TURETMEYLE_girer():
    """El listesi değil TÜRETME: yeni bir ALARM_ sabiti eklemek kapsamı kendiliğinden büyütmeli.
    (v98'deki donmuş literal ayrıca KAZARA kaymayı yakalar — ikisi farklı işler.)"""
    assert obs.ALARM_AUTHORITY == "AUTHORITY_CHANGE"
    assert obs.ALARM_AUTHORITY in obs.NOTIFY_TOKENS

    consts = {v for k, v in vars(obs).items() if k.startswith("ALARM_") and isinstance(v, str)}
    assert consts == obs.NOTIFY_TOKENS


def _terfi_defteri(destekle_n=20, karsi_n=15, karsi_r=0.0) -> None:
    """Terfi kuralını (>=30 çift · her kovada >=8 · Rfark>=0.3) GERÇEKTEN dolduran defter."""
    plans, trades = [], []
    for i in range(destekle_n):
        plans.append({"id": f"P-D{i}", "llm_opinion": "destekle", "date": "2026-07-27"})
        trades.append({"plan_id": f"P-D{i}", "r_multiple": 1.0})
    for i in range(karsi_n):
        plans.append({"id": f"P-K{i}", "llm_opinion": "karşı", "date": "2026-07-27"})
        trades.append({"plan_id": f"P-K{i}", "r_multiple": karsi_r})
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)


def _authority_olaylari() -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("alarm") == obs.ALARM_AUTHORITY]


def test_yetki_KAZANIMI_alarm_uretir(sandbox_state):
    _terfi_defteri()

    out = analytics.llm_opinion_calibration()

    assert out["promoted"] is True
    ev = _authority_olaylari()
    assert len(ev) == 1 and ev[0]["level"] == "alarm"
    assert "AÇILDI" in ev[0]["message"]
    assert ev[0]["promoted"] is True and ev[0]["n"] == 35 and ev[0]["r_gap"] == 1.0


def test_yetki_KAYBI_da_ayni_yukseklikte_alarm_uretir(sandbox_state):
    """Kayıp, kazanım kadar operatörü ilgilendirir: sessizce geri alınan bir yetki 'danışman hâlâ
    konuşuyor' sanısını bırakır ve kimse aramaz."""
    _terfi_defteri()
    analytics.llm_opinion_calibration()                  # False → True
    _terfi_defteri(karsi_r=0.9)                          # R farkı 0.1 < 0.3 → terfi düşer

    out = analytics.llm_opinion_calibration()

    assert out["promoted"] is False
    ev = _authority_olaylari()
    assert len(ev) == 2 and "GERİ ALINDI" in ev[1]["message"]
    assert ev[1]["promoted"] is False


def test_flip_YOKKEN_alarm_YOK(sandbox_state):
    """Alarm bir KENAR sinyalidir. Her turda yeniden basılsaydı 6 saatlik susturma penceresi
    dolar ve gerçek bir devir sırasında kanal zaten susmuş olurdu."""
    _terfi_defteri()
    analytics.llm_opinion_calibration()
    analytics.llm_opinion_calibration()
    analytics.llm_opinion_calibration()

    assert len(_authority_olaylari()) == 1


def test_alarm_satiri_ham_jetonu_TASIR(sandbox_state, capsys):
    """monitoring.sh düz altdizge arar: jeton basılan satırda GÖRÜNMELİ."""
    _terfi_defteri()
    analytics.llm_opinion_calibration()

    assert "AUTHORITY_CHANGE" in capsys.readouterr().out


# =================================================================================================
# C2) BAR ARŞİVİ — Faz 5 kanıt birikiminin ilk taşı
# =================================================================================================
BAR = {"AAPL": {"o": 1.0, "h": 1.2, "l": 0.9, "c": 1.1, "v": 100, "t": "2026-07-27T13:31:00Z"}}


@pytest.fixture(autouse=True)
def _arsiv_bayragini_sifirla(monkeypatch):
    """`_WARNED` süreç-globaldır (süreç başına TEK uyarı kuralı). Testler arası sızarsa ikinci
    test kendi kurmadığı bir sessizliği ölçer ve GEÇER — ölçtüğü şey sızıntı olur."""
    monkeypatch.setattr(bararchive, "_WARNED", False)


def _gun_dosyasi(sandbox, gun: str):
    return sandbox / bararchive.ARCHIVE_DIR / f"{gun}.jsonl"


def test_cerceve_UTC_gununun_dosyasina_yazilir(sandbox_state):
    assert bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00") is True

    rows = store.read_jsonl(f"{bararchive.ARCHIVE_DIR}/2026-07-27.jsonl")
    assert len(rows) == 1
    assert rows[0] == {"ts": "2026-07-27T13:31:00+00:00", "bars": BAR}


def test_ayni_gunun_ikinci_cercevesi_AYNI_dosyaya_eklenir(sandbox_state):
    bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00")
    bararchive.archive_frame({"MSFT": {"c": 9.0}}, "2026-07-27T19:59:00+00:00")

    rows = store.read_jsonl(f"{bararchive.ARCHIVE_DIR}/2026-07-27.jsonl")
    assert [r["ts"][11:19] for r in rows] == ["13:31:00", "19:59:00"]
    assert len(list((sandbox_state / bararchive.ARCHIVE_DIR).glob("*.jsonl"))) == 1


def test_ny_seansi_TEK_utc_gunune_duser(sandbox_state):
    """13:30-20:00 UTC penceresi bir gün sınırını asla kesmez — bu yüzden UTC dilimi yeterlidir
    ve saat dilimi/DST bağımlılığı eklemeye gerek yoktur."""
    for ts in ("2026-07-27T13:30:00+00:00", "2026-07-27T20:00:00+00:00"):
        bararchive.archive_frame(BAR, ts)

    assert [p.stem for p in (sandbox_state / bararchive.ARCHIVE_DIR).glob("*.jsonl")] == ["2026-07-27"]


def test_kapaliyken_False_doner_ve_DOSYA_OLUSMAZ(sandbox_state, monkeypatch):
    monkeypatch.setattr(bararchive, "ENABLED", False)

    assert bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00") is False
    assert not (sandbox_state / bararchive.ARCHIVE_DIR).exists()


def test_bos_cerceve_ya_da_damgasiz_cagri_dosya_URETMEZ(sandbox_state):
    assert bararchive.archive_frame({}, "2026-07-27T13:31:00+00:00") is False
    assert bararchive.archive_frame(BAR, "") is False
    assert bararchive.archive_frame(BAR, "2026") is False
    assert not (sandbox_state / bararchive.ARCHIVE_DIR).exists()


def test_retention_YENI_GUN_yaziminda_eski_dosyalari_siler(sandbox_state):
    """Budama yalnız gün dosyası İLK kez yazılırken koşar: her çerçevede dizin taramak dakikalık
    yolda gereksiz G/Ç olurdu."""
    d = sandbox_state / bararchive.ARCHIVE_DIR
    d.mkdir(parents=True)
    eski = "2026-01-01"                                  # 120 günden eski
    taze = "2026-07-01"                                  # sınırın içinde
    for g in (eski, taze):
        (d / f"{g}.jsonl").write_text('{"ts": "x", "bars": {}}\n')
    (d / "notlar.txt").write_text("silinmemeli")

    bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00")

    kalan = sorted(p.name for p in d.iterdir())
    assert kalan == ["2026-07-01.jsonl", "2026-07-27.jsonl", "notlar.txt"]
    pruned = [e for e in store.read_jsonl("events.jsonl") if e["event"] == "bar_archive_pruned"]
    assert len(pruned) == 1 and pruned[0]["removed"] == 1


def test_retention_tarih_ADI_TASIMAYAN_dosyaya_dokunmaz(sandbox_state):
    """Yabancı bir dosyayı silmek, retention'ın konusu olmayan veriyi kaybetmek olurdu."""
    d = sandbox_state / bararchive.ARCHIVE_DIR
    d.mkdir(parents=True)
    (d / "elle-not.jsonl").write_text("{}\n")

    bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00")

    assert (d / "elle-not.jsonl").exists()


def test_ayni_gunun_ikinci_cercevesi_retention_KOSTURMAZ(sandbox_state):
    bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00")
    (sandbox_state / bararchive.ARCHIVE_DIR / "2026-01-01.jsonl").write_text("{}\n")

    bararchive.archive_frame(BAR, "2026-07-27T13:32:00+00:00")

    assert (sandbox_state / bararchive.ARCHIVE_DIR / "2026-01-01.jsonl").exists()


class _PatlayanStore:
    """`store` cephesinin yalnız yazma yüzeyi patlar — obs'un KENDİ store'u sağlam kalır, yoksa
    uyarının kendisi de kaybolur ve testin ölçtüğü şey belirsizleşirdi."""

    @staticmethod
    def append_jsonl(name, row):
        raise OSError("disk dolu")


def test_yazma_patlarsa_False_doner_ve_SUREC_BASINA_TEK_uyarir(sandbox_state, monkeypatch):
    """Arşiv arızası ingest'i ASLA düşüremez; ama sessiz de kalamaz. Dakikalık akışta her karede
    bir uyarı basmak olay defterini — bütün makullük dedektörlerinin okuduğu kaynağı — boğardı."""
    monkeypatch.setattr(bararchive, "store", _PatlayanStore)

    assert bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00") is False
    assert bararchive.archive_frame(BAR, "2026-07-27T13:32:00+00:00") is False
    assert bararchive.archive_frame(BAR, "2026-07-28T13:32:00+00:00") is False

    uyari = [e for e in store.read_jsonl("events.jsonl") if e["event"] == "bar_archive_failed"]
    assert len(uyari) == 1 and uyari[0]["level"] == "warn"


def test_retention_arizasi_YAZILMIS_cerceveyi_kaybettirmez(sandbox_state):
    """Budama bir TEMİZLİKTİR: başarısız olması, diske DÜŞMÜŞ bir çerçeveyi 'yazılmadı' diye
    raporlamamalı. Arıza gerçekçi biçimde kurulur (silinemeyen bir yol) — `_retention`ı doğrudan
    patlatmak, tam da sınanmak istenen iç sigortayı atlardı."""
    d = sandbox_state / bararchive.ARCHIVE_DIR
    (d / "2026-01-01.jsonl").mkdir(parents=True)          # eski görünüyor ama unlink edilemez

    assert bararchive.archive_frame(BAR, "2026-07-27T13:31:00+00:00") is True

    assert store.read_jsonl(f"{bararchive.ARCHIVE_DIR}/2026-07-27.jsonl"), "çerçeve kayboldu"
    hata = [e for e in store.read_jsonl("events.jsonl") if e["event"] == "bar_archive_retention_failed"]
    assert len(hata) == 1 and "veri kaybı YOK" in hata[0]["detail"]


def test_YASA6_dinamik_adli_artefakt_ihlal_URETMEZ():
    """C2 kaleminin ölçülmüş bulgusu: statik graf f-string ile kurulan TARİHLİ adı ÇÖZEMEZ, o
    yüzden artefakt olarak hiç görünmez — `DECLARED_SINKS`'e satır EKLENEMEZ (ölü muafiyet olur)
    ve GEREKMEZ (graf 'ihlal' demiyor, 'göremiyorum' diyor ve bunu raporluyor)."""
    g = codelaw.artifact_graph()
    dinamik = [u for u in g["unresolved"] if u["file"].endswith("bararchive.py")]

    assert len(dinamik) == 1 and dinamik[0]["role"] == "writer"
    assert not [a for a in g["artifacts"] if a.startswith(bararchive.ARCHIVE_DIR)]
    assert bararchive.ARCHIVE_DIR not in codelaw.DECLARED_SINKS

    r = codelaw.report()
    assert r["ok"] is True, r


def test_watchdog_haritalarina_EKLENMEDI():
    """v102 kararının aynısı: arşiv yalnız NY seansında büyür. `DERIVED_SOURCES`'a bir satır
    eklemek, her akşam ve her hafta sonu SAHTE bayat alarmı üretirdi — gürültüyle susturulmuş bir
    dedektör dedektör değildir."""
    from meridian import watchdog

    assert not [k for k in watchdog.DERIVED_SOURCES if bararchive.ARCHIVE_DIR in k]


# ---- ingest_bars entegrasyonu ------------------------------------------------------------------
class _SahtePipe:
    def hset(self, *a, **k): pass
    def expire(self, *a, **k): pass
    def xadd(self, *a, **k): pass
    def execute(self): return []


class _SahteRedis:
    def pipeline(self): return _SahtePipe()


def test_ingest_bars_basarili_yazimdan_sonra_arsive_duser(sandbox_state, monkeypatch):
    """Redis mock'u ile GERÇEK çağrı yolu koşturulur — çağrı-yeri varlığını kaynak metinde
    doğrulamak zorunda kalmadık (v100 idiomu yedek olarak aşağıda ayrıca duruyor)."""
    from meridian import hotstate as hs
    monkeypatch.setattr(hs, "_redis", lambda: _SahteRedis())

    n = hs.ingest_bars({"AAPL": {"c": 1.1, "t": "2026-07-27T13:31:00Z"}})

    assert n == 1
    bugun = dt.datetime.now(dt.timezone.utc).date().isoformat()
    rows = store.read_jsonl(f"{bararchive.ARCHIVE_DIR}/{bugun}.jsonl")
    assert len(rows) == 1 and "AAPL" in rows[0]["bars"]


def test_yazilan_bar_YOKKEN_arsiv_cagrilmaz(sandbox_state, monkeypatch):
    """`t`si olmayan bar akışa girmez (look-ahead sözleşmesi); girmeyen bar kanıt da değildir."""
    from meridian import hotstate as hs
    monkeypatch.setattr(hs, "_redis", lambda: _SahteRedis())

    assert hs.ingest_bars({"AAPL": {"c": 1.1}}) == 0
    assert not (sandbox_state / bararchive.ARCHIVE_DIR).exists()


def test_arsiv_arizasi_INGEST_i_dusuremez(sandbox_state, monkeypatch):
    """Kanıt yan etkisi canlı hattı kesemez: arşiv patlasa bile yazılan sembol sayısı DÖNER ve
    Redis sağlığı yanlış-kırmızıya boyanmaz."""
    from meridian import hotstate as hs
    monkeypatch.setattr(hs, "_redis", lambda: _SahteRedis())
    monkeypatch.setattr(bararchive, "store", _PatlayanStore)
    hs._HEALTH.update(ok=True, down_since=None)

    assert hs.ingest_bars({"AAPL": {"c": 1.1, "t": "2026-07-27T13:31:00Z"}}) == 1
    assert hs._HEALTH["ok"] is True, "arşiv arızası Redis'i 'down' işaretledi"


def test_cagri_yeri_ingest_bars_in_ICINDE_ve_TRY_DISINDA():
    """v100 idiomu (kaynak metin kanıtı): çağrı `try` bloğunun İÇİNDE olsaydı bir arşiv/import
    arızası `_note_down`a düşer ve BAŞARILI bir yazımı 'Redis düştü' diye raporlardı."""
    from meridian import hotstate as hs
    src = inspect.getsource(hs.ingest_bars)

    assert "bararchive.archive_frame(bars, ts0)" in src
    assert src.index("except Exception as e:") < src.index("bararchive.archive_frame"), \
        "arşiv çağrısı try bloğunun içinde kalmış"


# =================================================================================================
# B1) NOUS_MODEL geçiş desteği — arayüz; kaldıraç operatörün
# =================================================================================================
def test_app_js_sozdizimi_gecerli():
    r = subprocess.run(["node", "--check", "meridian/web/app.js"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_nous_model_alani_ipucunu_ve_TEST_dugmesini_tasir():
    """Alan zaten vardı; eksik olan tek bir metin girişinin beyin çeşitliliği ölçümünü nasıl
    düzelttiğinin YAZILI olmasıydı. 4. eleman mevcut sır-alanı desenidir: `keyField` onu görünce
    Test düğmesini çıkarır."""
    src = open("meridian/web/app.js").read()
    satir = [s for s in src.splitlines() if s.strip().startswith('["NOUS_MODEL"')]

    assert len(satir) == 1, "NOUS_MODEL alanı listede yok ya da çoğaldı"
    assert "tencent/hy3:free" in satir[0]
    assert "beyin çeşitliliği ölçümü kendiliğinden düzelir" in satir[0]
    assert satir[0].rstrip().endswith('"nous"],'), "Test düğmesi sağlayıcıya bağlanmamış"


def test_nous_test_dugmesi_VAR_OLAN_uca_baglanir():
    """YENİ uç yazılmadı: /api/secrets/test/nous zaten hermes.ping_brain('nous') çağırıyor."""
    from meridian import api
    src = inspect.getsource(api.api_test_secret)

    assert 'provider in ("gemini", "nous")' in src and "ping_brain(provider)" in src
