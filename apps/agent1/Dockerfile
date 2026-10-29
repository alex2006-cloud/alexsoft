# LangGraph Agent Server (Studio API). Build from repo root:
#   docker build -f apps/agent1/Dockerfile -t alexsoft-agent1 .
FROM python:3.12-slim-bookworm

WORKDIR /app
COPY apps/agent1/pyproject.toml apps/agent1/langgraph.json ./
COPY apps/agent1/*.py ./

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir . "langgraph-cli[inmem]"

# langgraph.json points at ../../.env locally; in the image use process env only.
RUN python -c "import json; p='langgraph.json'; d=json.load(open(p)); d.pop('env', None); json.dump(d, open(p,'w'), indent=2)"

ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV LANGSMITH_TRACING=false
ENV LOG_COLOR=false

EXPOSE 2024
# Single worker to fit 6GB VDS with LiteLLM+RAG already running.
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser", "--n-jobs-per-worker", "1"]
