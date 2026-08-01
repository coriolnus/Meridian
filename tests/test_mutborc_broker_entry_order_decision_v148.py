"""test_mutborc_broker_entry_order_decision_v148.py — H5 TEST-BORCU kümesi:
`meridian/broker.py::entry_order_decision` (E1 giriş-icra yasasının 3. maddesi).

NİYE VAR: mutasyon koşusu bu fonksiyonda 72 HAYATTA KALAN mutant bıraktı. Yani fonksiyonun
çıktı sözleşmesi — hangi dalın seçildiği, hangi alanın hangi adla ve hangi hassasiyetle yazıldığı,
ölçülemeyenin nasıl BEYAN edildiği — testlerce bağlanmamıştı. Bu dosya davranış testleriyle o
sözleşmeyi bağlar. Çıktı bir DEFTER SATIRIDIR: alan adları (`offset_kaynak`, `ref_kaynak`)
ölçüm-dürüstlüğü beyanıdır; sessizce yeniden adlandırılırsa geriye dönük okuyucular "ölçüldü"
sanır. Bu yüzden anahtar kümesi ve string hükümleri harfi harfine sınanır.

FİKSTÜR: saf/sentetik. Fonksiyon zaten saf (ağ yok, saat yok, defter yok) — tmp-state gerekmez.
`_CFG` LİTERAL bir sözlük: testler `state/goal.yaml`e BAĞLI DEĞİL (yapılandırma değişince testin
hükmü kaymasın). Tek istisna `test_m18` — orada cfg'nin gerçekten okunduğunu kanıtlamak için
yasanın yürürlükteki değerinden farklı olduğu AÇIKÇA doğrulanır.

--------------------------------------------------------------------------------------------------
HEDEFLENEN HAYATTA-KALAN MUTANTLAR (72/72) — sınıf → numara
--------------------------------------------------------------------------------------------------
  A. Anahtar adı bozma ("XXalanXX" / "ALAN")   : 48 49 62 63 71 72 91 92 99 100 109 110 117 118
                                                 121 122                                  → m1
  B. `t = float(trigger or 0.0)` sabiti        : 6                                         → m2 m3
  C. cfg'nin limit hesabına geçirilmemesi      : 10 13                                     → m18
  D. Bozuk referansın except dalı (`rp = ""`)  : 17                                        → m10
  E. ATR ölçüm dalı (float(None)/is None/1.0)  : 19 20 21                                  → m7 m8
  F. Bozuk ATR'nin except dalı (None / 1.0)    : 22 23                                     → m9
  G. Gap sınırı `t > 0` (>=0 / >1)             : 28 29                                     → m3 m4
  H. Yuvarlama hassasiyeti (None / 5 / arg-düş): 51 52 53 54 61 65 66 67 68 94 95 96 97
                                                 124 125 126 132                           → m5 m6 m7 m16
  I. `atr` alanının a>0 kapısı (>=0 / >1)      : 69 70                                     → m8 m11
  J. offset_kaynak dal mantığı (and→or, sınır,
     * → /, < → <=)                            : 75 76 77 78 81 82 87 88                   → m8 m11 m12 m13 m14
  K. offset_kaynak string hükümleri            : 73 74 85 86 89 90                         → m8 m11 m12
  L. ref_kaynak dalı + string hükümleri        : 101 102 103 104 105                       → m15
  M. limit_bps aritmetiği (/10000, +1.0, *t,
     -2.0, *10001)                             : 127 128 129 130 131                       → m16 m17
  N. limit_bps `t > 0` kapısı (>=0 / >1)       : 133 134                                   → m2 m4

EŞDEĞER (ÖLDÜRÜLEMEZ) İLAN EDİLEN: **YOK — 0 mutant**. 72'sinin tamamı için gerçek kodda yeşil,
mutant gövdesinde kırmızı düşen bir girdi bulundu ve her biri mutant modülü (`mutants/meridian/
broker.py`) doğrudan çağrılarak DOĞRULANDI (yalnız akıl yürütmeyle iddia edilmedi). Yakın-eşdeğer
görünüp ÖZEL girdiyle öldürülenler, gerekçeleri kayda geçsin diye:
  * 51/53 (`round(t, None)` ve `round(t, )`): tam sayı tetikte davranış AYNI — ancak kesirli
    tetikte (100.123456) int'e yuvarlar; testin girdisi bilerek kesirlidir.
  * 78 (`mult * a` → `mult / a`): a = 1.0'da iki ifade özdeş — bu yüzden test a = 0.5 kullanır.
  * 81 (`<` → `<=`): yalnız TAM EŞİTLİKTE ayrışır → t=100, ATR=2.0 (0.5·2.0 == 100·0.01, ikisi de
    kayan noktada tam 1.0; doğrulandı) sınır noktası özellikle seçildi.
  * 131 (`*10000` → `*10001`): %1'lik varsayılan tavanda fark 2 haneli yuvarlamanın altında kalır
    (18.25 == 18.25). Ayrışma ancak daha geniş tavanda görünür → m17 %5 tavan kullanır (500.0 vs
    500.05). Bu, "varsayılan noktada ölçemedim" değil, "ayrıştıran noktayı kullandım" hükmüdür.
"""
from __future__ import annotations

