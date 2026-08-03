"""WP-M ÖLÇÜM ŞASİSİ — dört araç + iki damga, tek tur (v173, 2026-08-02).

A) 2B  BLOK-BOOTSTRAP CI   — `olcum_araclari.blok_bootstrap_ci` (moving block)
B) 2C  EMPİRİK-BAYES       — `olcum_araclari.eb_kucult` (SE tabanlı, kazananın laneti)
C) KIYAS-KİRLENMESİ (gün)  — `olcum_araclari.olay_disi_kiyas` (+ `temiz_taban` KIRILMADI çivisi)
D) KOD-SÜRÜMÜ DAMGASI      — `olcum_araclari.kod_surumu_damgasi` → prescreen raporları
E) CANLI-BEKLENTİ TAVANI   — v146'da bağlanmıştı; bu tur YALNIZ TEK-KAYNAK çivisi çakar

BU DOSYANIN EN ÖNEMLİ TESTLERİ "yeni araç doğru mu" değil, ŞUNLARDIR:
  * yeni araç MEVCUT hesapları oynatmadı mı (analytics/temiz_taban devredilmedi),
  * araç ölçemediğinde UYDURMUYOR mu (None + neden, 0.0/False DEĞİL),
  * aynı kuralın İKİNCİ bir adı doğmadı mı (tek doğruluk kaynağı).

ÖLÇÜLMÜŞ SAYILAR (bu dosyadaki sentetiklerden, sabit tohumla — tekrarlanabilir):
  * AR(1) φ=0,5 · n=1000 · M=300 kol: blok kapsaması 0,923 · IID kapsaması 0,700.
    Blok bootstrap ORTA n'de %95'in bir miktar ALTINDA kapsar (yazının bilinen davranışı, blok
    uzadıkça %95'e yaklaşır: L=20'de 0,940 ölçüldü) — bu test o gerçeği BANTLA kabul eder,
    "±0" diye uydurmaz. IID'nin kusuru ise tek yönlüdür ve büyüktür: 0,70.
  * EB küçültme (K=20, τ=0,4, M=300): MSE 0,6063 → 0,1646 (%73 iyileşme); ham kazanan yanlılığı
    +1,3716 iken küçültülmüş kazanan −0,0397. Ham "en iyi hücre" GERÇEK etkisinin ~3,4 katını
    gösteriyordu (τ=0,4 iken +1,37 yanlılık).
"""
import pathlib
import subprocess

import numpy as np
import pytest

from meridian import analytics, config
from meridian.olcum_araclari import (ARAC_SURUMLERI, SURUM, blok_bootstrap_ci, eb_kucult,
                                     kod_surumu_damgasi, olay_disi_kiyas, temiz_taban)

KOK = pathlib.Path(__file__).resolve().parent.parent
SRC = KOK / "meridian"


# =================================================================================================
# A) 2B — BLOK-BOOTSTRAP CI
# =================================================================================================
def _ar1(n: int, phi: float, rng) -> np.ndarray:
    """Bilinen GERÇEĞİ olan sentetik: ortalaması TAM 0 olan AR(1). Kapsama testinin dayanağı bu —
    gerçeği bilmediğimiz bir seride "aralık doğru mu" sorusu sorulamaz."""
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0] / np.sqrt(1 - phi ** 2)          # durağan başlangıç (ısınma yanlılığı olmasın)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def _kapsama(phi: float, n: int, M: int, blok=None, B: int = 400) -> float:
    """M bağımsız kolda, aralığın GERÇEK ortalamayı (0) kapsama oranı. Tohumlar SABİT."""
    rng = np.random.default_rng(7)
    kapsayan = 0
    for m in range(M):
        r = blok_bootstrap_ci(_ar1(n, phi, rng), blok=blok, n_ornek=B, tohum=100 + m)
        kapsayan += int(r["lo"] <= 0.0 <= r["hi"])
    return kapsayan / M


def test_A_AR1_kapsamasi_blok_ile_YUKSEK_IID_ile_COKUYOR():
    """BU TESTİN VAR OLUŞ SEBEBİ: IID bootstrap'ın kusuru TEK YÖNLÜDÜR — daima "daha anlamlı"
    görünür, hiçbir zaman daha az. Otokorelasyonlu bir seride IID aralık gerçeği yalnız %70
    kapsıyor, yani nominal %95'lik bir aralık aslında %70'lik. Böyle bir aralıkla verilen "CI
    0-dışı" hükmü, ölçülmemiş bir kesinliktir.

    BLOK TARAFI DA MÜKEMMEL DEĞİL ve bu test onu ÖRTMEZ: orta n'de kapsama %95'in bir miktar
    altındadır (ölçülen 0,923). Bant bilerek geniş: "±0" yazmak, ölçülmemiş bir kesinlik iddia
    etmek olurdu — tam da bu aracın önlemeye çalıştığı şey."""
    blok = _kapsama(phi=0.5, n=1000, M=300)
    iid = _kapsama(phi=0.5, n=1000, M=300, blok=1)
    assert 0.88 <= blok <= 0.97, f"blok kapsaması bandın dışında: {blok}"
    assert iid <= 0.80, f"IID kapsaması beklenenden İYİ ({iid}) — sentetiğin otokorelasyonu bozuldu"
    assert blok - iid >= 0.15, f"blok/IID farkı kayboldu (blok={blok}, iid={iid})"


