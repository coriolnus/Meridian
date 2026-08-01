"""test_mutborc_score_ispan_days_v148.py — H5 TEST-BORCU: meridian/score.py::_span_days
(9 hayatta-kalan mutant, mutmut 28-36). Yazım tarihi 2026-08-01.

NEDEN BU KÜME ÖNEMLİ: `_span_days` yıllıklandırmanın PAYDASIDIR. `score_detail` içinde
`realized_30d = (1+total_return) ** (30/span) - 1` satırı doğrudan bu sayıyı kullanır, o da
kapı kararına (`ret_c` bileşeni) girer. Yani buradaki bir "miktar kayması" hiçbir istisna
atmaz, hiçbir log basmaz — yalnız skoru sistematik olarak kaydırır. Deponun baskın kusur
sınıfı tam olarak budur; bu yüzden 9 mutantın HEPSİ hata yolunda (`except` bloğu) yaşıyor:
hata yolu, ölçülmediği için mutasyonun serbestçe barındığı yerdir.

HAYATTA-KALAN MUTANT HARİTASI (mutants/meridian/score.py'den TAM okundu, ezberden değil):

  #28  _span_warn(e, None,   ts[-1])   → uyarının `first` alanı None'a düşer   [alan-kaybı]
  #29  _span_warn(e, ts[0],  None)     → uyarının `last`  alanı None'a düşer   [alan-kaybı]
  #30  _span_warn(ts[0], ts[-1])       → `e` argümanı DÜŞER → TypeError (arity) [imza]
  #31  _span_warn(e, ts[-1])           → `ilk` argümanı DÜŞER → TypeError       [imza]
  #32  _span_warn(e, ts[0], )          → `son` argümanı DÜŞER → TypeError       [imza]
  #33  _span_warn(e, ts[1],  ts[-1])   → ilk = EN ERKEN değil, İKİNCİ ts        [sınır/indeks]
  #34  _span_warn(e, ts[0],  ts[+1])   → son = EN GEÇ değil, İKİNCİ ts          [sınır/indeks]
  #35  _span_warn(e, ts[0],  ts[-2])   → son = EN GEÇ değil, SONDAN İKİNCİ ts   [sınır/indeks]
  #36  return 31.0 (yedek sabit)       → yedek payda 30 değil 31 gün            [sabit]

EŞDEĞER İLAN EDİLEN: YOK. Dokuzunun dokuzu da GÖZLENEBİLİR davranış değiştirir — üçü
(#30/#31/#32) `_span_days`i TypeError'la patlatır, dördü (#28/#29/#33/#34/#35) operatöre
sunulan uyarı kaydının içeriğini bozar, biri (#36) paydayı kaydırır. Uyarı alanlarını
"yalnız telemetri, davranış değil" sayıp eşdeğer ilan etmek YASA 4'ün ihlali olurdu: bu
uyarının VARLIK SEBEBİ, sessiz payda kaymasını operatöre GÖSTERMEKtir; `first`/`last` yanlış
tarihi söylerse operatör hangi işlemin biçimsiz olduğunu bulamaz ve kayıt kanalı bir kanıt
değil, ikinci bir yalan olur. Bu yüzden alanlar DEĞER olarak sınanır, varlık olarak değil.

FİKSTÜR SÖZLEŞMESİ: `_SPAN_WARNED` MODÜL-GLOBALİ (bir kez uyarır) her testte monkeypatch ile
False'a çekilir — aksi halde bu dosyanın testleri, kendinden ÖNCE koşan herhangi bir testin
uyarıyı harcamış olmasına bağlı hâle gelir (sıra bağımlı suite = geçtiğinde bile hiçbir şey
kanıtlamayan suite). obs.warn da yamalanır: yamalanmazsa uyarı CANLI state/events.jsonl'a
düşer ve conftest'in canlı-state bekçisi testi haklı olarak düşürür.
"""
from __future__ import annotations

import pytest

from meridian import obs
from meridian import score as sc


