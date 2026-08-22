"""test_hafta3a_v119.py — HAFTA 3a: dolar merceği + kuyruk ölçütü + ısı + doğrulama üçlüsü
(ROADMAP §5.1'in ilk yarısı, 2026-07-30)

BU TURUN ORTAK SINIFI: **ölçüt, ölçtüğünü sandığı şeyi ölçmüyordu.**

  1B SONUÇ HÜKMÜ. Sistem "para var mı?" sorusunu R ORTALAMASIYLA yargılıyordu ve R birimi geniş
     stopa yapısal önyargılı (stop genişler → boyut R-nötr küçülür → aynı fiyat hareketi daha az R
     üretir). Üç bağımsız ölçümde aynı desen çıktı: kuyruğu İYİLEŞTİREN adaylar (G3a'nın üç paketi,
     S2 bant filtresi) reddedildi. Şüphe artık adayda değil ölçütte — bu tur ikinci merceği kurar.

  3A KUYRUK. Kapı yasası kuyruk vetosunu 2026-07-22'den beri taşıyor; kuzey yıldızı onu HİÇ
     görmüyordu. Aynı depoda kuyruğun kapıda veto, hükümde yok olması iki farklı risk iştahıydı.

  3B ISI. Pozisyon başına risk kapılı, pozisyon SAYISI kapılı, ama TOPLAM açık risk hiçbir yerde
     tek sayı değildi. Bu turda YALNIZ GÖSTERGE — kapıya bağlanması Hafta 3b.

  Y1 DOĞRULAMA. Kapı "bu aday geçti mi?" diye soruyor, "kaç aday denedik de bu geçti?" diye
     sormuyordu. DSR ve PBO o soruyu sorar — bu turda ADVISORY (passes semantiği DEĞİŞMEZ).

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar (canlı worker eski kodla
çalışıyor; restart operatörde).
"""
from __future__ import annotations

import inspect
import json
import math
import pathlib

import pytest

from meridian import analytics, backtest, codelaw, config, ledgers, score as score_mod, store, validation


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _islem(i: int, r: float, pnl: float, costs: float = 5.0, o: str | None = None,
           c: str | None = None) -> dict:
    gun = (i % 26) + 1
    return {"id": f"T{i:05d}", "ts_open": o or f"2026-01-{gun:02d}",
            "ts_close": c or f"2026-02-{gun:02d}", "ticker": "AAA",
            "entry": 100.0, "exit": 100.0 + r, "qty": 10,
            "r_multiple": r, "pnl_dollars": pnl, "costs": costs,
            "exit_reason": "target" if r > 0 else "stop",
            "plan_id": f"P-2026-01-{gun:02d}-AAA", "regime": "trend_up",
            "score": 80, "setup": "breakout_vcp", "strategy_version": 3}


def _kazanan_defter(n: int = 45) -> list:
    """Dört ölçütü de GEÇEN dolar defteri: pozitif beklenti, PF yüksek, düşüş sığ, net >> friksiyon.
    Deterministik (rastgelelik yok) — aynı defter her koşuda aynı hükmü vermeli."""
    out = []
    for i in range(n):
        kazanan = i % 3 != 2                      # 2/3 kazanan
        out.append(_islem(i, 2.0 if kazanan else -1.0, 900.0 if kazanan else -300.0))
    return out


def _yaz(trades: list, egri: list | None = None) -> None:
    store.write_jsonl("trades.jsonl", trades)
    if egri is not None:
        store.write_json("equity_curve.json", {"version": 4, "points": egri})


# =================================================================================================
# A) SONUÇ HÜKMÜ — DOLAR MERCEĞİ
# =================================================================================================
def test_A_esikler_adlandirilmis_sabit_olarak_TEK_yerde_durur():
    """Eşik koda gömülü olsaydı hüküm denetlenemezdi: okur "1,3 nereden geldi?" diye soramaz,
    testler de eşiği değiştirmeden senaryo kuramazdı (EDGE hükmünün aynı yasası)."""
    assert analytics.RESULT_N_MIN == 30
    assert analytics.RESULT_PF_MIN == 1.3
    assert analytics.RESULT_MAXDD_MAX == 0.16   # 0.08→0.16: operatör kararı 2026-08-13
    assert analytics.RESULT_NET_OVER_FRICTION == 1.0
    # DÜŞÜŞ TAVANI TEK KAYNAK: goal.yaml (operatörün yazılı başarısızlık sınırı), EDGE'in kuyruk
    # ölçütü ve SONUÇ hükmü AYNI sayıyı kullanmak zorunda. Sürüklenirse burası kırmızı yanar.
    assert analytics.RESULT_MAXDD_MAX == analytics.EDGE_MAXDD_MAX == float(
        config.goal()["max_drawdown"]), "düşüş tavanı üç kaynakta ayrıştı"
    # min_sample ile aynı olmak zorunda: aynı depoda "bir istatistik için kaç satır" sorusunun iki
    # cevabı olmamalı.
    assert analytics.RESULT_N_MIN == int(config.goal()["min_sample"])


def test_A_n_tabani_dolmadan_DORDU_DE_OLCULEMEDI_ve_deger_YINE_raporlanir(sandbox_state):
    """UYDURMA YASAĞI: 10 işlemle "profit factor 0,4 — para yok" demek, ölçülemeyen bir şeyi
    ölçülmüş göstermektir. Ama değeri GİZLEMEK de kayıp: "0,4 gördük ama n yetersiz" ile "hiç
    ölçüm yok" aynı cümle değildir."""
    _yaz([_islem(i, -1.0, -300.0) for i in range(10)])
    rv = analytics.result_verdict()
    assert [c["status"] for c in rv["criteria"].values()] == ["olculemedi"] * 4
    assert rv["unmeasured"] == 4 and rv["passed"] == 0
    assert "TAM" not in rv["verdict"]
    # değer YİNE var (gizlenmiyor)
    assert rv["criteria"]["profit_factor"]["value"] is None or \
        rv["criteria"]["dolar_beklenti"]["value"] is not None


