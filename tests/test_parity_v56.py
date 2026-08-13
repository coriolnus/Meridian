"""test_parity_v56.py — 7. desen: MAKULLÜK / EŞLEŞME (2026-07-21).

Neden var: motorun evrenin %18'inde karar verdiği bulundu ve HER BİLEŞEN DOĞRUYDU — tazelik
koruması, seans seçimi, tarama; üçünün de testi geçiyordu. Hata BİLEŞİMDEYDİ. İlk altı desen
bileşen bazlıdır ("üretiyor mu / koruyor mu / deterministik mi") ve bu sınıfı yapısal olarak
göremez. Bu dedektör tek soru sorar: **üretilen sayı MAKUL mü?**

Canlıda ilk çalıştırmada iki gerçek sorun işaretledi:
  * kalibrasyonun tamamı simülasyondan besleniyor (gerçek 0 / simüle 241, 90 kapalı işlem varken)
  * ölçülen edge her rejimde negatif — bir SONUÇ, ama hiçbir yerde alarm değildi
"""
from __future__ import annotations

import pytest

from meridian import config, store, watchdog as wd


def _cycles(n, candidates=1, armed=0):
    return [{"event": "daily_cycle", "date": f"2026-06-{(i % 27) + 1:02d}",
             "candidates": candidates, "armed": armed} for i in range(n)]


def _row(rep, name):
    return next((r for r in rep["rows"] if r["check"] == name), None)


# ---------- 1) evren kapsaması ----------
def test_low_universe_coverage_is_flagged(sandbox_state):
    """Bulunan hatanın ta kendisi: kararlar evrenin küçük, YANLI bir kesitinde alınıyorsa
    'aday yok' bir sonuç değil, bir arızadır."""
    for e in _cycles(10):
        store.append_jsonl("events.jsonl", e)
    store.append_jsonl("events.jsonl", {"event": "universe_coverage_low", "date": "2026-07-21",
                                        "coverage": 0.18, "min_required": 0.9})
    r = _row(wd.parity_report(), "universe_coverage")
    assert r and r["ok"] is False and "0.18" in r["detail"] or "%18" in r["detail"]


def test_full_coverage_is_quiet(sandbox_state):
    for e in _cycles(10):
        store.append_jsonl("events.jsonl", e)
    assert _row(wd.parity_report(), "universe_coverage")["ok"] is True


# ---------- 2) tarama verimi ----------
def test_persistent_zero_candidates_is_suspicious(sandbox_state):
    for e in _cycles(12, candidates=0):
        store.append_jsonl("events.jsonl", e)
    r = _row(wd.parity_report(), "scan_yield")
    assert r and r["ok"] is False and "şüpheli" in r["detail"]


def test_some_candidates_means_the_scan_path_works(sandbox_state):
    for e in _cycles(6, candidates=0) + _cycles(6, candidates=2):
        store.append_jsonl("events.jsonl", e)
    assert _row(wd.parity_report(), "scan_yield")["ok"] is True


def test_no_verdict_before_enough_cycles(sandbox_state):
    """Az veriyle yorum yapılmaz: 8 döngü birikmeden tarama verimi hakkında konuşulmaz."""
    for e in _cycles(3, candidates=0):
        store.append_jsonl("events.jsonl", e)
    assert _row(wd.parity_report(), "scan_yield") is None


# ---------- 3) kanıt kaynağı ----------
def test_calibration_fed_only_by_simulation_is_flagged(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "r_multiple": 0.5} for i in range(30)])
    store.write_json("score_calibration.json", {"n": 241, "n_real": 0, "n_cf": 241})
    r = _row(wd.parity_report(), "evidence_source")
    assert r and r["ok"] is False and "GİRMİYOR" in r["detail"]


def test_real_evidence_present_is_ok(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "r_multiple": 0.5} for i in range(30)])
    store.write_json("score_calibration.json", {"n": 250, "n_real": 30, "n_cf": 220})
    assert _row(wd.parity_report(), "evidence_source")["ok"] is True


