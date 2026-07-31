#!/usr/bin/env python3
"""Build a FinViz screener URL from filter codes — fetch the rows directly, or open it in Chrome.

With a FINVIZ_API_KEY present the script FETCHES the Elite CSV export and prints the rows in the
terminal (no browser).  Without a key it falls back to the original behaviour: build the URL and
hand it to Chrome.  The canonical export endpoint, the token handling and the error masking live
in ONE place — ``meridian/adapters/finviz.py`` — and this script only ever calls into it.

Usage:
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3,fa_pe_u20" --url-only
    python3 open_finviz_screener.py --themes "artificialintelligence,cybersecurity" --url-only
    python3 open_finviz_screener.py --themes "artificialintelligence" --subthemes "aicloud" --filters "cap_midover" --url-only
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3" --view valuation
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3" --elite
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3" --fetch --limit 40
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3" --fetch --csv out.csv
    python3 open_finviz_screener.py --filters "cap_small,fa_div_o3" --open
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import quote

# View type name -> code mapping
VIEW_CODES: dict[str, str] = {
    "overview": "111",
    "valuation": "121",
    "ownership": "131",
    "performance": "141",
    "custom": "152",
    "financial": "161",
    "technical": "171",
}

# Known filter prefixes (warning only if unknown)
KNOWN_PREFIXES: set[str] = {
    "an_",
    "cap_",
    "earningsdate_",
    "etf_",
    "exch_",
    "fa_",
    "geo_",
    "idx_",
    "ind_",
    "ipodate_",
    "news_",
    "sec_",
    "sh_",
    "subtheme_",
    "ta_",
    "targetprice_",
    "theme_",
}

# Strict token pattern: lowercase letters, digits, underscore, dot, hyphen only
_TOKEN_RE = re.compile(r"^[a-z0-9_.\-]+$")

# Slug pattern for theme/sub-theme values: lowercase letters and digits only
_SLUG_RE = re.compile(r"^[a-z0-9]+$")

# Order parameter pattern: optional leading dash, then lowercase letters/digits/underscore
_ORDER_RE = re.compile(r"^-?[a-z0-9_]+$")


def normalize_grouped_slug(value: str, prefix: str) -> str:
    """Strip optional prefix and whitespace from a theme/sub-theme slug."""
    value = value.strip()
    full_prefix = f"{prefix}_"
    if value.startswith(full_prefix):
        value = value[len(full_prefix) :]
    return value


def validate_grouped_slugs(raw: str, prefix: str) -> list[str]:
    """Validate comma-separated theme or sub-theme slugs.

    Args:
        raw: Comma-separated slug values (with or without prefix).
        prefix: ``"theme"`` or ``"subtheme"``.

    Returns:
        Deduplicated list of bare slugs in input order.

    Raises:
        SystemExit: If any slug is empty or contains invalid characters.
    """
    parts = [normalize_grouped_slug(p, prefix) for p in raw.split(",") if p.strip()]
    if not parts:
        print(f"Error: --{prefix}s must contain at least one slug.", file=sys.stderr)
        sys.exit(1)

    validated: list[str] = []
    for slug in parts:
        if not _SLUG_RE.match(slug):
            print(
                f"Error: Invalid {prefix} slug '{slug}'. "
                "Only lowercase letters and digits are allowed (no underscores, dots, or hyphens).",
                file=sys.stderr,
            )
            sys.exit(1)
        validated.append(slug)

    # Deduplicate preserving order
    return list(dict.fromkeys(validated))


def build_filter_parts(
    filters: list[str],
    themes: list[str] | None = None,
    subthemes: list[str] | None = None,
) -> list[str]:
    """Assemble filter parts in canonical order: theme → subtheme → plain filters."""
    parts: list[str] = []
    if themes:
        parts.append("theme_" + "|".join(themes))
    if subthemes:
        parts.append("subtheme_" + "|".join(subthemes))
    parts.extend(filters)
    return parts


def validate_filters(raw_filters: str) -> list[str]:
    """Validate and return a list of filter tokens.

    Each token must match ``^[a-z0-9_.\\-]+$`` (lowercase, digits, underscore,
    dot, hyphen).  Tokens containing ``&``, ``=``, spaces, or other characters
    are rejected to prevent URL injection.

    Unknown prefixes generate a warning to stderr but are not rejected.

    Returns:
        Sorted list of valid filter tokens.

    Raises:
        SystemExit: If any token fails the character-class check.
    """
    tokens: list[str] = [t.strip() for t in raw_filters.split(",") if t.strip()]
    if not tokens:
        print("Error: --filters must contain at least one filter code.", file=sys.stderr)
        sys.exit(1)

    validated: list[str] = []
    for token in tokens:
        # Check for theme/subtheme BEFORE regex validation
        if token.startswith("theme_") or token.startswith("subtheme_"):
            suggested = "--themes" if token.startswith("theme_") else "--subthemes"
            print(
                f"Error: '{token}' detected in --filters. "
                f"Use {suggested} instead for theme/sub-theme filtering.",
                file=sys.stderr,
            )
            sys.exit(1)
        if not _TOKEN_RE.match(token):
            print(
                f"Error: Invalid filter token '{token}'. "
                "Only lowercase letters, digits, underscores, and dots are allowed.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Warn on unknown prefix (not an error)
        prefix = token.split("_", 1)[0] + "_" if "_" in token else ""
        if prefix and prefix not in KNOWN_PREFIXES:
            print(f"Warning: Unknown filter prefix '{prefix}' in '{token}'.", file=sys.stderr)

        validated.append(token)

    return validated


def validate_order(order: str) -> str:
    """Validate the sort order parameter.

    Must match ``^-?[a-z0-9_]+$`` (optional leading dash, then lowercase
    letters, digits, underscores).  Rejects characters that could inject
    additional URL parameters.

    Returns:
        The validated order string.

    Raises:
        SystemExit: If the order value fails validation.
    """
    if not _ORDER_RE.match(order):
        print(
            f"Error: Invalid order value '{order}'. "
            "Only lowercase letters, digits, underscores, and an optional leading dash are allowed.",
            file=sys.stderr,
        )
        sys.exit(1)
    return order


def detect_elite(args: argparse.Namespace) -> bool:
    """Determine whether to use elite.finviz.com.

    Priority:
    1. ``--elite`` flag → True
    2. ``$FINVIZ_API_KEY`` environment variable present → True
    3. Otherwise → False (public)
    """
    if args.elite:
        return True
    if os.environ.get("FINVIZ_API_KEY"):
        return True
    return False


def build_url(
    filters: list[str],
    *,
    elite: bool = False,
    view: str = "overview",
    order: str | None = None,
    themes: list[str] | None = None,
    subthemes: list[str] | None = None,
) -> str:
    """Build the full FinViz screener URL.

    Args:
        filters: List of validated filter tokens.
        elite: Use elite.finviz.com if True.
        view: View type name (overview, valuation, etc.).
        order: Optional sort order code (e.g., ``-marketcap``).
        themes: Optional list of theme slugs.
        subthemes: Optional list of sub-theme slugs.

    Returns:
        Complete URL string.
    """
    host = "elite.finviz.com" if elite else "finviz.com"
    view_code = VIEW_CODES.get(view, VIEW_CODES["overview"])

    parts = build_filter_parts(filters, themes, subthemes)
    filter_str = ",".join(parts)
    encoded_filter_str = quote(filter_str, safe=",_.-")

    url = f"https://{host}/screener.ashx?v={view_code}&f={encoded_filter_str}"
    if order:
        url += f"&o={order}"
    return url


def open_browser(url: str) -> None:
    """Open *url* in Google Chrome, with fallbacks.

    macOS: ``open -a "Google Chrome"``  → ``open``
    Linux: ``google-chrome`` → ``chromium-browser`` → ``xdg-open``
    Final fallback: ``webbrowser.open()``.
    """
    if sys.platform == "darwin":
        # Try Chrome first
        try:
            subprocess.run(  # nosec B607 — macOS open is a known local tool
                ["open", "-a", "Google Chrome", url],
                check=True,
                capture_output=True,
            )
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        # Fallback to default browser on macOS
        try:
            subprocess.run(["open", url], check=True, capture_output=True)  # nosec B607
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    elif sys.platform.startswith("linux"):
        for cmd in ("google-chrome", "chromium-browser", "xdg-open"):
            if shutil.which(cmd):
                try:
                    subprocess.run([cmd, url], check=True, capture_output=True)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

    # Final fallback
    webbrowser.open(url)


# ---------------------------------------------------------------------------
# Direct CSV fetch (Elite).  Everything about the export endpoint — the canonical
# /export/screener path, the auth token, follow_redirects, the error masking — is
# owned by meridian/adapters/finviz.py.  This script never builds an export URL of
# its own; it hands over the same ``f=`` codes the URL builder produces.
# ---------------------------------------------------------------------------


def repo_root() -> Path | None:
    """Walk up from this file looking for the repo root (the dir holding ``meridian/``).

    The script lives in ``skills/finviz-screener/scripts/``, but resolving the root by
    counting parents would break the moment the skill is moved; look for the package.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "meridian" / "adapters" / "finviz.py").is_file():
            return parent
    return None


