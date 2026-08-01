"""test_mutborc_score_kelly_fraction_v148.py — H5 TEST-BORCU: meridian/score.py::kelly_fraction.

Kümedeki 23 HAYATTA KALAN mutant için davranış testleri. Fonksiyonun sözleşmesi:

    rs   = r_multiple'ı OLAN işlemler                       (anahtarı olmayan işlem hiç sayılmaz)
    n<12 → None                                              (TAIL_MIN_SAMPLE — dürüst 'bilinmiyor')
    wins = r > 0   /  losses = r < 0                         (SIFIR ne kazanç ne kayıptır)
    W    = len(wins)/len(rs)
    R    = ort(kazanç) / |ort(kayıp)|                        (ORAN — çarpım değil)
    f    = W − (1−W)/R    ama R > 0 değilse f = −1.0         (sıfıra bölünmeyi kesen bekçi)
    çıktı: win_rate=3hne, win_loss_ratio=2hne, full_kelly=3hne, half_kelly=round(max(0,f/2),3), n

Her test TEK bir mutasyon SINIFINI hedefler; fikstürler sentetik (ne state'e ne dosyaya dokunur).

ÖLDÜRÜLEN SINIFLAR (mutant no → sınıf → öldüren test)
  15            r>0 → r>=0        (sıfır-R kazanç sayılıyor)        → test_sifir_r_kazanc_degildir
  18            r<0 → r<=0        (sıfır-R kayıp sayılıyor)         → test_sifir_r_kayip_degildir
  19            r<0 → r<1         (kayıp eşiği 0→1 kaydı)           → test_birin_altindaki_kazanc_kayip_degildir
  26            /  → *            (R oran değil çarpım oldu)        → test_r_orandir_carpim_degildir
  37            R>0 → R>=0        (sıfır-bölme bekçisi delindi)     → test_r_sifira_dustugunde_bekci_tutar
  38            R>0 → R>1         (bekçi eşiği 0→1 kaydı)           → test_r_birin_altindayken_gercek_f_hesaplanir
  39            else −1.0 → +1.0  (bekçi işaret çevirdi)            → test_r_sifira_dustugunde_bekci_tutar
  40            else −1.0 → −2.0  (bekçi sabiti büyüdü)             → test_r_sifira_dustugunde_bekci_tutar
  47            round(W,3)→4      (win_rate hassasiyeti)            → test_win_rate_uc_haneye_yuvarlanir
  51,52,53      round(R,2)→int    (win_loss_ratio tamsayıya düştü)  → test_win_loss_ratio_iki_haneye_yuvarlanir
  54            round(R,2)→3      (win_loss_ratio hassasiyeti)      → test_win_loss_ratio_iki_haneye_yuvarlanir
  61            round(f,3)→4      (full_kelly hassasiyeti)          → test_full_kelly_uc_haneye_yuvarlanir
  65,67         round(h,3)→int    (half_kelly tamsayıya düştü)      → test_half_kelly_uc_haneye_yuvarlanir
  74            f/2.0 → f/3.0     (YARIM-Kelly üçte-bir oldu)       → test_half_kelly_tam_kellynin_yarisidir
  75            round(h,3)→4      (half_kelly hassasiyeti)          → test_half_kelly_uc_haneye_yuvarlanir
  76            "n" → "XXnXX"     (anahtar adı bozuldu)             → test_cikti_anahtarlari_sozlesmesi
  77            "n" → "N"         (anahtar adı büyük harf)          → test_cikti_anahtarlari_sozlesmesi

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: test etmeye ÇALIŞILMADI, gerekçesi burada)
  4, 6, 9       t.get("r_multiple", 0.0) → sırasıyla None / (varsayılansız) / 1.0.
                Üç mutant da SADECE `.get` varsayılanını değiştirir; ama aynı satırdaki
                `if "r_multiple" in t` filtresi anahtarı OLMAYAN işlemi zaten eleyip attığı için
                varsayılan HİÇBİR ZAMAN okunmaz. Fonksiyon `list[dict]` alır (state JSON'undan
                gelen düz sözlükler), yani `in` ile `.get` arasında farklı davranan bir kap yok.
                Davranışı değiştiren girdi ÜRETİLEMEZ → eşdeğer, kapsam dışı bırakıldı.
"""
from __future__ import annotations