def test_A_bagimsiz_seride_iki_yontem_de_dogru_kapsar():
    """POZİTİF KONTROLÜN İKİZİ: φ=0 (gerçekten bağımsız) seride blok bootstrap IID'den KÖTÜ
    olmamalı. Aksi hâlde araç "her koşulda daha geniş aralık" üreten bir muhafazakârlık makinesi
    olurdu; ölçtüğü şey bağımlılık değil, kendi blok uzunluğu olurdu."""
    blok = _kapsama(phi=0.0, n=400, M=200)
    iid = _kapsama(phi=0.0, n=400, M=200, blok=1)
    assert 0.90 <= blok <= 0.99 and 0.90 <= iid <= 0.99
    assert abs(blok - iid) <= 0.06, f"bağımsız seride ayrışma: blok={blok} iid={iid}"


def test_A_deterministik_ayni_seri_ayni_aralik():
    x = list(_ar1(300, 0.4, np.random.default_rng(1)))
    a, b = blok_bootstrap_ci(x), blok_bootstrap_ci(x)
    assert (a["lo"], a["hi"]) == (b["lo"], b["hi"])
    assert a["tohum"] == b["tohum"]


def test_A_blok_uzunlugu_KURALI_adiyla_raporlanir():
    r = blok_bootstrap_ci(list(range(1000)))
    assert r["blok"] == 10 and r["blok_kaynagi"] == "n^(1/3) kuralı"      # 1000^(1/3) = 10
    v = blok_bootstrap_ci(list(range(1000)), blok=25)
    assert v["blok"] == 25 and v["blok_kaynagi"] == "verildi"
    kirpik = blok_bootstrap_ci([1.0, 2.0, 3.0], blok=99)
    assert kirpik["blok"] == 3 and "kırpıldı" in kirpik["blok_kaynagi"]


def test_A_IID_kolu_DAMGALANIR():
    """`blok=1` reddedilmez ama SESSİZ de kalmaz — kartta gerekçesi yazılmadan kullanılamaz."""
    r = blok_bootstrap_ci([0.1, -0.2, 0.3, 0.05, -0.1, 0.2], blok=1)
    assert r["iid"] is True and "IID" in (r["uyari"] or "")
    assert blok_bootstrap_ci([0.1, -0.2, 0.3, 0.05, -0.1, 0.2])["iid"] is False


@pytest.mark.parametrize("seri", [[], [0.5], None])
def test_A_olculemeyen_aralik_None_ve_NEDENLI(seri):
    """UYDURMA YASAĞI: n<2'de `lo/hi` None ve `sifiri_disliyor` da None — False DEĞİL.
    "sıfırı dışlamıyor" ölçülmüş bir cevaptır; ölçülememiş olan onun yerine geçemez."""
    r = blok_bootstrap_ci(seri)
    assert r["lo"] is None and r["hi"] is None
    assert r["sifiri_disliyor"] is None
    assert r["neden"] and "kurulamaz" in r["neden"]


def test_A_sayi_olmayan_gozlem_SESSIZCE_dusmez():
    r = blok_bootstrap_ci([1.0, None, 2.0, float("nan"), 3.0, "x", float("inf")])
    assert r["n"] == 3 and r["n_cozulemeyen"] == 4
    assert "4 gözlem sayı değildi" in (r["uyari"] or "")


def test_A_sifiri_disliyor_dogru_okunuyor():
    ayrik = blok_bootstrap_ci([5.0, 5.1, 4.9, 5.2, 5.0, 4.95, 5.05, 5.1])
    assert ayrik["sifiri_disliyor"] is True and ayrik["lo"] > 0
    sifirli = blok_bootstrap_ci([1.0, -1.0, 0.5, -0.5, 1.2, -1.1, 0.3, -0.4])
    assert sifirli["sifiri_disliyor"] is False and sifirli["lo"] < 0 < sifirli["hi"]


def _import_ediyor_mu(dosya: str, modul: str) -> bool:
    """AST ÇİVİSİ, metin araması DEĞİL: `olcum_araclari` adı analytics'te BEYAN olarak (yorumda)
    geçiyor ve geçmelidir de — ikizliğin yazılı olması bu turun şartı. Sorulan soru "adı geçiyor
    mu" değil, "GERÇEKTEN import edilip çağrılıyor mu"dur."""
    import ast
    agac = ast.parse((SRC / dosya).read_text())
    for d in ast.walk(agac):
        if isinstance(d, ast.Import) and any(modul in a.name for a in d.names):
            return True
        if isinstance(d, ast.ImportFrom) and (modul in (d.module or "")
                                              or any(modul in a.name for a in d.names)):
            return True
    return False


