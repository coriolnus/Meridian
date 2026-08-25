"""FMP ÜCRETSİZ-PLAN BÜTÇE ÇİVİLERİ (v291 turu, 2026-08-25).

ÖLÇÜLEN DURUM (bu tur ÖNCESİ, operatör brief'i — yeniden ölçülmedi): evren 251 sembol, ücretsiz
plan 250 çağrı/gün/anahtar, iki anahtar kurulu → ~502 çağrı her gece 20:00-20:20 UTC arasında
tükeniyor. Bütçe kırılımı: Y1 bar zinciri FMP kolu 253/gün · Y2 kazanç takvimi FMP yedeği 249/gün ·
Y3 içeriden işlem 1/gün (VAZGEÇİLMEZ) · Y4 S&P üyeliği 1/gün.

DÖRT ÇİVİ, DÖRT AYRI BÖLÜM — her biri bir İDDİAYI çiviler, bir uygulamayı değil:
  [1] bar zincirinde FMP kolu cboe/nasdaq'ın ARKASINDA (sıra geri alınırsa çivi düşer)
  [2] kota bloğu SAĞLAYICININ günlük sıfırlamasına bağlı (saatlik kendiliğinden açılma yok)
  [3] 402 alan UÇ o gün için kapanır — rotasyon DEĞİL (ikinci anahtar aynı ücretsiz planda)
  [4] kazanç takvimi FMP yedeği TAVANLI ve daraltma BEYANLI (sessiz kırpma yasak)
"""
import datetime as dt
import time

import pandas as pd
import pytest

from meridian import earnings, obs, secrets
from meridian.adapters import data as da
from meridian.adapters import fmp


class _Resp:
    """httpx yanıt saplaması (tests/test_fmp.py ile aynı desen)."""

    def __init__(self, payload, status=200, text=""):
        self._p, self.status_code, self.text = payload, status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._p


def _blokları_sifirla():
    """Süreç-içi FMP bloklarını temizle. `_PATH_BLOCKED` bu turda DOĞUYOR; `getattr` yedeği
    yalnız KIRMIZI fazda (henüz yokken) fikstürün patlamamasi içindir — asıl iddia bölüm 3'ün
    ağ-isteği sayacındadır, bu satırda değil."""
    fmp._KEY_BLOCKED.clear()
    getattr(fmp, "_PATH_BLOCKED", {}).clear()


@pytest.fixture(autouse=True)
def _sandbox_all(sandbox_state, monkeypatch):
    """Her test kum havuzunda: FMP yolları her çağrıda `fmp_usage.json` yazar (operatörün CANLI
    kota sayacı ezilmesin) ve süreç-içi bloklar testler ARASI sızmasın."""
    _blokları_sifirla()
    yield
    _blokları_sifirla()


# ==================================================================================================
# BÖLÜM 1 — BAR ZİNCİRİNDE FMP KOLU SONDA  [ölçülen kazanç ≥219 çağrı/gün]
# ==================================================================================================
def test_1_fmp_kolu_cboe_ve_nasdaqin_ARKASINDA(monkeypatch):
    """Zincir tüketicisi İLK YETERLİ kaynakta `return df` yapar; yani SIRA gerçekten çağrı
    kazandırır. `bars_source.json` FMP'nin hiçbir sembolün sahibi OLMADIĞINI söylüyor
    (cboe 192 · nasdaq 59 · fmp 0), o yüzden FMP'yi öne sormak 253 çağrıyı bedavaya yakıyordu.

    SIRA KAYNAK METNİNDEN DEĞİL, `chain`in GERÇEK KOŞUM SIRASINDAN ölçülür: kollar sahte
    adaptörlerle çağrılır ve hangi kolun ne zaman koştuğu kaydedilir."""
    from meridian.adapters import massive

    sira: list[str] = []
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(massive, "available", lambda: False)
    monkeypatch.setattr(massive, "write_enabled", lambda: False)
    for ad, fn_adi in (("fmp", "_fetch_fmp"), ("cboe", "_fetch_cboe"), ("nasdaq", "_fetch_nasdaq")):
        def _kaydet(*a, _ad=ad, **k):
            sira.append(_ad)
            return pd.DataFrame()
        monkeypatch.setattr(da, fn_adi, _kaydet)

    da.fetch("AAA", "2026-08-01", "2026-08-20", incremental_ok=False)

    assert set(sira) == {"fmp", "cboe", "nasdaq"}, f"zincir eksik koştu: {sira}"
    assert sira.index("fmp") > sira.index("cboe"), f"FMP hâlâ cboe'nin ÖNÜNDE: {sira}"
    assert sira.index("fmp") > sira.index("nasdaq"), f"FMP hâlâ nasdaq'ın ÖNÜNDE: {sira}"


