"""KARNE VERİ HATTI — İKİ FİŞ KÖKÜ, TEK SINIF (v293, 2026-08-25).

SINIF: **bir alan üretilmediği için ondan türeyen HÜKÜM `olculemedi` kalıyor** — ve sistem aynı
boşluğu her koşuda yeniden fişliyor. İki kök, aynı çatı:

KÖK A — `backtest_full.avg_r` (fiş 1, 4, 9): `analytics.live_expectancy_ceiling`ın backtest tarafı
BUGÜNE KADAR TEK bir alandan okuyordu (`versions[<sürüm>].backtest_full.avg_r`) ve o alanı karneye
YALNIZ tam re-seed yolu (`run.replay_seed`) yazıyor. Sürümü doğuran diğer iki yol — öğrenme
döngüsünün ship yolu (`reflect._ship` → `versioning.update_scoreboard`) ve operatör kalemi —
onu HİÇ yazmaz. Yani kapı ölçtüğü şeyi diskte YAZILI olduğu hâlde (ship yolu `backtest_folds`
yazıyor ve her fold ÖLÇÜLMÜŞ bir `avg_r` taşıyor) göremiyordu. ÖLÇÜLDÜ (canlı karne kopyası,
2026-08-25): `current_version = 5`, v5 satırı = {params, parent, source, live_since, note} —
`backtest_full` de `backtest_folds` de YOK; v4 satırında `backtest_full` VAR (re-seed yazmış).

KÖK B — `gunluk_m2m_dd` (fiş 7, 8): `analytics._realized_drawdown` m2m bacağını serinin KAPSADIĞI
DÖNEME göre kabul eder; seri kitabın seansını kapsamıyorsa bacak ÖLÇÜLEMEDİ olur, `max_dd` bir ALT
SINIRA döner ve İKİ hüküm birden düşer (`result_verdict.criteria.maks_dusus` +
`edge_verdict.criteria.kuyruk.dd_bacagi`). Bu okuma DOĞRUdur ve bu dosya onu KORUR (B4). Eksik olan
şey okuma değil TEŞHİStİ: çıktı "seri bayat" diyordu ama seriyi kimin yazması gerektiğini, kaç gün
geride olduğunu ve yazarın DENEYİP reddedilmiş mi yoksa HİÇ KOŞMAMIŞ mı olduğunu söylemiyordu —
yani fiş her koşuda aynı cümleyle yeniden doğuyor, hiçbir koşuda AKSİYONA çevrilemiyordu.

ÜÇ ÇİVİ (brief'in a/b/c'si), iki kökte de:
  (a) alan üretiliyor ve ŞEKLİ doğru,
  (b) alan VARKEN hüküm `olculemedi` DEĞİL,
  (c) alan YOKKEN hüküm `olculemedi` + NEDEN — boşluk sessizce "iyi" okunmasın.

(b) çivilerinde HÜKMÜN NE OLACAĞI TAHMİN EDİLMEZ: yalnız "artık `olculemedi` değil" çivilenir.
Eşiğe hiçbir dosyada dokunulmadı; hangi tarafa düştüğünü kod söyler.

GÜNCELLEME 2026-09-01 (akıbet kalemi N00017) — KÖK A YUKARIDAN DA KAPANDI. Ship yolu artık
`backtest_full`ı da yazıyor: `backtest.walk_forward` tam-pencere detayını (`full_detail` =
`BacktestResult.detail(goal)` = `score_detail(...)`) ZATEN döndürüyordu ve ship yolu onu ATIYORDU
— yani yeni bir replay koşulmadan kapatılabilen bir boşluktu. Bu dosyanın aşağıdaki AST çivisi
(`test_A_ship_yolu_backtest_full_YAZIYOR_folds_da_YAZIYOR`) o günkü YOKLUĞU çiviliyordu; kendi
docstring'inin verdiği izinle gövdesi yeni gerçeğe çevrildi. YEDEK BACAK KALDI ve gerekçesi
DARALDI: (i) rejim ship'i `backtest_full` yazMAZ (tam-pencere detayı rejim dilimlenmemiştir —
global bir popülasyonu rejim satırının ÖNCELİKLİ bacağına koymak `backtest_oos@<rejim>`
ek-adının önlediği hatanın ta kendisi olurdu) ve (ii) operatör kalemi satırları hiçbirini yazmaz.
"""
import ast
import json
import pathlib

import pytest