def test_A_dordu_de_gecerse_TAM_der(sandbox_state):
    _yaz(_kazanan_defter())
    rv = analytics.result_verdict()
    assert rv["passed"] == 4 and rv["failed"] == 0 and rv["unmeasured"] == 0, rv["criteria"]
    assert "4/4 sağlandı" in rv["verdict"] and "TAM" in rv["verdict"]
    assert all(c["durum"] == "SAGLANDI" for c in rv["criteria"].values())


def test_A_dort_kova_toplami_olcut_sayisini_TUTAR(sandbox_state):
    """Cümle ile sayılar ayrı hesaplansaydı biri diğerini yalanlayabilirdi — okur cümleye inanır."""
    _yaz([_islem(i, -1.0, -300.0) for i in range(40)])
    rv = analytics.result_verdict()
    assert (rv["passed"] + rv["failed"] + rv["unmeasured"] + rv["zayif"]
            == len(rv["criteria"]) == 4)
    assert f"{rv['passed']}/4 sağlandı" in rv["verdict"]
    assert "para kanıtlanmadı" in rv["verdict"]


def test_A_FRIKSIYON_IKI_KEZ_KESILMEZ(sandbox_state):
    """CANLI KAYNAKTAN DOĞRULANMIŞ SÖZLEŞME (broker.close_position): `pnl_dollars` ZATEN nettir
    (kayma dolum fiyatının içinde, iki bacağın komisyonu düşülmüş) ve `costs` broker'ın kendi
    ifadesiyle "informational total friction" — YENİDEN KESİLMEZ. Bu testin var olma sebebi:
    "friksiyon-sonrası beklenti" ifadesi, `costs`ı bir kez daha çıkarmaya DAVET eder ve o hata
    hükmü hak edilmemiş biçimde sertleştirir (95 işlemde $6,12/işlem, yani beklentinin %10'u)."""
    trades = [_islem(i, 1.0, 100.0, costs=50.0) for i in range(40)]
    _yaz(trades)
    b = analytics.result_verdict()["criteria"]["dolar_beklenti"]
    assert b["value"] == 100.0, "beklenti costs ile İKİNCİ KEZ düşülmüş (50.0 çıkarılmış olurdu)"
    assert b["toplam_net"] == 4000.0
    # `costs` yalnız 4. ölçütte KIYAS TABANI: 40×50 = 2000 friksiyon, net 4000 → 2,0× → geçer
    np_ = analytics.result_verdict()["criteria"]["net_pnl"]
    assert np_["toplam_friksiyon"] == 2000.0 and np_["oran"] == 2.0


def test_A_dorduncu_olcut_ISARET_DEGIL_BUYUKLUK_sorar(sandbox_state):
    """4. ölçüt "net > 0" olsaydı 1. ölçütle MATEMATİKSEL OLARAK aynı soruyu sorardı
    (Σpnl = n × ortalama) ve payda şişerdi. Ayrım: net, ÖDENEN FRİKSİYONUN katı olarak yeterli mi?
    Bu defter pozitif net üretir ama friksiyonu bile karşılamaz → 1. ölçüt geçer, 4. KALIR."""
    trades = [_islem(i, 0.05, 10.0, costs=50.0) for i in range(40)]   # net +400, friksiyon 2000
    _yaz(trades)
    c = analytics.result_verdict()["criteria"]
    assert c["net_pnl"]["value"] == 400.0 and c["net_pnl"]["toplam_friksiyon"] == 2000.0
    assert c["net_pnl"]["status"] == "kaldi", "işaret pozitif diye geçirilmiş — büyüklük sorulmuyor"
    assert c["dolar_beklenti"]["value"] > 0, "1. ölçüt bu defterde pozitif olmalıydı"


def test_A_blok_bootstrap_araligi_IID_araliktan_GENIS(sandbox_state):
    """NEDEN BLOK, NEDEN IID DEĞİL: işlem sonuçları bağımsız değildir (kayıp SERİLERİ). IID
    yeniden örnekleme bağımlılığı kırar ve aralığı SİSTEMATİK olarak daraltır — yani ölçülmemiş bir
    kesinlik yazar. Burada bir SERİLİ defter kurulur (ilk yarı kazanç, ikinci yarı kayıp) ve blok
    aralığının IID aralığından geniş olduğu ÖLÇÜLÜR."""
    import numpy as np
    seri = [300.0] * 30 + [-300.0] * 30          # maksimum serisel kümelenme
    _yaz([_islem(i, 1.0 if p > 0 else -1.0, p) for i, p in enumerate(seri)])
    blok = analytics._blok_bootstrap_ci(seri)
    rng = np.random.default_rng(analytics.BOOT_SEED)
    x = np.array(seri)
    iid = np.percentile(x[rng.integers(0, x.size, size=(analytics.BOOT_N, x.size))].mean(axis=1),
                        [2.5, 97.5])
    assert (blok["hi"] - blok["lo"]) > (iid[1] - iid[0]), \
        f"blok aralığı IID'den geniş DEĞİL: blok {blok['lo']}..{blok['hi']} vs IID {iid}"
    assert blok["blok"] == analytics.BOOT_BLOCK_TRADES
    assert "circular blok bootstrap" in blok["yontem"]


def test_A_blok_uzunlugu_score_tail_risk_ILE_AYNI():
    """Aynı depoda "işlem ekseninde bağımlılık bloğu ne kadar uzun?" sorusunun iki cevabı olmamalı.
    `score.tail_risk` circular-block bootstrap'ı 5 kullanıyor; dolar aralığı da 5 kullanır."""
    kaynak = inspect.getsource(score_mod.tail_risk)
    assert "block = min(5, horizon)" in kaynak, "tail_risk'in blok boyu değişmiş — sabiti eşitle"
    assert analytics.BOOT_BLOCK_TRADES == 5


