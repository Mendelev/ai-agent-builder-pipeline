# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from app.core import settings, setup_logging, CorrelationIdMiddleware
from app.api.v1 import requirements
import time

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > settings.MAX_PAYLOAD_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Max size: {settings.MAX_PAYLOAD_SIZE / (1024*1024)}MB"}
            )
    return await call_next(request)

# Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(requirements.router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Requirements Manager API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }