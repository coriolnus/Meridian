"""test_kovab_ogrenme_v162.py — KOVA-B ÖĞRENME POLİTİKASI (denetim C14/C16/C17, 2026-08-02).

Üç bulgu, üç kablo. Hepsi ÖĞRENME KATMANINDA ve üçü de aynı sınıftan: kodun BEYAN ettiği ile
yaptığı arasındaki sessiz fark.

  C14 — BİLEŞİK ÖNERİ KUYRUĞU HİÇ KAPANMIYORDU. `spawn_pending` satırı 'measuring' damgalıyor,
        prescreen sonucu yalnız `--workdir`e yazıyor ve geri okuyan kimse yok. Depoda `measured`
        yazan tek üretim yolu YOKTU (tek örnek bir testin elle attığı damgaydı): `n_olculen`
        yapısal olarak 0, `son_olcum` hep None, ölmüş süreçler sonsuza dek "ÖLÇÜLÜYOR". Kablo:
        `--queue-id` ile kimlik taşıması + gece kancasında pid yoklaması (`measure_failed`).

  C16 — ARKA PLAN YANSIMASI GLOBAL SHIP EDEBİLİYORDU. `_bg_ready_regime` docstring'i "ship yalnız
        params_by_regime[o rejim]'i değiştirir" diyordu; kod bg rejimi `trend_up` olduğunda
        `!= "trend_up"` istisnasına düşüp aramayı GLOBAL koşuyor ve düz `params`a yazıyordu — chop
        canlıyken chop davranışı, chop'un hiç sertifika vermediği kanıtla anında değişiyordu.
        Kablo: `reflect_once(..., background=True)` → arama O REJİME zorlanır, global öneri reddedilir.

  C17 — ARAMA SONDALARI RESMÎ DEFTERE SONDA BAŞINA YAZIYORDU. Kodun kendi yorumu "arama oturumu
        pencereye BİR soru sorar" derken döngünün İÇİNDE `record_erosion=True` vardı: tek günde 204
        satır, `erosion.queries` 351→554, aynı K yükü hem sayaca hem `k_probes` beyanına. Kablo:
        sondalar KAYITSIZ (marj yine uygulanır), oturum başına TAM BİR resmî kayıt.

BU DOSYANIN ÖLÇTÜĞÜ ŞEY DAVRANIŞTIR, YORUM DEĞİL: her testin iddiası defterin/çağrının kendisinden
okunur (kuyruk satırı, aşınma sayacı, `search_and_submit`a giden `regime`), bir docstring'den değil.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

from meridian import (config, dataset, hermes, hermes_composite, oos_erosion, prescreen, reflect,
                      store, validation)
from tests import wf_fixtures as wf

SRC = pathlib.Path("meridian")


# =================================================================================================
# ORTAK YARDIMCILAR
# =================================================================================================
def _kuyruga_yaz(status: str = "measuring", **alanlar) -> str:
    """Kuyruğa bir satır koy ve istenen duruma getir. Dönen: satır kimliği."""
    res = hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4},
                                   bounds=config.bounds())
    rid = res["row"]["id"]
    if status != "pending":
        hermes_composite.mark(rid, status, **alanlar)
    return rid


def _satir(rid: str) -> dict:
    for r in store.read_jsonl(hermes_composite.QUEUE_FILE):
        if r.get("id") == rid:
            return r
    raise AssertionError(f"kuyruk satırı bulunamadı: {rid}")


def _sahte_rapor() -> dict:
    """prescreen.run'un dönebileceği en küçük GERÇEKÇİ rapor (alan adları üretimdekiyle birebir)."""
    return {
        "incumbent": {"version": 1, "oos_score": 0.10, "n": 90, "folds": [30, 30, 30]},
        "k_probes": 1, "n_denenen": 1, "n_bilesik": 1,
        "adaylar": [{"knob": "stop_buffer_atr=0.4;stop_mode=1", "bilesik": True, "n_knobs": 2,
                     "knobs": {"stop_mode": 1, "stop_buffer_atr": 0.4},
                     "motor_isliyor": True, "inc_oos": 0.10, "cand_oos": 0.14, "delta": 0.04,
                     "para_delta": 0.012, "p": 0.97, "p_required": 0.95, "dd_durum": "gecti",
                     "gate_law": "probabilistic", "yasa_surumu": "para_v3",
                     "passes": True, "why": ""}],
        "guard_reddi": [],
        "pencereler": {"pencere_id": "R1"},
        "canli_state_degisen_dosyalar": [],
        "workdir": "/tmp/prescreen-TEST", "sure_s": 12.3,
    }


