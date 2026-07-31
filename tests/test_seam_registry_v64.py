"""test_seam_registry_v64.py — KAYNAK DİKİŞİ: BİR KEZ SÖYLE, SAYMAYA DEVAM ET (2026-07-22).

Dikiş koruması doğru çalışıyordu ama HER sembolde HER tazelemede uyarı basıyordu: 250 satır × her
tur. Bu, susturmaktan beter bir durumdu — gerçek uyarılar (kota, karantina, sızıntı) bu gürültünün
içinde görünmez oluyordu. Operatör: "sustur, bir kez kaydetsin tekrar etmesin."

Ama SESSİZCE yok saymak da olmaz: dikiş, geçmişin artık yayın yapmayan bir kaynağa ait olduğu
anlamına gelir ve KALICI bir durumdur. Bugün kapattığımız hata sınıfının kendisi "üretilen kanıtın
tüketilmemesi"ydi. Kural bu yüzden üç parçalı ve üçü de burada kilitli:
  1. DURUM DEĞİŞİMİ bir kez uyarır (ilk görülme ya da kaynak çifti değişimi),
  2. tekrarlar sayılır ama LOGLANMAZ,
  3. toplam `seam_report()` ile okunabilir kalır (teşhis ucu + pano onu gösterir).
"""
from __future__ import annotations

import pytest

from meridian import store
from meridian.adapters import data


@pytest.fixture(autouse=True)
def _clean(sandbox_state):
    data._SEAMS.clear()
    data._SEAM_DIRTY = 0
    yield
    data._SEAMS.clear()


def _warns(event: str) -> int:
    return sum(1 for e in store.read_jsonl("events.jsonl") if e.get("event") == event)


def test_first_seam_warns_once():
    data._record_seam("AAPL", "cboe", "nasdaq", 1)
    assert _warns("bar_source_seam_opened") == 1
    assert store.read_json(data.SEAM_FILE, {})["AAPL"]["pinned"] == "cboe"


def test_repeats_are_counted_not_logged():
    """Asıl istek: 250 sembol × her tur = log çöplüğü. Tekrar SAYILIR, basılmaz."""
    for _ in range(40):
        data._record_seam("AAPL", "cboe", "nasdaq", 0)
    assert _warns("bar_source_seam_opened") == 1, "tekrarlar yeniden uyarı üretmiş"
    assert data._seams()["AAPL"]["n"] == 40, "tekrar SAYILMAMIŞ — susturmak yok saymak değildir"


def test_a_changed_source_pair_is_a_new_finding():
    """Kaynak çifti değişirse bu YENİ bir durumdur: geçmişi başka bir kaynak sunmaya başlamış."""
    data._record_seam("AAPL", "cboe", "nasdaq", 1)
    data._record_seam("AAPL", "cboe", "fmp", 1)
    assert _warns("bar_source_seam_opened") == 2


def test_many_tickers_produce_one_line_each_not_one_per_fetch():
    """Canlı senaryo: 213 sembol, 3 tazeleme turu. Eskiden 639 satır; şimdi 213."""
    for tur in range(3):
        for i in range(213):
            data._record_seam(f"T{i}", "cboe", "nasdaq", 0)
    assert _warns("bar_source_seam_opened") == 213
    assert data._seams()["T0"]["n"] == 3


def test_the_silenced_total_stays_readable():
    """SUSTURULAN UYARI GÖRÜNÜR KALIR — yoksa 'üretilip tüketilmeyen kanıt' sınıfına düşerdi."""
    for i in range(12):
        data._record_seam(f"T{i}", "cboe", "nasdaq", 0)
    data._record_seam("XYZ", "fmp", "cboe", 0)
    rep = data.seam_report()
    assert rep["tickers"] == 13
    assert rep["by_pair"]["cboe→nasdaq"] == 12 and rep["by_pair"]["fmp→cboe"] == 1
    assert rep["oldest"] and rep["sample"]["cboe→nasdaq"]


