"""test_mutborc_score_equity_curve_v148.py — H5 TEST-BORCU: `meridian/score.py::equity_curve`
mutasyon kümesi (11 hayatta kalan mutant, mutmut çalışması 2026-08-01).

NEDEN VAR: `equity_curve` altı satırdır ve "toplamı doğru mu" diye bakan her test onu YEŞİL
gösterir. Ama bu fonksiyonun ürettiği şey bir TOPLAM değil, bir YOL'dur: `max_drawdown` yolun
tepelerinden geçer, `score_detail` drawdown'ı puanın %30'u yapar. Toplam değişmeden yol
değişebilir — ve hayatta kalan 11 mutantın 8'i tam olarak bu sınıftadır (sıralamayı bozar,
toplamı KORUR). Mevcut testler (`test_para_yasasi_v127.py`, `test_score_audit_v40.py`) eğriyi
hep ZATEN ts_close sırasında hazırlanmış fikstürlerle çağırıyordu; sıralama satırının silinmesi
o testlerde HİÇBİR fark yaratmıyordu. Bu dosya yolu çivileyerek o kör noktayı kapatır.

KAPSAM HARİTASI (mutant no → sınıf → test):
  8, 9, 11, 13, 14   sıralama anahtarı SABİTLENİR (str(None) / x.get(None) / x.get("") /
                     "XXts_closeXX" / "TS_CLOSE" → her işlem için aynı anahtar). sorted()
                     kararlı olduğu için GİRDİ SIRASI korunur: eğri artık zaman sırasında
                     değildir.                                              → test_m01
  10, 12, 15         ts_close YOKKEN kullanılan varsayılan ("" yerine None/"XXXX").
                     "" her tarihten KÜÇÜKTÜR (damgasız kayıt en başa gider); "None" ve "XXXX"
                     ise "2026-…"den BÜYÜKTÜR (en sona gider).              → test_m02
  20, 22, 25         pnl_dollars YOKKEN kullanılan varsayılan (0.0 yerine None/1.0).
                     None → float(None) patlar; 1.0 → eksik kayıt yoktan 1 dolar üretir. → test_m03

EŞDEĞER — ÖLDÜRÜLEMEZ: bu kümede YOK. 11 hayatta kalanın 11'i de gözlemlenebilir davranışı
değiştirir ve aşağıdaki üç test hepsini kırmızıya düşürür. YASA 4 ruhu gereği kayda geçiyorum:
atlanan, "eşdeğer sayıldığı için test yazılmayan" mutant yoktur.

NASIL DOĞRULANDI (UYDURMA YASAĞI — iddia ölçüldü, varsayılmadı): `mutmut results` bu oturumda
ÇIKTI VERMEDİ (sonuç veritabanı yok), yani hayatta-kalan listesi mutmut'tan OKUNMADI; 26 mutant
gövdesi `mutants/meridian/score.py`ten AST ile çıkarılıp tek tek `sc.equity_curve` yerine takıldı
ve bu dosyanın testleri her biri için koşuldu. Sonuç: 26/26 mutant en az bir testi düşürüyor,
hayatta kalan YOK. Yalnız sınıf-özgü testle ölen 11 mutant (yani bu dosya olmadan ayakta kalanlar)
tam olarak yukarıdaki haritadaki 8,9,10,11,12,13,14,15,20,22,25'tir — brief'in bildirdiği 11
sayısıyla birebir örtüşür. Geri kalan 15'i zaten ölüydü (aşağıdaki listeye bakınız).

ZATEN ÖLÜ (referans; bu dosya onları hedeflemez ama test_m04/m05/m06 geri dirilmelerini önler):
  1,2,3,5,7,18,19,21   → TypeError/AttributeError (None'a += , None.append, sorted(None), …)
  4, 6                 → key düşürülür; sorted() ham dict'leri karşılaştırmaya çalışır → TypeError
  16                   → `eq +=` → `eq =` (kümülatif eğri per-trade P&L listesine döner)
  17                   → `eq +=` → `eq -=` (işaret)
  23, 24               → "XXpnl_dollarsXX" / "PNL_DOLLARS" (her işlem 0 → düz eğri)
  26                   → `curve.append(None)`
"""
from __future__ import annotations

from meridian import score as sc


# =================================================================================================
# F1 — SIRALAMA FİKSTÜRÜ: girdi sırası ts_close sırasının TERSİ değil, KARIŞIK olsun diye seçildi
# =================================================================================================
# Bilinçli tasarım: üç işlemin TOPLAMI (+3000) sıradan bağımsızdır, ama YOL değildir.
#   ts_close sırası : -3000 (Oca 20) → +1000 (Şub 14) → +5000 (Mar 10)
#     eğri          : 100000 → 97000 → 98000 → 103000     (dip 97000, max_dd = 3000/100000)
#   girdi sırası    : +5000 → -3000 → +1000
#     eğri          : 100000 → 105000 → 102000 → 103000   (tepe 105000, max_dd = 3000/105000)
# Son değer İKİ HALDE DE 103000'dir. "Toplam tutuyor" diye bakan bir test bu farkı GÖREMEZ;
# drawdown ise %3 ile %2.857 arasında ayrışır — kapının okuduğu sayı budur.
F1 = [
    {"ts_open": "2026-03-02", "ts_close": "2026-03-10", "pnl_dollars": 5000.0},
    {"ts_open": "2026-01-12", "ts_close": "2026-01-20", "pnl_dollars": -3000.0},
    {"ts_open": "2026-02-06", "ts_close": "2026-02-14", "pnl_dollars": 1000.0},
]

