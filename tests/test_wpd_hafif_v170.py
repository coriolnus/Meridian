"""v170 — WP-D VERİ-HATTI HAFİF KÜMESİ (denetim 2026-08-02 + ROADMAP küçük-kuyruk).

Dört beyan-davranış ayrışmasını çiviler. Hiçbiri YENİ ÖZELLİK değildir; dördü de davranışı
BEYAN EDİLENE geri getirir:

  1. `gap_scan` beklentiyi TATİL/YARIM GÜN bilmeyen `barclock.is_market_open`tan üretiyordu.
     O fonksiyonun kendi gerekçesi ("Alpaca zaten kapalıyken bar göndermez, bu yalnız bir KOLAYLIK
     kapısıdır") `is_admissible` için doğru, `gap_scan` için TERSİNE ÇEVRİLMİŞTİR: burada semantik
     "bar YOKSA kesinti VAR"dır. NYSE yarım günlerinde (13:00 ET) dosya vardır ama pencere kapanış
     sonrasına düşer → SAHTE `intraday_gap_detected`. Yeni yasa: beklenti XNYS `schedule()`ün
     GERÇEK market_open/market_close aralığından; takvim okunamazsa `durum="takvim_yok"` (hüküm yok).

  2. Aynı-akşam bacağının İKİNCİ "HATA ≠ BOŞ" deliği. C20 kardeşi yalnız FIRLATAN yolu kapatmıştı;
     `alpaca.same_evening_bars` arızada FIRLATMAZ ({"source": None, "bars": {}}), yani 429/soğuma
     hâlinde `outcomes`a hâlâ "empty" yazılıyordu → `symbol_unknown` hükmü → `_record_no_data`
     serisi → DATA_QUALITY "evren bakımı". Yeni yasa: calls/fails deltası `_fetch_alpaca_session`
     üzerinden taşınır ve arıza `error:` sınıfına yazılır.

  3. `bars_integrity_written` olayı `dataset.load_cached`i "güvensiz dönemi dışlayanlar" arasında
     sayıyordu; `data.measurement_bars` docstring'i (GERÇEK KAYNAK) bunu ölçülmüş gerekçeyle
     reddediyor. Yeni yasa: olay hangi yolların HÂLÂ kirli dönemi GÖRDÜĞÜNÜ aynı satırda yazar.

  4. Kazanç takvimi birleştirme semantiği İKİ DALDA FARKLI ve ikisi de yanlış taraftaydı:
     (i) Nasdaq dalı yalnız EKLİYOR, revize edilen tarihi EMEKLİYE AYIRMIYORDU (hayalet karartma +
     şişen future_dates); (ii) FMP dalı başarıyla çekilen ticker'ın birikmiş tarihlerini SESSİZCE
     düşürüyordu ("kaynak değişimi geçmiş çapaları silmez" beyanının tam ihlali).

KIRMIZI-ÖNCE: her testin docstring'i düzeltme geri alındığında hangi satırın kırmızıya döneceğini
söyler. KARARTMA ETKİSİ AYRICA ÖLÇÜLÜR (§4 testleri `in_blackout`u iki yönde de çiviler): bu depoda
karartmanın DARALMASI yasaktır; daralan tek şey kaynağın KENDİSİNİN geri çektiği hayalet tarihtir ve
o da yalnız TAM kapsamalı bir pencerede.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from meridian import store

UTC = dt.timezone.utc


# ================================================================================================
# 1) gap_scan — beklenti GERÇEK seans aralığından
# ================================================================================================
# 2025-11-28 = Şükran ertesi YARIM GÜN (13:00 ET = 18:00 UTC kapanış) · 2025-11-26 = TAM gün.
# İkisi de GERÇEK takvimden okunur (fikstür uydurmaz): dedektörün bağlandığı kaynak sınanmalı.
YARIM_GUN = "2025-11-28"
TAM_GUN = "2025-11-26"


@pytest.fixture(autouse=True)
def _seans_onbellegi_temiz():
    """`_SEANS_CACHE` MODÜL GLOBALİDİR — bir testin taktığı sahte gün sonrakine sızarsa test kendi
    kurmadığı takvimle 'geçiyor' görünür (v133'ün aynı dersi)."""
    from meridian import barsarchive
    barsarchive._SEANS_CACHE.clear()
    yield
    barsarchive._SEANS_CACHE.clear()


def _dakikalar(ilk: dt.datetime, n: int) -> list:
    return [ilk + dt.timedelta(minutes=i) for i in range(n)]


def _satirlar(dakikalar, ticker="AAA") -> list:
    return [(ticker, m.isoformat().replace("+00:00", "Z")) for m in dakikalar]


def test_seans_araligi_yarim_gunu_GERCEK_takvimden_okur():
    """ÇİVİNİN ÇİVİSİ: `_seans_araligi` XNYS `schedule()`e bağlı olmasaydı aşağıdaki yarım gün
    16:00 ET kapanışı gibi görünürdü. Üç hâl AYRI ADLA döner (ok / seans_disi / takvim_yok)."""
    from meridian import barsarchive
    durum, ac, kap, hata = barsarchive._seans_araligi(YARIM_GUN)
    assert durum == "ok" and hata is None
    assert ac.astimezone(UTC).strftime("%H:%M") == "14:30"
    assert kap.astimezone(UTC).strftime("%H:%M") == "18:00", "yarım gün kapanışı GERÇEK değil"

    durum2, _a2, _k2, _h2 = barsarchive._seans_araligi(TAM_GUN)
    assert durum2 == "ok" and _k2.astimezone(UTC).strftime("%H:%M") == "21:00"

    # TAM TATİL: takvim OKUNDU ve o gün seans değil — "takvim_yok" ile karışmaz
    assert barsarchive._seans_araligi("2025-12-25")[0] == "seans_disi"


def test_yarim_gunde_SAHTE_akis_kesintisi_ALARMI_BASMAZ(sandbox_state):
    """KIRMIZI-ÖNCE: beklenti `barclock.is_market_open`tan üretilirse bu test düşer — 18:00 UTC
    kapanışından SONRAKİ 48 dakika da 'beklenen' sayılır, `dolu` onları taşımaz ve `tur="akis"`
    boşluğu doğar (scheduler bunu `intraday_gap_detected` diye basar: 'o dakikalar geri gelmez')."""
    from meridian import barsarchive
    as_of = dt.datetime(2025, 11, 28, 18, 50, tzinfo=UTC)      # kapanıştan 50 dk SONRA
    # Pencere 17:48–18:48; seansın İÇİNDE kalan tek dilim 17:48–17:59 (12 dk) ve o dilim DOLU.
    dolu = _dakikalar(dt.datetime(2025, 11, 28, 17, 48, tzinfo=UTC), 12)
    rapor = barsarchive.gap_scan(as_of=as_of, day=YARIM_GUN, rows=_satirlar(dolu))

    assert rapor["durum"] == "ok"
    assert rapor["pencere"]["beklenen_dk"] == 12, "beklenti kapanış SONRASINI da saydı"
    assert rapor["bosluk_sayisi"] == 0, f"SAHTE kesinti alarmı: {rapor['bosluklar']}"
    assert rapor["seans"]["kapanis"].endswith("18:00:00+00:00")


def test_yarim_gunde_GERCEK_kesinti_HALA_yakalanir(sandbox_state):
    """DEDEKTÖR KÖRELMEDİ: yarım günün AÇIK olduğu dakikalarda gerçekten bar gelmediyse boşluk
    yine raporlanır. Sahte alarmı susturmak, gerçek alarmı susturmakla aynı şey değildir."""
    from meridian import barsarchive
    as_of = dt.datetime(2025, 11, 28, 18, 50, tzinfo=UTC)
    dolu = _dakikalar(dt.datetime(2025, 11, 28, 17, 48, tzinfo=UTC), 4)   # 17:52–17:59 SUSTU (8 dk)
    rapor = barsarchive.gap_scan(as_of=as_of, day=YARIM_GUN, rows=_satirlar(dolu))

    akis = [b for b in rapor["bosluklar"] if b["tur"] == "akis"]
    assert akis and akis[0]["eksik_dk"] == 8, rapor["bosluklar"]


def test_tam_gunde_gercek_kesinti_yakalanir_ve_davranis_AYNI(sandbox_state):
    """REGRESYON: değişiklik yalnız TAKVİM kaynağıdır. Normal bir seansta 9:30-16:00 beklentisi
    XNYS ile birebir aynıdır — tam gün davranışı bit-bit korunmalı."""
    from meridian import barsarchive
    as_of = dt.datetime(2025, 11, 26, 19, 0, tzinfo=UTC)       # seans İÇİ (kapanış 21:00 UTC)
    baslangic = dt.datetime(2025, 11, 26, 17, 58, tzinfo=UTC)  # pencere 17:58–18:58 (60 dk)
    tum = _dakikalar(baslangic, 60)
    rapor = barsarchive.gap_scan(as_of=as_of, day=TAM_GUN, rows=_satirlar(tum))
    assert rapor["pencere"]["beklenen_dk"] == 60 and rapor["bosluk_sayisi"] == 0

    delikli = tum[:20] + tum[32:]                              # ortadan 12 dk kesildi
    rapor2 = barsarchive.gap_scan(as_of=as_of, day=TAM_GUN, rows=_satirlar(delikli))
    akis = [b for b in rapor2["bosluklar"] if b["tur"] == "akis"]
    assert akis and akis[0]["eksik_dk"] == 12, rapor2["bosluklar"]


def test_takvim_okunamazsa_HUKUM_VERILMEZ(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI + KAPATILAN DELİĞİN GERİ AÇILMAMASI: takvim düşerse `is_market_open`a geri
    düşmek yarım-gün deliğini aynen geri açardı. Ölçülemeyen şey None'dır — `durum="takvim_yok"`,
    hiçbir boşluk raporlanmaz ve NEDEN raporda durur.

    KIRMIZI-ÖNCE: yedek beklenti üretilirse `bosluk_sayisi` 0'dan büyür (pencerede hiç bar yok)."""
    import sys
    from meridian import barsarchive

    class _Patlak:
        @staticmethod
        def get_calendar(_ad):
            raise RuntimeError("takvim modülü yok")

    monkeypatch.setitem(sys.modules, "pandas_market_calendars", _Patlak)
    as_of = dt.datetime(2025, 11, 26, 19, 0, tzinfo=UTC)
    rapor = barsarchive.gap_scan(as_of=as_of, day=TAM_GUN, rows=[])

    assert rapor["durum"] == "takvim_yok"
    assert rapor["bosluk_sayisi"] == 0 and rapor["bosluklar"] == []
    assert rapor["pencere"]["beklenen_dk"] == 0
    assert "RuntimeError" in (rapor["seans"]["hata"] or ""), "neden kaydedilmedi"
    # ARIZA ÖNBELLEĞE ALINMAZ: takvim geri geldiğinde gün yeniden ölçülebilmeli
    assert TAM_GUN not in barsarchive._SEANS_CACHE


# ================================================================================================
# 2) aynı-akşam bacağı — İKİNCİ "HATA ≠ BOŞ" deliği (fırlatmayan taşıma arızası)
# ================================================================================================
SESSION = "2026-07-29"


@pytest.fixture(autouse=True)
def _bacak_defterleri():
    """Bacak/taşıma defterleri MODÜL GLOBALİDİR; taşıma sayacı MUTLAKtır ve düzeltme ARTIŞA bakar."""
    from meridian.adapters import alpaca, data

    def _sifirla():
        for d in (data._ALPACA_MEMO, data._ALPACA_ASKED, data._ALPACA_PENDING, data._LAST_SOURCE):
            d.clear()
        alpaca._DATA_FAIL_AT.clear()
        alpaca._DATA_COOLDOWN.clear()
        alpaca._DATA_LAST_FAIL.clear()
        alpaca._DATA_TRANSPORT.clear()
        alpaca._DATA_TRANSPORT.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                                       "last_error": "", "at": None})
        data._SE = {}
        data._SE_PENDING_EVENT.clear()
        data._NO_DATA = {}

    _sifirla()
    yield
    _sifirla()


