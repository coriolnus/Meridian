"""Defter broker-teyit boyutu — çiviler (ROADMAP Ö-52, kart EXE-2026-007 karar kuralı).

KARAR KURALI (kartta DONUK, ölçümden önce yazıldı): Ö1 > 0 ⇒ damga sözleşmesi YETERSİZ,
`ledgerstamp`e broker-teyit boyutu EKLENİR. Ön-ölçüm Ö1 = 2/8 = %25 (ALL T00096 · VLO T00097
broker'da hiç var olmamış — 62 emirde 0, 55 aktivitede 0 fill, 61.511 olayda 0 alpaca_submit).

TASARIM: `kaynak` damgası bir KOD YOLU beyanıdır ve öyle KALIR — teyit boyutu onu düzeltmez,
ONA DİK ikinci bir eksendir. Üç görev deseni ledgerstamp'inkiyle aynı: ileri yol (asla ezme) ·
sayaç yüzeyi · dürüst üçüncü hâl. Damgalayıcı reconcile'da koşar (broker emirleri orada) ve
kendi kendini iyileştirir: damgasız her live_paper satırı her turda yeniden denenir.
"""
import ast
import pathlib

import pytest

from meridian import ledgerstamp as LS

LOOP = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "loop.py"
API = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "api.py"
APP = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js"


# ── sözlük + teyit_of ────────────────────────────────────────────────────────

def test_sozluk_dort_deger():
    """teyitli · karsiliksiz · olculemedi · kapsam_disi — DÖRDÜ AYRI. `kapsam_disi` tohum
    satırlarıdır: kartın kill kriteri 'tohum satırları kıyasa girerse geçersiz' der; onları
    `olculemedi`ye atmak, kill kriterini sayaçta eritmek olurdu."""
    assert LS.TEYITLI == "teyitli" and LS.KARSILIKSIZ == "karsiliksiz"
    assert LS.TEYIT_OLCULEMEDI == "olculemedi" and LS.TEYIT_KAPSAM_DISI == "kapsam_disi"
    assert LS.TEYIT_FIELD == "broker_teyit"


def test_teyit_of_tohum_satiri_KAPSAM_DISI():
    assert LS.teyit_of({"kaynak": LS.REPLAY_SEED}) == LS.TEYIT_KAPSAM_DISI
    assert LS.teyit_of({"kaynak": LS.BELIRSIZ}) == LS.TEYIT_KAPSAM_DISI, \
        "kaynağı belirsiz satır canlı KANIT sayılamaz — teyit kapsamına girmez"


def test_teyit_of_damgasiz_canli_satir_OLCULEMEDI():
    """Alan yokluğu 'teyitli' DEĞİL 'henüz ölçülmedi'dir (mirror_divergence'in None kusuru
    burada TEKRARLANMAZ)."""
    assert LS.teyit_of({"kaynak": LS.LIVE_PAPER}) == LS.TEYIT_OLCULEMEDI


def test_teyit_of_damgali_satir_degerini_okur():
    r = {"kaynak": LS.LIVE_PAPER, LS.TEYIT_FIELD: LS.KARSILIKSIZ}
    assert LS.teyit_of(r) == LS.KARSILIKSIZ


def test_teyit_stamp_asla_ezmez():
    """`stamp` ile aynı yasa: var olan damga ASLA ezilmez — sonraki tur 'teyitli' bulsa bile
    ilk hüküm kanıttır, sessizce değişmez."""
    r = {"kaynak": LS.LIVE_PAPER, LS.TEYIT_FIELD: LS.KARSILIKSIZ}
    LS.teyit_stamp(r, LS.TEYITLI)
    assert r[LS.TEYIT_FIELD] == LS.KARSILIKSIZ


def test_teyit_stamp_olculemedi_neden_ister():
    with pytest.raises(ValueError):
        LS.teyit_stamp({"kaynak": LS.LIVE_PAPER}, LS.TEYIT_OLCULEMEDI)   # nedensiz olmaz
    r = {"kaynak": LS.LIVE_PAPER}
    LS.teyit_stamp(r, LS.TEYIT_OLCULEMEDI, neden="emir penceresi dolu — defter kırpılmış olabilir")
    assert r[LS.TEYIT_FIELD] == LS.TEYIT_OLCULEMEDI
    assert len(r["broker_teyit_neden"]) >= 20, "YASA 4: gerekçe ≥20 karakter"


