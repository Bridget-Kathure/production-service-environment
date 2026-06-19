from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import uvicorn
import requests
import uuid
from logger import get_logger

app = FastAPI()
logger = get_logger("service-b")

@app.get("/health")
async def health(request: Request):
    request_id = str(uuid.uuid4())
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
        "message": "Hello service-b listening on 3002"
    }

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
            "http://service-c.internal:3003/greet-c",
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
    uvicorn.run(app, host="127.0.0.1", port=3002)
