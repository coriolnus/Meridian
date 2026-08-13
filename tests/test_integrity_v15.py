"""test_integrity_v15.py — BÜTÜNLÜK DEDEKTÖRLERİ (2026-07-21, operatör: "bu tarz gözünden kaçan çok
fazla eksiklik olabilir, bunu nasıl çözeriz" → "üçünü de kur").

Bugün bulunan hataların HEPSİ mevcut testlerden/denetimlerden geçmişti ("import oluyor, koşuyor, 200
dönüyor"). Eksik olan üç soru, üç dedektör:
  #1 ÜRETKENLİK  — mekanizma koşuyor ama ÜRETİYOR mu?      (cf defteri ömrü boyunca 0 satırdı)
  #2 KORUNUM     — giren plan kayıtlı terminale ulaşıyor mu? (silahlı planlar kayıtsız buharlaştı)
  #3 DETERMİNİZM — barlar geçersiz kılınmadan değişti mi?    (cache altından bar mutasyonu)
Hepsi yalnız GÖZLEM: hiçbir karara/kapıya dokunmaz."""
import json

from meridian import store, watchdog as w


# ---------------- #1 ÜRETKENLİK ----------------
def test_production_flags_starved_but_not_waiting(sandbox_state):
    """'Hiç üretmemiş' (starved = hata şüphesi) ile 'eşik dolmamış' (waiting = sabır) DÜRÜSTÇE ayrılır."""
    store.write_jsonl("counterfactuals.jsonl", [{"id": "a"}])          # üretiyor
    store.write_jsonl("trades.jsonl", [{"id": 1}])
    store.write_jsonl("hypotheses.jsonl", [{"id": "h"}])
    store.write_json("score_calibration.json", {"n": 5})               # var ama eşik(30) altı → waiting
    store.write_json("near_miss.json", {"resolved_total": 12})
    store.write_json("llm_calibration.json", {"n_pairs": 2})
    store.write_json("gate_calibration.json", {"n_measured": 1})
    # exit_efficiency + cf_fidelity dosyaları YOK → starved
    rep = w.production_report()
    starved = {s["name"] for s in rep["starved"]}
    waiting = {s["name"] for s in rep["waiting"]}
    assert "exit_efficiency" in starved and "cf_fidelity" in starved   # hiç üretmemiş
    assert "score_calibration" in waiting                              # üretiyor ama eşik altı
    assert "counterfactual_ledger" not in starved                      # üretiyor → temiz


def test_production_catches_the_cf_bug_that_escaped_everything(sandbox_state):
    """Regresyon: cf defteri BOŞ olsaydı dedektör onu ilk gün 'ÜRETMİYOR' derdi (canlıda ömrü boyunca
    boştu ve hiçbir denetim söylemedi — 4 alt mekanizmayı da aç bıraktı)."""
    store.write_jsonl("counterfactuals.jsonl", [])
    rep = w.production_report()
    assert any(s["name"] == "counterfactual_ledger" for s in rep["starved"])


# ---------------- #2 KORUNUM ----------------
def test_conservation_counts_only_real_silent_losses(sandbox_state):
    """Giren plan ya işleme dönmeli, ya kapıda ölmeli (NO_GO), ya düşüşü OLAYLA kaydedilmeli, ya da
    tetiği hiç gelmemiş olmalı (cf no_fill = MEŞRU). Hiçbirine uymayan = sessiz kayıp."""
    store.write_json("portfolio.json", {"last_date": "2026-07-17"})
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-1", "date": "2026-07-01", "ticker": "AAA", "gate_verdict": "GO"},   # işleme döndü
        {"id": "P-2", "date": "2026-07-02", "ticker": "BBB", "gate_verdict": "NO_GO"},# kapıda öldü
        {"id": "P-3", "date": "2026-07-03", "ticker": "CCC", "gate_verdict": "GO"},   # olayla düştü
        {"id": "P-4", "date": "2026-07-04", "ticker": "DDD", "gate_verdict": "GO"},   # cf: no_fill → meşru
        {"id": "P-5", "date": "2026-07-05", "ticker": "EEE", "gate_verdict": "GO"},   # SESSİZ KAYIP
        {"id": "P-6", "date": "2026-07-17", "ticker": "FFF", "gate_verdict": "GO"},   # bugünün planı
    ])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P-1", "r_multiple": 1.0}])
    store.write_jsonl("events.jsonl", [
        {"event": "daily_cycle", "date": "2026-07-01"},          # canlı dönem sınırı
        {"event": "armed_expired_no_bar", "plan_id": "P-3"}])
    store.write_jsonl("counterfactuals.jsonl", [
        {"id": "CF-1", "date": "2026-07-04", "ticker": "DDD", "status": "no_fill_gap"},
        {"id": "CF-2", "date": "2026-07-05", "ticker": "EEE", "status": "closed"},
    ])
    rep = w.conservation_report()
    assert rep["no_fill"] == 1                                  # DDD meşru (tetik gelmedi)
    assert rep["unexplained"] == 1                              # yalnız EEE (canlı dönem)
    assert rep["rows"][0]["ticker"] == "EEE"


