"""test_para_v3_tamamlama_v178.py — PARA-v3 ②'NİN KAPIYA BAĞLANMASI (WP-M, 2026-08-02).

BU TURUN KAPSAMI, ÖNCEKİ TURUN BIRAKTIĞI TEK BOŞLUKTUR. 2026-08-01'de ① (`shadowlaw.realized_usd`
+ karne para sütunu) ve ②'nin RAPOR yüzü (`walk_forward.mtm_dd_veto`) indi ve v145'te çivilendi.
Ama ②'nin asıl borcu `reflect._gate_eval`in kendi yorumunda adıyla yazılıydı:

    "veto, Search diliminin KAPANMIŞ-İŞLEM sermaye eğrisini okur... `walk_forward` o eğriyi DİLİM
     BAŞINA döndürmüyor... Kapatmak için `walk_forward`ın dilim-başına M2M eğrisi döndürmesi gerekir"

Bu tur o cümleyi gerçeğe çevirir: `walk_forward` artık `_mtm_search` döndürür (aynı sınırlar,
`_trades_search` ile bit-bit) ve kapı AÇIK-POZİSYON düşüşünü İKİNCİ BİR BACAK olarak ÖLÇER.

VE ÖLÇMEKLE KALIR — HÜKÜM VERMEZ. `DD_VETO_MARGIN` kapanmış-işlem düşüş dağılımından türetildi
(σ=0,0343 + %8 bütçenin yarısı); M2M dağılımı BAŞKA bir dağılımdır ve σ'sı ölçülmemiştir. Ölçülmemiş
bir dağılıma ölçülmüş bir marj taşımak "eşiği sonradan seçmek"tir. Bu yüzden bacak bayrak arkasında
(`MERIDIAN_DD_MTM_VETO`) ve VARSAYILAN KAPALI iner; bağlanması ölçüm kartı ister.

BU DOSYANIN ÇİVİLERİ:
  ⓐ M2M eğrisi dilimleme yasası TEK: `backtest.mtm_slice` — `segment_score` de onu kullanır.
  ⓑ `_mtm_search` GERÇEK bir koşuda `_trades_search` ile AYNI sınırlardan kesilir.
  ⓒ Elle hesaplanmış M2M eğrilerinde düşüş sayısı BİREBİR (iki bağımsız uygulama aynı sayıyı verir).
  ⓓ BAYRAK KAPALIYKEN `passes` BİT-BİT ESKİ DAVRANIŞ — ihlal görülür, kayda yazılır, hükme girmez.
  ⓔ Bayrak açıkken bacak GERÇEKTEN bağlanır (aksi hâlde "bayrak arkasında" beyanı boş olurdu).
  ⓕ ① tarafının okuyucu zinciri (realized_usd → karne → hermes_scorecard) AYAKTA.
  ⓖ Mevcut PARA çivileri (marjlar, yasa damgası, rapor bloğunun hükümsüzlüğü) DEĞİŞMEDİ.

HİÇBİR TEST CANLI STATE'E YAZMAZ: tümü salt-okuma ya da bellek-içi fikstür.
"""
from __future__ import annotations

import datetime as dt
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



# =================================================================================================
# ⓐ DİLİMLEME YASASI — TEK UYGULAMA, YARI-AÇIK SINIR
# =================================================================================================
EGRI = [("2024-01-01", 100_000.0), ("2024-01-02", 101_000.0), ("2024-01-03", 99_000.0),
        ("2024-01-04", 103_000.0), ("2024-01-05", 97_000.0)]


def test_mtm_slice_YARI_ACIK_ve_ELLE_hesaplanan_dilimi_verir():
    """Alt sınır DAHİL, üst sınır HARİÇ — `_in_segment`in işlem yasasıyla aynı dilbilgisi.
    Sınır günü iki komşu dilimde birden sayılamaz."""
    assert backtest.mtm_slice(EGRI, "2024-01-02", "2024-01-04") == [
        ("2024-01-02", 101_000.0), ("2024-01-03", 99_000.0)]
    # üst sınır günü DIŞARIDA (yarı-açık), alt sınır günü İÇERİDE
    assert [d for d, _ in backtest.mtm_slice(EGRI, "2024-01-01", "2024-01-05")] == \
        ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    # pencere dışı / boş girdi: BOŞ liste (uydurma nokta üretilmez)
    assert backtest.mtm_slice(EGRI, "2025-01-01", "2025-02-01") == []
    assert backtest.mtm_slice(None, "2024-01-01", "2024-01-05") == []
    assert backtest.mtm_slice([], "2024-01-01", "2024-01-05") == []


def test_segment_score_AYNI_dilimleme_yasasini_kullanir_ikinci_kopya_YOK():
    """SÜRÜKLENME KİLİDİ: yasa artık iki okuyuculudur (segment_score + walk_forward._mtm_search).
    İkinci bir kopya yazılırsa biri değişir, diğeri sessizce eski popülasyonu ölçer."""
    src = inspect.getsource(backtest.segment_score)
    assert "mtm_slice(" in src, "segment_score dilimlemeyi tek kaynaktan almıyor"
    assert "for dd, e in" not in src, "satır-içi dilimleme kopyası geri gelmiş"
    # DAVRANIŞ AYNI: eski satır-içi ifade ile yeni fonksiyon aynı sonucu verir
    lo, hi = "2024-01-02", "2024-01-05"
    eski = [(d, e) for d, e in EGRI if lo <= str(d)[:10] < hi]
    assert backtest.mtm_slice(EGRI, lo, hi) == eski


# =================================================================================================
# ⓒ DÜŞÜŞ SAYISI — ELLE HESAPLI, İKİ BAĞIMSIZ UYGULAMA AYNI SONUCU VERİR
# =================================================================================================
def _mtm_egrisi(dd: float, gun: int = 31, lo: str = wf.S_LO, tepe: float = 100_000.0) -> list:
    """Tepe ilk gün, ortada TAM `dd` oranında tek çukur, sonra tepeye dönüş.
    Tanım gereği maks düşüş = `dd` (tepe ilk gündedir, çukur ondan sonra gelir)."""
    d0 = dt.date.fromisoformat(lo)
    return [((d0 + dt.timedelta(days=i)).isoformat(),
             round(tepe * (1.0 - dd) if i == gun // 2 else tepe, 2)) for i in range(gun)]


@pytest.mark.parametrize("dd", [0.0, 0.02, 0.05, 0.129])
def test_M2M_dusus_ELLE_hesaplanan_sayiyi_verir(dd):
    """Fikstür tepe-çukur-tepe: beklenen düşüş TAM `dd`. Kapının kullandığı `score.max_drawdown` ile
    raporun kullandığı `backtest.mtm_dd_veto` AYNI sayıyı vermek ZORUNDA — ayrışırlarsa kapı ve
    rapor iki farklı gerçeği anlatır."""
    egri = _mtm_egrisi(dd)
    kapinin_gordugu = score_mod.max_drawdown([e for _d, e in egri])
    raporun_gordugu = backtest.mtm_dd_veto(egri)["max_mtm_dd"]
    assert kapinin_gordugu == pytest.approx(dd, abs=1e-9)
    assert raporun_gordugu == pytest.approx(dd, abs=1e-4)


# =================================================================================================
# ⓑ ÜRETİCİ — `_mtm_search`, `_trades_search` İLE AYNI SINIRLARDAN KESİLİR
# =================================================================================================
def _kucuk_evren():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def _wf_kosusu():
    bars, idx = _kucuk_evren()
    args = (config.default_strategy()["params"], bars, idx, config.goal(),
            "2022-06-01", "2022-10-01", "2023-04-01", "2023-06-01")
    kw = {"oos_folds": ["2022-10-01", "2023-01-01", "2023-04-01"], "embargo_days": 5}
    return backtest.walk_forward(*args, **kw), args, kw


def test_walk_forward_mtm_search_URETIR_ve_TRADES_SEARCH_ile_AYNI_PENCEREDEDIR():
    """GERÇEK koşu. Dilim sınırları `oos_split`te yazılıdır; eğri o sınırların DIŞINA taşamaz,
    yoksa vetonun iki bacağı iki farklı sınav penceresi okur."""
    w, args, _ = _wf_kosusu()
    assert "_mtm_search" in w, "kapının açık-pozisyon girdisi üretilmiyor"
    sp = w["oos_split"]
    lo, hi = sp["search_start"], sp["search_end"]
    for tarih, _eq in w["_mtm_search"]:
        assert lo <= str(tarih)[:10] < hi, f"eğri Search penceresi dışına taştı: {tarih}"
    # aynı işlemler için işlem dilimi de aynı sınırlarda
    for t in w["_trades_search"]:
        assert lo <= str(t["ts_open"])[:10] < hi

    # BAĞIMSIZ TÜRETME: replay'in kendi eğrisinden aynı dilim çıkmalı
    res = backtest.replay(args[0], args[1], args[2], config.goal(), "2022-06-01", "2023-06-01",
                          strategy_version=1)
    assert w["_mtm_search"] == backtest.mtm_slice(res.equity, lo, hi)
    json.dumps(w["_mtm_search"], ensure_ascii=False)


def test_walk_forward_RAPOR_blogu_ve_KAPI_alanlari_DEGISMEDI():
    """② rapor bloğu (v145'te çivili) TAM pencereyi okumaya devam eder; yeni dilim ONU değiştirmez.
    Kapı metrikleri de aynı koşuda aynı sayıları verir (yeni anahtar hesaba girmiyor)."""
    w, args, kw = _wf_kosusu()
    res = backtest.replay(args[0], args[1], args[2], config.goal(), "2022-06-01", "2023-06-01",
                          strategy_version=1)
    assert w["mtm_dd_veto"] == backtest.mtm_dd_veto(res.equity)      # TAM pencere, dilim DEĞİL
    assert w["mtm_dd_veto"]["hukum_verir"] is False
    if w["mtm_dd_veto"]["olculdu"]:
        assert w["mtm_dd_veto"]["n_gun"] == len(res.equity)
        assert len(w["_mtm_search"]) <= w["mtm_dd_veto"]["n_gun"], "dilim tam pencereden büyük"
    w2 = backtest.walk_forward(*args, **kw)
    for alan in ("oos_score", "is_score", "holdout_score", "oos_fold_avg_r_mean"):
        assert w[alan] == w2[alan]


# =================================================================================================
# ⓓ/ⓔ KAPI — ÖLÇER, VARSAYILAN BAĞLAMAZ
# =================================================================================================
@pytest.fixture
def kapi_ortami(sandbox_state, monkeypatch):
    """Sandbox + bayrak KAPALI (varsayılan) — canlı ortam değişkeni suite'e sızmasın."""
    monkeypatch.delenv(reflect.DD_MTM_VETO_ENV, raising=False)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _ciftler(inc_dd_mtm=None, cand_dd_mtm=None):
    """Kapının gerçekten geçtiği bir aday çifti; istenirse M2M eğrileri eklenir."""
    inc = wf.wf_from_scores(0.20, folds=((40, 0.4), (40, 0.4)))
    cand = wf.wf_from_scores(0.55, folds=((40, 1.2), (40, 1.2)))
    if inc_dd_mtm is not None:
        inc["_mtm_search"] = _mtm_egrisi(inc_dd_mtm)
    if cand_dd_mtm is not None:
        cand["_mtm_search"] = _mtm_egrisi(cand_dd_mtm)
    return inc, cand


def test_M2M_egrisi_YOKSA_olculemedi_yazar_ve_HICBIR_SEYI_engellemez(kapi_ortami):
    """UYGULANAMAYAN KONTROL VETO SEBEBİ OLAMAZ: fikstür/legacy sözlükte eğri yoktur — 'temiz kâğıt'
    değil 'bakılmadı' yazılır."""
    inc, cand = _ciftler()
    passes, gate, _why = reflect._gate_eval(inc, cand, k_probes=1)
    assert gate["dd_mtm_durum"] == "olculemedi"
    assert gate["dd_mtm_ok"] is True and gate["dd_mtm_bagli"] is False
    assert gate["incumbent_dd_mtm"] is None and gate["candidate_dd_mtm"] is None
    assert passes is True, "taban fikstürü kapıyı geçmiyor — sonraki çiviler boş kalırdı"


def test_BAYRAK_KAPALIYKEN_M2M_ihlali_HUKME_GIRMEZ_ama_KAYDA_girer(kapi_ortami):
    """ⓓ ASIL ÇİVİ. Aday M2M düşüşünü marjın çok ötesinde kötüleştiriyor: `passes` DEĞİŞMEZ
    (bit-bit eski davranış), ama kapı kaydı ihlali ADIYLA taşır — ölçüm kartının ham maddesi."""
    temiz_passes, g0, w0 = reflect._gate_eval(*_ciftler(), k_probes=1)
    # FİKSTÜR EŞİK-BAĞIL (2026-08-13): fark marjdan TÜRETİLİR — marj değişince test kendini onarır.
    inc, cand = _ciftler(inc_dd_mtm=0.05,
                         cand_dd_mtm=0.05 + shadowlaw.DD_VETO_MARGIN * 2.5)   # marjın belirgin ÜSTÜ → ihlal
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)

    assert passes is temiz_passes is True, "M2M bacağı bayrak kapalıyken hükmü değiştirdi"
    # ÖNCE/SONRA: M2M girdisi EKLENDİĞİNDE kapı kaydının ESKİ alanlarının HİÇBİRİ kımıldamıyor —
    # yeni bacak toplama değil, YANA yazıyor. (Bu turun "davranış değişikliği yok" iddiasının kanıtı.)
    _yeni = {"dd_mtm_ok", "dd_mtm_durum", "dd_mtm_bagli", "dd_mtm_beyan",
             "incumbent_dd_mtm", "candidate_dd_mtm"}
    assert {k: v for k, v in gate.items() if k not in _yeni} == \
           {k: v for k, v in g0.items() if k not in _yeni}
    assert why == w0
    assert gate["dd_mtm_durum"] == "ihlal_baglanmadi"
    assert gate["dd_mtm_ok"] is True and gate["dd_mtm_bagli"] is False
    assert gate["incumbent_dd_mtm"] == pytest.approx(0.05, abs=1e-4)
    assert gate["candidate_dd_mtm"] == pytest.approx(0.15, abs=1e-4)
    assert "M2M" not in why, "hüküm gerekçesi bağlanmamış bacaktan besleniyor"
    assert gate["dd_mtm_beyan"], "bağlanmama gerekçesi kayda yazılmıyor"
    # KAPANMIŞ-İŞLEM BACAĞI DOKUNULMADI: eski alanlar aynı anlamda, aynı yerde
    assert gate["dd_ok"] is True and gate["dd_veto_margin"] == shadowlaw.DD_VETO_MARGIN
    json.dumps(gate, ensure_ascii=False, default=str)


def test_BAYRAK_ACIKKEN_bacak_GERCEKTEN_baglanir(monkeypatch, kapi_ortami):
    """ⓔ 'Bayrak arkasında' beyanı ancak bayrak bir şeyi DEĞİŞTİRİYORSA doğrudur. Aynı çift,
    bayrak açık: aday RET ve gerekçe M2M'yi adıyla söyler."""
    monkeypatch.setenv(reflect.DD_MTM_VETO_ENV, "1")
    inc, cand = _ciftler(inc_dd_mtm=0.05, cand_dd_mtm=0.15)
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)
    assert passes is False and gate["dd_mtm_ok"] is False
    assert gate["dd_mtm_durum"] == "veto" and gate["dd_mtm_bagli"] is True
    assert "M2M" in why and "0.1500" in why


def test_BAYRAK_ACIK_ama_IHLAL_YOKSA_hukum_DEGISMEZ(monkeypatch, kapi_ortami):
    """Bacak TEK YÖNLÜ: yalnız kötüleşmeyi cezalandırır. Marj içinde kalan aday etkilenmez."""
    monkeypatch.setenv(reflect.DD_MTM_VETO_ENV, "1")
    inc, cand = _ciftler(inc_dd_mtm=0.05,
                         cand_dd_mtm=0.05 + shadowlaw.DD_VETO_MARGIN * 0.75)  # marjın ALTI → geçti
    passes, gate, _why = reflect._gate_eval(inc, cand, k_probes=1)
    assert gate["dd_mtm_durum"] == "gecti" and passes is True
    # İYİLEŞME ÖDÜLLENDİRİLMEZ (çift-sayım arka kapıdan dönmesin)
    inc2, cand2 = _ciftler(inc_dd_mtm=0.15, cand_dd_mtm=0.01)
    p2, g2, _ = reflect._gate_eval(inc2, cand2, k_probes=1)
    assert g2["dd_mtm_durum"] == "gecti" and p2 is True


def test_ONBELLEKTEN_gelen_egri_de_OLCULUR_JSON_donusu_kirmiyor(kapi_ortami):
    """ÜRETİMDEKİ EN SIK YOL: `reflect._inc_disk_save` incumbent walk'ın TÜM sözlüğünü
    `inc_cache.json`a yazar — JSON turunda demetler LİSTEye döner. Bacak listeyi okuyamazsa
    önbellekli her oturumda ölçüm sessizce 'olculemedi'ye düşer ve kart hiç veri toplayamaz."""
    inc, cand = _ciftler(inc_dd_mtm=0.05, cand_dd_mtm=0.15)
    inc["_mtm_search"] = json.loads(json.dumps(inc["_mtm_search"]))
    cand["_mtm_search"] = json.loads(json.dumps(cand["_mtm_search"]))
    assert isinstance(inc["_mtm_search"][0], list), "fikstür JSON turunu taklit etmiyor"
    _p, gate, _w = reflect._gate_eval(inc, cand, k_probes=1)
    assert gate["dd_mtm_durum"] == "ihlal_baglanmadi"
    assert gate["candidate_dd_mtm"] == pytest.approx(0.15, abs=1e-4)
    # dilimleyici de liste biçimini okur (aynı önbellek turundan geçer)
    assert backtest.mtm_slice(json.loads(json.dumps(EGRI)), "2024-01-02", "2024-01-04") == \
        [("2024-01-02", 101_000.0), ("2024-01-03", 99_000.0)]


def test_VARSAYILAN_KAPALI_ve_passes_formulunde_NO_OP(kapi_ortami):
    """Varsayılan gerçekten kapalı mı ve `passes` formülünde bacak duruyor mu — ikisi birden."""
    assert reflect._dd_mtm_bagli() is False, "bayrak varsayılan AÇIK inmiş"
    src = inspect.getsource(reflect._gate_eval)
    assert "and dd_mtm_ok)" in src, "bacak passes formülüne bağlanmamış (bayrak ölü olurdu)"
    assert "_mtm_search" in src, "kapı yeni girdiyi okumuyor"


# =================================================================================================
# ⓕ ① TARAFI — OKUYUCU ZİNCİRİ AYAKTA (YASA 6, uçtan uca)
# =================================================================================================
def test_realized_usd_alani_ve_OKUYUCUSUNUN_OKUYUCUSU_yerinde():
    """v145 bloğu ve ilk okuyucuyu (karne para sütunu) çiviliyor; buradaki çivi zincirin SON
    halkasıdır: karne `hermes_scorecard` üzerinden gerçekten yayına çıkıyor mu?"""
    d = shadowlaw.money_score_detail(wf.trades(40, 1178, "2024-01-01", "2024-12-01", 0.35),
                                     config.goal())
    assert "realized_usd" in d and d["realized_usd"]["hukum_verir"] is False
    assert d["realized_usd"]["birim"] == "USD"
    # zincir: money_score_detail → prediction_accuracy_band → hermes_scorecard
    assert "realized_usd" in inspect.getsource(analytics.prediction_accuracy_band)
    assert "prediction_accuracy_band()" in inspect.getsource(analytics.hermes_scorecard)


def test_IKI_BILESEN_de_HUKUMSUZLUGUNU_ADIYLA_beyan_eder():
    """① para sütunu ve ② M2M bacağı aynı sınıftandır: ölçülür, görünür, HÜKÜM VERMEZ. Beyan
    kaybolursa bir sonraki okuyucu onları karar girdisi sanır."""
    band = analytics.prediction_accuracy_band()
    assert band["para_olcegi"]["hukum_verir"] is False
    assert backtest.mtm_dd_veto(_mtm_egrisi(0.05))["hukum_verir"] is False
    assert "ölçüm kartı" in inspect.getsource(reflect).split("DD_MTM_VETO_ENV")[0][-2000:], \
        "M2M bacağının bağlanma koşulu (ölçüm kartı) beyan edilmemiş"


# =================================================================================================
# ⓖ MEVCUT PARA ÇİVİLERİ — REGRESYON
# =================================================================================================
def test_PARA_v3_sabitleri_ve_yasa_damgasi_DEGISMEDI():
    """Bu tur ŞASİ turudur: hiçbir yasa sayısı değişmez. Değişirse tüm geçmiş hükümler kıyaslanamaz."""
    assert shadowlaw.DD_VETO_MARGIN == 0.5 * float(config.goal()["max_drawdown"])  # sayı değil TÜRETİM (2026-08-13)
    assert reflect.DD_VETO_MARGIN == shadowlaw.DD_VETO_MARGIN
    assert reflect.GATE_MARGIN == 0.02
    assert reflect.MONEY_GATE_MARGIN == shadowlaw.MONEY_GATE_MARGIN
    assert shadowlaw.YASA_SURUMU and shadowlaw.YASA_METNI


def test_KAPININ_kapanmis_islem_bacagi_RAPOR_blogundan_girdi_ALMIYOR():
    """v145 çivisinin bu turdaki hâli: kapı, `walk_forward`ın 'hüküm vermez' beyanlı rapor bloğunu
    okumaz — M2M sayısını KENDİ girdisinden, kapanmış-işlem bacağıyla AYNI formülle türetir."""
    src = inspect.getsource(reflect._gate_eval)
    assert "mtm_dd_veto" not in src, "rapor bloğu kapı hükmüne sızmış"
    # 4 = iki bacak × (aday, incumbent). Hepsi `score.max_drawdown`; kapıda elle yazılmış ikinci
    # bir düşüş döngüsü YOK — olsaydı iki bacak aynı adı taşıyıp farklı sayı üretebilirdi.
    assert src.count("max_drawdown(") == 4, "düşüş formülü tek kaynak olmaktan çıkmış"
    assert "peak = " not in src and "tepe = " not in src, "kapıda elle düşüş döngüsü doğmuş"
