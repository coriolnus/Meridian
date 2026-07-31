"""test_learning_firewall_v90.py — mrd:bars → ÖĞRENME ateş duvarı (Faz 4, YAPISAL kilit).

İnvaryant 3: mrd:bars (uçucu dakikalık Redis akışı) backtest/öğrenme/OOS'a ASLA girmez; kalıcı öğrenme
kaynağı state/bars/*.json immutable günlük barlarıdır. Bu bugün YAPISAL (öğrenme yolu hotstate import
etmez). Bu test o duvarı KİLİTLER: biri bir gün öğrenme yoluna hotstate sokarsa build KIRILIR.
"""
import ast
import pathlib

MERIDIAN = pathlib.Path(__file__).resolve().parent.parent / "meridian"
LEARNING_MODULES = ("backtest", "dataset", "reflect", "recompute", "counterfactual", "oos_pipeline")


def test_learning_path_never_imports_hotstate():
    for name in LEARNING_MODULES:
        p = MERIDIAN / f"{name}.py"
        if not p.exists():
            continue
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and "hotstate" in n.module:
                raise AssertionError(f"{name}.py hotstate import ediyor — mrd:bars ÖĞRENMEYE sızıyor (İnvaryant 3)")
            if isinstance(n, ast.Import):
                assert not any("hotstate" in a.name for a in n.names), \
                    f"{name}.py hotstate import ediyor — mrd:bars öğrenmeye sızıyor"


def test_intraday_consumer_never_touches_execution_or_persistent_book():
    """intraday_cycle GÖZLEM-modu: icra (submit/fill/cancel) ve iç broker defteri (portfolio yazımı)
    yollarını İÇERMEZ — sıfır yetki yapısal kanıtı."""
    src = (MERIDIAN / "intraday_cycle.py").read_text()
    for forbidden in ("submit_plan", "submit_bracket", "fill_entry", "close_all", "cancel_open_entries",
                      "write_json", "update_json"):
        assert forbidden not in src, f"intraday_cycle '{forbidden}' içeremez (gözlem-modu, sıfır yetki)"
