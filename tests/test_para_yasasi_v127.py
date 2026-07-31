"""test_para_yasasi_v127.py — BÜYÜKLÜK YASASI "PARA-v3" (2026-07-30).

Bu tur bir ANAYASA DEĞİŞİKLİĞİDİR: kapının karar değişkeni değişti. Yasa metni:

    ESKİ:  ΔS = kıs(0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c) farkı   [30-güne indirgemeli, aylık %7]
    YENİ:  ΔS = ret_c_v3 farkı = kıs(pencere_getirisi / ((1+%25)^(span/365) − 1)) farkı

Gerekçe ÖLÇÜLDÜ (3a E raporu + 3b gölge ölçümü): eski ΔS varyansının %82'si düşüş, %17,7'si
Sharpe, %0,3'ü paraydı — ve düşüş/Sharpe HEM skorda HEM ayrı sert vetolarda sayılıyordu (ÇİFT
SAYIM). Yeni yasada skorda yalnız para var; düşüş **güçlenerek** sert vetoya taşındı.

BU DOSYANIN ÇİVİLERİ — yeni yasanın kendi bekçileri:
  ① TEK TERİM: karar değişkeni YALNIZ paradan türer (dd/Sharpe ΔS'e giremez, varyans payı %100).
  ② DÜŞÜŞ VETOSU TEK YÖNLÜ: kötüleşme RET eder; iyileşme HİÇBİR puan kazandırmaz.
  ③ ESKİ YASA GÖLGEDE: her değerlendirmede ölçülür, kayda geçer, karara GİRMEZ + damga basılır.
  ④ MARJ ÇEVRİMİ: 0,02 (bileşik) → 0,004 (para) ve çevrim σ-EŞDEĞERLİĞİYLE türetilmiş.
  ⑤ SÜREKLİLİK: `score_detail` bileşiği RAPOR metriği olarak DEĞİŞMEDİ (karne/tarih kırılmadı).
  ⑥ ÖLÇEK KARIŞIMI YASAĞI: para öngörüsü ÷ bileşik gerçekleşme oranı meta-kalibrasyona GİRMEZ.

HİÇBİR TEST CANLI STATE'E YAZMAZ (canlı worker koşuyor): yazan yollar `sandbox_state` ile izole,
kalanlar salt-okuma.
"""
from __future__ import annotations

import datetime as dt
import inspect
import json

from meridian import (analytics, codelaw, config, oos_erosion, prescreen, probgate, reflect,
                      score as score_mod, shadowlaw, store)
from tests import wf_fixtures as wf


def _goal():
    return config.goal()


SPAN_S = (dt.date.fromisoformat(wf.S_END) - dt.date.fromisoformat(wf.S_LO)).days


def _yerlestir(ts, desen, bump=0.0):
    """AYNI zaman damgaları, AYNI kâr çokluğu (+ sabit bump) — yalnız SIRA değişir.

    NEDEN BÖYLE: düşüş vetosunu izole sınamak için "para AYNI / düşüş FARKLI" bir çift gerekiyor.
    Kârları zaman içinde yeniden dizmek tam bunu verir: Σpnl (dolayısıyla `ret_c_v3`) birebir
    korunur, sermaye eğrisinin şekli — yani maks düşüş — değişir. Rastgele fikstür gürültüsüne
    bırakılsa iki etki birbirine karışırdı ve test neyi ölçtüğünü söyleyemezdi.

    `r_multiple` +0,002 artırılır: fold çoğunluğu kazanılsın ve ret sebebi YALNIZ düşüş vetosu
    olsun (aksi hâlde `majority` False olur ve veto hiç sınanmaz). `r_multiple` para skoruna
    GİRMEZ (o `pnl_dollars`tan gelir), yani izolasyon bozulmaz."""
    ps = [float(t["pnl_dollars"]) + bump for t in ts]
    kaz = sorted([p for p in ps if p > 0], reverse=True)
    kay = sorted([p for p in ps if p <= 0])
    if desen == "derin":          # önce TÜM kayıplar → erken çukur, uzun toparlanma
        yeni = kay + kaz
    else:                         # DÖNÜŞÜMLÜ → dar bantta salınım, sığ düşüş
        yeni = []
        while kaz or kay:
            if kaz:
                yeni.append(kaz.pop(0))
            if kay:
                yeni.append(kay.pop(0))
    sirali = sorted(ts, key=lambda t: str(t["ts_close"]))
    return [{**t, "pnl_dollars": round(p, 4),
             "r_multiple": round(float(t["r_multiple"]) + 0.002, 5)} for t, p in zip(sirali, yeni)]