F1_ZAMAN_SIRASI = [100000.0, 97000.0, 98000.0, 103000.0]
F1_GIRDI_SIRASI = [100000.0, 105000.0, 102000.0, 103000.0]


# =================================================================================================
# test_m01 — eğri ts_close'a göre sıralanır, GİRDİ SIRASINA göre değil   (mutant 8, 9, 11, 13, 14)
# =================================================================================================
def test_m01_egri_zaman_sirasinda_kurulur_girdi_sirasinda_degil():
    """Sıralama anahtarı sabitlenirse (`str(None)`, `x.get(None, "")`, `x.get("")`,
    `"XXts_closeXX"`, `"TS_CLOSE"` — hepsi her işlem için AYNI anahtarı üretir) `sorted`
    kararlı olduğundan girdi sırası olduğu gibi kalır. Defterin dosyadan okunma sırası
    kapanış sırası DEĞİLDİR; eğri o zaman sermayenin hiç uğramadığı tepelerden/diplerden
    geçer ve `max_drawdown` gerçekte yaşanmamış bir yolu ölçer.

    Toplam iki halde de aynı (+3000) olduğu için burada iddia edilen şey EĞRİNİN TAMAMIDIR;
    yalnız son değere bakan bir iddia bu mutasyon sınıfını GÖREMEZ."""
    egri = sc.equity_curve(F1)

    assert egri == F1_ZAMAN_SIRASI
    assert len(egri) == len(F1) + 1, "eğri başlangıç sermayesiyle BAŞLAR (n+1 nokta)"

    # Testin kendi keskinliği: girdi sırası gerçekten FARKLI bir eğri veriyor mu?
    assert F1_GIRDI_SIRASI != F1_ZAMAN_SIRASI
    assert egri != F1_GIRDI_SIRASI
    assert egri[-1] == F1_GIRDI_SIRASI[-1] == 103000.0, "toplam sıradan bağımsız — ayrım YOLDA"

    # Ve fark KARARA giriyor: drawdown iki yolda ayrışıyor.
    assert sc.max_drawdown(egri) == 0.03
    assert sc.max_drawdown(F1_GIRDI_SIRASI) != sc.max_drawdown(egri)

    # Girdi sırası permütasyondan bağımsız olmalı: aynı işlemler, başka sırayla → AYNI eğri.
    assert sc.equity_curve([F1[1], F1[2], F1[0]]) == F1_ZAMAN_SIRASI
    assert sc.equity_curve(list(reversed(F1))) == F1_ZAMAN_SIRASI


# =================================================================================================
# test_m02 — ts_close YOKSA kayıt EN BAŞA gider (varsayılan "")           (mutant 10, 12, 15)
# =================================================================================================
def test_m02_ts_close_yoksa_kayit_en_basa_gider():
    """Zaman damgasız bir kapanış kaydının nereye konacağı bir HÜKÜMDÜR, tesadüf değil.
    Sözleşme: varsayılan `""` — boş dize her tarih dizesinden küçüktür, yani damgasız kayıt
    eğrinin EN BAŞINA düşer (muhafazakâr: sermayeyi en erken etkiler, sonraki drawdown'lar
    onun üzerinden ölçülür). Varsayılan `None` olursa `str(None)` = "None", `"XXXX"` olursa
    "XXXX" — ikisi de "2026-…"den BÜYÜKTÜR ve kayıt sessizce EN SONA kayar.

    Bu mutantlar ts_close'u OLAN işlemlerde gerçek kodla birebir aynı davranır; ancak
    damgasız bir kayıt varken ayrışırlar. test_m01 onları göremez, bu test görür."""
    islemler = [
        {"ts_open": "2026-01-02", "pnl_dollars": 7000.0},                      # ts_close YOK
        {"ts_open": "2026-01-02", "ts_close": "2026-01-05", "pnl_dollars": -2000.0},
        {"ts_open": "2026-02-02", "ts_close": "2026-02-09", "pnl_dollars": 500.0},
    ]

    egri = sc.equity_curve(islemler)
    assert egri == [100000.0, 107000.0, 105000.0, 105500.0]
    assert egri[1] == 107000.0, "damgasız kayıt İLK uygulanır (+7000); sona atılmadı"

    # Sözleşmenin dayandığı dize sırası açıkça yazılı olsun (mutantların ayrıştığı nokta):
    assert "" < "2026-01-05" < "None" and "2026-02-09" < "XXXX"

    # Damgasız kayıt sona atılsaydı eğri BU olurdu — ayrım yalnız yolda, son değer aynı:
    sona_atilmis = [100000.0, 98000.0, 98500.0, 105500.0]
    assert egri != sona_atilmis and egri[-1] == sona_atilmis[-1]
    assert sc.max_drawdown(egri) != sc.max_drawdown(sona_atilmis)


