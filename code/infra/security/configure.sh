#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../../scripts/load-env.sh
source scripts/load-env.sh

: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID in .env}"
: "${AZURE_TENANT_ID:?Set AZURE_TENANT_ID in .env}"
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP in .env}"
: "${PREFIX:?Set PREFIX in .env}"
: "${AKS_CLUSTER_NAME:?Set AKS_CLUSTER_NAME in .env}"
: "${LOG_ANALYTICS_WORKSPACE:?Set LOG_ANALYTICS_WORKSPACE in .env}"
: "${ENTRA_APP_NAME:?Set ENTRA_APP_NAME in .env}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
FRONTEND_APP="${PREFIX}-web"
FRONTEND_FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "$FRONTEND_APP" --query properties.configuration.ingress.fqdn -o tsv)"
REDIRECT_URI="https://${FRONTEND_FQDN}/.auth/login/aad/callback"

APP_ID="$(az ad app list --display-name "$ENTRA_APP_NAME" --query '[0].appId' -o tsv)"
if [[ -z "$APP_ID" ]]; then
  APP_ID="$(az ad app create \
    --display-name "$ENTRA_APP_NAME" \
    --sign-in-audience AzureADMyOrg \
    --web-redirect-uris "$REDIRECT_URI" \
    --query appId -o tsv)"
  az ad sp create --id "$APP_ID" --only-show-errors >/dev/null
else
  az ad app update --id "$APP_ID" --web-redirect-uris "$REDIRECT_URI"
fi

CLIENT_SECRET="$(az ad app credential reset \
  --id "$APP_ID" \
  --append \
  --display-name moodframe-aca-auth \
  --years 1 \
  --query password -o tsv)"
set_env_value ENTRA_CLIENT_ID "$APP_ID"
set_env_value ENTRA_CLIENT_SECRET "$CLIENT_SECRET"

az containerapp auth microsoft update \
  -g "$RESOURCE_GROUP" \
  -n "$FRONTEND_APP" \
  --client-id "$APP_ID" \
  --client-secret "$CLIENT_SECRET" \
  --issuer "https://login.microsoftonline.com/${AZURE_TENANT_ID}/v2.0" \
  --yes \
  --only-show-errors >/dev/null
az containerapp auth update \
  -g "$RESOURCE_GROUP" \
  -n "$FRONTEND_APP" \
  --enabled true \
  --unauthenticated-client-action RedirectToLoginPage \
  --redirect-provider Microsoft \
  --require-https true \
  --yes \
  --only-show-errors >/dev/null

az security pricing create \
  --name Containers \
  --tier Standard \
  --only-show-errors >/dev/null

WORKSPACE_ID="$(az monitor log-analytics workspace show \
  -g "$RESOURCE_GROUP" \
  -n "$LOG_ANALYTICS_WORKSPACE" \
  --query id -o tsv)"
az aks update \
  -g "$RESOURCE_GROUP" \
  -n "$AKS_CLUSTER_NAME" \
  --enable-defender \
  --workspace-resource-id "$WORKSPACE_ID" \
  --only-show-errors >/dev/null

echo "Microsoft Entra sign-in: https://${FRONTEND_FQDN}/.auth/login/aad"
echo "Defender for Containers: enabled"
