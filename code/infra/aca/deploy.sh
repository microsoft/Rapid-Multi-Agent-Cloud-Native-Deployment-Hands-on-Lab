#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../../scripts/load-env.sh
source scripts/load-env.sh

command -v az >/dev/null
command -v gh >/dev/null
: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID in .env}"
: "${AZURE_LOCATION:?Set AZURE_LOCATION in .env}"
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP in .env}"
: "${PREFIX:?Set PREFIX in .env}"
: "${ACR_NAME:?Set ACR_NAME in .env}"
: "${IMAGE_TAG:=latest}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  set_env_value GITHUB_TOKEN "$(gh auth token)"
fi

az group create --name "$RESOURCE_GROUP" --location "$AZURE_LOCATION" --output none
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/aca/registry.bicep \
  --parameters acrName="$ACR_NAME" \
  --output none

LOGIN_SERVER="$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)"
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  az acr build --registry "$ACR_NAME" --image "moodframe-content:$IMAGE_TAG" --file agents/content_agent/Dockerfile .
  az acr build --registry "$ACR_NAME" --image "moodframe-image:$IMAGE_TAG" --file agents/image_agent/Dockerfile .
  az acr build --registry "$ACR_NAME" --image "moodframe-api:$IMAGE_TAG" --file backend/Dockerfile .
  az acr build --registry "$ACR_NAME" --image "moodframe-web:$IMAGE_TAG" --file frontend/Dockerfile .
fi

DEPLOYMENT_OUTPUT="$(az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/aca/main.bicep \
  --parameters \
    prefix="$PREFIX" \
    acrName="$ACR_NAME" \
    githubToken="$GITHUB_TOKEN" \
    contentAgentImage="$LOGIN_SERVER/moodframe-content:$IMAGE_TAG" \
    imageAgentImage="$LOGIN_SERVER/moodframe-image:$IMAGE_TAG" \
    backendImage="$LOGIN_SERVER/moodframe-api:$IMAGE_TAG" \
    frontendImage="$LOGIN_SERVER/moodframe-web:$IMAGE_TAG" \
  --query properties.outputs -o json)"

FRONTEND_URL="$(printf '%s' "$DEPLOYMENT_OUTPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["frontendUrl"]["value"])')"
for agent_name in "${PREFIX}-content" "${PREFIX}-image"; do
  AGENT_FQDN="$(az containerapp show \
    -g "$RESOURCE_GROUP" \
    -n "$agent_name" \
    --query properties.configuration.ingress.fqdn -o tsv)"
  az containerapp update \
    -g "$RESOURCE_GROUP" \
    -n "$agent_name" \
    --set-env-vars "AGENT_PUBLIC_URL=https://${AGENT_FQDN}/" \
    --only-show-errors >/dev/null
done
set_env_value ACA_FRONTEND_URL "$FRONTEND_URL"
echo "ACA frontend: $FRONTEND_URL"
