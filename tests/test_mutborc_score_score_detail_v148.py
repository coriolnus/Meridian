"""test_mutborc_score_score_detail_v148.py — H5 TEST-BORCU: `meridian/score.py::score_detail`
mutasyon kümesi (120 hayatta kalan mutant, mutmut çalışması 2026-08-01).

NEDEN VAR: score_detail kapının okuduğu TEK sayıyı üretir. Mevcut testler (özellikle
`test_score_audit_v40.py`) sözleşmeyi YÖN olarak sınıyordu — "geniş pencere daha düşük getiri
verir", "M2M drawdown'ı kötüleştirir". Yön testleri sabit/kat sayı/yuvarlama mutasyonlarını
GÖRMEZ: `0.3 * dd_c` yerine `0.3 * dd_c` ile `2.0 - dd/max_dd` aynı yönü verir, farklı sayıyı.
Bu dosya SAYIYI çivileyerek o sınıfı kapatır: fikstürler sentetiktir, beklenen değerler
elle türetilmiştir (aşağıdaki F1 türetimine bakınız), ve her iddia round() basamağına kadar
kesindir.

KAPSAM HARİTASI (mutant no → test):
  4,6,9            min_sample varsayılanı/int()            → test_m01
  14,15,16,17      yetersiz-örnek sözlüğü anahtarları      → test_m02
  167,168,190,191,197,198,200,201,208,209,217,218,224,225,231,232,244,245
                   tam sözlük + components + targets anahtarları → test_m03
  29,30,39,40,42,44,45,66,70,71,77,81,82,85,86,87,90,98,103,104,106,123,129,
  133,134,135,139,140,141,145,148,152,164,175,182,189,193,194,195,196,199,
  203,204,205,207,220,221,222,223,227,228,229,230,234,235,236,237
                   aritmetik + yuvarlama + sabit           → test_m04 (F1 çivisi)
  24               equity_curve'e start_equity geçilmesi   → test_m05
  36,89            span_days == 1 sınırı                   → test_m06
  112              max(trades_per_year, 1) tabanı          → test_m07
  91,97,114        varyans 0 → "ölçülemedi"                → test_m08
  93,100           n == 3 sınırı                           → test_m09
  101              n <= 2 → else False                     → test_m10
  67,69,72         eksik r_multiple → 0.0                  → test_m11
  78,80,83         eksik pnl_dollars → 0.0                 → test_m12
  130,136,142      dejenere hedef (0) → bileşen 0.0        → test_m13
  48,49,50         total_return <= -1 tabanı               → test_m14
  155,156,211,212,213,214   win_rate sınırı ve yuvarlaması → test_m15
  157              n == 0 → win_rate 0.0                   → test_m16

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: sessizce atlanmadı, gerekçesiyle kayda geçti).
Aşağıdaki 9 mutant gözlemlenebilir davranışı DEĞİŞTİRMEZ; onlar için test yazmak, testi
uygulamanın kopyasına çevirmekten başka bir şey yapmaz:
  35   `span_days >= 0`  — `span_days and span_days > 0` ifadesinde 0 zaten YANLIŞ (falsy) olduğu
       için kısa devre yapar; `>=` ile `>`nin ayrıştığı TEK nokta span_days == 0'dır ve oraya
       hiç varılmaz. Negatifler her iki halde de else dalına düşer.
  46   `total_return >= -1` — ayrışma noktası total_return == -1. Orada mutant
       (1.0 + -1.0) ** (30/span) - 1.0 = 0.0 ** pozitif - 1.0 = -1.0 hesaplar; gerçek kod da
       -1.0 döndürür. Sayı AYNI.
  62   `dtype=None` ve
  64   `np.array([...], )` — liste elemanları `float(...)` ile üretildiği için çıkarsanan dtype
       zaten float64'tür; `r` yalnız `r.mean()` ve `(r > 0).mean()` için kullanılır. Sonuç aynı.
  74   `pnl / start_equity` → `pnl * start_equity` — per_trade_ret YALNIZ `mean()/std(ddof=1)`
       oranında ve `std > 0` yoklamasında kullanılır; ikisi de ölçek değişmezidir (sabit c ile
       çarpım hem payı hem paydayı çarpar). Ayrışma ancak start_equity == 0 iken olurdu, ama o
       durumda fonksiyon daha ÖNCE `curve[-1] / curve[0]` satırında ZeroDivisionError atar.
  88   `span >= 0` — span ya float(span_days) > 0'dır ya da _span_days() çıktısıdır; _span_days
       en kötü halde max(1.0, ...) ya da 30.0 döndürür. span == 0 erişilemez.
  92   `n >= 2 and ...` — ifade zaten `... if n > 2 else False` koşulunun DOĞRU dalındadır;
       orada n > 2 olduğundan `n >= 2` ile `n > 2` ikisi de True. Sonuç `std > 0`.
  96   `std(ddof=2) > 0` (yalnız ölçülebilirlik yoklamasında) — sqrt(SS/(n-ddof)) yalnızca
       SS == 0 iken sıfırdır; ddof payda seçimi işareti değil ölçeği değiştirir, yani
       `> 0` boole'si her iki ddof için AYNI. (Formüldeki ddof=2 farklı bir mutant: 106, öldü.)
  99   `if n >= 2 else False` — n == 2'de mutant DOĞRU dala girer ve orada `n > 2 and ...`
       = False üretir; gerçek kod da else dalından False verir. Aynı değer.
"""
from __future__ import annotations

