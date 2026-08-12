"""test_para_v3_borclari_v145.py — PARA-v3'ün İKİ ÖLÇÜM BORCU (WP-M, 2026-08-01).

Bu tur YASA DEĞİŞTİRMEZ. PARA-v3 skoru bugüne kadarki TÜM ölçüm hükümlerinin ortak cetvelidir;
karar değişkeni değişirse eski hükümler kıyaslanamaz hâle gelir. İki borç bu yüzden EK ALAN olarak
gelir ve mevcut hiçbir sayıya dokunmaz:

  ① `shadowlaw.realized_usd` → `money_score_detail`in `realized_usd` bloğu. Karar skoru
     kıs([-1,+1])'tir; kırpılma bölgesinde para hareket eder ama skor DONAR. Ayrıca rollback'in
     yazdığı `realized_delta` hâlâ BİLEŞİK ölçektedir (probgate'in `olcek_borcu` beyanı) — iki
     ölçeği bağlayabilecek tek ortak cetvel kırpılmamış DOLAR'dır.
  ② `backtest.mtm_dd_veto` → `walk_forward`ın `mtm_dd_veto` bloğu. Günlük M2M eğrisinin tepe-altı
     düşüşü, `score_detail` onu kapanmış-işlem eğrisiyle BİRLEŞTİRMEDEN önce ayrı bir sayı olarak.
     EDG-2026-003 kill#2'nin "kapalı %9,7 / M2M %12,9" bulgusunun kalıcı hâli. VETO ADI TAŞIR AMA
     HÜKÜM VERMEZ — kapının kendi düşüş vetosu (`reflect._gate_eval`, aday↔incumbent FARKI)
     değişmedi ve bu bloktan hiçbir girdi almaz.

BU DOSYANIN ÇİVİLERİ:
  ⓐ GERİYE-UYUM: bilinen fikstürde `money_score_detail`in ESKİ alanları BİT-BİT aynı (hem sabit
     literallerle hem yasanın kendi formülünden bağımsız türetmeyle).
  ⓑ YAPISAL ÖZDEŞLİK: `skor_usd` ile karar skoru AYNI sayıdır — blok yeni bir yasa DEĞİL, aynı
     yasanın kırpılmamış ikizidir. Ayrışırsa biri sessizce başka bir şey ölçüyor demektir.
  ⓒ UYDURMA YASAĞI: `pnl_dollars`sız defterde dolar None + NEDEN; boş M2M eğrisinde `ihlal` None
     (False DEĞİL — hiç bakılmamış koşula temiz kâğıdı verilmez).
  ⓓ YASA 6: her iki blok da GERÇEK bir okuyucuya bağlı.

HİÇBİR TEST CANLI STATE'E YAZMAZ: tümü salt-okuma ya da bellek-içi fikstür.
"""
from __future__ import annotations

import inspect
import json

import pytest

from meridian import analytics, backtest, config, reflect, score as score_mod, shadowlaw
from tests import wf_fixtures as wf
from tests.conftest import make_bars

# =================================================================================================
# PARA-v3 ÖLÇÜM TABANI DONMUŞ (2026-08-13)
# =================================================================================================
# Bu dosyanın fikstürleri 2026-07-30'un PARA-v3 ölçümüne kalibre: `max_drawdown=0,08` →
# `DD_VETO_MARGIN=0,04`, ve sentetik eğrilerin ihlal-günü sayıları/örnekleri o eşikten türetildi
# (ör. 102k seviyesi %7,3 düşüşle 0,04'ün ÜSTÜ, 0,08'in ALTI — marj değişince aynı eğri farklı
# sayıda ihlal üretir). Operatör 2026-08-13'te bütçeyi 0,16'ya çıkardı; canlı sabitler okunsaydı
# bu dosya OPERATÖRÜN RİSK İŞTAHINA bağlı olurdu — oysa ölçtüğü şey PARA-v3 YASASI (blok eşiği
# ödünç alır mı, m2m ihlali hükme girer mi, geriye-uyum korunuyor mu).
# YASANIN KENDİSİ AYRICA ÇİVİLİ: marj↔bütçe bağı `test_para_yasasi_v127` ve
# `test_dalga_w1_v216::test_C5_dd_veto_margin_goalun_TAM_YARISIDIR` tarafından CANLI değere karşı
# sınanır — yani bu dondurma bir körlük yaratmaz, yalnız tarihsel tabanı tarihsel tutar.
@pytest.fixture(autouse=True)
def _para_v3_olcum_tabani(monkeypatch):
    monkeypatch.setattr(shadowlaw, "DD_VETO_MARGIN", 0.04)
    monkeypatch.setattr(reflect, "DD_VETO_MARGIN", 0.04)
    _ger = config.goal()

    def _donmus_goal():
        return {**_ger, "max_drawdown": 0.08}
    # `cache_clear` ŞART: gerçek `config.goal` lru_cache'lidir ve `sandbox_state` fixture'ı her
    # kurulumda onu çağırır — yerine konan sade fonksiyonda o alan yoksa TÜM dosya setup'ta patlar.
    _donmus_goal.cache_clear = lambda: None
    monkeypatch.setattr(config, "goal", _donmus_goal)