def test_A_analytics_KENDI_bootstrapini_DEVRETMEDI():
    """YAYIMLANMIŞ SAYI OYNATILMADI ÇİVİSİ. `analytics._blok_bootstrap_ci` (circular blok, blok=5
    İŞLEM) `result_verdict`in tabanıdır; yeni araca devredilseydi pano aralıkları HABERSİZ
    kayardı. Kaynak seviyesinde bekçi: analytics yeni aracı import ETMEZ."""
    src = (SRC / "analytics.py").read_text()
    assert "def _blok_bootstrap_ci" in src, "analytics kendi bootstrap'ını kaybetmiş"
    assert not _import_ediyor_mu("analytics.py", "olcum_araclari"), \
        "analytics ölçüm aracına devretmiş — yayımlanmış aralıklar kayar"
    assert analytics.BOOT_BLOCK_TRADES == 5 and analytics.BOOT_SEED == 11


# =================================================================================================
# B) 2C — EMPİRİK-BAYES KÜÇÜLTME
# =================================================================================================
def _eb_sentetik(M: int = 300, K: int = 20, tau: float = 0.4):
    """BİLİNEN GERÇEK: θᵢ ~ N(0, τ²), gözlem xᵢ = θᵢ + N(0, SEᵢ²). Küçültme MSE'yi düşürmeli.
    Dönüş: (ham MSE, EB MSE, ham kazanan yanlılığı, EB kazanan yanlılığı, sıra değişme sayısı)."""
    rng = np.random.default_rng(4242)
    mse_h = mse_e = b_h = b_e = 0.0
    sira = 0
    for _ in range(M):
        theta = rng.normal(0, tau, K)
        se = rng.uniform(0.3, 1.2, K)
        x = theta + rng.normal(0, se)
        r = eb_kucult({f"h{i}": float(x[i]) for i in range(K)},
                      {f"h{i}": float(se[i]) for i in range(K)})
        km = np.array([r["hucreler"][f"h{i}"]["kucultulmus"] for i in range(K)])
        mse_h += float(np.mean((x - theta) ** 2))
        mse_e += float(np.mean((km - theta) ** 2))
        j = int(np.argmax(x))                    # SEÇİM ham değere göre yapılır (gerçek pratik)
        b_h += float(x[j] - theta[j])
        b_e += float(km[j] - theta[j])
        sira += int(int(np.argmax(km)) != j)
    return mse_h / M, mse_e / M, b_h / M, b_e / M, sira


def test_B_kalibrasyon_KUCULTME_MSEyi_DUSURUR():
    """BİLİNEN GERÇEK → küçültme kazanır. Bu, aracın tek kalibrasyon kanıtıdır: gerçeği bilmeden
    "küçültme daha iyi" cümlesi bir inançtır, ölçüm değil."""
    mse_ham, mse_eb, *_ = _eb_sentetik()
    assert mse_eb < mse_ham, f"küçültme MSE'yi DÜŞÜRMEDİ (ham={mse_ham:.4f}, eb={mse_eb:.4f})"
    assert mse_eb / mse_ham <= 0.5, f"iyileşme beklenenden küçük: {mse_eb / mse_ham:.3f}"


def test_B_KAZANANIN_LANETI_kuculterek_geri_alinir():
    """Aracın var oluş sebebi. HAM en iyi hücre, gerçek etkisinden SİSTEMATİK olarak yukarıdadır
    (ölçülen yanlılık +1,37 — oysa hücreler arası gerçek yayılım τ=0,4). Küçültülmüş kazanan
    neredeyse yansızdır. `sira_degisti` de gerçektir: ham sıralama gürültüye borçludur."""
    _, _, yanlilik_ham, yanlilik_eb, sira = _eb_sentetik()
    assert yanlilik_ham > 1.0, f"sentetikte kazananın laneti yok ({yanlilik_ham:.3f})"
    assert abs(yanlilik_eb) < 0.2, f"küçültülmüş kazanan hâlâ yanlı ({yanlilik_eb:.3f})"
    assert abs(yanlilik_eb) < abs(yanlilik_ham) / 3
    assert sira > 0, "hiçbir kolda sıra değişmedi — kurgu gerçekçi değil"


