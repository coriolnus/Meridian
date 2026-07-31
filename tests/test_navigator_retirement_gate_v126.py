"""test_navigator_retirement_gate_v126.py — navigatör emeklilik kapısı (2026-07-30 boşluk kapatma).

2026-07-30 denetimi 68 klasörü 31 canlıya indirdi ama navigatörün katalog metadata'sı
(assets/metadata_snapshot.json) denetim ÖNCESİNDEN kalmaydı ve üretildiği SSoT
(skills-index.yaml + workflows/) bu depoya hiç taşınmadı — yani snapshot yeniden üretilemez,
elle de düzeltilemez (parite değişmezi). Çözüm: öneri anında uygulanan EMEKLİLİK KAPISI.
Gerçekler kayıt defterinden (Claude Code, canlı) ya da paketlenmiş
assets/retirement_digest.json'dan (Web App, paket anı) gelir; ikisi de yoksa kapı dürüstçe
"çalışmadım" der ve çıktı doğrulama uyarısı taşır.

Bu dosya kapının geri dönmediğini kanıtlar:
  R1 sürüklenme bekçisi — digest, kayıt defterinin emeklilik gerçekleriyle bayt-bayt aynı
     (build_retirement_digest.py --check'in CI'daki karşılığı; pre-commit bu depoda yok)
  R2 eyleme dönük hiçbir alanda arşiv adı yok — tüm persona yelpazesi taranır
  R3 arşivlenmiş birincil workflow dürüst boşluğa dönüşür (uydurma öneri YOK)
  R4 arşivlenmiş ikincil, ADIYLA gerekçelendirilerek düşer — sessiz kayıp yok
  R5 ortam paritesi — kayıt defteri ve digest aynı gerçekleri verdiğinde öneri yalnız
     beyan edilen retirement.source alanında ayrışır
  R6 dürüst bozulma — gerçekler yoksa filtre YOKTUR (bugünkü davranış) + doğrulama uyarısı
  R7 PROTECTED beşlisi kapıdan etkilenmez
  R8 kapı saf ve idempotent; çıktı baytları kararlı
  R9 CLI ucu — gerçek depo kökünden koşunca kaynak "registry" ve stderr bunu söyler
"""
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
NAV = REPO / "skills" / "trading-skills-navigator"
DIGEST = NAV / "assets" / "retirement_digest.json"
PROTECTED = frozenset({"pre-trade-discipline-gate", "drawdown-circuit-breaker",
                       "data-quality-checker", "position-sizer", "portfolio-manager"})

# Persona yelpazesi: her satır (sorgu, beklenen_birincil | None) — None = dürüst boşluk.
QUERY_BATTERY = (
    ("I want to short the market", None),                                  # persona boşluğu
    ("I want to backtest a strategy idea", None),                          # persona boşluğu
    ("what works with no api keys", "market-regime-daily"),
    ("I want to swing trade only when the market is favorable", "market-regime-daily"),
    ("can I take risk today", "market-regime-daily"),
    ("separate my long-term holdings from short-term risk", "market-regime-daily"),
    ("review my dividend holdings", None),                                 # arşiv boşluğu
    ("find me breakout trade setups", None),                               # arşiv boşluğu
    ("log my trade postmortem", None),                                     # arşiv boşluğu
    ("monthly performance review", None),                                  # arşiv boşluğu
    ("where do I start", "market-regime-daily"),
    ("tamamen alakasız bir soru", "market-regime-daily"),                  # eşleşmeyen varsayılan
)


def _load(name: str):
    path = NAV / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_nav_{name}_v126", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rec():
    return _load("recommend")


@pytest.fixture(scope="module")
def digest_builder():
    return _load("build_retirement_digest")


@pytest.fixture(scope="module")
def raw_metadata(rec):
    metadata, source = rec.resolve_metadata(REPO)
    assert source == "snapshot", "bu depoda SSoT yok — snapshot yolu beklenir"
    return metadata


@pytest.fixture(scope="module")
def facts(rec):
    f = rec.load_retirement(REPO)
    assert f.source == "registry", "canlı kayıt defteri okunamadı"
    return f


def _registry_retired() -> dict:
    reg = json.loads((REPO / "state" / "skills_registry.json").read_text())["skills"]
    return {n: i for n, i in reg.items() if i.get("retired")}