# Ölçümün penceresi ELLE sabitlenir: `_span_days` fikstürün kendi kümelenmesinden türetseydi
# beklenen sayılar fikstür gürültüsüyle birlikte kayardı ve "elle hesaplı" iddiası çökerdi.
SPAN = 335.0
BASLANGIC = 100_000.0


def _goal():
    return config.goal()


def _fikstur(n=40, seed=1145):
    return wf.trades(n, seed=seed, lo="2024-01-01", hi="2024-12-01", r_mu=0.35)


# =================================================================================================
# ① realized_usd — ELLE HESAPLI FİKSTÜR
# =================================================================================================
def test_realized_usd_bloku_ELLE_HESAPLANAN_dolarla_birebir():
    """Blok, defterin `pnl_dollars` toplamını ve pencere-eşlenik DOLAR hedefini doğru kurar.

    Beklenen değerler bu testin İÇİNDE yeniden türetilir (uygulamanın çıktısı kopyalanmaz):
        hedef_usd = ((1+%25)^(span/365) − 1) × başlangıç_sermayesi
        ham_oran  = Σ pnl_dollars / hedef_usd
    Uygulama bir gün başka bir paydaya kayarsa bu türetme onu yakalar."""
    ts = _fikstur()
    beklenen_pnl = round(sum(float(t["pnl_dollars"]) for t in ts), 2)
    beklenen_hedef = ((1.0 + 0.25) ** (SPAN / 365.0) - 1.0) * BASLANGIC
    beklenen_oran = beklenen_pnl / beklenen_hedef

    b = shadowlaw.realized_usd(ts, span_days=SPAN)

    assert b["olculdu"] is True and b["neden"] is None
    assert b["pnl_usd"] == beklenen_pnl == 9731.11        # elle sabit: fikstür sürüklenirse kırılır
    assert b["hedef_usd"] == pytest.approx(beklenen_hedef, abs=0.01) == pytest.approx(22728.32,
                                                                                      abs=0.01)
    assert b["ham_oran"] == pytest.approx(beklenen_oran, abs=1e-6)
    assert b["n_islem"] == b["n_pnl"] == 40 and b["n_eksik"] == 0 and b["tam_kapsam"] is True
    assert b["birim"] == "USD" and b["start_equity"] == BASLANGIC
    assert b["hukum_verir"] is False, "rapor bloğu hüküm veriyor gibi etiketlenmiş"


def test_realized_usd_pnl_dollars_YOKSA_None_ve_NEDEN_sifir_DEGIL():
    """UYDURMA YASAĞI: dolar ölçülemiyorsa 0.0 yazmak, ölçülmemişi 'başabaş' diye raporlamaktır."""
    ts = [{k: v for k, v in t.items() if k != "pnl_dollars"} for t in _fikstur()]
    b = shadowlaw.realized_usd(ts, span_days=SPAN)
    assert b["olculdu"] is False
    assert b["pnl_usd"] is None and b["skor_usd"] is None and b["ham_oran"] is None
    assert b["kirpildi"] is None, "ölçülemeyen defterde kırpılma hükmü verilmiş"
    assert b["neden"] and "ÖLÇÜLEMEDİ" in b["neden"], f"neden yazılmamış: {b['neden']}"
    assert b["n_pnl"] == 0 and b["n_eksik"] == 40 and b["tam_kapsam"] is False

    # boş defter de ölçülemedi demektir (sıfır değil) — ve nedeni AYRI cümleyle söyler
    bo = shadowlaw.realized_usd([], span_days=SPAN)
    assert bo["olculdu"] is False and bo["pnl_usd"] is None and "boş" in bo["neden"]


