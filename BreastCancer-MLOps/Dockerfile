ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
COPY . .
EXPOSE 8000 8501
