# Production Service Environment

A production-style microservices environment demonstrating service discovery, reverse proxying, structured logging, request tracing, and systemd lifecycle management.

## Architecture

```
Client
  ↓
Nginx (Port 80)
  ↓
Service A (Port 3001) — Public
  ↓
Service B (Port 3002) — Internal
  ↓
Service C (Port 3003) — Internal
  ↓
Service A Callback (Port 3001)
```

## Project Structure

```
production-service-environment/
├── service-a/          # Public API gateway (Person 1)
│   ├── app.py
│   └── logger.py
├── service-b/          # Internal forwarding service (Person 2)
│   ├── app.py
│   └── logger.py
├── service-c/          # Internal processing service (Person 2)
│   ├── app.py
│   └── logger.py
├── systemd/            # Service definitions (Person 3)
│   ├── service-a.service
│   ├── service-b.service
│   └── service-c.service
├── nginx/              # Reverse proxy config (Person 3)
│   └── production-env.conf
├── scripts/            # Automation (Person 3)
│   └── install.sh
└── README.md           # Documentation (Person 3)
```

## Team Responsibilities

- **Person 1 (Service A):** Health endpoint, greet-service-b endpoint, callback receiver, logging, request tracing
- **Person 2 (Services B & C):** Health endpoints, forward chain, callback sender, service discovery setup
- **Person 3 (Infrastructure):** Nginx, systemd, install script, README, troubleshooting guide

## Prerequisites

- Ubuntu 22.04/24.04
- Python 3.12+
- Nginx
- systemd

## Quick Start

```bash
# 1. Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx

# 2. Setup virtual environment
cd ~/devops-lab/production-service-environment
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests

# 3. Configure service discovery
sudo nano /etc/hosts
# Add: 127.0.0.1 service-a.internal service-b.internal service-c.internal

# 4. Install systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable service-c service-b service-a

# 5. Configure Nginx
sudo cp nginx/production-env.conf /etc/nginx/sites-available/
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/production-env.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 6. Start services
sudo systemctl start service-c service-b service-a
```

## Verification

```bash
curl http://localhost/health
curl http://localhost/greet-service-b
```

## TODO

- [ ] Person 1: Implement full Service A flow (call Service B, handle callback)
- [ ] Person 2: Implement Service B forward to Service C
- [ ] Person 2: Implement Service C callback to Service A
- [ ] Person 3: Create install.sh script
- [ ] Person 3: Write full README with troubleshooting guide
- [ ] All: Test end-to-end flow
- [ ] All: Verify JSON logs and request tracing
