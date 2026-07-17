# Architecture

## Service Architecture
Client / Load Test Tool
|
v
Nginx (Gateway)
:8080
|
v
+------------------+
|   Service A      |
|   :3001          |
+--------+---------+
|
v
+------------------+
|   Service B      |
|   :3002          |
+--------+---------+
|
v
+------------------+
|   Service C      |
|   :3003          |
+------------------+

## Request Flow

1. Client sends request to `http://localhost:8080/service-a/greet-service-b`
2. Nginx routes to Service A
3. Service A calls Service B (`/greet`)
4. Service B calls Service C (`/greet-c`)
5. Service C fires an asynchronous callback to Service A (`/greeting-rcvd`)

## Telemetry Flow

### Metrics Collection
Services (/metrics) --> Prometheus (:9090) --> Grafana (:3000)
Prometheus scrapes each service every 15s via Docker Compose service names (service-a:3001, etc.). Grafana queries Prometheus as its datasource.

### Tracing Flow
Services --> Jaeger Agent (UDP :6831) --> Jaeger Collector --> Jaeger UI (:16686)
Trace context is propagated via HTTP headers across service-a to service-b to service-c and back via the fire-and-forget callback, preserving a single trace ID across the full request chain.

### Logging Flow
Services (stdout, structured JSON) --> docker compose logs
Each log line includes service, level, request_id, and trace_id for correlation across MELT signals.

### Alerting Flow
Prometheus Rules (alert-rules.yml) --> Alertmanager (:9093) --> Slack channel via webhook
Prometheus evaluates the rules in alert-rules.yml and forwards firing alerts to Alertmanager, which groups them and routes them to Slack using the webhook configured in `alertmanager/alertmanager.yml`. Alerts also remain visible via Prometheus (`/alerts`) and Grafana as before.

## Known Limitations
1. Logs are not centralized in Loki -- viewed via docker compose logs SERVICE_NAME
2. `docker-compose.prod.yml` (the CI/CD deployment path) does not include Prometheus, Grafana, Jaeger, or Alertmanager -- the observability/alerting stack currently only runs via `docker-compose.yml` for local/dev use. This should be addressed before relying on Slack alerting in a deployed environment.
3. Tracing uses the legacy Jaeger Thrift exporter rather than OTLP (deprecation warning present in service logs; functionally correct but should be migrated for production use)
