# Lab 3：保护 MoodFrame 社交社区

**预计时间：**15 分钟  
**难度：**入门  
**技术：**Microsoft Entra ID、Container Apps 身份验证、Microsoft Defender for Cloud

## 故事背景

MoodFrame 即将进入公司内部试用。团队必须保证只有员工能够访问 ACA 版本，集群管理员使用组织身份登录，并且安全团队可以持续发现容器风险。

## 技术介绍

**Microsoft Entra ID** 为应用和 AKS 控制平面提供身份。Azure Container Apps 内置身份验证可以完成 OAuth/OpenID Connect 流程，无需在 SPA 或 FastAPI 中编写登录代码。

**Microsoft Defender for Cloud** 持续评估云安全状态。Defender for Containers 提供 Kubernetes 和容器工作负载建议，并提供运行时安全信号。

## 为什么选择这些技术

- Entra ID 提供单租户企业登录。
- Container Apps 内置身份验证减少自定义安全代码。
- AKS 托管 Entra 集成让日常管理不依赖 Kubernetes 本地账号。
- Defender for Containers 将集群接入 Azure 安全建议与监控。

> Defender for Containers 在适用试用期结束后会产生费用。

## 练习 1：在 Microsoft Entra ID 注册 MoodFrame

```bash
cd code
source scripts/load-env.sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

根据 ACA 前端生成回调地址：

```bash
FRONTEND_FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --query properties.configuration.ingress.fqdn -o tsv)"
REDIRECT_URI="https://${FRONTEND_FQDN}/.auth/login/aad/callback"
```

创建单租户应用和凭据：

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

## 练习 2：保护 ACA 前端

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

## 身份验证如何被调用

访问应用登录地址，ACA 会拦截请求并启动 Entra 登录流程：

```bash
open "$ACA_FRONTEND_URL/.auth/login/aad"
```

Linux 用户可以在浏览器中打开输出地址。也可以查看 HTTP 跳转：

```bash
curl -I "$ACA_FRONTEND_URL/.auth/login/aad"
```

登录成功后，浏览器获得 ACA 身份验证 Cookie，并可以继续调用 `/api/generate`。

## 练习 3：启用 Defender for Containers

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

## 如何查询 Defender 状态

```bash
az security pricing show -n Containers \
  --query '{plan:name,tier:pricingTier}' -o table

az aks show -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" \
  --query '{entra:aadProfile.managed,azureRbac:aadProfile.enableAzureRbac,defender:securityProfile.defender.securityMonitoring.enabled}' \
  -o table
```

在 Azure 门户打开 **Microsoft Defender for Cloud > Recommendations**，按 AKS 集群名称筛选。

## 检查结果

- ACA 登录地址跳转到 `login.microsoftonline.com`。
- Entra 应用为单租户。
- AKS 使用托管 Entra 身份验证和 Azure RBAC。
- Containers 计划为 `Standard`。
- AKS Defender 安全监控已启用。

## MS Learn 延伸学习

- [Microsoft 标识平台概述](https://learn.microsoft.com/entra/identity-platform/v2-overview)
- [Azure Container Apps 身份验证](https://learn.microsoft.com/azure/container-apps/authentication)
- [AKS 的 Microsoft Entra 身份验证](https://learn.microsoft.com/azure/aks/entra-id-control-plane-authentication)
- [Microsoft Defender for Containers](https://learn.microsoft.com/azure/defender-for-cloud/defender-for-containers-introduction)
- [Defender for Cloud 安全建议](https://learn.microsoft.com/azure/defender-for-cloud/review-security-recommendations)

