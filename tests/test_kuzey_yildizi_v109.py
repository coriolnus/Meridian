"""v109 — KUZEY YILDIZI TURU, kanıt motoru tarafı (2026-07-28).

Kapsam: Aşama 2.1 (n-dengeli fold kesimi) ve Aşama 2.2 (OOS aşınma defteri).

İKİ AYRI YANLIŞA KARŞI ÇİVİ:
  * Fold tarafında: takvim eşit UZUNLUKTA pencere üretir, piyasa eşit SAYIDA işlem üretmez. Canlı
    dağılım [45, 46, 7] idi — 7 işlemlik bir pencere, sağlamlık oylamasında 45'likle eşit oy
    kullanıyordu. Kesim işlem sayısına geçerken kapı yasasının SEMANTİĞİ değişmemeli: değişen
    yalnız sınırların nerede kesildiği.
  * Aşınma tarafında: bir OOS penceresi "dokunulmamış" olduğu sürece kanıt taşır. Sayılmayan
    aşınma, kapı hükümlerini sessizce değersizleştirir — kapı hâlâ "OOS'ta kazandı" der.
"""
from __future__ import annotations

import datetime as dt
import inspect

import pytest

from meridian import (backtest, dataset, oos_erosion, reflect, score as score_mod, shadowlaw,
                      store)
from tests import wf_fixtures as wf


def _tr(n, lo, hi, r=0.5, seed=1):
    return wf.trades(n, seed, lo, hi, r)


# =================================================================================================
# D) N-DENGELİ FOLD KESİMİ
# =================================================================================================
def test_kesim_ISLEM_SAYISINA_gore_dengelenir_takvime_gore_degil():
    """Kurgu canlı patolojinin birebir kopyası: ilk iki pencere kalabalık, üçüncüsü neredeyse boş.
    Takvim kesimi [45, 46, 7] üretirdi; n-dengeli kesim üç fold'u da birbirine yakın doldurmalı."""
    trades = (_tr(45, "2023-07-11", "2024-04-01", seed=1)
              + _tr(46, "2024-04-01", "2025-01-11", seed=2)
              + _tr(7, "2025-01-11", "2025-04-01", seed=3))

    bounds = backtest.balanced_fold_bounds(trades, "2025-04-01", dataset.EMBARGO_DAYS)

    assert bounds, "dengeli kesim üretilemedi"
    folds = backtest._fold_metrics(trades, bounds, dataset.EMBARGO_DAYS)
    ns = [f["n"] for f in folds]
    assert min(ns) >= backtest.FOLD_TARGET_N, f"hedef taban tutmadı: {ns}"
    assert max(ns) - min(ns) < 45, f"kesim hâlâ takvim gibi dengesiz: {ns}"


def test_kesim_TAM_DETERMINISTIK():
    """Aynı işlemler → aynı sınırlar, her koşuda. Kesim herhangi bir rastgelelik ya da sözlük
    sırası taşısaydı, kapı kararı koşudan koşuya değişir ve hiçbir hüküm tekrarlanamazdı."""
    trades = _tr(90, "2023-07-11", "2025-04-01", seed=4)
    a = backtest.balanced_fold_bounds(trades, "2025-04-01", dataset.EMBARGO_DAYS)
    b = backtest.balanced_fold_bounds(list(reversed(trades)), "2025-04-01", dataset.EMBARGO_DAYS)
    assert a == b and a, f"kesim deterministik değil: {a} vs {b}"