def test_realized_usd_KISMI_eksikte_olcer_ama_EKSIKLIGI_BEYAN_eder():
    """`score.equity_curve` eksik `pnl_dollars`ı sessizce 0 sayıyor. Blok aynı toplamı üretebilir
    ama SESSİZ KALAMAZ: kaç satırın düştüğü adıyla çıktıdadır (YASA 4 sınıfı)."""
    ts = _fikstur()
    kirli = [dict(t) for t in ts]
    kirli[0].pop("pnl_dollars")
    kirli[1]["pnl_dollars"] = "abc"          # biçimsiz → sayılamaz, ama SAYILIR (n_eksik)
    b = shadowlaw.realized_usd(kirli, span_days=SPAN)
    assert b["olculdu"] is True
    assert b["n_pnl"] == 38 and b["n_eksik"] == 2 and b["tam_kapsam"] is False
    assert b["neden"] and "2/40" in b["neden"] and "EKSİK" in b["neden"]
    assert b["pnl_usd"] == round(sum(float(t["pnl_dollars"]) for t in ts[2:]), 2)


def test_realized_usd_KIRPILMA_bayragi_skorun_KOR_oldugu_bolgeyi_gosterir():
    """Bloğun asıl bilgi katkısı burada: karar skoru 1,0'da DONAR, para donmaz.

    İki defter — biri hedefin 2 katı, diğeri 4 katı para kazanıyor. Karar skoru İKİSİNDE DE 1,0
    (kırpılma). `pnl_usd` ikisini AYIRIR ve `kirpildi=True` "bu skorun ötesinde para hareket
    ediyor ama karar değişkeni kör" der. `realized_delta` çelişkilerinin doğduğu bölge tam burası."""
    ts = _fikstur()
    hedef_usd = ((1.0 + 0.25) ** (SPAN / 365.0) - 1.0) * BASLANGIC
    olcek = hedef_usd * 2.0 / sum(float(t["pnl_dollars"]) for t in ts)
    iki = [{**t, "pnl_dollars": round(float(t["pnl_dollars"]) * olcek, 2)} for t in ts]
    dort = [{**t, "pnl_dollars": round(float(t["pnl_dollars"]) * olcek * 2.0, 2)} for t in ts]

    g = {**_goal(), "min_sample": 1}
    assert shadowlaw.money_score(iki, g, span_days=SPAN) == 1.0
    assert shadowlaw.money_score(dort, g, span_days=SPAN) == 1.0, "fikstür kırpılma bölgesinde değil"

    b2 = shadowlaw.realized_usd(iki, span_days=SPAN)
    b4 = shadowlaw.realized_usd(dort, span_days=SPAN)
    assert b2["kirpildi"] is True and b4["kirpildi"] is True
    assert b2["skor_usd"] == b4["skor_usd"] == 1.0, "kırpılmış ikiz kırpılmıyor"
    # ...ama HAM taraf iki defteri AYIRIR — körlüğün panzehiri budur
    assert b4["pnl_usd"] == pytest.approx(2.0 * b2["pnl_usd"], rel=1e-3)
    assert b4["ham_oran"] > b2["ham_oran"] > 1.0

    # temiz (kırpılmayan) defterde bayrak inik olmalı — bayrak her zaman True dönmüyor
    assert shadowlaw.realized_usd(ts, span_days=SPAN)["kirpildi"] is False


def test_skor_usd_karar_skoruyla_YAPISAL_OZDES():
    """ÇİVİ ⓑ: `skor_usd` = kıs(Σpnl/başlangıç / hedef_pencere) = `ret_c_v3`. Blok İKİNCİ BİR YASA
    DEĞİL, aynı yasanın kırpılmamış ikizidir; ayrışırsa biri sessizce başka bir şey ölçüyordur.

    Tolerans 1e-3: karar yolu `score_detail`in 4 haneye YUVARLANMIŞ `total_return`ünü okur, blok
    ham toplamı — fark yalnız o yuvarlamadır ve büyümesi bir kayma işaretidir."""
    for n, seed in ((40, 1145), (55, 7), (31, 99)):
        ts = wf.trades(n, seed=seed, lo="2024-01-01", hi="2024-12-01", r_mu=0.2)
        d = shadowlaw.money_score_detail(ts, {**_goal(), "min_sample": 1}, span_days=SPAN)
        assert d["realized_usd"]["skor_usd"] == pytest.approx(d["score"], abs=1e-3), \
            f"para ikizi karar skorundan ayrıştı (n={n})"


