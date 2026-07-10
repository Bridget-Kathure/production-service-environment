from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import random
from logger import get_logger

# Jaeger / OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

app = FastAPI()
logger = get_logger("service-a")
START_TIME = time.time()

# Initialize Jaeger tracing
resource = Resource(attributes={SERVICE_NAME: "service-a"})
provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("service-a")

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

service_up = Counter(
    'service_up_total',
    'Service uptime indicator',
    ['service']
)

# Mark service as up
service_up.labels(service="service-a").inc()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    route = request.url.path
    method = request.method

    response = await call_next(request)
    duration = time.time() - start_time
    status = response.status_code

    http_requests_total.labels(
        service="service-a",
        method=method,
        route=route,
        status_code=str(status)
    ).inc()

    http_request_duration_seconds.labels(
        service="service-a",
        method=method,
        route=route
    ).observe(duration)

    if status >= 400:
        http_errors_total.labels(
            service="service-a",
            route=route,
            error_type=str(status)
        ).inc()

    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health(request: Request):
    request_id = str(uuid.uuid4())
    uptime = round(time.time() - START_TIME, 2)
    logger.info("health_check", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/health",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-a",
        "status": "healthy",
        "port": 3001,
        "uptime_seconds": uptime,
        "check_type": "liveness"
    }

@app.get("/ready")
async def ready(request: Request):
    request_id = str(uuid.uuid4())
    try:
        with tracer.start_as_current_span("check_service_b_health"):
            resp = requests.get(
                "http://service-b:3002/health",
                headers={"X-Request-ID": request_id},
                timeout=2
            )
            resp.raise_for_status()
        logger.info("readiness_check", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/ready",
            "status": 200,
            "method": "GET",
            "target": "service-b"
        })
        return {
            "service": "service-a",
            "status": "ready",
            "downstream": "service-b",
            "downstream_status": "healthy"
        }
    except requests.exceptions.RequestException as e:
        logger.error("readiness_check_failed", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/ready",
            "status": 503,
            "method": "GET",
            "error": str(e),
            "target": "service-b"
        })
        return JSONResponse(status_code=503, content={
            "service": "service-a",
            "status": "not_ready",
            "downstream": "service-b",
            "downstream_status": "unreachable"
        })

@app.get("/greet-service-b")
def greet_service_b(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())

    with tracer.start_as_current_span("greet_service_b") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/greet-service-b")
        span.set_attribute("request_id", request_id)

        logger.info("request_received", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/greet-service-b",
            "status": 200,
            "method": "GET",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

        # Propagate trace context to service-b
        headers = {"X-Request-ID": request_id}
        propagator = TraceContextTextMapPropagator()
        propagator.inject(headers)

        try:
            with tracer.start_as_current_span("call_service_b"):
                resp = requests.get(
                    "http://service-b:3002/greet",
                    headers=headers,
                    timeout=5
                )
                resp.raise_for_status()
        except requests.exceptions.RequestException:
            logger.error("request_failed", extra={
                "service_name": "service-a",
                "request_id": request_id,
                "path": "/greet-service-b",
                "status": 502,
                "method": "GET",
                "error": "service_b_unreachable",
                "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
            })
            return JSONResponse(status_code=502, content={
                "request_id": request_id,
                "status": "error",
                "message": "Service B unreachable"
            })

        logger.info("request_completed", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/greet-service-b",
            "status": 200,
            "method": "GET",
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

        return {
            "request_id": request_id,
            "status": "success",
            "message": "Request completed successfully"
        }

@app.post("/greeting-rcvd")
async def greeting_rcvd(request: Request, x_request_id: str = Header(None)):
    body = await request.json()
    request_id = x_request_id or body.get("request_id", "unknown")

    with tracer.start_as_current_span("greeting_received") as span:
        span.set_attribute("source_service", body.get("source_service", "unknown"))
        span.set_attribute("request_id", request_id)

        logger.info("callback_received", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/greeting-rcvd",
            "status": 200,
            "method": "POST",
            "source_service": body.get("source_service", "unknown"),
            "trace_id": format(trace.get_current_span().get_span_context().trace_id, '032x')
        })

    return {"status": "received"}

@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    with tracer.start_as_current_span("fail_endpoint") as span:
        span.set_attribute("error", True)
        span.set_attribute("request_id", request_id)
        logger.error("controlled_failure", extra={
            "service_name": "service-a",
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
        time.sleep(delay)
        logger.info("slow_response", extra={
            "service_name": "service-a",
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
        "service_name": "service-a",
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)
