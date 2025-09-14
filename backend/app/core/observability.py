# backend/app/core/observability.py
import json
import logging
import time
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from prometheus_client import Histogram, Counter

# Metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent task duration in seconds',
    ['task']
)

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Metrics
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).observe(process_time)
        
        logger = structlog.get_logger()
        logger.info(
            "request_processed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        return response

def get_logger(name: str = __name__):
    logger = structlog.get_logger(name)
    correlation_id = correlation_id_var.get()
    if correlation_id:
        logger = logger.bind(correlation_id=correlation_id)
    return logger