def test_A_zayif_durumu_MUMKUN_ve_anlamlilik_beyani_dogru(sandbox_state):
    """1. ölçütün anlamlılık HESABI VAR (blok-bootstrap aralığı) → ZAYIF mümkün. 2./3./4.'ün
    hesabı YOKTUR ve bunu `anlamlilik_hesabi: False` ile AÇIKÇA söylerler; onlara "anlamlı değil"
    damgası basmak yapılmamış bir testin sonucunu uydurmak olurdu."""
    _yaz(_kazanan_defter())
    c = analytics.result_verdict()["criteria"]
    assert c["dolar_beklenti"]["anlamlilik_hesabi"] is True
    for ad in ("profit_factor", "maks_dusus", "net_pnl"):
        assert c[ad]["anlamlilik_hesabi"] is False, f"{ad}: hesap beyanı yanlış"
        assert c[ad]["status"] != "zayif", f"{ad}: hesabı yokken ZAYIF damgası basılmış"
    # ZAYIF fiilen ulaşılabilir mi? Pozitif ama gürültülü bir defter kurulur.
    _yaz([_islem(i, 1.0 if i % 2 else -1.0, 1000.0 if i % 2 else -980.0) for i in range(40)])
    b = analytics.result_verdict()["criteria"]["dolar_beklenti"]
    assert b["value"] > 0 and b["anlamli"] is False and b["status"] == "zayif", b


def test_A_karar_kullanimi_hukmun_ICINDE_yazili(sandbox_state):
    """Rafineri kararı EDGE'e, sermaye/silahlanma İKİSİNE bakar (ROADMAP §5.1). Bu kural bir
    oturum notunda kalırsa bir sonraki turda kaybolur — hükmün kendi payload'ında durur."""
    _yaz(_kazanan_defter())
    rv = analytics.result_verdict()
    assert "rafineri" in rv["karar_kullanimi"] and "sermaye" in rv["karar_kullanimi"]
    assert "USD" in rv["birim"]
    # EDGE hükmü de aynı ayrımı docstring'inde taşır (iki hüküm birbirine referans verir)
    assert "result_verdict" in (analytics.edge_verdict.__doc__ or "")


# =================================================================================================
# B) KUYRUK — KUZEY YILDIZININ BEŞİNCİ ÖLÇÜTÜ
# =================================================================================================
def test_B_hukum_artik_BES_olcut_ve_cumle_x_bolu_5(sandbox_state):
    _yaz(_kazanan_defter())
    ev = analytics.edge_verdict()
    assert len(ev["criteria"]) == 5 and "kuyruk" in ev["criteria"]
    assert "/5 sağlandı" in ev["verdict"]


def test_B_n_tabani_dolmadan_OLCULEMEDI_ama_deger_raporlanir(sandbox_state):
    """n < EDGE_TAIL_N_MIN: %5'lik dilim n=20'de tek işlemdir ve tek işlem bir dağılım değil bir
    anekdottur. Ama ölçülen düşüş/CVaR YİNE payload'da durur."""
    _yaz([_islem(i, -1.0, -300.0) for i in range(20)])
    k = analytics.edge_verdict()["criteria"]["kuyruk"]
    assert k["status"] == "olculemedi" and k["n"] == 20
    assert k["max_dd"] is not None and k["cvar5_r"] is not None, "değer gizlenmiş"
    assert k["esikler"]["n_min"] == analytics.EDGE_TAIL_N_MIN == 40


@pytest.mark.parametrize("dd_iyi,cvar_iyi,beklenen", [
    (True, True, "gecti"),
    (True, False, "kaldi"),      # kuyruk kalın → veto (düşüş sığ olsa bile)
    (False, True, "kaldi"),      # düşüş derin → veto (stop disiplini kusursuz olsa bile)
    (False, False, "kaldi"),
])
def test_B_IKI_BACAK_BIRDEN_gerekir_VE_degil_VEYA(sandbox_state, dd_iyi, cvar_iyi, beklenen):
    """İKİ AYRI SORU: maks düşüş YOL riskini ölçer (sıralanmış kayıpların bileşiği), CVaR%5 BİRİM
    riskini (tek işlemin en kötü %5'i risk birimini aşıyor mu). Bir sistem stop disiplinini
    kusursuz uygulayıp üst üste kayıplarla derin düşebilir; ya da düşüşü küçük tutup tek bir
    boşlukta 4R yiyebilir. Biri diğerini AFFEDEMEZ — bağlaç VE olmak zorunda."""
    n = 45
    trades = []
    for i in range(n):
        kazanan = i % 3 != 2
        r = 2.0 if kazanan else (-1.0 if cvar_iyi else -4.0)
        trades.append(_islem(i, r, 900.0 if kazanan else -300.0))
    # Düşüş bacağı: günlük M2M eğrisi ile kurulur (kapanmış eğri işlemlerden gelir).
    egri = ([["2026-01-01", 100000.0], ["2026-01-02", 100000.0]] if dd_iyi
            else [["2026-01-01", 100000.0], ["2026-01-02", 80000.0]])   # %20 düşüş
    _yaz(trades, egri)
    k = analytics.edge_verdict()["criteria"]["kuyruk"]
    assert k["status"] == beklenen, (dd_iyi, cvar_iyi, k)
    if k["status"] != "olculemedi":
        assert k["dd_bacagi"] is dd_iyi
        assert k["cvar_bacagi"] is cvar_iyi


def test_B_maks_dusus_IKI_EGRININ_KOTUSUNU_okur(sandbox_state):
    """DENETİM #6'NIN AYNI DERSİ: yalnız kapanmış işlemlere bakan bir eğri AÇIK pozisyonların
    düşüşünü GİZLER. Canlı ölçüm bu ayrımın ne kadar önemli olduğunu gösterdi (2026-07-30):
    kapanmış eğri %5,70, günlük eğri %8,04 — yani kapanmış eğri tek başına okunsaydı hem SONUÇ
    hükmü hem EDGE'in 5. ölçütü eşiği GEÇMİŞ görünürdü, düşüş hiç küçülmemişken."""
    _yaz(_kazanan_defter(), [["2026-01-01", 100000.0], ["2026-01-02", 85000.0]])  # %15 M2M düşüşü
    dd = analytics._realized_drawdown()
    assert dd["gunluk_m2m_dd"] > dd["kapali_islem_dd"]
    assert dd["max_dd"] == dd["gunluk_m2m_dd"], "kötü olan seçilmemiş"
    # İKİ HÜKÜM TEK KAYNAKTAN: EDGE'in kuyruğu ve SONUÇ'un maks düşüşü aynı sayıyı görmek zorunda.
    assert analytics.edge_verdict()["criteria"]["kuyruk"]["max_dd"] == \
        analytics.result_verdict()["criteria"]["maks_dusus"]["value"] == dd["max_dd"]


