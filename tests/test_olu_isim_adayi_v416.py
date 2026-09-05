"""v416 — TSK-153: ÖLÜ-İSİM (DELİST) ADAY SENSÖRÜ — SON BAR YAŞI (2026-09-05).

KÖK (TSK-143 keşfi): `adapters.data._record_no_data` streak'i YALNIZ verdict=='symbol_unknown'
(her kaynak SIFIR satır) artırır; sağlayıcı TARİHSEL satır döndürünce sıfırlanır. EA 2026-08-04
delist oldu ama 4 hafta LIVE fetch'inde kaldı — delist tespiti o turda YALNIZ endeks-sapması
alarmının yan etkisiydi ve TSK-143'ün beyanlı kümesi (`EVREN_DISI_BEYANLI`) o yan etkiyi tam da
YENİ komşuları (10 sembol) için KAPATTI (kendi bedel beyanı: "biri delist olursa universe_drift
onu GÖRMEZ").

SÖZLEŞME (bu dosya çiviler):
  * `watchdog.olu_isim_adaylari()` → `{adaylar, zaten_emekli, olculemedi, esik, n_tarandi, bugun,
    takvim_var}`. Evren = `LIVE_UNIVERSE ∪ REPLAY_UNIVERSE ∪ RETIRED_SYMBOLS ∪ EVREN_DISI_BEYANLI`
    (dördü de TARANIR — kör nokta tam burada kapanıyor). Her sembolün YEREL bar arşivindeki
    (`data._cache_path`) son tarihi ile ölçüm günü arasındaki GEÇERLİ (XNYS) seans farkı
    `OLU_ISIM_SEANS_ESIGI` (=5) değerini/üstünü aşarsa aday: `RETIRED_SYMBOLS`ta ZATEN hüküm
    görmüşse `zaten_emekli`ye (beklenen sonuç, gürültü DEĞİL), değilse `adaylar`a (YENİ bulgu —
    `EVREN_DISI_BEYANLI` sembolü dahil, `no_data_report.retired` ayrımıyla AYNI disiplin).
  * Hafta sonu/tatil bir "eksik seans" SAYILMAZ: seans farkı XNYS takvimi (`data._sessions()`)
    üzerinden ikili aramayla (`bisect`) hesaplanır, naif takvim-günü farkı DEĞİL.
  * Ölçülemeyen sembol (arşiv yok/boş/okunamaz, ya da takvim okunamadı) `olculemedi`ye `neden`
    ile düşer — `adaylar`a GİRMEZ (UYDURMA YASAĞI).
  * `watchdog.check_olu_isim_and_alarm()` — `adaylar` boş değilse günde EN ÇOK
    `GUNLUK_ALARM_TAVANI` (=1) kez `obs.warn("SEMBOL_OLU_ADAY", ...)` (ALARM DEĞİL — emeklilik
    kararı operatörün). `ALARM_GUNLUK_FILE`ı `veri_disk_esigi` ile PAYLAŞIR (tek kaynak).
  * YASA 6 okuyucu: `check_and_alarm()` bu sensörü KENDİ try'ında çağırır (AST çivisi — metin
    çapası DEĞİL, watchdog.py motor dosyası `dosya.py:NNN` sıfır toleransı v382).
"""
from __future__ import annotations

import ast
import datetime as dt
import pathlib

import pandas as pd
import pytest

from meridian import config, store, watchdog

SRC = pathlib.Path(__file__).resolve().parents[1]


# ---- yardımcılar --------------------------------------------------------------------------

