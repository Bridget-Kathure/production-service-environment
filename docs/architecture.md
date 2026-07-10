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
plain

## Request Flow

1. Client sends request to `http://localhost:8080/service-a/greet-service-b`
2. Nginx routes to Service A
3. Service A calls Service B (`/greet`)
4. Service B calls Service C (`/greet-c`)
5. Service C fires callback to Service A (`/greeting-rcvd`)

## Telemetry Flow

### Metrics Collection
Services (/metrics) --> Prometheus (:9090) --> Grafana (:3000)
plain

### Tracing Flow
Services (Jaeger Agent) --> Jaeger (:16686)
plain

### Logging Flow
Services (stdout) --> docker compose logs
plain

### Alerting Flow
Prometheus Rules --> Alert Conditions --> Grafana Dashboard
plain

## Known Limitations

1. Logs are not centralized in Loki (viewed via `docker compose logs`)
2. No Alertmanager for notifications (alerts visible in Grafana only)
3. Tracing uses Jaeger Thrift; OTLP collector not configured