# ---------- R1: sürüklenme bekçisi (digest ↔ kayıt defteri) ----------
def test_r1_digest_matches_live_registry_byte_for_byte(digest_builder):
    assert DIGEST.is_file(), "paketlenecek digest yok — build_retirement_digest.py koşulmamış"
    regenerated = digest_builder.build_digest_text(REPO)
    assert DIGEST.read_text(encoding="utf-8") == regenerated, (
        "retirement_digest.json kayıt defterinden sürüklenmiş — "
        "python3 skills/trading-skills-navigator/scripts/build_retirement_digest.py koş"
    )


def test_r1b_digest_carries_every_retired_entry_and_merge_target():
    digest = json.loads(DIGEST.read_text())["retired"]
    registry = _registry_retired()
    assert set(digest) == set(registry)
    for name, info in registry.items():
        assert digest[name]["merged_into"] == (info.get("merged_into") or None), name


# ---------- R2: eyleme dönük alanlarda arşiv adı YOK ----------
def _actionable_names(result: dict) -> set[str]:
    """Kullanıcıya 'kur/koş' diye sunulan her ad — gerekçe/not satırları HARİÇ
    (oralar arşivi ADIYLA anmak zorunda, dürüstlük kanalı orası)."""
    names: set[str] = set()
    sb = result["setup_bundle"]
    names |= set(sb["required"]) | set(sb["recommended"]) | set(sb["optional"])
    names |= {s["id"] for s in result["suggested_skills"]}
    for wf in [result["primary_workflow"], *result["secondary_workflows"]]:
        if wf is None:
            continue
        names.add(wf["id"])
        names |= set(wf["required_skills"]) | set(wf["optional_skills"])
        names |= set(wf["prerequisite_workflows"])
    man = result["skillset"]["manifest"]
    if man is not None:
        names |= set(man["required_skills"]) | set(man["recommended_skills"])
        names |= set(man["optional_skills"]) | set(man["related_workflows"])
    return names


@pytest.mark.parametrize("query,expected_primary", QUERY_BATTERY)
def test_r2_no_archived_name_in_actionable_fields(rec, raw_metadata, facts,
                                                  query, expected_primary):
    _, gate = rec.apply_retirement_gate(raw_metadata, facts)
    archived = set(facts.retired) | set(gate.archived_workflows)
    result = rec.recommend(query, raw_metadata, retirement=facts)
    leaked = _actionable_names(result) & archived
    assert not leaked, f"{query!r}: arşiv adı eyleme dönük alanda: {sorted(leaked)}"
    assert result["retirement"] == {"as_of": facts.as_of, "source": "registry"}
    pw = result["primary_workflow"]
    assert (pw["id"] if pw else None) == expected_primary, f"{query!r} yönlendirmesi kaydı"


# ---------- R3: arşivlenmiş birincil → dürüst boşluk ----------
def test_r3_archived_primary_becomes_an_honest_gap(rec, raw_metadata, facts):
    result = rec.recommend("log my trade postmortem", raw_metadata, retirement=facts)
    assert result["honest_gap"] is True
    assert result["primary_workflow"] is None
    assert result["no_api_path"] is None
    assert "trade-memory-loop" in (result["note"] or ""), "not arşivlenen workflow'u adlandırmalı"
    suggested = {s["id"] for s in result["suggested_skills"]}
    assert suggested == {"weekly-performance-digest"}, (
        "trade-memory kategorisinin tek canlı skill'i weekly-performance-digest olmalı")
    assert any("trade-memory-loop" in r and "_emekli" in r
               for r in result["rationale"]), "gerekçe arşiv yolunu adıyla anmalı"


def test_r3b_dividend_gap_suggests_only_the_live_portfolio_manager(rec, raw_metadata, facts):
    result = rec.recommend("review my dividend holdings", raw_metadata, retirement=facts)
    assert result["honest_gap"] is True
    assert {s["id"] for s in result["suggested_skills"]} == {"portfolio-manager"}
    assert result["setup_bundle"]["required"] == ["portfolio-manager"]


# ---------- R4: arşivlenmiş ikincil adıyla düşer ----------
def test_r4_archived_secondary_is_excluded_and_named(rec, raw_metadata, facts):
    result = rec.recommend("I want to swing trade only when the market is favorable",
                           raw_metadata, retirement=facts)
    assert result["primary_workflow"]["id"] == "market-regime-daily"
    assert result["secondary_workflows"] == []
    assert any("swing-opportunity-daily" in r and "excluded" in r
               for r in result["rationale"]), "ikincil sessizce kaybolmuş — gerekçe satırı yok"


