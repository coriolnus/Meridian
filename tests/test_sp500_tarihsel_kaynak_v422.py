"""test_sp500_tarihsel_kaynak_v422.py — TSK-156 dilim-1 (2026-09-05) çivisi.

KANIT ZEMİNİ (EDG-2026-075/076, research/olcumler/edg075_sp500_tarihsel/
sonuc_edg076_2026-09-05.json): Wikipedia'nın AYRI 'Historical_components_of_the_S%26P_500'
sayfası — asıl S&P 500 sayfasındaki (eski `tables[1]`) 'Selected changes' tablosunun kalkmasından
BAĞIMSIZ, DAHA GENİŞ bir birincil değişiklik günlüğü — 407 satır, 2020→bugün 136 değişiklik, 0
hayalet, 0 tarih hatası, 28/28 S&P DJI bülten olgusu tarih+yön doğru; as_of yeniden kurulumu güncel
listeyle fark 0. A1'den httpx bu sayfaya (ve ana sayfaya) 200 döner (2026-09-05 ölçüldü); bu ölçüm
`meridian.adapters.constituents` başlığındaki eski "Wikipedia yolu fiilen kapalı" notunu YANLIŞLAR.

TEK KAYNAK SINIRI: tablo ÜYELİK olaylarını (ekleme/çıkarma) taşır, SAF ticker yeniden-adlandırmasını
(şirket S&P 500'de KALIRKEN sembol değiştirmesi) satır olarak taşımaz — o olay yalnız BAŞKA bir
satırın `reason` metninde "(now X)" izi bırakır (EQR→VMRK 2026-08-18: AvalonBay'in kaldırılma
satırının reason'ı "now Vivmark Residential" der, EQR/VMRK'nin KENDİ satırı YOKTUR). Bu yüzden
`as_of()` modül-düzeyi donuk `SEMBOL_YENIDEN_ADLANDIRMA` defterini AYRICA geriye uygular.

İKİ MUTASYON (devir notunda elle doğrulanacak):
  MUTASYON 1 — `_fetch_hist_changes`in tablo seçimi sütun-eşleşmesi yerine `tables[0]`a
  bağlanırsa `test_1_hist_tablo_sutunlardan_secilir_indeksten_degil` KIRMIZI olur (sentetik HTML'de
  alakasız 'See also' tablosu BİLEREK ÖNCE gelir).
  MUTASYON 2 — `as_of()`teki `SEMBOL_YENIDEN_ADLANDIRMA` geri-uygulama bloğu kaldırılırsa
  `test_5_as_of_pre_rename_verir_eqr` KIRMIZI olur (VMRK, 2026-06-01'de de VMRK kalır, EQR'ye
  dönmez).
"""
from __future__ import annotations

import httpx
import pytest

from meridian import store
from meridian.adapters import constituents as con


@pytest.fixture(autouse=True)
def _reset():
    con._HEALTH.update({"ok": None, "source": None, "n": 0, "at": None, "error": ""})
    con._SON_HIST_META = None
    yield
    con._SON_HIST_META = None


def _real_list(n=460, prefix="A"):
    return [f"{prefix}{i:03d}" for i in range(n)]


class _R:
    """httpx.get sahtesi: sabit metin + durum kodu."""

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


_SYMBOL_TABLE = """
<table>
<tr><th>Symbol</th><th>Security</th></tr>
<tr><td>AAPL</td><td>Apple Inc.</td></tr>
</table>
"""

_ALAKASIZ_TABLO = """
<table>
<tr><th>Item</th><th>Description</th></tr>
<tr><td>See also</td><td>List of S&amp;P 500 companies</td></tr>
<tr><td>NASDAQ-100</td><td>Related index</td></tr>
</table>
"""


def _hist_tablo(satirlar: str) -> str:
    """Gerçek Wikipedia 'Historical components' yapısını taklit eden sentetik HTML: alakasız
    tablo ÖNCE (indeks-körlüğünü yakalamak için), gerçek değişiklik tablosu iki başlıklı thead ile
    (MultiIndex → düzleştirilmiş: 'Effective Date_Effective Date', 'Added_Ticker', 'Added_Security',
    'Removed_Ticker', 'Removed_Security', 'Reason_Reason', 'Refs_Refs' — kanıt zemininde ÖLÇÜLEN
    gerçek sütun biçimi, elle doğrulandı: pandas.read_html + lxml)."""
    return _ALAKASIZ_TABLO + f"""
    <table>
    <thead>
    <tr>
    <th rowspan="2">Effective Date</th>
    <th colspan="2">Added</th>
    <th colspan="2">Removed</th>
    <th rowspan="2">Reason</th>
    <th rowspan="2">Refs</th>
    </tr>
    <tr>
    <th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th>
    </tr>
    </thead>
    <tbody>
    {satirlar}
    </tbody>
    </table>
    """


