#!/usr/bin/env bash
# deploy.sh — push CODE to the VM and restart the compose stack. For code changes only;
# a parameter change is a version bump that hot-reloads without redeploy (§4/§5).
# Resource names are READ from gcloud and confirmed — never invented (Hard Rule 4).
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID (run: gcloud config get-value project)}"
: "${VM_NAME:?set VM_NAME (run: gcloud compute instances list)}"
: "${VM_ZONE:?set VM_ZONE (from the same instances list)}"

SSH_FLAGS="--tunnel-through-iap --zone=${VM_ZONE} --project=${PROJECT_ID}"
REMOTE_DIR="/opt/meridian"

echo "→ Deploying code to ${VM_NAME} (${VM_ZONE}) in ${PROJECT_ID} over IAP…"
echo "  NOTE: state/ is NOT synced — it is the agent's learning and lives only on the VM (+ GCS backup)."

# rsync code (NOT .env, NOT state/) to the VM via the IAP tunnel
gcloud compute scp --recurse ${SSH_FLAGS} \
  meridian skills pyproject.toml Dockerfile docker-compose.yml \
  "${VM_NAME}:${REMOTE_DIR}/"

# rebuild + restart the stack on the VM
gcloud compute ssh ${SSH_FLAGS} "${VM_NAME}" --command "\
  cd ${REMOTE_DIR} && \
  sudo docker compose build && \
  sudo docker compose up -d && \
  sudo docker compose ps"

echo "✓ Deployed. Verify heartbeat freshness in the dashboard (IAP tunnel on :8080)."
