#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../../scripts/load-env.sh
source scripts/load-env.sh

command -v az >/dev/null
command -v kubectl >/dev/null
command -v gh >/dev/null
: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID in .env}"
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP in .env}"
: "${ACR_NAME:?Set ACR_NAME in .env}"
: "${AKS_CLUSTER_NAME:?Set AKS_CLUSTER_NAME in .env}"
: "${LOG_ANALYTICS_WORKSPACE:?Set LOG_ANALYTICS_WORKSPACE in .env}"
: "${AGENT_IMAGE_TAG:=fix3}"
: "${API_IMAGE_TAG:=fix3}"
: "${WEB_IMAGE_TAG:=fix2}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  set_env_value GITHUB_TOKEN "$(gh auth token)"
fi

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/aks/main.bicep \
  --parameters \
    acrName="$ACR_NAME" \
    clusterName="$AKS_CLUSTER_NAME" \
    workspaceName="$LOG_ANALYTICS_WORKSPACE" \
    tenantId="$AZURE_TENANT_ID" \
  --output none

LOGIN_SERVER="$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)"
AKS_ID="$(az aks show -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" --query id -o tsv)"
USER_ID="$(az ad signed-in-user show --query id -o tsv)"
az role assignment create \
  --assignee-object-id "$USER_ID" \
  --assignee-principal-type User \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "$AKS_ID" \
  --only-show-errors >/dev/null || true

az aks get-credentials \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --overwrite-existing

kubectl apply -f <(printf '%s\n' 'apiVersion: v1' 'kind: Namespace' 'metadata:' '  name: moodframe')
kubectl -n moodframe create secret generic copilot-auth \
  --from-literal=github-token="$GITHUB_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
sed \
  -e "s|__LOGIN_SERVER__|$LOGIN_SERVER|g" \
  -e "s|__AGENT_TAG__|$AGENT_IMAGE_TAG|g" \
  -e "s|__API_TAG__|$API_IMAGE_TAG|g" \
  -e "s|__WEB_TAG__|$WEB_IMAGE_TAG|g" \
  infra/aks/k8s.yaml > infra/aks/rendered.yaml
kubectl apply -f infra/aks/rendered.yaml
kubectl -n moodframe rollout status deployment/content-agent --timeout=5m
kubectl -n moodframe rollout status deployment/image-agent --timeout=5m
kubectl -n moodframe rollout status deployment/backend --timeout=5m
kubectl -n moodframe rollout status deployment/frontend --timeout=5m
for _ in {1..30}; do
  FRONTEND_IP="$(kubectl -n moodframe get service frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  [[ -n "$FRONTEND_IP" ]] && break
  sleep 10
done
if [[ -z "${FRONTEND_IP:-}" ]]; then
  echo "AKS frontend public IP was not assigned in time." >&2
  exit 1
fi
set_env_value AKS_FRONTEND_URL "http://$FRONTEND_IP"
echo "AKS frontend: http://$FRONTEND_IP"