# ---------- 4) ayna eşleşmesi ----------
def test_armed_plans_without_any_mirror_order_is_flagged(sandbox_state, monkeypatch):
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    for e in _cycles(10, armed=2):
        store.append_jsonl("events.jsonl", e)
    store.write_json("portfolio.json", {"armed": [], "alpaca_submitted": []})
    r = _row(wd.parity_report(), "mirror_parity")
    assert r and r["ok"] is False


def test_mirror_parity_not_asked_in_internal_broker_mode(sandbox_state, monkeypatch):
    monkeypatch.setattr(config, "BROKER", "internal")
    for e in _cycles(10, armed=2):
        store.append_jsonl("events.jsonl", e)
    assert _row(wd.parity_report(), "mirror_parity") is None      # soru anlamsız → sorulmaz


# ---------- 5) ölçülen edge ----------
def test_negative_edge_in_every_regime_is_surfaced(sandbox_state):
    store.write_json("regime_edge.json", {"trend_up": {"n": 30, "avg_r": -0.8},
                                          "chop": {"n": 40, "avg_r": -0.5}})
    r = _row(wd.parity_report(), "measured_edge")
    assert r and r["ok"] is False and "negatif" in r["detail"]


def test_thin_regime_slices_are_ignored(sandbox_state):
    """n<20 dilimlerle edge yorumu yapılmaz — gürültüyle alarm üretmek dedektörü değersizleştirir."""
    store.write_json("regime_edge.json", {"trend_up": {"n": 5, "avg_r": -2.0}})
    assert _row(wd.parity_report(), "measured_edge") is None


# ---------- entegrasyon ----------
def test_parity_is_part_of_the_integrity_report_and_alarms(sandbox_state, monkeypatch):
    rep = wd.integrity_report()
    assert "parity" in rep and "rows" in rep["parity"]
    store.write_json("regime_edge.json", {"chop": {"n": 40, "avg_r": -0.5}})
    wd.check_integrity_and_alarm()
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "MAKULLÜK" in blob, "makullük ihlali alarma dönüşmüyor"


# ---------- 5) cf sadakati: BİRLEŞME MÜMKÜN MÜ ----------
def test_impossible_join_is_named_as_such(sandbox_state):
    """CANLI BULGU: cf_fidelity plan_id'yi `P-YYYY-MM-DD-TICKER` diye ayrıştırıyor, ama replay'den
    tohumlanmış işlemler `P00140` şemasındaydı → 90 işlemin 90'ı elendi ve mekanizma sonsuza kadar
    None döndü. Üretkenlik dedektörü 'aç' diyordu; NEDEN'ini söyleyemiyordu. 'Veri birikmiyor' ile
    'anahtar tutmuyor' aynı şey değildir."""
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P{i:05d}", "r_multiple": 0.5}
                                       for i in range(20)])
    r = _row(wd.parity_report(), "cf_fidelity_join")
    assert r and r["ok"] is False and "ANAHTAR TUTMUYOR" in r["detail"]


def test_joinable_ids_pass(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P-2026-05-{i+1:02d}-AAA",
                                        "r_multiple": 0.5} for i in range(20)])
    assert _row(wd.parity_report(), "cf_fidelity_join")["ok"] is True


def test_unfaithful_simulation_is_flagged(sandbox_state):
    """Sadakat ÖLÇÜLDÜ ve KÖTÜ çıktıysa bu sessiz kalamaz: cf-beslemeli her kalibrasyon (gölge
    model, silahlanma, near-miss) o iskontoyla okunmalı."""
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P-2026-05-{i+1:02d}-AAA",
                                        "r_multiple": 0.5} for i in range(20)])
    store.write_json("cf_fidelity.json", {"n": 25, "corr": 0.1, "mean_diff_r": 1.4,
                                          "fidelity_ok": False})
    r = _row(wd.parity_report(), "cf_fidelity_quality")
    assert r and r["ok"] is False and "UYMUYOR" in r["detail"]


def test_faithful_simulation_is_quiet(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P-2026-05-{i+1:02d}-AAA",
                                        "r_multiple": 0.5} for i in range(20)])
    store.write_json("cf_fidelity.json", {"n": 25, "corr": 0.8, "mean_diff_r": 0.1,
                                          "fidelity_ok": True})
    assert _row(wd.parity_report(), "cf_fidelity_quality")["ok"] is True


