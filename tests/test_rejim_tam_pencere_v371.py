"""test_rejim_tam_pencere_v371.py — REJİM SHIP SATIRINDA TAM-PENCERE DEFTERİ (2026-09-02).

SINIF: **doğru gerekçeyle bırakılmış bir boşluk, gerekçe ortadan kalkınca da boşluk kalıyor.**

Akıbet kalemi N00017 `backtest_full`ü GLOBAL ship yoluna bağladı ama REJİM ship'ini BİLİNÇLİ
dışarıda bıraktı: `walk_forward.full_detail` replay'in BÜTÜN işlemlerinden üretilir (rejim
dilimlenmemiş) ve onu rejim satırının ÖNCELİKLİ bacağına koymak, `backtest_oos@<rejim>` ek-adının
önlediği hatanın ta kendisi olurdu — global bir popülasyon, rejim dilimli fold bacağını ezerdi.
O gerekçe DOĞRUydu ve bugün de doğrudur; yanlış olan, ondan "rejim satırı tam-pencere defterini
HİÇ göremez" sonucunu çıkarmaktı. Doğru popülasyon zaten elin altındaydı: `walk_forward`
notlandırmasını `graded = _regime_slice(res.trades, eval_regime)` üzerinden yapıyor.

ÜÇ YÜZEY, TEK KABLO (bu dosya üçünü de ayrı ayrı çiviler):
  1. ÜRETİCİ — `backtest.walk_forward` rejimli çağrıda İKİNCİ bir defter döndürür:
     `full_detail_graded = score_detail(graded, goal)`. `eval_regime=None` iken anahtar HİÇ YOKtur;
     orada `graded == res.trades` olduğundan ikinci kopya TEK-KAYNAK YASASINI çiğnerdi — yokluk
     bir eksiklik değil, BEYANdır.
  2. YAZAN — `reflect._submit_locked` rejim ship'inde `backtest_full@<rejim>` yazar. DÜZ
     `backtest_full` rejim satırına ASLA düşmez: `rollback`un düz-anahtar geri-düşüşleri
     popülasyon-tutarlı kalmak zorunda.
  3. OKUYAN — `analytics._backtest_beklenti_r` önce DÜZ `backtest_full`e bakar; yoksa satırdaki
     TEK ek-adlı `backtest_oos@<X>` anahtarından rejimi türetip `backtest_full@<X>` dener.
     `kaynak`/`kapsam` okunan bacağı ADIYLA söyler — iki farklı popülasyon aynı sayı sanılamaz.
     BİRDEN ÇOK ek-adlı oos anahtarı varsa HİÇBİRİ seçilmez (tahmin yasak) ve arıza `neden`de konuşur.

YASA 6 (okuyucusuz yazım yok) BU DOSYADA UÇTAN UCA ÖLÇÜLÜR: 1'in ürettiğini 2 yazar, 2'nin
yazdığını 3 okur ve son çivi `live_expectancy_ceiling`in gerçekten o bacaktan hüküm verdiğini
gösterir. Zincirin bir halkası kopsa geri kalanı yeşil kalır ve boşluk sessizce geri gelirdi.
"""
from __future__ import annotations

import pandas as pd
import pytest
import yaml

from meridian import analytics, backtest, config, reflect, versioning
from tests import wf_fixtures as wf


# =================================================================================================
# ORTAK DÜZENEK
# =================================================================================================
def _bolunmus_islemler():
    """6 chop + 6 trend_up: rejim dilimi ile global popülasyon SAYIYLA ayrışsın (6 ≠ 12).
    `test_regime_patch._fake_trades` ile aynı desen — orada da dilimleme bu şekilde ölçülüyor."""
    def mk(i, reg, r):
        return {"ts_open": f"2024-0{1 + i % 6}-10", "ts_close": f"2024-0{1 + i % 6}-20",
                "regime": reg, "r_multiple": r, "pnl_dollars": r * 100.0}
    return ([mk(i, "chop", 1.0) for i in range(6)] +
            [mk(i, "trend_up", -1.0) for i in range(6)])


@pytest.fixture
def ince_goal(sandbox_state, monkeypatch):
    """min_sample=3: 6 işlemlik bir dilim `score_detail`de SKOR üretsin. Eşik testin konusu değil —
    min_sample 30 kalsaydı iki defter de `{"score": None, ...}` döner ve ÇİVİ POPÜLASYONU DEĞİL
    eşiği ölçerdi (n alanı yine dolardı, yani çivi yanlış sebeple yeşil kalabilirdi)."""
    g = dict(config.goal())
    g["min_sample"] = 3
    return g


def _wf_kos(monkeypatch, goal, eval_regime=None, trades=None):
    """`walk_forward`ı SENTETİK bir replay üzerinde koşar (ağır veri yok) — emsal:
    `test_regime_patch.test_walk_forward_grades_only_the_target_regime`."""
    res = backtest.BacktestResult(trades=trades if trades is not None else _bolunmus_islemler(),
                                  equity=[], params={}, start="2024-01-01", end="2024-12-31")
    monkeypatch.setattr(backtest, "replay", lambda *a, **k: res)
    return backtest.walk_forward({}, {}, pd.DataFrame({"date": []}), goal,
                                 "2024-01-01", "2024-01-01", "2024-12-31", "2024-12-31",
                                 eval_regime=eval_regime)


# =================================================================================================
# YÜZEY 1 — ÜRETİCİ: rejim-dilimli tam-pencere defteri
# =================================================================================================
def test_1a_rejimli_cagri_DILIMLI_tam_pencere_defteri_dondurur(ince_goal, monkeypatch):
    """ÜRETİCİNİN ÇİVİSİ. Ship yolunun rejim satırına yazacağı defterin KAYNAĞI burasıdır ve
    popülasyonu `graded`dir — yani `_regime_slice(res.trades, eval_regime)`.

    `n` DİLİM SAYISINA eşit olmalı: global popülasyonla (12) karışırsa çivi ısırır. Bu tam olarak
    `backtest_oos@<rejim>` ek-adının önlediği hatadır, bir yüzey yukarıda."""
    w = _wf_kos(monkeypatch, ince_goal, eval_regime="chop")

    assert "full_detail_graded" in w, \
        "rejimli çağrı dilimli tam-pencere defterini döndürmüyor — rejim ship'inin KAYNAĞI yok"
    gd = w["full_detail_graded"]
    assert isinstance(gd, dict) and gd.get("avg_r") is not None, \
        "dilimli defter `score_detail` çıktısı değil (avg_r yok)"
    assert gd["n"] == w["n_trades_graded"] == 6, \
        f"dilimli defter GLOBAL popülasyondan üretilmiş (n={gd['n']}, dilim=6)"
    assert gd["avg_r"] == pytest.approx(1.0), \
        "dilimli defterin beklentisi karışık kitabınkine kaymış — popülasyon dar DEĞİL"


def test_1b_dilimsiz_defter_AYNI_cagrida_GLOBAL_kalir(ince_goal, monkeypatch):
    """İKİ DEFTER İKİ POPÜLASYONDUR ve rejimli çağrıda İKİSİ DE döner. `full_detail` global kalır
    (rapor/teşhis tarafı onu okur); daralan yalnız ikinci defterdir. Biri diğerini EZERSE
    "hangi pencere?" sorusu okuyucudan gizlenirdi."""
    w = _wf_kos(monkeypatch, ince_goal, eval_regime="chop")

    assert w["full_detail"]["n"] == w["n_trades_total"] == 12, \
        "rejimli çağrı GLOBAL defteri de daraltmış — iki popülasyon tek alana çökmüş"
    assert w["full_detail"]["n"] != w["full_detail_graded"]["n"], \
        "iki defter aynı popülasyonu taşıyor — dilimleme fiilen koşmadı"


def test_1c_global_cagrida_anahtar_HIC_YOK_yokluk_BEYANLIdir(ince_goal, monkeypatch):
    """TEK-KAYNAK YASASI. `eval_regime=None` iken `graded == res.trades`, yani ikinci defter
    birincinin BİREBİR KOPYASI olurdu. Aynı gerçeğin iki kopyası sessizce ayrışır (kopyalardan
    biri bir gün başka bir yasadan türetilir ve kimse fark etmez) — o yüzden anahtar YAZILMAZ.

    `None` YAZMAK DA YASAK: "ölçtük, boş çıktı" diye okunurdu. Yokluk burada bir BEYANdır."""
    w = _wf_kos(monkeypatch, ince_goal, eval_regime=None)

    assert "full_detail_graded" not in w, \
        "global çağrıda dilimli defter üretildi — `full_detail`in birebir kopyası, tek-kaynak ihlali"
    assert w["full_detail"]["n"] == 12, "global defter kayboldu"


def test_1d_hayalet_rejim_de_GLOBAL_sayilir_anahtar_yine_YOK(ince_goal, monkeypatch):
    """`reflect._eval_regime_of` geçersiz rejimde None döndürür (hayalet rejim → global
    notlandırma). Üretici tarafta da aynı ayrım korunur: BOŞ dizge/None global demektir ve
    `_regime_slice` filtre uygulamaz — anahtar üretmek "dilimlendi" yalanı olurdu."""
    w = _wf_kos(monkeypatch, ince_goal, eval_regime="")

    assert "full_detail_graded" not in w
    assert w["n_trades_graded"] == 12


def test_1e_INCE_dilimde_defter_SKORSUZ_ama_n_DURUSTTUR(sandbox_state, monkeypatch):
    """İnce dilim SESSİZCE kaybolmaz. `score_detail` min_sample altında `{"score": None, "n": …}`
    döndürür; alan yine YAZILIR çünkü `n` bir OLGUdur ve okuyan taraf "ölçülemedi"yi "alan yok"tan
    ayırabilmelidir. avg_r yoksa `analytics` bacağı zaten çözmez ve fold'lara düşer — dürüst yol."""
    goal = dict(config.goal())
    goal["min_sample"] = 10
    w = _wf_kos(monkeypatch, goal, eval_regime="chop")

    gd = w["full_detail_graded"]
    assert gd["n"] == 6 and gd["score"] is None, "ince dilim skorsuz DEĞİL — eşik dilime uygulanmamış"
    assert "avg_r" not in gd, "skorsuz defter yine de bir beklenti uydurdu"