def test_B_gunluk_egri_OKUNAMAZSA_sessiz_kalmaz(sandbox_state, monkeypatch):
    """YASA 4: günlük eğri okunamazsa düşüş SESSİZCE küçülür (yalnız kapanmış eğri kalır) ve iki
    hüküm de hak etmediği bir SAGLANDI alabilir. Davranış aynı kalır, ama neden GÖRÜNÜR."""
    _yaz(_kazanan_defter())
    store.write_json("equity_curve.json", {"version": 4, "points": [["2026-01-01", "bozuk"]]})
    kayitlar = []
    from meridian import obs
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: kayitlar.append(ev))
    dd = analytics._realized_drawdown()
    assert dd["gunluk_m2m_dd"] is None and dd["kapali_islem_dd"] is not None
    assert "mtm_curve_unreadable" in kayitlar, "sessiz yutma — düşüş küçüldü, kimse duymadı"
    assert "günlük eğri okunamadı" in dd["kaynak"]


def test_B_CVaR_ISARET_SOZLESMESI_cikitinin_ICINDE_yazar(sandbox_state):
    """`score.tail_risk` VaR/CVaR'ı POZİTİF kayıp büyüklüğü olarak ve 20 işlemlik UFUK üzerinde
    raporlar; buradaki hesap TEK işlemin R dağılımının alt kuyruğudur ve işaret GETİRİ yönündedir.
    İki sözleşmeyi aynı ada sıkıştırmak bir işaret hatasıyla vetoyu TERSİNE çevirebilirdi."""
    _yaz(_kazanan_defter())
    k = analytics.edge_verdict()["criteria"]["kuyruk"]
    assert k["cvar5_r"] < 0, "işaret getiri yönünde değil (kayıp pozitif yazılmış)"
    assert "getiri yönünde" in k["isaret"] and "score.tail_risk" in k["isaret"]
    # score.tail_risk'in kendi sözleşmesi DEĞİŞMEDİ (pozitif kayıp) — iki taraf ayrı ayrı doğru
    tr = score_mod.tail_risk([_islem(i, -1.0, -300.0) for i in range(30)])
    assert tr is not None and tr["cvar_r"] > 0


def test_B_esikler_gerekcesiyle_birlikte_adlandirilmis():
    assert analytics.EDGE_TAIL_N_MIN == 40
    assert analytics.EDGE_MAXDD_MAX == 0.16   # 0.08→0.16: operatör kararı 2026-08-13
    assert analytics.EDGE_CVAR5_MIN_R == -1.5
    src = inspect.getsource(analytics)
    # Gerekçe YASADAN türer, ölçümden değil: boyutlayıcı adedi risk_$/(giriş−stop) kurar → stopa
    # uyulan çıkış tam −1,0R'dir; −1,5R risk biriminin yarısı kadar boşluk hasarına izin verir.
    i = src.index("EDGE_CVAR5_MIN_R = -1.5")
    assert "giriş − stop" in src[i:i + 2000] or "giriş − stop" in src[i - 500:i + 2000]


# =================================================================================================
# C) PORTFÖY ISISI — YALNIZ GÖSTERGE
# =================================================================================================
def test_C_acik_pozisyon_yokken_isi_SIFIR_degil_None(sandbox_state):
    """"Masada hiçbir şey yok" ÖLÇÜLMÜŞ bir gerçektir; None dönmek "bilmiyoruz" derdi."""
    store.write_json("portfolio.json", {"cash": 100000.0, "positions": {}})
    h = analytics.portfolio_heat()
    assert h["isi_pct"] == 0.0 and h["acik_risk_dolar"] == 0.0 and h["n_pozisyon"] == 0


def test_C_yururlukteki_stop_okunur_ve_ilk_stop_KIYAS_olarak_yaninda(sandbox_state):
    """`analytics.today.current_exposure_pct` GİRİŞTEKİ riski toplar — stop yukarı taşındıkça
    gerçek risk düşer ve pano olduğundan SICAK görünür. Isı yürürlükteki stopu okur; giriş stopuna
    göre hesap kıyas olarak yanında durur (ikisi bir kazananda ciddi biçimde ayrışır)."""
    store.write_json("portfolio.json", {"cash": 100000.0, "positions": {
        "AAA": {"ticker": "AAA", "entry": 100.0, "stop": 90.0, "trail_stop": 95.0, "qty": 100}}})
    h = analytics.portfolio_heat()
    assert h["acik_risk_dolar"] == 500.0          # (100−95)×100
    assert h["ilk_stop_riski_dolar"] == 1000.0    # (100−90)×100
    assert h["isi_pct"] == 0.5 and h["ilk_stop_isi_pct"] == 1.0


def test_C_kilitli_kar_DIGER_pozisyonu_MAHSUP_ETMEZ(sandbox_state):
    """Trail'i girişin üstüne çıkmış pozisyonun riski negatiftir (kilitlenmiş kâr) — ama o negatif
    BAŞKA bir pozisyonun açık riskini düşüremez. Toplamda mahsup edilse ısı olduğundan SOĞUK
    okunurdu ve ısı tavanı Hafta 3b'de kapıya bağlanacak."""
    store.write_json("portfolio.json", {"cash": 100000.0, "positions": {
        "AAA": {"ticker": "AAA", "entry": 100.0, "stop": 90.0, "trail_stop": 120.0, "qty": 100},
        "BBB": {"ticker": "BBB", "entry": 50.0, "stop": 45.0, "trail_stop": 45.0, "qty": 100}}})
    h = analytics.portfolio_heat()
    assert h["acik_risk_dolar"] == 500.0, "kilitli kâr diğer pozisyonun riskini mahsup etti"
    assert [s["risk_dolar"] for s in h["pozisyonlar"]] == [0.0, 500.0]


