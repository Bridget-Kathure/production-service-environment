from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import uvicorn
import requests
import uuid
from datetime import datetime, timezone
from logger import get_logger

app = FastAPI()
logger = get_logger("service-a")

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
        "service": "service-a",
        "status": "healthy",
        "port": 3001,
        "message": "Hello service-a listening on 3001"
    }

@app.get("/greet-service-b")
async def greet_service_b(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())
    logger.info("request_received", extra={
        "request_id": request_id,
        "path": "/greet-service-b",
        "status": 200,
        "method": "GET"
    })
    # TODO: Call Service B at http://service-b.internal:3002/greet
    # TODO: Pass X-Request-ID header
    # TODO: Handle callback from Service C
    return {"request_id": request_id, "status": "pending", "message": "TODO: implement full flow"}

@app.post("/greeting-rcvd")
async def greeting_rcvd(request: Request, x_request_id: str = Header(None)):
    body = await request.json()
    request_id = x_request_id or body.get("request_id", "unknown")
    logger.info("callback_received", extra={
        "request_id": request_id,
        "path": "/greeting-rcvd",
        "status": 200,
        "method": "POST",
        "source_service": body.get("source_service", "unknown")
    })
    return {"received": True, "status": "success"}

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
    uvicorn.run(app, host="0.0.0.0", port=3001)