def test_1_fmp_kolu_kota_blokluyken_zincire_HIC_girmez(monkeypatch):
    """SIRA DEĞİŞTİ, KAPI DEĞİŞMEDİ: kota bloğu varken FMP kolu zincire hiç eklenmez (boş istek
    ne veri getirir ne kotayı geri verir). Bu satır taşınırken düşerse sessizce 250 boş istek geri
    gelirdi."""
    from meridian.adapters import massive

    sira: list[str] = []
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: True)
    monkeypatch.setattr(massive, "available", lambda: False)
    monkeypatch.setattr(massive, "write_enabled", lambda: False)
    for ad, fn_adi in (("fmp", "_fetch_fmp"), ("cboe", "_fetch_cboe"), ("nasdaq", "_fetch_nasdaq")):
        def _kaydet(*a, _ad=ad, **k):
            sira.append(_ad)
            return pd.DataFrame()
        monkeypatch.setattr(da, fn_adi, _kaydet)

    da.fetch("AAA", "2026-08-01", "2026-08-20", incremental_ok=False)
    assert "fmp" not in sira, f"kota bloklu anahtarla FMP'ye istek atıldı: {sira}"


# ==================================================================================================
# BÖLÜM 2 — KOTA BLOĞU SAĞLAYICININ GÜNLÜK SIFIRLAMASINA BAĞLI  [ölçülen kazanç 10-20 çağrı/gün]
# ==================================================================================================
def _epoch(y, m, d, hh, mm, ss=0) -> float:
    return dt.datetime(y, m, d, hh, mm, ss, tzinfo=dt.timezone.utc).timestamp()


def test_2_blok_ayni_UTC_gunu_boyunca_acilmaz(monkeypatch):
    """KUSUR: blok süresi 1 saatti ama FMP kotası GÜNLÜKTÜR. Blok her saat kendiliğinden açılıyor
    ve her açılışta İKİ anahtara birer GARANTİLİ-429 atılıyordu (`quota_hits` defteri: 07-28
    21:37→22:37, 07-29 20:33→21:36→22:56 — hepsi tam bir saat arayla, ÇİFT)."""
    monkeypatch.setattr(time, "time", lambda: _epoch(2026, 8, 20, 20, 30))
    fmp._block_key("FMP_API_KEY")

    monkeypatch.setattr(time, "time", lambda: _epoch(2026, 8, 20, 21, 31))
    assert fmp._key_blocked("FMP_API_KEY") is True, "blok bir saat sonra kendiliğinden açıldı"
    monkeypatch.setattr(time, "time", lambda: _epoch(2026, 8, 20, 23, 59, 59))
    assert fmp._key_blocked("FMP_API_KEY") is True, "blok gün bitmeden açıldı"


def test_2_blok_UTC_gun_donumunde_acilir(monkeypatch):
    """Blok SONSUZ değildir: sağlayıcının günlük sıfırlamasında açılmalı, yoksa bir gün önceki
    429 yüzünden ertesi günün tüm kotası kullanılmadan kalırdı."""
    monkeypatch.setattr(time, "time", lambda: _epoch(2026, 8, 20, 20, 30))
    fmp._block_key("FMP_API_KEY")

    monkeypatch.setattr(time, "time", lambda: _epoch(2026, 8, 21, 0, 0, 30))
    assert fmp._key_blocked("FMP_API_KEY") is False, "gün dönümünde blok açılmadı"