def test_conservation_separates_replay_era_blindness(sandbox_state):
    """Replay tohumu planı yazar ama OLAY kaydı tutmaz — 'neden silahlanmadı' orada yapısal olarak
    görünmez. Canlıda ölçüldü: 31 bayrağın 30'u replay dönemiydi, 1'i gerçek sızıntı (GS). Dedektör
    bu ikisini KARIŞTIRMAMALI, yoksa sayı eyleme dönüşmez."""
    store.write_json("portfolio.json", {"last_date": "2026-07-17"})
    store.write_jsonl("events.jsonl", [{"event": "daily_cycle", "date": "2026-07-10"}])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "R-1", "date": "2024-05-02", "ticker": "OLD", "gate_verdict": "GO"},   # replay dönemi
        {"id": "R-2", "date": "2025-11-03", "ticker": "OLD2", "gate_verdict": "REVIEW"},
        {"id": "L-1", "date": "2026-07-14", "ticker": "GS", "gate_verdict": "GO"},    # CANLI sızıntı
    ])
    rep = w.conservation_report()
    assert rep["replay_era"] == 2                               # körlük — sızıntı sayılmaz
    assert rep["unexplained"] == 1 and rep["rows"][0]["ticker"] == "GS"


# ---------------- #3 DETERMİNİZM ----------------
def test_determinism_detects_silent_bar_mutation(sandbox_state):
    """Barlar DEĞİŞTİ ama wf-revizyon SABİT kaldıysa → önbelleklenmiş walk-forward'lar artık yok olan
    barlara ait (bugün bulunan kapı-bütünlüğü hatası). Dedektör bunu yakalamalı."""
    from meridian import config
    (config.BARS / "aaa.csv").write_text("date,open,high,low,close,volume\n2024-01-02,1,1,1,1,1\n")
    store.write_json("wf_cache_rev.json", {"rev": 3})
    first = w.determinism_report(persist=True)
    assert first["ok"] and "ilk anlık görüntü" in first.get("detail", "")
    # GEÇMİŞİ yeniden yaz (dosya KÜÇÜLSÜN), revizyonu SABİT bırak → sessiz mutasyon
    (config.BARS / "aaa.csv").write_text("date,o\n1,2\n")
    bad = w.determinism_report(persist=True)
    assert bad["ok"] is False and bad.get("silent_bar_mutation") is True
    assert "aaa.csv" in bad["shrunk"]


def test_determinism_ignores_benign_append(sandbox_state):
    """Bugünün mumunun EKLENMESİ (dosya büyür) walk-forward penceresini (geçmişte biter) etkilemez —
    alarm ÜRETMEMELİ. Dedektörün kurt masalı anlatmaması bunun kadar önemlidir."""
    from meridian import config
    (config.BARS / "ccc.csv").write_text("date,open,high,low,close,volume\n2024-01-02,1,1,1,1,1\n")
    store.write_json("wf_cache_rev.json", {"rev": 100})
    w.determinism_report(persist=True)
    (config.BARS / "ccc.csv").write_text("date,open,high,low,close,volume\n2024-01-02,1,1,1,1,1\n"
                                         "2024-01-03,1,1,1,1,1\n")          # yalnız EKLEME
    rep = w.determinism_report(persist=True)
    assert rep["ok"] is True and rep["appended"] >= 1


def test_determinism_ok_when_rev_bumped_with_bars(sandbox_state):
    """Karşı-kontrol: barlar değişti AMA revizyon da arttıysa (doğru davranış) → alarm YOK."""
    from meridian import config
    (config.BARS / "bbb.csv").write_text("date,open,high,low,close,volume\n2024-01-02,1,1,1,1,1\n")
    store.write_json("wf_cache_rev.json", {"rev": 1})
    w.determinism_report(persist=True)
    (config.BARS / "bbb.csv").write_text("date,open,high,low,close,volume\n2024-01-02,2,2,2,2,2\n")
    store.write_json("wf_cache_rev.json", {"rev": 2})            # bar değişimiyle birlikte bumplandı
    assert w.determinism_report(persist=True)["ok"] is True