def _leg_faki(*, bars_for, calls=1, fails=0, source="alpaca_iex"):
    """`alpaca.same_evening_bars` yerine geçer ve TAŞIMA SAYACINI GERÇEĞİ GİBİ oynatır (v157 deseni:
    `calls` istek başına, `fails` arıza başına artar — `alpaca._get_data`)."""
    from meridian.adapters import alpaca

    def _leg(syms, session, timeout=30.0):
        istenen = [str(s).upper() for s in syms]
        alpaca._DATA_TRANSPORT["calls"] += calls
        alpaca._DATA_TRANSPORT["fails"] += fails
        veren = [s for s in istenen if s in set(bars_for)]
        bars = {s: {"date": session, "open": 10.0, "high": 10.0, "low": 10.0,
                    "close": 10.0, "volume": 1000.0} for s in veren}
        return {"source": (source if bars else None), "bars": bars, "detail": "test"}

    return _leg


def _bos_zincir(monkeypatch):
    """Zincirin TÜM kolları TEMİZ-BOŞ döner: hüküm YALNIZ bacağın yazdığına kalır."""
    from meridian.adapters import alpaca, data, fmp, massive
    monkeypatch.setattr(massive, "available", lambda: False)
    monkeypatch.setattr(massive, "write_enabled", lambda: False)
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(alpaca, "data_available", lambda: True)