# ---------- 6) LLM görüş↔sonuç ----------
def test_stamped_opinions_that_never_become_pairs_are_flagged(sandbox_state):
    store.write_jsonl("trade_plans.jsonl", [{"id": f"P-2026-05-{i+1:02d}-AAA", "llm_opinion": "destekle"}
                                            for i in range(6)])
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P-2026-05-{i+1:02d}-AAA",
                                        "r_multiple": 0.4} for i in range(6)])
    store.write_json("llm_calibration.json", {"n_pairs": 0, "buckets": {}})
    r = _row(wd.parity_report(), "llm_pair_join")
    assert r and r["ok"] is False and "görüş çiftine dönüşmüyor" in r["detail"]


def test_pairs_accumulating_is_ok(sandbox_state):
    store.write_jsonl("trade_plans.jsonl", [{"id": f"P-2026-05-{i+1:02d}-AAA", "llm_opinion": "destekle"}
                                            for i in range(6)])
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P-2026-05-{i+1:02d}-AAA",
                                        "r_multiple": 0.4} for i in range(6)])
    store.write_json("llm_calibration.json", {"n_pairs": 6, "buckets": {}})
    assert _row(wd.parity_report(), "llm_pair_join")["ok"] is True


def test_promotion_without_enough_pairs_is_flagged(sandbox_state):
    """Terfi kuralı yazılı: >=30 çift. İşaret varsa ama kanıt yoksa kural atlanmış demektir."""
    store.write_json("llm_calibration.json", {"n_pairs": 4, "promoted": True, "buckets": {}})
    r = _row(wd.parity_report(), "llm_promotion_rule")
    assert r and r["ok"] is False and "30" in r["detail"]


def test_plan_id_scheme_is_shared_by_both_engines():
    """Kimlik şeması TEK olmalı: canlı döngü, backtest ve cf_backfill aynı anahtarı üretir."""
    import inspect
    from meridian import backtest, loop, cf_backfill
    assert 'f"P-{d.date()}-{sig.ticker}"' in inspect.getsource(backtest.replay)
    assert 'f"P-{dstr}-' in inspect.getsource(loop.daily_cycle)
    assert 'f"P-{dstr}-' in inspect.getsource(cf_backfill)