def _hafta_ici(baslangic: str, bitis: str, tatiller: tuple = ()) -> list[str]:
    """[baslangic, bitis] arası Pazartesi-Cuma tarihleri (YYYY-MM-DD), `tatiller` hariç. Sentetik
    XNYS takvimi — gerçek `pandas_market_calendars`in tam kendisini test etmiyoruz (o kütüphanenin
    işi), yalnız SENSÖRÜN hafta sonu/tatili SAYMADIĞINI ölçüyoruz."""
    d = dt.date.fromisoformat(baslangic)
    son = dt.date.fromisoformat(bitis)
    out = []
    while d <= son:
        if d.weekday() < 5 and d.isoformat() not in tatiller:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _arsiv_yaz(ticker: str, son_bar: str) -> None:
    """Sembolün YEREL bar arşivini (`state/bars/<ticker>.csv`) tek satırla kurar — sensör yalnız
    `date` sütununun EN BÜYÜK değerine bakar, OHLCV'nin kendisi ölçüme girmez."""
    df = pd.DataFrame({"date": [son_bar], "open": [1.0], "high": [1.0], "low": [1.0],
                        "close": [1.0], "volume": [100]})
    df.to_csv(config.BARS / f"{ticker.lower()}.csv", index=False)


def _bugun_ayarla(monkeypatch, tarih: str) -> None:
    """`watchdog._now()`ı sabit bir UTC güne çiviler (öğlen — gece yarısı sınırından uzak)."""
    an = dt.datetime.combine(dt.date.fromisoformat(tarih), dt.time(12, 0), dt.timezone.utc)
    monkeypatch.setattr(watchdog, "_now", lambda: an.timestamp())


@pytest.fixture
def evren(sandbox_state, monkeypatch):
    """Gerçek 251-sembollü evren yerine küçük sentetik küme: gerçek CSV'lerin yokluğu
    `olculemedi`yi boğar ve testi YAVAŞLATIR. `RETIRED_SYMBOLS`/`EVREN_DISI_BEYANLI` varsayılan
    BOŞ — testler ihtiyaç duyduğunda kendi girdisini ekler."""
    from meridian.adapters import data
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    monkeypatch.setattr(data, "RETIRED_SYMBOLS", {})
    monkeypatch.setattr(data, "EVREN_DISI_BEYANLI", {})
    return data


@pytest.fixture
def takvim(evren, monkeypatch):
    """Sentetik XNYS takvimi: 2026-07-01 → 2026-10-31 arası hafta içi, tatilsiz (test (1)/(3)/(4)/
    (5) bu takvimi kullanır; test (2) kendi tatilli/tatilsiz varyantını AYRICA kurar)."""
    from meridian.adapters import data
    ses = frozenset(_hafta_ici("2026-07-01", "2026-10-31"))
    monkeypatch.setattr(data, "_sessions", lambda: ses)
    return ses


@pytest.fixture
def warnlar(monkeypatch):
    """obs.warn çağrılarını yakalar — bu sensörün TEK gözlenebilir bildirim çıktısı (ALARM
    DEĞİL)."""
    from meridian import obs
    kayit: list[dict] = []

    def _yakala(event, **fields):
        kayit.append({"event": event, **fields})
        return {"event": event}

    monkeypatch.setattr(obs, "warn", _yakala)
    return kayit


# ---- (1) sentetik arşiv: 3 sembol, biri 8 seans bar yok → aday -----------------------------

def test_sekiz_seans_bar_yok_aday(takvim, monkeypatch):
    from meridian.adapters import data
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["AAA", "BBB", "CCC"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["AAA", "BBB", "CCC"])
    _arsiv_yaz("AAA", "2026-08-20")   # Perşembe — bugüne (2026-09-01) kadar 8 GEÇERLİ seans var
    _arsiv_yaz("BBB", "2026-08-31")   # Pazartesi — 1 seans geride, normal
    _arsiv_yaz("CCC", "2026-09-01")   # bugünün kendisi — 0 seans geride
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()

    assert rep["esik"] == watchdog.OLU_ISIM_SEANS_ESIGI == 5
    adaylar = {a["ticker"]: a for a in rep["adaylar"]}
    assert set(adaylar) == {"AAA"}, "yalnız AAA eşiği aşmalı"
    assert adaylar["AAA"]["seans_farki"] == 8
    assert adaylar["AAA"]["son_bar"] == "2026-08-20"
    assert rep["zaten_emekli"] == []
    assert rep["olculemedi"] == []
    assert rep["takvim_var"] is True
    assert rep["n_tarandi"] == 3


