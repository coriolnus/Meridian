#!/usr/bin/env bash
# deploy/push_secret.sh — put a secret into Secret Manager WITHOUT it landing in shell history,
# a .env, or logs (Hard Rule 5). Reads the value from a prompt (silent), not from argv.
set -euo pipefail
NAME="${1:?usage: push_secret.sh SECRET_NAME}"
: "${PROJECT_ID:?set PROJECT_ID}"

read -r -s -p "Paste value for ${NAME} (hidden, not echoed): " VALUE; echo
gcloud secrets describe "$NAME" --project "$PROJECT_ID" >/dev/null 2>&1 \
  || gcloud secrets create "$NAME" --replication-policy automatic --project "$PROJECT_ID"
printf '%s' "$VALUE" | gcloud secrets versions add "$NAME" --data-file=- --project "$PROJECT_ID"
unset VALUE
echo "✓ ${NAME} stored in Secret Manager (value never written to disk or history)."
