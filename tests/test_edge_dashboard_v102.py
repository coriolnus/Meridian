"""test_edge_dashboard_v102.py — KENAR SAĞLIĞI: ÜRETİLEN ÖLÇÜM PANOYA ULAŞIYOR MU? (2026-07-27)

Bu turun dört kaleminin ortak sınıfı YASA 6'nın iki yüzü:

  1. `score_calibration.json` her P5 turunda ÜZERİNE yazılıyordu — panoda hep bugünün IC'si duruyor,
     dünkü hiç var olmamış gibi. "IC kaç?" cevaplanabiliyordu, "IC YÜKSELİYOR MU?" cevaplanamıyordu.
     Zaman serisi olmadan bir öğrenme iddiası ölçülemez; tek nokta bir trend değildir.
  2. `regime_edge.json` analytics tarafından HER P5'te yazılıyor ama HİÇBİR uçtan servis edilmiyordu
     (kanıt üretiliyor, tüketilmiyor — deponun adını koyduğu ihlal sınıfı).
  3. Tahmin↔gerçekleşen isabeti hiç ölçülmüyordu: `predicted_delta` neredeyse her satırda dolu,
     `realized_delta` yalnız terminal satırlarda. Tek başına ilkini saymak "35 tahmin ölçüldü" diye
     okunurdu — oysa ölçülen bir tane bile olmayabilir.
  4. Intraday sayaçları seans dışında 0'dır ve bu NORMALDİR; aynı sıfırı arıza gibi göstermek her
     akşam yanlış alarm üretir ve gerçek kesintiyi görünmez kılar.

İDEMPOTENSİN SEBEBİ (kalem 1): worker yeniden başlarsa aynı gün ikinci bir nokta düşerdi ve serinin
eğimi ölçümden değil SÜREÇ KAZALARINDAN gelirdi — kimse fark etmezdi, çünkü grafik yine güzel görünür.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from meridian import analytics, codelaw, store


# =================================================================================================
# 1) IC zaman serisi — bir gün bir nokta, tekrar YOK
# =================================================================================================
def _cal(rank_ic=-0.01, real_ic=None, n_real=95, n_cf=2102) -> dict:
    """`analytics.score_calibration()` çıktısının GERÇEK şeması (real/cf ayrık dilimler, 2026-07-26).
    Canlı `state/score_calibration.json` bu ayrımdan ÖNCEKİ turda yazıldığı için orada `real` yok —
    şema koda göre çivilenir, diskteki bayat kopyaya göre değil."""
    out = {"n": n_real + n_cf, "n_real": n_real, "n_cf": n_cf, "rank_ic": rank_ic,
           "quintiles": [], "real": None, "cf": None, "monotone_hint": False}
    if real_ic is not None:
        out["real"] = {"rank_ic": real_ic, "n": n_real, "anlamli": False, "se_yontem": "i.i.d._varsayimi"}
    return out


def test_ilk_nokta_yazilir_ve_alanlari_semadan_gelir(sandbox_state):
    """ŞEMA GENİŞLEDİ (2026-07-28, Aşama 1.1): seri artık ÜÇ katmanı da taşır. `cf_ic` eklenmeden
    önce grafik yalnız gerçek ve havuz çizgilerini çizebiliyordu; aradaki makasın NEREDEN geldiği
    (cf dilimi) her bakışta yeniden tahmin edilmek zorundaydı. `_cal` cf dilimi vermediği için
    burada dürüstçe None — ölçülmeyen alan sıfırla doldurulmaz."""
    assert analytics.record_score_calibration_point("2026-07-27", _cal(real_ic=0.12)) is True

    rows = store.read_jsonl(analytics.SCORE_CAL_HISTORY)
    assert len(rows) == 1
    assert rows[0] == {"date": "2026-07-27", "rank_ic": -0.01, "real_ic": 0.12, "cf_ic": None,
                       "n_real": 95, "n_cf": 2102}


def test_ayni_gun_ikinci_cagri_YAZMAZ(sandbox_state):
    """Worker restart'ı ya da aynı günün ikinci P5'i seriyi ÇOĞALTAMAZ — yoksa trendin eğimi
    ölçümden değil süreç kazalarından gelir ve grafik yine düzgün görünürdü."""
    assert analytics.record_score_calibration_point("2026-07-27", _cal(rank_ic=0.05)) is True
    assert analytics.record_score_calibration_point("2026-07-27", _cal(rank_ic=0.99)) is False

    rows = store.read_jsonl(analytics.SCORE_CAL_HISTORY)
    assert len(rows) == 1 and rows[0]["rank_ic"] == 0.05, "ikinci çağrı ilk noktayı ezdi"


def test_farkli_gun_yeni_nokta_ekler(sandbox_state):
    analytics.record_score_calibration_point("2026-07-26", _cal(rank_ic=0.01))
    assert analytics.record_score_calibration_point("2026-07-27", _cal(rank_ic=0.02)) is True

    rows = store.read_jsonl(analytics.SCORE_CAL_HISTORY)
    assert [r["date"] for r in rows] == ["2026-07-26", "2026-07-27"]


def test_gercek_dilim_yokken_real_ic_UYDURULMAZ(sandbox_state):
    """UYDURMA YASAĞI: gerçek dilim <30 iken `real` None'dır. Havuzlanmış IC'yi oraya kopyalamak
    sim ağırlıklı bir sayıyı 'gerçek ölçüm' diye kaydetmek olurdu."""
    analytics.record_score_calibration_point("2026-07-27", _cal(rank_ic=-0.0095, real_ic=None))

    row = store.read_jsonl(analytics.SCORE_CAL_HISTORY)[0]
    assert row["real_ic"] is None and row["rank_ic"] == -0.0095


def test_bos_tarih_ya_da_bos_kalibrasyon_satir_uretmez(sandbox_state):
    assert analytics.record_score_calibration_point("", _cal()) is False
    assert analytics.record_score_calibration_point("2026-07-27", None) is False
    assert store.read_jsonl(analytics.SCORE_CAL_HISTORY) == []


def test_p5_dongusu_noktayi_gercekten_dusuruyor():
    """YASA 6: fonksiyon var olmak yetmez, ÇAĞRILMASI gerekir. Kablolanmamış bir kaydedici
    sonsuza kadar boş bir seri üretir ve pano 'veri birikmedi' der — sebebi görünmeden."""
    import inspect

    from meridian import loop
    src = inspect.getsource(loop.daily_cycle)
    assert "record_score_calibration_point" in src, "P5 bloğu noktayı düşürmüyor"


# =================================================================================================
# 2) Tahmin isabeti — ikisi de ölçülü satırlar
# =================================================================================================
def _hyp(pid, predicted=None, realized=None) -> dict:
    r = {"id": pid, "variable": "entry.min_score"}
    if predicted is not None:
        r["predicted_delta"] = predicted
    if realized is not None:
        r["realized_delta"] = realized
    return r


def test_bos_defter_dururst_bos_doner(sandbox_state):
    assert analytics.prediction_hit_rate() == {"n": 0, "sign_hits": None, "mean_abs_err": None}


def test_yalniz_tahmini_olan_satirlar_SAYILMAZ(sandbox_state):
    """Canlı defterin bugünkü hâli tam olarak bu: 35 satırın 35'inde tahmin var, 1'inde
    gerçekleşen. `predicted_delta`yı tek başına saymak '35 tahmin ölçüldü' diye okunurdu."""
    store.write_jsonl("hypotheses.jsonl", [_hyp("H1", 0.03), _hyp("H2", 0.03), _hyp("H3", -0.01)])

    out = analytics.prediction_hit_rate()

    assert out == {"n": 0, "sign_hits": None, "mean_abs_err": None}


def test_isaret_ve_ortalama_hata_dogru_sayilir(sandbox_state):
    store.write_jsonl("hypotheses.jsonl", [
        _hyp("H1", 0.10, 0.20),      # + / + → tutar, |hata| 0.10
        _hyp("H2", -0.10, -0.05),    # − / − → tutar, |hata| 0.05
        _hyp("H3", 0.10, -0.30),     # + / − → TUTMAZ, |hata| 0.40
        _hyp("H4", 0.05),            # gerçekleşen yok → sayılmaz
        _hyp("H5", None, 0.02),      # tahmin yok  → sayılmaz
    ])

    out = analytics.prediction_hit_rate()

    assert out["n"] == 3 and out["sign_hits"] == 2
    assert out["mean_abs_err"] == round((0.10 + 0.05 + 0.40) / 3, 4)


def test_sifir_tahmin_sifir_sonuc_ISABETTIR(sandbox_state):
    """0 kendi başına bir işarettir: 'değişmeyecek' dedik ve değişmediyse bu bir isabettir.
    >0/<0 ile aynı kefeye konsaydı sıfır tahminler ya hep tutar ya hep tutmaz görünürdü."""
    store.write_jsonl("hypotheses.jsonl", [_hyp("H1", 0.0, 0.0), _hyp("H2", 0.0, 0.4)])

    out = analytics.prediction_hit_rate()

    assert out["n"] == 2 and out["sign_hits"] == 1


def test_bicimsiz_satir_paydayi_sismez(sandbox_state):
    """Bozuk bir satır ölçümün DIŞINDA kalır; paydaya girseydi isabet oranı sessizce seyrelirdi."""
    store.write_jsonl("hypotheses.jsonl", [_hyp("H1", "iki", "üç"), _hyp("H2", 0.1, 0.2)])

    out = analytics.prediction_hit_rate()

    assert out["n"] == 1 and out["sign_hits"] == 1


# =================================================================================================
# 3) Uç sözleşmesi — /api/diagnostics BEŞ ölçütü de taşır (5. ölçüt KUYRUK: Hafta 3a)
# =================================================================================================
@pytest.fixture
def client(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    return TestClient(api.app)


def test_diagnostics_dort_olcutu_de_servis_eder(client):
    d = client.get("/api/diagnostics")
    assert d.status_code == 200
    ml = d.json()["mlops"]
    for k in ("score_calibration_history", "regime_edge", "benchmark_relative", "prediction_hit"):
        assert k in ml, f"{k} uçtan servis edilmiyor — kanıt üretiliyor, tüketilmiyor"


def test_bos_state_500_URETMEZ_ve_seri_bos_liste_doner(client):
    """Boş sandbox: ölçülmeyen None/[] döner, uç ÇÖKMEZ. (numpy sigortası ayrı bir yasa;
    bu regresyon kilidi yeni alanların o sigortayı delmediğini söyler.)"""
    ml = client.get("/api/diagnostics").json()["mlops"]

    assert ml["score_calibration_history"] == []
    assert ml["regime_edge"] is None
    assert ml["benchmark_relative"] is None
    assert ml["prediction_hit"] == {"n": 0, "sign_hits": None, "mean_abs_err": None}


def test_seri_yazilinca_uc_onu_tasir_ve_son_60_ile_sinirlidir(client):
    for i in range(70):
        analytics.record_score_calibration_point(f"2026-05-{i + 1:03d}", _cal(rank_ic=i / 100))

    hist = client.get("/api/diagnostics").json()["mlops"]["score_calibration_history"]

    assert len(hist) == 60 and hist[-1]["rank_ic"] == 0.69, "pencere sonu değil başı kırpılmış"


def test_intraday_silahli_plan_sayisi_bayraktan_AYRI_servis_edilir(client):
    """`intraday.armed` operatörün Faz 4b bayrağıdır (bool); silahlı plan SAYISI bambaşka bir
    olgudur. İkisi tek alana sıkışsaydı 'silahsız seans' ile 'bayrak kapalı' aynı görünürdü."""
    store.write_json("portfolio.json", {"armed": [{"ticker": "AAA"}, {"ticker": "BBB"}]})

    iq = client.get("/api/diagnostics").json()["intraday"]

    assert iq["armed_plans"] == 2
    assert iq["armed"] is False, "bayrak ile plan sayısı aynı alana çöktü"
    assert iq["decisions"]["today"] == 0 and iq["decisions"]["total"] == 0


def test_bugunun_karar_sayisi_toplamdan_ayri_sayilir(client, monkeypatch):
    """Ömür boyu toplam 'bugün akış çalıştı mı?' sorusunu ASLA cevaplayamaz — dünkü 400 satır
    bugünkü sessizliği gizler."""
    store.write_json("data_quality.json", {"date": "2026-07-27"})
    store.write_jsonl("intraday_decisions.jsonl", [
        {"ts": "2026-07-26T15:00:00+00:00", "ticker": "AAA", "fired": True},
        {"ts": "2026-07-27T15:00:00+00:00", "ticker": "BBB", "fired": False},
        {"ts": "2026-07-27T15:01:00+00:00", "ticker": "CCC", "fired": True},
    ])

    dec = client.get("/api/diagnostics").json()["intraday"]["decisions"]

    assert dec["total"] == 3 and dec["today"] == 2 and dec["fired"] == 2
    assert dec["recent"][0]["ticker"] == "CCC", "son karar en yeni satır değil"


# =================================================================================================
# 4) Pano gerçekten tüketiyor mu — "gösteriliyor" kanıtlanabilir olmalı
# =================================================================================================
def test_app_js_sozdizimi_gecerli():
    r = subprocess.run(["node", "--check", "meridian/web/app.js"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("alan", [
    "score_calibration_history", "regime_edge", "benchmark_relative", "prediction_hit",
    "sign_hits", "mean_abs_err", "real_ic", "excess_return", "armed_plans", "legacy_ships",
])
def test_yeni_alanlarin_panoda_tuketicisi_var(alan):
    """YASA 6: üretilen alan tüketilir. 'Panoda gösteriliyor' gerekçesi, app.js taranarak
    KANITLANABİLİR olmadıkça gerekçe değildir."""
    assert codelaw.dashboard_mentions(alan), f"{alan} hiçbir panoda okunmuyor"


def test_yeni_kartlar_bolum3_kompozisyonuna_gercekten_giriyor():
    """Kart dizgesini tanımlayıp innerHTML'e EKLEMEMEK sessiz bir ölü koddur: testler geçer,
    ekranda hiçbir şey görünmez."""
    src = open("meridian/web/app.js").read()
    for kart in ("Edge sağlığı · beş ölçüt", "Öğrenme çarkı · hipotez hunisi", "Intraday · Faz 4a gözlem"):
        assert kart in src, f"{kart} kartı yok"
    # Hafta 3a: EDGE kartının hemen YANINA ikizi (sSonuc = dolar merceği) ve ısı+doğrulama kartı
    # girdi. Sıra anlam taşır — SONUÇ hükmü EDGE'in ikizidir ve okunma yeri onun yanıdır.
    # Hafta 3b (2026-07-30): doğrulama kartından SONRA iki kart daha girdi — `sHermes` (H1-H3
    # karnesi + MAE + gölge-varyant) ve `sY3` (rejim/risk dörtlüsü + 2C küçültme + 2D rotasyon).
    # SIRA ANLAM TAŞIR: karne doğrulamanın hemen ardından okunur (ikisi de "bu hükme ne kadar
    # güvenebiliriz?" sorusunun katmanlarıdır), Y3 ondan sonra çünkü risk okuması karneye dayanır.
    # NOUS SİSTEM-DEĞERLENDİRME (2026-07-30): `sNous` kartı `sHermes`in HEMEN ARDINA girdi ve sıra
    # yine anlam taşır — karne "beyin PARAMETRE tahminlerinde ne kadar isabetli?", sistem önerileri
    # bir ÜST katman ("beyin MEKANİZMALAR hakkında ne görüyor?"). İkisi yan yana durunca kendini
    # geliştirme döngüsü tek bakışta okunur; araya başka bir kart girse zincir kopardı.
    assert ("${s1}${s2}${s3}${sEdge}${sSonuc}${sDogrulama}${sHermes}${sNous}${sY3}"
            "${sSelale}${sCark}${sIntra}${s4}${s5}${s6}") in src, \
        "yeni kartlar sayfa kompozisyonuna girmedi — tanımlı ama ölü"
    for kart in ("Hermes karnesi", "Y3 rejim/risk dörtlüsü", "Sistem önerileri"):
        assert kart in src, f"{kart} kartı yok"


def test_yeni_artefakt_YASA6_ihlali_uretmez():
    """Yeni bir state dosyası, DIŞ bir modül tarafından okunmadıkça 'yazılıyor ama okunmuyor'
    ihlalidir. `integrity_registry` bileşen×desen kaydıdır (dosya başına beyan içermez), o yüzden
    beyan edilecek tek yer codelaw'un artefakt grafiğidir — ve orada muafiyet değil GERÇEK bir
    okuyucu gerekiyor."""
    g = codelaw.artifact_graph()
    rec = g["artifacts"][analytics.SCORE_CAL_HISTORY]

    assert "api.py" in rec["external_readers"], "seriyi hiçbir dış modül okumuyor"
    assert analytics.SCORE_CAL_HISTORY not in g["violations"]
    assert analytics.SCORE_CAL_HISTORY not in codelaw.DECLARED_SINKS, \
        "gerçek okuyucusu olan bir artefakt lağım listesine yazılmış (stale_sink)"
    assert g["violations"] == [] and g["stale_sinks"] == []


def test_seri_satiri_json_serilestirilebilir(sandbox_state):
    """numpy sigortası regresyonu: kalibrasyon çıktısı np.float64 taşıyabilir; diskte NaN/np tipi
    kalırsa hem `json.dumps` hem tarayıcının `JSON.parse`ı düşer (uç 500'e gider)."""
    import numpy as np

    analytics.record_score_calibration_point(
        "2026-07-27", {"rank_ic": np.float64(0.12), "n_real": np.int64(31), "n_cf": 2000,
                       "real": {"rank_ic": np.float64(float("nan")), "n": 31}})

    raw = (sandbox_state / analytics.SCORE_CAL_HISTORY).read_text().strip()
    row = json.loads(raw)
    assert row["rank_ic"] == pytest.approx(0.12) and row["n_real"] == 31
    assert row["real_ic"] is None, "NaN 'ölçüldü' gibi diske düştü"