_GECERLI_SATIRLAR = """
<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>October 1, 2024</td><td>NEW</td><td>New Co</td><td>OLD</td><td>Old Co</td><td>replaced</td><td>[1]</td></tr>
<tr><td>TBD</td><td>FOO</td><td>Foo Co</td><td>BAR</td><td>Bar Co</td><td>pending review</td><td>[2]</td></tr>
<tr><td>August 18, 2026</td><td>XYZ</td><td>Some Co</td><td>AVB</td><td>AvalonBay</td><td>Equity Residential (now Vivmark Residential) acquired AvalonBay</td><td>[3]</td></tr>
<tr><td>March 5, 2023</td><td>ZZZ</td><td>Zz Co</td><td>QQQ</td><td>Qq Co</td><td>Foo Corp (now Bar Corp) renamed</td><td>[4]</td></tr>
"""

_REVID_ISARETI = '<script>var x = {"wgRevisionId":123456789,"other":1};</script>'


def _hist_html_gecerli() -> str:
    return _hist_tablo(_GECERLI_SATIRLAR) + _REVID_ISARETI


def _real_list_html() -> str:
    satirlar = "".join(f"<tr><td>{s}</td><td>{s} Inc.</td></tr>" for s in _real_list())
    return f"<table><tr><th>Symbol</th><th>Security</th></tr>{satirlar}</table>"


def _router(wiki_html: str, hist_html: str, hist_status: int = 200, wiki_status: int = 200):
    """URL'ye göre ana sayfa / tarihsel sayfa döndüren httpx.get sahtesi (A1 kalıbı: iki AYRI
    Wikipedia sayfası, iki AYRI yanıt)."""

    def _get(url, **kwargs):
        if url == con.HIST_URL:
            return _R(hist_html, hist_status)
        return _R(wiki_html, wiki_status)

    return _get