def _olu_pid() -> int:
    """GERÇEKTEN ölmüş bir pid. Sabit bir sayı uydurmak (ör. 999999) testi işletim sisteminin o anki
    pid uzayına bağlardı — geçtiğinde hiçbir şey kanıtlamayan bir test. Burada süreç AÇILIR, biter ve
    `wait()` ile toplanır; yoklama artık ESRCH almak ZORUNDADIR."""
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


# =================================================================================================
# C14 — ÖNER→ÖLÇ→ÖĞREN HALKASI KAPANIYOR
# =================================================================================================
def test_C14_olcum_bitisi_kuyruk_satirini_measured_yapar(sandbox_state, monkeypatch):
    """Ölçüm biter → satır `measured` + `result` ÖZETİ taşır.

    ÖZET BOŞ OLAMAZ: `nous_eval._akibet` "ÖLÇÜLDÜ → {result}" diye beyne rapor eder; `result` None
    ise beyin "ölçüldü ama sonucu yok" cümlesini okur ve aynı öneriyi yeniden üretir — halkanın
    kapanmış GÖRÜNÜP kapanmamış hâli, açık halkadan beterdir."""
    rid = _kuyruga_yaz("measuring", pid=os.getpid(), k_probes=1)   # spawn_pending'in yazdığı hâl
    monkeypatch.setattr(prescreen, "run", lambda *a, **k: _sahte_rapor())
    prescreen.main(["--composite", "stop_mode=1;stop_buffer_atr=0.4",
                    "--workdir", str(sandbox_state / "wd"),
                    "--live-state", str(sandbox_state), "--queue-id", rid])
    r = _satir(rid)
    assert r["status"] == "measured", "ölçüm bitti ama satır 'measured' olmadı — halka hâlâ açık"
    ozet = r["result"]
    assert ozet and ozet["n_aday"] == 1
    a = ozet["adaylar"][0]
    # HÜKMÜN KENDİSİ ve KARAR DEĞİŞKENLERİ satırda: `passes` hüküm, `para_delta`/`p` PARA-v3'ün
    # okuduğu sayılar. Yalnız bileşik `delta` yazılsaydı okuyucu rapor metriğini hüküm sanardı.
    assert a["passes"] is True and a["para_delta"] == 0.012 and a["p"] == 0.97
    assert a["knobs"] == {"stop_mode": 1, "stop_buffer_atr": 0.4}
    assert ozet["pencere_id"] == "R1"          # habersiz kıyas yasağı satırın İÇİNDE
    assert r["olcum_k_probes"] == 1            # kapı dili; H4 bütçe dili olan `k_probes` AYRI alan
    assert r["k_probes"] == 1                  # bütçe alanı EZİLMEDİ


def test_C14_kuyruk_durumu_olculeni_gorur(sandbox_state, monkeypatch):
    """`n_olculen` artık yapısal olarak 0 DEĞİL — okuyucu tarafın (analytics/evidence_pack) gördüğü
    sayı gerçekten hareket ediyor."""
    rid = _kuyruga_yaz("measuring", pid=os.getpid())
    monkeypatch.setattr(prescreen, "run", lambda *a, **k: _sahte_rapor())
    once = hermes_composite.queue_status()
    assert once["n_olculen"] == 0 and once["son_olcum"] is None
    prescreen.main(["--composite", "stop_mode=1", "--workdir", str(sandbox_state / "wd"),
                    "--live-state", str(sandbox_state), "--queue-id", rid])
    sonra = hermes_composite.queue_status()
    assert sonra["n_olculen"] == 1 and sonra["son_olcum"] is not None


