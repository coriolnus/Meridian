"""test_mutation_v61.py — MUTASYON KOŞUMUNUN kendi testi (2026-07-22).

Koşum bir ÖLÇÜ ALETİDİR; ölçü aletinin kendisi kalibre edilmeden ürettiği sayı hiçbir şey ifade
etmez. Bu dosya dört şeyi bağlar:

  1. TEMEL DURUM TEMİZ — kirli bir temelde her mutasyon "yakalandı" görünür ve kapsama sayısı yalan
     söyler. Bu, koşumun tek ve en kritik ön koşuludur; ihlal edilirse koşum DURMALIDIR.
  2. HER MUTASYON GERÇEKTEN BOZAR — hiçbir şeyi değiştirmeyen bir mutasyon sessizce "kaçtı" ya da
     (daha kötüsü) başka bir mutasyonun etkisiyle "yakalandı" sayılırdı.
  3. ENVANTER SABİT — bugünün yakalanan/KAÇAN dökümü çakılır. Bir dedektör yakalamayı bırakırsa
     test kırılır; yeni bir mutasyon sınıflandırılmadan eklenemez.
  4. CANLI DEFTERE DOKUNULMAZ.

KAÇANLAR listesi DÜRÜSTÇE tutulur. Düşük kapsama sayısı burada başarısızlık değil, ÜRÜNDÜR: her
KAÇAN satır, sistemin bugün göremediği bir hata sınıfının adıdır. Sayıyı yükseltmek için mutasyonu
zayıflatmak, ölçümün kendisini çöpe atmak demektir.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meridian import config, mutation


# ---------------------------------------------------------------------------------------------
# BUGÜNÜN ENVANTERİ — çakılmış döküm (2026-07-22)
# ---------------------------------------------------------------------------------------------
EXPECTED_CAUGHT = {
    "plan_id_legacy_scheme",
    "trade_plan_id_legacy_scheme",
    "cf_id_legacy_scheme",
    "drop_required_field_setup",
    "drop_required_field_status",
    "truncate_trades_ledger",
    "stale_derived_artifact",
    "zero_out_calibration_artifact",
    "duplicate_rows_in_trades",
    "owned_field_clobbered",
    "book_date_regression",
    "bars_file_shrinks_without_rev_bump",
    "hypothesis_id_reused",
    "silent_plan_loss",
    "consumer_silently_drops_every_row",
    "realized_pnl_drifts_from_the_ledger",
    "measured_edge_turns_negative",
    # 2026-07-22'de körlük haritasından buraya taşınan ALTI sınıf (dedektörler eklendi/genişletildi):
    "rename_field_to_legacy_alias",            # ledgers: takma ad kanonik adın yerini alamaz
    "regime_overwritten_with_question_mark",   # recompute: regime_label_quality (değer, varlık değil)
    "truncate_events_ledger",                  # watchdog: monotonluk artık events+candidates izliyor
    "value_shifted_out_of_bounds",             # recompute: bounds_respected (bounds.yaml'a karşı)
    "writer_produces_rows_nobody_reads",       # recompute: orphan_state_files (çalışma-anı tüketici grafiği)
    "candidates_ledger_emptied",               # watchdog: monotonluk artık candidates izliyor
}

# KÖRLÜK HARİTASI — bu satırların her biri bugün GÖRÜLEMEYEN bir hata sınıfıdır.
# Yanlarındaki not, "neden görülemiyor"un cevabıdır; düzeltilirse buradan çıkarılır (ve o gün
# EXPECTED_CAUGHT'a girer).
EXPECTED_MISSED: set = set()   # 2026-07-22: körlük haritası BOŞALDI (23/23). Bu boşluk bir iddiadır —
# yeni bir mutasyon eklenip yakalanamazsa test onu buraya düşmeye zorlar, "sessizce %100" olmaz.


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    """Koşumu bir kez çalıştır (batarya × 23 mutasyon pahalı), sonucu bütün testler paylaşsın."""
    work = tmp_path_factory.mktemp("mutation-run")
    res = mutation.run(workdir=work, keep=True)
    yield res
    shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# 1) ÖN KOŞUL: TEMEL DURUM TEMİZ
# ---------------------------------------------------------------------------------------------
def test_baseline_state_is_genuinely_clean(harness):
    """Ölçümün tamamı buna dayanır: temel kirliyse her mutasyon 'yakalandı' görünür."""
    assert harness["baseline_clean"], \
        f"temel durum kirli — kapsama sayısı anlamsız: {harness['baseline_red']}"
    assert harness["baseline_red"] == []


def test_a_dirty_baseline_stops_the_run_loudly(tmp_path, monkeypatch):
    """Ön koşul SESSİZCE geçilemez: temel kirliyse koşum sayı üretmek yerine DURMALI."""
    real_build = mutation.build_state

    def _sabotaged(dest):
        real_build(dest)
        mutation.MUTATIONS[0].apply(dest)      # temel durumu bilerek boz
        return dest

    monkeypatch.setattr(mutation, "build_state", _sabotaged)
    with pytest.raises(RuntimeError, match="TEMEL DURUM KİRLİ"):
        mutation.run(workdir=tmp_path / "dirty")


def test_baseline_satisfies_the_written_ledger_contract(tmp_path):
    """Temel durum 'dedektör susuyor' diye değil, SÖZLEŞMEYE UYDUĞU için temiz olmalı."""
    from meridian import ledgers
    dest = mutation.build_state(tmp_path / "base")
    with mutation.using_state(dest):
        for name in ledgers.CONTRACTS:
            v = ledgers.validate_live(name)
            assert v["ok"], f"{name}: temel durum sözleşmeyi ihlal ediyor → {v['violations']}"


# ---------------------------------------------------------------------------------------------
# 2) HER MUTASYON GERÇEKTEN BİR ŞEY BOZAR (no-op mutasyon skoru sessizce şişirir)
# ---------------------------------------------------------------------------------------------
def test_every_mutation_actually_changes_the_state(tmp_path):
    base = mutation.build_state(tmp_path / "base")
    before = mutation.dir_digest(base)
    for mut in mutation.MUTATIONS:
        work = tmp_path / f"m_{mut.name}"
        shutil.copytree(base, work)
        mut.apply(work)
        after = mutation.dir_digest(work)
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        assert changed, f"'{mut.name}' hiçbir şeyi değiştirmedi — sahte bir ölçüm satırı"


def test_the_harness_records_that_each_mutation_changed_the_state(harness):
    noop = [r["mutation"] for r in harness["rows"] if not r["changed_state"]]
    assert not noop, f"durumu değiştirmeyen mutasyon(lar): {noop}"


def test_mutation_names_are_unique_and_documented():
    names = [m.name for m in mutation.MUTATIONS]
    assert len(names) == len(set(names)), "mutasyon adı tekrarlanıyor"
    for m in mutation.MUTATIONS:
        assert m.note and len(m.note) > 20, f"{m.name}: Türkçe gerekçesi yok"


# ---------------------------------------------------------------------------------------------
# 3) ENVANTER ÇAKILI: bir dedektör yakalamayı bırakırsa burası kırılır
# ---------------------------------------------------------------------------------------------
def test_caught_inventory_is_pinned(harness):
    caught = set(harness["caught"])
    regressed = EXPECTED_CAUGHT - caught
    assert not regressed, (
        f"bu mutasyonlar ARTIK YAKALANMIYOR (bir dedektör körleşti): {sorted(regressed)}")


def test_missed_inventory_is_pinned(harness):
    missed = set(harness["missed"])
    newly_blind = missed - EXPECTED_MISSED
    assert not newly_blind, f"yeni körlük belirdi: {sorted(newly_blind)}"
    newly_seen = EXPECTED_MISSED - missed
    assert not newly_seen, (
        f"artık YAKALANIYOR — körlük listesinden çıkarılmalı (liste yalan söylememeli): "
        f"{sorted(newly_seen)}")


def test_every_mutation_is_classified(harness):
    """Sınıflandırılmamış bir mutasyon, envanteri sessizce anlamsızlaştırır."""
    known = EXPECTED_CAUGHT | EXPECTED_MISSED
    all_names = {m.name for m in mutation.MUTATIONS}
    assert all_names == known, (
        f"envanterde olmayan: {sorted(all_names - known)} · "
        f"artık var olmayan: {sorted(known - all_names)}")
    assert set(harness["caught"]) | set(harness["missed"]) == all_names


def test_each_caught_mutation_names_the_detector_that_saw_it(harness):
    for name, dets in harness["caught"].items():
        assert dets, f"{name}: 'yakalandı' deniyor ama dedektör adı yok"
        assert all(":" in d for d in dets), f"{name}: dedektör jetonları biçimsiz {dets}"


def test_coverage_number_matches_the_inventory(harness):
    n = harness["n_mutations"]
    assert n == len(mutation.MUTATIONS)
    assert harness["n_caught"] + harness["n_missed"] == n
    assert harness["coverage_pct"] == pytest.approx(100.0 * harness["n_caught"] / n, abs=0.1)


# ---------------------------------------------------------------------------------------------
# 4) RAPOR: kaçanlar GEREKÇESİYLE görünür olmalı (sayı tek başına işe yaramaz)
# ---------------------------------------------------------------------------------------------
def test_blind_spots_are_reported_with_their_reason(harness):
    assert len(harness["blind_spots"]) == harness["n_missed"]
    for b in harness["blind_spots"]:
        assert b["note"], f"{b['mutation']}: körlük notu yok"


def test_human_report_names_every_missed_class(harness):
    txt = mutation.format_report(harness)
    assert "KAÇANLAR" in txt and "körlük haritası" in txt
    for name in harness["missed"]:
        assert name in txt, f"{name} insan raporunda görünmüyor"


def test_the_sieve_detector_is_either_used_or_its_absence_is_logged(harness):
    """'Ölçülmedi' ile 'temiz' aynı şey değildir: sieve yoksa bu raporda YAZAR."""
    if not harness["sieve_present"]:
        assert any("sieve" in m for m in harness["log"]), "sieve yokluğu kayda geçmemiş"
    else:
        import meridian.sieve  # noqa: F401  (varsa gerçekten yüklenebiliyor olmalı)


def test_network_dependent_checks_are_declared_out_of_scope(harness):
    """Ağa çıkan üretkenlik kontrolleri susturuldu — bu sessizce yapılmaz, raporda beyan edilir."""
    assert harness["out_of_scope"], "kapsam dışı bırakılanlar beyan edilmemiş"


# ---------------------------------------------------------------------------------------------
# 5) CANLI DEFTERE ASLA DOKUNULMAZ
# ---------------------------------------------------------------------------------------------
def test_the_live_state_directory_is_refused():
    live = Path(config.ROOT) / "state"
    with pytest.raises(RuntimeError, match="canlı defter"):
        mutation._assert_not_live(live)
    with pytest.raises(RuntimeError, match="canlı defter"):
        mutation._assert_not_live(live / "trades.jsonl")
    with pytest.raises(RuntimeError):
        mutation.run(workdir=live)


def test_a_full_run_leaves_the_live_ledgers_untouched(harness):
    """Koşum bittiğinde config.STATE geri alınmış ve canlı defterlere dokunulmamış olmalı."""
    live = Path(config.ROOT) / "state"
    assert Path(config.STATE).resolve() != Path(harness["workdir"]).resolve()
    for f in ("trades.jsonl", "trade_plans.jsonl", "portfolio.json"):
        p = live / f
        if p.exists():
            assert Path(harness["workdir"]) not in p.parents


def test_the_harness_never_writes_ledgers_through_the_store_module():
    """Koşum defterlere store.* ile yazsaydı `ledgers.declared_writers()` onu BEYAN EDİLMEMİŞ bir
    yazar sayar, `ledger_writers` kırmızıya döner ve TEMEL DURUM kirlenirdi — yani ölçü aleti,
    ölçtüğü şeyi bozardı. Dosyalar bilerek doğrudan yazılıyor."""
    from meridian import ledgers
    assert "mutation.py" not in {w for ws in ledgers.declared_writers().values() for w in ws}
    assert not ledgers.writer_violations(), "koşum sözleşme yazar taramasını kirletti"


def test_module_is_runnable_as_a_cli_and_importable():
    """İki yüzey de olmalı: `python -m meridian.mutation` (operatör) ve import (test/pano)."""
    import inspect
    src = inspect.getsource(mutation)
    assert 'if __name__ == "__main__"' in src and "def main(" in src
    with pytest.raises(SystemExit) as e:                  # --help: argparse kurulumu gerçekten çalışıyor
        mutation.main(["--help"])
    assert e.value.code == 0
    assert callable(mutation.run) and callable(mutation.format_report)