import pytest

from meridian.score import TAIL_MIN_SAMPLE, kelly_fraction


# ---------------------------------------------------------------- fikstürler (sentetik)

def _t(rs: list[float]) -> list[dict]:
    """r_multiple listesini işlem sözlüklerine çevirir — başka alan gerekmiyor."""
    return [{"r_multiple": r} for r in rs]


def _sifirli() -> list[dict]:
    """6 kazanç (+2R), 6 kayıp (−1R) ve TAM 1 adet 0.0R → n=13. Sıfır sınırının tek sondası.
    Gerçek kod: wins=6, losses=6, W=6/13=0.462, R=2.0/1.0=2.0"""
    return _t([2.0] * 6 + [-1.0] * 6 + [0.0])


def _kesirli_r() -> list[dict]:
    """6 kazanç (+4.25R), 6 kayıp (−2R) → n=12 (TAIL_MIN_SAMPLE sınırında).
    R = 4.25/2.0 = 2.125 → yuvarlama ve oran sınıflarının hepsini ayırt eder:
      * 2.125 tamsayı DEĞİL          → round(R) / round(2) mutantları yakalanır
      * 2. ve 3. hane FARKLI (2.12 ≠ 2.125) → hassasiyet mutantı yakalanır
      * |ort(kayıp)| = 2.0 ≠ 1.0     → bölme/çarpma ayrımı görünür olur"""
    return _t([4.25] * 6 + [-2.0] * 6)


def _r_birin_altinda() -> list[dict]:
    """Kazançlar 1R'nin ÜSTÜNDE ama kayıplar daha büyük: R = 1.5/3.0 = 0.5 (0 < R < 1)."""
    return _t([1.5] * 6 + [-3.0] * 6)


def _r_sifira_dusen() -> list[dict]:
    """R'nin gerçekten 0.0 olabildiği TEK yol: ort(kazanç) denormal, ort(kayıp) devasa →
    bölüm float'ta alttan taşar. wins hep >0 olduğundan R matematiksel olarak asla 0 değildir;
    0.0'a DÜŞMESİ float'ın gerçeğidir ve `R > 0` bekçisi tam olarak bunun içindir."""
    return _t([5e-324] * 6 + [-1e300] * 6)


# ---------------------------------------------------------------- sıfır-R sınırı (15, 18, 19)

def test_sifir_r_kazanc_degildir():
    """0.0R BAŞA BAŞ çıkıştır; kazanç sayılırsa hem W hem ortalama kazanç yalan söyler.
    ÖLDÜRÜR 15 (r>0 → r>=0): kazanç sayısı 6→7 olur, win_rate 0.462→0.538'e sıçrar."""
    d = kelly_fraction(_sifirli())
    assert d is not None
    assert d["n"] == 13                      # sıfırlı işlem örnekleme SAYILIR (paydadadır)
    assert d["win_rate"] == 0.462            # 6/13 — sıfır PAYDA'da, PAY'da değil
    assert d["full_kelly"] == 0.192


def test_sifir_r_kayip_degildir():
    """Aynı sıfır kayıp sayılırsa ortalama kayıp yapay olarak KÜÇÜLÜR ve R şişer — Kelly tavanı
    hak etmediği kadar cömert olur. ÖLDÜRÜR 18 (r<0 → r<=0) ve 19 (r<0 → r<1): ikisinde de
    kayıp sayısı 6→7, |ort kayıp| 1.0→0.857 ve win_loss_ratio 2.0→2.33 olur."""
    d = kelly_fraction(_sifirli())
    assert d is not None
    assert d["win_loss_ratio"] == 2.0        # (12/6) / |−6/6| = 2.0 — sıfır iki kümenin de dışında


def test_birin_altindaki_kazanc_kayip_degildir():
    """Kayıp eşiği 0 iken +0.5R bir KAZANÇTIR; eşik 1'e kayarsa aynı işlem hem kazanç hem kayıp
    kümesine girer ve R tersine döner. ÖLDÜRÜR 19 (r<0 → r<1): losses 12 elemana çıkar,
    |ort kayıp| 1.0→0.25 düşer, win_loss_ratio 0.5→2.0 olur (edge YOKken VAR gösterir)."""
    d = kelly_fraction(_t([0.5] * 6 + [-1.0] * 6))
    assert d is not None
    assert d["win_rate"] == 0.5
    assert d["win_loss_ratio"] == 0.5        # 0.5 / 1.0 — kazançlar kayıp kümesine SIZMAZ
    assert d["full_kelly"] == -0.5           # negatif f* = "bu edge mevcut boyutu haklı çıkarmaz"


