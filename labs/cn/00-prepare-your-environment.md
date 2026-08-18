# Lab 0：加入 MoodFrame 团队

**预计时间：**10 分钟  
**难度：**入门

## 故事背景

MoodFrame 是一个分享心情的社交 Agent 小应用。用户选择一个 Emoji 后，内容 Agent 会生成社交文案，另一个 Agent 会结合心情和文案，制作一张可以下载的像素拍立得图片。

原型已经能够在开发者电脑上运行。你将先准备一套可重复使用的实验环境，让团队能够安全地把应用部署到 Azure，而不是把 Token 和密码写进代码。

## 你将准备什么

- Git 与实验仓库。
- Python 3.12 和 Conda 环境 `agentdev`。
- Azure CLI 与 Bicep。
- GitHub CLI 与 GitHub Copilot CLI 登录。
- `kubectl`、Docker 和项目 `.env`。

## 应用架构

```text
HTML/CSS/JavaScript SPA
          |
          v
     FastAPI 编排器
       |           |
       v           v
内容 A2A Agent   像素 A2A Agent
       \           /
        GitHub Copilot
         gpt-5.6-sol
```

应用源码、测试、Dockerfile、Bicep、Kubernetes 清单和部署脚本全部位于 `code/` 文件夹。

## 练习 1：克隆实验仓库

```bash
git clone <repository-url> moodframe-azure-lab
cd moodframe-azure-lab
ls
```

确认仓库包含：

```text
code/
labs/
```

进入应用目录。除非实验特别说明，后续所有命令都在 `code/` 中执行：

```bash
cd code
```

## 练习 2：安装并检查工具

根据你的操作系统安装：

- [Git](https://git-scm.com/downloads)
- [Miniforge 或 Conda](https://github.com/conda-forge/miniforge)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [GitHub CLI](https://cli.github.com/)
- [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker Desktop](https://docs.docker.com/desktop/)

检查命令：

```bash
git --version
conda --version
az version
az bicep version
gh --version
copilot --version
kubectl version --client
docker version
```

## 练习 3：创建 Python 环境

```bash
conda create -n agentdev python=3.12 -y
conda activate agentdev
pip install --pre -r requirements.txt
python -m pytest -q tests
```

## 练习 4：登录 Azure 与 GitHub

```bash
az login
gh auth login
gh auth refresh --scopes copilot
copilot --model gpt-5.6-sol -p "Reply with READY"
```

## 练习 5：配置 `.env`

```bash
cp .env.example .env
source scripts/load-env.sh
```

打开 `.env`，设置实验使用的 Azure 订阅、资源组、区域与资源名称。然后保存具备 Copilot 权限的 Token：

```bash
set_env_value GITHUB_TOKEN "$(gh auth token)"
```

> `.env` 已被 Git 忽略。不要提交该文件，也不要在实验报告中粘贴其中的 Secret。

## 练习 6：了解应用如何被调用

启动本地服务：

```bash
./scripts/run-local.sh
```

调用 FastAPI 编排接口：

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"emoji":"😊","mood":"joyful","language":"zh"}'
```

打开 <http://localhost:8080> 生成图片，然后停止服务：

```bash
./scripts/stop-local.sh
```

## 检查结果

- Python 测试套件通过。
- Copilot CLI 返回 `READY`。
- `.env` 只存在于 `code/`。
- 本地 API 返回社交文案和 `.png` 下载地址。

## MS Learn 延伸学习

- [Azure CLI 概述](https://learn.microsoft.com/cli/azure/what-is-azure-cli)
- [什么是 Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview)
- [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)
- [使用 Conda 管理环境](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
