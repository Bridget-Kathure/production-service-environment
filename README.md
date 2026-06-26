# Production Service Environment

A production-style microservices environment demonstrating service discovery, reverse proxying, structured JSON logging, distributed request tracing, systemd lifecycle management, and Docker Compose containerization.

> **Branch:** `docker-compose-migration`
> This branch adds Docker Compose containerization as an alternative to the VM-based systemd setup.
> For the original VM-only version, see the [`main`](https://github.com/Bridget-Kathure/production-service-environment/tree/main) branch.

---

## Table of Contents

1. [Project Overview](#project-overview)
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