def test_realized_usd_min_sample_ALTINDA_da_doner_skor_None_iken():
    """"Skor yok" ile "para yok" AYNI cümle değildir. Rollback meta-kalibrasyonunun okumak istediği
    ayrım tam budur: skor min_sample altında ÖLÇÜLEMEZ ama defterin dolarları ortadadır."""
    ts = _fikstur(n=10)
    d = shadowlaw.money_score_detail(ts, _goal(), span_days=SPAN)
    assert d["score"] is None and d["reason"], "min_sample dalı değişmiş"
    assert d["realized_usd"]["olculdu"] is True
    assert d["realized_usd"]["pnl_usd"] == round(sum(float(t["pnl_dollars"]) for t in ts), 2)


# =================================================================================================
# ⓐ GERİYE-UYUM ÇİVİSİ — mevcut money_score değerleri BİT-BİT aynı
# =================================================================================================
BEKLENEN_ESKI_ALANLAR = {
    "score": 0.4281,
    "score_eski_yasa": 0.5152,
    "n": 40,
    "total_return": 0.0973,
    "span_days": 335.0,
    "hedef_pencere": 0.22728,
    "annual_target": 0.25,
    "max_drawdown": 0.0119,
    "components": {"para": 0.4281},
    "components_eski_yasa": {"ret": 0.119, "dd": 0.852, "sharpe": 1.0},
    "law": "para_v3",
    "decides": True,
}


def test_GERIYE_UYUM_money_score_detail_eski_alanlari_BIT_BIT_ayni():
    """PARA-v3 skoru bugüne kadarki tüm ölçüm hükümlerinin ORTAK CETVELİDİR. Bu turda eklenen
    alanlar cetveli kaydırırsa çivilenmiş her hüküm (kartlar, K-defteri, prescreen tabloları)
    sessizce kıyaslanamaz hâle gelir. Sabitler ELLE yazılıdır: uygulamanın çıktısından türetilseydi
    çivi kendisiyle karşılaştırma yapardı ve hiçbir kaymayı göremezdi."""
    d = shadowlaw.money_score_detail(_fikstur(), _goal(), span_days=SPAN)
    for alan, deger in BEKLENEN_ESKI_ALANLAR.items():
        assert d[alan] == deger, f"geriye-uyum kırıldı: {alan} {d[alan]!r} != {deger!r}"
    assert d["yasa_metni"] == shadowlaw.YASA_METNI

    # ve karar sayısı FORMÜLDEN bağımsız olarak da doğrulanır (literal sürüklense bile yakalanır)
    hp = (1.25 ** (SPAN / 365.0)) - 1.0
    assert d["score"] == pytest.approx(round(d["total_return"] / hp, 4), abs=1e-9)
    assert shadowlaw.money_score(_fikstur(), _goal(), span_days=SPAN) == 0.4281


def test_GERIYE_UYUM_eklenen_alan_ESKI_anahtarlari_SILMEDI_veya_yeniden_adlandirmadi():
    """Ek alan EKLEMEK serbest, mevcut anahtarı KALDIRMAK değil: tüketiciler (reflect, probgate,
    prescreen, pano) bu anahtarları adıyla okuyor."""
    d = shadowlaw.money_score_detail(_fikstur(), _goal(), span_days=SPAN)
    assert set(BEKLENEN_ESKI_ALANLAR) | {"yasa_metni"} <= set(d)
    assert set(d) - (set(BEKLENEN_ESKI_ALANLAR) | {"yasa_metni"}) == {"realized_usd"}, \
        "beyan edilmemiş yeni anahtar sızdı"
    # min_sample dalı da eski şemasını korur
    az = shadowlaw.money_score_detail(_fikstur(n=5), _goal(), span_days=SPAN)
    assert set(az) == {"score", "reason", "n", "law", "decides", "realized_usd"}
    json.dumps(d, ensure_ascii=False)      # pano/API yüzeyi: numpy sızması 500 döndürür


