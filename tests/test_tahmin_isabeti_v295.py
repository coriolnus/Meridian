"""test_tahmin_isabeti_v295.py — TAHMİN İSABETİ n=1: EŞLEŞTİRME Mİ KOPUK, TERMİNAL HİPOTEZ Mİ YOK?

FİŞ KÖKÜ. `edge_hukmu.criteria.tahmin_isabeti` canlıda `olculemedi / n=1 / sign_hits=0` diyor ve
öneri hattı bunu "tahmin↔gerçekleşen eşleştirme hattını özelleştir" diye okuyor. İki teşhis
BAMBAŞKA iştir:

  (a) EŞLEŞTİRME KOPUK  → hipotez terminale ulaşıyor ama `realized_delta` yazılmıyor: onarılacak
      bir hat var.
  (b) TERMİNAL HİPOTEZ YOK → hipotezler ship'e hiç ULAŞMIYOR (kapı/guard reddi), dolayısıyla
      gerçekleşecek bir şey yok: onarılacak hat yok, eşik/arama tarafında iş var.

Yanlış teşhis veren bir beyan, beyansızlıktan KÖTÜDÜR: (b) durumunda (a)'yı onarmaya çıkmak,
çalışan bir hattı kurcalamaktır.

CANLI ÖLÇÜM (2026-08-25, `state/hypotheses.jsonl`, 41 satır): 39 satırda `version_to` YOK
(22 rejected_by_guard, 16 rejected_by_backtest, 1 rejected_by_confirmation) — yani ship'e hiç
ulaşmamışlar; kalan 2'den H00026 ÖLÇÜLMÜŞ (predicted +0,0593 → realized −0,0364, calibration_hit
False) ve H00029 v4 tarafından ölçülemeden aşılmış. Yani n=1 (b)'dir.

BU DOSYANIN ÇİVİSİ İKİ CÜMLEDİR:
  Ç1 — Eşleştirme hattı KURGULANMIŞ bir terminal hipotez için kayıt ÜRETİR. Kum havuzunda gerçek
       `rollback.evaluate_outcomes` sürülür; hipoteze `realized_delta` yazılır ve
       `analytics.prediction_hit_rate()` n=1 sayar. Hat kopuk olsaydı bu test kırmızı olurdu.
  Ç2 — Üretemediğinde NEDENİ beyan edilir: `memory.pairing_diagnosis()` "ship yok" ile "ölçüm
       bekliyor" ile "eşleme kopuk" hâllerini ADIYLA ayırır ve hiçbir satırı sayımın dışında
       bırakmaz. Beyanın OKUYUCUSU var (YASA 6): `lessons.md` — hermes `build_context` onu her
       reflection'a enjekte eder. (Kanıt paketi DEĞİL: canlı ölçümde paket 6.183 karakter ve
       tavanı 6.200; teşhisi oraya koymak iki kanıt alanını prompt'tan düşürürdü.)

HANGİ KAPI: burada sınanan eşik `analytics.PRED_HIT_N_MIN` (=10) — bir RAPORLAMA eşiğidir,
öğrenme kapılarından DEĞİLDİR. Ne `reflect`in ship yetkilisi (0,80) ne de ön eleme (0,995) bu
sayıya karışır; ikisini karıştırmak "sistem öğrenmiyor" yanlış teşhisini üretmişti.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

from meridian import analytics, config, hermes, memory, rollback, store

REPO = pathlib.Path(__file__).resolve().parent.parent


def _trades(n, version, r, regime="trend_up"):
    return [{"id": f"T{version}{i}", "strategy_version": version, "regime": regime,
             "r_multiple": r, "pnl_dollars": r * 1000,
             "ts_open": f"2026-0{1 + (i % 6)}-{(i % 27) + 1:02d}",
             "ts_close": f"2026-0{1 + (i % 6)}-{(i % 27) + 2:02d}",
             "score": 70, "r_multiple_expected": 2.5} for i in range(n)]


def _ship(version=2, parent=1, predicted_delta=0.05):
    """v{parent} anlık görüntüsü + canlı v{version} + o sürümü sevk eden `live` hipotez."""
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    (config.HISTORY / f"v{parent:04d}.yaml").write_text(yaml.safe_dump(
        {"version": parent, "parent": None, "params": config.default_strategy()["params"]}))
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": version, "parent": parent, "params": config.default_strategy()["params"]}))
    memory.record({"id": "H00001", "version_to": version, "version_from": parent, "status": "live",
                   "variable": "entry.min_score", "predicted_delta": predicted_delta,
                   "predicted_direction": "improve_oos_score",
                   "backtest": {"incumbent_oos": 0.30}})


# ---------------------------------------------------------------------------------------------
# Ç1 — EŞLEŞTİRME HATTI KAYIT ÜRETİYOR (kurgulanmış girdiyle)
# ---------------------------------------------------------------------------------------------
def test_C1_kurgulanmis_terminal_hipotez_icin_kayit_URETILIYOR(sandbox_state):
    """Hat KOPUK DEĞİL: ship edilmiş bir hipotez min_sample'a ulaşınca tahmin↔gerçekleşen çifti
    doğar ve `prediction_hit_rate` onu SAYAR. Bu kırmızıya dönerse teşhis (a)'dır."""
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, 0.30) + _trades(n, 1, 0.30))

    assert analytics.prediction_hit_rate() == {"n": 0, "sign_hits": None, "mean_abs_err": None}, \
        "ölçüm ÖNCESİ çift olmamalı — testin başlangıç noktası yanlış"

    out = rollback.evaluate_outcomes(goal)
    assert out is not None, "değerlendirme hiç koşmadı — kurgu girdisi min_sample'ı doldurmuyor"

    h = memory.all_hypotheses()[0]
    assert h.get("realized_delta") is not None, "EŞLEŞTİRME HATTI KOPUK: gerçekleşen delta yazılmadı"
    assert h.get("calibration_hit") is not None, "kalibrasyon isabeti yazılmadı"

    ph = analytics.prediction_hit_rate()
    assert ph["n"] == 1 and ph["sign_hits"] is not None, f"çift sayılmadı: {ph}"


