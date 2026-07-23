FROM python:3.12.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY logger.py .

ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA

RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser

EXPOSE 3003

CMD ["python", "app.py"]
