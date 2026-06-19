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
async def greet(request: Request, x_request_id: str = Header(None)):
    request_id = x_request_id or str(uuid.uuid4())
    logger.info("request_received", extra={
        "request_id": request_id,
        "path": "/greet",
        "status": 200,
        "method": "GET"
    })
    # TODO: Forward to Service C at http://service-c.internal:3003/greet-c
    # TODO: Pass X-Request-ID header
    return {"request_id": request_id, "status": "forwarded", "target": "service-c"}

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
    uvicorn.run(app, host="127.0.0.1", port=3002)