# =================================================================================================
# ② M2M DÜŞÜŞ BLOĞU — sentetik eğriyle ihlal / temiz
# =================================================================================================
def _egri(seviyeler: list[float], ilk_gun: int = 1) -> list:
    import datetime as dt
    d0 = dt.date(2024, 1, 1) + dt.timedelta(days=ilk_gun - 1)
    return [(str(d0 + dt.timedelta(days=i)), float(v)) for i, v in enumerate(seviyeler)]


def test_mtm_dd_bloku_IHLALI_bulur_ve_ILK_5_gunu_ornekler():
    """Sentetik eğri: 100k → 110k tepe → 92k dip (%16,4 düşüş) → toparlanma. Eşik 0,04 olduğu için
    çukurun İÇİNDEKİ her gün ihlaldir; blok maksimumu, ihlal sayısını ve İLK 5 örneği vermeli."""
    seviyeler = [100_000, 105_000, 110_000, 106_000, 102_000, 98_000, 95_000, 92_000,
                 96_000, 101_000, 108_000, 112_000]
    r = backtest.mtm_dd_veto(_egri(seviyeler))

    assert r["olculdu"] is True and r["neden"] is None
    # 2026-08-13: sabit 0,04 KALDIRILDI — bu satırın yasası "blok eşiği ÖDÜNÇ ALIR, kendi
    # eşiğini tanımlamaz"dır; sayının kendisi goal'e yapışık (operatör 0,08→0,16 → marj 0,08).
    assert r["esik"] == shadowlaw.DD_VETO_MARGIN
    assert r["esik_kaynagi"] == "shadowlaw.DD_VETO_MARGIN"
    # maksimum düşüş ELLE: (110000 − 92000)/110000
    assert r["max_mtm_dd"] == pytest.approx((110_000 - 92_000) / 110_000, abs=1e-4) == \
        pytest.approx(0.1636, abs=1e-4)
    assert r["ihlal"] is True
    assert r["max_mtm_dd_gunu"] == "2024-01-08"
    # 106k (%3,64) ve 108k (%1,8) eşiğin ALTINDA → ihlal DEĞİL; aradaki 6 gün ihlal.
    # ÖRNEKLEME ÇİVİSİ: sayaç 6 der ama liste İLK 5'i taşır (defter şişmesin).
    assert r["n_ihlal_gunu"] == 6
    assert [g["tarih"] for g in r["ihlal_gunleri"]] == [f"2024-01-0{i}" for i in range(5, 10)]
    assert all(g["dd"] > shadowlaw.DD_VETO_MARGIN for g in r["ihlal_gunleri"])
    assert r["n_gun"] == len(seviyeler) and r["pencere"] == {"ilk": "2024-01-01",
                                                            "son": "2024-01-12"}
    assert r["hukum_verir"] is False, "rapor bloğu hüküm veriyor gibi etiketlenmiş"
    assert len(r["ihlal_gunleri"]) <= backtest.MTM_DD_ORNEK_LIMIT


def test_mtm_dd_bloku_TEMIZ_egride_ihlal_yazmaz():
    """Sığ salınım (maks %2,7) eşiğin altında: ihlal False, ihlal günleri BOŞ — ama maksimum yine
    ÖLÇÜLÜR (rapor bloğu "temiz" derken de sayı verir)."""
    seviyeler = [100_000, 101_000, 100_500, 102_000, 99_800, 101_500, 102_500]
    r = backtest.mtm_dd_veto(_egri(seviyeler))
    assert r["olculdu"] is True and r["ihlal"] is False
    assert r["ihlal_gunleri"] == [] and r["n_ihlal_gunu"] == 0
    assert r["max_mtm_dd"] == pytest.approx((102_000 - 99_800) / 102_000, abs=1e-4)
    assert 0 < r["max_mtm_dd"] < r["esik"]


def test_mtm_dd_bloku_BOS_egride_ihlal_None_doner_False_DEGIL():
    """UYDURMA YASAĞI: hiç bakılmamış bir koşula temiz kâğıdı verilmez."""
    for bos in ([], None):
        r = backtest.mtm_dd_veto(bos)
        assert r["olculdu"] is False
        assert r["max_mtm_dd"] is None
        assert r["ihlal"] is None, "boş eğriden 'ihlal yok' hükmü üretildi"
        assert r["neden"] and "ÖLÇÜLEMEDİ" in r["neden"]