def load_adapter():
    """Import ``meridian.adapters.finviz`` after bootstrapping sys.path.

    Raises:
        RuntimeError: If the repo root (and therefore the adapter) cannot be located.
    """
    root = repo_root()
    if root is None:
        raise RuntimeError(
            "meridian/adapters/finviz.py bulunamadı — bu skill Meridian deposunun içinden çalışır."
        )
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from meridian.adapters import finviz  # noqa: E402 — sys.path bootstrap'ından SONRA

    return finviz


def key_present() -> bool:
    """Is a Finviz Elite key reachable — env var, or the operator's local secret store?

    ``detect_elite`` only looks at the environment (it decides a hostname, nothing more).
    Fetching needs the real token, which ``secrets.get`` may also pull from state/secrets.json
    or Secret Manager, so ask the adapter when it is importable.  Never returns the token.
    """
    if os.environ.get("FINVIZ_API_KEY"):
        return True
    try:
        return bool(load_adapter().elite())
    except Exception:
        return False


def select_columns(header: list[str], max_cols: int = 6) -> list[str]:
    """Pick the columns to display, IN THE ORDER FINVIZ SENT THEM.

    Column names come from the CSV header only — never invented here.  Which columns exist at
    all is decided by the ``v=`` view code in the request, so this function must stay agnostic:
    it drops the row-number column, floats a ticker column to the front if one is present, and
    keeps whatever comes next.
    """
    cols = [c for c in header if c and c.strip() and c.strip().lower() not in ("no.", "no")]
    ticker = next((c for c in cols if c.strip().lower() == "ticker"), None)
    if ticker is not None:
        cols = [ticker] + [c for c in cols if c != ticker]
    return cols[:max_cols]