import math
import warnings

import pytest

from meridian import score as sc


# =================================================================================================
# F1 — ANA ÇİVİ FİKSTÜRÜ
# =================================================================================================
# Sentetik, elle türetilebilir olsun diye seçildi (başlangıç sermayesi 100_000, span 53 gün):
#   pnl            : +2137, -983, +3041, -1777        → toplam +2418
#   equity eğrisi  : 100000 → 102137 → 101154 → 104195 → 102418
#   total_return   : 102418/100000 - 1        = 0.02418            → round4 0.0242
#   realized_30d   : 1.02418 ** (30/53) - 1   = 0.0136158012…      → round4 0.0136
#   max_drawdown   : (104195-102418)/104195   = 0.0170545612…      → round4 0.0171
#   per_trade_ret  : 0.02137, -0.00983, 0.03041, -0.01777
#     ortalama = 0.001045, std(ddof=1) = 0.0207985…
#   trades_per_year: 4 / (53/365) = 27.5471…, sqrt = 5.24853…
#   sharpe         : 0.001045/0.0207985 * 5.24853 = 1.3538145…     → round3 1.354
#   bileşenler     : ret = 0.0136158/0.02 = 0.6807900…             → round3 0.681
#                    dd  = 1 - 0.0170546/0.10 = 0.8294543…         → round3 0.829
#                    sh  = 1.3538145/(1.0*2)  = 0.6769072…         → round3 0.677
#   composite      : 0.5*0.68079 + 0.3*0.8294544 + 0.2*0.6769072 = 0.7246128 → round4 0.7246
# Her ara değerin 5. ondalığı SIFIR DEĞİL: bu bilinçli — round(x,4)/round(x,5) (ve 3/4) farkı
# ancak böyle görünür, yuvarlama-basamağı mutasyonları aksi halde hayatta kalır.
GOAL = {"min_sample": 4, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}
SPAN = 53.0

F1 = [
    {"pnl_dollars": 2137.0, "r_multiple": 2.1234, "ts_open": "2026-01-02", "ts_close": "2026-01-05"},
    {"pnl_dollars": -983.0, "r_multiple": -1.0, "ts_open": "2026-01-09", "ts_close": "2026-01-12"},
    {"pnl_dollars": 3041.0, "r_multiple": 1.5, "ts_open": "2026-02-03", "ts_close": "2026-02-06"},
    {"pnl_dollars": -1777.0, "r_multiple": -0.9, "ts_open": "2026-03-11", "ts_close": "2026-03-14"},
]

TAM_ANAHTARLAR = {
    "score", "n", "min_sample", "total_return", "realized_30d", "max_drawdown",
    "sharpe", "sharpe_measurable", "avg_r", "win_rate", "components", "targets",
}


