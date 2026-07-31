"""test_pipeline_deadlock_v63.py — UYGULAMAYI KİLİTLEYEN HATA (2026-07-22).

Operatör: "gene çok fazla hata buldun ama uygulama hâlâ çalışmıyor." Haklıydı: bulduğum her şey
altyapıydı, motorun ilerlememesinin sebebi değil. Sebep şuydu —

  1. Zamanlayıcı, "bu seansın barı geldi mi?" sorusunu YALNIZ ENDEKSE (SPY) soruyordu.
  2. SPY, EOD'yi erken yayınlayan azınlıktandır: 2026-07-21 barı 250 sembolün 46'sında vardı.
  3. Bayrak İLK denemede tükeniyor → kalan 204 sembol bir daha hiç çekilmiyor.
  4. Motorun kapsama kapısı (≥%90) "%18" deyip BİR ÖNCEKİ seansa düşüyor.
  5. O seans zaten işlenmiş → döngü `noop`. Ertesi tur aynı. Uygulama HİÇ ilerlemiyor.

Hiçbir istisna fırlamadı, hiçbir test kırılmadı, panoda hata görünmedi: yalnız "bugün aday yok".
Bu, motorda düzelttiğimiz evren-kapsaması hatasının veri hattındaki İKİZİDİR — aynı yasa iki yerde
yazılmış, biri güncellenmiş, diğeri unutulmuştu. Bu dosya ikisinin de aynı ölçütü kullandığını
kilitler.
"""
from __future__ import annotations

import pandas as pd
import pytest

from meridian import loop, scheduler


def _bars(n_total: int, n_with_session: int, session: str, prev: str = "2026-07-20") -> dict:
    """n_total sembolün n_with_session tanesinde `session` barı VAR, kalanında yok."""
    out = {}
    for i in range(n_total):
        dates = ["2026-07-17", prev] + ([session] if i < n_with_session else [])
        out[f"T{i}"] = pd.DataFrame({"date": pd.to_datetime(dates), "close": [10.0] * len(dates)})
    return out


# ---------- kilidin kendisi ----------
def test_index_alone_must_not_satisfy_the_refetch_flag():
    """CANLI KİLİT: SPY barı geldi diye tazeleme durursa, evrenin %82'si eksik kalır ve motor
    bir daha ilerleyemez. Kapsama eşiğin ALTINDAYKEN bayrak tükenmemeli."""
    bars = _bars(250, 46, "2026-07-21")            # canlıda ölçülen tam oran: 46/250
    cov = scheduler._session_coverage(bars, "2026-07-21")
    assert cov == pytest.approx(46 / 250)
    assert cov < loop.UNIVERSE_MIN_COVERAGE, "bu kapsamayla motor karar VEREMEZ — tazeleme sürmeli"


def test_full_coverage_satisfies_it():
    bars = _bars(250, 240, "2026-07-21")
    assert scheduler._session_coverage(bars, "2026-07-21") >= loop.UNIVERSE_MIN_COVERAGE


def test_coverage_is_measured_on_the_universe_not_the_index():
    """Ölçüm nesnesi ENDEKS değil EVREN olmalı: endeks tek seri, motor 250 seri üzerinde karar verir."""
    import inspect
    src = inspect.getsource(scheduler.advance_once)
    assert "_session_coverage(bars" in src, "kapsama evrenden ölçülmüyor"
    # endeksin son barı TEK BAŞINA bayrağı tüketen koşul olamaz: gelme kararı KAPSAMADAN doğar
    # (2026-07-30 merdiveni: eski tek satırlık `if _arrived or attempts >= 8:` ikiye ayrıldı —
    # "bar geldi mi" ile "sık faz bütçesi doldu mu" artık AYRI kararlar; ölçüt aynı kaldı)
    assert "_arrived = _cov >= _need" in src
    assert "if attempts >= DENSE_ATTEMPTS:" in src
    assert 'if (got is not None and got >= last_closed)' not in src


def test_both_gates_share_one_threshold():
    """AYNI YASA İKİ YERDE yazılmasın: veri hattının beklediği kapsama ile motorun istediği kapsama
    aynı sabitten gelmeli. Ayrışırlarsa biri diğerini sonsuza kadar bekler — kilit tam buydu."""
    import inspect
    src = inspect.getsource(scheduler.advance_once)
    assert "loop.UNIVERSE_MIN_COVERAGE" in src, "zamanlayıcı kendi eşiğini TANIMLAMAMALI"
    assert isinstance(loop.UNIVERSE_MIN_COVERAGE, float) and 0.5 < loop.UNIVERSE_MIN_COVERAGE <= 1.0


def test_giving_up_after_the_retry_cap_is_loud():
    """SIK FAZ BÜTÇESİ DOLDUĞUNDA PES EDİLMEZ — AMA HİÇBİR ADIM SESSİZ DEĞİLDİR (2026-07-30).

    Eski yasa: 8. denemede pes + alarm. Ürettiği alarm sahteydi (zincirin en taze kolu T+1
    yayınlıyor; 40 dakikada gelmesi yapısal olarak imkânsızdı) ve sahte alarm gerçek alarmı okunmaz
    yapar. Yeni yasa üç adımlıdır ve ÜÇÜ DE kayıt bırakır:
      1. sık faz dolar  → bayrak yanar (poll'ler cache-only)   ve `session_bar_retry_sparse` yazılır
      2. seyrek faz     → 30-60 dk aralıklarla kovalama sürer
      3. SON TARİH      → bir sonraki seansın kapanışında terminal ilan + alarm
    'Sessiz pes yok' iddiası artık 1. ve 3. adımın birlikte kanıtıdır."""
    import inspect
    src = inspect.getsource(scheduler.advance_once)
    # 1. adım: bütçe dolunca kovalama SÜRER (chase kapanmaz) ve durum kayda geçer
    assert "if attempts >= DENSE_ATTEMPTS:" in src
    assert "session_bar_retry_sparse" in src, "sık fazın kapanışı sessiz"
    # 2. adım: seyrek faz gerçekten planlanır
    assert "_schedule_sparse()" in src and "_sparse_due()" in src
    # 3. adım: terminal ilan YALNIZ son tarihte ve tek yerde — ve o yer LOUD
    assert "_declare_terminal_skip(_chase)" in src
    term = inspect.getsource(scheduler._declare_terminal_skip)
    # rindex: adın İLK geçtiği yer docstring'dir (imzanın neden korunduğunu anlatır); ölçülmek
    # istenen, olayı GERÇEKTEN yayan çağrıdır — ilk geçişe bakan pencere gövdeyi hiç görmezdi.
    i = term.rindex("session_bar_never_published")
    assert "universe_coverage" in term[i:] and "ATLAYACAK" in term[i:]
    assert "obs.ALARM_DATA_QUALITY" in term, "alarm seviyesi düştü — notify zinciri devreye girmez"


def test_coverage_helper_is_conservative_on_broken_series():
    """Bozuk seri kapsamayı DÜŞÜRMELİ (muhafazakâr taraf): yukarı yuvarlamak, eksik veriyle karar
    verilmesine yol açardı."""
    bars = _bars(10, 10, "2026-07-21")
    bars["BOZUK"] = pd.DataFrame({"date": ["bozuk"], "close": [1.0]})
    cov = scheduler._session_coverage(bars, "2026-07-21")
    assert cov < 1.0


def test_no_session_no_claim():
    assert scheduler._session_coverage({}, "2026-07-21") == 0.0
    assert scheduler._session_coverage(_bars(5, 5, "2026-07-21"), None) == 0.0
