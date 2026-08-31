"""v346 — EDG-2026-062 YOL-TUTARLI POZİTİF KONTROL: gerçek EDGAR satırı, TAM `scan_all` yolu.

Kartın `pozitif_kontrol` şartı (`research/cards/EDG-2026-062-pit-arsiv-baglamasi.yaml`):
"gerçek arşiv satırından bilinen bir vaka, replay yolunun TAMAMINDAN (scan → evaluate_pead →
days_since_report) geçerek True üretir; aynı sembolün sınır-dışı günü False üretir; arşiv-ufku-
ötesi gün OLCULEMEDI sayılır. Üçü de gerçek CSV satırıyla, sentetikle değil."

NEDEN `scan_all`, NEDEN DOĞRUDAN ÇAĞRI DEĞİL (vaka 2026-08-25): tek-enstrümanlı / tek-fonksiyonlu
bir PK portföy-YOLU hatalarına kördür. `days_since_report_pit`i doğrudan çağıran bir çivi, dikiş
`scan_all`ın hiçbir dalına bağlı olmasa bile yeşil kalırdı. Bu dosya çapayı HİÇ doğrudan çağırmaz:
her hüküm `strategy.scan_all(...)` dönüşünden ve `earnings_pit.sayac_oku()`dan okunur — yani
ölçülen şey "fonksiyon doğru cevabı veriyor mu" değil, "üretim yolu o cevaba VARIYOR mu"dur.

NE GERÇEK, NE SENTETİK (kartın ayrımı): ÇAPA VERİSİ ve YOL gerçektir — çapa, depodaki gerçek
`research/edgar_facts/earnings_8k_tarihleri.csv` arşivinden, üretim tarama yüzeyinden geçerek
sorulur. BARLAR sentetiktir ve olmak zorundadır: PEAD geometrisi (kazanç boşluğu → yeşil hafta →
kırmızı hafta → taze yeniden-kırılım) gerçek bir OHLCV serisinde ancak rastlantıyla bulunur ve
bulunduğu gün kırılırdı; bu kartın ölçtüğü şey fiyat geometrisi DEĞİL, çapanın kaynağıdır.
Fikstür `tests.test_pead_v93._pead_bars`ten İTHAL edilir, kopyalanmaz (tek-kaynak yasası).

SEANS GÜNÜ FİKSTÜRE TAM HAFTA KATIYLA TAŞINIR (`_seans_barlari`): kaydırma 7'nin katı olduğu için
her bar aynı HAFTA GÜNÜNDE kalır, `evaluate_pead`in haftalık `resample("W")` gruplaması birebir
korunur ve fikstürün sabitlediği `red_high` değişmez. Kayma 7'nin katı değilse çivi ADIYLA durur —
sessizce başka bir geometri ölçmeye başlamaz.

ÇİVİLENEN GERÇEK SATIR (arşivde ölçüldü 2026-08-31): `JPM,2025-04-11,2025-04-11` — bir CUMA sabahı
dosyalanmış 8-K item 2.02. Cuma seçimi rastgele değildir: fikstürün son barı da Cumadır, yani
dosyalama GÜNÜ tam hafta katıyla hizalanabilir ve muhafazakâr görünürlük sınırı (`filed <= seans-1`)
GERÇEK bir günde sınanabilir. Satırın hâlâ arşivde olduğu her koşumda doğrulanır
(`test_PK_GERCEK_arsivi_okur_ve_civilenen_satir_YERINDEDIR`) — arşiv aylık tazelenir ve satır
düşerse PK sessizce hiçbir şey ölçmez hâle gelirdi.

SAYAÇ NEDEN İKİ ARTAR: `scan_all` kazanç çapalı İKİ üreticiyi de koşturur —
`evaluate_episodic_pivot` (pencere `max_days=2`) ve `evaluate_pead` (pencere `pead.watch_days`=35).
İkisi de aynı seans için çapayı sorar, yani her tarama sayaca İKİ çağrı yazar. Hükümler bu yüzden
TAM SÖZLÜKTÜR, "en az bir true" gibi gevşek bir yüklem değil — ve bu tercih ÖLÇÜLDÜ, beyan değil:
üreticilerden biri çapaya VARMADAN düştüğünde (mutasyon `evaluate_episodic_pivot`te
`len(bars) < 60` → `< 200`, 2026-08-31) sayaç `{"true": 1, "false": 0, "olculemedi": 0}` olur —
`true` alanı BİREBİR AYNI kalır, yalnız `false` kaybolur. Gevşek yüklem o kaybı GÖRMEZDİ.
(Şerh: bir üreticinin SEVKİ kopunca akış canlı çapaya iner ve patlayıcı öter; o kırmızıyı gevşek
yüklem de verirdi — sözlüğün taşıyıcılığını ölçen mutasyon yukarıdaki, bu değil.)
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

import meridian.config as config
import meridian.earnings as earn
import meridian.earnings_pit as earnings_pit
import meridian.strategy as strat
from tests.test_pead_v93 import _pead_bars
# `_patlayici` / `_canli_capa` v345'ten İTHAL EDİLİR, kopyalanmaz: "yasaklı çağrı" usulü ve canlı
# defterin biçimi TEK gerçektir; iki dosyada ayrışırsa bu dosyanın yasakları sessizce gevşerdi.
from tests.test_pit_baglama_yolu_v345 import _canli_capa, _patlayici

#: Gerçek arşiv satırı — `symbol,report_date,filed` (ölçüm 2026-08-31; koşum başına doğrulanır).
SEMBOL, RAPOR, FILED = "JPM", "2025-04-11", "2025-04-11"

#: DÖRT SEANS — dördü de Cuma (fikstürün son barıyla aynı hafta günü; bkz. `_seans_barlari`).
GUN_TRUE = "2025-05-09"          # RAPOR + 28 gün: `watch_days` (35) penceresi İÇİ, filed görünür
GUN_FALSE = "2025-03-28"         # RAPOR - 14 gün: ufuk İÇİ, sembol arşivde VAR, pencere DIŞI
GUN_SINIR = "2025-04-11"         # DOSYALAMA GÜNÜNÜN KENDİSİ: muhafazakâr kural gereği HENÜZ görünmez
GUN_OLCULEMEDI = "2026-08-14"    # arşivin `filed` ufkunun ÖTESİ → "rapor yok" DEĞİL, "bilmiyoruz"

PIT = {"earnings.pit_arsiv": True}
RS = 95                          # v345'in pead çivilerindeki değer (RS kapısı bu PK'nın konusu değil)

#: Fikstürün son barı — kaydırma çapası. `_pead_bars`ten TÜRETİLİR, ikinci bir tarih ızgarası
#: yazılmaz: v93 ızgarasını değiştirirse hizalama iddiası burada ADIYLA düşer (`_seans_barlari`).
_TEMEL_SON: dt.date = _pead_bars()[0]["date"].iloc[-1].date()


@pytest.fixture(autouse=True)
def _pit_temiz():
    """Sayaç hem ÖNCE hem SONRA sıfırlanır (v344/v345 emsali): her çivi yalnız KENDİ çağrılarını
    sayar ve bu dosyadan çıkan artık komşu dosyalara sızmaz.

    `clear_cache()` BİLİNÇLİ OLARAK ÇAĞRILMAZ: bu dosyanın arşivi GERÇEK ve 17 bin satırlıdır,
    ve `ARSIV_YOLU` hiçbir çivide monkeypatch'lenmez — yani (yol, mtime) anahtarı koşum boyunca
    sabittir ve önbellek TAM OLARAK doğru cevabı verir. Her çivide düşürmek 17k satırı yeniden
    ayrıştırmaktan başka bir şey yapmazdı (ölçülmeyen bedel; komşu dosyaların sentetik arşivleri
    zaten kendi `clear_cache`leriyle gelir/gider)."""
    earnings_pit.sayac_sifirla()
    yield
    earnings_pit.sayac_sifirla()


def _seans_barlari(gun: str) -> pd.DataFrame:
    """PEAD fikstürünü `gun` seansında BİTİRİR — kaydırma TAM HAFTA KATIDIR.

    Neden hafta katı: fikstür `red_high`ı haftalık `resample("W")` üzerinden hesaplayıp son iki barı
    ona göre SABİTLER. Rastgele bir gün kaydırması bar-hafta gruplamasını değiştirir, `red_high`
    kayar ve `cprev < red_high <= c` çaprazı bozulur — yani çivi "çapa yüzünden sinyal yok" derken
    aslında geometriyi bozmuş olurdu (aranan kusur, gösterdiği yerde olmazdı). 7'nin katı kaydırma
    her barı aynı hafta gününde bırakır: `bdate_range` yalnız hafta sonlarını atar, dolayısıyla
    ızgara birebir taşınır ve fiyat serisine HİÇ dokunulmaz."""
    df, _rep = _pead_bars()
    kayma = (dt.date.fromisoformat(gun) - _TEMEL_SON).days
    assert kayma % 7 == 0, (
        f"{gun} fikstürün son barıyla ({_TEMEL_SON}, {_TEMEL_SON:%A}) aynı hafta gününde DEĞİL — "
        "kaydırma geometriyi bozar; ya günü hizala ya v93 ızgarası değişmiştir")
    df = df.copy()
    df["date"] = df["date"] + pd.Timedelta(days=kayma)
    return df


def _tara(gun: str, params: dict) -> dict:
    """TAM YOL: `strategy.scan_all` → (episodic_pivot | pead) → çapa. Çapa DOĞRUDAN çağrılmaz."""
    return strat.scan_all(_seans_barlari(gun), dict(params), RS, SEMBOL)


# ---------------------------------------------------------------------------------------------
# 0) PK'NIN ZEMİNİ — gerçek arşiv, gerçek satır (yoksa aşağıdaki her çivi boş geçerdi)
# ---------------------------------------------------------------------------------------------
def test_PK_GERCEK_arsivi_okur_ve_civilenen_satir_YERINDEDIR():
    """Kartın "üçü de gerçek CSV satırıyla, sentetikle değil" şartının KANITI — ve aşağıdaki bütün
    çivilerin ön koşulu. Üç ayrı sessiz ölüm biçimi burada yakalanır:

    (a) `ARSIV_YOLU` başka bir yere bakıyor (komşu dosyaların monkeypatch'i sızmış) → PK sentetik
        bir arşivi ölçer ve kart şartı YAZILI kalır, ölçülü değil.
    (b) Çivilenen satır arşivden düşmüş (arşiv AYLIK tazelenir — kart `girdi_dondurma`) → çapa
        `olculemedi`ye iner, üç dal da "sinyal yok" der ve PK'nın True dalı ayırt etmez olur.
    (c) Arşivin ufku `GUN_OLCULEMEDI`yi kapsayacak kadar ilerlemiş → üçüncü dal sessizce `false`a
        döner ve tam olarak AYIRMAK için var olduğu iki durumu birleştirir.

    Ufuk EŞİTLİK yerine EŞİTSİZLİKLE ölçülür: `son == "2026-07-31"` yazmak, arşivin bir sonraki
    tazelemesinde bu çiviyi ARIZASIZ kırardı. Ölçülen şey tarihin kendisi değil, GUN_OLCULEMEDI'nin
    hâlâ ufkun DIŞINDA olmasıdır."""
    beklenen = config.ROOT / "research" / "edgar_facts" / "earnings_8k_tarihleri.csv"
    assert earnings_pit.ARSIV_YOLU == beklenen, "arşiv yolu sapmış — PK gerçek veriyi okumuyor"
    assert beklenen.exists(), f"gerçek PIT arşivi yok: {beklenen}"

    satirlar = earnings_pit._arsiv_yukle().get(SEMBOL)
    assert satirlar, f"{SEMBOL} gerçek arşivde YOK — PK'nın çapası kalmadı"
    assert (RAPOR, FILED) in satirlar, (
        f"çivilenen gerçek satır ({SEMBOL}, {RAPOR}, {FILED}) arşivde YOK — arşiv tazelenmiş "
        "olabilir; yeni bir satır seç ve sabitleri güncelle (PK aksi hâlde hiçbir şey ölçmez)")

    ufuk = earnings_pit.arsiv_ufku()
    assert ufuk["ilk"] is not None and ufuk["son"] is not None, f"arşiv ufku ölçülemedi: {ufuk}"
    assert dt.date.fromisoformat(ufuk["ilk"]) <= dt.date.fromisoformat(GUN_FALSE), \
        f"GUN_FALSE ufkun ÖNÜNDE — o dal `olculemedi`ye düşer, `false` ölçmez ({ufuk['ilk']})"
    assert dt.date.fromisoformat(ufuk["son"]) < dt.date.fromisoformat(GUN_OLCULEMEDI), (
        f"arşiv ufku {ufuk['son']}'e ilerledi ve GUN_OLCULEMEDI ({GUN_OLCULEMEDI}) artık İÇERİDE — "
        "üçüncü dal `false` ile karışır; sabiti ufkun ötesine taşı")
    # ÜST UÇ DA SORULUR (inceleme 2026-08-31, Bulgu 2): arşiv GERİYE büzülürse (yeniden üretim
    # kazası, kısmi tazeleme) `GUN_TRUE` ufkun DIŞINDA kalır ve TRUE dalı sessizce `olculemedi`ye
    # düşer. O hâl 1. çivide bir sözlük uyuşmazlığı olarak yine yakalanır — ama zemin çivisi tam
    # olarak bu sessiz ölüm sınıfını ADIYLA söylemek için var; teşhisi doğru yerde vermeyen bir
    # bekçi, arızayı fikstürün içinde arattırır.
    assert dt.date.fromisoformat(ufuk["son"]) >= dt.date.fromisoformat(GUN_TRUE), (
        f"arşiv ufku {ufuk['son']}'e BÜZÜLDÜ ve GUN_TRUE ({GUN_TRUE}) artık kapsam DIŞINDA — "
        "PK'nın pozitif dalı `olculemedi`ye düşer, yani True'yu ayırt eden çivi kalmaz")


# ---------------------------------------------------------------------------------------------
# 1) TRUE DALI — gerçek rapordan 28 gün sonra, tam yoldan PEAD sinyali
# ---------------------------------------------------------------------------------------------
def test_PIT_yolu_GERCEK_rapor_penceresinde_PEAD_URETIR(sandbox_state, monkeypatch):
    """PK'nın POZİTİF ucu: gerçek `JPM 2025-04-11` raporundan 28 gün sonraki seansta, `scan_all`
    penceresi geçen bir PEAD sinyali ÜRETİR ve çapa `true` sayılır.

    CANLI KAYNAK PATLAYICIDIR: param varken `earnings.days_since_report` çağrılırsa çivi ADIYLA
    düşer. Yani bu sinyal "bir yerden çapa bulundu"nun değil, "çapa PIT ARŞİVİNDEN geldi"nin
    kanıtıdır — üstelik sandbox'ta `state/earnings.csv` HİÇ YOK, yani canlı yol sızsaydı sinyal
    zaten çıkmazdı (çift kanıt).

    SAYAÇ TAM SÖZLÜKTÜR: `false: 1` bir arıza DEĞİL, yolun kendisidir — `evaluate_episodic_pivot`
    aynı seansı `max_days=2` penceresiyle sorar ve 28 gün önceki rapor o pencerede yoktur. İki
    üretici de sorduğu için toplam 2'dir. Sözlüğün TAŞIYICI olduğu ölçüldü (modül başlığındaki
    mutasyon şerhi): episodic çapaya varmadan düşürüldüğünde `true` 1 kalır ve YALNIZ `false`
    kaybolur — "true >= 1" yüklemi o kaybı görmezdi, bu satır görür."""
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    by = _tara(GUN_TRUE, PIT)
    assert "pead" in by, f"gerçek rapor penceresinde PEAD ateşlemedi — üretilen: {sorted(by)}"
    assert by["pead"].setup == "pead" and by["pead"].ticker == SEMBOL
    assert earnings_pit.sayac_oku() == {"true": 1, "false": 1, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 2) FALSE DALI — aynı sembol, pencere DIŞI gün: sinyal yok, ve `olculemedi` DEĞİL
# ---------------------------------------------------------------------------------------------
def test_PIT_yolu_PENCERE_DISI_gunde_sinyal_URETMEZ_ve_FALSE_sayar(sandbox_state, monkeypatch):
    """Aynı sembol, aynı barlar, TEK FARK seans günü: rapordan 14 gün ÖNCE. Kurulum yok.

    ASIL HÜKÜM İKİNCİ SATIRDADIR: `false: 2` — yani cevap "o gün rapor yoktu" diye ÖLÇÜLDÜ, "o gün
    hakkında bilgimiz yoktu" diye katlanmadı. Bu ayrım kartın kapsama eşiğinin (>=%95) okuduğu
    şeydir; `olculemedi`ye düşseydi karar aynı, ÖLÇÜM yanlış olurdu.

    "pead not in by" YETMEZ, `episodic_pivot` de sınanır: iki kazanç çapalı üretici de bu seansta
    susmalıdır. Diğer kurulumlar (entry/burst/pullback…) bu PK'nın konusu değildir ve serbesttir —
    onları da yasaklamak, fikstürün geometrisini ölçen sahte bir kısıt olurdu."""
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    by = _tara(GUN_FALSE, PIT)
    assert "pead" not in by and "episodic_pivot" not in by, \
        f"pencere DIŞI günde kazanç çapalı kurulum ateşledi: {sorted(by)}"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 2, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 3) OLCULEMEDI DALI — arşiv ufkunun ÖTESİ: `false` ile KARIŞMAZ
# ---------------------------------------------------------------------------------------------
def test_PIT_yolu_UFUK_OTESI_gunde_OLCULEMEDI_sayar_FALSE_DEGIL(sandbox_state, monkeypatch):
    """Kartın `ufuk_sozlesmesi` maddesi (eşik değil SÖZLEŞME): "seans > arşiv filed-max ise satır
    OLCULEMEDI — asla 'rapor yok' (False) sayılmaz".

    KARAR İKİ DALDA AYNIDIR (kurulum yok) ve olması gereken de budur; AYRIM SAYAÇTADIR. Bir
    önceki çiviyle birlikte okunur: aynı sembol, aynı barlar, aynı "sinyal yok" hükmü — ama biri
    `false`, diğeri `olculemedi` kovasına düşer. İkisi tek kovaya katlansaydı, arşivin kapsamadığı
    bir dönemde koşan bir replay "bu isimlerde hiç kazanç yoktu" diye okunurdu."""
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    by = _tara(GUN_OLCULEMEDI, PIT)
    assert "pead" not in by and "episodic_pivot" not in by, \
        f"ufuk ötesi günde kazanç çapalı kurulum ateşledi: {sorted(by)}"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 2}


# ---------------------------------------------------------------------------------------------
# 4) GÖRÜNÜRLÜK SINIRI — dosyalama GÜNÜ henüz görünmez (kartın `zaman_cozunurlugu` maddesi)
# ---------------------------------------------------------------------------------------------
def test_PIT_yolu_DOSYALAMA_GUNUNDE_sinyal_URETMEZ(sandbox_state, monkeypatch):
    """`filed <= seans - 1` — dosyalamanın KENDİ günü DAHİL DEĞİL (kart: "EŞİT seans günü DAHİL
    DEĞİL; acceptance saat-dilimi belirsizliği çözülene dek gün-içi bilgi varsayılmaz").

    BU ÇİVİ GERÇEK BİR GÜNDE SINAR: `JPM 2025-04-11` bir Cuma sabahı dosyalanmıştır ve seans o
    Cumadır. Kural `<= seans`a gevşerse (bir karakterlik değişiklik) çapa o gün True döner, PEAD
    ateşler ve motor, kapanmamış bir seansın kararında o gün henüz kesinleşmemiş bir bilgiyi
    kullanmış olur — tam olarak bu kartın kaldırdığı look-ahead sınıfı. Hüküm çift ayaklıdır:
    sinyal YOK ve sayaç `false` (yani "sembol/tarih kapsam dışı" gibi bir kaza değil, kuralın
    ÖLÇÜLMÜŞ reddi)."""
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    by = _tara(GUN_SINIR, PIT)
    assert "pead" not in by, (
        "dosyalama GÜNÜNDE PEAD ateşledi — muhafazakâr görünürlük kuralı (filed <= seans-1) "
        "gevşemiş; o seansın kararına henüz görünür olmayan bir rapor sızıyor")
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 2, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 5) YOL AYRIMININ PK'SI — param YOKKEN aynı seanslar CANLI yoldan akar, PIT sayacı HİÇ artmaz
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("gun,pead_bekleniyor",
                         [(GUN_TRUE, True), (GUN_FALSE, False), (GUN_OLCULEMEDI, False)],
                         ids=["true_gunu", "false_gunu", "olculemedi_gunu"])
def test_param_YOKKEN_ayni_seanslar_CANLI_yoldan_akar_ve_PIT_SAYACI_ARTMAZ(
        gun, pead_bekleniyor, sandbox_state, monkeypatch):
    """PK'nın DÖRDÜNCÜ dalı — kartın "canlı yol DEĞİŞMİŞSE kill" maddesinin pozitif kontrolü.

    Yukarıdaki üç dalın hepsi param VARKEN ölçüldü. Bu çivi aynı üç seansı param YOKKEN koşturur:
    hüküm canlı `state/earnings.csv` defterindendir, PIT arşivi HİÇ sorulmaz (`days_since_report_pit`
    patlayıcıdır ve sayaç sıfır kalır). İkisi birden gerekir: yalnız "sayaç sıfır" yazsaydık,
    dikiş her iki kaynağı da atlayıp sabit None dönse çivi yine yeşil kalırdı — bu yüzden `true`
    gününde sinyalin GERÇEKTEN ateşlemesi de sınanır.

    CANLI DEFTERDE `filed` SÜTUNU YOKTUR (o dosya bugünün ileri-pencere önbellekidir, PIT arşivi
    değil) — bu yüzden canlı yol yalnız `report_date` mesafesine bakar; iki yolun bundan doğan
    AYRIMI bir alttaki çivide ölçülür."""
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    _canli_capa(sandbox_state, SEMBOL, RAPOR)
    by = strat.scan_all(_seans_barlari(gun), {}, RS, SEMBOL)
    assert ("pead" in by) is pead_bekleniyor, \
        f"canlı yol {gun} seansında beklenen PEAD hükmünü vermedi: {sorted(by)}"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}, \
        "param YOKKEN PIT arşivi sayaç artırdı — canlı yol PIT'e sızıyor"


def test_DOSYALAMA_GUNUNDE_IKI_YOL_AYRISIR_canli_atesler_PIT_ATESLEMEZ(sandbox_state, monkeypatch):
    """KARTIN BÜTÜN GEREKÇESİ TEK ÇİVİDE — ve bu, bağlamanın DAVRANIŞ DEĞİŞTİRDİĞİNİN ölçüsüdür
    (kill-list 4: "davranış değişimi RAPORSUZ kalırsa kill").

    Aynı sembol, aynı barlar, aynı seans (`2025-04-11`, raporun dosyalandığı Cuma):
      · CANLI yol  → `state/earnings.csv` yalnız rapor TARİHİNİ taşır, `filed` taşımaz; 0 gün
                     mesafe penceredir → PEAD ATEŞLER. O gün o bilgi gerçekten görünür müydü,
                     bu kaynak SÖYLEYEMEZ (`pitlaw` bu yüzden onu tarihsel yolda sıfır-toleransa
                     koyuyordu).
      · PIT yolu   → arşiv `filed`i TAŞIR; muhafazakâr kural gereği o gün henüz görünmez →
                     ATEŞLEMEZ, ve `false` sayılır.

    İki yol AYRIŞMASAYDI bağlama bir isim değişikliğinden ibaret olurdu: PIT'e "bağladık" cümlesi
    ölçülür bir fark üretmezdi. `monkeypatch.undo()` KULLANILMAZ (autouse fikstürleri de geri
    alır — vaka 2026-08-30); yasaklar sırayla YENİDEN atanır."""
    gercek_pit = earnings_pit.days_since_report_pit

    # FAZ 1 — CANLI YOL (param yok): PIT sorulursa çivi adıyla düşer.
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    _canli_capa(sandbox_state, SEMBOL, RAPOR)
    canli = strat.scan_all(_seans_barlari(GUN_SINIR), {}, RS, SEMBOL)
    assert "pead" in canli, (
        "canlı yol dosyalama gününde ateşlemedi — bu çivinin ölçtüğü AYRIM ortadan kalktı "
        "(canlı defterin look-ahead'i başka bir sebeple kapanmışsa bu kayıt ÇÜRÜMÜŞTÜR)")
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}

    # FAZ 2 — PIT YOLU (param var): şimdi canlı kaynak yasak. `undo` YOK, yeniden atama VAR.
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", gercek_pit)
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    pit = _tara(GUN_SINIR, PIT)
    assert "pead" not in pit, "PIT yolu da ateşledi — görünürlük kuralı iki yolu AYIRMIYOR"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 2, "olculemedi": 0}
