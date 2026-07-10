from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import random
from logger import get_logger

app = FastAPI()
logger = get_logger("service-b")
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

service_up.labels(service='service-b').inc()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    route = request.url.path
    method = request.method
    status = str(response.status_code)
    
    http_requests_total.labels(
        service='service-b',
        method=method,
        route=route,
        status_code=status
    ).inc()
    
    http_request_duration_seconds.labels(
        service='service-b',
        method=method,
        route=route
    ).observe(duration)
    
    if response.status_code >= 400:
        http_errors_total.labels(
            service='service-b',
            route=route,
            error_type=str(response.status_code)
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
        "service_name": "service-b",
        "request_id": request_id,
        "path": "/health",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-b",
        "status": "healthy",
        "port": 3002,
        "uptime_seconds": uptime,
        "check_type": "liveness"
    }

@app.get("/ready")
async def ready(request: Request):
    request_id = str(uuid.uuid4())
    try:
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
    logger.info("request_received", extra={
        "service_name": "service-b",
        "request_id": request_id,
        "path": "/greet",
        "status": 200,
        "method": "GET"
    })
    try:
        requests.get(
            "http://service-c:3003/greet-c",
            headers={"X-Request-ID": request_id},
            timeout=5
        ).raise_for_status()
    except requests.exceptions.RequestException:
        logger.error("request_failed", extra={
            "service_name": "service-b",
            "request_id": request_id,
            "path": "/greet",
            "status": 502,
            "method": "GET",
            "error": "service_c_unreachable"
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
        "target": "service-c"
    })
    return {"request_id": request_id, "status": "forwarded", "target": "service-c"}

@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    logger.error("controlled_failure_triggered", extra={
        "service_name": "service-b",
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
        "service_name": "service-b",
        "request_id": request_id,
        "path": "/slow",
        "status": 200,
        "method": "GET",
        "delay_seconds": delay
    })
    time.sleep(delay)
    logger.info("slow_request_completed", extra={
        "service_name": "service-b",
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
        "service_name": "service-b",
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3002)
