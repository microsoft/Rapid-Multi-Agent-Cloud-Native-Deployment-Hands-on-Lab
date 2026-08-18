FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --pre -r requirements.txt
COPY agents ./agents
EXPOSE 5001
CMD ["uvicorn", "agents.content_agent.app:app", "--host", "0.0.0.0", "--port", "5001"]