# ---------------------------------------------------------------- R'nin kendisi (26)

def test_r_orandir_carpim_degildir():
    """R = ort(kazanç) / |ort(kayıp)|. Çarpıma dönerse |ort kayıp| = 1.0 olan fikstürlerde fark
    GÖRÜNMEZ; bu yüzden fikstür bilerek |ort kayıp| = 2.0 seçildi.
    ÖLDÜRÜR 26 (/ → *): 4.25/2.0 = 2.125 yerine 4.25*2.0 = 8.5 raporlanır."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    assert d["win_loss_ratio"] == 2.12       # 4.25/2.0; çarpım olsaydı 8.5
    assert d["full_kelly"] == 0.265          # 0.5 − 0.5/2.125


# ---------------------------------------------------------------- sıfıra-bölme bekçisi (37, 38, 39, 40)

def test_r_sifira_dustugunde_bekci_tutar():
    """`R > 0` bekçisi hem sıfıra bölünmeyi keser hem de "edge yok" hükmünü −1.0 olarak yazar.
    ÖLDÜRÜR 37 (R>0 → R>=0): R = 0.0 iken (1−W)/R ZeroDivisionError fırlatır, fonksiyon çöker.
    ÖLDÜRÜR 39 (−1.0 → +1.0): ölçülemeyen edge TAM Kelly gibi görünür — tehlikeli yön.
    ÖLDÜRÜR 40 (−1.0 → −2.0): sabit büyür."""
    d = kelly_fraction(_r_sifira_dusen())    # mutant 37'de bu satır ZeroDivisionError ile patlar
    assert d is not None
    assert d["win_loss_ratio"] == 0.0        # R gerçekten 0.0'a düştü (fikstür sözleşmesi)
    assert d["full_kelly"] == -1.0           # bekçinin sabiti: işaret ve büyüklük AYNEN
    assert d["half_kelly"] == 0.0            # max(0.0, −0.5) → negatif tavan sıfırlanır


def test_r_birin_altindayken_gercek_f_hesaplanir():
    """0 < R ≤ 1 aralığı bekçinin DIŞINDADIR: f formülle hesaplanır, sabite düşmez.
    ÖLDÜRÜR 38 (R>0 → R>1): R = 0.5 iken gerçek f = −0.5 yerine sabit −1.0 yazılır — kayıp
    yapan bir stratejinin ne KADAR kaybettiği bilgisi silinir."""
    d = kelly_fraction(_r_birin_altinda())
    assert d is not None
    assert d["win_loss_ratio"] == 0.5
    assert d["full_kelly"] == -0.5           # 0.5 − 0.5/0.5 = −0.5; sabit −1.0 DEĞİL
    assert d["half_kelly"] == 0.0


# ---------------------------------------------------------------- yuvarlama sözleşmesi (47, 51-54, 61, 65, 67, 75)

def test_win_rate_uc_haneye_yuvarlanir():
    """win_rate 3 haneye yuvarlanır. Fikstür n=13 seçildi: 6/13 = 0.461538… → 3 hane 0.462,
    4 hane 0.4615 — iki hassasiyet AYRILABİLİR. ÖLDÜRÜR 47 (round(W,3) → round(W,4))."""
    d = kelly_fraction(_sifirli())
    assert d is not None
    assert d["win_rate"] == 0.462
    assert d["win_rate"] != round(6 / 13, 4)


def test_win_loss_ratio_iki_haneye_yuvarlanir():
    """win_loss_ratio 2 haneye yuvarlanır ve FLOAT kalır.
    ÖLDÜRÜR 54 (2 → 3 hane): 2.125 raporlanır.
    ÖLDÜRÜR 51 (round(R,None)) ve 53 (round(R)): tamsayı 2 raporlanır.
    ÖLDÜRÜR 52 (round(2)): R'den bağımsız sabit 2 raporlanır."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    assert d["win_loss_ratio"] == 2.12       # 2.125 ne olduğu gibi ne de tamsayıya kırpılarak
    assert isinstance(d["win_loss_ratio"], float)
    assert d["win_loss_ratio"] != 2.125