def _son_bos_olay() -> dict | None:
    ev = [e for e in store.read_jsonl("events.jsonl")
          if (e.get("event") or e.get("kind")) == "bar_sources_all_empty"]
    return ev[-1] if ev else None


def _bacagi_kos(monkeypatch, leg):
    from meridian.adapters import alpaca, data
    _bos_zincir(monkeypatch)
    monkeypatch.setattr(alpaca, "same_evening_bars", leg)
    with data.live_session_leg(SESSION):
        return data.fetch("AAA", "2021-01-01", SESSION, incremental_ok=True)


def test_firlatmayan_tasima_arizasi_error_sinifina_yazilir(sandbox_state, monkeypatch):
    """ROADMAP KÜÇÜK-KUYRUK: `same_evening_bars` 429'da FIRLATMAZ, `{"source": None, "bars": {}}`
    döner. Eski kodda `_leg_err` None kalıyor ve `outcomes["alpaca"] = "empty"` yazılıyordu; hüküm
    `symbol_unknown` çıkıyor, `_record_no_data` serisi artıyor ve 5. turda DATA_QUALITY 'evren
    bakımı gerekiyor olabilir' diyordu — yani AĞ ARIZASI 'sembol öldü' kanıtına dönüşüyordu.

    KIRMIZI-ÖNCE: calls/fails deltası taşınmazsa `outcomes` yine "empty" olur."""
    from meridian.adapters import data
    got = _bacagi_kos(monkeypatch, _leg_faki(bars_for=[], calls=3, fails=2))
    assert got.empty

    ev = _son_bos_olay()
    assert ev, "hiçbir kaynak veri vermedi ama olay basılmadı"
    assert "alpaca=error:transport_fail:2/3" in ev["outcomes"], ev["outcomes"]
    assert ev["verdict"] == "source_error", "taşıma arızası sembol hakkında HÜKÜM ÜRETTİ"
    assert "alpaca" in ev["errored"]
    # SERİ ARTMAZ: `source_error` evren-bakımı adayı sayacını BESLEMEZ
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 0


