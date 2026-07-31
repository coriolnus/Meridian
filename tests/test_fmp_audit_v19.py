"""test_fmp_audit_v19.py — adapters.fmp denetimi (2026-07-21, tur 4).

7. soru: "neyi VARSAYIYOR ama iddia etmiyor?"
  F1 "boş liste = veri yok"        → hata da boş liste döndürüyordu; kotanın PAS ORTASINDA bitmesi
     yarım bir kazanç takvimi yazıyor, karartma guard'ı veri yokken FAIL-OPEN olduğu için o
     isimlerde kazanç günü işlem açılıyordu (sert guard sessizce no-op)
  F2 "kota sonsuz"                  → 250 ticker'lık BİR bar tazelemesi günlük kotanın tamamı;
     muhasebe yoktu, "kota neden bitti" tahminle cevaplanıyordu
  F3 "anahtar loglanmaz"            → httpx hata metni TAM URL taşır (tur 2'de maskelendi; burada kilit)
"""
from __future__ import annotations

import httpx
import pytest

from meridian import earnings, store
from meridian.adapters import fmp


class _R:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._p = payload if payload is not None else []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(f"{self.status_code}", request=None, response=self)

    def json(self):
        return self._p


@pytest.fixture(autouse=True)
def _sandbox_all(sandbox_state):
    """Dosya geneli kum havuzu (2026-07-22, sızıntı bekçisi): bu dosyadaki yollar canlı `state/`e
    telemetri/olay yazıyordu — operatörün defterine test verisi karışıyor ve kimse fark etmiyordu."""
    yield


@pytest.fixture(autouse=True)

def _reset(monkeypatch):
    # `blocked_until` YAZIMLARI SİLİNDİ (2026-07-26): alan üretimden kaldırıldı (yazılıyordu ama
    # hiçbir yerde okunmuyordu). Testin onu yeniden kurması ÖLÜ bir satırdı — üstelik kaldırılmış
    # bir alanı canlı gibi gösteriyordu. Gerçek kota bloğu `_KEY_BLOCKED.clear()` ile sıfırlanır.
    fmp._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                        "last_error": "", "at": None})
    fmp._KEY_BLOCKED.clear()                          # anahtar-başına 429 bloğu testler arası sızmasın
    monkeypatch.setattr(fmp.secrets, "get", lambda n, *a, **k: "KEY123")
    monkeypatch.setattr(fmp.secrets, "present", lambda n: True)
    yield
    fmp._KEY_BLOCKED.clear()


# ---------- F1: boş ≠ hata ----------
def test_f1_strict_mode_surfaces_the_error(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(429))
    assert fmp.earnings_dates("KO") == []                       # varsayılan: eskisi gibi yutar
    with pytest.raises(Exception):
        fmp.earnings_dates("KO", strict=True)                   # toplu tazeleme bunu kullanır


def test_f1b_partial_quota_failure_keeps_old_dates(sandbox_state, monkeypatch):
    """ASIL BULGU: kota pasın ortasında biterse dosya YARIM listeyle ÜZERİNE YAZILIYORDU; düşen
    isimlerde in_blackout() False dönerdi (veri yok → engelleme yok) ve motor kazanç günü işlem
    açardı. Artık eski tarihler korunur ve durum kaydedilir."""
    earnings.clear_cache()
    (store.config.STATE / "earnings.csv").write_text("ticker,date\nAAA,2026-08-01\nBBB,2026-08-02\n")
    earnings.clear_cache()

    calls = {"n": 0}

    def _get(path, params=None, timeout=20.0):
        calls["n"] += 1
        if params.get("symbol") == "AAA":
            return [{"date": "2026-09-01"}]
        raise httpx.HTTPStatusError("429", request=None, response=_R(429))

    monkeypatch.setattr(fmp, "_get", _get)
    n = earnings.refresh_from_fmp(["AAA", "BBB"])
    earnings.clear_cache()

    rows = (store.config.STATE / "earnings.csv").read_text()
    assert "AAA,2026-09-01" in rows                              # taze veri yazıldı
    assert "BBB,2026-08-02" in rows                              # DÜŞEN isim eski tarihini KORUDU
    assert n >= 2
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "earnings_refresh_partial"]
    assert ev and ev[-1]["failed"] == 1