# =================================================================================================
# ① TEK TERİM — karar değişkeni YALNIZ paradan türer
# =================================================================================================
def test_karar_degiskeni_YALNIZ_paradan_turer_dd_ve_sharpe_giremez():
    """ÇİVİ: `ret_c_v3` yalnız (toplam getiri, span) fonksiyonudur. Düşüşü ya da Sharpe'ı değiştiren
    ama kârı AYNI bırakan iki defter, kapı için AYNI skoru vermek ZORUNDADIR — çift-sayımın
    bittiğinin doğrudan davranış kanıtı."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    its = inc["_trades_search"]
    derin = _yerlestir(its, "derin")
    sig = _yerlestir(its, "sig")
    dd_derin = score_mod.max_drawdown(score_mod.equity_curve(derin))
    dd_sig = score_mod.max_drawdown(score_mod.equity_curve(sig))
    assert dd_derin > dd_sig * 2, "fikstür düşüşü ayırmıyor — test neyi ölçtüğünü söyleyemez"
    # ESKİ yasa bu ikisini AYRI skorlardı (dd_c varyansın %82'siydi)...
    g = {**_goal(), "min_sample": 1}
    e_derin = score_mod.score_detail(derin, g, span_days=SPAN_S)["score"]
    e_sig = score_mod.score_detail(sig, g, span_days=SPAN_S)["score"]
    assert e_derin != e_sig, "eski yasa düşüşü görmüyordu — taban varsayımı yanlış"
    # ...YENİ yasa ikisini AYNI görür: para aynı, karar aynı.
    p_derin = shadowlaw.money_score(derin, g, span_days=SPAN_S)
    p_sig = shadowlaw.money_score(sig, g, span_days=SPAN_S)
    assert p_derin == p_sig, f"karar skoru düşüşten etkileniyor ({p_derin} vs {p_sig})"

    # ARA BULGU (fikstürün kendisi hakkında, çivilenmeye değer): işlemleri zaman içinde yeniden
    # dizmek `pnl_dollars` ÇOKLUĞUNU değiştirmediği için Sharpe'ı da DEĞİŞTİRMEZ (Sharpe
    # ort/std'den gelir, sıradan değil). Yani bu fikstür SAF bir düşüş manipülasyonudur — düşüş
    # vetosu testlerinin izolasyonu tam bu yüzden geçerli.
    assert score_mod.score_detail(derin, g, span_days=SPAN_S)["sharpe"] == \
        score_mod.score_detail(sig, g, span_days=SPAN_S)["sharpe"]

    # SHARPE DE KARARA GİREMEZ — ayrı bir fikstürle: sapmaları küçültmek toplamı KORUR (Σ aynı) ama
    # std'yi düşürür, yani Sharpe'ı belirgin biçimde YÜKSELTİR. "Sharpe hiçbir yerde AYRICA
    # sayılmaz" beyanının davranış kanıtı: kapı bu adayı incumbent'la AYNI görmek zorundadır.
    ort = sum(float(t["pnl_dollars"]) for t in its) / len(its)
    duzgun = [{**t, "pnl_dollars": round(ort + 0.3 * (float(t["pnl_dollars"]) - ort), 4)}
              for t in its]
    d_ham = score_mod.score_detail(its, g, span_days=SPAN_S)
    d_duz = score_mod.score_detail(duzgun, g, span_days=SPAN_S)
    assert abs(d_ham["total_return"] - d_duz["total_return"]) < 1e-9, "toplam kâr korunmadı"
    assert d_duz["sharpe_measurable"] and d_duz["sharpe"] > d_ham["sharpe"] * 2, \
        "fikstür Sharpe'ı ayırmıyor"
    assert shadowlaw.money_score(duzgun, g, span_days=SPAN_S) == \
        shadowlaw.money_score(its, g, span_days=SPAN_S), "karar skoru Sharpe'tan etkileniyor"


def test_probgate_ADIM_ADIM_yalnız_para_terimini_kullanir():
    """Kaynak düzeyi çivisi: `_score_pair`in KARAR değeri `ret_c_v3`ten gelir ve bileşiği (dd/sharpe
    ağırlıkları) KULLANMAZ. Davranış testi bunu zaten gösteriyor; bu çivi, birinin ileride
    "gölge" tarafı yanlışlıkla karar tarafına bağlamasını yakalar."""
    src = inspect.getsource(probgate.PairedProbabilisticGate._score_pair)
    assert "ret_c_v3" in src, "karar terimi para değil"
    # eski bileşik ağırlıklar karar hesabına GERİ GELMESİN
    for yasak in ("V2_WEIGHTS", "OLD_LAW_WEIGHTS", "w_d *", "w_s *", 'components"]["dd"'):
        assert yasak not in src, f"eski yasanın bacağı karar hesabına sızmış: {yasak}"
    # ...ama eski skor GÖLGE olarak dönmeye devam ediyor (ters gölgeleme)
    assert "s_eski" in src and "return shadowlaw.ret_c_v3" in src


def test_varyans_atamasi_PARA_payi_YUZDE_YUZ():
    """Yasanın kendi çivisi — ÖLÇÜLÜR, varsayılmaz. Skora bir gün ikinci bir bacak sızarsa pay
    1,0'ın altına düşer ve bu test kırılır."""
    r = shadowlaw.variance_attribution(analytics._trades(), _goal(), n_boot=300)
    assert r is not None, "canlı defterde ölçülemedi"
    assert r["v3_paylar"] == {"para": 1.0, "dusus": 0.0, "sharpe": 0.0}
    assert r["para_payi_tek_terim"] is True
    # ve TABAN doğrulanır: eski yasanın payları E raporunu replike etmeli
    assert r["eski_paylar"]["para"] < 0.02 and r["eski_paylar"]["dusus"] > 0.70