def test_mtm_dd_bloku_BICIMSIZ_noktayi_SAYAR_sessizce_atmaz():
    r = backtest.mtm_dd_veto([("2024-01-01", 100_000), ("2024-01-02", "xx"),
                              ("2024-01-03", 90_000)])
    assert r["olculdu"] is True and r["n_gun"] == 2 and r["n_atlanan"] == 1
    assert r["max_mtm_dd"] == pytest.approx(0.10, abs=1e-6)


def test_mtm_dd_esigi_disaridan_verilebilir_ama_VARSAYILAN_tek_kaynaktan_gelir():
    """İkinci bir eşik sabiti tanımlamak, aynı yasanın ikinci uygulaması olurdu."""
    egri = _egri([100_000, 94_000])
    assert backtest.mtm_dd_veto(egri)["ihlal"] is True
    disaridan = backtest.mtm_dd_veto(egri, esik=0.20)
    assert disaridan["ihlal"] is False
    # ...ve rapor, eşiğin NEREDEN geldiğini söyler: elle eşikli bir duyarlılık taraması
    # "yasanın eşiğiyle ölçüldü" diye okunamaz.
    assert disaridan["esik_kaynagi"] == "cagiran_verdi"
    assert backtest.mtm_dd_veto(egri)["esik_kaynagi"] == "shadowlaw.DD_VETO_MARGIN"
    src = inspect.getsource(backtest.mtm_dd_veto)
    assert "shadowlaw.DD_VETO_MARGIN" in src, "eşik yerel bir sabitten geliyor (çift yasa)"


# =================================================================================================
# ② walk_forward — İMZA DEĞİŞMEDİ, ANAHTAR EKLENDİ
# =================================================================================================
def _kucuk_evren():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def test_walk_forward_IMZASI_DEGISMEDI():
    """Kapının çağrıldığı her yer (reflect, prescreen, baseline, oos_pipeline) bu imzayı kullanıyor;
    yeni bir parametre eklemek sessiz bir çağrı kırılması riski olurdu. Anahtar EKLEMEK serbest."""
    p = list(inspect.signature(backtest.walk_forward).parameters)
    assert p == ["params", "bars", "index_bars", "goal", "is_start", "oos_start", "oos_end",
                 "holdout_end", "strategy_version", "oos_folds", "embargo_days",
                 "params_by_regime", "eval_regime"]


def test_walk_forward_mtm_dd_bloguNU_URETIR_ve_kapi_alanlarina_DOKUNMAZ():
    """Blok gerçek bir koşuda üretilir ve replay'in KENDİ M2M eğrisiyle birebir uyuşur.
    Kapının okuduğu alanlar (oos_score/oos_folds/oos_tail_risk) blokla birlikte DEĞİŞMEZ."""
    bars, idx = _kucuk_evren()
    args = (config.default_strategy()["params"], bars, idx, config.goal(),
            "2022-06-01", "2022-10-01", "2023-04-01", "2023-06-01")
    kw = {"oos_folds": ["2022-10-01", "2023-01-01", "2023-04-01"], "embargo_days": 5}
    w = backtest.walk_forward(*args, **kw)

    assert "mtm_dd_veto" in w
    blok = w["mtm_dd_veto"]
    assert blok["hukum_verir"] is False
    assert blok["esik"] == shadowlaw.DD_VETO_MARGIN
    # replay'in eğrisinden BAĞIMSIZ olarak yeniden hesaplanır — blok gerçekten o eğriyi okuyor mu?
    res = backtest.replay(args[0], bars, idx, config.goal(), "2022-06-01", "2023-06-01",
                          strategy_version=1)
    assert blok == backtest.mtm_dd_veto(res.equity)
    if blok["olculdu"]:
        assert blok["n_gun"] == len(res.equity)
        assert blok["pencere"]["ilk"] == str(res.equity[0][0])[:10]
    json.dumps(w["mtm_dd_veto"], ensure_ascii=False)

    # KAPI ALANLARI: blok hiçbirine girmiyor (aynı çağrı, aynı sayılar)
    w2 = backtest.walk_forward(*args, **kw)
    for alan in ("oos_score", "is_score", "holdout_score", "oos_fold_avg_r_mean"):
        assert w[alan] == w2[alan]
    src = inspect.getsource(backtest.walk_forward)
    assert src.count("mtm_dd_veto(") == 1, "blok kapı hesabının içinde ikinci kez çağrılıyor"
    assert '"mtm_dd_veto": mtm_dd_veto(res.equity),' in src, "blok dönüş sözlüğünde değil"