def test_taban_dolmayinca_fold_sayisi_DUSER_ama_n15_altina_INILMEZ():
    """Brief yasası: hedef n>=25; toplam yetmezse 3→2; n<15 fold ASLA üretilmez. Üç fold'a
    bölündüğünde taban tutmayan bir defter, iki fold'a düşerek kanıtını korur — üç zayıf pencere
    iki sağlam pencereden daha az kanıttır."""
    trades = _tr(41, "2023-07-11", "2025-04-01", seed=5)   # 3'e bölününce taban kırılır, 2'ye tutar

    bounds = backtest.balanced_fold_bounds(trades, "2025-04-01", dataset.EMBARGO_DAYS)

    folds = backtest._fold_metrics(trades, bounds, dataset.EMBARGO_DAYS)
    assert len(folds) == 2, f"fold sayısı düşmedi: {[f['n'] for f in folds]}"
    assert min(f["n"] for f in folds) >= backtest.FOLD_MIN_N


def test_fold_sayisi_veri_arttikca_AZALMAZ():
    """ÖLÇÜLEREK BULUNAN TASARIM HATASI (2026-07-28): "önce hedefi tutturan kesim" kuralı 50
    işlemde 3 fold, 90 işlemde 2 fold üretiyordu — daha çok veri, daha az pencere. Bu yalnız tuhaf
    değil KAPIYI GEVŞETİYORDU: çoğunluk yasasında 2 fold'da BİR galibiyet yeter, 3 fold'da İKİ
    gerekir. Seçim artık "taban tuttuğu sürece en çok fold"."""
    onceki = 0
    for n in (50, 60, 90, 150):
        tr = _tr(n, "2023-07-11", "2025-04-01", seed=5)
        b = backtest.balanced_fold_bounds(tr, "2025-04-01", dataset.EMBARGO_DAYS)
        k = len(backtest._fold_metrics(tr, b, dataset.EMBARGO_DAYS)) if b else 0
        assert k >= onceki, f"n={n}: fold sayısı {onceki} → {k} düştü (daha çok veri, daha az kanıt)"
        onceki = k
    assert onceki == 3


def test_iki_folda_bile_taban_tutmuyorsa_BOS_liste_doner():
    """Boş liste = "kontrol ÇALIŞTIRILAMADI" ve `_gate_eval` bunu `fold_total == 0` olarak okur.
    Zorla 8 işlemlik fold üretmek, sağlamlık iddiasını gürültüden kurmak olurdu."""
    assert backtest.balanced_fold_bounds(_tr(16, "2023-07-11", "2025-04-01", seed=6),
                                         "2025-04-01", dataset.EMBARGO_DAYS) == []
    assert backtest.balanced_fold_bounds([], "2025-04-01", 10) == []


def test_ilk_folda_ambargo_IKI_KEZ_uygulanmaz():
    """Gelen işlemler `walk_forward`ta zaten ambargolu alt sınırdan sonrasını kapsıyor;
    `_fold_metrics` her sınıra ambargo EKLEDİĞİ için ilk sınır o kadar geri alınmalı. Alınmazsa
    ilk fold bir kez daha purge edilir, haksızca incelir ve dengeleme bozulur."""
    trades = _tr(90, "2023-07-11", "2025-04-01", seed=7)
    bounds = backtest.balanced_fold_bounds(trades, "2025-04-01", 10)

    ilk = dt.date.fromisoformat(bounds[0])
    en_erken = min(dt.date.fromisoformat(t["ts_open"][:10]) for t in trades)
    assert ilk == en_erken - dt.timedelta(days=10), \
        f"ilk sınır ambargoyu telafi etmiyor: {bounds[0]} vs en erken işlem {en_erken}"
    # SONUÇ: en erken işlem İLK FOLD'UN İÇİNDE kalmalı. Sınır telafi edilmeseydi `_fold_metrics`in
    # eklediği ambargo onu (ve ardındaki 10 günü) purge ederdi — dengeleme daha doğmadan bozulurdu.
    # NOT: iç sınırlardaki purge YERİNDE KALIR; o, fold'lar arası sızıntı koruması ve kasıtlıdır.
    folds = backtest._fold_metrics(trades, bounds, 10)
    ilk_fold = [t for t in trades if backtest._in_segment(
        t, backtest._embargoed_start(bounds[0], 10), bounds[1])]
    assert any(t["ts_open"][:10] == en_erken.isoformat() for t in ilk_fold), \
        "en erken işlem çifte ambargoyla düşmüş"
    assert folds[0]["n"] > 0