# ---------- R5: ortam paritesi (registry ↔ bundled) ----------
def test_r5_registry_and_bundled_facts_agree_modulo_declared_source(rec, raw_metadata,
                                                                    facts, tmp_path):
    bundled = rec.load_retirement(tmp_path, digest_path=DIGEST)   # state/ yok → digest yolu
    assert bundled.source == "bundled"
    assert bundled.as_of == facts.as_of
    assert bundled.retired == facts.retired
    for query, _ in QUERY_BATTERY:
        a = rec.recommend(query, raw_metadata, retirement=facts)
        b = rec.recommend(query, raw_metadata, retirement=bundled)
        assert a["retirement"]["source"] == "registry"
        assert b["retirement"]["source"] == "bundled"
        a["retirement"] = b["retirement"] = None
        assert rec.dumps(a) == rec.dumps(b), f"{query!r}: ortamlar kaynak beyanı dışında ayrıştı"


# ---------- R6: gerçekler yoksa dürüst bozulma ----------
def test_r6_unavailable_facts_disable_the_gate_and_say_so(rec, raw_metadata, tmp_path):
    none = rec.load_retirement(tmp_path, digest_path=tmp_path / "yok.json")
    assert none.source == "unavailable" and none.retired == {}
    result = rec.recommend("log my trade postmortem", raw_metadata, retirement=none)
    # Filtre YOK: bugünkü (kapı öncesi) davranış aynen — arşivlenmiş workflow hâlâ önerilir…
    assert result["primary_workflow"]["id"] == "trade-memory-loop"
    assert "trader-memory-core" in result["setup_bundle"]["required"]
    # …ama çıktı bunu saklamaz: kaynak beyanı + doğrulama uyarısı taşır.
    assert result["retirement"] == {"as_of": None, "source": "unavailable"}
    assert any("verify against skills/" in r for r in result["rationale"])
    # retirement=None (eski çağıran) da aynı dürüst bozulmayı verir.
    legacy = rec.recommend("log my trade postmortem", raw_metadata)
    assert legacy["retirement"]["source"] == "unavailable"


# ---------- R7: PROTECTED beşlisi ----------
def test_r7_protected_five_survive_the_gate(rec, raw_metadata, facts):
    gated, _ = rec.apply_retirement_gate(raw_metadata, facts)
    live_ids = {s["id"] for s in gated["skills"]}
    assert PROTECTED <= live_ids, "PROTECTED skill kapıya takıldı"
    result = rec.recommend("find me breakout trade setups", raw_metadata, retirement=facts)
    assert {"drawdown-circuit-breaker", "position-sizer",
            "pre-trade-discipline-gate"} <= set(result["setup_bundle"]["required"])


# ---------- R8: saflık, idempotens, kararlı baytlar ----------
def test_r8_gate_is_pure_idempotent_and_output_is_stable(rec, raw_metadata, facts):
    before = copy.deepcopy(raw_metadata)
    gated1, _ = rec.apply_retirement_gate(raw_metadata, facts)
    assert raw_metadata == before, "kapı girdisini yerinde değiştirmiş (saflık ihlali)"
    gated2, gate2 = rec.apply_retirement_gate(gated1, facts)
    assert gated2 == gated1, "kapı idempotent değil"
    assert gate2.archived_workflows == {}, "ikinci geçişte arşivlenecek workflow kalmamalı"
    q = "what works with no api keys"
    assert (rec.dumps(rec.recommend(q, raw_metadata, retirement=facts))
            == rec.dumps(rec.recommend(q, raw_metadata, retirement=facts)))


# ---------- R9: CLI ucu ----------
def test_r9_cli_reports_registry_source_from_repo_root(rec):
    proc = subprocess.run(
        [sys.executable, str(NAV / "scripts" / "recommend.py"),
         "--query", "where do I start", "--format", "json",
         "--project-root", str(REPO)],
        capture_output=True, text=True, cwd=str(REPO), timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "retirement facts: registry" in proc.stderr
    result = json.loads(proc.stdout)
    assert result["retirement"]["source"] == "registry"
    assert rec.dumps(result) == proc.stdout, "CLI çıktısı kanonik dumps ile aynı olmalı"


def test_r9b_digest_builder_check_passes(digest_builder):
    assert digest_builder.main(["--project-root", str(REPO), "--check"]) == 0