def test_B_elle_hesapli_kucultme():
    """ELLE HESAP: x = (1,0 · 0,0 · −1,0), SE = 1,0 (üçü de) →
       hedef = 0,0 · yayılım = ((1)²+0+(1)²)/2 = 1,0 · ort SE² = 1,0 → τ² = max(0, 1−1) = 0
       → w = 0 → her hücre TAM hedefe küçülür."""
    r = eb_kucult({"a": 1.0, "b": 0.0, "c": -1.0}, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert r["kucultuldu"] is True and r["tau2"] == 0.0 and r["hedef"] == 0.0
    assert all(h["kucultulmus"] == 0.0 and h["agirlik"] == 0.0 for h in r["hucreler"].values())
    assert "τ²=0" in (r["uyari"] or "")


def test_B_gercek_yayilim_KISMI_kuculme_verir():
    """Yayılım gürültüden BÜYÜKSE küçültme kısmidir ve ağırlık (0,1) aralığındadır."""
    r = eb_kucult({"a": 3.0, "b": 0.0, "c": -3.0}, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert r["tau2"] > 0
    for ad in ("a", "b", "c"):
        w = r["hucreler"][ad]["agirlik"]
        assert 0.0 < w < 1.0
        assert abs(r["hucreler"][ad]["kucultulmus"]) < abs(r["hucreler"][ad]["ham"]) or ad == "b"
    assert r["en_iyi_ham"]["hucre"] == "a" and r["en_iyi_ham"]["cekim"] > 0


def test_B_az_hucrede_KUCULTME_YOK_ve_NEDEN_yazili():
    r = eb_kucult({"a": 1.0, "b": 2.0}, {"a": 0.5, "b": 0.5})
    assert r["kucultuldu"] is False and "TAHMİN EDİLEMEZ" in r["neden"]
    assert r["tau2"] is None and r["en_iyi_ham"] is None
    assert r["hucreler"] == {} or all(h.get("kucultulmus") == h.get("ham")
                                      for h in r["hucreler"].values())


def test_B_SEsiz_hucre_ATILMAZ_SAYILIR():
    """SE'siz bir hücreye ağırlık uydurmak, ölçülmemiş bir kesinlik yazmaktır. Hücre ham hâliyle
    durur ve sayacı vardır."""
    r = eb_kucult({"a": 1.0, "b": 0.0, "c": -1.0, "d": 5.0, "e": 9.0},
                  {"a": 1.0, "b": 1.0, "c": 1.0, "d": None, "e": 0.0})
    assert r["n_se_yok"] == 1 and r["n_se_gecersiz"] == 1
    assert r["hucreler"]["d"]["kucultulmus"] == 5.0 and r["hucreler"]["d"]["agirlik"] == 1.0
    assert r["hucreler"]["e"]["kucultulmus"] == 9.0
    assert r["n_hucre"] == 3                        # yalnız küçültülebilenler sayılır
    assert "SE'si YOK" in (r["uyari"] or "") and "pozitif değildi" in (r["uyari"] or "")
    # SE'siz hücre "en iyi" yarışına da GİREMEZ (küçültülmemiş 9,0 kazanan ilan edilemez)
    assert r["en_iyi_ham"]["hucre"] in ("a", "b", "c")


def test_B_hizasi_kaymis_SE_listesi_HATA():
    with pytest.raises(ValueError, match="uyuşmuyor"):
        eb_kucult([1.0, 2.0, 3.0], [0.5, 0.5])


def test_B_liste_ve_sozluk_girdisi_AYNI_sonucu_verir():
    liste = eb_kucult([1.0, 0.0, -1.0], [1.0, 1.0, 1.0])
    sozluk = eb_kucult({"0": 1.0, "1": 0.0, "2": -1.0}, {"0": 1.0, "1": 1.0, "2": 1.0})
    assert liste["hucreler"] == sozluk["hucreler"] and liste["tau2"] == sozluk["tau2"]


def test_B_analytics_EB_uygulamasi_DEVREDILMEDI():
    """`component_ic.json`ın `eb` sütunu ve pano `analytics._empirical_bayes`ten okur; ortak gövdeye
    indirgense YAYIMLANMIŞ `eb_ic` sayıları habersiz oynardı. İkizlik BEYANLI, gövde AYRI."""
    src = (SRC / "analytics.py").read_text()
    assert "def _empirical_bayes" in src and "eb_kucult" in src   # ikizin adı yazılı (beyan)
    assert not _import_ediyor_mu("analytics.py", "olcum_araclari")
    govde = src.split("def _empirical_bayes")[1].split("\ndef ")[0]
    assert "eb_kucult(" not in govde, "analytics'in gövdesi yeni araca devretmiş"


# =================================================================================================
# C) KIYAS-KİRLENMESİ — GÜN BAZLI OLAY-DIŞI KIYAS
# =================================================================================================
def _evren():
    """11 sembol × 21 gün (sıra birimi). 6 olay sembolü 10. günde olay yaşar (pencere ±1 → 9/10/11
    kirli) ve o gün 0,05 getirir; 5 temiz sembol her gün 0,01 getirir.

    ELLE HESAP (10. gün): temiz taban medyanı = 0,01 → fazla = 0,04.
    KİRLİ taban (kendi hariç TÜM satırlar) = medyan([0,01 ×5, 0,05 ×5]) = 0,03 → fazla = 0,02.
    Yani kirli kıyas etkiyi TAM YARIYA sıkıştırır — EAP'nin yan bulgusunun birebir kurgusu."""
    satirlar = []
    olay_sembolleri = [f"O{i}" for i in range(1, 7)]
    for s in olay_sembolleri + [f"T{i}" for i in range(1, 6)]:
        for g in range(21):
            v = 0.05 if (s.startswith("O") and g == 10) else 0.01
            satirlar.append((s, g, v))
    return satirlar, {s: [10] for s in olay_sembolleri}


def test_C_gun_tabani_OLAY_SATIRLARINI_DISLIYOR():
    satirlar, olaylar = _evren()
    hedefler = [(s, 10, 0.05) for s in olaylar]
    r = olay_disi_kiyas(satirlar, olaylar, pencere=1, hedefler=hedefler)
    assert r["n_kiyaslanan"] == 6 and r["n_taban_yok"] == 0
    assert all(abs(k["taban"] - 0.01) < 1e-12 for k in r["kiyaslar"])
    assert all(abs(k["fazla"] - 0.04) < 1e-12 for k in r["kiyaslar"])
    assert all(k["n_taban"] == 5 for k in r["kiyaslar"])          # 5 temiz sembol
    assert r["gun_birimi"] == "sira/bar indeksi"


def test_C_SIKISMA_olculur_ve_raporlanir():
    """Kirli taban aynı hedefleri OLAYLA kıyaslar ve etkiyi 0,04'ten 0,02'ye sıkıştırır. Bu sayı
    raporun İÇİNDE durur — düzeltmenin büyüklüğünü görmeyen okuyucu, düzeltmenin gerekli olup
    olmadığını değerlendiremez."""
    satirlar, olaylar = _evren()
    r = olay_disi_kiyas(satirlar, olaylar, pencere=1,
                        hedefler=[(s, 10, 0.05) for s in olaylar])
    s = r["sikisma"]
    assert abs(s["temiz"] - 0.04) < 1e-12 and abs(s["kirli"] - 0.02) < 1e-12
    assert abs(s["fark"] - 0.02) < 1e-12
    assert "hükme girmez" in s["aciklama"]
    assert all(abs(k["kirli_fazla"] - 0.02) < 1e-12 for k in r["kiyaslar"])


def test_C_varsayilan_hedefler_KIRLI_satirlardir():
    satirlar, olaylar = _evren()
    r = olay_disi_kiyas(satirlar, olaylar, pencere=1)
    assert r["n_hedef"] == 18                      # 6 sembol × (9, 10, 11)
    assert "varsayılan" in r["hedef_kaynagi"]
    assert r["n_kirli"] == 18 and r["kirlilik_orani"] == round(18 / 231, 4)
    # 9. ve 11. günlerde olay sembolü de 0,01 getiriyor → fazla 0; yalnız 10. günde 0,04
    fazlalar = sorted(round(f, 4) for f in r["fazlalar"])
    assert fazlalar.count(0.0) == 12 and fazlalar.count(0.04) == 6


def test_C_KENDI_SATIRI_kendi_tabanina_GIRMEZ():
    """Aksi hâlde ölçüm kendini kendine kıyaslar ve etkiyi 1/N kadar sistematik küçültür.
    ELLE: hedef X=1,0; taban {A:0,0 · B:0,0}. Kendi hariç ortalama = 0,0 → fazla = 1,0.
    Kendi DAHİL olsaydı ortalama 1/3 olur, fazla 0,667 çıkardı."""
    satirlar = [("X", 5, 1.0), ("A", 5, 0.0), ("B", 5, 0.0)]
    r = olay_disi_kiyas(satirlar, {}, pencere=1, hedefler=[("X", 5, 1.0)],
                        ozet="ortalama", min_taban=2)
    k = r["kiyaslar"][0]
    assert k["n_taban"] == 2 and k["taban"] == 0.0 and k["fazla"] == 1.0


def test_C_ZAYIF_TABAN_atlanir_ama_SAYILIR():
    """Sessizce düşen hedef, seçim yanlılığıdır: tabanı zayıf günler İNCE günlerdir, rastgele
    değildir."""
    satirlar = [("X", 5, 1.0), ("A", 5, 0.0), ("B", 5, 0.0)]
    r = olay_disi_kiyas(satirlar, {}, pencere=1, hedefler=[("X", 5, 1.0)], min_taban=5)
    assert r["n_kiyaslanan"] == 0 and r["n_taban_yok"] == 1
    assert "RASTGELE değildir" in (r["uyari"] or "")
    assert "HİÇBİR HEDEF KIYASLANAMADI" in (r["uyari"] or "")
    assert r["sikisma"] is None and r["fazla_ozeti"] is None


def test_C_yuksek_kirlilikte_UYARI():
    """EAP vakası: evrenin %64-74'ü kendi olay penceresindeydi. Böyle bir tabloda uyarı ŞART."""
    satirlar = [(f"S{i}", 10, 0.02) for i in range(10)] + [(f"S{i}", 3, 0.01) for i in range(10)]
    olaylar = {f"S{i}": [10] for i in range(8)}
    r = olay_disi_kiyas(satirlar, olaylar, pencere=0, hedefler=[("S0", 10, 0.02)], min_taban=2)
    assert r["kirlilik_orani"] == 0.4
    satirlar2 = [(f"S{i}", 10, 0.02) for i in range(10)]
    r2 = olay_disi_kiyas(satirlar2, olaylar, pencere=0, hedefler=[("S0", 10, 0.02)], min_taban=2)
    assert r2["kirlilik_orani"] == 0.8 and "SIKIŞTIRIRDI" in (r2["uyari"] or "")


def test_C_karisik_gun_birimi_HATA():
    with pytest.raises(ValueError, match="KARIŞIK"):
        olay_disi_kiyas([("X", 5, 1.0), ("Y", "2026-01-05", 1.0)], {}, pencere=1)


def test_C_taninmayan_ozet_HATA():
    """Sessiz varsayılan seçmek, ölçütü ölçümden SONRA seçmek olurdu (Ders #2'nin ikizi)."""
    with pytest.raises(ValueError, match="tanınmıyor"):
        olay_disi_kiyas([("X", 5, 1.0)], {}, pencere=1, ozet="geometrik")


def test_C_cozulemeyen_satir_SESSIZCE_dusmez():
    satirlar = [("X", 5, 1.0), ("A", 5, 0.0), ("B", 5, 0.0), ("C", None, 0.0), ("D", 5, "abc")]
    r = olay_disi_kiyas(satirlar, {}, pencere=1, hedefler=[("X", 5, 1.0)], min_taban=2)
    assert r["n_cozulemeyen"] == 2 and "çözülemedi" in (r["uyari"] or "")
    r2 = olay_disi_kiyas(satirlar, {}, pencere=1, hedefler=[("Z", None, 1.0)], min_taban=2)
    assert r2["n_deger_cozulemeyen"] == 1


def test_C_gun_tabani_tablosu_her_gunu_TASIR():
    satirlar, olaylar = _evren()
    r = olay_disi_kiyas(satirlar, olaylar, pencere=1)
    assert r["n_gun"] == 21 and len(r["gun_tabani"]) == 21
    g10 = r["gun_tabani"]["10"]
    assert g10["n_temiz"] == 5 and g10["n_kirli"] == 6
    assert g10["kirlilik_orani"] == round(6 / 11, 4)
    assert abs(g10["taban"] - 0.01) < 1e-12 and abs(g10["kirli_taban"] - 0.05) < 1e-12
    assert r["gun_tabani"]["0"]["n_kirli"] == 0


def test_C_TEMIZ_TABAN_KIRILMADI():
    """`temiz_taban` bu turda ORTAK yardımcılara taşındı (`_olaylari_ordinalle`, `_birim_kontrolu`).
    Belgelenmiş davranışı BİT-BİT aynı kalmalı — v146'nın çivileri burada da çakılı."""
    getiriler = [("X", g, 1.0) for g in range(10)]
    r = temiz_taban(getiriler, {"X": [2, 6]}, 1)          # 1,2,3 ve 5,6,7 kirli → 6/10
    assert r["kirlilik_orani"] == 0.6 and r["n_temiz"] == 4 and r["n_kirli"] == 6
    assert "SIKIŞTIRIRDI" in (r["uyari"] or "")
    matris = {"X": {1: 1.0, 5: 2.0}}
    uzun = [("X", 1, 1.0), ("X", 5, 2.0)]
    sozluk = [{"sembol": "X", "tarih": 1, "getiri": 1.0}, {"sembol": "X", "tarih": 5, "getiri": 2.0}]
    ciktilar = [temiz_taban(g, {"X": [1]}, 1) for g in (matris, uzun, sozluk)]
    assert all(c["taban"] == [("X", 5, 2.0)] for c in ciktilar)
    assert all(c["kirlilik_orani"] == 0.5 for c in ciktilar)
    assert temiz_taban([], {}, 1)["kirlilik_orani"] is None      # 0.0 DEĞİL
    with pytest.raises(ValueError, match="KARIŞIK"):
        temiz_taban([("X", 5, 1.0), ("Y", "2026-01-05", 1.0)], {}, 1)


def test_C_iki_taban_FARKLI_sorulara_cevap_verir():
    """`temiz_taban` HAVUZ, `olay_disi_kiyas` GÜN tabanı. Aynı veride farklı sayılar üretmeleri bir
    tutarsızlık değil, iki ayrı sorunun cevabıdır — kart hangisini kullandığını YAZAR."""
    satirlar, olaylar = _evren()
    havuz = temiz_taban(satirlar, olaylar, 1)
    gun = olay_disi_kiyas(satirlar, olaylar, pencere=1)
    assert havuz["n_kirli"] == gun["n_kirli"] == 18          # kirlilik TANIMI ortak
    assert havuz["kirlilik_orani"] == gun["kirlilik_orani"]  # ve aynı paydadan okunuyor
    assert "taban" in havuz and "gun_tabani" in gun          # ama sözleşmeleri farklı


def test_C_ZINCIR_gun_bazli_fazlalar_bootstrapa_girebilir():
    """YOL BÜTÜNLÜĞÜ: Ders #5 → Ders #6 zinciri gerçekten kuruluyor mu (fazlalar bir seridir ve
    aralığı blok bootstrap'la kurulur)."""
    satirlar, olaylar = _evren()
    r = olay_disi_kiyas(satirlar, olaylar, pencere=1,
                        hedefler=[(s, 10, 0.05) for s in olaylar])
    ci = blok_bootstrap_ci(r["fazlalar"], n_ornek=200)
    assert ci["n"] == 6 and ci["lo"] is not None
    assert abs(ci["ort"] - 0.04) < 1e-12


# =================================================================================================
# D) KOD-SÜRÜMÜ DAMGASI
# =================================================================================================
def test_D_depoda_git_HEAD_okunuyor():
    d = kod_surumu_damgasi()
    assert d["git_head"] and len(d["git_head"]) == 40
    assert d["git_head_kisa"] == d["git_head"][:7]
    assert d["kirli_agac"] in (True, False)          # None DEĞİL: bu depo bir git deposu
    assert d["git_neden"] is None
    beklenen = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(KOK),
                              capture_output=True, text=True).stdout.strip()
    assert d["git_head"] == beklenen


def test_D_git_YOKSA_None_ve_NEDEN(tmp_path):
    """UYDURMA YASAĞI: depo değilse SHA None'dır ve sebebi yazılıdır — boş dizgi ya da eski bir
    SHA konmaz."""
    d = kod_surumu_damgasi(kok=tmp_path)
    assert d["git_head"] is None and d["git_head_kisa"] is None
    assert d["kirli_agac"] is None
    assert d["git_neden"] and "git" in d["git_neden"]
    assert d["arac_surumleri"] == dict(ARAC_SURUMLERI)      # araç listesi git'ten BAĞIMSIZ


def test_D_arac_surum_listesi_GERCEK_araclari_sayiyor():
    from meridian import olcum_araclari
    for ad in ARAC_SURUMLERI:
        assert callable(getattr(olcum_araclari, ad, None)), f"{ad} sürüm listesinde ama yok"
    assert kod_surumu_damgasi()["olcum_araclari_surum"] == SURUM


def test_D_prescreen_raporu_damgayi_TASIR():
    """`prescreen.run` tam bir walk_forward koşar (bu testin kapsamı değil) — damganın rapor
    ZARFINDA olduğu ve koşu başında TEK KEZ alındığı kaynaktan çivilenir."""
    src = (SRC / "prescreen.py").read_text()
    assert src.count("kod_surumu_damgasi()") == 1, "damga aday başına yeniden alınıyor olabilir"
    assert 'damga = olcum_araclari.kod_surumu_damgasi()' in src
    # ÜÇ ÇIKIŞ YOLU, ÜÇ DAMGA (v182'de üçüncüsü eklendi): kısmi rapor · nihai rapor · guard'ın
    # hepsini reddettiği ERKEN dönüş. Üçüncüsü kuyruğa kalıcı bir hata satırı bırakıyor ve
    # damgasızken "hangi bounds/kod hâlinde reddedildi?" sorusu cevapsız kalıyordu.
    assert src.count('"kod_surumu": damga') == 3, "üç rapor çıkışının hepsi damgayı taşımalı"
    # damga, canlı state'e DEĞİL rapora yazılır (prescreen'in kendi yasası)
    assert "canli_state_degisen_dosyalar" in src


def test_D_saf_yaprak_sozlesmesi_KORUNDU():
    """Modül hiçbir meridian modülünü import etmez ve hiçbir dosyaya YAZMAZ. Tek beyanlı istisna
    `kod_surumu_damgasi`ın yalnız-okuma git çağrısıdır ve modül başlığında yazılıdır."""
    src = (SRC / "olcum_araclari.py").read_text()
    assert "from . import" not in src and "from .." not in src and "import meridian" not in src
    for yasak in ("write_json", "append_jsonl", "open("):
        assert yasak not in src, f"ölçüm yardımcısı yan etki taşıyor ({yasak})"
    assert "TEK BEYANLI İSTİSNA" in src and "YALNIZ-OKUMA" in src
    assert "write_text" not in src and "mkdir" not in src


# =================================================================================================
# E) CANLI-BEKLENTİ TAVANI — TEK KAYNAK ÇİVİSİ (kural v146'da bağlandı, bu tur DOKUNULMADI)
# =================================================================================================
def test_E_kural_config_sabitlerinde_ve_OKUYUCUSU_VAR():
    """WP-M "canlı-beklenti tavanı config'e" kalemi 2026-08-01'de KAPANDI. Bu tur onu yeniden
    yazmaz, YERİNDE olduğunu çivi ile doğrular: sabitler + okuyucu + karne satırı."""
    assert config.LIVE_EXPECTANCY_CAP_MULT == 0.5 and config.LIVE_SUSPEND_RATIO == 0.4
    k = config.live_expectancy_rule({})
    assert (k["cap_mult"], k["suspend_ratio"]) == (0.5, 0.4)
    assert set(k["kaynak"].values()) == {"kod varsayilani"}
    src = (SRC / "analytics.py").read_text()
    assert "config.live_expectancy_rule" in src          # YASA 6: sabitin OKUYUCUSU var
    assert '"tavan_durumu": live_expectancy_ceiling()' in src   # ve karne satırına bağlı


def test_E_kuralin_IKINCI_bir_ADI_dogmadi():
    """TEK DOĞRULUK KAYNAĞI. Aynı kurala ikinci bir ad (ör. `CANLI_BEKLENTI_TAVAN`) eklemek,
    ikinci bir doğruluk kaynağı yaratırdı: biri değişince öteki sessizce eski değerde kalır ve
    hangisinin yürürlükte olduğu ancak iki sabiti yan yana koyan biri tarafından görülür. Kural
    `LIVE_EXPECTANCY_CAP_MULT`/`LIVE_SUSPEND_RATIO` adlarıyla ZATEN yürürlükte."""
    for ikiz in ("CANLI_BEKLENTI_TAVAN", "CANLI_BEKLENTI_SUSPANSIYON"):
        assert not hasattr(config, ikiz), f"{ikiz} — aynı kuralın ikinci adı doğmuş"
    src = (SRC / "config.py").read_text()
    assert src.count("LIVE_EXPECTANCY_CAP_MULT = ") == 1
    assert src.count("LIVE_SUSPEND_RATIO = ") == 1


def test_E_tavan_HUKUM_VERMEZ_kapisi_duruyor():
    """v146'nın kapı kaydı: tavan bir KOLONDUR, ölçüt değil. Hüküm makinesine dokunmadığımızın
    kaynak-seviyesi çivisi (bu tur da dokunulmadı)."""
    for dosya in ("probgate.py", "reflect.py", "guard.py", "arming.py", "rollback.py"):
        yol = SRC / dosya
        if yol.exists():
            assert "live_expectancy_ceiling" not in yol.read_text(), \
                f"{dosya} tavan kolonunu okuyor — kolon ölçüte dönüşmüş"


# =================================================================================================
# F) STANDARTLAR DOSYASI — YAZILI OLMAYAN STANDART, STANDART DEĞİLDİR (YASA 6'nın doküman yüzü)
# =================================================================================================
def test_F_standartlar_dosyasi_yeni_dersleri_TASIR():
    d = (KOK / "docs" / "olcum_standartlari.md").read_text()
    for parca in ("Ders #5", "Ders #6", "Ders #7", "olay_disi_kiyas", "blok_bootstrap_ci",
                  "eb_kucult", "kod_surumu_damgasi", "min_taban", "sikisma",
                  "İLERİYE DÖNÜKLÜK ŞERHİ", "kazananın laneti"):
        assert parca in d, f"ölçüm standardı '{parca}' maddesini taşımıyor"
    # eski dört ders YERİNDE (yeni araçlar eskiyi süpürmedi)
    for parca in ("oosonly", "DİLBİLGİSİ", "TABAN-FAZLASI", "KIYAS TEMİZLİĞİ", "temiz_taban",
                  "kirlilik_orani", "Geriye dönük düzeltme YOK"):
        assert parca in d, f"eski ders '{parca}' kaybolmuş"


def test_F_olcum_sablonu_bolumu_PK4_PK5_ve_pozitif_kontrolu_zorunlu_kiliyor():
    d = (KOK / "docs" / "olcum_standartlari.md").read_text()
    for parca in ("Ölçüm şablonu — ZORUNLU ADIMLAR", "POZİTİF KONTROL", "PK4", "PK5",
                  "YOL TUTARLILIĞI", "ÖZDEŞLİKLER", "geriye-bakışsızlık",
                  "tek-enstrümanlı pozitif kontrol", "DURDURMA sebebidir"):
        assert parca in d, f"ölçüm şablonu '{parca}' adımını taşımıyor"


def test_F_ILERIYE_DONUKLUK_serhi_retro_hukmu_YASAKLIYOR():
    """MEVCUT kart hükümleri/eşikleri DEĞİŞMEZ — yeni araç geçmişi yeniden okumaz."""
    d = (KOK / "docs" / "olcum_standartlari.md").read_text()
    serh = d.split("İLERİYE DÖNÜKLÜK ŞERHİ")[1].split("\n---")[0]
    assert "geçersizleştirmez" in serh and "ön-kayıt kartı" in serh
    assert "research/cards/" in serh