from meridian import analytics, config, ledgerstamp, loop, score as score_mod, store

SRC = pathlib.Path(__file__).resolve().parent.parent / "meridian"


# =================================================================================================
# ORTAK DÜZENEK
# =================================================================================================
def _karne(sandbox_state, surum=5, *, backtest_full=None, backtest_folds=None):
    """Karneyi (scoreboard.json) sentetik olarak kurar. Alan YOKSA anahtar HİÇ yazılmaz —
    `None` yazmak "ölçtük ve boş çıktı" gibi okunurdu, oysa kastedilen "hiç yazılmadı"dır."""
    satir = {"params": {}, "parent": surum - 1}
    if backtest_full is not None:
        satir["backtest_full"] = backtest_full
    if backtest_folds is not None:
        satir["backtest_folds"] = backtest_folds
    store.write_json("scoreboard.json", {"current_version": surum, "versions": {str(surum): satir}})


def _defter(sandbox_state, surum=5, *, canli_r=0.09, n=40):
    """Canlı defter: yürürlükteki sürüme ait, `live_paper` damgalı, R'si ölçülmüş satırlar."""
    store.write_jsonl("trades.jsonl",
                      [{"strategy_version": surum, "r_multiple": canli_r,
                        ledgerstamp.FIELD: ledgerstamp.LIVE_PAPER} for _ in range(n)])


def _fold(n, avg_r, i=0):
    """`backtest._fold_metrics`in ürettiği fold şekli — kaynak sözleşmesi budur."""
    return {"start": f"2025-0{i + 1}-01", "end": f"2025-0{i + 2}-01", "n": n, "avg_r": avg_r}


# =================================================================================================
# KÖK A — (a) ALAN ÜRETİLİYOR VE ŞEKLİ DOĞRU
# =================================================================================================
def test_A_a_avg_r_URETICISI_score_detail_ve_sekli_float(sandbox_state):
    """`backtest_full` bir ayrıntı defteri değil, `score.score_detail`in ÇIKTISIDIR (run.py
    `backtest_full=detail` yazar, `detail = BacktestResult.detail(goal) = score_detail(...)`).
    Üretici burada çivilenir: alan VAR ve SAYIdır — kaybolursa karne tarafı sessizce boşalır."""
    goal = config.goal()
    trades = [{"r_multiple": 0.2, "pnl_dollars": 100.0, "ts_close": f"2026-01-{i % 28 + 1:02d}"}
              for i in range(int(goal.get("min_sample", 30)) + 5)]
    d = score_mod.score_detail(trades, goal)
    assert "avg_r" in d, "score_detail avg_r üretmiyor — karnenin backtest tarafının ÜRETİCİSİ yok"
    assert isinstance(d["avg_r"], float) and d["avg_r"] == pytest.approx(0.2)


def test_A_a_fold_sekli_backtest_ile_AYNI_sozlesmeyi_konusuyor():
    """İkinci bacağın (ship yolu) okuduğu şekil `backtest._fold_metrics`ten gelir: her fold
    `n` ve `avg_r` taşır. Şekil ayrışırsa bacak sessizce boşalır — o yüzden KAYNAKTAN çivilenir."""
    from meridian import backtest as bt
    folds = bt._fold_metrics(
        [{"ts_open": "2025-02-05", "ts_close": "2025-02-10", "r_multiple": 0.5},
         {"ts_open": "2025-02-15", "ts_close": "2025-02-20", "r_multiple": -0.1}],
        ["2025-01-01", "2025-03-01"], 0)
    assert folds and set(folds[0]) >= {"n", "avg_r"}
    assert folds[0]["n"] == 2 and folds[0]["avg_r"] == pytest.approx(0.2)


# =================================================================================================
# KÖK A — (b) ALAN VARKEN HÜKÜM `olculemedi` DEĞİL
# =================================================================================================
def test_A_b_backtest_full_varken_hukum_OLCULEMEDI_degil(sandbox_state):
    """Doğrudan bacak: alan varsa hüküm ölçülür. Hangi tarafa düştüğü TAHMİN EDİLMEZ."""
    _karne(sandbox_state, backtest_full={"avg_r": 0.20, "n": 95})
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] != "olculemedi", r["neden"]
    assert r["backtest_kaynak"] == "backtest_full"
    assert r["backtest_beklenti_r"] == pytest.approx(0.20)