# =================================================================================================
# YÜZEY 2 — YAZAN: rejim ship'i EK-ADLI anahtara yazar, DÜZ anahtara ASLA
# =================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    """`test_ship_baseline_v100.seeded` ile AYNI düzenek — ship yolunun koşabilmesi için
    strategy.yaml + v0001 geçmişi + boş önbellekler."""
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    config.dump_yaml(config.default_strategy(), config.HISTORY / "v0001.yaml")
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
    yield sandbox_state
    config.reload_config()


def _wf(oos, *, dilimli=False, fold_r=None):
    """walk_forward fikstürü. `dilimli=True` üreticinin REJİMLİ çağrıda döndürdüğü ikinci defteri
    de kurar: global kitaptan DAR bir alt küme (n farkı çiviyi ayırt edici kılar — iki defter aynı
    n'i taşısaydı "hangisi yazıldı?" sorusu ölçülemezdi).

    `wf_fixtures` bu alanı ÜRETMEZ ve üretmemeli: fabrikanın `eval_regime` kavramı yoktur ve
    koşulsuz bir alan, "global çağrıda anahtar YOK" yasasını fikstür tarafında yalanlardı."""
    from meridian import score as score_mod
    r = oos if fold_r is None else fold_r
    base = wf.wf_from_scores(oos, folds=((40, r), (40, r)))
    if dilimli:
        base["full_detail_graded"] = score_mod.score_detail(base["_trades_search"][:40],
                                                            config.goal())
    return base


def _kapiyi_sabitle(monkeypatch, inc_wf, cand_wf):
    """`test_ship_baseline_v100._kapiyi_sabitle` ile aynı köprü: kapı fikstürlerden koşar."""
    fixtures = {1: inc_wf, 2: cand_wf}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()


def test_2a_rejim_shipi_EK_ADLI_tam_pencere_defterini_YAZAR(seeded, monkeypatch):
    """YAZANIN ÇİVİSİ. Rejim ship'i artık tam-pencere defterini de karneye düşürür — ama DOĞRU
    popülasyonla ve EK-ADLI anahtarla. `backtest_oos@<rejim>` ile aynı damga mantığı: satırdaki
    sayının hangi nüfustan geldiği ADIN İÇİNDE durur, okuyucunun çıkarımına bırakılmaz."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10, dilimli=True), _wf(0.90, dilimli=True))

    res = reflect.submit({"variable": "entry.min_score@chop", "new": 65})

    assert res["status"] == "shipped" and res["gate"]["eval_regime"] == "chop"
    satir = versioning.scoreboard()["versions"][str(res["version"])]
    bt = satir.get("backtest_full@chop")
    assert isinstance(bt, dict), \
        "rejim ship'i dilimli tam-pencere defterini yine atıyor — rejim satırında ÖNCELİKLİ bacak boş"
    assert isinstance(bt["avg_r"], float) and int(bt["n"]) == 40, \
        "yazılan defter `score_detail` şekli değil ya da DİLİM DEĞİL global popülasyondan geliyor"
    assert "backtest_oos@chop" in satir and "backtest_folds" in satir


def test_2b_rejim_satirina_DUZ_backtest_full_ASLA_dusmez(seeded, monkeypatch):
    """DEĞİŞMEYEN YASA. Ek-ad, düz anahtarın YERİNE geçer — YANINA değil. `rollback`un ve
    `analytics`in düz-anahtar geri-düşüşleri yalnız GLOBAL popülasyonu okumak üzere yazıldı;
    rejim satırına düz bir `backtest_full` düşerse o geri-düşüşler sessizce dilimlenmiş bir sayıyı
    global sanar (uydurma delta → sahte promote/rollback)."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10, dilimli=True), _wf(0.90, dilimli=True))

    res = reflect.submit({"variable": "entry.min_score@chop", "new": 65})

    satir = versioning.scoreboard()["versions"][str(res["version"])]
    assert "backtest_full" not in satir, \
        "rejim satırına DÜZ tam-pencere anahtarı düştü — popülasyon-tutarlılığı kırıldı"


def test_2c_GLOBAL_ship_davranisi_BIT_ES_kaldi(seeded, monkeypatch):
    """REGRESYON KAPISI (v293/v100 çivileri yeşil kalmalı). Global ship DÜZ `backtest_full` yazar
    ve HİÇBİR ek-adlı tam-pencere anahtarı üretmez — bu turun eklediği dal, global yolu tek bir
    alan kadar bile oynatmamalı."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10), _wf(0.90))

    res = reflect.submit({"variable": "entry.min_score", "new": 65})

    assert res["status"] == "shipped" and res["gate"]["eval_regime"] is None
    satir = versioning.scoreboard()["versions"][str(res["version"])]
    assert isinstance(satir.get("backtest_full"), dict), "global ship düz anahtarı kaybetti"
    assert not [k for k in satir if k.startswith("backtest_full@")], \
        "global ship ek-adlı bir tam-pencere anahtarı yazdı — damga popülasyonu yalanlıyor"


def test_2d_URETICI_dilimli_defter_VERMEZSE_anahtar_HIC_YAZILMAZ(seeded, monkeypatch):
    """ÜRETİCİ SÖZLEŞMESİNİ ÇİVİ ZORLAR, SERT İNDEKSLEME DEĞİL (`backtest_full`ün v293 gerekçesiyle
    birebir aynı): `walk_forward`ı taklit eden bir düzine fikstür bu alanı üretmez ve sert
    indeksleme onları konuyla ilgisiz biçimde kırardı — kırılma yeri kusuru değil fikstürü
    gösterirdi. Alan yoksa anahtar HİÇ yazılmaz; `None` yazmak "ölçtük, boş çıktı" olurdu."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10), _wf(0.90))       # dilimli defter YOK

    res = reflect.submit({"variable": "entry.min_score@chop", "new": 65})

    assert res["status"] == "shipped"
    satir = versioning.scoreboard()["versions"][str(res["version"])]
    assert "backtest_full@chop" not in satir and "backtest_full" not in satir, \
        "üretici defteri vermediği hâlde karneye bir tam-pencere anahtarı düştü"
    assert "backtest_folds" in satir, "yedek bacağın kaynağı kurudu"


# =================================================================================================
# YÜZEY 3 — OKUYAN: ek-adlı bacak, ADIYLA
# =================================================================================================
def _detay(avg_r, n=40):
    """`score.score_detail` çıktısının okunan yarısı — kaynak sözleşmesi budur."""
    return {"avg_r": avg_r, "n": n}


def _fold(n, avg_r, i=0):
    """`backtest._fold_metrics` şekli (v293'teki yardımcıyla aynı sözleşme)."""
    return {"start": f"2025-0{i + 1}-01", "end": f"2025-0{i + 2}-01", "n": n, "avg_r": avg_r}


def test_3a_EK_ADLI_bacak_cozulur_ve_KAYNAGINI_adiyla_soyler():
    """OKUYANIN ÇİVİSİ. Rejim satırında düz `backtest_full` YOKtur (yüzey 2'nin yasası); okuyucu
    rejimi satırdaki TEK ek-adlı oos anahtarından TÜRETİR ve `backtest_full@<X>`i dener.

    KAYNAK ADIYLA DURUR: iki farklı popülasyon (tam replay ↔ tam replay'in rejim dilimi) aynı sayı
    sanılamaz. `kapsam` da rejimi ADIYLA anmalı, yoksa okuyucu hangi dilimi gördüğünü bilemez."""
    satir = {"backtest_oos@chop": 0.31, "backtest_full@chop": _detay(0.22, 55)}

    r = analytics._backtest_beklenti_r(satir)

    assert r["avg_r"] == pytest.approx(0.22) and r["n"] == 55
    assert r["kaynak"] == "backtest_full@chop", \
        f"ek-adlı bacak kaynağını adıyla söylemiyor: {r['kaynak']}"
    assert "chop" in (r["kapsam"] or ""), "kapsam hangi rejimin dilimi olduğunu söylemiyor"
    assert "dilim" in (r["kapsam"] or "").lower(), "kapsam metni popülasyonun DAR olduğunu anmıyor"
    assert r["neden"] is None


def test_3b_EK_ADLI_bacak_fold_YEDEGINDEN_once_okunur():
    """SIRA YAZILIDIR VE DEĞİŞMEZ (`backtest_full` ↔ `backtest_folds` ile aynı gerekçe):
    tam-pencere dilimi, aynı dilimin OOS alt kümesinden GENİŞtir. Keyfî seçim yapılmaz."""
    satir = {"backtest_oos@high_vol": 0.4, "backtest_full@high_vol": _detay(0.18, 60),
             "backtest_folds": [_fold(30, 0.30, 0)]}

    r = analytics._backtest_beklenti_r(satir)

    assert r["kaynak"] == "backtest_full@high_vol" and r["avg_r"] == pytest.approx(0.18)


def test_3c_DUZ_anahtar_tasiyan_satirda_davranis_BIT_ES():
    """REGRESYON KAPISI: global satırlarda hiçbir şey değişmedi. Ek-adlı dal yalnız düz anahtar
    ÇÖZÜLEMEYİNCE denenir; düz anahtar varken ona bile bakılmaz."""
    satir = {"backtest_full": _detay(0.20, 95), "backtest_folds": [_fold(30, 0.30, 0)]}

    r = analytics._backtest_beklenti_r(satir)

    assert r["kaynak"] == "backtest_full" and r["avg_r"] == pytest.approx(0.20) and r["n"] == 95
    assert r["kapsam"] == analytics.BACKTEST_BEKLENTI_KAPSAM["backtest_full"]


def test_3d_EK_ADLI_defter_YOKKEN_sessizce_fold_yedegine_duser():
    """Rejim ship'i üreticiden dilimli defter alamadıysa satırda YALNIZ `backtest_oos@<X>` durur.
    Okuyucu bir kaynak UYDURMAZ: yedek bacak konuşur ve `kaynak` onu adıyla söyler."""
    satir = {"backtest_oos@chop": 0.31, "backtest_folds": [_fold(40, 0.15, 0)]}

    r = analytics._backtest_beklenti_r(satir)

    assert r["kaynak"] == "backtest_folds" and r["avg_r"] == pytest.approx(0.15)


def test_3e_IKI_ek_adli_oos_anahtari_varsa_HICBIRI_SECILMEZ_ve_ariza_KONUSUR():
    """UYDURMA YASAĞI, seçim yüzeyinde. Bugünkü üretici satır başına TEK ek-ad yazar; iki tane
    görünürse ya yazan sözleşmeyi kırmıştır ya satır elle kirletilmiştir. "Herhalde ilki" demek
    bir TAHMİNdir ve tavan hükmü o tahmine dayanırdı — hangi rejimin defterini okuduğunu bilmeyen
    bir sayı, ölçüm değildir.

    ARIZA SESSİZ DEĞİL: yedek bacak okunsa bile `backtest_uyari`ya taşınır, yoksa okuyucu ikinci
    bacağı bir TERCİH sanar (v293'ün "biçimsiz `backtest_full`" dersiyle birebir aynı sınıf)."""
    satir = {"backtest_oos@chop": 0.31, "backtest_full@chop": _detay(0.22, 55),
             "backtest_oos@high_vol": 0.12, "backtest_full@high_vol": _detay(0.05, 20),
             "backtest_folds": [_fold(40, 0.15, 0)]}

    r = analytics._backtest_beklenti_r(satir)

    assert r["kaynak"] == "backtest_folds", "belirsiz satırda ek-adlı bir bacak yine de SEÇİLDİ"
    assert r["avg_r"] == pytest.approx(0.15)
    assert "chop" in (r["neden"] or "") and "high_vol" in (r["neden"] or ""), \
        f"belirsizliğin tarafları ADIYLA sayılmadı: {r['neden']}"


def test_3f_IKI_ek_adli_anahtar_ve_fold_YOKSA_hukum_OLCULEMEDI_ve_NEDEN_konusur():
    """Belirsizlik hiçbir bacak çözülmediğinde de GÖRÜNÜR kalmalı. Yalnız "`backtest_full.avg_r`
    YOK" demek, satırda İKİ ek-adlı defter DURUYORKEN yanıltıcı olurdu — okuyucu alanı hiç
    yazılmamış sanar ve yanlış yerde arar."""
    satir = {"backtest_oos@chop": 0.31, "backtest_full@chop": _detay(0.22, 55),
             "backtest_oos@trend_up": 0.12, "backtest_full@trend_up": _detay(0.05, 20)}

    r = analytics._backtest_beklenti_r(satir)

    assert r["avg_r"] is None and r["kaynak"] is None
    assert "chop" in r["neden"] and "trend_up" in r["neden"], \
        f"ölçülemedi nedeni belirsizliği anmıyor: {r['neden']}"


def test_3g_SOZLESME_KAYDI_ek_adli_kaynagi_SABLONUYLA_tasiyor():
    """SÖZLEŞME KAYDI ÜÇÜNCÜ KAYNAĞI TANIYOR. Kayıt, "bu alanı kim hangi kapsamda yazar" sorusunun
    tek yazılı cevabıdır ve çıktıya `backtest_kaynaklar` olarak taşınır (YASA 6). Ek-adlı kaynak
    somut bir rejim adı taşıyamaz (rejim satırdan türetilir), o yüzden kayda ŞABLON olarak girer ve
    dönen `kapsam` o şablondan üretilir — iki metnin ayrışması tek-kaynak ihlali olurdu."""
    assert analytics.EK_ADLI_TAM_PENCERE in analytics.BACKTEST_BEKLENTI_KAYNAKLARI
    assert analytics.EK_ADLI_TAM_PENCERE in analytics.BACKTEST_BEKLENTI_KAPSAM
    # ÖNCELİK SIRASI KAYITTA DA DURUR: geniş olan önce.
    k = list(analytics.BACKTEST_BEKLENTI_KAYNAKLARI)
    assert k.index("backtest_full") < k.index(analytics.EK_ADLI_TAM_PENCERE) \
        < k.index("backtest_folds"), f"sözleşme kaydı okuma sırasını yansıtmıyor: {k}"
    # Şablon ile üretilen metin AYNI kaynaktan gelir.
    uretilen = analytics._backtest_beklenti_r(
        {"backtest_oos@chop": 0.3, "backtest_full@chop": _detay(0.2)})["kapsam"]
    assert uretilen == analytics.BACKTEST_BEKLENTI_KAPSAM[analytics.EK_ADLI_TAM_PENCERE].replace(
        "<rejim>", "chop")


def test_3h_UCTAN_UCA_rejim_shipi_tavan_hukmunu_EK_ADLI_bacaktan_besliyor(seeded, monkeypatch):
    """YASA 6 — ÜÇ YÜZEY TEK KABLO. Üretici döndürdü (yüzey 1), ship yazdı (yüzey 2); bu çivi
    okuyanın GERÇEKTEN o alandan hüküm verdiğini gösterir. Aksi hâlde üç yüzey de kendi içinde
    yeşil kalır ve rejim satırında tavan hükmü yine "ölçülemedi" doğardı (fiş 1/4/9'un rejim yüzü).

    Hangi tarafa düştüğü TAHMİN EDİLMEZ — yalnız hangi BACAKTAN okunduğu çivilenir."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10, dilimli=True), _wf(0.90, dilimli=True))

    res = reflect.submit({"variable": "entry.min_score@chop", "new": 65})
    assert res["status"] == "shipped"

    r = analytics.live_expectancy_ceiling()
    assert r["backtest_kaynak"] == "backtest_full@chop", \
        f"karneye düşen ek-adlı defter OKUNMUYOR (yazıldı ama tüketilmedi): {r['neden']}"
    assert "chop" in (r["backtest_kapsam"] or "")
    assert analytics.EK_ADLI_TAM_PENCERE in r["backtest_kaynaklar"], \
        "çıktının kaynak künyesi üçüncü bacağı anmıyor"