def test_registry_survives_a_restart():
    """Süreç yeniden başlarsa uyarı TEKRAR basılmamalı — durum diskte kayıtlı."""
    data._record_seam("AAPL", "cboe", "nasdaq", 1)
    data.flush_seams()
    data._SEAMS.clear()                       # süreç yeniden başladı
    data._record_seam("AAPL", "cboe", "nasdaq", 0)
    assert _warns("bar_source_seam_opened") == 1
    assert data._seams()["AAPL"]["n"] == 2


def test_writes_are_batched_not_per_ticker():
    """250'lik tazelemede her sembolde bir kilitli yazım yapılmaz — tekrarlar toplu yazılır."""
    assert data._SEAM_FLUSH_EVERY >= 10
    data._record_seam("AAPL", "cboe", "nasdaq", 1)      # yeni dikiş → yazar
    n0 = store.io_stats().get("writes", 0)
    for _ in range(data._SEAM_FLUSH_EVERY - 1):
        data._record_seam("AAPL", "cboe", "nasdaq", 0)
    assert store.io_stats().get("writes", 0) == n0, "her tekrar diske yazıyor — toplu yazım yok"


def test_the_guard_itself_still_blocks_history_rewrites():
    """Sessizleştirme KORUMAYI zayıflatmamalı: farklı kaynak hâlâ yalnız YENİ tarih ekleyebilir.

    2026-07-30'da kural TEK bir istisna kazandı (aynı-akşam bacağı + T+1 düzeltmesi): otoriter bir
    kaynak, BACAĞIN KENDİ yazdığı GEÇİCİ barı ezebilir. İstisna DAR ve ADLIDIR — kapı `_prov`
    kümesidir, yani `_provisional_dates(ticker)`; başka hiçbir tarih bu kapıdan geçemez. İstisna
    olmasaydı düzeltme yapısal olarak imkânsızdı: IEX barı sonsuza dek geçmişte kalırdı."""
    import inspect
    src = inspect.getsource(data.load_bars)
    assert "_record_seam(" in src
    assert "_prov = _provisional_dates(ticker)" in src, "istisna kümesi ADSIZ — kapı ölçülemez"
    assert 'newer = fetched[(fetched["date"] > cached["date"].max()) | _fd2.isin(_prov)]' in src
    assert "fetched = newer" in src
    # BACAĞIN KENDİSİ DE AYNI KURALA TABİ: geçmişe yazamaz, yalnız son bardan SONRASI (ya da kendi
    # geçici barının tazelenmesi). Bu satır olmadan sabitlenmemiş bir sembolde temsilî bir bar,
    # önbellekteki konsolide barı sessizce ezebilirdi — düzeltmenin TERS yönü.
    assert 'fetched = fetched[(fetched["date"] > cached["date"].max()) | _fd.isin(_prov)]' in src


def test_the_exception_is_only_for_bars_the_leg_itself_wrote():
    """İstisna kümesinin ÜRETİCİSİ de kilitlenir: geçici damga YALNIZ aynı-akşam bacağının yazdığı
    satırlara konur (`_LEG_SOURCES`). Başka bir kaynak kendi barını 'geçici' ilan edip ertesi gün
    geçmişi yeniden yazamaz — dikiş korumasının delinme yolu tam da bu olurdu."""
    import inspect
    src = inspect.getsource(data.load_bars)
    i = src.index("_note_provisional(")
    assert "if src in _LEG_SOURCES:" in src[:i], "geçici damga kaynak sınıfına bağlı değil"
    assert data._LEG_SOURCES and all(s.startswith("alpaca_") for s in data._LEG_SOURCES)
    # damga DİSKE YAZIM SONRASI konur: yazılmamış bir bar hakkında hüküm bırakılmaz
    assert src.index("_write_bars(merged, cp)") < i


def test_report_is_consumed_by_the_diagnostics_endpoint():
    import pathlib
    api = pathlib.Path("meridian/api.py").read_text()
    js = pathlib.Path("meridian/web/app.js").read_text()
    assert "seam_report" in api, "toplam sunulmuyor"
    assert "bar_source_seams" in js, "pano susturulan durumu OKUMUYOR"