def test_A_b_SHIP_YOLUNUN_yazdigi_folds_da_hukum_verdirir(sandbox_state):
    """KÖK A'NIN ÇİVİSİ. Karnede `backtest_full` YOK ama ship yolunun yazdığı `backtest_folds` VAR.
    Backtest beklentisi diskte ÖLÇÜLMÜŞ hâlde duruyor — hüküm artık `olculemedi` OLAMAZ.

    Ağırlık n'dir: fold'lar farklı uzunlukta ve eşit ağırlık, kısa bir fold'un gürültüsünü uzun
    bir fold'unkiyle aynı sayarak beklentiyi kaydırırdı."""
    _karne(sandbox_state, backtest_full=None,
           backtest_folds=[_fold(30, 0.30, 0), _fold(10, 0.10, 1)])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] != "olculemedi", r["neden"]
    assert r["backtest_kaynak"] == "backtest_folds"
    assert r["backtest_beklenti_r"] == pytest.approx((30 * 0.30 + 10 * 0.10) / 40)
    assert r["backtest_n"] == 40


def test_A_b_backtest_full_ONCELIKLI_folds_yedek(sandbox_state):
    """İki bacak birden varsa ÖNCELİK yazılıdır ve DEĞİŞMEZ: tam-dönem detayı, OOS fold'larının
    özetinden daha geniş bir popülasyondur. İki kaynak arasında keyfî seçim yapılmaz."""
    _karne(sandbox_state, backtest_full={"avg_r": 0.20, "n": 95},
           backtest_folds=[_fold(30, 0.30, 0)])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["backtest_kaynak"] == "backtest_full"
    assert r["backtest_beklenti_r"] == pytest.approx(0.20)


# =================================================================================================
# KÖK A — (c) ALAN YOKKEN `olculemedi` + NEDEN  (regresyon koruması)
# =================================================================================================
def test_A_c_iki_bacak_da_yoksa_OLCULEMEDI_ve_neden_IKISINI_de_aniyor(sandbox_state):
    """Canlı hâl (v5 satırı): ne `backtest_full` ne `backtest_folds`. Hüküm ölçülemez ve NEDEN
    hangi iki alanın eksik olduğunu ADIYLA söyler — okuyucu koda inmeden nereye bakacağını bilsin."""
    _karne(sandbox_state, backtest_full=None, backtest_folds=None)
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi"
    assert "backtest_full.avg_r` YOK" in r["neden"]
    assert "backtest_folds" in r["neden"]
    assert r["backtest_kaynak"] is None
    assert r["backtest_beklenti_r"] is None, "ölçülemeyen taraf SAYIYA çevrilmiş"


def test_A_c_BOS_foldlar_SIFIR_degil_OLCULEMEDI(sandbox_state):
    """REGRESYON KORUMASI — boşluk sessizce "iyi" okunmasın. Fold listesi VAR ama hiçbirinde
    ölçülmüş `avg_r` yok (n=0 pencereler). Ağırlıklı ortalamanın paydası sıfırdır; 0.0 yazmak
    "ölçtük, beklenti sıfır" demek olurdu ve 0 ≤ 0 olduğu için tavan hükmü SAHTE bir sayıya
    dayanırdı."""
    _karne(sandbox_state, backtest_folds=[_fold(0, None, 0), _fold(0, None, 1)])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi"
    assert r["backtest_beklenti_r"] is None and r["backtest_kaynak"] is None


def test_A_c_BICIMSIZ_fold_sessizce_yutulmaz_ama_hukmu_bozmaz(sandbox_state):
    """Biçimsiz tek fold, ölçülmüş fold'ları çöpe atmaz (bilgi kaybı) ama sayıya da girmez
    (uydurma). Payda ÖLÇÜLEN fold'lardan kurulur ve `backtest_n` onu söyler."""
    _karne(sandbox_state, backtest_folds=[_fold(20, 0.25, 0), {"n": "x", "avg_r": "y"}])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["backtest_kaynak"] == "backtest_folds"
    assert r["backtest_beklenti_r"] == pytest.approx(0.25) and r["backtest_n"] == 20