def test_AYNI_sinirlar_incumbent_ve_ADAYA_uygulanir(sandbox_state):
    """KARŞILAŞTIRILABİLİRLİK ŞARTI. Sınırlar yalnız incumbent'tan türetilir; aday kendi kesimini
    doğursaydı her aday kendi lehine bir bölünme üretir ve iki taraf FARKLI pencerelerde ölçülürdü
    — kapının elma-armut yasağının ta kendisi."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.4), (30, 0.4), (30, 0.4)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.6), (30, 0.6), (30, 0.6)))

    _p, gate, _w = reflect._gate_eval(inc, cand)

    assert gate["fold_law"] == "n_dengeli"
    assert gate["fold_bounds"], "sınırlar kapı kaydında görünmüyor"
    assert [f["start"] for f in gate["incumbent_folds"]] == [f["start"] for f in gate["candidate_folds"]]
    assert [f["end"] for f in gate["incumbent_folds"]] == [f["end"] for f in gate["candidate_folds"]]


def test_dilimsiz_sozluk_TAKVIM_davranisini_korur(sandbox_state):
    """Fikstürler ve eski kayıtlar `_trades_search` taşımaz. Yeni yasayı veri olmayan yere
    zorlamak, olmayan bir kesimi varmış gibi raporlamak olurdu."""
    inc = {"oos_score": 0.10, "oos_folds": [{"n": 30, "avg_r": 0.2}, {"n": 30, "avg_r": 0.2}],
           "holdout_score": None}
    cand = {"oos_score": 0.30, "oos_folds": [{"n": 30, "avg_r": 0.5}, {"n": 30, "avg_r": 0.5}],
            "holdout_score": None}

    _p, gate, _w = reflect._gate_eval(inc, cand)

    assert gate["fold_law"] == "takvim" and gate["fold_bounds"] is None
    assert gate["incumbent_folds"] == inc["oos_folds"]


def test_kapi_yasasinin_SEMANTIGI_degismedi():
    """Reform yalnız KESİMİ değiştirir. Marj tabanı, kuyruk marjı ve fold-çoğunluğu aritmetiği
    aynen yerinde; biri sessizce kaysaydı kapı gevşer ve bunu hiçbir yerde göremezdik."""
    assert reflect.GATE_MARGIN == 0.02
    assert reflect.TAIL_MARGIN_R == 0.5
    src = inspect.getsource(reflect._gate_eval)
    assert "fold_wins >= (fold_total + 1) // 2" in src, "çoğunluk aritmetiği değişmiş"
    assert "k_probes=k_probes" in inspect.getsource(reflect._submit_locked) \
        or "k_probes" in src, "K-ceza kanalı kopmuş"


def test_SINAVIN_yarisina_girmeyen_aday_saglamlik_IDDIA_EDEMEZ(sandbox_state):
    """n-dengeli kesimin GEREKTİRDİĞİ koruma (SAPMA: brief 'fold çoğunluğu aynen kalır' diyordu;
    bu ek kural yasayı GEVŞETMEZ, SIKILAŞTIRIR — eklenmeseydi mevcut bir koruma sessizce kaybolurdu).

    Takvim fold'ları, işlemleri tek patlamaya sıkışmış bir adayı "fold 1'de 60, fold 2-3'te sıfır"
    diye gösteriyor ve `fold_total=1` ile çoğunluğu reddediyordu. Dengeli kesim sınırları
    incumbent'ın DAĞILIMINDAN türettiği için aynı patlama İKİ dengeli fold'a bölünebiliyor ve aday
    "birkaç pencerede sağlam" etiketiyle geçiyordu. Sınavın yarısına hiç girmemiş aday geçemez."""
    goal = __import__("meridian.config", fromlist=["goal"]).goal()
    inc_tr = (_tr(60, wf.S_LO, "2024-04-01", 0.05, seed=1)
              + _tr(60, "2024-04-01", "2025-01-11", 0.05, seed=2)
              + _tr(60, "2025-01-11", wf.OOS_END, 0.05, seed=3))
    cand_tr = _tr(60, wf.S_LO, "2024-04-01", 0.95, seed=11)        # YALNIZ ilk pencerede
    inc, cand = wf.wf_from_trades(inc_tr, goal), wf.wf_from_trades(cand_tr, goal)

    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)

    assert gate["fold_uncontested"] >= 1, "boş bırakılan pencere sayılmadı"
    assert passes is False, f"tek pencereye sıkışmış aday kapıyı geçti (fold_wins={gate['fold_wins']})"
    assert "HİÇ işlem yapmadı" in why


# =================================================================================================
# E) OOS AŞINMA DEFTERİ
# =================================================================================================
def test_parmak_izi_pencere_GEOMETRISINE_duyarli():
    """Fold sınırları hash'e DAHİL: n-dengeli kesim onları incumbent'tan türetiyor, yani incumbent
    değişince geometri de değişir. Sınırlar dışarıda kalsaydı gerçekte FARKLI bir sınavı aynı
    sayaca yazardık."""
    a = oos_erosion.fingerprint("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
                                ["2023-07-01", "2024-04-01"], 10)
    assert a == oos_erosion.fingerprint("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
                                        ["2023-07-01", "2024-04-01"], 10), "parmak izi kararsız"
    farkli_fold = oos_erosion.fingerprint("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
                                          ["2023-07-01", "2024-09-01"], 10)
    farkli_ambargo = oos_erosion.fingerprint("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
                                             ["2023-07-01", "2024-04-01"], 20)
    assert len({a, farkli_fold, farkli_ambargo}) == 3, "geometri değişimi parmak izine yansımıyor"


def test_sayac_artar_ve_esik_asilinca_EK_MARJ_dogar(sandbox_state):
    fp = "abc123"
    for i in range(oos_erosion.EROSION_QUERY_LIMIT):
        d = oos_erosion.record(fp)
        assert d["queries"] == i + 1
        assert d["extra_margin"] == 0.0, "eşik dolmadan ceza kesildi"

    son = oos_erosion.record(fp)                       # 21. sorgu — eşiği AŞAR

    assert son["queries"] == oos_erosion.EROSION_QUERY_LIMIT + 1
    assert son["extra_margin"] == oos_erosion.EROSION_EXTRA_MARGIN
    assert oos_erosion.report()["extra_margin_yururlukte"] == oos_erosion.EROSION_EXTRA_MARGIN


def test_status_SAYMAZ_yalnizca_okur(sandbox_state):
    """`_gate_eval` arama döngüsünde, silahlanma yolunda ve onlarca testte çağrılıyor. Her çağrıda
    yazan bir defter, sayacı "kaç resmî soru soruldu"dan "kaç kez fonksiyon çağrıldı"ya çevirirdi."""
    oos_erosion.record("fp1")
    for _ in range(5):
        d = oos_erosion.status("fp1")
    assert d["queries"] == 1 and d["kaydedildi"] is False
    assert oos_erosion.status("hic-gorulmemis")["queries"] == 0


def test_gate_eval_VARSAYILAN_olarak_sayaca_YAZMAZ(sandbox_state):
    """Resmî sayaç yalnız resmî kapı değerlendirmelerini sayar; ön-eleme yükü `k_probes` beyanıyla
    AYRI bir kanaldan taşınır. İkisini tek sayaca toplamak aynı cezayı iki kez kesmek olurdu."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.4), (30, 0.4), (30, 0.4)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.6), (30, 0.6), (30, 0.6)))

    _p, gate, _w = reflect._gate_eval(inc, cand)                       # varsayılan: kaydetme

    assert gate["erosion"]["kaydedildi"] is False
    assert store.read_json(oos_erosion.EROSION_FILE, None) is None, "salt-okuma yol deftere yazdı"

    _p2, gate2, _w2 = reflect._gate_eval(inc, cand, record_erosion=True)

    assert gate2["erosion"]["kaydedildi"] is True and gate2["erosion"]["queries"] == 1
    assert store.read_json(oos_erosion.EROSION_FILE, None) is not None


