#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
source scripts/load-env.sh

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az containerapp auth show \
  -g "$RESOURCE_GROUP" \
  -n "${PREFIX}-web" \
  --query '{enabled:platform.enabled,action:globalValidation.unauthenticatedClientAction,clientId:identityProviders.azureActiveDirectory.registration.clientId}' \
  -o table
az aks show \
  -g "$RESOURCE_GROUP" \
  -n "$AKS_CLUSTER_NAME" \
  --query '{aadManaged:aadProfile.managed,azureRbac:aadProfile.enableAzureRbac,defender:securityProfile.defender.securityMonitoring.enabled}' \
  -o table
az security pricing show -n Containers --query '{name:name,tier:pricingTier}' -o table
