#!/usr/bin/env bash
# deploy/connect.sh — reach the agent's dashboard from your laptop over an IAP TCP tunnel. The VM has
# NO public IP (provisioned --no-address), so there is no inbound port to hit directly; IAP forwards
# 8080 through Google's identity-aware proxy — encrypted, and only for principals with the IAP role.
# After it prints "Listening on port [8080]", open http://localhost:8080 in your browser.
#
#   PROJECT=<proj> ZONE=<zone> VM=<name> ./deploy/connect.sh
#
set -euo pipefail
: "${PROJECT:?set PROJECT=<gcp project id>}"
: "${ZONE:?set ZONE=<vm zone, e.g. us-central1-a (free-tier region)>}"
: "${VM:?set VM=<instance name>}"
LOCAL_PORT="${LOCAL_PORT:-8080}"

echo "→ IAP tunnel  localhost:${LOCAL_PORT}  →  ${VM}:8080   (project ${PROJECT}, zone ${ZONE})"
echo "  Requires the 'IAP-secured Tunnel User' role on your account and the firewall rule that allows"
echo "  ingress from 35.235.240.0/20 on tcp:8080 (created by gcp_provision.sh). Ctrl-C to close."
echo
exec gcloud compute start-iap-tunnel "$VM" 8080 \
  --local-host-port="localhost:${LOCAL_PORT}" \
  --zone "$ZONE" --project "$PROJECT"