# =================================================================================================
# test_m03 — pnl_dollars YOKSA katkı TAM 0.0'dır                          (mutant 20, 22, 25)
# =================================================================================================
def test_m03_eksik_pnl_dollars_tam_sifir_katki_yapar():
    """UYDURMA YASAĞI'nın en küçük ölçekteki hâli: P&L'i olmayan bir kayıt sermayeyi
    OYNATMAZ. Varsayılan düşerse (`t.get("pnl_dollars", None)` / tek argümanlı `t.get(...)`)
    `float(None)` patlar ve tek bozuk satır tüm skor hesabını çökertir; varsayılan `1.0`
    olursa eksik veri yoktan 1 dolar kâr üretir — sessizce, her eksik satır için.

    Eğri UZUNLUĞU değişmez: kayıt eğride bir NOKTA olarak durur (n+1 nokta sözleşmesi),
    yalnız değeri bir öncekiyle AYNIdır. Bu, 'satır atlandı' ile 'satır sıfır katkı yaptı'
    ayrımını da çivilemiş olur."""
    islemler = [
        {"ts_open": "2026-01-02", "ts_close": "2026-01-10", "pnl_dollars": 2500.0},
        {"ts_open": "2026-01-15", "ts_close": "2026-01-20"},                   # pnl_dollars YOK
        {"ts_open": "2026-01-25", "ts_close": "2026-01-30", "pnl_dollars": -400.0},
    ]

    egri = sc.equity_curve(islemler)
    assert egri == [100000.0, 102500.0, 102500.0, 102100.0]
    assert len(egri) == 4, "eksik satır ATLANMAZ; eğride noktası vardır"
    assert egri[2] == egri[1], "eksik P&L sermayeyi HİÇ oynatmaz"
    assert egri[2] != egri[1] + 1.0, "varsayılan 1.0 değil 0.0"

    # Aynı fikstür açıkça 0.0 yazılmış hâliyle BİREBİR aynı eğriyi vermeli — 'yok' ile
    # 'sıfır' bu fonksiyonun sözleşmesinde aynı şeydir (üst katman farkı ayrıca beyan eder).
    acik_sifir = [dict(t) for t in islemler]
    acik_sifir[1]["pnl_dollars"] = 0.0
    assert sc.equity_curve(acik_sifir) == egri


# =================================================================================================
# DEFANS — zaten ölü sınıflar (bu dosyanın hedefi değil; geri dirilmesinler diye duruyorlar)
# =================================================================================================
def test_m04_egri_kumulatiftir_ve_isaret_korunur():
    """`eq +=` → `eq =` (mutant 16) eğriyi per-trade P&L listesine çevirir; `eq -=` (17)
    işareti ters çevirir. İkisi de son değeri değiştirir, ama iddia AÇIK dursun."""
    egri = sc.equity_curve(F1)
    artislar = [egri[i + 1] - egri[i] for i in range(len(egri) - 1)]
    assert artislar == [-3000.0, 1000.0, 5000.0], "her adım o işlemin P&L'i kadar KÜMÜLE eder"
    assert egri[-1] - egri[0] == 3000.0, "net değişim toplam P&L'dir (işaret dahil)"


def test_m05_baslangic_sermayesi_egrinin_ILK_noktasidir():
    """`eq = None` (mutant 1) / `curve = None` (2) sınıfı; ayrıca varsayılan sermaye
    sözleşmesi. Eğri HER ZAMAN başlangıç sermayesiyle açılır, ilk işlemle değil."""
    assert sc.equity_curve([]) == [sc.START_EQUITY]
    assert sc.equity_curve([], start_equity=0.0) == [0.0]

    ozel = sc.equity_curve(F1, start_equity=50000.0)
    assert ozel[0] == 50000.0
    assert ozel == [50000.0, 47000.0, 48000.0, 53000.0]
    assert sc.equity_curve(F1)[0] == 100000.0 == sc.START_EQUITY


def test_m06_tek_islem_ve_bos_defter_sinirlari():
    """`sorted(trades)` anahtarsız (mutant 4, 6) tek elemanlı listede PATLAMAZ — bu yüzden
    sınır testleri tek başına yeterli değildir; test_m01 çok elemanlı fikstürü bu yüzden
    kullanır. Burada kayda geçen şey n=0 ve n=1 sözleşmesidir."""
    assert sc.equity_curve([]) == [100000.0]
    assert sc.equity_curve([{"ts_close": "2026-01-01", "pnl_dollars": 250.0}]) == [100000.0, 100250.0]
    assert sc.equity_curve([{}]) == [100000.0, 100000.0], "bomboş kayıt: damga yok, P&L yok → 0"
