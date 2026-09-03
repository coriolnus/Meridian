"""test_dsr_damgasi_v392.py — TSK-077 DSR DAMGASI (KYS-2026-002 R2 planı, 2026-09-03).

R1 tabanının DSR yarısı kill#2 ile durmuştu (research/cards/KYS-2026-002-pbo-dsr-r1-taban.yaml):
donmuş kopya kapının `_ret` girdi serisini (pnl_dollars/START_EQUITY, `reflect._gate_eval`)
TAŞIMIYORDU — defterdeki `seri` (kapanış-günü, r_multiple) ölçek-eşdeğer DEĞİL (motorun kendi
_moments'ıyla ÖLÇÜLDÜ ve REDDEDİLDİ, medyan Sharpe sapması 0,0131). Tek yol İLERİYE DÖNÜK DAMGA:
`validation.record_candidate` satırına `ret_seri` (kapının `deflated_sharpe`'a verdiği liste,
YUVARLAMASIZ) + `ret_n` eklenir.

DÖRT ÇİVİ, DÖRT AYRI SESSİZ KAYMA YOLU:
  ① EŞİTLİK    — yazılan `ret_seri`, kapının `deflated_sharpe`'a verdiği listeyle BİREBİR aynı
                 (monkeypatch ile yakalanır); `ret_n` == len. Yeniden hesap YOK — `_gate_eval`in
                 koşulsuz kurduğu `_ret`in KENDİSİ (satır ~681).
  ② UYDURMA    — `_trades_search` anahtarı YOKSA `ret_seri`/`ret_n` None + beyan cümlesi; anahtar
    YASAĞI       VARSA ve boşsa []/0 (o da bir ÖLÇÜMDÜR — None ile karıştırılamaz).
  ③ RETRO-DAMGA — alan yokken yazılmış eski satır `ledger()`/`pbo_cscv` tarafından okunmaya devam
    YASAK/UYUM    eder; `ledgers.py` sözleşmesinin `required` listesi DEĞİŞMEDİ.
  ④ FAIL-OPEN  — damga yazımı patlasa bile (`store.append_jsonl` raise) `_gate_eval`in
                 `passes`/`why` hükmü DEĞİŞMEZ: `validation.record_candidate` YASA 4 gereği zaten
                 yutuyor ve uyarıyor; bu turun eklediği kod bu zarfın DIŞINA taşmaz.
"""
from __future__ import annotations

from meridian import ledgers, reflect, store, validation
from tests import wf_fixtures as wf


def _iyi_cift():
    """Kapıyı rahatça GEÇEN incumbent/aday çifti (`test_dsr_hard_gate_v130._pass_gate` ile aynı
    fikstür değerleri) — `_trades_search` DOLU ve deterministik (sabit tohum)."""
    inc = wf.wf_from_scores(0.10, folds=[(30, 0.2)] * 3, holdout=0.10)
    cand = wf.wf_from_scores(0.30, folds=[(30, 0.6)] * 3, holdout=0.30)
    return inc, cand


def _dilimsiz_cift(cts=None) -> tuple[dict, dict]:
    """Dilimsiz (legacy) fikstür — `test_28f_DILIMSIZ_fikstur_dunyasinda_davranis_DEGISMEDI`
    deseniyle aynı: `_trades_search` YOK (varsayılan) ya da elle verilen bir liste taşır."""
    inc = {"oos_score": 0.10, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None,
           "params": {}}
    cand = {"oos_score": 0.30, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None,
            "params": {}}
    if cts is not None:
        cand["_trades_search"] = cts
    return inc, cand