def test_2_saatlik_sabit_geri_gelirse_civi_duser():
    """ÇAPA: 1 saatlik sabit geri konursa yukarıdaki iki çivi düşer; bu çivi NEDENİ okur —
    blok süresi bir SAAT sabiti değil, gün dönümüne kalan süre olmalı."""
    monkeypatch_yok = fmp._blok_bitisi(_epoch(2026, 8, 20, 20, 30))
    assert monkeypatch_yok == _epoch(2026, 8, 21, 0, 0), "blok bitişi UTC gün sonuna hizalı değil"
    # Gün dönümüne 30 saniye kala bloklanan anahtar yalnız 30 saniye bloklu kalır — sağlayıcının
    # takvimi neyse odur; süreyi yapay olarak uzatmak "uydurma saat sabiti" olurdu.
    assert fmp._blok_bitisi(_epoch(2026, 8, 20, 23, 59, 30)) == _epoch(2026, 8, 21, 0, 0)


# ==================================================================================================
# BÖLÜM 3 — 402: ROTASYON DEĞİL, UCU O GÜN İÇİN KAPAT
# ==================================================================================================
def _anahtarlar(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "k_birincil")
    monkeypatch.setenv("FMP_API_KEY_2", "k_yedek")
    secrets.clear_cache()


def test_3_402_sonrasi_ayni_uca_ikinci_cagri_ag_istegi_ATMAZ(monkeypatch):
    """ÖLÇÜLEN VAKA (2026-08-23): 43 çağrının 43'ü 402 ile düştü, hepsi birinci anahtarda.
    402 = "bu uç ücretsiz planda kapalı"; ikinci anahtar AYNI planda, yani rotasyon 43 kaybı 86
    yapardı. Doğru davranış: UCU o gün için kapat ve bir daha istek ATMA."""
    _anahtarlar(monkeypatch)
    istekler: list[str] = []

    def sahte_get(url, params=None, timeout=None):
        istekler.append(url)
        return _Resp({"Error Message": "Special Endpoint"}, status=402, text="Special Endpoint")

    monkeypatch.setattr(fmp.httpx, "get", sahte_get)

    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "A,B"})
    assert len(istekler) == 1, f"402 rotasyon tetikledi — ikinci anahtar aynı planda: {istekler}"

    with pytest.raises(Exception) as ikinci:
        fmp._get("quote", {"symbol": "A,B"})
    assert len(istekler) == 1, f"KAPALI uca ikinci ağ isteği atıldı: {len(istekler)} istek"
    assert "402" in str(ikinci.value), f"gerekçe dürüst değil: {ikinci.value}"


def test_3_kapali_uc_muhasebede_GORUNUR(monkeypatch):
    """Sessiz atlama yasak: atlanan istek `usage`ta AYRI sayılır (çağrı sayacını ŞİŞİRMEDEN —
    atılmayan istek bir çağrı değildir) ve kapalı uç `health()`te adıyla görünür."""
    _anahtarlar(monkeypatch)
    monkeypatch.setattr(fmp.httpx, "get",
                        lambda url, params=None, timeout=None: _Resp({}, status=402, text="402"))
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "A,B"})
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "A,B"})

    u = fmp.usage()
    assert u.get("calls") == 1, f"atlanan istek ÇAĞRI olarak sayıldı: {u}"
    assert u.get("atlanan") == 1, f"atlanan istek muhasebede yok: {u}"
    assert (u.get("atlanan_by_path") or {}).get("quote") == 1, f"atlama UÇ bazında yok: {u}"
    assert fmp.blocked_paths() == ["quote"], f"kapalı uç muhasebede görünmüyor: {fmp.blocked_paths()}"