# ---- (2) hafta sonu/tatil sayılmaz (Cuma son bar, Pazartesi sabah ölçüm → aday değil) ------

def test_hafta_sonu_sayilmaz_cuma_pazartesi(evren, monkeypatch):
    from meridian.adapters import data
    # Perşembe tam tatil GÜNÜ de eklenir (Şükran/Memorial Day sınıfı) — yalnız hafta sonu değil,
    # takvimin GERÇEKTEN dışladığı bir tatil de "eksik seans" SAYILMAMALI.
    tatil = "2026-08-20"
    ses = frozenset(_hafta_ici("2026-07-01", "2026-10-31", tatiller=(tatil,)))
    monkeypatch.setattr(data, "_sessions", lambda: ses)
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["FRI"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["FRI"])
    _arsiv_yaz("FRI", "2026-08-21")   # Cuma son bar
    _bugun_ayarla(monkeypatch, "2026-08-24")   # takip eden Pazartesi (sabah — tek bir seans geçti)

    # BİRİM DÜZEYİ: gerçek seans farkı TAM 1'dir — naif takvim-günü farkı (3) DEĞİL. Bu, hafta
    # sonunun ayrıca sayılmadığının doğrudan kanıtıdır (threshold'dan BAĞIMSIZ).
    sirali = sorted(ses)
    assert watchdog._seans_farki(sirali, "2026-08-21", "2026-08-24") == 1
    assert (dt.date.fromisoformat("2026-08-24") - dt.date.fromisoformat("2026-08-21")).days == 3

    # BÜTÜNLEŞİK: varsayılan eşikle (5) bu sembol ADAY DEĞİLDİR.
    rep = watchdog.olu_isim_adaylari()
    assert rep["adaylar"] == []
    assert rep["zaten_emekli"] == []
    assert rep["olculemedi"] == []


# ---- (3) RETIRED/beyanlı sembol de taranır --------------------------------------------------

def test_retired_ve_beyanli_de_tarandi(takvim, monkeypatch):
    """RETIRED_SYMBOLS'taki eski bulgu `zaten_emekli`ye düşer (gürültü değil, BEKLENEN sonuç);
    `EVREN_DISI_BEYANLI`deki sembol ise (LIVE/REPLAY_UNIVERSE'de HİÇ olmasa bile) `adaylar`a düşer
    — TSK-143 bedel beyanının kapattığı kör nokta tam bu: universe_drift() bu 10 sembolü hiç
    görmez, bu sensör KENDİ evren birleşimiyle onları YİNE DE tarar."""
    from meridian.adapters import data
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["BBB"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["BBB"])
    monkeypatch.setattr(data, "RETIRED_SYMBOLS", {"ZZZ": "2026-01-01 delist — sentetik"})
    monkeypatch.setattr(data, "EVREN_DISI_BEYANLI", {"YYY": "S&P 500 dışı ama aktif — sentetik"})
    _arsiv_yaz("BBB", "2026-08-31")   # taze, aday değil
    _arsiv_yaz("ZZZ", "2026-08-01")   # eski — RETIRED, beklenen
    _arsiv_yaz("YYY", "2026-08-01")   # eski — beyanlı ama YENİ bulgu (kör nokta)
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()

    assert rep["n_tarandi"] == 3, "üç sembolün HİÇBİRİ evrenden sessizce düşmemeli (YASA 6)"
    aday_ad = {a["ticker"] for a in rep["adaylar"]}
    emekli_ad = {a["ticker"] for a in rep["zaten_emekli"]}
    assert aday_ad == {"YYY"}, "beyanlı ama RETIRED olmayan sembol YENİ bulgu olarak aday olmalı"
    assert emekli_ad == {"ZZZ"}, "RETIRED sembol zaten_emekli'de durmalı, adaylar'a KARIŞMAMALI"
    assert "BBB" not in aday_ad and "BBB" not in emekli_ad


