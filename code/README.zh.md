# MoodFrame

MoodFrame 是一个前后端分离的示例应用。用户只需选择一个 Emoji，系统就会生成 Instagram 风格的社交分享文案，以及一张可下载的像素风拍立得 PNG 图片。

系统包含两个通过 A2A 协议通信、独立部署的 Microsoft Agent Framework（MAF）Agent：

1. **MoodPost Content Agent**：通过 GitHub Copilot SDK Provider 和 `gpt-5.6-sol` 生成文案、Hashtag 与视觉提示。
2. **Pixelaroid Image Agent**：结合心情与文案，生成受约束的像素画场景规格。
3. FastAPI 后端依次调用两个远程 A2A Agent，验证 JSON，并使用 Pillow 将生成的文案和 Hashtag 一起渲染到最终 PNG。

## 架构

```text
HTML/CSS/JS SPA
      |
      v
FastAPI 编排服务
      |
      +-- A2A --> MoodPost Agent 容器
      |
      +-- A2A --> Pixelaroid Agent 容器
                         |
                         v
                    Pillow PNG 渲染
```

这里不会把文本模型描述成原生图片生成模型。第二个 Agent 负责艺术指导并输出类型安全的场景规格，Pillow 再将规格确定性地渲染成像素画。

## 前置条件

- 名为 `agentdev` 的 Conda 环境
- Python 3.12
- 已安装并登录 GitHub Copilot CLI
- GitHub Copilot 订阅，并拥有 `gpt-5.6-sol` 模型权限
- 容器运行方式需要 Docker Desktop
- Azure 脚本需要 Azure CLI、Bicep、`kubectl` 和 GitHub CLI

登录并确认模型权限：

```bash
gh auth login
gh auth refresh --scopes copilot
copilot --model gpt-5.6-sol -p "Reply with OK"
```

## 使用 Conda 本地运行

```bash
conda activate agentdev
pip install --pre -r requirements.txt
cp .env.example .env
./scripts/run-local.sh
```

访问 <http://localhost:8080>，FastAPI 文档位于 <http://localhost:8000/docs>。

A2A Agent Card 地址：

- <http://localhost:5001/.well-known/agent-card.json>
- <http://localhost:5002/.well-known/agent-card.json>

停止本地服务：

```bash
./scripts/stop-local.sh
```

日志位于 `.local/logs/`。

## 使用 Docker Compose

请先启动 Docker，并导出具有 Copilot 权限的 GitHub Token：

```bash
export GITHUB_TOKEN="$(gh auth token)"
docker compose up --build
```

访问 <http://localhost:8080>。

## API

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"emoji":"😊","mood":"joyful","language":"zh"}'
```

支持的心情包括：`joyful`、`calm`、`loved`、`dreamy`、`energetic`、`cozy`；语言为 `en` 或 `zh`。

## 测试

```bash
conda activate agentdev
python -m pytest -q tests
```

## Azure Container Apps 脚本

当前仓库只生成基础设施和部署脚本，不会自动执行 Azure 部署。

`infra/aca/deploy.sh` 会创建 ACR，通过 ACR Tasks 构建四个镜像，然后创建 Container Apps 环境并部署两个 Agent、后端和前端。

```bash
export AZURE_LOCATION=eastus2
export RESOURCE_GROUP=rg-moodframe
export PREFIX=moodframe
export GITHUB_TOKEN="$(gh auth token)"
./infra/aca/deploy.sh
```

GitHub Token 通过 Bicep 安全参数传递，并保存为 Container Apps Secret。

## 一小时引导式实验

Microsoft Learn 风格的入门实验位于：

- 英文：[`../labs/en/`](../labs/en/)
- 中文：[`../labs/cn/`](../labs/cn/)

请从 Lab 0 开始，再依次完成 ACA、AKS、Microsoft Entra ID 与 Microsoft Defender for Cloud。

## Azure Kubernetes Service 脚本

`infra/aks/deploy.sh` 会创建 ACR 与 AKS。AKS 配置包括 Azure CNI Overlay、Cilium、OIDC、Workload Identity 和自动扩缩容，随后构建镜像并应用 Kubernetes 清单。

```bash
export AZURE_LOCATION=eastus2
export RESOURCE_GROUP=rg-moodframe-aks
export PREFIX=moodframe
export GITHUB_TOKEN="$(gh auth token)"
./infra/aks/deploy.sh
```

生成的 `infra/aks/rendered.yaml` 包含环境相关镜像名称，因此已加入 Git 忽略列表。GitHub Token 会直接创建为 Kubernetes Secret，不会写入渲染后的清单。

## 目录结构

| 路径 | 作用 |
|---|---|
| `agents/content_agent` | MAF GitHub Copilot 社交文案 A2A 服务 |
| `agents/image_agent` | MAF GitHub Copilot 像素画艺术指导 A2A 服务 |
| `agents/common/server.py` | 共用 A2A Hosting Adapter |
| `backend` | FastAPI 编排、校验与 PNG 渲染 |
| `frontend` | Instagram 风格 HTML5/CSS3/JavaScript SPA |
| `infra/aca` | Azure Container Apps Bicep 与部署脚本 |
| `infra/aks` | AKS Bicep、Kubernetes 清单与部署脚本 |

## 安全说明

- 两个 Agent 均未开放 Shell、文件或 URL 工具。
- 不要提交 `.env`、Token 或包含 Secret 的文件。
- 生产环境应为 API 与 Agent Endpoint 增加身份认证，收紧 CORS，并按需使用私有入口和定期轮换 Token。
