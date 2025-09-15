# backend/app/middleware/tracing.py
import time

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.observability import correlation_id_var, get_logger

logger = get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.tracer = trace.get_tracer(__name__)

    async def dispatch(self, request: Request, call_next):
        # Get or create correlation ID
        correlation_id = correlation_id_var.get()

        # Start span
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "correlation_id": correlation_id,
            },
        ) as span:
            start_time = time.time()

            try:
                response = await call_next(request)

                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)

                # Calculate duration
                duration = (time.time() - start_time) * 1000  # ms
                span.set_attribute("duration_ms", duration)

                return response

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise


def setup_tracing(app):
    """Setup OpenTelemetry tracing"""
    if not settings.ENABLE_TELEMETRY:
        logger.info("Telemetry disabled")
        return

    # Configure resource
    resource = Resource.create(
        {
            "service.name": "requirements-manager",
            "service.version": "1.0.0",
            "deployment.environment": "development" if settings.DEBUG else "production",
        }
    )

    # Configure tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter (optional, can use Jaeger, Zipkin, etc.)
    if hasattr(settings, "OTLP_ENDPOINT"):
        otlp_exporter = OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=None)  # Will use global engine
    RedisInstrumentor().instrument()
    CeleryInstrumentor().instrument()

    # Add custom middleware
    app.add_middleware(TracingMiddleware)

    logger.info("OpenTelemetry tracing initialized")