def test_full_kelly_uc_haneye_yuvarlanir():
    """full_kelly 3 haneye yuvarlanır: f = 0.5 − 0.5/2.125 = 0.2647058… → 0.265 (4 hane 0.2647).
    ÖLDÜRÜR 61 (round(f,3) → round(f,4))."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    assert d["full_kelly"] == 0.265
    assert d["full_kelly"] != 0.2647


def test_half_kelly_uc_haneye_yuvarlanir():
    """half_kelly 3 haneye yuvarlanır ve FLOAT kalır: 0.2647058…/2 = 0.1323529… → 0.132.
    ÖLDÜRÜR 75 (3 → 4 hane): 0.1324 raporlanır.
    ÖLDÜRÜR 65 (round(h,None)) ve 67 (round(h)): tamsayı 0 raporlanır — tavan SIFIRLANIR,
    yani 'boyut alma' der; sessizce yanlış yönde bir hüküm."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    assert d["half_kelly"] == 0.132
    assert isinstance(d["half_kelly"], float)
    assert d["half_kelly"] != 0.1324


def test_half_kelly_tam_kellynin_yarisidir():
    """half_kelly adı YARIM-Kelly'dir: f/2. Payda 3 olursa çıkan sayı hâlâ 'makul' göründüğü için
    gözle yakalanmaz — bu yüzden oran açıkça sınanır.
    ÖLDÜRÜR 74 (f/2.0 → f/3.0): 0.132 yerine 0.088 raporlanır."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    # tolerans 1e-3: iki alan da AYRI AYRI 3 haneye yuvarlandığı için yarıya bölme ile yuvarlama
    # sırası bir birim oynayabilir (0.265/2 = 0.1325 → 0.132). Mutant 74'ün farkı ~0.044, kat kat üstü.
    assert d["half_kelly"] == pytest.approx(d["full_kelly"] / 2.0, abs=1e-3)
    assert d["half_kelly"] == 0.132
    assert d["half_kelly"] != 0.088


# ---------------------------------------------------------------- çıktı sözleşmesi (76, 77)

def test_cikti_anahtarlari_sozlesmesi():
    """Anahtar adları çağıranın (reflect/pano) okuduğu SÖZLEŞMEDİR; 'n' yerine 'N' ya da 'XXnXX'
    yazılırsa okuyucu sessizce None/eksik görür — örneklem sayısı kaybolur.
    ÖLDÜRÜR 76 ("n" → "XXnXX") ve 77 ("n" → "N")."""
    d = kelly_fraction(_kesirli_r())
    assert d is not None
    assert set(d) == {"win_rate", "win_loss_ratio", "full_kelly", "half_kelly", "n"}
    assert d["n"] == 12
    assert isinstance(d["n"], int)


# ---------------------------------------------------------------- örneklem tabanı (regresyon bekçisi)

def test_tail_min_sample_sinirinda_bilinmeyen_none_kalir():
    """TAIL_MIN_SAMPLE altında dürüst 'bilinmiyor' = None (0.0 ya da uydurma dict DEĞİL).
    Sınır TAM eşitlikte açılır. (Bu sınıfın mutantları zaten ölü; sözleşme regresyon bekçisi.)"""
    assert TAIL_MIN_SAMPLE == 12
    az = _t([2.0] * 6 + [-1.0] * (TAIL_MIN_SAMPLE - 7))          # n = 11
    assert len(az) == TAIL_MIN_SAMPLE - 1
    assert kelly_fraction(az) is None
    tam = _t([2.0] * 6 + [-1.0] * 6)                             # n = 12
    assert kelly_fraction(tam) is not None
    assert kelly_fraction([]) is None


def test_tek_yonlu_seri_none_doner():
    """Hiç kayıp (ya da hiç kazanç) yokken R tanımsızdır — fonksiyon uydurmaz, None döner.
    (Sözleşme bekçisi: bu dal olmadan R sıfıra bölme ya da inf üretirdi.)"""
    assert kelly_fraction(_t([1.0] * 12)) is None
    assert kelly_fraction(_t([-1.0] * 12)) is None
    assert kelly_fraction(_t([0.0] * 12)) is None                # sıfırlar iki kümede de yok
