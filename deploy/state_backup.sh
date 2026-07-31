#!/usr/bin/env bash
# deploy/state_backup.sh — nightly backup of state/ to GCS. The state dir is the agent's accumulated
# learning; it is the only thing here that cannot be rebuilt (§9). Install as a cron on the VM:
#   0 5 * * *  /opt/meridian/deploy/state_backup.sh >> /var/log/meridian-backup.log 2>&1
set -euo pipefail
: "${MERIDIAN_GCP_PROJECT:?set MERIDIAN_GCP_PROJECT}"
DATE=$(date +%F)
DEST="gs://${MERIDIAN_GCP_PROJECT}-meridian-state/${DATE}"
gcloud storage rsync -r /opt/meridian/state "$DEST"
echo "✓ state/ synced to ${DEST}"