def test_ret_c_v3_30_GUNE_INDIRGEME_yapmaz_para_terimi_CANLANDI():
    """3a E raporunun teşhisi: 30-güne indirgeme getiri oynaklığının ~%98'ini söndürüyordu. ÇİVİ:
    yeni terim ESKİSİNDEN belirgin biçimde DAHA OYNAK olmalı (yoksa çarpıtma kalkmamıştır)."""
    m = shadowlaw.MEASURED_V3
    assert m["sd_ret_c_v3"] > m["sd_ret_c_eski"] * 2, "para terimi hâlâ sönümlü"
    assert m["ret_scale_k"] > 2.0
    # docstring'de 30-güne indirgemenin KALKTIĞI yazılı olmak zorunda (yasa metni okunabilir olsun)
    assert "30-GÜNE İNDİRGEME YOK" in shadowlaw.__doc__
    assert shadowlaw.YASA_METNI and "ret_c_v3" in shadowlaw.YASA_METNI


# =================================================================================================
# ② DÜŞÜŞ VETOSU — kötüleşme RET, iyileşme SIFIR PUAN
# =================================================================================================
def test_dusus_vetosu_ISIRIR_para_DAHA_IYI_olsa_bile(sandbox_state):
    """ÇİVİ (vetonun dişleri): adayın parası incumbent'tan BELİRGİN biçimde iyi olsa DA, maks düşüşü
    marjdan fazla kötüleşiyorsa RET. Eski yasada bu bir PAZARLIKtı (kâr artışı, dd_c kaybını 0,3
    ağırlıkla telafi edebiliyordu); yeni yasada PAZARLIK YOK."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    its, itc = inc["_trades_search"], inc["_trades_confirm"]
    # bump=80 ÖLÇÜLEREK seçildi: para farkı P(ΔS>0)=0,92 verecek kadar büyük (yani büyüklük
    # kapısı GEÇİYOR ve ret sebebi kesinlikle veto), düşüş ise 0,0660 — marjın (0,04) net üstünde.
    # Daha büyük bump'lar düşüşü SEYRELTİR (bump=200'de dd 0,0422 < eşik) ve testi anlamsızlaştırır.
    cand = wf.wf_from_trades(_yerlestir(its, "derin", bump=80.0)
                             + _yerlestir(itc, "derin", bump=80.0))
    cand["oos_score"] = 0.20

    passes, gate, why = reflect._gate_eval(inc, cand)

    # (a) PARA gerçekten daha iyi — yani ret sebebi büyüklük DEĞİL
    assert gate["candidate_para"] > gate["incumbent_para"] + reflect.MONEY_GATE_MARGIN
    assert gate["search_p"] >= gate["search_p_required"], "büyüklük geçmedi — veto izole sınanamaz"
    # (b) düşüş marjdan fazla kötüleşti
    assert gate["candidate_dd"] > gate["incumbent_dd"] + reflect.DD_VETO_MARGIN
    assert gate["dd_ok"] is False and gate["dd_durum"] == "veto"
    # (c) HÜKÜM: RET, ve sebebi ADIYLA yazılı
    assert passes is False
    assert "düşüş vetosu" in why, f"ret sebebi düşüş vetosu olarak yazılmamış: {why}"


def test_dusus_vetosu_TEK_YONLU_iyilesme_puan_KAZANDIRMAZ(sandbox_state):
    """ÇİVİ (tek yönlülük): düşüşü BÜYÜK ölçüde iyileştiren ama kârı AYNI olan bir aday, kapıdan
    HİÇBİR puan kazanmaz ve geçmez.

    NEDEN ÖNEMLİ: iyileşme ödüllendirilse düşüş karar değişkenine geri sızardı ve çift-sayım arka
    kapıdan dönerdi — skorun varyansı yine düşüşe kayardı. Veto YALNIZ kötüleşmeyi cezalandırır;
    iyileşme raporda görünür (`candidate_dd`, 3A kuyruk ölçütü) ama KARARDA görünmez."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    its, itc = inc["_trades_search"], inc["_trades_confirm"]
    # bump=0 → para BİREBİR aynı; "sig" deseni → düşüş belirgin biçimde DAHA İYİ
    cand = wf.wf_from_trades(_yerlestir(its, "sig") + _yerlestir(itc, "sig"))
    cand["oos_score"] = 0.10

    passes, gate, why = reflect._gate_eval(inc, cand)

    # (a) düşüş GERÇEKTEN iyileşti (veto tetiklenmedi — tek yönlü)
    assert gate["candidate_dd"] < gate["incumbent_dd"], "fikstür düşüşü iyileştirmiyor"
    assert gate["dd_ok"] is True and gate["dd_durum"] == "gecti"
    # (b) para AYNI → karar değişkeni sistematik bir üstünlük GÖRMÜYOR
    assert abs(gate["candidate_para"] - gate["incumbent_para"]) < 1e-9, "para izolasyonu bozuldu"
    # (c) HÜKÜM: geçmez. İyileşme puana ÇEVRİLMEDİ.
    assert gate["search_p"] < gate["search_p_required"]
    assert passes is False
    assert "P(ΔS>0)" in why, f"ret büyüklükten gelmiyor: {why}"


