# Lab 2: Scale the MoodFrame platform with AKS

**Duration:** 20 minutes  
**Level:** Beginner  
**Technology:** Azure Kubernetes Service, Kubernetes, Azure CNI, Microsoft Entra integration

## The story

The public preview is successful. The platform team now wants Kubernetes APIs, explicit workload scheduling, namespaces, health probes, service objects, and the ability to apply organization-wide policies. You will deploy the same application images to AKS without rewriting the app.

## Technology introduction

**Azure Kubernetes Service (AKS)** provides a managed Kubernetes control plane while the team controls Kubernetes workloads and configuration.

MoodFrame uses:

- Deployments for the four workloads.
- ClusterIP Services for the API and A2A agents.
- A LoadBalancer Service for the frontend.
- Readiness probes for safe traffic routing.
- Azure CNI Overlay and Cilium for scalable networking and policy.
- Microsoft Entra ID and Azure RBAC for cluster access.
- OIDC and Workload Identity for future secretless Azure access.

## Why this technology?

AKS is selected for the second stage because the team now needs:

- Kubernetes-native deployment and service primitives.
- More control over networking, scaling, policies, and operations.
- A portable platform for additional agents and services.
- Enterprise identity integration at the cluster control plane.

ACA remains the simpler option for the preview; AKS demonstrates when deeper orchestration control is valuable.

## Exercise 1: Create the cluster

```bash
cd code
source scripts/load-env.sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

```bash
az deployment group create \
  -g "$RESOURCE_GROUP" \
  -f infra/aks/main.bicep \
  -p \
    acrName="$ACR_NAME" \
    clusterName="$AKS_CLUSTER_NAME" \
    workspaceName="$LOG_ANALYTICS_WORKSPACE" \
    tenantId="$AZURE_TENANT_ID"
```

Grant your signed-in identity access to the Kubernetes data plane:

```bash
AKS_ID="$(az aks show -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" --query id -o tsv)"
USER_ID="$(az ad signed-in-user show --query id -o tsv)"
az role assignment create \
  --assignee-object-id "$USER_ID" \
  --assignee-principal-type User \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "$AKS_ID"
```

## Exercise 2: Connect to Kubernetes

```bash
az aks get-credentials -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" --overwrite-existing
kubectl get nodes
```

Create a namespace and provide the Copilot token to the two agent Pods:

```bash
kubectl create namespace moodframe --dry-run=client -o yaml | kubectl apply -f -
kubectl -n moodframe create secret generic copilot-auth \
  --from-literal=github-token="$GITHUB_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Exercise 3: Deploy the existing images

Render the environment-specific ACR address and the `lab1` image version:

```bash
LOGIN_SERVER="$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)"
sed \
  -e "s|__LOGIN_SERVER__|$LOGIN_SERVER|g" \
  -e "s|__AGENT_TAG__|lab1|g" \
  -e "s|__API_TAG__|lab1|g" \
  -e "s|__WEB_TAG__|lab1|g" \
  infra/aks/k8s.yaml > infra/aks/rendered.yaml
kubectl apply -f infra/aks/rendered.yaml
```

Wait for each workload:

```bash
kubectl -n moodframe rollout status deployment/content-agent --timeout=5m
kubectl -n moodframe rollout status deployment/image-agent --timeout=5m
kubectl -n moodframe rollout status deployment/backend --timeout=5m
kubectl -n moodframe rollout status deployment/frontend --timeout=5m
```

## Exercise 4: Call the AKS application

```bash
kubectl -n moodframe get pods,services
FRONTEND_IP="$(kubectl -n moodframe get service frontend \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
set_env_value AKS_FRONTEND_URL "http://$FRONTEND_IP"
```

Call the FastAPI flow through the AKS LoadBalancer:

```bash
curl -X POST "$AKS_FRONTEND_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"emoji":"☕","mood":"cozy","language":"en"}'
```

Inspect one agent's health and logs:

```bash
kubectl -n moodframe get deployment content-agent
kubectl -n moodframe logs deployment/content-agent --tail=30
```

## Check your work

- All Pods are `Running` and ready.
- Only the frontend Service is `LoadBalancer`.
- The same API contract works without changing application code.
- AKS reports managed Entra authentication, Azure RBAC, OIDC, and Workload Identity.

## Learn more

- [What is AKS?](https://learn.microsoft.com/azure/aks/what-is-aks)
- [Core Kubernetes concepts for AKS](https://learn.microsoft.com/azure/aks/concepts-clusters-workloads)
- [Azure CNI Overlay](https://learn.microsoft.com/azure/aks/azure-cni-overlay)
- [Microsoft Entra authentication for AKS](https://learn.microsoft.com/azure/aks/entra-id-control-plane-authentication)
- [Workload Identity on AKS](https://learn.microsoft.com/azure/aks/workload-identity-overview)