# ---------------- alarm katmanı ----------------
def test_integrity_alarms_once_per_violation(sandbox_state, monkeypatch):
    """İhlaller bir kez alarmlanır (spam yok); bekçi felsefesi: yalnız haber verir, düzeltmez."""
    from meridian import obs
    fired = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: fired.append((tok, kw.get("kind"))))
    store.write_jsonl("counterfactuals.jsonl", [])               # starved
    w.check_integrity_and_alarm()
    n1 = len(fired)
    assert n1 > 0 and any(k == "starved" for _, k in fired)
    w.check_integrity_and_alarm()                                # ikinci koşum: aynı ihlal
    assert len(fired) == n1                                      # tekrar alarmlamaz


def test_integrity_report_shape(sandbox_state):
    """Şekil sözleşmesi — SEKİZ desenin TAMAMI raporda. 7. desen (makullük/parity) 2026-07-21'de
    eklendi: ilk altısı bileşen bazlıdır ve 'doğru parçalar, yanlış sistem sonucu' sınıfını göremez
    — motorun evrenin %18'inde karar verdiği hata tam o sınıftandı.

    8. desen (değer-eşitliği/divergence) 2026-08-13'te BEYANLI eklendi: ilk yedisinin hiçbiri
    "iki kaynak AYNI ŞEYİ mi söylüyor?" diye sormuyordu — `coherence` ZAMAN ölçer, dolayısıyla
    aynı saniyede yazılmış ZIT DEĞERLİ iki dosya bütün kapılardan yeşil geçiyordu."""
    rep = w.integrity_report(persist=True)
    assert {"production", "conservation", "determinism", "coherence",
            "monotonicity", "ownership", "parity", "divergence"} == set(rep)


# ---------------- #4 TUTARLILIK (türev bayatlığı) ----------------
def test_coherence_flags_derived_older_than_source(sandbox_state):
    """Bar↔cache hatasının GENEL hali: kaynak büyümüş ama türev güncellenmemişse o türev sessizce
    bayattır (canlıda: gölge model 7115 yeni cf satırını görmedi)."""
    import os, time
    from meridian import config
    src = config.STATE / "counterfactuals.jsonl"
    art = config.STATE / "near_miss.json"
    art.write_text("{}")
    src.write_text('{"id":"x"}\n')
    old = time.time() - 6 * 3600                       # türev 6 saat ESKİ
    os.utime(art, (old, old))
    rep = w.coherence_report()
    assert any(s["artifact"] == "near_miss.json" for s in rep["stale"])
    # tersine: türev kaynaktan yeniyse temiz
    now = time.time()
    os.utime(art, (now, now))
    assert not any(s["artifact"] == "near_miss.json" for s in w.coherence_report()["stale"])


# ---------------- #5 MONOTONLUK ----------------
def test_monotonicity_detects_backward_movement(sandbox_state):
    """İleri-only nicelikler (kitap tarihi, sürüm, revizyon, defter satırları) ASLA azalmamalı —
    azalma bozuk yazım/kötü restore/geri sarma demektir (geriye-seans hatasının genel hali)."""
    store.write_json("portfolio.json", {"last_date": "2026-07-17", "peak_equity": 110000})
    store.write_json("wf_cache_rev.json", {"rev": 5})
    store.write_jsonl("trades.jsonl", [{"id": 1}, {"id": 2}])
    first = w.monotonicity_report(persist=True)
    assert first["ok"] and "ilk anlık" in first.get("detail", "")
    # kitap GERİ sarsın + defter küçülsün
    store.write_json("portfolio.json", {"last_date": "2026-07-10", "peak_equity": 90000})
    store.write_jsonl("trades.jsonl", [{"id": 1}])
    bad = w.monotonicity_report(persist=True)
    assert bad["ok"] is False
    fields = {r["field"] for r in bad["regressions"]}
    assert {"book_date", "peak_equity", "trades"} <= fields


# ---------------- #6 SAHİPLİK ----------------
def test_ownership_detects_field_clobber(sandbox_state):
    """Bir kez dolmuş kritik alan sonradan kaybolduysa, sahiplenmeyen bir yazıcı üzerine yazmıştır
    (canlıda: /api/halt nabzı yalnız note ile yazınca rejim/bütçe silindi → HUD 'rejim yok')."""
    store.write_json("heartbeat.json", {"regime": "chop", "exposure_budget_pct": 25, "equity": 100000})
    assert w.ownership_report(persist=True)["ok"] is True
    store.write_json("heartbeat.json", {"note": "HALT"})        # alanları ezen yazım
    bad = w.ownership_report(persist=True)
    assert bad["ok"] is False
    lost = {l["field"] for l in bad["lost"]}
    assert {"regime", "exposure_budget_pct"} <= lost