def test_dusus_vetosu_UYGULANAMAZSA_veto_sebebi_OLAMAZ():
    """`fold_total == 0` ile aynı ilke: dilim yoksa düşüş ÖLÇÜLEMEZ ve ölçülemeyen bir kontrol
    veto sebebi olamaz. Sessizce "geçti" de demez — kayıtta `olculemedi` yazar."""
    src = inspect.getsource(reflect._gate_eval)
    assert 'dd_ok, dd_durum = True, "olculemedi"' in src, "uygulanamayan kontrol muhafazakâr değil"
    assert "dd_ok" in src.split("passes = bool(")[1].split(")")[0], "veto hükme bağlanmamış"


def test_dusus_vetosu_MARJI_kendi_gurultusunun_DISINDA():
    """`TAIL_SIMS` dersinin genellemesi: bir vetonun karar sınırı, vetoladığı büyüklüğün ölçüm
    gürültüsünün İÇİNDE olamaz — yoksa veto gürültüyle tetiklenir ve tekrarlanabilir olması onu
    DOĞRU yapmaz. İki bağımsız türetim de aynı sayıya çıkıyor (docstring'de yazılı)."""
    m = shadowlaw.MEASURED_V3
    assert shadowlaw.DD_VETO_MARGIN > m["sd_dusus"], "veto sınırı kendi gürültüsünün içinde"
    # ikinci türetim: düşüş bütçesinin YARISI
    assert abs(shadowlaw.DD_VETO_MARGIN - 0.5 * float(_goal()["max_drawdown"])) < 1e-9
    # gerekçe kodda YAZILI (sabit gerekçesiz duramaz)
    src = inspect.getsource(shadowlaw)
    assert "BÜTÇENİN YARISI" in src and "KENDİ GÜRÜLTÜSÜNÜN DIŞINDA" in src