def test_dusus_vetosunun_KENDISI_bu_bloktan_girdi_ALMAZ():
    """ÇİVİ: kapının düşüş vetosu aday↔incumbent FARKINI okur (`reflect._gate_eval`). Yeni rapor
    bloğu oraya bağlanırsa "hüküm vermez" beyanı yalan olur."""
    from meridian import reflect
    src = inspect.getsource(reflect._gate_eval)
    assert "mtm_dd_veto" not in src, "rapor bloğu kapı hükmüne sızmış"


# =================================================================================================
# ⓓ YASA 6 — her iki blok da GERÇEK bir okuyucuya bağlı
# =================================================================================================
def test_YASA6_realized_usd_bloğunun_okuyucusu_VAR_ve_karneye_giriyor():
    """`analytics.prediction_accuracy_band` — rollback karnesi — bloğu okur ve para sütununu yazar.
    Karne `hermes_scorecard` üzerinden evidence_pack'e ve panoya çıkar."""
    src = inspect.getsource(analytics.prediction_accuracy_band)
    assert "realized_usd" in src, "realized_usd'nin okuyucusu yok (YASA 6)"
    # ...ve blok `money_score_detail`in KENDİ çıktısından okunur — ayrı bir hesap kurulmaz, yoksa
    # kapının gördüğü sözlük ile karnenin gördüğü sözlük sessizce ayrışır.
    assert 'money_score_detail(rows, _g)["realized_usd"]' in src

    b = analytics.prediction_accuracy_band()
    p = b["para_olcegi"]
    assert p["hukum_verir"] is False and p["birim"] == "USD"
    assert set(p) >= {"n_olculen", "n_celiski", "celiskili_idler", "hukum", "beyan", "kaynak"}
    assert p["n_celiski"] <= p["n_olculen"]
    assert p["hukum"], "para sütunu hükümsüz (boş karne 'yolunda' gibi okunur)"
    # her çift para sütununu TAŞIR (ölçülemeyen taraf None kalır, uydurulmaz)
    for c in b["ciftler"]:
        assert set(c) >= {"para_usd", "para_n", "celiski"}
        assert c["celiski"] in (True, False, None)
    json.dumps(b, ensure_ascii=False)


def test_YASA6_para_sutunu_ROLLBACK_ile_AYNI_populasyon_yasasini_kullanir():
    """Popülasyon karışımı bu depoda adıyla yasak: rollback `strategy_version` eşleşmesiyle diliyor,
    para sütunu da öyle dilmek ZORUNDA (yoksa iki cetvel iki ayrı defteri ölçer)."""
    src = inspect.getsource(analytics.prediction_accuracy_band)
    assert "strategy_version" in src
    from meridian import rollback
    assert 'strategy_version") == version' in inspect.getsource(rollback.check_and_rollback)


def test_YASA6_mtm_bloğunun_okuyucusu_walk_forward_ciktisidir():
    """② için okuyucu, kapının kendi çıktısıdır: `walk_forward` sözlüğü ölçüm raporlarının ve
    prescreen/baseline yollarının doğrudan okuduğu şeydir — blok orada durur, ölü kalmaz."""
    assert "mtm_dd_veto" in inspect.getsource(backtest.walk_forward)
    assert callable(backtest.mtm_dd_veto)


# =================================================================================================
# ÖLÇÜM KAYDININ KENDİSİ — DD_VETO_MARGIN hâlâ tek kaynak
# =================================================================================================
def test_DD_VETO_MARGIN_tek_kaynak_kalir_ve_kendi_gurultusunun_disinda():
    """Blok eşiği ÖDÜNÇ ALIR, kendi eşiğini TANIMLAMAZ; ve kayıtlı türetim koşulu bozulmamış."""
    # 2026-08-13: sayı değil TÜRETİM çivilenir — marj `goal.max_drawdown`ın tam yarısı (canlı bağ,
    # `test_para_yasasi_v127`de ayrıca çivili) ve kendi ölçüm gürültüsünün DIŞINDA.
    assert shadowlaw.DD_VETO_MARGIN == 0.5 * float(config.goal()["max_drawdown"])
    assert shadowlaw.DD_VETO_MARGIN > shadowlaw.MEASURED_V3["sd_dusus"], \
        "veto sınırı kendi ölçüm gürültüsünün içine düştü (yazılı türetim koşulu)"
    assert score_mod.START_EQUITY == BASLANGIC
