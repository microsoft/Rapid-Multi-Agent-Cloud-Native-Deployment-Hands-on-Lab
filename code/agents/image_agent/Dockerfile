FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --pre -r requirements.txt
COPY agents ./agents
EXPOSE 5002
CMD ["uvicorn", "agents.image_agent.app:app", "--host", "0.0.0.0", "--port", "5002"]