# ==============================================================================================
# ① EŞİTLİK — ret_seri kapının deflated_sharpe'a verdiği listeyle BİREBİR aynı
# ==============================================================================================
def test_ret_seri_kapinin_dsr_girdisiyle_birebir_esit(sandbox_state, monkeypatch):
    inc, cand = _iyi_cift()
    assert cand.get("_trades_search"), "kurgu geçersiz: aday _trades_search taşımıyor"

    yakalanan: dict = {}
    orig = validation.deflated_sharpe

    def _spy(returns, n_trials, trial_sharpes=None):
        yakalanan["returns"] = list(returns)
        return orig(returns, n_trials, trial_sharpes)

    monkeypatch.setattr(validation, "deflated_sharpe", _spy)
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)

    assert "returns" in yakalanan, "kurgu geçersiz: deflated_sharpe hiç çağrılmadı"
    row = validation.ledger()[-1]
    assert row["ret_seri"] == yakalanan["returns"], (
        "ret_seri kapının deflated_sharpe'a verdiği listeyle BİREBİR eşit olmalı (yuvarlama YOK) — "
        f"yazılan: {row['ret_seri']} kapının gördüğü: {yakalanan['returns']}")
    assert row["ret_n"] == len(yakalanan["returns"]) > 0


# ==============================================================================================
# ② UYDURMA YASAĞI — _trades_search yok → None + beyan; boş liste → []/0
# ==============================================================================================
def test_trades_search_yok_ret_seri_None_ve_beyanli(sandbox_state):
    inc, cand = _dilimsiz_cift(cts=None)
    assert "_trades_search" not in cand, "kurgu geçersiz: _trades_search VAR"
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    row = validation.ledger()[-1]
    assert row["ret_seri"] is None and row["ret_n"] is None, (
        f"anahtar YOKKEN None dışında bir şey uydurulmuş: {row['ret_seri']!r}/{row['ret_n']!r}")
    assert "_trades_search yok" in row["beyan"], row["beyan"]


def test_trades_search_bos_liste_ret_seri_bos_liste_ve_sifir(sandbox_state):
    inc, cand = _dilimsiz_cift(cts=[])
    assert cand["_trades_search"] == [], "kurgu geçersiz"
    reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)
    row = validation.ledger()[-1]
    assert row["ret_seri"] == [] and row["ret_n"] == 0, \
        "boş liste de bir ÖLÇÜMDÜR — None ile karıştırılamaz"
    assert "_trades_search yok" not in row["beyan"], \
        "anahtar VARDI (boş liste) — 'yok' cümlesi yalnız anahtar EKSİKKEN basılmalı"


# ==============================================================================================
# ③ RETRO-DAMGA YASAK / GERİYE UYUMLULUK
# ==============================================================================================
def test_eski_satir_ret_seri_olmadan_gecerli_ve_okunur(sandbox_state):
    eski = {"ts": "2026-01-01T00:00:00Z", "fingerprint": "eski-fp", "etiket": "eski_satir",
            "seri": [["2026-01-02", 0.5]], "sharpe_gozlem": 0.1, "n_trials": 5, "passes": False}
    store.append_jsonl(validation.LEDGER_FILE, eski)

    assert ledgers.validate_row(validation.LEDGER_FILE, eski) == [], (
        "ret_seri/ret_n required'a eklenmiş olamaz — retro damga yasağı, eski satır İHLAL "
        "sayılmamalı")
    c = ledgers.CONTRACTS[validation.LEDGER_FILE]
    assert "ret_seri" not in c.required and "ret_n" not in c.required
    assert "ret_seri" in c.note, "yeni alan sözleşme notunda beyan edilmemiş (YASA 6)"

    rows = validation.ledger()
    assert any(r.get("etiket") == "eski_satir" for r in rows), \
        "ret_seri alanı YOKKEN satır ledger()'dan sessizce düşüyor"
    validation.pbo_cscv(rows=rows)          # yalnız `seri` okur — ret_seri'siz satırda patlamamalı


# ==============================================================================================
# ④ FAIL-OPEN — damga yazımı patlarsa `_gate_eval` hükmü AYNI kalır
# ==============================================================================================
def test_damga_yazimi_patlasa_bile_gate_hukmu_degismez(sandbox_state, monkeypatch):
    inc, cand = _iyi_cift()

    def _patlat(name, row):
        raise OSError("disk dolu (test fikstürü)")

    monkeypatch.setattr(store, "append_jsonl", _patlat)
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1, record_erosion=True)

    assert passes is True and why == "", (
        f"damga yazımı patladı ve kapı hükmü etkilendi (fail-open ihlali): passes={passes} "
        f"why={why!r}")
    assert gate["dsr_rol"], "kapı kaydı yine de tam üretilmeli — yalnız DEFTER yazımı düşer"