def test_kapi_kaydi_taban_marji_ile_yururlukteki_marji_AYRI_yazar(sandbox_state):
    """`margin` artık yürürlükteki marj (taban + aşınma). Tabanı ayrı yazmadan bırakmak, kaydı
    sonradan okuyanın "GATE_MARGIN değişmiş" sanmasına yol açardı."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.4), (30, 0.4), (30, 0.4)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.6), (30, 0.6), (30, 0.6)))

    _p, gate, _w = reflect._gate_eval(inc, cand)

    assert gate["gate_margin_base"] == reflect.GATE_MARGIN
    assert gate["margin"] == reflect.GATE_MARGIN, "aşınma yokken marj tabandan sapmış"
    assert gate["erosion"]["limit"] == oos_erosion.EROSION_QUERY_LIMIT


def test_asinmis_pencerede_cita_YUKSELIR(sandbox_state, monkeypatch):
    """Ceza kapıyı KAPATMAZ, çıtayı yükseltir: bir pencereyi yakmanın doğru cevabı "artık soru
    sorma" değil, "artık daha büyük bir fark iste"dir. Zayıf-ama-pozitif bir aday, aşınmamış
    pencerede geçerken aşınmış pencerede geçmemeli.

    GÜNCELLEME GEREKÇESİ (PARA-v3, 2026-07-30) — ÇİVİLENEN ŞEY AYNI, ÖLÇEĞİ DEĞİŞTİ. Eski kurulum
    adayın BİLEŞİK skorunu incumbent'ın 0,005 üstüne koyuyordu ve aşınma marjı (0,01) bileşik
    ölçekte kıyaslandığı için ceza ısırıyordu. Yeni yasada karar değişkeni PARA olduğundan aşınma
    marjı da para ölçeğinde uygulanır (0,01 × 0,1908 ≈ 0,0019) — yoksa skordan ÇIKARDIĞIMIZ
    düşüş/Sharpe bacakları arka kapıdan karara geri sızardı (aday, kârı DEĞİL düşüşünü iyileştirerek
    aşınma cezasını geçebilirdi). Eski fikstür (avg_r 0,30 → 0,55) para ölçeğinde ÇOK BÜYÜK bir
    kazanç demek olduğu için ceza artık ısırmıyordu; senaryo, para farkı marjın ALTINDA kalacak
    biçimde YENİDEN KURULDU ve fark artık ELLE hesaplanıyor (fikstür gürültüsüne bırakılmıyor).

    KURULUM: aday = incumbent'ın AYNI işlemleri + her işleme küçük ve SABİT bir kâr artışı. Böylece
    (a) para farkı tam olarak hedeflenen büyüklükte olur, (b) her replikasyonda ΔS > 0 olduğu için
    olasılıksal yasa aşınmasız hâlde GEÇER (izolasyon sağlanır), (c) fold çoğunluğu da kazanılır
    (r_multiple da artar), yani ret sebebi YALNIZ aşınma marjıdır."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    n_search = len(inc["_trades_search"])
    # Aşınma marjının PARA ölçeğindeki karşılığı — koddan türetilir, elle yazılmaz
    marj_para = oos_erosion.EROSION_EXTRA_MARGIN * shadowlaw.MARGIN_MONEY_SCALE
    span_s = (dt.date.fromisoformat(wf.S_END) - dt.date.fromisoformat(wf.S_LO)).days
    hedef = shadowlaw.hedef_pencere(span_s)
    # Hedef para farkı: marjın YARISI (kesin ALTINDA kalsın) → işlem başına dolar artışı
    bump_usd = (0.5 * marj_para * hedef * score_mod.START_EQUITY) / n_search

    def _bump(ts):
        return [{**t, "r_multiple": round(float(t["r_multiple"]) + 0.002, 5),
                 "pnl_dollars": round(float(t["pnl_dollars"]) + bump_usd, 4)} for t in ts]

    cand = wf.wf_from_trades(_bump(inc["_trades_search"]) + _bump(inc["_trades_confirm"]))
    cand["oos_score"] = 0.105

    temiz, g0, _w = reflect._gate_eval(inc, cand)
    # İZOLASYON KANITI: para farkı POZİTİF ama marjın ALTINDA — yani aşınmasız hâlde geçen aday,
    # yalnızca ceza yüzünden kalacak.
    para_fark = g0["candidate_para"] - g0["incumbent_para"]
    assert 0 < para_fark < marj_para, f"senaryo izole değil: para farkı {para_fark} vs {marj_para}"
    if not temiz:
        pytest.skip("taban senaryo zaten geçmiyor — aşınma etkisi izole ölçülemez")

    monkeypatch.setattr(oos_erosion, "status",
                        lambda fp: {"fingerprint": fp, "queries": 99,
                                    "limit": oos_erosion.EROSION_QUERY_LIMIT,
                                    "extra_margin": oos_erosion.EROSION_EXTRA_MARGIN,
                                    "sayac_baslangici": None, "kaydedildi": False})

    asinmis, gate, why = reflect._gate_eval(inc, cand)

    # BİLEŞİK ölçekli rapor alanları AYNEN korunur (kaydı okuyan "GATE_MARGIN değişmiş" sanmasın)
    assert gate["margin"] == reflect.GATE_MARGIN + oos_erosion.EROSION_EXTRA_MARGIN
    # ...ama YÜRÜRLÜKTE uygulanan marj PARA ölçeğindedir ve kayda o da girer
    assert gate["erosion_margin_para"] == round(marj_para, 6)
    assert asinmis is False and "OOS aşınması" in why and "PARA ölçeğinde" in why


