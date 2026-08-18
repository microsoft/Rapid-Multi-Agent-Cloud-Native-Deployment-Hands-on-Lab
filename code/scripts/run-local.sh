#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

eval "$(conda shell.bash hook)"
conda activate agentdev

mkdir -p .local/logs generated
export GITHUB_COPILOT_MODEL="${GITHUB_COPILOT_MODEL:-gpt-5.6-sol}"
export CONTENT_AGENT_URL="http://localhost:5001"
export IMAGE_AGENT_URL="http://localhost:5002"

start_service() {
  local name="$1"
  shift
  "$@" >".local/logs/${name}.log" 2>&1 &
  echo "$!" >".local/${name}.pid"
}

start_service content-agent uvicorn agents.content_agent.app:app --host 127.0.0.1 --port 5001
start_service image-agent uvicorn agents.image_agent.app:app --host 127.0.0.1 --port 5002
start_service backend uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
start_service frontend python -m http.server 8080 --directory frontend

echo "MoodFrame started:"
echo "  Frontend:      http://localhost:8080"
echo "  Backend:       http://localhost:8000/docs"
echo "  Content agent: http://localhost:5001/.well-known/agent-card.json"
echo "  Image agent:   http://localhost:5002/.well-known/agent-card.json"
echo "Logs are in .local/logs/. Run scripts/stop-local.sh to stop all services."

