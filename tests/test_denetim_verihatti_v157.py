"""v157 — DENETİM 2026-08-02, VERİ HATTI kümesi: C20 + hafif-kardeşi + C25 (sayaç yarısı).

Üç hata-yolu düzeltmesini çiviler. Hiçbiri YENİ ÖZELLİK değildir; üçü de davranışı BEYAN EDİLENE
geri getirir:

  1. C20 — `_alpaca_session_bars` sembolü CEVAP GELMEDEN "soruldu" işaretliyordu. `same_evening_bars`
     arızada FIRLATMAZ ({"source": None, "bars": {}} döner) ve altındaki katmanlar chunk arızasında
     KISMİ sonuç döndürür; yani 3 chunk'ın 2.'si 429 alınca ~150 sembol "soruldu" kümesine giriyor
     ama memo'ya HİÇ girmiyordu. Defteri temizleyen üretim yolu olmadığı için o semboller SEANS
     BOYUNCA bir daha SORULAMIYORDU — bacağın kapatmak için yazıldığı SAHTE "SEANS ATLANDI"
     sınıfının ta kendisi. Yeni yasa: işaret İSTEKTEN SONRA ve yalnız CEVAPLAYAN sembollere.

  2. C20 hafif-kardeşi — bacak İSTEĞİ PATLADIĞINDA `outcomes` defterine "empty" yazılıyordu. Hüküm
     `o.startswith("error")` ile okunuyor; bacak hiçbir zaman `error:` yazmadığı için ağ arızası
     `symbol_unknown` hükmüne dönüşüyor, `_record_no_data` serisi artıyor ve 5. turda DATA_QUALITY
     "evren bakımı gerekiyor olabilir" diyordu. Yeni yasa: istisna → `error:{tip}`, gerçek boş → "empty".

  3. C25 (SAYAÇ YARISI) — `nasdaq_earnings_window` gün-başına hataları SAYISIZ yutuyordu; "20 iş
     gününün 19'u düştü" ile "hepsi geldi" çağırana AYNI şekilde görünüyordu. Yeni yasa: adaptör
     `stats` sayacını doldurur, `earnings.refresh` eksik kapsamada `earnings_refresh_window_partial`
     uyarısı basar ve sayılar `earnings_refreshed`e alan olarak geçer.
     ⚠ BU DOSYA FMP YEDEĞİNE DÜŞME EŞİĞİNİ SINAMAZ — o eşik (bugün: yalnız TAM boşluk) KOVA B'de,
     operatör kalemindedir. Aşağıdaki `test_c25_esik_degismedi` tam da eşiğin DEĞİŞMEDİĞİNİ çiviler.

KIRMIZI-ÖNCE: her testin docstring'i, düzeltme geri alındığında hangi satırın kırmızıya döneceğini
söyler; testler eski davranışı da (yanlış tarafı) açıkça yasaklar.
"""
from __future__ import annotations

import pandas as pd
import pytest

from meridian import store


# ================================================================================================
# ortak fikstür — bacak/taşıma defterleri MODÜL GLOBALİDİR (v133'ün aynı dersi, yeni dosya)
# ================================================================================================
@pytest.fixture(autouse=True)
def _reset_modul_defterleri():
    from meridian.adapters import alpaca, data
    _dicts = (data._ALPACA_MEMO, data._ALPACA_ASKED, data._ALPACA_PENDING, data._LAST_SOURCE)

    def _sifirla():
        for d in _dicts:
            d.clear()
        alpaca._DATA_FAIL_AT.clear()
        alpaca._DATA_COOLDOWN.clear()
        alpaca._DATA_LAST_FAIL.clear()
        # TAŞIMA SAYACI MUTLAKTIR ve C20 düzeltmesi ARTIŞA bakar: komşu testlerin bıraktığı sayı
        # tek başına zarar vermez ama testin ölçtüğü şeyi "sıra"ya bağlar. Yerinde temizlenir
        # (clear+update): yeni bir dict atamak `data_transport()` dışındaki referansları koparırdı.
        alpaca._DATA_TRANSPORT.clear()
        alpaca._DATA_TRANSPORT.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                                       "last_error": "", "at": None})
        data._SE = {}
        data._SE_PENDING_EVENT.clear()
        data._NO_DATA = {}

    _sifirla()
    yield
    _sifirla()


