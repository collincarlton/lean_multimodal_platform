#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: deploy_cloud_run.sh
# ARCHITECTURE: Lean Local Client, Heavy Cloud Execution (Phase 4)
# ==============================================================================
set -euo pipefail

REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="lean-genkit-backend"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null || echo "")"

if [ -z "$PROJECT_ID" ]; then
    echo "[PHASE 4 ERROR] No active GCP project configured in gcloud CLI."
    echo "1. Run 'gcloud projects list' to view your available projects."
    echo "2. Run 'gcloud config set project YOUR_PROJECT_ID' to activate one."
    exit 1
fi

# FinOps guard: require explicit confirmation before provisioning billed GCP resources
if [ "${FINOPS_CONFIRMED:-0}" != "1" ]; then
    echo "[FINOPS GUARD] Cloud Run deployment is gated to prevent unintended cloud billing on project $PROJECT_ID."
    echo "To authorize cloud provisioning, rerun with FINOPS_CONFIRMED=1: FINOPS_CONFIRMED=1 ./deploy_cloud_run.sh"
    exit 1
fi

# Extract GEMINI_API_KEY from genkit_backend/.env if not in shell environment
if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "./genkit_backend/.env" ]; then
    GEMINI_API_KEY="$(grep '^GEMINI_API_KEY=' ./genkit_backend/.env | cut -d '=' -f2-)"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "[PHASE 4 ERROR] GEMINI_API_KEY not found in environment or ./genkit_backend/.env."
    exit 1
fi

echo "[PHASE 4] Project ID: $PROJECT_ID"
echo "[PHASE 4] Enabling required GCP APIs (Cloud Run, Cloud Build, Artifact Registry)..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --quiet

echo "[PHASE 4] Deploying $SERVICE_NAME to Google Cloud Run in $REGION..."

gcloud run deploy "$SERVICE_NAME" \
  --source="./genkit_backend" \
  --region="$REGION" \
  --platform="managed" \
  --allow-unauthenticated \
  --memory="1Gi" \
  --cpu="1" \
  --min-instances="0" \
  --max-instances="10" \
  --set-env-vars="NODE_ENV=production,PORT=8080,GEMINI_API_KEY=$GEMINI_API_KEY"

echo ""
echo "[PHASE 4 SUCCESS] Cloud Run deployment complete."
ENDPOINT="$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")"
echo "================================================================================"
echo "Production Cloud Run Service URL: $ENDPOINT"
echo "Health check: curl $ENDPOINT/api/health"
echo "================================================================================"
