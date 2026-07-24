# Production Service Environment

A production-style microservices environment demonstrating service discovery, reverse proxying, structured JSON logging, distributed request tracing, systemd lifecycle management, and Docker Compose containerization.

> This repository now uses Docker Compose containerization with a GitHub Actions CI/CD pipeline as the primary deployment path (see [For Reviewers](#for-reviewers) and [Container CI/CD Deployment](#container-cicd-deployment) below). The original VM/systemd setup is documented under [Option A](#option-a-vm-with-systemd) for reference.

---

## Table of Contents

1. [For Reviewers](#for-reviewers)
2. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technologies Used](#technologies-used)
4. [Project Structure](#project-structure)
5. [Deployment Options](#deployment-options)
   - [Option A: VM with systemd](#option-a-vm-with-systemd)
   - [Option B: Docker Compose](#option-b-docker-compose)
6. [Peer Review Feedback & Fixes](#peer-review-feedback--fixes)
7. [Logging](#logging)
8. [Troubleshooting](#troubleshooting)

---


---

## Observability Stack

This project includes a full MELT (Metrics, Events, Logs, Traces) observability layer.

### Quick Start

```bash
# Start everything
docker compose up -d

# Access services
curl http://localhost:8080/service-a/health
curl http://localhost:8080/service-a/metrics
curl http://localhost:8080/service-a/greet-service-b
```

Access observability tools:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686

### Grafana Dashboard
- URL: http://localhost:3000
- Login: admin / admin
- Dashboard: "Observability Lab - Service Overview"
- Panels: Service health, request rate, error rate, p95 latency, alert state

### Prometheus
- URL: http://localhost:9090
- Scrapes: service-a:3001, service-b:3002, service-c:3003
- Rules: ServiceDown, HighErrorRate, HighLatency

### Jaeger Tracing
- URL: http://localhost:16686
- Services: service-a, service-b, service-c
- Search by service name to see multi-service request traces

### Logs

```bash
# View structured JSON logs
docker compose logs service-a
docker compose logs service-b
docker compose logs service-c
```

### Load Testing

```bash
# Run k6 load test (normal, stress, failure scenarios)
k6 run scripts/load-test.js
```

### Controlled Failure Endpoints

| Endpoint | Purpose |
|----------|---------|
| /fail | Returns 500 error |
| /slow | Returns 200 after 1-3s delay |

### Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| ServiceDown | up == 0 for 15s | critical |
| HighErrorRate | Error rate > 10% for 30s | warning |
| HighLatency | p95 latency > 1s for 1m | warning |

### Slack Alerting (Alertmanager)

Alerts defined in `alert-rules.yml` are evaluated by Prometheus and routed through
**Alertmanager** to a Slack channel via an incoming webhook.

**One-time setup (per person running the stack):**

1. In Slack, create an [Incoming Webhook](https://api.slack.com/messaging/webhooks) for the channel you want alerts posted to (e.g. `#alerts`). Copy the webhook URL.
2. Copy the template config:
   ```bash
   cp alertmanager/alertmanager.yml.example alertmanager/alertmanager.yml
   ```
3. Edit `alertmanager/alertmanager.yml` and replace the placeholder `api_url` with your real Slack webhook URL.
4. `alertmanager/alertmanager.yml` is gitignored -- it will never be committed, so your webhook URL stays private.
5. Start (or restart) the stack:
   ```bash
   docker compose up -d
   ```

**Verify it works:**

```bash
# Trigger a controlled failure so ServiceDown or HighErrorRate fires
curl http://localhost:8080/service-a/fail
curl http://localhost:8080/service-a/fail
curl http://localhost:8080/service-a/fail

# Check Alertmanager sees it
curl http://localhost:9093/api/v2/alerts
```

Access Alertmanager's UI at http://localhost:9093 to see alert grouping and routing state. Within a few seconds of an alert firing, you should see it posted to your configured Slack channel.

> **Note:** `docker-compose.prod.yml` (used by the CI/CD deployment path) does not currently include Prometheus/Alertmanager/Grafana/Jaeger -- this alerting setup applies to the local dev stack (`docker-compose.yml`). Extending the production compose file to include monitoring is a good next step before relying on this in a deployed environment.

## For Reviewers

This section maps directly to the assignment's peer-review checklist. Each item below can be verified independently in under a few minutes -- no source code trust required.

**Repo:** https://github.com/Bridget-Kathure/production-service-environment
**Docker Hub namespace:** `ainembabazi`

### 1. CI proves code quality before Docker packaging, and failed tests would block merge

Open the [Actions tab](https://github.com/Bridget-Kathure/production-service-environment/actions) and look at any pull request run. You'll see three matrix jobs -- one per service -- each running `pytest` before any Docker build step. A failing test or failing `pip install` fails that job and blocks the rest of the pipeline.

### 2. Images are commit-tagged, pullable, and never `:latest`

Pull the currently published images directly -- no login required:

```bash
docker pull ainembabazi/production-service-environment-service-a:sha-71dd255
docker pull ainembabazi/production-service-environment-service-b:sha-71dd255
docker pull ainembabazi/production-service-environment-service-c:sha-71dd255
```

Tags follow `sha-<short-commit-hash>` exclusively. Check the [workflow file](.github/workflows/container-ci-cd.yml) -- there is no code path that pushes a `latest`, `main`, or `dev` tag.

### 3. Publishing only happens on `main`, never on pull requests

Open any pull request's checks and note the `Publish Docker images` job shows as **Skipped**. Compare against a push-to-main run in the [Actions tab](https://github.com/Bridget-Kathure/production-service-environment/actions), where the same job actually executes and pushes images. This is enforced by `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` in the workflow, not by convention.

### 4. Runtime does not rebuild locally

`docker-compose.prod.yml` uses `image:`, not `build:`, for every service:

```bash
grep -A1 "^  service-a:" docker-compose.prod.yml
```

You'll see it references `${DOCKERHUB_USERNAME}/${APP_NAME}-service-a:${IMAGE_TAG}` -- a pulled image, not a local Dockerfile.

### 5. Deployment works end-to-end from a clean clone

```bash
git clone https://github.com/Bridget-Kathure/production-service-environment.git
cd production-service-environment
cp .env.example .env
export DOCKERHUB_USERNAME=ainembabazi
export APP_NAME=production-service-environment
./scripts/deploy.sh sha-71dd255
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8080/service-a/health
curl http://localhost:8080/service-a/ready
```

Expected: `service-a` reports `"status":"healthy"`, and the readiness check confirms `service-b` is reachable through the internal network.

### 6. Only the gateway is exposed; internal services are network-isolated

```bash
# service-b/c should be unreachable from the host -- no port mapping exists
curl -m 3 http://localhost:3002/health   # expect: connection refused

# nginx explicitly blocks direct routing to internal services
curl -i http://localhost:8080/service-b/  # expect: 403 Forbidden
curl -i http://localhost:8080/service-c/  # expect: 403 Forbidden
```

### 7. Containers avoid root

```bash
docker run --rm ainembabazi/production-service-environment-service-a:sha-71dd255 whoami
# expect: appuser
```

### 8. No secrets committed

`DOCKERHUB_TOKEN` and `DOCKERHUB_USERNAME` are stored as a GitHub repository secret and variable respectively -- never in source. `.env` is gitignored; only `.env.example` (with placeholder values) is tracked.

### Cleanup

```bash
docker compose -f docker-compose.prod.yml down
```

## Project Overview

This system runs three HTTP services that communicate through a defined request chain. All external traffic enters through an **Nginx reverse proxy**, which forwards only to **Service A**. Service A calls Service B, which calls Service C. Service C sends an asynchronous callback to Service A upon completion. Services B and C are internal and unreachable from outside.

**Two deployment options are supported:**
- **VM with systemd** -- Services run as systemd units on an Ubuntu VM
- **Docker Compose** -- Services run as containers with isolated networking (this branch)

---

## Architecture

```
Client
  |
  v
Nginx (Port 80 VM / 8080 Docker)  <-- Public entry point
  |
  v
Service A (Port 3001)             <-- Public API gateway
  |
  v
Service B (Port 3002)             <-- Internal forwarding
  |
  v
Service C (Port 3003)             <-- Internal processing
  |
  v
Service A /greeting-rcvd          <-- Async callback
```

| Component | Role | Access |
|-----------|------|--------|
| **Nginx** | Reverse proxy, request ID assignment | Public |
| **Service A** | Public API gateway, callback receiver | Public via Nginx only |
| **Service B** | Internal forwarding service | Internal only |
| **Service C** | Internal processing service | Internal only |

---

## Technologies Used

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Application logic |
| **Web Framework** | FastAPI | 0.115.0 | HTTP API framework |
| **ASGI Server** | Uvicorn | 0.32.0 | WSGI/ASGI server |
| **HTTP Client** | Requests | 2.32.0 | Service-to-service calls |
| **Reverse Proxy** | Nginx | Latest | Traffic routing |
| **VM Service Manager** | systemd | -- | Process supervision |
| **Container Runtime** | Docker | 29.x | Container engine |
| **Container Orchestration** | Docker Compose | 1.29.2+ | Multi-container management |
| **Base Image** | `python:3.12-slim` | -- | Lightweight Python container |
| **Nginx Image** | `nginx:alpine` | -- | Lightweight Nginx container |
| **Logging** | Python `logging` + JSON formatter | -- | Structured logs to stdout |

---

## Project Structure

```
production-service-environment/
|-- docker-compose.yml          # Docker Compose orchestration
|-- requirements.txt            # Pinned Python dependencies
|-- .dockerignore               # Docker build exclusions
|-- README.md                   # This file
|-- services/
|   |-- service-a/
|   |   |-- Dockerfile
|   |   |-- app.py
|   |   |-- logger.py
|   |-- service-b/
|   |   |-- Dockerfile
|   |   |-- app.py
|   |   |-- logger.py
|   |-- service-c/
|       |-- Dockerfile
|       |-- app.py
|       |-- logger.py
|-- nginx/
|   |-- production-env.conf     # Nginx config for VM
|   |-- docker-nginx.conf       # Nginx config for Docker
|-- systemd/
|   |-- service-a.service
|   |-- service-b.service
|   |-- service-c.service
|   |-- generate_systemd.py
|-- scripts/
|   |-- install.sh
|   |-- generate_systemd.py
|-- docs/
    |-- CONTAINER_VALIDATION.md
```

---

## Deployment Options

### Option A: VM with systemd

Run services as systemd units on an Ubuntu VM. Services bind to loopback and communicate via /etc/hosts entries.

> For full VM setup instructions, see the `main` branch. Below is a quick reference.

#### Quick Start (VM)

```bash
git checkout main
bash scripts/install.sh
```

#### Validation (VM)

```bash
# Health check
curl http://localhost/service-a/health

# Full chain
curl -s http://localhost/service-a/greet-service-b | python3 -m json.tool

# Prove B and C are internal
curl -I http://localhost/service-b/health    # 403
curl -I http://localhost/service-c/health    # 403
```

---

### Option B: Docker Compose

Run services as containers with isolated Docker networking. Only Nginx publishes a host port.

> This is the focus of the `docker-compose-migration` branch.

#### Prerequisites

- Docker
- Docker Compose (v1.29.2+ or v2.x)

#### Step 1: Ensure You Are on This Branch

```bash
git checkout docker-compose-migration
```

#### Step 2: Build and Start Containers

```bash
docker-compose up --build -d
```

#### Step 3: Verify Containers

```bash
docker-compose ps
```

Expected: 4 containers Up. Only nginx has 0.0.0.0:8080->80/tcp.

#### Step 4: Test Public Route

```bash
curl -s http://localhost:8080/service-a/health | python3 -m json.tool
```

#### Step 5: Prove B and C Are Internal-Only

```bash
curl -i --connect-timeout 3 http://localhost:3002/health   # Connection refused
curl -i --connect-timeout 3 http://localhost:3003/health   # Connection refused
```

#### Step 6: Prove Internal Service Discovery

```bash
docker-compose exec service-a python -c "import urllib.request; print(urllib.request.urlopen('http://service-b:3002/health').read().decode())"
docker-compose exec service-b python -c "import urllib.request; print(urllib.request.urlopen('http://service-c:3003/health').read().decode())"
```

#### Step 7: Trace One Request

```bash
curl -s http://localhost:8080/service-a/greet-service-b -H "X-Request-ID: demo-container-001"
docker-compose logs | grep demo-container-001
```

Expected: Same ID in nginx, service-a, service-b, service-c logs.

#### Step 8: Failure and Recovery Test

```bash
# Stop B
docker-compose stop service-b

# Send failing request
curl -s http://localhost:8080/service-a/greet-service-b -H "X-Request-ID: fail-test-001"
# Expected: {"status": "error", "message": "Service B unreachable"}

# Check logs
docker-compose logs service-a | grep fail-test-001

# Recover
docker-compose start service-b
curl -s http://localhost:8080/service-a/greet-service-b -H "X-Request-ID: recover-test-001"
# Expected: {"status": "success"}
```

#### Step 9: Shut Down

```bash
docker-compose down
```

---

## Peer Review Feedback & Fixes

Original score: **88/100** ("Approve with changes")

| # | Issue | Original Problem | Fix Applied |
|---|-------|-----------------|-------------|
| 1 | **Synchronous callback deadlock** | Service C made blocking requests.post() to Service A before returning | Changed to threading.Thread fire-and-forget |
| 2 | **systemd cascading shutdown** | Requires= caused cascading failures | Replaced with Wants= in all .service files |
| 3 | **Hardcoded paths & users** | /home/ubuntu and User=ubuntu hardcoded | Created scripts/generate_systemd.py for dynamic generation |
| 4 | **No requirements.txt** | Unpinned pip install in install.sh | Created requirements.txt with pinned versions |
| 5 | **Static health checks** | /health returned hardcoded JSON | Added uptime_seconds, check_type, and /ready endpoints |

---

## Logging

All services emit structured JSON logs to stdout.

### VM: systemd journal

```bash
journalctl -u service-a -n 50 --no-pager
journalctl -u service-a -f
journalctl -u service-a -u service-b -u service-c --since "5 minutes ago" --no-pager
sudo tail -f /var/log/nginx/production-env.access.log
```

### Docker Compose

```bash
docker-compose logs
docker-compose logs service-a
docker-compose logs -f
```

### Log Fields

| Field | Description |
|-------|-------------|
| timestamp | UTC ISO 8601 |
| service | Service name |
| event | Event type |
| request_id | Trace ID shared across services |
| path | HTTP path |
| method | HTTP method |
| status | HTTP status code |
| target | Downstream service |
| error | Error description |

---

## Container CI/CD Deployment

This project uses GitHub Actions for continuous integration and deployment. Every pull request to `main` triggers automated tests, builds, and container verification. Only successful merges to `main` publish images to Docker Hub.

### Latest deployed version

Commit: `71dd25563ae7b9fc1755b7fefdf886eb6af343ec`
Image tag: `sha-71dd255`

Images:
- `ainembabazi/production-service-environment-service-a:sha-71dd255`
- `ainembabazi/production-service-environment-service-b:sha-71dd255`
- `ainembabazi/production-service-environment-service-c:sha-71dd255`

### Deploy

```bash
# Set environment variables
export DOCKERHUB_USERNAME=ainembabazi
export APP_NAME=production-service-environment

# Deploy a specific version using the deployment script
./scripts/deploy.sh sha-71dd255
```

**Verify Deployment**

```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Test health endpoint
curl http://localhost:8080/service-a/health
```

**CI/CD Pipeline Overview**

| Stage              | Trigger               | What It Does                                                     |
| ------------------ | ---------------------- | ----------------------------------------------------------------|
| **Verify**         | PR + Push to main      | Installs Python deps, runs pytest, builds Docker images locally |
| **Verify Compose** | After Verify succeeds  | Validates compose config, builds full stack, runs health checks |
| **Publish**        | Push to main only      | Logs into Docker Hub, builds and pushes commit-tagged images    |

**Required GitHub Secrets & Variables**

| Name                 | Type                 | Purpose                                    |
| --------------------- | -------------------- | ------------------------------------------ |
| `DOCKERHUB_USERNAME` | Repository Variable  | Docker Hub username for image naming       |
| `DOCKERHUB_TOKEN`    | Repository Secret    | Docker Hub access token for authentication |

**Image Tag Format**

Images are tagged with the short commit hash: `sha-<7-char-hash>`

Allowed: `sha-a1b2c3d`

Not Allowed: `latest`, `main`, `dev`


## Troubleshooting

### VM Setup

| Symptom | Cause | Fix |
|---------|-------|-----|
| Service won't start | Port in use | ss -tlnp | grep 3001 |
| Missing packages | venv not activated | source venv/bin/activate && pip install -r requirements.txt |
| Can't reach peer | /etc/hosts missing | grep '.internal' /etc/hosts |
| Nginx 502 | Service not running | sudo systemctl status service-a |
| No logs | Journal full | journalctl --disk-usage |

### Docker Compose

| Symptom | Cause | Fix |
|---------|-------|-----|
| Container won't start | Port 8080 in use | docker-compose down && lsof -i :8080 |
| Can't reach service | Wrong hostname | Use service-b, not localhost |
| Build fails | Missing requirements.txt | Ensure file is in repo root |
| Logs empty | Service crashed | docker-compose logs --tail 50 <service> |
test