def test_3_402_bir_ucu_kapatir_DIGER_ucu_kapatmaz(monkeypatch):
    """Kapatma ANAHTAR başına değil UÇ başına: `insider-trading/search` 402 verirken
    `insider-trading/latest` (Y3, günde 1 çağrı, VAZGEÇİLMEZ) çalışmaya devam etmeli."""
    _anahtarlar(monkeypatch)
    yollar: list[str] = []

    def sahte_get(url, params=None, timeout=None):
        yollar.append(url.rsplit("/stable/", 1)[-1])
        if yollar[-1] == "insider-trading/search":
            return _Resp({}, status=402, text="402")
        return _Resp([{"symbol": "AAA"}], status=200)

    monkeypatch.setattr(fmp.httpx, "get", sahte_get)
    with pytest.raises(Exception):
        fmp._get("insider-trading/search", {"symbol": "AAA"})
    with pytest.raises(Exception):
        fmp._get("insider-trading/search", {"symbol": "BBB"})
    assert yollar.count("insider-trading/search") == 1

    assert fmp._get("insider-trading/latest", {"page": 0}) == [{"symbol": "AAA"}]
    assert yollar.count("insider-trading/latest") == 1, "başka bir uç yanlışlıkla kapatıldı"


def test_3_429_ROTASYONU_aynen_korunur(monkeypatch):
    """402 yolu 429 yolunu BOZMAMALI: gerçek KOTA sinyali bu hesapta 429'dur ve tam 251./502.
    çağrıda gelir (`quota_hits` defteri). Rotasyon orada DOĞRU davranıştır."""
    _anahtarlar(monkeypatch)
    gorulen: list[str] = []

    def sahte_get(url, params=None, timeout=None):
        gorulen.append(params["apikey"])
        if params["apikey"] == "k_birincil":
            return _Resp({"Error Message": "Limit Reach"}, status=429, text="Limit Reach")
        return _Resp([{"symbol": "AAPL", "price": 150.0}], status=200)

    monkeypatch.setattr(fmp.httpx, "get", sahte_get)
    out = fmp._get("quote", {"symbol": "AAPL"})
    assert out and out[0]["price"] == 150.0, "429 sonrası yedek anahtardan dönmedi"
    assert gorulen == ["k_birincil", "k_yedek"], f"rotasyon sırası bozuldu: {gorulen}"
    assert fmp._key_blocked("FMP_API_KEY") is True
    assert fmp.blocked_paths() == [], "429 UCU kapattı — kota sinyali plan sinyaliyle karıştı"


def test_3_ping_kapali_ucta_bile_AGA_CIKAR(monkeypatch):
    """`ping()` TEŞHİS aracıdır: uç kapalıyken de gerçek isteği atmalı, yoksa operatör anahtarın
    canlı olup olmadığını bir daha ölçemez."""
    _anahtarlar(monkeypatch)
    istekler: list[str] = []

    def sahte_get(url, params=None, timeout=None):
        istekler.append(params["apikey"])
        if len(istekler) == 1:
            return _Resp({}, status=402, text="402")
        return _Resp([{"symbol": "AAPL", "price": 12.5}], status=200)

    monkeypatch.setattr(fmp.httpx, "get", sahte_get)
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "A,B"})
    r = fmp.ping()
    assert r["ok"] is True and len(istekler) == 2, f"ping kapalı uçta ağa çıkmadı: {istekler}"


# ==================================================================================================
# BÖLÜM 4 — KAZANÇ TAKVİMİ FMP YEDEĞİNİ TAVANLA  [ölçülen kazanç ~224 çağrı/gün]
# ==================================================================================================
def _fmp_sahte(monkeypatch, sorulan: list[str]):
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)

    def _dates(t, strict=False):
        sorulan.append(t.upper())
        return []
    monkeypatch.setattr(fmp, "earnings_dates", _dates)
    monkeypatch.setattr(time, "sleep", lambda s: None)     # polite delay testi yavaşlatmasın