def _islemler(n: int, pnl: float = 500.0, r: float = 0.5, gun: int = 3) -> list[dict]:
    import datetime as dt
    d0 = dt.date(2026, 1, 1)
    return [{"pnl_dollars": pnl, "r_multiple": r,
             "ts_open": str(d0 + dt.timedelta(days=i * gun)),
             "ts_close": str(d0 + dt.timedelta(days=i * gun + 1))} for i in range(n)]


# =================================================================================================
# test_m01 — min_sample varsayılanı goal ile eşittir ve tamsayıya çevrilir   (mutant 4, 6, 9)
# =================================================================================================
def test_m01_min_sample_varsayilani_goal_ile_esittir():
    """goal içinde min_sample YOKSA eşik, goal.yaml'daki gerçek değerle EŞİT yedekten gelir
    (envanter #16, 2026-08-22: yedek 20 iken goal 30'du — anahtar düşerse modül sessizce daha
    GEVŞEK bir tabana dönüyordu; v239 test_8a tüm yedekleri goal'a çiviler). Mutasyon koruması
    aynen durur: varsayılan kalkarsa (`get("min_sample")` → None) `int(None)` patlar; bir
    yukarı kayarsa eşik-tam-dolu küme sessizce 'ölçülemedi'ye düşer — yani kapı, elinde
    yeterli örnek varken adayı reddeder."""
    goal = {"target_return_30d": 0.03, "max_drawdown": 0.12, "min_sharpe": 1.0}  # min_sample YOK

    d30 = sc.score_detail(_islemler(30), goal, span_days=60.0)
    assert d30["min_sample"] == 30
    assert d30["score"] is not None, "30 işlem varsayılan eşiği KARŞILAR (n < min_sample değil)"

    d29 = sc.score_detail(_islemler(29), goal, span_days=60.0)
    assert d29["min_sample"] == 30 and d29["score"] is None


# =================================================================================================
# test_m02 — yetersiz örnek sözlüğünün anahtarları sabittir            (mutant 14, 15, 16, 17)
# =================================================================================================
def test_m02_yetersiz_ornek_sozlugu_anahtarlari():
    """Eşik altı dönüşü tüketiciler alan ADIYLA okur (`n`, `min_sample`). Ad değişirse KeyError
    değil, sessiz bir `.get()` None'ı doğar — 'kaç işlem vardı' sorusu cevapsız kalır."""
    d = sc.score_detail(_islemler(3), GOAL)
    assert set(d) == {"score", "n", "min_sample", "reason"}
    assert d["score"] is None and d["n"] == 3 and d["min_sample"] == 4
    assert d["reason"] == "3/4 closed trades — score undefined (None, not 0.0)"


# =================================================================================================
# test_m03 — tam sözlüğün anahtar kümeleri sabittir
#            (mutant 167,168,190,191,197,198,200,201,208,209,217,218,224,225,231,232,244,245)
# =================================================================================================
def test_m03_tam_sozluk_anahtar_kumeleri():
    """Karne/pano/kapı bu sözlüğü ADLA tüketir. Bir anahtarın büyük harfe kayması ya da
    'XX...XX' olması testleri kırmadan alanı GÖRÜNMEZ yapar; tüketici None okur ve
    'ölçülmedi' ile 'yanlış adlandırıldı' ayırt edilemez."""
    d = sc.score_detail(F1, GOAL, span_days=SPAN)
    assert set(d) == TAM_ANAHTARLAR
    assert set(d["components"]) == {"ret", "dd", "sharpe"}
    assert set(d["targets"]) == {"target_return_30d", "max_drawdown", "min_sharpe"}


