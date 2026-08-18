# Lab 2：使用 AKS 扩展 MoodFrame 平台

**预计时间：**20 分钟  
**难度：**入门  
**技术：**Azure Kubernetes Service、Kubernetes、Azure CNI、Microsoft Entra 集成

## 故事背景

MoodFrame 预览版本获得了积极反馈。平台团队希望使用 Kubernetes API，明确控制工作负载调度、命名空间、健康探针、Service 和组织策略。你将把同一组镜像部署到 AKS，而不修改应用代码。

## 技术介绍

**Azure Kubernetes Service（AKS）**提供托管 Kubernetes 控制平面，同时允许团队控制 Kubernetes 工作负载和配置。

MoodFrame 使用：

- Deployment 运行四个工作负载。
- ClusterIP Service 连接后端和 A2A Agent。
- LoadBalancer Service 发布前端。
- Readiness Probe 保证流量只进入健康 Pod。
- Azure CNI Overlay 与 Cilium 提供网络和策略能力。
- Microsoft Entra ID 与 Azure RBAC 管理集群访问。
- OIDC 与 Workload Identity 为后续无密码 Azure 访问做准备。

## 为什么选择 AKS

第二阶段选择 AKS，是因为团队开始需要：

- Kubernetes 原生 Deployment 与 Service。
- 更强的网络、扩缩容、策略和运维控制。
- 可以继续增加 Agent 与微服务的平台。
- 企业身份与集群控制面的集成。

ACA 仍然是预览环境更简单的选择；AKS 展示了何时需要更深度的编排能力。

## 练习 1：创建集群

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

授予当前登录身份 Kubernetes 数据平面权限：

```bash
AKS_ID="$(az aks show -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" --query id -o tsv)"
USER_ID="$(az ad signed-in-user show --query id -o tsv)"
az role assignment create \
  --assignee-object-id "$USER_ID" \
  --assignee-principal-type User \
  --role "Azure Kubernetes Service RBAC Cluster Admin" \
  --scope "$AKS_ID"
```

## 练习 2：连接 Kubernetes

```bash
az aks get-credentials -g "$RESOURCE_GROUP" -n "$AKS_CLUSTER_NAME" --overwrite-existing
kubectl get nodes
```

创建命名空间，并向两个 Agent Pod 提供 Copilot Token：

```bash
kubectl create namespace moodframe --dry-run=client -o yaml | kubectl apply -f -
kubectl -n moodframe create secret generic copilot-auth \
  --from-literal=github-token="$GITHUB_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
```

## 练习 3：部署现有镜像

将 ACR 地址和 `lab1` 镜像版本写入渲染后的清单：

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

等待工作负载：

```bash
kubectl -n moodframe rollout status deployment/content-agent --timeout=5m
kubectl -n moodframe rollout status deployment/image-agent --timeout=5m
kubectl -n moodframe rollout status deployment/backend --timeout=5m
kubectl -n moodframe rollout status deployment/frontend --timeout=5m
```

## 练习 4：调用 AKS 应用

```bash
kubectl -n moodframe get pods,services
FRONTEND_IP="$(kubectl -n moodframe get service frontend \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
set_env_value AKS_FRONTEND_URL "http://$FRONTEND_IP"
```

通过 AKS LoadBalancer 调用 FastAPI：

```bash
curl -X POST "$AKS_FRONTEND_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"emoji":"☕","mood":"cozy","language":"zh"}'
```

查看 Agent 健康状态与日志：

```bash
kubectl -n moodframe get deployment content-agent
kubectl -n moodframe logs deployment/content-agent --tail=30
```

## 检查结果

- 所有 Pod 均为 `Running` 且 Ready。
- 只有前端 Service 是 `LoadBalancer`。
- 未修改应用代码即可使用同一个 API 契约。
- AKS 已启用托管 Entra 身份验证、Azure RBAC、OIDC 和 Workload Identity。

## MS Learn 延伸学习

- [什么是 AKS](https://learn.microsoft.com/azure/aks/what-is-aks)
- [AKS 核心 Kubernetes 概念](https://learn.microsoft.com/azure/aks/concepts-clusters-workloads)
- [Azure CNI Overlay](https://learn.microsoft.com/azure/aks/azure-cni-overlay)
- [AKS 的 Microsoft Entra 身份验证](https://learn.microsoft.com/azure/aks/entra-id-control-plane-authentication)
- [AKS Workload Identity](https://learn.microsoft.com/azure/aks/workload-identity-overview)