def test_RETRO_DAMGA_YASAGI_kodda_ve_defterde_yazili(sandbox_state):
    """Geçmiş ~38 sorgu geriye dönük damgalanMAZ: hangi pencere geometrisiyle koştuklarını bugün
    bilmiyoruz ve tahmin edilmiş bir sayacı gerçek gibi sunmak tam da bu modülün önlediği şey.
    Beyan KODDA durur ve deftere de YAZILIR — okuyan düşük sayıyı "aşınma yok" sanmasın."""
    assert "retro damga yasağı" in inspect.getsource(oos_erosion).lower()

    bos = oos_erosion.report()
    assert bos["toplam_sorgu"] is None, "sorgu yokken 0 yazıldı — 'ölçmüyoruz' ile 'hiç olmadı' karıştı"

    oos_erosion.record("fp-x")
    doc = store.read_json(oos_erosion.EROSION_FILE, None)
    assert "retro damga yasağı" in doc["beyan"]
    assert doc["sayac_baslangici"], "sayacın ne zaman başladığı defterde yazmıyor"


def test_yazim_dusse_bile_kapi_KARARI_dusmez(sandbox_state, monkeypatch):
    """Bir telemetri defterinin kapıyı durdurma yetkisi yoktur — ama sessiz de kalamaz (YASA 4)."""
    def _patla(*a, **k):
        raise OSError("disk dolu")
    monkeypatch.setattr(oos_erosion, "record", _patla)
    uyarilar = []
    monkeypatch.setattr(oos_erosion.obs, "warn", lambda e, **kw: uyarilar.append(e))

    d = oos_erosion.note("fp-y")

    assert d["queries"] is None and d["extra_margin"] == 0.0
    assert "oos_erosion_write_failed" in uyarilar, "yazım sessizce yutuldu"