def test_C14_guard_hepsini_reddederse_measure_failed(sandbox_state, monkeypatch):
    """Guard bütün adayları reddettiyse ölçüm YAPILMADI. 'measured' demek, olmamış bir ölçümü
    olmuş göstermek olurdu (uydurma yasağı) — satır `measure_failed` + NEDEN taşır."""
    rid = _kuyruga_yaz("measuring", pid=os.getpid())
    monkeypatch.setattr(prescreen, "run", lambda *a, **k: {"hata": "guard_hepsini_reddetti",
                                                           "reddedilen": [], "n_denenen": 1})
    prescreen.main(["--composite", "stop_mode=99", "--workdir", str(sandbox_state / "wd"),
                    "--live-state", str(sandbox_state), "--queue-id", rid])
    r = _satir(rid)
    assert r["status"] == "measure_failed"
    assert "guard" in str(r["neden"])


def test_C14_olcum_patlarsa_satir_damgalanir_ve_istisna_YUKSELIR(sandbox_state, monkeypatch):
    """Çökme de bir akıbettir: satır damgalanır AMA istisna yutulmaz (çıkış kodu ve log izi kalır)."""
    rid = _kuyruga_yaz("measuring", pid=os.getpid())

    def _patla(*a, **k):
        raise RuntimeError("veri yüklenemedi")
    monkeypatch.setattr(prescreen, "run", _patla)
    with pytest.raises(RuntimeError):
        prescreen.main(["--composite", "stop_mode=1", "--workdir", str(sandbox_state / "wd"),
                        "--live-state", str(sandbox_state), "--queue-id", rid])
    r = _satir(rid)
    assert r["status"] == "measure_failed" and "RuntimeError" in str(r["neden"])


def test_C14_kimlik_spawn_komutunda_TASINIR(sandbox_state):
    """Kimlik taşınmazsa alt süreç sonucu geri yazamaz — C14'ün kök nedeni tam olarak buydu
    (`prescreen.main` argümanları kuyruk kimliğini hiç almıyordu)."""
    hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4}, bounds=config.bounds())
    r = hermes_composite.spawn_pending(limit=1, dry_run=True)
    cmd = r["spawned"][0]["cmd"]
    assert "--queue-id" in cmd, "spawn komutu kuyruk kimliğini taşımıyor — halka kapanamaz"
    assert cmd[cmd.index("--queue-id") + 1] == r["spawned"][0]["id"]
    # İKİ TARAF AYRIŞIRSA SÜREÇ ANINDA ÖLÜR: komutu KURAN taraf `--queue-id` yazarken argümanı KABUL
    # eden taraf onu tanımazsa argparse `unrecognized arguments` ile 2 döner ve ölçüm hiç başlamaz —
    # bütçe harcanır, satır 'measuring' asılı kalır. Kabul yüzeyi bu yüzden ayrıca sınanır.
    with pytest.raises(SystemExit):
        prescreen.main(["--queue-id", "C00001"])            # --workdir zorunlu → 2 (kimlik TANINDI)
    ap_kaynak = (SRC / "prescreen.py").read_text(encoding="utf-8")
    assert 'ap.add_argument("--queue-id"' in ap_kaynak


def test_C14_olu_surec_measure_failed_damgalanir(sandbox_state):
    """Ölü pid → `measure_failed`. Bu damga olmadan `nous_eval._akibet` beyne aylarca "ÖLÇÜLÜYOR
    (prescreen süreci koşuyor)" der; doğrulanmamış bir olguyu olmuş gibi bildirmek uydurma
    yasağının ihlalidir ve beyin aynı öneriyi her hafta yeniden üretir."""
    rid = _kuyruga_yaz("measuring", pid=_olu_pid())
    out = hermes_composite.reap_measuring()
    assert out["olu"] == [rid]
    r = _satir(rid)
    assert r["status"] == "measure_failed"
    assert len(str(r["neden"])) >= 20, "YASA 4: damganın gerekçesi ≥20 karakter olmalı"


def test_C14_canli_surec_ASLA_damgalanmaz(sandbox_state):
    """Koşan bir ölçümü 'başarısız' damgalamak, sonucunu çöpe atmak olurdu. Yoklamanın yanılma yönü
    muhafazakârdır: emin olunmayan hâl DOKUNULMAZ."""
    rid = _kuyruga_yaz("measuring", pid=os.getpid())
    out = hermes_composite.reap_measuring()
    assert out["canli"] == [rid] and not out["olu"]
    assert _satir(rid)["status"] == "measuring"


