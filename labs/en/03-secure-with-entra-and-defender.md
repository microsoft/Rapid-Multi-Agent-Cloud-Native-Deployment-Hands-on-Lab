# Lab 3: Protect the MoodFrame community

**Duration:** 15 minutes  
**Level:** Beginner  
**Technology:** Microsoft Entra ID, Container Apps authentication, Microsoft Defender for Cloud

## The story

MoodFrame is ready for an internal community pilot. The team must ensure that only employees can access the ACA experience, cluster administrators use organizational identities, and the security team can monitor container risks.

## Technology introduction

**Microsoft Entra ID** is the identity provider for the application and AKS control plane. Azure Container Apps built-in authentication can perform the OAuth/OpenID Connect flow without adding authentication code to the SPA or FastAPI service.

**Microsoft Defender for Cloud** continuously evaluates cloud security posture. Defender for Containers adds Kubernetes and container workload recommendations and runtime protection signals.

## Why these technologies?

- Entra ID gives the team single-tenant organizational sign-in.
- Container Apps built-in authentication reduces custom security code.
- AKS managed Entra integration avoids Kubernetes local accounts for normal administration.
- Defender for Containers connects the deployed cluster to Azure security recommendations.

> Defender for Containers is a paid plan after any applicable trial period.

## Exercise 1: Register MoodFrame in Microsoft Entra ID

```bash
cd code
source scripts/load-env.sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

Build the callback URL from the deployed ACA frontend:

```bash
FRONTEND_FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --query properties.configuration.ingress.fqdn -o tsv)"
REDIRECT_URI="https://${FRONTEND_FQDN}/.auth/login/aad/callback"
```

Create a single-tenant app registration and credential:

```bash
APP_ID="$(az ad app create \
  --display-name "$ENTRA_APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --web-redirect-uris "$REDIRECT_URI" \
  --query appId -o tsv)"
az ad sp create --id "$APP_ID"
CLIENT_SECRET="$(az ad app credential reset \
  --id "$APP_ID" --append --display-name moodframe-aca-auth --years 1 \
  --query password -o tsv)"
set_env_value ENTRA_CLIENT_ID "$APP_ID"
set_env_value ENTRA_CLIENT_SECRET "$CLIENT_SECRET"
```

## Exercise 2: Protect the ACA frontend

```bash
az containerapp auth microsoft update \
  -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --client-id "$APP_ID" \
  --client-secret "$CLIENT_SECRET" \
  --issuer "https://login.microsoftonline.com/${AZURE_TENANT_ID}/v2.0" \
  --yes

az containerapp auth update \
  -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --enabled true \
  --unauthenticated-client-action RedirectToLoginPage \
  --redirect-provider Microsoft \
  --require-https true \
  --yes
```

## How authentication is invoked

Open the application URL. ACA intercepts the request and starts the Entra sign-in flow:

```bash
open "$ACA_FRONTEND_URL/.auth/login/aad"
```

On Linux, open the printed URL in a browser instead. You can inspect the HTTP redirect:

```bash
curl -I "$ACA_FRONTEND_URL/.auth/login/aad"
```

After sign-in, the browser receives the ACA authentication cookie and can call `/api/generate`.

## Exercise 3: Enable Defender for Containers

```bash
az security pricing create --name Containers --tier Standard
WORKSPACE_ID="$(az monitor log-analytics workspace show \
  -g "$RESOURCE_GROUP" -n "$LOG_ANALYTICS_WORKSPACE" --query id -o tsv)"
az aks update \
  -g "$RESOURCE_GROUP" \
  -n "$AKS_CLUSTER_NAME" \
  --enable-defender \
  --workspace-resource-id "$WORKSPACE_ID"
```

## How Defender is queried

```bash
az security pricing show -n Containers \
  --query '{plan:name,tier:pricingTier}' -o table

az aks show -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" \
  --query '{entra:aadProfile.managed,azureRbac:aadProfile.enableAzureRbac,defender:securityProfile.defender.securityMonitoring.enabled}' \
  -o table
```

Open **Microsoft Defender for Cloud > Recommendations** in the Azure portal and filter by the AKS cluster name.

## Check your work

- The ACA login endpoint redirects to `login.microsoftonline.com`.
- The Entra app is single tenant.
- AKS uses managed Entra authentication and Azure RBAC.
- The Containers plan is `Standard`.
- AKS Defender security monitoring is enabled.

## Learn more

- [Microsoft identity platform overview](https://learn.microsoft.com/entra/identity-platform/v2-overview)
- [Authentication in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/authentication)
- [Microsoft Entra authentication for AKS](https://learn.microsoft.com/azure/aks/entra-id-control-plane-authentication)
- [Microsoft Defender for Containers](https://learn.microsoft.com/azure/defender-for-cloud/defender-for-containers-introduction)
- [Security recommendations in Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/review-security-recommendations)

