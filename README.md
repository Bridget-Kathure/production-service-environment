# Production Service Environment

A production-style microservices environment demonstrating service discovery, reverse proxying, structured JSON logging, distributed request tracing, and systemd lifecycle management.

## Project Overview

This system runs three HTTP services that communicate through a defined request chain. All external traffic enters through an Nginx reverse proxy, which forwards only to Service A. Service A calls Service B, which calls Service C. Service C sends a callback to Service A upon completion. Services B and C are internal and unreachable from outside the VM.

## Architecture

```
Client
  ↓
Nginx (Port 80)           ← Public entry point; strips /service-a/ prefix
  ↓
Service A (Port 3001)     ← Public API gateway; initiates chain
  ↓
Service B (Port 3002)     ← Internal forwarding service
  ↓
Service C (Port 3003)     ← Internal processing service
  ↓
Service A /greeting-rcvd  ← Callback; completes the trace
```

Only Service A is reachable through Nginx. Services B and C bind to `127.0.0.1` and are inaccessible from outside the VM.

## Project Structure

```
production-service-environment/
├── services/
│   ├── service-a/          # Public API gateway
│   │   ├── app.py
│   │   └── logger.py
│   ├── service-b/          # Internal forwarding service
│   │   ├── app.py
│   │   └── logger.py
│   └── service-c/          # Internal processing service
│       ├── app.py
│       └── logger.py
├── systemd/
│   ├── service-a.service
│   ├── service-b.service
│   └── service-c.service
├── nginx/
│   └── production-env.conf
├── scripts/
│   └── install.sh
└── README.md
```

## Service Discovery

Services communicate using hostnames defined in `/etc/hosts` rather than hardcoded IP addresses.

**How services discover one another:** Each service references its peers by a `.internal` hostname (e.g. `http://service-b.internal:3002`). No external DNS is involved.

**How name resolution works:** The OS resolver checks `/etc/hosts` before querying DNS. This is controlled by `/etc/nsswitch.conf`, which has `hosts: files dns` — meaning `/etc/hosts` is checked first.

**What component performs the resolution:** The system resolver (`libc`/`nss`). No additional service discovery daemon is needed.

**Required `/etc/hosts` entries:**
```
127.0.0.1 service-a.internal service-b.internal service-c.internal
```

**Troubleshooting discovery failures:**
```bash
# Verify entries exist
grep '\.internal' /etc/hosts

# Test resolution
getent hosts service-b.internal
ping -c1 service-c.internal

# Test reachability
curl http://service-b.internal:3002/health
```

## Network Security

Services B and C are internal and must not be reachable from outside the VM.

**Why they are protected:** All external traffic must pass through Nginx, which only routes to Service A. Direct access to internal services would bypass the reverse proxy and expose internal endpoints.

**What enforces the protection:**
1. Services B and C bind to `127.0.0.1` (loopback only), not `0.0.0.0`. External packets never reach them.
2. Nginx returns `403 Forbidden` for any requests to `/service-b/` or `/service-c/` paths.

**How to verify:**
```bash
# From outside the VM — both should fail (connection refused)
curl http://<public-ip>:3002/health
curl http://<public-ip>:3003/health

# Confirm services bind to loopback only
ss -tlnp | grep -E '3002|3003'
# Expected: 127.0.0.1:3002 and 127.0.0.1:3003

# Confirm Nginx blocks internal paths
curl -I http://localhost/service-b/health   # 403
curl -I http://localhost/service-c/health   # 403
```

## Request Tracing

Every request is assigned an `X-Request-ID` that propagates through the full chain.

**How it works:**
1. Nginx assigns `X-Request-ID` — it uses the client-provided value if present, otherwise generates one with `$request_id`. This value is forwarded to Service A.
2. Service A reads the header and logs it. It passes the same ID to Service B.
3. Service B passes it to Service C.
4. Service C includes it in the callback POST body and header to Service A.
5. Every log entry from every service and from Nginx contains the same `request_id`.

