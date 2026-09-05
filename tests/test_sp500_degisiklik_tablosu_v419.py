"""test_sp500_degisiklik_tablosu_v419.py — TSK-154 (2026-09-05) çivisi.

BULGU (TSK-143 keşfi): Wikipedia S&P 500 sayfasındaki 'Selected changes' tablosu (eskiden
`tables[1]`) KALKTI. Eski `_fetch_tables` bunu ayırt etmiyordu: sütun eşleşmesi (Date/Added
Ticker/Removed Ticker) hiç bulunamayınca `dcol/acol/rcol` hepsi `None` kalıyor, `row.get(None)`
her satırda `None` dönüyor, `_cell(None)` bunu ""ya çeviriyor — SONUÇ: gerçek tablo NE olursa
olsun `changes` alanı N satır {date:'',added:'',removed:''} ile doluyordu (A1'de 11 satır,
uyarısız). `constituents.as_of()` böyle boş-ama-dolu bir günlükle geriye sararken hiçbir satır
`_iso(date)` üretmediği için hiçbir değişikliği geri almıyor ve sessizce BUGÜNKÜ listeyi PIT
sanıyordu (survivorship, `pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI[('constituents','as_of')]`
zaten bunu 'besleyeni kapalı' diye BEYAN ediyordu — hüküm tutarlı ama ÖNBELLEK YAZIMI sessizdi).

RULING (D1/D2, Rol-1): (1) `_fetch_tables` artık sütun eşleşmesi yoksa tabloyu 'değişiklik günlüğü
DEĞİL' sayıp `changes=[]` + `changes_kaynak=None` + `obs.warn('sp500_degisiklik_tablosu_yok', ...)`
yazar (Yasa 4: sessiz değil); (2) üç alanı da boş satır (hayalet) hiçbir zaman `changes`e
YAZILMAZ — sütun eşleşse bile (rowspan/birleşik hücre gibi başka bir hayalet-satır kaynağına karşı
ikinci savunma); (3) `as_of_pit_durumu(date)` günlük boşken/`date` kapsamının dışındayken
`as_of()`un GERÇEK PIT değil bugünkü listeye eşit survivorship olduğunu `{"pit": False, "neden":
...}` ile BEYAN eder — `as_of()`un kendi `list[str]` dönüş biçimi DEĞİŞMEDİ (üretim çağıranı yok).

Dört test — mutasyon: (2)'deki hayalet-satır süzgeci (`if not (d or a or rm): continue`)
kaldırılınca `test_2_hayalet_satir_yazilmaz` KIRMIZI olur (elle doğrulandı, bkz. devir notu)."""
from __future__ import annotations

import httpx
import pandas as pd
import pytest

from meridian import store
from meridian.adapters import constituents as con


@pytest.fixture(autouse=True)
def _reset():
    con._HEALTH.update({"ok": None, "source": None, "n": 0, "at": None, "error": ""})
    yield


def _real_list(n=460, prefix="A"):
    return [f"{prefix}{i:03d}" for i in range(n)]


class _R:
    """httpx.get sahtesi: sabit metin, 200."""
    status_code = 200

    def __init__(self, text):
        self.text = text


_SYMBOL_TABLE = """
<table>
<tr><th>Symbol</th><th>Security</th></tr>
<tr><td>AAPL</td><td>Apple Inc.</td></tr>
</table>
"""


def test_1_degisiklik_tablosu_yokken_bos_ve_uyarili(sandbox_state, monkeypatch):
    """Tablo VAR ama sütunları (Date/Added Ticker/Removed Ticker) eşleşmiyor — canlıdaki gerçek
    kök neden (A1: `tables[1]` artık başka bir tablo). `changes=[]`, `changes_kaynak=None`,
    `obs.warn('sp500_degisiklik_tablosu_yok', ...)` yazılır (Yasa 4)."""
    html = _SYMBOL_TABLE + """
    <table>
    <tr><th>Item</th><th>Description</th></tr>
    <tr><td>See also</td><td>List of S&amp;P 500 companies</td></tr>
    <tr><td>NASDAQ-100</td><td>Related index</td></tr>
    </table>
    """
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(html))
    cur, changes, changes_kaynak = con._fetch_tables()
    assert changes == []
    assert changes_kaynak is None
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "sp500_degisiklik_tablosu_yok"]
    assert ev, "obs.warn('sp500_degisiklik_tablosu_yok', ...) yazılmadı"
    assert ev[-1]["tablo_n"] == 2


