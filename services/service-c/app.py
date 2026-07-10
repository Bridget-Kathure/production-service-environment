from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
import requests
import uuid
import time
import random
import threading
from datetime import datetime, timezone
from logger import get_logger

app = FastAPI()
logger = get_logger("service-c")
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

service_up.labels(service='service-c').inc()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    route = request.url.path
    method = request.method
    status = str(response.status_code)
    
    http_requests_total.labels(
        service='service-c',
        method=method,
        route=route,
        status_code=status
    ).inc()
    
    http_request_duration_seconds.labels(
        service='service-c',
        method=method,
        route=route
    ).observe(duration)
    
    if response.status_code >= 400:
        http_errors_total.labels(
            service='service-c',
            route=route,
            error_type=str(response.status_code)
        ).inc()
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def send_callback(request_id: str):
    """Fire-and-forget callback to Service A."""
    try:
        requests.post(
            "http://service-a:3001/greeting-rcvd",
            headers={"X-Request-ID": request_id},
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
            "target": "service-a"
        })
    except requests.exceptions.RequestException as e:
        logger.error("callback_failed", extra={
            "service_name": "service-c",
            "request_id": request_id,
            "path": "/greet-c",
            "status": 502,
            "method": "GET",
            "error": str(e),
            "target": "service-a"
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
    logger.info("request_received", extra={
        "service_name": "service-c",
        "request_id": request_id,
        "path": "/greet-c",
        "status": 200,
        "method": "GET"
    })

    # Fire callback in background thread so we return immediately to Service B
    threading.Thread(target=send_callback, args=(request_id,), daemon=True).start()

    return {"request_id": request_id, "status": "processed", "callback_sent": True}

@app.get("/fail")
async def fail_endpoint(request: Request):
    request_id = str(uuid.uuid4())
    logger.error("controlled_failure_triggered", extra={
        "service_name": "service-c",
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
        "service_name": "service-c",
        "request_id": request_id,
        "path": "/slow",
        "status": 200,
        "method": "GET",
        "delay_seconds": delay
    })
    time.sleep(delay)
    logger.info("slow_request_completed", extra={
        "service_name": "service-c",
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
        "service_name": "service-c",
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3003)