def test_C1b_esleme_hatti_calisirken_teshis_KOPUK_DEMEZ(sandbox_state):
    """Hat kayıt ürettikten sonra beyan 'ölçüldü' der; 'kopuk' iddiası ORTADA KALMAZ."""
    goal = config.goal()
    n = int(goal["min_sample"])
    _ship()
    store.write_jsonl("trades.jsonl", _trades(n, 2, 0.30) + _trades(n, 1, 0.30))
    rollback.evaluate_outcomes(goal)

    t = memory.pairing_diagnosis()
    assert t["kopuk"] is False and t["neden"] == "olculdu", t
    assert t["n_cift"] == 1


# ---------------------------------------------------------------------------------------------
# Ç2 — ÜRETEMEDİĞİNDE NEDEN BEYAN EDİLİYOR
# ---------------------------------------------------------------------------------------------
def test_C2_bos_defter_ship_yok_DEMEZ_bos_der(sandbox_state):
    t = memory.pairing_diagnosis()
    assert t["neden"] == "defter_bos" and t["kopuk"] is False and t["n_defter"] == 0


def test_C2a_canli_defter_sekli_SHIP_YOK_der_esleme_kopuk_DEMEZ(sandbox_state):
    """CANLI ŞEKLİN BİREBİR KURGUSU: 39 ship'siz red + 1 ölçülmüş + 1 ölçülemeden aşılmış.
    Beyanın vermesi gereken teşhis (b)'dir; (a) demek hattı boşuna kurcalatır."""
    rows = []
    for i in range(22):
        rows.append({"id": f"H{i:05d}", "status": "rejected_by_guard", "version_to": None,
                     "predicted_delta": 0.03})
    for i in range(22, 38):
        rows.append({"id": f"H{i:05d}", "status": "rejected_by_backtest", "version_to": None,
                     "predicted_delta": 0.03})
    rows.append({"id": "H00038", "status": "rejected_by_confirmation", "version_to": None,
                 "predicted_delta": 0.03})
    rows.append({"id": "H00039", "status": "superseded", "version_to": 2,
                 "predicted_delta": 0.0593, "realized_delta": -0.0364, "calibration_hit": False})
    rows.append({"id": "H00040", "status": "superseded", "version_to": 3, "predicted_delta": 0.0})
    store.write_jsonl("hypotheses.jsonl", rows)

    t = memory.pairing_diagnosis()
    assert t["n_defter"] == 41 and t["n_cift"] == 1
    assert t["n_sevk_edilmemis"] == 39, t
    assert t["n_sevk_olculmeden_kapandi"] == 1, t
    assert t["kopuk"] is False, "çalışan hat KOPUK diye damgalandı — yanlış teşhis"
    assert t["neden"] == "ship_yok", t
    # Beyan teşhisi ADIYLA söylemeli ve karşı-teşhisi ÜSTLENMEMELİ. Karşılaştırma OLDUĞU GİBİ
    # yapılır: Python'un `.lower()`ı Türkçe "İ"yi birleştirici noktalı bir çifte çevirir
    # ("DEĞİL" → "deği̇l"), yani harf-duyarsız arama burada SESSİZCE ıskalar.
    assert "ship" in t["beyan"]
    assert "kopuk DEĞİL" in t["beyan"]