# =================================================================================================
# ③ ESKİ YASA GÖLGEDE + DAMGA
# =================================================================================================
def test_kapi_kaydi_ESKI_YASA_golgesini_ve_DAMGAyi_tasir(sandbox_state):
    """Süreklilik: yeni yasa altında ölçülen her adayda eski yasanın hükmü de ölçülmüş olarak
    durur, böylece iki yasa AYNI adaylar üzerinde kıyaslanabilir kalır."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.60), (30, 0.60), (30, 0.60)))
    _p, gate, _w = reflect._gate_eval(inc, cand)

    sh = gate["search_eski_yasa"]
    assert isinstance(sh, dict) and sh["decides"] is False and sh["law"] == "eski_yasa"
    assert sh["p"] is not None and sh["n_valid"] > 0
    assert "would_pass" in sh and "agrees_with_law" in sh
    # DAMGA + geçiş tarihi
    assert gate["yasa_surumu"] == "para_v3" == shadowlaw.YASA_SURUMU
    assert gate["yasa_gecis_tarihi"] == "2026-07-30"
    assert gate["search_yasa_surumu"] == "para_v3"
    assert "ret_c_v3" in gate["yasa_metni"]
    # KARAR skorları PARA ölçeğinde kayda girer (yasanın gerçekten okuduğu sayılar)
    assert gate["incumbent_para"] is not None and gate["candidate_para"] is not None
    # ...ve bileşik RAPOR metriği AYNI kayıtta AYRI satır olarak durur (süreklilik)
    assert gate["incumbent_oos"] == 0.10 and gate["candidate_oos"] == 0.20
    json.dumps(gate, ensure_ascii=False)      # kapı kaydı JSON-güvenli kalmalı (/api 500 dersi)


def test_LEGACY_yol_damgasini_ESKI_yasa_olarak_atar():
    """Dilimsiz sözlük (fikstür/sandbox) legacy marj yasasına düşer ve orada PARA ölçeği
    HESAPLANAMAZ (dilim yok → span yok → payda yok). Bu yüzden o yol `GATE_MARGIN`ı (0,02) bileşik
    ölçekte kullanmaya devam eder — ve damga bunu AÇIKÇA söyler ki kayıt yanlış okunmasın."""
    inc = {"oos_score": 0.10, "oos_folds": [], "holdout_score": None, "params": {}}
    cand = {"oos_score": 0.20, "oos_folds": [], "holdout_score": None, "params": {}}
    passes, gate, _w = reflect._gate_eval(inc, cand)
    assert gate["gate_law"] == "legacy_margin"
    assert gate["yasa_surumu"] == "eski_bilesik_marj", "legacy yol para-v3 damgası taşıyor"
    assert gate["incumbent_para"] is None and gate["candidate_para"] is None
    assert gate["dd_durum"] == "olculemedi"
    assert passes is True      # 0.20 > 0.10 + 0.02 — eski yasa davranışı AYNEN korunur
    assert reflect.GATE_MARGIN == 0.02, "eski yasanın marjı değişmiş"


def test_golge_hukum_passes_semantigine_SIZAMAZ(sandbox_state):
    """Kod düzeni çivisi: gölge alanı üretilir ama `passes` yalnız para p'sinden gelir."""
    src = inspect.getsource(reflect._gate_eval)
    i_passes = src.index("passes = bool(magnitude_ok")
    # `passes` satırı, eski-yasa alanının OKUNDUĞU hiçbir yere bağlı olmamalı
    assert "eski_yasa" not in src[:i_passes], "eski yasa hükmü passes'ten ÖNCE okunuyor"
    kosul = src[i_passes:src.index("\n", i_passes)]
    for yasak in ("eski", "shadow", "dsr"):
        assert yasak not in kosul, f"passes koşuluna yetkisiz terim girmiş: {yasak}"
    # ve DSR hâlâ passes'ten SONRA (Hafta 3a'nın çivisi korunur)
    assert i_passes < src.index("dsr = validation.deflated_sharpe")


