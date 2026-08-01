"""WP-M KALAN BORÇLARI — üç kalem, tek tur (v146, 2026-08-01).

A) CANLI-BEKLENTİ TAVANI config'e bağlandı  — `config.live_expectancy_rule` +
   `analytics.live_expectancy_ceiling` + `result_verdict()["tavan_durumu"]` kolonu.
B) KIYAS-KİRLENMESİ STANDARDI               — `meridian/olcum_araclari.temiz_taban`.
C) 2C EMPİRİK-BAYES KÜÇÜLTME                — `component_ic` tablosunun paralel `eb` sütunu.

ÜÇÜNÜN ORTAK ÇİVİSİ: hiçbiri HÜKÜM VERMEZ. Bu dosyanın en önemli testleri "yeni alan doğru mu"
değil, "yeni alan mevcut hükümlere DOKUNMADI mı" sorusunu soranlardır — sessiz davranış değişikliği
bu depoda yasak.
"""
import copy
import json
import pathlib

import pytest

from meridian import analytics, component_ic, config
from meridian.olcum_araclari import temiz_taban

SRC = pathlib.Path(__file__).resolve().parent.parent / "meridian"


# =================================================================================================
# A) CANLI-BEKLENTİ TAVANI — KONFİGÜRASYON
# =================================================================================================
def test_A_varsayilanlar_KODDA_ve_kaynagi_adiyla_soyleniyor():
    """goal.yaml'da alan YOKKEN kural yine yürürlüktedir ve bunu SÖYLER.

    Sessiz bir varsayılan, okuyucuya "operatör böyle yazmış" izlenimi verirdi — `explore_rate`
    sınıfının tersi: orada dosyada yazan bir sayıyı kimse okumuyordu, burada kimsenin yazmadığı
    bir sayı yürürlükte ve kaynağı yazılı."""
    k = config.live_expectancy_rule({})
    assert k["cap_mult"] == 0.5 and k["suspend_ratio"] == 0.4
    assert k["kaynak"]["live_expectancy_cap_mult"] == "kod varsayilani"
    assert k["kaynak"]["live_suspend_ratio"] == "kod varsayilani"
    assert k["uyari"] is None
    assert k["varsayilanlar"] == {"live_expectancy_cap_mult": config.LIVE_EXPECTANCY_CAP_MULT,
                                  "live_suspend_ratio": config.LIVE_SUSPEND_RATIO}


def test_A_gercek_goal_yaml_ile_de_calisir(sandbox_state):
    """CANLI goal.yaml bu alanları TAŞIMIYOR (bilinçli — değişmez dosyaya bu turda dokunulmadı).
    Kural yine de okunabilmeli: goal_doc=None yolu goal()'u okur ve varsayılanlara düşer."""
    g = config.goal()
    assert "live_expectancy_cap_mult" not in g, "goal.yaml'a alan yazılmış — test varsayımı eskidi"
    k = config.live_expectancy_rule()
    assert (k["cap_mult"], k["suspend_ratio"]) == (0.5, 0.4)


def test_A_goal_yaml_kazanir():
    k = config.live_expectancy_rule({"live_expectancy_cap_mult": 0.6, "live_suspend_ratio": 0.35})
    assert k["cap_mult"] == 0.6 and k["suspend_ratio"] == 0.35
    assert set(k["kaynak"].values()) == {"goal.yaml"}


@pytest.mark.parametrize("bozuk", [
    {"live_expectancy_cap_mult": 0.0},          # 0 bir tavan değil
    {"live_expectancy_cap_mult": -0.5},
    {"live_expectancy_cap_mult": 1.5},          # canlıdan backtest'in ÜSTÜNÜ beklemek
    {"live_expectancy_cap_mult": "yarim"},
    {"live_suspend_ratio": "x"},
    {"live_suspend_ratio": 0.0},
    {"live_suspend_ratio": 2.0},
])
def test_A_gecersiz_deger_SESSIZCE_kabul_edilmez(bozuk, sandbox_state):
    k = config.live_expectancy_rule(dict(bozuk))
    assert k["uyari"] and "geçersiz" in k["uyari"]
    assert (k["cap_mult"], k["suspend_ratio"]) == (0.5, 0.4), "geçersiz değer varsayılana düşmedi"


