from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import asyncio
import random
import os
from logger import get_logger

VERSION = os.environ.get("GIT_SHA", "unknown")

# Jaeger / OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

app = FastAPI()
logger = get_logger("service-b")
START_TIME = time.time()

# Initialize Jaeger tracing
resource = Resource(attributes={SERVICE_NAME: "service-b"})
provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("service-b")

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
service_up.labels(service="service-b").set(1)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    route = request.url.path
    method = request.method

    response = await call_next(request)
    duration = time.time() - start_time
    status = response.status_code

    http_requests_total.labels(
        service="service-b",
        method=method,
        route=route,
        status_code=str(status)
    ).inc()

    http_request_duration_seconds.labels(
        service="service-b",
        method=method,
        route=route
    ).observe(duration)

    if status >= 400:
        http_errors_total.labels(
            service="service-b",
            route=route,
            error_type=str(status)
        ).inc()

    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Gate 3A verification: hands-off deploy via CodePipeline/EventBridge
@app.get("/health")
async def health(request: Request):
    request_id = str(uuid.uuid4())
    uptime = round(time.time() - START_TIME, 2)
    logger.info("health_check", extra={
        "service_name": "service-b",
        "request_id": request_id,
        "path": "/health",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-b",
        "version": VERSION,
        "status": "healthy",
        "port": 3002,
        "uptime_seconds": uptime,
        "check_type": "liveness"
    }

@app.get("/ready")
async def ready(request: Request):
    request_id = str(uuid.uuid4())
    try:
        with tracer.start_as_current_span("check_service_c_health"):
            resp = requests.get(
                "http://service-c:3003/health",
                headers={"X-Request-ID": request_id},
                timeout=2
            )
            resp.raise_for_status()
        logger.info("readiness_check", extra={
            "service_name": "service-b",
            "request_id": request_id,
            "path": "/ready",
            "status": 200,
            "method": "GET",
            "target": "service-c"
        })
        return {
            "service": "service-b",
            "status": "ready",
            "downstream": "service-c",
            "downstream_status": "healthy"
        }
    except requests.exceptions.RequestException as e:
        logger.error("readiness_check_failed", extra={
            "service_name": "service-b",
            "request_id": request_id,
            "path": "/ready",
            "status": 503,
            "method": "GET",
            "error": str(e),
            "target": "service-c"
        })
        return JSONResponse(status_code=503, content={
            "service": "service-b",
            "status": "not_ready",
            "downstream": "service-c",
            "downstream_status": "unreachable"
        })

@app.get("/greet")
def greet(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())

    carrier = dict(request.headers)
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

    with tracer.start_as_current_span("greet", context=ctx) as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/greet")
        span.set_attribute("request_id", request_id)

        logger.info("request_received", extra={
            "service_name": "service-b",
            "request_id": request_id,
            "path": "/greet",
            "status": 200,
            "method": "GET",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

        # Propagate trace context to service-c
        headers = {"X-Request-ID": request_id}
        propagator = TraceContextTextMapPropagator()

        try:
            with tracer.start_as_current_span("call_service_c"):
                propagator.inject(headers)
                resp = requests.get(
                    "http://service-c:3003/greet-c",
                    headers=headers,
                    timeout=5
                )
                resp.raise_for_status()
        except requests.exceptions.RequestException:
            logger.error("request_failed", extra={
                "service_name": "service-b",
                "request_id": request_id,
                "path": "/greet",
                "status": 502,
                "method": "GET",
                "error": "service_c_unreachable",
                "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
            })
            return JSONResponse(status_code=502, content={
                "request_id": request_id,
                "status": "error",
                "target": "service-c"
            })

        logger.info("request_forwarded", extra={
            "service_name": "service-b",
            "request_id": request_id,
            "path": "/greet",
            "status": 200,
            "method": "GET",
            "target": "service-c",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

        return {"request_id": request_id, "status": "forwarded", "target": "service-c"}

@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    with tracer.start_as_current_span("fail_endpoint") as span:
        span.set_attribute("error", True)
        span.set_attribute("request_id", request_id)
        logger.error("controlled_failure", extra={
            "service_name": "service-b",
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
            "service_name": "service-b",
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
        "service_name": "service-b",
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3002)
