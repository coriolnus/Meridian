#!/usr/bin/env bash
# deploy/gcp_provision.sh — one-time GCP provisioning, confirmation-gated. Reads real resource
# names from gcloud; never invents them (Hard Rule 4). Says the money number out loud before any
# billable create. Run step-by-step; each create asks for an explicit yes.
set -euo pipefail

confirm(){ read -r -p "$1 [y/N] " a; [[ "$a" == "y" || "$a" == "Y" ]]; }

echo "=== 0. Auth + project discovery (no charges) ==="
gcloud auth list --filter=status:ACTIVE --format="value(account)" || { echo "run: gcloud auth login"; exit 1; }
echo "Projects you can use:"; gcloud projects list --format="table(projectId,name)"
read -r -p "PROJECT_ID to use: " PROJECT_ID
gcloud config set project "$PROJECT_ID"

echo "=== 1. Existing instances (pick one, or create) ==="
gcloud compute instances list || true
REGION="${REGION:-us-central1}"; ZONE="${ZONE:-us-central1-a}"
VM_NAME="${VM_NAME:-meridian}"

if ! gcloud compute instances describe "$VM_NAME" --zone "$ZONE" >/dev/null 2>&1; then
  echo "No VM named '$VM_NAME' in $ZONE."
  echo "PROPOSED: e2-medium, ${ZONE}, --no-address (Cloud NAT for egress), Debian 12."
  echo ">>> COST: an e2-medium runs ≈ US\$27/month. This is a BILLABLE resource. <<<"
  if confirm "Create the VM now?"; then
    gcloud compute instances create "$VM_NAME" \
      --zone "$ZONE" --machine-type e2-medium \
      --image-family debian-12 --image-project debian-cloud \
      --no-address --boot-disk-size 30GB \
      --scopes cloud-platform
  else
    echo "Skipped VM creation."; exit 0
  fi
fi

echo "=== 2. Cloud NAT for outbound (screeners need FMP; --no-address has no egress without it) ==="
echo "Without Cloud NAT the VM has NO internet and failures are baffling. Small hourly cost applies."
if confirm "Create Cloud Router + NAT in ${REGION}?"; then
  gcloud compute routers create meridian-router --network default --region "$REGION" || true
  gcloud compute routers nats create meridian-nat \
    --router meridian-router --region "$REGION" \
    --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges || true
fi

echo "=== 3. State backup bucket (GCS) ==="
BUCKET="gs://${PROJECT_ID}-meridian-state"
if confirm "Create ${BUCKET} for nightly state backups?"; then
  gcloud storage buckets create "$BUCKET" --location "$REGION" || true
fi

echo "=== 4. Secret Manager: grant the VM service account access ==="
SA=$(gcloud compute instances describe "$VM_NAME" --zone "$ZONE" \
     --format="value(serviceAccounts[0].email)")
echo "VM service account: $SA"
for S in FMP_API_KEY ALPACA_PAPER_KEY ALPACA_PAPER_SECRET HERMES_API_KEY; do
  gcloud secrets describe "$S" >/dev/null 2>&1 || \
    (echo "Secret $S not found — create it with deploy/push_secret.sh $S")
  gcloud secrets add-iam-policy-binding "$S" \
    --member "serviceAccount:${SA}" --role roles/secretmanager.secretAccessor >/dev/null 2>&1 || true
done

echo "✓ Provisioning complete. Save these for later commands:"
echo "  export PROJECT_ID=$PROJECT_ID VM_NAME=$VM_NAME VM_ZONE=$ZONE"