def test_C14_pid_yoksa_damga_YOK_ama_sessizlik_de_yok(sandbox_state):
    """Canlılık ÖLÇÜLEMEDİĞİNDE damga basılmaz (uydurma yasağı) — ama satır görünmez de kalmaz:
    uyarı defterine düşer ve `queue_status.n_olculuyor` içinde sayılır."""
    rid = _kuyruga_yaz("measuring")            # pid alanı YOK
    out = hermes_composite.reap_measuring()
    assert out["olculemedi"] == [rid] and not out["olu"]
    assert _satir(rid)["status"] == "measuring"
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "composite_measuring_pid_yok"]
    assert olaylar and len(str(olaylar[-1].get("detail", ""))) >= 20
    assert hermes_composite.queue_status()["n_olculuyor"] == 1


def test_C14_kuru_kosum_satiri_olu_sayilmaz(sandbox_state):
    """`dry_run` satırı hiç süreç açmadı — onu "ölü süreç" diye damgalamak, olmamış bir ölçümün
    olmamış bir çöküşünü kaydetmek olurdu. Ayrı kovada raporlanır."""
    rid = _kuyruga_yaz("measuring", dry_run=True)
    out = hermes_composite.reap_measuring()
    assert out["kuru_kosum"] == [rid] and not out["olu"] and not out["olculemedi"]


def test_C14_gece_kancasi_once_yoklar_sonra_baslatir(sandbox_state):
    """Toplama, gece kancasının (spawn_pending) İLK adımıdır: yeni ölçüm başlatmadan önce eski
    ölçümlerin akıbeti kesinleşir. loop.py'ye dokunmadan kablolanmasının sebebi de bu — kanca zaten
    `spawn_pending` çağırıyor."""
    olu = _kuyruga_yaz("measuring", pid=_olu_pid())
    hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4}, bounds=config.bounds())
    out = hermes_composite.spawn_pending(limit=1, dry_run=True)
    assert out["reaped"]["olu"] == [olu]
    assert _satir(olu)["status"] == "measure_failed"
    assert out["spawned"], "yoklama yeni ölçümü engellememeli"


def test_C14_measure_failed_OKUYUCUSU_var(sandbox_state):
    """YASA 6: yeni damganın okuyucusu GÖSTERİLİR. İki tüketici: kuyruk sayacı (`n_basarisiz`) ve
    hermes kanıt paketi (`composite_queue.measure_failed`) — yani beyin, kuyruğa attığı fikrin
    ölçümünün DÜŞTÜĞÜNÜ görür. 'Sırada bekliyor' ile 'ölçüm denendi ve düştü' aynı cümle değildir."""
    rid = _kuyruga_yaz("measure_failed", neden="ölçüm süreci ÖLÜ (pid yoklaması ESRCH)")
    q = hermes_composite.queue_status()
    assert q["n_basarisiz"] == 1 and q["son_basarisiz"]["id"] == rid
    kaynak = (SRC / "hermes.py").read_text(encoding="utf-8")
    assert '"measure_failed": _q.get("n_basarisiz")' in kaynak, \
        "kanıt paketi measure_failed sayısını okumuyor — YASA 6 tüketicisi yok"


# =================================================================================================
# C16 — ARKA PLAN YANSIMASI REJİMLE SINIRLI
# =================================================================================================
@pytest.fixture
def bg_ortami(sandbox_state, monkeypatch):
    """Canlı rejim `chop`, arka plan rejimi `trend_up` — denetimde ölçülen CANLI durumun aynısı.
    Arama ve ship yolları yakalanır (hiçbir şey gerçekten koşmaz/ship etmez)."""
    store.write_json("regime.json", {"regime": "chop"})
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "propose_virgin_knob", lambda: None)
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    cagrilar: dict = {"search": [], "submit": []}
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: (cagrilar["search"].append(k)
                                         or {"status": "no_clearing_candidate", "search": {}}))
    monkeypatch.setattr(reflect, "submit",
                        lambda *a, **k: (cagrilar["submit"].append(a[0] if a else k)
                                         or {"status": "rejected_by_backtest"}))
    return cagrilar