# İKİ GEÇERLİ + BİR BİÇİMSİZ tarih. Sıralama sonrası ts = [
#   "2026-01-01",  ← ts[0]   (EN ERKEN)
#   "2026-02-02",  ← ts[1]   (#33 ve #34 buraya kayıyor)
#   "2026-03-03",  ← ts[-2]  (#35 buraya kayıyor)
#   "ZZZZ-BOZUK",  ← ts[-1]  (EN GEÇ; 'Z' > '2' olduğu için string sıralamada sonda)
# ]
# DÖRT DEĞERİN DE FARKLI olması ŞART: ts[0]==ts[1] olsaydı #33 sessizce hayatta kalırdı —
# yani fikstürün kendisi mutantı gizlerdi (yanlış-yeşil'in en sinsi biçimi).
BOZUK_TRADES = [
    {"ts_open": "2026-01-01", "ts_close": "2026-02-02"},
    {"ts_open": "2026-03-03", "ts_close": "ZZZZ-BOZUK"},
]
ILK_TS = "2026-01-01"
SON_TS = "ZZZZ-BOZUK"
IKINCI_TS = "2026-02-02"
SONDAN_IKINCI_TS = "2026-03-03"


@pytest.fixture
def uyarilar(monkeypatch):
    """obs.warn'ı yakalar ve `_SPAN_WARNED` kapısını açar. (event, fields) çiftleri döner."""
    kayit: list[tuple[str, dict]] = []
    monkeypatch.setattr(obs, "warn", lambda event, **fields: kayit.append((event, fields)) or {})
    monkeypatch.setattr(sc, "_SPAN_WARNED", False)
    return kayit


def _span_fallback_kaydi(kayit: list[tuple[str, dict]]) -> dict:
    span = [f for ev, f in kayit if ev == "span_days_fallback"]
    assert len(span) == 1, f"tam olarak BİR span_days_fallback uyarısı beklendi, gelen: {kayit}"
    return span[0]


# ---------------------------------------------------------------------------------------------
# #36 — YEDEK SABİT: payda 30 gündür, 31 değil
# ---------------------------------------------------------------------------------------------
def test_m36_bicimsiz_tarihte_yedek_payda_tam_30_gundur(uyarilar):
    """Biçimsiz bir ts gördüğünde `_span_days` TAM 30.0 döner.

    Sabit keyfi değil SÖZLEŞMEdir: docstring ve uyarı metni ('yıllıklandırma paydası 30 güne
    sabitlendi') 30'u vaat eder. 31'e kayarsa hiçbir şey patlamaz, yalnız her yıllıklandırma
    ~%3 aşağı kayar — ölçülmediği sürece görünmeyen sınıf."""
    assert sc._span_days(BOZUK_TRADES) == 30.0
    assert isinstance(sc._span_days(BOZUK_TRADES), float)


def test_m36b_yedek_payda_skorun_yillik_landirmasina_30_olarak_girer(uyarilar):
    """DAVRANIŞ ZİNCİRİ: yedek 30 gün ise `realized_30d` TAM `total_return`e eşit olmalıdır —
    (1+r)**(30/30) - 1 = r. Payda 31 olsaydı bu eşitlik bozulurdu. Sabiti tüketicinin
    penceresinden çivileyen test; `_span_days`in neden para yolunda olduğunu da gösterir."""
    trades = [{"pnl_dollars": 500.0, "r_multiple": 1.0,
               "ts_open": "2026-01-01", "ts_close": "2026-01-02"} for _ in range(20)]
    trades[-1]["ts_close"] = "ZZZZ-BOZUK"          # sıralamada EN SONA düşer → fromisoformat patlar
    goal = {"min_sample": 20, "target_return_30d": 0.03, "max_drawdown": 0.12, "min_sharpe": 1.0}

    d = sc.score_detail(trades, goal)                       # span_days VERİLMEDİ → _span_days yolu

    assert d["realized_30d"] == d["total_return"], (
        "yedek payda 30 gün değilse 30-günlük getiri ham getiriden ayrışır — "
        f"realized_30d={d['realized_30d']} total_return={d['total_return']}")
    _span_fallback_kaydi(uyarilar)                          # gerçekten yedek yola girildiği kanıtı


