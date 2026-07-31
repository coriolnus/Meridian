"""versioning.py — strategy.yaml version bumps, immutable history snapshots, and the scoreboard.
A parameter change is a version bump + a state/history/vNNNN.yaml snapshot + a hot-reloadable
strategy.yaml. No redeploy for a parameter change (§5); deploy.sh is for code only."""
from __future__ import annotations
import copy
from pathlib import Path

from . import config, store


def snapshot(strategy: dict) -> Path:
    v = int(strategy.get("version", 1))
    path = config.HISTORY / f"v{v:04d}.yaml"
    config.dump_yaml(strategy, path)
    return path


def _next_version(current: dict) -> int:
    """Version numbers are NEVER reused. current+1 alone is wrong after a rollback: revert_to(parent)
    makes strategy.yaml carry the parent's number, so the next ship would reuse the rolled-back child's
    number — and then be judged on the DEAD version's trades (trades.jsonl rows keep the old tag) while
    update_scoreboard merges its fields into the dead row (rolled_back:true and all). Allocate past the
    max of: current, every scoreboard entry, every history snapshot (audit #17/#31)."""
    hi = int(current.get("version", 1))
    for v in scoreboard().get("versions", {}):
        try:
            hi = max(hi, int(v))
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            pass
    try:
        for p in config.HISTORY.glob("v*.yaml"):
            try:
                hi = max(hi, int(p.stem[1:]))
            except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
                pass
    except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        pass
    return hi + 1


def bump(current: dict, variable: str, new, note: str = "") -> dict:
    child = copy.deepcopy(current)
    child["version"] = _next_version(current)
    child["parent"] = int(current.get("version", 1))
    child["params"] = dict(current.get("params", {}))
    if "@" in variable:
        # regime-conditional knob 'base@regime' -> write into params_by_regime, leave flat params intact
        base, regime = variable.split("@", 1)
        by = copy.deepcopy(current.get("params_by_regime", {}) or {})
        by.setdefault(regime, {})[base] = new
        child["params_by_regime"] = by
    else:
        child["params"][variable] = new
    child["note"] = note or f"{variable}->{new}"
    child["changed_variable"] = variable
    return child


def commit(child: dict) -> None:
    """Write the new strategy.yaml (hot-reloaded within one bar) and snapshot it to history."""
    config.dump_yaml(child, config.strategy_path())
    snapshot(child)


def scoreboard() -> dict:
    return store.read_json("scoreboard.json", {"current_version": None, "versions": {}})


SCOREBOARD = "scoreboard.json"


def _sb_default() -> dict:
    return {"current_version": None, "versions": {}}


def update_scoreboard(version: int, **fields) -> dict:
    """KİLİTLİ oku-değiştir-yaz (B3, 2026-07-31).

    Eskiden kilitsizdi ve bu depoda BELGELİ bir kayıp-güncelleme yoluydu: karneye ship yolu
    (reflect), ölçüm yolu (baseline.set_row_fields) ve replay (run.py) yazıyor — üçü ayrı
    süreçte olabiliyor. Kilitsiz oku-değiştir-yaz'da geç kalan yazar, arada yazılmış BÜTÜN
    satırları eski kopyasıyla geri alır ve hiçbir yerde iz kalmaz. `store.update_json` hem
    süreç-içi hem (artık) süreçler-arası kilidi alır."""
    v = str(version)

    def _patch(sb: dict) -> bool:
        sb.setdefault("versions", {}).setdefault(v, {}).update(fields)
        sb["current_version"] = version
        return True

    return store.update_json(SCOREBOARD, _patch, _sb_default())


def set_row_fields(version: int, **fields) -> dict:
    """`update_scoreboard`'ın CANLI SÜRÜM İŞARETİNE DOKUNMAYAN kardeşi.

    `update_scoreboard` her çağrısında `sb["current_version"] = version` yazar (74. satır) — bu ship
    yolu için DOĞRUDUR: karneye yazan taraf zaten o sürümü canlıya alandır. Ama GEÇMİŞE dönük bir
    ölçüm (ebeveyn tabanının backfill'i, bkz. `meridian/baseline.py`) aynı fonksiyonu kullanırsa
    karnedeki canlı sürüm işareti sessizce ATAYA döner: strategy.yaml hâlâ v4 der, karne v3 der ve
    iki gerçek kaynağı birbirini yalanlar. Ölçüm bir KARAR değildir; hangi sürümün canlı olduğunu
    değiştiremez.

    Yalnız `versions[str(version)]` satırına yazar; `current_version` olduğu gibi bırakılır.

    KİLİTLİ (B3, 2026-07-31): `update_scoreboard` ile AYNI gerekçe — bu fonksiyon canlı worker
    koşarken elle tetiklenen bir ölçüm yolundan (baseline backfill) çağrılıyor, yani iki süreçli
    kayıp-güncellemenin en olası kapısı buydu."""
    v = str(version)

    def _patch(sb: dict) -> bool:
        sb.setdefault("versions", {}).setdefault(v, {}).update(fields)
        return True

    return store.update_json(SCOREBOARD, _patch, _sb_default())


def revert_to(version: int) -> dict:
    """Load a historical snapshot and make it the live strategy.yaml again."""
    path = config.HISTORY / f"v{version:04d}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"no snapshot for version {version}: {path}")
    import yaml
    with open(path) as f:
        strat = yaml.safe_load(f)
    config.dump_yaml(strat, config.strategy_path())
    return strat