# ---------------- kapsam kaydı ----------------
def test_coverage_registry_is_honest_and_finite(sandbox_state):
    """Kayıt bilinmeyen yüzeyi SONLU ve GÖRÜNÜR kılar; hücre ancak gerçek kontrol varsa dolu sayılır."""
    from meridian import integrity_registry as ir
    r = ir.coverage_report()
    assert r["cells_total"] == r["components"] * r["patterns"]
    assert 0 < r["cells_covered"] < r["cells_total"]          # dürüst: ne sıfır ne tam
    # 2026-07-21: dönüşümlü denetimin İLK TAM TURU bitti — 49 bileşenin hepsi en az bir kez
    # denetlendi, yani unaudited_n artık 0. Değişmez olan şu: kayıt HER ZAMAN geçerli bir sonraki
    # hedef verir (rotasyon durmaz) ve kapsam asla "tam" iddia etmez.
    assert r["unaudited_n"] >= 0 and r["next_target"] in ir.COVERED
    # 2026-07-21: UYGULANABİLİR hücrelerin tamamı kapandı (%100). Korunması gereken dürüstlük şu:
    # HAM ızgara asla "tam" değildir — 109 hücre "sorusu yok" diye ELENDİ ve bu eleme BİR YARGIDIR.
    # Yani "%100" = "beyan ettiğim soruların hepsini test ettim", "hata kalmadı" DEĞİL.
    assert r["raw_pct"] < 100.0, "ham ızgara tam iddiası — N/A yargısı gözden geçirilmeli"
    assert r["cells_na"] > 0 and r["coverage_pct"] <= 100.0
    # denetim kaydı hedefi ilerletir
    t = r["next_target"]
    ir.record_audit(t)
    assert store.read_json(ir.AUDIT_LOG, {}).get(t)


# (şekil sözleşmesi tek yerde: test_integrity_report_shape. Buradaki ikinci kopya 2026-07-21'de
#  silindi — aynı yasanın iki uygulaması, bu denetimin bulduğu baskın hata sınıfının kendisiydi.)


def test_wf_revision_is_monotonic_by_construction(sandbox_state):
    """Monotonluk dedektörü canlıda wf_rev 4→1 GERİLEMESİNİ yakaladı: sayaç oku-artır-yaz idi, okuma
    boş dönünce 1'e sıfırlanıyor ve bayat önbellekler yeniden 'geçerli' oluyordu. Artık zaman-damgalı:
    sıfırlanamaz, eşzamanlı yazımda kayıp-güncelleme üretmez."""
    from meridian import reflect
    store.write_json("wf_cache_rev.json", {"rev": 999_999_999_999})   # gelecekten büyük değer
    reflect.clear_wf_caches()
    assert store.read_json("wf_cache_rev.json", {})["rev"] > 999_999_999_999   # ASLA geri gitmez
    store.write_json("wf_cache_rev.json", {})                          # okuma boş dönse bile
    reflect.clear_wf_caches()
    assert store.read_json("wf_cache_rev.json", {})["rev"] > 1_700_000_000     # 1'e düşmez


# ---------------- uygulanabilirlik matrisi (2026-07-21, ilk tam turdan sonra) ----------------
def test_covered_is_a_subset_of_applicable(sandbox_state):
    """Dürüstlük kuralının ikinci yarısı: ANLAMSIZ ilan ettiğin bir hücreyi 'kapsandı' sayamazsın.
    (İhlal, ya kapsam iddiasının ya da N/A gerekçesinin yanlış olduğunu söyler.)"""
    from meridian import integrity_registry as ir
    for comp, cov in ir.COVERED.items():
        app = set(ir.APPLICABLE.get(comp, ()))
        extra = set(cov) - app
        assert not extra, f"{comp}: {sorted(extra)} hem 'kapsandı' hem 'uygulanamaz' işaretli"


def test_every_component_has_an_applicability_row(sandbox_state):
    from meridian import integrity_registry as ir
    assert set(ir.APPLICABLE) == set(ir.COVERED)
    for comp, app in ir.APPLICABLE.items():
        assert app, f"{comp}: hiçbir desen uygulanabilir değil — bu bir modül değil, bir sabit olurdu"
        assert set(app) <= set(ir.PATTERNS)


def test_gaps_are_the_real_queue(sandbox_state):
    """gaps() SADECE uygulanabilir-ama-boş hücreleri verir; N/A hücreler kuyruğa girmez."""
    from meridian import integrity_registry as ir
    g = ir.gaps()
    for row in g:
        app = set(ir.APPLICABLE[row["component"]])
        assert set(row["missing"]) <= app
        assert not (set(row["missing"]) & set(row["covered"]))
    r = ir.coverage_report()
    assert r["cells_applicable"] + r["cells_na"] == r["cells_total"]
    assert r["coverage_pct"] >= r["raw_pct"], "dürüst payda ham paydadan küçük olmalı"
