# BL API (FastAPI). Build from repo root:
#   docker build -f apps/api/Dockerfile -t alexsoft-bl-api .
FROM python:3.12-slim-bookworm

WORKDIR /repo
COPY apps/api /repo/apps/api
WORKDIR /repo/apps/api

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

# Inside the compose network listen on all interfaces; host bind stays 127.0.0.1 via ports.
ENV BL_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8100
CMD ["python", "-m", "alexsoft_api"]