import pytest

from meridian import broker as b


# Yasanın varsayılan noktası, LİTERAL (goal.yaml'den bağımsız): min(0.5·ATR14, %1.0), gap → limit emri.
_CFG = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01,
        "gap_behavior": b.GAP_MARKETABLE, "tif": "day", "version": "TEST-E1"}

# Aynı yasa, YALNIZ yüzde tavanı %5: cfg'nin gerçekten okunduğunu ve bps çarpanının tam 10000
# olduğunu ayrıştıran nokta.
_CFG_GENIS = dict(_CFG, limit_pct_cap=0.05)

# Deftere yazılan alanların TAMAMI. Bu küme sözleşmedir: bir alan eklenir/adı değişirse okuyucular
# (E2 slipaj defteri, ayna gönderimi, analytics) sessizce None okumaya başlar — test önce kırılsın.
_ALANLAR = {"mode", "olay", "trigger", "limit", "atr", "offset_kaynak", "ref_price",
            "ref_kaynak", "gap_at_submit", "gap_behavior", "tif", "law", "limit_bps"}


def _karar(trigger, ref_price=None, atr=None, cfg=None):
    return b.entry_order_decision(trigger, ref_price, atr, cfg=cfg or _CFG)


# ---------- A: alan adları harfi harfine (defter şeması) ----------
def test_m1_anahtar_sozlesmesi_harfi_harfine():
    """Sınıf A (16 mutant): anahtar adının bozulması sessiz bir veri kaybıdır — satır yazılır,
    okuyucu alanı bulamaz, "ölçülemedi" sanır. Ad kümesi TAM olarak sınanır."""
    d = _karar(100.0, 98.0, 1.0)
    assert set(d.keys()) == _ALANLAR
    # Büyük/küçük harf ve XX-sarmalama varyantları ayrıca yakalansın:
    for ad in _ALANLAR:
        assert ad in d and ad.upper() not in d and f"XX{ad}XX" not in d


# ---------- B + N: tetik 0 ----------
def test_m2_tetik_sifir_ise_sifir_kalir_ve_bps_olculemez():
    """Sınıf B/N: `float(trigger or 0.0)` sabiti 1.0'a kayarsa 0 tetik sessizce 1 dolarlık bir
    kuruluma dönüşür. Ayrıca bps kapısı `t > 0` gevşerse 0'a bölme patlar — kapı `> 0` kalmalı."""
    d = _karar(0.0)
    assert d["trigger"] == 0.0
    assert d["limit"] == 0.0
    assert d["limit_bps"] is None          # ölçülemez; 0.0 yazmak "slipaj yoktu" demek olurdu


def test_m3_tetik_sifir_ama_referans_varsa_gap_YOK():
    """Sınıf B/G: gap koşulundaki `t > 0` kapısı `>= 0`a gevşerse tetiksiz bir satır gap dalına
    düşer ve buy-stop teyidi kaybolur. t=0'da gap YOKTUR."""
    d = _karar(0.0, 50.0)
    assert d["gap_at_submit"] is False
    assert d["mode"] == "stop_limit" and d["olay"] == b.EV_STOP_LIMIT
    assert d["trigger"] == 0.0


# ---------- G + N: 0 < t <= 1 bandı ----------
def test_m4_bir_dolar_altinda_tetik_de_tam_yasaya_tabi():
    """Sınıf G/N: `t > 0` kapısı `t > 1`e kayarsa kuruş hisseleri hem gap teyidini hem bps
    ölçümünü sessizce kaybeder. 0.5'lik tetik de tam yasaya tabidir."""
    d = _karar(0.5, 0.8)
    assert d["gap_at_submit"] is True
    assert d["mode"] == "marketable_limit" and d["olay"] == b.EV_GAP_MARKETABLE
    assert d["limit_bps"] == pytest.approx(100.0)      # %1 tavan = 100 bps