def test_aga_hic_cikilmadiysa_ayri_ad_ve_yine_error(sandbox_state, monkeypatch):
    """SOĞUMA/ANAHTARSIZLIK: `calls` hiç artmadıysa istek AĞA ÇIKMAMIŞTIR. 'İstek atılmadı' ile
    'cevap geldi, bar yok' aynı sayılamaz (C20'nin `asked` yasasının bu koldaki karşılığı)."""
    from meridian.adapters import data
    _bacagi_kos(monkeypatch, _leg_faki(bars_for=[], calls=0, fails=0))
    ev = _son_bos_olay()
    assert "alpaca=error:transport_no_call" in ev["outcomes"], ev["outcomes"]
    assert ev["verdict"] == "source_error"
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 0


def test_istek_gitti_ama_hicbir_katman_servis_etmediyse_de_hukum_yok(sandbox_state, monkeypatch):
    """ÜÇÜNCÜ SINIF: `source is None` — sip atlandı, iex de boş döndü. C20 bu hâli 'temiz tam cevap'
    SAYMIYOR (sembolleri `asked`e yazmıyor); aynı yasa burada da geçerli olmalı, yoksa aynı olgu
    iki yerde iki farklı hükme bağlanırdı (bu deponun baskın kusuru)."""
    from meridian.adapters import data
    _bacagi_kos(monkeypatch, _leg_faki(bars_for=[], calls=3, fails=0, source=None))
    ev = _son_bos_olay()
    assert "alpaca=error:transport_no_source" in ev["outcomes"], ev["outcomes"]
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 0


