# Lab 1：使用 Azure Container Apps 发布 MoodFrame

**预计时间：**15 分钟  
**难度：**入门  
**技术：**Azure Container Apps、Azure Container Registry、Bicep

## 故事背景

MoodFrame 产品负责人希望今天就能获得一个公开预览版本。团队已经有四个容器，但暂时不想管理虚拟机或 Kubernetes。两个 Agent 和后端必须保持私有，只有 Web 页面可以让用户访问。

## 技术介绍

**Azure Container Apps（ACA）**是无服务器容器平台。它提供 HTTPS 入口、服务发现、版本、日志和自动扩缩容，团队无需维护 Kubernetes 控制平面。

**Azure Container Registry（ACR）**用于保存四个私有镜像。**ACR Tasks** 在 Azure 中构建镜像，不依赖学员电脑的 CPU 架构。

**Bicep** 将 Azure 资源定义为可重复部署的基础设施即代码。

## 为什么选择 ACA

MoodFrame 的第一个云端版本适合 ACA，因为：

- 应用已经容器化。
- 服务通过 HTTP 和私有服务调用进行通信。
- 团队需要快速发布并减少运维。
- 当前不需要直接操作 Kubernetes API。

## 目标架构

```text
Internet
   |
ACA 前端（外部入口）
   |
ACA FastAPI（内部入口）
   |----------------|
内容 Agent       图片 Agent
     （内部 A2A 服务）
```

## 练习 1：加载实验配置

```bash
cd code
source scripts/load-env.sh
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
set_env_value GITHUB_TOKEN "$(gh auth token)"
```

## 练习 2：在 Azure 中构建四个镜像

创建 ACR：

```bash
az deployment group create \
  -g "$RESOURCE_GROUP" \
  -f infra/aca/registry.bicep \
  -p acrName="$ACR_NAME"
```

构建统一的 `lab1` 版本：

```bash
az acr build -r "$ACR_NAME" -t moodframe-content:lab1 -f agents/content_agent/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-image:lab1 -f agents/image_agent/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-api:lab1 -f backend/Dockerfile .
az acr build -r "$ACR_NAME" -t moodframe-web:lab1 -f frontend/Dockerfile .
LOGIN_SERVER="$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)"
```

## 练习 3：部署 Container Apps

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

Agent Card 需要公开自己的 Azure 内部地址：

```bash
for AGENT in "${PREFIX}-content" "${PREFIX}-image"; do
  FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "$AGENT" \
    --query properties.configuration.ingress.fqdn -o tsv)"
  az containerapp update -g "$RESOURCE_GROUP" -n "$AGENT" \
    --set-env-vars "AGENT_PUBLIC_URL=https://${FQDN}/"
done
```

保存公网地址：

```bash
FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "${PREFIX}-web" \
  --query properties.configuration.ingress.fqdn -o tsv)"
set_env_value ACA_FRONTEND_URL "https://$FQDN"
```

## 练习 4：调用云端应用

使用与本地相同的 API 契约，通过前端反向代理调用：

```bash
curl -X POST "$ACA_FRONTEND_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"emoji":"🌙","mood":"dreamy","language":"zh"}'
```

查看部署状态：

```bash
az containerapp list -g "$RESOURCE_GROUP" \
  --query "[?starts_with(name, '$PREFIX')].{name:name,running:properties.runningStatus,external:properties.configuration.ingress.external}" \
  -o table
```

打开 `$ACA_FRONTEND_URL`，生成 MoodFrame 并下载 PNG。

## 检查结果

- 四个应用均为 `Running`。
- 只有 `${PREFIX}-web` 使用外部入口。
- API 返回 `post`、`art` 和 `download_url`。
- 下载图片包含文案和 Hashtag。

## MS Learn 延伸学习

- [Azure Container Apps 概述](https://learn.microsoft.com/azure/container-apps/overview)
- [Container Apps 入口](https://learn.microsoft.com/azure/container-apps/ingress-overview)
- [Azure Container Registry 概述](https://learn.microsoft.com/azure/container-registry/container-registry-intro)
- [使用 Azure CLI 部署 Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deploy-cli)

