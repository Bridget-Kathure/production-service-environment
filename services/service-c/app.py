from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import asyncio
import random
import threading
from datetime import datetime, timezone
from logger import get_logger

# Jaeger / OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry import context as otel_context
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

app = FastAPI()
logger = get_logger("service-c")
START_TIME = time.time()

# Initialize Jaeger tracing
resource = Resource(attributes={SERVICE_NAME: "service-c"})
provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("service-c")

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'route', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['service', 'method', 'route']
)

http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['service', 'route', 'error_type']
)

service_up = Gauge(
    'service_up',
    'Service uptime indicator',
    ['service']
)

# Mark service as up
service_up.labels(service="service-c").set(1)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    route = request.url.path
    method = request.method

    response = await call_next(request)
    duration = time.time() - start_time
    status = response.status_code

    http_requests_total.labels(
        service="service-c",
        method=method,
        route=route,
        status_code=str(status)
    ).inc()

    http_request_duration_seconds.labels(
        service="service-c",
        method=method,
        route=route
    ).observe(duration)

    if status >= 400:
        http_errors_total.labels(
            service="service-c",
            route=route,
            error_type=str(status)
        ).inc()

    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def send_callback(request_id: str, parent_ctx):
    """Fire-and-forget callback to Service A."""
    otel_context.attach(parent_ctx)
    with tracer.start_as_current_span("send_callback_to_service_a") as span:
        span.set_attribute("target_service", "service-a")
        span.set_attribute("request_id", request_id)
        try:
            headers = {"X-Request-ID": request_id}
            propagator = TraceContextTextMapPropagator()
            propagator.inject(headers)
            requests.post(
                "http://service-a:3001/greeting-rcvd",
                headers=headers,
                json={
                    "request_id": request_id,
                    "source_service": "service-c",
                    "message": "Greeting processed",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                timeout=5
            ).raise_for_status()
            logger.info("callback_sent", extra={
                "service_name": "service-c",
                "request_id": request_id,
                "path": "/greet-c",
                "status": 200,
                "method": "GET",
                "target": "service-a",
                "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
            })
        except requests.exceptions.RequestException as e:
            logger.error("callback_failed", extra={
                "service_name": "service-c",
                "request_id": request_id,
                "path": "/greet-c",
                "status": 502,
                "method": "GET",
                "error": str(e),
                "target": "service-a",
                "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
            })

@app.get("/health")
async def health(request: Request):
    request_id = str(uuid.uuid4())
    uptime = round(time.time() - START_TIME, 2)
    logger.info("health_check", extra={
        "service_name": "service-c",
        "request_id": request_id,
        "path": "/health",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-c",
        "status": "healthy",
        "port": 3003,
        "uptime_seconds": uptime,
        "check_type": "liveness"
    }

@app.get("/ready")
async def ready(request: Request):
    request_id = str(uuid.uuid4())
    logger.info("readiness_check", extra={
        "service_name": "service-c",
        "request_id": request_id,
        "path": "/ready",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-c",
        "status": "ready",
        "downstream": "none",
        "downstream_status": "n/a"
    }

@app.get("/greet-c")
def greet_c(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())

    carrier = dict(request.headers)
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

    with tracer.start_as_current_span("greet_c", context=ctx) as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/greet-c")
        span.set_attribute("request_id", request_id)

        logger.info("request_received", extra={
            "service_name": "service-c",
            "request_id": request_id,
            "path": "/greet-c",
            "status": 200,
            "method": "GET",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

        # Fire callback in background thread so we return immediately to Service B
        current_ctx = otel_context.get_current()
        threading.Thread(target=send_callback, args=(request_id, current_ctx), daemon=True).start()

        return {"request_id": request_id, "status": "processed", "callback_sent": True}

@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    with tracer.start_as_current_span("fail_endpoint") as span:
        span.set_attribute("error", True)
        span.set_attribute("request_id", request_id)
        logger.error("controlled_failure", extra={
            "service_name": "service-c",
            "request_id": request_id,
            "path": "/fail",
            "status": 500,
            "method": "GET",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": "Controlled failure endpoint triggered"})

@app.get("/slow")
async def slow_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    delay = random.uniform(1, 3)
    with tracer.start_as_current_span("slow_endpoint") as span:
        span.set_attribute("delay_seconds", delay)
        span.set_attribute("request_id", request_id)
        await asyncio.sleep(delay)
        logger.info("slow_response", extra={
            "service_name": "service-c",
            "request_id": request_id,
            "path": "/slow",
            "status": 200,
            "method": "GET",
            "duration_ms": int(delay * 1000),
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })
    return {"status": "success", "message": f"Delayed response after {delay:.2f} seconds"}

@app.get("/{path:path}")
async def catch_all(request: Request, path: str):
    request_id = str(uuid.uuid4())
    logger.info("route_not_found", extra={
        "service_name": "service-c",
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3003)