SESSION = "2026-07-29"


def _leg_faki(*, bars_for, calls=1, fails=0, source="alpaca_iex", kayit=None):
    """`alpaca.same_evening_bars` yerine geçer ve TAŞIMA SAYACINI GERÇEĞİ GİBİ oynatır.

    Gerçek uçta `calls` istek başına, `fails` arıza başına artar (`alpaca._get_data`). Kısmi chunk
    arızası = `calls` arttı + `fails` arttı + KISMİ `bars` (alpaca.snapshots: `return out or None`).
    """
    from meridian.adapters import alpaca

    def _leg(syms, session, timeout=30.0):
        istenen = [str(s).upper() for s in syms]
        if kayit is not None:
            kayit.append(tuple(istenen))
        alpaca._DATA_TRANSPORT["calls"] += calls
        alpaca._DATA_TRANSPORT["fails"] += fails
        veren = [s for s in istenen if s in set(bars_for)]
        bars = {s: {"date": session, "open": 10.0, "high": 10.0, "low": 10.0,
                    "close": 10.0, "volume": 1000.0} for s in veren}
        return {"source": (source if bars else None), "bars": bars, "detail": "test"}

    return _leg


# ================================================================================================
# 1) C20 — `asked` işareti CEVAPTAN SONRA
# ================================================================================================
def test_c20_kismi_arizada_cevapsiz_semboller_sorulmus_sayilmaz(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: `asked.update(...)` istekten ÖNCE atılırsa bu test düşer — cevapsız 150 sembol
    de "soruldu" kümesine girer. Kısmi arıza = ilk chunk cevapladı, sonrakiler 429."""
    from meridian.adapters import alpaca, data
    evren = [s.upper() for s in data._leg_universe("AAA")]
    assert len(evren) > 100, "evren tek chunk'a sığıyorsa kısmi arıza senaryosu ölçülemez"
    cevaplayan = evren[:100]

    monkeypatch.setattr(alpaca, "same_evening_bars",
                        _leg_faki(bars_for=cevaplayan, calls=3, fails=2))
    memo = data._alpaca_session_bars("AAA", SESSION)

    asked = data._ALPACA_ASKED[SESSION]
    assert asked == set(cevaplayan), "cevap dönmeyen sembol 'soruldu' işaretlendi"
    assert set(memo) == set(cevaplayan)
    eksik = set(evren) - set(cevaplayan)
    assert eksik and not (eksik & asked), f"{len(eksik)} sembol cevapsız ama işaretli"


def test_c20_sonraki_poll_cevapsiz_kalanlari_yeniden_sorar(sandbox_state, monkeypatch):
    """BACAK BİR SOĞUMA PENCERESİ KAYBEDER, BÜTÜN SEANSI DEĞİL. Kısmi arızadan sonra SAĞLIKLI bir
    sağlayıcıyla yapılan ikinci çağrı, eksik kalan sembolleri GERÇEKTEN ağa sorar."""
    from meridian.adapters import alpaca, data
    evren = [s.upper() for s in data._leg_universe("AAA")]
    cevaplayan = evren[:100]

    monkeypatch.setattr(alpaca, "same_evening_bars",
                        _leg_faki(bars_for=cevaplayan, calls=3, fails=2))
    data._alpaca_session_bars("AAA", SESSION)

    kayit: list = []
    monkeypatch.setattr(alpaca, "same_evening_bars",
                        _leg_faki(bars_for=evren, calls=3, fails=0, kayit=kayit))
    memo = data._alpaca_session_bars("AAA", SESSION)

    assert kayit, "ikinci poll AĞA HİÇ ÇIKMADI — bacak seans boyunca ölü"
    ikinci_istek = set(kayit[0])
    assert ikinci_istek == set(evren) - set(cevaplayan), "eksik küme birebir yeniden sorulmadı"
    assert set(memo) == set(evren), "ikinci tur eksikleri kapatmadı"
    assert data._ALPACA_ASKED[SESSION] == set(evren)


def test_c20_temiz_tam_cevapta_barsiz_sembol_de_sorulmus_sayilir(sandbox_state, monkeypatch):
    """TEKRAR-DÖVME YASAĞI: istek TEMİZ tamamlandıysa (calls>0, fails==0, source var) barı dönmeyen
    sembol GERÇEKTEN o seansta barsızdır — onu her `fetch`te yeniden sormak sembol-başına istek
    demek olurdu (evren TEK grupta sorulur yasasının çiğnenmesi)."""
    from meridian.adapters import alpaca, data
    evren = [s.upper() for s in data._leg_universe("AAA")]
    kayit: list = []
    monkeypatch.setattr(alpaca, "same_evening_bars",
                        _leg_faki(bars_for=evren[:1], calls=3, fails=0, kayit=kayit))

    data._alpaca_session_bars("AAA", SESSION)
    assert data._ALPACA_ASKED[SESSION] == set(evren), "temiz cevapta barsız sembol işaretlenmedi"
    # AYNI SEANSIN SONRAKİ SEMBOLLERİ: evrenin içinden seçilir — evren DIŞI bir sembol (Finviz
    # keşfi) kendi küçük isteğini yapar ve o davranış bu turda DEĞİŞMEDİ (`_leg_universe` yasası).
    data._alpaca_session_bars(evren[5], SESSION)
    data._alpaca_session_bars(evren[9], SESSION)
    assert len(kayit) == 1, "temiz cevaptan sonra ikinci bir istek atıldı (tekrar-dövme)"


def test_c20_hic_istek_cikmadiysa_hicbir_sembol_isaretlenmez(sandbox_state, monkeypatch):
    """SOĞUMA/ANAHTARSIZLIK HÂLİ: `snapshots` `_data_cooled` yüzünden None dönerse ağa HİÇ
    çıkılmamıştır (calls artmaz). "İstek atılmadı" ile "cevap geldi, bar yok" aynı sayılamaz."""
    from meridian.adapters import alpaca, data
    monkeypatch.setattr(alpaca, "same_evening_bars",
                        _leg_faki(bars_for=[], calls=0, fails=0))
    data._alpaca_session_bars("AAA", SESSION)
    assert data._ALPACA_ASKED[SESSION] == set(), "istek çıkmadan sembol 'soruldu' sayıldı"


# ================================================================================================
# 2) C20 hafif-kardeşi — `outcomes` sözleşmesi: HATA ≠ BOŞ
# ================================================================================================
def _bos_zincir(monkeypatch):
    """Zincirin TÜM kolları TEMİZ-BOŞ döner (hata değil): hüküm yalnız bacağın yazdığına kalır."""
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


def test_kardes_bacak_istegi_patlarsa_error_oneki_yazilir(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: `outcomes["alpaca"] = "empty"` kalırsa hüküm `symbol_unknown` çıkar ve ağ
    arızası "sembol öldü" kanıtına dönüşür (`_record_no_data` serisi → DATA_QUALITY)."""
    from meridian.adapters import data
    _bos_zincir(monkeypatch)

    def _patla(ticker, session):
        raise TimeoutError("uç cevap vermedi")

    monkeypatch.setattr(data, "_fetch_alpaca_session", _patla)
    with data.live_session_leg(SESSION):
        got = data.fetch("AAA", "2021-01-01", SESSION, incremental_ok=True)
    assert got.empty

    ev = _son_bos_olay()
    assert ev, "hiçbir kaynak veri vermedi ama olay basılmadı"
    assert "alpaca=error:TimeoutError" in ev["outcomes"], ev["outcomes"]
    assert ev["verdict"] == "source_error", "istek arızası sembol hakkında HÜKÜM ÜRETTİ"
    assert "alpaca" in ev["errored"]
    # SERİ ARTMAZ: `source_error` evren bakımı adayı sayacını beslemez
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 0


def test_kardes_gercek_bos_cevap_hala_empty(sandbox_state, monkeypatch):
    """AYRIMIN DİĞER YARISI: bacak DÜZGÜN çalışıp bar bulamadıysa bu bir arıza değildir — "empty"
    kalır ve hüküm `symbol_unknown` olur (evren bakımı adayı gerçekten adaydır)."""
    from meridian.adapters import data
    _bos_zincir(monkeypatch)
    monkeypatch.setattr(data, "_fetch_alpaca_session",
                        lambda ticker, session: (pd.DataFrame(), None))
    with data.live_session_leg(SESSION):
        data.fetch("AAA", "2021-01-01", SESSION, incremental_ok=True)

    ev = _son_bos_olay()
    assert ev and "alpaca=empty" in ev["outcomes"], (ev or {}).get("outcomes")
    assert ev["verdict"] == "symbol_unknown"
    assert (data._no_data_reg().get("AAA") or {}).get("streak") == 1


# ================================================================================================
# 3) C25 — gün-başına sayaç + kısmi pencere olayı
# ================================================================================================
def _json_faki(dusen_gunler: set):
    class _R:
        def __init__(self, gun):
            self._gun = gun

        def json(self):
            return {"data": {"rows": [{"symbol": "AAA", "time": "time-after-hours"}]}}

    def _get(url, timeout, attempts=3):
        gun = url.rsplit("date=", 1)[-1]
        if gun in dusen_gunler:
            raise RuntimeError(f"HTTP 403 {gun}")
        return _R(gun)

    return _get


def test_c25_adaptor_dusen_gunu_sayar(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: `except Exception: pass` sayaçsız kalırsa `stats` boş döner ve "19 gün düştü"
    ile "hepsi geldi" çağırana AYNI görünür."""
    from meridian.adapters import data
    gunler = [str(d.date()) for d in pd.bdate_range("2026-07-27", "2026-07-31")]
    dusen = set(gunler[1:4])
    monkeypatch.setattr(data, "_get_json", _json_faki(dusen))

    stats: dict = {}
    out = data.nasdaq_earnings_window("2026-07-27", "2026-07-31", polite_delay=0.0, stats=stats)

    assert stats["istenen"] == len(gunler) and stats["dusen"] == len(dusen)
    assert stats["cevaplayan"] == len(gunler) - len(dusen)
    assert set(stats["dusen_gunler"]) == dusen
    assert stats["kapsama"] == round(stats["cevaplayan"] / stats["istenen"], 4)
    assert stats["son_hata"] == "RuntimeError"
    # KISMİ SONUÇ HÂLÂ DÜRÜSTTÜR: cevaplayan günlerin satırları döner (davranış değişmedi)
    assert out["AAA"] and len(out["AAA"]) == stats["cevaplayan"]


def test_c25_stats_verilmezse_eski_sozlesme_bit_bit_ayni(sandbox_state, monkeypatch):
    """GERİYE UYUM: `stats` yardımcı ALANDIR, dönüş tipi değil — `{TICKER: [...]}` sözleşmesine
    yaslanan kayıtlı sahteler (test_wpd_kalanlar_v147, test_throughput_v7) kırılmaz."""
    from meridian.adapters import data
    monkeypatch.setattr(data, "_get_json", _json_faki(set()))
    out = data.nasdaq_earnings_window("2026-07-27", "2026-07-28", polite_delay=0.0)
    assert isinstance(out, dict) and out["AAA"] == ["2026-07-27", "2026-07-28"]


def test_c25_is_gunu_yoksa_kapsama_uydurulmaz(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: pencerede iş günü yoksa oran ÖLÇÜLEMEZ — 0,0 ya da 1,0 yazmak ölçülmemiş
    bir sayı uydurmak olurdu. None + NEDEN."""
    from meridian.adapters import data
    monkeypatch.setattr(data, "_get_json", _json_faki(set()))
    stats: dict = {}
    data.nasdaq_earnings_window("2026-08-01", "2026-08-02", polite_delay=0.0, stats=stats)  # hafta sonu
    assert stats["istenen"] == 0 and stats["kapsama"] is None
    assert stats["kapsama_yok_nedeni"]


def _nasdaq_faki(veri: dict, *, istenen=10, dusen=0):
    def _f(s, e, **k):
        st = k.get("stats")
        if st is not None:
            st.update(istenen=istenen, cevaplayan=istenen - dusen, dusen=dusen,
                      dusen_gunler=[f"2026-07-{20 + i:02d}" for i in range(dusen)],
                      son_hata=("FetchError" if dusen else None),
                      kapsama=(round((istenen - dusen) / istenen, 4) if istenen else None),
                      kapsama_yok_nedeni=None)
        return veri

    return _f


def _olay(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if (e.get("event") or e.get("kind")) == ad]


def test_c25_kismi_pencere_uyari_basar(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: sayaç okunmazsa KISMİ tur sessizce "başarı" sayılır — `earnings_refreshed`
    yalnız new_rows/total basıyordu ve kaç gün-diliminin kaçtığı HİÇBİR yerde yoktu."""
    from meridian import earnings
    from meridian.adapters import data as da
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=20, dusen=19))
    n = earnings.refresh(["AAA"])
    assert n == 1

    ev = _olay("earnings_refresh_window_partial")
    assert ev, "kısmi pencere SESSİZ geçti"
    assert ev[-1]["dusen"] == 19 and ev[-1]["cevaplayan"] == 1 and ev[-1]["istenen"] == 20
    assert ev[-1]["kapsama"] == 0.05 and ev[-1]["source"] == "nasdaq"
    assert len(ev[-1]["detail"]) >= 20

    ref = _olay("earnings_refreshed")
    assert ref and ref[-1]["gun_dusen"] == 19 and ref[-1]["gun_kapsama"] == 0.05
    assert ref[-1]["gun_olcum_yok"] is None


def test_c25_tam_pencerede_uyari_yok(sandbox_state, monkeypatch):
    """GÜRÜLTÜ YASAĞI: her tazelemede uyarı basan bir dedektör okunmaz hâle gelir."""
    from meridian import earnings
    from meridian.adapters import data as da
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=20, dusen=0))
    earnings.refresh(["AAA"])
    assert not _olay("earnings_refresh_window_partial")
    ref = _olay("earnings_refreshed")
    assert ref[-1]["gun_kapsama"] == 1.0 and ref[-1]["gun_dusen"] == 0


def test_c25_sayac_dolmazsa_kapsama_olculmedi_der(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: sahte/eski bir adaptör `stats`e dokunmazsa kapsama ÖLÇÜLMEMİŞTİR — olay
    "tam" DEMEZ, None + NEDEN yazar."""
    from meridian import earnings
    from meridian.adapters import data as da
    monkeypatch.setattr(da, "nasdaq_earnings_window", lambda s, e, **k: {"AAA": ["2026-08-05"]})
    earnings.refresh(["AAA"])
    assert not _olay("earnings_refresh_window_partial")
    ref = _olay("earnings_refreshed")
    assert ref[-1]["gun_kapsama"] is None and ref[-1]["gun_cevaplayan"] is None
    assert ref[-1]["gun_olcum_yok"]


def test_c25_esik_degismedi_kismi_pencere_hala_fmpye_dusmez(sandbox_state, monkeypatch):
    """KOVA B ÇİVİSİ: FMP yedeğine düşme eşiği OPERATÖR KARARIDIR ve bu tur DEĞİŞMEDİ. Kısmi
    pencere (19/20 gün düştü) hâlâ FMP'yi ÇAĞIRMAZ; eklenen tek şey görünürlüktür. Bu test bir
    gün eşik bilinçli değiştirilirse KIRILARAK haber verir — sessiz kota sürüklenmesi olmaz."""
    from meridian import earnings
    from meridian.adapters import data as da
    cagrildi: list = []
    monkeypatch.setattr(earnings, "refresh_from_fmp", lambda t: cagrildi.append(t) or 7)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=20, dusen=19))
    n = earnings.refresh(["AAA"])
    assert cagrildi == [], "kısmi pencerede FMP yedeğine düşüldü — eşik sessizce değişmiş"
    assert n == 1

    # TAM BOŞLUK HÂLÂ YEDEĞE DÜŞER (eşiğin diğer ucu bozulmadı)
    monkeypatch.setattr(da, "nasdaq_earnings_window", _nasdaq_faki({}, istenen=20, dusen=20))
    assert earnings.refresh(["AAA"]) == 7 and cagrildi
