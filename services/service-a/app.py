from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import random
from logger import get_logger

app = FastAPI()
logger = get_logger("service-a")
START_TIME = time.time()

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

service_up = Counter('service_up', 'Service uptime indicator', ['service'])

# Mark service as up
service_up.labels(service='service-a').inc()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    route = request.url.path
    method = request.method
    status = str(response.status_code)
    
    http_requests_total.labels(
        service='service-a',
        method=method,
        route=route,
        status_code=status
    ).inc()
    
    http_request_duration_seconds.labels(
        service='service-a',
        method=method,
        route=route
    ).observe(duration)
    
    if response.status_code >= 400:
        http_errors_total.labels(
            service='service-a',
            route=route,
            error_type=str(response.status_code)
        ).inc()
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

from fastapi.responses import Response

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
    logger.info("request_received", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/greet-service-b",
        "status": 200,
        "method": "GET"
    })
    try:
        requests.get(
            "http://service-b:3002/greet",
            headers={"X-Request-ID": request_id},
            timeout=5
        ).raise_for_status()
    except requests.exceptions.RequestException:
        logger.error("request_failed", extra={
            "service_name": "service-a",
            "request_id": request_id,
            "path": "/greet-service-b",
            "status": 502,
            "method": "GET",
            "error": "service_b_unreachable"
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
        "method": "GET"
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
    logger.info("callback_received", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/greeting-rcvd",
        "status": 200,
        "method": "POST",
        "source_service": body.get("source_service", "unknown")
    })
    return {"status": "received"}

# Controlled failure endpoints
@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    logger.error("controlled_failure_triggered", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/fail",
        "status": 500,
        "method": "GET"
    })
    return JSONResponse(status_code=500, content={
        "error": "Internal Server Error",
        "message": "Controlled failure endpoint triggered"
    })

@app.get("/slow")
async def slow_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    delay = random.uniform(1.0, 3.0)
    logger.info("slow_request_started", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/slow",
        "status": 200,
        "method": "GET",
        "delay_seconds": delay
    })
    time.sleep(delay)
    logger.info("slow_request_completed", extra={
        "service_name": "service-a",
        "request_id": request_id,
        "path": "/slow",
        "status": 200,
        "method": "GET",
        "delay_seconds": delay
    })
    return {
        "status": "success",
        "message": f"Delayed response after {delay:.2f} seconds"
    }

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
