# MoodFrame Azure Deployment Plan

**Status:** Deployed

## 1. Request

- Deploy the existing MoodFrame application to Azure.
- Deployment order: Azure Container Apps, Azure Kubernetes Service, then identity and security hardening with Microsoft Entra ID and Microsoft Defender for Cloud.
- Target existing resource group: `rg-kinfey`.
- Target AKS cluster name: `kinfey-mood-aks`.
- Produce a beginner-friendly Microsoft Learn-style lab that can be completed in under one hour.
- English labs: `labs/en/`.
- Chinese labs: `labs/cn/`.
- Keep runtime configuration in `code/.env`; lab instructions use the existing project code directly.

## 2. Workspace Analysis

- **Mode:** Modify and deploy an existing application.
- **Application:** Four-container MoodFrame application:
  - MAF GitHub Copilot content A2A agent.
  - MAF GitHub Copilot pixel-art A2A agent.
  - Python FastAPI orchestrator and PNG renderer.
  - HTML5/CSS3/JavaScript SPA served by Nginx.
- **Deployment method:** Azure CLI + Bicep + ACR Tasks.
- **Application root:** `code/`.
- **Local configuration:** `code/.env`, excluded from Git.
- **Lab style:** Microsoft Learn-inspired, beginner-level, command-by-command, under 60 minutes total.

## 3. Azure Context

- **Subscription:** CloudNative (`4498459e-01d5-4a3f-b07e-8f1f36598c16`) — user confirmed.
- **Tenant:** `a1657432-4206-4c94-9e8d-57b65b539fd5`.
- **Resource group:** Existing `rg-kinfey`.
- **Location:** Sweden Central — user confirmed and matches the resource group.
- **AKS cluster:** `kinfey-mood-aks` does not currently exist.
- **Effective access:** Owner inherited through a Microsoft Entra group.
- **Resource providers:** Microsoft.App, Microsoft.ContainerService, and Microsoft.Security are registered.
- **Capacity:** 76 regional vCPUs remain; Standard DSv5 family has 344 vCPUs remaining; Standard public IPv4 has 987 remaining.
- **Name checks:** `kinfeymoodacr` and planned Container App names are available.

## 4. Architecture and Deployment Order

### Lab 1 — Azure Container Apps

1. Create shared ACR `kinfeymoodacr`.
2. Build four images remotely with ACR Tasks.
3. Create Log Analytics and Container Apps environment `kinfey-mood-aca-env`.
4. Deploy internal content agent, image agent, and API Container Apps.
5. Deploy external frontend Container App and verify generation/download.

### Lab 2 — Azure Kubernetes Service

1. Create AKS Standard cluster `kinfey-mood-aks`.
2. Use Azure CNI Overlay, Cilium, OIDC issuer, Workload Identity, managed Microsoft Entra integration, Azure RBAC, Azure Policy, and autoscaling.
3. Reuse `kinfeymoodacr`.
4. Deploy the same four existing images with Kubernetes manifests.
5. Verify the LoadBalancer endpoint and A2A services.

### Lab 3 — Microsoft Entra ID and Microsoft Defender for Cloud

1. Create single-tenant app registration `kinfey-moodframe-lab`.
2. Configure Container Apps built-in authentication on the public frontend; no application authentication code changes.
3. Keep backend and both A2A agents internal to the Container Apps environment.
4. Confirm AKS Microsoft Entra control-plane authentication and Azure RBAC.
5. Enable the paid Microsoft Defender for Containers plan at subscription scope.
6. Enable AKS Defender sensor/security monitoring and inspect Defender recommendations.

Lab 0 plus the three deployment labs target 10, 15, 20, and 15 minutes respectively.

## 5. Recipe

- **Type:** Bicep with Azure CLI orchestration.
- **Reason:** Existing Bicep files and deployment scripts are already present; this is easier to teach manually than AZD for a one-hour introductory lab.
- **Deployment order:** ACA → AKS → Entra ID and Defender.
- **No destructive operations:** Existing resources in `rg-kinfey` remain untouched.
- **Shared resources:** ACR and Log Analytics are reused by ACA and AKS to reduce time and cost.

## 6. Artifacts and Documentation

- Update `code/.env.example` and create local `code/.env` with Azure resource names and non-secret settings.
- Update ACA Bicep/script for fixed lab names, internal service ingress, and shared ACR.
- Update AKS Bicep/script to reuse ACR and enable Entra/Defender-ready cluster features.
- Add Entra ID and Defender configuration/verification scripts.
- Create:
  - `labs/en/00-prepare-your-environment.md`
  - `labs/en/01-deploy-to-aca.md`
  - `labs/en/02-deploy-to-aks.md`
  - `labs/en/03-secure-with-entra-and-defender.md`
  - `labs/cn/00-prepare-your-environment.md`
  - `labs/cn/01-deploy-to-aca.md`
  - `labs/cn/02-deploy-to-aks.md`
  - `labs/cn/03-secure-with-entra-and-defender.md`