def test_C16_bg_turu_aramayi_O_REJIME_zorlar(bg_ortami):
    """SEÇİLEN VARYANT: turu atlamak DEĞİL, aramayı bg rejimine zorlamak. `trend_up` istisnası
    (arama global koşar) YALNIZ trend_up CANLI iken meşrudur; arka plan turunda o istisna,
    canlı-dışı kanıtla düz `params`a yazma ruhsatına dönüşüyordu."""
    hermes.reflect_once(target_regime="trend_up", background=True)
    assert bg_ortami["search"], "bg turu hiç arama koşmadı"
    assert bg_ortami["search"][-1]["regime"] == "trend_up", \
        "bg turu GLOBAL koştu — canlı-dışı kanıt düz params'a ship edebilir"


def test_C16_canli_trend_up_turu_BIREBIR_ESKI_DAVRANIS(bg_ortami):
    """Canlı tur DEĞİŞMEDİ: canlı rejim trend_up iken arama global kalır (defterin ~%90'ı zaten o
    dilim). Yeni kapının canlı yolu daraltması, bulgunun kapsamını aşan bir davranış değişikliği
    olurdu."""
    hermes.reflect_once(target_regime="trend_up")
    assert bg_ortami["search"][-1]["regime"] is None


def test_C16_canli_chop_turu_BIREBIR_ESKI_DAVRANIS(bg_ortami):
    hermes.reflect_once(target_regime="chop")
    assert bg_ortami["search"][-1]["regime"] == "chop"


def test_C16_bg_turunda_GLOBAL_oneri_reddedilir(sandbox_state, bg_ortami, monkeypatch):
    """(b) bacağı: `preg is None` (@'sız = global) öneride sertifika kontrolü HİÇ devreye girmiyordu
    — LLM/bakir-düğme yolu, aramayı rejime zorlamanın etrafından dolaşan bir yan kapıydı."""
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: {"variable": "stop_loss_atr_mult", "new": 2.2, "old": 2.0,
                                 "source": "llm", "rationale": "test"})
    hermes.reflect_once(target_regime="trend_up", background=True)
    assert not bg_ortami["submit"], "bg turunda GLOBAL öneri kapıya gitti — sertifikasız global ship"
    assert bg_ortami["search"][-1]["regime"] == "trend_up", "reddedilen öneri aramaya düşmedi"
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "hermes_bg_proposal_rejected"]
    assert olaylar and len(str(olaylar[-1].get("detail", ""))) >= 20


def test_C16_bg_turunda_DOGRU_REJIM_onerisi_gecer(sandbox_state, bg_ortami, monkeypatch):
    """Kapı kör değildir: bg rejimini HEDEFLEYEN bir öneri (var@trend_up) kapıya gider. Aksi hâlde
    düzeltme, arka plan turunun akıllı-hamle yuvasını tamamen kapatırdı."""
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: {"variable": "stop_loss_atr_mult@trend_up", "new": 2.2, "old": 2.0,
                                 "source": "llm", "rationale": "test"})
    hermes.reflect_once(target_regime="trend_up", background=True)
    assert bg_ortami["submit"], "doğru rejimi hedefleyen öneri kapıya hiç gitmedi"


def test_C16_kapsanamayan_bg_turu_KOSMAZ(bg_ortami):
    """SON ÇARE ATLAMA: rejim adı geçerli değilse tur koşmaz. Alternatif "global koş" olurdu ve o,
    kapatılan deliğin ta kendisidir. Atlama sessiz de değildir — olay defterine düşer."""
    r = hermes.reflect_once(target_regime=None, background=True)
    assert r["status"] == "bg_regime_unscoped"
    assert not bg_ortami["search"], "kapsanamayan bg turu yine de arama koştu"
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "bg_reflection_skipped_unscoped"]
    assert olaylar and len(str(olaylar[-1].get("detail", ""))) >= 20


def test_C16_calisan_kanca_bayragi_TASIYOR(sandbox_state):
    """Kablonun canlı ucu: bekleme döngüsünün bg dalı `background=True` geçirmezse bütün bu kapı
    üretimde hiç devreye girmez (bulgunun kök nedeni tam olarak beyanın kablosuz kalmasıydı)."""
    kaynak = (SRC / "hermes_runtime.py").read_text(encoding="utf-8")
    assert "reflect_once(target_regime=bg, background=True)" in kaynak