def test_f1c_blackout_guard_stays_armed_after_partial_failure(sandbox_state, monkeypatch):
    """Zincirin ucu: guard hâlâ silahlı mı? (Kısmi hatadan SONRA BBB için karartma çalışmalı.)"""
    earnings.clear_cache()
    (store.config.STATE / "earnings.csv").write_text("ticker,date\nBBB,2026-08-02\n")
    earnings.clear_cache()
    monkeypatch.setattr(fmp, "_get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("429")))
    earnings.refresh_from_fmp(["BBB"])
    earnings.clear_cache()
    assert earnings.in_blackout("BBB", "2026-07-30") is True     # 3 gün kala → karartma AKTİF


# ---------- F2: kota muhasebesi ----------
def test_f2_daily_usage_is_counted(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(200, [{"symbol": "KO"}]))
    fmp._get("quote", {"symbol": "KO"})
    fmp._get("quote", {"symbol": "PG"})
    u = fmp.usage()
    assert u["calls"] == 2 and u["fails"] == 0

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(429))
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "X"})
    u = fmp.usage()
    assert u["calls"] == 3 and u["fails"] == 1 and u["blocked_at"] == 3   # kotanın bittiği çağrı no'su


def test_f2b_quota_block_stops_bulk_consumers(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(429))
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "X"})
    assert fmp.quota_blocked() is True
    from meridian.adapters import data
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: __import__("pandas").DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: __import__("pandas").DataFrame())
    monkeypatch.setattr(data, "_fetch_fmp",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("kota doluyken çağrılmamalı")))
    data.fetch("KO", "2026-07-01", "2026-07-08")


# ---------- F3: anahtar sızıntısı ----------
def test_f3_key_never_in_error_or_health(monkeypatch):
    def _boom(*a, **k):
        raise httpx.ConnectError("failed for https://x/stable/quote?apikey=KEY123")

    monkeypatch.setattr(httpx, "get", _boom)
    with pytest.raises(Exception) as ei:
        fmp._get("quote", {"symbol": "KO"})
    assert "KEY123" not in str(ei.value)
    assert "KEY123" not in str(fmp.health())


# ---------- sahiplik: anahtar tek yerde ----------
def test_key_names_enumerated_in_exactly_one_place():
    """Yedek-anahtar rotasyonu geldi (2026-07-23) ama sahiplik yasası aynı: anahtar ADLARI (birincil +
    yedek) TEK yerde — _active_keys()'in enumerasyonunda — okunur; hardcoded `secrets.get("FMP_API_KEY")`
    literali kalmadı (_redact ve _get artık _active_keys üzerinden gider, ping tek adı parametreyle okur).
    Dağılırlarsa sızma/sürüklenme riski (denetim turu 2)."""
    import inspect
    src = inspect.getsource(fmp)
    assert 'secrets.get("FMP_API_KEY")' not in src               # dağınık hardcoded okuma YOK
    assert src.count('("FMP_API_KEY", BACKUP_KEY)') == 1         # anahtar adları TEK enumerasyonda


# ---------- F4: ön-bloklu anahtarlarda İSTEK ATILMAZ (2026-07-26) ----------
def test_f4_all_keys_pre_blocked_raises_without_touching_the_network(monkeypatch):
    """Kota dolmuşken atılan istek ne veri getirir ne kotayı geri verir — yalnız `fails` sayacını
    şişirir ve bloğun kendi amacını (boş istek atmamak) çiğner. Canlı defterde 510 çağrının 418'i
    başarısızdı; bu yol o sayının bir kısmını KENDİ ELİYLE üretiyordu. İddia 'daha az istek' değil
    'HİÇ istek': sayaçlı bir sahte `httpx.get` bunu kanıtlar."""
    sayac = {"n": 0}

    def _sayan(*a, **k):
        sayac["n"] += 1
        return _R(200, [{"price": 1}])

    monkeypatch.setattr(httpx, "get", _sayan)
    monkeypatch.setattr(fmp.secrets, "get",
                        lambda n, *a, **k: {"FMP_API_KEY": "K1", "FMP_API_KEY_2": "K2"}.get(n))
    fmp._block_key("FMP_API_KEY")
    fmp._block_key(fmp.BACKUP_KEY)
    assert fmp.quota_blocked() is True                      # ön koşul: iki anahtar da bloklu

    with pytest.raises(RuntimeError, match="kota-bloklu"):
        fmp._get("quote", {"symbol": "KO"})
    assert sayac["n"] == 0, f"ön-bloklu anahtarlarla {sayac['n']} istek atıldı — blok anlamsızlaştı"