# ---- (4) arşiv okunamıyor → None + neden, warn yok ------------------------------------------

def test_arsiv_okunamiyor_none_ve_neden_warn_yok(takvim, monkeypatch, warnlar):
    from meridian.adapters import data
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["BBB", "YOK", "BOZUK"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["BBB", "YOK", "BOZUK"])
    _arsiv_yaz("BBB", "2026-08-31")           # taze, sorunsuz
    # "YOK": hiç CSV yazılmadı (arşiv yok).
    (config.BARS / "bozuk.csv").write_text("bu bir CSV degil ne bir baslik ne bir tarih\x00\x01")
    _bugun_ayarla(monkeypatch, "2026-09-01")

    rep = watchdog.olu_isim_adaylari()

    olculemedi = {o["ticker"]: o["neden"] for o in rep["olculemedi"]}
    assert set(olculemedi) == {"YOK", "BOZUK"}
    assert olculemedi["YOK"], "UYDURMA YASAĞI: neden BOŞ olamaz"
    assert olculemedi["BOZUK"]
    assert rep["adaylar"] == [] and rep["zaten_emekli"] == []

    check_rep = watchdog.check_olu_isim_and_alarm()
    assert check_rep == rep
    assert warnlar == [], "hiçbir GERÇEK aday yok — ölçülemeyen sembol warn ÜRETMEMELİ"


# ---- (5) aynı gün ikinci çağrı mandal --------------------------------------------------------

def test_ayni_gun_ikinci_cagri_mandallanir(takvim, monkeypatch, warnlar):
    from meridian.adapters import data
    monkeypatch.setattr(data, "LIVE_UNIVERSE", ["AAA"])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["AAA"])
    _arsiv_yaz("AAA", "2026-08-20")
    _bugun_ayarla(monkeypatch, "2026-09-01")

    watchdog.check_olu_isim_and_alarm()
    watchdog.check_olu_isim_and_alarm()          # AYNI gün, AYNI aday kümesi — tekrar YOK

    assert len(warnlar) == 1, "günlük tavan aşıldı: ikinci çağrı yeni satır ÜRETMEMELİ (mandal)"
    assert warnlar[0]["event"] == "SEMBOL_OLU_ADAY"
    assert warnlar[0]["semboller"] == ["AAA"]
    assert warnlar[0]["en_eski"]["ticker"] == "AAA"
    assert warnlar[0]["en_eski"]["seans_farki"] == 8
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    satir = doc["mekanizmalar"][watchdog._OLU_ISIM_MEK_ADI]
    assert satir["alarm"] == 1
    assert satir["bastirilan"] == 1, "bastırılan SESSİZ DEĞİL — sayaçta GÖRÜNÜR olmalı (YASA 6)"


# ---- YASA 6: okuyucu zinciri (AST çivisi — metin çivisi değil) ------------------------------

def test_zincir_check_and_alarm_kendi_tryinda_cagirir():
    agac = ast.parse((SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8"))
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == "check_and_alarm")
    hedefli_try = None
    for tr in (n for n in ast.walk(fn) if isinstance(n, ast.Try)):
        adlar = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                 for c in ast.walk(tr) if isinstance(c, ast.Call)
                 if isinstance(c.func, (ast.Name, ast.Attribute))}
        if "check_olu_isim_and_alarm" in adlar:
            hedefli_try = tr
            break
    assert hedefli_try is not None, (
        "check_and_alarm zinciri check_olu_isim_and_alarm'ı çağırmıyor — sensör OKUYUCUSUZ "
        "(YASA 6): bekçi yazılmış ama zincire bağlanmamış")
    # yalıtım: kendi try'ı Exception yakalar (akranlarının deseni — biri düşünce zincir düşmez)
    assert any(isinstance(h.type, ast.Name) and h.type.id == "Exception"
               for h in hedefli_try.handlers)
