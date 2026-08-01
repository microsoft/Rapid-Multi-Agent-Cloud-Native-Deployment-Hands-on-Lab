# Lab 1: Launch MoodFrame with Azure Container Apps

**Duration:** 15 minutes  
**Level:** Beginner  
**Technology:** Azure Container Apps, Azure Container Registry, Bicep

## The story

The MoodFrame product owner wants a public preview today. The team has four containers but does not want to manage virtual machines or Kubernetes yet. The content and image agents must remain private, while only the web experience is exposed to users.

## Technology introduction

**Azure Container Apps (ACA)** is a serverless container platform. It runs containers, provides HTTPS ingress, service discovery, revisions, logs, and autoscaling without requiring the team to operate a Kubernetes control plane.

**Azure Container Registry (ACR)** stores the four private application images. **ACR Tasks** builds them in Azure, so this lab does not depend on the learner's local CPU architecture.

**Bicep** describes the Azure resources as repeatable infrastructure as code.

## Why this technology?

ACA is the right first deployment because MoodFrame:

- Is already containerized.
- Uses HTTP services and private service-to-service calls.
- Needs a fast public preview with minimal operations.
- Does not yet require direct Kubernetes API control.

## Target architecture

```text
Internet
   |
ACA frontend (external)
   |
ACA FastAPI (internal)
   |-------------------|
ACA content agent   ACA image agent
        (internal A2A services)
```

## Exercise 1: Load the lab configuration

```bash
cd code
source scripts/load-env.sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
set_env_value GITHUB_TOKEN "$(gh auth token)"
```

## Exercise 2: Build the four images in Azure

Create ACR:

```bash
az deployment group create \
  -g "$RESOURCE_GROUP" \
  -f infra/aca/registry.bicep \
  -p acrName="$ACR_NAME"
```

Build a shared `lab1` image version:

```bash
az acr build -r "$ACR_NAME" -t moodframe-content:lab1 -f agents/content_agent/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-image:lab1 -f agents/image_agent/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-api:lab1 -f backend/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-web:lab1 -f frontend/Dockerfile .
LOGIN_SERVER="$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)"
```

## Exercise 3: Deploy the Container Apps

```bash
az deployment group create \
  -g "$RESOURCE_GROUP" \
  -f infra/aca/main.bicep \
  -p \
    prefix="$PREFIX" \
    acrName="$ACR_NAME" \
    githubToken="$GITHUB_TOKEN" \
    contentAgentImage="$LOGIN_SERVER/moodframe-content:lab1" \
    imageAgentImage="$LOGIN_SERVER/moodframe-image:lab1" \
    backendImage="$LOGIN_SERVER/moodframe-api:lab1" \
    frontendImage="$LOGIN_SERVER/moodframe-web:lab1"
```

The Agent Card must advertise its Azure address. Update both agents:

```bash
for AGENT in "${PREFIX}-content" "${PREFIX}-image"; do
  FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "$AGENT" \
    --query properties.configuration.ingress.fqdn -o tsv)"
  az containerapp update -g "$RESOURCE_GROUP" -n "$AGENT" \
    --set-env-vars "AGENT_PUBLIC_URL=https://${FQDN}/"
done
```

Save the public application URL:

```bash
FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --query properties.configuration.ingress.fqdn -o tsv)"
set_env_value ACA_FRONTEND_URL "https://$FQDN"
```

## Exercise 4: Call the cloud application

Call the same API contract used locally, now through the frontend reverse proxy:

```bash
curl -X POST "$ACA_FRONTEND_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"emoji":"🌙","mood":"dreamy","language":"en"}'
```

List the deployment:

```bash
az containerapp list -g "$RESOURCE_GROUP" \
  --query "[?starts_with(name, '$PREFIX')].{name:name,running:properties.runningStatus,external:properties.configuration.ingress.external}" \
  -o table
```

Open `$ACA_FRONTEND_URL`, generate a MoodFrame, and download the PNG.

## Check your work

- Four apps report `Running`.
- Only `${PREFIX}-web` has external ingress.
- The API response contains `post`, `art`, and `download_url`.
- The downloaded image contains the caption and hashtags.

## Learn more

- [Azure Container Apps overview](https://learn.microsoft.com/azure/container-apps/overview)
- [Ingress in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/ingress-overview)
- [Azure Container Registry overview](https://learn.microsoft.com/azure/container-registry/container-registry-intro)
- [Deploy Bicep with Azure CLI](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deploy-cli)

