# backend/app/main.py (update)
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import orchestration, plan, prompts, projects, requirements
from app.core import CorrelationIdMiddleware, settings, setup_logging
from app.middleware.tracing import setup_tracing

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME, debug=settings.DEBUG, version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc"
)

# Setup OpenTelemetry tracing
setup_tracing(app)


# Size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > settings.MAX_PAYLOAD_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Max size: {settings.MAX_PAYLOAD_SIZE / (1024*1024)}MB"},
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
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include routers
app.include_router(projects.router, prefix=settings.API_V1_PREFIX)
app.include_router(requirements.router, prefix=settings.API_V1_PREFIX)
app.include_router(plan.router, prefix=settings.API_V1_PREFIX)
app.include_router(prompts.router, prefix=settings.API_V1_PREFIX)
app.include_router(orchestration.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time(), "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Requirements Manager API", "version": "1.0.0", "docs": "/api/docs", "metrics": "/metrics"}