def test_C2b_olcum_bekleyen_ship_SHIP_YOK_ile_karistirilmaz(sandbox_state):
    """'koşmuyor' ile 'koştu, kanıt birikiyor' ayrı cümlelerdir (bu deponun 1. dersi)."""
    store.write_jsonl("hypotheses.jsonl", [
        {"id": "H00001", "status": "rejected_by_guard", "version_to": None, "predicted_delta": 0.03},
        {"id": "H00002", "status": "live", "version_to": 2, "predicted_delta": 0.05}])
    t = memory.pairing_diagnosis()
    assert t["neden"] == "olcum_bekliyor" and t["kopuk"] is False, t
    assert t["n_sevk_acik"] == 1 and t["n_sevk_olculmeden_kapandi"] == 0


def test_C2c_GERCEKTEN_kopuk_sekil_kopuk_DER(sandbox_state):
    """Tek meşru 'kopuk' kanıtı: gerçekleşen yazılmış ama eşleşecek tahmin YOK. Bu şekilde beyan
    (a)'yı söylemeli — aksi hâlde 'kopuk' etiketi hiçbir zaman ateşlemeyen ölü bir dal olurdu."""
    store.write_jsonl("hypotheses.jsonl", [
        {"id": "H00001", "status": "promoted", "version_to": 2, "realized_delta": 0.04},
        {"id": "H00002", "status": "rejected_by_guard", "version_to": None, "predicted_delta": 0.03}])
    t = memory.pairing_diagnosis()
    assert t["kopuk"] is True and t["neden"] == "esleme_kopuk", t
    assert t["n_gerceklesen_tahminsiz"] == 1


def test_C2d_hicbir_satir_sayimin_DISINDA_kalmaz(sandbox_state):
    """Sessiz sınıflandırma kaybı, sayının kendisini uydurma yapar."""
    store.write_jsonl("hypotheses.jsonl", [
        {"id": "H00001", "status": "rejected_by_guard", "version_to": None, "predicted_delta": 0.03},
        {"id": "H00002", "status": "live", "version_to": 2, "predicted_delta": 0.05},
        {"id": "H00003", "status": "superseded", "version_to": 3, "predicted_delta": 0.01},
        {"id": "H00004", "status": "promoted", "version_to": 4, "predicted_delta": 0.02,
         "realized_delta": 0.03},
        {"id": "H00005", "status": "promoted", "version_to": 5, "realized_delta": 0.03},
        {"id": "H00006", "status": "proposed", "version_to": None}])
    t = memory.pairing_diagnosis()
    toplam = (t["n_cift"] + t["n_sevk_edilmemis"] + t["n_sevk_acik"]
              + t["n_sevk_olculmeden_kapandi"] + t["n_gerceklesen_tahminsiz"])
    assert toplam == t["n_defter"] == 6, t


def test_C2e_biçimsiz_satir_cift_SAYILMAZ(sandbox_state):
    """`prediction_hit_rate` biçimsiz satırı atlıyor (işaretli sessiz-yutma). Teşhis de aynı
    popülasyon yasasını uygulamalı — yoksa iki sayı ayrışır ve hangisinin doğru olduğu bilinmez."""
    store.write_jsonl("hypotheses.jsonl", [
        {"id": "H00001", "status": "promoted", "version_to": 2,
         "predicted_delta": "muz", "realized_delta": 0.03}])
    t = memory.pairing_diagnosis()
    assert t["n_cift"] == analytics.prediction_hit_rate()["n"] == 0, t