def test_TEMIZ_tam_cevapta_barsizlik_HALA_empty(sandbox_state, monkeypatch):
    """AYRIMIN DİĞER YARISI (kapı iki yönden sınanır): istek TEMİZ tamamlandıysa (calls>0, fails==0,
    source var) barı dönmeyen sembol GERÇEKTEN o seansta barsızdır — "empty" kalır ve hüküm
    `symbol_unknown` olur. Her barsızlığı `error:` saymak, evren bakımı sinyalini yok ederdi."""
    from meridian.adapters import data
    _bacagi_kos(monkeypatch, _leg_faki(bars_for=[data.INDEX_SYMBOL], calls=3, fails=0))
    ev = _son_bos_olay()
    assert "alpaca_iex=empty" in ev["outcomes"] or "alpaca=empty" in ev["outcomes"], ev["outcomes"]
    assert ev["verdict"] == "symbol_unknown", "temiz cevap arıza sayıldı — evren bakımı körelir"
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 1


def test_tek_yasa_iki_tuketici(sandbox_state):
    """YAPISAL ÇİVİ: `asked` işareti ile `outcomes` hükmü AYNI ölçütten (`_leg_temiz_cevap`) okunur.
    İki kopya yazılsaydı biri güncellenip diğeri unutulurdu — C20'de tam olarak bu oldu."""
    import inspect
    from meridian.adapters import data
    assert data._leg_temiz_cevap("alpaca_iex", 3, 0) is True
    assert data._leg_temiz_cevap(None, 3, 0) is False
    assert data._leg_temiz_cevap("alpaca_iex", 0, 0) is False
    assert data._leg_temiz_cevap("alpaca_iex", 3, 1) is False
    assert "_leg_temiz_cevap" in inspect.getsource(data._alpaca_session_bars), \
        "C20 kolu ölçütü ADIYLA okumuyor — ikinci kopya sızmış"


# ================================================================================================
# 3) barrepair — `bars_integrity_written` olayının BEYANI
# ================================================================================================
def test_integrity_olayi_dataset_yolunu_temiz_ILAN_ETMEZ(sandbox_state):
    """KIRMIZI-ÖNCE: olay metni `dataset.load_cached`i dışlayanlar arasında sayarsa bu test düşer.
    GERÇEK KAYNAK `data.measurement_bars` docstring'idir ve 'dataset YOLU BİLEREK BAĞLANMADI …
    walk-forward/prescreen/reflect tabloları HÂLÂ kirli dönemi görüyor' der. Yanlış beyan tam da
    türetilmiş artefaktların yeniden üretilip üretilmeyeceğine karar veren satırdaydı."""
    from meridian import barrepair
    from meridian.adapters import data

    barrepair.integrity_apply({"taranan": 1, "sembol_sayisi": 1, "kirilma_sayisi": 1,
                               "dislanan_bar_toplam": 5, "semboller": {}})
    ev = [e for e in store.read_jsonl("events.jsonl")
          if (e.get("event") or e.get("kind")) == "bars_integrity_written"]
    assert ev, "olay basılmadı"
    d = ev[-1]["detail"]
    assert "component_ic" in d and "cf_backfill" in d
    assert "dataset.load_cached" in d, "hangi yolun HÂLÂ kirli gördüğü söylenmiyor"
    # SIRA TAŞIYICIDIR: `dataset.*` "DIŞLAYAN" değil "HÂLÂ ... GÖREN" cümlesinde geçmeli
    assert d.index("DIŞLAYAN") < d.index("component_ic") < d.index("dataset.load_cached")
    assert "HÂLÂ" in d and d.index("HÂLÂ") < d.index("dataset.load_cached")
    # GERÇEK KAYNAK YERİNDE DURUYOR (iki beyan bir daha ayrışmasın)
    assert "BİLEREK BAĞLANMADI" in (data.measurement_bars.__doc__ or "")


