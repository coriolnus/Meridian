"""test_mutborc_score_tail_risk_v148.py — H5 TEST-BORCU: `meridian/score.py::tail_risk`.

NEDEN: mutasyon taraması bu fonksiyonda 39 HAYATTA KALAN mutant buldu. En utandırıcı bulgu şuydu:
mutant 42 (`sum(axis=1)` → `sum(axis=None)`) ayakta kaldı — DOĞRULAYICI DÜZELTMESİ (2026-08-01,
ölçüldü): bu mutant TypeError ile PATLAMIYOR, SESSİZCE yanlış skaler döndürüyor (−400000.0 ≠ −20.0);
yani daha da kötüsü. Sonuç değişmez: mevcut suite'te `tail_risk`i TAIL_MIN_SAMPLE üstünde bir örneklem
ile çağıran TEK BİR test bile yoktu — kuyruk vetosu (reflect.TAIL_MARGIN_R) ölçülmemiş bir sayının
üstünde duruyordu. Bu dosya o borcu kapatır.

HEDEFLENEN MUTASYON SINIFLARI (34 mutant):
  * varsayılan argüman sabitleri — 1 (horizon 20→21), 3 (seed 7→8)
  * eşik yönü/sınırı        — 20 (`rs.size < TAIL_MIN_SAMPLE` → `<=`)
  * blok bootstrap yapısı   — 28 (block min(5,·)→min(6,·)), 39 (start+arange → start-arange),
                              42 (sum(axis=1) → sum(axis=None) — yol başına değil TÜM matris)
  * kuantil sabiti          — 58 ((1-alpha)*100.0 → *101.0)
  * kuyruk sınırı eşitliği  — 60 (`paths <= q` → `paths < q`)
  * yuvarlama → int'e çökme — 63, 64, 65, 70, 72, 90, 91, 92, 99, 100, 101
                              (round(x, None) / round(3) / round(x, ) hepsi int döndürür)
  * yuvarlama basamağı      — 67, 75, 95, 103 (3 → 4 ondalık)
  * işaret                  — 94 (`-paths.min()` → `+paths.min()`: kayıp büyüklüğü negatife döner)
  * sözleşme anahtarları    — 76, 77 (horizon), 78, 79 (alpha), 80, 81 (n), 87, 88 (worst_r),
                              96, 97 (mean_r) — "XXanahtarXX" / "ANAHTAR" varyantları

EŞDEĞER — ÖLDÜRÜLEMEZ (5 mutant, YASA 4 ruhu: neden kaydedilir, sessizce atlanmaz):
  * 6  `np.array(..., dtype=float)` → `dtype=None`
  * 8  `np.array(..., dtype=float)` → argüman tamamen düşürülmüş
       GEREKÇE: liste kavrayışı her elemanı `float(...)` ile ürettiği için girdi HER ZAMAN Python
       float'tır; np.array bu listeden dtype çıkarımıyla da float64 üretir. Boş listede bile
       `np.array([])` float64'tür. Gözlemlenebilir davranış farkı YOK.
  * 11 `t.get("r_multiple", 0.0)` → `t.get("r_multiple", None)`
  * 13 varsayılan tamamen düşürülmüş (`t.get("r_multiple", )`)
  * 16 `t.get("r_multiple", 0.0)` → `t.get("r_multiple", 1.0)`
       GEREKÇE: kavrayışın filtresi `if "r_multiple" in t` — anahtar YOKSA eleman zaten hiç
       üretilmez, yani `.get`in VARSAYILANI ERİŞİLEBİLİR DEĞİLDİR (ölü argüman). Varsayılanı
       değiştirmek çıktıyı değiştiremez. Bunu öldürmek için testin değil KODUN değişmesi gerekir
       (filtre ile varsayılan aynı anda tutulmamalı) — test-borcu turunun kapsamı dışında.
"""
from __future__ import annotations

import numpy as np
import pytest

from meridian import score as sc


# ---- fikstürler (sentetik, tmp-state yok: tail_risk saf fonksiyondur) ---------------------------