def test_C_eksik_alanli_pozisyon_SAYILIR_ve_UYARIR(sandbox_state, monkeypatch):
    """YASA 4: eksik alanlı bir pozisyon sessizce 0 risk sayılırsa ısı olduğundan soğuk okunur ve
    Hafta 3b'de o sessizlik kapının göremediği bir risk olur."""
    store.write_json("portfolio.json", {"cash": 100000.0, "positions": {
        "AAA": {"ticker": "AAA", "entry": 100.0, "qty": 100},          # stop YOK
        "BBB": {"ticker": "BBB", "entry": 50.0, "stop": 45.0, "trail_stop": 45.0, "qty": 100}}})
    kayitlar = []
    from meridian import obs
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: kayitlar.append(ev))
    h = analytics.portfolio_heat()
    assert h["n_eksik"] == 1 and h["acik_risk_dolar"] == 500.0
    assert "heat_position_incomplete" in kayitlar


def test_C_ISI_BU_TURDA_HICBIR_KAPIYA_BAGLI_DEGIL():
    """3B'nin yazılı sınırı: ısı YALNIZ GÖSTERGEdir. Isı TAVANI (açık risk ≤ NAV %6-8) Hafta 3b'nin
    default-OFF knob'u olacak; bu turda emir akışına dokunması ölçülmemiş bir eşiğin canlı kararı
    kesmesi demekti (ROADMAP §6: ölçüm ÖNCE, kapı SONRA). Karar veren modüller taranır."""
    for mod in ("guard.py", "broker.py", "reflect.py", "loop.py", "arming.py", "risk.py"):
        p = pathlib.Path("meridian") / mod
        if not p.exists():
            continue
        src = p.read_text()
        assert "portfolio_heat" not in src and "isi_pct" not in src, \
            f"{mod} ısıyı okuyor — bu turda ısı hiçbir karara girmemeli"
    assert "YALNIZ GÖSTERGE" in analytics.portfolio_heat.__doc__ or \
        "YALNIZ GÖSTERGE" in inspect.getsource(analytics.portfolio_heat)


# =================================================================================================
# D) Y1 DOĞRULAMA ÜÇLÜSÜ — DSR / PBO / DEFTER (HEPSİ ADVISORY)
# =================================================================================================
def test_D_dsr_taban_altinda_None_doner_SIFIR_DEGIL():
    """UYDURMA YASAĞI: 5 gözlemle bir DSR üretmek, √(n−1)=2 çarpanıyla çarpıklık/basıklık
    tahminlerinin kendi standart hatalarından küçük olduğu bir bölgede sayı icat etmektir."""
    assert validation.deflated_sharpe([0.01] * 10, 100) is None
    assert validation.DSR_MIN_N == 20
    # varyansı SIFIR olan seri de ölçülemez (sabit getiri → Sharpe tanımsız)
    assert validation.deflated_sharpe([0.01] * 40, 100) is None


def test_D_deflasyon_DENEME_SAYISIYLA_MONOTON_SIKILASIR():
    """DSR'nin var olma sebebi: aynı Sharpe, 300 denemeden seçildiyse 1 denemeden seçildiğinden
    DAHA AZ şaşırtıcıdır. N büyüdükçe DSR düşmek ZORUNDA."""
    seri = [0.01 * ((i % 7) - 2) for i in range(60)]
    ds = [validation.deflated_sharpe(seri, n)["dsr"] for n in (2, 10, 50, 300)]
    assert all(a >= b for a, b in zip(ds, ds[1:])), f"deflasyon monoton değil: {ds}"
    # N < 2 → deflasyon YOK ve DSR, deflate edilmemiş PSR(0)'a EŞİT olmalı (formülün sınır hâli)
    tek = validation.deflated_sharpe(seri, 1)
    assert tek["beklenen_maks_sharpe"] == 0.0
    assert tek["dsr"] == tek["psr_sifir"]


def test_D_carpiklik_basiklik_DUZELTMESI_gercekten_ETKILI():
    """Payda `1 − γ3·SR + ((γ4−1)/4)·SR²`. Kalın kuyruk ve negatif çarpıklık aynı Sharpe'ı DAHA AZ
    kanıtlı yapar. Düzeltme etkisiz olsaydı formül normal-dağılım güveni yazıyor olurdu — ve bu
    depoda kuyruk gerçek (canlı işlem-getiri basıklığı 3,83, çarpıklık −0,26)."""
    n, sr = 95, 0.2
    normal = validation.psr(sr, n, skew=0.0, kurtosis=3.0)
    kuyruklu = validation.psr(sr, n, skew=-1.0, kurtosis=8.0)
    assert kuyruklu < normal, f"düzeltme etkisiz: {kuyruklu} vs {normal}"
    # payda tanımsızsa (kök içi <= 0) None — küçük bir tabana kıstırmak sayı uydurmak olurdu
    assert validation.psr(5.0, n, skew=10.0, kurtosis=3.0) is None


def test_D_varyans_kaynagi_CIKTIDA_YAZAR_ve_defterle_OLCULUR():
    """BEYAN (3): deneme-Sharpe varyansı iki kaynaktan gelebilir ve hangisi olduğu gizlenemez —
    ölçülmüş bir varyans ile varsayılmış bir null aynı sayı değildir."""
    seri = [0.01 * ((i % 5) - 2) for i in range(60)]
    yok = validation.deflated_sharpe(seri, 50)
    assert yok["varyans_kaynagi"] == "sifir_beceri_null" and yok["deneme_sharpe_n"] == 0
    var = validation.deflated_sharpe(seri, 50, trial_sharpes=[0.1, -0.2, 0.05, 0.3, -0.1, 0.0])
    assert var["varyans_kaynagi"] == "deneme_defteri" and var["deneme_sharpe_n"] == 6
    assert validation.DSR_TRIAL_VAR_MIN_N == 5
    # 5'in ALTINDA ölçüm yapılmaz (gürültülü bir varyans, varsayımdan kötüdür)
    az = validation.deflated_sharpe(seri, 50, trial_sharpes=[0.1, -0.2])
    assert az["varyans_kaynagi"] == "sifir_beceri_null"


