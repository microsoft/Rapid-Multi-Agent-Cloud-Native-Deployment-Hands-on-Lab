# 快速部署多智能体云原生应用动手实验

本仓库是一套具有连续故事线的一小时入门实验：你将帮助 MoodFrame 团队，把一个“选择 Emoji、分享心情、生成像素拍立得”的 Agent 小应用从开发者电脑逐步部署到 Azure。

## 项目架构

MoodFrame 采用前后端分离架构。用户选择 Emoji 后，FastAPI 通过 A2A 协议调用两个独立部署的 Microsoft Agent Framework Agent。两个 Agent 均通过 GitHub Copilot SDK 使用 `gpt-5.6-sol`；Pillow 根据图片 Agent 返回的结构化艺术规格生成像素拍立得 PNG，并将文案和 Hashtag 一起写入图片。

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                用户体验层                                    │
│  浏览器 → 选择 Emoji → Instagram 风格 SPA → 预览并下载 PNG                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ HTTPS
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                                前端应用层                                    │
│  moodframe-web                                                              │
│  HTML5 + CSS3 + JavaScript SPA │ Nginx 反向代理                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ /api/*
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                                后端应用层                                    │
│  moodframe-api                                                              │
│  Python FastAPI 编排 │ JSON 校验 │ Pillow PNG 渲染                          │
└───────────────────────┬─────────────────────────┬───────────────────────────┘
                        │ A2A                     │ A2A
          ┌─────────────▼─────────────┐  ┌────────▼─────────────────────────┐
          │ moodframe-content         │  │ moodframe-image                 │
          │ MAF 社交文案 Agent        │  │ MAF 像素艺术指导 Agent          │
          │ 生成文案与 Hashtag        │  │ 生成结构化场景规格              │
          └─────────────┬─────────────┘  └────────┬─────────────────────────┘
                        └──────────────┬────────────┘
                                       │ GitHub Copilot SDK
                          ┌────────────▼────────────┐
                          │ GitHub Copilot          │
                          │ 模型：gpt-5.6-sol       │
                          └─────────────────────────┘

┌────────────────────────────── AZURE 部署层 ─────────────────────────────────┐
│                                                                             │
│  Azure Container Registry                                                  │
│  └── 保存 Web、API、文案 Agent、图片 Agent 四个容器镜像                    │
│                                                                             │
│  Lab 1 — Azure Container Apps              Lab 2 — Azure Kubernetes Service│
│  ┌──────────────────────────────┐           ┌──────────────────────────────┐ │
│  │ 外部入口                    │           │ LoadBalancer Service         │ │
│  │ └── moodframe-web           │           │ └── moodframe-web           │ │
│  │ 内部入口                    │           │ ClusterIP Service            │ │
│  │ ├── moodframe-api           │           │ ├── moodframe-api           │ │
│  │ ├── moodframe-content       │           │ ├── moodframe-content       │ │
│  │ └── moodframe-image         │           │ └── moodframe-image         │ │
│  │ 托管身份 → ACR             │           │ Kubelet 身份 → ACR          │ │
│  └──────────────────────────────┘           └──────────────────────────────┘ │
│                                                                             │
│  Lab 3 — 身份、安全与运维                                                   │
│  ├── Microsoft Entra ID → ACA 用户登录 + AKS 管理员身份                    │
│  ├── Microsoft Defender for Cloud → AKS 与容器安全监控                     │
│  └── Log Analytics → Container Apps 与 AKS 运行遥测                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 应用组件 | 容器 | ACA 对应方式 | AKS 对应方式 | 支撑技术 |
|---|---|---|---|---|
| Web SPA | `moodframe-web` | 外部入口 | LoadBalancer Service | Nginx、Entra 内置身份验证 |
| API 与 PNG 渲染 | `moodframe-api` | 内部入口 | ClusterIP Service | FastAPI、Pillow |
| 社交文案 Agent | `moodframe-content` | 内部 A2A 服务 | ClusterIP A2A Service | MAF、GitHub Copilot SDK |
| 像素艺术指导 Agent | `moodframe-image` | 内部 A2A 服务 | ClusterIP A2A Service | MAF、GitHub Copilot SDK |
| 容器镜像 | 全部四个容器 | 通过托管身份拉取 | 通过 Kubelet 身份拉取 | Azure Container Registry |
| 安全与遥测 | 整体工作负载 | Entra ID、Log Analytics | Entra ID、Defender、Log Analytics | Azure 平台服务 |

### 仓库目录

```text
.
├── code/
│   ├── agents/          # 文案与图片 MAF A2A Agent
│   ├── backend/         # FastAPI 编排与 PNG 渲染
│   ├── frontend/        # HTML5/CSS3/JavaScript SPA
│   ├── infra/
│   │   ├── aca/         # Container Apps Bicep 与部署脚本
│   │   ├── aks/         # AKS Bicep 与 Kubernetes 清单
│   │   └── security/    # Entra ID 与 Defender 脚本
│   ├── scripts/         # 本地环境脚本
│   └── tests/           # Python 测试
├── labs/
│   ├── en/              # 英文实验
│   └── cn/              # 中文实验
└── README.md
```

## 实验路线

| 实验 | 故事阶段 | 时间 |
|---|---|---:|
| [Lab 0](labs/cn/00-prepare-your-environment.md) | 加入 MoodFrame 团队并准备开发环境 | 10 分钟 |
| [Lab 1](labs/cn/01-deploy-to-aca.md) | 使用 Azure Container Apps 发布首个云端版本 | 15 分钟 |
| [Lab 2](labs/cn/02-deploy-to-aks.md) | 使用 AKS 获得 Kubernetes 编排能力 | 20 分钟 |
| [Lab 3](labs/cn/03-secure-with-entra-and-defender.md) | 添加身份认证与云原生安全保护 | 15 分钟 |

应用代码、测试和部署脚本全部位于 [`code/`](code/)；完成 Lab 0 后，请进入 `code/` 目录执行后续命令。

English version: [README.md](README.md)