# ================================================================================================
# 4) kazanç takvimi — İKİ DAL, TEK BİRLEŞTİRME YASASI
# ================================================================================================
BUGUN = dt.date.today()


def _g(n: int) -> str:
    return (BUGUN + dt.timedelta(days=n)).isoformat()


def _takvim(sandbox_state, satirlar) -> None:
    from meridian import earnings
    metin = "ticker,date,time\n" + "".join(f"{t},{d},{tm or ''}\n" for t, d, tm in satirlar)
    (sandbox_state / "earnings.csv").write_text(metin)
    earnings.clear_cache()


def _nasdaq_faki(veri: dict, *, istenen=20, dusen=0):
    """Adaptörün `stats` sözleşmesini birebir taklit eder (bkz. data.nasdaq_earnings_window)."""
    def _f(s, e, **k):
        st = k.get("stats")
        if st is not None:
            st.update(istenen=istenen, cevaplayan=istenen - dusen, dusen=dusen,
                      dusen_gunler=[f"2026-07-{20 + i:02d}" for i in range(min(dusen, 8))],
                      son_hata=("FetchError" if dusen else None),
                      kapsama=(round((istenen - dusen) / istenen, 4) if istenen else None),
                      kapsama_yok_nedeni=(None if istenen else "pencerede iş günü yok"))
        return veri
    return _f


def _olay(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if (e.get("event") or e.get("kind")) == ad]