# ---------- 7) ŞEMA TAKASI ENVANTERİ ----------
# "Bu tarz şemaları uyuşmayan başka fonksiyonlar var mı?" sorusunun kalıcı cevabı.
# Her sınır geçişinde alan adı değişebiliyor (plan→cf: r_multiple_expected→rr_expected,
# plan→Position: score→plan_score, Position→trade: regime_at_plan→regime). Tüketiciler bunu
# "iki ad da olabilir" yamasıyla telafi ediyor — ama yaması OLMAYAN her yeni tüketici satırı
# sessizce eler. Yamalar bir envanterde SABİTLENİR: yenisi çıkarsa test kırılır ve tartışılır.
DECLARED_ALIASES = {
    ("hermes.py", "variable", "new"),              # şema değil: geçerlilik kontrolü
    ("hermes.py", "n_pairs", "cf_pairs"),          # gerçek çift yoksa simüle çifte düş (bilinçli)
    ("hermes_runtime.py", "ts_close", "ts_open"),  # kapanış yoksa açılış tarihi (bilinçli)
    ("loop.py", "plan_id", "ticker"),              # kayıt etiketi için yedek (görüntüleme)
    ("memory.py", "status_ts", "ts"),              # geçiş damgası yoksa oluşturma damgası
    ("mirror_stream.py", "kept", "foreign"),       # sayım için iki liste
    ("rollback.py", "live_score", "backtest_oos"), # canlı skor yoksa kapı skoru (bilinçli zincir)
    ("shadow_model.py", "score", "plan_score"),    # ŞEMA TAKASI: aynı kavram, iki ad
    ("shadow_model.py", "r_multiple_expected", "rr_expected"),   # ŞEMA TAKASI
    ("shadow_model.py", "regime_at_plan", "regime"),             # ŞEMA TAKASI
    ("watchdog.py", "armed", "alpaca_submitted"), # "ikisinden biri varsa" kontrolü
    # mutasyon koşumu farklı dedektörlerin çıktısını tek biçime indirger: kimi `violations`,
    # kimi `rows` döndürür. Şema ayrışması değil, dedektör arayüzlerinin normalleştirilmesi.
    ("mutation.py", "violations", "rows"),
    # Sağlayıcı API'leri aynı kavramı farklı adlandırır: Gemini `functionCall`, diğerleri
    # `tool_calls`. Bu bir ŞEMA AYRIŞMASI değil, dış arayüzün normalleştirilmesi (2026-07-22).
    ("hermes.py", "tool_calls", "function_call"),
    # Kimlik havuzu sağlığı: toplam anahtar sayısı ile SAĞLIKLI anahtar sayısı ayrı ölçülerdir;
    # ikisi de yalnız SAYIDIR — hiçbir kimlik DEĞERİ okunmaz (bir test bunu ayrıca kilitliyor).
    ("hermes.py", "keys", "healthy"),
    # OLAY DEFTERİNİN İKİ TARİHSEL YAZIMI (2026-07-30, nous telemetri paketi). `events.jsonl`da bir
    # olayın adı İKİ ayrı alanda yazılıdır: `warn` döneminde yazılan tarihsel satırlar adı `event`te
    # taşır, K1'den sonra alarma çevrilen satırlar `obs.alarm(token, msg, kind=...)` yüzünden adı
    # `kind`ta taşır. Bu bir ŞEMA AYRIŞMASI DEĞİL, tek defterin iki tarihsel yazımının
    # normalleştirilmesidir ve `watchdog.parity_report` ZATEN aynı ikiliyi okuyor (orada iki ayrı
    # eşitlik olduğu için tarayıcının deseni tutmuyordu). Yalnız `event`i okumak dedektörü GEÇMİŞE
    # kör bırakırdı — `session_bar_never_published`ın 164 tarihsel satırının kaybolduğu hata tam
    # buydu (bkz. watchdog.py:parity_report'taki "failed_broker_rejection dersinin tersi" notu).
    ("analytics.py", "event", "kind"),
    # ALIAS DEĞİL, AYRI DÜRÜSTLÜK SAYACI (2026-08-02, HERMES-DAYANIKLILIK / `-Q` turu). CLI'nin
    # sessiz modu (`-Q`) oturum özetini bastırdığı için bazı çağrılarda araç sayısı ÖLÇÜLEMEZ.
    # `calls` = araç sayısı ÖLÇÜLEBİLEN çağrılar (oranın paydası), `olculemeyen` = ölçülemeyenler.
    # İkisi aynı kavramın iki adı DEĞİLDİR ve bilerek ayrık tutulur: ölçülemeyeni `calls`a katmak
    # `rate`i sessizce seyreltir (uydurma), hiç saymamak ise sayacı dondurup "MCP hiç kullanılmadı"
    # diye okutur (eksik alan = sıfır sanılır sınıfı). `integrations_status` ikisini AYRI yayınlar
    # ve payda sıfırken `rate` None döner. Deseni yakalayan satır yalnızca "hangisi doluysa göster"
    # kapısıdır (`if tu and (tu.get("calls") or tu.get("olculemeyen"))`), bir yedek-ad yaması değil.
    ("hermes.py", "calls", "olculemeyen"),
    # ALIAS DEĞİL, İKİ AYRI SAPMA BOYUTUNUN BİRLEŞİMİ (2026-08-13, v239 ayna-rozeti turu).
    # `loop.ayna_sapma_alanlari` nabza `position_drift` yazarken şu kapıyı kuruyor:
    #     bool(pos.get("missing_on_alpaca") or pos.get("qty_drift"))
    # İkisi AYNI kavramın iki adı DEĞİLDİR ve biri diğerinin yedeği hiç değildir:
    #   · `missing_on_alpaca` = pozisyon bizim kitabımızda VAR, Alpaca aynasında YOK (EKSİK KAYIT).
    #   · `qty_drift`         = pozisyon İKİ TARAFTA DA var ama ADET tutmuyor (canlı ölçüm
    #                           2026-08-12T22:01Z: NUE 54/25 · EMR 64/37 · BKNG 43/22 · AMGN 33/22).
    # Yani bu bir "hangi ad varsa onu al" yaması değil, İKİSİNDEN BİRİ VARSA sapma vardır MANTIKSAL
    # BİRLEŞİMİdir — envanterdeki `("watchdog.py", "armed", "alpaca_submitted")` ve
    # `("mirror_stream.py", "kept", "foreign")` satırlarıyla aynı sınıf. Tarayıcının deseni
    # (`X.get(a) or X.get(b)`) birleşimi takastan ayırt edemez; ayrım ancak burada YAZILI olur.
    # İKİSİNİ TEK ALANA İNDİRMEK YASAK: rozet "sapma var mı" sorusunu tek bit olarak cevaplar, ama
    # kaynak iki alan AYRI kalmalı — mutabakat masası hangi sınıfın gerçekleştiğini söyler
    # (eksik kayıt → gönderim yolu onarımı; adet sapması → miktar mutabakatı; farklı eylemler).
    ("loop.py", "missing_on_alpaca", "qty_drift"),
}