def test_teyit_counts_dort_kovayi_sayar():
    rows = [
        {"kaynak": LS.LIVE_PAPER, LS.TEYIT_FIELD: LS.TEYITLI},
        {"kaynak": LS.LIVE_PAPER, LS.TEYIT_FIELD: LS.KARSILIKSIZ},
        {"kaynak": LS.LIVE_PAPER},                       # damgasız → olculemedi
        {"kaynak": LS.REPLAY_SEED},                      # tohum → kapsam_disi
    ]
    c = LS.teyit_counts(rows)
    assert c[LS.TEYITLI] == 1 and c[LS.KARSILIKSIZ] == 1
    assert c[LS.TEYIT_OLCULEMEDI] == 1 and c[LS.TEYIT_KAPSAM_DISI] == 1


# ── damgalayıcı (reconcile kablosu) ──────────────────────────────────────────

def _fn(ad):
    agac = ast.parse(LOOP.read_text(encoding="utf-8"))
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name == ad:
            return d
    return None


def test_damgalayici_var_ve_reconcile_cagiriyor():
    f = _fn("_defter_teyit_yamasi")
    assert f is not None, "_defter_teyit_yamasi YOK — teyit boyutu deftere hiç inmez"
    src = LOOP.read_text(encoding="utf-8")
    rec = src[src.index("def reconcile_broker_state"):]
    assert "_defter_teyit_yamasi(" in rec, "reconcile damgalayıcıyı ÇAĞIRMIYOR — ölü kod"


def test_damgalayici_kirpik_defterde_karsiliksiz_DEMEZ():
    """EN KRİTİK ÇİVİ. Emir sorgusunun tavanı var; defter kırpıldıysa 'emri görmedim'
    'emir yok' demek DEĞİLDİR. Kırpık defterde karşılıksız damgası UYDURMADIR —
    `olculemedi` + neden düşülmeli. (`koruma_report.emir_tavani_dolu` ile aynı sınıf.)"""
    govde = ast.unparse(_fn("_defter_teyit_yamasi"))
    assert "KARSILIKSIZ" in govde and "OLCULEMEDI" in govde
    assert ("tavan" in govde or "kirp" in govde or "len(" in govde), \
        "damgalayıcı defter kırpılmasını hiç sormuyor — kırpık defterde karşılıksız uydurur"


def test_damgalayici_yalniz_live_paper_damgalar():
    """Kaynak ayrımı ya AÇIKÇA (LIVE_PAPER/kaynak_of) ya da `teyit_of` DEVRİYLE yapılmalı —
    `teyit_of` tohum satırına KAPSAM_DISI döner ve birim çivisi bunu ayrıca bağlar. İlk hâl
    yalnız açık kullanımı kabul ediyordu; devretmek daha iyidir (tek doğru kaynak)."""
    govde = ast.unparse(_fn("_defter_teyit_yamasi"))
    assert ("LIVE_PAPER" in govde or "kaynak_of" in govde or "teyit_of" in govde), \
        "damgalayıcı kaynak ayrımını NE açıkça yapıyor NE teyit_of'a devrediyor — tohum satırına damga basar"


# ── YASA 6: okuyucular ───────────────────────────────────────────────────────

def test_api_teyit_sayaclarini_uretir():
    assert 'd["defter_teyit"]' in API.read_text(encoding="utf-8"), \
        "teyit sayaçları /api/today'de yok — panoya inemez"


def test_pano_teyit_satirini_cizer():
    app = APP.read_text(encoding="utf-8")
    i = app.index("function mutabakatSatirlari")
    govde = app[i:app.index("\nfunction ", i + 10)]
    assert "defter_teyit" in govde, "pano teyit sayaçlarını OKUMUYOR — YASA 6 borcu"
    assert "karsiliksiz" in govde, "pano karşılıksız kovasını ayırt etmiyor"