# ---------------------------------------------------------------------------------------------
# #30 / #31 / #32 — İMZA: `_span_warn` ÜÇ argümanla çağrılır; eksik argüman TypeError kaçırır
# ---------------------------------------------------------------------------------------------
def test_m30_31_32_hata_yolu_istisna_kacirmaz_ve_uyariyi_gercekten_basar(uyarilar):
    """Hata yolunun KENDİSİ patlamamalıdır.

    `_span_warn(exc, ilk, son)` üç ZORUNLU konumsal argüman ister. Çağrıdan biri düşerse
    TypeError `except Exception as e:` bloğunun İÇİNDE doğar ve `_span_days`ten DIŞARI kaçar —
    yani telemetri denemesi skor hesabını düşürür. Bu, modülün açıkça reddettiği şeydir
    ('telemetri denemesi skor hesabını ASLA düşüremez'). Test hem 'istisna kaçmadı'yı hem de
    'uyarı gerçekten basıldı'yı ölçer: ikincisi olmadan no-op bir _span_warn de geçerdi."""
    sonuc = sc._span_days(BOZUK_TRADES)                     # TypeError kaçarsa test burada düşer

    assert sonuc == 30.0
    fields = _span_fallback_kaydi(uyarilar)
    assert set(fields) >= {"error", "first", "last", "detail"}, (
        f"uyarı sözleşmesi eksik alanla basıldı: {sorted(fields)}")


def test_m30_uyarinin_error_alani_gercek_istisnayi_adlandirir(uyarilar):
    """`error` alanı YAKALANAN istisnadan türemeli: 'ValueError: ...'.

    #30 `e` yerine bir tarih STRING'i geçirir; ilk kurban arity (TypeError) olsa da bu test
    sözleşmeyi ikinci bir eksenden çivi ler: bir gün imza esnetilip `exc` opsiyonel yapılırsa,
    string geçen varyant `str: ...` yazar ve operatör hangi hatanın olduğunu ASLA öğrenemez."""
    sc._span_days(BOZUK_TRADES)

    fields = _span_fallback_kaydi(uyarilar)
    assert fields["error"].startswith("ValueError:"), (
        f"error alanı gerçek istisna tipini söylemiyor: {fields['error']!r}")
    assert SON_TS in fields["error"], "istisna metni biçimsiz değeri içermeli (teşhis edilebilirlik)"


# ---------------------------------------------------------------------------------------------
# #28 / #33 — SINIR: `first` EN ERKEN ts'tir (ts[0]), ikinci değil, None değil
# ---------------------------------------------------------------------------------------------
def test_m28_m33_uyarinin_first_alani_en_erken_ts_olmali(uyarilar):
    """`first` = sıralanmış ts listesinin BAŞI.

    #28 onu None yapar (alan var ama boş — operatör aralığı göremez), #33 ts[1]'e kaydırır
    (alan DOLU ve YANLIŞ — çok daha kötüsü: uydurma bir aralık, kanıt kılığında). Fikstürde
    ts[0] != ts[1] olduğu için ikisi de burada ölür."""
    sc._span_days(BOZUK_TRADES)

    fields = _span_fallback_kaydi(uyarilar)
    assert fields["first"] is not None, "#28: first alanı None'a düşerse aralık kaybolur"
    assert fields["first"] == ILK_TS, (
        f"#33: first EN ERKEN ts olmalı ({ILK_TS!r}), gelen {fields['first']!r} "
        f"(ikinci ts {IKINCI_TS!r} ile karıştırılıyor)")
    assert fields["first"] != IKINCI_TS


# ---------------------------------------------------------------------------------------------
# #29 / #34 / #35 — SINIR: `last` EN GEÇ ts'tir (ts[-1]), ts[1] değil, ts[-2] değil, None değil
# ---------------------------------------------------------------------------------------------
def test_m29_m34_m35_uyarinin_last_alani_en_gec_ts_olmali(uyarilar):
    """`last` = sıralanmış ts listesinin SONU.

    Üç ayrı kayma tek fikstürde ölür, çünkü dört indeks (ts[0], ts[1], ts[-2], ts[-1]) DÖRT
    FARKLI değer taşır:
      #29 None    → aralığın üst ucu kaybolur
      #34 ts[+1]  → 'en geç' yerine ikinci eleman
      #35 ts[-2]  → 'en geç' yerine sondan ikinci
    Üçü de operatöre BİÇİMSİZ OLMAYAN bir tarihi biçimsizmiş gibi gösterir — teşhis, hatayı
    içermeyen bir kayda bakarak yapılamaz."""
    sc._span_days(BOZUK_TRADES)

    fields = _span_fallback_kaydi(uyarilar)
    assert fields["last"] is not None, "#29: last alanı None'a düşerse aralığın üst ucu kaybolur"
    assert fields["last"] == SON_TS, (
        f"#34/#35: last EN GEÇ ts olmalı ({SON_TS!r}), gelen {fields['last']!r}")
    assert fields["last"] != IKINCI_TS, "#34: ts[+1] EN GEÇ değildir"
    assert fields["last"] != SONDAN_IKINCI_TS, "#35: ts[-2] EN GEÇ değildir"