def test_A_c_BICIMSIZ_backtest_full_yedege_dusurur_ama_KAYBOLMAZ(sandbox_state):
    """Birinci bacak BOZUKken ikinci bacaktan okumak bir TERCİH değil bir ARIZA TELAFİSİdir; uyarı
    bunu söylemezse okuyucu `backtest_full`ın bozuk olduğunu HİÇ öğrenmez."""
    _karne(sandbox_state, backtest_full={"avg_r": "yarim", "n": 95},
           backtest_folds=[_fold(20, 0.25, 0)])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["backtest_kaynak"] == "backtest_folds"
    assert r["backtest_beklenti_r"] == pytest.approx(0.25)
    assert "BİÇİMSİZ" in (r["backtest_uyari"] or ""), "birinci bacağın arızası sessizce yutuldu"


def test_A_c_negatif_beklenti_hala_TANIMSIZ_ORAN(sandbox_state):
    """Yedek bacak ESKİ YASAYI GEVŞETMEZ: negatif bir beklentinin yarısı bir tavan değildir.
    Fold'lardan gelen negatif bir ortalama da aynı kapıya çarpar."""
    _karne(sandbox_state, backtest_folds=[_fold(40, -0.05, 0)])
    _defter(sandbox_state, canli_r=-0.01)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi" and "pozitif DEĞİL" in r["neden"]
    assert r["backtest_beklenti_r"] == pytest.approx(-0.05), "ölçülen değer GİZLENMİŞ"


