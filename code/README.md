# MoodFrame

MoodFrame is a frontend/backend-separated demo that turns one selected emoji into an Instagram-style social post and a downloadable pixel-polaroid PNG.

Two independently hosted Microsoft Agent Framework (MAF) agents communicate through the A2A protocol:

1. **MoodPost Content Agent** uses the GitHub Copilot SDK provider and `gpt-5.6-sol` to write the caption, hashtags, and a visual hook.
2. **Pixelaroid Image Agent** uses the same model to convert the mood and copy into a constrained pixel-art specification.
3. The FastAPI backend calls both remote A2A endpoints, validates their JSON, and renders the final PNG with Pillow, including the generated caption and hashtags.

## Architecture

```text
HTML/CSS/JS SPA
      |
      v
FastAPI orchestrator
      |
      +-- A2A --> MoodPost Agent container
      |
      +-- A2A --> Pixelaroid Agent container
                         |
                         v
                   Pillow PNG renderer
```

The text model does not claim native image-generation capability. The image agent acts as an art director and returns a safe, typed scene specification; Pillow renders that specification as deterministic pixel art.

## Prerequisites

- Conda environment named `agentdev`
- Python 3.12
- GitHub Copilot CLI installed and authenticated
- An active GitHub Copilot subscription with access to `gpt-5.6-sol`
- Docker Desktop for the container workflow
- Azure CLI, Bicep, `kubectl`, and GitHub CLI for the optional Azure scripts

Authenticate and confirm model access:

```bash
gh auth login
gh auth refresh --scopes copilot
copilot --model gpt-5.6-sol -p "Reply with OK"
```

## Run locally with Conda

```bash
conda activate agentdev
pip install --pre -r requirements.txt
cp .env.example .env
./scripts/run-local.sh
```

Open <http://localhost:8080>. API docs are available at <http://localhost:8000/docs>.

The A2A agent cards are exposed at:

- <http://localhost:5001/.well-known/agent-card.json>
- <http://localhost:5002/.well-known/agent-card.json>

Stop all local processes:

```bash
./scripts/stop-local.sh
```

Logs are written to `.local/logs/`.

## Run with Docker Compose

Docker must be running. Export a GitHub token authorized for Copilot, then start four containers:

```bash
export GITHUB_TOKEN="$(gh auth token)"
docker compose up --build
```

Open <http://localhost:8080>.

## API

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"emoji":"😊","mood":"joyful","language":"en"}'
```

Supported moods are `joyful`, `calm`, `loved`, `dreamy`, `energetic`, and `cozy`. Languages are `en` and `zh`.

## Tests

```bash
conda activate agentdev
python -m pytest -q tests
```

## Azure Container Apps scripts

The repository generates infrastructure and deployment scripts only; it does not deploy automatically.

`infra/aca/deploy.sh` creates ACR, builds the four images with ACR Tasks, provisions a Container Apps environment, and deploys the two agents, API, and frontend.

```bash
export AZURE_LOCATION=eastus2
export RESOURCE_GROUP=rg-moodframe
export PREFIX=moodframe
export GITHUB_TOKEN="$(gh auth token)"
./infra/aca/deploy.sh
```

The GitHub token is passed as a secure Bicep parameter and stored as a Container Apps secret.

## One-hour guided labs

Microsoft Learn-style beginner labs are available in:

- English: [`../labs/en/`](../labs/en/)
- Chinese: [`../labs/cn/`](../labs/cn/)

Start with Lab 0, then complete ACA, AKS, and the Microsoft Entra ID and Microsoft Defender for Cloud security lab.

## Azure Kubernetes Service scripts

`infra/aks/deploy.sh` provisions ACR and AKS with Azure CNI Overlay, Cilium, OIDC, workload identity, and autoscaling. It then builds the images and applies the Kubernetes manifests.

```bash
export AZURE_LOCATION=eastus2
export RESOURCE_GROUP=rg-moodframe-aks
export PREFIX=moodframe
export GITHUB_TOKEN="$(gh auth token)"
./infra/aks/deploy.sh
```

The generated `infra/aks/rendered.yaml` is ignored by Git because it contains environment-specific image names. The GitHub token is created directly as a Kubernetes Secret and is never written to the rendered manifest.

## Project layout

| Path | Purpose |
|---|---|
| `agents/content_agent` | MAF GitHub Copilot social-copy A2A service |
| `agents/image_agent` | MAF GitHub Copilot pixel-art-director A2A service |
| `agents/common/server.py` | Shared A2A hosting adapter |
| `backend` | FastAPI orchestration, validation, and PNG rendering |
| `frontend` | Instagram-inspired HTML5/CSS3/JavaScript SPA |
| `infra/aca` | Azure Container Apps Bicep and deployment script |
| `infra/aks` | AKS Bicep, Kubernetes manifests, and deployment script |

## Security notes

- The agents receive no shell, file, or URL tools.
- Do not commit `.env`, tokens, or rendered Kubernetes secrets.
- For production, place an authentication layer in front of the API and agent endpoints, restrict CORS, use private ingress where appropriate, and rotate the GitHub token regularly.
