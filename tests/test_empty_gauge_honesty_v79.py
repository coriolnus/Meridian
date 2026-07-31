"""test_empty_gauge_honesty_v79.py — BOŞ GÖSTERGE DÜRÜSTLÜĞÜ (2026-07-22).

Operatör panoda iki ölü gösterge gördü ve sordu: "neden hiç veri yok". İkisinin de altındaki
açıklama YANLIŞTI — ve ikisi de aynı kusur sınıfından:

  BOŞ BİR DEĞERİN GEREKÇESİ, O DEĞERİN KENDİSİNDEN UYDURULMUŞTU.

  1. Deflasyon halkası: "henüz ship yok — ilk ship'te dolar". Bu iddia `deflate_stats() is None`
     üzerinden türetilmişti, ship SAYISINDAN değil. Defterde 2 ship vardı. Vaat de yanlıştı:
     `predicted_delta_search` yalnız teyit yürüyüşünü geçen ship yolunda yazılır.
  2. Isınma termometresi: "henüz sprint koşmadı" SIRADA demekti. Oysa sprint bir elif zincirinin
     SON dalı; arka plan yansıması sırayı her poll'da tutuyorsa sayaç ASLA ilerlemez. "Koşmadı"
     ile "koşamaz" aynı görünüyordu.

Kurt masalı yasağının ikizi: yanlış alarm operatöre kırmızıyı yok saymayı öğretir; YANLIŞ VAAT
ise ölü bir ölçümü sağlıklı gösterir. İkisi de teşhisi öldürür.
"""
from __future__ import annotations

import re
from pathlib import Path

from meridian import analytics, memory, store

SRC = Path(__file__).resolve().parent.parent
RUNTIME = SRC / "meridian" / "hermes_runtime.py"
APPJS = SRC / "meridian" / "web" / "app.js"


def _hyp(hid: str, status: str, **extra) -> None:
    store.append_jsonl(memory.HYP, {"id": hid, "ts": memory.now_iso(),
                                    "variable": "entry.min_score", "status": status, **extra})


# ---------------- 1) DEFLASYON: gerekçe ÖLÇÜLÜR ----------------
def test_empty_deflate_reports_the_measured_stage_not_a_guess(sandbox_state):
    """CANLI DURUM: 34 hipotez, 22 kapıda + 9 backtest'te + 1 teyitte elendi, 2 superseded.
    'Henüz ship yok' demek düpedüz yanlıştı."""
    for i in range(22):
        _hyp(f"H{i:05d}", "rejected_by_guard")
    _hyp("H00098", "superseded", predicted_delta=-0.03)
    _hyp("H00099", "rejected_by_confirmation")

    assert analytics.deflate_stats() is None                 # halka gerçekten boş
    w = analytics.deflate_why()
    assert w["n_hypotheses"] == 24
    assert w["shipped"] == 1, "superseded BİR ship'tir — 'ship yok' iddiası buradan çürüyor"
    assert w["measured"] == 0
    assert w["legacy_ships"] == 1, "ship var ama alan yok → 'bir SONRAKİ ship'te dolar'"
    assert w["by_status"]["rejected_by_guard"] == 22         # huni NEREDE ölüyor: söylenebilir olmalı


def test_a_ledger_with_no_hypotheses_is_distinguished_from_one_that_never_ships(sandbox_state):
    """AYRIM: 'defter boş' (sabır) ile 'hiçbiri ship'e ulaşmıyor' (arıza sinyali) aynı metni almamalı."""
    bos = analytics.deflate_why()
    assert bos["n_hypotheses"] == 0 and bos["shipped"] == 0

    for i in range(5):
        _hyp(f"H{i:05d}", "rejected_by_backtest")
    dolu = analytics.deflate_why()
    assert dolu["n_hypotheses"] == 5 and dolu["shipped"] == 0 and dolu["legacy_ships"] == 0
    assert bos != dolu, "iki farklı durum panoda aynı gerekçeye düşer"


def test_a_measured_ship_fills_the_gauge_and_empties_the_excuse(sandbox_state):
    """POZİTİF KONTROL: alan yazıldığı anda halka dolmalı — 'why' bir bahane fabrikası olmamalı."""
    _hyp("H00001", "live", predicted_delta_search=0.40, predicted_delta=0.10)
    d = analytics.deflate_stats()
    assert d is not None and d["n"] == 1 and d["avg_deflation_pct"] == 75.0
    assert analytics.deflate_why()["measured"] == 1


# ---------------- 2) ISINMA: 'koşmadı' ile 'koşamaz' ayrı ----------------
def test_every_skip_token_python_emits_is_named_by_the_dashboard():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ — baskın kusur sınıfı. hermes_runtime bir token yazar, app.js onu
    metne çevirir. Biri yeni token eklerse diğeri sessizce ham token gösterir (ya da hiç göstermez):
    ölü gösterge yeniden ölü gerekçeye döner. İki taraf da BURADA eşleşmeye zorlanır."""
    uretilen = set(re.findall(r'_state\["_warm_skip"\]\s*=\s*"([a-z_]+)"', RUNTIME.read_text()))
    assert uretilen, "üretici token yazmıyor — ayıklama okuması bozuldu"

    js = APPJS.read_text()
    blok = js[js.index("const S = { bg_reflect:"):]
    blok = blok[:blok.index("};")]
    bilinen = set(re.findall(r'([a-z_]+)\s*:\s*"', blok))

    assert uretilen <= bilinen, f"pano bu tokenleri tanımıyor: {sorted(uretilen - bilinen)}"
    assert bilinen <= uretilen, f"pano olmayan token için metin taşıyor: {sorted(bilinen - uretilen)}"


def test_the_sprint_branch_is_last_so_a_skip_reason_is_mandatory():
    """YAPISAL KANIT: ısınma sprinti elif zincirinin SON dalı — yani önceki dallar onu SÜREKLİ
    aç bırakabilir. Bu yüzden zincirin HER dalı bir neden yazmak zorunda; yazmayan bir dal
    '0/12 · henüz koşmadı'yı yeniden sessiz yalana çevirir."""
    src = RUNTIME.read_text()
    govde = src[src.index("def _run("):]
    govde = govde[:govde.index("def start(")]
    dallar = re.findall(r"\n {16}(if |elif |else)", govde)
    assert len(dallar) >= 5, f"zincir beklenenden kısa: {dallar}"
    # zincirdeki her dal ya sprinti KOŞAR ya da neden yazar
    assert govde.count('_state["_warm_skip"]') >= len(dallar), \
        "bir dal ısınmayı atlarken neden bırakmıyor — sessiz atlama"
    assert '_state["_warm_ticks"]' in govde, "sprint sayacı zincirden düşmüş"