# =================================================================================================
# KÖK A — NEDEN İKİNCİ BACAK GEREKTİ (iddianın kendisi)
# =================================================================================================
def _karne_yazim_anahtarlari(modul: str) -> set:
    """Bir modülün `update_scoreboard`/`set_row_fields` çağrılarına GEÇİRDİĞİ alan adları (AST).

    İKİ BİÇİM DE SAYILIR ve bu 2026-09-01'de ZORUNLU oldu: düz anahtar argüman (`backtest_folds=`)
    VE `**{...}` ile açılan SÖZLÜK SABİTİ. Ship yolu koşullu alanlarını (rejime göre yazılan
    `backtest_oos@<rejim>`, yalnız global ship'te yazılan `backtest_full`) ikinci biçimle geçirir;
    yalnız `kw.arg` toplayan bir dedektör tam da o alanlara KÖR olurdu — yani "karneye kim ne
    yazıyor?" sorusunun statik cevabı, cevabın en oynak yarısını atlardı."""
    tree = ast.parse((SRC / modul).read_text())
    anahtarlar = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        ad = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if ad not in ("update_scoreboard", "set_row_fields"):
            continue
        for kw in node.keywords:
            if kw.arg:
                anahtarlar.add(kw.arg)
                continue
            # `**{...}` — sözlük SABİTİNİN dizge anahtarları (f-string anahtarlar sabit değildir
            # ve bilerek dışarıda kalır: `backtest_oos@{ereg}` statik olarak çözülemez).
            anahtarlar |= {k.value for d in ast.walk(kw.value) if isinstance(d, ast.Dict)
                           for k in d.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return anahtarlar


def test_A_a_full_detail_URETICIDE_VAR_ship_yolunun_okudugu_alan():
    """SHIP YOLUNUN KAYNAĞI ÜRETİCİDE ÇİVİLENİR. Ship yolu `backtest_full`ı yeni bir replay
    koşarak DEĞİL, `walk_forward`ın zaten döndürdüğü `full_detail`den yazar. Üretici o anahtarı
    düşürürse ship yolu sessizce yazmayı bırakır (alan `.get` ile okunur — bkz. `reflect._ship`
    yorumu) ve fiş 1/4/9 geri gelirdi. Kaynak burada, ADIYLA, statik olarak kilitlenir."""
    tree = ast.parse((SRC / "backtest.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "walk_forward")
    anahtarlar = {k.value for d in ast.walk(fn) if isinstance(d, ast.Dict)
                  for k in d.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert "full_detail" in anahtarlar, \
        "walk_forward tam-pencere detayını döndürmüyor — ship yolunun backtest_full KAYNAĞI kurudu"


def test_A_ship_yolu_backtest_full_YAZIYOR_folds_da_YAZIYOR():
    """BU ÇİVİ İKİ BACAĞIN DA KAYNAĞINI ÖLÇER, biçim değil.

    2026-08-25'te bu çivi YOKLUĞU ölçüyordu: `reflect._ship`in `update_scoreboard(...)` çağrıları
    `backtest_folds` yazıyor, `backtest_full` YAZMIYORDU — yani ship edilen bir sürümün tavan
    hükmü ÖNCELİKLİ bacakla asla ölçülemiyordu. 2026-09-01'de kök yukarıdan kapandı (N00017) ve
    testin kendi docstring'i bu güncellemeye izin veriyordu: artık İKİSİ de yazılıyor.

    YEDEK BACAK EMEKLİ OLMADI — gerekçesi daraldı: rejim ship'i `backtest_full` yazmaz (dilimlenmemiş
    popülasyon) ve operatör kalemi ikisini de yazmaz. Bu iki hâlde hüküm hâlâ fold'lardan gelir.

    KIRMIZI YANARSA: ship yolu bir bacağı kaybetmiştir; ÖNCE `reflect._submit_locked`in karne
    yazımına bakılır, sonra bu gövde."""
    anahtarlar = _karne_yazim_anahtarlari("reflect.py")
    assert "backtest_full" in anahtarlar, \
        "ship yolu backtest_full yazmayı bırakmış — ship edilen her sürümde ÖNCELİKLİ bacak yine boş"
    assert "backtest_folds" in anahtarlar, \
        "ship yolu backtest_folds yazmayı bırakmış — yedek bacağın KAYNAĞI kurudu"


# =================================================================================================
# KÖK B — (a) ALAN ÜRETİLİYOR VE ŞEKLİ DOĞRU
# =================================================================================================
def _egri(sandbox_state, son="2026-07-20"):
    """Tohum re-seed'inin bıraktığı eğri: uzun bir seri, `son` gününde biten."""
    pts = [["2023-01-12", 100000.0], ["2024-01-12", 108000.0], ["2025-01-12", 92000.0],
           [son, 94457.91]]
    store.write_json("equity_curve.json", {"version": 4, "points": pts})


def _kitap(sandbox_state, seans="2026-07-28"):
    store.write_json("portfolio.json", {"cash": 94457.91, "realized_pnl": -5542.09,
                                        "positions": {}, "last_date": seans})


def _dolu_defter(sandbox_state, n=95):
    """Kuyruk (n>=40) ve sonuç (n>=30) hükümlerinin ikisini de ölçülebilir kılan bir defter."""
    rows = []
    for i in range(n):
        r = 0.4 if i % 3 else -0.6
        rows.append({"strategy_version": 4, "r_multiple": r, "pnl_dollars": r * 500.0,
                     "costs": 20.0, "ts_close": f"2026-0{i % 6 + 1}-{i % 27 + 1:02d}",
                     ledgerstamp.FIELD: ledgerstamp.LIVE_PAPER})
    store.write_jsonl("trades.jsonl", rows)


def test_B_a_gecikme_ve_YAZAR_adiyla_olculuyor(sandbox_state):
    """TEŞHİS ALANLARI ÜRETİLİYOR VE ŞEKLİ DOĞRU. Fişin bugüne kadar cevaplayamadığı üç soru:
    kaç gün geride · seriyi KİM yazmalı · yazar deneyip mi reddedildi yoksa hiç mi koşmadı."""
    _egri(sandbox_state, son="2026-07-20")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)
    dd = analytics._realized_drawdown()
    assert dd["donem_kapsami"] == "kapsamiyor"
    assert dd["gecikme_gun"] == 8, "seri ile kitap arasındaki gecikme ÖLÇÜLMÜYOR"
    assert dd["yazar"] == analytics.EGRI_KADANSLI_YAZAR == "loop._persist_equity_point"
    # ÇAPA BAYATLAMA KAPISI: ad bir DİZGEdir (analytics loop'u içe aktaramaz). Fonksiyon yeniden
    # adlandırılırsa teşhis sessizce var olmayan bir sembolü işaret ederdi.
    assert hasattr(loop, "_persist_equity_point"), "teşhisin işaret ettiği yazar sembolü YOK"
    assert isinstance(dd["yazar_kanit"], dict)
    assert dd["yazar_kanit"]["durum"] == "olay_yok", dd["yazar_kanit"]
    assert dd["yazar_kanit"]["neden"], "yazar kanıtı NEDENSİZ"


def test_B_a_yazar_DENEYIP_reddedildiyse_kanit_onu_soyler(sandbox_state):
    """İki hipotez tek alanda ayrışır: yazar KOŞTU ve reddedildi (olay defterinde `equity_point_*`)
    ya da HİÇ KOŞMADI (olay yok). Ayrım olmadan fiş her koşuda aynı cümleyle yeniden doğuyordu."""
    from meridian import obs
    _egri(sandbox_state, son="2026-07-20")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)
    obs.warn("equity_point_skipped", neden="öz sermaye ölçülemedi (None) — nokta yazılmadı",
             date="2026-07-28")
    dd = analytics._realized_drawdown()
    assert dd["yazar_kanit"]["durum"] == "olay_var"
    assert dd["yazar_kanit"]["son_olay"] == "equity_point_skipped"
    assert "ölçülemedi" in (dd["yazar_kanit"]["son_neden"] or "")


def test_B_a_seri_kapsiyorken_teshis_alanlari_SUSAR(sandbox_state):
    """Teşhis yalnız kusur hâlinde konuşur: kapsayan bir seride gecikme 0'dır ve yazar kanıtı
    ARANMAZ (olay defterini her okuma turunda taramak, kusursuz hâlde ödenen bir bedeldir)."""
    _egri(sandbox_state, son="2026-07-28")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)
    dd = analytics._realized_drawdown()
    assert dd["donem_kapsami"] == "kapsiyor" and dd["gecikme_gun"] == 0
    assert dd["yazar_kanit"] is None


# =================================================================================================
# KÖK B — (b) ALAN VARKEN HÜKÜM `olculemedi` DEĞİL
# =================================================================================================
def test_B_b_kadansli_nokta_dusunce_IKI_HUKUM_de_olculemediden_cikar(sandbox_state):
    """KÖK B'NİN ÇİVİSİ — VERİ HATTI UÇTAN UCA. Kadanslı yazarın TEK noktası seriyi kitabın
    seansına oturtur; `gunluk_m2m_dd` dolar, `max_dd` alt sınır olmaktan çıkar ve İKİ hüküm birden
    `olculemedi`den çıkar. Hangi tarafa düştüğü TAHMİN EDİLMEZ — kod söyler."""
    _egri(sandbox_state, son="2026-07-20")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)

    once_dd = analytics._realized_drawdown()
    assert once_dd["gunluk_m2m_dd"] is None and once_dd["m2m_durum"] == "donem_disi"
    assert analytics.result_verdict()["criteria"]["maks_dusus"]["status"] == "olculemedi"
    assert analytics.edge_verdict()["criteria"]["kuyruk"]["dd_bacagi"] is None

    mak = loop._persist_equity_point("2026-07-28", 94457.91, store.read_json("portfolio.json", {}))
    assert mak["yazildi"] is True, mak

    sonra_dd = analytics._realized_drawdown()
    assert sonra_dd["m2m_durum"] == "olculdu"
    assert sonra_dd["gunluk_m2m_dd"] is not None
    assert sonra_dd["max_dd_alt_sinir"] is False
    assert sonra_dd["gecikme_gun"] == 0 and sonra_dd["yazar_kanit"] is None
    assert analytics.result_verdict()["criteria"]["maks_dusus"]["status"] != "olculemedi"
    assert analytics.edge_verdict()["criteria"]["kuyruk"]["dd_bacagi"] is not None