# ---------------------------------------------------------------------------------------------
# YASA 6 — BEYANIN OKUYUCUSU
# ---------------------------------------------------------------------------------------------
def _ship_yok_defteri():
    store.write_jsonl("hypotheses.jsonl", [
        {"id": f"H{i:05d}", "status": "rejected_by_guard", "version_to": None,
         "variable": "entry.min_score", "new": 70 + i, "predicted_delta": 0.03,
         "predicted_direction": "improve_oos_score"} for i in range(5)])


def test_YASA6_beyanin_okuyucusu_lessons_md_uzerinden_hermes(sandbox_state):
    """Beyan üretilip kimseye ulaşmazsa yazılmamış sayılır. Okuyucu: hipotezi ÖNEREN taraf.
    Taşıyıcı `lessons.md` — hermes `build_context` onu HER reflection'a enjekte eder."""
    _ship_yok_defteri()
    text = memory.distill_lessons()
    assert "why the pair count is what it is" in text, "beyan lessons.md'ye hiç yazılmadı"
    assert memory.pairing_diagnosis()["beyan"] in text
    assert "verdict=ship_yok" in text

    ctx = json.loads(hermes.build_context())
    assert "why the pair count is what it is" in ctx["lessons_md"], \
        "beyanın OKUYUCUSU yok (YASA 6) — reflection bağlamına girmiyor"
    assert "ship" in ctx["lessons_md"]


def test_YASA6b_bos_defterde_beyan_YAZILMAZ(sandbox_state):
    """Boş defterde "defter boş" satırı teknik olarak doğru ama bilgi taşımaz ve "no lessons yet"
    hükmünü yerinden ederdi (uydurma yasağının uygulanması)."""
    text = memory.distill_lessons()
    assert "why the pair count is what it is" not in text
    assert "No lessons yet" in text


def test_YASA6c_lessons_md_DETERMINISTIK_kalir(sandbox_state):
    """`distill_lessons` iki kez koşunca AYNI metni vermeli — teşhis satırı damga/zaman taşımaz."""
    _ship_yok_defteri()
    assert memory.distill_lessons() == memory.distill_lessons()


def test_YASA6d_beyan_hermes_ders_tavanina_sigar(sandbox_state):
    """Teşhis lessons.md'ye kondu ÇÜNKÜ kanıt paketinde yeri yoktu (canlı ölçüm: paket 6.183 /
    tavan 6.200). Aynı hatayı burada tekrarlamayalım: derslerin tavanı da BEYAN edilmiş bir
    bütçedir ve teşhis onu tek başına doldurmamalı."""
    _ship_yok_defteri()
    assert len(memory.distill_lessons()) < hermes.LESSONS_CAP


# ---------------------------------------------------------------------------------------------
# TEŞHİSİN KENDİSİ: canlı defter (a) DEĞİL (b)
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("_", [0])
def test_canli_defter_teshisi_SHIP_YOK(_):
    """Canlı `state/hypotheses.jsonl` üzerinde SALT-OKUR teşhis. Dosya yoksa test ATLANIR —
    ölçemediğimizi 'geçti' diye yazmak uydurma olurdu."""
    p = REPO / "state" / "hypotheses.jsonl"
    if not p.exists():
        pytest.skip("canlı defter yok — teşhis ölçülemedi (uydurma yok)")
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not rows:
        pytest.skip("canlı defter boş")
    sevksiz = sum(1 for r in rows if r.get("version_to") is None)
    cift = sum(1 for r in rows
               if r.get("predicted_delta") is not None and r.get("realized_delta") is not None)
    kopuk = sum(1 for r in rows
                if r.get("realized_delta") is not None and r.get("predicted_delta") is None)
    assert kopuk == 0, (f"canlı defterde eşleşmemiş gerçekleşen var ({kopuk}) — teşhis (a): "
                        f"EŞLEŞTİRME KOPUK")
    assert sevksiz > cift, ("canlı defterde ship'siz satır sayısı çiftlerden fazla DEĞİL — bu "
                            "dosyanın dayandığı ölçüm bayatlamış, teşhisi yeniden ölç")