# =================================================================================================
# C17 — OTURUM BAŞINA TEK RESMÎ KAYIT
# =================================================================================================
_DUZ = [(30, 0.2), (30, 0.2), (30, 0.2)]
_KENAR = [(30, 0.5), (30, 0.5), (30, 0.5)]


def _arama_stub(monkeypatch, *, cand_oos: float = 0.11, folds=None):
    """incumbent 0.10 + sabit aday. `folds=_DUZ` → hiçbir sonda kapıyı geçmez (oturum temsilcisi
    yolu), `_KENAR` → geçer (submit yolu)."""
    f = folds if folds is not None else _DUZ

    def fake_wf(params, bars, index, goal, *a, **kw):
        if int(kw.get("strategy_version", 1)) == 1:
            return wf.wf_from_scores(0.10, folds=_DUZ, holdout=0.10)
        return wf.wf_from_scores(cand_oos, folds=f, holdout=cand_oos)
    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()


def _sorgu_sayisi() -> int:
    doc = store.read_json(oos_erosion.EROSION_FILE, {}) or {}
    return sum(int((w or {}).get("queries") or 0) for w in (doc.get("windows") or {}).values())


@pytest.mark.parametrize("butce", [2, 6])
def test_C17_arama_oturumu_deftere_TEK_kayit_dusurur(sandbox_state, monkeypatch, butce):
    """ÇEKİRDEK İDDİA: resmî kayıt sayısı SONDA SAYISINDAN BAĞIMSIZDIR — 2 sondalık ve 6 sondalık
    oturum aynı tek soruyu sorar. Eski hâlde 204 sonda 204 satır + 204 sayaç artışı yazmıştı."""
    _arama_stub(monkeypatch, cand_oos=0.11, folds=_DUZ)      # hiçbiri kapıyı geçmez
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=butce)
    assert res["evaluated"] >= 2, "test kendi ön koşulunu sağlamıyor (birden çok sonda koşmalı)"
    assert _sorgu_sayisi() == 1, "aşınma sayacı sonda başına arttı — çifte ceza sürüyor"
    assert len(validation.ledger()) == 1, "doğrulama defteri sonda başına satır yazdı"
    assert res["oturum_kaydi"]["kaydedildi"] is True
    assert res["oturum_kaydi"]["k_probes"] == res["planlanan_sonda"]


def test_C17_kayit_K_YUKUNU_beyanla_tasir(sandbox_state, monkeypatch):
    """ÇİFTE CEZA BEYANI, ÖLÇÜLMÜŞ HÂLİ: oturumun tek satırı `k_probes`ı PLANLANAN sonda sayısı
    olarak taşır ve `n_trials = erosion.queries + k_probes` her yükü tam bir kez fiyatlar. Eski
    hâlde aynı K hem sayaca K kez hem beyana bir kez yazılıyordu."""
    _arama_stub(monkeypatch, cand_oos=0.11, folds=_DUZ)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=4)
    satir = validation.ledger()[-1]
    assert satir["k_probes"] == res["planlanan_sonda"]
    assert satir["erosion_queries"] == 1
    assert satir["n_trials"] == satir["erosion_queries"] + satir["k_probes"]


