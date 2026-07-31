#!/usr/bin/env python3
"""Regenerate assets/retirement_digest.json from state/skills_registry.json.

The registry (operational state) records which skills were archived to
skills/_emekli/. `.skill` packages ship only this skill folder — no state/ —
so the Claude Web App cannot read the registry. This digest freezes the
retirement facts at package time; recommend.py prefers the live registry and
falls back to this digest (retirement source: "bundled").

The digest is a pure function of the registry's retirement facts only
(name, merged_into, retired_at). Volatile registry fields (last_run,
counters, enablement) do NOT enter, so the digest drifts only when a
retirement actually changes. Never edit the digest by hand.

Usage:
  build_retirement_digest.py [--project-root PATH] [--check]

`--check` exits non-zero if the committed digest drifts from the registry.
The same guard runs in CI via tests/test_navigator_retirement_gate_v126.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_DIGEST = SKILL_ROOT / "assets" / "retirement_digest.json"
REGISTRY_RELPATH = Path("state") / "skills_registry.json"
SCHEMA_VERSION = 1


def build_digest_text(project_root: Path) -> str:
    """Return the canonical digest JSON text for the given repo root."""
    registry_path = project_root / REGISTRY_RELPATH
    entries = json.loads(registry_path.read_text(encoding="utf-8")).get("skills") or {}
    retired: dict[str, dict[str, str | None]] = {}
    for name, info in entries.items():
        if not isinstance(info, dict) or not info.get("retired"):
            continue
        retired[str(name)] = {
            "merged_into": str(info["merged_into"]) if info.get("merged_into") else None,
            "retired_at": str(info["retired_at"]) if info.get("retired_at") else None,
        }
    as_of = max((v["retired_at"] or "" for v in retired.values()), default="") or None
    digest = {
        "as_of": as_of,
        "retired": retired,
        "schema_version": SCHEMA_VERSION,
        "source": REGISTRY_RELPATH.as_posix(),
    }
    # Same canonical encoding as metadata_snapshot.json: sorted keys, 2-space
    # indent, trailing newline.
    return json.dumps(digest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate assets/retirement_digest.json from state/skills_registry.json."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root holding state/skills_registry.json (default: cwd)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed digest would change.",
    )
    parser.add_argument(
        "--digest-path",
        type=Path,
        default=BUNDLED_DIGEST,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    if not (args.project_root / REGISTRY_RELPATH).is_file():
        print(
            f"ERROR: registry not found under {args.project_root} (need {REGISTRY_RELPATH})",
            file=sys.stderr,
        )
        return 1

    try:
        regenerated = build_digest_text(args.project_root)
    except Exception as exc:  # noqa: BLE001 — surface load/parse errors cleanly
        print(f"ERROR: failed to build digest: {exc}", file=sys.stderr)
        return 1

    digest_path: Path = args.digest_path
    current = digest_path.read_text(encoding="utf-8") if digest_path.is_file() else None

    if args.check:
        if current != regenerated:
            print(
                f"DRIFT: {digest_path} is out of sync with the registry. "
                "Run: python3 skills/trading-skills-navigator/scripts/"
                "build_retirement_digest.py",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {digest_path} matches the registry", file=sys.stderr)
        return 0

    if current == regenerated:
        print(f"Unchanged: {digest_path}", file=sys.stderr)
        return 0
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(regenerated, encoding="utf-8")
    print(f"Wrote {digest_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