def test_nasdaq_dali_ILERI_yonlu_revizyonu_EMEKLIYE_AYIRIR(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: dal 'yalnız EKLE' kalırsa hayalet tarih dosyada sonsuza dek durur; `in_blackout`
    OLMAYAN bir rapor için karartma uygular, `coverage().future_dates` şişer ve hayalet ertesi gün
    GEÇMİŞ çapaya (PEAD) dönüşür. Kaynak TAM kapsamalı pencerede o tarihi artık bildirmiyorsa
    'geri çekti' demektir — tek meşru silme budur."""
    from meridian import earnings
    from meridian.adapters import data as da
    hayalet, yeni = _g(5), _g(12)
    _takvim(sandbox_state, [("AAA", _g(-10), None), ("AAA", _g(-3), None),
                            ("AAA", hayalet, "amc"), ("AAA", _g(40), None)])
    assert earnings.in_blackout("AAA", _g(3)) is True          # ÖNCE: hayalet karartıyordu

    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [(yeni, "amc")]}, istenen=20, dusen=0))
    earnings.refresh(["AAA"])
    earnings.clear_cache()
    takvim = earnings._load()["AAA"]

    assert hayalet not in takvim, "revize edilen GELECEK tarih emekliye ayrılmadı"
    assert yeni in takvim, "kaynağın YENİ tarihi yazılmadı"
    # GEÇMİŞ SİLİNMEZ (modülün sözü): iki geçmiş çapa da yerinde
    assert _g(-10) in takvim and _g(-3) in takvim
    # PENCERE DIŞI GELECEK DE SİLİNMEZ: o gün kaynağa HİÇ sorulmadı, yokluğu kanıt değil
    assert _g(40) in takvim

    # KARARTMA ETKİSİ SAYILI: hayaletin karartması gitti, gerçek tarihinki geldi
    assert earnings.in_blackout("AAA", _g(3)) is False
    assert earnings.in_blackout("AAA", _g(10)) is True

    ev = _olay("earnings_future_revision_retired")
    assert ev and ev[-1]["satir"] == 1 and ev[-1]["sembol"] == 1
    assert f"AAA:{hayalet}" in ev[-1]["ornek"] and len(ev[-1]["detail"]) >= 20
    assert _olay("earnings_refreshed")[-1]["emekli_satir"] == 1


def test_KISMI_pencerede_emeklilik_KOSMAZ(sandbox_state, monkeypatch):
    """KARARTMA DARALMASI YASAĞININ KAPISI: kısmi pencerede bir tarihin yokluğu revizyon DEĞİL,
    kaçan gün-dilimi olabilir. Onu silmek gerçek bir rapor tarihini yok eder ve motor bilanço
    gününe pozisyonla girer — bu modülün en pahalı hata sınıfı.

    KIRMIZI-ÖNCE: kapsama kapısı kaldırılırsa hayalet düşer ve karartma DARALIR."""
    from meridian import earnings
    from meridian.adapters import data as da
    hayalet = _g(5)
    _takvim(sandbox_state, [("AAA", hayalet, None)])
    # kapsama 0,90 = TAM eşikte → FMP yedeği de tetiklenmez (bu test yalnız emekliliği ölçer)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [(_g(12), None)]}, istenen=20, dusen=2))
    earnings.refresh(["AAA"])
    earnings.clear_cache()

    assert hayalet in earnings._load()["AAA"], "KISMİ pencerede hayalet düşürüldü — karartma DARALDI"
    assert not _olay("earnings_future_revision_retired")
    assert _olay("earnings_refreshed")[-1]["emekli_satir"] == 0


def test_olculemeyen_kapsamada_emeklilik_KOSMAZ(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: `kapsama=None` bir sayı değildir. Sayaç doldurmayan eski/sahte bir adaptör
    (kayıtlı testler bunu kullanıyor) sessizce takvim silmeye yol açmamalı."""
    from meridian import earnings
    from meridian.adapters import data as da
    hayalet = _g(5)
    _takvim(sandbox_state, [("AAA", hayalet, None)])
    monkeypatch.setattr(da, "nasdaq_earnings_window", lambda s, e, **k: {"AAA": [_g(12)]})
    earnings.refresh(["AAA"])
    earnings.clear_cache()
    assert hayalet in earnings._load()["AAA"]


def test_kaynagin_SUSTUGU_sembol_dokunulmaz(sandbox_state, monkeypatch):
    """DAR KAPSAM, BİLEREK: tarihi pencerenin TAMAMEN dışına kayan sembol kaynaktan hiç dönmez.
    'Kaynak sustu' ile 'kaynak geri çekti' AYNI KANIT DEĞİLDİR — susan sembolün tarihi KALIR."""
    from meridian import earnings
    from meridian.adapters import data as da
    _takvim(sandbox_state, [("AAA", _g(5), None), ("BBB", _g(6), None)])
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [(_g(12), None)]}, istenen=20, dusen=0))
    earnings.refresh(["AAA", "BBB"])
    earnings.clear_cache()
    takvim = earnings._load()
    assert _g(5) not in takvim["AAA"], "konuşan sembolün hayaleti kaldı"
    assert takvim["BBB"] == [_g(6)], "SUSAN sembolün tarihi silindi — kanıtsız daraltma"
    assert earnings.in_blackout("BBB", _g(4)) is True