# =================================================================================================
# KÖK B — (c) ALAN YOKKEN `olculemedi` + NEDEN  (regresyon koruması)
# =================================================================================================
def test_B_c_bayat_seri_ESIGIN_ALTINDA_bile_GECTI_yazdirmaz(sandbox_state):
    """EN ÖNEMLİ REGRESYON ÇİVİSİ: boşluk sessizce "iyi" okunmasın.

    Bayat seri hâlinde `max_dd` yalnız kapanmış bacaktan gelir ve eşiğin ALTINDA kalır. Ölçülmeyen
    bacağı 0 sayan bir okuma burada "gecti" yazardı — hak edilmemiş bir geçiş. İki hüküm de
    `olculemedi` demeli ve NEDEN'i taşımalı; görülen bayat sayı da GİZLENMEMELİ."""
    _egri(sandbox_state, son="2026-07-20")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)
    dd = analytics._realized_drawdown()
    assert dd["max_dd"] is not None and dd["max_dd"] <= analytics.RESULT_MAXDD_MAX
    assert dd["max_dd"] <= analytics.EDGE_MAXDD_MAX
    assert dd["max_dd_alt_sinir"] is True
    assert dd["bayat_seri_dd"] is not None, "görülen sayı gizlenmiş — hüküm denetlenemez olur"
    assert dd["m2m_neden"]

    rv = analytics.result_verdict()["criteria"]["maks_dusus"]
    ev = analytics.edge_verdict()["criteria"]["kuyruk"]
    assert rv["status"] == "olculemedi" and rv["m2m_neden"]
    assert ev["status"] == "olculemedi" and ev["dd_bacagi"] is None


