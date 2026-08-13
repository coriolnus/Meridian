"""test_tohum_parity_yuku_v243.py — TOHUM DİLİMİ PANO YOLUNU BOĞMASIN (2026-08-13, ACİL ARIZA).

VAKA (canlı A1, 2026-08-13 20:2xZ, operatör bildirdi — Rol-1 ölçtü): pano yüklenmiyor.
`/api/today` 0,18 sn · `/api/approvals` 0,05 sn · `/api/summary` 0,49 sn AYAKTA;
`/api/diagnostics` 20-90 sn TIMEOUT. Kök `watchdog.parity_report` (16.705 ms) ve onun içinde
`recompute.report()` → `ledger_matches_bars`: baktığı HER işlem satırı için `adapters.data.
load_bars` çağrılıyor (sembolün TÜM önbellek CSV'si + tam `sanitize_bars` + tek güne dilimleme).
Aynı gün 18:54Z tohum yenilemesi `trades.jsonl`ı 97→887 satıra çıkarmıştı.

ÖLÇÜM-1 · DEFTER BOYU DENEYİ (yerel kum havuzu, canlı defter boyutuna tohumlanmış; aynı state,
aynı sıcak bar önbelleği, DEĞİŞEN TEK ŞEY defter boyu):
     95 satır →  95 load_bars / 1.064 ms · recompute.report 2.554 ms · parity_report 3.481 ms
    887 satır → 400 load_bars / 4.032 ms · recompute.report 5.650 ms · parity_report 6.680 ms
  düzeltmeden SONRA (887 satır) → 0 load_bars · parity_report 2.459 ms soğuk / 457 ms sıcak süreç
  (sıcak süreç düzeltme ÖNCESİ 4.161 ms idi — canlı sunucu uzun ömürlü bir süreçtir, işleyen sayı
  budur).

ÖLÇÜM-2 · UÇ SEVİYESİ A/B (aynı süreç, aynı kum havuzu, 887 satır; `?taze=1` + `watchdog.
_INTEGRITY_CACHE` boşaltılmış — yani GERÇEK soğuk teşhis hesabı. İki kol arasındaki tek fark
tohum diliminin taranıp taranmaması):
    ÖNCE  `/api/diagnostics` 4.628 ms · 4.847 ms
    SONRA `/api/diagnostics` 1.097 ms · 1.107 ms      (≈4,3×; −3,7 sn)
    45 sn'lik yanıt zarfından servis edilirken: 10 ms · `/api/today`: 44 ms

NOT (ölçüm sırasında bulundu, kayda geçer): `?taze=1` YALNIZ API'nin 45 sn'lik yanıt zarfını
atlar; `watchdog.integrity_report_cached`in KENDİ 20 sn'lik önbelleğini DEĞİL. Yani art arda iki
`taze=1` isteği bütünlük raporunu yeniden hesaplatmaz — teşhis ederken bu bilinmeli.

BU DOSYA NEYİ ÇİVİLER: süreyi DEĞİL (süre-tabanlı çivi kırılgandır ve makineye bağlıdır),
DAVRANIŞI — `replay_seed` satırları pano yolunda mutabakat hesabına HİÇ girmez, dışlama ADIYLA
SAYILIR (sessiz filtreleme yasağı), ve dışlama bir KÖRLÜK değil bir YOL AYRIMIDIR: `deep=True`
(gece işi) defterin tamamını görmeye devam eder.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from meridian import ledgerstamp, recompute, store
from meridian.adapters import data as _dt

D0 = "2026-08-10"
APP_JS = pathlib.Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js"


def _islem(i: int, kaynak: str | None, tk: str) -> dict:
    """Sözleşmeye uyan asgari işlem satırı (ledgers.CONTRACTS: trades.jsonl)."""
    r = {"id": f"T{i:05d}", "ts_open": D0, "ts_close": D0, "ticker": tk, "entry": 100.0,
         "r_multiple": 0.5, "pnl_dollars": 10.0, "plan_id": f"P-2026-08-10-{tk}",
         "regime": "chop", "score": 70, "setup": "breakout_vcp", "strategy_version": 4}
    if kaynak is not None:
        r["kaynak"] = kaynak
    return r


@pytest.fixture
def bar_casusu(monkeypatch):
    """`load_bars`ı SAYAN saplama + her sembolün önbelleği VARMIŞ gibi davranan `_cache_path`.

    Gerçek `load_bars` çağrılsaydı test ağa/diske bağlı olurdu; burada ölçülen şey ZATEN çağrının
    KENDİSİDİR — kaç kez ve HANGİ satır için yapıldığı."""
    cagrilar: list[tuple[str, str]] = []

    def _sahte_load_bars(ticker, start, end, use_cache=True, **kw):
        cagrilar.append((str(ticker), str(start)))
        return pd.DataFrame({"date": [pd.Timestamp(start)], "open": [100.0], "high": [101.0],
                             "low": [99.0], "close": [100.5], "volume": [1000]})

    class _VarOlanYol:
        def exists(self):
            return True

    monkeypatch.setattr(_dt, "load_bars", _sahte_load_bars)
    monkeypatch.setattr(_dt, "_cache_path", lambda tk: _VarOlanYol())
    return cagrilar


def _defter_yaz(tohum_n: int, canli: list[tuple[str, str | None]]) -> None:
    """`tohum_n` tane `replay_seed` + `canli` listesindeki (ticker, kaynak) satırları."""
    rows = [_islem(i, ledgerstamp.REPLAY_SEED, f"S{i % 90:02d}") for i in range(tohum_n)]
    rows += [_islem(90000 + k, kaynak, tk) for k, (tk, kaynak) in enumerate(canli)]
    store.write_jsonl("trades.jsonl", rows)


def _satir(rep: dict, ad: str = "ledger_matches_bars") -> dict:
    return next(r for r in rep["rows"] if r["check"] == ad)


# ---- 1) DAVRANIŞSAL ÇİVİ: tohum satırı mutabakat yoluna GİRMEZ --------------------------------
def test_tohum_satirlari_pano_yolunda_bar_okumasi_tetiklemez(sandbox_state, bar_casusu):
    """300 tohum + 2 canlı satır → YALNIZ iki canlı satır için bar okunur.

    POZİTİF KONTROL aynı iddianın içinde: sayı 0 değil 2'dir — yani dedektör kapatılmadı,
    kapsamı canlı dilime indirildi. Damgasız (tarihsel) satır da İÇERİDE kalır: `kaynak` alanı
    olmayan bir satırı tohum saymak, ölçülmemiş bir kökeni varsaymak olurdu."""
    _defter_yaz(300, [("AAA", ledgerstamp.LIVE_PAPER), ("BBB", None)])

    rep = recompute.report()

    assert len(bar_casusu) == 2, f"canlı dilim 2 satır, bar okuması {len(bar_casusu)}: {bar_casusu}"
    assert {t for t, _ in bar_casusu} == {"AAA", "BBB"}
    assert not any(t.startswith("S") for t, _ in bar_casusu), "tohum sembolü mutabakata girdi"
    assert _satir(rep)["b"] == 2      # payda = karşılaştırılan satır sayısı


# ---- 2) DIŞLAMA SESSİZ DEĞİL: adıyla ve sayısıyla görünür -------------------------------------
def test_dislama_adiyla_ve_sayisiyla_beyan_edilir(sandbox_state, bar_casusu):
    """Sessiz bir filtre paydayı okuyucudan gizler: "2 işlem birebir" cümlesi, 300 satır
    atlanmışken de aynı görünürdü. Satır dışlanan dilimi ADIYLA taşımak ZORUNDA."""
    _defter_yaz(300, [("AAA", ledgerstamp.LIVE_PAPER)])

    detay = _satir(recompute.report())["detail"]

    assert "replay_seed_haric: 300" in detay, detay
    assert "--deep" in detay, "dışlananın nerede ölçüldüğü söylenmiyor: " + detay


# ---- 3) DOĞRUSAL PATLAMA ÇİVİSİ: defter büyür, mutabakat yükü BÜYÜMEZ -------------------------
@pytest.mark.parametrize("tohum_n", [100, 300, 900])
def test_defter_buyumesi_mutabakat_yukunu_artirmaz(sandbox_state, bar_casusu, tohum_n):
    """Arızanın SINIFI buydu: yük defter boyuyla doğrusal büyüyordu (95→887 satır = 95→400
    bar okuması). Tohum dilimi 9 katına çıksa da pano yolunun bar okuması SABİT kalmalı."""
    _defter_yaz(tohum_n, [("AAA", ledgerstamp.LIVE_PAPER)])

    recompute.report()

    assert len(bar_casusu) == 1, (f"{tohum_n} tohum satırında {len(bar_casusu)} bar okuması — "
                                  f"yük defter boyuyla büyüyor")


# ---- 4) DIŞLAMA BİR KÖRLÜK DEĞİL, YOL AYRIMI: gece işi tohumu GÖRÜR ---------------------------
def test_deep_yolu_tohum_dilimini_gorur(sandbox_state, bar_casusu):
    """`report(deep=True)` defterin TAMAMINA bakar. Bu çivi olmasaydı düzeltme, dedektörü
    sessizce emekliye ayırmanın kibar bir biçimi olurdu. (Düzeltmeden önce `trades[-400:]`
    KOŞULSUZDU — yani docstring'in "gece işi tamamını görür" sözü YANLIŞTI.)"""
    _defter_yaz(20, [("AAA", ledgerstamp.LIVE_PAPER)])

    rep = recompute.report(deep=True)

    assert len(bar_casusu) == 21, f"gece işi tohumu atladı: {len(bar_casusu)} okuma"
    assert any(t.startswith("S") for t, _ in bar_casusu)
    assert "replay_seed_haric" not in _satir(rep)["detail"], "deep yolunda dışlama olmamalı"


# ---- 5) CANLI DİLİM BOŞSA SATIR KAYBOLMAZ -----------------------------------------------------
def test_canli_dilim_bos_olsa_bile_satir_gorunur(sandbox_state, bar_casusu):
    """Tohum yenilemesinden hemen sonraki NORMAL hâl: 887 satırın 885'i tohum, canlı dilim boş
    olabilir. Satırın DÜŞMESİ dedektörün kaybolmasıyla aynı şeydir — okuyucu neyin ölçülmediğini
    bilemez. `ok=True` çünkü ölçülen hiçbir şey TUTMADI değil; bu yolun kapsamında ölçülecek şey
    yok, ve kalıcı kırmızı bir satır operatöre bakmayı bıraktırırdı (alarm_delivery dersi)."""
    _defter_yaz(50, [])

    satir = _satir(recompute.report())

    assert len(bar_casusu) == 0
    assert satir["ok"] is True and satir["b"] == 0
    assert "karşılaştırılabilir işlem YOK" in satir["detail"]
    assert "replay_seed_haric: 50" in satir["detail"]


# ---- 6) SAPMA HÂLÂ YAKALANIYOR: dedektör kapatılmadı ------------------------------------------
def test_canli_dilimde_sapma_hala_kirmizi(sandbox_state, monkeypatch):
    """Hız düzeltmesinin dedektörü işlevsizleştirmediğinin POZİTİF KONTROLÜ: canlı bir satırın
    girişi kendi barının açılışından saparsa satır KIRMIZI olmalı."""
    class _VarOlanYol:
        def exists(self):
            return True

    monkeypatch.setattr(_dt, "_cache_path", lambda tk: _VarOlanYol())
    monkeypatch.setattr(_dt, "load_bars", lambda tk, s, e, **kw: pd.DataFrame(
        {"date": [pd.Timestamp(s)], "open": [78.55], "high": [79.0], "low": [78.0],
         "close": [78.4], "volume": [1000]}))
    _defter_yaz(200, [("AAA", ledgerstamp.LIVE_PAPER)])   # defter entry=100.0, bar open=78.55

    satir = _satir(recompute.report())

    assert satir["ok"] is False, satir["detail"]
    assert "SAPIYOR" in satir["detail"]
    assert "replay_seed_haric: 200" in satir["detail"]


# ---- 7) PANONUN İLK BOYAMASI EN PAHALI UCA ZİNCİRLİ OLMASIN -----------------------------------
#      Arızanın İKİNCİ yarısı buydu ve sunucu tarafı düzeltmesinden BAĞIMSIZ: `parity` bugün ucuz
#      olsa bile, varsayılan rotanın ilk boyamasını teşhis ucuna `await` ile bağlamak, o ucun
#      yarın pahalılaşmasını panonun AÇILMAMASI olarak yaşatır. Sınıf burada çivilenir.
def _render_bugun_govdesi() -> str:
    js = APP_JS.read_text()
    i = js.index("RENDER.bugun = async () => {")
    return js[i:js.index("\n};\n", i)]


def test_bugun_sayfasi_teshis_ucunu_BEKLEMEZ():
    """`RENDER.bugun` VARSAYILAN rotadır. `await`i `/api/today`e bağlıdır; `/api/diagnostics`
    ARKADAN gelir. (2026-08-13 arızasında ikisi `Promise.all` ile beklenip pano 20-90 sn boyunca
    "yükleniyor…" iskeletinde kaldı — oysa `/api/today` 0,18 sn ile ayaktaydı.)"""
    govde = _render_bugun_govdesi()
    assert 'await j("/api/today")' in govde, "beklenen tek uç değişmiş"
    for kalip in ('Promise.all([\n    j("/api/today"), j("/api/diagnostics")',
                  'await j("/api/diagnostics")',
                  'await Promise.all([j("/api/today"), j("/api/diagnostics")'):
        assert kalip not in govde, f"ilk boyama yine teşhis ucuna zincirlenmiş: {kalip}"


def test_teshis_karti_KAYBOLMAZ_yalnizca_arkadan_gelir():
    """Hızlanma, veriyi ekrandan silerek elde edilmez. Uç HÂLÂ çekilir ve beslediği üç yüzey
    (sessiz hat şeridi · alarm bütçesi satırı · ret sayısı) yerinde doldurulur."""
    govde = _render_bugun_govdesi()
    assert 'j("/api/diagnostics").then(' in govde, "teşhis ucu tamamen düşmüş — kart kaybolur"
    assert "sessizHatGlobal(" in govde
    assert "gbAlarmSatiri(" in govde and 'id="gb-ret"' in govde
    # BEKLERKEN UYDURMA YOK: yuva "0 ret"/"aşım yok" ile doğmaz.
    assert "gbAlarmSatiri(null, true)" in govde, "bekleyen alarm satırı üçüncü durumu taşımıyor"