**Following a request through logs:**
```bash
# Send a request and capture the ID
REQ_ID=$(uuidgen)
curl -s http://localhost/service-a/greet-service-b -H "X-Request-ID: $REQ_ID"

# Trace it across all services
journalctl -u service-a -u service-b -u service-c --no-pager | grep "$REQ_ID"

# Also check Nginx
sudo grep "$REQ_ID" /var/log/nginx/production-env.access.log
```

## Installation

### Prerequisites

- Ubuntu 22.04/24.04
- Python 3.12+
- Nginx
- systemd

### One-Command Install (Recommended)

```bash
bash scripts/install.sh
```

### Manual Steps

```bash
# 1. Install system dependencies
# Note: if apt update exits with a GPG error, run the install step separately
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx

# 2. Clone the repository
git clone <repo-url> ~/devops-lab/production-service-environment
cd ~/devops-lab/production-service-environment

# 3. Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests

# 4. Configure service discovery
echo "127.0.0.1 service-a.internal service-b.internal service-c.internal" | sudo tee -a /etc/hosts

# For cloud VMs where /etc/hosts is managed by cloud-init, also add to the template:
echo "127.0.0.1 service-a.internal service-b.internal service-c.internal" | sudo tee -a /etc/cloud/templates/hosts.debian.tmpl

# 5. Install and enable systemd units
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable service-c service-b service-a

# 6. Configure Nginx
sudo cp nginx/production-env.conf /etc/nginx/sites-available/
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/production-env.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 7. Start services (order matters for dependencies)
sudo systemctl start service-c service-b service-a
```

## Operation

### Start
```bash
sudo systemctl start service-c service-b service-a
```

### Stop
```bash
sudo systemctl stop service-a service-b service-c
```

### Restart a single service
```bash
sudo systemctl restart service-a
```

### Check status
```bash
sudo systemctl status service-a service-b service-c
```

### Verify health endpoints
```bash
curl http://localhost/service-a/health
curl http://service-b.internal:3002/health
curl http://service-c.internal:3003/health
```

## Validation

### Full request chain
```bash
curl -s http://localhost/service-a/greet-service-b | python3 -m json.tool
```
Expected: `{"request_id": "...", "status": "success", "message": "Request completed successfully"}`

### Nginx routing
```bash
curl -I http://localhost/service-a/health    # 200
curl -I http://localhost/service-b/health    # 403
curl -I http://localhost/service-c/health    # 403
curl -I http://localhost/anything            # 404
```

### Auto-restart after failure
```bash
# systemctl stop is an intentional stop — it does NOT trigger auto-restart.
# Simulate a crash by killing the process directly instead:
sudo systemctl start service-b
sudo kill -9 $(systemctl show -p MainPID service-b | cut -d= -f2)
sleep 5
sudo systemctl status service-b   # Should show active (running) — restarted after crash
```

### Reboot recovery
```bash
sudo reboot
# After reboot:
sudo systemctl status service-a service-b service-c   # All active
curl http://localhost/service-a/health                 # 200
```

## Logging

All services write structured JSON logs to stdout, captured by the systemd journal.

### Viewing logs
```bash
# Recent logs for a service
journalctl -u service-a -n 50 --no-pager

# Follow live
journalctl -u service-a -f

# All services together, last 5 minutes
journalctl -u service-a -u service-b -u service-c --since "5 minutes ago" --no-pager

# Nginx access log
sudo tail -f /var/log/nginx/production-env.access.log
```

### Log fields

| Field | Description |
|---|---|
| `timestamp` | UTC ISO 8601 |
| `service` | `service-a`, `service-b`, or `service-c` |
| `event` | What happened (`request_received`, `callback_sent`, `request_failed`, etc.) |
| `request_id` | Trace ID shared across all services for one request |
| `path` | HTTP path |
| `method` | HTTP method |
| `status` | HTTP status code |
| `target` | Downstream service called (when applicable) |
| `source_service` | Upstream service that sent the request (when applicable) |
| `error` | Error description (on failure events only) |