# =================================================================================================
# ④ MARJ ÇEVRİMİ — 0,02 (bileşik) → 0,004 (para)
# =================================================================================================
def test_GATE_MARGIN_para_olcegine_SIGMA_ESDEGERLIGIYLE_cevrildi():
    """ÇİVİ: çevrim uydurma bir sayı değil, ÖLÇÜLMÜŞ bir orandır — marj, karar değişkeninin KENDİ
    gürültüsünde aynı yerde durur. İki ölçekte de aynı σ konumu."""
    m = shadowlaw.MEASURED_V3
    assert shadowlaw.MARGIN_MONEY_SCALE == m["margin_scale"]
    # çarpan GERÇEKTEN σ oranı mı (ölçüm kaydıyla tutarlı mı)
    beklenen = m["sd_ret_c_v3"] / m["sd_score_eski"]
    assert abs(shadowlaw.MARGIN_MONEY_SCALE - beklenen) < 5e-4, "çarpan ölçümle tutarsız"
    # sabit, çarpanla türetilmiş olmak zorunda (0,02 × 0,1908 = 0,00382 → 0,004)
    assert abs(shadowlaw.MONEY_GATE_MARGIN - 0.02 * shadowlaw.MARGIN_MONEY_SCALE) < 5e-4
    # σ KONUMU KORUNDU: eski marj kaç σ ise yenisi de o kadar σ
    sigma_eski = 0.02 / m["sd_score_eski"]
    sigma_yeni = shadowlaw.MONEY_GATE_MARGIN / m["sd_ret_c_v3"]
    assert abs(sigma_eski - sigma_yeni) < 0.02, f"marjın sertliği kaydı: {sigma_eski} vs {sigma_yeni}"
    # REDDEDİLEN İKİNCİ ÇEVRİM kodda gerekçesiyle YAZILI (seçim beyan edilmeden yapılmaz)
    src = inspect.getsource(shadowlaw)
    assert "PARA-BACAĞI OKUMASI" in src and "REDDEDİLDİ" in src


def test_asinma_marji_da_PARA_olceginde_uygulanir(sandbox_state):
    """Aşınma cezası bileşik ölçekte kalsaydı, skordan ÇIKARDIĞIMIZ bacaklar arka kapıdan karara
    geri sızardı: aşınmış bir pencerede aday, kârı DEĞİL düşüşünü iyileştirerek cezayı geçebilirdi."""
    src = inspect.getsource(reflect._gate_eval)
    assert "erosion_margin_para" in src
    assert "shadowlaw.MARGIN_MONEY_SCALE" in src, "aşınma marjı çevrilmemiş"
    # ceza yalnız eşik aşılınca biner → normal hâlde para marjı 0 ve satır NO-OP
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.60), (30, 0.60), (30, 0.60)))
    _p, gate, _w = reflect._gate_eval(inc, cand)
    assert gate["erosion"]["extra_margin"] == 0.0
    assert gate["erosion_margin_para"] == 0.0
    assert gate["money_gate_margin"] == shadowlaw.MONEY_GATE_MARGIN == 0.004


# =================================================================================================
# ⑤ SÜREKLİLİK — bileşik skor RAPOR metriği olarak DEĞİŞMEDİ
# =================================================================================================
def test_score_detail_bilesigi_AYNEN_yerinde_karne_kirilmadi():
    """Yasa değişti ama `score_detail` DEĞİŞMEDİ: karne, tarih ve `oos_score` serisi kırılmasın.
    Bu, turun en kolay ihlal edilecek sözüydü — çivilenmesi şart."""
    tr = wf.trades(40, 5, wf.S_LO, wf.S_END, 0.4)
    d = score_mod.score_detail(tr, _goal(), span_days=SPAN_S)
    c = d["components"]
    assert set(c) == {"ret", "dd", "sharpe"}, "rapor metriğinin bileşenleri değişmiş"
    yeniden = max(-1.0, min(1.0, 0.5 * c["ret"] + 0.3 * c["dd"] + 0.2 * c["sharpe"]))
    assert abs(yeniden - d["score"]) < 5e-3, "bileşik RAPOR metriği sürüklendi"
    # hedefler hâlâ goal'dan (eski ölçek raporda yaşamaya devam eder)
    assert d["targets"]["target_return_30d"] == float(_goal()["target_return_30d"])


def test_defter_satiri_YASA_SURUMUNU_tasir(sandbox_state):
    """PBO/DSR analizleri iki farklı karar değişkenini tek popülasyon sanmasın: doğrulama defteri
    satırı hangi yasa altında hüküm aldığını yazar."""
    inc = wf.wf_from_scores(0.10, folds=((30, 0.30), (30, 0.30), (30, 0.30)))
    cand = wf.wf_from_scores(0.20, folds=((30, 0.60), (30, 0.60), (30, 0.60)))
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    from meridian import ledgers, validation
    rows = store.read_jsonl(validation.LEDGER_FILE)
    assert rows, "resmî değerlendirme deftere yazmadı"
    r = rows[-1]
    assert r["yasa_surumu"] == "para_v3"
    assert "oos_para" in r and "dd_ok" in r and "candidate_dd" in r
    # sözleşme İHLAL EDİLMEDİ (yeni alanlar eklendi, gerekli alanlar yerinde)
    assert ledgers.validate_row(validation.LEDGER_FILE, r) == []