def test_B_c_kitap_seansi_YOKSA_seri_bayat_SAYILMAZ(sandbox_state):
    """Dedektörün kendi körlüğü bulguya çevrilmez: kitap seansı okunamıyorsa dönem kapsaması
    ÖLÇÜLEMEZ ve seri suçlanmaz. Gecikme de uydurulmaz (None, 0 DEĞİL)."""
    _egri(sandbox_state, son="2026-07-20")
    store.write_json("portfolio.json", {"cash": 1.0, "positions": {}})
    _dolu_defter(sandbox_state)
    dd = analytics._realized_drawdown()
    assert dd["donem_kapsami"] == "olculemedi"
    assert dd["m2m_durum"] == "olculdu" and dd["gunluk_m2m_dd"] is not None
    assert dd["gecikme_gun"] is None and dd["yazar_kanit"] is None


# =================================================================================================
# İKİ KÖK ORTAK — HÜKME GİRMEZ SÖZLEŞMESİ BOZULMADI
# =================================================================================================
def test_ortak_tavan_kolonu_SAYACLARA_dokunmuyor(sandbox_state):
    """Yedek bacak eklendi ama tavan kolonu hâlâ ADVISORY: `criteria` dörtlüsüne girmez ve
    passed/failed/unmeasured paydasını oynatmaz. Sessiz hüküm kayması bu depoda yasak."""
    _karne(sandbox_state, backtest_folds=[_fold(40, 0.30, 0)])
    _dolu_defter(sandbox_state)
    _egri(sandbox_state, son="2026-07-28")
    _kitap(sandbox_state, seans="2026-07-28")
    rv = analytics.result_verdict()
    assert set(rv["criteria"]) == {"dolar_beklenti", "profit_factor", "maks_dusus", "net_pnl"}
    assert rv["tavan_durumu"]["hukme_girmez"] is True
    assert rv["passed"] + rv["failed"] + rv["unmeasured"] + rv["zayif"] == len(rv["criteria"])


def test_ortak_YASA6_teshis_ucLUSU_IKI_HUKME_de_TASINIYOR(sandbox_state):
    """OKUYUCUSUZ YAZIM YOK. Teşhis üçlüsü `_realized_drawdown`ın içinde kalırsa hiçbir yüzey onu
    görmez: iki hüküm de `system_telemetry`ye (`sonuc_hukmu` / `edge_hukmu`) girer ve fiş üreten
    beyin YALNIZ oradan okur. Alanlar burada durmazsa fiş yine "seri bayat" cümlesiyle doğar."""
    _egri(sandbox_state, son="2026-07-20")
    _kitap(sandbox_state, seans="2026-07-28")
    _dolu_defter(sandbox_state)
    md = analytics.result_verdict()["criteria"]["maks_dusus"]
    ku = analytics.edge_verdict()["criteria"]["kuyruk"]
    for olcut, ad in ((md, "sonuc_hukmu.maks_dusus"), (ku, "edge_hukmu.kuyruk")):
        assert olcut["gecikme_gun"] == 8, ad
        assert olcut["egri_yazari"] == analytics.EGRI_KADANSLI_YAZAR, ad
        assert isinstance(olcut["yazar_kanit"], dict) and olcut["yazar_kanit"]["neden"], ad


def test_ortak_ceiling_ciktisi_KAYNAGINI_adiyla_soyluyor(sandbox_state):
    """YASA: hangi bacaktan okunduğu çıktıda ADIYLA durur. İki kaynaklı bir alan, kaynağını
    söylemezse okuyucu iki farklı popülasyonu aynı sayı sanar (fold'lar Search-OOS dilimidir,
    `backtest_full` tam replay penceresidir)."""
    _karne(sandbox_state, backtest_folds=[_fold(40, 0.30, 0)])
    _defter(sandbox_state)
    r = analytics.live_expectancy_ceiling()
    assert r["backtest_kaynak"] in analytics.BACKTEST_BEKLENTI_KAYNAKLARI
    assert r["backtest_kapsam"], "kaynağın KAPSAMI beyan edilmemiş"
    assert "backtest_folds" in r["kaynak"], "künye ikinci bacağı anmıyor"
