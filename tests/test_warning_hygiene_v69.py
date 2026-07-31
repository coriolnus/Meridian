"""test_warning_hygiene_v69.py — UYARI HİJYENİ (2026-07-22).

Operatör: "testlerde de hata görüyorum." Suite `970 passed` diyordu ama koşarken uyarı yağdırıyordu.
Bu, bu kod tabanının baskın hata deseninin bir başka yüzü: **gürültü, gerçek uyarıyı gizler.** Her
koşuda basılan bir RuntimeWarning'e alışan göz, bir gün gerçekten önemli olanı da atlar.

İki gerçek bulgu vardı, ikisi de burada kilitli:
  1. `score_detail` ince örneklemde `std(ddof=1)`'i ÖNCE hesaplıyordu → numpy "Degrees of freedom
     <= 0" uyarısı + NaN. Sonuç tesadüfen doğruydu (NaN > 0 False), hesap boşunaydı.
  2. Ölçülemeyen Sharpe `0.0` olarak yazılıyordu — "ölçtük, sıfır çıktı" ile "veri yetmedi" aynı
     görünüyordu. Kapı eşiği (`min_sharpe`) bu sayıyı okuyor.
"""
from __future__ import annotations

import warnings

import pytest

from meridian import config, score


def _trades(n: int, spread: float = 0.0) -> list[dict]:
    """n işlem; spread=0 → tüm getiriler AYNI (varyans sıfır, Sharpe tanımsız)."""
    return [{"r_multiple": 1.0 + i * spread, "pnl_dollars": 100.0 + i * spread * 100,
             "ts_open": "2026-01-02", "ts_close": f"2026-01-{2 + (i % 25):02d}"} for i in range(n)]


def test_thin_sample_emits_no_numpy_warning():
    """CANLI GÜRÜLTÜ: bootstrap ince dilimlerde skor hesaplıyor ve her replikasyon bir uyarı
    basıyordu. Örneklem yetmiyorsa varyans HİÇ hesaplanmamalı."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        for n in (0, 1, 2, 3):
            score.score_detail(_trades(n), config.goal())     # uyarı → hata olur


def test_zero_variance_emits_no_warning_and_is_not_measurable():
    """Tüm getiriler aynıysa Sharpe TANIMSIZDIR — sıfır değil."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        d = score.score_detail(_trades(40, spread=0.0), config.goal())
    assert d["sharpe"] == 0.0
    assert d["sharpe_measurable"] is False, "varyans sıfırken 'ölçüldü' denemez"


def test_measurable_sharpe_is_flagged_true():
    """Karşı-kontrol: gerçek dağılım varsa bayrak True olmalı — yoksa test boş bir iddia olurdu."""
    d = score.score_detail(_trades(40, spread=0.08), config.goal())
    assert d["sharpe_measurable"] is True and d["sharpe"] != 0.0


def test_unmeasurable_zero_is_distinguishable_from_a_measured_zero():
    """ASIL DÜRÜSTLÜK İDDİASI: iki farklı '0.0' aynı sayıdır ama AYNI ŞEY DEĞİLDİR. Kapı eşiği
    bu sayıyı okuyor; ayrım kaybolursa 'veri yetmedi' sessizce 'başarısız' diye okunur."""
    thin = score.score_detail(_trades(40, spread=0.0), config.goal())
    rich = score.score_detail(_trades(40, spread=0.08), config.goal())
    assert thin["sharpe"] == 0.0
    assert thin["sharpe_measurable"] != rich["sharpe_measurable"]


def test_thin_sharpe_stays_on_the_conservative_side():
    """Ölçülemeyen Sharpe kapıyı GEVŞETMEMELİ: 0.0, min_sharpe eşiğinin altında kalır."""
    d = score.score_detail(_trades(40, spread=0.0), config.goal())
    assert d["sharpe"] <= float(config.goal()["min_sharpe"])


# ---------- FastAPI lifespan ----------
def test_no_deprecated_startup_event():
    """`@app.on_event("startup")` her test koşusunda DeprecationWarning basıyordu. Davranış aynı
    kaldı (lifespan), gürültü gitti."""
    import pathlib
    # Yorum metnini değil, GERÇEK dekoratör kullanımını ara: satır başında `@app.on_event(`.
    # (İlk hâli kendi açıklama yorumumu yakalıyordu — tarayıcı testi de yanlış pozitif verebilir.)
    lines = pathlib.Path("meridian/api.py").read_text().splitlines()
    kullanim = [i + 1 for i, ln in enumerate(lines) if ln.lstrip().startswith("@app.on_event(")]
    assert not kullanim, f"kullanımdan kalkmış başlangıç kancası geri gelmiş: satır {kullanim}"
    src = "\n".join(lines)
    assert "lifespan=_lifespan" in src and "_autostart()" in src


def test_autostart_still_runs_on_app_start(monkeypatch, sandbox_state):
    # sandbox_state ZORUNLU (2026-07-22): açılış artık yetki duruşunu kaydediyor
    # (`_auth_posture_check` → obs.warn/alarm), yani TestClient'ı çıplak kurmak canlı olay defterine
    # test artefaktı düşürür. Sızıntı bekçisi bunu yakaladı — kendi eklediğim yazımı, kendi testimde.
    """Gürültüyü susturmak DAVRANIŞI değiştirmemeli: lifespan gerçekten _autostart'ı çağırıyor mu?
    (Sessizleştirme uğruna zamanlayıcıyı öldürmek, gürültüden çok daha pahalı bir hata olurdu.)"""
    from fastapi.testclient import TestClient
    from meridian import api
    calls = []
    monkeypatch.setattr(api, "_autostart", lambda: calls.append(1))
    with TestClient(api.app):
        pass
    assert calls == [1], "lifespan açılış kancasını çağırmıyor — zamanlayıcı/Hermes hiç başlamaz"