# =================================================================================================
# ⑥ ÖLÇEK KARIŞIMI YASAĞI — meta-kalibrasyon
# =================================================================================================
def test_meta_kalibrasyon_PARA_ongorusunu_BILESIK_gerceklesmeyle_BOLMEZ(sandbox_state, monkeypatch):
    """SESSİZ MİKTAR HATASI ÖNLENDİ. `predicted_delta` artık PARA, `realized_delta` hâlâ BİLEŞİK
    (rollback yolu). İkisini bölmek "gerçekleşme oranı" değil birim karışımıdır ve σ oranı ≈0,19
    olduğundan oran sistematik olarak ~5× ŞİŞERDİ → sahte "öngörüler fazlasıyla gerçekleşiyor"
    sinyali → kapı YANLIŞ yerde gevşerdi. Hiçbir test kırılmadan.

    ÇİVİ: para-v3 damgalı çiftler SAYILMAZ ve atlandıkları BEYAN edilir."""
    store.write_jsonl_replace = getattr(store, "write_jsonl_replace", None)
    satirlar = []
    for i in range(6):      # META_MIN_N=5'in ÜSTÜNDE — sayılsalardı extra_p oynardı
        satirlar.append({"id": f"H{i}", "predicted_delta": 0.10, "realized_delta": 0.005,
                         "backtest": {"confirm_yasa_surumu": "para_v3"}})
    for s in satirlar:
        store.append_jsonl("hypotheses.jsonl", s)
    out = probgate.refresh_meta_calibration()
    assert out["olcek_karisimi_atlanan"] == 6, "para öngörüleri bileşik gerçekleşmeyle bölünüyor"
    assert out["n_measured"] == 0 and out["extra_p"] == 0.0, "muhafazakâr davranış korunmadı"
    assert out["olcek_borcu"], "ölçüm borcu beyan edilmemiş"

    # GEÇİŞ ÖNCESİ çiftler (damgasız) SAYILMAYA DEVAM EDER — mekanizma tarihiyle çalışır
    for i in range(6):
        store.append_jsonl("hypotheses.jsonl", {"id": f"E{i}", "predicted_delta": 0.10,
                                               "realized_delta": 0.005, "backtest": {}})
    out2 = probgate.refresh_meta_calibration()
    assert out2["n_measured"] == 6 and out2["olcek_karisimi_atlanan"] == 6
    assert out2["extra_p"] > 0.0, "sistematik iyimserlik artık sıkılaştırmıyor"


# =================================================================================================
# YASA 6 — pano yeni yasayı GERÇEKTEN okuyor
# =================================================================================================
def test_YASA6_pano_yeni_yasa_alanlarini_okuyor():
    for alan in ("yasa_surumu", "para_payi_v3", "dd_veto_margin", "money_gate_margin",
                 "gecis_oncesi_kayit", "p_eski", "margin_scale"):
        assert codelaw.dashboard_mentions(alan), f"pano yeni yasa alanını okumuyor: {alan}"


def test_pano_satiri_GECIS_YAPILDI_der_ve_JSON_guvenli():
    """Operatör bu satıra bakıp hâlâ eski yasanın koştuğunu sanarsa, kapı kayıtlarındaki p'leri
    yanlış yasanın p'si olarak okur — satırın geçişi BEYAN etmesi zorunlu."""
    r = analytics.shadow_law_row()
    assert r["law_transition"] is True
    assert r["yasa_surumu"] == "para_v3" and r["gecis_tarihi"] == "2026-07-30"
    assert "PARA-v3" in r["aktif_yasa"] and "SKORDAN ÇIKTI" in r["aktif_yasa"]
    assert "ESKİ" in r["golge_yasa"]
    assert r["para_payi_v3"] == 1.0 and r["para_payi_eski"] < 0.02
    assert r["dd_veto_margin"] == shadowlaw.DD_VETO_MARGIN
    assert r["money_gate_margin"] == shadowlaw.MONEY_GATE_MARGIN
    # v2 rötuşunun ölçüm kaydı DURUYOR (v3'ün gerekçesi silinemez)
    assert r["v2_rotusu"]["hedef_tuttu"] is False and r["v2_rotusu"]["deneme_sayisi"] == 3
    json.dumps(r, ensure_ascii=False)


