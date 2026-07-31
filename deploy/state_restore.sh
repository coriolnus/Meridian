#!/usr/bin/env bash
# deploy/state_restore.sh — restore state/ from a GCS backup (the counterpart to state_backup.sh).
# The state dir is the agent's accumulated learning; a backup with no tested restore is not a backup.
# HALTS first, validates every JSON parses before swapping in, keeps the current state as .bak.
#   usage: MERIDIAN_GCP_PROJECT=... deploy/state_restore.sh [YYYY-MM-DD|latest]
set -euo pipefail
: "${MERIDIAN_GCP_PROJECT:?set MERIDIAN_GCP_PROJECT}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUCKET="gs://${MERIDIAN_GCP_PROJECT}-meridian-state"
WHEN="${1:-latest}"

echo "→ HALT first (no new entries while we swap state)"
touch "$ROOT/state/HALT"

if [ "$WHEN" = "latest" ]; then
  WHEN=$(gcloud storage ls "$BUCKET" | sed 's#.*/\([0-9-]\{10\}\)/#\1#' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort | tail -1)
  echo "  latest backup = $WHEN"
fi
SRC="$BUCKET/$WHEN"
TMP=$(mktemp -d)
echo "→ pulling $SRC → $TMP"
gcloud storage rsync -r "$SRC" "$TMP"

echo "→ validating every .json / .jsonl parses before swap"
bad=0
while IFS= read -r f; do
  if [[ "$f" == *.json ]]; then python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$f" 2>/dev/null || { echo "  CORRUPT: $f"; bad=1; }; fi
  if [[ "$f" == *.jsonl ]]; then python3 -c "import json,sys;[json.loads(l) for l in open(sys.argv[1]) if l.strip()]" "$f" 2>/dev/null || { echo "  CORRUPT: $f"; bad=1; }; fi
done < <(find "$TMP" -type f \( -name '*.json' -o -name '*.jsonl' \))
[ "$bad" = 0 ] || { echo "✗ backup has corrupt files — NOT restoring. state/HALT left in place."; exit 1; }

echo "→ backing up current state → state.bak, then swapping in the restore"
rm -rf "$ROOT/state.bak"; cp -a "$ROOT/state" "$ROOT/state.bak"
cp -a "$TMP/." "$ROOT/state/"
echo "✓ restored from $WHEN. Review, then remove state/HALT to resume:  rm $ROOT/state/HALT"