def _trades(rs: list[float]) -> list[dict]:
    return [{"r_multiple": float(x)} for x in rs]


# 24 işlem, 5 ondalıklı R değerleri. ONDALIK SAYISI KASITLI: yuvarlama basamağı mutantlarını
# (3 → 4 ondalık) ancak 4. ondalığı SIFIRDAN FARKLI olan bir çıktı yakalayabilir; 2 ondalıklı
# R'lerle yol toplamları da 2 ondalıklı çıkıyor ve round(x,3) == round(x,4) oluyordu.
KARISIK_R = [-1.03721, -0.98407, 2.41539, -1.00812, 0.73264, -0.99175, 3.10486, -1.02093,
             -0.97658, 1.88342, -0.41027, -1.01364, 0.35719, -0.96285, -1.04938, 2.75613,
             -1.00246, 1.14872, -0.93551, -0.86094, 4.19238, -1.02777, 0.61483, -0.99619]

# Kuantil TAM BİR VERİ NOKTASINA otursun diye AYRIK fikstür (bkz. sınır eşitliği testi).
# n=25, horizon=2 → blok=2: yol = ardışık iki R'nin toplamı; yalnız 3 farklı değer üretir.
AYRIK_R = [-5.0, -5.0] + [0.0] * 23

R_ALANLARI = ("var_r", "cvar_r", "worst_r", "mean_r")


# ---- referans (oracle) uygulaması ---------------------------------------------------------------

