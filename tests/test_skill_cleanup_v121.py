"""test_skill_cleanup_v121.py — 2026-07-30 skill temizlik turu (ROADMAP §3.2 kalemi).

Denetim 68 skill klasörünü inceledi: 22 EMEKLİ, 16 BİRLEŞTİR, 8 ÖLÇÜMLE-AKTİVE, 22 OLDUĞU-GİBİ.
Temizliğin asıl amacı bir SAYIM değil DÜRÜSTLÜK: zincirde durup hiç koşmayan skill her koşuda
`skills_declared_not_run` listesine yazılıyor ve panoda "çalışan sistem" izlenimi üretiyordu.

Bu dosya uygulamanın geri dönmediğini kanıtlar:
  C1 arşiv gerçekten arşiv — klasör `skills/_emekli/` altında, canlı yolda değil, SİLİNMEMİŞ
  C2 kayıt dürüstlüğü — emekli/birleştirilen kayıt kapalı, zincirsiz, gerekçeli
  C3 anahtar-kapısı emekliyi DİRİLTMEZ — `reconcile_enablement` `retired` kaydı atlar
  C4 zincir dürüstlüğü — arşivlenen ad hiçbir PIPELINES zincirinde yok; zincirdeki her ad canlı
  C5 katalog — `_emekli` katalog taramasına girmez, etkin skill'in klasörü vardır
  C6 koruma — PROTECTED beşlisi ve Hermes/skill_evolve ön-yükleme adları canlı ve dokunulmamış
  C7 bayat damga — dürüstlük düzeltmesi (2026-07-15T10:29) öncesi `last_run` kalmadı; uydurma yeni yok
  C8 birleştirme belgesi — her kaynağın çekirdek sezgisi hedef dosyada bölüm olarak duruyor
  C9 ölçümle-aktive — 8 adayın `aktivasyon_kosulu` alanı var ve boş değil
  C10 sunum dürüstlüğü — sunum katmanında sabit skill sayısı yok; landing sayıyı canlı uçtan
      okur ve uç sayıyı kayıt defterinden HESAPLAR (2026-07-30 kopya düzeltmesi)
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from meridian import skills as sk, store

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
ARCHIVE = SKILLS_DIR / "_emekli"

# --- denetim hükümleri (tablo: 2026-07-30 skill denetimi) ---------------------------------------
RETIRED = (
    "cot-contrarian-detector", "dividend-growth-pullback-screener", "downtrend-duration-analyzer",
    "edge-signal-aggregator", "kanchi-dividend-review-monitor", "kanchi-dividend-sop",
    "kanchi-dividend-us-tax-accounting", "news-reaction-failure-analyzer", "options-strategy-advisor",
    "pair-trade-screener", "scenario-analyzer", "sector-analyst", "shadow", "skill-designer",
    "skill-idea-miner", "skill-integration-tester", "stanley-druckenmiller-investment",
    "stockbee-20pct-study", "technical-analyst", "trader-memory-core", "us-stock-analysis",
    "value-dividend-screener",
)
# kaynak → çekirdek sezgisinin katlandığı hedef (kayıt defterindeki `merged_into` değeri).
# 14'ü canlı bir skill; breakout-trade-planner'ın hedefi bir BELGE, çünkü doğal hedefi
# (position-sizer) PROTECTED beşlisinde ve bu turda korumalı dosyalara dokunulmadı.
MERGED = {
    "breadth-chart-analyst": "market-breadth-analyzer",
    "breakout-trade-planner": "docs/G3B-CIKIS-REFORMU-NOTLARI.md",
    "dual-axis-skill-reviewer": "trading-skills-navigator",
    "earnings-trade-analyzer": "pead-screener",
    "edge-candidate-agent": "edge-pipeline-orchestrator",
    "edge-concept-synthesizer": "edge-pipeline-orchestrator",
    "edge-hint-extractor": "edge-pipeline-orchestrator",
    "edge-strategy-designer": "edge-pipeline-orchestrator",
    "trade-hypothesis-ideator": "edge-pipeline-orchestrator",
    "ftd-detector": "macro-regime-detector",
    "market-news-analyst": "market-environment-analysis",
    "signal-postmortem": "backtest-expert",
    "stockbee-setup-fluency-trainer": "weekly-performance-digest",
    "trade-performance-coach": "weekly-performance-digest",
    "us-market-bubble-detector": "market-top-detector",
}
# katlanan bölümün aranacağı dosya
MERGE_DOC = {src: (tgt if tgt.endswith(".md") else f"skills/{tgt}/SKILL.md")
             for src, tgt in MERGED.items()}
ARCHIVED = set(RETIRED) | set(MERGED)
MEASURE_THEN_ACTIVATE = ("canslim-screener", "economic-calendar-fetcher", "edge-pipeline-orchestrator",
                         "ibd-distribution-day-monitor", "parabolic-short-trade-planner",
                         "strategy-pivot-designer", "theme-detector", "uptrend-analyzer")
RETIRE_REASON = "programa hizmet etmiyor (2026-07-30 denetimi)"
HONESTY_FIX_TS = "2026-07-15T10:29"      # pipeline_runs dürüst-ayrım düzeltmesi


def live_registry() -> dict:
    """GERÇEK kayıt defteri (sandbox değil): temizliğin depoda kalıcı olduğunu doğrularız."""
    return json.loads((REPO / "state" / "skills_registry.json").read_text())["skills"]


def _key_gated(info: dict) -> bool:
    return info.get("fmp") == "req" or info.get("alpaca") == "req"


# ---------- C1: arşiv gerçekten arşiv (silme YOK) ----------
@pytest.mark.parametrize("name", sorted(ARCHIVED))
def test_c1_archived_folder_moved_not_deleted(name):
    assert (ARCHIVE / name).is_dir(), f"{name} arşivde yok — taşıma yerine SİLİNMİŞ olabilir"
    assert not (SKILLS_DIR / name).exists(), f"{name} hâlâ canlı skill yolunda"


def test_c1b_archive_has_an_index_and_live_count_matches():
    readme = (ARCHIVE / "README.md").read_text()
    assert "geri" in readme.lower(), "arşiv README'si geri-getirme yolunu anlatmıyor"
    live = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")}
    assert live.isdisjoint(ARCHIVED)
    assert len(live) == 31, f"canlı skill sayısı 31 değil: {len(live)}"
    for d in live:
        assert (SKILLS_DIR / d / "SKILL.md").exists(), f"{d} klasöründe SKILL.md yok"


# ---------- C2: kayıt dürüstlüğü ----------
def test_c2_archived_registry_entries_are_disabled_unchained_and_reasoned():
    reg = live_registry()
    for name in sorted(ARCHIVED):
        if name == "shadow":
            assert name not in reg, "shadow boş klasör artığıydı; kayıt girdisi uydurulmamalı"
            continue
        info = reg[name]                                   # kayıt SİLİNMEZ: dürüst envanter + geri dönüş
        assert info.get("retired") is True, f"{name}: retired damgası yok"
        assert info.get("retired_folder") == f"skills/_emekli/{name}"
        assert info.get("pipeline") is None, f"{name}: emekli ama hâlâ boru hattı beyan ediyor"
        assert info.get("enabled") is False, f"{name}: hâlâ enabled"
        assert info.get("mode") == "disabled", f"{name}: mode={info.get('mode')}"
        expected = (f"birleştirildi → {MERGED[name]}" if name in MERGED else RETIRE_REASON)
        assert info["reason"] == expected, f"{name}: gerekçe {info['reason']!r}"
        if name in MERGED:
            assert info.get("merged_into") == MERGED[name]


def test_c2b_merged_entries_name_their_target():
    reg = live_registry()
    for name, target in MERGED.items():
        assert reg[name].get("merged_into") == target, f"{name}: hedef kaydı yok"


def test_c2c_chain_contradictions_are_cleared_for_survivors():
    """Kayıt bir boru hattı beyan edip skills.py zincirinde olmamak = kayıt-kod çelişkisi."""
    reg = live_registry()
    chained = {n for chain in sk.PIPELINES.values() for n in chain}
    for name, info in reg.items():
        if info.get("pipeline"):
            assert name in chained, f"{name}: pipeline={info['pipeline']} ama zincirde yok"


# ---------- C3: anahtar-kapısı emekliyi diriltmez ----------
def test_c3_reconcile_never_resurrects_a_retired_skill(sandbox_state, monkeypatch):
    store.write_json(sk.REGISTRY, {"skills": {
        "emekli-anahtarli": {"enabled": False, "mode": "disabled", "reason": RETIRE_REASON,
                             "retired": True, "fmp": "req", "alpaca": "-", "style_active": True},
        "canli-anahtarli": {"enabled": False, "mode": "disabled", "reason": "FMP_API_KEY yok",
                            "fmp": "req", "alpaca": "-", "style_active": True},
    }})
    from meridian.adapters import fmp, alpaca
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    sk.reconcile_enablement()
    reg = sk.registry()["skills"]
    assert reg["emekli-anahtarli"]["enabled"] is False, "anahtar gelince emekli skill dirildi"
    assert reg["emekli-anahtarli"]["reason"] == RETIRE_REASON, "denetim gerekçesi ezildi"
    assert reg["canli-anahtarli"]["enabled"] is True, "guard normal anahtar-kapısını da kapatmış"


def test_c3b_live_registry_has_no_enabled_retired_entry():
    assert [n for n, i in live_registry().items() if i.get("retired") and i.get("enabled")] == []


def test_c3c_archived_entries_are_outside_the_key_gate_with_provenance():
    """CANLI SÜREÇ ESKİ KODU KOŞUYOR (restart yasak) — o sürümde `retired` muafiyeti yok ve
    fmp='req' + anahtar mevcut gördüğü arşiv kaydını yeniden ENABLED yapıyordu (2026-07-30'da
    ftd-detector ve news-reaction-failure-analyzer'da tam bu oldu). Arşivlenmiş skill koşmadığı
    için anahtar sorusu onun için tanımsız: kapı adaylığından çıkarıldı, özgün gereksinim
    `retired_requires`ta AYNEN saklandı. Yani temizlik restart beklemeden ayakta kalır."""
    for name, info in live_registry().items():
        if not info.get("retired"):
            continue
        assert not _key_gated(info), f"{name}: arşivlenmiş ama hâlâ anahtar-kapısı adayı"
        req = info.get("retired_requires")
        if req:                                  # gereksinim sıfırlanmışsa özgün değer saklanmalı
            assert set(req) <= {"fmp", "alpaca"} and all(v == "req" for v in req.values())
            assert info.get("denetim_notu"), f"{name}: muafiyet gerekçesiz"


# ---------- C4: zincir dürüstlüğü ----------
def test_c4_no_archived_skill_remains_in_a_pipeline_chain():
    for pipeline, chain in sk.PIPELINES.items():
        leaked = sorted(set(chain) & ARCHIVED)
        assert not leaked, f"{pipeline} arşivlenen skill'i hâlâ zincirde tutuyor: {leaked}"


def test_c4b_every_chained_skill_is_live_and_registered():
    reg = live_registry()
    for pipeline, chain in sk.PIPELINES.items():
        for name in chain:
            assert (SKILLS_DIR / name / "SKILL.md").exists(), f"{pipeline}: {name} klasörü yok"
            assert name in reg, f"{pipeline}: {name} kayıtlı değil"


# ---------- C5: katalog taraması ----------
def test_c5_catalog_scan_skips_the_archive(monkeypatch):
    monkeypatch.setattr(sk, "_DESC_CACHE", None)
    descs = sk._skill_descriptions()
    assert not [n for n in descs if n.startswith("_")], "arşiv dizini katalogda skill gibi görünüyor"
    assert descs.keys().isdisjoint(ARCHIVED), "arşivlenen skill katalog taramasına giriyor"
    assert descs.get("vcp-screener"), "canlı skill'in açıklaması kayboldu"


def test_c5b_enabled_skills_all_have_a_live_folder():
    for name, info in live_registry().items():
        if info.get("enabled"):
            assert (SKILLS_DIR / name / "SKILL.md").exists(), f"{name} etkin ama klasörü arşivde/yok"


# ---------- C6: koruma katmanı ve ön-yükleme adları ----------
def test_c6_protected_five_untouched():
    reg = live_registry()
    assert sk.PROTECTED == frozenset({"pre-trade-discipline-gate", "drawdown-circuit-breaker",
                                      "data-quality-checker", "position-sizer", "portfolio-manager"})
    for name in sk.PROTECTED:
        assert (SKILLS_DIR / name / "SKILL.md").exists(), f"PROTECTED {name} klasörü taşınmış"
        info = reg[name]
        assert info.get("enabled") is True and not info.get("retired"), f"PROTECTED {name} kapatılmış"


def test_c6b_hermes_and_skill_evolve_preloads_point_at_live_skills():
    """Ön-yükleme listeleri arşive işaret ederse beyin bağlamı sessizce boşalır."""
    import inspect
    from meridian import hermes, skill_evolve
    reg = live_registry()
    names = set(hermes.REVIEW_SKILLS) | set(skill_evolve.CORE_NEVER)
    src = inspect.getsource(hermes._skill_preload)
    names |= {q for q in re.findall(r'"([a-z][a-z0-9-]{4,})"', src) if q in reg}
    assert {"pre-trade-discipline-gate", "position-sizer", "backtest-expert"} <= names, \
        "çekirdek üçlü ön-yükleme taramasında bulunamadı — test kör kalmış olabilir"
    for name in sorted(names):
        assert name not in ARCHIVED, f"ön-yükleme arşivlenmiş skill'i istiyor: {name}"
        assert (SKILLS_DIR / name / "SKILL.md").exists(), f"ön-yükleme adı canlı değil: {name}"


def test_c6c_engine_implemented_set_is_all_live():
    for name in sk.ENGINE_IMPLEMENTED:
        assert name not in ARCHIVED
        assert (SKILLS_DIR / name / "SKILL.md").exists(), f"motor-uygulanmış {name} klasörü yok"


# ---------- C7: bayat damga temizliği (uydurma damga YASAK) ----------
def test_c7_no_stale_run_stamps_survive():
    for name, info in live_registry().items():
        lr = info.get("last_run")
        if lr:
            assert str(lr) > HONESTY_FIX_TS, f"{name}: dürüstlük düzeltmesi öncesi bayat damga ({lr})"


def test_c7b_archived_skills_have_no_run_stamp_and_keep_provenance():
    for name, info in live_registry().items():
        if not info.get("retired"):
            continue
        assert info.get("last_run") in (None, ""), f"{name}: emekli ama koşu damgası var"
        assert info.get("last_artifact") in (None, ""), f"{name}: emekli ama artefakt damgası var"


def test_c7c_cleared_stamp_is_recorded_not_silently_dropped():
    reg = live_registry()
    cleared = [n for n, i in reg.items() if i.get("stale_last_run_cleared")]
    assert cleared, "bayat damgalar silindi ama ne silindiği kayda geçmemiş"
    for name in cleared:
        assert str(reg[name]["stale_last_run_cleared"]) < HONESTY_FIX_TS


# ---------- C8: birleştirme belgesi ----------
@pytest.mark.parametrize("source,doc", sorted(MERGE_DOC.items()))
def test_c8_merge_target_documents_the_folded_skill(source, doc):
    text = (REPO / doc).read_text()
    assert source in text, f"{doc} katlanan {source} sezgisini belgelemiyor"
    marker = "Folded in" if doc.startswith("skills/") else "Katlanan sezgiler"
    assert marker in text, f"{doc} birleştirme bölümü başlığı taşımıyor"
    assert "_emekli" in text, f"{doc} arşiv yolunu söylemiyor — okuyucu kaynağı bulamaz"


def test_c8b_orchestrator_stage_scripts_still_resolve():
    """edge-* aşama script'leri arşive taşındı; orchestrator onları hâlâ bulmalı."""
    import importlib.util
    import sys
    path = SKILLS_DIR / "edge-pipeline-orchestrator" / "scripts" / "orchestrate_edge_pipeline.py"
    spec = importlib.util.spec_from_file_location("_orc_v121", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_orc_v121"] = mod
    try:
        spec.loader.exec_module(mod)
        for stage, script in mod.SCRIPT_PATHS.items():
            assert pathlib.Path(script).exists(), f"{stage} aşama script'i çözülemedi: {script}"
    finally:
        sys.modules.pop("_orc_v121", None)


# ---------- C9: ölçümle-aktive adayları ----------
@pytest.mark.parametrize("name", MEASURE_THEN_ACTIVATE)
def test_c9_measure_then_activate_carries_its_condition(name):
    info = live_registry()[name]
    cond = info.get("aktivasyon_kosulu")
    assert cond and len(cond) > 40, f"{name}: aktivasyon koşulu yok/boş"
    assert not info.get("retired"), f"{name}: ölçümle-aktive adayı emekliye alınmış"
    assert (SKILLS_DIR / name / "SKILL.md").exists()


def test_c9b_activation_conditions_are_measurement_gated():
    """Koşul metni 'ölç' demiyorsa kalem yine 'bir gün açarız' olur."""
    reg = live_registry()
    evidence = ("ölç", "cf", "gölge", "Y1", "helper", "DSR")
    for name in MEASURE_THEN_ACTIVATE:
        cond = reg[name]["aktivasyon_kosulu"]
        assert any(w in cond for w in evidence), f"{name}: koşul ölçüme bağlanmamış → {cond!r}"


# ---------- C10: sunum katmanı dürüstlüğü (2026-07-30 kopya düzeltmesi) ----------
PRESENTATION_PAGES = ("meridian/web/landing.html", "meridian/web/workflow.html",
                      "workflow-diagram.html")


@pytest.mark.parametrize("page", PRESENTATION_PAGES)
def test_c10_presentation_carries_no_hardcoded_skill_count(page):
    """Sabit "66/68/59 skill" yazıları arşivle bir gecede yalan oldu. Sabit sayı sunum katmanına
    geri yazılamaz: sayı ya /api/public/summary'den canlı gelir ya da hiç görünmez."""
    stale = re.findall(r"\d+\s+skill", (REPO / page).read_text(), flags=re.IGNORECASE)
    assert not stale, f"{page} sabit skill sayısı taşıyor: {stale}"


def test_c10b_landing_binds_the_live_skill_count():
    """Sayıyı silmek yetmez — landing kancayı (#pub-skills) ve alanı (skills_live) kaybederse
    sayfa sessizce sayısız kalır ve kimse fark etmez.

    KAPSAM GENİŞLETİLDİ (2026-08-01): kanca HTML'de kalır ama okuma kodu artık `landing.js`'te.
    Satır içi `<script>` blokları dağıtım CSP'si (`script-src 'self'`) onları blokladığı için
    dışarı alındı — HTML'de bırakılsalardı sayfa canlıda ölü açılırdı. Bu test o taşımada
    kırıldı ve **kırılması doğruydu**: bekçinin işi bağlamanın VARLIĞINI kanıtlamak, bağlamanın
    hangi dosyada olduğunu varsaymak değil. Zayıflatılmadı, doğru yere baktırıldı — `skills_live`
    ikisinden BİRİNDE yoksa test yine kırılır."""
    html = (REPO / "meridian/web/landing.html").read_text()
    js_yol = REPO / "meridian/web/landing.js"
    js = js_yol.read_text() if js_yol.exists() else ""

    assert 'id="pub-skills"' in html, "hero cred canlı bağlama kancasını kaybetmiş"
    assert "skills_live" in html + js, (
        "landing, /api/public/summary'nin skills_live alanını okumuyor "
        "(ne landing.html'de ne landing.js'te)"
    )
    # Betik gerçekten sayfaya bağlı mı — dosya var ama <script src> düşmüşse okuma kodu ölüdür.
    if "skills_live" in js:
        assert 'src="/landing.js"' in html, (
            "okuma kodu landing.js'te ama landing.html onu YÜKLEMİYOR — sayfa sayısız kalır"
        )


def test_c10c_public_summary_computes_skill_counts_from_the_registry():
    """Tanıtım ucu skill sayısını kayıt defterinden HESAPLAR — kayıt değişince sayfa
    kendiliğinden doğru kalır, elle güncelleme diye bir adım yoktur."""
    from meridian import api
    reg = live_registry()
    d = api.api_public_summary()
    assert d["skills_live"] == sum(1 for i in reg.values() if not i.get("retired"))
    assert d["skills_enabled"] == sum(
        1 for i in reg.values() if i.get("enabled") and not i.get("retired"))