# ---------- H: yuvarlama hassasiyeti ----------
def test_m5_tetik_ve_limit_dort_haneye_yuvarlanir():
    """Sınıf H: 4 hane fiyat hassasiyetidir (kuruş-altı). None/5/argümansız varyantlar ya tam
    sayıya çöker ya fazladan hane yazar — ikisi de defterin fiyat sözleşmesini bozar."""
    d = _karar(100.123456)
    assert d["trigger"] == 100.1235                    # round(...,5) → 100.12346; round(...) → 100
    assert d["limit"] == 101.1247                      # round(...,5) → 101.12469


def test_m6_referans_fiyat_dort_haneye_yuvarlanir():
    d = _karar(100.0, 98.765432)
    assert d["ref_price"] == 98.7654                   # 5 hane → 98.76543; int → 99; sabit → 4


def test_m7_atr_dort_haneye_yuvarlanir_ve_gercekten_okunur():
    """Sınıf E/H: ATR verilmişse alana O DEĞER yazılır. `float(None)`/`is None` varyantları a'yı
    0.0'a çökertir ve alan sessizce None olur — "ATR yoktu" yalanı."""
    d = _karar(100.0, 98.0, 2.345678)
    assert d["atr"] == 2.3457                          # 5 hane → 2.34568; int → 2; sabit → 4
    assert d["atr"] is not None


# ---------- E/I/J/K: ATR ölçülemedi dalı ----------
def test_m8_atr_olculemezse_alan_None_ve_kaynak_BEYANLI():
    """Sınıf E/I/J/K: ATR yoksa (a == 0.0) üç şey aynı anda doğru olmalı:
      * `atr` alanı None — 0.0 yazmak "ATR sıfırdı" demek olurdu (uydurma yasağı),
      * `offset_kaynak` "pct_cap(atr_olculemedi)" — ölçülemediğini DIŞARI söyler,
      * limit yalnız yüzde tavanıyla bağlanır.
    `a >= 0` / `and`→`or` varyantları bu beyanı sessizce "atr" ya da "pct_cap"e çevirir."""
    d = _karar(100.0, 90.0, None)
    assert d["atr"] is None
    assert d["offset_kaynak"] == "pct_cap(atr_olculemedi)"
    assert d["limit"] == 101.0


def test_m9_bicimsiz_atr_da_olculemedi_sayilir_patlamaz():
    """Sınıf F: except dalındaki `a = 0.0` sabiti None'a kayarsa `a > 0` karşılaştırması TypeError
    atar (satır hiç yazılmaz); 1.0'a kayarsa uydurma bir ATR ölçülmüş gibi rapor edilir."""
    d = _karar(100.0, 90.0, "bicimsiz")
    assert d["atr"] is None
    assert d["offset_kaynak"] == "pct_cap(atr_olculemedi)"


# ---------- D: bozuk referans ----------
def test_m10_bicimsiz_referans_olculemedi_sayilir_ve_gap_dalina_duser():
    """Sınıf D: except dalındaki `rp = None` boş dizgeye kayarsa `rp >= t` TypeError atar. Yasanın
    bilinçli hükmü: ölçülemeyen referans GAP dalına düşer (teyit yok ama ödenen fiyat aynı)."""
    d = _karar(100.0, "bicimsiz")
    assert d["ref_price"] is None
    assert d["ref_kaynak"] == "olculemedi"
    assert d["gap_at_submit"] is True
    assert d["mode"] == "marketable_limit"


# ---------- I/J/K: hangi tavan bağladı? ----------
def test_m11_atr_daha_sikiysa_kaynak_ATR():
    """Sınıf I/J/K: 0.5·0.5 = 0.25 < 100·0.01 = 1.0 → ATR bağlar. `mult / a` varyantı burada
    1.0 üretir (a=1.0 seçilseydi iki ifade ÖZDEŞ olurdu — bu yüzden a=0.5), `a > 1` varyantı ATR'yi
    hem alandan hem kaynaktan düşürür."""
    d = _karar(100.0, 98.0, 0.5)
    assert d["offset_kaynak"] == "atr"
    assert d["atr"] == 0.5                             # `a > 1` kapısı bunu None yapardı
    assert d["limit"] == 100.25


def test_m12_yuzde_tavani_daha_sikiysa_kaynak_PCT_CAP():
    """Sınıf J/K: 0.5·4.0 = 2.0 > 1.0 → yüzde tavanı bağlar. `t / pct_cap` varyantı sağ tarafı
    10000'e şişirir ve her ATR'yi "bağladı" gibi gösterir."""
    d = _karar(100.0, 98.0, 4.0)
    assert d["offset_kaynak"] == "pct_cap"
    assert d["limit"] == 101.0                         # tavan yine %1
    assert d["atr"] == 4.0                             # ölçüldü — yalnız bağlamadı