## Troubleshooting

### Service startup failures
```bash
sudo systemctl status service-a
journalctl -u service-a -n 50 --no-pager

# Common causes:
# Port already in use
ss -tlnp | grep 3001

# Python or venv not found
ls /home/ubuntu/devops-lab/production-service-environment/venv/bin/python3

# Missing packages
/home/ubuntu/devops-lab/production-service-environment/venv/bin/pip list | grep -E 'fastapi|uvicorn|requests'

# Wrong WorkingDirectory or User in unit file
systemctl cat service-a
```

### Service dependency failures
```bash
# Service A requires B and C. If either is stopped, A will not start.
sudo systemctl status service-b service-c

# Start in dependency order
sudo systemctl start service-c
sudo systemctl start service-b
sudo systemctl start service-a

# View dependency chain
systemctl cat service-a | grep -E 'After|Requires'
```

### Reverse proxy failures
```bash
sudo systemctl status nginx
sudo nginx -t

# Check error log
sudo tail -50 /var/log/nginx/production-env.error.log

# Verify config is linked
ls -la /etc/nginx/sites-enabled/

# Reload after config change (no downtime)
sudo nginx -s reload
```

### Service discovery failures
```bash
# Check /etc/hosts
grep '\.internal' /etc/hosts

# Test resolution
getent hosts service-b.internal

# If missing, re-add
echo "127.0.0.1 service-a.internal service-b.internal service-c.internal" | sudo tee -a /etc/hosts

# For cloud VMs where /etc/hosts is managed by cloud-init, also add to the template:
echo "127.0.0.1 service-a.internal service-b.internal service-c.internal" | sudo tee -a /etc/cloud/templates/hosts.debian.tmpl
```

### Name resolution failures
```bash
# nsswitch.conf must have 'files' before 'dns'
grep '^hosts' /etc/nsswitch.conf
# Expected: hosts: files dns

# If 'dns' appears first, /etc/hosts entries are skipped.
# Edit /etc/nsswitch.conf to put 'files' first.
```

### Network access failures
```bash
# Confirm each service binds to the correct interface
ss -tlnp | grep -E '3001|3002|3003'
# Service A: 127.0.0.1:3001
# Service B: 127.0.0.1:3002
# Service C: 127.0.0.1:3003

# Check firewall
sudo ufw status
sudo iptables -L INPUT -n
```

### Missing logs
```bash
# Confirm service is running
sudo systemctl status service-a

# Check journal for startup errors
journalctl -u service-a --since "10 minutes ago" --no-pager

# Verify journal disk usage is not full
journalctl --disk-usage
```

### Invalid routing behavior
```bash
# Test each route explicitly
curl -v http://localhost/service-a/health    # expect 200
curl -v http://localhost/service-b/health    # expect 403
curl -v http://localhost/service-c/health    # expect 403
curl -v http://localhost/anything-else       # expect 404

# Inspect active Nginx config
sudo nginx -T 2>&1 | grep -A5 'location'

# Confirm the correct config is enabled
ls -la /etc/nginx/sites-enabled/
```

### Inter-service communication failures
```bash
# Test each hop manually with a consistent request ID
curl http://service-b.internal:3002/greet -H "X-Request-ID: test-123"
curl http://service-c.internal:3003/greet-c -H "X-Request-ID: test-123"

# Confirm /etc/hosts maps to 127.0.0.1
getent hosts service-b.internal

# Trace a full request and check logs at each service
REQ_ID=$(uuidgen)
curl -s http://localhost/service-a/greet-service-b -H "X-Request-ID: $REQ_ID"
journalctl -u service-a -u service-b -u service-c --no-pager | grep "$REQ_ID"
```