def test_C17_sondalar_MARJI_gorur_ama_SAYMAZ(sandbox_state):
    """AYRIM ÇİZGİSİ: kayıtsız değerlendirme SAYMAZ ama MARJI UYGULAR.

    Marjın da sessizce düşmesi kapıyı GEVŞETİRDİ — aşınmış bir pencerede sonda, kapının göremediği
    bir kolaylıktan yararlanırdı. Burada sayaç eşiğin ÜSTÜNE kurulur (aşınmış pencere taklidi) ve
    tek bir kayıtsız değerlendirme koşulur: çıta yükselmiş OLMALI, sayaç ise KIPIRDAMAMALI."""
    kaynak = (SRC / "reflect.py").read_text(encoding="utf-8")
    assert "_gate_eval(inc, cand, k_probes=total, record_erosion=False)" in kaynak
    inc = wf.wf_from_scores(0.10, folds=_DUZ, holdout=0.10)
    cand = wf.wf_from_scores(0.11, folds=_DUZ, holdout=0.11)
    # PARMAK İZİ KAPININ KENDİSİNDEN OKUNUR, YENİDEN TÜRETİLMEZ: `_gate_eval` fold sınırlarını
    # incumbent'ın işlemlerinden KESER (n-dengeli kesim) ve geometri hash'i o sınırları da kapsar —
    # testin kendi hash'ini kurması, ölçtüğünü sandığı pencereden BAŞKA bir sayacı doldurmak olurdu.
    _p0, g0, _w0 = reflect._gate_eval(inc, cand, k_probes=3, record_erosion=False)
    assert g0["margin"] == reflect.GATE_MARGIN                    # taban: sayaç henüz 0
    fp = g0["erosion"]["fingerprint"]
    for _ in range(oos_erosion.EROSION_QUERY_LIMIT + 1):
        oos_erosion.record(fp)
    once = _sorgu_sayisi()
    _p, gate, _w = reflect._gate_eval(inc, cand, k_probes=3, record_erosion=False)
    assert gate["margin"] > reflect.GATE_MARGIN, "aşınma marjı kayıtsız değerlendirmede DÜŞTÜ"
    assert gate["erosion"]["extra_margin"] == oos_erosion.EROSION_EXTRA_MARGIN
    assert _sorgu_sayisi() == once, "kayıtsız değerlendirme sayacı artırdı"
    assert not validation.ledger(), "kayıtsız değerlendirme doğrulama defterine satır yazdı"


def test_C17_ship_eden_oturum_da_TEK_kayit(sandbox_state, monkeypatch):
    """Kapıyı geçen aday çıkarsa resmî kaydı `submit` düşürür ve arama İKİNCİSİNİ yazmaz. Toplam
    yine 1: oturum başına tam bir resmî soru — ne sıfır (bedava aşınma) ne iki (aynı adayın PBO
    ızgarasında iki kopyası)."""
    _arama_stub(monkeypatch, cand_oos=0.30, folds=_KENAR)     # gerçek kenar → kapıyı geçer
    res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=1, budget=3)
    assert res["search"]["cleared"] >= 1, "test ön koşulu: en az bir aday kapıyı geçmeli"
    assert res["search"]["oturum_kaydi"] is None, "arama, submit'in yazdığı kaydı ikizledi"
    assert _sorgu_sayisi() == 1
    assert len(validation.ledger()) == 1


def test_C17_isinma_sprinti_HICBIR_resmi_kayit_dusurmez(sandbox_state, monkeypatch):
    """'Nothing ships' beyanı artık DEFTER tarafında da doğru. Isınma 12 poll'da bir koşuyor ve
    sonda başına kayıtla tek gecede `EROSION_QUERY_LIMIT=20`yi aşıp +0.01 ek marjı ömür boyu
    açıyordu — hiçbir şey ship edemeyen bir turun kapıyı KALICI olarak sıkması."""
    _arama_stub(monkeypatch, cand_oos=0.11, folds=_DUZ)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=3, record_session=False)
    assert res["evaluated"] >= 1 and res["oturum_kaydi"] is None
    assert _sorgu_sayisi() == 0 and validation.ledger() == []
    # canlı ısınma yolunun bayrağı GERÇEKTEN taşıdığı kaynaktan doğrulanır (kabloyu unutan bir
    # gelecek turda bu test düşer — davranışın kendisi tekrar sessizce açılamaz)
    kaynak = (SRC / "hermes_runtime.py").read_text(encoding="utf-8")
    assert "record_session=False" in kaynak


def test_C17_sonda_kosmayan_oturum_soru_SORMAZ(sandbox_state, monkeypatch):
    """Sıfır sonda = sorulmamış soru. Boş bir oturumu saymak, sayacı "kaç kez fonksiyon çağrıldı"ya
    çevirirdi (oos_erosion'ın kendi beyanı)."""
    _arama_stub(monkeypatch, cand_oos=0.11, folds=_DUZ)
    monkeypatch.setattr(reflect, "_ucb_rank", lambda *a, **k: [])   # hiç sonda planlanmaz
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=3)
    assert res["evaluated"] == 0 and res["oturum_kaydi"] is None
    assert _sorgu_sayisi() == 0