def test_m13_tam_esitlikte_yuzde_tavani_baglar_atr_DEGIL():
    """Sınıf J: sınır noktası. 0.5·2.0 == 100.0·0.01 (kayan noktada tam eşit). `<` `<=`ye
    gevşerse eşitlik "atr bağladı" diye rapor edilir — E2 defteri hangi tavanın bağladığını
    yanlış öğrenir."""
    d = _karar(100.0, 98.0, 2.0)
    assert d["offset_kaynak"] == "pct_cap"


def test_m14_kucuk_tetikte_atr_gevsek_ama_OLCULDU():
    """Sınıf J: 0.5·1.0 = 0.5 > 10·0.01 = 0.1 → tavan yüzde. ATR gevşek kaldı ama ÖLÇÜLDÜ:
    kaynak "pct_cap" olmalı, "pct_cap(atr_olculemedi)" DEĞİL (`a > 1` varyantının yaptığı)."""
    d = _karar(10.0, 9.0, 1.0)
    assert d["offset_kaynak"] == "pct_cap"
    assert d["atr"] == 1.0


# ---------- L: ref_kaynak iki yönlü ----------
def test_m15_ref_kaynak_iki_yonlu_ve_harfi_harfine():
    """Sınıf L: `rp is None` ↔ `rp is not None` ters çevrilirse defter "ölçüldü"yü "ölçülemedi"
    diye yazar — sayaçlar ters döner. İki yön de sabitlenir."""
    olculemedi = _karar(100.0, None)
    olculdu = _karar(100.0, 98.0)
    assert olculemedi["ref_kaynak"] == "olculemedi"
    assert olculdu["ref_kaynak"] == "son_kapanis"
    assert olculemedi["ref_price"] is None
    assert olculdu["ref_price"] == 98.0


# ---------- H/M: limit_bps aritmetiği ----------
def test_m16_limit_bps_isaret_olcek_ve_iki_hane():
    """Sınıf H/M: (limit/t − 1)·10000, 2 hane. Kesirli bir nokta seçildi (137.0 / ATR 0.5 →
    137.25) ki `/10000`, `+1.0`, `limit*t`, `−2.0` ve hassasiyet varyantlarının HEPSİ ayrışsın —
    tam sayıya oturan bir örnekte (%1 tavan → tam 100.0) bunların bir kısmı gizlenirdi."""
    d = _karar(137.0, None, 0.5)
    assert d["limit"] == 137.25
    assert d["limit_bps"] == 18.25                     # 3 hane → 18.248; int → 18; /10000 → 0.0
    assert 0 < d["limit_bps"] < 100                    # işaret + ölçek: +1.0 → 20018.25, −2.0 → −9981.75


def test_m17_bps_carpani_tam_on_bin():
    """Sınıf M: `*10000` → `*10001` farkı %1 tavanda iki haneli yuvarlamanın ALTINDA kalır
    (18.25 == 18.25). %5 tavanda ayrışır: 500.0 vs 500.05. Ayrıştıran noktayı kullanıyoruz."""
    d = _karar(100.0, 90.0, None, cfg=_CFG_GENIS)
    assert d["limit"] == 105.0
    assert d["limit_bps"] == 500.0


# ---------- C: cfg gerçekten okunuyor mu? ----------
def test_m18_gecirilen_cfg_limit_hesabina_da_gider():
    """Sınıf C: `entry_limit_price(t, atr, cfg)` çağrısından cfg düşerse fonksiyon sessizce
    YÜRÜRLÜKTEKİ yasaya döner — çağıranın (kart grid'i, karşı-olgusal defter) seçtiği nokta yok
    sayılır ve rapor edilen `law`/`gap_behavior` ile fiilen kullanılan limit ÇELİŞİR."""
    yururlukte = b.entry_law()
    assert yururlukte["limit_pct_cap"] != _CFG_GENIS["limit_pct_cap"], (
        "Test gücü ön koşulu: _CFG_GENIS yürürlükteki yasadan FARKLI olmalı, yoksa cfg'nin "
        "düşürüldüğü mutasyon ayrışmaz. goal.yaml'de limit_pct_cap %5 olduysa buradaki değeri "
        "değiştir.")
    d = _karar(100.0, 90.0, None, cfg=_CFG_GENIS)
    assert d["limit"] == 105.0                         # cfg düşerse 101.0 olurdu
    assert d["limit_bps"] == 500.0                     # ve 100.0
    assert d["law"] == "TEST-E1"                       # rapor edilen yasa ile hesap aynı kaynaktan