- Labs use Microsoft Learn conventions: a continuous scenario, technology introductions, selection rationale, invocation examples, estimated duration, exercises, checks, and learning links.

## 7. Validation Proof

Validated on 2026-08-01 before deployment:

- `az bicep build` for `code/infra/aca/registry.bicep`, `code/infra/aca/main.bicep`, and `code/infra/aks/main.bicep`: passed.
- `az deployment group validate` for ACR registry template: passed.
- `az deployment group what-if` for ACA registry/application templates: passed.
- `az deployment group what-if` for AKS template: passed.
- `kubectl apply --dry-run=client --validate=false -f code/infra/aks/rendered.yaml`: passed.
- `cd code && python -m pytest -q tests`: 4 passed.
- Shell syntax and frontend JavaScript syntax: passed.
- Azure authentication: CloudNative subscription active.
- GitHub authentication: `copilot` scope added and verified.
- Azure Policy and deny assignment check for `rg-kinfey`: no blocking assignments found.
- Static RBAC verification:
  - ACA user-assigned pull identity receives `AcrPull` scoped to `kinfeymoodacr`.
  - AKS kubelet identity receives `AcrPull` scoped to `kinfeymoodacr`.
  - Current user receives AKS Azure RBAC Cluster Admin at cluster scope during deployment.
- Sweden Central capacity:
  - 76 regional vCPUs available.
  - 344 Standard DSv5 family vCPUs available.
  - 987 Standard public IPv4 addresses available.
  - `Standard_D4ds_v5` has no regional restriction.

## 8. Deployment Results

- ACA attempt 1: ACR created; first agent image build failed because `python -m copilot download-runtime` is not an available module entry point in the Linux wheel.
- Remediation: removed the unnecessary command; the installed SDK wheel already contains `copilot/bin/copilot`.
- ACA attempt 2: all four ACR builds succeeded and Bicep deployment ran; local result parsing failed because macOS exposed `python3` but not `python`.
- Remediation: use `python3` and allow `SKIP_BUILD=1` for idempotent deployment completion.
- ACA runtime verification: frontend returned 502.
- Root causes:
  - A2A SDK resolved to 1.1.2 and imported optional `sse_starlette` that was not installed.
  - Nginx did not send TLS SNI to the internal Container Apps backend.
- Remediation: pin `a2a-sdk==1.0.2`, enable `proxy_ssl_server_name`, and deploy a new immutable image tag.
- ACA verification attempt 2: internal TLS succeeded but returned 404 because Nginx forwarded the public frontend `Host` header.
- Remediation: set the upstream `Host` header to the internal API FQDN.
- ACA verification attempt 3: proxying reached FastAPI, but both Agent containers still failed because A2A 1.0.2 server routes import `sse_starlette` without declaring it as a required dependency.
- Remediation: explicitly add `sse-starlette` to application requirements.
- ACA verification attempt 4: A2A request reached the running content agent, but protobuf 6 removed the `FieldDescriptor.label` API used by A2A validation.
- Remediation: pin protobuf 5.29.5, which is within the A2A SDK supported range.
- ACA final verification: passed end-to-end generation and downloaded a valid 640x980 PNG.
- **ACA:** deployed four Container Apps and verified end-to-end generation.
- **ACA frontend:** `https://kinfey-mood-web.agreeablebeach-beb750ba.swedencentral.azurecontainerapps.io`.
- **AKS:** created `kinfey-mood-aks`, deployed all workloads, and verified Chinese generation and PNG download.
- **AKS frontend:** `http://4.166.91.162`.
- **Microsoft Entra ID:** created single-tenant app `kinfey-moodframe-lab` and enabled built-in authentication on the ACA frontend.
- **Microsoft Defender for Cloud:** enabled the `Containers` plan at `Standard` tier and enabled AKS Defender security monitoring.
- **Live RBAC verification:** ACA pull identity and AKS kubelet identity have `AcrPull`; deploying user has AKS RBAC Cluster Admin at cluster scope.

## 9. Cost and Security Notes

- AKS nodes, Container Apps, ACR, and Log Analytics incur Azure usage charges.
- Microsoft Defender for Containers is a paid plan after any applicable trial period.
- The GitHub token and Entra client secret remain in the ignored local `code/.env` or Azure secret stores and are never committed.
- The deployment will not delete or replace existing resources.