def test_first_ile_last_ayni_olamaz_ve_sirali_gelir(uyarilar):
    """İki alan BİRLİKTE bir ARALIK bildirir. Aynı değere çökerlerse (ör. ikisi de ts[0] ya da
    ikisi de ts[-1]) kayıt 'aralık' olmaktan çıkar; sıralı gelmezlerse aralık ters okunur.
    #33/#34'ün ikisini birden aynı indekse kaydıran bir gelecek varyantını da kapatır."""
    sc._span_days(BOZUK_TRADES)

    fields = _span_fallback_kaydi(uyarilar)
    assert fields["first"] != fields["last"], "first ve last aynı olursa kayıt aralık bildirmiyor"
    assert fields["first"] < fields["last"], "aralık ters bildirilmiş (first > last)"


# ---------------------------------------------------------------------------------------------
# FİKSTÜR SÖZLEŞMESİNİN KENDİSİ — yukarıdaki testlerin dayandığı iki varsayım ölçülür
# ---------------------------------------------------------------------------------------------
def test_fikstur_dort_ayrik_indeks_uretir_yoksa_mutantlar_gizlenir():
    """ts[0] / ts[1] / ts[-2] / ts[-1] DÖRT FARKLI değer olmalı.

    Bu bir öz-testtir: yarın biri fikstürden bir işlem silerse #33/#34/#35 sessizce hayatta
    kalmaya başlar ve yukarıdaki testler YEŞİL kalarak hiçbir şey ölçmez. Ölçüm aracının
    kendisi ölçülmezse, ölçüm bir varsayımdır."""
    ts = []
    for t in BOZUK_TRADES:
        for k in ("ts_open", "ts_close"):
            v = t.get(k)
            if v:
                ts.append(str(v)[:10])
    ts.sort()
    assert len({ts[0], ts[1], ts[-2], ts[-1]}) == 4, f"indeksler ayrık değil: {ts}"
    assert (ts[0], ts[1], ts[-2], ts[-1]) == (ILK_TS, IKINCI_TS, SONDAN_IKINCI_TS, SON_TS)


def test_gecerli_tarihlerde_yedek_yola_hic_girilmez(uyarilar):
    """KARŞIT KUTUP: 30 günlük GEÇERLİ bir aralık da 30.0 döndürür — ama uyarı BASILMAZ.

    Yedek sabitin (30.0) meşru bir ölçümle aynı sayı olması tehlikelidir: '30.0 gördüm' demek
    'ölçtüm' demek DEĞİLDİR. İkisini ayıran tek şey uyarının varlığıdır; bu test o ayrımın
    gerçekten var olduğunu çivi ler."""
    gecerli = [{"ts_open": "2026-01-01", "ts_close": "2026-01-31"}]

    assert sc._span_days(gecerli) == 30.0                   # ÖLÇÜLMÜŞ 30 gün
    assert uyarilar == [], "geçerli tarihlerde span_days_fallback uyarısı basılmamalı"


def test_tek_tarihte_uyari_basmadan_30_doner(uyarilar):
    """len(ts) < 2 dalı ERKEN döner: try bloğuna hiç girilmez, dolayısıyla uyarı da basılmaz.
    'Bilgi yok' ile 'bilgi bozuk' aynı sayıya düşer ama aynı KAYDA düşmez."""
    assert sc._span_days([{"ts_open": "2026-01-01"}]) == 30.0
    assert sc._span_days([]) == 30.0
    assert uyarilar == []
