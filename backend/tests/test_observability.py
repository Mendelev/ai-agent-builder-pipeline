# backend/tests/test_observability.py
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request, Response

from app.core.observability import (
    CorrelationIdMiddleware,
    agent_duration,
    correlation_id_var,
    get_logger,
    request_duration,
    setup_logging,
)


def test_setup_logging():
    """Test logging setup."""
    # Should not raise any exceptions
    setup_logging()


def test_correlation_id_var():
    """Test correlation ID context variable."""
    # Default should be None
    assert correlation_id_var.get() is None

    # Set and get correlation ID
    test_id = "test-correlation-id"
    correlation_id_var.set(test_id)
    assert correlation_id_var.get() == test_id


def test_get_logger_without_correlation_id():
    """Test get_logger without correlation ID."""
    # Reset correlation ID
    correlation_id_var.set(None)

    logger = get_logger("test_module")
    assert logger is not None


def test_get_logger_with_correlation_id():
    """Test get_logger with correlation ID."""
    test_id = "test-correlation-id"
    correlation_id_var.set(test_id)

    logger = get_logger("test_module")
    assert logger is not None


@pytest.mark.asyncio
async def test_correlation_id_middleware_with_header():
    """Test middleware with existing correlation ID header."""
    middleware = CorrelationIdMiddleware(app=MagicMock())

    # Mock request with correlation ID header
    request = MagicMock(spec=Request)
    request.headers = {"X-Correlation-ID": "existing-id"}
    request.method = "GET"
    request.url.path = "/test"

    # Mock response
    response = MagicMock(spec=Response)
    response.headers = {}
    response.status_code = 200

    # Mock call_next
    async def mock_call_next(req):
        return response

    result = await middleware.dispatch(request, mock_call_next)

    assert result == response
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == "existing-id"
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_correlation_id_middleware_without_header():
    """Test middleware without correlation ID header."""
    middleware = CorrelationIdMiddleware(app=MagicMock())

    # Mock request without correlation ID header
    request = MagicMock(spec=Request)
    request.headers = {}
    request.method = "POST"
    request.url.path = "/api/test"

    # Mock response
    response = MagicMock(spec=Response)
    response.headers = {}
    response.status_code = 201

    # Mock call_next
    async def mock_call_next(req):
        # Simulate some processing time
        await asyncio.sleep(0.001)
        return response

    with patch("uuid.uuid4") as mock_uuid:
        mock_uuid.return_value = "generated-id"

        result = await middleware.dispatch(request, mock_call_next)

    assert result == response
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == "generated-id"


@pytest.mark.asyncio
async def test_correlation_id_middleware_metrics():
    """Test middleware records metrics."""
    middleware = CorrelationIdMiddleware(app=MagicMock())

    request = MagicMock(spec=Request)
    request.headers = {}
    request.method = "GET"
    request.url.path = "/metrics-test"

    response = MagicMock(spec=Response)
    response.headers = {}
    response.status_code = 200

    async def mock_call_next(req):
        return response

    with patch.object(request_duration, "labels") as mock_labels:
        mock_observe = MagicMock()
        mock_labels.return_value.observe = mock_observe

        await middleware.dispatch(request, mock_call_next)

        # Verify metrics were recorded
        mock_labels.assert_called_once_with(method="GET", endpoint="/metrics-test", status=200)
        mock_observe.assert_called_once()


def test_metrics_objects():
    """Test metrics objects are properly configured."""
    assert request_duration is not None
    assert agent_duration is not None

    # Test that metrics have expected labels
    assert "method" in request_duration._labelnames
    assert "endpoint" in request_duration._labelnames
    assert "status" in request_duration._labelnames

    assert "task" in agent_duration._labelnames


@pytest.mark.asyncio
async def test_middleware_logging():
    """Test middleware logs request information."""
    middleware = CorrelationIdMiddleware(app=MagicMock())

    request = MagicMock(spec=Request)
    request.headers = {}
    request.method = "DELETE"
    request.url.path = "/logging-test"

    response = MagicMock(spec=Response)
    response.headers = {}
    response.status_code = 204

    async def mock_call_next(req):
        return response

    with patch("structlog.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        await middleware.dispatch(request, mock_call_next)

        # Verify logging was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "request_processed"