def _alias_scan():
    import re, pathlib
    pats = [
        r'(\w+)\.get\("([a-z_]+)"\)\s+if\s+\1\.get\("\2"\)\s+is not None\s+else\s+\1\.get\("([a-z_]+)"\)',
        r'(\w+)\.get\("([a-z_]+)"\)\s+or\s+\1\.get\("([a-z_]+)"\)',
        r'(\w+)\.get\("([a-z_]+)",\s*\1\.get\("([a-z_]+)"',
    ]
    found = set()
    for f in pathlib.Path("meridian").rglob("*.py"):
        src = f.read_text()
        for pat in pats:
            for m in re.finditer(pat, src):
                if m.group(2) != m.group(3):
                    found.add((f.name, m.group(2), m.group(3)))
    return found


def test_no_undeclared_field_alias_appears():
    """Yeni bir 'iki ad da olabilir' yaması, geçmişte yaşanmış bir şema ayrışmasının izidir.
    Beyan edilmemiş bir tanesi belirirse burada tartışılır — sessizce birikmez."""
    undeclared = _alias_scan() - DECLARED_ALIASES
    assert not undeclared, f"beyan edilmemiş şema takası: {sorted(undeclared)}"


def test_declared_aliases_still_exist():
    """Envanter ÇÜRÜMESİN: düzeltilen bir takas listede kalırsa liste yalan söylemeye başlar."""
    stale = DECLARED_ALIASES - _alias_scan()
    assert not stale, f"artık var olmayan takas beyanı (listeden çıkarılmalı): {sorted(stale)}"


def test_cf_rows_carry_the_canonical_expected_r(sandbox_state):
    """Kaynağında düzeltme: cf satırı artık KANONİK adı da taşır, böylece yaması olmayan bir
    tüketici de satırı görebilir (eski ad geriye dönük uyumluluk için duruyor)."""
    from meridian import counterfactual as cf
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    plan = {"id": "P-2026-07-20-AAA", "ticker": "AAA", "setup": "breakout_vcp", "score": 71,
            "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0,
            "r_multiple_expected": 3.0, "regime_at_plan": "chop", "gate_verdict": "GO"}
    cf.collect("2026-07-20", [plan], {"P-2026-07-20-AAA"}, [], 15, regime="chop")
    row = store.read_json(cf.OPEN_FILE, [])[0]
    assert row["r_multiple_expected"] == 3.0 and row["rr_expected"] == 3.0


# ---------- 8) DEFTER ŞEMASI ----------
# Şema denetiminin GÖVDESİ buradan taşındı: tests/test_ledger_contract_v57.py
# (üretici doğrulaması + yazar sınırı + anahtar biçimi). Şemayı iki test dosyasında tanımlamak,
# bu denetimin bulduğu "aynı yasanın iki uygulaması" hatasını üretirdi. Burada yalnız dedektörün
# EŞİK davranışı kalıyor — ince defteri yargılamamak makullük dedektörüne özgü bir karardır.
def test_thin_ledger_is_not_judged(sandbox_state):
    store.write_jsonl("trades.jsonl", [{"id": "T1", "r_multiple": 0.4}])
    assert _row(wd.parity_report(), "ledger_contract:trades") is None    # 5 satırdan az → yorum yok