def test_eski_alan_adlari_panoda_KALMADI():
    """Pano artık OLMAYAN alanları okumamalı: `shadow_law_row` anahtarları yeniden adlandırıldı
    (`varyans_payi.v1/v2` → `.eski/.v3`, `son_kayit.p_v1/p_v2` → `.p_v3/.p_eski`, `agirliklar` ve
    `hedef_tuttu` kaldırıldı). Eski erişimler kalsa satır SESSİZCE boş/undefined çizerdi — hiçbir
    test kırılmadan, çünkü JSON-güvenlik testi yalnız serileştirmeye bakar.

    NOT: kontrol PROSE'a değil ALAN ERİŞİMİNE bakar. Blok yorumu geçmişi ("3b'de v2 olsaydı
    diyordu") bilerek anlatıyor ve anlatması gerekiyor — silinmesi gereken şey KOD, tarih değil."""
    js = (__import__("pathlib").Path("meridian/web/app.js")).read_text()
    i = js.index("BÜYÜKLÜK YASASI SATIRI")
    blok = js[i:i + 5000]
    for olu in ("shadow_v2", "s.agirliklar", "son.p_v1", "son.p_v2", "son.v1_gecti",
                "son.v2_gecerdi", "s.hedef_tuttu", ".v1 || {}", ".v2 || {}"):
        assert olu not in blok, f"pano artık var olmayan alanı okuyor: {olu}"
    # ...ve yeni alanları GERÇEKTEN okuyor
    for canli in ("s.yasa_surumu", "s.para_payi_v3", "s.dd_veto_margin", "son.p_eski",
                  "son.v3_gecti", "s.gecis_oncesi_kayit"):
        assert canli in blok, f"pano yeni alanı okumuyor: {canli}"
    assert "GEÇİŞ YAPILDI" in blok and "eski hüküm" in blok


def test_on_eleme_harness_i_YASANIN_gercek_sayilarini_kaydeder():
    """`prescreen` ölçüm ARACIdır ve yasadan geri kalamaz. Bugüne dek satırı yalnız BİLEŞİK
    `oos_score` farkını (`delta`) yazıyordu; o sayı artık kapının KARAR değişkeni DEĞİL. Araç
    güncellenmeseydi kabul sınavı tablosu kurulamazdı: rapor "Δ −0,03 → geçmez" derdi ama hükmün
    PARA farkından mı, düşüş vetosundan mı, yoksa olasılıksal çıtadan mı geldiği OKUNAMAZDI.

    (Kaynak düzeyi çivi: bu alanlar bir walk-forward koşusu gerektirdiği için birim testinde
    davranışla sınanamaz — sınav koşusu dakikalar sürer. Alanların satıra YAZILDIĞI çivilenir.)"""
    src = inspect.getsource(prescreen)
    for alan in ('"yasa_surumu": gate.get("yasa_surumu")', '"para_delta"', '"p": gate.get("search_p")',
                 '"dd_ok": gate.get("dd_ok")', '"eski_yasa_p"', '"iki_yasa_ayni_hukum"'):
        assert alan in src, f"ön-eleme satırı yeni yasanın sayısını kaydetmiyor: {alan}"
    # bileşik `delta` KALDI (eski okuyucular kırılmasın) ama artık YANINDA para farkı var
    assert '"delta": delta' in src and '"para_delta"' in src


def test_oos_erosion_marji_ile_yeni_marj_ARASINDA_karisiklik_yok():
    """İki marj AYRI ölçektedir ve ikisi de kayıtta AYRI adla durur — biri diğerinin yerine
    okunamaz (kaydı sonradan okuyan 'GATE_MARGIN değişmiş' sanmasın)."""
    assert oos_erosion.EROSION_EXTRA_MARGIN == 0.01      # bileşik ölçek (rapor)
    assert shadowlaw.MONEY_GATE_MARGIN == 0.004          # para ölçeği (karar)
    assert reflect.GATE_MARGIN == 0.02                   # eski yasa / legacy yol
    assert reflect.MONEY_GATE_MARGIN is shadowlaw.MONEY_GATE_MARGIN
    assert reflect.DD_VETO_MARGIN is shadowlaw.DD_VETO_MARGIN
