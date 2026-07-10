# Jaeger - Distributed Tracing

## What is Jaeger?
Jaeger is an open-source distributed tracing system used to monitor and troubleshoot microservices-based applications.

## What data it collects
- Trace spans from service-a, service-b, service-c
- Request duration per span
- Service dependencies and call chains
- Error states in traces

## Where the data is viewed
- Jaeger UI: http://localhost:16686
- Search by service name, operation, or trace ID
- View request flow across services

## How it helps debugging
1. **Latency analysis**: Identify which service in the chain is slow
2. **Error tracing**: See exactly where a request failed
3. **Dependency mapping**: Visualize service call relationships
4. **Request correlation**: Link traces with logs via trace_id

## Trace Path
gateway → service-a → service-b → service-c → callback → service-a

## How to view traces
1. Send a request: `curl http://localhost:8080/service-a/greet-service-b`
2. Open http://localhost:16686
3. Select "service-a" from the Service dropdown
4. Click "Find Traces"
5. Click on a trace to see the full request journey