# ---------------------------------------------------------------------------
# 1) Tablo sütunlardan seçilir, indeksten DEĞİL — MUTASYON 1
# ---------------------------------------------------------------------------
def test_1_hist_tablo_sutunlardan_secilir_indeksten_degil(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", _router(_SYMBOL_TABLE, _hist_html_gecerli()))
    rows, meta = con._fetch_hist_changes()
    tarihler = {r["date"] for r in rows}
    assert "2024-10-01" in tarihler, f"alakasız tablo önce geldiği için gerçek tablo kaçırıldı: {rows}"
    assert meta is not None and meta["n_satir"] == len(rows)


# ---------------------------------------------------------------------------
# 2) Hayalet satır yazılmaz; tarih ayrışmayan satır yazılmaz + sayılır; reason taşınır; meta dolu
# ---------------------------------------------------------------------------
def test_2_hayalet_ve_tarihsiz_satirlar_ve_meta(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", _router(_SYMBOL_TABLE, _hist_html_gecerli()))
    rows, meta = con._fetch_hist_changes()

    # hayalet (üç alan da boş) hiç yazılmadı
    assert all(r["date"] for r in rows), f"hayalet satır sızdı: {rows}"
    assert not any(r["added"] == "" and r["removed"] == "" for r in rows)

    # "TBD" tarihi ayrışmadı: satır yazılmadı AMA sayıldı
    assert not any(r["added"] == "FOO" for r in rows), "ayrışmayan tarihli satır yazılmamalıydı"
    assert meta["n_tarih_yok"] == 1

    # reason aynen taşınıyor
    ekim = next(r for r in rows if r["date"] == "2024-10-01")
    assert ekim["reason"] == "replaced"
    assert ekim["added"] == "NEW" and ekim["removed"] == "OLD"

    # meta oldid/sha256 dolu
    assert meta["oldid"] == 123456789
    assert isinstance(meta["sha256"], str) and len(meta["sha256"]) == 64
    assert meta["n_satir"] == len(rows)
    assert meta["cekim_ts"]


# ---------------------------------------------------------------------------
# 3) _fetch_tables: changes hist'ten, changes_kaynak == wikipedia_historical_components;
#    hist HTTP 403 → eski tables[1] yoluna düşer, üçlü imza korunur
# ---------------------------------------------------------------------------
def test_3_fetch_tables_hist_oncelikli(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", _router(_SYMBOL_TABLE, _hist_html_gecerli()))
    cur, changes, changes_kaynak = con._fetch_tables()
    assert cur == ["AAPL"]
    assert changes_kaynak == "wikipedia_historical_components"
    assert any(r["date"] == "2024-10-01" for r in changes)


def test_3b_fetch_tables_hist_403_eski_yola_duser(sandbox_state, monkeypatch):
    # hist sayfası 403 — main sayfada eski 'Selected changes' biçiminde bir tablo VAR (tables[1])
    eski_degisiklik_tablosu = """
    <table>
    <tr><th>Date</th><th>Added Ticker</th><th>Removed Ticker</th></tr>
    <tr><td>March 5, 2023</td><td>FOO</td><td>BAR</td></tr>
    </table>
    """
    wiki_html = _SYMBOL_TABLE + eski_degisiklik_tablosu
    monkeypatch.setattr(httpx, "get", _router(wiki_html, "<html>yasak</html>", hist_status=403))
    cur, changes, changes_kaynak = con._fetch_tables()
    assert cur == ["AAPL"]
    assert changes_kaynak == "wikipedia_selected_changes"
    assert changes == [{"date": "March 5, 2023", "added": "FOO", "removed": "BAR"}]
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "sp500_tarihsel_tablo_yok"]
    assert ev, "hist başarısızlığı obs.warn('sp500_tarihsel_tablo_yok', ...) ile kaydedilmedi"
    assert ev[-1]["url"] == con.HIST_URL


# ---------------------------------------------------------------------------
# 4) current(): wikipedia dalı önbelleğe changes_meta yazar; fmp dalı hist başarısızken
#    önbellekteki changes'i EZMEZ
# ---------------------------------------------------------------------------
def test_4a_current_wikipedia_dali_changes_meta_yazar(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(httpx, "get", _router(_real_list_html(), _hist_html_gecerli()))
    syms = con.current()
    assert len(syms) >= con.MIN_MEMBERS
    cached = store.read_json(con.CACHE, {})
    assert cached.get("changes_kaynak") == "wikipedia_historical_components"
    assert cached.get("changes_meta") and cached["changes_meta"]["oldid"] == 123456789


def test_4b_current_fmp_dali_hist_basarisizken_changes_ezmez(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    eski_meta = {"oldid": 1, "sha256": "eski", "n_satir": 2, "n_tarih_yok": 0,
                "cekim_ts": "2026-09-01T00:00:00+00:00"}
    store.write_json(con.CACHE, {"as_of": "2026-09-01", "current": _real_list(),
                                 "changes": [{"date": "2026-01-01", "added": "OLD1", "removed": "OLD2",
                                             "reason": "eski"}],
                                 "changes_kaynak": "wikipedia_historical_components",
                                 "changes_meta": eski_meta, "source": "wikipedia"})
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "sp500_constituents", lambda: _real_list(prefix="B"))
    # hist HTTP 403 → _fetch_hist_changes() boş döner
    monkeypatch.setattr(httpx, "get", _router("<html></html>", "<html>yasak</html>", hist_status=403))
    syms = con.current()
    assert syms == _real_list(prefix="B")
    cached = store.read_json(con.CACHE, {})
    assert cached.get("source") == "fmp"
    # ÖNBELLEKTEKİ changes/changes_kaynak/changes_meta KORUNDU, boşla EZİLMEDİ
    assert cached.get("changes") == [{"date": "2026-01-01", "added": "OLD1", "removed": "OLD2",
                                      "reason": "eski"}]
    assert cached.get("changes_kaynak") == "wikipedia_historical_components"
    assert cached.get("changes_meta") == eski_meta


# ---------------------------------------------------------------------------
# 5) as_of: rename eşleme — MUTASYON 2
# ---------------------------------------------------------------------------
def test_5_as_of_pre_rename_verir_eqr(sandbox_state):
    """`as_of("2026-06-01")` VMRK yerine EQR verir (rename 2026-08-18'de yürürlüğe girdi, o
    tarihten ÖNCESİ hâlâ EQR)."""
    store.write_json(con.CACHE, {"as_of": "2026-09-05",
                                 "current": _real_list() + ["VMRK"],
                                 "changes": [], "changes_kaynak": None, "changes_meta": None})
    sonuc = con.as_of("2026-06-01")
    assert "EQR" in sonuc
    assert "VMRK" not in sonuc


def test_6_as_of_rename_sonrasi_tarihte_yeni_kalir(sandbox_state):
    """`as_of("2026-09-01")` VMRK verir (rename tarihinden SONRA — geri alınmaz). Bu test
    `test_5` ile BİRLİKTE mutasyonu yakalar: yalnız bu test mutasyonla da yeşil kalırdı."""
    store.write_json(con.CACHE, {"as_of": "2026-09-05",
                                 "current": _real_list() + ["VMRK"],
                                 "changes": [], "changes_kaynak": None, "changes_meta": None})
    sonuc = con.as_of("2026-09-01")
    assert "VMRK" in sonuc
    assert "EQR" not in sonuc


# ---------------------------------------------------------------------------
# 6) rename_adaylari: "(now X)" kalıbı → aday; kayıtlı rename tarihiyle eşleşmeyen aday → warn
# ---------------------------------------------------------------------------
def test_7_rename_adaylari_ve_uyari(sandbox_state, monkeypatch):
    monkeypatch.setattr(httpx, "get", _router(_SYMBOL_TABLE, _hist_html_gecerli()))
    rows, _meta = con._fetch_hist_changes()

    adaylar = con.rename_adaylari(rows)
    ad_lar = {a["reason_ad"] for a in adaylar}
    assert "Vivmark Residential" in ad_lar
    assert "Bar Corp" in ad_lar

    # kayıtlı SEMBOL_YENIDEN_ADLANDIRMA tarihi (2026-08-18) eşleşiyor; 2023-03-05 eşleşmiyor —
    # eşleşmeyen aday olduğu için TEK obs.warn("sp500_rename_adayi", ...) yazıldı
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "sp500_rename_adayi"]
    assert len(ev) == 1, f"tek uyarı beklenir, {len(ev)} bulundu: {ev}"
    assert ev[0]["n"] == 1
    assert any(o.get("reason_ad") == "Bar Corp" for o in ev[0]["ornek"])


def test_7b_rename_adaylari_saf_fonksiyon_boyle_calisir():
    """`rename_adaylari` doğrudan çağrıldığında (ağsız) davranışı: eşleşen/eşleşmeyen ayrımı
    yalnız `reason` metnine bakar, "(now X)" kalıbı yoksa aday üretmez."""
    changes = [
        {"date": "2020-01-01", "added": "A", "removed": "B", "reason": "no pattern here"},
        {"date": "2021-02-02", "added": "C", "removed": "D", "reason": "Foo (now Bar) merged"},
    ]
    adaylar = con.rename_adaylari(changes)
    assert len(adaylar) == 1
    assert adaylar[0] == {"date": "2021-02-02", "added": "C", "removed": "D", "reason_ad": "Bar"}


# ---------------------------------------------------------------------------
# 7) as_of_pit_durumu: hist kaynaklı + sonraki geçerli satır → pit True, kaynak_sinifi
#    "tarihsel_tablo", changes_meta dolu
# ---------------------------------------------------------------------------
def test_8_as_of_pit_durumu_tarihsel_tablo(sandbox_state):
    meta = {"oldid": 42, "sha256": "abc", "n_satir": 1, "n_tarih_yok": 0,
            "cekim_ts": "2026-09-05T00:00:00+00:00"}
    store.write_json(con.CACHE, {"as_of": "2026-09-05", "current": _real_list() + ["NEW"],
                                 "changes": [{"date": "2026-08-01", "added": "NEW", "removed": "OLD",
                                             "reason": "x"}],
                                 "changes_kaynak": "wikipedia_historical_components",
                                 "changes_meta": meta})
    d = con.as_of_pit_durumu("2025-01-01")
    assert d["pit"] is True
    assert d["neden"] is None
    assert d["changes_kaynak"] == "wikipedia_historical_components"
    assert d["kaynak_sinifi"] == "tarihsel_tablo"
    assert d["changes_meta"] == meta


def test_8b_as_of_pit_durumu_secilmis_degisiklikler_siniflanir(sandbox_state):
    """Eski (TSK-154) `wikipedia_selected_changes` kaynağı `kaynak_sinifi='secilmis_degisiklikler'`
    ile ayırt edilir — tarihsel tablo ile karışmaz."""
    store.write_json(con.CACHE, {"as_of": "2026-09-05", "current": _real_list() + ["NEW"],
                                 "changes": [{"date": "2026-08-01", "added": "NEW", "removed": "OLD"}],
                                 "changes_kaynak": "wikipedia_selected_changes", "changes_meta": None})
    d = con.as_of_pit_durumu("2025-01-01")
    assert d["kaynak_sinifi"] == "secilmis_degisiklikler"
    assert d["changes_meta"] is None


def test_8c_as_of_pit_durumu_kaynaksizken_sinif_none(sandbox_state):
    store.write_json(con.CACHE, {"as_of": "2026-09-05", "current": _real_list(),
                                 "changes": [], "changes_kaynak": None, "changes_meta": None})
    d = con.as_of_pit_durumu("2025-01-01")
    assert d["pit"] is False
    assert d["kaynak_sinifi"] is None
    assert d["changes_meta"] is None