# ---------- F5: muhasebe kimin adına yazıyor? (200+429 karışık dizi) ----------
def test_f5_mixed_status_sequence_is_attributed_to_the_right_key(monkeypatch):
    """`by_status`/`by_key`/`quota_hits` TEŞHİSİN kendisidir: "kota mı, auth mı, ağ mı" sorusu
    buradan cevaplanır. Atıf `_HEALTH` modül-globalinden geri okunuyordu — `ping()` adı hiç
    yazmadığı için bayat atıf, iki iş parçacığı da birbirinin adına yazdığı için yarış üretiyordu.
    Karışık bir dizi ikisini birden sınar: değerler değil KİME AİT oldukları."""
    sira = [_R(200, [{"price": 1}]), _R(429, {}), _R(200, [{"price": 2}]), _R(429, {})]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: sira.pop(0))
    monkeypatch.setattr(fmp.secrets, "get",
                        lambda n, *a, **k: {"FMP_API_KEY": "K1", "FMP_API_KEY_2": "K2"}.get(n))

    fmp._get_with_key("quote", {"symbol": "A"}, 5.0, "K1", key_name="FMP_API_KEY")      # 200
    with pytest.raises(httpx.HTTPStatusError):
        fmp._get_with_key("quote", {"symbol": "B"}, 5.0, "K1", key_name="FMP_API_KEY")  # 429
    fmp._get_with_key("quote", {"symbol": "C"}, 5.0, "K2", key_name=fmp.BACKUP_KEY)     # 200
    with pytest.raises(httpx.HTTPStatusError):
        fmp._get_with_key("quote", {"symbol": "D"}, 5.0, "K2", key_name=fmp.BACKUP_KEY) # 429

    u = fmp.usage()
    assert u["calls"] == 4 and u["fails"] == 2
    assert u["by_status"] == {"200": 2, "429": 2}, f"durum dağılımı yanlış: {u['by_status']}"
    assert u["by_key"] == {"FMP_API_KEY": 2, "FMP_API_KEY_2": 2}, \
        f"anahtar atfı yanlış: {u['by_key']}"
    assert u["blocked_at"] == 2, "ilk 429'un kaçıncı çağrıda olduğu kaydedilmedi"
    hits = u["quota_hits"]
    assert [h["key"] for h in hits] == ["FMP_API_KEY", "FMP_API_KEY_2"], \
        f"429 kayıtları yanlış anahtara yazıldı: {hits}"
    assert [h["calls_today"] for h in hits] == [2, 4]


def test_f5b_ping_attributes_the_backup_key_to_its_own_name(monkeypatch):
    """BAYAT ATIF (canlı sınıf): `ping()` rotasyonsuzdur ve eskiden anahtar adını HİÇ yazmıyordu —
    yedek anahtarın testi bir ÖNCEKİ çağrının adıyla sayılıyordu."""
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(200, [{"price": 9}]))
    monkeypatch.setattr(fmp.secrets, "get",
                        lambda n, *a, **k: {"FMP_API_KEY": "K1", "FMP_API_KEY_2": "K2"}.get(n))
    assert fmp.ping(which=fmp.BACKUP_KEY)["ok"] is True
    assert fmp.usage()["by_key"] == {"FMP_API_KEY_2": 1}, \
        f"ping yedek anahtarı kendi adına yazmadı: {fmp.usage()['by_key']}"


def test_f6_quota_hits_survive_the_day_rollover(monkeypatch):
    """GÜN DÖNÜMÜ ÖLÇÜMÜ SİLİYORDU: `quota_hits` defterinin TEK amacı sağlayıcının kota RESET
    SAATİNİ ölçmek ve o ölçüm ancak gün SINIRINI aşan bir pencerede yapılabilir. Her gece silmek,
    tam da ölçülmek istenen olguyu siliyordu."""
    store.write_json(fmp.USAGE_FILE, {"date": "1999-01-01", "calls": 500, "fails": 400,
                                      "blocked_at": 120,
                                      "quota_hits": [{"at": "1999-01-01T14:00:00+00:00",
                                                      "key": "FMP_API_KEY", "calls_today": 120}]})
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(200, [{"price": 1}]))
    fmp._get_with_key("quote", {"symbol": "A"}, 5.0, "K1", key_name="FMP_API_KEY")

    u = fmp.usage()
    assert u["calls"] == 1 and u["fails"] == 0 and u["blocked_at"] is None, "sayaçlar devredildi"
    assert len(u["quota_hits"]) == 1 and u["quota_hits"][0]["at"].startswith("1999-01-01"), \
        "dünün 429 kaydı silindi — reset saati bir daha ölçülemez"