def test_D_pbo_taban_dolmadan_OLCULEMEDI(sandbox_state):
    assert validation.PBO_MIN_ADAY == 8
    p = validation.pbo_cscv([])
    assert p["durum"] == "olculemedi" and p["pbo"] is None and "0/8" in p["neden"]
    # 7 adayla da ölçülmez (taban SERT)
    rows = [{"etiket": f"a{i}", "seri": [[f"2026-01-{d:02d}", 0.1] for d in range(1, 21)]}
            for i in range(7)]
    assert validation.pbo_cscv(rows)["durum"] == "olculemedi"


def test_D_pbo_OVERFIT_verisinde_YUKSEK_gercek_edge_de_DUSUK(sandbox_state):
    """PBO'nun YÖN GEÇERLİLİĞİ. İki sentetik dünya:
      * GÜRÜLTÜ dünyası — hiçbir adayın gerçek kenarı yok, IS'te en iyi görünen OOS'ta rastgele →
        PBO yüksek (%50 civarı: seçim yazı-tura).
      * KENAR dünyası — bir aday HER blokta tutarlı biçimde daha iyi → IS'te seçilen OOS'ta da
        kazanır → PBO düşük.
    Bu ayrımı yapamayan bir PBO, ölçüt değil süstür."""
    import random
    tarihler = [f"2026-{m:02d}-{d:02d}" for m in range(1, 7) for d in range(1, 9)]
    rnd = random.Random(7)
    gurultu = [{"etiket": f"n{i}", "seri": [[t, rnd.gauss(0, 1)] for t in tarihler]}
               for i in range(10)]
    kenar = [{"etiket": f"e{i}",
              "seri": [[t, rnd.gauss(0.05, 1) + (2.5 if i == 0 else 0.0)] for t in tarihler]}
             for i in range(10)]
    p_g, p_k = validation.pbo_cscv(gurultu), validation.pbo_cscv(kenar)
    assert p_g["durum"] == "olculdu" and p_k["durum"] == "olculdu"
    assert p_g["pbo"] > p_k["pbo"], f"PBO iki dünyayı ayırmıyor: gürültü {p_g['pbo']} vs kenar {p_k['pbo']}"
    assert p_k["pbo"] < 0.2, f"gerçek kenar dünyasında PBO yüksek çıktı: {p_k['pbo']}"
    assert p_g["n_kombinasyon"] == math.comb(validation.PBO_BLOCKS, validation.PBO_BLOCKS // 2)


def test_D_pbo_izgarasi_BIRLESIM_ve_islemsiz_gun_SIFIR(sandbox_state):
    """Izgara KESİŞİM olsaydı birkaç güne çökerdi (iki aday asla aynı günlerde işlem yapmaz).
    İşlem yapılmayan gün 0.0'dır ve bu UYDURMA DEĞİL o günün gerçekleşen getirisidir."""
    rows = [{"etiket": "a", "seri": [["2026-01-01", 1.0]]},
            {"etiket": "b", "seri": [["2026-01-02", -1.0]]}]
    tarihler, adaylar, mat = validation._matris(rows)
    assert tarihler == ["2026-01-01", "2026-01-02"] and adaylar == ["a", "b"]
    assert mat == [[1.0, 0.0], [0.0, -1.0]]
    # AYNI GÜNDE çok işlem → o günün toplam getirisi
    t2, _, m2 = validation._matris([{"etiket": "c", "seri": [["2026-01-01", 1.0],
                                                            ["2026-01-01", 0.5]]}])
    assert m2 == [[1.5]]


def test_D_defter_SOZLESMESI_kayitli_ve_satir_UYUYOR(sandbox_state):
    """`seri` ve `sharpe_gozlem` ZORUNLU: serisiz bir satır PBO paydasından SESSİZCE düşer
    (`trades.jsonl`ın `setup`/`score` dersinin aynısı)."""
    c = ledgers.CONTRACTS[validation.LEDGER_FILE]
    assert "seri" in c.required and "sharpe_gozlem" in c.required
    assert c.writers == ("validation.py",)
    satir = {"ts": "2026-07-30T00:00:00+00:00", "fingerprint": "abc", "etiket": "x=1",
             "seri": [["2026-01-01", 0.5]], "sharpe_gozlem": 0.1, "n_trials": 10, "passes": False}
    assert ledgers.validate_row(validation.LEDGER_FILE, satir) == []
    assert ledgers.validate_row(validation.LEDGER_FILE, {k: v for k, v in satir.items()
                                                         if k != "seri"}) != []
    assert validation.record_candidate(satir) is not None
    assert len(store.read_jsonl(validation.LEDGER_FILE)) == 1


def test_D_defter_yazimi_KAPIYI_DUSURMEZ_ama_sessiz_kalmaz(sandbox_state, monkeypatch):
    """Bir doğrulama defterinin ship kararını durdurma yetkisi YOKTUR (YASA 4: ama sessiz de
    kalamaz)."""
    kayitlar = []
    from meridian import obs
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: kayitlar.append(ev))
    monkeypatch.setattr(store, "append_jsonl",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk dolu")))
    assert validation.record_candidate({"ts": "x"}) is None
    assert "validation_ledger_write_failed" in kayitlar


def test_D_yeni_artefakt_YASA6_ihlali_URETMEZ():
    """Yeni bir state dosyası, DIŞ bir modül tarafından okunmadıkça "yazılıyor ama okunmuyor"
    ihlalidir. Zincir: validation.py yazar → analytics.validation_trio okur → api servis eder →
    pano gösterir. `analytics`teki okuma LİTERAL dosya adıyla yapılır, çünkü statik graf bir
    fonksiyon içindeki okumayı o fonksiyonu BARINDIRAN modüle sayar."""
    g = codelaw.artifact_graph()
    assert g["violations"] == [], g["violations"]
    a = g["artifacts"][validation.LEDGER_FILE]
    assert a["writers"] == ["validation.py"]
    assert "analytics.py" in a["external_readers"] and a["unread"] is False


# =================================================================================================
# D2) KAPI YOLU — DSR ADVISORY, DEFTER YALNIZ RESMÎ DEĞERLENDİRMEDE
# =================================================================================================
def _wf(scores: list, n: int = 40, oos: float = 0.10) -> dict:
    """`walk_forward` çıktısının kapı için gereken minimal şekli (dilimsiz → legacy marj yasası)."""
    tr = [{"ts_open": f"2026-01-{(i % 26) + 1:02d}", "ts_close": f"2026-02-{(i % 26) + 1:02d}",
           "r_multiple": scores[i % len(scores)],
           "pnl_dollars": scores[i % len(scores)] * 300.0} for i in range(n)]
    return {"oos_score": oos, "holdout_score": None, "params": {"entry.min_score": 60},
            "oos_folds": [{"start": "2026-01-01", "end": "2026-02-01", "n": n // 2, "avg_r": 0.1},
                          {"start": "2026-02-01", "end": "2026-03-01", "n": n // 2, "avg_r": 0.1}],
            "oos_tail_risk": None, "oos_detail": {"n": n, "components": {"ret": 0.05, "dd": 0.3,
                                                                        "sharpe": 0.2},
                                                  "avg_r": 0.1, "sharpe": 0.5},
            "_trades_search": tr, "eval_regime": None}


def test_D2_kapi_kaydinda_dsr_alani_var_ve_ADVISORY(sandbox_state):
    """Kapı kaydına `dsr` girer ama `passes` hükmüne GİRMEZ. Kod düzeni de bunu garanti eder:
    `passes` satırı DSR bloğundan ÖNCE gelir."""
    from meridian import reflect
    inc = _wf([1.0, -1.0, 2.0, -1.0], oos=0.10)
    cand = _wf([1.0, -1.0, 2.0, -1.0], n=44, oos=0.30)
    cand["params"] = {"entry.min_score": 65}
    passes, gate, _why = reflect._gate_eval(inc, cand, k_probes=2)
    assert "dsr" in gate and gate["dsr_n_trials"] >= 2
    assert "ADVISORY" in gate["dsr_rol"] and "passes" in gate["dsr_rol"]
    src = inspect.getsource(reflect._gate_eval)
    assert src.index("passes = bool(magnitude_ok") < src.index("dsr = validation.deflated_sharpe"), \
        "DSR `passes` hesabından ÖNCE üretiliyor — advisory olduğu kod düzeninde görünmüyor"
    # Aynı girdi → aynı hüküm: DSR üretimi kapı kararına hiçbir yol açmıyor (determinizm çivisi)
    p2, g2, _ = reflect._gate_eval(inc, cand, k_probes=2)
    assert p2 is passes and g2["candidate_oos"] == gate["candidate_oos"]


def test_D2_defter_YALNIZ_resmi_degerlendirmede_yazar(sandbox_state):
    """`_gate_eval` arama döngüsünde binlerce kez çağrılıyor; her çağrıda yazan bir defter "kaç aday
    değerlendirildi" değil "kaç kez fonksiyon çağrıldı" ölçerdi (oos_erosion'ın birebir dersi)."""
    from meridian import reflect
    inc, cand = _wf([1.0, -1.0]), _wf([1.0, -1.0], n=44)
    cand["params"] = {"entry.min_score": 65}
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=False)
    assert store.read_jsonl(validation.LEDGER_FILE) == [], "arama yolunda deftere yazıldı"
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    rows = store.read_jsonl(validation.LEDGER_FILE)
    assert len(rows) == 1
    r = rows[0]
    assert r["etiket"] == "entry.min_score=65" and r["degisen_params"] == {"entry.min_score": 65}
    assert r["seri"] and isinstance(r["seri"][0], list) and len(r["seri"][0]) == 2
    assert ledgers.validate_row(validation.LEDGER_FILE, r) == []


def test_D2_defter_satiri_oos_components_TASIR_olcum_borcunu_kapatir(sandbox_state):
    """BU SATIR BİR ÖLÇÜM BORCUNU KAPATIR: bileşik skorun hangi TERİMİNİN bir adayı reddettiği
    bugüne kadar hiçbir kayıtta yoktu (S1/S2 ve G3a ölçümleri yalnız `oos_score` sakladı) — o
    yüzden o vakaların terim kırılımı yeniden koşmadan çıkarılamıyor. Artık her resmî
    değerlendirmede duruyor."""
    from meridian import reflect
    inc, cand = _wf([1.0, -1.0]), _wf([1.0, -1.0], n=44)
    cand["params"] = {"entry.min_score": 65}
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    r = store.read_jsonl(validation.LEDGER_FILE)[0]
    assert set(r["oos_components"]) == {"ret", "dd", "sharpe"}
    assert "n" in r["oos_ozet"] and "sharpe" in r["oos_ozet"]


# =================================================================================================
# E) SKOR AYRIŞTIRMASI — "ÖLÇÜNÜN ÖLÇÜMÜ"
# =================================================================================================
def test_E_segment_score_docstringi_FORMULU_duz_yaziyla_tasir():
    """Formül yalnız `score.score_detail`in içindeydi ve kapının okuduğu sayı oradan geliyordu;
    "bu skor neyi ödüllendiriyor?" sorusunun cevabı hiçbir yerde YAZILI DEĞİLDİ. Bir sonraki tur
    "büyüklük yasası revizyonu gerekir mi?" kararını verecek ve o karar sözlü bir açıklamaya
    dayanamaz."""
    d = backtest.segment_score.__doc__ or ""
    for parca in ("0,5 · ret_c", "0,3 · dd_c", "0,2 · sharpe_c",
                  "target_return_30d", "max_drawdown", "min_sharpe"):
        assert parca in d, f"formülün '{parca}' parçası docstring'de yok"
    # NOMİNAL ≠ GERÇEK ağırlık: ret_c yarısını taşır ama aralığı ~1/20'ye sıkışmıştır
    assert "NOMİNAL" in d and "1/20" in d
    # ROADMAP §5.1 kararına referans: bu bir HATA raporu değil ÖLÇÜM
    assert "büyüklük yasası revizyonu" in d


def test_E_agirliklar_docstring_ile_KODUN_ayni_seyi_soylemesi(sandbox_state):
    """Docstring'deki formül koddan sürüklenirse rapor yanlış bir zemine oturur. Ağırlıklar
    ÖLÇÜLEREK doğrulanır: bileşenlerden yeniden kurulan skor, fonksiyonun döndürdüğüne eşit."""
    goal = config.goal()
    trades = _kazanan_defter(40)
    d = score_mod.score_detail(trades, goal, span_days=365.0)
    c = d["components"]
    yeniden = max(-1.0, min(1.0, 0.5 * c["ret"] + 0.3 * c["dd"] + 0.2 * c["sharpe"]))
    assert abs(yeniden - d["score"]) < 5e-3, f"ağırlıklar sürüklendi: {yeniden} vs {d['score']}"


def test_E_para_terimi_KENDI_ARALIGININ_kucuk_bir_kismina_sikismis(sandbox_state):
    """RAPORUN SAYISAL ÇİVİSİ. `ret_c = kıs(gerçekleşen_30g / 0,07)` ve `gerçekleşen_30g` çok yıllık
    bir toplam getirinin 30 GÜNE indirgenmiş hâlidir — yani kâr terimi yapısal olarak sıfıra yakın
    bir bantta yaşar; `dd_c` ise 1 − düşüş/0,08 ile doğal olarak 0,2-0,4 bandındadır. Sonuç: nominal
    0,5 ağırlıklı "para kazandık mı?" terimi, skorun HAREKETİNDE küçük bir paya sahiptir."""
    goal = config.goal()
    trades = _kazanan_defter(60)
    d = score_mod.score_detail(trades, goal, span_days=900.0)      # ~2,5 yıllık pencere
    c = d["components"]
    assert abs(0.5 * c["ret"]) < abs(0.3 * c["dd"]), \
        f"para teriminin katkısı düşüş teriminden büyük çıktı: {c}"
    assert abs(c["ret"]) < 0.2, f"ret_c beklenenden geniş bir bantta: {c['ret']}"


def test_E_frekans_iki_terimde_TERS_yonde_calisir(sandbox_state):
    """İkinci yapısal not: n büyürse `sharpe_c` √(işlem/yıl) üzerinden BÜYÜR ama `ret_c` yalnız
    Σpnl arttıysa büyür. Ortalama R'si düşüp işlem sayısı artan bir aday (S2 vakası: n 98→106)
    Sharpe'tan kazanıp getiriden kaybeder — "daha çok işlem = daha çok kanıt" sezgisi bu skorda
    OTOMATİK ÖDÜL DEĞİLDİR."""
    goal = config.goal()
    az = [_islem(i, 1.0, 300.0) for i in range(40)]
    # AYNI Σpnl, DAHA ÇOK işlem (her işlem yarı büyüklükte) → ret_c aynı, sharpe_c √2 kat büyür
    cok = [_islem(i, 0.5, 150.0) for i in range(80)]
    d_az = score_mod.score_detail(az, goal, span_days=900.0)
    d_cok = score_mod.score_detail(cok, goal, span_days=900.0)
    assert abs(d_az["components"]["ret"] - d_cok["components"]["ret"]) < 1e-9, "Σpnl eşit değil"
    assert d_cok["components"]["sharpe"] > d_az["components"]["sharpe"], \
        "frekans Sharpe terimini büyütmüyor — √(işlem/yıl) çarpanı kaybolmuş"


# =================================================================================================
# YASA 6) HER YENİ ALANIN DIŞ TÜKETİCİSİ BU TURDA BAĞLANDI
# =================================================================================================
@pytest.mark.parametrize("alan", [
    "result_verdict", "portfolio_heat", "validation_trio",     # /api/diagnostics alanları
    "dolar_beklenti", "profit_factor", "maks_dusus", "net_pnl",  # SONUÇ hükmünün ölçütleri
    "kuyruk", "cvar5_r", "gunluk_m2m_dd",                      # 5. ölçütün alanları
    "isi_pct", "ilk_stop_isi_pct", "acik_risk_dolar",          # ısı alanları
    "dsr_canli", "psr_sifir", "n_trials", "pbo",               # doğrulama alanları
])
def test_YASA6_pano_yeni_alanlari_gercekten_okuyor(alan):
    """Üretilen alanın DIŞ tüketicisi olmalı. "Panoda gösteriliyor" gerekçesi, app.js taranarak
    KANITLANABİLİR olmadıkça gerekçe değildir."""
    assert codelaw.dashboard_mentions(alan), f"pano '{alan}' alanını hiç okumuyor (YASA 6)"


@pytest.fixture
def client(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    return TestClient(api.app)


def test_YASA6_diagnostics_ucu_uc_yeni_yuku_de_TASIR(client):
    d = client.get("/api/diagnostics")
    assert d.status_code == 200
    ml = d.json()["mlops"]
    rv = ml["result_verdict"]
    assert set(rv["criteria"]) == {"dolar_beklenti", "profit_factor", "maks_dusus", "net_pnl"}
    assert rv["verdict"].startswith("SONUÇ:")
    assert ml["edge_verdict"]["criteria"]["kuyruk"] is not None
    assert "isi_pct" in ml["portfolio_heat"]
    vt = ml["validation_trio"]
    assert "dsr_canli" in vt and "pbo" in vt and "n_trials" in vt
    assert "ADVISORY" in vt["rol"]


def test_YASA6_bos_state_500_URETMEZ(client, sandbox_state):
    """Boş bir depoda hüküm üretmeyi DENEYEN her yeni yol bir 500 adayıdır (numpy tipleri,
    sıfıra bölme, None aritmetiği). Boş depoda uç 200 dönmek ZORUNDA."""
    d = client.get("/api/diagnostics")
    assert d.status_code == 200
    json.dumps(d.json())          # JSON-serileştirilebilirlik (numpy.bool_ dersi)