# =================================================================================================
# test_m04 — F1 çivisi: her sayı ve her yuvarlama basamağı
# =================================================================================================
def test_m04_f1_tum_alanlar_civilendi():
    """Dosya başındaki türetimin sayısal karşılığı. Tek bir sabit, işaret, üs ya da yuvarlama
    basamağı kayarsa BURASI düşer — 'yön doğru, miktar yanlış' sınıfının kapısı budur."""
    d = sc.score_detail(F1, GOAL, span_days=SPAN)

    assert d["n"] == 4 and d["min_sample"] == 4
    assert d["total_return"] == 0.0242          # ham 0.02418  → 5 basamak 0.02418 (≠ 4 basamak)
    assert d["realized_30d"] == 0.0136          # ham 0.0136158012…
    assert d["max_drawdown"] == 0.0171          # ham 0.0170545612…
    assert d["sharpe"] == 1.354                 # ham 1.3538145…
    assert d["sharpe_measurable"] is True
    assert d["avg_r"] == 0.431                  # ham 0.43085
    assert d["win_rate"] == 0.5                 # 4 işlemin 2'si r > 0
    assert d["components"] == {"ret": 0.681, "dd": 0.829, "sharpe": 0.677}
    assert d["targets"] == {"target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}
    assert d["score"] == 0.7246                 # ham 0.7246128…
    assert sc.score(F1, GOAL) is not None       # sarmalayıcı aynı sözlükten okur

    # Yuvarlama basamağı GERÇEKTEN ayırt edici mi? (test kendi keskinliğini ölçüyor)
    assert round(0.0136158012, 5) != d["realized_30d"]
    assert round(1.3538145, 4) != d["sharpe"]
    assert round(0.43085, 4) != d["avg_r"]
    assert round(0.6807900, 4) != d["components"]["ret"]


# =================================================================================================
# test_m05 — start_equity gerçekten equity_curve'e geçer               (mutant 24)
# =================================================================================================
def test_m05_start_equity_equity_curve_e_gecirilir():
    """Argüman düşerse eğri sessizce 100_000 varsayılanına döner: 50_000'lik bir hesabın %4.84
    getirisi %2.42 diye raporlanır. Aynı fonksiyonla ölçülen iki taraf farklı sermayedeyse
    kıyas da bozulur."""
    d = sc.score_detail(F1, GOAL, start_equity=50_000.0, span_days=SPAN)
    assert d["total_return"] == 0.0484           # 2418/50000 = 0.04836 → round4
    assert d["max_drawdown"] == 0.0328           # 1777/54195 = 0.032789…

    varsayilan = sc.score_detail(F1, GOAL, span_days=SPAN)
    assert d["total_return"] != varsayilan["total_return"]


# =================================================================================================
# test_m06 — span_days == 1 GEÇERLİ bir penceredir                     (mutant 36, 89)
# =================================================================================================
def test_m06_span_days_bir_gun_gecerli_penceredir():
    """Sınır eşitliği: `span_days > 0` koşulu `> 1`e kayarsa 1 günlük pencere sessizce
    kümenin KENDİ aralığına (burada 179 gün) düşer ve yıllıklandırma 179 kat sapar. Aynı
    şekilde `span > 0` → `span > 1` olursa trades_per_year 365 kat küçülür."""
    islemler = [
        {"pnl_dollars": 400.0, "r_multiple": 0.5, "ts_open": "2026-01-05", "ts_close": "2026-01-06"},
        {"pnl_dollars": -250.0, "r_multiple": -1.0, "ts_open": "2026-02-05", "ts_close": "2026-02-06"},
        {"pnl_dollars": 900.0, "r_multiple": 1.2, "ts_open": "2026-04-05", "ts_close": "2026-04-06"},
        {"pnl_dollars": -175.0, "r_multiple": -0.4, "ts_open": "2026-07-01", "ts_close": "2026-07-03"},
    ]
    assert sc._span_days(islemler) == 179.0, "fikstür kendi aralığında 1 gün DEĞİL"

    d = sc.score_detail(islemler, GOAL, span_days=1.0)
    assert d["total_return"] == 0.0088                 # 875/100000 = 0.00875
    assert d["realized_30d"] == 0.2987                 # 1.00875 ** 30 - 1 = 0.29866…
    assert d["sharpe"] == 15.506                       # trades_per_year = 4*365 = 1460

    kendi_araligi = sc.score_detail(islemler, GOAL)     # span_days YOK → 179 gün
    assert kendi_araligi["realized_30d"] != d["realized_30d"]
    assert kendi_araligi["sharpe"] != d["sharpe"]


# =================================================================================================
# test_m07 — sqrt(max(trades_per_year, 1)) tabanı 1'dir                (mutant 112)
# =================================================================================================
def test_m07_yillik_islem_sayisi_tabani_birdir():
    """20 işlem / 20 yıl → trades_per_year = 1.0; taban 1 olduğu için ölçek çarpanı sqrt(1)=1'dir.
    Taban 2'ye kayarsa SEYREK bir strateji, hiç kazanmadığı sqrt(2) = 1.41 katlık bir Sharpe
    primi alır — tam da örneklem kuraklığında kapıyı gevşeten yön."""
    islemler = [{"pnl_dollars": (150.0 if i % 3 else -220.0), "r_multiple": (0.7 if i % 3 else -1.0),
                 "ts_open": "2026-01-01", "ts_close": "2026-01-02"} for i in range(20)]
    goal = {"min_sample": 20, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}

    d = sc.score_detail(islemler, goal, span_days=7300.0)     # 7300/365 = 20 yıl → tpy = 1.0
    assert d["sharpe"] == 0.113, "ham 0.11322…  = mean/std * sqrt(1); taban 2 olsaydı 0.160"
    assert d["sharpe"] != round(0.11322002309478849 * math.sqrt(2.0), 3)

    # Aynı veri 2 yıla sıkışırsa tpy = 10 olur ve çarpan sqrt(10)'a çıkar — taban ARTIK
    # devrede değildir, yani ölçek çarpanının gerçekten trades_per_year'dan geldiğini gösterir.
    yogun = sc.score_detail(islemler, goal, span_days=730.0)
    assert yogun["sharpe"] == 0.358                            # ham 0.3580331…


# =================================================================================================
# test_m08 — varyans 0 ise Sharpe ÖLÇÜLEMEDİ (0.0 + bayrak False)      (mutant 91, 97, 114)
# =================================================================================================
def test_m08_varyans_sifirsa_sharpe_olculemedi():
    """Tüm işlemler AYNI getiriyi verirse std = 0 ve Sharpe tanımsızdır. Sözleşme: sayı
    muhafazakâr tarafta 0.0 kalır ama `sharpe_measurable` False der. `and` → `or` ya da
    `std > 0` → `std >= 0` bu ayrımı yok eder ve 0/0 = nan'ı 'ölçüldü' diye sunar; else
    dalındaki 0.0 → 1.0 ise ölçülemeyen Sharpe'ı min_sharpe'ın tam yarısı gibi gösterir.

    Sermaye 131072 = 2**17 ve pnl 512 = 2**9 SEÇİLDİ: oran 2**-8 ikilik tabanda TAM temsil
    edilir, dolayısıyla std kayan nokta artığı bırakmadan TAM sıfır olur."""
    islemler = [{"pnl_dollars": 512.0, "r_multiple": 1.0,
                 "ts_open": "2026-01-01", "ts_close": "2026-01-02"} for _ in range(32)]
    goal = {"min_sample": 20, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}

    d = sc.score_detail(islemler, goal, start_equity=131072.0, span_days=90.0)
    assert d["n"] == 32
    assert d["sharpe_measurable"] is False, "sabit getiride varyans yok — Sharpe ÖLÇÜLEMEZ"
    assert d["sharpe"] == 0.0, "ölçülemeyen Sharpe muhafazakâr 0.0'dır, 1.0 değil"
    assert d["components"]["sharpe"] == 0.0


# =================================================================================================
# test_m09 — n == 3 Sharpe için YETERLİDİR                             (mutant 93, 100)
# =================================================================================================
def test_m09_uc_islem_sharpe_icin_yeterlidir():
    """Sınır eşitliği: koşul `n > 2`dir. `n > 3`e kayarsa tam 3 işlemli bir küme sessizce
    'ölçülemedi' olur; ddof=1 varyansı 3 gözlemde pekâlâ tanımlıdır (payda 2)."""
    goal = {"min_sample": 3, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}
    d = sc.score_detail(F1[:3], goal, span_days=SPAN)
    assert d["n"] == 3
    assert d["sharpe_measurable"] is True
    assert d["sharpe"] != 0.0


# =================================================================================================
# test_m10 — n <= 2 Sharpe için YETERSİZDİR                            (mutant 101)
# =================================================================================================
def test_m10_iki_islem_sharpe_icin_yetersizdir():
    """Diğer sınır: 2 gözlemde ddof=1 varyansı hesaplanabilir ama ANLAMSIZDIR; sözleşme
    else dalında False der. False → True olursa iki işlemlik bir küme yıllıklandırılmış bir
    Sharpe üretir ve kapı onu 'ölçülmüş' sayar."""
    goal = {"min_sample": 2, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}
    d = sc.score_detail(F1[:2], goal, span_days=SPAN)
    assert d["n"] == 2
    assert d["sharpe_measurable"] is False
    assert d["sharpe"] == 0.0 and d["components"]["sharpe"] == 0.0


# =================================================================================================
# test_m11 — eksik r_multiple 0.0 sayılır                              (mutant 67, 69, 72)
# =================================================================================================
def test_m11_eksik_r_multiple_sifir_sayilir():
    """Defterde r_multiple'ı olmayan bir kayıt SKORU DÜŞÜRMEZ ama UYDURMAZ da: nötr 0.0.
    Varsayılan kalkarsa `float(None)` patlar (skor hesabı çöker); 1.0 olursa eksik veri
    sessizce 'kazanan işlem' gibi ortalamaya girer."""
    islemler = [dict(t) for t in F1]
    del islemler[1]["r_multiple"]                       # -1.0 yerine anahtar YOK

    d = sc.score_detail(islemler, GOAL, span_days=SPAN)
    assert d["avg_r"] == 0.681                          # (2.1234 + 0.0 + 1.5 - 0.9)/4 = 0.68085
    assert d["win_rate"] == 0.5                         # 0.0 KAZANAN SAYILMAZ (r > 0)
    assert d["avg_r"] != sc.score_detail(F1, GOAL, span_days=SPAN)["avg_r"]


# =================================================================================================
# test_m12 — eksik pnl_dollars 0.0 sayılır                             (mutant 78, 80, 83)
# =================================================================================================
def test_m12_eksik_pnl_dollars_sifir_sayilir():
    """Aynı hüküm getiri tarafında. Fikstür bilerek 'düz': dört işlem 0 P&L, biri anahtarsız.
    Gerçek kodda per_trade_ret'in TAMAMI sıfırdır → varyans yok → Sharpe ölçülemez. Eksik
    anahtar 1.0 sayılırsa yoktan bir varyans doğar ve 'ölçüldü' bayrağı yanlışlıkla kalkar."""
    islemler = [{"pnl_dollars": 0.0, "r_multiple": 0.5,
                 "ts_open": "2026-01-01", "ts_close": "2026-01-02"} for _ in range(4)]
    islemler.append({"r_multiple": 0.5, "ts_open": "2026-01-03", "ts_close": "2026-01-04"})
    goal = {"min_sample": 5, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}

    d = sc.score_detail(islemler, goal, span_days=90.0)
    assert d["n"] == 5
    assert d["total_return"] == 0.0
    assert d["sharpe_measurable"] is False, "hepsi 0 P&L → varyans yok; eksik anahtar 1.0 DEĞİL"
    assert d["sharpe"] == 0.0


# =================================================================================================
# test_m13 — dejenere hedef (0) bileşeni 0.0 yapar                     (mutant 130, 136, 142)
# =================================================================================================
@pytest.mark.parametrize("hedef_alan,bilesen", [
    ("target_return_30d", "ret"),
    ("max_drawdown", "dd"),
    ("min_sharpe", "sharpe"),
])
def test_m13_sifir_hedef_bileseni_sifirlar(hedef_alan, bilesen):
    """Hedef 0 ise oran tanımsızdır. Sözleşme: bileşen 0.0 — yani NÖTR. 1.0 olursa tanımsız
    bir hedef, o bileşenin TAM PUANI gibi okunur ve kapı yapılandırma hatasını ödüllendirir."""
    goal = dict(GOAL, **{hedef_alan: 0.0})
    d = sc.score_detail(F1, goal, span_days=SPAN)
    assert d["components"][bilesen] == 0.0
    assert d["targets"][hedef_alan] == 0.0
    assert d["components"][bilesen] != sc.score_detail(F1, GOAL, span_days=SPAN)["components"][bilesen]


def test_m13b_min_sharpe_hedefi_dogru_okunur():
    """(mutant 123) `min_sharpe = None` olsaydı hem targets yalan söylerdi hem de Sharpe
    bileşeni sessizce 0'a düşerdi — 'hedef yok' ile 'hedef tutmadı' aynı görünürdü."""
    d = sc.score_detail(F1, GOAL, span_days=SPAN)
    assert d["targets"]["min_sharpe"] == 1.0
    assert d["components"]["sharpe"] == 0.677


# =================================================================================================
# test_m14 — sermayeyi aşan kayıpta realized_30d TABANI -1.0'dır       (mutant 48, 49, 50)
# =================================================================================================
def test_m14_sermayeden_buyuk_kayipta_realized_taban():
    """total_return <= -1 (hesap eksiye geçti) iken (1 + tr) negatiftir ve kesirli üs KARMAŞIK
    sayı verir. Sözleşme: bu dalda -1.0 sabitlenir. Eşik -2'ye kayarsa round() bir karmaşık
    sayıyla patlar; sabit +1.0 olursa TAM İFLAS eden bir strateji %100 kâr raporlar."""
    islemler = [{"pnl_dollars": -60000.0, "r_multiple": -2.0,
                 "ts_open": "2026-01-01", "ts_close": f"2026-01-0{i + 2}"} for i in range(3)]
    goal = {"min_sample": 3, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}

    d = sc.score_detail(islemler, goal, span_days=90.0)
    assert d["total_return"] == -1.8, "eğri -80_000'e indi: 100000 - 180000"
    assert d["realized_30d"] == -1.0, "taban -1.0; -2.0 ya da +1.0 değil"
    assert d["components"]["ret"] == -1.0
    assert d["score"] == -0.8


# =================================================================================================
# test_m15 — win_rate sınırı KESİN pozitiftir                          (mutant 155,156,211-214)
# =================================================================================================
def test_m15_win_rate_kesin_pozitif_r_sayar():
    """r == 0 (başabaş) KAZANAN DEĞİLDİR; 0 < r <= 1 ise kazanandır. `>=` sınırı başabaşları
    kazanç yazar, `> 1` ise 1R altındaki tüm kazançları siler. 7 işlem SEÇİLDİ: 3/7 = 0.428571…
    — 3 ve 4 basamaklı yuvarlama ancak böyle ayrışır (0.429 ≠ 0.4286)."""
    ciftler = [(100.0, 0.0), (250.0, 0.5), (900.0, 2.0), (-300.0, -1.0),
               (-120.0, -0.5), (380.0, 0.75), (-640.0, -2.0)]
    islemler = [{"pnl_dollars": p, "r_multiple": r, "ts_open": "2026-01-01", "ts_close": "2026-03-01"}
                for p, r in ciftler]
    goal = {"min_sample": 7, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}

    d = sc.score_detail(islemler, goal, span_days=90.0)
    assert d["n"] == 7
    assert d["win_rate"] == 0.429                        # 3/7 = 0.4285714…  (>= olsaydı 4/7)
    assert d["win_rate"] != round(3 / 7, 4)              # yuvarlama basamağı 3, 4 değil
    assert d["avg_r"] == -0.036                          # (-0.25)/7 = -0.0357142…


# =================================================================================================
# test_m16 — hiç işlem yokken win_rate 0.0'dır                         (mutant 157)
# =================================================================================================
def test_m16_islem_yokken_win_rate_sifirdir():
    """min_sample 0 ise boş küme eşik kapısından GEÇER (0 < 0 yanlış). O dalda win_rate
    tanımsızdır; sözleşme 0.0 der. 1.0 olsaydı hiç işlem yapmamış bir strateji %100 isabet
    raporlardı — 'ölçülemedi'nin en tehlikeli 'iyi görünen' hâli.

    numpy boş dilim uyarısı (avg_r = nan) bilinçli olarak bastırıldı: burada ölçtüğümüz alan
    avg_r değil win_rate; uyarıyı hataya çevirmek testi konusundan uzaklaştırırdı."""
    goal = {"min_sample": 0, "target_return_30d": 0.02, "max_drawdown": 0.10, "min_sharpe": 1.0}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        d = sc.score_detail([], goal)
    assert d["n"] == 0
    assert d["win_rate"] == 0.0
    assert d["sharpe_measurable"] is False