def _referans(rs_list, horizon=20, sims=500, alpha=0.95, seed=7):
    """tail_risk'in SÖZLEŞMESİNİ bağımsız (döngüsel, vektörsüz) yazımla yeniden üretir.

    Sözleşme: blok = min(5, horizon); blok sayısı = ceil(horizon/blok); her blok DÖNGÜSEL ve
    İLERİ yönde (start, start+1, ... mod n); yol = ilk `horizon` elemanın TOPLAMI; q = (1-alpha)
    yüzdelik dilimi (yüzde cinsinden ×100); kuyruk = q'ya EŞİT VE ALTINDAKİ yollar; tüm çıktılar
    3 ondalığa yuvarlanır ve kayıplar POZİTİF büyüklük olarak raporlanır.

    Yalnızca RNG akışı ortaktır (aynı tohum → aynı çekiliş); geri kalanı elle kurulur. Toplama
    sırası numpy'ninkinden farklı olduğu için son bit düzeyinde ~1e-15 sapma mümkündür; 3 ondalık
    yuvarlamadan sonra bu sapmanın görünür olma olasılığı ihmal edilebilir (ölçüldü: eşleşiyor).
    """
    rs = [float(x) for x in rs_list]
    n = len(rs)
    block = min(5, horizon)
    n_blocks = -(-horizon // block)
    u = np.random.default_rng(seed).random((sims, n_blocks))
    paths = []
    for s in range(sims):
        seq = []
        for b in range(n_blocks):
            start = int(u[s, b] * n)
            for k in range(block):
                seq.append(rs[(start + k) % n])
        paths.append(sum(seq[:horizon]))
    arr = np.array(paths, dtype=float)
    q = float(np.percentile(arr, (1.0 - alpha) * 100.0))
    tail = [p for p in paths if p <= q]
    return {"horizon": horizon, "alpha": alpha, "n": n,
            "var_r": round(-q, 3),
            "cvar_r": round(-(sum(tail) / len(tail)), 3) if tail else round(-q, 3),
            "worst_r": round(-min(paths), 3), "mean_r": round(sum(paths) / len(paths), 3)}


# ---- 1) örneklem eşiği: TAM SINIRDA tanımlı, ALTINDA None --------------------------------------

def test_h5_esik_tam_sinirda_tanimlidir():
    """`<` mutasyonu (`<=`) tam sınırdaki örneklemi 'bilinmiyor' ilan ederdi — kuyruk vetosu
    12 işlemlik ilk dürüst ölçümünü sessizce kaybederdi. Hedef: mutant 20."""
    tam = sc.tail_risk(_trades([-1.0] * sc.TAIL_MIN_SAMPLE))
    assert tam is not None, "TAIL_MIN_SAMPLE TAM sayıda işlemde sonuç ÜRETİLMELİ"
    assert tam["n"] == sc.TAIL_MIN_SAMPLE


def test_h5_esik_altinda_none_doner():
    """Eşiğin altı 0.0 değil None: ölçülemeyen kuyruk 'risksiz' görünmemeli (UYDURMA YASAĞI)."""
    assert sc.tail_risk(_trades([-1.0] * (sc.TAIL_MIN_SAMPLE - 1))) is None
    assert sc.tail_risk([]) is None
    assert sc.tail_risk(_trades([-1.0] * 30)[:3]) is None


def test_h5_r_multiple_alani_olmayan_islem_sayilmaz():
    """n, R'si OLAN işlemlerin sayısıdır; alansız kayıt 0.0 diye içeri sızmaz."""
    karisik = _trades([-1.0] * sc.TAIL_MIN_SAMPLE) + [{"pnl_dollars": -250.0}] * 5
    out = sc.tail_risk(karisik)
    assert out is not None and out["n"] == sc.TAIL_MIN_SAMPLE
    # eşiğin ALTINA düşüren de aynı sayımdır
    assert sc.tail_risk(_trades([-1.0] * (sc.TAIL_MIN_SAMPLE - 1))
                        + [{"pnl_dollars": -250.0}] * 9) is None


# ---- 2) varsayılan argüman sabitleri ------------------------------------------------------------

def test_h5_varsayilan_ufuk_20_islemdir():
    """Sabit R=-1 ile her yol TAM `horizon` işlemin toplamıdır: ufuk 20 ise mean_r = -20.0.
    Ufuk varsayılanı 21'e kayarsa sayı -21.0 olur. Aynı fikstür `sum(axis=1)` sözleşmesini de
    kilitler: yol başına toplam alınmazsa fonksiyon çağrı anında patlar.
    Hedef: mutant 1, mutant 42."""
    d = sc.tail_risk(_trades([-1.0] * sc.TAIL_MIN_SAMPLE))
    assert d["horizon"] == 20
    assert d["mean_r"] == -20.0 and d["var_r"] == 20.0 and d["worst_r"] == 20.0
    # ufuk gerçekten ölçeklendiriyor mu — 7 işlemlik pencerede yol toplamı -7.0
    d7 = sc.tail_risk(_trades([-1.0] * sc.TAIL_MIN_SAMPLE), horizon=7)
    assert d7["horizon"] == 7 and d7["mean_r"] == -7.0 and d7["var_r"] == 7.0


def test_h5_varsayilan_tohum_7_ve_belirlenimcidir():
    """Kapı iki tarafı KIYASLIYOR: varsayılan tohum kayarsa incumbent ile aday farklı çekilişte
    ölçülür. Varsayılan çağrı seed=7 ile BİREBİR aynı, seed=8 ile FARKLI olmalı.
    Hedef: mutant 3."""
    t = _trades(KARISIK_R)
    varsayilan = sc.tail_risk(t)
    assert varsayilan == sc.tail_risk(t, seed=7), "varsayılan tohum 7 DEĞİL"
    assert varsayilan != sc.tail_risk(t, seed=8), "tohum çıktıyı hiç etkilemiyor — fikstür kör"
    assert varsayilan == sc.tail_risk(t), "aynı girdi aynı sayıyı vermiyor (belirlenimci değil)"


# ---- 3) dönüş sözleşmesi: anahtar kümesi ve tipler ----------------------------------------------

def test_h5_donus_anahtarlari_tam_kume():
    """Anahtar adları SÖZLEŞMEdir: reflect/karne bu adlarla okuyor. Bir harf değişirse okuyucu
    sessizce KeyError yer ya da alanı 'yok' sayar. Hedef: mutant 76, 77, 78, 79, 80, 81, 87, 88,
    96, 97."""
    d = sc.tail_risk(_trades(KARISIK_R))
    assert set(d) == {"horizon", "alpha", "n", "var_r", "cvar_r", "worst_r", "mean_r"}
    assert d["alpha"] == 0.95 and d["n"] == len(KARISIK_R)


def test_h5_r_alanlari_float_tipinde_kalir():
    """`round(x, None)` / `round(x, )` / `round(3)` hepsi INT döndürür — JSON'a 5 diye yazılan
    bir VaR, 5.071'lik bir kuyruğu 'tam sayı' gibi gösterir ve marj kıyası bozulur.
    Hedef: mutant 63, 64, 65, 70, 72, 90, 91, 92, 99, 100, 101."""
    d = sc.tail_risk(_trades(KARISIK_R), sims=500)
    for k in R_ALANLARI:
        assert isinstance(d[k], float), f"{k} float değil: {type(d[k]).__name__}={d[k]!r}"
        assert not isinstance(d[k], int), f"{k} int'e çökmüş: {d[k]!r}"
    # 'round(3)' varyantı alanı sabit 3'e çivilerdi; fikstür kasten 3'ten uzak sayılar üretir
    for k in R_ALANLARI:
        assert d[k] != 3, f"{k} sabit 3 — yuvarlama argümanı değere dönüşmüş"


def test_h5_yuvarlama_uc_ondaliktir():
    """Sözleşme 3 ondalık. 4 ondalığa kayarsa değer 3 ondalığa yuvarlanmış haline EŞİT OLMAZ
    (fikstür 4. ondalığı sıfırdan farklı olacak şekilde seçildi). Hedef: mutant 67, 75, 95, 103."""
    d = sc.tail_risk(_trades(KARISIK_R), sims=500)
    for k in R_ALANLARI:
        assert d[k] == round(d[k], 3), f"{k} 3 ondalıktan fazla taşıyor: {d[k]!r}"


# ---- 4) işaret sözleşmesi: kayıplar POZİTİF büyüklük --------------------------------------------

def test_h5_worst_r_pozitif_kayip_buyuklugudur():
    """worst_r = -min(paths): en kötü yolun kayıp BÜYÜKLÜĞÜ. İşaret düşerse en kötü senaryo
    negatif bir sayı olarak raporlanır ve 'worst_r < TAIL_MARGIN_R' kıyası HER ZAMAN geçer —
    veto ölür. Hedef: mutant 94 (ve sabit-3 varyantı 91)."""
    d = sc.tail_risk(_trades(KARISIK_R), sims=500)
    assert d["worst_r"] > 0.0, "en kötü yol pozitif kayıp büyüklüğü olarak raporlanmalı"
    assert d["worst_r"] >= d["var_r"] >= 0.0, "en kötü yol VaR'dan sığ olamaz"
    assert d["worst_r"] >= d["cvar_r"], "en kötü yol CVaR'dan sığ olamaz"
    # mean_r ise İŞARETLİdir (kayıp büyüklüğü değil): kazançlı seride pozitif kalmalı
    assert d["mean_r"] > 0.0


# ---- 5) kuyruk sınırı: kuantile EŞİT yollar kuyruğun İÇİNDEdir ----------------------------------

def test_h5_kuantile_esit_yollar_kuyruga_dahildir():
    """`paths <= q` → `paths < q`. Sürekli veride fark görünmez; ayrık fikstürde q TAM bir veri
    noktasına oturur ve fark keskinleşir: VaR seviyesindeki senaryolar dışlanırsa CVaR yalnız en
    dip kovayı ortalar ve kuyruğu ABARTIR (10.0 vs ~6.6). Hedef: mutant 60."""
    d = sc.tail_risk(_trades(AYRIK_R), horizon=2)
    assert d["var_r"] == 5.0 and d["worst_r"] == 10.0     # fikstür beklendiği gibi ayrık
    assert d["var_r"] < d["cvar_r"] < d["worst_r"], (
        f"CVaR kuyruğun TAMAMINI ortalamıyor: {d}")
    assert d["cvar_r"] == pytest.approx(6.648, abs=0.001)


def test_h5_cvar_var_dan_sig_olamaz():
    """Beklenen açık (CVaR) tanımı gereği VaR'dan derindir; ihlali kuyruk aritmetiğinin bozulduğunu
    söyler."""
    for h in (5, 20, 40):
        d = sc.tail_risk(_trades(KARISIK_R), horizon=h, sims=500)
        assert d["cvar_r"] >= d["var_r"], f"horizon={h}: {d}"


def test_h5_alpha_derinlestikce_var_artar():
    """alpha kuantilin derinliğidir: 0.99 kuyruğu 0.90'dan daha derin bir kayıp vermeli."""
    t = _trades(KARISIK_R)
    sig = sc.tail_risk(t, alpha=0.90, sims=2000)
    derin = sc.tail_risk(t, alpha=0.99, sims=2000)
    assert derin["var_r"] > sig["var_r"] and derin["cvar_r"] > sig["cvar_r"]
    assert sig["alpha"] == 0.90 and derin["alpha"] == 0.99


# ---- 6) referans uygulaması ile BİREBİR sayı kilidi ---------------------------------------------

def test_h5_referans_uygulamasiyla_birebir_ayni():
    """Blok bootstrap'in YAPISI (blok boyu 5, İLERİ yönde döngüsel blok, (1-alpha)×100 kuantili)
    tek tek davranış testiyle yakalanamayacak kadar sayısaldır; bu yüzden bağımsız bir referans
    uygulamasıyla TAM eşitlik aranır. Blok 6'ya kayarsa, blok geriye sarılırsa ya da kuantil
    101'le çarpılırsa dört sayının hepsi kayar. Hedef: mutant 28, 39, 58 (+ 42 ve tüm yuvarlama
    sınıfları)."""
    gercek = sc.tail_risk(_trades(KARISIK_R), sims=500)
    assert gercek == _referans(KARISIK_R, sims=500)


def test_h5_referans_kisa_ufukta_da_ayni():
    """horizon < blok kenarı: blok = min(5, horizon) kısalmalı, ceil bölmesi 1 blok vermeli."""
    for h in (3, 5, 13):
        assert sc.tail_risk(_trades(KARISIK_R), horizon=h, sims=400) == \
            _referans(KARISIK_R, horizon=h, sims=400)


def test_h5_referans_farkli_tohum_ve_alpha_ile_de_ayni():
    """Referans yalnız tek bir çekilişte değil, tohum/alpha değişince de tutmalı — yoksa test
    tek bir rastlantıyı kilitlemiş olur."""
    assert sc.tail_risk(_trades(KARISIK_R), sims=600, seed=99) == \
        _referans(KARISIK_R, sims=600, seed=99)
    assert sc.tail_risk(_trades(KARISIK_R), sims=600, alpha=0.9) == \
        _referans(KARISIK_R, sims=600, alpha=0.9)


# ---- 7) blok bootstrap gerçekten BAĞIMLILIK koruyor mu ------------------------------------------

def test_h5_blok_bootstrap_seri_kumelenmeyi_korur():
    """Kuyruk kapısının VAR OLMA sebebi: kayıplar KÜMELENİR. Kayıpları bitişik bir seride
    toplayan seri (blok bootstrap onları BİRLİKTE çeker), aynı kayıpları serpiştiren seriden
    DAHA DERİN bir kuyruk vermeli. IID örnekleme bu farkı sıfırlar."""
    kumelenmis = [-2.0] * 6 + [1.0] * 18                      # kayıplar bitişik
    serpistirilmis = ([-2.0] + [1.0] * 3) * 6                  # aynı çokluk, dağıtılmış
    assert sorted(kumelenmis) == sorted(serpistirilmis)        # aynı marjinal dağılım
    a = sc.tail_risk(_trades(kumelenmis), sims=4000)
    b = sc.tail_risk(_trades(serpistirilmis), sims=4000)
    assert a["cvar_r"] > b["cvar_r"], f"kümelenme kuyruğu derinleştirmiyor: {a} vs {b}"