def test_A_tutarsiz_kural_IKI_alani_da_geri_alir(sandbox_state):
    """suspend_ratio > cap_mult tutarsızdır: tavanın altındaki her NORMAL sonuç aynı anda
    süspansiyon adayı olurdu. Tek alanı düzeltmek keyfî olurdu — ikisi de varsayılana döner."""
    k = config.live_expectancy_rule({"live_expectancy_cap_mult": 0.3, "live_suspend_ratio": 0.9})
    assert (k["cap_mult"], k["suspend_ratio"]) == (0.5, 0.4)
    assert "tutarsız kural" in (k["uyari"] or "")


# =================================================================================================
# A) CANLI-BEKLENTİ TAVANI — ÖLÇÜM (sentetik state)
# =================================================================================================
def _kur(sandbox_state, *, surum=7, backtest_avg_r=0.20, canli_r=0.09, n=40,
         kaynak="live_paper", tohum_r=None):
    """Sentetik karne + defter. `tohum_r` verilirse aynı sayıda `replay_seed` satırı da yazılır —
    tohumun paydaya girmediğini kanıtlamak için."""
    sb = {"current_version": surum, "versions": {str(surum): {}}}
    if backtest_avg_r is not None:
        sb["versions"][str(surum)]["backtest_full"] = {"avg_r": backtest_avg_r, "n": 95}
    (sandbox_state / "scoreboard.json").write_text(json.dumps(sb))
    satirlar = [{"strategy_version": surum, "r_multiple": canli_r, "kaynak": kaynak}
                for _ in range(n)]
    if tohum_r is not None:
        satirlar += [{"strategy_version": surum, "r_multiple": tohum_r, "kaynak": "replay_seed"}
                     for _ in range(200)]
    (sandbox_state / "trades.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in satirlar))
    return sb


def test_A_tavan_ALTINDA_normal_haldir(sandbox_state):
    _kur(sandbox_state, backtest_avg_r=0.20, canli_r=0.09)
    r = analytics.live_expectancy_ceiling()
    assert r["tavan_r"] == 0.10 and r["oran"] == 0.45
    assert r["durum"] == "tavan_altinda"
    assert r["hukme_girmez"] is True


def test_A_tavan_USTU_bir_basari_ilani_degil_supHe_isaretidir(sandbox_state):
    _kur(sandbox_state, backtest_avg_r=0.20, canli_r=0.15)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "tavan_ustunde" and r["oran"] == 0.75
    assert "ŞÜPHE" in r["hukum"]


def test_A_suspansiyon_esigi_TETIKLENIR_ama_karar_vermez(sandbox_state):
    _kur(sandbox_state, backtest_avg_r=0.20, canli_r=0.05)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "suspansiyon_degerlendirmesi" and r["oran"] == 0.25
    assert r["hukme_girmez"] is True and "KARAR DEĞİL" in r["hukum"]


def test_A_negatif_backtest_beklentisinde_oran_TANIMSIZ(sandbox_state):
    """−0,04'ün yarısı −0,02'dir ve canlı −0,01 gelirse "tavanı aştı" demek saçmadır.
    Canlı karnenin BUGÜNKÜ hâli tam olarak budur (v4 backtest_full.avg_r = −0.042)."""
    _kur(sandbox_state, backtest_avg_r=-0.042, canli_r=-0.01)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi" and r["tavan_r"] is None and r["oran"] is None
    assert "pozitif DEĞİL" in r["neden"]


def test_A_backtest_tarafi_YOKSA_uydurmaz(sandbox_state):
    _kur(sandbox_state, backtest_avg_r=None)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi" and "backtest_full.avg_r` YOK" in r["neden"]


def test_A_orneklem_altinda_SIFIR_degil_BILINMIYOR(sandbox_state):
    _kur(sandbox_state, n=5)
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi" and r["canli_n"] == 5
    assert "BİLİNMİYOR" in r["neden"]


def test_A_replay_seed_paydaya_GIRMEZ(sandbox_state):
    """Tohum satırları TRAINING'dir. Payda yasası `learning_scorecard`ınkiyle birebir aynı olmalı;
    ikinci bir "canlı defter kimdir" cevabı bu depoda yasak."""
    _kur(sandbox_state, canli_r=0.09, n=40, tohum_r=5.0)
    r = analytics.live_expectancy_ceiling()
    assert r["canli_n"] == 40, "tohum satırları paydaya sızdı"
    assert abs(r["canli_beklenti_r"] - 0.09) < 1e-9
    assert r["canli_kanitli_n"] == 40 and r["canli_belirsiz_n"] == 0


def test_A_damgasiz_satir_belirsiz_sayilir_ama_paydaya_girer(sandbox_state):
    _kur(sandbox_state, canli_r=0.09, n=40, kaynak=None)
    r = analytics.live_expectancy_ceiling()
    assert r["canli_n"] == 40 and r["canli_kanitli_n"] == 0 and r["canli_belirsiz_n"] == 40


def test_A_baska_surumun_satirlari_karismaz(sandbox_state):
    _kur(sandbox_state, surum=7, canli_r=0.09, n=40)
    with open(sandbox_state / "trades.jsonl", "a") as f:
        for _ in range(100):
            f.write(json.dumps({"strategy_version": 6, "r_multiple": 9.9,
                                "kaynak": "live_paper"}) + "\n")
    r = analytics.live_expectancy_ceiling()
    assert r["canli_n"] == 40 and abs(r["canli_beklenti_r"] - 0.09) < 1e-9


def test_A_bos_state_HUKUM_UYDURMAZ(sandbox_state):
    r = analytics.live_expectancy_ceiling()
    assert r["durum"] == "olculemedi" and r["neden"]
    assert r["durum"] in analytics.LIVE_CEILING_DURUMLAR


# --- A) KOLON, ÖLÇÜT DEĞİL -----------------------------------------------------------------------
def test_A_tavan_durumu_SONUC_hukmunun_paydasina_DOKUNMAZ(sandbox_state):
    """`beta_duzeltilmis`/`net_kotumser` ile aynı sözleşme: dört ölçüt DÖRT kalır."""
    _kur(sandbox_state, canli_r=0.05)       # süspansiyon tetikleyen en sert hâl
    rv = analytics.result_verdict()
    assert set(rv["criteria"]) == {"dolar_beklenti", "profit_factor", "maks_dusus", "net_pnl"}
    assert rv["passed"] + rv["failed"] + rv["unmeasured"] + rv["zayif"] == 4
    assert rv["verdict"].startswith("SONUÇ:")
    assert rv["tavan_durumu"]["durum"] == "suspansiyon_degerlendirmesi"
    assert rv["tavan_durumu"]["hukme_girmez"] is True


def test_A_tavan_kolonu_hicbir_KAPIYA_baglanmadi():
    """Kaynak çivisi: kapı/silahlanma yolları bu fonksiyonu ÇAĞIRMAZ. Bir gün çağıran çıkarsa,
    "görünür kılar" cümlesi sessizce "hüküm verir"e döner ve bu test kırılır."""
    for dosya in ("probgate.py", "guard.py", "arming.py", "reflect.py", "rollback.py",
                  "health.py", "loop.py", "broker.py"):
        src = (SRC / dosya).read_text()
        assert "live_expectancy_ceiling" not in src, f"{dosya} tavan kolonunu okuyor — kapı kaydı"


def test_A_tavan_kolonu_state_e_YAZMAZ():
    src = (SRC / "analytics.py").read_text()
    blok = src.split("def live_expectancy_ceiling")[1].split("\ndef ")[0]
    for yasak in ("write_json", "update_json", "append_jsonl", "write_jsonl"):
        assert yasak not in blok, f"tavan ölçümü state'e YAZIYOR ({yasak})"


# =================================================================================================
# B) KIYAS-KİRLENMESİ STANDARDI — temiz_taban
# =================================================================================================
def test_B_elle_hesapli_fikstur():
    """ELLE SAYIM (pencere (1,2), yani [olay−1, olay+2] KİRLİ):

      AAA olayı 2026-01-10 → kirli günler 09,10,11,12
        AAA: 08(temiz) 09(K) 10(K) 11(K) 12(K) 13(temiz)          → 2 temiz / 4 kirli
      BBB olayı YOK (listede hiç geçmiyor)
        BBB: 09 10 11 12                                          → 4 temiz / 0 kirli
      CCC olayı 2026-01-20 (seride o pencere hiç yok)
        CCC: 09 10                                                → 2 temiz / 0 kirli

    toplam 12 satır · temiz 8 · kirli 4 · kirlilik = 4/12 = 0.3333
    """
    getiriler = {
        "AAA": {"2026-01-08": 0.1, "2026-01-09": 0.2, "2026-01-10": 0.3,
                "2026-01-11": 0.4, "2026-01-12": 0.5, "2026-01-13": 0.6},
        "BBB": {"2026-01-09": 1.0, "2026-01-10": 1.1, "2026-01-11": 1.2, "2026-01-12": 1.3},
        "CCC": {"2026-01-09": 2.0, "2026-01-10": 2.1},
    }
    r = temiz_taban(getiriler, {"AAA": ["2026-01-10"], "CCC": ["2026-01-20"]}, (1, 2))
    assert r["n_toplam"] == 12 and r["n_temiz"] == 8 and r["n_kirli"] == 4
    assert r["kirlilik_orani"] == 0.3333
    assert [(k, g) for k, g, _ in r["taban"]] == [
        ("AAA", "2026-01-08"), ("AAA", "2026-01-13"),
        ("BBB", "2026-01-09"), ("BBB", "2026-01-10"),
        ("BBB", "2026-01-11"), ("BBB", "2026-01-12"),
        ("CCC", "2026-01-09"), ("CCC", "2026-01-10")]
    assert r["degerler"] == [0.1, 0.6, 1.0, 1.1, 1.2, 1.3, 2.0, 2.1]
    assert r["gun_birimi"] == "takvim gunu"
    assert r["n_olaysiz_kimlik"] == 1          # BBB — "olay yok" değil, "listede yok"
    assert r["pencere"] == {"once": 1, "sonra": 2}


def test_B_olay_gununun_KENDISI_kirlidir():
    r = temiz_taban({"X": {"2026-03-02": 1.0}}, {"X": ["2026-03-02"]}, 0)
    assert r["n_kirli"] == 1 and r["n_temiz"] == 0 and r["kirlilik_orani"] == 1.0
    assert "TEMİZ SATIR KALMADI" in (r["uyari"] or "")


def test_B_isaretli_pencere_de_kabul_edilir():
    """Olay-çalışması yazını `[-1, +2]` diye yazar; şablonun elle çevirmesi gereksiz hata kapısı."""
    a = temiz_taban({"X": {1: 1.0, 2: 2.0, 5: 5.0}}, {"X": [2]}, (-1, 2))
    b = temiz_taban({"X": {1: 1.0, 2: 2.0, 5: 5.0}}, {"X": [2]}, (1, 2))
    assert a["taban"] == b["taban"] == [("X", 5, 5.0)]


def test_B_bos_seride_kirlilik_SIFIR_DEGIL_None():
    """Ölçülmemiş bir temizlik "temiz" diye raporlanamaz (UYDURMA YASAĞI)."""
    r = temiz_taban({}, {"X": ["2026-01-01"]}, 3)
    assert r["n_toplam"] == 0 and r["kirlilik_orani"] is None and r["degerler"] == []


def test_B_gun_birimi_ADIYLA_raporlanir_bar_indeksinde():
    r = temiz_taban([("X", 10, 1.0), ("X", 14, 2.0), ("X", 30, 3.0)], {"X": [12]}, 3)
    assert r["gun_birimi"] == "sira/bar indeksi"
    assert [g for _, g, _ in r["taban"]] == [30]     # 10 ve 14, [9,15] penceresinin içinde


def test_B_karisik_birim_SESSIZCE_toplanmaz():
    with pytest.raises(ValueError, match="KARIŞIK"):
        temiz_taban([("X", 5, 1.0), ("X", "2026-01-01", 2.0)], {"X": [5]}, 1)


def test_B_cozulemeyen_gun_SAYILIR_ve_paydadan_duser():
    r = temiz_taban([("X", "cop", 1.0), ("X", 10, 2.0), ("X", 20, 3.0)], {"X": [10]}, 0)
    assert r["n_cozulemeyen"] == 1 and r["n_olculebilir"] == 2
    assert r["n_kirli"] == 1 and r["n_temiz"] == 1
    assert r["kirlilik_orani"] == 0.5           # payda 2, 3 DEĞİL
    assert "günü çözülemedi" in (r["uyari"] or "")


def test_B_yuksek_kirlilikte_UYARIR():
    """EAP vakası: evrenin %64-74'ü kendi penceresindeydi ve kimse görmedi."""
    getiriler = [("X", g, 1.0) for g in range(10)]
    r = temiz_taban(getiriler, {"X": [2, 6]}, 1)      # 1,2,3 ve 5,6,7 kirli → 6/10
    assert r["kirlilik_orani"] == 0.6
    assert "SIKIŞTIRIRDI" in (r["uyari"] or "")


def test_B_uc_girdi_sekli_de_AYNI_sonucu_verir():
    matris = {"X": {1: 1.0, 5: 2.0}}
    uzun = [("X", 1, 1.0), ("X", 5, 2.0)]
    sozluk = [{"sembol": "X", "tarih": 1, "getiri": 1.0}, {"sembol": "X", "tarih": 5, "getiri": 2.0}]
    ciktilar = [temiz_taban(g, {"X": [1]}, 1) for g in (matris, uzun, sozluk)]
    assert all(c["taban"] == [("X", 5, 2.0)] for c in ciktilar)
    assert all(c["kirlilik_orani"] == 0.5 for c in ciktilar)


def test_B_saf_yaprak_hicbir_meridian_modulunu_import_etmez():
    """Ölçüm şablonları kum havuzundan da çağırabilmeli; ayrıca hiçbir dosyaya YAZMAMALI."""
    src = (SRC / "olcum_araclari.py").read_text()
    assert "from . import" not in src and "from .." not in src and "import meridian" not in src
    for yasak in ("write_json", "append_jsonl", "open("):
        assert yasak not in src, f"ölçüm yardımcısı yan etki taşıyor ({yasak})"


def test_B_docs_standardi_dort_dersi_de_TASIR():
    d = (SRC.parent / "docs" / "olcum_standartlari.md").read_text()
    for parca in ("oosonly", "DİLBİLGİSİ", "TABAN-FAZLASI", "KIYAS TEMİZLİĞİ",
                  "temiz_taban", "kirlilik_orani", "Geriye dönük düzeltme YOK"):
        assert parca in d, f"ölçüm standardı '{parca}' maddesini taşımıyor"


# =================================================================================================
# C) 2C EMPİRİK-BAYES SÜTUNU
# =================================================================================================
def _tablo():
    """n=101 BİLİNÇLİ: sd = √(101/100) ⇒ σ²ᵢ = sd²/n = 1.01/101 = 0.01 TAM — elle hesap yuvarlama
    payı olmadan yürür."""
    def h(ic, n=101):
        return {"ic": ic, "n": n, "ci": None, "anlamli": None}
    return {
        # gercek: 3 hücre, yayılım GERÇEK → kısmi küçültme
        "gercek": {"rs": {"5": h(0.0), "10": h(0.2), "20": h(0.4)}},
        # cf: 3 hücre, yayılım YOK → τ²=0 → TAM küçültme
        "cf": {"rs": {"5": h(0.5), "10": h(0.5), "20": h(0.5)}},
        # havuz: 2 ölçülebilir hücre → SHRINK_MIN_CELLS altı → küçültme YOK
        "havuz": {"rs": {"5": h(0.9), "10": h(0.1), "20": {"ic": None, "n": 3}}},
    }


def test_C_eb_ELLE_hesapli_fiksturde_dogru():
    """ELLE HESAP (gerçek katman, ic = 0.0 / 0.2 / 0.4, n = 101):
         genel (n-ağırlıklı)      = 0.2
         hücreler-arası varyans   = (0.04 + 0 + 0.04) / 2 = 0.04
         ortalama hücre-içi (σ²ᵢ) = 0.01
         τ²  = 0.04 − 0.01        = 0.03
         w   = τ²/(τ²+σ²ᵢ)        = 0.03/0.04 = 0.75
         eb_ic = 0.75·ic + 0.25·0.2 → 0.05 / 0.20 / 0.35
    """
    eb = component_ic._eb_blok(_tablo())
    g = eb["katmanlar"]["gercek"]
    assert g["kucultuldu"] is True and g["n_hucre"] == 3
    assert abs(g["genel_ortalama"] - 0.2) < 1e-9
    assert abs(g["tau2"] - 0.03) < 1e-6
    beklenen = {"rs@5": (0.0, 0.05), "rs@10": (0.2, 0.20), "rs@20": (0.4, 0.35)}
    for ad, (ham, eb_ic) in beklenen.items():
        h = g["hucreler"][ad]
        assert abs(h["ham_ic"] - ham) < 1e-9, ad
        assert abs(h["eb_ic"] - eb_ic) < 1e-4, ad
        assert abs(h["shrink_katsayisi"] - 0.75) < 1e-3, ad
        assert abs(h["cekim"] - (ham - eb_ic)) < 1e-4, ad
        assert h["n"] == 101


def test_C_tau2_sifirsa_TAM_kuculur():
    """Hücreler arasında ölçülebilir gerçek fark YOKSA dürüst cevap tam küçültmedir."""
    cf = component_ic._eb_blok(_tablo())["katmanlar"]["cf"]
    assert cf["tau2"] == 0.0
    for h in cf["hucreler"].values():
        assert h["shrink_katsayisi"] == 0.0 and abs(h["eb_ic"] - 0.5) < 1e-9


def test_C_yetersiz_hucrede_KUCULTMEZ_ve_nedenini_soyler():
    hz = component_ic._eb_blok(_tablo())["katmanlar"]["havuz"]
    assert hz["kucultuldu"] is False and "tahmin EDİLEMEZ" in hz["neden"]
    for h in hz["hucreler"].values():
        assert h["ham_ic"] == h["eb_ic"] and h["cekim"] == 0.0


def test_C_katmanlar_AYRI_kuculur():
    """gerçek (alınmış işlemler) ile cf (alınmamış hipotetik girişler) FARKLI popülasyonlardır;
    tek havuzda küçültmek iki farklı gerçeği tek ortalamaya eritirdi."""
    k = component_ic._eb_blok(_tablo())["katmanlar"]
    assert k["gercek"]["genel_ortalama"] != k["cf"]["genel_ortalama"]
    assert abs(k["cf"]["genel_ortalama"] - 0.5) < 1e-9


def test_C_HAM_ic_alanlari_BIT_BIT_degismedi():
    """GERİYE-UYUM ÇİVİSİ: `eb` bir PARALEL sütundur. `tablo` sözlüğüne tek bayt dokunulmaz —
    okuyucular (beyin/pano/yeniden-üretim farkı) ham `ic` okumaya devam eder."""
    t = _tablo()
    once = copy.deepcopy(t)
    eb = component_ic._eb_blok(t)
    assert t == once, "eb hesabı tabloyu MUTASYONA uğrattı"
    # ve eb bloğu tablonun içine sızmadı
    assert "eb" not in json.dumps(t)
    assert set(eb["katmanlar"]) == set(component_ic.LAYERS)


def test_C_eb_TABLONUN_YANINDA_durur_icinde_degil():
    src = (SRC / "component_ic.py").read_text()
    assert '"eb": _eb_blok(tablo)' in src, "eb bloğu çıktıya bağlanmamış"
    blok = src.split("def _eb_blok")[1].split("\ndef ")[0]
    assert "tablo[" not in blok, "_eb_blok tabloya yazıyor"


def test_C_beyin_ozeti_eb_den_ETKILENMEZ():
    """`compact_lines` beyne gider ve HAM ic okumalı — eb bloğu eklendiğinde satırlar değişmemeli."""
    doc = {"tablo": _tablo(), "components": ["rs"], "horizons": [5, 10, 20],
           "agirliklar": {"rs": 0.35}, "getiri_tanimi": "close[t+h]/close[t]-1"}
    once = component_ic.compact_lines(doc)
    doc["eb"] = component_ic._eb_blok(doc["tablo"])
    assert component_ic.compact_lines(doc) == once


def test_C_yontem_ve_shrink_tanimi_CIKTININ_ICINDE():
    """Panoyu/beyni okuyan biri "shrink_katsayisi 1 mi iyi 0 mı iyi?" sorusunu koda inmeden
    cevaplayabilmeli — `_fisher_ci`nin `ci_yontem` beyanıyla aynı gerekçe."""
    eb = component_ic._eb_blok(_tablo())
    assert "James-Stein" in eb["yontem"] and "τ²" in eb["yontem"]
    assert "w=1" in eb["shrink_katsayisi_tanimi"] and "w=0" in eb["shrink_katsayisi_tanimi"]
    assert "1/√(n−1)" in eb["sigma_yasasi"] and "1/√(n−3)" in eb["sigma_yasasi"]
    assert "ham `ic` alanları DEĞİŞMEZ" in eb["beyan"]


# --- C) YASA 6: ÜRETİLEN ALANIN DIŞ OKUYUCUSU ----------------------------------------------------
def test_C_okuyucu_blok_YOKKEN_durustce_yok_der(sandbox_state):
    (sandbox_state / "component_ic.json").write_text(json.dumps({"tablo": _tablo()}))
    r = analytics.shrunk_component_ic()
    assert r["tablo_ici_eb"]["var"] is False and "YOK" in r["tablo_ici_eb"]["neden"]
    assert r["n_hucre"] == 3, "pano okuyucusunun KENDİ hesabı bozuldu"


def test_C_okuyucu_blogu_gorunur_kilar(sandbox_state):
    tablo = _tablo()
    (sandbox_state / "component_ic.json").write_text(
        json.dumps({"tablo": tablo, "eb": component_ic._eb_blok(tablo)}))
    r = analytics.shrunk_component_ic()
    t = r["tablo_ici_eb"]
    assert t["var"] is True and t["hukum_verir"] is False and t["n_hucre"] == 3
    assert t["en_cok_cekilen"]["hucre"] in ("rs@5", "rs@20")
    assert abs(abs(t["en_cok_cekilen"]["cekim"]) - 0.05) < 1e-4


def test_C_iki_cetvel_YOK_pano_okuyucusu_ile_tablo_blogu_ayni(sandbox_state):
    """TEK UYGULAMA, İKİ TÜKETİCİ: `analytics.shrunk_component_ic` ile tablonun kendi `eb` bloğu
    AYNI hücre kurucusunu ve AYNI küçültmeyi kullanır. Ayrışırlarsa aynı adı taşıyan iki farklı
    sayı doğar ve fark ancak üçüncü haneyi karşılaştıran biri tarafından görülür."""
    tablo = _tablo()
    (sandbox_state / "component_ic.json").write_text(
        json.dumps({"tablo": tablo, "eb": component_ic._eb_blok(tablo)}))
    r = analytics.shrunk_component_ic()
    blok = component_ic._eb_blok(tablo)["katmanlar"]["gercek"]["hucreler"]
    for ad, h in r["hucreler"].items():
        assert h["kucultulmus"] == blok[ad]["eb_ic"], ad
        assert h["agirlik"] == blok[ad]["shrink_katsayisi"], ad


def test_C_kuculTulmus_deger_VERDICT_tabanlarina_girmez():
    """2C'nin kurucu çivisi (test_hafta3b_v125 ile aynı yasa) `eb` sütunu için de geçerli:
    küçültme n'i BÜYÜTMEZ, dolayısıyla hiçbir eşiğe/hükme giremez."""
    src = (SRC / "analytics.py").read_text()
    for ad in ("def edge_verdict", "def result_verdict"):
        blok = src.split(ad)[1].split("\ndef ")[0]
        assert "shrunk_" not in blok and "_eb_blok" not in blok, f"{ad} küçültülmüş değer okuyor"
    ci_src = (SRC / "component_ic.py").read_text()
    hukum_blok = ci_src.split("# HÜKÜM: en güçlü")[1].split("out = {")[0]
    for yasak in ("_eb_blok", '["eb"]', '"eb_ic"', "shrink_katsayisi"):
        assert yasak not in hukum_blok, f"component_ic hükmü eb sütununu okuyor ({yasak})"
