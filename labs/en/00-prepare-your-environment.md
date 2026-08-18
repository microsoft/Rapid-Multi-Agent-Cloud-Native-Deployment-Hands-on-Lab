# Lab 0: Join the MoodFrame team

**Duration:** 10 minutes  
**Level:** Beginner

## The story

MoodFrame is a small social application for sharing feelings. A user selects an emoji, a content agent writes a short social post, and a second agent turns the mood and post into a downloadable pixel-polaroid image.

The prototype works locally. Your role is to prepare a repeatable lab environment so the team can deploy it to Azure without copying secrets into source code.

## What you will prepare

- Git and the workshop repository.
- Conda environment `agentdev` with Python 3.12.
- Azure CLI with Bicep.
- GitHub CLI and GitHub Copilot CLI authentication.
- `kubectl`, Docker, and the project `.env`.

## Application architecture

```text
HTML/CSS/JavaScript SPA
          |
          v
   FastAPI orchestrator
      |             |
      v             v
Content A2A     Pixel A2A
Agent           Agent
      \             /
       GitHub Copilot
        gpt-5.6-sol
```

The application source, tests, Dockerfiles, Bicep, Kubernetes manifests, and deployment scripts are all in the `code/` folder.

## Exercise 1: Clone the workshop

```bash
git clone <repository-url> moodframe-azure-lab
cd moodframe-azure-lab
ls
```

Confirm that the repository contains both folders:

```text
code/
labs/
```

Enter the application folder. Run every remaining command in this workshop from here unless a lab says otherwise.

```bash
cd code
```

## Exercise 2: Install and verify the tools

Install the tools with the package manager for your operating system:

- [Git](https://git-scm.com/downloads)
- [Miniforge or Conda](https://github.com/conda-forge/miniforge)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [GitHub CLI](https://cli.github.com/)
- [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker Desktop](https://docs.docker.com/desktop/)

Verify the command-line tools:

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

## Exercise 3: Create the Python environment

```bash
conda create -n agentdev python=3.12 -y
conda activate agentdev
pip install --pre -r requirements.txt
python -m pytest -q tests
```

## Exercise 4: Sign in

```bash
az login
gh auth login
gh auth refresh --scopes copilot
copilot --model gpt-5.6-sol -p "Reply with READY"
```

## Exercise 5: Configure `.env`

```bash
cp .env.example .env
source scripts/load-env.sh
```

Open `.env` and set the Azure subscription, resource group, region, and resource names for your environment. Then store the Copilot-enabled token:

```bash
set_env_value GITHUB_TOKEN "$(gh auth token)"
```

> `.env` is ignored by Git. Never commit it or paste its secret values into lab reports.

## Exercise 6: Understand how the app is called

Start the local services:

```bash
./scripts/run-local.sh
```

Call the FastAPI orchestration endpoint:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"emoji":"😊","mood":"joyful","language":"en"}'
```

Open <http://localhost:8080>, generate an image, and stop the services:

```bash
./scripts/stop-local.sh
```

## Check your work

- The Python test suite passes.
- The Copilot CLI returns `READY`.
- `.env` exists only inside `code/`.
- The local API returns social copy and a `.png` download URL.

## Learn more

- [Azure CLI overview](https://learn.microsoft.com/cli/azure/what-is-azure-cli)
- [What is Bicep?](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview)
- [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)
- [Python environments with Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