def render_table(rows: list[dict], limit: int, cell_width: int = 22) -> str:
    """Render the first *limit* rows as an aligned plain-text table."""
    shown = rows[:limit]
    cols = select_columns(list(shown[0].keys()))

    def cell(value: object) -> str:
        text = "" if value is None else str(value).strip()
        return text if len(text) <= cell_width else text[: cell_width - 1] + "…"

    widths = {c: max([len(c)] + [len(cell(r.get(c))) for r in shown]) for c in cols}
    lines = ["  ".join(c.ljust(widths[c]) for c in cols).rstrip()]
    lines.append("  ".join("-" * widths[c] for c in cols))
    for row in shown:
        lines.append("  ".join(cell(row.get(c)).ljust(widths[c]) for c in cols).rstrip())
    return "\n".join(lines)


def write_csv(rows: list[dict], path: str) -> None:
    """Write the FULL result (every row, every column) to *path*."""
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_fetch(filter_str: str, view_code: str, args: argparse.Namespace) -> int:
    """Fetch the Elite CSV export for *filter_str* and print it.  Returns an exit code."""
    try:
        finviz = load_adapter()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        rows = finviz.export_rows(filter_str, view=view_code)
    except RuntimeError as exc:
        # Token yok / adapter sözleşme hatası — tek satır, traceback yok.
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        # Ağ/HTTP hataları.  httpx'in metni tam URL taşıyabilir → adapter'ın maskesinden geçir;
        # gömülü satır sonlarını da düzleştir ki operatöre TEK dürüst satır düşsün, traceback değil.
        detail = " ".join(finviz._mask_url(str(exc)).split())
        print(f"Error: {type(exc).__name__}: {detail}", file=sys.stderr)
        return 1

    if not rows:
        # SESSİZ BOŞ ≠ BAŞARISIZLIK: istek geçti, sonuç boş.  İkisi ayrı okunsun.
        print("0 rows — the request succeeded but no stock matched these filters.")
        return 0

    if args.csv:
        write_csv(rows, args.csv)
        print(f"Wrote {len(rows)} rows x {len(rows[0])} columns -> {args.csv}")

    limit = max(1, args.limit)
    print(render_table(rows, limit))
    if len(rows) > limit:
        print(f"\n... {len(rows)} rows total, showing first {limit} (--limit to change).")
    else:
        print(f"\n{len(rows)} rows.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a FinViz screener URL and open it in Chrome.",
    )
    parser.add_argument(
        "--filters",
        required=False,
        default=None,
        help="(optional) Comma-separated FinViz filter codes (e.g., cap_small,fa_div_o3,fa_pe_u20).",
    )
    parser.add_argument(
        "--themes",
        default=None,
        help="Comma-separated theme slugs (e.g., artificialintelligence,cybersecurity).",
    )
    parser.add_argument(
        "--subthemes",
        default=None,
        help="Comma-separated sub-theme slugs (e.g., aicloud,aicompute).",
    )
    parser.add_argument(
        "--elite",
        action="store_true",
        default=False,
        help="Use elite.finviz.com (auto-detected from $FINVIZ_API_KEY if not set).",
    )
    parser.add_argument(
        "--view",
        default="overview",
        choices=sorted(VIEW_CODES.keys()),
        help="Screener view type (default: overview).",
    )
    parser.add_argument(
        "--order",
        default=None,
        help="Sort order code (e.g., -marketcap, dividendyield). Prefix - for descending.",
    )
    parser.add_argument(
        "--url-only",
        action="store_true",
        default=False,
        help="Print the URL without opening a browser (never fetches).",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        default=False,
        help=(
            "Fetch the Elite CSV export and print the rows in the terminal. "
            "Automatic when a FINVIZ_API_KEY is available; requires one."
        ),
    )
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the browser as well, even in fetch mode.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Rows to print in fetch mode (default: 25). --csv always gets the full result.",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Write the full fetched result to this CSV path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Validate inputs
    filters: list[str] = []
    themes: list[str] | None = None
    subthemes: list[str] | None = None

    if args.filters is not None:
        filters = validate_filters(args.filters)
    if args.themes is not None:
        themes = validate_grouped_slugs(args.themes, "theme")
    if args.subthemes is not None:
        subthemes = validate_grouped_slugs(args.subthemes, "subtheme")

    if not filters and not themes and not subthemes:
        print(
            "Error: At least one of --filters, --themes, or --subthemes is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    order = validate_order(args.order) if args.order else None
    elite = detect_elite(args)
    url = build_url(
        filters, elite=elite, view=args.view, order=order, themes=themes, subthemes=subthemes
    )

    # MOD SEÇİMİ.  Anahtar varsa varsayılan artık doğrudan çekim: tarayıcıya gerek yok, sonuç
    # terminale gelir.  Anahtar yoksa bugüne kadarki davranış AYNEN sürer (URL kur + Chrome).
    # --url-only'nin anlamı korunur: açıkça "yalnız URL" istendiğinde ne çekilir ne tarayıcı açılır.
    has_key = key_present()
    fetch = bool(args.fetch) or (has_key and not args.url_only)
    want_browser = bool(args.open) or (not fetch and not args.url_only)

    if args.fetch and not has_key:
        print(
            "Error: FINVIZ_API_KEY yok — Elite export anahtarsız çalışmaz; "
            "URL modu için bayraksız çağır.",
            file=sys.stderr,
        )
        sys.exit(2)

    mode = "Elite" if elite else "Public"
    print(f"[{mode}] {url}")

    exit_code = 0
    if fetch:
        if order:
            # --o yalnız URL'in parametresidir; export ucuna taşınmaz.  Sessizce yutmak yerine söyle.
            print(
                f"Warning: --order '{order}' applies to the URL only; "
                "the fetched CSV keeps FinViz's own row order.",
                file=sys.stderr,
            )
        # Filtre string'i URL kurucusunun TA KENDİSİNDEN türer — iki yol asla ayrışmasın.
        filter_str = ",".join(build_filter_parts(filters, themes, subthemes))
        exit_code = run_fetch(filter_str, VIEW_CODES.get(args.view, VIEW_CODES["overview"]), args)

    if want_browser:
        open_browser(url)

    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