def test_2_hayalet_satir_yazilmaz(sandbox_state, monkeypatch):
    """Sütunlar eşleşiyor (gerçek değişiklik günlüğü) AMA bir satırın üç alanı da boş (hayalet —
    rowspan/birleşik hücre benzeri bir ayrıştırma artığı). O satır `changes`e YAZILMAZ; gerçek
    satır aynen kalır. MUTASYON: `_fetch_tables`teki `if not (d or a or rm): continue` satırı
    kaldırılırsa bu test KIRMIZI olur (elle doğrulandı)."""
    html = _SYMBOL_TABLE + """
    <table>
    <tr><th>Date</th><th>Added Ticker</th><th>Removed Ticker</th></tr>
    <tr><td>October 1, 2024</td><td>NEW</td><td>OLD</td></tr>
    <tr><td></td><td></td><td></td></tr>
    </table>
    """
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(html))
    cur, changes, changes_kaynak = con._fetch_tables()
    assert changes == [{"date": "October 1, 2024", "added": "NEW", "removed": "OLD"}]
    assert changes_kaynak == "wikipedia_selected_changes"
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "sp500_degisiklik_tablosu_yok"]
    assert not ev, "geçerli tabloda 'tablo yok' uyarısı YANLIŞ ateşlendi"


def test_3_gecerli_tablo_satirlari_aynen(sandbox_state, monkeypatch):
    """Ghost-satır yokken iki geçerli değişiklik satırı aynen (regresyon: mevcut davranış
    bozulmadı — sıra ve alan değerleri korunur)."""
    html = _SYMBOL_TABLE + """
    <table>
    <tr><th>Date</th><th>Added Ticker</th><th>Removed Ticker</th></tr>
    <tr><td>October 1, 2024</td><td>NEW</td><td>OLD</td></tr>
    <tr><td>March 5, 2023</td><td>FOO</td><td>BAR</td></tr>
    </table>
    """
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R(html))
    cur, changes, changes_kaynak = con._fetch_tables()
    assert changes == [
        {"date": "October 1, 2024", "added": "NEW", "removed": "OLD"},
        {"date": "March 5, 2023", "added": "FOO", "removed": "BAR"},
    ]
    assert changes_kaynak == "wikipedia_selected_changes"
    assert cur == ["AAPL"]


def test_4_as_of_pit_durumu_beyani(sandbox_state):
    """`changes` boşken (TSK-154 kök neden: tablo kalktı) `as_of_pit_durumu` `pit=False` +
    `neden` beyanı taşır — `as_of()`un kendi `list[str]` dönüşü DEĞİŞMEZ. Günlük DOLUYKEN ve
    `date`ten sonraki geçerli bir satır varken `pit=True` döner (karşıt uç, aynı fonksiyon)."""
    store.write_json(con.CACHE, {"as_of": "2026-09-05", "current": _real_list(),
                                 "changes": [], "changes_kaynak": None})
    d = con.as_of_pit_durumu("2025-01-01")
    assert d["pit"] is False
    assert d["neden"] and "değişiklik tablosu yok" in d["neden"]
    assert d["changes_kaynak"] is None
    # as_of()'un kendisi hâlâ düz liste — sözleşme değişmedi
    assert con.as_of("2025-01-01") == sorted(_real_list())

    store.write_json(con.CACHE, {"as_of": "2026-09-05", "current": _real_list() + ["NEW"],
                                 "changes": [{"date": "2026-08-01", "added": "NEW", "removed": "OLD"}],
                                 "changes_kaynak": "wikipedia_selected_changes"})
    d2 = con.as_of_pit_durumu("2025-01-01")
    assert d2["pit"] is True and d2["neden"] is None
    assert d2["changes_kaynak"] == "wikipedia_selected_changes"