def test_4_tavan_asilmaz(monkeypatch, sandbox_state):
    """251 sembollük evren TAVANSIZ bir döngüydü ve günlük kotanın tamamını (249) yakıyordu.
    Tavan bir ÇARE değil SİGORTAdır: Nasdaq bacağındaki regresyonun bedelini tavana indirir."""
    sorulan: list[str] = []
    _fmp_sahte(monkeypatch, sorulan)
    earnings.clear_cache()

    earnings.refresh_from_fmp([f"T{i:03d}" for i in range(251)])

    assert earnings.EARNINGS_FMP_TAVAN == 25, "tavan değişti — gerekçesi şerhte güncellendi mi?"
    assert len(sorulan) <= earnings.EARNINGS_FMP_TAVAN, f"tavan aşıldı: {len(sorulan)} sembol"
    assert len(sorulan) == earnings.EARNINGS_FMP_TAVAN, f"tavan altında kaldı: {len(sorulan)}"


def test_4_atlananlar_BEYAN_edilir(monkeypatch, sandbox_state):
    """SESSİZ KIRPMA YASAK (bu deponun yasası): kaç sembol soruldu, kaçı atlandı — sayıyla."""
    sorulan: list[str] = []
    _fmp_sahte(monkeypatch, sorulan)
    earnings.clear_cache()
    uyarilar: list[tuple] = []
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyarilar.append((ev, kw)))

    earnings.refresh_from_fmp([f"T{i:03d}" for i in range(251)])

    beyan = [kw for ev, kw in uyarilar if ev == "earnings_fmp_yedek_daraltildi"]
    assert beyan, f"daraltma beyan edilmedi: {[ev for ev, _ in uyarilar]}"
    b = beyan[0]
    assert b["istenen"] == 251 and b["soruldu"] == 25
    assert b["atlandi"] == 251 - 25 - b["ufukta_bilinen"], f"sayılar tutmuyor: {b}"
    assert b["tavan"] == earnings.EARNINGS_FMP_TAVAN


def test_4_ufuk_disindaki_sembol_SORULMAZ(monkeypatch, sandbox_state):
    """KARARTMA UFKU: takvimde önümüzdeki BLACKOUT_DAYS + REFRESH_CADENCE_DAYS gün içinde tarihi
    OLAN sembol zaten BİLİNİYOR — onu FMP'ye sormak kotayı bilinen bir cevaba harcamaktır.
    Riskli olan, o pencerede tarihi OLMAYAN sembollerdir (karartma orada fail-open kalır)."""
    ufuk_ici = (dt.date.today() + dt.timedelta(days=2)).isoformat()
    uzak = (dt.date.today() + dt.timedelta(days=90)).isoformat()
    (sandbox_state / "earnings.csv").write_text(
        f"ticker,date,time\nBILINEN,{ufuk_ici},\nUZAK,{uzak},\n")
    earnings.clear_cache()
    sorulan: list[str] = []
    _fmp_sahte(monkeypatch, sorulan)

    earnings.refresh_from_fmp(["BILINEN", "UZAK", "BOSTA"])

    assert "BILINEN" not in sorulan, "ufuk İÇİNDE tarihi bilinen sembole kota harcandı"
    assert sorulan == ["UZAK", "BOSTA"], f"ufuk daraltması yanlış sembolleri sordu: {sorulan}"


def test_4_ufuk_penceresi_SABITLERDEN_turetilir():
    """Pencere literal DEĞİL: karartma ya da kadans sabiti değişirse ufuk kendiliğinden kayar.
    Üç sayının aritmetiğinin bir yerde YAZILI olmaması bu modülün bilinen hata sınıfıydı."""
    assert earnings.fmp_yedek_ufku() == earnings.BLACKOUT_DAYS + earnings.REFRESH_CADENCE_DAYS
