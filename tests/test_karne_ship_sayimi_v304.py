"""KARNE SHIP'İ SAYAMIYORDU — "hiçbir öneri OOS kapısını geçemedi" YANLIŞTI · v304

OPERATÖR SORUSU (2026-08-25): "neden hiçbir öneri OOS kapısını geçemiyor?"
CEVAP: GEÇTİ. İki kez. Ve iki düğme de BUGÜN CANLIDA.

ÖLÇÜLDÜ (canlı defter, 2026-08-25):
    60 hipotez · rejected_by_backtest 32 · rejected_by_guard 25 · rejected_by_confirmation 1
    · superseded 2
    H00026  entry.pivot_proximity_pct  v1→v2  reject_reasons=None  realized_delta −0,0364
    H00029  entry.w_prox               v2→v3  reject_reasons=None
    canlı strategy.yaml: version 5 · parent 3 · pivot_proximity_pct 2,3 · w_prox 0,15

Operatörün okuduğu cümle `analytics.py:730`du:
    "hiçbir öneri OOS kapısını geçemedi — canlı strateji hâlâ v1 (parent yok)"
İKİ İDDİA DA YANLIŞ: iki öneri geçti, ve canlı v5/parent 3.

KÖK NEDEN — SONRADAN EKLENEN HİJYEN, ESKİ SAYACIN VARSAYIMINI GEÇERSİZ KILDI:
`ever_shipped` (analytics.py:708) = live + promoted + rolled_back. `superseded` YOK.
Ama `rollback.sweep_orphan_hypotheses` (rollback.py:367-375) YALNIZ `status == "live"` olanları
`superseded`e taşır — ve bir hipotez ancak SHIP ETTİYSE `live` olur. Yani süpürme, öğrenmenin
kanıtını karneden SESSİZCE SİLİYORDU. Arıza biçimi ("sistem hiç öğrenmedi") makul bir cümle
olduğu için kimse fark etmedi.
AYNI DOSYA ZATEN DOĞRUSUNU BİLİYORDU: `analytics.py:1115` (`deflate_why`) superseded'i ship
sayıyor ve docstring'i (satır 1109) "defterde ship VARDI (2 superseded)" diyor. Tek dosya,
iki farklı ship tanımı; operatöre yanlış olan servis ediliyordu.
"""
from __future__ import annotations

import inspect

from meridian import analytics, memory, rollback, store


def _defter(monkeypatch, hyps: list[dict]):
    monkeypatch.setattr(memory, "all_hypotheses", lambda: hyps)
    monkeypatch.setattr(analytics.memory, "all_hypotheses", lambda: hyps, raising=False)


def test_superseded_SHIP_sayilir(sandbox_state, monkeypatch):
    """ASIL ÇİVİ: ship etmiş ama sonradan aşılmış hipotez 'hiç ship olmadı' saydırmaz."""
    _defter(monkeypatch, [
        {"id": "H1", "status": "superseded", "version_from": 1, "version_to": 2},
        {"id": "H2", "status": "rejected_by_backtest"},
    ])
    r = analytics.learning_scorecard()
    assert r.get("loop_state") != "no_ship_v1_stands", (
        f"superseded ship sayılmıyor — süpürme öğrenmenin kanıtını siliyor: {r.get('loop_state')}")
    assert "hiçbir öneri OOS kapısını geçemedi" not in str(r.get("verdict", "")), (
        f"karne hâlâ 'hiçbir öneri geçemedi' diyor: {r.get('verdict')}")


def test_hic_ship_yokken_cumle_KORUNUR(sandbox_state, monkeypatch):
    """Aşırıya kaçma çivisi: gerçekten hiç ship yoksa dürüst cümle AYNEN kalmalı."""
    _defter(monkeypatch, [
        {"id": "H1", "status": "rejected_by_backtest"},
        {"id": "H2", "status": "rejected_by_guard"},
    ])
    r = analytics.learning_scorecard()
    assert r.get("loop_state") == "no_ship_v1_stands", (
        f"hiç ship yokken cümle kaybolmuş — kapsam taşmış: {r.get('loop_state')}")


def test_cumle_CANLI_SURUMU_uydurmaz(sandbox_state, monkeypatch):
    """'canlı strateji hâlâ v1 (parent yok)' bir f-string SABİTİYDİ ve v5 taşıyan yükte de
    aynen basılıyordu. Sürüm iddiası ölçülmeli ya da hiç edilmemeli (UYDURMA YASAĞI)."""
    store.write_json("strategy.json", {})          # canlı sürüm sandbox'ta yok → uydurma yasak
    _defter(monkeypatch, [{"id": "H1", "status": "rejected_by_backtest"}])
    r = analytics.learning_scorecard()
    v = str(r.get("verdict", ""))
    assert "hâlâ v1" not in v, (
        f"karne canlı sürümü ÖLÇMEDEN 'v1' diye yazıyor — sabit literal duruyor: {v}")


def test_TEK_ship_tanimi(sandbox_state):
    """Aynı dosya ship'i İKİ farklı sayamaz. `deflate_why` ve `learning_scorecard` AYNI
    kümeyi kullanmalı — yoksa aynı defter iki cevap verir ve hangisinin servis edildiği
    tesadüfe kalır (tam da bu vakada olan)."""
    assert hasattr(analytics, "SHIP_DURUMLARI"), (
        "ship kümesi tek kaynakta değil — iki fonksiyon kendi listesini taşıyorsa ayrışır")
    for fn in (analytics.learning_scorecard, analytics.deflate_why):
        src = inspect.getsource(fn)
        assert "SHIP_DURUMLARI" in src, (
            f"{fn.__name__} kendi ship listesini taşıyor — tek kaynak kuralı bozuk")


def test_supurmenin_HEDEF_durumu_ship_kumesinde():
    """ANTI-SÜRÜKLENME. `sweep_orphan_hypotheses` `live` olanı hangi duruma taşıyorsa, o durum
    ship kümesinde OLMALI. Süpürmenin hedefi bir gün değişirse bu çivi öter — kusurun
    kendisi tam olarak buydu: hijyen eklendi, sayaç güncellenmedi."""
    src = inspect.getsource(rollback.sweep_orphan_hypotheses)
    assert 'h.get("status") != "live"' in src, (
        "süpürme artık `live` dışını da taşıyor olabilir — çivinin öncülü geçersiz, gözden geçir")
    import re
    m = re.search(r'update_status\(h\["id"\],\s*"([a-z_]+)"', src)
    assert m, f"süpürmenin hedef durumu kaynaktan okunamadı: {src[:200]}"
    assert m.group(1) in analytics.SHIP_DURUMLARI, (
        f"süpürme `live` hipotezi '{m.group(1)}' durumuna taşıyor ama o durum ship kümesinde YOK "
        f"({sorted(analytics.SHIP_DURUMLARI)}) — öğrenmenin kanıtı yine sessizce silinir")