def test_fmp_dali_UST_KUME_yazar(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: `refresh_from_fmp` yalnız `failed` ticker'ların satırlarını kurtarırsa,
    BAŞARIYLA çekilen AAA'nın Nasdaq'tan birikmiş tarihi yazımdan sessizce DÜŞER — docstring'in
    'kaynak değişimi geçmiş çapaları silmez' cümlesi tam da kaynak değişimi anında ihlal edilirdi
    (`days_since_report` körelir, karartma o tarihte fail-open'a düşerdi)."""
    from meridian import earnings
    from meridian.adapters import fmp
    birikmis, fmp_tarih = _g(6), _g(14)
    _takvim(sandbox_state, [("AAA", birikmis, "amc"), ("OLD", _g(9), "bmo")])
    assert earnings.in_blackout("AAA", _g(4)) is True

    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "earnings_dates", lambda t, strict=False: [fmp_tarih])
    n = earnings.refresh_from_fmp(["AAA"])
    earnings.clear_cache()
    takvim = earnings._load()

    assert birikmis in takvim["AAA"], "BAŞARILI ticker'ın birikmiş tarihi FMP yazımıyla düştü"
    assert fmp_tarih in takvim["AAA"], "FMP satırı eklenmedi"
    assert takvim.get("OLD") == [_g(9)], "hiç istenmeyen sembolün çapası düştü"
    assert earnings.report_time("AAA", birikmis) == "amc", "saat sütunu kayboldu"
    assert earnings.report_time("OLD", _g(9)) == "bmo"
    # KARARTMA GENİŞLEMESİ (fail-open KAPANDI) — ölçülü: iki tarih de artık karartıyor
    assert earnings.in_blackout("AAA", _g(4)) is True
    assert earnings.in_blackout("AAA", _g(12)) is True
    # DÖNÜŞ SÖZLEŞMESİ DEĞİŞMEDİ: "bu turda elde edilen satır" (dosya toplamı DEĞİL)
    assert n == 1, "dönüş değeri dosya toplamına kaydı — scheduler nabzı ve `if not n` kapısı bozulur"


def test_fmp_dali_bos_donerse_dosyaya_DOKUNMAZ(sandbox_state, monkeypatch):
    """REGRESYON: FMP hiç satır döndürmezse (anahtar yok / kota) dosya YAZILMAZ. Üst küme kuralı
    'her çağrıda yeniden yaz' demek değildir; yazımsız yol PIT defterine de satır atmamalı."""
    from meridian import earnings
    from meridian.adapters import fmp
    _takvim(sandbox_state, [("AAA", _g(6), "amc")])
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "earnings_dates", lambda t, strict=False: [])
    assert earnings.refresh_from_fmp(["AAA"]) == 0
    earnings.clear_cache()
    assert earnings._load()["AAA"] == [_g(6)]
    assert not store.read_jsonl(earnings.SNAPSHOT_FILE)


def test_karartma_semantigi_DEGISMEDI(sandbox_state):
    """KAPSAM ÇİVİSİ: bu tur BİRLEŞTİRME yasasına dokundu, KARAR yasasına değil. `in_blackout`ın
    kendisi (pencere, BMO daraltması) bit-bit aynı kalmalı."""
    from meridian import earnings
    assert earnings.BLACKOUT_DAYS == 5 and earnings.TIME_TIGHTEN is False
    _takvim(sandbox_state, [("AAA", "2026-08-20", "bmo")])
    assert earnings.in_blackout("AAA", "2026-08-16") is True     # 4 gün önce
    assert earnings.in_blackout("AAA", "2026-08-14") is False    # 6 gün önce
    assert earnings.in_blackout("AAA", "2026-08-20") is True     # rapor günü (TIME_TIGHTEN kapalı)
    assert earnings.in_blackout("YOK", "2026-08-16") is False    # kapsam dışı → beyanlı fail-open


def test_iki_dal_da_refresh_docstringinde_BEYANLI():
    """YASA: beyan kodla eşitlenir. Denetimin bulduğu kusur 'docstring yalnız BİR dalı anlatıyor'du;
    beyan geri çekilirse bir sonraki tur aynı ayrışmayı yeniden üretir."""
    import inspect
    from meridian import earnings
    d = inspect.getdoc(earnings.refresh) or ""
    assert "NASDAQ DALI" in d and "FMP DALI" in d
    assert "GEÇMİŞ ÇAPALAR KALIR" in d
    assert "ÜST KÜME" in d and "kapsaması TAM" in d
    fd = inspect.getdoc(earnings.refresh_from_fmp) or ""
    assert "ÜST KÜMEDİR" in fd and "DÖNÜŞ DEĞERİ DEĞİŞMEDİ" in fd
