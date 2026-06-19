from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import uvicorn
import requests
import uuid
from datetime import datetime, timezone
from logger import get_logger

app = FastAPI()
logger = get_logger("service-c")

@app.get("/health")
async def health(request: Request):
    request_id = str(uuid.uuid4())
    logger.info("health_check", extra={
        "request_id": request_id,
        "path": "/health",
        "status": 200,
        "method": "GET"
    })
    return {
        "service": "service-c",
        "status": "healthy",
        "port": 3003,
        "message": "Hello service-c listening on 3003"
    }

@app.get("/greet-c")
async def greet_c(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())
    logger.info("request_received", extra={
        "request_id": request_id,
        "path": "/greet-c",
        "status": 200,
        "method": "GET"
    })
    # TODO: Call Service A callback at http://service-a.internal:3001/greeting-rcvd
    # TODO: Pass X-Request-ID header
    # TODO: Send JSON body with request_id, source_service, message, timestamp
    return {"request_id": request_id, "status": "processed", "callback_sent": True}

@app.get("/{path:path}")
async def catch_all(request: Request, path: str):
    request_id = str(uuid.uuid4())
    logger.info("route_not_found", extra={
        "request_id": request_id,
        "path": f"/{path}",
        "status": 404,
        "method": request.method
    })
    return JSONResponse(status_code=404, content={"error": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3003)
